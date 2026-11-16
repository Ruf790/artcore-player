"""Taking the current frame out of an mpv instance as a Pillow image.

python-mpv's own screenshot_raw() builds the picture with the row stride as its width.
mpv pads rows (on 4K HEVC almost always), so those extra columns come out as a strip of
coloured garbage along the right edge. Here the real width is used and the padding is cut off.
"""

from __future__ import annotations


def frame(m, includes: str = "video"):
    from PIL import Image
    res = m.command("screenshot-raw", includes)
    if res.get("format") != "bgr0":
        raise ValueError("unexpected screenshot format: %r" % res.get("format"))
    w, h, stride = int(res["w"]), int(res["h"]), int(res["stride"])
    data = res["data"]
    # rows are `stride` bytes long; read only the first w*4 of each
    img = Image.frombuffer("RGBA", (w, h), bytes(data), "raw", "BGRA", stride, 1)
    return img.convert("RGB")
