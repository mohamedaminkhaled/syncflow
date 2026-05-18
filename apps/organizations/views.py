"""Views for the organizations app."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.organizations.models import Organization, OrganizationMember
from apps.organizations.serializers import OrganizationSerializer, OrganizationMemberSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for Organization CRUD operations."""
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Organization.objects.filter(
            members=self.request.user
        ).prefetch_related('members__user')
    
    def perform_create(self, serializer):
        organization = serializer.save()
        # Add creator as admin member
        OrganizationMember.objects.create(
            user=self.request.user,
            organization=organization,
            role=OrganizationMember.Role.ADMIN
        )
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, id=None):
        """Add a member to the organization."""
        organization = self.get_object()
        
        # Check if user is admin
        membership = OrganizationMember.objects.filter(
            organization=organization,
            user=request.user,
            role=OrganizationMember.Role.ADMIN
        ).first()
        
        if not membership:
            return Response(
                {'error': 'Only admins can add members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user_id = request.data.get('user_id')
        role = request.data.get('role', OrganizationMember.Role.MEMBER)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        membership, created = OrganizationMember.objects.get_or_create(
            user=user,
            organization=organization,
            defaults={'role': role}
        )
        
        if not created:
            membership.role = role
            membership.save()
        
        return Response(
            OrganizationSerializer(organization).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, id=None):
        """Remove a member from the organization."""
        organization = self.get_object()
        
        # Check if user is admin
        membership = OrganizationMember.objects.filter(
            organization=organization,
            user=request.user,
            role=OrganizationMember.Role.ADMIN
        ).first()
        
        if not membership:
            return Response(
                {'error': 'Only admins can remove members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        member_id = request.data.get('member_id')
        
        try:
            member = OrganizationMember.objects.get(
                id=member_id,
                organization=organization
            )
            member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except OrganizationMember.DoesNotExist:
            return Response(
                {'error': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )
