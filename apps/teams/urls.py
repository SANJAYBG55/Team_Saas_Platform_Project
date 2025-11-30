"""
URL configuration for teams app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
api_router = DefaultRouter()
api_router.register(r'', views.TeamViewSet, basename='team')

invitation_router = DefaultRouter()
invitation_router.register(r'', views.TeamInvitationViewSet, basename='team-invitation')

# Template view URLs
template_urlpatterns = [
    path('', views.teams_list, name='teams_list'),
    path('<int:team_id>/', views.team_detail, name='team_detail'),
]

# API URLs
api_urlpatterns = [
    path('', include(api_router.urls)),
    path('invitations/', include(invitation_router.urls)),
]

# Default to API URLs for backwards compatibility
urlpatterns = api_urlpatterns
