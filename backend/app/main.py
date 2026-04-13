from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.settings import settings
from .db.sqlite_db import init_db
from .routes import documents, chat, analytics, config


app = FastAPI(
    title="MDQA-System RAG API",
    version="2.0.0",
    description="A modern, fully offline RAG API for document intelligence. Powered by Qwen3 + llama-cpp-python.",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(config.router, prefix="/api/config", tags=["Configuration"])

@app.on_event("startup")
def on_startup():
    """Initialize the database on application startup."""
    init_db()

@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify API is running."""
    return {"status": "ok", "version": "2.0.0"}