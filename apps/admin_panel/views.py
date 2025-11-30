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
def access_denied(request):
    """
    Access denied page for non-admin users trying to access admin panel.
    """
    return render(request, 'admin_panel/access_denied.html', status=403)
