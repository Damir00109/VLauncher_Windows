import hashlib
import platform
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

def _app_base_dir() -> Path:
    """Корень лаунчера: папка с main.py (или рядом с исполняемым файлом)."""
    if "__compiled__" in globals() or getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _app_base_dir()

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

API_BASE = "https://api.underworldmc.com"
APP_NAME = "VLauncher"


def extract_texture_host() -> str:
    return urlparse(API_BASE).hostname or "127.0.0.1"
