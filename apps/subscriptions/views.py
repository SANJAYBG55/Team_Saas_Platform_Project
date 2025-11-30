"""
Views for subscriptions app.
"""
from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Plan, Subscription, Payment, Invoice, InvoiceItem
from .serializers import (
    PlanSerializer, SubscriptionSerializer, SubscriptionCreateSerializer,
    PaymentSerializer, PaymentCreateSerializer, PaymentVerificationSerializer,
    InvoiceSerializer, InvoiceCreateSerializer, InvoiceItemSerializer
)
from apps.core.permissions import IsSuperAdmin, IsTenantAdmin, IsApprovedTenant
from apps.core.utils import generate_invoice_number, log_activity


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Plan model (read-only for regular users)."""
    
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return Plan.objects.filter(is_active=True).order_by('sort_order', 'price')


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for Subscription model."""
    
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_super_admin:
            return Subscription.objects.all()
        elif user.tenant:
            return Subscription.objects.filter(tenant=user.tenant)
        return Subscription.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Create a new subscription."""
        serializer = SubscriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tenant_id = serializer.validated_data['tenant_id']
        plan_id = serializer.validated_data['plan_id']
        auto_renew = serializer.validated_data.get('auto_renew', True)
        
        from apps.tenants.models import Tenant
        tenant = get_object_or_404(Tenant, id=tenant_id)
        plan = get_object_or_404(Plan, id=plan_id)
        
        # Create subscription
        now = timezone.now()
        if plan.billing_interval == 'MONTHLY':
            period_end = now + timedelta(days=30)
        elif plan.billing_interval == 'QUARTERLY':
            period_end = now + timedelta(days=90)
        else:  # YEARLY
            period_end = now + timedelta(days=365)
        
        subscription = Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status='TRIAL' if plan.trial_days > 0 else 'ACTIVE',
            current_period_start=now,
            current_period_end=period_end,
            auto_renew=auto_renew,
            trial_start=now if plan.trial_days > 0 else None,
            trial_end=now + timedelta(days=plan.trial_days) if plan.trial_days > 0 else None
        )
        
        # Update tenant subscription
        tenant.subscription = subscription
        tenant.max_users = plan.max_users
        tenant.max_teams = plan.max_teams
        tenant.max_projects = plan.max_projects
        tenant.max_storage_gb = plan.max_storage_gb
        tenant.save()
        
        log_activity(
            user=request.user,
            action='CREATE',
            resource_type='SUBSCRIPTION',
            description=f'Subscription created for {tenant.name} - {plan.name}',
            tenant=tenant,
            request=request
        )
        
        return Response(
            SubscriptionSerializer(subscription, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a subscription."""
        subscription = self.get_object()
        immediately = request.data.get('immediately', False)
        
        subscription.cancel(immediately=immediately)
        
        log_activity(
            user=request.user,
            action='UPDATE',
            resource_type='SUBSCRIPTION',
            description=f'Subscription cancelled',
            tenant=subscription.tenant,
            request=request
        )
        
        return Response({
            'message': 'Subscription cancelled successfully'
        })
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Renew a subscription."""
        subscription = self.get_object()
        
        # Calculate new period
        now = timezone.now()
        plan = subscription.plan
        
        if plan.billing_interval == 'MONTHLY':
            period_end = now + timedelta(days=30)
        elif plan.billing_interval == 'QUARTERLY':
            period_end = now + timedelta(days=90)
        else:  # YEARLY
            period_end = now + timedelta(days=365)
        
        subscription.current_period_start = now
        subscription.current_period_end = period_end
        subscription.status = 'ACTIVE'
        subscription.save()
        
        log_activity(
            user=request.user,
            action='UPDATE',
            resource_type='SUBSCRIPTION',
            description=f'Subscription renewed',
            tenant=subscription.tenant,
            request=request
        )
        
        return Response({
            'message': 'Subscription renewed successfully'
        })


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment model."""
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def get_permissions(self):
        if self.action in ['verify']:
            return [IsSuperAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_super_admin:
            return Payment.objects.all()
        elif user.tenant:
            return Payment.objects.filter(tenant=user.tenant)
        return Payment.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Create a new payment."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment = serializer.save()
        
        # If manual payment with proof, set to pending verification
        if payment.payment_method == 'MANUAL' and payment.payment_proof:
            payment.verification_status = 'PENDING'
            payment.save()
        
        log_activity(
            user=request.user,
            action='CREATE',
            resource_type='PAYMENT',
            description=f'Payment created: ${payment.amount}',
            tenant=payment.tenant,
            request=request
        )
        
        return Response(
            PaymentSerializer(payment, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def verify(self, request, pk=None):
        """Verify a payment (admin only)."""
        payment = self.get_object()
        serializer = PaymentVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        
        if action_type == 'approve':
            payment.approve_verification(request.user, notes)
            message = 'Payment approved successfully'
            
            # Activate subscription if needed
            subscription = payment.subscription
            if subscription.status != 'ACTIVE':
                subscription.status = 'ACTIVE'
                subscription.save()
        else:
            payment.reject_verification(request.user, notes)
            message = 'Payment rejected'
        
        log_activity(
            user=request.user,
            action='UPDATE',
            resource_type='PAYMENT',
            description=f'Payment {action_type}d: ${payment.amount}',
            tenant=payment.tenant,
            request=request
        )
        
        return Response({
            'message': message,
            'payment': PaymentSerializer(payment, context={'request': request}).data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsSuperAdmin])
    def pending_verification(self, request):
        """Get all payments pending verification."""
        payments = Payment.objects.filter(
            verification_status='PENDING',
            payment_method='MANUAL'
        )
        
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Invoice model."""
    
    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_super_admin:
            return Invoice.objects.all()
        elif user.tenant:
            return Invoice.objects.filter(tenant=user.tenant)
        return Invoice.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Create a new invoice."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        subscription = get_object_or_404(Subscription, id=data['subscription_id'])
        tenant = get_object_or_404(Tenant, id=data['tenant_id'])
        
        # Calculate subtotal from items
        subtotal = Decimal('0.00')
        for item_data in data['items']:
            subtotal += item_data['quantity'] * item_data['unit_price']
        
        # Create invoice
        invoice = Invoice.objects.create(
            subscription=subscription,
            tenant=tenant,
            invoice_number=generate_invoice_number(),
            status='DRAFT',
            subtotal=subtotal,
            tax_rate=data.get('tax_rate', Decimal('0.00')),
            discount_amount=data.get('discount_amount', Decimal('0.00')),
            issue_date=data['issue_date'],
            due_date=data['due_date'],
            notes=data.get('notes', ''),
            terms=data.get('terms', '')
        )
        
        # Calculate total
        invoice.calculate_total()
        invoice.save()
        
        # Create invoice items
        for item_data in data['items']:
            InvoiceItem.objects.create(
                invoice=invoice,
                **item_data
            )
        
        log_activity(
            user=request.user,
            action='CREATE',
            resource_type='INVOICE',
            description=f'Invoice created: {invoice.invoice_number}',
            tenant=tenant,
            request=request
        )
        
        return Response(
            InvoiceSerializer(invoice, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def send(self, request, pk=None):
        """Send invoice to tenant."""
        invoice = self.get_object()
        invoice.status = 'SENT'
        invoice.save()
        
        # Send email notification
        # send_email(...)
        
        return Response({
            'message': 'Invoice sent successfully'
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid."""
        invoice = self.get_object()
        invoice.status = 'PAID'
        invoice.paid_at = timezone.now()
        invoice.save()
        
        return Response({
            'message': 'Invoice marked as paid'
        })


class BillingDashboardView(views.APIView):
    """Billing dashboard with statistics."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get billing dashboard data."""
        tenant = request.user.tenant
        
        if not tenant:
            return Response({
                'error': 'No tenant found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get current subscription
        subscription = tenant.subscription
        
        # Get payment history
        payments = Payment.objects.filter(tenant=tenant).order_by('-created_at')[:10]
        
        # Get invoices
        invoices = Invoice.objects.filter(tenant=tenant).order_by('-issue_date')[:10]
        
        return Response({
            'subscription': SubscriptionSerializer(subscription).data if subscription else None,
            'recent_payments': PaymentSerializer(payments, many=True).data,
            'recent_invoices': InvoiceSerializer(invoices, many=True).data,
            'stats': {
                'total_paid': Payment.objects.filter(
                    tenant=tenant,
                    status='COMPLETED'
                ).aggregate(total=models.Sum('amount'))['total'] or 0,
                'pending_payments': Payment.objects.filter(
                    tenant=tenant,
                    status='PENDING'
                ).count(),
                'overdue_invoices': Invoice.objects.filter(
                    tenant=tenant,
                    status='OVERDUE'
                ).count(),
            }
        })
