from typing import List, Dict, Any, Tuple, Optional, AsyncGenerator
import time
from app.core.vector_store import vector_store
from app.services.ai_service import ai_service
from app.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        pass
    
    async def process_query(self, document_id: str, question: str) -> Tuple[str, float, List[str]]:
        """
        Process a query using RAG and return the answer, execution time, and relevant context chunks
        """
        start_time = time.time()
        
        # Check cache first
        cached_result = cache.get_cached_query(document_id, question)
        if cached_result:
            logger.info(f"Cache hit for query {document_id}:{question}")
            end_time = time.time()
            execution_time = end_time - start_time
            return cached_result["answer"], execution_time, []
        
        # Generate embedding for the question
        question_embedding = await ai_service.generate_embedding(question)
        
        # Search for relevant chunks
        search_results = vector_store.search_chunks(
            query_embedding=question_embedding,
            document_id=document_id,
            top_k=5
        )
        
        if not search_results["documents"] or not search_results["documents"][0]:
            return "I couldn't find any relevant information to answer your question.", time.time() - start_time, []
        
        # Construct context from retrieved chunks
        context_chunks = search_results["documents"][0]
        context = "\n\n".join(context_chunks)
        
        # Generate answer
        answer = await ai_service.generate_answer(question, context)
        
        # Cache the result
        cache.cache_query(document_id, question, answer)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        return answer, execution_time, context_chunks
    
    async def process_query_stream(self, document_id: str, question: str) -> AsyncGenerator[Tuple[str, Optional[List[str]]], None]:
        """
        Process a query using RAG and stream the answer tokens
        """
        # Check cache first
        cached_result = cache.get_cached_query(document_id, question)
        if cached_result:
            logger.info(f"Cache hit for query {document_id}:{question}")
            yield cached_result["answer"], []
            return
        
        # Generate embedding for the question
        question_embedding = await ai_service.generate_embedding(question)
        
        # Search for relevant chunks
        search_results = vector_store.search_chunks(
            query_embedding=question_embedding,
            document_id=document_id,
            top_k=5
        )
        
        if not search_results["documents"] or not search_results["documents"][0]:
            yield "I couldn't find any relevant information to answer your question.", []
            return
        
        # Construct context from retrieved chunks
        context_chunks = search_results["documents"][0]
        context = "\n\n".join(context_chunks)
        
        # Generate and stream the answer
        full_answer = ""
        async for token in ai_service.generate_answer_stream(question, context):
            full_answer += token
            yield token, None
        
        # Cache the complete answer
        cache.cache_query(document_id, question, full_answer)

# Create a singleton instance
rag_engine = RAGEngine()