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
        if not audio_bytes:
            return {"text": "", "language": "unknown"}

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.wav"

        # No hard language= constraint — Whisper auto-detects per utterance.
        # We pass a soft prompt hint so it knows which languages to expect.
        kwargs = {
            "model": self._model,
            "file": audio_file,
            "response_format": "json",
        }
        if languages:
            lang_list = ", ".join(languages[:5])
            kwargs["prompt"] = f"Speech may be in: {lang_list}. Clean transcription, no filler words."

        response = self._client.audio.transcriptions.create(**kwargs)

        return {
            "text": response.text,
            "language": getattr(response, "language", "unknown"),
        }
