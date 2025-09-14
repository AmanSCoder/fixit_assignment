from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

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
    status: str = "processing"  # "processing", "ready", "failed"
    
    class Config:
        orm_mode = True

class DocumentList(BaseModel):
    documents: List[DocumentResponse]
    total: int