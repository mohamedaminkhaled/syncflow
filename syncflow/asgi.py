"""ASGI config for SyncFlow project."""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syncflow.settings')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import websocket patterns after Django is set up
from apps.tasks.routing import websocket_urlpatterns as task_websocket_urls

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                task_websocket_urls
            )
        )
    ),
})
