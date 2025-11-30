"""
Views for tenants app.
"""
from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import Tenant, Domain, TenantInvitation, TenantSettings
from .serializers import (
    TenantSerializer, TenantCreateSerializer, TenantUpdateSerializer,
    TenantInvitationSerializer, TenantApproveSerializer,
    TenantSuspendSerializer, DomainSerializer, TenantSettingsSerializer
)
from apps.core.permissions import IsSuperAdmin, IsTenantAdmin
from apps.core.utils import generate_token, send_email, log_activity


class TenantViewSet(viewsets.ModelViewSet):
    """ViewSet for Tenant model."""
    
    queryset = Tenant.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TenantCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TenantUpdateSerializer
        return TenantSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['list', 'approve', 'suspend']:
            return [IsSuperAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_super_admin:
            return Tenant.objects.all()
        elif user.tenant:
            return Tenant.objects.filter(id=user.tenant.id)
        return Tenant.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Create a new tenant (signup)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant = serializer.save()
        
        log_activity(
            user=None,
            action='CREATE',
            resource_type='TENANT',
            description=f'New tenant created: {tenant.name}',
            tenant=tenant,
            request=request
        )
        
        return Response({
            'message': 'Tenant created successfully. Awaiting approval.',
            'tenant': TenantSerializer(tenant, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def approve(self, request, pk=None):
        """Approve a tenant."""
        tenant = self.get_object()
        serializer = TenantApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tenant.approve(request.user)
        
        if serializer.validated_data.get('notes'):
            tenant.notes = serializer.validated_data['notes']
            tenant.save()
        
        log_activity(
            user=request.user,
            action='APPROVE',
            resource_type='TENANT',
            description=f'Tenant approved: {tenant.name}',
            tenant=tenant,
            request=request
        )
        
        # Send approval email
        # send_email(...)
        
        return Response({
            'message': 'Tenant approved successfully',
            'tenant': TenantSerializer(tenant, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def suspend(self, request, pk=None):
        """Suspend a tenant."""
        tenant = self.get_object()
        serializer = TenantSuspendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tenant.suspend(serializer.validated_data['reason'])
        
        log_activity(
            user=request.user,
            action='SUSPEND',
            resource_type='TENANT',
            description=f'Tenant suspended: {tenant.name}',
            tenant=tenant,
            request=request
        )
        
        # Send suspension email
        # send_email(...)
        
        return Response({
            'message': 'Tenant suspended successfully'
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def activate(self, request, pk=None):
        """Activate a suspended tenant."""
        tenant = self.get_object()
        tenant.status = 'ACTIVE'
        tenant.save()
        
        log_activity(
            user=request.user,
            action='ACTIVATE',
            resource_type='TENANT',
            description=f'Tenant activated: {tenant.name}',
            tenant=tenant,
            request=request
        )
        
        return Response({
            'message': 'Tenant activated successfully'
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get tenant statistics."""
        tenant = self.get_object()
        
        return Response({
            'users_count': tenant.current_users_count,
            'teams_count': tenant.current_teams_count,
            'projects_count': tenant.current_projects_count,
            'storage_used': float(tenant.current_storage_gb),
            'limits': tenant.check_limits(),
        })


class TenantInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet for tenant invitations."""
    
    serializer_class = TenantInvitationSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_super_admin:
            return TenantInvitation.objects.all()
        elif user.tenant:
            return TenantInvitation.objects.filter(tenant=user.tenant)
        return TenantInvitation.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Send a tenant invitation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Generate invitation token
        token = generate_token()
        expires_at = timezone.now() + timedelta(days=7)
        
        invitation = serializer.save(
            invited_by=request.user,
            token=token,
            expires_at=expires_at
        )
        
        # Send invitation email
        # send_email(...)
        
        log_activity(
            user=request.user,
            action='INVITE',
            resource_type='TENANT_INVITATION',
            description=f'Invitation sent to {invitation.email}',
            tenant=request.user.tenant,
            request=request
        )
        
        return Response(
            self.get_serializer(invitation).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def accept(self, request):
        """Accept a tenant invitation."""
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            invitation = TenantInvitation.objects.get(
                token=token,
                status='PENDING',
                expires_at__gt=timezone.now()
            )
        except TenantInvitation.DoesNotExist:
            return Response({
                'error': 'Invalid or expired invitation'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists
        from apps.accounts.models import User
        
        try:
            user = User.objects.get(email=invitation.email)
            # User exists, just link to tenant
            user.tenant = invitation.tenant
            user.role = invitation.role
            user.save()
        except User.DoesNotExist:
            # User doesn't exist, they need to register
            return Response({
                'message': 'Please complete registration',
                'tenant': invitation.tenant.slug,
                'email': invitation.email,
                'role': invitation.role
            })
        
        invitation.status = 'ACCEPTED'
        invitation.accepted_at = timezone.now()
        invitation.save()
        
        return Response({
            'message': 'Invitation accepted successfully'
        })


class TenantSettingsView(views.APIView):
    """View for tenant settings."""
    
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    
    def get(self, request):
        """Get tenant settings."""
        tenant = request.user.tenant
        if not tenant:
            return Response({
                'error': 'No tenant found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        settings, created = TenantSettings.objects.get_or_create(tenant=tenant)
        serializer = TenantSettingsSerializer(settings)
        return Response(serializer.data)
    
    def patch(self, request):
        """Update tenant settings."""
        tenant = request.user.tenant
        if not tenant:
            return Response({
                'error': 'No tenant found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        settings, created = TenantSettings.objects.get_or_create(tenant=tenant)
        serializer = TenantSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        log_activity(
            user=request.user,
            action='UPDATE',
            resource_type='TENANT_SETTINGS',
            description='Tenant settings updated',
            tenant=tenant,
            request=request
        )
        
        return Response(serializer.data)
