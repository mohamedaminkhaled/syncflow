"""Serializers for the tasks app."""

from rest_framework import serializers
from apps.users.serializers import UserSerializer
from apps.tasks.models import Task, Comment, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model."""
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'mentions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer for listing tasks (simplified)."""
    assignees = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'priority', 'status', 'due_date',
            'position', 'assignees', 'created_at', 'updated_at'
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    """Serializer for task details (full)."""
    assignees = UserSerializer(many=True, read_only=True)
    reporter = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'column', 'assignees', 'reporter',
            'tags', 'priority', 'status', 'due_date', 'estimated_hours',
            'position', 'comments', 'comments_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reporter', 'created_at', 'updated_at']
    
    def get_comments_count(self, obj):
        return obj.comments.count()
