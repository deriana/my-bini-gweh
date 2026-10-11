import os
import shutil
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.core import load_config, save_config, get_mcp_config_path, db, app_logger, persona_engine
from src.tts import TTSManager, TTSEngine
from src.mcp import MCPManager
from src.llm import LLMService

# Paths setup
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BG_DIR = DATA_DIR / "backgrounds"
CACHE_DIR = BASE_DIR / "cache"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Load Central Configuration
config = load_config()

# Initialize Domain Services
tts_engine = TTSManager(
    config=config.get("tts", {}),
    cache_dir=str(CACHE_DIR)
)
mcp_manager = MCPManager(get_mcp_config_path())
llm_service = LLMService(config, tts_engine, mcp_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Server", "Starting Personal AI VTuber server...")
    try:
        await mcp_manager.initialize()
    except Exception as e:
        app_logger.error("Server", f"Failed to initialize MCP Manager: {e}")
    yield
    app_logger.info("Server", "Shutting down server...")
    await mcp_manager.close()


app = FastAPI(title="Personal AI VTuber", lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets & Directories
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/live2d-models", StaticFiles(directory="live2d-models"), name="live2d-models")
app.mount("/cache", StaticFiles(directory="cache"), name="cache")
app.mount("/backgrounds", StaticFiles(directory=str(BG_DIR)), name="backgrounds")


# ==========================================
# Routes & Page Endpoints
# ==========================================
@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/settings")
async def settings_page():
    return FileResponse("static/settings.html")


# ==========================================
# Configuration & Management APIs
# ==========================================
@app.get("/api/config")
async def get_config():
    """Returns runtime info for the client stage."""
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


@app.get("/api/persona")
async def get_persona_api():
    """Returns persona archetypes, sliders, and mood."""
    return persona_engine.get_persona_data()


@app.post("/api/persona")
async def update_persona_api(payload: Dict[str, Any]):
    """Updates persona archetypes, sliders, and custom presets."""
    persona_engine.update_persona(payload)
    return {"status": "success", "message": "Sifat dan persona berhasil diperbarui!"}


@app.get("/api/mood")
async def get_mood_api():
    """Returns current emotional mood state."""
    data = persona_engine.get_persona_data()
    return {"mood": data.get("current_mood", "Ceria")}


@app.post("/api/mood/reset")
async def reset_mood_api():
    """Resets emotional mood state to Ceria."""
    persona_engine.update_mood("Ceria")
    return {"status": "success", "mood": "Ceria"}


@app.get("/api/settings")
async def get_all_settings():
    """Returns complete settings for the dedicated Settings page."""
    uploaded_bgs = [f"/backgrounds/{f.name}" for f in BG_DIR.glob("*") if f.is_file()]
    tts_status = await tts_engine.list_providers_status()
    return {
        "config": config,
        "uploaded_backgrounds": uploaded_bgs,
        "tts_providers": tts_status,
        "mcp_tools": [t["function"]["name"] for t in mcp_manager.get_openai_tools()]
    }


@app.post("/api/settings")
async def update_settings(new_settings: Dict[str, Any]):
    """Saves updated settings to config/config.json and live reloads services."""
    global config
    try:
        config = new_settings
        save_config(config)

        # Live reload services without restart
        tts_engine.update_config(config.get("tts", {}))
        llm_service.update_config(config)

        app_logger.info("Settings", "Configuration updated and reloaded dynamically.")
        return {"status": "success", "message": "Pengaturan berhasil disimpan dan dimuat ulang!"}
    except Exception as e:
        app_logger.error("Settings", f"Failed to save settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tts/providers")
async def get_tts_providers():
    """Returns status and voices of all registered TTS engines."""
    return {"providers": await tts_engine.list_providers_status()}


@app.get("/api/tts/voicevox/speakers")
async def get_voicevox_speakers():
    """Fetches real-time speakers from VOICEVOX server if running."""
    voicevox_provider = tts_engine.providers.get("voicevox")
    if voicevox_provider and hasattr(voicevox_provider, "fetch_engine_speakers"):
        speakers = await voicevox_provider.fetch_engine_speakers()
        return {"speakers": speakers}
    return {"speakers": []}


@app.post("/api/tts/test")
async def test_voice(payload: Dict[str, Any]):
    """Generates preview speech for a chosen voice/provider in Settings page."""
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


@app.post("/api/upload-bg")
async def upload_background(file: UploadFile = File(...)):
    """Handles custom wallpaper background upload."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="File tidak valid")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        raise HTTPException(status_code=400, detail="Hanya format gambar yang didukung (JPG, PNG, WebP)")

    save_path = BG_DIR / file.filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    bg_url = f"/backgrounds/{file.filename}"
    app_logger.info("Background", f"Uploaded new wallpaper: {bg_url}")
    return {"status": "success", "url": bg_url}


# ==========================================
# History & Memory Management APIs (SQLite)
# ==========================================
@app.get("/api/history")
async def get_history(session_id: str = "default"):
    """Returns conversation history for a given session."""
    sessions = db.get_sessions()
    messages = db.get_messages(session_id=session_id)
    return {"sessions": sessions, "messages": messages}


@app.post("/api/history/reset")
async def reset_memory(payload: Dict[str, str]):
    """Clears messages for the active session (AI forgets current conversation)."""
    session_id = payload.get("session_id", "default")
    db.clear_session_messages(session_id)
    app_logger.info("Memory", f"Reset conversation memory for session: {session_id}")
    return {"status": "success", "message": f"Memori sesi '{session_id}' telah dibersihkan."}


@app.delete("/api/history")
async def delete_all_history():
    """Clears all conversation sessions and messages from SQLite."""
    db.delete_all()
    app_logger.info("Memory", "All conversation history deleted.")
    return {"status": "success", "message": "Seluruh riwayat chat telah dihapus."}


# ==========================================
# System & Model Logs API
# ==========================================
@app.get("/api/logs")
async def get_logs():
    """Returns recent model and system logs."""
    return {"logs": app_logger.get_logs(limit=200)}


@app.post("/api/logs/clear")
async def clear_logs():
    """Clears log buffer."""
    app_logger.clear()
    return {"status": "success", "message": "Log telah dibersihkan."}


# ==========================================
# WebSocket Endpoint (Live Duplex)
# ==========================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app_logger.info("WS", "Client connected to interactive WebSocket.")

    chat_history: List[Dict[str, Any]] = llm_service.create_initial_history()

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "chat")

            if msg_type == "chat":
                user_text = data.get("text", "").strip()
                image_base64 = data.get("image")
                active_model = data.get("model", config["live2d"]["default_model"])
                active_voice = data.get("voice", config["tts"]["default_voice"])
                session_id = data.get("session_id", "default")

                if not user_text and not image_base64:
                    continue

                # Save user message to SQLite database
                db.add_message(
                    session_id=session_id,
                    role="user",
                    content=user_text or "[Kirim Gambar Kamera]"
                )

                await websocket.send_json({"type": "status", "status": "Berpikir..."})

                # Format user message (supports text and camera vision)
                user_content = llm_service.format_user_content(user_text, image_base64)
                chat_history.append({"role": "user", "content": user_content})

                # Stream response sentence-by-sentence with lip-sync and tool execution
                full_reply = await llm_service.stream_conversation(
                    messages=chat_history,
                    websocket=websocket,
                    active_model_key=active_model,
                    active_voice=active_voice
                )

                # Save AI response to SQLite database
                if full_reply:
                    db.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=full_reply
                    )

                # Keep sliding memory window (system prompt + last 20 messages)
                if len(chat_history) > 22:
                    chat_history = [chat_history[0]] + chat_history[-20:]

                await websocket.send_json({
                    "type": "done",
                    "full_text": full_reply
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        app_logger.info("WS", "Client disconnected from WebSocket.")
    except Exception as e:
        app_logger.error("WS", f"WebSocket exception: {e}")


if __name__ == "__main__":
    host = os.getenv("HOST", config["server"].get("host", "127.0.0.1"))
    port = int(os.getenv("PORT", config["server"].get("port", 8080)))
    print(f"[Server] Running on http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True)
