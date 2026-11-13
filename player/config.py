"""Settings and per-file state (resume positions, recent files) in %APPDATA%\\ArtCorePlayer\\config.json.
A portable.ini next to the exe keeps everything in .\\Data instead."""
from __future__ import annotations

import copy
import json
import os
import sys

DEFAULTS = {
    "language":      "ru",
    "volume":        80,
    "muted":         False,
    "hwdec":         True,          # hardware decoding (auto-safe); off = software
    "resume":        True,          # continue where you stopped
    "autoplay_next": True,          # next file of the folder when one ends (series)
    "single_window": True,          # files opened from Explorer go to the running player
    "on_top":        False,
    "alang":         "rus,ru,russian,eng,en",   # preferred audio languages
    "slang":         "",                         # preferred subtitle languages, "" = only forced/default
    "screenshot_dir": "",
    "remaining_time": False,        # time label shows -remaining instead of the duration
    "thumbs":        True,          # frame previews over the seek bar
    "audio_mode":    "off",         # off | night | level | dialog
    "eq":            [0] * 10,      # equalizer, dB per band (audio.BANDS)
    "eq_preset":     "flat",
    "check_updates": True,
    "last_update_check": 0,
    "update_notified": "",
    "reopen":        "",            # the file that was open when the player updated itself
    "smooth":        False,         # smooth motion: display-resample + interpolation
    "picture":       {"brightness": 0, "contrast": 0, "saturation": 0, "gamma": 0},
    "mini_geometry": [],            # x, y, w, h of the mini player
    "intros":        {},            # folder → {"a": start, "b": end, "auto": bool}
    # 1.3.0
    "seek_step":     5,             # ← → (Ctrl: 10 s, Shift: 1 min)
    "vol_step":      5,             # ↑ ↓ / wheel
    "repeat":        "off",         # off | file | list
    "start_fullscreen": False,
    "pause_minimized": False,
    "keep_speed":    True,          # the speed stays for the next file (off: every file starts at 1×)
    "pitch":         True,          # audio-pitch-correction
    "quality":       "normal",      # fast | normal | high (scalers)
    "deband":        False,
    "deinterlace":   "auto",        # auto | yes | no
    "tone_mapping":  "auto",        # auto | bt.2446a | spline | hable | mobius
    "screenshot_format": "png",     # png | jpg | webp
    "screenshot_subs": True,
    "audio_device":  "auto",
    "audio_channels": "auto-safe",  # auto-safe | stereo | 5.1 | 7.1
    "audio_exclusive": False,
    "volume_max":    150,
    "sub_font":      "",
    "sub_scale":     1.0,
    "sub_color":     "#FFFFFF",
    "sub_border":    "normal",      # thin | normal | thick
    "sub_bold":      False,
    "sub_force_style": False,       # sub-ass-override=force
    "sub_auto":      "fuzzy",       # fuzzy | exact | no
    "sub_codepage":  "auto",
    "hide_delay":    2.6,           # seconds
    "geometry":      "",
    "last_dir":      "",
    "recent":        [],            # most recent first
    "positions":     {},            # path → seconds (resume)
}
MAX_RECENT = 12
MAX_POSITIONS = 400


def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_portable() -> bool:
    return os.path.isfile(os.path.join(app_dir(), "portable.ini"))


def data_dir() -> str:
    if is_portable():
        path = os.path.join(app_dir(), "Data")
    else:
        base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
        path = os.path.join(base, "ArtCorePlayer")
    os.makedirs(path, exist_ok=True)
    return path


def _path() -> str:
    return os.path.join(data_dir(), "config.json")


def load() -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    try:
        with open(_path(), encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            cfg.update({k: v for k, v in saved.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    if cfg.get("language") not in ("ru", "en"):
        cfg["language"] = "ru"
    return cfg


KEEP_ON_RESET = ("language", "recent", "positions", "intros", "geometry", "last_dir", "mini_geometry",
                 "last_update_check", "update_notified", "reopen", "volume", "muted")


def reset(cfg: dict) -> None:
    """Every setting back to default; history, resume positions, intros and the window stay."""
    keep = {k: cfg.get(k) for k in KEEP_ON_RESET if k in cfg}
    cfg.clear()
    cfg.update(copy.deepcopy(DEFAULTS))
    cfg.update(keep)


def save(cfg: dict) -> None:
    path = _path()
    try:
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=1)
        os.replace(path + ".tmp", path)
    except OSError:
        pass


def add_recent(cfg: dict, path: str) -> None:
    rec = [p for p in cfg.get("recent", []) if os.path.normcase(p) != os.path.normcase(path)]
    cfg["recent"] = [path] + rec[:MAX_RECENT - 1]


def set_position(cfg: dict, path: str, pos: float | None) -> None:
    pos_map = cfg.setdefault("positions", {})
    pos_map.pop(path, None)
    if pos is not None:
        pos_map[path] = round(pos, 1)          # newest last: the oldest go first when trimming
        while len(pos_map) > MAX_POSITIONS:
            pos_map.pop(next(iter(pos_map)))
