from django.contrib import admin
from .models import Tenant, Domain, TenantInvitation, TenantSettings


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'company_name', 'status', 'is_approved',
        'subscription', 'created_at'
    ]
    list_filter = ['status', 'is_approved', 'created_at']
    search_fields = ['name', 'slug', 'company_name', 'company_email']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'company_name', 'company_email', 'company_phone')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code')
        }),
        ('Branding', {
            'fields': ('logo', 'favicon', 'primary_color')
        }),
        ('Status', {
            'fields': ('status', 'is_approved', 'approved_at', 'approved_by')
        }),
        ('Subscription', {
            'fields': ('subscription', 'trial_ends_at')
        }),
        ('Limits', {
            'fields': (
                'max_users', 'max_teams', 'max_projects', 'max_storage_gb',
                'current_users_count', 'current_teams_count', 'current_projects_count', 'current_storage_gb'
            )
        }),
        ('Settings', {
            'fields': ('allow_user_registration', 'require_email_verification', 'two_factor_auth_required')
        }),
        ('Additional', {
            'fields': ('notes', 'metadata', 'created_at', 'updated_at')
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'domain_type', 'is_primary', 'is_verified', 'created_at']
    list_filter = ['domain_type', 'is_primary', 'is_verified']
    search_fields = ['domain', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'tenant', 'role', 'status', 'invited_by', 'created_at', 'expires_at']
    list_filter = ['status', 'role', 'created_at']
    search_fields = ['email', 'tenant__name']
    readonly_fields = ['created_at', 'accepted_at']


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'enable_teams', 'enable_tasks', 'enable_projects', 'timezone']
    search_fields = ['tenant__name']
    readonly_fields = ['created_at', 'updated_at']
