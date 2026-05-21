"""Speech-to-text via OpenAI's transcription API (gpt-4o-mini-transcribe)."""

import io
import time
from concurrent.futures import ThreadPoolExecutor, FIRST_COMPLETED, wait

import soundfile as sf
from openai import OpenAI


class CloudTranscribeClient:
    """Transcribes audio using OpenAI's gpt-4o-mini-transcribe model.

    Note: the local-mode counterpart in whisper_local.py uses Whisper proper
    via faster-whisper. This cloud client used to use whisper-1 (hence the
    old WhisperClient name), but was switched to gpt-4o-mini-transcribe
    for ~2x speed and half the cost.
    """

    DEFAULT_MODEL = "gpt-4o-mini-transcribe"

    # If the first transcribe call hasn't returned within this many seconds,
    # fire a second identical request in parallel and take whichever wins.
    # Trades a (rare) duplicate API spend for tail-latency resilience when
    # the network has bufferbloat.
    HEDGE_AFTER_SECONDS = 2.5

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: OpenAI | None = None,
    ):
        """Create a transcribe client.

        Either pass a pre-built `client` (preferred, lets us share an HTTP
        connection pool with the formatter) or pass `api_key` and we'll
        build our own.
        """
        if client is not None:
            self._client = client
        else:
            if not api_key:
                raise ValueError("CloudTranscribeClient requires either client= or api_key=")
            self._client = OpenAI(api_key=api_key)
        self._model = model or self.DEFAULT_MODEL

    # ── Payload encoding ───────────────────────────────────────────

    @staticmethod
    def _wav_to_flac(wav_bytes: bytes) -> bytes:
        """Re-encode a WAV byte blob as FLAC. Lossless, ~50–60% smaller."""
        data, sr = sf.read(io.BytesIO(wav_bytes))
        out = io.BytesIO()
        sf.write(out, data, sr, format="FLAC", subtype="PCM_16")
        return out.getvalue()

    # ── Hedged transcribe ──────────────────────────────────────────

    def _do_transcribe_once(self, audio_bytes: bytes, kwargs: dict):
        """Single transcribe attempt. BytesIO is single-use, so wrap each call."""
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.flac"
        call_kwargs = dict(kwargs)
        call_kwargs["file"] = audio_file
        # max_retries=0 prevents the SDK from doubling up on top of our hedge.
        client = self._client.with_options(max_retries=0)
        return client.audio.transcriptions.create(**call_kwargs)

    def _hedged_transcribe(self, audio_bytes: bytes, kwargs: dict):
        """Run transcribe with a 2.5 s hedge: if it stalls, fire a second one.

        The two requests race; whichever returns first wins, the loser is
        cancelled best-effort (the network call may still complete server-side,
        but the Python future is dropped).
        """
        executor = ThreadPoolExecutor(max_workers=2)
        try:
            first = executor.submit(self._do_transcribe_once, audio_bytes, kwargs)
            done, _ = wait([first], timeout=self.HEDGE_AFTER_SECONDS, return_when=FIRST_COMPLETED)
            if first in done:
                return first.result(), False  # finished before hedge timer
            # Hedge: fire a second identical request and race them.
            second = executor.submit(self._do_transcribe_once, audio_bytes, kwargs)
            done, _ = wait([first, second], return_when=FIRST_COMPLETED)
            winner = next(iter(done))
            # Best-effort cancel of the loser. If it's mid-network, this is a
            # no-op, but the future itself is discarded.
            for f in (first, second):
                if f is not winner:
                    f.cancel()
            return winner.result(), True
        finally:
            # Don't wait on the loser to finish; let the daemon threads die.
            executor.shutdown(wait=False, cancel_futures=True)

    # ── Public API ─────────────────────────────────────────────────

    def transcribe(
        self,
        audio_bytes: bytes,
        languages: list[str] | None = None,
    ) -> dict:
        if not audio_bytes:
            return {"text": "", "language": "unknown"}

        # Re-encode WAV → FLAC. Lossless and roughly half the bytes on the wire.
        flac_bytes = self._wav_to_flac(audio_bytes)
        print(f"[Murmur] Batch: WAV→FLAC {len(audio_bytes)//1024}KB → {len(flac_bytes)//1024}KB",
              flush=True)

        # No hard language= constraint — Whisper auto-detects per utterance.
        # We pass a soft prompt hint so it knows which languages to expect.
        kwargs = {
            "model": self._model,
            "response_format": "json",
        }
        if languages:
            lang_list = ", ".join(languages[:5])
            kwargs["prompt"] = lang_list

        t0 = time.time()
        response, hedged = self._hedged_transcribe(flac_bytes, kwargs)
        api_ms = (time.time() - t0) * 1000
        hedge_tag = " (hedged)" if hedged else ""
        print(f"[Murmur] Batch: API returned in {api_ms:.0f}ms{hedge_tag}", flush=True)

        return {
            "text": response.text,
            "language": getattr(response, "language", "unknown"),
        }
