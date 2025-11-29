from django.contrib import admin
from .models import Task, Comment, Attachment, TaskLabel, TaskActivity


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'tenant', 'team', 'status', 'priority',
        'assigned_to', 'due_date', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'priority', 'tenant', 'team', 'created_at']
    search_fields = ['title', 'description', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'content_preview', 'created_at', 'is_edited']
    list_filter = ['created_at', 'is_edited']
    search_fields = ['content', 'user__email', 'task__title']
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'task', 'uploaded_by', 'file_size_mb', 'created_at']
    list_filter = ['created_at', 'file_type']
    search_fields = ['file_name', 'task__title', 'uploaded_by__email']
    readonly_fields = ['created_at']


@admin.register(TaskLabel)
class TaskLabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'color', 'created_at']
    list_filter = ['tenant', 'created_at']
    search_fields = ['name']


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'action', 'description', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['task__title', 'user__email', 'description']
    readonly_fields = ['created_at']
