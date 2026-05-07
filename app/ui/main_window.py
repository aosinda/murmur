"""Main application window — everything lives here."""

import platform
from collections import defaultdict
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QApplication, QFrame, QStackedWidget,
    QComboBox, QCheckBox, QListWidget, QListWidgetItem,
    QLineEdit, QSizePolicy,
)

from app.ui.theme import Palette, LIGHT


# ── Timestamp helpers ─────────────────────────────────────────────

def _parse_ts(ts: str) -> tuple[str, str]:
    try:
        dt = datetime.fromisoformat(ts)
        date = dt.strftime("%B %-d, %Y").upper()
        time = dt.strftime("%I:%M %p").lstrip("0")
        return date, time
    except Exception:
        return "EARLIER", ts


# ── Shared layout helpers ─────────────────────────────────────────

def _hsep(p: Palette) -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {p.border}; border: none;")
    return f


class SettingRow(QWidget):
    def __init__(self, label: str, desc: str, control: QWidget, p: Palette):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(20)

        # Fixed-width text column. Without this, the column expands to fill the
        # row and Qt/macOS Core Text spreads words to fill the extra space.
        text_col = QWidget()
        text_col.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        text = QVBoxLayout(text_col)
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(1)
        self._lbl = QLabel(label)
        self._lbl.setFont(QFont("", 13, QFont.Weight.Medium))
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        text.addWidget(self._lbl)
        if desc:
            self._desc = QLabel(desc)
            self._desc.setFont(QFont("", 11))
            self._desc.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self._desc.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            self._desc.setWordWrap(False)
            text.addWidget(self._desc)
        else:
            self._desc = None
        text_col.setFixedWidth(text.sizeHint().width())
        layout.addWidget(text_col)
        layout.addStretch()
        layout.addWidget(control, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.apply_theme(p)

    def apply_theme(self, p: Palette):
        self.setStyleSheet("background: transparent; border: none;")
        self._lbl.setStyleSheet(f"color: {p.text}; border: none; background: transparent;")
        if self._desc:
            self._desc.setStyleSheet(f"color: {p.subtext}; border: none; background: transparent;")


def _card(rows: list[QWidget], p: Palette) -> QWidget:
    """Clean rounded card — direct style only, no cascading to children."""
    w = QWidget()
    _apply_card_theme(w, p)
    seps = []
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)
    for i, row in enumerate(rows):
        lay.addWidget(row)
        if i < len(rows) - 1:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background: {p.border}; border: none;")
            seps.append(sep)
            lay.addWidget(sep)
    w._murmur_separators = seps
    return w


def _apply_card_theme(card: QWidget, p: Palette) -> None:
    card.setStyleSheet(
        f"background: {p.surface}; border: 1px solid {p.border}; border-radius: 12px;"
    )
    for sep in getattr(card, "_murmur_separators", []):
        sep.setStyleSheet(f"background: {p.border}; border: none;")


def _make_combo(items: list[tuple[str, str]], width: int = 200) -> QComboBox:
    cb = QComboBox()
    cb.setFixedWidth(width)
    for label, data in items:
        cb.addItem(label, data)
    return cb


def _combo_style(p: Palette) -> str:
    return f"""
        QComboBox {{
            background: {p.bg}; color: {p.text};
            border: 1px solid {p.border}; border-radius: 7px;
            padding: 4px 10px; min-height: 30px;
            font-size: 13px;
        }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox::down-arrow {{ width: 10px; height: 10px; }}
        QComboBox QAbstractItemView {{
            background: {p.surface}; color: {p.text};
            border: 1px solid {p.border};
            selection-background-color: {p.border}; outline: none;
        }}
    """


# ── Sidebar ───────────────────────────────────────────────────────

class NavBtn(QPushButton):
    def __init__(self, label: str, p: Palette):
        super().__init__(label)
        self._p = p
        self._selected = False
        self.setFont(QFont("", 13))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)
        self._style()

    def set_selected(self, v: bool):
        self._selected = v
        self._style()

    def _style(self):
        p = self._p
        bg = p.border if self._selected else "transparent"
        color = p.text if self._selected else p.subtext
        weight = "600" if self._selected else "400"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg}; color: {color}; border: none;
                border-radius: 7px; padding: 0 12px; text-align: left;
                font-weight: {weight}; font-size: 13px;
            }}
            QPushButton:hover {{ background: {p.border}; color: {p.text}; }}
        """)

    def apply_theme(self, p: Palette):
        self._p = p
        self._style()


class Sidebar(QWidget):
    nav_changed = pyqtSignal(int)
    save_requested = pyqtSignal()

    # Page indices
    HOME = 0
    DICTIONARY = 1
    GENERAL = 2
    LANGUAGES = 3
    TRANSCRIPTION = 4
    APPEARANCE = 5

    _NAV_LABELS = ["Home", "Dictionary"]
    _SETTINGS_LABELS = ["General", "Languages", "Transcription", "Appearance"]

    def __init__(self, p: Palette):
        super().__init__()
        self._p = p
        self.setFixedWidth(190)
        self._btns: list[NavBtn] = []
        self._save_btn: QPushButton | None = None
        self._setup()

    def _setup(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 20, 12, 16)
        lay.setSpacing(2)

        self._app_lbl = QLabel("Murmur")
        self._app_lbl.setFont(QFont("", 16, QFont.Weight.Bold))
        self._app_lbl.setContentsMargins(12, 0, 0, 0)
        lay.addWidget(self._app_lbl)
        lay.addSpacing(14)

        for i, label in enumerate(self._NAV_LABELS):
            btn = NavBtn(label, self._p)
            btn.clicked.connect(lambda _, idx=i: self._select(idx))
            self._btns.append(btn)
            lay.addWidget(btn)

        lay.addSpacing(8)
        self._div1 = _hsep(self._p)
        lay.addWidget(self._div1)
        lay.addSpacing(4)

        self._settings_lbl = QLabel("SETTINGS")
        self._settings_lbl.setFont(QFont("", 10, QFont.Weight.Bold))
        self._settings_lbl.setContentsMargins(12, 4, 0, 2)
        lay.addWidget(self._settings_lbl)

        offset = len(self._NAV_LABELS)
        for i, label in enumerate(self._SETTINGS_LABELS):
            btn = NavBtn(label, self._p)
            idx = offset + i
            btn.clicked.connect(lambda _, id=idx: self._select(id))
            self._btns.append(btn)
            lay.addWidget(btn)

        lay.addStretch()

        self._div2 = _hsep(self._p)
        lay.addWidget(self._div2)
        lay.addSpacing(8)

        self._save_btn = QPushButton("Save Settings")
        self._save_btn.setFixedHeight(36)
        self._save_btn.setFont(QFont("", 13, QFont.Weight.Medium))
        self._save_btn.clicked.connect(self.save_requested.emit)
        self._save_btn.setVisible(False)
        lay.addWidget(self._save_btn)

        self._select(0)
        self._apply_palette()

    def _select(self, idx: int):
        for i, btn in enumerate(self._btns):
            btn.set_selected(i == idx)
        # Show Save only on settings pages
        if self._save_btn:
            self._save_btn.setVisible(idx >= len(self._NAV_LABELS))
        self.nav_changed.emit(idx)

    def _apply_palette(self):
        p = self._p
        self.setStyleSheet(f"background: {p.sidebar}; border: none;")
        self._app_lbl.setStyleSheet(f"color: {p.text};")
        self._settings_lbl.setStyleSheet(f"color: {p.subtext}; letter-spacing: 1px;")
        self._div1.setStyleSheet(f"background: {p.border};")
        self._div2.setStyleSheet(f"background: {p.border};")
        if self._save_btn:
            self._save_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {p.accent}; color: #000;
                    border: none; border-radius: 8px; font-weight: 600;
                }}
                QPushButton:hover {{ background: {p.accent}; opacity: 0.85; }}
            """)
        for btn in self._btns:
            btn.apply_theme(p)

    def apply_theme(self, p: Palette):
        self._p = p
        self._apply_palette()


# ── Home page ─────────────────────────────────────────────────────

class HomePage(QWidget):
    def __init__(self, p: Palette):
        super().__init__()
        self._p = p
        self._setup()

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        lay = QVBoxLayout(self._content)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(0)

        # Greeting
        self._greeting = QLabel("Good afternoon")
        self._greeting.setFont(QFont("", 26, QFont.Weight.Bold))
        lay.addWidget(self._greeting)
        lay.addSpacing(12)

        # Stats row
        self._stats_row = QHBoxLayout()
        self._stats_row.setContentsMargins(0, 0, 0, 0)
        self._stats_row.setSpacing(0)
        self._stat_labels: list[tuple[QLabel, QLabel]] = []
        self._stat_keys = [
            ("0", "sessions"),
            ("0", "words"),
            ("0", "avg WPM"),
            ("0h", "total"),
            ("0 min", "/day avg"),
        ]
        for val, label in self._stat_keys:
            val_lbl = QLabel(val)
            val_lbl.setFont(QFont("", 13, QFont.Weight.Bold))
            label_lbl = QLabel(label)
            label_lbl.setFont(QFont("", 12))
            self._stat_labels.append((val_lbl, label_lbl))
            self._stats_row.addWidget(val_lbl)
            self._stats_row.addSpacing(4)
            self._stats_row.addWidget(label_lbl)
            self._stats_row.addSpacing(20)
        self._stats_row.addStretch()
        lay.addLayout(self._stats_row)

        lay.addSpacing(28)
        self._hist_div = _hsep(self._p)
        lay.addWidget(self._hist_div)
        lay.addSpacing(4)

        # History
        self._hist_layout = QVBoxLayout()
        self._hist_layout.setSpacing(0)
        self._hist_layout.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self._hist_layout)

        self._empty_lbl = QLabel("Hold Fn and start talking.")
        self._empty_lbl.setFont(QFont("", 13))
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setContentsMargins(0, 40, 0, 0)
        lay.addWidget(self._empty_lbl)

        lay.addStretch()

        self._scroll.setWidget(self._content)
        outer.addWidget(self._scroll)

        self._apply_palette()

    def _apply_palette(self):
        p = self._p
        self.setStyleSheet(f"background: {p.bg};")
        self._content.setStyleSheet(f"background: {p.bg};")
        self._greeting.setStyleSheet(f"color: {p.text};")
        self._empty_lbl.setStyleSheet(f"color: {p.subtext};")
        self._hist_div.setStyleSheet(f"background: {p.border};")
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ background: {p.bg}; border: none; }}
            QScrollBar:vertical {{ background: {p.bg}; width: 6px; border: none; }}
            QScrollBar::handle:vertical {{ background: {p.border}; border-radius: 3px; min-height: 20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        for val_lbl, label_lbl in self._stat_labels:
            val_lbl.setStyleSheet(f"color: {p.text};")
            label_lbl.setStyleSheet(f"color: {p.subtext};")

    def apply_theme(self, p: Palette):
        self._p = p
        self._apply_palette()

    def update_stats(self, stats: dict):
        hour = datetime.now().hour
        self._greeting.setText(
            "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        )
        if not stats:
            return

        sessions = stats.get("total_sessions", 0)
        words = stats.get("total_words", 0)
        wpm = stats.get("avg_wpm", 0)
        total_h = stats.get("total_hours", 0)
        avg_daily = stats.get("avg_daily_minutes", 0)

        words_str = f"{words / 1_000_000:.1f}M" if words >= 1_000_000 \
            else f"{words / 1_000:.1f}K" if words >= 1_000 else str(words)

        total_str = f"{total_h:.1f}h" if total_h >= 1 else f"{round(total_h * 60)}m"
        daily_str = f"{avg_daily:.0f} min" if avg_daily >= 1 else f"{round(avg_daily * 60)}s"

        values = [str(sessions), words_str, str(wpm), total_str, daily_str]
        for (val_lbl, _), val in zip(self._stat_labels, values):
            val_lbl.setText(val)

    def populate_history(self, dictations: list[dict]):
        # Clear
        while self._hist_layout.count():
            item = self._hist_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        p = self._p
        self._empty_lbl.setVisible(not dictations)
        if not dictations:
            return

        groups: dict[str, list] = defaultdict(list)
        for d in dictations:
            date_str, time_str = _parse_ts(d.get("timestamp", ""))
            groups[date_str].append((time_str, d))

        for gi, (date_str, items) in enumerate(groups.items()):
            date_lbl = QLabel(date_str)
            date_lbl.setFont(QFont("", 10, QFont.Weight.Bold))
            date_lbl.setStyleSheet(f"color: {p.subtext}; letter-spacing: 1px; background: transparent;")
            date_lbl.setContentsMargins(0, 20 if gi > 0 else 4, 0, 8)
            self._hist_layout.addWidget(date_lbl)

            for time_str, d in items:
                row = self._make_row(time_str, d["cleaned_text"])
                self._hist_layout.addWidget(row)
                self._hist_layout.addWidget(_hsep(p))

    def _make_row(self, time_str: str, text: str) -> QWidget:
        p = self._p
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 10, 0, 10)
        lay.setSpacing(18)

        t = QLabel(time_str)
        t.setFont(QFont("Menlo", 11))
        t.setStyleSheet(f"color: {p.subtext};")
        t.setFixedWidth(70)
        t.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(t)

        tx = QLabel(text[:220] + ("…" if len(text) > 220 else ""))
        tx.setFont(QFont("", 13))
        tx.setStyleSheet(f"color: {p.text};")
        tx.setWordWrap(True)
        lay.addWidget(tx, stretch=1)

        cp = QPushButton("Copy")
        cp.setFixedSize(52, 26)
        cp.setFont(QFont("", 11))
        cp.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {p.subtext};
                border: 1px solid {p.border}; border-radius: 5px; }}
            QPushButton:hover {{ color: {p.text}; border-color: {p.text}; }}
        """)
        cp.clicked.connect(lambda: QApplication.clipboard().setText(text))
        lay.addWidget(cp, alignment=Qt.AlignmentFlag.AlignVCenter)
        return row


# ── Dictionary page ───────────────────────────────────────────────

class DictionaryPage(QWidget):
    def __init__(self, p: Palette):
        super().__init__()
        self._p = p
        self._formatter = None
        self._setup()

    def _setup(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(0)

        self._title = QLabel("Dictionary")
        self._title.setFont(QFont("", 26, QFont.Weight.Bold))
        lay.addWidget(self._title)
        lay.addSpacing(6)

        self._subtitle = QLabel("Words you say on the left → what gets typed on the right.")
        self._subtitle.setFont(QFont("", 12))
        lay.addWidget(self._subtitle)
        lay.addSpacing(20)

        # Add row
        add_row = QHBoxLayout()
        add_row.setSpacing(10)
        self._spoken_input = QLineEdit()
        self._spoken_input.setPlaceholderText("You say…")
        self._spoken_input.setFixedHeight(36)
        add_row.addWidget(self._spoken_input)

        arrow = QLabel("→")
        arrow.setFont(QFont("", 15))
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_row.addWidget(arrow)
        self._arrow = arrow

        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText("Output as…")
        self._replace_input.setFixedHeight(36)
        add_row.addWidget(self._replace_input)

        self._add_btn = QPushButton("Add")
        self._add_btn.setFixedSize(64, 36)
        self._add_btn.setFont(QFont("", 13, QFont.Weight.Medium))
        self._add_btn.clicked.connect(self._add_entry)
        add_row.addWidget(self._add_btn)

        lay.addLayout(add_row)
        lay.addSpacing(16)

        # Entries scroll
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._entries_widget = QWidget()
        self._entries_layout = QVBoxLayout(self._entries_widget)
        self._entries_layout.setContentsMargins(0, 0, 0, 0)
        self._entries_layout.setSpacing(0)
        self._entries_layout.addStretch()

        self._scroll.setWidget(self._entries_widget)
        lay.addWidget(self._scroll)

        self._apply_palette()

    def set_formatter(self, formatter):
        self._formatter = formatter
        self._load()

    def _apply_palette(self):
        p = self._p
        self.setStyleSheet(f"background: {p.bg};")
        self._title.setStyleSheet(f"color: {p.text};")
        self._subtitle.setStyleSheet(f"color: {p.subtext};")
        self._arrow.setStyleSheet(f"color: {p.subtext};")

        input_style = f"""
            QLineEdit {{
                background: {p.surface}; color: {p.text};
                border: 1px solid {p.border}; border-radius: 8px;
                padding: 0 10px; font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {p.accent}; }}
        """
        self._spoken_input.setStyleSheet(input_style)
        self._replace_input.setStyleSheet(input_style)

        self._add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {p.accent}; color: #000;
                border: none; border-radius: 8px; font-weight: 600;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ background: {p.bg}; border: none; }}
            QScrollBar:vertical {{ background: {p.bg}; width: 6px; border: none; }}
            QScrollBar::handle:vertical {{ background: {p.border}; border-radius: 3px; min-height: 20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self._entries_widget.setStyleSheet(f"background: {p.bg};")

    def apply_theme(self, p: Palette):
        self._p = p
        self._apply_palette()
        self._load()

    def _add_entry(self):
        spoken = self._spoken_input.text().strip()
        replacement = self._replace_input.text().strip()
        if not spoken or not replacement or not self._formatter:
            return
        self._formatter.add_word(spoken, replacement)
        self._spoken_input.clear()
        self._replace_input.clear()
        self._load()

    def _load(self):
        while self._entries_layout.count() > 1:
            item = self._entries_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = self._formatter.get_dictionary() if self._formatter else {}
        p = self._p
        rows = []
        for spoken, replacement in entries.items():
            rows.append(self._make_entry_row(spoken, replacement))

        if rows:
            card = _card(rows, p)
            self._entries_layout.insertWidget(0, card)

    def _make_entry_row(self, spoken: str, replacement: str) -> QWidget:
        p = self._p
        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(20, 12, 16, 12)
        lay.setSpacing(10)

        s = QLabel(spoken)
        s.setFont(QFont("", 13))
        s.setStyleSheet(f"color: {p.text};")
        lay.addWidget(s)

        arrow = QLabel("→")
        arrow.setFont(QFont("", 13))
        arrow.setStyleSheet(f"color: {p.subtext};")
        lay.addWidget(arrow)

        r = QLabel(replacement)
        r.setFont(QFont("", 13, QFont.Weight.Medium))
        r.setStyleSheet(f"color: {p.text};")
        lay.addWidget(r, stretch=1)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setFont(QFont("", 11))
        del_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {p.subtext};
                border: none; border-radius: 6px; }}
            QPushButton:hover {{ color: {p.danger}; background: rgba(220,50,50,0.1); }}
        """)
        del_btn.clicked.connect(lambda _, s=spoken: self._remove(s))
        lay.addWidget(del_btn)
        return row

    def _remove(self, spoken: str):
        if self._formatter:
            self._formatter.remove_word(spoken)
        self._load()


# ── Settings pages ────────────────────────────────────────────────

class GeneralPage(QWidget):
    def __init__(self, db, p: Palette):
        super().__init__()
        self._db = db
        self._p = p
        self._rows: list[SettingRow] = []
        self._setup()

    def _setup(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(28)

        self._title = QLabel("General")
        self._title.setFont(QFont("", 26, QFont.Weight.Bold))
        lay.addWidget(self._title)

        from app.audio.devices import DeviceManager
        self._mic_combo = QComboBox()
        self._mic_combo.setFixedWidth(240)
        self._refresh_devices()

        self._vibe_cb = QCheckBox()
        self._vibe_cb.setFixedSize(22, 22)

        self._retention_combo = _make_combo([
            ("24 hours (default)", "24h"),
            ("7 days", "7d"),
            ("30 days", "30d"),
            ("Keep forever", "forever"),
        ])

        mic_row = SettingRow("Microphone", "Input device for recording", self._mic_combo, self._p)
        retain_row = SettingRow("Keep history", "How long transcriptions are stored", self._retention_combo, self._p)
        vibe_row = SettingRow("Vibe Coding", "Optimizes output for code dictation", self._vibe_cb, self._p)
        self._rows = [mic_row, retain_row, vibe_row]

        self._card = _card(self._rows, self._p)
        lay.addWidget(self._card)
        lay.addStretch()
        self._load()
        self._apply_palette()

    def refresh_devices(self):
        """Re-scan audio devices — called automatically when page is shown."""
        from app.audio.devices import DeviceManager
        current = self._mic_combo.currentData()
        self._mic_combo.clear()
        for dev in DeviceManager.list_input_devices():
            self._mic_combo.addItem(dev["name"] + (" (Default)" if dev["is_default"] else ""), dev["id"])
        if current is not None:
            idx = self._mic_combo.findData(current)
            if idx >= 0:
                self._mic_combo.setCurrentIndex(idx)

    def _refresh_devices(self):
        self.refresh_devices()

    def _load(self):
        if not self._db:
            return
        saved_mic = self._db.get_setting("mic_device_id", "")
        if saved_mic:
            try:
                idx = self._mic_combo.findData(int(saved_mic))
                if idx >= 0:
                    self._mic_combo.setCurrentIndex(idx)
            except (ValueError, TypeError):
                pass
        self._vibe_cb.setChecked(self._db.get_setting("vibe_coding", "False").lower() == "true")
        idx = self._retention_combo.findData(self._db.get_setting("history_retention", "24h"))
        if idx >= 0:
            self._retention_combo.setCurrentIndex(idx)

    def get_values(self) -> dict:
        return {
            "mic_device_id": str(self._mic_combo.currentData() or ""),
            "vibe_coding": str(self._vibe_cb.isChecked()),
            "history_retention": self._retention_combo.currentData(),
        }

    def _apply_palette(self):
        p = self._p
        self.setStyleSheet(f"background: {p.bg};")
        self._title.setStyleSheet(f"color: {p.text};")
        _apply_card_theme(self._card, p)
        cs = _combo_style(p)
        self._mic_combo.setStyleSheet(cs)
        self._retention_combo.setStyleSheet(cs)
        for row in self._rows:
            row.apply_theme(p)

    def apply_theme(self, p: Palette):
        self._p = p
        self._apply_palette()


SUPPORTED_LANGUAGES = sorted([
    "Afrikaans", "Arabic", "Armenian", "Azerbaijani", "Belarusian",
    "Bosnian", "Bulgarian", "Catalan", "Chinese", "Croatian", "Czech",
    "Danish", "Dutch", "English", "Estonian", "Finnish", "French",
    "Galician", "German", "Greek", "Hebrew", "Hindi", "Hungarian",
    "Icelandic", "Indonesian", "Italian", "Japanese", "Kannada",
    "Kazakh", "Korean", "Latvian", "Lithuanian", "Macedonian", "Malay",
    "Maltese", "Maori", "Marathi", "Nepali", "Norwegian", "Persian",
    "Polish", "Portuguese", "Romanian", "Russian", "Serbian", "Slovak",
    "Slovenian", "Spanish", "Swahili", "Swedish", "Tagalog", "Tamil",
    "Thai", "Turkish", "Ukrainian", "Urdu", "Vietnamese", "Welsh",
])


class LanguagesPage(QWidget):
    def __init__(self, db, p: Palette):
        super().__init__()
        self._db = db
        self._p = p
        self._setup()

    def _setup(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(12)

        self._title = QLabel("Languages")
        self._title.setFont(QFont("", 26, QFont.Weight.Bold))
        lay.addWidget(self._title)

        self._desc = QLabel("Murmur auto-detects between your selected languages.")
        self._desc.setFont(QFont("", 12))
        lay.addWidget(self._desc)

        self._lang_list = QListWidget()
        self._lang_list.setMaximumHeight(320)
        for lang in SUPPORTED_LANGUAGES:
            item = QListWidgetItem(lang)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if lang in ("English", "Bosnian", "Danish")
                else Qt.CheckState.Unchecked
            )
            self._lang_list.addItem(item)
        lay.addWidget(self._lang_list)
        lay.addStretch()
        self._load()
        self._apply_palette()

    def _load(self):
        if not self._db:
            return
        saved = [l.strip() for l in self._db.get_setting("languages", "English,Bosnian,Danish").split(",")]
        for i in range(self._lang_list.count()):
            item = self._lang_list.item(i)
            item.setCheckState(Qt.CheckState.Checked if item.text() in saved else Qt.CheckState.Unchecked)

    def get_values(self) -> dict:
        langs = [
            self._lang_list.item(i).text()
            for i in range(self._lang_list.count())
            if self._lang_list.item(i).checkState() == Qt.CheckState.Checked
        ]
        return {"languages": ",".join(langs)}

    def _apply_palette(self):
        p = self._p
        self.setStyleSheet(f"background: {p.bg};")
        self._title.setStyleSheet(f"color: {p.text};")
        self._desc.setStyleSheet(f"color: {p.subtext};")
        self._lang_list.setStyleSheet(f"""
            QListWidget {{
                background: {p.surface}; border: 1px solid {p.border};
                border-radius: 10px; padding: 4px; color: {p.text};
            }}
            QListWidget::item {{ padding: 4px 6px; border-radius: 5px; color: {p.text}; }}
            QListWidget::item:hover {{ background: {p.border}; }}
        """)

    def apply_theme(self, p: Palette):
        self._p = p
        self._apply_palette()


class TranscriptionPage(QWidget):
    def __init__(self, db, p: Palette):
        super().__init__()
        self._db = db
        self._p = p
        self._rows: list[SettingRow] = []
        self._setup()

    def _setup(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(28)

        self._title = QLabel("Transcription")
        self._title.setFont(QFont("", 26, QFont.Weight.Bold))
        lay.addWidget(self._title)

        self._engine_combo = _make_combo([
            ("Cloud (OpenAI)", "cloud"),
            ("Local (on-device)", "local"),
        ])
        self._model_combo = _make_combo([
            ("Tiny — ~75 MB", "tiny"),
            ("Base — ~145 MB", "base"),
            ("Small — ~244 MB", "small"),
            ("Medium — ~769 MB", "medium"),
            ("Large — ~1.5 GB", "large-v3"),
        ])

        self._engine_row = SettingRow("Engine", "Cloud uses OpenAI; Local runs on-device", self._engine_combo, self._p)
        self._model_row = SettingRow("Local Model", "Larger = more accurate, slower to load", self._model_combo, self._p)
        self._rows = [self._engine_row, self._model_row]

        self._engine_combo.currentIndexChanged.connect(
            lambda: self._model_row.setVisible(self._engine_combo.currentData() == "local")
        )

        self._card = _card(self._rows, self._p)
        lay.addWidget(self._card)
        lay.addStretch()
        self._load()
        self._apply_palette()

    def _load(self):
        if not self._db:
            return
        def _set(cb, key, default):
            idx = cb.findData(self._db.get_setting(key, default))
            if idx >= 0:
                cb.setCurrentIndex(idx)
        _set(self._engine_combo, "transcription_mode", "cloud")
        _set(self._model_combo, "local_model_size", "small")
        self._model_row.setVisible(self._engine_combo.currentData() == "local")

    def get_values(self) -> dict:
        return {
            "transcription_mode": self._engine_combo.currentData(),
            "local_model_size": self._model_combo.currentData(),
        }

    def _apply_palette(self):
        p = self._p
        self.setStyleSheet(f"background: {p.bg};")
        self._title.setStyleSheet(f"color: {p.text};")
        _apply_card_theme(self._card, p)
        cs = _combo_style(p)
        self._engine_combo.setStyleSheet(cs)
        self._model_combo.setStyleSheet(cs)
        for row in self._rows:
            row.apply_theme(p)

    def apply_theme(self, p: Palette):
        self._p = p
        self._apply_palette()


class AppearancePage(QWidget):
    theme_changed = pyqtSignal(str)

    def __init__(self, db, p: Palette):
        super().__init__()
        self._db = db
        self._p = p
        self._rows: list[SettingRow] = []
        self._setup()

    def _setup(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 32)
        lay.setSpacing(28)

        self._title = QLabel("Appearance")
        self._title.setFont(QFont("", 26, QFont.Weight.Bold))
        lay.addWidget(self._title)

        self._theme_combo = _make_combo([("Light", "light"), ("Dark", "dark")])
        row = SettingRow("Theme", "Choose light or dark mode", self._theme_combo, self._p)
        self._rows = [row]
        self._card = _card([row], self._p)
        lay.addWidget(self._card)
        lay.addStretch()
        self._load()
        self._apply_palette()
        self._theme_combo.currentIndexChanged.connect(self._emit_theme_changed)

    def _load(self):
        if not self._db:
            return
        idx = self._theme_combo.findData(self._db.get_setting("theme", "light"))
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)

    def get_values(self) -> dict:
        return {"theme": self._theme_combo.currentData()}

    def _emit_theme_changed(self):
        theme = self._theme_combo.currentData()
        if theme:
            self.theme_changed.emit(theme)

    def _apply_palette(self):
        p = self._p
        self.setStyleSheet(f"background: {p.bg};")
        self._title.setStyleSheet(f"color: {p.text};")
        _apply_card_theme(self._card, p)
        self._theme_combo.setStyleSheet(_combo_style(p))
        for row in self._rows:
            row.apply_theme(p)

    def apply_theme(self, p: Palette):
        self._p = p
        self._apply_palette()


# ── Main window ───────────────────────────────────────────────────

class MainWindow(QWidget):

    settings_changed = pyqtSignal(dict)

    def __init__(self, db, palette: Palette = LIGHT):
        super().__init__()
        self._db = db
        self._palette = palette
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        self.setWindowTitle("Murmur")
        self.setMinimumSize(720, 520)

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = Sidebar(self._palette)
        self._sidebar.nav_changed.connect(self._on_nav)
        self._sidebar.save_requested.connect(self._save_settings)
        root.addWidget(self._sidebar)

        self._vdiv = QFrame()
        self._vdiv.setFrameShape(QFrame.Shape.VLine)
        self._vdiv.setFixedWidth(1)
        root.addWidget(self._vdiv)

        # Content wrapper: status bar + stack
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)
        self._wrap = wrap

        self._status_bar = QWidget()
        self._status_bar.setFixedHeight(36)
        sl = QHBoxLayout(self._status_bar)
        sl.setContentsMargins(20, 0, 20, 0)
        self._status_dot = QLabel("●")
        self._status_dot.setFont(QFont("", 8))
        sl.addWidget(self._status_dot)
        self._status_label = QLabel("Ready")
        self._status_label.setFont(QFont("", 12))
        sl.addWidget(self._status_label)
        sl.addStretch()
        hint = "Fn = talk  ·  Fn+Space = toggle" if platform.system() == "Darwin" \
            else "Ctrl+Shift = talk  ·  Ctrl+Shift+Space = toggle"
        self._hint = QLabel(hint)
        self._hint.setFont(QFont("", 11))
        self._hint.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._hint.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sl.addWidget(self._hint)

        self._status_div = QFrame()
        self._status_div.setFrameShape(QFrame.Shape.HLine)
        self._status_div.setFixedHeight(1)

        wl.addWidget(self._status_bar)
        wl.addWidget(self._status_div)

        self._stack = QStackedWidget()
        self._home_page = HomePage(self._palette)
        self._dict_page = DictionaryPage(self._palette)
        self._general_page = GeneralPage(self._db, self._palette)
        self._lang_page = LanguagesPage(self._db, self._palette)
        self._trans_page = TranscriptionPage(self._db, self._palette)
        self._appear_page = AppearancePage(self._db, self._palette)
        self._appear_page.theme_changed.connect(self._change_theme)

        for page in [self._home_page, self._dict_page, self._general_page,
                     self._lang_page, self._trans_page, self._appear_page]:
            self._stack.addWidget(page)

        wl.addWidget(self._stack)
        root.addWidget(wrap, stretch=1)

        self._apply_palette()

    def _on_nav(self, idx: int):
        self._stack.setCurrentIndex(idx)
        if idx == Sidebar.GENERAL:
            self._general_page.refresh_devices()

    def _apply_palette(self):
        p = self._palette
        self.setStyleSheet(f"background: {p.bg};")
        self._vdiv.setStyleSheet(f"background: {p.border};")
        self._wrap.setStyleSheet(f"background: {p.bg};")
        self._stack.setStyleSheet(f"background: {p.bg};")
        self._status_bar.setStyleSheet(f"background: {p.bg}; border: none;")
        self._status_dot.setStyleSheet(f"color: {p.accent};")
        self._status_label.setStyleSheet(f"color: {p.subtext};")
        self._hint.setStyleSheet(f"color: {p.subtext};")
        self._status_div.setStyleSheet(f"background: {p.border};")

    def _save_settings(self):
        settings = {}
        settings.update(self._general_page.get_values())
        settings.update(self._lang_page.get_values())
        settings.update(self._trans_page.get_values())
        settings.update(self._appear_page.get_values())

        if self._db:
            for k, v in settings.items():
                self._db.set_setting(k, v)

        self.settings_changed.emit(settings)

    def _change_theme(self, theme: str):
        if self._db:
            self._db.set_setting("theme", theme)
        self.settings_changed.emit({"theme": theme})

    # ── Public API ────────────────────────────────────────────────

    def set_formatter(self, formatter):
        self._dict_page.set_formatter(formatter)

    def apply_theme(self, palette: Palette):
        self._palette = palette
        self._sidebar.apply_theme(palette)
        self._home_page.apply_theme(palette)
        self._dict_page.apply_theme(palette)
        self._general_page.apply_theme(palette)
        self._lang_page.apply_theme(palette)
        self._trans_page.apply_theme(palette)
        self._appear_page.apply_theme(palette)
        self._apply_palette()
        self.refresh()

    def refresh(self):
        stats = self._db.get_stats()
        self._home_page.update_stats(stats or {})
        dictations = self._db.get_recent_dictations(limit=50)
        self._home_page.populate_history(dictations or [])

    def set_status(self, status: str):
        p = self._palette
        if status == "recording":
            self._status_dot.setStyleSheet(f"color: {p.danger};")
            self._status_label.setText("Recording…")
        elif status == "processing":
            self._status_dot.setStyleSheet(f"color: {p.warning};")
            self._status_label.setText("Processing…")
        else:
            self._status_dot.setStyleSheet(f"color: {p.accent};")
            self._status_label.setText("Ready")

    def show_settings(self):
        """Navigate to General settings page."""
        self._sidebar._select(Sidebar.GENERAL)
