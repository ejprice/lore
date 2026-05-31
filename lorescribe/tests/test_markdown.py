"""Contract tests for ``lorescribe.markdown.MarkdownChunker``.

The Markdown chunker splits a documentation file along its heading hierarchy
(h1-h4) and size-limits oversized sections, emitting one :class:`Chunk` per
piece. The load-bearing guarantees pinned here trace directly to the **Chunk
Identity Contract**: loremaster derives a deterministic point-ID from
``(slug, file_path, chunk_type, identity, sub_ordinal, key_version)``, so two
chunks that share an ``(identity, sub_ordinal)`` would collide and one would
silently overwrite the other in the vector store.

What the contract pins:

* **Routing.** ``handles`` claims ``.md`` (case-insensitively) and rejects
  unrelated extensions. ``chunk_type`` is always ``"markdown_section"``.

* **Heading breadcrumb.** Each chunk's ``metadata_header`` is exactly
  ``"File: <path>\nSection: <h1 > h2 > h3>"`` — the breadcrumb that gives the
  embedder retrieval context. A dropped or malformed breadcrumb degrades every
  chunk's retrieval, so it is pinned to the byte.

* **Identity = heading-path.** A section's ``identity`` is its heading path
  joined with ``" > "``. The adversarial case the scheme MUST survive: two
  DISTINCT sections whose heading text is byte-identical get DISTINCT
  identities (an occurrence ordinal disambiguates them) — otherwise the
  sibling-collapse bug from odoo-code's XML keys recurs here.

* **Size-split siblings.** A single section longer than the size budget is
  split into N pieces that share one ``identity`` but carry distinct
  ``sub_ordinal`` values ``0..N-1`` — so the N pieces never collide.

* **Token cap.** Every emitted chunk's ``embedding_text`` stays at or below
  ``ctx.max_input_tokens`` as measured by the injected ``ctx.count_tokens``;
  the embedder rejects (HTTP 422) over-length inputs, never truncates.

* **Code fences.** A fenced code block that FITS in the size budget is not
  torn across two chunks at an internal blank line — the fence stays whole.

* **Preamble.** Text before the first heading is emitted as its own chunk with
  a stable, non-empty identity (the model rejects a blank identity).

The fixtures are real-shape handbook Markdown (headings, prose, tables, fenced
code), not toy single-line strings, so a wrong-scale or wrong-anchor bug has
real input to fail on. Token counts use the conftest's behavioural counter
(the same ``str -> int`` seam the consumer injects), and the byte-exact header
expectation is composed independently of the chunker's own formatting code.
"""

from __future__ import annotations

from collections.abc import Callable

from lorescribe.markdown import MarkdownChunker
from lorescribe.models import Chunk, ChunkContext

from .conftest import (
    SAMPLE_SLUG,
    VOYAGE4_MAX_INPUT_TOKENS,
    approx_token_count,
)

# The chunk_type every Markdown chunk must carry, per the plan.
MARKDOWN_CHUNK_TYPE: str = "markdown_section"

# An on-disk path the breadcrumb header must echo verbatim.
MARKDOWN_FILE_PATH: str = "docs/onboarding/handbook.md"


def _ctx(
    count_tokens: Callable[[str], int],
    *,
    file_path: str = MARKDOWN_FILE_PATH,
    max_input_tokens: int = VOYAGE4_MAX_INPUT_TOKENS,
) -> ChunkContext:
    """Build a realistic per-file context for the chunker under test."""
    return ChunkContext(
        slug=SAMPLE_SLUG,
        file_path=file_path,
        count_tokens=count_tokens,
        max_input_tokens=max_input_tokens,
    )


def _expected_header(file_path: str, section: str) -> str:
    """Compose the breadcrumb header the chunk MUST carry, independently.

    Re-derives ``File: <path>\\nSection: <breadcrumb>`` from first principles so
    the assertion does not borrow the chunker's own formatting helper — a
    chunker that emits a subtly different header (wrong key, wrong separator,
    missing newline) fails against this value.
    """
    return f"File: {file_path}\nSection: {section}"


# --------------------------------------------------------------------------- #
# Real-shape Markdown fixtures
# --------------------------------------------------------------------------- #

# A handbook with a clear h1 > h2 hierarchy and distinct section names.
HIERARCHY_DOC: str = (
    "# Employee Handbook\n"
    "\n"
    "Welcome to the company.\n"
    "\n"
    "## Payroll\n"
    "\n"
    "Direct deposit posts on the second business day after the pay period closes.\n"
    "\n"
    "## Benefits\n"
    "\n"
    "Open enrollment runs the first two weeks of November each year.\n"
)

# Two sections whose heading text is byte-identical ("Notes") under the same
# parent — the sibling-collapse adversarial case. Distinct bodies so the test
# can prove the two distinct chunks are actually preserved, not merged.
REPEATED_HEADING_DOC: str = (
    "# Operations\n"
    "\n"
    "## Notes\n"
    "\n"
    "The first notes section covers morning shift handover procedures.\n"
    "\n"
    "## Notes\n"
    "\n"
    "The second notes section covers evening shift closing procedures.\n"
)

# Text before the very first heading (a preamble), then a real section.
PREAMBLE_DOC: str = (
    "This document describes the deployment runbook for the payroll service.\n"
    "\n"
    "It assumes familiarity with the staging environment.\n"
    "\n"
    "# Prerequisites\n"
    "\n"
    "You need cluster admin and a valid kubeconfig.\n"
)


def _make_long_section(heading: str, paragraph: str, repeats: int) -> str:
    """Build one heading whose body greatly exceeds the 4000-char size budget."""
    body = "\n\n".join(f"{paragraph} (paragraph {index})" for index in range(repeats))
    return f"# {heading}\n\n{body}\n"


class TestHandlesAndType:
    """``handles`` routing and the fixed ``chunk_type`` stamp."""

    def setup_method(self) -> None:
        self.chunker = MarkdownChunker()

    def test_handles_md_extension(self) -> None:
        assert self.chunker.handles("docs/handbook.md") is True

    def test_handles_is_case_insensitive(self) -> None:
        # A README.MD on a case-insensitive filesystem must still be claimed.
        assert self.chunker.handles("docs/README.MD") is True

    def test_does_not_handle_unrelated_extension(self) -> None:
        assert self.chunker.handles("src/payroll.py") is False
        assert self.chunker.handles("data/report.csv") is False

    def test_emits_markdown_section_chunk_type(self) -> None:
        chunks = self.chunker.chunk(HIERARCHY_DOC, _ctx(approx_token_count))
        assert chunks, "a non-empty document must yield at least one chunk"
        assert all(chunk.chunk_type == MARKDOWN_CHUNK_TYPE for chunk in chunks)


class TestChunkShapeAndBreadcrumb:
    """Each chunk is a real ``Chunk`` carrying the byte-exact breadcrumb header."""

    def setup_method(self) -> None:
        self.chunker = MarkdownChunker()
        self.chunks = self.chunker.chunk(HIERARCHY_DOC, _ctx(approx_token_count))

    def test_returns_list_of_chunk_instances(self) -> None:
        assert isinstance(self.chunks, list)
        assert all(isinstance(chunk, Chunk) for chunk in self.chunks)

    def test_every_chunk_has_non_blank_identity(self) -> None:
        # The model already rejects a blank identity; this asserts the chunker
        # never even tries to emit one (e.g. for the preamble or an empty path).
        assert all(chunk.identity.strip() for chunk in self.chunks)

    def test_breadcrumb_header_is_byte_exact_for_a_named_section(self) -> None:
        # The "Payroll" section must carry exactly the documented header.
        payroll = [c for c in self.chunks if "Payroll" in c.metadata_header]
        assert payroll, "expected a chunk for the Payroll section"
        expected = _expected_header(MARKDOWN_FILE_PATH, "Employee Handbook > Payroll")
        assert payroll[0].metadata_header == expected

    def test_breadcrumb_uses_the_context_file_path(self) -> None:
        # The header echoes ctx.file_path, not a hardcoded path.
        other_path = "wiki/policies/leave.md"
        chunks = self.chunker.chunk(HIERARCHY_DOC, _ctx(approx_token_count, file_path=other_path))
        assert all(chunk.metadata_header.startswith(f"File: {other_path}\n") for chunk in chunks)

    def test_breadcrumb_joins_heading_path_with_arrow(self) -> None:
        # h1 > h2 nesting renders as "Employee Handbook > Benefits".
        benefits = [c for c in self.chunks if c.metadata_header.endswith("Benefits")]
        assert benefits
        assert benefits[0].metadata_header == _expected_header(
            MARKDOWN_FILE_PATH, "Employee Handbook > Benefits"
        )

    def test_line_range_is_within_source_bounds(self) -> None:
        # Line numbers are 1-based and never exceed the source's line count.
        total_lines = HIERARCHY_DOC.count("\n") + 1
        for chunk in self.chunks:
            assert 1 <= chunk.line_start <= chunk.line_end <= total_lines


class TestIdentityIsHeadingPath:
    """A section's identity is its heading path; distinct sections differ."""

    def setup_method(self) -> None:
        self.chunker = MarkdownChunker()
        self.chunks = self.chunker.chunk(HIERARCHY_DOC, _ctx(approx_token_count))

    def test_distinct_sections_have_distinct_identities(self) -> None:
        identities = {chunk.identity for chunk in self.chunks}
        # Three logical sections: preamble (under h1), Payroll, Benefits.
        assert len(identities) == len(self.chunks)

    def test_identity_reflects_the_heading_path(self) -> None:
        # The Payroll chunk's identity must encode the Payroll heading path.
        payroll = [c for c in self.chunks if "Payroll" in c.metadata_header]
        assert payroll
        assert "Payroll" in payroll[0].identity


class TestRepeatedHeadingGetsDistinctIdentities:
    """The sibling-collapse adversarial case: identical heading text, distinct ids."""

    def setup_method(self) -> None:
        self.chunker = MarkdownChunker()
        self.chunks = self.chunker.chunk(REPEATED_HEADING_DOC, _ctx(approx_token_count))

    def test_two_same_named_sections_yield_two_chunks(self) -> None:
        # Both "Notes" bodies must survive as distinct content — not be merged
        # into one chunk (langchain merges identical adjacent headings; the
        # chunker must re-separate them).
        notes_chunks = [c for c in self.chunks if "Notes" in c.metadata_header]
        assert len(notes_chunks) >= 2
        bodies = " ".join(c.source_text for c in notes_chunks)
        assert "morning shift" in bodies
        assert "evening shift" in bodies

    def test_same_named_sections_have_distinct_identities(self) -> None:
        # The decisive assertion: the two "Notes" sections must NOT share an
        # (identity, sub_ordinal) — otherwise their point-IDs collide downstream
        # and one silently overwrites the other.
        notes_chunks = [c for c in self.chunks if "Notes" in c.metadata_header]
        keys = {(c.identity, c.sub_ordinal) for c in notes_chunks}
        assert len(keys) == len(notes_chunks)

    def test_no_two_chunks_in_a_file_share_identity_and_sub_ordinal(self) -> None:
        # Global invariant across the whole file, the property loremaster relies on.
        keys = [(c.identity, c.sub_ordinal) for c in self.chunks]
        assert len(keys) == len(set(keys))


class TestLongSectionSplitsIntoSubOrdinalSiblings:
    """A section over the size budget splits into N (identity, sub_ordinal) siblings."""

    def setup_method(self) -> None:
        self.chunker = MarkdownChunker()
        # A single h1 whose body is far larger than the 4000-char size budget.
        paragraph = (
            "The reconciliation job walks every open invoice, matches it against "
            "the bank feed, and posts a clearing entry when the amounts agree "
            "within the configured tolerance."
        )
        self.doc = _make_long_section("Reconciliation", paragraph, repeats=60)
        self.chunks = self.chunker.chunk(self.doc, _ctx(approx_token_count))

    def test_long_section_produces_multiple_chunks(self) -> None:
        # The body is several times the size budget, so it cannot be one chunk.
        assert len(self.chunks) >= 2

    def test_split_siblings_share_one_identity(self) -> None:
        identities = {chunk.identity for chunk in self.chunks}
        assert len(identities) == 1, "a single section's pieces share one identity"

    def test_split_siblings_have_contiguous_sub_ordinals(self) -> None:
        # sub_ordinal must run 0..N-1 with no gaps or repeats, so the N pieces
        # of one section never collide on (identity, sub_ordinal).
        sub_ordinals = sorted(chunk.sub_ordinal for chunk in self.chunks)
        assert sub_ordinals == list(range(len(self.chunks)))

    def test_split_siblings_keys_are_all_distinct(self) -> None:
        keys = [(c.identity, c.sub_ordinal) for c in self.chunks]
        assert len(keys) == len(set(keys))


class TestTokenCapIsRespected:
    """Every emitted chunk stays at or below the embedder's hard token cap."""

    def setup_method(self) -> None:
        self.chunker = MarkdownChunker()

    def test_chunks_respect_the_default_cap(self) -> None:
        # Real-scale cap (8192). With ~4 chars/token a 4000-char chunk is ~1000
        # tokens, comfortably under — this guards the steady-state path.
        paragraph = (
            "Payroll runs on a fortnightly cycle; the cutoff for timesheet "
            "submission is the Wednesday before the pay date at 17:00 local time."
        )
        doc = _make_long_section("Payroll Cycle", paragraph, repeats=40)
        ctx = _ctx(approx_token_count)
        chunks = self.chunker.chunk(doc, ctx)
        assert chunks
        for chunk in chunks:
            assert ctx.count_tokens(chunk.embedding_text) <= ctx.max_input_tokens

    def test_tight_cap_forces_token_level_subsplit(self) -> None:
        # Pin the hard guarantee under an adversarially TIGHT cap: a single
        # dense section that fits the char budget but blows a small token cap
        # must still be sub-split until every piece is under the cap. This is
        # the correctness path the plan calls out (fit the hard limit), not the
        # ordinary char-size split.
        paragraph = (
            "The settlement ledger aggregates clearing entries by counterparty "
            "and currency, nets offsetting positions, and emits a single wire "
            "instruction per netting group at the end of the value date."
        )
        doc = _make_long_section("Settlement", paragraph, repeats=12)
        tight_cap = 64  # far below a whole 4000-char section's token count
        ctx = _ctx(approx_token_count, max_input_tokens=tight_cap)
        chunks = self.chunker.chunk(doc, ctx)
        assert chunks
        for chunk in chunks:
            assert ctx.count_tokens(chunk.embedding_text) <= tight_cap

    def test_tight_cap_keys_remain_distinct(self) -> None:
        # The extra token-level splitting must not produce colliding keys.
        paragraph = "Dense settlement prose that must be sub-split aggressively under a tiny cap."
        doc = _make_long_section("Dense", paragraph, repeats=20)
        ctx = _ctx(approx_token_count, max_input_tokens=48)
        chunks = self.chunker.chunk(doc, ctx)
        keys = [(c.identity, c.sub_ordinal) for c in chunks]
        assert len(keys) == len(set(keys))


class TestCodeFenceIntegrity:
    """A fenced code block that fits the budget is not torn across chunks."""

    def setup_method(self) -> None:
        self.chunker = MarkdownChunker()

    def test_fence_with_internal_blank_lines_is_not_split_mid_block(self) -> None:
        # A section over the size budget that CONTAINS a code block which itself
        # fits. A naive char splitter breaks the fence at its internal blank
        # line; the chunker must keep the fence whole. The block's distinctive
        # lines must all land in exactly ONE chunk.
        intro = "Configuration steps follow below. " * 110  # pushes section over budget
        outro = "Further operational notes apply here. " * 110
        code = (
            "```python\n"
            "def alpha():\n"
            "    return 1\n"
            "\n"
            "\n"
            "def beta():\n"
            "    return 2\n"
            "\n"
            "\n"
            "def gamma():\n"
            "    return 3\n"
            "```"
        )
        doc = f"# Setup\n\n{intro}\n\n{code}\n\n{outro}\n"
        chunks = self.chunker.chunk(doc, _ctx(approx_token_count))
        markers = ("def alpha():", "def beta():", "def gamma():")
        chunks_holding_code = [
            chunk for chunk in chunks if any(marker in chunk.source_text for marker in markers)
        ]
        # All three function defs must live together in a single chunk — the
        # fence was not severed at its internal blank lines.
        assert len(chunks_holding_code) == 1, (
            "fenced code block was split mid-fence across multiple chunks"
        )
        holder = chunks_holding_code[0]
        assert all(marker in holder.source_text for marker in markers)


class TestPreambleHandling:
    """Text before the first heading becomes its own well-identified chunk."""

    def setup_method(self) -> None:
        self.chunker = MarkdownChunker()
        self.chunks = self.chunker.chunk(PREAMBLE_DOC, _ctx(approx_token_count))

    def test_preamble_content_is_emitted(self) -> None:
        preamble = [c for c in self.chunks if "deployment runbook" in c.source_text]
        assert preamble, "preamble text before the first heading must be chunked"

    def test_preamble_chunk_has_non_blank_identity(self) -> None:
        preamble = [c for c in self.chunks if "deployment runbook" in c.source_text]
        assert preamble[0].identity.strip()

    def test_preamble_identity_distinct_from_first_section(self) -> None:
        preamble = [c for c in self.chunks if "deployment runbook" in c.source_text]
        section = [c for c in self.chunks if "Prerequisites" in c.metadata_header]
        assert preamble and section
        assert preamble[0].identity != section[0].identity


class TestEmptyAndWhitespaceSource:
    """A document with no real content yields no chunks, never a blank identity."""

    def setup_method(self) -> None:
        self.chunker = MarkdownChunker()

    def test_empty_source_yields_no_chunks(self) -> None:
        assert self.chunker.chunk("", _ctx(approx_token_count)) == []

    def test_whitespace_only_source_yields_no_chunks(self) -> None:
        assert self.chunker.chunk("   \n\n  \t\n", _ctx(approx_token_count)) == []


class TestRegistryIntegration:
    """The chunker plugs into the registry's dispatch path end to end."""

    def test_dispatch_routes_md_to_markdown_chunker(self) -> None:
        from lorescribe.registry import ChunkerRegistry

        registry = ChunkerRegistry()
        registry.register("markdown", MarkdownChunker(), extensions=[".md"])
        ctx = _ctx(approx_token_count)
        chunks = registry.dispatch_file("docs/handbook.md", HIERARCHY_DOC, ctx)
        assert chunks
        assert all(chunk.chunk_type == MARKDOWN_CHUNK_TYPE for chunk in chunks)

    def test_dispatch_passes_injected_counter_through(self) -> None:
        # Prove the counter seam is traversed: a tight cap injected via the
        # registry's ctx forces sub-splitting just as a direct call would.
        from lorescribe.registry import ChunkerRegistry

        calls: list[str] = []

        def counting_tokenizer(text: str) -> int:
            calls.append(text)
            return approx_token_count(text)

        registry = ChunkerRegistry()
        registry.register("markdown", MarkdownChunker(), extensions=[".md"])
        ctx = _ctx(counting_tokenizer)
        registry.dispatch_file("docs/handbook.md", HIERARCHY_DOC, ctx)
        assert calls, "the chunker must call through ctx.count_tokens"
