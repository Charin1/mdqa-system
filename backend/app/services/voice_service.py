"""
Voice Service Module.

Business logic for:
  - Speech-to-Text (STT): Audio file → transcribed text via faster-whisper.
  - Text-to-Speech (TTS): Text → WAV audio bytes via Kokoro-82M.

Both models load in-process (no separate server needed), following the
same lazy @lru_cache pattern. Memory cost: ~150 MB (Whisper) + ~300 MB (Kokoro).
"""

import io
import tempfile
import os
import numpy as np
import soundfile as sf
from fastapi import UploadFile

from ..rag.voice_models import get_whisper_model, get_kokoro_pipeline
from ..core.settings import settings


# All available Kokoro voices grouped by accent and gender
KOKORO_VOICES = [
    # American Female
    {"id": "af_heart",    "label": "Heart (American Female)",    "gender": "Female", "accent": "American"},
    {"id": "af_bella",    "label": "Bella (American Female)",    "gender": "Female", "accent": "American"},
    {"id": "af_nicole",   "label": "Nicole (American Female)",   "gender": "Female", "accent": "American"},
    {"id": "af_sky",      "label": "Sky (American Female)",      "gender": "Female", "accent": "American"},
    # American Male
    {"id": "am_adam",     "label": "Adam (American Male)",       "gender": "Male",   "accent": "American"},
    {"id": "am_michael",  "label": "Michael (American Male)",    "gender": "Male",   "accent": "American"},
    # British Female
    {"id": "bf_emma",     "label": "Emma (British Female)",      "gender": "Female", "accent": "British"},
    {"id": "bf_isabella", "label": "Isabella (British Female)",  "gender": "Female", "accent": "British"},
    # British Male
    {"id": "bm_george",   "label": "George (British Male)",      "gender": "Male",   "accent": "British"},
    {"id": "bm_lewis",    "label": "Lewis (British Male)",        "gender": "Male",   "accent": "British"},
]

VOICE_IDS = {v["id"] for v in KOKORO_VOICES}


class VoiceService:
    """Handles speech transcription and speech synthesis."""

    async def transcribe(self, audio_file: UploadFile) -> str:
        """
        Transcribes an uploaded audio file to text using faster-whisper.
        Accepts WAV, WebM, MP3, OGG, or any ffmpeg-compatible format.
        Returns the full transcribed text as a single string.
        """
        suffix = os.path.splitext(audio_file.filename or "audio.webm")[1] or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            model = get_whisper_model()
            print(f"--- [INFO] Transcribing audio: {audio_file.filename} ({len(content)} bytes) ---")

            segments, info = model.transcribe(
                tmp_path,
                beam_size=5,
                language=None,    # Auto-detect language
                vad_filter=True,  # Filter out silence
            )

            # Consume the generator before file cleanup
            text_parts = [segment.text.strip() for segment in segments]
            transcribed_text = " ".join(text_parts)

            print(f"--- [INFO] Transcription done ({info.language}, {info.duration:.1f}s): '{transcribed_text[:100]}' ---")
            return transcribed_text

        finally:
            os.unlink(tmp_path)

    async def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """
        Synthesizes speech from text using Kokoro-82M.

        Runs entirely in-process (no server needed). ~300 MB RAM.
        First call loads the model (~2s); subsequent calls are fast.

        Args:
            text:  The text to speak.
            voice: Kokoro voice ID (e.g. "af_heart"). Defaults to settings.TTS_VOICE.

        Returns:
            Raw WAV audio bytes at 24kHz.
        """
        voice = voice or settings.TTS_VOICE

        # Validate — fall back gracefully to the default
        if voice not in VOICE_IDS:
            print(f"--- [WARNING] Unknown voice '{voice}', using default '{settings.TTS_VOICE}' ---")
            voice = settings.TTS_VOICE

        print(f"--- [INFO] Synthesizing speech with Kokoro ({len(text)} chars, voice={voice}) ---")

        pipeline = get_kokoro_pipeline()

        # Generate audio chunks (Kokoro streams sentence-by-sentence)
        audio_chunks = []
        sample_rate = 24000  # Kokoro outputs 24kHz

        for _, _, audio_chunk in pipeline(text, voice=voice, speed=1.0, split_pattern=r'\n+'):
            if audio_chunk is not None and len(audio_chunk) > 0:
                audio_chunks.append(audio_chunk)

        if not audio_chunks:
            raise RuntimeError("Kokoro TTS produced no audio output.")

        audio = np.concatenate(audio_chunks)

        # Normalize to [-1, 1] if needed
        max_val = np.abs(audio).max()
        if max_val > 1.0:
            audio = audio / max_val

        # Encode to WAV bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
        wav_bytes = buffer.getvalue()

        print(f"--- [INFO] Kokoro synthesis complete: {len(wav_bytes)} bytes ---")
        return wav_bytes

    def list_voices(self) -> list[dict]:
        """Returns all available Kokoro voice presets."""
        return KOKORO_VOICES
