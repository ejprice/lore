"""Contract tests for ``loremaster.briefs`` — the durable, versioned BRIEF
LEDGER (PKT-28 C1 seam S2), against the REAL SurrealDB server (parametrized
against an ADVERSARIAL in-memory fake too — see ``_comms_fakes.py``).

Binding spec: ``docs/design/2026-07-12-pkt28-c1-semantics.md`` §0, §5, §7-§8
(brief/briefed schema, publish/head/coverage/skew semantics, brief_get/
brief_ack legality, the error taxonomy). Where this file's contract decisions
are genuinely open in the spec, they are recorded in
``REPORT-c1-contract-ledgers.md`` — the spec is executed verbatim everywhere
it speaks; this docstring does not re-transcribe it.

The pinned contract (the public surface THIS FILE decides — the module does
not exist yet, so these names ARE the contract a later STUB/GREEN phase must
match):

    Brief:                                  # a value object (pydantic model)
        id: str                             # opaque hex — uuid5(name:version)
        name: str
        version: int
        body: str                           # RAW, never sanitised in storage
        created_by: str
        note: str | None
        created_at: datetime                # tz-aware UTC

    BriefPublishResult:
        brief: Brief
        first_version: bool

    BriefAckResult:
        name: str
        version: int                        # the version the caller targeted
        head_version: int                   # head AT THE TIME of this ack
        already_acked: bool                 # True on an idempotent re-ack no-op
        via: Literal["register", "explicit"]

    BriefBehindEntry:
        agent_name: str
        acked_version: int | None           # None = unbriefed

    BriefCoverage:
        name: str
        head_version: int
        total_agents: int
        current_count: int                  # agents AT head
        behind: list[BriefBehindEntry]      # NOT capped here — capping is a render (S3) concern

    AgentRefLike(Protocol):                 # the roster item coverage() accepts
        id: str
        name: str

    BriefLedger(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async close() -> None
        async publish(name, body, *, created_by, note=None) -> BriefPublishResult
        async get_head(name) -> Brief
        async get_version(name, version) -> Brief
        async known_names() -> list[str]
        async ack(*, agent_id, agent_name, name, version, via) -> BriefAckResult
        async acked_version(*, agent_id, name) -> int | None
        async coverage(name, *, active_agents) -> BriefCoverage

    Exceptions: BriefLedgerError(RuntimeError);
                UnknownBriefError(BriefLedgerError);
                UnknownBriefVersionError(BriefLedgerError).

    Module constants: BRIEF_NAME_PROJECT, BRIEF_NAME_BASE,
        _BRIEF_PUBLISH_MAX_ATTEMPTS, _BRIEF_PUBLISH_BACKOFF_SECONDS,
        _BRIEF_PUBLISH_JITTER_SLOTS, _BRIEF_PUBLISH_JITTER_SECONDS.

Deliberate design decoupling (see the report): ``coverage``/``ack`` accept an
externally-resolved agent identity (``agent_id``/``agent_name`` or an
``AgentRefLike`` roster) rather than querying the ``agent`` table directly —
mirrors ``TaskLedger.create_many``'s "the ledger stays key-agnostic" idiom.
The caller (S3's dispatcher, backed by ``AgentRegistry``) resolves the
roster; this ledger never imports ``loremaster.agents``.

Expected until the module lands: collection ERROR in THIS FILE —
``ModuleNotFoundError: No module named 'loremaster.briefs'``.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid5

import pytest
import pytest_asyncio
from _comms_fakes import FakeBriefDatabase, FakeBriefLedger
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.briefs import (
    _BRIEF_PUBLISH_BACKOFF_SECONDS,
    _BRIEF_PUBLISH_JITTER_SECONDS,
    _BRIEF_PUBLISH_JITTER_SLOTS,
    _BRIEF_PUBLISH_MAX_ATTEMPTS,
    _KNOWN_BRIEFS_CAP,
    BRIEF_NAME_BASE,
    BRIEF_NAME_PROJECT,
    Brief,
    BriefLedger,
    UnknownBriefError,
    UnknownBriefVersionError,
)
from loremaster.store._txn import SurrealConnectionError, SurrealStoreError, _SurrealConnection
from render_injection_scaffold import _ROW_FORGE_PAYLOAD
from surrealdb.errors import ErrorKind, ServerError

# --- realistic identities/bodies (the spec's own worked examples) -----------
PUBLISHER_LEAD = "lead"
PUBLISHER_C1_LEAD = "comms-c1-lead"
AGENT_FIXER_B_ID = "fixer-b-opaque-id"
AGENT_SCOUT_C_ID = "scout-c-opaque-id"
AGENT_AUDIT_D_ID = "audit-d-opaque-id"

BODY_V1 = "Register first, work from your spawn brief, report via lore_tasks."
BODY_V2 = "Register first; publish/ack against 'project'; report via lore_tasks; new: cite lore_impact."
WAVE_BRIEF_NAME = "wave7"

_CONCURRENT_PUBLISHERS = 8
_TIMESTAMP_TOLERANCE = timedelta(seconds=10)


def _brief_id(name: str, version: int) -> str:
    """The spec's pinned id recipe, computed independently of the ledger under
    test — a structural pin, not a shortcut that imports the ledger's own
    private helper.
    """
    return uuid5(NAMESPACE_URL, f"lore://brief/{name}/{version}").hex


def _assert_recent_utc(stamp: datetime, *, not_before: datetime, not_after: datetime) -> None:
    assert stamp.tzinfo is not None, "timestamp must be timezone-aware (fleet-comparable), not naive"
    assert not_before - _TIMESTAMP_TOLERANCE <= stamp <= not_after + _TIMESTAMP_TOLERANCE


@dataclass(frozen=True)
class _AgentRef:
    """A minimal, locally-defined stand-in satisfying ``AgentRefLike`` (``id``
    + ``name``) — deliberately NOT importing ``loremaster.agents.Agent``, so
    this test file stays collectible independently of the sibling registry
    module (see the module docstring's decoupling note).
    """

    id: str
    name: str


# A factory that builds one more ready ``BriefLedger`` on the SAME database —
# the second (and Nth) live connection the concurrency pin needs.
BriefLedgerFactory = Callable[[], Awaitable[BriefLedger]]


@pytest_asyncio.fixture(params=["real", "fake"])
async def brief_ledger_factory(request: pytest.FixtureRequest) -> AsyncIterator[BriefLedgerFactory]:
    """Clones ``task_ledger_factory``'s shape (see that fixture's docstring for
    the pytest-asyncio 1.4 ``Runner``-reentrancy rationale for NOT depending
    on ``surreal_env``).
    """
    created: list[BriefLedger] = []

    if request.param == "real":
        env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()

        async def make() -> BriefLedger:
            ledger = BriefLedger(
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
        shared_db = FakeBriefDatabase()

        async def make() -> BriefLedger:
            fake_ledger = FakeBriefLedger(db=shared_db)
            await fake_ledger.ensure_ready()
            typed_ledger = cast(BriefLedger, fake_ledger)
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
async def brief_ledger(brief_ledger_factory: BriefLedgerFactory) -> BriefLedger:
    """A single ready ledger on a fresh unique database (the common per-test case)."""
    return await brief_ledger_factory()


class TestPublishFirstVersion:
    async def test_first_publish_mints_v1(self, brief_ledger: BriefLedger) -> None:
        before = datetime.now(UTC)
        result = await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        after = datetime.now(UTC)
        assert result.first_version is True
        assert result.brief.version == 1
        assert result.brief.name == BRIEF_NAME_PROJECT
        assert result.brief.body == BODY_V1
        assert result.brief.created_by == PUBLISHER_LEAD
        assert result.brief.note is None
        _assert_recent_utc(result.brief.created_at, not_before=before, not_after=after)

    async def test_id_matches_the_pinned_uuid5_recipe(self, brief_ledger: BriefLedger) -> None:
        result = await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        assert result.brief.id == _brief_id(BRIEF_NAME_PROJECT, 1)

    async def test_note_is_recorded_when_given(self, brief_ledger: BriefLedger) -> None:
        result = await brief_ledger.publish(
            BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD, note="kickoff wave7"
        )
        assert result.brief.note == "kickoff wave7"


class TestPublishMaxPlusOne:
    async def test_second_publish_of_the_same_name_mints_v2(self, brief_ledger: BriefLedger) -> None:
        first = await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        second = await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_C1_LEAD)
        assert first.brief.version == 1
        assert second.brief.version == 2
        assert second.first_version is False

    async def test_get_head_reflects_the_latest_publish(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_C1_LEAD)
        head = await brief_ledger.get_head(BRIEF_NAME_PROJECT)
        assert head.version == 2
        assert head.body == BODY_V2

    async def test_two_names_version_independently(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_BASE, BODY_V1, created_by=PUBLISHER_LEAD)
        second_project = await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_LEAD)
        base_head = await brief_ledger.get_head(BRIEF_NAME_BASE)
        assert second_project.brief.version == 2
        assert base_head.version == 1


class TestConcurrentPublishesLandDistinctVersions:
    """THE load-bearing concurrency pin (spec §5.1): N concurrent publishes of
    the SAME brief name, on SEPARATE live connections, must ALL land on
    distinct, gapless, consecutive versions — no lost update, bounded (never
    hangs/exhausts). Runs against BOTH backends (fake-vs-real parity).
    """

    async def test_n_concurrent_publishes_all_land_with_distinct_consecutive_versions(
        self, brief_ledger_factory: BriefLedgerFactory
    ) -> None:
        ledgers = [await brief_ledger_factory() for _ in range(_CONCURRENT_PUBLISHERS)]

        results = await asyncio.gather(
            *[
                ledger.publish(
                    WAVE_BRIEF_NAME, f"standing instruction from publisher {index}", created_by=f"pub-{index}"
                )
                for index, ledger in enumerate(ledgers)
            ]
        )

        versions = sorted(result.brief.version for result in results)
        assert versions == list(range(1, _CONCURRENT_PUBLISHERS + 1)), (
            f"expected a gapless consecutive run of {_CONCURRENT_PUBLISHERS} versions, got {versions}"
        )
        # Every result's row is independently readable at ITS OWN version — no
        # lost update silently overwrote a sibling's row.
        for result in results:
            fetched = await ledgers[0].get_version(WAVE_BRIEF_NAME, result.brief.version)
            assert fetched.id == result.brief.id

        head = await ledgers[0].get_head(WAVE_BRIEF_NAME)
        assert head.version == _CONCURRENT_PUBLISHERS


class TestGetHeadAndVersionMisses:
    async def test_get_head_when_no_briefs_exist_at_all(self, brief_ledger: BriefLedger) -> None:
        with pytest.raises(UnknownBriefError) as exc_info:
            await brief_ledger.get_head(BRIEF_NAME_PROJECT)
        message = str(exc_info.value).lower()
        assert "no briefs published yet" in message
        assert "brief_publish" in message

    async def test_get_head_of_an_unknown_name_among_known_names(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        with pytest.raises(UnknownBriefError) as exc_info:
            await brief_ledger.get_head("wave99")
        message = str(exc_info.value)
        assert "wave99" in message
        assert BRIEF_NAME_PROJECT in message

    async def test_get_version_exact_hit(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_LEAD)
        v1 = await brief_ledger.get_version(BRIEF_NAME_PROJECT, 1)
        assert v1.body == BODY_V1

    async def test_get_version_beyond_head_names_the_real_head(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_LEAD)
        with pytest.raises(UnknownBriefVersionError) as exc_info:
            await brief_ledger.get_version(BRIEF_NAME_PROJECT, 9)
        message = str(exc_info.value)
        assert "9" in message
        assert "2" in message

    async def test_get_version_of_an_unknown_name(self, brief_ledger: BriefLedger) -> None:
        with pytest.raises(UnknownBriefError):
            await brief_ledger.get_version("never-published", 1)


class TestKnownNames:
    async def test_known_names_sorted_and_deduplicated_across_versions(
        self, brief_ledger: BriefLedger
    ) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_BASE, BODY_V1, created_by=PUBLISHER_LEAD)
        assert await brief_ledger.known_names() == [BRIEF_NAME_BASE, BRIEF_NAME_PROJECT]

    async def test_known_names_empty_before_any_publish(self, brief_ledger: BriefLedger) -> None:
        assert await brief_ledger.known_names() == []


class TestUnknownBriefErrorCappedKnownNames:
    """v4 audit D2 fix (docs/design/2026-07-12-pkt28-c1-semantics.md §7,
    CHANGELOG v4): ``_unknown_brief_error``'s known-names clause was an
    unbounded, uncounted ``', '.join(known)`` (briefs.py:756) -- an unbounded
    name dump in a teaching error is the same context blowout the render
    caps exist to prevent elsewhere. Spec grammar: ``unknown brief 'x' —
    known briefs: base, project, wave7 (+4 more)`` -- sorted, capped at
    ``_KNOWN_BRIEFS_CAP``, the ``(+K more)`` counter present ONLY when K>0.

    Contract decision (flagged in REPORT-c1-contract-d1d2-b.md): the spec's
    §4 constant table lists ``_KNOWN_BRIEFS_CAP`` under "(server.py)",
    mirroring ``_COVERAGE_NAMES_CAP``/``_MAX_FLEET_LIMIT`` -- but briefs.py
    cannot import a server.py constant (server.py imports FROM briefs.py; the
    reverse would cycle), AND this file already pins
    (``TestGetHeadAndVersionMisses.test_get_head_of_an_unknown_name_among_
    known_names``) that the LEDGER's own raised message embeds the known
    name directly -- reversing that into a bare-ledger/server-enriches split
    (mirroring ``UnknownAgentError``/contract decision #4) is a bigger,
    riskier redesign than this LOW defect warrants and would touch server.py
    handlers outside a tests-only contract wave's writable set. Pinned here
    instead: ``_KNOWN_BRIEFS_CAP`` is a module constant DEFINED IN
    ``briefs.py`` (value 10, matching the spec), consumed by
    ``_unknown_brief_error`` itself -- self-contained, zero risk to the
    already-green ledger contract (the existing test above has only ONE
    known name, well under any reasonable cap, so it is unaffected).
    """

    async def test_over_cap_names_are_sorted_capped_and_counted(self, brief_ledger: BriefLedger) -> None:
        names = [f"wave{i:02d}" for i in range(_KNOWN_BRIEFS_CAP + 2)]
        for name in names:
            await brief_ledger.publish(name, BODY_V1, created_by=PUBLISHER_LEAD)

        with pytest.raises(UnknownBriefError) as exc_info:
            await brief_ledger.get_head("totally-unknown")

        message = str(exc_info.value)
        assert "totally-unknown" in message
        sorted_names = sorted(names)
        for shown_name in sorted_names[:_KNOWN_BRIEFS_CAP]:
            assert shown_name in message
        for hidden_name in sorted_names[_KNOWN_BRIEFS_CAP:]:
            assert hidden_name not in message
        assert "(+2 more)" in message

    async def test_at_cap_names_carry_no_counter_suffix(self, brief_ledger: BriefLedger) -> None:
        names = [f"wave{i:02d}" for i in range(_KNOWN_BRIEFS_CAP)]
        for name in names:
            await brief_ledger.publish(name, BODY_V1, created_by=PUBLISHER_LEAD)

        with pytest.raises(UnknownBriefError) as exc_info:
            await brief_ledger.get_head("totally-unknown")

        message = str(exc_info.value)
        assert "more)" not in message
        for name in names:
            assert name in message


class TestAckHeadVersion:
    async def test_ack_at_head_is_recorded_as_not_already_acked(self, brief_ledger: BriefLedger) -> None:
        published = await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        result = await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_PROJECT,
            version=published.brief.version,
            via="explicit",
        )
        assert result.already_acked is False
        assert result.version == 1
        assert result.head_version == 1
        assert result.via == "explicit"

    async def test_acked_version_reflects_the_ack(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        assert await brief_ledger.acked_version(agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_PROJECT) == 1

    async def test_unacked_agent_has_no_acked_version(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        assert await brief_ledger.acked_version(agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_PROJECT) is None


class TestAckBehindVersionIsLegal:
    """§5.4: acking a version BELOW head is LEGAL and recorded — the ledger
    records the truth of what the agent actually read.
    """

    async def test_ack_of_a_behind_version_succeeds(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_LEAD)
        result = await brief_ledger.ack(
            agent_id=AGENT_SCOUT_C_ID,
            agent_name="scout-c",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        assert result.already_acked is False
        assert result.version == 1
        assert result.head_version == 2

    async def test_acked_version_reports_the_max_ack_not_just_the_latest_call(
        self, brief_ledger: BriefLedger
    ) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_LEAD)
        await brief_ledger.ack(
            agent_id=AGENT_SCOUT_C_ID,
            agent_name="scout-c",
            name=BRIEF_NAME_PROJECT,
            version=2,
            via="explicit",
        )
        await brief_ledger.ack(
            agent_id=AGENT_SCOUT_C_ID,
            agent_name="scout-c",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        assert await brief_ledger.acked_version(agent_id=AGENT_SCOUT_C_ID, name=BRIEF_NAME_PROJECT) == 2


class TestAckUnknownVersion:
    async def test_ack_beyond_head_names_the_real_head(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        with pytest.raises(UnknownBriefVersionError) as exc_info:
            await brief_ledger.ack(
                agent_id=AGENT_FIXER_B_ID,
                agent_name="fixer-b",
                name=BRIEF_NAME_PROJECT,
                version=9,
                via="explicit",
            )
        message = str(exc_info.value)
        assert "9" in message
        assert "1" in message

    async def test_ack_of_an_unknown_name_raises_unknown_brief_error(self, brief_ledger: BriefLedger) -> None:
        with pytest.raises(UnknownBriefError):
            await brief_ledger.ack(
                agent_id=AGENT_FIXER_B_ID,
                agent_name="fixer-b",
                name="never-published",
                version=1,
                via="explicit",
            )


class TestAckIdempotentReack:
    """§5.4: re-acking an already-acked (agent, name@version) is a no-op via
    UNIQUE(in, out); first-write-wins on ``via``.
    """

    async def test_reack_of_the_same_version_is_reported_as_already_acked(
        self, brief_ledger: BriefLedger
    ) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        second = await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        assert second.already_acked is True

    async def test_reack_does_not_create_a_second_edge(self, brief_ledger: BriefLedger) -> None:
        """A double-ack must not double-count in coverage (proves UNIQUE(in,
        out) rather than an accumulating list)."""
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        for _ in range(3):
            await brief_ledger.ack(
                agent_id=AGENT_FIXER_B_ID,
                agent_name="fixer-b",
                name=BRIEF_NAME_PROJECT,
                version=1,
                via="explicit",
            )
        coverage = await brief_ledger.coverage(
            BRIEF_NAME_PROJECT, active_agents=[_AgentRef(AGENT_FIXER_B_ID, "fixer-b")]
        )
        assert coverage.current_count == 1

    async def test_via_is_first_write_wins_across_register_then_explicit(
        self, brief_ledger: BriefLedger
    ) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        first = await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="register",
        )
        second = await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        assert first.via == "register"
        assert second.already_acked is True
        assert second.via == "register"  # unchanged — the second call is a pure no-op


class TestCoverageQuery:
    async def test_coverage_partitions_current_and_behind(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_LEAD)
        await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_PROJECT,
            version=2,
            via="explicit",
        )
        await brief_ledger.ack(
            agent_id=AGENT_SCOUT_C_ID,
            agent_name="scout-c",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        roster = [
            _AgentRef(AGENT_FIXER_B_ID, "fixer-b"),
            _AgentRef(AGENT_SCOUT_C_ID, "scout-c"),
            _AgentRef(AGENT_AUDIT_D_ID, "audit-d"),
        ]
        coverage = await brief_ledger.coverage(BRIEF_NAME_PROJECT, active_agents=roster)
        assert coverage.head_version == 2
        assert coverage.total_agents == 3
        assert coverage.current_count == 1
        behind_by_name = {entry.agent_name: entry.acked_version for entry in coverage.behind}
        assert behind_by_name == {"scout-c": 1, "audit-d": None}

    async def test_coverage_all_current_yields_an_empty_behind_list(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        roster = [_AgentRef(AGENT_FIXER_B_ID, "fixer-b")]
        coverage = await brief_ledger.coverage(BRIEF_NAME_PROJECT, active_agents=roster)
        assert coverage.behind == []
        assert coverage.current_count == coverage.total_agents == 1

    async def test_coverage_of_an_unknown_name_raises(self, brief_ledger: BriefLedger) -> None:
        with pytest.raises(UnknownBriefError):
            await brief_ledger.coverage("never-published", active_agents=[])


class TestCoverageQueryCountIsBounded:
    """F3 (REPORT-c1-audit-fixwave.md, finding): ``coverage()`` iterates its
    caller-supplied roster with a per-member ``acked_version()`` call --
    unbounded N+1, live-measured 2N+7 store round-trips (107 @N=50, 417
    @N=205, 1007 @N=500; the D1 fix made the roster complete -- correctly --
    and thereby made this N+1 unbounded, where it used to ride the
    ``_MAX_FLEET_LIMIT``-capped window). Not a correctness defect -- every
    served number stays true -- but a scaling defect with a clean fix.

    Real-only: ``FakeBriefLedger`` has no ``_query`` seam to instrument (it
    is an independent in-memory implementation with no store round-trips at
    all) -- mirrors ``TestBriefLedgerConnectionLifecycle``'s real-only
    posture, the same "no fault/instrumentation hook on the fake" limit the
    ``_comms_fakes.py`` module docstring itself documents.

    Expected production fix (the shape named for the implementer):
    ``coverage()`` already issues ONE query for ``versions`` (the brief's own
    version rows). It should issue exactly ONE further query fetching every
    ``briefed`` edge for the roster's agent ids in a single shot (e.g.
    ``SELECT in, out FROM briefed WHERE in IN $roster_ids``) and join that
    result against ``versions`` in memory to compute each member's
    acked/behind status -- replacing the per-member ``acked_version()`` loop
    entirely. Total query count independent of N (a small constant, e.g. 2),
    never 2N+7.

    Correctness invariant for the implementer: ``TestCoverageQuery`` above
    already pins ``BriefCoverage``'s exact result shape (head_version,
    total_agents, current_count, behind list + order) against a real store
    -- the fix must keep those tests green unchanged; this class adds NO new
    correctness assertion, only a query-COUNT bound.
    """

    @staticmethod
    async def _coverage_query_count(agent_count: int) -> int:
        """Publish v1, ack ``agent_count`` distinct agents at head, then call
        ``coverage()`` with the ``_query`` seam instrumented -- returns the
        number of ``_query`` calls that ONE ``coverage()`` call issued.

        Mirrors ``_delayed_signin_factory`` (test_surreal_store.py)'s
        capture-then-wrap idiom: an instance-local reassignment, thrown away
        with the ledger at the end of this helper -- never a class-level
        monkeypatch, so no cross-test restore is needed.
        """
        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()
        ledger = BriefLedger(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )
        try:
            await ledger.ensure_ready()
            await ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
            roster = [
                _AgentRef(f"agent-{index:03d}-id", f"agent-{index:03d}") for index in range(agent_count)
            ]
            for ref in roster:
                await ledger.ack(
                    agent_id=ref.id,
                    agent_name=ref.name,
                    name=BRIEF_NAME_PROJECT,
                    version=1,
                    via="explicit",
                )

            call_count = 0
            original_query = ledger._query

            async def _counting_query(statement: str, params: dict[str, Any] | None = None) -> Any:
                nonlocal call_count
                call_count += 1
                return await original_query(statement, params)

            ledger._query = _counting_query  # type: ignore[method-assign]
            await ledger.coverage(BRIEF_NAME_PROJECT, active_agents=roster)
            return call_count
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_query_count_does_not_grow_with_roster_size(self) -> None:
        small_n_count = await self._coverage_query_count(5)
        large_n_count = await self._coverage_query_count(50)
        assert large_n_count == small_n_count, (
            f"coverage() issued {small_n_count} store queries at N=5 but "
            f"{large_n_count} at N=50 -- expected a query count independent "
            f"of roster size (one grouped edge query, not one per member)"
        )


class TestHostileBodyRoundTripsVerbatim:
    """Storage models are RAW ``str`` — sanitisation is render-time line
    policy, never storage mutation (spec §5.2). A hostile body (newlines + a
    row-shaped forgery line + backtick runs) must round-trip byte-identical
    through storage.
    """

    async def test_hostile_body_round_trips_byte_identical(self, brief_ledger: BriefLedger) -> None:
        hostile = (
            "STANDING INSTRUCTION\n"
            "second line with a control char \x1b[31m escape\n"
            f"{_ROW_FORGE_PAYLOAD}\n"
            "``` a backtick fence run ```\n"
            "````` an even longer run `````"
        )
        published = await brief_ledger.publish(BRIEF_NAME_PROJECT, hostile, created_by=PUBLISHER_LEAD)
        assert published.brief.body == hostile
        fetched = await brief_ledger.get_head(BRIEF_NAME_PROJECT)
        assert fetched.body == hostile
        fetched_by_version = await brief_ledger.get_version(BRIEF_NAME_PROJECT, 1)
        assert fetched_by_version.body == hostile


class TestBriefStructuralFields:
    """Structural pin: the ``Brief`` model's field set is EXACTLY the C1 §0
    schema slice.
    """

    def test_brief_field_set_is_exactly_the_c1_slice(self) -> None:
        expected = {"id", "name", "version", "body", "created_by", "note", "created_at"}
        assert set(Brief.model_fields) == expected

    def test_brief_model_forbids_unknown_fields(self) -> None:
        assert Brief.model_config.get("extra") == "forbid"


class TestBriefNameConstants:
    def test_project_and_base_are_the_pinned_protocol_vocabulary(self) -> None:
        assert BRIEF_NAME_PROJECT == "project"
        assert BRIEF_NAME_BASE == "base"


class TestPublishMintConstants:
    """§4: the publish-retry mechanism's module constants — budget 4 (not 12,
    findings' N-way figure): publish contention is lead-shaped, ≤2-way.
    """

    def test_mint_retry_constants_match_the_spec(self) -> None:
        assert _BRIEF_PUBLISH_MAX_ATTEMPTS == 4
        assert _BRIEF_PUBLISH_BACKOFF_SECONDS == 0.01
        assert _BRIEF_PUBLISH_JITTER_SLOTS == 4
        assert _BRIEF_PUBLISH_JITTER_SECONDS == 0.001


# ---------------------------------------------------------------------------
# Connection lifecycle (global CLAUDE.md law: degradation -> recovery over a
# dropped-and-recovered store connection). Real-only — mirrors
# ``TestQueryClassifiedErrorPosture`` in test_task_ledger.py.
# ---------------------------------------------------------------------------

_BRIEF_SENSITIVE_ENGINE_TEXT = "Found NONE for field `body`, with record `brief:poisonvalue`"
_BRIEF_SENSITIVE_MARKER = "poisonvalue"
_BRIEF_TRANSPORT_ENGINE_TEXT = "There was a problem with the database: Not allowed to do this"


class _RejectingConnection:
    """A fake SDK connection whose ``query`` raises a scripted error — clones
    ``test_task_ledger.py``'s ``_RejectingConnection`` fault-injector.
    """

    def __init__(self, error: BaseException) -> None:
        self.error = error

    async def query(self, statement: str, params: dict[str, Any]) -> Any:
        raise self.error

    async def close(self) -> None:
        return None


class TestBriefLedgerConnectionLifecycle:
    @staticmethod
    def _bare_ledger() -> BriefLedger:
        return BriefLedger(
            url="ws://127.0.0.1:19557/rpc",  # never dialed — the fake handle short-circuits
            namespace="ns",
            database="db",
            user="root",
            password="root",
        )

    async def test_domain_rejection_never_echoes_the_raw_engine_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger = self._bare_ledger()
        ledger._connection = cast(
            "_SurrealConnection",
            _RejectingConnection(ServerError(ErrorKind.INTERNAL, _BRIEF_SENSITIVE_ENGINE_TEXT)),
        )
        connection_before = ledger._connection
        with caplog.at_level(logging.ERROR, logger="loremaster.briefs"):
            with pytest.raises(SurrealStoreError) as exc_info:
                await ledger._query("UPDATE brief SET body = $b", {"b": "poison"})
        message = str(exc_info.value)
        assert type(exc_info.value) is SurrealStoreError
        assert not isinstance(exc_info.value, SurrealConnectionError)
        assert ledger._connection is connection_before
        assert _BRIEF_SENSITIVE_ENGINE_TEXT not in message
        assert _BRIEF_SENSITIVE_MARKER not in message
        assert "server log" in message.lower()

    async def test_transport_failure_drops_the_handle_and_raises_connection_error(self) -> None:
        ledger = self._bare_ledger()
        ledger._connection = cast(
            "_SurrealConnection",
            _RejectingConnection(ServerError(ErrorKind.NOT_ALLOWED, _BRIEF_TRANSPORT_ENGINE_TEXT)),
        )
        with pytest.raises(SurrealConnectionError):
            await ledger._query("SELECT * FROM brief", {})
        assert ledger._connection is None

    async def test_recovers_on_the_next_call_after_a_dropped_connection(self) -> None:
        """Recovery: after the cached handle is dropped, the NEXT call reconnects
        and succeeds — the ledger is never permanently wedged by a transient loss.
        Real-only (a fake holds no connection to drop).
        """
        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()
        ledger = BriefLedger(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        try:
            await ledger.ensure_ready()
            await ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
            ledger._connection = None  # simulate a dropped connection
            recovered = await ledger.get_head(BRIEF_NAME_PROJECT)
            assert recovered.version == 1
        finally:
            await ledger.close()
            await drop_database(env)
