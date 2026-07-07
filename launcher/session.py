import json
from typing import Any, Dict

from launcher.config import SESSION_FILE


def load_session() -> Dict[str, Any]:
    if not SESSION_FILE.exists():
        return {}
    try:
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_session(refresh_token: str, login: str) -> None:
    SESSION_FILE.write_text(
        json.dumps({"refreshToken": refresh_token, "login": login}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def clear_session_file() -> None:
    try:
        SESSION_FILE.unlink(missing_ok=True)
    except OSError:
        pass
