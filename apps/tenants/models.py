"""
Tenant models for multi-tenancy support.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator


class Tenant(models.Model):
    """Tenant model representing a company/organization."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    company_name = models.CharField(max_length=255)
    company_email = models.EmailField()
    company_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')]
    )
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Logo and branding
    logo = models.ImageField(upload_to='tenants/logos/', blank=True, null=True)
    favicon = models.ImageField(upload_to='tenants/favicons/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#2563EB')
    
    # Status and approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_tenants'
    )
    
    # Subscription
    subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenants'
    )
    
    # Limits and usage
    max_users = models.IntegerField(default=10)
    max_teams = models.IntegerField(default=5)
    max_projects = models.IntegerField(default=10)
    max_storage_gb = models.IntegerField(default=10)
    
    current_users_count = models.IntegerField(default=0)
    current_teams_count = models.IntegerField(default=0)
    current_projects_count = models.IntegerField(default=0)
    current_storage_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Settings
    allow_user_registration = models.BooleanField(default=False)
    require_email_verification = models.BooleanField(default=True)
    two_factor_auth_required = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Additional fields
    notes = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'tenants'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_trial(self):
        """Check if tenant is in trial period."""
        if self.trial_ends_at:
            return timezone.now() < self.trial_ends_at
        return False
    
    @property
    def trial_days_remaining(self):
        """Calculate remaining trial days."""
        if self.trial_ends_at and self.is_trial:
            delta = self.trial_ends_at - timezone.now()
            return delta.days
        return 0
    
    def approve(self, approved_by_user):
        """Approve the tenant."""
        self.is_approved = True
        self.status = 'ACTIVE'
        self.approved_at = timezone.now()
        self.approved_by = approved_by_user
        self.save()
    
    def suspend(self, reason=None):
        """Suspend the tenant."""
        self.status = 'SUSPENDED'
        if reason:
            self.notes = f"{self.notes}\n\nSuspended: {reason}" if self.notes else f"Suspended: {reason}"
        self.save()
    
    def check_limits(self):
        """Check if tenant has reached any limits."""
        limits = {
            'users': self.current_users_count >= self.max_users,
            'teams': self.current_teams_count >= self.max_teams,
            'projects': self.current_projects_count >= self.max_projects,
            'storage': self.current_storage_gb >= self.max_storage_gb,
        }
        return limits


class Domain(models.Model):
    """Domain model for tenant domain/subdomain mapping."""
    
    DOMAIN_TYPE_CHOICES = [
        ('PRIMARY', 'Primary Domain'),
        ('SUBDOMAIN', 'Subdomain'),
        ('CUSTOM', 'Custom Domain'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=255, unique=True, db_index=True)
    domain_type = models.CharField(max_length=20, choices=DOMAIN_TYPE_CHOICES, default='SUBDOMAIN')
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_domains'
        ordering = ['-is_primary', 'domain']
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['tenant', 'is_primary']),
        ]
    
    def __str__(self):
        return self.domain


class TenantInvitation(models.Model):
    """Invitation model for inviting users to join a tenant."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, default='MEMBER')
    token = models.CharField(max_length=255, unique=True)
    
    invited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tenant_invitations'
        ordering = ['-created_at']
        unique_together = [['tenant', 'email']]
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email', 'status']),
        ]
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.tenant.name}"


class TenantSettings(models.Model):
    """Settings model for tenant-specific configuration."""
    
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='settings')
    
    # Feature toggles
    enable_teams = models.BooleanField(default=True)
    enable_tasks = models.BooleanField(default=True)
    enable_projects = models.BooleanField(default=True)
    enable_time_tracking = models.BooleanField(default=False)
    enable_file_uploads = models.BooleanField(default=True)
    enable_comments = models.BooleanField(default=True)
    enable_notifications = models.BooleanField(default=True)
    
    # Customization
    custom_css = models.TextField(blank=True, null=True)
    custom_js = models.TextField(blank=True, null=True)
    welcome_message = models.TextField(blank=True, null=True)
    
    # Integration settings
    slack_webhook_url = models.URLField(blank=True, null=True)
    webhook_url = models.URLField(blank=True, null=True)
    
    # Other settings
    timezone = models.CharField(max_length=50, default='UTC')
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    time_format = models.CharField(max_length=20, default='HH:mm')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_settings'
    
    def __str__(self):
        return f"Settings for {self.tenant.name}"
