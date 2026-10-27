from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.modules.voice.transcriber import voice_transcriber

router = APIRouter()


class TranscribeResponse(BaseModel):
    text: str
    language: str
    confidence: float
    needs_confirmation: bool


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_voice(
    file: UploadFile = File(...),
):
    """
    Accepts multipart audio (wav/m4a, max 15s).
    Returns transcribed text, language (en, hi, pa), confidence, and needs_confirmation flag.
    """
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio file provided.",
        )

    # 15 seconds of 16-bit 44.1kHz stereo is ~2.6 MB; 16kHz 16-bit mono is ~480 KB.
    # Cap at 3 MB to enforce <= 15 s audio limit.
    if len(content) > 3 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio exceeds maximum duration of 15 seconds.",
        )

    result = voice_transcriber.transcribe_audio(
        audio_bytes=content,
        filename=file.filename or "audio.wav",
    )

    return TranscribeResponse(
        text=str(result["text"]),
        language=str(result["language"]),
        confidence=float(result["confidence"]),
        needs_confirmation=bool(result["needs_confirmation"]),
    )
