from celery import Celery

from core.config import settings

celery_app = Celery(
    "databridge",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.reports", "tasks.exports", "tasks.sweeper"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "sweep-stuck-jobs": {
            "task": "tasks.sweeper.sweep_stuck_jobs",
            "schedule": 60.0,  # every 60 seconds
        },
    },
)
