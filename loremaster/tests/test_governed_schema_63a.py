"""Contract — packet 63a: the GOVERNED store-law DDL (design §4.1) via the ONE emitter, plus
SF-63-4 ``keep.key``. RED before the 63a build; authored by ``contract-63a`` (Opus 4.8 contract
author — tests ONLY, no production logic).

SPEC (executed verbatim, never re-transcribed): ``docs/design/2026-08-28-packet63-retrofit-
rulings.md`` §4.1 (the exact DDL: ``owner_principal option<record<principal>>`` + ``owner_agent
option<record<agent>>`` + ``scope option<string>`` via OVERWRITE; PLAIN IF-NOT-EXISTS indexes on
``scope`` AND ``owner_principal``; ``owner_agent`` NOT indexed — the two-not-three ruling), §2.2 +
SF-63-4 (``keep.key option<string>`` + UNIQUE index), §9.5 (P1/P2/P6 as PINNED EXPLAINs with C+
controls in the SAME test). The probe-63 receipt (``REPORT-probe-63.md``) established these plans
BY CONSTRUCTION on the live 3.2.4 store.

STORE LAW (``docs/reference/surrealdb-31-capabilities.md`` — cited): §1.1 (FIELD OVERWRITE / INDEX
IF NOT EXISTS never OVERWRITE), §1.4 (option<> on a POPULATED table with NO ASSERT/DEFAULT), §1.8
(UNIQUE over option<> = multiple NONE coexist), §2 (#413 IN-in-OR TableScan trap; composite
leading-column-only → two separate indexes), §3 (execute_transaction). ⚠ **P5 CORRECTION** (probe-63,
lead-verified 2026-08-28): the boot ``WHERE scope IS NONE`` count is an **IndexScan** on 3.2.4, NOT a
TableScan — this file pins NO boot-count plan (that is §2.3's migration verb, test_governed_migration_63a).

RED vs CONTROL (fixtures-must-discriminate): the "emits X" pins carry the RED at HEAD (the governed
columns are simply absent); each clause / index pin is a POSITIVE CONTROL or DISCRIMINATOR that names
the WRONG build it reddens. Every EXPLAIN pin carries a C+ control proving the walker can SEE a
TableScan (a pin that cannot see a TableScan is not a pin).

Live TEST store: ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip marker.
"""

from __future__ import annotations

from typing import Any

import pytest
from _governed_contract import (
    MEMORY_TABLE,
    apply_ddl,
    explain,
    field_statement,
    index_statement,
    member,
    operators,
    scans_table,
)
from _surreal_harness import SurrealConnection, SurrealEnv, admin_db  # noqa: F401 - fixture
from loremaster.store import surreal_schema

import lorerunes as pdp

_DIM = 8  # a tiny HNSW width — the scope/owner index plans are dim-independent (probe-63)
_KEEP_TABLE = "keep"
_PRINCIPAL_TABLE = "principal"


def _memory_ddl() -> str:
    return surreal_schema.generate_memory_ddl(dim=_DIM)


def _keep_ddl() -> str:
    return surreal_schema.generate_keep_ddl()


# =========================================================================== #
# LEG 1 — OFFLINE DDL pins over generate_memory_ddl (the ONE emitter). String-level;
# the "emits X" pins carry RED, the clause pins are guarded by them.
# =========================================================================== #


class TestGovernedColumnsAreEmittedOnMemory:
    """§4.1 — the three governed columns land on ``memory`` via the ONE emitter, OVERWRITE,
    option<>, NO ASSERT/DEFAULT. RED at HEAD (``_MEMORY_FIELD_SPECS`` carries none of them)."""

    @pytest.mark.parametrize(
        ("column", "inner_type"),
        [
            ("owner_principal", "option<record<principal>>"),
            ("owner_agent", "option<record<agent>>"),
            ("scope", "option<string>"),
        ],
    )
    def test_the_governed_field_is_emitted_as_option_wrapped(self, column: str, inner_type: str) -> None:
        """⚠ RED at HEAD. §1.4: ``memory`` is a POPULATED table, so a NEW governed field MUST be
        ``option<>`` — a required field poisons every legacy row's next UPDATE and a DEFAULT does
        not rescue it. REDDENS a required-not-option build (and the absent-field HEAD)."""
        statement = field_statement(_memory_ddl(), MEMORY_TABLE, column)
        assert statement is not None, (
            f"generate_memory_ddl emits no DEFINE FIELD for memory.{column} — the governed overlay "
            f"is unbuilt (design §4.1)"
        )
        assert inner_type in statement.replace(" ", ""), (
            f"memory.{column} must be {inner_type} (§1.4 — a required link/field on a POPULATED "
            f"table poisons every legacy row): {statement}"
        )

    @pytest.mark.parametrize("column", ["owner_principal", "owner_agent", "scope"])
    def test_the_governed_field_is_OVERWRITE_not_if_not_exists(self, column: str) -> None:
        """⚠ #107 verbatim (§1.1): IF NOT EXISTS on an existing field is a SILENT no-op, so a
        changed def never migrates a live store. Only OVERWRITE lands. REDDENS an IF-NOT-EXISTS build."""
        statement = field_statement(_memory_ddl(), MEMORY_TABLE, column)
        assert statement is not None, f"unbuilt: memory.{column} (see the emitted pin)"
        assert "OVERWRITE" in statement.upper(), (
            f"memory.{column} must be DEFINE FIELD OVERWRITE (#107): {statement}"
        )
        assert "IF NOT EXISTS" not in statement.upper(), statement

    @pytest.mark.parametrize("column", ["owner_principal", "owner_agent", "scope"])
    def test_the_governed_field_carries_no_assert_and_no_default(self, column: str) -> None:
        """⚠ §1.4 DISCRIMINATOR: an option<> governed column on a POPULATED table must carry NO
        ASSERT and NO DEFAULT — a DEFAULT does not rescue a legacy row (it applies at CREATE) and
        an ASSERT poisons the legacy rows option<> exists to spare. The scope DOMAIN is enforced
        at the WRITE seam (Resource/_is_valid_scope), NOT a store ASSERT (§4.1). REDDENS a build
        that adds a DEFAULT/ASSERT (which would silently write-poison every legacy memory row)."""
        statement = field_statement(_memory_ddl(), MEMORY_TABLE, column)
        assert statement is not None, f"unbuilt: memory.{column} (see the emitted pin)"
        assert "DEFAULT" not in statement.upper(), (
            f"memory.{column} must carry NO DEFAULT (§1.4 — a DEFAULT does not rescue a row): {statement}"
        )
        assert "ASSERT" not in statement.upper(), (
            f"memory.{column} must carry NO ASSERT (§1.4 — an ASSERT poisons the legacy rows "
            f"option<> exists to spare; the scope domain is a WRITE-seam check): {statement}"
        )

    def test_the_governed_fields_route_through_the_shared_emitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ ONE-IMPLEMENTATION, proven by MUTATION (R-a.5 / §3.2 RIDER): nothing REQUIRES the
        memory slice to CALL ``_governed_field_specs`` — a hand-written governed DEFINE FIELD
        would pass every clause pin above while NOT sharing the emitter with message/task/finding.
        Perturb the shared governed emitter; the memory governed field defs must move. RED at HEAD
        (no governed field to move); REDDENS a hand-rolled per-table copy."""
        original = surreal_schema._governed_field_specs

        def _marked() -> tuple[tuple[str, str, str], ...]:
            return tuple(
                (name, type_expr, (constraint + " COMMENT 'gov-emitter-probe'").strip())
                for name, type_expr, constraint in original()
            )

        monkeypatch.setattr(surreal_schema, "_governed_field_specs", _marked)
        statement = field_statement(_memory_ddl(), MEMORY_TABLE, "scope")
        assert statement is not None, (
            "no memory.scope DEFINE FIELD to route-check — the governed overlay is unbuilt OR the "
            "memory slice hand-writes the governed columns instead of calling _governed_field_specs"
        )
        assert "gov-emitter-probe" in statement, (
            "memory.scope does not route through surreal_schema._governed_field_specs — a hand-"
            "written governed column bypasses the ONE emitter (ROUTING-IS-NOT-SHARING, R-a.5)"
        )


class TestGovernedIndexesAreEmittedOnMemory:
    """§4.1 — TWO plain IF-NOT-EXISTS indexes (scope, owner_principal); ``owner_agent`` NOT indexed
    (the #413 leading-column-only fact: separate indexes, not a composite; owner_agent never leads
    a disjunct). RED at HEAD."""

    @pytest.mark.parametrize("column", ["scope", "owner_principal"])
    def test_the_governed_index_is_emitted_plain_if_not_exists(self, column: str) -> None:
        """⚠ RED at HEAD. §1.1: an index is IF NOT EXISTS, never OVERWRITE (OVERWRITE rebuilds
        over every row → boot crash). Plain (non-UNIQUE — a scope/owner value is shared by many
        rows). REDDENS an OVERWRITE or UNIQUE governed index."""
        statement = index_statement(_memory_ddl(), MEMORY_TABLE, column)
        assert statement is not None, (
            f"generate_memory_ddl emits no single-column DEFINE INDEX over memory.{column} — the "
            f"§4.1 read index is unbuilt"
        )
        assert "IF NOT EXISTS" in statement.upper(), statement
        assert "OVERWRITE" not in statement.upper(), statement
        assert "UNIQUE" not in statement.upper(), (
            f"memory.{column} must be a NON-unique read index (a scope/owner is shared): {statement}"
        )

    def test_owner_agent_is_NOT_indexed(self) -> None:
        """⚠ §4.1 THE TWO-NOT-THREE DISCRIMINATOR: ``owner_agent`` is NOT indexed at 63 (it never
        LEADS a read disjunct — it appears only ANDed under scope='agent-private' AND
        owner_principal=…). GREEN at HEAD (absent) and on the correct build; REDDENS a build that
        (wrongly) indexes owner_agent — the named re-open trigger, not a free index. The live C+
        control below proves owner_agent=… alone TableScans."""
        assert index_statement(_memory_ddl(), MEMORY_TABLE, "owner_agent") is None, (
            "memory.owner_agent must NOT carry a single-column index at 63 (§4.1 — it never leads a "
            "read disjunct; the re-open trigger is the first owner_agent-leading LIST read). A build "
            "that indexed it reddens here."
        )

    def test_the_governed_indexes_route_through_the_shared_emitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ ONE-IMPLEMENTATION, proven by MUTATION (R-a.5): perturb the shared governed INDEX
        emitter; memory's governed index statements must move. RED at HEAD; REDDENS hand-rolled
        per-table index copies."""
        original = surreal_schema._governed_index_statements

        def _marked(table: str) -> list[str]:
            return [f"{statement} COMMENT 'gov-index-probe'" for statement in original(table)]

        monkeypatch.setattr(surreal_schema, "_governed_index_statements", _marked)
        statement = index_statement(_memory_ddl(), MEMORY_TABLE, "scope")
        assert statement is not None, (
            "no memory.scope index to route-check — unbuilt OR the memory slice hand-writes the "
            "governed indexes instead of calling _governed_index_statements"
        )
        assert "gov-index-probe" in statement, (
            "memory.scope index does not route through _governed_index_statements — a hand-written "
            "governed index bypasses the ONE emitter (R-a.5)"
        )


# =========================================================================== #
# LEG 2 — LIVE round-trip + the EXPLAIN pins (P1/P2) with C+ controls.
# =========================================================================== #


class TestGovernedColumnsOnTheLiveEngine:
    """The generated DDL against the real engine — the recipe proven on the cake."""

    async def test_a_governed_memory_row_stores_and_reads_back_owner_and_scope(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD — the governed columns are undeclared, so a SCHEMAFULL CREATE that sets
        owner_principal/owner_agent/scope is REJECTED. On a correct build they store and read back."""
        connection, env = admin_db
        await apply_ddl(connection, _memory_ddl(), url=env.url)
        await run_governed_create(connection, row_id="g1", owner="alice", agent="ag_a", scope="server")
        row = _one(
            await _select(
                connection, "SELECT owner_principal, owner_agent, scope FROM type::record('memory', 'g1')"
            )
        )
        assert str(row["owner_principal"]) == f"{_PRINCIPAL_TABLE}:alice", row
        assert str(row["owner_agent"]) == "agent:ag_a", row
        assert row["scope"] == "server", row

    async def test_a_legacy_memory_row_reads_governed_columns_as_none(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ POSITIVE CONTROL / option<> DISCRIMINATOR (§2). A row created WITHOUT the governed
        columns reads them back as None under an EXPLICIT projection — proving option<>. GREEN at
        HEAD (projection of an absent column is None) and on the option<> build; a required build
        REJECTS this ownerless/scopeless CREATE and reddens."""
        connection, env = admin_db
        await apply_ddl(connection, _memory_ddl(), url=env.url)
        await _create_memory_legacy(connection, row_id="leg")
        row = _one(
            await _select(connection, "SELECT owner_principal, scope FROM type::record('memory', 'leg')")
        )
        assert row["owner_principal"] is None and row["scope"] is None, row


class TestTheReadIndexFires:
    """§9.5 / probe-63 P1/P2 — the governed READ predicate is INDEX-served, with C+ controls that
    prove the walker can SEE a TableScan (a pin that cannot see a TableScan is not a pin)."""

    async def test_C_control_unindexed_column_tablescans(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """C+ — the walker CAN see a TableScan (``kind`` is unindexed). GREEN at HEAD."""
        connection, env = admin_db
        await apply_ddl(connection, _memory_ddl(), url=env.url)
        plan = await explain(connection, f"SELECT id FROM {MEMORY_TABLE} WHERE kind = $k", {"k": "fact"})
        assert scans_table(plan, MEMORY_TABLE) and "IndexScan" not in operators(plan), (
            f"the unindexed control did not TableScan — the walker is blind. ops={operators(plan)}"
        )

    async def test_C_control_owner_agent_alone_tablescans_documenting_the_unindexed_bound(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """C+ / §4.1 — ``WHERE owner_agent = $a`` alone TableScans (owner_agent is deliberately
        UNINDEXED at 63). GREEN at HEAD (column absent → TableScan) and on the correct build
        (present but unindexed → TableScan); REDDENS a build that indexed owner_agent."""
        connection, env = admin_db
        await apply_ddl(connection, _memory_ddl(), url=env.url)
        plan = await explain(
            connection,
            f"SELECT id FROM {MEMORY_TABLE} WHERE owner_agent = type::record('agent', $a)",
            {"a": "ag_a"},
        )
        assert scans_table(plan, MEMORY_TABLE), (
            f"owner_agent=… alone must TableScan (unindexed at 63, §4.1) — a build that indexed it "
            f"IndexScans and reddens here. ops={operators(plan)}"
        )

    async def test_P1_scope_equality_indexscans(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD — probe-63 P1: ``WHERE scope = $s`` IndexScans ``memory_scope`` (the one
        genuinely unprobed delta: a plain index on an option<string> scope column, HNSW-co-resident).
        At HEAD scope is undeclared → the plan TableScans. On the correct build → IndexScan."""
        connection, env = admin_db
        await apply_ddl(connection, _memory_ddl(), url=env.url)
        plan = await explain(connection, f"SELECT id FROM {MEMORY_TABLE} WHERE scope = $s", {"s": "server"})
        assert not scans_table(plan, MEMORY_TABLE), (
            f"memory.scope equality TABLESCANS — the §4.1 scope index is unbuilt (the #107 shape: "
            f"green on a virgin DB, a full scan on a large dirty store). ops={operators(plan)}"
        )
        assert "IndexScan" in operators(plan), f"expected an IndexScan on memory_scope. ops={operators(plan)}"

    async def test_P2_the_full_member_read_filter_indexscans_no_tablescan(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD — probe-63 P2: the REAL emitted member READ predicate for a ≥2-keep
        subject (IN expanded to per-keep equalities, #413) is an IndexScan (UnionIndexScan) with NO
        memory TableScan. This is the store proof the §4.1 index set serves the WHOLE PDP filter on
        the real HNSW/FULLTEXT-co-resident table. At HEAD the governed columns are absent → TableScan."""
        connection, env = admin_db
        await apply_ddl(connection, _memory_ddl(), url=env.url)
        subject = member(
            "alice", "ag_a", frozenset({pdp.keep_scope("k1"), pdp.keep_scope("k9")})
        )
        fragment, params = pdp.authorize_filter(subject, pdp.Action.READ, MEMORY_TABLE).to_surql()
        assert " IN " not in f" {fragment} ", (
            f"the emitted READ fragment has a literal IN — the #413 TableScan trap. fragment={fragment!r}"
        )
        plan = await explain(connection, f"SELECT id FROM {MEMORY_TABLE} WHERE {fragment}", params)
        assert not scans_table(plan, MEMORY_TABLE), (
            f"the full member READ filter TABLESCANS memory — the §4.1 read indexes are unbuilt. "
            f"ops={operators(plan)}"
        )
        assert "IndexScan" in operators(plan), f"expected an IndexScan. ops={operators(plan)}"


# =========================================================================== #
# LEG 3 — SF-63-4: keep.key option<string> UNIQUE + the P6 EXPLAIN + coexistence.
# =========================================================================== #


class TestKeepKeyColumnAndIndex:
    """SF-63-4 (§2.2 / §4.1) — the deterministic natural key ``keep.key`` addresses the canonical
    project keep + 63b's session keeps. option<string> (§1.4) + UNIQUE index (§1.8: many NONE keys
    coexist; a real key maps to ≤1 row). RED at HEAD (keep has no key column today)."""

    def test_the_key_field_is_emitted_option_string_overwrite_no_assert(self) -> None:
        """⚠ RED at HEAD. §1.1/§1.4: ``key`` is option<string>, OVERWRITE, no ASSERT/DEFAULT
        (a manual keep carries NONE). REDDENS a required-string or ASSERT build."""
        statement = field_statement(_keep_ddl(), _KEEP_TABLE, "key")
        assert statement is not None, "generate_keep_ddl emits no DEFINE FIELD for keep.key (SF-63-4)"
        collapsed = statement.replace(" ", "")
        assert "option<string>" in collapsed, f"keep.key must be option<string> (§1.4): {statement}"
        assert "OVERWRITE" in statement.upper() and "IF NOT EXISTS" not in statement.upper(), statement
        assert "ASSERT" not in statement.upper() and "DEFAULT" not in statement.upper(), statement

    def test_the_key_index_is_emitted_unique_if_not_exists(self) -> None:
        """⚠ RED at HEAD. §1.1/§1.8: a UNIQUE index over option<string> — the backstop that makes a
        real key map to ≤1 row (multiple NONE keys still coexist). IF NOT EXISTS (never OVERWRITE)."""
        statement = index_statement(_keep_ddl(), _KEEP_TABLE, "key")
        assert statement is not None, "generate_keep_ddl emits no DEFINE INDEX over keep.key (SF-63-4)"
        assert "UNIQUE" in statement.upper(), f"keep.key index must be UNIQUE (SF-63-4 backstop): {statement}"
        assert "IF NOT EXISTS" in statement.upper() and "OVERWRITE" not in statement.upper(), statement

    async def test_P6_key_lookup_indexscans_and_none_keys_coexist(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD — probe-63 P6: after the UNIQUE key index, ``WHERE key = $k`` IndexScans
        ``keep_key``, AND ≥2 keeps with a NONE key COEXIST (§1.8 — the fill-later shape). Seeds two
        keyless keeps + one keyed. At HEAD keep has no key column → the SELECT TableScans (RED)."""
        connection, env = admin_db
        await apply_ddl(connection, _keep_ddl(), url=env.url)
        # two NONE-key keeps (§1.8 coexistence) + one keyed project keep
        await _create_keep(connection, keep_id="k_none1", keeper="p1", keep_type="project", key=None)
        await _create_keep(connection, keep_id="k_none2", keeper="p1", keep_type="session", key=None)
        await _create_keep(connection, keep_id="k_proj", keeper="p1", keep_type="project", key="project:lore")
        coexisting = _one(
            await _select(connection, f"SELECT count() FROM {_KEEP_TABLE} WHERE key IS NONE GROUP ALL")
        )["count"]
        assert coexisting >= 2, (
            f"≥2 NONE-key keeps must COEXIST under the UNIQUE index (§1.8), got {coexisting} — a build "
            f"that treats option<> UNIQUE as SQL 'one NULL only' would reject the 2nd keyless keep"
        )
        plan = await explain(
            connection, f"SELECT id FROM {_KEEP_TABLE} WHERE key = $k", {"k": "project:lore"}
        )
        assert not scans_table(plan, _KEEP_TABLE) and "IndexScan" in operators(plan), (
            f"keep.key lookup must IndexScan keep_key (SF-63-4). ops={operators(plan)}"
        )

    async def test_a_duplicate_non_none_key_is_rejected(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ THE UNIQUE BACKSTOP (§1.8): a real (non-NONE) key maps to ≤1 row. Two keeps with the
        SAME key must not both persist. RED at HEAD (no key column → both persist); on the correct
        build the 2nd CREATE with a duplicate key is REJECTED."""
        connection, env = admin_db
        await apply_ddl(connection, _keep_ddl(), url=env.url)
        await _create_keep(connection, keep_id="p_a", keeper="p1", keep_type="project", key="project:lore")
        with pytest.raises(Exception):  # noqa: B017,PT011 - store UNIQUE rejection (any store error is a pass)
            await _create_keep(
                connection, keep_id="p_b", keeper="p1", keep_type="project", key="project:lore"
            )


# --------------------------------------------------------------------------- #
# local helpers (thin wrappers over the harness ``run`` — memory/keep seeders that
# CREATE the governed columns; RED at HEAD because those columns are undeclared).
# --------------------------------------------------------------------------- #


def _one(rows: Any) -> Any:
    assert rows, f"expected one row, got {rows!r}"
    return rows[0]


async def _select(connection: SurrealConnection, statement: str) -> Any:
    from _surreal_harness import run

    return await run(connection, statement)


async def run_governed_create(
    connection: SurrealConnection, *, row_id: str, owner: str, agent: str, scope: str
) -> Any:
    from datetime import UTC, datetime

    from _surreal_harness import run
    from surrealdb import RecordID

    content = {
        "note_text": "n",
        "kind": "fact",
        "source": {"kind": "test", "ref": None, "trust": "experiential"},
        "created_at": datetime.now(UTC),
        "embedding": [0.0] * _DIM,
        "owner_principal": RecordID(_PRINCIPAL_TABLE, owner),
        "owner_agent": RecordID("agent", agent),
        "scope": scope,
    }
    return await run(
        connection,
        f"CREATE type::record('{MEMORY_TABLE}', $id) CONTENT $content",
        {"id": row_id, "content": content},
    )


async def _create_memory_legacy(connection: SurrealConnection, *, row_id: str) -> Any:
    from datetime import UTC, datetime

    from _surreal_harness import run

    content = {
        "note_text": "n",
        "kind": "fact",
        "source": {"kind": "test", "ref": None, "trust": "experiential"},
        "created_at": datetime.now(UTC),
        "embedding": [0.0] * _DIM,
    }
    return await run(
        connection,
        f"CREATE type::record('{MEMORY_TABLE}', $id) CONTENT $content",
        {"id": row_id, "content": content},
    )


async def _create_keep(
    connection: SurrealConnection, *, keep_id: str, keeper: str, keep_type: str, key: str | None
) -> Any:
    from _surreal_harness import run
    from surrealdb import RecordID

    content: dict[str, Any] = {"keeper": RecordID(_PRINCIPAL_TABLE, keeper), "type": keep_type}
    if key is not None:
        content["key"] = key
    return await run(
        connection,
        f"CREATE type::record('{_KEEP_TABLE}', $id) CONTENT $content",
        {"id": keep_id, "content": content},
    )
