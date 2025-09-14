import io
from minio import Minio
from minio.error import S3Error
import uuid
from fastapi import UploadFile, HTTPException
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MinioService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False  # Set to True for HTTPS
        )
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the documents bucket exists"""
        try:
            if not self.client.bucket_exists(settings.MINIO_BUCKET_NAME):
                self.client.make_bucket(settings.MINIO_BUCKET_NAME)
                logger.info(f"Created bucket {settings.MINIO_BUCKET_NAME}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize storage")
    
    async def upload_document(self, file: UploadFile) -> dict:
        """Upload a document to MinIO storage"""
        try:
            # Generate a unique file ID and construct the object name
            file_id = str(uuid.uuid4())
            object_name = f"{file_id}/{file.filename}"
            
            # Read the file content
            content = await file.read()
            if len(content) > settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds the maximum allowed ({settings.MAX_DOCUMENT_SIZE_MB}MB)"
                )
            
            # Upload the file to MinIO
            self.client.put_object(
                settings.MINIO_BUCKET_NAME,
                object_name,
                io.BytesIO(content),
                len(content),
                file.content_type
            )
            
            # Return document details
            return {
                "id": file_id,
                "file_name": file.filename,
                "file_size": len(content),
                "file_type": file.content_type,
                "object_name": object_name
            }
        except S3Error as e:
            logger.error(f"Error uploading document: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")
    
    def get_document(self, document_id: str, file_name: str) -> io.BytesIO:
        """Get a document from MinIO storage"""
        try:
            object_name = f"{document_id}/{file_name}"
            response = self.client.get_object(settings.MINIO_BUCKET_NAME, object_name)
            return io.BytesIO(response.read())
        except S3Error as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            raise HTTPException(status_code=404, detail="Document not found")
    
    def delete_document(self, document_id: str, file_name: str) -> bool:
        """Delete a document from MinIO storage"""
        try:
            object_name = f"{document_id}/{file_name}"
            self.client.remove_object(settings.MINIO_BUCKET_NAME, object_name)
            return True
        except S3Error as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise HTTPException(status_code=404, detail="Document not found")

# Create a singleton instance
minio_service = MinioService()