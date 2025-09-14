from sqlalchemy.orm import Session
from app.models.document_db import Document, DocumentStatusEnum

def create_document(db: Session, doc_data: dict):
    db_doc = Document(**doc_data)
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def get_document(db: Session, document_id: str):
    return db.query(Document).filter(Document.id == document_id).first()

def list_documents(db: Session, skip: int = 0, limit: int = 10):
    docs = db.query(Document).offset(skip).limit(limit).all()
    total = db.query(Document).count()
    return docs, total

def update_document_status(db: Session, document_id: str, status: DocumentStatusEnum):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        doc.status = status
        db.commit()
        db.refresh(doc)
    return doc

def delete_document(db: Session, document_id: str):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        db.delete(doc)
        db.commit()
    return doc