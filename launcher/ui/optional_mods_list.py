from typing import Callable, Dict, List, Optional, Set

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from launcher.profile_settings import get_enabled_optional_mod_ids, set_enabled_optional_mod_ids


class OptionalModsList(QWidget):
    """Список опциональных модов сервера с галочками."""

    def __init__(
        self,
        log: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._log = log
        self._profile_id: Optional[str] = None
        self._mods: List[Dict] = []
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.title_label = QLabel("Доступно (0)")
        self.title_label.setStyleSheet("color:#8b97ad;font-size:11px;background:transparent;")
        layout.addWidget(self.title_label)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(160)
        self.list_widget.setStyleSheet(
            "QListWidget { background: rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.06);"
            "border-radius: 10px; color: #eef2ff; }"
            "QListWidget::item { padding: 8px 10px; }"
            "QListWidget::item:hover { background: rgba(124,92,255,0.12); }"
        )
        self.list_widget.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list_widget, stretch=1)

        self.hint_label = QLabel("Моды добавляет сервер. Выберите, что установить при запуске.")
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color:#6b7a94;font-size:10px;background:transparent;")
        layout.addWidget(self.hint_label)

    def set_profile(self, profile_id: Optional[str], mods: List[Dict]) -> None:
        self._profile_id = profile_id
        self._mods = list(mods)
        self._refresh()

    def _refresh(self) -> None:
        self._updating = True
        self.list_widget.clear()

        if not self._profile_id or not self._mods:
            self.title_label.setText("Доступно (0)")
            item = QListWidgetItem("— нет опциональных модов —")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_widget.addItem(item)
            self._updating = False
            return

        enabled = get_enabled_optional_mod_ids(self._profile_id, self._mods)
        self.title_label.setText(f"Доступно ({len(self._mods)})")

        for mod in self._mods:
            mod_id = str(mod.get("id") or "")
            name = str(mod.get("name") or mod_id)
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, mod_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if mod_id in enabled else Qt.CheckState.Unchecked
            )
            description = str(mod.get("description") or "").strip()
            if description:
                item.setToolTip(description)
            self.list_widget.addItem(item)

        self._updating = False

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        if self._updating or not self._profile_id:
            return
        mod_id = item.data(Qt.ItemDataRole.UserRole)
        if not mod_id:
            return

        enabled_ids: Set[str] = set()
        for index in range(self.list_widget.count()):
            row = self.list_widget.item(index)
            row_id = row.data(Qt.ItemDataRole.UserRole)
            if row_id and row.checkState() == Qt.CheckState.Checked:
                enabled_ids.add(str(row_id))

        set_enabled_optional_mod_ids(self._profile_id, sorted(enabled_ids))
        if self._log:
            state = "вкл." if mod_id in enabled_ids else "выкл."
            self._log(f"[OPTS] {item.text()}: {state}")
