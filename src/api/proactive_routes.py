from typing import Optional
from fastapi import APIRouter

from src.core.proactive import proactive_engine
from src.core import (
    config,
    persona_engine,
    tts_engine,
    app_logger
)
from src.live2d import parse_emotion_and_clean

router = APIRouter(prefix="/api/proactive", tags=["Proactive Companion"])


@router.get("/greeting")
async def get_proactive_greeting(model: Optional[str] = None):
    """
    Returns an autonomous greeting based on current time of day
    and active character persona with TTS audio and Live2D volumes.
    """
    active_model = model or config["live2d"]["default_model"]
    persona_data = persona_engine.get_persona_data()
    archetype = persona_data.get("active_archetype", "tsundere")

    raw_text, emotion = proactive_engine.get_greeting(archetype)
    model_info = config["live2d"]["models"].get(active_model, {})
    emotion_map = model_info.get("emotions", {})
    clean_text, detected_emotion, expression_idx = parse_emotion_and_clean(raw_text, emotion_map)

    app_logger.info("Proactive", f"Time greeting: [{emotion}] {clean_text}")

    audio_res = await tts_engine.generate_audio(clean_text, voice=tts_engine.default_voice, emotion=emotion)
    audio_b64 = None
    volumes = []
    if audio_res:
        _, audio_b64, volumes = audio_res

    return {
        "status": "success",
        "period": proactive_engine.get_time_period(),
        "text": raw_text,
        "clean_text": clean_text,
        "emotion": emotion,
        "expression_index": expression_idx,
        "audio": audio_b64,
        "volumes": volumes
    }


@router.get("/reminder")
async def get_break_reminder(model: Optional[str] = None):
    """
    Returns an autonomous wellness / hydration reminder
    with TTS audio and Live2D volumes.
    """
    active_model = model or config["live2d"]["default_model"]
    persona_data = persona_engine.get_persona_data()
    archetype = persona_data.get("active_archetype", "tsundere")

    raw_text, emotion = proactive_engine.get_break_reminder(archetype)
    model_info = config["live2d"]["models"].get(active_model, {})
    emotion_map = model_info.get("emotions", {})
    clean_text, detected_emotion, expression_idx = parse_emotion_and_clean(raw_text, emotion_map)

    app_logger.info("Proactive", f"Break reminder: [{emotion}] {clean_text}")

    audio_res = await tts_engine.generate_audio(clean_text, voice=tts_engine.default_voice, emotion=emotion)
    audio_b64 = None
    volumes = []
    if audio_res:
        _, audio_b64, volumes = audio_res

    return {
        "status": "success",
        "text": raw_text,
        "clean_text": clean_text,
        "emotion": emotion,
        "expression_index": expression_idx,
        "audio": audio_b64,
        "volumes": volumes
    }
