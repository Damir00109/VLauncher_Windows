import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Callable, Optional

import httpx

from launcher.config import PORTABLE_GIT_DIR, TOOLS_DIR

# MinGit — портативный Git for Windows без GUI.
GIT_RELEASE = "2.47.1.windows.1"
GIT_VERSION = "2.47.1"
MINGWIT_URL = (
    f"https://github.com/git-for-windows/git/releases/download/v{GIT_RELEASE}/"
    f"MinGit-{GIT_VERSION}-64-bit.zip"
)


def _git_candidates() -> list[Path]:
    if sys.platform == "win32":
        return [
            PORTABLE_GIT_DIR / "cmd" / "git.exe",
            PORTABLE_GIT_DIR / "mingw64" / "bin" / "git.exe",
        ]
    return [
        PORTABLE_GIT_DIR / "bin" / "git",
        PORTABLE_GIT_DIR / "cmd" / "git",
    ]


def find_portable_git() -> Optional[Path]:
    for path in _git_candidates():
        if path.is_file():
            return path
    return None


def find_system_git() -> Optional[Path]:
    which = shutil.which("git")
    if not which:
        return None
    path = Path(which)
    if not path.is_file():
        return None
    try:
        result = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return path
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def find_git_executable() -> Optional[Path]:
    portable = find_portable_git()
    if portable:
        return portable
    return find_system_git()


def portable_git_ready() -> bool:
    return find_git_executable() is not None


def _log(log: Optional[Callable[[str], None]], message: str) -> None:
    if log:
        log(message)


def _extract_zip(archive: Path, dest: Path) -> None:
    with zipfile.ZipFile(archive, "r") as zf:
        zf.extractall(dest)


def _missing_git_message() -> str:
    if sys.platform == "darwin":
        return "Git не найден. Установите: brew install git"
    if sys.platform == "win32":
        return "Git не найден. Перезапустите лаунчер для автоустановки MinGit"
    return "Git не найден. Установите: sudo apt install git (или git из пакетного менеджера)"


def install_portable_git(
    log: Optional[Callable[[str], None]] = None,
    force: bool = False,
) -> Path:
    """Скачивает и распаковывает MinGit в tools/git/ (только Windows)."""
    existing = find_portable_git()
    if existing and not force:
        return existing

    if sys.platform != "win32":
        raise RuntimeError(_missing_git_message())

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if force and PORTABLE_GIT_DIR.exists():
        shutil.rmtree(PORTABLE_GIT_DIR)
    PORTABLE_GIT_DIR.mkdir(parents=True, exist_ok=True)

    archive = TOOLS_DIR / f"MinGit-{GIT_VERSION}-64-bit.zip"
    _log(log, f"[GIT] Загрузка MinGit {GIT_VERSION}...")
    with httpx.stream("GET", MINGWIT_URL, follow_redirects=True, timeout=120) as response:
        response.raise_for_status()
        with archive.open("wb") as f:
            for chunk in response.iter_bytes(65536):
                f.write(chunk)

    _log(log, f"[GIT] Распаковка → {PORTABLE_GIT_DIR}")
    _extract_zip(archive, PORTABLE_GIT_DIR)
    try:
        archive.unlink(missing_ok=True)
    except OSError:
        pass

    git_exe = find_portable_git()
    if not git_exe:
        raise RuntimeError("MinGit распакован, но git.exe не найден")
    _log(log, f"[GIT] Готово: {git_exe}")
    return git_exe


def ensure_portable_git(
    log: Optional[Callable[[str], None]] = None,
    *,
    install_if_missing: bool = True,
) -> Path:
    git_exe = find_git_executable()
    if git_exe:
        if log and git_exe == find_system_git():
            _log(log, f"[GIT] Используется системный git: {git_exe}")
        return git_exe
    if not install_if_missing:
        raise FileNotFoundError(_missing_git_message())
    if sys.platform == "win32":
        return install_portable_git(log=log)
    raise RuntimeError(_missing_git_message())
