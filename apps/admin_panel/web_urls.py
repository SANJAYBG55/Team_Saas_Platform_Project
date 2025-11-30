"""
Web URL configuration for admin panel app.
"""
from django.urls import path
from django.shortcuts import render


def admin_dashboard(request):
    """Render the admin dashboard page."""
    return render(request, 'admin_panel/dashboard.html')


urlpatterns = [
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
]
