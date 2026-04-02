"""Bottom-anchored dictation bar — always visible, never steals focus."""

import random
from ctypes import c_void_p

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QApplication,
)


class WaveformWidget(QWidget):
    """Animated sound wave bars — white, calm."""

    NUM_BARS = 5

    def __init__(self):
        super().__init__()
        self.setFixedSize(28, 14)
        self._heights = [0.15] * self.NUM_BARS
        self._active = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)

    def start(self):
        self._active = True
        self._timer.start(180)

    def stop(self):
        self._active = False
        self._timer.stop()
        self._heights = [0.15] * self.NUM_BARS
        self.update()

    def _animate(self):
        for i in range(self.NUM_BARS):
            target = 0.25 + random.random() * 0.75
            self._heights[i] += (target - self._heights[i]) * 0.35
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 200))

        bar_w = 2.5
        gap = (self.width() - bar_w * self.NUM_BARS) / (self.NUM_BARS - 1)
        max_h = self.height()

        for i, h in enumerate(self._heights):
            x = i * (bar_w + gap)
            bar_h = max(2, h * max_h)
            y = (max_h - bar_h) / 2
            painter.drawRoundedRect(QRectF(x, y, bar_w, bar_h), 1.2, 1.2)


class DictationBar(QWidget):
    """Persistent compact bar. Never takes focus from other apps."""

    cancel_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    play_clicked = pyqtSignal()

    BAR_WIDTH = 140
    BAR_HEIGHT = 30
    CORNER_RADIUS = 15
    BG_COLOR = QColor(20, 20, 20, 210)

    def __init__(self):
        super().__init__()
        self._elapsed_seconds = 0
        self._recording = False
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._tick)

        self._setup_window()
        self._setup_ui()

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(self.BAR_WIDTH, self.BAR_HEIGHT)

    def showEvent(self, event):
        """After the window is shown, patch the NSWindow to never activate."""
        super().showEvent(event)
        self._patch_ns_window()

    def _patch_ns_window(self) -> None:
        """Make the underlying NSWindow truly non-activating."""
        try:
            import objc
            import AppKit
            nsview = objc.objc_object(c_void_p=int(self.winId()))
            ns_window = nsview.window()
            if ns_window:
                # Set to panel level, non-activating
                ns_window.setLevel_(AppKit.NSStatusWindowLevel)
                ns_window.setStyleMask_(
                    ns_window.styleMask() | AppKit.NSWindowStyleMaskNonactivatingPanel
                )
                ns_window.setHidesOnDeactivate_(False)
                ns_window.setCanBecomeKeyWindow_(False)
                ns_window.setCanBecomeMainWindow_(False)
        except Exception:
            pass

    def _setup_ui(self) -> None:
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 3, 8, 3)
        self._layout.setSpacing(6)

        # ── Play button (idle) ──
        self._play_btn = QPushButton("\u25b6")
        self._play_btn.setFixedSize(20, 20)
        self._play_btn.setFont(QFont("SF Pro", 8))
        self._play_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._play_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 200, 130, 0.9);
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(100, 200, 130, 1.0);
            }
        """)
        self._play_btn.clicked.connect(self.play_clicked.emit)
        self._layout.addWidget(self._play_btn)

        # ── Cancel button (recording) ──
        self._cancel_btn = QPushButton("\u2715")
        self._cancel_btn.setFixedSize(20, 20)
        self._cancel_btn.setFont(QFont("SF Pro", 8))
        self._cancel_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(140, 50, 50, 0.5);
                color: rgba(255, 255, 255, 0.7);
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(140, 50, 50, 0.8);
            }
        """)
        self._cancel_btn.clicked.connect(self.cancel_clicked.emit)
        self._layout.addWidget(self._cancel_btn)

        # ── Waveform ──
        self._waveform = WaveformWidget()
        self._layout.addWidget(self._waveform)

        # ── Timer ──
        self._timer_label = QLabel("0:00")
        self._timer_label.setFont(QFont("SF Mono", 9))
        self._timer_label.setStyleSheet("color: rgba(255, 255, 255, 0.85);")
        self._layout.addWidget(self._timer_label)

        # ── Stop button ──
        self._stop_btn = QPushButton("\u25a0")
        self._stop_btn.setFixedSize(20, 20)
        self._stop_btn.setFont(QFont("SF Pro", 7))
        self._stop_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(210, 55, 55, 0.85);
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(210, 55, 55, 1.0);
            }
        """)
        self._stop_btn.clicked.connect(self.stop_clicked.emit)
        self._layout.addWidget(self._stop_btn)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(
            0, 0, self.width(), self.height(),
            self.CORNER_RADIUS, self.CORNER_RADIUS,
        )
        painter.fillPath(path, self.BG_COLOR)

    # ── State management ──

    def _set_idle(self) -> None:
        self._play_btn.setVisible(True)
        self._cancel_btn.setVisible(False)
        self._waveform.setVisible(False)
        self._timer_label.setVisible(False)
        self._stop_btn.setVisible(False)
        self._waveform.stop()

    def _set_recording(self) -> None:
        self._play_btn.setVisible(False)
        self._cancel_btn.setVisible(True)
        self._waveform.setVisible(True)
        self._timer_label.setVisible(True)
        self._stop_btn.setVisible(True)
        self._waveform.start()

    # ── Public API ──

    def show_bar(self) -> None:
        self._set_idle()
        self._position_bottom_center()
        self.show()

    def show_recording(self) -> None:
        self._recording = True
        self._elapsed_seconds = 0
        self._timer_label.setText("0:00")
        self._set_recording()
        self._tick_timer.start(1000)

    def hide_recording(self) -> None:
        self._recording = False
        self._tick_timer.stop()
        self._set_idle()

    def _tick(self) -> None:
        self._elapsed_seconds += 1
        minutes = self._elapsed_seconds // 60
        seconds = self._elapsed_seconds % 60
        self._timer_label.setText(f"{minutes}:{seconds:02d}")

    def _position_bottom_center(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.BAR_WIDTH) // 2
            y = geo.y() + geo.height() - self.BAR_HEIGHT - 10
            self.move(x, y)

    def get_elapsed(self) -> float:
        return float(self._elapsed_seconds)
