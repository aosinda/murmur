"""Audio feedback sounds for recording start/stop."""

import platform
import threading


def _play_macos_sound(sound_name: str) -> None:
    """Play a macOS system sound."""
    try:
        import AppKit
        sound = AppKit.NSSound.soundNamed_(sound_name)
        if sound:
            sound.play()
    except Exception:
        pass


def _play_beep(frequency: int, duration_ms: int) -> None:
    """Play a simple beep using sounddevice (cross-platform fallback)."""
    try:
        import numpy as np
        import sounddevice as sd
        t = np.linspace(0, duration_ms / 1000, int(44100 * duration_ms / 1000), False)
        # Soft sine wave with fade in/out
        wave = 0.3 * np.sin(2 * np.pi * frequency * t)
        fade = min(len(wave), 200)
        wave[:fade] *= np.linspace(0, 1, fade)
        wave[-fade:] *= np.linspace(1, 0, fade)
        sd.play(wave.astype(np.float32), 44100)
    except Exception:
        pass


def play_start_sound() -> None:
    """Play a subtle sound when recording starts."""
    def _play():
        if platform.system() == "Darwin":
            _play_beep(880, 80)  # Short high blip
        else:
            _play_beep(880, 80)
    threading.Thread(target=_play, daemon=True).start()


def play_stop_sound() -> None:
    """Play a subtle sound when recording stops."""
    def _play():
        if platform.system() == "Darwin":
            _play_beep(660, 80)  # Short lower blip
        else:
            _play_beep(660, 80)
    threading.Thread(target=_play, daemon=True).start()
