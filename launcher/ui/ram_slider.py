from typing import Optional

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QLinearGradient, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QVBoxLayout, QWidget

from launcher.system_ram import get_total_ram_mb

DANGER_ZONE_MB = 2048
MIN_RAM_MB = 1024
STEP_MB = 256

GROOVE_HEIGHT = 10
THUMB_RADIUS = 11
SIDE_MARGIN = 14

COLOR_GREEN = QColor("#16a34a")
COLOR_LIME = QColor("#65a30d")
COLOR_YELLOW = QColor("#ca8a04")
COLOR_ORANGE = QColor("#ea580c")
COLOR_RED = QColor("#dc2626")
COLOR_DARK_RED = QColor("#991b1b")
TRACK_BG = QColor(0, 0, 0, 70)


def _lerp_color(a: QColor, b: QColor, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
    )


def _color_for_ratio(ratio: float, danger_ratio: float) -> QColor:
    ratio = max(0.0, min(1.0, ratio))
    danger_ratio = max(0.01, min(0.99, danger_ratio))

    if ratio <= danger_ratio:
        local = ratio / danger_ratio
        if local < 0.5:
            return _lerp_color(COLOR_GREEN, COLOR_LIME, local * 2)
        return _lerp_color(COLOR_LIME, COLOR_ORANGE, (local - 0.5) * 2)

    local = (ratio - danger_ratio) / (1.0 - danger_ratio)
    if local < 0.45:
        return _lerp_color(COLOR_ORANGE, COLOR_RED, local / 0.45)
    return _lerp_color(COLOR_RED, COLOR_DARK_RED, (local - 0.45) / 0.55)


class RamGradientSlider(QWidget):
    valueChanged = pyqtSignal(int)
    sliderReleased = pyqtSignal()

    def __init__(
        self,
        min_mb: int,
        max_mb: int,
        danger_from_mb: int,
        value: int,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._min_mb = min_mb
        self._max_mb = max_mb
        self._danger_from_mb = danger_from_mb
        self._value = value
        self._dragging = False
        self.setMinimumHeight(THUMB_RADIUS * 2 + 8)
        self.setMouseTracking(True)

    def value(self) -> int:
        return self._value

    def setValue(self, mb: int) -> None:
        mb = self._snap(mb)
        if mb == self._value:
            return
        self._value = mb
        self.update()
        self.valueChanged.emit(mb)

    def _snap(self, mb: float) -> int:
        snapped = round(mb / STEP_MB) * STEP_MB
        return int(max(self._min_mb, min(self._max_mb, snapped)))

    def _danger_ratio(self) -> float:
        span = self._max_mb - self._min_mb
        if span <= 0:
            return 1.0
        return (self._danger_from_mb - self._min_mb) / span

    def _groove_rect(self) -> QRectF:
        y = (self.height() - GROOVE_HEIGHT) / 2
        return QRectF(SIDE_MARGIN, y, max(1.0, self.width() - SIDE_MARGIN * 2), GROOVE_HEIGHT)

    def _ratio_for_value(self, mb: int) -> float:
        span = self._max_mb - self._min_mb
        if span <= 0:
            return 0.0
        return (mb - self._min_mb) / span

    def _value_for_x(self, x: float) -> int:
        groove = self._groove_rect()
        if groove.width() <= 0:
            return self._min_mb
        ratio = (x - groove.left()) / groove.width()
        mb = self._min_mb + ratio * (self._max_mb - self._min_mb)
        return self._snap(mb)

    def _thumb_center(self) -> QPointF:
        groove = self._groove_rect()
        ratio = self._ratio_for_value(self._value)
        return QPointF(groove.left() + ratio * groove.width(), self.height() / 2)

    def _track_gradient(self, groove: QRectF) -> QLinearGradient:
        danger_ratio = self._danger_ratio()
        grad = QLinearGradient(groove.left(), 0, groove.right(), 0)
        grad.setColorAt(0.0, COLOR_GREEN)
        grad.setColorAt(danger_ratio * 0.35, COLOR_LIME)
        grad.setColorAt(danger_ratio * 0.7, COLOR_YELLOW)
        grad.setColorAt(danger_ratio, COLOR_ORANGE)
        edge = min(1.0, danger_ratio + 0.02)
        grad.setColorAt(edge, COLOR_RED)
        grad.setColorAt(1.0, COLOR_DARK_RED)
        return grad

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        groove = self._groove_rect()
        thumb = self._thumb_center()
        fill_right = max(groove.left(), thumb.x())

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(TRACK_BG)
        painter.drawRoundedRect(groove, GROOVE_HEIGHT / 2, GROOVE_HEIGHT / 2)

        fill_rect = QRectF(groove.left(), groove.top(), fill_right - groove.left(), groove.height())
        if fill_rect.width() > 0.5:
            painter.setClipRect(fill_rect)
            painter.setBrush(self._track_gradient(groove))
            painter.drawRoundedRect(groove, GROOVE_HEIGHT / 2, GROOVE_HEIGHT / 2)
            painter.setClipping(False)

        ratio = self._ratio_for_value(self._value)
        thumb_color = _color_for_ratio(ratio, self._danger_ratio())

        painter.setPen(QPen(thumb_color.darker(115), 2))
        painter.setBrush(QColor("#f4f7ff"))
        painter.drawEllipse(thumb, THUMB_RADIUS, THUMB_RADIUS)

        inner = THUMB_RADIUS - 4
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(thumb_color)
        painter.drawEllipse(thumb, inner, inner)
        painter.end()

    def _set_from_mouse(self, event: QMouseEvent) -> None:
        self.setValue(self._value_for_x(event.position().x()))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._set_from_mouse(event)
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self._set_from_mouse(event)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.sliderReleased.emit()
            event.accept()


class RamSliderWidget(QWidget):
    value_changed = pyqtSignal(int)

    def __init__(self, default_mb: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._max_mb = get_total_ram_mb()
        self._danger_from_mb = max(MIN_RAM_MB, self._max_mb - DANGER_ZONE_MB)
        self._warned_in_session = False
        self._in_danger = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.value_label = QLabel()
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.value_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.value_label.setFont(font)
        layout.addWidget(self.value_label)

        row = QHBoxLayout()
        min_label = QLabel(f"{MIN_RAM_MB} МБ")
        min_label.setStyleSheet("color:#8b97ad;background:transparent;")
        row.addWidget(min_label)
        initial = max(MIN_RAM_MB, min(default_mb, self._max_mb))
        self.slider = RamGradientSlider(
            MIN_RAM_MB,
            self._max_mb,
            self._danger_from_mb,
            initial,
            self,
        )
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.sliderReleased.connect(self._on_released)
        row.addWidget(self.slider, stretch=1)
        max_label = QLabel(f"{self._max_mb} МБ")
        max_label.setStyleSheet("color:#8b97ad;background:transparent;")
        row.addWidget(max_label)
        layout.addLayout(row)

        self._update_label(initial)

    def value(self) -> int:
        return self.slider.value()

    def set_value(self, mb: int) -> None:
        mb = max(MIN_RAM_MB, min(int(mb), self._max_mb))
        self.slider.blockSignals(True)
        self.slider.setValue(mb)
        self.slider.blockSignals(False)
        self._update_label(mb)
        self._in_danger = mb >= self._danger_from_mb

    def _danger_ratio(self) -> float:
        span = self._max_mb - MIN_RAM_MB
        if span <= 0:
            return 1.0
        return (self._danger_from_mb - MIN_RAM_MB) / span

    def _update_label(self, mb: int):
        gb = mb / 1024
        ratio = (mb - MIN_RAM_MB) / max(1, self._max_mb - MIN_RAM_MB)
        color = _color_for_ratio(ratio, self._danger_ratio())
        weight = "bold" if mb >= self._danger_from_mb else "600"
        self.value_label.setText(f"{mb} МБ  ({gb:.1f} ГБ)")
        self.value_label.setStyleSheet(f"color:{color.name()};font-weight:{weight}")

    def _on_value_changed(self, value: int):
        self._update_label(value)
        in_danger = value >= self._danger_from_mb
        if in_danger and not self._in_danger:
            self._show_danger_warning(value)
        self._in_danger = in_danger
        self.value_changed.emit(value)

    def _on_released(self):
        if self.slider.value() >= self._danger_from_mb:
            self._show_danger_warning(self.slider.value())

    def _show_danger_warning(self, value: int):
        if self._warned_in_session:
            return
        self._warned_in_session = True
        QMessageBox.warning(
            self.window(),
            "Много оперативной памяти",
            f"Выделено {value} МБ — это попадает в последние 2 ГБ системной памяти.\n\n"
            "Windows и другие программы могут не хватать RAM, из‑за чего игра или система "
            "станут работать нестабильно.",
        )
