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
    # --- Model & Cache Configuration ---
    # CORRECTED: Define a central, project-level directory for all Hugging Face models.
    HF_HOME_DIR: str = str(BACKEND_ROOT / "models")
    
    # --- Database ---
    SQLITE_PATH: str = str(BACKEND_ROOT / "data/sqlite/main.db")
    CHROMA_PERSIST_DIR: str = str(BACKEND_ROOT / "data/chroma")
    
    # --- File Storage ---
    UPLOAD_DIR: str = str(BACKEND_ROOT / "uploads")
    
    # --- RAG Defaults ---
    DEFAULT_CHUNK_SIZE: int = 256
    DEFAULT_CHUNK_OVERLAP: int = 64
    
    # --- OCR ---
    OCR_ENABLED: bool = True
    PADDLEOCR_LANG: str = "en"
    PADDLEOCR_USE_GPU: bool = False

settings = Settings()

# This line of code tells the Hugging Face libraries to use our custom directory
# instead of the default hidden cache. It must be set before any models are loaded.
os.environ['HF_HOME'] = settings.HF_HOME_DIR
os.environ['HF_HUB_CACHE'] = settings.HF_HOME_DIR # For newer versions of HF Hub

print(f"--- [INFO] Hugging Face model cache is set to: {os.environ['HF_HOME']} ---")