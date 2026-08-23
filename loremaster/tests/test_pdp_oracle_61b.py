"""Contract — the packet-61b-w1 PDP LIVE-STORE ORACLE (the single most important pin in
packet 61). RED before the 61b-w1 build; authored by ``contract-61b-w1`` (session
``pkt61``).

WHY AN ORACLE, NOT A MOCK (Fork A / design §5). The single-brain mechanism is a closed
predicate IR with two total interpreters — ``to_surql`` (emitter) and ``matches`` (Python
evaluator) — walking ONE tree. That gives structural agreement on the predicate SHAPE, but
NOT on what each node MEANS: ``matches`` uses Python ``in``/``==``; ``to_surql`` emits
SurrealQL and the ENGINE decides (NONE handling, ``record<>`` coercion, ``option<>``/
``SELECT *`` traps of store-ref §2). If ``matches`` models the engine wrong, both interpreters
walk one tree and still DISAGREE — ROUTING-IS-NOT-SHARING, the #102 defect wearing an IR.
So the equivalence is PROVEN against the REAL 3.2.4 engine, NEVER a Python mock of SurrealQL
(a mock cannot exhibit the store's real ``IN``/``option<>``/``SELECT *`` semantics — the mock
IS the false-clear this pin prevents).

THE ORACLE (Fork A rider). For a HOSTILE fixture row set (≥2 principals × ≥2 agents each,
EVERY scope value, keep rows IN and OUT of ``$my_keeps``, a ``server`` row, the empty-keeps
case), for EVERY ``(subject, action)``:

    {r.id for r in fixture if authorize(s, a, r).allowed}
        == set(store SELECT id FROM gov WHERE <authorize_filter(s, a, 'gov').to_surql()>)

— BYTE-IDENTICAL id sets, against the REAL test store ``ws://127.0.0.1:18000``.

Two more live pins here:
  * THE READ EMITTER INDEXSCANS (finding #413 / store-ref §2). The member READ predicate,
    with ``scope IN $my_keeps`` EXPANDED to per-keep equality disjuncts and the ``owner_*``
    equalities as ``type::record('principal', $p)`` (bare-string param — lorerunes is
    stdlib-only, no RecordID import), EXPLAINs as an IndexScan with NO TableScan of ``gov`` —
    with positive controls (an unindexed predicate TableScans; a literal ``scope IN $set``
    inside an OR TableScans — the trap the expansion avoids). Separate indexes on ``scope``
    AND ``owner_principal`` (probe E2 — a single composite is leading-column only).
  * THE AUDIT CARVE-OUT ORACLE (Fork G). ``authorize_filter(admin, {mutating}, 'audit')``
    selects ZERO audit rows (the ``NoRows`` node → ``WHERE false``), while the Python
    ``authorize`` denies the same — byte-parity on the carve-out too. admin READ of audit
    still selects all (mutation-only carve-out).

STORE TOPOLOGY / SAFETY: the ``_surreal_harness`` fixtures mint a UNIQUE throwaway database
on the spike TEST store and reap it — NEVER production ``:18500``. record<> owner fields do
NOT enforce endpoint existence (confirmed live in the de-risk probe + store-ref §4), so the
synthetic ``gov`` rows seed without pre-creating principals/agents (that + the ``member_of``
resolver are 61b-w2).

RED DISCIPLINE (#133): the PDP surface is loaded via ``importlib`` (``_pdp()``); this file
collects + typechecks clean while unbuilt.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path
from typing import Any

import pytest
from _surreal_harness import (  # the shared real-SurrealDB harness (env-driven topology)
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.store import surreal_schema  # the module — for the D2 re-home SHARING pins

# --------------------------------------------------------------------------- #
# RED-safe loader (finding #133) — identical to the pure-core file's gate.
# --------------------------------------------------------------------------- #

_PACKAGE = "lorerunes"
_REQUIRED_SYMBOLS = (
    "Action",
    "Subject",
    "Resource",
    "authorize",
    "authorize_filter",
    "SCOPE_AGENT_PRIVATE",
    "SCOPE_PRINCIPAL_PRIVATE",
    "SCOPE_SERVER",
    "keep_scope",
    "PRINCIPAL_ROLE_MEMBER",
    "PRINCIPAL_ROLE_ADMIN",
    "PRINCIPAL_ROLES",
    "AUDIT_TABLE",
    "PRINCIPAL_TABLE",
    "AGENT_TABLE",
    "AllRows",
    "And",
    "NoRows",
    "OwnerPrincipalEq",
    "ScopeInKeeps",
)


def _pdp() -> Any:
    """Return the ``lorerunes`` PDP surface once 61b-w1 builds it, else ``pytest.fail``."""
    package = importlib.import_module(_PACKAGE)
    missing = [name for name in _REQUIRED_SYMBOLS if not hasattr(package, name)]
    if missing:
        pytest.fail(
            f"the 61b-w1 PDP core is not built yet — lorerunes is missing {missing}. "
            "RED before the build (expected pre-GREEN).",
            pytrace=False,
        )
    return package


# --------------------------------------------------------------------------- #
# The synthetic governed table (Fork E owner shape: SEPARATE indexes on scope AND
# owner_principal AND owner_agent — probe E2) + the hostile fixture row set. The
# ids MUST match test_pdp_core._HOSTILE_ROWS so the two files pin the SAME set.
# --------------------------------------------------------------------------- #

_GOV = "gov"
_AUDIT = "audit"  # a synthetic append-trail table for the carve-out oracle (schema is 61a's)

_PRINCIPAL_TABLE = "principal"
_AGENT_TABLE = "agent"

# (id, owner_principal, owner_agent, scope) — the r1..r12 owners are byte-identical to
# test_pdp_core._HOSTILE_ROWS; r13/r14 (F2) add ABSENT-owner (option<> NONE) rows, which the
# pure-core file cannot seed but the store can. None ⟺ the store column is NONE.
_HOSTILE_ROWS: tuple[tuple[str, str | None, str | None, str], ...] = (
    ("r1", "alice", "ag_a", "agent-private"),
    ("r2", "alice", "ag_b", "agent-private"),
    ("r3", "alice", "ag_a", "principal-private"),
    ("r4", "alice", "ag_b", "principal-private"),
    ("r5", "bob", "ag_c", "principal-private"),
    ("r6", "bob", "ag_c", "agent-private"),
    ("r7", "alice", "ag_a", "server"),
    ("r8", "bob", "ag_c", "server"),
    ("r9", "alice", "ag_a", "keep:k1"),
    ("r10", "bob", "ag_c", "keep:k1"),
    ("r11", "alice", "ag_a", "keep:k9"),
    ("r12", "bob", "ag_c", "keep:k9"),
    ("r13", None, None, "server"),  # F2: absent-owner server row (readable by all)
    ("r14", None, None, "agent-private"),  # F2: absent-owner private row (owned by nobody)
)


def _gov_ddl() -> str:
    """Fork-E owner shape: two indexed ``option<record<>>`` owner links (F2 — option<> so an
    absent/unowned row is representable, the §7 grandfathering shape) + an indexed ``scope`` + a
    deliberately UNINDEXED ``note`` (the TableScan positive-control anchor)."""
    return (
        f"DEFINE TABLE {_GOV} SCHEMAFULL;\n"
        f"DEFINE FIELD owner_principal ON {_GOV} TYPE option<record<{_PRINCIPAL_TABLE}>>;\n"
        f"DEFINE FIELD owner_agent ON {_GOV} TYPE option<record<{_AGENT_TABLE}>>;\n"
        f"DEFINE FIELD scope ON {_GOV} TYPE string;\n"
        f"DEFINE FIELD note ON {_GOV} TYPE string;\n"
        f"DEFINE INDEX {_GOV}_owner_principal ON {_GOV} FIELDS owner_principal;\n"
        f"DEFINE INDEX {_GOV}_owner_agent ON {_GOV} FIELDS owner_agent;\n"
        f"DEFINE INDEX {_GOV}_scope ON {_GOV} FIELDS scope;\n"
    )


async def _apply_ddl(connection: Any, ddl: str) -> None:
    """Apply DDL through the production ``execute_transaction`` seam (store-ref §3 — every
    statement's status checked, not the lax ``.query()`` that inspects only statement[0])."""
    from loremaster.store._txn import execute_transaction

    async def _acquire() -> Any:
        return connection

    async def _never_drop(_c: Any) -> None:
        raise AssertionError("a DDL rejection must never drop the connection")

    await execute_transaction(
        f"BEGIN;\n{ddl}COMMIT;\n",
        {},
        acquire=_acquire,
        drop=_never_drop,
        url=connection._url if hasattr(connection, "_url") else "ws://127.0.0.1:18000/rpc",
    )


async def _seed(connection: Any) -> None:
    """Seed ``gov`` (the hostile set) + two synthetic ``audit`` rows (carve-out oracle)."""
    for row_id, principal, agent, scope in _HOSTILE_ROWS:
        if principal is None:
            # F2: an ABSENT-owner row — omit the owner columns so the option<> fields decode NONE.
            await connection.query(
                f"CREATE type::record('{_GOV}', $id) CONTENT {{ scope: $scope, note: $note }}",
                {"id": row_id, "scope": scope, "note": f"n_{row_id}"},
            )
        else:
            await connection.query(
                f"CREATE type::record('{_GOV}', $id) CONTENT {{ "
                f"owner_principal: type::record('{_PRINCIPAL_TABLE}', $op), "
                f"owner_agent: type::record('{_AGENT_TABLE}', $oa), "
                f"scope: $scope, note: $note }}",
                {"id": row_id, "op": principal, "oa": agent, "scope": scope, "note": f"n_{row_id}"},
            )
    await _apply_ddl(connection, f"DEFINE TABLE {_AUDIT} SCHEMALESS;\n")
    for audit_id in ("a1", "a2"):
        await connection.query(
            f"CREATE type::record('{_AUDIT}', $id) CONTENT {{ action: 'DELETE' }}",
            {"id": audit_id},
        )


def _bare_id(record_id: Any) -> str:
    """The bare id of a returned ``id`` cell (``RecordID`` or ``table:id`` string)."""
    text = str(getattr(record_id, "id", record_id))
    return text.split(":", 1)[-1] if ":" in text else text


def _owner_principal_of(row_id: str) -> str | None:
    """The seeded owner_principal of a gov row id (for the #416 leak check)."""
    for rid, principal, _agent, _scope in _HOSTILE_ROWS:
        if rid == row_id:
            return principal
    raise KeyError(row_id)


async def _store_allowed_ids(connection: Any, table: str, predicate: Any) -> set[str]:
    """Run ``SELECT id FROM <table> WHERE <predicate.to_surql()>`` — the store's own verdict."""
    fragment, params = predicate.to_surql()
    rows = await connection.query(f"SELECT id FROM {table} WHERE {fragment}", params)
    materialised = rows if isinstance(rows, list) else []
    return {_bare_id(row["id"]) for row in materialised}


# --------------------------------------------------------------------------- #
# Subjects (identities matching the seeded owners).
# --------------------------------------------------------------------------- #


def _alice_member(pdp: Any) -> Any:
    return pdp.Subject(
        principal_id="alice",
        agent_id="ag_a",
        role=pdp.PRINCIPAL_ROLE_MEMBER,
        visible_keep_ids=frozenset({pdp.keep_scope("k1")}),
    )


def _bob_member(pdp: Any) -> Any:
    return pdp.Subject(
        principal_id="bob",
        agent_id="ag_c",
        role=pdp.PRINCIPAL_ROLE_MEMBER,
        visible_keep_ids=frozenset({pdp.keep_scope("k1")}),  # bob is also in keep k1
    )


def _no_keep_member(pdp: Any) -> Any:
    """A member with the EMPTY keep set — the ScopeInKeeps empty-omission case (Fork A rider)."""
    return pdp.Subject(
        principal_id="alice",
        agent_id="ag_a",
        role=pdp.PRINCIPAL_ROLE_MEMBER,
        visible_keep_ids=frozenset(),
    )


def _two_keep_member(pdp: Any) -> Any:
    """A member with ≥2 keeps — the ONLY subject that actually exercises the #413 IN-EXPANSION
    (F1): ``scope IN $my_keeps`` expands to ``scope=$k0 OR scope=$k1``. A 1-keep monoculture
    can't discriminate the expanded OR (IndexScan) from a literal 2-element IN (TableScan) —
    a 1-element ``IN`` IndexScans, so the trap is invisible at N=1."""
    return pdp.Subject(
        principal_id="alice",
        agent_id="ag_a",
        role=pdp.PRINCIPAL_ROLE_MEMBER,
        visible_keep_ids=frozenset({pdp.keep_scope("k1"), pdp.keep_scope("k9")}),
    )


def _admin(pdp: Any) -> Any:
    return pdp.Subject(
        principal_id="alice",
        agent_id="ag_a",
        role=pdp.PRINCIPAL_ROLE_ADMIN,
        visible_keep_ids=frozenset(),
    )


def _all_subjects(pdp: Any) -> list[tuple[str, Any]]:
    return [
        ("alice/member/keep:k1", _alice_member(pdp)),
        ("bob/member/keep:k1", _bob_member(pdp)),
        ("alice/member/no-keeps", _no_keep_member(pdp)),
        ("alice/member/2-keeps{k1,k9}", _two_keep_member(pdp)),  # F1: exercises the IN-expansion
        ("alice/admin", _admin(pdp)),
    ]


def _python_allowed_ids(
    pdp: Any, subject: Any, action: Any, target_scope: str | None = None
) -> set[str]:
    """The Python ``authorize`` verdict over the hostile set (the matches side)."""
    allowed: set[str] = set()
    for row_id, principal, agent, scope in _HOSTILE_ROWS:
        resource = pdp.Resource(
            table=_GOV, owner_principal=principal, owner_agent=agent, scope=scope
        )
        if pdp.authorize(subject, action, resource, target_scope=target_scope).allowed:
            allowed.add(row_id)
    return allowed


# --------------------------------------------------------------------------- #
# Per-module live database fixture (mirrors the ``admin_db`` harness fixture).
# --------------------------------------------------------------------------- #


@pytest.fixture()
async def oracle_connection() -> Any:
    """A signed-in connection on a fresh unique DB with the seeded ``gov`` + ``audit``
    tables, reaped on exit (NEVER production)."""
    env = make_env(database=unique_database(), dim=512)
    connection = await connect_admin(env)
    try:
        await _apply_ddl(connection, _gov_ddl())
        await _seed(connection)
        yield connection
    finally:
        await connection.close()
        await drop_database(env)


# =========================================================================== #
# ⭐ THE LIVE-STORE ORACLE — byte-identical id sets, engine vs Python, ∀(s, a)
# =========================================================================== #


class TestTheLiveStoreOracle:
    """The load-bearing pin: for every ``(subject, action)``, the Python ``authorize`` set
    EQUALS the store's ``SELECT ... WHERE authorize_filter().to_surql()`` set, byte for byte,
    against the real 3.2.4 engine (Fork A / §5)."""

    async def test_authorize_equals_the_emitted_filter_over_the_store(
        self, oracle_connection: Any
    ) -> None:
        pdp = _pdp()
        mismatches: list[str] = []
        for subject_label, subject in _all_subjects(pdp):
            for action in pdp.Action:
                python_ids = _python_allowed_ids(pdp, subject, action)
                predicate = pdp.authorize_filter(subject, action, _GOV)
                store_ids = await _store_allowed_ids(oracle_connection, _GOV, predicate)
                if python_ids != store_ids:
                    mismatches.append(
                        f"[{subject_label} / {action.name}] python={sorted(python_ids)} "
                        f"store={sorted(store_ids)} "
                        f"(only-python={sorted(python_ids - store_ids)}, "
                        f"only-store={sorted(store_ids - python_ids)})"
                    )
        assert not mismatches, (
            "the single-brain equivalence FAILED — to_surql and matches DISAGREE on the real "
            "engine (a Python mock would have hidden this):\n" + "\n".join(mismatches)
        )

    async def test_empty_keep_set_oracle_holds(self, oracle_connection: Any) -> None:
        """The empty-``$my_keeps`` case specifically (Fork A rider): a member with no keeps
        sees NO keep rows on either side — the ScopeInKeeps omission is engine-correct."""
        pdp = _pdp()
        subject = _no_keep_member(pdp)
        predicate = pdp.authorize_filter(subject, pdp.Action.READ, _GOV)
        store_ids = await _store_allowed_ids(oracle_connection, _GOV, predicate)
        python_ids = _python_allowed_ids(pdp, subject, pdp.Action.READ)
        assert store_ids == python_ids
        assert not (store_ids & {"r9", "r10", "r11", "r12"}), (
            "a member with no keeps must see NO keep-scoped rows"
        )

    @pytest.mark.parametrize(
        ("target_label", "target"),
        [("grantable keep:k1 (alice ∈ k1)", "keep:k1"), ("non-grantable keep:k9 (alice ∉ k9)", "keep:k9")],
    )
    async def test_set_scope_oracle_grantable_and_non_grantable(
        self, oracle_connection: Any, target_label: str, target: str
    ) -> None:
        """D4(b): SET_SCOPE = owner=me AND the TARGET is grantable — the oracle covers it on
        the store too. A grantable target → owner rows; a non-grantable keep → NoRows (zero
        rows both sides)."""
        pdp = _pdp()
        subject = _alice_member(pdp)  # keeps={k1}
        predicate = pdp.authorize_filter(subject, pdp.Action.SET_SCOPE, _GOV, target_scope=target)
        store_ids = await _store_allowed_ids(oracle_connection, _GOV, predicate)
        python_ids = _python_allowed_ids(pdp, subject, pdp.Action.SET_SCOPE, target_scope=target)
        assert store_ids == python_ids, f"SET_SCOPE oracle diverged for {target_label}"
        if target == "keep:k9":
            assert store_ids == set(), "a non-grantable target must select ZERO rows"
        else:
            assert store_ids == {"r1", "r3", "r7", "r9", "r11"}, "grantable → alice-owned rows"


# =========================================================================== #
# #416 (security MEDIUM) — composition-safety: no cross-principal LEAK under an And
# =========================================================================== #


class TestCompositionSafetyNoLeakUnderAnd:
    """#416 (latent cross-principal LEAK in the PUBLIC IR): ``And(OwnerPrincipalEq($p),
    ScopeInKeeps($keeps))`` must NOT return rows owned by OTHER principals. A self-contained
    (parenthesised) ScopeInKeeps keeps the And's owner constraint binding; an unparenthesised twin
    lets a keep disjunct ESCAPE (SQL binds AND tighter than OR) → leaks. Not reachable via 61b's
    entry points, but And/Or/ScopeInKeeps are re-exported and 63/64 compose them — so it is pinned
    on the store, with the leaky twin as the positive control proving the pin can SEE the leak."""

    async def test_and_owner_and_scope_in_keeps_returns_only_the_owners_rows(
        self, oracle_connection: Any
    ) -> None:
        pdp = _pdp()
        predicate = pdp.And(
            (pdp.OwnerPrincipalEq("alice"), pdp.ScopeInKeeps(frozenset({"keep:k1", "keep:k9"})))
        )
        store_ids = await _store_allowed_ids(oracle_connection, _GOV, predicate)
        leaked = {rid for rid in store_ids if _owner_principal_of(rid) != "alice"}
        assert not leaked, (
            f"And(owner=alice, ScopeInKeeps) LEAKED rows owned by others {leaked} — the #416 "
            "cross-principal leak. ScopeInKeeps must emit a self-contained (parenthesised) fragment."
        )
        assert store_ids == {"r9", "r11"}, (
            f"expected exactly alice's keep rows in {{k1,k9}} (r9, r11); got {store_ids}"
        )

    async def test_positive_control_the_unparenthesised_twin_DOES_leak(
        self, oracle_connection: Any
    ) -> None:
        """Proves the store pin can SEE the leak: the leaky (unparenthesised) fragment a buggy
        And-over-unparenthesised-ScopeInKeeps would produce returns a row owned by a DIFFERENT
        principal (r12, bob's keep:k9). Without this control the safety pin could pass vacuously."""
        leaky = (
            "owner_principal = type::record('principal', $p) AND scope = $k0 OR scope = $k1"
        )
        rows = await oracle_connection.query(
            f"SELECT id FROM {_GOV} WHERE {leaky}",
            {"p": "alice", "k0": "keep:k1", "k1": "keep:k9"},
        )
        ids = {_bare_id(row["id"]) for row in (rows if isinstance(rows, list) else [])}
        leaked = {rid for rid in ids if _owner_principal_of(rid) not in (None, "alice")}
        assert leaked, (
            f"the unparenthesised twin did NOT leak — the composition-safety pin would be vacuous. "
            f"ids={ids}"
        )


class TestAbsentOwnerRowsAgree:
    """F2 (Fork-A rider — option<> owner present AND absent): the oracle's hostile fixture carries
    NONE-owner rows (r13 server, r14 agent-private). to_surql (store NULL) and matches (Python None)
    must AGREE on them: a NONE-owner ``server`` row is READable by all; a NONE-owner private row is
    owned by nobody, so no member reads/writes it."""

    async def test_none_owner_rows_agree_across_every_subject_and_action(
        self, oracle_connection: Any
    ) -> None:
        pdp = _pdp()
        none_ids = {"r13", "r14"}
        for subject_label, subject in _all_subjects(pdp):
            for action in (pdp.Action.READ, pdp.Action.WRITE, pdp.Action.DELETE):
                predicate = pdp.authorize_filter(subject, action, _GOV)
                store_ids = await _store_allowed_ids(oracle_connection, _GOV, predicate)
                python_ids = _python_allowed_ids(pdp, subject, action)
                # focus on the NONE rows — the store's NULL vs Python's None must agree
                assert (store_ids & none_ids) == (python_ids & none_ids), (
                    f"absent-owner disagreement [{subject_label}/{action.name}]: "
                    f"store={sorted(store_ids & none_ids)} python={sorted(python_ids & none_ids)}"
                )

    async def test_a_member_reads_the_none_owner_server_row_but_not_the_private_one(
        self, oracle_connection: Any
    ) -> None:
        pdp = _pdp()
        predicate = pdp.authorize_filter(_alice_member(pdp), pdp.Action.READ, _GOV)
        store_ids = await _store_allowed_ids(oracle_connection, _GOV, predicate)
        assert "r13" in store_ids, "a NONE-owner server row is readable by everyone"
        assert "r14" not in store_ids, "a NONE-owner agent-private row is owned by nobody"


# =========================================================================== #
# Finding #413 / store-ref §2 — the READ emitter INDEXSCANS (no TableScan)
# =========================================================================== #


def _operators(plan: Any) -> list[str]:
    """Every ``operator``/``operation`` string in an EXPLAIN plan tree (the shipped
    ``test_keeps_schema.TestTheKeeperIndexFires`` / ``probe_read_filter_61b`` walker)."""
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("operator", "operation"):
                op = node.get(key)
                if isinstance(op, str):
                    found.append(op)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(plan)
    return found


def _scans_table(plan: Any, table: str) -> bool:
    found = False

    def walk(node: Any) -> None:
        nonlocal found
        if isinstance(node, dict):
            attributes = node.get("attributes")
            if (
                node.get("operator") == "TableScan"
                and isinstance(attributes, dict)
                and attributes.get("table") == table
            ):
                found = True
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(plan)
    return found


async def _explain_operators(connection: Any, statement: str, params: dict[str, Any]) -> list[str]:
    plan = await connection.query(f"{statement} EXPLAIN", params)
    return _operators(plan)


async def _explain_plan(connection: Any, statement: str, params: dict[str, Any]) -> Any:
    return await connection.query(f"{statement} EXPLAIN", params)


class TestTheReadEmitterIndexScans:
    """The member READ emitter's SurrealQL is INDEX-served, not a TableScan (finding #413 /
    store-ref §2) — the #107-class hazard (green on a virgin DB, TableScan on a large dirty
    store). With positive controls proving the instrument can SEE a TableScan."""

    async def test_positive_control_unindexed_predicate_tablescans(
        self, oracle_connection: Any
    ) -> None:
        """The plan walker CAN see a TableScan (store-ref §4 — an instrument with no positive
        control can be blind). ``note`` is unindexed."""
        plan = await _explain_plan(
            oracle_connection, f"SELECT id FROM {_GOV} WHERE note = $n", {"n": "n_r1"}
        )
        assert _scans_table(plan, _GOV) and "IndexScan" not in _operators(plan), (
            f"unindexed control did not TableScan — the walker is blind. ops={_operators(plan)}"
        )

    async def test_positive_control_literal_IN_inside_OR_tablescans(
        self, oracle_connection: Any
    ) -> None:
        """THE #413 trap, proven live: a LITERAL ``scope IN $set`` inside an OR TableScans —
        which is exactly why the emitter must EXPAND it. If the emitter regressed to a literal
        ``IN``, THIS is the plan it would produce."""
        plan = await _explain_plan(
            oracle_connection,
            f"SELECT id FROM {_GOV} WHERE scope = 'server' OR scope IN $keeps",
            {"keeps": ["keep:k1", "keep:k9"]},
        )
        assert _scans_table(plan, _GOV), (
            f"expected the literal `IN`-inside-OR to TableScan (#413) — if it no longer does, "
            f"the engine changed and the expansion rationale must be re-probed. ops={_operators(plan)}"
        )

    async def test_member_read_emitter_with_TWO_keeps_indexscans_no_tablescan(
        self, oracle_connection: Any
    ) -> None:
        """F1: the ACTUAL emitted member READ predicate for a ≥2-keep subject (IN expanded to
        ``scope=$k0 OR scope=$k1``, type::record owners) is an IndexScan with NO TableScan of
        ``gov``. This is the store proof that the expansion WORKS at the scale where it matters:
        the literal 2-element ``IN`` inside the OR TableScans (the control below), while THIS
        expanded form IndexScans. A 1-keep subject can't tell them apart (1-element IN IndexScans)."""
        pdp = _pdp()
        predicate = pdp.authorize_filter(_two_keep_member(pdp), pdp.Action.READ, _GOV)
        fragment, params = predicate.to_surql()
        assert " IN " not in f" {fragment} ", (
            f"the emitted READ fragment contains a literal `IN` — the #413 TableScan trap. "
            f"fragment={fragment!r}"
        )
        # the expansion produced ≥2 distinct bound keep values (k1, k9), not a single-element IN
        assert {"keep:k1", "keep:k9"} <= set(params.values()), (
            f"the 2-keep expansion did not bind both keeps as params — fragment={fragment!r}"
        )
        plan = await _explain_plan(
            oracle_connection, f"SELECT id FROM {_GOV} WHERE {fragment}", params
        )
        assert not _scans_table(plan, _GOV), (
            f"the 2-keep member READ emitter TABLESCANS `gov` — the #107 shape (green on a small "
            f"DB, wrong on a large one). fragment={fragment!r} ops={_operators(plan)}"
        )
        assert "IndexScan" in _operators(plan), (
            f"expected an IndexScan for the emitted 2-keep READ predicate. ops={_operators(plan)}"
        )


# =========================================================================== #
# Fork G — the audit carve-out ORACLE (byte-parity on the carve-out too)
# =========================================================================== #


class TestTheAuditCarveOutOracle:
    """admin canNOT mutate audit rows (Fork G / §9), proven against the store: the carve-out
    ``NoRows`` predicate selects ZERO audit rows, matching the Python DENY; admin READ of
    audit selects all (mutation-only carve-out)."""

    @pytest.mark.parametrize("action", ["WRITE", "DELETE", "SET_SCOPE", "SET_OWNER"])
    async def test_admin_mutating_audit_selects_zero_rows(
        self, oracle_connection: Any, action: str
    ) -> None:
        pdp = _pdp()
        predicate = pdp.authorize_filter(_admin(pdp), pdp.Action[action], pdp.AUDIT_TABLE)
        store_ids = await _store_allowed_ids(oracle_connection, _AUDIT, predicate)
        assert store_ids == set(), (
            f"admin {action} on the audit table selected {store_ids} rows — the carve-out "
            "must select ZERO (admin cannot erase its trail)"
        )
        # byte-parity with the Python side
        audit_resource = pdp.Resource(
            table=pdp.AUDIT_TABLE, owner_principal="alice", owner_agent="ag_a", scope=pdp.SCOPE_SERVER
        )
        assert pdp.authorize(_admin(pdp), pdp.Action[action], audit_resource).allowed is False

    async def test_admin_read_of_audit_selects_all_rows(self, oracle_connection: Any) -> None:
        """The carve-out is MUTATION-only — admin READS the trail (§9)."""
        pdp = _pdp()
        predicate = pdp.authorize_filter(_admin(pdp), pdp.Action.READ, pdp.AUDIT_TABLE)
        store_ids = await _store_allowed_ids(oracle_connection, _AUDIT, predicate)
        assert store_ids == {"a1", "a2"}, (
            f"admin READ of audit selected {store_ids} — must select all trail rows"
        )


# =========================================================================== #
# Fork D — the shared-vocabulary drift guard (one-column-one-vocabulary)
# =========================================================================== #


def _module_binds_name_by_import_from(module: Any, name: str, from_prefix: str) -> tuple[bool, bool]:
    """AST-inspect ``module``'s source: does it (imported_from_prefix, assigned_locally)?

    Returns ``(imported, assigned)``: ``imported`` iff a ``from <from_prefix...> import <name>``
    (alias or not) appears; ``assigned`` iff a module-level ``<name> = ...`` assignment appears.
    A private copy is ``(_, assigned=True)``; a re-home is ``(imported=True, assigned=False)``.
    Interning-proof (an ``is`` check on a short string cannot tell a private ``"audit"`` from
    the shared one), so this is the durable D2 guard for the STRING vocab.
    """
    source_file = inspect.getsourcefile(module)
    assert source_file is not None
    tree = ast.parse(Path(source_file).read_text(encoding="utf-8"))
    imported = False
    assigned = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(from_prefix):
            for alias in node.names:
                if alias.name == name:
                    imported = True
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    assigned = True
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            assigned = True
    return imported, assigned


class TestSharedVocabularyIsReHomedInLorerunes:
    """D2 (lead-61 §Fork-D addendum): the principal role domain + the audit table name are ONE
    vocabulary, HOMED in stdlib-only lorerunes and IMPORTED by surreal_schema (lorerunes cannot
    import loremaster, so the shared home MUST be lorerunes — one-column-one-vocabulary). Pinned
    by SHARING (a private copy in surreal_schema REDS), not a drift ``==``. RED at HEAD (the
    re-home is the builder's, pre-authorized); GREEN once surreal_schema imports from lorerunes."""

    def test_principal_roles_are_the_SAME_object_as_lorerunes(self) -> None:
        """Sharing-by-identity (reliable for a TUPLE — not interned): a private copy in
        surreal_schema is a DIFFERENT object → RED. Change ``PRINCIPAL_ROLES`` in lorerunes and
        both the PDP and surreal_schema move together (same object)."""
        pdp = _pdp()
        # getattr, not attribute access: post-re-home ``_PRINCIPAL_ROLES`` is an IMPORTED name
        # in surreal_schema, which mypy's no-implicit-reexport flags on external access — the
        # introspection is deliberate, so name it as such (clean pre- AND post-re-home).
        schema_roles = getattr(surreal_schema, "_PRINCIPAL_ROLES")  # noqa: B009
        assert schema_roles is pdp.PRINCIPAL_ROLES, (
            "surreal_schema._PRINCIPAL_ROLES must BE lorerunes.PRINCIPAL_ROLES (imported, not a "
            "private copy) — one vocabulary, shared with the PDP (D2 re-home). A separate but "
            "equal tuple is a private copy that will drift."
        )

    def test_audit_table_is_imported_from_lorerunes_not_assigned_locally(self) -> None:
        """Sharing-by-structure for the STRING vocab (``is`` is defeated by interning): AST
        proves surreal_schema IMPORTS ``AUDIT_TABLE`` from lorerunes and does NOT assign it
        locally. A private ``AUDIT_TABLE = "audit"`` → assigned=True → RED."""
        pdp = _pdp()
        schema_audit_table = getattr(surreal_schema, "AUDIT_TABLE")  # noqa: B009 - see identity pin
        assert pdp.AUDIT_TABLE == schema_audit_table  # values agree (readable backstop)
        imported, assigned = _module_binds_name_by_import_from(
            surreal_schema, "AUDIT_TABLE", "lorerunes"
        )
        assert imported and not assigned, (
            f"surreal_schema must IMPORT AUDIT_TABLE from lorerunes (imported={imported}) and "
            f"NOT assign it locally (assigned={assigned}) — D2 re-home; a local copy will drift"
        )

    def test_mutating_actions_match_the_audited_action_domain(self) -> None:
        """The PDP's four MUTATING actions == the shipped audit store's ``_AUDITED_ACTIONS``
        (61a). NOT re-homed (the audit ASSERT domain stays in surreal_schema), so this is a
        must-AGREE ``==`` cross-check across two vocabularies: a governed mutation the PDP flags
        ``requires_audit`` must be a value the ``audit.action`` ASSERT accepts. Because the PDP side
        is DERIVED (F4 — all actions − READ), a NEW mutating action that surreal_schema's hand-list
        forgot makes this MISMATCH → RED."""
        pdp = _pdp()
        mutating = {member.name for member in pdp.Action} - {"READ"}
        audited = getattr(surreal_schema, "_AUDITED_ACTIONS")  # noqa: B009 - see the identity pin
        assert mutating == set(audited), f"PDP mutating actions {mutating} != audit domain {set(audited)}"

    @pytest.mark.parametrize("name", ["PRINCIPAL_TABLE", "AGENT_TABLE"])
    def test_governed_table_names_are_imported_from_lorerunes(self, name: str) -> None:
        """R4 (DRY — the D2 pattern extended): the emitter's record-link table names are homed in
        lorerunes and IMPORTED by surreal_schema, not a 2nd copy. AST import-not-assigned guard
        (interning-proof, like AUDIT_TABLE); a private ``PRINCIPAL_TABLE = "principal"`` → RED."""
        pdp = _pdp()
        assert getattr(pdp, name) == getattr(surreal_schema, name)  # noqa: B009 - values agree
        imported, assigned = _module_binds_name_by_import_from(surreal_schema, name, "lorerunes")
        assert imported and not assigned, (
            f"surreal_schema must IMPORT {name} from lorerunes (imported={imported}) and NOT assign "
            f"it locally (assigned={assigned}) — R4 re-home; a local copy is a 2nd definition"
        )
