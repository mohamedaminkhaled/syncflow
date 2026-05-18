"""Views for the core app."""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render


class HomeView(TemplateView):
    """Home page view - Marketing landing page."""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['features'] = [
            {
                'title': 'Real-time Collaboration',
                'icon': 'users',
                'description': 'Work together with your team in real-time. See changes instantly as they happen.'
            },
            {
                'title': 'Agile Kanban Boards',
                'icon': 'columns',
                'description': 'Visualize your workflow with flexible Kanban boards. Drag and drop tasks effortlessly.'
            },
            {
                'title': 'REST & GraphQL APIs',
                'icon': 'api',
                'description': 'Choose your preferred API style. Full support for both REST and GraphQL.'
            },
            {
                'title': 'WebSocket Real-time',
                'icon': 'bolt',
                'description': 'Instant updates via WebSockets. No refresh needed.'
            },
        ]
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """User dashboard view - Main application landing after login."""
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's organizations
        from apps.organizations.models import OrganizationMember
        context['organizations'] = OrganizationMember.objects.filter(
            user=user
        ).select_related('organization')[:5]
        
        # Get user's assigned tasks
        from apps.tasks.models import Task
        context['my_tasks'] = Task.objects.filter(
            assignees=user
        ).select_related(
            'column__board__project'
        ).exclude(
            status=Task.Status.DONE
        )[:10]
        
        return context
