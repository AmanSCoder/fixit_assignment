import os
import logging
from app.helpers.celery_tasks import celery_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log important settings for troubleshooting
logger.info("Starting Celery worker...")
logger.info(f"Database URL: {os.environ.get('DATABASE_URL', 'Not set')}")
logger.info(f"MinIO endpoint: {os.environ.get('MINIO_ENDPOINT', 'Not set')}")
logger.info(f"Redis host: {os.environ.get('REDIS_HOST', 'Not set')}")


if __name__ == "__main__":
    celery_app.worker_lp(loglevel="info", concurrency=2)
