from app.helpers.celery_tasks import celery_app

if __name__ == "__main__":
    celery_app.worker_lp(loglevel="info", concurrency=2)
