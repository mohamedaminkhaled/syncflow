"""Celery application for SyncFlow."""

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'syncflow.settings')

app = Celery('syncflow')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
