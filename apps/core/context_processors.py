"""
Context processors for templates.
"""
from apps.core.models import SystemSetting
from django.conf import settings


def tenant_context(request):
    """Add tenant information to template context."""
    context = {
        'current_tenant': getattr(request, 'tenant', None),
    }
    
    # Add subscription info if tenant exists
    if hasattr(request, 'tenant') and request.tenant:
        tenant = request.tenant
        context.update({
            'tenant_name': tenant.name,
            'tenant_logo': tenant.logo.url if tenant.logo else None,
            'tenant_subscription': tenant.subscription,
            'is_trial': tenant.is_trial,
            'trial_days_remaining': tenant.trial_days_remaining,
        })
    
    return context


def global_settings(request):
    """Add global settings to template context."""
    return {
        'site_name': settings.SITE_NAME,
        'current_user': request.user if request.user.is_authenticated else None,
    }
