"""
URL configuration for tasks app - both template views and API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()
router.register(r'api', views.TaskViewSet, basename='task')
router.register(r'api/comments', views.CommentViewSet, basename='comment')
router.register(r'api/attachments', views.AttachmentViewSet, basename='attachment')

# URL Patterns
urlpatterns = [
    # Template views
    path('', views.tasks_list, name='tasks-list'),
    path('<int:task_id>/', views.task_detail, name='task-detail'),
    
    # API routes
    path('', include(router.urls)),
]
