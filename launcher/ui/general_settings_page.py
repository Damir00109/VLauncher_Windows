from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from launcher.config import (
    APP_VERSION,
    UPDATE_REPO_URL,
    data_dir,
    default_data_dir,
    reset_data_dir_to_default,
    set_data_dir,
)
from launcher.launcher_settings import get_keep_launcher_visible, set_keep_launcher_visible
from launcher.ui.theme import ACCENT_BUTTON_STYLE, CHECKBOX_STYLE, GHOST_BUTTON_STYLE
from launcher.ui.widgets import create_panel
from launcher.utils import reveal_path


class GeneralSettingsPage(QWidget):
    def __init__(
        self,
        console: QTextEdit,
        on_back: Callable[[], None],
        on_check_updates: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._on_back = on_back
        self._on_check_updates = on_check_updates
        self.console = console
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.addStretch()
        self.btn_clear = QPushButton("Очистить лог")
        self.btn_clear.setStyleSheet(GHOST_BUTTON_STYLE)
        self.btn_clear.clicked.connect(self.console.clear)
        top.addWidget(self.btn_clear)
        layout.addLayout(top)

        title = QLabel("Настройки")
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet("color:#f4f7ff;background:transparent;")
        layout.addWidget(title)

        path_box, path_layout = create_panel("Папка данных")
        path_hint = QLabel(
            "По умолчанию: %APPDATA%\\.mcvanilla — сюда пишутся .minecraft, "
            "instances, session и конфиги."
        )
        path_hint.setWordWrap(True)
        path_hint.setStyleSheet("color:#8b97ad;font-size:11px;background:transparent;")
        path_layout.addWidget(path_hint)

        self.path_edit = QLineEdit()
        self.path_edit.setText(str(data_dir()))
        self.path_edit.setMinimumHeight(40)
        path_layout.addWidget(self.path_edit)

        path_btns = QHBoxLayout()
        self.btn_browse = QPushButton("Обзор…")
        self.btn_browse.setStyleSheet(GHOST_BUTTON_STYLE)
        self.btn_browse.clicked.connect(self._browse_data_dir)
        path_btns.addWidget(self.btn_browse)

        self.btn_open_data = QPushButton("Открыть")
        self.btn_open_data.setStyleSheet(GHOST_BUTTON_STYLE)
        self.btn_open_data.clicked.connect(lambda: reveal_path(data_dir()))
        path_btns.addWidget(self.btn_open_data)

        self.btn_default_path = QPushButton("По умолчанию")
        self.btn_default_path.setStyleSheet(GHOST_BUTTON_STYLE)
        self.btn_default_path.clicked.connect(self._reset_data_dir)
        path_btns.addWidget(self.btn_default_path)

        self.btn_apply_path = QPushButton("Применить")
        self.btn_apply_path.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.btn_apply_path.clicked.connect(self._apply_data_dir)
        path_btns.addWidget(self.btn_apply_path)
        path_layout.addLayout(path_btns)
        layout.addWidget(path_box)

        options_box, options_layout = create_panel("Поведение")
        self.chk_keep_visible = QCheckBox("Не скрывать лаунчер при запуске игры")
        self.chk_keep_visible.setChecked(get_keep_launcher_visible())
        self.chk_keep_visible.setStyleSheet(CHECKBOX_STYLE)
        self.chk_keep_visible.toggled.connect(set_keep_launcher_visible)
        options_layout.addWidget(self.chk_keep_visible)
        hint = QLabel(
            "Если включено, лаунчер остаётся на экране: кнопка «Играть» "
            "меняется на «Запущено», справа появится кнопка остановки."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#8b97ad;font-size:11px;background:transparent;")
        options_layout.addWidget(hint)
        layout.addWidget(options_box)

        update_box, update_layout = create_panel("Обновления")
        self.version_label = QLabel(f"Версия: {APP_VERSION}")
        self.version_label.setStyleSheet("color:#e8edf7;background:transparent;")
        update_layout.addWidget(self.version_label)

        repo_label = QLabel(f'<a href="{UPDATE_REPO_URL}" style="color:#8eb6ff;">GitHub: VLauncher_Windows</a>')
        repo_label.setOpenExternalLinks(True)
        repo_label.setStyleSheet("background:transparent;")
        update_layout.addWidget(repo_label)

        self.btn_check_updates = QPushButton("Проверить обновления")
        self.btn_check_updates.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.btn_check_updates.setMinimumHeight(40)
        if self._on_check_updates:
            self.btn_check_updates.clicked.connect(self._on_check_updates)
        update_layout.addWidget(self.btn_check_updates)
        layout.addWidget(update_box)

        log_title = QLabel("Логи")
        log_font = QFont()
        log_font.setPointSize(14)
        log_font.setBold(True)
        log_title.setFont(log_font)
        log_title.setStyleSheet("color:#f4f7ff;background:transparent;")
        layout.addWidget(log_title)

        log_box, log_layout = create_panel()
        log_layout.addWidget(self.console)
        layout.addWidget(log_box, stretch=1)

    def refresh_path_field(self) -> None:
        self.path_edit.setText(str(data_dir()))

    def set_updates_busy(self, busy: bool) -> None:
        self.btn_check_updates.setEnabled(not busy)
        self.btn_check_updates.setText("Проверка…" if busy else "Проверить обновления")

    def _browse_data_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Папка данных лаунчера",
            self.path_edit.text().strip() or str(default_data_dir()),
        )
        if chosen:
            self.path_edit.setText(chosen)

    def _reset_data_dir(self) -> None:
        reply = QMessageBox.question(
            self,
            "Сброс пути",
            f"Вернуть путь по умолчанию?\n\n{default_data_dir()}\n\n"
            "Уже скачанные файлы в старой папке не переносятся автоматически.",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        reset_data_dir_to_default()
        self.refresh_path_field()
        self.console.append(f"[PATH] Данные: {data_dir()}")
        QMessageBox.information(
            self,
            "Путь сброшен",
            "Используется папка по умолчанию.\nРекомендуется перезапустить лаунчер.",
        )

    def _apply_data_dir(self) -> None:
        raw = self.path_edit.text().strip()
        if not raw:
            QMessageBox.warning(self, "Путь", "Укажите папку данных.")
            return
        target = Path(raw)
        reply = QMessageBox.question(
            self,
            "Смена папки данных",
            f"Сохранять данные здесь?\n\n{target}\n\n"
            "Сессия, .minecraft и instances будут читаться из новой папки.\n"
            "Рекомендуется перезапустить лаунчер после смены.",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            set_data_dir(target)
        except OSError as exc:
            QMessageBox.critical(self, "Путь", f"Не удалось применить путь:\n{exc}")
            return
        self.refresh_path_field()
        self.console.append(f"[PATH] Данные: {data_dir()}")
        QMessageBox.information(
            self,
            "Путь сохранён",
            "Новая папка данных применена.\nЛучше перезапустить лаунчер.",
        )

    def append_log(self, text: str) -> None:
        self.console.append(text)
