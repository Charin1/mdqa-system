"""
Voice API Routes.

Endpoints:
  GET  /api/voice/voices      – List all available TTS voice presets
  POST /api/voice/transcribe  – Upload audio → get transcribed text
  POST /api/voice/synthesize  – Send text → get WAV audio back
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List

from ..services.voice_service import VoiceService
from ..core.settings import settings

router = APIRouter()


class TTSRequest(BaseModel):
    """Request body for text-to-speech synthesis."""
    text: str
    voice: Optional[str] = None  # Falls back to settings.TTS_VOICE


class TranscriptionResponse(BaseModel):
    """Response body for speech-to-text transcription."""
    text: str


class VoicePreset(BaseModel):
    id: str
    label: str
    gender: str
    accent: str


# ─── Voices List Endpoint ─────────────────────────────────────

@router.get("/voices", response_model=List[VoicePreset])
def list_voices():
    """
    Returns all available Voxtral TTS voice presets.
    Used by the frontend to populate the voice selector dropdown.
    """
    service = VoiceService()
    return service.list_voices()


# ─── STT Endpoint ─────────────────────────────────────────────

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Accepts an audio file (WAV, WebM, MP3, OGG) and returns transcribed text.
    Audio is processed locally by faster-whisper. Language is auto-detected.
    """
    if not file.filename and not file.content_type:
        raise HTTPException(status_code=400, detail="No audio file provided.")

    service = VoiceService()
    try:
        text = await service.transcribe(file)
        return TranscriptionResponse(text=text)
    except Exception as e:
        print(f"--- [ERROR] Transcription failed: {e} ---")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


# ─── TTS Endpoint ─────────────────────────────────────────────

@router.post("/synthesize")
async def synthesize_speech(payload: TTSRequest):
    """
    Accepts text and returns WAV audio bytes via Voxtral TTS.

    Requires vllm-omni server running. Start with:
        vllm serve mistralai/Voxtral-4B-TTS-2603 --omni --port 8001

    Returns:
        audio/wav response with the synthesized speech.
    """
    if not settings.TTS_ENABLED:
        raise HTTPException(status_code=503, detail="TTS is disabled. Set TTS_ENABLED=true in .env")

    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # Truncate to prevent extremely long synthesis times
    max_chars = 2000
    text = payload.text[:max_chars]
    if len(payload.text) > max_chars:
        print(f"--- [WARNING] TTS text truncated from {len(payload.text)} to {max_chars} chars ---")

    service = VoiceService()
    try:
        wav_bytes = await service.synthesize(text, voice=payload.voice)
        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline; filename=\"speech.wav\"",
                "Content-Length": str(len(wav_bytes)),
            },
        )
    except RuntimeError as e:
        # Specific errors from our service layer (connection issues, etc.)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"--- [ERROR] Speech synthesis failed: {e} ---")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")
