"""Text formatting and cleanup via GPT-5.4 Nano."""

import json
from pathlib import Path
from openai import OpenAI


class TextFormatter:
    """Cleans up raw transcription: removes filler, applies dictionary, formats."""

    DEFAULT_MODEL = "gpt-5.4-nano"
    DICTIONARY_PATH = Path.home() / ".murmur" / "dictionary.json"

    SYSTEM_PROMPT = """You are a dictation formatter. Your ONLY job is to clean up spoken text.

Rules:
1. Remove filler words: um, uh, like, you know, I mean, so, basically, actually, right, kind of, sort of
2. Fix punctuation and capitalization
3. Format into proper sentences and paragraphs
4. Apply dictionary replacements ONLY when the spoken phrase clearly matches the intended word — not when the word appears in a different context
5. DO NOT change the meaning, rephrase, rewrite, add information, or summarize
6. When the speaker corrects themselves (says a word then immediately says a different word as a correction), keep ONLY the corrected version. Example: "taste it, test it" → "test it"
7. Preserve the speaker's natural voice and word choices
8. KEEP the original language — never translate
9. Output ONLY the cleaned text, nothing else

Formatting:
- When the speaker says "first", "second", "third" (or "one", "two", "three", etc.) to enumerate items, ALWAYS format as a numbered list:
  1. First item
  2. Second item
  3. Third item
- Each list item on its own line
- When the speaker says "bullet" or lists without numbering, use bullet points (-)"""

    VIBE_CODING_ADDENDUM = """
Additional context: The speaker is doing vibe coding (dictating instructions for code).
- Preserve technical terms exactly as spoken
- Format code-related terms properly (camelCase, PascalCase, etc. as appropriate)
- Keep imperative instructions clear and direct
- If they mention file paths, function names, or variables, keep them exact"""

    # When raw text is at most this many words, skip the GPT call and route
    # through the local regex formatter instead. GPT adds ~1 second per call;
    # for short utterances the local formatter produces the same quality.
    SKIP_GPT_WORD_LIMIT = 25

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: OpenAI | None = None,
    ):
        """Create a formatter.

        Either pass a pre-built `client` (preferred, lets us share an HTTP
        connection pool with the transcribe client) or pass `api_key` and
        we'll build our own.
        """
        if client is not None:
            self._client = client
        else:
            if not api_key:
                raise ValueError("TextFormatter requires either client= or api_key=")
            self._client = OpenAI(api_key=api_key)
        self._model = model or self.DEFAULT_MODEL
        self._dictionary: dict[str, str] = {}
        self._load_dictionary()
        # Lazy-initialized local formatter for the fast path.
        self._local_formatter = None

    def _can_skip_gpt(self, raw_text: str, vibe_coding: bool) -> bool:
        # Vibe coding needs the model's judgment for casing/paths/identifiers.
        if vibe_coding:
            return False
        word_count = len(raw_text.split())
        return word_count <= self.SKIP_GPT_WORD_LIMIT

    def _format_locally(self, raw_text: str, language: str) -> str:
        from app.cleanup.formatter_local import LocalTextFormatter
        if self._local_formatter is None:
            self._local_formatter = LocalTextFormatter()
        # Sync the local formatter's dictionary with ours so replacements apply
        # the same way regardless of which path runs.
        self._local_formatter.update_dictionary(self._dictionary)
        return self._local_formatter.format(raw_text, language=language, vibe_coding=False)

    def format(
        self,
        raw_text: str,
        language: str = "english",
        vibe_coding: bool = False,
    ) -> str:
        """Clean up raw transcription text.

        Short utterances are handled by the local regex formatter to avoid a
        round-trip to GPT. Longer or vibe-coding utterances go to GPT.

        Args:
            raw_text: Raw transcription from the transcription model.
            language: Detected language of the speech.
            vibe_coding: Whether vibe coding mode is active.

        Returns:
            Cleaned, formatted text.
        """
        if not raw_text.strip():
            return ""

        system = self.SYSTEM_PROMPT
        if vibe_coding:
            system += self.VIBE_CODING_ADDENDUM

        # Build user prompt with dictionary and language context
        user_parts = []

        if self._dictionary:
            replacements = "\n".join(
                f'  "{k}" → "{v}"' for k, v in self._dictionary.items()
            )
            user_parts.append(f"Word replacements to apply:\n{replacements}")

        user_parts.append(f"Language: {language}")
        user_parts.append(f"Raw dictation:\n{raw_text}")

        user_prompt = "\n\n".join(user_parts)

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temp = faithful to original
            max_completion_tokens=4096,
        )

        return response.choices[0].message.content.strip()

    # ── Dictionary management ──────────────────────────────────────

    def _load_dictionary(self) -> None:
        """Load dictionary from JSON file."""
        if self.DICTIONARY_PATH.exists():
            try:
                self._dictionary = json.loads(
                    self.DICTIONARY_PATH.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                self._dictionary = {}

    def save_dictionary(self) -> None:
        """Save dictionary to JSON file."""
        self.DICTIONARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.DICTIONARY_PATH.write_text(
            json.dumps(self._dictionary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_word(self, spoken: str, replacement: str) -> None:
        """Add a dictionary mapping."""
        self._dictionary[spoken.lower()] = replacement
        self.save_dictionary()

    def remove_word(self, spoken: str) -> None:
        """Remove a dictionary mapping."""
        self._dictionary.pop(spoken.lower(), None)
        self.save_dictionary()

    def get_dictionary(self) -> dict[str, str]:
        """Return current dictionary."""
        return dict(self._dictionary)

    def update_dictionary(self, entries: dict[str, str]) -> None:
        """Replace entire dictionary."""
        self._dictionary = {k.lower(): v for k, v in entries.items()}
        self.save_dictionary()
