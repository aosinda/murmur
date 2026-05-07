"""Settings window — mic, languages, modes."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QCheckBox, QGroupBox, QListWidget, QListWidgetItem,
)

from app.audio.devices import DeviceManager


class SettingsWindow(QWidget):
    """Settings panel for Murmur configuration."""

    settings_changed = pyqtSignal(dict)

    SUPPORTED_LANGUAGES = [
        "English", "Bosnian", "Danish", "German", "French", "Spanish",
        "Italian", "Portuguese", "Dutch", "Swedish", "Norwegian",
        "Finnish", "Polish", "Turkish", "Russian", "Arabic",
        "Chinese", "Japanese", "Korean", "Hindi", "Croatian", "Serbian",
    ]

    def __init__(self, db=None):
        super().__init__()
        self._db = db
        self._setup_window()
        self._setup_ui()
        self._load_settings()

    def _setup_window(self) -> None:
        self.setWindowTitle("Murmur — Settings")
        self.setFixedSize(450, 610)
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
        )

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Settings")
        title.setFont(QFont("SF Pro", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # ── Microphone ──
        mic_group = QGroupBox("Microphone")
        mic_layout = QVBoxLayout(mic_group)

        self._mic_combo = QComboBox()
        self._refresh_devices()
        mic_layout.addWidget(self._mic_combo)

        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self._refresh_devices)
        mic_layout.addWidget(refresh_btn)

        layout.addWidget(mic_group)

        # ── Languages ──
        lang_group = QGroupBox("Languages (auto-detect between selected)")
        lang_layout = QVBoxLayout(lang_group)

        self._lang_list = QListWidget()
        self._lang_list.setMaximumHeight(150)
        for lang in self.SUPPORTED_LANGUAGES:
            item = QListWidgetItem(lang)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            # Default: check English, Bosnian, Danish
            if lang in ("English", "Bosnian", "Danish"):
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self._lang_list.addItem(item)

        lang_layout.addWidget(self._lang_list)
        layout.addWidget(lang_group)

        # ── Transcription Engine ──
        engine_group = QGroupBox("Transcription Engine")
        engine_layout = QVBoxLayout(engine_group)

        engine_row = QHBoxLayout()
        engine_row.addWidget(QLabel("Mode:"))
        self._engine_combo = QComboBox()
        self._engine_combo.addItem("Cloud (OpenAI)", "cloud")
        self._engine_combo.addItem("Local (on-device)", "local")
        engine_row.addWidget(self._engine_combo)
        engine_layout.addLayout(engine_row)

        self._model_row = QHBoxLayout()
        self._model_row.addWidget(QLabel("Model:"))
        self._model_combo = QComboBox()
        self._model_combo.addItem("Tiny  — fastest, ~75 MB", "tiny")
        self._model_combo.addItem("Base  — fast, ~145 MB", "base")
        self._model_combo.addItem("Small — recommended, ~244 MB", "small")
        self._model_combo.addItem("Medium — accurate, ~769 MB", "medium")
        self._model_combo.addItem("Large — most accurate, ~1.5 GB", "large-v3")
        self._model_row.addWidget(self._model_combo)
        engine_layout.addLayout(self._model_row)

        engine_note = QLabel("Local runs fully on-device — no API key needed.")
        engine_note.setStyleSheet("color: #888; font-size: 11px;")
        engine_layout.addWidget(engine_note)

        layout.addWidget(engine_group)

        self._engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        self._on_engine_changed()

        # ── Mode ──
        mode_group = QGroupBox("Dictation Mode")
        mode_layout = QVBoxLayout(mode_group)

        self._vibe_coding_cb = QCheckBox("Vibe Coding Mode")
        self._vibe_coding_cb.setToolTip(
            "Optimizes output for code-related dictation"
        )
        mode_layout.addWidget(self._vibe_coding_cb)

        layout.addWidget(mode_group)

        # ── Save ──
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

    def _on_engine_changed(self) -> None:
        is_local = self._engine_combo.currentData() == "local"
        for i in range(self._model_row.count()):
            item = self._model_row.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(is_local)

    def _refresh_devices(self) -> None:
        """Reload available audio input devices."""
        self._mic_combo.clear()
        devices = DeviceManager.list_input_devices()
        for dev in devices:
            label = dev["name"]
            if dev["is_default"]:
                label += " (Default)"
            self._mic_combo.addItem(label, dev["id"])

    def get_selected_languages(self) -> list[str]:
        """Return list of checked language names."""
        langs = []
        for i in range(self._lang_list.count()):
            item = self._lang_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                langs.append(item.text())
        return langs

    def get_selected_mic_id(self) -> int | None:
        """Return selected device ID."""
        return self._mic_combo.currentData()

    def is_vibe_coding(self) -> bool:
        return self._vibe_coding_cb.isChecked()

    def _save_settings(self) -> None:
        """Save current settings."""
        settings = {
            "mic_device_id": str(self.get_selected_mic_id() or ""),
            "languages": ",".join(self.get_selected_languages()),
            "vibe_coding": str(self.is_vibe_coding()),
            "transcription_mode": self._engine_combo.currentData(),
            "local_model_size": self._model_combo.currentData(),
        }

        if self._db:
            for key, value in settings.items():
                self._db.set_setting(key, value)

        self.settings_changed.emit(settings)

    def _load_settings(self) -> None:
        """Load settings from database."""
        if not self._db:
            return

        # Load languages
        saved_langs = self._db.get_setting("languages", "English,Bosnian,Danish")
        lang_list = [l.strip() for l in saved_langs.split(",")]
        for i in range(self._lang_list.count()):
            item = self._lang_list.item(i)
            if item.text() in lang_list:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

        # Load transcription engine
        mode = self._db.get_setting("transcription_mode", "cloud")
        idx = self._engine_combo.findData(mode)
        if idx >= 0:
            self._engine_combo.setCurrentIndex(idx)

        # Load local model size
        model_size = self._db.get_setting("local_model_size", "small")
        idx = self._model_combo.findData(model_size)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)

        # Load vibe coding
        vibe = self._db.get_setting("vibe_coding", "False")
        self._vibe_coding_cb.setChecked(vibe.lower() == "true")

        # Load mic (best effort — device IDs can change)
        saved_mic = self._db.get_setting("mic_device_id", "")
        if saved_mic:
            idx = self._mic_combo.findData(int(saved_mic))
            if idx >= 0:
                self._mic_combo.setCurrentIndex(idx)
