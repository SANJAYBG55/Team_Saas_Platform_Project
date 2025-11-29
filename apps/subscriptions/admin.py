from django.contrib import admin
from .models import Plan, Subscription, Payment, Invoice, InvoiceItem


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'billing_interval', 'is_popular', 'is_active', 'sort_order']
    list_filter = ['billing_interval', 'is_popular', 'is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'plan', 'status', 'current_period_start', 'current_period_end', 'auto_renew']
    list_filter = ['status', 'auto_renew', 'plan']
    search_fields = ['tenant__name', 'tenant__company_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'tenant', 'amount', 'currency', 'payment_method',
        'status', 'verification_status', 'created_at'
    ]
    list_filter = ['status', 'verification_status', 'payment_method', 'created_at']
    search_fields = ['tenant__name', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at', 'verified_at', 'paid_at']


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'tenant', 'total', 'currency', 'status', 'issue_date', 'due_date']
    list_filter = ['status', 'issue_date']
    search_fields = ['invoice_number', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [InvoiceItemInline]
