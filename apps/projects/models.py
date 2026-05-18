"""Models for the projects app."""

from django.db import models
from django.conf import settings
from apps.organizations.models import Organization


class Project(models.Model):
    """Project model.
    
    Represents a project within an organization that contains boards.
    """
    
    name = models.CharField(max_length=200)
    key = models.CharField(max_length=10, unique=True)  # e.g., "PROJ", "SYNC"
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ProjectMember',
        related_name='projects'
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['key']),
        ]
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
    
    def __str__(self):
        return f"{self.key} - {self.name}"


class ProjectMember(models.Model):
    """Through model for Project-User many-to-many relationship."""
    
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
        VIEWER = 'viewer', 'Viewer'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_members'
        unique_together = ['user', 'project']
        verbose_name = 'Project Member'
        verbose_name_plural = 'Project Members'
    
    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.role})"


class Board(models.Model):
    """Board model.
    
    Represents a Kanban board within a project.
    """
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='boards'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    layout_config = models.JSONField(default=dict, blank=True)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'boards'
        ordering = ['position']
        indexes = [
            models.Index(fields=['project', 'position']),
        ]
        verbose_name = 'Board'
        verbose_name_plural = 'Boards'
    
    def __str__(self):
        return f"{self.project.name} - {self.name}"


class Column(models.Model):
    """Column model.
    
    Represents a column/list within a board (e.g., To Do, In Progress, Done).
    """
    
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    name = models.CharField(max_length=100)
    position = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#3b82f6')  # Hex color
    wip_limit = models.PositiveIntegerField(null=True, blank=True)  # Work in progress limit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'columns'
        ordering = ['position']
        indexes = [
            models.Index(fields=['board', 'position']),
        ]
        verbose_name = 'Column'
        verbose_name_plural = 'Columns'
    
    def __str__(self):
        return f"{self.board.name} - {self.name}"
    
    @property
    def task_count(self):
        """Return the number of tasks in this column."""
        return self.tasks.count()
