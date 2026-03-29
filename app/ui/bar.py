"""Bottom-anchored dictation bar — appears during recording."""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QApplication, QGraphicsOpacityEffect,
)


class DictationBar(QWidget):
    """Small dark bar anchored to bottom of screen during dictation.

    Shows: [X cancel] [waveform/timer] [■ stop]
    """

    cancel_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    BAR_HEIGHT = 48
    BAR_WIDTH = 320
    CORNER_RADIUS = 24
    BG_COLOR = QColor(30, 30, 30, 240)
    TEXT_COLOR = QColor(255, 255, 255)
    CANCEL_COLOR = QColor(180, 60, 60)
    STOP_COLOR = QColor(220, 60, 60)
    RECORDING_DOT_COLOR = QColor(220, 60, 60)

    def __init__(self):
        super().__init__()
        self._elapsed_seconds = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._setup_window()
        self._setup_ui()

    def _setup_window(self) -> None:
        """Configure window as a floating overlay."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # Don't show in dock/taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(self.BAR_WIDTH, self.BAR_HEIGHT)
        self._position_bottom_center()

    def _setup_ui(self) -> None:
        """Build the bar layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Cancel button (X)
        self._cancel_btn = QPushButton("✕")
        self._cancel_btn.setFixedSize(28, 28)
        self._cancel_btn.setFont(QFont("SF Pro", 14))
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(180, 60, 60, 0.3);
                color: {self.TEXT_COLOR.name()};
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(180, 60, 60, 0.6);
            }}
        """)
        self._cancel_btn.clicked.connect(self.cancel_clicked.emit)
        layout.addWidget(self._cancel_btn)

        # Recording indicator + timer
        self._recording_dot = QLabel("●")
        self._recording_dot.setFont(QFont("SF Pro", 10))
        self._recording_dot.setStyleSheet(f"color: {self.RECORDING_DOT_COLOR.name()};")
        layout.addWidget(self._recording_dot)

        self._timer_label = QLabel("0:00")
        self._timer_label.setFont(QFont("SF Mono", 13))
        self._timer_label.setStyleSheet(f"color: {self.TEXT_COLOR.name()};")
        layout.addWidget(self._timer_label)

        layout.addStretch()

        # Stop button (■)
        self._stop_btn = QPushButton("■")
        self._stop_btn.setFixedSize(28, 28)
        self._stop_btn.setFont(QFont("SF Pro", 12))
        self._stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(220, 60, 60, 0.8);
                color: {self.TEXT_COLOR.name()};
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(220, 60, 60, 1.0);
            }}
        """)
        self._stop_btn.clicked.connect(self.stop_clicked.emit)
        layout.addWidget(self._stop_btn)

    def paintEvent(self, event) -> None:
        """Draw rounded dark background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(
            0, 0, self.width(), self.height(),
            self.CORNER_RADIUS, self.CORNER_RADIUS,
        )

        painter.fillPath(path, self.BG_COLOR)

    def show_recording(self) -> None:
        """Show the bar and start the timer."""
        print("[Murmur] Bar: show_recording called", flush=True)
        self._elapsed_seconds = 0
        self._timer_label.setText("0:00")
        self._position_bottom_center()
        self.show()
        self._timer.start(1000)

    def hide_recording(self) -> None:
        """Hide the bar and stop the timer."""
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        """Update the timer display."""
        self._elapsed_seconds += 1
        minutes = self._elapsed_seconds // 60
        seconds = self._elapsed_seconds % 60
        self._timer_label.setText(f"{minutes}:{seconds:02d}")

        # Blink recording dot
        visible = self._elapsed_seconds % 2 == 0
        self._recording_dot.setStyleSheet(
            f"color: {'#dc3c3c' if visible else 'transparent'};"
        )

    def _position_bottom_center(self) -> None:
        """Place bar at bottom center of the primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.BAR_WIDTH) // 2
            y = geo.y() + geo.height() - self.BAR_HEIGHT - 20
            self.move(x, y)

    def get_elapsed(self) -> float:
        """Return elapsed recording time in seconds."""
        return float(self._elapsed_seconds)
