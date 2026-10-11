import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class BaseTTSProvider(ABC):
    """
    Abstract Base Class for all Text-to-Speech providers.
    Every provider produces a local audio file (.wav or .mp3) that the
    TTSManager consumes to generate uniform Base64 audio and Live2D lip-sync chunks.
    """

    def __init__(self, provider_id: str, name: str, config: Dict[str, Any], cache_dir: str):
        self.provider_id = provider_id
        self.name = name
        self.config = config
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def update_config(self, new_config: Dict[str, Any]):
        """Updates runtime configuration for this provider."""
        self.config = new_config

    @abstractmethod
    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        emotion: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Generates audio file from text.
        Returns:
            Path to generated audio file (.mp3 or .wav), or None on failure.
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        Returns list of available voice dictionaries:
        [{"id": "...", "name": "...", "lang": "..."}]
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Verifies if provider engine, binary, or API endpoint is accessible and ready.
        """
        pass
