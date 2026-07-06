"""Contract tests for ``loremaster.store.query_text`` — the shared, store- and
memory-agnostic hybrid-search lexical-arm bounding mechanism (finding #69).

``SurrealStore.hybrid_search`` (chunk search, finding #66/#67) and
``LocalMemoryBackend._hybrid_search`` (memory recall, finding #69) both build a
lexical (BM25) predicate that can trip SurrealDB's own parser "expression
recursion depth limit" on a long/token-rich query. This module is the ONE
shared home for the two things that must never be independently
hand-copied again: the clause-budget-to-token-cap derivation
(:func:`max_query_tokens`) and the word-boundary text truncation
(:func:`truncate_at_word_boundary`). These tests are pure/unit — no live
server needed — and a separate pin (``TestSharedMechanismPin`` below) proves
BOTH consumers actually route through this module rather than re-defining
their own copies.
"""

from __future__ import annotations

import loremaster.memory.local as memory_local_module
import loremaster.store.surreal as surreal_module
from loremaster.memory.local import LocalMemoryBackend
from loremaster.store.query_text import (
    MAX_FULLTEXT_OR_CLAUSES,
    max_query_tokens,
    truncate_at_word_boundary,
)
from loremaster.store.surreal import SurrealStore
from loremaster.store.surreal_schema import CHUNK_FULLTEXT_FIELDS, MEMORY_FULLTEXT_FIELDS


class TestMaxQueryTokens:
    """The clause-budget-to-token-cap derivation — pure arithmetic, no server."""

    def test_three_field_consumer_matches_the_chunk_stores_measured_cap(self) -> None:
        # The chunk store's own live-measured-safe cap (finding #66/#67):
        # MAX_FULLTEXT_OR_CLAUSES=60 // 3 fields == 20.
        assert max_query_tokens(3) == 20

    def test_one_field_consumer_matches_memorys_measured_cap(self) -> None:
        # The memory recall arm's own live-measured-safe cap (finding #69):
        # MAX_FULLTEXT_OR_CLAUSES=60 // 1 field == 60.
        assert max_query_tokens(1) == 60

    def test_result_is_floored_at_one_even_for_a_huge_field_count(self) -> None:
        # A (hypothetical) consumer with more fields than the clause budget
        # must still get at least one token, never zero.
        assert max_query_tokens(1000) == 1

    def test_result_scales_inversely_with_field_count(self) -> None:
        assert max_query_tokens(2) == MAX_FULLTEXT_OR_CLAUSES // 2
        assert max_query_tokens(6) == MAX_FULLTEXT_OR_CLAUSES // 6


class TestTruncateAtWordBoundary:
    """The word-boundary text pre-truncation — pure/static, no live store needed.

    Mirrors ``test_surreal_store.py``'s ``TestTruncateAtWordBoundary`` (finding
    #66) exactly, now pinned directly against the SHARED function rather than
    the (now-delegating) ``SurrealStore`` staticmethod.
    """

    def test_text_at_or_under_the_cap_is_returned_unchanged(self) -> None:
        assert truncate_at_word_boundary("short query", 300) == "short query"
        exactly_at_cap = "x" * 10
        assert truncate_at_word_boundary(exactly_at_cap, 10) == exactly_at_cap

    def test_over_cap_backs_off_to_the_last_word_boundary_never_splitting_a_word(self) -> None:
        text = "one two three four five"
        # The cutoff (17) lands mid-"four" (spanning indices 14-17); the
        # result must back off to the LAST full word before it, "three".
        assert truncate_at_word_boundary(text, 17) == "one two three"

    def test_hostile_newline_and_tab_are_valid_word_boundaries(self) -> None:
        text = "alpha\tbeta\ncharlie delta epsilon zeta eta theta iota kappa"
        assert truncate_at_word_boundary(text, 20) == "alpha\tbeta\ncharlie"

    def test_single_giant_token_with_no_whitespace_falls_back_to_the_raw_slice(self) -> None:
        text = "x" * 500
        assert truncate_at_word_boundary(text, 300) == "x" * 300

    def test_punctuation_and_non_ascii_text_truncates_as_a_clean_prefix(self) -> None:
        text = (
            "Quelle était la décision, et comment le cycle « slate » "
            "est-il séquencé ? 日本語のテスト文字列もここに含まれています。"
        ) * 3
        truncated = truncate_at_word_boundary(text, 50)
        assert len(truncated) <= 50
        assert truncated == text[: len(truncated)]  # a genuine prefix, never mangled/reordered


class TestSharedMechanismPin:
    """Structural pins: BOTH ``SurrealStore`` (chunk search) and
    ``LocalMemoryBackend`` (memory recall) actually resolve to THIS module's
    helper + constant — never an independently hand-copied twin (finding #69's
    root cause). A future rename/reshape that re-introduces a third copy fails
    ONE of these, not a silent drift.
    """

    def test_surreal_store_truncate_is_the_shared_function_itself(self) -> None:
        # ``SurrealStore._truncate_at_word_boundary`` is bound directly to the
        # shared function (``staticmethod(truncate_at_word_boundary)``) — an
        # IDENTITY pin, not just "produces the same output".
        assert SurrealStore._truncate_at_word_boundary is truncate_at_word_boundary

    def test_memory_local_module_imports_the_same_truncate_function(self) -> None:
        assert memory_local_module.truncate_at_word_boundary is truncate_at_word_boundary

    def test_both_consumers_share_the_same_clause_budget_constant(self) -> None:
        assert surreal_module._MAX_FULLTEXT_OR_CLAUSES is MAX_FULLTEXT_OR_CLAUSES
        assert memory_local_module._MAX_FULLTEXT_OR_CLAUSES is MAX_FULLTEXT_OR_CLAUSES

    def test_each_consumers_token_cap_is_derived_from_its_own_field_count(self) -> None:
        # The MECHANISM is shared; the DERIVED token cap is per-consumer (own
        # field count) — a chunk-store value must never leak into memory's cap
        # or vice versa.
        assert surreal_module._MAX_QUERY_TOKENS == max_query_tokens(len(CHUNK_FULLTEXT_FIELDS))
        assert memory_local_module._MAX_QUERY_TOKENS == max_query_tokens(
            len(MEMORY_FULLTEXT_FIELDS)
        )
        assert surreal_module._MAX_QUERY_TOKENS != memory_local_module._MAX_QUERY_TOKENS

    def test_local_memory_backend_class_is_still_importable_and_unaffected(self) -> None:
        # A cheap sanity import-anchor: the sharing refactor must not break the
        # ordinary import path a caller uses.
        assert LocalMemoryBackend.__name__ == "LocalMemoryBackend"
