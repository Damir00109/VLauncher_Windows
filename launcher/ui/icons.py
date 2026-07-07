from pathlib import Path

from PyQt6.QtGui import QIcon

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def load_svg_icon(name: str) -> QIcon:
    path = ASSETS_DIR / name
    if not path.is_file():
        return QIcon()
    return QIcon(str(path))
