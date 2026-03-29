"""Dictionary editor — add/edit/remove word mappings."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox,
)


class DictionaryEditor(QWidget):
    """UI for managing the word replacement dictionary.

    Example: "bright kids" → "BrAIght Kids"
    """

    dictionary_updated = pyqtSignal(dict)

    def __init__(self, formatter=None):
        super().__init__()
        self._formatter = formatter
        self._setup_window()
        self._setup_ui()
        self._load_entries()

    def _setup_window(self) -> None:
        self.setWindowTitle("Murmur — Dictionary")
        self.setFixedSize(500, 480)
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
        )

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Dictionary")
        title.setFont(QFont("SF Pro", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel(
            "When you say the word on the left, Murmur will output the word on the right."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        # ── Add new entry ──
        add_layout = QHBoxLayout()

        self._spoken_input = QLineEdit()
        self._spoken_input.setPlaceholderText("You say...")
        self._spoken_input.setMinimumHeight(36)
        add_layout.addWidget(self._spoken_input)

        arrow = QLabel("→")
        arrow.setFont(QFont("SF Pro", 16))
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_layout.addWidget(arrow)

        self._replacement_input = QLineEdit()
        self._replacement_input.setPlaceholderText("Output as...")
        self._replacement_input.setMinimumHeight(36)
        add_layout.addWidget(self._replacement_input)

        add_btn = QPushButton("Add")
        add_btn.setMinimumHeight(36)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        add_btn.clicked.connect(self._add_entry)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        # ── Table of entries ──
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["You say", "Output as", ""])
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(2, 60)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self._table)

        # ── Entry count ──
        self._count_label = QLabel("0 entries")
        self._count_label.setStyleSheet("color: #999;")
        layout.addWidget(self._count_label)

    def _add_entry(self) -> None:
        """Add a new dictionary entry."""
        spoken = self._spoken_input.text().strip()
        replacement = self._replacement_input.text().strip()

        if not spoken or not replacement:
            return

        if self._formatter:
            self._formatter.add_word(spoken, replacement)

        self._spoken_input.clear()
        self._replacement_input.clear()
        self._load_entries()

    def _remove_entry(self, spoken: str) -> None:
        """Remove a dictionary entry."""
        if self._formatter:
            self._formatter.remove_word(spoken)
        self._load_entries()

    def _load_entries(self) -> None:
        """Reload table from formatter's dictionary."""
        entries = {}
        if self._formatter:
            entries = self._formatter.get_dictionary()

        self._table.setRowCount(len(entries))

        for row, (spoken, replacement) in enumerate(entries.items()):
            spoken_item = QTableWidgetItem(spoken)
            spoken_item.setFlags(spoken_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, spoken_item)

            replacement_item = QTableWidgetItem(replacement)
            replacement_item.setFlags(
                replacement_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            self._table.setItem(row, 1, replacement_item)

            # Delete button
            delete_btn = QPushButton("✕")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(220, 60, 60, 0.2);
                    color: #dc3c3c;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(220, 60, 60, 0.4);
                }
            """)
            # Capture spoken in closure
            delete_btn.clicked.connect(
                lambda checked, s=spoken: self._remove_entry(s)
            )
            self._table.setCellWidget(row, 2, delete_btn)

        self._count_label.setText(f"{len(entries)} entries")
        self.dictionary_updated.emit(entries)
