"""Platform dispatcher for hotkey listener."""

import platform

if platform.system() == "Darwin":
    from app.hotkeys.listener_macos import HotkeyListener
elif platform.system() == "Windows":
    from app.hotkeys.listener_windows import HotkeyListener
else:
    raise RuntimeError(f"Unsupported platform: {platform.system()}")

__all__ = ["HotkeyListener"]
