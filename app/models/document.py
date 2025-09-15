from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.models.document_table import DocumentStatusEnum


class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    file_name: str
    file_size: Optional[int]
    file_type: Optional[str]
    created_at: Optional[datetime] = None  # <-- Make this optional
    status: DocumentStatusEnum

    class Config:
        orm_mode = True


class DocumentList(BaseModel):
    documents: List[DocumentResponse]
    total: int
