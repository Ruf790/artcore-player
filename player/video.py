"""The video surface: libmpv renders into a QOpenGLWidget (render API), so Qt owns the window,
the mouse and the keyboard, and the controls can float over the picture."""
from __future__ import annotations

import ctypes

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QOpenGLContext
from PySide6.QtOpenGLWidgets import QOpenGLWidget


class VideoWidget(QOpenGLWidget):
    frame = Signal()                     # mpv has a new frame (emitted from mpv's thread)
    ready = Signal()                     # the render context exists: files may be loaded now
    clicked = Signal()
    double_clicked = Signal()
    context_menu = Signal(QPoint)
    wheel = Signal(int)                  # +1 / -1 steps
    moved = Signal()

    def __init__(self, mpv_module, player, parent=None):
        super().__init__(parent)
        self._mpv = mpv_module
        self.player = player
        self.ctx = None
        self._gpa = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.frame.connect(self.update, Qt.QueuedConnection)
        # one click toggles pause, a double click goes fullscreen: wait to see which one it is
        self._click = QTimer(self)
        self._click.setSingleShot(True)
        self._click.timeout.connect(self.clicked.emit)

    # ── mpv render context ────────────────────────────────────
    def initializeGL(self):
        ctx = QOpenGLContext.currentContext()

        def get_proc_address(_, name):
            addr = ctx.getProcAddress(name.decode() if isinstance(name, bytes) else name)
            return int(addr) if addr else 0
        self._gpa = self._mpv.MpvGlGetProcAddressFn(get_proc_address)
        self.ctx = self._mpv.MpvRenderContext(self.player, "opengl",
                                              opengl_init_params={"get_proc_address": self._gpa})
        self.ctx.update_cb = self._on_update
        self.ready.emit()

    def _on_update(self):
        try:
            self.frame.emit()
        except RuntimeError:           # widget already gone (shutdown)
            pass

    def paintGL(self):
        if self.ctx is None:
            f = self.context().functions()
            f.glClearColor(0, 0, 0, 1)
            f.glClear(0x4000)          # GL_COLOR_BUFFER_BIT
            return
        r = self.devicePixelRatioF()
        self.ctx.render(flip_y=True, opengl_fbo={"w": int(self.width() * r), "h": int(self.height() * r),
                                                 "fbo": self.defaultFramebufferObject()})

    def shutdown(self):
        """Free the render context before mpv itself is terminated (with the GL context current)."""
        if self.ctx is not None:
            self.makeCurrent()
            try:
                self.ctx.update_cb = None
                self.ctx.free()
            except Exception:
                pass
            self.ctx = None
            self.doneCurrent()

    # ── mouse ─────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            from PySide6.QtWidgets import QApplication
            self._click.start(QApplication.doubleClickInterval())
        elif e.button() == Qt.RightButton:
            self.context_menu.emit(e.globalPosition().toPoint())

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._click.stop()
            self.double_clicked.emit()

    def mouseMoveEvent(self, e):
        self.moved.emit()

    def wheelEvent(self, e):
        d = e.angleDelta().y()
        if d:
            self.wheel.emit(1 if d > 0 else -1)
