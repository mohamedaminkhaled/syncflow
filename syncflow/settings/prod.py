"""Production settings for SyncFlow."""

import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

def _env_bool(name, default):
    return os.environ.get(name, str(default)).lower() in ('1', 'true', 'yes', 'on')

# Secure cookie settings (disable when serving over plain HTTP, e.g. local docker)
SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', True)
CSRF_COOKIE_SECURE = _env_bool('CSRF_COOKIE_SECURE', True)
SECURE_SSL_REDIRECT = _env_bool('SECURE_SSL_REDIRECT', True)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS settings
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database from environment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'syncflow'),
        'USER': os.environ.get('POSTGRES_USER', 'syncflow'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Production channel layers (Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Production caching (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
    }
}

# Logging
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['apps'] = {
    'handlers': ['console'],
    'level': 'INFO',
    'propagate': False,
}
