"""
Serializers for tenants app.
"""
from rest_framework import serializers
from .models import Tenant, Domain, TenantInvitation, TenantSettings
from apps.subscriptions.models import Subscription


class DomainSerializer(serializers.ModelSerializer):
    """Serializer for Domain model."""
    
    class Meta:
        model = Domain
        fields = [
            'id', 'domain', 'domain_type', 'is_primary',
            'is_verified', 'verified_at', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'verified_at', 'created_at']


class TenantSettingsSerializer(serializers.ModelSerializer):
    """Serializer for Tenant Settings."""
    
    class Meta:
        model = TenantSettings
        exclude = ['id', 'tenant', 'created_at']


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model."""
    
    domains = DomainSerializer(many=True, read_only=True)
    settings = TenantSettingsSerializer(read_only=True)
    subscription_details = serializers.SerializerMethodField()
    usage_stats = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'company_name', 'company_email',
            'company_phone', 'address_line1', 'address_line2',
            'city', 'state', 'country', 'postal_code',
            'logo', 'logo_url', 'favicon', 'primary_color',
            'status', 'is_approved', 'approved_at', 'approved_by',
            'subscription', 'subscription_details',
            'max_users', 'max_teams', 'max_projects', 'max_storage_gb',
            'current_users_count', 'current_teams_count',
            'current_projects_count', 'current_storage_gb',
            'usage_stats', 'allow_user_registration',
            'require_email_verification', 'two_factor_auth_required',
            'created_at', 'updated_at', 'trial_ends_at',
            'is_trial', 'trial_days_remaining', 'notes', 'metadata',
            'domains', 'settings'
        ]
        read_only_fields = [
            'id', 'slug', 'is_approved', 'approved_at', 'approved_by',
            'created_at', 'updated_at', 'current_users_count',
            'current_teams_count', 'current_projects_count',
            'current_storage_gb'
        ]
    
    def get_subscription_details(self, obj):
        if obj.subscription:
            return {
                'plan_name': obj.subscription.plan.name,
                'status': obj.subscription.status,
                'current_period_end': obj.subscription.current_period_end,
                'is_active': obj.subscription.is_active,
            }
        return None
    
    def get_usage_stats(self, obj):
        return {
            'users': f"{obj.current_users_count}/{obj.max_users}",
            'teams': f"{obj.current_teams_count}/{obj.max_teams}",
            'projects': f"{obj.current_projects_count}/{obj.max_projects}",
            'storage': f"{obj.current_storage_gb}/{obj.max_storage_gb} GB",
        }
    
    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
        return None


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tenants."""
    
    admin_email = serializers.EmailField(write_only=True)
    admin_password = serializers.CharField(write_only=True)
    admin_first_name = serializers.CharField(write_only=True)
    admin_last_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'company_name', 'company_email', 'company_phone',
            'admin_email', 'admin_password', 'admin_first_name', 'admin_last_name'
        ]
    
    def create(self, validated_data):
        from apps.accounts.models import User
        from django.utils.text import slugify
        import secrets
        
        # Extract admin data
        admin_email = validated_data.pop('admin_email')
        admin_password = validated_data.pop('admin_password')
        admin_first_name = validated_data.pop('admin_first_name')
        admin_last_name = validated_data.pop('admin_last_name')
        
        # Generate unique slug
        base_slug = slugify(validated_data['name'])
        slug = base_slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create tenant
        tenant = Tenant.objects.create(
            slug=slug,
            **validated_data
        )
        
        # Create tenant admin user
        admin_user = User.objects.create_user(
            email=admin_email,
            password=admin_password,
            first_name=admin_first_name,
            last_name=admin_last_name,
            role='TENANT_ADMIN',
            tenant=tenant
        )
        
        # Create default domain
        Domain.objects.create(
            tenant=tenant,
            domain=f"{slug}.yourdomain.com",
            domain_type='SUBDOMAIN',
            is_primary=True,
            is_verified=True
        )
        
        # Create tenant settings
        TenantSettings.objects.create(tenant=tenant)
        
        return tenant


class TenantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tenant."""
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'company_name', 'company_email', 'company_phone',
            'address_line1', 'address_line2', 'city', 'state',
            'country', 'postal_code', 'logo', 'favicon', 'primary_color',
            'allow_user_registration', 'require_email_verification',
            'two_factor_auth_required', 'notes'
        ]


class TenantInvitationSerializer(serializers.ModelSerializer):
    """Serializer for tenant invitations."""
    
    invited_by_name = serializers.CharField(
        source='invited_by.get_full_name',
        read_only=True
    )
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = TenantInvitation
        fields = [
            'id', 'tenant', 'tenant_name', 'email', 'role',
            'token', 'invited_by', 'invited_by_name', 'status',
            'message', 'created_at', 'expires_at', 'accepted_at'
        ]
        read_only_fields = [
            'id', 'token', 'invited_by', 'status',
            'created_at', 'accepted_at'
        ]


class TenantApproveSerializer(serializers.Serializer):
    """Serializer for approving tenant."""
    
    notes = serializers.CharField(required=False, allow_blank=True)


class TenantSuspendSerializer(serializers.Serializer):
    """Serializer for suspending tenant."""
    
    reason = serializers.CharField(required=True)
