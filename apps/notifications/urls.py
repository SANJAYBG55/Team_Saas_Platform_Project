"""
URL configuration for notifications app API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Placeholder for notifications views - to be completed
router = DefaultRouter()
# router.register(r'', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
