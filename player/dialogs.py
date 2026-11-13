"""Settings, About, keyboard shortcuts, equalizer, picture, update."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFontComboBox,
                               QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QProgressBar, QPushButton,
                               QSlider, QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from . import APP_TITLE, REPO, VERSION, audio, config, style, winint
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


def _hint(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setWordWrap(True)
    lab.setStyleSheet(f"color: {style.MUTED}; font-size: 9pt;")
    return lab


def _combo(items, current) -> QComboBox:
    """items: (data, text) pairs; selects current (or the first)."""
    cb = QComboBox()
    for data, text in items:
        cb.addItem(text, data)
    i = cb.findData(current)
    cb.setCurrentIndex(i if i >= 0 else 0)
    return cb


def _check(text: str, on) -> QCheckBox:
    cb = QCheckBox(text)
    cb.setChecked(bool(on))
    return cb


def _page() -> tuple[QWidget, QFormLayout]:
    w = QWidget()
    form = QFormLayout(w)
    form.setContentsMargins(16, 16, 16, 12)
    form.setVerticalSpacing(10)
    form.setHorizontalSpacing(14)
    form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    return w, form


QUALITIES = ("fast", "normal", "high")
DEINT = ("auto", "yes", "no")
TONEMAP = (("auto", "tm_auto"), ("bt.2446a", "tm_bt2446a"), ("spline", "tm_spline"), ("hable", "tm_hable"),
           ("mobius", "tm_mobius"))
CHANNELS = (("auto-safe", "ch_auto"), ("stereo", "ch_stereo"), ("5.1", "ch_51"), ("7.1", "ch_71"))
CODEPAGES = (("auto", None), ("cp1251", "Windows-1251"), ("UTF-8", "UTF-8"), ("KOI8-R", "KOI8-R"),
             ("CP866", "CP866 (DOS)"), ("cp1250", "Windows-1250"), ("cp1252", "Windows-1252"))
SUB_COLORS = (("#FFFFFF", "col_white"), ("#FFE94D", "col_yellow"), ("#D8D8D8", "col_gray"), ("#8FE3FF", "col_cyan"))
SUB_BORDERS = {"thin": 1.6, "normal": 2.6, "thick": 3.8}


def codepage_name(cp: str) -> str:
    return next((n for c, n in CODEPAGES if c == cp and n), t("cp_auto"))


class SettingsDialog(QDialog):
    """Everything in tabs: playback, video, sound, subtitles, interface, system."""
    def __init__(self, cfg: dict, parent=None, devices: list | None = None, tab: int = 0):
        super().__init__(parent)
        self.cfg = cfg
        self.lang_changed = False
        self.reset_all = False
        self.setWindowTitle(t("settings") + " — " + APP_TITLE)
        self.setMinimumWidth(820)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 16)
        lay.addWidget(_head(t("settings"), "fa6s.gear"))
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        lay.addWidget(self.tabs, 1)
        c = cfg

        # ── playback
        w, f = _page()
        self.resume = _check(t("set_resume"), c.get("resume", True))
        self.autonext = _check(t("set_autonext"), c.get("autoplay_next", True))
        self.keep_speed = _check(t("set_keep_speed"), c.get("keep_speed", True))
        self.start_full = _check(t("set_start_full"), c.get("start_fullscreen"))
        self.pause_min = _check(t("set_pause_min"), c.get("pause_minimized"))
        for cb in (self.resume, self.autonext, self.keep_speed, self.start_full, self.pause_min):
            f.addRow(cb)
        self.repeat = _combo((("off", t("rep_off")), ("file", t("rep_file")), ("list", t("rep_list"))),
                             c.get("repeat", "off"))
        f.addRow(t("set_repeat"), self.repeat)
        self.seek_step = _combo([(v, t("sec_n", v)) for v in (3, 5, 10, 15, 30)], int(c.get("seek_step", 5)))
        f.addRow(t("set_seek_step"), self.seek_step)
        self.alang = QLineEdit(c.get("alang", ""))
        self.alang.setPlaceholderText("rus,eng")
        f.addRow(t("set_alang"), self.alang)
        self.tabs.addTab(w, style.icon("fa6s.play"), t("tab_play"))

        # ── video
        w, f = _page()
        self.hwdec = _check(t("set_hwdec"), c.get("hwdec", True))
        f.addRow(self.hwdec)
        f.addRow(_hint(t("set_hwdec_hint")))
        self.quality = _combo([(q, t("q_" + q)) for q in QUALITIES], c.get("quality", "normal"))
        f.addRow(t("set_quality"), self.quality)
        self.deint = _combo([(d, t("deint_" + d)) for d in DEINT], c.get("deinterlace", "auto"))
        f.addRow(t("set_deint"), self.deint)
        self.tonemap = _combo([(v, t(k)) for v, k in TONEMAP], c.get("tone_mapping", "auto"))
        f.addRow(t("set_tonemap"), self.tonemap)
        self.deband = _check(t("set_deband"), c.get("deband"))
        self.smooth = _check(t("smooth") + "  (H)", c.get("smooth"))
        f.addRow(self.deband)
        f.addRow(self.smooth)
        row = QHBoxLayout()
        self.shots = QLineEdit(c.get("screenshot_dir", ""))
        self.shots.setPlaceholderText(winint.pictures_dir() + "\\ArtCore Player")
        b = QPushButton("…"); b.setFixedWidth(42)
        b.clicked.connect(self._pick)
        row.addWidget(self.shots); row.addWidget(b)
        f.addRow(t("set_shots"), row)
        srow = QHBoxLayout()
        self.shot_fmt = _combo((("png", "PNG"), ("jpg", "JPEG"), ("webp", "WebP")), c.get("screenshot_format", "png"))
        srow.addWidget(self.shot_fmt)
        self.shot_subs = _check(t("set_shot_subs"), c.get("screenshot_subs", True))
        srow.addSpacing(10)
        srow.addWidget(self.shot_subs, 1)
        f.addRow(t("set_shot_fmt"), srow)
        self.tabs.addTab(w, style.icon("fa6s.film"), t("tab_video"))

        # ── sound
        w, f = _page()
        devs = [("auto", t("adevice_auto"))]
        for d in devices or []:
            name = str(d.get("name", ""))
            if name and name != "auto":
                devs.append((name, str(d.get("description") or name)))
        cur_dev = c.get("audio_device", "auto")
        if cur_dev not in [d for d, _ in devs]:
            devs.append((cur_dev, cur_dev))
        self.adevice = _combo(devs, cur_dev)
        self.adevice.setMinimumContentsLength(28)
        f.addRow(t("set_adevice"), self.adevice)
        self.channels = _combo([(v, t(k)) for v, k in CHANNELS], c.get("audio_channels", "auto-safe"))
        f.addRow(t("set_channels"), self.channels)
        self.exclusive = _check(t("set_exclusive"), c.get("audio_exclusive"))
        f.addRow(self.exclusive)
        self.pitch = _check(t("set_pitch"), c.get("pitch", True))
        f.addRow(self.pitch)
        self.upmix = _check(t("upmix") + "  (U)", c.get("upmix"))
        f.addRow(self.upmix)
        f.addRow(_hint(t("upmix_hint")))
        self.vol_max = _combo([(v, f"{v} %") for v in (100, 130, 150, 200)], int(c.get("volume_max", 150)))
        f.addRow(t("set_vol_max"), self.vol_max)
        self.vol_step = _combo([(v, f"{v} %") for v in (1, 2, 5, 10)], int(c.get("vol_step", 5)))
        f.addRow(t("set_vol_step"), self.vol_step)
        self.tabs.addTab(w, style.icon("fa6s.volume-high"), t("tab_audio"))

        # ── subtitles
        w, f = _page()
        self.slang = QLineEdit(c.get("slang", ""))
        self.slang.setPlaceholderText(t("set_slang_ph"))
        f.addRow(t("set_slang"), self.slang)
        self.sub_auto = _combo([(v, t("sa_" + v)) for v in ("fuzzy", "exact", "no")], c.get("sub_auto", "fuzzy"))
        f.addRow(t("set_sub_auto"), self.sub_auto)
        self.codepage = _combo([(cp, name or t("cp_auto")) for cp, name in CODEPAGES], c.get("sub_codepage", "auto"))
        f.addRow(t("set_codepage"), self.codepage)
        self.font = QFontComboBox()
        self.font.setEditable(False)
        self.font.insertItem(0, t("sub_font_def"))
        if c.get("sub_font"):
            self.font.setCurrentFont(QFont(c["sub_font"]))
        else:
            self.font.setCurrentIndex(0)
        f.addRow(t("set_sub_font"), self.font)
        self.sub_size = _combo([(v, f"{int(round(v * 100))} %") for v in (0.8, 0.9, 1.0, 1.15, 1.3, 1.5)],
                               min((0.8, 0.9, 1.0, 1.15, 1.3, 1.5), key=lambda v: abs(v - float(c.get("sub_scale", 1.0)))))
        f.addRow(t("set_sub_size"), self.sub_size)
        self.sub_color = _combo([(v, t(k)) for v, k in SUB_COLORS], str(c.get("sub_color", "#FFFFFF")).upper())
        for i, (v, _k) in enumerate(SUB_COLORS):
            self.sub_color.setItemIcon(i, style.icon("fa6s.square", v))
        f.addRow(t("set_sub_color"), self.sub_color)
        self.sub_border = _combo([(k, t(n)) for k, n in (("thin", "col_none"), ("normal", "col_black"),
                                                          ("thick", "col_thick"))], c.get("sub_border", "normal"))
        f.addRow(t("set_sub_border"), self.sub_border)
        self.sub_bold = _check(t("set_sub_bold"), c.get("sub_bold"))
        self.sub_force = _check(t("set_sub_force"), c.get("sub_force_style"))
        f.addRow(self.sub_bold)
        f.addRow(self.sub_force)
        self.tabs.addTab(w, style.icon("fa6s.closed-captioning"), t("tab_subs"))

        # ── interface
        w, f = _page()
        self.lang = _combo((("ru", "Русский"), ("en", "English")), c.get("language", "ru"))
        f.addRow(t("set_lang"), self.lang)
        self.hide_delay = _combo([(v, t("sec_n", f"{v:g}")) for v in (1.5, 2.6, 4.0, 6.0)],
                                 min((1.5, 2.6, 4.0, 6.0), key=lambda v: abs(v - float(c.get("hide_delay", 2.6)))))
        f.addRow(t("set_hide_delay"), self.hide_delay)
        self.single = _check(t("set_single"), c.get("single_window", True))
        self.thumbs = _check(t("set_thumbs"), c.get("thumbs", True))
        self.remaining = _check(t("set_remaining"), c.get("remaining_time"))
        self.on_top = _check(t("on_top") + "  (T)", c.get("on_top"))
        self.smtc = _check(t("set_smtc"), c.get("smtc", True))
        self.jumplist = _check(t("set_jumplist"), c.get("jumplist", True))
        for cb in (self.single, self.thumbs, self.remaining, self.on_top, self.smtc, self.jumplist):
            f.addRow(cb)
        self.tabs.addTab(w, style.icon("fa6s.display"), t("tab_ui"))

        # ── system
        w, f = _page()
        urow = QHBoxLayout()
        self.upd = _check(t("set_updates"), c.get("check_updates", True))
        urow.addWidget(self.upd)
        urow.addStretch()
        ub = QPushButton(style.icon("fa6s.rotate"), "  " + t("upd_check_now"))
        ub.clicked.connect(lambda: parent.check_updates(manual=True) if hasattr(parent, "check_updates") else None)
        urow.addWidget(ub)
        f.addRow(urow)
        drow = QHBoxLayout()
        dpath = QLineEdit(config.data_dir())
        dpath.setReadOnly(True)
        drow.addWidget(dpath, 1)
        ob = QPushButton(style.icon("fa6s.folder-open"), "  " + t("set_open_data"))
        ob.clicked.connect(lambda: winint.open_folder(config.data_dir()))
        drow.addWidget(ob)
        f.addRow(t("set_data"), drow)
        brow = QHBoxLayout()
        self.clear_btn = QPushButton(style.icon("fa6s.eraser"), "  " + t("set_clear_hist"))
        self.clear_btn.clicked.connect(self._clear)
        brow.addWidget(self.clear_btn)
        rb = QPushButton(style.icon("fa6s.arrow-rotate-left"), "  " + t("set_reset_all"))
        rb.clicked.connect(self._reset)
        brow.addWidget(rb)
        brow.addStretch()
        f.addRow(brow)
        ab = QPushButton(style.icon("fa6s.circle-info"), "  " + t("about") + "…")
        ab.clicked.connect(lambda: AboutDialog(parent, self).exec())
        arow = QHBoxLayout()
        arow.addWidget(ab)
        arow.addStretch()
        f.addRow(arow)
        f.addRow(_hint(t("about_line", VERSION)))
        self.tabs.addTab(w, style.icon("fa6s.gear"), t("tab_system"))

        self.tabs.setCurrentIndex(max(0, min(tab, self.tabs.count() - 1)))
        lay.addWidget(_buttons(self))

    def _pick(self):
        d = QFileDialog.getExistingDirectory(self, t("set_shots"), self.shots.text())
        if d:
            self.shots.setText(d)

    def _clear(self):
        self.cfg["recent"] = []
        self.cfg["positions"] = {}
        config.save(self.cfg)
        self.clear_btn.setText("  " + t("set_cleared"))
        self.clear_btn.setEnabled(False)

    def _reset(self):
        from PySide6.QtWidgets import QMessageBox
        if QMessageBox.question(self, t("set_reset_all"), t("set_reset_q")) == QMessageBox.Yes:
            self.lang_changed = False
            self.reset_all = True
            config.reset(self.cfg)
            super().accept()

    def accept(self):
        c = self.cfg
        lang = self.lang.currentData()
        self.lang_changed = lang != c.get("language")
        font = "" if self.font.currentIndex() == 0 else self.font.currentFont().family()
        c.update(language=lang, resume=self.resume.isChecked(), autoplay_next=self.autonext.isChecked(),
                 keep_speed=self.keep_speed.isChecked(), start_fullscreen=self.start_full.isChecked(),
                 pause_minimized=self.pause_min.isChecked(), repeat=self.repeat.currentData(),
                 seek_step=int(self.seek_step.currentData()), alang=self.alang.text().strip(),
                 hwdec=self.hwdec.isChecked(), quality=self.quality.currentData(),
                 deinterlace=self.deint.currentData(), tone_mapping=self.tonemap.currentData(),
                 deband=self.deband.isChecked(), smooth=self.smooth.isChecked(),
                 screenshot_dir=self.shots.text().strip(), screenshot_format=self.shot_fmt.currentData(),
                 screenshot_subs=self.shot_subs.isChecked(),
                 audio_device=self.adevice.currentData(), audio_channels=self.channels.currentData(),
                 audio_exclusive=self.exclusive.isChecked(), pitch=self.pitch.isChecked(),
                 upmix=self.upmix.isChecked(), smtc=self.smtc.isChecked(), jumplist=self.jumplist.isChecked(),
                 volume_max=int(self.vol_max.currentData()), vol_step=int(self.vol_step.currentData()),
                 slang=self.slang.text().strip(), sub_auto=self.sub_auto.currentData(),
                 sub_codepage=self.codepage.currentData(), sub_font=font,
                 sub_scale=float(self.sub_size.currentData()), sub_color=self.sub_color.currentData(),
                 sub_border=self.sub_border.currentData(), sub_bold=self.sub_bold.isChecked(),
                 sub_force_style=self.sub_force.isChecked(),
                 hide_delay=float(self.hide_delay.currentData()), single_window=self.single.isChecked(),
                 thumbs=self.thumbs.isChecked(), remaining_time=self.remaining.isChecked(),
                 on_top=self.on_top.isChecked(), check_updates=self.upd.isChecked())
        super().accept()


class AboutDialog(QDialog):
    """Logo, version, the engine and FFmpeg versions, links, and a "copy details" button for bug reports."""
    def __init__(self, win=None, parent=None):
        super().__init__(parent or win)
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        self.win = win
        self.setWindowTitle(t("about") + " — " + APP_TITLE)
        self.setMinimumWidth(540)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 22, 26, 16)
        lay.setSpacing(10)
        head = QHBoxLayout()
        head.setSpacing(18)
        logo = QLabel()
        ratio = max(1.0, float(self.devicePixelRatioF()))
        pm = style.app_icon_pixmap(int(96 * ratio))
        pm.setDevicePixelRatio(ratio)
        logo.setPixmap(pm)
        logo.setFixedSize(96, 96)
        head.addWidget(logo, 0, Qt.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(3)
        name = QLabel(APP_TITLE)
        name.setStyleSheet("font-size: 20pt; font-weight: 800;")
        col.addWidget(name)
        ver = QLabel(t("about_version", VERSION) + ("  ·  " + t("about_portable") if config.is_portable() else ""))
        ver.setStyleSheet(f"color: {style.ACCENT_LIGHT}; font-weight: 600;")
        col.addWidget(ver)
        sub = QLabel(t("about_sub"))
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {style.MUTED};")
        col.addWidget(sub)
        col.addStretch()
        head.addLayout(col, 1)
        lay.addLayout(head)

        self.details = self._details()
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(5)
        for r, (k, v) in enumerate(self.details):
            kl = QLabel(k)
            kl.setStyleSheet(f"color: {style.MUTED};")
            vl = QLabel(v)
            vl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            vl.setWordWrap(True)
            grid.addWidget(kl, r, 0, Qt.AlignTop)
            grid.addWidget(vl, r, 1)
        grid.setColumnStretch(1, 1)
        box = QWidget()
        box.setObjectName("aboutBox")
        box.setStyleSheet(f"QWidget#aboutBox {{ background: {style.PANEL}; border: 1px solid {style.BORDER};"
                          " border-radius: 10px; }")
        box.setLayout(grid)
        grid.setContentsMargins(14, 12, 14, 12)
        lay.addWidget(box)

        fam = QLabel(f"{t('about_family')}: "
                     f"<a style='color:{style.ACCENT_LIGHT}' href='https://github.com/Ruf790/artcore-torrent-client'>ArtCore Client</a>"
                     f" · <b>ArtCore Player</b> · "
                     f"<a style='color:{style.ACCENT_LIGHT}' href='https://github.com/Ruf790/artcore-music'>ArtCore Music</a>")
        fam.setOpenExternalLinks(True)
        lay.addWidget(fam)
        lay.addWidget(_hint(t("about_license")))

        links = QHBoxLayout()
        links.setSpacing(8)
        repo = "https://github.com/" + REPO
        for icon_name, key, target in (("fa6b.github", "about_github", repo),
                                       ("fa6s.star", "about_releases", repo + "/releases"),
                                       ("fa6s.scale-balanced", "about_license_b", self._license())):
            b = QPushButton(style.icon(icon_name), "  " + t(key))
            b.clicked.connect(lambda _=False, u=target: QDesktopServices.openUrl(
                QUrl(u) if "://" in u else QUrl.fromLocalFile(u)))
            links.addWidget(b)
        links.addStretch()
        lay.addLayout(links)

        bb = QDialogButtonBox()
        self.copy_btn = bb.addButton(t("about_copy"), QDialogButtonBox.ActionRole)
        self.copy_btn.setIcon(style.icon("fa6s.copy"))
        self.copy_btn.clicked.connect(self._copy)
        if win is not None and hasattr(win, "check_updates"):
            upd = bb.addButton(t("upd_check_now"), QDialogButtonBox.ActionRole)
            upd.setIcon(style.icon("fa6s.rotate"))
            upd.clicked.connect(lambda: win.check_updates(manual=True))
        close = bb.addButton(QDialogButtonBox.Close)
        from PySide6.QtGui import QIcon
        close.setIcon(QIcon())
        close.setObjectName("primary")
        close.setText(t("close"))
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    @staticmethod
    def _license() -> str:
        import os
        p = os.path.join(config.app_dir(), "LICENSE.txt")
        if not os.path.isfile(p):
            p = os.path.join(config.app_dir(), "LICENSE")
        return p if os.path.isfile(p) else "https://github.com/" + REPO + "/blob/main/LICENSE"

    def _details(self) -> list[tuple[str, str]]:
        import platform
        import PySide6
        from PySide6.QtCore import qVersion
        rows = []
        mpv = getattr(self.win, "mpv", None)
        mv = ff = hw = ""
        if mpv is not None:
            try:
                mv = str(mpv.mpv_version or "")
                ff = str(mpv.ffmpeg_version or "")
            except Exception:
                pass
            try:
                hw = str(self.win._get("hwdec-current", "") or "")
            except Exception:
                hw = ""
        rows.append((t("about_engine"), (mv or "mpv") + (f"  ·  FFmpeg {ff}" if ff else "")))
        if mpv is not None and getattr(self.win, "path", ""):
            rows.append((t("about_decoding"), t("about_hw", hw) if hw and hw != "no" else t("about_sw")))
        rows.append(("Qt", f"{qVersion()}  ·  PySide6 {PySide6.__version__}  ·  Python {platform.python_version()}"))
        rows.append((t("about_system"), _windows_name()))
        return rows

    def _copy(self):
        from PySide6.QtWidgets import QApplication
        text = f"{APP_TITLE} {VERSION}" + (" (portable)" if config.is_portable() else "") + "\n"
        text += "\n".join(f"{k}: {v}" for k, v in self.details)
        QApplication.clipboard().setText(text)
        self.copy_btn.setText(t("about_copied"))


def _windows_name() -> str:
    import platform
    if winint.IS_WIN:
        try:
            build = int(platform.version().split(".")[-1])
            name = "Windows 11" if build >= 22000 else "Windows 10"
            return f"{name} (build {platform.version()}, {platform.machine()})"
        except Exception:
            pass
    return f"{platform.system()} {platform.release()} ({platform.machine()})"


KEYS = [
    ("Space / K", "k_pause"), ("F, Enter, " + "double-click", "k_full"), ("Esc", "k_esc"),
    ("← →", "k_seekstep"), ("Ctrl + ← →", "k_seek10"), ("Shift + ← →", "k_seek60"), ("0 … 9", "k_percent"),
    ("Home", "k_home"), (". ,", "k_frame"), ("↑ ↓ / wheel", "k_vol"), ("M", "k_mute"),
    ("A", "k_audio"), ("S", "k_subs"), ("Z / X", "k_subdelay"), ("[ ]  Backspace", "k_speed"),
    ("PgUp / PgDn", "k_chapters"), ("Shift + PgUp / PgDn, P / N", "k_prevnext"), ("C", "k_chapter_list"),
    ("E", "k_eq"), ("D", "k_dialog"), ("U", "k_upmix"), ("Ctrl + Z / X", "k_audiodelay"), ("B", "k_ab"), ("V", "k_picture"),
    ("H", "k_smooth"), ("Ctrl + M", "k_mini"), ("L", "k_playlist"), ("T", "k_ontop"), ("I", "k_stats"),
    ("R", "k_repeat"), ("Ctrl + R", "k_rotate"), ("Ctrl + S", "k_shot"), ("Ctrl + O", "k_open"),
    ("Ctrl + U", "k_url"), ("Ctrl + W", "k_close"), ("Ctrl + ,", "k_settings"),
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


class CountdownDialog(QDialog):
    """"Shut down the PC in 30 s" — Cancel stops it, Now does it at once; accepted when the time is up."""
    def __init__(self, what: str, seconds: int, parent=None):
        super().__init__(parent)
        from PySide6.QtCore import QTimer
        self.what, self.left = what, seconds
        self.setWindowTitle(APP_TITLE)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setMinimumWidth(380)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 16)
        self.label = QLabel()
        self.label.setStyleSheet("font-size: 13pt; font-weight: 700;")
        lay.addWidget(self.label)
        self.bar = QProgressBar()
        self.bar.setRange(0, seconds)
        self.bar.setTextVisible(False)
        lay.addWidget(self.bar)
        bb = QDialogButtonBox()
        bb.addButton(t("after_now"), QDialogButtonBox.AcceptRole)
        cancel = bb.addButton(t("after_cancel"), QDialogButtonBox.RejectRole)
        cancel.setObjectName("primary")
        cancel.setDefault(True)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()
        self._show()

    def _show(self):
        self.label.setText(t("after_count", self.what, self.left))
        self.bar.setValue(self.left)

    def _tick(self):
        self.left -= 1
        if self.left <= 0:
            self.timer.stop()
            self.accept()
            return
        self._show()


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


class PictureDialog(QDialog):
    """Brightness / contrast / saturation / gamma, −100…100, heard… seen at once."""
    changed = Signal()
    KEYS = ("brightness", "contrast", "saturation", "gamma")
    ICONS = ("fa6s.sun", "fa6s.circle-half-stroke", "fa6s.droplet", "fa6s.chart-line")

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle(t("picture") + " — " + APP_TITLE)
        self.setMinimumWidth(460)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 16)
        lay.addWidget(_head(t("picture"), "fa6s.circle-half-stroke"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        pic = cfg.setdefault("picture", {})
        self.sliders = {}
        for r, (k, ic) in enumerate(zip(self.KEYS, self.ICONS)):
            icl = QLabel()
            icl.setPixmap(style.icon(ic, style.MUTED).pixmap(16, 16))
            name = QLabel(t("pic_" + k))
            sl = QSlider(Qt.Horizontal)
            sl.setRange(-100, 100)
            sl.setValue(int(pic.get(k, 0)))
            val = QLabel()
            val.setFixedWidth(40)
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            sl.valueChanged.connect(lambda v, k=k, val=val: self._moved(k, v, val))
            self._moved(k, sl.value(), val, emit=False)
            grid.addWidget(icl, r, 0)
            grid.addWidget(name, r, 1)
            grid.addWidget(sl, r, 2)
            grid.addWidget(val, r, 3)
            self.sliders[k] = sl
        grid.setColumnStretch(2, 1)
        lay.addLayout(grid)
        row = QHBoxLayout()
        for key, vals in (("pic_preset_dark", (8, 6, 0, 12)), ("pic_preset_vivid", (0, 6, 20, 0)),
                          ("pic_preset_soft", (0, -6, -10, 0))):
            b = QPushButton(t(key))
            b.clicked.connect(lambda _=False, vals=vals: self._set(vals))
            row.addWidget(b)
        reset = QPushButton(t("reset"))
        reset.clicked.connect(lambda: self._set((0, 0, 0, 0)))
        row.addWidget(reset)
        lay.addLayout(row)
        lay.addWidget(_buttons(self))

    def _set(self, vals):
        for k, v in zip(self.KEYS, vals):
            self.sliders[k].setValue(v)

    def _moved(self, k: str, v: int, val: QLabel, emit: bool = True):
        val.setText(f"{v:+d}" if v else "0")
        self.cfg.setdefault("picture", {})[k] = v
        if emit:
            self.changed.emit()
