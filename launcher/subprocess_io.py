import locale
import subprocess
import sys
from typing import Any, Dict

from launcher.config import is_debug_mode

_PATCHED = False


def subprocess_console_encoding() -> str:
    enc = locale.getpreferredencoding(False)
    if enc:
        return enc
    return "cp1251" if sys.platform == "win32" else "utf-8"


def decode_subprocess_bytes(raw: bytes) -> str:
    if not raw:
        return ""
    candidates = []
    for enc in ("utf-8", subprocess_console_encoding(), "cp1251", "cp866"):
        if enc and enc not in candidates:
            candidates.append(enc)
    for enc in candidates:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def hidden_subprocess_kwargs() -> Dict[str, Any]:
    if is_debug_mode() or sys.platform != "win32":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }


def _merge_hidden_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    hidden = hidden_subprocess_kwargs()
    if not hidden:
        return kwargs
    merged = dict(kwargs)
    merged["creationflags"] = int(merged.get("creationflags", 0)) | int(hidden["creationflags"])
    if "startupinfo" not in merged:
        merged["startupinfo"] = hidden["startupinfo"]
    return merged


def install_hidden_subprocess_patch() -> None:
    global _PATCHED
    if _PATCHED or is_debug_mode() or sys.platform != "win32":
        return

    original_popen = subprocess.Popen
    original_run = subprocess.run

    def patched_popen(*args, **kwargs):
        return original_popen(*args, **_merge_hidden_kwargs(kwargs))

    def patched_run(*args, **kwargs):
        return original_run(*args, **_merge_hidden_kwargs(kwargs))

    subprocess.Popen = patched_popen  # type: ignore[misc, assignment]
    subprocess.run = patched_run  # type: ignore[misc, assignment]
    _PATCHED = True
