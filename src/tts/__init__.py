from .base import BaseTTSProvider
from .manager import TTSManager

# Backward-compatible alias
TTSEngine = TTSManager

__all__ = ["BaseTTSProvider", "TTSManager", "TTSEngine"]
