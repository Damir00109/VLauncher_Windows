from datetime import datetime
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from launcher.workers import NewsCoverWorker

HERO_HEIGHT = 160
HERO_RADIUS = 12


def _round_top_corners(pixmap: QPixmap, radius: int) -> QPixmap:
    if pixmap.isNull():
        return pixmap
    w = pixmap.width()
    h = pixmap.height()
    rounded = QPixmap(w, h)
    rounded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.moveTo(0, h)
    path.lineTo(0, radius)
    path.quadTo(0, 0, radius, 0)
    path.lineTo(w - radius, 0)
    path.quadTo(w, 0, w, radius)
    path.lineTo(w, h)
    path.closeSubpath()
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return rounded


def _format_date(raw: Optional[str]) -> str:
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y")
    except ValueError:
        return str(raw)[:10]


def _fit_text_browser_height(browser: QTextBrowser) -> None:
    browser.document().setTextWidth(max(1, browser.viewport().width()))
    height = int(browser.document().size().height()) + 8
    browser.setFixedHeight(max(48, height))


class HeroCover(QWidget):
    def __init__(self, title: str, date_text: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self.setFixedHeight(HERO_HEIGHT)

        self.cover_label = QLabel(self)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet(
            f"background:rgba(0,0,0,0.28);color:#7b879d;"
            f"border-top-left-radius:{HERO_RADIUS}px;"
            f"border-top-right-radius:{HERO_RADIUS}px;"
        )

        self.title_label = QLabel(title, self)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumWidth(260)
        self.title_label.setStyleSheet(
            "color:#ffffff;background:rgba(15,23,42,0.72);"
            "padding:8px 10px;border-radius:8px"
        )

        self.date_label = QLabel(date_text, self)
        date_font = QFont()
        date_font.setPointSize(10)
        self.date_label.setFont(date_font)
        self.date_label.setStyleSheet(
            "color:#ffffff;background:rgba(15,23,42,0.72);"
            "padding:6px 10px;border-radius:8px"
        )
        self.date_label.setVisible(bool(date_text))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.cover_label.setGeometry(0, 0, self.width(), self.height())
        self.title_label.move(12, 12)
        self.date_label.adjustSize()
        self.date_label.move(
            max(12, self.width() - self.date_label.width() - 12),
            12,
        )
        self._refresh_cover()

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self._refresh_cover()

    def _refresh_cover(self) -> None:
        if self._pixmap.isNull() or self.width() <= 0:
            self.cover_label.setPixmap(QPixmap())
            self.cover_label.setText("Нет обложки")
            return
        scaled = self._pixmap.scaled(
            self.width(),
            self.height(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        cropped = scaled.copy(
            (scaled.width() - self.width()) // 2,
            (scaled.height() - self.height()) // 2,
            self.width(),
            self.height(),
        )
        self.cover_label.setPixmap(_round_top_corners(cropped, HERO_RADIUS))
        self.cover_label.setText("")


class NewsCard(QFrame):
    def __init__(self, item: Dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("newsCard")
        self.setStyleSheet(
            "#newsCard { background:rgba(0,0,0,0.2);border-radius:14px; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(10)

        title = str(item.get("title") or "Без названия")
        self.hero = HeroCover(title, _format_date(item.get("publishedAt")), self)
        layout.addWidget(self.hero)

        description = str(item.get("description") or "").strip()
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color:#9aa8c0;padding:0 12px;background:transparent;")
            layout.addWidget(desc_label)

        body_text = str(item.get("text") or "").strip()
        if body_text:
            self.body = QTextBrowser()
            self.body.setOpenExternalLinks(True)
            self.body.setFrameShape(QFrame.Shape.NoFrame)
            self.body.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.body.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.body.setStyleSheet(
                "QTextBrowser { background:transparent; padding:0 12px; color:#d7deec; }"
            )
            self.body.setMarkdown(body_text)
            self.body.document().contentsChanged.connect(
                lambda: _fit_text_browser_height(self.body)
            )
            layout.addWidget(self.body)
            _fit_text_browser_height(self.body)

        image_url = item.get("image")
        if image_url:
            worker = NewsCoverWorker(str(image_url), self)
            worker.ready_signal.connect(self._on_cover_ready)
            worker.finished.connect(worker.deleteLater)
            worker.start()

    def _on_cover_ready(self, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return
        self.hero.set_pixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "body"):
            _fit_text_browser_height(self.body)


class NewsPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._cards: List[NewsCard] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.status_label = QLabel("Загрузка новостей…")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color:#8b97ad;background:transparent;")
        outer.addWidget(self.status_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(14)
        self.list_layout.addStretch()
        self.scroll.setWidget(self.list_host)
        self.scroll.setVisible(False)
        outer.addWidget(self.scroll, stretch=1)

    def _clear_cards(self) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._cards.clear()

    def set_loading(self) -> None:
        self._clear_cards()
        self.scroll.setVisible(False)
        self.status_label.setText("Загрузка новостей…")
        self.status_label.setVisible(True)

    def set_error(self, message: str) -> None:
        self._clear_cards()
        self.scroll.setVisible(False)
        self.status_label.setText(message)
        self.status_label.setVisible(True)

    def set_disabled(self, message: str = "Новости не настроены") -> None:
        self._clear_cards()
        self.scroll.setVisible(False)
        self.status_label.setText(message)
        self.status_label.setVisible(True)

    def set_articles(self, articles: List[Dict]) -> None:
        self._clear_cards()
        if not articles:
            self.scroll.setVisible(False)
            self.status_label.setText("Новостей пока нет")
            self.status_label.setVisible(True)
            return

        self.status_label.setVisible(False)
        self.scroll.setVisible(True)
        for item in articles:
            card = NewsCard(item, self.list_host)
            self._cards.append(card)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)

        self.list_host.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
