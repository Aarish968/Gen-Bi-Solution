"""
celery_app.py

Celery instance for the Generative BI project.

Broker  : Redis — receives tasks from FastAPI
Backend : Redis — stores task results so /api/task/{id} can fetch them

How it works:
  FastAPI submits a task → Redis queue → Celery worker picks it up
  → executes → stores result in Redis → frontend polls /api/task/{id}
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "generative_bi",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.analyze_task"],  # register task modules here
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Result expires after 1 hour — no stale data in Redis
    result_expires=3600,
    # Worker concurrency — how many tasks run in parallel
    worker_concurrency=2,
)
