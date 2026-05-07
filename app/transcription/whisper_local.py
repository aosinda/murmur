"""Speech-to-text using a local Whisper model via faster-whisper."""

import tempfile
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
        if not audio_bytes:
            return {"text": "", "language": "unknown"}

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            # No hard language= — let Whisper auto-detect per utterance.
            # Soft hint via initial_prompt so it knows what languages to expect.
            lang_hint = ""
            if languages:
                lang_hint = f"Speech may be in: {', '.join(languages[:5])}. "

            segments, info = self._model.transcribe(
                tmp_path,
                initial_prompt=f"{lang_hint}Clean transcription without filler words like um, uh, ah.",
            )

            text = " ".join(seg.text.strip() for seg in segments)

            return {
                "text": text,
                "language": info.language or "unknown",
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)
