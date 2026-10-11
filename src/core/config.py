import json
import os
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "config.json"
MCP_CONFIG_FILE = CONFIG_DIR / "mcp_servers.json"


def load_config() -> Dict[str, Any]:
    """Loads and returns the main application configuration."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_FILE}")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_mcp_config_path() -> str:
    """Returns the absolute path to mcp_servers.json."""
    return str(MCP_CONFIG_FILE)
