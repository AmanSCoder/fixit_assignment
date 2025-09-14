import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "DocuQuery"
    API_V1_STR: str = "/api/v1"

    # MinIO settings
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9001")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "documents")

    # Redis settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))

    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://redis:6379/0"
    )

    # Vector DB settings
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "qdrant")
    VECTOR_DB_HOST: str = os.getenv("VECTOR_DB_HOST", "qdrant")
    VECTOR_DB_PORT: int = int(os.getenv("VECTOR_DB_PORT", 6333))

    # AI Model settings
    AI_MODEL_PROVIDER: str = os.getenv("AI_MODEL_PROVIDER", "openai")
    AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "gpt-4")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")

    # Document processing settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 200))
    MAX_DOCUMENT_SIZE_MB: int = int(os.getenv("MAX_DOCUMENT_SIZE_MB", 10))

    # Azure OpenAI settings
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_EMBEDDING_DEPLOYMENT_NAME: str = os.getenv(
        "AZURE_EMBEDDING_DEPLOYMENT_NAME", ""
    )
    AZURE_OPENAI_API_VERSION: str = os.getenv(
        "AZURE_OPENAI_API_VERSION", "2024-02-15-preview"
    )
    AZURE_CHAT_MODEL_DEPLOYMENT_NAME: str = os.getenv(
        "AZURE_CHAT_MODEL_DEPLOYMENT_NAME", ""
    )


settings = Settings()
