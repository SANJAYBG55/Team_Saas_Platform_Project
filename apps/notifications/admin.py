from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'recipient', 'notification_type', 'is_read',
        'email_sent', 'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'email_sent', 'created_at']
    search_fields = ['title', 'message', 'recipient__email']
    readonly_fields = ['created_at', 'read_at', 'email_sent_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'email_task_assigned', 'email_team_invitation',
        'daily_digest', 'weekly_digest'
    ]
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
