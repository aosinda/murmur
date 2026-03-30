"""Text injection — pastes cleaned text into the focused application."""

import subprocess
import time

import AppKit
import Quartz


class TextInjector:
    """Injects text into the currently focused text field via clipboard + Cmd+V."""

    def __init__(self):
        self._pasteboard = AppKit.NSPasteboard.generalPasteboard()
        self._last_text: str = ""

    def inject(self, text: str) -> bool:
        """Paste text into the currently focused field.

        Strategy: Write to clipboard, simulate Cmd+V, then restore original
        clipboard content.

        Args:
            text: The cleaned text to inject.

        Returns:
            True if injection was attempted, False if text was empty.
        """
        if not text:
            return False

        self._last_text = text

        # Save current clipboard
        old_clipboard = self._get_clipboard()

        # Write our text to clipboard
        self._set_clipboard(text)

        # Small delay to ensure clipboard is ready
        time.sleep(0.05)

        # Simulate Cmd+V
        self._simulate_paste()

        # Small delay to let the paste complete
        time.sleep(0.1)

        # Restore original clipboard
        if old_clipboard is not None:
            self._set_clipboard(old_clipboard)

        return True

    def to_clipboard(self, text: str) -> None:
        """Store text in clipboard without pasting (fallback mode)."""
        self._last_text = text
        self._set_clipboard(text)

    def get_last_text(self) -> str:
        """Return the last injected/stored text."""
        return self._last_text

    def _get_clipboard(self) -> str | None:
        """Read current clipboard content."""
        content = self._pasteboard.stringForType_(AppKit.NSPasteboardTypeString)
        return str(content) if content else None

    def _set_clipboard(self, text: str) -> None:
        """Write text to clipboard."""
        self._pasteboard.clearContents()
        self._pasteboard.setString_forType_(text, AppKit.NSPasteboardTypeString)

    @staticmethod
    def _simulate_paste() -> None:
        """Simulate Cmd+V keystroke."""
        # Key code for 'V' is 9
        v_keycode = 9

        # Create Cmd+V key down event
        event_down = Quartz.CGEventCreateKeyboardEvent(None, v_keycode, True)
        Quartz.CGEventSetFlags(
            event_down, Quartz.kCGEventFlagMaskCommand
        )

        # Create Cmd+V key up event
        event_up = Quartz.CGEventCreateKeyboardEvent(None, v_keycode, False)
        Quartz.CGEventSetFlags(
            event_up, Quartz.kCGEventFlagMaskCommand
        )

        # Post events
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)

    @staticmethod
    def has_focused_field() -> bool:
        """Check if there's a focused text input field.

        Uses macOS Accessibility API to check for a focused text element.
        Note: Requires accessibility permissions.
        """
        try:
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                try
                    set focusedElement to focused of frontApp
                    return true
                on error
                    return false
                end try
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=2
            )
            return result.stdout.strip().lower() == "true"
        except Exception:
            # Default to true — attempt paste anyway
            return True
