"""
Celery configuration for background job processing and task queue.
"""

import os
from celery import Celery
from celery.signals import task_failure, task_success
import logging

logger = logging.getLogger(__name__)

# Celery configuration
celery_app = Celery(
    'music_platform',
    broker=os.getenv('CELERY_BROKER_URL', 'amqp://admin:admin@localhost:5672/'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    include=[
        'app.tasks.payments',
        'app.tasks.recommendations',
        'app.tasks.notifications',
        'app.tasks.analytics',
    ]
)

# Celery beat schedule
celery_app.conf.beat_schedule = {
    'generate-daily-recommendations': {
        'task': 'app.tasks.recommendations.generate_daily_recommendations',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-sessions': {
        'task': 'app.tasks.analytics.cleanup_old_sessions',
        'schedule': 86400.0,  # Daily
    },
    'process-failed-payments': {
        'task': 'app.tasks.payments.retry_failed_payments',
        'schedule': 300.0,  # Every 5 minutes
    },
}

# Task configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task event handlers
@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Handle task failure events."""
    logger.error(f"Task {task_id} failed: {exception}")

@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """Handle task success events."""
    logger.info(f"Task {sender.name} completed successfully")

# Export celery app
__all__ = ['celery_app']
