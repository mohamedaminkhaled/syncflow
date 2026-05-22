"""URL configuration for the core app."""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('playground/', views.LLMPlaygroundView.as_view(), name='playground'),
    path('api/llm/ask/', views.llm_ask, name='llm_ask'),
    path('api/llm/stream/', views.llm_stream, name='llm_stream'),
]
