"""
Web URL configuration for tenants app.
"""
from django.urls import path
from . import web_views


urlpatterns = [
    path('dashboard/', web_views.tenant_dashboard, name='tenant_dashboard'),
]
