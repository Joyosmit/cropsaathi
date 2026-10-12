"""Saaras STT (saaras:v4) + Bulbul TTS (bulbul:v3) with mock fallback."""
from __future__ import annotations
import asyncio
import base64
import io
import wave
from typing import Tuple

from app.config import settings, use_mock

MOCK_STT = {
    "hi-IN": "मेरी फसल सोयाबीन है, बारिश 18 सितंबर को हुई थी, लगभग साठ प्रतिशत नुकसान हुआ है।",
    "mr-IN": "माझं नाव रमेश पाटील, गट नंबर 123/4, सोयाबीन पिकाचं साठ टक्के नुकसान झालं.",
    "en-IN": "My soybean crop was damaged by excess rainfall on 18th September, around sixty percent loss.",
}

async def speech_to_text(audio_bytes: bytes, filename: str = "audio.webm", language: str = "auto") -> Tuple[str, str]:
    if use_mock():
        await asyncio.sleep(0.4)
        lang = "mr-IN" if language in ("auto", "mr-IN") else language
        return MOCK_STT.get(lang, MOCK_STT["en-IN"]), lang
    return await asyncio.to_thread(_stt_sync, audio_bytes, filename)

def _stt_sync(audio_bytes: bytes, filename: str) -> Tuple[str, str]:
    from sarvamai import SarvamAI
    client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
    bio = io.BytesIO(audio_bytes)
    # SDK expects a file-like object; attach a name for multipart detection
    bio.name = filename  # type: ignore[attr-defined]
    resp = client.speech_to_text.transcribe(file=bio, model="saaras:v4", mode="transcribe")
    transcript = getattr(resp, "transcript", "") or (resp.get("transcript") if isinstance(resp, dict) else "")
    lang = getattr(resp, "language_code", None) or (resp.get("language_code") if isinstance(resp, dict) else None) or "auto"
    return transcript, lang

async def text_to_speech(text: str, language_code: str = "hi-IN", speaker: str = "simran", pace: float = 1.0) -> Tuple[bytes, str]:
    """Returns (wav_bytes, mime). Mock returns a 1s silent WAV."""
    if use_mock():
        await asyncio.sleep(0.4)
        return _silent_wav(), "audio/wav"
    return await asyncio.to_thread(_tts_sync, text, language_code, speaker, pace)

def _tts_sync(text: str, language_code: str, speaker: str, pace: float) -> Tuple[bytes, str]:
    from sarvamai import SarvamAI
    client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
    model = "bulbul:v3"
    try:
        resp = client.text_to_speech.convert(
            text=text[:2000], language_code=language_code,
            model=model, speaker=speaker, pace=pace,
        )
    except TypeError:
        resp = client.text_to_speech.convert(text=text[:2000], language_code=language_code, model=model, speaker=speaker)
    audios = getattr(resp, "audios", None) or (resp.get("audios") if isinstance(resp, dict) else [])
    combined = "".join(audios or [])
    return base64.b64decode(combined), "audio/wav"

def _silent_wav(seconds: int = 1, sr: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"\x00\x00" * sr * seconds)
    return buf.getvalue()
