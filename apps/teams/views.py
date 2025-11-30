"""
Views for teams app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta

from .models import Team, TeamMember, TeamInvitation
from .serializers import (
    TeamSerializer, TeamCreateSerializer, TeamMemberSerializer,
    TeamInvitationSerializer
)
from apps.core.permissions import IsApprovedTenant
from apps.core.utils import generate_token, send_email, log_activity


class TeamViewSet(viewsets.ModelViewSet):
    """ViewSet for Team model."""
    
    permission_classes = [IsAuthenticated, IsApprovedTenant]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TeamCreateSerializer
        return TeamSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_super_admin:
            return Team.objects.all()
        elif user.tenant:
            # Get teams user is a member of
            member_teams = user.team_memberships.values_list('team_id', flat=True)
            return Team.objects.filter(
                tenant=user.tenant
            ).filter(
                models.Q(id__in=member_teams) | models.Q(is_private=False)
            ).distinct()
        return Team.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Create a new team."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tenant = request.user.tenant
        
        # Check team limit
        if tenant.current_teams_count >= tenant.max_teams:
            return Response({
                'error': 'Team limit reached. Please upgrade your plan.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate unique slug
        base_slug = slugify(serializer.validated_data['name'])
        slug = base_slug
        counter = 1
        while Team.objects.filter(tenant=tenant, slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        team = serializer.save(
            tenant=tenant,
            owner=request.user,
            slug=slug
        )
        
        # Add creator as team member
        TeamMember.objects.create(
            team=team,
            user=request.user,
            role='OWNER'
        )
        
        # Update tenant stats
        tenant.current_teams_count += 1
        tenant.save()
        
        # Update team members count
        team.members_count = 1
        team.save()
        
        log_activity(
            user=request.user,
            action='CREATE',
            resource_type='TEAM',
            description=f'Team created: {team.name}',
            tenant=tenant,
            request=request
        )
        
        return Response(
            TeamSerializer(team, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a team."""
        team = self.get_object()
        
        # Only owner can delete
        if team.owner != request.user and not request.user.is_super_admin:
            return Response({
                'error': 'Only team owner can delete the team'
            }, status=status.HTTP_403_FORBIDDEN)
        
        tenant = team.tenant
        team_name = team.name
        
        team.delete()
        
        # Update tenant stats
        tenant.current_teams_count = max(0, tenant.current_teams_count - 1)
        tenant.save()
        
        log_activity(
            user=request.user,
            action='DELETE',
            resource_type='TEAM',
            description=f'Team deleted: {team_name}',
            tenant=tenant,
            request=request
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get team members."""
        team = self.get_object()
        members = team.members.all()
        
        serializer = TeamMemberSerializer(members, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the team."""
        team = self.get_object()
        
        # Check if user has permission
        member = TeamMember.objects.filter(team=team, user=request.user).first()
        if not member or member.role == 'MEMBER':
            return Response({
                'error': 'Only team admins can add members'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'MEMBER')
        
        from apps.accounts.models import User
        user = get_object_or_404(User, id=user_id, tenant=team.tenant)
        
        # Check if already a member
        if TeamMember.objects.filter(team=team, user=user).exists():
            return Response({
                'error': 'User is already a team member'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        team_member = TeamMember.objects.create(
            team=team,
            user=user,
            role=role,
            invited_by=request.user
        )
        
        # Update team members count
        team.members_count += 1
        team.save()
        
        log_activity(
            user=request.user,
            action='CREATE',
            resource_type='TEAM_MEMBER',
            description=f'{user.get_full_name()} added to team {team.name}',
            tenant=team.tenant,
            request=request
        )
        
        return Response(
            TeamMemberSerializer(team_member, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the team."""
        team = self.get_object()
        
        # Check if user has permission
        member = TeamMember.objects.filter(team=team, user=request.user).first()
        if not member or member.role == 'MEMBER':
            return Response({
                'error': 'Only team admins can remove members'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user_id')
        
        from apps.accounts.models import User
        user = get_object_or_404(User, id=user_id)
        
        # Cannot remove owner
        if user == team.owner:
            return Response({
                'error': 'Cannot remove team owner'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        team_member = get_object_or_404(TeamMember, team=team, user=user)
        user_name = user.get_full_name()
        team_member.delete()
        
        # Update team members count
        team.members_count = max(0, team.members_count - 1)
        team.save()
        
        log_activity(
            user=request.user,
            action='DELETE',
            resource_type='TEAM_MEMBER',
            description=f'{user_name} removed from team {team.name}',
            tenant=team.tenant,
            request=request
        )
        
        return Response({
            'message': 'Member removed successfully'
        })


class TeamInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet for team invitations."""
    
    serializer_class = TeamInvitationSerializer
    permission_classes = [IsAuthenticated, IsApprovedTenant]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get teams where user is admin or owner
        admin_teams = TeamMember.objects.filter(
            user=user,
            role__in=['OWNER', 'ADMIN']
        ).values_list('team_id', flat=True)
        
        return TeamInvitation.objects.filter(team_id__in=admin_teams)
    
    def create(self, request, *args, **kwargs):
        """Send a team invitation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        team = serializer.validated_data['team']
        
        # Check if user can invite
        member = TeamMember.objects.filter(
            team=team,
            user=request.user,
            role__in=['OWNER', 'ADMIN']
        ).first()
        
        if not member:
            return Response({
                'error': 'Only team admins can send invitations'
            }, status=status.HTTP_403_FORBIDDEN)
        
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
            resource_type='TEAM_INVITATION',
            description=f'Team invitation sent to {invitation.email}',
            tenant=team.tenant,
            request=request
        )
        
        return Response(
            self.get_serializer(invitation).data,
            status=status.HTTP_201_CREATED
        )
