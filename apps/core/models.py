"""
Core models for activity logs and audit trails.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class ActivityLog(models.Model):
    """Global activity log for tracking all actions."""
    
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('LOGIN', 'Logged In'),
        ('LOGOUT', 'Logged Out'),
        ('VIEW', 'Viewed'),
        ('DOWNLOAD', 'Downloaded'),
        ('UPLOAD', 'Uploaded'),
        ('APPROVE', 'Approved'),
        ('REJECT', 'Rejected'),
        ('SUSPEND', 'Suspended'),
        ('ACTIVATE', 'Activated'),
        ('INVITE', 'Invited'),
        ('ACCEPT_INVITE', 'Accepted Invitation'),
        ('PAYMENT', 'Payment Made'),
        ('OTHER', 'Other'),
    ]
    
    # Who performed the action
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    
    # Action details
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=100)
    resource_id = models.IntegerField(null=True, blank=True)
    description = models.TextField()
    
    # Generic relation to any object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    request_path = models.CharField(max_length=500, null=True, blank=True)
    request_method = models.CharField(max_length=10, null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'System'
        return f"{user_str} {self.action} {self.resource_type}"


class AuditLog(models.Model):
    """Audit log specifically for admin actions."""
    
    admin_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    
    action = models.CharField(max_length=100)
    target_model = models.CharField(max_length=100)
    target_id = models.IntegerField(null=True, blank=True)
    target_description = models.CharField(max_length=500)
    
    # Changes
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    # Request info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', 'created_at']),
            models.Index(fields=['target_model', 'target_id']),
        ]
    
    def __str__(self):
        user_str = self.admin_user.email if self.admin_user else 'System'
        return f"{user_str} {self.action} on {self.target_model}"


class SystemSetting(models.Model):
    """System-wide settings."""
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    value_type = models.CharField(
        max_length=20,
        choices=[
            ('STRING', 'String'),
            ('INTEGER', 'Integer'),
            ('BOOLEAN', 'Boolean'),
            ('JSON', 'JSON'),
        ],
        default='STRING'
    )
    
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_settings'
        ordering = ['key']
    
    def __str__(self):
        return self.key
    
    def get_value(self):
        """Get the properly typed value."""
        if self.value_type == 'INTEGER':
            return int(self.value)
        elif self.value_type == 'BOOLEAN':
            return self.value.lower() in ['true', '1', 'yes']
        elif self.value_type == 'JSON':
            import json
            return json.loads(self.value)
        return self.value


class EmailTemplate(models.Model):
    """Email template model for system emails."""
    
    TEMPLATE_TYPE_CHOICES = [
        ('WELCOME', 'Welcome Email'),
        ('VERIFICATION', 'Email Verification'),
        ('PASSWORD_RESET', 'Password Reset'),
        ('TENANT_APPROVED', 'Tenant Approved'),
        ('TENANT_SUSPENDED', 'Tenant Suspended'),
        ('TEAM_INVITATION', 'Team Invitation'),
        ('TENANT_INVITATION', 'Tenant Invitation'),
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('PAYMENT_SUCCESS', 'Payment Successful'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('INVOICE', 'Invoice'),
        ('SUBSCRIPTION_REMINDER', 'Subscription Reminder'),
        ('CUSTOM', 'Custom Template'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES)
    subject = models.CharField(max_length=255)
    
    # Template content (supports variables like {{user_name}}, {{link}}, etc.)
    html_content = models.TextField()
    text_content = models.TextField(blank=True, null=True)
    
    # Available variables for this template
    available_variables = models.JSONField(default=list, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_templates'
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"
