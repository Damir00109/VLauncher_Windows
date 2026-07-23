import json
from typing import Any, Dict

from launcher.config import data_prefs_file, ensure_data_dirs


def _load_prefs() -> Dict[str, Any]:
    path = data_prefs_file()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_prefs(data: Dict[str, Any]) -> None:
    ensure_data_dirs()
    data_prefs_file().write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def get_keep_launcher_visible() -> bool:
    return bool(_load_prefs().get("keep_launcher_visible_on_start", False))


def set_keep_launcher_visible(value: bool) -> None:
    prefs = _load_prefs()
    prefs["keep_launcher_visible_on_start"] = bool(value)
    _save_prefs(prefs)
