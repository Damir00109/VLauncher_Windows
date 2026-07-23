from pathlib import Path
import sys
from typing import Iterable, Optional

from PyQt6.QtGui import QIcon

from launcher.config import APP_NAME, BASE_DIR, install_dir

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def _candidate_icon_paths() -> Iterable[Path]:
    names = ("logo.ico", "logo.png")
    # 1) Bundled with the UI package (works for source + PyInstaller extract dir)
    for name in names:
        yield ASSETS_DIR / name
    # 2) Next to the exe / project root / data dir (user override)
    for name in names:
        yield install_dir() / name
        yield BASE_DIR / name
    # 3) PyInstaller onefile unpack root
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        root = Path(meipass)
        for name in names:
            yield root / "launcher" / "ui" / "assets" / name
            yield root / name


def resolve_app_icon_path() -> Optional[Path]:
    for path in _candidate_icon_paths():
        try:
            if path.is_file():
                return path
        except OSError:
            continue
    return None


def load_svg_icon(name: str) -> QIcon:
    path = ASSETS_DIR / name
    if not path.is_file():
        return QIcon()
    return QIcon(str(path))


def load_app_icon() -> QIcon:
    path = resolve_app_icon_path()
    if path is None:
        return QIcon()
    return QIcon(str(path))


def prepare_platform_app_icon() -> None:
    if sys.platform != "win32":
        return
    import ctypes

    app_id = f"UnderworldMC.{APP_NAME}"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
