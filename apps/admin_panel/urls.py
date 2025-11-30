"""
URL configuration for admin_panel app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

app_name = 'admin_panel'

urlpatterns = [
    # Web views
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('tenants/<int:tenant_id>/', views.tenant_detail, name='tenant_detail'),
    path('access-denied/', views.access_denied, name='access_denied'),
    
    # API endpoints (AJAX)
    path('api/tenants/<int:tenant_id>/approve/', views.approve_tenant, name='approve_tenant'),
    path('api/tenants/<int:tenant_id>/toggle-status/', views.toggle_tenant_status, name='toggle_tenant_status'),
    path('api/tenants/<int:tenant_id>/message/', views.send_tenant_message, name='send_tenant_message'),
    path('api/tenants/', views.create_tenant, name='create_tenant'),
    path('api/tenants/export/', views.export_tenants, name='export_tenants'),
    
    # DRF router URLs
    path('', include(router.urls)),
]
