"""Speech-to-text using a local Whisper model via faster-whisper."""

import io
import tempfile
import wave
from pathlib import Path


class LocalWhisperClient:
    """Transcribes audio using a local Whisper model (no API needed)."""

    DEFAULT_MODEL = "base"
    MODEL_DIR = Path.home() / ".murmur" / "models"

    def __init__(self, model_size: str | None = None):
        from faster_whisper import WhisperModel

        self._model_size = model_size or self.DEFAULT_MODEL
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)

        self._model = WhisperModel(
            self._model_size,
            download_root=str(self.MODEL_DIR),
            device="auto",
            compute_type="auto",
        )

    def transcribe(
        self,
        audio_bytes: bytes,
        languages: list[str] | None = None,
    ) -> dict:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: WAV audio data.
            languages: List of expected languages (first is used as hint).

        Returns:
            dict with keys: "text", "language"
        """
        if not audio_bytes:
            return {"text": "", "language": "unknown"}

        # Write WAV to temp file (faster-whisper needs a file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            language_hint = None
            if languages:
                language_hint = self._to_iso_code(languages[0])

            kwargs = {}
            if language_hint:
                kwargs["language"] = language_hint

            segments, info = self._model.transcribe(tmp_path, **kwargs)

            text = " ".join(seg.text.strip() for seg in segments)

            return {
                "text": text,
                "language": info.language or language_hint or "en",
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    @staticmethod
    def _to_iso_code(language: str) -> str:
        mapping = {
            "english": "en", "bosnian": "bs", "danish": "da",
            "german": "de", "french": "fr", "spanish": "es",
            "italian": "it", "portuguese": "pt", "dutch": "nl",
            "swedish": "sv", "norwegian": "no", "finnish": "fi",
            "polish": "pl", "turkish": "tr", "russian": "ru",
            "arabic": "ar", "chinese": "zh", "japanese": "ja",
            "korean": "ko", "hindi": "hi", "croatian": "hr", "serbian": "sr",
        }
        return mapping.get(language.lower(), language.lower()[:2])
