import re
import os
from typing import Tuple, Optional, List, Dict
from pydub import AudioSegment
from pydub.utils import make_chunks


def parse_emotion_and_clean(text: str, emotion_map: Dict[str, int]) -> Tuple[str, Optional[str], Optional[int]]:
    """
    Extracts emotion tag (e.g., [joy], [sadness]) from text,
    maps it to the model's expression index, and returns the cleaned text.
    """
    detected_emotion = None
    expression_index = None

    # Find emotion tags like [joy], [anger], etc.
    matches = re.findall(r"\[([a-zA-Z0-9_\-]+)\]", text)
    for tag in matches:
        tag_lower = tag.lower()
        if tag_lower in emotion_map:
            detected_emotion = tag_lower
            expression_index = emotion_map[tag_lower]
            break

    # Strip all bracketed tags and stray markdown from text for TTS
    clean_text = re.sub(r"\[.*?\]", "", text)
    clean_text = re.sub(r"\*.*?\*", "", clean_text)  # Remove asterisks like *smiles*
    clean_text = re.sub(r"https?://\S+", "", clean_text)
    clean_text = re.sub(r"\s+([,.!?])", r"\1", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text)
    clean_text = clean_text.strip()

    return clean_text, detected_emotion, expression_index


def get_audio_volume_chunks(audio_path: str, chunk_length_ms: int = 20) -> List[float]:
    """
    Calculates normalized volume (0.0 to 1.0) for every audio chunk (default 20ms).
    Used by frontend for mouth opening (lip-sync) synchronization.
    """
    if not os.path.exists(audio_path):
        return []

    try:
        audio = AudioSegment.from_file(audio_path)
        chunks = make_chunks(audio, chunk_length_ms)
        volumes = [chunk.rms for chunk in chunks]
        max_volume = max(volumes) if volumes else 0
        if max_volume == 0:
            return [0.0] * len(chunks)

        return [round(vol / max_volume, 3) for vol in volumes]
    except Exception as e:
        print(f"[Live2D Helper] Error calculating audio volumes: {e}")
        return []
