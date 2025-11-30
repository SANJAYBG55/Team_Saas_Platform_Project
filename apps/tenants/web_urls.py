"""
Web URL configuration for tenants app.
"""
from django.urls import path
from django.shortcuts import render


def tenant_dashboard(request):
    """Render the tenant dashboard page."""
    return render(request, 'tenant/dashboard.html')


urlpatterns = [
    path('dashboard/', tenant_dashboard, name='tenant_dashboard'),
]
