"""
URL configuration for tenants app API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.TenantViewSet, basename='tenant')
router.register(r'invitations', views.TenantInvitationViewSet, basename='tenant-invitation')

urlpatterns = [
    path('', include(router.urls)),
    path('settings/', views.TenantSettingsView.as_view(), name='tenant-settings'),
]
