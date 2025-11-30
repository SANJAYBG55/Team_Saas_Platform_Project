"""
Task management views - Template views and API viewsets.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Task, Comment, Attachment, TaskLabel, TaskActivity
from .serializers import (
    TaskSerializer, TaskDetailSerializer, TaskCreateSerializer,
    CommentSerializer, AttachmentSerializer
)
from apps.core.permissions import IsTenantMember
from apps.teams.models import Team, TeamMember


# ==================== Template Views ====================

@login_required
def tasks_list(request):
    """Main tasks page with board, list, and calendar views."""
    tenant = request.user.tenant
    
    # Get all tasks for the tenant
    tasks = Task.objects.filter(
        tenant=tenant
    ).select_related(
        'team', 'assigned_to', 'created_by'
    ).prefetch_related(
        'comments', 'attachments'
    )
    
    # Apply filters
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    team_filter = request.GET.get('team')
    assigned_filter = request.GET.get('assigned_to')
    search_query = request.GET.get('search')
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if team_filter:
        tasks = tasks.filter(team_id=team_filter)
    if assigned_filter:
        tasks = tasks.filter(assigned_to_id=assigned_filter)
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Separate tasks by status for board view
    todo_tasks = tasks.filter(status='TODO')
    in_progress_tasks = tasks.filter(status='IN_PROGRESS')
    review_tasks = tasks.filter(status='IN_REVIEW')
    completed_tasks = tasks.filter(status='COMPLETED')
    
    # Get task stats
    stats = {
        'todo_count': todo_tasks.count(),
        'in_progress_count': in_progress_tasks.count(),
        'review_count': review_tasks.count(),
        'completed_count': completed_tasks.count(),
    }
    
    # Get user's teams
    my_teams = Team.objects.filter(
        members__user=request.user,
        tenant=tenant
    )
    
    # Get team members
    team_members = TeamMember.objects.filter(
        team__tenant=tenant
    ).select_related('user')
    
    # Get today and tomorrow for template filters
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    context = {
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'review_tasks': review_tasks,
        'completed_tasks': completed_tasks,
        'all_tasks': tasks,
        'stats': stats,
        'my_teams': my_teams,
        'team_members': team_members,
        'today': today,
        'tomorrow': tomorrow,
    }
    
    return render(request, 'tenant/tasks.html', context)


@login_required
def task_detail(request, task_id):
    """Task detail page with comments and attachments."""
    tenant = request.user.tenant
    
    task = get_object_or_404(
        Task.objects.select_related(
            'team', 'assigned_to', 'created_by', 'parent_task'
        ).prefetch_related(
            'comments__user',
            'attachments__uploaded_by',
            'subtasks',
            'activities__user'
        ),
        id=task_id,
        tenant=tenant
    )
    
    # Check if user has access to this task
    if task.team:
        is_team_member = TeamMember.objects.filter(
            team=task.team,
            user=request.user
        ).exists()
        
        if not is_team_member and task.created_by != request.user:
            return render(request, 'errors/403.html', status=403)
    
    context = {
        'task': task,
        'comments': task.comments.filter(parent_comment=None),
        'attachments': task.attachments.all(),
        'subtasks': task.subtasks.all(),
        'activities': task.activities.all()[:20],  # Last 20 activities
    }
    
    return render(request, 'tenant/task_detail.html', context)


# ==================== API ViewSets ====================

class TaskViewSet(viewsets.ModelViewSet):
    """API viewset for task CRUD operations."""
    
    permission_classes = [IsAuthenticated, IsTenantMember]
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        """Get tasks for the user's tenant."""
        tenant = self.request.user.tenant
        queryset = Task.objects.filter(tenant=tenant)
        
        # Apply filters
        status = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        team_id = self.request.query_params.get('team')
        assigned_to = self.request.query_params.get('assigned_to')
        created_by = self.request.query_params.get('created_by')
        search = self.request.query_params.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if team_id:
            queryset = queryset.filter(team_id=team_id)
        if assigned_to:
            if assigned_to == 'me':
                queryset = queryset.filter(assigned_to=self.request.user)
            elif assigned_to == 'unassigned':
                queryset = queryset.filter(assigned_to=None)
            else:
                queryset = queryset.filter(assigned_to_id=assigned_to)
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Date filters
        due_date = self.request.query_params.get('due_date')
        overdue = self.request.query_params.get('overdue')
        
        if due_date:
            queryset = queryset.filter(due_date=due_date)
        if overdue == 'true':
            queryset = queryset.filter(
                due_date__lt=timezone.now().date(),
                status__in=['TODO', 'IN_PROGRESS', 'IN_REVIEW']
            )
        
        return queryset.select_related(
            'team', 'assigned_to', 'created_by'
        ).prefetch_related('comments', 'attachments')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return TaskDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskCreateSerializer
        return TaskSerializer
    
    def perform_create(self, serializer):
        """Create task and log activity."""
        task = serializer.save(
            tenant=self.request.user.tenant,
            created_by=self.request.user
        )
        
        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=self.request.user,
            action='CREATED',
            description=f'Created task "{task.title}"'
        )
    
    def perform_update(self, serializer):
        """Update task and log changes."""
        old_task = self.get_object()
        task = serializer.save()
        
        # Log status change
        if old_task.status != task.status:
            TaskActivity.objects.create(
                task=task,
                user=self.request.user,
                action='STATUS_CHANGED',
                description=f'Changed status from {old_task.get_status_display()} to {task.get_status_display()}',
                old_value={'status': old_task.status},
                new_value={'status': task.status}
            )
        
        # Log assignment change
        if old_task.assigned_to != task.assigned_to:
            if task.assigned_to:
                TaskActivity.objects.create(
                    task=task,
                    user=self.request.user,
                    action='ASSIGNED',
                    description=f'Assigned to {task.assigned_to.get_full_name()}'
                )
            else:
                TaskActivity.objects.create(
                    task=task,
                    user=self.request.user,
                    action='UNASSIGNED',
                    description='Unassigned task'
                )
        
        # Log priority change
        if old_task.priority != task.priority:
            TaskActivity.objects.create(
                task=task,
                user=self.request.user,
                action='PRIORITY_CHANGED',
                description=f'Changed priority from {old_task.get_priority_display()} to {task.get_priority_display()}',
                old_value={'priority': old_task.priority},
                new_value={'priority': task.priority}
            )
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get tasks assigned to current user."""
        tasks = self.get_queryset().filter(assigned_to=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks."""
        tasks = self.get_queryset().filter(
            due_date__lt=timezone.now().date(),
            status__in=['TODO', 'IN_PROGRESS', 'IN_REVIEW']
        )
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change task status."""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Task.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = task.status
        task.status = new_status
        
        if new_status == 'COMPLETED':
            task.completed_at = timezone.now()
        
        task.save()
        
        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            action='STATUS_CHANGED',
            description=f'Changed status from {task.get_status_display(old_status)} to {task.get_status_display()}',
            old_value={'status': old_status},
            new_value={'status': new_status}
        )
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign task to a user."""
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        if user_id:
            from apps.accounts.models import User
            try:
                user = User.objects.get(id=user_id, tenant=task.tenant)
                task.assigned_to = user
                task.save()
                
                TaskActivity.objects.create(
                    task=task,
                    user=request.user,
                    action='ASSIGNED',
                    description=f'Assigned to {user.get_full_name()}'
                )
                
                message = f'Task assigned to {user.get_full_name()}'
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            task.assigned_to = None
            task.save()
            
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                action='UNASSIGNED',
                description='Unassigned task'
            )
            
            message = 'Task unassigned'
        
        serializer = self.get_serializer(task)
        return Response({
            'task': serializer.data,
            'message': message
        })


class CommentViewSet(viewsets.ModelViewSet):
    """API viewset for task comments."""
    
    permission_classes = [IsAuthenticated, IsTenantMember]
    serializer_class = CommentSerializer
    
    def get_queryset(self):
        """Get comments for tasks in user's tenant."""
        task_id = self.request.query_params.get('task_id')
        if task_id:
            return Comment.objects.filter(
                task_id=task_id,
                task__tenant=self.request.user.tenant
            ).select_related('user', 'task')
        return Comment.objects.none()
    
    def perform_create(self, serializer):
        """Create comment and log activity."""
        comment = serializer.save(user=self.request.user)
        
        # Update task comments count
        comment.task.comments_count = comment.task.comments.count()
        comment.task.save(update_fields=['comments_count'])
        
        # Log activity
        TaskActivity.objects.create(
            task=comment.task,
            user=self.request.user,
            action='COMMENTED',
            description=f'Added a comment'
        )


class AttachmentViewSet(viewsets.ModelViewSet):
    """API viewset for task attachments."""
    
    permission_classes = [IsAuthenticated, IsTenantMember]
    serializer_class = AttachmentSerializer
    
    def get_queryset(self):
        """Get attachments for tasks in user's tenant."""
        task_id = self.request.query_params.get('task_id')
        if task_id:
            return Attachment.objects.filter(
                task_id=task_id,
                task__tenant=self.request.user.tenant
            ).select_related('uploaded_by', 'task')
        return Attachment.objects.none()
    
    def perform_create(self, serializer):
        """Create attachment and log activity."""
        attachment = serializer.save(uploaded_by=self.request.user)
        
        # Update task attachments count
        attachment.task.attachments_count = attachment.task.attachments.count()
        attachment.task.save(update_fields=['attachments_count'])
        
        # Log activity
        TaskActivity.objects.create(
            task=attachment.task,
            user=self.request.user,
            action='ATTACHMENT_ADDED',
            description=f'Added attachment "{attachment.file_name}"'
        )
    
    def perform_destroy(self, instance):
        """Delete attachment and log activity."""
        task = instance.task
        file_name = instance.file_name
        
        instance.delete()
        
        # Update task attachments count
        task.attachments_count = task.attachments.count()
        task.save(update_fields=['attachments_count'])
        
        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=self.request.user,
            action='ATTACHMENT_REMOVED',
            description=f'Removed attachment "{file_name}"'
        )
