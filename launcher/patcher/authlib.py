import glob
from pathlib import Path
from typing import Callable, Optional

from launcher.config import MINECRAFT_DIR
from launcher.patcher.jar import java_utf8_constant, patch_jar_files

TEXTURE_CHECKER_CLASS = "com/mojang/authlib/yggdrasil/TextureUrlChecker.class"
TEXTURE_CHECKER_STUB = (
    Path(__file__).resolve().parent / "assets" / "com" / "mojang" / "authlib" / "yggdrasil" / "TextureUrlChecker.class"
)


def _legacy_texture_patch(texture_host: str, data: bytes) -> tuple[bytes, bool]:
    new_pat = java_utf8_constant(texture_host)
    changed = False
    for old in (b"\x01\x00\x0e.minecraft.net", b"\x01\x00\x0b.mojang.com"):
        if old in data:
            data = data.replace(old, new_pat)
            changed = True
    tex = b"\x01\x00\x16textures.minecraft.net"
    if tex in data:
        data = data.replace(tex, new_pat)
        changed = True
    return data, changed


def patch_authlib(
    texture_host: str,
    log: Optional[Callable[[str], None]] = None,
    *,
    refresh_backup: bool = False,
) -> int:
    pattern = str(MINECRAFT_DIR / "libraries" / "com" / "mojang" / "authlib" / "*" / "authlib-*.jar")
    stub_bytes = TEXTURE_CHECKER_STUB.read_bytes() if TEXTURE_CHECKER_STUB.is_file() else None

    def _patch(data: bytes) -> tuple[bytes, bool]:
        if stub_bytes is not None:
            return stub_bytes, data != stub_bytes
        return _legacy_texture_patch(texture_host, data)

    count = patch_jar_files(
        pattern,
        TEXTURE_CHECKER_CLASS,
        _patch,
        log,
        refresh_backup=refresh_backup,
        log_label="authlib TextureUrlChecker",
    )
    if log:
        if count:
            mode = "stub" if stub_bytes else f"host {texture_host}"
            log(f"[PATCH] authlib: {count} jar ({mode})")
        elif not glob.glob(pattern):
            log("[PATCH] authlib jar не найден в libraries/")
        else:
            log("[PATCH] authlib: TextureUrlChecker уже актуален")
    return count
