"""Shared low-level SurrealDB store internals — the single audited home for the
two failure-handling concerns that :class:`~loremaster.store.surreal.SurrealStore`
and :class:`~loremaster.index.surreal_manifest.SurrealManifest` both depend on.

Both classes own ONE signed-in, stateful SurrealDB connection reached over the
async SDK, and both had (until this module) independently-evolving copies of the
same two seams. They are extracted here — now that a SECOND real caller exists
(``replace_file`` joining ``replace``) — so the behaviour can never drift between
them again:

1. **Transport-vs-domain error classification** (:func:`is_connection_error`).
   A single-statement ``query()`` raises a :class:`surrealdb.errors.SurrealError`
   for BOTH a genuine transport failure AND a domain/schema rejection, and the
   two demand OPPOSITE handling:

   * a transport failure — the socket died mid-life and the SDK silently
     reconnected *unauthenticated*, surfacing as a ``NotAllowed`` server error
     (verified live on 3.1.5), or a raw ``OSError`` / ``WebSocketException`` —
     must drop the cached handle so the next call transparently reconnects (the
     mid-life self-heal);
   * a domain/schema rejection — an ``ASSERT`` violation or a type-coercion
     failure, surfacing as an ``Internal`` server error (verified live) — must
     NOT throw away a perfectly healthy connection, and must reach the caller as
     a :class:`SurrealStoreError`, not a :class:`SurrealConnectionError`.

   The distinguishing signal is the SDK's structured :attr:`ServerError.kind`:
   only the auth/connection kinds (:data:`_CONNECTION_ERROR_KINDS`) are
   transport; every other kind is a domain rejection.

2. **The per-statement transaction check** (:func:`execute_transaction`). The
   SDK's plain ``query()`` only inspects the FIRST statement's ``status`` before
   deciding whether to raise, so a LATER statement's rejection inside a
   ``BEGIN … COMMIT`` rolls the whole transaction back server-side while
   ``query()`` returns ``None`` with no exception at all (confirmed live). The
   executor uses the lower-level ``query_raw`` and inspects EVERY statement's
   ``status`` itself, raising the moment any statement in the transaction
   failed — so neither caller can observe the SDK's "silent success". A
   RETRYABLE optimistic-concurrency conflict (two genuinely concurrent writers
   racing the same row) is retried with a fresh, full-jittered exponential
   backoff on EVERY attempt (finding #102: a purely deterministic backoff let
   concurrent racers wake in lockstep and re-collide), bounded by a wall-clock
   deadline plus an attempt-count backstop, and raises the typed
   :class:`TxnContentionExhaustedError` on exhaustion; every OTHER rejection (a
   domain/``ASSERT`` violation) surfaces immediately as :class:`SurrealStoreError`,
   never retried, since retrying it would never succeed.

The connection-lifecycle vocabulary (:class:`SurrealStoreError`,
:class:`SurrealConnectionError`, :data:`_CONNECTION_ERRORS`,
:data:`_SurrealConnection`) lives here rather than in ``surreal.py`` so both the
executor and the classifier can raise/catch it without an import cycle;
``surreal.py`` re-exports it so the historical ``from loremaster.store.surreal
import …`` seam every caller (and test) uses keeps working unchanged.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from surrealdb import (
    AsyncEmbeddedSurrealConnection,
    AsyncHttpSurrealConnection,
    AsyncWsSurrealConnection,
)
from surrealdb.errors import ErrorKind, ServerError, SurrealError
from websockets.exceptions import WebSocketException

# The server-side home for the FULL engine detail a rolled-back transaction
# carries (see :func:`execute_transaction` / :func:`_failed_statements`): the
# raised :class:`SurrealStoreError` NEVER carries this raw text (ledger #31 —
# an ASSERT/coercion rejection can echo a bound VALUE back verbatim, and that
# text will flow to MCP clients in P8); an operator can always correlate a
# classified exception back to the full detail here via this module's logger.
logger = logging.getLogger(__name__)


class SurrealStoreError(RuntimeError):
    """Base class for every error the SurrealDB store/manifest layer raises."""


class SurrealConnectionError(SurrealStoreError):
    """The store could not reach or authenticate to the SurrealDB server."""


class TxnParamCollisionError(SurrealStoreError):
    """Two composed fragments bound the SAME parameter name.

    Raised by :func:`compose` the moment a later fragment's params dict carries
    a key an earlier fragment already bound: a naive merge would silently
    overwrite one producer's value with another's, corrupting the transaction.
    Every producer namespaces its params with a distinct prefix precisely so
    this never happens in practice — this typed error is the LOUD guard that
    turns a namespacing bug into an immediate, diagnosable failure instead of a
    silent data corruption.
    """


class TxnEnvelopeViolationError(SurrealStoreError):
    """A fragment statement smuggles its own transaction-envelope control.

    Raised by :func:`compose` when a fragment's statement text carries a bare
    ``BEGIN``/``COMMIT`` keyword (case-insensitive, word-boundary aware — an
    identifier that merely CONTAINS ``begin``/``commit`` as a substring, e.g. a
    ``commit_hash`` audit column, is ordinary and never flagged) or an internal
    statement separator (a ``;`` beyond the single, optional trailing
    terminator a builder may author). A fragment is composable precisely
    because it owns none of the envelope compose() adds exactly once; either
    poison shape would corrupt that guarantee: a smuggled ``COMMIT`` closes the
    atomic block early (everything composed after it would run OUTSIDE the
    intended transaction); a smuggled ``BEGIN`` opens a second, nested one; a
    bare internal ``;`` splits one declared statement into several UNTRACKED
    ones, silently undercounting what :data:`TXN_STATEMENT_HARD_CAP` and
    :data:`TXN_STATEMENT_WARN_THRESHOLD` count against.
    """


class TxnContentionExhaustedError(SurrealStoreError):
    """A genuine write-write conflict outlived :func:`execute_transaction`'s
    retry budget (finding #102).

    Raised only when :func:`_rollback_verdict` classifies the LATEST rollback
    as a retryable conflict (the engine's own ``"can be retried"`` marker) AND
    the attempt ceiling or wall-clock deadline has been reached — never for a
    domain/``ASSERT`` rejection, which always raises the plain
    :class:`SurrealStoreError` immediately, unretried (see
    :func:`_rollback_verdict`). Subclasses :class:`SurrealStoreError` so every
    existing ``except SurrealStoreError`` keeps catching it unchanged; a caller
    that must NOT treat exhausted contention as a lost compare-and-set (the
    guarded-CAS handlers in :mod:`loremaster.findings` / :mod:`loremaster.tasks`)
    opts in by catching THIS type FIRST, above its own ``SurrealStoreError``
    handler.

    Attributes:
        attempts: The number of transaction attempts actually made — read off
            the loop that made them, never a docstring's promise (finding #102's
            own root cause: a "12 x 5 = 60 attempts" claim about a loop that had
            never executed a single retry).
        elapsed_seconds: The wall-clock time spent across all of them.
    """

    def __init__(self, message: str, *, attempts: int, elapsed_seconds: float) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.elapsed_seconds = elapsed_seconds


# The body-statement count above which :meth:`SurrealStore.apply` emits a
# WARNING rather than a DEBUG telemetry record. A per-file transaction that
# spans a file's chunks + body + graph + manifest sits far below this; crossing
# it means an accidentally-huge batch (thousands of statements in one
# ``BEGIN … COMMIT``) that should be visible in the logs before it strains the
# engine. A generous ceiling — high enough never to warn on a legitimately large
# file, low enough to catch a runaway batch.
TXN_STATEMENT_WARN_THRESHOLD = 800

# The composed transaction's HARD body-statement ceiling — the write-path
# analogue of the read path's ``_MAX_HYBRID_K`` clamp (``store/surreal.py``): a
# DISTINCT, HIGHER bound than :data:`TXN_STATEMENT_WARN_THRESHOLD` (crossing
# the WARN threshold only logs and still composes; crossing THIS one refuses
# outright). Defense-in-depth against a pathological single file (e.g. a
# 100k-tiny-generated-function source) producing one multi-hundred-thousand-
# statement transaction that would strain the SHARED server — refused at BUILD
# time in :func:`compose`, so :meth:`SurrealStore.apply` (which calls
# ``compose`` first) never even reaches ``execute_transaction``.
TXN_STATEMENT_HARD_CAP = 5000

# The single ``BEGIN … COMMIT`` envelope :func:`compose` wraps the merged
# fragment bodies in. A fragment carries NONE of its own (that is what makes it
# composable); the envelope is added exactly once, here.
_TXN_BEGIN = "BEGIN;\n"
_TXN_COMMIT = "\nCOMMIT;"

# The per-statement terminator :func:`_normalise_statement` guarantees, so a
# builder may author its statements with or without a trailing ``;`` and compose
# still emits one well-formed, semicolon-separated body.
_STATEMENT_TERMINATOR = ";"

# The envelope-integrity keyword scan (see :class:`TxnEnvelopeViolationError`):
# a bare ``BEGIN``/``COMMIT`` token, case-insensitive (the engine treats
# SurrealQL keywords case-insensitively even though every builder here emits
# uppercase). ``\b`` word boundaries make this identifier-safe: ``commit_hash``
# has no boundary between ``commit`` and the following ``_`` (a word
# character), so it never matches.
_BEGIN_COMMIT_KEYWORD_PATTERN = re.compile(r"\b(BEGIN|COMMIT)\b", re.IGNORECASE)


@dataclass(frozen=True)
class TxnFragment:
    """One producer's composable slice of a larger transaction.

    A fragment is an ORDERED list of SurrealQL ``statements`` plus the
    ``params`` those statements bind — and, crucially, it carries NO
    ``BEGIN``/``COMMIT`` of its own. That omission is what lets any set of
    fragments (a file's chunks, its verbatim body, its manifest row, its
    code-graph nodes/edges) merge into ONE transaction via :func:`compose`,
    which adds the single envelope exactly once. Each producer namespaces its
    ``params`` keys with a distinct prefix so the merged param dict never
    collides (see :class:`TxnParamCollisionError`).

    Attributes:
        statements: The ordered SurrealQL statements, without any transaction
            envelope; a builder may include or omit the trailing ``;`` — compose
            normalises it.
        params: The bound parameters these statements reference, producer-
            namespaced so they survive the merge without clobbering a sibling.
    """

    statements: Sequence[str]
    params: Mapping[str, Any]


def _normalise_statement(statement: str) -> str:
    """Return ``statement`` with exactly one trailing ``;`` and no surrounding whitespace.

    A fragment builder may author a statement with or without its terminator;
    normalising here means :func:`compose` always emits a uniform,
    semicolon-separated body regardless of the producer's local style.
    """
    trimmed = statement.strip().rstrip(_STATEMENT_TERMINATOR).rstrip()
    return f"{trimmed}{_STATEMENT_TERMINATOR}"


def _assert_envelope_integrity(statement: str) -> None:
    """Refuse a fragment statement that could split or close compose()'s envelope.

    Checked on every RAW fragment statement, before :func:`_normalise_statement`
    runs. A single, optional trailing terminator is the ONLY ``;`` a legitimate
    one-statement fragment ever carries — anything beyond that (an internal
    separator) or a bare ``BEGIN``/``COMMIT`` keyword means the fragment is
    smuggling more than the one statement it declared. See
    :class:`TxnEnvelopeViolationError`.

    Raises:
        TxnEnvelopeViolationError: ``statement`` carries an internal statement
            separator or a bare ``BEGIN``/``COMMIT`` keyword.
    """
    stripped = statement.strip()
    # Peel off exactly one optional trailing terminator (the ordinary shape a
    # builder may author) before checking for an INTERNAL separator, so a
    # single trailing ``;`` is never mistaken for smuggled statements.
    body = (
        stripped[: -len(_STATEMENT_TERMINATOR)]
        if stripped.endswith(_STATEMENT_TERMINATOR)
        else stripped
    )
    if _STATEMENT_TERMINATOR in body:
        raise TxnEnvelopeViolationError(
            f"fragment statement contains an internal statement separator "
            f"({_STATEMENT_TERMINATOR!r}) beyond its single trailing terminator, "
            f"which would split it into untracked statements: {statement!r}"
        )
    if _BEGIN_COMMIT_KEYWORD_PATTERN.search(stripped):
        raise TxnEnvelopeViolationError(
            f"fragment statement contains a bare BEGIN/COMMIT keyword, which "
            f"would close or nest compose()'s single transaction envelope: "
            f"{statement!r}"
        )


def compose(*fragments: TxnFragment) -> tuple[str, dict[str, Any]]:
    """Merge ``fragments`` into ONE ``BEGIN … COMMIT`` transaction.

    Concatenates the fragments' statements in the order given (statement order
    is load-bearing — a producer's DELETE-then-UPSERT must stay ordered, and the
    fragment order the caller chose must stay stable) inside a single
    transaction envelope, and unions their params into one dict.

    Every statement is checked for envelope integrity (see
    :class:`TxnEnvelopeViolationError`) before it is normalised, and the
    composed body-statement count is checked against
    :data:`TXN_STATEMENT_HARD_CAP` before the envelope text is assembled — both
    BUILD-time refusals, so :meth:`~loremaster.store.surreal.SurrealStore.apply`
    (which calls this first) never reaches ``execute_transaction`` for either.

    Args:
        *fragments: The producer fragments to compose (at least one).

    Returns:
        ``(statement_text, merged_params)`` — the full multi-statement
        ``BEGIN … COMMIT`` SurrealQL text and the merged bound parameters, ready
        to hand straight to :func:`execute_transaction`.

    Raises:
        ValueError: No fragments were given — composing nothing is a caller bug
            (an empty apply names no work), never a silently-empty transaction.
        TxnParamCollisionError: Two fragments bound the same param name; a naive
            merge would silently drop one value, so compose refuses loudly.
        TxnEnvelopeViolationError: A fragment statement smuggles its own
            ``BEGIN``/``COMMIT`` or an internal statement separator.
        SurrealStoreError: The composed body would exceed
            :data:`TXN_STATEMENT_HARD_CAP` statements.
    """
    if not fragments:
        raise ValueError(
            "compose() requires at least one fragment; composing nothing would "
            "emit a BEGIN … COMMIT that commits no work"
        )
    merged_params: dict[str, Any] = {}
    body: list[str] = []
    for fragment in fragments:
        for key, value in fragment.params.items():
            if key in merged_params:
                raise TxnParamCollisionError(
                    f"parameter {key!r} bound by more than one fragment — a naive "
                    f"merge would silently overwrite one producer's value; every "
                    f"producer must namespace its params with a distinct prefix"
                )
            merged_params[key] = value
        for statement in fragment.statements:
            _assert_envelope_integrity(statement)
            body.append(_normalise_statement(statement))
    if len(body) > TXN_STATEMENT_HARD_CAP:
        raise SurrealStoreError(
            f"composed transaction has {len(body)} statements, exceeding the "
            f"hard cap of {TXN_STATEMENT_HARD_CAP} statements per transaction — "
            f"refused before anything was sent to the server"
        )
    statement_text = _TXN_BEGIN + "\n".join(body) + _TXN_COMMIT
    return statement_text, merged_params



# ``AsyncSurreal`` is a factory returning one of these by URL scheme; this alias
# is exactly its return union so a cached connection type-checks under strict.
_SurrealConnection = (
    AsyncEmbeddedSurrealConnection | AsyncHttpSurrealConnection | AsyncWsSurrealConnection
)

# Connection/transport failures that mean "the server is unreachable or refused
# us" — the broad set an operation's ``except`` must catch so a domain rejection
# is never left unwrapped. ``OSError`` covers ``ConnectionRefusedError``;
# ``SurrealError`` covers the SDK's server/auth errors AND an ``ASSERT``/coercion
# rejection (:func:`is_connection_error` then separates the two); ``WebSocket
# Exception`` covers a broken/closed WS transport.
_CONNECTION_ERRORS = (OSError, SurrealError, WebSocketException)

# The structured :attr:`ServerError.kind` values that mean "this is a transport /
# session-loss problem, not a rejection of the write we sent". ``NotAllowed``
# covers both a bad-password sign-in AND a mid-life socket drop the SDK silently
# reconnected *unauthenticated* (the reconnected session has no token, so the
# next statement runs as anonymous and is refused); ``Connection`` covers the
# SDK's explicit connection-unavailable kind. Every OTHER kind (``Internal`` /
# ``Query`` / ``Validation`` / …) is a domain rejection of the statement itself.
_CONNECTION_ERROR_KINDS = frozenset({ErrorKind.NOT_ALLOWED, ErrorKind.CONNECTION})

# The exact substring the engine appends to a rolled-back transaction's final
# statement when the rollback was caused by optimistic-concurrency contention
# between two genuinely concurrent writers on the SAME row — verified live:
# "Cannot COMMIT: Transaction conflict: Resource busy. This transaction can be
# retried". This is the ONLY signal 3.1.5 exposes to distinguish a retryable
# write-write race (safe, and expected, to retry transparently) from every other
# kind of rolled-back transaction (e.g. a domain/``ASSERT`` violation, which must
# never be retried and must surface to the caller immediately) — neither the
# per-statement ``kind`` nor ``details.kind`` differ between the two cases, only
# this message text does.
_RETRYABLE_CONFLICT_MARKER = "can be retried"

# The two LIVE substrings (captured against spike-surreal, SurrealDB 3.1.5 —
# ``scratchpad/contract-v5/capture_engine.py``) a rolled-back transaction's
# NON-substantive entries carry — never a genuine root cause, always noise
# generated by the rollback itself (audit-102 B3): the engine retroactively
# stamps every statement BEFORE the offender ``ERR`` too, as a non-execution
# notice ("The query was not executed due to a failed transaction" / "…due to
# a cancelled transaction"), and every statement's COMMIT is refused the same
# way ("Cannot COMMIT: the transaction was aborted due to a prior error"). A
# domain root-cause selector must skip both, at BOTH ends of the entry list.
_CASCADE_NOT_EXECUTED_MARKER = "was not executed due to"
_CASCADE_COMMIT_ABORTED_MARKER = "aborted due to a prior error"
_DOMAIN_CASCADE_MARKERS = (_CASCADE_NOT_EXECUTED_MARKER, _CASCADE_COMMIT_ABORTED_MARKER)

# NOT a ladder tuned for 2-way contention any more (finding #102: it was never
# re-measured as callers grew to N-way — the finding mint funnels EVERY
# concurrent reporter through ONE row). Left importable deliberately:
# ``briefs.py`` IMPORTS this and derives its OWN, unrelated single-statement
# mint budget from it
# (``_BRIEF_MINT_MAX_ATTEMPTS = _BRIEF_PUBLISH_MAX_ATTEMPTS * _MAX_TXN_CONFLICT_
# ATTEMPTS``) — deleting it would ``ImportError`` the whole package; repointing
# it at the repaired policy's own ceiling would silently re-tune briefs'
# measured budget. The repaired policy below gets its OWN, freshly-measured
# backoff/deadline/ceiling constants instead of touching this one (see
# ``TestBriefsInheritedConflictBudgetIsNotSilentlyRepointed`` in
# ``test_surreal_store.py``).
#
# LOAD-BEARING A SECOND WAY since audit-102 B1: this is also
# :func:`execute_transaction`'s own guaranteed attempt FLOOR — not a tuned
# number but the pre-#102 behavioural contract itself. The deadline may only
# cut retries once this many attempts have run; a transaction slower than the
# deadline is still guaranteed this many tries, exactly as every caller was
# guaranteed before finding #102 introduced the deadline at all.
_MAX_TXN_CONFLICT_ATTEMPTS = 5

# --- the repaired conflict-retry policy (finding #102) -----------------------
#
# Per-attempt FULL JITTER, redrawn from the process PRNG on EVERY attempt
# (never cached, never derived from the contended row's identity or a coarse
# clock — the exact defect class that let N racers wake in lockstep and
# re-collide), exponential with a cap, under a wall-clock DEADLINE with a
# generous attempt count as a structural runaway backstop. Replaces the old
# deterministic ``BACKOFF * (attempt + 1)`` ladder above, whose complete
# absence of jitter is finding #102's root cause: every racer slept the
# IDENTICAL duration and woke together, attempt after attempt, until the
# budget drained (measured: 6 of 10 solo 8-way runs failed).
#
# MEASURED (committed survey probe: scripts/survey_txn_contention_102.py;
# reproduce with ``cd loremaster && uv run python
# ../scripts/survey_txn_contention_102.py``), against spike-surreal, N in
# {2, 8, 16, 32} GENUINELY CONCURRENT racers x 50 rounds each (n = N*50
# observations per row), driving the REAL ``FindingLedger._report_fragment``
# shape — the exact statements ``report()`` sends in production — through this
# repaired seam:
#
#   N=2   n=100   attempts p50=1 p90=2 p99=2   latency p50=0.010s p90=0.012s p99=0.020s
#   N=8   n=400   attempts p50=2 p90=3 p99=4   latency p50=0.011s p90=0.021s p99=0.032s
#   N=16  n=800   attempts p50=2 p90=3 p99=4   latency p50=0.011s p90=0.019s p99=0.047s
#   N=32  n=1600  attempts p50=2 p90=3 p99=5   latency p50=0.011s p90=0.021s p99=0.045s
#
# (full JSON receipt in ``REPORT-builder-102.md``). ZERO exhaustions across all
# 2900 observed mints; the attempt distribution at every N was a narrow spread
# (max observed attempt count 6, at N=32) with no multi-modal clustering near
# the ceiling — no lockstep signature. BASE/CAP are therefore left at the
# design's own starting values, endorsed rather than merely assumed.
_TXN_CONFLICT_BACKOFF_BASE_SECONDS = 0.005
_TXN_CONFLICT_BACKOFF_CAP_SECONDS = 0.1
# >= 10x the measured N=32 p99 (0.045s) — the design's stated rule, cleared
# with a wide margin (2.0s is ~44x that p99, not a bare 10x). The measured p99
# came in far under the design's 0.7s prediction — contention resolves in tens
# of milliseconds even at 32-way — so a much smaller deadline would also clear
# the rule, but 2.0s is kept as a generous, still-cheap ceiling: an MCP client
# waiting on a mint is parked for at most ~2s even under pathological
# contention nothing in this survey observed.
_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS = 2.0
# NOT a tuned constant — a structural runaway backstop against a pathological
# run of near-zero early draws spinning inside the deadline, never reached by
# any measured run above; logged when hit (see the exhaustion raise below).
_TXN_CONFLICT_ATTEMPT_CEILING = 64

# The per-statement status the engine stamps on a rejected statement.
_ERR_STATUS = "ERR"

# The short, engine-derived error CLASSES the raised (public) message may name —
# ledger #31: informative enough for an operator/caller to triage WITHOUT ever
# repeating the raw engine text (which can carry an interpolated bound VALUE).
# Checked in this order by :func:`_classify_engine_error`, most-specific first.
_ERROR_CLASS_RETRYABLE_CONFLICT = "retryable conflict"
_ERROR_CLASS_ASSERT_VIOLATION = "assert violation"
_ERROR_CLASS_FIELD_COERCION = "field coercion"
# Finding #66: SurrealDB 3.1.5's own "expression recursion depth limit" on a
# deeply-chained boolean expression — the shape ``store.surreal``'s BM25
# OR-predicate collides with once it exceeds its measured-safe clause budget
# (see ``store.surreal._MAX_FULLTEXT_OR_CLAUSES``). A TEACHING label (what
# happened + what to do), not just a generic one, since the store's own
# truncation should make this vanishingly rare in practice — a caller seeing it
# anyway knows immediately what to retry with, rather than "see the server log".
_ERROR_CLASS_QUERY_TOO_COMPLEX = "query too complex — reduce or shorten the search terms"
_ERROR_CLASS_UNSPECIFIED = "unspecified rejection"

# The substrings (verified live — see the module docstring's ``ASSERT``/coercion
# grounding, and ``TestDomainRejectionErrorType`` / ``TestReplaceFile`` in
# ``test_surreal_store.py``) that :func:`_classify_engine_error` keys off of. A
# case-insensitive membership check, never a value-bearing capture group — the
# classifier only ever RETURNS one of the fixed labels above, never a slice of
# the raw text itself.
_ASSERT_VIOLATION_MARKER = "must conform to"
_FIELD_COERCION_MARKER = "coerce"
# The live-verified substring of SurrealDB 3.1.5's own rejection text: "Parse
# error: Exceeded expression recursion depth limit ... this expression nests or
# chains operators too deeply" (finding #66, scratchpad/probe_long_query_66b.py
# — the raw, pre-classification ``ValidationError`` text captured against
# spike-surreal). Matched case-insensitively, same as the other markers.
_QUERY_RECURSION_DEPTH_MARKER = "recursion depth"

# The correlation hint appended to every classified rollback message, so an
# operator holding only the (deliberately generic) exception text can still
# find the full engine detail :func:`execute_transaction` logs server-side.
_SERVER_LOG_HINT = "see the server log for the full engine detail"


def _classify_engine_error(raw_result: object) -> str:
    """Classify a rolled-back statement's raw engine result into a short,
    GENERIC label — never a slice of ``raw_result`` itself.

    This is the hygiene boundary (ledger #31): callers of
    :func:`execute_transaction` see only the label this returns; the full
    ``raw_result`` text (which can carry an interpolated bound value, e.g. an
    ``ASSERT`` rejection echoing the offending value back verbatim) is logged
    server-side and never returned here.

    Args:
        raw_result: The failed statement's raw ``result`` field from the
            engine's ``query_raw`` response (usually a ``str``, but handled
            defensively via ``str()`` since the engine's shape is not a
            contract this module controls).

    Returns:
        One of the ``_ERROR_CLASS_*`` labels — the retryable-conflict marker is
        checked FIRST because the single-statement ``_query`` callers (which
        classify a caught exception's full text directly through this same
        function — e.g. ``briefs.py``'s version mint, not yet migrated to the
        typed error) can hand it text that DOES carry the marker. On the transactional
        :func:`execute_transaction` path this function is only ever called
        with a DOMAIN root cause — :func:`_rollback_verdict` never routes
        conflict-marked text here, since a genuine conflict is either retried
        internally or raised as the typed :class:`TxnContentionExhaustedError`
        without ever reaching this classifier (finding #102) — so the marker
        branch is unreachable from that caller; it stays first because it
        remains load-bearing for the other one.
    """
    text = str(raw_result)
    if _RETRYABLE_CONFLICT_MARKER in text:
        return _ERROR_CLASS_RETRYABLE_CONFLICT
    lowered = text.lower()
    if _ASSERT_VIOLATION_MARKER in lowered:
        return _ERROR_CLASS_ASSERT_VIOLATION
    if _FIELD_COERCION_MARKER in lowered:
        return _ERROR_CLASS_FIELD_COERCION
    if _QUERY_RECURSION_DEPTH_MARKER in lowered:
        return _ERROR_CLASS_QUERY_TOO_COMPLEX
    return _ERROR_CLASS_UNSPECIFIED


@dataclass(frozen=True)
class _FailedStatement:
    """One ``ERR``-status statement from a rolled-back transaction's raw response.

    Carries the statement's POSITION in the raw response (``index``, 0-based)
    alongside the engine's raw per-statement result (``raw_result``) — the
    latter is kept STRICTLY internal to this module (logged server-side,
    consulted by :func:`_is_retryable_conflict`) and must never be
    interpolated into a :class:`SurrealStoreError` message; see
    :func:`_classify_engine_error`.
    """

    index: int
    raw_result: Any


# Callback aliases the two owners hand :func:`execute_transaction`: how to obtain
# the live connection (their own lazy ``_ensure_connection``) and how to self-heal
# a dropped one (null the cached handle + close the dead socket).
AcquireConnection = Callable[[], Awaitable[_SurrealConnection]]
DropConnection = Callable[[_SurrealConnection], Awaitable[None]]


def is_connection_error(error: BaseException) -> bool:
    """Classify a caught operation error as transport (``True``) or domain (``False``).

    Called from the single-statement ``_query`` seam of both the store and the
    manifest to decide whether a failure is a connection-class fault (drop the
    cached handle and self-heal on the next call, surfaced as
    :class:`SurrealConnectionError`) or a domain/schema rejection of the write
    itself (keep the healthy connection, surfaced as :class:`SurrealStoreError`).

    Args:
        error: A caught member of :data:`_CONNECTION_ERRORS`.

    Returns:
        ``True`` if the error is a transport/socket/auth failure; ``False`` if it
        is a domain/schema/type rejection of the statement.
    """
    if isinstance(error, ServerError):
        # A structured server error: only the auth/connection kinds are
        # transport; every other kind (``Internal``/``Query``/``Validation``/…)
        # is the engine rejecting the write we sent — a domain rejection.
        return error.kind in _CONNECTION_ERROR_KINDS
    # A raw ``OSError`` / ``WebSocketException`` (a dead or refused socket), or a
    # non-``ServerError`` SDK error such as ``ConnectionUnavailableError``, is
    # always transport-class.
    return True


def _rollback_verdict(
    failed_statements: list[_FailedStatement],
) -> tuple[bool, _FailedStatement]:
    """ONE semantic verdict over a rolled-back transaction's failed statements —
    consumed by BOTH the retry decision and the final raise, in
    :func:`execute_transaction`, so they can never read different witnesses and
    silently disagree again.

    This is finding #102's precise root cause, fixed structurally rather than
    by convention: finding #93 legitimately changed the raise site's root-cause
    pick from ``[-1]`` to ``[0]``, which silently flipped the classified label
    for an EXHAUSTED conflict (the live engine puts its retry marker only on
    the LAST entry) — and a distant ``except`` body that had been
    string-matching that label stopped matching, killing a retry loop with zero
    test signal. Folding both decisions through one function makes that
    divergence structurally impossible: there is only one place either of them
    can read from.

    Args:
        failed_statements: Every ``ERR``-status entry from the LATEST attempt's
            response, in engine order.

    Returns:
        ``(is_conflict, root_cause)``:

        * ``is_conflict`` — the UNCHANGED :func:`_is_retryable_conflict` scan
          (an ``any()`` over every entry — it must see all of them, since the
          engine's marker can ride any position). Checked FIRST: a "Cannot
          COMMIT: Transaction conflict … can be retried" entry is claimed here
          before the domain branch's cascade markers could ever misread it —
          ordering is load-bearing.
        * ``root_cause`` — for a conflict, the FIRST entry whose raw text
          carries :data:`_RETRYABLE_CONFLICT_MARKER` (the entry that actually
          drove the retry decision); for a domain rejection,
          :func:`_domain_root_cause` (audit-102 B3: finding #93's premise —
          "everything before the first ``ERR`` succeeded" — is FALSE on the
          live engine, so ``failed_statements[0]`` names a cascade notice, not
          the cause).

        Selecting by POSITION is refused outright, at both ends: the engine
        writes DOMAIN root causes FIRST (cascade after) but CONFLICT evidence
        LAST (non-execution noise before), and even within the domain branch
        pre-offender statements are ALSO stamped cascade-``ERR`` — neither
        ``[0]`` nor ``[-1]`` is correct for any shape here; only a SEMANTIC
        (marker-seeking) selector is.
    """
    is_conflict = _is_retryable_conflict(failed_statements)
    if is_conflict:
        root_cause = next(
            failed
            for failed in failed_statements
            if _RETRYABLE_CONFLICT_MARKER in str(failed.raw_result)
        )
    else:
        root_cause = _domain_root_cause(failed_statements)
    return is_conflict, root_cause


def _domain_root_cause(failed_statements: list[_FailedStatement]) -> _FailedStatement:
    """Select the SUBSTANTIVE entry from a non-conflict rollback's failed
    statements (audit-102 B3, design addendum Ruling 3) — never a positional
    pick.

    The live engine writes a domain rollback as: zero or more cascade
    ``ERR`` entries BEFORE the offender ("the query was not executed due to a
    failed/cancelled transaction" — statements that never actually ran),
    THEN the offender's own substantive rejection, THEN more cascade entries
    AFTER it, ending in the marker-less "Cannot COMMIT: the transaction was
    aborted due to a prior error". Neither end of that list is ever the
    cause: ``[0]`` is cascade (finding #93's false premise), ``[-1]`` is the
    COMMIT abort.

    Returns:
        The FIRST entry whose text is non-empty and carries no
        :data:`_DOMAIN_CASCADE_MARKERS` marker. When every entry is cascade
        (no substantive rejection exists anywhere — degenerate but real),
        degrades to the LAST entry: the engine's own final word, and the
        honest thing to report when nothing substantive was ever said.
    """
    for failed in failed_statements:
        text = str(failed.raw_result)
        if text and not _is_domain_cascade_notice(text):
            return failed
    return failed_statements[-1]


def _is_domain_cascade_notice(text: str) -> bool:
    """Whether ``text`` is rollback NOISE (a non-execution or COMMIT-abort
    notice) rather than a substantive engine rejection — see
    :data:`_DOMAIN_CASCADE_MARKERS`.
    """
    return any(marker in text for marker in _DOMAIN_CASCADE_MARKERS)


def _txn_conflict_backoff_seconds(attempt_number: int) -> float:
    """Full-jitter exponential backoff for the ``attempt_number``-th retry
    (1-based: the sleep taken right after the FIRST failed attempt is
    ``attempt_number == 1``).

    Redrawn from the process PRNG on EVERY call — never cached, never derived
    from the contended row's identity or a coarse clock (the exact defect class
    that let concurrent racers desynchronise only by luck, or not at all) — so
    two racers colliding on the same row draw INDEPENDENT durations instead of
    waking together and re-colliding, attempt after attempt, until the budget
    drains. ``uniform(0, window)`` is FULL jitter (the draw reaches down to
    zero), not jitter around a floor, so one racer can retry almost immediately
    while another waits — the asymmetry that actually breaks a tie.

    Args:
        attempt_number: The 1-based count of attempts made so far (the window
            grows exponentially with it, capped).

    Returns:
        A backoff duration in seconds, uniformly drawn from
        ``[0, min(CAP, BASE * 2**(attempt_number - 1)))``.
    """
    window = min(
        _TXN_CONFLICT_BACKOFF_CAP_SECONDS,
        _TXN_CONFLICT_BACKOFF_BASE_SECONDS * (2 ** (attempt_number - 1)),
    )
    return random.uniform(0, window)


def _log_rollback(
    root_cause: _FailedStatement,
    statement_count: int,
    failed_statements: list[_FailedStatement],
) -> None:
    """Log the FULL engine detail server-side (ledger #31: the raised exception
    never carries it) for a rolled-back transaction — shared by
    :func:`execute_transaction`'s domain-rejection raise and its
    contention-exhausted raise, so both carry the identical receipt shape.
    """
    logger.error(
        "store.transaction.rolled_back",
        extra={
            "statement_index": root_cause.index,
            "statement_count": statement_count,
            "status": _ERR_STATUS,
            "engine_result": root_cause.raw_result,
            "failed_statements": [
                {"index": failed.index, "engine_result": failed.raw_result}
                for failed in failed_statements
            ],
        },
    )


async def execute_transaction(
    statement: str,
    params: dict[str, Any],
    *,
    acquire: AcquireConnection,
    drop: DropConnection,
    url: str,
    deadline_seconds: float | None = None,
) -> None:
    """Run a multi-statement ``BEGIN … COMMIT`` and verify EVERY statement.

    The counter to the SDK's own ``query()`` gap: ``query()`` only checks the
    FIRST statement's ``status`` before deciding whether to raise, so a later
    rejection inside a transaction rolls back server-side while ``query()``
    returns ``None`` with no exception at all. Each attempt runs three linear
    steps: :func:`_txn_query_raw` (self-healing ``query_raw`` + the SDK's own
    RPC-error check), :func:`_failed_statements` (extract the per-statement
    ``ERR`` entries), then :func:`_rollback_verdict` (the ONE decision both the
    retry and the eventual raise read from).

    A genuine transport/auth failure (the socket died, or the server is
    unreachable) self-heals via ``drop`` and surfaces as
    :class:`SurrealConnectionError` — see :func:`_txn_query_raw`.

    A per-statement engine rejection (the rollback case) splits two ways:

    * A DOMAIN rejection (e.g. an ``ASSERT`` violation) is never retried —
      retrying it would never succeed — and raises :class:`SurrealStoreError`
      immediately, naming the root cause :func:`_rollback_verdict` selects: the
      FIRST failed entry whose text is non-empty and carries no cascade marker
      (audit-102 B3: finding #93's premise — "everything before the first
      ``ERR`` succeeded" — is FALSE on the live engine, which retroactively
      stamps pre-offender statements ``ERR`` too, as non-execution cascade
      notices; a rollback with no substantive entry anywhere degrades to the
      LAST entry, the engine's marker-less "Cannot COMMIT: the transaction was
      aborted due to a prior error").
    * A RETRYABLE optimistic-concurrency conflict
      (:data:`_RETRYABLE_CONFLICT_MARKER`) is retried with a fresh,
      full-jittered exponential backoff (:func:`_txn_conflict_backoff_seconds`)
      redrawn on EVERY attempt, so concurrent racers on the same row
      desynchronise instead of waking together in lockstep — finding #102's
      root cause was a purely deterministic backoff, identical for every
      racer. Retrying is bounded by a generous attempt-count backstop
      (:data:`_TXN_CONFLICT_ATTEMPT_CEILING`), OR by a wall-clock
      ``deadline_seconds`` (or the module default when ``None``) ONCE the
      attempt floor (:data:`_MAX_TXN_CONFLICT_ATTEMPTS` — the pre-#102
      five-attempt guarantee every caller had regardless of wall time) has
      been met (audit-102 B1: a deadline shorter than a single attempt must
      never veto that attempt's own retry budget); exhausting either raises
      the TYPED :class:`TxnContentionExhaustedError` (never a plain
      :class:`SurrealStoreError` — a caller that must not mistake exhausted
      contention for a lost compare-and-set opts in by catching the typed
      error first, see :mod:`loremaster.findings` / :mod:`loremaster.tasks`).

    Both raise paths share ONE classification witness (:func:`_rollback_verdict`)
    so the retry decision and the final report can never again read different
    entries and silently disagree — the exact way finding #93's legitimate
    root-cause fix silently broke finding #102's dead backstop.

    Error-message hygiene (ledger #31): the engine's raw per-statement result
    can echo a bound VALUE back verbatim (e.g. an ``ASSERT`` rejection quoting
    the offending value) — text that will flow to MCP clients in P8. The FULL
    detail is logged server-side (:func:`_log_rollback`, structured: the root
    cause's statement index, status and raw engine result, plus every failed
    statement's index and raw result) immediately before EITHER raise; the
    raised exception carries only a CLASSIFIED, generic summary plus a "see the
    server log" correlation hint — never the raw text itself.

    Args:
        statement: The full multi-statement ``BEGIN … COMMIT`` SurrealQL text.
        params: The bound parameters for the whole transaction.
        acquire: Returns the owner's live connection (its ``_ensure_connection``).
        drop: Self-heals the owner on a transport failure — nulls the cached
            handle and closes the dead socket so the next call reconnects.
        url: The owner's RPC URL, for the error messages.
        deadline_seconds: The wall-clock budget for conflict retries, honoured
            only once :data:`_MAX_TXN_CONFLICT_ATTEMPTS` attempts have run
            (audit-102 B1 — a budget shorter than one attempt can never veto
            that attempt's own retry). ``None`` (the default — every caller in
            this repo today) uses :data:`_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS`.

    Raises:
        SurrealConnectionError: The server is unreachable or the socket died.
        SurrealStoreError: A non-retryable (domain) statement failure — the
            transaction was rolled back and retrying it would never succeed.
            The message is classified/generic; the full engine detail is
            logged server-side (see above).
        TxnContentionExhaustedError: A genuine write-write conflict outlived
            the deadline/attempt budget. Subclasses :class:`SurrealStoreError`.
    """
    deadline = (
        _TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS if deadline_seconds is None else deadline_seconds
    )
    started = time.monotonic()
    attempt = 0
    while True:
        response = await _txn_query_raw(statement, params, acquire=acquire, drop=drop, url=url)
        attempt += 1
        failed_statements = _failed_statements(response)
        statement_count = len(response.get("result") or [])
        if not failed_statements:
            return
        is_conflict, root_cause = _rollback_verdict(failed_statements)
        elapsed = time.monotonic() - started
        if not is_conflict:
            error_class = _classify_engine_error(root_cause.raw_result)
            _log_rollback(root_cause, statement_count, failed_statements)
            raise SurrealStoreError(
                f"SurrealDB transaction failed and was rolled back: statement "
                f"{root_cause.index + 1} of {statement_count} was rejected "
                f"({error_class}); {_SERVER_LOG_HINT}"
            )
        # B1 (audit-102): the deadline may bound retries; it may never veto the
        # FIRST one. A wall-clock budget smaller than a single attempt's own
        # execution time is incoherent as a retry budget — the caller's own
        # attempt duration is not the retry policy's to ration. Give up on the
        # CEILING alone (the structural runaway backstop), or on the deadline
        # ONLY once the attempt floor (the pre-#102 five-attempt guarantee,
        # ``_MAX_TXN_CONFLICT_ATTEMPTS``) has been met — restoring, BY
        # CONSTRUCTION, the same non-regression guarantee every caller had
        # before finding #102 introduced the deadline at all. Zero new
        # constants (design addendum, Ruling 1).
        if attempt >= _TXN_CONFLICT_ATTEMPT_CEILING or (
            elapsed >= deadline and attempt >= _MAX_TXN_CONFLICT_ATTEMPTS
        ):
            _log_rollback(root_cause, statement_count, failed_statements)
            raise TxnContentionExhaustedError(
                f"SurrealDB transaction gave up after {attempt} attempts over "
                f"{elapsed:.3f}s ({_ERROR_CLASS_RETRYABLE_CONFLICT}); {_SERVER_LOG_HINT}",
                attempts=attempt,
                elapsed_seconds=elapsed,
            )
        await asyncio.sleep(_txn_conflict_backoff_seconds(attempt))


async def _txn_query_raw(
    statement: str,
    params: dict[str, Any],
    *,
    acquire: AcquireConnection,
    drop: DropConnection,
    url: str,
) -> dict[str, Any]:
    """Run ``statement`` via ``query_raw``, self-healing on a connection failure.

    Mirrors the single-statement ``_query`` self-heal seam, but calls the SDK's
    lower-level ``query_raw`` (which skips the SDK's own per-statement error
    check) so :func:`_failed_statements` can run the per-statement inspection
    itself. ``check_response_for_error`` is re-run here (rather than hand-parsing
    the ``error`` field) so it reuses the SDK's own error-to-exception mapping:
    an RPC-level failure — e.g. the socket silently reconnected unauthenticated
    after a mid-life drop, surfacing as an "Anonymous access not allowed"
    response rather than a raised exception — is caught by the SAME
    :data:`_CONNECTION_ERRORS` branch below as a genuine transport failure, and
    self-heals the same way.

    The ``except`` also catches a raw ``KeyError``: probe-verified live (a
    socket drop with a query in flight), the installed SDK's OWN response
    routing raises ``builtins.KeyError(<request-uuid>)`` from EITHER await
    above — never a domain rejection (a per-statement ``ERR`` never raises
    here at all; see :func:`_failed_statements`), so it is always a transport
    fault and always self-heals via ``drop``. The ``except`` wraps ONLY these
    two SDK calls — never our own dict-indexing code — so this can never
    misclassify a ``KeyError`` raised by application logic.

    Raises:
        SurrealConnectionError: The server is unreachable or the socket died.
    """
    connection = await acquire()
    try:
        response = await connection.query_raw(statement, params)
        connection.check_response_for_error(response, "query")
    except (*_CONNECTION_ERRORS, KeyError) as error:
        await drop(connection)
        raise SurrealConnectionError(
            f"SurrealDB transaction failed against {url!r}: {error}"
        ) from error
    return response


def _failed_statements(response: dict[str, Any]) -> list[_FailedStatement]:
    """Return the ``ERR``-status per-statement results from a ``query_raw`` response.

    Raises:
        SurrealStoreError: The response carried no per-statement result list at
            all — a shape the engine should never actually return, but one this
            helper refuses to silently paper over. Hygiene (ledger #31): the
            full malformed ``response`` is logged server-side; the raised
            message never echoes it (the response CAN carry per-statement
            results with bound values, the same leak surface as the ordinary
            rollback path below).
    """
    results = response.get("result")
    if not isinstance(results, list):
        logger.error("store.transaction.malformed_response", extra={"response": response})
        raise SurrealStoreError(
            "SurrealDB returned an unexpected transaction response shape "
            f"(no per-statement result list); {_SERVER_LOG_HINT}"
        )
    return [
        _FailedStatement(index=index, raw_result=statement_result.get("result"))
        for index, statement_result in enumerate(results)
        if isinstance(statement_result, dict) and statement_result.get("status") == _ERR_STATUS
    ]


def _is_retryable_conflict(failed_statements: list[_FailedStatement]) -> bool:
    """Whether a rolled-back transaction's failure is a RETRYABLE conflict.

    True only when at least one failed statement's message carries the engine's
    own "this transaction can be retried" marker — the write-write race between
    two genuinely concurrent transactions on the same row, which resolves cleanly
    on retry. Every other rejection (e.g. a domain/``ASSERT`` violation) never
    carries that marker and is never retried. Reads the RAW engine text (never
    exposed outside this module — see :class:`_FailedStatement`); ledger #31
    only changed what :func:`execute_transaction` RAISES, not this decision.
    """
    return any(
        _RETRYABLE_CONFLICT_MARKER in str(failed.raw_result) for failed in failed_statements
    )
