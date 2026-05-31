"""Contract tests for ``lorescribe.stylesheet.StylesheetChunker``.

The contract pinned here:

* ``handles`` claims ``.css`` and ``.scss`` (case-insensitive), and nothing
  else.  A ``.min.css`` path is claimed by ``handles`` (extension is ``.css``),
  but the chunker **skips** it — ``chunk`` returns ``[]``.

* **Empty / whitespace-only source** → ``[]``.

* **Minified detection**: if the source's average line length exceeds the
  minified threshold (200 chars/line), ``chunk`` returns ``[]``.  This covers
  ``.min.css`` content AND any minified file not using a ``.min.css`` name.

* **Small file** (≤ 200 lines): a single ``Chunk`` is returned with
  ``identity="window#0"``, ``chunk_type="stylesheet"``, ``sub_ordinal=0``,
  ``line_start=1``, ``line_end=<n>``.

* **Large file** (> 200 lines): multiple overlapping windows are returned.
  Windows are ~200 lines with ~40-line overlap.  Each window carries a
  sequential ``identity`` (``window#0``, ``window#1``, …) and together they
  cover the file from line 1 to the last line.  The overlap guarantees the
  *start* of window N+1 is at most 200−40 = 160 lines after the *start* of
  window N.

* **Identity uniqueness + sequence**: identities are distinct and form an
  unbroken ``window#0, window#1, …`` sequence — no gaps, no duplicates.

* **Token cap**: every emitted chunk stays at or below ``ctx.max_input_tokens``
  as measured by ``ctx.count_tokens``.  A chunk that would exceed the cap must
  be shrunk (fewer lines per window) rather than emitted over-length.

* **Registry integration**: after registering ``StylesheetChunker`` with the
  ``ChunkerRegistry`` under ``"stylesheet"`` for ``[".css", ".scss"]``, the
  registry routes both extensions (case-insensitively) to the chunker and
  returns ``[]`` for unrelated extensions.
"""

from __future__ import annotations

import pytest
from lorescribe.models import Chunk, ChunkContext
from lorescribe.registry import ChunkerRegistry
from lorescribe.stylesheet import StylesheetChunker

from .conftest import (
    SAMPLE_FILE_PATH,
    SAMPLE_SLUG,
    VOYAGE4_MAX_INPUT_TOKENS,
    approx_token_count,
)

# ---------------------------------------------------------------------------
# Constants mirroring the chunker's design parameters (independent of impl).
# These are the *spec* numbers — tests compare against these, not against
# values read back from StylesheetChunker attributes.
# ---------------------------------------------------------------------------
WINDOW_SIZE: int = 200       # target lines per window
OVERLAP: int = 40            # overlap lines between adjacent windows
STEP: int = WINDOW_SIZE - OVERLAP  # 160 — start-of-window stride
MINIFIED_AVG_LINE_LEN: int = 200   # threshold for minified detection

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def chunker() -> StylesheetChunker:
    """A fresh StylesheetChunker instance."""
    return StylesheetChunker()


@pytest.fixture
def ctx() -> ChunkContext:
    """Realistic ChunkContext wired to the Voyage-4 cap and conftest counter."""
    return ChunkContext(
        slug=SAMPLE_SLUG,
        file_path=SAMPLE_FILE_PATH,
        count_tokens=approx_token_count,
        max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_css_source(n_lines: int, line_template: str = ".rule-{i} {{ color: red; }}") -> str:
    """Build a non-minified CSS source with exactly ``n_lines`` lines."""
    return "\n".join(line_template.format(i=i) for i in range(n_lines))


def _make_minified_source(n_lines: int = 5) -> str:
    """Build a source whose avg line length clearly exceeds the minified threshold."""
    long_line = "a" * (MINIFIED_AVG_LINE_LEN + 50)
    return "\n".join(long_line for _ in range(n_lines))


# ===========================================================================
# handles() — extension claims
# ===========================================================================

class TestStylesheetChunkerHandles:
    """``handles`` claims .css and .scss (case-insensitive), nothing else."""

    def test_handles_dot_css(self, chunker: StylesheetChunker) -> None:
        assert chunker.handles("theme/main.css") is True

    def test_handles_dot_scss(self, chunker: StylesheetChunker) -> None:
        assert chunker.handles("static/src/_vars.scss") is True

    def test_handles_uppercase_CSS(self, chunker: StylesheetChunker) -> None:
        # Case-insensitive: .CSS must be claimed.
        assert chunker.handles("THEME/MAIN.CSS") is True

    def test_handles_uppercase_SCSS(self, chunker: StylesheetChunker) -> None:
        assert chunker.handles("STATIC/SRC/_VARS.SCSS") is True

    def test_handles_min_css_by_extension(self, chunker: StylesheetChunker) -> None:
        # The extension of "app.min.css" is ".css"; handles() claims it.
        # chunk() will return [] due to the minified-filename rule — separate test.
        assert chunker.handles("dist/app.min.css") is True

    def test_does_not_handle_dot_py(self, chunker: StylesheetChunker) -> None:
        assert chunker.handles("src/models.py") is False

    def test_does_not_handle_dot_md(self, chunker: StylesheetChunker) -> None:
        assert chunker.handles("docs/readme.md") is False

    def test_does_not_handle_dot_js(self, chunker: StylesheetChunker) -> None:
        assert chunker.handles("src/app.js") is False

    def test_does_not_handle_dot_html(self, chunker: StylesheetChunker) -> None:
        assert chunker.handles("templates/index.html") is False

    def test_does_not_handle_no_extension(self, chunker: StylesheetChunker) -> None:
        assert chunker.handles("Makefile") is False


# ===========================================================================
# chunk() — skip / empty cases
# ===========================================================================

class TestStylesheetChunkerSkipsEmpty:
    """Empty and whitespace-only sources produce no chunks."""

    def test_empty_string_returns_empty_list(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk("", ctx)
        assert result == []

    def test_whitespace_only_source_returns_empty_list(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk("   \n\n\t\n  ", ctx)
        assert result == []


class TestStylesheetChunkerSkipsMinified:
    """Minified content (long average line) → []."""

    def test_min_css_filename_returns_empty_list(
        self, chunker: StylesheetChunker
    ) -> None:
        # A .min.css filename is a hard skip regardless of content.
        ctx = ChunkContext(
            slug=SAMPLE_SLUG,
            file_path="dist/app.min.css",
            count_tokens=approx_token_count,
            max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
        )
        source = _make_css_source(10)  # non-minified content
        result = chunker.chunk(source, ctx)
        assert result == []

    def test_long_avg_line_length_returns_empty_list(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        # Content with avg line len > MINIFIED_AVG_LINE_LEN is skipped.
        source = _make_minified_source(n_lines=10)
        result = chunker.chunk(source, ctx)
        assert result == []

    def test_borderline_avg_line_length_not_skipped(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        # A file exactly at the threshold (not above) must NOT be skipped.
        # Use avg length == MINIFIED_AVG_LINE_LEN (exactly 200) → not minified.
        line = "a" * MINIFIED_AVG_LINE_LEN  # exactly 200 chars
        source = "\n".join(line for _ in range(5))
        result = chunker.chunk(source, ctx)
        # This file is NOT minified by the "> threshold" rule; must return chunks.
        assert result != []


# ===========================================================================
# chunk() — small file (≤ WINDOW_SIZE lines)
# ===========================================================================

class TestStylesheetChunkerSmallFile:
    """A file with ≤ 200 lines produces a single chunk."""

    def test_single_line_file_produces_one_chunk(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = ".foo { color: blue; }"
        result = chunker.chunk(source, ctx)
        assert len(result) == 1

    def test_small_file_chunk_type_is_stylesheet(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(50)
        result = chunker.chunk(source, ctx)
        assert result[0].chunk_type == "stylesheet"

    def test_small_file_identity_is_window_zero(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(50)
        result = chunker.chunk(source, ctx)
        assert result[0].identity == "window#0"

    def test_small_file_sub_ordinal_is_zero(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(50)
        result = chunker.chunk(source, ctx)
        assert result[0].sub_ordinal == 0

    def test_small_file_line_start_is_one(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(50)
        result = chunker.chunk(source, ctx)
        assert result[0].line_start == 1

    def test_small_file_line_end_matches_line_count(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(50)
        result = chunker.chunk(source, ctx)
        # 50 lines → line_end == 50
        assert result[0].line_end == 50

    def test_exactly_window_size_file_produces_one_chunk(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(WINDOW_SIZE)
        result = chunker.chunk(source, ctx)
        assert len(result) == 1

    def test_small_file_source_text_equals_full_source(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(50)
        result = chunker.chunk(source, ctx)
        # The chunk's source_text must contain all 50 lines.
        assert result[0].source_text.strip() == source.strip()

    def test_small_scss_file_chunk_type_is_stylesheet(
        self, chunker: StylesheetChunker
    ) -> None:
        ctx = ChunkContext(
            slug=SAMPLE_SLUG,
            file_path="static/src/main.scss",
            count_tokens=approx_token_count,
            max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
        )
        source = "$primary: #fff;\nbody { color: $primary; }"
        result = chunker.chunk(source, ctx)
        assert len(result) == 1
        assert result[0].chunk_type == "stylesheet"


# ===========================================================================
# chunk() — large file (> WINDOW_SIZE lines): multi-window sliding
# ===========================================================================

class TestStylesheetChunkerLargeFile:
    """A file with > 200 lines produces multiple overlapping windows."""

    # Use a file clearly bigger than one window; 500 lines gives 3–4 windows.
    N_LINES: int = 500

    @pytest.fixture
    def large_source(self) -> str:
        return _make_css_source(self.N_LINES)

    @pytest.fixture
    def large_chunks(
        self,
        chunker: StylesheetChunker,
        ctx: ChunkContext,
        large_source: str,
    ) -> list[Chunk]:
        return chunker.chunk(large_source, ctx)

    def test_large_file_produces_multiple_chunks(self, large_chunks: list[Chunk]) -> None:
        assert len(large_chunks) > 1

    def test_large_file_first_chunk_type_is_stylesheet(self, large_chunks: list[Chunk]) -> None:
        assert all(ch.chunk_type == "stylesheet" for ch in large_chunks)

    def test_large_file_first_line_start_is_one(self, large_chunks: list[Chunk]) -> None:
        assert large_chunks[0].line_start == 1

    def test_large_file_last_chunk_covers_final_line(
        self, large_chunks: list[Chunk], large_source: str
    ) -> None:
        total_lines = len(large_source.splitlines())
        assert large_chunks[-1].line_end == total_lines

    def test_large_file_all_chunks_sub_ordinal_zero(self, large_chunks: list[Chunk]) -> None:
        # Each window is a distinct identity; sub_ordinal disambiguates siblings
        # of the SAME identity.  Since every window has a unique identity, all
        # sub_ordinals are 0.
        assert all(ch.sub_ordinal == 0 for ch in large_chunks)

    def test_large_file_window_stride_approximately_correct(
        self, large_chunks: list[Chunk]
    ) -> None:
        # The stride between window starts must be ≤ STEP (== WINDOW_SIZE - OVERLAP == 160).
        # This guarantees the overlap invariant.  A stride > STEP means we lost content.
        for previous, current in zip(large_chunks, large_chunks[1:]):
            stride = current.line_start - previous.line_start
            assert stride <= STEP, (
                f"stride {stride} between window#{large_chunks.index(previous)} "
                f"and window#{large_chunks.index(current)} exceeds max STEP {STEP}"
            )

    def test_large_file_adjacent_windows_overlap(self, large_chunks: list[Chunk]) -> None:
        # The end of window N must be >= the start of window N+1 (overlap).
        for previous, current in zip(large_chunks, large_chunks[1:]):
            assert previous.line_end >= current.line_start, (
                f"Gap between window ending at line {previous.line_end} and "
                f"next window starting at line {current.line_start}"
            )

    def test_large_file_window_size_approximately_correct(self, large_chunks: list[Chunk]) -> None:
        # Every non-final window should span ≤ WINDOW_SIZE lines.
        for chunk in large_chunks[:-1]:
            span = chunk.line_end - chunk.line_start + 1
            assert span <= WINDOW_SIZE, (
                f"Window span {span} exceeds WINDOW_SIZE {WINDOW_SIZE}"
            )

    def test_large_file_expected_number_of_windows(
        self, large_source: str, large_chunks: list[Chunk]
    ) -> None:
        # With N_LINES=500, STEP=160: windows start at 1, 161, 321, 481 → 4 windows.
        # ceil((500 - WINDOW_SIZE) / STEP) + 1 = ceil(300/160) + 1 = 2 + 1 = 3 or 4.
        # Independent calculation: number of starts until start >= total_lines.
        total_lines = len(large_source.splitlines())
        expected_starts = list(range(0, total_lines, STEP))
        # Adjust: last window may absorb the remainder.
        expected_count = len(expected_starts)
        # Allow ±1 for boundary handling of the final partial window.
        assert abs(len(large_chunks) - expected_count) <= 1, (
            f"Expected ~{expected_count} windows for {total_lines} lines "
            f"(STEP={STEP}), got {len(large_chunks)}"
        )


# ===========================================================================
# Identity uniqueness + sequential ordering
# ===========================================================================

class TestStylesheetChunkerIdentities:
    """Identities are distinct, sequential window#N labels starting from 0."""

    def test_small_file_identity_is_window_zero(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        result = chunker.chunk(_make_css_source(10), ctx)
        assert result[0].identity == "window#0"

    def test_large_file_identities_are_sequential_from_zero(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(500)
        chunks = chunker.chunk(source, ctx)
        for n, chunk in enumerate(chunks):
            assert chunk.identity == f"window#{n}", (
                f"Expected window#{n}, got {chunk.identity!r} at position {n}"
            )

    def test_large_file_identities_are_all_distinct(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(500)
        chunks = chunker.chunk(source, ctx)
        identities = [ch.identity for ch in chunks]
        assert len(identities) == len(set(identities)), (
            f"Duplicate identities found: {identities}"
        )

    def test_identities_have_no_gaps(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(500)
        chunks = chunker.chunk(source, ctx)
        expected = [f"window#{n}" for n in range(len(chunks))]
        actual = [ch.identity for ch in chunks]
        assert actual == expected, f"Gap or reorder in identities: {actual}"


# ===========================================================================
# Token cap enforcement
# ===========================================================================

class TestStylesheetChunkerTokenCap:
    """Every emitted chunk must be at or below ctx.max_input_tokens."""

    def test_small_file_within_token_cap(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(50)
        chunks = chunker.chunk(source, ctx)
        for chunk in chunks:
            token_count = ctx.count_tokens(chunk.source_text)
            assert token_count <= ctx.max_input_tokens, (
                f"Chunk {chunk.identity!r} has {token_count} tokens "
                f"(cap={ctx.max_input_tokens})"
            )

    def test_large_file_all_chunks_within_token_cap(
        self, chunker: StylesheetChunker, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(500)
        chunks = chunker.chunk(source, ctx)
        for chunk in chunks:
            token_count = ctx.count_tokens(chunk.source_text)
            assert token_count <= ctx.max_input_tokens, (
                f"Chunk {chunk.identity!r} has {token_count} tokens "
                f"(cap={ctx.max_input_tokens})"
            )

    def test_chunk_shrinks_when_window_exceeds_cap(
        self, chunker: StylesheetChunker
    ) -> None:
        """A window that would exceed a tight token cap must be shrunk."""
        # 8192-char line × 10 lines → rough token count ≈ 8192*10/4 = 20480.
        # Set a very tight cap so the 200-line window would exceed it.
        tight_cap = 50  # tokens  (much smaller than any full 200-line window)
        ctx_tight = ChunkContext(
            slug=SAMPLE_SLUG,
            file_path="src/large.css",
            count_tokens=approx_token_count,
            max_input_tokens=tight_cap,
        )
        # Source: 300 lines of moderately long CSS rules (long enough so any
        # 200-line window exceeds the tight cap of 50 tokens).
        long_value = "f" * 50
        line = f".rule-0 {{ background-color: #{long_value}; }}"
        source = "\n".join(line for _ in range(300))
        chunks = chunker.chunk(source, ctx_tight)
        # The shrunk windows must produce at least one embeddable chunk — a
        # vacuous empty list would mean the shrink logic silently dropped all
        # windows rather than emitting reduced-size ones.
        assert len(chunks) > 0, (
            f"Expected shrunken chunks for source with {len(source.splitlines())} lines "
            f"and tight cap of {tight_cap} tokens, but got []"
        )
        # Every produced chunk must be within the cap.
        for chunk in chunks:
            token_count = ctx_tight.count_tokens(chunk.source_text)
            assert token_count <= tight_cap, (
                f"Chunk {chunk.identity!r} has {token_count} tokens "
                f"(cap={tight_cap})"
            )


# ===========================================================================
# Registry integration
# ===========================================================================

class TestStylesheetChunkerRegistryIntegration:
    """StylesheetChunker integrates correctly with ChunkerRegistry."""

    @pytest.fixture
    def registry_with_stylesheet(self, chunker: StylesheetChunker) -> ChunkerRegistry:
        registry = ChunkerRegistry()
        registry.register("stylesheet", chunker, extensions=[".css", ".scss"])
        return registry

    @pytest.fixture
    def ctx(self) -> ChunkContext:
        return ChunkContext(
            slug=SAMPLE_SLUG,
            file_path=SAMPLE_FILE_PATH,
            count_tokens=approx_token_count,
            max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
        )

    def test_css_extension_routes_to_stylesheet_chunker(
        self, registry_with_stylesheet: ChunkerRegistry, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(10)
        chunks = registry_with_stylesheet.dispatch_file("theme/main.css", source, ctx)
        assert len(chunks) >= 1
        assert chunks[0].chunk_type == "stylesheet"

    def test_scss_extension_routes_to_stylesheet_chunker(
        self, registry_with_stylesheet: ChunkerRegistry, ctx: ChunkContext
    ) -> None:
        source = "$primary: #fff;\n.foo { color: $primary; }"
        chunks = registry_with_stylesheet.dispatch_file("src/main.scss", source, ctx)
        assert len(chunks) >= 1
        assert chunks[0].chunk_type == "stylesheet"

    def test_uppercase_CSS_extension_routes_to_stylesheet_chunker(
        self, registry_with_stylesheet: ChunkerRegistry, ctx: ChunkContext
    ) -> None:
        source = _make_css_source(10)
        chunks = registry_with_stylesheet.dispatch_file("THEME/MAIN.CSS", source, ctx)
        assert len(chunks) >= 1
        assert chunks[0].chunk_type == "stylesheet"

    def test_uppercase_SCSS_routes_to_stylesheet_chunker(
        self, registry_with_stylesheet: ChunkerRegistry, ctx: ChunkContext
    ) -> None:
        source = "$x: 1px;\n.y { margin: $x; }"
        chunks = registry_with_stylesheet.dispatch_file("SRC/MAIN.SCSS", source, ctx)
        assert len(chunks) >= 1
        assert chunks[0].chunk_type == "stylesheet"

    def test_js_extension_not_handled_by_stylesheet_registry(
        self, registry_with_stylesheet: ChunkerRegistry, ctx: ChunkContext
    ) -> None:
        chunks = registry_with_stylesheet.dispatch_file("src/app.js", "var x = 1;", ctx)
        assert chunks == []

    def test_dispatch_returns_empty_for_unknown_extension(
        self, registry_with_stylesheet: ChunkerRegistry, ctx: ChunkContext
    ) -> None:
        chunks = registry_with_stylesheet.dispatch_file("data/config.yaml", "key: val", ctx)
        assert chunks == []
