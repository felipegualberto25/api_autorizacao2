# app/test_tasks.py
from app.tasks import celery_app

@celery_app.task(bind=True)
def ping(self, x):
    return f"pong {x}"
