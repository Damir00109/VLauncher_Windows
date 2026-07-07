from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from launcher.installed_packs import delete_installed_pack, list_installed_packs


class InstalledPacksList(QWidget):
    """Список установленных .zip в папке инстанса с кнопкой удаления."""

    def __init__(
        self,
        title: str,
        pack_subdir: str,
        log: Optional[Callable[[str], None]] = None,
        *,
        compact: bool = True,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.pack_subdir = pack_subdir
        self._log = log
        self._instance_dir: Optional[Path] = None
        self._base_title = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.title_label = QLabel(f"{title} (0)")
        self.title_label.setStyleSheet("color:#8b97ad;font-size:11px;background:transparent;")
        layout.addWidget(self.title_label)

        self.list_widget = QListWidget()
        if compact:
            self.list_widget.setMaximumHeight(88)
        else:
            self.list_widget.setMinimumHeight(160)
        self.list_widget.setToolTip("Установленные файлы")
        layout.addWidget(self.list_widget, stretch=0 if compact else 1)

        row = QHBoxLayout()
        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._delete_selected)
        row.addWidget(self.btn_delete)
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedWidth(36)
        self.btn_refresh.setToolTip("Обновить список")
        self.btn_refresh.clicked.connect(self.refresh)
        row.addWidget(self.btn_refresh)
        layout.addLayout(row)

        self.list_widget.currentItemChanged.connect(
            lambda *_: self.btn_delete.setEnabled(self.list_widget.currentItem() is not None)
        )

    def set_instance_dir(self, instance_dir: Optional[Path]) -> None:
        self._instance_dir = instance_dir
        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        self.btn_delete.setEnabled(False)

        if not self._instance_dir:
            self.title_label.setText(f"{self._base_title} (0)")
            return

        files = list_installed_packs(self._instance_dir, self.pack_subdir)
        self.title_label.setText(f"{self._base_title} ({len(files)})")

        if not files:
            self.list_widget.addItem("— пусто —")
            return

        for name in files:
            self.list_widget.addItem(name)

    def _delete_selected(self) -> None:
        if not self._instance_dir:
            return
        item = self.list_widget.currentItem()
        if not item:
            return
        filename = item.text()
        if filename == "— пусто —":
            return

        reply = QMessageBox.question(
            self.window(),
            "Удаление",
            f"Удалить файл?\n{filename}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            path = delete_installed_pack(self._instance_dir, self.pack_subdir, filename)
            if self._log:
                self._log(f"[PACKS] Удалён: {path.name}")
            self.refresh()
        except OSError as exc:
            QMessageBox.critical(self, "Удаление", f"Не удалось удалить файл:\n{exc}")
