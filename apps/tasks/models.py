"""
Task management models.
"""
from django.db import models
from django.utils import timezone


class Task(models.Model):
    """Task model for project/team tasks."""
    
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('IN_REVIEW', 'In Review'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True
    )
    
    # Task details
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Assignment
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='created_tasks'
    )
    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    
    # Dates
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Parent task (for subtasks)
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks'
    )
    
    # Ordering and position (for Kanban)
    position = models.IntegerField(default=0)
    
    # Stats
    comments_count = models.IntegerField(default=0)
    attachments_count = models.IntegerField(default=0)
    subtasks_count = models.IntegerField(default=0)
    
    # Additional fields
    tags = models.JSONField(default=list, blank=True)
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        ordering = ['position', '-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['team', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if self.due_date and self.status not in ['COMPLETED', 'CANCELLED']:
            return timezone.now().date() > self.due_date
        return False
    
    @property
    def progress_percentage(self):
        """Calculate task progress based on subtasks."""
        if self.subtasks_count == 0:
            return 100 if self.status == 'COMPLETED' else 0
        
        completed_subtasks = self.subtasks.filter(status='COMPLETED').count()
        return int((completed_subtasks / self.subtasks_count) * 100)


class Comment(models.Model):
    """Comment model for task discussions."""
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    
    content = models.TextField()
    
    # Parent comment (for replies)
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    # Editing
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_comments'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.get_full_name()} on {self.task.title}"


class Attachment(models.Model):
    """Attachment model for task files."""
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='uploaded_attachments'
    )
    
    file = models.FileField(upload_to='tasks/attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # Size in bytes
    file_type = models.CharField(max_length=100)
    
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_attachments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
        ]
    
    def __str__(self):
        return self.file_name
    
    @property
    def file_size_mb(self):
        """Return file size in MB."""
        return round(self.file_size / (1024 * 1024), 2)


class TaskLabel(models.Model):
    """Label/Tag model for categorizing tasks."""
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='task_labels'
    )
    
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6B7280')
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_labels'
        ordering = ['name']
        unique_together = [['tenant', 'name']]
    
    def __str__(self):
        return self.name


class TaskActivity(models.Model):
    """Activity log for task changes."""
    
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('UPDATED', 'Updated'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('ASSIGNED', 'Assigned'),
        ('UNASSIGNED', 'Unassigned'),
        ('COMMENTED', 'Commented'),
        ('ATTACHMENT_ADDED', 'Attachment Added'),
        ('ATTACHMENT_REMOVED', 'Attachment Removed'),
        ('DUE_DATE_CHANGED', 'Due Date Changed'),
        ('PRIORITY_CHANGED', 'Priority Changed'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='task_activities'
    )
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    
    # Store old and new values for changes
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
        ]
        verbose_name_plural = 'Task activities'
    
    def __str__(self):
        return f"{self.user.get_full_name()} {self.action} on {self.task.title}"
