from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    processing = "processing"
    ready = "ready"
    failed = "failed"

class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    file_name: str
    file_size: int
    file_type: str
    created_at: datetime
    status: DocumentStatus  # <-- use Enum here

    class Config:
        orm_mode = True

class DocumentList(BaseModel):
    documents: List[DocumentResponse]
    total: int