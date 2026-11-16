"""Colours, the app icon and the dark style sheet."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPixmap

ACCENT = "#0d6efd"
ACCENT2 = "#6f42c1"
ACCENT_LIGHT = "#6ea8fe"
BG = "#0f1115"
PANEL = "#171a21"
PANEL2 = "#1f232c"
BORDER = "#2b303b"
TEXT = "#e9ecef"
MUTED = "#9aa3b2"


def _icon_png(name: str, glyph: str, color: str, size: int) -> str:
    """Small icon saved to a file (QSS needs a file)."""
    import os
    import tempfile
    path = os.path.join(tempfile.gettempdir(), "artcore_player_%s.png" % name)
    if not os.path.isfile(path):
        try:
            icon(glyph, color).pixmap(size, size).save(path)
        except Exception:
            return ""
    return path.replace("\\", "/")


def _check_png() -> str:
    """White check mark for checked boxes."""
    return _icon_png("check", "fa6s.check", "#ffffff", 12)


def stylesheet() -> str:
    return (QSS.replace("%CHECK%", _check_png())
               .replace("%UP%", _icon_png("up", "fa6s.chevron-up", TEXT, 8))
               .replace("%DOWN%", _icon_png("down", "fa6s.chevron-down", TEXT, 8)))


def icon(name: str, color: str = TEXT):
    import qtawesome as qta
    return qta.icon(name, color=color)


def app_icon_pixmap(size: int = 256) -> QPixmap:
    """Rounded square, blue → purple, a white play triangle (the ArtCore family look)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(size * 0.04, size * 0.04, size * 0.92, size * 0.92)
    g = QLinearGradient(r.topLeft(), r.bottomRight())
    g.setColorAt(0, QColor(ACCENT))
    g.setColorAt(1, QColor(ACCENT2))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawRoundedRect(r, size * 0.22, size * 0.22)
    tri = QPainterPath()
    cx, cy, s = size * 0.535, size * 0.5, size * 0.25
    tri.moveTo(QPointF(cx - s * 0.8, cy - s))
    tri.lineTo(QPointF(cx + s * 1.0, cy))
    tri.lineTo(QPointF(cx - s * 0.8, cy + s))
    tri.closeSubpath()
    p.setBrush(QColor("#ffffff"))
    p.drawPath(tri)
    p.end()
    return pm


def format_icon(path: str) -> QIcon | None:
    """The file-type icon of a video (assets/formats/<ext>.ico — next to the exe in a build); None if there is none."""
    import os
    from . import config
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if not ext or "://" in path:
        return None
    cache = _FMT_CACHE
    if ext not in cache:
        cache[ext] = None
        for d in (os.path.join(config.app_dir(), "formats"), os.path.join(config.app_dir(), "assets", "formats")):
            p = os.path.join(d, ext + ".ico")
            if os.path.isfile(p):
                cache[ext] = QIcon(p)
                break
    return cache[ext]


_FMT_CACHE: dict = {}


def app_icon() -> QIcon:
    ic = QIcon()
    for n in (16, 20, 24, 32, 48, 64, 128, 256):
        ic.addPixmap(app_icon_pixmap(n))
    return ic


QSS = f"""
QWidget {{ color: {TEXT}; font-size: 10pt; }}
QMainWindow, QDialog {{ background: {BG}; }}
QToolTip {{ background: {PANEL2}; color: {TEXT}; border: 1px solid {BORDER}; padding: 4px 7px; border-radius: 6px; }}
QMenu {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px; }}
QMenu::item {{ padding: 7px 26px 7px 12px; border-radius: 6px; }}
QMenu::item:selected {{ background: {ACCENT}; color: #ffffff; }}
QMenu::item:disabled {{ color: {MUTED}; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 5px 8px; }}
QMenu::icon {{ padding-left: 8px; }}
QMenu::indicator {{ width: 14px; height: 14px; left: 6px; }}
QPushButton {{ background: {PANEL2}; border: 1px solid {BORDER}; border-radius: 9px; padding: 8px 16px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton#primary {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2});
                       border: none; color: #ffffff; font-weight: 600; }}
QPushButton#primary:hover {{ background: {ACCENT}; }}
QToolButton#ctl {{ background: transparent; border: none; border-radius: 8px; padding: 6px; }}
QToolButton#ctl:hover {{ background: rgba(255,255,255,38); }}
QToolButton#ctl:pressed {{ background: rgba(255,255,255,60); }}
QToolButton#ctl::menu-indicator {{ image: none; width: 0; }}
QToolButton#ctlText {{ background: transparent; border: none; border-radius: 8px; padding: 6px 8px;
                       font-weight: 600; }}
QToolButton#ctlText:hover {{ background: rgba(255,255,255,38); }}
QToolButton#ctlText::menu-indicator {{ image: none; width: 0; }}
QLabel#time {{ font-size: 10pt; color: #ffffff; padding: 0 6px; }}
QLabel#title {{ font-size: 13pt; font-weight: 600; color: #ffffff; }}
QLabel#badge {{ background: rgba(255,255,255,30); border: 1px solid rgba(255,255,255,60); border-radius: 5px;
                padding: 1px 6px; font-size: 8.5pt; font-weight: 700; color: #ffffff; }}
QLabel#badgeHdr {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f59f00, stop:1 #e8590c);
                   border-radius: 5px; padding: 1px 6px; font-size: 8.5pt; font-weight: 700; color: #ffffff; }}
QSlider#volume::groove:horizontal {{ height: 4px; background: rgba(255,255,255,70); border-radius: 2px; }}
QSlider#volume::sub-page:horizontal {{ background: #ffffff; border-radius: 2px; }}
QSlider#volume::handle:horizontal {{ background: #ffffff; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }}
QListWidget#playlist {{ background: transparent; border: none; outline: none; }}
QListWidget#playlist::item {{ padding: 8px 10px; border-radius: 8px; color: {TEXT}; }}
QListWidget#playlist::item:hover {{ background: rgba(255,255,255,22); }}
QListWidget#playlist::item:selected {{ background: rgba(13,110,253,90); }}
QListWidget#recent {{ background: transparent; border: none; outline: none; }}
QListWidget#recent::item {{ padding: 9px 12px; border-radius: 9px; }}
QListWidget#recent::item:hover {{ background: {PANEL2}; }}
QListWidget#recent::item:selected {{ background: {PANEL2}; color: {TEXT}; }}
QCheckBox {{ spacing: 9px; }}
QCheckBox::indicator {{ width: 17px; height: 17px; border-radius: 5px; border: 1px solid {BORDER}; background: {PANEL2}; }}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; image: url(%CHECK%); }}
QLineEdit, QComboBox {{ background: {PANEL2}; border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 9px; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QSpinBox {{ background: {PANEL2}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 8px;
            padding: 6px 24px 6px 9px; min-width: 34px; selection-background-color: {ACCENT}; selection-color: #ffffff; }}
QSpinBox:focus {{ border-color: {ACCENT}; }}
QSpinBox:disabled {{ color: {MUTED}; }}
QSpinBox::up-button, QSpinBox::down-button {{ subcontrol-origin: border; width: 20px; border: none;
            border-left: 1px solid {BORDER}; background: {PANEL}; }}
QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 8px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 8px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {ACCENT}; }}
QSpinBox::up-arrow {{ image: url(%UP%); width: 8px; height: 8px; }}
QSpinBox::down-arrow {{ image: url(%DOWN%); width: 8px; height: 8px; }}
QSpinBox::up-arrow:disabled, QSpinBox::up-arrow:off, QSpinBox::down-arrow:disabled, QSpinBox::down-arrow:off {{ image: none; }}
QComboBox QAbstractItemView {{ background: {PANEL}; border: 1px solid {BORDER}; selection-background-color: {ACCENT}; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 10px; background: {PANEL}; top: -1px; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; padding: 8px 12px; margin-right: 2px;
                border-top-left-radius: 8px; border-top-right-radius: 8px; }}
QTabBar::tab:hover {{ color: {TEXT}; background: {PANEL2}; }}
QTabBar::tab:selected {{ color: #ffffff; background: {PANEL}; border: 1px solid {BORDER}; border-bottom: 2px solid {ACCENT}; }}
QProgressBar {{ background: {PANEL2}; border: 1px solid {BORDER}; border-radius: 6px; height: 10px; text-align: center; }}
QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2}); border-radius: 5px; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: rgba(255,255,255,50); border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
