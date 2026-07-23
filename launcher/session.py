import json
from typing import Any, Dict

from launcher.config import ensure_data_dirs, session_file


def load_session() -> Dict[str, Any]:
    path = session_file()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_session(refresh_token: str, login: str) -> None:
    ensure_data_dirs()
    session_file().write_text(
        json.dumps({"refreshToken": refresh_token, "login": login}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def clear_session_file() -> None:
    try:
        session_file().unlink(missing_ok=True)
    except OSError:
        pass
