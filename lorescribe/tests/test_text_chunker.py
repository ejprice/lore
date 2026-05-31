"""Contract tests for TextChunker — the plain-text fallback chunker.

TextChunker claims ``.txt`` and ``.rst`` files and splits their content into
``RecursiveCharacterTextSplitter``-sized windows, each identified by
``window#N`` with a matching ``sub_ordinal``.

Adversarial coverage:
  1. Window identities are distinct across a multi-chunk file.
  2. Window identities are strictly sequential (window#0, window#1, …).
  3. sub_ordinal equals the window index (not pinned to 0).
  4. A long file produces multiple chunks, not just 1.
  5. Empty source → [].
  6. Whitespace-only source → [].
  7. Each chunk's source_text stays ≤ max_input_tokens.
  8. handles('.txt') and handles('.rst') return True.
  9. handles for non-claimed extensions returns False.
  10. Single short file → exactly 1 chunk, identity "window#0", sub_ordinal 0.
  11. chunk_type is always "text".
  12. line_start and line_end are ≥ 1 for every chunk.
  13. Case-insensitive extension dispatch: .TXT and .RST are claimed.
"""

from __future__ import annotations

from collections.abc import Callable

from lorescribe.models import ChunkContext
from lorescribe.text import TextChunker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_SLUG = "test-project"
SAMPLE_FILE_PATH = "docs/guide.txt"


def _default_count_tokens(text: str) -> int:
    """Approximate token counter: ~4 chars per token."""
    return max(1, len(text) // 4)


def _make_ctx(
    max_input_tokens: int,
    count_tokens: Callable[[str], int] | None = None,
    file_path: str = SAMPLE_FILE_PATH,
) -> ChunkContext:
    """Build a ChunkContext with a configurable token cap."""
    if count_tokens is None:
        count_tokens = _default_count_tokens
    return ChunkContext(
        slug=SAMPLE_SLUG,
        file_path=file_path,
        count_tokens=count_tokens,
        max_input_tokens=max_input_tokens,
    )


def _long_text(approx_tokens: int) -> str:
    """Generate prose whose ~4-chars/token estimate exceeds ``approx_tokens``."""
    # One sentence ≈ 10 tokens.  Repeat enough times to exceed the cap.
    sentence = "The quick brown fox jumps over the lazy dog. "
    repetitions = (approx_tokens // 10) + 5
    return sentence * repetitions


# ---------------------------------------------------------------------------
# handles()
# ---------------------------------------------------------------------------


class TestHandles:
    def setup_method(self) -> None:
        self.chunker = TextChunker()

    def test_handles_txt(self) -> None:
        assert self.chunker.handles("readme.txt") is True

    def test_handles_rst(self) -> None:
        assert self.chunker.handles("CHANGES.rst") is True

    def test_handles_txt_uppercase(self) -> None:
        """Extension matching must be case-insensitive."""
        assert self.chunker.handles("README.TXT") is True

    def test_handles_rst_uppercase(self) -> None:
        """Extension matching must be case-insensitive."""
        assert self.chunker.handles("changes.RST") is True

    def test_does_not_handle_py(self) -> None:
        assert self.chunker.handles("script.py") is False

    def test_does_not_handle_md(self) -> None:
        assert self.chunker.handles("notes.md") is False

    def test_does_not_handle_no_extension(self) -> None:
        assert self.chunker.handles("Makefile") is False

    def test_does_not_handle_empty_string(self) -> None:
        assert self.chunker.handles("") is False

    def test_does_not_handle_xml(self) -> None:
        assert self.chunker.handles("schema.xml") is False


# ---------------------------------------------------------------------------
# chunk() — empty / whitespace inputs
# ---------------------------------------------------------------------------


class TestChunkEmpty:
    def setup_method(self) -> None:
        self.chunker = TextChunker()
        self.ctx = _make_ctx(max_input_tokens=8192)

    def test_empty_source_returns_empty_list(self) -> None:
        assert self.chunker.chunk("", self.ctx) == []

    def test_whitespace_only_source_returns_empty_list(self) -> None:
        assert self.chunker.chunk("   \n\t\n  ", self.ctx) == []

    def test_newlines_only_returns_empty_list(self) -> None:
        assert self.chunker.chunk("\n\n\n", self.ctx) == []


# ---------------------------------------------------------------------------
# chunk() — single short document
# ---------------------------------------------------------------------------


class TestChunkSingleWindow:
    def setup_method(self) -> None:
        self.chunker = TextChunker()
        # Large cap so a short document is a single window.
        self.ctx = _make_ctx(max_input_tokens=8192)
        self.source = "Hello, world. This is a short text document.\n"
        self.chunks = self.chunker.chunk(self.source, self.ctx)

    def test_produces_exactly_one_chunk(self) -> None:
        assert len(self.chunks) == 1

    def test_chunk_type_is_text(self) -> None:
        assert self.chunks[0].chunk_type == "text"

    def test_identity_is_window_zero(self) -> None:
        assert self.chunks[0].identity == "window#0"

    def test_sub_ordinal_is_zero(self) -> None:
        assert self.chunks[0].sub_ordinal == 0

    def test_source_text_contains_input(self) -> None:
        # The chunk's source_text must be a verbatim, reconstructable substring
        # of the original source — not merely non-empty. A chunker that mangled
        # or re-synthesised content would pass a non-empty check but fail this.
        assert self.chunks[0].source_text.strip() != ""
        assert self.chunks[0].source_text in self.source

    def test_line_start_is_positive(self) -> None:
        assert self.chunks[0].line_start >= 1

    def test_line_end_is_positive(self) -> None:
        assert self.chunks[0].line_end >= 1

    def test_line_end_ge_line_start(self) -> None:
        assert self.chunks[0].line_end >= self.chunks[0].line_start


# ---------------------------------------------------------------------------
# chunk() — multi-window (long document, small token cap)
# ---------------------------------------------------------------------------


class TestChunkMultipleWindows:
    """A small max_input_tokens forces the long text into multiple windows.

    Uses a STRICTER 1-token-per-character counter than the implementation's
    internal 4-chars-per-token estimate, so the first-pass splitter's windows
    overshoot the cap and the ``_fit_to_cap`` second pass genuinely engages.
    With the lenient 4-chars/token counter the second pass would never run,
    giving false confidence that the cap is enforced.
    """

    SMALL_CAP = 20  # tokens

    @staticmethod
    def _strict_count_tokens(text: str) -> int:
        """One token per character — stricter than the impl's 4-chars/token."""
        return len(text)

    def setup_method(self) -> None:
        self.chunker = TextChunker()
        self.ctx = _make_ctx(
            max_input_tokens=self.SMALL_CAP,
            count_tokens=self._strict_count_tokens,
        )
        # Generate text that is clearly more than SMALL_CAP tokens.
        self.source = _long_text(approx_tokens=self.SMALL_CAP * 5)
        self.chunks = self.chunker.chunk(self.source, self.ctx)

    def test_produces_multiple_chunks(self) -> None:
        assert len(self.chunks) >= 2, (
            f"Expected ≥2 chunks for a {len(self.source)}-char source "
            f"with cap={self.SMALL_CAP}, got {len(self.chunks)}"
        )

    def test_identities_are_distinct(self) -> None:
        identities = [c.identity for c in self.chunks]
        assert len(identities) == len(set(identities)), (
            f"Duplicate identities found: {identities}"
        )

    def test_identities_are_sequential(self) -> None:
        """Identities must be window#0, window#1, … window#N-1 in order."""
        expected = [f"window#{n}" for n in range(len(self.chunks))]
        actual = [c.identity for c in self.chunks]
        assert actual == expected

    def test_sub_ordinals_match_window_index(self) -> None:
        """sub_ordinal must equal the window index, not be pinned to 0."""
        for n, chunk in enumerate(self.chunks):
            assert chunk.sub_ordinal == n, (
                f"chunk[{n}].sub_ordinal={chunk.sub_ordinal}, expected {n}"
            )

    def test_each_chunk_respects_token_cap(self) -> None:
        """Every chunk must be ≤ max_input_tokens as measured by the injected counter."""
        for n, chunk in enumerate(self.chunks):
            token_count = self.ctx.count_tokens(chunk.source_text)
            assert token_count <= self.SMALL_CAP, (
                f"chunk[{n}] has {token_count} tokens, cap is {self.SMALL_CAP}"
            )

    def test_chunk_type_is_text_for_all(self) -> None:
        assert all(c.chunk_type == "text" for c in self.chunks)

    def test_line_start_positive_for_all(self) -> None:
        for n, chunk in enumerate(self.chunks):
            assert chunk.line_start >= 1, f"chunk[{n}].line_start={chunk.line_start}"

    def test_line_end_positive_for_all(self) -> None:
        for n, chunk in enumerate(self.chunks):
            assert chunk.line_end >= 1, f"chunk[{n}].line_end={chunk.line_end}"


# ---------------------------------------------------------------------------
# chunk() — RST file (extension routing is symmetrical)
# ---------------------------------------------------------------------------


class TestChunkRstFile:
    def setup_method(self) -> None:
        self.chunker = TextChunker()
        self.ctx = _make_ctx(
            max_input_tokens=8192,
            file_path="docs/CHANGES.rst",
        )
        self.source = ".. note::\n\n   This is a RST file.\n"
        self.chunks = self.chunker.chunk(self.source, self.ctx)

    def test_produces_chunk_for_rst(self) -> None:
        assert len(self.chunks) == 1

    def test_chunk_type_is_text_for_rst(self) -> None:
        assert self.chunks[0].chunk_type == "text"

    def test_identity_window_zero_for_rst(self) -> None:
        assert self.chunks[0].identity == "window#0"


# ---------------------------------------------------------------------------
# chunk() — line numbering across repeated / duplicate content
# ---------------------------------------------------------------------------


class TestChunkRepeatedContentLineNumbers:
    """Duplicate-content windows must report ADVANCING line numbers.

    A naive ``source.find(window_text)`` always returns the FIRST occurrence,
    so every window of identical content would report line (1, 1). The chunker
    must thread a cumulative offset so each window resolves to its own location.
    Five identical paragraphs separated by blank lines yield five identical
    windows on lines 1, 3, 5, 7, 9 — the bug would report 1, 1, 1, 1, 1.
    """

    SMALL_CAP = 6  # tokens — one paragraph per window, whole doc does not fit

    def setup_method(self) -> None:
        self.chunker = TextChunker()
        self.ctx = _make_ctx(max_input_tokens=self.SMALL_CAP)
        # Five byte-identical paragraphs, blank-line separated. The splitter
        # keeps each paragraph intact, so every window has the SAME text.
        self.paragraph = "REPEATED PARAGRAPH."
        self.source = "\n\n".join([self.paragraph] * 5) + "\n"
        self.chunks = self.chunker.chunk(self.source, self.ctx)

    def test_produces_one_window_per_repeated_paragraph(self) -> None:
        assert len(self.chunks) == 5

    def test_window_contents_are_identical(self) -> None:
        # Precondition for the bug: all windows carry the same source_text, so
        # a first-occurrence lookup would collapse them all onto line 1.
        assert all(c.source_text == self.paragraph for c in self.chunks)

    def test_line_starts_are_strictly_increasing(self) -> None:
        """Each duplicate window's line_start must advance, not stick at 1."""
        line_starts = [c.line_start for c in self.chunks]
        for earlier, later in zip(line_starts, line_starts[1:]):
            assert later > earlier, f"line_start did not advance: {line_starts}"

    def test_line_starts_match_source_positions(self) -> None:
        """The Nth identical paragraph sits on its own 1-based line.

        Blank-line separation puts paragraphs on lines 1, 3, 5, 7, 9.
        """
        expected = [1, 3, 5, 7, 9]
        actual = [c.line_start for c in self.chunks]
        assert actual == expected

    def test_line_end_equals_line_start_for_single_line_windows(self) -> None:
        for chunk in self.chunks:
            assert chunk.line_end == chunk.line_start


# ---------------------------------------------------------------------------
# chunk() — token cap is strictly respected with injected counter
# ---------------------------------------------------------------------------


class TestChunkTokenCapInjected:
    """Verify the chunker calls ctx.count_tokens (not some internal estimate)."""

    def test_chunker_respects_small_injected_cap(self) -> None:
        chunker = TextChunker()
        # Use a 1-token-per-char counter and a cap of 50 tokens → windows ≤ 50 chars.
        token_cap = 50
        def count_tokens_by_char(text: str) -> int:
            """One token per character — used to make the cap strict."""
            return len(text)

        ctx = _make_ctx(
            max_input_tokens=token_cap,
            count_tokens=count_tokens_by_char,  # 1 token per char
        )
        # Source clearly exceeds the cap.
        source = "A" * (token_cap * 10)
        chunks = chunker.chunk(source, ctx)
        assert len(chunks) >= 2
        for n, chunk in enumerate(chunks):
            measured = len(chunk.source_text)  # same metric as injected counter
            assert measured <= token_cap, (
                f"chunk[{n}] source_text length {measured} exceeds cap {token_cap}"
            )

    def test_irreducible_single_char_does_not_recurse_forever(self) -> None:
        """A counter that reports a single char as over-cap must not hang.

        Pathological case: ``_fit_to_cap`` bisects, but a 1-char string can't be
        bisected — left="" is skipped and right=text re-enters with the same
        input, recursing forever. The chunker must emit the irreducible char as
        a bounded chunk instead of raising RecursionError.
        """
        chunker = TextChunker()

        def always_over_cap(text: str) -> int:
            """Report every non-empty string (even 1 char) as exceeding the cap."""
            return 999 if text else 0

        ctx = _make_ctx(max_input_tokens=1, count_tokens=always_over_cap)
        # A short multi-char source: every piece, down to 1 char, is "over cap".
        source = "abcd"
        chunks = chunker.chunk(source, ctx)  # must return, not RecursionError
        # Output is bounded (one chunk per surviving character, here 4).
        assert 0 < len(chunks) <= len(source)
        # The irreducible single-char windows are emitted verbatim.
        assert all(len(c.source_text) == 1 for c in chunks)
        assert "".join(c.source_text for c in chunks) == source
