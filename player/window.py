"""Main window: the picture, controls floating over it, menus, keys, playlist, resume."""
from __future__ import annotations

import os
import re
import time

from PySide6.QtCore import QObject, QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QCursor, QKeySequence
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QMenu, QMessageBox,
                               QPushButton, QSlider, QVBoxLayout, QWidget)

from . import APP_TITLE, AUDIO_EXT, DISC_EXT, SUB_EXT, VIDEO_EXT, VERSION, config, style, winint
from .i18n import lang_name, t
from .video import VideoWidget
from . import audio
from .widgets import (GradientPanel, Pulse, PlaylistPanel, SeekBar, SeekPreview, StartPage, Toast, ctl_button,
                      fmt_time)

MEDIA_EXT = VIDEO_EXT + AUDIO_EXT
SPEEDS = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 3.0)
OBSERVED = ("time-pos", "duration", "pause", "volume", "mute", "track-list", "chapter-list", "video-params",
            "audio-params", "eof-reached", "media-title", "speed", "demuxer-cache-state", "idle-active",
            "aid", "sid", "path", "chapter")


def natural_key(s: str):
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", s)]


def media_in(folder: str) -> list[str]:
    try:
        names = [n for n in os.listdir(folder) if n.lower().endswith(MEDIA_EXT)]
    except OSError:
        return []
    return [os.path.join(folder, n) for n in sorted(names, key=natural_key)]


def disc_of(path: str) -> tuple[str, str] | None:
    """("bd" | "dvd", device) when the path is a disc: a Blu-ray / DVD folder (or its BDMV / VIDEO_TS
    subfolder) or an .iso image. None for ordinary files and folders."""
    if os.path.isdir(path):
        base = os.path.basename(os.path.normpath(path)).upper()
        if base in ("BDMV", "VIDEO_TS"):
            return ("bd" if base == "BDMV" else "dvd"), os.path.dirname(os.path.normpath(path))
        if os.path.isdir(os.path.join(path, "BDMV")) or os.path.isfile(os.path.join(path, "index.bdmv")):
            return "bd", path
        if os.path.isdir(os.path.join(path, "VIDEO_TS")) or os.path.isfile(os.path.join(path, "VIDEO_TS.IFO")):
            return "dvd", path
        return None
    if path.lower().endswith(DISC_EXT) and os.path.isfile(path):
        return iso_kind(path), path
    return None


def iso_kind(path: str) -> str:
    """Blu-ray or DVD image: look for the BDMV / VIDEO_TS names in the file system area of the image."""
    try:
        with open(path, "rb") as f:
            head = f.read(48 << 20)
        if b"VIDEO_TS" in head and b"BDMV" not in head:
            return "dvd"
        if b"BDMV" in head:
            return "bd"
        return "bd" if os.path.getsize(path) > 9_000_000_000 else "dvd"
    except OSError:
        return "bd"


class Bridge(QObject):
    """mpv calls back from its own thread; everything is handed to the GUI thread through signals."""
    prop = Signal(str, object)
    loaded = Signal()
    failed = Signal(int)                 # end-file with an error (mpv error code)
    update = Signal(object, str)         # update check: info or None, error text


class Stage(QWidget):
    """Holds the video and the overlays; keeps the overlays laid out over the picture."""
    def __init__(self, win: "PlayerWindow"):
        super().__init__()
        self.win = win
        self.setMouseTracking(True)
        self.setObjectName("stage")
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("QWidget#stage { background: #000000; }")
        self.toast_top = 24

    def resizeEvent(self, e):
        self.win.layout_overlays()


class PlayerWindow(QMainWindow):
    def __init__(self, mpv_module, cfg: dict):
        super().__init__()
        self.cfg = cfg
        self.mpvmod = mpv_module
        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(style.app_icon())
        self.setAcceptDrops(True)
        self.resize(1280, 760)
        self.setMinimumSize(560, 340)
        self.playlist: list[str] = []
        self.index = -1
        self.path = ""
        self.duration = 0.0
        self.position = 0.0
        self.paused = True
        self.tracks: list[dict] = []
        self._resume_note = ""
        self._last_seek_ui = 0.0
        self._was_maximized = False

        self.bridge = Bridge()
        self.bridge.prop.connect(self._on_prop)
        self.bridge.loaded.connect(self._on_loaded)
        self.bridge.failed.connect(self._on_failed)
        self.bridge.update.connect(self._on_update_result)
        self.update_info: dict | None = None
        self._af = None
        self._chapters: list[dict] = []
        self.disc: tuple[str, str] | None = None
        self.disc_title: int | None = None      # None = the longest title (the film)
        self.mpv = self._make_mpv()

        # ── stage: video + overlays
        self.stage = Stage(self)
        self.setCentralWidget(self.stage)
        self.video = VideoWidget(mpv_module, self.mpv, self.stage)
        self.video.clicked.connect(self.toggle_pause)
        self.video.double_clicked.connect(self.toggle_fullscreen)
        self.video.context_menu.connect(self.show_context_menu)
        self.video.wheel.connect(lambda d: self.change_volume(5 * d))
        self.video.moved.connect(self.poke)
        self.video.ready.connect(self._video_ready)
        self._pending_index: int | None = None

        self.start = StartPage(cfg, self.stage)
        self.start.open_file.connect(self.open_dialog)
        self.start.open_folder.connect(self.open_folder_dialog)
        self.start.open_recent.connect(lambda p: self.open_paths([p]))

        self._build_top()
        self._build_controls()
        self.bubble = SeekPreview(self.stage)
        self.bubble.want_images = bool(cfg.get("thumbs", True))
        from .thumbs import Thumbnailer
        self.thumbs = Thumbnailer(mpv_module, bool(cfg.get("hwdec", True)))
        self.thumbs.ready.connect(self._thumb_ready)
        self._hover = (-1.0, -1)              # bucket under the mouse, x
        self.toast = Toast(self.stage)
        self.pulse = Pulse(self.stage)
        self.plpanel = PlaylistPanel(self.stage)
        self.plpanel.play.connect(self.play_index)
        self.plpanel.close_btn.clicked.connect(lambda: self.toggle_playlist(False))

        self.idle = QTimer(self)
        self.idle.setSingleShot(True)
        self.idle.setInterval(2600)
        self.idle.timeout.connect(self._hide_overlays)
        QApplication.instance().installEventFilter(self)

        self.ui_timer = QTimer(self)         # time label / seek bar at a calm rate
        self.ui_timer.setInterval(250)
        self.ui_timer.timeout.connect(self._refresh_time)
        self.ui_timer.start()

        if cfg.get("on_top"):
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self._set_idle_view(True)
        self.layout_overlays()

    # ── mpv ───────────────────────────────────────────────────
    def _make_mpv(self):
        cfg = self.cfg
        shots = cfg.get("screenshot_dir") or os.path.join(winint.pictures_dir(), "ArtCore Player")
        m = self.mpvmod.MPV(
            vo="libmpv", hwdec="auto-safe" if cfg.get("hwdec", True) else "no",
            keep_open="yes", idle="yes", osc=False, input_default_bindings=False, input_vo_keyboard=False,
            config=False, terminal=False, ytdl=False,
            volume=int(cfg.get("volume", 80)), mute=bool(cfg.get("muted")), volume_max=150,
            sub_auto="fuzzy", audio_file_auto="fuzzy", alang=cfg.get("alang", ""), slang=cfg.get("slang", ""),
            screenshot_directory=shots, screenshot_template="%F_%wH-%wM-%wS", screenshot_format="png",
            osd_font_size=30, osd_bar=False, sub_font_size=46, sub_border_size=2.6, sub_shadow_offset=1,
            demuxer_max_bytes="400MiB", demuxer_max_back_bytes="100MiB", cache="auto",
            hr_seek="yes", hr_seek_framedrop=True,
            gpu_shader_cache_dir=os.path.join(config.data_dir(), "shader-cache"),   # not shared with mpv itself
        )
        for name in OBSERVED:
            m.observe_property(name, lambda n, v: self.bridge.prop.emit(n, v))
        m.event_callback("file-loaded")(lambda _e: self.bridge.loaded.emit())

        def end_file(ev):
            try:
                d = ev.data
                if d.reason == self.mpvmod.MpvEventEndFile.ERROR:
                    self.bridge.failed.emit(int(d.error))
            except Exception:
                pass
        m.event_callback("end-file")(end_file)
        return m

    def _get(self, name, default=None):
        """A playback property (mpv["x"] in python-mpv would read the *option* x instead)."""
        try:
            v = getattr(self.mpv, name.replace("-", "_"))
            return default if v is None else v
        except Exception:
            return default

    # ── building the overlays ─────────────────────────────────
    def _build_top(self):
        self.top = GradientPanel(False, self.stage)
        lay = QHBoxLayout(self.top)
        lay.setContentsMargins(20, 12, 14, 34)
        lay.setSpacing(8)
        col = QVBoxLayout()
        col.setSpacing(1)
        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("title")
        col.addWidget(self.title_lbl)
        self.chapter_lbl = QLabel()
        self.chapter_lbl.setStyleSheet("color: rgba(255,255,255,190); font-size: 9.5pt; background: transparent;")
        self.chapter_lbl.setCursor(Qt.PointingHandCursor)
        self.chapter_lbl.setToolTip(t("chapters") + " (PgUp / PgDn)")
        self.chapter_lbl.mousePressEvent = lambda e: self._chapters_popup(e.globalPosition().toPoint())
        self.chapter_lbl.hide()
        col.addWidget(self.chapter_lbl)
        lay.addLayout(col, 1)
        self.upd_btn = QPushButton(style.icon("fa6s.circle-arrow-up", "#ffffff"), "")
        self.upd_btn.setObjectName("primary")
        self.upd_btn.setCursor(Qt.PointingHandCursor)
        self.upd_btn.setFocusPolicy(Qt.NoFocus)
        self.upd_btn.clicked.connect(self.show_update)
        self.upd_btn.hide()
        lay.addWidget(self.upd_btn)
        self.badges = QHBoxLayout()
        self.badges.setSpacing(6)
        lay.addLayout(self.badges)
        self.top_close = ctl_button("fa6s.xmark", t("close_file"), 16, self.close_file)
        lay.addWidget(self.top_close)

    def _build_controls(self):
        self.ctl = GradientPanel(True, self.stage)
        v = QVBoxLayout(self.ctl)
        v.setContentsMargins(16, 30, 16, 10)
        v.setSpacing(2)
        self.seekbar = SeekBar()
        self.seekbar.seek.connect(self._seek_from_bar)
        self.seekbar.hover.connect(self._seek_hover)
        v.addWidget(self.seekbar)
        row = QHBoxLayout()
        row.setSpacing(2)
        self.b_prev = ctl_button("fa6s.backward-step", t("prev") + " (PgUp)", 18, self.play_prev)
        self.b_back = ctl_button("fa6s.rotate-left", t("back10") + " (←)", 18, lambda: self.seek_rel(-10))
        self.b_play = ctl_button("fa6s.play", t("play") + " (Space)", 24, self.toggle_pause)
        self.b_fwd = ctl_button("fa6s.rotate-right", t("fwd10") + " (→)", 18, lambda: self.seek_rel(10))
        self.b_next = ctl_button("fa6s.forward-step", t("next") + " (PgDn)", 18, self.play_next)
        for b in (self.b_prev, self.b_back, self.b_play, self.b_fwd, self.b_next):
            row.addWidget(b)
        self.b_vol = ctl_button("fa6s.volume-high", t("mute") + " (M)", 18, self.toggle_mute)
        row.addSpacing(6)
        row.addWidget(self.b_vol)
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setObjectName("volume")
        self.vol.setRange(0, 150)
        self.vol.setFixedWidth(96)
        self.vol.setFocusPolicy(Qt.NoFocus)
        self.vol.setValue(int(self.cfg.get("volume", 80)))
        self.vol.valueChanged.connect(self._vol_slider)
        row.addWidget(self.vol)
        self.time_lbl = QLabel("0:00 / 0:00")
        self.time_lbl.setObjectName("time")
        self.time_lbl.setCursor(Qt.PointingHandCursor)
        self.time_lbl.setToolTip(t("time_tip"))
        self.time_lbl.mousePressEvent = lambda _e: self._toggle_remaining()
        row.addSpacing(8)
        row.addWidget(self.time_lbl)
        row.addStretch(1)
        self.b_speed = ctl_button("fa6s.gauge-high", t("speed"), 18)
        self.b_speed.setObjectName("ctlText")
        self.b_speed.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.b_speed.setText("1×")
        self.b_speed.setPopupMode(self.b_speed.ToolButtonPopupMode.InstantPopup)
        self.b_speed.setMenu(self._lazy_menu(self._fill_speed_menu))
        self.b_audio = ctl_button("fa6s.headphones", t("audio") + " (A)", 18)
        self.b_audio.setPopupMode(self.b_audio.ToolButtonPopupMode.InstantPopup)
        self.b_audio.setMenu(self._lazy_menu(self._fill_audio_menu))
        self.b_subs = ctl_button("fa6s.closed-captioning", t("subs") + " (S)", 18)
        self.b_subs.setPopupMode(self.b_subs.ToolButtonPopupMode.InstantPopup)
        self.b_subs.setMenu(self._lazy_menu(self._fill_subs_menu))
        self.b_list = ctl_button("fa6s.list-ul", t("playlist") + " (L)", 18, lambda: self.toggle_playlist())
        self.b_more = ctl_button("fa6s.sliders", t("more"), 18)
        self.b_more.setPopupMode(self.b_more.ToolButtonPopupMode.InstantPopup)
        self.b_more.setMenu(self._lazy_menu(self._fill_more_menu))
        self.b_full = ctl_button("fa6s.expand", t("fullscreen") + " (F)", 18, self.toggle_fullscreen)
        for b in (self.b_speed, self.b_audio, self.b_subs, self.b_list, self.b_more, self.b_full):
            row.addWidget(b)
        v.addLayout(row)

    def _lazy_menu(self, fill) -> QMenu:
        m = QMenu(self)
        m.aboutToShow.connect(lambda: (m.clear(), fill(m)))
        m.aboutToShow.connect(self.poke)
        return m

    def layout_overlays(self):
        w, h = self.stage.width(), self.stage.height()
        self.video.setGeometry(0, 0, w, h)
        self.start.setGeometry(0, 0, w, h)
        self.top.setGeometry(0, 0, w, 86)
        ch = self.ctl.sizeHint().height()
        self.ctl.setGeometry(0, h - ch, w, ch)
        pw = min(380, max(260, w // 3))
        self.plpanel.setGeometry(w - pw, 0, pw, h - (ch if self.ctl.isVisible() else 0))
        self.stage.toast_top = 70 if self.top.isVisible() else 24
        self.pulse.move((w - self.pulse.width()) // 2, (h - self.pulse.height()) // 2)
        for wdg in (self.top, self.ctl, self.plpanel, self.bubble, self.toast, self.pulse):
            wdg.raise_()

    # ── idle: hide controls and the cursor while watching ─────
    def eventFilter(self, obj, e):
        if e.type() == e.Type.MouseMove and self.isActiveWindow():
            self.poke()
        return False

    def poke(self):
        if not self.path:
            return
        if not self.ctl.isVisible():
            self.top.setVisible(True)
            self.ctl.setVisible(True)
            self.layout_overlays()
        self._sub_room(True)
        if self.stage.cursor().shape() == Qt.BlankCursor:
            self.stage.unsetCursor()
            self.video.unsetCursor()
        self.idle.start()

    def _hide_overlays(self):
        if not self.path or self.paused or QApplication.activePopupWidget() is not None:
            self.idle.start()
            return
        local = self.stage.mapFromGlobal(QCursor.pos())
        if self.ctl.isVisible() and self.ctl.geometry().contains(local) and self.stage.rect().contains(local):
            self.idle.start()                      # the mouse rests on the controls
            return
        if self.plpanel.isVisible() and self.plpanel.geometry().contains(local):
            self.idle.start()
            return
        self.top.hide()
        self.ctl.hide()
        self.bubble.hide()
        self.layout_overlays()
        self._sub_room(False)
        self.video.setCursor(Qt.BlankCursor)
        self.stage.setCursor(Qt.BlankCursor)

    def _sub_room(self, controls: bool):
        """Lift the subtitles above the control bar while it is shown (and drop them back after)."""
        h = max(1, self.stage.height())
        pos = 100 if not controls else max(70, min(100, int(100 - 100 * (self.ctl.height() + 6) / h)))
        if pos != getattr(self, "_sub_pos", None):
            self._sub_pos = pos
            try:
                self.mpv.sub_pos = pos
            except Exception:
                pass

    def _set_idle_view(self, idle: bool):
        self.start.setVisible(idle)
        self.top.setVisible(not idle)
        self.ctl.setVisible(not idle)
        if idle:
            self.start.refresh()
            self.plpanel.hide()
            self.setWindowTitle(APP_TITLE)
            self.video.unsetCursor()
            self.stage.unsetCursor()
        self.layout_overlays()

    # ── opening files ─────────────────────────────────────────
    def open_dialog(self):
        exts = " ".join("*" + e for e in MEDIA_EXT)
        files, _ = QFileDialog.getOpenFileNames(self, t("open_file"), self.cfg.get("last_dir") or "",
                                                f"{t('media_files')} ({exts});;{t('disc_images')} (*.iso);;"
                                                f"{t('all_files')} (*)")
        if files:
            self.open_paths(files)

    def open_folder_dialog(self):
        d = QFileDialog.getExistingDirectory(self, t("open_folder"), self.cfg.get("last_dir") or "")
        if d:
            if disc_of(d):
                self.cfg["last_dir"] = os.path.dirname(os.path.normpath(d))
                self._start_playlist([d], 0)
                return
            items = media_in(d)
            if items:
                self.cfg["last_dir"] = d
                self._start_playlist(items, 0)
            else:
                self.toast.show_text(t("no_media"))

    def open_paths(self, paths: list[str]):
        """One file → its folder becomes the playlist; several → exactly those; subtitles → loaded."""
        paths = [p for p in paths if p]
        subs = [p for p in paths if p.lower().endswith(SUB_EXT)]
        media = [p for p in paths if not p.lower().endswith(SUB_EXT)]
        if subs and self.path and not media:
            for s in subs:
                self.mpv.command("sub-add", s, "select")
            self.toast.show_text(t("sub_loaded", os.path.basename(subs[0])))
            return
        discs = [p for p in media if os.path.isdir(p) and disc_of(p)]
        if discs:                                   # a Blu-ray / DVD folder: play the disc, not its files
            self._start_playlist([os.path.abspath(p) for p in discs], 0)
            return
        folders = [p for p in media if os.path.isdir(p)]
        if folders and len(media) == 1:
            items = media_in(folders[0])
            if items:
                self._start_playlist(items, 0)
            return
        media = [p for p in media if not os.path.isdir(p)]
        if not media:
            return
        if len(media) == 1 and os.path.isfile(media[0]):
            folder_items = media_in(os.path.dirname(os.path.abspath(media[0])))
            target = os.path.normcase(os.path.abspath(media[0]))
            idx = next((i for i, p in enumerate(folder_items) if os.path.normcase(p) == target), -1)
            if idx < 0:
                folder_items, idx = [os.path.abspath(media[0])], 0
            self._start_playlist(folder_items, idx)
        else:
            self._start_playlist([os.path.abspath(p) if os.path.exists(p) else p for p in media], 0)
        self.cfg["last_dir"] = os.path.dirname(os.path.abspath(media[0])) if os.path.exists(media[0]) else ""

    def _start_playlist(self, items: list[str], idx: int):
        self.playlist = items
        self.play_index(idx)

    def _video_ready(self):
        if self._pending_index is not None:
            idx, self._pending_index = self._pending_index, None
            self.play_index(idx)

    def play_index(self, idx: int):
        if not (0 <= idx < len(self.playlist)):
            return
        if self.video.ctx is None:
            # libmpv's video output needs the render context first, or the file plays without a picture
            self._pending_index = idx
            self.video.show()
            self.video.update()
            return
        self._save_position()
        self.index = idx
        self.path = self.playlist[idx]
        self.duration = self.position = 0.0
        self._resume_note = ""
        config.add_recent(self.cfg, self.path)
        config.save(self.cfg)
        self._set_idle_view(False)
        self.title_lbl.setText(os.path.basename(self.path))
        self.setWindowTitle(f"{os.path.basename(self.path)} — {APP_TITLE}")
        self._clear_badges()
        self._chapters = []
        self.chapter_lbl.hide()
        self.mpv.pause = False
        self.disc = disc_of(self.path)
        self.thumbs.set_file(self.path, False)
        if self.disc:
            kind, dev = self.disc
            name = os.path.basename(os.path.normpath(dev))
            self.title_lbl.setText(f"{'Blu-ray' if kind == 'bd' else 'DVD'} · {name}")
            self.setWindowTitle(f"{name} — {APP_TITLE}")
            try:
                if kind == "bd":
                    self.mpv.bluray_device = dev
                else:
                    self.mpv.dvd_device = dev
            except Exception:
                pass
            self.disc_title = None
            self.mpv.play(f"{kind}://longest")
        else:
            self.mpv.play(self.path)
        self.plpanel.set_items(self.playlist, self.index)
        self.b_prev.setEnabled(idx > 0)
        self.b_next.setEnabled(idx < len(self.playlist) - 1)
        self.poke()

    def play_next(self):
        if self.index < len(self.playlist) - 1:
            self.play_index(self.index + 1)

    def play_prev(self):
        if self.position > 5 or self.index <= 0:
            self.seek_abs(0)
        else:
            self.play_index(self.index - 1)

    def close_file(self):
        self._save_position()
        config.save(self.cfg)
        self.mpv.command("stop")
        self.path = ""
        self.index = -1
        self.paused = True
        self._set_idle_view(True)

    # ── resume ────────────────────────────────────────────────
    def _save_position(self):
        if not self.path or not self.cfg.get("resume", True):
            return
        if self.disc and self.disc_title is not None:
            return                                 # extras of a disc: only the film keeps its place
        pos, dur = self._get("time-pos"), self._get("duration")
        if pos is None or not dur:
            return
        keep = dur > 120 and 30 < pos < dur - 45
        config.set_position(self.cfg, self.path, pos if keep else None)

    def _on_loaded(self):
        self.duration = float(self._get("duration", 0) or 0)
        pos = self.cfg.get("positions", {}).get(self.path)
        if self.cfg.get("resume", True) and pos and self.duration and pos < self.duration - 10:
            self.mpv.command("seek", pos, "absolute")
            self._resume_note = fmt_time(pos)
            self.toast.show_text(t("resumed", fmt_time(pos)), 3500)
        self._update_badges()
        self._af = None
        self.apply_audio(quiet=True)

    def _on_failed(self, code: int):
        if not self.path:
            return
        name = os.path.basename(os.path.normpath(self.path))
        if self.disc and self.disc_title is not None:
            self.toast.show_text(t("title_none", self.disc_title + 1), 3000)
        elif self.disc:
            self.toast.show_text(t("disc_fail", name), 6000)
        else:
            self.toast.show_text(t("open_fail", name), 5000)
        self.poke()

    # ── mpv → UI ──────────────────────────────────────────────
    def _on_prop(self, name: str, val):
        if name == "pause":
            self.paused = bool(val)
            self.b_play.setIcon(style.icon("fa6s.play" if self.paused else "fa6s.pause", "#ffffff"))
            self.b_play.setToolTip((t("play") if self.paused else t("pause")) + " (Space)")
            if self.paused:
                self.poke()
                self.idle.stop()
            else:
                self.idle.start()
        elif name == "duration":
            self.duration = float(val or 0)
        elif name == "volume" and val is not None:
            self.vol.blockSignals(True)
            self.vol.setValue(int(round(val)))
            self.vol.blockSignals(False)
            self.cfg["volume"] = int(round(val))
            self._vol_icon()
        elif name == "mute":
            self.cfg["muted"] = bool(val)
            self._vol_icon()
        elif name == "track-list":
            self.tracks = list(val or [])
            self._update_badges()
        elif name in ("video-params", "audio-params"):
            self._update_badges()
            if name == "video-params" and val and self.path:
                self.thumbs.set_file(self.path, str(val.get("gamma") or "") in ("pq", "hlg"))
            if name == "audio-params":
                self.apply_audio(quiet=True)
        elif name == "chapter-list":
            self._chapters = list(val or [])
            self.seekbar.chapters = [float(c.get("time", 0)) for c in self._chapters]
            self.seekbar.update()
            self._update_chapter_label()
        elif name == "chapter":
            self._update_chapter_label()
        elif name == "demuxer-cache-state":
            rng = (val or {}).get("seekable-ranges") or []
            self.seekbar.cached = [(float(r.get("start", 0)), float(r.get("end", 0))) for r in rng]
        elif name == "speed" and val is not None:
            self.b_speed.setText(f"{val:g}×")
        elif name == "eof-reached" and val:
            self._on_eof()
        elif name == "media-title" and val and self.path and not os.path.exists(self.path):
            self.title_lbl.setText(str(val))

    def _on_eof(self):
        config.set_position(self.cfg, self.path, None)         # watched to the end
        config.save(self.cfg)
        if self.cfg.get("autoplay_next", True) and self.index < len(self.playlist) - 1:
            self.toast.show_text(t("next_file", os.path.basename(self.playlist[self.index + 1])), 2500)
            QTimer.singleShot(400, self.play_next)
        else:
            self.poke()

    def _refresh_time(self):
        if not self.path:
            return
        pos = self._get("time-pos")
        if pos is None:
            return
        self.position = float(pos)
        if time.monotonic() - self._last_seek_ui > 0.3:
            self.seekbar.set_state(self.position, self.duration)
        dur = self.duration
        force_h = dur >= 3600
        if self.cfg.get("remaining_time") and dur:
            right = "-" + fmt_time(max(0.0, dur - self.position), force_h)
        else:
            right = fmt_time(dur, force_h)
        self.time_lbl.setText(f"{fmt_time(self.position, force_h)} / {right}")

    def _toggle_remaining(self):
        self.cfg["remaining_time"] = not self.cfg.get("remaining_time")
        self._refresh_time()

    # ── badges: 4K · HDR · HEVC · 5.1 ─────────────────────────
    def _clear_badges(self):
        while self.badges.count():
            w = self.badges.takeAt(0).widget()
            if w:
                w.deleteLater()

    def _update_badges(self):
        if not self.path:
            return
        self._clear_badges()
        vp = self._get("video-params", {}) or {}
        ap = self._get("audio-params", {}) or {}
        vt = next((tr for tr in self.tracks if tr.get("type") == "video" and tr.get("selected")), {})
        at = next((tr for tr in self.tracks if tr.get("type") == "audio" and tr.get("selected")), {})
        out = []
        h = int(vp.get("h") or vt.get("demux-h") or 0)
        w = int(vp.get("w") or vt.get("demux-w") or 0)
        if w >= 3800 or h >= 2100:
            out.append(("4K", False))
        elif w >= 2500 or h >= 1400:
            out.append(("1440p", False))
        elif w >= 1900 or h >= 1060:
            out.append(("1080p", False))
        elif h >= 700:
            out.append(("720p", False))
        elif h:
            out.append((f"{h}p", False))
        dv = vt.get("dolby-vision-profile")
        gamma = str(vp.get("gamma") or "")
        if dv:
            out.append((f"Dolby Vision {dv}", True))
        elif gamma == "pq":
            out.append(("HDR10", True))
        elif gamma == "hlg":
            out.append(("HLG", True))
        codec = str(vt.get("codec") or "").upper().replace("H264", "AVC")
        if codec:
            out.append(({"HEVC": "HEVC", "AVC": "AVC", "AV1": "AV1", "VP9": "VP9"}.get(codec, codec[:8]), False))
        ch = int(ap.get("channel-count") or at.get("demux-channel-count") or 0)
        if ch:
            out.append(({1: "1.0", 2: "2.0", 3: "2.1", 6: "5.1", 7: "6.1", 8: "7.1"}.get(ch, f"{ch}ch"), False))
        acodec = str(at.get("codec") or "").upper()
        if acodec in ("TRUEHD", "DTS", "EAC3", "AC3", "FLAC", "OPUS", "AAC"):
            out.append(({"EAC3": "DD+", "AC3": "DD", "TRUEHD": "TrueHD"}.get(acodec, acodec), False))
        for text, hdr in out:
            lab = QLabel(text)
            lab.setObjectName("badgeHdr" if hdr else "badge")
            self.badges.addWidget(lab)

    # ── commands ──────────────────────────────────────────────
    def toggle_pause(self):
        if not self.path:
            self.open_dialog()
            return
        if self._get("eof-reached") and self.paused:
            self.seek_abs(0)
        self.mpv.pause = not self.paused
        self.pulse.pulse("fa6s.pause" if not self.paused else "fa6s.play")

    def seek_rel(self, sec: float):
        if not self.path:
            return
        self.mpv.command("seek", sec, "relative+exact")
        sign = "+" if sec > 0 else "−"
        self.toast.show_text(f"{sign}{fmt_time(abs(sec))}   ·   {fmt_time(max(0.0, self.position + sec))}", 900)
        self.poke()

    def seek_abs(self, sec: float):
        if self.path:
            self.mpv.command("seek", max(0.0, sec), "absolute+exact")

    def _seek_from_bar(self, sec: float, exact: bool):
        self._last_seek_ui = time.monotonic()
        self.seekbar.set_state(sec, self.duration)
        self.mpv.command("seek", sec, "absolute+exact" if exact else "absolute+keyframes")

    def _chapter_at(self, sec: float) -> tuple[int, str]:
        idx, name = -1, ""
        for i, c in enumerate(self._chapters):
            if float(c.get("time", 0)) <= sec + 0.01:
                idx, name = i, c.get("title") or ""
        return idx, name

    def _thumb_step(self) -> float:
        return max(2.0, self.duration / 400) if self.duration else 2.0

    def _thumbs_ok(self) -> bool:
        return bool(self.cfg.get("thumbs", True)) and not self.disc and os.path.isfile(self.path)

    def _seek_hover(self, sec: float, x: int):
        if sec < 0:
            self.bubble.hide()
            self._hover = (-1.0, -1)
            return
        step = self._thumb_step()
        bucket = round(sec / step) * step
        self._hover = (bucket, x)
        img = self.thumbs.request(sec, bucket) if self._thumbs_ok() else None
        self._show_preview(sec, x, img)

    def _frame_size(self) -> QSize | None:
        if not self._thumbs_ok():
            return None
        vp = self._get("video-params", {}) or {}
        w, h = int(vp.get("dw") or vp.get("w") or 16), int(vp.get("dh") or vp.get("h") or 9)
        fw = 224
        return QSize(fw, max(60, min(170, int(fw * h / max(1, w)))))

    def _show_preview(self, sec: float, x: int, img):
        idx, name = self._chapter_at(sec)
        chap = (name or t("chapter_n", idx + 1)) if idx >= 0 and len(self._chapters) > 1 else ""
        self.bubble.want_images = self._thumbs_ok()
        self.bubble.set_content(fmt_time(sec, self.duration >= 3600), chap, img, self._frame_size())
        gp = self.seekbar.mapTo(self.stage, QPoint(x, 0))
        bx = max(6, min(self.stage.width() - self.bubble.width() - 6, gp.x() - self.bubble.width() // 2))
        self.bubble.move(bx, gp.y() - self.bubble.height() - 6)
        self.bubble.show()
        self.bubble.raise_()

    def _thumb_ready(self, path: str, bucket: float, img):
        if path == self.path and self.bubble.isVisible() and abs(bucket - self._hover[0]) < 1e-6:
            self._show_preview(bucket, self._hover[1], img)

    # ── chapters ──────────────────────────────────────────────
    def chapter_step(self, d: int) -> bool:
        if len(self._chapters) < 2:
            return False
        self.mpv.command("add", "chapter", d)
        QTimer.singleShot(200, self._announce_chapter)
        return True

    def _announce_chapter(self):
        i = self._get("chapter", -1)
        if i is not None and 0 <= i < len(self._chapters):
            name = self._chapters[i].get("title") or ""
            self.toast.show_text(t("chapter_toast", i + 1, len(self._chapters)) + (f" · {name}" if name else ""), 1600)

    def _update_chapter_label(self):
        i = self._get("chapter", -1)
        if len(self._chapters) > 1 and i is not None and 0 <= i < len(self._chapters):
            name = self._chapters[i].get("title") or ""
            self.chapter_lbl.setText(t("chapter_toast", i + 1, len(self._chapters)) + (f"  ·  {name}" if name else ""))
            self.chapter_lbl.show()
        else:
            self.chapter_lbl.hide()

    def _fill_chapters_menu(self, m: QMenu):
        cur = self._get("chapter", -1)
        grp = QActionGroup(m)
        force_h = self.duration >= 3600
        for i, c in enumerate(self._chapters):
            tm = float(c.get("time", 0))
            a = m.addAction(f"{fmt_time(round(tm), force_h)}   {c.get('title') or t('chapter_n', i + 1)}")
            a.setCheckable(True)
            a.setChecked(i == cur)
            a.triggered.connect(lambda _=False, i=i: (setattr(self.mpv, "chapter", i), self.poke()))
            grp.addAction(a)
        if not self._chapters:
            m.addAction(t("no_chapters")).setEnabled(False)

    def _chapters_popup(self, pos: QPoint):
        m = QMenu(self)
        self._fill_chapters_menu(m)
        m.exec(pos)

    def change_volume(self, delta: int):
        if not self.path:
            return
        v = max(0, min(150, int(round(self._get("volume", 80))) + delta))
        self.mpv.volume = v
        if self._get("mute"):
            self.mpv.mute = False
        self.toast.show_text(t("volume_v", v), 900)

    def _vol_slider(self, v: int):
        self.mpv.volume = v
        if self._get("mute") and v:
            self.mpv.mute = False

    def toggle_mute(self):
        self.mpv.mute = not self._get("mute", False)
        self.toast.show_text(t("muted") if self.mpv.mute else t("volume_v", int(self._get("volume", 0))), 900)

    def _vol_icon(self):
        v = self.vol.value()
        muted = bool(self.cfg.get("muted"))
        name = "fa6s.volume-xmark" if muted or v == 0 else "fa6s.volume-low" if v < 50 else "fa6s.volume-high"
        self.b_vol.setIcon(style.icon(name, "#ffffff"))

    def set_speed(self, s: float):
        self.mpv.speed = s
        self.toast.show_text(t("speed_v", f"{s:g}"), 900)

    def step_speed(self, up: bool):
        cur = float(self._get("speed", 1.0))
        nxt = [s for s in SPEEDS if (s > cur + 1e-6 if up else s < cur - 1e-6)]
        if nxt:
            self.set_speed(nxt[0] if up else nxt[-1])

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized() if self._was_maximized else self.showNormal()
            self.b_full.setIcon(style.icon("fa6s.expand", "#ffffff"))
        else:
            self._was_maximized = self.isMaximized()
            self.showFullScreen()
            self.b_full.setIcon(style.icon("fa6s.compress", "#ffffff"))
        self.poke()

    def toggle_playlist(self, on: bool | None = None):
        on = not self.plpanel.isVisible() if on is None else on
        if on and not self.playlist:
            return
        self.plpanel.set_items(self.playlist, self.index)
        self.plpanel.setVisible(on)
        self.layout_overlays()

    def toggle_on_top(self):
        on = not self.cfg.get("on_top")
        self.cfg["on_top"] = on
        geo = self.geometry()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, on)
        self.show()
        self.setGeometry(geo)
        self.toast.show_text(t("on_top_on") if on else t("on_top_off"))

    def screenshot(self):
        if not self.path:
            return
        try:
            folder = self._get("screenshot-directory") or ""
            if folder:
                os.makedirs(os.path.expanduser(folder), exist_ok=True)
            self.mpv.command("screenshot", "subtitles")
            self.toast.show_text(t("shot_saved", folder or "~"), 2200)
        except Exception as e:
            self.toast.show_text(t("shot_fail", e), 2500)

    def toggle_stats(self):
        try:
            self.mpv.command("script-binding", "stats/display-stats-toggle")
        except Exception:
            self.toast.show_text(t("stats_na"))

    def cycle(self, kind: str):
        items = [tr for tr in self.tracks if tr.get("type") == kind]
        if not items:
            self.toast.show_text(t("no_audio") if kind == "audio" else t("no_subs"))
            return
        self.mpv.command("cycle", "aid" if kind == "audio" else "sid")
        QTimer.singleShot(150, lambda: self._announce_track(kind))

    def _announce_track(self, kind: str):
        sel = next((tr for tr in self._get("track-list", []) if tr.get("type") == kind and tr.get("selected")), None)
        label = self._track_label(sel) if sel else t("off")
        self.toast.show_text((t("audio") if kind == "audio" else t("subs")) + ": " + label, 1500)

    # ── menus ─────────────────────────────────────────────────
    @staticmethod
    def _track_label(tr: dict) -> str:
        parts = []
        if tr.get("title"):
            parts.append(str(tr["title"]))
        lang = tr.get("lang")
        if lang and (not parts or lang_name(lang).lower() not in parts[0].lower()):
            parts.append(lang_name(lang))
        meta = []
        if tr.get("codec"):
            meta.append(str(tr["codec"]).upper().replace("SUBRIP", "SRT").replace("HDMV_PGS_SUBTITLE", "PGS"))
        ch = tr.get("demux-channel-count")
        if ch:
            meta.append({1: "1.0", 2: "2.0", 6: "5.1", 8: "7.1"}.get(int(ch), f"{ch}ch"))
        flags = []
        if tr.get("forced"):
            flags.append(t("forced"))
        if tr.get("external"):
            flags.append(t("external"))
        name = " · ".join(parts) or f"#{tr.get('id')}"
        tail = ", ".join(meta + flags)
        return f"{name}  ({tail})" if tail else name

    def _fill_tracks(self, m: QMenu, kind: str):
        items = [tr for tr in self.tracks if tr.get("type") == kind]
        grp = QActionGroup(m)
        if kind == "sub":
            a = m.addAction(t("off"))
            a.setCheckable(True)
            a.setChecked(not any(tr.get("selected") for tr in items))
            a.triggered.connect(lambda: setattr(self.mpv, "sid", "no"))
            grp.addAction(a)
        for tr in items:
            a = m.addAction(self._track_label(tr))
            a.setCheckable(True)
            a.setChecked(bool(tr.get("selected")))
            prop = "aid" if kind == "audio" else "sid"
            a.triggered.connect(lambda _=False, i=tr["id"], p=prop: setattr(self.mpv, p, i))
            grp.addAction(a)
        if kind == "audio" and not items:
            m.addAction(t("no_audio")).setEnabled(False)

    def apply_audio(self, quiet: bool = False):
        """Sound mode + equalizer → mpv's audio filter chain (rebuilt when the channel count changes)."""
        ap = self._get("audio-params", {}) or {}
        ch = int(ap.get("channel-count") or 2)
        layout = str(ap.get("channels") or "")
        af = audio.build(self.cfg.get("audio_mode", "off"), self.cfg.get("eq", [0] * 10), ch, layout)
        if af == self._af:
            return
        try:
            self.mpv.af = af
            self._af = af
        except Exception as e:
            self._af = None
            if not quiet:
                self.toast.show_text(t("af_fail", e), 2500)

    def set_audio_mode(self, mode: str):
        self.cfg["audio_mode"] = mode
        config.save(self.cfg)
        self.apply_audio()
        self.toast.show_text(t("sound") + ": " + t("am_" + mode), 1500)

    def _fill_sound_menu(self, m: QMenu):
        grp = QActionGroup(m)
        cur = self.cfg.get("audio_mode", "off")
        for mode in audio.MODES:
            a = m.addAction(t("am_" + mode))
            a.setCheckable(True)
            a.setChecked(mode == cur)
            a.setToolTip(t("am_" + mode + "_tip"))
            a.triggered.connect(lambda _=False, md=mode: self.set_audio_mode(md))
            grp.addAction(a)
        m.setToolTipsVisible(True)
        m.addSeparator()
        eq_on = any(self.cfg.get("eq", [0] * 10))
        m.addAction(style.icon("fa6s.sliders", "#6ea8fe" if eq_on else style.TEXT),
                    t("equalizer") + ("  ✓" if eq_on else "") + "…\tE", self.equalizer_dialog)

    def equalizer_dialog(self):
        from .dialogs import EqualizerDialog
        old = list(self.cfg.get("eq", [0] * 10))
        d = EqualizerDialog(self.cfg, self)
        d.changed.connect(lambda: self.apply_audio())
        if not d.exec():
            self.cfg["eq"] = old
            self.apply_audio()
        config.save(self.cfg)

    def _fill_audio_menu(self, m: QMenu):
        self._fill_tracks(m, "audio")
        m.addSeparator()
        self._fill_sound_menu(m.addMenu(style.icon("fa6s.wave-square"), t("sound")))
        m.addAction(style.icon("fa6s.file-audio"), t("load_audio"), self._load_audio)

    def _fill_subs_menu(self, m: QMenu):
        self._fill_tracks(m, "sub")
        m.addSeparator()
        m.addAction(style.icon("fa6s.file-lines"), t("load_subs"), self._load_subs)
        d = m.addMenu(style.icon("fa6s.clock"), t("sub_delay", f"{float(self._get('sub-delay', 0)):+.1f}"))
        for v, txt in ((-0.5, "−0.5 s  (Z)"), (-0.1, "−0.1 s"), (0.1, "+0.1 s"), (0.5, "+0.5 s  (X)")):
            d.addAction(txt, lambda v=v: self.shift_sub(v))
        d.addAction(t("reset"), lambda: self.shift_sub(None))
        sz = m.addMenu(style.icon("fa6s.text-height"), t("sub_size"))
        for v in (0.8, 0.9, 1.0, 1.15, 1.3, 1.5):
            a = sz.addAction(f"{int(v * 100)} %")
            a.setCheckable(True)
            a.setChecked(abs(float(self._get("sub-scale", 1.0)) - v) < 0.01)
            a.triggered.connect(lambda _=False, v=v: setattr(self.mpv, "sub_scale", v))

    def _fill_speed_menu(self, m: QMenu):
        cur = float(self._get("speed", 1.0))
        grp = QActionGroup(m)
        for s in SPEEDS:
            a = m.addAction(t("normal_speed") if s == 1.0 else f"{s:g}×")
            a.setCheckable(True)
            a.setChecked(abs(cur - s) < 1e-6)
            a.triggered.connect(lambda _=False, s=s: self.set_speed(s))
            grp.addAction(a)

    def play_disc_title(self, n: int | None):
        """mpv has no title list for discs any more: a title is chosen by loading bd://N / dvd://N again."""
        if not self.disc:
            return
        if n is not None and n < 0:
            return
        self._save_position()
        self.disc_title = n
        kind = self.disc[0]
        self.mpv.play(f"{kind}://{'longest' if n is None else n}")
        self.toast.show_text(t("main_film_on") if n is None else t("title_n", n + 1), 1800)

    def _fill_titles_menu(self, m: QMenu):
        cur = self.disc_title
        a = m.addAction(t("main_film"))
        a.setCheckable(True)
        a.setChecked(cur is None)
        a.triggered.connect(lambda: self.play_disc_title(None))
        m.addSeparator()
        if cur is not None:
            m.addAction(t("title_now", cur + 1)).setEnabled(False)
        nxt = 0 if cur is None else cur + 1
        m.addAction(style.icon("fa6s.forward-step"), t("title_next", nxt + 1), lambda: self.play_disc_title(nxt))
        if cur:
            m.addAction(style.icon("fa6s.backward-step"), t("title_prev", cur), lambda: self.play_disc_title(cur - 1))

    def _fill_more_menu(self, m: QMenu):
        if len(self._chapters) > 1:
            self._fill_chapters_menu(m.addMenu(style.icon("fa6s.bookmark"), t("chapters") + f" · {len(self._chapters)}"))
            m.addSeparator()
        if self.disc:
            self._fill_titles_menu(m.addMenu(style.icon("fa6s.compact-disc"), t("disc_titles")))
            m.addSeparator()
        asp = m.addMenu(style.icon("fa6s.crop"), t("aspect"))
        cur = str(self._get("video-aspect-override", "-1"))
        for val, txt in (("-1", t("aspect_auto")), ("16:9", "16:9"), ("4:3", "4:3"), ("2.35:1", "2.35:1"),
                         ("1.85:1", "1.85:1"), ("21:9", "21:9")):
            a = asp.addAction(txt)
            a.setCheckable(True)
            a.setChecked(cur == val or (val == "-1" and cur in ("-1", "-1.000000", "no")))
            a.triggered.connect(lambda _=False, v=val: setattr(self.mpv, "video_aspect_override", v))
        zoom = m.addMenu(style.icon("fa6s.magnifying-glass-plus"), t("zoom"))
        for val, txt in ((0, "100 %"), (0.1, "110 %"), (0.2, "120 %"), (0.33, "133 % — " + t("zoom_crop"))):
            zoom.addAction(txt, lambda v=val: setattr(self.mpv, "video_zoom", v))
        m.addSeparator()
        a = m.addAction(style.icon("fa6s.thumbtack"), t("on_top") + "\tT", self.toggle_on_top)
        a.setCheckable(True)
        a.setChecked(bool(self.cfg.get("on_top")))
        m.addAction(style.icon("fa6s.camera"), t("screenshot") + "\tCtrl+S", self.screenshot)
        m.addAction(style.icon("fa6s.circle-info"), t("stats") + "\tI", self.toggle_stats)
        if self.path and os.path.exists(self.path):
            m.addAction(style.icon("fa6s.folder-open"), t("show_in_folder"), lambda: winint.show_in_explorer(self.path))
        m.addSeparator()
        m.addAction(style.icon("fa6s.gear"), t("settings") + "\tCtrl+,", self.settings_dialog)
        m.addAction(style.icon("fa6s.keyboard"), t("keys") + "\tF1", self.keys_dialog)

    def show_context_menu(self, pos: QPoint):
        m = QMenu(self)
        m.addAction(style.icon("fa6s.file-video"), t("open_file") + "\tCtrl+O", self.open_dialog)
        m.addAction(style.icon("fa6s.folder-open"), t("open_folder"), self.open_folder_dialog)
        if self.path:
            m.addSeparator()
            m.addAction(style.icon("fa6s.pause" if not self.paused else "fa6s.play"),
                        (t("pause") if not self.paused else t("play")) + "\tSpace", self.toggle_pause)
            self._fill_audio_menu(m.addMenu(style.icon("fa6s.headphones"), t("audio")))
            self._fill_subs_menu(m.addMenu(style.icon("fa6s.closed-captioning"), t("subs")))
            self._fill_speed_menu(m.addMenu(style.icon("fa6s.gauge-high"), t("speed")))
            m.addSeparator()
            self._fill_more_menu(m)
            m.addSeparator()
            m.addAction(style.icon("fa6s.xmark"), t("close_file"), self.close_file)
        else:
            m.addSeparator()
            m.addAction(style.icon("fa6s.gear"), t("settings"), self.settings_dialog)
        m.exec(pos)

    def _load_subs(self):
        exts = " ".join("*" + e for e in SUB_EXT)
        f, _ = QFileDialog.getOpenFileName(self, t("load_subs"), os.path.dirname(self.path) if self.path else "",
                                           f"{t('subs')} ({exts})")
        if f:
            self.mpv.command("sub-add", f, "select")
            self.toast.show_text(t("sub_loaded", os.path.basename(f)))

    def _load_audio(self):
        exts = " ".join("*" + e for e in AUDIO_EXT)
        f, _ = QFileDialog.getOpenFileName(self, t("load_audio"), os.path.dirname(self.path) if self.path else "",
                                           f"{t('audio')} ({exts})")
        if f:
            self.mpv.command("audio-add", f, "select")

    def shift_sub(self, v: float | None):
        cur = float(self._get("sub-delay", 0))
        self.mpv.sub_delay = 0 if v is None else cur + v
        self.toast.show_text(t("sub_delay", f"{float(self._get('sub-delay', 0)):+.1f}"), 1100)

    # ── updates ───────────────────────────────────────────────
    UPDATE_EVERY = 24 * 3600

    def maybe_check_updates(self):
        from . import updater
        if self.cfg.get("check_updates", True) and updater.can_self_update() \
                and time.time() - float(self.cfg.get("last_update_check", 0)) > self.UPDATE_EVERY:
            self.check_updates()

    def check_updates(self, manual: bool = False):
        import threading
        from . import updater
        self._update_manual = manual
        self.cfg["last_update_check"] = int(time.time())
        config.save(self.cfg)

        def work():
            try:
                self.bridge.update.emit(updater.check(), "")
            except Exception as e:
                self.bridge.update.emit(None, str(e))
        threading.Thread(target=work, daemon=True).start()

    def _on_update_result(self, info, err: str):
        manual = getattr(self, "_update_manual", False)
        if err:
            if manual:
                QMessageBox.warning(self, APP_TITLE, t("upd_error", err))
            return
        if not info:
            if manual:
                QMessageBox.information(self, APP_TITLE, t("upd_none", VERSION))
            return
        self.update_info = info
        self.upd_btn.setText("  " + t("upd_available", info["version"]))
        self.upd_btn.show()
        self.start.show_update(info["version"], self.show_update)
        if manual:
            self.show_update()
        elif self.cfg.get("update_notified") != info["version"]:
            self.cfg["update_notified"] = info["version"]
            config.save(self.cfg)
            self.toast.show_text(t("upd_available", info["version"]), 4000)

    def show_update(self):
        info = self.update_info
        if not info:
            return
        from . import updater
        if not updater.can_self_update() or not info.get("url"):
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(info["page"]))
            return
        from .dialogs import UpdateDialog
        d = UpdateDialog(info, self)
        if d.exec() and d.path:
            self._installer = d.path
            self.cfg["reopen"] = self.path if self.path and os.path.exists(self.path) else ""
            self.close()

    # ── dialogs ───────────────────────────────────────────────
    def settings_dialog(self):
        from .dialogs import SettingsDialog
        d = SettingsDialog(self.cfg, self)
        if d.exec():
            config.save(self.cfg)
            try:
                self.mpv.hwdec = "auto-safe" if self.cfg.get("hwdec") else "no"
                self.mpv.alang = self.cfg.get("alang", "")
                self.mpv.slang = self.cfg.get("slang", "")
                if self.cfg.get("screenshot_dir"):
                    self.mpv.screenshot_directory = self.cfg["screenshot_dir"]
            except Exception:
                pass
            self.bubble.want_images = bool(self.cfg.get("thumbs", True))
            if d.lang_changed:
                QMessageBox.information(self, APP_TITLE, t("restart_lang"))

    def keys_dialog(self):
        from .dialogs import KeysDialog
        KeysDialog(self).exec()

    # ── keyboard ──────────────────────────────────────────────
    def keyPressEvent(self, e):
        k, mod = e.key(), e.modifiers()
        ctrl, shift = bool(mod & Qt.ControlModifier), bool(mod & Qt.ShiftModifier)
        step = 60 if shift else 10 if ctrl else 5
        if k in (Qt.Key_Space, Qt.Key_K, Qt.Key_MediaPlay, Qt.Key_MediaPause, Qt.Key_MediaTogglePlayPause):
            self.toggle_pause()
        elif k == Qt.Key_Right:
            self.seek_rel(step)
        elif k == Qt.Key_Left:
            self.seek_rel(-step)
        elif k == Qt.Key_Up:
            self.change_volume(5)
        elif k == Qt.Key_Down:
            self.change_volume(-5)
        elif k in (Qt.Key_F, Qt.Key_Return, Qt.Key_Enter) and not ctrl:
            self.toggle_fullscreen()
        elif k == Qt.Key_Escape:
            if self.isFullScreen():
                self.toggle_fullscreen()
            elif self.plpanel.isVisible():
                self.toggle_playlist(False)
        elif k == Qt.Key_M:
            self.toggle_mute()
        elif k == Qt.Key_A:
            self.cycle("audio")
        elif k == Qt.Key_S and ctrl:
            self.screenshot()
        elif k == Qt.Key_S:
            self.cycle("sub")
        elif k == Qt.Key_Z:
            self.shift_sub(-0.5 if not shift else -0.1)
        elif k == Qt.Key_X:
            self.shift_sub(0.5 if not shift else 0.1)
        elif k == Qt.Key_PageDown and not shift and self.chapter_step(1):
            pass                                   # chapters first; Shift+PgDn / N always go to the next file
        elif k == Qt.Key_PageUp and not shift and self.chapter_step(-1):
            pass
        elif k in (Qt.Key_PageDown, Qt.Key_N, Qt.Key_MediaNext):
            self.play_next()
        elif k in (Qt.Key_PageUp, Qt.Key_P, Qt.Key_MediaPrevious):
            self.play_prev()
        elif k == Qt.Key_C and self._chapters:
            self._chapters_popup(QCursor.pos())
        elif k == Qt.Key_E:
            self.equalizer_dialog()
        elif k == Qt.Key_D and not ctrl:
            self.set_audio_mode("off" if self.cfg.get("audio_mode", "off") == "dialog" else "dialog")
        elif k == Qt.Key_BracketRight:
            self.step_speed(True)
        elif k == Qt.Key_BracketLeft:
            self.step_speed(False)
        elif k == Qt.Key_Backspace:
            self.set_speed(1.0)
        elif k == Qt.Key_Period and self.path:
            self.mpv.command("frame-step")
        elif k == Qt.Key_Comma and self.path:
            self.mpv.command("frame-back-step")
        elif k == Qt.Key_Home:
            self.seek_abs(0)
            self.toast.show_text(t("from_start"))
        elif k == Qt.Key_I:
            self.toggle_stats()
        elif k == Qt.Key_L:
            self.toggle_playlist()
        elif k == Qt.Key_T:
            self.toggle_on_top()
        elif k == Qt.Key_O and ctrl:
            self.open_dialog()
        elif k == Qt.Key_W and ctrl:
            self.close_file()
        elif k == Qt.Key_Comma and ctrl:
            self.settings_dialog()
        elif k == Qt.Key_F1:
            self.keys_dialog()
        elif Qt.Key_0 <= k <= Qt.Key_9 and self.duration:
            self.seek_abs(self.duration * (k - Qt.Key_0) / 10)
        else:
            super().keyPressEvent(e)
            return
        self.poke()

    # ── drag & drop ───────────────────────────────────────────
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        paths = [u.toLocalFile() if u.isLocalFile() else u.toString() for u in e.mimeData().urls()]
        e.acceptProposedAction()
        QTimer.singleShot(0, lambda: self.open_paths(paths))

    # ── window ────────────────────────────────────────────────
    def showEvent(self, e):
        super().showEvent(e)
        winint.dark_title_bar(int(self.winId()))

    def restore_geometry(self):
        from PySide6.QtCore import QByteArray
        g = self.cfg.get("geometry")
        if g:
            try:
                self.restoreGeometry(QByteArray.fromBase64(g.encode()))
            except Exception:
                pass

    def closeEvent(self, e):
        self._save_position()
        self.cfg["geometry"] = bytes(self.saveGeometry().toBase64()).decode() if not self.isFullScreen() else self.cfg.get("geometry", "")
        config.save(self.cfg)
        QApplication.instance().removeEventFilter(self)
        self.ui_timer.stop()
        self.thumbs.stop()
        try:
            self.video.shutdown()
            self.mpv.terminate()
        except Exception:
            pass
        installer = getattr(self, "_installer", "")
        if installer:                         # self-update: settings saved, let the installer in
            from . import updater
            winint.release_mutex()
            updater.run_installer(installer)
        super().closeEvent(e)
