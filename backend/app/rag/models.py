"""
Centralized Model Loading Module.

Single source of truth for all AI model instances.
All models load lazily via @lru_cache on first use.

LLM:       llama-cpp-python (Llama) — GGUF inference with Metal/CUDA GPU
Embedding: sentence-transformers
Re-ranker: sentence-transformers CrossEncoder
"""

from functools import lru_cache
from ..core.settings import settings
import os


@lru_cache(maxsize=1)
def get_embedding_model():
    """Loads and caches the embedding model."""
    from sentence_transformers import SentenceTransformer
    model_name = settings.DEFAULT_EMBEDDING_MODEL
    print(f"--- [INFO] Loading embedding model: {model_name} ---")
    return SentenceTransformer(model_name)


@lru_cache(maxsize=1)
def get_reranker_model():
    """Loads and caches the Cross-Encoder re-ranking model."""
    from sentence_transformers import CrossEncoder
    model_name = settings.RERANKER_MODEL
    print(f"--- [INFO] Loading re-ranking model: {model_name} ---")
    return CrossEncoder(model_name)


@lru_cache(maxsize=1)
def get_llm_and_tokenizer():
    """
    Downloads (if needed) and loads the GGUF model via llama-cpp-python.

    llama-cpp-python (Llama class):
      - Proper Apple Silicon Metal support (n_gpu_layers=-1 offloads all layers)
      - Actively maintained, full GGUF support
      - Streaming output: chunk["choices"][0]["text"]

    Returns (llm, tokenizer) — tokenizer is None (llama-cpp-python handles
    tokenization internally; chat templates are applied via prompt formatting).
    """
    from llama_cpp import Llama
    from huggingface_hub import hf_hub_download

    repo_id = settings.LLM_MODEL_REPO
    filename = settings.LLM_MODEL_FILE
    n_gpu_layers = settings.LLM_GPU_LAYERS  # -1 = offload all to Metal/CUDA

    print(f"--- [INFO] Locating GGUF model: {repo_id}/{filename} ---")
    model_path = hf_hub_download(repo_id=repo_id, filename=filename)
    print(f"--- [INFO] Model path: {model_path} ---")

    print(f"--- [INFO] Loading LLM via llama-cpp-python (n_gpu_layers={n_gpu_layers}) ---")
    llm = Llama(
        model_path=model_path,
        n_ctx=settings.LLM_CONTEXT_SIZE,
        n_gpu_layers=n_gpu_layers,
        verbose=False,           # Disable verbose logs now that it's working
    )
    print("--- [INFO] LLM loaded successfully! ---")

    # tokenizer=None — llama-cpp-python handles tokenization internally
    return llm, None