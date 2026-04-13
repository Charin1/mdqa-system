"""
Centralized Model Loading Module.

This is the SINGLE source of truth for all AI model instances.
All models are loaded lazily via @lru_cache and configured through settings.py.

Models used:
  - LLM: Configurable GGUF via ctransformers (Default: Mistral-7B)
  - Embedding: all-MiniLM-L6-v2 via sentence-transformers (~80MB)
  - Re-ranker: cross-encoder/ms-marco-MiniLM-L-6-v2 via sentence-transformers (~80MB)
"""

from ..core.settings import settings

import os
from functools import lru_cache
from sentence_transformers import SentenceTransformer, CrossEncoder
from ctransformers import AutoModelForCausalLM
from transformers import AutoTokenizer
from huggingface_hub import hf_hub_download


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Loads and caches the embedding model."""
    model_name = settings.DEFAULT_EMBEDDING_MODEL
    print(f"--- [INFO] Loading embedding model: {model_name} ---")
    return SentenceTransformer(model_name)


@lru_cache(maxsize=1)
def get_reranker_model() -> CrossEncoder:
    """Loads and caches the Cross-Encoder re-ranking model."""
    model_name = settings.RERANKER_MODEL
    print(f"--- [INFO] Loading re-ranking model: {model_name} ---")
    return CrossEncoder(model_name)


@lru_cache(maxsize=1)
def get_llm_and_tokenizer():
    """
    Downloads (if needed) and loads the GGUF LLM via ctransformers.
    Also loads the tokenizer via transformers (required by ctransformers pipeline).
    """
    repo_id = settings.LLM_MODEL_REPO
    filename = settings.LLM_MODEL_FILE
    model_type = settings.LLM_MODEL_TYPE
    
    print(f"--- [INFO] Loading tokenizer from HF: {repo_id} ---")
    # ctransformers doesn't handle chat templates well on its own, so we need the tokenizer
    # We use trust_remote_code=True for models like Qwen/Mistral/etc.
    try:
        tokenizer = AutoTokenizer.from_pretrained(repo_id, trust_remote_code=True)
    except Exception as e:
        print(f"--- [WARNING] Failed to load tokenizer from {repo_id}: {e} ---")
        print("--- [INFO] Falling back to default tokenizer behavior ---")
        tokenizer = None
    
    print(f"--- [INFO] Downloading/locating GGUF model: {repo_id}/{filename} ---")
    
    # We use ctransformers AutoModelForCausalLM directly
    # Note: gpu_layers=50 is standard for Apple Silicon on 8B models
    gpu_layers = 50 if settings.LLM_GPU_LAYERS == -1 else settings.LLM_GPU_LAYERS
    
    print(f"--- [INFO] Loading LLM with ctransformers (Type: {model_type}, GPU layers: {gpu_layers}) ---")
    
    llm = AutoModelForCausalLM.from_pretrained(
        repo_id,
        model_file=filename,
        model_type=model_type,  # Configurable: mistral, llama, etc.
        gpu_layers=gpu_layers,
        context_length=settings.LLM_CONTEXT_SIZE,
        hf=False # Disable buggy HF compatibility mode for stability
    )
    
    print("--- [INFO] LLM loaded successfully! ---")
    return llm, tokenizer