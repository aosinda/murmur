"""Murmur — Private voice dictation tool.

Entry point that wires all modules together.
"""

import os
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from app.audio.recorder import AudioRecorder
from app.hotkeys.listener import HotkeyListener
from app.output.injector import TextInjector
from app.storage.db import MurmurDB
from app.ui.bar import DictationBar
from app.ui.onboarding import OnboardingWindow
from app.ui.main_window import MainWindow
from app.ui.settings import SettingsWindow
from app.ui.dictionary import DictionaryEditor


# Load .env — check multiple locations
_config_dir = Path.home() / ".murmur"
_config_dir.mkdir(exist_ok=True)

# Priority: ~/.murmur/.env → project root .env
load_dotenv(_config_dir / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")


class PipelineSignals(QObject):
    """Qt signals for cross-thread communication."""
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(bytes, float)  # audio_bytes, duration
    recording_cancelled = pyqtSignal()
    processing_done = pyqtSignal(str)  # cleaned text
    error_occurred = pyqtSignal(str)


class Murmur:
    """Main application controller."""

    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("Murmur")
        self._app.setQuitOnLastWindowClosed(False)

        self._db = MurmurDB()
        self._signals = PipelineSignals()

        # Check if onboarding is needed
        if self._db.get_setting("onboarding_complete") != "true":
            self._onboarding = OnboardingWindow(
                db=self._db, on_complete=self._start_app
            )
            self._onboarding.show()
        else:
            self._start_app()

    def _start_app(self):
        """Initialize all modules and start the app."""
        mode = self._db.get_setting("transcription_mode", "cloud")

        self._recorder = AudioRecorder()
        self._injector = TextInjector()

        if mode == "local":
            from app.transcription.whisper_local import LocalWhisperClient
            from app.cleanup.formatter_local import LocalTextFormatter
            self._whisper = LocalWhisperClient()
            self._formatter = LocalTextFormatter()
        else:
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                load_dotenv(_config_dir / ".env", override=True)
                api_key = os.environ.get("OPENAI_API_KEY", "")

            if not api_key:
                print("ERROR: OPENAI_API_KEY not set.")
                sys.exit(1)

            from app.transcription.whisper_client import WhisperClient
            from app.cleanup.formatter import TextFormatter
            self._whisper = WhisperClient(api_key=api_key)
            self._formatter = TextFormatter(api_key=api_key)

        # Load saved mic device
        saved_mic = self._db.get_setting("mic_device_id")
        if saved_mic:
            try:
                self._recorder.set_device(int(saved_mic))
            except (ValueError, TypeError):
                pass

        # ── UI ──
        self._bar = DictationBar()
        self._main_window = MainWindow(db=self._db)
        self._settings_window = SettingsWindow(db=self._db)
        self._dictionary_window = DictionaryEditor(formatter=self._formatter)

        # ── System tray ──
        self._setup_tray()

        # ── Connect signals ──
        self._connect_signals()

        # ── Start hotkey listener ──
        self._hotkeys = HotkeyListener(
            on_start=self._on_hotkey_start,
            on_stop=self._on_hotkey_stop,
            on_cancel=self._on_hotkey_cancel,
            on_reinsert=self._on_reinsert,
        )
        self._hotkeys.start()

        # ── Purge old dictations on startup ──
        self._db._purge_old()

    def _setup_tray(self) -> None:
        """Create system tray icon and menu."""
        self._tray = QSystemTrayIcon(self._app)
        self._tray.setToolTip("Murmur — Voice Dictation")

        from PyQt6.QtGui import QPixmap, QPainter, QColor
        pixmap = QPixmap(22, 22)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(100, 200, 130))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(3, 3, 16, 16)
        painter.end()
        self._tray.setIcon(QIcon(pixmap))

        menu = QMenu()

        open_action = QAction("Open Murmur", menu)
        open_action.triggered.connect(self._show_main)
        menu.addAction(open_action)

        menu.addSeparator()

        dict_action = QAction("Dictionary", menu)
        dict_action.triggered.connect(self._show_dictionary)
        menu.addAction(dict_action)

        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("Quit Murmur", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_click)
        self._tray.show()

    def _on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_main()

    def _connect_signals(self) -> None:
        """Wire up cross-thread signals to UI updates."""
        self._signals.recording_started.connect(self._on_recording_started)
        self._signals.recording_cancelled.connect(self._on_recording_cancelled)
        self._signals.recording_stopped.connect(self._process_audio)
        self._signals.processing_done.connect(self._deliver_text)
        self._signals.error_occurred.connect(self._on_error)

        # Bar button signals
        self._bar.cancel_clicked.connect(self._cancel_recording)
        self._bar.stop_clicked.connect(self._stop_recording)

        # Settings changes
        self._settings_window.settings_changed.connect(self._on_settings_changed)

    # ── Recording control ──────────────────────────────────────────

    def _on_recording_started(self):
        self._bar.show_recording()
        self._main_window.set_status("recording")

    def _on_recording_cancelled(self):
        self._bar.hide_recording()
        self._main_window.set_status("ready")

    def _on_hotkey_start(self) -> None:
        self._recorder.start()
        self._signals.recording_started.emit()

    def _on_hotkey_stop(self) -> None:
        duration = self._recorder.get_duration()
        audio_bytes = self._recorder.stop()
        self._signals.recording_stopped.emit(audio_bytes, duration)

    def _on_hotkey_cancel(self) -> None:
        self._recorder.cancel()
        self._signals.recording_cancelled.emit()

    def _on_reinsert(self) -> None:
        last = self._injector.get_last_text()
        if last:
            self._signals.processing_done.emit(last)

    def _stop_recording(self) -> None:
        if self._recorder.is_recording:
            self._on_hotkey_stop()

    def _cancel_recording(self) -> None:
        if self._recorder.is_recording:
            self._recorder.cancel()
        self._bar.hide_recording()
        self._main_window.set_status("ready")

    # ── Processing pipeline ────────────────────────────────────────

    def _process_audio(self, audio_bytes: bytes, duration: float) -> None:
        self._bar.hide_recording()
        self._main_window.set_status("processing")

        if not audio_bytes or duration < 0.3:
            self._main_window.set_status("ready")
            return

        def _pipeline():
            try:
                lang_setting = self._db.get_setting(
                    "languages", "English,Bosnian,Danish"
                )
                languages = [l.strip() for l in lang_setting.split(",")]

                result = self._whisper.transcribe(audio_bytes, languages=languages)
                raw_text = result["text"]
                language = result["language"]

                if not raw_text.strip():
                    self._main_window.set_status("ready")
                    return

                vibe = self._db.get_setting("vibe_coding", "False")
                cleaned = self._formatter.format(
                    raw_text=raw_text,
                    language=language,
                    vibe_coding=vibe.lower() == "true",
                )

                mode = "vibe_coding" if vibe.lower() == "true" else "normal"
                self._db.save_dictation(
                    raw_text=raw_text,
                    cleaned_text=cleaned,
                    language=language,
                    mode=mode,
                    duration_seconds=duration,
                )

                self._signals.processing_done.emit(cleaned)

            except Exception as e:
                self._signals.error_occurred.emit(str(e))

        thread = threading.Thread(target=_pipeline, daemon=True)
        thread.start()

    def _deliver_text(self, text: str) -> None:
        if not text:
            return

        self._main_window.set_status("ready")
        self._main_window.refresh()

        success = self._injector.inject(text)
        if not success:
            self._injector.to_clipboard(text)

    # ── UI actions ─────────────────────────────────────────────────

    def _show_main(self) -> None:
        self._main_window.refresh()
        self._main_window.show()
        self._main_window.raise_()

    def _show_settings(self) -> None:
        self._settings_window.show()
        self._settings_window.raise_()

    def _show_dictionary(self) -> None:
        self._dictionary_window.show()
        self._dictionary_window.raise_()

    def _on_settings_changed(self, settings: dict) -> None:
        mic_id = settings.get("mic_device_id")
        if mic_id:
            try:
                self._recorder.set_device(int(mic_id))
            except (ValueError, TypeError):
                self._recorder.set_device(None)

    def _on_error(self, error_msg: str) -> None:
        self._main_window.set_status("ready")
        print(f"Murmur error: {error_msg}")
        self._tray.showMessage(
            "Murmur Error",
            error_msg[:200],
            QSystemTrayIcon.MessageIcon.Warning,
            3000,
        )

    def _quit(self) -> None:
        self._hotkeys.stop()
        self._db.close()
        self._app.quit()

    # ── Run ────────────────────────────────────────────────────────

    def run(self) -> int:
        return self._app.exec()


def main():
    murmur = Murmur()
    sys.exit(murmur.run())


if __name__ == "__main__":
    main()
