"""Contract tests for finding #102 — ``TxnContentionExhaustedError``: the TYPED
seam between "the engine made us retry until we ran out of budget" and every
caller that has to tell that apart from its own domain failures.

WHY THIS MODULE EXISTS SEPARATELY. Every pin here needed a name that did not
exist before 9d29111 (``TxnContentionExhaustedError``, now at ``_txn.py``), so this
module could not even be COLLECTED against the then-unrepaired tree — its failure is an ``ImportError``, which
proves nothing about behaviour. The pins that COULD be behaviourally red (pre-9d29111)
therefore live in the modules they belong to, where they are red for the right
reason and the rest of the suite still runs:

  * ``test_surreal_store.py`` — the live rolled-back-conflict SHAPE (the marker
    on the LAST entry only), the root-cause selection, the jittered backoff, the
    no-control-flow-on-labels repo invariant, and the guard on briefs' inherited
    conflict budget.
  * ``test_findings.py`` — the 16/32-way live mint, and the deletion of the dead
    hand-rolled mint backstop.

Read those first; this module is the type-level half of the same contract.

------------------------------------------------------------------------------
THE CONTRACT THIS MODULE DECIDES (the builder builds FROM this):

    class TxnContentionExhaustedError(SurrealStoreError):
        '''A genuine write-write conflict outlived the retry budget.'''

        def __init__(
            self, message: str, *, attempts: int, elapsed_seconds: float
        ) -> None: ...

        attempts: int            # transaction attempts actually made
        elapsed_seconds: float   # wall time spent across all of them

    async def execute_transaction(
        statement, params, *, acquire, drop, url,
        deadline_seconds: float | None = None,   # None => the module default
    ) -> None

The CONSTRUCTOR is part of the contract, not just the attributes — see
``_contention_exhausted()`` below for why leaving it unpinned is a live hazard.

Two properties do the load-bearing work, and both are TYPES rather than prose:

1. It SUBCLASSES ``SurrealStoreError``. Every existing ``except SurrealStoreError``
   keeps catching it, so introducing it changes no caller's behaviour by
   accident — only the callers that opt IN by naming the new type behave
   differently. (That is also why the pass-through pins below matter: a subclass
   is caught by the old handlers *by default*, which is the safe direction for
   compatibility and the WRONG direction for the three handlers that would
   otherwise report exhausted contention as a lost compare-and-set.)

2. It carries ``attempts`` and ``elapsed_seconds`` as ATTRIBUTES, and its message
   is DERIVED from them. This repo has now shipped ten defects in the class
   "English beside the code that says what the code does, and is wrong" — a
   docstring promising "12 × 5 = 60 attempts, measured-safe" for a loop that
   never ran once is the very defect this finding is made of. A number a caller
   can READ cannot drift from the number the code MADE.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.findings import FindingLedger
from loremaster.store._txn import (
    _RETRYABLE_CONFLICT_MARKER,
    SurrealStoreError,
    TxnContentionExhaustedError,
    _SurrealConnection,
    execute_transaction,
)

# ``findings`` and ``tasks`` each define their OWN ``IllegalTransitionError``, and
# they are UNRELATED classes (verified: `issubclass` is False in both directions —
# one descends from ``FindingLedgerError``, the other from ``TaskLedgerError``).
# The v1 contract imported the FINDINGS one and asserted it around a TASK ledger
# call, so the counterweight could never pass — on ANY build, correct or wrong.
# They are aliased apart here so the mistake cannot be made silently again.
from loremaster.tasks import IllegalTransitionError as TaskIllegalTransitionError
from loremaster.tasks import TaskLedger
from pydantic import SecretStr

from loremaster import findings as findings_module
from loremaster import tasks as tasks_module

# --- the live engine texts (mirrors test_surreal_store.py's, deliberately) ----
# The exact live retryable-conflict text. The marker rides the COMMIT entry.
_CONFLICT_ENGINE_TEXT = (
    f"Cannot COMMIT: Transaction conflict: Resource busy. This transaction "
    f"{_RETRYABLE_CONFLICT_MARKER}"
)
# What the engine writes for statements that never ran because an earlier one
# (or the COMMIT) failed. Marker-less: this is the text a ``[0]``-classifier
# reads, and why it calls a conflict "unspecified".
_CASCADE_ENGINE_TEXT = "The query was not executed due to a failed transaction"
# A domain rejection: an ASSERT violation echoing a bound value back verbatim.
_SENSITIVE_MARKER = "TOP-SECRET-BOUND-VALUE-102"
# LIVE-CAPTURED ASSERT text (SurrealDB 3.1.5, spike-surreal, 2026-07-13,
# scratchpad/contract-v5/capture_engine.py). The engine says "must conform to";
# it has NEVER said "assertion". The previous, hand-typed value here contained the
# word "assert" and so matched the classifier's marker — which is exactly why the
# ASSERT class looked alive for this repo's entire life while never once firing in
# production (audit B2). Fixture and code shared one imagination.
_SENSITIVE_ENGINE_TEXT = (
    f"Found '{_SENSITIVE_MARKER}' for field `status`, with record `finding:abc`, "
    f"but field must conform to: "
    f"$value INSIDE ['open', 'acknowledged', 'resolved', 'wontfix']"
)

_OK_STATEMENT: dict[str, Any] = {"status": "OK", "result": None}

# See test_surreal_store.py's ``_ABSURD_ATTEMPT_CEILING``: not a budget, an
# absurdity stop, so an unbounded retry loop fails fast and legibly instead of
# hanging until the runner's timeout.
_ABSURD_ATTEMPT_CEILING = 5_000

# A deadline short enough to keep the deadline-branch pins fast, long enough
# that several attempts genuinely fit inside it.
_SHORT_DEADLINE_SECONDS = 0.25

# The default budget must be finite and reachable in a test's patience. Not a
# pin on its VALUE (the repair's survey sets that) — a bound on its absurdity.
_DEFAULT_BUDGET_SANITY_CEILING_SECONDS = 30.0


def _rolled_back_response(*results: str | None) -> dict[str, Any]:
    """A ``query_raw``-shaped response: ``None`` → an OK statement, a string →
    an ERR statement carrying that text.
    """
    return {
        "result": [
            dict(_OK_STATEMENT) if text is None else {"status": "ERR", "result": text}
            for text in results
        ]
    }


def _live_conflict_response() -> dict[str, Any]:
    """The LIVE conflict-rollback shape: cascade, cascade, conflict-marked COMMIT.

    The marker is on the LAST entry ONLY. THE fixture value the whole finding
    turns on — every pre-#102 conflict fixture put it on entry ``[0]``, a shape
    the engine never emits, and so could not tell a correct build from a broken
    one.
    """
    return _rolled_back_response(
        _CASCADE_ENGINE_TEXT, _CASCADE_ENGINE_TEXT, _CONFLICT_ENGINE_TEXT
    )


def _marker_first_conflict_response() -> dict[str, Any]:
    """The marker on entry ``[0]`` — the OTHER position, kept because a
    position-branching build must be caught at both ends.
    """
    return _rolled_back_response(_CONFLICT_ENGINE_TEXT)


_CONFLICT_SHAPES = [
    pytest.param(_live_conflict_response, id="marker-last-LIVE"),
    pytest.param(_marker_first_conflict_response, id="marker-first"),
]


@dataclass
class _SustainedConflictConnection:
    """A fake SDK connection that answers EVERY ``query_raw`` with the same
    rolled-back conflict — unresolvable contention, for as many attempts as the
    seam cares to make.
    """

    response: dict[str, Any]
    calls: int = field(default=0, init=False)

    async def query_raw(self, statement: str, params: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        if self.calls > _ABSURD_ATTEMPT_CEILING:
            raise AssertionError(
                f"more than {_ABSURD_ATTEMPT_CEILING} attempts against sustained "
                f"contention — the retry budget is effectively unbounded"
            )
        return self.response

    def check_response_for_error(self, response: Any, method: str) -> None:
        return None

    async def close(self) -> None:
        return None


async def _run_txn(
    connection: Any, *, deadline_seconds: float | None = _SHORT_DEADLINE_SECONDS
) -> None:
    """Drive ``execute_transaction`` against ``connection``. The statement text is
    irrelevant — the fake replays canned responses and never parses it.
    """

    async def _acquire() -> _SurrealConnection:
        return cast("_SurrealConnection", connection)

    async def _drop(_: Any) -> None:
        raise AssertionError("a conflict must never tear down a healthy connection")

    await execute_transaction(
        "BEGIN;\nUPDATE finding_counter SET seq += 1;\nCOMMIT;",
        {},
        acquire=_acquire,
        drop=_drop,
        url="ws://127.0.0.1:19555/rpc",  # unreachable — never dialed
        deadline_seconds=deadline_seconds,
    )


class TestContentionExhaustionIsTyped:
    """A genuine conflict that outlives the retry budget raises a TYPED error —
    at BOTH marker positions.

    This is the whole finding at the seam. Today the live shape (marker on the
    last entry) is classified off entry ``[0]`` — a cascade line that says only
    "the query was not executed" — so the seam reports an "unspecified
    rejection". Callers downstream then have nothing to branch on but that
    string, and findings' hand-rolled mint backstop did exactly that — and died
    silently when the string changed.
    """

    @pytest.mark.parametrize("build_response", _CONFLICT_SHAPES)
    async def test_exhausted_conflict_raises_the_typed_error(
        self, build_response: Callable[[], dict[str, Any]]
    ) -> None:
        connection = _SustainedConflictConnection(response=build_response())

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await _run_txn(connection)

        error = exc_info.value
        assert connection.calls >= 2, "a conflict must be RETRIED before it is given up on"
        assert connection.calls < _ABSURD_ATTEMPT_CEILING

        # Compatibility: every existing ``except SurrealStoreError`` still catches
        # it, so adding the type breaks no caller that has not opted in.
        assert isinstance(error, SurrealStoreError)

        # Hygiene (ledger #31): the raw engine text can echo a bound value.
        assert _CONFLICT_ENGINE_TEXT not in str(error)

    @pytest.mark.parametrize("build_response", _CONFLICT_SHAPES)
    async def test_the_typed_error_carries_the_numbers_its_message_quotes(
        self, build_response: Callable[[], dict[str, Any]]
    ) -> None:
        """``attempts`` and ``elapsed_seconds`` are ATTRIBUTES, and the message is
        derived from them.

        The anti-prose-drift pin. The deleted mint backstop's docstring promised
        "12 × 5 = 60 transaction attempts … measured-safe" about a loop that had
        never executed a single retry; nothing could catch it, because the claim
        was English sitting NEXT TO the code rather than derived FROM it. A
        number the caller can read off the exception cannot drift from the number
        the code actually made — and an operator triaging a contention storm
        needs the real one.
        """
        connection = _SustainedConflictConnection(response=build_response())
        started = time.monotonic()

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await _run_txn(connection)

        wall_elapsed = time.monotonic() - started
        error = exc_info.value

        assert error.attempts == connection.calls, (
            f"the error reports {error.attempts} attempts but the engine was actually "
            f"asked {connection.calls} times"
        )
        assert 0.0 < error.elapsed_seconds <= wall_elapsed + 1.0
        # Derived, not restated: the message quotes the attribute it carries.
        assert str(error.attempts) in str(error)

    async def test_a_domain_rejection_is_never_the_contention_type(self) -> None:
        """THE overcorrection pin — and the reason ``pytest.raises(SurrealStoreError)``
        alone can never certify this repair.

        ``TxnContentionExhaustedError`` SUBCLASSES ``SurrealStoreError``. So a
        build that simply types EVERY rollback as contention exhaustion satisfies
        every ``pytest.raises(SurrealStoreError)`` in the suite — including the
        finding-#93 pins — while destroying the distinction this finding exists to
        create. A domain rejection (an ASSERT violation; no conflict marker
        anywhere) must be a plain ``SurrealStoreError``, retried never.
        """
        connection = _SustainedConflictConnection(
            response=_rolled_back_response(_SENSITIVE_ENGINE_TEXT, _CASCADE_ENGINE_TEXT)
        )

        with pytest.raises(SurrealStoreError) as exc_info:
            await _run_txn(connection)

        assert not isinstance(exc_info.value, TxnContentionExhaustedError), (
            "an ASSERT violation was reported as exhausted CONTENTION — retrying it "
            "would never have helped, and a caller that retries on this type will now "
            "hammer a write that can never succeed"
        )
        assert connection.calls == 1, "a domain rejection must never be retried"
        assert _SENSITIVE_MARKER not in str(exc_info.value)


class TestContentionBudgetIsBounded:
    """The budget is a WALL-CLOCK DEADLINE with an attempt ceiling as the runaway
    backstop — not a bare attempt count.

    Why the shape matters: an attempt count alone cannot express "give up after
    a while" when the backoff is random, and a random backoff is exactly what the
    repair introduces. The deadline is the promise a caller can actually reason
    about; the attempt ceiling only stops a pathological spin when every draw
    lands near zero.
    """

    async def test_the_deadline_is_honoured(self) -> None:
        """The caller's deadline bounds the whole call.

        Reachability: without a caller-settable deadline this branch could only be
        exercised by waiting out the module default, so it would never be tested
        and would rot. A branch no test reaches is dead code waiting to be
        discovered by an auditor (this repo's law) — and dead retry code is
        precisely what finding #102 IS.
        """
        connection = _SustainedConflictConnection(response=_live_conflict_response())
        started = time.monotonic()

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await _run_txn(connection, deadline_seconds=_SHORT_DEADLINE_SECONDS)

        elapsed = time.monotonic() - started
        assert elapsed < _SHORT_DEADLINE_SECONDS * 4, (
            f"the call ran {elapsed:.3f}s against a {_SHORT_DEADLINE_SECONDS}s deadline — "
            f"the deadline is not bounding the retry loop"
        )
        assert exc_info.value.elapsed_seconds > 0

    async def test_a_longer_deadline_buys_more_attempts(self) -> None:
        """The deadline must be what ACTUALLY stops the loop — not decoration on
        top of an attempt ceiling that does the real work.

        The wall-clock pin above can be satisfied by accident: a build with NO
        deadline at all, whose attempt ceiling and backoff cap happen to multiply
        out to less than the deadline, finishes in time and looks compliant. This
        one cannot be. Give the seam ten times the budget and it must use it —
        a ceiling-bounded build makes the SAME number of attempts either way,
        because the clock was never consulted.

        Constant-free: it compares two budgets against each other rather than
        asserting anything about how many attempts either one should buy.
        """
        brief = _SustainedConflictConnection(response=_live_conflict_response())
        with pytest.raises(TxnContentionExhaustedError):
            await _run_txn(brief, deadline_seconds=_SHORT_DEADLINE_SECONDS)

        generous = _SustainedConflictConnection(response=_live_conflict_response())
        with pytest.raises(TxnContentionExhaustedError):
            await _run_txn(generous, deadline_seconds=_SHORT_DEADLINE_SECONDS * 10)

        assert generous.calls > brief.calls, (
            f"a 10x longer deadline bought no extra attempts ({generous.calls} vs "
            f"{brief.calls}) — the retry loop is bounded by an attempt ceiling and is "
            f"ignoring the clock; the deadline is decoration"
        )

    async def test_the_default_budget_is_finite_and_retries_generously(self) -> None:
        """No caller passes a deadline today, so the DEFAULT is what production
        actually runs on. It must be finite (this test would hang otherwise) and
        it must be worth having — a budget that gives up after one retry is not a
        retry policy.

        Deliberately does NOT pin the default's value: #102 exists because a
        constant tuned for 2-way contention was never re-measured, and minting its
        replacement by assertion here would repeat that mistake exactly. The
        builder's committed survey sets the number; this pins only that it is not
        absurd.
        """
        connection = _SustainedConflictConnection(response=_live_conflict_response())
        started = time.monotonic()

        with pytest.raises(TxnContentionExhaustedError) as exc_info:
            await _run_txn(connection, deadline_seconds=None)

        elapsed = time.monotonic() - started
        assert exc_info.value.attempts >= 3, (
            f"the default budget gave up after {exc_info.value.attempts} attempts — too "
            f"thin to survive the N-way contention the finding mint actually sees"
        )
        assert elapsed < _DEFAULT_BUDGET_SANITY_CEILING_SECONDS, (
            f"the default budget ran {elapsed:.1f}s — a caller (and an MCP client "
            f"waiting on it) cannot be parked that long"
        )


# ===========================================================================
# The three rollback handlers — exhausted contention is NOT a lost race.
#
# ``findings._transition``, ``tasks.transition`` and ``tasks.supersede_task``
# each guard a compare-and-set with a THROW, and each reads a rolled-back
# ``SurrealStoreError`` as "my CAS matched zero rows, so a concurrent writer
# committed first" — re-reading the row and raising ``IllegalTransitionError``.
#
# That inference is sound for a CAS rollback. It is FALSE for contention
# exhaustion, which means "I never got to find out." The row may be untouched and
# the caller's transition perfectly legal; reporting it as an illegal transition
# tells an agent its work was refused when in truth it was never attempted — and
# because ``TxnContentionExhaustedError`` subclasses ``SurrealStoreError``, that
# is what these handlers do BY DEFAULT unless they opt out. The subclassing that
# makes the type safe to introduce is the same subclassing that makes this pin
# mandatory.
#
# Fault injection: the ledgers are REAL and live (every read, every row, the real
# schema); only the transaction seam is replaced, so what is under test is purely
# the handler's reaction to an exhausted conflict.
# ===========================================================================

_TASK_SUBJECT = "wire the repaired conflict-retry seam into the finding mint"
_TASK_DESCRIPTION = (
    "Delete the dead string-gated backstop; the seam owns the retry, jittered, "
    "with a typed exhaustion error."
)
_TASK_OWNER = "builder-102"
_ACTOR = "team-lead-session-9f2b"
_STATUS_IN_PROGRESS = "in_progress"
_STATUS_DONE = "done"


# ===========================================================================
# THE PIN THAT ENDS #102 — and it is not a scanner.
#
# Three contract revisions tried to FORBID the prose-coupling syntactically: ban
# the comparison (v1), ban the label (v2), ban the message reaching a condition
# (v3). Each was defeated by a one-line refactor, and the third — the most
# elaborate — waved through 13 of 15 evasions, because a syntactic scan over one
# `except` body cannot see prose that leaves the body (a helper in another module,
# a `match`, a bare `except`, a classifier object). The evasion space is unbounded.
# You cannot enumerate it. I kept climbing that hill for three rounds.
#
# The property we actually care about was never syntactic:
#
#     ** IF THE LABEL IS REWORDED, DOES CONTENTION HANDLING STILL WORK? **
#
# That is not a hypothetical. It is finding #93, verbatim: #93 legitimately changed
# WHICH failed statement gets classified, the label for an exhausted conflict
# silently became "unspecified rejection", and the mint's 12-attempt backstop —
# which was gated on the old prose — became dead code that no gate could see. That
# is the entire causal chain of finding #102.
#
# So: TEST IT. Raise the SAME typed error carrying a DIFFERENT message, and require
# every handler to behave identically. A build that branches on the TYPE passes both
# spellings. A build that branches on the PROSE — however it is spelled, through
# however many helper functions, past a `match`, out of the handler entirely —
# fails the reworded one. No refactor evades this, because it is not looking at the
# code at all.
#
# This is nothing more than THIS REPO'S OWN LAW, applied to the value at the root of
# the finding: **"if the code can branch on a value, at least one pin must use a
# DIFFERENT value."** The label is a value the code can branch on. My v1 report
# quoted that rule while criticising other people's fixtures — and then I shipped a
# fixture with ONE hardcoded message containing the word "conflict", handing every
# prose-matching build the exact word it needed. Parameter-value monoculture, the
# repo's own named failure mode, in the contract written to prevent it.
# ===========================================================================

# An ARBITRARY message that CARRIES the current classification label ("retryable
# conflict"). That property — the label is present — is its entire job here: it is the
# row a prose-matching build passes, and the discriminator against the two rows below
# (a reworded message that shares no token, and no message at all).
#
# ⚠ ITS EXACT WORDING IS NOT PRODUCTION'S, AND MUST NEVER BE RE-SYNCED TO IT. Every pin
# fed this value is message-AGNOSTIC by construction (see the block above), so the seam's
# real sentence is irrelevant — and pinning it here would re-create the coupling this
# whole file exists to kill.
#
# THE PROOF THAT IT IS ARBITRARY IS THIS CONSTANT'S OWN HISTORY. It used to be called
# `_LABEL_BEARING_MESSAGE`, above a comment reading "the message the seam raises TODAY",
# and it spelled "SurrealDB **transaction** gave up…". Finding #108's DRY consolidation
# then changed the seam to raise "SurrealDB **operation** gave up…" (`_txn.py:851`), and
# **not one test noticed, because not one test reads it** — exactly as designed. The
# comment simply went on lying for a whole wave until a cold audit caught it
# (audit-dry-2 F5). English beside the code, saying what the code does, and wrong: this
# repo's most-shipped defect class, inside the file written to end a defect of the same
# family. The name now states the PROPERTY it must have instead of a fact about
# production it cannot keep.
_LABEL_BEARING_MESSAGE = (
    "SurrealDB operation gave up after 64 attempts over 2.000s "
    "(retryable conflict); see the server log for the full engine detail"
)

# The SAME error after a legitimate rewording — finding #93 replayed. Deliberately
# shares NO discriminating token with the message above: not "conflict", not
# "retryable", not even the sentence stem ("gave up after N attempts"), which is
# itself unique to contention and which a prose-gate could otherwise key on to
# straddle both spellings. Two messages that overlap nowhere; one exception type.
_REWORDED_LABEL_MESSAGE = (
    "the write could not be applied: the row stayed busy for 2.000s across 64 "
    "attempts and the budget ran out; consult the server log"
)

# Hostile third value: a build that reads the prose has NOTHING to read. The
# message is not part of the pass-through contract, so an empty one must change
# nothing.
_EMPTY_MESSAGE = ""

# If the code can branch on a value, at least one pin must use a DIFFERENT value.
_CONTENTION_MESSAGES = [
    pytest.param(_LABEL_BEARING_MESSAGE, id="label-bearing"),
    pytest.param(_REWORDED_LABEL_MESSAGE, id="REWORDED-label"),
    pytest.param(_EMPTY_MESSAGE, id="EMPTY-message"),
]


def _contention_exhausted(message: str = _LABEL_BEARING_MESSAGE) -> TxnContentionExhaustedError:
    """The exception the repaired seam raises when a real conflict outlives the
    budget — the exact object these handlers must let past untouched.

    ``message`` is a PARAMETER, and that is the whole point (see the block above):
    every pass-through pin runs against all of :data:`_CONTENTION_MESSAGES`, so a
    handler that depends on the message's prose fails on a spelling it was not
    handed.

    **This CONSTRUCTS the error, so it also pins the constructor**::

        TxnContentionExhaustedError(message, *, attempts: int, elapsed_seconds: float)

    A builder who makes the attributes required keyword-only arguments — the
    natural implementation, and the one that guarantees they can never be forgotten
    — would otherwise have broken every pin below **on a correct build**. A pin that
    is red no matter what the builder does teaches the builder to ignore reds.
    """
    return TxnContentionExhaustedError(message, attempts=64, elapsed_seconds=2.0)


@pytest_asyncio.fixture()
async def live_env() -> Any:
    """A throwaway database on spike-surreal, reaped afterwards."""
    env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def live_finding_ledger(live_env: SurrealEnv) -> Any:
    ledger = FindingLedger(
        url=live_env.url,
        namespace=live_env.namespace,
        database=live_env.database,
        user=live_env.user,
        password=live_env.password,
    )
    await ledger.ensure_ready()
    try:
        yield ledger
    finally:
        await ledger.close()


@pytest_asyncio.fixture()
async def live_task_ledger(live_env: SurrealEnv) -> Any:
    ledger = TaskLedger(
        url=live_env.url,
        namespace=live_env.namespace,
        database=live_env.database,
        user=live_env.user,
        password=live_env.password,
    )
    await ledger.ensure_ready()
    try:
        yield ledger
    finally:
        await ledger.close()


def _explode_with_contention(
    monkeypatch: pytest.MonkeyPatch, module: Any, message: str = _LABEL_BEARING_MESSAGE
) -> None:
    """Replace ``module``'s transaction seam with one that always reports exhausted
    contention, carrying ``message``. Everything else about the ledger stays real.
    """

    async def _exhausted(*args: Any, **kwargs: Any) -> None:
        raise _contention_exhausted(message)

    monkeypatch.setattr(module, "execute_transaction", _exhausted)


class TestContentionIsNeverReportedAsALostRace:
    """Every guarded-CAS handler lets ``TxnContentionExhaustedError`` through
    UNCHANGED — it is not an illegal transition, and it is not a lost race.
    """

    @pytest.mark.parametrize("message", _CONTENTION_MESSAGES)
    async def test_finding_transition_propagates_contention_untouched(
        self, live_finding_ledger: FindingLedger, monkeypatch: pytest.MonkeyPatch, message: str
    ) -> None:
        """RED against today's handler (findings.py:1058): it catches
        ``SurrealStoreError``, re-reads the row, finds it STILL ``open`` (nothing
        was written — the transaction never landed), and raises
        ``IllegalTransitionError`` for the perfectly legal edge ``open ->
        resolved``. The caller is told its transition was refused when in fact it
        was never attempted.
        """
        reported = await live_finding_ledger.report(
            "seam contention must not read as a lost CAS",
            "a rolled-back transaction and an exhausted retry budget are different facts",
            area="lore_findings",
            category="capability_gap",
            created_by=_ACTOR,
        )
        _explode_with_contention(monkeypatch, findings_module, message)

        with pytest.raises(TxnContentionExhaustedError):
            await live_finding_ledger.resolve(reported.number, _ACTOR)

    @pytest.mark.parametrize("message", _CONTENTION_MESSAGES)
    async def test_task_transition_propagates_contention_untouched(
        self, live_task_ledger: TaskLedger, monkeypatch: pytest.MonkeyPatch, message: str
    ) -> None:
        """RED against today's handler (tasks.py:875) for the same reason."""
        task_id = await live_task_ledger.create_task(
            _TASK_SUBJECT, _TASK_DESCRIPTION, created_by=_ACTOR
        )
        await live_task_ledger.claim_task(task_id, _TASK_OWNER)
        _explode_with_contention(monkeypatch, tasks_module, message)

        with pytest.raises(TxnContentionExhaustedError):
            await live_task_ledger.transition(task_id, _STATUS_IN_PROGRESS, actor=_TASK_OWNER)

    @pytest.mark.parametrize("message", _CONTENTION_MESSAGES)
    async def test_task_supersede_propagates_contention_untouched(
        self, live_task_ledger: TaskLedger, monkeypatch: pytest.MonkeyPatch, message: str
    ) -> None:
        """RED against today's handler (tasks.py:1139): it would report the task
        as "already superseded by someone else" — a claim about another agent's
        action that never happened.
        """
        task_id = await live_task_ledger.create_task(
            _TASK_SUBJECT, _TASK_DESCRIPTION, created_by=_ACTOR
        )
        _explode_with_contention(monkeypatch, tasks_module, message)

        with pytest.raises(TxnContentionExhaustedError):
            await live_task_ledger.supersede_task(
                task_id,
                subject=f"{_TASK_SUBJECT} (restated)",
                description=_TASK_DESCRIPTION,
                created_by=_ACTOR,
            )

    @pytest.mark.parametrize("message", _CONTENTION_MESSAGES)
    async def test_task_claim_propagates_contention_rather_than_reporting_a_loss(
        self, live_task_ledger: TaskLedger, monkeypatch: pytest.MonkeyPatch, message: str
    ) -> None:
        """The claim path has no rollback handler today, so contention already
        propagates — this pin FREEZES that.

        The tempting "fix" during this repair is to catch the new type at the
        claim seam and return ``ClaimResult(claimed=False)``, since a claim that
        did not land looks like a claim that was lost. It is not: a lost claim
        means someone else HOLDS the task; exhausted contention means nobody knows
        who holds it. An orchestrator that reads the first for the second hands
        the work to a second agent while the first may still be doing it.
        """
        task_id = await live_task_ledger.create_task(
            _TASK_SUBJECT, _TASK_DESCRIPTION, created_by=_ACTOR
        )
        _explode_with_contention(monkeypatch, tasks_module, message)

        with pytest.raises(TxnContentionExhaustedError):
            await live_task_ledger.claim_task(task_id, _TASK_OWNER)

    async def test_a_rolled_back_cas_still_reports_an_illegal_transition(
        self, live_task_ledger: TaskLedger, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """THE COUNTERWEIGHT — the pin that stops the pass-throughs from being
        implemented by DELETING the handler they sit above.

        Every pass-through pin above can be turned green by removing the
        ``except SurrealStoreError`` block outright. So this pins the other half:
        a rolled-back CAS (the guard's THROW matched zero rows — a *plain*
        ``SurrealStoreError``, no conflict marker) must STILL become an
        ``IllegalTransitionError``. Contention passes through; a lost race does not.

        **Fault-injected, not raced** — and that is the whole point. v1's
        counterweight drove an illegal EDGE (``done -> in_progress``), which
        ``_validate_transition`` refuses *before any write*: it never reached the
        rollback handler, so it could not see the handler being deleted. Proven —
        it passes on the delete-the-handler build. Injecting a rolled-back
        transaction at the seam reaches the handler deterministically, on every run,
        with no reliance on winning a race.

        (The live races in ``test_task_ledger.py`` — ``TestConcurrentTransitions``,
        ``TestSameTargetTransitionRace``, ``TestConcurrentSupersession`` — remain
        the end-to-end guard and must stay green. This pin is the belt to their
        braces, and it names the failure directly.)
        """
        task_id = await live_task_ledger.create_task(
            _TASK_SUBJECT, _TASK_DESCRIPTION, created_by=_ACTOR
        )
        await live_task_ledger.claim_task(task_id, _TASK_OWNER)

        async def _rolled_back_cas(*args: Any, **kwargs: Any) -> None:
            # What the guard's THROW produces when a concurrent writer got there
            # first: a plain rollback, carrying NO conflict marker.
            raise SurrealStoreError(
                "SurrealDB transaction failed and was rolled back: statement 2 of 3 "
                "was rejected (unspecified rejection); see the server log"
            )

        monkeypatch.setattr(tasks_module, "execute_transaction", _rolled_back_cas)

        # NOTE the class: a TaskLedger raises ``tasks.IllegalTransitionError``, NOT
        # the identically-named findings one. Asserting the wrong class here is how
        # v1 of this contract shipped a counterweight that failed on every build
        # alike — correct ones included.
        with pytest.raises(TaskIllegalTransitionError):
            await live_task_ledger.transition(task_id, _STATUS_IN_PROGRESS, actor=_TASK_OWNER)


class TestFindingMintSurfacesContentionEndToEnd:
    """The mint, end-to-end, with NOTHING mocked but the socket.

    A real ``FindingLedger``, its real ``report()``, its real fragment, the real
    ``compose()``, the real ``execute_transaction`` — and a connection that
    answers with the live conflict shape forever. This is the one pin in the file
    that exercises the ENTIRE path the finding lives on, and it is possible only
    because ``report()`` (without ``supersedes``) reads nothing before it writes.

    What it catches that the seam pins alone cannot: a repaired seam that raises
    the typed error correctly, while ``report()`` still routes through a
    string-gated backstop that swallows or relabels it on the way out.
    """

    async def test_report_surfaces_sustained_contention_as_the_typed_error(
        self,
    ) -> None:
        ledger = FindingLedger(
            url="ws://127.0.0.1:19555/rpc",  # never dialed — the fake handle short-circuits
            namespace="ns",
            database="db",
            user="root",
            password=SecretStr("root"),
        )
        connection = _SustainedConflictConnection(response=_live_conflict_response())
        ledger._connection = cast("_SurrealConnection", connection)

        with pytest.raises(TxnContentionExhaustedError):
            await ledger.report(
                "the mint must not lie about why it failed",
                "sustained contention on finding_counter is not an unspecified rejection",
                area="lore_findings",
                category="capability_gap",
                created_by=_ACTOR,
            )

        assert connection.calls >= 2, (
            "the mint gave up without a single retry — the exact symptom of the dead "
            "backstop (its string gate stopped matching, so it re-raised immediately)"
        )
