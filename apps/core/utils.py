"""
Utility functions for the platform.
"""
import secrets
import string
from datetime import datetime, timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from apps.core.models import EmailTemplate, ActivityLog


def generate_token(length=64):
    """Generate a secure random token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_invoice_number():
    """Generate a unique invoice number."""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = ''.join(secrets.choice(string.digits) for _ in range(4))
    return f"INV-{timestamp}-{random_part}"


def send_email(subject, recipient_list, template_name=None, context=None, 
               html_content=None, text_content=None):
    """
    Send email using template or provided content.
    
    Args:
        subject: Email subject
        recipient_list: List of recipient emails
        template_name: Name of email template (optional)
        context: Context data for template (optional)
        html_content: HTML content (if not using template)
        text_content: Text content (if not using template)
    """
    if template_name:
        try:
            template = EmailTemplate.objects.get(
                template_type=template_name,
                is_active=True
            )
            html_content = render_template_string(template.html_content, context or {})
            text_content = render_template_string(template.text_content, context or {}) \
                           if template.text_content else strip_tags(html_content)
            subject = render_template_string(template.subject, context or {})
        except EmailTemplate.DoesNotExist:
            # Fallback to provided content
            pass
    
    if not html_content and not text_content:
        raise ValueError("Either template_name or content must be provided")
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content or strip_tags(html_content),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list
    )
    
    if html_content:
        email.attach_alternative(html_content, "text/html")
    
    email.send()


def render_template_string(template_string, context):
    """Render a template string with context."""
    from django.template import Template, Context
    template = Template(template_string)
    return template.render(Context(context))


def log_activity(user, action, resource_type, description, 
                 tenant=None, metadata=None, request=None):
    """
    Create an activity log entry.
    
    Args:
        user: User performing the action
        action: Action type (CREATE, UPDATE, DELETE, etc.)
        resource_type: Type of resource
        description: Description of the action
        tenant: Tenant (optional)
        metadata: Additional metadata (optional)
        request: HTTP request object (optional)
    """
    ip_address = None
    user_agent = None
    request_path = None
    request_method = None
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        request_path = request.path
        request_method = request.method
    
    ActivityLog.objects.create(
        user=user,
        tenant=tenant,
        action=action,
        resource_type=resource_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        request_path=request_path,
        request_method=request_method,
        metadata=metadata or {}
    )


def check_feature_access(tenant, feature_name):
    """
    Check if tenant has access to a specific feature.
    
    Args:
        tenant: Tenant object
        feature_name: Name of the feature
    
    Returns:
        Boolean indicating access
    """
    if not tenant or not tenant.subscription:
        return False
    
    plan = tenant.subscription.plan
    
    feature_map = {
        'api_access': plan.enable_api_access,
        'advanced_reports': plan.enable_advanced_reports,
        'priority_support': plan.enable_priority_support,
        'custom_branding': plan.enable_custom_branding,
        'sso': plan.enable_sso,
        'audit_logs': plan.enable_audit_logs,
    }
    
    return feature_map.get(feature_name, False)


def calculate_usage_percentage(current, maximum):
    """Calculate usage percentage."""
    if maximum == 0:
        return 0
    return min(int((current / maximum) * 100), 100)


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
