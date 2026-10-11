from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core import config, db, app_logger, llm_service, tts_engine

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_duplex_endpoint(websocket: WebSocket):
    """
    Interactive Live Duplex WebSocket Endpoint.
    Streams AI responses sentence-by-sentence with Live2D lip-sync chunks,
    mood updates, and persists conversation context into SQLite database.
    """
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
                active_voice = data.get("voice", tts_engine.default_voice)
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

                # Format user message (supports text and vision camera)
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
