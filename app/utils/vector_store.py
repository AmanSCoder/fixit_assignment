import numpy as np
from typing import List, Dict, Any, Optional
import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from app.config import settings as app_settings
import uuid

logger = logging.getLogger(__name__)

COLLECTION_NAME = "document_chunks"


class VectorStore:
    def __init__(self):
        logger.info("Initializing vector store")
        host = app_settings.VECTOR_DB_HOST

        # Remove protocol if present
        if host.startswith("http://"):
            host = host[len("http://"):]
            url = f"http://{host}:{app_settings.VECTOR_DB_PORT}"
        elif host.startswith("https://"):
            host = host[len("https://"):]
            url = f"https://{host}:{app_settings.VECTOR_DB_PORT}"
        else:
            url = f"http://{host}:{app_settings.VECTOR_DB_PORT}"

        self.client = QdrantClient(
            url=url
        )
        logger.debug(
            f"QdrantClient initialized with host={app_settings.VECTOR_DB_HOST}, port={app_settings.VECTOR_DB_PORT}"
        )
        # Create collection if not exists
        collections = [c.name for c in self.client.get_collections().collections]
        logger.debug(f"Existing Qdrant collections: {collections}")
        if COLLECTION_NAME not in collections:
            logger.info(
                f"Collection '{COLLECTION_NAME}' not found. Creating new collection."
            )
            self.client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "size": 1536,
                    "distance": "Cosine",
                },  # Adjust size to your embedding dimension
            )
            logger.info(f"Collection '{COLLECTION_NAME}' created.")
        else:
            logger.info(f"Collection '{COLLECTION_NAME}' already exists.")

    def add_document_chunks(
        self,
        document_id: str,
        chunk_texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> bool:
        try:
            logger.info(
                f"Adding {len(chunk_texts)} chunks for document_id={document_id} to vector store."
            )
            chunk_ids = [str(uuid.uuid4()) for _ in range(len(chunk_texts))]
            points = [
                PointStruct(
                    id=chunk_ids[i],
                    vector=embeddings[i],
                    payload={
                        **metadatas[i],
                        "document_id": document_id,
                        "text": chunk_texts[i],
                    },
                )
                for i in range(len(chunk_texts))
            ]
            logger.debug(f"Upserting points: {points}")
            self.client.upsert(collection_name=COLLECTION_NAME, points=points)
            logger.info(f"Successfully added chunks for document_id={document_id}.")
            return True
        except Exception as e:
            logger.error(f"Error adding document chunks to vector store: {e}")
            return False

    def search_chunks(
        self,
        query_embedding: List[float],
        document_id: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict:
        try:
            logger.info(
                f"Searching for top {top_k} chunks for document_id={document_id}."
            )
            query_filter = None
            if document_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id", match=MatchValue(value=document_id)
                        )
                    ]
                )
                logger.debug(f"Using filter: {query_filter}")
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter,
            )
            response = {
                "documents": [r.payload.get("text") for r in results],
                "metadatas": [r.payload for r in results],
                "distances": [r.score for r in results],
            }
            logger.debug(f"Search response: {response}")
            logger.info(
                f"Search completed for document_id={document_id}. Found {len(results)} results."
            )
            return response
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return {"documents": [], "metadatas": [], "distances": []}

    def delete_document_chunks(self, document_id: str) -> bool:
        try:
            logger.info(
                f"Deleting chunks for document_id={document_id} from vector store."
            )
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id", match=MatchValue(value=document_id)
                        )
                    ]
                ),
            )
            logger.info(f"Successfully deleted chunks for document_id={document_id}.")
            return True
        except Exception as e:
            logger.error(f"Error deleting document chunks from vector store: {e}")
            return False


vector_store = VectorStore()
