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
# These functions rely on the HF_HOME environment variable being set correctly
# in settings.py, which directs all downloads and lookups to our local `backend/models` folder.

@lru_cache(maxsize=1)
def get_embedding_model():
    """Loads and caches the BAAI/bge-m3 embedding model from the local cache."""
    print("--- [INFO] Loading embedding model: BAAI/bge-m3 ---")
    return SentenceTransformer("BAAI/bge-m3")

@lru_cache(maxsize=1)
def get_reranker_model():
    """Loads and caches a Cross-Encoder model for re-ranking from the local cache."""
    print("--- [INFO] Loading re-ranking model: cross-encoder/ms-marco-MiniLM-L-6-v2 ---")
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

@lru_cache(maxsize=1)
def get_llm_and_tokenizer():
    """
    Initializes and caches the Llama-3 GGUF model and its tokenizer.
    The tokenizer is loaded from the HF_HOME cache, and the GGUF model
    is downloaded by ctransformers into the same cache.
    """
    print("--- [INFO] Loading tokenizer: meta-llama/Meta-Llama-3-8B-Instruct ---")
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
    
    print("--- [INFO] Loading generation model: TheBloke/Meta-Llama-3-8B-Instruct-GGUF ---")
    llm = AutoModelForCausalLM.from_pretrained(
        "TheBloke/LLaMA-Pro-8B-Instruct-GGUF",
        model_file="llama-pro-8b-instruct.Q2_K.gguf",
        model_type="llama",
        # This will automatically use the best hardware available (CUDA, Metal, CPU).
        # On Mac, set a number to offload layers to the GPU for a massive speed boost.
        # On Windows/Linux with no NVIDIA GPU, it will run efficiently on the CPU.
        gpu_layers=50 
    )
    
    return llm, tokenizer