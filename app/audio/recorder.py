"""Audio recording module — captures mic input into a buffer."""

import io
import time
import wave
import threading
import numpy as np
import sounddevice as sd

from app.audio.devices import DeviceManager


class AudioRecorder:
    """Records audio from the selected input device."""

    SAMPLE_RATE = 16000  # Whisper expects 16kHz
    CHANNELS = 1         # Mono
    DTYPE = "int16"

    def __init__(self, device_id: int | None = None):
        self._device_id = device_id
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._recording = False
        self._lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        """Start recording audio."""
        if self._recording:
            return

        self._frames = []
        self._recording = True

        # Always flush PortAudio's cached device list before opening.
        # If AirPods were the default at app launch and got disconnected,
        # InputStream(device=None) still "succeeds" silently against the
        # stale default and produces no audio — so we never see an
        # exception to trigger the retry path. Refreshing here makes
        # `default` resolve to whatever macOS actually has selected now.
        DeviceManager.refresh()

        # Preflight: drop a saved device id that's clearly gone (AirPods
        # removed, USB mic unplugged).
        if self._device_id is not None and not self._device_exists(self._device_id):
            print(f"[Murmur] Device {self._device_id} no longer present, using default.",
                  flush=True)
            self._device_id = None

        print(f"[Murmur] Recording from: {DeviceManager.describe(self._device_id)}",
              flush=True)

        try:
            self._stream = self._open_stream(self._device_id)
        except Exception as first_err:
            # PortAudio caches the device topology at init time, so when
            # macOS switches the default input (AirPods out, etc.) even
            # device=None can resolve to a stale, now-invalid device.
            # Refresh PortAudio and retry against the system default.
            if self._device_id is not None:
                print(f"[Murmur] Device {self._device_id} failed, falling back to default mic.",
                      flush=True)
                self._device_id = None

            last_err = first_err
            for attempt in range(4):
                if attempt > 0:
                    time.sleep(0.4)
                DeviceManager.refresh()
                print(f"[Murmur] Retry {attempt + 1}/4 after refresh → "
                      f"{DeviceManager.describe(None)}", flush=True)
                try:
                    self._stream = self._open_stream(None)
                    last_err = None
                    break
                except Exception as e:
                    last_err = e

            if last_err:
                self._recording = False
                raise RuntimeError(f"No working audio input: {last_err}") from last_err

        self._stream.start()

    def _open_stream(self, device_id: int | None) -> sd.InputStream:
        """Open a PortAudio InputStream for the given device."""
        return sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.DTYPE,
            device=device_id,
            callback=self._audio_callback,
            blocksize=1024,
        )

    @staticmethod
    def _device_exists(device_id: int) -> bool:
        try:
            devices = sd.query_devices()
        except Exception:
            return False
        if not (0 <= device_id < len(devices)):
            return False
        return devices[device_id].get("max_input_channels", 0) > 0


    def stop(self) -> bytes:
        """Stop recording and return WAV bytes."""
        if not self._recording:
            return b""

        self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        return self._frames_to_wav()

    def cancel(self) -> None:
        """Cancel recording, discard audio."""
        self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self._frames = []

    def set_device(self, device_id: int | None) -> None:
        """Change the input device. None = system default."""
        self._device_id = device_id

    def _audio_callback(self, indata: np.ndarray, frames: int,
                        time_info, status) -> None:
        """Called by sounddevice for each audio block."""
        if self._recording:
            with self._lock:
                self._frames.append(indata.copy())

    def _frames_to_wav(self) -> bytes:
        """Convert recorded frames to WAV byte buffer."""
        if not self._frames:
            return b""

        with self._lock:
            audio_data = np.concatenate(self._frames, axis=0)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())

        buf.seek(0)
        return buf.read()

    def get_duration(self) -> float:
        """Return current recording duration in seconds."""
        with self._lock:
            if not self._frames:
                return 0.0
            total_frames = sum(f.shape[0] for f in self._frames)
            return total_frames / self.SAMPLE_RATE
