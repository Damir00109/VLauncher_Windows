import glob
import re
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

from launcher.config import minecraft_dir
from launcher.patcher.jar import java_utf8_constant, patch_jar_files

TEXTURE_CHECKER_CLASS = "com/mojang/authlib/yggdrasil/TextureUrlChecker.class"
_ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "com" / "mojang" / "authlib" / "yggdrasil"
_LEGACY_CONSTANTS = (
    b"\x01\x00\x0e.minecraft.net",
    b"\x01\x00\x0b.mojang.com",
    b"\x01\x00\x16textures.minecraft.net",
)
_AUTHLIB_VERSION_RE = re.compile(r"authlib[\\/]+(\d+)\.(\d+)\.(\d+)[\\/]", re.IGNORECASE)


def _parse_authlib_version(jar_path: str) -> Tuple[int, int, int]:
    match = _AUTHLIB_VERSION_RE.search(jar_path.replace("/", "\\"))
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())


def _stub_release_for_authlib(version: Tuple[int, int, int]) -> int:
    major, _, _ = version
    return 25 if major >= 9 else 21


def _load_stub(release: int) -> Optional[bytes]:
    path = _ASSETS_DIR / f"TextureUrlChecker-j{release}.class"
    if not path.is_file():
        legacy = _ASSETS_DIR / "TextureUrlChecker.class"
        if release == 21 and legacy.is_file():
            return legacy.read_bytes()
        return None
    return path.read_bytes()


def _legacy_texture_patch(texture_host: str, data: bytes) -> tuple[bytes, bool]:
    new_pat = java_utf8_constant(texture_host)
    changed = False
    for old in _LEGACY_CONSTANTS:
        if old in data and len(old) == len(new_pat):
            data = data.replace(old, new_pat)
            changed = True
    return data, changed


def _is_legacy_patched(texture_host: str, data: bytes) -> bool:
    new_pat = java_utf8_constant(texture_host)
    if new_pat not in data:
        return False
    return not any(old in data for old in _LEGACY_CONSTANTS)


def patch_authlib(
    texture_host: str,
    log: Optional[Callable[[str], None]] = None,
    *,
    refresh_backup: bool = False,
) -> int:
    pattern = str(minecraft_dir() / "libraries" / "com" / "mojang" / "authlib" / "*" / "authlib-*.jar")
    patch_modes: Dict[str, str] = {}

    def _patch(data: bytes, jar_path: str) -> tuple[bytes, bool]:
        version = _parse_authlib_version(jar_path)
        version_label = ".".join(str(part) for part in version) if version != (0, 0, 0) else "?"

        if _is_legacy_patched(texture_host, data):
            patch_modes[jar_path] = f"host {texture_host} (authlib {version_label})"
            return data, False

        patched, changed = _legacy_texture_patch(texture_host, data)
        if changed:
            patch_modes[jar_path] = f"host {texture_host} (authlib {version_label})"
            return patched, True

        release = _stub_release_for_authlib(version)
        stub_bytes = _load_stub(release)
        if stub_bytes is None:
            patch_modes[jar_path] = f"skip (stub Java {release} missing)"
            return data, False

        patch_modes[jar_path] = f"stub Java {release} (authlib {version_label})"
        return stub_bytes, data != stub_bytes

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
            modes = ", ".join(sorted(set(patch_modes.values())))
            log(f"[PATCH] authlib: {count} jar ({modes})")
        elif not glob.glob(pattern):
            log("[PATCH] authlib jar не найден в libraries/")
        else:
            log("[PATCH] authlib: TextureUrlChecker уже актуален")
    return count
