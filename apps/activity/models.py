"""Models for the activity app."""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType


class ActivityLog(models.Model):
    """Activity Log model.
    
    Generic model to track all activities across the application.
    Uses Django's Generic Relations to link to any model.
    """
    
    class ActionType(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        MOVE = 'move', 'Move'
        COMMENT = 'comment', 'Comment'
        ASSIGN = 'assign', 'Assign'
        UNASSIGN = 'unassign', 'Unassign'
    
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities'
    )
    action = models.CharField(max_length=20, choices=ActionType.choices)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id', '-created_at']),
            models.Index(fields=['actor', '-created_at']),
        ]
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
    
    def __str__(self):
        return f"{self.actor} {self.action} {self.content_object} at {self.created_at}"
