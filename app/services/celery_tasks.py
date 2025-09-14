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
        logger.info(f"Processing document {document_id} with object_name: {object_name}")

        # Process document to extract text and split into chunks
        logger.debug(f"Calling document_processor.process_document with document_id={document_id}, object_name={object_name}")
        chunks, metadatas = document_processor.process_document(document_id, object_name)
        logger.debug(f"Extracted {len(chunks)} chunks and metadatas: {metadatas}")

        if not chunks:
            logger.warning(f"No text extracted from document {document_id}")
            if document_id in documents:
                documents[document_id]["status"] = "failed"
            return False

        # Generate embeddings for chunks using the AI service
        logger.debug(f"Generating embeddings for document {document_id} chunks: {chunks}")
        loop = asyncio.get_event_loop()
        embeddings = loop.run_until_complete(ai_service.generate_embeddings(chunks))
        logger.debug(f"Generated embeddings for document {document_id}")

        # Store chunks and embeddings in vector store
        logger.debug(f"Adding document chunks to vector store for document_id={document_id}")
        result = vector_store.add_document_chunks(document_id, chunks, embeddings, metadatas)
        logger.debug(f"Vector store add_document_chunks result for document_id={document_id}: {result}")

        # Update document status
        if document_id in documents:
            documents[document_id]["status"] = "ready" if result else "failed"
            logger.debug(f"Updated document status for {document_id} to {documents[document_id]['status']}")

        # Cache document chunks for faster retrieval
        logger.debug(f"Caching document chunks for document_id={document_id}")
        cache.cache_document_chunks(document_id, chunks)

        logger.info(f"Document {document_id} processed successfully")
        return result
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
        if document_id in documents:
            documents[document_id]["status"] = "failed"
        return False

# Create a separate Celery worker file that imports these tasks