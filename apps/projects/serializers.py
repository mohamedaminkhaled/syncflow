"""Serializers for the projects app."""

from rest_framework import serializers
from apps.users.serializers import UserSerializer
from apps.projects.models import Project, ProjectMember, Board, Column


class ColumnSerializer(serializers.ModelSerializer):
    """Serializer for Column model."""
    task_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Column
        fields = [
            'id', 'name', 'position', 'color', 'wip_limit',
            'task_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BoardSerializer(serializers.ModelSerializer):
    """Serializer for Board model."""
    columns = ColumnSerializer(many=True, read_only=True)
    
    class Meta:
        model = Board
        fields = [
            'id', 'name', 'description', 'position', 'layout_config',
            'columns', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectMemberSerializer(serializers.ModelSerializer):
    """Serializer for ProjectMember model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model."""
    boards = BoardSerializer(many=True, read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'key', 'description', 'organization',
            'boards', 'members', 'member_count', 'is_archived',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'key', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Generate project key from name
        name = validated_data.get('name', '')
        key = ''.join([word[0].upper() for word in name.split()[:3]])
        if len(key) < 2:
            key = 'PR'
        validated_data['key'] = key
        return super().create(validated_data)
