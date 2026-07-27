"""Contract tests for **packet 43 — derivation-source unification** (`a075e85`).

Binding spec: ``docs/plans/v2/43-derivation-source-unification.md``.  **Packet 43 is a
DESIGN pass before it is a build**, so most of this file is deliberately SKIPPED: the
pins state what must become true, not how.  Unskipping them is packet 43's entry
condition.

**Provenance — why these pins are here and not in packet 04a.**  They were authored as
part of 04a's `ENFORCED` sweep contract
(``docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-contract-04a-enforced.md`` §4.D2) and
SPLIT out on 2026-07-26 by operator ruling.  04a flips ``briefed``; the ``refers`` /
``answers_to`` flip cannot land with it, because:

    ``CodeGraph._derive_nodes`` reads the CHUNK SET its caller supplies, while
    ``_derive_edges``' reference half RE-READS THE FILE OFF DISK (``_resolve`` calls
    ``evict_resolved_file`` to read it deliberately fresh).  ``Indexer.index_file(tier,
    path, source)`` takes ``source`` from ITS caller, so a save landing between the
    watcher's read and the derivation's read makes the two disagree — and MEASURED
    2026-07-26, a divergent chunk set makes ``build_file_graph_fragment`` emit
    ``refers`` RELATEs whose ``src`` ``code_node`` no statement of the same fragment
    ever creates.

Today those are invisible dangling edges.  Under ``ENFORCED`` each one **aborts the whole
file's index transaction** — the graph slice rides the SAME ``store.apply`` as the chunk /
``file_text`` / manifest fragments (``Indexer._index_chunks``), so the file is isolated
``failed`` (last-good retained, one WARNING) and its chunks never update.

**The operator ruled the ROOT fix over both local patches** — neither minting the missing
``code_node`` nor dropping the edge.  ``_derive_edges`` stops re-reading; both derivations
read ONE source.  That is packet 43's subject, and it is why
``test_a_DIVERGENT_chunk_set_still_yields_a_self_consistent_fragment`` below is stated as
a ∀ over the FRAGMENT rather than as a survey of a corpus: pinning "our 56 modules are
clean" would be the quantifier law violated — an invariant conditioned on the inputs that
happened to be tested.

**What is SKIPPED and what RUNS, and why they differ.**  Every pin that would be
permanently RED until packet 43 lands is ``@pytest.mark.skip``ped with a reason naming
both ``packet 43`` and the finding, so it is greppable and cannot be silently inherited.
The five pins that are GREEN today and must STAY green **run**: four of them exercise
``_unsatisfied_relate_endpoints`` — the helper the headline ∀ pin depends on — and a
helper nobody runs between now and packet 43 is a helper that can rot into a false green
the day everything is unskipped.  *A guard nobody runs is a hope with a filename.*  This
is a deliberate deviation from "skip every moved pin", disclosed in
``docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-contract-04a-enforced.md`` §SPLIT.
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from _enforced_relations_scaffold import (
    DEFERRED_TO_PACKET_43,
    KNOWN_RELATION_EDGES,
    apply_ddl,
    every_emitted_relation_table,
    ghost_id,
    is_enforced,
    migration_db,  # noqa: F401 - re-exported pytest fixture
    old_world_ddl,
    record_exists,
    relate,
    relation_table_statements,
    seed_endpoint,
    unenforced_ddl,
)
from _surreal_harness import SurrealConnection, SurrealEnv, run
from loremaster.graph import CodeGraph
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.store.surreal_schema import (
    ANSWERS_TO_RELATION,
    CODE_NODE_TABLE,
    NAME_TABLE,
    REFERS_RELATION,
    generate_graph_ddl,
)
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker
from pydantic import SecretStr
from surrealdb import RecordID

#: The one skip reason, so ``grep "packet 43"`` over the test tree finds every deferred
#: pin in one pass and no variant spelling can hide one.
SKIP_REASON = (
    "packet 43 (derivation-source unification, docs/plans/v2/43-derivation-source-"
    "unification.md): the refers/answers_to ENFORCED flip is BLOCKED until _derive_edges "
    "and _derive_nodes read ONE source — see "
    "docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-contract-04a-enforced.md §4.D2. "
    "UNSKIPPING THESE IS PACKET 43'S ENTRY CONDITION."
)

#: The two edges packet 43 flips, with the slice generator that owns them.  Both endpoint
#: tables live in the SAME slice, so the endpoint generator is that slice too.
_GRAPH_EDGES: tuple[tuple[str, str, str, Callable[[], str]], ...] = (
    (REFERS_RELATION, CODE_NODE_TABLE, NAME_TABLE, generate_graph_ddl),
    (ANSWERS_TO_RELATION, CODE_NODE_TABLE, NAME_TABLE, generate_graph_ddl),
)
_GRAPH_EDGE_IDS = [edge[0] for edge in _GRAPH_EDGES]


# =========================================================================== #
# THE ENTRY CONDITION.
# =========================================================================== #


class TestPacket43EmptiesTheDeferredSet:
    """The one pin that says packet 43 is DONE.

    ``_enforced_relations_scaffold.DEFERRED_TO_PACKET_43`` is the named, greppable hole
    in packet 04a's ∀ law — the *deny-by-default with a small, enumerated, ASSERTED
    safe-set* shape repo law prescribes, rather than silence.  04a's own ∀ pin permits
    exactly the edges in that set to be un-guarded; emptying it is what makes the law
    total again.
    """

    @pytest.mark.skip(reason=SKIP_REASON)
    def test_the_deferred_set_is_EMPTY(self) -> None:
        assert DEFERRED_TO_PACKET_43 == frozenset(), (
            "packet 43 is complete only when no relation edge is exempt from the ENFORCED "
            "∀ law. Empty DEFERRED_TO_PACKET_43 in _enforced_relations_scaffold.py and "
            "unskip this file — leaving the set populated keeps a permanent hole that "
            "packet 04a's ∀ pin is contractually obliged to tolerate"
        )

    def test_the_deferred_set_names_EXACTLY_the_two_code_graph_edges(self) -> None:
        """RUNS today, and must go RED when packet 43 empties the set — at which point
        this pin is deleted along with the constant.

        It exists so the deferral cannot QUIETLY GROW: an author who hits the ∀ pin and
        "fixes" it by adding a third edge to the exemption set reddens here.
        """
        assert set(DEFERRED_TO_PACKET_43) == {REFERS_RELATION, ANSWERS_TO_RELATION}, (
            "the ENFORCED exemption set may only ever SHRINK. If you added an edge to it, "
            "you deferred a guard rather than shipping one — that is a scope decision and "
            "it belongs to the operator, not to a passing build"
        )

    def test_every_deferred_edge_is_a_KNOWN_relation_edge(self) -> None:
        """RUNS today.  A deferral naming an edge the schema does not emit is a typo that
        would silently exempt nothing while looking like a considered decision.
        """
        assert set(DEFERRED_TO_PACKET_43) <= set(KNOWN_RELATION_EDGES)


# =========================================================================== #
# THE MOVED DDL PINS — refers / answers_to.
# =========================================================================== #


class TestTheCodeGraphEdgesAreEnforced:
    """Packet 04a's per-edge ``ENFORCED`` pins for the two deferred edges.

    These are the DECLARED-RED targets of packet 43's own mutation proof, exactly as
    ``briefed``'s are for 04a's: delete ``enforced=True`` from one
    ``_define_relation_table`` call and precisely that edge's pins must redden.
    """

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.parametrize("edge", _GRAPH_EDGE_IDS)
    def test_the_edge_carries_ENFORCED_in_its_own_slice(self, edge: str) -> None:
        emitted = relation_table_statements(generate_graph_ddl())
        assert edge in emitted, f"generate_graph_ddl no longer emits the {edge!r} relation table"
        assert is_enforced(emitted[edge]), f"{edge} must be declared ENFORCED: {emitted[edge]!r}"

    @pytest.mark.skip(reason=SKIP_REASON)
    def test_NO_relation_table_is_exempt_once_packet_43_lands(self) -> None:
        """The ∀ law with no exemption — the total form of packet 04a's pin.

        04a's version reads ``unguarded <= DEFERRED_TO_PACKET_43``; this one reads
        ``unguarded == {}``.  Both are needed: 04a's keeps "a fifth edge cannot arrive
        un-guarded" true for packet 04b while the hole is open, and this one closes it.
        """
        unguarded = {
            edge: f"{label}: {statement}"
            for edge, (label, statement) in every_emitted_relation_table().items()
            if not is_enforced(statement)
        }
        assert unguarded == {}, (
            "every TYPE RELATION table this schema emits must carry ENFORCED — the only "
            "guard that validates BOTH endpoints and covers INSERT RELATION (store "
            f"reference §4). Un-guarded: {unguarded}"
        )


# =========================================================================== #
# THE MOVED DIRTY-STORE MIGRATION PINS — refers / answers_to.
#
# THE TEST ENVIRONMENT IS A FICTION (store reference §1.6): every test mints a VIRGIN
# database, and on a virgin database ANY clause creates the table WITH whatever the
# generator says — so a flip that never migrates is invisible to every offline pin and
# every ordinary live pin.  The flip lands on EXISTING tables.  These are the only pins
# that can see it.
# =========================================================================== #


class TestTheOldWorldDerivationIsNotVacuous:
    """Keeps the migration pins below honest: if the "old" and "current" DDL are
    IDENTICAL, they migrate a schema to ITSELF and test nothing at all while looking
    perfectly green.
    """

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator"), _GRAPH_EDGES, ids=_GRAPH_EDGE_IDS
    )
    def test_the_old_world_DIFFERS_from_todays_generator(
        self, edge: str, in_table: str, out_table: str, generator: Callable[[], str]
    ) -> None:
        assert old_world_ddl(edge, in_table, out_table, generator) != generator(), (
            f"re-emitting {edge!r} with enforced=False does not change the DDL, which "
            f"means today's generator ALREADY emits it un-enforced — the flip has not "
            f"happened"
        )


class TestTheEnforcedFlipMigratesADirtyStore:
    """THE #107 SHAPE, per deferred edge.

    ``IF NOT EXISTS`` is a MEASURED silent no-op on an existing edge table and
    ``OVERWRITE`` is the only clause that lands the flip (probe §3 legs A/B, 3.2.1).
    These pins apply the OLD (un-enforced) definition, DIRTY the store with a dangling
    edge that is legal under it, then apply today's generator.
    """

    @staticmethod
    async def _dirty_old_world(
        connection: SurrealConnection,
        env: SurrealEnv,
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
    ) -> tuple[str, str]:
        """Apply the OLD world and write ONE dangling edge under it.

        Returns ``(live_in_id, ghost_out_id)`` — a real IN endpoint and an OUT endpoint
        verified NOT to exist.
        """
        await apply_ddl(connection, generator(), url=env.url)
        await apply_ddl(connection, old_world_ddl(edge, in_table, out_table, generator), url=env.url)
        live_in = ghost_id("live_in")
        await seed_endpoint(connection, in_table, live_in)
        ghost_out = ghost_id("ghost_out")
        assert not await record_exists(connection, out_table, ghost_out), (
            "the negative fixture's OUT endpoint must genuinely NOT exist — an "
            "all-registered fixture cannot discriminate a guarded table from an "
            "un-guarded one"
        )
        await relate(
            connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
            out_id=ghost_out,
        )
        return live_in, ghost_out

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator"), _GRAPH_EDGES, ids=_GRAPH_EDGE_IDS
    )
    async def test_BASELINE_the_old_world_really_ACCEPTS_a_dangling_edge(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
    ) -> None:
        """Without this control, "the guard is live after migrating" could be true
        because it was ALWAYS live — and the migration itself never tested.
        """
        connection, env = migration_db
        await self._dirty_old_world(connection, env, edge, in_table, out_table, generator)
        assert await run(connection, f"SELECT id FROM {edge}"), (
            f"the OLD (un-enforced) {edge} definition was supposed to ACCEPT a dangling "
            f"RELATE — if it did not, this fixture is not installing the old world"
        )

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator"), _GRAPH_EDGES, ids=_GRAPH_EDGE_IDS
    )
    async def test_the_guard_is_LIVE_after_applying_todays_ddl_to_a_DIRTY_store(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
    ) -> None:
        """THE load-bearing pin.  A definition that emits perfectly and never LANDS is
        invisible to every offline pin.

        The rejection is demanded BEHAVIOURALLY, never by reading back a stored DDL
        string: probe §3 leg A records that a stored-DDL diff alone could be a rendering
        artifact, so the behavioural confirmation is the measurement.
        """
        connection, env = migration_db
        live_in, _ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator
        )
        await apply_ddl(connection, generator(), url=env.url)
        fresh_ghost = ghost_id("still_absent")
        assert not await record_exists(connection, out_table, fresh_ghost)
        with pytest.raises(Exception):  # noqa: B017 - the engine's NotFoundError surface
            await relate(
                connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
                out_id=fresh_ghost,
            )

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator"), _GRAPH_EDGES, ids=_GRAPH_EDGE_IDS
    )
    async def test_POSITIVE_CONTROL_a_REAL_endpoint_is_still_accepted_after_the_flip(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
    ) -> None:
        """A guard that refuses EVERYTHING is not a guard, it is an outage."""
        connection, env = migration_db
        live_in, _ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator
        )
        await apply_ddl(connection, generator(), url=env.url)
        live_out = ghost_id("live_out")
        await seed_endpoint(connection, out_table, live_out)
        await relate(
            connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
            out_id=live_out,
        )
        rows = await run(
            connection,
            f"SELECT id FROM {edge} WHERE out = $out",
            {"out": RecordID(out_table, live_out)},
        )
        assert rows, f"a {edge} RELATE between two REAL endpoints must still be accepted"

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator"), _GRAPH_EDGES, ids=_GRAPH_EDGE_IDS
    )
    async def test_the_PRE_EXISTING_dangling_edge_SURVIVES_the_flip(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
    ) -> None:
        """Probe §3 P2b, MEASURED on 3.2.1 — the flip succeeds with a dangling row present
        and there is NO validation sweep over existing rows.

        Pinned because the opposite belief is the attractive one: *turning ENFORCED on and
        calling the ghost problem closed is a FALSE ALL-CLEAR* (store reference §4).
        Cleanup is a separate data migration, ruled OUT as #236.
        """
        connection, env = migration_db
        _live_in, ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator
        )
        before = await run(connection, f"SELECT id FROM {edge}")
        await apply_ddl(connection, generator(), url=env.url)
        after = await run(
            connection,
            f"SELECT id, out FROM {edge} WHERE out = $out",
            {"out": RecordID(out_table, ghost_out)},
        )
        assert len(before) == 1, "fixture: exactly one dangling edge should exist pre-flip"
        assert after, "the pre-existing dangling edge must SURVIVE the flip"

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator"), _GRAPH_EDGES, ids=_GRAPH_EDGE_IDS
    )
    async def test_the_migration_is_IDEMPOTENT_on_an_already_migrated_store(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
    ) -> None:
        """``ensure_ready`` re-applies this DDL on EVERY boot, so repeated applies must be
        clean no-ops that neither raise nor lose the guard.
        """
        connection, env = migration_db
        live_in, _ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator
        )
        for _ in range(3):
            await apply_ddl(connection, generator(), url=env.url)
        live_out = ghost_id("live_out")
        await seed_endpoint(connection, out_table, live_out)
        await relate(
            connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
            out_id=live_out,
        )


class TestTheUnEnforcingDoor:
    """The hazard, pinned so the next author meets it DELIBERATELY (probe §3 item (a)).

    ``DEFINE TABLE OVERWRITE`` is FULL REPLACE for ``ENFORCED`` too: a re-emission that
    omits the keyword silently un-guards the table.  §1.2 states full-replace for
    ``ASSERT``; §4 does NOT state it for ``ENFORCED``.  The door cannot be CLOSED — it is
    the same semantics that makes the flip land — so it is pinned instead.
    """

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator"), _GRAPH_EDGES, ids=_GRAPH_EDGE_IDS
    )
    async def test_re_emitting_the_edge_WITHOUT_ENFORCED_silently_un_guards_it(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
    ) -> None:
        """Three legs in order, and the middle one is the control that makes the third
        meaningful: (1) today's DDL guards; (2) an ``OVERWRITE`` without ``ENFORCED``
        raises nothing at all; (3) the dangling RELATE it refused a moment ago is
        accepted again.
        """
        connection, env = migration_db
        await apply_ddl(connection, generator(), url=env.url)
        live_in = ghost_id("live_in")
        await seed_endpoint(connection, in_table, live_in)
        ghost_out = ghost_id("ghost_out")
        assert not await record_exists(connection, out_table, ghost_out)
        with pytest.raises(Exception):  # noqa: B017 - the engine's NotFoundError surface
            await relate(
                connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
                out_id=ghost_out,
            )

        await apply_ddl(connection, unenforced_ddl(edge, in_table, out_table), url=env.url)

        await relate(
            connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
            out_id=ghost_out,
        )
        assert await run(connection, f"SELECT id FROM {edge}"), (
            "MEASURED (probe §3 item (a)): DEFINE TABLE OVERWRITE omitting ENFORCED "
            "silently un-guards the table"
        )


# =========================================================================== #
# THE HEADLINE PIN — the ∀ over the FRAGMENT, statement-ORDERED.
#
# This is packet 43's actual subject.  Probe §6.5 flagged the condition
# ``{edge.src} ⊆ {node.qualified_name}`` and could not settle it; contract-04a settled
# it as "conditionally" and MEASURED the divergence (§4.D2).  The property below is the
# quantifier-law-clean statement of what must hold — not "our corpus is clean", but
# "this fragment never RELATEs from an endpoint it did not create".
# =========================================================================== #

_FRAGMENT_CREATE_RE = re.compile(r"^CREATE \$(\w+)\b")
_FRAGMENT_UPSERT_RE = re.compile(r"^UPSERT \$(\w+)\b")
_FRAGMENT_RELATE_RE = re.compile(r"^RELATE \$(\w+)->(\w+)->\$(\w+)\b")

_GRAPH_TIER = "custom"
_GRAPH_FILE = "demo/svc.py"
_GRAPH_MODULE = "demo.svc"

#: A realistic multi-chunk module: an in-project import, a class with a method, a
#: module-level function, a nested function, and an unresolved reference.  ≥3 symbol
#: kinds and a resolved AND an unresolved edge — a single-class fixture cannot
#: discriminate a derivation that emits src names for only one node kind.
_GRAPH_SOURCE = textwrap.dedent(
    '''\
    """A small but realistic service module."""
    from __future__ import annotations

    from demo.helper import target


    class Service:
        """Does the thing."""

        def boot(self):
            """Boot it."""
            return target()


    def helper_fn():
        """A module-level helper with a nested function."""

        def inner():
            return target()

        return inner() + undefined_symbol()
    '''
)

_GRAPH_HELPER_SOURCE = 'def target():\n    """The in-project reference target."""\n    return 1\n'


def _chunk(file_path: str, source: str) -> list[Chunk]:
    """Chunk ``source`` through the REAL ``PythonAstChunker`` — the production producer.

    Hand-rolling ``Chunk`` objects would let a chunker-shape drift slip past the pins
    below (``test_graph.py``'s own rationale, cloned).
    """
    context = ChunkContext(
        slug="demo-project",
        file_path=file_path,
        count_tokens=lambda text: max(1, len(text) // 4),
        max_input_tokens=8192,
    )
    return PythonAstChunker().chunk(source, context)


@pytest.fixture()
def graph_project(tmp_path: Path) -> Path:
    """The demo package materialised on disk so astroid resolves it in-project."""
    root = tmp_path / "project"
    (root / "demo").mkdir(parents=True, exist_ok=True)
    (root / "demo" / "__init__.py").write_text("", encoding="utf-8")
    (root / "demo" / "helper.py").write_text(_GRAPH_HELPER_SOURCE, encoding="utf-8")
    (root / "demo" / "svc.py").write_text(_GRAPH_SOURCE, encoding="utf-8")
    return root


@pytest.fixture()
def code_graph(graph_project: Path) -> SurrealCodeGraph:
    """A ``SurrealCodeGraph`` used ONLY as a pure fragment BUILDER.

    ``build_file_graph_fragment`` is documented pure — the derivation is sync CPU +
    on-disk source reads, never a socket touch — so the connection details are
    deliberately unreachable: if any pin below ever opened one it would fail loudly
    rather than quietly contacting a store.
    """
    return SurrealCodeGraph(
        url="ws://127.0.0.1:1/rpc",
        namespace="unused",
        database="unused",
        user="unused",
        password=SecretStr("unused"),
        tier_roots={_GRAPH_TIER: graph_project},
        project_roots=[graph_project],
    )


def _unsatisfied_relate_endpoints(fragment: Any) -> list[tuple[str, str, str]]:
    """Every RELATE endpoint in ``fragment`` that no EARLIER statement created.

    Statement-ORDERED on purpose.  Probe §6.4, MEASURED: ``ENFORCED`` is checked at
    RELATE time, not deferred to COMMIT (leg L5 — the endpoint exists by the end of the
    transaction and the RELATE is still rejected because it ran first), and it is
    per-RECORD, not per-transaction (leg L8).  So "statement order" IS the contract, and
    an unordered set check would pass a fragment the engine rejects.

    Returns ``(edge, param name, rendered RecordID)`` triples.
    """
    created: set[str] = set()
    unsatisfied: list[tuple[str, str, str]] = []
    for raw in fragment.statements:
        statement = raw.strip()
        mint = _FRAGMENT_CREATE_RE.match(statement) or _FRAGMENT_UPSERT_RE.match(statement)
        if mint is not None:
            created.add(str(fragment.params[mint.group(1)]))
            continue
        relate_match = _FRAGMENT_RELATE_RE.match(statement)
        if relate_match is None:
            continue
        for param_name in (relate_match.group(1), relate_match.group(3)):
            rendered = str(fragment.params[param_name])
            if rendered not in created:
                unsatisfied.append((relate_match.group(2), param_name, rendered))
    return unsatisfied


def _relate_count(fragment: Any) -> int:
    """How many RELATEs the fragment carries (the anti-vacuity counter)."""
    return sum(1 for raw in fragment.statements if _FRAGMENT_RELATE_RE.match(raw.strip()))


class TestTheCodeGraphFragmentNeverRelatesFromAnUncreatedEndpoint:
    """§I — the property that makes the ``refers``/``answers_to`` flip SAFE, stated as a ∀
    over the fragment rather than as a survey of a corpus.

    Four of these five pins RUN today and must STAY green: they exercise
    ``_unsatisfied_relate_endpoints`` itself, and an instrument nobody runs between now
    and packet 43 can rot into a false green the day the headline pin is unskipped.
    """

    def test_a_realistic_multi_chunk_file_is_self_consistent(
        self, code_graph: SurrealCodeGraph
    ) -> None:
        """RUNS.  The establishing leg: the shape production actually indexes.  If this
        ever reddens, packet 43's change is breaking real indexing.
        """
        chunks = _chunk(_GRAPH_FILE, _GRAPH_SOURCE)
        fragment = code_graph.build_file_graph_fragment(
            _GRAPH_TIER, _GRAPH_FILE, chunks, module_name=_GRAPH_MODULE
        )
        assert _relate_count(fragment) >= 4, (
            "the fixture must actually produce RELATEs — a fragment with none satisfies "
            f"the assertion below vacuously. Got {_relate_count(fragment)}"
        )
        assert _unsatisfied_relate_endpoints(fragment) == []

    def test_BOTH_edge_kinds_are_present_in_the_fixture(
        self, code_graph: SurrealCodeGraph
    ) -> None:
        """RUNS.  FIXTURES MUST DISCRIMINATE.  ``answers_to``'s src is a ``code_node``
        CREATEd one statement earlier (structurally safe); ``refers``' src comes from a
        DIFFERENT derivation and is the one at risk.  A fixture carrying only
        ``answers_to`` would pass the pin above while proving nothing about the edge
        packet 43 is actually about.
        """
        chunks = _chunk(_GRAPH_FILE, _GRAPH_SOURCE)
        fragment = code_graph.build_file_graph_fragment(
            _GRAPH_TIER, _GRAPH_FILE, chunks, module_name=_GRAPH_MODULE
        )
        edges = {
            match.group(2)
            for match in (_FRAGMENT_RELATE_RE.match(raw.strip()) for raw in fragment.statements)
            if match is not None
        }
        assert edges == {REFERS_RELATION, ANSWERS_TO_RELATION}, (
            f"the fixture must exercise BOTH code-graph edges; got {sorted(edges)}"
        )

    @pytest.mark.skip(reason=SKIP_REASON)
    def test_a_DIVERGENT_chunk_set_still_yields_a_self_consistent_fragment(
        self, code_graph: SurrealCodeGraph
    ) -> None:
        """**THE HEADLINE PIN OF PACKET 43.**  RED until the derivation sources are
        unified; do not delete it, do not weaken it, and do not satisfy it by dropping
        every ``refers`` edge (see the anti-vacuity assertion below, and
        ``docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-contract-04a-enforced.md`` §3 survivor 6).

        The two derivations read DIFFERENT inputs: ``_derive_nodes`` reads the CHUNK SET
        the caller supplies, while ``_derive_edges``' reference half re-reads the FILE off
        disk (``_resolve`` calls ``evict_resolved_file`` to read it FRESH, on purpose).
        ``Indexer.index_file(tier, path, source)`` takes ``source`` from its caller, so a
        save landing between the watcher's read and the derivation's read makes the two
        disagree — and MEASURED 2026-07-26, a divergent chunk set makes
        ``build_file_graph_fragment`` emit ``refers`` RELATEs whose ``src`` code_node no
        statement ever created.

        Today those become invisible dangling edges.  After the flip they abort the whole
        file's index transaction.  **The operator ruled the ROOT fix: ``_derive_edges``
        stops re-reading, and both derivations read ONE source** — not a local patch that
        mints the missing node or drops the edge.

        The empty chunk set is the SMALLEST input that forces the divergence; it is not
        the only one, and the pin is written over the fragment's PROPERTY rather than over
        this input so any other divergence is caught too.
        """
        fragment = code_graph.build_file_graph_fragment(
            _GRAPH_TIER, _GRAPH_FILE, [], module_name=_GRAPH_MODULE
        )
        assert _relate_count(fragment) >= 1, (
            "the divergent fixture must still produce RELATEs, or it cannot discriminate "
            "a fragment that fixed the problem from one that emits nothing at all"
        )
        assert _unsatisfied_relate_endpoints(fragment) == [], (
            "build_file_graph_fragment must NEVER RELATE from an endpoint no earlier "
            "statement of the SAME fragment created: ENFORCED is checked at RELATE time, "
            "per record, and statement order IS the contract (probe §6.4 legs L5/L8). "
            "Under ENFORCED each of these aborts the whole file's index transaction"
        )

    def test_the_instrument_can_SEE_a_violation(self, code_graph: SurrealCodeGraph) -> None:
        """RUNS.  A PROBE NEEDS A CONTROL.  ``_unsatisfied_relate_endpoints`` returning
        ``[]`` is worthless until it has been shown returning something on a fragment that
        is known-inconsistent — otherwise a parser that matches no statement at all reads
        exactly like a perfectly self-consistent fragment.

        Deliberately UNSKIPPED: this is the guard on the guard, and it must not sit
        un-run for the length of packet 43's design pass.
        """
        chunks = _chunk(_GRAPH_FILE, _GRAPH_SOURCE)
        fragment = code_graph.build_file_graph_fragment(
            _GRAPH_TIER, _GRAPH_FILE, chunks, module_name=_GRAPH_MODULE
        )
        forged = type(fragment)(
            statements=[
                f"RELATE $forged_src->{REFERS_RELATION}->$forged_dst SET kind = 'calls';"
            ],
            params={
                "forged_src": RecordID(CODE_NODE_TABLE, [_GRAPH_TIER, _GRAPH_FILE, "never.made"]),
                "forged_dst": RecordID(NAME_TABLE, "also.never.made"),
            },
        )
        assert len(_unsatisfied_relate_endpoints(forged)) == 2, (
            "the instrument must report BOTH endpoints of a RELATE nothing created"
        )

    def test_the_ORDER_matters_not_merely_the_presence(
        self, code_graph: SurrealCodeGraph
    ) -> None:
        """RUNS.  The second control, and the one an unordered implementation would fail.

        Probe §6.4 leg L5: a RELATE that runs BEFORE its endpoint's CREATE is rejected
        even though the endpoint exists by COMMIT.  An instrument that collected every
        minted id first and then checked RELATEs would call that fragment fine.
        """
        chunks = _chunk(_GRAPH_FILE, _GRAPH_SOURCE)
        fragment = code_graph.build_file_graph_fragment(
            _GRAPH_TIER, _GRAPH_FILE, chunks, module_name=_GRAPH_MODULE
        )
        reversed_fragment = type(fragment)(
            statements=list(reversed(fragment.statements)), params=dict(fragment.params)
        )
        assert _unsatisfied_relate_endpoints(reversed_fragment) != [], (
            "reversing the statements must break the check — otherwise it is not "
            "statement-ordered and cannot model what ENFORCED actually enforces"
        )


class TestTheDerivationsAgreeOnSourceNames:
    """RUNS.  The narrower, DERIVATION-level statement of the same condition (probe §8
    decision 6): ``{edge.src} ⊆ {node.qualified_name}``.

    Kept live and unskipped because it LOCALISES a future failure: if the fragment pin
    above reddens, this says whether the cause is the DERIVATION disagreeing with itself
    or the fragment builder losing a statement.  It is also the pin packet 43's root fix
    must keep green — unifying the sources must not change what a matching chunk set
    derives.
    """

    def test_every_edge_src_is_a_derived_node_for_a_matching_chunk_set(
        self, graph_project: Path
    ) -> None:
        graph = CodeGraph(tier_roots={_GRAPH_TIER: graph_project}, project_roots=[graph_project])
        chunks = _chunk(_GRAPH_FILE, _GRAPH_SOURCE)
        nodes = graph._derive_nodes(_GRAPH_MODULE, chunks)  # noqa: SLF001 - derivation seam
        edges = graph._derive_edges(  # noqa: SLF001 - derivation seam
            _GRAPH_MODULE, chunks, tier=_GRAPH_TIER, file_path=_GRAPH_FILE
        )
        assert len(nodes) >= 4, f"fixture too small to discriminate: {nodes}"
        assert edges, "fixture produced no edges at all"
        missing = sorted({edge.src for edge in edges} - {node.qualified_name for node in nodes})
        assert missing == [], (
            "every reference edge's src must be a node this same file derived — "
            f"unmatched: {missing}"
        )
