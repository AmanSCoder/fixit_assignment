from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api import documents, query, websocket
from app.config import settings
from app.models.document_table import Base
from app.db.session import engine
import os
import logging
import time

log_level = os.getenv("LOG_LEVEL", "info").upper()
logging.basicConfig(level=log_level)

app = FastAPI(
    title=settings.APP_NAME,
    description="Document-based Question Answering System with RAG",
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logging.exception(f"Request failed: {e}")
        # Re-raise to let FastAPI handle it
        raise
    finally:
        process_time = time.time() - start_time
        logging.info(f"Request processed in {process_time:.2f} seconds")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(documents.router) 
app.include_router(query.router)
app.include_router(websocket.router)

# Create the database tables
Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    logging.info("Starting application")
    try:
        # Test database connection
        from app.db.session import SessionLocal
        from sqlalchemy import text  # Add this import
        db = SessionLocal()
        db.execute(text("SELECT 1"))  # Use text() here
        db.close()
        logging.info("Database connection successful")
    except Exception as e:
        logging.exception(f"Database connection failed: {e}")


if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)

