import os
import base64
from typing import Optional, Tuple, List, Dict, Any

from src.tts.base import BaseTTSProvider
from src.tts.providers import (
    EdgeTTSProvider,
    KokoroTTSProvider,
    VoicevoxTTSProvider,
    CustomHTTPTTSProvider
)
from src.live2d import get_audio_volume_chunks


class TTSManager:
    """
    Dynamic Central TTS Engine Manager.
    Coordinates multiple TTS providers (Edge-TTS, Kokoro-82M, VOICEVOX, Custom HTTP)
    and ensures consistent Base64 audio encoding and Live2D lip-sync synchronization.
    """

    def __init__(self, config: Dict[str, Any], cache_dir: str = "cache"):
        self.config = config or {}
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        self.active_provider_key = self.config.get("active_provider", "edge")

        # Extract provider specific settings
        providers_cfg = self.config.get("providers", {})
        edge_cfg = providers_cfg.get("edge", {})
        if not edge_cfg and "default_voice" in self.config:
            # Backwards compatibility with flat config
            edge_cfg = {
                "default_voice": self.config.get("default_voice", "id-ID-GadisNeural"),
                "available_voices": self.config.get("available_voices", [])
            }

        kokoro_cfg = providers_cfg.get("kokoro", {})
        voicevox_cfg = providers_cfg.get("voicevox", {})
        custom_cfg = providers_cfg.get("custom_http", {})

        self.providers: Dict[str, BaseTTSProvider] = {
            "edge": EdgeTTSProvider(edge_cfg, cache_dir),
            "kokoro": KokoroTTSProvider(kokoro_cfg, cache_dir),
            "voicevox": VoicevoxTTSProvider(voicevox_cfg, cache_dir),
            "custom_http": CustomHTTPTTSProvider(custom_cfg, cache_dir)
        }

    @property
    def default_voice(self) -> str:
        provider = self.providers.get(self.active_provider_key)
        if provider:
            return provider.config.get("default_voice", "")
        return ""

    @default_voice.setter
    def default_voice(self, val: str):
        provider = self.providers.get(self.active_provider_key)
        if provider:
            provider.config["default_voice"] = val

    def get_active_provider(self) -> BaseTTSProvider:
        return self.providers.get(self.active_provider_key, self.providers["edge"])

    def set_active_provider(self, provider_id: str):
        if provider_id in self.providers:
            self.active_provider_key = provider_id
            self.config["active_provider"] = provider_id

    def update_config(self, new_config: Dict[str, Any]):
        """Dynamically reconfigures all providers and active selection from Settings."""
        self.config = new_config
        self.active_provider_key = self.config.get("active_provider", "edge")

        providers_cfg = self.config.get("providers", {})
        for key, provider in self.providers.items():
            if key in providers_cfg:
                provider.update_config(providers_cfg[key])

    def get_available_voices(self, provider_id: Optional[str] = None) -> List[Dict[str, str]]:
        target_id = provider_id or self.active_provider_key
        provider = self.providers.get(target_id)
        if provider:
            return provider.get_available_voices()
        return []

    async def list_providers_status(self) -> List[Dict[str, Any]]:
        """Returns discovery information and availability status for all registered engines."""
        status_list = []
        for p_id, provider in self.providers.items():
            is_avail = await provider.is_available()
            status_list.append({
                "id": p_id,
                "name": provider.name,
                "is_active": p_id == self.active_provider_key,
                "is_available": is_avail,
                "default_voice": provider.config.get("default_voice", ""),
                "voices": provider.get_available_voices(),
                "config": provider.config
            })
        return status_list

    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        emotion: Optional[str] = None,
        provider_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Tuple[str, str, List[float]]]:
        """
        Coordinates audio generation using chosen or active provider.
        Computes Live2D lip-sync chunks and Base64 audio representation.
        Gracefully falls back to Edge-TTS if local/custom engine fails.
        """
        if not text or not text.strip():
            return None

        target_provider_id = provider_id or self.active_provider_key
        provider = self.providers.get(target_provider_id, self.providers["edge"])

        file_path = None
        try:
            file_path = await provider.generate_audio(
                text=text,
                voice=voice,
                emotion=emotion,
                **kwargs
            )
        except Exception as e:
            print(f"[TTSManager] Provider '{target_provider_id}' failed: {e}")

        # Graceful fallback to Edge-TTS if active engine failed and is not edge
        if not file_path and target_provider_id != "edge":
            print(f"[TTSManager] Falling back to Edge-TTS for: '{text[:40]}...'")
            try:
                edge_provider = self.providers["edge"]
                file_path = await edge_provider.generate_audio(
                    text=text,
                    voice=edge_provider.config.get("default_voice", "id-ID-GadisNeural"),
                    emotion=emotion
                )
            except Exception as fe:
                print(f"[TTSManager] Fallback failed: {fe}")

        if not file_path or not os.path.exists(file_path):
            return None

        try:
            # Read and encode audio to base64
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            # Calculate Live2D mouth movement (lip sync) volume chunks
            volumes = get_audio_volume_chunks(file_path, chunk_length_ms=20)

            return file_path, audio_base64, volumes
        except Exception as e:
            print(f"[TTSManager] Error processing audio file '{file_path}': {e}")
            return None
