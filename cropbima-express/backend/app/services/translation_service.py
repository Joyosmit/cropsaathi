"""Lightweight language helpers (mock-friendly; Sarvam translate when key present)."""
from __future__ import annotations
import asyncio
from app.config import use_mock, settings

LANGS = ["hi-IN", "mr-IN", "ta-IN", "te-IN", "bn-IN", "kn-IN", "ml-IN", "gu-IN", "pa-IN", "en-IN"]

async def translate(text: str, target: str = "en-IN", source: str = "auto") -> str:
    if use_mock() or not text.strip():
        return text
    def _sync():
        from sarvamai import SarvamAI
        c = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
        r = c.text.translate(input=text, source_language_code=source, target_language_code=target)
        return getattr(r, "translated_text", str(r))
    return await asyncio.to_thread(_sync)

def guess_language(text: str) -> str:
    if any("\u0900" <= ch <= "\u097F" for ch in text):
        return "hi-IN"
    if any("\u0A80" <= ch <= "\u0AFF" for ch in text):
        return "gu-IN"
    if any("\u0C00" <= ch <= "\u0C7F" for ch in text):
        return "te-IN"
    if any("\u0B80" <= ch <= "\u0BFF" for ch in text):
        return "ta-IN"
    return "en-IN"
