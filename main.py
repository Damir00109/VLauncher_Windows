import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from launcher.config import APP_NAME
from launcher.subprocess_io import install_hidden_subprocess_patch
from launcher.ui.icons import load_app_icon, prepare_platform_app_icon
from launcher.ui.main_window import MainWindow
from launcher.ui.theme import APP_STYLESHEET


def main() -> int:
    prepare_platform_app_icon()
    install_hidden_subprocess_patch()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app_icon = load_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)
    window.show()
    exit_code = app.exec()
    window.shutdown_workers()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
