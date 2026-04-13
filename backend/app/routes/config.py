from fastapi import APIRouter
from ..core.settings import settings

router = APIRouter()

@router.get("/models")
def get_model_config():
    """Returns the current model configuration for all RAG components."""
    return {
        "llm_model": f"{settings.LLM_MODEL_REPO}/{settings.LLM_MODEL_FILE}",
        "llm_gpu_layers": settings.LLM_GPU_LAYERS,
        "llm_context_size": settings.LLM_CONTEXT_SIZE,
        "embedding_model": settings.DEFAULT_EMBEDDING_MODEL,
        "reranker_model": settings.RERANKER_MODEL,
        "chunk_size": settings.DEFAULT_CHUNK_SIZE,
        "chunk_overlap": settings.DEFAULT_CHUNK_OVERLAP,
        "ocr_enabled": settings.OCR_ENABLED,
    }