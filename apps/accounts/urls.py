"""
URL configuration for accounts app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('preferences/', views.UserPreferenceView.as_view(), name='user_preferences'),
    
    # Password reset
    path('password-reset/request/', views.request_password_reset, name='request_password_reset'),
    path('password-reset/confirm/', views.reset_password, name='reset_password'),
    
    # Tenant Signup Flow
    path('signup/', views.signup_page, name='signup_page'),
    path('check-domain/', views.check_domain_availability, name='check_domain'),
    path('plans/', views.get_plans, name='get_plans'),
    path('complete-signup/', views.complete_signup, name='complete_signup'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification'),
]
