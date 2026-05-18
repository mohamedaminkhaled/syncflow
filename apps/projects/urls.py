"""URL configuration for the projects app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.projects.views import ProjectViewSet, BoardViewSet, ColumnViewSet

app_name = 'projects'

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'columns', ColumnViewSet, basename='column')

urlpatterns = [
    path('', include(router.urls)),
]
