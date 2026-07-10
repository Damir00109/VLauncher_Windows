import sys
from typing import Optional

from PyQt6.QtCore import QEvent, QObject, QPoint, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QMouseEvent, QPainter, QPainterPath
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from launcher.ui.icons import load_svg_icon

SHELL_RADIUS = 18
SHELL_MARGIN = 10
TITLE_BAR_HEIGHT = 50
CONTROL_SIZE = 34


class ChromeIconButton(QPushButton):
    def __init__(self, parent: Optional[QWidget] = None, *, danger: bool = False):
        super().__init__(parent)
        self._danger = danger
        self.setFixedSize(CONTROL_SIZE, CONTROL_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._apply_style(hovered=False)

    def _apply_style(self, hovered: bool) -> None:
        if self._danger and hovered:
            bg = "#e5484d"
            border = "#ff6b6b"
        elif hovered:
            bg = "rgba(255,255,255,0.12)"
            border = "rgba(255,255,255,0.18)"
        else:
            bg = "rgba(255,255,255,0.05)"
            border = "rgba(255,255,255,0.08)"
        self.setStyleSheet(
            f"QPushButton {{ background:{bg}; border:1px solid {border}; border-radius:10px;"
            f"padding:0; color:#eef2ff; }}"
            f"QPushButton:disabled {{ background:rgba(255,255,255,0.03); border-color:rgba(255,255,255,0.05); }}"
        )

    def enterEvent(self, event):
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)


class WindowControlButton(ChromeIconButton):
    def __init__(self, icon_name: str, *, danger: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent, danger=danger)
        self.setIcon(load_svg_icon(icon_name))
        self.setIconSize(QSize(int(CONTROL_SIZE * 0.45), int(CONTROL_SIZE * 0.45)))


class ChromeTextButton(QPushButton):
    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setFixedHeight(CONTROL_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        font = QFont()
        font.setPointSize(10)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)
        self._apply_style(hovered=False)

    def _apply_style(self, hovered: bool) -> None:
        if hovered:
            bg = "rgba(255, 255, 255, 0.12)"
            border = "rgba(255, 255, 255, 0.18)"
        else:
            bg = "rgba(255, 255, 255, 0.05)"
            border = "rgba(255, 255, 255, 0.08)"
        self.setStyleSheet(
            f"QPushButton {{ background:{bg}; border:1px solid {border}; border-radius:10px;"
            f"padding: 3px 12px; color:#eef2ff; }}"
        )

    def enterEvent(self, event):
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)


class ChromeBackButton(ChromeTextButton):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("← Назад", parent)


class ProfileChipButton(QPushButton):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(CONTROL_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        font = QFont()
        font.setPointSize(10)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)
        self.setIconSize(QSize(26, 26))
        self._apply_style(hovered=False)

    def _apply_style(self, hovered: bool) -> None:
        if hovered:
            bg = "rgba(255, 255, 255, 0.12)"
            border = "rgba(255, 255, 255, 0.18)"
        else:
            bg = "rgba(255, 255, 255, 0.05)"
            border = "rgba(255, 255, 255, 0.08)"
        self.setStyleSheet(
            f"QPushButton {{ background:{bg}; border:1px solid {border}; border-radius:10px;"
            f"padding: 3px 10px 3px 6px; color:#eef2ff; }}"
        )

    def enterEvent(self, event):
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)

class TitleBar(QWidget):
    minimize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()
    back_clicked = pyqtSignal()

    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drag_offset: Optional[QPoint] = None
        self.setFixedHeight(TITLE_BAR_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 12, 8)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._left_slot = QWidget()
        self._left_slot.setFixedHeight(CONTROL_SIZE)
        left_layout = QHBoxLayout(self._left_slot)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.btn_back = ChromeBackButton(self._left_slot)
        self.btn_back.setVisible(False)
        self.btn_back.clicked.connect(self.back_clicked.emit)
        left_layout.addWidget(self.btn_back)
        left_layout.addStretch(1)
        layout.addWidget(self._left_slot, stretch=1)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setMinimumHeight(CONTROL_SIZE)
        self.title_label.setStyleSheet(
            "color:#eef2ff;font-size:14px;font-weight:700;letter-spacing:0.3px;"
            "background:transparent;padding:0;margin:0;"
        )
        layout.addWidget(self.title_label, stretch=0, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._right_slot = QWidget()
        self._right_slot.setFixedHeight(CONTROL_SIZE)
        right_layout = QHBoxLayout(self._right_slot)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right_layout.addStretch(1)

        self.trailing_layout = QHBoxLayout()
        self.trailing_layout.setSpacing(6)
        right_layout.addLayout(self.trailing_layout)

        self.btn_minimize = WindowControlButton("minimize.svg", parent=self)
        self.btn_minimize.clicked.connect(self.minimize_clicked.emit)
        right_layout.addWidget(self.btn_minimize)

        self.btn_close = WindowControlButton("close.svg", danger=True, parent=self)
        self.btn_close.clicked.connect(self.close_clicked.emit)
        right_layout.addWidget(self.btn_close)
        layout.addWidget(self._right_slot, stretch=1)

        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        for slot in (self._left_slot, self._right_slot):
            slot.installEventFilter(self)

    def set_back_visible(self, visible: bool) -> None:
        self.btn_back.setVisible(visible)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def add_trailing_widget(self, widget: QWidget) -> None:
        self.trailing_layout.addWidget(widget)

    def _slot_child_at(self, slot: QWidget, event: QMouseEvent) -> Optional[QWidget]:
        local_pos = event.position().toPoint()
        child = slot.childAt(local_pos)
        if child is not None:
            return child
        return slot.childAt(local_pos.x(), local_pos.y())

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched not in (self._left_slot, self._right_slot):
            return super().eventFilter(watched, event)

        if not isinstance(event, QMouseEvent):
            return super().eventFilter(watched, event)

        slot = watched
        if not isinstance(slot, QWidget):
            return super().eventFilter(watched, event)

        if self._slot_child_at(slot, event) is not None:
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            if self._begin_window_drag(event):
                return True

        if event.type() == QEvent.Type.MouseButtonDblClick and event.button() == Qt.MouseButton.LeftButton:
            self.minimize_clicked.emit()
            return True

        return super().eventFilter(watched, event)

    def _begin_window_drag(self, event: QMouseEvent) -> bool:
        window = self.window()
        if window is None:
            return False

        handle = window.windowHandle()
        if handle is not None:
            try:
                if handle.startSystemMove():
                    return True
            except RuntimeError:
                pass

        if sys.platform == "win32":
            self._drag_offset = event.globalPosition().toPoint() - window.frameGeometry().topLeft()
            return True

        if sys.platform.startswith("linux"):
            global_pos = event.globalPosition().toPoint()
            self._drag_offset = global_pos - window.frameGeometry().topLeft()
            return True

        return False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._begin_window_drag(event):
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            window = self.window()
            if window:
                window.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.minimize_clicked.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class LauncherFrame(QWidget):
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 110))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_bar = TitleBar(title, self)
        layout.addWidget(self.title_bar)

        self.content_host = QWidget()
        self.content_host.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.content_layout = QVBoxLayout(self.content_host)
        self.content_layout.setContentsMargins(16, 8, 16, 16)
        self.content_layout.setSpacing(0)
        layout.addWidget(self.content_host, stretch=1)

    def set_content(self, widget: QWidget) -> None:
        self.content_layout.addWidget(widget)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(
            float(rect.x()),
            float(rect.y()),
            float(rect.width()),
            float(rect.height()),
            SHELL_RADIUS,
            SHELL_RADIUS,
        )
        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        gradient.setColorAt(0.0, QColor("#252d42"))
        gradient.setColorAt(0.5, QColor("#1b2130"))
        gradient.setColorAt(1.0, QColor("#131720"))
        painter.fillPath(path, gradient)
        painter.setPen(QColor(255, 255, 255, 24))
        painter.drawPath(path)
        painter.end()


class LauncherShell(QWidget):
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(SHELL_MARGIN, SHELL_MARGIN, SHELL_MARGIN, SHELL_MARGIN)
        self.frame = LauncherFrame(title, self)
        outer.addWidget(self.frame)

    @property
    def title_bar(self) -> TitleBar:
        return self.frame.title_bar

    def set_content(self, widget: QWidget) -> None:
        self.frame.set_content(widget)
