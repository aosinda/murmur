"""Platform dispatcher for text injector."""

import platform

if platform.system() == "Darwin":
    from app.output.injector_macos import TextInjector
elif platform.system() == "Windows":
    from app.output.injector_windows import TextInjector
else:
    raise RuntimeError(f"Unsupported platform: {platform.system()}")

__all__ = ["TextInjector"]
