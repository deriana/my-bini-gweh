from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from src.core import tts_engine

router = APIRouter(prefix="/api/tts", tags=["Text-to-Speech"])


@router.get("/providers")
async def get_tts_providers():
    """Returns discovery status, health, and voices for all registered TTS engines."""
    return {"providers": await tts_engine.list_providers_status()}


@router.get("/voicevox/speakers")
async def get_voicevox_speakers():
    """Fetches real-time speakers from local or remote VOICEVOX engine if online."""
    voicevox_provider = tts_engine.providers.get("voicevox")
    if voicevox_provider and hasattr(voicevox_provider, "fetch_engine_speakers"):
        speakers = await voicevox_provider.fetch_engine_speakers()
        return {"speakers": speakers}
    return {"speakers": []}


@router.post("/test")
async def test_voice(payload: Dict[str, Any]):
    """Generates preview speech for a chosen voice and engine in the Settings page."""
    provider_id = payload.get("provider", tts_engine.active_provider_key)
    voice = payload.get("voice")
    text = payload.get("text", "Halo! Ini adalah contoh tes suara untuk Ryza.")

    try:
        res = await tts_engine.generate_audio(text, voice=voice, provider_id=provider_id)
        if res:
            _, audio_b64, _ = res
            return {"status": "success", "audio": audio_b64}
        raise HTTPException(status_code=500, detail=f"Gagal membuat audio menggunakan engine '{provider_id}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
