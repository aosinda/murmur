"""Usage statistics dashboard."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
)


class StatsWindow(QWidget):
    """Displays lifetime usage statistics like Wispr Flow's dashboard."""

    def __init__(self, db=None):
        super().__init__()
        self._db = db
        self._stat_labels: dict[str, QLabel] = {}
        self._setup_window()
        self._setup_ui()
        self.refresh()

    def _setup_window(self) -> None:
        self.setWindowTitle("Murmur — Stats")
        self.setFixedSize(420, 300)
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
        )

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("Your Stats")
        title.setFont(QFont("SF Pro", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Stats grid
        grid = QGridLayout()
        grid.setSpacing(16)

        stats_config = [
            ("weeks_active", "⭐", "Weeks"),
            ("total_words", "🚀", "Words"),
            ("avg_wpm", "🏆", "WPM"),
            ("total_sessions", "🎙️", "Sessions"),
        ]

        for col, (key, emoji, label) in enumerate(stats_config):
            card = self._create_stat_card(key, emoji, label)
            grid.addWidget(card, 0, col)

        layout.addLayout(grid)
        layout.addStretch()

    def _create_stat_card(self, key: str, emoji: str, label: str) -> QFrame:
        """Create a single stat display card."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border-radius: 12px;
                padding: 12px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(4)

        emoji_label = QLabel(emoji)
        emoji_label.setFont(QFont("SF Pro", 20))
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(emoji_label)

        value_label = QLabel("0")
        value_label.setFont(QFont("SF Pro", 22, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)
        self._stat_labels[key] = value_label

        desc_label = QLabel(label)
        desc_label.setFont(QFont("SF Pro", 11))
        desc_label.setStyleSheet("color: #888;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(desc_label)

        return card

    def refresh(self) -> None:
        """Reload stats from database."""
        if not self._db:
            return

        stats = self._db.get_stats()

        formatters = {
            "weeks_active": lambda v: str(v),
            "total_words": lambda v: self._format_number(v),
            "avg_wpm": lambda v: str(v),
            "total_sessions": lambda v: self._format_number(v),
        }

        for key, label in self._stat_labels.items():
            value = stats.get(key, 0)
            fmt = formatters.get(key, str)
            label.setText(fmt(value))

    @staticmethod
    def _format_number(n: int) -> str:
        """Format large numbers: 270100 → 270.1K"""
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(n)
