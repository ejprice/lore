"""Contract tests for packet 04a — **the `ENFORCED` sweep (#105)**.

⚠ **SPLIT 2026-07-26 (operator ruling; packet 43 minted `a075e85`).**  This file originally
pinned all three deferred edges.  The ``refers`` / ``answers_to`` flip **moved to
``test_derivation_source_unification.py``** because it is blocked on a root fix that is
not 04a's: ``CodeGraph._derive_nodes`` reads the CHUNK SET while ``_derive_edges``
re-reads the FILE, and a divergence makes ``build_file_graph_fragment`` RELATE from a
``code_node`` it never created (``REPORT-contract-04a-enforced.md`` §4.D2).  A 04a builder
must be able to reach GREEN with 04a's scope alone — a permanently-RED pin is a broken
gate, and a builder facing one is a builder tempted to weaken the flip.

**04a therefore flips exactly ONE edge: ``briefed``.**  What survives the split, and how
the ∀ law survives with it, is stated in :class:`TestEveryRelationEdgeIsEnforced`.

Scope: the ``briefed`` flip, the DIRTY-STORE migration that makes it actually LAND, the
un-enforcing regression door, the negative fixtures' ghost-member reading, and the
app-level check that is the only layer able to TEACH.  **NOT in scope:** the ``blocks``
task-DAG edge, the fleet message columns, ``_comms_footer``, #219 (all packet 04b); the
code-graph edges and the derivation ∀ (packet 43).

Binding spec, in the order it must be read:

* ``docs/plans/v2/04-comms-blocks-footer.md`` — the packet, §"#105 — THE ``ENFORCED``
  SWEEP" and the 2026-07-26 operator ruling *"None of the comms package is in use.
  Change whatever."*
* ``docs/plans/v2/receipts/2026-07-26-packet04/REPORT-probe-pkt04-store.md`` — every store
  fact this file relies on, MEASURED on spike-surreal ``surrealdb-3.2.1`` 2026-07-26.
  Cited by section (§2 = P1, §3 = P2/P2b, §6 = P5, §10 = P5b).  **This file re-probes
  nothing.**
* ``docs/plans/v2/receipts/2026-07-26-packet04/REPORT-scout-pkt04-seams.md`` §S4 — the
  dirty-store pin idiom these pins clone, §S5/§S6 — the ``briefed`` exposure map.
* ``docs/reference/surrealdb-31-capabilities.md`` §1.1 (the RELATION-TABLE row), §1.2
  (``OVERWRITE`` = FULL REPLACE), §1.6 (the virgin-DB blind spot), §3 (the SDK validates
  ``statement[0]`` only), §4 (the ``ENFORCED`` adoption table), §6.4 (the vendor's
  "dangling edges read as ``[]``" claim is FALSE).

The shared migration idiom — DDL application, old-world derivation, the live-store
helpers, the edge vocabulary — lives in ``_enforced_relations_scaffold.py`` and is
IMPORTED by both this file and packet 43's, never copied into each.  Repo law (#102): if
two call sites need the same POLICY it is a FUNCTION THEY CALL.

RED-BY-DESIGN.  Against the tree at `28387a0` this file is RED, deliberately, in the pins
that describe the CHANGE — and GREEN in the ones that describe a CONTROL or a preserved
behaviour.  Which is which is stated in every class docstring, because a contract whose
author cannot say why each pin is red today has not written a contract.

⚠ **TWO PRE-EXISTING CONTRACT FILES STRUCTURALLY CONTRADICTED THIS ONE.  BOTH ARE NOW
CLOSED — recorded here because a builder meeting either mid-wave would be tempted to
weaken the flip rather than fix the fixture.**

1. ``test_brief_ledger.py`` (§4.D1, operator-ruled a NAMED 04a deliverable 2026-07-26,
   **landed `dfb5cd0`**): its ``brief_ledger_factory`` applied ``generate_brief_ddl()``
   and nothing else, so the ``agent`` table never existed there and every ``briefed``
   edge its suite wrote was a DANGLING edge.  Six functions in that file build a real
   ledger; all six now call ``_seed_agent_rows``, and that coverage is a CHECKED variable
   (``TestEveryRealLedgerSiteSeedsItsAgentRows``).
2. ``test_retry_seam.py`` (adversary §C-DEF-2, **closed 2026-07-27**): its
   ``_AckConnection`` is a DENY-BY-DEFAULT fake serving exactly ``ack()``'s two SELECTs
   and the RELATE, so the app-level existence check this contract requires inside ``ack``
   made five of its pins fail with *"the ack path issued a statement this fake does not
   serve"*.  **Operator/lead RULING: widen the fake, honestly** — it now models the
   ``agent`` table (deny-by-default preserved for every other statement) and the
   retry-seam pins it exists to catch were re-proven RED under their own mutation after
   the widening (``REPORT-contract-04a-enforced-3.md`` §3).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from typing import Any

import pytest
import pytest_asyncio
from _enforced_relations_scaffold import (
    ALL_DDL_GENERATORS,
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
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealConnection,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.briefs import BriefLedger
from loremaster.store.surreal import SurrealStoreError
from loremaster.store.surreal_schema import (
    AGENT_TABLE,
    BRIEF_COUNTER_TABLE,
    BRIEF_TABLE,
    BRIEFED_RELATION,
    MESSAGE_TABLE,
    TO_RELATION,
    generate_agent_ddl,
    generate_brief_ddl,
)
from surrealdb import RecordID

# --------------------------------------------------------------------------- #
# LAZY access to packet 04a's own additions.
#
# ⚠ CALL-TIME IMPORTS ON PURPOSE, for the SHARED unknown-agent policy module that does
# not exist yet.  A module-level import of it makes this whole file UNCOLLECTABLE at
# clean HEAD — deleting every pin below from the run — rather than RED.  Those are
# different states and the uncollectable one is the dangerous one (finding #133; the same
# note guards ``test_comms_schema.py`` and ``test_message_ledger.py``).  Every BEHAVIOURAL
# pin below is written against the EXISTING public surface and needs none of this, on
# purpose: only the two DRY pins in section E reach for it.
# --------------------------------------------------------------------------- #

#: The module the shared "reject unknown agents" policy must live in.  A NEW module rather
#: than a method on either ledger, cloning the ``loremaster.agent_ref`` precedent verbatim:
#: a ledger owning the shared object would force its sibling to import IT, reintroducing
#: exactly the coupling ``briefs.py``'s own decoupling law ("the ledger never imports its
#: neighbours") exists to prevent.
SHARED_POLICY_MODULE = "loremaster.agent_existence"

#: The name BOTH ledgers must import the shared policy under.  This IS a name-keyed handle
#: and it is here on purpose: a mutation proof needs a mutation POINT, and a mutation point
#: has a name (repo law: prove sharing by MUTATION, never by inspection).  It fails CLOSED —
#: a module missing the attribute reddens rather than silently skipping.  Renaming it is
#: legal; it costs one edit, HERE.
SHARED_POLICY_ATTR = "reject_unknown_agents"


def _shared_policy() -> Any:
    """The packet-04a shared unknown-agent policy module, imported at CALL time."""
    import importlib

    return importlib.import_module(SHARED_POLICY_MODULE)


# =========================================================================== #
# SECTION A — THE FLIP.  Offline pins over the emitted DDL.
#
# RED TODAY (2): the ∀ law (naming ``briefed``) and ``briefed``'s own slice pin.
# GREEN TODAY (10): the exact-set pin, ``to``'s regression pin, and the OVERWRITE /
# IN-OUT pins for all four edges — those hold for every edge already.
# =========================================================================== #

#: The edges packet 04a itself flips.  ONE, after the split — and the mutation proof at
#: the foot of this file declares exactly this set, because a proof still naming four
#: edges when 04a flips one is a declared-RED that stays GREEN, which is the failure
#: direction ``scripts/mutation_proof.py``'s both-ways diff exists to catch.
FLIPPED_BY_04A: tuple[tuple[str, str, str, Callable[[], str], Callable[[], str]], ...] = (
    (BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, generate_brief_ddl, generate_agent_ddl),
)
_FLIPPED_IDS = [edge[0] for edge in FLIPPED_BY_04A]


class TestEveryRelationEdgeIsEnforced:
    """#105's ruled scope: ``ENFORCED`` on every relation edge, not on a list of names.

    ``ENFORCED`` validates BOTH endpoints and guards the TABLE — including the
    ``INSERT RELATION`` door an app-level check on one verb can never reach (store
    reference §4, the adoption table's last row).

    **How the ∀ law survives the 04a/43 split.**  The obvious move — narrow the pin to the
    edges 04a flips — would turn the law back into the name list repo law forbids, and
    packet 04b's ``blocks`` edge could then arrive un-guarded with every gate green.  So
    the ∀ is kept TOTAL over the emitter's output and takes ONE deny-by-default exemption:
    ``DEFERRED_TO_PACKET_43``, a small, enumerated, ASSERTED safe-set (*allowlist the
    safe*).  Packet 43's contract pins its exact contents and empties it.  Anything NOT in
    that set must be ``ENFORCED``, today and forever.
    """

    def test_EVERY_relation_table_the_schema_emits_is_ENFORCED(self) -> None:
        """THE LAW.  ∀ over the emitted DDL, not over a name list.

        RED at `28387a0`: ``briefed`` is un-guarded and is NOT exempt.  It also pins packet
        04b's ``blocks`` edge before that edge exists — the day a fifth relation table is
        emitted un-guarded, this is what says so.
        """
        emitted = every_emitted_relation_table()
        assert emitted, "the sweep found NO relation tables at all — the parser is broken"
        unguarded = {
            edge: f"{label}: {statement}"
            for edge, (label, statement) in emitted.items()
            if not is_enforced(statement)
        }
        offenders = {
            edge: where for edge, where in unguarded.items() if edge not in DEFERRED_TO_PACKET_43
        }
        assert offenders == {}, (
            "every TYPE RELATION table this schema emits must carry ENFORCED — the only "
            "guard that validates BOTH endpoints and covers INSERT RELATION (store "
            f"reference §4). Un-guarded and NOT exempt: {offenders}. The ONLY legal "
            f"exemption is DEFERRED_TO_PACKET_43 ({sorted(DEFERRED_TO_PACKET_43)}); adding "
            "an edge to it defers a guard rather than shipping one, which is a scope "
            "decision that belongs to the operator"
        )

    def test_the_relation_edge_set_is_EXACTLY_the_four_known_edges(self) -> None:
        """An exact-set pin over the emitted edges (the house idiom).

        GREEN at `28387a0` and RED the moment packet 04b adds ``blocks`` — which is the
        point: a new edge must be ADDED to ``KNOWN_RELATION_EDGES`` with its endpoints
        stated, so the flip cannot silently miss it.
        """
        assert set(every_emitted_relation_table()) == set(KNOWN_RELATION_EDGES), (
            "the emitted relation-table set drifted from the declared set in "
            "_enforced_relations_scaffold.py — if you ADDED an edge, add it there (with its "
            "IN/OUT tables) and confirm it is ENFORCED from birth; if you REMOVED one, "
            "delete its row"
        )

    @pytest.mark.parametrize(
        ("edge", "generator_label"),
        [
            (BRIEFED_RELATION, "generate_brief_ddl"),
            (TO_RELATION, "generate_message_ddl"),
        ],
    )
    def test_the_edge_carries_ENFORCED_in_its_own_slice(
        self, edge: str, generator_label: str
    ) -> None:
        """The DECLARED-RED targets of the group-C mutation proof, for the edges 04a owns.

        ``refers``/``answers_to``'s equivalents moved to
        ``test_derivation_source_unification.py`` with the rest of packet 43.

        ``to`` is GREEN at `28387a0` (packet 03 shipped it) — a REGRESSION pin, and the
        positive control proving this assertion can pass at all.
        """
        emitted = relation_table_statements(ALL_DDL_GENERATORS[generator_label]())
        assert edge in emitted, f"{generator_label} no longer emits the {edge!r} relation table"
        assert is_enforced(emitted[edge]), f"{edge} must be declared ENFORCED: {emitted[edge]!r}"

    @pytest.mark.parametrize("edge", sorted(KNOWN_RELATION_EDGES))
    def test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS(self, edge: str) -> None:
        """GREEN at `28387a0`, for ALL FOUR edges including the two deferred ones — the
        #107-shape guard, pinned so the flip cannot arrive on a clause that never lands.

        Kept total (not narrowed to 04a's edge) because it is already true everywhere:
        narrowing a GREEN universal to match a scope split would discard live coverage for
        no reason.

        Store reference §1.1 (RELATION-TABLE row) + probe §3 LEG A, MEASURED on 3.2.1:
        ``DEFINE TABLE IF NOT EXISTS`` on an existing edge table is a SILENT NO-OP — it
        raises nothing, the stored definition is untouched, and the guard never reaches a
        live store.  ``OVERWRITE`` is the only clause that lands it.
        """
        _label, statement = every_emitted_relation_table()[edge]
        assert statement.startswith(f"DEFINE TABLE OVERWRITE {edge} "), (
            f"{edge}'s relation clause must be OVERWRITE — IF NOT EXISTS is a measured "
            f"silent no-op on an existing edge table (store reference §1.1): {statement!r}"
        )

    @pytest.mark.parametrize(("edge", "endpoints"), sorted(KNOWN_RELATION_EDGES.items()))
    def test_the_edge_declares_its_IN_and_OUT_endpoint_tables(
        self, edge: str, endpoints: tuple[str, str]
    ) -> None:
        """GREEN at `28387a0`, all four edges.  ``ENFORCED`` is meaningless without
        ``IN``/``OUT``: the clause validates that the endpoints EXIST, the typing validates
        that they are of the right TABLE, and both halves are wanted on every edge.
        """
        in_table, out_table = endpoints
        _label, statement = every_emitted_relation_table()[edge]
        assert f"IN {in_table} OUT {out_table}" in statement, (
            f"{edge} must declare IN {in_table} OUT {out_table}: {statement!r}"
        )


# =========================================================================== #
# SECTION B — THE DIRTY-STORE MIGRATION.
#
# THE TEST ENVIRONMENT IS A FICTION (repo CLAUDE.md; store reference §1.6): every test
# mints a VIRGIN database, and on a virgin database ANY clause creates the table WITH
# whatever the generator says — so a flip that never migrates is invisible to every
# offline pin and every ordinary live pin.  The flip lands on an EXISTING table.  These
# are the only pins that can see it.
#
# Shape: scout §S4's five steps, DDL applied through ``execute_transaction`` (see
# ``_enforced_relations_scaffold.apply_ddl``).
# =========================================================================== #


class TestTheOldWorldDerivationIsNotVacuous:
    """RED at `28387a0`, and it is the pin that keeps section B honest.

    Every migration pin below applies an "old" DDL and then the current one.  If the two
    are IDENTICAL the pins migrate a schema to ITSELF and test nothing at all while looking
    perfectly green.  This states that hazard as its own assertion rather than burying it
    in a helper's exception.
    """

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator"),
        [(e, i, o, g) for e, i, o, g, _ in FLIPPED_BY_04A],
        ids=_FLIPPED_IDS,
    )
    def test_the_old_world_DIFFERS_from_todays_generator(
        self, edge: str, in_table: str, out_table: str, generator: Callable[[], str]
    ) -> None:
        assert old_world_ddl(edge, in_table, out_table, generator) != generator(), (
            f"re-emitting {edge!r} with enforced=False does not change the DDL, which "
            f"means today's generator ALREADY emits it un-enforced — the flip has not "
            f"happened. Once it has, this pin passes and every migration pin below starts "
            f"testing a real old->new transition instead of a no-op."
        )


class TestTheEnforcedFlipMigratesADirtyStore:
    """THE #107 SHAPE.

    ``IF NOT EXISTS`` is a MEASURED silent no-op on an existing edge table and
    ``OVERWRITE`` is the only clause that lands the flip (probe §3 legs A/B, 3.2.1).  A
    virgin-DB fixture cannot distinguish the two: on a fresh database the table is CREATED
    with whatever the generator says, so the migration is never exercised.  These pins
    apply the OLD (un-enforced) definition, DIRTY the store with a dangling edge that is
    legal under it, then apply today's generator.

    RED at `28387a0`: ``test_the_guard_is_LIVE_…``.
    GREEN at `28387a0`: the BASELINE, positive-control, survival and idempotence legs —
    they are controls and preserved behaviours, and they must stay green after the flip.
    """

    @staticmethod
    async def _dirty_old_world(
        connection: SurrealConnection,
        env: SurrealEnv,
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> tuple[str, str]:
        """Apply the OLD world and write ONE dangling edge under it.

        Returns ``(live_in_id, ghost_out_id)`` — a real IN endpoint and an OUT endpoint
        that is verified NOT to exist.
        """
        await apply_ddl(connection, endpoint_generator(), url=env.url)
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

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator", "endpoint_generator"),
        FLIPPED_BY_04A,
        ids=_FLIPPED_IDS,
    )
    async def test_BASELINE_the_old_world_really_ACCEPTS_a_dangling_edge(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """Without this control, "the guard is live after migrating" could be true because
        it was ALWAYS live — and the migration itself never tested.

        GREEN at `28387a0` and GREEN after the flip: it describes the OLD world.
        """
        connection, env = migration_db
        _live_in, ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator, endpoint_generator
        )
        rows = await run(connection, f"SELECT id FROM {edge}")
        assert rows, (
            f"the OLD (un-enforced) {edge} definition was supposed to ACCEPT a RELATE to "
            f"the non-existent {out_table}:{ghost_out} — if it did not, this fixture is not "
            f"installing the old world and every leg below is measuring the wrong transition"
        )

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator", "endpoint_generator"),
        FLIPPED_BY_04A,
        ids=_FLIPPED_IDS,
    )
    async def test_the_guard_is_LIVE_after_applying_todays_ddl_to_a_DIRTY_store(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """RED at `28387a0`.  THE load-bearing pin of packet 04a.

        A definition that emits perfectly and never LANDS is invisible to every offline
        pin — this is the leg that catches it.  The rejection is demanded BEHAVIOURALLY (a
        new dangling RELATE is refused), never by reading back a stored DDL string: probe
        §3 leg A records that a stored-DDL diff alone could be a rendering artifact, so the
        behavioural confirmation is the measurement.
        """
        connection, env = migration_db
        live_in, _ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator, endpoint_generator
        )
        await apply_ddl(connection, generator(), url=env.url)

        fresh_ghost = ghost_id("still_absent")
        assert not await record_exists(connection, out_table, fresh_ghost)
        with pytest.raises(Exception):  # noqa: B017 - the engine's NotFoundError surface
            await relate(
                connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
                out_id=fresh_ghost,
            )

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator", "endpoint_generator"),
        FLIPPED_BY_04A,
        ids=_FLIPPED_IDS,
    )
    async def test_POSITIVE_CONTROL_a_REAL_endpoint_is_still_accepted_after_the_flip(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """The control the rejection pin needs: a guard that refuses EVERYTHING is not a
        guard, it is an outage.

        GREEN at `28387a0` (nothing rejects today) and it must STAY green after the flip —
        which is exactly what makes it a control rather than decoration.
        """
        connection, env = migration_db
        live_in, _ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator, endpoint_generator
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

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator", "endpoint_generator"),
        FLIPPED_BY_04A,
        ids=_FLIPPED_IDS,
    )
    async def test_the_PRE_EXISTING_dangling_edge_SURVIVES_the_flip(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """GREEN today and after: probe §3 P2b, MEASURED on 3.2.1 — the flip succeeds with
        a dangling row present and there is NO validation sweep over existing rows.

        Pinned because the opposite belief is the attractive one: "we turned ENFORCED on,
        so the ghosts are gone."  They are not.  Store reference §4: *turning it on and
        calling the ghost problem closed is a FALSE ALL-CLEAR* — cleanup is a separate data
        migration, ruled OUT of this packet as #236.
        """
        connection, env = migration_db
        _live_in, ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator, endpoint_generator
        )
        before = await run(connection, f"SELECT id FROM {edge}")
        await apply_ddl(connection, generator(), url=env.url)
        after = await run(
            connection,
            f"SELECT id, out FROM {edge} WHERE out = $out",
            {"out": RecordID(out_table, ghost_out)},
        )
        assert len(before) == 1, "fixture: exactly one dangling edge should exist pre-flip"
        assert after, (
            "the pre-existing dangling edge must SURVIVE the flip — ENFORCED is a "
            "write-path guard, not a retro-validation (probe §3 P2b)"
        )

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator", "endpoint_generator"),
        FLIPPED_BY_04A,
        ids=_FLIPPED_IDS,
    )
    async def test_the_migration_is_IDEMPOTENT_on_an_already_migrated_store(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """GREEN today and after.  ``ensure_ready`` re-applies this DDL on EVERY boot, so a
        second and third apply must be a clean no-op that neither raises nor loses the
        guard.
        """
        connection, env = migration_db
        live_in, _ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator, endpoint_generator
        )
        for _ in range(3):
            await apply_ddl(connection, generator(), url=env.url)

        live_out = ghost_id("live_out")
        await seed_endpoint(connection, out_table, live_out)
        await relate(
            connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
            out_id=live_out,
        )


class TestTheLEDGERsOwnMigrationPathLandsTheGuard:
    """⛔ **THE PIN THAT KILLS W-A** — the #107 shape, in the packet written to prevent it.

    Every pin in section B applies the DDL ITSELF
    (``apply_ddl(connection, generator(), url=env.url)``).  That proves the **RECIPE**
    migrates.  It cannot prove the **CAKE** does — and ``BriefLedger.ensure_ready()`` is the
    SOLE path by which production ever migrates this table.  MEASURED (adversary §P1 W-A,
    2026-07-26/27): a build whose emitter is perfectly correct and whose ``ensure_ready``
    de-enforces the DDL on its way to the store
    (``generate_brief_ddl().replace(" ENFORCED SCHEMAFULL", " SCHEMAFULL")``) passed this
    contract **38/38 with ZERO new failures repo-wide**.

    So this leg drives the LEDGER's own migration path and nothing else: the old world is
    installed by hand, the store is dirtied, and then the ONLY step is ``ensure_ready()``.
    Nothing here applies DDL on the ledger's behalf.

    RED at `369db57`: the guard does not exist yet, so the fresh dangling RELATE is accepted.
    """

    @staticmethod
    def _ledger_on(env: SurrealEnv) -> BriefLedger:
        return BriefLedger(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )

    @staticmethod
    async def _old_world_with_a_dangling_edge(
        connection: SurrealConnection, env: SurrealEnv
    ) -> str:
        """Install the OLD (un-enforced) ``briefed`` world and dirty it.  Returns a REAL
        agent id that exists on this database."""
        await apply_ddl(connection, generate_agent_ddl(), url=env.url)
        await apply_ddl(
            connection,
            old_world_ddl(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, generate_brief_ddl),
            url=env.url,
        )
        live_agent = ghost_id("live_agent")
        await seed_endpoint(connection, AGENT_TABLE, live_agent)
        ghost_brief = ghost_id("ghost_brief")
        assert not await record_exists(connection, BRIEF_TABLE, ghost_brief)
        await relate(
            connection, BRIEFED_RELATION, in_table=AGENT_TABLE, in_id=live_agent,
            out_table=BRIEF_TABLE, out_id=ghost_brief,
        )
        rows = await run(connection, f"SELECT id FROM {BRIEFED_RELATION}")
        assert len(rows) == 1, (
            "the OLD world must ACCEPT the dangling edge — otherwise this fixture is not "
            "installing the world whose migration is under test"
        )
        return live_agent

    async def test_ensure_ready_on_a_DIRTY_store_makes_the_guard_LIVE(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = migration_db
        live_agent = await self._old_world_with_a_dangling_edge(connection, env)

        ledger = self._ledger_on(env)
        try:
            await ledger.ensure_ready()  # THE ONLY migration step. Nothing else runs DDL.
        finally:
            await ledger.close()

        fresh_ghost = ghost_id("still_absent")
        assert not await record_exists(connection, BRIEF_TABLE, fresh_ghost)
        with pytest.raises(Exception):  # noqa: B017 - the engine's NotFoundError surface
            await relate(
                connection, BRIEFED_RELATION, in_table=AGENT_TABLE, in_id=live_agent,
                out_table=BRIEF_TABLE, out_id=fresh_ghost,
            )

    async def test_POSITIVE_CONTROL_ensure_ready_still_accepts_two_REAL_endpoints(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
    ) -> None:
        """A migration that refuses EVERYTHING is not a guard, it is an outage — and it
        would satisfy the pin above.  GREEN today and after the flip.
        """
        connection, env = migration_db
        live_agent = await self._old_world_with_a_dangling_edge(connection, env)

        ledger = self._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()

        live_brief = ghost_id("live_brief")
        await seed_endpoint(connection, BRIEF_TABLE, live_brief)
        await relate(
            connection, BRIEFED_RELATION, in_table=AGENT_TABLE, in_id=live_agent,
            out_table=BRIEF_TABLE, out_id=live_brief,
        )
        rows = await run(
            connection,
            f"SELECT id FROM {BRIEFED_RELATION} WHERE out = $out",
            {"out": RecordID(BRIEF_TABLE, live_brief)},
        )
        assert rows, (
            "after the LEDGER's own migration a briefed RELATE between two REAL endpoints "
            "must still be accepted"
        )


# =========================================================================== #
# SECTION C — THE UN-ENFORCING DOOR (probe §3 item (a)).
#
# ``DEFINE TABLE OVERWRITE`` is FULL REPLACE for ``ENFORCED`` too: a re-emission that
# omits the keyword silently un-guards the table.  §1.2 states full-replace for
# ``ASSERT``; §4 does NOT state it for ``ENFORCED``, and this is a LIVE regression door —
# a DDL generator change, a copy-paste, or a new table-recreate path drops the guard with
# zero error and zero test signal ON A VIRGIN DB.
# =========================================================================== #


class TestTheUnEnforcingDoor:
    """The hazard, pinned so the next author meets it DELIBERATELY.

    Repo law, WHEN YOU CANNOT CLOSE A HOLE, PIN IT: this door cannot be closed —
    ``OVERWRITE`` full-replace is the engine's semantics and the very thing that makes the
    flip land.  What CAN be done is make it impossible to walk through unnoticed: the ∀ pin
    in section A refuses an un-enforced emission at the source, and the leg below
    demonstrates the mechanism live so nobody has to rediscover it from an outage.
    """

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator", "endpoint_generator"),
        FLIPPED_BY_04A,
        ids=_FLIPPED_IDS,
    )
    async def test_re_emitting_the_edge_WITHOUT_ENFORCED_silently_un_guards_it(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """RED at `28387a0` — it cannot reach its own subject until the guard exists.

        Three legs in order, and the middle one is the control that makes the third
        meaningful: (1) today's DDL guards; (2) an ``OVERWRITE`` without ``ENFORCED``
        raises nothing at all; (3) the dangling RELATE it refused a moment ago is accepted
        again.
        """
        connection, env = migration_db
        await apply_ddl(connection, endpoint_generator(), url=env.url)
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

        # The door: a full-replace re-emission that simply omits the keyword.
        await apply_ddl(connection, unenforced_ddl(edge, in_table, out_table), url=env.url)

        await relate(
            connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
            out_id=ghost_out,
        )
        rows = await run(connection, f"SELECT id FROM {edge}")
        assert rows, (
            "MEASURED (probe §3 item (a)): DEFINE TABLE OVERWRITE omitting ENFORCED "
            "silently un-guards the table. If this assertion ever fails, the engine's "
            "full-replace semantics changed and the ∀ pin in section A is no longer the "
            "only thing standing between a re-emission and a re-opened #105"
        )


# =========================================================================== #
# SECTION D — THE GHOST-MEMBER READING (probe §2 / store reference §6.4).
#
# The vendor says a dangling edge makes "a query on the relation return an empty array".
# That is FALSE as a reader would apply it, on 3.1.5 AND re-confirmed on 3.2.1: the
# identity traversal returns the ghost as a FIRST-CLASS MEMBER.  A negative pin written to
# the vendor's sentence would be GREEN on a build that never wrote the edge at all.
# =========================================================================== #


class TestADanglingEdgeReadsAsAFirstClassMember:
    """GREEN today and after the flip — an ENGINE reading, pinned because getting it
    backwards silently inverts every negative fixture in this file.

    Also the reason ``ENFORCED`` matters independently of provenance (probe §2, NEW):
    ``array::len`` over a traversal COUNTS the ghost, so any served per-agent or
    per-message count computed from a traversal over an un-guarded edge over-reports,
    silently.  That is a TRUST-DOCTRINE surface.
    """

    async def test_the_traversal_lists_the_ghost_and_NOT_an_empty_array(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = migration_db
        await apply_ddl(connection, generate_agent_ddl(), url=env.url)
        await apply_ddl(
            connection,
            old_world_ddl(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, generate_brief_ddl),
            url=env.url,
        )
        agent_id = ghost_id("live_agent")
        await seed_endpoint(connection, AGENT_TABLE, agent_id)
        ghost_brief = ghost_id("ghost_brief")
        assert not await record_exists(connection, BRIEF_TABLE, ghost_brief)
        await relate(
            connection, BRIEFED_RELATION, in_table=AGENT_TABLE, in_id=agent_id,
            out_table=BRIEF_TABLE, out_id=ghost_brief,
        )

        rows = await run(
            connection,
            f"SELECT ->{BRIEFED_RELATION}->{BRIEF_TABLE} AS briefs FROM $agent",
            {"agent": RecordID(AGENT_TABLE, agent_id)},
        )
        assert len(rows) == 1
        briefs = rows[0]["briefs"]
        assert len(briefs) == 1, (
            "store reference §6.4 / probe §2: a dangling edge is a FIRST-CLASS MEMBER of "
            "the identity traversal on 3.2.1. The vendor's 'returns an empty array' "
            f"sentence is FALSE, and a pin written to it would pass on a build that never "
            f"wrote the edge at all. Got: {briefs!r}"
        )
        assert str(briefs[0]).endswith(ghost_brief), (
            f"the traversal must name the ghost itself, not some other row: {briefs!r}"
        )

    async def test_POSITIVE_CONTROL_a_node_with_NO_edges_really_does_yield_an_empty_array(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
    ) -> None:
        """The control that makes the pin above a real negative rather than a blind
        instrument: ``[]`` IS producible by this exact query shape, so the ghost-only row
        returning a member is evidence, not noise.

        Probe §2 records that this probe's ancestor reported the OPPOSITE of the truth on
        its first run and ONLY the control caught it.
        """
        connection, env = migration_db
        await apply_ddl(connection, generate_agent_ddl(), url=env.url)
        await apply_ddl(
            connection,
            old_world_ddl(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, generate_brief_ddl),
            url=env.url,
        )
        lonely = ghost_id("lonely_agent")
        await seed_endpoint(connection, AGENT_TABLE, lonely)
        rows = await run(
            connection,
            f"SELECT ->{BRIEFED_RELATION}->{BRIEF_TABLE} AS briefs FROM $agent",
            {"agent": RecordID(AGENT_TABLE, lonely)},
        )
        assert rows[0]["briefs"] == [], (
            "an edge-less row must yield [] — without this the ghost-member pin cannot "
            "distinguish 'the ghost was listed' from 'this query never returns []'"
        )


# =========================================================================== #
# SECTIONS E–H — THE APP-LEVEL CHECK.
#
# ⚠⚠ ``ENFORCED`` ALONE CANNOT SATISFY THE PACKET'S OWN EXIT CRITERION (probe §10.5,
# MEASURED).  What a caller actually receives from an ENFORCED rejection is ``statement N
# of M was rejected (unspecified rejection); see the server log`` — the engine's ``The
# record 'agent:x' does not exist`` is deliberately withheld by the seam's error-message
# hygiene (ledger #31).  "A bogus-recipient publish/send TEACHES instead of dangling" is
# therefore UNREACHABLE via the engine guard: the app-level check is the ONLY layer that
# can teach.  It is REQUIRED, not garnish.
#
# ONE IMPLEMENTATION (repo law, #102): ``send`` and ``publish`` need the SAME policy —
# "resolve these agent ids against the agent table; refuse, naming every missing one,
# BEFORE any write" — so it is a FUNCTION THEY CALL, never a pattern ``briefs.py`` clones
# from ``MessageLedger._reject_unknown_recipients``.
# =========================================================================== #

#: An agent id no fixture below ever registers.
UNREGISTERED_AGENT_ID = "unregistered_agent_0000000000000000"

#: A SECOND unregistered identity, and the reason it exists (adversary §P1 W-B, MEASURED
#: 2026-07-26/27): with ONE literal on every negative leg, a "policy" that never queries the
#: store at all — ``unknown = {id for id in agents if id == "unregistered_agent_0000…"}`` —
#: passed this whole file 38/38.  A single-literal negative fixture is a MONOCULTURE, and the
#: perturbation pair (§P2: swapping this literal reddened four pins on that wrong build)
#: proved the fixture VALUE was what blinded the contract.
#:
#: This one deliberately wears the REGISTERED shape — ``registered_agent_`` + 32 hex, exactly
#: the shape :func:`brief_ledger_with_a_real_agent` mints for the identity that DOES exist —
#: so a refusal keyed on a prefix, a literal, a length, or "looks unregistered" accepts it.
#: The 32 zeros cannot collide with a ``uuid4().hex``.  The fixture ASSERTS both ids absent.
UNREGISTERED_AGENT_ID_WEARING_THE_REGISTERED_SHAPE = (
    "registered_agent_00000000000000000000000000000000"
)

#: Every negative agent identity, as a parametrisation.  FIXTURES MUST DISCRIMINATE: if the
#: code can branch on a value, at least one pin must use a DIFFERENT value.
UNREGISTERED_AGENT_IDS = (
    UNREGISTERED_AGENT_ID,
    UNREGISTERED_AGENT_ID_WEARING_THE_REGISTERED_SHAPE,
)

_BRIEF_NAME = "project"
_BRIEF_BODY = "the standing law"
_PUBLISHER = "lead"


@pytest_asyncio.fixture()
async def brief_ledger_with_a_real_agent() -> AsyncIterator[tuple[BriefLedger, str, SurrealEnv]]:
    """A REAL :class:`BriefLedger` on a database where the ``agent`` table exists and holds
    exactly ONE registered row.

    Deliberately NOT ``test_brief_ledger.py``'s ``brief_ledger_factory``: that fixture
    applies ``generate_brief_ddl()`` alone, so the ``agent`` table never exists there and
    every ``briefed`` edge it writes is a dangling edge (this module's docstring, ⚠).  A
    fixture that guarantees the one condition under which the bug is invisible is exactly
    what THE TEST ENVIRONMENT IS A FICTION warns about — so this one guarantees the
    opposite: a real registered agent AND a genuinely absent one, in the same database, so
    the positive and negative legs share a fixture and neither can pass for a fixture
    reason.

    ⚠ The agent slice is applied FIRST.  After the flip ``briefed`` is ``IN agent …
    ENFORCED``, which makes ``generate_brief_ddl`` ORDER-DEPENDENT on
    ``generate_agent_ddl`` in a way it has never been —
    :class:`TestTheBriefSliceIsOrderDependentOnTheAgentSlice` pins that consequence.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup = await connect_admin(env)
    registered_id = f"registered_agent_{uuid.uuid4().hex}"
    try:
        await apply_ddl(setup, generate_agent_ddl(), url=env.url)
        await seed_endpoint(setup, AGENT_TABLE, registered_id)
        for absent_id in UNREGISTERED_AGENT_IDS:
            assert not await record_exists(setup, AGENT_TABLE, absent_id), (
                f"the negative fixture's agent id {absent_id!r} must genuinely NOT exist"
            )
    finally:
        await setup.close()

    ledger = BriefLedger(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await ledger.ensure_ready()
    try:
        yield ledger, registered_id, env
    finally:
        await ledger.close()
        await drop_database(env)


async def _brief_rows(ledger: BriefLedger, name: str) -> list[Any]:
    """Every stored ``brief`` row under ``name`` — a RAW read.

    Raw, because the question these pins ask is "did a row land at all", and the public
    readers raise or filter rather than answering it.
    """
    rows = await ledger._query(  # noqa: SLF001 - the raw-read seam the atomicity pins need
        f"SELECT id FROM {BRIEF_TABLE} WHERE name = $name", {"name": name}
    )
    return list(rows) if isinstance(rows, list) else []


async def _briefed_edge_count(ledger: BriefLedger) -> int:
    """The total ``briefed`` edge count — a RAW read that SEES orphan edges.

    ``acked_version``'s edge->brief join cannot: it drops a dangling target silently, which
    is the very defect #105 is about.  Cloned in intent from
    ``test_brief_ledger.py::_edge_count``.
    """
    rows = await ledger._query(  # noqa: SLF001 - see above
        f"SELECT count() FROM {BRIEFED_RELATION} GROUP ALL"
    )
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


async def _version_counter_rows(ledger: BriefLedger) -> list[Any]:
    """Every stored ``brief_counter`` row — a RAW read of the hot MINT row itself.

    ROW EXISTENCE is the discriminator the version NUMBER is not.  ``publish`` mints off
    this row with an ``UPSERT`` **before** the CREATE, so a build that mints first, lets the
    write be rejected, and hands the number back via ``_release_version`` leaves the row
    BEHIND at ``next = 0`` — and the next real publish still gets v1.  "The next publish got
    v1" is therefore true of BOTH a refused-early build and a minted-then-released one
    (adversary §P1 W-D / §P2 leg 2b, MEASURED); "no counter row exists at all" is true of
    only the first.
    """
    rows = await ledger._query(  # noqa: SLF001 - see above
        f"SELECT id FROM {BRIEF_COUNTER_TABLE}"
    )
    return list(rows) if isinstance(rows, list) else []


class TestPublishRefusesAnUnregisteredAgent:
    """RED at `28387a0`, all four legs — today ``publish`` writes the brief AND a dangling
    ack edge for an agent that does not exist (probe §10.2 leg A, MEASURED).

    THE QUANTIFIER LAW.  ``publish``'s ``agent_id`` has exactly THREE input classes and
    each one's fate is FORCED by its own fixture below — unregistered (refused), registered
    (written), ``None`` (accepted, no edge).  Not "no silent dangle on a bad id": every
    input, its stated fate.
    """

    @pytest.mark.parametrize("unregistered_agent_id", UNREGISTERED_AGENT_IDS)
    async def test_an_UNREGISTERED_agent_id_is_REFUSED(
        self,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
        unregistered_agent_id: str,
    ) -> None:
        ledger, _registered, _env = brief_ledger_with_a_real_agent
        with pytest.raises(Exception) as caught:  # noqa: B017 - the type is section E's job
            await ledger.publish(
                _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=unregistered_agent_id
            )
        assert not isinstance(caught.value, SurrealStoreError), (
            "the refusal must come from the APP-LEVEL check, not from the engine: an "
            "ENFORCED rejection reaches the caller as 'statement N of M was rejected "
            "(unspecified rejection); see the server log' (probe §10.5), which cannot "
            "satisfy this packet's Exit criterion that a bogus publish TEACHES"
        )

    @pytest.mark.parametrize("unregistered_agent_id", UNREGISTERED_AGENT_IDS)
    async def test_the_refusal_NAMES_the_bad_agent_id(
        self,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
        unregistered_agent_id: str,
    ) -> None:
        """The whole point of the app layer.  ``ENFORCED`` reports ONE bad endpoint, as
        untyped prose, only AFTER the write is attempted (store reference §4,
        error-ergonomics row) — and the seam withholds even that.  A refusal that does not
        name the offending id has taught the caller nothing.
        """
        ledger, _registered, _env = brief_ledger_with_a_real_agent
        with pytest.raises(Exception) as caught:  # noqa: B017
            await ledger.publish(
                _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=unregistered_agent_id
            )
        assert unregistered_agent_id in str(caught.value), (
            f"the refusal must name the offending agent id: {str(caught.value)!r}"
        )

    async def test_the_refused_publish_writes_NO_brief_row(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """RED at `28387a0` for the interesting reason: today the brief IS written (probe
        §10.2 leg A) and a dangling ack edge lands beside it.

        Note what this does NOT settle.  After the flip, ``ENFORCED`` alone would ALSO
        leave no brief row — but by ROLLING IT BACK after attempting the write (§10.2 leg
        B: ``SELECT id FROM brief WHERE id = brief:b_lost`` -> ``[]``).  "No row afterwards"
        cannot tell refused-early from rolled-back-late; the version pin below is what does.
        """
        ledger, _registered, _env = brief_ledger_with_a_real_agent
        with pytest.raises(Exception):  # noqa: B017
            await ledger.publish(
                _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=UNREGISTERED_AGENT_ID
            )
        assert await _brief_rows(ledger, _BRIEF_NAME) == []
        assert await _briefed_edge_count(ledger) == 0, (
            "a refused publish must leave NO ack edge — a dangling ack is a receipt for an "
            "agent that does not exist, which is finding #105 itself"
        )

    async def test_the_refusal_happens_BEFORE_the_version_is_minted(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """THE discriminator between "refused early" and "rolled back late".

        ``publish`` mints its version off the per-name counter hot row BEFORE the CREATE,
        and hands it back via ``_release_version`` when the write is rejected — a
        compensating path that is BEST-EFFORT and swallows its own failures.  An app check
        that runs first never enters that path at all, so the next real publish gets v1.  A
        build that merely lets ``ENFORCED`` reject would take the release path and this pin
        would still see v1 only if the release succeeded; forcing the check upstream
        removes the question.
        """
        ledger, registered, _env = brief_ledger_with_a_real_agent
        with pytest.raises(Exception):  # noqa: B017
            await ledger.publish(
                _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=UNREGISTERED_AGENT_ID
            )
        result = await ledger.publish(
            _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=registered
        )
        assert result.brief.version == 1, (
            "a publish refused by the app-level check must burn no version at all — it "
            f"never reached the mint. Got v{result.brief.version}"
        )


class TestPublishWithARegisteredAgentStillWorks:
    """THE POSITIVE CONTROL, without which every pin above passes on a build that refuses
    EVERYTHING.

    GREEN at `28387a0` — but not for the right reason: today it passes because nothing is
    checked at all.  After the flip it passes because the agent genuinely resolves.  A pin
    can be green in both worlds and still be load-bearing; what it forbids is the wrong
    build BETWEEN them.
    """

    async def test_a_REGISTERED_agent_id_writes_the_brief_AND_the_ack_edge(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        ledger, registered, _env = brief_ledger_with_a_real_agent
        result = await ledger.publish(
            _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=registered
        )
        assert result.brief.version == 1
        assert len(await _brief_rows(ledger, _BRIEF_NAME)) == 1
        assert await _briefed_edge_count(ledger) == 1, (
            "the author's self-ack edge must still be written for a REAL agent"
        )
        acked = await ledger.acked_version(agent_id=registered, name=_BRIEF_NAME)
        assert acked == 1

    async def test_agent_id_None_is_ACCEPTED_and_writes_no_edge(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """The third input class.  ``None`` means "a ledger-level caller with no agent row
        in play" and must stay a legal, edge-free publish — a check that refused it would
        break the ~50 call sites that pass no ``agent_id`` at all, and would be the
        quantifier law violated in the other direction (an invariant conditioned on the
        failure mode that prompted the work).
        """
        ledger, _registered, _env = brief_ledger_with_a_real_agent
        result = await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER)
        assert result.brief.version == 1
        assert await _briefed_edge_count(ledger) == 0


class TestARefusedAgentIdReachesNoWritePathAtAll:
    """§F/§G — **the pins that kill W-D**, the wrong build that is GREENER repo-wide than the
    correct one (adversary §P1: 2 failed / 2077 passed vs the correct build's 6 / 2073).

    W-D checks AFTER the write instead of before: ``publish`` mints, writes, and lets the
    engine's ``ENFORCED`` rejection arrive through ``_release_version``; ``ack`` has no
    upstream check at all, so the rejection lands in ``_relate_briefed``'s
    ``except SurrealStoreError`` — the IDEMPOTENT-RE-ACK signal — and the app error is
    manufactured from inside that handler.  It survived the contract 38/38 because the two
    properties that forbid it were stated in DOCSTRINGS and asserted nowhere:

    * *"the refusal happens BEFORE the version is minted"* — observed only as "the next
      publish gets v1", which a mint-then-release build also satisfies.  Closed by
      :meth:`test_a_refused_publish_never_TOUCHES_the_version_counter_row`.
    * *"two distinct failure modes must not share one except clause"* — the class docstring
      below states it outright and no assertion in that class checks it.  Closed by
      :meth:`test_a_refused_ack_never_ATTEMPTS_the_RELATE`.

    A message that promises a check the assertion does not perform is a FALSE GATE (repo
    law); these two convert the prose into assertions.

    RED at `369db57`: today neither verb refuses anything, so both legs reach the write.
    """

    async def test_a_refused_publish_never_TOUCHES_the_version_counter_row(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """MINT-THEN-RELEASE leaves the hot row behind; refused-early never creates it."""
        ledger, _registered, _env = brief_ledger_with_a_real_agent
        with pytest.raises(Exception):  # noqa: B017
            await ledger.publish(
                _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=UNREGISTERED_AGENT_ID
            )
        assert await _version_counter_rows(ledger) == [], (
            f"a publish refused by the app-level check must never reach the MINT — the "
            f"{BRIEF_COUNTER_TABLE} row exists, so this build minted a version, attempted "
            f"the write, and handed the number back through the best-effort compensating "
            f"path (_release_version). That path SWALLOWS its own failures: it is the "
            f"difference between 'refused' and 'rolled back, we think'"
        )

    async def test_POSITIVE_CONTROL_an_ACCEPTED_publish_DOES_create_the_counter_row(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """Without this, the pin above passes on a build where the counter row is never
        created by ANY publish — i.e. on an instrument that cannot see the row at all.
        """
        ledger, registered, _env = brief_ledger_with_a_real_agent
        await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=registered)
        assert len(await _version_counter_rows(ledger)) == 1, (
            f"an ACCEPTED publish must leave exactly one {BRIEF_COUNTER_TABLE} row — if it "
            f"does not, the read above cannot distinguish 'never minted' from 'never visible'"
        )

    async def test_a_refused_ack_never_ATTEMPTS_the_RELATE(
        self,
        monkeypatch: pytest.MonkeyPatch,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
    ) -> None:
        """§G's own class docstring, converted from prose into an assertion.

        A sentinel replaces ``_relate_briefed`` entirely, so *reaching* the RELATE is
        OBSERVABLE rather than inferred from an error type: a build whose unknown-agent
        refusal is manufactured inside that method's ``except`` raises the sentinel and goes
        RED here.  The error TYPE alone cannot see it — W-D raises an app error with the id
        in it, from inside the shared catch.
        """

        class _RelateAttempted(RuntimeError):
            """Raised INSTEAD of the RELATE — never by any upstream refusal."""

        async def _sentinel(**_kwargs: Any) -> tuple[bool, str]:
            raise _RelateAttempted("the ack path reached the briefed RELATE")

        ledger, registered, _env = brief_ledger_with_a_real_agent
        await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=registered)
        monkeypatch.setattr(ledger, "_relate_briefed", _sentinel, raising=True)

        with pytest.raises(Exception) as caught:  # noqa: B017
            await ledger.ack(
                agent_id=UNREGISTERED_AGENT_ID,
                agent_name="ghost",
                name=_BRIEF_NAME,
                version=1,
                via="explicit",
            )
        assert not isinstance(caught.value, _RelateAttempted), (
            "the ack path ATTEMPTED the briefed RELATE for an agent that does not exist. "
            "The refusal must happen upstream: an engine rejection arriving in "
            "_relate_briefed's `except SurrealStoreError` shares its catch with the "
            "IDEMPOTENT-RE-ACK signal, and two distinct failure modes separated only by a "
            "follow-up read is the hazard this packet exists to close"
        )
        assert UNREGISTERED_AGENT_ID in str(caught.value), (
            f"the upstream refusal must still NAME the bad id: {str(caught.value)!r}"
        )

    async def test_POSITIVE_CONTROL_a_REGISTERED_agents_ack_DOES_reach_the_RELATE(
        self,
        monkeypatch: pytest.MonkeyPatch,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
    ) -> None:
        """The control the sentinel pin needs, and it is not decoration: without it, a run
        where the monkeypatch silently failed to attach — or a build that refuses EVERY ack
        upstream — passes the pin above for a reason that has nothing to do with the
        property.  Here the sentinel MUST fire.
        """

        class _RelateAttempted(RuntimeError):
            """Raised INSTEAD of the RELATE — never by any upstream refusal."""

        async def _sentinel(**_kwargs: Any) -> tuple[bool, str]:
            raise _RelateAttempted("the ack path reached the briefed RELATE")

        ledger, registered, _env = brief_ledger_with_a_real_agent
        await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=registered)
        monkeypatch.setattr(ledger, "_relate_briefed", _sentinel, raising=True)

        with pytest.raises(_RelateAttempted):
            await ledger.ack(
                agent_id=registered,
                agent_name="fixer-b",
                name=_BRIEF_NAME,
                version=1,
                via="explicit",
            )


class TestTheIdempotentReAckSignalIsNotConfusedWithAnUnknownAgent:
    """§G — the SHARED-CATCH hazard, and the reason this section demands the app check run
    UPSTREAM rather than merely alongside.

    ``BriefLedger._relate_briefed`` catches ``SurrealStoreError`` as its IDEMPOTENT-RE-ACK
    SIGNAL: a ``UNIQUE(in, out)`` rejection means "already acked", disambiguated only by a
    follow-up read.  After the flip an ``ENFORCED`` rejection arrives through that SAME
    ``except``, leaving two distinct failure modes sharing one catch (probe §9, READ from
    source).  Today the follow-up read happens to re-raise correctly — but "happens to" is
    not a contract, and the operator's no-consumers ruling explicitly invites reshaping the
    seam so the two modes stop sharing a catch at all.

    RED at `28387a0`: today neither call refuses anything.
    """

    @pytest.mark.parametrize("unregistered_agent_id", UNREGISTERED_AGENT_IDS)
    async def test_an_ack_by_an_UNREGISTERED_agent_is_REFUSED_and_never_already_acked(
        self,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
        unregistered_agent_id: str,
    ) -> None:
        ledger, registered, _env = brief_ledger_with_a_real_agent
        await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=registered)
        with pytest.raises(Exception) as caught:  # noqa: B017
            await ledger.ack(
                agent_id=unregistered_agent_id,
                agent_name="ghost",
                name=_BRIEF_NAME,
                version=1,
                via="explicit",
            )
        assert unregistered_agent_id in str(caught.value)
        assert not isinstance(caught.value, SurrealStoreError), (
            "an unknown agent must be refused by the app check, never surface as the raw "
            "store rejection the idempotent-re-ack handler also catches — two distinct "
            "failure modes must not share one except clause"
        )

    async def test_POSITIVE_CONTROL_a_REGISTERED_agents_re_ack_is_still_already_acked(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """The control that keeps the pin above from being satisfied by breaking
        idempotence: the re-ack SIGNAL must still work for a real agent.

        GREEN today and after — a preserved behaviour, adjudicated ``preserved-with-pin``
        in the removed-behaviour inventory.
        """
        ledger, registered, _env = brief_ledger_with_a_real_agent
        await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=registered)
        again = await ledger.ack(
            agent_id=registered,
            agent_name="fixer-b",
            name=_BRIEF_NAME,
            version=1,
            via="explicit",
        )
        assert again.already_acked is True
        assert again.via == "publish", (
            "first-write-wins: the self-ack's via must survive a later explicit re-ack"
        )
        assert await _briefed_edge_count(ledger) == 1, "a re-ack must not create a second edge"


class TestTheBriefSliceIsOrderDependentOnTheAgentSlice:
    """A consequence of the flip that NOTHING in the packet text names, surfaced rather
    than judged.

    ``_message_statements``'s docstring records that its slice is *"applied AFTER
    generate_agent_ddl in every consumer, so agent exists for the edge's OUT agent"*.
    ``generate_brief_ddl``'s does not — because until the flip it did not need to.
    Production already orders them correctly (``server.py``: ``agent_registry`` ->
    ``brief_ledger`` -> ``message_ledger``), so this is a pin on a property that HOLDS,
    stated so a later reordering is a RED test rather than a silent 100% failure of
    ``brief_publish``.

    RED at `28387a0`: an un-enforced ``briefed`` accepts the RELATE regardless of whether
    ``agent`` exists, so the "guard is live" half cannot be shown yet.
    """

    async def test_a_brief_slice_applied_WITHOUT_the_agent_slice_still_guards(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811 - imported fixture
    ) -> None:
        connection, env = migration_db
        await apply_ddl(connection, generate_brief_ddl(), url=env.url)
        ghost_agent = ghost_id("ghost_agent")
        ghost_brief = ghost_id("ghost_brief")
        with pytest.raises(Exception):  # noqa: B017
            await relate(
                connection, BRIEFED_RELATION, in_table=AGENT_TABLE, in_id=ghost_agent,
                out_table=BRIEF_TABLE, out_id=ghost_brief,
            )


class TestTheUnknownAgentPolicyHasONEHome:
    """§E — ONE IMPLEMENTATION, proved by MUTATION and not by inspection.

    ``MessageLedger._reject_unknown_recipients`` already implements this policy for
    ``send``; ``briefs.py`` has none.  Writing a second copy is the #102 shape verbatim — a
    doc naming one method as "the reference pattern" got its bug faithfully cloned into a
    sibling.  So the policy is EXTRACTED to :data:`SHARED_POLICY_MODULE` and both ledgers
    CALL it.

    ⚠ ROUTING IS NOT SHARING.  A build where both modules import the shared symbol but each
    hand-rolls the decision underneath it passes every "did you call the driver" check.  The
    mutation pin below is the only one that can tell the difference: it replaces the shared
    function and demands BOTH verbs change behaviour.  A caller that stays working is a
    private copy wearing the shared name.

    RED at `28387a0`: the module does not exist.
    """

    def test_the_shared_policy_module_exists_and_exports_the_policy(self) -> None:
        policy = _shared_policy()
        assert hasattr(policy, SHARED_POLICY_ATTR), (
            f"{SHARED_POLICY_MODULE} must export {SHARED_POLICY_ATTR!r} — the ONE function "
            f"both ledgers call. It lives in neither ledger module on purpose (the "
            f"loremaster.agent_ref precedent: a ledger owning the shared object forces its "
            f"sibling to import IT)"
        )

    @pytest.mark.parametrize("module_name", ["loremaster.briefs", "loremaster.messages"])
    def test_BOTH_ledgers_import_the_SHARED_policy_under_the_pinned_name(
        self, module_name: str
    ) -> None:
        """Fails CLOSED: a module that hand-rolled its own copy has no such attribute, so
        the mutation pin below could not patch it — and a mutation proof that cannot find
        its mutation point is a proof of nothing.  This states that precondition as its own
        assertion instead of letting it hide inside a monkeypatch.
        """
        import importlib

        module = importlib.import_module(module_name)
        assert hasattr(module, SHARED_POLICY_ATTR), (
            f"{module_name} must import {SHARED_POLICY_ATTR} from {SHARED_POLICY_MODULE} and "
            f"call it — never clone MessageLedger._reject_unknown_recipients' body"
        )

    async def test_MUTATION_replacing_the_shared_policy_changes_BOTH_verbs(
        self,
        monkeypatch: pytest.MonkeyPatch,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
    ) -> None:
        """PROVE SHARING BY MUTATION — the only test that distinguishes DRY from looks-DRY.

        A sentinel replaces the shared policy in the brief ledger's module; ``publish`` with
        a REGISTERED agent (an input the real policy would ACCEPT) must now raise it.  If
        ``briefs.py`` carries a private copy, the sentinel never fires and this goes red —
        which is the whole point.

        The ``send`` half of the same mutation is pinned in
        :meth:`TestSendRefusesBeforeTheWrite.test_MUTATION_send_routes_through_the_same_shared_policy`
        rather than here, so each verb's failure is attributable to that verb.
        """

        class _SharedPolicySentinel(RuntimeError):
            """Raised by the substituted shared policy — never by any private copy."""

        async def _sentinel(*_args: Any, **_kwargs: Any) -> None:
            raise _SharedPolicySentinel("the shared policy ran")

        import loremaster.briefs

        monkeypatch.setattr(loremaster.briefs, SHARED_POLICY_ATTR, _sentinel, raising=True)
        ledger, registered, _env = brief_ledger_with_a_real_agent
        with pytest.raises(_SharedPolicySentinel):
            await ledger.publish(
                _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=registered
            )

    async def test_BOTH_verbs_raise_an_error_a_caller_can_catch_with_ONE_except(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """A value-level sharing proof that needs no ATTRIBUTE name at all.

        ⚠ **RE-SHAPED 2026-07-27 BY LEAD RULING (adversary §C-DEF-3).**  This pin used to
        assert ``type(a) is type(b)`` — TYPE IDENTITY — and that made the contract
        UNSATISFIABLE alongside ``test_message_ledger.py::TestVocabularies::
        test_every_domain_error_is_a_message_ledger_error``, which requires
        ``UnknownRecipientError`` to remain a ``MessageLedgerError``.  All three readings
        were measured; the only one green on both suites made ``agent_existence`` import its
        neighbour, destroying the layering that module exists for (§4.D4).
        **RULED: a SHARED BASE CLASS with distinct subclasses.**

        So the property pinned here is the one a CALLER actually needs — *one ``except``
        catches both verbs* — and the base must belong to the SHARED policy module, not to
        either ledger.  A satisfying shape (illustrative, not prescribed):
        ``agent_existence.UnknownAgentError`` as the base, with
        ``messages.UnknownRecipientError(MessageLedgerError, UnknownAgentError)``.

        ⚠ And what this pin no longer does: TYPE IDENTITY was only ever a weak PROXY for
        *"is the policy really shared"*.  :class:`TestTheSharedPolicyIsTheSOLEDecisionPoint`
        tests that DIRECTLY, by neutralising the policy and demanding both verbs change —
        which is why that class, not this one, is now the load-bearing sharing instrument.
        """
        from loremaster.messages import MessageLedger

        ledger, _registered, env = brief_ledger_with_a_real_agent
        message_ledger = MessageLedger(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )
        await message_ledger.ensure_ready()
        try:
            with pytest.raises(Exception) as publish_error:  # noqa: B017
                await ledger.publish(
                    _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER,
                    agent_id=UNREGISTERED_AGENT_ID,
                )
            with pytest.raises(Exception) as send_error:  # noqa: B017
                await message_ledger.send(
                    sender=_Ref(UNREGISTERED_AGENT_ID, "ghost"),
                    session="wave7",
                    body="hello",
                    grade="signal",
                    recipients=[_Ref(UNREGISTERED_AGENT_ID, "ghost")],
                )
        finally:
            await message_ledger.close()
        shared_bases = sorted(
            base.__name__
            for base in set(type(publish_error.value).__mro__)
            & set(type(send_error.value).__mro__)
            if base.__module__ == SHARED_POLICY_MODULE
        )
        assert shared_bases, (
            f"publish raised {type(publish_error.value).__name__} "
            f"({type(publish_error.value).__module__}) and send raised "
            f"{type(send_error.value).__name__} ({type(send_error.value).__module__}), and "
            f"they share NO base class defined in {SHARED_POLICY_MODULE}. One policy, one "
            f"catchable thing: a caller that wants 'this id names no agent' must be able to "
            f"write ONE except clause. Subclasses are legal (the ruled shape); a base owned "
            f"by either LEDGER is not — that is the coupling the shared module exists to "
            f"prevent (§4.D4)"
        )


class _Ref:
    """A minimal ``AgentRefLike`` stand-in (``id`` + ``name``), read-only.

    Locally defined rather than imported from ``loremaster.agents``: the ledgers accept this
    Protocol STRUCTURALLY and never import their neighbours, and neither does this contract.
    """

    def __init__(self, ref_id: str, name: str) -> None:
        self._id = ref_id
        self._name = name

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name


class TestSendRefusesBeforeTheWrite:
    """§F(3) — ``send`` to ``[real, bogus]``.

    GREEN at `28387a0` for the refusal itself (``_reject_unknown_recipients`` already exists
    and already names EVERY bad id, which is why it is the precedent the shared policy is
    extracted FROM) — these pins are here as the REGRESSION half: the extraction must not
    weaken ``send``.  The mutation leg is RED until the extraction lands.

    The mixed fixture is the discriminating one: a wholly-bogus recipient list cannot tell
    "refused because one was unknown" from "refuses every list".
    """

    @staticmethod
    async def _ledger(env: SurrealEnv) -> Any:
        from loremaster.messages import MessageLedger

        ledger = MessageLedger(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )
        await ledger.ensure_ready()
        return ledger

    async def test_a_MIXED_recipient_list_is_refused_and_writes_NO_message_row(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """Asserting "no message row afterwards" is what distinguishes REFUSED EARLY from
        ROLLED BACK LATE.

        Both leave zero rows (probe §10.3 leg D: one bad recipient loses the WHOLE fan-out,
        message row included), so the row count alone cannot tell them apart — the ERROR
        TYPE does, and it is asserted here too.  Stating both is the pin; stating only the
        row count would be a false gate.
        """
        _brief_ledger, registered, env = brief_ledger_with_a_real_agent
        ledger = await self._ledger(env)
        try:
            with pytest.raises(Exception) as caught:  # noqa: B017
                await ledger.send(
                    sender=_Ref(registered, "fixer-b"),
                    session="wave7",
                    body="hello",
                    grade="signal",
                    recipients=[_Ref(registered, "fixer-b"), _Ref(UNREGISTERED_AGENT_ID, "ghost")],
                )
            assert not isinstance(caught.value, SurrealStoreError), (
                "the refusal must be the app check's, BEFORE the write — not the engine's "
                "rollback afterwards"
            )
            assert "ghost" in str(caught.value) or UNREGISTERED_AGENT_ID in str(caught.value), (
                f"the refusal must name the bad recipient: {str(caught.value)!r}"
            )
            rows = await ledger._query(f"SELECT id FROM {MESSAGE_TABLE}")  # noqa: SLF001
            assert rows == [], "a refused send must leave NO message row"
        finally:
            await ledger.close()

    async def test_POSITIVE_CONTROL_an_all_REGISTERED_recipient_list_is_delivered(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """Without this, "refused" above is satisfied by a build that refuses every send."""
        _brief_ledger, registered, env = brief_ledger_with_a_real_agent
        ledger = await self._ledger(env)
        try:
            result = await ledger.send(
                sender=_Ref(registered, "fixer-b"),
                session="wave7",
                body="hello",
                grade="signal",
                recipients=[_Ref(registered, "fixer-b")],
            )
            assert result.message.body == "hello"
            rows = await ledger._query(f"SELECT id FROM {MESSAGE_TABLE}")  # noqa: SLF001
            assert len(rows) == 1
        finally:
            await ledger.close()

    async def test_MUTATION_send_routes_through_the_same_shared_policy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
    ) -> None:
        """The ``send`` half of the sharing mutation.  RED at `28387a0`.

        ``send`` must stop owning ``_reject_unknown_recipients``' BODY and call the shared
        function instead: with the shared policy replaced, an ALL-REGISTERED send (which the
        real policy accepts) must raise the sentinel.
        """

        class _SharedPolicySentinel(RuntimeError):
            """Raised by the substituted shared policy — never by any private copy."""

        async def _sentinel(*_args: Any, **_kwargs: Any) -> None:
            raise _SharedPolicySentinel("the shared policy ran")

        import loremaster.messages

        monkeypatch.setattr(loremaster.messages, SHARED_POLICY_ATTR, _sentinel, raising=True)
        _brief_ledger, registered, env = brief_ledger_with_a_real_agent
        ledger = await self._ledger(env)
        try:
            with pytest.raises(_SharedPolicySentinel):
                await ledger.send(
                    sender=_Ref(registered, "fixer-b"),
                    session="wave7",
                    body="hello",
                    grade="signal",
                    recipients=[_Ref(registered, "fixer-b")],
                )
        finally:
            await ledger.close()


class TestTheSharedPolicyIsTheSOLEDecisionPoint:
    """⛔ **THE PINS THAT KILL W-E** — *routing is not sharing* — **and W-A as well.**

    The two sentinel mutations in :class:`TestTheUnknownAgentPolicyHasONEHome` /
    :class:`TestSendRefusesBeforeTheWrite` replace the shared policy with a **RAISING**
    stub, which proves only that the function is CALLED.  MEASURED (adversary §P1 W-E): a
    build where ``agent_existence.reject_unknown_agents`` exists, both ledgers import and
    call it, and it decides NOTHING (``return None``) — each ledger keeping a private copy
    of the decision underneath — passed this contract 38/38 **and every neighbouring
    suite**.  A caller that keeps working after the shared thing is changed is a private
    copy wearing the shared name.

    The mutation these legs run is SEMANTIC, and it is the only one that can tell the
    difference: replace the shared policy with an **ACCEPT-EVERYTHING** stub and demand that
    the unregistered id then reaches the **ENGINE**, i.e. surfaces as a
    :class:`~loremaster.store.surreal.SurrealStoreError` from the ``ENFORCED`` rejection.

    * a PRIVATE copy underneath still refuses -> not a ``SurrealStoreError`` -> RED (W-E)
    * NOTHING refuses, at either layer -> no raise at all -> RED (W-A, and any build whose
      guard never LANDED)

    ⚠ These two legs deliberately observe BOTH layers, so unlike the rest of sections E–H
    they ARE in the group-C mutation proof's declared-RED set — see the ``MUTATION_PROOF``
    block at the foot of this file.

    RED at `369db57`: neither module has the attribute, so ``monkeypatch.setattr(…,
    raising=True)`` fails closed.
    """

    @staticmethod
    async def _accept_everything(*_args: Any, **_kwargs: Any) -> None:
        """The substituted policy: it looks at nothing and refuses nothing."""
        return None

    async def test_MUTATION_neutralising_the_shared_policy_lets_publish_reach_the_ENGINE(
        self,
        monkeypatch: pytest.MonkeyPatch,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
    ) -> None:
        import loremaster.briefs

        monkeypatch.setattr(
            loremaster.briefs, SHARED_POLICY_ATTR, self._accept_everything, raising=True
        )
        ledger, _registered, _env = brief_ledger_with_a_real_agent
        with pytest.raises(SurrealStoreError):
            await ledger.publish(
                _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=UNREGISTERED_AGENT_ID
            )

    async def test_MUTATION_neutralising_the_shared_policy_lets_send_reach_the_ENGINE(
        self,
        monkeypatch: pytest.MonkeyPatch,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
    ) -> None:
        """``send``'s half.  ``to`` has been ``ENFORCED`` since packet 03, so the engine
        backstop this leg observes is already live — only the app layer is mutated.
        """
        import loremaster.messages

        _brief_ledger, registered, env = brief_ledger_with_a_real_agent
        monkeypatch.setattr(
            loremaster.messages, SHARED_POLICY_ATTR, self._accept_everything, raising=True
        )
        ledger = await TestSendRefusesBeforeTheWrite._ledger(env)
        try:
            with pytest.raises(SurrealStoreError):
                await ledger.send(
                    sender=_Ref(registered, "fixer-b"),
                    session="wave7",
                    body="hello",
                    grade="signal",
                    recipients=[_Ref(UNREGISTERED_AGENT_ID, "ghost")],
                )
        finally:
            await ledger.close()

    async def test_POSITIVE_CONTROL_the_neutralised_policy_still_lets_a_REGISTERED_publish_through(
        self,
        monkeypatch: pytest.MonkeyPatch,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
    ) -> None:
        """The control both legs above need, and it is load-bearing twice over.

        A build that raised ``SurrealStoreError`` for EVERY publish would satisfy them; so
        would a run in which the substitution silently did not take.  Here the stub is
        installed identically and a REGISTERED agent must still publish cleanly — which
        proves the mutation is inert for legal input and that the reds above are caused by
        the ID, not by the patch.
        """
        import loremaster.briefs

        monkeypatch.setattr(
            loremaster.briefs, SHARED_POLICY_ATTR, self._accept_everything, raising=True
        )
        ledger, registered, _env = brief_ledger_with_a_real_agent
        result = await ledger.publish(
            _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=registered
        )
        assert result.brief.version == 1
        assert await _briefed_edge_count(ledger) == 1


# =========================================================================== #
# MUTATION_PROOF — the DECLARED-RED set, written BEFORE the run (finding #196).
#
# ⚠ RE-SCOPED AT THE 04a/43 SPLIT.  04a flips exactly ONE edge, so this proof declares
# ONE edge's pins.  A proof still declaring four edges when 04a flips one produces
# DECLARED REDS THAT STAY GREEN — the direction ``scripts/mutation_proof.py``'s both-ways
# diff exists to catch, and the direction that reads as success. ``refers``/``answers_to``
# get their own proof in ``test_derivation_source_unification.py`` when packet 43 lands.
#
# ⚠ THE SET BELOW IS A PREDICTION, and is honestly labelled as one.  It was DERIVED from
# ``pytest --collect-only -q`` (never transcribed from a run — a set read off failures you
# just watched is the tautology in a new costume) plus reasoning about which pins depend
# on the clause.  It cannot be executed until the flip lands, because the mutation
# (deleting ``enforced=True``) is a no-op on a tree that never added it.  The both-ways
# diff is precisely what will catch a wrong prediction; do not "fix" a mismatch by editing
# this list to match the output.
#
# After the flip, run:
#
#   F=loremaster/tests/test_enforced_relations.py
#   A="$F::TestEveryRelationEdgeIsEnforced"
#   B="$F::TestTheOldWorldDerivationIsNotVacuous"
#   C="$F::TestTheEnforcedFlipMigratesADirtyStore"
#   D="$F::TestTheUnEnforcingDoor"
#   E="$F::TestTheBriefSliceIsOrderDependentOnTheAgentSlice"
#   G="$F::TestTheLEDGERsOwnMigrationPathLandsTheGuard"
#   H="$F::TestTheSharedPolicyIsTheSOLEDecisionPoint"
#   OLD="_define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)"
#   NEW="_define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE)"
#   ./scripts/mutation_proof.py \
#     --file loremaster/loremaster/store/surreal_schema.py \
#     --anchor "$OLD" --replacement "$NEW" \
#     --expect-red "$A::test_EVERY_relation_table_the_schema_emits_is_ENFORCED" \
#     --expect-red "$A::test_the_edge_carries_ENFORCED_in_its_own_slice[briefed-generate_brief_ddl]" \
#     --expect-red "$B::test_the_old_world_DIFFERS_from_todays_generator[briefed]" \
#     --expect-red "$C::test_the_guard_is_LIVE_after_applying_todays_ddl_to_a_DIRTY_store[briefed]" \
#     --expect-red "$D::test_re_emitting_the_edge_WITHOUT_ENFORCED_silently_un_guards_it[briefed]" \
#     --expect-red "$E::test_a_brief_slice_applied_WITHOUT_the_agent_slice_still_guards" \
#     --expect-red "$G::test_ensure_ready_on_a_DIRTY_store_makes_the_guard_LIVE" \
#     --expect-red "$H::test_MUTATION_neutralising_the_shared_policy_lets_publish_reach_the_ENGINE" \
#     -- uv run pytest -q "$F"
#
# ⚠ THE SET GREW BY TWO ON 2026-07-27, and the reason is a CORRECTION to the sentence that
# used to stand here (*"the app-check pins are deliberately NOT in the set"*):
#
#   * ``$G`` is a MIGRATION pin, not an app-check pin — it drives ``ensure_ready`` and
#     nothing else.  It belongs to group B/C and reddens with them.
#   * ``$H``'s PUBLISH leg is the one place where a pin OBSERVES BOTH LAYERS ON PURPOSE: it
#     neutralises the app policy precisely so the ENGINE's rejection is what it measures.
#     Under this mutation nothing refuses at either layer, so it reddens — CORRECTLY.  Its
#     SEND leg does not (``to``'s clause is untouched by this mutation), and neither does its
#     positive control.
#
# Every OTHER app-check pin (sections E–H: the refusal, the naming, the counter row, the
# RELATE sentinel, the second identity, the common-base pin) stays OUT of the set and must
# stay GREEN under this mutation: they depend on the app-level layer, not on the engine
# clause, and a build that reddened them here would have coupled two layers the contract
# requires to stay independent.  The adversary RAN this proof on its reference build and the
# six-pin version fired EXACTLY (6/6, no unexpected reds, no declared-green) with every
# app-check pin staying independent — so a mismatch on the eight-pin version is a finding
# about the BUILD, not a licence to edit this list.
#
# PROOF 2 — group E, ONE IMPLEMENTATION.  Already MECHANISED IN-SUITE rather than left to
# a shell block: ``test_MUTATION_replacing_the_shared_policy_changes_BOTH_verbs`` and
# ``test_MUTATION_send_routes_through_the_same_shared_policy`` replace the shared function
# at runtime and demand each verb changes behaviour.  A private copy in either module
# leaves its verb working and reddens the pin.
# =========================================================================== #
