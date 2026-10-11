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

    # Get reaction text & emotion
    raw_text, emotion = interact_engine.get_touch_reaction(touch_type, archetype)

    # Resolve expression index for active model
    model_info = config["live2d"]["models"].get(model_key, {})
    emotion_map = model_info.get("emotions", {})
    clean_text, detected_emotion, expression_idx = parse_emotion_and_clean(raw_text, emotion_map)

    app_logger.info("Interact", f"Touch '{touch_type}' triggered on {model_key} ({archetype}): [{emotion}] {clean_text}")

    # Generate reactive voice audio
    audio_res = await tts_engine.generate_audio(clean_text, voice=voice, emotion=emotion)
    audio_b64 = None
    volumes = []
    if audio_res:
        _, audio_b64, volumes = audio_res

    # Record event in conversation history
    action_label = "elus kepala (headpat)" if touch_type == "headpat" else ("cubit pipi" if touch_type == "poke" else "sentuh badan")
    db.add_message(session_id=session_id, role="user", content=f"*[Menyentuh avatar: {action_label}]*")
    db.add_message(session_id=session_id, role="assistant", content=raw_text)

    return {
        "status": "success",
        "touch_type": touch_type,
        "text": raw_text,
        "clean_text": clean_text,
        "emotion": emotion,
        "expression_index": expression_idx,
        "audio": audio_b64,
        "volumes": volumes
    }
