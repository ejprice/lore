"""Contract tests for the DRY retry seam — findings #108, #120, and the operator's
own ruling on ``DESIGN-LAW.md:75``:

    "Can this just be written as a helper method or decorator? DRY principle."

WHY THIS MODULE EXISTS. ``DESIGN-LAW.md`` told every future agent that the seam's
conflict-retry was **the reference pattern for ANY new hot-row mint** — i.e. *clone
this*. It was obeyed, twice, and each clone got the jitter wrong in a DIFFERENT way:
``findings.py`` hand-rolled a 16-slot id-derived jitter (finding #102 — the retry was
dead code for the whole of its life), and ``briefs.py`` cloned the shape with a 4-slot
per-call jitter (finding #108 — at 8-way contention the pigeonhole guarantees two
racers share a slot and then stay lockstepped for the entire ladder). Meanwhile the
THIRD caller — the single-statement ``_query`` seam — got **no retry at all** (finding
#120), so a retryable write-write conflict raises on its FIRST occurrence.

A doc that says "clone this pattern" is a defect generator, and this tree is the proof.
The fix is not better prose. **There must be nothing to clone, because it is a function
you call.**

------------------------------------------------------------------------------
THE CONTRACT THIS MODULE DECIDES (the builder builds FROM this)::

    # loremaster/loremaster/store/_txn.py

    class RetryableConflictSignal(Exception):
        '''An attempt callable's way of saying "the engine reported a RETRYABLE
        write-write conflict". Consumed by retry_on_conflict; it never escapes.'''

    async def retry_on_conflict(
        attempt: Callable[[], Awaitable[T]],
        *,
        deadline_seconds: float | None = None,
    ) -> T: ...

``retry_on_conflict`` is the ONLY place in the package that owns:

  * attempt counting;
  * the give-up predicate — ``attempts >= _TXN_CONFLICT_ATTEMPT_CEILING`` **or**
    (``elapsed >= deadline`` **and** ``attempts >= _MAX_TXN_CONFLICT_ATTEMPTS``);
  * the per-attempt FRESH full jitter (``_txn_conflict_backoff_seconds``);
  * raising :class:`TxnContentionExhaustedError` on exhaustion.

Everything the attempt raises that is NOT the signal propagates UNTOUCHED, with ZERO
retries. ``execute_transaction`` (multi-statement) and **all TEN single-statement
``_query`` seams** CALL it. ``briefs.py`` deletes its loop, its 4-slot jitter, its budget
constants and its label import.

**TEN, not two — and the ten are DISCOVERED, not listed** (operator ruling). ``_query``
is not one seam; it is ten hand-rolled copies of one seam, in ``store/surreal.py``,
``briefs.py``, ``agents.py``, ``tasks.py``, ``findings.py``, ``diff.py``,
``index/snapshots.py``, ``graph_surreal.py``, ``index/surreal_manifest.py`` and
``memory/local.py``. That is the DRY defect one level ABOVE the retry: what
``DESIGN-LAW.md:75`` invited a clone of was the seam itself. The first version of this
contract pinned two of them — the two the brief named — because nobody knew the other
eight existed. **A pin over a hand-written list is only as complete as the list, and the
list is exactly what nobody can be trusted to keep.** So the seams are enumerated from
the AST (see ``_discover_query_seams``) and every seam pin is parametrised over what is
FOUND: an eleventh clone is pinned the day it is written, by nobody's memory.

A HELPER, NOT A DECORATOR (design ruling, upheld): the deadline is per-call and the
conflict DETECTION differs per path — the transactional path reads the returned
response's failed statements, the single-statement path reads the RAISED exception —
so a decorator would have to hide both behind a configuration it cannot type. The
retry POLICY is identical across all three; only detection differs, and detection
stays with the caller that owns the wire shape. The signal is the seam between them.

TWO CONTRACT REQUIREMENTS THAT LOOK LIKE IMPLEMENTATION DETAIL AND ARE NOT:

1. **The default deadline is resolved at CALL time** (a module-global lookup of
   ``_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS`` when ``deadline_seconds is None``) — NOT
   frozen into a default argument at import. The two single-statement callers pass no
   deadline, so without this their deadline/floor branches are unreachable by ANY test
   — and an unreachable retry branch is precisely what finding #102 WAS. The
   unrepaired seam already does exactly this; the pins below depend on it.

2. **``asyncio.sleep`` is the backoff mechanism, and ``_txn_conflict_backoff_seconds``
   remains its single, NAMED source** — the driver calls it once per retry. Both are
   inherited from the existing seam (the sequential and concurrent jitter families in
   test_surreal_store.py read the backoff back through a patched ``asyncio.sleep``;
   the pins below additionally read it through the named draw, because identity is the
   only way to tell "shares the jitter" from "has one of its own"). A repair that
   inlines the draw, or waits by some other means, is not covered by these pins and
   must not be shipped without replacing them.

------------------------------------------------------------------------------
IDEMPOTENCY — THE QUESTION THAT HAD TO BE ANSWERED BEFORE ANY OF THIS WAS SAFE.

Retrying a single statement is only safe if a conflicted statement committed NOTHING.
That is an assumption about the ENGINE, so it was MEASURED, not assumed
(``scratchpad/contract-dry/probe_single_statement_conflict.py``, spike-surreal 3.1.5,
16 racers x 5 rounds = 80 mints against ONE hot counter row, 73 conflicted attempts
actually retried):

    every round: minted versions == {1..16} exactly, final counter row == 16.

**A conflicted single-statement write commits nothing. Retry is exactly-once.** That
finding is pinned live, not merely reported — see
:class:`TestSingleStatementRetryLandsExactlyOnce`.

THE OTHER HALF of that safety argument is the AT-MOST-ONCE rule, and it is why the
driver retries the SIGNAL and nothing else: a TRANSPORT fault (the socket died with a
statement in flight) may well have COMMITTED — only the acknowledgement was lost.
Retrying THAT would double-apply. ``SurrealConnectionError`` therefore propagates with
zero retries, and there are pins on it (the tempting ``except SurrealStoreError:
retry`` shape is a data-corruption bug wearing a resilience costume).

------------------------------------------------------------------------------
THE LIVE ERROR SHAPES (captured, never hand-typed — "fixture and code shared one
imagination" is how the dead ``"assert"`` marker survived this repo's entire life).
Captured 2026-07-13 against spike-surreal 3.1.5 / SDK 2.0.0 by
``scratchpad/contract-dry/probe_single_statement_conflict.py`` and ``probe_domain.py``:

    | case              | class            | kind       | details                 |
    |-------------------|------------------|------------|-------------------------|
    | retryable conflict| QueryError       | Query      | {'kind': 'NotExecuted'} |
    | ASSERT violation  | InternalError    | Internal   | None                    |
    | field coercion    | InternalError    | Internal   | None                    |
    | parse error       | ValidationError  | Validation | None                    |
    | transport / auth  | NotAllowedError  | NotAllowed | None                    |

NOTE, because it is tempting and WRONG: the conflict DOES carry a structured detail
(``is_not_executed == True``). It is **not a conflict signal** — "NotExecuted" means
"this statement did not run", which is equally true of a cancelled or cascaded
statement, and ``QueryDetailKind`` also spells ``TimedOut``/``Cancelled``. The only
CONFLICT-SPECIFIC signal SurrealDB 3.1.5 exposes is the engine's own retry advice in
the message text ("...can be retried") — the same marker the transactional path
already keys on. Keeping ONE signal for both paths is the point; two signals is the
divergence finding #102 was made of. That marker is consumed INSIDE ``_txn`` and is
never read by a caller (:class:`TestNoCallerEverReadsAnEngineMessage`).
"""

from __future__ import annotations

import ast
import asyncio
import contextlib
import functools
import importlib
import inspect
import io
import logging
import re
import sys
import tokenize
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_asyncio
from _sdk_guard import GuardCannotSubstantiate, GuardReport, _witness_file, artifact_root
from _sdk_guard import install as _install_shared_guard
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.briefs import BriefLedger
from loremaster.store import _txn as txn_module
from loremaster.store import surreal as surreal_module
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    _MAX_TXN_CONFLICT_ATTEMPTS,
    _TXN_CONFLICT_ATTEMPT_CEILING,
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
    _SurrealConnection,
    execute_transaction,
)
from loremaster.store.surreal import SurrealStore
from loremaster.store.surreal_schema import AGENT_TABLE, BRIEF_TABLE, BRIEFED_RELATION
from surrealdb import (
    AsyncEmbeddedSurrealConnection,
    AsyncHttpSurrealConnection,
    AsyncWsSurrealConnection,
    RecordID,
)
from surrealdb.errors import ErrorKind, InternalError, NotAllowedError, QueryError, ValidationError

from loremaster import briefs as briefs_module
from loremaster import scout as scout_module

# ---------------------------------------------------------------------------
# The two NEW names are resolved at CALL time, by attribute, not imported at module
# level.
#
# A module-level ``from loremaster.store._txn import retry_on_conflict`` would make this
# whole file uncollectable against the unrepaired tree — its RED would be a collection
# ImportError, which proves nothing about behaviour and would hide the ~20 pins here
# that ARE behaviourally red today (#120's missing retry, briefs' private loop, the
# policy divergence, the label prose). Every pin must be red for its OWN reason.
#
# It also keeps the CONTRACT itself mypy-clean against the unrepaired tree, so the
# builder's gate loop reports only ITS errors, never two pre-existing ones about names
# it has not written yet.
# ---------------------------------------------------------------------------

_MISSING_DRIVER = (
    "loremaster.store._txn.{name} does not exist. The shared retry driver IS the "
    "contract (see this module's docstring): one function owns attempt counting, the "
    "give-up predicate, the per-attempt jitter and the typed exhaustion error, and the "
    "three callers CALL it."
)


def _driver() -> Any:
    """The shared retry driver: ``_txn.retry_on_conflict``."""
    driver = getattr(txn_module, "retry_on_conflict", None)
    assert driver is not None, _MISSING_DRIVER.format(name="retry_on_conflict")
    return driver


def _signal() -> Any:
    """The shared conflict signal: ``_txn.RetryableConflictSignal``."""
    signal = getattr(txn_module, "RetryableConflictSignal", None)
    assert signal is not None, _MISSING_DRIVER.format(name="RetryableConflictSignal")
    return signal


_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "loremaster"
_TESTS_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = Path(__file__).resolve().parents[2]


# ===========================================================================
# DETECTION IS A SHARED THING TOO — and I nearly shipped a contract that never
# said so. (Cold adversary, blocker 1.)
#
# My first contract centralised the retry POLICY (one driver: counting, backoff,
# budget, typed error) and pinned it eight ways. It never once asked WHO DECIDES
# WHAT A CONFLICT IS. The adversary built **WB-PROSE**: all ten seams route through
# the shared driver for policy, and each hand-rolls its own detection by matching
# `"Resource busy"` in the engine text locally. It scored **839 passed, 0 failed,
# ruff clean, mypy 0** — indistinguishable from a correct build. Reword the engine's
# message and ALL TEN SEAMS STOP RETRYING.
#
# That is finding #93 → #102 reborn INSIDE the fix for #102: eleven copies of the
# exact prose coupling the whole wave exists to delete, under a banner that claims
# "the no-prose-branching invariant now has ZERO exemptions".
#
# The syntactic ban cannot catch it — it bans the label constants and the marker
# `"can be retried"`, and WB-PROSE keys on a DIFFERENT substring of the same
# sentence. The evasion space of "some substring of the engine's message" is
# unbounded; enumerating it is the arms race three earlier contract revisions lost.
#
# So detection is pinned the way policy is: **BY MUTATION.** Move the ONE shared
# marker; every seam's notion of "conflict" must move with it. A seam with a private
# prose match is UNCHANGED by the mutation — it keeps retrying the old text and
# ignores the new one — and that is mechanically visible, in both directions.
#
# HONEST LIMIT (stated here because a gate that overstates its reach is the thing we
# police): this does NOT make detection robust to a real engine rewording. SurrealDB
# 3.1.5 exposes no structured conflict signal (probed: the conflict arrives as
# QueryError/kind=Query/details={'kind':'NotExecuted'} — a "did not run" fact, equally
# true of a cancelled statement), so a text marker is FORCED. What this buys is that a
# rewording becomes a ONE-LINE fix in ONE place instead of eleven silent ones — and
# that the gate SAYS SO, loudly, instead of a suite going green while every retry in
# the tree is dead.
# ===========================================================================

# A conflict message that shares NOT ONE discriminating token with the live one: no
# "Transaction conflict", no "Resource busy", no "can be retried". A seam that matches
# ANY substring of the real message privately cannot recognise this — which is the point.
_MUTATED_MARKER = "the writer may take another turn"
_MUTATED_CONFLICT_TEXT = f"Row is presently occupied; {_MUTATED_MARKER}"


def _mutate_shared_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    """Move the ONE conflict-detection authority. Every seam must follow it."""
    assert hasattr(txn_module, "_RETRYABLE_CONFLICT_MARKER"), (
        "the shared conflict marker is gone — detection has no single authority left, "
        "and nothing can pin that eleven callers agree on what a conflict IS"
    )
    monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_MARKER", _MUTATED_MARKER)

# --- LIVE-CAPTURED engine shapes (see the module docstring's table) ----------
_LIVE_CONFLICT_TEXT = "Transaction conflict: Resource busy. This transaction can be retried"
_LIVE_CONFLICT_DETAILS = {"kind": "NotExecuted"}

# A bound value the engine echoes back verbatim in a domain rejection — the ledger-#31
# hygiene leak surface. It must never reach a raised message.
_SENSITIVE_MARKER = "TOP-SECRET-BOUND-VALUE-120"
_LIVE_ASSERT_TEXT = (
    f"Found '{_SENSITIVE_MARKER}' for field `status`, with record `brief:abc`, but field "
    f"must conform to: $value INSIDE ['open', 'done']"
)
_LIVE_COERCION_TEXT = (
    f"Couldn't coerce value for field `next` of `brief_counter:abc`: Expected `int` but "
    f"found `'{_SENSITIVE_MARKER}'`"
)
_LIVE_PARSE_TEXT = "Parse error: Unexpected token `an identifier`, expected Eof"
_LIVE_TRANSPORT_TEXT = "There was a problem with the database: Not allowed to do this"


def _conflict_error() -> QueryError:
    """The EXACT exception a single-statement write-write conflict raises."""
    return QueryError(ErrorKind.QUERY, _LIVE_CONFLICT_TEXT, details=dict(_LIVE_CONFLICT_DETAILS))


def _mutated_conflict_error() -> QueryError:
    """A conflict the engine reports in words the SHARED marker has been moved to."""
    return QueryError(
        ErrorKind.QUERY, _MUTATED_CONFLICT_TEXT, details=dict(_LIVE_CONFLICT_DETAILS)
    )


# Every LIVE rejection that is NOT a retryable conflict. Retrying any of them would
# never succeed, and hammering the engine with a statement it has already refused is
# the failure mode a too-broad ``except`` produces.
#
# FIXTURE DIVERSITY IS THE POINT (repo law: "if the code can branch on a value, at
# least one pin must use a DIFFERENT value"). A build that retries on
# ``isinstance(error, QueryError)``, or on ``kind == Internal``, or on
# ``is_not_executed``, or on "any ServerError", is caught by a DIFFERENT row here.
_NON_CONFLICT_REJECTIONS = [
    pytest.param(
        lambda: InternalError(ErrorKind.INTERNAL, _LIVE_ASSERT_TEXT), True, id="assert-violation"
    ),
    pytest.param(
        lambda: InternalError(ErrorKind.INTERNAL, _LIVE_COERCION_TEXT), True, id="field-coercion"
    ),
    pytest.param(
        lambda: ValidationError(ErrorKind.VALIDATION, _LIVE_PARSE_TEXT), True, id="parse-error"
    ),
    pytest.param(
        lambda: NotAllowedError(ErrorKind.NOT_ALLOWED, _LIVE_TRANSPORT_TEXT),
        False,
        id="transport-not-allowed",
    ),
    # P-5 (contract adversary, W8-NOKEYERROR): the SDK's OWN response routing raises a bare
    # ``builtins.KeyError(<request-uuid>)`` when a socket drops with a query in flight —
    # probe-verified live, and every seam classifies it as TRANSPORT (``isinstance(error,
    # KeyError) or is_connection_error(error)``). It is NOT a ``SurrealError``, so it enters
    # the ``except`` through a DIFFERENT door from every other row here, and the contract was
    # BLIND to it: a collapse whose ``run_query`` drops the ``KeyError`` from its catch tuple
    # turns a self-healing reconnect into an unhandled crash, and this contract scored
    # 342/342 on that build. (Three OTHER files pin it per-seam today — but the collapse makes
    # ONE body serve all ten, so their coverage becomes incidental rather than structural.)
    pytest.param(lambda: KeyError("a1b2c3d4-request-uuid"), False, id="sdk-KeyError-routing-drop"),
]

# The multi-statement rollback shape, LIVE (the marker rides the COMMIT entry, LAST —
# mirrors test_txn_contention.py's fixture, deliberately).
_CASCADE_TEXT = "The query was not executed due to a failed transaction"
_OK_STATEMENT: dict[str, Any] = {"status": "OK", "result": None}


def _conflict_rollback_response(conflict_text: str = _LIVE_CONFLICT_TEXT) -> dict[str, Any]:
    return {
        "result": [
            {"status": "ERR", "result": _CASCADE_TEXT},
            {"status": "ERR", "result": _CASCADE_TEXT},
            {"status": "ERR", "result": f"Cannot COMMIT: {conflict_text}"},
        ]
    }


def _ok_response() -> dict[str, Any]:
    return {"result": [dict(_OK_STATEMENT)]}


# An absurdity stop, NOT a budget: turns "the retry loop is unbounded" from a hang into
# an immediate, legible failure. Any real budget sits far below it.
_ABSURD_ATTEMPT_CEILING = 5_000

# Captured before any monkeypatching, so a recorder can still yield to the loop.
_REAL_ASYNCIO_SLEEP = asyncio.sleep

# The mint every hot-row caller in this repo runs — the statement `brief_counter` is
# actually contended on. Used by the live exactly-once pin.
_MINT_STATEMENT = (
    "UPSERT type::record('retry_counter', $name) SET next = (next ?? 0) + 1 RETURN AFTER"
)

# The brief name the live pins publish under. Deliberately NOT ``project`` and NOT
# ``base``: C1 shipped a defect that was invisible because all 37 fixtures used the one
# name the code branched on. If the code can branch on a value, the pins use another.
_WAVE_NAME = "dry-wave-108"

# Genuinely concurrent racers. The house floor for a concurrency pin is 8; 16 is used
# because the probe measured 12 conflicted attempts per 16-racer round (and only ~4 at
# 8-way) — a pin that must OBSERVE a retry needs contention it can rely on.
_RACERS = 16

# ---------------------------------------------------------------------------
# WHAT AN UNRETRIED BOOTSTRAP COSTS — a RANGE, with its protocol. Never a point.
#
# This figure was carried across four sites as two different flat point-estimates, and
# **NEITHER WAS REPRODUCIBLE AS STATED** (audit-fix-1 A4). Re-measured under the protocol
# below, three independent runs gave 55/160, 43/160 and 10/160 — the spread SWAMPS its own
# mean, so quoting any single run as a measured constant is precisely how a noisy sample
# becomes standing law. The DIRECTION is what is load-bearing: an unretried bootstrap loses
# first-connects, often. A range with its protocol says that honestly where a point estimate
# lies precisely.
#
# ONE constant, and the served assertion message below INTERPOLATES it — so the number in
# the string an engineer reads cannot drift from the number this file believes. (A retired
# figure re-typed into ten comments is ten copies to re-retire; that is how eight of them
# outlived their own retirement from production and standing law.)
# Receipt: ``scratchpad/blindreader2/probe_bootstrap.py``.
_UNRETRIED_BOOTSTRAP_LOSS = "6.2%-34.4%"
_UNRETRIED_BOOTSTRAP_PROTOCOL = (
    "16 racers x 10 rounds = 160 virgin first-connects, bootstrap unretried; "
    "three runs: 55/160, 43/160, 10/160"
)


# ---------------------------------------------------------------------------
# Fakes. ONE fake serves BOTH wire shapes — ``query`` (single statement, conflict
# arrives as a RAISED exception) and ``query_raw`` (transaction, conflict arrives in
# the RETURNED response) — and counts both against ONE attempt counter. That is what
# lets the policy-parity pins compare the three callers on the same axis.
# ---------------------------------------------------------------------------


@dataclass
class _ConflictingConnection:
    """Answers with a retryable conflict for the first ``conflicts`` attempts, then
    succeeds. ``conflicts=None`` conflicts forever (sustained, unresolvable contention).

    ``rows`` is what a successful single-statement ``query`` returns.
    """

    conflicts: int | None
    rows: Any = field(default_factory=lambda: [{"next": 7}])
    calls: int = field(default=0, init=False)
    dropped: int = field(default=0, init=False)
    # The words the engine reports the conflict IN. A FIELD, not a constant: the
    # detection pins move the shared marker and must then hand a caller a conflict
    # spelled the NEW way — and one spelled the OLD way, which must stop counting.
    conflict_text: str = _LIVE_CONFLICT_TEXT

    def _still_conflicting(self) -> bool:
        self.calls += 1
        if self.calls > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError(
                f"more than {_ABSURD_ATTEMPT_CEILING} attempts against sustained "
                f"contention — the retry budget is effectively unbounded"
            )
        return self.conflicts is None or self.calls <= self.conflicts

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        if self._still_conflicting():
            raise QueryError(
                ErrorKind.QUERY, self.conflict_text, details=dict(_LIVE_CONFLICT_DETAILS)
            )
        return self.rows

    async def query_raw(self, statement: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._still_conflicting():
            return _conflict_rollback_response(self.conflict_text)
        return _ok_response()

    def check_response_for_error(self, response: Any, method: str) -> None:
        return None

    async def close(self) -> None:
        self.dropped += 1


@dataclass
class _RejectingConnection:
    """Raises ``error`` on EVERY query — the domain/transport fault injector."""

    error: BaseException
    calls: int = field(default=0, init=False)

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        self.calls += 1
        raise self.error

    async def close(self) -> None:
        return None


@dataclass
class _ScriptedConnection:
    """Raises ``error`` for the first ``failures`` calls, then returns ``rows``.

    Unlike :class:`_ConflictingConnection` the failure is CALLER-SUPPLIED, so the same
    fake serves the detection pins (which need a conflict spelled in words the shared
    marker has been moved to, and the live words it has been moved AWAY from).
    """

    error: BaseException
    failures: int | None
    rows: Any = field(default_factory=lambda: [{"next": 4}])
    calls: int = field(default=0, init=False)

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        self.calls += 1
        if self.calls > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError("unbounded retry")
        if self.failures is None or self.calls <= self.failures:
            raise self.error
        return self.rows

    async def close(self) -> None:
        return None


@dataclass
class _SleepRecorder:
    """Records every duration handed to ``asyncio.sleep`` without waiting."""

    durations: list[float] = field(default_factory=list)

    async def sleep(self, duration: float) -> None:
        self.durations.append(duration)
        await _REAL_ASYNCIO_SLEEP(0)


@dataclass
class _JitterRecorder:
    """Records every call to the SHARED backoff function ``_txn_conflict_backoff_seconds``
    and DELEGATES to the real one.

    THE instrument for pin 3. A caller that keeps a PRIVATE copy of the jitter still
    backs off, still retries, still passes every "does briefs still work?" pin — and
    records ZERO draws here. That is the whole difference between DRY and looks-DRY.

    Delegating (rather than returning a canned 0.0) matters in exactly one place and it
    is the most important one: the LIVE 16-way pins run with the REAL backoff, so the
    racers genuinely desynchronise and the run converges the way production does. In the
    fake-connection pins ``asyncio.sleep`` is silenced anyway, so the real draw costs
    nothing there. A recorder that flattened the backoff to zero would have turned the
    live contention pins into a thrash test of their own making.
    """

    real: Callable[[int], float]
    draws: list[int] = field(default_factory=list)

    def draw(self, attempt_number: int) -> float:
        self.draws.append(attempt_number)
        return self.real(attempt_number)


def _record_shared_jitter(monkeypatch: pytest.MonkeyPatch) -> _JitterRecorder:
    assert hasattr(txn_module, "_txn_conflict_backoff_seconds"), (
        "the seam's named jitter source is gone. It must survive the extraction as the "
        "ONE function the driver draws from: identity is the only way a pin can tell "
        "'shares the jitter' from 'hand-rolled one that looks like it' (module "
        "docstring, requirement 2)."
    )
    recorder = _JitterRecorder(real=txn_module._txn_conflict_backoff_seconds)
    monkeypatch.setattr(txn_module, "_txn_conflict_backoff_seconds", recorder.draw)
    return recorder


def _silence_sleep(monkeypatch: pytest.MonkeyPatch) -> _SleepRecorder:
    recorder = _SleepRecorder()
    monkeypatch.setattr(asyncio, "sleep", recorder.sleep)
    return recorder


def _set_default_deadline(monkeypatch: pytest.MonkeyPatch, seconds: float) -> None:
    """Repoint the seam's DEFAULT deadline — the budget both single-statement callers
    actually run on, since neither passes one.

    This is why the contract requires the default to be read at CALL time: without it
    the deadline/floor branches of ``_query`` and the brief mint are unreachable by any
    test, and an unreachable retry branch is what finding #102 IS.
    """
    monkeypatch.setattr(txn_module, "_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS", seconds)


async def _run_execute_transaction(
    connection: Any, *, deadline_seconds: float | None = None
) -> None:
    async def _acquire() -> _SurrealConnection:
        return cast("_SurrealConnection", connection)

    async def _drop(_: Any) -> None:
        raise AssertionError("a conflict must never tear down a healthy connection")

    await execute_transaction(
        "BEGIN;\nUPSERT brief_counter SET next += 1;\nCOMMIT;",
        {},
        acquire=_acquire,
        drop=_drop,
        url="ws://127.0.0.1:19555/rpc",  # unreachable — never dialed
        deadline_seconds=deadline_seconds,
    )


def _store_on(connection: Any) -> SurrealStore:
    return cast("SurrealStore", _seam_on(SurrealStore, connection))


def _ledger_on(connection: Any) -> BriefLedger:
    return cast("BriefLedger", _seam_on(BriefLedger, connection))


# ===========================================================================
# THE ENUMERATION — and it is MECHANICAL, because a hand-written list is the next
# thing to go stale.
#
# ``_query`` is not one seam. It is TEN HAND-ROLLED COPIES of one seam, and that is the
# DRY defect one level ABOVE the retry: ``DESIGN-LAW.md:75`` invited a clone, and the
# thing that got cloned was the seam itself. The original brief scoped two of them — not
# out of carelessness, but because **nobody knew the other eight existed.** That is the
# whole argument for discovering the list instead of writing it:
#
#     A pin over a hand-listed set can only ever be as complete as the list, and the
#     list is exactly what nobody can be trusted to keep.
#
# So every class in the package that OWNS an ``async def _query`` is discovered from the
# AST and parametrised into every seam pin below. An ELEVENTH clone — a new ledger that
# hand-rolls the same seam without the retry — is discovered the day it is written and
# goes RED without anyone remembering to add it. That is the only kind of gate worth
# having.
#
# HONEST LIMITS, stated because a gate that overstates its reach is the thing we police:
#   * It finds a class OWNING ``_query``. A module that spells its single-statement seam
#     some other way (``_run``, a bare ``connection.query`` inline) is NOT found. The
#     shape is this repo's own universal idiom in all ten cases, and the identity pin
#     below means a new seam cannot even LOOK right without holding the one driver — but
#     the scan is a scan, not a proof.
#   * ``_MIN_KNOWN_SEAMS`` guards the scan against silently finding nothing: a
#     parametrised suite over an empty list is vacuously green, which is the failure mode
#     of every "mechanical" gate ever written.
# ===========================================================================

_MIN_KNOWN_SEAMS = 10

# The values the discovered constructors are fed, BY PARAMETER NAME. Nothing here is used
# by ``_query`` — the connection is injected — so a collaborator can be ``None``; these
# exist only to let a seam be CONSTRUCTED. A required parameter with no entry here fails
# LOUDLY (see ``_construct``) rather than silently dropping that seam from the suite: an
# eleventh clone must never fall out of the enumeration because its constructor was
# unfamiliar.
_CTOR_VALUES: dict[str, Any] = {
    "url": "ws://127.0.0.1:19555/rpc",  # unreachable — never dialed
    "namespace": "ns",
    "database": "db",
    "user": "root",
    "password": "root",
    "dim": PRODUCTION_DIM,
    "store": None,
    "manifest": None,
    "ledger": None,
    "embedder": None,
    "existing_chunks": None,
    "tier_roots": {},
    "project_roots": (),
    "project_root": Path("."),
}


def _discover_query_seams() -> list[tuple[str, type]]:
    """Every class in the package owning an ``async def _query`` — ``(module, class)``."""
    names: list[tuple[str, str]] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        module_path = (
            f"loremaster.{path.relative_to(_PACKAGE_ROOT).with_suffix('').as_posix()}".replace(
                "/", "."
            )
        )
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ClassDef) and any(
                isinstance(item, ast.AsyncFunctionDef) and item.name == "_query"
                for item in node.body
            ):
                names.append((module_path, node.name))
    return [
        (module_path, cast("type", getattr(importlib.import_module(module_path), class_name)))
        for module_path, class_name in names
    ]


_QUERY_SEAMS = [
    pytest.param(module_path, seam, id=seam.__name__)
    for module_path, seam in _discover_query_seams()
]


def _construct(seam: type) -> Any:
    """Build ``seam`` from :data:`_CTOR_VALUES`, supplying only its REQUIRED parameters."""
    signature = inspect.signature(cast("Any", seam))
    required = [
        name
        for name, parameter in signature.parameters.items()
        if name != "self" and parameter.default is inspect.Parameter.empty
    ]
    unknown = [name for name in required if name not in _CTOR_VALUES]
    assert not unknown, (
        f"{seam.__name__} requires constructor parameter(s) {unknown} that this contract "
        f"does not know how to supply. Add them to _CTOR_VALUES — do NOT drop the seam "
        f"from the suite. A single-statement seam that quietly falls out of the "
        f"enumeration is finding #120 with a fresh coat of paint."
    )
    return seam(**{name: _CTOR_VALUES[name] for name in required})


def _seam_on(seam: type, connection: Any) -> Any:
    """A live instance of ``seam`` whose cached connection IS ``connection``."""
    instance = _construct(seam)
    instance._connection = connection
    return instance


# The REAL SDK connection classes. Enumerated from the SDK, never hand-listed — the
# runtime guard wraps every public coroutine on each (33 today), so a method the SDK adds
# tomorrow is covered without anyone editing anything.
_SDK_CONNECTION_CLASSES = (
    AsyncWsSurrealConnection,
    AsyncHttpSurrealConnection,
    AsyncEmbeddedSurrealConnection,
)


def _construct_live(seam: type, env: SurrealEnv) -> Any:
    """Build ``seam`` pointed at a REAL database."""
    live_values = dict(_CTOR_VALUES)
    live_values.update(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
        dim=env.dim,
    )
    signature = inspect.signature(cast("Any", seam))
    required = [
        name
        for name, parameter in signature.parameters.items()
        if name != "self" and parameter.default is inspect.Parameter.empty
    ]
    return seam(**{name: live_values[name] for name in required})


# The controls point the guard's notion of "production" at THIS FILE, so a call made from
# a test function is treated exactly as a production call would be. The guard's logic is
# untouched — only its root moves. This is what lets the controls fire identically on the
# unrepaired tree AND on a correct build: pinning them to real production code would make
# the positive control go silently vacuous the moment the repair lands, which is precisely
# the kind of instrument that stops discriminating without telling anyone.
#
# DERIVED FROM A CODE OBJECT, NOT FROM ``__file__`` (finding #136). The guard classifies a
# frame by its ``co_filename``, so a root it is compared against must be minted from the
# same string the interpreter puts in a frame. ``__file__`` is a DIFFERENT answer to a
# similar-looking question, and in an out-of-tree copy the two diverge: pytest sets
# ``__file__`` from the copy's path while the module runs bytecode cached under the
# original path (``cp -a`` preserves mtimes, so the stale ``__pycache__`` is reused and its
# code objects carry the ORIGINAL ``co_filename``). The controls staged their escape, the
# guard could not see the file it came from, and they went RED beside a GREEN "no escapes".


def _a_function_defined_in_this_file() -> None:
    """A WITNESS, and nothing else: its ``__code__.co_filename`` is this file exactly as a
    stack frame reports it. The controls hand it to the guard so the guard can prove, at
    arm time, that it can actually SEE the code it is about to be asked to judge.
    """


_THIS_FILE_ROOT = _witness_file(_a_function_defined_in_this_file).parent


class TestTheSeamEnumerationIsHonest:
    """The control on the instrument. Everything below is parametrised over a DISCOVERED
    list, and a parametrised suite over an empty list is vacuously, silently green — the
    signature failure of every "mechanical" gate ever written.
    """

    def test_the_scan_finds_every_known_single_statement_seam(self) -> None:
        found = [seam.__name__ for _, seam in _discover_query_seams()]

        assert len(found) >= _MIN_KNOWN_SEAMS, (
            f"the scan found only {len(found)} classes owning an `async def _query` "
            f"({found}) — this contract was written against {_MIN_KNOWN_SEAMS}. Either "
            f"seams were consolidated (good — lower this floor deliberately, in a diff a "
            f"reviewer can see) or the SCANNER broke and every pin below just went "
            f"vacuously green."
        )

    def test_every_discovered_seam_can_be_constructed(self) -> None:
        """A seam that cannot be built is a seam that silently escapes every pin."""
        for _, seam in _discover_query_seams():
            assert _construct(seam) is not None


# ===========================================================================
# 1. THE DRIVER ITSELF.
#
# Every pin here is red today with an ImportError naming ``retry_on_conflict`` /
# ``RetryableConflictSignal`` — the names do not exist yet. The pins that follow
# (sections 2-6) are behaviourally red against the real, unrepaired code.
# ===========================================================================


class TestRetryOnConflictDriver:
    """One driver owns attempt counting, the give-up predicate, the fresh per-attempt
    jitter and the typed exhaustion error. Nothing else in the package may.
    """

    async def test_a_successful_attempt_returns_its_value_and_never_sleeps(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The driver is TRANSPARENT on the happy path — it is wrapped around every
        query in the store, so a stray sleep or a mangled return value would tax the
        entire read path.
        """
        recorder = _silence_sleep(monkeypatch)
        calls = 0

        async def _attempt() -> str:
            nonlocal calls
            calls += 1
            return "minted-7"

        assert await _driver()(_attempt) == "minted-7"
        assert calls == 1
        assert recorder.durations == [], "the happy path must never back off"

    async def test_the_signal_is_retried_until_the_attempt_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two conflicts then success: the driver RETURNS the third attempt's value.

        A driver that returns ``None`` after a retry (the shape ``execute_transaction``
        gets away with, because it returns ``None`` anyway) would silently destroy the
        mint — the version the caller needs is the attempt's RETURN VALUE.
        """
        recorder = _silence_sleep(monkeypatch)
        attempts = 0

        async def _attempt() -> int:
            nonlocal attempts
            attempts += 1
            if attempts <= 2:
                raise _signal()()
            return 3

        assert await _driver()(_attempt) == 3
        assert attempts == 3
        assert len(recorder.durations) == 2, "one backoff between each pair of attempts"

    async def test_sustained_conflict_raises_the_typed_error_and_the_signal_never_escapes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _silence_sleep(monkeypatch)
        attempts = 0

        async def _attempt() -> None:
            nonlocal attempts
            attempts += 1
            raise _signal()()

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await _driver()(_attempt)

        error = exc_info.value
        assert isinstance(error, SurrealStoreError), (
            "the typed error must keep subclassing SurrealStoreError — every existing "
            "`except SurrealStoreError` still has to catch it"
        )
        assert not isinstance(error, _signal()), "the signal is internal; it must never escape"
        assert error.attempts == attempts == _TXN_CONFLICT_ATTEMPT_CEILING
        assert str(error.attempts) in str(error), (
            "the message must be DERIVED from the attributes, never restated beside them"
        )
        assert error.elapsed_seconds >= 0.0

    @pytest.mark.parametrize(
        "error",
        [
            pytest.param(SurrealStoreError("assert violation"), id="domain-rejection"),
            pytest.param(SurrealConnectionError("socket died"), id="TRANSPORT-fault"),
            pytest.param(ValueError("a bug in the attempt itself"), id="arbitrary-exception"),
        ],
    )
    async def test_anything_that_is_not_the_signal_propagates_with_zero_retries(
        self, monkeypatch: pytest.MonkeyPatch, error: BaseException
    ) -> None:
        """THE AT-MOST-ONCE PIN, and the reason this driver keys on a SIGNAL rather
        than on ``except SurrealStoreError``.

        A conflict is safe to retry because the engine PROVED the statement did not
        commit. A TRANSPORT fault proves nothing of the kind: the socket may well have
        died AFTER the write landed, with only the acknowledgement lost. Retrying THAT
        double-applies — a retry loop that catches ``SurrealStoreError`` (or, worse,
        ``Exception``) is a data-corruption bug wearing a resilience costume.

        A domain rejection must not be retried either: it can never succeed, and
        hammering the engine with a write it has already refused is the other failure
        mode of a too-broad ``except``.
        """
        recorder = _silence_sleep(monkeypatch)
        attempts = 0

        async def _attempt() -> None:
            nonlocal attempts
            attempts += 1
            raise error

        with pytest.raises(type(error)) as exc_info:
            await _driver()(_attempt)

        assert exc_info.value is error, "the driver must propagate the ORIGINAL error object"
        assert attempts == 1, f"{type(error).__name__} was RETRIED — it must never be"
        assert recorder.durations == []

    async def test_the_attempt_floor_survives_a_deadline_shorter_than_one_attempt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """audit-102 B1, now owned by the driver: a deadline may BOUND retries; it may
        never VETO the floor.

        A wall-clock budget smaller than a single attempt's own execution time is
        incoherent as a retry budget — pre-#102 every caller got five attempts
        regardless of wall time, and a bulk apply measured at 9.56s against a 2.0s
        deadline would otherwise get a retry budget of ZERO.
        """
        _silence_sleep(monkeypatch)
        attempts = 0

        async def _attempt() -> None:
            nonlocal attempts
            attempts += 1
            raise _signal()()

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await _driver()(_attempt, deadline_seconds=0.0)

        assert attempts == _MAX_TXN_CONFLICT_ATTEMPTS, (
            f"a zero deadline cut the retry budget to {attempts} attempts — the floor "
            f"({_MAX_TXN_CONFLICT_ATTEMPTS}) is the pre-#102 guarantee every caller had "
            f"before the deadline existed at all, and the deadline may not veto it"
        )
        assert exc_info.value.attempts == _MAX_TXN_CONFLICT_ATTEMPTS

    async def test_the_ceiling_stops_a_runaway_even_under_an_effectively_infinite_deadline(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The structural backstop: a pathological run of near-zero jitter draws must
        not spin forever inside a generous deadline.
        """
        _silence_sleep(monkeypatch)
        attempts = 0

        async def _attempt() -> None:
            nonlocal attempts
            attempts += 1
            raise _signal()()

        with pytest.raises(TxnContentionExhaustedError):
            await _driver()(_attempt, deadline_seconds=1e9)

        assert attempts == _TXN_CONFLICT_ATTEMPT_CEILING

    async def test_the_default_deadline_is_read_at_call_time(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``deadline_seconds=None`` resolves the MODULE constant when the call is
        made — not when the function was defined.

        Contract requirement, not decoration (module docstring, requirement 1): both
        single-statement callers pass no deadline, so a default frozen at import leaves
        their deadline branch unreachable by every test that will ever be written.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        attempts = 0

        async def _attempt() -> None:
            nonlocal attempts
            attempts += 1
            raise _signal()()

        with pytest.raises(TxnContentionExhaustedError):
            await _driver()(_attempt)

        assert attempts == _MAX_TXN_CONFLICT_ATTEMPTS, (
            "the driver ignored the patched module default — the deadline was frozen "
            "into a default argument at import, so no test can ever reach the deadline "
            "branch of the callers that pass no deadline"
        )

    async def test_every_attempt_draws_a_fresh_backoff_from_the_shared_jitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The jitter lives IN the driver — one draw per retry, with a 1-based,
        MONOTONICALLY GROWING attempt number (the exponential window's input).

        A build that draws once and reuses it, or hands the same attempt number every
        time (a flat window), is caught here; the DISTRIBUTION itself is pinned by the
        existing sequential + concurrent backoff families in test_surreal_store.py, and
        those must stay green.
        """
        _silence_sleep(monkeypatch)
        recorder = _record_shared_jitter(monkeypatch)

        async def _attempt() -> None:
            raise _signal()()

        with pytest.raises(TxnContentionExhaustedError):
            await _driver()(_attempt, deadline_seconds=1e9)

        assert recorder.draws == list(range(1, _TXN_CONFLICT_ATTEMPT_CEILING)), (
            f"expected one FRESH draw after every failed attempt but the last "
            f"(1-based, growing): got {recorder.draws[:8]}..."
        )


# ===========================================================================
# 2. FINDING #120 — EVERY single-statement seam must RETRY. All TEN of them.
#
# RED today in all ten: a retryable write-write conflict raises on its FIRST occurrence.
# (``briefs.py`` is no exception — its retry sits ABOVE ``_query``, in the mint's own
# loop, so its ``_query`` is as unprotected as the other nine. That is precisely how a
# hand-rolled fix leaves the seam it was hand-rolled around still broken.)
#
# Every pin in this section is parametrised over the DISCOVERED seams, so an eleventh
# clone is pinned the day it is written, by nobody's memory.
# ===========================================================================


class TestEverySingleStatementSeamRetriesAConflict:
    """The retry belongs to the SEAM, not to one caller that happened to notice.

    THE WRONG BUILD THIS CATCHES, named because a cold adversary will build it: a repair
    that routes ``surreal.py`` and ``briefs.py`` — the two the brief named — and leaves
    the other eight raising on first conflict. It passes every pin a hand-listed contract
    would have contained, ships, and #120 stays live in eight modules that have just been
    told they are fixed.
    """

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_a_retryable_conflict_is_retried_and_the_statement_succeeds(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        """RED today, ×10: raises ``SurrealStoreError('… (retryable conflict) …')`` on
        the first conflict, having made exactly one attempt.
        """
        _silence_sleep(monkeypatch)
        connection = _ConflictingConnection(conflicts=3, rows=[{"next": 4}])
        instance = _seam_on(seam, connection)

        result = await instance._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        assert result == [{"next": 4}]
        assert connection.calls == 4, (
            f"{seam.__name__}._query retried the conflict {connection.calls - 1} times — "
            f"a retryable write-write conflict must be retried transparently, in EVERY "
            f"single-statement seam (finding #120). This one is in {module_path}."
        )
        assert connection.dropped == 0, (
            "a conflict tore down a HEALTHY connection — only a transport fault self-heals"
        )
        assert instance._connection is connection, (
            "the cached handle was replaced across a conflict retry"
        )

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_sustained_conflict_raises_the_TYPED_error_not_a_bare_store_error(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        """Exhaustion raises ``TxnContentionExhaustedError`` — the SAME type the
        transactional path raises, from EVERY seam.

        CATCHES THE SWALLOW-AND-RELABEL BUILD: one that wraps ``_query`` in a loop and
        re-raises the classified ``SurrealStoreError``. It passes "it retried" and fails
        here — a caller can only tell exhausted contention from a lost compare-and-set by
        TYPE, and finding #102 is the record of what happens when it has only prose.
        """
        _silence_sleep(monkeypatch)
        connection = _ConflictingConnection(conflicts=None)
        instance = _seam_on(seam, connection)

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await instance._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        error = exc_info.value
        assert error.attempts == connection.calls, (
            f"{seam.__name__}'s error reports {error.attempts} attempts; the engine was "
            f"asked {connection.calls} times"
        )
        assert connection.calls >= 2, "a conflict must be RETRIED before it is given up on"
        assert _LIVE_CONFLICT_TEXT not in str(error), (
            "ledger #31: the raised message must never echo the raw engine text"
        )

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_the_seam_backs_off_through_the_SHARED_jitter(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        """**THE DISCRIMINATING PIN, now ten times over** (lead's requirement 2).

        CATCHES THE TEN-PRIVATE-COPIES BUILD: ten seams that each retry, each back off,
        each raise the typed error — and each hand-roll the mechanics. It satisfies every
        behavioural pin above and is not DRY at all; it is finding #102 industrialised.

        The recorder is a MUTATION of the shared jitter. A seam that does not route
        through it is UNCHANGED by mutating it — which is the definition of not sharing
        it. Its positive control is
        ``TestBriefMintSharesTheDriver::test_the_shared_jitter_recorder_can_actually_see_a_draw``.
        """
        _silence_sleep(monkeypatch)
        recorder = _record_shared_jitter(monkeypatch)
        connection = _ConflictingConnection(conflicts=3, rows=[{"next": 4}])

        await _seam_on(seam, connection)._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        assert recorder.draws, (
            f"{seam.__name__}._query ({module_path}) backed off WITHOUT calling the "
            f"shared jitter — it is hand-rolling its own. Ten seams that each own a "
            f"private copy of the retry mechanics are not DRY; they are finding #102, "
            f"ten times, each free to get the jitter wrong in its own way (findings did: "
            f"16 slots; briefs did: 4)."
        )

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    @pytest.mark.parametrize(("build_error", "is_domain"), _NON_CONFLICT_REJECTIONS)
    async def test_a_non_conflict_rejection_is_raised_immediately_with_zero_retries(
        self,
        monkeypatch: pytest.MonkeyPatch,
        build_error: Callable[[], BaseException],
        is_domain: bool,
        module_path: str,
        seam: type,
    ) -> None:
        """THE OVERCORRECTION PIN, across every live rejection shape × every seam.

        A domain rejection can never succeed on retry; a TRANSPORT fault may already have
        COMMITTED (the driver's at-most-once rule). Both must surface on the FIRST
        occurrence, unretried — and the transport one must still self-heal and still
        raise ``SurrealConnectionError``, exactly as all ten do today.

        Green today (no seam retries anything), so it is MUTATION-PROVEN rather than
        merely asserted: see the report's §C.1/C.1b.
        """
        recorder = _silence_sleep(monkeypatch)
        connection = _RejectingConnection(build_error())
        instance = _seam_on(seam, connection)
        expected = SurrealStoreError if is_domain else SurrealConnectionError

        with pytest.raises(expected) as exc_info:
            await instance._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        assert connection.calls == 1, (
            f"{seam.__name__} retried a "
            f"{'domain rejection' if is_domain else 'TRANSPORT fault'} "
            f"{connection.calls - 1} times"
        )
        assert recorder.durations == []
        assert not isinstance(exc_info.value, TxnContentionExhaustedError), (
            "a non-conflict rejection was reported as exhausted CONTENTION — a caller "
            "that retries on that type will now hammer a write that can never succeed"
        )
        if is_domain:
            assert isinstance(exc_info.value, SurrealStoreError)
            assert not isinstance(exc_info.value, SurrealConnectionError), (
                "a domain rejection threw away a perfectly healthy connection"
            )
            assert _SENSITIVE_MARKER not in str(exc_info.value), (
                "ledger #31: the raised message echoed the bound value back verbatim"
            )
        else:
            assert instance._connection is None, (
                "a transport fault must drop the cached handle so the next call reconnects"
            )


class TestDetectionFollowsTheOneSharedMarker:
    """**BLOCKER 1, closed.** Eleven callers must agree on what a conflict IS — and
    "agree" is proven by MOVING the definition and watching them all follow.

    THE WRONG BUILD (the adversary built it; it scored 839 passed / 0 failed / ruff
    clean / mypy 0): every seam routes through the shared driver for POLICY and matches
    ``"Resource busy"`` in the engine text LOCALLY for DETECTION. Reword the engine's
    message and all ten stop retrying, silently. That is the #93 → #102 coupling, eleven
    times over, inside the fix for #102.

    Both directions are needed, and each kills a different build:

      * the NEW marker must START being a conflict — kills a seam matching any private
        substring of the OLD message (it cannot see the new words at all);
      * the OLD text must STOP being a conflict — kills a seam matching any private
        substring of the old message (it keeps retrying words the authority abandoned).

    A seam that reads the shared marker passes both. A seam with its own copy of the
    prose fails both. There is no third build.
    """

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_the_new_marker_starts_being_a_conflict(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        _silence_sleep(monkeypatch)
        _mutate_shared_marker(monkeypatch)
        connection = _ScriptedConnection(error=_mutated_conflict_error(), failures=3)

        result = await _seam_on(seam, connection)._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        assert result == [{"next": 4}]
        assert connection.calls == 4, (
            f"{seam.__name__}._query did NOT retry a conflict the shared marker now "
            f"names ({connection.calls} attempt(s)). It is matching engine prose of its "
            f"OWN — so it cannot see a conflict the ONE authority recognises. Detection "
            f"has to live in one place for the same reason policy does."
        )

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_the_old_text_stops_being_a_conflict(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        """THE KILLER. WB-PROSE passes the pin above (its private ``"Resource busy"``
        match happens to be absent from the mutated text only if the fixture is chosen
        carelessly) — but it can NEVER pass this one: it keeps retrying a message the
        shared authority has stopped calling a conflict.
        """
        _silence_sleep(monkeypatch)
        _mutate_shared_marker(monkeypatch)
        connection = _ScriptedConnection(error=_conflict_error(), failures=None)

        with pytest.raises(SurrealStoreError) as exc_info:
            await _seam_on(seam, connection)._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        assert connection.calls == 1, (
            f"{seam.__name__}._query retried {connection.calls - 1} times on a message "
            f"the shared marker NO LONGER recognises as a conflict — it is branching on "
            f"engine prose it keeps privately. Reword the engine and this seam's retry "
            f"dies silently: that is finding #102, and this is the fix for finding #102."
        )
        assert not isinstance(exc_info.value, TxnContentionExhaustedError), (
            "a non-conflict was reported as exhausted contention"
        )

    async def test_the_transactional_caller_follows_the_marker_too(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """POSITIVE CONTROL — the instrument must be shown MOVING something.

        ``execute_transaction`` has always read the shared marker (via
        ``_rollback_verdict``), so mutating the marker MUST change its behaviour in both
        directions. If this went red, the monkeypatch would not be reaching detection at
        all and every verdict above would be worthless.
        """
        _silence_sleep(monkeypatch)
        _mutate_shared_marker(monkeypatch)

        # The NEW marker is now a conflict: retried, then succeeds.
        mutated = _ConflictingConnection(conflicts=2)
        mutated.conflict_text = _MUTATED_CONFLICT_TEXT
        await _run_execute_transaction(mutated)
        assert mutated.calls == 3, "the transactional seam did not follow the moved marker"

        # The OLD text is no longer a conflict: raised immediately, unretried.
        stale = _ConflictingConnection(conflicts=None)
        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_execute_transaction(stale)
        assert stale.calls == 1
        assert not isinstance(exc_info.value, TxnContentionExhaustedError)


class TestTheRetryIsNotGatedOnTheStatementShape:
    """The statement text is a VALUE the code can branch on — so at least one pin uses a
    DIFFERENT value (this repo's own law, and the exact fixture monoculture that let C1's
    self-ack defect pass an entire contract).

    CATCHES: a build that retries only what LOOKS like a write (``UPSERT``/``CREATE``/…)
    and leaves reads — or any shape its author did not picture — unretried.

    Driven through ONE seam deliberately: the ten share a single driver (pinned by
    identity in :class:`TestEverySeamHoldsTheOneDriver`), so a shape heuristic can only
    live in the driver or in one seam's detection — and both are reachable from here.
    Running 5 shapes × 10 seams would be 50 tests that all re-prove the same branch.
    """

    @pytest.mark.parametrize(
        "statement",
        [
            pytest.param(_MINT_STATEMENT, id="UPSERT-mint"),
            pytest.param("CREATE brief CONTENT $content", id="CREATE"),
            pytest.param("UPDATE brief_counter SET next -= 1 WHERE next = $version", id="UPDATE"),
            pytest.param("DELETE chunk WHERE tier = $tier", id="DELETE"),
            pytest.param("SELECT * FROM brief WHERE name = $name", id="SELECT"),
        ],
    )
    async def test_every_statement_shape_is_retried_alike(
        self, monkeypatch: pytest.MonkeyPatch, statement: str
    ) -> None:
        _silence_sleep(monkeypatch)
        connection = _ConflictingConnection(conflicts=3, rows=[{"next": 4}])

        result = await _store_on(connection)._query(statement, {"name": _WAVE_NAME})

        assert result == [{"next": 4}]
        assert connection.calls == 4, (
            f"a conflict on {statement.split(maxsplit=1)[0]} was not retried — the retry is gated "
            f"on the STATEMENT TEXT. A conflict is a fact about the engine's commit, not "
            f"about the verb the caller happened to use."
        )


# ===========================================================================
# 3. FINDING #108 — briefs SHARES the driver. Not a private copy of it.
# ===========================================================================


class TestBriefMintSharesTheDriver:
    """``briefs.py`` deletes its loop, its 4-slot jitter and its budget constants, and
    CALLS the shared driver.

    A build that keeps a private copy passes every "does briefs still work?" pin ever
    written — including its own 8-way race. These are the pins it cannot pass.
    """

    async def test_the_mint_backs_off_through_the_SHARED_jitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """THE DISCRIMINATING PIN (brief §3): a mutation to the SHARED jitter must turn
        briefs' mint RED.

        RED today: the mint sleeps ``backoff + jitter_slot * 0.001``, drawn from its OWN
        4-slot table (``uuid4().hex[:4] % 4``) — the shared jitter is never called, so
        the recorder sees ZERO draws.

        The recorder is a MUTATION of the shared function: if briefs' retry does not
        route through it, briefs' behaviour is unchanged by mutating it. That is the
        definition of "not sharing it".
        """
        _silence_sleep(monkeypatch)
        recorder = _record_shared_jitter(monkeypatch)
        connection = _ConflictingConnection(conflicts=3, rows=[{"next": 4}])
        ledger = _ledger_on(connection)

        version = await ledger._mint_version(_WAVE_NAME)

        assert version == 4
        assert connection.calls == 4, "the mint did not retry the conflict"
        assert recorder.draws, (
            "the brief mint backed off WITHOUT calling the shared jitter — it is "
            "hand-rolling its own. A private copy of a retry policy is exactly what "
            "findings #102 and #108 are, one clone each."
        )

    async def test_the_shared_jitter_recorder_can_actually_see_a_draw(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """POSITIVE CONTROL for the pin above — this repo's law: "pair every negative
        result with a positive control showing the probe firing on a case you know is
        broken."

        The instrument is proven capable of observing a draw by pointing it at the
        caller that HAS always used the shared jitter (``execute_transaction``). If this
        is green and the pin above is red, briefs genuinely is not sharing. If BOTH go
        red, the instrument is blind and the verdict above means nothing.
        """
        _silence_sleep(monkeypatch)
        recorder = _record_shared_jitter(monkeypatch)
        connection = _ConflictingConnection(conflicts=2)

        await _run_execute_transaction(connection)

        assert recorder.draws == [1, 2], (
            "the shared-jitter recorder did not observe execute_transaction's own "
            "backoffs — the instrument is blind, so it can prove nothing about briefs"
        )

    async def test_the_mint_gives_up_with_the_TYPED_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sustained contention out of ``publish()`` is ``TxnContentionExhaustedError``.

        RED today: the mint raises ``BriefLedgerError('failed to mint a version ... after
        20 attempts')`` — a message, not a type. It is the LAST production site that
        branches on an exception's prose, and this is the pin that ends it.
        """
        _silence_sleep(monkeypatch)
        connection = _ConflictingConnection(conflicts=None)
        ledger = _ledger_on(connection)

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await ledger.publish(_WAVE_NAME, "a standing instruction", created_by="lead")

        assert exc_info.value.attempts == connection.calls
        assert _LIVE_CONFLICT_TEXT not in str(exc_info.value)

    async def test_exhausted_contention_on_the_CREATE_still_burns_no_version(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**REMOVED-BEHAVIOUR PRESERVATION** — the compensating half of the mint/CREATE
        split, adjudicated *preserved-with-pin* and pinned here because nothing pinned it
        before.

        ``publish()`` mints a version, then CREATEs the row. If the CREATE is REJECTED it
        hands the number back (``_release_version``, a GUARDED decrement) so a failed
        publish burns no version. The existing pin covers a DOMAIN rejection only.

        After this wave the CREATE can also fail with ``TxnContentionExhaustedError`` —
        which subclasses ``SurrealStoreError``, so the release path still runs. That is
        the behaviour, and it now has a witness: sustained contention on the CREATE
        leaves the counter where it was, so the NEXT publisher takes the same number
        rather than a burnt one.

        The wrong build this catches: a repair that catches the typed error ABOVE the
        release (or re-raises before it), silently reintroducing gapped versions under
        contention — invisible to every other pin in the tree.
        """
        _silence_sleep(monkeypatch)
        ledger = _ledger_on(_ConflictingConnection(conflicts=0, rows=[{"next": 1}]))
        minted = await ledger._mint_version(_WAVE_NAME)
        assert minted == 1

        released: list[tuple[str, int]] = []

        async def _capture_release(name: str, version: int) -> None:
            released.append((name, version))

        monkeypatch.setattr(ledger, "_release_version", _capture_release)

        async def _exhausted(*args: Any, **kwargs: Any) -> None:
            raise TxnContentionExhaustedError("busy", attempts=64, elapsed_seconds=2.0)

        monkeypatch.setattr(briefs_module, "execute_transaction", _exhausted)

        with pytest.raises(TxnContentionExhaustedError):
            await ledger.publish(_WAVE_NAME, "a body", created_by="lead")

        assert released, (
            "a publish whose CREATE died of exhausted contention did NOT hand its version "
            "back — the number is burnt and the brief's versions are no longer gapless. "
            "TxnContentionExhaustedError subclasses SurrealStoreError precisely so this "
            "path keeps working; a handler that catches it ABOVE the release breaks it."
        )

    def test_briefs_no_longer_sleeps_at_all(self) -> None:
        """STRUCTURAL: the hand-rolled loop is GONE, not merely bypassed.

        ``briefs.py``'s only ``asyncio.sleep`` was the mint's own backoff (briefs.py:681).
        A build that calls the shared driver AND leaves a private loop behind ships two
        retry policies and a doc-shaped invitation to clone the wrong one — the exact
        way ``DESIGN-LAW.md:75`` produced findings #102 and #108.
        """
        source = (_PACKAGE_ROOT / "briefs.py").read_text(encoding="utf-8")

        assert "asyncio.sleep" not in source, (
            "briefs.py still sleeps — the hand-rolled retry loop was not deleted. The "
            "driver owns the backoff now; there must be nothing left to clone."
        )


# ===========================================================================
# 4. ONE POLICY, ONE DRIVER — for all ELEVEN callers.
#
# The ten discovered ``_query`` seams cannot diverge from ``execute_transaction``, or
# from each other, because after this wave none of them HAS a policy to diverge with.
# This is what makes DRY mechanical rather than aspirational: it is not enough that
# every seam retries; they must all retry the SAME WAY, through the SAME OBJECT.
# ===========================================================================


async def _seam_attempts_until_exhaustion(seam: type) -> int:
    connection = _ConflictingConnection(conflicts=None)
    with pytest.raises(TxnContentionExhaustedError):
        await _seam_on(seam, connection)._query(_MINT_STATEMENT, {"name": _WAVE_NAME})
    return connection.calls


async def _txn_attempts_until_exhaustion() -> int:
    connection = _ConflictingConnection(conflicts=None)
    with pytest.raises(TxnContentionExhaustedError):
        await _run_execute_transaction(connection)
    return connection.calls


class TestEveryCallerRunsTheSameRetryPolicy:
    """ELEVEN callers — the ten discovered ``_query`` seams plus ``execute_transaction``
    — and not one of them may carry a budget of its own.

    Both budget BOUNDARIES are driven through every caller, on the DEFAULT deadline
    (which is what production runs on: no caller passes one):

      * default deadline -> 0.0  ⇒ the FLOOR governs   ⇒ exactly _MAX_TXN_CONFLICT_ATTEMPTS
      * default deadline -> 1e9  ⇒ the CEILING governs ⇒ exactly _TXN_CONFLICT_ATTEMPT_CEILING

    A private 20-attempt budget (briefs today) reports 20 in BOTH. A caller passing its
    own deadline reports the ceiling in the floor case. A caller with no retry at all
    (nine seams today) reports 1 in both. The constants are IMPORTED, never spelled — the
    survey is free to re-measure them; what it may not do is let one caller diverge.
    """

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_the_floor_governs_identically_for_every_seam(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)

        attempts = await _seam_attempts_until_exhaustion(seam)

        assert attempts == _MAX_TXN_CONFLICT_ATTEMPTS, (
            f"{seam.__name__}._query made {attempts} attempts under an exhausted "
            f"deadline; every caller gets the seam's floor ({_MAX_TXN_CONFLICT_ATTEMPTS}) "
            f"and none may carry a budget of its own"
        )

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_the_ceiling_governs_identically_for_every_seam(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 1e9)

        attempts = await _seam_attempts_until_exhaustion(seam)

        assert attempts == _TXN_CONFLICT_ATTEMPT_CEILING, (
            f"{seam.__name__}._query made {attempts} attempts against a deadline it can "
            f"never reach; every caller stops at the seam's ceiling "
            f"({_TXN_CONFLICT_ATTEMPT_CEILING})"
        )

    async def test_the_transactional_caller_obeys_the_same_two_boundaries(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``execute_transaction`` is the ELEVENTH caller, and it is held to the same
        budget as the ten — otherwise the seam has two policies and the extraction
        achieved nothing.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        assert await _txn_attempts_until_exhaustion() == _MAX_TXN_CONFLICT_ATTEMPTS

        _set_default_deadline(monkeypatch, 1e9)
        assert await _txn_attempts_until_exhaustion() == _TXN_CONFLICT_ATTEMPT_CEILING

    async def test_the_brief_mint_obeys_them_too_end_to_end(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """And through ``publish()`` — the real production hot-row mint, whose own
        20-attempt budget is the thing being deleted.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _ConflictingConnection(conflicts=None)

        with pytest.raises(TxnContentionExhaustedError):
            await _ledger_on(connection).publish(_WAVE_NAME, "body", created_by="lead")

        assert connection.calls == _MAX_TXN_CONFLICT_ATTEMPTS, (
            f"publish() made {connection.calls} attempts — briefs' private 20-attempt "
            f"budget is still in there"
        )


# The shared names a seam may legitimately hold from ``_txn``. WHICH of them a seam holds is
# the COLLAPSE's business (§7d moves the attempt body into ``run_query``, so the seams'
# direct ``retry_on_conflict`` import goes unused and ruff's F401 DEMANDS its deletion);
# which OBJECT each one is, and whether the driver is REACHED, is this pin's business.
_SHARED_SEAM_NAMES = ("retry_on_conflict", "run_query")


def _spy_the_driver(monkeypatch: pytest.MonkeyPatch, *modules: Any) -> list[object]:
    """Spy ``retry_on_conflict`` at EVERY binding a seam could reach it through.

    C-DEF-2 (contract adversary): a spy installed only on the SEAM MODULE's binding sees
    nothing after the §7d collapse — ``_query`` then calls ``_txn.run_query``, which resolves
    ``retry_on_conflict`` in ``_txn``'s OWN namespace. A spy installed only on ``_txn``'s
    binding sees nothing BEFORE the collapse, for the mirror reason. Patching both makes the
    pin world-agnostic: it asks "was the ONE driver reached?", which is the actual property,
    instead of "was this particular name looked up?", which is an implementation detail that
    the fix is *supposed* to change.
    """
    real = _driver()
    spied: list[object] = []

    async def _spy(attempt: Any, **kwargs: Any) -> Any:
        spied.append(attempt)
        return await real(attempt, **kwargs)

    monkeypatch.setattr(txn_module, "retry_on_conflict", _spy)
    for module in modules:
        if getattr(module, "retry_on_conflict", None) is not None:
            monkeypatch.setattr(module, "retry_on_conflict", _spy)
    return spied


class TestEverySeamHoldsTheOneDriver:
    """THE DRY PIN, structurally — and it is an IDENTITY check, not a name check.

    THE WRONG BUILD THIS EXISTS FOR (and a cold adversary WILL build it): ten modules
    that each define their own ``retry_on_conflict`` (or ``run_query``), or bind the name to
    a local re-implementation. Every behavioural pin passes. Every module "has" the shared
    thing. The spy sees calls. And there are ten private copies wearing one name — which is
    finding #102's clone problem with a coat of DRY paint.

    ``module.<name> is _txn.<name>`` cannot be faked by a copy. A copy is a different object.

    The spy then proves the seam actually REACHES THE DRIVER (a module can import a name and
    still hand-roll a loop). Both halves are needed: identity without the spy proves it is
    imported and unused; the spy without identity proves it calls *something* by that name.

    **RESHAPED for the collapsed world (C-DEF-2, contract adversary).** The old pin asserted
    that each seam module holds AND CALLS ``retry_on_conflict`` *through its own binding*.
    After §7d that is false on a CORRECT build, in both shapes a builder can ship: keep the
    now-unused import and the spy never fires (and ruff reports 64 × F401); delete it, as ruff
    demands, and the ``is not None`` assert fires. **The builder could satisfy it only by
    contorting production — a redundant per-seam wrapper that exists to please a spy — or by
    editing a test it is forbidden to touch.** So the pin now asks the question it always
    meant: *whatever shared name this seam holds must BE the ``_txn`` object, and driving its
    ``_query`` must REACH THE ONE DRIVER.* True before the collapse, true after, and still
    fatal to a private copy.
    """

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_the_seam_calls_the_one_and_only_driver(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        _silence_sleep(monkeypatch)
        module = importlib.import_module(module_path)
        held = {
            name: getattr(module, name)
            for name in _SHARED_SEAM_NAMES
            if getattr(module, name, None) is not None
        }

        assert held, (
            f"{module_path} holds NONE of the shared seam names {list(_SHARED_SEAM_NAMES)} — "
            f"it cannot be calling shared code, so whatever retry {seam.__name__}._query "
            f"performs is its own private copy"
        )
        for name, obj in held.items():
            assert obj is getattr(txn_module, name), (
                f"{module_path}.{name} is NOT _txn.{name} — it is a different object wearing "
                f"the same name. A private copy passes every behavioural pin and shares "
                f"nothing; that is the defect this whole wave exists to delete, and identity "
                f"is the one thing a copy cannot fake."
            )

        spied = _spy_the_driver(monkeypatch, module)
        connection = _ConflictingConnection(conflicts=2, rows=[{"next": 3}])

        await _seam_on(seam, connection)._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        assert spied, (
            f"{seam.__name__}._query retried a conflict WITHOUT reaching retry_on_conflict — "
            f"it holds the shared names and hand-rolls the policy anyway. (The spy is armed "
            f"on BOTH _txn's binding and {module_path}'s, so neither the pre-collapse nor the "
            f"post-collapse call chain can slip past it.)"
        )
        assert connection.calls == 3, "the conflict was not retried to success"

    async def test_the_transactional_caller_holds_it_too(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``execute_transaction`` must not keep its own loop. A build that routes only
        the NEW callers is *looks-DRY*: two policies, one of them shared.
        """
        _silence_sleep(monkeypatch)
        real = getattr(txn_module, "retry_on_conflict", None)
        assert real is not None, "the driver does not exist"
        spied: list[object] = []

        async def _spy(attempt: Any, **kwargs: Any) -> Any:
            spied.append(attempt)
            return await real(attempt, **kwargs)

        monkeypatch.setattr(txn_module, "retry_on_conflict", _spy)
        connection = _ConflictingConnection(conflicts=2)

        await _run_execute_transaction(connection)

        assert spied, (
            "execute_transaction kept its own retry loop — the driver was extracted FROM "
            "it, and it must be the driver's first caller, not its exception"
        )


# ===========================================================================
# 4b. THE SEAM IS DEFINED BY THE SDK CALL — not by a method's NAME.
#
# **BLOCKER 2, closed.** My enumerator discovered classes owning an ``async def _query``.
# It found ten. It structurally COULD NOT find ``scout.py``, which calls
# ``connection.query(...)`` inline, owns no ``_query``, and runs a **compare-and-set
# WRITE** on the command table (scout.py:328) with no retry and a raw SDK ``QueryError``.
# On the CORRECT build it still raised on the first conflict: **#120 would have shipped
# alive, in a tree that had just been told it fixed #120.**
#
# The lesson is the one this session keeps re-learning: **a name is a PROXY for a
# property, and a proxy for a property is exactly what keeps failing us** — a name-based
# registry, a label literal, a `_query` spelling. So the gate enumerates the PROPERTY:
#
#     NO production code may call the SDK's query()/query_raw() outside the retry seam.
#
# An eleventh clone spelled ``_run``, or a bare inline call like scout's, is then caught
# BY CONSTRUCTION rather than by anyone's memory.
#
# WHAT COUNTS AS "INSIDE THE SEAM" — and this is mechanical, not a blessed-name list:
#   1. ``store/_txn.py`` — the seam itself.
#   2. An ATTEMPT BODY: a function whose name is handed to ``retry_on_conflict(...)``
#      somewhere in its own module. The gate READS that from the AST, so the builder may
#      call it whatever it likes; what it may not do is call the SDK from a function the
#      driver never runs.
# THERE IS NO THIRD CATEGORY. THE GATE HAS **ZERO ALLOWANCES**, and the story of why is
# the sixth hole I was told to go and find myself.
#
# My first draft of this gate granted ONE allowance: connection-bootstrap DDL (`DEFINE
# NAMESPACE` / `DEFINE DATABASE IF NOT EXISTS`), which every `_ensure_connection` runs on
# a virgin connection. It looked unimpeachable — idempotent DDL, run once, before the
# connection can address anything.
#
# It is the only place in the package where an SDK write is deliberately left unretried,
# so it is the only place a sixth defect could hide. I probed it
# (`scratchpad/contract-dry/probe_bootstrap_ddl_race.py`), 16 concurrent FIRST connects
# to a VIRGIN database, 10 rounds:
#
#     connects attempted : 160
#     failures           : 21          <- 21/160, in ONE run (see _UNRETRIED_BOOTSTRAP_LOSS:
#                                          re-measured, the rate ranges 6.2%-34.4%)
#     retryable conflicts: 21          <- ALL of them
#
#     SurrealConnectionError: could not connect to SurrealDB at 'ws://...':
#     Transaction conflict: Resource busy. This transaction can be retried
#
# **The bootstrap DDL conflicts, and it is MISCLASSIFIED as a transport fault** — the
# caller is told the server is unreachable when the server is perfectly reachable and
# merely busy. It is unretried (correctly, for a transport fault) and so it simply fails.
# That is a live #120 instance, in the one call site my own gate had blessed.
#
# WHY NO EXISTING PIN EVER SAW IT — and this is the lesson, not the bug: every live
# fixture in this repo (mine included) calls `connect_admin()` first, which CREATES the
# namespace and database. So every racer's `DEFINE ... IF NOT EXISTS` is a no-op on an
# object that already exists, and no-ops do not contend. **The pins passed for a FIXTURE
# reason.** I wrote 164 of them and my own 16-way concurrency fixture had this hole in it.
#
# So the allowance is gone: the bootstrap DDL routes through the seam like everything
# else, and `TestConcurrentFirstConnectsSurviveTheBootstrapRace` is its witness.
#
# ---------------------------------------------------------------------------
# THE GATE IS DENY-BY-DEFAULT ON THE **RECEIVER**, NOT AN ALLOWLIST OF METHOD NAMES.
#
# v2 of this gate enumerated the DANGEROUS methods: {query, query_raw, use}. The adversary
# broke it in one line — an unretried ``connection.upsert(...)`` write (**measured: 31
# retryable conflicts in 64 live attempts**) is INVISIBLE to a three-name allowlist and
# ships green. Its control settles it: the same write spelled ``connection.query()``
# fires the gate. Same defect, different method name.
#
# **THIS IS THE FOURTH TIME THIS SESSION THE SAME MISTAKE HAS BEEN MADE**, by four
# different instruments, each keyed on a NAME as a proxy for a PROPERTY:
#
#     the retry gate keyed on a label's LITERAL      -> defeated by a substring of it
#     the retired-symbol pin keyed on a symbol NAME  -> blind to a numeric claim
#     the seam enumerator keyed on `async def _query`-> blind to scout.py
#     the SDK gate keyed on 3 METHOD NAMES           -> blind to the other 30
#
# Every time, the fix was the same inversion, and every time it worked:
#
#     **STOP ENUMERATING THE DANGEROUS. ALLOWLIST THE SAFE.**
#
# The dangerous set is unbounded (33 SDK methods today, more in the next release, and the
# 25 nobody in this session has thought of). The SAFE set — what a caller may legitimately
# do to a live connection OUTSIDE a driver attempt — is small, enumerable, and probed.
# That asymmetry is the entire design. It is what finally killed the prose-branching arms
# race after three failed rounds; I wrote that sentence myself and then failed to apply it
# one section later.
#
# THE INVARIANT: no production code may call ANY method on a live SDK connection outside
# an attempt the driver runs — except the SAFE set below.
# ---------------------------------------------------------------------------

# THE SAFE SET — and it is TWO methods, because the burden of proof is on the ALLOWANCE.
#
#   * ``signin`` — PROBED across 256 concurrent virgin connects (probe_bootstrap_ddl_race
#     + the stage-by-stage probe): **zero conflicts**. It authenticates a socket; it
#     touches no row.
#   * ``close``  — tears the socket down. There is no statement and nothing left to
#     contend for.
#
# ⚠ ``kill`` AND ``subscribe_live`` ARE **NOT** IN THIS SET, AND THAT IS THE SEVENTH
# HOLE — I FOUND IT IN MY OWN ALLOWLIST. I had put ``kill`` here on the reasoning that
# "cancelling a LIVE subscription writes no row". That is an OPINION. It is the identical
# move that blessed the bootstrap DDL ("idempotent DDL cannot contend") — which then lost
# 6.2%-34.4% of concurrent virgin first-connects, on ``use()``, a call nobody
# suspected. I could not PROVE either is conflict-free, so under deny-by-default they route
# through the seam. One line each; the alternative is another lost tail of connects.
#
# **The burden of proof lives on the allowance, not on the gate.** Adding to this set is a
# diff a reviewer can see, and it needs a probe, not an argument.
_SAFE_CONNECTION_METHODS = frozenset({"signin", "close"})

# How a live connection ENTERS scope. Small and enumerable by construction — this is the
# receiver test, and it is the half of the gate that must be complete.
_CONNECTION_NAMES = frozenset({"connection", "conn"})
_SEAM_MODULE = "store/_txn.py"


def _is_connection_receiver(node: ast.expr) -> bool:
    """Is this expression a live SDK connection?

    ``ast.Name`` and ``ast.Attribute`` are tested by the SAME rule — ends with
    ``connection``, or is the short idiom ``conn``. The asymmetry this replaces was a
    real hole: ``self._connection`` (an ``Attribute``, matched by the suffix test) was
    caught while a plain local ``_connection`` (a ``Name``, tested against a two-item
    frozenset) was MISSED, so an entirely idiomatic private-local name evaded the scan
    that the identical attribute name could not (#150 audit R1b).

    ⚠ **STATED LIMIT, and it is why this predicate no longer gates the DDL leg.** This is
    syntactic, not type inference: a connection bound to any name not ending in
    ``connection`` is invisible here. The names measured sailing past it are not listed in
    this docstring — they are the non-control half of
    :meth:`TestTheTestTreeRoutesThroughTheOneBootstrapToo
    .test_the_DDL_leg_is_RECEIVER_BLIND_whatever_the_handle_is_called`'s parameter list,
    which is executable and cannot drift from a prose copy of itself. Receiver-name keying
    is the sixth entry in this repo's own table of instruments defeated by enumerating a
    NAME as a proxy for a PROPERTY. So the DDL leg of :func:`_executed_bootstrap_sites_in`
    is now RECEIVER-BLIND and does not call this at all; this predicate survives only on
    the ``use()`` leg, where the method name alone is too generic to deny on.
    """
    name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else None
    return name is not None and (name in _CONNECTION_NAMES or name.endswith("connection"))


def _driver_run_bodies(tree: ast.AST) -> tuple[set[str], set[int]]:
    """What the driver actually RUNS: ``(named attempt bodies, inline lambda node ids)``.

    Read out of every ``retry_on_conflict(...)`` call, so the builder names its own
    attempt body — a function the driver never runs cannot be blessed by what it is
    CALLED. Both idioms are recognised, because BOTH are correct and v2's gate
    false-flagged one of them:

        retry_on_conflict(self._attempt)                    # named
        retry_on_conflict(lambda: connection.query(stmt))   # inline lambda
    """
    named: set[str] = set()
    lambdas: set[int] = set()
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "retry_on_conflict"
        ):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Lambda):
                lambdas.add(id(inner))
            elif isinstance(inner, ast.Attribute):
                named.add(inner.attr)
            elif isinstance(inner, ast.Name):
                named.add(inner.id)
    return named, lambdas


def _enclosing_callable(node: ast.AST, parents: dict[int, ast.AST]) -> ast.AST | None:
    """The INNERMOST function/lambda a node sits in.

    v2 walked every FunctionDef and then walked its whole subtree — so a call inside a
    NESTED attempt closure was attributed to the OUTER function too, and the outer
    function is not blessed. That made the gate reject the idiomatic nested-closure
    caller: **a false positive on the CORRECT build.** A gate that fires on the right
    answer gets deleted by the first engineer it blocks, and then we have nothing.
    """
    current = parents.get(id(node))
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return current
        current = parents.get(id(current))
    return None


def _talks_to_surrealdb(tree: ast.AST) -> bool:
    """Does this module handle a SurrealDB connection at all?

    NOT scope creep — a NECESSARY narrowing, and my own gate found it: ``memory/ledger.py``
    and ``index/sqlite_resilient.py`` both hold a variable called ``connection`` and call
    ``.execute()`` / ``.commit()`` on it. **They are SQLite.** A gate that demands a
    SQLite cursor be retried on a SurrealDB conflict is crying wolf, and a gate that cries
    wolf gets deleted by the first engineer it blocks.

    A module handles a SurrealDB connection iff it imports ``surrealdb`` (it builds one)
    or ``loremaster.store._txn`` (it uses the seam's connection vocabulary). Every module
    in this package that touches the engine does one or both; neither SQLite module does
    either. STATED LIMIT: a module that only RECEIVES a connection and imports neither
    would be skipped — its caller is still gated, and closing that hole would need type
    inference this scan does not have.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.startswith("surrealdb") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith(("surrealdb", "loremaster.store._txn")):
                return True
    return False


# Exactly the methods the runtime guard wraps — read off the SDK classes, so this can never
# drift from what the guard actually watches. Public + async + not in the safe set.
_GUARDED_SDK_METHODS = frozenset(
    name
    for connection_class in _SDK_CONNECTION_CLASSES
    for name, function in inspect.getmembers(connection_class, inspect.isfunction)
    if not name.startswith("_")
    and name not in _SAFE_CONNECTION_METHODS
    and inspect.iscoroutinefunction(function)
)


def _all_sdk_call_sites() -> dict[str, str]:
    """**EVERY** call on a live connection in the package — ``{"file:line": "func:method"}``.

    THE **ALL** SET, AND THE DISTINCTION IS THE WHOLE BLOCKER. My v5 coverage pin built its
    enumeration from :func:`_unseamed_sdk_call_sites` — the **OFFENDERS** set, which is
    **empty by construction on any lint-clean build**. So the pin was STRICTLY DOMINATED by
    the lint: it could not fire on any build the lint passed, while its docstring promised
    *"a call site no test executes is NAMED … coverage stops being a hidden variable."*
    **That claim was false**, and `WB-ROUTED-UNDRIVEN` walked through it: a call routed
    through the driver but never CLASSIFYING, at a site no test executes. 199/0. 4375/0.
    Retries zero times. #120 alive again, one altitude up.

    This is the repo's own law breaking on me — **A DIAGNOSIS IS NOT AN INSTRUMENT.** I
    pinned the INSTANCE that killed v4 (scout's drain SELECT — and that pin works) and
    shipped a broken instrument for the CLASS. The instance was fixed; the class was not.

    Unlike the offenders set, this one includes call sites that are perfectly correct — a
    site INSIDE a driver attempt still has to be EXECUTED under the guard before anyone may
    claim the guard certifies it. Watched is not the same as well-formed, and neither is the
    same as unexamined.
    """
    sites: dict[str, str] = {}
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        key = path.relative_to(_PACKAGE_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if not _talks_to_surrealdb(tree):
            continue
        parents: dict[int, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[id(child)] = parent
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if not _is_connection_receiver(node.func.value):
                continue
            # Only methods the guard CAN observe. Derived from the SDK classes, never a
            # hand-list: the safe set is not wrapped, and neither are SYNC methods (the guard
            # wraps coroutines). ``check_response_for_error`` is exactly that — a sync
            # response check, in the source, on a connection, and unobservable by
            # construction. Without this filter the pin was RED on a CORRECT build for a
            # call the guard can never see: a permanently-red instrument is one nobody keeps.
            # The pin caught that on its own first run.
            if node.func.attr not in _GUARDED_SDK_METHODS:
                continue
            scope = _enclosing_callable(node, parents)
            where = getattr(scope, "name", "<lambda>") if scope else "<module>"
            sites[f"{key}:{node.lineno}"] = f"{where}:{node.func.attr}"
    return sites


def _unseamed_sdk_call_sites() -> dict[str, list[tuple[int, str]]]:
    """Every call on a live connection that the retry seam does not run."""
    offenders: dict[str, list[tuple[int, str]]] = {}
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        key = path.relative_to(_PACKAGE_ROOT).as_posix()
        if key == _SEAM_MODULE:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if not _talks_to_surrealdb(tree):
            continue
        parents: dict[int, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[id(child)] = parent
        named, lambdas = _driver_run_bodies(tree)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if not _is_connection_receiver(node.func.value):
                continue
            if node.func.attr in _SAFE_CONNECTION_METHODS:
                continue
            scope = _enclosing_callable(node, parents)
            if isinstance(scope, ast.Lambda) and id(scope) in lambdas:
                continue
            if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)) and scope.name in named:
                continue
            where = getattr(scope, "name", "<lambda>") if scope else "<module>"
            offenders.setdefault(key, []).append((node.lineno, f"{where}:{node.func.attr}"))
    return offenders


def _offenders_in(source: str) -> list[tuple[int, str]]:
    """Run the gate over a source snippet — the controls' instrument."""
    tree = ast.parse(source)
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    named, lambdas = _driver_run_bodies(tree)
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if not _is_connection_receiver(node.func.value):
            continue
        if node.func.attr in _SAFE_CONNECTION_METHODS:
            continue
        scope = _enclosing_callable(node, parents)
        if isinstance(scope, ast.Lambda) and id(scope) in lambdas:
            continue
        if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)) and scope.name in named:
            continue
        found.append((node.lineno, node.func.attr))
    return found


# Every one of these is a WRITE that can lose a race, and NOT ONE of them is spelled
# ``query``. The adversary measured ``upsert`` at 31 retryable conflicts in 64 live
# attempts and my three-name allowlist waved it through, green. A deny-by-default gate
# does not need to have heard of any of them.
_UNGATED_SDK_WRITES = [
    pytest.param("upsert", id="upsert-MEASURED-31-conflicts-in-64"),
    pytest.param("create", id="create"),
    pytest.param("update", id="update"),
    pytest.param("merge", id="merge"),
    pytest.param("patch", id="patch"),
    pytest.param("insert", id="insert"),
    pytest.param("delete", id="delete"),
    pytest.param("relate", id="relate"),
    pytest.param("select", id="select"),
    pytest.param("query_raw", id="query_raw"),
    pytest.param("some_method_the_sdk_adds_in_2027", id="A-METHOD-NOBODY-HAS-HEARD-OF"),
]


class TestNoProductionCodeCallsTheSdkOutsideTheSeam:
    """⚠ **THIS IS A LINT, NOT THE INVARIANT.** The invariant is
    :class:`TestNoSdkCallEscapesTheDriverAtRuntime`, which checks the property where it
    lives — at runtime, on the real SDK object — and cannot be evaded by spelling.

    This scan is kept because it is instant, it names the site, and it can see code that
    never executes (which the runtime gate cannot). It is keyed on names, and **every
    name-keyed instrument in this session has been defeated** — four of them, in four
    rounds, including two of mine. Read it as a fast lint whose failures are real and
    whose greens prove nothing on their own.
    """

    def test_every_sdk_call_site_is_run_by_the_retry_seam(self) -> None:
        """RED today: the ten ``_query`` bodies, scout's bare calls (one a compare-and-set
        WRITE), and the bootstrap DDL + ``use`` that a probe proved conflict on 6.2%-34.4%
        of 16-way virgin first-connects.
        """
        offenders = _unseamed_sdk_call_sites()

        assert not offenders, (
            f"production code calls a live SDK connection outside the retry seam: "
            f"{offenders}. EVERY method on a connection must be an attempt the driver runs "
            f"— hand it to retry_on_conflict — or be in the small, probed SAFE set "
            f"({sorted(_SAFE_CONNECTION_METHODS)}). The gate denies by default because the "
            f"dangerous surface is the SDK's and grows without asking us: an unretried "
            f"`connection.upsert()` loses 31 races in 64 live attempts, and a three-name "
            f"allowlist waved it straight through."
        )

    @pytest.mark.parametrize("method", _UNGATED_SDK_WRITES)
    def test_the_gate_denies_a_method_it_has_never_heard_of(self, method: str) -> None:
        """**THE INVERSION, PROVEN.** The gate must catch the SDK methods nobody in this
        session enumerated — including the ones that do not exist yet.

        This is the pin v2 could not have had: it was an allowlist of the DANGEROUS, so
        every method outside it was safe by omission. Deny-by-default has no omissions.
        """
        source = f"""
class Ledger:
    async def _write(self):
        connection = await self._ensure_connection()
        return await connection.{method}("thing", {{}})
"""
        assert _offenders_in(source), (
            f"an unretried connection.{method}() is INVISIBLE to the gate — it is keyed on "
            f"a list of method names again, and the list will always be shorter than the SDK"
        )

    def test_the_gate_spares_a_ledger_method_that_merely_shares_the_name(self) -> None:
        """NEGATIVE CONTROL. ``server.py`` calls ``self._finding_ledger.query(area=…)`` —
        a LEDGER's own method, not a connection. A gate that cries wolf gets deleted by
        the first engineer it annoys, which is strictly worse than no gate.
        """
        source = """
async def render(self):
    return await self._finding_ledger.query(area=area, status=STATUS_OPEN)
"""
        assert not _offenders_in(source)

    def test_the_gate_spares_a_SQLITE_connection(self) -> None:
        """NEGATIVE CONTROL — and the gate found this false positive on ITSELF.

        ``memory/ledger.py`` and ``index/sqlite_resilient.py`` each hold a variable named
        ``connection`` and call ``.execute()`` / ``.commit()`` on it. **They are SQLite.**
        Demanding they be retried on a SurrealDB write-write conflict is nonsense, and a
        gate that fires on correct, unrelated code is a gate somebody deletes.
        """
        sqlite_module = ast.parse("""
import sqlite3

def record(self, note):
    connection = sqlite3.connect(self._path)
    connection.execute("INSERT INTO memory VALUES (?)", (note,))
    connection.commit()
""")
        surreal_module_tree = ast.parse("""
from surrealdb import AsyncSurreal

async def write(connection):
    await connection.upsert("thing", {})
""")

        assert not _talks_to_surrealdb(sqlite_module), (
            "a SQLite module was scanned as if it spoke to SurrealDB"
        )
        assert _talks_to_surrealdb(surreal_module_tree)

    @pytest.mark.parametrize("method", sorted(_SAFE_CONNECTION_METHODS))
    def test_the_SAFE_set_is_spared(self, method: str) -> None:
        """NEGATIVE CONTROL for the allowlist itself. ``signin`` (probed: zero conflicts
        across 256 concurrent virgin connects), ``close`` (nothing left to contend for)
        and ``kill`` (cancels a LIVE subscription) run no transaction. Every OTHER method
        is denied — and enlarging this set requires a probe, not an opinion.
        """
        source = f"""
async def teardown(connection):
    await connection.{method}()
"""
        assert not _offenders_in(source)

    def test_the_gate_spares_the_NAMED_attempt_body(self) -> None:
        """NEGATIVE CONTROL — correct idiom #1. FALSE POSITIVE in v2."""
        source = """
class Ledger:
    async def _query(self, statement, params=None):
        return await retry_on_conflict(lambda: self._attempt(statement, params))

    async def _attempt(self, statement, params=None):
        connection = await self._ensure_connection()
        return await connection.query(statement, params)
"""
        assert not _offenders_in(source), "the gate rejected a correct named attempt body"

    def test_the_gate_spares_the_NESTED_CLOSURE_attempt_body(self) -> None:
        """NEGATIVE CONTROL — correct idiom #2, and **the false positive that mattered**.

        v2 attributed a call to EVERY enclosing function, so a call inside a nested attempt
        closure was also charged to the OUTER method — which is not blessed. The gate
        rejected the correct build. **A gate that fires on the right answer gets deleted by
        the first engineer it blocks, and then we have nothing.**
        """
        source = """
class Ledger:
    async def _query(self, statement, params=None):
        async def _attempt():
            connection = await self._ensure_connection()
            return await connection.query(statement, params)

        return await retry_on_conflict(_attempt)
"""
        assert not _offenders_in(source), (
            "the gate rejected the idiomatic NESTED-CLOSURE attempt body — a false "
            "positive on the CORRECT build"
        )

    def test_the_gate_spares_an_INLINE_LAMBDA_attempt_body(self) -> None:
        """NEGATIVE CONTROL — correct idiom #3."""
        source = """
async def bootstrap(connection, namespace):
    await retry_on_conflict(lambda: connection.query(f"DEFINE NAMESPACE {namespace}"))
"""
        assert not _offenders_in(source), "the gate rejected a correct inline-lambda attempt"

    def test_a_function_the_driver_never_runs_is_NOT_blessed_by_its_name(self) -> None:
        """POSITIVE CONTROL. Calling it ``_query_once`` earns nothing — being handed to the
        driver does. Name-as-proxy-for-property is the mistake this gate replaces.
        """
        source = """
class Ledger:
    async def _query(self, statement, params=None):
        return await self._query_once(statement, params)

    async def _query_once(self, statement, params=None):
        connection = await self._ensure_connection()
        return await connection.query(statement, params)
"""
        assert _offenders_in(source), (
            "a function the driver NEVER RUNS was blessed because of what it is called"
        )


# ===========================================================================
# 4b-RUNTIME. **THE INVARIANT.** Everything above is a LINT.
#
# FIVE ROUNDS. FIVE INSTRUMENTS. FIVE DEFEATS, ALL THE SAME SHAPE:
#
#     the retry gate      keyed on a label's LITERAL     -> a substring of it
#     the retired pin     keyed on a symbol's NAME       -> a numeric claim naming nothing
#     the seam enumerator keyed on `async def _query`    -> scout.py
#     the SDK gate v2     keyed on 3 METHOD names        -> the other 30 (`upsert`)
#     the SDK gate v3     keyed on 2 RECEIVER names      -> six doors, 924 passed / 0 failed
#
# I inverted the METHOD half and left the RECEIVER half a two-name list. That is not a
# slip; it is the METHOD failing. **Static analysis is inherently name-based** — whatever
# property you want, the AST hands you only names to key on, and the evasion space over
# names is unbounded. We keep losing because we keep choosing a SYNTACTIC instrument for
# a BEHAVIOURAL property.
#
# THE PROPERTY: *no call on a live SurrealDB connection ever escapes the driver.*
# That is a RUNTIME fact. So it is checked at RUNTIME.
#
# HOW: wrap **every public method on the real SDK connection class** — all 33, enumerated
# from the class itself, so the SDK's next release is covered without anyone editing a
# list — and, on each call, walk the stack:
#
#   * no PRODUCTION frame below us  -> the harness is talking to the engine. Allowed.
#   * a `retry_on_conflict` frame   -> we are inside a driver attempt. Allowed.
#   * SAFE method (probed)          -> allowed.
#   * otherwise                     -> **ESCAPE**, recorded with file:line and the method.
#
# Aliasing, containers, proxies, helper modules, `getattr`, `Any`-typing, a module the
# import-filter skips, and every method nobody has thought of ALL die at once — because
# the check never looks at code. **It cannot be evaded by spelling.**
#
# THE LINT ABOVE STAYS, honestly labelled: it scans code that never runs (which the
# runtime gate cannot see), it is instant, and it names the site. It is a LINT. **This
# is the invariant.**
# ===========================================================================




def _install_runtime_sdk_guard(
    monkeypatch: pytest.MonkeyPatch,
    *,
    production_root: Path | None = None,
    witness: Any = None,
) -> GuardReport:
    """Arm the SHARED guard (``tests/_sdk_guard.py``) for a focused, in-test assertion.

    The guard is ALREADY autouse for every test (conftest) — that is its reach, and its
    reach is the thing v4 got wrong. Arming it again here is not redundancy: these pins
    assert on WHAT IT SAW, and the controls aim its notion of "production" at this file so
    they fire identically on a repaired tree. (A control that goes vacuous the day the fix
    lands is the disease, not the cure.)

    ``production_root=None`` means the ARTIFACT's root — where the imported ``loremaster``
    executes from, not where this file sits (#136). Aiming it elsewhere requires a
    ``witness`` from there: you may not point this guard at a directory and then be told,
    with a straight face, that nothing happened in it.
    """
    report = _install_shared_guard(
        monkeypatch, production_root=production_root, witness=witness
    )
    assert report.armed, (
        "the shared retry driver does not exist, so the runtime guard cannot arm: there is "
        "nothing for a call to be INSIDE. Build `_txn.retry_on_conflict` first."
    )
    return report


def _install_guard_aimed_at_this_file(monkeypatch: pytest.MonkeyPatch) -> GuardReport:
    """Arm the guard with THIS FILE as "production" — the controls' idiom, in one place."""
    return _install_runtime_sdk_guard(
        monkeypatch,
        production_root=_THIS_FILE_ROOT,
        witness=_a_function_defined_in_this_file,
    )


class TestNoSdkCallEscapesTheDriverAtRuntime:
    """**THE INVARIANT — enforced where the property actually lives.**

    Every production flow below runs against the REAL engine with the REAL SDK class
    instrumented. A call that the driver did not run is recorded with its file:line, and
    no amount of spelling hides it.

    SCOPE, stated honestly (a gate that overstates its reach is the thing we police): the
    runtime gate sees the code these flows EXECUTE. Code that never runs is the LINT's
    job, and the lint says so. Between them: the lint covers all code weakly, the gate
    covers executed code absolutely.
    """

    async def test_no_seam_escapes_the_driver_against_the_real_engine(
        self, live_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RED today with the full list of escapes — every seam's bootstrap and every
        seam's ``_query``.
        """
        report = _install_runtime_sdk_guard(monkeypatch)

        for _, seam in _discover_query_seams():
            instance = _construct_live(seam, live_env)
            try:
                await instance._ensure_connection()
                await instance._query("INFO FOR DB")
            finally:
                await instance.close()

        # The TRANSACTIONAL path too (``query_raw``) — a different SDK method on the same
        # object, and the runtime gate does not care which: it is a call on a connection.
        store = _construct_live(SurrealStore, live_env)
        try:
            await execute_transaction(
                "BEGIN;\nUPSERT retry_counter:probe SET next = 1;\nCOMMIT;",
                {},
                acquire=store._ensure_connection,
                drop=store._drop_connection,
                url=live_env.url,
            )
        finally:
            await store.close()

        # A CLEAN VERDICT IT CANNOT SUBSTANTIATE IS NOT A CLEAN VERDICT (#136). Every seam
        # above bootstrapped a connection and ran a statement: if the guard saw NOTHING, it
        # is blind, not satisfied — and its silence must not read as a pass.
        report.require_observations("driving every discovered seam against the real engine")
        assert not report.escapes, (
            f"{len(report.escapes)} SurrealDB call(s) escaped the retry driver:\n  "
            + "\n  ".join(str(escape) for escape in report.escapes)
            + "\n\nEvery call on a live connection must be an attempt the driver runs. "
            "This is checked at RUNTIME, on the real SDK class, so it cannot be evaded by "
            "aliasing, by a helper module, by `getattr`, by a detached `gather`, or by an "
            "SDK method nobody has listed."
        )

    async def test_the_scout_command_channel_escapes_nothing(
        self, live_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scout's CAS write, against the real engine, under the same guard."""
        admin = await connect_admin(live_env)
        await run(admin, "DEFINE TABLE IF NOT EXISTS command SCHEMALESS")
        await admin.close()

        report = _install_runtime_sdk_guard(monkeypatch)

        connection = await scout_module._open_command_connection(
            url=live_env.url,
            namespace=live_env.namespace,
            database=live_env.database,
            user=live_env.user,
            password=live_env.password,
        )
        try:
            # A RecordID, not a string: the CAS binds ``$command_id`` as a record link,
            # and the engine refuses a bare string ("Cannot execute UPDATE statement using
            # value: 'command:x'"). The row need not exist — an empty CAS result is scout's
            # legitimate duplicate-completion path, and the guard is what is under test.
            await _subscriber()._mark(connection, RecordID("command", "absent"), "done")
        finally:
            await connection.close()

        report.require_observations("driving scout's CAS write against the real engine")
        assert not report.escapes, (
            "scout's command channel escaped the driver:\n  "
            + "\n  ".join(str(escape) for escape in report.escapes)
        )

    async def test_the_guard_SEES_an_escape_it_is_shown(
        self, live_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**POSITIVE CONTROL.** A guard that has never been shown FIRING is not a guard.

        The guard's "production" root is aimed at THIS FILE, so the call below is treated
        exactly as a production call. It has no driver above it, so it MUST be recorded.
        (Aiming it at real production code would make this control go silently vacuous the
        day the repair lands — an instrument that stops discriminating without telling
        anyone is the whole disease.)
        """
        connection = await connect_admin(live_env)  # connect BEFORE arming the guard
        report = _install_guard_aimed_at_this_file(monkeypatch)
        try:
            await connection.query("INFO FOR DB")  # no driver above this call
        finally:
            await connection.close()

        assert report.escapes, (
            "the runtime guard did NOT see a call made outside the driver — the "
            "instrument is blind, and every green it reports is worthless"
        )
        assert [escape.method for escape in report.escapes] == ["query"]

    async def test_a_call_INSIDE_a_driver_attempt_is_allowed(
        self, live_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**NEGATIVE CONTROL.** The guard must permit the correct idiom, or the builder
        cannot satisfy it and deletes it — and then we have nothing.
        """
        connection = await connect_admin(live_env)  # connect BEFORE arming the guard
        report = _install_guard_aimed_at_this_file(monkeypatch)
        try:

            async def _attempt() -> Any:
                return await connection.query("INFO FOR DB")

            await _driver()(_attempt)
        finally:
            await connection.close()

        report.require_observations("making a driver-run call from this file")
        assert not report.escapes, (
            "a call the driver DID run was reported as an escape — the guard rejects the "
            "correct idiom and will be deleted by the first engineer it blocks"
        )

    # THE 2x2 DETACHMENT MATRIX. My v4 wrapper was an ``async def``, so it walked the
    # stack when the EVENT LOOP resumed its body — by which time the caller's frame was
    # gone. Result: an ordinary, awaited ``asyncio.gather(connection.query(...))`` was
    # INVISIBLE while the identical direct call was caught, and the docstring claiming the
    # guard "cannot be evaded by spelling" was simply FALSE.
    #
    # The wrapper is a plain ``def`` now: the walk happens when the call is MADE. All four
    # cells must be judged the same way — detachment is not a defence, and being inside the
    # driver is not forfeited by one.
    @pytest.mark.parametrize(
        "detached",
        [pytest.param(False, id="direct"), pytest.param(True, id="DETACHED-via-gather")],
    )
    @pytest.mark.parametrize(
        "driven",
        [pytest.param(False, id="outside-the-driver"), pytest.param(True, id="inside-driver")],
    )
    async def test_the_detachment_matrix(
        self,
        live_env: SurrealEnv,
        monkeypatch: pytest.MonkeyPatch,
        detached: bool,
        driven: bool,
    ) -> None:
        connection = await connect_admin(live_env)
        report = _install_guard_aimed_at_this_file(monkeypatch)

        async def _call() -> Any:
            if detached:
                return await asyncio.gather(connection.query("INFO FOR DB"))
            return await connection.query("INFO FOR DB")

        try:
            await (_driver()(_call) if driven else _call())
        finally:
            await connection.close()

        report.require_observations("making a call from this file, driven or not")
        if driven:
            assert not report.escapes, (
                "a call the driver DID run was flagged — detaching an attempt's own call "
                "through gather() must not forfeit the driver above it"
            )
        else:
            assert report.escapes, (
                "a call OUTSIDE the driver was invisible. If this is the DETACHED cell, "
                "the stack is being walked when the coroutine RESUMES rather than when it "
                "is CALLED — and `await asyncio.gather(connection.query(...))`, an "
                "entirely ordinary line, walks straight past the guard."
            )

    async def test_every_production_sdk_call_site_was_OBSERVED_by_the_guard(
        self, live_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**COVERAGE IS A CHECKED VARIABLE — and in v5 it was not, whatever I wrote.**

        My v5 pin enumerated from the **OFFENDERS** set (`_unseamed_sdk_call_sites`), which
        is **empty by construction on any lint-clean build**. It was therefore STRICTLY
        DOMINATED by the lint and could not fire on any build the lint passed — while its
        docstring promised the opposite. `WB-ROUTED-UNDRIVEN` walked straight through:
        an SDK call ROUTED through the driver but never CLASSIFYING the conflict, at a site
        **no test executes**. Contract 199/0. Full suite 4375/0. It retries **zero** times.
        Finding #120, alive again, one altitude up.

        **That is this repo's own law breaking on me: A DIAGNOSIS IS NOT AN INSTRUMENT.**
        I pinned the INSTANCE that killed v4 (scout's drain SELECT — and that pin does
        work) and shipped a broken instrument for the CLASS. The instance was fixed; the
        class was not.

        THE FIX: enumerate **EVERY** SDK call site in production (:func:`_all_sdk_call_sites`
        — the ALL set, correct ones included), drive every production entry point that can
        reach one, and require the guard to have **OBSERVED** each. A site the guard never
        executed is a site it certifies **nothing** about, and it is NAMED here.

        WHY THIS PIN DRIVES THE FLOWS ITSELF rather than aggregating what the wider suite
        happened to observe: an aggregate is per-worker under ``-n auto`` and would have to
        be stitched across processes, and — worse — it would make this pin's verdict depend
        on which OTHER tests ran. Driving them here makes it deterministic and self-contained,
        and it puts the obligation where it belongs: **a new SDK call site that nothing drives
        turns this RED on the day it is written**, which is exactly what did not happen to
        ``_drain_pending``.

        HONEST LIMIT, stated because a gate that overstates its reach is the thing we police:
        this proves every call site is **WATCHED** (executed under the guard), not that every
        BRANCH of it is exercised. A call site whose conflict path never runs is watched but
        not proven correct — which is why ``TestEverySdkCallSiteActuallyRetries`` exists and
        counts engine attempts.
        """
        report = _install_runtime_sdk_guard(monkeypatch)

        # Every production entry point that can reach the engine. If a future call site is
        # added somewhere nothing here drives, this pin goes RED and names it — which is the
        # entire point.
        for _, seam in _discover_query_seams():
            instance = _construct_live(seam, live_env)
            try:
                await instance._ensure_connection()  # bootstrap: DEFINE x2 + use x2
                await instance._query("INFO FOR DB")  # the single-statement seam
            finally:
                await instance.close()

        store = _construct_live(SurrealStore, live_env)
        try:
            await execute_transaction(  # the transactional seam (query_raw)
                "BEGIN;\nUPSERT retry_counter:probe SET next = 1;\nCOMMIT;",
                {},
                acquire=store._ensure_connection,
                drop=store._drop_connection,
                url=live_env.url,
            )
        finally:
            await store.close()

        admin = await connect_admin(live_env)
        await run(admin, "DEFINE TABLE IF NOT EXISTS command SCHEMALESS")
        await admin.close()

        connection = await scout_module._open_command_connection(
            url=live_env.url,
            namespace=live_env.namespace,
            database=live_env.database,
            user=live_env.user,
            password=live_env.password,
        )
        subscriber = _subscriber()
        try:
            await subscriber._drain_pending(connection)  # the drain SELECT (WB-GHOST's home)
            await subscriber._mark(connection, RecordID("command", "absent"), "done")  # the CAS
            # The LIVE uuid is fetched from the TEST (so the guard allows it); what must be
            # OBSERVED is production's own `connection.subscribe_live(...)` inside
            # `_consume_live`, which is a call site all of its own.
            live_uuid = await connection.query(subscriber.live_select_statement())
            with contextlib.suppress(Exception):
                await asyncio.wait_for(subscriber._consume_live(connection, live_uuid), 1.0)
            await subscriber._safe_kill(connection, live_uuid)
        finally:
            await connection.close()

        observed = {site.split(" in ")[0] for site in report.observed}
        all_sites = _all_sdk_call_sites()
        unobserved = sorted(site for site in all_sites if site not in observed)

        # This pin compares two trees: the SOURCE the AST scanner reads (`_PACKAGE_ROOT`)
        # and the ARTIFACT the guard watches execute. They are the same directory in the
        # checkout. When they are not — an out-of-tree copy importing `loremaster` from the
        # original via an editable install — the comparison is apples to oranges, and the
        # honest thing is to SAY so in the failure rather than let the reader conclude their
        # code is unwatched when in fact their code never ran at all (#136).
        divergent_trees = (
            ""
            if _PACKAGE_ROOT.resolve() == artifact_root()
            else (
                f"\n\nNB: THE TREE YOU ARE SCANNING IS NOT THE TREE THAT RAN. The call sites "
                f"above were enumerated from {_PACKAGE_ROOT.resolve()}, but `loremaster` "
                f"imported from {artifact_root()} — so your edits to production code in this "
                f"tree were NEVER EXECUTED by this run. Re-sync this checkout's venv "
                f"(`uv sync --reinstall-package loremaster`) before trusting ANY verdict here."
            )
        )

        assert all_sites, "the ALL-call-site enumeration found nothing — the scanner is broken"
        assert not unobserved, (
            f"the runtime guard never EXECUTED {len(unobserved)} of {len(all_sites)} "
            f"production SDK call sites, so it certifies NOTHING about them:\n  "
            + "\n  ".join(f"{site}  ({all_sites[site]})" for site in unobserved)
            + "\n\nA runtime gate is an invariant only over code it RUNS. An unwatched call "
            "site is how `_drain_pending` shipped finding #120 alive through a suite that "
            "scored 932/0. Drive it here — or it is watched by nothing but a name-keyed lint."
            + divergent_trees
        )


class TestTheGuardRefusesAVerdictItCannotSubstantiate:
    """**FINDING #136 — a gate whose controls are red is a gate whose greens are worthless.**

    In an out-of-tree copy of this repo, the guard's watched root was derived from THIS
    FILE's path while ``loremaster`` imported from the ORIGINAL checkout (an editable
    install's ``.pth`` names an absolute path). So the guard watched a directory nothing
    executed from: it observed ZERO calls, every ``assert not report.escapes`` in the file
    passed — **vacuously** — and the three positive controls, the only evidence the guard
    can SEE a breach, went RED beside them. The suite reported "no escapes" from an
    instrument that could not have seen one.

    Repairing the root resolution alone fixes the INSTANCE. These pins kill the CLASS: the
    guard now proves, at arm time, that it can see the code it is about to judge — and
    REFUSES to arm when it cannot. A vacuous green is no longer a reachable state, whatever
    tree the suite is run from and however its roots are computed tomorrow.
    """

    def test_the_guard_REFUSES_a_root_no_code_executes_from(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """THE FAIL-LOUD PATH. Aim it at an empty directory and it must refuse, naming both
        the root it was given and the file the code it must judge actually runs from.
        """
        with pytest.raises(GuardCannotSubstantiate) as refusal:
            _install_shared_guard(monkeypatch, production_root=tmp_path)

        message = str(refusal.value)
        assert str(tmp_path) in message, "the refusal must name the root it was asked to watch"
        assert "_txn.py" in message, (
            "the refusal must name where the code it has to judge ACTUALLY executes — a "
            "refusal that does not say what diverged sends the reader hunting"
        )

    def test_the_POSITIVE_CONTROL_the_guard_arms_normally_against_the_real_artifact(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The control on the pin above: a gate that refuses EVERYTHING is not discriminating,
        it is broken. The default arming must succeed and watch the artifact that ran.
        """
        report = _install_runtime_sdk_guard(monkeypatch)

        assert report.armed
        assert report.watched_root == artifact_root()
        assert _driver().__code__.co_filename.startswith(str(report.watched_root)), (
            "the guard's watched root does not contain the retry driver itself — it is "
            "watching a tree the production code does not execute from"
        )

    def test_the_watched_root_comes_from_the_IMPORTED_package_not_this_files_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """**THE #136 REGRESSION PIN, and it discriminates IN THE CHECKOUT** — where the two
        roots coincide and so a plain equality assertion would prove nothing.

        Move where the IMPORTED package says it lives. A guard that derives its root from
        the imported module follows it there, finds that production does not execute from
        the new root, and REFUSES. A guard that derives its root from ``__file__`` (the bug)
        never notices the move at all: it keeps watching the real package and arms happily —
        which is exactly how it came to watch a copy's directory while the code ran elsewhere.
        """
        import loremaster

        monkeypatch.setattr(loremaster, "__file__", str(tmp_path / "loremaster" / "__init__.py"))

        with pytest.raises(GuardCannotSubstantiate) as refusal:
            _install_shared_guard(monkeypatch)

        assert str(tmp_path) in str(refusal.value)

    def test_the_witness_is_CHECKED_not_decorative(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Aiming the guard at this file while naming a witness that executes SOMEWHERE ELSE
        must refuse. Otherwise "name the code you expect to be watched" is a comment, not a
        precondition — and the controls could go blind again without a word.
        """
        with pytest.raises(GuardCannotSubstantiate):
            _install_shared_guard(
                monkeypatch, production_root=_THIS_FILE_ROOT, witness=_driver()
            )

        # ...and the controls' OWN witness, which does execute from here, arms fine.
        assert _install_guard_aimed_at_this_file(monkeypatch).armed

    def test_a_clean_verdict_requires_OBSERVATIONS(self) -> None:
        """**"No escapes" having seen NOTHING is blindness wearing cleanliness.**

        The poison state, stated exactly: ``escapes == []`` and ``observed == set()`` in a
        flow that provably called the SDK. It must not be assertable as a pass.
        """
        blind = GuardReport(
            escapes=[],
            observed=set(),
            armed=True,
            watched_root=artifact_root(),
            intercepted=7,  # it SAW seven SDK calls and attributed none of them
        )
        with pytest.raises(GuardCannotSubstantiate) as refusal:
            blind.require_observations("driving a flow that provably calls the SDK")
        assert "BLINDNESS" in str(refusal.value)

        # POSITIVE CONTROL: a report that DID see production is not refused — or the check
        # is an unconditional raise and discriminates nothing.
        seeing = GuardReport(
            escapes=[],
            observed={"store/_txn.py:1092 in _attempt()"},
            armed=True,
            watched_root=artifact_root(),
            intercepted=7,
        )
        seeing.require_observations("driving a flow that provably calls the SDK")


# ===========================================================================
# 4c. SCOUT — the ELEVENTH seam, and a LIVE #120 instance.
#
# ``CommandSubscriber._mark`` is a compare-and-set WRITE on the command table:
#
#     UPDATE $command_id SET status = $status, processed_at = time::now()
#     WHERE status = $pending_status RETURN BEFORE
#
# It runs on a raw ``connection.query`` with no retry and no wrapper. A retryable
# conflict raises a bare SDK ``QueryError`` straight out of the dispatch loop.
#
# AND IT CARRIES A SEMANTIC THAT A CARELESS RETRY WOULD DESTROY: an EMPTY result means
# the CAS matched nothing — *another instance already completed this command* — which is
# logged as a duplicate completion and is NOT an error. An empty result is a LOST RACE,
# not a conflict. A build that retries "nothing came back" would re-run a claim that was
# correctly refused, and could re-stamp a row another instance owns.
# ===========================================================================


def _subscriber() -> Any:
    async def _connect() -> Any:
        raise AssertionError("the fake handle short-circuits the connect factory")

    async def _handler(row: dict[str, Any]) -> None:
        return None

    return scout_module.CommandSubscriber(
        connect=_connect, handler=_handler, poll_interval_s=0.01
    )


@dataclass
class _ScoutFakeConnection:
    """A command-table connection for the BEHAVIOURAL ladder pins.

    Models exactly what ``run()`` drives: a pending SELECT, a CAS stamp that removes the
    row (which is what makes a re-poll idempotent), and no LIVE. ``dead`` makes the whole
    socket raise (a mid-run drop); ``cas_error`` makes only the CAS fail (a conflict that
    will exhaust into the typed error).
    """

    pending: dict[str, dict[str, Any]] = field(default_factory=dict)
    dead: bool = False
    cas_error: Callable[[], BaseException] | None = None
    closed: bool = False

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        if self.dead:
            raise ConnectionResetError("fake socket is dead")
        upper = statement.strip().upper()
        if upper.startswith("LIVE SELECT"):
            # LIVE must SUCCEED here (it is established before the poll loop runs); it is
            # the SUBSCRIPTION that is unavailable, so the poll backstop carries the load.
            # Mirrors test_scout.py's own `die_on_subscribe` fake — get this wrong and the
            # subscriber reconnects forever without ever polling, and the pin is vacuous.
            return "live-uuid-1"
        if upper.startswith("SELECT"):
            return list(self.pending.values())
        if upper.startswith("UPDATE"):
            if self.cas_error is not None:
                raise self.cas_error()
            blob = statement + repr(params or {})
            for key in list(self.pending):
                if key in blob:
                    self.pending.pop(key, None)
            return []
        return []

    async def subscribe_live(self, live_uuid: Any) -> Any:
        raise ConnectionResetError("live subscription unavailable — poll must carry it")

    async def kill(self, live_uuid: Any) -> None:
        return None

    async def close(self) -> None:
        self.closed = True


async def _run_subscriber_until_recovered(
    *connections: Any, until: Callable[[], bool]
) -> list[str]:
    """Drive the REAL ``CommandSubscriber.run()`` across a scripted connection sequence.

    Returns the ids it dispatched. A subscriber that dies on the first connection never
    reaches the second — which is the whole assertion.
    """
    handed: list[Any] = list(connections)
    dispatched: list[str] = []

    async def _connect() -> Any:
        return handed.pop(0) if handed else connections[-1]

    async def _handler(row: dict[str, Any]) -> None:
        dispatched.append(str(row["id"]))

    async def _immediate_sleep(_: float) -> None:
        await _REAL_ASYNCIO_SLEEP(0)

    subscriber = scout_module.CommandSubscriber(
        connect=_connect,
        handler=_handler,
        poll_interval_s=0.001,
        sleep=_immediate_sleep,
    )
    task = asyncio.create_task(subscriber.run())
    try:
        for _ in range(600):  # generous: the contended CAS burns its real retry budget
            if until():
                break
            await _REAL_ASYNCIO_SLEEP(0.01)
    finally:
        with contextlib.suppress(Exception):
            await subscriber.stop()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await task
    return dispatched


class TestScoutCommandClaimRidesTheSeam:
    """The command CAS retries a retryable conflict, raises the TYPED error on
    exhaustion, and NEVER retries a legitimately-lost claim.
    """

    async def test_a_retryable_conflict_on_the_command_claim_is_retried(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RED today: raises a bare ``surrealdb.errors.QueryError`` on the first
        conflict — not even wrapped in a store error. This is finding #120, live, in the
        one module my first enumerator could not see.
        """
        _silence_sleep(monkeypatch)
        connection = _ConflictingConnection(conflicts=3, rows=[{"id": "command:1"}])

        await _subscriber()._mark(connection, "command:1", "done")

        assert connection.calls == 4, (
            f"scout's command CAS made {connection.calls} attempt(s) — a retryable "
            f"conflict on a WRITE must be retried like every other single-statement write"
        )

    async def test_sustained_contention_raises_the_TYPED_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _silence_sleep(monkeypatch)
        connection = _ConflictingConnection(conflicts=None)

        with pytest.raises(TxnContentionExhaustedError):
            await _subscriber()._mark(connection, "command:1", "done")

    async def test_the_claim_backs_off_through_the_SHARED_jitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _silence_sleep(monkeypatch)
        recorder = _record_shared_jitter(monkeypatch)
        connection = _ConflictingConnection(conflicts=2, rows=[{"id": "command:1"}])

        await _subscriber()._mark(connection, "command:1", "done")

        assert recorder.draws, "scout hand-rolled its own backoff instead of sharing one"

    async def test_detection_follows_the_shared_marker(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scout is held to the SAME detection authority as the other ten — otherwise it
        is an eleventh copy of the prose coupling, which is how it got here.

        NOTE the expected type: scout raises the SDK error RAW (see the transport pin
        below). It is not a ledger and its error contract is not a ledger's.
        """
        _silence_sleep(monkeypatch)
        _mutate_shared_marker(monkeypatch)
        stale = _ScriptedConnection(error=_conflict_error(), failures=None)

        with pytest.raises(QueryError):
            await _subscriber()._mark(stale, "command:1", "done")

        assert stale.calls == 1, (
            "scout retried a message the shared marker no longer calls a conflict — it "
            "keeps its own copy of the engine's prose"
        )

    @pytest.mark.parametrize(
        "transport",
        [
            pytest.param(
                lambda: NotAllowedError(ErrorKind.NOT_ALLOWED, _LIVE_TRANSPORT_TEXT),
                id="reconnected-unauthenticated",
            ),
            pytest.param(lambda: OSError("connection refused"), id="dead-socket"),
            pytest.param(lambda: KeyError("request-uuid"), id="SDK-routing-KeyError"),
        ],
    )
    async def test_a_transport_fault_still_reaches_the_reconnect_ladder(
        self, monkeypatch: pytest.MonkeyPatch, transport: Callable[[], BaseException]
    ) -> None:
        """**THE PIN MY OWN INVENTORY MISSED — and it cost a false receipt.**

        I claimed test_scout.py was still green. It was not: routing scout's CAS through
        the seam **killed scout's reconnect ladder**, deterministically, and I reported a
        green I had never run.

        The mechanism, stated so nobody rebuilds it: ``run()``'s ladder is

            except (*_CONNECTION_ERRORS, KeyError):
                await self._drop_connection(); await self._backoff(attempt); continue

        — it is built on the **RAW SDK TYPES**. The ten ledgers wrap a transport fault as
        ``SurrealConnectionError``, which is a ``RuntimeError`` and therefore NOT in
        ``_CONNECTION_ERRORS``. Wrap scout's the same way and the socket drop flies
        straight past the ladder: no drop, no backoff, no reconnect, subscriber dead.

        **TRANSPORT IS NOT CONTENTION.** A conflict means "the write did not land, try
        again" — the seam's business. A dead socket means "reconnect" — the ladder's. The
        seam may claim the conflict and NOTHING else; every other error scout raises
        must arrive at the ladder in the type the ladder catches.
        """
        _silence_sleep(monkeypatch)
        error = transport()
        connection = _ScriptedConnection(error=error, failures=None)

        with pytest.raises((*_CONNECTION_ERRORS, KeyError)) as exc_info:
            await _subscriber()._mark(connection, "command:1", "done")

        assert connection.calls == 1, "a transport fault was RETRIED as if it were contention"
        assert isinstance(exc_info.value, (*_CONNECTION_ERRORS, KeyError)), (
            f"scout's seam raised {type(exc_info.value).__name__}, which "
            f"`except (*_CONNECTION_ERRORS, KeyError)` in run() CANNOT catch. The reconnect "
            f"ladder is dead and every socket drop now kills the subscriber."
        )
        assert not isinstance(exc_info.value, SurrealStoreError), (
            "scout's transport fault was wrapped in a store error — the ladder is built on "
            "the RAW SDK types and cannot see a RuntimeError"
        )

    async def test_the_run_loop_survives_exhausted_contention_and_RECONNECTS(self) -> None:
        """The other half of the same removed behaviour — **and this pin is BEHAVIOURAL,
        because the source-grep version of it was a fraud.**

        My v3 pin asserted ``"TxnContentionExhaustedError" in inspect.getsource(run)``.
        The adversary defeated it with a **comment**, and with a names-it-then-re-raises
        build in which the subscriber still dies. Both GREEN. **A pin that greps source
        text is not a pin** — it tests the spelling of the code, not what the code does.

        So: drive the real ``run()`` loop. The first connection's CAS is a sustained
        conflict (which exhausts into ``TxnContentionExhaustedError``, a ``RuntimeError``
        the ladder cannot see unless it is told to); the second is healthy and holds a
        pending command. A subscriber that survives **reconnects and processes it**. A
        subscriber that dies never asks for a second connection.

        WHAT WAS REMOVED: pre-change, ANY ``SurrealError`` out of the CAS reached the
        ladder (``SurrealError`` IS in ``_CONNECTION_ERRORS``), so a contended command
        backed off and reconnected. Ladder REACHABILITY is a behaviour, and the rewrite
        drops it silently.
        """
        # Connection #1 HOLDS the command, so the CAS is actually reached and conflicts
        # forever (my first draft gave it an empty pending set — the CAS never ran, nothing
        # ever conflicted, and the pin was vacuous. A fixture that cannot reach the code it
        # names is decoration).
        contended = _ScoutFakeConnection(
            pending={"command:gap": {"id": "command:gap"}}, cas_error=_conflict_error
        )
        healthy = _ScoutFakeConnection(pending={"command:gap": {"id": "command:gap"}})

        await _run_subscriber_until_recovered(contended, healthy, until=lambda: not healthy.pending)

        assert not healthy.pending, (
            "the subscriber did not survive exhausted contention on the command CAS — it "
            "never reached the second connection at all. Before this wave a conflict "
            "surfaced as a SurrealError and REACHED the reconnect ladder, which backed off "
            "and reconnected. Now it arrives as TxnContentionExhaustedError — a "
            "RuntimeError the ladder cannot catch — so sustained contention KILLS the "
            "subscriber where it used to back off. Ladder reachability is a behaviour, and "
            "the rewrite drops it silently."
        )

    async def test_a_transport_drop_still_RECONNECTS_and_recovers_the_gap_command(
        self,
    ) -> None:
        """The transport half, also behavioural (modelled on ``test_scout.py``'s own
        reconnect pin, which is the thing my rewrite broke and I reported green).

        Connection #1 is a dead socket; connection #2 is healthy and holds a command
        inserted during the gap. The subscriber must RECONNECT and recover it exactly
        once — which it cannot do if the seam wrapped the transport fault in a
        ``SurrealConnectionError`` the ladder cannot catch.
        """
        dead = _ScoutFakeConnection(dead=True)
        recovered = _ScoutFakeConnection(pending={"command:gap": {"id": "command:gap"}})
        dispatched = await _run_subscriber_until_recovered(
            dead, recovered, until=lambda: not recovered.pending
        )

        assert dispatched == ["command:gap"], (
            "the subscriber did not reconnect after a socket drop. Its ladder catches the "
            "RAW SDK types; a seam that wraps a transport fault as SurrealConnectionError "
            "(a RuntimeError) makes the drop fly straight past it — no drop, no backoff, "
            "no reconnect, subscriber dead."
        )


# ===========================================================================
# 4d. **ROUTED IS NOT RETRYING.** (Adversary blocker 3 — and it is a real defect.)
#
# In my OWN reference build, ``retry_on_conflict(lambda: connection.kill(u))`` retried
# **ZERO** times. The gate was satisfied and nothing retried: a green gate over a dead
# mechanism — *literally finding #102's shape* (a backstop that never executed),
# reproduced inside the fix for #102.
#
# ROOT CAUSE: the driver retries only when the attempt raises the shared SIGNAL. A bare
# SDK call raises a raw SDK error that nothing classifies. **Routing is necessary and NOT
# sufficient — the attempt body must CLASSIFY and SIGNAL.** That is the real contract of
# a caller, and no pin of mine had ever stated it.
#
# So every SDK call site is now pinned on the thing that matters: under a conflict, DOES
# IT ACTUALLY RETRY — counted, at the engine.
# ===========================================================================


@dataclass
class _AllMethodsConflictConnection:
    """Every method conflicts ``conflicts`` times, then succeeds. Counts per method."""

    conflicts: int
    calls: dict[str, int] = field(default_factory=dict)

    def _tick(self, method: str) -> bool:
        self.calls[method] = self.calls.get(method, 0) + 1
        if self.calls[method] > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError("unbounded retry")
        return self.calls[method] <= self.conflicts

    async def signin(self, credentials: dict[str, Any]) -> None:
        return None

    async def use(self, namespace: str, database: str) -> None:
        if self._tick("use"):
            raise _conflict_error()

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        if self._tick("query"):
            raise _conflict_error()
        return []

    async def kill(self, live_uuid: Any) -> None:
        if self._tick("kill"):
            raise _conflict_error()

    async def subscribe_live(self, live_uuid: Any) -> Any:
        if self._tick("subscribe_live"):
            raise _conflict_error()
        return _empty_subscription()

    async def close(self) -> None:
        return None


async def _empty_subscription() -> Any:
    """An exhausted async iterator — ``subscribe_live``'s success shape.

    Built from an empty list rather than the ``return``-then-``yield`` marker: that idiom
    needs a ``warn_unreachable`` ignore, and an ignore in a CONTRACT is a place a builder
    learns to put ignores.
    """

    async def _iterator() -> Any:
        for notification in []:  # type: ignore[var-annotated]
            yield notification

    return _iterator()


class TestEverySdkCallSiteActuallyRetries:
    """Routing a call through the driver proves NOTHING unless a conflict on it produces
    a RETRY. Count them at the engine.

    THE WRONG BUILD (and it was MINE): ``retry_on_conflict(lambda: connection.kill(u))``.
    It satisfies any structural gate — the call is inside a driver attempt — and retries
    zero times, because a bare SDK error is not the driver's signal. The gate goes green
    over a mechanism that never runs.
    """

    async def test_the_bootstrap_use_call_is_retried(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``connection.use()`` is the call that actually loses the bootstrap race (probed
        — 6.2%-34.4% of concurrent virgin first-connects). Routing it is worthless
        unless it retries.
        """
        _silence_sleep(monkeypatch)
        connection = _AllMethodsConflictConnection(conflicts=3)
        monkeypatch.setattr(surreal_module, "AsyncSurreal", lambda url: connection)
        store = _construct(SurrealStore)

        await store._ensure_connection()

        # >= 4, not == 4: the bootstrap calls ``use`` twice (once per DEFINE), and the
        # fake's conflict budget is per-method. A build that ROUTES but does not CLASSIFY
        # attempts it exactly ONCE and raises. Any number above the conflict count proves
        # the retry; the exact total is the bootstrap's business, not the contract's.
        assert connection.calls.get("use", 0) >= 4, (
            f"connection.use() was attempted {connection.calls.get('use', 0)} time(s) "
            f"under a sustained conflict. It is INSIDE the driver and it is not RETRYING "
            f"— the attempt body is not classifying the conflict into the shared signal, "
            f"so the driver never sees one. A green gate over a dead mechanism is finding "
            f"#102 exactly."
        )

    async def test_scouts_pending_drain_SELECT_is_retried(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**WB-GHOST. A CORRECTNESS PIN, NOT A GATE PIN.**

        ``_drain_pending``'s SELECT is the first statement the command channel runs on
        every poll. Un-route it and a retryable conflict raises a raw SDK ``QueryError``
        that nothing classifies, nothing retries, and — per this module's own §4c — **kills
        the subscriber**. That build scored **193 passed / 0 failed on my contract and
        932 / 0 across every suite**: finding #120 shipping ALIVE in the tree certified as
        having fixed it.

        My runtime gate never fired on it **because no test ever executed
        ``_drain_pending``.** The gate was armed in four tests, so its REACH was a list of
        remembered flows — the same name-list mistake in its sixth costume. The gate is
        autouse now (conftest), and this pin exists because the property deserves a direct
        witness and not only a guard.
        """
        _silence_sleep(monkeypatch)
        connection = _ConflictingConnection(conflicts=3, rows=[])

        await _subscriber()._drain_pending(connection)

        assert connection.calls == 4, (
            f"scout's pending-command SELECT was attempted {connection.calls} time(s) "
            f"under a sustained conflict. It is the first statement of every poll, it is "
            f"unretried, and its raw SDK error kills the subscriber. #120 is alive."
        )

    async def test_scouts_kill_is_retried(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The call that exposed this. It routed, and it retried zero times."""
        _silence_sleep(monkeypatch)
        connection = _AllMethodsConflictConnection(conflicts=3)

        await _subscriber()._safe_kill(connection, "live-uuid")

        assert connection.calls.get("kill", 0) == 4, (
            f"connection.kill() was attempted {connection.calls.get('kill', 0)} time(s) — "
            f"routed through the driver and never retried. Classify + signal, or the "
            f"routing is decoration."
        )

    async def test_scouts_live_subscription_is_retried(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _silence_sleep(monkeypatch)
        connection = _AllMethodsConflictConnection(conflicts=3)
        subscriber = _subscriber()

        with contextlib.suppress(Exception):
            await asyncio.wait_for(subscriber._consume_live(connection, "live-uuid"), 5.0)

        assert connection.calls.get("subscribe_live", 0) == 4, (
            f"connection.subscribe_live() was attempted "
            f"{connection.calls.get('subscribe_live', 0)} time(s) — routed and not retried."
        )

    async def test_an_EMPTY_claim_is_a_lost_race_and_is_never_retried(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**REMOVED-BEHAVIOUR PRESERVATION** (and the pin a careless repair fails).

        An empty CAS result means ANOTHER instance already completed this command
        (scout.py's own duplicate-completion path). It is a lost race with a defined
        meaning — NOT a conflict, and NOT an error. A build that retries "nothing came
        back" re-runs a claim the engine correctly refused, hammering a row another
        instance owns, and turns one duplicate-completion log line into a storm.
        """
        _silence_sleep(monkeypatch)
        recorder = _record_shared_jitter(monkeypatch)
        connection = _ScriptedConnection(error=AssertionError("unused"), failures=0, rows=[])

        await _subscriber()._mark(connection, "command:1", "done")

        assert connection.calls == 1, (
            f"scout retried an EMPTY claim {connection.calls - 1} times. An empty result "
            f"is not a conflict — it is another instance having already completed the "
            f"command, which scout logs as a duplicate completion and must never contest."
        )
        assert not recorder.draws, "an empty claim backed off — it was treated as contention"


# ===========================================================================
# 5. THE PIN THAT MATTERS MOST — IDEMPOTENCY UNDER RETRY, LIVE.
#
# Retrying a single statement is only safe because a CONFLICT means it did not commit.
# That is a claim about SurrealDB 3.1.5, so it is MEASURED against SurrealDB 3.1.5 —
# 16 genuinely concurrent racers on ONE hot row, exactly the shape the brief mint runs
# in production.
#
# THE ORACLE IS EXACT. N racers, one mint each, off a counter that only ever
# increments: exactly-once <=> the minted versions are {1..N} AND the counter row ends
# at N. A retry that double-applied would push the counter above N and tear a GAP in
# the versions. Nothing here is statistical.
#
# THE CONTROL: the run must actually have RETRIED something (the shared-jitter recorder
# is consulted). A contention pin that never contended proves nothing, and would pass
# on a build with no retry at all. What the control may NOT do is fail a correct build —
# see ``_run_contending_waves`` for how that guarantee is kept WITHOUT the control
# becoming a coin-flip under the runner this repo mandates.
# ===========================================================================


@pytest_asyncio.fixture()
async def live_env() -> Any:
    env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    admin = await connect_admin(env)
    await run(admin, "DEFINE TABLE IF NOT EXISTS retry_counter SCHEMAFULL")
    await run(admin, "DEFINE FIELD OVERWRITE next ON retry_counter TYPE int DEFAULT 0")
    await admin.close()
    try:
        yield env
    finally:
        await drop_database(env)


# ---------------------------------------------------------------------------
# THE ANTI-VACUITY CONTROL, REPAIRED — and the repair is the DUAL of this repo's
# fixtures-must-discriminate law.
#
# WHAT WAS BROKEN (audit-dry-2 §3.3-3.4, root-caused and measured, not guessed): the two
# 16-way pins below asserted ``recorder.draws`` — "did we actually retry anything?" — as a
# FATAL assertion on ONE wave of racers. Under the runner this repo MANDATES (`-n auto`),
# that assertion fired on a CORRECT build **2 runs in 20 on an IDLE machine (10%)**, and
# **0 in 20 without xdist**: the failure is xdist-SPECIFIC, not load-specific, so "run it on
# a quiet box" never fixes it. Every captured failure — the auditor's 2, the predecessor's
# 3, the builder's — failed on that control and NEVER on the oracle; the exactly-once
# property itself held across 85 independent live 16-way rounds (three load regimes,
# 11-21 genuine retries each, ZERO violations).
#
# The control was RIGHT and the fixture was WRONG. A pin that goes red on correct code
# manufactures the "flaky" verdict — and "flaky" is the verdict that shipped C1's mint
# defect. This repo's law says a failing test is a STOP; it cannot also ship a test that
# fails a correct build 10% of the time.
#
# WHAT IS TRUE, AND IT IS TRUE BY CONSTRUCTION: ``draws == 0`` <=> the driver never
# retried <=> the retry path never ran <=> a RETRIED write cannot have double-applied,
# because there was no retried write. **A wave with zero conflicts is VACUOUS, not
# failing.**
#
# THE REPAIR — and it took TWO parts, because the first one alone did not work and this
# comment is derived from what was MEASURED, not from what was intended.
#
# PART 1 — a vacuous wave is RE-RUN, not failed:
#   * the exactly-once ORACLE is asserted on EVERY wave, contended or not — it is exact,
#     it is cheap, and it is always meaningful, so it is never skipped;
#   * a wave that produced no conflict is re-run, against a FRESH counter row, up to a
#     small bound;
#   * the run fails only when NO wave in the bound produced a single conflict — which is
#     no longer "the racers got unlucky once" but "retry is DEAD", and that is exactly what
#     the neutered-classifier mutation proof produces (audit-dry-2 §2.2, re-run against
#     THIS fixture: both pins RED).
#
# PART 1 WAS NOT ENOUGH, AND THE MEASUREMENT SAYS WHY. Five waves at an independent 10%
# vacuity rate should fail ~1 run in 100 000. Measured over 120 runs of Part 1 alone: **1
# red in ~120 (~1%)** — and the captured failure was all FIVE waves vacuous
# (``scratchpad/contract-fix/hunt2-red-56.log``). **THE WAVES ARE NOT INDEPENDENT.** A
# worker that falls into the non-overlapping regime STAYS in it for the whole test, so five
# correlated waves buy roughly one trial's worth of protection. Re-running a correlated
# experiment is not a fix; it is the same experiment, five times.
#
# PART 2 — make the racers actually MEET. The mechanism the barrier misses: **a Barrier
# synchronises PYTHON, not the WIRE.** All 16 coroutines are released together, but each
# then awaits its own socket, and the sends spread out in time. If the engine's commit
# window (~1ms) is narrower than the spread, sixteen "concurrent" mints arrive as sixteen
# SEQUENTIAL ones and NOTHING contends — no matter how tightly they started. Contention was
# never a property of the release; it is a property of the racers' LIFETIMES overlapping.
#
# So each racer now mints REPEATEDLY (:data:`_MINTS_PER_RACER`). A racer is in flight for
# the whole run rather than for one round trip, so the windows overlap by construction
# instead of by luck — and the ORACLE GETS STRONGER, not weaker: 16 x N mints off ONE
# counter must still be exactly {1..16N}, and the row must end at 16N. More retried writes,
# and every one of them still has to land exactly once.
#
# The anti-vacuity guarantee is PRESERVED EXACTLY throughout. It is not weakened, softened,
# or downgraded to a warning: a build that never retries is still RED here, on every wave.
# ---------------------------------------------------------------------------

# Waves a contention pin may run before it declares retry dead. Kept as belt-and-braces
# behind Part 2 — it is no longer load-bearing (measured below), and a bound that never
# fires is exactly the kind of "guard" this repo has learned to distrust, so it is stated
# honestly: it exists to convert a residual, correlated unlucky run into a re-run rather
# than a phantom seam defect.
_CONTENTION_WAVE_BOUND = 5

# Mints per racer. The knob that makes contention STRUCTURAL rather than incidental: with
# one mint each, sixteen racers overlap only if their sends land inside one commit window;
# with N each, every racer is in flight across the others' whole run.
#
# MEASURED on this box (both pins, `-n auto`, the mandated runner): with N=1, 1 red in ~120
# runs — all five waves vacuous. With the values below: **0 red in 100 consecutive runs**,
# and every single wave contended on its FIRST try (the wave bound above never fired once).
# See ``scratchpad/contract-fix/``.
_MINTS_PER_RACER = 8
# Publishing is the heavier operation (a mint, then a CREATE, then a read-back), so fewer
# rounds buy the same overlap. The oracle is identical in shape: 16 x 4 gapless versions.
_PUBLISHES_PER_RACER = 4

_NO_WAVE_CONTENDED = (
    "NOT ONE conflict was retried across {racers} concurrent racers on ONE row — in ANY "
    "of {bound} independent waves. The exactly-once oracle was asserted on every wave and "
    "held, but the retry path this pin exists to certify never ran even once. A build with "
    "NO RETRY AT ALL lands here, so this is not a pass: either the driver is dead (classify "
    "-and-signal is the usual corpse — routing alone retries zero times), or the harness can "
    "no longer make these racers meet in the engine and the fixture must be re-measured."
)


async def _run_contending_waves(
    recorder: _JitterRecorder, wave: Callable[[int], Awaitable[bool]]
) -> None:
    """Run ``wave(index)`` until one of them genuinely CONTENDED, bounded by
    :data:`_CONTENTION_WAVE_BOUND`.

    ``wave`` owns — and always asserts — its OWN exactly-once oracle, and returns whether
    the racers actually conflicted. This helper owns ONLY the anti-vacuity control: it
    re-runs a wave that produced no conflict, and fails when no wave produced one.

    Each wave MUST mint against a FRESH row (the caller varies it by ``index``): a second
    wave against the counter the first already advanced would compare its oracle to the
    wrong baseline and go red for a bookkeeping reason.
    """
    for wave_index in range(_CONTENTION_WAVE_BOUND):
        recorder.draws.clear()
        if await wave(wave_index):
            return
    raise AssertionError(_NO_WAVE_CONTENDED.format(racers=_RACERS, bound=_CONTENTION_WAVE_BOUND))


class TestSingleStatementRetryLandsExactlyOnce:
    """A retried single-statement write lands EXACTLY ONCE — no double-write, no
    double-increment — under real 16-way contention.
    """

    async def test_sixteen_racers_minting_one_counter_land_exactly_once_each(
        self, live_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Each racer mints :data:`_MINTS_PER_RACER` times, so the racers' LIFETIMES overlap
        instead of only their start instants (see the section note: a barrier synchronises
        Python, not the wire). The oracle scales with it and gets STRONGER — 16 x N mints
        off one counter must be exactly {1..16N}, and the row must end at 16N.
        """
        recorder = _record_shared_jitter(monkeypatch)
        stores = [_construct_live(SurrealStore, live_env) for _ in range(_RACERS)]
        expected_total = _RACERS * _MINTS_PER_RACER

        async def _wave(wave_index: int) -> bool:
            name = f"{_WAVE_NAME}-{wave_index}"
            barrier = asyncio.Barrier(_RACERS)
            minted: list[int] = [
                version
                for versions in await asyncio.gather(
                    *(self._mint(store, barrier, name) for store in stores)
                )
                for version in versions
            ]
            # Read the control BEFORE the verification SELECT below: that SELECT's own
            # (unlikely) conflict is not the racers' contention and must never be counted
            # as it — an instrument that credits itself is the whole disease.
            contended = bool(recorder.draws)
            rows = await stores[0]._query(
                "SELECT next FROM type::record('retry_counter', $name)", {"name": name}
            )

            assert sorted(minted) == list(range(1, expected_total + 1)), (
                f"the {_RACERS} racers minted {len(minted)} numbers that are not the exact "
                f"run 1..{expected_total} — a retried write DOUBLE-APPLIED (the counter "
                f"jumped, tearing a gap) or two racers took one number. Retry on this path "
                f"is NOT safe and the refactor must stop. Got: {sorted(minted)}"
            )
            assert int(rows[0]["next"]) == expected_total, (
                f"the counter row ended at {rows[0]['next']} after {expected_total} single "
                f"mints — a conflicted statement COMMITTED and was then retried, applying twice"
            )
            return contended

        try:
            await asyncio.gather(*(store._ensure_connection() for store in stores))
            await _run_contending_waves(recorder, _wave)
        finally:
            for store in stores:
                await store.close()

    @staticmethod
    async def _mint(store: SurrealStore, barrier: asyncio.Barrier, name: str) -> list[int]:
        await barrier.wait()
        minted: list[int] = []
        for _ in range(_MINTS_PER_RACER):
            rows = await store._query(_MINT_STATEMENT, {"name": name})
            minted.append(int(rows[0]["next"]))
        return minted


class TestConcurrentFirstConnectsSurviveTheBootstrapRace:
    """**THE SIXTH HOLE — and I found it in my OWN gate's one allowance.**

    16 stores, ALL connecting for the first time, against a database NOTHING has defined
    yet. Every one of them runs ``DEFINE NAMESPACE IF NOT EXISTS`` + ``DEFINE DATABASE IF
    NOT EXISTS`` on a virgin connection, and they contend.

    Measured before any repair (probe_bootstrap_ddl_race.py, 10 rounds — ONE run; the rate
    is noisy and ranges 6.2%-34.4% across runs, see _UNRETRIED_BOOTSTRAP_LOSS):
        160 connects attempted · 21 failures · ALL 21 retryable conflicts,
        each surfaced as ``SurrealConnectionError: could not connect to SurrealDB``.

    Two defects in one: the DDL is unretried, AND a conflict is reported as a TRANSPORT
    fault — the caller is told the server is unreachable when it is merely busy.

    **WHY NO FIXTURE IN THIS REPO HAS EVER SEEN THIS, INCLUDING MY OWN 16-WAY PINS:** they
    all call ``connect_admin()`` first, which CREATES the namespace and database. Every
    racer's ``IF NOT EXISTS`` is then a no-op on an object that already exists, and
    no-ops do not contend. **The pins passed for a fixture reason.** This one does not
    pre-create anything — that is the entire difference, and it is the whole finding.
    """

    async def test_sixteen_concurrent_first_connects_to_a_virgin_database_all_succeed(
        self,
    ) -> None:
        database = unique_database()
        env: SurrealEnv = make_env(database=database, dim=PRODUCTION_DIM)
        stores = [
            SurrealStore(
                url=env.url,
                namespace=env.namespace,
                database=env.database,
                dim=env.dim,
                user=env.user,
                password=env.password,
            )
            for _ in range(_RACERS)
        ]
        try:
            outcomes = await asyncio.gather(
                *(store._ensure_connection() for store in stores), return_exceptions=True
            )
        finally:
            for store in stores:
                await store.close()
            await drop_database(env)

        failures = [
            f"{type(outcome).__name__}: {outcome}"
            for outcome in outcomes
            if isinstance(outcome, BaseException)
        ]
        assert not failures, (
            f"{len(failures)} of {_RACERS} concurrent FIRST connects to a virgin database "
            f"failed: {failures[:3]}. The connection-bootstrap DDL contends like any other "
            f"write — and a retryable conflict on it is currently reported as "
            f"SurrealConnectionError ('could not connect'), which is both unretried and "
            f"untrue: the server is reachable, it is busy. Route the bootstrap DDL through "
            f"the seam. NOTE the fixture: nothing pre-creates the database here, which is "
            f"the ONLY reason this is visible — every other live pin in this repo, mine "
            f"included, calls connect_admin() first and turns the DDL into a no-op."
        )


class TestBriefPublishLandsExactlyOnceUnderContention:
    """The same oracle, end to end, through the REAL production mint.

    The existing 8-way race in test_brief_ledger.py must stay green; this one raises
    the degree to 16 and adds the assertion that pin never made — that the COUNTER ROW
    itself ends at N. A double-applying retry burns a version, and a burnt version is
    invisible to a test that only checks the versions it was handed.
    """

    async def test_sixteen_concurrent_publishes_burn_no_version(
        self, live_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Wave-bounded exactly like its sibling, and for the same measured reason (see the
        section note): the oracle runs on every wave; only the anti-vacuity control gets to
        ask for another one.

        Each wave publishes under a DISTINCT brief name, so each gets its own virgin
        ``brief_counter`` hot row and its own {1..N} version run.
        """
        recorder = _record_shared_jitter(monkeypatch)
        ledgers = [
            BriefLedger(
                url=live_env.url,
                namespace=live_env.namespace,
                database=live_env.database,
                user=live_env.user,
                password=live_env.password,
            )
            for _ in range(_RACERS)
        ]

        expected_total = _RACERS * _PUBLISHES_PER_RACER

        async def _wave(wave_index: int) -> bool:
            name = f"{_WAVE_NAME}-{wave_index}"
            barrier = asyncio.Barrier(_RACERS)

            async def _publish(index: int, ledger: BriefLedger) -> list[int]:
                await barrier.wait()  # see the determinism note on the sibling pin
                published: list[int] = []
                for round_index in range(_PUBLISHES_PER_RACER):
                    result = await ledger.publish(
                        name, f"standing instruction {index}.{round_index}", created_by="lead"
                    )
                    published.append(result.brief.version)
                return published

            results = await asyncio.gather(
                *(_publish(index, ledger) for index, ledger in enumerate(ledgers))
            )
            contended = bool(recorder.draws)  # read BEFORE the verification SELECT
            counter = await ledgers[0]._query(
                "SELECT next FROM type::record('brief_counter', $name)", {"name": name}
            )

            versions = sorted(version for published in results for version in published)
            assert versions == list(range(1, expected_total + 1)), (
                f"{expected_total} concurrent publishes minted {versions} — not a gapless "
                f"consecutive run"
            )
            assert int(counter[0]["next"]) == expected_total, (
                f"the brief_counter row ended at {counter[0]['next']} after {expected_total} "
                f"publishes — a retry double-incremented it and burnt a version"
            )
            return contended

        try:
            await ledgers[0].ensure_ready()
            await asyncio.gather(*(ledger._ensure_connection() for ledger in ledgers))
            await _run_contending_waves(recorder, _wave)
        finally:
            for ledger in ledgers:
                await ledger.close()


# ===========================================================================
# 6. THE INVARIANT LOSES ITS LAST EXEMPTION.
#
# ``briefs.py`` was the ONE production site branching on an exception's MESSAGE, and
# the single grandfathered exemption in the no-prose-branching pin
# (test_surreal_store.py::TestNoProductionModuleHoldsAClassificationLabel). It is now
# DELETED, the exemption set is EMPTY, and the ban widens from "holds a label" to
# "mentions one at all, in code or in prose".
#
# The prose half is not decoration. briefs.py:634's docstring still TEACHES the
# coupling ("that label — and ONLY that label — is retried here"), and an AST scan
# cannot see a docstring. A future agent reads the prose, not the AST. This repo has
# now shipped ten defects in the class "English beside the code that says what the code
# does, and is wrong" — and CLAUDE.md's own answer is that a defect class gets an
# INSTRUMENT, in the same breath as the law.
# ===========================================================================

# The label constants' one legitimate home: the module that DEFINES them and classifies
# engine text. It is the invariant's subject, not its exception.
_LABEL_HOME = "store/_txn.py"

_LABEL_PREFIX = "_ERROR_CLASS_"
# The engine's own raw marker. After this wave it is consumed strictly INSIDE the seam:
# both conflict detectors (the response scan and the exception scan) live in _txn.py, so
# no caller has any business naming it — and a caller that names it is one refactor away
# from branching on it.
_MARKER_NAME = "_RETRYABLE_CONFLICT_MARKER"
_MARKER_TEXT = "can be retried"


def _production_modules() -> list[Path]:
    return sorted(
        path
        for path in _PACKAGE_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
        and path.relative_to(_PACKAGE_ROOT).as_posix() != _LABEL_HOME
    )


class TestNoCallerEverReadsAnEngineMessage:
    """A classification label is a human-facing summary; the engine's marker is raw
    wire text. Neither is an API, and no caller may hold either — not in a branch, not
    in a local, not in a docstring that teaches the next agent to write the branch.

    This is a TRIPWIRE, and it is honest about that: the guard against #102 is
    behavioural and lives in test_txn_contention.py
    (``TestContentionIsNeverReportedAsALostRace`` re-runs every pass-through pin against
    a REWORDED label). Three earlier contract revisions tried to forbid the coupling
    with ever-more-elaborate AST scanners and a cold adversary walked through each one.
    What survives is narrow, precise, and had ZERO false positives against the live
    tree: nobody outside ``store/_txn.py`` may so much as NAME these things.
    """

    def test_no_production_module_mentions_a_classification_label(self) -> None:
        """RED today: briefs.py imports ``_ERROR_CLASS_RETRYABLE_CONFLICT`` (line 107),
        teaches it in a docstring (line 634) and branches on it (line 677).
        """
        offenders = {
            path.relative_to(_PACKAGE_ROOT).as_posix(): [
                index
                for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
                if _LABEL_PREFIX in line
            ]
            for path in _production_modules()
        }
        held = {module: lines for module, lines in offenders.items() if lines}

        assert not held, (
            f"production code outside {_LABEL_HOME} names a classification label: {held}. "
            f"A label is a human-facing summary, not an API — finding #93 reworded one "
            f"and silently killed the retry loop that depended on it (that is finding "
            f"#102). Branch on the exception TYPE: catch TxnContentionExhaustedError. "
            f"A DOCSTRING counts: prose that teaches the coupling is how the next agent "
            f"writes it back."
        )

    def test_no_production_module_holds_the_engines_conflict_marker(self) -> None:
        """The marker is the seam's private business. Detection lives in ``_txn.py`` on
        BOTH paths — the response scan and the exception scan — precisely so that two
        callers can never end up with two different ideas of what a conflict IS.

        Green today (a RATCHET, not a repair) except for briefs.py's docstring, which
        quotes the marker while teaching the retry it is about to lose.
        """
        offenders = {
            path.relative_to(_PACKAGE_ROOT).as_posix(): [
                index
                for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
                if _MARKER_NAME in line or _MARKER_TEXT in line
            ]
            for path in _production_modules()
        }
        held = {module: lines for module, lines in offenders.items() if lines}

        assert not held, (
            f"production code outside {_LABEL_HOME} names the engine's retryable-conflict "
            f"marker: {held}. Conflict DETECTION is the seam's own; a caller signals one "
            f"by raising RetryableConflictSignal from its attempt, and hears about "
            f"exhaustion as a TYPE."
        )


class TestTheAttemptFloorOutlivesItsBriefsConsumer:
    """``_MAX_TXN_CONFLICT_ATTEMPTS`` SURVIVES this wave — it is the seam's guaranteed
    attempt FLOOR (audit-102 B1), the pre-#102 five-attempt guarantee every caller had
    before the deadline existed.

    It replaces ``TestBriefsInheritedConflictBudgetIsNotSilentlyRepointed``, which
    pinned the OPPOSITE world: that briefs.py imports this constant and multiplies it
    into a private 20-attempt budget. That test certified the corpse — a suite can be
    green BECAUSE it still asserts what the change deletes.
    """

    def test_the_floor_is_still_five(self) -> None:
        assert _MAX_TXN_CONFLICT_ATTEMPTS == 5, (
            "the attempt floor changed value — it is not a tuned number but the "
            "pre-#102 behavioural contract itself, and re-tuning it silently re-tunes "
            "the non-regression guarantee every caller depends on"
        )

    def test_no_production_module_outside_the_seam_consumes_the_floor(self) -> None:
        """RED today: briefs.py:108 imports it to compose its own budget.

        A constant tuned for one purpose and silently inherited by another IS finding
        #102's trap. After this wave the floor has exactly one consumer — the driver
        that owns the policy.
        """
        consumers = {
            path.relative_to(_PACKAGE_ROOT).as_posix()
            for path in _production_modules()
            if "_MAX_TXN_CONFLICT_ATTEMPTS" in path.read_text(encoding="utf-8")
        }

        assert not consumers, (
            f"{sorted(consumers)} still consume the seam's attempt floor. The retry "
            f"policy has ONE owner now; a caller that reaches for its constants is "
            f"rebuilding the policy beside it."
        )


# ===========================================================================
# 7. THE DOC THAT GENERATED THE DEFECT.
#
#     DESIGN-LAW.md:75  "The reference pattern for ANY new hot-row mint is
#                        `_txn.execute_transaction`'s conflict-retry seam: per-attempt
#                        FULL jitter ... a guaranteed attempt FLOOR ... a wall-clock
#                        deadline ..."
#
# That sentence is an instruction to REPRODUCE a mechanism. It was obeyed twice and
# produced two findings. Standing law now has a function to CALL, and this pin is what
# keeps it that way — because CLAUDE.md's own lesson from the ten-instance C1 wave is
# that a rule people must remember is not a guard; it is a hope.
# ===========================================================================

_DESIGN_LAW = _REPO_ROOT / "docs" / "plans" / "v2" / "DESIGN-LAW.md"
_HOT_ROW_HEADING = "Hot-row minting"


def _hot_row_bullet() -> str:
    """The DESIGN-LAW bullet a future agent reads before writing a hot-row mint: from
    the ``Hot-row minting`` marker to the start of the next top-level bullet.
    """
    lines = _DESIGN_LAW.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if _HOT_ROW_HEADING in line)
    bullet = [lines[start]]
    for line in lines[start + 1 :]:
        if line.startswith("- ") or line.startswith("#"):
            break
        bullet.append(line)
    return "\n".join(bullet)


class TestStandingLawNamesTheFunctionInsteadOfDescribingIt:
    def test_the_hot_row_bullet_tells_the_reader_what_to_CALL(self) -> None:
        """RED today: the bullet describes a mechanism and never names a callable."""
        bullet = _hot_row_bullet()

        assert "retry_on_conflict" in bullet, (
            "DESIGN-LAW's hot-row-mint law does not name the function to CALL. A doc "
            "that describes a retry mechanism is a doc that will be re-implemented — "
            "twice, so far, each time with a different jitter bug (#102, #108)."
        )

    def test_the_hot_row_bullet_does_not_prescribe_a_pattern_to_reproduce(self) -> None:
        """RED today: it says "The reference pattern for ANY new hot-row mint is ...".

        Prose that describes behaviour must be DERIVED from the behaviour, not restated
        beside it (CLAUDE.md). The only honest instruction now is a call.
        """
        bullet = _hot_row_bullet().lower()

        assert "reference pattern" not in bullet, (
            "DESIGN-LAW still prescribes a PATTERN for hot-row mints. There is nothing "
            "to clone any more — it is a function you call. A doc that says 'clone this' "
            "is a defect generator, and this repo has the two findings to prove it."
        )


class TestNoStoreModuleTeachesTheRetiredMigrationVerb:
    """Finding #107 (a 100% ``brief_publish`` production outage): ``DEFINE FIELD IF NOT
    EXISTS`` is a NO-OP against an EXISTING field, so a widened field ASSERT never
    migrated a live store. Fields are ``DEFINE FIELD OVERWRITE`` now — the code emits
    the old verb NOWHERE.

    ``surreal_schema.py:873`` still TEACHES it as the live mechanism. Same class as
    every other defect in this session: a natural-language surface whose consistency
    with the code no gate checks. So: a gate.

    SCOPE, stated because a gate that overstates its reach is the thing it polices:
    this scans the PACKAGE only. ``docs/reference/surrealdb-31-capabilities.md``, this
    repo's CLAUDE.md and the #107 pins MUST name the verb — teaching the gotcha is
    their job. Tables, indexes and the analyzer deliberately STAY ``IF NOT EXISTS``
    (an ``INDEX OVERWRITE`` would rebuild a populated HNSW), so the pattern is
    FIELD-specific by construction, and the namespace/database DDL is untouched.

    WHAT IT DOES NOT CATCH: a claim that names no verb. ``findings.py:472`` and
    ``tasks.py:484`` say "The DDL is ``IF NOT EXISTS``, so a second call neither raises
    nor wipes data" — now only half true (the DDL is a MIX), and invisible to any
    pattern that does not false-fire on the table/index DDL. Those are flagged for the
    builder by hand, and this pin does not pretend to cover them.
    """

    def test_no_package_module_names_define_field_if_not_exists(self) -> None:
        offenders = {
            path.relative_to(_PACKAGE_ROOT).as_posix(): [
                index
                for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
                if "DEFINE FIELD IF NOT EXISTS" in line
            ]
            for path in _PACKAGE_ROOT.rglob("*.py")
            if "__pycache__" not in path.parts
        }
        held = {module: lines for module, lines in offenders.items() if lines}

        assert not held, (
            f"production code still teaches `DEFINE FIELD IF NOT EXISTS` as the live "
            f"field mechanism: {held}. It is a NO-OP on an existing field — that is "
            f"finding #107, a 100% production outage — and the code has emitted "
            f"`DEFINE FIELD OVERWRITE` since it was fixed."
        )


# ===========================================================================
# 7. THE FIX WAVE — the four defects the cold audits found in the DRY consolidation,
#    each pinned before a builder touches it.
#
#    Provenance, so nobody has to trust me: REPORT-blindreader-dry-1.md (a CONTRACT-BLIND
#    diff read — its frame was "what happens to each input, and what did the deleted code
#    do that this does not?", the one question no contract-holding auditor asks) found F1,
#    F2, F3, F4; REPORT-audit-dry-2.md (the cold REFUTE audit) found the broken instrument
#    repaired in section 5 above, and ruled on the test harness's private marker copy.
#
#    Sections 7a-7e below. Every pin here is RED against the wave as it stands EXCEPT the
#    ones that pin behaviour the wave already has and must not lose — those are marked
#    PRESERVATION and are green, because a removed-behaviour inventory whose items are all
#    red is not an inventory, it is a rewrite.
# ===========================================================================


# ---------------------------------------------------------------------------
# 7a. THE ACK EDGE — exhausted contention is not an idempotent re-ack.
#     (blindreader F1 — HIGH. "The single worst thing" in that report.)
#
# BEFORE the wave, ``BriefLedger._query`` never retried, so the ONLY exception that could
# reach ``_relate_briefed``'s ``except SurrealStoreError`` was a DOMAIN rejection — which
# is exactly the signal that handler is built to read: a UNIQUE(in, out) violation means
# "this pair is already acked", so re-read the edge and report ``already_acked=True``.
# Sound, because a domain rejection means THE ROW ALREADY EXISTS.
#
# AFTER the wave, ``_query`` rides the shared driver, so it can raise
# ``TxnContentionExhaustedError`` — a ``SurrealStoreError`` SUBCLASS whose meaning is the
# exact OPPOSITE: *our RELATE never committed, and we do not know what is there*. It lands
# in the same ``except``. Under sustained contention on the edge row (two agents acking the
# same (agent, brief) pair — a documented, real race in this file: the register-then-
# explicit path), the handler re-reads, finds the RACER's edge, and returns
# ``(already_acked=True, via=<the racer's via>)``. The caller is told its ack was an
# idempotent no-op against an existing edge. It was not. **It was dropped.**
#
# ``TxnContentionExhaustedError``'s own docstring names this hazard and names the fix:
# a caller that must not treat exhausted contention as a lost compare-and-set "opts in by
# catching THIS type FIRST, above its own ``SurrealStoreError`` handler".
# ``findings.py:1049`` and ``tasks.py:927`` both carry that guard. ``briefs.py`` — the file
# this wave rewrites, and the file whose seam newly GAINED the ability to raise it — has no
# exhaustion guard on any of its three handlers.
#
# THE FIXTURE THAT DISCRIMINATES, and it is the whole pin: **the racer's edge must be
# PRESENT.** With no edge in the store, the unguarded handler re-raises anyway (there is
# nothing to attribute the failure to) and a pin written that way passes a broken build.
# Both edge-states are forced below, because "the same wrong build must fail" is the only
# question a fixture answers.
# ---------------------------------------------------------------------------

# The LIVE text of a UNIQUE(in, out) violation on the ``briefed`` edge — CAPTURED against
# spike-surreal 3.1.5 (``scratchpad/contract-fix/probe_unique.py``), never hand-typed:
#     surrealdb.errors.InternalError · kind=Internal · details=None
# "fixture and code shared one imagination" is how the dead ``"assert"`` marker survived
# this repo's entire life; the domain rejection this handler reads is captured, like every
# other engine shape in this module.
_LIVE_UNIQUE_EDGE_TEXT = (
    "Database index `briefed_unique` already contains [agent:a1, brief:b1], with record "
    "`briefed:bwxkw5y0buakqzsy3vyd`"
)

_ACK_AGENT_ID = "0199c4f1-7d2a-7c3e-9b41-2f6ad8e5c110"
_ACK_BRIEF_ID = "3f1c9d5e7a0b4c2d8e6f1a3b5c7d9e02"
_ACK_VERSION = 3
# The via the RACER already wrote. Deliberately NOT the via this ack is attempting: a
# handler that reports ``already_acked=True`` hands the caller SOMEONE ELSE'S value, and
# the pin should be able to see whose.
_ACK_RACERS_VIA = "register"
_ACK_ATTEMPTED_VIA = "explicit"


def _unique_edge_error() -> InternalError:
    """The engine's UNIQUE(in, out) rejection — a DOMAIN error, never retried."""
    return InternalError(ErrorKind.INTERNAL, _LIVE_UNIQUE_EDGE_TEXT)


@dataclass
class _AckConnection:
    """The ack path's wire, with the RELATE's fate under the test's control.

    Serves ``ack()``'s two SELECTs (the brief's versions, then the existing edge) and fails
    the RELATE the way the test asks. ``relate_error`` is raised on EVERY RELATE attempt, so
    a retryable conflict makes the **REAL driver** exhaust and raise the **REAL**
    ``TxnContentionExhaustedError`` — never a hand-built one posted through a monkeypatch,
    which would prove only that the handler catches what the test threw at it.

    ``existing_edge_via`` decides what ``_select_briefed_edge`` finds afterwards, and it is
    the discriminator: ``None`` means no edge exists (the handler has nothing to
    misattribute the failure to and re-raises for the WRONG reason); a value means a
    racer's edge is sitting there, and an unguarded handler will report the dropped ack as
    that racer's successful re-ack.
    """

    relate_error: BaseException
    existing_edge_via: str | None
    relate_calls: int = field(default=0, init=False)

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        if statement.startswith("RELATE"):
            self.relate_calls += 1
            if self.relate_calls > _ABSURD_ATTEMPT_CEILING:
                raise AssertionError("unbounded retry on the ack RELATE")
            raise self.relate_error
        if statement.startswith(f"SELECT * FROM {BRIEF_TABLE} "):
            return [
                {
                    "id": RecordID(BRIEF_TABLE, _ACK_BRIEF_ID),
                    "name": _WAVE_NAME,
                    "version": _ACK_VERSION,
                }
            ]
        if statement.startswith(f"SELECT * FROM {BRIEFED_RELATION} "):
            if self.existing_edge_via is None:
                return []
            return [{"via": self.existing_edge_via, "in": RecordID(AGENT_TABLE, _ACK_AGENT_ID)}]
        raise AssertionError(
            f"the ack path issued a statement this fake does not serve: {statement!r}"
        )

    async def close(self) -> None:
        return None


async def _ack_through(ledger: BriefLedger) -> Any:
    return await ledger.ack(
        agent_id=_ACK_AGENT_ID,
        agent_name="contract-fix-1",
        name=_WAVE_NAME,
        version=_ACK_VERSION,
        via=_ACK_ATTEMPTED_VIA,
    )


class TestTheAckEdgeNeverReportsAnExhaustedRelateAsAReAck:
    """**blindreader F1.** ``_relate_briefed``'s ``except SurrealStoreError`` is the one
    guarded-CAS handler in the package that never learned ``TxnContentionExhaustedError``
    — and the seam beneath it just gained the ability to raise it.

    THE QUANTIFIER LAW (PR93): the invariant is not "the bug we found does not happen". It
    is **∀ ways the RELATE can fail, the caller is told the truth** — so every fate below
    is FORCED by its own fixture, and the two that matter are distinguished only by whether
    a racer's edge happens to be sitting in the store.
    """

    @pytest.mark.parametrize(
        "existing_edge_via",
        [
            pytest.param(_ACK_RACERS_VIA, id="A-RACERS-EDGE-IS-PRESENT-the-defect"),
            pytest.param(None, id="no-edge-exists-at-all"),
        ],
    )
    async def test_exhausted_contention_on_the_ack_RELATE_raises_the_TYPED_error(
        self, monkeypatch: pytest.MonkeyPatch, existing_edge_via: str | None
    ) -> None:
        """RED today in the ``A-RACERS-EDGE-IS-PRESENT`` case: the handler catches the
        exhaustion, re-reads, finds the racer's edge and returns
        ``BriefAckResult(already_acked=True, via='register')`` — a successful idempotent
        re-ack, reported for a write that never landed.

        Green today in the no-edge case, and it is here as the CONTROL: it proves the
        parametrised pin is not passing merely because everything raises. Only the fixture
        with an edge in it can tell a guarded handler from an unguarded one.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)  # the floor governs: exhaust in 5 attempts
        connection = _AckConnection(
            relate_error=_conflict_error(), existing_edge_via=existing_edge_via
        )
        ledger = _ledger_on(connection)

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await _ack_through(ledger)

        assert connection.relate_calls == _MAX_TXN_CONFLICT_ATTEMPTS, (
            f"the ack RELATE was attempted {connection.relate_calls} time(s) against "
            f"sustained contention — it does not ride the shared driver's budget"
        )
        assert exc_info.value.attempts == connection.relate_calls
        assert _LIVE_CONFLICT_TEXT not in str(exc_info.value), (
            "ledger #31: the raised message must never echo the raw engine text"
        )

    async def test_a_UNIQUE_violation_still_reports_the_honest_idempotent_re_ack(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**PRESERVATION + POSITIVE CONTROL.** The sibling fate, and the reason the guard
        must go ABOVE the existing handler rather than replace it.

        A genuine ``UNIQUE(in, out)`` violation means the row is ALREADY THERE. That is not
        a lost write; it is the idempotent re-ack this ledger promises, and it must keep
        reporting ``already_acked=True`` with the FIRST-recorded ``via`` (first-write-wins
        — a re-ack via a different route never overwrites it).

        This is also the control for the pin above: it proves the ``already_acked=True``
        branch is REACHABLE with this fixture. Without it, a build that simply raised on
        every RELATE failure would pass the exhaustion pin and have quietly deleted the
        idempotency the ledger's whole ack contract rests on.
        """
        _silence_sleep(monkeypatch)
        connection = _AckConnection(
            relate_error=_unique_edge_error(), existing_edge_via=_ACK_RACERS_VIA
        )

        result = await _ack_through(_ledger_on(connection))

        assert result.already_acked is True
        assert result.via == _ACK_RACERS_VIA, (
            f"the idempotent re-ack reported via={result.via!r}; the FIRST-recorded value "
            f"is {_ACK_RACERS_VIA!r} and first-write-wins is the ledger's contract"
        )
        assert connection.relate_calls == 1, (
            f"a UNIQUE violation was retried {connection.relate_calls - 1} time(s) — a "
            f"domain rejection can never succeed on retry, and hammering the engine with a "
            f"write it has already refused is what a too-broad `except` produces"
        )

    async def test_a_domain_rejection_on_a_GENUINELY_NEW_pair_still_propagates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**PRESERVATION.** The fourth cell of the fate matrix: a domain rejection with NO
        existing edge (e.g. an out-of-domain ``via`` hitting the schema's ASSERT on a brand
        new pair) has nothing to attribute itself to, so the original rejection stands —
        untyped, unretried, and LOUD.
        """
        _silence_sleep(monkeypatch)
        connection = _AckConnection(relate_error=_unique_edge_error(), existing_edge_via=None)

        with pytest.raises(SurrealStoreError) as exc_info:
            await _ack_through(_ledger_on(connection))

        assert not isinstance(exc_info.value, TxnContentionExhaustedError), (
            "a domain rejection was reported as exhausted CONTENTION"
        )
        assert connection.relate_calls == 1


# ---------------------------------------------------------------------------
# 7b. THE EXHAUSTION LOG — the message says "see the server log", and there is no line.
#     (blindreader F2 — HIGH.)
#
# ``retry_on_conflict`` raises:
#
#     "SurrealDB operation gave up after {attempts} attempts over {elapsed}s
#      (retryable conflict); see the server log for the full engine detail"
#
# ``execute_transaction`` EARNS that sentence: it stashes the last conflict and calls
# ``_log_rollback`` on the way out. **The eleven single-statement seams do not.** Their
# attempt bodies raise ``RetryableConflictSignal`` BEFORE reaching their own
# ``<x>.query.rejected`` log line, and ``retry_on_conflict`` contains no logging call at
# all. So an exhausted ``brief_publish`` / agent register / task claim / store apply emits
# **zero** log lines and hands the operator an error instructing them to go and read a line
# that was never written.
#
# BEFORE the wave, every conflicted ``_query`` logged ``<x>.query.rejected`` with the full
# ``engine_error`` and then raised; an exhausted brief mint left ~20 such lines. This is a
# straight observability regression on the ONE path where the detail matters, wearing prose
# that says otherwise — and the second-order twin: ``_TXN_CONFLICT_ATTEMPT_CEILING``'s own
# comment claims the ceiling is "logged when hit (see the exhaustion raise below)", and the
# exhaustion raise below logs nothing. That is served English contradicting the code, which
# is the class this repo has now shipped ten instances of; CLAUDE.md's answer is that a
# defect class gets an INSTRUMENT in the same breath as the law.
#
# THE CONTRACT: ``retry_on_conflict`` — the only place that CAN see the attempt count —
# logs EXACTLY ONE record on exhaustion, carrying the attempts and the elapsed time. It
# fires for BOTH paths, because there is only one driver. ``execute_transaction`` KEEPS its
# rolled-back detail log (the engine's per-statement text, ledger-#31-safe, server-side):
# the exhaustion record says how hard we tried; the rollback record says what the engine
# actually said. Losing the second while adding the first trades one blind spot for another.
# ---------------------------------------------------------------------------

# The event the driver logs on exhaustion. House idiom: the log MESSAGE is the event name
# and the facts ride ``extra`` (see ``store.transaction.rolled_back`` /
# ``brief.query.rejected``), so an operator greps one string and reads structured fields.
_EXHAUSTION_EVENT = "store.retry.exhausted"
# The event ``execute_transaction`` already logs with the FULL engine detail. It must
# survive the driver gaining a log of its own.
_ROLLBACK_EVENT = "store.transaction.rolled_back"
_TXN_LOGGER = "loremaster.store._txn"
# READ from the seam, never re-typed: this is the sentence the raised message makes true or
# false, and a copy of it here would be one more piece of English nobody checks.
_SERVER_LOG_HINT_TEXT = txn_module._SERVER_LOG_HINT


def _records(caplog: pytest.LogCaptureFixture, event: str) -> list[logging.LogRecord]:
    """Every captured record whose message IS ``event`` (the house's structured idiom)."""
    return [record for record in caplog.records if record.getMessage() == event]


class TestExhaustionIsLoggedExactlyOnceOnBothPaths:
    """**blindreader F2.** The raised message promises a server-side log line. One must
    exist — on every path, exactly once, carrying the two facts only the driver knows.

    The numbers are read OFF THE RAISED ERROR and compared to the record, never spelled in
    the assertion: prose (and a fixture) that describes behaviour must be DERIVED from the
    behaviour, not restated beside it. A build that logs ``attempts=5`` because someone
    typed 5 passes a hand-written assertion and fails this one the day the floor moves.
    """

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_a_single_statement_seams_exhaustion_logs_exactly_one_record(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        module_path: str,
        seam: type,
    ) -> None:
        """RED today, x10: an exhausted ``_query`` logs NOTHING and raises an error telling
        the operator to consult a log line that does not exist.
        """
        _silence_sleep(monkeypatch)
        caplog.set_level(logging.DEBUG, logger=_TXN_LOGGER)
        connection = _ConflictingConnection(conflicts=None)

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await _seam_on(seam, connection)._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        exhausted = _records(caplog, _EXHAUSTION_EVENT)
        assert len(exhausted) == 1, (
            f"{seam.__name__}._query ({module_path}) exhausted its retry budget and emitted "
            f"{len(exhausted)} `{_EXHAUSTION_EVENT}` record(s). The raised error tells the "
            f"operator to '{_SERVER_LOG_HINT_TEXT}' — and before this wave every conflicted "
            f"attempt logged the full engine text. Exactly ONE record: zero is a lie in the "
            f"error message, and one-per-attempt is a log storm for a conflict that usually "
            f"resolves."
        )
        record = exhausted[0]
        assert record.levelno >= logging.WARNING, (
            "an exhausted retry budget is not DEBUG chatter — it is the terminal "
            "disposition of a write the caller asked for and did not get"
        )
        assert getattr(record, "attempts", None) == exc_info.value.attempts, (
            "the log record must carry the attempt count the driver actually made — the "
            "same number the typed error carries. `retry_on_conflict` is the ONLY place "
            "that can see it, which is exactly why the log belongs there."
        )
        assert getattr(record, "elapsed_seconds", None) == pytest.approx(
            exc_info.value.elapsed_seconds
        ), "the log record must carry the elapsed time the typed error reports"

    async def test_the_transactional_paths_exhaustion_logs_the_same_one_record(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """One driver, one exhaustion record — for the transactional caller too.

        RED today: ``execute_transaction`` logs its rollback detail on exhaustion, but no
        record carries the ATTEMPTS or the ELAPSED time, which are the two facts the raised
        message quotes and the only two the driver owns.
        """
        _silence_sleep(monkeypatch)
        caplog.set_level(logging.DEBUG, logger=_TXN_LOGGER)
        connection = _ConflictingConnection(conflicts=None)

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await _run_execute_transaction(connection)

        exhausted = _records(caplog, _EXHAUSTION_EVENT)
        assert len(exhausted) == 1, (
            f"execute_transaction exhausted and emitted {len(exhausted)} "
            f"`{_EXHAUSTION_EVENT}` record(s). Both paths share ONE driver, so both get "
            f"the same one record — a driver that logs for the ten seams and not for the "
            f"eleventh caller has two policies again."
        )
        assert getattr(exhausted[0], "attempts", None) == exc_info.value.attempts
        assert getattr(exhausted[0], "elapsed_seconds", None) == pytest.approx(
            exc_info.value.elapsed_seconds
        )

    async def test_the_transactional_path_KEEPS_its_rolled_back_engine_detail(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**REMOVED-BEHAVIOUR PRESERVATION — and the pin the tempting simplification
        fails.**

        The blindreader's own fix shape observes that a driver-level log "would let
        ``execute_transaction`` drop its ``last_conflict`` stash". It must NOT: the two
        records answer different questions. The exhaustion record says how hard we tried
        (attempts, elapsed). The rollback record carries the ENGINE'S OWN per-statement
        text — the root cause, the statement index, every failed entry — which is the only
        thing that tells an operator WHAT conflicted, and which the raised exception may
        never carry (ledger #31: it can echo a bound value back verbatim).

        Delete the stash and the exhaustion message's "see the server log for the full
        engine detail" becomes false again — in the other direction. GREEN today, and this
        pin is why it stays green.
        """
        _silence_sleep(monkeypatch)
        caplog.set_level(logging.DEBUG, logger=_TXN_LOGGER)
        connection = _ConflictingConnection(conflicts=None)

        with pytest.raises(TxnContentionExhaustedError):
            await _run_execute_transaction(connection)

        rolled_back = _records(caplog, _ROLLBACK_EVENT)
        assert len(rolled_back) == 1, (
            f"an exhausted TRANSACTION emitted {len(rolled_back)} `{_ROLLBACK_EVENT}` "
            f"record(s). The driver's new exhaustion log does not replace this one — it "
            f"reports the BUDGET; this reports what the ENGINE said, which is the only "
            f"place the full per-statement detail is ever written (ledger #31 keeps it out "
            f"of the raised message)."
        )
        assert _LIVE_CONFLICT_TEXT in str(getattr(rolled_back[0], "engine_result", "")), (
            "the rollback record no longer carries the engine's raw conflict text — the "
            "'see the server log' hint has nothing to point at"
        )

    async def test_nothing_is_logged_when_the_conflict_RESOLVES(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**POSITIVE-CONTROL'S TWIN — the probe must be shown NOT firing, too.**

        "The exhaustion record was emitted" is worthless until it is also shown that a
        conflict which RESOLVES emits none: a build that logs on every conflicted attempt
        satisfies "exactly one record" whenever the budget happens to allow exactly one
        retry, and turns a routine 3-attempt mint into three ERROR lines in production —
        where contention is the NORMAL case (measured: 30% of statements at 16-way).

        **P-4 (contract adversary, `WB-LOGSTORM`): the assertion is on the LEVEL, not on the
        event NAME.** Forbidding only ``store.retry.exhausted`` forbids one string; the log
        storm this pin exists to prevent simply picks another one, and the build scores
        342/342. **The forbidden set is unbounded; the safe one is small** — so: a conflict
        that resolves emits NOTHING at WARNING-or-above from the driver's module, whatever it
        is called. (DEBUG is left free: it is off in production and has no consumer.)
        """
        _silence_sleep(monkeypatch)
        caplog.set_level(logging.DEBUG, logger=_TXN_LOGGER)
        connection = _ConflictingConnection(conflicts=3, rows=[{"next": 4}])

        await _store_on(connection)._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        assert connection.calls == 4, "the fixture did not actually retry — nothing is proven"
        noisy = [
            f"{record.levelname} {record.getMessage()}"
            for record in caplog.records
            if record.name == _TXN_LOGGER and record.levelno >= logging.WARNING
        ]
        assert not noisy, (
            f"a conflict that RESOLVED after 3 retries emitted {len(noisy)} record(s) at "
            f"WARNING-or-above from {_TXN_LOGGER}: {noisy}. The driver logs the terminal "
            f"disposition, NOT the journey. Contention is the NORMAL case — 30% of statements "
            f"at 16-way contention — so a line per retried attempt is a log storm in "
            f"production, and naming it something other than {_EXHAUSTION_EVENT!r} does not "
            f"make it one fewer line."
        )

    @pytest.mark.parametrize(("build_error", "is_domain"), _NON_CONFLICT_REJECTIONS)
    async def test_a_non_conflict_rejection_logs_no_exhaustion_record(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        build_error: Callable[[], BaseException],
        is_domain: bool,
    ) -> None:
        """The DISCRIMINATION control: a domain rejection and a transport fault are not
        exhausted contention, and an operator grepping ``store.retry.exhausted`` must not
        find them there. Driven across every live rejection shape, so a build that logs the
        record from a broad ``except`` is caught by whichever row it did not picture.
        """
        _silence_sleep(monkeypatch)
        caplog.set_level(logging.DEBUG, logger=_TXN_LOGGER)
        expected = SurrealStoreError if is_domain else SurrealConnectionError

        with pytest.raises(expected):
            await _store_on(_RejectingConnection(build_error()))._query(
                _MINT_STATEMENT, {"name": _WAVE_NAME}
            )

        assert not _records(caplog, _EXHAUSTION_EVENT), (
            "a non-conflict rejection was logged as exhausted contention — the record is "
            "the driver's, and the driver only ever gives up on the SIGNAL"
        )


# ---------------------------------------------------------------------------
# 7c. WHAT `_ensure_connection` RAISES — and the ruling that settles it.
#     (blindreader F4 — MEDIUM. Behaviour ruling made by the lead.)
#
# BEFORE the wave: a retryable conflict during the bootstrap DDL was a ``SurrealError`` ->
# caught by ``except _CONNECTION_ERRORS`` -> ``_safe_close`` -> **SurrealConnectionError**.
# (Probed: this fired on **6.2%-34.4%** of 16-way virgin first-connects.)
#
# AFTER the wave: it is RETRIED (0% failures — the fix is real and measured), but on
# EXHAUSTION it raises **TxnContentionExhaustedError**, which is a ``RuntimeError`` — not a
# ``SurrealConnectionError``, and not a member of ``_CONNECTION_ERRORS``. Every typed
# handler outside the store modules was written against the OLD type. ``scout.py`` was
# correctly patched; ``server.py:2917`` — the batched finding resolve/acknowledge tool,
# which catches ``SurrealConnectionError`` PER ITEM to degrade gracefully into
# "- {ref} ABORTED — store connection lost; retry these" — was not. A bootstrap exhaustion
# now flies past it as an unhandled exception out of an MCP tool, where the old code
# produced a clean per-item line.
#
# THE RULING (lead): **exhaustion INSIDE the bootstrap surfaces as SurrealConnectionError**
# — the connection never became usable, which is precisely what that type MEANS and what
# every caller of ``_ensure_connection`` has always been told. **Exhaustion of the
# OPERATION itself stays TxnContentionExhaustedError** — the connection is fine; the WRITE
# lost a race, and a caller that must not mistake that for a lost compare-and-set needs the
# type to say so (findings/tasks/briefs all depend on it).
#
# THE INVARIANT, QUANTIFIED (the PR93 law: never condition an invariant on the failure mode
# that prompted the work). It is not "exhaustion is wrapped". It is:
#
#     ∀ ways the bootstrap can fail — transport, domain rejection, parse error, EXHAUSTED
#     CONTENTION — the caller of ``_ensure_connection`` sees SurrealConnectionError, and
#     the cached handle is left None so the next call reconnects.
#
# Each fate is FORCED by its own fixture below. Three of the four are green today; the
# fourth is the defect. A pin written only against the fourth would go green on a build that
# started leaking ``SurrealStoreError`` out of the bootstrap while "sharing the ladder" —
# which is exactly the reconciliation section 7d demands, and exactly how a rewrite loses
# the old world's virtues while every new-world pin stays green.
# ---------------------------------------------------------------------------


@dataclass
class _BootstrapFailingConnection:
    """Every bootstrap step fails with ``error``, forever. ``signin`` succeeds (it is in the
    probed SAFE set — it authenticates a socket and touches no row).
    """

    error: BaseException
    calls: dict[str, int] = field(default_factory=dict)

    def _tick(self, method: str) -> None:
        self.calls[method] = self.calls.get(method, 0) + 1
        if self.calls[method] > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError(f"unbounded retry on the bootstrap's {method}()")

    async def signin(self, credentials: dict[str, Any]) -> None:
        self._tick("signin")

    async def use(self, namespace: str, database: str) -> None:
        self._tick("use")
        raise self.error

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        self._tick("query")
        raise self.error

    async def close(self) -> None:
        self._tick("close")


@dataclass
class _BootstrapCleanThenConflictingConnection:
    """The bootstrap DDL SUCCEEDS; every subsequent statement conflicts forever.

    The contrast fixture for the ruling: same seam, same driver, same engine error — only
    WHERE it happens differs, and that is what decides the type the caller sees. Split on
    the statement (``DEFINE …`` is the bootstrap) rather than the method, because
    ``_query`` and the bootstrap both ride ``connection.query``.
    """

    bootstrap_calls: int = field(default=0, init=False)
    operation_calls: int = field(default=0, init=False)

    async def signin(self, credentials: dict[str, Any]) -> None:
        return None

    async def use(self, namespace: str, database: str) -> None:
        self.bootstrap_calls += 1

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        if statement.upper().lstrip().startswith("DEFINE "):
            self.bootstrap_calls += 1
            return []
        self.operation_calls += 1
        if self.operation_calls > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError("unbounded retry")
        raise _conflict_error()

    async def close(self) -> None:
        return None


@dataclass
class _BootstrapScriptedConnection:
    """The bootstrap fails with ``error`` for its first ``failures`` steps, then succeeds.

    Unlike :class:`_BootstrapFailingConnection` the failure is CALLER-SUPPLIED, so the same
    fake serves the ladder pins — which need a conflict spelled in words the shared marker
    has been MOVED to, and the live words it has been moved AWAY from. ``failures=None``
    fails forever.
    """

    error: BaseException
    failures: int | None
    bootstrap_calls: int = field(default=0, init=False)

    def _tick(self) -> None:
        self.bootstrap_calls += 1
        if self.bootstrap_calls > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError("unbounded retry on the bootstrap")
        if self.failures is None or self.bootstrap_calls <= self.failures:
            raise self.error

    async def signin(self, credentials: dict[str, Any]) -> None:
        return None

    async def use(self, namespace: str, database: str) -> None:
        self._tick()

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        self._tick()
        return []

    async def close(self) -> None:
        return None


# Every way the bootstrap can fail, and whether the driver must have RETRIED it. The
# retryable row is the defect; the other three are the preserved fates that a "share the
# ladder" rewrite could silently change without any new-world pin noticing.
_BOOTSTRAP_FAILURE_FATES = [
    pytest.param(_conflict_error, True, id="EXHAUSTED-CONTENTION-the-defect"),
    pytest.param(
        lambda: NotAllowedError(ErrorKind.NOT_ALLOWED, _LIVE_TRANSPORT_TEXT),
        False,
        id="transport-fault",
    ),
    pytest.param(
        lambda: InternalError(ErrorKind.INTERNAL, _LIVE_ASSERT_TEXT), False, id="domain-rejection"
    ),
    pytest.param(
        lambda: ValidationError(ErrorKind.VALIDATION, _LIVE_PARSE_TEXT), False, id="parse-error"
    ),
]


def _point_at(monkeypatch: pytest.MonkeyPatch, module_path: str, connection: Any) -> Any:
    """Make ``module_path``'s ``AsyncSurreal(url)`` hand back ``connection``, and return a
    freshly-constructed, NEVER-connected seam from that module.
    """
    module = importlib.import_module(module_path)
    monkeypatch.setattr(module, "AsyncSurreal", lambda url: connection)
    return module


class TestTheBootstrapAlwaysSurfacesAsAConnectionFailure:
    """**blindreader F4, and the lead's ruling.** ``_ensure_connection`` has exactly ONE
    failure type, for EVERY reason it can fail. The connection never became usable; that is
    what ``SurrealConnectionError`` means, and it is what every caller — including
    ``server.py``'s per-item graceful-degradation handler — was written against.
    """

    @pytest.mark.parametrize(("build_error", "is_retryable"), _BOOTSTRAP_FAILURE_FATES)
    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_every_bootstrap_failure_raises_SurrealConnectionError(
        self,
        monkeypatch: pytest.MonkeyPatch,
        module_path: str,
        seam: type,
        build_error: Callable[[], BaseException],
        is_retryable: bool,
    ) -> None:
        """RED today x10 on the ``EXHAUSTED-CONTENTION`` row: the bootstrap re-raises the
        typed ``TxnContentionExhaustedError`` out of ``_ensure_connection``, past every
        handler in the tree that catches ``SurrealConnectionError`` to degrade gracefully.

        Green today on the other three rows — and they are not decoration: they are the
        removed-behaviour inventory of the ladder reconciliation in 7d. A build that shares
        one classification ladder and forgets that the BOOTSTRAP's disposition differs from
        ``_query``'s will start raising ``SurrealStoreError`` out of a connect, and only
        these rows will see it.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)  # the floor governs: exhaust in 5 attempts
        connection = _BootstrapFailingConnection(error=build_error())
        _point_at(monkeypatch, module_path, connection)
        instance = _construct(seam)

        with pytest.raises(SurrealConnectionError) as exc_info:
            await instance._ensure_connection()

        assert not isinstance(exc_info.value, TxnContentionExhaustedError), (
            f"{seam.__name__}._ensure_connection ({module_path}) raised the CONTENTION type "
            f"out of a CONNECT. Every caller of a connect — server.py:2917's per-item "
            f"'ABORTED — store connection lost; retry these' among them — catches "
            f"SurrealConnectionError. The connection never became usable: that is what the "
            f"type says, and it is the fact the caller needs."
        )
        assert instance._connection is None, (
            "a failed bootstrap left a cached handle behind — the next call would reuse a "
            "connection that never finished being set up"
        )
        assert connection.calls.get("close", 0) >= 1, (
            "a failed bootstrap did not close its socket — it leaks one per failed connect"
        )
        attempts = connection.calls.get("query", 0) + connection.calls.get("use", 0)
        if is_retryable:
            assert attempts >= _MAX_TXN_CONFLICT_ATTEMPTS, (
                f"the bootstrap made {attempts} attempt(s) against a RETRYABLE conflict. It "
                f"is inside the driver and it is not retrying — routing without "
                f"classify-and-signal retries zero times, and a green gate over a dead "
                f"mechanism is finding #102 exactly. (Probed: an unretried bootstrap loses "
                f"{_UNRETRIED_BOOTSTRAP_LOSS} of concurrent virgin first-connects — "
                f"{_UNRETRIED_BOOTSTRAP_PROTOCOL}.)"
            )
        else:
            assert attempts == 1, (
                f"the bootstrap retried a non-conflict failure {attempts - 1} time(s). A "
                f"transport fault may already have COMMITTED (the at-most-once rule) and a "
                f"domain rejection can never succeed — only the SIGNAL is ever retried."
            )

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_the_OPERATIONS_exhaustion_still_raises_the_CONTENTION_type(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        """**THE CONTRAST, and it is the other half of the ruling.** Same seam, same driver,
        same engine error — the bootstrap succeeds and the OPERATION exhausts. Here the
        connection is perfectly healthy and the WRITE lost a race, so the caller MUST see
        ``TxnContentionExhaustedError``: findings, tasks and (after 7a) briefs all branch on
        that type to avoid reporting exhausted contention as a lost compare-and-set.

        Green today. It is here because a build that "fixes" F4 by wrapping ALL exhaustion
        into ``SurrealConnectionError`` passes every pin above and destroys every
        guarded-CAS handler in the package — silently, since a lost CAS and a dead socket
        both just propagate.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _BootstrapCleanThenConflictingConnection()
        _point_at(monkeypatch, module_path, connection)
        instance = _construct(seam)

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await instance._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        assert connection.bootstrap_calls >= 1, "the fixture never bootstrapped — nothing is proven"
        assert exc_info.value.attempts == connection.operation_calls == _MAX_TXN_CONFLICT_ATTEMPTS
        assert instance._connection is connection, (
            "an exhausted OPERATION tore down a healthy connection — only a transport fault "
            "self-heals"
        )


# ===========================================================================
# 7d. ONE IMPLEMENTATION — the half of the DRY consolidation it did not do.
#     (blindreader F3 — HIGH, a design finding.)
#
# The retry MECHANICS are genuinely shared now, and that half is real (probed: 16-way
# concurrent virgin first-connect went 6.2%-34.4% -> 0% failures). But measured on the wave's own
# tree:
#
#     | shape                                                      | copies |
#     | `_define_namespace` + `_select_namespace_database`
#       + `_define_database` bootstrap closures                    | 10 x 3 = 30 |
#     | the `async def _attempt()` `_query` body (byte-identical
#       but for one log-event string)                              |     10 |
#
# The retry POLICY is shared. The BOOTSTRAP SHAPE and the CLASSIFICATION-AND-SIGNAL POLICY
# are copy #1 … copy #10, hand-written, in ten files — and this wave's OWN new standing law
# is the indictment:
#
#     "If two call sites need the same POLICY, it is a FUNCTION THEY CALL — never a pattern
#      they clone. Policy = retry budgets, backoff/jitter, ERROR CLASSIFICATION, …"
#     "ROUTING IS NOT SHARING. A caller that calls the shared driver but hand-rolls the
#      DECISION underneath it is a private copy wearing the shared name."
#
# And the two cloned shapes ALREADY DISAGREE WITH EACH OTHER, in the same file:
#
#   * the three bootstrap closures classify with ``is_retryable_conflict_error()`` ONLY —
#     they never consult ``is_connection_error()``;
#   * ``_query``'s ``_attempt`` consults ``is_connection_error()`` FIRST, and only then
#     ``is_retryable_conflict_error()``.
#
# Two different ladders for the same exception set, each hand-written ten times. Apply this
# wave's own mutation test — change the shared decision and every caller must move — and a
# change to the bootstrap's classification moves 1 site in 20.
#
# ---------------------------------------------------------------------------
# THE RECONCILIATION, stated because the two ladders must become one and a contract that
# left this to the builder would be handing it a fork to choose silently:
#
#   ORDER — transport FIRST, then conflict, then domain. ``_query``'s ladder is the correct
#   one and the bootstrap adopts it. The order is load-bearing, not stylistic: a fault that
#   is BOTH transport-class and conflict-worded must never be retried, because a transport
#   fault may already have COMMITTED (the driver's at-most-once rule). Conflict-first would
#   retry it.
#
#   DISPOSITION — the two callers do NOT dispose of the three outcomes identically, and
#   that is not a second ladder; it is the same ladder read by callers with different
#   contracts:
#       bootstrap:  conflict -> signal (retry) · transport -> SurrealConnectionError ·
#                   domain   -> SurrealConnectionError   (the connection never became usable)
#       _query:     conflict -> signal (retry) · transport -> SurrealConnectionError + drop
#                                                            the cached handle ·
#                   domain   -> SurrealStoreError        (the connection is healthy; the
#                                                         WRITE was rejected)
#   Section 7c's ∀-fates table is the witness for the bootstrap column, and
#   ``TestEverySingleStatementSeamRetriesAConflict`` for the ``_query`` column. Sharing the
#   CLASSIFIER must not collapse the DISPOSITIONS — that is a distinct removed-behaviour
#   hazard, and it is pinned in both places rather than trusted.
#
# THE CONTRACT (blindreader's fix shape, adopted):
#
#     # loremaster/loremaster/store/_txn.py
#     async def bootstrap_session(connection, namespace, database) -> None: ...
#     async def run_query(
#         *, acquire, drop, url, noun, label, statement, params
#     ) -> Any: ...
#
# ⚠ ``noun`` IS NOT DECORATION, AND THIS SKETCH ONCE OMITTED IT (audit-fix-1 A2). The ten
# seams do not share one raised-message wording: five say plain "query", the other five say
# "brief query" / "agent query" / "task query" / "finding query" / "memory query" — an
# OPERATOR-FACING surface, preserved from HEAD. A builder tidying its code to match a sketch
# that omitted the parameter would silently regress five seams' messages and pass 385/385 +
# the full suite + mypy + ruff. **A removed behaviour preserved without an invariant is half
# a fix**, so the sketch names it and ``TestTheSeamsRejectionLogSurvivesTheCollapse`` pins it
# as an exact MAPPING (§8e).
#
# Called once per ``_ensure_connection`` and once per ``_query``. Collapses 30 + 10 into 2.
# The exact SIGNATURES are the builder's (these pins never assert one) — what the pins
# assert is that there is exactly ONE of each, that every seam HOLDS it by IDENTITY (a copy
# is a different object, and identity is the only thing a copy cannot fake), that every
# seam CALLS it (a module can import a name and hand-roll a loop anyway), and that no
# module-local bootstrap survives to be cloned an eleventh time.
# ===========================================================================

# Conflicts the ladder pins feed the bootstrap before letting it through. Below the shared
# attempt FLOOR, so a correct bootstrap always survives them; above zero, so a bootstrap that
# cannot see the moved marker always dies on the first one.
_BOOTSTRAP_MOVED_FAILURES = 3

_MISSING_SHARED_HELPER = (
    "loremaster.store._txn.{name} does not exist. The bootstrap and the single-statement "
    "attempt body are POLICY — error classification, signal-raising, the DDL shape — and "
    "policy is a FUNCTION CALLERS CALL, never a pattern they clone. Thirty closures and ten "
    "attempt bodies is finding #108 one altitude up: the thing DESIGN-LAW.md:75 invited a "
    "clone of was the seam itself."
)


def _shared(name: str) -> Any:
    helper = getattr(txn_module, name, None)
    assert helper is not None, _MISSING_SHARED_HELPER.format(name=name)
    return helper


def _discover_bootstrap_owners() -> list[tuple[str, str]]:
    """Every class in the package owning an ``async def _ensure_connection``.

    The ALL set, discovered — not the offenders set, and not a hand-list. The v5 coverage
    pin's whole failure was enumerating from the OFFENDERS (empty by construction on any
    lint-clean build), so it could not fire on any build the lint passed. An eleventh ledger
    that hand-rolls its own bootstrap is pinned the day it is written, by nobody's memory.
    """
    owners: list[tuple[str, str]] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        module_path = (
            f"loremaster.{path.relative_to(_PACKAGE_ROOT).with_suffix('').as_posix()}".replace(
                "/", "."
            )
        )
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ClassDef) and any(
                isinstance(item, ast.AsyncFunctionDef) and item.name == "_ensure_connection"
                for item in node.body
            ):
                owners.append((module_path, node.name))
    return owners


_BOOTSTRAP_OWNERS = [
    pytest.param(module_path, class_name, id=class_name)
    for module_path, class_name in _discover_bootstrap_owners()
]

# The store seams are ten; scout owns an ``_ensure_connection`` too (it delegates to the
# module-level ``_open_command_connection``, which carries the ELEVENTH copy of the same
# three closures — the copy no `_query`-keyed enumeration can see, exactly as scout was the
# copy no `_query`-keyed enumeration could see the first time).
_MIN_KNOWN_BOOTSTRAP_OWNERS = 11

# The bootstrap DDL, in the engine's OWN words — not ours. These are SurrealQL keywords, so
# unlike a symbol name they cannot be renamed out from under the scan.
_BOOTSTRAP_DDL_KEYWORDS = ("DEFINE NAMESPACE", "DEFINE DATABASE")
# The SDK call that SELECTS the namespace+database on a live socket. It is the third leg of
# every bootstrap, it is the call the probe measured LOSING the race (6.2%-34.4% of virgin
# first-connects), and it appears nowhere else in this package.
_SESSION_SELECT_METHOD = "use"


def _bootstrap_sites_in(source: str) -> list[tuple[int, str]]:
    """Every SESSION-BOOTSTRAP site in ``source`` — ``(lineno, what)``.

    Two shapes, and they are the property, not a name: a ``connection.use(...)`` call
    (selecting the namespace+database on a live socket), and a statement literal carrying
    the engine's own ``DEFINE NAMESPACE`` / ``DEFINE DATABASE``. f-string parts are walked
    too — every bootstrap in this tree interpolates the namespace, so a scan that only read
    ``ast.Constant`` would find NONE of them and go vacuously green.
    """
    tree = ast.parse(source)
    sites: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == _SESSION_SELECT_METHOD
            and _is_connection_receiver(node.func.value)
        ):
            sites.append((node.lineno, f"connection.{_SESSION_SELECT_METHOD}()"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            upper = node.value.upper()
            for keyword in _BOOTSTRAP_DDL_KEYWORDS:
                if keyword in upper:
                    sites.append((node.lineno, keyword))
    return sites


class TestTheSessionBootstrapLivesInExactlyOnePlace:
    """**blindreader F3, structurally.** Thirty closures become one function, and the AST is
    what says so — a behavioural spy proves the shared helper is CALLED, but it cannot see a
    private bootstrap that still runs beside it.

    Enumerated from the ALL set (every production module), never from the offenders: the
    offenders set is empty by construction on any build that already passes, which is the
    precise way the v5 coverage pin certified nothing while promising everything.
    """

    def test_the_owner_scan_is_not_silently_finding_nothing(self) -> None:
        """The control on the instrument. A parametrised suite over an empty list is
        vacuously, silently green — the signature failure of every mechanical gate.
        """
        owners = _discover_bootstrap_owners()

        assert len(owners) >= _MIN_KNOWN_BOOTSTRAP_OWNERS, (
            f"the scan found only {len(owners)} classes owning an `async def "
            f"_ensure_connection` ({[name for _, name in owners]}) — this contract was "
            f"written against {_MIN_KNOWN_BOOTSTRAP_OWNERS}. Either the connection owners "
            f"were consolidated (good — lower this floor deliberately, in a diff a reviewer "
            f"can see) or the SCANNER broke and every pin below just went vacuously green."
        )

    def test_no_production_module_outside_the_seam_bootstraps_a_session(self) -> None:
        """RED today: 30 closures across ten modules, plus scout's eleventh copy.

        Every residual site is named with ``file:line`` — this repo's own law bans "all
        remaining hits are X" as an output, because wholesale classification under volume is
        how a found defect gets re-buried.
        """
        held: dict[str, list[tuple[int, str]]] = {}
        for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            key = path.relative_to(_PACKAGE_ROOT).as_posix()
            if key == _SEAM_MODULE:
                continue
            sites = _bootstrap_sites_in(path.read_text(encoding="utf-8"))
            if sites:
                held[key] = sites

        assert not held, (
            f"the session bootstrap is hand-rolled outside {_SEAM_MODULE}:\n  "
            + "\n  ".join(
                f"{key}:{lineno}  {what}" for key, sites in held.items() for lineno, what in sites
            )
            + "\n\nThirty closures and eleven copies. It is ONE function — "
            "`_txn.bootstrap_session` — and every `_ensure_connection` CALLS it. A pattern "
            "to clone is a defect to clone: DESIGN-LAW.md invited a clone of the mint and "
            "got findings #102 AND #108; the thing that got cloned underneath BOTH of them "
            "was this."
        )

    def test_the_scan_SEES_a_hand_rolled_bootstrap_it_is_shown(self) -> None:
        """**POSITIVE CONTROL.** A scan that has never been shown firing is not a scan — and
        this one has a specific way to go blind: every bootstrap in this tree interpolates
        the namespace into an f-string, so a scan reading only ``ast.Constant`` values finds
        ZERO sites and reports a clean tree forever.
        """
        source = """
class Ledger:
    async def _ensure_connection(self):
        connection = AsyncSurreal(self._url)
        await connection.signin(credentials)

        async def _define_namespace():
            await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {self._namespace}")

        async def _select_namespace_database():
            await connection.use(self._namespace, self._database)

        await retry_on_conflict(_define_namespace)
        await retry_on_conflict(_select_namespace_database)
"""
        found = _bootstrap_sites_in(source)

        assert [what for _, what in found] == ["connection.use()", "DEFINE NAMESPACE"], (
            f"the scan saw {found} in a textbook hand-rolled bootstrap. It must see BOTH "
            f"shapes — the f-string DDL and the use() call — or the ten it is hunting are "
            f"invisible to it."
        )

    def test_the_scan_SPARES_a_module_that_merely_talks_to_the_engine(self) -> None:
        """**NEGATIVE CONTROL.** A gate that fires on correct, unrelated code gets deleted by
        the first engineer it blocks, and then we have nothing. An ordinary seam that runs
        statements through the driver bootstraps nothing and is not this pin's business —
        and neither is a DEFINE the SCHEMA legitimately emits (``DEFINE TABLE`` /
        ``DEFINE FIELD`` / ``DEFINE INDEX`` live in ``surreal_schema.py`` by design).
        """
        source = """
class Ledger:
    async def _query(self, statement, params=None):
        return await run_query(
            acquire=self._ensure_connection, drop=self._drop_connection, url=self._url,
            label="brief.query.rejected", statement=statement, params=params or {},
        )

def generate_brief_ddl():
    return "DEFINE TABLE IF NOT EXISTS brief SCHEMAFULL; DEFINE FIELD OVERWRITE body ON brief;"
"""
        assert not _bootstrap_sites_in(source), (
            "the scan flagged a module that bootstraps nothing — it is keyed on the SESSION "
            "bootstrap (namespace/database/use), not on the word DEFINE"
        )


# ===========================================================================
# THE SAME GATE, OVER THE TEST TREE — closing the CLASS, not the instance (#150)
#
# The pin above scans ``_PACKAGE_ROOT``: production modules only. That is not an
# implementation detail, it is the whole reason finding #150 existed. The harness's
# session bootstrap was three BARE, UNRETRIED ``await``\s in ``tests/_surreal_harness.py``,
# and it rode out the entire #102/#108 consolidation wave untouched — not because anyone
# waved it through, but because a sweep whose root is the package cannot see a seam that
# lives in the test tree. Ten hand-rolled copies were found and deleted; the ELEVENTH was
# structurally invisible to the instrument that found the ten.
#
# Fixing #150 removed the INSTANCE. This removes the BLINDNESS. Without it, the next test
# helper that hand-rolls a bootstrap is exactly as invisible as the last one was.
#
# ---------------------------------------------------------------------------
# THREAT MODEL — WHO THIS GATE IS FOR. Stated in the instrument, because a gate whose
# audience is unwritten gets re-argued from scratch by every auditor who meets it, and
# each of them is entitled to their own verdict.
#
#   IT IS FOR THE HONEST ENGINEER who writes a test helper that opens a socket and
#   hand-rolls ``DEFINE NAMESPACE`` / ``DEFINE DATABASE`` / ``use()`` because they did
#   not know ``_txn.bootstrap_session`` existed. That is #150 verbatim, written by an
#   author doing their best with the seam one directory away and no sign pointing at it.
#
#   IT IS NOT A SECURITY BOUNDARY against an author trying to get past it. Anyone who
#   can commit here can already bootstrap a session in a way no AST scan will name — via
#   a helper, a getattr, a receiver spelled something else entirely. Saying so is not a
#   weakness admitted; it is this pin's SPEC.
#
#   So the verdicts follow mechanically, and no future auditor has to guess:
#     * "a determined author could evade this"      -> NOT a defect. Out of model.
#     * "an honest engineer's hand-rolled bootstrap
#        in a test helper goes unnoticed"           -> A DEFECT. The only one this
#                                                      pin answers to.
#
#   And the reason that trade is the correct one, which is the half worth remembering:
#   A GATE THAT REFUSES HONEST CODE IS A GATE THAT GETS SWITCHED OFF, and then the next
#   #150 ships with nothing watching at all. This tree is FULL of legitimate fakes that
#   define ``async def use(...)`` and fixtures that hold ``DEFINE NAMESPACE`` as a plain
#   string, and not one of them may ever cost an engineer a red suite.
#
# ---------------------------------------------------------------------------
# WHY THE TEST-TREE SCAN IS NARROWER THAN PRODUCTION'S — same property, different
# population. In ``loremaster/``, a ``DEFINE NAMESPACE`` literal is necessarily a
# bootstrap: production has no reason to hold that string as DATA. In ``tests/`` the same
# literal is OVERWHELMINGLY data — expected-value constants, source fixtures fed to the
# scanners above, prose inside pin messages. Run production's literal-keyed scan over this
# tree verbatim and nearly every hit is correct code. That gate lasts one afternoon.
#
# ⚠ NO NUMERALS IN THIS BLOCK, AND THAT IS THE POINT. It used to say "23 sites, 22 of
# them correct code". That was MEASURED, HONEST, AND TRUE WHEN WRITTEN — and the very
# commit that wrote it added new `DEFINE NAMESPACE` fixtures to this file and falsified it
# in the same diff (a cold audit measured 31 at that commit, 23 at its parent). A
# self-invalidating measurement, in served English, with nothing able to catch it: this
# repo's single most-named defect class, shipped inside the wave that was fixing that
# class. So the quantitative claim is not RESTATED here — it is DERIVED at assert time by
# `test_the_literal_keyed_scan_would_be_MOSTLY_FALSE_POSITIVES_here`, which re-measures
# both populations on every run and can never drift from the tree.
#
# The property that survives the move is EXECUTION: a bootstrap is not a string, it is
# three operations RUN ON A LIVE CONNECTION. So the test-tree scan keys on the CALL — a
# `use()` on a connection-named receiver, or ANY call carrying the engine's own DDL
# keywords in its arguments, on ANY receiver. The DDL leg is receiver-blind and
# method-blind by ruling (#150 audit R1): keyed on the receiver NAME it was measured
# missing most natural handle names, `db` among them — i.e. the literal #150 construct
# ships green — which made this tree strictly WEAKER than the production gate on the one
# population that has actually failed. The names are enumerated ONCE, in the parameter
# list of `test_the_DDL_leg_is_RECEIVER_BLIND_whatever_the_handle_is_called`, where they
# execute; and the cost of the blindness is DERIVED by
# `test_the_receiver_blind_DDL_leg_costs_this_tree_NOTHING` rather than claimed here.
#
# This is a NARROWING OF THE SAME PREDICATE, not a second implementation: both legs read
# `_SESSION_SELECT_METHOD` and `_BOOTSTRAP_DDL_KEYWORDS`, and both `use()` legs read
# `_is_connection_receiver` — the production gate's own constants. Mutate any one of the
# three and BOTH scans go blind together, which is the only proof of sharing that a
# private copy wearing a shared name cannot fake. That mutation is not an argument here;
# ALL THREE are executed, below — the claim used to name three constants and execute one.

# THE SAFE SET, ENUMERATED — and it is one file.
#
# This is an ALLOWLIST, and deliberately so. Six instruments in this repo have now been
# defeated by keying on what is FORBIDDEN (a label's literal, beaten by a substring of it;
# ``async def _query``, beaten by a module that spelled it differently; three SDK method
# names, beaten by the other thirty). The forbidden set is unbounded and the next entry in
# it is by definition the one nobody thought of. The SAFE set here is one row long, and a
# reviewer can read it in full.
#
# Every allowance carries its REASON and its expected SITE COUNT. The count is the half
# that matters: a bare file-level exemption would make ``_surreal_harness.py`` — the file
# #150 actually lived in — a permanent blind spot, which is the failure this whole section
# exists to end. A new bootstrap operation appearing in an allowlisted file goes RED and
# has to be justified in a diff a reviewer can see.
_TEST_TREE_BOOTSTRAP_ALLOWANCES: dict[str, tuple[int, str]] = {
    "_surreal_harness.py": (
        1,
        "`drop_database` selects the namespace+database for teardown and runs that select "
        "UNDER the store's retry seam, on a deadline composed with the drop's (#150 R4). "
        "`open_connection` holds no site at all — it hands the whole three-statement "
        "bootstrap to `_txn.bootstrap_session`, which is exactly why it is invisible to "
        "this scan. Both halves are the #150 fix; this row is the standing receipt that "
        "they stayed fixed.",
    ),
}

# The scan must actually reach the tree it claims to scan. REACH IS A CHECKED VARIABLE,
# never an assumption: this repo has already shipped a gate that certified nothing because
# it enumerated from a set that was empty by construction, and a scan that silently visits
# zero files passes forever while promising everything. 92 modules today.
_MIN_SCANNED_TEST_MODULES = 60


def _executed_bootstrap_sites_in(source: str) -> list[tuple[int, str]]:
    """Every session-bootstrap operation ``source`` RUNS ON A LIVE CONNECTION.

    Two legs, both keyed on the CALL rather than on a string, because in this tree the
    string is usually data — and they are keyed DIFFERENTLY on purpose:

      * **The DDL leg — RECEIVER-BLIND.** ``<anything>.<anything>(... "DEFINE NAMESPACE"
        ...)``: the engine's own session DDL reaching *any* method on *any* receiver as an
        argument. It does NOT ask what the receiver is called. f-string parts are walked,
        so the near-universal ``f"DEFINE NAMESPACE IF NOT EXISTS {ns}"`` is seen; a scan
        reading only bare ``ast.Constant`` values would find none of them and go silently
        green.
      * **The ``use()`` leg — receiver-keyed**, via :func:`_is_connection_receiver`. Here
        the method name carries no evidence at all (``use`` is a generic English verb, and
        an unqualified deny on it would fire on any unrelated helper), so the receiver is
        the only signal available. Its blindness is a KNOWN BOUND, now ASSERTED — with its
        rationale and its re-open trigger — by :meth:`TestTheTestTreeRoutesThroughTheOne
        BootstrapToo.test_the_use_leg_MISSES_a_DDL_LESS_bootstrap_on_an_oddly_named_handle`,
        so it goes RED the day someone closes it rather than being silently inherited or
        silently "fixed" — and it is covered on the population that matters,
        because a hand-rolled bootstrap that runs ``use()`` runs the DDL too, and the DDL
        leg sees that with no opinion about naming.

    **WHY THE DDL LEG IS BLIND, since it was not always** (#150 audit R1): keyed on the
    receiver NAME, this scan MEASURED the majority of natural handle names walking
    straight past it — the exact set is the parameter list of
    :meth:`TestTheTestTreeRoutesThroughTheOneBootstrapToo
    .test_the_DDL_leg_is_RECEIVER_BLIND_whatever_the_handle_is_called`, stated once, there,
    where it executes. The literal #150 construct with the handle called ``db`` was green,
    which is the one that settled it. That is the sixth time
    an instrument in this repo keyed on a name as a proxy for a property and lost; the
    settled reframe is *receiver-blind deny, and allowlist the safe* — which is exactly the
    shape here, with :data:`_TEST_TREE_BOOTSTRAP_ALLOWANCES` as the one-row safe set.

    **It is method-blind as well as receiver-blind, and that is deliberate.** Keying the
    deny on ``{query, execute}`` would have re-opened the same hole one column over: the
    installed SDK ships ``query_raw`` beside ``query``, so a method-name enumeration is
    already defeated on the day it lands. The MEASURED cost of blindness on both axes is
    zero — over every module in this tree, receiver-blind-and-method-blind finds exactly
    the same single site the receiver-keyed version did, because this tree's bootstrap DDL
    literals are bare strings and scanner fixtures, never call ARGUMENTS. That measurement
    is not restated as a numeral anywhere; it is re-derived at assert time by
    :meth:`TestTheTestTreeRoutesThroughTheOneBootstrapToo
    .test_the_receiver_blind_DDL_leg_costs_this_tree_NOTHING`.

    A fake that DEFINES ``async def use`` is not a bootstrap and is not matched here — a
    ``FunctionDef`` is not a ``Call``. That distinction is the difference between this gate
    and a gate that gets deleted; it is pinned as a control, not left to this docstring.
    """
    sites: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr == _SESSION_SELECT_METHOD and _is_connection_receiver(node.func.value):
            sites.append((node.lineno, f"connection.{_SESSION_SELECT_METHOD}()"))
            continue
        for argument in ast.walk(node):
            if not (isinstance(argument, ast.Constant) and isinstance(argument.value, str)):
                continue
            upper = argument.value.upper()
            for keyword in _BOOTSTRAP_DDL_KEYWORDS:
                if keyword in upper:
                    sites.append((node.lineno, f".{node.func.attr}({keyword} ...)"))
    return sites


@functools.cache
def _scanned_test_tree() -> tuple[tuple[str, tuple[tuple[int, str], ...]], ...]:
    """Every test module and its bootstrap sites, parsed ONCE per session.

    Parsing 92 modules costs ~400ms and three pins below need the same answer; without
    this the extension put ~2s on a 14s run for nothing. Cached as tuples so the shared
    result cannot be mutated by one caller under another — the callers get fresh
    containers from :func:`_test_tree_bootstrap_sites`.
    """
    return tuple(
        (
            path.relative_to(_TESTS_ROOT).as_posix(),
            tuple(_executed_bootstrap_sites_in(path.read_text(encoding="utf-8"))),
        )
        for path in sorted(_TESTS_ROOT.rglob("*.py"))
        if "__pycache__" not in path.parts
    )


def _test_tree_bootstrap_sites() -> tuple[dict[str, list[tuple[int, str]]], list[str]]:
    """``(sites by test-tree-relative path, every module actually scanned)``.

    The scanned list is returned rather than discarded so REACH can be asserted by the
    pins below instead of assumed by their author.
    """
    scanned = _scanned_test_tree()
    held = {key: list(sites) for key, sites in scanned if sites}
    return held, [key for key, _ in scanned]


class TestTheTestTreeRoutesThroughTheOneBootstrapToo:
    """**Finding #150's blindness, closed.** The production pin above cannot see this tree;
    a hand-rolled bootstrap lived here through an entire consolidation wave because of it.

    Read the threat model in the block above before grading this class: it is built for the
    honest engineer who did not know the seam existed, and it is explicitly NOT a boundary
    against an author working around it.
    """

    def test_the_test_tree_scan_actually_reaches_the_test_tree(self) -> None:
        """**THE REACH CONTROL.** A scan that visits nothing is green forever, and this repo
        has shipped exactly that instrument before. Reach is checked, never assumed.
        """
        _, scanned = _test_tree_bootstrap_sites()

        assert len(scanned) >= _MIN_SCANNED_TEST_MODULES, (
            f"the test-tree scan visited only {len(scanned)} modules — this pin was written "
            f"against 92, and its floor is {_MIN_SCANNED_TEST_MODULES}. Either the suite "
            f"shrank dramatically (lower this floor deliberately, in a diff a reviewer can "
            f"see) or the WALK broke and every pin in this class just went vacuously green."
        )
        assert "_surreal_harness.py" in scanned, (
            "the scan did not visit `_surreal_harness.py` — the file finding #150 actually "
            "lived in. A reach that excludes the one known offender is not reach."
        )
        assert "test_retry_seam.py" in scanned, (
            "the scan did not visit its own file. This module holds more `DEFINE NAMESPACE` "
            "string fixtures than any other in the tree, so it is also the strongest "
            "evidence that the scan tells DATA from EXECUTION — skipping it would hide "
            "exactly the false positives this design exists to avoid."
        )

    def test_no_test_module_outside_the_allowlist_bootstraps_a_session(self) -> None:
        """THE GATE. Every site outside the enumerated safe set, named ``file:line`` —
        because "all remaining hits are fixtures" is banned output in this repo, and
        wholesale classification under volume is how a real defect gets re-buried.
        """
        held, _ = _test_tree_bootstrap_sites()
        violations = {key: sites for key, sites in held.items() if key not in _TEST_TREE_BOOTSTRAP_ALLOWANCES}

        assert not violations, (
            "a test-tree module hand-rolls a SurrealDB session bootstrap:\n  "
            + "\n  ".join(
                f"{key}:{lineno}  {what}" for key, sites in violations.items() for lineno, what in sites
            )
            + "\n\nIt is ONE function — `loremaster.store._txn.bootstrap_session` — and the "
            "test harness calls it like every production `_ensure_connection` does; see "
            "`_surreal_harness.open_connection`. THIS IS FINDING #150: the harness carried "
            "three bare, unretried bootstrap `await`s that no gate could see, because the "
            "gate above this one scans production only. Live-probed, 16-way concurrent, "
            "6.2%-34.4% of virgin first-connects LOSE that race — under the standing "
            "`-n auto` runner that is a stochastic setup failure across the whole suite.\n"
            "If your site is legitimate (it routes through the seam), add it to "
            "`_TEST_TREE_BOOTSTRAP_ALLOWANCES` with its reason — an allowance is a diff a "
            "reviewer can see, which is the point."
        )

    def test_every_allowance_still_holds_exactly_the_sites_it_was_granted(self) -> None:
        """An allowance is bounded by COUNT, so an allowlisted file cannot become a blind
        spot. ``_surreal_harness.py`` is the file #150 lived in; exempting it wholesale
        would re-open the exact hole this class closes, one level down.
        """
        held, _ = _test_tree_bootstrap_sites()

        for key, (expected, reason) in _TEST_TREE_BOOTSTRAP_ALLOWANCES.items():
            found = held.get(key, [])
            assert len(found) == expected, (
                f"`{key}` is allowed {expected} bootstrap site(s), and the scan found "
                f"{len(found)}: {found}. The allowance reads:\n  {reason}\n"
                f"If you ADDED a site, it is not covered by that reason — route it through "
                f"`_txn.bootstrap_session` (or the store retry seam) and raise the count "
                f"here with a reason of its own. If you REMOVED one, lower the count: an "
                f"allowance for a site that no longer exists is a standing exemption nobody "
                f"is checking."
            )

    def test_the_scan_SEES_the_hand_rolled_bootstrap_of_finding_150(self) -> None:
        """**POSITIVE CONTROL, and it is #150's own construct.** A scan never shown firing
        is not a scan. This is the shape the harness actually held: bare awaits, the DDL
        interpolated into f-strings, the select on a live socket.
        """
        source = """
async def open_connection(env):
    connection = AsyncSurreal(env.url)
    await connection.signin({"username": env.user, "password": env.password})
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {env.namespace}")
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {env.database}")
    await connection.use(env.namespace, env.database)
    return connection
"""
        found = _executed_bootstrap_sites_in(source)

        assert [what for _, what in found] == [
            ".query(DEFINE NAMESPACE ...)",
            ".query(DEFINE DATABASE ...)",
            "connection.use()",
        ], (
            f"the scan saw {found} in finding #150's verbatim construct. It must see all "
            f"three legs — both f-string DDL statements and the select — or the next helper "
            f"to hand-roll a bootstrap is as invisible as the last one was."
        )

    @pytest.mark.parametrize(
        "receiver",
        [
            # the four the OLD receiver-keyed predicate already caught — the control leg,
            # so a build that merely broke the scan cannot pass this by failing everything
            "connection", "conn", "self._connection", "_connection",
            # and the seven MEASURED sailing straight past it
            "db", "client", "surreal", "sdb", "session", "handle", "store",
        ],
    )
    def test_the_DDL_leg_is_RECEIVER_BLIND_whatever_the_handle_is_called(self, receiver: str) -> None:
        """**THE R1 FIX, AND ITS DISCRIMINATION.** An engineer who calls a SurrealDB handle
        ``db`` is not evading a gate — they are naming a variable. The previous predicate
        keyed on the receiver's NAME, and every name in the second group below was MEASURED
        walking past it — `db` among them, which is finding #150's own construct passing
        green in the file class this gate was built for. **The list is the measurement**;
        no ratio is restated in prose, because a ratio beside a list is one edit away from
        contradicting it (#150 audit R2 is that exact defect).

        Every name here must be CAUGHT, and the first four are the control: they were
        caught before the fix too, so a build that simply broke the scan cannot pass this
        by failing everything. (``_connection`` is R1b — an ``ast.Name`` that the old
        asymmetric predicate missed while catching the identical ``self._connection``.)
        """
        source = f'''
async def open_connection(env):
    {receiver} = AsyncSurreal(env.url)
    await {receiver}.signin({{"username": env.user}})
    await {receiver}.query(f"DEFINE NAMESPACE IF NOT EXISTS {{env.namespace}}")
    await {receiver}.query(f"DEFINE DATABASE IF NOT EXISTS {{env.database}}")
    return {receiver}
'''
        found = _executed_bootstrap_sites_in(source)

        assert [what for _, what in found] == [
            ".query(DEFINE NAMESPACE ...)",
            ".query(DEFINE DATABASE ...)",
        ], (
            f"a hand-rolled bootstrap whose connection is called `{receiver}` was seen as "
            f"{found}. The DDL leg must not care what the handle is named: keying it on the "
            f"receiver name is the sixth instrument in this repo defeated by enumerating a "
            f"NAME as a proxy for a PROPERTY, and it left this tree strictly weaker than the "
            f"production gate on the one population that has actually failed (#150 audit R1)."
        )

    def test_the_use_leg_still_reads_the_shared_receiver_predicate(self) -> None:
        """The other half of R1b, and the reason :func:`_is_connection_receiver` still
        exists: ``use`` is a generic English verb, so the ``use()`` leg cannot deny
        receiver-blind without firing on unrelated helpers. It therefore keeps the
        predicate — and the predicate must now treat ``_connection`` (an ``ast.Name``) and
        ``self._connection`` (an ``ast.Attribute``) IDENTICALLY, which it did not before.
        """
        for receiver in ("connection", "conn", "_connection", "self._connection", "self._db_connection"):
            assert _executed_bootstrap_sites_in(f"await {receiver}.use(ns, db)\n"), (
                f"the use() leg missed `{receiver}.use(ns, db)`. `self._connection` was "
                f"caught by a suffix test while a plain local `_connection` was tested "
                f"against a two-item frozenset and missed — an idiomatic private-local name "
                f"evading the scan its own attribute spelling could not (#150 audit R1b)."
            )
        assert not _executed_bootstrap_sites_in("await monkeypatch.use(thing)\n"), (
            "the use() leg fired on an unrelated receiver. It is receiver-KEYED precisely "
            "because `use` is too generic to deny on; if this ever goes blind the fix is "
            "not to widen it but to lean on the receiver-blind DDL leg, which sees any "
            "real bootstrap anyway."
        )

    def test_the_use_leg_MISSES_a_DDL_LESS_bootstrap_on_an_oddly_named_handle(self) -> None:
        """**PINNING A HOLE WE DID NOT CLOSE** (CLAUDE.md: "when you cannot close a hole,
        PIN IT"). This asserts the bound EXISTS, so the next engineer meets it deliberately
        instead of rediscovering it from an outage — or "helpfully" closing it and re-opening
        the noise problem that closing it costs.

        **THE BOUND:** a bootstrap that runs ONLY ``use()``, on a handle whose name the
        receiver predicate does not recognise, and that runs NO DDL, is NOT seen by this
        scan.

        **WHY IT IS NOT CLOSED, and it is a trade rather than an oversight:** ``use`` is a
        generic English verb. A receiver-blind deny on ``.use(...)`` — the shape the DDL leg
        rightly took — would fire on ``monkeypatch.use()``, ``fixture.use()`` and any
        unrelated helper that happens to spell a method that way. That is the false-positive
        class that gets an instrument SWITCHED OFF, and then the next #150 ships with nothing
        watching at all. The DDL leg can afford blindness because ``DEFINE NAMESPACE`` is the
        engine's own vocabulary and means one thing; ``use`` is not, and does not. Blinding
        this leg was MEASURED at zero sites in this tree at the time, and that was declined as
        grounds to ship: zero-today on a token that generic is luck, not a property.

        **WHY THE EXPOSURE IS NARROW:** a hand-rolled bootstrap does not select a session it
        never defined — it runs the DDL too, and the receiver-blind DDL leg sees that with no
        opinion about naming (the control below proves it on this very handle). So the
        *bootstrap* population is still covered; what escapes is a select with no DDL beside
        it.

        **RE-OPEN TRIGGER: the day a reconnect path selects a session without re-running the
        DDL** — a resume/reconnect that calls ``use()`` on an already-defined namespace. That
        is when DDL-less selects stop being hypothetical, the narrowness argument above stops
        holding, and this trade must be re-decided rather than inherited.

        **THE DURABLE ADDRESS IS FINDING #150** (this is its residual) and commit
        ``2105c7e``, the wave that made the DDL leg receiver-blind and left this leg keyed.
        Cite those, never the review reports of that wave — they are untracked scratch files
        at the repo root that repo law requires be DELETED before any image build, so a bound
        whose rationale points at one is a bound nobody can act on.
        """
        # CONTROL 1 — the scan is ALIVE on this exact handle. Without this, the bound below
        # is indistinguishable from a scanner that returns nothing for everything.
        assert _executed_bootstrap_sites_in(
            'await db.query(f"DEFINE NAMESPACE IF NOT EXISTS {ns}")\n'
        ), (
            "the receiver-blind DDL leg stopped seeing `db.query(DEFINE NAMESPACE ...)`. "
            "Fix that first — until it holds, the known-bound assertion below proves nothing, "
            "because a dead scan misses everything."
        )
        # CONTROL 2 — the use() leg itself is live, on a name the predicate DOES recognise.
        assert _executed_bootstrap_sites_in("await connection.use(ns, database)\n"), (
            "the use() leg stopped seeing `connection.use(...)` on a connection-named "
            "receiver. That is not this bound widening — that is the leg going blind "
            "entirely, and it makes the assertion below vacuous."
        )

        # THE BOUND ITSELF.
        assert not _executed_bootstrap_sites_in("await db.use(ns, database)\n"), (
            "the use() leg now SEES `db.use(...)` on a receiver the predicate does not "
            "recognise. **This is a KNOWN BOUND (#150, commit 2105c7e) — if you closed it "
            "deliberately, delete this pin and say so in the same diff.** That is the "
            "conversation this pin exists to force, because closing it means denying "
            "receiver-blind on a generic English verb: check that `monkeypatch.use()` and "
            "every unrelated `.use()` in this tree still pass, or you have built the gate "
            "that gets switched off. If instead you arrived here because a RECONNECT path "
            "now selects a session without re-running the DDL, that is this bound's stated "
            "re-open trigger and the trade genuinely needs re-deciding."
        )

    def test_the_receiver_blind_DDL_leg_costs_this_tree_NOTHING(self) -> None:
        """**THE FALLOUT MEASUREMENT, DERIVED — never a numeral in a comment.**

        Receiver-blindness is only affordable if honest code does not pay for it. That was
        MEASURED before the leg shipped and it is re-measured here on every run, because a
        measurement written into English is a measurement that goes stale silently — which
        is precisely what happened to this section's previous "23 sites, 22 correct code"
        (true when written, falsified by its own commit, #150 audit R2).

        The property, stated so it cannot drift: widening the DDL leg from
        connection-named receivers to ALL receivers adds no site anywhere in this tree.
        """
        blind, _ = _test_tree_bootstrap_sites()

        def _receiver_keyed(source: str) -> list[tuple[int, str]]:
            """The predicate as it was BEFORE R1 — the narrow leg, for comparison only."""
            sites: list[tuple[int, str]] = []
            for node in ast.walk(ast.parse(source)):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and _is_connection_receiver(node.func.value)
                ):
                    continue
                if node.func.attr == _SESSION_SELECT_METHOD:
                    sites.append((node.lineno, "use"))
                    continue
                for argument in ast.walk(node):
                    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                        upper = argument.value.upper()
                        sites.extend(
                            (node.lineno, keyword) for keyword in _BOOTSTRAP_DDL_KEYWORDS if keyword in upper
                        )
            return sites

        narrow = {
            path.relative_to(_TESTS_ROOT).as_posix(): found
            for path in sorted(_TESTS_ROOT.rglob("*.py"))
            if "__pycache__" not in path.parts
            and (found := _receiver_keyed(path.read_text(encoding="utf-8")))
        }

        widened = {
            key: sites for key, sites in blind.items() if len(sites) != len(narrow.get(key, []))
        }
        assert not widened, (
            "going receiver-blind added bootstrap sites to this tree:\n  "
            + "\n  ".join(
                f"{key}:{lineno}  {what}" for key, sites in widened.items() for lineno, what in sites
            )
            + "\n\nThat is the STOP condition the widening shipped under: a gate that "
            "refuses honest code is a gate that gets switched off, and then the next #150 "
            "ships with nothing watching at all. Classify every site above individually "
            "(`all remaining hits are fixtures` is banned output here). If they are "
            "legitimate, they belong in `_TEST_TREE_BOOTSTRAP_ALLOWANCES` with reasons — "
            "if they are not, the widening just caught what it was built to catch."
        )

    def test_the_literal_keyed_scan_would_be_MOSTLY_FALSE_POSITIVES_here(self) -> None:
        """**THE POPULATION CLAIM, DERIVED.** The block above this class asserts that
        production's literal-keyed scan is right for production and wrong here, because in
        ``tests/`` that literal is overwhelmingly DATA. That claim used to be carried by a
        hardcoded pair of numerals which the commit that wrote them falsified in the same
        diff (#150 audit R2). Numerals in prose cannot be checked; this can.

        Both populations are re-derived from the tree on every run, and the pin asserts the
        RELATIONSHIP the design rests on rather than either count.
        """
        executed, scanned = _test_tree_bootstrap_sites()
        executed_total = sum(len(sites) for sites in executed.values())
        literal_total = sum(
            len(_bootstrap_sites_in((_TESTS_ROOT / key).read_text(encoding="utf-8"))) for key in scanned
        )

        assert literal_total > 4 * executed_total, (
            f"the literal-keyed scan found {literal_total} sites in this tree and the "
            f"execution-keyed scan found {executed_total}. The whole justification for the "
            f"test-tree gate being keyed on EXECUTION rather than on the string is that the "
            f"string is overwhelmingly data here. If those two numbers have converged, that "
            f"justification no longer holds and this section's reasoning needs rewriting — "
            f"not this threshold nudging."
        )
        assert executed_total == sum(
            expected for expected, _ in _TEST_TREE_BOOTSTRAP_ALLOWANCES.values()
        ), (
            f"the execution-keyed scan found {executed_total} sites tree-wide but the "
            f"allowlist grants "
            f"{sum(expected for expected, _ in _TEST_TREE_BOOTSTRAP_ALLOWANCES.values())}. "
            f"Those must agree exactly, or some site is being tolerated by neither the "
            f"gate nor a reasoned allowance."
        )

    def test_the_scan_SPARES_a_fake_that_merely_DEFINES_the_bootstrap_methods(self) -> None:
        """**NEGATIVE CONTROL 1 — the false positive that would kill this gate on day one.**
        This tree is full of doubles that define ``async def use`` / ``async def query``;
        ``_FakeConnection`` in ``test_surreal_harness.py`` is one, and it exists precisely
        to test the #150 fix. DEFINING a method is not RUNNING a bootstrap.
        """
        source = '''
class _FakeConnection:
    """A double: it defines the bootstrap surface and records what it is asked to run."""

    async def use(self, namespace, database):
        self.used = (namespace, database)

    async def query(self, statement, params=None):
        self.statements.append(statement)

    async def signin(self, credentials):
        self.signed_in = True
'''
        assert not _executed_bootstrap_sites_in(source), (
            "the scan flagged a test double for DEFINING `use`/`query`. Every fake in this "
            "tree defines them; a gate that reds the suite for writing a fake is a gate the "
            "next engineer switches off, and then nothing is watching at all."
        )

    def test_the_scan_SPARES_bootstrap_DDL_held_as_fixture_DATA(self) -> None:
        """**NEGATIVE CONTROL 2 — the discrimination that makes a test-tree scan possible.**
        nearly every literal-keyed hit in this tree is DATA: expected values, source
        fixtures fed to the scanners above, prose inside assertion messages. Production's
        literal-keyed pin is right for production and would be wrong here, and the reason
        is population, not rigour.
        """
        source = '''
_EXPECTED_BOOTSTRAP_DDL = "DEFINE NAMESPACE IF NOT EXISTS lore; DEFINE DATABASE IF NOT EXISTS main;"

_HAND_ROLLED_FIXTURE = """
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {ns}")
    await connection.use(ns, db)
"""


def test_the_seam_emits_the_bootstrap_ddl(recorded):
    assert recorded.statements[0] == _EXPECTED_BOOTSTRAP_DDL, (
        "the seam must emit DEFINE NAMESPACE before DEFINE DATABASE"
    )
'''
        assert not _executed_bootstrap_sites_in(source), (
            "the scan flagged bootstrap DDL held as DATA — a fixture, an expected value, a "
            "message. Nothing here reaches a live connection. Firing on these is how a "
            "test-tree gate earns 22 false positives and one very short life."
        )

    def test_the_two_scans_SHARE_their_predicates_rather_than_cloning_them(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """**PROVED BY MUTATION, the only proof a private copy cannot fake.** Routing is not
        sharing and neither is looking identical: a second scan that hand-rolled its own
        notion of "the select method" would pass every pin above while drifting silently
        from the production gate it claims to extend.

        So: move each shared name, and BOTH scans must go blind together.

        **ALL THREE SHARED NAMES ARE MUTATED HERE, and that is the repair.** This
        docstring's predecessor named three — ``_is_connection_receiver``,
        ``_SESSION_SELECT_METHOD``, ``_BOOTSTRAP_DDL_KEYWORDS`` — and then promised
        *"that mutation is not an argument here; it is executed, below"*. Only
        ``_SESSION_SELECT_METHOD`` was ever mutated. A comment that tells a reviewer a
        case is covered when it is not is a FALSE GATE of exactly the class this file
        hunts (#150 audit R4), and the cure for a claim is to EXECUTE it, not to soften
        the prose.
        """
        module = sys.modules[__name__]

        # --- shared name 1: the select method, on both use() legs -------------------
        select = "await connection.use(namespace, database)\n"
        assert _bootstrap_sites_in(select), "control: the production scan sees the select"
        assert _executed_bootstrap_sites_in(select), "control: the test-tree scan sees it"

        monkeypatch.setattr(module, "_SESSION_SELECT_METHOD", "not_the_select")

        assert not _bootstrap_sites_in(select), (
            "the PRODUCTION scan kept finding `use()` after `_SESSION_SELECT_METHOD` moved "
            "— it is not reading the shared constant, so this mutation proves nothing about "
            "either scan."
        )
        assert not _executed_bootstrap_sites_in(select), (
            "the TEST-TREE scan kept finding `use()` after `_SESSION_SELECT_METHOD` moved: "
            "it is a private copy wearing the shared name. Fold it back onto the production "
            "gate's constants — one implementation, or the two drift and only one gets the "
            "next fix."
        )
        monkeypatch.undo()

        # --- shared name 2: the DDL keywords, on both DDL legs ----------------------
        ddl = 'await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {ns}")\n'
        assert _bootstrap_sites_in(ddl), "control: the production scan sees the DDL literal"
        assert _executed_bootstrap_sites_in(ddl), "control: the test-tree scan sees the DDL call"

        monkeypatch.setattr(module, "_BOOTSTRAP_DDL_KEYWORDS", ("DEFINE GALAXY",))

        assert not _bootstrap_sites_in(ddl), (
            "the PRODUCTION scan kept finding `DEFINE NAMESPACE` after "
            "`_BOOTSTRAP_DDL_KEYWORDS` moved — it holds its own private copy of the "
            "engine's vocabulary."
        )
        assert not _executed_bootstrap_sites_in(ddl), (
            "the TEST-TREE scan kept finding `DEFINE NAMESPACE` after "
            "`_BOOTSTRAP_DDL_KEYWORDS` moved: it hand-rolled its own keyword tuple. Teach "
            "the engine a new bootstrap statement and only one of these two scans would "
            "learn it — which is the drift this pin exists to make impossible."
        )
        monkeypatch.undo()

        # --- shared name 3: the receiver predicate, on both use() legs --------------
        # NOTE the asymmetry, and it is by design rather than an oversight: only the
        # use() legs consult this predicate now. The DDL legs are receiver-blind (test
        # tree) and literal-keyed (production), so neither can be blinded by moving it —
        # asserting that they COULD would be a second false gate, in the fix for the first.
        assert _bootstrap_sites_in(select), "control: the production scan sees the select again"
        assert _executed_bootstrap_sites_in(select), "control: the test-tree scan does too"

        monkeypatch.setattr(module, "_is_connection_receiver", lambda node: False)

        assert not _bootstrap_sites_in(select), (
            "the PRODUCTION scan still matched a receiver after `_is_connection_receiver` "
            "was blinded — it is not the predicate this section claims both scans read."
        )
        assert not _executed_bootstrap_sites_in(select), (
            "the TEST-TREE scan still matched a receiver after `_is_connection_receiver` "
            "was blinded: its use() leg hand-rolls its own notion of what a connection is, "
            "so widening the shared predicate would reach only one of the two scans."
        )
        assert _executed_bootstrap_sites_in(ddl), (
            "the test-tree DDL leg went blind when `_is_connection_receiver` did — it is "
            "supposed to be RECEIVER-BLIND (#150 audit R1). If it consults the predicate "
            "again, `db = AsyncSurreal(url)` is invisible to this gate once more."
        )


class TestOneBootstrapImplementationAndOneQueryImplementation:
    """**THE DRY PIN, and it is IDENTITY + SPY** — the same pair
    :class:`TestEverySeamHoldsTheOneDriver` established, because they answer different
    questions and neither is sufficient alone:

      * IDENTITY cannot be faked by a copy. ``module.bootstrap_session is
        _txn.bootstrap_session`` is False for ten private re-implementations wearing one
        name — the exact build a cold adversary writes, which passes every behavioural pin
        because every module "has" the helper.
      * The SPY proves the seam actually CALLS it. A module can import a name and hand-roll
        the loop anyway; identity alone proves it is imported and unused.

    The AST pin above is the third leg, and it covers what neither of these can: a private
    bootstrap that still runs BESIDE the shared one.
    """

    @pytest.mark.parametrize(("module_path", "class_name"), _BOOTSTRAP_OWNERS)
    def test_every_connection_owner_holds_the_ONE_shared_bootstrap(
        self, module_path: str, class_name: str
    ) -> None:
        """RED today x11 (the ten store seams + scout): the name does not exist."""
        module = importlib.import_module(module_path)
        held = getattr(module, "bootstrap_session", None)

        assert held is not None, (
            f"{module_path} ({class_name}) does not hold the shared session bootstrap — so "
            f"whatever DDL its `_ensure_connection` runs is its own private copy, and there "
            f"are eleven of them. " + _MISSING_SHARED_HELPER.format(name="bootstrap_session")
        )
        assert held is _shared("bootstrap_session"), (
            f"{module_path}.bootstrap_session is NOT _txn.bootstrap_session — it is a "
            f"different object wearing the same name. A copy passes every behavioural pin "
            f"and shares nothing; that is the defect this wave exists to delete, and it is "
            f"the one thing a copy can never fake."
        )

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_every_seams_bootstrap_GOES_THROUGH_the_shared_helper(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        """The SPY half — and it checks the ARGUMENTS, not just the call.

        THE WRONG BUILD THIS CATCHES: one that calls the shared helper with the seam's
        wiring and then runs its OWN DDL anyway (belt and braces, ships two bootstraps), or
        one that calls it with placeholder arguments to satisfy a spy and bootstraps for
        real underneath. The first is caught by the AST pin; the second is caught here, by
        requiring the helper to receive THIS seam's namespace and database.
        """
        module = _point_at(monkeypatch, module_path, _BootstrapCleanThenConflictingConnection())
        helper = getattr(module, "bootstrap_session", None)
        assert helper is not None, _MISSING_SHARED_HELPER.format(name="bootstrap_session")

        seen: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

        async def _spy(*args: Any, **kwargs: Any) -> Any:
            seen.append((args, kwargs))
            return await helper(*args, **kwargs)

        monkeypatch.setattr(module, "bootstrap_session", _spy)
        instance = _construct(seam)

        await instance._ensure_connection()

        assert seen, (
            f"{seam.__name__}._ensure_connection ({module_path}) bootstrapped WITHOUT going "
            f"through the shared helper — it imports the name and hand-rolls the DDL anyway. "
            f"Routing is not sharing, and neither is importing."
        )
        # A LIST, never a set (C-DEF-1, caught by the contract adversary): the connection
        # fakes are ``@dataclass`` instances, so they are UNHASHABLE — and the contract's own
        # prescribed signature, ``bootstrap_session(connection, namespace, database)``, hands
        # the connection straight in. Building a set here raised ``TypeError`` on EVERY
        # correct build, in all ten seams. The pin was red today for the RIGHT reason (the
        # helper does not exist, so the assert above fires first), which is exactly why its
        # author never saw it. **A contract no correct build can satisfy is a defect, whatever
        # else it catches.** List membership uses ``__eq__`` and needs no hash.
        passed = [*seen[0][0], *seen[0][1].values()]
        assert _CTOR_VALUES["namespace"] in passed and _CTOR_VALUES["database"] in passed, (
            f"the shared bootstrap was called, but not with {seam.__name__}'s own namespace "
            f"and database ({seen[0]!r}). A call whose arguments the seam does not depend on "
            f"is a call that satisfies a spy and bootstraps nothing."
        )

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_every_seams_query_GOES_THROUGH_the_shared_attempt_body(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        """The other ten copies: the ``async def _attempt()`` body, byte-identical across ten
        files but for one log-event string. It carries the classification LADDER — the
        decision this wave's own law says may never be cloned — so it is one function too.

        RED today x10: ``_txn.run_query`` does not exist and each seam hand-rolls the body.
        """
        module = importlib.import_module(module_path)
        held = getattr(module, "run_query", None)

        assert held is not None, (
            f"{module_path} does not hold the shared single-statement attempt body, so "
            f"{seam.__name__}._query hand-rolls one — including its CLASSIFICATION, which is "
            f"policy. " + _MISSING_SHARED_HELPER.format(name="run_query")
        )
        assert held is _shared("run_query"), (
            f"{module_path}.run_query is NOT _txn.run_query — a private copy wearing the "
            f"shared name"
        )

        seen: list[object] = []

        async def _spy(*args: Any, **kwargs: Any) -> Any:
            seen.append(kwargs or args)
            return await held(*args, **kwargs)

        monkeypatch.setattr(module, "run_query", _spy)
        connection = _ConflictingConnection(conflicts=2, rows=[{"next": 3}])

        result = await _seam_on(seam, connection)._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        assert seen, (
            f"{seam.__name__}._query ran a statement WITHOUT going through the shared attempt "
            f"body — it is still one of ten hand-written copies of the same ladder"
        )
        assert result == [{"next": 3}]
        assert connection.calls == 3, "the conflict was not retried to success through the helper"

    async def test_scouts_command_bootstrap_holds_it_too(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """**THE ELEVENTH COPY, and it is the one a name-keyed scan cannot see** — again.

        ``scout.py::_open_command_connection`` is a module-level function, owns no
        ``_query``, and carries the same three closures. It was invisible to the `_query`
        enumerator the first time (§4b, the sixth hole) and it is invisible to the
        `_ensure_connection` enumerator now, because scout's own ``_ensure_connection``
        merely delegates to it. The AST pin above sees it; this drives it.
        """
        connection = _BootstrapCleanThenConflictingConnection()
        monkeypatch.setattr(scout_module, "AsyncSurreal", lambda url: connection)
        helper = getattr(scout_module, "bootstrap_session", None)
        assert helper is not None, (
            "scout.py does not hold the shared session bootstrap — it carries the eleventh "
            "hand-rolled copy of the three closures. "
            + _MISSING_SHARED_HELPER.format(name="bootstrap_session")
        )
        assert helper is _shared("bootstrap_session")

        seen: list[object] = []

        async def _spy(*args: Any, **kwargs: Any) -> Any:
            seen.append((args, kwargs))
            return await helper(*args, **kwargs)

        monkeypatch.setattr(scout_module, "bootstrap_session", _spy)

        await scout_module._open_command_connection(
            url="ws://127.0.0.1:19555/rpc",
            namespace=_CTOR_VALUES["namespace"],
            database=_CTOR_VALUES["database"],
            user=_CTOR_VALUES["user"],
            password=_CTOR_VALUES["password"],
        )

        assert seen, "scout's command bootstrap did not go through the shared helper"


class TestTheBootstrapClassifiesThroughTheONEAuthority:
    """**ONE LADDER, proven the only way a ladder can be proven shared: MOVE THE DEFINITION
    AND WATCH EVERY CALLER FOLLOW.**

    The bootstrap's ladder and ``_query``'s ladder are being merged. The hazard in a merge is
    the same one ``TestDetectionFollowsTheOneSharedMarker`` exists for on the ``_query`` side:
    a collapse that routes the bootstrap through the shared helper and matches the engine's
    prose LOCALLY inside it. That build retries, backs off, raises the typed error, and
    passes every pin in 7c — and the day SurrealDB rewords its message, every bootstrap in
    the tree silently stops retrying and the 6.2%-34.4% tail of concurrent first-connects
    starts failing again.

    Green today (the bootstrap closures already call ``is_retryable_conflict_error``). It is
    here so that it is STILL green after thirty closures become one — the property is not
    "the bootstrap retries", it is "the bootstrap and the seam cannot disagree about what a
    conflict IS".
    """

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_the_bootstrap_retries_a_conflict_the_MOVED_marker_now_names(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        """The ORACLE here is that ``_ensure_connection()`` RETURNS AT ALL: a bootstrap that
        cannot see the moved marker classifies the first conflict as a non-conflict and
        raises ``SurrealConnectionError`` on attempt one.

        The attempt COUNT is a corroborating floor, not the oracle, and it is deliberately
        an inequality: the bootstrap is not one driver call but THREE (namespace, use,
        database), each with its own budget, so the fixture's ``_BOOTSTRAP_MOVED_FAILURES``
        conflicts are all absorbed by the FIRST step and the remaining steps add calls of
        their own. Pinning an exact total here would pin the bootstrap's internal step count
        — which is precisely what section 7d is about to collapse — and the pin would go red
        for a bookkeeping reason on the correct build. (It did, on its first run. This
        comment is the receipt.)
        """
        _silence_sleep(monkeypatch)
        _mutate_shared_marker(monkeypatch)
        connection = _BootstrapScriptedConnection(
            error=_mutated_conflict_error(), failures=_BOOTSTRAP_MOVED_FAILURES
        )
        _point_at(monkeypatch, module_path, connection)
        instance = _construct(seam)

        await instance._ensure_connection()

        assert connection.bootstrap_calls > _BOOTSTRAP_MOVED_FAILURES, (
            f"{seam.__name__}'s bootstrap ({module_path}) did NOT retry a conflict the shared "
            f"marker now names ({connection.bootstrap_calls} attempt(s) against "
            f"{_BOOTSTRAP_MOVED_FAILURES} conflicts) — it is matching engine prose of its "
            f"OWN, so it cannot see a conflict the ONE authority recognises. Detection lives "
            f"in one place for the same reason policy does."
        )

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_the_bootstrap_stops_retrying_text_the_marker_ABANDONED(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        """THE KILLER, and it is the direction a private prose-match can never survive: it
        keeps retrying a message the shared authority has stopped calling a conflict.
        """
        _silence_sleep(monkeypatch)
        _mutate_shared_marker(monkeypatch)
        connection = _BootstrapScriptedConnection(error=_conflict_error(), failures=None)
        _point_at(monkeypatch, module_path, connection)
        instance = _construct(seam)

        with pytest.raises(SurrealConnectionError) as exc_info:
            await instance._ensure_connection()

        assert connection.bootstrap_calls == 1, (
            f"{seam.__name__}'s bootstrap retried {connection.bootstrap_calls - 1} time(s) on "
            f"a message the shared marker NO LONGER recognises as a conflict — it is "
            f"branching on engine prose it keeps privately. Reword the engine and this "
            f"bootstrap's retry dies silently."
        )
        assert not isinstance(exc_info.value, TxnContentionExhaustedError), (
            "a non-conflict bootstrap failure was reported as exhausted contention"
        )


# ---------------------------------------------------------------------------
# 7e. THE TWELFTH COPY — RETIRED, because the copy is GONE (finding #150).
#
# This section used to hold a ruling and its instrument: ``tests/_surreal_harness.py``
# hand-rolled its own retry budget, its own linear backoff and its own DECLARED literal
# copy of the engine's conflict marker, and the lead ruled the copy KEEPS — on ONE stated
# ground, that the harness must never import a store module (35 test files import it — the
# ruling was argued from a FALSE count of 21, which is the number that CALL ``connect_admin``,
# a smaller and different population; corrected in finding #150's wave at fff1382 — so a
# mid-TDD store breakage would become a collection error across all of them). A duplicate
# that could not be deleted at least got a drift pin.
#
# **THE OPERATOR OVERTURNED THAT RULING ON 2026-07-20**, because RULING 1 removes the ground
# it stood on: the harness reaches ``_txn`` by IN-FUNCTION import, so the collection-isolation
# guarantee is fully preserved AND the duplication is deleted. The harness now declares NO
# CONFLICT-RETRY policy at all — no conflict budget, no backoff, no marker — and the drift
# pin is deleted with
# the copy it guarded, exactly as its own failure message instructed ("if teardown no longer
# needs to detect a retryable conflict, delete this pin in the same diff").
#
# The sharing is now proven where it belongs: by MUTATION, in ``test_surreal_harness.py``
# (``TestTheHarnessRetryPolicyIsTheSeamsPolicy``), which moves this seam's ceiling, deadline
# and marker at run time and requires the harness's OBSERVED attempt count to move with them
# at BOTH its paths. That is strictly stronger than the equality assertion it replaces: two
# literals being EQUAL is something a private copy satisfies by definition.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 7f. THE CONTROL ON THE REPAIRED INSTRUMENT.
#
# Section 5's anti-vacuity control was rebuilt (a vacuous wave is re-run rather than
# failed). That is a change to a GUARD, and a guard nobody has watched fire is not a guard —
# this repo's law, and the reason two of C1's own audits caught themselves: a "closed set is
# enforced" probe that actually rejected on a PARSE ERROR, and a fixture whose collapsed
# group held one item so `len()` was indistinguishable from `sum()`.
#
# So the wave runner is interrogated with the only question that matters: **what WRONG build
# would it still pass?** Three, and each has a pin:
#
#   1. A build whose retry is DEAD produces zero conflicts, forever. If the runner treated
#      the bound as "give up and pass", every contention pin in this module would be
#      decoration. -> ``test_a_run_in_which_NOTHING_ever_contends_is_a_FAILURE``.
#   2. A runner that swallowed a wave's exception to "try another one" would turn a REAL
#      double-apply — a torn counter, a burnt version — into a silent retry, and the oracle
#      this whole section exists for would be unreachable. That is the single most dangerous
#      thing a re-runnable fixture can do. -> ``test_a_failing_ORACLE_is_never_re_run_into_silence``.
#   3. A runner that only ever accepted the FIRST wave would have fixed nothing — the 10%
#      red-on-correct-code rate would survive the repair. -> ``test_a_LATE_wave_that_contends_is_accepted``.
# ---------------------------------------------------------------------------


class TestTheAntiVacuityControlStillFires:
    """The repaired control, shown firing — and shown NOT firing — on cases whose answers
    are known.
    """

    async def test_a_run_in_which_NOTHING_ever_contends_is_a_FAILURE(self) -> None:
        """**POSITIVE CONTROL.** A build with no retry at all conflicts nowhere. The bound is
        a bound on PATIENCE, never a licence to pass: it must run every wave and then FAIL.
        """
        recorder = _JitterRecorder(real=lambda attempt_number: 0.0)
        ran: list[int] = []

        async def _never_contends(wave_index: int) -> bool:
            ran.append(wave_index)
            return False

        with pytest.raises(AssertionError, match="NOT ONE conflict was retried"):
            await _run_contending_waves(recorder, _never_contends)

        assert ran == list(range(_CONTENTION_WAVE_BOUND)), (
            f"the runner tried {len(ran)} wave(s), not {_CONTENTION_WAVE_BOUND} — it either "
            f"gives up early (re-introducing the 10% red-on-correct-code it was built to "
            f"remove) or loops past its bound"
        )

    async def test_a_failing_ORACLE_is_never_re_run_into_silence(self) -> None:
        """**THE PIN THAT MATTERS MOST HERE.** The exactly-once oracle is asserted INSIDE the
        wave. A runner that caught a wave's exception in order to try another one would
        convert a genuine double-applied write — the very defect these pins exist to catch —
        into a retry, and then into a pass.

        The wave's assertions propagate. Only the ANTI-VACUITY control is re-runnable, and
        only because a zero-conflict wave is vacuous BY CONSTRUCTION (``draws == 0`` <=> the
        retry path never ran <=> no retried write can have double-applied).
        """
        recorder = _JitterRecorder(real=lambda attempt_number: 0.0)
        waves_run = 0

        async def _oracle_fails(wave_index: int) -> bool:
            nonlocal waves_run
            waves_run += 1
            raise AssertionError("the 16 racers minted a torn sequence")

        with pytest.raises(AssertionError, match="torn sequence"):
            await _run_contending_waves(recorder, _oracle_fails)

        assert waves_run == 1, (
            f"a wave whose ORACLE failed was re-run ({waves_run} waves). A real double-apply "
            f"would be retried until it happened not to reproduce, and then reported as a "
            f"pass. The wave-retry is for VACUITY only; a torn counter is a STOP."
        )

    async def test_a_LATE_wave_that_contends_is_accepted(self) -> None:
        """**NEGATIVE CONTROL** — and the whole point of the repair. The measured
        red-on-correct-code rate was ~10% per wave under `-n auto`: a runner that demanded
        the FIRST wave contend would have changed nothing at all.
        """
        recorder = _JitterRecorder(real=lambda attempt_number: 0.0)
        ran: list[int] = []
        contends_on = _CONTENTION_WAVE_BOUND - 1  # the LAST wave in the bound

        async def _contends_late(wave_index: int) -> bool:
            ran.append(wave_index)
            return wave_index == contends_on

        await _run_contending_waves(recorder, _contends_late)

        assert ran == list(range(_CONTENTION_WAVE_BOUND)), (
            "the runner did not reach the wave that finally contended"
        )

    async def test_the_recorder_is_cleared_between_waves(self) -> None:
        """A wave must be judged on ITS OWN conflicts. Carrying a previous wave's draws
        forward would make every wave after the first look contended, and the control would
        certify a run in which the racers never met again.
        """
        recorder = _JitterRecorder(real=lambda attempt_number: 0.0)
        draws_seen_at_wave_start: list[int] = []

        async def _wave(wave_index: int) -> bool:
            draws_seen_at_wave_start.append(len(recorder.draws))
            recorder.draw(1)  # this wave "contended"
            return wave_index == 2

        await _run_contending_waves(recorder, _wave)

        assert draws_seen_at_wave_start == [0, 0, 0], (
            f"a wave began with {draws_seen_at_wave_start} draws already on the recorder — "
            f"the control is crediting one wave's contention to the next"
        )


# ---------------------------------------------------------------------------
# THE REJECTION-EVENT EXACT SET (lead ruling, R3).
#
# Each of the ten ``_query`` bodies logs a rejected write under its OWN event name. Those
# names are an OPERATOR-FACING SERVED SURFACE — log greps and dashboards key on them — and
# section 7d routes all ten through ONE ``run_query`` with a ``label`` parameter. **That is
# precisely the moment a silent rename ships**: ten literals become one argument, and no
# gate in this repo can see an English string change value.
#
# So they are pinned the way this repo pins every served set: **ONE canonical list, in ONE
# place** (the exact-set idiom — cf. the tool-registration pin in test_mcp_server.py), not
# ten literals scattered across ten parametrised cases. A DELIBERATE rename then edits this
# list, in a diff a reviewer can see. An ACCIDENTAL one goes red.
#
# The pin below compares this list against what the code ACTUALLY EMITS (driven, captured
# from caplog) — the list is the expectation, never the evidence. Prose that describes
# behaviour must be derived from the behaviour, not re-stated beside it.
#
# THE SEAM'S SERVED SURFACE IS THREE THINGS, NOT ONE (audit-fix-1 A2 · blindreader-dry-2 F6),
# and the collapse threatens each of them differently:
#
#   1. the rejection EVENT  (`_SEAM_REJECTION_EVENTS`) — ten literals become one `label`
#      argument: the moment a silent rename ships.
#   2. the raised-message NOUN (`_SEAM_REJECTION_NOUNS`) — five seams say plain "query" and
#      five say "brief query" / "agent query" / "task query" / "finding query" /
#      "memory query". Preserved from HEAD by the builder, and (until now) pinned by NOTHING:
#      a bare grep of the whole test tree found ZERO assertions on it, while this contract's
#      own illustrative signature omitted the parameter. A builder cleaning up to match the
#      sketch drops five seams' operator-facing wording and passes every gate.
#   3. the emitting LOGGER (`record.name`) — the ten records used to come from
#      `loremaster.tasks` / `loremaster.briefs` / …; after the collapse they are emitted by
#      `_txn`'s module logger. `JsonFormatter` writes `"logger": record.name`, so **every
#      Mezmo query or alert keyed on `logger:loremaster.tasks` silently returns nothing.**
#      Handler/level routing is unaffected (children propagate to the `loremaster` parent), so
#      no gate and no test can see this — only an operator whose dashboard went quiet.
#
# All three are pinned as EXACT MAPPINGS in one place, driven from the DISCOVERED seams.
_SEAM_REJECTION_EVENTS = {
    "AgentRegistry": "agent.query.rejected",
    "BriefLedger": "brief.query.rejected",
    "DiffEngine": "diff.query.rejected",
    "FindingLedger": "finding.query.rejected",
    "LocalMemoryBackend": "memory.query.rejected",
    "SnapshotStamper": "snapshot.query.rejected",
    "SurrealCodeGraph": "graph.query.rejected",
    "SurrealManifest": "manifest.query.rejected",
    "SurrealStore": "store.query.rejected",
    "TaskLedger": "task.query.rejected",
}

# What each seam CALLS the statement it ran, in the message it raises: "SurrealDB {noun}
# rejected against {url} ({error_class})". Derived from HEAD (`git show HEAD:<file>`) and
# re-verified against the built tree — five plain "query", five that name their domain.
#
# THE MONOCULTURE TRAP THIS AVOIDS: a mapping in which every value were "query" would be
# satisfied by a build that hardcoded "query" and dropped the parameter — the exact regression
# audit-fix-1 A2 predicts. Five of the ten values differ, so no single hardcoded noun can pass.
_SEAM_REJECTION_NOUNS = {
    "AgentRegistry": "agent query",
    "BriefLedger": "brief query",
    "DiffEngine": "query",
    "FindingLedger": "finding query",
    "LocalMemoryBackend": "memory query",
    "SnapshotStamper": "query",
    "SurrealCodeGraph": "query",
    "SurrealManifest": "query",
    "SurrealStore": "query",
    "TaskLedger": "task query",
}

# The seam's OWN logger — the `logger:` field every Mezmo query keys on. NOT a hand-list: it
# IS the module path, because every seam does `logger = logging.getLogger(__name__)`. Derived
# from the discovered seams, so an eleventh is covered without anyone editing anything.
_REJECTION_NOUN_PATTERN = re.compile(r"SurrealDB (?P<noun>.+?) rejected against")
_TRANSPORT_NOUN_PATTERN = re.compile(r"SurrealDB (?P<noun>.+?) failed against")


class TestTheSeamsRejectionLogSurvivesTheCollapse:
    """**REMOVED-BEHAVIOUR PRESERVATION for section 7d.** Ten ``_query`` bodies become one
    ``run_query`` — and each of those ten bodies carries a ``logger.error`` that is the ONLY
    place a domain rejection's full engine text is ever written.

    Ledger #31 keeps the raw text OUT of the raised exception (it can echo a bound VALUE
    back verbatim, and that text flows to MCP clients), so the log line is not a nicety: it
    is the entire diagnostic path for a rejected write. A collapse that folds ten bodies
    into one and drops the logging leaves an operator with a classified label and nothing
    else — and no gate would see it, because every behavioural pin in this module asserts on
    the raised TYPE.

    Green today, x10. It is here to still be green tomorrow.
    """

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_a_domain_rejection_still_logs_the_full_engine_text_server_side(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, module_path: str, seam: type
    ) -> None:
        _silence_sleep(monkeypatch)
        caplog.set_level(logging.DEBUG)
        rejection = InternalError(ErrorKind.INTERNAL, _LIVE_ASSERT_TEXT)

        with pytest.raises(SurrealStoreError) as exc_info:
            await _seam_on(seam, _RejectingConnection(rejection))._query(
                _MINT_STATEMENT, {"name": _WAVE_NAME}
            )

        carriers = [
            record
            for record in caplog.records
            if _SENSITIVE_MARKER in str(getattr(record, "engine_error", ""))
        ]
        assert len(carriers) == 1, (
            f"{seam.__name__}._query ({module_path}) rejected a write and emitted "
            f"{len(carriers)} log record(s) carrying the engine's own text. Ledger #31 keeps "
            f"that text OUT of the raised message, so this line is the ONLY place it is ever "
            f"written — an operator holding the classified label has nowhere else to look. "
            f"Ten bodies collapsing into one must carry their logging with them, not lose it."
        )
        assert _SENSITIVE_MARKER not in str(exc_info.value), (
            "ledger #31: the raised message echoed the bound value back verbatim"
        )

    async def test_every_seam_still_logs_its_OWN_canonical_rejection_event(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**THE EXACT-SET PIN** (lead ruling R3) — one canonical list, compared against what
        the code actually EMITS, in ONE test so the comparison is over the whole SET.

        Three wrong builds, three failure modes, and a per-seam parametrised pin catches none
        of them as a set:

          * **the silent rename.** ``run_query(label=…)`` turns ten literals into one
            argument. A builder who tidies ``brief.query.rejected`` into
            ``briefs.query.rejected`` breaks every operator log-grep and dashboard keyed on
            it, and no gate in this repo can see an English string change value. -> the
            value comparison.
          * **the HOMOGENISED event.** A collapse that logs ONE generic
            ``store.query.rejected`` for all ten is the easiest thing to write and destroys
            the operator's ability to tell WHICH ledger rejected a write. -> the
            distinctness assertion (ten seams, ten distinct events).
          * **the seam that quietly falls out.** An eleventh ledger, or one whose logging is
            dropped in the collapse, must not slip past by simply not being in anyone's
            list. -> the KEY-set comparison, driven from the DISCOVERED seams, so the
            observed side is the ALL set and the canonical list is only the expectation.

        The list is the EXPECTATION. The evidence is driven and captured. If those two ever
        disagree, this names both — and a deliberate rename edits one list, in a diff a
        reviewer can see.
        """
        _silence_sleep(monkeypatch)
        caplog.set_level(logging.DEBUG)
        observed: dict[str, str] = {}
        observed_nouns: dict[str, str] = {}
        observed_loggers: dict[str, str] = {}
        expected_loggers = {
            seam.__name__: module_path for module_path, seam in _discover_query_seams()
        }

        for module_path, seam in _discover_query_seams():
            caplog.clear()
            rejection = InternalError(ErrorKind.INTERNAL, _LIVE_ASSERT_TEXT)
            with pytest.raises(SurrealStoreError) as exc_info:
                await _seam_on(seam, _RejectingConnection(rejection))._query(
                    _MINT_STATEMENT, {"name": _WAVE_NAME}
                )
            # The NOUN, read out of the message the seam actually RAISED (audit-fix-1 A2).
            raised = _REJECTION_NOUN_PATTERN.search(str(exc_info.value))
            assert raised is not None, (
                f"{seam.__name__} raised {str(exc_info.value)!r}, which does not match the "
                f"seam's rejection-message shape 'SurrealDB <noun> rejected against <url> "
                f"(<class>)'. That shape is operator-facing and is preserved from HEAD."
            )
            observed_nouns[seam.__name__] = raised.group("noun")

            carriers = [
                record
                for record in caplog.records
                if _SENSITIVE_MARKER in str(getattr(record, "engine_error", ""))
            ]
            assert len(carriers) == 1, (
                f"{seam.__name__} emitted {len(carriers)} rejection record(s) carrying the "
                f"engine text — expected exactly one (see the sibling pin)"
            )
            # R-1 (contract adversary): the record's SHAPE is served too, not just its name.
            # A collapse that keeps the event and drops the extras leaves an operator with a
            # log line that says a write was rejected and will not say WHICH SERVER or WHAT
            # KIND — and the triage label is the one thing ledger #31 lets out of the seam.
            for key in ("url", "error_class"):
                assert getattr(carriers[0], key, None) is not None, (
                    f"{seam.__name__}'s rejection record dropped the {key!r} extra. The "
                    f"raised message is deliberately generic (ledger #31 keeps the engine's "
                    f"text out of it), so this record is the operator's ONLY triage surface: "
                    f"it must still name the server and the error class."
                )
            observed[seam.__name__] = carriers[0].getMessage()
            observed_loggers[seam.__name__] = carriers[0].name
            del module_path  # named for symmetry; the logger map above is what consumes it

        # -- the NOUN, as an exact MAPPING (audit-fix-1 A2) -----------------------------
        assert observed_nouns == _SEAM_REJECTION_NOUNS, (
            "a seam's raised-message NOUN changed:\n  "
            + "\n  ".join(
                f"{name}: raises 'SurrealDB {observed_nouns[name]} rejected …', canonical "
                f"says 'SurrealDB {_SEAM_REJECTION_NOUNS.get(name)} rejected …'"
                for name in sorted(observed_nouns)
                if observed_nouns.get(name) != _SEAM_REJECTION_NOUNS.get(name)
            )
            + "\n\nFive of the ten seams name their domain ('brief query', 'agent query', "
            "'task query', 'finding query', 'memory query') and five say plain 'query'. That "
            "wording is OPERATOR-FACING and was preserved from HEAD through the collapse — but "
            "it survives only as a `noun=` argument now, and until this pin NOTHING in the "
            "whole test tree asserted it. A builder tidying its code to match a signature "
            "sketch that omitted the parameter regresses five seams and passes every gate."
        )

        # -- the emitting LOGGER (blindreader-dry-2 F6) ---------------------------------
        assert observed_loggers == expected_loggers, (
            "a seam's rejection record is no longer emitted by the seam's OWN logger:\n  "
            + "\n  ".join(
                f"{name}: logger={observed_loggers[name]!r}, expected {expected_loggers[name]!r}"
                for name in sorted(observed_loggers)
                if observed_loggers[name] != expected_loggers[name]
            )
            + "\n\n`JsonFormatter` writes `\"logger\": record.name`, so this IS a served field. "
            "Every Mezmo query or alert keyed on `logger:loremaster.tasks` for "
            "`task.query.rejected` silently returns NOTHING once the record is emitted by "
            "`loremaster.store._txn` instead. Handler and level routing are unaffected (children "
            "propagate to the `loremaster` parent), which is precisely why no gate, no type "
            "checker and no other test can see this — only an operator whose dashboard went "
            "quiet. The shared `run_query` must log through the CALLER's logger, not its own.\n\n"
            "(The driver's own `store.retry.exhausted` is a NEW event with no existing "
            "consumers and may stay on `loremaster.store._txn` — see "
            "TestExhaustionIsLoggedExactlyOnceOnBothPaths.)"
        )

        assert observed.keys() == _SEAM_REJECTION_EVENTS.keys(), (
            f"the set of seams that log a rejection has changed.\n"
            f"  seams with NO entry in the canonical list: "
            f"{sorted(observed.keys() - _SEAM_REJECTION_EVENTS.keys())}\n"
            f"  entries naming a seam that no longer exists: "
            f"{sorted(_SEAM_REJECTION_EVENTS.keys() - observed.keys())}\n"
            f"Add or remove the entry DELIBERATELY, in a diff a reviewer can see — a served "
            f"log event is not something that should change by accident."
        )
        assert observed == _SEAM_REJECTION_EVENTS, (
            "a seam's rejection log EVENT changed value:\n  "
            + "\n  ".join(
                f"{name}: emits {observed[name]!r}, canonical list says "
                f"{_SEAM_REJECTION_EVENTS[name]!r}"
                for name in sorted(observed)
                if observed[name] != _SEAM_REJECTION_EVENTS[name]
            )
            + "\n\nThese are OPERATOR-FACING: log greps and dashboards key on them. The "
            "`run_query` collapse turns ten literals into one `label` argument, which is "
            "exactly where a rename ships silently. If the rename is intended, edit the "
            "canonical list above."
        )
        assert len(set(observed.values())) == len(observed), (
            f"two or more seams now log the SAME rejection event "
            f"({sorted(observed.values())}). The collapse HOMOGENISED them — an operator "
            f"reading the log can no longer tell which ledger rejected the write, which is "
            f"the entire reason each seam carried its own event name."
        )


# ===========================================================================
# 8. THE ADVERSARY'S THREE SURVIVORS.
#
# A cold contract-adversary built the fix (W0), then built wrong builds on top of it, and
# found THREE that pass this entire contract **and the entire 5,328-test suite with results
# byte-identical to a correct build**. Every one is a plausible builder move, not a
# contrivance. The common shape, and it is the PR93 quantifier law arriving for THIS
# contract's own invariants:
#
#     an invariant conditioned on the failure mode that prompted the work is not an
#     invariant. It is a description of the bug we already found.
#
#   * §7c pinned "∀ ways the BOOTSTRAP can fail -> SurrealConnectionError" — quantified over
#     the ten `_query` OWNERS. **Scout owns a bootstrap and no `_query`.** Its connect's
#     failure fate was quantified over by nothing.  -> 8a
#   * The wave REWRITES all ten `_ensure_connection`s and the contract pinned NOTHING about
#     the double-checked connect lock they each carry. The only pin in the repo is a
#     HAND-LIST of three, in a neighbouring file, written before the other seven existed —
#     "a pin over a hand-written list is only as complete as the list", which is this
#     contract's own docstring, coming true on this contract.  -> 8b
#   * Item B pinned ONE guarded-CAS handler: the one that had the bug. The package has
#     FOUR.  -> 8c
# ===========================================================================


# ---------------------------------------------------------------------------
# 8a. SCOUT'S CONNECT MUST REACH THE RECONNECT LADDER.  (adversary P-1, BLOCKER)
#
# `CommandSubscriber.run()` catches `(*_CONNECTION_ERRORS, KeyError,
# TxnContentionExhaustedError)` — **raw SDK types** — and backs off + reconnects.
# `SurrealConnectionError` is a `RuntimeError`, and `_CONNECTION_ERRORS` is
# `(OSError, SurrealError, WebSocketException)`. It is NOT in that tuple.
#
# So a §7d collapse that puts the `SurrealConnectionError` wrap INSIDE the shared
# `bootstrap_session` — **the obvious DRY reading: one helper, one disposition** — satisfies
# §7c perfectly for all ten seams, and the connect's failure then flies straight past scout's
# ladder. No backoff. No reconnect. **The command channel is dead until the process
# restarts.** That build scores 342/342 here, 33/33 on test_scout.py, and is indistinguishable
# from correct across the whole suite.
#
# scout.py:138-145 states this law in PROSE. Prose is not an instrument — this repo's own law,
# and this is the third time it has been proven on this wave. The instrument is below.
#
# WHERE THE WRAP GOES IS THEREFORE PART OF THE CONTRACT: at the SEAM (each
# `_ensure_connection` wraps what the shared bootstrap raises), never inside the shared
# bootstrap. One helper; the DISPOSITION stays with the caller that owns the fate — exactly
# the same reconciliation §7d already makes for `run_query` (see the ORDER-vs-DISPOSITION
# note there). Scout's caller wants the raw type. The ledgers' callers want the wrap.
# ---------------------------------------------------------------------------


@dataclass
class _BootstrapFailsThenHealthy:
    """Connection #1's bootstrap dies with ``error``, forever. Connection #2 is a healthy
    command channel holding one pending command, inserted during the gap.

    A subscriber that SURVIVES the failed connect backs off, asks for connection #2, drains
    the command and dispatches it. One that dies never asks for a second connection — so the
    oracle is the DISPATCH, not an exception type: it reads the behaviour the ladder exists
    to produce, not the plumbing that produces it.
    """

    error: BaseException
    pending: dict[str, dict[str, Any]] = field(default_factory=dict)
    bootstrap_attempts: int = field(default=0, init=False)
    healthy: bool = field(default=False, init=False)

    def _fail(self) -> None:
        self.bootstrap_attempts += 1
        if self.bootstrap_attempts > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError("unbounded retry in scout's bootstrap")
        raise self.error

    async def signin(self, credentials: dict[str, Any]) -> None:
        return None

    async def use(self, namespace: str, database: str) -> None:
        if not self.healthy:
            self._fail()

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        if not self.healthy:
            self._fail()
        upper = statement.strip().upper()
        if upper.startswith("LIVE SELECT"):
            return "live-uuid-1"
        if upper.startswith("SELECT"):
            return list(self.pending.values())
        if upper.startswith("UPDATE"):
            blob = statement + repr(params or {})
            for key in list(self.pending):
                if key in blob:
                    self.pending.pop(key, None)
            return []
        return []

    async def subscribe_live(self, live_uuid: Any) -> Any:
        raise ConnectionResetError("live unavailable — the poll backstop carries it")

    async def kill(self, live_uuid: Any) -> None:
        return None

    async def close(self) -> None:
        return None


# The two ways a CONNECT can fail. Both must reach the ladder; the wave newly makes the
# second one POSSIBLE (before it, the bootstrap never retried, so it could not exhaust).
_SCOUT_CONNECT_FAILURES = [
    pytest.param(lambda: OSError("connection refused"), id="transport-fault"),
    pytest.param(_conflict_error, id="SUSTAINED-CONTENTION-exhausts-the-budget"),
]


class TestScoutsConnectFailureReachesTheReconnectLadder:
    """**adversary P-1 — the BLOCKER that survives everything else.**

    Drives the REAL ``CommandSubscriber.run()`` loop with the REAL
    ``_open_command_connection`` as its connect factory. The oracle is that the gap command
    is eventually DISPATCHED: the subscriber must back off, RECONNECT, and recover it.
    """

    @pytest.mark.parametrize("build_error", _SCOUT_CONNECT_FAILURES)
    async def test_a_failed_CONNECT_backs_off_and_RECONNECTS(
        self, monkeypatch: pytest.MonkeyPatch, build_error: Callable[[], BaseException]
    ) -> None:
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)  # a sustained conflict exhausts at the floor
        dead = _BootstrapFailsThenHealthy(error=build_error())
        healthy = _BootstrapFailsThenHealthy(
            error=AssertionError("unused"), pending={"command:gap": {"id": "command:gap"}}
        )
        healthy.healthy = True
        handed: list[Any] = [dead, healthy]
        monkeypatch.setattr(scout_module, "AsyncSurreal", lambda url: handed.pop(0) if handed else healthy)

        dispatched: list[str] = []

        async def _handler(row: dict[str, Any]) -> None:
            dispatched.append(str(row["id"]))

        async def _connect() -> Any:
            return await scout_module._open_command_connection(
                url="ws://127.0.0.1:19555/rpc",
                namespace=_CTOR_VALUES["namespace"],
                database=_CTOR_VALUES["database"],
                user=_CTOR_VALUES["user"],
                password=_CTOR_VALUES["password"],
            )

        async def _immediate_sleep(_: float) -> None:
            await _REAL_ASYNCIO_SLEEP(0)

        subscriber = scout_module.CommandSubscriber(
            connect=_connect, handler=_handler, poll_interval_s=0.001, sleep=_immediate_sleep
        )
        task = asyncio.create_task(subscriber.run())
        try:
            for _ in range(400):
                if not healthy.pending:
                    break
                await _REAL_ASYNCIO_SLEEP(0.01)
        finally:
            with contextlib.suppress(Exception):
                await subscriber.stop()
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task

        assert dead.bootstrap_attempts >= 1, (
            "the fixture never reached scout's bootstrap — nothing is proven"
        )
        died_with = task.exception() if task.done() and not task.cancelled() else None
        assert dispatched == ["command:gap"], (
            f"the subscriber did NOT survive a failed CONNECT (dispatched={dispatched}; the "
            f"run() task died with: {died_with!r}).\n\n"
            f"`run()`'s reconnect ladder catches (*_CONNECTION_ERRORS, KeyError, "
            f"TxnContentionExhaustedError) — RAW SDK types. `SurrealConnectionError` is a "
            f"RuntimeError and is NOT among them. A shared `bootstrap_session` that wraps its "
            f"own failure (the obvious DRY reading: one helper, one disposition) satisfies "
            f"§7c for all ten ledgers and flies straight past this ladder: no backoff, no "
            f"reconnect, the command channel dead until the process restarts.\n\n"
            f"THE WRAP GOES AT THE SEAM, not inside the shared bootstrap. One helper; the "
            f"DISPOSITION stays with the caller that owns the fate."
        )


# ---------------------------------------------------------------------------
# 8b. ONE SOCKET UNDER CONCURRENT FIRST-USE.  (adversary P-2, BLOCKER)
#
# Every `_ensure_connection` this wave rewrites carries a DOUBLE-CHECKED LOCK:
#
#     if self._connection is not None: return self._connection      # fast path
#     async with self._connect_lock:
#         if self._connection is not None: return self._connection  # the re-check
#         ... AsyncSurreal(url) ... signin ... bootstrap ...
#
# **The contract pinned nothing about it.** The only pin in the repo is
# `test_surreal_store.py::TestConnectionRaceSingleConnect` — a HAND-LIST OF THREE
# (`SurrealStore`, `SurrealManifest`, `SurrealCodeGraph`; its docstring says "verified by
# reading each class's source"), written before the other seven owners existed. Drop the lock
# in the SEVEN nobody pins and the build scores 342/342 here and is byte-identical to correct
# across the whole 5,328-test suite. N concurrent first-callers each open their own socket;
# N−1 are abandoned, N signins are burned.
#
# That is *this contract's own docstring* — "a pin over a hand-written list is only as
# complete as the list, and the list is exactly what nobody can be trusted to keep" — coming
# true ON this contract, from a neighbouring file. So the set is DISCOVERED.
#
# THE ENUMERATION IS BY PROPERTY, NOT BY MEMBERSHIP: every class whose `_ensure_connection`
# CONSTRUCTS its own socket (`AsyncSurreal(...)`). That is precisely the population the
# double-checked lock protects, and it is what makes the eleventh lazy ledger pinned the day
# it is written.
#
# ⚠ AND IT IS WHY THIS IS **NOT** PARAMETRISED OVER `_discover_bootstrap_owners()` (11), which
# the brief suggested: scout's `CommandSubscriber` owns an `_ensure_connection` but RECEIVES
# its connection from an injected `connect` callable and constructs no socket — and it holds
# no lock. Parametrising over all 11 would have made this pin RED ON A CORRECT BUILD, which is
# exactly the C-DEF class the adversary just caught me shipping. The property excludes it; my
# opinion does not. (Scout's own bare check-then-set is surfaced as a residual — see the
# report — because `run()` is its only driver today, and "only one caller exists" is an
# argument, not a probe.)
# ---------------------------------------------------------------------------

# The concurrent first-callers. Eight, matching the house floor for a concurrency pin and the
# neighbouring hand-listed pin it replaces.
_RACE_CALLERS = 8
# A delay inside `signin` so all _RACE_CALLERS coroutines are GUARANTEED to pass the
# `self._connection is not None` fast-path check before any of them completes and assigns.
# That forces the interleave deterministically instead of hoping for it — the fixture must
# create the race, not wait for one (§5's whole lesson: a Barrier synchronises Python, not
# the wire, and a race you did not force is a race you did not test).
_RACE_SIGNIN_DELAY_SECONDS = 0.02


def _discover_socket_owners() -> list[tuple[str, str]]:
    """Every class whose ``_ensure_connection`` CONSTRUCTS its own SDK socket.

    The property, read from the AST — not a list anyone maintains. A class that receives its
    connection (scout's subscriber) is not in this population and needs no connect lock;
    a class that opens one lazily is, and does.
    """
    owners: list[tuple[str, str]] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        module_path = (
            f"loremaster.{path.relative_to(_PACKAGE_ROOT).with_suffix('').as_posix()}".replace(
                "/", "."
            )
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not (
                    isinstance(item, ast.AsyncFunctionDef) and item.name == "_ensure_connection"
                ):
                    continue
                if any(
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name)
                    and call.func.id == "AsyncSurreal"
                    for call in ast.walk(item)
                ):
                    owners.append((module_path, node.name))
    return owners


_SOCKET_OWNERS = [
    pytest.param(module_path, class_name, id=class_name)
    for module_path, class_name in _discover_socket_owners()
]
_MIN_KNOWN_SOCKET_OWNERS = 10


@dataclass
class _SlowSigninConnection:
    """A healthy connection whose ``signin`` is slow — the race window, widened on purpose."""

    async def signin(self, credentials: dict[str, Any]) -> None:
        await _REAL_ASYNCIO_SLEEP(_RACE_SIGNIN_DELAY_SECONDS)

    async def use(self, namespace: str, database: str) -> None:
        return None

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        return []

    async def close(self) -> None:
        return None


class TestEveryConnectionOwnerOpensExactlyOneSocket:
    """**adversary P-2 — the BLOCKER hiding behind a hand-list in a neighbouring file.**"""

    def test_the_socket_owner_scan_is_not_silently_finding_nothing(self) -> None:
        owners = _discover_socket_owners()

        assert len(owners) >= _MIN_KNOWN_SOCKET_OWNERS, (
            f"the scan found only {len(owners)} classes whose `_ensure_connection` constructs "
            f"a socket ({[name for _, name in owners]}) — this pin was written against "
            f"{_MIN_KNOWN_SOCKET_OWNERS}. Either they were consolidated (good — lower this "
            f"floor deliberately, in a diff a reviewer can see) or the SCANNER broke and the "
            f"pin below just went vacuously green."
        )

    @pytest.mark.parametrize(("module_path", "class_name"), _SOCKET_OWNERS)
    async def test_concurrent_first_callers_open_exactly_ONE_socket(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, class_name: str
    ) -> None:
        """GREEN today, x10 — this is a REMOVED-BEHAVIOUR pin, and the behaviour it guards is
        the double-checked connect lock the wave rewrites in all ten owners.

        The wrong build (the adversary's `W7b`): drop the lock in the seven owners no pin
        covers. Every concurrent first-caller opens its own socket; N−1 are abandoned and N
        signins are burned against the server. Contract 342/342, full suite byte-identical to
        correct.
        """
        opened = 0

        def _factory(url: str) -> Any:
            nonlocal opened
            opened += 1
            return _SlowSigninConnection()

        module = importlib.import_module(module_path)
        monkeypatch.setattr(module, "AsyncSurreal", _factory)
        instance = _construct(getattr(module, class_name))

        connections = await asyncio.gather(
            *(instance._ensure_connection() for _ in range(_RACE_CALLERS))
        )

        assert opened == 1, (
            f"{class_name} ({module_path}) opened {opened} sockets for {_RACE_CALLERS} "
            f"concurrent FIRST callers. Its `_ensure_connection` has lost the double-checked "
            f"connect lock: every caller passes the `self._connection is not None` check "
            f"before any of them finishes connecting and assigns, so each opens its own — "
            f"{opened - 1} of them are then abandoned, and {opened} signins are burned. The "
            f"only pin that ever covered this was a HAND-LIST of three, in another file, "
            f"written before seven of these owners existed."
        )
        assert len({id(connection) for connection in connections}) == 1, (
            f"{class_name}'s concurrent first-callers were handed DIFFERENT connection "
            f"objects — the cached handle is not shared, so the lock (if any) is not "
            f"publishing its result"
        )
        assert instance._connection is connections[0]


# ---------------------------------------------------------------------------
# 8c. NO GUARDED-CAS HANDLER MAY REINTERPRET EXHAUSTED CONTENTION.  (adversary P-3, BLOCKER)
#
# Item B fixes ONE door — `briefs._relate_briefed`, the one that had the bug. **The package
# has FOUR.** Each catches `SurrealStoreError`, RE-READS the row, and reports an
# idempotent/lost-race outcome from what it finds. That inference is sound for a DOMAIN
# rejection (the row is really there) and a LIE for exhausted contention (our write never
# committed and we know nothing).
#
#     briefs._relate_briefed   -> "already_acked, via=<a racer's>"   guard MISSING (item B)
#     findings._transition     -> IllegalTransitionError             guard present
#     tasks.transition         -> IllegalTransitionError             guard present
#     tasks.supersede_task     -> "already superseded by someone else"   guard present,
#                                                                     PINNED BY NOTHING
#
# Delete `tasks.supersede_task`'s guard alone and the build scores 342/342 here and is
# byte-identical to correct across the whole suite: an exhausted supersede is re-read and
# reported as *"already superseded by <someone>"* — a claim about another agent's action that
# **never happened**. Item B's exact defect, through the door item B does not quantify over.
#
# THE INVARIANT IS THEREFORE THE UNIVERSAL, not the instance (the PR93 quantifier law):
#
#     ∀ guarded-CAS handlers: exhausted contention propagates UNREAD.
#
# And the population is DISCOVERED, by the property that MAKES a handler a guarded CAS —
# `except SurrealStoreError` whose body RE-READS state (`await self._select…`). A fifth door
# is pinned the day it is written, by nobody's memory.
# ---------------------------------------------------------------------------

_GUARDED_CAS_GUARD = "TxnContentionExhaustedError"
_GUARDED_CAS_RE_READ = "_select"


def _discover_guarded_cas_handlers() -> dict[str, tuple[str, int, bool]]:
    """Every guarded-CAS door: ``{"<module>::<function>": (file, lineno, has_guard)}``.

    The PROPERTY, from the AST: an ``except SurrealStoreError`` handler whose body re-reads
    state. ``has_guard`` is whether the SAME ``try`` also catches
    :class:`TxnContentionExhaustedError` — which, because ``except`` clauses are tried in
    order and the typed error SUBCLASSES ``SurrealStoreError``, is the only thing standing
    between "exhausted" and "re-read and reinterpreted".
    """
    doors: dict[str, tuple[str, int, bool]] = {}
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        key = path.relative_to(_PACKAGE_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents: dict[int, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[id(child)] = parent
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            caught = {
                handler.type.id
                for handler in node.handlers
                if isinstance(handler.type, ast.Name)
            }
            for handler in node.handlers:
                if not (
                    isinstance(handler.type, ast.Name)
                    and handler.type.id == "SurrealStoreError"
                ):
                    continue
                re_reads = any(
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr.startswith(_GUARDED_CAS_RE_READ)
                    for call in ast.walk(handler)
                )
                if not re_reads:
                    continue
                scope = _enclosing_callable(handler, parents)
                where = getattr(scope, "name", "<lambda>") if scope else "<module>"
                doors[f"{key}::{where}"] = (key, handler.lineno, _GUARDED_CAS_GUARD in caught)
    return doors


# The canonical set of guarded-CAS doors, as an EXACT SET (the house idiom — one list, one
# place). The value is what each door REPORTS when it reinterprets a failure, i.e. the lie it
# tells if exhausted contention reaches it.
_GUARDED_CAS_DOORS = {
    "briefs.py::_relate_briefed": "already_acked=True with a racer's `via`",
    "findings.py::_transition": "IllegalTransitionError — a lost transition race",
    "tasks.py::transition": "IllegalTransitionError — a lost transition race",
    "tasks.py::supersede_task": "IllegalTransitionError — 'already superseded by someone else'",
}


class TestNoGuardedCasHandlerReinterpretsExhaustedContention:
    """**adversary P-3 — the BLOCKER item B left standing in three other doors.**"""

    def test_the_door_enumeration_matches_the_canonical_set(self) -> None:
        """EXACT SET. A new guarded-CAS handler — a fifth door — must be a DELIBERATE entry
        here, in a diff a reviewer can see, not something that slips in unpinned.
        """
        found = _discover_guarded_cas_handlers()

        assert found.keys() == _GUARDED_CAS_DOORS.keys(), (
            f"the set of guarded-CAS doors has changed.\n"
            f"  doors with NO entry in the canonical set: "
            f"{sorted(found.keys() - _GUARDED_CAS_DOORS.keys())}\n"
            f"  entries naming a door that no longer exists: "
            f"{sorted(_GUARDED_CAS_DOORS.keys() - found.keys())}\n\n"
            f"A guarded-CAS handler re-reads state after a rollback and reports a lost-race "
            f"or idempotent outcome from what it finds. That inference is TRUE for a domain "
            f"rejection and a LIE for exhausted contention. Every one of them needs the "
            f"`except {_GUARDED_CAS_GUARD}: raise` guard ABOVE it — so every one of them has "
            f"to be known about."
        )

    @pytest.mark.parametrize("door", sorted(_GUARDED_CAS_DOORS))
    def test_every_door_guards_the_typed_error_ABOVE_its_rollback_handler(self, door: str) -> None:
        """RED today on `briefs.py::_relate_briefed` (item B's defect, seen structurally).

        ``TxnContentionExhaustedError`` SUBCLASSES ``SurrealStoreError`` and ``except``
        clauses are tried IN ORDER — so without a clause naming the typed error first, an
        exhausted write lands in the rollback handler and is re-read as a lost race. This is
        the structural half; the behavioural half is below, and neither is sufficient alone
        (a guard can be present and still guard nothing — see the `W4-ACKSWALLOW` build).
        """
        found = _discover_guarded_cas_handlers()
        assert door in found, f"the canonical door {door!r} was not found by the scan"
        module_file, lineno, has_guard = found[door]

        assert has_guard, (
            f"{module_file}:{lineno} ({door}) re-reads state after a SurrealStoreError and "
            f"reports {_GUARDED_CAS_DOORS[door]} — with NO `except {_GUARDED_CAS_GUARD}` "
            f"above it.\n\n"
            f"The typed error SUBCLASSES SurrealStoreError, so exhausted contention lands "
            f"HERE, and this handler then tells the caller a story about a race that never "
            f"happened: our write never committed, and what it re-reads is somebody else's "
            f"state (or none at all). `findings._transition` and `tasks.transition` carry the "
            f"guard, with a four-line comment explaining exactly this."
        )


class TestEveryGuardedCasDoorPropagatesExhaustionUNREAD:
    """The BEHAVIOURAL half of P-3 — because a guard can exist and guard NOTHING.

    The adversary's `W4-ACKSWALLOW` build names the typed error in an `except` clause and
    then re-reads and reports the racer's edge anyway. It satisfies any structural scan. The
    only thing that kills it is driving the door and asserting the state was **never
    re-selected**.
    """

    async def test_the_brief_ack_door(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Door 1 — the one item B fixes. RED today (it returns ``already_acked=True``)."""
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _AckConnection(
            relate_error=_conflict_error(), existing_edge_via=_ACK_RACERS_VIA
        )
        ledger = _ledger_on(connection)
        re_reads: list[str] = []
        real_select = ledger._select_briefed_edge

        async def _spy(**kwargs: Any) -> Any:
            re_reads.append("select")
            return await real_select(**kwargs)

        monkeypatch.setattr(ledger, "_select_briefed_edge", _spy)

        with pytest.raises(TxnContentionExhaustedError):
            await _ack_through(ledger)

        assert not re_reads, (
            "the ack door RE-READ the edge after exhausted contention. Even a handler that "
            "then re-raises has already asked the store a question whose answer it must not "
            "act on — and the build that acts on it (`W4-ACKSWALLOW`: name the type, re-read "
            "anyway, return the racer's `via`) passes every structural scan ever written."
        )

    @pytest.mark.parametrize(
        ("module_name", "door"),
        [
            pytest.param("findings", "findings.py::_transition", id="findings-transition"),
            pytest.param("tasks", "tasks.py::transition", id="tasks-transition"),
            pytest.param("tasks", "tasks.py::supersede_task", id="TASKS-SUPERSEDE-unpinned"),
        ],
    )
    def test_the_transactional_doors_never_re_read_after_exhaustion(
        self, module_name: str, door: str
    ) -> None:
        """Doors 2-4, structurally: the guard must RE-RAISE, not re-read.

        Driven from the AST rather than through a live ledger because the property is about
        the SHAPE of the handler chain — `except TxnContentionExhaustedError` must contain
        nothing but a bare `raise`. A guard whose body re-reads (`W4-ACKSWALLOW`'s shape,
        transplanted to these doors) is a guard that guards nothing, and it is exactly what a
        builder writes when it "handles" the new type by copying the handler below it.

        ``tasks.supersede_task`` is the one the adversary stripped: 342/342, full suite
        byte-identical, and an exhausted supersede reported as *"already superseded by
        someone else"*.
        """
        source = (_PACKAGE_ROOT / f"{module_name}.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        function_name = door.split("::")[1]

        guards: list[ast.ExceptHandler] = []
        for node in ast.walk(tree):
            if not (isinstance(node, ast.AsyncFunctionDef) and node.name == function_name):
                continue
            for inner in ast.walk(node):
                if not isinstance(inner, ast.Try):
                    continue
                guards.extend(
                    handler
                    for handler in inner.handlers
                    if isinstance(handler.type, ast.Name)
                    and handler.type.id == _GUARDED_CAS_GUARD
                )

        assert guards, (
            f"{door} has no `except {_GUARDED_CAS_GUARD}` clause at all — exhausted "
            f"contention falls into its rollback handler and is reinterpreted as a lost race"
        )
        for guard in guards:
            body = [statement for statement in guard.body if not isinstance(statement, ast.Pass)]
            assert all(isinstance(statement, ast.Raise) for statement in body), (
                f"{door}'s `except {_GUARDED_CAS_GUARD}` does something OTHER than re-raise "
                f"(line {guard.lineno}). A guard that re-reads the row is a guard that guards "
                f"nothing: exhausted contention means our write never committed and whatever "
                f"is in the store belongs to somebody else. Re-raise, untouched."
            )
            assert all(
                cast("ast.Raise", statement).exc is None for statement in body
            ), (
                f"{door}'s guard re-raises a DIFFERENT exception (line {guard.lineno}) — the "
                f"caller must see the typed contention error, which is the only thing that "
                f"tells it 'nobody knows who holds this row'"
            )


# ---------------------------------------------------------------------------
# 8d. THE CONNECTION IS RE-ACQUIRED ON EVERY ATTEMPT.  (adversary R-3, latent)
#
# `_query`'s attempt body calls `await self._ensure_connection()` INSIDE the retried callable.
# That is load-bearing the moment a retried attempt can follow a dropped handle: a build that
# hoists the acquire OUT of the body (the obvious "why look it up every time?" tidy-up, and
# `run_query`'s signature makes it a one-line move) would re-run the statement on a connection
# it has already closed.
#
# LATENT, NOT LIVE, and said plainly: today only the SIGNAL is retried, and a transport fault
# is never a signal — so the dropped handle is never followed by a retry. The pin costs one
# test and stops the day someone widens what gets retried from being the day this becomes a
# use-after-close.
# ---------------------------------------------------------------------------


class TestTheConnectionIsReAcquiredOnEveryAttempt:
    """R-3 (contract adversary): the acquire lives INSIDE the attempt body."""

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_every_retry_re_acquires_the_connection(
        self, monkeypatch: pytest.MonkeyPatch, module_path: str, seam: type
    ) -> None:
        _silence_sleep(monkeypatch)
        connection = _ConflictingConnection(conflicts=3, rows=[{"next": 4}])
        instance = _seam_on(seam, connection)
        acquires = 0
        real_acquire = instance._ensure_connection

        async def _counting_acquire() -> Any:
            nonlocal acquires
            acquires += 1
            return await real_acquire()

        monkeypatch.setattr(instance, "_ensure_connection", _counting_acquire)

        await instance._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        assert connection.calls == 4, "the fixture did not retry — nothing is proven"
        assert acquires == connection.calls, (
            f"{seam.__name__}._query ({module_path}) acquired the connection {acquires} "
            f"time(s) across {connection.calls} engine attempts. The acquire must live INSIDE "
            f"the retried body: a build that hoists it out re-runs the statement on a handle a "
            f"previous attempt may have DROPPED (a use-after-close). Latent today — only the "
            f"conflict SIGNAL is retried, and a transport fault is never one — which is "
            f"exactly why it is cheap to pin now and expensive to discover later."
        )


# ===========================================================================
# 9. THE POLISH WAVE — what the cold audit and the SECOND blind reader found in the BUILT
#    tree. The built tree is now the reference: GREEN means the behaviour exists; RED means
#    the builder still owes it.
# ===========================================================================


# ---------------------------------------------------------------------------
# 9a. THE EXHAUSTION RECORD MUST SAY WHO, WHERE, AND WHAT THE ENGINE SAID.
#     (blindreader-dry-2 F1 / audit-fix-1 B3 — expected RED)
#
# The raised error says: *"…; see the server log for the full engine detail"*.
#
# **The server log contains nothing.** `run_query`'s conflict branch raises the signal
# WITHOUT logging (correct — a line per retried attempt would be a log storm; contention is
# the normal case at 30% of statements at 16-way), and the driver's one terminal record
# carries only `attempts` and `elapsed_seconds`. So an exhausted `brief_publish` mint leaves
# the operator with:
#
#     store.retry.exhausted {attempts: 64, elapsed_seconds: 2.1}   from loremaster.store._txn
#     TxnContentionExhaustedError: SurrealDB operation gave up … see the server log …
#
# — a record attributable to NONE of the possible emitters (the ten `_query` seams, scout's
# query seam, `bootstrap_session`), naming no server, carrying no engine text. **The hint
# points at a log
# that does not exist**, which makes ledger #31's contract ("raised message generic, FULL
# detail server-side") unsatisfiable on this path.
#
# AND THE ASYMMETRY IS THE PROOF IT IS AN OVERSIGHT, NOT A CHOICE: `execute_transaction`
# DELIBERATELY kept its receipt — it stashes `last_conflict` and calls `_log_rollback` on the
# way out, for exactly this reason. The ten single-statement seams got no counterpart, and
# nothing in the diff says the omission is intentional.
#
# STILL EXACTLY ONE DRIVER RECORD. The exactly-once pin above keeps every bit of its force;
# it simply gains required keys. HOW the driver comes to know them is the builder's business
# (the signal can carry the original error; the driver can take optional `label`/`url`).
# ---------------------------------------------------------------------------

# The keys the ONE exhaustion record must carry, beyond `attempts`/`elapsed_seconds`.
# `engine_error` is the house name for "what the engine actually said" (it is what every
# seam's rejection record uses) — the same fact, on the path where it is currently lost.
_EXHAUSTION_ATTRIBUTION_KEYS = ("label", "url", "engine_error")


class TestTheExhaustionRecordIsATTRIBUTABLE:
    """**blindreader-dry-2 F1 / audit-fix-1 B3.** One record — but a record that says WHICH
    seam, against WHICH server, and WHAT THE ENGINE SAID.
    """

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_the_exhaustion_record_names_the_seam_the_server_and_the_engine_text(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        module_path: str,
        seam: type,
    ) -> None:
        """RED today, x10: the record carries `attempts` and `elapsed_seconds` and nothing else.

        The `label` is what makes it attributable (it is the seam's own canonical event name —
        the string an operator already greps). The `url` names the server. The `engine_error`
        is the detail the raised message promises and no log currently holds.
        """
        _silence_sleep(monkeypatch)
        caplog.set_level(logging.DEBUG)
        connection = _ConflictingConnection(conflicts=None)

        with pytest.raises(TxnContentionExhaustedError):
            await _seam_on(seam, connection)._query(_MINT_STATEMENT, {"name": _WAVE_NAME})

        exhausted = _records(caplog, _EXHAUSTION_EVENT)
        assert len(exhausted) == 1, (
            f"{seam.__name__} emitted {len(exhausted)} `{_EXHAUSTION_EVENT}` record(s) — the "
            f"exactly-once rule is unchanged; this pin only requires the ONE record to say more"
        )
        record = exhausted[0]
        missing = [
            key for key in _EXHAUSTION_ATTRIBUTION_KEYS if getattr(record, key, None) is None
        ]
        assert not missing, (
            f"{seam.__name__}._query ({module_path}) exhausted its retry budget and its ONE "
            f"log record is missing {missing}.\n\n"
            f"The raised error tells the operator to '{_SERVER_LOG_HINT_TEXT}'. The record it "
            f"points at carries only the attempt count and the elapsed time — no seam, no "
            f"server, no engine text. It cannot be attributed to ANY of the possible "
            f"emitters — every caller into the driver labels its own exhaustion, save "
            f"`execute_transaction`, which is attributed by `_log_rollback` instead — "
            f"so the hint points at a log "
            f"that does not exist and ledger #31's contract (generic message, FULL detail "
            f"server-side) is unsatisfiable on this path.\n\n"
            f"`execute_transaction` KEPT its receipt on exhaustion (it stashes `last_conflict` "
            f"and logs the rollback detail on the way out) — for exactly this reason. The ten "
            f"single-statement seams got no counterpart. That asymmetry is the defect."
        )
        assert str(getattr(record, "label", "")) == _SEAM_REJECTION_EVENTS[seam.__name__], (
            f"{seam.__name__}'s exhaustion record is labelled "
            f"{getattr(record, 'label', None)!r} — it must carry the seam's OWN canonical "
            f"rejection event, which is the string an operator already greps for"
        )
        assert _LIVE_CONFLICT_TEXT in str(getattr(record, "engine_error", "")), (
            f"{seam.__name__}'s exhaustion record carries an `engine_error` that is not the "
            f"engine's own conflict text. The point of the key is the DETAIL the raised "
            f"message deliberately withholds (ledger #31) — a placeholder is worse than "
            f"nothing, because it makes the log look complete."
        )
        assert _LIVE_CONFLICT_TEXT not in str(
            getattr(record, "message", "")
        ) and _SENSITIVE_MARKER not in str(getattr(record, "url", "")), (
            "ledger #31: the raw engine text belongs in the structured `extra`, server-side — "
            "never interpolated into the event name"
        )


# ---------------------------------------------------------------------------
# 9b. SCOUT'S FAILED CONNECT MUST NOT LEAK ITS SOCKET — AND MUST NOT CHANGE TYPE.
#     (blindreader-dry-2 F7 / audit-fix-1 B1 — expected RED)
#
# `_open_command_connection`: `AsyncSurreal(url)` -> `signin` -> `bootstrap_session` ->
# `return`. **No try/except, no close.** On ANY failure the half-open socket is abandoned;
# `run()`'s ladder backs off and constructs a NEW one — forever.
#
# The wave added `await self._safe_close(connection)` to the new exhaustion handler in ALL
# TEN ledger seams and gave **the one bootstrap owner it also rewrote no cleanup at all.**
# The fate is unchanged from HEAD, so it is not a regression — but the wave now makes each
# failed connect take *seconds* (the bootstrap retries), and the subscriber retries
# indefinitely, so under sustained store contention this is an **unbounded socket leak in a
# long-running process.**
#
# ⚠ THE TWO HALVES ARE PINNED IN ONE TEST ON PURPOSE. "Close the socket" is one line, and the
# obvious way to write it — `try: … except Exception: await connection.close(); raise` — is
# also the obvious place to accidentally WRAP the error, which is `W1-SCOUTKILL`: scout's
# ladder catches RAW SDK types, and a `SurrealConnectionError` (a `RuntimeError`) flies
# straight past it and kills the command channel. A test that pinned only the close would
# green-light the fix that reintroduces the blocker. **Closed AND raw, or neither.**
# ---------------------------------------------------------------------------


@dataclass
class _ClosingBootstrapFailure:
    """A connection whose bootstrap fails with ``error`` forever, counting its own closes."""

    error: BaseException
    closes: int = field(default=0, init=False)
    attempts: int = field(default=0, init=False)

    def _fail(self) -> None:
        self.attempts += 1
        if self.attempts > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError("unbounded retry in scout's bootstrap")
        raise self.error

    async def signin(self, credentials: dict[str, Any]) -> None:
        return None

    async def use(self, namespace: str, database: str) -> None:
        self._fail()

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        self._fail()

    async def close(self) -> None:
        self.closes += 1


# Every way scout's bootstrap can fail, and the RAW type its reconnect ladder must still see.
_SCOUT_BOOTSTRAP_FATES = [
    pytest.param(lambda: OSError("connection refused"), OSError, id="transport-fault"),
    pytest.param(
        lambda: InternalError(ErrorKind.INTERNAL, _LIVE_ASSERT_TEXT),
        InternalError,
        id="domain-rejection",
    ),
    pytest.param(_conflict_error, TxnContentionExhaustedError, id="EXHAUSTED-CONTENTION"),
]


class TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType:
    """**blindreader-dry-2 F7 / audit-fix-1 B1** — and the trap that comes with the fix."""

    @pytest.mark.parametrize(("build_error", "expected_type"), _SCOUT_BOOTSTRAP_FATES)
    async def test_the_socket_is_closed_and_the_raw_type_survives(
        self,
        monkeypatch: pytest.MonkeyPatch,
        build_error: Callable[[], BaseException],
        expected_type: type,
    ) -> None:
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)  # a sustained conflict exhausts at the floor
        connection = _ClosingBootstrapFailure(error=build_error())
        monkeypatch.setattr(scout_module, "AsyncSurreal", lambda url: connection)

        with pytest.raises(expected_type) as exc_info:
            await scout_module._open_command_connection(
                url="ws://127.0.0.1:19555/rpc",
                namespace=_CTOR_VALUES["namespace"],
                database=_CTOR_VALUES["database"],
                user=_CTOR_VALUES["user"],
                password=_CTOR_VALUES["password"],
            )

        assert connection.attempts >= 1, "the fixture never reached the bootstrap"
        assert connection.closes >= 1, (
            f"scout's `_open_command_connection` LEAKED its socket on a failed bootstrap "
            f"({type(exc_info.value).__name__}). `run()`'s ladder backs off and constructs a "
            f"NEW connection — forever — so under sustained store contention this leaks one "
            f"socket per failed connect in a long-running process. All TEN ledger seams close "
            f"theirs; the one bootstrap owner the wave also rewrote closes nothing."
        )
        assert not isinstance(exc_info.value, SurrealConnectionError), (
            f"scout's failed connect raised {type(exc_info.value).__name__} — a "
            f"SurrealConnectionError (a RuntimeError). **That is W1-SCOUTKILL.** `run()`'s "
            f"ladder catches RAW SDK types (`_CONNECTION_ERRORS` + KeyError + "
            f"TxnContentionExhaustedError); a wrap flies straight past it and the command "
            f"channel dies with no backoff and no reconnect. Adding the close is one line, and "
            f"the obvious way to write it (`except Exception: await connection.close(); raise`) "
            f"is also the obvious place to wrap by accident. **Closed AND raw, or neither.**"
        )


# ---------------------------------------------------------------------------
# 9c. THE BOOTSTRAP SHARES ONE WALL-CLOCK BUDGET.
#     (blindreader-dry-2 F2 / audit-fix-1 B2 — expected RED)
#
# `bootstrap_session` makes THREE separate `retry_on_conflict` calls (DEFINE NAMESPACE ->
# use() -> DEFINE DATABASE), each taking the module DEFAULT deadline. The budget is therefore
# per-STATEMENT, not per-BOOTSTRAP: **3 x 2.0s**, where a reader of
# `_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS` computes 2.0s.
#
# And all of it runs inside the caller's held `async with self._connect_lock` — so one
# contended virgin first-connect can hold the connect lock for SECONDS while every other
# coroutine in the process blocks in `_ensure_connection`. At HEAD the bootstrap had ZERO
# retry and failed in milliseconds; "what is held across a backoff" is exactly what changed.
#
# PINNED STRUCTURALLY, NEVER BY WALL-CLOCK. A timing assertion here would be a sleep-based
# flake in a suite that already paid for one (§5). The observable is the `deadline_seconds`
# each `retry_on_conflict` call RECEIVES: one composed, shrinking budget — not three
# independent defaults.
#
# The attempt FLOOR still protects each statement (`_MAX_TXN_CONFLICT_ATTEMPTS` guarantees 5
# attempts regardless of wall time — audit-102 B1), so composing the budget cannot starve the
# third statement of its retries. That is why this is safe to demand.
# ---------------------------------------------------------------------------


class TestTheBootstrapSharesOneDeadline:
    """**blindreader-dry-2 F2 / audit-fix-1 B2** — three statements, ONE budget."""

    async def test_the_three_bootstrap_statements_compose_one_budget(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RED today: all three calls pass NO deadline, so each silently takes the module
        default and the bootstrap's real budget is 3x what any reader would compute.
        """
        _silence_sleep(monkeypatch)
        real = _driver()
        deadlines: list[float | None] = []

        async def _spy(attempt: Any, **kwargs: Any) -> Any:
            deadlines.append(kwargs.get("deadline_seconds"))
            return await real(attempt, **kwargs)

        monkeypatch.setattr(txn_module, "retry_on_conflict", _spy)
        bootstrap = _shared("bootstrap_session")

        await bootstrap(
            cast("Any", _BootstrapScriptedConnection(error=_conflict_error(), failures=0)),
            _CTOR_VALUES["namespace"],
            _CTOR_VALUES["database"],
            # #151: `url` is REQUIRED and keyword-only. It plays no part in THIS pin (which
            # reads only the deadlines each driver call receives) but the call does not bind
            # without it — see `TestBootstrapSessionRequiresItsUrl` in test_surreal_harness.py.
            url=_CTOR_VALUES["url"],
        )

        assert len(deadlines) == 3, (
            f"the bootstrap made {len(deadlines)} driver call(s), not 3 (DEFINE NAMESPACE, "
            f"use(), DEFINE DATABASE) — the fixture no longer describes the code"
        )
        default = txn_module._TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS
        assert all(deadline is not None for deadline in deadlines), (
            f"the bootstrap's three statements pass deadline_seconds={deadlines} — i.e. NONE, "
            f"so each takes the module default ({default}s) on its own. The bootstrap's real "
            f"wall-clock budget is therefore 3 x {default}s = {3 * default}s, while a reader of "
            f"_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS computes {default}s. All of it runs inside "
            f"the caller's HELD `_connect_lock`, so one contended virgin first-connect blocks "
            f"every other coroutine in the process for that whole time. Compose ONE budget "
            f"across the three statements and pass the REMAINDER to each.\n\n"
            f"(The attempt FLOOR still guarantees each statement its {_MAX_TXN_CONFLICT_ATTEMPTS} "
            f"attempts regardless of wall time, so a shared budget cannot starve the third.)"
        )
        # STRICT, BOTH OF THEM — and the reason is written here because the non-strict version
        # of these two lines waved through the EXACT build this pin exists to catch
        # (audit-polish-1 §P2: three independent 2.0s budgets scored 399/399 + mypy + ruff).
        #
        #     budgets[0] <= default                     # 2.0 <= 2.0     -> True
        #     budgets == sorted(budgets, reverse=True)  # [2.0,2.0,2.0]  IS non-increasing
        #
        # **THE PIN'S OWN FAILURE MESSAGE NAMED THE BUILD IT COULD NOT SEE** — "three equal
        # values is three independent budgets wearing a parameter" — while the code below it
        # performed a check that admits exactly those three equal values. English beside the
        # code, saying what the code does, and wrong: this repo's most-shipped defect class,
        # committed by the author writing the pin against it. A message that describes a
        # STRICTER check than the assertion performs is not a typo; it is a false gate.
        #
        # The margins are REAL, not luck: a composed budget re-reads the clock per statement,
        # and `_silence_sleep` patches `asyncio.sleep`, NOT `time.monotonic`. Measured on the
        # real build: [1.99999507, 1.99999068, 1.99998763] — strictly decreasing, ~3-4µs apart,
        # 20/20 consecutive green.
        budgets = cast("list[float]", deadlines)
        assert budgets[0] < default, (
            f"the bootstrap's FIRST statement was given {budgets[0]}s — the WHOLE bootstrap's "
            f"budget is {default}s, so no single statement inside it may be handed the full "
            f"amount. Handing each of the three the default IS the defect: three independent "
            f"budgets, 3 x {default}s of wall-clock held under `_connect_lock`."
        )
        assert all(
            earlier > later
            for earlier, later in zip(budgets[:-1], budgets[1:], strict=True)
        ), (
            f"the bootstrap's three deadlines are {budgets} — they must be STRICTLY "
            f"DECREASING. A shared wall-clock budget only ever shrinks: each statement gets "
            f"what is LEFT of it, and time passes between them. Three EQUAL values is three "
            f"independent budgets wearing a parameter — which is the whole defect, and which "
            f"a merely non-increasing check cannot tell apart from the real thing."
        )


# ---------------------------------------------------------------------------
# 10. EVERY CALL INTO THE RETRY DRIVER IS ATTRIBUTABLE.  (finding #151, R3)
#
# §9a made the driver's exhaustion record carry `label`/`url`/`engine_error` — but it
# gates all three on `label is not None`, so the record is only as attributable as the
# CALL SITE chose to be. `bootstrap_session` chose nothing, for three statements, and the
# result was a raised message promising "see the server log for the full engine detail"
# over a record holding `{attempts, elapsed_seconds}`. **The behaviour pin and the
# structural pin are not redundant: §9a proves the driver CAN attribute; this proves every
# caller DOES.**
#
# DENY BY DEFAULT, ALLOWLIST THE SAFE. This repo's instrument lesson is a table of six
# gates defeated by enumerating what is FORBIDDEN. So this one does not hunt for known-bad
# call sites: it requires `label=` at EVERY call into the driver and carries a small,
# EVIDENCE-BACKED allowlist of sites that are attributable by another mechanism. An
# exemption states the mechanism; "it writes no row" is not evidence, and neither is "it
# has always been that way".
# ---------------------------------------------------------------------------

_RETRY_DRIVER_NAME = "retry_on_conflict"
# The keyword each gate requires at its call sites. Named constants, not literals at the
# call: both gates read them, and the mutation proof that the two scanners SHARE one
# implementation moves these and requires both to change behaviour together.
_RETRY_ATTRIBUTION_KEYWORD = "label"
_SESSION_BOOTSTRAP_NAME = "bootstrap_session"
_BOOTSTRAP_URL_KEYWORD = "url"

# Call sites that reach the driver WITHOUT a label and are attributable anyway. Each entry
# is (module path relative to the package root, innermost enclosing function) -> the
# EVIDENCE and the NUMBER of unlabelled calls that evidence covers. A site not listed here
# must pass `label=`.
#
# ⚠ THE COUNT IS NOT BOOKKEEPING — IT IS THE EXEMPTION'S SCOPE (adversary MP4, wrong build
# D3). The first version of this allowlist keyed on `(module, enclosing_function)` alone,
# which exempts a FUNCTION rather than a CALL. Measured: an unreachable
# `await retry_on_conflict(lambda: None)` added inside `execute_transaction` — zero runtime
# effect, so only this gate could ever object — passed the entire contract **489/0**. One
# evidence-backed exemption silently pre-approved every unlabelled call any future author
# writes anywhere in that body, and the evidence cited (`_log_rollback` runs on the way out)
# is true of the ORIGINAL call and says nothing whatever about a new one.
#
# A COUNT, not a line number, deliberately: a lineno makes the gate go red on every
# unrelated edit above it, and a gate that cries wolf is a gate that gets switched off
# (CLAUDE.md's threat-model rule). The count changes only when the number of unlabelled
# calls in that body changes — which is exactly the event that needs a human to re-read the
# evidence and decide whether it still covers what is there.
_Exemption = tuple[str, int]

_ATTRIBUTED_BY_ANOTHER_MECHANISM: dict[tuple[str, str], _Exemption] = {
    ("store/_txn.py", "execute_transaction"): (
        (
            "calls `_log_rollback` on the way out (_txn.py:789-801), which logs the failing "
            "statement's INDEX, the full engine result and every failed statement — strictly "
            "more detail than a label. This is the asymmetry #151 measured: the transactional "
            "caller kept its receipt, the bootstrap had none."
        ),
        1,
    ),
}
# ⚠ TWO SCOUT ENTRIES USED TO LIVE HERE AND WERE DELETED DELIBERATELY (§10f, the cold
# audit's NO-GO — REPORT-audit-151-cold.md §FINDING). `_consume_live`'s evidence claimed
# the swallowed exception carried "the engine's text ... on the traceback"; that clause was
# MEASURED FALSE (the driver raises the exhaustion error BARE, so `__cause__` is `None`),
# and nothing here could ever have caught it — this gate reads an evidence string for
# PRESENCE, never for TRUTH. The operator ruled the aspiration made TRUE rather than the
# clause reworded: both seams now pass `label=`, so both are ordinary attributed callers
# with no exemption to justify. Do not re-add them; §10f pins what replaced them.

# Every call site the scan finds today. A FLOOR, not an equality: a new labelled caller
# must not have to edit this number, but a scan that suddenly finds FEWER sites has gone
# blind and every pin below it would go vacuously green.
_MIN_KNOWN_RETRY_DRIVER_CALL_SITES = 8


def _call_sites_in(source: str, callee: str, required_keyword: str) -> list[tuple[int, str, bool]]:
    """Every call to ``callee`` in ``source`` — ``(lineno, enclosing, has_required_keyword)``.

    ONE IMPLEMENTATION, TWO KEYS (CLAUDE.md's DRY law). Both attribution gates in this file
    ask the identical structural question — *does every call to X pass Y?* — of two different
    pairs: ``(retry_on_conflict, label=)`` for R3, and ``(bootstrap_session, url=)`` for R1's
    url leg. That is a POLICY (what counts as a call site, what counts as the innermost
    enclosing function, which call shapes are in reach), and a policy shared by two callers
    is a function they call, never a pattern the second one clones. A second copy is where
    the two gates' reach silently diverges, and only one of them gets the next fix.

    ``enclosing`` is the INNERMOST enclosing function (a call inside a nested ``_attempt``
    is that function's, not its parent's), because the allowlist keys on it.

    ⚠ KEYED ON THE DRIVER'S NAME, and that bound is stated rather than hidden: this
    matcher sees ``retry_on_conflict(...)`` and ``<anything>.retry_on_conflict(...)``. It
    does NOT see a call through an import alias, a variable holding the function, or
    ``getattr``. Those are the shapes the repo's instrument-lesson table records as having
    defeated six name-keyed gates. They are accepted here because the ONE property that
    makes them reachable — a module that calls the driver at all — is already pinned
    structurally elsewhere (the seams hold `_txn.retry_on_conflict` BY IDENTITY, and no
    production module may hand-roll a bootstrap), so an aliased call would have to be
    written deliberately, by an author who knew this gate existed. The gate's threat model
    is the HONEST engineer adding a new caller, not an author routing around it.
    """
    sites: list[tuple[int, str, bool]] = []

    def visit(node: ast.AST, enclosing: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                visit(child, child.name)
                continue
            if isinstance(child, ast.Call):
                func = child.func
                name = (
                    func.id
                    if isinstance(func, ast.Name)
                    else func.attr
                    if isinstance(func, ast.Attribute)
                    else None
                )
                if name == callee:
                    sites.append(
                        (
                            child.lineno,
                            enclosing,
                            any(keyword.arg == required_keyword for keyword in child.keywords),
                        )
                    )
            visit(child, enclosing)

    visit(ast.parse(source), "<module>")
    return sites


def _retry_driver_call_sites_in(source: str) -> list[tuple[int, str, bool]]:
    """Every call into the retry driver — ``(lineno, enclosing, has_label)``. See
    :func:`_call_sites_in` for the shared policy and its stated reach bound."""
    return _call_sites_in(source, _RETRY_DRIVER_NAME, _RETRY_ATTRIBUTION_KEYWORD)


def _retry_driver_docstring() -> str:
    """The retry driver's OWN docstring, read live from the seam module's source.

    Read from ``__doc__`` rather than re-parsed so it reflects exactly what a reader of the
    running code sees; the empty string when the function somehow has none, so callers can
    assert non-emptiness as a reach control rather than crashing on ``None``."""
    return txn_module.retry_on_conflict.__doc__ or ""


def _all_retry_driver_call_sites() -> list[tuple[str, int, str, bool]]:
    """``(module, lineno, enclosing, has_label)`` for the whole production package."""
    found: list[tuple[str, int, str, bool]] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        key = path.relative_to(_PACKAGE_ROOT).as_posix()
        for lineno, enclosing, has_label in _retry_driver_call_sites_in(
            path.read_text(encoding="utf-8")
        ):
            found.append((key, lineno, enclosing, has_label))
    return found


class TestEveryCallIntoTheRetryDriverIsAttributable:
    """**FINDING #151, STRUCTURALLY.** A label is what makes the driver's one exhaustion
    record say WHO — and the driver suppresses the url and the engine text without it.
    """

    def test_the_call_site_scan_is_not_silently_finding_nothing(self) -> None:
        """**THE REACH CONTROL.** A scan that matched nothing would report a perfectly
        attributable tree forever. This is the failure mode the repo's own instrument-lesson
        table records for a runtime gate — an invariant only over the code it actually
        REACHES — hoisted to an AST scan: assert the reach, or the reach becomes the bug.
        """
        sites = _all_retry_driver_call_sites()

        assert len(sites) >= _MIN_KNOWN_RETRY_DRIVER_CALL_SITES, (
            f"the scan found {len(sites)} call(s) into `{_RETRY_DRIVER_NAME}` "
            f"({[(module, lineno) for module, lineno, _, _ in sites]}) — this contract was "
            f"written against {_MIN_KNOWN_RETRY_DRIVER_CALL_SITES}. Either callers were "
            f"consolidated (good — lower this floor deliberately, in a diff a reviewer can "
            f"see) or the SCANNER broke and the gate below just went vacuously green."
        )

    def test_every_exemption_matches_a_REAL_call_site(self) -> None:
        """A stale allowlist entry is a silent hole: it exempts nothing today and silently
        blesses whatever is written at that address tomorrow. Every exemption must be
        REACHED, so the allowlist can only shrink by accident, never grow blind.
        """
        sites = _all_retry_driver_call_sites()
        addresses = {(module, enclosing) for module, _, enclosing, _ in sites}
        stale = sorted(set(_ATTRIBUTED_BY_ANOTHER_MECHANISM) - addresses)

        assert not stale, (
            f"these allowlist entries match no call site: {stale}. An exemption for code "
            f"that no longer exists is not harmless — it pre-approves the next unlabelled "
            f"call written at that address. Delete it, or fix the address."
        )

        # THE OTHER DIRECTION, and it is the one MP4 exists for: an exemption whose COUNT
        # exceeds the unlabelled calls actually present is a budget for calls that are gone —
        # headroom nobody voted for, waiting to bless the next unlabelled call written in
        # that body. The count may only ever be EXACT.
        unlabelled_per_body: dict[tuple[str, str], int] = {}
        for module, _lineno, enclosing, has_label in sites:
            if not has_label:
                key = (module, enclosing)
                unlabelled_per_body[key] = unlabelled_per_body.get(key, 0) + 1

        overdrawn = sorted(
            (address, allowed, unlabelled_per_body.get(address, 0))
            for address, (_evidence, allowed) in _ATTRIBUTED_BY_ANOTHER_MECHANISM.items()
            if allowed > unlabelled_per_body.get(address, 0)
        )

        assert not overdrawn, (
            "these exemptions budget MORE unlabelled calls than their body contains:\n  "
            + "\n  ".join(
                f"{module}:{enclosing}() — exemption allows {allowed}, found {found}"
                for (module, enclosing), allowed, found in overdrawn
            )
            + "\n\nThe surplus is silent headroom: the next unlabelled call written there is "
            "pre-approved by a number, with no human ever re-reading the evidence. Lower "
            "the count to what is actually there."
        )

    def test_every_call_into_the_driver_passes_a_label(self) -> None:
        """RED today x3: ``bootstrap_session``'s three calls (``_txn.py:1021-1023``) pass
        neither ``label`` nor ``url``, so their exhaustion record carries only an attempt
        count and an elapsed time — over a raised message that says "see the server log for
        the full engine detail".

        Every residual site is named with ``file:line`` and its enclosing function. This
        repo's law bans "all remaining hits are X" as an output: wholesale classification
        under volume is how a found defect gets re-buried.
        """
        by_body: dict[tuple[str, str], list[int]] = {}
        for module, lineno, enclosing, has_label in _all_retry_driver_call_sites():
            if not has_label:
                by_body.setdefault((module, enclosing), []).append(lineno)

        # THE EXEMPTION IS A BUDGET, NOT A BLANKET (MP4). A body whose evidence covers ONE
        # unlabelled call and which now holds TWO reports the WHOLE group: which of them the
        # evidence was written for is exactly the question a human has to answer, and this
        # gate must not answer it by guessing.
        unattributed: list[tuple[str, int, str]] = []
        for (module, enclosing), linenos in sorted(by_body.items()):
            _evidence, allowed = _ATTRIBUTED_BY_ANOTHER_MECHANISM.get((module, enclosing), ("", 0))
            if len(linenos) > allowed:
                unattributed.extend((module, lineno, enclosing) for lineno in sorted(linenos))

        assert not unattributed, (
            "these calls into the retry driver pass no `label=`, so the driver suppresses "
            "`label`, `url` AND `engine_error` on their exhaustion record (it gates all "
            "three on `label is not None`):\n  "
            + "\n  ".join(
                f"{module}:{lineno}  in {enclosing}()" for module, lineno, enclosing in unattributed
            )
            + "\n\nIf a body above is ALREADY in `_ATTRIBUTED_BY_ANOTHER_MECHANISM`, it now "
            "holds MORE unlabelled calls than its evidence was written to cover, and every "
            "call in that body is listed: an exemption is a BUDGET for the calls its "
            "evidence actually describes, never a blanket over the function (adversary MP4 "
            "— an unreachable unlabelled call added inside an exempt body passed the whole "
            "contract 489/0). Re-read the evidence against what is now there, then either "
            "label the new call or raise the count DELIBERATELY, in a diff a reviewer sees."
            + "\n\nEach then raises 'see the server log for the full engine detail' over a "
            "record holding `{attempts, elapsed_seconds}` — a hint pointing at a log that "
            "holds nothing (finding #151, measured). Pass the caller's own canonical event "
            "name as `label=` and its RPC url as `url=`.\n\n"
            "If a site is attributable by ANOTHER mechanism, add it to "
            "`_ATTRIBUTED_BY_ANOTHER_MECHANISM` WITH THE EVIDENCE — the record it emits "
            "instead, by name and file:line. 'It writes no row' is not evidence."
        )

    def test_the_scan_SEES_an_unlabelled_call(self) -> None:
        """**POSITIVE CONTROL.** A gate that has never been shown firing is not a gate.
        Exercised on both call shapes the matcher claims to see.
        """
        source = """
async def _ensure_connection(self):
    async def _define_namespace():
        await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {self._namespace}")

    await retry_on_conflict(_define_namespace, deadline_seconds=_remaining_budget())
    await txn.retry_on_conflict(_define_database)
"""
        found = _retry_driver_call_sites_in(source)

        assert [(enclosing, has_label) for _, enclosing, has_label in found] == [
            ("_ensure_connection", False),
            ("_ensure_connection", False),
        ], (
            f"the scan saw {found} in a textbook unlabelled bootstrap. It must see BOTH the "
            f"bare call and the attribute call, and must not mistake `deadline_seconds` for "
            f"attribution — or the sites it is hunting are invisible to it."
        )

    def test_the_scan_ATTRIBUTES_a_call_to_its_INNERMOST_function(self) -> None:
        """The allowlist keys on the enclosing function, so a call inside a nested closure
        must not be credited to its parent — otherwise one exemption silently covers every
        call written anywhere inside an exempt function.
        """
        source = """
async def execute_transaction():
    async def _attempt():
        await retry_on_conflict(_inner)
    await retry_on_conflict(_attempt, label="x")
"""
        found = _retry_driver_call_sites_in(source)

        assert sorted((enclosing, has_label) for _, enclosing, has_label in found) == [
            ("_attempt", False),
            ("execute_transaction", True),
        ], (
            f"the scan reported {found}. The nested call belongs to `_attempt`, not to "
            f"`execute_transaction` — crediting it to the parent would let one allowlist "
            f"entry exempt every call inside an exempt function."
        )

    def test_the_scan_SPARES_a_labelled_call(self) -> None:
        """**NEGATIVE CONTROL.** A gate that fires on correct code gets switched off by the
        first engineer it blocks, and then nothing is watching at all.
        """
        source = """
async def run_query(*, url, label, statement):
    return await retry_on_conflict(_attempt, label=label, url=url)
"""
        found = _retry_driver_call_sites_in(source)

        assert [has_label for _, _, has_label in found] == [True], (
            f"the scan reported {found} for a correctly-attributed call — a gate that "
            f"flags `run_query`, the one caller that already does this right, is a gate "
            f"that gets deleted."
        )

    def test_the_scan_does_NOT_see_an_ALIASED_call_a_KNOWN_BOUND(self) -> None:
        """**THIS IS A KNOWN BOUND (#151), PINNED — it is not a passing gate.**

        The scan is keyed on the driver's NAME, so a call reached through an import alias,
        a variable holding the function, ``getattr``, or ``functools.partial`` is invisible
        to it. Measured across twelve call shapes: six seen (bare · attribute · in a lambda ·
        in a comprehension · class method · module level), six not (the four above plus dict
        dispatch and a decorator).

        Repo law: *an unpinned known limitation is indistinguishable from an unknown one* —
        the next engineer either rediscovers it from an outage or "helpfully" closes it and
        silently re-opens a settled trade. So the hole is asserted here, and this test goes
        RED the day someone closes it.

        **IF YOU CLOSED THIS DELIBERATELY, DELETE THIS PIN AND SAY SO IN THE SAME DIFF.**

        WHY THE HOLE IS ACCEPTED TODAY: the gate's threat model is the HONEST ENGINEER
        adding a new caller (#131 verbatim), not an author routing around it — and anyone
        who can commit here can already ship anything. Closing it means either a runtime
        guard (wrap the driver; assert every call arrives with an attributed frame), which
        per CLAUDE.md is an invariant only over code it RUNS and would need its own
        coverage-as-a-checked-variable leg, or an assignment/alias tracker, which is the
        shape that produced three REGRESSIONS the last time this repo tried it (packet 01's
        v2 image gate).

        ⚠ ONE SHAPE THE MEASUREMENT ABOVE DOES NOT ENUMERATE, AND IT FAILS SAFE
        (adversary-151b residual 4): ``retry_on_conflict(_attempt, **attribution)`` IS seen
        as a call site, but scores ``has_label=False`` — ``keyword.arg`` is ``None`` for a
        ``**`` unpacking, so no keyword can ever match ``label``. That is a FALSE POSITIVE:
        the gate is too STRICT, not too loose, and it errs toward reporting an attributed
        call as unattributed. It is recorded here rather than fixed because the safe
        direction needs no urgency and because a matcher that tried to reason about what a
        ``**`` mapping contains would be guessing — the author can simply pass ``label=``
        explicitly, which is what every caller does today.

        ⚠ ONE HONEST DISAGREEMENT, RECORDED RATHER THAN SETTLED (adversary §3-E): the
        scanner's own docstring says an aliased call "would have to be written deliberately,
        by an author who knew this gate existed." ``from ._txn import retry_on_conflict as
        _retry`` is ORDINARY Python — routinely written to dodge a name clash, by exactly
        the honest engineer the gate is declared to be for. The BOUND is accepted; that
        REASON for accepting it is too generous, and the pin does not rely on it.

        **NAMED RE-OPEN TRIGGER:** the day any production module imports the driver under an
        alias, holds it in a variable, or dispatches to it indirectly — i.e. the day
        ``test_every_call_into_the_driver_passes_a_label`` could go green on a caller that
        genuinely has no label. The reach floor cannot catch that: an aliased call is not a
        FEWER-sites signal, it is a never-was-a-site signal.
        """
        aliased = """
from ._txn import retry_on_conflict as _retry

async def _ensure_connection(self):
    await _retry(_define_namespace)
"""
        indirect = """
async def _ensure_connection(self):
    driver = txn.retry_on_conflict
    await driver(_define_namespace)
"""
        # POSITIVE CONTROL FIRST — a probe that reports "not seen" because it is broken
        # reports "not seen" for everything (CLAUDE.md: a probe needs a control).
        visible = """
async def _ensure_connection(self):
    await retry_on_conflict(_define_namespace)
"""
        assert _retry_driver_call_sites_in(visible), (
            "CONTROL FAILED: the scan cannot see even a bare `retry_on_conflict(...)` call, "
            "so the two assertions below prove nothing about aliasing — they would hold for "
            "a scanner that sees nothing at all."
        )

        assert _retry_driver_call_sites_in(aliased) == [], (
            f"the scan now SEES an aliased driver call: {_retry_driver_call_sites_in(aliased)}. "
            f"That is an IMPROVEMENT, not a failure — this pin exists so the improvement "
            f"cannot happen silently. **This is a KNOWN BOUND (#151) — the gate is "
            f"name-keyed; if you closed this deliberately, delete this pin and say so.** "
            f"Then widen `_MIN_KNOWN_RETRY_DRIVER_CALL_SITES` if the new reach found real "
            f"sites, and re-read the scanner's docstring, which still declares the bound."
        )
        assert _retry_driver_call_sites_in(indirect) == [], (
            f"the scan now SEES a call through a variable holding the driver: "
            f"{_retry_driver_call_sites_in(indirect)}. Same verdict as the aliased case "
            f"above — **KNOWN BOUND (#151), deliberately closed ⇒ delete this pin and say "
            f"so in the same diff.**"
        )


# ---------------------------------------------------------------------------
# 10a. ATTRIBUTING THE BOOTSTRAP MUST NOT CHANGE ITS DISPOSITION.
#
# `bootstrap_session` propagates EVERY failure UNWRAPPED (`_txn.py:950-963`): scout's
# reconnect ladder catches raw SDK types and `TxnContentionExhaustedError` DIRECTLY, never
# `SurrealConnectionError`. §8a pins that end-to-end through scout's real `run()` loop, and
# §7c pins each SEAM's wrap. Neither pins the helper ITSELF — so a #151 fix that added a
# `try/except` to log the label locally, and wrapped on the way out, would satisfy every
# attribution pin above and kill the command channel. This is the removed-behaviour half:
# the fix must ADD attribution and SUBTRACT nothing.
# ---------------------------------------------------------------------------


class TestAttributingTheBootstrapDoesNotChangeItsDisposition:
    """∀ the four ways a bootstrap can fail — the fate is UNCHANGED by #151's fix."""

    @pytest.mark.parametrize(("build_error", "is_retryable"), _BOOTSTRAP_FAILURE_FATES)
    async def test_bootstrap_session_propagates_every_failure_UNWRAPPED(
        self,
        monkeypatch: pytest.MonkeyPatch,
        build_error: Callable[[], BaseException],
        is_retryable: bool,
    ) -> None:
        """RED today x4 — but for the PLUMBING, not the property: the call below passes
        ``url=``, which ``bootstrap_session`` does not yet accept, so all four fates die on
        a ``TypeError`` before any disposition is exercised. Once the signature lands, this
        becomes a pure NON-REGRESSION pin: it goes green on a fix that only ADDS
        attribution, and red on one that also gave the helper a disposition of its own.

        Stated because the distinction is load-bearing: a pin that is red today for a
        reason OTHER than the property it names cannot demonstrate that property, and its
        author is the one person who will never notice (the C-DEF class, CLAUDE.md). The
        mutation proof for the property itself is therefore owed AFTER the signature
        change, and is recorded as such in REPORT-contract-151.md.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)  # the floor governs: exhaust in 5 attempts
        raised = build_error()
        connection = _BootstrapFailingConnection(error=raised)

        with pytest.raises(BaseException) as exc_info:  # noqa: PT011 — the TYPE is the assertion
            await _shared("bootstrap_session")(
                cast("Any", connection),
                _CTOR_VALUES["namespace"],
                _CTOR_VALUES["database"],
                url=_CTOR_VALUES["url"],
            )

        expected = TxnContentionExhaustedError if is_retryable else type(raised)
        assert type(exc_info.value) is expected, (
            f"`bootstrap_session` raised {type(exc_info.value).__name__}, expected "
            f"{expected.__name__}. This assertion checks the EXACT type (not isinstance): "
            f"the helper must translate NOTHING.\n\n"
            f"scout's reconnect ladder catches (*_CONNECTION_ERRORS, KeyError, "
            f"TxnContentionExhaustedError) — RAW types. `SurrealConnectionError` is a "
            f"RuntimeError and is NOT among them, so a bootstrap that wrapped its own "
            f"failure (the obvious place to put a `try/except` that logs a label) would "
            f"satisfy every attribution pin and fly straight past that ladder: no backoff, "
            f"no reconnect, the command channel dead until the process restarts.\n\n"
            f"THE WRAP GOES AT THE SEAM. Attribution is added by passing `label=`/`url=` "
            f"INTO the driver, never by catching anything here."
        )
        assert not isinstance(exc_info.value, SurrealConnectionError), (
            "`bootstrap_session` raised a `SurrealConnectionError`. The ten ledger seams "
            "wrap what this raises, in their OWN `_ensure_connection`; scout deliberately "
            "does not wrap at all. Wrapping here takes that choice away from both."
        )


# ---------------------------------------------------------------------------
# 10b. EVERY `bootstrap_session` CALL PASSES ITS OWN URL.  (finding #151, R1 + adversary MP2)
#
# §10 proves the LABEL half of R1's triple over every caller. It proves the URL half over
# NONE — it never looks at a `bootstrap_session` call site at all. The consequence was
# measured: a build in which **all eleven production connection owners hardcode
# `url="ws://127.0.0.1:8000/rpc"`** passed the contract 489/0 AND produced a ZERO failure
# delta across all 6079 tests in the repository. Nothing anywhere could tell it from the
# real fix.
#
# THE OPERATIONAL HARM IS WORSE THAN THE HOLE #151 SET OUT TO CLOSE. Production connects to
# `:18500`. A hardcoded `:8000` in the exhaustion record is a PLAUSIBLE-LOOKING WRONG SERVER
# NAME — an absent url tells an operator nothing; a confident wrong one sends them to the
# wrong host. "Looks complete" is the failure mode.
#
# Same deny-by-default discipline as §10, same shared scanner (`_call_sites_in`), same
# evidence-backed allowlist — which is EMPTY, because all eleven owners have their url in
# hand at the call site (the ten seams hold `self._url`; scout's `_open_command_connection`
# takes `url` as a parameter). An empty allowlist is the strongest possible statement of the
# rule, and `test_every_bootstrap_exemption_is_EVIDENCE_BACKED` keeps it that way.
# ---------------------------------------------------------------------------

# Bootstrap call sites that pass no `url=` and are attributable anyway — `(module,
# enclosing) -> (evidence, count)`, exactly as §10's allowlist. EMPTY BY DESIGN: no
# production owner lacks a url at the call. An entry here needs the same quality of evidence
# §10 demands ("it writes no row" is not evidence), and the count is the exemption's SCOPE.
_BOOTSTRAP_ATTRIBUTED_BY_ANOTHER_MECHANISM: dict[tuple[str, str], _Exemption] = {}

# A floor on how much text an exemption's evidence must carry. Not a quality measure — no
# assertion can read English — but it makes the CHEAPEST way to punch a hole in a
# deny-by-default gate ("n/a", "", "TODO") mechanically impossible, so an author who wants
# one has to write a sentence a reviewer can then judge. §10's three entries run 180-300
# characters; this is set well below them so a genuinely terse real citation still passes.
_MIN_EVIDENCE_CHARACTERS = 60

# The eleven production connection owners: ten `_query` seams plus scout's
# `_open_command_connection`. A FLOOR, not an equality — a twelfth owner must not have to
# edit this number — but a scan finding FEWER has gone blind and every pin below it would
# go vacuously green. This is the same count `_MIN_KNOWN_BOOTSTRAP_OWNERS` pins from the
# `_ensure_connection` side; the two are derived independently and must agree.
_MIN_KNOWN_BOOTSTRAP_CALL_SITES = 11


def _bootstrap_call_sites_in(source: str) -> list[tuple[int, str, bool]]:
    """Every call to the shared session bootstrap — ``(lineno, enclosing, has_url)``."""
    return _call_sites_in(source, _SESSION_BOOTSTRAP_NAME, _BOOTSTRAP_URL_KEYWORD)


def _all_bootstrap_call_sites() -> list[tuple[str, int, str, bool]]:
    """``(module, lineno, enclosing, has_url)`` for the whole production package."""
    found: list[tuple[str, int, str, bool]] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        key = path.relative_to(_PACKAGE_ROOT).as_posix()
        for lineno, enclosing, has_url in _bootstrap_call_sites_in(
            path.read_text(encoding="utf-8")
        ):
            # The DEFINITION site is not a call site: `_txn.py` declares the helper, it does
            # not invoke it. The scanner is call-shaped (`ast.Call`), so this never fires
            # today — it is stated so a reader does not go looking for a twelfth owner.
            found.append((key, lineno, enclosing, has_url))
    return found


class TestEveryBootstrapCallThreadsItsOwnUrl:
    """**FINDING #151, THE URL LEG, STRUCTURALLY (adversary MP2 / invariant I8).**

    §10 asks *does every caller pass a label?* This asks *does every caller pass a url?* —
    the half of R1's triple that, before this class existed, was enforced by nothing at all.
    """

    def test_the_bootstrap_call_scan_is_not_silently_finding_nothing(self) -> None:
        """**THE REACH CONTROL**, and it is not optional decoration: every assertion below is
        a statement about a SET, and a scanner that returns the empty set satisfies all of
        them forever. Assert the reach, or the reach becomes the bug.
        """
        sites = _all_bootstrap_call_sites()

        assert len(sites) >= _MIN_KNOWN_BOOTSTRAP_CALL_SITES, (
            f"the scan found {len(sites)} call(s) to `{_SESSION_BOOTSTRAP_NAME}` "
            f"({[(module, lineno) for module, lineno, _, _ in sites]}) — this contract was "
            f"written against {_MIN_KNOWN_BOOTSTRAP_CALL_SITES} (ten `_query` seams + "
            f"scout's `_open_command_connection`). Either owners were consolidated (good — "
            f"lower this floor deliberately, in a diff a reviewer can see) or the SCANNER "
            f"broke and the gate below just went vacuously green."
        )

    def test_the_two_independent_owner_counts_AGREE(self) -> None:
        """The `_ensure_connection` side and the `bootstrap_session` side are enumerated by
        two different scans over two different properties. They describe the same eleven
        owners, so they must agree — and a disagreement means one of them has gone blind,
        which is precisely the failure neither can detect about itself.
        """
        assert _MIN_KNOWN_BOOTSTRAP_CALL_SITES == _MIN_KNOWN_BOOTSTRAP_OWNERS, (
            f"the bootstrap CALL-SITE floor ({_MIN_KNOWN_BOOTSTRAP_CALL_SITES}) and the "
            f"connection-OWNER floor ({_MIN_KNOWN_BOOTSTRAP_OWNERS}) disagree. They count "
            f"the same eleven owners from opposite ends; if one moved deliberately, move "
            f"the other in the same diff and say why."
        )

    def test_every_bootstrap_exemption_is_EVIDENCE_BACKED_and_REAL(self) -> None:
        """The allowlist is empty today. This pin is what makes "empty" a decision rather
        than an accident: a future entry must name a REAL call site and carry real evidence.
        """
        addresses = {(module, enclosing) for module, _, enclosing, _ in _all_bootstrap_call_sites()}
        stale = sorted(set(_BOOTSTRAP_ATTRIBUTED_BY_ANOTHER_MECHANISM) - addresses)
        assert not stale, (
            f"these bootstrap exemptions match no call site: {stale}. An exemption for code "
            f"that no longer exists pre-approves the next url-less call written there."
        )

        thin = sorted(
            address
            for address, (evidence, _count) in _BOOTSTRAP_ATTRIBUTED_BY_ANOTHER_MECHANISM.items()
            if len(evidence.strip()) < _MIN_EVIDENCE_CHARACTERS
        )
        assert not thin, (
            f"these bootstrap exemptions carry no real evidence: {thin}. An exemption must "
            f"name the record the caller emits INSTEAD, by event name and file:line. 'It "
            f"writes no row' and 'out of scope for this wave' are not evidence — the repo "
            f"forbids exactly that, and an un-evidenced hole in a deny-by-default gate is "
            f"the thing the gate exists to prevent."
        )

    def test_every_bootstrap_session_call_passes_a_url(self) -> None:
        """RED today x11: not one production owner passes a ``url``, because
        ``bootstrap_session`` does not yet take one.

        THE WRONG BUILD THIS EXISTS FOR is not the unfixed tree — it is the *fixed-looking*
        one: `bootstrap_session` grows its `url` parameter, threads it faithfully into all
        three `retry_on_conflict` calls, every behavioural pin in
        `TestTheBootstrapPathsExhaustionIsAttributable` goes green... and the eleven callers
        hardcode a constant into it. Measured: 489/0 on the contract, zero failure delta
        across 6079 tests. This gate is the thing that sees it, and
        `TestEveryProductionOwnerThreadsITSOWNUrl` is the behavioural half.

        Every residual site is named with `file:line` and its enclosing function — repo law
        bans "all remaining hits are X" as an output.
        """
        by_body: dict[tuple[str, str], list[int]] = {}
        for module, lineno, enclosing, has_url in _all_bootstrap_call_sites():
            if not has_url:
                by_body.setdefault((module, enclosing), []).append(lineno)

        without_url: list[tuple[str, int, str]] = []
        for (module, enclosing), linenos in sorted(by_body.items()):
            _evidence, allowed = _BOOTSTRAP_ATTRIBUTED_BY_ANOTHER_MECHANISM.get(
                (module, enclosing), ("", 0)
            )
            if len(linenos) > allowed:
                without_url.extend((module, lineno, enclosing) for lineno in sorted(linenos))

        assert not without_url, (
            "these calls to the shared session bootstrap pass no `url=`:\n  "
            + "\n  ".join(
                f"{module}:{lineno}  in {enclosing}()" for module, lineno, enclosing in without_url
            )
            + "\n\nR1: the exhaustion record carries the full triple — WHICH statement "
            "(`label`), WHICH server (`url`), and WHAT THE ENGINE SAID (`engine_error`). "
            "A bootstrap that is labelled but not addressed tells an operator that "
            "DEFINE NAMESPACE exhausted somewhere. Every owner listed above has its url "
            "in hand at the call site: the ten `_query` seams hold `self._url`, and "
            "scout's `_open_command_connection` takes `url` as a parameter. Pass it.\n\n"
            "⚠ DO NOT satisfy this by hardcoding a url inside `bootstrap_session` or by "
            "defaulting the parameter. That build passes 489/0 and adds a plausible-looking "
            "WRONG server name to every exhaustion record — worse than the absent url #151 "
            "set out to fix. `TestEveryProductionOwnerThreadsITSOWNUrl` drives all eleven "
            "owners at eleven DIFFERENT urls and will catch it."
        )

    def test_the_bootstrap_scan_SEES_a_url_less_call(self) -> None:
        """**POSITIVE CONTROL.** A gate never shown firing is not a gate — and this one must
        not mistake a POSITIONAL fourth argument for the keyword R2 requires.
        """
        source = """
async def _ensure_connection(self):
    await bootstrap_session(connection, self._namespace, self._database)
    await _txn.bootstrap_session(connection, ns, db, self._url)
"""
        found = _bootstrap_call_sites_in(source)

        assert [(enclosing, has_url) for _, enclosing, has_url in found] == [
            ("_ensure_connection", False),
            ("_ensure_connection", False),
        ], (
            f"the scan saw {found} in a textbook url-less bootstrap. It must see BOTH the "
            f"bare call and the attribute call, and must NOT count a positional fourth "
            f"argument as the url — R2 makes `url` KEYWORD-ONLY precisely because all four "
            f"parameters are strings and a swap type-checks."
        )

    def test_the_bootstrap_scan_SPARES_a_url_carrying_call(self) -> None:
        """**NEGATIVE CONTROL.** A gate that fires on the correct build gets switched off,
        and then nothing is watching at all.
        """
        source = """
async def _ensure_connection(self):
    await bootstrap_session(connection, self._namespace, self._database, url=self._url)
"""
        found = _bootstrap_call_sites_in(source)

        assert [has_url for _, _, has_url in found] == [True], (
            f"the scan reported {found} for a correctly-threaded call — it flags the exact "
            f"shape the fix asks every owner to write."
        )

    def test_the_TWO_gates_SHARE_one_scanner(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """**PROVE SHARING BY MUTATION** — the only test that distinguishes DRY from
        looks-DRY (CLAUDE.md #102: routing is not sharing, and a caller that keeps working
        after the shared thing moves is a private copy wearing the shared name).

        Move the keyword each gate requires, and BOTH gates' verdicts must move with it. A
        second, hand-rolled `_bootstrap_call_sites_in` would keep answering the old way — and
        then the day someone widens one scanner's reach (to see decorated calls, say), only
        one of the two attribution gates would learn it.
        """
        module = sys.modules[__name__]
        labelled = "await retry_on_conflict(_attempt, label='x')\n"
        addressed = "await bootstrap_session(connection, ns, db, url=self._url)\n"

        assert _retry_driver_call_sites_in(labelled)[0][2], "control: the retry gate sees `label=`"
        assert _bootstrap_call_sites_in(addressed)[0][2], "control: the bootstrap gate sees `url=`"

        monkeypatch.setattr(module, "_RETRY_ATTRIBUTION_KEYWORD", "not_the_keyword")
        assert not _retry_driver_call_sites_in(labelled)[0][2], (
            "the retry gate still recognised `label=` after `_RETRY_ATTRIBUTION_KEYWORD` "
            "moved — it holds a private copy of the keyword, so this mutation proves "
            "nothing about either scanner."
        )
        monkeypatch.undo()

        monkeypatch.setattr(module, "_BOOTSTRAP_URL_KEYWORD", "not_the_keyword")
        assert not _bootstrap_call_sites_in(addressed)[0][2], (
            "the bootstrap gate still recognised `url=` after `_BOOTSTRAP_URL_KEYWORD` "
            "moved: it is a SECOND scanner wearing the shared name, not a caller of "
            "`_call_sites_in`. Fold it back onto the shared function — two copies of one "
            "policy is where the two gates' reach silently diverges."
        )


# ---------------------------------------------------------------------------
# 10c. EACH PRODUCTION OWNER LOGS *ITS OWN* URL.  (finding #151 — adversary B1/MP1, BLOCKER)
#
# THE HOLE THIS CLOSES, MEASURED. The first contract's url invariant was quantified over
# exactly ONE caller — `_surreal_harness.connect_admin` — and that caller is a TEST FILE the
# builder is allowed to edit (R5). The eleven PRODUCTION owners carried zero url pins. A
# build in which all eleven hardcode `url="ws://127.0.0.1:8000/rpc"` passed the contract
# **489 / 0** and produced a **ZERO failure delta across all 6079 tests in the repository**.
# Nothing anywhere could tell it from the real fix.
#
# THE QUANTIFIER LAW, VERBATIM (CLAUDE.md): never condition an invariant on the failure mode
# that prompted the work. #151 was *"the record carries no url"*, so the contract pinned
# *"a url arrives"* — and every wrong build that carries a url, from anywhere, walks through.
# Pin the OUTCOME property ∀ callers and FORCE each fate with a fixture.
#
# THE GENERALISATION THE ADVERSARY DREW, worth keeping: the first contract broke
# parameter-value monoculture correctly at the driver (`_DISTINCT_BOOTSTRAP_URL`, a
# TEST-NET-2 address appearing nowhere else) and then reintroduced it one level up as
# **CALLER-POPULATION MONOCULTURE**. The repo's law reads *"if the code can branch on a
# value, at least one pin must use a DIFFERENT value."* Its dual: **if a value must be
# THREADED from N call sites, at least two pins must drive DIFFERENT call sites with
# DIFFERENT values** — and one caller is a monoculture, a test-tree caller doubly so.
#
# So this class drives ALL ELEVEN owners at ELEVEN DIFFERENT urls, and
# `test_every_owner_the_scan_finds_is_DRIVEN_here` makes that coverage a CHECKED VARIABLE
# rather than a claim in a comment.
# ---------------------------------------------------------------------------

# One url per owner, derived from the owner's OWN name — never a shared constant, which is
# the very build this class exists to catch. RFC-5737 TEST-NET-2 with an owner-specific path,
# so no two owners share a value and no value appears anywhere else in the repository. Never
# dialed: `AsyncSurreal` is monkeypatched out in every pin here.
#
# ⚠ DERIVED FROM THE NAME, NEVER FROM `hash()`: string hashing is per-process randomised, so
# a hash-derived url is a value that differs between xdist workers and can COLLIDE between
# two owners — a 1-in-N flake in the one pin that compares two owners' urls to each other.
# A failing test is a STOP in this repo and "flaky" is not a verdict anyone may render, so
# the fixture may not manufacture one.
_OWNER_URL_TEMPLATE = "ws://198.51.100.151:19151/rpc-151-owner-{owner}"

# Scout's bootstrap owner is a module-level FUNCTION, not a class with an
# `_ensure_connection` — which is exactly why it was the eleventh hand-rolled copy that no
# `_query`-keyed enumeration could see (#120). It is driven by its own pin below; naming it
# here keeps the coverage check honest about why it is not in `_QUERY_SEAMS`.
_SCOUT_BOOTSTRAP_MODULE = "loremaster.scout"
_SCOUT_BOOTSTRAP_FUNCTION = "_open_command_connection"


def _owner_url(owner: str) -> str:
    """A url unique to ``owner`` — stable across runs, distinct across owners."""
    return _OWNER_URL_TEMPLATE.format(owner=owner)


def _construct_at_url(seam: type, url: str) -> Any:
    """Build ``seam`` from :data:`_CTOR_VALUES` but pointed at ``url``.

    Deliberately NOT a mutation of `_CTOR_VALUES`: this class's whole point is that two
    owners alive at once hold two DIFFERENT urls, which a shared dict cannot express.
    """
    values = dict(_CTOR_VALUES, url=url)
    signature = inspect.signature(cast("Any", seam))
    required = [
        name
        for name, parameter in signature.parameters.items()
        if name != "self" and parameter.default is inspect.Parameter.empty
    ]
    unknown = [name for name in required if name not in values]
    assert not unknown, (
        f"{seam.__name__} requires constructor parameter(s) {unknown} this contract cannot "
        f"supply. Add them to `_CTOR_VALUES` — do NOT drop the owner from the enumeration; "
        f"an owner that quietly falls out of this class is the blocker walking back in."
    )
    assert "url" in required, (
        f"{seam.__name__} takes no required `url` constructor parameter, so this pin cannot "
        f"give it a url of its own and would pass for a FIXTURE reason. If an owner now "
        f"obtains its url some other way, drive it explicitly — do not let it fall out."
    )
    return seam(**{name: values[name] for name in required})


def _forever_conflicting_bootstrap() -> Any:
    """A connection whose every bootstrap step conflicts, forever."""
    return cast("Any", _BootstrapScriptedConnection(error=_conflict_error(), failures=None))


def _exhaustion_record(caplog: pytest.LogCaptureFixture) -> logging.LogRecord:
    """The single ``store.retry.exhausted`` record, or a loud failure.

    Exactly-once on every path is itself a pinned property of the driver
    (:class:`TestExhaustionIsLoggedExactlyOnceOnBothPaths`), so reading "the" record must
    never silently take the first of several — a build that logged one record per statement
    would otherwise let this class read a url that belongs to a different call.
    """
    records = _records(caplog, _EXHAUSTION_EVENT)
    assert len(records) == 1, (
        f"expected exactly one `{_EXHAUSTION_EVENT}` record, got {len(records)}"
    )
    return records[0]


class TestEveryProductionOwnerThreadsITSOWNUrl:
    """**FINDING #151, THE BLOCKER (adversary B1/MP1).** Eleven owners, eleven urls, and each
    exhaustion record names the server THAT owner was connecting to.
    """

    @pytest.mark.parametrize(("module_path", "seam"), _QUERY_SEAMS)
    async def test_each_production_owner_logs_ITS_OWN_url_on_bootstrap_exhaustion(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        module_path: str,
        seam: type,
    ) -> None:
        """RED today x10: the record carries ``attempts`` and ``elapsed_seconds`` and nothing
        else, because no owner passes a ``url`` and the driver gates the extra on ``label``.

        Each owner is constructed at a url derived from its OWN class name, so the value on
        the record can only have arrived by being threaded from THIS owner's call site. A
        build that hardcodes, defaults, or module-globals its way to a url fails here for
        ten of the eleven owners even when the url it logs looks entirely plausible.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)  # the attempt floor governs: 5 and out
        _point_at(monkeypatch, module_path, _forever_conflicting_bootstrap())
        url = _owner_url(seam.__name__)
        owner = _construct_at_url(seam, url)

        with caplog.at_level(logging.WARNING, logger=_TXN_LOGGER):
            with pytest.raises(SurrealConnectionError):
                await owner._ensure_connection()

        record = _exhaustion_record(caplog)
        assert getattr(record, "url", None) == url, (
            f"{seam.__name__} ({module_path}) exhausted its session bootstrap and logged "
            f"url={getattr(record, 'url', None)!r}; it was connecting to {url!r}.\n\n"
            f"This assertion checks EXACT equality with the url THIS OWNER holds, and this "
            f"pin runs once per owner at a DIFFERENT url each time — because the wrong build "
            f"it exists for is not 'no url' but 'the same url for everyone'. Measured: all "
            f"eleven owners hardcoding one RPC address passed the previous contract 489/0 "
            f"with a ZERO failure delta over 6079 tests. In production, where the real "
            f"server is `:18500`, that build writes a confident WRONG hostname into the one "
            f"record an operator reads at 3am.\n\n"
            f"The fix is one argument at this owner's call site: "
            f"`await bootstrap_session(connection, ns, db, url=self._url)`."
        )

    async def test_scouts_command_connection_logs_ITS_OWN_url_on_bootstrap_exhaustion(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """RED today: **the ELEVENTH owner**, and the one every symbol-keyed enumeration
        misses — a module-level function, not a class with an ``_ensure_connection``. It was
        the eleventh hand-rolled bootstrap copy for exactly that reason (#120), so a pin
        parametrized over `_QUERY_SEAMS` alone would leave it exactly as unpinned as before.

        Note the disposition differs and MUST: scout's ladder needs the RAW exhaustion type,
        so this raises `TxnContentionExhaustedError` where the ten seams wrap.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        monkeypatch.setattr(
            scout_module, "AsyncSurreal", lambda url: _forever_conflicting_bootstrap()
        )
        url = _owner_url(_SCOUT_BOOTSTRAP_FUNCTION)

        with caplog.at_level(logging.WARNING, logger=_TXN_LOGGER):
            with pytest.raises(TxnContentionExhaustedError):
                await scout_module._open_command_connection(
                    url=url,
                    namespace=_CTOR_VALUES["namespace"],
                    database=_CTOR_VALUES["database"],
                    user=_CTOR_VALUES["user"],
                    password=_CTOR_VALUES["password"],
                )

        record = _exhaustion_record(caplog)
        assert getattr(record, "url", None) == url, (
            f"scout's `{_SCOUT_BOOTSTRAP_FUNCTION}` exhausted its session bootstrap and "
            f"logged url={getattr(record, 'url', None)!r}; it was connecting to {url!r}. "
            f"The url is a PARAMETER of this function — it is in hand at the call site, "
            f"exactly as `self._url` is for the ten seams. Pass it: "
            f"`await bootstrap_session(connection, namespace, database, url=url)`."
        )

    async def test_two_owners_at_two_urls_log_TWO_DIFFERENT_urls(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**DERIVED, not declared** — the same idiom as the three-distinct-labels pin.

        The per-owner pins above each compare an observation to a CONSTANT this file chose.
        This one compares two OBSERVATIONS to EACH OTHER, so it cannot be satisfied by any
        build in which the url reaching the record is a single value — a module global, a
        cached last-connected address, a class attribute on a shared base — however that
        value was obtained. Two owners, two urls, one assertion that they differ.
        """
        seams = sorted(_discover_query_seams(), key=lambda entry: entry[1].__name__)
        assert len(seams) >= 2, (
            f"this pin needs TWO distinct production owners to compare and found "
            f"{len(seams)}. With one owner it cannot tell 'threaded' from 'hardcoded to the "
            f"value this fixture happens to use' — the exact non-discrimination that made "
            f"the blocker invisible."
        )

        observed: list[tuple[str, Any]] = []
        for module_path, seam in seams[:2]:
            caplog.clear()
            with monkeypatch.context() as patch:
                _silence_sleep(patch)
                _set_default_deadline(patch, 0.0)
                _point_at(patch, module_path, _forever_conflicting_bootstrap())
                url = _owner_url(seam.__name__)
                owner = _construct_at_url(seam, url)
                with caplog.at_level(logging.WARNING, logger=_TXN_LOGGER):
                    with pytest.raises(SurrealConnectionError):
                        await owner._ensure_connection()
            observed.append((seam.__name__, getattr(_exhaustion_record(caplog), "url", None)))

        first, second = observed
        assert first[1] != second[1], (
            f"{first[0]} and {second[0]} were connecting to two DIFFERENT servers and both "
            f"exhaustion records name {first[1]!r}. Whatever the record's url is being read "
            f"from, it is not this owner's — it is one shared value wearing eleven owners' "
            f"names. This assertion compares the two OBSERVED urls to each other, so it "
            f"holds no opinion about what the right value is: it only requires that two "
            f"different callers cannot report the same server."
        )

    def test_the_per_owner_urls_this_class_drives_are_PAIRWISE_DISTINCT(self) -> None:
        """**THE FIXTURE'S OWN DISCRIMINATION, ASSERTED RATHER THAN ASSUMED** (adversary-151b
        I16). Every per-owner pin above compares one observation to ``_owner_url(name)``. All
        of their discriminating power therefore lives in ONE property of the fixture: that
        the template's ``{owner}`` slot makes eleven DIFFERENT values.

        Measured by the adversary: collapse that slot to a shared constant and the correct
        build and the hardcoded-url blocker build become INDISTINGUISHABLE across all ten
        per-owner pins — every one of them passes for both. The collapse is currently
        self-announcing only INDIRECTLY, via
        ``test_two_owners_at_two_urls_log_TWO_DIFFERENT_urls`` going red for a reason that
        names the production code rather than the fixture. This pin names the real cause.

        It is GREEN today by design: it asserts a property of this file's own fixture, not of
        the tree under test, so it goes red only if someone edits ``_OWNER_URL_TEMPLATE`` in a
        way that silently un-discriminates ten pins.
        """
        owners = [seam.__name__ for _, seam in _discover_query_seams()] + [
            _SCOUT_BOOTSTRAP_FUNCTION
        ]
        urls = [_owner_url(owner) for owner in owners]

        assert len(set(urls)) == len(urls), (
            f"the {len(urls)} owners this class drives resolve to only {len(set(urls))} "
            f"distinct url(s). Two owners sharing a url makes the pins that drive them "
            f"unable to tell a threaded url from a hardcoded one — they would pass for the "
            f"blocker build this whole class exists to catch. `_OWNER_URL_TEMPLATE` must "
            f"keep its `{{owner}}` slot, and no two owners may share a name."
        )

    def test_every_owner_the_scan_finds_is_DRIVEN_here(self) -> None:
        """**COVERAGE AS A CHECKED VARIABLE** — the failure this repo has been bitten by six
        times (CLAUDE.md's instrument table: *a runtime gate is an invariant only over code
        it actually RUNS*). This class asserts a property ∀ owners; that quantifier is a LIE
        the moment an owner exists that no pin drives, and nothing about a green run would
        say so.

        So: enumerate the owners STRUCTURALLY (every module the bootstrap call-site scan
        finds), enumerate the owners this class DRIVES, and require the two sets to match. A
        twelfth owner added tomorrow fails HERE, by name, instead of quietly inheriting the
        blocker.
        """
        scanned = {
            f"loremaster.{module.removesuffix('.py').replace('/', '.')}"
            for module, _, _, _ in _all_bootstrap_call_sites()
        }
        driven = {module_path for module_path, _ in _discover_query_seams()} | {
            _SCOUT_BOOTSTRAP_MODULE
        }

        undriven = sorted(scanned - driven)
        assert not undriven, (
            f"these modules call the shared session bootstrap and NO pin in this class "
            f"drives them to exhaustion: {undriven}.\n\nThey are therefore exempt from the "
            f"one invariant that catches the #151 blocker, and the class's ∀-over-owners "
            f"claim is false for them. Add a pin (a class owner joins `_QUERY_SEAMS` "
            f"automatically by owning an `async def _query`; a module-level owner needs its "
            f"own pin, as scout's does) — do not widen this exclusion."
        )

        phantom = sorted(driven - scanned)
        assert not phantom, (
            f"this class drives {phantom}, which the structural scan does not see calling "
            f"`{_SESSION_BOOTSTRAP_NAME}` at all. Either the scanner has gone blind (in "
            f"which case every gate in §10b is vacuous) or these owners stopped using the "
            f"shared bootstrap — which is finding #120 reopening. Neither is a test-list "
            f"problem; do not fix it by deleting a pin."
        )


# ---------------------------------------------------------------------------
# 10d. SCOUT'S QUERY SEAM IS ATTRIBUTED BY LABEL ONLY — A PINNED, KNOWN BOUND.
#      (finding #151, OPERATOR RULING R4)
#
# `scout.py:171` (`_scout_query`) is a FOURTH unlabelled call into the retry driver, and it
# is #151's exact shape in a different function: it propagates, it logs nothing of its own,
# and its exhaustion produces the same unattributable record under the same "see the server
# log" hint. It is NOT exempt — there is no evidence to offer, and "out of scope for this
# wave" is precisely what this repo forbids an exemption to say.
#
# THE OPERATOR RULED (R4): it gets a LABEL only. Partial attribution — label + engine text,
# `url=None`. The reason is structural, not a scheduling excuse: `_scout_query` takes a
# `connection` and nothing else, and `CommandSubscriber` holds a `connect` CALLABLE rather
# than a url, so full url attribution there means threading a url through scout's whole
# connection ownership — a design change, not a one-line fix.
#
# AND SO THE HOLE IS PINNED, NOT INHERITED (CLAUDE.md: *when you cannot close a hole, pin
# it* — an unpinned known limitation is indistinguishable from an unknown one, and the next
# engineer either rediscovers it from an outage or closes it and silently re-opens a settled
# trade).
# ---------------------------------------------------------------------------


@dataclass
class _ForeverConflictingQuery:
    """A connection whose every ``query`` conflicts — scout's query seam, driven to exhaustion."""

    calls: int = field(default=0, init=False)

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        self.calls += 1
        if self.calls > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError("unbounded retry in scout's query seam")
        raise _conflict_error()


class TestScoutsQuerySeamIsAttributedByLabelOnly:
    """**OPERATOR RULING R4, pinned in both directions.**"""

    async def test_scouts_query_exhaustion_carries_a_label_OF_ITS_OWN(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """RED today: `scout.py:171` passes no `label`, so the driver suppresses all three
        extras and scout's exhaustion is as unattributable as the bootstrap's was.

        The expected label is checked as a PROPERTY, not against a constant this file
        declares: it must be a non-empty string that is none of the bootstrap's three and not
        `run_query`'s either. That deliberately holds no opinion on scout's naming vocabulary
        (its own log events are `command_subscriber.*`, not `scout.*`, so a substring pin on
        "scout" would have been a C-DEF trap for a builder doing the right thing) while still
        refusing the wrong build that borrows another caller's label to satisfy a gate.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _ForeverConflictingQuery()

        with caplog.at_level(logging.WARNING, logger=_TXN_LOGGER):
            with pytest.raises(TxnContentionExhaustedError):
                await scout_module._scout_query(cast("Any", connection), "SELECT * FROM command")

        record = _exhaustion_record(caplog)
        label = getattr(record, "label", None)

        assert isinstance(label, str) and label, (
            f"scout's query seam exhausted and logged label={label!r}. Every other caller of "
            f"the driver names itself; this one raises 'see the server log for the full "
            f"engine detail' over a record holding `{{attempts, elapsed_seconds}}`. That is "
            f"finding #151's shape, in `_scout_query` instead of `bootstrap_session`. Pass a "
            f"canonical event name as `label=` (operator ruling R4)."
        )

        borrowed = {
            getattr(txn_module, name)
            for name in (
                "_BOOTSTRAP_DEFINE_NAMESPACE_LABEL",
                "_BOOTSTRAP_SELECT_DATABASE_LABEL",
                "_BOOTSTRAP_DEFINE_DATABASE_LABEL",
            )
            if isinstance(getattr(txn_module, name, None), str)
        }
        assert label not in borrowed, (
            f"scout's query seam labelled its exhaustion {label!r} — a label that belongs to "
            f"the session bootstrap. A borrowed label satisfies a presence check and sends "
            f"the operator to the wrong emitter, which is worse than no label at all."
        )

    async def test_scouts_query_exhaustion_carries_NO_url_a_KNOWN_BOUND(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**THIS IS A KNOWN BOUND (#151, operator ruling R4), PINNED — not a passing gate.**

        Scout's query seam is attributed by LABEL ONLY. The record names WHICH seam and WHAT
        THE ENGINE SAID; it does NOT name WHICH SERVER, because `_scout_query` has no url in
        scope and `CommandSubscriber` holds a `connect` callable rather than an address.
        Closing that is a design change to scout's connection ownership, and the operator
        ruled it a separate wave.

        **IF YOU CLOSED THIS DELIBERATELY, DELETE THIS PIN AND SAY SO IN THE SAME DIFF** —
        then extend `test_scouts_query_exhaustion_carries_a_label_OF_ITS_OWN` to assert the
        url too, so the seam does not go from pinned-partial to unpinned-complete.

        **NAMED RE-OPEN TRIGGER:** the day `_scout_query` (or its caller chain) gains a url —
        e.g. `CommandSubscriber` taking a url alongside its `connect` factory, or the command
        channel joining the ten `_query` seams' shape. At that point the bound has no reason
        left to exist and this pin is what makes closing it a DECISION rather than a drift.

        ⚠ DISCLOSED: this assertion does not discriminate on the UNFIXED tree — today the
        record carries no url because it carries no label either, so `url is None` is true
        for the wrong reason. Its proof is a MUTATION (thread a url into `scout.py:171` and
        watch this go red), recorded in REPORT-contract-151b.md, and it becomes a real
        tripwire the moment the label lands.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _ForeverConflictingQuery()

        with caplog.at_level(logging.WARNING, logger=_TXN_LOGGER):
            with pytest.raises(TxnContentionExhaustedError):
                await scout_module._scout_query(cast("Any", connection), "SELECT * FROM command")

        record = _exhaustion_record(caplog)
        assert getattr(record, "url", None) is None, (
            f"scout's query seam now logs url={getattr(record, 'url', None)!r}. **This is a "
            f"KNOWN BOUND (#151, operator ruling R4) — scout's query seam is attributed by "
            f"LABEL ONLY, because `_scout_query` has no url in scope. If you closed this "
            f"deliberately, delete this pin and say so in the same diff**, and extend the "
            f"label pin above to assert the url as well."
        )


# ---------------------------------------------------------------------------
# 10e. THE PROSE HALF OF #151 — the driver's own ENGLISH, DERIVED FROM ITS CALLERS.
#      (finding #151 HALF 2 · adversary-151b MP7 · adversary-151b residual R1)
#
# #151's defect statement has TWO coupled halves, and every pin above grades the first.
# HALF 2, verbatim from the finding: `retry_on_conflict`'s own docstring (`_txn.py:857-859`)
# justifies the `None` default with *"`bootstrap_session` and `execute_transaction`, which
# have their own attribution"* — TRUE of `execute_transaction` (`_log_rollback`), FALSE of
# `bootstrap_session`, which logs nothing at all. The finding is explicit that this clause
# "did not document the hole; it CLOSED THE QUESTION for every reader who trusted it."
#
# MEASURED (adversary-151b §4): a build with the BEHAVIOUR perfectly correct and that clause
# left in place scores **515 passed / 0 failed** — indistinguishable from the real fix. And
# after the fix the sentence does not merely go stale, it INVERTS: `bootstrap_session` no
# longer uses the `None` default it is documented as using, so the prose describes a RETIRED
# world in the one place a future caller looks to decide whether IT needs a label. That is
# #151 re-planted, in the exact function #151 is about.
#
# WHY THIS IS A GATE AND NOT A REMINDER. CLAUDE.md, "A DIAGNOSIS IS NOT AN INSTRUMENT":
# *"when a defect CLASS is identified, ship the INSTRUMENT in the same breath as the law"* —
# written because this repo shipped TEN more instances of the served-English class in one
# phase AFTER naming it. The instrument for exactly this shape already existed thirty lines
# away in `test_surreal_harness.py` (`test_the_harnesss_docstring_counts_are_the_DERIVED_counts`)
# and was simply never pointed at the docstring the finding names.
#
# ⚠ AND IT IS NOT A STRING MATCH ON PROSE. CLAUDE.md: *"prose that describes behaviour must
# be DERIVED from the behaviour, not re-stated beside it."* A pin asserting a sentence's text
# would pin the CURRENT wording and go red on every honest rewrite — the cry-wolf gate that
# gets switched off. So both pins below CROSS-REFERENCE two independently-derived sets: what
# the prose NAMES, and what the AST scan MEASURES. Neither set is written down here.
# ---------------------------------------------------------------------------

# The one variable whose explanation carries R1's universal. Named, not inlined: the comment
# extractor is keyed on it, and a rename must move the pin rather than blind it.
_LAST_CONFLICT_CAUSE_VARIABLE = "last_conflict_cause"
_RETRY_SIGNAL_NAME = "RetryableConflictSignal"

# Every `raise RetryableConflictSignal` the seam module holds today: three in
# `bootstrap_session`'s statement bodies, one in `run_query`'s attempt, one in
# `execute_transaction`'s. A FLOOR, not an equality — a new seam must not have to edit this
# number — but a walker that suddenly finds FEWER has gone blind and both pins below would
# go vacuously green.
_MIN_KNOWN_CONFLICT_SIGNAL_RAISE_SITES = 5


def _seam_module_source() -> str:
    """The retry seam's own source, read from the tree the AST scans already enumerate."""
    return (_PACKAGE_ROOT / _SEAM_MODULE).read_text(encoding="utf-8")


# The callers whose SELF-ATTRIBUTION CLAIM this pin audits: the two the driver's docstring
# has ever named as deliberately omitting `label=` (its `None`-default users). NOT "every
# caller the docstring mentions" — a docstring may legitimately name a LABELLED caller in
# passing (e.g. as a positive example), and a universe of all callers would then red-flag it
# for being mentioned at all, which is a gate that fires on correct code. This set is the
# enumeration of CLAIMS under audit, not a forbidden-name list: a claim outside it is simply
# not checked (a completeness bound the reach control below makes visible), never mis-flagged.
#
# It is not required to stay in the docstring: the whole point of #151's fix is that
# `bootstrap_session` LEAVES this clause, so a member absent from the current docstring means
# "no longer claimed" (fine), while a member present-and-labelled means "claimed but false"
# (the liar). What the reach control DOES pin is that every member is a real driver caller, so
# a renamed caller cannot leave a dead audit entry that silently checks nothing.
_DOCUMENTED_SELF_ATTRIBUTING = frozenset({"bootstrap_session", "execute_transaction"})


def _prose_liars(prose: str, audited: frozenset[str], unlabelled: set[str]) -> list[str]:
    """Audited callers the ``prose`` names as label-less that in fact PASS a label.

    A PURE FUNCTION of three derived inputs, so it can be exercised against a KNOWN-BROKEN
    case (a probe that reports "no liars" because it is broken reports that for everything —
    CLAUDE.md's positive-control law). ``audited`` scopes which claims are checked, so a
    labelled caller the prose merely mentions cannot trip the pin — only a caller the prose
    names AND that is under audit AND that turns out to pass a label is a liar.
    """
    named = {caller for caller in audited if caller in prose}
    return sorted(named - unlabelled)


def _unlabelled_driver_callers() -> set[str]:
    """The enclosing functions that call the driver WITHOUT a label, from the scan §10 gates.

    Read from `_all_retry_driver_call_sites`, so this class and §10 can never disagree about
    who omits the label — and §10's reach control already guards the scan.
    """
    return {enclosing for _, _, enclosing, has_label in _all_retry_driver_call_sites() if not has_label}


class TestTheDriversProseAboutItsCallersIsDerivedFromItsCallers:
    """**FINDING #151, HALF 2 (adversary-151b MP7 / invariant I14).**

    The driver's docstring tells the next author which callers deliberately omit `label=`.
    That is a claim ABOUT CODE, and this class is the only thing in the repository that
    checks it against the code.
    """

    def test_the_reach_the_liar_check_depends_on_is_ALL_LIVE(self) -> None:
        """**THE REACH CONTROL.** This pin is a statement about an INTERSECTION over three
        derived inputs, and any one of them going quiet satisfies it forever: an empty
        docstring, an empty audit set, or an audit-set entry that no longer names a real
        caller (so its claim is checked against nothing). All three are asserted live.
        """
        prose = _retry_driver_docstring()
        every_caller = {enclosing for _, _, enclosing, _ in _all_retry_driver_call_sites()}

        assert prose.strip(), (
            f"`{_RETRY_DRIVER_NAME}` has no docstring at all, so the pin below compares the "
            f"empty set against the callers and passes vacuously. If the docstring was "
            f"deliberately removed, this pin has nothing left to guard — say so in the diff."
        )
        assert _DOCUMENTED_SELF_ATTRIBUTING, (
            "the audit set of self-attribution claims is empty, so the pin below checks "
            "nothing. It must name every caller the driver's docstring has claimed omits "
            "`label=` deliberately."
        )
        dead = sorted(_DOCUMENTED_SELF_ATTRIBUTING - every_caller)
        assert not dead, (
            f"these audited self-attribution claims name no live driver caller: {dead}. An "
            f"audit entry for a caller that no longer exists checks its claim against nothing "
            f"— the vacuously-green failure this control exists to catch. If a caller was "
            f"renamed, rename it here; if it was removed, drop it and say so."
        )

    def test_the_liar_detector_FIRES_on_a_known_lie(self) -> None:
        """**POSITIVE CONTROL, plus the two negatives that make it mean something.**

        Four legs, deliberately: a prose/behaviour pair that IS a lie must be reported; the
        SAME prose against behaviour that matches must not; a name the prose does not mention
        must not be reported however it behaves; and a caller OUTSIDE the audit set that the
        prose names as label-less while it passes a label must NOT be reported — that last
        leg is the false-positive door this pin's audit-set scoping exists to shut.
        """
        audited = frozenset({"bootstrap_session", "execute_transaction"})
        prose = (
            "``bootstrap_session`` and ``execute_transaction`` have their own attribution; "
            "``run_query`` passes its own label."
        )

        assert _prose_liars(prose, audited, {"execute_transaction"}) == ["bootstrap_session"], (
            "CONTROL FAILED: the detector cannot see a caller the prose names as unlabelled "
            "that in fact passes a label. The pin below then proves nothing — it would hold "
            "for a detector that reports nothing at all."
        )
        assert _prose_liars(prose, audited, {"bootstrap_session", "execute_transaction"}) == [], (
            "CONTROL FAILED: the detector reports a lie when the prose and the behaviour "
            "AGREE. A gate that fires on correct code is a gate that gets switched off."
        )
        assert _prose_liars(prose, audited, set()) == [
            "bootstrap_session",
            "execute_transaction",
        ], (
            "CONTROL FAILED: the detector must report EVERY audited caller whose behaviour "
            "contradicts the prose, not just the first."
        )
        # `run_query` is named by the prose AND passes a label (so it is NOT in `unlabelled`),
        # yet it must NOT be a liar — because it is not a claim under audit. This is the leg
        # that distinguishes audit-set scoping from a universe of all callers.
        assert "run_query" not in _prose_liars(prose, audited, {"execute_transaction"}), (
            "CONTROL FAILED: the detector flagged a LABELLED caller the prose merely mentions. "
            "That is exactly the false positive the audit-set scoping exists to prevent — a "
            "gate that reds on a docstring naming a caller that already does the right thing."
        )

    def test_every_caller_the_docstring_names_as_UNLABELLED_really_passes_no_label(self) -> None:
        """**GREEN TODAY, BY DESIGN — and RED the moment #151's behaviour lands unaccompanied.**

        Today the docstring names `bootstrap_session` and `execute_transaction` as omitting
        the seam-identity extras, and both genuinely do: the prose is TRUE, so this pin passes
        on the UNFIXED tree. It is therefore not an always-red trap that a builder could
        satisfy by doing nothing, and not a pin that can be inherited silently.

        The instant `bootstrap_session` starts passing `label=` — i.e. the instant HALF 1 of
        #151 is fixed — the docstring's claim becomes false and this goes RED, naming
        `bootstrap_session`. The fix is to retire the clause in the SAME diff, exactly as the
        finding directs.

        DERIVED, NOT MATCHED: the verdict is `{claims the docstring still names} − {callers
        the AST scan measured as unlabelled}`. Nothing here asserts a sentence's WORDING —
        reword the clause however you like, and it only ever objects when a caller the English
        still names as label-less has in fact grown a label. Adding a NEW self-attribution
        claim to the docstring is a deliberate act (extend `_DOCUMENTED_SELF_ATTRIBUTING` in
        the same diff), which is why the audit set is enumerated rather than derived from the
        prose: a claim nobody registered is a claim nobody meant to make.
        """
        prose = _retry_driver_docstring()
        unlabelled = _unlabelled_driver_callers()
        liars = _prose_liars(prose, _DOCUMENTED_SELF_ATTRIBUTING, unlabelled)

        assert not liars, (
            f"`{_RETRY_DRIVER_NAME}`'s docstring names these callers as omitting `label=`, "
            f"and every one of them now PASSES a label: {liars}.\n\n"
            f"  docstring names as label-less : "
            f"{sorted(caller for caller in _DOCUMENTED_SELF_ATTRIBUTING if caller in prose)}\n"
            f"  callers that ACTUALLY pass no label : {sorted(unlabelled)}\n\n"
            "This is finding #151's SECOND half. The first was the missing label; the second "
            "was the sentence that licensed it — *'`bootstrap_session` and "
            "`execute_transaction`, which have their own attribution'* — TRUE of one and "
            "FALSE of the other, and it is the stated reasoning that made the omission look "
            "deliberate rather than like a hole.\n\n"
            "Fixing the behaviour without retiring the prose does not leave that sentence "
            "merely stale: it INVERTS it. The named function no longer uses the `None` "
            "default it is documented as using, and the next author reads that claim in the "
            "one place they look to decide whether THEIR caller needs a label — re-planting "
            "the exact belief that hid #151, in the exact function #151 is about. Measured: "
            "a build with the behaviour perfect and this prose untouched scores 515/0.\n\n"
            "Retire the clause in the SAME diff (finding #151, and DESIGN-LAW's rule that "
            "prose describing behaviour is DERIVED from it, never restated beside it)."
        )


# ---------------------------------------------------------------------------
# 10e-2. THE DRIVER'S `from error` UNIVERSAL IS FALSE — AND THE EXCEPTION IS ARCHITECTURAL.
#        (adversary-151b residual R1 / invariant I15 · LEAD-RULED 2026-07-20)
#
# `_txn.py:876-880` explains `last_conflict_cause` with an unqualified ∀: *"every caller that
# raises the signal does so ``from error`` (the original engine exception)"*. The whole
# `engine_error` extra — the artifact #151 exists to restore — is built on that premise.
#
# MEASURED: FOUR sites raise `from error` (`:1002`, `:1010`, `:1018`, `:1103`); `:1242`,
# inside `execute_transaction._attempt`, raises `RetryableConflictSignal()` BARE.
#
# THE LEAD INSPECTED `:1242` AND RULED: THE CODE CANNOT CONFORM, SO THE COMMENT MUST CHANGE.
# At that site there is no exception in scope AT ALL — the transactional caller detects a
# conflict by INSPECTING a returned response's `failed_statements`, not by catching a raise,
# so there is nothing to chain `from`. This is not an oversight; it is the architectural split
# the driver's OWN docstring already describes: *"the transactional caller reads a returned
# response's failed statements; every single-statement seam reads a RAISED exception."*
#
# SO THE PINS BELOW SPLIT THE POPULATION THE WAY THE CODE ACTUALLY DOES, and neither of them
# can be satisfied by deleting the sentence:
#   * the ∀ holds over the seams that raise FROM AN `except` HANDLER — that population is
#     derived structurally (being inside a handler IS "reads a RAISED exception"), so a new
#     seam that forgets `from error` goes red without anyone maintaining a list;
#   * and the comment must NAME whichever callers raise with no exception in scope, so the
#     exemption is documented WHERE THE PREMISE IS STATED rather than merely being true.
#
# The second pin therefore does more than correct prose: it makes the driver's own
# explanation carry the EVIDENCE for why `execute_transaction` is exempt from the label
# requirement §10's allowlist already grants it. Delete the comment and it goes red; leave the
# false universal and it goes red; name the exception and it goes green.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ConflictSignalRaise:
    """One ``raise RetryableConflictSignal`` site, with everything the pins need."""

    lineno: int
    enclosing: tuple[str, ...]
    """Every enclosing function, outermost first — so a nested `_attempt` can be named by
    either its own name or its parent's, and the pin holds no opinion on which reads better."""
    handler_name: str | None
    """The name bound by the innermost `except ... as NAME:` in scope, or `None` when the
    raise sits outside any handler — i.e. when there is no exception to chain from."""
    chained_from: str | None
    """The name in `raise ... from NAME`, or `None` for a bare raise."""


def _conflict_signal_raise_sites(source: str) -> list[_ConflictSignalRaise]:
    """Every ``raise RetryableConflictSignal(...)`` in ``source``, classified.

    The handler stack is reset at every function boundary: a closure defined inside an
    ``except`` block does not run with that block's name bound (Python deletes it on the way
    out), so crediting its raises to the enclosing handler would be a lie in the safe-looking
    direction — it would report a bare raise as chainable.
    """
    sites: list[_ConflictSignalRaise] = []

    def raised_name(node: ast.expr | None) -> str | None:
        if isinstance(node, ast.Call):
            node = node.func
        return node.id if isinstance(node, ast.Name) else None

    def visit(node: ast.AST, functions: tuple[str, ...], handlers: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                visit(child, (*functions, child.name), ())
                continue
            if isinstance(child, ast.ExceptHandler):
                visit(child, functions, (*handlers, child.name) if child.name else handlers)
                continue
            if isinstance(child, ast.Raise) and raised_name(child.exc) == _RETRY_SIGNAL_NAME:
                sites.append(
                    _ConflictSignalRaise(
                        lineno=child.lineno,
                        enclosing=functions,
                        handler_name=handlers[-1] if handlers else None,
                        chained_from=raised_name(child.cause),
                    )
                )
            visit(child, functions, handlers)

    visit(ast.parse(source), (), ())
    return sites


def _explanation_above(source: str, variable: str) -> list[str] | None:
    """The contiguous ``#`` comment block immediately above ``variable``'s annotated assignment.

    ``None`` when the assignment itself cannot be found (the pin then fails loudly rather than
    passing over a variable it could not locate) and ``[]`` when the assignment is there but
    carries no explanation at all — which is the "deleted the comment" build.
    """
    declared_at: int | None = None
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == variable
        ):
            declared_at = node.lineno
            break
    if declared_at is None:
        return None

    comments: dict[int, str] = {
        token.start[0]: token.string
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
    }
    block: list[str] = []
    lineno = declared_at - 1
    while lineno in comments:
        block.append(comments[lineno])
        lineno -= 1
    return list(reversed(block))


class TestTheSignalsChainingUniversalHoldsOverThePopulationItIsTrueOf:
    """**adversary-151b R1 / invariant I15.** The driver's `engine_error` extra is only as
    good as the chaining premise it rests on — so the premise is pinned where it is TRUE, and
    the architectural exception is pinned as an exception.
    """

    def test_the_raise_site_walker_is_not_silently_finding_nothing(self) -> None:
        """**THE REACH CONTROL.** Both pins below quantify over a set the walker produces, and
        the empty set satisfies both. Assert the reach, or the reach becomes the bug.
        """
        sites = _conflict_signal_raise_sites(_seam_module_source())

        assert len(sites) >= _MIN_KNOWN_CONFLICT_SIGNAL_RAISE_SITES, (
            f"the walker found {len(sites)} `raise {_RETRY_SIGNAL_NAME}` site(s) "
            f"({[site.lineno for site in sites]}) — this contract was written against "
            f"{_MIN_KNOWN_CONFLICT_SIGNAL_RAISE_SITES} (three in the session bootstrap's "
            f"statement bodies, one in `run_query`'s attempt, one in the transactional "
            f"caller's). Either seams were consolidated (good — lower this floor "
            f"deliberately) or the walker broke and both pins below are vacuous."
        )

    def test_the_walker_TELLS_APART_a_chained_raise_from_a_bare_one(self) -> None:
        """**POSITIVE CONTROL.** A classifier that reported everything as chained would make
        the ∀ pin vacuous; one that reported everything as bare would make the naming pin
        unsatisfiable. Both directions are shown on synthetic source.
        """
        source = """
async def _seam():
    try:
        await connection.query("...")
    except Exception as error:
        raise RetryableConflictSignal() from error

async def _transactional():
    if failed:
        raise RetryableConflictSignal()
"""
        classified = [
            (site.enclosing, site.handler_name, site.chained_from)
            for site in _conflict_signal_raise_sites(source)
        ]

        assert classified == [
            (("_seam",), "error", "error"),
            (("_transactional",), None, None),
        ], (
            f"the walker classified {classified}. It must see BOTH shapes and must record "
            f"the handler name and the chained name separately — a classifier that conflates "
            f"them cannot tell 'chained correctly' from 'nothing was in scope to chain'."
        )

    def test_every_signal_raised_FROM_AN_EXCEPT_HANDLER_chains_that_exception(self) -> None:
        """**GREEN TODAY, BY DESIGN** — all four handler-borne raises already chain. This is
        the ∀ half of R1: pinned over the population where the driver's premise is TRUE, so a
        new single-statement seam that raises the signal bare inside its `except` goes red
        here instead of silently emptying `engine_error` for its own exhaustion records.

        The population is DERIVED, not listed: being lexically inside `except ... as NAME:` is
        what "reads a RAISED exception" means structurally, so no one has to maintain a set.
        """
        unchained = [
            site
            for site in _conflict_signal_raise_sites(_seam_module_source())
            if site.handler_name is not None and site.chained_from != site.handler_name
        ]

        assert not unchained, (
            f"these `raise {_RETRY_SIGNAL_NAME}` sites are inside an `except ... as NAME:` "
            f"handler and do NOT chain that exception:\n  "
            + "\n  ".join(
                f"{_SEAM_MODULE}:{site.lineno} in {'.'.join(site.enclosing)}() — caught as "
                f"{site.handler_name!r}, raised `from {site.chained_from}`"
                for site in unchained
            )
            + f"\n\nThe driver stashes `{_LAST_CONFLICT_CAUSE_VARIABLE} = signal.__cause__` "
            "and puts it on the exhaustion record as `engine_error`. An unchained raise "
            "leaves that empty, and the operator is back to an attempt count under a message "
            "promising 'the full engine detail' — finding #151's exact harm, arriving through "
            "a different door. Write `raise RetryableConflictSignal() from <the caught name>`."
        )

    def test_the_drivers_explanation_NAMES_every_caller_that_raises_UNCHAINABLY(self) -> None:
        """**RED TODAY.** The comment above `last_conflict_cause` claims *"every caller that
        raises the signal does so ``from error``"*. `_txn.py:1242` does not, and cannot: the
        transactional caller detects its conflict by INSPECTING a returned response's failed
        statements, so at that raise there is no exception in scope to chain.

        LEAD RULING (2026-07-20): the code cannot conform, so the COMMENT changes. And it must
        change by NAMING the exception rather than by dropping the claim — this pin fails on a
        deleted comment exactly as it fails on a false one.

        WHY NAMING IS THE RIGHT REPAIR AND NOT BOOKKEEPING: `execute_transaction` is also the
        one body §10's allowlist exempts from `label=`. Naming it HERE, where the chaining
        premise is stated, is what makes that exemption's reason visible at the premise it
        depends on — the driver's own explanation ends up carrying the evidence instead of the
        reader having to reconstruct it from two files.

        DERIVED, NOT MATCHED: the required names come from the AST walk, and the check is
        membership in the comment block the tokenizer finds above the declaration. Any wording
        passes as long as it names the callers that genuinely cannot chain — and if a future
        refactor makes every raise chainable, the required set empties and the unqualified
        universal becomes true again, so this pin correctly stops asking for anything.
        """
        source = _seam_module_source()
        explanation = _explanation_above(source, _LAST_CONFLICT_CAUSE_VARIABLE)

        assert explanation is not None, (
            f"`{_LAST_CONFLICT_CAUSE_VARIABLE}` has no annotated declaration in "
            f"{_SEAM_MODULE}, so this pin cannot find the explanation it grades. If the "
            f"variable was renamed, move `_LAST_CONFLICT_CAUSE_VARIABLE` with it — do not "
            f"leave the pin pointing at a name that no longer exists."
        )
        assert explanation, (
            f"`{_LAST_CONFLICT_CAUSE_VARIABLE}` now carries NO explanatory comment at all. "
            f"Deleting the sentence is not a repair: the `engine_error` extra rests on a "
            f"premise about how callers raise the signal, and an unstated premise is one the "
            f"next author cannot check. State it — accurately."
        )

        prose = "\n".join(explanation)
        unnameable = [
            site
            for site in _conflict_signal_raise_sites(source)
            if site.handler_name is None
            and not any(function in prose for function in site.enclosing)
        ]

        assert not unnameable, (
            f"the explanation above `{_LAST_CONFLICT_CAUSE_VARIABLE}` states a universal "
            f"about how callers raise the signal, and these sites raise it with NO exception "
            f"in scope — un-chainable by construction — while the comment names neither them "
            f"nor any function enclosing them:\n  "
            + "\n  ".join(
                f"{_SEAM_MODULE}:{site.lineno} in {'.'.join(site.enclosing)}()"
                for site in unnameable
            )
            + "\n\nThe comment currently reads:\n  "
            + "\n  ".join(explanation)
            + "\n\nThat ∀ is FALSE, and the `engine_error` extra is built on it: the day "
            "anyone passes a `label=` at one of the sites above, the record silently gets the "
            "driver's `\"\"` fallback while this comment says that cannot happen.\n\n"
            "The code cannot conform (LEAD RULING): the transactional caller reads a RETURNED "
            "response's failed statements rather than catching a raise, exactly as this "
            "driver's own docstring describes — so there is nothing to chain `from`. Qualify "
            "the claim to the callers that raise from an `except` handler, and NAME the "
            "caller that does not, with its reason. Naming it here is also where the reader "
            "learns why that same body is the one §10's allowlist exempts from `label=`."
        )


# ---------------------------------------------------------------------------
# 10f. SCOUT'S TWO BEST-EFFORT SEAMS ARE ATTRIBUTED BY LABEL TOO — AND THE EXEMPTION THAT
#      USED TO COVER THEM CARRIED A CLAUSE THAT WAS FALSE.
#      (finding #151 · REPORT-audit-151-cold.md §FINDING · OPERATOR RULING, this wave)
#
# THE COLD AUDIT'S NO-GO, verbatim. §10's allowlist exempted `_consume_live` on this
# evidence: *"swallows `TxnContentionExhaustedError` and logs its own
# `command_subscriber.live_unavailable` record with `exc_info=True`. The exception never
# escapes, AND THE ENGINE'S TEXT RIDES THE TRACEBACK."*
#
# The final clause was MEASURED FALSE. The driver's `raise TxnContentionExhaustedError`
# sits OUTSIDE the `except RetryableConflictSignal` block, so `__cause__` and `__context__`
# are both `None`: the engine's own "can be retried" text does NOT ride the traceback.
# `exc_info=True` captured only the driver's "see the server log for the full engine
# detail" sentence — over a record that, being unlabelled, held `{attempts,
# elapsed_seconds}` and nothing else. **A hint pointing at a log that holds nothing: #151's
# exact false-promise shape, reproduced inside #151's own contract**, and green at every
# gate because §10's exemption check reads an evidence string for PRESENCE and a length
# floor and CANNOT READ IT FOR TRUTH. That is not a bug in §10 — it is the reason this
# section exists. *A DIAGNOSIS IS NOT AN INSTRUMENT*: the repair for a false claim about
# behaviour is a pin on the BEHAVIOUR, never a better sentence.
#
# THE OPERATOR RULED: make the aspiration TRUE rather than reword it. Both seams pass a
# `label=`, so the driver's ONE `store.retry.exhausted` record carries the engine's own
# text server-side — where ledger #31 says the detail belongs — and both LEAVE the
# allowlist. `execute_transaction` is the only exemption left.
#
# THE SHAPE IS §10d's, DELIBERATELY: label + engine text, `url=None`. Neither seam has a
# url in scope, for the same structural reason `_scout_query` has none — `CommandSubscriber`
# holds a `connect` CALLABLE rather than an address — so the url gap is INHERITED here, and
# pinned as a KNOWN BOUND in both directions rather than left to be rediscovered from an
# outage (CLAUDE.md: *when you cannot close a hole, pin it*).
# ---------------------------------------------------------------------------


@dataclass
class _ForeverConflictingSubscription:
    """A connection whose every ``subscribe_live`` conflicts — scout's LIVE seam, exhausted.

    Deliberately answers ONLY ``subscribe_live``. ``_consume_live`` must never reach the
    drain on this fixture: a fake that also answered ``query`` would let a wrong build
    satisfy this section from a different code path, and the retry count below would stop
    being a statement about the subscription attempt.
    """

    calls: int = field(default=0, init=False)

    async def subscribe_live(self, live_uuid: Any) -> Any:
        self.calls += 1
        if self.calls > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError("unbounded retry in scout's live-subscription seam")
        raise _conflict_error()


@dataclass
class _ForeverConflictingKill:
    """A connection whose every ``kill`` conflicts — scout's cleanup seam, exhausted."""

    calls: int = field(default=0, init=False)

    async def kill(self, live_uuid: Any) -> None:
        self.calls += 1
        if self.calls > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError("unbounded retry in scout's kill seam")
        raise _conflict_error()


async def _drive_scouts_live_subscription_to_exhaustion(connection: Any) -> None:
    """Exhaust ``_consume_live``. It SWALLOWS by design, so nothing propagates from here."""
    await _subscriber()._consume_live(connection, "live-uuid")


async def _drive_scouts_kill_to_exhaustion(connection: Any) -> None:
    """Exhaust ``_safe_kill``. Best-effort cleanup — it SWALLOWS by design."""
    await _subscriber()._safe_kill(connection, "live-uuid")


async def _drive_scouts_query_to_exhaustion(connection: Any) -> None:
    """Exhaust ``_scout_query`` — §10d's seam, which PROPAGATES (its disposition differs)."""
    with pytest.raises(TxnContentionExhaustedError):
        await scout_module._scout_query(connection, "SELECT * FROM command")


async def _scout_seam_exhaustion_record(
    caplog: pytest.LogCaptureFixture, drive: Callable[[], Awaitable[None]]
) -> logging.LogRecord:
    """Drive ONE scout seam to exhaustion; return its ONE ``store.retry.exhausted`` record.

    ``caplog`` is CLEARED first so a single test may drive several seams in sequence and
    still read *the* record for each — :func:`_exhaustion_record` refuses to take the first
    of several, which is what lets the three-way distinctness pin below attribute each
    observed label to the seam that actually emitted it.

    IT IS ALSO THE REACH CONTROL, and that is not incidental: a seam that never ran emits
    ZERO records, and :func:`_exhaustion_record` fails loudly on zero. No pin in this
    section can go vacuously green by simply not driving anything.
    """
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger=_TXN_LOGGER):
        await drive()
    return _exhaustion_record(caplog)


def _bootstrap_labels() -> set[str]:
    """The session bootstrap's three canonical rejection events, read from the seam module.

    Read live rather than re-typed: these are the labels a wrong build is most likely to
    BORROW to satisfy a presence check, and a copy of them here would go stale exactly when
    it mattered.
    """
    names = (
        "_BOOTSTRAP_DEFINE_NAMESPACE_LABEL",
        "_BOOTSTRAP_SELECT_DATABASE_LABEL",
        "_BOOTSTRAP_DEFINE_DATABASE_LABEL",
    )
    found = {getattr(txn_module, name, None) for name in names}
    return {label for label in found if isinstance(label, str)}


# A label no production caller may ever use. It exists only for the control below, which
# proves the driver's `engine_error` extra CAN be the empty string on a LABELLED call —
# the wrong build the two engine-text pins in this section exist to refuse.
_UNCHAINED_CONTROL_LABEL = "test.control.labelled_but_unchained.rejected"


class TestScoutsBestEffortSeamsAreAttributedByLabelOnly:
    """**THE COLD AUDIT'S NO-GO, CLOSED BY MAKING THE CLAIM TRUE (operator ruling).**

    `_consume_live` and `_safe_kill` swallow their exhaustion — that is correct and stays.
    What was wrong was believing the swallow PRESERVED the engine's text. It does not, and
    the only place that text can now survive is the driver's own record, which requires a
    label. These pins grade the record, not the sentence.
    """

    async def test_scouts_live_subscription_exhaustion_carries_a_label_OF_ITS_OWN(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """RED today: `scout.py:571` passes no `label`, so the driver suppresses all three
        extras and this seam's exhaustion is as unattributable as the bootstrap's was.

        The label is checked as a PROPERTY, never against a constant this file declares —
        the same choice §10d made and for the same reason: scout's own log events are
        `command_subscriber.*` rather than `scout.*`, so any substring pin on a naming
        vocabulary would be a C-DEF trap for a builder doing the right thing. What IS
        refused is a label BORROWED from the session bootstrap, which satisfies a presence
        check while sending the operator to the wrong emitter.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _ForeverConflictingSubscription()

        record = await _scout_seam_exhaustion_record(
            caplog,
            lambda: _drive_scouts_live_subscription_to_exhaustion(cast("Any", connection)),
        )
        label = getattr(record, "label", None)

        assert connection.calls > 1, (
            f"`subscribe_live` was attempted {connection.calls} time(s) under a sustained "
            f"conflict, so this fixture reached exhaustion without ever RETRYING. Every "
            f"assertion below would then be grading a path that is not the one #151 is "
            f"about — fix the fixture (or the seam), never the pin."
        )
        assert isinstance(label, str) and label, (
            f"scout's live-subscription seam exhausted and logged label={label!r}. The "
            f"exception is swallowed, so the OPERATOR-FACING artifact is this record and "
            f"only this record — and unlabelled, the driver suppresses `label`, `url` AND "
            f"`engine_error` on it. The traceback does not rescue it: the driver raises the "
            f"exhaustion error BARE, so `__cause__` is `None` and the engine's text is "
            f"nowhere (the cold audit measured exactly this — the clause claiming otherwise "
            f"is the defect this section replaced). Pass a canonical event name as `label=` "
            f"at `scout.py:571`."
        )
        assert label not in _bootstrap_labels(), (
            f"scout's live-subscription seam labelled its exhaustion {label!r} — a label "
            f"that belongs to the session bootstrap. A borrowed label satisfies a presence "
            f"check and points the operator at the wrong emitter, which is worse than no "
            f"label at all."
        )

    async def test_scouts_live_subscription_exhaustion_carries_the_ENGINES_OWN_TEXT(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """RED today, and it is the HALF THE FALSE CLAUSE PROMISED.

        The retired evidence said the engine's text "rides the traceback". It does not, and
        it never did. Once labelled, the ONE place it survives is this record's
        `engine_error` — so this pin asserts the engine's ACTUAL conflict text is IN it,
        not merely that the key exists. A build that lands a label but raises the signal
        BARE (no `from error`) gets `engine_error == ""` from the driver's own fallback and
        fails HERE while the label pin above stays green; that empty-string build is
        demonstrated live by
        `test_a_LABELLED_call_that_raises_the_signal_BARE_logs_an_EMPTY_engine_error`.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _ForeverConflictingSubscription()

        record = await _scout_seam_exhaustion_record(
            caplog,
            lambda: _drive_scouts_live_subscription_to_exhaustion(cast("Any", connection)),
        )
        engine_error = str(getattr(record, "engine_error", ""))

        assert _LIVE_CONFLICT_TEXT in engine_error, (
            f"scout's live-subscription seam exhausted and its record carries "
            f"engine_error={engine_error!r}; the engine said {_LIVE_CONFLICT_TEXT!r}. This "
            f"assertion checks CONTAINMENT of the engine's own words — an empty string, a "
            f"placeholder, or a re-worded summary all fail it, and all three make the log "
            f"look complete while holding nothing the operator can act on. If the label "
            f"landed but this is empty, the attempt body raised "
            f"`{_RETRY_SIGNAL_NAME}()` without `from error`, so the driver had no cause to "
            f"quote."
        )

    async def test_scouts_kill_exhaustion_carries_a_label_OF_ITS_OWN(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """RED today: `scout.py:599` passes no `label`.

        SEPARATE FROM THE LIVE SEAM'S PIN ON PURPOSE. A build that labels one of scout's two
        best-effort calls and forgets the other is the likeliest wrong build here — the two
        sit sixteen lines apart in one class — and a single pin over "scout's best-effort
        paths" would go green on it.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _ForeverConflictingKill()

        record = await _scout_seam_exhaustion_record(
            caplog, lambda: _drive_scouts_kill_to_exhaustion(cast("Any", connection))
        )
        label = getattr(record, "label", None)

        assert connection.calls > 1, (
            f"`kill` was attempted {connection.calls} time(s) under a sustained conflict, "
            f"so this fixture exhausted without ever RETRYING — the assertions below would "
            f"be grading the wrong path."
        )
        assert isinstance(label, str) and label, (
            f"scout's kill seam exhausted and logged label={label!r}. Best-effort cleanup "
            f"still swallows the exception — which is exactly why the record is the only "
            f"artifact left, and why an unlabelled one loses the engine's text with nothing "
            f"downstream to recover it. Pass a canonical event name as `label=` at "
            f"`scout.py:599`."
        )
        assert label not in _bootstrap_labels(), (
            f"scout's kill seam labelled its exhaustion {label!r} — a label that belongs to "
            f"the session bootstrap. Borrowing one satisfies a presence check and misroutes "
            f"the operator."
        )

    async def test_scouts_kill_exhaustion_carries_the_ENGINES_OWN_TEXT(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """RED today. Same property as the live seam's, pinned independently for the same
        reason its label pin is: one seam labelled and the other not must go RED on the one
        that is not."""
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _ForeverConflictingKill()

        record = await _scout_seam_exhaustion_record(
            caplog, lambda: _drive_scouts_kill_to_exhaustion(cast("Any", connection))
        )
        engine_error = str(getattr(record, "engine_error", ""))

        assert _LIVE_CONFLICT_TEXT in engine_error, (
            f"scout's kill seam exhausted and its record carries "
            f"engine_error={engine_error!r}; the engine said {_LIVE_CONFLICT_TEXT!r}. "
            f"Containment of the engine's own words is the check — empty, placeholder and "
            f"paraphrase all fail it."
        )

    async def test_scouts_three_seams_label_their_exhaustion_THREE_DIFFERENT_WAYS(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**DERIVED, not declared** — three OBSERVATIONS compared to EACH OTHER.

        The per-seam pins above each compare an observation to a property. This one compares
        scout's three driver callers to one another, so it cannot be satisfied by any build
        in which one string reaches all three records — a module constant, a
        `label="command_subscriber.rejected"` copied twice, a shared default on a helper —
        however that string was obtained. A single shared scout label passes every
        presence check in this file and still tells an operator only that *something in the
        command channel* died, which is precisely the state #151 is about.

        The bootstrap's three labels are excluded by the same argument, one layer out: a
        borrowed label is a confidently WRONG attribution, and the driver's record is the
        artifact an operator reads at 3am.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        subscription_connection = _ForeverConflictingSubscription()
        kill_connection = _ForeverConflictingKill()
        query_connection = _ForeverConflictingQuery()

        observed = {
            "_consume_live": getattr(
                await _scout_seam_exhaustion_record(
                    caplog,
                    lambda: _drive_scouts_live_subscription_to_exhaustion(
                        cast("Any", subscription_connection)
                    ),
                ),
                "label",
                None,
            ),
            "_safe_kill": getattr(
                await _scout_seam_exhaustion_record(
                    caplog,
                    lambda: _drive_scouts_kill_to_exhaustion(cast("Any", kill_connection)),
                ),
                "label",
                None,
            ),
            "_scout_query": getattr(
                await _scout_seam_exhaustion_record(
                    caplog,
                    lambda: _drive_scouts_query_to_exhaustion(cast("Any", query_connection)),
                ),
                "label",
                None,
            ),
        }

        assert len(set(observed.values())) == len(observed), (
            f"scout's three driver callers labelled their exhaustion {observed} — the "
            f"values must be PAIRWISE DISTINCT, and this assertion counts distinct values "
            f"against the number of seams. Two seams sharing a label (or both carrying "
            f"`None`) makes the record name the CHANNEL rather than the STATEMENT, which is "
            f"the whole of what a label is for: an operator lands on WHICH of the three "
            f"died, not merely that one did."
        )
        borrowed = sorted(
            (seam, label) for seam, label in observed.items() if label in _bootstrap_labels()
        )
        assert not borrowed, (
            f"these scout seams labelled their exhaustion with a SESSION BOOTSTRAP label: "
            f"{borrowed}. Distinct-from-each-other is not enough — three scout labels that "
            f"are all borrowed from `bootstrap_session` are three confidently wrong "
            f"attributions."
        )

    async def test_scouts_live_subscription_exhaustion_carries_NO_url_a_KNOWN_BOUND(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**THIS IS A KNOWN BOUND (#151), PINNED — not a passing gate.**

        `_consume_live` is attributed by LABEL ONLY, inheriting §10d's bound for the same
        structural reason: it holds a bare `connection`, and `CommandSubscriber` holds a
        `connect` callable rather than an address. Closing it means threading a url through
        scout's whole connection ownership — a design change, ruled a separate wave.

        **IF YOU CLOSED THIS DELIBERATELY, DELETE THIS PIN AND SAY SO IN THE SAME DIFF** —
        then extend the label pin above to assert the url too, so the seam does not go from
        pinned-partial to unpinned-complete.

        **NAMED RE-OPEN TRIGGER:** the day `CommandSubscriber` takes a url alongside its
        `connect` factory, or the command channel joins the ten `_query` seams' shape. It is
        the SAME trigger §10d names, and both pins must be retired together.

        ⚠ DISCLOSED, exactly as §10d disclosed it: on the UNFIXED tree this assertion does
        not discriminate — the record carries no url because it carries no label either, so
        `url is None` holds for the wrong reason. It becomes a real tripwire the moment the
        label lands, which is the same diff that turns the pins above green.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _ForeverConflictingSubscription()

        record = await _scout_seam_exhaustion_record(
            caplog,
            lambda: _drive_scouts_live_subscription_to_exhaustion(cast("Any", connection)),
        )

        assert getattr(record, "url", None) is None, (
            f"scout's live-subscription seam now logs url={getattr(record, 'url', None)!r}. "
            f"**This is a KNOWN BOUND (#151) — scout's best-effort seams are attributed by "
            f"LABEL ONLY, because `_consume_live` has no url in scope. If you closed this "
            f"deliberately, delete this pin and say so in the same diff**, and extend the "
            f"label pin above to assert the url as well."
        )

    async def test_scouts_kill_exhaustion_carries_NO_url_a_KNOWN_BOUND(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**THIS IS A KNOWN BOUND (#151), PINNED — not a passing gate.**

        `_safe_kill`'s bound is stricter than its sibling's and worth stating: it is a
        `@staticmethod`, so it does not even hold the subscriber, let alone a url. Same
        ruling, same re-open trigger, same instruction.

        **IF YOU CLOSED THIS DELIBERATELY, DELETE THIS PIN AND SAY SO IN THE SAME DIFF.**

        ⚠ DISCLOSED: does not discriminate on the UNFIXED tree (no label ⇒ no url either).
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)
        connection = _ForeverConflictingKill()

        record = await _scout_seam_exhaustion_record(
            caplog, lambda: _drive_scouts_kill_to_exhaustion(cast("Any", connection))
        )

        assert getattr(record, "url", None) is None, (
            f"scout's kill seam now logs url={getattr(record, 'url', None)!r}. **This is a "
            f"KNOWN BOUND (#151) — attributed by LABEL ONLY. If you closed this "
            f"deliberately, delete this pin and say so in the same diff**, and extend the "
            f"label pin above to assert the url as well."
        )

    async def test_a_LABELLED_call_that_raises_the_signal_BARE_logs_an_EMPTY_engine_error(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """**POSITIVE CONTROL for the two engine-text pins in this section.**

        Those pins assert the engine's words are IN `engine_error`. A probe that reports
        "the text is present" because it cannot see an absence reports that for everything —
        so here is the absence, driven live: a call that passes a `label=` and whose attempt
        raises `RetryableConflictSignal()` BARE (nothing to chain `from`) exhausts into a
        record that is labelled and whose `engine_error` is the EMPTY STRING, straight from
        the driver's own `"" if last_conflict_cause is None` fallback.

        This is the wrong build that matters: a builder can satisfy every label pin above
        and still lose the engine's text, and the failure would be invisible without this
        leg. It also pins the driver's fallback itself — the day `engine_error` stops being
        `""` for an unchained cause, the two containment pins change meaning and this goes
        RED first, naming why.
        """
        _silence_sleep(monkeypatch)
        _set_default_deadline(monkeypatch, 0.0)

        async def _labelled_but_unchained() -> None:
            raise txn_module.RetryableConflictSignal()

        with caplog.at_level(logging.WARNING, logger=_TXN_LOGGER):
            with pytest.raises(TxnContentionExhaustedError):
                await txn_module.retry_on_conflict(
                    _labelled_but_unchained, label=_UNCHAINED_CONTROL_LABEL
                )

        record = _exhaustion_record(caplog)

        assert getattr(record, "label", None) == _UNCHAINED_CONTROL_LABEL, (
            "CONTROL FAILED: a call passing `label=` did not put that label on its "
            "exhaustion record, so this control cannot demonstrate the labelled-but-empty "
            "build the engine-text pins exist to refuse."
        )
        assert getattr(record, "engine_error", None) == "", (
            f"CONTROL FAILED: an attempt raising `{_RETRY_SIGNAL_NAME}()` with no `from` "
            f"clause logged engine_error="
            f"{getattr(record, 'engine_error', None)!r} rather than the empty string. Either "
            f"the driver now recovers a cause from somewhere (in which case the containment "
            f"pins above are no longer testing what they claim, and this control is the "
            f"right place to find that out) or this probe is not reaching the fallback at "
            f"all — in which case the containment pins have never been shown able to fail."
        )
