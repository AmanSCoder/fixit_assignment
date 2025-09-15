import redis
import json
import hashlib
from typing import Any, Optional, Dict
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        self.default_ttl = 3600  # 1 hour

    def _generate_key(self, key_type: str, identifier: str) -> str:
        """Generate a Redis key with a type prefix"""
        return f"{key_type}:{identifier}"

    def _generate_query_key(self, document_id: str, question: str) -> str:
        """Generate a unique key for a query"""
        # Create a hash of the question to handle minor variations
        question_hash = hashlib.md5(question.lower().strip().encode()).hexdigest()
        return self._generate_key("query", f"{document_id}:{question_hash}")

    def set(
        self, key_type: str, identifier: str, data: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set data in cache with TTL"""
        try:
            key = self._generate_key(key_type, identifier)
            try:
                serialized_data = json.dumps(data)
            except Exception as ser_e:
                logger.error(
                    f"Error serializing data for key {key}: {ser_e} | Data: {repr(data)}"
                )
                return False
            ttl = ttl or self.default_ttl
            self.redis.set(key, serialized_data, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    def get(self, key_type: str, identifier: str) -> Optional[Any]:
        """Get data from cache"""
        try:
            key = self._generate_key(key_type, identifier)
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    def delete(self, key_type: str, identifier: str) -> bool:
        """Delete data from cache"""
        try:
            key = self._generate_key(key_type, identifier)
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    def cache_query(
        self, document_id: str, question: str, answer: str, ttl: Optional[int] = None
    ) -> bool:
        """Cache a query result"""
        key = self._generate_query_key(document_id, question)
        return self.set("query_result", key, {"answer": answer}, ttl)

    def get_cached_query(
        self, document_id: str, question: str
    ) -> Optional[Dict[str, str]]:
        """Get a cached query result"""
        key = self._generate_query_key(document_id, question)
        return self.get("query_result", key)

    def cache_document_chunks(
        self, document_id: str, chunks: Any, ttl: Optional[int] = None
    ) -> bool:
        """Cache document chunks"""
        return self.set("document_chunks", document_id, chunks, ttl)

    def get_cached_document_chunks(self, document_id: str) -> Optional[Any]:
        """Get cached document chunks"""
        return self.get("document_chunks", document_id)

    def delete_document_cache(self, document_id: str) -> bool:
        """Delete all cache entries related to a document"""
        try:
            # Delete document chunks
            self.delete("document_chunks", document_id)

            pattern = self._generate_key("query_result", f"{document_id}:*")
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)

            return True
        except Exception as e:
            logger.error(f"Error deleting document cache: {e}")
            return False


# Create a singleton instance
cache = RedisCache()
