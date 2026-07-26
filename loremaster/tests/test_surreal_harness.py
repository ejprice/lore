"""Pins that ``_surreal_harness``'s retry policy IS the store seam's, not a copy of it
(finding #150).

BUG: the harness hand-rolled its own retry substrate — a private 5-attempt budget, a
private linear backoff, and a private literal copy of the engine's conflict marker — and
used it for exactly ONE of the three operations that can hit a retryable conflict. The
other two (``connect_admin``'s three-statement session bootstrap, and ``drop_database``'s
``use()``) were BARE, UNRETRIED ``await``s. Under the standing ``-n auto`` runner that
gave every ``[real]`` fixture in the suite a stochastic setup-failure rate: the identical
defect ``loremaster.store._txn.bootstrap_session`` was BUILT to close on the production
side (probed live, 16-way concurrent: 6.2%-34.4% of virgin first-connects lost).

THE FIX routes ALL THREE sites through the ONE shared seam in
``loremaster.store._txn`` — ``bootstrap_session`` for ``connect_admin``, and
``retry_on_conflict`` + ``is_retryable_conflict_error`` (via the single harness-local
classify-and-signal helper ``_run_under_store_retry_seam``) for the other two. The
harness now owns NO CONFLICT-RETRY policy at all: no conflict budget, no backoff, no
marker. (``call_until_recovered`` does own an attempt bound — it is a lifecycle RECOVERY
probe, a different concern, and it correctly does NOT route through ``_txn``.)

WHY THESE TESTS DO NOT DEPEND ON THE LIVE RACE FIRING: the live conflict is a genuine,
rare race against background server work — a test that only passes when that race happens
to occur is not a real pin. Instead these monkeypatch the SDK connection factory
(``_surreal_harness.AsyncSurreal``) with a fake connection whose ``query``/``use`` are
scripted to raise the EXACT engine error (or a non-retryable one) on demand, so the
retry/no-retry decision is pinned deterministically, every run.

AND WHY THAT IS NOT ENOUGH: routing is not sharing. A harness that CALLS the shared
driver while keeping its own budget underneath it is a private copy wearing the shared
name, and it passes every pin that only checks a retry happened. So the load-bearing pin
here is :class:`TestTheHarnessRetryPolicyIsTheSeamsPolicy`, which MUTATES the seam's own
constants at run time and asserts the harness's OBSERVED attempt count moves with them,
with a positive control showing the same assertion at the unmutated values.

AND ITS REACH IS A CHECKED VARIABLE, NOT AN ASSUMPTION (CLAUDE.md: "a runtime gate is an
invariant only over code it actually RUNS"). That mutation proof originally reached 2 of
the 5 operations the harness puts under the seam, and neither ``use()`` was among them —
the call this repo's own probe named "the call that actually loses the bootstrap race"
(blindreader-150 F6). So the operations are now DISCOVERED by driving both functions
against the fake, and :data:`_OPERATION_PROBES` must cover the discovered set EXACTLY: put
a sixth operation under the seam and the reach pin goes RED until it has a constant-tied
probe of its own.

THE OTHER THREE PROPERTIES pinned here, each from a grader finding on the first fix:
attribution (the seam's exhaustion record must carry the label, the url and WHAT THE
ENGINE SAID — blindreader-150 F1), budget COMPOSITION (several operations driven by one
caller share ONE wall-clock budget rather than each resolving a fresh copy — F2 / audit
R1+R4), and socket hygiene on the FAILURE paths (F10 / audit R5).

------------------------------------------------------------------------------
HOW TO RESOLVE THE ``blindreader-150 F*`` / ``audit-150 R*`` CITATIONS IN THIS FILE.

They are review-pass identifiers from finding **#150**'s review wave. The reports they
name (``REPORT-blindreader-150.md``, ``REPORT-audit-150*.md``) were ARCHIVED at
``7d2ff44`` and resolve, section-exactly, under
``docs/plans/v2/receipts/2026-07-20-150/`` (#152). Repo law now ARCHIVES a wave's reports
into that tree at close-out rather than deleting them, precisely so a citation like these
resolves — the old delete-before-image-build rule was #152's root cause (#153). Their
durable addresses remain the ledger row **#150** (this wave's subject; **#151** for the
one defect deliberately left open) and the wave's commits, in order:

    6be78d6 RED  ·  0734d78 route  ·  20e7635 attribute/compose/release
    4659056 repair the instruments  ·  fff1382 + 9d4b48d the counts and the reach

Every citation below states its own substance inline; none of them is a pointer a
reader must follow to act.

**#151 IS CLOSED, AND THIS FILE NO LONGER PINS IT AS A BOUND.** This file used to carry
``test_the_bootstrap_paths_exhaustion_is_UNATTRIBUTED_a_known_bound``, which ASSERTED that
the ``connect_admin`` path's exhaustion record had NO ``label`` — a hole pinned rather than
closed, whose stated re-open trigger was "the day ``bootstrap_session`` passes a label".
That day is this diff: ``_txn.bootstrap_session`` now takes a required keyword-only ``url``
and labels each of its three statements, so the bound is GONE and the pin that asserted it
is DELETED rather than weakened — weakening it to keep it green would re-hide the defect it
was built to force a conversation about. What replaces it is
:class:`TestTheBootstrapPathsExhaustionIsAttributable`, which asserts the attribution that
is now present, on all three statements.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import _surreal_harness
import pytest
from _surreal_harness import SurrealEnv
from loremaster.store import _txn as txn_module
from pydantic import SecretStr
from surrealdb.errors import QueryError

# A fake connection target; the real topology is irrelevant since ``AsyncSurreal``
# itself is monkeypatched to return the fake below.
_FAKE_ENV = SurrealEnv(
    url="ws://127.0.0.1:19999/rpc",
    user="root",
    password=SecretStr("fake"),
    namespace="lore_test",
    database="test_fake_db",
    dim=8,
)

# The exact live message reported in the bug (surrealdb.errors.QueryError, kind "Query").
# Its retryable-conflict marker is the seam's ``_txn._RETRYABLE_CONFLICT_MARKER``
# ("can be retried") — the ONE authority; the harness no longer declares a copy.
_CONFLICT_MESSAGE = "Transaction conflict: Resource busy. This transaction can be retried"

# A same-shaped ``QueryError`` that is emphatically NOT the retryable conflict —
# a genuine domain rejection teardown must never silently swallow.
_NON_RETRYABLE_MESSAGE = "Specified database does not exist"

# Enough scripted conflicts to outlast any give-up bound the seam could impose (its
# structural ceiling is 64), so a sustained-conflict fixture never accidentally
# "succeeds" by running off the end of its script.
_SUSTAINED_CONFLICTS = 500

# The mutated ceiling the sharing pin moves the seam's to. Deliberately a value that
# is NOT the seam's real ceiling (64), NOT its attempt floor (5), and NOT any budget
# the deleted harness copy used (5) — so an observed count of 7 can only have come
# from reading the seam's live constant.
_MUTATED_ATTEMPT_CEILING = 7

# The three operation keys the fake routes on, and the statement text each matches.
_DEFINE_NAMESPACE = "DEFINE NAMESPACE"
_DEFINE_DATABASE = "DEFINE DATABASE"
_REMOVE_DATABASE = "REMOVE DATABASE"

# --- #151: the bootstrap-attribution fixture values ---------------------------------
# A url used by the BOOTSTRAP attribution pins and by NOTHING else in this tree.
#
# WHY IT IS NOT `_FAKE_ENV.url`: the defect being closed is that `bootstrap_session`
# carried no url at all, and the fix threads the CALLER's url through a new required
# parameter. A pin that asserted `_FAKE_ENV.url` would be satisfied by a build that
# hardcoded a url, defaulted one, or read some module global that happened to hold the
# same value — parameter-value MONOCULTURE, which this repo's own law names as a defect
# class that has produced a blocker four times. This value is an RFC-5737 TEST-NET-2
# address with a path that appears nowhere else in the repo, so the ONLY way for it to
# reach a log record is for the record to have been given THIS CALL's url.
#
# It is never dialed: `AsyncSurreal` is monkeypatched out in every pin that uses it.
_DISTINCT_BOOTSTRAP_URL = "ws://198.51.100.77:19998/rpc-151-bootstrap-attribution"

_DISTINCT_URL_ENV = SurrealEnv(
    url=_DISTINCT_BOOTSTRAP_URL,
    user="root",
    password=SecretStr("fake"),
    namespace="lore_test",
    database="test_fake_db",
    dim=8,
)

# The three labels `_txn.bootstrap_session` must attribute its three statements to, in
# BOOTSTRAP ORDER. Read as module constants off `_txn` (never re-declared here) for the
# same reason the harness reads `_TEARDOWN_*_LABEL` off `_surreal_harness`: the seam owns
# its own canonical event names, and a copy in a test is a copy that goes stale.
_BOOTSTRAP_LABEL_CONSTANTS = (
    "_BOOTSTRAP_DEFINE_NAMESPACE_LABEL",
    "_BOOTSTRAP_SELECT_DATABASE_LABEL",
    "_BOOTSTRAP_DEFINE_DATABASE_LABEL",
)

# --- budget-COMPOSITION fixture values --------------------------------------------
# A short seam deadline the composition pins mutate to, and a per-attempt delay that
# deliberately OVERSPENDS it on the caller's FIRST operation. The arithmetic is the
# whole pin, so it is stated explicitly rather than left for a reader to reconstruct:
# the first operation conflicts `_BUDGET_BURN_CONFLICTS` times (strictly BELOW the
# seam's attempt floor, so it can never give up) and then succeeds, spending
# (_BUDGET_BURN_CONFLICTS + 1) * _BUDGET_BURN_DELAY_SECONDS = 0.30s against a 0.20s
# budget. `asyncio.sleep` never returns EARLY, so the overspend is guaranteed, not
# probable — there is no flake here.
#
# A caller that COMPOSES therefore hands its NEXT operation a remaining budget of 0.0
# and that operation lands on the seam's attempt FLOOR. A caller that hands each
# operation a FRESH copy of the deadline gives the next one the full 0.20s, in which
# (with backoff silenced) it runs all the way to the seam's CEILING. Floor vs ceiling
# — two constants that must not coincide, which the pins assert before relying on it.
_COMPOSITION_DEADLINE_SECONDS = 0.20
_BUDGET_BURN_DELAY_SECONDS = 0.06
_BUDGET_BURN_CONFLICTS = 4


def _conflict_error() -> QueryError:
    return QueryError("Query", _CONFLICT_MESSAGE)


def _non_retryable_error() -> QueryError:
    return QueryError("Query", _NON_RETRYABLE_MESSAGE)


def _sustained_conflicts() -> list[BaseException | None]:
    """A script of DISTINCT conflict instances long enough to outlast any bound."""
    return [_conflict_error() for _ in range(_SUSTAINED_CONFLICTS)]


def _the_one_exhaustion_record(caplog: pytest.LogCaptureFixture) -> logging.LogRecord:
    """The single ``store.retry.exhausted`` record, or a loud failure.

    Exactly-once is itself a pinned property of the driver (``test_retry_seam.py``), so
    reading "the" record must never silently take the first of several.
    """
    records = [r for r in caplog.records if r.getMessage() == "store.retry.exhausted"]
    assert len(records) == 1, (
        f"expected exactly one `store.retry.exhausted` record, got {len(records)}"
    )
    return records[0]


@dataclass
class _FakeConnection:
    """Stand-in for the SDK connection ``connect_admin`` / ``drop_database`` drive.

    Two scripting modes, because the two paths under test issue different shapes:

    * ``query_outcomes`` — a flat, ordered script consumed one entry per ``query()``
      call, regardless of statement text. Used by the teardown pins, which issue
      exactly one kind of statement.
    * ``statement_outcomes`` — per-statement scripts keyed by a substring of the
      statement (``"DEFINE NAMESPACE"``, ``"REMOVE DATABASE"``, …), each consumed
      independently. Used by the ``connect_admin`` pins, whose bootstrap issues two
      DIFFERENT statements around a ``use()`` and would be ambiguous under a single
      counter. When ``statement_outcomes`` is non-empty it takes precedence, and a
      statement matching NO key succeeds — which is why every pin that cares also
      asserts against ``operations`` (below) rather than trusting a bare success.

    ``use_outcomes`` scripts ``use()`` the same way (empty ⇒ always succeeds), because
    session selection is one of the three sites that can hit a retryable conflict.

    An outcome that is a ``BaseException`` is raised; anything else is returned as the
    (unused) result. Running off the end of a script is a loud ``IndexError``, never a
    silent success.

    ``operations`` records every call in order, as ``"query:<statement>"`` /
    ``"use:<namespace>/<database>"``, so a pin can assert the exact bootstrap SEQUENCE
    — a build that reorders ``use()`` before ``DEFINE NAMESPACE`` would work against
    this fake but fail against the real engine.

    ``statement_delays`` / ``use_delay_seconds`` make an operation SPEND WALL CLOCK.
    They exist for the budget-COMPOSITION pins and nothing else: the only way to tell
    "these operations share one budget" from "each got a fresh copy of it" is to have an
    earlier operation actually consume the budget. The delay is keyed per statement (and
    separately for ``use()``) so a pin can slow down exactly the operation that must
    overspend, and leave the operation it is MEASURING running at full speed.
    """

    query_outcomes: list[BaseException | None] = field(default_factory=list)
    statement_outcomes: dict[str, list[BaseException | None]] = field(default_factory=dict)
    use_outcomes: list[BaseException | None] = field(default_factory=list)
    statement_delays: dict[str, float] = field(default_factory=dict)
    use_delay_seconds: float = 0.0
    query_calls: int = field(default=0, init=False)
    use_calls: int = field(default=0, init=False)
    statement_calls: dict[str, int] = field(default_factory=dict, init=False)
    operations: list[str] = field(default_factory=list, init=False)
    closed: bool = field(default=False, init=False)

    async def signin(self, credentials: dict[str, Any]) -> None:
        return None

    async def use(self, namespace: str, database: str) -> None:
        self.operations.append(f"use:{namespace}/{database}")
        index = self.use_calls
        self.use_calls += 1
        if self.use_delay_seconds:
            await asyncio.sleep(self.use_delay_seconds)
        if not self.use_outcomes:
            return None
        outcome = self.use_outcomes[index]
        if isinstance(outcome, BaseException):
            raise outcome
        return None

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        self.operations.append(f"query:{statement}")
        self.query_calls += 1
        for delayed_key, delay in self.statement_delays.items():
            if delayed_key in statement:
                await asyncio.sleep(delay)
        if self.statement_outcomes:
            for key, outcomes in self.statement_outcomes.items():
                if key in statement:
                    index = self.statement_calls.get(key, 0)
                    self.statement_calls[key] = index + 1
                    outcome = outcomes[index]
                    if isinstance(outcome, BaseException):
                        raise outcome
                    return outcome
            return None
        outcome = self.query_outcomes[self.query_calls - 1]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    async def close(self) -> None:
        self.closed = True


def _patch_connection(monkeypatch: pytest.MonkeyPatch, fake: _FakeConnection) -> None:
    monkeypatch.setattr(_surreal_harness, "AsyncSurreal", lambda url: fake)


def _silence_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Collapse the seam's jittered sleep to zero — a SPEED patch, not a policy one.

    The give-up predicate is untouched; only the duration of the sleeps between
    attempts is. Without this a sustained-conflict pin spends the seam's full
    wall-clock budget doing nothing but sleeping.
    """
    monkeypatch.setattr(txn_module, "_TXN_CONFLICT_BACKOFF_BASE_SECONDS", 0.0)
    monkeypatch.setattr(txn_module, "_TXN_CONFLICT_BACKOFF_CAP_SECONDS", 0.0)


def _seam_attempt_ceiling() -> int:
    """The seam's LIVE attempt ceiling, read at ASSERT time.

    Never a module-level ``from … import``: that freezes a value at import and the
    resulting assertion pins nothing (it would compare the harness's behaviour against
    a copy of the constant rather than against the constant).
    """
    ceiling = getattr(txn_module, "_TXN_CONFLICT_ATTEMPT_CEILING", None)
    assert isinstance(ceiling, int), (
        "the store seam's `_TXN_CONFLICT_ATTEMPT_CEILING` is gone or is no longer an "
        "int — the harness reads its retry bound from the seam, so there is no bound "
        "left to read"
    )
    return ceiling


def _seam_attempt_floor() -> int:
    """The seam's LIVE attempt floor, read at ASSERT time (see :func:`_seam_attempt_ceiling`)."""
    floor = getattr(txn_module, "_MAX_TXN_CONFLICT_ATTEMPTS", None)
    assert isinstance(floor, int), (
        "the store seam's `_MAX_TXN_CONFLICT_ATTEMPTS` is gone or is no longer an int"
    )
    return floor


class TestConnectAdminBootstrapsThroughTheSharedSeam:
    """``connect_admin``'s session bootstrap is retried — it used to be three bare awaits."""

    async def test_a_conflict_on_define_namespace_is_retried_then_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # One retryable conflict on the FIRST bootstrap statement, then success.
        # Pre-fix this raised straight out of `connect_admin` and failed the fixture.
        fake = _FakeConnection(
            statement_outcomes={
                _DEFINE_NAMESPACE: [_conflict_error(), None],
                _DEFINE_DATABASE: [None],
            }
        )
        _patch_connection(monkeypatch, fake)

        await _surreal_harness.connect_admin(_FAKE_ENV)

        # The exact bootstrap sequence, retry included: DEFINE NAMESPACE (conflicted,
        # retried), then use(), then DEFINE DATABASE. Order is load-bearing against the
        # real engine — `use()` on an unmaterialised namespace is a different failure.
        assert fake.operations == [
            f"query:DEFINE NAMESPACE IF NOT EXISTS {_FAKE_ENV.namespace}",
            f"query:DEFINE NAMESPACE IF NOT EXISTS {_FAKE_ENV.namespace}",
            f"use:{_FAKE_ENV.namespace}/{_FAKE_ENV.database}",
            f"query:DEFINE DATABASE IF NOT EXISTS {_FAKE_ENV.database}",
        ]

    async def test_a_conflict_on_the_use_call_is_retried_then_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The middle bootstrap operation is a `use()`, not a query — a retry that only
        # covered the two DDL statements would leave the same hole one step over.
        fake = _FakeConnection(
            statement_outcomes={_DEFINE_NAMESPACE: [None], _DEFINE_DATABASE: [None]},
            use_outcomes=[_conflict_error(), None],
        )
        _patch_connection(monkeypatch, fake)

        await _surreal_harness.connect_admin(_FAKE_ENV)

        assert fake.use_calls == 2
        assert fake.statement_calls[_DEFINE_DATABASE] == 1

    async def test_sustained_conflict_raises_the_seams_own_exhaustion_type(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # `TxnContentionExhaustedError` is the SEAM's type. A harness that had merely
        # grown a private retry loop of its own could raise the engine's `QueryError`
        # here and satisfy "it retried" — it could never raise THIS.
        _silence_backoff(monkeypatch)
        fake = _FakeConnection(statement_outcomes={_DEFINE_NAMESPACE: _sustained_conflicts()})
        _patch_connection(monkeypatch, fake)

        with pytest.raises(txn_module.TxnContentionExhaustedError) as exc_info:
            await _surreal_harness.connect_admin(_FAKE_ENV)

        ceiling = _seam_attempt_ceiling()
        assert exc_info.value.attempts == ceiling
        assert fake.statement_calls[_DEFINE_NAMESPACE] == ceiling

    async def test_a_non_retryable_rejection_propagates_on_the_first_attempt(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Everything that is not the engine's retryable conflict must propagate
        # UNTOUCHED with zero retries — the seam's own rule, inherited here.
        fake = _FakeConnection(statement_outcomes={_DEFINE_NAMESPACE: [_non_retryable_error()]})
        _patch_connection(monkeypatch, fake)

        with pytest.raises(QueryError) as exc_info:
            await _surreal_harness.connect_admin(_FAKE_ENV)

        assert _NON_RETRYABLE_MESSAGE in str(exc_info.value)
        assert not isinstance(exc_info.value, txn_module.TxnContentionExhaustedError), (
            "a non-conflict bootstrap failure was reported as exhausted contention"
        )
        assert fake.statement_calls[_DEFINE_NAMESPACE] == 1


class TestDropDatabaseRetriesRetryableConflict:
    """A retryable engine conflict is retried, bounded, and never reaches the caller."""

    async def test_retries_past_conflicts_then_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Two retryable conflicts, then success on the third attempt — well
        # within the bound, so teardown must swallow all three and return.
        fake = _FakeConnection(query_outcomes=[_conflict_error(), _conflict_error(), None])
        _patch_connection(monkeypatch, fake)

        await _surreal_harness.drop_database(_FAKE_ENV)

        assert fake.query_calls == 3
        assert fake.closed is True

    async def test_a_conflict_on_teardowns_use_call_is_retried_then_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Teardown selects the database before removing it. That `use()` was a bare,
        # unretried await — the same hole as the bootstrap's, one function over.
        fake = _FakeConnection(
            statement_outcomes={_REMOVE_DATABASE: [None]},
            use_outcomes=[_conflict_error(), None],
        )
        _patch_connection(monkeypatch, fake)

        await _surreal_harness.drop_database(_FAKE_ENV)

        assert fake.use_calls == 2
        assert fake.statement_calls[_REMOVE_DATABASE] == 1
        assert fake.closed is True
        # ORDER is load-bearing against the real engine, exactly as it is for the
        # bootstrap sibling above: a build that issued `REMOVE DATABASE` BEFORE `use()`
        # passes this fake (an unkeyed statement succeeds by design) and fails against a
        # real server, which has no database selected to remove from. Asserting only the
        # call COUNTS cannot see that build (blindreader-150 F8).
        assert fake.operations == [
            f"use:{_FAKE_ENV.namespace}/{_FAKE_ENV.database}",
            f"use:{_FAKE_ENV.namespace}/{_FAKE_ENV.database}",
            f"query:REMOVE DATABASE IF EXISTS {_FAKE_ENV.database}",
        ]

    async def test_exhausting_the_seams_budget_raises_the_seams_exhaustion_type(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # REPLACES the pre-#150 pin, which asserted `QueryError` and `1 < calls < 10`.
        # That test certified the OLD world: the harness's own 5-attempt budget raising
        # the engine's own error. Teardown now exhausts through the shared driver, so
        # the type is the SEAM's and the bound is the SEAM's.
        _silence_backoff(monkeypatch)
        fake = _FakeConnection(query_outcomes=_sustained_conflicts())
        _patch_connection(monkeypatch, fake)

        with pytest.raises(txn_module.TxnContentionExhaustedError) as exc_info:
            await _surreal_harness.drop_database(_FAKE_ENV)

        ceiling = _seam_attempt_ceiling()
        assert exc_info.value.attempts == ceiling
        assert fake.query_calls == ceiling


class TestDropDatabasePropagatesNonRetryableErrors:
    """A non-retryable rejection propagates immediately — never retried, never swallowed."""

    async def test_propagates_on_first_attempt_without_retrying(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake = _FakeConnection(query_outcomes=[_non_retryable_error()])
        _patch_connection(monkeypatch, fake)

        with pytest.raises(QueryError) as exc_info:
            await _surreal_harness.drop_database(_FAKE_ENV)

        assert _NON_RETRYABLE_MESSAGE in str(exc_info.value)
        # Exactly one attempt: a non-retryable error is never retried.
        assert fake.query_calls == 1


class TestTheAdminSocketIsClosedOnEveryFailurePath:
    """The connection is released whether the operation succeeded or raised.

    ``close()`` used to be reachable only on the SUCCESS path in both functions, so
    every failure leaked the socket against the shared dev server (audit-150 R5 /
    blindreader-150 F10). That was pre-existing, and harmless-ish while a failure meant
    one fast raise — but routing these operations through the retry seam means a
    contended failure now holds the socket for the seam's whole budget before leaking
    it, and teardown runs on EVERY ``[real]`` test under ``-n auto``.

    ``connect_admin``'s failure path matters for the same reason and is worse: the
    caller never receives the connection, so on a raise there is no other object in the
    program that could close it.
    """

    async def test_teardown_closes_the_socket_when_the_operation_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake = _FakeConnection(query_outcomes=[_non_retryable_error()])
        _patch_connection(monkeypatch, fake)

        with pytest.raises(QueryError):
            await _surreal_harness.drop_database(_FAKE_ENV)

        assert fake.closed is True, (
            "`drop_database` raised without closing its admin connection. Teardown runs "
            "for every [real] test under `-n auto`; a socket leaked per failure against "
            "the shared server is how a contention storm becomes a connection storm."
        )

    async def test_teardown_closes_the_socket_when_the_conflict_exhausts_the_budget(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _silence_backoff(monkeypatch)
        fake = _FakeConnection(query_outcomes=_sustained_conflicts())
        _patch_connection(monkeypatch, fake)

        with pytest.raises(txn_module.TxnContentionExhaustedError):
            await _surreal_harness.drop_database(_FAKE_ENV)

        assert fake.closed is True, (
            "`drop_database` leaked its admin connection on the EXHAUSTION path — the "
            "one path that, by construction, held the socket for the seam's entire "
            "wall-clock budget before failing."
        )

    async def test_connect_admin_closes_the_socket_when_the_bootstrap_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake = _FakeConnection(statement_outcomes={_DEFINE_NAMESPACE: [_non_retryable_error()]})
        _patch_connection(monkeypatch, fake)

        with pytest.raises(QueryError):
            await _surreal_harness.connect_admin(_FAKE_ENV)

        assert fake.closed is True, (
            "`connect_admin` raised without closing the connection it had already "
            "opened. It never returned that connection, so NOTHING else in the program "
            "holds a reference to close — the socket is unreachable and leaked."
        )

    async def test_connect_admin_still_hands_back_an_OPEN_connection_on_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The control on the pin above: closing on failure must not close on success.

        Without this leg, a build that closed the connection UNCONDITIONALLY (a bare
        ``finally``) would satisfy every assertion above while handing every fixture in
        the suite a dead socket.
        """
        fake = _FakeConnection(
            statement_outcomes={_DEFINE_NAMESPACE: [None], _DEFINE_DATABASE: [None]}
        )
        _patch_connection(monkeypatch, fake)

        # `Any` deliberately: `connect_admin` is typed to the SDK's concrete connection
        # union, which the fake structurally satisfies but does not inherit from.
        returned: Any = await _surreal_harness.connect_admin(_FAKE_ENV)

        assert returned is fake
        assert fake.closed is False, (
            "`connect_admin` closed the connection it returned. Every `[real]` fixture "
            "in this suite goes on to USE that connection."
        )


class TestTheSeamsExhaustionRecordIsAttributable:
    """On exhaustion, the seam's log record must carry WHAT THE ENGINE SAID.

    The raised ``TxnContentionExhaustedError`` deliberately carries only an attempt
    count and a hint (``see the server log for the full engine detail``) — the engine's
    own text rides on the LOG RECORD instead. The seam gates that record's
    ``label``/``url``/``engine_error`` extras on ``label is not None``
    (``_txn.retry_on_conflict``), so a call site that omits ``label`` raises a message
    promising a receipt that does not exist: measured on the first fix as
    ``{'attempts': 64, 'elapsed_seconds': 0.0003}`` and nothing else, with
    ``__cause__``/``__context__`` both ``None`` (blindreader-150 F1).

    That matters in exactly the scenario the marker mutation pins exist for: if the
    engine REWORDS its conflict message, the operator needs to see the new wording
    somewhere. Discarding it leaves the one artifact that would diagnose the failure
    nowhere at all.
    """

    def _exhaustion_record(self, caplog: pytest.LogCaptureFixture) -> logging.LogRecord:
        return _the_one_exhaustion_record(caplog)

    @pytest.mark.parametrize(
        ("script", "expected_label"),
        [
            pytest.param(
                {"use_outcomes": _sustained_conflicts()},
                "_TEARDOWN_SELECT_DATABASE_LABEL",
                id="teardown-select-database",
            ),
            pytest.param(
                {"query_outcomes": _sustained_conflicts()},
                "_TEARDOWN_REMOVE_DATABASE_LABEL",
                id="teardown-remove-database",
            ),
        ],
    )
    async def test_each_teardown_operation_logs_its_label_url_and_engine_text(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        script: dict[str, Any],
        expected_label: str,
    ) -> None:
        _silence_backoff(monkeypatch)
        fake = _FakeConnection(**script)
        _patch_connection(monkeypatch, fake)

        with caplog.at_level(logging.WARNING, logger=txn_module.logger.name):
            with pytest.raises(txn_module.TxnContentionExhaustedError):
                await _surreal_harness.drop_database(_FAKE_ENV)

        record = self._exhaustion_record(caplog)
        label = getattr(_surreal_harness, expected_label)
        assert getattr(record, "label", None) == label, (
            f"the exhaustion record is not attributable to a harness call site: its "
            f"`label` is {getattr(record, 'label', None)!r}, expected {label!r}. An "
            f"unlabelled call also suppresses `url` and `engine_error` — the raised "
            f"message then points an operator at a log record that holds neither."
        )
        assert getattr(record, "url", None) == _FAKE_ENV.url
        assert _CONFLICT_MESSAGE in getattr(record, "engine_error", ""), (
            f"the exhaustion record does not carry the ENGINE's own text (it has "
            f"{getattr(record, 'engine_error', None)!r}). The raised exception says "
            f"'see the server log for the full engine detail'; if the engine reworded "
            f"its conflict message, that wording now exists nowhere."
        )


def _bootstrap_conflicting_on_define_namespace() -> _FakeConnection:
    return _FakeConnection(statement_outcomes={_DEFINE_NAMESPACE: _sustained_conflicts()})


def _bootstrap_conflicting_on_use() -> _FakeConnection:
    return _FakeConnection(
        statement_outcomes={_DEFINE_NAMESPACE: [None], _DEFINE_DATABASE: [None]},
        use_outcomes=_sustained_conflicts(),
    )


def _bootstrap_conflicting_on_define_database() -> _FakeConnection:
    return _FakeConnection(
        statement_outcomes={_DEFINE_NAMESPACE: [None], _DEFINE_DATABASE: _sustained_conflicts()}
    )


# EACH of the bootstrap's three statements, driven to exhaustion ON ITS OWN. Three
# separate fixtures, not one: the wrong build this discriminates against is a bootstrap
# that labels only its FIRST statement (or labels all three the same), which a fixture
# that only ever conflicts DEFINE NAMESPACE cannot tell from a correct one. The
# QUANTIFIER LAW — force every fate, do not infer the others from the one you tested.
_BOOTSTRAP_STATEMENT_BUILDERS: list[tuple[str, Callable[[], _FakeConnection], str]] = [
    ("DEFINE-NAMESPACE", _bootstrap_conflicting_on_define_namespace, _BOOTSTRAP_LABEL_CONSTANTS[0]),
    ("use", _bootstrap_conflicting_on_use, _BOOTSTRAP_LABEL_CONSTANTS[1]),
    ("DEFINE-DATABASE", _bootstrap_conflicting_on_define_database, _BOOTSTRAP_LABEL_CONSTANTS[2]),
]

_BOOTSTRAP_STATEMENT_FATES = [
    pytest.param(build_connection, label_constant, id=statement_id)
    for statement_id, build_connection, label_constant in _BOOTSTRAP_STATEMENT_BUILDERS
]

# What each statement's label must NAME, and what it must NOT — derived from the ENGINE's own
# SurrealQL vocabulary, never from the constants under test. `DEFINE NAMESPACE` concerns a
# namespace and no database; `use()` SELECTS a database and is not a `DEFINE`; `DEFINE
# DATABASE` is both a define and about a database. Exactly one assignment of three values
# satisfies all three rows, so every permutation — including the NS/DB swap that passed the
# previous contract 489/0 — fails at least one of them.
#
# The middle row admits any of three words because the SDK call is `use()` and the operation
# is "select the database": a builder may reasonably name it for either, and a contract that
# dictated one spelling would be a C-DEF trap rather than a property.
_BOOTSTRAP_LABEL_NAMING: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("namespace",), ("database",)),  # DEFINE NAMESPACE
    (("database", "select", "use"), ("namespace", "define")),  # use() — selects, never defines
    (("database",), ("namespace",)),  # DEFINE DATABASE
]

_BOOTSTRAP_LABEL_NAMING_FATES = [
    pytest.param(build_connection, label_constant, required, forbidden, id=statement_id)
    for (statement_id, build_connection, label_constant), (required, forbidden) in zip(
        _BOOTSTRAP_STATEMENT_BUILDERS, _BOOTSTRAP_LABEL_NAMING, strict=True
    )
]


class TestTheBootstrapPathsExhaustionIsAttributable:
    """**FINDING #151, CLOSED.** The bootstrap's exhaustion record says WHICH statement,
    WHICH server, and WHAT THE ENGINE SAID.

    This class REPLACES ``test_the_bootstrap_paths_exhaustion_is_UNATTRIBUTED_a_known_bound``,
    which asserted the opposite and named its own re-open trigger as "the day
    ``bootstrap_session`` passes a label". That day is this diff. The old pin is DELETED,
    not weakened: a bound that gets quietly relaxed to stay green re-hides the defect it
    existed to force a conversation about.

    THE DEFECT IT CLOSES (#151, measured): ``bootstrap_session`` called
    ``retry_on_conflict`` three times passing NO ``label`` and NO ``url``. The driver gates
    the record's ``label``/``url``/``engine_error`` extras on ``label is not None``, and its
    ``raise`` sits OUTSIDE the ``except RetryableConflictSignal`` block so implicit chaining
    never fires either. A bootstrap that exhausted therefore raised a message saying "see
    the server log for the full engine detail" over a record holding
    ``{attempts, elapsed_seconds}`` and nothing else, with ``__cause__`` and ``__context__``
    both ``None``. **The message promised a receipt that did not exist.**

    WHY THE ENGINE TEXT IS THE LOAD-BEARING HALF: if the engine ever REWORDS its conflict
    message — the exact drift the marker pins exist to catch — the operator cannot see the
    new wording anywhere, because the one artifact that would diagnose it was discarded.
    """

    @pytest.mark.parametrize(("build_connection", "label_constant"), _BOOTSTRAP_STATEMENT_FATES)
    async def test_each_bootstrap_statement_logs_its_own_label_url_and_engine_text(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        build_connection: Callable[[], _FakeConnection],
        label_constant: str,
    ) -> None:
        """RED before 352db0e x3: the record carried ``attempts`` and ``elapsed_seconds`` and nothing else.

        Driven through ``connect_admin``, which reaches the seam via
        ``_txn.bootstrap_session`` — the same function every production
        ``_ensure_connection`` calls.
        """
        _silence_backoff(monkeypatch)
        fake = build_connection()
        _patch_connection(monkeypatch, fake)

        with caplog.at_level(logging.WARNING, logger=txn_module.logger.name):
            with pytest.raises(txn_module.TxnContentionExhaustedError):
                await _surreal_harness.connect_admin(_DISTINCT_URL_ENV)

        record = self._record_for(caplog, label_constant)

        # MP6 — THE ORPHANED VIRTUE, restored. The deleted `…is_UNATTRIBUTED_a_known_bound`
        # pin asserted THREE things: no `label` (the bound), no `engine_error` (its cost),
        # and `attempts == _seam_attempt_ceiling()` — the attempt count ON THE LOG RECORD.
        # The first two are the bound, correctly INVERTED by this class. The third was a
        # behaviour the old world pinned and the new world did not: this class asserts label,
        # url, engine_error and distinctness, and never `attempts`.
        #
        # Repo law (the removed-behaviour inventory): a delete/replace ships with every
        # dropped behaviour ADJUDICATED, and "the old code did it" is banned as a reason.
        # The adjudication here is PRESERVED-WITH-PIN, and the spec clause is #151's own R1 —
        # the record must let an operator reconstruct what happened, and how many attempts
        # were spent is half of "what happened". It survives at the EXCEPTION level
        # (`test_sustained_conflict_raises_the_seams_own_exhaustion_type`) but nothing
        # required the two artifacts to agree; the driver computes the count once for both,
        # so they cannot diverge without a deliberate edit — which is exactly when a pin is
        # worth having.
        assert getattr(record, "attempts", None) == _seam_attempt_ceiling(), (
            f"the exhaustion record reports attempts={getattr(record, 'attempts', None)!r}; "
            f"the seam's ceiling is {_seam_attempt_ceiling()} and this fixture conflicts "
            f"forever, so the record must show the seam ran to that ceiling. The raised "
            f"exception carries the same number (it is computed ONCE, for both artifacts) — "
            f"a record disagreeing with the exception it accompanies means an operator "
            f"reconciling a log line against a traceback gets two different stories."
        )

        expected_label = getattr(txn_module, label_constant, None)
        assert isinstance(expected_label, str) and expected_label, (
            f"`_txn.{label_constant}` is {expected_label!r}. Each of the bootstrap's three "
            f"statements needs its OWN canonical event name, declared on the seam that owns "
            f"it — the same way each `_query` seam declares its rejection event and the "
            f"harness declares `_TEARDOWN_*_LABEL`. An operator who greps the exhaustion "
            f"record must land on WHICH of the three statements died."
        )
        assert getattr(record, "label", None) == expected_label, (
            f"the bootstrap's exhaustion record is labelled "
            f"{getattr(record, 'label', None)!r}, expected `_txn.{label_constant}` "
            f"({expected_label!r}). This assertion checks the label ALONE — but an "
            f"unlabelled call also suppresses `url` and `engine_error` in the driver "
            f"(they are gated on `label is not None`), so a missing label is three "
            f"missing facts, and the raised message then points an operator at a log "
            f"record that holds none of them. That is finding #151 verbatim."
        )

    @pytest.mark.parametrize(("build_connection", "label_constant"), _BOOTSTRAP_STATEMENT_FATES)
    async def test_each_bootstrap_statement_carries_the_CALLERS_url(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        build_connection: Callable[[], _FakeConnection],
        label_constant: str,
    ) -> None:
        """The url on the record must be the one THIS CALL was given — not a default.

        The distinguishing wrong build hardcodes a url, or defaults the new parameter to
        something, or reads a module global. :data:`_DISTINCT_BOOTSTRAP_URL` appears
        nowhere else in the repo, so the only way it reaches the record is by being
        threaded from this call site.
        """
        _silence_backoff(monkeypatch)
        _patch_connection(monkeypatch, build_connection())

        with caplog.at_level(logging.WARNING, logger=txn_module.logger.name):
            with pytest.raises(txn_module.TxnContentionExhaustedError):
                await _surreal_harness.connect_admin(_DISTINCT_URL_ENV)

        record = self._record_for(caplog, label_constant)
        assert getattr(record, "url", None) == _DISTINCT_BOOTSTRAP_URL, (
            f"the bootstrap's exhaustion record names the server "
            f"{getattr(record, 'url', None)!r}; this connect was made against "
            f"{_DISTINCT_BOOTSTRAP_URL!r}. This assertion checks EXACT equality with the "
            f"url the caller passed — a build that hardcodes, defaults, or globals its way "
            f"to a url fails here even when it logs a url that looks plausible."
        )

    @pytest.mark.parametrize(("build_connection", "label_constant"), _BOOTSTRAP_STATEMENT_FATES)
    async def test_each_bootstrap_statement_carries_the_ENGINES_OWN_text(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        build_connection: Callable[[], _FakeConnection],
        label_constant: str,
    ) -> None:
        """**THE LOAD-BEARING PIN OF THE WHOLE FINDING.**

        The raised ``TxnContentionExhaustedError`` deliberately carries only an attempt
        count and the hint "see the server log for the full engine detail" (ledger #31:
        generic message, FULL detail server-side). That contract is satisfiable ONLY if the
        record actually holds the engine's words. A build that threads a label and a url but
        loses the engine text — one that raises the signal without ``from error``, or drops
        ``last_conflict_cause`` — satisfies the two pins above and still leaves the hint
        pointing at nothing.

        An EMPTY ``engine_error`` fails here, and is called out separately from a WRONG one,
        because the driver's own fallback for "no cause" is exactly ``""`` — the failure
        mode this pin most needs to name.
        """
        _silence_backoff(monkeypatch)
        _patch_connection(monkeypatch, build_connection())

        with caplog.at_level(logging.WARNING, logger=txn_module.logger.name):
            with pytest.raises(txn_module.TxnContentionExhaustedError):
                await _surreal_harness.connect_admin(_DISTINCT_URL_ENV)

        record = self._record_for(caplog, label_constant)
        engine_error = str(getattr(record, "engine_error", ""))
        assert engine_error, (
            "the bootstrap's exhaustion record carries an EMPTY `engine_error`. That is the "
            "driver's own `last_conflict_cause is None` fallback: the signal reached it "
            "without a `__cause__`, so the engine's words were never captured. The raised "
            "message still says 'see the server log for the full engine detail'."
        )
        assert _CONFLICT_MESSAGE in engine_error, (
            f"the bootstrap's exhaustion record carries `engine_error`={engine_error!r}, "
            f"which does not contain the engine's own conflict text "
            f"({_CONFLICT_MESSAGE!r}). This assertion is a SUBSTRING check against the text "
            f"the fake engine actually raised — a placeholder, a repr of the signal, or our "
            f"own prose about the conflict all fail it, and are worse than nothing because "
            f"they make the log look complete. If the engine reworded its conflict message, "
            f"this record is the only place that wording would survive."
        )

    async def test_the_three_statements_carry_THREE_DISTINCT_labels(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """One shared label ("store.bootstrap") would satisfy every per-statement pin above
        if the constants all held the same string. This reads the three labels the three
        runs ACTUALLY logged and requires them to be pairwise distinct.

        DERIVED, not declared: it compares the observed records to each other, so it cannot
        be satisfied by three constant NAMES pointing at one value. Without it, an operator
        looking at a bootstrap exhaustion still could not tell WHICH statement died — which
        is half of what #151 asked for.
        """
        _silence_backoff(monkeypatch)
        observed: list[Any] = []

        for _, build_connection, _label_constant in _BOOTSTRAP_STATEMENT_BUILDERS:
            caplog.clear()
            _patch_connection(monkeypatch, build_connection())
            with caplog.at_level(logging.WARNING, logger=txn_module.logger.name):
                with pytest.raises(txn_module.TxnContentionExhaustedError):
                    await _surreal_harness.connect_admin(_DISTINCT_URL_ENV)
            observed.append(getattr(_the_one_exhaustion_record(caplog), "label", None))

        assert len(observed) == 3, "the fixture did not drive all three statements"
        assert len(set(observed)) == 3, (
            f"the bootstrap's three statements logged labels {observed} — they must be "
            f"PAIRWISE DISTINCT. This assertion compares the three OBSERVED labels to each "
            f"other, so three constants holding one shared string (e.g. 'store.bootstrap') "
            f"fails here even though every per-statement pin passes. A single label tells an "
            f"operator that A bootstrap statement exhausted; #151 asks WHICH one."
        )

    @pytest.mark.parametrize(
        ("build_connection", "label_constant", "required", "forbidden"),
        _BOOTSTRAP_LABEL_NAMING_FATES,
    )
    async def test_each_bootstrap_label_NAMES_its_own_statement(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        build_connection: Callable[[], _FakeConnection],
        label_constant: str,
        required: tuple[str, ...],
        forbidden: tuple[str, ...],
    ) -> None:
        """**THE WRONG BUILD THIS CATCHES, MEASURED: 489 passed / 0 failed.**

        Swap the VALUES of ``_BOOTSTRAP_DEFINE_NAMESPACE_LABEL`` and
        ``_BOOTSTRAP_DEFINE_DATABASE_LABEL`` — so the DEFINE-NAMESPACE statement reports
        itself as ``…define_database.rejected`` and vice versa — and every pin above stays
        green. The labels are still present, still three, still pairwise distinct; they
        simply name the WRONG statements, and an operator greeted with a bootstrap
        exhaustion lands on the wrong one of the three.

        WHY THE PINS ABOVE CANNOT SEE IT: they assert ``record.label ==
        getattr(txn_module, <constant name>)`` — comparing the observation to the constant
        that is itself under test. Self-referential, and therefore true for any assignment
        of values to those three names. The existing pin's own failure message promises
        more than that: *"An operator who greps the exhaustion record must land on WHICH of
        the three statements died."* **A message promising a check the assertion does not
        perform is a FALSE GATE** — this repo has already shipped one in this exact area
        whose wrong build passed 399/399.

        SO THIS PIN DERIVES ITS EXPECTATION FROM THE STATEMENT, NOT FROM THE CONSTANT: the
        record for the statement that ran must carry that statement's own SurrealQL
        vocabulary and must NOT carry the vocabulary that distinguishes the other two.
        ``DEFINE NAMESPACE`` says "namespace" and never "database"; ``use()`` selects a
        database and is not a ``DEFINE``; ``DEFINE DATABASE`` is both. Those three
        constraints are jointly satisfied by exactly one assignment, so ANY permutation of
        the three values fails — which is the property, stated as a property.

        (Vocabulary, not spelling: the check is case-insensitive and substring-based, so
        `store.bootstrap.select_database.rejected` and `store.bootstrap.use_session.rejected`
        both pass for the middle statement. It constrains what a label must NAME, not how
        its author must punctuate.)
        """
        _silence_backoff(monkeypatch)
        _patch_connection(monkeypatch, build_connection())

        with caplog.at_level(logging.WARNING, logger=txn_module.logger.name):
            with pytest.raises(txn_module.TxnContentionExhaustedError):
                await _surreal_harness.connect_admin(_DISTINCT_URL_ENV)

        label = str(getattr(_the_one_exhaustion_record(caplog), "label", "")).lower()

        # ANY-OF, not all-of: `required` is a set of ALTERNATIVES (see the table's middle
        # row, where "select"/"use"/"database" are three reasonable names for one statement).
        assert any(word in label for word in required), (
            f"the statement this fixture drove to exhaustion logged label={label!r}, which "
            f"does not name what it is: it carries none of {list(required)}. "
            f"`_txn.{label_constant}` is "
            f"the constant the seam declares for this statement, and its VALUE must say "
            f"which statement it belongs to — the label is the string an operator greps, "
            f"and a label that does not name its statement leaves them exactly where #151 "
            f"found them: knowing A bootstrap statement died, not WHICH."
        )

        intruding = [word for word in forbidden if word in label]
        assert not intruding, (
            f"the statement this fixture drove to exhaustion logged label={label!r}, which "
            f"carries {intruding} — vocabulary belonging to a DIFFERENT bootstrap "
            f"statement.\n\nThis is the wrong build that passed the previous contract "
            f"489/0: three labels, present, distinct, and rotated so each names its "
            f"neighbour. The pins that compare a record to `getattr(txn_module, "
            f"'{label_constant}')` cannot see it — they compare the observation to the very "
            f"constant under test. An operator reading a rotated label is sent to the wrong "
            f"statement with full confidence, which is worse than the missing label #151 "
            f"began with."
        )

    def _record_for(
        self, caplog: pytest.LogCaptureFixture, label_constant: str
    ) -> logging.LogRecord:
        del label_constant  # the fixture drives ONE statement; the record is unambiguous
        return _the_one_exhaustion_record(caplog)


class TestBootstrapSessionRequiresItsUrl:
    """**R2 — ``url`` is REQUIRED and KEYWORD-ONLY, not an optional defaulting to None.**

    All eleven production owners have their url in hand at the call site. A defaulted
    parameter is a silent hole a future caller falls into: it would type-check, lint clean,
    and log ``url=None`` on the one path where an operator needs a server name. Required is
    the deny-by-default choice, and deny-by-default only holds if something asserts it.
    """

    # Both pins below call the seam with a DELIBERATELY WRONG signature, so both are
    # invoked through an ``Any``-typed reference rather than the imported name.
    #
    # That is not a style dodge, it is a satisfiability requirement: mypy runs over the
    # test tree with zero errors permitted (repo law), and a direct call would be a STATIC
    # error — `Too many arguments` today, `Missing named argument "url"` after the fix
    # lands. Either way the builder would be trapped between the type gate and a test it
    # may not edit, which this repo names the C-DEF class. The runtime binding is exactly
    # what these pins are about; the static call shape is not.
    @property
    def _bootstrap(self) -> Any:
        return txn_module.bootstrap_session

    async def test_omitting_url_is_a_TypeError_at_the_call(self) -> None:
        """A build that defaults ``url=None`` passes every attribution pin that supplies a
        url, and silently admits every future caller that forgets one.
        """
        with pytest.raises(TypeError):
            await self._bootstrap(_FakeConnection(), _FAKE_ENV.namespace, _FAKE_ENV.database)

    async def test_passing_url_POSITIONALLY_is_a_TypeError(self) -> None:
        """Keyword-only, not merely required. A positional fourth parameter is orderable
        with ``namespace``/``database`` at a glance and mis-orderable in a diff — all three
        are strings, so a swap type-checks and the store silently bootstraps the wrong
        database while logging the right url.

        ⚠ This pin does NOT discriminate on the unfixed tree: with only three parameters, a
        fourth positional argument is a ``TypeError`` for the WRONG reason (arity, not
        keyword-only-ness), so it is green today and cannot be red-by-design. It is
        mutation-proven instead — dropping the ``*`` from the fixed signature turns it red.
        """
        with pytest.raises(TypeError):
            await self._bootstrap(
                _FakeConnection(),
                _FAKE_ENV.namespace,
                _FAKE_ENV.database,
                _FAKE_ENV.url,
            )


class TestSeveralOperationsUnderOneCallerShareONEBudget:
    """A caller driving N operations composes ONE wall-clock budget across them.

    ``_txn.bootstrap_session``'s docstring states the property and the reason: "three
    equal deadlines would be three independent budgets wearing a parameter". The first
    fix routed teardown's two operations to the shared driver while handing each a FRESH
    copy of the seam's default — so teardown's real bound was DOUBLE its designed one
    (measured 3.812s against a designed 2.0s: blindreader-150 F2 / audit-150 R4).

    And the ``connect_admin`` side had the opposite problem: the shipped code was
    CORRECT (it delegates to ``bootstrap_session``, which composes) but NOTHING pinned
    it. The cold auditor built the wrong build — ``connect_admin`` inlining three
    independent ``_run_under_store_retry_seam`` calls over the same three statements —
    and it passed the entire contract **17/17**, because it still routes to the shared
    driver and therefore satisfies every sharing pin (audit-150 R1). Routing is not
    sharing; sharing a DRIVER is not sharing a BUDGET.

    HOW THESE DISCRIMINATE: see :data:`_COMPOSITION_DEADLINE_SECONDS`. The caller's
    FIRST operation deliberately overspends a short seam deadline; the operation being
    MEASURED then lands on the seam's attempt FLOOR under a composing caller, and would
    run to its CEILING under a caller handing out fresh budgets.
    """

    def _assert_the_two_bounds_differ(self) -> tuple[int, int]:
        floor = _seam_attempt_floor()
        ceiling = _seam_attempt_ceiling()
        assert floor != ceiling, (
            "the seam's attempt floor and ceiling coincide, so 'composed' and "
            "'uncomposed' produce the same observed count — this pin cannot discriminate"
        )
        assert _BUDGET_BURN_CONFLICTS < floor, (
            f"the budget-burning operation is scripted to conflict "
            f"{_BUDGET_BURN_CONFLICTS} times, which is not below the seam's attempt "
            f"floor of {floor} — it would give up instead of burning the budget, and "
            f"this pin would pass for the wrong reason"
        )
        return floor, ceiling

    def _shorten_the_seams_budget(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _silence_backoff(monkeypatch)
        monkeypatch.setattr(
            txn_module,
            "_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS",
            _COMPOSITION_DEADLINE_SECONDS,
        )

    async def test_connect_admins_three_statements_share_one_budget(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        floor, ceiling = self._assert_the_two_bounds_differ()
        self._shorten_the_seams_budget(monkeypatch)

        # DEFINE NAMESPACE conflicts (below the floor, so it recovers) while spending
        # more than the whole budget; DEFINE DATABASE — the LAST of the three — then
        # conflicts forever and reports how much budget it was given.
        fake = _FakeConnection(
            statement_outcomes={
                _DEFINE_NAMESPACE: [_conflict_error()] * _BUDGET_BURN_CONFLICTS + [None],
                _DEFINE_DATABASE: _sustained_conflicts(),
            },
            statement_delays={_DEFINE_NAMESPACE: _BUDGET_BURN_DELAY_SECONDS},
        )
        _patch_connection(monkeypatch, fake)

        with pytest.raises(txn_module.TxnContentionExhaustedError):
            await _surreal_harness.connect_admin(_FAKE_ENV)

        # All three statements really ran, in order — otherwise the count below could be
        # low for a reason that has nothing to do with budgets.
        assert fake.operations[-1] == f"query:DEFINE DATABASE IF NOT EXISTS {_FAKE_ENV.database}"
        assert fake.statement_calls[_DEFINE_NAMESPACE] == _BUDGET_BURN_CONFLICTS + 1
        assert fake.use_calls == 1

        observed = fake.statement_calls[_DEFINE_DATABASE]
        assert observed == floor, (
            f"`connect_admin`'s third bootstrap statement attempted {observed} times "
            f"after the first two had already overspent the seam's whole "
            f"{_COMPOSITION_DEADLINE_SECONDS}s budget. A caller that COMPOSES leaves it "
            f"the attempt floor ({floor}); {ceiling} means it was handed a FRESH budget "
            f"— three independent budgets wearing a parameter (audit-150 R1). This is "
            f"the wrong build that passed the entire first contract 17/17."
        )

    async def test_teardowns_two_operations_share_one_budget(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        floor, ceiling = self._assert_the_two_bounds_differ()
        self._shorten_the_seams_budget(monkeypatch)

        fake = _FakeConnection(
            use_outcomes=[_conflict_error()] * _BUDGET_BURN_CONFLICTS + [None],
            use_delay_seconds=_BUDGET_BURN_DELAY_SECONDS,
            query_outcomes=_sustained_conflicts(),
        )
        _patch_connection(monkeypatch, fake)

        with pytest.raises(txn_module.TxnContentionExhaustedError):
            await _surreal_harness.drop_database(_FAKE_ENV)

        assert fake.use_calls == _BUDGET_BURN_CONFLICTS + 1
        observed = fake.query_calls
        assert observed == floor, (
            f"teardown's REMOVE attempted {observed} times after its `use()` had "
            f"already overspent the seam's whole {_COMPOSITION_DEADLINE_SECONDS}s "
            f"budget. A caller that COMPOSES leaves it the attempt floor ({floor}); "
            f"{ceiling} means `drop_database` handed each of its two operations a fresh "
            f"copy of the deadline — measured at 3.812s against a designed 2.0s on the "
            f"first fix (blindreader-150 F2)."
        )

    async def test_the_composed_budget_is_READ_from_the_seam_not_copied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The composed budget must be the SEAM's number, live — not a private copy of it.

        The distinguishing wrong build is a `drop_database` that composes a budget it
        hardcodes (or froze at import). It satisfies both pins above — they only require
        composition — while being exactly the private-policy copy finding #150 removed.
        Driving the seam's default to zero makes the two builds disagree: a live read
        leaves the FIRST operation the attempt floor; a private copy leaves it the
        ceiling.
        """
        _silence_backoff(monkeypatch)
        floor, ceiling = self._assert_the_two_bounds_differ()

        monkeypatch.setattr(txn_module, "_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS", 0.0)
        fake = _FakeConnection(use_outcomes=_sustained_conflicts())
        _patch_connection(monkeypatch, fake)

        with pytest.raises(txn_module.TxnContentionExhaustedError):
            await _surreal_harness.drop_database(_FAKE_ENV)

        assert fake.use_calls == floor, (
            f"teardown's first operation attempted {fake.use_calls} times under a ZERO "
            f"seam deadline; the seam's attempt floor is {floor}. `drop_database` is "
            f"composing a budget it did not read from the seam."
        )


async def _sustain(
    function_name: str,
    monkeypatch: pytest.MonkeyPatch,
    fake: _FakeConnection,
) -> None:
    """Drive ``function_name`` against ``fake`` and require it to exhaust the seam's budget."""
    _patch_connection(monkeypatch, fake)
    driver = getattr(_surreal_harness, function_name)
    with pytest.raises(txn_module.TxnContentionExhaustedError):
        await driver(_FAKE_ENV)


async def _probe_bootstrap_define_namespace(monkeypatch: pytest.MonkeyPatch) -> int:
    fake = _FakeConnection(statement_outcomes={_DEFINE_NAMESPACE: _sustained_conflicts()})
    await _sustain("connect_admin", monkeypatch, fake)
    return fake.statement_calls[_DEFINE_NAMESPACE]


async def _probe_bootstrap_use(monkeypatch: pytest.MonkeyPatch) -> int:
    fake = _FakeConnection(
        statement_outcomes={_DEFINE_NAMESPACE: [None], _DEFINE_DATABASE: [None]},
        use_outcomes=_sustained_conflicts(),
    )
    await _sustain("connect_admin", monkeypatch, fake)
    return fake.use_calls


async def _probe_bootstrap_define_database(monkeypatch: pytest.MonkeyPatch) -> int:
    fake = _FakeConnection(
        statement_outcomes={_DEFINE_NAMESPACE: [None], _DEFINE_DATABASE: _sustained_conflicts()}
    )
    await _sustain("connect_admin", monkeypatch, fake)
    return fake.statement_calls[_DEFINE_DATABASE]


async def _probe_teardown_use(monkeypatch: pytest.MonkeyPatch) -> int:
    fake = _FakeConnection(use_outcomes=_sustained_conflicts())
    await _sustain("drop_database", monkeypatch, fake)
    return fake.use_calls


async def _probe_teardown_remove_database(monkeypatch: pytest.MonkeyPatch) -> int:
    fake = _FakeConnection(query_outcomes=_sustained_conflicts())
    await _sustain("drop_database", monkeypatch, fake)
    return fake.query_calls


# EVERY operation the harness puts under the seam, mapped to a probe that reports how
# many times it was ATTEMPTED under a sustained conflict. This is the reach of the
# mutation proof, written down so it can be CHECKED (see
# ``test_every_operation_under_the_seam_has_a_constant_tied_probe``) rather than assumed:
# the first fix's proof reached only `connect_admin:DEFINE NAMESPACE` and
# `drop_database:REMOVE DATABASE`, leaving BOTH `use()` calls asserted by nothing but a
# constant-independent "it retried once" — and `use()` is the call this repo's own probe
# identified as the one that actually loses the bootstrap race (blindreader-150 F6).
_OPERATION_PROBES: dict[str, Callable[[pytest.MonkeyPatch], Awaitable[int]]] = {
    "connect_admin:DEFINE NAMESPACE": _probe_bootstrap_define_namespace,
    "connect_admin:use": _probe_bootstrap_use,
    "connect_admin:DEFINE DATABASE": _probe_bootstrap_define_database,
    "drop_database:use": _probe_teardown_use,
    "drop_database:REMOVE DATABASE": _probe_teardown_remove_database,
}


def _operation_key(function_name: str, recorded: str) -> str:
    """Normalise one ``_FakeConnection.operations`` entry into an operation key.

    Deliberately NOT a lookup against the known statements: a NEW statement the harness
    starts issuing must produce a NEW key (and so redden the reach pin), not fall into a
    default bucket. ``use:<ns>/<db>`` collapses to ``use``; ``query:<statement>`` keeps
    the statement's first two words, which is what distinguishes ``DEFINE NAMESPACE``
    from ``DEFINE DATABASE`` from ``REMOVE DATABASE``.
    """
    if recorded.startswith("use:"):
        return f"{function_name}:use"
    statement = recorded.removeprefix("query:")
    return f"{function_name}:{' '.join(statement.split()[:2])}"


class TestTheHarnessRetryPolicyIsTheSeamsPolicy:
    """THE SHARING PIN (finding #150): move the seam's constant, and the harness moves.

    ROUTING IS NOT SHARING. A harness that calls ``retry_on_conflict`` but keeps its own
    budget, its own backoff, or its own marker match underneath it is a private copy
    wearing the shared name — and it passes every pin above, which only establish THAT a
    retry happened. The only test that can tell the two apart is a mutation: change the
    shared thing and require every caller to change with it.

    Each pin here carries its own POSITIVE CONTROL leg — the identical assertion run at
    the UNMUTATED value — so a pin that had quietly stopped discriminating (e.g. one
    whose observed count no longer depends on the constant at all) cannot hide behind a
    green mutated leg.

    AND THE PROOF'S REACH IS ITSELF CHECKED. These pins run over
    :data:`_OPERATION_PROBES` — every operation the harness puts under the seam, one
    probe each — and a separate pin DISCOVERS the operations from the harness's own
    behaviour and requires the two sets to match exactly. A guard is an invariant only
    over the code it actually runs; leaving that reach implicit is how the first fix's
    proof came to cover 2 of 5 operations with nobody noticing.
    """

    async def test_every_operation_under_the_seam_has_a_constant_tied_probe(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """REACH AS A CHECKED VARIABLE — the operations are discovered, not declared.

        Drives both functions on their happy paths and reads back every engine operation
        they actually issued. If that set ever exceeds :data:`_OPERATION_PROBES`, some
        operation is running under the seam with no mutation probe tying it to the
        seam's constants — which is precisely the state this suite was in when a grader
        found it.
        """
        bootstrap_fake = _FakeConnection(
            statement_outcomes={_DEFINE_NAMESPACE: [None], _DEFINE_DATABASE: [None]}
        )
        _patch_connection(monkeypatch, bootstrap_fake)
        await _surreal_harness.connect_admin(_FAKE_ENV)

        teardown_fake = _FakeConnection(statement_outcomes={_REMOVE_DATABASE: [None]})
        _patch_connection(monkeypatch, teardown_fake)
        await _surreal_harness.drop_database(_FAKE_ENV)

        discovered = {
            _operation_key("connect_admin", recorded)
            for recorded in bootstrap_fake.operations
        } | {
            _operation_key("drop_database", recorded) for recorded in teardown_fake.operations
        }

        assert discovered == set(_OPERATION_PROBES), (
            f"the set of engine operations the harness issues has changed.\n"
            f"  operations with NO constant-tied probe: "
            f"{sorted(discovered - set(_OPERATION_PROBES))}\n"
            f"  probes naming an operation the harness no longer issues: "
            f"{sorted(set(_OPERATION_PROBES) - discovered)}\n"
            f"Every operation under the retry seam needs its own probe in "
            f"`_OPERATION_PROBES`, or the mutation proof below silently stops covering "
            f"it — the reach of a guard is a variable to CHECK, not to assume."
        )

    @pytest.mark.parametrize("operation", sorted(_OPERATION_PROBES))
    async def test_every_operation_follows_the_seams_attempt_ceiling(
        self, monkeypatch: pytest.MonkeyPatch, operation: str
    ) -> None:
        _silence_backoff(monkeypatch)
        probe = _OPERATION_PROBES[operation]

        # POSITIVE CONTROL: at the seam's real ceiling, the observed count IS it.
        control_ceiling = _seam_attempt_ceiling()
        assert await probe(monkeypatch) == control_ceiling, (
            f"the control leg for {operation} did not reach the seam's real ceiling; "
            f"this probe is not measuring what it claims to"
        )

        # MUTATION: move the seam's ceiling; the operation must move with it.
        monkeypatch.setattr(txn_module, "_TXN_CONFLICT_ATTEMPT_CEILING", _MUTATED_ATTEMPT_CEILING)
        assert _seam_attempt_ceiling() != control_ceiling, "the mutation did not take"
        observed = await probe(monkeypatch)

        assert observed == _MUTATED_ATTEMPT_CEILING, (
            f"{operation} attempted {observed} times after the store seam's attempt "
            f"ceiling moved to {_MUTATED_ATTEMPT_CEILING} (it was {control_ceiling}). "
            f"The harness is NOT sharing the seam's retry policy at this operation — it "
            f"is running a private budget that merely happens to call the shared driver, "
            f"which is the exact shape finding #150 exists to remove."
        )

    @pytest.mark.parametrize("operation", sorted(_OPERATION_PROBES))
    async def test_every_operation_follows_the_seams_wall_clock_deadline(
        self, monkeypatch: pytest.MonkeyPatch, operation: str
    ) -> None:
        """Moving the seam's DEADLINE (not its ceiling) moves every operation too.

        A second, independent axis: the give-up predicate is
        ``ceiling reached`` OR (``deadline elapsed`` AND ``attempt floor met``). Driving
        the deadline to zero therefore lands every operation on the seam's attempt FLOOR
        — a different constant from the ceiling leg above, so a build that happened to
        agree with the seam on one number cannot agree with it on both by coincidence.
        """
        _silence_backoff(monkeypatch)
        probe = _OPERATION_PROBES[operation]

        # POSITIVE CONTROL: with the real (non-zero) deadline, the operation runs to the
        # CEILING, which is emphatically not the floor.
        ceiling = _seam_attempt_ceiling()
        floor = _seam_attempt_floor()
        assert ceiling != floor, "the ceiling and floor coincide; this pin cannot discriminate"
        assert await probe(monkeypatch) == ceiling

        # MUTATION: a zero wall-clock budget makes the FLOOR the binding bound.
        monkeypatch.setattr(txn_module, "_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS", 0.0)
        observed = await probe(monkeypatch)

        assert observed == floor, (
            f"{operation} attempted {observed} times under a zero seam deadline; the "
            f"seam's attempt floor is {floor}. This operation is not reading the seam's "
            f"wall-clock budget."
        )

    async def test_detection_follows_the_seams_one_conflict_marker(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Moving the seam's MARKER stops the harness retrying — proving it never
        kept a literal copy of the engine's prose.

        This is the pin the retired ``TestTheTestHarnessCannotDriftFromTheSeamsMarker``
        could not be: that one asserted two literals were EQUAL, which a private copy
        satisfies by definition. This one asserts there is no second copy to compare.
        """
        _silence_backoff(monkeypatch)

        # POSITIVE CONTROL: at the seam's real marker, teardown retries the conflict.
        control = _FakeConnection(query_outcomes=[_conflict_error(), None])
        _patch_connection(monkeypatch, control)
        await _surreal_harness.drop_database(_FAKE_ENV)
        assert control.query_calls == 2, "the control leg did not retry; the pin is blind"

        # MUTATION: the seam no longer recognises the engine's prose as a conflict.
        monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_MARKER", "a marker no engine emits")

        mutated = _FakeConnection(query_outcomes=[_conflict_error(), None])
        _patch_connection(monkeypatch, mutated)
        with pytest.raises(QueryError):
            await _surreal_harness.drop_database(_FAKE_ENV)

        assert mutated.query_calls == 1, (
            f"teardown retried {mutated.query_calls - 1} time(s) on a message the "
            f"SHARED marker no longer recognises as a conflict — it is branching on "
            f"engine prose it keeps privately. Reword the engine and this retry dies "
            f"silently, which is exactly how finding #150's copy would have failed."
        )

    async def test_the_bootstrap_paths_detection_follows_the_seams_marker(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The same mutation, at the bootstrap path — the site with no retry at all
        before #150, and therefore the site with no prior detection to inherit."""
        _silence_backoff(monkeypatch)

        control = _FakeConnection(
            statement_outcomes={
                _DEFINE_NAMESPACE: [_conflict_error(), None],
                _DEFINE_DATABASE: [None],
            }
        )
        _patch_connection(monkeypatch, control)
        await _surreal_harness.connect_admin(_FAKE_ENV)
        assert control.statement_calls[_DEFINE_NAMESPACE] == 2, (
            "the control leg did not retry; the pin is blind"
        )

        monkeypatch.setattr(txn_module, "_RETRYABLE_CONFLICT_MARKER", "a marker no engine emits")

        mutated = _FakeConnection(
            statement_outcomes={
                _DEFINE_NAMESPACE: [_conflict_error(), None],
                _DEFINE_DATABASE: [None],
            }
        )
        _patch_connection(monkeypatch, mutated)
        with pytest.raises(QueryError):
            await _surreal_harness.connect_admin(_FAKE_ENV)

        assert mutated.statement_calls[_DEFINE_NAMESPACE] == 1, (
            f"the bootstrap retried {mutated.statement_calls[_DEFINE_NAMESPACE] - 1} "
            f"time(s) on a message the SHARED marker no longer recognises as a conflict "
            f"— it is keeping a private copy of the engine's prose."
        )


# --- structural derivations over the harness and its consumers --------------------
# Grep is the honest instrument for none of this: these are AST questions about which
# files import a module and which call a function, and the answers are DERIVED here so
# no failure message and no docstring can carry a number nobody re-measured.
_ALLOWED_MODULE_LEVEL_IMPORT = "loremaster.index.records"

# THE SAFE SET, not a forbidden one (CLAUDE.md: "when you catch yourself enumerating
# what is FORBIDDEN, you have already lost — the forbidden set is unbounded; the SAFE
# set is small and enumerable"). Every module-level binding the harness is allowed to
# declare. A reintroduced private retry budget cannot be spelled in a way that escapes
# this, whatever it is NAMED — which is exactly what defeated the three-name deny-list
# that used to be the only structural guard here (blindreader-150 F4 / audit-150 R3).
_ALLOWED_MODULE_LEVEL_NAMES = frozenset(
    {
        # public topology + fixture vocabulary
        "ANALYZER_NAME",
        "DEFAULT_PASS",
        "DEFAULT_URL",
        "DEFAULT_USER",
        "NONDEFAULT_DIM",
        "PRODUCTION_DIM",
        "SLUG",
        "SurrealConnection",
        "SurrealEnv",
        "TEST_NAMESPACE",
        "TIER_A",
        "TIER_B",
        "_ENV_PASS",
        "_ENV_URL",
        "_ENV_USER",
        "_SOURCE_TEXT",
        # seam call-site IDENTITY (labels for the seam's exhaustion record) — not policy
        "_TEARDOWN_REMOVE_DATABASE_LABEL",
        "_TEARDOWN_SELECT_DATABASE_LABEL",
        # helpers, protocols and fixtures
        "_RemovableDatabaseConnection",
        "_remove_database_with_retry",
        "_run_under_store_retry_seam",
        "_seam_default_deadline_seconds",
        "admin_db",
        "call_until_recovered",
        "chunk_record",
        "connect_admin",
        "drop_database",
        "make_env",
        "run",
        "surreal_env",
        "surreal_password",
        "surreal_url",
        "surreal_user",
        "unique_database",
        "unit_vector",
    }
)


def _harness_source() -> str:
    import pathlib

    return pathlib.Path(_surreal_harness.__file__).read_text(encoding="utf-8")


def _module_level_imported_modules(source: str) -> set[str]:
    """Every module imported when ``source`` is IMPORTED — not merely at ``tree.body``.

    The property this scan must have is "executes at import time", and that is NOT the
    same as "is a direct child of Module": an import inside a module-level ``try``,
    ``if``, ``with``, ``for`` or ``while`` runs on import just the same. Scanning
    ``tree.body`` alone therefore passed a ``try: from loremaster.store._txn import …
    except ImportError:`` wrapper GREEN (blindreader-150 F3, demonstrated) — and the
    wrapper does not even help, because a store module broken mid-TDD typically raises
    ``SyntaxError``/``NameError``/``AttributeError`` from its own body, none of which is
    an ``ImportError``.

    So: recurse everywhere EXCEPT into function and class bodies, which do not execute
    at import. That is the property the pin's docstring has always described.
    """
    import ast

    def walk(node: ast.AST) -> set[str]:
        found: set[str] = set()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                continue
            if isinstance(child, ast.Import):
                found.update(alias.name for alias in child.names)
            elif isinstance(child, ast.ImportFrom):
                if child.module is not None:
                    found.add(child.module)
            else:
                found |= walk(child)
        return found

    return walk(ast.parse(source))


def _module_level_bound_names(source: str) -> set[str]:
    """Every name ``source`` binds at module level (assignments, functions, classes)."""
    import ast

    names: set[str] = set()
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _test_files() -> list[Any]:
    import pathlib

    harness = pathlib.Path(_surreal_harness.__file__)
    return sorted(p for p in harness.parent.rglob("*.py") if p != harness)


def _harness_importer_files() -> list[str]:
    """Every test file that IMPORTS ``_surreal_harness`` — the collection-blast radius."""
    import ast

    importers = []
    for path in _test_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name == "_surreal_harness" or alias.name.startswith("_surreal_harness.")
                for alias in node.names
            ):
                importers.append(path.name)
                break
            if isinstance(node, ast.ImportFrom) and node.module == "_surreal_harness":
                importers.append(path.name)
                break
    return sorted(importers)


def _connect_admin_caller_files() -> list[str]:
    """Every test file that CALLS ``connect_admin`` — a SMALLER, DIFFERENT population."""
    import ast

    callers = []
    for path in _test_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if (isinstance(func, ast.Name) and func.id == "connect_admin") or (
                isinstance(func, ast.Attribute) and func.attr == "connect_admin"
            ):
                callers.append(path.name)
                break
    return sorted(callers)


class TestTheHarnessDeclaresNoRetryPolicyOfItsOwn:
    """The structural half of finding #150: there is nothing left to drift.

    The retired drift pin (``test_retry_seam.py``'s
    ``TestTheTestHarnessCannotDriftFromTheSeamsMarker``) guarded a copy it could not
    delete. The copy is now gone, and this asserts the deletion — so a future edit that
    reintroduces a private budget/backoff/marker goes RED here rather than being
    discovered by a suite that quietly stops retrying.

    THE PRIMARY GUARD IS THE ALLOWLIST, not the retired-name list under it. This class
    used to consist of three ``not hasattr`` assertions on three literal names, under a
    docstring promising that "a future edit that reintroduces a private
    budget/backoff/marker goes RED **here**" — which a reintroduced
    ``_TEARDOWN_MAX_ATTEMPTS`` would have walked straight past. The retired-name legs are
    kept for the specific message they can give, but they are DEFENCE IN DEPTH; the
    property is carried by :data:`_ALLOWED_MODULE_LEVEL_NAMES`.
    """

    def test_the_harnesss_module_level_names_are_exactly_the_allowed_set(self) -> None:
        bound = _module_level_bound_names(_harness_source())
        added = sorted(bound - _ALLOWED_MODULE_LEVEL_NAMES)
        removed = sorted(_ALLOWED_MODULE_LEVEL_NAMES - bound)
        assert not added and not removed, (
            f"`_surreal_harness`'s module-level names no longer match the allowed set.\n"
            f"  declared but NOT allowed: {added}\n"
            f"  allowed but no longer declared: {removed}\n"
            f"This is an ALLOWLIST on purpose: the harness owns no conflict-retry policy "
            f"— no conflict budget, no backoff, no copy of the engine's marker — and a "
            f"list of FORBIDDEN names cannot express that, because the forbidden set is "
            f"unbounded (finding #150; the three-name deny-list this replaces admitted "
            f"any privately-named budget). If the new name is legitimate, add it here in "
            f"a diff a reviewer can see; if it is retry policy, it belongs in "
            f"`loremaster.store._txn`."
        )

    @pytest.mark.parametrize(
        "retired_name",
        [
            "_RETRYABLE_CONFLICT_MARKER",
            "_MAX_DROP_DATABASE_ATTEMPTS",
            "_DROP_DATABASE_BACKOFF_SECONDS",
        ],
    )
    def test_the_retired_policy_constants_are_gone(self, retired_name: str) -> None:
        """Defence in depth over the allowlist above, for a NAMED message.

        These three names are the ones the harness actually declared before #150, so a
        re-introduction of one of them is worth its own sentence. The GENERAL property —
        no private policy under any name — is the allowlist's job, not this one's.
        """
        assert not hasattr(_surreal_harness, retired_name), (
            f"`_surreal_harness.{retired_name}` is back — the exact constant finding "
            f"#150 deleted. Its budget, its backoff and its conflict marker all live in "
            f"`loremaster.store._txn` and are reached through `retry_on_conflict` / "
            f"`is_retryable_conflict_error`. If you deliberately reintroduced a private "
            f"policy here, this pin is the conversation."
        )

    def test_the_module_level_imports_stay_confined_to_the_sdk_and_records(self) -> None:
        """RULING 1 (operator, 2026-07-20): ``_txn`` is reached by IN-FUNCTION import only.

        A module-level store import would turn any mid-TDD breakage in the store package
        into a COLLECTION error across every file that imports the harness — the
        isolation the harness's docstring has always promised. The lazy import keeps that
        promise while still sharing the seam.
        """
        offenders = sorted(
            name
            for name in _module_level_imported_modules(_harness_source())
            if name.startswith("loremaster") and name != _ALLOWED_MODULE_LEVEL_IMPORT
        )
        importers = _harness_importer_files()
        assert not offenders, (
            f"`_surreal_harness` imports {offenders} at MODULE level. Only "
            f"`{_ALLOWED_MODULE_LEVEL_IMPORT}` may be imported there; every store import "
            f"is in-function (RULING 1, 2026-07-20), so a store package that does not "
            f"yet compile mid-TDD cannot make {len(importers)} test files uncollectable."
        )

    @pytest.mark.parametrize(
        ("shape", "source"),
        [
            pytest.param(
                "try/except ImportError",
                "try:\n"
                "    from loremaster.store._txn import retry_on_conflict\n"
                "except ImportError:\n"
                "    retry_on_conflict = None\n",
                id="try-except",
            ),
            pytest.param(
                "module-level if",
                "import os\nif os.environ.get('X'):\n    from loremaster.store import _txn\n",
                id="if",
            ),
            pytest.param(
                "module-level with",
                "import contextlib\n"
                "with contextlib.suppress(Exception):\n"
                "    from loremaster.store import _txn\n",
                id="with",
            ),
            pytest.param(
                "module-level for",
                "for _ in range(1):\n    from loremaster.store import _txn\n",
                id="for",
            ),
            pytest.param(
                "module-level try/finally",
                "try:\n    from loremaster.store import _txn\nfinally:\n    pass\n",
                id="try-finally",
            ),
        ],
    )
    def test_the_import_scan_sees_every_shape_that_executes_at_import(
        self, shape: str, source: str
    ) -> None:
        """THE PROBE'S POSITIVE CONTROL — proven to fire on builds known to be broken.

        Each source here imports the store package AT IMPORT TIME while keeping the
        import out of ``tree.body``. The previous ``for node in tree.body`` scan returned
        ``[]`` for all of them: a green pin over a module that would take every importer
        down with it.
        """
        assert "loremaster.store._txn" in _module_level_imported_modules(
            source
        ) or "loremaster.store" in _module_level_imported_modules(source), (
            f"the module-level import scan does not see a store import inside a {shape}. "
            f"That shape executes on import, so it carries the full collection-error "
            f"blast radius the scan exists to prevent."
        )

    def test_the_import_scan_does_NOT_flag_an_in_function_import(self) -> None:
        """THE NEGATIVE CONTROL: the scan must not simply flag every occurrence.

        Without this leg, a scan that returned every import in the file — making the pin
        permanently RED-or-vacuous rather than discriminating — would pass every case
        above.
        """
        source = (
            "def f():\n"
            "    from loremaster.store._txn import retry_on_conflict\n"
            "    return retry_on_conflict\n"
            "class C:\n"
            "    import loremaster.store\n"
        )
        assert not [
            name
            for name in _module_level_imported_modules(source)
            if name.startswith("loremaster")
        ], "the scan flagged an import that does NOT execute at module import time"

    def test_the_harnesss_docstring_counts_are_the_DERIVED_counts(self) -> None:
        """The two populations in the harness docstring are re-derived, never trusted.

        "21 test files import this harness" was committed at four sites and was FALSE:
        **35** files import it; **21** call ``connect_admin``. Two real counts of two
        different populations, conflated into one sentence — the same defect shape as
        this repo's ten-`_query`-bodies-vs-eleven-bootstraps lesson, and one of the four
        sites was inside a FAILURE MESSAGE, so a reader was told the wrong number at the
        exact moment the gate fired (audit-150 R2).

        Prose that describes behaviour must be DERIVED from the behaviour or CHECKED
        against it. This is the check.
        """
        import re

        docstring = _surreal_harness.__doc__ or ""
        importers = _harness_importer_files()
        callers = _connect_admin_caller_files()

        # The two populations are genuinely different, or this pin proves nothing.
        assert set(callers) < set(importers), (
            "every `connect_admin` caller should also be an importer, and the two sets "
            "should not be equal — if they have become equal, the docstring's "
            "distinction is no longer meaningful and should be rewritten deliberately"
        )

        stated_importers = re.findall(r"(\d+) test files import this harness", docstring)
        stated_callers = re.findall(r"(\d+) test files — calls ``connect_admin``", docstring)
        assert len(stated_importers) == 1 and len(stated_callers) == 1, (
            f"the harness docstring no longer states exactly one importer count and one "
            f"`connect_admin`-caller count in the form this pin reads "
            f"(found {stated_importers} and {stated_callers}). Rewording is fine — "
            f"update this pin's patterns in the same diff so the numbers stay checked."
        )
        assert int(stated_importers[0]) == len(importers), (
            f"the harness docstring says {stated_importers[0]} test files import it; "
            f"{len(importers)} actually do. That number is the stated justification for "
            f"RULING 1's in-function import, so understating it understates the blast "
            f"radius."
        )
        assert int(stated_callers[0]) == len(callers), (
            f"the harness docstring says {stated_callers[0]} test files call "
            f"`connect_admin`; {len(callers)} actually do. Do not collapse this into the "
            f"importer count — they are different populations (audit-150 R2)."
        )
