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
        self.client = QdrantClient(
            host=app_settings.VECTOR_DB_HOST,
            port=app_settings.VECTOR_DB_PORT,
        )
        # Create collection if not exists
        if COLLECTION_NAME not in [c.name for c in self.client.get_collections().collections]:
            self.client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={"size": 1536, "distance": "Cosine"}  # Adjust size to your embedding dimension
            )

    def add_document_chunks(
        self,
        document_id: str,
        chunk_texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> bool:
        try:
            # Use a UUID for each chunk
            chunk_ids = [str(uuid.uuid4()) for _ in range(len(chunk_texts))]
            points = [
                PointStruct(
                    id=chunk_ids[i],  # Now a valid UUID string
                    vector=embeddings[i],
                    payload={**metadatas[i], "document_id": document_id, "text": chunk_texts[i]}
                )
                for i in range(len(chunk_texts))
            ]
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            return True
        except Exception as e:
            logger.error(f"Error adding document chunks to vector store: {e}")
            return False

    def search_chunks(
        self,
        query_embedding: List[float],
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict:
        try:
            query_filter = None
            if document_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter
            )
            return {
                "documents": [r.payload.get("text") for r in results],
                "metadatas": [r.payload for r in results],
                "distances": [r.score for r in results]
            }
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return {"documents": [], "metadatas": [], "distances": []}

    def delete_document_chunks(self, document_id: str) -> bool:
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting document chunks from vector store: {e}")
            return False

vector_store = VectorStore()