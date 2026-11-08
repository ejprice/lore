"""Contract — packet 63b wave ii-b: P1-m Leg B + P-G3, the DD-3.c DIRTY-STORE MIGRATE twin.

Design ``docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md`` §12.6 (Leg B) + §13.3 (the
grade delta: Leg B carries SIX rows — five length violators + one clean; the junk-grade row moves to
the PINNED KNOWN BOUND P-G3). Authored by ``contract-63b-ii-b`` (Opus 4.8 contract author; CONTRACT
TESTS ONLY — no production). Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500).

WHY A SIBLING, NOT ``test_message_migrate_63b_ii_a.py``: this leg needs the UNBOUNDED old-world DDL
(so the app-cap-refused violators can be SEEDED under it) — the ii-a ``message_world`` seeds through
the real ``send`` (which the app cap bounds), so it cannot hold a violator. This file imports the ii-a
migrate substrate (``store_handle``/``build_principal_and_keep_stores``/the seeder) rather than cloning
it (F-DUP / ONE IMPLEMENTATION), and leaves the GREEN ii-a file untouched.

THE TWO-LEG SHAPE (trust doctrine, at test scale — §12.6 "why two legs"): Leg A
(``test_comms_schema.py::TestTheMessageAssertsAreDroppedFromADIRTYStore``) starts from the ASSERTED
world and proves the DROP LANDS (the #107 direction); it never runs the migrate, so it cannot see a
re-added constraint denying it. Leg B (here) starts from the UNBOUNDED world and proves the REAL
migrate SURVIVES legacy violators (the DD-3.c direction); its fixture cannot start asserted, so it
cannot see an emitter that fails to LAND the drop. Each is blind exactly where the other is strong.

RED-AT-HEAD: at HEAD ``generate_message_ddl()`` STILL emits the four length ASSERTs, so migrating the
schema over the six dirty rows write-poisons the five violators, and the REAL ``migrate_governed``
UPDATE (which SETs owner/scope over every NONE-owner row, re-validating the WHOLE record — store-ref
§1.4) is REFUSED WHOLESALE (a SurrealStoreError naming the field). On the ii-b build the length
ASSERTs are gone, the migrate stamps all six, and the over-cap values survive byte-intact.
"""

from __future__ import annotations

from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    apply_ddl,
    build_principal_and_keep_stores,
    frozen_asserted_message_ddl,
    seed_message_legacy,
    session_keep_id_for,
    store_handle,
    unbounded_message_ddl,
)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from loremaster.agents import AgentRegistry
from loremaster.store import surreal_schema
from loremaster.store._txn import TxnDomainRejectionError
from sdk3_shape_fakes import bare_record_key, same_record

from loremaster import principals

_MESSAGE_TABLE = surreal_schema.MESSAGE_TABLE
_AGENT_TABLE = "agent"
_DIM = 8

# The five LENGTH violator shapes Leg B migrates (grade is P-G3, a pinned KNOWN BOUND — it is NOT in
# Leg B's stamped set because R19 keeps its ASSERT and a junk-grade row REFUSES the cutover by design).
_LENGTH_VIOLATOR_SHAPES = ("body", "thread", "refs_count", "refs_entry", "task_id")


def _violator_overrides(shape: str) -> dict[str, Any]:
    """The seed override for one violator shape — sizes DERIVED from the caps (so they track the
    constant), one over its bound."""
    pointer = surreal_schema.MESSAGE_POINTER_MAX_CHARS
    body_cap = surreal_schema.MESSAGE_BODY_MAX_CHARS
    refs_cap = surreal_schema.MESSAGE_REFS_MAX_COUNT
    overrides: dict[str, dict[str, Any]] = {
        "body": {"body": "z" * (body_cap + 1)},
        "thread": {"thread": "t" * (pointer + 1)},
        "refs_count": {"refs": [f"r{index}" for index in range(refs_cap + 1)]},
        "refs_entry": {"refs": ["r" * (pointer + 1)]},
        "task_id": {"task_id": "t" * (pointer + 1)},
        "grade": {"grade": "urgent"},
    }
    return overrides[shape]


def _assert_value_byte_intact(row: dict[str, Any], shape: str) -> None:
    """A migration converges the SCHEMA, never the DATA (store-ref §1.4): the over-cap value survives
    byte-intact after the migrate (this ruling adds no heal)."""
    pointer = surreal_schema.MESSAGE_POINTER_MAX_CHARS
    body_cap = surreal_schema.MESSAGE_BODY_MAX_CHARS
    refs_cap = surreal_schema.MESSAGE_REFS_MAX_COUNT
    if shape == "body":
        assert len(row["body"]) == body_cap + 1, row
    elif shape == "thread":
        assert len(row["thread"]) == pointer + 1, row
    elif shape == "refs_count":
        assert len(row["refs"]) == refs_cap + 1, row
    elif shape == "refs_entry":
        assert len(row["refs"][0]) == pointer + 1, row
    elif shape == "task_id":
        assert len(row["task_id"]) == pointer + 1, row
    else:  # pragma: no cover - only length shapes reach here
        raise AssertionError(f"no byte-intact check for shape {shape!r}")


async def _migrate(connection: Any, env: Any, *, keep_store: Any, principal_store: Any) -> Any:
    """Drive ``migrate_governed(table='message')`` through a StoreHandle over the fixture connection
    (R4: the verb borrows the target store's driver, never a raw connection — ROUTING IS NOT SHARING:
    a copied ``UPDATE message SET …`` is a private copy that drifts from ``_migrate_message_owner``)."""
    handle, _calls = store_handle(connection, url=env.url)
    return await principals.migrate_governed(
        table=_MESSAGE_TABLE, store=handle, keep_store=keep_store, principal_store=principal_store
    )


@pytest_asyncio.fixture()
async def dirty_message_world() -> Any:
    """A store whose ``message`` table carries the UNBOUNDED old-world DDL + governed overlay, a single
    operator principal, and ONE MIGRATED sender agent (``owner_principal`` set, so the migrate does not
    refuse on the §2.6 agent-first precondition — this fixture forces the BACKFILL fate). Yields
    ``(principal_store, keep_store, connection, env, sender_bare)``; each test seeds its own legacy
    rows under the unbounded DDL, then migrates the SCHEMA. Reaped (NEVER :18500)."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    registry = AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    try:
        await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
        await apply_ddl(connection, unbounded_message_ddl(), url=env.url)
        await principal_store.create(email="operator@example.com", role="member")
        operator = (await principal_store.list())[0]
        # a MIGRATED sender agent (owner_principal set → agent-first SATISFIED, so the migrate reaches
        # the message backfill rather than refusing before it).
        sender = (
            await registry.register(
                "sender_agent",
                session="s1",
                role="builder",
                owner_principal_id=bare_record_key(operator.id),
                session_keep_id=await session_keep_id_for(
                    keep_store, principal_store, owner_principal_id=bare_record_key(operator.id), session="s1"
                ),  # r2 (A3): the owner travels WITH THE session keep
            )
        ).agent
        yield principal_store, keep_store, connection, env, bare_record_key(sender.id)
    finally:
        await registry.close()
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


class TestTheRealMigrateSurvivesLegacyViolators:
    """P1-m Leg B (§12.6 / §13.3) — the DD-3.c direction: the REAL ``migrate_governed(table='message')``
    survives the six legacy rows the app cap would have refused (five length violators + one clean), is
    NOT refused, stamps all six, and leaves every over-cap value byte-intact.

    Mutation proof (declared, from ``--collect-only``): re-add ONE length ASSERT to
    ``_MESSAGE_FIELD_SPECS`` → Leg B's main leg RED with the engine's text naming that field; Leg A's
    matching parametrization RED; P2-m RED; the C-CONTROL stays GREEN (it uses the frozen DDL); restore
    → all GREEN. Both directions diffed (``scripts/mutation_proof.py``).
    """

    @staticmethod
    async def _seed_six(connection: Any, sender_bare: str) -> dict[str, str]:
        """Seed the six legacy rows (five length violators + one clean) UNDER the unbounded DDL, all
        NONE-owner, ``sender`` = the migrated agent. Returns ``{shape: message_id}`` (the clean row is
        keyed ``clean``)."""
        ids: dict[str, str] = {}
        for index, shape in enumerate(_LENGTH_VIOLATOR_SHAPES):
            ids[shape] = await seed_message_legacy(
                connection, sender_id=sender_bare, session="s1", seq=index,
                **_violator_overrides(shape),
            )
        ids["clean"] = await seed_message_legacy(
            connection, sender_id=sender_bare, session="s1", seq=99, body="a clean legacy body"
        )
        return ids

    async def test_the_real_migrate_survives_six_legacy_violators_all_stamped(
        self, dirty_message_world: Any
    ) -> None:
        """⚠ RED at HEAD (DD-3.c direction) — seed six legacy rows under the unbounded DDL, migrate the
        SCHEMA with the current ``generate_message_ddl()``, then drive the REAL
        ``migrate_governed(table='message')``: it is NOT refused, stamps all SIX, and every over-cap
        value survives byte-intact. At HEAD the emitter STILL emits the four length ASSERTs, so
        migrating the schema write-poisons the five violators and the migrate UPDATE (SET owner/scope
        over every NONE-owner row — a WHOLE-record re-validation) is REFUSED WHOLESALE (a
        SurrealStoreError naming the field). On the ii-b build the length ASSERTs are gone and the
        migrate stamps all six."""
        principal_store, keep_store, connection, env, sender_bare = dirty_message_world
        ids = await self._seed_six(connection, sender_bare)
        before = await run(connection, f"SELECT count() FROM {_MESSAGE_TABLE} GROUP ALL")
        assert before and before[0]["count"] == 6, (
            f"BASELINE: the unbounded old world must accept all six legacy rows before migrating, got "
            f"{before!r}"
        )
        await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
        try:
            result = await _migrate(
                connection, env, keep_store=keep_store, principal_store=principal_store
            )
        except Exception as error:  # noqa: BLE001 - RED-at-HEAD surface (a length ASSERT poisons it)
            pytest.fail(
                "RED-at-HEAD (right reason): migrate_governed(table='message') RAISED on the dirty "
                "store — a legacy over-cap row failed a length ASSERT the current emitter STILL lands, "
                f"so the whole cutover UPDATE aborted (§12.6 Leg B / DD-3.c). engine: {error}"
            )
        assert not result.refused, (
            f"the message migrate was REFUSED over the dirty store — a legacy violator failed a store "
            f"ASSERT the emitter still lands, or a precondition tripped (reason: {result.reason!r})"
        )
        assert result.backfilled == 6, (
            f"the migrate must backfill all SIX legacy rows (five violators + one clean), got "
            f"backfilled={result.backfilled!r} (scanned={getattr(result, 'scanned', '?')!r})"
        )
        # First call over the dirty store: it SCANNED all six and NONE were already migrated
        # (they were all NONE-owner legacy rows) — the receipt, not just the backfilled count.
        assert result.scanned == 6 and result.already_migrated == 0, (
            f"the FIRST migrate over the dirty store must scan all six NONE-owner rows and count zero "
            f"already-migrated, got scanned={result.scanned!r} already_migrated={result.already_migrated!r}"
        )
        # every over-cap violator VALUE survives byte-intact + is now owner-stamped.
        for shape in _LENGTH_VIOLATOR_SHAPES:
            row = (
                await run(
                    connection,
                    f"SELECT owner_agent, owner_principal, scope, body, thread, refs, task_id "
                    f"FROM type::record('{_MESSAGE_TABLE}', $id)",
                    {"id": ids[shape]},
                )
            )[0]
            assert same_record(row["owner_agent"], f"{_AGENT_TABLE}:{sender_bare}"), (
                f"{shape}: owner_agent must be the SENDER after migrate (§4.C), got {row['owner_agent']!r}"
            )
            assert row["owner_principal"] is not None and isinstance(row["scope"], str), (
                f"{shape}: owner_principal/scope not backfilled, got {row!r}"
            )
            _assert_value_byte_intact(row, shape)

    async def test_the_migrate_is_idempotent_on_the_dirty_store(
        self, dirty_message_world: Any
    ) -> None:
        """⚠ RED at HEAD (same cause) — a SECOND migrate over the already-stamped dirty store backfills
        ZERO (idempotent), not refused. At HEAD the FIRST migrate raises, so this reds on the first
        call. On the ii-b build the first stamps six and the second backfills zero."""
        principal_store, keep_store, connection, env, sender_bare = dirty_message_world
        await self._seed_six(connection, sender_bare)
        await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
        try:
            first = await _migrate(connection, env, keep_store=keep_store, principal_store=principal_store)
            second = await _migrate(connection, env, keep_store=keep_store, principal_store=principal_store)
        except Exception as error:  # noqa: BLE001 - RED-at-HEAD surface
            pytest.fail(
                f"RED-at-HEAD (right reason): the migrate RAISED on the dirty store (§12.6 Leg B). "
                f"engine: {error}"
            )
        assert not first.refused and first.backfilled == 6, f"first migrate: {first!r}"
        assert not second.refused and second.backfilled == 0, (
            f"the SECOND migrate over the dirty store must backfill 0 (idempotent), got {second!r}"
        )

    async def test_C_CONTROL_the_frozen_asserted_ddl_makes_the_migrate_RAISE(
        self, dirty_message_world: Any
    ) -> None:
        """C-CONTROL (§12.6 step 6) — the instrument CAN see the hazard: seed the six rows, then apply
        the FROZEN asserted DDL (not the current emitter) as the schema migrate, and the REAL migrate
        RAISES with ZERO rows stamped (the measured DD-3.c mechanism reproduced on ``message``). This
        makes Leg B self-validating rather than trusting a mutation run — a build where Leg B's main leg
        goes GREEN only because the migrate never touched a poisoned row would leave THIS control GREEN
        too, which it is (it uses the FROZEN DDL, immune to the emitter's drop) — proving a poisoned row
        DOES abort the migrate. GREEN at HEAD AND after the ii-b build."""
        principal_store, keep_store, connection, env, sender_bare = dirty_message_world
        ids = await self._seed_six(connection, sender_bare)
        await apply_ddl(connection, frozen_asserted_message_ddl(), url=env.url)
        # §14.1 (sidecar): the migrate drives ``run_query`` through the driver, which WRAPS the engine
        # ASSERT violation as the typed ``TxnDomainRejectionError`` carrying the ``(assert violation)``
        # class label (the engine's field text is redacted; ledger #31). Pin the TYPE + label so a raise
        # for the WRONG reason (transport fault, a governed conflict, a fixture TypeError) reds instead
        # of passing — a bare ``Exception`` would admit them.
        with pytest.raises(TxnDomainRejectionError, match=r"\(assert violation\)"):
            await _migrate(connection, env, keep_store=keep_store, principal_store=principal_store)
        # ZERO stamped — a whole-statement abort leaves every row NONE-owner.
        for message_id in ids.values():
            row = (
                await run(
                    connection,
                    f"SELECT owner_principal FROM type::record('{_MESSAGE_TABLE}', $id)",
                    {"id": message_id},
                )
            )[0]
            assert row["owner_principal"] is None, (
                f"the aborted migrate left a row STAMPED ({message_id}) — the whole-statement mechanism "
                f"must stamp NOTHING when it raises"
            )


class TestAJunkGradeLegacyRowRefusesTheCutover:
    """P-G3 (§13.3) — a PINNED KNOWN BOUND. The grade ASSERT is KEPT (R19), so a legacy out-of-domain
    ``grade`` row REFUSES the message cutover — BY DESIGN, because the reader (``InboxEntry.grade:
    MessageGrade``) could never serve that row either. This pin goes RED the day someone drops the grade
    ASSERT (then the junk row would be migrated + later crash a recipient's drain on decode — worse).

    ⚠ It is the GRADE twin of Leg B's C-control (a LENGTH violator under the frozen DDL), kept LIVE and
    against the CURRENT emitter: because grade STAYS asserted, the current emitter poisons a junk-grade
    row exactly as the frozen DDL does. GREEN at HEAD AND after the ii-b build (grade kept throughout).
    """

    async def test_a_legacy_junk_grade_row_refuses_the_real_migrate(
        self, dirty_message_world: Any
    ) -> None:
        """KNOWN BOUND (63b-ii-b §13): seed ONE junk-``grade`` legacy row + one clean under the
        unbounded DDL (NO length violators — the ONLY thing that can poison this migrate is the grade),
        migrate the schema with the CURRENT emitter (grade ASSERT kept), then drive the REAL migrate →
        it RAISES and the read-back shows BOTH rows still NONE-owner (zero stamped — the whole-statement
        mechanism). Heal a real occurrence FIRST with the §13.2 three-step widen/heal/narrow protocol.
        If you closed this deliberately (dropped grade's ASSERT), delete this pin and say so.

        ⚠ The engine's FIELD NAME is NOT asserted: the migrate driver WRAPS the ASSERT violation as
        *"…backfill rejected (assert violation); see the server log for the full engine detail"* — the
        field is redacted by construction (measured 2026-09-11; report §Flags). The GRADE is isolated
        instead by CONSTRUCTION: the fixture carries no length violator, so the sibling positive control
        ``test_CONTROL_a_legal_grade_fixture_migrates_cleanly`` (same rows, LEGAL grade → migrate
        SUCCEEDS) proves the ONLY difference that refuses is the junk grade. GREEN at HEAD AND after the
        ii-b build (grade kept throughout)."""
        principal_store, keep_store, connection, env, sender_bare = dirty_message_world
        junk_id = await seed_message_legacy(
            connection, sender_id=sender_bare, session="s1", seq=0, grade="urgent"
        )
        clean_id = await seed_message_legacy(
            connection, sender_id=sender_bare, session="s1", seq=1, body="a clean legacy body"
        )
        await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
        # §14.1 (sidecar): pin the driver's typed domain rejection + its ``(assert violation)`` class
        # label (not a bare ``Exception``) — the grade ASSERT is what poisons the migrate, and a raise
        # for another reason (transport, a fixture error) must RED, not satisfy the KNOWN BOUND. The
        # sibling positive control isolates the GRADE as the sole refusing difference (the field name
        # is redacted, so it cannot be matched).
        with pytest.raises(TxnDomainRejectionError, match=r"\(assert violation\)"):
            await _migrate(connection, env, keep_store=keep_store, principal_store=principal_store)
        for message_id in (junk_id, clean_id):
            row = (
                await run(
                    connection,
                    f"SELECT owner_principal FROM type::record('{_MESSAGE_TABLE}', $id)",
                    {"id": message_id},
                )
            )[0]
            assert row["owner_principal"] is None, (
                f"the aborted (junk-grade) migrate left a row STAMPED ({message_id}) — zero rows must "
                f"stamp when the whole-statement UPDATE raises"
            )

    async def test_CONTROL_a_legal_grade_fixture_migrates_cleanly(
        self, dirty_message_world: Any
    ) -> None:
        """POSITIVE CONTROL for the KNOWN BOUND above (the field name is unavailable, so the grade is
        isolated by construction): the SAME two-row fixture with a LEGAL grade instead of ``urgent``
        migrates SUCCESSFULLY (not refused, both stamped). The ONLY difference from the pin above is the
        junk grade, so the pin above refuses BECAUSE OF the grade. GREEN at HEAD AND after the build (no
        length or grade violation exists here). A build that DROPPED grade's ASSERT would make the pin
        above red (accepted) while this stays green — that pair is the R19 discrimination."""
        principal_store, keep_store, connection, env, sender_bare = dirty_message_world
        await seed_message_legacy(
            connection, sender_id=sender_bare, session="s1", seq=0, grade="directive"
        )
        await seed_message_legacy(
            connection, sender_id=sender_bare, session="s1", seq=1, body="a clean legacy body"
        )
        await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
        result = await _migrate(connection, env, keep_store=keep_store, principal_store=principal_store)
        assert not result.refused and result.backfilled == 2, (
            f"a legal-grade fixture (no length or grade violation) must migrate cleanly — the KNOWN "
            f"BOUND's refusal is the junk grade, not a fixture artifact. got {result!r}"
        )
