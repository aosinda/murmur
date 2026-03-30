"""Text injection for Windows — pastes text via clipboard + Ctrl+V."""

import time
import ctypes
import ctypes.wintypes


# Windows API constants
CF_UNICODETEXT = 13
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_V = 0x56


class TextInjector:
    """Injects text into the currently focused text field on Windows."""

    def __init__(self):
        self._last_text: str = ""

    def inject(self, text: str) -> bool:
        """Paste text into the currently focused field via clipboard + Ctrl+V."""
        if not text:
            return False

        self._last_text = text

        old_clipboard = self._get_clipboard()
        self._set_clipboard(text)
        time.sleep(0.05)
        self._simulate_paste()
        time.sleep(0.1)

        if old_clipboard is not None:
            self._set_clipboard(old_clipboard)

        return True

    def to_clipboard(self, text: str) -> None:
        self._last_text = text
        self._set_clipboard(text)

    def get_last_text(self) -> str:
        return self._last_text

    @staticmethod
    def _get_clipboard() -> str | None:
        try:
            ctypes.windll.user32.OpenClipboard(0)
            handle = ctypes.windll.user32.GetClipboardData(CF_UNICODETEXT)
            if handle:
                data = ctypes.c_wchar_p(handle)
                text = data.value
                ctypes.windll.user32.CloseClipboard()
                return text
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            try:
                ctypes.windll.user32.CloseClipboard()
            except Exception:
                pass
        return None

    @staticmethod
    def _set_clipboard(text: str) -> None:
        try:
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()

            data = text.encode("utf-16-le") + b"\x00\x00"
            h_mem = ctypes.windll.kernel32.GlobalAlloc(0x0042, len(data))
            ptr = ctypes.windll.kernel32.GlobalLock(h_mem)
            ctypes.memmove(ptr, data, len(data))
            ctypes.windll.kernel32.GlobalUnlock(h_mem)

            ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, h_mem)
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            try:
                ctypes.windll.user32.CloseClipboard()
            except Exception:
                pass

    @staticmethod
    def _simulate_paste() -> None:
        """Simulate Ctrl+V keystroke."""
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_V, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
