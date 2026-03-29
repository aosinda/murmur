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
4. When the speaker lists items ("first... second... third..." or "one... two... three..."), format as a numbered list (1. 2. 3.)
4. Apply the provided word replacements exactly as specified
5. DO NOT change the meaning of anything
6. DO NOT rephrase, rewrite, or alter sentences
7. DO NOT add information or opinions
8. DO NOT summarize or shorten the content
9. Preserve the speaker's natural voice and word choices
10. KEEP the original language — if the speaker speaks Bosnian, output Bosnian. If Danish, output Danish. NEVER translate.
11. Output ONLY the cleaned text, nothing else"""

    VIBE_CODING_ADDENDUM = """
Additional context: The speaker is doing vibe coding (dictating instructions for code).
- Preserve technical terms exactly as spoken
- Format code-related terms properly (camelCase, PascalCase, etc. as appropriate)
- Keep imperative instructions clear and direct
- If they mention file paths, function names, or variables, keep them exact"""

    def __init__(self, api_key: str, model: str | None = None):
        self._client = OpenAI(api_key=api_key)
        self._model = model or self.DEFAULT_MODEL
        self._dictionary: dict[str, str] = {}
        self._load_dictionary()

    def format(
        self,
        raw_text: str,
        language: str = "english",
        vibe_coding: bool = False,
    ) -> str:
        """Clean up raw transcription text.

        Args:
            raw_text: Raw transcription from Whisper.
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
