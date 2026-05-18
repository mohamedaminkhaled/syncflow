"""GraphQL schema for the users app."""

import graphene
from graphene_django import DjangoObjectType
from apps.users.models import User


class UserType(DjangoObjectType):
    """GraphQL type for User model."""
    
    full_name = graphene.String()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar', 'phone', 'bio', 'timezone', 'is_active',
            'date_joined'
        )
    
    def resolve_full_name(self, info):
        return self.full_name


class Query(graphene.ObjectType):
    """GraphQL queries for users."""
    
    me = graphene.Field(UserType)
    user = graphene.Field(UserType, id=graphene.Int(required=True))
    users = graphene.List(UserType)
    
    def resolve_me(self, info):
        if info.context.user.is_authenticated:
            return info.context.user
        return None
    
    def resolve_user(self, info, id):
        return User.objects.filter(id=id).first()
    
    def resolve_users(self, info):
        return User.objects.all()


class Mutation(graphene.ObjectType):
    """GraphQL mutations for users."""
    pass
