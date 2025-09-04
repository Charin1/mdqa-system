from functools import lru_cache
from sentence_transformers import SentenceTransformer, CrossEncoder
from ctransformers import AutoModelForCausalLM
from transformers import AutoTokenizer
import os
from huggingface_hub import login

# --- Hugging Face Login ---
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN:
    print("--- [INFO] Logging in to Hugging Face Hub ---")
    login(token=HF_TOKEN)
else:
    print("--- [WARNING] HF_TOKEN environment variable not set. ---")


# --- Model Loading Functions ---

@lru_cache(maxsize=1)
def get_embedding_model():
    """Loads and caches the state-of-the-art BAAI/bge-m3 embedding model."""
    return SentenceTransformer("BAAI/bge-m3")

@lru_cache(maxsize=1)
def get_reranker_model():
    """Loads and caches a lightweight but powerful Cross-Encoder model for re-ranking."""
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

@lru_cache(maxsize=1)
def get_llm_and_tokenizer():
    """
    Initializes and caches the Llama-3-8B-Instruct GGUF model and a standard tokenizer.
    """
    
    llm = AutoModelForCausalLM.from_pretrained(
        "TheBloke/LLaMA-Pro-8B-Instruct-GGUF",
        model_file="llama-pro-8b-instruct.Q2_K.gguf",
        model_type="llama",
        gpu_layers=50 
    )
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
    
    return llm, tokenizer