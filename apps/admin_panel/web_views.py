"""
Web views for admin panel app.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def admin_dashboard(request):
    """Render the admin dashboard page."""
    return render(request, 'admin_panel/dashboard.html')
