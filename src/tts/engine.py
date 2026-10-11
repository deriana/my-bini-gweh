"""
Legacy compatibility module for TTSEngine.
Redirects to TTSManager.
"""
from src.tts.manager import TTSManager

# Backward-compatible alias
TTSEngine = TTSManager

__all__ = ["TTSEngine", "TTSManager"]
