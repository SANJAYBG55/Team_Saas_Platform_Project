"""
Core views for public pages and error handlers.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.tenants.models import Tenant


def landing_page(request):
    """Public landing page."""
    if request.user.is_authenticated:
        if request.user.is_super_admin:
            return redirect('admin_dashboard')
        return redirect('tenant_dashboard')
    
    return render(request, 'public/landing.html')


def pending_approval(request):
    """Pending approval page for unapproved tenants."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.is_super_admin:
        return redirect('admin_dashboard')
    
    if request.user.tenant and request.user.tenant.is_approved:
        return redirect('tenant_dashboard')
    
    return render(request, 'public/pending_approval.html', {
        'tenant': request.user.tenant
    })


def error_404(request, exception=None):
    """Custom 404 error page."""
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    """Custom 500 error page."""
    return render(request, 'errors/500.html', status=500)


def error_403(request, exception=None):
    """Custom 403 error page."""
    return render(request, 'errors/403.html', status=403)
