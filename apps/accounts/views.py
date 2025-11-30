"""
Views for accounts app.
"""
from rest_framework import generics, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.utils import timezone
from datetime import timedelta

from .models import User, UserPreference, EmailVerification, PasswordReset
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, LoginSerializer, UserPreferenceSerializer
)
from apps.core.utils import generate_token, send_email, log_activity


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create user preferences
        UserPreference.objects.create(user=user)
        
        # Send verification email
        token = generate_token()
        EmailVerification.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        # Send email (implement later)
        # send_email(...)
        
        return Response({
            'message': 'Registration successful. Please verify your email.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    """User login endpoint."""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Update last login
        user.last_login = timezone.now()
        user.save()
        
        # Log activity
        log_activity(
            user=user,
            action='LOGIN',
            resource_type='AUTH',
            description='User logged in',
            tenant=user.tenant,
            request=request
        )
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class LogoutView(views.APIView):
    """User logout endpoint."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        log_activity(
            user=request.user,
            action='LOGOUT',
            resource_type='AUTH',
            description='User logged out',
            tenant=request.user.tenant,
            request=request
        )
        
        logout(request)
        
        return Response({
            'message': 'Logout successful'
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserUpdateSerializer


class ChangePasswordView(views.APIView):
    """Change password endpoint."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Old password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        log_activity(
            user=user,
            action='UPDATE',
            resource_type='USER',
            description='Password changed',
            tenant=user.tenant,
            request=request
        )
        
        return Response({
            'message': 'Password changed successfully'
        })


class UserPreferenceView(generics.RetrieveUpdateAPIView):
    """User preferences view."""
    
    permission_classes = [IsAuthenticated]
    serializer_class = UserPreferenceSerializer
    
    def get_object(self):
        obj, created = UserPreference.objects.get_or_create(user=self.request.user)
        return obj


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """Request password reset."""
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        # Generate reset token
        token = generate_token()
        PasswordReset.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Send email (implement later)
        # send_email(...)
        
        return Response({
            'message': 'Password reset email sent'
        })
    
    except User.DoesNotExist:
        # Don't reveal if user exists
        return Response({
            'message': 'Password reset email sent'
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password with token."""
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not token or not new_password:
        return Response({
            'error': 'Token and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        reset = PasswordReset.objects.get(
            token=token,
            is_used=False,
            expires_at__gt=timezone.now()
        )
        
        user = reset.user
        user.set_password(new_password)
        user.save()
        
        reset.is_used = True
        reset.save()
        
        return Response({
            'message': 'Password reset successful'
        })
    
    except PasswordReset.DoesNotExist:
        return Response({
            'error': 'Invalid or expired token'
        }, status=status.HTTP_400_BAD_REQUEST)


# =============================
# Tenant Signup Views
# =============================

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.utils.text import slugify


def signup_page(request):
    """Render the signup page."""
    return render(request, 'auth/signup.html')


@login_required
def profile_page(request):
    """Render the profile & settings page."""
    # Check if user has approved tenant
    if not request.user.tenant or not request.user.tenant.is_approved:
        return redirect('pending_approval')
    
    # Ensure user has preferences
    from .models import UserPreference
    if not hasattr(request.user, 'preferences'):
        UserPreference.objects.create(user=request.user)
    
    return render(request, 'tenant/profile.html')


@api_view(['GET'])
@permission_classes([AllowAny])
def check_domain_availability(request):
    """Check if domain is available."""
    from apps.tenants.models import Tenant
    
    domain = request.GET.get('domain', '').lower().strip()
    
    if not domain:
        return Response({
            'available': False,
            'message': 'Domain is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if domain exists
    exists = Tenant.objects.filter(slug=domain).exists()
    
    return Response({
        'available': not exists,
        'domain': domain
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_plans(request):
    """Get all available subscription plans."""
    from apps.subscriptions.models import Plan
    
    plans = Plan.objects.filter(is_active=True).order_by('sort_order', 'price')
    
    plans_data = []
    for plan in plans:
        plans_data.append({
            'id': plan.id,
            'name': plan.name,
            'slug': plan.slug,
            'description': plan.description,
            'price_monthly': float(plan.price) if plan.billing_interval == 'MONTHLY' else float(plan.price),
            'price_annual': float(plan.price) if plan.billing_interval == 'YEARLY' else float(plan.price * 12 * 0.8),  # 20% discount
            'currency': plan.currency,
            'max_users': plan.max_users,
            'max_teams': plan.max_teams,
            'max_projects': plan.max_projects,
            'max_storage_gb': plan.max_storage_gb,
            'enable_api_access': plan.enable_api_access,
            'enable_priority_support': plan.enable_priority_support,
            'enable_custom_branding': plan.enable_custom_branding,
            'enable_sso': plan.enable_sso,
            'is_popular': plan.is_popular,
            'trial_days': plan.trial_days
        })
    
    return Response({
        'success': True,
        'plans': plans_data
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def complete_signup(request):
    """Complete the signup process."""
    from apps.tenants.models import Tenant, Domain
    from apps.subscriptions.models import Plan, Subscription, Payment
    from django.db import transaction
    
    try:
        # Get form data
        data = request.data
        
        company_name = data.get('company_name')
        domain = data.get('domain', '').lower().strip()
        admin_name = data.get('admin_name')
        email = data.get('email')
        password = data.get('password')
        plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle', 'monthly')
        payment_method = data.get('payment_method', 'card')
        stripe_payment_method = data.get('stripe_payment_method')
        
        # Validate required fields
        if not all([company_name, domain, admin_name, email, password, plan_id]):
            return Response({
                'success': False,
                'message': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if domain is taken
        if Tenant.objects.filter(slug=domain).exists():
            return Response({
                'success': False,
                'message': 'Domain is already taken'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email is taken
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'message': 'Email is already registered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get plan
        plan = Plan.objects.get(id=plan_id)
        
        # Calculate trial end date
        trial_end = timezone.now() + timedelta(days=plan.trial_days)
        
        with transaction.atomic():
            # Create tenant
            tenant = Tenant.objects.create(
                name=company_name,
                company_name=company_name,
                slug=domain,
                company_email=email,
                status='PENDING',
                is_approved=False,
                trial_ends_at=trial_end,
                max_users=plan.max_users,
                max_teams=plan.max_teams,
                max_projects=plan.max_projects,
                max_storage_gb=plan.max_storage_gb
            )
            
            # Create domain
            Domain.objects.create(
                tenant=tenant,
                domain=f"{domain}.yourdomain.com",
                domain_type='SUBDOMAIN',
                is_primary=True,
                is_verified=False
            )
            
            # Create admin user
            name_parts = admin_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            user = User.objects.create_user(
                email=email,
                username=email.split('@')[0],
                password=password,
                first_name=first_name,
                last_name=last_name,
                tenant=tenant,
                role='OWNER',
                is_active=True
            )
            
            # Create user preferences
            UserPreference.objects.create(user=user)
            
            # Create subscription
            subscription = Subscription.objects.create(
                tenant=tenant,
                plan=plan,
                status='TRIAL',
                current_period_start=timezone.now(),
                current_period_end=trial_end,
                trial_start=timezone.now(),
                trial_end=trial_end,
                auto_renew=True
            )
            
            # Create payment record
            payment_amount = plan.price if billing_cycle == 'monthly' else plan.price * 12 * 0.8
            
            payment = Payment.objects.create(
                subscription=subscription,
                tenant=tenant,
                amount=payment_amount,
                currency=plan.currency,
                payment_method=payment_method.upper(),
                status='PENDING',
                verification_status='PENDING',
                description=f'Signup payment for {plan.name} plan'
            )
            
            # Handle Stripe payment method
            if payment_method == 'card' and stripe_payment_method:
                payment.transaction_id = stripe_payment_method
                payment.payment_gateway = 'stripe'
                # In production, you would charge the card after trial
                # For now, just save the payment method for later
            
            # Handle payment proof upload
            if 'payment_proof' in request.FILES:
                payment.payment_proof = request.FILES['payment_proof']
                payment.save()
            
            # Send verification email
            token = generate_token()
            EmailVerification.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(days=1)
            )
            
            # TODO: Send welcome email with verification link
            # TODO: Send notification to admins about new signup
            
            return Response({
                'success': True,
                'message': 'Signup successful! Please check your email to verify your account.',
                'tenant_id': tenant.id,
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
    
    except Plan.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Invalid plan selected'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """Resend verification email."""
    email = request.data.get('email')
    
    if not email:
        return Response({
            'success': False,
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        # Delete old verification tokens
        EmailVerification.objects.filter(user=user, is_verified=False).delete()
        
        # Create new token
        token = generate_token()
        EmailVerification.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        # TODO: Send email
        
        return Response({
            'success': True,
            'message': 'Verification email sent'
        })
    
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
