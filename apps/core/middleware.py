"""
Custom middleware for the SaaS platform.
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from apps.tenants.models import Tenant, Domain
from apps.core.models import ActivityLog


class TenantMiddleware(MiddlewareMixin):
    """Middleware to resolve tenant from domain/subdomain."""
    
    def process_request(self, request):
        """Resolve tenant from the request domain."""
        host = request.get_host().split(':')[0]  # Remove port
        
        # Skip tenant resolution for admin and API auth endpoints
        if request.path.startswith('/django-admin/') or \
           request.path.startswith('/api/auth/') or \
           request.path.startswith('/admin/login/'):
            request.tenant = None
            return None
        
        # Try to find tenant by domain
        try:
            domain = Domain.objects.select_related('tenant').get(
                domain=host,
                is_verified=True
            )
            tenant = domain.tenant
            
            # Check if tenant is active
            if tenant.status != 'ACTIVE':
                request.tenant = None
                return None
            
            request.tenant = tenant
            
        except Domain.DoesNotExist:
            # Try to extract subdomain
            parts = host.split('.')
            if len(parts) >= 2:
                subdomain = parts[0]
                try:
                    tenant = Tenant.objects.get(slug=subdomain, status='ACTIVE')
                    request.tenant = tenant
                except Tenant.DoesNotExist:
                    request.tenant = None
            else:
                request.tenant = None
        
        return None


class ApprovalMiddleware(MiddlewareMixin):
    """Middleware to check tenant approval status."""
    
    def process_request(self, request):
        """Check if user's tenant is approved."""
        # Skip for certain paths
        excluded_paths = [
            '/django-admin/',
            '/api/auth/',
            '/admin/login/',
            '/app/pending-approval/',
            '/logout/',
            '/static/',
            '/media/',
        ]
        
        if any(request.path.startswith(path) for path in excluded_paths):
            return None
        
        # Check if user is authenticated and has a tenant
        if request.user.is_authenticated and hasattr(request.user, 'tenant'):
            tenant = request.user.tenant
            
            # Super admins bypass approval check
            if request.user.is_super_admin:
                return None
            
            # If tenant exists and is not approved
            if tenant and not tenant.is_approved:
                # Redirect to pending approval page
                if not request.path == '/app/pending-approval/':
                    return redirect('pending_approval')
        
        return None


class ActivityLogMiddleware(MiddlewareMixin):
    """Middleware to log user activities."""
    
    def process_response(self, request, response):
        """Log successful requests."""
        # Only log for authenticated users
        if not request.user.is_authenticated:
            return response
        
        # Only log certain types of requests
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Skip logging for certain paths
            excluded_paths = [
                '/static/',
                '/media/',
                '/api/notifications/',  # Too frequent
            ]
            
            if not any(request.path.startswith(path) for path in excluded_paths):
                # Get IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')
                
                # Determine action based on method
                action_map = {
                    'POST': 'CREATE',
                    'PUT': 'UPDATE',
                    'PATCH': 'UPDATE',
                    'DELETE': 'DELETE',
                }
                
                try:
                    ActivityLog.objects.create(
                        user=request.user,
                        tenant=getattr(request, 'tenant', None),
                        action=action_map.get(request.method, 'OTHER'),
                        resource_type='API',
                        description=f"{request.method} {request.path}",
                        ip_address=ip_address,
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                        request_path=request.path,
                        request_method=request.method,
                    )
                except Exception:
                    # Don't break the request if logging fails
                    pass
        
        return response


class LimitUsageMiddleware(MiddlewareMixin):
    """Middleware to enforce tenant usage limits."""
    
    def process_request(self, request):
        """Check tenant usage limits."""
        # Only check for authenticated users with tenants
        if not request.user.is_authenticated or not hasattr(request, 'tenant'):
            return None
        
        tenant = request.tenant
        if not tenant:
            return None
        
        # Skip for super admins
        if request.user.is_super_admin:
            return None
        
        # Check limits on certain operations
        # This is a simple implementation; can be expanded
        if request.method == 'POST':
            limits = tenant.check_limits()
            
            # Check specific endpoints
            if '/api/teams/' in request.path and limits['teams']:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Team limit reached. Please upgrade your plan.'
                }, status=403)
            
            if '/api/tasks/' in request.path and limits['projects']:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Project limit reached. Please upgrade your plan.'
                }, status=403)
        
        return None
