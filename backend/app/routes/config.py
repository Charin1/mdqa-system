from fastapi import APIRouter
from ..core.settings import settings

router = APIRouter()

@router.get("/models")
def get_model_config():
    """Returns the current embedding model and chunking configuration."""
    return {
        "embedding_model": settings.DEFAULT_EMBEDDING_MODEL,
        "chunk_size": settings.DEFAULT_CHUNK_SIZE,
        "chunk_overlap": settings.DEFAULT_CHUNK_OVERLAP,
    }