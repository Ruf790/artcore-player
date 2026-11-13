# Third-party components

ArtCore Player is distributed under the GNU General Public License v3 (see LICENSE).
It contains the following components:

| Component | What for | License |
|---|---|---|
| [mpv](https://mpv.io) — `libmpv-2.dll`, Windows build by [shinchiro/mpv-winbuild-cmake](https://github.com/shinchiro/mpv-winbuild-cmake) | playback engine | GPL v2+ (this build), parts LGPL |
| [FFmpeg](https://ffmpeg.org), libplacebo, libass and other libraries inside libmpv | decoding, rendering, subtitles | GPL / LGPL |
| [Qt 6](https://www.qt.io) via [PySide6](https://pypi.org/project/PySide6/) | user interface | LGPL v3 |
| [python-mpv](https://github.com/jaseg/python-mpv) | Python binding for libmpv | GPL v2+ or LGPL v2.1+ |
| [QtAwesome](https://github.com/spyder-ide/qtawesome) | icons | MIT |
| [Font Awesome Free](https://fontawesome.com) (inside QtAwesome) | icon font | SIL OFL 1.1 (font), CC BY 4.0 (icons) |
| Python | runtime | PSF License |

The source code of mpv and of the libraries it is built from is available from the projects above;
the exact libmpv build used is named in the release notes and in the build log (`tools/fetch_libmpv.py`).
