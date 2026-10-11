import os
import uuid
import httpx
from typing import Optional, List, Dict, Any
from src.tts.base import BaseTTSProvider


class CustomHTTPTTSProvider(BaseTTSProvider):
    """
    Custom HTTP / OpenAI-compatible TTS Provider.
    Enables plug-and-play integration with OpenAI TTS (/v1/audio/speech),
    ElevenLabs, CosyVoice, Fish Audio, or any custom microservice.
    """

    DEFAULT_VOICES = [
        {"id": "alloy", "name": "Alloy (Neutral)", "lang": "en-US"},
        {"id": "echo", "name": "Echo (Warm)", "lang": "en-US"},
        {"id": "fable", "name": "Fable (Expressive)", "lang": "en-US"},
        {"id": "onyx", "name": "Onyx (Deep)", "lang": "en-US"},
        {"id": "nova", "name": "Nova (Energetic)", "lang": "en-US"},
        {"id": "shimmer", "name": "Shimmer (Clear)", "lang": "en-US"}
    ]

    def __init__(self, config: Dict[str, Any], cache_dir: str):
        super().__init__("custom_http", "Custom HTTP / OpenAI TTS", config, cache_dir)

    def _get_endpoint(self) -> str:
        return self.config.get("endpoint_url", "http://127.0.0.1:8000/v1/audio/speech").strip()

    async def is_available(self) -> bool:
        endpoint = self._get_endpoint()
        if not endpoint:
            return False
        # If endpoint starts with http, consider configured
        return True

    def get_available_voices(self) -> List[Dict[str, str]]:
        configured_voices = self.config.get("available_voices")
        if configured_voices and isinstance(configured_voices, list):
            return configured_voices
        return self.DEFAULT_VOICES

    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        emotion: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        if not text or not text.strip():
            return None

        endpoint = self._get_endpoint()
        api_key = self.config.get("api_key", "").strip()
        model_name = self.config.get("model", "tts-1")
        chosen_voice = voice or self.config.get("default_voice", "alloy")
        speed = float(self.config.get("speed", 1.0))
        response_format = self.config.get("response_format", "mp3")

        ext = "wav" if "wav" in response_format.lower() else "mp3"
        file_id = f"custom_{uuid.uuid4().hex[:12]}.{ext}"
        file_path = os.path.join(self.cache_dir, file_id)

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model_name,
            "input": text.strip(),
            "voice": chosen_voice,
            "speed": speed,
            "response_format": response_format
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(endpoint, json=payload, headers=headers)
                if res.status_code != 200:
                    print(f"[CustomHTTPTTSProvider] Request failed ({res.status_code}): {res.text[:150]}")
                    return None

                with open(file_path, "wb") as f:
                    f.write(res.content)

                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return file_path
                return None
        except Exception as e:
            print(f"[CustomHTTPTTSProvider] Error generating speech: {e}")
            return None
