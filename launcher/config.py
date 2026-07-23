import hashlib
import json
import os
import platform
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

APP_NAME = "VLauncher"
APP_VERSION = "0.1.0"
UPDATE_REPO = "Damir00109/VLauncher_Windows"
UPDATE_RELEASES_API = f"https://api.github.com/repos/{UPDATE_REPO}/releases/latest"
UPDATE_REPO_URL = f"https://github.com/{UPDATE_REPO}"

API_BASE = "https://api.underworldmc.com"
PROXY_PORT = 8080

PACKS_SELECTOR_REPO = "https://github.com/Damir00109/Packs-Selector.git"
PACKS_SELECTOR_NAME = "Packs-Selector"

HWID = hashlib.sha256((platform.node() + str(uuid.getnode())).encode()).hexdigest()[:32]

_data_dir: Optional[Path] = None

# Aliases updated by refresh_path_aliases() for gradual migration / debugging.
BASE_DIR: Path
SESSION_FILE: Path
MINECRAFT_DIR: Path
INSTANCES_DIR: Path
SUBMODULES_DIR: Path
TOOLS_DIR: Path
PORTABLE_GIT_DIR: Path
PORTABLE_CONDA_DIR: Path
PORTABLE_CONDA_ENV: Path
PACKS_SELECTOR_DIR: Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False)) or hasattr(sys, "_MEIPASS") or "__compiled__" in globals()


def install_dir() -> Path:
    """Папка с exe (или корень репозитория в dev)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def default_data_dir() -> Path:
    """Каталог данных по умолчанию: %APPDATA%\\.mcvanilla"""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(appdata) / ".mcvanilla"
    return Path.home() / ".mcvanilla"


def meta_dir() -> Path:
    """Фиксированное место для указателя на data_dir (не зависит от выбранного пути)."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(appdata) / "VLauncher"
    return Path.home() / ".config" / "VLauncher"


def meta_prefs_file() -> Path:
    return meta_dir() / "prefs.json"


def _load_meta() -> Dict[str, Any]:
    path = meta_prefs_file()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_meta(data: Dict[str, Any]) -> None:
    root = meta_dir()
    root.mkdir(parents=True, exist_ok=True)
    meta_prefs_file().write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _resolve_data_dir() -> Path:
    env = os.environ.get("VLAUNCHER_DATA_DIR", "").strip()
    if env:
        return Path(env).expanduser()

    portable = install_dir() / "data_dir.txt"
    if portable.is_file():
        try:
            line = portable.read_text(encoding="utf-8").strip().splitlines()[0].strip()
            if line:
                return Path(line).expanduser()
        except OSError:
            pass

    raw = _load_meta().get("data_dir")
    if isinstance(raw, str) and raw.strip():
        return Path(raw.strip()).expanduser()

    return default_data_dir()


def data_dir() -> Path:
    global _data_dir
    if _data_dir is None:
        _data_dir = _resolve_data_dir()
    return _data_dir


def set_data_dir(path: Path | str, *, persist: bool = True) -> Path:
    global _data_dir
    resolved = Path(path).expanduser()
    if not resolved.is_absolute():
        resolved = (Path.cwd() / resolved).resolve()
    else:
        resolved = resolved.resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    _data_dir = resolved
    if persist:
        meta = _load_meta()
        meta["data_dir"] = str(resolved)
        _save_meta(meta)
    refresh_path_aliases()
    ensure_data_dirs()
    return resolved


def reset_data_dir_to_default(*, persist: bool = True) -> Path:
    if persist:
        meta = _load_meta()
        meta.pop("data_dir", None)
        _save_meta(meta)
    global _data_dir
    _data_dir = default_data_dir()
    refresh_path_aliases()
    ensure_data_dirs()
    return _data_dir


def session_file() -> Path:
    return data_dir() / "session.json"


def minecraft_dir() -> Path:
    return data_dir() / ".minecraft"


def instances_dir() -> Path:
    return data_dir() / "instances"


def submodules_dir() -> Path:
    return data_dir() / "submodules"


def tools_dir() -> Path:
    return data_dir() / "tools"


def portable_git_dir() -> Path:
    return tools_dir() / "git"


def portable_conda_dir() -> Path:
    return tools_dir() / "conda"


def portable_conda_env() -> Path:
    return portable_conda_dir() / "envs" / "vlauncher"


def packs_selector_dir() -> Path:
    return submodules_dir() / PACKS_SELECTOR_NAME


def profile_settings_file() -> Path:
    return data_dir() / "profile_settings.json"


def data_prefs_file() -> Path:
    return data_dir() / ".vlauncher_prefs.json"


def refresh_path_aliases() -> None:
    global BASE_DIR, SESSION_FILE, MINECRAFT_DIR, INSTANCES_DIR, SUBMODULES_DIR
    global TOOLS_DIR, PORTABLE_GIT_DIR, PORTABLE_CONDA_DIR, PORTABLE_CONDA_ENV, PACKS_SELECTOR_DIR
    BASE_DIR = data_dir()
    SESSION_FILE = session_file()
    MINECRAFT_DIR = minecraft_dir()
    INSTANCES_DIR = instances_dir()
    SUBMODULES_DIR = submodules_dir()
    TOOLS_DIR = tools_dir()
    PORTABLE_GIT_DIR = portable_git_dir()
    PORTABLE_CONDA_DIR = portable_conda_dir()
    PORTABLE_CONDA_ENV = portable_conda_env()
    PACKS_SELECTOR_DIR = packs_selector_dir()


def ensure_data_dirs() -> None:
    refresh_path_aliases()
    for path in (
        data_dir(),
        minecraft_dir(),
        instances_dir(),
        submodules_dir(),
        tools_dir(),
        meta_dir(),
    ):
        path.mkdir(parents=True, exist_ok=True)


def extract_texture_host() -> str:
    return urlparse(API_BASE).hostname or "127.0.0.1"


ensure_data_dirs()
