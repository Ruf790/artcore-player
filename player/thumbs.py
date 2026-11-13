"""Frame previews for the seek bar: a second, invisible mpv decodes single frames (keyframe seek,
scaled down, HDR tone-mapped) in its own thread; the newest request wins, results are cached."""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

WIDTH = 256
TONEMAP = ("lavfi=[scale=%d:-2,zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p]" % WIDTH)
PLAIN = "scale=w=%d:h=-2" % WIDTH


class Thumbnailer(QObject):
    ready = Signal(str, float, QImage)          # path, bucket time, image

    def __init__(self, mpv_module, hwdec: bool):
        super().__init__()
        self.mpvmod = mpv_module
        self.hwdec = hwdec
        self.path = ""
        self.hdr = False
        self.cache: dict[tuple[str, float], QImage] = {}
        self._want: tuple[str, float] | None = None
        self._wake = threading.Event()
        self._stop = False
        self._thread: threading.Thread | None = None

    # ── GUI thread ────────────────────────────────────────────
    def set_file(self, path: str, hdr: bool):
        self.path, self.hdr = path, hdr
        self._want = None

    def request(self, sec: float, bucket: float):
        if not self.path:
            return None
        key = (self.path, bucket)
        img = self.cache.get(key)
        if img is not None:
            return img
        self._want = key
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, daemon=True, name="thumbs")
            self._thread.start()
        self._wake.set()
        return None

    def stop(self):
        self._stop = True
        self._wake.set()

    # ── worker thread ─────────────────────────────────────────
    def _run(self):
        import locale
        locale.setlocale(locale.LC_NUMERIC, "C")
        m = None
        loaded = (None, None)               # (path, hdr) loaded in m
        restart = threading.Event()
        try:
            m = self.mpvmod.MPV(vo="null", ao="null", aid="no", sid="no", pause=True, hr_seek="no",
                                cache="no", demuxer_readahead_secs=0, keep_open="yes", idle="yes",
                                config=False, terminal=False, ytdl=False, osc=False, load_scripts=False,
                                hwdec="auto-copy-safe" if self.hwdec else "no")
            m.event_callback("playback-restart")(lambda _e: restart.set())
            while not self._stop:
                self._wake.wait()
                self._wake.clear()
                want = self._want
                if self._stop or want is None or want in self.cache:
                    continue
                path, sec = want
                if loaded != (path, self.hdr):
                    m.vf = TONEMAP if self.hdr else PLAIN
                    restart.clear()
                    m.play(path)
                    if not restart.wait(8):
                        continue
                    loaded = (path, self.hdr)
                restart.clear()
                m.command("seek", sec, "absolute+keyframes")
                if not restart.wait(4):
                    continue
                try:
                    pil = m.screenshot_raw("video").convert("RGB")
                except Exception:
                    continue
                data = pil.tobytes()
                img = QImage(data, pil.width, pil.height, pil.width * 3, QImage.Format_RGB888).copy()
                if len(self.cache) > 500:
                    self.cache.clear()
                self.cache[want] = img
                self.ready.emit(path, sec, img)
        except Exception:
            pass
        finally:
            if m is not None:
                try:
                    m.terminate()
                except Exception:
                    pass
