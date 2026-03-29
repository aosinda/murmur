"""Audio device discovery and selection."""

import sounddevice as sd


class DeviceManager:
    """Lists and selects audio input devices."""

    @staticmethod
    def list_input_devices() -> list[dict]:
        """Return a list of available input devices.

        Each entry: {"id": int, "name": str, "channels": int, "is_default": bool}
        """
        devices = sd.query_devices()
        default_input = sd.default.device[0]

        input_devices = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                input_devices.append({
                    "id": i,
                    "name": dev["name"],
                    "channels": dev["max_input_channels"],
                    "is_default": i == default_input,
                })

        return input_devices

    @staticmethod
    def get_default_device_id() -> int | None:
        """Return the system default input device ID."""
        try:
            return sd.default.device[0]
        except Exception:
            return None

    @staticmethod
    def validate_device(device_id: int) -> bool:
        """Check if a device ID is a valid input device."""
        try:
            dev = sd.query_devices(device_id)
            return dev["max_input_channels"] > 0
        except Exception:
            return False
