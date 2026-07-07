import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from launcher.config import APP_NAME, BASE_DIR
from launcher.ui.main_window import MainWindow
from launcher.ui.theme import APP_STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    icon_path = BASE_DIR / "logo.ico"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    exit_code = app.exec()
    window.shutdown_workers()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
