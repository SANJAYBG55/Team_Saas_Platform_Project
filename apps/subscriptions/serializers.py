"""
Serializers for subscriptions app.
"""
from rest_framework import serializers
from .models import Plan, Subscription, Payment, Invoice, InvoiceItem
from apps.tenants.models import Tenant


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for Plan model."""
    
    features = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'currency',
            'billing_interval', 'max_users', 'max_teams', 'max_projects',
            'max_storage_gb', 'features', 'is_popular', 'is_active',
            'trial_days', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_features(self, obj):
        return {
            'api_access': obj.enable_api_access,
            'advanced_reports': obj.enable_advanced_reports,
            'priority_support': obj.enable_priority_support,
            'custom_branding': obj.enable_custom_branding,
            'sso': obj.enable_sso,
            'audit_logs': obj.enable_audit_logs,
        }


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model."""
    
    plan_details = PlanSerializer(source='plan', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    days_remaining = serializers.IntegerField(
        source='days_until_renewal',
        read_only=True
    )
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'tenant', 'tenant_name', 'plan', 'plan_details',
            'status', 'current_period_start', 'current_period_end',
            'auto_renew', 'cancel_at_period_end', 'cancelled_at',
            'trial_start', 'trial_end', 'is_active', 'is_trial',
            'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'current_period_start', 'current_period_end',
            'cancelled_at', 'created_at', 'updated_at'
        ]


class SubscriptionCreateSerializer(serializers.Serializer):
    """Serializer for creating a subscription."""
    
    tenant_id = serializers.IntegerField()
    plan_id = serializers.IntegerField()
    auto_renew = serializers.BooleanField(default=True)


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    subscription_details = serializers.SerializerMethodField()
    proof_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'subscription', 'subscription_details', 'tenant',
            'tenant_name', 'amount', 'currency', 'payment_method',
            'status', 'transaction_id', 'payment_gateway',
            'verification_status', 'verified_by', 'verified_at',
            'verification_notes', 'payment_proof', 'proof_url',
            'description', 'notes', 'created_at', 'updated_at', 'paid_at'
        ]
        read_only_fields = [
            'id', 'status', 'transaction_id', 'verification_status',
            'verified_by', 'verified_at', 'created_at', 'updated_at', 'paid_at'
        ]
    
    def get_subscription_details(self, obj):
        if obj.subscription:
            return {
                'plan_name': obj.subscription.plan.name,
                'billing_interval': obj.subscription.plan.billing_interval,
            }
        return None
    
    def get_proof_url(self, obj):
        if obj.payment_proof:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.payment_proof.url)
        return None


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a payment."""
    
    class Meta:
        model = Payment
        fields = [
            'subscription', 'tenant', 'amount', 'currency',
            'payment_method', 'payment_proof', 'description', 'notes'
        ]


class PaymentVerificationSerializer(serializers.Serializer):
    """Serializer for payment verification."""
    
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    notes = serializers.CharField(required=False, allow_blank=True)


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for Invoice Items."""
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'description', 'quantity', 'unit_price', 'amount'
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model."""
    
    items = InvoiceItemSerializer(many=True, read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    payment_status = serializers.CharField(
        source='payment.status' if 'payment' else None,
        read_only=True
    )
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'subscription', 'tenant', 'tenant_name', 'payment',
            'payment_status', 'invoice_number', 'status', 'subtotal',
            'tax_rate', 'tax_amount', 'discount_amount', 'total',
            'currency', 'issue_date', 'due_date', 'paid_at',
            'notes', 'terms', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'tax_amount', 'total',
            'paid_at', 'created_at', 'updated_at'
        ]


class InvoiceCreateSerializer(serializers.Serializer):
    """Serializer for creating invoices."""
    
    subscription_id = serializers.IntegerField()
    tenant_id = serializers.IntegerField()
    issue_date = serializers.DateField()
    due_date = serializers.DateField()
    items = InvoiceItemSerializer(many=True)
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    terms = serializers.CharField(required=False, allow_blank=True)
