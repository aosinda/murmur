"""First-launch onboarding — mode selection, API key, shortcuts, permissions."""

import os
import sys
import platform
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QApplication, QProgressBar,
)


DARK_BG = "#111111"
CARD_BG = "#1e1e1e"
CARD_SELECTED = "#1a2e20"
ACCENT = "#64c882"
ACCENT_GLOW = "rgba(100, 200, 130, 0.12)"
TEXT_PRIMARY = "#f0f0f0"
TEXT_SECONDARY = "#777777"
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


def _card_style(selected=False):
    bg = CARD_SELECTED if selected else CARD_BG
    border = ACCENT if selected else "#2a2a2a"
    glow = f"0 0 12px {ACCENT_GLOW}" if selected else "none"
    return f"""
        QWidget#modeCard {{
            background-color: {bg};
            border: 2px solid {border};
            border-radius: 14px;
            padding: 4px;
        }}
    """


class OnboardingWindow(QWidget):
    """Multi-step onboarding for first-time users."""

    PAGE_WELCOME = 0
    PAGE_MODE = 1
    PAGE_API_KEY = 2
    PAGE_LOCAL_SETUP = 3
    PAGE_SHORTCUTS = 4
    PAGE_PERMISSIONS = 5

    def __init__(self, db, on_complete):
        super().__init__()
        self._db = db
        self._on_complete = on_complete
        self._selected_mode = None  # "cloud" or "local"
        self._setup_window()
        self._setup_pages()

    def _setup_window(self):
        self.setWindowTitle("Murmur")
        self.setFixedSize(520, 520)
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT_PRIMARY};")

        self._stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

    def _setup_pages(self):
        self._stack.addWidget(self._welcome_page())       # 0
        self._stack.addWidget(self._mode_page())           # 1
        self._stack.addWidget(self._api_key_page())        # 2
        self._stack.addWidget(self._local_setup_page())    # 3
        self._stack.addWidget(self._shortcuts_page())      # 4
        self._stack.addWidget(self._permissions_page())    # 5

    def _make_page(self):
        page = QWidget()
        page.setStyleSheet(f"background-color: {DARK_BG};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        return page, layout

    # ── Page 0: Welcome ───────────────────────────────────────────

    def _welcome_page(self):
        page, layout = self._make_page()
        layout.addStretch()

        icon = QLabel("\U0001f399")
        icon.setFont(QFont("Apple Color Emoji", 48))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        title = QLabel("Murmur")
        title.setFont(QFont("SF Pro", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Voice dictation that stays private.")
        subtitle.setFont(QFont("SF Pro", 15))
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        tagline = QLabel("Your words, your choice — cloud or fully offline.")
        tagline.setFont(QFont("SF Pro", 12))
        tagline.setStyleSheet(f"color: #555555;")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tagline)

        layout.addStretch()

        btn = QPushButton("Get Started")
        btn.setStyleSheet(BUTTON_STYLE)
        btn.clicked.connect(lambda: self._stack.setCurrentIndex(self.PAGE_MODE))
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        return page

    # ── Page 1: Mode selection ────────────────────────────────────

    def _mode_page(self):
        page, layout = self._make_page()

        title = QLabel("How do you want to transcribe?")
        title.setFont(QFont("SF Pro", 20, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addSpacing(12)

        # Cloud card
        self._cloud_card = QWidget()
        self._cloud_card.setObjectName("modeCard")
        self._cloud_card.setStyleSheet(_card_style(False))
        self._cloud_card.setCursor(Qt.CursorShape.PointingHandCursor)
        cloud_layout = QHBoxLayout(self._cloud_card)
        cloud_layout.setContentsMargins(18, 16, 18, 16)
        cloud_layout.setSpacing(14)

        cloud_icon = QLabel("\u2601")
        cloud_icon.setFont(QFont("SF Pro", 28))
        cloud_icon.setFixedWidth(40)
        cloud_layout.addWidget(cloud_icon, alignment=Qt.AlignmentFlag.AlignTop)

        cloud_text_col = QVBoxLayout()
        cloud_text_col.setSpacing(4)
        cloud_title = QLabel("Cloud")
        cloud_title.setFont(QFont("SF Pro", 15, QFont.Weight.Bold))
        cloud_text_col.addWidget(cloud_title)

        cloud_sub = QLabel("Best accuracy  \u00b7  OpenAI API key required")
        cloud_sub.setFont(QFont("SF Pro", 12))
        cloud_sub.setStyleSheet(f"color: {ACCENT};")
        cloud_text_col.addWidget(cloud_sub)

        cloud_desc = QLabel("Whisper + GPT for transcription and smart cleanup.\nAbout $6/month with heavy daily use.")
        cloud_desc.setFont(QFont("SF Pro", 11))
        cloud_desc.setStyleSheet(f"color: {TEXT_SECONDARY};")
        cloud_desc.setWordWrap(True)
        cloud_text_col.addWidget(cloud_desc)

        cloud_layout.addLayout(cloud_text_col)

        self._cloud_card.mousePressEvent = lambda _: self._select_mode("cloud")
        layout.addWidget(self._cloud_card)

        layout.addSpacing(10)

        # Local card
        self._local_card = QWidget()
        self._local_card.setObjectName("modeCard")
        self._local_card.setStyleSheet(_card_style(False))
        self._local_card.setCursor(Qt.CursorShape.PointingHandCursor)
        local_layout = QHBoxLayout(self._local_card)
        local_layout.setContentsMargins(18, 16, 18, 16)
        local_layout.setSpacing(14)

        local_icon = QLabel("\U0001f4bb")
        local_icon.setFont(QFont("SF Pro", 28))
        local_icon.setFixedWidth(40)
        local_layout.addWidget(local_icon, alignment=Qt.AlignmentFlag.AlignTop)

        local_text_col = QVBoxLayout()
        local_text_col.setSpacing(4)
        local_title = QLabel("Local")
        local_title.setFont(QFont("SF Pro", 15, QFont.Weight.Bold))
        local_text_col.addWidget(local_title)

        local_sub = QLabel("Fully offline  \u00b7  Free  \u00b7  No account needed")
        local_sub.setFont(QFont("SF Pro", 12))
        local_sub.setStyleSheet(f"color: {ACCENT};")
        local_text_col.addWidget(local_sub)

        local_desc = QLabel("Runs a local Whisper model on your machine.\nDownloads ~150 MB once, then works without internet.")
        local_desc.setFont(QFont("SF Pro", 11))
        local_desc.setStyleSheet(f"color: {TEXT_SECONDARY};")
        local_desc.setWordWrap(True)
        local_text_col.addWidget(local_desc)

        local_layout.addLayout(local_text_col)

        self._local_card.mousePressEvent = lambda _: self._select_mode("local")
        layout.addWidget(self._local_card)

        layout.addStretch()

        btn_row = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(self.PAGE_WELCOME))
        btn_row.addWidget(back_btn)

        self._mode_next_btn = QPushButton("Continue")
        self._mode_next_btn.setStyleSheet(BUTTON_STYLE)
        self._mode_next_btn.setEnabled(False)
        self._mode_next_btn.clicked.connect(self._mode_next)
        btn_row.addWidget(self._mode_next_btn)

        layout.addLayout(btn_row)
        return page

    def _select_mode(self, mode: str):
        self._selected_mode = mode
        self._cloud_card.setStyleSheet(_card_style(mode == "cloud"))
        self._local_card.setStyleSheet(_card_style(mode == "local"))
        self._mode_next_btn.setEnabled(True)

    def _mode_next(self):
        if self._selected_mode == "cloud":
            self._stack.setCurrentIndex(self.PAGE_API_KEY)
        else:
            self._stack.setCurrentIndex(self.PAGE_LOCAL_SETUP)

    # ── Page 2: API Key (cloud mode) ─────────────────────────────

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
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(self.PAGE_MODE))
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

            env_path = Path.home() / ".murmur" / ".env"
            env_path.parent.mkdir(parents=True, exist_ok=True)
            env_path.write_text(f"OPENAI_API_KEY={key}\n")
            os.environ["OPENAI_API_KEY"] = key

            self._db.set_setting("transcription_mode", "cloud")

            self._key_status.setText("Key valid!")
            self._key_status.setStyleSheet(f"color: {ACCENT};")
            QTimer.singleShot(600, lambda: self._stack.setCurrentIndex(self.PAGE_SHORTCUTS))

        except Exception as e:
            self._key_status.setText(f"Invalid key: {e}")
            self._key_status.setStyleSheet(f"color: {ERROR_COLOR};")

        self._validate_btn.setEnabled(True)

    # ── Page 3: Local setup ───────────────────────────────────────

    def _local_setup_page(self):
        page, layout = self._make_page()

        title = QLabel("Local Model Setup")
        title.setFont(QFont("SF Pro", 22, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel(
            "Murmur will download a local Whisper model (~150 MB).\n"
            "This happens once. After that, everything runs offline."
        )
        desc.setFont(QFont("SF Pro", 13))
        desc.setStyleSheet(f"color: {TEXT_SECONDARY};")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(16)

        self._local_progress = QProgressBar()
        self._local_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {CARD_BG};
                border: none;
                border-radius: 6px;
                height: 12px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
                border-radius: 6px;
            }}
        """)
        self._local_progress.setVisible(False)
        layout.addWidget(self._local_progress)

        self._local_status = QLabel("")
        self._local_status.setFont(QFont("SF Pro", 12))
        self._local_status.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(self._local_status)

        layout.addStretch()

        # Model info
        info = QLabel(
            "Model: whisper-base (74M parameters)\n"
            "Languages: auto-detect\n"
            "Speed: ~1s per 10s of audio on Apple Silicon"
        )
        info.setFont(QFont("SF Pro", 11))
        info.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(info)

        layout.addSpacing(8)

        btn_row = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(self.PAGE_MODE))
        btn_row.addWidget(back_btn)

        self._download_btn = QPushButton("Download & Continue")
        self._download_btn.setStyleSheet(BUTTON_STYLE)
        self._download_btn.clicked.connect(self._download_local_model)
        btn_row.addWidget(self._download_btn)

        layout.addLayout(btn_row)
        return page

    def _download_local_model(self):
        import threading

        self._download_btn.setEnabled(False)
        self._local_progress.setVisible(True)
        self._local_progress.setRange(0, 0)  # Indeterminate
        self._local_status.setText("Downloading model... this may take a minute.")
        QApplication.processEvents()

        def _do_download():
            try:
                from app.transcription.whisper_local import LocalWhisperClient
                client = LocalWhisperClient()
                # Loading the client triggers model download
                self._db.set_setting("transcription_mode", "local")
                self._local_status.setText("Model ready!")
                self._local_status.setStyleSheet(f"color: {ACCENT};")
                self._local_progress.setRange(0, 1)
                self._local_progress.setValue(1)
                QTimer.singleShot(600, lambda: self._stack.setCurrentIndex(self.PAGE_SHORTCUTS))
            except Exception as e:
                self._local_status.setText(f"Error: {e}")
                self._local_status.setStyleSheet(f"color: {ERROR_COLOR};")
                self._local_progress.setVisible(False)
                self._download_btn.setEnabled(True)

        thread = threading.Thread(target=_do_download, daemon=True)
        thread.start()

    # ── Page 4: Shortcuts ─────────────────────────────────────────

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
                ("Ctrl+Shift (hold)", "Push-to-talk — hold to record, release to transcribe"),
                ("Ctrl+Shift+Space", "Toggle mode — press to start, press again to stop"),
                ("Escape", "Cancel current recording"),
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
        back_btn.clicked.connect(self._shortcuts_back)
        btn_row.addWidget(back_btn)

        next_btn = QPushButton("Next")
        next_btn.setStyleSheet(BUTTON_STYLE)
        next_btn.clicked.connect(lambda: self._stack.setCurrentIndex(self.PAGE_PERMISSIONS))
        btn_row.addWidget(next_btn)

        layout.addLayout(btn_row)
        return page

    def _shortcuts_back(self):
        if self._selected_mode == "cloud":
            self._stack.setCurrentIndex(self.PAGE_API_KEY)
        else:
            self._stack.setCurrentIndex(self.PAGE_LOCAL_SETUP)

    # ── Page 5: Permissions ───────────────────────────────────────

    def _permissions_page(self):
        page, layout = self._make_page()

        title = QLabel("Almost Ready")
        title.setFont(QFont("SF Pro", 22, QFont.Weight.Bold))
        layout.addWidget(title)

        if platform.system() == "Darwin":
            perms_text = (
                "Murmur needs two macOS permissions:\n\n"
                "1. Accessibility — for keyboard shortcuts and pasting text\n"
                "   Go to System Settings > Privacy & Security > Accessibility\n"
                "   and add Murmur (or Terminal if running from terminal)\n\n"
                "2. Microphone — macOS will ask when you first record.\n"
                "   Just click Allow."
            )
        else:
            perms_text = (
                "Murmur needs microphone access to record your voice.\n\n"
                "Windows will ask when you first record. Just click Allow."
            )

        desc = QLabel(perms_text)
        desc.setFont(QFont("SF Pro", 13))
        desc.setStyleSheet(f"color: {TEXT_SECONDARY};")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

        tip = QLabel("Look for the green dot in your menu bar — that's Murmur.\nClick it to open the dashboard.")
        tip.setFont(QFont("SF Pro", 12))
        tip.setStyleSheet(f"color: {ACCENT};")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        layout.addSpacing(8)

        btn_row = QHBoxLayout()
        back_btn = QPushButton("Back")
        back_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(self.PAGE_SHORTCUTS))
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
