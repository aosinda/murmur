"""Main application window — dashboard, history, settings."""

import platform
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QApplication, QFrame,
)


DARK_BG = "#1a1a1a"
CARD_BG = "#252525"
ACCENT = "#64c882"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#999999"
RECORDING_COLOR = "#e05555"
PROCESSING_COLOR = "#e0a855"


class StatCard(QFrame):
    """Single stat card for the dashboard."""

    def __init__(self, title: str, value: str, subtitle: str = ""):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border-radius: 12px;
            }}
        """)
        self.setFixedHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self._title = QLabel(title)
        self._title.setFont(QFont("SF Pro", 11))
        self._title.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(self._title)

        self._value = QLabel(value)
        self._value.setFont(QFont("SF Pro", 24, QFont.Weight.Bold))
        self._value.setStyleSheet(f"color: {TEXT_PRIMARY};")
        layout.addWidget(self._value)

        if subtitle:
            self._subtitle = QLabel(subtitle)
            self._subtitle.setFont(QFont("SF Pro", 10))
            self._subtitle.setStyleSheet(f"color: {TEXT_SECONDARY};")
            layout.addWidget(self._subtitle)

    def update_value(self, value: str, subtitle: str = ""):
        self._value.setText(value)
        if hasattr(self, "_subtitle") and subtitle:
            self._subtitle.setText(subtitle)


class TranscriptionItem(QFrame):
    """Single transcription entry in the history list."""

    def __init__(self, text: str, language: str, timestamp: str):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border-radius: 10px;
            }}
        """)
        self._text = text

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)

        text_col = QVBoxLayout()
        text_label = QLabel(text[:150] + ("..." if len(text) > 150 else ""))
        text_label.setFont(QFont("SF Pro", 12))
        text_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        text_label.setWordWrap(True)
        text_col.addWidget(text_label)

        meta = QLabel(f"{language}  ·  {timestamp}")
        meta.setFont(QFont("SF Pro", 10))
        meta.setStyleSheet(f"color: {TEXT_SECONDARY};")
        text_col.addWidget(meta)

        layout.addLayout(text_col, stretch=1)

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedSize(60, 28)
        copy_btn.setFont(QFont("SF Pro", 11))
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ACCENT};
                border: 1px solid {ACCENT};
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: rgba(100, 200, 130, 0.15); }}
        """)
        copy_btn.clicked.connect(self._copy)
        layout.addWidget(copy_btn, alignment=Qt.AlignmentFlag.AlignTop)

    def _copy(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._text)


class MainWindow(QWidget):
    """Main application window with dashboard and settings."""

    settings_changed = pyqtSignal(dict)

    def __init__(self, db):
        super().__init__()
        self._db = db
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        self.setWindowTitle("Murmur")
        self.setMinimumSize(560, 500)
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT_PRIMARY};")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Status bar at top ──
        self._status_bar = QWidget()
        self._status_bar.setFixedHeight(40)
        self._status_bar.setStyleSheet(f"background-color: {CARD_BG};")
        status_layout = QHBoxLayout(self._status_bar)
        status_layout.setContentsMargins(16, 0, 16, 0)

        self._status_dot = QLabel("●")
        self._status_dot.setFont(QFont("SF Pro", 10))
        self._status_dot.setStyleSheet(f"color: {ACCENT};")
        status_layout.addWidget(self._status_dot)

        self._status_label = QLabel("Ready")
        self._status_label.setFont(QFont("SF Pro", 12))
        self._status_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        status_layout.addWidget(self._status_label)

        status_layout.addStretch()

        shortcut_hint = QLabel("Fn hold = talk  ·  Fn+Space = toggle")
        if platform.system() == "Windows":
            shortcut_hint = QLabel("Ctrl+Shift hold = talk  ·  Ctrl+Shift+Space = toggle")
        shortcut_hint.setFont(QFont("SF Pro", 11))
        shortcut_hint.setStyleSheet(f"color: {TEXT_SECONDARY};")
        status_layout.addWidget(shortcut_hint)

        layout.addWidget(self._status_bar)

        # ── Tab widget ──
        self._tabs = QTabWidget()
        self._tabs.setFont(QFont("SF Pro", 12))
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {DARK_BG};
            }}
            QTabBar::tab {{
                background-color: {DARK_BG};
                color: {TEXT_SECONDARY};
                padding: 10px 20px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                color: {TEXT_PRIMARY};
                border-bottom: 2px solid {ACCENT};
            }}
            QTabBar::tab:hover {{
                color: {TEXT_PRIMARY};
            }}
        """)

        self._tabs.addTab(self._dashboard_tab(), "Dashboard")
        self._tabs.addTab(self._history_tab(), "History")

        layout.addWidget(self._tabs)

    # ── Dashboard tab ─────────────────────────────────────────────

    def _dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Stats grid (2x2)
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        self._card_weeks = StatCard("Weeks Active", "0")
        self._card_words = StatCard("Total Words", "0")
        row1.addWidget(self._card_weeks)
        row1.addWidget(self._card_words)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)
        self._card_wpm = StatCard("Avg WPM", "0")
        self._card_sessions = StatCard("Sessions", "0")
        row2.addWidget(self._card_wpm)
        row2.addWidget(self._card_sessions)
        layout.addLayout(row2)

        layout.addStretch()
        return tab

    # ── History tab ───────────────────────────────────────────────

    def _history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Recent Transcriptions")
        title.setFont(QFont("SF Pro", 14, QFont.Weight.Bold))
        header.addWidget(title)

        self._history_hint = QLabel("Last 24 hours")
        self._history_hint.setFont(QFont("SF Pro", 11))
        self._history_hint.setStyleSheet(f"color: {TEXT_SECONDARY};")
        header.addWidget(self._history_hint, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)

        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {DARK_BG};
            }}
            QScrollBar:vertical {{
                background: {DARK_BG};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: #444444;
                border-radius: 4px;
            }}
        """)

        self._history_container = QWidget()
        self._history_layout = QVBoxLayout(self._history_container)
        self._history_layout.setContentsMargins(0, 0, 0, 0)
        self._history_layout.setSpacing(8)
        self._history_layout.addStretch()

        scroll.setWidget(self._history_container)
        layout.addWidget(scroll)

        return tab

    # ── Public methods ────────────────────────────────────────────

    def refresh(self):
        """Reload stats and history from database."""
        self._refresh_stats()
        self._refresh_history()

    def set_status(self, status: str):
        """Update status indicator: 'ready', 'recording', 'processing'."""
        if status == "recording":
            self._status_dot.setStyleSheet(f"color: {RECORDING_COLOR};")
            self._status_label.setText("Recording...")
        elif status == "processing":
            self._status_dot.setStyleSheet(f"color: {PROCESSING_COLOR};")
            self._status_label.setText("Processing...")
        else:
            self._status_dot.setStyleSheet(f"color: {ACCENT};")
            self._status_label.setText("Ready")

    def _refresh_stats(self):
        stats = self._db.get_stats()
        if not stats:
            return

        self._card_weeks.update_value(str(stats.get("weeks_active", 0)))
        self._card_sessions.update_value(str(stats.get("total_sessions", 0)))
        self._card_wpm.update_value(str(stats.get("avg_wpm", 0)))

        words = stats.get("total_words", 0)
        if words >= 1_000_000:
            self._card_words.update_value(f"{words / 1_000_000:.1f}M")
        elif words >= 1_000:
            self._card_words.update_value(f"{words / 1_000:.1f}K")
        else:
            self._card_words.update_value(str(words))

    def _refresh_history(self):
        # Clear existing items
        while self._history_layout.count() > 1:
            item = self._history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        dictations = self._db.get_recent_dictations(limit=30)

        if not dictations:
            empty = QLabel("No transcriptions yet.\nHold Fn and start talking!")
            empty.setFont(QFont("SF Pro", 13))
            empty.setStyleSheet(f"color: {TEXT_SECONDARY};")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._history_layout.insertWidget(0, empty)
            return

        for d in dictations:
            entry = TranscriptionItem(
                text=d["cleaned_text"],
                language=d.get("language", ""),
                timestamp=d.get("timestamp", ""),
            )
            self._history_layout.insertWidget(
                self._history_layout.count() - 1, entry
            )
