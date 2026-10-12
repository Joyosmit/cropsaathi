"""POST /api/v1/voice/stt and /api/v1/voice/tts."""
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import Response
from app.config import use_mock
from app.models.pydantic_schemas import TTSRequest
from app.services.sarvam_voice_service import speech_to_text, text_to_speech

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])

@router.post("/stt")
async def stt(file: UploadFile = File(...), language: str = Form("auto")):
    audio = await file.read()
    if len(audio) > 12 * 1024 * 1024:
        from fastapi import HTTPException
        raise HTTPException(413, "Audio too large (max ~12MB / 30s for live STT)")
    transcript, lang = await speech_to_text(audio, file.filename or "audio.webm", language)
    return {"transcript": transcript, "language_code": lang, "mock": use_mock()}

@router.post("/tts")
async def tts(body: TTSRequest):
    wav, mime = await text_to_speech(body.text, body.language_code, body.speaker, body.pace)
    return Response(content=wav, media_type=mime,
                    headers={"Content-Disposition": 'inline; filename="speech.wav"'})

@router.get("/languages")
async def languages():
    return {"stt": ["auto", "hi-IN", "mr-IN", "ta-IN", "te-IN", "bn-IN", "en-IN"],
            "tts": ["hi-IN", "mr-IN", "ta-IN", "te-IN", "bn-IN", "kn-IN", "ml-IN",
                    "gu-IN", "pa-IN", "od-IN", "en-IN"]}
