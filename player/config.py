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
