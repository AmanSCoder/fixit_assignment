from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class QueryRequest(BaseModel):
    document_id: str
    question: str


class QueryResponse(BaseModel):
    id: str
    document_id: str
    question: str
    answer: str
    created_at: datetime
    execution_time: float
    context_chunks: Optional[List[str]] = None


class QueryHistoryItem(BaseModel):
    id: str
    document_id: str
    question: str
    answer: str
    created_at: datetime


class QueryHistory(BaseModel):
    queries: List[QueryHistoryItem]
    total: int
