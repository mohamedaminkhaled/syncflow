"""GraphQL schema for the organizations app."""

import graphene
from graphene_django import DjangoObjectType
from apps.organizations.models import Organization, OrganizationMember
from apps.users.schema import UserType


class OrganizationMemberType(DjangoObjectType):
    """GraphQL type for OrganizationMember model."""
    user = graphene.Field(UserType)
    
    class Meta:
        model = OrganizationMember
        fields = ('id', 'user', 'role', 'joined_at')


class OrganizationType(DjangoObjectType):
    """GraphQL type for Organization model."""
    owner = graphene.Field(UserType)
    members = graphene.List(OrganizationMemberType)
    member_count = graphene.Int()
    
    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'slug', 'description', 'owner',
            'members', 'member_count', 'settings', 'created_at', 'updated_at'
        )
    
    def resolve_member_count(self, info):
        return self.members.count()


class Query(graphene.ObjectType):
    """GraphQL queries for organizations."""
    
    organization = graphene.Field(OrganizationType, id=graphene.Int(required=True))
    organizations = graphene.List(OrganizationType)
    
    def resolve_organization(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            return None
        return Organization.objects.filter(
            id=id,
            members=user,
        ).first()
    
    def resolve_organizations(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        return Organization.objects.filter(members=user)


class Mutation(graphene.ObjectType):
    """GraphQL mutations for organizations."""
    pass
