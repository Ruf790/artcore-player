"""Overlay pieces: seek bar, control / title panels, toast, play-pause pulse, start page, playlist."""
from __future__ import annotations

import os

from PySide6.QtCore import (Property, QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer,
                            Signal)
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QToolButton,
                               QVBoxLayout, QWidget)

from . import style
from .i18n import t


def fmt_time(sec: float | None, force_hours: bool = False) -> str:
    if sec is None or sec != sec or sec < 0:
        sec = 0
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h or force_hours else f"{m}:{s:02d}"


def ctl_button(icon_name: str, tip: str, size: int = 20, slot=None) -> QToolButton:
    b = QToolButton()
    b.setObjectName("ctl")
    b.setIcon(style.icon(icon_name, "#ffffff"))
    b.setIconSize(QSize(size, size))
    b.setToolTip(tip)
    b.setFocusPolicy(Qt.NoFocus)
    b.setCursor(Qt.PointingHandCursor)
    if slot:
        b.clicked.connect(slot)
    return b


class SeekBar(QWidget):
    """Thin bar that grows under the mouse; shows buffered ranges, chapters and a time bubble."""
    seek = Signal(float, bool)            # seconds, exact (False while dragging = keyframes)
    hover = Signal(float, int)            # seconds under the mouse (-1 = left), x in this widget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFixedHeight(22)
        self.setCursor(Qt.PointingHandCursor)
        self.duration = 0.0
        self.position = 0.0
        self.cached: list[tuple[float, float]] = []
        self.chapters: list[float] = []
        self._hover_x = -1
        self._drag = False

    def set_state(self, pos: float | None, dur: float | None):
        self.position = pos or 0.0
        self.duration = dur or 0.0
        self.update()

    def _sec_at(self, x: float) -> float:
        w = max(1, self.width() - 12)
        return max(0.0, min(1.0, (x - 6) / w)) * self.duration

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        active = self._hover_x >= 0 or self._drag
        th = 6 if active else 4
        y = self.height() / 2 - th / 2
        x0, w = 6, self.width() - 12
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 60))
        p.drawRoundedRect(QRectF(x0, y, w, th), th / 2, th / 2)
        if self.duration > 0:
            p.setBrush(QColor(255, 255, 255, 105))
            for a, b in self.cached:
                xa = x0 + w * max(0.0, a) / self.duration
                xb = x0 + w * min(self.duration, b) / self.duration
                if xb > xa:
                    p.drawRoundedRect(QRectF(xa, y, xb - xa, th), th / 2, th / 2)
            if self._hover_x >= 0 and not self._drag:
                hx = max(x0, min(x0 + w, self._hover_x))
                p.setBrush(QColor(255, 255, 255, 70))
                p.drawRoundedRect(QRectF(x0, y, hx - x0, th), th / 2, th / 2)
            px = x0 + w * min(1.0, self.position / self.duration)
            g = QLinearGradient(x0, 0, x0 + w, 0)
            g.setColorAt(0, QColor(style.ACCENT))
            g.setColorAt(1, QColor(style.ACCENT2))
            p.setBrush(g)
            p.drawRoundedRect(QRectF(x0, y, px - x0, th), th / 2, th / 2)
            p.setBrush(QColor(0, 0, 0, 150))
            for c in self.chapters:
                if 0 < c < self.duration:
                    cx = x0 + w * c / self.duration
                    p.drawRect(QRectF(cx - 1, y, 2, th))
            if active:
                p.setBrush(QColor("#ffffff"))
                p.drawEllipse(QPointF(px, self.height() / 2), 7, 7)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.duration > 0:
            self._drag = True
            self.seek.emit(self._sec_at(e.position().x()), False)
            self.update()

    def mouseMoveEvent(self, e):
        self._hover_x = e.position().x()
        if self.duration > 0:
            self.hover.emit(self._sec_at(self._hover_x), int(self._hover_x))
            if self._drag:
                self.seek.emit(self._sec_at(self._hover_x), False)
        self.update()

    def mouseReleaseEvent(self, e):
        if self._drag:
            self._drag = False
            self.seek.emit(self._sec_at(e.position().x()), True)
            self.update()

    def leaveEvent(self, _):
        self._hover_x = -1
        self.hover.emit(-1, -1)
        self.update()


class GradientPanel(QWidget):
    """Transparent → dark gradient behind the controls (bottom) or the title (top)."""
    def __init__(self, bottom: bool, parent=None):
        super().__init__(parent)
        self.bottom = bottom
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, _):
        p = QPainter(self)
        g = QLinearGradient(0, 0, 0, self.height())
        dark, clear = QColor(0, 0, 0, 205), QColor(0, 0, 0, 0)
        g.setColorAt(0, clear if self.bottom else dark)
        g.setColorAt(1, dark if self.bottom else clear)
        p.fillRect(self.rect(), g)


class Bubble(QLabel):
    """Time bubble above the seek bar."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: rgba(15,17,21,230); color: #ffffff; border: 1px solid rgba(255,255,255,40);"
                           " border-radius: 6px; padding: 3px 8px; font-weight: 600;")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()


class Toast(QLabel):
    """Short message in the top-left corner (volume, seek, track…), like mpv's OSD."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: rgba(15,17,21,215); color: #ffffff; border-radius: 10px;"
                           " padding: 8px 14px; font-size: 11pt; font-weight: 600;")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.hide()

    def show_text(self, text: str, ms: int = 1300):
        self.setText(text)
        self.adjustSize()
        self.move(24, 24 if not self.parent() else getattr(self.parent(), "toast_top", 24))
        self.show()
        self.raise_()
        self._timer.start(ms)


class Pulse(QWidget):
    """Big play / pause icon that grows and fades in the middle of the picture."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(110, 110)
        self._v = 0.0
        self._name = "fa6s.play"
        self.anim = QPropertyAnimation(self, b"v", self)
        self.anim.setDuration(550)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.finished.connect(self.hide)
        self.hide()

    def _get(self):
        return self._v

    def _set(self, v):
        self._v = v
        self.update()

    v = Property(float, _get, _set)

    def pulse(self, icon_name: str):
        self._name = icon_name
        par = self.parentWidget()
        if par:
            self.move((par.width() - self.width()) // 2, (par.height() - self.height()) // 2)
        self.show()
        self.raise_()
        self.anim.stop()
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(max(0.0, 1.0 - self._v))
        s = 70 + 30 * self._v
        r = QRectF((self.width() - s) / 2, (self.height() - s) / 2, s, s)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawEllipse(r)
        isz = int(s * 0.42)
        p.drawPixmap(int(r.center().x() - isz / 2 + (3 if self._name.endswith("play") else 0)),
                     int(r.center().y() - isz / 2), style.icon(self._name, "#ffffff").pixmap(isz, isz))


class PlaylistPanel(QWidget):
    """Files of the folder (or the dropped files), on the right over the picture."""
    play = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("PlaylistPanel { background: rgba(15,17,21,228); border-left: 1px solid rgba(255,255,255,30); }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 14, 10, 10)
        head = QHBoxLayout()
        self.title = QLabel(t("playlist"))
        self.title.setStyleSheet("font-weight: 700; font-size: 11pt; padding-left: 6px;")
        head.addWidget(self.title, 1)
        self.close_btn = ctl_button("fa6s.xmark", t("close"), 14)
        head.addWidget(self.close_btn)
        lay.addLayout(head)
        self.list = QListWidget()
        self.list.setObjectName("playlist")
        self.list.setFocusPolicy(Qt.NoFocus)
        self.list.setWordWrap(True)
        self.list.itemActivated.connect(lambda it: self.play.emit(self.list.row(it)))
        self.list.itemDoubleClicked.connect(lambda it: self.play.emit(self.list.row(it)))
        lay.addWidget(self.list, 1)
        self.hide()

    def set_items(self, paths: list[str], current: int):
        self.list.clear()
        for i, p in enumerate(paths):
            it = QListWidgetItem(f"{i + 1}.  {os.path.basename(p)}")
            it.setToolTip(p)
            if i == current:
                f = it.font()
                f.setBold(True)
                it.setFont(f)
                it.setForeground(QColor("#6ea8fe"))
                it.setIcon(style.icon("fa6s.play", "#6ea8fe"))
            self.list.addItem(it)
        self.title.setText(t("playlist_n", len(paths)))
        if 0 <= current < self.list.count():
            self.list.setCurrentRow(current)
            self.list.scrollToItem(self.list.item(current), QListWidget.PositionAtCenter)


class SeekPreview(QWidget):
    """Above the seek bar: the frame at the mouse position (when the thumbnailer has it), the time
    and the chapter name."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setObjectName("seekPreview")
        self.setStyleSheet("QWidget#seekPreview { background: rgba(15,17,21,235); border: 1px solid rgba(255,255,255,45);"
                           " border-radius: 9px; }")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 5)
        lay.setSpacing(3)
        self.pic = QLabel()
        self.pic.setAlignment(Qt.AlignCenter)
        self.pic.setStyleSheet("background: #000000; border-radius: 6px;")
        lay.addWidget(self.pic)
        self.text = QLabel()
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setStyleSheet("color: #ffffff; font-weight: 600; background: transparent; padding: 0 6px;")
        lay.addWidget(self.text)
        self.chapter = QLabel()
        self.chapter.setAlignment(Qt.AlignCenter)
        self.chapter.setStyleSheet(f"color: {style.MUTED}; font-size: 8.5pt; background: transparent; padding: 0 6px;")
        lay.addWidget(self.chapter)
        self.want_images = True
        self.hide()

    def set_content(self, time_text: str, chapter: str, image=None, frame_size: QSize | None = None):
        self.text.setText(time_text)
        self.chapter.setText(chapter)
        self.chapter.setVisible(bool(chapter))
        if self.want_images and frame_size is not None:
            from PySide6.QtGui import QPixmap
            if image is not None and not image.isNull():
                pm = QPixmap.fromImage(image).scaled(frame_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.pic.setPixmap(pm)
            else:
                self.pic.setPixmap(QPixmap())
            self.pic.setFixedSize(frame_size)
            self.pic.show()
        else:
            self.pic.hide()
        self.adjustSize()
