import json

from launcher.config import CONFIG_FILE, load_launcher_config


def get_keep_launcher_visible() -> bool:
    return bool(load_launcher_config().get("keep_launcher_visible_on_start", False))


def set_keep_launcher_visible(value: bool) -> None:
    config = load_launcher_config()
    config["keep_launcher_visible_on_start"] = bool(value)
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
