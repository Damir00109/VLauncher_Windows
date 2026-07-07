from typing import Callable, Dict, List, Optional

from PyQt6.QtCore import Qt, QSize, QRectF, pyqtSignal
from PyQt6.QtGui import QFont, QPainterPath, QPixmap, QRegion
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from launcher.ui.icons import load_svg_icon
from launcher.ui.profile_background_layer import pixmap_cover
from launcher.ui.theme import ICON_BUTTON_STYLE

CARD_MIN_HEIGHT = 76
CARD_ICON_SIZE = 36
CARD_ICON_INNER = 18
CARD_RADIUS = 14


def _rounded_region(width: int, height: int, radius: int = CARD_RADIUS) -> QRegion:
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, width, height), radius, radius)
    return QRegion(path.toFillPolygon().toPolygon())


class ProfileCard(QFrame):
    selected_changed = pyqtSignal(object)
    packs_clicked = pyqtSignal(dict)

    def __init__(self, profile: Dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.profile = profile
        self._selected = False
        self._hovered = False
        self._show_background = True
        self._pixmap = QPixmap()
        self.setObjectName("profileCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(CARD_MIN_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._bg_label = QLabel(self)
        self._bg_label.hide()

        self._overlay = QLabel(self)
        self._overlay.hide()
        self._overlay.setStyleSheet(
            f"background:rgba(15,23,42,0.55);border-radius:{CARD_RADIUS}px;"
        )

        self._content = QWidget(self)
        self._content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QHBoxLayout(self._content)
        layout.setContentsMargins(14, 12, 12, 12)
        layout.setSpacing(12)

        info = QWidget()
        info.setCursor(Qt.CursorShape.PointingHandCursor)
        info.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        self._name_label = QLabel(str(profile.get("name", "Сборка")))
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setBold(True)
        self._name_label.setFont(name_font)
        self._name_label.setStyleSheet("color:#f4f7ff;background:transparent;")
        info_layout.addWidget(self._name_label)

        meta_parts = [
            str(profile.get("minecraftVersion", "")),
            str(profile.get("loader", "")),
        ]
        if not profile.get("built"):
            meta_parts.append("обновляется")
        self._meta_label = QLabel(" · ".join(part for part in meta_parts if part))
        self._meta_label.setStyleSheet("color:#c6d0e4;font-size:11px;background:transparent;")
        self._meta_label.setWordWrap(True)
        info_layout.addWidget(self._meta_label)
        layout.addWidget(info, stretch=1)

        actions = QHBoxLayout()
        actions.setSpacing(6)

        self.btn_packs = QPushButton()
        self.btn_packs.setStyleSheet(ICON_BUTTON_STYLE)
        self.btn_packs.setFixedSize(CARD_ICON_SIZE, CARD_ICON_SIZE)
        self.btn_packs.setIcon(load_svg_icon("folder.svg"))
        self.btn_packs.setIconSize(QSize(CARD_ICON_INNER, CARD_ICON_INNER))
        self.btn_packs.setToolTip("Паки, моды и память")
        self.btn_packs.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_packs.clicked.connect(lambda: self.packs_clicked.emit(self.profile))
        actions.addWidget(self.btn_packs)

        layout.addLayout(actions)
        self._apply_style()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.rect()
        self._bg_label.setGeometry(rect)
        self._overlay.setGeometry(rect)
        self._content.setGeometry(rect)
        if self.width() > 0 and self.height() > 0:
            clip = _rounded_region(self.width(), self.height())
            self._bg_label.setMask(clip)
            self._overlay.setMask(clip)
        self._update_bg_pixmap()

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style()
        super().leaveEvent(event)

    def _update_bg_pixmap(self) -> None:
        if self._pixmap.isNull() or self.width() <= 0 or self.height() <= 0:
            return
        self._bg_label.setPixmap(pixmap_cover(self._pixmap, self.width(), self.height()))

    def profile_id(self) -> str:
        return str(self.profile.get("id"))

    def set_background_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        if pixmap.isNull():
            self._bg_label.clear()
            self._bg_label.hide()
            self._overlay.hide()
            return
        self._update_bg_pixmap()
        self._refresh_background_visibility()

    def set_show_background(self, show: bool) -> None:
        self._show_background = show
        self._refresh_background_visibility()

    def _refresh_background_visibility(self) -> None:
        visible = self._show_background and not self._pixmap.isNull() and not self._selected
        self._bg_label.setVisible(visible)
        self._overlay.setVisible(visible)
        self._apply_style()

    def set_selected(self, selected: bool) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self._refresh_background_visibility()
        self._apply_style()

    def set_actions_enabled(self, enabled: bool) -> None:
        self.btn_packs.setEnabled(enabled)

    def _apply_style(self) -> None:
        radius = CARD_RADIUS
        if self._selected:
            self.setStyleSheet(
                "#profileCard {"
                "background:transparent;"
                "border:1px solid rgba(124,92,255,0.55);"
                f"border-radius:{radius}px;"
                "}"
            )
            return

        has_bg = (
            self._show_background
            and not self._pixmap.isNull()
            and not self._selected
        )
        if self._hovered:
            bg = "transparent" if has_bg else "rgba(255,255,255,0.08)"
            border = "rgba(124,92,255,0.35)" if has_bg else "rgba(255,255,255,0.16)"
        else:
            bg = "transparent" if has_bg else "rgba(255,255,255,0.04)"
            border = "rgba(255,255,255,0.06)"

        self.setStyleSheet(
            "#profileCard {"
            f"background:{bg};"
            f"border:1px solid {border};"
            f"border-radius:{radius}px;"
            "}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            while child is not None and child is not self:
                if isinstance(child, QPushButton):
                    super().mousePressEvent(event)
                    return
                child = child.parent()
            if self._selected:
                event.accept()
                return
            self.selected_changed.emit(self.profile)
            event.accept()
            return
        super().mousePressEvent(event)


class ProfileCardsPanel(QWidget):
    selection_changed = pyqtSignal()

    def __init__(
        self,
        on_packs: Callable[[Dict], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._on_packs = on_packs
        self._cards: List[ProfileCard] = []
        self._selected_profile: Optional[Dict] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.status_label = QLabel("Сборки пока недоступны")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color:#8b97ad;background:transparent;padding:24px;")
        outer.addWidget(self.status_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVisible(False)

        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        self.list_layout.addStretch()
        self.scroll.setWidget(self.list_host)
        outer.addWidget(self.scroll, stretch=1)

    def card_for_id(self, profile_id: str) -> Optional[ProfileCard]:
        for card in self._cards:
            if card.profile_id() == profile_id:
                return card
        return None

    def _clear_cards(self) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._cards.clear()
        self._selected_profile = None

    def set_profiles(self, profiles: List[Dict]) -> None:
        self._clear_cards()
        if not profiles:
            self.scroll.setVisible(False)
            self.status_label.setText("Сборки пока недоступны — попробуйте позже")
            self.status_label.setVisible(True)
            return

        self.status_label.setVisible(False)
        self.scroll.setVisible(True)
        for profile in profiles:
            card = ProfileCard(profile, self.list_host)
            card.selected_changed.connect(self._on_card_selected)
            card.packs_clicked.connect(self._on_packs)
            self._cards.append(card)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)

        self.list_host.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._select_profile(profiles[0])

    def _on_card_selected(self, profile: Dict) -> None:
        if self._selected_profile and self._selected_profile.get("id") == profile.get("id"):
            return
        self._select_profile(profile)

    def _select_profile(self, profile: Dict) -> None:
        if self._selected_profile and self._selected_profile.get("id") == profile.get("id"):
            return
        self._selected_profile = profile
        selected_id = profile.get("id")
        for card in self._cards:
            card.set_selected(card.profile.get("id") == selected_id)
        self.selection_changed.emit()

    def selected_profile(self) -> Optional[Dict]:
        return self._selected_profile

    def set_actions_enabled(self, enabled: bool) -> None:
        for card in self._cards:
            card.set_actions_enabled(enabled)

    def clear(self) -> None:
        self._clear_cards()
        self.scroll.setVisible(False)
        self.status_label.setText("Войдите, чтобы видеть сборки")
        self.status_label.setVisible(True)
