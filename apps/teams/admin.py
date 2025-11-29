from django.contrib import admin
from .models import Team, TeamMember, TeamInvitation


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'owner', 'members_count', 'tasks_count', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at', 'tenant']
    search_fields = ['name', 'slug', 'tenant__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__email', 'team__name']
    readonly_fields = ['joined_at', 'updated_at']


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'team', 'role', 'status', 'invited_by', 'created_at', 'expires_at']
    list_filter = ['status', 'role', 'created_at']
    search_fields = ['email', 'team__name']
    readonly_fields = ['created_at', 'responded_at']
