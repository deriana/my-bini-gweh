import os
from pathlib import Path
from typing import Dict, Any

from src.core.config import load_config, save_config, get_mcp_config_path
from src.core.database import db
from src.core.logger import app_logger
from src.core.persona import persona_engine, extract_mood_from_text
from src.tts import TTSManager
from src.mcp import MCPManager
from src.llm import LLMService

# Core Path Constants
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
BG_DIR = DATA_DIR / "backgrounds"
CACHE_DIR = BASE_DIR / "cache"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Central Runtime Configuration
config: Dict[str, Any] = load_config()

# Domain Singletons
tts_engine = TTSManager(
    config=config.get("tts", {}),
    cache_dir=str(CACHE_DIR)
)

mcp_manager = MCPManager(get_mcp_config_path())

llm_service = LLMService(
    config=config,
    tts_engine=tts_engine,
    mcp_manager=mcp_manager
)


def reload_services_config(new_config: Dict[str, Any]) -> None:
    """Updates runtime config, persists to disk, and live-reloads dependent services."""
    global config
    if "persona" not in new_config and "persona" in config:
        new_config["persona"] = config["persona"]
    config = new_config
    save_config(config)

    tts_engine.update_config(config.get("tts", {}))
    llm_service.update_config(config)
    app_logger.info("Services", "Central configuration reloaded and applied across all domain services.")
