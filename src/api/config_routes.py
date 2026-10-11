from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from src.core import (
    config,
    BG_DIR,
    tts_engine,
    llm_service,
    mcp_manager,
    persona_engine,
    app_logger,
    reload_services_config
)

router = APIRouter(prefix="/api", tags=["Configuration"])


@router.get("/config")
async def get_client_config():
    """Returns runtime bootstrap information for the main stage."""
    persona_data = persona_engine.get_persona_data()
    return {
        "models": config["live2d"]["models"],
        "default_model": config["live2d"]["default_model"],
        "active_tts_provider": tts_engine.active_provider_key,
        "voices": tts_engine.get_available_voices(),
        "default_voice": tts_engine.default_voice,
        "llm_model": llm_service.model,
        "mcp_tools": [t["function"]["name"] for t in mcp_manager.get_openai_tools()],
        "persona": persona_data
    }


@router.get("/settings")
async def get_all_settings():
    """Returns comprehensive settings for the dedicated Settings page."""
    uploaded_bgs = [f"/backgrounds/{f.name}" for f in BG_DIR.glob("*") if f.is_file()]
    tts_status = await tts_engine.list_providers_status()
    return {
        "config": config,
        "uploaded_backgrounds": uploaded_bgs,
        "tts_providers": tts_status,
        "mcp_tools": [t["function"]["name"] for t in mcp_manager.get_openai_tools()]
    }


@router.post("/settings")
async def update_settings(new_settings: Dict[str, Any]):
    """Saves updated settings to disk and live reloads all dependent services."""
    try:
        reload_services_config(new_settings)
        app_logger.info("Settings", "System configuration updated and reloaded dynamically.")
        return {"status": "success", "message": "Pengaturan berhasil disimpan dan dimuat ulang!"}
    except Exception as e:
        app_logger.error("Settings", f"Failed to save settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
