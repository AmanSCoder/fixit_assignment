from celery import Celery
from app.config import settings
from app.core.document_processor import document_processor
from app.services.ai_service import ai_service
from app.core.vector_store import vector_store
from app.core.cache import cache
import asyncio
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "docuquery",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# TODO replace with proper database
from app.db.memory import documents

@celery_app.task(bind=True, name="process_document")
def process_document_task(self, document_id: str, object_name: str):
    """Process document, extract text, generate embeddings, and store in vector DB"""
    try:
        logger.info(f"Processing document {document_id}")
        
        # Process document to extract text and split into chunks
        chunks, metadatas = document_processor.process_document(document_id, object_name)
        
        if not chunks:
            logger.warning(f"No text extracted from document {document_id}")
            if document_id in documents:
                documents[document_id]["status"] = "failed"
            return False
        
        # Generate embeddings for chunks using the AI service
        # We need to run the async function in the sync context
        loop = asyncio.get_event_loop()
        embeddings = loop.run_until_complete(ai_service.generate_embeddings(chunks))
        
        # Store chunks and embeddings in vector store
        result = vector_store.add_document_chunks(document_id, chunks, embeddings, metadatas)
        
        # Update document status
        if document_id in documents:
            documents[document_id]["status"] = "ready" if result else "failed"
        
        # Cache document chunks for faster retrieval
        cache.cache_document_chunks(document_id, chunks)
        
        logger.info(f"Document {document_id} processed successfully")
        return result
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        if document_id in documents:
            documents[document_id]["status"] = "failed"
        return False

# Create a separate Celery worker file that imports these tasks