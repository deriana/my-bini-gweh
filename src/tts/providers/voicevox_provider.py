import os
import uuid
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from src.tts.base import BaseTTSProvider


class VoicevoxTTSProvider(BaseTTSProvider):
    """
    VOICEVOX Engine TTS Provider.
    Connects to local or remote VOICEVOX instance (default http://127.0.0.1:50021).
    Provides iconic anime voices including Zundamon, Shikoku Metan, Kasukabe Tsumugi, etc.
    """

    DEFAULT_VOICES = [
        {"id": "3", "name": "Zundamon (ずんだもん - Normal)", "lang": "ja-JP"},
        {"id": "1", "name": "Zundamon (ずんだもん - Amaama/Manja)", "lang": "ja-JP"},
        {"id": "7", "name": "Zundamon (ずんだもん - Tsuntsun/Tsundere)", "lang": "ja-JP"},
        {"id": "2", "name": "Shikoku Metan (四国めたん - Normal)", "lang": "ja-JP"},
        {"id": "0", "name": "Shikoku Metan (四国めたん - Amaama)", "lang": "ja-JP"},
        {"id": "8", "name": "Kasukabe Tsumugi (春日部つむぎ - Normal)", "lang": "ja-JP"},
        {"id": "14", "name": "Meimei Himari (冥鳴ひまり - Normal)", "lang": "ja-JP"}
    ]

    def __init__(self, config: Dict[str, Any], cache_dir: str):
        super().__init__("voicevox", "VOICEVOX Engine", config, cache_dir)
        self._resolved_base_url: Optional[str] = None
        self._cached_speakers: List[Dict[str, str]] = []
        self._client: Optional[httpx.AsyncClient] = None
        self._client_loop: Optional[Any] = None

    def _get_client(self) -> httpx.AsyncClient:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if (
            self._client is None
            or self._client.is_closed
            or self._client_loop != loop
            or (self._client_loop and self._client_loop.is_closed())
        ):
            self._client = httpx.AsyncClient(
                timeout=15.0,
                limits=httpx.Limits(max_keepalive_connections=20, keepalive_expiry=60.0)
            )
            self._client_loop = loop
        return self._client

    def _get_base_url(self) -> str:
        if self._resolved_base_url:
            return self._resolved_base_url
        from src.core.network import resolve_service_url
        raw_url = self.config.get("base_url", "http://127.0.0.1:50021").rstrip("/")
        self._resolved_base_url = resolve_service_url(raw_url, probe_path="version")
        return self._resolved_base_url

    def update_config(self, new_config: Dict[str, Any]):
        super().update_config(new_config)
        self._resolved_base_url = None  # Reset URL cache on config change

    async def is_available(self) -> bool:
        base_url = self._get_base_url()
        client = self._get_client()
        try:
            res = await client.get(f"{base_url}/version", timeout=2.5)
            return res.status_code == 200
        except Exception:
            return False

    async def fetch_engine_speakers(self) -> List[Dict[str, str]]:
        """Queries the live VOICEVOX server for all registered speakers and styles."""
        base_url = self._get_base_url()
        client = self._get_client()
        voices = []
        try:
            res = await client.get(f"{base_url}/speakers", timeout=4.0)
            if res.status_code == 200:
                data = res.json()
                for speaker in data:
                    char_name = speaker.get("name", "Speaker")
                    for style in speaker.get("styles", []):
                        style_id = str(style.get("id"))
                        style_name = style.get("name", "Normal")
                        voices.append({
                            "id": style_id,
                            "name": f"{char_name} - {style_name}",
                            "character": char_name,
                            "style": style_name,
                            "lang": "ja-JP"
                        })
                if voices:
                    self._cached_speakers = voices
                    self.config["available_voices"] = voices
        except Exception as e:
            print(f"[VoicevoxTTSProvider] Could not fetch live speakers: {e}")
        return voices or self._cached_speakers or self.DEFAULT_VOICES

    def get_available_voices(self) -> List[Dict[str, str]]:
        if self._cached_speakers:
            return self._cached_speakers
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

        base_url = self._get_base_url()
        speaker_id = str(voice or self.config.get("default_voice", "3"))
        if not speaker_id.isdigit():
            speaker_id = str(self.config.get("default_voice", "3"))
        speed = float(self.config.get("speed", 1.0))

        file_id = f"voicevox_{uuid.uuid4().hex[:12]}.wav"
        file_path = os.path.join(self.cache_dir, file_id)

        from src.core.romanize import prepare_for_voicevox
        synth_text = prepare_for_voicevox(text)
        if not synth_text:
            synth_text = text.strip()

        try:
            client = self._get_client()
            # 1. Generate audio query
            query_res = await client.post(
                f"{base_url}/audio_query",
                params={"text": synth_text, "speaker": speaker_id}
            )
            if query_res.status_code != 200:
                print(f"[VoicevoxTTSProvider] audio_query failed ({query_res.status_code}): {query_res.text}")
                return None

            query_data = query_res.json()
            query_data["speedScale"] = speed

            # Optional emotion pitch adjustments
            if emotion:
                emotion = emotion.lower()
                if emotion in ["joy", "happy", "ceria"]:
                    query_data["pitchScale"] = query_data.get("pitchScale", 0.0) + 0.05
                    query_data["intonationScale"] = query_data.get("intonationScale", 1.0) * 1.15
                elif emotion in ["anger", "angry", "marah"]:
                    query_data["pitchScale"] = query_data.get("pitchScale", 0.0) + 0.08
                    query_data["speedScale"] *= 1.1
                elif emotion in ["sadness", "sad", "sedih"]:
                    query_data["pitchScale"] = query_data.get("pitchScale", 0.0) - 0.05
                    query_data["speedScale"] *= 0.9

            # 2. Synthesize audio
            synth_res = await client.post(
                f"{base_url}/synthesis",
                params={"speaker": speaker_id},
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            if synth_res.status_code != 200:
                print(f"[VoicevoxTTSProvider] synthesis failed ({synth_res.status_code}): {synth_res.text}")
                return None

            with open(file_path, "wb") as f:
                f.write(synth_res.content)

            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return file_path
            return None

        except Exception as e:
            print(f"[VoicevoxTTSProvider] Error generating speech: {e}")
            return None
