"""
URL configuration for admin_panel app API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Placeholder for admin panel views - to be completed
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]
