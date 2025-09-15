import io
import os
from typing import List, Dict, Any, Tuple
import logging
from PyPDF2 import PdfReader
import docx
from app.config import settings
from app.helpers.minio_helpers import minio_helper
from app.helpers.ai_helpers import ai_helper

logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    def extract_text(self, file_content: io.BytesIO, file_type: str) -> str:
        """Extract text from a document"""
        if file_type == "application/pdf":
            return self._extract_from_pdf(file_content)
        elif file_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ]:
            return self._extract_from_docx(file_content)
        elif file_type == "text/plain":
            return file_content.read().decode("utf-8")
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _extract_from_pdf(self, file_content: io.BytesIO) -> str:
        """Extract text from PDF"""
        try:
            reader = PdfReader(file_content)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    def _extract_from_docx(self, file_content: io.BytesIO) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(file_content)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []

        chunks = []
        start_idx = 0

        while start_idx < len(text):
            # Extract chunk with size chunk_size
            end_idx = min(start_idx + self.chunk_size, len(text))

            # Find the nearest end of paragraph or sentence
            if end_idx < len(text):
                # First try to find paragraph end
                paragraph_end = text.rfind("\n\n", start_idx, end_idx)
                if (
                    paragraph_end != -1
                    and paragraph_end > start_idx + self.chunk_size // 2
                ):
                    end_idx = paragraph_end + 2
                else:
                    # Try to find sentence end
                    sentence_end_markers = [". ", "! ", "? ", ".\n", "!\n", "?\n"]
                    for marker in sentence_end_markers:
                        sentence_end = text.rfind(marker, start_idx, end_idx)
                        if (
                            sentence_end != -1
                            and sentence_end > start_idx + self.chunk_size // 2
                        ):
                            end_idx = sentence_end + len(marker)
                            break

            # Extract the chunk
            chunk = text[start_idx:end_idx].strip()
            if chunk:
                chunks.append(chunk)

            # Move the start index for the next chunk, accounting for overlap
            start_idx = max(start_idx + 1, end_idx - self.chunk_overlap)

        return chunks

    def process_document(
        self, document_id: str, object_name: str
    ) -> Tuple[List[str], List[Dict]]:
        """Process a document and return chunks with metadata"""
        # Retrieve file info from object_name
        file_name = object_name.split("/")[-1]
        file_type = self._get_content_type(file_name)

        # Get document content from MinIO
        file_content = minio_helper.get_document(document_id, file_name)

        # Extract text from document
        text = self.extract_text(file_content, file_type)

        # Split text into chunks
        chunks = self.chunk_text(text)

        # Create metadata for each chunk
        metadatas = []
        for i, chunk in enumerate(chunks):
            metadatas.append(
                {
                    "document_id": document_id,
                    "chunk_index": i,
                    "filename": file_name,
                    "total_chunks": len(chunks),
                }
            )

        return chunks, metadatas

    def _get_content_type(self, file_name: str) -> str:
        """Determine content type from file extension"""
        ext = file_name.split(".")[-1].lower()
        content_type_map = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "doc": "application/msword",
            "txt": "text/plain",
        }
        return content_type_map.get(ext, "application/octet-stream")


# Create a singleton instance
document_processor = DocumentProcessor()
