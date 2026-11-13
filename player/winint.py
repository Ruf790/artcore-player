"""Windows bits: dark title bar, taskbar id, installer mutex, the folder with libmpv-2.dll."""
from __future__ import annotations

import os
import sys

IS_WIN = sys.platform == "win32"
MUTEX_NAME = "ArtCorePlayerMutex"       # same as AppMutex in setup.iss
_mutex = None


def init_process(app_id: str) -> None:
    if not IS_WIN:
        return
    import ctypes
    global _mutex
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass
    try:
        _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    except Exception:
        pass


def dark_title_bar(win_id: int, dark: bool = True) -> None:
    """DWMWA_USE_IMMERSIVE_DARK_MODE (20; 19 on early Windows 10 builds)."""
    if not IS_WIN:
        return
    import ctypes
    val = ctypes.c_int(1 if dark else 0)
    for attr in (20, 19):
        try:
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(win_id, attr, ctypes.byref(val), ctypes.sizeof(val)) == 0:
                break
        except Exception:
            break


def prepare_libmpv() -> list[str]:
    """Make libmpv-2.dll findable: next to the exe, in PyInstaller's _internal, in the source tree."""
    dirs = []
    for d in (os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else "",
              getattr(sys, "_MEIPASS", ""),
              os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
              os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "libmpv")):
        if d and os.path.isdir(d) and d not in dirs:
            dirs.append(d)
    if IS_WIN:
        os.environ["PATH"] = os.pathsep.join(dirs + [os.environ.get("PATH", "")])
        for d in dirs:
            try:
                os.add_dll_directory(d)
            except (OSError, AttributeError):
                pass
    return dirs


def pictures_dir() -> str:
    if IS_WIN:
        try:
            import ctypes
            from ctypes import wintypes
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 0x27, None, 0, buf) == 0:   # CSIDL_MYPICTURES
                return buf.value
        except Exception:
            pass
    p = os.path.join(os.path.expanduser("~"), "Pictures")
    return p if os.path.isdir(p) else os.path.expanduser("~")


def show_in_explorer(path: str) -> None:
    import subprocess
    if IS_WIN:
        subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
    else:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))
