"""Views for the tasks app."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.tasks.models import Task, Comment, Tag
from apps.tasks.serializers import (
    TaskListSerializer, TaskDetailSerializer, CommentSerializer, TagSerializer
)


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for Task CRUD operations."""
    serializer_class = TaskDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'column']
    lookup_field = 'id'
    
    def get_queryset(self):
        return Task.objects.filter(
            column__board__project__members=self.request.user
        ).select_related(
            'column__board__project', 'reporter'
        ).prefetch_related(
            'assignees', 'tags', 'comments__author'
        )
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        return TaskDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
    
    @action(detail=True, methods=['post'])
    def move(self, request, id=None):
        """Move task to another column."""
        task = self.get_object()
        new_column_id = request.data.get('column_id')
        new_position = request.data.get('position', 0)
        
        from apps.projects.models import Column
        try:
            new_column = Column.objects.get(id=new_column_id)
            task.column = new_column
            task.position = new_position
            task.save()
            
            # Broadcast via WebSocket
            from apps.tasks.signals import broadcast_task_update
            broadcast_task_update(task, 'moved', request.user)
            
            return Response(TaskDetailSerializer(task).data)
        except Column.DoesNotExist:
            return Response(
                {'error': 'Column not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def assign(self, request, id=None):
        """Assign users to task."""
        task = self.get_object()
        user_ids = request.data.get('user_ids', [])
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.filter(id__in=user_ids)
        task.assignees.set(users)
        
        return Response(TaskDetailSerializer(task).data)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for Comment CRUD operations."""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['task']
    lookup_field = 'id'
    
    def get_queryset(self):
        return Comment.objects.filter(
            task__column__board__project__members=self.request.user
        ).select_related('task', 'author')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for Tag CRUD operations."""
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Tag.objects.filter(
            organization_id__in=self.request.user.organizations.values_list('id', flat=True)
        )
