import glob
import os
import shutil
import zipfile
from typing import Callable, Optional


def java_utf8_constant(value: str) -> bytes:
    data = value.encode("utf-8")
    return b"\x01" + len(data).to_bytes(2, "big") + data


def patch_jar_files(
    jar_glob: str,
    class_name: str,
    patch_fn: Callable[[bytes, str], tuple[bytes, bool]],
    log: Optional[Callable[[str], None]] = None,
    *,
    refresh_backup: bool = False,
    log_label: str = "patch",
) -> int:
    jars = [p for p in glob.glob(jar_glob) if not p.endswith((".bak", ".tmp"))]
    patched_count = 0
    for jar_path in jars:
        backup = jar_path + ".bak"
        if refresh_backup or not os.path.exists(backup):
            shutil.copyfile(jar_path, backup)
        elif os.path.getmtime(jar_path) > os.path.getmtime(backup):
            shutil.copyfile(jar_path, backup)
        tmp = jar_path + ".tmp"
        try:
            patched = False
            with zipfile.ZipFile(backup, "r") as rj:
                if class_name not in rj.namelist():
                    continue
                with zipfile.ZipFile(tmp, "w") as wj:
                    for item in rj.infolist():
                        data = rj.read(item.filename)
                        if item.filename == class_name:
                            data, changed = patch_fn(data, jar_path)
                            patched = patched or changed
                        wj.writestr(item, data)
            if patched:
                shutil.move(tmp, jar_path)
                patched_count += 1
                if log:
                    log(f"[PATCH] {log_label} ← {jar_path}")
            elif os.path.exists(tmp):
                os.remove(tmp)
        except Exception as exc:
            if os.path.exists(tmp):
                os.remove(tmp)
            if log:
                log(f"[PATCH] {log_label} ошибка {jar_path}: {exc}")
    return patched_count
