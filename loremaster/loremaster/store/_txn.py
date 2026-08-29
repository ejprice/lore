"""Shared low-level SurrealDB store internals — the single audited home for
every failure-handling concern the package's connection owners depend on.

What started as two concerns shared by two classes (finding #102/#108's
original extraction) is now FIVE, serving eleven owners (blindreader F3, the
DRY collapse): **transport-vs-domain classification** (:func:`is_connection_error`
et al.), **the per-statement transaction executor** (:func:`execute_transaction`),
**the shared retry driver** (:func:`retry_on_conflict`), **the ONE session
bootstrap** (:func:`bootstrap_session`), and **the ONE single-statement attempt
body** (:func:`run_query`). Every class that owns a signed-in, stateful SurrealDB
connection reached over the async SDK depends on this module now: the TEN
classes owning an ``async def _query`` (``store/surreal.py``, ``briefs.py``,
``agents.py``, ``tasks.py``, ``findings.py``, ``diff.py``, ``graph_surreal.py``,
``index/snapshots.py``, ``index/surreal_manifest.py``, ``memory/local.py``) call
:func:`run_query`; those same ten PLUS ``scout.py``'s module-level
``_open_command_connection`` (a bootstrap owner with no ``_query`` of its own —
the eleventh copy no ``_query``-keyed scan can see) call
:func:`bootstrap_session`. Ten `_query` bodies and eleven bootstrap owners are
two different populations that happen to overlap in ten of eleven members —
conflating them into one count is the exact class of prose-vs-code defect this
module's own callers now guard against (CLAUDE.md's "ONE IMPLEMENTATION"
section; do not repeat the conflation here).

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

3. **The shared retry driver** (:func:`retry_on_conflict`). The ONE place that
   owns attempt counting, the give-up predicate, the per-attempt jitter and the
   typed exhaustion error — called by :func:`execute_transaction`,
   :func:`run_query`, and (three times, composing ONE wall-clock budget)
   :func:`bootstrap_session`.

4. **The ONE session bootstrap** (:func:`bootstrap_session`). Materialises +
   selects a namespace/database on a freshly signed-in socket — the thirty
   hand-rolled, UNRETRIED bare inline ``await`` statements across ten modules
   (three per owner, no closures, no shared retry — see this function's own
   docstring), plus scout's own eleventh copy, collapsed into one function
   every owner calls AND retries through (blindreader F3).

5. **The ONE single-statement attempt body** (:func:`run_query`). Classifies,
   signals, self-heals and logs a single ``query()`` call — the ten attempt
   bodies, byte-identical but for TWO strings (the raised message's ``noun``
   and the ``label`` the rejection is logged under — see :func:`run_query`'s
   own docstring), collapsed.

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
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any

from pydantic import SecretStr
from surrealdb import (
    AsyncEmbeddedSurrealConnection,
    AsyncHttpSurrealConnection,
    AsyncWsSurrealConnection,
)
from surrealdb.errors import ErrorKind, ServerError, SurrealError
from websockets.exceptions import WebSocketException

from lorerunes import reclassify

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


class RetryableConflictSignal(Exception):
    """An attempt callable's way of telling :func:`retry_on_conflict` "the engine
    reported a RETRYABLE write-write conflict; try again".

    Raised INSIDE an attempt body, after it has classified a caught engine
    error via :func:`is_retryable_conflict_error` (the single-statement path)
    or read a rolled-back response's failed statements via
    :func:`_rollback_verdict` (the transactional path) — never raised
    anywhere else. Consumed entirely by :func:`retry_on_conflict`; it must
    never escape to a caller of the driver, and deliberately does NOT
    subclass :class:`SurrealStoreError` so a caller's broad ``except
    SurrealStoreError`` can never accidentally intercept it first.
    """


def wrap_store_rejection(
    domain_error: type[Exception], context: str
) -> AbstractContextManager[None]:
    """The ONE surreal-taxonomy binding for the engine-rejection wrap (finding #400, Layer 2).

    Every store write-path that must translate a raw engine rejection into its own domain
    error routes through THIS context manager instead of hand-rolling the ``try/except
    (SurrealConnectionError, TxnContentionExhaustedError): raise; except SurrealStoreError as
    e: raise <Domain>(...) from e`` idiom. It is the single place the surreal taxonomy is
    named — ``passthrough=(SurrealConnectionError, TxnContentionExhaustedError)``,
    ``catch=(SurrealStoreError,)`` — and it delegates the control flow (re-raise the
    pass-throughs FIRST, then translate the catch ``from`` the original) to the stdlib-only
    :func:`lorerunes.reclassify` (Layer 1). Splitting it this way keeps BOTH the taxonomy and
    the control-flow policy each exactly ONE thing: a taxonomy change (a new pass-through
    class) lands here and reaches every caller; a control-flow change lands in ``reclassify``
    and reaches every caller — routing without either would be ROUTING-IS-NOT-SHARING.

    The wrapped body is the store's awaited call(s); a transport fault / exhausted contention
    (:class:`SurrealConnectionError` / :class:`TxnContentionExhaustedError`, both of which
    SUBCLASS :class:`SurrealStoreError`) propagates UNTOUCHED to the retry/lifecycle layer,
    and only a genuine :class:`SurrealStoreError` domain rejection is wrapped LOUD as
    ``domain_error(context)`` chained ``from`` the raw engine error (consumer law: no raw
    engine error reaches the caller; ledger #31 keeps the raw detail out of the message).

    Args:
        domain_error: The store's domain-error class to raise on a rejection (e.g.
            :class:`~loremaster.keeps.KeepStoreError`). Called with ``context`` to build the
            one raised error, only on a ``SurrealStoreError`` — never on the happy path or a
            pass-through.
        context: The domain error's message — WHAT was rejected, in the store's own words.

    Returns:
        A context manager wrapping the store's awaited write; enter it with
        ``with wrap_store_rejection(<DomainError>, <context>): await ...``.
    """
    return reclassify(
        passthrough=(SurrealConnectionError, TxnContentionExhaustedError),
        catch=(SurrealStoreError,),
        make_error=lambda: domain_error(context),
    )


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

# The ONE SDK-await-boundary error-classification set (packet 05a-ii, R-2). At the
# boundary where a query is IN FLIGHT on the socket, a mid-op drop surfaces not only the
# :data:`_CONNECTION_ERRORS` transport family but ALSO a raw ``builtins.KeyError(request-
# uuid)`` from SDK 2.0.0's response routing — probed on 3.1.5 and re-probed unchanged on
# 3.2.4 (store reference §3 ~:420-427; finding #336). Both the ``await`` verb's
# ``InboxAwaiter`` and ``CommandSubscriber``'s reconnect ladder / teardown ride this SAME
# atom rather than each hand-rolling ``(*_CONNECTION_ERRORS, KeyError)`` inline: a policy
# two call sites must agree on is a function/constant they IMPORT, never a pattern they
# clone (ONE IMPLEMENTATION, #102/#120 — routing is not sharing). Consumers must
# ``from loremaster.store._txn import _SDK_AWAIT_BOUNDARY_ERRORS`` and reference it as a
# module global so a mutation of this ONE definition reaches every catch site; a same-named
# LOCAL re-definition is a drift-only two-source clone the mutation proof cannot see (the
# adversary's R3.3 pinned bound — re-open if a THIRD module ever catches this boundary, or
# if this value ever changes, at which point add a same-value drift check).
_SDK_AWAIT_BOUNDARY_ERRORS = (*_CONNECTION_ERRORS, KeyError)

# The reconnect-LADDER variant: the SDK-await boundary PLUS a
# :class:`TxnContentionExhaustedError` (a ``RuntimeError``, so NOT a member of
# ``_CONNECTION_ERRORS``). ``CommandSubscriber.run`` unions it at its reconnect ladder so
# sustained contention on a command claim backs off and reconnects rather than killing the
# channel (finding #108's removed-behaviour preservation); ``InboxAwaiter`` treats an
# exhaustion on its LIVE path as a transient and re-polls within budget. Teardown /
# best-effort-close sites ride the base ``_SDK_AWAIT_BOUNDARY_ERRORS`` (no contention leg
# there — a kill/close never contends).
_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION = (*_SDK_AWAIT_BOUNDARY_ERRORS, TxnContentionExhaustedError)

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
# concurrent reporter through ONE row). This is :func:`retry_on_conflict`'s
# OWN guaranteed attempt FLOOR (audit-102 B1) — not a tuned number but the
# pre-#102 behavioural contract itself: the deadline may only cut retries
# once this many attempts have run, so a transaction (or single-statement
# write) slower than the deadline is still guaranteed this many tries, exactly
# as every caller was guaranteed before finding #102 introduced the deadline
# at all. It has exactly ONE consumer now — the driver that owns the policy
# (finding #108: ``briefs.py`` used to derive its own private mint budget from
# this constant; that consumer is gone, and nothing outside this module may
# reach for it again — see ``TestTheAttemptFloorOutlivesItsBriefsConsumer`` in
# ``test_retry_seam.py``).
_MAX_TXN_CONFLICT_ATTEMPTS = 5

# --- the repaired conflict-retry policy (finding #102), owned by ------------
# --- retry_on_conflict() below (finding #108: the ONE driver every caller ---
# --- shares, rather than eleven private copies of the same mechanics) -------
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
# (regenerate the full JSON receipt with the survey script above). ZERO exhaustions across all
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
        One of the ``_ERROR_CLASS_*`` labels. The retryable-conflict marker is
        checked FIRST for defensive symmetry with :func:`_is_retryable_conflict_text`
        (the same authority every caller's conflict detection reads), even
        though every seam's attempt body now raises :class:`RetryableConflictSignal`
        the moment it sees that marker (finding #108) and
        :func:`retry_on_conflict` consumes the signal without ever reaching a
        classifier — so on BOTH the transactional and single-statement paths
        this function is only ever called with a genuinely non-conflict
        (domain) rejection today. The branch stays first anyway: it is a
        one-line defensive check, not a load-bearing one, and removing it buys
        nothing.
    """
    text = str(raw_result)
    if _is_retryable_conflict_text(text):
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


@dataclass(frozen=True)
class StoreHandle:
    """The connection-OWNER triple a governed store injects into the shared substrate
    (design ``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §10.6 — packet 63a).

    A frozen bundle of EXACTLY the three values :func:`run_query` and
    :func:`execute_transaction` already take as separate keyword arguments — ``acquire``
    (the owner's lazy :meth:`_ensure_connection`), ``drop`` (its self-heal
    :meth:`_drop_connection`), and ``url`` — so :func:`~loremaster.governed.guarded_write`
    and :func:`~loremaster.governed.report_unmigrated_governed_rows` reach the store through
    the ONE retry/self-heal driver and NEVER a raw connection (design §10.6 R4). It carries
    connection callables, so it lives in ``loremaster`` (this module, beside the seams),
    NEVER ``lorerunes`` (predicates only).

    Every governed store exposes it through ONE accessor (e.g.
    :attr:`~loremaster.memory.local.LocalMemoryBackend.handle`), so a caller that composes a
    guarded write borrows the owner's real driver rather than cloning a connection lifecycle
    (ONE IMPLEMENTATION, #102/#120). 64's task/finding ledgers expose the same accessor over
    their own owner triple — the substrate signature stays table-agnostic.

    This is a data-carrier, not a mechanism: it holds the callables; the driver seams own
    the retry/self-heal/classification policy. The adversary's ``run_governed_query(
    connection, …)`` shim is the WRONG direction — it takes a raw connection, the exact SDK
    escape R4 forbids.
    """

    acquire: AcquireConnection
    drop: DropConnection
    url: str


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


def _is_retryable_conflict_text(text: str) -> bool:
    """The ONE place :data:`_RETRYABLE_CONFLICT_MARKER` is ever consulted.

    Both conflict detectors read the SAME marker through this function: the
    transactional path's per-statement scan (:func:`_is_retryable_conflict`,
    :func:`_rollback_verdict`) and the single-statement path's caught-exception
    check (:func:`is_retryable_conflict_error`). Moving
    :data:`_RETRYABLE_CONFLICT_MARKER` (as the contract's detection pins do)
    therefore moves every caller's notion of "conflict" at once — there is no
    second copy of this comparison anywhere in the package.
    """
    return _RETRYABLE_CONFLICT_MARKER in text


def is_retryable_conflict_error(error: BaseException) -> bool:
    """Whether a caught exception from a single-statement SDK call is the
    engine's own retryable write-write conflict (finding #108).

    The single-statement seam's ONE detection authority: an attempt body that
    has already ruled out a transport/connection fault
    (:func:`is_connection_error`) calls THIS — never inspects the raw engine
    text itself — to decide whether to raise :class:`RetryableConflictSignal`.
    Reads :data:`_RETRYABLE_CONFLICT_MARKER` via :func:`_is_retryable_conflict_text`
    on every call, so it always sees the CURRENT marker, never one captured at
    import time — the same property :func:`_rollback_verdict` has always had
    on the transactional path.

    Args:
        error: A caught, non-connection SDK/domain error.

    Returns:
        ``True`` if ``error`` is the engine's retryable write-write conflict;
        ``False`` for any other domain/schema rejection.
    """
    return _is_retryable_conflict_text(str(error))


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
            if _is_retryable_conflict_text(str(failed.raw_result))
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


async def retry_on_conflict[T](
    attempt: Callable[[], Awaitable[T]],
    *,
    deadline_seconds: float | None = None,
    label: str | None = None,
    url: str | None = None,
) -> T:
    """Run ``attempt`` until it succeeds, retrying ONLY a classified
    :class:`RetryableConflictSignal` (finding #108 — the DRY retry seam).

    The ONE place in this package that owns: attempt counting; the give-up
    predicate (``attempts >= _TXN_CONFLICT_ATTEMPT_CEILING`` OR
    (``elapsed >= deadline`` AND ``attempts >= _MAX_TXN_CONFLICT_ATTEMPTS``));
    the per-attempt FRESH full jitter (:func:`_txn_conflict_backoff_seconds`);
    and raising :class:`TxnContentionExhaustedError` on exhaustion. Every
    single-statement seam in this package, and :func:`execute_transaction`,
    call this — there is nothing left to hand-roll.

    A HELPER, NOT A DECORATOR (design ruling): the deadline is per-call and
    conflict DETECTION differs per path — the transactional caller reads a
    returned response's failed statements; every single-statement seam reads
    a RAISED exception — so a decorator would have to hide both behind a
    configuration it cannot type. The retry POLICY below is identical across
    every caller; only detection differs, and detection stays with the
    caller that owns the wire shape: ``attempt`` is responsible for
    classifying whatever it catches into :class:`RetryableConflictSignal` (or
    not); this function is responsible for everything that happens once that
    decision has been made.

    Anything ``attempt`` raises that is NOT :class:`RetryableConflictSignal`
    propagates UNTOUCHED, with ZERO retries: a transport fault may already
    have committed (retrying would double-apply — the at-most-once rule) and
    a domain rejection can never succeed, so only the signal is ever caught.

    Args:
        attempt: A zero-argument async callable, safe to re-run from scratch
            on every retry (true for every caller in this package — a
            conflicted single-statement write commits nothing; see the
            module docstring's idempotency measurement in
            ``test_retry_seam.py``).
        deadline_seconds: The wall-clock retry budget, honoured only once
            :data:`_MAX_TXN_CONFLICT_ATTEMPTS` attempts have run (audit-102
            B1 — a budget shorter than one attempt can never veto that
            attempt's own retry floor). ``None`` (the default) resolves
            :data:`_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS` — read HERE, at
            CALL time (a module-global lookup, never frozen into a default
            argument at import), so the two single-statement callers — which
            pass no deadline — have a deadline branch any test can actually
            reach; freezing it at import is exactly what left finding #102's
            retry branch unreachable by every test that was ever written.
        label: The caller's OWN canonical rejection event (e.g.
            ``"brief.query.rejected"``), carried into the exhaustion record so
            it is attributable (blindreader-dry-2 F1 / audit-fix-1 B3).
            ``None`` (the default) omits the seam-identity extras entirely rather
            than logging a hole. EVERY caller passes its own ``label`` except one:
            :func:`_run_verified_transaction` — the ONE ``BEGIN … COMMIT`` attempt
            body behind :func:`execute_transaction` and
            :func:`execute_read_transaction` — which keeps its own attribution via
            ``_log_rollback``. The EXEMPT caller is what is named — enumerating the
            attributed ones instead goes stale at the next caller (finding #151).
        url: The caller's RPC URL, logged alongside ``label`` — ``None`` unless
            ``label`` is also given.

    Returns:
        Whatever ``attempt`` returned once it stopped raising the signal.

    Raises:
        TxnContentionExhaustedError: The attempt ceiling, or the deadline
            once the attempt floor has been met, was reached with the
            conflict still unresolved. Subclasses :class:`SurrealStoreError`.
    """
    deadline = (
        _TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS if deadline_seconds is None else deadline_seconds
    )
    started = time.monotonic()
    attempts = 0
    # blindreader-dry-2 F1 / audit-fix-1 B3: the LATEST classified conflict's own cause. Every
    # caller that raises the signal FROM AN ``except`` HANDLER does so ``from error`` (the
    # original engine exception) — the ten single-statement seams and the three
    # session-bootstrap statements alike — so the exhaustion record can quote the SAME engine
    # text the seam's own non-exhausted rejections already log, instead of leaving the operator
    # with only an attempt count and a hint pointing at a server log that holds nothing. The
    # ONE exception is ``execute_transaction``'s nested ``_attempt`` (LEAD RULING
    # 2026-07-20): the transactional caller detects a conflict by INSPECTING a returned
    # response's failed statements, not by catching a raise, so it raises the signal BARE —
    # there is no exception in scope to chain — which is also why §10's allowlist exempts that
    # same body from ``label=``. On that path ``last_conflict_cause`` stays ``None`` and the
    # ``engine_error`` extra is the empty string, but the record still carries the failing
    # statement via ``_log_rollback``.
    last_conflict_cause: BaseException | None = None
    while True:
        try:
            return await attempt()
        except RetryableConflictSignal as signal:
            last_conflict_cause = signal.__cause__
        attempts += 1
        elapsed = time.monotonic() - started
        # B1 (audit-102): the deadline may bound retries; it may never veto the
        # FIRST one. Give up on the CEILING alone (the structural runaway
        # backstop), or on the deadline ONLY once the attempt floor (the
        # pre-#102 five-attempt guarantee) has been met — restoring, BY
        # CONSTRUCTION, the same non-regression guarantee every caller had
        # before finding #102 introduced the deadline at all.
        if attempts >= _TXN_CONFLICT_ATTEMPT_CEILING or (
            elapsed >= deadline and attempts >= _MAX_TXN_CONFLICT_ATTEMPTS
        ):
            # blindreader F2: this is the ONLY place that can see the attempt count, so
            # it is the ONLY place that can log it. Exactly one record, on EVERY caller
            # (the ten single-statement seams and ``execute_transaction`` alike, since
            # there is only one driver) — the terminal DISPOSITION, never the journey: a
            # conflict that resolves logs nothing here (see
            # ``test_nothing_is_logged_when_the_conflict_RESOLVES``), because contention
            # is the NORMAL case — the committed survey (``scripts/survey_txn_contention_102.py``,
            # cited above) measures a p50 of TWO attempts per mint at every N >= 8 — and a line
            # per retried attempt would be a log storm in production.
            extra: dict[str, Any] = {"attempts": attempts, "elapsed_seconds": elapsed}
            if label is not None:
                # Attributable: WHICH seam (the canonical event an operator already
                # greps), WHICH server, and WHAT THE ENGINE SAID — the same three facts
                # every non-exhausted rejection already logs, now on the one path that
                # previously lost all three.
                extra["label"] = label
                extra["url"] = url
                extra["engine_error"] = (
                    str(last_conflict_cause) if last_conflict_cause is not None else ""
                )
            logger.warning("store.retry.exhausted", extra=extra)
            raise TxnContentionExhaustedError(
                f"SurrealDB operation gave up after {attempts} attempts over "
                f"{elapsed:.3f}s ({_ERROR_CLASS_RETRYABLE_CONFLICT}); {_SERVER_LOG_HINT}",
                attempts=attempts,
                elapsed_seconds=elapsed,
            )
        await asyncio.sleep(_txn_conflict_backoff_seconds(attempts))


# The three session-bootstrap statements each carry their OWN canonical rejection event into
# the driver's exhaustion record, so an operator greeting a contended virgin first-connect
# lands on WHICH of the three statements died, not merely THAT one did (finding #151). Each
# value names its statement in the engine's own SurrealQL vocabulary — `DEFINE NAMESPACE`
# concerns a namespace, `use()` SELECTS a database, `DEFINE DATABASE` concerns a database —
# and the three are pairwise distinct so a single shared label cannot masquerade as three.
_BOOTSTRAP_DEFINE_NAMESPACE_LABEL = "store.bootstrap.define_namespace.rejected"
_BOOTSTRAP_SELECT_DATABASE_LABEL = "store.bootstrap.select_database.rejected"
_BOOTSTRAP_DEFINE_DATABASE_LABEL = "store.bootstrap.define_database.rejected"

# The signin credential keys the SurrealDB SDK expects. Defined ONCE here — the
# module every connection owner already imports ``bootstrap_session`` from — not
# re-declared per owner: twelve private copies of one payload shape is twelve
# places a change reaches eleven of ("a pattern to clone is a defect to clone",
# #102).
_SIGNIN_USER_KEY = "username"
_SIGNIN_PASS_KEY = "password"


def signin_credentials(*, user: str, password: SecretStr) -> dict[str, Any]:
    """Build the SDK ``signin`` payload — THE ONE PLACE A SECRET IS UNWRAPPED.

    Every connection owner in the package holds its password as a
    :class:`pydantic.SecretStr` (#211) precisely so the raw value cannot render
    through a ``repr``, an f-string, or a traceback frame. The SDK, however,
    needs the real bytes on the wire — so ``get_secret_value()`` is called HERE,
    once, in the narrowest possible scope, and the resulting dict is handed
    straight to ``connection.signin``. Twelve owners each calling
    ``get_secret_value()`` inline would be twelve copies of the unwrap policy;
    this is one (#102 — if two call sites need the same policy, it is a function
    they call, never a pattern they clone).

    Args:
        user: The root username to sign in as. Deliberately NOT a secret: it is
            a public default (named by ``SURREAL_DEFAULT_USER_ENV``), typing it
            as one would dilute the signal until nothing reads as a secret, and
            it is interpolated into no log or error message in this package.
        password: The root password, held as a :class:`SecretStr`.

    Returns:
        The ``{"username": …, "password": …}`` mapping ``connection.signin``
        expects, carrying the raw credential the SDK needs on the wire.
    """
    return {_SIGNIN_USER_KEY: user, _SIGNIN_PASS_KEY: password.get_secret_value()}


async def bootstrap_session(
    connection: _SurrealConnection, namespace: str, database: str, *, url: str
) -> None:
    """Materialise and select ``namespace``/``database`` on a freshly signed-in socket —
    THE ONE SESSION BOOTSTRAP (blindreader F3, finding #108's own sixth hole).

    Every ``_ensure_connection`` in the package used to hand-roll the same three
    statements (``DEFINE NAMESPACE IF NOT EXISTS`` / ``connection.use()`` /
    ``DEFINE DATABASE IF NOT EXISTS``) as three BARE, UNRETRIED inline ``await``
    statements — no closures, no shared anything — thirty copies across ten
    store/manifest/ledger modules, plus an eleventh in ``scout.py``'s module-level
    ``_open_command_connection`` (invisible to any scan keyed on ``_query``, exactly as
    scout was invisible to it the first time). **At HEAD this driver did not exist**: a
    retryable conflict during the DDL hit each owner's own ``except _CONNECTION_ERRORS``
    and was misclassified as a plain connection failure — unretried, and surfaced as
    :class:`SurrealConnectionError` for a server that was merely busy, not down (probed
    live, 16-way concurrent: **6.2%–34.4%** of virgin first-connects lost, across three
    160-connect runs — a RANGE, stated with its protocol, never a point estimate). **Two
    different defects, cloned in the same shape ten times, hand-written: nothing was
    SHARED, and the retry this function now performs is not a pre-existing convenience —
    it is what this wave BUILT.** Routing every owner through the ONE shared bootstrap is
    what turns that loss into the 0% this module's own test suite now measures.

    Disposition is deliberately NOT this function's concern — every failure (a
    conflict, retried to exhaustion, or a genuine transport/domain fault) propagates
    UNWRAPPED to the caller, EXACTLY as raised by the SDK or by
    :func:`retry_on_conflict` — no ``except`` clause of this function's own translates
    anything. That is load-bearing (``W1-SCOUTKILL`` — pinned by
    ``TestScoutsConnectFailureReachesTheReconnectLadder`` and
    ``TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType`` in
    ``test_retry_seam.py``): scout's
    reconnect ladder catches raw SDK types and :class:`TxnContentionExhaustedError`
    directly, never :class:`SurrealConnectionError`. A ``bootstrap_session`` that
    wrapped its own exhaustion would satisfy every store-seam pin and still fly straight
    past that ladder, killing the command channel with no backoff and no reconnect.
    **The wrap belongs at the SEAM, not in the shared helper** — the ten
    store/manifest/ledger owners wrap what this raises into
    :class:`SurrealConnectionError` in their own ``_ensure_connection`` (the F4 ruling:
    the connection never became usable, regardless of why); ``scout.py`` does not wrap
    at all, by design.

    The three statements share ONE wall-clock budget (blindreader-dry-2 F2 / audit-fix-1
    B2): each ``retry_on_conflict`` call below is handed what is LEFT of
    :data:`_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS`, not a fresh copy of it — three equal
    deadlines would be three independent budgets wearing a parameter, and this bootstrap
    runs under the caller's HELD connect lock, so an uncomposed budget triples how long a
    contended virgin first-connect blocks every other coroutine. Composing the budget
    cannot starve a statement of its retries: the attempt FLOOR
    (:data:`_MAX_TXN_CONFLICT_ATTEMPTS`, audit-102 B1) guarantees every statement its
    attempts regardless of wall time, deadline or no.

    Each of the three statements carries its OWN canonical rejection event
    (:data:`_BOOTSTRAP_DEFINE_NAMESPACE_LABEL` / :data:`_BOOTSTRAP_SELECT_DATABASE_LABEL`
    / :data:`_BOOTSTRAP_DEFINE_DATABASE_LABEL`) and ``url`` into
    :func:`retry_on_conflict`, so a bootstrap that exhausts logs a record naming WHICH
    statement died, WHICH server it was talking to, and WHAT THE ENGINE SAID — the full
    triple the raised ``TxnContentionExhaustedError``'s "see the server log" hint promises
    (finding #151, which this closed: the three calls previously passed neither).

    Args:
        connection: The freshly constructed, already SIGNED-IN socket to bootstrap.
        namespace: The namespace to materialise and select.
        database: The database to materialise and select.
        url: The caller's RPC URL (KEYWORD-ONLY, REQUIRED — every owner has it in hand
            at the call site). Threaded into each statement's exhaustion record so the
            server named there is the one THIS caller was connecting to, never a default.

    Raises:
        TxnContentionExhaustedError: The DDL or ``use()`` contended past the shared
            budget (or the attempt ceiling). Never wrapped here — see above.

    This function's OWN body raises nothing else: a transport fault (a raw ``OSError``/
    ``SurrealError``/``WebSocketException``) or a domain rejection of the bootstrap DDL
    propagates UNTRANSLATED, exactly as the SDK (or :func:`retry_on_conflict`) raised it
    — by design, so scout's reconnect ladder (which catches those raw types directly)
    and each of the ten seams' own translation (into :class:`SurrealConnectionError`)
    both see what actually happened.
    """
    started = time.monotonic()

    def _remaining_budget() -> float:
        """What is LEFT of the bootstrap's ONE wall-clock budget, never negative."""
        return max(0.0, _TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS - (time.monotonic() - started))

    async def _define_namespace() -> None:
        try:
            await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {namespace}")
        except _CONNECTION_ERRORS as error:
            if is_retryable_conflict_error(error):
                raise RetryableConflictSignal() from error
            raise

    async def _select_namespace_database() -> None:
        try:
            await connection.use(namespace, database)
        except _CONNECTION_ERRORS as error:
            if is_retryable_conflict_error(error):
                raise RetryableConflictSignal() from error
            raise

    async def _define_database() -> None:
        try:
            await connection.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
        except _CONNECTION_ERRORS as error:
            if is_retryable_conflict_error(error):
                raise RetryableConflictSignal() from error
            raise

    await retry_on_conflict(
        _define_namespace,
        deadline_seconds=_remaining_budget(),
        label=_BOOTSTRAP_DEFINE_NAMESPACE_LABEL,
        url=url,
    )
    await retry_on_conflict(
        _select_namespace_database,
        deadline_seconds=_remaining_budget(),
        label=_BOOTSTRAP_SELECT_DATABASE_LABEL,
        url=url,
    )
    await retry_on_conflict(
        _define_database,
        deadline_seconds=_remaining_budget(),
        label=_BOOTSTRAP_DEFINE_DATABASE_LABEL,
        url=url,
    )


async def run_query(
    *,
    acquire: AcquireConnection,
    drop: DropConnection,
    url: str,
    noun: str,
    label: str,
    statement: str,
    params: dict[str, Any] | None = None,
    logger: logging.Logger,
) -> Any:
    """The ONE single-statement attempt body (blindreader F3) — classify, signal,
    self-heal, log; every seam's ``_query`` calls this instead of hand-rolling its own
    copy of the same ladder.

    Ten modules used to carry this exact body, byte-identical but for the ``noun`` in
    the raised message and the ``label`` the rejection is logged under — the
    classification-and-signal POLICY, cloned ten times. ``acquire`` is called INSIDE
    the retried attempt (adversary R-3, latent): a build that hoisted it out would
    re-run the statement on a connection a previous attempt already dropped.

    Args:
        acquire: The seam's own ``_ensure_connection`` — returns the live, cached
            connection, reconnecting on first use or after a self-heal.
        drop: The seam's own connection self-heal — nulls the cached handle (if it is
            still the one that just failed) and closes the dead socket.
        url: The seam's RPC URL, for the raised messages.
        noun: What this seam calls the statement it runs (e.g. ``"brief query"``) —
            purely for the raised message's wording; the seam-identifying signal an
            operator actually greps on is ``label``, below.
        label: This seam's OWN canonical rejection log event (e.g.
            ``"brief.query.rejected"`` — see ``_SEAM_REJECTION_EVENTS`` in
            ``test_retry_seam.py``). Collapsing ten hand-rolled bodies into one function
            must not homogenise this: an operator grepping one seam's event name still
            finds only that seam's rejections.
        statement: The SurrealQL statement to run.
        params: The statement's bound parameters.
        logger: The CALLING seam's OWN module logger (``logging.getLogger(__name__)``
            in that seam's file) — ``JsonFormatter`` in ``loremaster/logging_setup.py`` writes
            ``"logger": record.name``, a served field, and every Mezmo query/alert
            keyed on ``logger:loremaster.tasks`` for ``task.query.rejected`` must keep
            matching. A shared attempt body logging under its OWN ``_txn`` logger would
            silently move every seam's rejection record to one logger name.

    Returns:
        Whatever the SDK's ``query()`` returned, laundered through ``Any`` (the SDK's
        wide ``Value`` return union) exactly as every existing ``_query`` seam does.

    Raises:
        SurrealConnectionError: A transport/socket/auth failure — self-heals via
            ``drop`` before raising.
        SurrealStoreError: A domain/schema rejection of the statement; the connection
            is left healthy. The full engine detail is logged under ``label`` first
            (ledger #31: the raised message never echoes it).
        TxnContentionExhaustedError: A genuine write-write conflict outlived the shared
            driver's retry budget. The ONE ``store.retry.exhausted`` record (logged by
            :func:`retry_on_conflict`, on ``_txn``'s OWN logger — a new event with no
            existing consumers, unlike this seam's rejection event above) carries this
            seam's ``label``/``url``/the engine's conflict text too (blindreader-dry-2
            F1 / audit-fix-1 B3), so exhaustion is attributable the same way a
            non-exhausted rejection already is.
    """

    async def _attempt() -> Any:
        connection = await acquire()
        try:
            return await connection.query(statement, params or {})
        except (*_CONNECTION_ERRORS, KeyError) as error:
            if isinstance(error, KeyError) or is_connection_error(error):
                # A genuine transport/auth fault (or the SDK's own response-routing
                # KeyError — see ``_txn_query_raw``'s docstring): self-heal and surface
                # loudly.
                await drop(connection)
                raise SurrealConnectionError(
                    f"SurrealDB {noun} failed against {url!r}: {error}"
                ) from error
            if is_retryable_conflict_error(error):
                raise RetryableConflictSignal() from error
            # A domain/schema rejection of the write — the connection is healthy and
            # must not be thrown away for a fault that is not the transport's. Message
            # hygiene (ledger #31): the raw engine text can echo a bound VALUE back
            # verbatim, and that text flows to MCP clients in P8 — so the FULL detail is
            # logged server-side under this seam's OWN event (and OWN logger — F6),
            # and the RAISED error carries only a CLASSIFIED, generic label plus a "see
            # the server log" hint, never the raw engine text itself.
            error_class = _classify_engine_error(error)
            logger.error(
                label,
                extra={"url": url, "error_class": error_class, "engine_error": str(error)},
            )
            raise SurrealStoreError(
                f"SurrealDB {noun} rejected against {url!r} ({error_class}); {_SERVER_LOG_HINT}"
            ) from error

    return await retry_on_conflict(_attempt, label=label, url=url)


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
    returns ``None`` with no exception at all. Each attempt (run by the shared
    :func:`retry_on_conflict` driver, finding #108) executes three linear
    steps: :func:`_txn_query_raw` (self-healing ``query_raw`` + the SDK's own
    RPC-error check), :func:`_failed_statements` (extract the per-statement
    ``ERR`` entries), then :func:`_rollback_verdict` (the ONE decision both
    the retry and the eventual raise read from) — raising
    :class:`RetryableConflictSignal` for a conflict (which the driver
    consumes) or :class:`SurrealStoreError` immediately for a domain
    rejection.

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
    await _run_verified_transaction(
        statement,
        params,
        acquire=acquire,
        drop=drop,
        url=url,
        deadline_seconds=deadline_seconds,
    )


async def execute_read_transaction(
    statement: str,
    params: dict[str, Any],
    *,
    acquire: AcquireConnection,
    drop: DropConnection,
    url: str,
    deadline_seconds: float | None = None,
) -> list[Any]:
    """:func:`execute_transaction`'s READ sibling — same guarantees, and it RETURNS.

    ⚠ **IT EXISTS BECAUSE A TRANSACTION THAT MUST SERVE A READ HAS NOWHERE ELSE TO
    GO.** :func:`execute_transaction` returns ``None`` by design, so a caller whose
    two dependent reads must share ONE snapshot (operator ruling **R7**: *"the TOCTOU
    is CLOSED BY CONSTRUCTION, not measured and accepted"*) could otherwise only
    hand-roll a ``query_raw`` — which was MEASURED to fail this repo's runtime
    SDK-escape guard. So the shared seam is EXTENDED rather than escaped: both verbs
    ride ONE attempt body (:func:`_run_verified_transaction`), which owns the
    per-statement verification, the rollback classification, the retry/backoff driver
    and the hygiene boundary. The ONLY difference is what is done with the response —
    this one projects it, that one discards it. Duplicating the body would have been
    the #102 shape inside the seam that exists to prevent it.

    Args:
        statement: The full multi-statement ``BEGIN … COMMIT`` SurrealQL text.
        params: The bound parameters for the whole transaction.
        acquire: Returns the owner's live connection (its ``_ensure_connection``).
        drop: Self-heals the owner on a transport failure.
        url: The owner's RPC URL, for the error messages.
        deadline_seconds: The wall-clock budget for conflict retries (see
            :func:`execute_transaction`).

    Returns:
        Each statement's ``result``, in statement order — including the ``None`` a
        ``LET`` yields, so a caller can index by the position it composed.

    Raises:
        SurrealConnectionError: The server is unreachable or the socket died.
        SurrealStoreError: A non-retryable (domain) statement failure — the whole
            transaction was rolled back. Classified/generic, exactly as its sibling.
        TxnContentionExhaustedError: A genuine write-write conflict outlived the
            deadline/attempt budget.
    """
    response = await _run_verified_transaction(
        statement,
        params,
        acquire=acquire,
        drop=drop,
        url=url,
        deadline_seconds=deadline_seconds,
    )
    results = response.get("result")
    if not isinstance(results, list):
        return []
    return [entry.get("result") if isinstance(entry, dict) else None for entry in results]


async def _run_verified_transaction(
    statement: str,
    params: dict[str, Any],
    *,
    acquire: AcquireConnection,
    drop: DropConnection,
    url: str,
    deadline_seconds: float | None,
) -> dict[str, Any]:
    """The ONE ``BEGIN … COMMIT`` attempt body — verify every statement, then return it.

    Extracted so :func:`execute_transaction` and :func:`execute_read_transaction` share
    the classification, the retry disposition and the hygiene boundary rather than
    cloning them. Its own contract is :func:`execute_transaction`'s docstring, which is
    the canonical description of the mechanism.
    """
    # Stashed by the attempt body on every CONFLICTED try, so the exhaustion
    # log line (below) can report the LAST attempt's root cause — logging on
    # every retry would spam the log for a conflict that resolves cleanly;
    # logging only the terminal disposition (a domain rejection, immediately,
    # or an exhausted conflict, once) matches this seam's behaviour before
    # finding #108 extracted the driver.
    last_conflict: tuple[_FailedStatement, int, list[_FailedStatement]] | None = None
    verified: dict[str, Any] = {}

    async def _attempt() -> None:
        nonlocal last_conflict
        response = await _txn_query_raw(statement, params, acquire=acquire, drop=drop, url=url)
        failed_statements = _failed_statements(response)
        statement_count = len(response.get("result") or [])
        if not failed_statements:
            verified.clear()
            verified.update(response)
            return
        is_conflict, root_cause = _rollback_verdict(failed_statements)
        if not is_conflict:
            error_class = _classify_engine_error(root_cause.raw_result)
            _log_rollback(root_cause, statement_count, failed_statements)
            raise SurrealStoreError(
                f"SurrealDB transaction failed and was rolled back: statement "
                f"{root_cause.index + 1} of {statement_count} was rejected "
                f"({error_class}); {_SERVER_LOG_HINT}"
            )
        last_conflict = (root_cause, statement_count, failed_statements)
        raise RetryableConflictSignal()

    try:
        await retry_on_conflict(_attempt, deadline_seconds=deadline_seconds)
    except TxnContentionExhaustedError:
        if last_conflict is not None:
            _log_rollback(*last_conflict)
        raise
    return verified


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
    exposed outside this module — see :class:`_FailedStatement`) via
    :func:`_is_retryable_conflict_text` — the SAME authority
    :func:`is_retryable_conflict_error` reads for the single-statement path;
    ledger #31 only changed what :func:`execute_transaction` RAISES, not this
    decision.
    """
    return any(_is_retryable_conflict_text(str(failed.raw_result)) for failed in failed_statements)


def _txn_coroutines() -> dict[str, Callable[..., Any]]:
    """THE ONE store-seam derivation (finding #279 / design INSTRUMENT F): every coroutine
    function DEFINED in this module (``loremaster.store._txn``), keyed by name.

    Both store-seam callers derive from THIS one walk rather than re-walking a namespace
    independently:

    * ``scripts.forgery_door_sweep.store_seams`` filters it to the DOOR subset (public +
      accepting a caller-supplied ``statement``);
    * ``loremaster/tests/test_blocks_edge._degrade_every_STORE_seam`` intersects it (by
      identity) with what ``loremaster.tasks`` binds — the WIDE set.

    So a 4th coroutine added here is classified CONSISTENTLY by both, never by "whichever
    walk happens to see it" (the #279 defect, one level up: CLAUDE.md ONE IMPLEMENTATION —
    "if two call sites need the same POLICY, it is a FUNCTION THEY CALL"). Returns the WIDE
    superset; each caller applies its own filter. Empty is a broken derivation, never a clean
    module — callers fail closed on it.
    """
    import inspect  # noqa: PLC0415

    return {
        name: value
        for name, value in globals().items()
        if inspect.iscoroutinefunction(value) and getattr(value, "__module__", None) == __name__
    }
