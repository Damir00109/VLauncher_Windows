import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict

from launcher.config import install_dir, portable_conda_env


def is_frozen_app() -> bool:
    """True for PyInstaller / Nuitka / similar one-file or frozen builds."""
    return bool(getattr(sys, "frozen", False)) or hasattr(sys, "_MEIPASS")


def find_runtime_python() -> Path:
    """
    Interpreter for child Python processes (pip, Packs-Selector).

    When frozen, sys.executable is the launcher EXE — spawning it again opens
    another GUI and can fork-bomb. Prefer portable Conda, then system Python.
    """
    if not is_frozen_app():
        return Path(sys.executable)

    env_dirs = [
        portable_conda_env(),
        install_dir() / "tools" / "conda" / "envs" / "vlauncher",
    ]
    candidates: list[Path] = []
    if sys.platform == "win32":
        for env in env_dirs:
            candidates.extend([env / "python.exe", env / "pythonw.exe"])
    else:
        for env in env_dirs:
            candidates.append(env / "bin" / "python")

    for name in ("python", "python3"):
        which = shutil.which(name)
        if which:
            candidates.append(Path(which))

    frozen_exe = Path(sys.executable).resolve()
    seen: set[Path] = set()
    for path in candidates:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.is_file() or resolved == frozen_exe:
            continue
        seen.add(resolved)
        return resolved

    raise RuntimeError(
        "Для Packs-Selector нужен Python (tools\\conda\\envs\\vlauncher или python в PATH). "
        "Собранный .exe нельзя использовать как интерпретатор — это вызывает бесконечный запуск окон."
    )


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
