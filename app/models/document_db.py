from sqlalchemy import Column, String, DateTime, Integer, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class DocumentStatusEnum(str, enum.Enum):
    processing = "processing"
    ready = "ready"
    failed = "failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    file_name = Column(String, nullable=False)
    file_size = Column(Integer)
    file_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(DocumentStatusEnum), default=DocumentStatusEnum.processing)