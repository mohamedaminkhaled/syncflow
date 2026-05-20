"""Development settings for SyncFlow."""

from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Development-specific database (SQLite for local development)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Use InMemory channel layer for development
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Development caching (local memory)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Disable CORS restrictions in development
CORS_ALLOW_ALL_ORIGINS = True

# Logging
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}
