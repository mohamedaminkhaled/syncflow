"""GraphQL Schema for SyncFlow."""

import graphene
from graphene_django import DjangoObjectType
from apps.users.schema import Query as UserQuery, Mutation as UserMutation
from apps.organizations.schema import Query as OrganizationQuery, Mutation as OrganizationMutation
from apps.projects.schema import Query as ProjectQuery, Mutation as ProjectMutation
from apps.tasks.schema import Query as TaskQuery, Mutation as TaskMutation


class Query(UserQuery, OrganizationQuery, ProjectQuery, TaskQuery, graphene.ObjectType):
    """Root Query combining all app queries."""
    pass


class Mutation(UserMutation, OrganizationMutation, ProjectMutation, TaskMutation, graphene.ObjectType):
    """Root Mutation combining all app mutations."""
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
