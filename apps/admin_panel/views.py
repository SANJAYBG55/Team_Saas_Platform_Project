"""
Admin Panel Views
Handles internal admin dashboard, tenant management, approvals, and analytics.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import csv

from apps.tenants.models import Tenant
from apps.subscriptions.models import Subscription
from apps.accounts.models import User
from apps.notifications.models import Notification


def is_internal_admin(user):
    """Check if user is internal admin with special permissions."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_internal_admin, login_url='/admin-panel/access-denied/')
def admin_dashboard(request):
    """
    Main admin dashboard showing tenant overview, stats, and management tools.
    """
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    plan_filter = request.GET.get('plan', '')
    page_number = request.GET.get('page', 1)
    
    # Base queryset - Get tenant's most recent active subscription
    tenants = Tenant.objects.prefetch_related('subscriptions', 'domains').all()
    
    # Apply filters
    if search_query:
        tenants = tenants.filter(
            Q(name__icontains=search_query) |
            Q(slug__icontains=search_query) |
            Q(company_email__icontains=search_query)
        )
    
    if status_filter:
        tenants = tenants.filter(status=status_filter.upper())
    
    if plan_filter:
        tenants = tenants.filter(subscriptions__plan__id=plan_filter)
    
    # Order by created date (newest first)
    tenants = tenants.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tenants, 10)  # 10 tenants per page
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary stats
    total_tenants = Tenant.objects.count()
    pending_approvals = Tenant.objects.filter(status='PENDING').count()
    active_tenants = Tenant.objects.filter(status='ACTIVE').count()
    suspended_tenants = Tenant.objects.filter(status='SUSPENDED').count()
    
    # Calculate MRR (Monthly Recurring Revenue)
    active_subscriptions = Subscription.objects.filter(
        status='ACTIVE',
        tenant__status='ACTIVE'
    )
    total_mrr = 0
    for sub in active_subscriptions:
        if sub.plan.billing_interval == 'MONTHLY':
            total_mrr += float(sub.plan.price)
        elif sub.plan.billing_interval == 'YEARLY':
            total_mrr += float(sub.plan.price) / 12
        elif sub.plan.billing_interval == 'QUARTERLY':
            total_mrr += float(sub.plan.price) / 3
    
    # Total active users across all tenants
    active_users = User.objects.filter(is_active=True).count()
    
    # Recent activity (last 10 events)
    recent_activity = []
    
    # Get recent tenant registrations
    recent_tenants = Tenant.objects.order_by('-created_at')[:5]
    for tenant in recent_tenants:
        recent_activity.append({
            'type': 'tenant_created',
            'icon': 'fa-building',
            'color': 'primary',
            'message': f'New tenant: {tenant.name}',
            'time': tenant.created_at,
        })
    
    # Get recent approvals
    recent_approvals = Tenant.objects.filter(
        status='ACTIVE',
        approved_at__isnull=False
    ).order_by('-approved_at')[:3]
    for tenant in recent_approvals:
        recent_activity.append({
            'type': 'tenant_approved',
            'icon': 'fa-check-circle',
            'color': 'success',
            'message': f'Approved: {tenant.name}',
            'time': tenant.approved_at,
        })
    
    # Sort by time and limit to 10
    recent_activity = sorted(recent_activity, key=lambda x: x['time'], reverse=True)[:10]
    
    # Quick stats for sidebar
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_tenants_30d = Tenant.objects.filter(created_at__gte=thirty_days_ago).count()
    conversion_rate = (active_tenants / total_tenants * 100) if total_tenants > 0 else 0
    
    # Average revenue per tenant
    avg_revenue = total_mrr / active_tenants if active_tenants > 0 else 0
    
    # Churn rate (tenants that became inactive in last 30 days)
    churned_tenants = Tenant.objects.filter(
        status='CANCELLED',
        updated_at__gte=thirty_days_ago
    ).count()
    churn_rate = (churned_tenants / active_tenants * 100) if active_tenants > 0 else 0
    
    context = {
        'total_tenants': total_tenants,
        'pending_approvals': pending_approvals,
        'active_tenants': active_tenants,
        'suspended_tenants': suspended_tenants,
        'monthly_revenue': total_mrr,
        'active_users': active_users,
        'tenants': page_obj,
        'page_obj': page_obj,
        'recent_activity': recent_activity,
        'new_tenants_30d': new_tenants_30d,
        'conversion_rate': round(conversion_rate, 1),
        'avg_revenue': round(avg_revenue, 2),
        'churn_rate': round(churn_rate, 1),
        # Filters for form state
        'search_query': search_query,
        'status_filter': status_filter,
        'plan_filter': plan_filter,
    }
    
    return render(request, 'admin_panel/dashboard_enhanced.html', context)


@login_required
@user_passes_test(is_internal_admin)
def tenant_detail(request, tenant_id):
    """
    Detailed view of a specific tenant with full information.
    """
    tenant = get_object_or_404(Tenant, id=tenant_id)
    users = tenant.users.all()
    
    context = {
        'tenant': tenant,
        'users': users,
    }
    
    return render(request, 'admin_panel/tenant_detail.html', context)


# =============================
# API Endpoints (AJAX)
# =============================

@login_required
@user_passes_test(is_internal_admin)
@require_http_methods(["POST"])
def approve_tenant(request, tenant_id):
    """
    Approve a pending tenant.
    """
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if tenant.status != 'PENDING':
        return JsonResponse({
            'success': False,
            'message': 'Tenant is not in pending status'
        }, status=400)
    
    tenant.status = 'ACTIVE'
    tenant.is_approved = True
    tenant.approved_at = timezone.now()
    tenant.approved_by = request.user
    tenant.save()
    
    # Send approval notification to tenant admin
    # TODO: Implement email notification
    
    return JsonResponse({
        'success': True,
        'message': 'Tenant approved successfully',
        'status': tenant.status
    })


@login_required
@user_passes_test(is_internal_admin)
@require_http_methods(["POST"])
def toggle_tenant_status(request, tenant_id):
    """
    Toggle tenant status between active and suspended.
    """
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if tenant.status == 'ACTIVE':
        tenant.status = 'SUSPENDED'
    elif tenant.status == 'SUSPENDED':
        tenant.status = 'ACTIVE'
    else:
        return JsonResponse({
            'success': False,
            'message': 'Cannot toggle status for pending tenants'
        }, status=400)
    
    tenant.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Tenant {tenant.status} successfully',
        'status': tenant.status
    })


@login_required
@user_passes_test(is_internal_admin)
@require_http_methods(["POST"])
def send_tenant_message(request, tenant_id):
    """
    Send a message/notification to a tenant.
    """
    import json
    
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    try:
        data = json.loads(request.body)
        subject = data.get('subject')
        body = data.get('body')
        
        if not subject or not body:
            return JsonResponse({
                'success': False,
                'message': 'Subject and body are required'
            }, status=400)
        
        # Create notification for all tenant users
        for user in tenant.users.all():
            Notification.objects.create(
                user=user,
                title=subject,
                message=body,
                type='admin_message',
                tenant=tenant
            )
        
        # TODO: Also send email
        
        return JsonResponse({
            'success': True,
            'message': 'Message sent successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)


@login_required
@user_passes_test(is_internal_admin)
@require_http_methods(["POST"])
def create_tenant(request):
    """
    Create a new tenant manually (admin-created).
    """
    import json
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['name', 'domain', 'admin_email', 'admin_name', 'plan_id']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'message': f'{field} is required'
                }, status=400)
        
        # Check if domain already exists
        if Tenant.objects.filter(domain=data['domain']).exists():
            return JsonResponse({
                'success': False,
                'message': 'Domain already exists'
            }, status=400)
        
        # Create tenant
        from django.utils.text import slugify
        tenant = Tenant.objects.create(
            name=data['name'],
            company_name=data['name'],
            slug=slugify(data['domain']),
            company_email=data['admin_email'],
            status='ACTIVE' if data.get('auto_approve') else 'PENDING',
            is_approved=bool(data.get('auto_approve')),
            approved_by=request.user if data.get('auto_approve') else None,
            approved_at=timezone.now() if data.get('auto_approve') else None
        )
        
        # Create subscription
        from apps.subscriptions.models import Plan
        plan = get_object_or_404(Plan, id=data['plan_id'])
        
        Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status='ACTIVE' if data.get('auto_approve') else 'PENDING',
            start_date=timezone.now()
        )
        
        # Create admin user for tenant
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        admin_user = User.objects.create_user(
            email=data['admin_email'],
            username=data['admin_email'].split('@')[0],
            first_name=data['admin_name'].split()[0] if ' ' in data['admin_name'] else data['admin_name'],
            last_name=data['admin_name'].split()[1] if ' ' in data['admin_name'] else '',
            tenant=tenant,
            role='owner'
        )
        
        # TODO: Send welcome email with password setup link
        
        return JsonResponse({
            'success': True,
            'message': 'Tenant created successfully',
            'tenant_id': tenant.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_internal_admin)
def export_tenants(request):
    """
    Export tenants to CSV based on current filters.
    """
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    plan_filter = request.GET.get('plan', '')
    
    # Base queryset
    tenants = Tenant.objects.prefetch_related('subscriptions').all()
    
    # Apply filters (same as dashboard)
    if search_query:
        tenants = tenants.filter(
            Q(name__icontains=search_query) |
            Q(slug__icontains=search_query) |
            Q(company_email__icontains=search_query)
        )
    
    if status_filter:
        tenants = tenants.filter(status=status_filter.upper())
    
    if plan_filter:
        tenants = tenants.filter(subscriptions__plan__id=plan_filter)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="tenants_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Slug', 'Company Email', 'Status', 'Plan', 'Created At', 'Users Count'])
    
    for tenant in tenants:
        # Get primary domain if exists
        primary_domain = tenant.domains.filter(is_primary=True).first()
        domain_str = primary_domain.domain if primary_domain else tenant.slug
        
        # Get active subscription
        active_sub = tenant.subscriptions.filter(status='ACTIVE').first()
        plan_name = active_sub.plan.name if active_sub else 'N/A'
        
        writer.writerow([
            tenant.id,
            tenant.name,
            tenant.slug,
            tenant.company_email,
            tenant.status,
            plan_name,
            tenant.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            tenant.current_users_count
        ])
    
    return response


@login_required
@user_passes_test(is_internal_admin)
def payment_verification(request):
    """
    Payment verification page showing all payment submissions for review.
    """
    from apps.subscriptions.models import Payment
    from datetime import date
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    method_filter = request.GET.get('method', '')
    page_number = request.GET.get('page', 1)
    
    # Base queryset
    payments = Payment.objects.select_related('tenant', 'subscription').all()
    
    # Apply filters
    if search_query:
        payments = payments.filter(
            Q(tenant__name__icontains=search_query) |
            Q(tenant__company_email__icontains=search_query) |
            Q(transaction_id__icontains=search_query)
        )
    
    if status_filter:
        payments = payments.filter(verification_status=status_filter.upper())
    
    if method_filter:
        payments = payments.filter(payment_method=method_filter.upper())
    
    # Order by created date (newest first)
    payments = payments.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(payments, 15)  # 15 payments per page
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary stats
    pending_payments = Payment.objects.filter(verification_status='PENDING').count()
    
    today = date.today()
    approved_today = Payment.objects.filter(
        verification_status='APPROVED',
        verified_at__date=today
    ).count()
    
    rejected_today = Payment.objects.filter(
        verification_status='REJECTED',
        verified_at__date=today
    ).count()
    
    # Week stats
    week_start = timezone.now() - timedelta(days=7)
    approved_this_week = Payment.objects.filter(
        verification_status='APPROVED',
        verified_at__gte=week_start
    ).count()
    
    rejected_this_week = Payment.objects.filter(
        verification_status='REJECTED',
        verified_at__gte=week_start
    ).count()
    
    # Total pending amount
    from django.db.models import Sum
    total_pending_amount = Payment.objects.filter(
        verification_status='PENDING'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'payments': page_obj,
        'page_obj': page_obj,
        'pending_payments': pending_payments,
        'approved_today': approved_today,
        'rejected_today': rejected_today,
        'approved_this_week': approved_this_week,
        'rejected_this_week': rejected_this_week,
        'total_pending_amount': total_pending_amount,
        # Filters for form state
        'search_query': search_query,
        'status_filter': status_filter,
        'method_filter': method_filter,
    }
    
    return render(request, 'admin_panel/payment_verification.html', context)


@login_required
@user_passes_test(is_internal_admin)
@require_http_methods(["GET"])
def payment_detail(request, payment_id):
    """
    Get payment details as JSON.
    """
    from apps.subscriptions.models import Payment
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    data = {
        'success': True,
        'payment': {
            'id': payment.id,
            'amount': str(payment.amount),
            'currency': payment.currency,
            'payment_method': payment.get_payment_method_display(),
            'transaction_id': payment.transaction_id,
            'verification_status': payment.verification_status,
            'description': payment.description,
            'notes': payment.notes,
            'payment_proof': payment.payment_proof.url if payment.payment_proof else None,
            'created_at': payment.created_at.isoformat(),
            'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
            'verified_at': payment.verified_at.isoformat() if payment.verified_at else None,
            'verified_by_name': payment.verified_by.get_full_name() if payment.verified_by else None,
            'verification_notes': payment.verification_notes,
            'tenant': {
                'id': payment.tenant.id,
                'name': payment.tenant.name,
                'slug': payment.tenant.slug,
                'company_email': payment.tenant.company_email,
            },
            'subscription': {
                'id': payment.subscription.id,
                'plan_name': payment.subscription.plan.name,
            } if payment.subscription else None,
        }
    }
    
    return JsonResponse(data)


@login_required
@user_passes_test(is_internal_admin)
@require_http_methods(["POST"])
def approve_payment(request, payment_id):
    """
    Approve a payment verification.
    """
    import json
    from apps.subscriptions.models import Payment
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.verification_status != 'PENDING':
        return JsonResponse({
            'success': False,
            'message': 'Payment is not in pending status'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        notes = data.get('notes', '')
        
        # Approve payment
        payment.approve_verification(request.user, notes)
        
        # Also approve tenant if still pending
        if payment.tenant.status == 'PENDING':
            payment.tenant.status = 'ACTIVE'
            payment.tenant.is_approved = True
            payment.tenant.approved_at = timezone.now()
            payment.tenant.approved_by = request.user
            payment.tenant.save()
        
        # Activate subscription
        if payment.subscription and payment.subscription.status != 'ACTIVE':
            payment.subscription.status = 'ACTIVE'
            payment.subscription.save()
        
        # TODO: Send email notification to tenant
        
        return JsonResponse({
            'success': True,
            'message': 'Payment approved successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_internal_admin)
@require_http_methods(["POST"])
def reject_payment(request, payment_id):
    """
    Reject a payment verification.
    """
    import json
    from apps.subscriptions.models import Payment
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.verification_status != 'PENDING':
        return JsonResponse({
            'success': False,
            'message': 'Payment is not in pending status'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        notes = data.get('notes', '')
        
        if not notes:
            return JsonResponse({
                'success': False,
                'message': 'Rejection reason is required'
            }, status=400)
        
        # Reject payment
        payment.reject_verification(request.user, notes)
        
        # TODO: Send email notification to tenant with rejection reason
        
        return JsonResponse({
            'success': True,
            'message': 'Payment rejected'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@user_passes_test(is_internal_admin)
def export_payments(request):
    """
    Export payments to CSV based on current filters.
    """
    from apps.subscriptions.models import Payment
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    method_filter = request.GET.get('method', '')
    
    # Base queryset
    payments = Payment.objects.select_related('tenant', 'subscription').all()
    
    # Apply filters
    if search_query:
        payments = payments.filter(
            Q(tenant__name__icontains=search_query) |
            Q(tenant__company_email__icontains=search_query) |
            Q(transaction_id__icontains=search_query)
        )
    
    if status_filter:
        payments = payments.filter(verification_status=status_filter.upper())
    
    if method_filter:
        payments = payments.filter(payment_method=method_filter.upper())
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="payments_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Tenant', 'Amount', 'Currency', 'Method', 'Transaction ID', 'Status', 'Submitted', 'Verified', 'Verified By'])
    
    for payment in payments:
        writer.writerow([
            payment.id,
            payment.tenant.name,
            str(payment.amount),
            payment.currency,
            payment.get_payment_method_display(),
            payment.transaction_id or 'N/A',
            payment.verification_status,
            payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            payment.verified_at.strftime('%Y-%m-%d %H:%M:%S') if payment.verified_at else 'N/A',
            payment.verified_by.get_full_name() if payment.verified_by else 'N/A'
        ])
    
    return response


@login_required
def access_denied(request):
    """
    Access denied page for non-admin users trying to access admin panel.
    """
    return render(request, 'admin_panel/access_denied.html', status=403)


@login_required
@user_passes_test(is_internal_admin, login_url='admin_panel:access_denied')
def analytics(request):
    """
    Analytics and reports dashboard for admins.
    Displays revenue metrics, tenant growth, user engagement, and business KPIs.
    """
    from django.db.models import Count, Sum, Avg, Q, F
    from django.utils import timezone
    from datetime import timedelta, datetime
    from apps.tenants.models import Tenant
    from apps.subscriptions.models import Subscription, Payment
    from django.contrib.auth import get_user_model
    from apps.tasks.models import Task
    import json
    
    User = get_user_model()
    
    # Get time range from query params (default: 30 days)
    time_range = request.GET.get('range', '30')
    
    try:
        days = int(time_range)
    except (ValueError, TypeError):
        days = 30
    
    if days == 0:  # All time
        start_date = None
    else:
        start_date = timezone.now() - timedelta(days=days)
    
    # ==================== Revenue Metrics ====================
    
    # Total revenue from all approved payments
    total_revenue_qs = Payment.objects.filter(
        verification_status='approved'
    )
    if start_date:
        total_revenue_qs = total_revenue_qs.filter(created_at__gte=start_date)
    
    total_revenue = total_revenue_qs.aggregate(total=Sum('amount'))['total'] or 0
    
    # MRR calculation (Monthly Recurring Revenue)
    active_subscriptions = Subscription.objects.filter(
        status='active',
        tenant__status='active'
    ).select_related('plan')
    
    mrr = 0
    for sub in active_subscriptions:
        if sub.plan.billing_interval == 'MONTHLY':
            mrr += float(sub.plan.price)
        elif sub.plan.billing_interval == 'YEARLY':
            mrr += float(sub.plan.price) / 12
        elif sub.plan.billing_interval == 'QUARTERLY':
            mrr += float(sub.plan.price) / 3
    
    # ==================== Tenant Metrics ====================
    
    # Total tenants count
    total_tenants = Tenant.objects.count()
    
    # Active tenants
    active_tenants = Tenant.objects.filter(status='active').count()
    
    # New tenants in time range
    new_tenants_qs = Tenant.objects.all()
    if start_date:
        new_tenants_qs = new_tenants_qs.filter(created_at__gte=start_date)
    new_tenants_count = new_tenants_qs.count()
    
    # ==================== User Metrics ====================
    
    # Active users (have logged in within last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    active_users = User.objects.filter(
        last_login__gte=thirty_days_ago
    ).count()
    
    # New users in time range
    new_users_qs = User.objects.all()
    if start_date:
        new_users_qs = new_users_qs.filter(date_joined__gte=start_date)
    new_users_count = new_users_qs.count()
    
    # Average users per tenant
    total_users = User.objects.count()
    avg_users_per_tenant = round(total_users / total_tenants, 1) if total_tenants > 0 else 0
    
    # ==================== Conversion Metrics ====================
    
    # Total signups
    total_signups = Tenant.objects.count()
    
    # Converted tenants (approved and active)
    converted_tenants = Tenant.objects.filter(
        is_approved=True,
        status='active'
    ).count()
    
    # Conversion rate
    conversion_rate = round((converted_tenants / total_signups * 100), 1) if total_signups > 0 else 0
    
    # ==================== Top Tenants by Revenue ====================
    
    # Get top 10 tenants by revenue
    top_tenants = Tenant.objects.filter(
        status='active'
    ).annotate(
        revenue=Sum('subscription__payment__amount', filter=Q(subscription__payment__verification_status='approved')),
        users_count=Count('users')
    ).select_related(
        'subscription__plan'
    ).order_by('-revenue')[:10]
    
    # Format top tenants data
    top_tenants_data = []
    for tenant in top_tenants:
        plan_name = tenant.subscription.plan.name if hasattr(tenant, 'subscription') and tenant.subscription else 'No Plan'
        top_tenants_data.append({
            'name': tenant.name,
            'plan_name': plan_name,
            'revenue': tenant.revenue or 0,
            'users_count': tenant.users_count
        })
    
    # ==================== Recent Signups ====================
    
    # Get 10 most recent tenant registrations
    recent_signups = Tenant.objects.select_related(
        'subscription__plan'
    ).order_by('-created_at')[:10]
    
    # Format recent signups data
    recent_signups_data = []
    for tenant in recent_signups:
        plan_name = tenant.subscription.plan.name if hasattr(tenant, 'subscription') and tenant.subscription else 'No Plan'
        recent_signups_data.append({
            'name': tenant.name,
            'plan_name': plan_name,
            'is_approved': tenant.is_approved,
            'created_at': tenant.created_at
        })
    
    # ==================== System Health Metrics ====================
    
    # These would typically come from monitoring systems
    # For now, we'll use mock data or simple calculations
    
    # Average response time (mock - would come from APM)
    avg_response_time = 120  # milliseconds
    
    # API success rate (calculate from logs if available)
    api_success_rate = 99.2
    
    # Database load (mock - would come from DB monitoring)
    db_load = 45
    
    # ==================== Business Metrics ====================
    
    # ARPU (Average Revenue Per User)
    arpu = round(total_revenue / active_users, 2) if active_users > 0 else 0
    
    # Churn rate (tenants that became inactive in last 30 days)
    churned_tenants = Tenant.objects.filter(
        status='suspended',
        updated_at__gte=thirty_days_ago
    ).count()
    churn_rate = round((churned_tenants / total_tenants * 100), 1) if total_tenants > 0 else 0
    
    # Retention rate
    retention_rate = round(100 - churn_rate, 1)
    
    # ==================== Chart Data ====================
    
    # Revenue chart data (last 12 months)
    revenue_chart_data = []
    for i in range(11, -1, -1):
        month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        month_revenue = Payment.objects.filter(
            verification_status='approved',
            created_at__gte=month_start,
            created_at__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        revenue_chart_data.append({
            'month': month_start.strftime('%b'),
            'revenue': float(month_revenue)
        })
    
    # Tenant growth chart data (last 12 months)
    tenant_growth_data = []
    for i in range(11, -1, -1):
        month_end = timezone.now().replace(day=1) - timedelta(days=30 * i)
        
        cumulative_tenants = Tenant.objects.filter(
            created_at__lte=month_end
        ).count()
        
        tenant_growth_data.append({
            'month': month_end.strftime('%b'),
            'tenants': cumulative_tenants
        })
    
    # User engagement data (last 4 weeks)
    engagement_data = []
    for i in range(3, -1, -1):
        week_start = timezone.now() - timedelta(days=7 * (i + 1))
        week_end = timezone.now() - timedelta(days=7 * i)
        
        week_active_users = User.objects.filter(
            last_login__gte=week_start,
            last_login__lt=week_end
        ).count()
        
        week_tasks = Task.objects.filter(
            created_at__gte=week_start,
            created_at__lt=week_end
        ).count()
        
        engagement_data.append({
            'week': f'Week {4 - i}',
            'active_users': week_active_users,
            'tasks_created': week_tasks
        })
    
    # Plan distribution data
    plan_distribution = Subscription.objects.filter(
        status='active'
    ).values(
        'plan__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    plan_distribution_data = [
        {
            'plan': item['plan__name'],
            'count': item['count']
        }
        for item in plan_distribution
    ]
    
    # ==================== Context ====================
    
    context = {
        # Revenue metrics
        'total_revenue': round(total_revenue, 2),
        'mrr': round(mrr, 2),
        'new_tenants_count': new_tenants_count,
        
        # Tenant metrics
        'active_tenants': active_tenants,
        'total_tenants': total_tenants,
        
        # User metrics
        'active_users': active_users,
        'new_users_count': new_users_count,
        'avg_users_per_tenant': avg_users_per_tenant,
        
        # Conversion metrics
        'conversion_rate': conversion_rate,
        'converted_tenants': converted_tenants,
        'total_signups': total_signups,
        
        # Lists
        'top_tenants': top_tenants_data,
        'recent_signups': recent_signups_data,
        
        # System health
        'avg_response_time': avg_response_time,
        'api_success_rate': api_success_rate,
        'db_load': db_load,
        
        # Business metrics
        'arpu': arpu,
        'churn_rate': churn_rate,
        'retention_rate': retention_rate,
        
        # Chart data (for JavaScript) - JSON serialized
        'revenue_chart_data': json.dumps(revenue_chart_data),
        'tenant_growth_data': json.dumps(tenant_growth_data),
        'engagement_data': json.dumps(engagement_data),
        'plan_distribution_data': json.dumps(plan_distribution_data),
        
        # Current time range
        'time_range': days,
    }
    
    return render(request, 'admin_panel/analytics.html', context)


@login_required
@user_passes_test(is_internal_admin, login_url='admin_panel:access_denied')
def audit_logs(request):
    """
    Audit logs viewer for tracking admin actions.
    """
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    from apps.core.models import AuditLog
    from django.contrib.auth import get_user_model
    from django.core.paginator import Paginator
    
    User = get_user_model()
    
    # Get filter parameters
    user_filter = request.GET.get('user', '')
    target_model_filter = request.GET.get('target_model', '')
    action_filter = request.GET.get('action', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    logs = AuditLog.objects.select_related('admin_user').all()
    
    # Apply filters
    if user_filter:
        logs = logs.filter(admin_user_id=user_filter)
    
    if target_model_filter:
        logs = logs.filter(target_model__icontains=target_model_filter)
    
    if action_filter:
        logs = logs.filter(action__icontains=action_filter)
    
    if date_from:
        logs = logs.filter(created_at__gte=date_from)
    
    if date_to:
        # Add one day to include the entire end date
        from datetime import datetime
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        date_to_obj = date_to_obj + timedelta(days=1)
        logs = logs.filter(created_at__lt=date_to_obj)
    
    if search_query:
        logs = logs.filter(
            Q(target_description__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # Get total count before pagination
    total_logs = logs.count()
    
    # Calculate statistics
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    
    today_logs = AuditLog.objects.filter(created_at__gte=today_start).count()
    week_logs = AuditLog.objects.filter(created_at__gte=week_start).count()
    
    # Active admins (admins who performed actions in last 7 days)
    active_admins = AuditLog.objects.filter(
        created_at__gte=week_start
    ).values('admin_user').distinct().count()
    
    # Get list of admin users for filter
    admin_users = User.objects.filter(
        Q(is_staff=True) | Q(is_superuser=True)
    ).order_by('first_name', 'last_name')
    
    # Get unique target models for filter
    target_models = AuditLog.objects.values_list(
        'target_model', flat=True
    ).distinct().order_by('target_model')
    
    # Pagination
    paginator = Paginator(logs, 20)  # 20 logs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'audit_logs': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_logs': total_logs,
        'today_logs': today_logs,
        'week_logs': week_logs,
        'active_admins': active_admins,
        'admin_users': admin_users,
        'target_models': target_models,
    }
    
    return render(request, 'admin_panel/audit_logs.html', context)


@require_http_methods(["GET"])
@login_required
@user_passes_test(is_internal_admin, login_url='admin_panel:access_denied')
def audit_log_detail(request, log_id):
    """
    Get details of a specific audit log entry.
    """
    from apps.core.models import AuditLog
    from django.http import JsonResponse
    
    try:
        log = AuditLog.objects.select_related('admin_user').get(id=log_id)
        
        data = {
            'success': True,
            'log': {
                'id': log.id,
                'admin_user': log.admin_user.get_full_name() if log.admin_user else 'System',
                'action': log.action,
                'target_model': log.target_model,
                'target_id': log.target_id,
                'target_description': log.target_description,
                'old_values': log.old_values,
                'new_values': log.new_values,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'notes': log.notes,
                'created_at': log.created_at.strftime('%B %d, %Y at %I:%M %p'),
            }
        }
        
        return JsonResponse(data)
    except AuditLog.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Log not found'}, status=404)


@require_http_methods(["GET"])
@login_required
@user_passes_test(is_internal_admin, login_url='admin_panel:access_denied')
def export_audit_logs(request):
    """
    Export audit logs to CSV.
    """
    from django.http import HttpResponse
    from django.utils import timezone
    from datetime import timedelta
    from apps.core.models import AuditLog
    from django.db.models import Q
    import csv
    
    # Get filter parameters (same as audit_logs view)
    user_filter = request.GET.get('user', '')
    target_model_filter = request.GET.get('target_model', '')
    action_filter = request.GET.get('action', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    logs = AuditLog.objects.select_related('admin_user').all()
    
    # Apply filters
    if user_filter:
        logs = logs.filter(admin_user_id=user_filter)
    
    if target_model_filter:
        logs = logs.filter(target_model__icontains=target_model_filter)
    
    if action_filter:
        logs = logs.filter(action__icontains=action_filter)
    
    if date_from:
        logs = logs.filter(created_at__gte=date_from)
    
    if date_to:
        from datetime import datetime
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        date_to_obj = date_to_obj + timedelta(days=1)
        logs = logs.filter(created_at__lt=date_to_obj)
    
    if search_query:
        logs = logs.filter(
            Q(target_description__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="audit_logs_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Admin User', 'Action', 'Target Model', 'Target ID', 
        'Description', 'IP Address', 'Timestamp', 'Notes'
    ])
    
    for log in logs:
        writer.writerow([
            log.id,
            log.admin_user.get_full_name() if log.admin_user else 'System',
            log.action,
            log.target_model,
            log.target_id or 'N/A',
            log.target_description,
            log.ip_address or 'N/A',
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.notes or ''
        ])
    
    return response
