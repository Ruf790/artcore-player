"""File-type icons for the formats ArtCore Player opens: assets/formats/<ext>.ico (+ a preview sheet),
and the per-format block of the installer (setup.iss, between the "formats" markers).

The same family look as ArtCore Music: a page with a folded corner in the colour of the format's family,
the format name in big letters and a tag at the bottom (MATROSKA, BLU-RAY, DVD…). Video pages are film:
sprocket holes run down both edges and the glyph on top is a play button (a disc for .iso images, a
"</>" stream mark for raw codec streams). Every size of the .ico is drawn on its own (no blurry
downscaling): 16–24 px show the page, the holes and the glyph, 32 px and up carry the name.

    python tools/make_format_icons.py [font.ttf/otf] [--preview sheet.png] [--iss]
The .ico files and the setup.iss block are committed; this script is only needed to change them."""
from __future__ import annotations

import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "formats")
SIZES = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
SS = 4                                     # supersampling

# family: (top colour, bottom colour, tag, glyph)
FAMILIES = {
    "mkv":     ("#7b5cf0", "#3f2fb0", "MATROSKA", "play"),
    "mp4":     ("#3d8bfd", "#1d4fbf", "MPEG-4", "play"),
    "apple":   ("#b9bcc6", "#6f7380", "QUICKTIME", "play"),
    "avi":     ("#f08a3c", "#c0551a", "", "play"),
    "divx":    ("#e2683a", "#a83a18", "", "play"),
    "windows": ("#4a6fa5", "#2c4670", "WINDOWS", "play"),
    "web":     ("#2fb36b", "#16774a", "WEB", "play"),
    "xiph":    ("#e0507a", "#a72a52", "OGG", "play"),
    "bluray":  ("#2b8fe0", "#0f4fa0", "BLU-RAY", "play"),
    "tv":      ("#2bb3c6", "#167a8c", "TV STREAM", "play"),
    "camera":  ("#3fb8a0", "#1d7a68", "CAMERA", "play"),
    "mpeg":    ("#a8a03a", "#6f6a1d", "MPEG", "play"),
    "dvd":     ("#d9a52b", "#94680f", "DVD", "play"),
    "flash":   ("#e04848", "#9c1f26", "FLASH", "play"),
    "mobile":  ("#c25bd6", "#7e2c96", "MOBILE", "play"),
    "real":    ("#3a5fc8", "#1e3784", "REAL", "play"),
    "pro":     ("#5a6475", "#343b48", "PRO", "play"),
    "other":   ("#7d8797", "#4b5363", "", "play"),
    "raw":     ("#2b2f3a", "#0e1016", "STREAM", "raw"),
    "iso":     ("#6f42c1", "#0d6efd", "DISC IMAGE", "disc"),
}

# extension → (label on the icon, family). Every extension of player.VIDEO_EXT is here.
FORMATS = {
    "mkv": ("MKV", "mkv"), "mk3d": ("MK3D", "mkv"),
    "mp4": ("MP4", "mp4"), "m4v": ("M4V", "mp4"),
    "mov": ("MOV", "apple"), "qt": ("QT", "apple"),
    "avi": ("AVI", "avi"), "divx": ("DIVX", "divx"), "xvid": ("XVID", "divx"),
    "wmv": ("WMV", "windows"), "asf": ("ASF", "windows"), "wtv": ("WTV", "windows"), "dvr-ms": ("DVR-MS", "windows"),
    "webm": ("WEBM", "web"), "ogv": ("OGV", "xiph"), "ogm": ("OGM", "xiph"),
    "m2ts": ("M2TS", "bluray"), "mts": ("MTS", "camera"), "ts": ("TS", "tv"), "trp": ("TRP", "tv"),
    "tp": ("TP", "tv"), "mod": ("MOD", "camera"), "tod": ("TOD", "camera"),
    "mpg": ("MPG", "mpeg"), "mpeg": ("MPEG", "mpeg"), "mpe": ("MPE", "mpeg"), "mpv": ("MPV", "mpeg"),
    "m2v": ("M2V", "mpeg"), "m1v": ("M1V", "mpeg"),
    "vob": ("VOB", "dvd"), "evo": ("EVO", "dvd"),
    "flv": ("FLV", "flash"), "f4v": ("F4V", "flash"),
    "3gp": ("3GP", "mobile"), "3g2": ("3G2", "mobile"), "amv": ("AMV", "mobile"),
    "rm": ("RM", "real"), "rmvb": ("RMVB", "real"),
    "mxf": ("MXF", "pro"), "dv": ("DV", "pro"), "nut": ("NUT", "other"), "bik": ("BIK", "other"),
    "hevc": ("HEVC", "raw"), "h265": ("H.265", "raw"), "265": ("H.265", "raw"),
    "h264": ("H.264", "raw"), "264": ("H.264", "raw"), "avc": ("AVC", "raw"),
    "ivf": ("IVF", "raw"), "obu": ("AV1", "raw"), "y4m": ("Y4M", "raw"),
    "iso": ("ISO", "iso"),
}
# what the tag says when it is more precise than the family's
TAGS = {"mts": "AVCHD", "m2ts": "BLU-RAY", "evo": "HD DVD", "obu": "STREAM", "divx": "DIVX", "xvid": "XVID"}


def _font(path: str | None, px: int):
    for p in ([path] if path else []) + ["/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
                                         "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
                                         "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
                                         "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
        if p and os.path.isfile(p):
            return ImageFont.truetype(p, px)
    return ImageFont.load_default()


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _fit(draw, text, font_path, max_w, max_h):
    px = int(max_h)
    while px > 4:
        f = _font(font_path, px)
        b = draw.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= max_w and b[3] - b[1] <= max_h:
            return f, b
        px -= 1
    f = _font(font_path, 5)
    return f, draw.textbbox((0, 0), text, font=f)


def draw_icon(size: int, label: str, family: str, font_path: str | None = None, tag: str | None = None) -> Image.Image:
    c1, c2, ftag, glyph = FAMILIES[family]
    tag = ftag if tag is None else tag
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    small = size < 32
    # the page: a bit narrower than tall, a folded top-right corner
    pad_x, pad_y = (0.08 if small else 0.11) * S, 0.04 * S
    x0, y0, x1, y1 = pad_x, pad_y, S - pad_x, S - pad_y
    W, H = x1 - x0, y1 - y0
    fold = W * 0.28
    r = max(SS, 0.07 * S)
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    a, b = _rgb(c1), _rgb(c2)
    for y in range(S):
        k = max(0.0, min(1.0, (y - y0) / max(1, H)))
        gd.line([(0, y), (S, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3)) + (255,))
    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=255)
    md.rectangle([x1 - fold, y0 - 1, x1 + 1, y0 + fold], fill=0)                        # the corner goes
    md.polygon([(x1 - fold, y0), (x1 - fold, y0 + fold), (x1, y0 + fold)], fill=255)   # under the flap
    # film: sprocket holes punched through both edges (transparent, so the page reads as a strip)
    rail = W * (0.105 if not small else 0.15)
    hole_w, hole_h = rail * 0.46, H * (0.055 if not small else 0.10)
    n = 7 if not small else 4
    for side in (0, 1):
        hx = x0 + (rail - hole_w) / 2 if side == 0 else x1 - (rail + hole_w) / 2
        top = y0 + H * 0.07 + (fold if side == 1 else 0)
        bot = y1 - H * 0.07
        cnt = n if side == 0 else max(2, n - (2 if not small else 1))
        step = (bot - top - hole_h) / max(1, cnt - 1)
        for i in range(cnt):
            hy = top + i * step
            md.rounded_rectangle([hx, hy, hx + hole_w, hy + hole_h], radius=hole_w * 0.3, fill=0)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    # the folded flap: lighter triangle with a soft shadow line
    flap = tuple(min(255, int(v * 0.55 + 255 * 0.45)) for v in a) + (255,)
    d.polygon([(x1 - fold, y0), (x1, y0 + fold), (x1 - fold, y0 + fold)], fill=flap)
    d.line([(x1 - fold, y0 + fold), (x1, y0 + fold)], fill=(0, 0, 0, 60), width=max(1, SS // 2))
    # thin rails along the holes
    for xx in (x0 + rail, x1 - rail):
        d.line([(xx, y0 + (fold if xx > S / 2 else H * 0.03)), (xx, y1 - H * 0.03)],
               fill=(0, 0, 0, 55), width=max(1, SS // 2))
    white = (255, 255, 255, 255)
    soft = (255, 255, 255, 225)
    inner_x0, inner_x1 = x0 + rail, x1 - rail
    IW = inner_x1 - inner_x0
    # glyph
    if small:
        gs = IW * 0.62
        gx, gy = inner_x0 + (IW - gs) / 2, y0 + H * 0.5 - gs / 2 + H * 0.04
    else:
        gs = H * 0.22
        gx, gy = inner_x0 + IW * 0.10, y0 + H * 0.10
    if glyph == "play":
        d.rounded_rectangle([gx, gy, gx + gs, gy + gs], radius=gs * 0.26, fill=(0, 0, 0, 70) if not small else None)
        cx, cy, s = gx + gs * 0.54, gy + gs / 2, gs * 0.27
        d.polygon([(cx - s * 0.85, cy - s), (cx + s * 1.0, cy), (cx - s * 0.85, cy + s)], fill=white)
    elif glyph == "disc":
        cx, cy, rr = gx + gs / 2, gy + gs / 2, gs / 2
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=soft)
        d.ellipse([cx - rr * 0.62, cy - rr * 0.62, cx + rr * 0.62, cy + rr * 0.62], fill=(255, 255, 255, 120))
        hr = rr * 0.22
        d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=_rgb(c1) + (255,))
    elif glyph == "raw":
        lw = max(SS, gs * 0.12)
        m = gs * 0.5
        d.line([(gx + m * 0.55, gy + gs * 0.18), (gx + gs * 0.05, gy + gs / 2), (gx + m * 0.55, gy + gs * 0.82)],
               fill=soft, width=int(lw), joint="curve")
        d.line([(gx + gs - m * 0.55, gy + gs * 0.18), (gx + gs * 0.95, gy + gs / 2),
                (gx + gs - m * 0.55, gy + gs * 0.82)], fill=soft, width=int(lw), joint="curve")
        d.line([(gx + gs * 0.58, gy + gs * 0.12), (gx + gs * 0.42, gy + gs * 0.88)], fill=soft, width=int(lw))
    if small:
        return img.resize((size, size), Image.LANCZOS)
    # the name, as big as it fits
    f, bb = _fit(d, label, font_path, IW * 0.84, H * 0.24)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    ty = y0 + H * (0.55 if tag else 0.60) - th / 2
    d.text((inner_x0 + (IW - tw) / 2 - bb[0], ty - bb[1]), label, font=f, fill=white)
    if tag and size >= 48:
        f2, b2 = _fit(d, tag, font_path, IW * 0.80, H * 0.075)
        tw2, th2 = b2[2] - b2[0], b2[3] - b2[1]
        px_, py_ = IW * 0.06, H * 0.03
        bx0 = inner_x0 + (IW - tw2) / 2 - px_
        by0 = y1 - H * 0.19
        d.rounded_rectangle([bx0, by0, bx0 + tw2 + 2 * px_, by0 + th2 + 2 * py_], radius=(th2 + 2 * py_) / 2,
                            fill=(0, 0, 0, 80))
        d.text((bx0 + px_ - b2[0], by0 + py_ - b2[1]), tag, font=f2, fill=(255, 255, 255, 235))
    elif tag:
        d.rounded_rectangle([inner_x0 + IW * 0.18, y1 - H * 0.16, inner_x1 - IW * 0.18, y1 - H * 0.11],
                            radius=SS, fill=(255, 255, 255, 150))
    return img.resize((size, size), Image.LANCZOS)


def _draw(ext: str, size: int, font_path: str | None = None) -> Image.Image:
    label, fam = FORMATS[ext]
    return draw_icon(size, label, fam, font_path, TAGS.get(ext))


def build(font_path: str | None = None, out: str = OUT) -> list[str]:
    os.makedirs(out, exist_ok=True)
    done = []
    for ext in FORMATS:
        frames = [_draw(ext, s, font_path) for s in SIZES]
        path = os.path.join(out, ext + ".ico")
        frames[-1].save(path, format="ICO", sizes=[(s, s) for s in SIZES], append_images=frames[:-1])
        done.append(path)
    return done


def preview(path: str, font_path: str | None = None):
    """A sheet: every format at 96 px with its extension, and one row of sizes."""
    exts = list(FORMATS)
    cols, cell = 10, 128
    rows = (len(exts) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * (cell + 26) + 150), (245, 246, 248, 255))
    d = ImageDraw.Draw(sheet)
    f = _font(font_path, 15)
    for i, ext in enumerate(exts):
        x, y = (i % cols) * cell, (i // cols) * (cell + 26)
        sheet.alpha_composite(_draw(ext, 96, font_path), (x + 16, y + 12))
        tb = d.textbbox((0, 0), "." + ext, font=f)
        d.text((x + (cell - tb[2]) / 2, y + 112), "." + ext, font=f, fill=(60, 64, 72))
    y = rows * (cell + 26) + 20
    x = 16
    for s in (16, 20, 24, 32, 48, 64, 128):
        for ext in ("mkv", "m2ts", "iso"):
            sheet.alpha_composite(_draw(ext, s, font_path), (x, y + (128 - s)))
            x += s + 6
        x += 26
    sheet.convert("RGB").save(path)


# ── the installer ─────────────────────────────────────────────
ISS = os.path.join(ROOT, "setup.iss")
BEGIN = "; >>> formats (tools/make_format_icons.py --iss)"
END = "; <<< formats"


def iss_block() -> str:
    """Every format gets its own ProgId (ArtCorePlayer.<ext>) with its own icon and name in Explorer."""
    sys.path.insert(0, ROOT)
    from player import VIDEO_EXT
    missing = [e for e in VIDEO_EXT if e.lstrip(".") not in FORMATS]
    if missing:
        raise SystemExit(f"no icon for {missing}")
    lines = [BEGIN]
    for e in VIDEO_EXT:
        ext = e.lstrip(".")
        label, fam = FORMATS[ext]
        prog = "ArtCorePlayer." + ext
        kind = "{cm:DiscImage}" if fam == "iso" else "{cm:VideoFile}"
        k = r"Software\Classes"
        lines += [
            f'Root: HKA; Subkey: "{k}\\{prog}"; ValueType: string; ValueName: ""; ValueData: "{label} — {kind}"; Flags: uninsdeletekey; Tasks: openwith',
            f'Root: HKA; Subkey: "{k}\\{prog}\\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{{app}}\\formats\\{ext}.ico"",0"; Tasks: openwith',
            f'Root: HKA; Subkey: "{k}\\{prog}\\shell\\open\\command"; ValueType: string; ValueName: ""; ValueData: """{{app}}\\{{#AppExe}}"" ""%1"""; Tasks: openwith',
            f'Root: HKA; Subkey: "{k}\\{e}\\OpenWithProgids"; ValueType: none; ValueName: "{{#OldProg}}"; Flags: deletevalue; Tasks: openwith',
            f'Root: HKA; Subkey: "{k}\\{e}\\OpenWithProgids"; ValueType: string; ValueName: "{prog}"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith',
            f'Root: HKA; Subkey: "{k}\\Applications\\{{#AppExe}}\\SupportedTypes"; ValueType: string; ValueName: "{e}"; ValueData: ""; Tasks: openwith',
            f'Root: HKA; Subkey: "{{#CapKey}}\\FileAssociations"; ValueType: string; ValueName: "{e}"; ValueData: "{prog}"; Tasks: openwith',
        ]
    lines.append(END)
    return "\n".join(lines)


def write_iss():
    with open(ISS, encoding="utf-8-sig") as f:
        text = f.read()
    block = iss_block()
    pat = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    if not pat.search(text):
        raise SystemExit("setup.iss has no formats markers")
    text = pat.sub(lambda _m: block, text)
    with open(ISS, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)
    print("setup.iss:", block.count("\n") - 1, "lines")


if __name__ == "__main__":
    args = sys.argv[1:]
    sheet = ""
    if "--preview" in args:
        i = args.index("--preview")
        sheet = args[i + 1]
        del args[i:i + 2]
    iss = "--iss" in args
    args = [a for a in args if a != "--iss"]
    fp = args[0] if args else None
    files = build(fp)
    if sheet:
        preview(sheet, fp)
    if iss:
        write_iss()
    print(len(files), "icons in", OUT)
