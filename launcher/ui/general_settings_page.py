from typing import Callable, Optional

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from launcher.launcher_settings import get_keep_launcher_visible, set_keep_launcher_visible
from launcher.ui.theme import CHECKBOX_STYLE, GHOST_BUTTON_STYLE
from launcher.ui.widgets import create_panel


class GeneralSettingsPage(QWidget):
    def __init__(
        self,
        console: QTextEdit,
        on_back: Callable[[], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._on_back = on_back
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

        title = QLabel("Логи")
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet("color:#f4f7ff;background:transparent;")
        layout.addWidget(title)

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

        log_box, log_layout = create_panel()
        log_layout.addWidget(self.console)
        layout.addWidget(log_box, stretch=1)

    def append_log(self, text: str) -> None:
        self.console.append(text)
