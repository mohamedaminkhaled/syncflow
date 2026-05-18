"""URL configuration for the tasks app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.tasks.views import TaskViewSet, CommentViewSet, TagViewSet

app_name = 'tasks'

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
