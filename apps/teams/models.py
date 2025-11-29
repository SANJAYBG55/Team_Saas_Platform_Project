"""
Teams and team member models.
"""
from django.db import models
from django.utils import timezone


class Team(models.Model):
    """Team model for organizing users."""
    
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='teams'
    )
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    # Team settings
    is_private = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='teams/avatars/', blank=True, null=True)
    color = models.CharField(max_length=7, default='#3B82F6')
    
    # Owner
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='owned_teams'
    )
    
    # Stats
    members_count = models.IntegerField(default=1)
    tasks_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'teams'
        ordering = ['-created_at']
        unique_together = [['tenant', 'slug']]
        indexes = [
            models.Index(fields=['tenant', 'slug']),
            models.Index(fields=['owner']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class TeamMember(models.Model):
    """Team membership model."""
    
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),
        ('ADMIN', 'Admin'),
        ('MEMBER', 'Member'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    
    # Invitation
    invited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_invitations_sent'
    )
    invitation_accepted_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    joined_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'team_members'
        ordering = ['-joined_at']
        unique_together = [['team', 'user']]
        indexes = [
            models.Index(fields=['team', 'user']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} in {self.team.name}"


class TeamInvitation(models.Model):
    """Team invitation model."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, default='MEMBER')
    token = models.CharField(max_length=255, unique=True)
    
    invited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sent_team_invitations'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'team_invitations'
        ordering = ['-created_at']
        unique_together = [['team', 'email']]
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email', 'status']),
        ]
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.team.name}"
