"""Sound processing: night mode, loudness levelling, clear dialogue, a 10-band equalizer."""
from __future__ import annotations

BANDS = (31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)
PRESETS = {                          # dB per band
    "flat":     (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    "bass":     (6, 5, 4, 2, 0, 0, 0, 0, 0, 0),
    "treble":   (0, 0, 0, 0, 0, 0, 2, 4, 5, 6),
    "voice":    (-4, -3, -1, 1, 3, 4, 4, 3, 1, 0),
    "cinema":   (4, 3, 1, 0, -1, 0, 1, 2, 3, 3),
    "music":    (4, 3, 2, 0, -1, 0, 2, 3, 4, 4),
    "loudness": (5, 4, 2, 0, -1, 0, 1, 2, 4, 5),
}
MODES = ("off", "night", "level", "dialog")


def eq_filter(gains) -> str:
    if not any(gains):
        return ""
    entries = ";".join(f"entry({f},{g:g})" for f, g in zip(BANDS, gains))
    return f"lavfi=[firequalizer=gain_entry='{entries}']"


def mode_filter(mode: str, channels: int, layout: str = "") -> str:
    if mode == "night":          # quiet loud scenes, lift quiet ones: no waking the neighbours
        return "lavfi=[acompressor=threshold=0.1:ratio=6:attack=5:release=200:makeup=4,dynaudnorm=f=200:g=11]"
    if mode == "level":          # same loudness for every film / episode
        return "lavfi=[loudnorm=I=-18:LRA=7:TP=-2]"
    if mode == "dialog":
        if channels >= 6:        # the centre channel carries the voices: louder centre, softer rest
            weights = ["1.6" if i == 2 else "0.6" if i == 3 else "0.7" for i in range(channels)]
            lay = layout if layout else f"{channels}c"
            return "lavfi=[pan=" + lay + "|" + "|".join(f"c{i}={w}*c{i}" for i, w in enumerate(weights)) + "]"
        if channels == 2:
            return "lavfi=[dialoguenhance=original=0.6:enhance=1.6]"
        return eq_filter(PRESETS["voice"])              # mono: lift the speech frequencies
    return ""


def build(mode: str, gains, channels: int, layout: str = "") -> str:
    parts = [p for p in (mode_filter(mode, channels, layout), eq_filter(gains)) if p]
    return ",".join(parts)
