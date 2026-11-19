"""Cut the A–B segment into a file with ffmpeg: no re-encoding, frame-exact MP4, WebM or GIF.
Also finds / asks for ArtCore Convert (the "open in Convert" menu item)."""
from __future__ import annotations

import os
import shutil
import sys

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QProgressBar, QPushButton, QSpinBox, QVBoxLayout)

from . import config, winint
from .i18n import t
from .widgets import fmt_precise

MODES = ("copy", "exact", "webm", "gif")
FIXED_EXT = {"exact": ".mp4", "webm": ".webm", "gif": ".gif"}      # "copy" keeps the source's extension
GIF_WIDTHS = (320, 480, 640, 800, 0)                                  # 0 = the original width
# HDR (PQ / HLG) → SDR, otherwise GIF / WebM / MP4 come out grey and washed out
HDR_CHAIN = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
             "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
CREATE_NO_WINDOW = 0x08000000


# ── finding the tools ─────────────────────────────────────────
def _app_dirs() -> list[str]:
    base = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0]))
    dirs = [base, os.path.join(base, "tools"), os.path.join(base, "ffmpeg"), os.path.join(base, "ffmpeg", "bin")]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        dirs += [meipass, os.path.join(meipass, "tools")]
    return dirs


def find_ffmpeg(cfg: dict | None = None) -> str | None:
    """Saved path → next to the program (or its tools folder) → PATH."""
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    cands = [(cfg or {}).get("ffmpeg_path", "")] + [os.path.join(d, exe) for d in _app_dirs()]
    cands.append(shutil.which("ffmpeg") or "")
    return next((c for c in cands if c and os.path.isfile(c)), None)


def find_convert(cfg: dict | None = None) -> str | None:
    """ArtCore Convert: the saved path, then the usual install folders."""
    saved = (cfg or {}).get("convert_path", "")
    if saved and os.path.isfile(saved):
        return saved
    roots = [os.environ.get(k, "") for k in ("ProgramFiles", "ProgramFiles(x86)")]
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        roots.append(os.path.join(local, "Programs"))
    for root in filter(None, roots):
        for folder in ("ArtCore Convert", "ArtCore-Convert", "ArtCoreConvert"):
            for name in ("ArtCore Convert.exe", "ArtCoreConvert.exe", "artcore-convert.exe"):
                p = os.path.join(root, folder, name)
                if os.path.isfile(p):
                    return p
    return None


def _ask_exe(parent, cfg: dict, key: str, title: str, message: str) -> str | None:
    QMessageBox.information(parent, title, message)
    f, _ = QFileDialog.getOpenFileName(parent, title, "", "Program (*.exe);;All files (*)")
    if not f:
        return None
    cfg[key] = f
    config.save(cfg)
    return f


def ask_ffmpeg(parent, cfg: dict) -> str | None:
    return _ask_exe(parent, cfg, "ffmpeg_path", t("clip_ff_pick"), t("clip_ff_missing"))


def ask_convert(parent, cfg: dict) -> str | None:
    return _ask_exe(parent, cfg, "convert_path", t("convert_pick"), t("convert_missing"))


# ── the ffmpeg command ────────────────────────────────────────
def stamp(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}-{m:02d}-{s:02d}.{ms:03d}"


def default_output(src: str, a: float, b: float, mode: str) -> str:
    base, ext = os.path.splitext(os.path.basename(src))
    ext = ext if mode == "copy" and ext else FIXED_EXT.get(mode, ".mkv")
    folder = os.path.dirname(src)
    if not os.access(folder, os.W_OK):
        folder = os.path.join(os.path.expanduser("~"), "Videos")
        os.makedirs(folder, exist_ok=True)
    name = f"{base}_{stamp(a)}_{stamp(b)}"
    out, n = os.path.join(folder, name + ext), 2
    while os.path.exists(out):
        out = os.path.join(folder, f"{name}_{n}{ext}")
        n += 1
    return out


def build_cmd(ffmpeg: str, src: str, a: float, b: float, mode: str, out: str, *, audio_map: str = "0:a:0?",
              has_video: bool = True, hdr: bool = False, gif_width: int = 480, gif_fps: int = 15) -> list[str]:
    """-ss before -i is fast; with re-encoding ffmpeg still decodes from the previous key frame, so the start is exact.
    The length goes as -t (after -i): it counts from the cut start, whatever the container's own timestamps are."""
    cmd = [ffmpeg, "-hide_banner", "-nostdin", "-y", "-loglevel", "error", "-nostats", "-progress", "pipe:1",
           "-ss", f"{a:.3f}", "-i", src, "-t", f"{max(0.001, b - a):.3f}"]
    maps = (["-map", "0:v:0"] if has_video else []) + ["-map", audio_map]
    vf = [HDR_CHAIN] if hdr and has_video and mode != "copy" else []

    if mode == "copy":
        return cmd + maps + ["-sn", "-dn", "-c", "copy", "-avoid_negative_ts", "make_zero", out]

    if mode == "exact":
        chain = ",".join(vf + ["scale=trunc(iw/2)*2:trunc(ih/2)*2"])      # x264 + yuv420p want even sizes
        return cmd + maps + ["-sn", "-dn", "-vf", chain, "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]

    if mode == "webm":
        chain = ",".join(vf + ["scale=trunc(iw/2)*2:trunc(ih/2)*2"])
        return cmd + maps + ["-sn", "-dn", "-vf", chain, "-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0",
                             "-row-mt", "1", "-pix_fmt", "yuv420p", "-c:a", "libopus", "-b:a", "128k", out]

    # gif: one palette for the whole clip (palettegen), then dithered with it
    scale = [f"scale={gif_width}:-1:flags=lanczos"] if gif_width else []
    chain = ",".join(vf + [f"fps={gif_fps}"] + scale)
    chain += ",split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5"
    return cmd + ["-map", "0:v:0", "-sn", "-dn", "-an", "-vf", chain, "-loop", "0", out]


# ── the dialog ────────────────────────────────────────────────
class ClipDialog(QDialog):
    """Mode, file name, progress. Not modal: the video keeps playing while a long GIF is being made."""

    def __init__(self, parent, ffmpeg: str, src: str, a: float, b: float, cfg: dict, *,
                 audio_map: str = "0:a:0?", has_video: bool = True, hdr: bool = False):
        super().__init__(parent)
        self.setWindowTitle(t("clip_title"))
        self.setMinimumWidth(520)
        self.ffmpeg, self.src, self.a, self.b, self.cfg = ffmpeg, src, a, b, cfg
        self.audio_map, self.has_video, self.hdr = audio_map, has_video, hdr
        self.dur = max(0.001, b - a)
        self.proc: QProcess | None = None
        self._buf = ""
        self._err = ""
        self._out_path = ""
        self._canceled = False

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(t("clip_range", fmt_precise(a), fmt_precise(b), f"{self.dur:.2f} " + t("clip_sec"))))

        form = QFormLayout()
        self.mode = QComboBox()
        for m in (MODES if has_video else ("copy",)):
            self.mode.addItem(t("clip_m_" + m), m)
        saved = cfg.get("clip_mode", "copy")
        self.mode.setCurrentIndex(max(0, self.mode.findData(saved)))
        form.addRow(t("clip_mode"), self.mode)
        lay.addLayout(form)

        self.hint = QLabel()
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color: #9aa0a6;")
        lay.addWidget(self.hint)

        gif_row = QHBoxLayout()
        self.gif_width = QComboBox()
        for w in GIF_WIDTHS:
            self.gif_width.addItem(f"{w} px" if w else t("clip_orig"), w)
        self.gif_width.setCurrentIndex(max(0, self.gif_width.findData(int(cfg.get("clip_gif_w", 480)))))
        self.gif_fps = QSpinBox()
        self.gif_fps.setRange(5, 30)
        self.gif_fps.setValue(int(cfg.get("clip_gif_fps", 15)))
        self._gif_widgets = [QLabel(t("clip_width")), self.gif_width, QLabel(t("clip_fps")), self.gif_fps]
        for w in self._gif_widgets:
            gif_row.addWidget(w)
        gif_row.addStretch(1)
        lay.addLayout(gif_row)

        row = QHBoxLayout()
        self.out = QLineEdit(default_output(src, a, b, self.mode.currentData()))
        self.browse = QPushButton(t("clip_browse"))
        self.browse.clicked.connect(self._browse)
        row.addWidget(QLabel(t("clip_out")))
        row.addWidget(self.out, 1)
        row.addWidget(self.browse)
        lay.addLayout(row)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setVisible(False)
        lay.addWidget(self.bar)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.status)

        btns = QHBoxLayout()
        btns.addStretch(1)
        self.b_folder = QPushButton(t("show_in_folder"))
        self.b_folder.setVisible(False)
        self.b_folder.clicked.connect(lambda: winint.show_in_explorer(self._out_path))
        self.b_go = QPushButton(t("clip_start"))
        self.b_go.setDefault(True)
        self.b_go.clicked.connect(self._start)
        self.b_close = QPushButton(t("close"))
        self.b_close.clicked.connect(self.reject)
        for b_ in (self.b_folder, self.b_go, self.b_close):
            btns.addWidget(b_)
        lay.addLayout(btns)

        self.mode.currentIndexChanged.connect(self._mode_changed)
        self._mode_changed()

    # ── UI ────────────────────────────────────────────────────
    def _mode_changed(self):
        m = self.mode.currentData()
        self.hint.setText(t("clip_h_" + m))
        for w in self._gif_widgets:
            w.setVisible(m == "gif")
        # keep the folder and the name, swap only the extension
        base, ext = os.path.splitext(self.out.text())
        src_ext = os.path.splitext(self.src)[1]
        new_ext = src_ext if m == "copy" and src_ext else FIXED_EXT.get(m, ".mkv")
        self.out.setText(base + new_ext)
        self.adjustSize()

    def _browse(self):
        f, _ = QFileDialog.getSaveFileName(self, t("clip_out"), self.out.text())
        if f:
            self.out.setText(f)

    def _set_busy(self, busy: bool):
        for w in (self.mode, self.out, self.browse, self.gif_width, self.gif_fps):
            w.setEnabled(not busy)
        self.b_go.setText(t("clip_cancel") if busy else t("clip_start"))
        self.b_close.setEnabled(not busy)
        self.bar.setVisible(busy or self.bar.value() > 0)
        self.b_folder.setVisible(False)

    # ── run ───────────────────────────────────────────────────
    def _start(self):
        if self.proc is not None:                      # the button is "Cancel" while it works
            self._cancel()
            return
        out = os.path.abspath(self.out.text().strip())
        if not out or not os.path.isdir(os.path.dirname(out)):
            self.status.setText(t("clip_bad_path"))
            return
        if os.path.normcase(out) == os.path.normcase(os.path.abspath(self.src)):
            self.status.setText(t("clip_same"))
            return
        if os.path.exists(out) and QMessageBox.question(self, t("clip_title"), t("clip_overwrite", out)) != QMessageBox.Yes:
            return
        mode = self.mode.currentData()
        self.cfg.update(clip_mode=mode, clip_gif_w=self.gif_width.currentData(), clip_gif_fps=self.gif_fps.value())
        config.save(self.cfg)
        cmd = build_cmd(self.ffmpeg, self.src, self.a, self.b, mode, out, audio_map=self.audio_map,
                        has_video=self.has_video, hdr=self.hdr, gif_width=self.gif_width.currentData(),
                        gif_fps=self.gif_fps.value())
        self._out_path, self._buf, self._err, self._canceled = out, "", "", False
        self.bar.setValue(0)
        self.status.setText(t("clip_working", 0))
        p = self.proc = QProcess(self)
        if os.name == "nt":
            def no_console(args):
                try:
                    args.flags |= CREATE_NO_WINDOW
                except Exception:
                    pass
            try:
                p.setCreateProcessArgumentsModifier(no_console)
            except Exception:
                pass
        p.setProgram(cmd[0])
        p.setArguments(cmd[1:])
        p.readyReadStandardOutput.connect(self._on_out)
        p.readyReadStandardError.connect(self._on_err)
        p.finished.connect(self._finished)
        p.errorOccurred.connect(self._on_error)
        self._set_busy(True)
        p.start()

    def _on_out(self):
        self._buf += bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
        *lines, self._buf = self._buf.split("\n")
        for line in lines:
            if line.startswith("out_time_us="):
                try:
                    pct = max(0, min(99, int(int(line.split("=", 1)[1].strip()) / 1e6 / self.dur * 100)))
                except ValueError:                       # "N/A" at the very start
                    continue
                self.bar.setValue(pct)
                self.status.setText(t("clip_working", pct))

    def _on_err(self):
        self._err = (self._err + bytes(self.proc.readAllStandardError()).decode("utf-8", "replace"))[-1500:]

    def _on_error(self, err):
        if err == QProcess.FailedToStart:               # `finished` is not emitted in this case
            self._err = t("clip_ff_missing")
            self._finished(-1, QProcess.CrashExit)

    def _cancel(self):
        self._canceled = True
        if self.proc is not None:
            self.proc.kill()

    def _finished(self, code, status):
        p, self.proc = self.proc, None
        if p is not None:
            p.deleteLater()
        ok = code == 0 and status == QProcess.NormalExit and not self._canceled
        if ok:
            self.bar.setValue(100)
            self.status.setText(t("clip_done", os.path.basename(self._out_path)))
        else:
            try:                                          # no half-written files left behind
                if os.path.exists(self._out_path):
                    os.remove(self._out_path)
            except OSError:
                pass
            self.bar.setValue(0)
            self.status.setText(t("clip_canceled") if self._canceled
                                else t("clip_failed", self._err.strip()[-600:] or f"code {code}"))
        self._set_busy(False)
        self.bar.setVisible(ok)
        self.b_folder.setVisible(ok)

    def reject(self):
        p = self.proc
        if p is not None:
            self._cancel()
            p.waitForFinished(2000)
        super().reject()
