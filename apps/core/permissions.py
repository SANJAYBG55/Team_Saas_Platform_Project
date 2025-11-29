"""
Custom permissions and decorators for role-based access control.
"""
from functools import wraps
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from rest_framework import permissions


# Decorator-based permissions for views

def super_admin_required(view_func):
    """Decorator to require super admin role."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_super_admin:
            if request.is_ajax() or request.path.startswith('/api/'):
                return JsonResponse({'error': 'Super admin access required'}, status=403)
            return HttpResponseForbidden("Super admin access required")
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_admin_required(view_func):
    """Decorator to require tenant admin role."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_super_admin or request.user.is_tenant_admin):
            if request.is_ajax() or request.path.startswith('/api/'):
                return JsonResponse({'error': 'Tenant admin access required'}, status=403)
            return HttpResponseForbidden("Tenant admin access required")
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Decorator to require manager role or higher."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_super_admin or 
                request.user.is_tenant_admin or 
                request.user.is_manager):
            if request.is_ajax() or request.path.startswith('/api/'):
                return JsonResponse({'error': 'Manager access required'}, status=403)
            return HttpResponseForbidden("Manager access required")
        return view_func(request, *args, **kwargs)
    return wrapper


def approved_tenant_required(view_func):
    """Decorator to require approved tenant."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_super_admin:
            return view_func(request, *args, **kwargs)
        
        if not request.user.tenant or not request.user.tenant.is_approved:
            return redirect('pending_approval')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def subscription_required(view_func):
    """Decorator to require active subscription."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_super_admin:
            return view_func(request, *args, **kwargs)
        
        tenant = request.user.tenant
        if not tenant or not tenant.subscription or not tenant.subscription.is_active:
            if request.is_ajax() or request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Active subscription required'
                }, status=403)
            return redirect('subscription_expired')
        
        return view_func(request, *args, **kwargs)
    return wrapper


# DRF Permission classes

class IsSuperAdmin(permissions.BasePermission):
    """Permission class for super admins."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_super_admin


class IsTenantAdmin(permissions.BasePermission):
    """Permission class for tenant admins."""
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                (request.user.is_super_admin or request.user.is_tenant_admin))


class IsManager(permissions.BasePermission):
    """Permission class for managers or higher."""
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                (request.user.is_super_admin or 
                 request.user.is_tenant_admin or 
                 request.user.is_manager))


class IsTenantMember(permissions.BasePermission):
    """Permission class for tenant members."""
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.tenant is not None)


class IsApprovedTenant(permissions.BasePermission):
    """Permission class requiring approved tenant."""
    
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_super_admin:
                return True
            return (request.user.tenant and 
                    request.user.tenant.is_approved)
        return False


class HasActiveSubscription(permissions.BasePermission):
    """Permission class requiring active subscription."""
    
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_super_admin:
                return True
            
            tenant = request.user.tenant
            return (tenant and 
                    tenant.subscription and 
                    tenant.subscription.is_active)
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission class allowing owners to edit, others to read."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        return obj.created_by == request.user or request.user.is_super_admin


class IsTeamMember(permissions.BasePermission):
    """Permission class for team members."""
    
    def has_object_permission(self, request, view, obj):
        # Check if user is member of the team
        if hasattr(obj, 'team'):
            return obj.team.members.filter(user=request.user).exists()
        return False
