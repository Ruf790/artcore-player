"""Settings and keyboard shortcuts."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout)

from . import APP_TITLE, VERSION, config, style, winint
from .i18n import t


def _buttons(dlg, ok=True):
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel if ok else QDialogButtonBox.Close)
    from PySide6.QtGui import QIcon
    for b in bb.buttons():
        b.setIcon(QIcon())                     # Fusion puts odd stock icons on these
    if ok:
        bb.button(QDialogButtonBox.Ok).setObjectName("primary")
    bb.accepted.connect(dlg.accept)
    bb.rejected.connect(dlg.reject)
    return bb


def _head(text: str, icon_name: str) -> QLabel:
    lab = QLabel(f"&nbsp;{text}")
    lab.setTextFormat(Qt.RichText)
    lab.setStyleSheet("font-size: 14pt; font-weight: 700; padding-bottom: 6px;")
    return lab


class SettingsDialog(QDialog):
    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.lang_changed = False
        self.setWindowTitle(t("settings") + " — " + APP_TITLE)
        self.setMinimumWidth(520)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 16)
        lay.addWidget(_head(t("settings"), "fa6s.gear"))
        form = QFormLayout()
        form.setVerticalSpacing(10)
        self.lang = QComboBox()
        self.lang.addItem("Русский", "ru")
        self.lang.addItem("English", "en")
        self.lang.setCurrentIndex(max(0, self.lang.findData(cfg.get("language", "ru"))))
        form.addRow(t("set_lang"), self.lang)
        self.resume = QCheckBox(t("set_resume")); self.resume.setChecked(cfg.get("resume", True))
        self.autonext = QCheckBox(t("set_autonext")); self.autonext.setChecked(cfg.get("autoplay_next", True))
        self.single = QCheckBox(t("set_single")); self.single.setChecked(cfg.get("single_window", True))
        self.hwdec = QCheckBox(t("set_hwdec")); self.hwdec.setChecked(cfg.get("hwdec", True))
        for cb in (self.resume, self.autonext, self.single, self.hwdec):
            form.addRow(cb)
        hint = QLabel(t("set_hwdec_hint")); hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {style.MUTED}; font-size: 9pt;")
        form.addRow(hint)
        self.alang = QLineEdit(cfg.get("alang", ""))
        self.alang.setPlaceholderText("rus,eng")
        form.addRow(t("set_alang"), self.alang)
        self.slang = QLineEdit(cfg.get("slang", ""))
        self.slang.setPlaceholderText(t("set_slang_ph"))
        form.addRow(t("set_slang"), self.slang)
        row = QHBoxLayout()
        self.shots = QLineEdit(cfg.get("screenshot_dir", ""))
        self.shots.setPlaceholderText(winint.pictures_dir() + "\\ArtCore Player")
        b = QPushButton("…"); b.setFixedWidth(42)
        b.clicked.connect(self._pick)
        row.addWidget(self.shots); row.addWidget(b)
        form.addRow(t("set_shots"), row)
        clear = QPushButton(style.icon("fa6s.eraser"), "  " + t("set_clear_hist"))
        clear.clicked.connect(self._clear)
        form.addRow(clear)
        lay.addLayout(form)
        about = QLabel(t("about_line", VERSION))
        about.setStyleSheet(f"color: {style.MUTED}; font-size: 9pt; padding-top: 8px;")
        about.setWordWrap(True)
        lay.addWidget(about)
        lay.addWidget(_buttons(self))

    def _pick(self):
        d = QFileDialog.getExistingDirectory(self, t("set_shots"), self.shots.text())
        if d:
            self.shots.setText(d)

    def _clear(self):
        self.cfg["recent"] = []
        self.cfg["positions"] = {}
        config.save(self.cfg)

    def accept(self):
        c = self.cfg
        lang = self.lang.currentData()
        self.lang_changed = lang != c.get("language")
        c.update(language=lang, resume=self.resume.isChecked(), autoplay_next=self.autonext.isChecked(),
                 single_window=self.single.isChecked(), hwdec=self.hwdec.isChecked(),
                 alang=self.alang.text().strip(), slang=self.slang.text().strip(),
                 screenshot_dir=self.shots.text().strip())
        super().accept()


KEYS = [
    ("Space / K", "k_pause"), ("F, Enter, " + "double-click", "k_full"), ("Esc", "k_esc"),
    ("← →", "k_seek5"), ("Ctrl + ← →", "k_seek10"), ("Shift + ← →", "k_seek60"), ("0 … 9", "k_percent"),
    ("Home", "k_home"), (". ,", "k_frame"), ("↑ ↓ / wheel", "k_vol"), ("M", "k_mute"),
    ("A", "k_audio"), ("S", "k_subs"), ("Z / X", "k_subdelay"), ("[ ]  Backspace", "k_speed"),
    ("PgUp / PgDn, P / N", "k_prevnext"), ("L", "k_playlist"), ("T", "k_ontop"), ("I", "k_stats"),
    ("Ctrl + S", "k_shot"), ("Ctrl + O", "k_open"), ("Ctrl + W", "k_close"), ("Ctrl + ,", "k_settings"),
]


class KeysDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("keys") + " — " + APP_TITLE)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 16)
        lay.addWidget(_head(t("keys"), "fa6s.keyboard"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(6)
        half = (len(KEYS) + 1) // 2
        for i, (key, desc) in enumerate(KEYS):
            k = QLabel(key.replace("double-click", t("dbl_click")).replace("wheel", t("wheel")))
            k.setStyleSheet(f"background: {style.PANEL2}; border: 1px solid {style.BORDER}; border-radius: 6px;"
                            " padding: 3px 8px; font-weight: 600;")
            d = QLabel(t(desc))
            col = 0 if i < half else 2
            r = i if i < half else i - half
            grid.addWidget(k, r, col, Qt.AlignLeft)
            grid.addWidget(d, r, col + 1)
        lay.addLayout(grid)
        lay.addWidget(_buttons(self, ok=False))
