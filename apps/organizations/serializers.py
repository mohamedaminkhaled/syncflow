"""Serializers for the organizations app."""

from rest_framework import serializers
from apps.users.serializers import UserSerializer
from apps.organizations.models import Organization, OrganizationMember


class OrganizationMemberSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMember model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = OrganizationMember
        fields = ['id', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""
    members = OrganizationMemberSerializer(many=True, read_only=True)
    owner = UserSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'description', 'owner',
            'members', 'member_count', 'settings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Generate slug from name
        from django.utils.text import slugify
        import random
        import string
        
        name = validated_data.get('name', '')
        base_slug = slugify(name)
        
        # Ensure unique slug
        slug = base_slug
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        validated_data['slug'] = slug
        validated_data['owner'] = self.context['request'].user
        
        return super().create(validated_data)
