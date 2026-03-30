"""Global hotkey listener for macOS using Quartz event taps.

Supports:
  - Fn hold: push-to-talk (record while held, stop on release)
  - Fn + Space: toggle mode (press to start, stays on after release)
    Then Fn press again → stop
  - Escape: cancel current recording

Uses CGEventTap for reliable Fn key detection on macOS.
"""

import sys
import threading
from enum import Enum
from typing import Callable

import Quartz


# Fn key flag in macOS
kCGEventFlagMaskSecondaryFn = 0x800000

# Key codes
SPACE_KEYCODE = 49
ESCAPE_KEYCODE = 53
V_KEYCODE = 9


class HotkeyListener:
    """Listens for global hotkey events via macOS Quartz event taps."""

    def __init__(
        self,
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
        on_reinsert: Callable[[], None] | None = None,
        max_toggle_duration: float = 360.0,  # 6 minutes
    ):
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_cancel = on_cancel
        self._on_reinsert = on_reinsert
        self._max_toggle_duration = max_toggle_duration

        self._fn_held = False
        self._space_pressed_with_fn = False
        self._toggle_active = False
        self._recording = False
        self._toggle_timer: threading.Timer | None = None
        self._tap = None
        self._thread: threading.Thread | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run_event_tap, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._cancel_toggle_timer()
        if self._tap:
            Quartz.CFMachPortInvalidate(self._tap)
            self._tap = None

    def _run_event_tap(self) -> None:
        event_mask = (
            (1 << Quartz.kCGEventKeyDown) |
            (1 << Quartz.kCGEventKeyUp) |
            (1 << Quartz.kCGEventFlagsChanged)
        )

        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly,
            event_mask,
            self._event_callback,
            None,
        )

        if self._tap is None:
            print("ERROR: Could not create event tap. Check Accessibility permissions.",
                  flush=True)
            return

        run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, self._tap, 0)
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetCurrent(),
            run_loop_source,
            Quartz.kCFRunLoopCommonModes,
        )
        Quartz.CGEventTapEnable(self._tap, True)
        print("[Murmur] Event tap active. Fn=push-to-talk, Fn+Space=toggle.", flush=True)
        Quartz.CFRunLoopRun()

    def _event_callback(self, proxy, event_type, event, refcon):
        try:
            if event_type == Quartz.kCGEventFlagsChanged:
                self._handle_flags_changed(event)
            elif event_type == Quartz.kCGEventKeyDown:
                self._handle_key_down(event)
        except Exception as e:
            print(f"[Murmur] Hotkey error: {e}", file=sys.stderr, flush=True)

        return event

    def _handle_flags_changed(self, event) -> None:
        flags = Quartz.CGEventGetFlags(event)
        fn_pressed = bool(flags & kCGEventFlagMaskSecondaryFn)
        if fn_pressed and not self._fn_held:
            # Fn just pressed
            self._fn_held = True
            self._space_pressed_with_fn = False

            if self._toggle_active:
                self._toggle_active = False
                self._stop_recording()
            elif not self._recording:
                self._start_recording()

        elif not fn_pressed and self._fn_held:
            # Fn just released
            self._fn_held = False

            if self._space_pressed_with_fn:
                # Space was pressed during this Fn hold → enter toggle mode
                # Don't stop recording on Fn release
                self._space_pressed_with_fn = False
                self._toggle_active = True
                self._start_toggle_timer()
            elif self._recording and not self._toggle_active:
                # Normal push-to-talk release → stop
                self._stop_recording()

    def _handle_key_down(self, event) -> None:
        keycode = Quartz.CGEventGetIntegerValueField(
            event, Quartz.kCGKeyboardEventKeycode
        )

        # Fn + Space → mark that toggle was requested
        if keycode == SPACE_KEYCODE and self._fn_held:
            self._space_pressed_with_fn = True

        # Ctrl+Cmd+V → re-insert last output
        elif keycode == V_KEYCODE:
            flags = Quartz.CGEventGetFlags(event)
            has_ctrl = bool(flags & Quartz.kCGEventFlagMaskControl)
            has_cmd = bool(flags & Quartz.kCGEventFlagMaskCommand)
            if has_ctrl and has_cmd and self._on_reinsert:
                self._on_reinsert()

        # Escape → cancel
        elif keycode == ESCAPE_KEYCODE and self._recording:
            self._cancel_recording()
            self._toggle_active = False

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
