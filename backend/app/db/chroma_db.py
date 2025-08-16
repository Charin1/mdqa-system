import chromadb
# CORRECTED: Import the Settings object from chromadb
from chromadb.config import Settings
from functools import lru_cache
from ..core.settings import settings

@lru_cache(maxsize=1)
def get_chroma_client():
    """
    Returns a memoized ChromaDB client instance running in EMBEDDED mode.
    Telemetry is explicitly disabled to prevent known internal bugs.
    """
    # CORRECTED: Instantiate the client with telemetry disabled.
    # This is the definitive fix for the "capture() takes 1 positional argument..." error.
    client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False)
    )
    return client

def get_or_create_collection(name: str = "documents"):
    """
    Retrieves a ChromaDB collection or creates it if it doesn't exist.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})