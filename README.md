
# DocuQuery: Document-based Question Answering System

## 1. Project Overview

**DocuQuery** is a scalable, production-ready system for document-based question answering using Retrieval-Augmented Generation (RAG).  
It allows users to upload documents (PDF, DOCX, DOC, TXT), processes and stores them, and enables users to ask questions about the content.  
The system leverages modern cloud-native components:

- **FastAPI** for the API and WebSocket endpoints
- **MinIO** for object storage (document files)
- **PostgreSQL** for document metadata
- **Qdrant** for vector storage (semantic search)
- **Azure OpenAI** for embeddings and answer generation
- **Redis** for caching
- **Celery** for background processing

### **Main Features**

- **Document Upload:** Users can upload documents via REST API.
- **Background Processing:** Documents are processed asynchronously (text extraction, chunking, embedding).
- **Semantic Search:** Questions are answered by retrieving relevant document's chunks using vector search and generating answers with LLMs.
- **Streaming & Real-time:** Supports both REST and WebSocket streaming for real-time Q&A.
- **Caching:** Frequently asked questions and document chunks are cached for speed.
- **Scalable & Modular:** Easily deployable with Docker Compose and Fly.io.

---

## 2. Caching: When, Where, and Why

### **When & Where is Caching Used?**

Caching is implemented in [`app/utils/cache.py`](app/utils/cache.py) using Redis. It is used in two main scenarios:

1. **Query Result Caching**
   - **Where:**  
     - In the RAG engine ([`app/utils/rag_engine.py`](app/utils/rag_engine.py)), before generating embeddings and answers.
     - Methods: `cache_query`, `get_cached_query`.
   - **When:**  
     - Before answering a question, the system checks if the answer for the same document and question is already cached.
     - If found, it returns the cached answer immediately.
     - After generating a new answer, it is cached for future use.
   - **Why:**  
     - **Performance:** Reduces latency for repeated queries by avoiding redundant computation (embedding, vector search, LLM generation).
     - **Cost Efficiency:** Minimizes repeated calls to external APIs (e.g., Azure OpenAI), saving on compute and API costs.
     - **Scalability:** Reduces load on the backend and vector database for popular queries.

2. **Document Chunk Caching**
   - **Where:**  
     - After processing and chunking a document in the Celery task ([`app/helpers/celery_tasks.py`](app/helpers/celery_tasks.py)).
     - Methods: `cache_document_chunks`, `get_cached_document_chunks`.
   - **When:**  
     - After a document is processed, its chunks are cached for fast retrieval during question answering.
   - **Why:**  
     - **Performance:** Speeds up access to document chunks for frequently queried documents.
     - **Scalability:** Reduces repeated reads from MinIO and re-processing of documents.

---

## 3. Celery: When, Where, and Why

### **When & Where is Celery Used?**

Celery is used for **background processing** of heavy or time-consuming tasks, specifically:

- **Document Processing Pipeline**
  - **Where:**  
    - In the document upload endpoint ([`app/api/documents.py`](app/api/documents.py)), after a document is uploaded.
    - The task is defined in [`app/helpers/celery_tasks.py`](app/helpers/celery_tasks.py).
    - Task: `process_document_task`
  - **When:**  
    - After a document is uploaded and stored in MinIO, the API triggers a Celery task to:
      1. Extract text from the document.
      2. Chunk the text.
      3. Generate embeddings for each chunk.
      4. Store chunks and embeddings in the vector database.
      5. Cache the chunks.
      6. Update the document status in the database.
  - **Why:**  
    - **Non-blocking User Experience:** Uploading and processing large documents (text extraction, embedding, vector DB storage) can take several seconds or minutes. By offloading this work to Celery, the API responds quickly to the user and processes the document in the background.
    - **Reliability & Scalability:** Celery workers can be scaled independently of the API, allowing for robust handling of large workloads. Failed tasks can be retried or monitored.
    - **Separation of Concerns:** Keeps the API endpoints fast and responsive, while heavy lifting is done asynchronously.

---

## 4. System Architecture Diagram

```
User
 │
 │ 1. Upload Document (REST)
 │─────────────────────────────▶ FastAPI API
 │                                 │
 │                                 │ 2. Store file in MinIO
 │                                 │ 3. Store metadata in PostgreSQL
 │                                 │ 4. Trigger Celery Task
 │                                 ▼
 │                        Celery Worker(s)
 │                                 │
 │                                 │ 5. Extract & Chunk Text
 │                                 │ 6. Generate Embeddings (Azure OpenAI)
 │                                 │ 7. Store in Qdrant (Vector DB)
 │                                 │ 8. Cache Chunks (Redis)
 │                                 │ 9. Update Status (PostgreSQL)
 │
 │ 10. Ask Question (REST/WebSocket)
 │─────────────────────────────▶ FastAPI API
 │                                 │
 │                                 │ 11. Check Cache (Redis)
 │                                 │ 12. Generate Embedding (Azure OpenAI)
 │                                 │ 13. Search Chunks (Qdrant)
 │                                 │ 14. Generate Answer (Azure OpenAI)
 │                                 │ 15. Cache Answer (Redis)
 │                                 ▼
 │                        Response to User (Streaming/REST)
```

---

## 5. Key Files

- [`app/api/documents.py`](app/api/documents.py): Document upload, list, get, delete endpoints.
- [`app/helpers/celery_tasks.py`](app/helpers/celery_tasks.py): Celery background task for document processing.
- [`app/utils/document_processor.py`](app/utils/document_processor.py): Text extraction and chunking logic.
- [`app/helpers/ai_helpers.py`](app/helpers/ai_helpers.py): Embedding and answer generation using Azure OpenAI.
- [`app/utils/vector_store.py`](app/utils/vector_store.py): Vector DB (Qdrant) integration.
- [`app/utils/cache.py`](app/utils/cache.py): Redis caching logic.
- [`app/utils/rag_engine.py`](app/utils/rag_engine.py): RAG pipeline for answering questions.
- [`app/api/websocket.py`](app/api/websocket.py): Real-time Q&A via WebSocket.

---

## 6. Summary

- **Caching** is used to speed up repeated queries and chunk retrieval, reducing cost and latency.
- **Celery** is used to process documents asynchronously, keeping the API responsive and scalable.
- The system is modular, cloud-native, and ready for production workloads in document-based Q&A.
---