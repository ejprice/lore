"""Contract — packet 64b-i: the ``finding`` dirty-store MIGRATION (kickoff rulings ``e5fa7f9`` §2 F1 + §12
F1/DD-3.c rows; P64 §Scope IN 7–8). Authored by ``contract-64b`` (Opus 5.5 — contract tests ONLY).

THE RULING UNDER TEST (kickoff §2): ``finding`` is UNOWNED-LEGACY (``LegacyMapping("finding",
"STRING-UNRESOLVABLE")``): a legacy row's owner stays NONE/NONE — ``finding.created_by`` is a display
string, NEVER promoted to an owner, not even when it EXACTLY equals a registered agent name (the
guess-wearing-a-mapping door, 63-rulings §2.1) — and ``scope`` is backfilled to the canonical PROJECT
keep (``get_or_create_keyed(PROJECT_KEEP_KEY, …)``). The backfill is scope-keyed AND self-guarding (the
am-21 CD-1 WHERE), under ``governed_exempt("migrate-governed", statement=…)``, driver-routed,
idempotent, with NO order precondition. For THIS disposition the migrated state is ``(owner NONE, scope
set)``, so a scoped-but-ownerless row is HEALTHY; the only half-pair is owned-but-UNSCOPED → REFUSE,
byte-inert, ONE refusal naming the count + bounded ids + "half-applied".

⚠ THE QUANTIFIER (CLAUDE.md "THE QUANTIFIER LAW"): the half-pair rule is ruled for the DISPOSITION
("an UNOWNED-LEGACY table"), and ``memory`` is the other UNOWNED-LEGACY table — the kickoff DRY row
rules the memory leg PARAMETRISED by table (never two bodies). So the half-pair pins run over
``{memory, finding}``; the memory row is RED at HEAD for the same reason (the shared precondition is
unbuilt). REPORT §FORKS FK-2 records this as a reading.

DD-3.c (kickoff §12 DD-3.c row; P64 §Scope IN 8): the five non-empty ASSERTs DROP (their violation set
is WIDER than the reader's — ``Finding`` decodes any string), ``status`` is KEPT (its violation set ==
the ``FindingStatus`` Literal decode set). Leg A proves the DROP LANDS on a store that already carries
the asserts (the #107 direction); Leg B proves the REAL migrate survives the legacy violators the writer
would refuse (the DD-3.c direction) with a C-CONTROL that makes the instrument able to fail; P-F3 PINS
the KEPT assert's consequence (a junk-status legacy row refuses the backfill) as a KNOWN BOUND.

STORE LAW: ``docs/reference/surrealdb-31-capabilities.md`` §1.1 (OVERWRITE fields — the drop lands only
because OVERWRITE is a full replace, §1.2), §1.4 (legacy rows are seeded UNDER THE OLD DDL; a TYPE or
narrowing change converges schema, not data), §2 (``SELECT *`` omits NONE → readers use ``.get``),
§3 (multi-statement DDL through ``apply_ddl``). Live TEST store ``:18000`` (NEVER :18500), reaped.

F1 S2 (amendment 3 §D-3, ``aea2a9d``): the REAL production dump, restored by the COMMITTED driver
``scripts/restore_prod_dump.py`` (written by probe-64) into a minted ``test_dump_…`` database on :18000,
is the LAST class here — marker-gated on the driver's receipt line ``LORE_PROD_DUMP_DB=<name>`` (the ONLY
skip marker in the 64 contract). BOUND, named (amendment 3 §D-3): S2 is NOT in the standard gate; it RUNS
at 64b-i's close-out (builder receipt + the cold audit's re-run), at 64a's, and in 65's dress rehearsal —
a close-out without its receipt is ``done-with-deviations``. Re-open trigger: the day the export format
changes (the driver's section refusal is the alarm).
"""

from __future__ import annotations

import contextlib
import os
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _governed_contract import (
    _normalise_statement,
    apply_ddl,
    build_principal_and_keep_stores,
    classify_tree_observed_write,
    observe_governed_table_writes,
    seed_agent_governed,
    seed_agent_legacy,
    seed_memory_governed,
    seed_memory_legacy,
    store_handle,
)
from _governed_contract_64 import (
    FINDING_DROPPED_ASSERT_COLUMNS,
    FINDING_TABLE,
    FINDING_TREE_ALLOWLIST,
    HOSTILE_FREE_TEXT,
    MIGRATE_FINDING_GOLDEN,
    bare,
    current_finding_ddl,
    finding_row,
    frozen_asserted_finding_ddl,
    seed_finding_governed,
    seed_finding_legacy,
    unbounded_finding_ddl,
)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from loremaster.governed import PROJECT_KEEP_KEY, report_unmigrated_governed_rows
from loremaster.sanitise import CONTROL_CHAR_PATTERN
from loremaster.store import surreal_schema
from loremaster.store._txn import TxnDomainRejectionError
from lorerunes.pdp import keep_scope
from sdk3_shape_fakes import bare_record_key
from test_fixwave_a19a_63c_i_a import _names, _stated_integers

from loremaster import principals

if TYPE_CHECKING:
    from loremaster.keeps import KeepStore
    from loremaster.principals import PrincipalStore, _migrate_finding_scope
    from loremaster.store._txn import StoreHandle

    # 64b-i's RULED, not-yet-built signature this file pins — a TYPED CALL (amendment 8 §5, MP-9; a permanent
    # signature pin). Until the build lands it, a mypy error OWNED by bound `packet-64b-i-contract` (#461).
    # DUAL (r2): r1's name-only ``(_migrate_finding_scope,)`` tuple is replaced.
    async def _ruled_64b_i_finding_leg_shape(
        store: StoreHandle, keep_store: KeepStore, principal_store: PrincipalStore
    ) -> None:
        """kickoff §13 — the finding leg (the memory leg's shape; the ONE UNOWNED-LEGACY policy)."""
        result = await _migrate_finding_scope(store, keep_store, principal_store)
        assert result.backfilled >= 0


_DIM = 8
_MEMORY_TABLE = "memory"
_PRINCIPALS_PY = "loremaster/loremaster/principals.py"
#: every table a refused migrate must leave byte-identical (the governed tables it could touch + the
#: tables a leg would MINT into before refusing — the project keep and its household edge).
_BYTE_INERT_TABLES = (FINDING_TABLE, _MEMORY_TABLE, "agent", "keep", "member_of", "principal")


def migrate_goldens() -> dict[str, tuple[str, str]]:
    """leg function → (table, its adjudicated backfill GOLDEN) — the goldens are READ from their home oracles
    (each governed table's F5 allowlist / shape pin), never re-typed here (CLAUDE.md "one oracle")."""
    from test_agent_governance_63c_i_a import (  # noqa: PLC0415
        TestTheBackfillShapeAssertNormalisesSpellingNeverWidens63cIA as _AgentShape,
    )
    from test_memory_enforcement_63b_ia import _MIGRATE_GOLDEN as _MEMORY_GOLDEN  # noqa: PLC0415
    from test_message_enforcement_63b_ii_a import _MIGRATE_MESSAGE_GOLDEN  # noqa: PLC0415

    return {
        "_migrate_agent_owner": ("agent", _AgentShape._CORRECT),  # noqa: SLF001 - the agent shape oracle
        "_migrate_memory_scope": (_MEMORY_TABLE, _MEMORY_GOLDEN),
        "_migrate_message_owner": ("message", _MIGRATE_MESSAGE_GOLDEN),
        "_migrate_finding_scope": (FINDING_TABLE, MIGRATE_FINDING_GOLDEN),
    }


def unowned_legacy_tables() -> tuple[str, ...]:
    """FK-2 (packet-64 amendment 7 §3) — the UNOWNED-LEGACY disposition, DERIVED from the migrate goldens: a
    leg whose golden ``SET`` clause stamps NO owner column is UNOWNED-LEGACY (its migrated state is ``owner
    NONE, scope set``). ⚠ REPORT §FORKS FK-r2-4: am-7 §3 keys the rule on the WHERE containing
    ``owner_principal
    IS NONE``; MEASURED at ``4beb79e`` that rule yields ``{message, finding}`` (memory's WHERE has no owner
    conjunct; message's does, yet message is OWNED-legacy) — the opposite of the ruling's own stated output
    ``{memory, finding}``. The SET-clause rule yields exactly ``{memory, finding}``."""
    tables = []
    for _leg, (table, golden) in sorted(migrate_goldens().items()):
        set_clause = re.split(r"\bWHERE\b", golden, maxsplit=1, flags=re.IGNORECASE)[0]
        if not re.search(r"\bowner_(principal|agent)\s*=", set_clause):
            tables.append(table)
    return tuple(sorted(tables))


#: the UNOWNED-LEGACY tables the half-pair rule quantifies over — DERIVED (DUAL r2: r1's hand pair
#: ``(_MEMORY_TABLE, FINDING_TABLE)`` is RE-KEYED to the derivation; its value is unchanged today, which the
#: completeness pin below makes a checked fact rather than a hope).
_UNOWNED_LEGACY_TABLES = unowned_legacy_tables()
#: a count ≠ every other fixture count here, so a stated count discriminates.
_TRAP_COUNT = 2
_LEGACY_COUNT = 3
#: a HOSTILE stored id — THE shared hostile value (``_governed_contract_64.HOSTILE_FREE_TEXT``).
_HOSTILE_TRAP_ID = HOSTILE_FREE_TEXT


@dataclass
class _MigrateWorld:
    env: Any
    connection: Any
    principal_store: Any
    keep_store: Any
    handle: Any
    operator_bare: str

    async def migrate(self, table: str = FINDING_TABLE) -> Any:
        return await principals.migrate_governed(
            table=table, store=self.handle, keep_store=self.keep_store, principal_store=self.principal_store
        )

    async def snapshot(self) -> dict[str, Any]:
        return {
            table: await run(self.connection, f"SELECT * FROM {table} ORDER BY id")
            for table in _BYTE_INERT_TABLES
        }

    async def project_scope(self) -> str:
        ids = await run(self.connection, "SELECT VALUE id FROM keep WHERE key = $k", {"k": PROJECT_KEEP_KEY})
        assert ids, "the migrate did not mint the canonical project keep"
        return keep_scope(bare_record_key(ids[0]))


@contextlib.asynccontextmanager
async def _migrate_world(finding_ddl: str) -> AsyncIterator[_MigrateWorld]:
    """A throwaway store: the CURRENT agent/memory/message/brief emitters (so 63c's verb-level
    preconditions see a production-shaped store), the ``finding`` table under ``finding_ddl`` (the OLD
    world the caller chooses — seed legacy rows BEFORE upgrading it, store-ref §1.4), and ONE admin
    OPERATOR principal (so a refusal here is never the operator-ambiguity one). Reaped."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    try:
        await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
        await apply_ddl(connection, surreal_schema.generate_memory_ddl(dim=_DIM), url=env.url)
        await apply_ddl(connection, surreal_schema.generate_message_ddl(), url=env.url)
        await apply_ddl(connection, surreal_schema.generate_brief_ddl(), url=env.url)
        await apply_ddl(connection, finding_ddl, url=env.url)
        operator = await principal_store.create(email="operator@example.com", role="admin")
        handle, _calls = store_handle(connection, url=env.url)
        operator_bare = bare_record_key(operator.id)
        yield _MigrateWorld(env, connection, principal_store, keep_store, handle, operator_bare)
    finally:
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


async def _upgrade_finding_schema(world: _MigrateWorld) -> None:
    """Re-apply the CURRENT finding emitter over the old world (what ``FindingLedger.ensure_ready`` does
    at boot) — the #107 direction."""
    await apply_ddl(world.connection, current_finding_ddl(), url=world.env.url)


async def _seed_legacy(world: _MigrateWorld, count: int, *, start: int = 1, **overrides: Any) -> list[str]:
    return [
        await seed_finding_legacy(
            world.connection, row_id=f"legacy_{start + index}", number=start + index, **overrides
        )
        for index in range(count)
    ]


async def _assert_the_governed_trio_landed(world: _MigrateWorld) -> None:
    """RED-for-the-right-reason guard before a governed seed: the CURRENT emitter must carry the trio."""
    info = await run(world.connection, f"INFO FOR TABLE {FINDING_TABLE}")
    info_map = info[0] if isinstance(info, list) else info
    fields = set((info_map or {}).get("fields", {}))
    assert {"owner_principal", "owner_agent", "scope"} <= fields, (
        f"UNBUILT (kickoff §Scope IN 1): generate_finding_ddl() carries no governed trio: {sorted(fields)}"
    )


def _assert_finding_leg_ran(result: Any) -> None:
    assert not result.refused, (
        f"UNBUILT / REFUSED: migrate_governed(table='finding') did not run the finding leg (kickoff §2 F1): "
        f"{result.reason!r}"
    )


# =========================================================================== #
# F1-a / F1-b — the NEW DDL on the OLD world, and the fail-closed read before the verb.
# =========================================================================== #


class TestTheGovernedFindingSchemaLandsOnAnOldStore:
    """F1-a (kickoff §12): OLD DDL → seed legacy → NEW DDL: the governed trio + both governed indexes
    land (``_governed_field_specs`` via OVERWRITE + ``_governed_index_statements`` — the ONE emitter),
    the legacy rows survive, and an UNRELATED-column UPDATE of a legacy row succeeds (store-ref §1.4: a
    required post-birth field would poison every legacy row's next UPDATE; ``option<>`` does not)."""

    async def test_the_trio_lands_and_a_legacy_row_stays_writable(self) -> None:
        """⚠ RED at HEAD (the finding emitter carries no governed column). Kills: a trio defined
        ``IF NOT EXISTS`` (no-op on a live store — #107), a required (non-option) governed column (the
        UPDATE poisons), an emitter that re-declares the trio instead of calling the ONE spec."""
        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            legacy = await _seed_legacy(world, _LEGACY_COUNT)
            await _upgrade_finding_schema(world)
            info = await run(world.connection, f"INFO FOR TABLE {FINDING_TABLE}")
            info_map = info[0] if isinstance(info, list) else info
            fields = set((info_map or {}).get("fields", {}))
            indexes = set((info_map or {}).get("indexes", {}))
            assert {"owner_principal", "owner_agent", "scope"} <= fields, (
                "the governed trio did not land on the populated finding table (kickoff §Scope IN 1): "
                f"{sorted(fields)}"
            )
            assert {f"{FINDING_TABLE}_scope", f"{FINDING_TABLE}_owner_principal"} <= indexes, sorted(indexes)
            await run(
                world.connection,
                f"UPDATE type::record('{FINDING_TABLE}', $id) SET body = 'touched after the retrofit'",
                {"id": legacy[0]},
            )
            row = await finding_row(world.connection, legacy[0])
            assert row["body"] == "touched after the retrofit" and row["scope"] is None, row
            assert len(await run(world.connection, f"SELECT VALUE id FROM {FINDING_TABLE}")) == _LEGACY_COUNT


class TestALegacyFindingIsMemberInvisibleUntilMigrated:
    """F1-b (kickoff §12): BEFORE the verb, the fail-closed read — a member's ``read_filter`` serves 0 of
    the legacy NONE-scope rows, an admin serves all. GREEN at HEAD (``read_filter`` is table-generic) — an
    INSTRUMENT that goes RED the day a build 'helpfully' treats a NONE scope as visible (the §10.1 rule)."""

    async def test_member_sees_none_admin_sees_all(self) -> None:
        from _governed_contract import admin, member  # noqa: PLC0415

        from loremaster import governed  # noqa: PLC0415

        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            await _seed_legacy(world, _LEGACY_COUNT)
            await _upgrade_finding_schema(world)
            from _governed_contract import governed_overlay_ddl  # noqa: PLC0415

            await apply_ddl(world.connection, governed_overlay_ddl(FINDING_TABLE), url=world.env.url)
            project = keep_scope("anyproject")
            for subject, expected in (
                (member(world.operator_bare, "ag_op", frozenset({project})), 0),
                (admin(world.operator_bare, "ag_op"), _LEGACY_COUNT),
            ):
                fragment, params = governed.read_filter(subject, FINDING_TABLE)
                rows = await run(
                    world.connection, f"SELECT VALUE id FROM {FINDING_TABLE} WHERE {fragment}", params
                )
                assert len(rows) == expected, (subject.role, rows)


# =========================================================================== #
# F1-c / F1-f / F1-g / F1-h — the finding leg: UNOWNED-LEGACY, scope-keyed, self-guarding, observed.
# =========================================================================== #


class TestTheFindingMigrateLegIsTheUnownedLegacyShape:
    """F1-c/f/g/h (kickoff §2 + §12 F1 row)."""

    async def test_legacy_rows_get_the_project_scope_and_NO_owner_even_when_created_by_names_an_agent(
        self,
    ) -> None:
        """⚠ RED at HEAD (``migrate_governed`` refuses ``finding`` as unsupported). F1-c + the guess door:
        three legacy rows — one whose ``created_by`` EXACTLY equals a registered agent's name — plus one
        GOVERNED row. After the verb: ``backfilled == 3``; every legacy row NONE/NONE with
        ``scope == keep:<project>``; ``created_by`` bytes intact (a display string, byte-inert — am-22 §4);
        the governed row byte-identical; ``already_migrated == 1``. Kills: a leg stamping an owner from
        ``created_by`` (F1's guess), a leg touching the governed row, a leg rewriting ``created_by``."""
        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            await seed_agent_governed(
                world.connection,
                row_id="ag_lead",
                name="ag-lead",
                session="s64",
                owner_principal=world.operator_bare,
                owner_agent="ag_lead",
                scope=keep_scope("sessionkeep64"),
            )
            legacy = await _seed_legacy(world, _LEGACY_COUNT - 1)
            legacy.append(
                await seed_finding_legacy(
                    world.connection, row_id="legacy_named", number=50, created_by="ag-lead"
                )
            )
            await _upgrade_finding_schema(world)
            await _assert_the_governed_trio_landed(world)
            governed_id = await seed_finding_governed(
                world.connection,
                row_id="already_governed",
                number=60,
                owner_principal=world.operator_bare,
                owner_agent="ag_lead",
                scope=keep_scope("sessionkeep64"),
            )
            governed_before = await run(
                world.connection, f"SELECT * FROM type::record('{FINDING_TABLE}', $id)", {"id": governed_id}
            )
            result = await world.migrate()
            _assert_finding_leg_ran(result)
            assert (result.backfilled, result.already_migrated, result.scanned) == (
                _LEGACY_COUNT,
                1,
                _LEGACY_COUNT + 1,
            ), result
            project = await world.project_scope()
            for row_id in legacy:
                row = await finding_row(world.connection, row_id)
                assert row["scope"] == project, (row_id, row)
                assert row["owner_principal"] is None and row["owner_agent"] is None, (
                    f"F1: a created_by string is NEVER promoted to an owner (got {row!r})"
                )
            assert (await finding_row(world.connection, "legacy_named"))["created_by"] == "ag-lead"
            governed_after = await run(
                world.connection, f"SELECT * FROM type::record('{FINDING_TABLE}', $id)", {"id": governed_id}
            )
            assert governed_after == governed_before, "the migrate touched an already-governed finding"

    async def test_the_migrate_is_idempotent(self) -> None:
        """⚠ RED at HEAD. A second run backfills 0, refuses nothing, and leaves every row byte-identical."""
        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            await _seed_legacy(world, _LEGACY_COUNT)
            await _upgrade_finding_schema(world)
            _assert_finding_leg_ran(await world.migrate())
            before = await world.snapshot()
            again = await world.migrate()
            _assert_finding_leg_ran(again)
            assert again.backfilled == 0 and again.already_migrated == _LEGACY_COUNT, again
            assert await world.snapshot() == before

    async def test_there_is_no_order_precondition_unmigrated_agents_do_not_block_findings(self) -> None:
        """⚠ RED at HEAD. F1-f: a finding has no link to resolve, so the verb carries NO agent-first ORDER
        precondition (63c §6: a precondition with no mechanism behind it is ceremony). Two unmigrated
        (NONE-scope) legacy agents on the store; ``--table finding`` still SUCCEEDS."""
        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            for index in (1, 2):
                await seed_agent_legacy(
                    world.connection,
                    row_id=f"legacy_agent_{index}",
                    name=f"legacy-agent-{index}",
                    session="s64",
                )
            await _seed_legacy(world, _LEGACY_COUNT)
            await _upgrade_finding_schema(world)
            result = await world.migrate()
            _assert_finding_leg_ran(result)
            assert result.backfilled == _LEGACY_COUNT, result

    async def test_report_unmigrated_counts_the_legacy_findings_then_zero(self) -> None:
        """⚠ RED at HEAD (the after-leg: the verb refuses). F1-g: the §2.3 alarm counts 3 before, 0 after."""
        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            await _seed_legacy(world, _LEGACY_COUNT)
            await _upgrade_finding_schema(world)
            assert await report_unmigrated_governed_rows(world.handle, FINDING_TABLE) == _LEGACY_COUNT
            _assert_finding_leg_ran(await world.migrate())
            assert await report_unmigrated_governed_rows(world.handle, FINDING_TABLE) == 0

    async def test_the_executed_backfill_IS_the_scope_keyed_self_guarding_golden_under_the_named_exempt(
        self,
    ) -> None:
        """⚠ RED at HEAD. F1-h + the F5 exempt attribution: observed on the store (the F5 effect observer),
        the finding backfill runs under ``governed_exempt('migrate-governed')`` whose golden IS
        :data:`MIGRATE_FINDING_GOLDEN` (normalised — the classifier's leg 2), entered from
        ``principals._migrate_finding_scope`` (leg 4 — a helper borrowing the token on another frame's
        behalf has a foreign origin), and it CLASSIFIES against :data:`FINDING_TREE_ALLOWLIST` (legs 1–4
        incl. the effect: only ``scope`` moved, the owner pair stays NONE). COVERAGE CHECKED: ≥1 write
        observed (a leg nobody drives cannot be certified)."""
        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            await _seed_legacy(world, _LEGACY_COUNT)
            await _upgrade_finding_schema(world)
            with observe_governed_table_writes(FINDING_TABLE) as writes:
                result = await world.migrate()
            _assert_finding_leg_ran(result)
            assert writes, (
                "no finding write was OBSERVED — the ∀-tables rider cannot certify an unobserved leg"
            )
            for write in writes:
                exempt = write.exempt
                assert getattr(exempt, "name", None) == "migrate-governed", write
                assert _normalise_statement(str(getattr(exempt, "statement", ""))) == _normalise_statement(
                    MIGRATE_FINDING_GOLDEN
                ), write
                assert getattr(exempt, "origin", None) == (_PRINCIPALS_PY, "_migrate_finding_scope"), write
                assert classify_tree_observed_write(write, FINDING_TREE_ALLOWLIST), (
                    f"the observed finding backfill does not CLASSIFY under the finding allowlist: {write!r}"
                )
            where = re.sub(r"\s+", " ", MIGRATE_FINDING_GOLDEN.upper()).rpartition(" WHERE ")[2]
            assert "SCOPE IS NONE" in where and "OWNER_PRINCIPAL IS NONE" in where  # the golden itself (CD-1)


# =========================================================================== #
# The UNOWNED-LEGACY half-pair rule, ∀ {memory, finding} (kickoff §2 RIDER (i)–(iii)).
# =========================================================================== #


async def _seed_owned_unscoped(world: _MigrateWorld, table: str, count: int) -> list[str]:
    """``count`` owned-but-UNSCOPED rows of ``table`` (owner pair set, scope NONE) — the ONE half-pair an
    UNOWNED-LEGACY table's governed create cannot produce. One id is HOSTILE (newlines + a row-shaped
    forgery + backtick runs — the sanitiser leg: a stored id never reaches the served line raw, #484)."""
    ids = [_HOSTILE_TRAP_ID] + [f"trap_{table}_{index}" for index in range(1, count)]
    for index, row_id in enumerate(ids):
        if table == FINDING_TABLE:
            await seed_finding_governed(
                world.connection,
                row_id=row_id,
                number=700 + index,
                owner_principal=world.operator_bare,
                owner_agent="ag_op",
                scope=None,
            )
        else:
            await seed_memory_governed(
                world.connection,
                row_id=row_id,
                dim=_DIM,
                owner_principal=world.operator_bare,
                owner_agent="ag_op",
                scope=None,
            )
    return ids


async def _seed_one_legacy(world: _MigrateWorld, table: str) -> None:
    if table == FINDING_TABLE:
        await seed_finding_legacy(world.connection, row_id="one_legacy", number=1)
    else:
        await seed_memory_legacy(world.connection, row_id="one_legacy", dim=_DIM)


class TestAnOwnedButUnscopedRowIsAHalfPairForEveryUnownedLegacyTable:
    """Kickoff §2 RIDER (i) (+ the disposition quantifier): owned-but-unscoped rows ⇒ ``refused=True``,
    ZERO rows stamped (``SELECT *`` before == after over every table a leg could touch), ONE refusal
    naming the TRUE count + the ids (sanitised) + "half-applied"; receipts serve only what was MEASURED
    (am-22 §4 — ``scanned``/``already_migrated`` are ``None`` on a refusal, ``backfilled`` 0). The
    population always ALSO holds a clean legacy row, so a leg that ignores the trap WOULD stamp."""

    @pytest.mark.parametrize("table", _UNOWNED_LEGACY_TABLES)
    async def test_the_trap_refuses_byte_inert_naming_count_and_ids(self, table: str) -> None:
        """⚠ RED at HEAD — finding: unsupported; memory: the shared UNOWNED-LEGACY precondition is
        unbuilt (it stamps the clean row). Kills: a leg that proceeds past a half-pair; a refusal that
        states a fabricated count; a refusal that leaks a raw control character."""
        async with _migrate_world(current_finding_ddl()) as world:
            from _governed_contract import governed_overlay_ddl  # noqa: PLC0415

            await apply_ddl(world.connection, governed_overlay_ddl(FINDING_TABLE), url=world.env.url)
            trap_ids = await _seed_owned_unscoped(world, table, _TRAP_COUNT)
            await _seed_one_legacy(world, table)
            before = await world.snapshot()
            result = await world.migrate(table)
            after = await world.snapshot()
            reason = str(result.reason or "")
            assert result.refused is True, (
                f"--table {table} PROCEEDED past owned-but-unscoped rows: {result!r}"
            )
            assert before == after, f"--table {table}: the half-pair refusal wrote to the store"
            assert "half-applied" in reason.lower(), reason
            assert _TRAP_COUNT in _stated_integers(reason, identifiers=[*trap_ids, world.operator_bare]), (
                f"the refusal must state the TRUE count ({_TRAP_COUNT}) of owned-but-unscoped rows: "
                f"{reason!r}"
            )
            assert _names(reason, table, trap_ids[1]), f"the refusal must NAME the offending ids: {reason!r}"
            assert CONTROL_CHAR_PATTERN.search(reason) is None, (
                f"a stored id reached the served line raw: {reason!r}"
            )
            assert "\n#998" not in reason, f"the row-shaped forgery escaped the sanitiser: {reason!r}"
            assert result.backfilled == 0 and result.scanned is None and result.already_migrated is None, (
                result
            )

    @pytest.mark.parametrize("table", _UNOWNED_LEGACY_TABLES)
    async def test_CONTROL_without_the_trap_the_same_store_backfills(self, table: str) -> None:
        """POSITIVE CONTROL (a probe needs a control): the SAME population minus the trap migrates, so the
        refusal above is caused by the trap. ⚠ RED at HEAD for ``finding`` (unsupported); GREEN at HEAD
        for ``memory`` (its leg exists) — the discriminator for the memory row's RED above."""
        async with _migrate_world(current_finding_ddl()) as world:
            from _governed_contract import governed_overlay_ddl  # noqa: PLC0415

            await apply_ddl(world.connection, governed_overlay_ddl(FINDING_TABLE), url=world.env.url)
            await _seed_one_legacy(world, table)
            result = await world.migrate(table)
            assert not result.refused and result.backfilled == 1, result

    async def test_a_scoped_but_ownerless_finding_is_the_MIGRATED_state_not_a_half_pair(self) -> None:
        """⚠ RED at HEAD. RIDER (ii) — the DUAL of am-25's message rule, ruled for THIS disposition: a
        ``finding`` with a scope and NO owner is exactly what the leg PRODUCES, so it is NOT refused, it is
        byte-inert, and it counts as ``already_migrated`` (a pin written the other way would forbid the
        table's own migrated state). Two legacy rows beside it are stamped."""
        async with _migrate_world(current_finding_ddl()) as world:
            from _governed_contract import governed_overlay_ddl  # noqa: PLC0415

            await apply_ddl(world.connection, governed_overlay_ddl(FINDING_TABLE), url=world.env.url)
            healthy = await seed_finding_governed(
                world.connection,
                row_id="scoped_ownerless",
                number=80,
                owner_principal=None,
                owner_agent=None,
                scope=keep_scope("someproject"),
            )
            await _seed_legacy(world, 2, start=81)
            healthy_before = await run(
                world.connection, f"SELECT * FROM type::record('{FINDING_TABLE}', $id)", {"id": healthy}
            )
            result = await world.migrate()
            _assert_finding_leg_ran(result)
            assert (result.backfilled, result.already_migrated) == (2, 1), result
            assert (
                await run(
                    world.connection, f"SELECT * FROM type::record('{FINDING_TABLE}', $id)", {"id": healthy}
                )
                == healthy_before
            )


class TestTheFindingLegSharesTheUnownedLegacyPolicyWithMemory:
    """Kickoff §17 DRY row (``_migrate_finding_scope`` — EXTEND the memory leg; "never three bodies"):
    the POLICY (the project-keep mint, the half-pair refusal, the receipts) is ONE function both legs CALL
    (each leg still calls ``resolve_operator_principal`` itself — the 63b-ii-a routing pin). Proven
    structurally here (both legs call a common ``principals`` helper that mints the project keep AND counts
    the table) and by MUTATION in the report (perturb that
    helper → the memory AND finding pins above red together). The per-table backfill LITERAL stays in each
    leg so the L1 static scan still derives both sites and R1 self-containment holds (#444 — a
    dynamically-named table would fire that bound's re-open trigger)."""

    def test_both_legs_call_one_shared_policy_helper(self) -> None:
        """⚠ RED at HEAD (``_migrate_finding_scope`` absent)."""
        import ast  # noqa: PLC0415
        from pathlib import Path  # noqa: PLC0415

        tree = ast.parse(Path(principals.__file__).read_text(encoding="utf-8"))
        functions = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert "_migrate_finding_scope" in functions, (
            "UNBUILT: principals._migrate_finding_scope (kickoff §17 DRY row)"
        )

        def _calls(name: str) -> set[str]:
            names: set[str] = set()
            for node in ast.walk(functions[name]):
                if isinstance(node, ast.Call):
                    target = node.func
                    if isinstance(target, ast.Name):
                        names.add(target.id)
                    elif isinstance(target, ast.Attribute):
                        names.add(target.attr)
            return names

        shared = {
            name
            for name in _calls("_migrate_finding_scope") & _calls("_migrate_memory_scope")
            if name in functions and {"get_or_create_keyed", "_scope_count"} <= _calls(name)
        }
        assert shared, (
            "the finding and memory legs share NO helper that mints the project keep AND counts the "
            "table (the half-pair refusal + receipts policy) — "
            "the UNOWNED-LEGACY policy is cloned, not called (kickoff §17: never three bodies)"
        )


# =========================================================================== #
# DD-3.c Leg A — the DROP lands on a store that already carries the asserts (the #107 direction).
# =========================================================================== #

#: blank shapes per dropped column, TWO values each (empty and whitespace — the trim ASSERT's two faces).
_BLANK_VALUES = ("", " \t ")


class TestTheFindingAssertsDropFromADirtyStore:
    """DD-3.c Leg A (kickoff §12). BASELINE: under the FROZEN asserted DDL every blank shape is REFUSED
    (GREEN — the control that makes 'accepted after the drop' meaningful); after re-applying the CURRENT
    emitter the same raw seed is ACCEPTED, value byte-intact (RED at HEAD — the drop has not landed);
    ``status='urgent'`` is STILL refused (the KEEP guard)."""

    @pytest.mark.parametrize("value", _BLANK_VALUES)
    @pytest.mark.parametrize("column", FINDING_DROPPED_ASSERT_COLUMNS)
    async def test_BASELINE_the_asserted_old_world_refuses_the_blank(self, column: str, value: str) -> None:
        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            with pytest.raises(Exception):  # noqa: B017 - the engine ASSERT violation surface
                await seed_finding_legacy(
                    world.connection, row_id=f"baseline_{column}", number=1, **{column: value}
                )

    async def test_CONTROL_a_clean_row_lands_under_the_asserted_old_world(self) -> None:
        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            assert await seed_finding_legacy(world.connection, row_id="clean", number=1)

    @pytest.mark.parametrize("value", _BLANK_VALUES)
    @pytest.mark.parametrize("column", FINDING_DROPPED_ASSERT_COLUMNS)
    async def test_the_assert_DROPS_and_the_blank_survives_byte_intact(self, column: str, value: str) -> None:
        """⚠ RED at HEAD — the emitter still carries the ASSERT, so the seed after the upgrade RAISES."""
        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            await _upgrade_finding_schema(world)
            try:
                row_id = await seed_finding_legacy(
                    world.connection, row_id=f"blank_{column}", number=2, **{column: value}
                )
            except Exception as error:  # noqa: BLE001 - the RED-at-HEAD surface
                pytest.fail(
                    f"RED (right reason): the `{column}` non-empty ASSERT is STILL on the store after "
                    "re-applying generate_finding_ddl() — the DD-3.c DROP has not landed (the #107 "
                    f"direction). engine: {error}"
                )
            assert (await finding_row(world.connection, row_id))[column] == value

    async def test_the_status_assert_STAYS(self) -> None:
        """GREEN at HEAD AND after the build — the KEEP guard: a build that drops the reader-aligned status
        ASSERT (the wrong build) reds here."""
        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            await _upgrade_finding_schema(world)
            with pytest.raises(Exception):  # noqa: B017 - the engine ASSERT violation surface
                await seed_finding_legacy(world.connection, row_id="junk_status", number=3, status="urgent")


# =========================================================================== #
# DD-3.c Leg B — the REAL migrate survives the legacy violators (the DD-3.c direction).
# =========================================================================== #


async def _seed_five_violators_and_one_clean(world: _MigrateWorld) -> list[str]:
    ids = [
        await seed_finding_legacy(
            world.connection, row_id=f"violator_{column}", number=10 + index, **{column: ""}
        )
        for index, column in enumerate(FINDING_DROPPED_ASSERT_COLUMNS)
    ]
    ids.append(await seed_finding_legacy(world.connection, row_id="clean_legacy", number=20))
    return ids


class TestTheRealFindingMigrateSurvivesLegacyViolators:
    """DD-3.c Leg B (kickoff §12): the five violators the writer would refuse, seeded under the UNBOUNDED
    world, then the CURRENT emitter, then the REAL migrate → all six stamped, every blank byte-intact,
    second run 0. C-CONTROL: over the FROZEN asserted DDL the same migrate RAISES — the instrument can
    see the hazard (a KEEP of any of the five would deny the cutover)."""

    async def test_all_six_are_stamped_and_the_blanks_survive(self) -> None:
        """⚠ RED at HEAD (the finding leg is unsupported)."""
        async with _migrate_world(unbounded_finding_ddl()) as world:
            ids = await _seed_five_violators_and_one_clean(world)
            await _upgrade_finding_schema(world)
            result = await world.migrate()
            _assert_finding_leg_ran(result)
            assert result.backfilled == len(ids), result
            project = await world.project_scope()
            for column, row_id in zip(FINDING_DROPPED_ASSERT_COLUMNS, ids, strict=False):
                row = await finding_row(world.connection, row_id)
                assert row["scope"] == project and row[column] == "", (column, row)
            again = await world.migrate()
            assert not again.refused and again.backfilled == 0, again

    async def test_C_CONTROL_the_frozen_asserted_ddl_makes_the_migrate_RAISE(self) -> None:
        """⚠ RED at HEAD (the finding leg refuses before any UPDATE, so nothing raises). On the build the
        backfill UPDATE re-validates every legacy row (store-ref §1.4) and the frozen non-empty asserts
        abort it — ZERO rows stamped. This is what Leg B would look like had the ruling KEPT them."""
        async with _migrate_world(unbounded_finding_ddl()) as world:
            ids = await _seed_five_violators_and_one_clean(world)
            await apply_ddl(world.connection, frozen_asserted_finding_ddl(), url=world.env.url)
            from _governed_contract import governed_overlay_ddl  # noqa: PLC0415

            await apply_ddl(world.connection, governed_overlay_ddl(FINDING_TABLE), url=world.env.url)
            with pytest.raises(TxnDomainRejectionError):
                await world.migrate()
            for row_id in ids:
                assert (await finding_row(world.connection, row_id))["scope"] is None


class TestAJunkStatusLegacyFindingRefusesTheBackfill:
    """P-F3 — a PINNED KNOWN BOUND (kickoff §12 DD-3.c row; the 63c P-A3 shape). ``status`` is KEPT, so a
    legacy junk-status row REFUSES the finding backfill (ONE statement, ZERO stamped) — BY DESIGN: the
    reader (``FindingStatus`` Literal) could never serve it either. HEAL a real occurrence FIRST with the
    §13.2 three-step protocol: WIDEN ``FINDING_STATUSES`` → HEAL ``UPDATE finding SET status=… WHERE
    status=…`` → NARROW. If you closed this bound deliberately (dropped the status ASSERT), delete this
    pin and say so. Reading chosen (REPORT §FORKS FK-5): the heal protocol rides THIS pin's docstring, as
    63c's P-A3 did; the served refusal is the engine's (the driver redacts the field name — measured on
    ``message`` P-G3), so the status is isolated by CONSTRUCTION via the sibling control."""

    async def test_a_legacy_junk_status_row_refuses_the_real_migrate(self) -> None:
        """⚠ RED at HEAD (the finding leg refuses before the UPDATE). Built: the REAL migrate RAISES and
        both rows stay NONE-scope."""
        async with _migrate_world(unbounded_finding_ddl()) as world:
            await seed_finding_legacy(world.connection, row_id="junk", number=1, status="urgent")
            await seed_finding_legacy(world.connection, row_id="clean", number=2)
            await _upgrade_finding_schema(world)
            with pytest.raises(TxnDomainRejectionError, match=r"\(assert violation\)"):
                await world.migrate()
            for row_id in ("junk", "clean"):
                assert (await finding_row(world.connection, row_id))["scope"] is None

    async def test_CONTROL_a_legal_status_fixture_migrates_cleanly(self) -> None:
        """⚠ RED at HEAD. The SAME two rows with LEGAL statuses (two different values) migrate — so the pin
        above refuses BECAUSE of the junk status."""
        async with _migrate_world(unbounded_finding_ddl()) as world:
            await seed_finding_legacy(world.connection, row_id="ok1", number=1, status="wontfix")
            await seed_finding_legacy(world.connection, row_id="ok2", number=2, status="acknowledged")
            await _upgrade_finding_schema(world)
            result = await world.migrate()
            _assert_finding_leg_ran(result)
            assert result.backfilled == 2, result


class TestTheUnownedLegacySetIsDerivedFromTheGoldens:
    """FK-2 (amendment 7 §3): the half-pair rule's domain is DERIVED — and the derivation is COMPLETE both
    ways:
    every production governed backfill leg (``test_fixwave_a19a_63c_i_a._migrate_legs`` — the functions that
    open ``governed_exempt("migrate-governed", …)``) has a golden here, and every golden names a live leg."""

    def test_the_golden_map_covers_every_derived_leg(self) -> None:
        """⚠ RED at HEAD (``_migrate_finding_scope`` is not a production leg yet — a golden with no leg)."""
        from test_fixwave_a19a_63c_i_a import _migrate_legs  # noqa: PLC0415

        legs = _migrate_legs()
        goldens = set(migrate_goldens())
        assert legs == goldens, (
            f"legs with no golden: {sorted(legs - goldens)}; goldens with no leg: {sorted(goldens - legs)}"
        )

    def test_the_derivation_yields_the_ruled_disposition(self) -> None:
        """GREEN at HEAD AND after: the SET-clause rule yields {memory, finding} (kickoff §2 + am-7 §3's
        stated
        output) — a golden edited to stamp an owner on an unowned leg, or the reverse, moves it."""
        assert set(_UNOWNED_LEGACY_TABLES) == {_MEMORY_TABLE, FINDING_TABLE}, _UNOWNED_LEGACY_TABLES


class TestTheFindingBackfillCountIsMeasured:
    """MP-10 / S-2 (packet-64 amendment 8 §4; 63c amendment 27 FORK-1 ∀ legs): ``backfilled`` is the rows the
    UPDATE STAMPED, MEASURED — never a pre-UPDATE count. The 64b-local twin of a28's ∀-legs pin (whose finding
    population rides §HELD): a concurrent stamp lands BETWEEN the leg's count and its UPDATE (injected on the
    executed golden, through every store seam by identity), so the pre-count (3) ≠ the rows stamped (2)."""

    async def test_backfilled_equals_the_rows_the_update_changed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD (the finding leg is unsupported — the injection never lands, asserted)."""
        from _governed_contract import patch_shared_object_everywhere  # noqa: PLC0415
        from loremaster.store import _txn  # noqa: PLC0415

        async with _migrate_world(frozen_asserted_finding_ddl()) as world:
            await _seed_legacy(world, _LEGACY_COUNT)
            await _upgrade_finding_schema(world)
            landed = {"count": 0}
            golden = _normalise_statement(MIGRATE_FINDING_GOLDEN)
            for name in ("run_query", "execute_transaction", "execute_read_transaction"):
                real = getattr(_txn, name)

                def _wrap(real: Any = real) -> Any:
                    async def _racing(*args: Any, **kwargs: Any) -> Any:
                        statement = str(kwargs.get("statement", args[0] if args else ""))
                        if golden in _normalise_statement(statement) and not landed["count"]:
                            landed["count"] += 1
                            await run(
                                world.connection,
                                f"UPDATE type::record('{FINDING_TABLE}', 'legacy_1') SET scope = 'server'",
                            )
                        return await real(*args, **kwargs)

                    return _racing

                patch_shared_object_everywhere(
                    monkeypatch, name, real, _wrap(), expect_in=("loremaster.store._txn",)
                )
            before = await run(world.connection, f"SELECT * FROM {FINDING_TABLE} ORDER BY id")
            result = await world.migrate()
            after = await run(world.connection, f"SELECT * FROM {FINDING_TABLE} ORDER BY id")
            assert landed["count"] == 1, "the concurrent stamp never landed on the finding backfill (#194)"
            by_id = {str(row["id"]): row for row in before}
            changed = (
                sum(1 for row in after if by_id[str(row["id"])] != row) - 1
            )  # minus the racer's own stamp
            assert changed == _LEGACY_COUNT - 1, f"fixture: {changed} rows stamped by the leg"
            assert result.backfilled == changed, (
                f"backfilled={result.backfilled} but the UPDATE stamped {changed} row(s) — a served count "
                "must be "
                "the rows the statement CHANGED, measured (amendment 8 §4 / 63c amendment 27 FORK-1)"
            )


# =========================================================================== #
# F1 S2 — the REAL production dump (amendment 3 §D-3). Marker-gated on the COMMITTED driver's receipt.
# =========================================================================== #

_RESTORE_DRIVER = Path(__file__).resolve().parents[2] / "scripts" / "restore_prod_dump.py"
_PROD_DUMP_ENV = "LORE_PROD_DUMP_DB"
#: Amendment 4 §D2: the 2026-08-03 dump's measured finding population (probe-64), PASTED as the floor.
_S2_FINDING_FLOOR = 324
_S2_SKIP_REASON = (
    f"S2 needs a restored production dump: run `./scripts/restore_prod_dump.py` (it prints "
    f"`{_PROD_DUMP_ENV}=<name>`), export that line, re-run; reap with `--reap <name>`. Bound + cadence: "
    "docs/design/2026-09-26-packet64-amendment-3.md §D-3 (64b-i/64a close-outs + 65's dress rehearsal)"
)


class TestTheRestoreDriverSliceDecaysForFinding:
    """Amendment 4 §D1 item 1 — 64b-i's instance of the decay pin. ``PENDING_GOVERNED_TABLES`` is a ratified
    hand-list made honest by RED in both directions; the driver's ``--self-test`` carries the general pins
    (a builder item), and THIS packet's slice is: once 64b-i lands the finding trio, ``finding`` is a
    DERIVED governed population (the ONE derivation, ``_governed_contract.governed_populations`` over the
    emitted DDL) and its ``PENDING_GOVERNED_TABLES`` entry is DELETED in the same wave."""

    def test_finding_is_derived_governed_and_has_left_the_pending_list(self) -> None:
        """⚠ RED at HEAD (the trio is unemitted and ``finding`` is still pending)."""
        import importlib.util  # noqa: PLC0415
        import sys  # noqa: PLC0415

        from _enforced_relations_scaffold import emitted_schema_ddl  # noqa: PLC0415
        from _governed_contract import governed_populations  # noqa: PLC0415

        derived = governed_populations(emitted_ddl=emitted_schema_ddl())
        assert FINDING_TABLE in derived, (
            f"finding is not a DERIVED governed population ({sorted(derived)}) — the governed trio is not "
            "in the emitted DDL"
        )
        # The driver's dataclasses resolve their module through ``sys.modules``, so it is loaded REGISTERED
        # (or the already-loaded one reused). An unregistered ``exec_module`` passed only when another test
        # had imported the driver first in the same worker: an ORDER-DEPENDENT pass the mutation
        # instrument caught.
        driver = sys.modules.get("restore_prod_dump")
        if driver is None:
            spec = importlib.util.spec_from_file_location("restore_prod_dump", _RESTORE_DRIVER)
            assert spec is not None and spec.loader is not None, f"cannot load {_RESTORE_DRIVER}"
            driver = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = driver
            spec.loader.exec_module(driver)
        assert FINDING_TABLE not in driver.PENDING_GOVERNED_TABLES, (
            "finding is DERIVED governed yet still listed in PENDING_GOVERNED_TABLES — a decayed entry "
            "(amendment 4 §D1 item 1): delete it in the wave that lands the trio"
        )


async def _assert_no_restored_scope_is_out_of_domain(connection: Any) -> None:
    """packet-64 amendment 9 §2 (c) — the S2 dump leg of the scope DOMAIN (the store ASSERT is WITHDRAWN; this
    leg no longer guards a write-poison, it certifies the real store against the domain every writer now
    enforces): ∀ governed population (DERIVED from the emitted schema), every non-NONE ``scope`` on the REAL
    restored dump is IN THE DOMAIN — the SHAPE (``lorerunes.pdp.scope_shape_ok``) AND, for a ``keep:`` scope,
    a keep row that EXISTS. DUAL (r2 → am-9): r2's shape-only "would be poisoned" leg gains the existence half
    and loses its ASSERT premise."""
    from _enforced_relations_scaffold import emitted_schema_ddl  # noqa: PLC0415
    from _governed_contract import governed_populations  # noqa: PLC0415

    from lorerunes import pdp as pdp_module  # noqa: PLC0415

    scope_shape_ok = vars(pdp_module)["scope_shape_ok"]
    keep_ids = await run(connection, "SELECT VALUE id FROM keep")
    existing_keeps = {keep_scope(bare(row_id)) for row_id in keep_ids}
    out_of_domain = []
    for table in sorted(governed_populations(emitted_ddl=emitted_schema_ddl())):
        values = await run(connection, f"SELECT VALUE scope FROM {table} WHERE scope IS NOT NONE")
        out_of_domain += [
            (table, value)
            for value in values
            if not scope_shape_ok(value)
            or (value.startswith(pdp_module.KEEP_SCOPE_PREFIX) and value not in existing_keeps)
        ]
    assert not out_of_domain, f"production rows whose scope is out of the domain: {out_of_domain[:10]}"


@pytest.mark.skipif(not os.environ.get(_PROD_DUMP_ENV), reason=_S2_SKIP_REASON)
class TestTheRealProductionDumpMigrates:
    """S2 (kickoff §2 F1 + §12 last row; amendment 3 §D-3): over the fleet's REAL legacy findings. Applies
    the CURRENT emitter over the dirty rows (store-ref §1.6 — the new DDL over a store that already has
    rows); BEFORE the verb a member of the (to-be) project household reads 0 legacy findings through
    ``read_filter`` while admin reads N; the REAL ``migrate_governed(table="finding")`` stamps N; AFTER,
    the keeper's household reads EXACTLY the id set admin read before (63-rulings §2.2 byte-diff),
    ``created_by`` is byte-intact on every row, a second run backfills 0, and the §2.3 alarm reads 0.
    The minted DB is the DRIVER's to reap (``--reap``) — this leg never drops it."""

    async def test_the_real_legacy_findings_migrate_into_the_project_keep(self) -> None:
        from _governed_contract import admin, governed_overlay_ddl, member  # noqa: PLC0415

        from loremaster import governed  # noqa: PLC0415

        database = os.environ[_PROD_DUMP_ENV]
        assert database.startswith("test_dump_"), (
            f"{_PROD_DUMP_ENV} must name a driver-minted DB: {database!r}"
        )
        env = make_env(database=database, dim=_DIM)
        principal_store, keep_store = await build_principal_and_keep_stores(env)
        connection = await connect_admin(env)
        try:
            await apply_ddl(connection, current_finding_ddl(), url=env.url)
            await apply_ddl(connection, governed_overlay_ddl(FINDING_TABLE), url=env.url)
            handle, _calls = store_handle(connection, url=env.url)
            operator = await principals.resolve_operator_principal(principal_store)
            if operator is None:  # a pre-62 dump carries no principal: provision the ONE operator (65's step)
                operator = await principal_store.create(email="s2-operator@example.com", role="admin")
            operator_bare = bare_record_key(operator.id)
            legacy_ids = set(
                map(
                    bare_record_key,
                    await run(connection, f"SELECT VALUE id FROM {FINDING_TABLE} WHERE scope IS NONE"),
                )
            )
            assert legacy_ids, "the restored dump carries NO legacy finding — S2 would certify nothing"
            # Amendment 4 §D2 rider — the consumer-side twin of the driver's read-back check: the REQUIRED
            # population is at least the pasted floor (≥, never ==: a fresher export grows it), so a
            # driver regression that restores a PARTIAL table cannot pass unseen.
            restored = await run(connection, f"SELECT VALUE id FROM {FINDING_TABLE}")
            assert len(restored) >= _S2_FINDING_FLOOR, (
                f"the restored dump carries {len(restored)} findings, below the 2026-08-03 floor "
                f"{_S2_FINDING_FLOOR} (amendment 4 §D2) — a partial import read as success"
            )
            created_by_before = {
                bare_record_key(row["id"]): row.get("created_by")
                for row in await run(connection, f"SELECT id, created_by FROM {FINDING_TABLE}")
            }
            admin_fragment, admin_params = governed.read_filter(
                admin(operator_bare, "s2_admin"), FINDING_TABLE
            )
            admin_before = set(
                map(
                    bare_record_key,
                    await run(
                        connection,
                        f"SELECT VALUE id FROM {FINDING_TABLE} WHERE {admin_fragment}",
                        admin_params,
                    ),
                )
            )
            probe_member = member(operator_bare, "s2_member", frozenset({keep_scope("notyetminted")}))
            member_fragment, member_params = governed.read_filter(probe_member, FINDING_TABLE)
            member_before = set(
                map(
                    bare_record_key,
                    await run(
                        connection,
                        f"SELECT VALUE id FROM {FINDING_TABLE} WHERE {member_fragment}",
                        member_params,
                    ),
                )
            )
            assert not (member_before & legacy_ids), (
                "a member saw a NONE-scope legacy finding BEFORE the migrate"
            )
            result = await principals.migrate_governed(
                table=FINDING_TABLE, store=handle, keep_store=keep_store, principal_store=principal_store
            )
            _assert_finding_leg_ran(result)
            assert result.backfilled == len(legacy_ids), result
            project_ids = await run(
                connection, "SELECT VALUE id FROM keep WHERE key = $k", {"k": PROJECT_KEEP_KEY}
            )
            project_scope = keep_scope(bare_record_key(project_ids[0]))
            household = member(operator_bare, "s2_member", frozenset({project_scope}))
            household_fragment, household_params = governed.read_filter(household, FINDING_TABLE)
            household_after = set(
                map(
                    bare_record_key,
                    await run(
                        connection,
                        f"SELECT VALUE id FROM {FINDING_TABLE} WHERE {household_fragment}",
                        household_params,
                    ),
                )
            )
            assert household_after == admin_before, (
                f"the keeper's household does not read back the set admin read before: "
                f"missing {sorted(admin_before - household_after)[:10]}, "
                f"extra {sorted(household_after - admin_before)[:10]}"
            )
            created_by_after = {
                bare_record_key(row["id"]): row.get("created_by")
                for row in await run(connection, f"SELECT id, created_by FROM {FINDING_TABLE}")
            }
            assert created_by_after == created_by_before, "the migrate rewrote a created_by display string"
            again = await principals.migrate_governed(
                table=FINDING_TABLE, store=handle, keep_store=keep_store, principal_store=principal_store
            )
            assert not again.refused and again.backfilled == 0, again
            assert await report_unmigrated_governed_rows(handle, FINDING_TABLE) == 0
            await _assert_no_restored_scope_is_out_of_domain(connection)
        finally:
            await connection.close()
            await keep_store.close()
            await principal_store.close()
