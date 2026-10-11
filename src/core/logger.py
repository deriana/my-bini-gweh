import time
from collections import deque
from datetime import datetime
from typing import List, Dict, Any


class AppLogger:
    """
    In-memory circular log buffer to record real-time model, TTS, and tool execution logs
    accessible via the Settings Log Viewer.
    """

    def __init__(self, max_entries: int = 300):
        self.buffer = deque(maxlen=max_entries)

    def log(self, level: str, category: str, message: str, details: Any = None):
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "level": level.upper(),
            "category": category,
            "message": message,
            "details": details
        }
        self.buffer.append(entry)
        # Also print to terminal
        print(f"[{entry['timestamp']}] [{entry['level']}] [{entry['category']}] {message}")

    def info(self, category: str, message: str, details: Any = None):
        self.log("INFO", category, message, details)

    def warning(self, category: str, message: str, details: Any = None):
        self.log("WARN", category, message, details)

    def error(self, category: str, message: str, details: Any = None):
        self.log("ERROR", category, message, details)

    def get_logs(self, limit: int = 150) -> List[Dict[str, Any]]:
        entries = list(self.buffer)
        return entries[-limit:]

    def clear(self):
        self.buffer.clear()


app_logger = AppLogger()
