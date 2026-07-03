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
   ``status`` itself, raising :class:`SurrealStoreError` the moment any statement
   in the transaction failed — so neither caller can observe the SDK's "silent
   success". A RETRYABLE optimistic-concurrency conflict (two genuinely
   concurrent writers racing the same row) is retried, bounded, entirely within
   the call; every OTHER rejection (a domain/``ASSERT`` violation) surfaces
   immediately, since retrying it would never succeed.

The connection-lifecycle vocabulary (:class:`SurrealStoreError`,
:class:`SurrealConnectionError`, :data:`_CONNECTION_ERRORS`,
:data:`_SurrealConnection`) lives here rather than in ``surreal.py`` so both the
executor and the classifier can raise/catch it without an import cycle;
``surreal.py`` re-exports it so the historical ``from loremaster.store.surreal
import …`` seam every caller (and test) uses keeps working unchanged.
"""

from __future__ import annotations

import asyncio
import re
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

# The bounded number of attempts :func:`execute_transaction` makes when the
# engine reports a retryable write-write conflict. Two genuinely concurrent
# writers on the same row need at most a couple of rounds for the loser to retry
# against the winner's now-settled row; this ceiling is generous headroom without
# ever looping unboundedly under pathological contention.
_MAX_TXN_CONFLICT_ATTEMPTS = 5

# The linear backoff between conflict retries, in seconds — small enough that a
# legitimate two-writer race resolves in well under the test suite's own
# patience, but non-zero so two colliding retries do not immediately re-race in
# lockstep on the very next event-loop tick.
_TXN_CONFLICT_BACKOFF_SECONDS = 0.01

# The per-statement status the engine stamps on a rejected statement.
_ERR_STATUS = "ERR"

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


async def execute_transaction(
    statement: str,
    params: dict[str, Any],
    *,
    acquire: AcquireConnection,
    drop: DropConnection,
    url: str,
) -> None:
    """Run a multi-statement ``BEGIN … COMMIT`` and verify EVERY statement.

    The counter to the SDK's own ``query()`` gap: ``query()`` only checks the
    FIRST statement's ``status`` before deciding whether to raise, so a later
    rejection inside a transaction rolls back server-side while ``query()``
    returns ``None`` with no exception at all. Each attempt runs three linear
    steps: :func:`_txn_query_raw` (self-healing ``query_raw`` + the SDK's own
    RPC-error check), :func:`_failed_statements` (extract the per-statement
    ``ERR`` entries), then :func:`_should_retry` (decide whether a rollback is a
    transient conflict worth another attempt).

    A genuine transport/auth failure (the socket died, or the server is
    unreachable) self-heals via ``drop`` and surfaces as
    :class:`SurrealConnectionError` — see :func:`_txn_query_raw`.

    A per-statement engine rejection (the rollback case) splits two ways: a
    RETRYABLE optimistic-concurrency conflict (:data:`_RETRYABLE_CONFLICT_MARKER`)
    is retried, bounded, entirely within this call, so the caller never observes
    it; every OTHER rejection (e.g. an out-of-domain ``state``) raises
    :class:`SurrealStoreError` immediately — retrying it would never succeed.

    Args:
        statement: The full multi-statement ``BEGIN … COMMIT`` SurrealQL text.
        params: The bound parameters for the whole transaction.
        acquire: Returns the owner's live connection (its ``_ensure_connection``).
        drop: Self-heals the owner on a transport failure — nulls the cached
            handle and closes the dead socket so the next call reconnects.
        url: The owner's RPC URL, for the error messages.

    Raises:
        SurrealConnectionError: The server is unreachable or the socket died.
        SurrealStoreError: A non-retryable statement failure (the transaction was
            rolled back), or the conflict retries were exhausted under sustained
            contention.
    """
    # Populated by every attempt; guaranteed non-empty by the time the loop exits
    # (an empty result returns immediately, below), so the final raise can always
    # safely report the LAST attempt's failure.
    failed_statements: list[dict[str, Any]] = []
    for attempt in range(_MAX_TXN_CONFLICT_ATTEMPTS):
        response = await _txn_query_raw(statement, params, acquire=acquire, drop=drop, url=url)
        failed_statements = _failed_statements(response)
        if not failed_statements:
            return
        if not _should_retry(attempt, failed_statements):
            break
        await asyncio.sleep(_TXN_CONFLICT_BACKOFF_SECONDS * (attempt + 1))
    raise SurrealStoreError(
        f"SurrealDB transaction statement failed and was rolled back: "
        f"{failed_statements[-1].get('result')}"
    )


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


def _failed_statements(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the ``ERR``-status per-statement results from a ``query_raw`` response.

    Raises:
        SurrealStoreError: The response carried no per-statement result list at
            all — a shape the engine should never actually return, but one this
            helper refuses to silently paper over.
    """
    results = response.get("result")
    if not isinstance(results, list):
        raise SurrealStoreError(
            f"SurrealDB returned no result set for the transaction: {response!r}"
        )
    return [
        statement_result
        for statement_result in results
        if isinstance(statement_result, dict) and statement_result.get("status") == _ERR_STATUS
    ]


def _should_retry(attempt: int, failed_statements: list[dict[str, Any]]) -> bool:
    """Whether ``attempt``'s rollback should be retried.

    True only when attempts remain AND the failure is the retryable write-write
    conflict (:func:`_is_retryable_conflict`) — the final attempt, or any other
    kind of rejection, must stop and raise.
    """
    attempts_remaining = attempt < _MAX_TXN_CONFLICT_ATTEMPTS - 1
    return attempts_remaining and _is_retryable_conflict(failed_statements)


def _is_retryable_conflict(failed_statements: list[dict[str, Any]]) -> bool:
    """Whether a rolled-back transaction's failure is a RETRYABLE conflict.

    True only when at least one failed statement's message carries the engine's
    own "this transaction can be retried" marker — the write-write race between
    two genuinely concurrent transactions on the same row, which resolves cleanly
    on retry. Every other rejection (e.g. a domain/``ASSERT`` violation) never
    carries that marker and is never retried.
    """
    return any(
        _RETRYABLE_CONFLICT_MARKER in str(statement_result.get("result", ""))
        for statement_result in failed_statements
    )
