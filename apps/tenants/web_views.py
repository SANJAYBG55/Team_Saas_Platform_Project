"""
Web views for tenants app.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def tenant_dashboard(request):
    """Render the tenant dashboard page."""
    return render(request, 'tenant/dashboard.html')
