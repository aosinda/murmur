"""Speech-to-text via OpenAI Whisper API."""

import io
from openai import OpenAI


class WhisperClient:
    """Transcribes audio using OpenAI's Whisper API."""

    DEFAULT_MODEL = "gpt-4o-mini-transcribe"

    def __init__(self, api_key: str, model: str | None = None):
        self._client = OpenAI(api_key=api_key)
        self._model = model or self.DEFAULT_MODEL

    def transcribe(
        self,
        audio_bytes: bytes,
        languages: list[str] | None = None,
    ) -> dict:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: WAV audio data.
            languages: List of expected languages for auto-detection.
                       Whisper uses the first as a hint but auto-detects.

        Returns:
            dict with keys: "text", "language"
        """
        if not audio_bytes:
            return {"text": "", "language": "unknown"}

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.wav"

        # Whisper accepts a language hint (ISO 639-1 code)
        # We pass the first configured language as a hint,
        # but Whisper will auto-detect if speech is in another language
        language_hint = None
        if languages:
            language_hint = self._to_iso_code(languages[0])

        kwargs = {
            "model": self._model,
            "file": audio_file,
            "response_format": "json",
        }
        if language_hint:
            kwargs["language"] = language_hint

        response = self._client.audio.transcriptions.create(**kwargs)

        return {
            "text": response.text,
            "language": getattr(response, "language", language_hint or "en"),
        }

    @staticmethod
    def _to_iso_code(language: str) -> str:
        """Convert language name to ISO 639-1 code."""
        mapping = {
            "english": "en",
            "bosnian": "bs",
            "danish": "da",
            "german": "de",
            "french": "fr",
            "spanish": "es",
            "italian": "it",
            "portuguese": "pt",
            "dutch": "nl",
            "swedish": "sv",
            "norwegian": "no",
            "finnish": "fi",
            "polish": "pl",
            "turkish": "tr",
            "russian": "ru",
            "arabic": "ar",
            "chinese": "zh",
            "japanese": "ja",
            "korean": "ko",
            "hindi": "hi",
            "croatian": "hr",
            "serbian": "sr",
        }
        return mapping.get(language.lower(), language.lower()[:2])
