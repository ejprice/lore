"""Exact, offline token counting for the Voyage embedding models.

:class:`VoyageTokenCounter` wraps the *pinned, committed* voyage-4 tokenizer
shipped alongside this package at ``data/voyage4_tokenizer.json``. It returns the
exact token counts the live Voyage endpoint charges and limits against, with **no
network access and no Hugging Face download** — the tokenizer is loaded straight
from the on-disk file via :meth:`tokenizers.Tokenizer.from_file`.

The loaded tokenizer is cached at class level so the (multi-megabyte) file is
parsed at most once per process, regardless of how many counters are built.
"""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from tokenizers import Tokenizer

# Path to the committed, pinned voyage-4 tokenizer (resolved relative to this
# module so it works from an installed wheel or an editable checkout).
_TOKENIZER_PATH: Path = Path(__file__).parent / "data" / "voyage4_tokenizer.json"

# Special tokens are excluded so the count reflects only the content tokens the
# Voyage endpoint bills/limits against (and matches the live-server oracle).
_ADD_SPECIAL_TOKENS: bool = False


class VoyageTokenCounter:
    """Exact, offline token counter backed by the pinned voyage-4 tokenizer.

    The underlying :class:`tokenizers.Tokenizer` is loaded once and shared across
    all instances. Construction is cheap after the first instance; counting is a
    direct call into the Rust tokenizer.
    """

    _tokenizer: Tokenizer | None = None
    _lock: Lock = Lock()

    def __init__(self) -> None:
        """Build a counter, loading and caching the pinned tokenizer on first use."""
        self._ensure_tokenizer_loaded()

    @classmethod
    def _ensure_tokenizer_loaded(cls) -> Tokenizer:
        """Load the pinned tokenizer from disk once and cache it at class level.

        Returns:
            The shared :class:`tokenizers.Tokenizer` instance.
        """
        if cls._tokenizer is None:
            with cls._lock:
                # Re-check inside the lock to avoid a double load under threads.
                if cls._tokenizer is None:
                    cls._tokenizer = Tokenizer.from_file(str(_TOKENIZER_PATH))
        return cls._tokenizer

    def count(self, text: str) -> int:
        """Return the exact token count for a single string.

        Args:
            text: The string to tokenize.

        Returns:
            The number of content tokens (special tokens excluded).
        """
        tokenizer = self._ensure_tokenizer_loaded()
        return len(tokenizer.encode(text, add_special_tokens=_ADD_SPECIAL_TOKENS).ids)

    def count_tokens(self, texts: list[str]) -> list[int]:
        """Return an input-aligned list of exact token counts.

        Args:
            texts: The strings to tokenize.

        Returns:
            A list with one exact token count per input, in the same order.
        """
        return [self.count(text) for text in texts]
