from pathlib import Path
from typing import Callable, Dict, List, Optional

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from launcher.profile_settings import get_ram_mb, set_ram_mb
from launcher.ui.installed_packs_list import InstalledPacksList
from launcher.ui.optional_mods_list import OptionalModsList
from launcher.ui.ram_slider import RamSliderWidget
from launcher.ui.theme import ACCENT_BUTTON_STYLE, GHOST_BUTTON_STYLE
from launcher.ui.widgets import create_panel
from launcher.utils import reveal_path


class PacksManagerPage(QWidget):
    def __init__(
        self,
        on_back: Callable[[], None],
        on_open_manager: Callable[[str], None],
        log: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._on_back = on_back
        self._on_open_manager = on_open_manager
        self._log = log
        self._profile: Optional[Dict] = None
        self._instance_dir: Optional[Path] = None
        self.ram_slider: Optional[RamSliderWidget] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.addStretch()
        self.btn_open_folder = QPushButton("Открыть папку")
        self.btn_open_folder.setStyleSheet(GHOST_BUTTON_STYLE)
        self.btn_open_folder.clicked.connect(self._open_instance_folder)
        top.addWidget(self.btn_open_folder)
        layout.addLayout(top)

        self.title_label = QLabel()
        title_font = self.title_label.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color:#f4f7ff;background:transparent;")
        layout.addWidget(self.title_label)

        ram_box, ram_layout = create_panel("Оперативная память")
        self._ram_container = QVBoxLayout()
        ram_layout.addLayout(self._ram_container)
        layout.addWidget(ram_box)

        columns = QHBoxLayout()
        columns.setSpacing(14)

        textures_box, textures_layout = create_panel("Текстуры")
        self.btn_textures_manager = QPushButton("Установить")
        self.btn_textures_manager.setMinimumHeight(42)
        self.btn_textures_manager.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.btn_textures_manager.clicked.connect(lambda: self._on_open_manager("resourcepack"))
        textures_layout.addWidget(self.btn_textures_manager)
        self.installed_textures = InstalledPacksList(
            "Установлено",
            "resourcepacks",
            log=self._log,
            compact=False,
        )
        textures_layout.addWidget(self.installed_textures, stretch=1)
        columns.addWidget(textures_box, stretch=1)

        shaders_box, shaders_layout = create_panel("Шейдеры")
        self.btn_shaders_manager = QPushButton("Установить")
        self.btn_shaders_manager.setMinimumHeight(42)
        self.btn_shaders_manager.setStyleSheet(ACCENT_BUTTON_STYLE)
        self.btn_shaders_manager.clicked.connect(lambda: self._on_open_manager("shader"))
        shaders_layout.addWidget(self.btn_shaders_manager)
        self.installed_shaders = InstalledPacksList(
            "Установлено",
            "shaderpacks",
            log=self._log,
            compact=False,
        )
        shaders_layout.addWidget(self.installed_shaders, stretch=1)
        columns.addWidget(shaders_box, stretch=1)

        mods_box, mods_layout = create_panel("Опциональные моды")
        self.optional_mods = OptionalModsList(log=self._log)
        mods_layout.addWidget(self.optional_mods, stretch=1)
        columns.addWidget(mods_box, stretch=1)

        layout.addLayout(columns, stretch=1)

    def open_for_profile(
        self,
        profile: Dict,
        instance_dir: Path,
        optional_mods: Optional[List[Dict]] = None,
    ) -> None:
        self._profile = profile
        self._instance_dir = instance_dir
        self.title_label.setText(str(profile.get("name", "Сборка")))
        profile_id = str(profile.get("id") or "")
        self._setup_ram_slider(profile_id, int(profile.get("ramMb", 2048)))
        self.optional_mods.set_profile(profile_id, optional_mods or [])
        self.refresh_lists()

    def _setup_ram_slider(self, profile_id: str, default_ram: int) -> None:
        while self._ram_container.count():
            item = self._ram_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        saved_ram = get_ram_mb(profile_id, default_ram)
        self.ram_slider = RamSliderWidget(saved_ram, self)
        self.ram_slider.value_changed.connect(
            lambda mb, pid=profile_id: set_ram_mb(pid, mb)
        )
        self._ram_container.addWidget(self.ram_slider)

    def refresh_lists(self) -> None:
        self.installed_textures.set_instance_dir(self._instance_dir)
        self.installed_shaders.set_instance_dir(self._instance_dir)

    def set_managers_enabled(self, enabled: bool) -> None:
        self.btn_textures_manager.setEnabled(enabled)
        self.btn_shaders_manager.setEnabled(enabled)
        self.btn_open_folder.setEnabled(enabled)

    def _open_instance_folder(self) -> None:
        if not self._instance_dir:
            return
        try:
            reveal_path(self._instance_dir)
        except OSError as exc:
            QMessageBox.critical(self, "Папка", f"Не удалось открыть папку:\n{exc}")
