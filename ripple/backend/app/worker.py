"""Celery worker: `celery -A app.worker.celery_app worker -l info` (QUEUE_BACKEND=celery)."""
from celery import Celery

from .config import settings
from .service import run_analysis

celery_app = Celery("ripple", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_acks_late = True
celery_app.conf.task_time_limit = 900          # hard CPU/time limit per analysis


@celery_app.task(name="ripple.analyze")
def analyze_task(analysis_id: str) -> None:
    run_analysis(analysis_id)
