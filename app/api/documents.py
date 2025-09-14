from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from typing import List
from datetime import datetime
from app.models.document import DocumentResponse, DocumentList, DocumentStatus
from app.services.minio_service import minio_service
from app.services.celery_tasks import process_document_task
import uuid

router = APIRouter(prefix="/documents", tags=["documents"])

# TODO replace with proper database 
from app.db.memory import documents

@router.post("/", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)): # TODO verify this line
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
    document = {
        "id": doc_id,
        "title": file.filename,  
        "description": "",
        "file_name": file.filename,
        "file_size": doc_info["file_size"],
        "file_type": file.content_type,
        "created_at": datetime.now(),
        "status": DocumentStatus.processing
    }
    
    # Store document info
    documents[doc_id] = document
    
    # Process document in background
    process_document_task.delay(doc_id, doc_info["object_name"])
    
    return document

@router.get("/", response_model=DocumentList)
async def list_documents(skip: int = 0, limit: int = 10):
    """List all documents"""
    doc_list = list(documents.values())
    return {
        "documents": doc_list[skip:skip+limit],
        "total": len(doc_list)
    }

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get document details"""
    if document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")
    return documents[document_id]

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    if document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get the document info
    doc = documents[document_id]
    
    # Delete from MinIO
    minio_service.delete_document(document_id, doc["file_name"])
    
    # Remove from document store
    del documents[document_id]
    
    # In a real implementation, you would also:
    # 1. Delete embeddings from vector store
    # 2. Delete cached data from Redis
    
    return {"message": "Document deleted successfully"}