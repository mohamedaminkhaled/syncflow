"""SyncFlow package."""

# Expose the Celery app for autodiscovery when Celery is installed. Guarded so
# lightweight entry points (e.g. the `syncflow.llm` CLI) can import the package
# without pulling in the full Django/Celery stack.
try:
    from .celery import app as celery_app
except ModuleNotFoundError:  # pragma: no cover - depends on optional install
    celery_app = None

__all__ = ('celery_app',)
