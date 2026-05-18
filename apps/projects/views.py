"""Views for the projects app."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from apps.projects.models import Project, Board, Column
from apps.projects.serializers import (
    ProjectSerializer, BoardSerializer, ColumnSerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for Project CRUD operations."""
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_archived', 'organization']
    lookup_field = 'id'
    
    def get_queryset(self):
        return Project.objects.filter(
            members=self.request.user
        ).select_related('organization').prefetch_related(
            'boards__columns', 'members__user'
        )
    
    def perform_create(self, serializer):
        project = serializer.save()
        # Add creator as owner
        from apps.projects.models import ProjectMember
        ProjectMember.objects.create(
            user=self.request.user,
            project=project,
            role=ProjectMember.Role.OWNER
        )
    
    @action(detail=True, methods=['get'])
    def stats(self, request, id=None):
        """Get project statistics."""
        project = self.get_object()
        
        from apps.tasks.models import Task
        tasks = Task.objects.filter(column__board__project=project)
        
        data = {
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(status=Task.Status.DONE).count(),
            'in_progress_tasks': tasks.filter(status=Task.Status.IN_PROGRESS).count(),
            'overdue_tasks': tasks.filter(
                due_date__isnull=False,
                due_date__lt=timezone.now()
            ).exclude(status=Task.Status.DONE).count(),
        }
        return Response(data)


class BoardViewSet(viewsets.ModelViewSet):
    """ViewSet for Board CRUD operations."""
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project']
    lookup_field = 'id'
    
    def get_queryset(self):
        return Board.objects.filter(
            project__members=self.request.user
        ).select_related('project').prefetch_related(
            'columns__tasks'
        )
    
    def perform_create(self, serializer):
        serializer.save(position=0)


class ColumnViewSet(viewsets.ModelViewSet):
    """ViewSet for Column CRUD operations."""
    serializer_class = ColumnSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['board']
    lookup_field = 'id'
    
    def get_queryset(self):
        return Column.objects.filter(
            board__project__members=self.request.user
        ).prefetch_related('tasks')
