"""Entry point: one player window; files opened from Explorer go to the running copy."""
from __future__ import annotations

import locale
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

from . import APP_ID, APP_TITLE, VERSION, config, winint
from .i18n import set_lang, t

SERVER_NAME = "ArtCorePlayer-" + (os.environ.get("USERNAME") or os.environ.get("USER") or "user")


def _send_to_running(paths: list[str]) -> bool:
    s = QLocalSocket()
    s.connectToServer(SERVER_NAME)
    if not s.waitForConnected(400):
        return False
    s.write(("\n".join(paths) if paths else "--show").encode("utf-8"))
    s.waitForBytesWritten(1000)
    s.disconnectFromServer()
    return True


def _surface_format() -> None:
    """libmpv's OpenGL renderer wants a 3.3+ core context (the default compatibility one breaks on some drivers)."""
    f = QSurfaceFormat()
    f.setVersion(3, 3)
    f.setProfile(QSurfaceFormat.CoreProfile)
    f.setSwapInterval(1)
    QSurfaceFormat.setDefaultFormat(f)


def load_mpv():
    winint.prepare_libmpv()
    locale.setlocale(locale.LC_NUMERIC, "C")        # libmpv refuses to start with a non-C LC_NUMERIC
    import mpv
    return mpv


def selftest() -> int:
    """CI: the built exe imports everything, finds libmpv, builds the window. Result in %TEMP%."""
    import tempfile
    import traceback
    out = os.path.join(tempfile.gettempdir(), "artcore_player_selftest.txt")
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication(sys.argv)
        mpvmod = load_mpv()
        cfg = config.load()
        from .window import PlayerWindow
        win = PlayerWindow(mpvmod, cfg)
        win.show()
        for _ in range(10):
            app.processEvents()
        ver = win.mpv.mpv_version
        ff = win.mpv.ffmpeg_version
        win.close()
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"OK {VERSION} {ver} ffmpeg {ff}\n")
        return 0
    except Exception:
        with open(out, "w", encoding="utf-8") as f:
            f.write("FAIL\n" + traceback.format_exc())
        return 1


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    paths = [a for a in args if not a.startswith("--")]
    cfg = config.load()
    set_lang(cfg.get("language", "ru"))
    winint.init_process(APP_ID)
    _surface_format()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setStyle("Fusion")
    from . import style
    app.setStyleSheet(style.stylesheet())
    app.setWindowIcon(style.app_icon())
    if cfg.get("language", "ru") == "ru":
        from PySide6.QtCore import QLibraryInfo, QTranslator
        tr = QTranslator(app)
        if tr.load("qtbase_ru", QLibraryInfo.path(QLibraryInfo.TranslationsPath)):
            app.installTranslator(tr)

    if cfg.get("single_window", True) and _send_to_running(paths):
        return 0

    try:
        mpvmod = load_mpv()
    except Exception as e:
        QMessageBox.critical(None, APP_TITLE, t("mpv_missing", e))
        return 1
    locale.setlocale(locale.LC_NUMERIC, "C")         # QApplication may have changed it

    from .window import PlayerWindow
    win = PlayerWindow(mpvmod, cfg)
    win.restore_geometry()
    win.show()

    server = QLocalServer()
    QLocalServer.removeServer(SERVER_NAME)
    server.listen(SERVER_NAME)

    def on_conn():
        s = server.nextPendingConnection()

        def read():
            data = bytes(s.readAll()).decode("utf-8", "replace")
            got = [ln for ln in data.splitlines() if ln and ln != "--show"]
            if win.isMinimized():
                win.showNormal()
            win.raise_()
            win.activateWindow()
            if got:
                win.open_paths(got)
        s.readyRead.connect(read)
    server.newConnection.connect(on_conn)

    if paths:
        QTimer.singleShot(0, lambda: win.open_paths(paths))
    code = app.exec()
    server.close()
    return code
