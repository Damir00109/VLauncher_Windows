from typing import Dict, List, Optional

from PyQt6.QtCore import QEasingCurve, QEvent, QObject, QPoint, QPropertyAnimation, QRect, QSize, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QWidget

from launcher.ui.window_shell import SHELL_RADIUS
from launcher.workers import ImageLoadWorker

OVERLAY_ALPHA = 165
ANIM_MS = 380


def pixmap_cover(pixmap: QPixmap, width: int, height: int) -> QPixmap:
    if pixmap.isNull() or width <= 0 or height <= 0:
        return QPixmap()
    scaled = pixmap.scaled(
        width,
        height,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    x = max(0, (scaled.width() - width) // 2)
    y = max(0, (scaled.height() - height) // 2)
    return scaled.copy(x, y, width, height)


class _BackgroundPaintWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._source = QPixmap()
        self._cached = QPixmap()
        self._cached_size = QSize()
        self._paint_opacity = 1.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def get_paint_opacity(self) -> float:
        return self._paint_opacity

    def set_paint_opacity(self, value: float) -> None:
        self._paint_opacity = max(0.0, min(1.0, float(value)))
        self.update()

    paint_opacity = pyqtProperty(float, get_paint_opacity, set_paint_opacity)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._source = pixmap
        self._invalidate_cache()
        self.update()

    def _invalidate_cache(self) -> None:
        self._cached = QPixmap()
        self._cached_size = QSize()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._invalidate_cache()

    def _scaled_pixmap(self) -> QPixmap:
        if self._source.isNull() or self.width() <= 0 or self.height() <= 0:
            return QPixmap()
        size = self.size()
        if self._cached_size == size and not self._cached.isNull():
            return self._cached
        self._cached = pixmap_cover(self._source, size.width(), size.height())
        self._cached_size = size
        return self._cached

    def paintEvent(self, event) -> None:
        scaled = self._scaled_pixmap()
        if scaled.isNull() or self._paint_opacity <= 0.0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        clip = QPainterPath()
        clip.addRoundedRect(
            float(rect.x()),
            float(rect.y()),
            float(rect.width()),
            float(rect.height()),
            SHELL_RADIUS,
            SHELL_RADIUS,
        )
        painter.setClipPath(clip)
        painter.setOpacity(self._paint_opacity)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(0, 0, scaled)
        overlay = int(OVERLAY_ALPHA * self._paint_opacity)
        painter.fillRect(self.rect(), QColor(15, 23, 42, overlay))
        painter.end()


class ProfileBackgroundController(QObject):
    def __init__(self, host: QWidget, content_layer: QWidget, title_bar: QWidget):
        super().__init__(host)
        self._host = host
        self._content = content_layer
        self._title_bar = title_bar
        self._cards_panel = None
        self._cache: Dict[str, QPixmap] = {}
        self._workers: List[ImageLoadWorker] = []
        self._selected_id: Optional[str] = None
        self._anim: Optional[QPropertyAnimation] = None
        self._viewport_active = False
        self._animating = False

        self._fullscreen = _BackgroundPaintWidget(host)
        self._fullscreen.hide()

        host.installEventFilter(self)
        self._sync_geometry()

    def set_viewport_active(self, active: bool) -> None:
        self._viewport_active = active
        if active:
            self.sync_selection(animate=False)
        else:
            self._hide_fullscreen()

    def _place_below_ui(self) -> None:
        self._fullscreen.stackUnder(self._content)
        self._content.raise_()
        self._title_bar.raise_()

    def attach_cards_panel(self, panel) -> None:
        self._cards_panel = panel
        panel.selection_changed.connect(self._on_selection)

    def eventFilter(self, obj, event) -> bool:
        if obj is self._host and event.type() == QEvent.Type.Resize:
            self._sync_geometry()
        return False

    def _sync_geometry(self) -> None:
        if not self._animating and self._fullscreen.isVisible():
            self._fullscreen.setGeometry(self._host.rect())
        if not self._animating:
            self._place_below_ui()

    def preload_backgrounds(self, profiles: List[Dict]) -> None:
        self._retire_workers()
        for profile in profiles:
            url = str(profile.get("backgroundUrl") or "").strip()
            if not url:
                continue
            profile_id = str(profile.get("id"))
            if url in self._cache and not self._cache[url].isNull():
                self._apply_pixmap_to_card(profile_id, self._cache[url])
                continue
            worker = ImageLoadWorker(url, self._host)
            worker.ready_signal.connect(
                lambda pixmap, u=url, pid=profile_id: self._on_image_ready(u, pid, pixmap)
            )
            worker.finished.connect(worker.deleteLater)
            self._workers.append(worker)
            worker.start()

    def _retire_workers(self) -> None:
        for worker in self._workers:
            try:
                if worker.isRunning():
                    worker.requestInterruption()
            except RuntimeError:
                pass
        self._workers.clear()

    def _on_image_ready(self, url: str, profile_id: str, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return
        self._cache[url] = pixmap
        self._apply_pixmap_to_card(profile_id, pixmap)
        if self._selected_id == profile_id and self._viewport_active:
            self.sync_selection(animate=not self._fullscreen.isVisible())

    def _apply_pixmap_to_card(self, profile_id: str, pixmap: QPixmap) -> None:
        if not self._cards_panel:
            return
        card = self._cards_panel.card_for_id(profile_id)
        if card:
            card.set_background_pixmap(pixmap)

    def clear(self) -> None:
        self._retire_workers()
        self._cache.clear()
        self._selected_id = None
        self._hide_fullscreen()

    def sync_selection(self, animate: bool = True) -> None:
        self._on_selection(animate=animate)

    def _on_selection(self, animate: bool = True) -> None:
        if not self._cards_panel:
            return
        profile = self._cards_panel.selected_profile()
        if not profile:
            self._hide_fullscreen()
            self._selected_id = None
            return

        profile_id = str(profile.get("id"))
        url = str(profile.get("backgroundUrl") or "").strip()
        card = self._cards_panel.card_for_id(profile_id)
        pixmap = self._cache.get(url) if url else None

        previous_id = self._selected_id
        if profile_id == previous_id and self._fullscreen.isVisible() and not self._animating:
            return

        if previous_id and previous_id != profile_id:
            prev_card = self._cards_panel.card_for_id(previous_id)
            if prev_card:
                prev_card.set_show_background(True)

        self._selected_id = profile_id

        if card and pixmap and not pixmap.isNull():
            card.set_background_pixmap(pixmap)
        elif card:
            card.set_show_background(bool(url))

        if not self._viewport_active or not url or pixmap is None or pixmap.isNull():
            self._hide_fullscreen()
            if card:
                card.set_show_background(bool(url))
            return

        if animate and card is not None:
            self._expand_from_card(card, pixmap)
            return

        if card:
            card.set_show_background(False)
        self._show_fullscreen(pixmap)

    def _card_rect_in_host(self, card: QWidget) -> QRect:
        top_left = card.mapTo(self._host, QPoint(0, 0))
        return QRect(top_left, card.size())

    def _expand_from_card(self, card: QWidget, pixmap: QPixmap) -> None:
        if self._anim:
            self._anim.stop()
            self._anim = None

        card.set_show_background(False)
        self._animating = True

        start_rect = self._card_rect_in_host(card)
        end_rect = self._host.rect()

        self._fullscreen.set_pixmap(pixmap)
        self._fullscreen.set_paint_opacity(1.0)
        self._fullscreen.setGeometry(start_rect)
        self._place_below_ui()
        self._fullscreen.show()

        anim = QPropertyAnimation(self._fullscreen, b"geometry", self._host)
        anim.setDuration(ANIM_MS)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(start_rect)
        anim.setEndValue(end_rect)

        def _finish() -> None:
            self._animating = False
            self._fullscreen.setGeometry(self._host.rect())
            self._fullscreen.set_paint_opacity(1.0)
            self._place_below_ui()
            self._anim = None

        anim.finished.connect(_finish)
        self._anim = anim
        anim.start()

    def _show_fullscreen(self, pixmap: QPixmap) -> None:
        if self._anim:
            self._anim.stop()
            self._anim = None
        self._animating = False
        self._fullscreen.set_pixmap(pixmap)
        self._fullscreen.set_paint_opacity(1.0)
        self._fullscreen.setGeometry(self._host.rect())
        self._fullscreen.show()
        self._place_below_ui()

    def _hide_fullscreen(self) -> None:
        if self._anim:
            self._anim.stop()
            self._anim = None
        self._animating = False
        self._fullscreen.set_paint_opacity(1.0)
        self._fullscreen.hide()
