"""URL Configuration for SyncFlow."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from syncflow.graphql_urls import schema

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API
    path('api/', include('apps.projects.urls')),
    path('api/', include('apps.tasks.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/organizations/', include('apps.organizations.urls')),

    # GraphQL
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
    
    # Core app
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
