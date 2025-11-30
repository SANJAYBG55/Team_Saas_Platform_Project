"""
Web URL configuration for accounts app - Template-based views.
"""
from django.urls import path
from . import web_views

urlpatterns = [
    path('login/', web_views.login_view, name='login'),
    path('register/', web_views.register_view, name='register'),
    path('logout/', web_views.logout_view, name='logout'),
    path('password-reset/', web_views.password_reset_view, name='password_reset'),
    path('password-reset/<str:token>/', web_views.password_reset_confirm_view, name='password_reset_confirm'),
    path('verify-email/<str:token>/', web_views.verify_email_view, name='verify_email'),
]
