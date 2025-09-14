from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import documents, query, websocket
from app.config import settings
from app.models.document_db import Base
from app.db.session import engine
import os
import logging

log_level = os.getenv("LOG_LEVEL", "info").upper()
logging.basicConfig(level=log_level)

app = FastAPI(
    title=settings.APP_NAME,
    description="Document-based Question Answering System with RAG",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(query.router, prefix=settings.API_V1_STR)
app.include_router(websocket.router)

# Create the database tables
Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)