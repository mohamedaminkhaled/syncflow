"""Models for the organizations app."""

from django.db import models
from django.conf import settings


class Organization(models.Model):
    """Organization/Workspace model.
    
    Represents a company, team, or group that owns projects and boards.
    """
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_organizations'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='OrganizationMember',
        related_name='organizations'
    )
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
    
    def __str__(self):
        return self.name


class OrganizationMember(models.Model):
    """Through model for Organization-User many-to-many relationship.
    
    Defines the role of each member within an organization.
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        MEMBER = 'member', 'Member'
        VIEWER = 'viewer', 'Viewer'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'organization_members'
        unique_together = ['user', 'organization']
        indexes = [
            models.Index(fields=['organization', 'role']),
        ]
        verbose_name = 'Organization Member'
        verbose_name_plural = 'Organization Members'
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"
