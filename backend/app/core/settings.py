import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# --- Step 1: Define the Backend Root Directory ---
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent

# --- Step 2: Construct the absolute path to the .env file ---
ENV_FILE_PATH = BACKEND_ROOT / ".env"
if ENV_FILE_PATH.is_file():
    load_dotenv(dotenv_path=ENV_FILE_PATH)

class Settings(BaseSettings):
    """
    Manages application settings. All model names and paths are configurable
    via the .env file for easy swapping without touching code.
    """
    # --- Model & Cache Configuration ---
    HF_HOME_DIR: str = str(BACKEND_ROOT / "models")
    
    # --- Database ---
    SQLITE_PATH: str = str(BACKEND_ROOT / "data/sqlite/main.db")
    CHROMA_PERSIST_DIR: str = str(BACKEND_ROOT / "data/chroma")
    
    # --- File Storage ---
    UPLOAD_DIR: str = str(BACKEND_ROOT / "uploads")
    
    # --- LLM Configuration (ctransformers / GGUF) ---
    # Default to Mistral-7B-Instruct-v0.2 (Safe Fallback)
    LLM_MODEL_REPO: str = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
    LLM_MODEL_FILE: str = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    LLM_MODEL_TYPE: str = "mistral" # New setting: mistral, llama, qwen2 (if supported)
    
    # -1 = auto-detect (for ctransformers logic in models.py)
    LLM_GPU_LAYERS: int = -1 
    LLM_CONTEXT_SIZE: int = 4096
    LLM_MAX_TOKENS: int = 4096

    # --- Embedding Model ---
    DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # --- Re-ranker Model ---
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # --- RAG Defaults ---
    DEFAULT_CHUNK_SIZE: int = 256
    DEFAULT_CHUNK_OVERLAP: int = 64
    
    # --- OCR ---
    OCR_ENABLED: bool = True
    PADDLEOCR_LANG: str = "en"
    PADDLEOCR_USE_GPU: bool = False

    # --- Voice / STT (Whisper) ---
    WHISPER_MODEL_SIZE: str = "base"           # tiny, base, small, medium
    WHISPER_DEVICE: str = "cpu"                # cpu or auto (for MPS)
    WHISPER_COMPUTE_TYPE: str = "int8"          # int8 for speed on CPU

    # --- Voice / TTS (Kokoro-82M — loads in-process like Whisper) ---
    TTS_VOICE: str = "af_heart"       # Default Kokoro voice
    TTS_ENABLED: bool = True
    TTS_SPEED: float = 1.0             # Speech speed (0.5 = slow, 2.0 = fast)

    # --- Memory Management ---
    PYTORCH_MPS_HIGH_WATERMARK_RATIO: float = 0.0

settings = Settings()

# This tells the Hugging Face libraries to use our custom directory
# instead of the default hidden cache.
os.environ['HF_HOME'] = settings.HF_HOME_DIR
os.environ['HF_HUB_CACHE'] = settings.HF_HOME_DIR
os.environ['SENTENCE_TRANSFORMERS_HOME'] = settings.HF_HOME_DIR
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = str(settings.PYTORCH_MPS_HIGH_WATERMARK_RATIO)

print(f"--- [INFO] Hugging Face model cache: {os.environ['HF_HOME']} ---")
print(f"--- [INFO] Sentence Transformers cache: {os.environ['SENTENCE_TRANSFORMERS_HOME']} ---")
print(f"--- [INFO] LLM: {settings.LLM_MODEL_REPO}/{settings.LLM_MODEL_FILE} ({settings.LLM_MODEL_TYPE}) ---")
print(f"--- [INFO] Embedding: {settings.DEFAULT_EMBEDDING_MODEL} ---")
print(f"--- [INFO] Re-ranker: {settings.RERANKER_MODEL} ---")