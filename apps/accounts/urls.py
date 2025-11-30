"""
URL configuration for accounts app - API endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication API
    path('register/', views.RegisterView.as_view(), name='api_register'),
    path('login/', views.LoginView.as_view(), name='api_login'),
    path('logout/', views.LogoutView.as_view(), name='api_logout'),
    
    # User profile API
    path('profile/', views.UserProfileView.as_view(), name='api_user_profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='api_change_password'),
    path('preferences/', views.UserPreferenceView.as_view(), name='api_user_preferences'),
    
    # Password reset API
    path('password-reset/request/', views.request_password_reset, name='api_request_password_reset'),
    path('password-reset/confirm/', views.reset_password, name='api_reset_password'),
]
