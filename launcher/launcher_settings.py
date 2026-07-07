import json
from pathlib import Path

from launcher.config import BASE_DIR

_PREFS_FILE = BASE_DIR / ".vlauncher_prefs.json"


def _load_prefs() -> dict:
    if not _PREFS_FILE.is_file():
        return {}
    try:
        data = json.loads(_PREFS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_prefs(data: dict) -> None:
    _PREFS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def get_keep_launcher_visible() -> bool:
    return bool(_load_prefs().get("keep_launcher_visible_on_start", False))


def set_keep_launcher_visible(value: bool) -> None:
    prefs = _load_prefs()
    prefs["keep_launcher_visible_on_start"] = bool(value)
    _save_prefs(prefs)
