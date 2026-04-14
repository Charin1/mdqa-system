"""
Voice Model Loading Module.

Lazy-loaded singletons for all voice models.
Both models follow the same @lru_cache pattern — loaded once on first
request, then reused for all subsequent calls.

  STT: faster-whisper (OpenAI Whisper)
       ~150 MB for 'base' model, runs on CPU with int8

  TTS: Kokoro-82M (kokoro library)
       ~300 MB, runs on CPU or Apple Silicon MPS
       No separate server needed — loads in-process like Whisper.

Memory budget for 16 GB system:
  LLM (8B Q2_K)  ~4.0 GB
  BGE-M3          ~1.5 GB
  Whisper base    ~0.15 GB
  Kokoro 82M      ~0.30 GB
  OS + Python     ~3.5 GB
  ─────────────────────────
  Total           ~9.5 GB  ✅
"""

from functools import lru_cache
from ..core.settings import settings


# ─── STT: Whisper ────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_whisper_model():
    """
    Loads and caches a faster-whisper model.
    Model sizes: tiny (~75MB), base (~150MB), small (~500MB), medium (~1.5GB)
    """
    from faster_whisper import WhisperModel

    model_size = settings.WHISPER_MODEL_SIZE
    device = settings.WHISPER_DEVICE
    compute_type = settings.WHISPER_COMPUTE_TYPE

    print(f"--- [INFO] Loading Whisper STT: {model_size} (device={device}, compute={compute_type}) ---")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    print("--- [INFO] Whisper loaded. ---")
    return model


# ─── TTS: Kokoro ─────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_kokoro_pipeline():
    """
    Loads and caches the Kokoro-82M TTS pipeline.
    Lang code 'a' covers all English voices (American + British accents).
    Model is ~300MB and runs on CPU or Apple Silicon MPS with no server.
    """
    from kokoro import KPipeline

    lang_code = 'a'  # 'a' = American/British English
    print(f"--- [INFO] Loading Kokoro TTS pipeline (lang={lang_code}) ---")
    pipeline = KPipeline(lang_code=lang_code)
    print("--- [INFO] Kokoro TTS loaded. ---")
    return pipeline
