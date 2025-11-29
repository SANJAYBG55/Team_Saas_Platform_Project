"""
Admin panel models (if any additional models needed).
Most admin functionality will use models from other apps.
"""
from django.db import models


class AdminDashboardWidget(models.Model):
    """Custom widgets for admin dashboard."""
    
    WIDGET_TYPE_CHOICES = [
        ('STAT', 'Statistic'),
        ('CHART', 'Chart'),
        ('LIST', 'List'),
        ('TABLE', 'Table'),
    ]
    
    title = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    
    # Widget configuration
    config = models.JSONField(default=dict)
    
    # Display settings
    position = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_dashboard_widgets'
        ordering = ['position']
    
    def __str__(self):
        return self.title


class AdminReport(models.Model):
    """Saved admin reports."""
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    report_type = models.CharField(max_length=50)
    filters = models.JSONField(default=dict)
    
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='created_reports'
    )
    
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(
        max_length=20,
        choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
        ],
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
