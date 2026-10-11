import os
import uuid
from typing import Optional, List, Dict, Any, Tuple
import edge_tts
from src.tts.base import BaseTTSProvider


class EdgeTTSProvider(BaseTTSProvider):
    """
    Microsoft Edge TTS provider. Fast, high quality, and requires no local GPU/model.
    """

    DEFAULT_VOICES = [
        {"id": "id-ID-GadisNeural", "name": "Gadis (Indonesia - Ceria/Wanita)", "lang": "id-ID"},
        {"id": "id-ID-ArdiNeural", "name": "Ardi (Indonesia - Tenang/Pria)", "lang": "id-ID"},
        {"id": "ja-JP-NanamiNeural", "name": "Nanami (Jepang - Lucu/Anime)", "lang": "ja-JP"},
        {"id": "ja-JP-KeitaNeural", "name": "Keita (Jepang - Sopan/Pria)", "lang": "ja-JP"},
        {"id": "en-US-AvaMultilingualNeural", "name": "Ava (Multilingual - Alami)", "lang": "en-US"},
        {"id": "en-US-JennyNeural", "name": "Jenny (Inggris - Ramah)", "lang": "en-US"},
        {"id": "en-US-GuyNeural", "name": "Guy (Inggris - Santai/Pria)", "lang": "en-US"}
    ]

    def __init__(self, config: Dict[str, Any], cache_dir: str):
        super().__init__("edge", "Microsoft Edge TTS", config, cache_dir)

    def _get_emotion_pitch_rate(self, emotion: Optional[str]) -> Tuple[str, str]:
        """Maps emotion tags to subtle pitch and speech rate adjustments."""
        base_rate = self.config.get("rate", "+0%")
        base_pitch = self.config.get("pitch", "+0Hz")

        if not emotion:
            return base_pitch, base_rate

        emotion = emotion.lower()
        if emotion in ["joy", "happy", "ceria", "gembira"]:
            return "+10Hz", "+8%"
        elif emotion in ["anger", "angry", "marah", "kesal"]:
            return "+15Hz", "+15%"
        elif emotion in ["sadness", "sad", "sedih", "kecewa"]:
            return "-8Hz", "-10%"
        elif emotion in ["surprise", "kaget", "terkejut"]:
            return "+12Hz", "+10%"
        elif emotion in ["blush", "shy", "malu"]:
            return "+4Hz", "-5%"
        return base_pitch, base_rate

    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        emotion: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        if not text or not text.strip():
            return None

        chosen_voice = voice or self.config.get("default_voice", "id-ID-GadisNeural")
        pitch, rate = self._get_emotion_pitch_rate(emotion)

        file_id = f"edge_{uuid.uuid4().hex[:12]}.mp3"
        file_path = os.path.join(self.cache_dir, file_id)

        try:
            communicate = edge_tts.Communicate(
                text=text.strip(),
                voice=chosen_voice,
                pitch=pitch,
                rate=rate
            )
            await communicate.save(file_path)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return file_path
            return None
        except Exception as e:
            print(f"[EdgeTTSProvider] Error generating speech: {e}")
            return None

    def get_available_voices(self) -> List[Dict[str, str]]:
        configured_voices = self.config.get("available_voices")
        if configured_voices and isinstance(configured_voices, list):
            return configured_voices
        return self.DEFAULT_VOICES

    async def is_available(self) -> bool:
        # Edge-TTS connects over standard HTTPS
        return True
