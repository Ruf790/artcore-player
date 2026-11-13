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
- picture: brightness / contrast / saturation / gamma, smooth motion (interpolation to the monitor's refresh rate)
- mini player on top of other windows, A-B repeat, audio delay
- series: mark the intro once per folder — a Skip button (or automatic skipping) in every episode
- updates itself from GitHub Releases
- continues where you stopped (per file), recent files on the start page
- hardware decoding (D3D11VA / NVDEC / DXVA2), speed 0.25–3×, frame step, screenshots, always on top
- single window: files opened from Explorer go to the running player
- settings in tabs: playback, video (scaling quality, deinterlacing, debanding, HDR tone mapping), sound (output
  device, channels 2.0 / 5.1 / 7.1 downmix, WASAPI exclusive, max volume), subtitles (.srt encoding such as
  Windows-1251, font, size, colour, outline, own style for ASS), interface, system (settings folder, reset)
- repeat (file / playlist, R), rotation (Ctrl+R), open a URL / stream (Ctrl+U), "when playback ends": close the
  player, sleep or shut down the PC (with a 30-second countdown)
- stereo → 5.1 upmix for 5.1 speaker sets (voices to the centre, bass to the sub, ambience to the rears; U)
- Windows media panel (the card over the volume flyout and on the lock screen, with a frame of the film) and the
  media keys ⏮ ⏯ ⏭ — also when the player is not the active window
- Jump List: right click on the taskbar button — recent films with their format icon and resume time,
  "Open file…", "Open address…"
- About window: versions of the player, mpv, FFmpeg and Qt, decoding in use, "copy details" for bug reports
- its own icon for every video format in Explorer (MKV, MP4, AVI, M2TS, VOB, HEVC, ISO…), also in the playlist —
  `tools/make_format_icons.py` draws them and writes the installer block
- Russian and English interface

## Keys

Space — pause · F / double-click — fullscreen · ← → step from Settings, 5 s by default (Ctrl 10 s, Shift 1 min) · ↑ ↓ / wheel — volume ·
A — audio track · S — subtitles · Z / X — subtitle delay · [ ] — speed · PgUp / PgDn — previous / next ·
L — playlist · I — file info · R — repeat · Ctrl+R — rotate · Ctrl+U — open URL · U — stereo → 5.1 · Ctrl+S — screenshot · F1 — all keys

## Build

`build.bat` (Python 3.12/3.13 x64, 7-Zip, Inno Setup 6). GitHub Actions builds the installer and a portable zip
on every push; publishing a release (tag `v1.2.3`) attaches them to it.

License: GNU GPL v3 — see `LICENSE` and `THIRD-PARTY.md`.
