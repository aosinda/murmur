"""Audio device discovery and selection."""

import sounddevice as sd


class DeviceManager:
    """Lists and selects audio input devices."""

    @staticmethod
    def refresh() -> None:
        # Flush PortAudio's cached device list so it picks up the current
        # macOS default input after AirPods disconnect / USB mic unplug.
        try:
            sd._terminate()
        except Exception:
            pass
        try:
            sd._initialize()
        except Exception:
            pass

    @staticmethod
    def describe(device_id: int | None) -> str:
        """Human-readable label for a device id (or the resolved default)."""
        try:
            if device_id is None:
                default = sd.default.device[0]
                dev = sd.query_devices(default)
                return f"default → {dev['name']} (id={default})"
            dev = sd.query_devices(device_id)
            return f"{dev['name']} (id={device_id})"
        except Exception as e:
            return f"<unknown id={device_id}: {e}>"

    @staticmethod
    def list_input_devices() -> list[dict]:
        """Return a list of available input devices.

        Each entry: {"id": int, "name": str, "channels": int, "is_default": bool}
        """
        DeviceManager.refresh()
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

        print(f"[Murmur/audio] list_input_devices(): default={default_input}", flush=True)
        for d in input_devices:
            star = " *" if d["is_default"] else "  "
            print(f"[Murmur/audio]{star} id={d['id']:>2}  ch={d['channels']}  {d['name']}",
                  flush=True)

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
