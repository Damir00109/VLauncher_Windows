import locale
import sys


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
