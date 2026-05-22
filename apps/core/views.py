"""Views for the core app."""

import json

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(TemplateView):
    """Home page view - Marketing landing page."""
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['features'] = [
            {
                'title': 'Real-time Collaboration',
                'icon': '◇',
                'description': 'Work together with your team in real-time. See changes instantly as they happen.'
            },
            {
                'title': 'Agile Kanban Boards',
                'icon': '▦',
                'description': 'Visualize your workflow with flexible Kanban boards. Drag and drop tasks effortlessly.'
            },
            {
                'title': 'REST & GraphQL APIs',
                'icon': '⚙',
                'description': 'Choose your preferred API style. Full support for both REST and GraphQL.'
            },
            {
                'title': 'Multi-Provider LLMs',
                'icon': '✦',
                'description': 'Query Anthropic, OpenAI and OpenRouter with normalized token + cost tracking.'
            },
        ]
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """User dashboard view - Main application landing after login."""
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        from apps.organizations.models import OrganizationMember
        context['organizations'] = OrganizationMember.objects.filter(
            user=user
        ).select_related('organization')[:5]

        from apps.tasks.models import Task
        context['my_tasks'] = Task.objects.filter(
            assignees=user
        ).select_related(
            'column__board__project'
        ).exclude(
            status=Task.Status.DONE
        )[:10]

        return context


class LLMPlaygroundView(TemplateView):
    """Interactive page for testing LLM providers from the browser."""
    template_name = 'core/playground.html'

    def get_context_data(self, **kwargs):
        from syncflow.llm.pricing import list_models

        context = super().get_context_data(**kwargs)
        context['catalog_json'] = json.dumps(list_models())
        return context


def _parse_request(request):
    """Pull and validate the LLM request body."""
    from syncflow.llm.models import Message

    data = json.loads(request.body or '{}')
    provider = (data.get('provider') or '').strip()
    model = (data.get('model') or '').strip()
    prompt = (data.get('prompt') or '').strip()
    system = (data.get('system') or '').strip()

    if not provider or not model or not prompt:
        raise ValueError('provider, model and prompt are all required.')

    messages = []
    if system:
        messages.append(Message(role='system', content=system))
    messages.append(Message(role='user', content=prompt))
    return provider, model, messages


@require_POST
def llm_ask(request):
    """Non-streaming completion. Returns the answer plus token/cost metrics."""
    from syncflow.llm.providers import ProviderError, get_provider

    try:
        provider, model, messages = _parse_request(request)
        client = get_provider(provider)
        resp = client.complete(messages, model)
    except (ValueError, ProviderError) as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    except Exception as exc:  # noqa: BLE001 - surface SDK/runtime errors
        return JsonResponse({'error': f'{type(exc).__name__}: {exc}'}, status=502)

    return JsonResponse({
        'text': resp.text,
        'provider': resp.provider,
        'model': resp.model,
        'input_tokens': resp.input_tokens,
        'output_tokens': resp.output_tokens,
        'cost_usd': f'{resp.cost_usd:.6f}',
        'latency_ms': round(resp.latency_ms, 1),
        'finish_reason': resp.finish_reason,
        'prompt_hash': resp.prompt_hash,
    })


@require_POST
def llm_stream(request):
    """Streaming completion over Server-Sent Events.

    Emits ``delta`` events as text arrives and a final ``done`` event carrying
    the aggregated token/cost metrics.
    """
    from syncflow.llm.providers import ProviderError, get_provider

    try:
        provider, model, messages = _parse_request(request)
        client = get_provider(provider)
    except (ValueError, ProviderError) as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    def event_stream():
        try:
            for chunk in client.stream(messages, model):
                if chunk.text:
                    payload = json.dumps({'text': chunk.text})
                    yield f'event: delta\ndata: {payload}\n\n'
                if chunk.response is not None:
                    r = chunk.response
                    payload = json.dumps({
                        'provider': r.provider,
                        'model': r.model,
                        'input_tokens': r.input_tokens,
                        'output_tokens': r.output_tokens,
                        'cost_usd': f'{r.cost_usd:.6f}',
                        'latency_ms': round(r.latency_ms, 1),
                        'finish_reason': r.finish_reason,
                        'prompt_hash': r.prompt_hash,
                    })
                    yield f'event: done\ndata: {payload}\n\n'
        except Exception as exc:  # noqa: BLE001
            payload = json.dumps({'error': f'{type(exc).__name__}: {exc}'})
            yield f'event: error\ndata: {payload}\n\n'

    response = StreamingHttpResponse(
        event_stream(), content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
