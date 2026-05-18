"""User model for SyncFlow."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser.
    
    This model replaces the default Django User model to add
    additional fields and functionality for SyncFlow.
    """
    
    # Additional profile fields
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Notification preferences stored as JSON
    notification_preferences = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username
    
    @property
    def full_name(self):
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username
