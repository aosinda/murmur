"""First-launch onboarding — API key, shortcuts tutorial, permissions."""

import os
import sys
import platform
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QApplication,
)


DARK_BG = "#1a1a1a"
CARD_BG = "#252525"
ACCENT = "#64c882"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#999999"
ERROR_COLOR = "#e05555"

BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {ACCENT};
        color: #1a1a1a;
        border: none;
        border-radius: 10px;
        padding: 12px 32px;
        font-size: 15px;
        font-weight: bold;
    }}
    QPushButton:hover {{ background-color: #7ad49a; }}
    QPushButton:disabled {{ background-color: #444444; color: #888888; }}
"""

SECONDARY_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        border: 1px solid #444444;
        border-radius: 10px;
        padding: 10px 24px;
        font-size: 13px;
    }}
    QPushButton:hover {{ border-color: {ACCENT}; color: {TEXT_PRIMARY}; }}
"""


class OnboardingWindow(QWidget):
    """Multi-step onboarding for first-time users."""

    def __init__(self, db, on_complete):
        super().__init__()
        self._db = db
        self._on_complete = on_complete
        self._setup_window()
        self._setup_pages()

    def _setup_window(self):
        self.setWindowTitle("Murmur")
        self.setFixedSize(520, 480)
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT_PRIMARY};")

        self._stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

    def _setup_pages(self):
        self._stack.addWidget(self._welcome_page())
        self._stack.addWidget(self._api_key_page())
        self._stack.addWidget(self._shortcuts_page())
        self._stack.addWidget(self._permissions_page())

    def _make_page(self):
        page = QWidget()
        page.setStyleSheet(f"background-color: {DARK_BG};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        return page, layout

    # ── Page 1: Welcome ───────────────────────────────────────────

    def _welcome_page(self):
        page, layout = self._make_page()

        layout.addStretch()

        icon = QLabel("🎙")
        icon.setFont(QFont("Apple Color Emoji", 48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        title = QLabel("Murmur")
        title.setFont(QFont("SF Pro", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Private voice dictation.\nYour words stay yours.")
        subtitle.setFont(QFont("SF Pro", 14))
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addStretch()

        btn = QPushButton("Get Started")
        btn.setStyleSheet(BUTTON_STYLE)
        btn.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        return page

    # ── Page 2: API Key ───────────────────────────────────────────

    def _api_key_page(self):
        page, layout = self._make_page()

        title = QLabel("OpenAI API Key")
        title.setFont(QFont("SF Pro", 22, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel("Murmur uses OpenAI for transcription and text cleanup.\nYour key is stored locally and never shared.")
        desc.setFont(QFont("SF Pro", 13))
        desc.setStyleSheet(f"color: {TEXT_SECONDARY};")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(8)

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("sk-...")
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setFont(QFont("SF Mono", 13))
        self._key_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {CARD_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid #444444;
                border-radius: 8px;
                padding: 12px;
            }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
        """)
        layout.addWidget(self._key_input)

        self._key_status = QLabel("")
        self._key_status.setFont(QFont("SF Pro", 12))
        layout.addWidget(self._key_status)

        layout.addStretch()

        btn_row = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        btn_row.addWidget(back_btn)

        self._validate_btn = QPushButton("Validate & Continue")
        self._validate_btn.setStyleSheet(BUTTON_STYLE)
        self._validate_btn.clicked.connect(self._validate_api_key)
        btn_row.addWidget(self._validate_btn)

        layout.addLayout(btn_row)
        return page

    def _validate_api_key(self):
        key = self._key_input.text().strip()
        if not key:
            self._key_status.setText("Please enter your API key.")
            self._key_status.setStyleSheet(f"color: {ERROR_COLOR};")
            return

        self._validate_btn.setEnabled(False)
        self._key_status.setText("Testing key...")
        self._key_status.setStyleSheet(f"color: {TEXT_SECONDARY};")
        QApplication.processEvents()

        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            client.models.list()

            # Save key
            env_path = Path.home() / ".murmur" / ".env"
            env_path.parent.mkdir(parents=True, exist_ok=True)
            env_path.write_text(f"OPENAI_API_KEY={key}\n")
            os.environ["OPENAI_API_KEY"] = key

            self._key_status.setText("Key valid!")
            self._key_status.setStyleSheet(f"color: {ACCENT};")
            QTimer.singleShot(600, lambda: self._stack.setCurrentIndex(2))

        except Exception as e:
            self._key_status.setText(f"Invalid key: {e}")
            self._key_status.setStyleSheet(f"color: {ERROR_COLOR};")

        self._validate_btn.setEnabled(True)

    # ── Page 3: Shortcuts ─────────────────────────────────────────

    def _shortcuts_page(self):
        page, layout = self._make_page()

        title = QLabel("Shortcuts")
        title.setFont(QFont("SF Pro", 22, QFont.Weight.Bold))
        layout.addWidget(title)

        shortcuts = [
            ("Fn (hold)", "Push-to-talk — hold to record, release to transcribe"),
            ("Fn + Space", "Toggle mode — press to start, press Fn again to stop"),
            ("Escape", "Cancel current recording"),
            ("Ctrl + Cmd + V", "Re-insert last transcription"),
        ]

        if platform.system() == "Windows":
            shortcuts = [
                ("Ctrl + Shift (hold)", "Push-to-talk — hold to record, release to transcribe"),
                ("Ctrl + Shift + Space", "Toggle mode — press to start, press again to stop"),
                ("Escape", "Cancel current recording"),
                ("Ctrl + Win + V", "Re-insert last transcription"),
            ]

        for key, desc in shortcuts:
            row = QWidget()
            row.setStyleSheet(f"background-color: {CARD_BG}; border-radius: 10px;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(16, 12, 16, 12)

            key_label = QLabel(key)
            key_label.setFont(QFont("SF Mono", 13, QFont.Weight.Bold))
            key_label.setFixedWidth(160)
            row_layout.addWidget(key_label)

            desc_label = QLabel(desc)
            desc_label.setFont(QFont("SF Pro", 12))
            desc_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
            desc_label.setWordWrap(True)
            row_layout.addWidget(desc_label)

            layout.addWidget(row)

        layout.addStretch()

        btn_row = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        btn_row.addWidget(back_btn)

        next_btn = QPushButton("Next")
        next_btn.setStyleSheet(BUTTON_STYLE)
        next_btn.clicked.connect(lambda: self._stack.setCurrentIndex(3))
        btn_row.addWidget(next_btn)

        layout.addLayout(btn_row)
        return page

    # ── Page 4: Permissions ───────────────────────────────────────

    def _permissions_page(self):
        page, layout = self._make_page()

        title = QLabel("Almost Ready")
        title.setFont(QFont("SF Pro", 22, QFont.Weight.Bold))
        layout.addWidget(title)

        if platform.system() == "Darwin":
            perms_text = (
                "Murmur needs two macOS permissions:\n\n"
                "1. Accessibility — so it can detect keyboard shortcuts "
                "and paste text into your apps\n\n"
                "2. Microphone — so it can hear you\n\n"
                "macOS will ask you to grant these when you first use Murmur. "
                "Click Allow when prompted."
            )
        else:
            perms_text = (
                "Murmur needs microphone access to record your voice.\n\n"
                "Windows will ask you to grant this when you first use Murmur."
            )

        desc = QLabel(perms_text)
        desc.setFont(QFont("SF Pro", 13))
        desc.setStyleSheet(f"color: {TEXT_SECONDARY};")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

        tip = QLabel("💡 Look for the green dot in your menu bar — that's Murmur.")
        tip.setFont(QFont("SF Pro", 12))
        tip.setStyleSheet(f"color: {ACCENT};")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        layout.addSpacing(8)

        btn_row = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(2))
        btn_row.addWidget(back_btn)

        done_btn = QPushButton("Start Murmur")
        done_btn.setStyleSheet(BUTTON_STYLE)
        done_btn.clicked.connect(self._finish)
        btn_row.addWidget(done_btn)

        layout.addLayout(btn_row)
        return page

    def _finish(self):
        self._db.set_setting("onboarding_complete", "true")
        self.hide()
        self._on_complete()
