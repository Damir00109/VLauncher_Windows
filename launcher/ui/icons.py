from pathlib import Path
import sys

from PyQt6.QtGui import QIcon

from launcher.config import APP_NAME, BASE_DIR

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
APP_ICON_PATH = BASE_DIR / "logo.ico"


def load_svg_icon(name: str) -> QIcon:
    path = ASSETS_DIR / name
    if not path.is_file():
        return QIcon()
    return QIcon(str(path))


def load_app_icon() -> QIcon:
    if APP_ICON_PATH.is_file():
        return QIcon(str(APP_ICON_PATH))
    return QIcon()


def prepare_platform_app_icon() -> None:
    if sys.platform != "win32":
        return
    import ctypes

    app_id = f"UnderworldMC.{APP_NAME}"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

