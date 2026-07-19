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
        via: Literal["register", "explicit", "publish"]   # v7 — finding #98

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
        async publish(name, body, *, created_by, note=None,
                      agent_id=None) -> BriefPublishResult   # v7 — finding #98:
            # a given agent_id makes publish SELF-ACK its author — the briefed
            # edge (via='publish') is RELATE'd in the SAME transaction as the
            # brief CREATE (design doc §5.1 step 2), never a second write.
        async get_head(name) -> Brief
        async get_version(name, version) -> Brief
        async known_names() -> list[str]
        async ack(*, agent_id, agent_name, name, version, via) -> BriefAckResult
        async acked_version(*, agent_id, name) -> int | None
        async coverage(name, *, active_agents) -> BriefCoverage

    Exceptions: BriefLedgerError(RuntimeError);
                UnknownBriefError(BriefLedgerError);
                UnknownBriefVersionError(BriefLedgerError).

    Module constants: BRIEF_NAME_PROJECT, BRIEF_NAME_BASE.
        (The four private mint-retry constants are GONE — finding #108: the mint
        rides the shared ``_txn.retry_on_conflict`` driver and owns no retry
        mechanics of its own. See test_retry_seam.py.)

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
from typing import Any, cast, get_args
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
    _KNOWN_BRIEFS_CAP,
    BRIEF_NAME_BASE,
    BRIEF_NAME_PROJECT,
    Brief,
    BriefAckResult,
    BriefAckVia,
    BriefLedger,
    BriefPublishResult,
    UnknownBriefError,
    UnknownBriefVersionError,
)
from loremaster.store._txn import (
    SurrealConnectionError,
    SurrealStoreError,
    _SurrealConnection,
    execute_transaction,
)
from loremaster.store.surreal_schema import BRIEF_TABLE, BRIEFED_RELATION
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


async def _edge_count(ledger: BriefLedger) -> int:
    """The REAL store's total ``briefed`` edge count — a raw read that sees
    ORPHAN edges (an edge whose brief row was rolled back), which
    ``acked_version``'s edge->brief join cannot: it drops a dangling target
    silently. Real-store only (the atomicity pins).
    """
    rows = await ledger._query(f"SELECT count() FROM {BRIEFED_RELATION} GROUP ALL")  # noqa: SLF001
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


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


# ===========================================================================
# v7 / finding #98 — publish() SELF-ACKS its author, in the SAME transaction
# as the brief row (design doc §5.1 step 2, §5.3, §9.4).
#
# The contract this section pins on production (the builder codes to THIS):
#
#     async def publish(name, body, *, created_by, note=None,
#                       agent_id: str | None = None) -> BriefPublishResult
#
# ``agent_id`` is the PUBLISHING AGENT's opaque row id — never its
# ``created_by`` display name (a ``briefed`` edge is ``agent->briefed->brief``:
# only a real agent row id can carry it). When given, the CREATE fragment gains
# the author's self-ack RELATE (``via='publish'``, ``at=now``) and BOTH
# statements ride ONE ``execute_transaction``. When omitted (a ledger-level
# caller with no agent row in play), no edge is written.
#
#     BriefAckVia = Literal["register", "explicit", "publish"]   # widened
# ===========================================================================


async def _publish_as(
    ledger: BriefLedger,
    name: str,
    body: str,
    *,
    created_by: str,
    agent_id: str,
    note: str | None = None,
) -> BriefPublishResult:
    """Publish under the v7 signature — the ONE call site of the new
    ``agent_id`` kwarg, so the contract's demanded signature change is stated
    in exactly one place (and is the only place mypy reports until the builder
    lands it).
    """
    return await ledger.publish(name, body, created_by=created_by, note=note, agent_id=agent_id)


async def _stored_via(ledger: BriefLedger, *, agent_id: str, name: str, version: int) -> BriefAckResult:
    """Read back the STORED edge for (agent, name@version) through the public
    surface: a re-ack is an idempotent no-op that reports the FIRST-recorded
    ``via`` (design doc §5.4). Backend-agnostic — works against the real store
    and the fake alike, and doubles as the §9.5 ``already acked`` probe.
    """
    return await ledger.ack(
        agent_id=agent_id, agent_name="probe", name=name, version=version, via="explicit"
    )


class TestPublishSelfAcksItsAuthor:
    """§5.1 step 2 / §5.3: the author has BY CONSTRUCTION read what it wrote, so
    ``publish`` records an ordinary stored head-ack for it (``via='publish'``).
    Not a render carve-out — a real edge, which is what makes the author drop
    out of every downstream count (coverage numerator, skew, fleet cell,
    heartbeat) with no special-casing anywhere.
    """

    async def test_publish_writes_the_authors_briefed_edge_at_the_published_version(
        self, brief_ledger: BriefLedger
    ) -> None:
        result = await _publish_as(
            brief_ledger,
            BRIEF_NAME_PROJECT,
            BODY_V1,
            created_by=PUBLISHER_LEAD,
            agent_id=AGENT_FIXER_B_ID,
        )
        acked = await brief_ledger.acked_version(agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_PROJECT)
        assert acked == result.brief.version == 1, (
            "the publishing agent must be acked at the version it just published "
            "(design doc §5.1 step 2) — today it is served as a straggler behind its own brief"
        )

    async def test_the_self_ack_edge_records_via_publish(self, brief_ledger: BriefLedger) -> None:
        """The stored ``via`` is the THIRD vocabulary word, not ``explicit`` and
        not ``register``: the fleet/audit surfaces distinguish how an ack was
        obtained, and an author's ack was never an explicit read-and-ack call.
        """
        await _publish_as(
            brief_ledger,
            BRIEF_NAME_PROJECT,
            BODY_V1,
            created_by=PUBLISHER_LEAD,
            agent_id=AGENT_FIXER_B_ID,
        )
        probe = await _stored_via(
            brief_ledger, agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_PROJECT, version=1
        )
        assert probe.via == "publish"

    async def test_an_author_explicitly_acking_its_own_version_is_an_idempotent_no_op(
        self, brief_ledger: BriefLedger
    ) -> None:
        """§9.5's NEW v7 case: the author's own ``brief_ack`` of the version it
        just published hits the ``already acked`` path (the ``via=publish`` edge
        already exists) — never a second edge, never a UNIQUE(in,out) explosion.
        """
        await _publish_as(
            brief_ledger,
            BRIEF_NAME_PROJECT,
            BODY_V1,
            created_by=PUBLISHER_LEAD,
            agent_id=AGENT_FIXER_B_ID,
        )
        probe = await _stored_via(
            brief_ledger, agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_PROJECT, version=1
        )
        assert probe.already_acked is True
        assert probe.head_version == 1
        # ... and the ack is still SINGULAR: the agent's ack set is exactly {v1}.
        mapping = await brief_ledger.acked_versions_for_ids(
            [AGENT_FIXER_B_ID], name=BRIEF_NAME_PROJECT
        )
        assert mapping == {AGENT_FIXER_B_ID: 1}

    async def test_publish_without_an_agent_id_writes_no_edge(self, brief_ledger: BriefLedger) -> None:
        """A ledger-level publish with no agent row in play (no ``agent_id``)
        writes NO edge — the edge is ``agent->briefed->brief`` and there is no
        agent to hang it on. Pins the OPTIONALITY of the kwarg honestly: a build
        that invented an edge from the ``created_by`` STRING (which is a display
        name, not a row id) would be caught here and by the test above.
        """
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        acked = await brief_ledger.acked_version(agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_PROJECT)
        assert acked is None
        mapping = await brief_ledger.acked_versions_for_ids(
            [AGENT_FIXER_B_ID, AGENT_SCOUT_C_ID], name=BRIEF_NAME_PROJECT
        )
        assert mapping == {}

    async def test_the_author_is_current_and_only_the_others_are_behind(
        self, brief_ledger: BriefLedger
    ) -> None:
        """The consequence §5.3 sweeps: the author is excluded from ``behind``
        by an ORDINARY stored head-ack — coverage's numerator counts it at head.
        """
        await _publish_as(
            brief_ledger,
            BRIEF_NAME_PROJECT,
            BODY_V1,
            created_by=PUBLISHER_LEAD,
            agent_id=AGENT_FIXER_B_ID,
        )
        roster = [
            _AgentRef(id=AGENT_FIXER_B_ID, name="fixer-b"),
            _AgentRef(id=AGENT_SCOUT_C_ID, name="scout-c"),
            _AgentRef(id=AGENT_AUDIT_D_ID, name="audit-d"),
        ]
        coverage = await brief_ledger.coverage(BRIEF_NAME_PROJECT, active_agents=roster)
        assert coverage.current_count == 1
        assert coverage.total_agents == 3
        assert [(entry.agent_name, entry.acked_version) for entry in coverage.behind] == [
            ("audit-d", None),
            ("scout-c", None),
        ]

    async def test_a_republish_by_a_different_author_leaves_the_prior_author_at_its_old_version(
        self, brief_ledger: BriefLedger
    ) -> None:
        """v7 CHANGELOG, stated verbatim: a re-publish by a DIFFERENT author is
        ordinary behind-at-vN for the previous author — no special casing, no
        edge rewrite, no retro-ack. The prior author's stored ack stays at the
        version IT published; the new author is current.
        """
        await _publish_as(
            brief_ledger, BRIEF_NAME_PROJECT, BODY_V1, created_by="lead", agent_id=AGENT_FIXER_B_ID
        )
        second = await _publish_as(
            brief_ledger, BRIEF_NAME_PROJECT, BODY_V2, created_by="scout-c", agent_id=AGENT_SCOUT_C_ID
        )
        assert second.brief.version == 2
        assert await brief_ledger.acked_version(agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_PROJECT) == 1
        assert await brief_ledger.acked_version(agent_id=AGENT_SCOUT_C_ID, name=BRIEF_NAME_PROJECT) == 2
        coverage = await brief_ledger.coverage(
            BRIEF_NAME_PROJECT,
            active_agents=[
                _AgentRef(id=AGENT_FIXER_B_ID, name="fixer-b"),
                _AgentRef(id=AGENT_SCOUT_C_ID, name="scout-c"),
            ],
        )
        assert coverage.current_count == 1
        assert [(entry.agent_name, entry.acked_version) for entry in coverage.behind] == [
            ("fixer-b", 1)
        ]

    async def test_every_one_of_eight_concurrent_publishers_self_acks_exactly_its_own_version(
        self, brief_ledger_factory: BriefLedgerFactory
    ) -> None:
        """The self-ack under the PINNED 8-way race (§5.1's contention degree —
        never a 2-way stand-in): eight racers, eight distinct agent ids, eight
        distinct versions, and each agent acked at ITS OWN version — never a
        shared edge, never a lost one, never one agent acked at another's
        version. A build that RELATEd outside the minted transaction (or reused
        a stale ``version`` local) shows up here as a duplicate or a hole.
        """
        ledgers = [await brief_ledger_factory() for _ in range(_CONCURRENT_PUBLISHERS)]
        agent_ids = [f"agent-{index}-opaque-id" for index in range(_CONCURRENT_PUBLISHERS)]

        results = await asyncio.gather(
            *[
                _publish_as(
                    ledger,
                    WAVE_BRIEF_NAME,
                    f"standing instruction from publisher {index}",
                    created_by=f"pub-{index}",
                    agent_id=agent_ids[index],
                )
                for index, ledger in enumerate(ledgers)
            ]
        )

        versions = sorted(result.brief.version for result in results)
        assert versions == list(range(1, _CONCURRENT_PUBLISHERS + 1))
        mapping = await ledgers[0].acked_versions_for_ids(agent_ids, name=WAVE_BRIEF_NAME)
        assert mapping == {
            agent_ids[index]: result.brief.version for index, result in enumerate(results)
        }, "each of the eight publishers must be acked at exactly the version IT minted"
        # And nobody else got dragged in: exactly eight edges, one per racer.
        assert len(mapping) == _CONCURRENT_PUBLISHERS


class TestPublishSelfAckIsWrittenInTheSameTransaction:
    """§5.1 step 2: "one atomic write, never a second separately-failable call".
    Real-store only — these are statements-on-the-wire and rollback pins, which
    an in-memory fake cannot honestly stand in for.
    """

    @staticmethod
    async def _real_ledger() -> tuple[BriefLedger, SurrealEnv]:
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
        await ledger.ensure_ready()
        return ledger, env

    async def test_the_row_and_the_edge_ride_ONE_execute_transaction(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """THE structural discriminator between the two builds that both satisfy
        "the edge exists after a publish": a same-transaction RELATE, and a
        second write issued after the CREATE commits. Only the first survives a
        crash (or a rejection) between them — the second can leave a published
        brief whose author is a phantom straggler forever, which is finding #98
        itself, one layer down.

        Pinned by counting the WRITE transactions a publish issues (the mint and
        the read-back ride the single-statement ``_query`` seam, not
        ``execute_transaction``): exactly ONE, and its composed SQL carries BOTH
        the brief CREATE and the briefed RELATE.
        """
        ledger, env = await self._real_ledger()
        calls: list[str] = []

        async def spy(statement_text: str, params: dict[str, Any], **kwargs: Any) -> None:
            calls.append(statement_text)
            await execute_transaction(statement_text, params, **kwargs)

        try:
            # Patch the NAME in briefs' own namespace (the module imports the
            # function directly), delegating to the real seam so the write still
            # lands — a counting spy, never a stub.
            monkeypatch.setattr("loremaster.briefs.execute_transaction", spy)
            await _publish_as(
                ledger,
                BRIEF_NAME_PROJECT,
                BODY_V1,
                created_by=PUBLISHER_LEAD,
                agent_id=AGENT_FIXER_B_ID,
            )
        finally:
            monkeypatch.undo()
            await ledger.close()
            await drop_database(env)

        assert len(calls) == 1, (
            f"a publish must issue exactly ONE write transaction (the CREATE + the "
            f"self-ack RELATE together, §5.1 step 2) — saw {len(calls)}: {calls!r}"
        )
        composed = calls[0]
        assert f"CREATE type::record('{BRIEF_TABLE}'" in composed
        assert f"->{BRIEFED_RELATION}->" in composed, (
            "the author's self-ack RELATE must be composed INTO the same transaction as "
            "the brief CREATE, never issued as a second, separately-failable write"
        )

    async def test_a_rejected_create_rolls_back_the_edge_too_and_burns_no_version(self) -> None:
        """ATOMICITY, observed: a blank body is rejected by the schema's
        non-empty ASSERT. With both statements in ONE transaction, the whole
        write disappears — no brief row, no orphan ``briefed`` edge — and the
        guarded compensating release hands the version back, so the NEXT publish
        is gapless. (An orphan edge is invisible to ``acked_version`` — its join
        drops a dangling brief id — so this counts the EDGE TABLE directly.)
        """
        ledger, env = await self._real_ledger()
        try:
            await _publish_as(
                ledger, BRIEF_NAME_PROJECT, BODY_V1, created_by="lead", agent_id=AGENT_FIXER_B_ID
            )
            edges_before = await _edge_count(ledger)
            assert edges_before == 1  # the v1 author's own self-ack

            with pytest.raises(SurrealStoreError):
                await _publish_as(
                    ledger, BRIEF_NAME_PROJECT, "", created_by="scout-c", agent_id=AGENT_SCOUT_C_ID
                )

            assert await _edge_count(ledger) == edges_before, (
                "the rejected publish's self-ack edge must roll back WITH the row — a "
                "surviving edge is an ack to a brief that does not exist"
            )
            head = await ledger.get_head(BRIEF_NAME_PROJECT)
            assert head.version == 1, "the rejected CREATE must leave no brief row behind"
            assert (
                await ledger.acked_version(agent_id=AGENT_SCOUT_C_ID, name=BRIEF_NAME_PROJECT)
            ) is None
            # The guarded release (§5.1) hands the burnt number back: no gap.
            recovered = await _publish_as(
                ledger, BRIEF_NAME_PROJECT, BODY_V2, created_by="scout-c", agent_id=AGENT_SCOUT_C_ID
            )
            assert recovered.brief.version == 2
            assert (
                await ledger.acked_version(agent_id=AGENT_SCOUT_C_ID, name=BRIEF_NAME_PROJECT)
            ) == 2
        finally:
            await ledger.close()
            await drop_database(env)


class TestBriefAckViaVocabulary:
    """The wire vocabulary is a CLOSED THREE-value set after v7 (finding #98).
    Written out as literals — a pin derived from production's own alias would be
    a tautology (see test_comms_schema.py's note on the retired DDL pin).
    """

    def test_via_literal_is_exactly_register_explicit_publish(self) -> None:
        assert get_args(BriefAckVia) == ("register", "explicit", "publish")


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


class TestAckedVersionsForIds:
    """finding #94 (REPORT-c1b-contract-9495.md): pins the PUBLIC bulk method
    the ``fleet`` action's fix needs -- ``BriefLedger.acked_versions_for_ids``
    -- a self-contained sibling of the existing PRIVATE
    ``_acked_versions_for_roster`` (which requires a pre-computed
    ``version_by_brief_id`` the ``fleet`` action does not already have in
    hand; this one takes only a brief ``name`` and a list of agent ids,
    exactly what ``fleet`` already holds).

    Pinned public API (the contract a later implementation must match)::

        async def acked_versions_for_ids(
            self, agent_ids: Sequence[str], *, name: str
        ) -> dict[str, int]

    Convention mirrors ``_acked_versions_for_roster`` exactly (see its own
    docstring): an id ABSENT from the returned mapping is unbriefed for
    ``name`` -- never a ``None`` value in the dict, never silently dropped in
    a way indistinguishable from "never asked about" (the caller always
    supplies the full ``agent_ids`` it asked about, so absence is legible).
    An unknown ``name`` (no published version at all) returns ``{}`` --
    nobody can be briefed on a brief that does not exist; this is a bulk
    STATUS READ, not an error condition the way ``coverage()``'s
    ``UnknownBriefError`` is for a caller computing a skew standing.

    Runs against BOTH the real store and ``FakeBriefLedger`` (the
    ``brief_ledger`` fixture) -- mirrors ``TestCoverageQuery``'s posture:
    this is a correctness contract, not a store-dialect concern.
    """

    async def test_empty_agent_ids_returns_an_empty_mapping(self, brief_ledger: BriefLedger) -> None:
        """Boundary N=0 -- issues no lookup at all, no crash on an empty roster."""
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        result = await brief_ledger.acked_versions_for_ids([], name=BRIEF_NAME_PROJECT)
        assert result == {}

    async def test_unknown_brief_name_returns_an_empty_mapping(self, brief_ledger: BriefLedger) -> None:
        result = await brief_ledger.acked_versions_for_ids([AGENT_FIXER_B_ID], name="never-published")
        assert result == {}

    async def test_unbriefed_agent_is_absent_from_the_mapping(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        result = await brief_ledger.acked_versions_for_ids([AGENT_FIXER_B_ID], name=BRIEF_NAME_PROJECT)
        assert AGENT_FIXER_B_ID not in result

    async def test_agent_at_head_maps_to_the_head_version(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        result = await brief_ledger.acked_versions_for_ids([AGENT_FIXER_B_ID], name=BRIEF_NAME_PROJECT)
        assert result[AGENT_FIXER_B_ID] == 1

    async def test_agent_behind_head_maps_to_its_own_older_version(self, brief_ledger: BriefLedger) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.ack(
            agent_id=AGENT_SCOUT_C_ID,
            agent_name="scout-c",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_LEAD)  # head now v2
        result = await brief_ledger.acked_versions_for_ids([AGENT_SCOUT_C_ID], name=BRIEF_NAME_PROJECT)
        assert result[AGENT_SCOUT_C_ID] == 1

    async def test_agent_acked_at_multiple_versions_resolves_to_the_max(
        self, brief_ledger: BriefLedger
    ) -> None:
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_LEAD)
        # Out-of-order: v2 acked BEFORE v1 -- a naive first/last-write-wins
        # join would resolve to whichever edge it saw last, not the max.
        await brief_ledger.ack(
            agent_id=AGENT_AUDIT_D_ID,
            agent_name="audit-d",
            name=BRIEF_NAME_PROJECT,
            version=2,
            via="explicit",
        )
        await brief_ledger.ack(
            agent_id=AGENT_AUDIT_D_ID,
            agent_name="audit-d",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        result = await brief_ledger.acked_versions_for_ids([AGENT_AUDIT_D_ID], name=BRIEF_NAME_PROJECT)
        assert result[AGENT_AUDIT_D_ID] == 2

    async def test_mixed_roster_isolates_unbriefed_behind_and_current_together(
        self, brief_ledger: BriefLedger
    ) -> None:
        """Scale N=3 with all three outcomes side by side in ONE call, so a
        join that silently drops or conflates one id is caught."""
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_PROJECT,
            version=1,
            via="explicit",
        )
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V2, created_by=PUBLISHER_LEAD)  # head now v2
        await brief_ledger.ack(
            agent_id=AGENT_SCOUT_C_ID,
            agent_name="scout-c",
            name=BRIEF_NAME_PROJECT,
            version=2,
            via="explicit",
        )
        result = await brief_ledger.acked_versions_for_ids(
            [AGENT_FIXER_B_ID, AGENT_SCOUT_C_ID, AGENT_AUDIT_D_ID], name=BRIEF_NAME_PROJECT
        )
        assert result == {AGENT_FIXER_B_ID: 1, AGENT_SCOUT_C_ID: 2}
        assert AGENT_AUDIT_D_ID not in result

    async def test_edge_to_a_different_brief_name_is_filtered_out(self, brief_ledger: BriefLedger) -> None:
        """An agent briefed on ``BRIEF_NAME_BASE``, never on
        ``BRIEF_NAME_PROJECT``, must not leak into a ``BRIEF_NAME_PROJECT``
        lookup -- the join must filter edges by the brief's OWN name, not
        merely by agent id (exercises the ``continue`` guard a naive
        rewrite could drop)."""
        await brief_ledger.publish(BRIEF_NAME_PROJECT, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.publish(BRIEF_NAME_BASE, BODY_V1, created_by=PUBLISHER_LEAD)
        await brief_ledger.ack(
            agent_id=AGENT_FIXER_B_ID,
            agent_name="fixer-b",
            name=BRIEF_NAME_BASE,
            version=1,
            via="explicit",
        )
        result = await brief_ledger.acked_versions_for_ids([AGENT_FIXER_B_ID], name=BRIEF_NAME_PROJECT)
        assert AGENT_FIXER_B_ID not in result


class TestAckedVersionsForIdsQueryCountIsBounded:
    """finding #94 (REPORT-c1b-contract-9495.md): ``_comms_fleet``'s per-row
    ``acked_version()`` loop -- measured 407 store round-trips / 234 ms at
    limit=200 -- is BOUNDED by the display cap (never grows past the
    display limit no matter the roster size), unlike ``coverage()``'s
    pre-fix N+1 which was genuinely unbounded. Not a correctness defect --
    every served number stays true -- but a scaling defect with a fix that
    is nearly free once ``_acked_versions_for_roster`` exists:
    ``acked_versions_for_ids`` is its public, self-contained sibling.

    Real-only: ``FakeBriefLedger`` has no ``_query`` seam to instrument (see
    ``TestCoverageQueryCountIsBounded``'s docstring for the same limit).

    Expected production fix: ``acked_versions_for_ids`` issues exactly ONE
    query for ``name``'s version rows + ONE grouped ``briefed`` edge query
    over the ids passed in -- total query count independent of
    ``len(agent_ids)`` (a small constant, e.g. 2), never one
    ``acked_version()`` call per id.

    Correctness invariant for the implementer: ``TestAckedVersionsForIds``
    above already pins the exact result shape (unbriefed/behind/at-head/
    multi-version-max, cross-brief filtering) against a real store -- the
    fix must keep those tests green unchanged; this class adds NO new
    correctness assertion, only a query-COUNT bound.
    """

    @staticmethod
    async def _query_count(agent_count: int) -> int:
        """Publish v1, ack ``agent_count`` distinct agents at head, then call
        ``acked_versions_for_ids`` with the ``_query`` seam instrumented --
        returns the number of ``_query`` calls that ONE call issued. Mirrors
        ``TestCoverageQueryCountIsBounded._coverage_query_count``'s
        capture-then-wrap idiom exactly.
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
            agent_ids = [f"agent-{index:03d}-id" for index in range(agent_count)]
            for agent_id in agent_ids:
                await ledger.ack(
                    agent_id=agent_id,
                    agent_name=agent_id,
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
            await ledger.acked_versions_for_ids(agent_ids, name=BRIEF_NAME_PROJECT)
            return call_count
        finally:
            await ledger.close()
            await drop_database(env)

    async def test_empty_agent_ids_issues_no_queries(self) -> None:
        """Boundary N=0 -- an empty roster short-circuits before any query."""
        assert await self._query_count(0) == 0

    async def test_query_count_does_not_grow_with_displayed_row_count(self) -> None:
        small_n_count = await self._query_count(5)
        large_n_count = await self._query_count(50)
        assert large_n_count == small_n_count, (
            f"acked_versions_for_ids issued {small_n_count} store queries at "
            f"N=5 but {large_n_count} at N=50 -- expected a query count "
            f"independent of the number of displayed rows (one grouped "
            f"edge query, not one per row)"
        )
        assert large_n_count > 0, (
            "N=50 with every agent acked must still issue the versions + "
            "grouped-edge queries -- a count of 0 would mean the method is "
            "short-circuiting incorrectly, not scaling correctly"
        )

    async def test_query_count_does_not_grow_above_the_display_cap(self) -> None:
        """adversary P2 finding #4 (REPORT-c1-audit-adversary.md): the
        sibling test above never crosses ``_MAX_FLEET_LIMIT`` (200,
        ``server.py``) -- the exact scale finding #94 was MEASURED at (407
        round-trips at limit=200). 205 is hardcoded rather than imported
        from ``loremaster.server`` to keep this file independently
        collectible (mirrors this file's own decoupling stance -- see the
        module docstring).
        """
        above_cap_count = await self._query_count(205)
        small_n_count = await self._query_count(5)
        assert above_cap_count == small_n_count, (
            f"acked_versions_for_ids issued {small_n_count} store queries at "
            f"N=5 but {above_cap_count} at N=205 (one past _MAX_FLEET_LIMIT) "
            f"-- expected a query count independent of scale, even above the "
            f"display cap"
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


# ---------------------------------------------------------------------------
# DELETED (finding #108): ``TestPublishMintConstants`` pinned the four private mint
# constants — a 4-attempt budget, a linear backoff, and a FOUR-SLOT jitter table (the
# names are in test_retired_symbols.py's registry; naming them here would be the very
# dangling reference that gate exists to forbid) — against spec §5.1's claim that
# "publish contention is lead-shaped, ≤2-way".
#
# The spec was wrong (the contract itself pins an EIGHT-way race), the jitter was the
# defect (4 slots, 8 racers: the pigeonhole guarantees two racers share a slot and then
# stay lockstepped for the whole ladder), and the constants existed only because the
# substrate offered nothing to call. The mint rides ``_txn.retry_on_conflict`` now: one
# policy, one jitter, one typed exhaustion error, zero constants of its own.
#
# This test could only ever have gone GREEN — it asserted that a specified defect was
# still faithfully implemented. Its replacements are in test_retry_seam.py: the mint
# draws from the SHARED jitter, and every caller exhausts on the SAME budget.
# ---------------------------------------------------------------------------


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


# ===========================================================================
# pkt02 (#103, spec v8 §5.3 subscription + §9.2): the SUBSCRIBED-NAME SKEW read
# heartbeat uses to surface non-'project' briefs an agent has ACKED and is now
# behind on. The FAKE (``_comms_fakes.py::FakeBriefLedger.subscribed_name_skew``)
# is the surface spec; these pins run it against the REAL store too via the
# parametrized ``brief_ledger`` fixture. Against CLEAN production they are RED for
# the right reason — ``BriefLedger`` has no ``subscribed_name_skew`` yet, so the
# call raises ``AttributeError`` (a real-store BUILDER deliverable, validated
# reference impl in REPORT-pkt02-contract.md). Against the fake they are GREEN.
#
# Contract (mirroring the fake — the fake is the contract):
#   subscribed(agent, name) = >=1 briefed edge to ANY version of ``name`` (ack =
#   subscribe); per subscribed name acked = MAX acked version; skew = head - acked
#   returned ONLY when > 0; the ``exclude`` (standing) name is omitted (heartbeat
#   renders it via its own universal path). Returns (name, head, acked) tuples.
#   ORDER + CAP are RENDER concerns (§9.2) — the fake returns unordered/uncapped,
#   so these set-compare (see REPORT §FOLLOW-UP for the ordering/cap flag).
# ===========================================================================


async def _publish_versions(ledger: BriefLedger, name: str, count: int) -> None:
    for version in range(1, count + 1):
        await ledger.publish(name, f"{name} standing instruction v{version}", created_by=PUBLISHER_LEAD)


async def _subscribe(ledger: BriefLedger, *, agent_id: str, name: str, version: int) -> None:
    """Record an ack edge — i.e. SUBSCRIBE ``agent_id`` to ``name`` at ``version``."""
    await ledger.ack(agent_id=agent_id, agent_name="probe", name=name, version=version, via="explicit")


class TestSubscribedNameSkew:
    """§5.3 subscription + §9.2 heartbeat subscribed-name skew (the #103 ledger read)."""

    async def test_a_subscribed_behind_name_is_returned_with_head_and_acked(
        self, brief_ledger: BriefLedger
    ) -> None:
        await _publish_versions(brief_ledger, WAVE_BRIEF_NAME, 3)
        await _subscribe(brief_ledger, agent_id=AGENT_FIXER_B_ID, name=WAVE_BRIEF_NAME, version=1)
        result = await brief_ledger.subscribed_name_skew(
            agent_id=AGENT_FIXER_B_ID, exclude=BRIEF_NAME_PROJECT
        )
        # (name, head, acked) — pins the tuple SHAPE (head is v3, acked is v1).
        assert (WAVE_BRIEF_NAME, 3, 1) in result, result

    async def test_a_subscribed_but_current_name_is_omitted_when_skew_is_zero(
        self, brief_ledger: BriefLedger
    ) -> None:
        await _publish_versions(brief_ledger, WAVE_BRIEF_NAME, 2)
        await _subscribe(brief_ledger, agent_id=AGENT_FIXER_B_ID, name=WAVE_BRIEF_NAME, version=2)
        result = await brief_ledger.subscribed_name_skew(
            agent_id=AGENT_FIXER_B_ID, exclude=BRIEF_NAME_PROJECT
        )
        assert all(entry[0] != WAVE_BRIEF_NAME for entry in result), (
            f"a subscribed agent AT head (skew 0) must not be surfaced: {result!r}"
        )

    async def test_an_unsubscribed_name_with_a_head_is_never_returned(
        self, brief_ledger: BriefLedger
    ) -> None:
        # fixer-b subscribes to 'base' (behind) but NEVER acks 'wave7' (which HAS a head).
        await _publish_versions(brief_ledger, BRIEF_NAME_BASE, 2)
        await _subscribe(brief_ledger, agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_BASE, version=1)
        await _publish_versions(brief_ledger, WAVE_BRIEF_NAME, 2)
        result = await brief_ledger.subscribed_name_skew(
            agent_id=AGENT_FIXER_B_ID, exclude=BRIEF_NAME_PROJECT
        )
        assert (BRIEF_NAME_BASE, 2, 1) in result, result
        assert all(entry[0] != WAVE_BRIEF_NAME for entry in result), (
            f"an UNSUBSCRIBED name with a head was surfaced — subscription bound (§5.3): {result!r}"
        )

    async def test_the_excluded_standing_name_is_omitted_even_when_behind(
        self, brief_ledger: BriefLedger
    ) -> None:
        await _publish_versions(brief_ledger, BRIEF_NAME_PROJECT, 2)
        await _subscribe(brief_ledger, agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_PROJECT, version=1)
        await _publish_versions(brief_ledger, WAVE_BRIEF_NAME, 2)
        await _subscribe(brief_ledger, agent_id=AGENT_FIXER_B_ID, name=WAVE_BRIEF_NAME, version=1)
        result = await brief_ledger.subscribed_name_skew(
            agent_id=AGENT_FIXER_B_ID, exclude=BRIEF_NAME_PROJECT
        )
        assert (WAVE_BRIEF_NAME, 2, 1) in result, result
        assert all(entry[0] != BRIEF_NAME_PROJECT for entry in result), (
            f"the EXCLUDED standing brief was surfaced — heartbeat renders it universally: {result!r}"
        )

    async def test_acked_is_the_MAX_version_across_an_agents_edges(
        self, brief_ledger: BriefLedger
    ) -> None:
        """acked is the MAX version the agent has an edge to — never the edge
        COUNT, the MIN, or the last/first edge recorded. The fixture makes those
        wrong builds each return a DIFFERENT number: head 4, edges to v1 and v3
        (recorded out of order, v3 then v1). MAX=3 (correct, skew 1); COUNT=2;
        MIN=1; last-recorded=1. Only a max-over-edges build yields (…, 4, 3) — an
        acked-v1-then-v2/head-3 fixture would let a COUNT build pass (2 == 2).
        """
        await _publish_versions(brief_ledger, WAVE_BRIEF_NAME, 4)
        # Record the HIGHER edge first so a last-write-wins build resolves to v1,
        # not v3 — max and last-seen then disagree (mirrors the out-of-order ack
        # in TestAckedVersionsForIds.test_agent_acked_at_multiple_versions_...).
        await _subscribe(brief_ledger, agent_id=AGENT_FIXER_B_ID, name=WAVE_BRIEF_NAME, version=3)
        await _subscribe(brief_ledger, agent_id=AGENT_FIXER_B_ID, name=WAVE_BRIEF_NAME, version=1)
        result = await brief_ledger.subscribed_name_skew(
            agent_id=AGENT_FIXER_B_ID, exclude=BRIEF_NAME_PROJECT
        )
        assert (WAVE_BRIEF_NAME, 4, 3) in result, (
            f"acked must be the MAX acked version (3): a COUNT build yields 2, a "
            f"MIN/last-recorded build yields 1 — only max-over-edges gives (…, 4, 3): {result!r}"
        )

    async def test_another_agents_edges_never_leak(self, brief_ledger: BriefLedger) -> None:
        await _publish_versions(brief_ledger, WAVE_BRIEF_NAME, 2)
        await _subscribe(brief_ledger, agent_id=AGENT_FIXER_B_ID, name=WAVE_BRIEF_NAME, version=1)  # behind
        await _subscribe(brief_ledger, agent_id=AGENT_SCOUT_C_ID, name=WAVE_BRIEF_NAME, version=2)  # at head
        fixer = await brief_ledger.subscribed_name_skew(
            agent_id=AGENT_FIXER_B_ID, exclude=BRIEF_NAME_PROJECT
        )
        scout = await brief_ledger.subscribed_name_skew(
            agent_id=AGENT_SCOUT_C_ID, exclude=BRIEF_NAME_PROJECT
        )
        assert (WAVE_BRIEF_NAME, 2, 1) in fixer, fixer
        assert all(entry[0] != WAVE_BRIEF_NAME for entry in scout), (
            f"scout-c is AT head — another agent's behind-edge must not leak into its skew: {scout!r}"
        )

    async def test_an_agent_with_no_subscriptions_gets_an_empty_list(
        self, brief_ledger: BriefLedger
    ) -> None:
        """Boundary (N=0 subscriptions): a behind-able head EXISTS, but this agent
        has acked nothing — the result is exactly ``[]``. Kills a build that
        ignores ``agent_id`` and returns every behind name (the §5.3 subscription
        bound: an agent that never acked a name is not a party to it).
        """
        await _publish_versions(brief_ledger, WAVE_BRIEF_NAME, 2)  # a behind-able head exists...
        result = await brief_ledger.subscribed_name_skew(
            agent_id=AGENT_SCOUT_C_ID, exclude=BRIEF_NAME_PROJECT  # ...but scout-c never acked it
        )
        assert result == [], (
            f"an agent with zero briefed edges is subscribed to nothing — "
            f"nothing may be surfaced: {result!r}"
        )

    async def test_DISCRIMINATOR_two_subscribed_skews_plus_unsubscribed_plus_excluded(
        self, brief_ledger: BriefLedger
    ) -> None:
        """The repo-law single discriminating fixture. ONE agent, four names:
          - wave7:  head 4, acked v1 -> subscribed+behind, skew 3
          - base:   head 3, acked v2 -> subscribed+behind, skew 1 (acked-VALUE 2
                    != its edge-COUNT of 1, so a count-not-version build reds here)
          - loner:  head 2, UNSUBSCRIBED (never acked)
          - project(excluded): head 2, acked v1 -> subscribed+behind but EXCLUDED

        The result set must be EXACTLY the two kept names. This ONE fixture kills,
        at once: a build that returns unsubscribed names (loner leaks); a build
        that forgets ``exclude`` (project leaks despite skew 1); a build that
        returns the edge COUNT instead of the acked VERSION (base -> (base,3,1));
        and a build that drops a subscribed-behind name (base or wave7 missing).
        Distinct heads/acked/skews across the two kept names avoid the
        monoculture/alignment blind spots — no two fixture values coincide.
        """
        await _publish_versions(brief_ledger, WAVE_BRIEF_NAME, 4)  # head 4
        await _subscribe(brief_ledger, agent_id=AGENT_FIXER_B_ID, name=WAVE_BRIEF_NAME, version=1)  # skew 3
        await _publish_versions(brief_ledger, BRIEF_NAME_BASE, 3)  # head 3
        await _subscribe(  # acked v2 (NOT v1): acked-value 2 != edge-count 1
            brief_ledger, agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_BASE, version=2
        )  # skew 1
        await _publish_versions(brief_ledger, "loner", 2)  # head 2 — fixer-b UNSUBSCRIBED
        await _publish_versions(brief_ledger, BRIEF_NAME_PROJECT, 2)  # head 2
        await _subscribe(  # subscribed + behind on the standing brief -> EXCLUDED
            brief_ledger, agent_id=AGENT_FIXER_B_ID, name=BRIEF_NAME_PROJECT, version=1
        )
        result = await brief_ledger.subscribed_name_skew(
            agent_id=AGENT_FIXER_B_ID, exclude=BRIEF_NAME_PROJECT
        )
        assert set(result) == {(WAVE_BRIEF_NAME, 4, 1), (BRIEF_NAME_BASE, 3, 2)}, result
