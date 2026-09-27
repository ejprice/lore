"""THE engine's TYPED rejection shapes for forged driver responses — ONE home (non-collected support).

*Scoped to SurrealDB 3.2.4 (the pinned engine), measured 2026-09-27 by ``contract-63c-i-a-a28c``
(``REPORT-contract-63c-i-a-a28c.md`` §A.1 / §A.2: ``probe_a28c.py``, ``probe_conflict.py``).*

Packet 63c amendment 36 makes the driver's DECISIONS read the engine's typed signal — the retry decision
reads ``details.kind == "TransactionConflict"``, the root-cause selector reads ``details.kind ==
"NotExecuted"``, the classifier reads the SDK kind first — never the text. A forged ``query_raw`` response
that carries only ``result`` text is therefore no longer the engine's shape: the engine NEVER sends a
per-statement ERR without its ``kind``. Every fixture that forges a rejection builds it HERE, so the typed
fields are added in ONE place (ONE IMPLEMENTATION) and a later engine change is a one-line fix.

This module deliberately imports NOTHING from ``loremaster`` that the checkpoint lacks (the kinds are ENGINE
facts, spelled as the engine spells them), so every file that uses it stays collectable on a build that
predates the typed decisions — its pins then fail for the ruled reason, never at import.

The text → kind pairing below is the engine's own, measured: the engine pairs each of these texts with exactly
one kind. It is a description of the WIRE, used only to reconstruct the fields a text-only fixture left out.
"""

from __future__ import annotations

from typing import Any

from surrealdb.errors import ErrorKind, QueryError

#: ``details.kind`` of the engine's retryable write-write conflict, on BOTH paths (``query()`` raises a
#: ``QueryError`` carrying it; ``query_raw`` stamps it on the refused COMMIT entry).
RETRYABLE_CONFLICT_KIND = "TransactionConflict"
#: ``details.kind`` of every cascade notice — a statement that never ran, and the refused COMMIT.
CASCADE_KIND = "NotExecuted"
#: The words the engine pairs with the retryable conflict (the COMMIT entry reads
#: ``"Cannot COMMIT: Transaction conflict: Resource busy. This transaction can be retried"``).
CONFLICT_WORDS = "can be retried"
#: The openings of the two cascade notices ("The query was not executed due to a failed / cancelled
#: transaction"; "Cannot COMMIT: the transaction was aborted due to a prior error").
CASCADE_OPENINGS = (
    "The query was not executed due to",
    "Cannot COMMIT: the transaction was aborted due to a prior error",
)
#: The engine's wrapping of a ``THROW`` (``kind: Thrown``).
THROW_OPENING = "An error occurred: "


def typed_err_entry(result_text: str) -> dict[str, Any]:
    """The engine's per-statement ERR for a MEASURED ``result_text``, with the ``kind`` / ``details`` the
    engine sends beside it: a conflict → ``Query`` + ``TransactionConflict``; a cascade notice → ``Query`` +
    ``NotExecuted``; a ``THROW`` → ``Thrown``; anything else (ASSERT, coercion, a UNIQUE-index collision) →
    ``Internal`` with no details (measured: those three are untyped)."""
    if CONFLICT_WORDS in result_text:
        return {
            "status": "ERR",
            "kind": "Query",
            "details": {"kind": RETRYABLE_CONFLICT_KIND},
            "result": result_text,
        }
    if result_text.startswith(CASCADE_OPENINGS):
        return {"status": "ERR", "kind": "Query", "details": {"kind": CASCADE_KIND}, "result": result_text}
    if result_text.startswith(THROW_OPENING):
        return {"status": "ERR", "kind": "Thrown", "result": result_text}
    return {"status": "ERR", "kind": "Internal", "result": result_text}


def typed_conflict_error(message: str, *, conflict_kind: str = RETRYABLE_CONFLICT_KIND) -> QueryError:
    """The exception a single-statement write-write conflict raises (``query()`` path)."""
    return QueryError(ErrorKind.QUERY, message, details={"kind": conflict_kind})
