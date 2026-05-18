"""URL configuration for the organizations app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.organizations.views import OrganizationViewSet

app_name = 'organizations'

router = DefaultRouter()
router.register(r'', OrganizationViewSet, basename='organization')

urlpatterns = [
    path('', include(router.urls)),
]
