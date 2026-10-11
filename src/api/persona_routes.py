from typing import Dict, Any
from fastapi import APIRouter

from src.core import persona_engine

router = APIRouter(prefix="/api", tags=["Persona & Mood"])


@router.get("/persona")
async def get_persona():
    """Returns character archetypes, fine-tuning sliders, and current emotional mood."""
    return persona_engine.get_persona_data()


@router.post("/persona")
async def update_persona(payload: Dict[str, Any]):
    """Updates archetype templates, custom presets, and personality sliders."""
    persona_engine.update_persona(payload)
    return {"status": "success", "message": "Sifat dan persona berhasil diperbarui!"}


@router.get("/mood")
async def get_current_mood():
    """Returns the current real-time emotional mood state."""
    data = persona_engine.get_persona_data()
    return {"mood": data.get("current_mood", "Ceria")}


@router.post("/mood/reset")
async def reset_mood():
    """Resets the emotional mood state to Ceria."""
    persona_engine.update_mood("Ceria")
    return {"status": "success", "mood": "Ceria"}
