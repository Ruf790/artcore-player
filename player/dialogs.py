"""Settings and keyboard shortcuts."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit, QProgressBar, QPushButton, QSlider,
                               QTextBrowser, QVBoxLayout)

from . import APP_TITLE, VERSION, audio, config, style, winint
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
        self.thumbs = QCheckBox(t("set_thumbs")); self.thumbs.setChecked(cfg.get("thumbs", True))
        for cb in (self.resume, self.autonext, self.single, self.thumbs, self.hwdec):
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
        urow = QHBoxLayout()
        self.upd = QCheckBox(t("set_updates")); self.upd.setChecked(cfg.get("check_updates", True))
        urow.addWidget(self.upd)
        urow.addStretch()
        ub = QPushButton(style.icon("fa6s.rotate"), "  " + t("upd_check_now"))
        ub.clicked.connect(lambda: parent.check_updates(manual=True) if hasattr(parent, "check_updates") else None)
        urow.addWidget(ub)
        form.addRow(urow)
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
                 thumbs=self.thumbs.isChecked(), check_updates=self.upd.isChecked(),
                 alang=self.alang.text().strip(), slang=self.slang.text().strip(),
                 screenshot_dir=self.shots.text().strip())
        super().accept()


KEYS = [
    ("Space / K", "k_pause"), ("F, Enter, " + "double-click", "k_full"), ("Esc", "k_esc"),
    ("← →", "k_seek5"), ("Ctrl + ← →", "k_seek10"), ("Shift + ← →", "k_seek60"), ("0 … 9", "k_percent"),
    ("Home", "k_home"), (". ,", "k_frame"), ("↑ ↓ / wheel", "k_vol"), ("M", "k_mute"),
    ("A", "k_audio"), ("S", "k_subs"), ("Z / X", "k_subdelay"), ("[ ]  Backspace", "k_speed"),
    ("PgUp / PgDn", "k_chapters"), ("Shift + PgUp / PgDn, P / N", "k_prevnext"), ("C", "k_chapter_list"),
    ("E", "k_eq"), ("D", "k_dialog"), ("L", "k_playlist"), ("T", "k_ontop"), ("I", "k_stats"),
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


class EqualizerDialog(QDialog):
    """10 bands ±12 dB with presets; every move is heard at once (changed → apply_audio)."""
    changed = Signal()

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle(t("equalizer") + " — " + APP_TITLE)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 16)
        lay.addWidget(_head(t("equalizer"), "fa6s.sliders"))
        top = QHBoxLayout()
        top.addWidget(QLabel(t("eq_preset")))
        self.preset = QComboBox()
        for key in audio.PRESETS:
            self.preset.addItem(t("eqp_" + key), key)
        self.preset.addItem(t("eqp_custom"), "custom")
        top.addWidget(self.preset, 1)
        reset = QPushButton(t("reset"))
        reset.clicked.connect(lambda: self._load(audio.PRESETS["flat"], "flat"))
        top.addWidget(reset)
        lay.addLayout(top)
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        self.sliders: list[QSlider] = []
        self.vals: list[QLabel] = []
        for i, f in enumerate(audio.BANDS):
            v = QLabel("0")
            v.setAlignment(Qt.AlignCenter)
            v.setStyleSheet(f"color: {style.MUTED}; font-size: 8.5pt;")
            sl = QSlider(Qt.Vertical)
            sl.setRange(-12, 12)
            sl.setFixedHeight(170)
            sl.setTickPosition(QSlider.TicksBothSides)
            sl.setTickInterval(6)
            sl.valueChanged.connect(lambda _v, i=i: self._moved(i))
            lab = QLabel(f"{f // 1000}k" if f >= 1000 else str(f))
            lab.setAlignment(Qt.AlignCenter)
            grid.addWidget(v, 0, i, Qt.AlignHCenter)
            grid.addWidget(sl, 1, i, Qt.AlignHCenter)
            grid.addWidget(lab, 2, i, Qt.AlignHCenter)
            self.sliders.append(sl)
            self.vals.append(v)
        lay.addLayout(grid)
        hint = QLabel(t("eq_hint"))
        hint.setStyleSheet(f"color: {style.MUTED}; font-size: 9pt;")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addWidget(_buttons(self))
        self._loading = False
        gains = [int(g) for g in cfg.get("eq", [0] * 10)]
        self._load(gains, next((k for k, v in audio.PRESETS.items() if list(v) == gains), "custom"))
        self.preset.currentIndexChanged.connect(self._pick)

    def _load(self, gains, preset: str):
        self._loading = True
        for sl, g in zip(self.sliders, gains):
            sl.setValue(int(g))
        self.preset.setCurrentIndex(max(0, self.preset.findData(preset)))
        self._loading = False
        self._store("custom" if preset == "custom" else preset)

    def _pick(self, _i):
        key = self.preset.currentData()
        if key in audio.PRESETS and not self._loading:
            self._load(audio.PRESETS[key], key)

    def _moved(self, i: int):
        self.vals[i].setText(f"{self.sliders[i].value():+d}" if self.sliders[i].value() else "0")
        if self._loading:
            return
        gains = [sl.value() for sl in self.sliders]
        match = next((k for k, v in audio.PRESETS.items() if list(v) == gains), "custom")
        self._loading = True
        self.preset.setCurrentIndex(self.preset.findData(match))
        self._loading = False
        self._store(match)

    def _store(self, preset: str):
        for i, sl in enumerate(self.sliders):
            self.vals[i].setText(f"{sl.value():+d}" if sl.value() else "0")
        self.cfg["eq"] = [sl.value() for sl in self.sliders]
        self.cfg["eq_preset"] = preset
        self.changed.emit()


class UpdateDialog(QDialog):
    """Release notes + download and silent install of the new Setup.exe."""
    progress = Signal(int, int)
    done = Signal(str, str)               # path, error

    def __init__(self, info: dict, parent=None):
        super().__init__(parent)
        from . import updater
        self.info, self.updater, self.path = info, updater, ""
        self.setWindowTitle(t("upd_title"))
        self.resize(600, 440)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 16)
        lay.addWidget(_head(t("upd_available", info["version"]), "fa6s.circle-arrow-up"))
        sub = QLabel(t("upd_text", info["version"], VERSION))
        sub.setStyleSheet(f"color: {style.MUTED};")
        lay.addWidget(sub)
        notes = QTextBrowser()
        notes.setOpenExternalLinks(True)
        notes.setMarkdown(info.get("notes") or "")
        notes.setStyleSheet(f"background: {style.PANEL}; border: 1px solid {style.BORDER}; border-radius: 8px; padding: 6px;")
        lay.addWidget(notes, 1)
        self.bar = QProgressBar()
        self.bar.hide()
        lay.addWidget(self.bar)
        note = QLabel(t("upd_restart"))
        note.setStyleSheet(f"color: {style.MUTED}; font-size: 9pt;")
        note.setWordWrap(True)
        lay.addWidget(note)
        bb = QDialogButtonBox()
        self.go = bb.addButton(t("upd_install"), QDialogButtonBox.AcceptRole)
        self.go.setObjectName("primary")
        bb.addButton(t("upd_later"), QDialogButtonBox.RejectRole)
        bb.accepted.connect(self._go)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.progress.connect(self._on_progress)
        self.done.connect(self._on_done)

    def _go(self):
        import threading
        self.go.setEnabled(False)
        self.bar.setRange(0, max(1, self.info.get("size", 0)))
        self.bar.show()

        def work():
            try:
                p = self.updater.download(self.info["url"], self.info.get("size", 0),
                                          lambda d, n: self.progress.emit(d, n))
                self.done.emit(p, "")
            except Exception as e:
                self.done.emit("", str(e))
        threading.Thread(target=work, daemon=True).start()

    def _on_progress(self, d: int, n: int):
        if n:
            self.bar.setMaximum(n)
        self.bar.setValue(min(d, self.bar.maximum()))
        self.bar.setFormat(t("upd_downloading", f"{d / 1048576:.1f}", f"{(n or d) / 1048576:.1f}"))

    def _on_done(self, path: str, err: str):
        from PySide6.QtWidgets import QMessageBox
        if err:
            self.go.setEnabled(True)
            QMessageBox.warning(self, t("upd_title"), t("upd_error", err))
            return
        self.path = path
        self.accept()
