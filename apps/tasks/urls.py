"""
URL configuration for tasks app - both template views and API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
api_router = DefaultRouter()
api_router.register(r'', views.TaskViewSet, basename='task')

comment_router = DefaultRouter()
comment_router.register(r'', views.CommentViewSet, basename='comment')

attachment_router = DefaultRouter()
attachment_router.register(r'', views.AttachmentViewSet, basename='attachment')

# Template view URLs
template_urlpatterns = [
    path('', views.tasks_list, name='tasks-list'),
    path('<int:task_id>/', views.task_detail, name='task-detail'),
]

# API URLs (default for backwards compatibility)
urlpatterns = [
    path('', include(api_router.urls)),
    path('comments/', include(comment_router.urls)),
    path('attachments/', include(attachment_router.urls)),
]
