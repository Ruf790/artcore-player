"""A sheet of frames from the whole video in one picture (like PotPlayer's «Create thumbnails»): a header with the
file's name, size, length, picture and sound, then columns × rows frames spread over the film, each with its time.
The frames come from a second, invisible mpv (its own thread), HDR tone-mapped; the sheet is drawn with Pillow."""
from __future__ import annotations

import os
import threading
import time

from PySide6.QtCore import QObject, Signal

TONEMAP = ("lavfi=[scale=%d:-2,zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p]")
PLAIN = "scale=w=%d:h=-2"

BG = (24, 24, 27)
FG = (235, 235, 235)
MUTED = (160, 160, 168)


def tc(sec: float) -> str:
    sec = max(0, int(sec))
    return f"{sec // 3600:d}:{sec // 60 % 60:02d}:{sec % 60:02d}"


def size_text(n: float) -> str:
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.2f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return ""


def times(duration: float, count: int) -> list[float]:
    """count moments spread over the film (the middle of equal parts: no black first frame, no end credits frame)."""
    return [duration * (i + 0.5) / count for i in range(count)] if duration > 0 else []


def font(size: int, bold: bool = False):
    from PIL import ImageFont
    names = (["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold else
             ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"])
    windir = os.environ.get("WINDIR", r"C:\Windows")
    for n in names:
        for p in (os.path.join(windir, "Fonts", n), n, os.path.join("/usr/share/fonts/truetype/dejavu", n)):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def describe(m) -> list[str]:
    """The header lines from a loaded mpv: name, size · length, video, audio."""
    def get(name, default=None):
        try:
            v = getattr(m, name.replace("-", "_"))
            return default if v is None else v
        except Exception:
            return default
    path = get("path", "") or ""
    lines = [os.path.basename(path)]
    size = get("file-size", 0) or (os.path.getsize(path) if path and os.path.isfile(path) else 0)
    lines.append(f"{size_text(size)}  ·  {tc(get('duration', 0) or 0)}")
    tracks = get("track-list", []) or []
    for tr in tracks:
        if tr.get("type") == "video" and not tr.get("albumart"):
            vp = get("video-params", {}) or {}
            w, h = tr.get("demux-w") or vp.get("w"), tr.get("demux-h") or vp.get("h")
            fps = tr.get("demux-fps") or get("container-fps", 0) or 0
            bits = []
            bits.append(str(tr.get("codec") or "").upper())
            if w and h:
                bits.append(f"{w}×{h}")
            if fps:
                bits.append(f"{fps:.3f} fps".replace(".000", ""))
            gamma = str(vp.get("gamma") or "")
            if gamma in ("pq", "hlg"):
                bits.append("HDR10" if gamma == "pq" else "HLG")
            br = tr.get("demux-bitrate")
            if br:
                bits.append(f"{br / 1000:.0f} kbps")
            lines.append(t_video() + ": " + " · ".join(b for b in bits if b))
            break
    auds = []
    for tr in tracks:
        if tr.get("type") == "audio":
            ch = tr.get("demux-channel-count") or 0
            ch = {1: "1.0", 2: "2.0", 6: "5.1", 8: "7.1"}.get(ch, f"{ch}ch" if ch else "")
            sr = tr.get("demux-samplerate") or 0
            bits = [str(tr.get("codec") or "").upper(), ch, f"{sr / 1000:g} kHz" if sr else "",
                    str(tr.get("lang") or "")]
            auds.append(" ".join(b for b in bits if b))
    if auds:
        lines.append(t_audio() + ": " + "  |  ".join(auds))
    return lines


def t_video() -> str:
    from .i18n import t
    return t("sheet_video")


def t_audio() -> str:
    from .i18n import t
    return t("sheet_audio")


def compose(frames: list, header: list[str], cols: int, width: int, stamp: bool = True, gap: int = 6):
    """frames: [(seconds, PIL.Image)] → the sheet (PIL.Image), width pixels wide."""
    from PIL import Image, ImageDraw
    tile_w = (width - gap * (cols + 1)) // cols
    ims = []
    for sec, im in frames:
        h = round(im.height * tile_w / im.width)
        ims.append((sec, im.resize((tile_w, max(1, h)), Image.LANCZOS)))
    tile_h = max((im.height for _s, im in ims), default=tile_w * 9 // 16)
    rows = (len(ims) + cols - 1) // cols
    f_big, f_small = font(max(14, width // 70), True), font(max(12, width // 95))
    line_h = int(f_small.size * 1.45) if hasattr(f_small, "size") else 18
    head_h = ((int(f_big.size * 1.6) if hasattr(f_big, "size") else 24) + line_h * max(0, len(header) - 1) + gap * 3
              if header else gap)
    sheet = Image.new("RGB", (width, head_h + rows * (tile_h + gap) + gap), BG)
    d = ImageDraw.Draw(sheet)
    y = gap * 2
    for i, text in enumerate(header):
        d.text((gap * 2, y), text, fill=FG if i == 0 else MUTED, font=f_big if i == 0 else f_small)
        y += (int(f_big.size * 1.6) if hasattr(f_big, "size") else 24) if i == 0 else line_h
    f_tc = font(max(11, tile_w // 16), True)
    for n, (sec, im) in enumerate(ims):
        r, c = divmod(n, cols)
        x0 = gap + c * (tile_w + gap)
        y0 = head_h + r * (tile_h + gap) + (tile_h - im.height) // 2
        sheet.paste(im, (x0, y0))
        if stamp:
            text = tc(sec)
            box = d.textbbox((0, 0), text, font=f_tc)
            tw, th = box[2] - box[0], box[3] - box[1]
            bx, by = x0 + im.width - tw - 10, y0 + im.height - th - 10
            d.rectangle((bx - 5, by - 4, bx + tw + 5, by + th + 6), fill=(0, 0, 0))
            d.text((bx, by - box[1]), text, fill=(255, 255, 255), font=f_tc)
    return sheet


def sheet_path(folder: str, src: str, fmt: str) -> str:
    stem = os.path.splitext(os.path.basename(src))[0] or "video"
    base = os.path.join(folder, f"{stem}_sheet")
    path, n = f"{base}.{fmt}", 2
    while os.path.exists(path):
        path, n = f"{base} ({n}).{fmt}", n + 1
    return path


class SheetMaker(QObject):
    """make() in a thread; progress(done, total); done(path or "", error)."""
    progress = Signal(int, int)
    done = Signal(str, str)

    def __init__(self, mpv_module, hwdec: bool = True, parent=None):
        super().__init__(parent)
        self.mpvmod = mpv_module
        self.hwdec = hwdec
        self.stop = False
        self.busy = False

    def make(self, path: str, out: str, *, cols: int = 4, rows: int = 4, width: int = 1920, hdr: bool = False,
             stamp: bool = True, header: bool = True, quality: int = 90):
        if self.busy:
            return
        self.busy, self.stop = True, False
        threading.Thread(target=self._run, args=(path, out, cols, rows, width, hdr, stamp, header, quality),
                         daemon=True, name="sheet").start()

    def grab(self, path: str, count: int, tile_w: int, hdr: bool, tick=None):
        """(frames [(sec, PIL.Image)], header lines) from a second mpv."""
        import locale
        locale.setlocale(locale.LC_NUMERIC, "C")
        m = self.mpvmod.MPV(vo="null", ao="null", aid="no", sid="no", pause=True, hr_seek="yes",
                            cache="no", keep_open="yes", idle="yes", config=False, terminal=False, ytdl=False,
                            osc=False, load_scripts=False, hwdec="auto-copy-safe" if self.hwdec else "no")
        restart = threading.Event()
        m.event_callback("playback-restart")(lambda _e: restart.set())
        frames = []
        try:
            m.vf = (TONEMAP % tile_w) if hdr else (PLAIN % tile_w)
            m.play(path)
            if not restart.wait(15):
                raise RuntimeError("the file did not open")
            dur = 0.0
            for _ in range(50):
                dur = float(getattr(m, "duration", 0) or 0)
                if dur:
                    break
                time.sleep(0.1)
            head = describe(m)
            for i, sec in enumerate(times(dur, count)):
                if self.stop:
                    raise InterruptedError
                restart.clear()
                m.command("seek", sec, "absolute+exact")
                if not restart.wait(10):
                    continue
                try:
                    frames.append((sec, m.screenshot_raw("video").convert("RGB")))
                except Exception:
                    pass
                if tick:
                    tick(i + 1, count)
        finally:
            try:
                m.terminate()
            except Exception:
                pass
        return frames, head

    def _run(self, path, out, cols, rows, width, hdr, stamp, header, quality):
        err, made = "", ""
        try:
            tile_w = max(160, (width - 6 * (cols + 1)) // cols)
            frames, head = self.grab(path, cols * rows, tile_w, hdr, lambda k, n: self.progress.emit(k, n))
            if not frames:
                raise RuntimeError("no frames")
            im = compose(frames, head if header else [], cols, width, stamp)
            os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
            fmt = os.path.splitext(out)[1].lower().lstrip(".")
            if fmt in ("jpg", "jpeg"):
                im.save(out, "JPEG", quality=quality, optimize=True)
            elif fmt == "webp":
                im.save(out, "WEBP", quality=quality)
            else:
                im.save(out, "PNG", optimize=True)
            made = out
        except InterruptedError:
            err = "stopped"
        except Exception as e:                            # noqa: BLE001
            err = str(e)
        self.busy = False
        self.done.emit(made, err)
