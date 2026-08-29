"""Contract — packet 63a: the DIRTY-STORE MIGRATION (F1) + the ``lore-adm migrate-governed`` verb
(design §1.2 item 5, §2). The #107/#131 headline: a fixture that guarantees a clean slate can never
test what only happens on a dirty store. RED before the 63a build; authored by ``contract-63a``.

SPEC: ``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §2.1 (the memory LegacyMapping:
UNOWNED-LEGACY → owner NONE/NONE, scope = the canonical project keep), §2.2 (the project keep mint,
``key='project:lore'``), §2.3 (BOTH option<> columns AND an explicit idempotent backfill; the boot
WARNING NONE-count; ⚠ P5 CORRECTION — the count query is an IndexScan on 3.2.4, not a TableScan),
§2.6 (the checked agent-first ORDER), §3.2 F1 (the four assertions: survive+writable, member-
invisible/admin-visible BEFORE, project-visible+idempotent AFTER, agent-first order refused).

STORE LAW cited: §1.4 (a NEW field on a POPULATED table MUST be option<> — a required field poisons
every legacy row's next UPDATE + the write-the-legacy-row-UNDER-THE-OLD-DDL fixture trap), §1.6 (the
dirty-store blind spot), §1.8 (option<> keys coexist). The OLD-DDL seed is the store-ref §1.4 trap
verbatim: a fixture that writes its legacy row AFTER the migration cannot see the hazard at all.

⚠ S2 (the design §2.3 REAL-prod-dump integration leg — restore ``/backups/lore/lore-prod-*.surql``
into a throwaway TEST db) is a COMMITTED build-time integration script (an instrument is a
deliverable, like probe-63), NOT pinned here as a unit test (a backup file is an environment
dependency). This module pins the SYNTHETIC S1 unit F1 fully; S2 is a builder/adversary deliverable
flagged in REPORT-contract-63a.md.

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500); per-test unique DB, reaped; NO skip marker.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    MEMORY_TABLE,
    admin,
    apply_ddl,
    build_principal_and_keep_stores,
    governed_overlay_ddl,
    member,
    read_filter_ids,
    seed_memory_legacy,
)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from loremaster.store import surreal_schema

import lorerunes as pdp
from loremaster import governed, principals

_DIM = 8
_EMAIL_ALICE = "alice@example.com"


@pytest_asyncio.fixture()
async def migration_world() -> Any:
    """A DIRTY store: the OLD memory DDL (no governed columns) → a LEGACY memory row seeded UNDER
    IT (store-ref §1.4 trap) → the NEW DDL (memory + the §4.1 governed overlay) applied over it. Plus
    a PrincipalStore/KeepStore with alice (the operator principal / project keeper). The project keep
    is NOT pre-created — ``migrate_governed`` mints it (§2.2). Reaped on exit."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    # OLD world: the memory slice WITHOUT the governed overlay + a legacy row under it.
    await apply_ddl(connection, surreal_schema.generate_memory_ddl(dim=_DIM), url=env.url)
    await seed_memory_legacy(connection, row_id="legacy", dim=_DIM, note_text="a fleet note from before")
    # NEW world: apply the §4.1 governed overlay (the field-add migration — option<> lands on the
    # populated table). On a GREEN build generate_memory_ddl ALSO emits it (idempotent double-apply).
    await apply_ddl(connection, governed_overlay_ddl(MEMORY_TABLE), url=env.url)
    await principal_store.create(email=_EMAIL_ALICE, role="member")
    try:
        yield principal_store, keep_store, connection, env
    finally:
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


async def _migrate_memory(migration_world: Any, *, dry_run: bool = False) -> Any:
    principal_store, keep_store, connection, _env = migration_world
    return await principals.migrate_governed(
        table=MEMORY_TABLE, connection=connection, keep_store=keep_store,
        principal_store=principal_store, dry_run=dry_run,
    )


async def _legacy_scope(connection: Any) -> Any:
    row = await run(connection, f"SELECT scope FROM type::record('{MEMORY_TABLE}', 'legacy')")
    return row[0]["scope"] if row else "<gone>"


# =========================================================================== #
# F1(i) — the legacy row SURVIVES the field-add and stays writable (§1.4 option<> control).
# =========================================================================== #


class TestTheOptionColumnsDoNotPoisonTheLegacyRow:
    """§1.4 — the governed columns are option<> so a NEW field on a POPULATED table does not
    write-poison a legacy row. GREEN at HEAD (the manual overlay IS option<>) + on the correct
    build; REDDENS a build whose governed columns are REQUIRED (or carry a DEFAULT/ASSERT)."""

    async def test_a_legacy_row_survives_the_field_add(self, migration_world: Any) -> None:
        """GREEN CONTROL. The legacy row (written under the OLD DDL) survives the overlay and reads
        its governed columns as NONE (option<> unset; explicit projection, store §2)."""
        _p, _k, connection, _env = migration_world
        row = await run(
            connection,
            f"SELECT note_text, owner_principal, scope FROM type::record('{MEMORY_TABLE}', 'legacy')",
        )
        assert row and row[0]["note_text"] == "a fleet note from before"
        assert row[0]["owner_principal"] is None and row[0]["scope"] is None

    async def test_the_legacy_row_is_still_writable_after_the_field_add(self, migration_world: Any) -> None:
        """⚠ THE §1.4 DISCRIMINATOR (the pin no virgin-DB fixture can carry). After the field-add,
        an UPDATE of an UNRELATED column on the legacy row must SUCCEED — a REQUIRED governed column
        would reject it (``Expected record<principal> but found NONE``). GREEN at HEAD/correct build;
        REDDENS a required-not-option build."""
        _p, _k, connection, _env = migration_world
        await run(
            connection, f"UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET importance = $i", {"i": 0.9}
        )
        row = await run(connection, f"SELECT importance FROM type::record('{MEMORY_TABLE}', 'legacy')")
        assert row and row[0]["importance"] == 0.9


# =========================================================================== #
# F1(ii) — BEFORE the verb: a NONE-scope legacy row is member-INVISIBLE / admin-VISIBLE.
# =========================================================================== #


class TestBeforeTheVerbTheLegacyRowIsFailClosed:
    """§2.3 — before ``migrate-governed`` runs, the legacy row's scope is NONE, so it is INVISIBLE
    to every member (fail-closed) and visible ONLY to admin. This is the direction that makes a
    forgotten backfill LOUD (the fleet loses sight of its own memory) rather than a silent leak."""

    async def test_before_migrate_a_member_cannot_see_the_legacy_row(self, migration_world: Any) -> None:
        """⚠ RED at HEAD (``read_filter`` NotImplementedError). A member's read_filter EXCLUDES the
        NONE-scope legacy row. REDDENS a build whose read path shows a member a NONE-scope row."""
        _p, _k, connection, _env = migration_world
        member_ids = await read_filter_ids(
            connection, member("alice", "ag_a1", frozenset()), _memory_case()
        )
        assert "legacy" not in member_ids, "a member saw a NONE-scope legacy row (must be fail-closed, §2.3)"

    async def test_before_migrate_admin_sees_the_legacy_row(self, migration_world: Any) -> None:
        """⚠ RED at HEAD (``read_filter`` NotImplementedError). Admin (AllRows) DOES see the legacy
        row — it is not lost, only member-invisible until backfilled. REDDENS a build that hides it
        from admin too (then nobody could find it to migrate)."""
        _p, _k, connection, _env = migration_world
        admin_ids = await read_filter_ids(connection, admin("alice", "ag_a1"), _memory_case())
        assert "legacy" in admin_ids, "admin must see the un-migrated NONE-scope legacy row"


# =========================================================================== #
# F1(iii) — the VERB backfills the project keep scope, mints the keep, and is IDEMPOTENT.
# =========================================================================== #


class TestMigrateGovernedBackfillsAndIsIdempotent:
    """§2.1/§2.2/§3.2 F1 — ``migrate-governed --table memory`` backfills the legacy row's scope to
    the canonical project keep and is idempotent (a second run backfills 0)."""

    async def test_the_verb_backfills_the_project_keep_scope(self, migration_world: Any) -> None:
        """⚠ RED at HEAD (``migrate_governed`` NotImplementedError). After the verb the legacy row's
        scope is ``keep:<project>`` (a real, householded keep) — NOT NONE, NOT principal-private, NOT
        a sentinel string. REDDENS a build that leaves the scope NONE or uses a sentinel."""
        principal_store, keep_store, connection, _env = migration_world
        assert await _legacy_scope(connection) is None, "precondition: the legacy row starts NONE-scope"
        result = await _migrate_memory(migration_world)
        assert result.backfilled >= 1, f"the verb must backfill the legacy row, got {result!r}"
        scope = await _legacy_scope(connection)
        assert isinstance(scope, str) and scope.startswith("keep:"), (
            f"the legacy scope must be backfilled to a keep:<project> scope (§2.2), got {scope!r}"
        )
        # the scope names a REAL keep bearing the canonical natural key (§2.2)
        keyed = await run(
            connection, f"SELECT id FROM {surreal_schema.KEEP_TABLE} WHERE key = $k", {"k": "project:lore"}
        )
        assert keyed, "migrate must MINT the canonical project keep with key='project:lore' (§2.2, SF-63-4)"
        assert scope == f"keep:{_bare(str(keyed[0]['id']))}", (
            f"the backfilled scope must name the canonical project keep, got {scope!r} vs {keyed[0]['id']!r}"
        )

    async def test_the_verb_is_idempotent(self, migration_world: Any) -> None:
        """⚠ RED at HEAD. A SECOND run backfills 0 rows and exits clean (already-migrated) — a
        re-run at the cutover, or a crash-and-retry, must not double-write or fail. REDDENS a build
        that re-backfills (or errors) on the second pass."""
        first = await _migrate_memory(migration_world)
        assert first.backfilled >= 1
        second = await _migrate_memory(migration_world)
        assert second.backfilled == 0 and not second.refused, (
            f"the second run must backfill 0 and not refuse (idempotent), got {second!r}"
        )

    async def test_after_migrate_a_project_household_member_sees_the_legacy_row(
        self, migration_world: Any
    ) -> None:
        """⚠ RED at HEAD (migrate + read_filter unbuilt). §2.2 — after the backfill, a member of the
        project keep's HOUSEHOLD sees the legacy row through read_filter (the fleet regains sight of
        its own memory). REDDENS a build that backfills a scope no fleet member is householded in."""
        principal_store, keep_store, connection, _env = migration_world
        await _migrate_memory(migration_world)
        keyed = await run(
            connection, f"SELECT id FROM {surreal_schema.KEEP_TABLE} WHERE key = $k", {"k": "project:lore"}
        )
        assert keyed, "the project keep was not minted"
        project_scope = pdp.keep_scope(_bare(str(keyed[0]["id"])))
        household_member = member("alice", "ag_a1", frozenset({project_scope}))
        visible = await read_filter_ids(connection, household_member, _memory_case())
        assert "legacy" in visible, (
            "a project-household member must SEE the backfilled legacy row (§2.2 — the fleet's shared "
            "memory stays visible after the cutover)"
        )


# =========================================================================== #
# F1(iv) — the agent-first ORDER precondition (§2.6): message before agent REFUSES.
# =========================================================================== #


class TestTheAgentFirstOrderIsChecked:
    """§2.6 — the cutover order is agent → memory → message → brief. ``migrate-governed --table
    message`` BEFORE ``agent`` has been migrated is REFUSED LOUD (messages read
    ``sender.owner_principal``), never a silent partial widening."""

    async def test_migrate_message_before_agent_refuses(self, migration_world: Any) -> None:
        """⚠ RED at HEAD (``migrate_governed`` NotImplementedError). With the ``agent`` table
        un-migrated (its ``owner_principal`` NONE for every agent), ``--table message`` must REFUSE
        (``result.refused`` True with a naming reason, or a raised error) and write NOTHING. REDDENS
        a build that migrates message rows against an un-migrated agent table (they would read a NONE
        owner_principal and land member-invisible — a silent half-migration)."""
        principal_store, keep_store, connection, env = migration_world
        # give the DB an agent table so 'message' migration has an agent population to check.
        from loremaster.agents import AgentRegistry

        registry = AgentRegistry(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        await registry.ensure_ready()
        try:
            # ⚠ NO bare-except: at HEAD ``migrate_governed`` raises NotImplementedError, which must
            # RED here (unbuilt) — NOT be swallowed as a "refusal" (the fixtures-must-discriminate
            # trap: a pin that passes for the wrong reason at HEAD). The contract shape is a RETURNED
            # ``MigrateGovernedResult(refused=True, reason=…)`` (the CLI maps refused → exit non-zero).
            result = await principals.migrate_governed(
                table="message", connection=connection, keep_store=keep_store,
                principal_store=principal_store, registry=registry,
            )
            assert result.refused and not result.backfilled, (
                f"migrate-governed --table message must REFUSE (refused=True, 0 backfilled) before the "
                f"agent table is migrated (§2.6 agent-first ORDER — messages read sender.owner_principal); "
                f"got {result!r}"
            )
            assert result.reason and "agent" in result.reason.lower(), (
                f"the refusal must NAME the agent-first precondition, got reason={result.reason!r}"
            )
        finally:
            await registry.close()


# =========================================================================== #
# The boot WARNING NONE-count (§2.3) + the CLI verb existence.
# =========================================================================== #


class TestTheBootWarningCount:
    """§2.3 — a forgotten backfill is LOUD: a bounded per-governed-table
    ``SELECT count() WHERE scope IS NONE GROUP ALL`` (IndexScan on 3.2.4 — probe-63 P5), logged at
    WARNING with the count + the verb to run, so a silent (None,None)-for-months (#131) cannot
    recur. NOT run at boot silently — surfaced."""

    async def test_a_none_scope_count_is_reported_over_a_dirty_memory_table(
        self, migration_world: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """⚠ RED at HEAD — no boot-count surface exists. The mechanism must exist and report the
        NON-ZERO NONE-scope count for the dirty ``memory`` table (a caplog WARNING carrying the
        count and the ``migrate-governed`` remedy). REDDENS a build with no forgotten-backfill alarm
        (the #131 silent-(None,None) shape). The surface is the builder's (``ensure_ready`` or a
        boot hook); this pins that SOME governed-boot surface reports the count > 0."""
        _p, _k, connection, _env = migration_world
        report = getattr(governed, "report_unmigrated_governed_rows", None)
        assert report is not None, (
            "no governed-boot NONE-scope count surface exists (governed.report_unmigrated_governed_rows) "
            "— §2.3's forgotten-backfill alarm (#131 silent-(None,None) class) is unbuilt"
        )
        with caplog.at_level(logging.WARNING):
            count = await report(connection, MEMORY_TABLE)
        assert count >= 1, f"the dirty memory table has a NONE-scope row; count must be ≥1, got {count}"
        assert any("migrate-governed" in record.getMessage() for record in caplog.records), (
            "the boot NONE-count must WARN with the migrate-governed remedy (a count nobody renders "
            "is a hope; #131)"
        )


class TestTheMigrateGovernedCliVerbExists:
    """§1.2 item 5 — ``lore-adm migrate-governed --table <t> [--dry-run]`` is a real CLI verb."""

    def test_the_parser_accepts_migrate_governed(self) -> None:
        """⚠ RED at HEAD — ``build_parser()`` rejects the unknown subcommand. The builder adds the
        subparser + handler + dispatch. REDDENS the absent verb."""
        parser = principals.build_parser()
        namespace = parser.parse_args(["migrate-governed", "--table", "memory"])
        assert namespace.command == "migrate-governed" and namespace.table == "memory", namespace


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _bare(record_id: str) -> str:
    return record_id.partition(":")[2] or record_id


def _memory_case() -> Any:
    from _governed_contract import GovernedTableCase, seed_memory_governed

    return GovernedTableCase(
        table=MEMORY_TABLE,
        make_ddl=lambda: surreal_schema.generate_memory_ddl(dim=_DIM),
        seed_legacy=seed_memory_legacy,
        seed_governed=seed_memory_governed,
        read_verbs=("recall",),
        write_verbs=("remember", "invalidate"),
    )
