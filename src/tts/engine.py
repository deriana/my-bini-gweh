import os
import uuid
import base64
import asyncio
from typing import Optional, Tuple, List
import edge_tts
from src.live2d import get_audio_volume_chunks


class TTSEngine:
    def __init__(self, cache_dir: str = "cache", default_voice: str = "id-ID-GadisNeural"):
        self.cache_dir = cache_dir
        self.default_voice = default_voice
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_emotion_pitch_rate(self, emotion: Optional[str]) -> Tuple[str, str]:
        """Maps emotion to subtle pitch and rate adjustments for natural speech."""
        if not emotion:
            return "+0Hz", "+0%"

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
        return "+0Hz", "+0%"

    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        emotion: Optional[str] = None
    ) -> Optional[Tuple[str, str, List[float]]]:
        """
        Generates TTS audio file using edge-tts.
        Returns:
            Tuple of (file_path, base64_audio, volume_chunks) or None if text is empty.
        """
        if not text or not text.strip():
            return None

        chosen_voice = voice or self.default_voice
        pitch, rate = self._get_emotion_pitch_rate(emotion)

        file_id = f"{uuid.uuid4().hex[:12]}.mp3"
        file_path = os.path.join(self.cache_dir, file_id)

        try:
            communicate = edge_tts.Communicate(
                text=text.strip(),
                voice=chosen_voice,
                pitch=pitch,
                rate=rate
            )
            await communicate.save(file_path)

            # Read file and encode to base64
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            # Calculate lip sync volumes (20ms chunks)
            volumes = get_audio_volume_chunks(file_path, chunk_length_ms=20)

            return file_path, audio_base64, volumes
        except Exception as e:
            print(f"[TTS Engine] Error generating audio for '{text}': {e}")
            return None
