from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
import uuid
from datetime import datetime
import time
from typing import List, Dict, Any
from app.models.query import QueryRequest, QueryResponse, QueryHistory, QueryHistoryItem
from app.core.rag_engine import rag_engine
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

# TODO replace with proper database
query_history = {}


@router.post("/stream")
async def query_stream(request: QueryRequest):
    """Submit a query and stream the response"""
    document_id = request.document_id
    question = request.question

    # Create a streaming response
    async def generate():
        try:
            query_id = str(uuid.uuid4())
            start_time = time.time()
            full_answer = ""

            # Process query with streaming
            async for token, _ in rag_engine.process_query_stream(
                document_id, question
            ):
                full_answer += token
                yield token

            # Store in history
            execution_time = time.time() - start_time
            query_history[query_id] = {
                "id": query_id,
                "document_id": document_id,
                "question": question,
                "answer": full_answer,
                "created_at": datetime.now(),
                "execution_time": execution_time,
            }
        except Exception as e:
            logger.error(f"Error in streaming query: {e}")
            yield f"Error processing your query: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Submit a query and get a response"""
    try:
        document_id = request.document_id
        question = request.question

        # Process the query
        answer, execution_time, context_chunks = await rag_engine.process_query(
            document_id, question
        )

        # Generate a query ID
        query_id = str(uuid.uuid4())

        # Store in history
        query_history[query_id] = {
            "id": query_id,
            "document_id": document_id,
            "question": question,
            "answer": answer,
            "created_at": datetime.now(),
            "execution_time": execution_time,
        }

        return {
            "id": query_id,
            "document_id": document_id,
            "question": question,
            "answer": answer,
            "created_at": datetime.now(),
            "execution_time": execution_time,
            "context_chunks": context_chunks,
        }
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.get("/history", response_model=QueryHistory)
async def get_query_history(skip: int = 0, limit: int = 10):
    """Get query history"""
    history_list = list(query_history.values())
    history_list.sort(key=lambda x: x["created_at"], reverse=True)

    return {"queries": history_list[skip : skip + limit], "total": len(history_list)}
