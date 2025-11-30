"""
Serializers for tasks app.
"""
from rest_framework import serializers
from .models import Task, Comment, Attachment, TaskLabel, TaskActivity
from apps.accounts.serializers import UserSerializer
from apps.teams.serializers import TeamSerializer


class TaskLabelSerializer(serializers.ModelSerializer):
    """Serializer for TaskLabel model."""
    
    class Meta:
        model = TaskLabel
        fields = ['id', 'tenant', 'name', 'color', 'description', 'created_at']
        read_only_fields = ['id', 'tenant', 'created_at']


class AttachmentSerializer(serializers.ModelSerializer):
    """Serializer for Attachment model."""
    
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.get_full_name',
        read_only=True
    )
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Attachment
        fields = [
            'id', 'task', 'uploaded_by', 'uploaded_by_name',
            'file', 'file_url', 'file_name', 'file_size',
            'file_type', 'description', 'created_at'
        ]
        read_only_fields = [
            'id', 'uploaded_by', 'file_name', 'file_size',
            'file_type', 'created_at'
        ]
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model."""
    
    user_details = UserSerializer(source='user', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'task', 'user', 'user_details', 'content',
            'parent_comment', 'replies', 'is_edited', 'edited_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'is_edited', 'edited_at',
            'created_at', 'updated_at'
        ]
    
    def get_replies(self, obj):
        if obj.parent_comment is None:
            replies = obj.replies.all()
            return CommentSerializer(replies, many=True, context=self.context).data
        return []


class TaskActivitySerializer(serializers.ModelSerializer):
    """Serializer for TaskActivity model."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = TaskActivity
        fields = [
            'id', 'task', 'user', 'user_name', 'action',
            'description', 'old_value', 'new_value', 'created_at'
        ]
        read_only_fields = fields


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model."""
    
    created_by_details = UserSerializer(source='created_by', read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    team_details = serializers.SerializerMethodField()
    subtasks = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    progress = serializers.IntegerField(source='progress_percentage', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'tenant', 'team', 'team_details', 'title', 'description',
            'status', 'priority', 'created_by', 'created_by_details',
            'assigned_to', 'assigned_to_details', 'start_date', 'due_date',
            'completed_at', 'parent_task', 'subtasks', 'position',
            'comments_count', 'attachments_count', 'subtasks_count',
            'tags', 'estimated_hours', 'actual_hours', 'progress',
            'is_overdue', 'comments', 'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tenant', 'created_by', 'completed_at',
            'comments_count', 'attachments_count', 'subtasks_count',
            'is_overdue', 'created_at', 'updated_at'
        ]
    
    def get_team_details(self, obj):
        if obj.team:
            return {
                'id': obj.team.id,
                'name': obj.team.name,
                'slug': obj.team.slug
            }
        return None
    
    def get_subtasks(self, obj):
        if obj.parent_task is None:
            subtasks = obj.subtasks.all()
            return TaskSerializer(subtasks, many=True, context=self.context).data
        return []


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks."""
    
    class Meta:
        model = Task
        fields = [
            'team', 'title', 'description', 'status', 'priority',
            'assigned_to', 'start_date', 'due_date', 'parent_task',
            'tags', 'estimated_hours'
        ]


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tasks."""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority',
            'assigned_to', 'start_date', 'due_date', 'tags',
            'estimated_hours', 'actual_hours', 'position'
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for task with all relationships."""
    
    created_by_details = UserSerializer(source='created_by', read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    team_details = serializers.SerializerMethodField()
    subtasks = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    activities = TaskActivitySerializer(many=True, read_only=True)
    progress = serializers.IntegerField(source='progress_percentage', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'tenant', 'team', 'team_details', 'title', 'description',
            'status', 'priority', 'created_by', 'created_by_details',
            'assigned_to', 'assigned_to_details', 'start_date', 'due_date',
            'completed_at', 'parent_task', 'subtasks', 'position',
            'comments_count', 'attachments_count', 'subtasks_count',
            'tags', 'estimated_hours', 'actual_hours', 'progress',
            'is_overdue', 'comments', 'attachments', 'activities',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_team_details(self, obj):
        if obj.team:
            return {
                'id': obj.team.id,
                'name': obj.team.name,
                'slug': obj.team.slug
            }
        return None
    
    def get_subtasks(self, obj):
        if obj.parent_task is None:
            subtasks = obj.subtasks.all()
            return TaskSerializer(subtasks, many=True, context=self.context).data
        return []
