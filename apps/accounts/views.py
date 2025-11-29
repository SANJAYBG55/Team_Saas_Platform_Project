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
