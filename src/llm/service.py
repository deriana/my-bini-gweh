import os
import re
import json
import time
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from fastapi import WebSocket

from src.live2d import parse_emotion_and_clean
from src.tts import TTSEngine
from src.mcp import MCPManager
from src.core import app_logger, db


class LLMService:
    """
    Handles interactions with OpenAI-compatible LLMs (Ollama, Groq, OpenAI, Gemini).
    Streams responses sentence-by-sentence, coordinates Edge-TTS speech generation,
    records activity to AppLogger, and executes MCP tools when requested.
    """

    def __init__(self, config: Dict[str, Any], tts_engine: TTSEngine, mcp_manager: MCPManager):
        self.config = config
        self.tts_engine = tts_engine
        self.mcp_manager = mcp_manager
        self._init_client()

    def _init_client(self):
        llm_cfg = self.config.get("llm", {})
        self.provider = llm_cfg.get("provider", "ollama")
        self.base_url = os.getenv("OPENAI_BASE_URL", llm_cfg.get("base_url", "http://127.0.0.1:11434/v1"))
        self.api_key = os.getenv("OPENAI_API_KEY", llm_cfg.get("api_key", "ollama"))
        self.model = os.getenv("LLM_MODEL", llm_cfg.get("model", "qwen2.5:3b"))
        self.temperature = float(llm_cfg.get("temperature", 0.7))
        self.system_prompt = llm_cfg.get("system_prompt", "Kamu adalah asisten AI pribadi yang ramah.")

        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        app_logger.info("LLM", f"Client initialized. Provider: {self.provider}, Model: {self.model}, Base URL: {self.base_url}")

    def update_config(self, new_config: Dict[str, Any]):
        """Dynamically reconfigures LLM client from Settings page."""
        self.config = new_config
        self._init_client()

    def create_initial_history(self) -> List[Dict[str, Any]]:
        return [{"role": "system", "content": self.system_prompt}]

    def format_user_content(self, text: str, image_base64: Optional[str] = None) -> Any:
        if not image_base64:
            return text

        content = []
        if text:
            content.append({"type": "text", "text": text})
        else:
            content.append({"type": "text", "text": "Apa yang kamu lihat di gambar/kamera ini?"})

        img_url = image_base64 if image_base64.startswith("data:") else f"data:image/jpeg;base64,{image_base64}"
        content.append({
            "type": "image_url",
            "image_url": {"url": img_url}
        })
        return content

    async def stream_conversation(
        self,
        messages: List[Dict[str, Any]],
        websocket: WebSocket,
        active_model_key: str,
        active_voice: str
    ) -> str:
        model_info = self.config["live2d"]["models"].get(active_model_key, {})
        emotion_map = model_info.get("emotions", {})
        tools = self.mcp_manager.get_openai_tools()

        last_user_msg = messages[-1]["content"] if messages else ""
        app_logger.info("Chat", f"Received message for {active_model_key}: {str(last_user_msg)[:80]}...")

        call_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": True
        }
        if tools:
            call_kwargs["tools"] = tools

        full_response_text = ""
        buffer = ""
        tool_calls_accumulator = {}
        start_time = time.time()

        try:
            app_logger.info("LLM", f"Calling {self.model} (tools count: {len(tools)})...")
            response_stream = await self.client.chat.completions.create(**call_kwargs)

            async for chunk in response_stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                # Accumulate tool call fragments
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

                # Process streamed content text
                if delta.content:
                    piece = delta.content
                    full_response_text += piece
                    buffer += piece

                    delimiter_match = re.search(r'[.!?;:\n]', buffer)
                    if delimiter_match:
                        split_idx = delimiter_match.end()
                        sentence = buffer[:split_idx].strip()
                        buffer = buffer[split_idx:]

                        if sentence:
                            clean_text, emotion, expression_idx = parse_emotion_and_clean(sentence, emotion_map)
                            if emotion:
                                app_logger.info("Emotion", f"Detected emotion: [{emotion}] -> Expr index {expression_idx}")

                            if clean_text:
                                audio_result = await self.tts_engine.generate_audio(clean_text, active_voice, emotion)
                                if audio_result:
                                    _, audio_b64, volumes = audio_result
                                    await websocket.send_json({
                                        "type": "audio",
                                        "text": sentence,
                                        "clean_text": clean_text,
                                        "emotion": emotion,
                                        "expression_index": expression_idx,
                                        "audio": audio_b64,
                                        "volumes": volumes
                                    })
                                else:
                                    await websocket.send_json({
                                        "type": "text",
                                        "text": sentence,
                                        "clean_text": clean_text,
                                        "emotion": emotion,
                                        "expression_index": expression_idx
                                    })

            # Process leftover text in buffer
            if buffer.strip():
                sentence = buffer.strip()
                clean_text, emotion, expression_idx = parse_emotion_and_clean(sentence, emotion_map)
                if clean_text:
                    audio_result = await self.tts_engine.generate_audio(clean_text, active_voice, emotion)
                    if audio_result:
                        _, audio_b64, volumes = audio_result
                        await websocket.send_json({
                            "type": "audio",
                            "text": sentence,
                            "clean_text": clean_text,
                            "emotion": emotion,
                            "expression_index": expression_idx,
                            "audio": audio_b64,
                            "volumes": volumes
                        })
                    else:
                        await websocket.send_json({
                            "type": "text",
                            "text": sentence,
                            "clean_text": clean_text,
                            "emotion": emotion,
                            "expression_index": expression_idx
                        })

            elapsed = round(time.time() - start_time, 2)
            app_logger.info("LLM", f"Completed generation in {elapsed}s: {len(full_response_text)} chars")

            # Handle tool execution
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

                    app_logger.info("MCP", f"Executing tool: {tool_name} with args: {tool_args}")
                    await websocket.send_json({
                        "type": "status",
                        "status": f"Menjalankan alat: {tool_name}..."
                    })

                    tool_result = await self.mcp_manager.execute_tool(tool_name, tool_args)
                    app_logger.info("MCP", f"Tool {tool_name} returned: {str(tool_result)[:100]}...")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_result
                    })

                # Recursively stream continuation after tool results
                return await self.stream_conversation(messages, websocket, active_model_key, active_voice)

            return full_response_text

        except Exception as e:
            app_logger.error("LLM", f"Error during streaming: {str(e)}")
            err_msg = f"[sad] Maaf, ada kendala saat menghubungi model AI: {str(e)}"
            clean_err, emotion, expression_idx = parse_emotion_and_clean(err_msg, emotion_map)
            audio_result = await self.tts_engine.generate_audio(clean_err, active_voice, emotion)
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
