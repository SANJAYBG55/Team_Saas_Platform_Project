"""
Notification models.
"""
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """Notification model for user notifications."""
    
    TYPE_CHOICES = [
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('TASK_UPDATED', 'Task Updated'),
        ('TASK_DUE', 'Task Due Soon'),
        ('TASK_OVERDUE', 'Task Overdue'),
        ('TASK_COMPLETED', 'Task Completed'),
        ('COMMENT_ADDED', 'Comment Added'),
        ('TEAM_INVITATION', 'Team Invitation'),
        ('TENANT_INVITATION', 'Tenant Invitation'),
        ('MENTION', 'Mentioned in Comment'),
        ('PAYMENT_SUCCESS', 'Payment Successful'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('SUBSCRIPTION_EXPIRING', 'Subscription Expiring'),
        ('SUBSCRIPTION_EXPIRED', 'Subscription Expired'),
        ('SYSTEM', 'System Notification'),
    ]
    
    recipient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related objects (generic)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.IntegerField(blank=True, null=True)
    
    # Action URL
    action_url = models.CharField(max_length=500, blank=True, null=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Email notification
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.email}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class NotificationPreference(models.Model):
    """User notification preferences."""
    
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email notifications
    email_task_assigned = models.BooleanField(default=True)
    email_task_due = models.BooleanField(default=True)
    email_task_completed = models.BooleanField(default=True)
    email_comment_added = models.BooleanField(default=True)
    email_team_invitation = models.BooleanField(default=True)
    email_mention = models.BooleanField(default=True)
    email_payment_reminder = models.BooleanField(default=True)
    email_subscription_updates = models.BooleanField(default=True)
    
    # In-app notifications
    inapp_task_assigned = models.BooleanField(default=True)
    inapp_task_due = models.BooleanField(default=True)
    inapp_task_completed = models.BooleanField(default=True)
    inapp_comment_added = models.BooleanField(default=True)
    inapp_team_invitation = models.BooleanField(default=True)
    inapp_mention = models.BooleanField(default=True)
    
    # Digest settings
    daily_digest = models.BooleanField(default=False)
    weekly_digest = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.email}"
