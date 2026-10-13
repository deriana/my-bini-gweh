from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from src.core.interact import interact_engine
from src.core import (
    config,
    persona_engine,
    tts_engine,
    db,
    app_logger
)
from src.live2d import parse_emotion_and_clean

router = APIRouter(prefix="/api/interact", tags=["Interactions"])


@router.post("/touch")
async def handle_touch_interaction(payload: Dict[str, Any]):
    """
    Handles physical touch events (Headpat, Cheek Poke, Body Tap) on Live2D avatar.
    Produces reactive voice response with emotions and lip-sync chunks.
    """
    touch_type = payload.get("touch_type", "headpat").lower()
    model_key = payload.get("model", config["live2d"]["default_model"])
    voice = payload.get("voice", tts_engine.default_voice)
    session_id = payload.get("session_id", "default")

    persona_data = persona_engine.get_persona_data()
    archetype = persona_data.get("active_archetype", "tsundere")
    dominant_lang = persona_data.get("dominant_language", "ja")
    active_tts = config.get("tts", {}).get("active_provider", "voicevox")

    if dominant_lang == "auto":
        target_lang = "ja" if active_tts in ["voicevox", "kokoro"] else "id"
    else:
        target_lang = dominant_lang if dominant_lang in ["ja", "id", "en"] else "ja"

    # Get reaction text & emotion
    raw_text, emotion = interact_engine.get_touch_reaction(touch_type, archetype=archetype, lang=target_lang)

    # Resolve expression index for active model
    model_info = config["live2d"]["models"].get(model_key, {})
    emotion_map = model_info.get("emotions", {})
    clean_text, detected_emotion, expression_idx = parse_emotion_and_clean(raw_text, emotion_map)

    app_logger.info("Interact", f"Touch '{touch_type}' triggered on {model_key} ({archetype}/{target_lang}): [{emotion}] {clean_text}")

    # Generate reactive voice audio
    audio_res = await tts_engine.generate_audio(clean_text, voice=voice, emotion=emotion)
    audio_b64 = None
    volumes = []
    if audio_res:
        _, audio_b64, volumes = audio_res

    # Localized action label for conversation context
    action_label = {
        "ja": {
            "headpat": "頭を撫でる (headpat)",
            "poke": "ほっぺをつつく (poke)",
            "body": "体に触れる (touch body)"
        },
        "en": {
            "headpat": "headpat",
            "poke": "cheek poke",
            "body": "body touch"
        },
        "id": {
            "headpat": "elus kepala (headpat)",
            "poke": "cubit pipi (poke)",
            "body": "sentuh badan (touch body)"
        }
    }.get(target_lang, {}).get(touch_type, touch_type)

    user_note = {
        "ja": f"*[アバターに触れる: {action_label}]*",
        "en": f"*[Touches avatar: {action_label}]*",
        "id": f"*[Menyentuh avatar: {action_label}]*"
    }.get(target_lang, f"*[Touch: {action_label}]*")

    db.add_message(session_id=session_id, role="user", content=user_note)
    db.add_message(session_id=session_id, role="assistant", content=raw_text)

    from src.core.romanize import to_romaji, format_display_text, contains_japanese
    subtitle_fmt = persona_data.get("subtitle_format", "both")
    romaji = to_romaji(clean_text) if contains_japanese(clean_text) else None
    display_text = format_display_text(clean_text, subtitle_format=subtitle_fmt)

    return {
        "status": "success",
        "touch_type": touch_type,
        "text": raw_text,
        "clean_text": clean_text,
        "romaji": romaji,
        "display_text": display_text,
        "emotion": emotion,
        "expression_index": expression_idx,
        "audio": audio_b64,
        "volumes": volumes
    }
