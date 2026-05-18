"""Settings package for SyncFlow."""

import os

environment = os.environ.get('DJANGO_SETTINGS_MODULE', 'syncflow.settings.dev')

if environment == 'syncflow.settings.prod':
    from .prod import *
else:
    from .dev import *
