from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.settings import settings
from .db.sqlite_db import init_db
from .routes import documents, chat, analytics, config, voice


app = FastAPI(
    title="MDQA-System RAG API",
    version="2.1.0",
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
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])

@app.on_event("startup")
def on_startup():
    """Initialize the database and eagerly load AI models on application startup."""
    init_db()
    
    # Eagerly load AI models to avoid cold-start latency on first request
    from .rag.models import get_embedding_model, get_reranker_model, get_llm_and_tokenizer
    print("--- [INFO] Eagerly initializing AI models... ---")
    get_embedding_model()
    get_reranker_model()
    get_llm_and_tokenizer()
    print("--- [INFO] All models initialized and ready! ---")

@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify API is running."""
    return {"status": "ok", "version": "2.0.0"}