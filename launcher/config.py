import hashlib
import json
import platform
import sys
import uuid
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

def _app_base_dir() -> Path:
    """Корень лаунчера: папка с main.py (или рядом с исполняемым файлом)."""
    if "__compiled__" in globals() or getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _app_base_dir()
CONFIG_FILE = BASE_DIR / "launcher_config.json"

SESSION_FILE = BASE_DIR / "session.json"
MINECRAFT_DIR = BASE_DIR / ".minecraft"
INSTANCES_DIR = BASE_DIR / "instances"
SUBMODULES_DIR = BASE_DIR / "submodules"
TOOLS_DIR = BASE_DIR / "tools"
PORTABLE_GIT_DIR = TOOLS_DIR / "git"
PROXY_PORT = 8080

PACKS_SELECTOR_REPO = "https://github.com/Damir00109/Packs-Selector.git"
PACKS_SELECTOR_NAME = "Packs-Selector"
PACKS_SELECTOR_DIR = SUBMODULES_DIR / PACKS_SELECTOR_NAME

HWID = hashlib.sha256((platform.node() + str(uuid.getnode())).encode()).hexdigest()[:32]

_DEFAULT_CONFIG: Dict[str, Any] = {
    "api_base": "http://127.0.0.1:8000",
    "app_name": "VLauncher",
}


def load_launcher_config() -> Dict[str, Any]:
    if not CONFIG_FILE.is_file():
        return dict(_DEFAULT_CONFIG)
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(_DEFAULT_CONFIG)
        merged = dict(_DEFAULT_CONFIG)
        merged.update({k: v for k, v in data.items() if v is not None})
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_CONFIG)


_LAUNCHER_CONFIG = load_launcher_config()
API_BASE = str(_LAUNCHER_CONFIG.get("api_base", _DEFAULT_CONFIG["api_base"])).rstrip("/")
APP_NAME = str(_LAUNCHER_CONFIG.get("app_name", _DEFAULT_CONFIG["app_name"]))


def extract_texture_host() -> str:
    return urlparse(API_BASE).hostname or "127.0.0.1"
