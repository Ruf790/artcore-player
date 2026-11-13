# ArtCore Player

Video player for Windows on the **mpv** engine (libmpv) with a modern Qt interface — a companion of
[ArtCore Client](https://github.com/Ruf790/artcore-torrent-client).

- plays everything mpv plays: HEVC / AV1 / VP9, 4K, HDR10 / HLG / Dolby Vision (tone-mapped to SDR), any containers
- all audio tracks and subtitles (embedded and external, auto-loaded by name), subtitle delay and size
- controls float over the picture and hide while you watch; subtitles move up while the controls are shown
- badges with the format: 4K · HDR10 · HEVC · 5.1 · TrueHD
- frame previews over the seek bar (HDR tone-mapped), chapters: names, list, PgUp / PgDn
- sound: night mode, volume levelling, clear dialogue, 10-band equalizer with presets
- the folder is the playlist: next episode starts by itself (Shift+PgUp / PgDn, P / N)
- Blu-ray / DVD folders and .iso images, disc titles
- updates itself from GitHub Releases
- continues where you stopped (per file), recent files on the start page
- hardware decoding (D3D11VA / NVDEC / DXVA2), speed 0.25–3×, frame step, screenshots, always on top
- single window: files opened from Explorer go to the running player
- Russian and English interface

## Keys

Space — pause · F / double-click — fullscreen · ← → 5 s (Ctrl 10 s, Shift 1 min) · ↑ ↓ / wheel — volume ·
A — audio track · S — subtitles · Z / X — subtitle delay · [ ] — speed · PgUp / PgDn — previous / next ·
L — playlist · I — file info · Ctrl+S — screenshot · F1 — all keys

## Build

`build.bat` (Python 3.12/3.13 x64, 7-Zip, Inno Setup 6). GitHub Actions builds the installer and a portable zip
on every push; publishing a release (tag `v1.2.3`) attaches them to it.

License: GNU GPL v3 — see `LICENSE` and `THIRD-PARTY.md`.
