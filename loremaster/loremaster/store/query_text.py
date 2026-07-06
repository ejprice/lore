"""Shared query-text bounding helpers for a hybrid search's lexical (BM25) arm.

Both :class:`~loremaster.store.surreal.SurrealStore` (chunk search) and
:class:`~loremaster.memory.local.LocalMemoryBackend` (memory recall) build a
hybrid (HNSW vector ⊕ BM25 FULLTEXT) SurrealQL statement whose lexical arm's
fulltext predicate can trip SurrealDB's own parser "expression recursion depth
limit" on a sufficiently long/token-rich query — the SAME engine mechanism,
reached from two DIFFERENT predicate shapes:

* the chunk store's is a flat, DISJUNCTIVE OR-chain over
  :data:`~loremaster.store.surreal_schema.CHUNK_FULLTEXT_FIELDS` (3 fields) —
  live-measured end-to-end at 39 tokens/117 OR-clauses OK, 40 tokens/120
  clauses REJECTED (finding #66/#67, ``scratchpad/probe_long_query_66*.py``);
* the memory recall arm's is a CONJUNCTIVE AND-chain over
  :data:`~loremaster.store.surreal_schema.MEMORY_FULLTEXT_FIELDS` (1 field) —
  live-measured end-to-end, independently, at 114 tokens/AND-clauses OK, 115
  REJECTED (finding #69, ``scratchpad/probe_long_query_69.py``).

Both ceilings land in the same ~114-120-clause neighbourhood even though the
predicate shape (AND vs. OR) and field count differ, which is why this module
shares the MECHANISM — the clause-budget-to-token-cap derivation and the
word-boundary truncation helper — rather than a single hardcoded token count:
a shared token-count constant would be wrong for at least one caller (3x too
permissive for the chunk store, or 3x too conservative for memory recall).
Each caller derives its OWN safe token cap from its OWN fulltext-field count
via :func:`max_query_tokens` — self-correcting if that field count ever
changes, and structurally unable to silently drift back into a
hand-maintained, independently-copied twin (finding #69's root cause: memory/
local.py had carried its OWN copy of the chunk store's OLD, pre-fix
constants, diverging the moment either side changed).
"""

from __future__ import annotations

# Roughly HALF the smaller of the two independently-measured, real end-to-end
# safe clause ceilings (chunk store: 117; memory recall: 114) — margin for
# engine-version drift, a future fulltext-field addition on EITHER consumer,
# or an active extra filter clause AND-wrapping its own term on top. Shared so
# a THIRD hybrid-search consumer never has to re-measure this from scratch.
MAX_FULLTEXT_OR_CLAUSES = 60


def max_query_tokens(fulltext_field_count: int) -> int:
    """The safe analyzed-token cap for a consumer with ``fulltext_field_count`` fields.

    Derived, not hardcoded, from :data:`MAX_FULLTEXT_OR_CLAUSES`: a consumer
    whose predicate contributes ``fulltext_field_count`` clauses per token
    (the chunk store's OR-chain matches every field per token; the memory
    recall AND-chain matches its single field per token) can safely allow
    this many tokens before its OWN predicate approaches the shared clause
    budget. Self-correcting: a future fulltext-field-count change on either
    consumer recomputes this automatically, rather than requiring a
    hand-edited constant that can silently drift out of sync.

    Args:
        fulltext_field_count: The number of fulltext-indexed fields the
            caller's predicate matches each token against.

    Returns:
        The token cap, floored at ``1`` so a consumer with a huge field count
        still gets at least one token rather than zero.
    """
    return max(1, MAX_FULLTEXT_OR_CLAUSES // fulltext_field_count)


def truncate_at_word_boundary(text: str, max_chars: int) -> str:
    """Truncate ``text`` to at most ``max_chars``, never splitting a word.

    Backs off to the last WHITESPACE run at or before the cutoff (space, tab,
    newline, or carriage return — a hostile multi-line query is still a valid
    word boundary), so a hybrid search's lexical arm always tokenizes whole
    words. A bare ``text[:max_chars]`` slice can chop the final word in half,
    feeding the analyzer a fragment the indexed text never actually contains.
    ``text`` at or under ``max_chars`` is returned unchanged — the common case
    for real (short) queries, which this truncation must never alter
    (finding #66's short-query regression contract).

    Args:
        text: The raw query text (the lexical arm's input only — a hybrid
            search's vector arm always embeds the caller's FULL text upstream
            of this call and is never truncated).
        max_chars: The truncation ceiling.

    Returns:
        ``text`` unchanged, or its longest whole-word prefix within
        ``max_chars`` — or, if the window contains no whitespace at all (one
        pathological giant token), the raw ``max_chars``-char slice as the
        best truncation available.
    """
    if len(text) <= max_chars:
        return text
    window = text[:max_chars]
    boundary = max(window.rfind(character) for character in (" ", "\t", "\n", "\r"))
    if boundary <= 0:
        return window
    return window[:boundary]
