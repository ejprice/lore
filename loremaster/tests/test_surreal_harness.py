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
harness now owns NO retry policy at all: no budget, no backoff, no marker.

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
constants at run time and asserts the harness's OBSERVED attempt count moves with them —
at BOTH the ``connect_admin`` path and the teardown path — with a positive control
showing the same assertion at the unmutated values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import _surreal_harness
import pytest
from _surreal_harness import SurrealEnv
from loremaster.store import _txn as txn_module
from surrealdb.errors import QueryError

# A fake connection target; the real topology is irrelevant since ``AsyncSurreal``
# itself is monkeypatched to return the fake below.
_FAKE_ENV = SurrealEnv(
    url="ws://127.0.0.1:19999/rpc",
    user="root",
    password="fake",
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


def _conflict_error() -> QueryError:
    return QueryError("Query", _CONFLICT_MESSAGE)


def _non_retryable_error() -> QueryError:
    return QueryError("Query", _NON_RETRYABLE_MESSAGE)


def _sustained_conflicts() -> list[BaseException | None]:
    """A script of DISTINCT conflict instances long enough to outlast any bound."""
    return [_conflict_error() for _ in range(_SUSTAINED_CONFLICTS)]


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
    """

    query_outcomes: list[BaseException | None] = field(default_factory=list)
    statement_outcomes: dict[str, list[BaseException | None]] = field(default_factory=dict)
    use_outcomes: list[BaseException | None] = field(default_factory=list)
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
        if not self.use_outcomes:
            return None
        outcome = self.use_outcomes[index]
        if isinstance(outcome, BaseException):
            raise outcome
        return None

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        self.operations.append(f"query:{statement}")
        self.query_calls += 1
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
    """

    async def _observed_bootstrap_attempts(self, monkeypatch: pytest.MonkeyPatch) -> int:
        """How many times ``connect_admin`` attempts a sustained-conflict statement."""
        fake = _FakeConnection(statement_outcomes={_DEFINE_NAMESPACE: _sustained_conflicts()})
        _patch_connection(monkeypatch, fake)
        with pytest.raises(txn_module.TxnContentionExhaustedError):
            await _surreal_harness.connect_admin(_FAKE_ENV)
        return fake.statement_calls[_DEFINE_NAMESPACE]

    async def _observed_teardown_attempts(self, monkeypatch: pytest.MonkeyPatch) -> int:
        """How many times ``drop_database`` attempts a sustained-conflict REMOVE."""
        fake = _FakeConnection(query_outcomes=_sustained_conflicts())
        _patch_connection(monkeypatch, fake)
        with pytest.raises(txn_module.TxnContentionExhaustedError):
            await _surreal_harness.drop_database(_FAKE_ENV)
        return fake.query_calls

    async def test_the_bootstrap_path_follows_the_seams_attempt_ceiling(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _silence_backoff(monkeypatch)

        # POSITIVE CONTROL: at the seam's real ceiling, the observed count IS it.
        control_ceiling = _seam_attempt_ceiling()
        assert await self._observed_bootstrap_attempts(monkeypatch) == control_ceiling

        # MUTATION: move the seam's ceiling; the harness's bootstrap must move with it.
        monkeypatch.setattr(
            txn_module, "_TXN_CONFLICT_ATTEMPT_CEILING", _MUTATED_ATTEMPT_CEILING
        )
        assert _seam_attempt_ceiling() != control_ceiling, "the mutation did not take"
        observed = await self._observed_bootstrap_attempts(monkeypatch)

        assert observed == _MUTATED_ATTEMPT_CEILING, (
            f"`connect_admin` attempted {observed} times after the store seam's attempt "
            f"ceiling moved to {_MUTATED_ATTEMPT_CEILING} (it was {control_ceiling}). "
            f"The harness is NOT sharing the seam's retry policy — it is running a "
            f"private budget that merely happens to call the shared driver, which is "
            f"the exact shape finding #150 exists to remove."
        )

    async def test_the_teardown_path_follows_the_seams_attempt_ceiling(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _silence_backoff(monkeypatch)

        control_ceiling = _seam_attempt_ceiling()
        assert await self._observed_teardown_attempts(monkeypatch) == control_ceiling

        monkeypatch.setattr(
            txn_module, "_TXN_CONFLICT_ATTEMPT_CEILING", _MUTATED_ATTEMPT_CEILING
        )
        assert _seam_attempt_ceiling() != control_ceiling, "the mutation did not take"
        observed = await self._observed_teardown_attempts(monkeypatch)

        assert observed == _MUTATED_ATTEMPT_CEILING, (
            f"teardown attempted {observed} times after the store seam's attempt ceiling "
            f"moved to {_MUTATED_ATTEMPT_CEILING} (it was {control_ceiling}). The "
            f"harness is running a private retry budget, not the seam's — finding #150."
        )

    async def test_both_paths_follow_the_seams_wall_clock_deadline(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Moving the seam's DEADLINE (not its ceiling) also moves both paths.

        A second, independent axis: the give-up predicate is
        ``ceiling reached`` OR (``deadline elapsed`` AND ``attempt floor met``). Driving
        the deadline to zero therefore lands both paths on the seam's attempt FLOOR — a
        different constant from the ceiling leg above, so a build that happened to agree
        with the seam on one number cannot agree with it on both by coincidence.
        """
        _silence_backoff(monkeypatch)

        # POSITIVE CONTROL: with the real (non-zero) deadline, both paths run to the
        # CEILING, which is emphatically not the floor.
        ceiling = _seam_attempt_ceiling()
        floor = _seam_attempt_floor()
        assert ceiling != floor, "the ceiling and floor coincide; this pin cannot discriminate"
        assert await self._observed_bootstrap_attempts(monkeypatch) == ceiling
        assert await self._observed_teardown_attempts(monkeypatch) == ceiling

        # MUTATION: a zero wall-clock budget makes the FLOOR the binding bound.
        monkeypatch.setattr(txn_module, "_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS", 0.0)

        bootstrap_observed = await self._observed_bootstrap_attempts(monkeypatch)
        teardown_observed = await self._observed_teardown_attempts(monkeypatch)

        assert bootstrap_observed == floor, (
            f"`connect_admin` attempted {bootstrap_observed} times under a zero seam "
            f"deadline; the seam's attempt floor is {floor}. The bootstrap is not "
            f"reading the seam's wall-clock budget."
        )
        assert teardown_observed == floor, (
            f"teardown attempted {teardown_observed} times under a zero seam deadline; "
            f"the seam's attempt floor is {floor}. Teardown is not reading the seam's "
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


class TestTheHarnessDeclaresNoRetryPolicyOfItsOwn:
    """The structural half of finding #150: there is nothing left to drift.

    The retired drift pin (``test_retry_seam.py``'s
    ``TestTheTestHarnessCannotDriftFromTheSeamsMarker``) guarded a copy it could not
    delete. The copy is now gone, and this asserts the deletion — so a future edit that
    reintroduces a private budget/backoff/marker goes RED here rather than being
    discovered by a suite that quietly stops retrying.

    A ``Callable`` typed attribute is not what is being hunted: these are the three
    POLICY constants the harness used to declare, each of which is now the seam's alone.
    """

    @pytest.mark.parametrize(
        "retired_name",
        ["_RETRYABLE_CONFLICT_MARKER", "_MAX_DROP_DATABASE_ATTEMPTS", "_DROP_DATABASE_BACKOFF_SECONDS"],
    )
    def test_the_private_policy_constants_are_gone(self, retired_name: str) -> None:
        assert not hasattr(_surreal_harness, retired_name), (
            f"`_surreal_harness.{retired_name}` is back. The harness owns NO retry "
            f"policy: its budget, its backoff and its conflict marker all live in "
            f"`loremaster.store._txn` and are reached through `retry_on_conflict` / "
            f"`is_retryable_conflict_error` (finding #150). If you deliberately "
            f"reintroduced a private policy here, this pin is the conversation."
        )

    def test_the_module_level_imports_stay_confined_to_the_sdk_and_records(self) -> None:
        """RULING 1 (operator, 2026-07-20): ``_txn`` is reached by IN-FUNCTION import only.

        The harness is imported by 21 test files. A module-level store import would turn
        any mid-TDD breakage in the store package into a COLLECTION error across all of
        them — the isolation the harness's docstring has always promised. The lazy import
        keeps that promise while still sharing the seam.
        """
        import ast
        import pathlib

        source = pathlib.Path(_surreal_harness.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        module_level_modules: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                module_level_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                module_level_modules.add(node.module)

        offenders = sorted(
            name
            for name in module_level_modules
            if name.startswith("loremaster") and not name.startswith("loremaster.index.records")
        )
        assert not offenders, (
            f"`_surreal_harness` imports {offenders} at MODULE level. Only "
            f"`loremaster.index.records` may be imported there; every store import is "
            f"in-function (RULING 1, 2026-07-20), so a store package that does not yet "
            f"compile mid-TDD cannot make 21 test files uncollectable."
        )
