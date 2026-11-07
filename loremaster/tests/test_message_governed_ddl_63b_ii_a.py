"""Contract — packet 63b wave ii-a: §4.F — the ``message`` table's GOVERNED-COLUMN DDL, WIRED
through the ONE shared emitter. Design ``docs/design/2026-09-03-packet63b-design.md`` §4.F (+ §4.1
via the emitter). Authored by ``contract-63b-ii-a`` (Opus 4.8 contract author — CONTRACT TESTS ONLY,
no production).

SPEC (executed verbatim, cited not re-transcribed): §4.F rules that 63b-ii adds
``_governed_field_specs()`` + ``_governed_index_statements(MESSAGE_TABLE)`` to
``surreal_schema._message_statements`` — the three ``option<>`` governed columns (OVERWRITE, NO
ASSERT/DEFAULT) and the TWO plain ``IF NOT EXISTS`` indexes on ``scope`` AND ``owner_principal``
ONLY (``owner_agent`` deliberately NOT indexed — the named re-open trigger). The ``to`` edge gets NO
governed columns (§4.3: policy lives on ``message``); it is an F5 DEPENDENT population (pinned in
``test_message_enforcement_63b_ii_a.py``, not here).

FLAG F-2 (probe ``REPORT-probe-63b-ii.md``, committed 58865ba) DROVE this file's shape: the member
READ filter drives off ``message_scope`` ONLY — ``message_owner_principal`` rides as a RESIDUAL
``Filter``, so an EXPLAIN-of-the-read-filter pin would stay GREEN with ``owner_principal`` MISSING or
mis-typed. So this file PINS THE WIRING (that ``_message_statements`` CALLS both emitters — the
route-through-emitter MUTATION pins) AND carries a DEDICATED single-column ``owner_principal=``
IndexScan control, never only the read-filter plan (the FLAG's two consequences). The probe
(``scripts/probe_read_filter_63.py``, committed) is the DDL-index receipt this contract CITES; these
pins bind the wiring the probe's emitter-output plan cannot.

STORE LAW (``docs/reference/surrealdb-31-capabilities.md`` — cited): §1.1 (FIELD OVERWRITE / INDEX
IF NOT EXISTS never OVERWRITE — an index OVERWRITE rebuilds → boot crash), §1.4 (``option<>`` on a
POPULATED table with NO ASSERT/DEFAULT — a required field OR a DEFAULT poisons every legacy row),
§2 (#413 IndexScan-vs-TableScan via EXPLAIN; the IN-in-OR trap; composite leading-column-only → two
SEPARATE single-column indexes), §3 (execute_transaction validates every statement).

RED vs CONTROL (fixtures-must-discriminate): the "emits X" + "routes through the emitter" pins carry
the RED at HEAD (``_message_statements`` does NOT call ``_governed_field_specs`` /
``_governed_index_statements`` at HEAD — the governed columns/indexes are simply absent). Every
EXPLAIN pin carries a C+ control proving the walker can SEE a TableScan (a pin that cannot see a
TableScan is not a pin).

Live TEST store: ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip marker.
pytest runs ``-n auto``.
"""

from __future__ import annotations

import pytest
from _governed_contract import (
    apply_ddl,
    explain,
    field_statement,
    index_served,
    index_statement,
    member,
    operators,
    scans_table,
)
from _surreal_harness import SurrealConnection, SurrealEnv, admin_db  # noqa: F401 - fixture
from loremaster.store import surreal_schema

import lorerunes as pdp

_MESSAGE_TABLE = surreal_schema.MESSAGE_TABLE  # "message"
_TO_RELATION = surreal_schema.TO_RELATION  # "to"


def _message_ddl() -> str:
    """The REAL current message-slice DDL (the emitter under test). At HEAD it carries NO governed
    columns; on the §4.F build it carries the three governed fields + two governed indexes."""
    return surreal_schema.generate_message_ddl()


# =========================================================================== #
# LEG 1 — OFFLINE DDL pins over generate_message_ddl (the ONE emitter). String-level; the "emits X"
# + "routes through the emitter" pins carry the RED, the clause pins are guarded by them.
# =========================================================================== #


class TestGovernedColumnsAreEmittedOnMessage:
    """§4.F/§4.1 — the three governed columns land on ``message`` via the ONE emitter, OVERWRITE,
    option<>, NO ASSERT/DEFAULT. RED at HEAD (``_message_statements`` emits only the packet-03
    ``_MESSAGE_FIELD_SPECS`` + ``message_seq``/``message_sender_question`` + the ``to`` edge)."""

    @pytest.mark.parametrize(
        ("column", "inner_type"),
        [
            ("owner_principal", "option<record<principal>>"),
            ("owner_agent", "option<record<agent>>"),
            ("scope", "option<string>"),
        ],
    )
    def test_the_governed_field_is_emitted_as_option_wrapped(
        self, column: str, inner_type: str
    ) -> None:
        """⚠ RED at HEAD. §1.4: ``message`` is a POPULATED table (production carries message rows the
        day 03b deploys), so a NEW governed field MUST be ``option<>`` — a required field poisons
        every legacy row's next UPDATE and a DEFAULT does not rescue it. REDDENS a required-not-option
        build AND the absent-field HEAD."""
        statement = field_statement(_message_ddl(), _MESSAGE_TABLE, column)
        assert statement is not None, (
            f"generate_message_ddl emits no DEFINE FIELD for message.{column} — the §4.F governed "
            f"overlay is unwired into _message_statements (design §4.F)"
        )
        assert inner_type in statement.replace(" ", ""), (
            f"message.{column} must be {inner_type} (§1.4 — a required link/field on a POPULATED "
            f"table poisons every legacy row): {statement}"
        )

    @pytest.mark.parametrize("column", ["owner_principal", "owner_agent", "scope"])
    def test_the_governed_field_is_OVERWRITE_not_if_not_exists(self, column: str) -> None:
        """⚠ #107 verbatim (§1.1): IF NOT EXISTS on an existing field is a SILENT no-op, so a changed
        def never migrates a live store. Only OVERWRITE lands. REDDENS an IF-NOT-EXISTS build.
        (Doubly load-bearing on ``message``: the ``to`` edge is already OVERWRITE, so a governed field
        wrongly emitted IF NOT EXISTS would be the ONE non-migrating clause in the slice.)"""
        statement = field_statement(_message_ddl(), _MESSAGE_TABLE, column)
        assert statement is not None, f"unwired: message.{column} (see the emitted pin)"
        assert "OVERWRITE" in statement.upper(), (
            f"message.{column} must be DEFINE FIELD OVERWRITE (#107): {statement}"
        )
        assert "IF NOT EXISTS" not in statement.upper(), statement

    @pytest.mark.parametrize("column", ["owner_principal", "owner_agent", "scope"])
    def test_the_governed_field_carries_no_assert_and_no_default(self, column: str) -> None:
        """⚠ §1.4 DISCRIMINATOR: an option<> governed column on a POPULATED table carries NO ASSERT and
        NO DEFAULT — a DEFAULT does not rescue a legacy row (applies at CREATE) and an ASSERT poisons
        the legacy rows option<> exists to spare. The scope DOMAIN is a WRITE-seam check
        (``Resource``/``_is_valid_scope`` in ``lorerunes.pdp``), never a store ASSERT (§4.1). REDDENS a
        build that adds a DEFAULT/ASSERT (which would write-poison every legacy message row)."""
        statement = field_statement(_message_ddl(), _MESSAGE_TABLE, column)
        assert statement is not None, f"unwired: message.{column} (see the emitted pin)"
        assert "DEFAULT" not in statement.upper(), (
            f"message.{column} must carry NO DEFAULT (§1.4 — a DEFAULT does not rescue a row): {statement}"
        )
        assert "ASSERT" not in statement.upper(), (
            f"message.{column} must carry NO ASSERT (§1.4 — the scope domain is a WRITE-seam check): "
            f"{statement}"
        )

    def test_the_governed_fields_route_through_the_shared_emitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ FLAG F-2 / ONE-IMPLEMENTATION, proven by MUTATION (design §4.F consequence 2; the memory
        twin ``test_the_governed_fields_route_through_the_shared_emitter``): nothing REQUIRES
        ``_message_statements`` to CALL ``_governed_field_specs`` — a HAND-WRITTEN governed DEFINE FIELD
        on message would pass every clause pin above while NOT sharing the emitter with memory/task/
        finding, and a green EXPLAIN-of-the-read-filter probe over a hand-transcribed overlay would
        certify a seam the production DDL never invokes (ROUTING-IS-NOT-SHARING). Perturb the shared
        governed emitter; the message governed field defs MUST move. RED at HEAD (no governed field to
        move — ``_message_statements`` does not call the emitter); REDDENS a hand-rolled per-table copy."""
        original = surreal_schema._governed_field_specs

        def _marked() -> tuple[tuple[str, str, str], ...]:
            return tuple(
                (name, type_expr, (constraint + " COMMENT 'gov-emitter-probe'").strip())
                for name, type_expr, constraint in original()
            )

        monkeypatch.setattr(surreal_schema, "_governed_field_specs", _marked)
        statement = field_statement(_message_ddl(), _MESSAGE_TABLE, "scope")
        assert statement is not None, (
            "no message.scope DEFINE FIELD to route-check — the §4.F overlay is unwired OR the message "
            "slice hand-writes the governed columns instead of calling _governed_field_specs"
        )
        assert "gov-emitter-probe" in statement, (
            "message.scope does not route through surreal_schema._governed_field_specs — a hand-written "
            "governed column bypasses the ONE emitter (ROUTING-IS-NOT-SHARING, FLAG F-2)"
        )


class TestGovernedIndexesAreEmittedOnMessage:
    """§4.F/§4.1 — TWO plain IF-NOT-EXISTS indexes (scope, owner_principal); ``owner_agent`` NOT
    indexed (the #413 leading-column-only fact: two SEPARATE single-column indexes, not a composite;
    owner_agent never leads a read disjunct). RED at HEAD. The names ``message_scope`` /
    ``message_owner_principal`` do NOT collide with the existing ``message_seq`` /
    ``message_sender_question`` (probe F-2 consequence 2 — a clean ADDITIVE change)."""

    @pytest.mark.parametrize("column", ["scope", "owner_principal"])
    def test_the_governed_index_is_emitted_plain_if_not_exists(self, column: str) -> None:
        """⚠ RED at HEAD. §1.1: an index is IF NOT EXISTS, never OVERWRITE (OVERWRITE rebuilds over
        every row → boot crash). Plain (non-UNIQUE — a scope/owner value is shared by many rows).
        REDDENS an OVERWRITE or UNIQUE governed index."""
        statement = index_statement(_message_ddl(), _MESSAGE_TABLE, column)
        assert statement is not None, (
            f"generate_message_ddl emits no single-column DEFINE INDEX over message.{column} — the "
            f"§4.F read index is unwired"
        )
        assert "IF NOT EXISTS" in statement.upper(), statement
        assert "OVERWRITE" not in statement.upper(), statement
        assert "UNIQUE" not in statement.upper(), (
            f"message.{column} must be a NON-unique read index (a scope/owner is shared): {statement}"
        )

    def test_owner_agent_is_NOT_indexed(self) -> None:
        """⚠ §4.1 THE TWO-NOT-THREE DISCRIMINATOR: ``owner_agent`` is NOT indexed at 63 (it never LEADS
        a read disjunct — it appears only ANDed under scope='agent-private' AND owner_principal=…).
        GREEN at HEAD (absent) and on the correct build; REDDENS a build that (wrongly) indexes
        owner_agent — the named re-open trigger, not a free index. The live C+ control below proves
        ``owner_agent=`` alone TableScans (probe F-4 confirmed it on the message table)."""
        assert index_statement(_message_ddl(), _MESSAGE_TABLE, "owner_agent") is None, (
            "message.owner_agent must NOT carry a single-column index at 63 (§4.1 — it never leads a "
            "read disjunct; the re-open trigger is the first owner_agent-leading LIST read). A build "
            "that indexed it reddens here."
        )

    def test_the_governed_indexes_route_through_the_shared_emitter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ FLAG F-2 / ONE-IMPLEMENTATION, proven by MUTATION: perturb the shared governed INDEX
        emitter; message's governed index statements MUST move. RED at HEAD (no governed index to
        move); REDDENS a hand-rolled per-table index copy that bypasses ``_governed_index_statements``."""
        original = surreal_schema._governed_index_statements

        def _marked(table: str) -> list[str]:
            return [f"{statement} COMMENT 'gov-index-probe'" for statement in original(table)]

        monkeypatch.setattr(surreal_schema, "_governed_index_statements", _marked)
        statement = index_statement(_message_ddl(), _MESSAGE_TABLE, "scope")
        assert statement is not None, (
            "no message.scope index to route-check — unwired OR the message slice hand-writes the "
            "governed indexes instead of calling _governed_index_statements"
        )
        assert "gov-index-probe" in statement, (
            "message.scope index does not route through _governed_index_statements — a hand-written "
            "governed index bypasses the ONE emitter (FLAG F-2 / ROUTING-IS-NOT-SHARING)"
        )


class TestTheMessageSliceKeepsItsExistingSchema:
    """THE DUAL (CLAUDE.md rename-law — a delete/replace ships a removed-behavior inventory): the §4.F
    governed additions are ADDITIVE. The packet-03 message schema — the ``message_seq`` +
    ``message_sender_question`` indexes, the native ``message_seq`` SEQUENCE, and the ``to`` edge's
    ``to_in_out`` UNIQUE + ``to_out_seen_at`` plain indexes — MUST SURVIVE. GREEN at HEAD and on the
    correct build; REDDENS a build that REPLACES the message slice rather than extending it (the probe
    F-2 'clean additive change' turned into a pin so a builder cannot regress it while wiring the
    governed overlay). Keyed on the index/relation NAMES (the composites ``message_sender_question`` /
    ``to_in_out`` / ``to_out_seen_at`` are NOT single-column, so ``index_statement`` — which rejects a
    composite by design — cannot see them; a name-presence check does)."""

    @pytest.mark.parametrize(
        "definition_name",
        ["message_seq", "message_sender_question", "to_in_out", "to_out_seen_at"],
    )
    def test_the_preexisting_message_definitions_survive_the_governed_additions(
        self, definition_name: str
    ) -> None:
        """Each pre-63b hot-path index still emits after the governed columns land. GREEN at HEAD and
        on the correct build; REDDENS a build that REPLACES ``_message_statements`` rather than
        EXTENDing it (rename-law removed-behavior inventory)."""
        ddl_lower = _message_ddl().lower()
        assert definition_name in ddl_lower, (
            f"the pre-existing definition {definition_name!r} vanished from the message slice — the "
            f"§4.F governed additions must EXTEND _message_statements, never REPLACE it (rename-law "
            f"removed-behavior inventory)"
        )

    def test_the_to_edge_unique_in_out_index_survives(self) -> None:
        """The ``to_in_out`` UNIQUE(in, out) index — one delivery edge per (message, recipient) pair,
        the fan-out's dedup backstop (store-ref §4) — must survive AS a UNIQUE index. Finds the
        ``to_in_out`` statement and asserts it still carries UNIQUE (a build that downgraded it to a
        plain index, or dropped it, reddens)."""
        to_in_out = [
            statement
            for statement in _message_ddl().split(";")
            if "to_in_out" in statement.lower()
        ]
        assert to_in_out, "the to_in_out index vanished from the message slice (store-ref §4 dedup backstop)"
        assert "unique" in to_in_out[0].lower(), (
            f"the to_in_out index is no longer UNIQUE — a repeated recipient would silently write a "
            f"second edge instead of a loud engine error (store-ref §4): {to_in_out[0].strip()!r}"
        )

    def test_the_to_relation_edge_survives_as_an_enforced_relation(self) -> None:
        """The ``to`` edge stays ``TYPE RELATION … ENFORCED`` (store-ref §4: ENFORCED rejects a
        dangling edge to a phantom recipient; the ii-a governed additions land on ``message``, never on
        ``to``). REDDENS a build that dropped ENFORCED or the relation type while adding governed cols."""
        ddl_upper = _message_ddl().upper()
        assert "TYPE RELATION" in ddl_upper and "ENFORCED" in ddl_upper, (
            "the `to` edge lost its `TYPE RELATION … ENFORCED` clause — the dangling-edge guard "
            "(store-ref §4) must survive the §4.F additions (which touch `message`, not `to`)"
        )


# =========================================================================== #
# LEG 2 — LIVE round-trip + the EXPLAIN pins (P1/P2 + the FLAG F-2 dedicated owner_principal control),
# each with a C+ control proving the walker can SEE a TableScan. No rows are seeded — EXPLAIN plans
# against the schema+indexes; the LIVE proof that the governed columns store/read is the F5 send pins
# (test_message_enforcement_63b_ii_a.py), which observe a REAL send's stamped (owner, scope) — a
# stronger live proof than a hand-CREATE that must reconstruct every required message column.
# Applying generate_message_ddl() itself is the live proof the governed DDL DEFINEs cleanly on the
# real message table (probe: applies standalone on 3.2.4, EXIT=0).
# =========================================================================== #


class TestTheMessageReadIndexFires:
    """§4.F / probe-63b-ii P1/P3/P4 — the governed READ predicate is INDEX-served over ``message``,
    with C+ controls that prove the walker can SEE a TableScan. RED at HEAD (governed columns absent →
    the governed reads TableScan / the DDL apply itself is fine but the columns are undeclared)."""

    async def test_C_control_unindexed_column_tablescans(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """C+ — the walker CAN see a TableScan (``body`` is unindexed). GREEN at HEAD."""
        connection, env = admin_db
        await apply_ddl(connection, _message_ddl(), url=env.url)
        plan = await explain(
            connection, f"SELECT id FROM {_MESSAGE_TABLE} WHERE body = $b", {"b": "x"}
        )
        assert scans_table(plan, _MESSAGE_TABLE) and not index_served(plan), (
            f"the unindexed control did not TableScan — the walker is blind. ops={operators(plan)}"
        )

    async def test_C_control_owner_agent_alone_tablescans_documenting_the_unindexed_bound(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """C+ / §4.1 — ``WHERE owner_agent = $a`` alone TableScans (owner_agent is deliberately
        UNINDEXED at 63 — probe F-4). GREEN at HEAD (column absent → TableScan) and on the correct
        build (present but unindexed → TableScan); REDDENS a build that indexed owner_agent."""
        connection, env = admin_db
        await apply_ddl(connection, _message_ddl(), url=env.url)
        plan = await explain(
            connection,
            f"SELECT id FROM {_MESSAGE_TABLE} WHERE owner_agent = type::record('agent', $a)",
            {"a": "ag_a"},
        )
        assert scans_table(plan, _MESSAGE_TABLE), (
            f"owner_agent=… alone must TableScan (unindexed at 63, §4.1) — a build that indexed it "
            f"IndexScans and reddens here. ops={operators(plan)}"
        )

    async def test_FLAG_F2_owner_principal_equality_indexscans(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD — THE FLAG F-2 DEDICATED CONTROL. The member read filter drives off
        ``message_scope`` ONLY (``owner_principal`` rides as a RESIDUAL Filter), so ONLY this
        single-column ``owner_principal=`` probe proves ``message_owner_principal`` is a live index —
        a wrong column / wrong type on the second index leaves every read-filter probe GREEN. At HEAD
        owner_principal is undeclared → TableScan; on the correct build → IndexScan on
        ``message_owner_principal`` (serves the admin / migrate ``owner_principal``-keyed reads)."""
        connection, env = admin_db
        await apply_ddl(connection, _message_ddl(), url=env.url)
        plan = await explain(
            connection,
            f"SELECT id FROM {_MESSAGE_TABLE} WHERE owner_principal = type::record('principal', $p)",
            {"p": "alice"},
        )
        assert not scans_table(plan, _MESSAGE_TABLE), (
            f"message.owner_principal equality TABLESCANS — the §4.F message_owner_principal index is "
            f"unwired (FLAG F-2: this is the ONLY probe that exercises it). ops={operators(plan)}"
        )
        assert "IndexScan" in operators(plan), (
            f"expected an IndexScan on message_owner_principal. ops={operators(plan)}"
        )

    async def test_P1_scope_equality_indexscans(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD — probe P1: ``WHERE scope = $s`` IndexScans ``message_scope``. At HEAD scope
        is undeclared → TableScan. On the correct build → IndexScan (the #107 shape: green on a virgin
        DB, a full scan on a large dirty store, unless the index is wired)."""
        connection, env = admin_db
        await apply_ddl(connection, _message_ddl(), url=env.url)
        plan = await explain(
            connection, f"SELECT id FROM {_MESSAGE_TABLE} WHERE scope = $s", {"s": "keep:k1"}
        )
        assert not scans_table(plan, _MESSAGE_TABLE), (
            f"message.scope equality TABLESCANS — the §4.F scope index is unwired. ops={operators(plan)}"
        )
        assert "IndexScan" in operators(plan), (
            f"expected an IndexScan on message_scope. ops={operators(plan)}"
        )

    async def test_P3_the_full_member_read_filter_indexscans_no_tablescan(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD — probe P3: the REAL emitted member READ predicate for a ≥2-keep subject (IN
        EXPANDED to per-keep equalities, #413) is index-served (3.2: UnionIndexScan > IndexScan; 3.3:
        BitmapOr > BitmapIndexScan — ``index_served``) with NO message TableScan. This is the store
        proof the §4.F index set serves the WHOLE PDP filter on the real message table. At HEAD the
        governed columns are absent → TableScan. The fragment must carry NO literal ``IN`` (the
        #413 IN-in-OR trap — probe F-3 confirmed the emitter expands keeps)."""
        connection, env = admin_db
        await apply_ddl(connection, _message_ddl(), url=env.url)
        subject = member(
            "alice", "ag_a", frozenset({pdp.keep_scope("k1"), pdp.keep_scope("k9")})
        )
        fragment, params = pdp.authorize_filter(subject, pdp.Action.READ, _MESSAGE_TABLE).to_surql()
        assert " IN " not in f" {fragment} ", (
            f"the emitted READ fragment has a literal IN — the #413 TableScan trap. fragment={fragment!r}"
        )
        plan = await explain(connection, f"SELECT id FROM {_MESSAGE_TABLE} WHERE {fragment}", params)
        assert not scans_table(plan, _MESSAGE_TABLE), (
            f"the full member READ filter TABLESCANS message — the §4.F read indexes are unwired. "
            f"ops={operators(plan)}"
        )
        assert index_served(plan), f"expected an index-served plan. ops={operators(plan)}"
