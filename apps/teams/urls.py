"""
URL configuration for teams app API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.TeamViewSet, basename='team')
router.register(r'invitations', views.TeamInvitationViewSet, basename='team-invitation')

urlpatterns = [
    path('', include(router.urls)),
]
