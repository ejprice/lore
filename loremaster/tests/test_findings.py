"""Contract tests for ``loremaster.findings`` — the durable, fleet-visible
FINDING LEDGER (lore v2 P8b), against the REAL SurrealDB server.

``FindingLedger`` is the friction/finding coordination primitive: a table of
findings the fleet can FILE (``report`` — minting a race-safe, human-addressable
consecutive NUMBER), browse in order (``query`` — ordered by number ASC), address
by that stable number OR by opaque id (``get``), follow a supersedes chain to its
head (``chain_head``), and drive through a small review state machine
(``acknowledge`` / ``resolve`` / ``wontfix``). It rides the SAME store machinery
``loremaster.tasks`` uses (one signed-in SurrealDB connection; every mutation
rides ``compose()`` + ``execute_transaction()`` — a single ``BEGIN … COMMIT`` with
per-statement verification and bounded optimistic-concurrency retry). These tests
run against a LIVE engine (see ``_surreal_harness``) because every behaviour that
matters — the race-safe number mint, the transition compare-and-set, cross-session
visibility — is a server-side property no fake can stand in for at this phase.

The pinned contract (the public surface THIS FILE decides — the module is built
FROM this contract):

    Finding:                               # a value object (pydantic model)
        id: str                            # OPAQUE — never a raw RecordID
        number: int                        # STABLE, human-addressable (#1, #2, …)
        kind: str                          # "friction" is the first first-class kind
        status: Literal[open|acknowledged|resolved|wontfix]
        subject: str
        body: str
        area: str                          # the tool/subsystem (e.g. lore_tests_for)
        category: str                      # capability_gap / affordance_gap / …
        created_by: str
        created_at: datetime               # tz-aware UTC
        supersedes: str | None             # opaque id of the finding this supersedes
        provenance: dict                   # who created/changed + timestamps

    ReportResult:
        id: str
        number: int

    FindingLedger(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async close() -> None
        async report(subject, body, *, kind="friction", area, category, created_by,
                     supersedes=None) -> ReportResult
        async get(id_or_number) -> Finding
        async query(*, status=None, kind=None, area=None, limit=…) -> list[Finding]
        async chain_head(id_or_number) -> ChainHead   # head + fork-surfacing marks
        async acknowledge(id_or_number, actor) -> Finding
        async resolve(id_or_number, actor, note=None) -> Finding
        async wontfix(id_or_number, actor, note=None) -> Finding

    Exceptions: FindingLedgerError(RuntimeError);
                FindingNotFoundError(FindingLedgerError);
                IllegalTransitionError(FindingLedgerError);
                FindingChainCycleError(FindingLedgerError).

Expected until the module lands: collection ERROR in THIS FILE —
``ModuleNotFoundError: No module named 'loremaster.findings'``.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest
import pytest_asyncio
from _finding_fakes import FakeFindingDatabase, FakeFindingLedger
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.findings import (
    ChainHead,
    Finding,
    FindingChainCycleError,
    FindingLedger,
    FindingNotFoundError,
    IllegalTransitionError,
    ReportResult,
)
from loremaster.store._txn import (
    SurrealConnectionError,
    SurrealStoreError,
    _SurrealConnection,
)
from surrealdb.errors import ErrorKind, ServerError

# --- the domain's status vocabulary (the convention this contract decides) ----
STATUS_OPEN = "open"
STATUS_ACKNOWLEDGED = "acknowledged"
STATUS_RESOLVED = "resolved"
STATUS_WONTFIX = "wontfix"

TERMINAL_STATUSES = frozenset({STATUS_RESOLVED, STATUS_WONTFIX})

KIND_FRICTION = "friction"

# --- realistic fleet identities (agent/session ids, NOT foo/bar) --------------
REPORTER = "di-scout-session-4a1c"  # the scout session that files findings
ACK_ACTOR = "team-lead-session-9f2b"
RESOLVER_A = "builder-findings-1"
RESOLVER_B = "grader-agent-c"

# --- realistic finding areas + categories (real lore tool surfaces) -----------
AREA_TESTS_FOR = "lore_tests_for"
AREA_REFERENCES = "lore_references"
AREA_SEARCH = "lore_search_code"
AREA_RECALL = "lore_recall_memory"
CATEGORY_CAPABILITY = "capability_gap"
CATEGORY_AFFORDANCE = "affordance_gap"

# Real friction findings drawn from THIS repo's own FRICTION.md — the actual
# range and shape of what the ledger will hold, never convenience placeholders.
SUBJECT_TESTS_FOR = "tests_for reports only direct edges, missing indirect coverage"
BODY_TESTS_FOR = (
    "lore_tests_for(symbol) returns direct test nodes but misses tests exercising "
    "the symbol transitively through a helper; consumers over-trust the empty result."
)
SUBJECT_REFERENCES = "bare-name resolution returns zeros indistinguishable from unreferenced"
BODY_REFERENCES = (
    "lore_references('CoverageCalibrator') = 0/0/[] vs the qualified name = 1 prod / "
    "5 test (grep-verified); an agent reads that as DEAD."
)
SUBJECT_SEARCH = "excluded data-dir docs are read_file-visible but search_code-invisible"
BODY_SEARCH = (
    "load-bearing generated docs inside an excluded dir are unreachable via "
    "search_code; an include glob cannot pierce exclude_dirs."
)
SUBJECT_RECALL = "recall offers no kind/label filter to narrow digest dumps"
BODY_RECALL = (
    "specific-fact recall missed 4/7 probes; atomic facts drown inside multi-KB "
    "session digests with no kind= / labels= filter to narrow."
)

# The concurrency pin's fan-out: enough concurrent reporters that a broken number
# mint (a duplicate or a gap) lands reliably, comfortably below the single-row
# contention ceiling the shared bounded conflict-retry can absorb.
_CONCURRENT_REPORTS = 8

# The transition-race pin's iteration count — enough that a broken compare-and-set
# (two winners, or zero) lands reliably rather than hiding behind lucky scheduling.
_RACE_ITERATIONS = 20

# A generous window for the "derived timestamp is recent" sanity bound: absorbs
# clock skew + engine round-trip rounding while still catching a wrong-epoch /
# wrong-scale / stale-clock stamp.
_TIMESTAMP_TOLERANCE = timedelta(seconds=10)


# ---------------------------------------------------------------------------
# Helpers (reused across test classes)
# ---------------------------------------------------------------------------
def _provenance_mentions(provenance: Any, actor: str) -> bool:
    """Whether ``actor`` appears as a value ANYWHERE in a (possibly nested)
    provenance structure.

    Decouples the assertion from the exact provenance KEY layout (a dict shape
    this contract deliberately leaves open) while still pinning the real semantic:
    the acting identity is recorded. Catches the "actor not recorded" and "wrong
    identity recorded" bugs without over-specifying structure.
    """
    stack: list[Any] = [provenance]
    while stack:
        current = stack.pop()
        if isinstance(current, str):
            if current == actor:
                return True
        elif isinstance(current, dict):
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, (list, tuple, set)):
            stack.extend(current)
    return False


def _assert_recent_utc(stamp: datetime, *, not_before: datetime, not_after: datetime) -> None:
    """Sanity-bound a DERIVED timestamp: tz-aware UTC and within the call window.

    Timezone-awareness is the load-bearing anti-bug guard — a naive stamp is the
    classic "wrong anchor" defect for a value agents in different timezones
    compare. The window bound catches a wrong-epoch / stale-clock stamp.
    """
    assert stamp.tzinfo is not None, "timestamp must be timezone-aware (fleet-comparable), not naive"
    assert not_before - _TIMESTAMP_TOLERANCE <= stamp <= not_after + _TIMESTAMP_TOLERANCE


async def _report(
    ledger: FindingLedger,
    subject: str = SUBJECT_TESTS_FOR,
    body: str = BODY_TESTS_FOR,
    *,
    area: str = AREA_TESTS_FOR,
    category: str = CATEGORY_CAPABILITY,
    created_by: str = REPORTER,
) -> ReportResult:
    """File a friction finding via the ledger and return the report result."""
    return await ledger.report(
        subject, body, area=area, category=category, created_by=created_by
    )


# A factory that builds one more ready ``FindingLedger`` on the SAME database —
# the second live connection the fleet-visibility and race pins need.
FindingLedgerFactory = Callable[[], Awaitable[FindingLedger]]


@pytest_asyncio.fixture(params=["real", "fake"])
async def finding_ledger_factory(
    request: pytest.FixtureRequest,
) -> AsyncIterator[FindingLedgerFactory]:
    """A factory yielding independent ready ledgers on the SAME per-test backing
    store — parametrized over BOTH the real SurrealDB-backed ``FindingLedger`` and
    the adversarial in-memory ``FakeFindingLedger`` (``_finding_fakes.py``).

    THE single construction seam (no test builds a ledger inline) — every test in
    this module routes through here, so the SAME contract suite exercises both
    backends. This is the fake-vs-real PARITY PIN: a behaviour the fake gets
    wrong, or too friendly, shows up as a real-vs-fake divergence rather than a
    fake-only green.

    The ``"real"`` branch deliberately does NOT depend on the ``surreal_env``
    pytest fixture (mirroring ``test_task_ledger.py``'s ``task_ledger_factory``):
    pytest-asyncio 1.4's function-scoped ``Runner`` is SHARED by every async
    fixture a test uses, and resolving one async fixture from INSIDE another
    async fixture's own body re-enters that ``Runner`` (``RuntimeError:
    Runner.run() cannot be called from a running event loop``). Calling the SAME
    underlying harness helpers directly gets the identical isolated-throwaway-
    database guarantee without touching pytest's fixture graph, and keeps every
    ``FindingLedger`` on the SAME event loop the test runs on. The ``"fake"``
    branch builds ONE shared ``FakeFindingDatabase`` per test; every ``make()``
    hands back a distinct handle over that SAME store — two independent
    "connections" to one fleet-visible table.
    """
    created: list[FindingLedger] = []

    if request.param == "real":
        env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()

        async def make() -> FindingLedger:
            ledger = FindingLedger(
                url=env.url,
                namespace=env.namespace,
                database=env.database,
                user=env.user,
                password=env.password,
            )
            await ledger.ensure_ready()
            created.append(ledger)
            return ledger
    else:
        shared_db = FakeFindingDatabase()

        async def make() -> FindingLedger:
            fake_ledger = FakeFindingLedger(db=shared_db)
            await fake_ledger.ensure_ready()
            # A FakeFindingLedger satisfies the FindingLedger contract
            # behaviourally (that IS this parity pin); it shares no base class with
            # the real one, so the cast tells mypy what the suite proves.
            typed_ledger = cast(FindingLedger, fake_ledger)
            created.append(typed_ledger)
            return typed_ledger

    try:
        yield make
    finally:
        for ledger in created:
            await ledger.close()
        if request.param == "real":
            await drop_database(env)


@pytest_asyncio.fixture()
async def finding_ledger(finding_ledger_factory: FindingLedgerFactory) -> FindingLedger:
    """A single ready ledger on a fresh unique database (the common per-test case)."""
    return await finding_ledger_factory()


class TestReportAndGet:
    """File → get round-trip: default open state, an opaque id + a stable number,
    the reporter recorded in provenance, and addressing by BOTH number and id.
    """

    async def test_report_returns_id_and_number(self, finding_ledger: FindingLedger) -> None:
        result = await _report(finding_ledger)
        assert isinstance(result, ReportResult)
        assert isinstance(result.id, str) and result.id
        assert isinstance(result.number, int)

    async def test_first_finding_number_is_one(self, finding_ledger: FindingLedger) -> None:
        # On a fresh ledger the first minted number is 1 (human-addressable #1).
        result = await _report(finding_ledger)
        assert result.number == 1

    async def test_reported_finding_starts_open(self, finding_ledger: FindingLedger) -> None:
        result = await _report(finding_ledger)
        finding = await finding_ledger.get(result.id)
        assert isinstance(finding, Finding)
        assert finding.id == result.id
        assert finding.number == result.number
        assert finding.status == STATUS_OPEN
        assert finding.supersedes is None

    async def test_report_round_trips_all_content_fields(
        self, finding_ledger: FindingLedger
    ) -> None:
        result = await finding_ledger.report(
            SUBJECT_REFERENCES,
            BODY_REFERENCES,
            kind=KIND_FRICTION,
            area=AREA_REFERENCES,
            category=CATEGORY_AFFORDANCE,
            created_by=REPORTER,
        )
        finding = await finding_ledger.get(result.id)
        assert finding.subject == SUBJECT_REFERENCES
        assert finding.body == BODY_REFERENCES
        assert finding.kind == KIND_FRICTION
        assert finding.area == AREA_REFERENCES
        assert finding.category == CATEGORY_AFFORDANCE

    async def test_kind_defaults_to_friction(self, finding_ledger: FindingLedger) -> None:
        # friction is the first first-class kind — the default when unspecified.
        result = await _report(finding_ledger)
        assert (await finding_ledger.get(result.id)).kind == KIND_FRICTION

    async def test_created_at_is_timezone_aware_and_recent(
        self, finding_ledger: FindingLedger
    ) -> None:
        before = datetime.now(UTC)
        result = await _report(finding_ledger)
        after = datetime.now(UTC)
        finding = await finding_ledger.get(result.id)
        assert isinstance(finding.created_at, datetime)
        _assert_recent_utc(finding.created_at, not_before=before, not_after=after)

    async def test_provenance_records_the_reporter(self, finding_ledger: FindingLedger) -> None:
        result = await _report(finding_ledger)
        finding = await finding_ledger.get(result.id)
        assert isinstance(finding.provenance, dict)
        assert _provenance_mentions(finding.provenance, REPORTER)

    async def test_get_by_number_and_by_id_agree(self, finding_ledger: FindingLedger) -> None:
        # THE dual-addressing seam: the SAME finding is reachable by its stable
        # number and by its opaque id.
        result = await _report(finding_ledger)
        by_id = await finding_ledger.get(result.id)
        by_number = await finding_ledger.get(result.number)
        assert by_id.id == by_number.id == result.id
        assert by_id.number == by_number.number == result.number

    async def test_get_unknown_id_raises_not_found(self, finding_ledger: FindingLedger) -> None:
        await _report(finding_ledger)
        with pytest.raises(FindingNotFoundError):
            await finding_ledger.get("deadbeefdeadbeefdeadbeefdeadbeef")

    async def test_get_unknown_number_raises_not_found(
        self, finding_ledger: FindingLedger
    ) -> None:
        await _report(finding_ledger)
        with pytest.raises(FindingNotFoundError):
            await finding_ledger.get(9999)

    async def test_returned_finding_is_a_defensive_copy(
        self, finding_ledger: FindingLedger
    ) -> None:
        # A caller mutating a returned Finding's provenance must NOT corrupt the
        # store (production deserializes a fresh row every call).
        result = await _report(finding_ledger)
        first = await finding_ledger.get(result.id)
        first.provenance.setdefault("events", []).append({"actor": "attacker"})
        second = await finding_ledger.get(result.id)
        assert not _provenance_mentions(second.provenance, "attacker")


class TestReportRejectsEmptyAreaCategory:
    """P8b hardening (audit-findings #2): ``report`` refuses an empty/whitespace-only
    ``area`` or ``category`` with a typed ``ValueError`` BEFORE the store round-trip,
    so a caller gets a clean, early domain error (mirroring ``query``'s ``limit``
    guard) rather than a laundered store ``ASSERT`` rejection. Parity-pinned: the
    schema ASSERT is the store-side backstop, this is the ledger-side guard, and
    BOTH backends enforce it identically.
    """

    @pytest.mark.parametrize("empty_area", ["", " ", "\t"])
    async def test_report_rejects_empty_or_whitespace_area(
        self, finding_ledger: FindingLedger, empty_area: str
    ) -> None:
        with pytest.raises(ValueError):
            await finding_ledger.report(
                SUBJECT_TESTS_FOR,
                BODY_TESTS_FOR,
                area=empty_area,
                category=CATEGORY_CAPABILITY,
                created_by=REPORTER,
            )

    @pytest.mark.parametrize("empty_category", ["", " ", "\t"])
    async def test_report_rejects_empty_or_whitespace_category(
        self, finding_ledger: FindingLedger, empty_category: str
    ) -> None:
        with pytest.raises(ValueError):
            await finding_ledger.report(
                SUBJECT_TESTS_FOR,
                BODY_TESTS_FOR,
                area=AREA_TESTS_FOR,
                category=empty_category,
                created_by=REPORTER,
            )

    async def test_rejected_report_mints_no_number(
        self, finding_ledger: FindingLedger
    ) -> None:
        # The early guard fails BEFORE the counter bump — a refused report consumes
        # no number, so the next good report is still #1 (gapless).
        with pytest.raises(ValueError):
            await finding_ledger.report(
                SUBJECT_TESTS_FOR, BODY_TESTS_FOR,
                area="", category=CATEGORY_CAPABILITY, created_by=REPORTER,
            )
        good = await _report(finding_ledger)
        assert good.number == 1


class TestStableNumbering:
    """Numbers are minted consecutively and are STABLE addresses — the
    enumerate-in-order and address-by-number affordances the di-scout entry pins.
    """

    async def test_sequential_reports_get_consecutive_numbers(
        self, finding_ledger: FindingLedger
    ) -> None:
        numbers = [
            (await _report(finding_ledger, f"{SUBJECT_TESTS_FOR} #{i}")).number for i in range(5)
        ]
        assert numbers == [1, 2, 3, 4, 5]

    async def test_number_is_a_stable_address_across_calls(
        self, finding_ledger: FindingLedger
    ) -> None:
        first = await _report(finding_ledger, SUBJECT_TESTS_FOR)
        second = await _report(finding_ledger, SUBJECT_REFERENCES, area=AREA_REFERENCES)
        # Addressing #1 always returns the first finding, #2 always the second —
        # the number is a durable handle, never reused or reshuffled.
        assert (await finding_ledger.get(first.number)).subject == SUBJECT_TESTS_FOR
        assert (await finding_ledger.get(second.number)).subject == SUBJECT_REFERENCES


class TestConcurrentNumbering:
    """THE race-safe-mint pin: N reporters filing at once yield N DISTINCT,
    CONSECUTIVE numbers with ZERO failures — the stable-number invariant the whole
    "address a record by a number" affordance rests on.

    Separate live connections (not coroutines on one socket) is the
    production-realistic fleet scenario and the only configuration that exercises
    the server-side counter's compare-and-set + optimistic-concurrency retry.
    """

    async def test_concurrent_reports_get_distinct_consecutive_numbers(
        self, finding_ledger_factory: FindingLedgerFactory
    ) -> None:
        reporters = [await finding_ledger_factory() for _ in range(_CONCURRENT_REPORTS)]
        results = await asyncio.gather(
            *(
                reporter.report(
                    f"{SUBJECT_TESTS_FOR} (racer {i})",
                    BODY_TESTS_FOR,
                    area=AREA_TESTS_FOR,
                    category=CATEGORY_CAPABILITY,
                    created_by=f"{REPORTER}-{i}",
                )
                for i, reporter in enumerate(reporters)
            )
        )
        numbers = sorted(result.number for result in results)
        # DISTINCT and CONSECUTIVE — never a duplicate (broken mint), never a gap.
        assert numbers == list(range(1, _CONCURRENT_REPORTS + 1)), (
            f"expected {list(range(1, _CONCURRENT_REPORTS + 1))} distinct consecutive "
            f"numbers, got {numbers}"
        )
        # Every id is distinct too — no two reporters collided on a finding.
        assert len({result.id for result in results}) == _CONCURRENT_REPORTS


class TestQuery:
    """The ordered browse: ``query`` returns findings ordered by number ASC,
    filters exactly on status/kind/area, and honours ``limit``.
    """

    async def test_query_is_ordered_by_number_ascending(
        self, finding_ledger: FindingLedger
    ) -> None:
        for i in range(6):
            await _report(finding_ledger, f"{SUBJECT_TESTS_FOR} #{i}")
        rows = await finding_ledger.query()
        numbers = [finding.number for finding in rows]
        assert numbers == sorted(numbers)
        assert numbers == [1, 2, 3, 4, 5, 6]

    async def test_status_filter_is_exact(self, finding_ledger: FindingLedger) -> None:
        open_one = await _report(finding_ledger, SUBJECT_TESTS_FOR)
        to_ack = await _report(finding_ledger, SUBJECT_REFERENCES, area=AREA_REFERENCES)
        to_resolve = await _report(finding_ledger, SUBJECT_SEARCH, area=AREA_SEARCH)
        await finding_ledger.acknowledge(to_ack.number, ACK_ACTOR)
        await finding_ledger.resolve(to_resolve.number, RESOLVER_A)

        open_ids = {finding.id for finding in await finding_ledger.query(status=STATUS_OPEN)}
        assert open_ids == {open_one.id}
        ack_ids = {
            finding.id for finding in await finding_ledger.query(status=STATUS_ACKNOWLEDGED)
        }
        assert ack_ids == {to_ack.id}

    async def test_kind_and_area_filters_are_exact(self, finding_ledger: FindingLedger) -> None:
        tests_for = await _report(finding_ledger, SUBJECT_TESTS_FOR, area=AREA_TESTS_FOR)
        await _report(finding_ledger, SUBJECT_REFERENCES, area=AREA_REFERENCES)
        by_area = {finding.id for finding in await finding_ledger.query(area=AREA_TESTS_FOR)}
        assert by_area == {tests_for.id}
        by_kind = {finding.id for finding in await finding_ledger.query(kind=KIND_FRICTION)}
        assert len(by_kind) == 2  # both are friction

    async def test_limit_caps_the_result_in_number_order(
        self, finding_ledger: FindingLedger
    ) -> None:
        for i in range(5):
            await _report(finding_ledger, f"{SUBJECT_TESTS_FOR} #{i}")
        rows = await finding_ledger.query(limit=3)
        # The FIRST three by number (the ordered-browse head), not an arbitrary 3.
        assert [finding.number for finding in rows] == [1, 2, 3]

    async def test_filter_matching_nothing_is_honest_empty_list(
        self, finding_ledger: FindingLedger
    ) -> None:
        await _report(finding_ledger)  # open friction
        assert await finding_ledger.query(status=STATUS_RESOLVED) == []
        assert await finding_ledger.query(area="lore_nonexistent_tool") == []


class TestSupersedes:
    """The supersedes link + ``chain_head``: a new finding may reframe an older one
    by linking back to it; following the chain FORWARD reaches the newest record.
    """

    async def test_report_with_supersedes_records_the_link(
        self, finding_ledger: FindingLedger
    ) -> None:
        original = await _report(finding_ledger, SUBJECT_TESTS_FOR)
        successor = await finding_ledger.report(
            f"{SUBJECT_TESTS_FOR} (sharper restatement)",
            BODY_TESTS_FOR,
            area=AREA_TESTS_FOR,
            category=CATEGORY_CAPABILITY,
            created_by=REPORTER,
            supersedes=original.number,
        )
        linked = await finding_ledger.get(successor.id)
        # The link is stored as the OPAQUE id of the superseded finding.
        assert linked.supersedes == original.id

    async def test_supersedes_unknown_target_raises_not_found(
        self, finding_ledger: FindingLedger
    ) -> None:
        with pytest.raises(FindingNotFoundError):
            await finding_ledger.report(
                SUBJECT_TESTS_FOR,
                BODY_TESTS_FOR,
                area=AREA_TESTS_FOR,
                category=CATEGORY_CAPABILITY,
                created_by=REPORTER,
                supersedes=9999,
            )

    async def test_chain_head_of_a_lone_finding_is_itself(
        self, finding_ledger: FindingLedger
    ) -> None:
        # A finding nobody supersedes is its own head.
        original = await _report(finding_ledger, SUBJECT_TESTS_FOR)
        head = await finding_ledger.chain_head(original.number)
        assert head.finding.id == original.id

    async def test_chain_head_follows_supersedes_forward_to_newest(
        self, finding_ledger: FindingLedger
    ) -> None:
        first = await _report(finding_ledger, SUBJECT_TESTS_FOR)
        second = await finding_ledger.report(
            "restatement v2", BODY_TESTS_FOR, area=AREA_TESTS_FOR,
            category=CATEGORY_CAPABILITY, created_by=REPORTER, supersedes=first.number,
        )
        third = await finding_ledger.report(
            "restatement v3", BODY_TESTS_FOR, area=AREA_TESTS_FOR,
            category=CATEGORY_CAPABILITY, created_by=REPORTER, supersedes=second.number,
        )
        # From ANY point in the chain, the head is the newest (third).
        assert (await finding_ledger.chain_head(first.number)).finding.id == third.id
        assert (await finding_ledger.chain_head(second.id)).finding.id == third.id
        assert (await finding_ledger.chain_head(third.number)).finding.id == third.id

    async def test_chain_head_unknown_raises_not_found(
        self, finding_ledger: FindingLedger
    ) -> None:
        await _report(finding_ledger)
        with pytest.raises(FindingNotFoundError):
            await finding_ledger.chain_head(9999)


class TestChainHeadFork:
    """P8b hardening (audit-findings #1): two findings may each ``supersedes`` the
    SAME original — a FORK reachable through the public API. ``chain_head`` still
    walks the deterministic lowest-numbered branch, but its result SURFACES the
    fork (``forked`` + the unwalked sibling numbers) instead of silently dropping
    the higher-numbered arm and billing the lowest branch's head as "the newest".
    """

    async def _fork(
        self, ledger: FindingLedger
    ) -> tuple[ReportResult, ReportResult, ReportResult]:
        """Build a fork: X, then Y and Z both superseding X (Y minted before Z, so
        ``y.number < z.number`` — the deterministic walk follows Y)."""
        original = await _report(ledger, "original X")
        low = await ledger.report(
            "successor Y (low)", BODY_TESTS_FOR, area=AREA_TESTS_FOR,
            category=CATEGORY_CAPABILITY, created_by=REPORTER, supersedes=original.number,
        )
        high = await ledger.report(
            "successor Z (high)", BODY_TESTS_FOR, area=AREA_TESTS_FOR,
            category=CATEGORY_CAPABILITY, created_by=REPORTER, supersedes=original.number,
        )
        return original, low, high

    async def test_chain_head_returns_a_fork_aware_result(
        self, finding_ledger: FindingLedger
    ) -> None:
        original = await _report(finding_ledger, SUBJECT_TESTS_FOR)
        head = await finding_ledger.chain_head(original.number)
        # Even the lone/linear case returns the fork-aware value object, not a bare
        # Finding — a caller always gets the same shape.
        assert isinstance(head, ChainHead)
        assert isinstance(head.finding, Finding)
        assert head.finding.id == original.id
        assert head.forked is False
        assert head.fork_successor_numbers == []

    async def test_linear_chain_head_is_not_forked(
        self, finding_ledger: FindingLedger
    ) -> None:
        first = await _report(finding_ledger, SUBJECT_TESTS_FOR)
        second = await finding_ledger.report(
            "restatement v2", BODY_TESTS_FOR, area=AREA_TESTS_FOR,
            category=CATEGORY_CAPABILITY, created_by=REPORTER, supersedes=first.number,
        )
        third = await finding_ledger.report(
            "restatement v3", BODY_TESTS_FOR, area=AREA_TESTS_FOR,
            category=CATEGORY_CAPABILITY, created_by=REPORTER, supersedes=second.number,
        )
        head = await finding_ledger.chain_head(first.number)
        assert head.finding.id == third.id
        assert head.forked is False
        assert head.fork_successor_numbers == []

    async def test_forked_chain_head_walks_lowest_branch_deterministically(
        self, finding_ledger: FindingLedger
    ) -> None:
        _original, low, _high = await self._fork(finding_ledger)
        head = await finding_ledger.chain_head(_original.number)
        # The walk deterministically follows the LOWEST-numbered successor (Y).
        assert head.finding.id == low.id

    async def test_forked_chain_head_surfaces_the_other_branch(
        self, finding_ledger: FindingLedger
    ) -> None:
        original, _low, high = await self._fork(finding_ledger)
        head = await finding_ledger.chain_head(original.number)
        # The fork is SURFACED, not silently dropped: forked=True and the newer
        # (higher-numbered) arm's number is named so a consumer can walk it.
        assert head.forked is True
        assert high.number in head.fork_successor_numbers

    async def test_fork_surfacing_is_addressable_from_any_entry_point(
        self, finding_ledger: FindingLedger
    ) -> None:
        # Entering the walk at the shared original OR any point before the fork
        # surfaces the same sibling branch.
        original, low, high = await self._fork(finding_ledger)
        head = await finding_ledger.chain_head(original.id)  # by opaque id too
        assert head.forked is True
        assert head.finding.id == low.id
        # The surfaced sibling can itself be walked to its (own) head.
        sibling_head = await finding_ledger.chain_head(high.number)
        assert sibling_head.finding.id == high.id
        assert sibling_head.forked is False


# The full legal transition matrix (the brief's finding state machine, verbatim).
LEGAL_TRANSITIONS = [
    (STATUS_OPEN, STATUS_ACKNOWLEDGED),
    (STATUS_OPEN, STATUS_RESOLVED),
    (STATUS_OPEN, STATUS_WONTFIX),
    (STATUS_ACKNOWLEDGED, STATUS_RESOLVED),
    (STATUS_ACKNOWLEDGED, STATUS_WONTFIX),
]

# Representative ILLEGAL transitions REACHABLE by a public verb (a verb targets
# only acknowledged/resolved/wontfix — re-entering ``open`` has no verb at all, so
# a finding is never re-opened BY CONSTRUCTION, a stronger guarantee than a runtime
# refusal; see ``test_open_is_not_reachable_by_any_verb``). This samples the
# terminal-has-no-exit edges, the no-op self-edges, and the can't-re-acknowledge edge.
ILLEGAL_TRANSITIONS = [
    (STATUS_ACKNOWLEDGED, STATUS_ACKNOWLEDGED),  # no-op self-edge
    (STATUS_RESOLVED, STATUS_ACKNOWLEDGED),      # resolved is TERMINAL
    (STATUS_WONTFIX, STATUS_ACKNOWLEDGED),       # wontfix is TERMINAL
    (STATUS_RESOLVED, STATUS_RESOLVED),          # no-op self-edge
    (STATUS_WONTFIX, STATUS_RESOLVED),           # wontfix is TERMINAL
    (STATUS_WONTFIX, STATUS_WONTFIX),            # no-op self-edge
    (STATUS_RESOLVED, STATUS_WONTFIX),           # resolved is TERMINAL
]


async def _drive_to_status(ledger: FindingLedger, target: str) -> ReportResult:
    """Report a fresh finding and drive it to ``target`` via known-legal edges."""
    result = await _report(ledger, f"{SUBJECT_TESTS_FOR} -> {target}")
    if target == STATUS_OPEN:
        return result
    if target == STATUS_ACKNOWLEDGED:
        await ledger.acknowledge(result.number, ACK_ACTOR)
        return result
    if target == STATUS_RESOLVED:
        await ledger.resolve(result.number, RESOLVER_A)
        return result
    if target == STATUS_WONTFIX:
        await ledger.wontfix(result.number, RESOLVER_A)
        return result
    raise ValueError(f"unsupported target status {target!r}")


# A transition verb per target, for driving an EXISTING finding across a
# parametrized (from, to) edge without knowing which verb reaches which status.
# There is DELIBERATELY no entry for ``open``: no public verb re-enters open (a
# finding is never re-opened), so every parametrized target here is one of the
# three review verbs.
_TRANSITION_VERB: dict[str, Callable[[FindingLedger, int | str, str], Awaitable[Finding]]] = {
    STATUS_ACKNOWLEDGED: lambda ledger, target, actor: ledger.acknowledge(target, actor),
    STATUS_RESOLVED: lambda ledger, target, actor: ledger.resolve(target, actor),
    STATUS_WONTFIX: lambda ledger, target, actor: ledger.wontfix(target, actor),
}


class TestTransitions:
    """The review state machine: acknowledge/resolve/wontfix follow only the
    declared edges; illegal ones raise a typed error naming both states and leave
    the row untouched; every legal transition stamps provenance; terminal states
    have no exits; and a resolve/wontfix note is recorded.
    """

    @pytest.mark.parametrize(("from_status", "to_status"), LEGAL_TRANSITIONS)
    async def test_legal_transition_moves_to_target(
        self, finding_ledger: FindingLedger, from_status: str, to_status: str
    ) -> None:
        result = await _drive_to_status(finding_ledger, from_status)
        updated = await _TRANSITION_VERB[to_status](finding_ledger, result.number, RESOLVER_A)
        assert updated.status == to_status
        assert (await finding_ledger.get(result.number)).status == to_status

    async def test_acknowledge_moves_open_to_acknowledged(
        self, finding_ledger: FindingLedger
    ) -> None:
        result = await _report(finding_ledger)
        updated = await finding_ledger.acknowledge(result.number, ACK_ACTOR)
        assert updated.status == STATUS_ACKNOWLEDGED

    async def test_transition_stamps_the_actor_in_provenance(
        self, finding_ledger: FindingLedger
    ) -> None:
        result = await _report(finding_ledger)
        await finding_ledger.acknowledge(result.number, ACK_ACTOR)
        persisted = await finding_ledger.get(result.number)
        assert _provenance_mentions(persisted.provenance, ACK_ACTOR)

    async def test_resolve_records_the_note_in_provenance(
        self, finding_ledger: FindingLedger
    ) -> None:
        result = await _report(finding_ledger)
        note = "fixed by the answers_to bridge in 9171021"
        await finding_ledger.resolve(result.number, RESOLVER_A, note=note)
        persisted = await finding_ledger.get(result.number)
        assert _provenance_mentions(persisted.provenance, note)

    @pytest.mark.parametrize(("from_status", "to_status"), ILLEGAL_TRANSITIONS)
    async def test_illegal_transition_raises_and_leaves_row_untouched(
        self, finding_ledger: FindingLedger, from_status: str, to_status: str
    ) -> None:
        result = await _drive_to_status(finding_ledger, from_status)
        before = await finding_ledger.get(result.number)

        with pytest.raises(IllegalTransitionError) as exc_info:
            await _TRANSITION_VERB[to_status](finding_ledger, result.number, RESOLVER_B)
        message = str(exc_info.value)
        # The error names BOTH states so a caller/operator sees what was refused.
        assert from_status in message
        assert to_status in message

        after = await finding_ledger.get(result.number)
        assert after.status == before.status

    async def test_resolved_is_terminal(self, finding_ledger: FindingLedger) -> None:
        result = await _drive_to_status(finding_ledger, STATUS_RESOLVED)
        with pytest.raises(IllegalTransitionError):
            await finding_ledger.wontfix(result.number, RESOLVER_B)
        assert (await finding_ledger.get(result.number)).status == STATUS_RESOLVED

    async def test_open_is_not_reachable_by_any_verb(self, finding_ledger: FindingLedger) -> None:
        # A finding is never re-opened: the public surface offers ONLY
        # acknowledge/resolve/wontfix (targeting acknowledged/resolved/wontfix), so
        # re-entering ``open`` is impossible BY CONSTRUCTION — a stronger guarantee
        # than a runtime refusal. No ``reopen``/``open`` verb exists to attempt it.
        result = await _report(finding_ledger)
        await finding_ledger.acknowledge(result.number, ACK_ACTOR)
        await finding_ledger.resolve(result.number, RESOLVER_A)
        assert (await finding_ledger.get(result.number)).status == STATUS_RESOLVED
        assert not hasattr(finding_ledger, "reopen")
        assert not hasattr(finding_ledger, "open")

    async def test_transition_by_id_and_by_number_both_work(
        self, finding_ledger: FindingLedger
    ) -> None:
        by_number = await _report(finding_ledger, SUBJECT_TESTS_FOR)
        by_id = await _report(finding_ledger, SUBJECT_REFERENCES, area=AREA_REFERENCES)
        await finding_ledger.acknowledge(by_number.number, ACK_ACTOR)  # address by number
        await finding_ledger.acknowledge(by_id.id, ACK_ACTOR)          # address by id
        assert (await finding_ledger.get(by_number.number)).status == STATUS_ACKNOWLEDGED
        assert (await finding_ledger.get(by_id.id)).status == STATUS_ACKNOWLEDGED

    async def test_transition_unknown_raises_not_found(
        self, finding_ledger: FindingLedger
    ) -> None:
        await _report(finding_ledger)
        with pytest.raises(FindingNotFoundError):
            await finding_ledger.acknowledge(9999, ACK_ACTOR)


class TestConcurrentTransitions:
    """The state machine holds under CONCURRENCY: two agents racing the SAME open
    finding toward two DIFFERENT terminal states (one resolve, one wontfix) must
    NOT both land. Exactly ONE wins; the loser raises
    :class:`IllegalTransitionError` (its edge is illegal against the winner's
    already-terminal status); a fresh read shows the winner's terminal status; and
    the winner's provenance event survives.
    """

    async def test_concurrent_terminal_transitions_have_exactly_one_winner(
        self, finding_ledger_factory: FindingLedgerFactory
    ) -> None:
        ledger_a = await finding_ledger_factory()
        ledger_b = await finding_ledger_factory()

        for iteration in range(_RACE_ITERATIONS):
            result = await _report(ledger_a, f"{SUBJECT_TESTS_FOR} #{iteration}")

            outcomes = await asyncio.gather(
                ledger_a.resolve(result.number, RESOLVER_A),
                ledger_b.wontfix(result.number, RESOLVER_B),
                return_exceptions=True,
            )
            winners = [o for o in outcomes if isinstance(o, Finding)]
            losers = [o for o in outcomes if isinstance(o, IllegalTransitionError)]
            other = [
                o
                for o in outcomes
                if isinstance(o, BaseException) and not isinstance(o, IllegalTransitionError)
            ]

            assert not other, f"iteration {iteration}: unexpected exception(s): {other!r}"
            assert len(winners) == 1, (
                f"iteration {iteration}: expected exactly one winner, got "
                f"{len(winners)} — outcomes={outcomes!r}"
            )
            assert len(losers) == 1, (
                f"iteration {iteration}: expected exactly one typed loser, got "
                f"{len(losers)} — outcomes={outcomes!r}"
            )

            winner_status = winners[0].status
            winner_actor = RESOLVER_A if winner_status == STATUS_RESOLVED else RESOLVER_B

            persisted = await ledger_a.get(result.number)
            assert persisted.status in TERMINAL_STATUSES
            assert persisted.status == winner_status
            # The winner's event survived — the loser's refused write did not
            # clobber the provenance object.
            assert _provenance_mentions(persisted.provenance, winner_actor)
            # The terminal status is stable — a second read never differs.
            assert (await ledger_a.get(result.number)).status == persisted.status


class TestFleetVisibility:
    """Durability across sessions: a SECOND ledger over the SAME database sees the
    FIRST's findings, numbers, and transitions — SurrealDB's volume is the durable
    spine. This is the whole point of a "fleet-visible" table.
    """

    async def test_second_ledger_reads_first_ledgers_finding(
        self, finding_ledger_factory: FindingLedgerFactory
    ) -> None:
        writer = await finding_ledger_factory()
        result = await _report(writer, SUBJECT_TESTS_FOR)

        reader = await finding_ledger_factory()
        seen = await reader.get(result.number)
        assert seen.id == result.id
        assert seen.subject == SUBJECT_TESTS_FOR

    async def test_second_ledger_query_includes_first_ledgers_finding(
        self, finding_ledger_factory: FindingLedgerFactory
    ) -> None:
        writer = await finding_ledger_factory()
        result = await _report(writer, SUBJECT_REFERENCES, area=AREA_REFERENCES)

        reader = await finding_ledger_factory()
        open_numbers = {finding.number for finding in await reader.query(status=STATUS_OPEN)}
        assert result.number in open_numbers

    async def test_second_ledger_sees_a_transition_made_by_the_first(
        self, finding_ledger_factory: FindingLedgerFactory
    ) -> None:
        writer = await finding_ledger_factory()
        result = await _report(writer, SUBJECT_TESTS_FOR)
        await writer.acknowledge(result.number, ACK_ACTOR)

        reader = await finding_ledger_factory()
        seen = await reader.get(result.number)
        assert seen.status == STATUS_ACKNOWLEDGED  # durable + cross-session visible


class TestChainCycleTermination:
    """A corrupt supersedes CYCLE terminates ``chain_head`` with a typed error,
    never a hang. A cycle is unreachable via the public API (``supersedes`` is set
    once at report and never mutated), so each backend injects the corruption
    directly through its OWN store, then asserts the walk raises.
    """

    async def test_real_chain_cycle_raises_typed_error(self) -> None:
        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()
        ledger = FindingLedger(
            url=env.url, namespace=env.namespace, database=env.database,
            user=env.user, password=env.password,
        )
        await ledger.ensure_ready()
        try:
            first = await _report(ledger, SUBJECT_TESTS_FOR)
            second = await ledger.report(
                "restatement", BODY_TESTS_FOR, area=AREA_TESTS_FOR,
                category=CATEGORY_CAPABILITY, created_by=REPORTER, supersedes=first.number,
            )
            # Corrupt: make first supersede second too, closing the loop
            # first -> second -> first. (Never reachable via the public API.)
            admin = await connect_admin(env)
            try:
                await run(
                    admin,
                    "UPDATE type::record('finding', $id) SET "
                    "supersedes = type::record('finding', $target)",
                    {"id": first.id, "target": second.id},
                )
            finally:
                await admin.close()
            with pytest.raises(FindingChainCycleError):
                await ledger.chain_head(first.number)
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_fake_chain_cycle_raises_typed_error(self) -> None:
        db = FakeFindingDatabase()
        ledger = FakeFindingLedger(db=db)
        first = await _report(cast(FindingLedger, ledger), SUBJECT_TESTS_FOR)
        second = await ledger.report(
            "restatement", BODY_TESTS_FOR, area=AREA_TESTS_FOR,
            category=CATEGORY_CAPABILITY, created_by=REPORTER, supersedes=first.number,
        )
        # Inject the same corruption straight into the fake's store.
        db.findings[first.id].supersedes = second.id
        with pytest.raises(FindingChainCycleError):
            await ledger.chain_head(first.number)


# ===========================================================================
# The SINGLE-statement ``_query`` seam's classified-error posture (ledger #31).
#
# ``FindingLedger._query`` splits a caught error into transport (self-heal +
# ``SurrealConnectionError``) vs domain (keep the connection + ``SurrealStoreError``),
# mirroring ``TaskLedger._query``. A domain ``ASSERT``/coercion rejection's engine
# text can echo a bound VALUE back verbatim, and that text flows to MCP clients in
# P8; the raised message must launder it. These pins fix the seam at BOTH branches,
# deterministically and without a live server: a fake connection raises a scripted
# ``ServerError`` (domain- or transport-``kind``).
# ===========================================================================

_FINDING_SENSITIVE_MARKER = "TOP-SECRET-FINDING-BOUND-VALUE-3b8e2d"
_FINDING_SENSITIVE_ENGINE_TEXT = (
    f"Found '{_FINDING_SENSITIVE_MARKER}' for field `status`, with record "
    f"`finding:abc123`, but expected the value to fulfil the following "
    f"assertion: $value INSIDE ['open', 'acknowledged', 'resolved', 'wontfix']"
)
_FINDING_TRANSPORT_ENGINE_TEXT = "Anonymous access to the finding query is not allowed"


@dataclass
class _RejectingConnection:
    """A fake SDK connection whose ``query`` raises a scripted error — the seam
    fault-injector for ``_query``'s classified-error posture. ``close`` is a
    tolerant no-op so a ledger holding this handle still tears down cleanly.
    """

    error: BaseException

    async def query(self, statement: str, params: dict[str, Any]) -> Any:
        raise self.error

    async def close(self) -> None:
        return None


class TestQueryClassifiedErrorPosture:
    """The single-statement ``_query`` seam classifies like ``execute_transaction``
    (ledger #31): a DOMAIN rejection keeps the healthy connection and raises a
    ``SurrealStoreError`` naming a generic engine CLASS + a server-log hint, NEVER
    the raw engine text; a TRANSPORT fault self-heals (drops the handle) and raises
    ``SurrealConnectionError``. Real-only seam test — built inline with an injected
    fake connection (the fake ledger exposes no ``_query`` seam to fault-inject).
    """

    @staticmethod
    def _ledger_rejecting_with(error: BaseException) -> FindingLedger:
        ledger = FindingLedger(
            url="ws://127.0.0.1:19555/rpc",  # never dialed — the fake handle short-circuits
            namespace="ns",
            database="db",
            user="root",
            password="root",
        )
        ledger._connection = cast("_SurrealConnection", _RejectingConnection(error=error))
        return ledger

    async def test_domain_rejection_message_never_echoes_the_raw_engine_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger = self._ledger_rejecting_with(
            ServerError(ErrorKind.INTERNAL, _FINDING_SENSITIVE_ENGINE_TEXT)
        )
        connection_before = ledger._connection
        with caplog.at_level(logging.ERROR, logger="loremaster.findings"):
            with pytest.raises(SurrealStoreError) as exc_info:
                await ledger._query("UPDATE finding SET status = $s", {"s": "poison"})

        message = str(exc_info.value)
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert ledger._connection is connection_before  # healthy connection kept
        assert _FINDING_SENSITIVE_ENGINE_TEXT not in message
        assert _FINDING_SENSITIVE_MARKER not in message
        assert "assert violation" in message.lower()
        assert "server log" in message.lower()
        error_records = [record for record in caplog.records if record.levelno == logging.ERROR]
        assert error_records, "the full engine detail must be logged server-side"
        logged = " ".join(
            str(value)
            for value in (
                error_records[0].getMessage(),
                getattr(error_records[0], "engine_error", ""),
            )
        )
        assert _FINDING_SENSITIVE_MARKER in logged

    async def test_transport_failure_drops_the_handle_and_raises_connection_error(self) -> None:
        ledger = self._ledger_rejecting_with(
            ServerError(ErrorKind.NOT_ALLOWED, _FINDING_TRANSPORT_ENGINE_TEXT)
        )
        with pytest.raises(SurrealConnectionError):
            await ledger._query("SELECT * FROM finding", {})
        assert ledger._connection is None  # the dead handle was dropped (self-heal)
