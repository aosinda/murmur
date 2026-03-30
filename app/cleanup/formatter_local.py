"""Basic text cleanup without any API — regex-based filler removal and formatting."""

import json
import re
from pathlib import Path


class LocalTextFormatter:
    """Cleans up transcription text locally without any API calls."""

    DICTIONARY_PATH = Path.home() / ".murmur" / "dictionary.json"

    # Filler words/phrases to remove (case-insensitive)
    FILLERS = [
        r"\bum+\b", r"\buh+\b", r"\bah+\b", r"\beh+\b",
        r"\byou know\b", r"\bI mean\b", r"\blike,?\s*(?=\w)",
        r"\bbasically\b", r"\bactually\b", r"\bkind of\b",
        r"\bsort of\b", r"\bright\b(?=\s*[,.])",
    ]

    def __init__(self, **_kwargs):
        self._dictionary: dict[str, str] = {}
        self._load_dictionary()
        self._filler_pattern = re.compile(
            "|".join(self.FILLERS), re.IGNORECASE
        )

    def format(
        self,
        raw_text: str,
        language: str = "english",
        vibe_coding: bool = False,
    ) -> str:
        if not raw_text.strip():
            return ""

        text = raw_text

        # Remove fillers
        text = self._filler_pattern.sub("", text)

        # Apply dictionary replacements
        for spoken, replacement in self._dictionary.items():
            pattern = re.compile(re.escape(spoken), re.IGNORECASE)
            text = pattern.sub(replacement, text)

        # Format numbered lists: "first... second... third..."
        text = self._format_lists(text)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)
        text = re.sub(r"([.!?])\s*(\w)", lambda m: f"{m.group(1)} {m.group(2).upper()}", text)

        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]

        return text

    def _format_lists(self, text: str) -> str:
        """Convert spoken ordinals to numbered list."""
        ordinals = [
            ("first", "1"), ("second", "2"), ("third", "3"),
            ("fourth", "4"), ("fifth", "5"), ("sixth", "6"),
            ("seventh", "7"), ("eighth", "8"), ("ninth", "9"), ("tenth", "10"),
        ]

        # Only format if at least 2 ordinals are present
        count = sum(1 for w, _ in ordinals if re.search(rf"\b{w}\b", text, re.IGNORECASE))
        if count < 2:
            return text

        for word, num in ordinals:
            text = re.sub(
                rf"\b{word}[,:]?\s*", f"\n{num}. ", text, flags=re.IGNORECASE
            )

        return text.strip()

    # ── Dictionary management (same interface as cloud formatter) ──

    def _load_dictionary(self) -> None:
        if self.DICTIONARY_PATH.exists():
            try:
                self._dictionary = json.loads(
                    self.DICTIONARY_PATH.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                self._dictionary = {}

    def save_dictionary(self) -> None:
        self.DICTIONARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.DICTIONARY_PATH.write_text(
            json.dumps(self._dictionary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add_word(self, spoken: str, replacement: str) -> None:
        self._dictionary[spoken.lower()] = replacement
        self.save_dictionary()

    def remove_word(self, spoken: str) -> None:
        self._dictionary.pop(spoken.lower(), None)
        self.save_dictionary()

    def get_dictionary(self) -> dict[str, str]:
        return dict(self._dictionary)

    def update_dictionary(self, entries: dict[str, str]) -> None:
        self._dictionary = {k.lower(): v for k, v in entries.items()}
        self.save_dictionary()
