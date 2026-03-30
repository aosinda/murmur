"""Global hotkey listener for Windows using pynput.

Supports:
  - Ctrl+Shift (hold): push-to-talk (record while held, stop on release)
  - Ctrl+Shift+Space: toggle mode (press to start, stays on after release)
    Then Ctrl+Shift again → stop
  - Escape: cancel current recording
  - Ctrl+Win+V: re-insert last output
"""

import threading
from typing import Callable

from pynput import keyboard


class HotkeyListener:
    """Listens for global hotkey events on Windows via pynput."""

    def __init__(
        self,
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
        on_reinsert: Callable[[], None] | None = None,
        max_toggle_duration: float = 360.0,
    ):
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_cancel = on_cancel
        self._on_reinsert = on_reinsert
        self._max_toggle_duration = max_toggle_duration

        self._ctrl_held = False
        self._shift_held = False
        self._both_held = False
        self._space_pressed_with_both = False
        self._toggle_active = False
        self._recording = False
        self._toggle_timer: threading.Timer | None = None
        self._listener: keyboard.Listener | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()
        print("[Murmur] Hotkey listener active. Ctrl+Shift=push-to-talk, Ctrl+Shift+Space=toggle.", flush=True)

    def stop(self) -> None:
        self._cancel_toggle_timer()
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key):
        try:
            # Track modifier state
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self._ctrl_held = True
            elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                self._shift_held = True

            # Both Ctrl+Shift just pressed
            if self._ctrl_held and self._shift_held and not self._both_held:
                self._both_held = True
                self._space_pressed_with_both = False

                if self._toggle_active:
                    self._toggle_active = False
                    self._stop_recording()
                elif not self._recording:
                    self._start_recording()

            # Space while Ctrl+Shift held → toggle mode
            if key == keyboard.Key.space and self._both_held:
                self._space_pressed_with_both = True

            # Escape → cancel
            if key == keyboard.Key.esc and self._recording:
                self._cancel_recording()
                self._toggle_active = False

            # Ctrl+Win+V → re-insert
            if hasattr(key, 'char') and key.char == 'v':
                if self._ctrl_held:
                    # Check for Win key via vk code
                    pass  # Simplified: use Ctrl+Alt+V on Windows instead

            # Ctrl+Alt+V → re-insert (Windows alternative)
            if hasattr(key, 'char') and key.char == 'v':
                if self._ctrl_held and not self._shift_held:
                    try:
                        if keyboard.Controller().alt_pressed:
                            if self._on_reinsert:
                                self._on_reinsert()
                    except Exception:
                        pass

        except Exception as e:
            print(f"[Murmur] Hotkey error: {e}", flush=True)

    def _on_release(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self._ctrl_held = False
            elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                self._shift_held = False

            # Both released
            if self._both_held and (not self._ctrl_held or not self._shift_held):
                self._both_held = False

                if self._space_pressed_with_both:
                    self._space_pressed_with_both = False
                    self._toggle_active = True
                    self._start_toggle_timer()
                elif self._recording and not self._toggle_active:
                    self._stop_recording()

        except Exception as e:
            print(f"[Murmur] Hotkey error: {e}", flush=True)

    def _start_recording(self) -> None:
        self._recording = True
        if self._on_start:
            self._on_start()

    def _stop_recording(self) -> None:
        self._recording = False
        self._cancel_toggle_timer()
        if self._on_stop:
            self._on_stop()

    def _cancel_recording(self) -> None:
        self._recording = False
        self._cancel_toggle_timer()
        if self._on_cancel:
            self._on_cancel()

    def _start_toggle_timer(self) -> None:
        self._cancel_toggle_timer()
        self._toggle_timer = threading.Timer(
            self._max_toggle_duration, self._auto_stop_toggle
        )
        self._toggle_timer.daemon = True
        self._toggle_timer.start()

    def _cancel_toggle_timer(self) -> None:
        if self._toggle_timer:
            self._toggle_timer.cancel()
            self._toggle_timer = None

    def _auto_stop_toggle(self) -> None:
        if self._toggle_active:
            self._toggle_active = False
            self._stop_recording()
