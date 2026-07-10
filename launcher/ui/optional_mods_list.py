from typing import Callable, Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from launcher.profile_settings import get_enabled_optional_mod_ids, set_enabled_optional_mod_ids
from launcher.ui.theme import CHECKBOX_STYLE


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
        self._checkboxes: Dict[str, QCheckBox] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.title_label = QLabel("Доступно (0)")
        self.title_label.setStyleSheet("color:#8b97ad;font-size:11px;background:transparent;")
        layout.addWidget(self.title_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setMinimumHeight(160)
        self.scroll_area.setStyleSheet(
            "QScrollArea { background: rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.06);"
            "border-radius: 10px; }"
        )

        self._mods_host = QWidget()
        self._mods_host.setStyleSheet("background: transparent;")
        self._mods_layout = QVBoxLayout(self._mods_host)
        self._mods_layout.setContentsMargins(4, 4, 4, 4)
        self._mods_layout.setSpacing(2)
        self.scroll_area.setWidget(self._mods_host)
        layout.addWidget(self.scroll_area, stretch=1)

        self.hint_label = QLabel("Моды добавляет сервер. Выберите, что установить при запуске.")
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color:#6b7a94;font-size:10px;background:transparent;")
        layout.addWidget(self.hint_label)

    def set_profile(self, profile_id: Optional[str], mods: List[Dict]) -> None:
        self._profile_id = profile_id
        self._mods = list(mods)
        self._refresh()

    def _clear_mod_rows(self) -> None:
        self._checkboxes.clear()
        while self._mods_layout.count():
            item = self._mods_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh(self) -> None:
        self._updating = True
        self._clear_mod_rows()

        if not self._profile_id or not self._mods:
            self.title_label.setText("Доступно (0)")
            placeholder = QLabel("— нет опциональных модов —")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color:#6b7a94;font-size:12px;background:transparent;padding:24px 8px;")
            self._mods_layout.addWidget(placeholder)
            self._updating = False
            return

        enabled = get_enabled_optional_mod_ids(self._profile_id, self._mods)
        self.title_label.setText(f"Доступно ({len(self._mods)})")

        for mod in self._mods:
            mod_id = str(mod.get("id") or "")
            name = str(mod.get("name") or mod_id)
            checkbox = QCheckBox(name)
            checkbox.setStyleSheet(CHECKBOX_STYLE)
            checkbox.setChecked(mod_id in enabled)
            description = str(mod.get("description") or "").strip()
            if description:
                checkbox.setToolTip(description)
            checkbox.toggled.connect(
                lambda checked, mid=mod_id, label=name: self._on_toggle(mid, label, checked)
            )
            self._mods_layout.addWidget(checkbox)
            self._checkboxes[mod_id] = checkbox

        self._mods_layout.addStretch(1)
        self._updating = False

    def _on_toggle(self, mod_id: str, label: str, checked: bool) -> None:
        if self._updating or not self._profile_id:
            return

        enabled_ids = sorted(mid for mid, checkbox in self._checkboxes.items() if checkbox.isChecked())
        set_enabled_optional_mod_ids(self._profile_id, enabled_ids)
        if self._log:
            state = "вкл." if checked else "выкл."
            self._log(f"[OPTS] {label}: {state}")
