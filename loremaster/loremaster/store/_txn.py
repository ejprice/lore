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
from typing import Any, NoReturn

from lorerunes.engine_rejection import CatchSpec
from pydantic import SecretStr
from surrealdb import (
    AsyncEmbeddedSurrealConnection,
    AsyncHttpSurrealConnection,
    AsyncWsSurrealConnection,
)
from surrealdb.errors import (
    AlreadyExistsError,
    ErrorKind,
    QueryDetailKind,
    QueryError,
    ServerError,
    SurrealError,
    parse_query_error,
)
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

    Raised only when the LATEST attempt ended in a retryable conflict — the
    engine's TYPED ``details.kind: TransactionConflict``
    (:data:`_RETRYABLE_CONFLICT_KIND`), read by :func:`_rollback_verdict` on the
    transactional path and by :func:`is_retryable_conflict_error` on the
    single-statement path; the ``"can be retried"`` text is logged EVIDENCE,
    never consulted — AND the attempt ceiling or wall-clock deadline has been
    reached — never for a
    domain/``ASSERT`` rejection, which always raises
    :class:`TxnDomainRejectionError` immediately, unretried (see
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


class TxnDomainRejectionError(SurrealStoreError):
    """A non-retryable DOMAIN rejection: the store said the write is ILLEGAL and rolled back.

    Built by :func:`_domain_rejection_error` for every domain-class engine ``ERR`` the rollback
    verdict classifies as non-retryable — an ``ASSERT`` violation, a type-coercion failure, a
    ``governed_conflict:`` throw (the :class:`TxnGovernedConflictError` subclass below), any
    ``ERR`` that is neither transport nor exhausted contention. A generic teaching message with
    NO attributes parsed from the raw text (the §2.5 hygiene boundary is unchanged; ledger #31
    keeps the raw engine text out of the message).

    Subclasses :class:`SurrealStoreError` so every existing ``except SurrealStoreError`` keeps
    catching it unchanged — the same argument :class:`TxnContentionExhaustedError` makes. It is
    DISJOINT from :class:`SurrealConnectionError` (transport — an UNKNOWN outcome, the commit may
    have landed with the response lost) and from :class:`TxnContentionExhaustedError` (a conflict
    that outlived the budget), so ``isinstance(error, TxnDomainRejectionError)`` means precisely
    "the store rejected this write, for good" — a KNOWN-illegal outcome, the ONLY class safe to
    compensate for (close-out rulings §2.4-1; ``LocalMemoryBackend.remember``'s supersede
    compensation keeps the authoritative ledger row on every other cause and lets replay converge).

    It carries TWO TYPED attributes (am-37 §15.2), set by :func:`_domain_rejection_error` from what
    the raise site already holds — never parsed from the message or the engine text:

    Attributes:
        error_class: The classifier's ``_ERROR_CLASS_*`` label — a RECOGNISED refusal (UNIQUE,
            ``ASSERT``, coercion, the governed THROW, …) or ``unspecified rejection`` (the
            residue the classifier could not name). A construction that names none takes the
            class's own label (:meth:`_constructed_error_class`).
        kind: The engine's typed kind — the SDK ``ErrorKind`` value, or the ``QueryDetailKind``
            value for a ``Query`` error that carries one — or ``None`` for a kind-less
            (bare-text) input. :func:`proven_no_key` reads both.
    """

    def __init__(self, message: str = "", *, error_class: str | None = None, kind: str | None = None) -> None:
        super().__init__(message)
        self.error_class = error_class if error_class is not None else self._constructed_error_class()
        self.kind = kind

    @classmethod
    def _constructed_error_class(cls) -> str:
        """The label a construction that names no ``error_class`` carries: the unrecognised residue."""
        return _ERROR_CLASS_UNSPECIFIED


class TxnGovernedConflictError(TxnDomainRejectionError):
    """A governed guarded-write matched ZERO rows and THREW ``governed_conflict:`` (§2.5, #456).

    Same shape as :class:`TxnContentionExhaustedError`: a SUBCLASS so every existing
    ``except SurrealStoreError`` keeps catching it, a generic teaching message, and NO
    attributes parsed from the raw text (the caller already holds the table and row id).
    A governed conflict is a DOMAIN rejection (never retried).
    """

    @classmethod
    def _constructed_error_class(cls) -> str:
        """Classified by construction (am-37 §15.2): its own class IS the recognition."""
        return _ERROR_CLASS_GOVERNED_CONFLICT


class TxnUniqueViolationError(TxnDomainRejectionError):
    """The write's IDENTITY is already taken (amendment 32 §1): a record-id collision, or a UNIQUE-index
    collision on a natural key. The winner's row is there — a compare-and-set caller re-reads it.

    A SUBCLASS of :class:`TxnDomainRejectionError` (every existing ``except`` keeps catching it); a generic
    message; NO attribute parsed from the raw text (ledger #31).
    """

    @classmethod
    def _constructed_error_class(cls) -> str:
        """Classified by construction (am-37 §15.2): its own class IS the recognition."""
        return _ERROR_CLASS_UNIQUE_VIOLATION


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


#: am-37 §15.1 (RULED): the CLASS half of :func:`proven_no_key` — store faults that prove no write landed
#: whatever their kind: exhausted contention (rolled back) and the two pre-send faults (a parameter collision,
#: an envelope violation; never sent). A hand-adjudicated literal beside the classes it names (F-2 (b)): never
#: computed from the live subclass tree, which would file every new class as "proven" silently.
_PROVEN_NO_KEY_CLASSES: tuple[type[SurrealStoreError], ...] = (
    TxnContentionExhaustedError,
    TxnParamCollisionError,
    TxnEnvelopeViolationError,
)

#: am-37 §15.3 (RULED, an ALLOWLIST): the typed kinds of an UNRECOGNISED rejection that PROVE it preceded the
#: write — raised at or before the statement's evaluation, or as its refusal (§15's proven rows: top-level
#: ``Validation``, ``Thrown``, ``AlreadyExists``, ``NotFound``, ``Configuration``; Query detail
#: ``NotExecuted``). SDK constants, never re-spelled. EVERY other kind is outcome-unknown, never enumerated:
#: ``Internal`` / ``Serialization`` / ``TimedOut`` / ``Cancelled`` / a bare ``Query``, AND any kind the
#: engine serves that nobody adjudicated (``Transaction``, ``Query:Aborted`` on the floating ``v3.2`` tag,
#: #336, or one a future SDK adds) — the safe side of §15's asymmetry. The set grows ONLY by adjudication;
#: re-open trigger: a vendor/spec statement or a reproduced observation of per-kind commit timing for single
#: statements (§15).
_PROVEN_KINDS: frozenset[str] = frozenset(
    {
        ErrorKind.VALIDATION,
        ErrorKind.THROWN,
        ErrorKind.ALREADY_EXISTS,
        ErrorKind.NOT_FOUND,
        ErrorKind.CONFIGURATION,
        QueryDetailKind.NOT_EXECUTED,
    }
)


def proven_no_key(error: BaseException) -> bool:
    """Whether ``error`` PROVES the write it interrupted never landed: THE ONE predicate (am-37 §15-15.2).

    TRUE for:

    * a member of :data:`_PROVEN_NO_KEY_CLASSES` (rolled back / never sent), whatever its kind;
    * a :class:`TxnDomainRejectionError` the classifier RECOGNISED as a refusal (``error_class`` is
      not ``unspecified rejection`` — UNIQUE, ``ASSERT``, coercion, the governed THROW, …), whatever
      its raw kind: recognition means the engine evaluated the statement and refused it (§15.2);
    * an UNRECOGNISED :class:`TxnDomainRejectionError` whose typed ``kind`` proves the timing — a
      kind ON the allowlist :data:`_PROVEN_KINDS` (§15.3).

    FALSE for everything else, which is never enumerated: an unrecognised rejection of any kind OFF
    the allowlist (adjudicated outcome-unknown, or served by the engine and never adjudicated) or
    with NO kind (a bare-text input — the safe side), transport
    (:class:`SurrealConnectionError`), the bare :class:`SurrealStoreError` base, any foreign store
    class, cancellation, interrupts, timeouts, any future unknown.

    ``PrincipalKeyStore.mint`` asks THIS predicate both as its inner wrap's ``catch=`` (so a proven
    fault is translated to the not-landed message, an unproven one passes through to the outer,
    outcome-unknown wrap) and to decide its revoke note — one decider, three consequences. A
    pass-through member (:class:`TxnContentionExhaustedError`) is re-raised before any ``catch=`` is
    consulted, so for it the predicate decides the note only.

    The kind test compares typed values with ``==`` (amendment 36 §1.2 pin 3: only the classifier
    reads engine text; every other decision reads the typed kind).
    """
    if isinstance(error, _PROVEN_NO_KEY_CLASSES):
        return True
    if not isinstance(error, TxnDomainRejectionError):
        return False
    if error.error_class != _ERROR_CLASS_UNSPECIFIED:
        return True
    kind = error.kind
    return kind is not None and any(kind == proven for proven in _PROVEN_KINDS)


#: The catch set :func:`wrap_store_rejection` translates when its caller names none: every
#: :class:`SurrealStoreError` that is not a pass-through (finding #400's consumer law).
_DEFAULT_REJECTION_CATCH: tuple[type[SurrealStoreError], ...] = (SurrealStoreError,)


def wrap_store_rejection(
    domain_error: type[Exception],
    context: str,
    *,
    catch: CatchSpec = _DEFAULT_REJECTION_CATCH,
) -> AbstractContextManager[None]:
    """The ONE surreal-taxonomy binding for the engine-rejection wrap (finding #400, Layer 2).

    Every store write-path that must translate a raw engine rejection into its own domain
    error routes through THIS context manager instead of hand-rolling the ``try/except
    (SurrealConnectionError, TxnContentionExhaustedError): raise; except SurrealStoreError as
    e: raise <Domain>(...) from e`` idiom. It is the single place the surreal taxonomy is
    named — ``passthrough=(SurrealConnectionError, TxnContentionExhaustedError)``, the default
    ``catch=(SurrealStoreError,)``, and the predicate catch :func:`proven_no_key` — and it
    delegates the control flow (re-raise the pass-throughs FIRST, then translate the catch
    ``from`` the original) to the stdlib-only :func:`lorerunes.reclassify` (Layer 1).
    Splitting it this way keeps BOTH the taxonomy and the control-flow policy each exactly ONE
    thing: a taxonomy change (a new pass-through class) lands here and reaches every caller; a
    control-flow change lands in ``reclassify`` and reaches every caller — routing without
    either would be ROUTING-IS-NOT-SHARING.

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
        catch: What to translate (am-37 §14 Q1 N-3 mechanism (d); §15.1): a tuple of
            :class:`SurrealStoreError` classes, or a predicate over the raised exception
            (:data:`lorerunes.engine_rejection.CatchSpec`). Defaults to
            :data:`_DEFAULT_REJECTION_CATCH` — every non-pass-through store error — which every caller
            but one uses. ``PrincipalKeyStore.mint`` narrows an INNER wrap to the predicate
            :func:`proven_no_key`, so only a fault that proves no key landed gets its not-landed
            message (anything else passes it UNTOUCHED), and nests it inside a default-catch OUTER wrap
            whose message says the outcome is unknown. The pass-throughs are unchanged whatever
            ``catch`` is: they are re-raised first, before any predicate is consulted.

    Returns:
        A context manager wrapping the store's awaited write; enter it with
        ``with wrap_store_rejection(<DomainError>, <context>): await ...``.
    """
    return reclassify(
        passthrough=(SurrealConnectionError, TxnContentionExhaustedError),
        catch=catch,
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

# The engine's TYPED retry decision (amendment 36 §1.1 / amendment 37 §4) — ``details.kind`` of a
# per-statement ERR entry (the transactional path) or of the SDK's raised ``ServerError`` (the
# single-statement path), measured on 3.2.4 on BOTH paths, DECIDED by ``==`` on the kind — never by the
# message text, which can echo a caller's value (a finding body quoting "…can be retried" must not buy ~2 s of
# engine retries).
#
# The retryable write-write conflict: ``kind: Query``, ``details.kind: TransactionConflict`` (live text today:
# "…Transaction conflict: Resource busy. This transaction can be retried"). The SDK ships neither a constant
# nor a predicate for it, so this literal is ours. (The rollback CASCADE kinds need no constant: the SDK's
# own ``QueryError`` predicates decide them — see :func:`_is_domain_cascade_notice`, amendment 37 §7.)
_RETRYABLE_CONFLICT_KIND = "TransactionConflict"

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
# §2.5 (#456): the fixed teaching label for a governed-conflict THROW. Names WHAT happened + what
# to do — never a slice of the raw text, never the raw `governed_conflict:` marker (rider ii).
_ERROR_CLASS_GOVERNED_CONFLICT = (
    "governed conflict — the guarded row moved between authorization and the write; "
    "re-authorize and re-issue"
)
_ERROR_CLASS_UNIQUE_VIOLATION = (
    "unique violation — the record id or a unique index value is already taken; re-read the row"
)
_ERROR_CLASS_UNSPECIFIED = "unspecified rejection"

# The substrings (verified live — see the module docstring's ``ASSERT``/coercion
# grounding, and ``TestDomainRejectionErrorType`` / ``TestReplaceFile`` in
# ``test_surreal_store.py``) that :func:`_classify_engine_error` reads to pick a
# teaching LABEL — and ONLY on its text leg: an error the engine leaves untyped
# (``kind: Internal`` / ``Validation`` / ``Thrown`` with ``details: None``) or a
# bare string from a caller with no typed error. They never decide the CLASS or
# the retry: the retry is the typed :data:`_RETRYABLE_CONFLICT_KIND`, the
# rollback cascade is the SDK's own typed predicates (:func:`_is_domain_cascade_notice`),
# and any other typed kind is ``unspecified rejection`` whatever its text says
# (amendments 35 §2, 36 §1.1, 37 §1). A case-insensitive membership check, never a
# value-bearing capture group — the classifier only ever RETURNS one of the fixed
# labels above, never a slice of the raw text itself.
_ASSERT_VIOLATION_MARKER = "must conform to"
_FIELD_COERCION_MARKER = "coerce"
# The live-verified substring of SurrealDB 3.1.5's own rejection text: "Parse
# error: Exceeded expression recursion depth limit ... this expression nests or
# chains operators too deeply" (finding #66, scratchpad/probe_long_query_66b.py
# — the raw, pre-classification ``ValidationError`` text captured against
# spike-surreal). Matched case-insensitively, same as the other markers.
_QUERY_RECURSION_DEPTH_MARKER = "recursion depth"
# §2.5 (#456): the FIXED prefix OUR code authors into the in-store conflict THROW
# ("governed_conflict:<t>:<id>") — the classification key. The `<t>:<id>` suffix is free-form
# forensics that rides only the server-side rollback log, never the raised message (rider ii).
_GOVERNED_CONFLICT_MARKER = "governed_conflict:"
# amendment 32 §1 (+ FK-a28b-1): the two live-verified identity-taken texts (3.2.4, probe_exists_texts.py):
# a record-id collision "Database record `t:x` already exists" and a UNIQUE-index collision "Database index
# `k` already contains 'v', with record `k:1`". A table-level "The table 't' already exists" matches neither.
# amendment 35 §2: the ONE untyped identity shape (a UNIQUE-index collision; the record shape is TYPED on both
# paths) is a PREFIX test at position 0 of the engine-authored text — every echoed value comes after it.
_UNIQUE_INDEX_MARKER = "database index `"
# amendment 35 §2 item 3: the governed marker, anchored at the engine-authored START of the THROW text
# (measured 3.2.4: the engine wraps a THROW as "An error occurred: <thrown>").
_ENGINE_THROW_PREFIX = "an error occurred: "

# The correlation hint appended to every classified rollback message, so an
# operator holding only the (deliberately generic) exception text can still
# find the full engine detail :func:`execute_transaction` logs server-side.
_SERVER_LOG_HINT = "see the server log for the full engine detail"


def _classify_engine_error(raw_result: object) -> str:  # noqa: PLR0911 - one label per engine class
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

    TYPED FIRST (amendments 35 §2, 36 §1.1, 37 §1): the engine's kind decides the CLASS; message text
    decides only a teaching LABEL, and only for the kinds the engine leaves untyped — ``Internal`` (the
    UNIQUE-index prefix at position 0, then ``ASSERT``, then coercion), ``Validation`` (recursion depth,
    #66) and ``Thrown`` (OUR governed prefix, anchored at the engine's THROW wrapping — measured 3.2.4 on
    both paths: ``An error occurred: <thrown text>``, ``details: None``). Every other kind is
    ``unspecified rejection`` whatever its text says. A bare string (a legacy caller with no typed error)
    keeps the whole text ladder.

    Args:
        raw_result: The typed SDK error — the ``run_query`` path's raised ``ServerError``, or the
            transactional path's ONE parse of the failed statement (:func:`_typed_root_cause`) — or, for an
            untyped entry, the raw ``result`` text.

    Returns:
        One of the ``_ERROR_CLASS_*`` labels. The typed retryable conflict is checked first for defensive
        symmetry with :func:`is_retryable_conflict_error` (both attempt bodies raise
        :class:`RetryableConflictSignal` before any classifier runs, so no caller reaches it today).
    """
    if isinstance(raw_result, AlreadyExistsError):
        # Typed beats text (amendment 32 §1.1 item 3): the SDK's own discriminator decides.
        return _ERROR_CLASS_UNIQUE_VIOLATION if raw_result.record_id is not None else _ERROR_CLASS_UNSPECIFIED
    if _is_retryable_conflict_kind(raw_result):
        return _ERROR_CLASS_RETRYABLE_CONFLICT
    kind = raw_result.kind if isinstance(raw_result, ServerError) else None
    untyped = kind is None
    lowered = str(raw_result).lower()
    if (untyped or kind == ErrorKind.THROWN) and lowered.startswith(
        _ENGINE_THROW_PREFIX + _GOVERNED_CONFLICT_MARKER
    ):
        return _ERROR_CLASS_GOVERNED_CONFLICT
    if untyped or kind == ErrorKind.INTERNAL:
        if lowered.startswith(_UNIQUE_INDEX_MARKER):
            return _ERROR_CLASS_UNIQUE_VIOLATION
        if _ASSERT_VIOLATION_MARKER in lowered:
            return _ERROR_CLASS_ASSERT_VIOLATION
        if _FIELD_COERCION_MARKER in lowered:
            return _ERROR_CLASS_FIELD_COERCION
    if (untyped or kind == ErrorKind.VALIDATION) and _QUERY_RECURSION_DEPTH_MARKER in lowered:
        return _ERROR_CLASS_QUERY_TOO_COMPLEX
    return _ERROR_CLASS_UNSPECIFIED


def _domain_rejection_error(error_class: str, message: str, *, kind: str | None = None) -> SurrealStoreError:
    """Build the domain-rejection error for a raise site — §2.5 (#456), the ONE mapping helper.

    Returns :class:`TxnGovernedConflictError` iff ``error_class`` is the governed-conflict label,
    else :class:`TxnDomainRejectionError` — every domain rejection now carries a typed class
    (close-out rulings §2.4-1), so a compensation site can gate on
    ``isinstance(error, TxnDomainRejectionError)`` instead of exact-typing the base. BOTH raise
    sites (``run_query`` and ``_run_verified_transaction``) build their rejection through THIS,
    never a cloned ``if label ==`` at each site (ROUTING-IS-NOT-SHARING).

    am-37 §15.2: the built error carries BOTH typed attributes — ``error_class`` (the label this
    receives) and ``kind`` (the engine's typed kind, which each raise site derives from the typed
    error it holds via :func:`_typed_kind`; ``None`` for a bare-text input). ``kind`` is keyword-only
    and defaults to ``None`` — a kind-less rejection, which :func:`proven_no_key` treats as UNKNOWN
    (the safe side), so a raise site that dropped it would err toward the conditional note, never
    toward a false "no key"; each raise site's kind is pinned separately. Nothing is parsed from text.
    """
    if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:
        return TxnGovernedConflictError(message, error_class=error_class, kind=kind)
    if error_class == _ERROR_CLASS_UNIQUE_VIOLATION:
        return TxnUniqueViolationError(message, error_class=error_class, kind=kind)
    return TxnDomainRejectionError(message, error_class=error_class, kind=kind)


def _typed_kind(error: object) -> str | None:
    """The engine's typed kind of ``error`` (am-37 §15.2), as :class:`TxnDomainRejectionError` carries it.

    A ``Query`` error that carries a detail kind (``TimedOut`` / ``Cancelled`` / ``NotExecuted``) is
    keyed by that DETAIL kind — the fact §15 adjudicates; any other typed SDK error by its top-level
    ``kind`` (a ``Query`` error with no detail stays ``Query``). Anything untyped — a bare-text
    per-statement result, a non-SDK exception — is ``None``.
    """
    if not isinstance(error, ServerError):
        return None
    if isinstance(error, QueryError):
        return _detail_kind(error) or error.kind
    return error.kind


@dataclass(frozen=True)
class _FailedStatement:
    """One ``ERR``-status statement from a rolled-back transaction's raw response.

    Carries the statement's POSITION in the raw response (``index``, 0-based)
    alongside the engine's raw per-statement result (``raw_result``) — the
    latter is kept STRICTLY internal to this module (logged server-side as
    EVIDENCE only, never a decision input) and must never be interpolated into
    a :class:`SurrealStoreError` message; see :func:`_classify_engine_error`.

    ``typed`` is the ONE parse of the entry (amendment 36 §1.1): the SDK's
    ``parse_query_error`` over the whole per-statement dict, made once by
    :func:`_parse_failed_statement` and read by every decision — the retry verdict,
    the cascade selector and the classifier. ``None`` for an entry that carries
    no ``kind``, or whose shape the SDK's parser cannot type (amendment 37 §7 /
    F-C8; defaulted, so a two-argument construction keeps working).
    """

    index: int
    raw_result: Any
    typed: ServerError | None = None


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


def _detail_kind(error: object) -> str | None:
    """``details.kind`` of a typed SDK error (``None`` for anything untyped)."""
    details = getattr(error, "details", None)
    kind = details.get("kind") if isinstance(details, dict) else None
    return kind if isinstance(kind, str) else None


def _is_retryable_conflict_kind(error: object) -> bool:
    """THE ONE retryable-conflict authority (amendment 36): the engine's TYPED ``TransactionConflict``."""
    return isinstance(error, ServerError) and _detail_kind(error) == _RETRYABLE_CONFLICT_KIND


def is_retryable_conflict_error(error: BaseException) -> bool:
    """Whether a caught exception from a single-statement SDK call is the
    engine's own retryable write-write conflict (finding #108).

    The single-statement seam's ONE detection authority: an attempt body that
    has already ruled out a transport/connection fault
    (:func:`is_connection_error`) calls THIS — never inspects the raw engine
    text itself — to decide whether to raise :class:`RetryableConflictSignal`.
    Decides by the engine's TYPED kind through :func:`_is_retryable_conflict_kind`
    (``details.kind`` == :data:`_RETRYABLE_CONFLICT_KIND`, amendment 36 §1.1), read
    on every call — the SAME authority :func:`_rollback_verdict` reads on the
    transactional path; the message text (which can echo a caller's value) is
    never consulted.

    Args:
        error: A caught, non-connection SDK/domain error.

    Returns:
        ``True`` if ``error`` is the engine's retryable write-write conflict;
        ``False`` for any other domain/schema rejection.
    """
    return _is_retryable_conflict_kind(error)


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
          engine's typed conflict can ride any position). Checked FIRST: a
          ``TransactionConflict`` entry is claimed here before the domain
          branch's cascade selector could ever read it — ordering is
          load-bearing.
        * ``root_cause`` — for a conflict, the FIRST entry whose typed kind is
          :data:`_RETRYABLE_CONFLICT_KIND` (the entry that actually
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
        (kind-seeking) selector is.
    """
    is_conflict = _is_retryable_conflict(failed_statements)
    if is_conflict:
        root_cause = next(
            failed
            for failed in failed_statements
            if _is_retryable_conflict_kind(failed.typed)
        )
    else:
        root_cause = _domain_root_cause(failed_statements)
    return is_conflict, root_cause


def _domain_root_cause(failed_statements: list[_FailedStatement]) -> _FailedStatement:
    """Select the SUBSTANTIVE entry from a non-conflict rollback's failed
    statements (audit-102 B3, design addendum Ruling 3) — never a positional
    pick.

    The live engine (3.2.4) writes a domain rollback as: zero or more cascade
    ``ERR`` entries BEFORE the offender (``details.kind: NotExecuted`` —
    statements that never actually ran), THEN the offender's own substantive
    rejection, THEN cascade entries AFTER it (``details.kind: Cancelled``),
    ending in the refused COMMIT ("Cannot COMMIT: the transaction was aborted
    due to a prior error", ``details.kind: NotExecuted``). Neither end of that
    list is ever the cause: ``[0]`` is cascade (finding #93's false premise),
    ``[-1]`` is the COMMIT abort.

    Returns:
        The FIRST entry :func:`_is_domain_cascade_notice` does not call cascade
        (amendment 36 §1.1 / amendment 37 §7 — the SDK's typed predicates
        decide, never the text). When every entry is cascade
        (no substantive rejection exists anywhere — degenerate but real),
        degrades to the LAST entry: the engine's own final word, and the
        honest thing to report when nothing substantive was ever said.
    """
    for failed in failed_statements:
        if not _is_domain_cascade_notice(failed):
            return failed
    return failed_statements[-1]


def _is_domain_cascade_notice(failed: _FailedStatement) -> bool:
    """Whether ``failed`` is rollback NOISE (a statement the rollback stopped from running) rather than a
    substantive engine rejection — decided by the SDK's OWN typed predicates on the ONE parse
    (:attr:`_FailedStatement.typed`), never by the text (amendment 36 §1.1: an echoed or reworded phrase moves
    nothing) and never by a kind string of ours (amendment 37 §7 / F-C11: the SDK owns the ``details.kind``
    strings and exports the decision).

    THE adjudication of every member of the SDK's ``QueryDetailKind`` (the domain's source of truth; this
    docstring is the ONE place it lives, amendment 37 §5 / §7):

    * ``NotExecuted`` (:attr:`QueryError.is_not_executed`) → CASCADE. Measured 3.2.4 on the statements BEFORE
      the offender ("The query was not executed due to a failed transaction") and on the refused COMMIT
      ("Cannot COMMIT: the transaction was aborted due to a prior error").
    * ``Cancelled`` (:attr:`QueryError.is_cancelled`) → CASCADE. Measured 3.2.4 on a statement AFTER the
      offender (builder-63c-i-a-a28c §REQ-3).
    * ``TimedOut`` (:attr:`QueryError.is_timed_out`) → SUBSTANTIVE, deliberately excluded: a statement that
      RAN and timed out is the cause, never noise.

    An entry the SDK did not type as a :class:`QueryError` (``typed`` is ``None``, or another kind) is
    substantive. The day the SDK grows a fourth ``QueryDetailKind`` member it is unadjudicated here until
    this list is extended.
    """
    typed = failed.typed
    return isinstance(typed, QueryError) and (typed.is_not_executed or typed.is_cancelled)


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
    # blindreader-dry-2 F1 / audit-fix-1 B3: the LATEST classified conflict's own cause, so the
    # exhaustion record can quote the SAME engine text the seam's own non-exhausted rejections
    # already log, instead of leaving the operator with only an attempt count and a hint
    # pointing at a server log that holds nothing. Every raise of the signal but ONE chains
    # ``from error`` (the caught engine exception) — derived 2026-09-29 by reading every
    # ``RetryableConflictSignal()`` raise site in the workspace:
    #   * ``_raise_attempt_failure``, THE one failure ladder (amendment 37 §3), serving BOTH
    #     ``run_query`` (the ten single-statement seams) and ``_txn_query_raw`` (an RPC-level
    #     conflict on the transactional path): not lexically inside a handler, but called ONLY
    #     from one, with the caught exception as its ``error`` argument, and it chains itself;
    #   * the three session-bootstrap closures in ``bootstrap_session``;
    #   * the handlers in ``scout.py`` and ``inbox_awaiter.py``, lexically inside ``except``.
    # The ONE unchained raise is ``_run_verified_transaction``'s nested ``_attempt`` (LEAD
    # RULING 2026-07-20): it detects a PER-STATEMENT conflict by INSPECTING a returned response,
    # not by catching a raise, so it raises the signal BARE — no exception is in scope to chain.
    # That driver call also passes no ``label=`` (§10's allowlist exempts the body), so its
    # exhaustion record carries NO ``label`` / ``url`` / ``engine_error`` keys at all, whatever
    # ``last_conflict_cause`` holds; ``_run_verified_transaction`` logs the last attempt's
    # failing statements via ``_log_rollback`` instead.
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


# The transactional path's own rejection event (amendment 37 §3): an RPC-level (envelope) error on
# ``query_raw`` that is NOT transport — e.g. a statement the engine refuses to parse — is logged here, under
# ``_txn``'s OWN logger. It is distinct from ``store.transaction.rolled_back``, which records a
# PER-STATEMENT rollback the engine executed; this one records a request the engine refused as a whole.
_TXN_REJECTION_LABEL = "store.transaction.rejected"


async def _raise_attempt_failure(
    error: BaseException,
    connection: Any,
    *,
    drop: DropConnection,
    url: str,
    noun: str,
    label: str,
    logger: logging.Logger,
) -> NoReturn:
    """THE ONE failure ladder for a failed SDK call on a live connection (amendment 37 §3 / F-11).

    Both driver paths call this and nothing else decides: :func:`run_query`'s single-statement attempt and
    :func:`_txn_query_raw`'s transactional ``query_raw`` + ``check_response_for_error``. The three fates:

    1. **Transport** — the SDK's response-routing ``KeyError`` (a socket drop with a request in flight), or
       anything :func:`is_connection_error` classifies as transport/auth: self-heal via ``drop`` and raise
       :class:`SurrealConnectionError`.
    2. **Retryable conflict** — :func:`is_retryable_conflict_error` (the typed ``TransactionConflict``):
       raise :class:`RetryableConflictSignal` for :func:`retry_on_conflict` to consume.
    3. **Domain rejection** — every other kind (``Validation`` / ``Internal`` / ``Query`` / …) is the
       statement's own fault, so the connection is KEPT. The full engine text is logged under ``label`` on
       ``logger`` (the caller's, so a seam's rejection event keeps its logger name); the raised error — built
       by :func:`_domain_rejection_error` — carries only the classified label and :data:`_SERVER_LOG_HINT`,
       never the engine text (ledger #31: that text can echo a bound value).

    Args:
        error: The exception the SDK call raised (a member of ``(*_CONNECTION_ERRORS, KeyError)``).
        connection: The connection the call ran on — the one ``drop`` discards on a transport fault.
        drop: The owner's connection self-heal.
        url: The store's RPC URL, for the raised messages and the log record.
        noun: What the caller calls the request (``"transaction"``, ``"brief query"``, …), for the messages.
        label: The rejection log event.
        logger: The logger the rejection is recorded on.

    Raises:
        SurrealConnectionError: Fate 1.
        RetryableConflictSignal: Fate 2.
        SurrealStoreError: Fate 3 (a :class:`TxnDomainRejectionError` or one of its subclasses).
    """
    if isinstance(error, KeyError) or is_connection_error(error):
        await drop(connection)
        raise SurrealConnectionError(f"SurrealDB {noun} failed against {url!r}: {error}") from error
    if is_retryable_conflict_error(error):
        raise RetryableConflictSignal() from error
    error_class = _classify_engine_error(error)
    logger.error(label, extra={"url": url, "error_class": error_class, "engine_error": str(error)})
    raise _domain_rejection_error(
        error_class,
        f"SurrealDB {noun} rejected against {url!r} ({error_class}); {_SERVER_LOG_HINT}",
        kind=_typed_kind(error),
    ) from error


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
            # THE one failure ladder (amendment 37 §3), shared with ``_txn_query_raw``: transport → drop;
            # conflict → signal; domain → keep the connection, log the full engine detail under this seam's
            # OWN event and logger (F6), and raise the error ``_domain_rejection_error`` builds from the
            # classified label (§2.5 point 3 — the ONE mapping), never the engine text (#31).
            await _raise_attempt_failure(
                error, connection, drop=drop, url=url, noun=noun, label=label, logger=logger
            )

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
      FIRST failed entry that is not a cascade notice — decided by the SDK's
      own typed predicates on the ONE parse (:func:`_is_domain_cascade_notice`:
      ``details.kind`` ``NotExecuted`` or ``Cancelled`` is cascade, ``TimedOut``
      is substantive), never by the text, which is logged as evidence only
      (audit-102 B3: finding #93's premise — "everything before the first
      ``ERR`` succeeded" — is FALSE on the live engine, which retroactively
      stamps pre-offender statements ``ERR`` too, as non-execution cascade
      notices; a rollback with no substantive entry anywhere degrades to the
      LAST entry, the engine's refused COMMIT, "Cannot COMMIT: the transaction
      was aborted due to a prior error").
    * A RETRYABLE optimistic-concurrency conflict — the engine's TYPED
      ``details.kind: TransactionConflict`` (:data:`_RETRYABLE_CONFLICT_KIND`)
      on any per-statement entry, or on an RPC-level error
      :func:`_txn_query_raw` raises — is retried with a fresh,
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
    # log line (below) can report the LAST attempt's root cause. RESET to
    # ``None`` at every attempt's ENTRY (amendment 37 §6 / F-8), so it only ever
    # describes THIS attempt: an attempt that ends in an RPC-level conflict
    # (signalled by ``_txn_query_raw``, with no per-statement entries) leaves it
    # ``None``, and exhaustion then logs no per-statement root — honestly, none
    # exists — instead of an EARLIER attempt's stale one. Logging on
    # every retry would spam the log for a conflict that resolves cleanly;
    # logging only the terminal disposition (a domain rejection, immediately,
    # or an exhausted conflict, once) matches this seam's behaviour before
    # finding #108 extracted the driver.
    last_conflict: tuple[_FailedStatement, int, list[_FailedStatement]] | None = None
    verified: dict[str, Any] = {}

    async def _attempt() -> None:
        nonlocal last_conflict
        last_conflict = None
        response = await _txn_query_raw(statement, params, acquire=acquire, drop=drop, url=url)
        failed_statements = _failed_statements(response)
        statement_count = len(response.get("result") or [])
        if not failed_statements:
            verified.clear()
            verified.update(response)
            return
        is_conflict, root_cause = _rollback_verdict(failed_statements)
        if not is_conflict:
            typed_root = _typed_root_cause(root_cause)
            error_class = _classify_engine_error(typed_root)
            _log_rollback(root_cause, statement_count, failed_statements)
            raise _domain_rejection_error(
                error_class,
                f"SurrealDB transaction failed and was rolled back: statement "
                f"{root_cause.index + 1} of {statement_count} was rejected "
                f"({error_class}); {_SERVER_LOG_HINT}",
                kind=_typed_kind(typed_root),
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

    Every caught error is decided by :func:`_raise_attempt_failure`, THE ONE ladder
    :func:`run_query` also uses (amendment 37 §3 / F-11). Only TRANSPORT kinds
    self-heal: an RPC-level error of a domain kind — a statement the engine refuses
    to parse (``Validation``), an ``Internal`` or ``Query`` rejection — keeps the
    healthy connection and raises a classified domain rejection whose message never
    echoes the engine text, logged in full under ``store.transaction.rejected``.

    Raises:
        SurrealConnectionError: The server is unreachable, the socket died, or the
            connection lost its authentication.
        RetryableConflictSignal: The engine reported a retryable conflict for the
            request as a whole.
        SurrealStoreError: The engine rejected the request itself (a domain kind).
    """
    connection = await acquire()
    try:
        response = await connection.query_raw(statement, params)
        connection.check_response_for_error(response, "query")
    except (*_CONNECTION_ERRORS, KeyError) as error:
        await _raise_attempt_failure(
            error,
            connection,
            drop=drop,
            url=url,
            noun="transaction",
            label=_TXN_REJECTION_LABEL,
            logger=logger,
        )
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
        _FailedStatement(
            index=index,
            raw_result=statement_result.get("result"),
            typed=_parse_failed_statement(index, statement_result),
        )
        for index, statement_result in enumerate(results)
        if isinstance(statement_result, dict) and statement_result.get("status") == _ERR_STATUS
    ]


# The exception classes the installed SDK's ``parse_query_error`` (and the ``parse_rpc_error`` it recurses
# into for a ``cause``) can raise on a malformed per-statement dict — read from ``surrealdb/errors.py``
# (SDK 2.0.0, amendment 37 §7 / F-C8), never a bare ``except``:
#   * ``AttributeError`` — a ``cause`` that is not a dict (``parse_rpc_error`` calls ``raw.get``; measured by
#     coldaudit-63c-i-a-3);
#   * ``TypeError`` — an unhashable ``kind`` (or a cause's unhashable ``code``) used as a ``KIND_TO_CLASS`` /
#     ``CODE_TO_KIND`` dict key;
#   * ``RecursionError`` — a ``cause`` chain deeper than the interpreter's recursion limit
#     (``parse_rpc_error`` recurses once per level).
_SDK_PARSE_FAILURES = (AttributeError, TypeError, RecursionError)


def _parse_failed_statement(index: int, statement_result: dict[str, Any]) -> ServerError | None:
    """THE ONE parse of one per-statement ``ERR`` entry (amendment 36 §1.1), with THE ONE policy for an entry
    the SDK cannot type (amendment 37 §7 / F-C8 + F-14): it never escapes the verdict path.

    * An entry carrying a ``kind`` is typed by the SDK's own ``parse_query_error``.
    * An entry with no ``kind`` is carried untyped (``None``) — the bare-text ladder decides its label, loud
      ``unspecified rejection`` at worst (F-14's residual: the single-statement path would resolve such an
      entry to ``Internal``; unobserved on 3.2.4).
    * An entry whose ``kind`` is present but whose shape makes the SDK's parser raise one of
      :data:`_SDK_PARSE_FAILURES` is ALSO carried untyped, and logged at WARNING naming its index — the
      rollback is still classified and raised as a domain rejection, never an ``AttributeError`` out of
      :func:`execute_transaction`.

    Args:
        index: The entry's 0-based position in the raw response, for the warning.
        statement_result: The per-statement result dict (already known to be an ``ERR`` entry).

    Returns:
        The SDK's typed error for the entry, or ``None`` when the entry is untyped or untypeable.
    """
    if not statement_result.get("kind"):
        return None
    try:
        return parse_query_error(statement_result)
    except _SDK_PARSE_FAILURES as parse_failure:
        logger.warning(
            "store.transaction.untypeable_err_entry",
            extra={
                "statement_index": index,
                "parse_error": f"{type(parse_failure).__name__}: {parse_failure}",
            },
        )
        return None


def _typed_root_cause(failed: _FailedStatement) -> object:
    """The ONE parse's typed error for a per-statement ERR, else the raw text (amendment 36: parsed once)."""
    return failed.typed if failed.typed is not None else failed.raw_result


def _is_retryable_conflict(failed_statements: list[_FailedStatement]) -> bool:
    """Whether a rolled-back transaction's failure is a RETRYABLE conflict.

    True only when at least one failed statement's TYPED kind is the engine's
    ``TransactionConflict`` (:data:`_RETRYABLE_CONFLICT_KIND`) — the write-write
    race between two genuinely concurrent transactions on the same row, which
    resolves cleanly on retry. Every other rejection (e.g. a domain/``ASSERT``
    violation) is never retried, whatever its text echoes. Reads the ONE parse
    each entry carries (:attr:`_FailedStatement.typed`) via
    :func:`_is_retryable_conflict_kind` — the SAME authority
    :func:`is_retryable_conflict_error` reads for the single-statement path;
    ledger #31 only changed what :func:`execute_transaction` RAISES, not this
    decision.
    """
    return any(_is_retryable_conflict_kind(failed.typed) for failed in failed_statements)


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
