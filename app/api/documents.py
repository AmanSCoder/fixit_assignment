from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from typing import List
from datetime import datetime
from app.models.document import DocumentResponse, DocumentList
from app.services.minio_service import minio_service
from app.services.celery_tasks import process_document_task
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.crud_documents import (
    create_document, get_document, list_documents, update_document_status, delete_document
)
from app.models.document_db import DocumentStatusEnum
import uuid

router = APIRouter(prefix="/documents", tags=["documents"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a new document"""
    # Check file extension
    allowed_extensions = [".pdf", ".txt", ".docx", ".doc"]
    file_ext = "." + file.filename.split(".")[-1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Upload file to MinIO
    doc_info = await minio_service.upload_document(file)
    
    doc_id = doc_info["id"]
    document_data = {
        "id": doc_id,
        "title": file.filename,
        "description": "",
        "file_name": file.filename,
        "file_size": doc_info["file_size"],
        "file_type": file.content_type,
        "status": DocumentStatusEnum.processing,
    }
    create_document(db, document_data)
    
    # Process document in background
    process_document_task.delay(doc_id, doc_info["object_name"])
    
    return document_data

@router.get("/", response_model=DocumentList)
async def list_documents_endpoint(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List all documents"""
    docs, total = list_documents(db, skip, limit)
    return {
        "documents": [doc.__dict__ for doc in docs],
        "total": total
    }

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Get document details"""
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc.__dict__

@router.delete("/{document_id}")
async def delete_document_endpoint(document_id: str, db: Session = Depends(get_db)):
    """Delete a document"""
    doc = delete_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get the document info
    # doc = documents[document_id]
    
    # Delete from MinIO
    # minio_service.delete_document(document_id, doc["file_name"])
    
    # Remove from document store
    # del documents[document_id]
    
    # In a real implementation, you would also:
    # 1. Delete embeddings from vector store
    # 2. Delete cached data from Redis
    
    return {"message": "Document deleted successfully"}