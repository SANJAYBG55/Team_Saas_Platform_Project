"""
URL configuration for tasks app API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Placeholder for tasks views - to be completed
router = DefaultRouter()
# router.register(r'', views.TaskViewSet, basename='task')
# router.register(r'comments', views.CommentViewSet, basename='comment')
# router.register(r'attachments', views.AttachmentViewSet, basename='attachment')

urlpatterns = [
    path('', include(router.urls)),
]
