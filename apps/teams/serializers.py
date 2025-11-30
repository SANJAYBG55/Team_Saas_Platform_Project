"""
Serializers for teams app.
"""
from rest_framework import serializers
from .models import Team, TeamMember, TeamInvitation
from apps.accounts.serializers import UserSerializer


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for TeamMember model."""
    
    user_details = UserSerializer(source='user', read_only=True)
    invited_by_name = serializers.CharField(
        source='invited_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = TeamMember
        fields = [
            'id', 'team', 'user', 'user_details', 'role',
            'invited_by', 'invited_by_name', 'invitation_accepted_at',
            'joined_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invited_by', 'invitation_accepted_at',
            'joined_at', 'updated_at'
        ]


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model."""
    
    owner_details = UserSerializer(source='owner', read_only=True)
    members = TeamMemberSerializer(many=True, read_only=True)
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id', 'tenant', 'name', 'slug', 'description',
            'is_private', 'avatar', 'avatar_url', 'color',
            'owner', 'owner_details', 'members_count',
            'tasks_count', 'members', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tenant', 'slug', 'owner', 'members_count',
            'tasks_count', 'created_at', 'updated_at'
        ]
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None


class TeamCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating teams."""
    
    class Meta:
        model = Team
        fields = ['name', 'description', 'is_private', 'avatar', 'color']


class TeamInvitationSerializer(serializers.ModelSerializer):
    """Serializer for TeamInvitation model."""
    
    team_name = serializers.CharField(source='team.name', read_only=True)
    invited_by_name = serializers.CharField(
        source='invited_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = TeamInvitation
        fields = [
            'id', 'team', 'team_name', 'email', 'role',
            'token', 'invited_by', 'invited_by_name', 'status',
            'message', 'created_at', 'expires_at', 'responded_at'
        ]
        read_only_fields = [
            'id', 'token', 'invited_by', 'status',
            'created_at', 'responded_at'
        ]
