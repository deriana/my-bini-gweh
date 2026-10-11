import os
import uvicorn
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from src.core import load_config, get_mcp_config_path
from src.tts import TTSEngine
from src.mcp import MCPManager
from src.llm import LLMService

# Load Central Configuration
config = load_config()

# Initialize Domain Services
tts_engine = TTSEngine(
    cache_dir="cache",
    default_voice=config["tts"]["default_voice"]
)
mcp_manager = MCPManager(get_mcp_config_path())
llm_service = LLMService(config, tts_engine, mcp_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Server] Starting Personal AI VTuber server...")
    try:
        await mcp_manager.initialize()
    except Exception as e:
        print(f"[Server] Failed to initialize MCP Manager: {e}")
    yield
    print("[Server] Shutting down...")
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

# Ensure essential runtime folders exist
os.makedirs("cache", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("live2d-models", exist_ok=True)

# Mount Static Assets
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/live2d-models", StaticFiles(directory="live2d-models"), name="live2d-models")
app.mount("/cache", StaticFiles(directory="cache"), name="cache")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/api/config")
async def get_config():
    """Returns available Live2D models, TTS voices, and server info."""
    return {
        "models": config["live2d"]["models"],
        "default_model": config["live2d"]["default_model"],
        "voices": config["tts"]["available_voices"],
        "default_voice": config["tts"]["default_voice"],
        "llm_model": llm_service.model,
        "mcp_tools": [t["function"]["name"] for t in mcp_manager.get_openai_tools()]
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Client connected.")

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

                if not user_text and not image_base64:
                    continue

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
        print("[WS] Client disconnected.")
    except Exception as e:
        print(f"[WS] Connection error: {e}")


if __name__ == "__main__":
    host = os.getenv("HOST", config["server"].get("host", "127.0.0.1"))
    port = int(os.getenv("PORT", config["server"].get("port", 8080)))
    print(f"[Server] Running on http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True)
