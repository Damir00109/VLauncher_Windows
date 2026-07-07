import json
from typing import Dict, List, Set

from launcher.config import BASE_DIR

SETTINGS_FILE = BASE_DIR / "profile_settings.json"


def _load_all() -> Dict[str, Dict]:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(data: Dict[str, Dict]) -> None:
    SETTINGS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_ram_mb(profile_id: str, default_ram_mb: int) -> int:
    entry = _load_all().get(profile_id, {})
    ram = entry.get("ramMb")
    if isinstance(ram, int) and ram >= 1024:
        return ram
    return max(1024, int(default_ram_mb))


def set_ram_mb(profile_id: str, ram_mb: int) -> None:
    data = _load_all()
    entry = data.get(profile_id, {})
    if not isinstance(entry, dict):
        entry = {}
    entry["ramMb"] = int(ram_mb)
    data[profile_id] = entry
    _save_all(data)


def get_enabled_optional_mod_ids(profile_id: str, catalog: List[Dict]) -> Set[str]:
    valid_ids = {str(mod["id"]) for mod in catalog if mod.get("id")}
    entry = _load_all().get(profile_id, {})
    saved = entry.get("optionalMods")
    if isinstance(saved, list):
        return {str(item) for item in saved if str(item) in valid_ids}
    return {str(mod["id"]) for mod in catalog if mod.get("defaultEnabled") and mod.get("id")}


def set_enabled_optional_mod_ids(profile_id: str, enabled_ids: List[str]) -> None:
    data = _load_all()
    entry = data.get(profile_id, {})
    if not isinstance(entry, dict):
        entry = {}
    entry["optionalMods"] = list(enabled_ids)
    data[profile_id] = entry
    _save_all(data)
