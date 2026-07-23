import glob
from typing import Callable, List, Optional, Tuple

from launcher.config import minecraft_dir, PROXY_PORT
from launcher.patcher.jar import patch_jar_files

REALMS_ENV_CLASS = "com/mojang/realmsclient/client/RealmsClient$Environment.class"
REALMS_CLIENT_CLASS = "com/mojang/realmsclient/client/RealmsClient.class"

_PROXY_HOST = f"127.0.0.1:{PROXY_PORT}".encode("ascii")

# Только замены одинаковой длины — иначе .class повреждается.
_REALM_HOST_CANDIDATES: List[Tuple[bytes, bytes]] = [
    (b"localhost:8080", _PROXY_HOST),
    (b"localhost:8756", _PROXY_HOST),
    (b"pc.realms.minecraft.net", _PROXY_HOST),
]


def _realm_replacements() -> List[Tuple[bytes, bytes]]:
    return [(src, dst) for src, dst in _REALM_HOST_CANDIDATES if len(src) == len(dst)]


def patch_realms_client(
    log: Optional[Callable[[str], None]] = None,
    *,
    refresh_backup: bool = False,
) -> int:
    replacements = _realm_replacements()
    pattern = str(minecraft_dir() / "libraries" / "net" / "minecraft" / "client" / "*" / "client-*.jar")
    target_classes = (REALMS_ENV_CLASS, REALMS_CLIENT_CLASS)

    if not replacements:
        if log:
            log("[PATCH] Realms: нет замен host с одинаковой длиной (пропуск)")
        return 0

    def _patch(data: bytes, _jar_path: str) -> tuple[bytes, bool]:
        changed = False
        for src, dst in replacements:
            if src in data:
                data = data.replace(src, dst)
                changed = True
        return data, changed

    patched_count = 0
    for class_name in target_classes:
        patched_count += patch_jar_files(
            pattern,
            class_name,
            _patch,
            log,
            refresh_backup=refresh_backup,
            log_label=f"Realms ({class_name.rsplit('/', 1)[-1]})",
        )

    if log:
        if patched_count:
            log(f"[PATCH] Realms: {patched_count} client jar → {_PROXY_HOST.decode()}")
        elif not glob.glob(pattern):
            log("[PATCH] Realms: client jar не найден")
        else:
            log("[PATCH] Realms: host уже пропатчен или строки не найдены")
    return patched_count
