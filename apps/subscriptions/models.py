"""
Subscription and billing models.
"""
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Plan(models.Model):
    """Subscription plan model."""
    
    BILLING_INTERVAL_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    billing_interval = models.CharField(
        max_length=20,
        choices=BILLING_INTERVAL_CHOICES,
        default='MONTHLY'
    )
    
    # Features and limits
    max_users = models.IntegerField(default=10)
    max_teams = models.IntegerField(default=5)
    max_projects = models.IntegerField(default=10)
    max_storage_gb = models.IntegerField(default=10)
    
    # Feature flags
    enable_api_access = models.BooleanField(default=False)
    enable_advanced_reports = models.BooleanField(default=False)
    enable_priority_support = models.BooleanField(default=False)
    enable_custom_branding = models.BooleanField(default=False)
    enable_sso = models.BooleanField(default=False)
    enable_audit_logs = models.BooleanField(default=False)
    
    # Display
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    # Trial
    trial_days = models.IntegerField(default=14)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plans'
        ordering = ['sort_order', 'price']
    
    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_interval}"


class Subscription(models.Model):
    """Subscription model linking tenant to a plan."""
    
    STATUS_CHOICES = [
        ('TRIAL', 'Trial'),
        ('ACTIVE', 'Active'),
        ('PAST_DUE', 'Past Due'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TRIAL')
    
    # Billing cycle
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    
    # Auto-renewal
    auto_renew = models.BooleanField(default=True)
    cancel_at_period_end = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Trial
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['current_period_end']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name}"
    
    @property
    def is_active(self):
        """Check if subscription is active."""
        return self.status in ['TRIAL', 'ACTIVE']
    
    @property
    def is_trial(self):
        """Check if subscription is in trial."""
        return self.status == 'TRIAL'
    
    @property
    def days_until_renewal(self):
        """Calculate days until renewal."""
        if self.current_period_end:
            delta = self.current_period_end - timezone.now()
            return max(0, delta.days)
        return 0
    
    def cancel(self, immediately=False):
        """Cancel the subscription."""
        self.cancelled_at = timezone.now()
        if immediately:
            self.status = 'CANCELLED'
        else:
            self.cancel_at_period_end = True
        self.save()


class Payment(models.Model):
    """Payment model for tracking transactions."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('CARD', 'Credit/Debit Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('PAYPAL', 'PayPal'),
        ('MANUAL', 'Manual Payment'),
        ('OTHER', 'Other'),
    ]
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Transaction details
    transaction_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    payment_gateway = models.CharField(max_length=50, blank=True, null=True)
    payment_gateway_response = models.JSONField(default=dict, blank=True)
    
    # Verification (for manual payments)
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Verification'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
        ],
        default='PENDING'
    )
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, null=True)
    
    # Proof of payment (for manual verification)
    payment_proof = models.FileField(
        upload_to='payments/proofs/',
        blank=True,
        null=True
    )
    
    # Additional info
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.id} - {self.tenant.name} - ${self.amount}"
    
    def approve_verification(self, verified_by_user, notes=None):
        """Approve payment verification."""
        self.verification_status = 'APPROVED'
        self.status = 'COMPLETED'
        self.verified_by = verified_by_user
        self.verified_at = timezone.now()
        self.paid_at = timezone.now()
        if notes:
            self.verification_notes = notes
        self.save()
    
    def reject_verification(self, verified_by_user, notes=None):
        """Reject payment verification."""
        self.verification_status = 'REJECTED'
        self.status = 'FAILED'
        self.verified_by = verified_by_user
        self.verified_at = timezone.now()
        if notes:
            self.verification_notes = notes
        self.save()


class Invoice(models.Model):
    """Invoice model for billing records."""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    payment = models.OneToOneField(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice'
    )
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Dates
    issue_date = models.DateField()
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    notes = models.TextField(blank=True, null=True)
    terms = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['invoice_number']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.tenant.name}"
    
    def calculate_total(self):
        """Calculate invoice total."""
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total = self.subtotal + self.tax_amount - self.discount_amount
        return self.total


class InvoiceItem(models.Model):
    """Invoice line items."""
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'invoice_items'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.description} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        """Calculate amount before saving."""
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
