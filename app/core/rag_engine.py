from typing import List, Dict, Any, Tuple, Optional, AsyncGenerator
import time
from app.core.vector_store import vector_store
from app.services.ai_service import ai_service
from app.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class RAGEngine:
    def __init__(self):
        logger.info("RAGEngine initialized.")

    async def process_query(
        self, document_id: str, question: str
    ) -> Tuple[str, float, List[str]]:
        """
        Process a query using RAG and return the answer, execution time, and relevant context chunks
        """
        logger.info(
            f"Processing query for document_id={document_id}, question='{question}'"
        )
        start_time = time.time()

        # Check cache first
        cached_result = cache.get_cached_query(document_id, question)
        if cached_result:
            logger.info(f"Cache hit for query {document_id}:{question}")
            end_time = time.time()
            execution_time = end_time - start_time
            logger.debug(f"Returning cached answer: {cached_result['answer']}")
            return cached_result["answer"], execution_time, []

        # Generate embedding for the question
        logger.debug(f"Generating embedding for question: '{question}'")
        question_embedding = await ai_service.generate_embedding(question)
        logger.debug(f"Generated embedding for question: {question_embedding}")

        # Search for relevant chunks
        logger.debug(
            f"Searching for relevant chunks in vector store for document_id={document_id}"
        )
        search_results = vector_store.search_chunks(
            query_embedding=question_embedding, document_id=document_id, top_k=5
        )
        logger.debug(f"Search results: {search_results}")

        if not search_results["documents"] or not search_results["documents"][0]:
            logger.warning(
                f"No relevant information found for document_id={document_id}, question='{question}'"
            )
            return (
                "I couldn't find any relevant information to answer your question.",
                time.time() - start_time,
                [],
            )

        # Construct context from retrieved chunks
        context_chunks = search_results["documents"][0]
        logger.debug(f"Context chunks: {context_chunks}")
        context = "\n\n".join(context_chunks)

        # Generate answer
        logger.debug(f"Generating answer for question: '{question}' with context.")
        answer = await ai_service.generate_answer(question, context)
        logger.info(f"Generated answer: {answer}")

        # Cache the result
        logger.debug(
            f"Caching result for document_id={document_id}, question='{question}'"
        )
        cache.cache_query(document_id, question, answer)

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Query processed in {execution_time:.2f} seconds.")

        return answer, execution_time, context_chunks

    async def process_query_stream(
        self, document_id: str, question: str
    ) -> AsyncGenerator[Tuple[str, Optional[List[str]]], None]:
        """
        Process a query using RAG and stream the answer tokens
        """
        logger.info(
            f"Processing streaming query for document_id={document_id}, question='{question}'"
        )
        # Check cache first
        cached_result = cache.get_cached_query(document_id, question)
        if cached_result:
            logger.info(f"Cache hit for streaming query {document_id}:{question}")
            logger.debug(f"Yielding cached answer: {cached_result['answer']}")
            yield cached_result["answer"], []
            return

        # Generate embedding for the question
        logger.debug(f"Generating embedding for question: '{question}'")
        question_embedding = await ai_service.generate_embedding(question)
        logger.debug(f"Generated embedding for question: {question_embedding}")

        # Search for relevant chunks
        logger.debug(
            f"Searching for relevant chunks in vector store for document_id={document_id}"
        )
        search_results = vector_store.search_chunks(
            query_embedding=question_embedding, document_id=document_id, top_k=50
        )
        logger.debug(f"Search results: {search_results}")

        if not search_results["documents"] or not search_results["documents"][0]:
            logger.warning(
                f"No relevant information found for document_id={document_id}, question='{question}'"
            )
            yield "I couldn't find any relevant information to answer your question.", []
            return

        # Construct context from retrieved chunks
        context_chunks = search_results["documents"]
        context = "\n\n".join(context_chunks)
        logger.debug(f"Context: {context}")

        # Generate and stream the answer
        logger.debug(f"Streaming answer for question: '{question}' with context.")
        full_answer = ""
        async for token in ai_service.generate_answer_stream(question, context):
            full_answer += token
            logger.debug(f"Streaming token: {token}")
            yield token, None

        # Cache the complete answer
        logger.debug(
            f"Caching streamed result for document_id={document_id}, question='{question}'"
        )
        cache.cache_query(document_id, question, full_answer)
        logger.info(
            f"Streaming query processed and cached for document_id={document_id}, question='{question}'"
        )


# Create a singleton instance
rag_engine = RAGEngine()
