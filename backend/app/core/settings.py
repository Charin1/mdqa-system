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
    Manages application settings using absolute paths for reliability.
    """
    # --- Database ---
    SQLITE_PATH: str = str(BACKEND_ROOT / "data/sqlite/main.db")
    
    # CORRECTED: New setting for the embedded ChromaDB data path.
    CHROMA_PERSIST_DIR: str = str(BACKEND_ROOT / "data/chroma")
    
    # REMOVED: These are no longer needed for embedded mode.
    # CHROMA_HOST: str
    # CHROMA_PORT: int
    
    # --- File Storage ---
    UPLOAD_DIR: str = str(BACKEND_ROOT / "uploads")
    
    # --- RAG Defaults ---
    DEFAULT_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    DEFAULT_CHUNK_SIZE: int = 1000
    DEFAULT_CHUNK_OVERLAP: int = 150
    
    # --- OCR ---
    OCR_ENABLED: bool = True
    PADDLEOCR_LANG: str = "en"
    PADDLEOCR_USE_GPU: bool = False

settings = Settings()

print(f"--- [DEBUG] Settings loaded. ChromaDB persistence directory is: {settings.CHROMA_PERSIST_DIR} ---")