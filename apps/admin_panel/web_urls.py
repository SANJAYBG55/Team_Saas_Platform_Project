"""
Web URL configuration for admin panel app.
"""
from django.urls import path
from . import web_views


urlpatterns = [
    path('dashboard/', web_views.admin_dashboard, name='admin_dashboard'),
]
