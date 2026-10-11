import os
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
import uvicorn

from live2d_helper import parse_emotion_and_clean
from tts_engine import TTSEngine
from mcp_manager import MCPManager

# Load Configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

tts_engine = TTSEngine(
    cache_dir="cache",
    default_voice=config["tts"]["default_voice"]
)
mcp_manager = MCPManager("mcp_servers.json")

# LLM Client setup (OpenAI compatible)
llm_cfg = config.get("llm", {})
base_url = os.getenv("OPENAI_BASE_URL", llm_cfg.get("base_url", "http://127.0.0.1:11434/v1"))
api_key = os.getenv("OPENAI_API_KEY", llm_cfg.get("api_key", "ollama"))
llm_model = os.getenv("LLM_MODEL", llm_cfg.get("model", "qwen2.5:3b"))
system_prompt = llm_cfg.get("system_prompt", "Kamu adalah asisten AI pribadi yang ramah.")

openai_client = AsyncOpenAI(
    base_url=base_url,
    api_key=api_key
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MCP tools
    print("[Server] Starting Personal AI VTuber server...")
    try:
        await mcp_manager.initialize()
    except Exception as e:
        print(f"[Server] Failed to initialize MCP Manager: {e}")
    yield
    # Shutdown
    print("[Server] Shutting down...")
    await mcp_manager.close()


app = FastAPI(title="Personal AI VTuber", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mounts
os.makedirs("cache", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("live2d-models", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/live2d-models", StaticFiles(directory="live2d-models"), name="live2d-models")
app.mount("/cache", StaticFiles(directory="cache"), name="cache")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/api/config")
async def get_config():
    """Returns available models, voices, and active settings."""
    return {
        "models": config["live2d"]["models"],
        "default_model": config["live2d"]["default_model"],
        "voices": config["tts"]["available_voices"],
        "default_voice": config["tts"]["default_voice"],
        "llm_model": llm_model,
        "mcp_tools": [t["function"]["name"] for t in mcp_manager.get_openai_tools()]
    }


def split_into_sentences(text: str) -> List[str]:
    """Splits text into speakable sentence chunks by punctuation."""
    parts = re.split(r'([.!?;:\n]+)', text)
    sentences = []
    current = ""
    for i in range(0, len(parts) - 1, 2):
        sentence = parts[i] + parts[i + 1]
        if sentence.strip():
            sentences.append(sentence.strip())
    if len(parts) % 2 != 0 and parts[-1].strip():
        sentences.append(parts[-1].strip())
    return sentences


async def process_llm_stream(
    messages: List[Dict[str, Any]],
    websocket: WebSocket,
    active_model_key: str,
    active_voice: str
) -> str:
    """Streams LLM tokens, detects sentences, processes TTS, and sends to client."""
    model_info = config["live2d"]["models"].get(active_model_key, {})
    emotion_map = model_info.get("emotions", {})
    tools = mcp_manager.get_openai_tools()

    # Step 1: Query LLM (with function calling if tools exist)
    call_kwargs = {
        "model": llm_model,
        "messages": messages,
        "temperature": llm_cfg.get("temperature", 0.7),
        "stream": True
    }
    if tools:
        call_kwargs["tools"] = tools

    full_response_text = ""
    buffer = ""
    tool_calls_accumulator = {}

    try:
        response_stream = await openai_client.chat.completions.create(**call_kwargs)

        async for chunk in response_stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            # Check for tool call chunks
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_accumulator:
                        tool_calls_accumulator[idx] = {
                            "id": tc.id or "",
                            "name": tc.function.name if tc.function and tc.function.name else "",
                            "arguments": ""
                        }
                    if tc.id:
                        tool_calls_accumulator[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_accumulator[idx]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_accumulator[idx]["arguments"] += tc.function.arguments

            # Check for content text chunks
            if delta.content:
                text_piece = delta.content
                full_response_text += text_piece
                buffer += text_piece

                # Check if buffer contains sentence delimiters
                delimiter_match = re.search(r'[.!?;:\n]', buffer)
                if delimiter_match:
                    split_idx = delimiter_match.end()
                    sentence_to_process = buffer[:split_idx].strip()
                    buffer = buffer[split_idx:]

                    if sentence_to_process:
                        clean_text, emotion, expression_idx = parse_emotion_and_clean(sentence_to_process, emotion_map)
                        if clean_text:
                            # Generate audio in background
                            audio_result = await tts_engine.generate_audio(clean_text, active_voice, emotion)
                            if audio_result:
                                _, audio_b64, volumes = audio_result
                                await websocket.send_json({
                                    "type": "audio",
                                    "text": sentence_to_process,
                                    "clean_text": clean_text,
                                    "emotion": emotion,
                                    "expression_index": expression_idx,
                                    "audio": audio_b64,
                                    "volumes": volumes
                                })
                            else:
                                await websocket.send_json({
                                    "type": "text",
                                    "text": sentence_to_process,
                                    "clean_text": clean_text,
                                    "emotion": emotion,
                                    "expression_index": expression_idx
                                })

        # Process any remaining text in buffer
        if buffer.strip():
            sentence_to_process = buffer.strip()
            clean_text, emotion, expression_idx = parse_emotion_and_clean(sentence_to_process, emotion_map)
            if clean_text:
                audio_result = await tts_engine.generate_audio(clean_text, active_voice, emotion)
                if audio_result:
                    _, audio_b64, volumes = audio_result
                    await websocket.send_json({
                        "type": "audio",
                        "text": sentence_to_process,
                        "clean_text": clean_text,
                        "emotion": emotion,
                        "expression_index": expression_idx,
                        "audio": audio_b64,
                        "volumes": volumes
                    })
                else:
                    await websocket.send_json({
                        "type": "text",
                        "text": sentence_to_process,
                        "clean_text": clean_text,
                        "emotion": emotion,
                        "expression_index": expression_idx
                    })

        # Handle tool execution if tools were invoked
        if tool_calls_accumulator:
            tool_calls_list = [v for k, v in sorted(tool_calls_accumulator.items())]
            assistant_msg = {
                "role": "assistant",
                "content": full_response_text or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"]
                        }
                    }
                    for tc in tool_calls_list
                ]
            }
            messages.append(assistant_msg)

            for tc in tool_calls_list:
                tool_name = tc["name"]
                try:
                    tool_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except Exception:
                    tool_args = {}

                await websocket.send_json({
                    "type": "status",
                    "status": f"Menjalankan alat: {tool_name}..."
                })

                tool_result = await mcp_manager.execute_tool(tool_name, tool_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": tool_result
                })

            # Re-call LLM to provide final natural answer with tool results
            return await process_llm_stream(messages, websocket, active_model_key, active_voice)

        return full_response_text

    except Exception as e:
        print(f"[LLM] Error during completion: {e}")
        err_msg = f"[sad] Maaf, ada kendala saat menghubungi model AI: {str(e)}"
        clean_err, emotion, expression_idx = parse_emotion_and_clean(err_msg, emotion_map)
        audio_result = await tts_engine.generate_audio(clean_err, active_voice, emotion)
        if audio_result:
            _, audio_b64, volumes = audio_result
            await websocket.send_json({
                "type": "audio",
                "text": err_msg,
                "clean_text": clean_err,
                "emotion": emotion,
                "expression_index": expression_idx,
                "audio": audio_b64,
                "volumes": volumes
            })
        else:
            await websocket.send_json({"type": "text", "text": err_msg})
        return err_msg


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Client connected.")

    chat_history: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt}
    ]

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "chat")

            if msg_type == "chat":
                user_text = data.get("text", "").strip()
                image_base64 = data.get("image")  # Camera snapshot
                active_model = data.get("model", config["live2d"]["default_model"])
                active_voice = data.get("voice", config["tts"]["default_voice"])

                if not user_text and not image_base64:
                    continue

                await websocket.send_json({"type": "status", "status": "Berpikir..."})

                # Prepare user content (supports multimodal vision)
                if image_base64:
                    user_content = []
                    if user_text:
                        user_content.append({"type": "text", "text": user_text})
                    else:
                        user_content.append({"type": "text", "text": "Apa yang kamu lihat di gambar/kamera ini?"})

                    # Handle data url format
                    img_url = image_base64 if image_base64.startswith("data:") else f"data:image/jpeg;base64,{image_base64}"
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": img_url}
                    })
                    chat_history.append({"role": "user", "content": user_content})
                else:
                    chat_history.append({"role": "user", "content": user_text})

                # Stream response
                full_reply = await process_llm_stream(
                    messages=chat_history,
                    websocket=websocket,
                    active_model_key=active_model,
                    active_voice=active_voice
                )

                # Keep history within reasonable window (last 20 messages)
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
        print(f"[WS] Exception: {e}")


if __name__ == "__main__":
    host = config["server"].get("host", "127.0.0.1")
    port = config["server"].get("port", 8000)
    print(f"[Server] Running on http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True)
