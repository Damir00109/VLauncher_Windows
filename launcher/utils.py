import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def make_install_callback(
    log: Callable[[str], None],
    on_status: Callable[[str], None],
    on_max: Callable[[int], None],
    on_progress: Callable[[int], None],
) -> Dict[str, Callable]:
    return {
        "setStatus": lambda s: (log(f"[INSTALL] {s}"), on_status(str(s))),
        "setMax": on_max,
        "setProgress": on_progress,
    }


def reveal_path(path: Path) -> None:
    target = path.resolve()
    target.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        os.startfile(target)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(target)], check=False)
    else:
        subprocess.run(["xdg-open", str(target)], check=False)
