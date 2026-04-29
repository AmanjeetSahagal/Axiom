from celery import Celery

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.optimizer import process_optimization_job
from app.services.run_service import process_run

celery_app = Celery("axiom", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_run_task(self, run_id: str):
    db = SessionLocal()
    try:
        process_run(db, run_id)
    finally:
        db.close()


def enqueue_run(run_id: str) -> None:
    process_run_task.delay(run_id)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_optimization_job_task(self, job_id: str):
    db = SessionLocal()
    try:
        process_optimization_job(db, job_id)
    finally:
        db.close()


def enqueue_optimization_job(job_id: str) -> None:
    process_optimization_job_task.delay(job_id)
