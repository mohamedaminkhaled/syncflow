"""Models for the tasks app."""

from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.projects.models import Column


class Task(models.Model):
    """Task model.
    
    Represents a task/card within a column on a board.
    """
    
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'
    
    class Status(models.TextChoices):
        BACKLOG = 'backlog', 'Backlog'
        TODO = 'todo', 'To Do'
        IN_PROGRESS = 'in_progress', 'In Progress'
        IN_REVIEW = 'in_review', 'In Review'
        DONE = 'done', 'Done'
    
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    column = models.ForeignKey(
        Column,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_tasks',
        blank=True
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_tasks'
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.BACKLOG
    )
    due_date = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        ordering = ['position']
        indexes = [
            models.Index(fields=['column', 'position']),
            models.Index(fields=['assignees', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status', '-created_at']),
        ]
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
    
    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        """Check if the task is overdue."""
        if self.due_date and self.status != self.Status.DONE:
            return self.due_date < timezone.now()
        return False
    
    @property
    def project(self):
        """Get the project this task belongs to."""
        return self.column.board.project


class Comment(models.Model):
    """Comment model.
    
    Represents a comment on a task.
    """
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    content = models.TextField()
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='mentioned_in_comments',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comments'
        ordering = ['created_at']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"


class Tag(models.Model):
    """Tag model.
    
    Represents a tag that can be applied to tasks.
    """
    
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#3b82f6')
    organization_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tags'
        unique_together = ['name', 'organization_id']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
    
    def __str__(self):
        return self.name


class TaskTag(models.Model):
    """Through model for Task-Tag many-to-many relationship."""
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_tags'
        unique_together = ['task', 'tag']
