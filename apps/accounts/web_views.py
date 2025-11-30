"""
Web views for accounts app - Template-based authentication views.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods


def login_view(request):
    """Render the login page."""
    if request.user.is_authenticated:
        if request.user.is_super_admin:
            return redirect('admin_dashboard')
        return redirect('tenant_dashboard')
    return render(request, 'auth/login.html')


def register_view(request):
    """Render the registration page."""
    if request.user.is_authenticated:
        if request.user.is_super_admin:
            return redirect('admin_dashboard')
        return redirect('tenant_dashboard')
    return render(request, 'auth/register.html')


def password_reset_view(request):
    """Render the password reset request page."""
    if request.user.is_authenticated:
        return redirect('landing')
    return render(request, 'auth/password_reset.html')


def password_reset_confirm_view(request, token=None):
    """Render the password reset confirmation page."""
    if request.user.is_authenticated:
        return redirect('landing')
    return render(request, 'auth/password_reset_confirm.html', {'token': token})


def verify_email_view(request, token=None):
    """Render the email verification page."""
    return render(request, 'auth/verify_email.html', {'token': token})


@login_required
def logout_view(request):
    """Log the user out and redirect to login page."""
    auth_logout(request)
    return redirect('login')
