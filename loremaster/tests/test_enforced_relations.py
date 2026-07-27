"""Contract tests for packet 04a — **the `ENFORCED` sweep (#105)**.

Scope (deliberately narrow — this is 04**a**): flipping `ENFORCED` onto the three
relation edge tables that lack it (``briefed`` / ``refers`` / ``answers_to``), the
DIRTY-STORE migration that makes the flip actually LAND, the app-level check that is
the only layer able to TEACH, and the ONE derivation condition the ``refers`` /
``answers_to`` verdict rests on.  **NOT in scope:** the ``blocks`` task-DAG edge, the
fleet message columns, ``_comms_footer``, #219 — all packet 04**b**.

Binding spec, in the order it must be read:

* ``docs/plans/v2/04-comms-blocks-footer.md`` — the packet, §"#105 — THE ``ENFORCED``
  SWEEP" and the 2026-07-26 operator ruling *"None of the comms package is in use.
  Change whatever."*
* ``docs/plans/v2/receipts/2026-07-26-packet04/REPORT-probe-pkt04-store.md`` — every
  store fact this file relies on, MEASURED on spike-surreal ``surrealdb-3.2.1``
  2026-07-26.  Cited by section (§2 = P1, §3 = P2/P2b, §6 = P5, §10 = P5b).  **This
  file re-probes nothing.**
* ``docs/plans/v2/receipts/2026-07-26-packet04/REPORT-scout-pkt04-seams.md`` §S4 — the
  dirty-store pin idiom these pins clone, §S5/§S6 — the ``briefed`` exposure map.
* ``docs/reference/surrealdb-31-capabilities.md`` §1.1 (the RELATION-TABLE row),
  §1.2 (``OVERWRITE`` = FULL REPLACE), §1.6 (the virgin-DB blind spot), §3 (the SDK
  validates ``statement[0]`` only), §4 (the ``ENFORCED`` adoption table), §6.4 (the
  vendor's "dangling edges read as ``[]``" claim is FALSE).

Two shapes in here are worth naming before you read the assertions, because they are
what makes this a contract rather than decoration:

**1. Everything universal is stated as a ∀ over what the EMITTER emits, never as a
list of edge names.**  ``test_EVERY_relation_table_the_schema_emits_is_ENFORCED``
sweeps every DDL generator and parses the ``DEFINE TABLE … TYPE RELATION`` statements
out of the text, so packet 04b's ``blocks`` edge is pinned the day it is written and a
fifth edge cannot be added un-guarded.  Repo law: *when you catch yourself enumerating
what is FORBIDDEN you have already lost — allowlist the safe, or quantify.*  The four
per-edge pins beside it exist for a different job: they are the DECLARED-RED set of the
group-C mutation proof (see this module's ``MUTATION_PROOF`` block).

**2. The old world is DERIVED from the production emitter, never hand-written.**
:func:`_old_world_ddl` re-emits a slice with the target relation's ``DEFINE TABLE``
replaced by ``_define_relation_table(rel, in_t, out_t, enforced=False)`` — the same
self-checking trick ``test_surreal_store.py::_brief_ddl_before_the_via_widening`` uses.
A hand-written old-DDL string is how a migration pin rots into a test of its own copy
of the code (scout §S4).

RED-BY-DESIGN.  Against the tree at ``28387a0`` this file is RED, deliberately, in the
pins that describe the CHANGE — and GREEN in the ones that describe a CONTROL or a
preserved behaviour.  Which is which is stated in every class docstring, because a
contract whose author cannot say why each pin is red today has not written a contract.

⚠ **ONE PRE-EXISTING CONTRACT FILE STRUCTURALLY CONTRADICTS THIS ONE, AND FIXING IT IS
OUTSIDE THIS FILE'S WRITABLE SET.**  ``test_brief_ledger.py``'s ``brief_ledger_factory``
applies ``generate_brief_ddl()`` and NOTHING ELSE, so the ``agent`` table never exists
in that file and **every ``briefed`` edge its suite writes is a DANGLING edge to an
agent row that was never created** (29 collected ``[real]`` ids, derived 2026-07-26 —
see ``REPORT-contract-04a-enforced.md`` §"WHAT I COULD NOT DETERMINE"/D1).  After the
``briefed`` flip every one of them fails.  Its sibling ``test_message_ledger.py``
already seeds real agent rows (``_seed_agents``) precisely because ``to`` is already
``ENFORCED``; the brief-ledger fixture needs the same treatment, and that edit belongs
to whoever lands the flip.
"""

from __future__ import annotations

import re
import textwrap
import uuid
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
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
from loremaster.graph import CodeGraph
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.store._txn import execute_transaction
from loremaster.store.surreal import SurrealStoreError, _SurrealConnection
from loremaster.store.surreal_schema import (
    AGENT_TABLE,
    ANSWERS_TO_RELATION,
    BRIEF_TABLE,
    BRIEFED_RELATION,
    CODE_NODE_TABLE,
    MESSAGE_TABLE,
    NAME_TABLE,
    REFERS_RELATION,
    TO_RELATION,
    _define_relation_table,
    generate_agent_ddl,
    generate_brief_ddl,
    generate_ddl,
    generate_finding_ddl,
    generate_graph_ddl,
    generate_manifest_ddl,
    generate_memory_ddl,
    generate_message_ddl,
    generate_task_ddl,
)
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker
from pydantic import SecretStr
from surrealdb import RecordID

# --------------------------------------------------------------------------- #
# LAZY access to packet 04a's own additions.
#
# ⚠ CALL-TIME IMPORTS ON PURPOSE, for the SHARED unknown-agent policy module that
# does not exist yet.  A module-level import of it makes this whole file
# UNCOLLECTABLE at clean HEAD — deleting every pin below from the run — rather than
# RED.  Those are different states and the uncollectable one is the dangerous one
# (finding #133; the same note guards ``test_comms_schema.py`` and
# ``test_message_ledger.py``).  Every BEHAVIOURAL pin below is written against the
# EXISTING public surface and needs none of this, on purpose: only the two DRY pins
# in section E reach for it.
# --------------------------------------------------------------------------- #

#: The module the shared "reject unknown agents" policy must live in.  A NEW module
#: rather than a method on either ledger, cloning the ``loremaster.agent_ref``
#: precedent verbatim: a ledger owning the shared object would force its sibling to
#: import IT, reintroducing exactly the coupling ``briefs.py``'s own decoupling law
#: ("the ledger never imports its neighbours") exists to prevent.
SHARED_POLICY_MODULE = "loremaster.agent_existence"

#: The name BOTH ledgers must import the shared policy under.  This IS a name-keyed
#: handle and it is here on purpose: a mutation proof needs a mutation POINT, and a
#: mutation point has a name (repo law: prove sharing by MUTATION, never by
#: inspection).  It fails CLOSED — a module missing the attribute reddens rather
#: than silently skipping.  Renaming it is legal; it costs one edit, HERE.
SHARED_POLICY_ATTR = "reject_unknown_agents"


def _shared_policy() -> Any:
    """The packet-04a shared unknown-agent policy module, imported at CALL time."""
    import importlib

    return importlib.import_module(SHARED_POLICY_MODULE)


# =========================================================================== #
# Vocabulary — the four relation edges the schema emits, and their endpoints.
# =========================================================================== #

#: Every DDL generator that could emit a ``TYPE RELATION`` table, labelled.  The ∀
#: pin sweeps THIS, so a new slice generator is added here once and every relation
#: table it emits is guarded from birth.
_ALL_DDL_GENERATORS: dict[str, Callable[[], str]] = {
    "generate_ddl": lambda: generate_ddl(dim=_MIGRATION_DIM),
    "generate_manifest_ddl": generate_manifest_ddl,
    "generate_memory_ddl": lambda: generate_memory_ddl(dim=_MIGRATION_DIM),
    "generate_task_ddl": generate_task_ddl,
    "generate_finding_ddl": generate_finding_ddl,
    "generate_agent_ddl": generate_agent_ddl,
    "generate_brief_ddl": generate_brief_ddl,
    "generate_message_ddl": generate_message_ddl,
    "generate_graph_ddl": generate_graph_ddl,
}

#: The relation edges that exist at packet 04a, as ``edge -> (in_table, out_table)``.
#: An EXACT-SET pin below reads this, so adding a fifth edge (04b's ``blocks``) is a
#: deliberate act with a teaching failure message, never a silent one.
_KNOWN_RELATION_EDGES: dict[str, tuple[str, str]] = {
    BRIEFED_RELATION: (AGENT_TABLE, BRIEF_TABLE),
    TO_RELATION: (MESSAGE_TABLE, AGENT_TABLE),
    REFERS_RELATION: (CODE_NODE_TABLE, NAME_TABLE),
    ANSWERS_TO_RELATION: (CODE_NODE_TABLE, NAME_TABLE),
}

#: A tiny embedding width: every pin here exercises DDL or edge semantics, never
#: recall, and ``generate_ddl``/``generate_memory_ddl`` build HNSW indexes.
_MIGRATION_DIM = 8

_ENFORCED_CLAUSE = "ENFORCED"

_DEFINE_RELATION_RE = re.compile(
    r"^DEFINE TABLE (?:OVERWRITE |IF NOT EXISTS )?(?P<name>\S+) TYPE RELATION\b"
)


def _statements(ddl: str) -> list[str]:
    """Split a generated DDL blob into its individual statements."""
    return [statement.strip() for statement in ddl.split(";") if statement.strip()]


def _relation_table_statements(ddl: str) -> dict[str, str]:
    """``{edge name: its DEFINE TABLE statement}`` for every relation table in ``ddl``."""
    found: dict[str, str] = {}
    for statement in _statements(ddl):
        match = _DEFINE_RELATION_RE.match(statement)
        if match is not None:
            found[match.group("name")] = statement
    return found


def _every_emitted_relation_table() -> dict[str, tuple[str, str]]:
    """``{edge: (generator label, its DEFINE TABLE statement)}`` across ALL generators.

    The ∀ instrument.  It reads the emitted TEXT rather than a hand-list of edge
    names, so a relation table added by any generator — including one nobody thought
    to tell this file about — is swept.
    """
    emitted: dict[str, tuple[str, str]] = {}
    for label, generator in _ALL_DDL_GENERATORS.items():
        for edge, statement in _relation_table_statements(generator()).items():
            emitted[edge] = (label, statement)
    return emitted


def _is_enforced(statement: str) -> bool:
    """Whether a ``DEFINE TABLE … TYPE RELATION`` statement carries ``ENFORCED``."""
    return f" {_ENFORCED_CLAUSE} " in f"{statement} "


# =========================================================================== #
# SECTION A — THE FLIP.  Offline pins over the emitted DDL.
#
# RED TODAY (3): briefed / refers / answers_to are not ENFORCED, and the ∀ pin
# fails naming exactly those three.  GREEN TODAY (2): ``to`` (packet 03's, a
# regression pin) and the exact-set pin.
# =========================================================================== #


class TestEveryRelationEdgeIsEnforced:
    """#105's ruled scope: ``ENFORCED`` on every relation edge, not on a list of three.

    ``ENFORCED`` validates BOTH endpoints and guards the TABLE — including the
    ``INSERT RELATION`` door an app-level check on one verb can never reach (store
    reference §4, the adoption table's last row).  That is why the law is a ∀ over
    the emitter's output and not four hand-written assertions: the four assertions
    below exist to be a mutation-proof target, not to BE the invariant.
    """

    def test_EVERY_relation_table_the_schema_emits_is_ENFORCED(self) -> None:
        """THE LAW.  ∀ over the emitted DDL, not over a name list.

        RED at ``28387a0``: three of four edges lack the clause.  It also pins
        packet 04b's ``blocks`` edge before that edge exists — the day a fifth
        relation table is emitted un-guarded, this is what says so.
        """
        emitted = _every_emitted_relation_table()
        assert emitted, "the sweep found NO relation tables at all — the parser is broken"
        unguarded = {
            edge: f"{label}: {statement}"
            for edge, (label, statement) in emitted.items()
            if not _is_enforced(statement)
        }
        assert unguarded == {}, (
            "every TYPE RELATION table this schema emits must carry ENFORCED — the only "
            "guard that validates BOTH endpoints and covers INSERT RELATION (store "
            f"reference §4). Un-guarded: {unguarded}"
        )

    def test_the_relation_edge_set_is_EXACTLY_the_four_known_edges(self) -> None:
        """An exact-set pin over the emitted edges (the house idiom).

        GREEN at ``28387a0`` and RED the moment packet 04b adds ``blocks`` — which is
        the point: a new edge must be ADDED to :data:`_KNOWN_RELATION_EDGES` with its
        endpoints stated, so the flip cannot silently miss it.
        """
        assert set(_every_emitted_relation_table()) == set(_KNOWN_RELATION_EDGES), (
            "the emitted relation-table set drifted from this contract's declared set — "
            "if you ADDED an edge, add it to _KNOWN_RELATION_EDGES (with its IN/OUT "
            "tables) and confirm it is ENFORCED from birth; if you REMOVED one, delete "
            "its row here"
        )

    @pytest.mark.parametrize(
        ("edge", "generator_label"),
        [
            (BRIEFED_RELATION, "generate_brief_ddl"),
            (REFERS_RELATION, "generate_graph_ddl"),
            (ANSWERS_TO_RELATION, "generate_graph_ddl"),
            (TO_RELATION, "generate_message_ddl"),
        ],
    )
    def test_the_edge_carries_ENFORCED_in_its_own_slice(
        self, edge: str, generator_label: str
    ) -> None:
        """The four DECLARED-RED targets of the group-C mutation proof.

        ⚠ These four ids are the ``--expect-red`` set for
        ``scripts/mutation_proof.py`` when ``enforced=True`` is deleted from a
        ``_define_relation_table`` call — see this module's ``MUTATION_PROOF`` block.
        A routed-but-not-shared build (four private copies of the clause) passes the
        ∀ pin above and fails the mutation proof; that asymmetry is the whole reason
        both exist.

        ``to`` is GREEN at ``28387a0`` (packet 03 shipped it) — a REGRESSION pin, and
        the positive control proving this assertion can pass at all.
        """
        emitted = _relation_table_statements(_ALL_DDL_GENERATORS[generator_label]())
        assert edge in emitted, f"{generator_label} no longer emits the {edge!r} relation table"
        assert _is_enforced(emitted[edge]), (
            f"{edge} must be declared ENFORCED: {emitted[edge]!r}"
        )

    @pytest.mark.parametrize("edge", sorted(_KNOWN_RELATION_EDGES))
    def test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS(self, edge: str) -> None:
        """GREEN at ``28387a0`` — the #107-shape guard, pinned so the flip cannot
        arrive on a clause that never lands.

        Store reference §1.1 (RELATION-TABLE row) + probe §3 LEG A, MEASURED on
        3.2.1: ``DEFINE TABLE IF NOT EXISTS`` on an existing edge table is a SILENT
        NO-OP — it raises nothing, the stored definition is untouched, and the guard
        never reaches a live store.  ``OVERWRITE`` is the only clause that lands it.
        """
        _label, statement = _every_emitted_relation_table()[edge]
        assert statement.startswith(f"DEFINE TABLE OVERWRITE {edge} "), (
            f"{edge}'s relation clause must be OVERWRITE — IF NOT EXISTS is a measured "
            f"silent no-op on an existing edge table (store reference §1.1): {statement!r}"
        )

    @pytest.mark.parametrize(("edge", "endpoints"), sorted(_KNOWN_RELATION_EDGES.items()))
    def test_the_edge_declares_its_IN_and_OUT_endpoint_tables(
        self, edge: str, endpoints: tuple[str, str]
    ) -> None:
        """GREEN at ``28387a0``.  ``ENFORCED`` is meaningless without ``IN``/``OUT``:
        the clause validates that the endpoints EXIST, the typing validates that they
        are of the right TABLE, and the packet needs both halves on all four edges.
        """
        in_table, out_table = endpoints
        _label, statement = _every_emitted_relation_table()[edge]
        assert f"IN {in_table} OUT {out_table}" in statement, (
            f"{edge} must declare IN {in_table} OUT {out_table}: {statement!r}"
        )


# =========================================================================== #
# SECTION B — THE DIRTY-STORE MIGRATION.  One set per FLIPPED edge.
#
# THE TEST ENVIRONMENT IS A FICTION (repo CLAUDE.md; store reference §1.6): every
# test mints a VIRGIN database, and on a virgin database ANY clause creates the
# table WITH whatever the generator says — so a flip that never migrates is
# invisible to every offline pin and every ordinary live pin.  The flip lands on
# THREE EXISTING tables.  These are the only pins that can see it.
#
# Shape: scout §S4's five steps, and DDL applied through ``execute_transaction``
# (never a bare ``connection.query``) — the SDK checks ``statement[0]`` only, so a
# rejected later DDL statement rolls the schema back server-side while ``query()``
# raises nothing at all (store reference §3).  A lax pin reports a GREEN migration
# over a schema the engine silently discarded.
# =========================================================================== #

#: The three edges packet 04a flips, with the slice generator that owns each and the
#: DDL that must exist first for its endpoint tables to be real.
_FLIPPED_EDGES: tuple[tuple[str, str, str, Callable[[], str], Callable[[], str]], ...] = (
    (
        BRIEFED_RELATION,
        AGENT_TABLE,
        BRIEF_TABLE,
        generate_brief_ddl,
        generate_agent_ddl,
    ),
    (REFERS_RELATION, CODE_NODE_TABLE, NAME_TABLE, generate_graph_ddl, generate_graph_ddl),
    (ANSWERS_TO_RELATION, CODE_NODE_TABLE, NAME_TABLE, generate_graph_ddl, generate_graph_ddl),
)

_FLIPPED_EDGE_IDS = [edge[0] for edge in _FLIPPED_EDGES]


async def _apply_ddl(connection: SurrealConnection, ddl: str, *, url: str) -> None:
    """Apply ``ddl`` EXACTLY as production does — one ``BEGIN … COMMIT`` through
    :func:`~loremaster.store._txn.execute_transaction`.

    Cloned from ``test_surreal_store.py::_apply_ddl`` (scout §S4), including its
    ``_never_drop`` callback: a DDL rejection must never be mistaken for a dead
    socket.  NOT a bare ``connection.query(ddl)`` — see this section's header.
    """

    async def _acquire() -> _SurrealConnection:
        return connection

    async def _never_drop(_connection: _SurrealConnection) -> None:
        raise AssertionError("a DDL rejection must never drop the connection")

    await execute_transaction(
        f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_acquire, drop=_never_drop, url=url
    )


def _old_world_ddl(edge: str, in_table: str, out_table: str, generator: Callable[[], str]) -> str:
    """``generator()``'s DDL with ``edge``'s relation clause re-emitted UN-enforced.

    DERIVED from the production emitter, never hand-written: the target statement is
    replaced by ``_define_relation_table(edge, in_table, out_table, enforced=False)``
    — the same emitter production calls, with the OLD argument.  Scout §S4 names this
    the best thing in ``test_surreal_store.py``, and the reason is that a hand-copied
    old-DDL string tests a COPY of the code and passes while production stays broken.

    Deliberately does NOT raise when the replacement is a no-op.  The
    "is this fixture testing anything?" question gets its OWN pin
    (:meth:`TestTheOldWorldDerivationIsNotVacuous.test_the_old_world_DIFFERS_from_todays_generator`)
    so the BASELINE and survival controls stay readable-green and only the pins that
    describe the CHANGE go red.
    """
    current = generator()
    target = _relation_table_statements(current).get(edge)
    if target is None:  # pragma: no cover - guarded by the section-A exact-set pin
        raise AssertionError(f"{generator.__name__} no longer emits the {edge!r} relation table")
    return current.replace(target, _define_relation_table(edge, in_table, out_table, enforced=False))


def _unenforced_ddl(edge: str, in_table: str, out_table: str) -> str:
    """A bare ``OVERWRITE`` re-declaration of ``edge`` WITHOUT ``ENFORCED``.

    The group-C un-enforcing door, spelled through the production emitter.
    """
    return f"{_define_relation_table(edge, in_table, out_table, enforced=False)};\n"


def _ghost_id(prefix: str) -> str:
    """A record-id component for a record that is guaranteed NEVER to be created.

    FIXTURES MUST DISCRIMINATE: every negative pin here needs an identity that
    genuinely does not exist — a fixture where every endpoint is registered cannot
    tell a guarded table from an un-guarded one (packet 04, "Negative fixtures
    REQUIRED").  A fresh uuid4 per call means it cannot collide with a real row even
    if a sibling pin seeded one.
    """
    return f"{prefix}_{uuid.uuid4().hex}"


async def _record_exists(connection: SurrealConnection, table: str, row_id: str) -> bool:
    """Ground truth: does ``table:row_id`` actually exist?  (Never assumed.)"""
    rows = await run(
        connection, "SELECT id FROM $row", {"row": RecordID(table, row_id)}
    )
    return bool(rows)


async def _seed_endpoint(connection: SurrealConnection, table: str, row_id: str) -> None:
    """CREATE a minimally-valid row in ``table`` so it can be a live RELATE endpoint.

    ``session`` is a SurrealDB PROTECTED variable name, so ``agent`` is written with
    ``CONTENT`` and never ``SET session = $session`` (store reference §2).
    """
    now = datetime.now(UTC)
    content_by_table: dict[str, dict[str, Any]] = {
        AGENT_TABLE: {
            "name": "fixer-b",
            "session": "wave7",
            "role": "builder",
            "status": "active",
            "registered_at": now,
            "heartbeat_at": now,
        },
        BRIEF_TABLE: {"name": "project", "version": 1, "body": "law", "created_by": "lead"},
        CODE_NODE_TABLE: {
            "kind": "module",
            "qualified_name": "demo.svc",
            "bare_name": "svc",
            "file_path": "demo/svc.py",
            "tier": "custom",
            "chunk_id": None,
        },
        NAME_TABLE: {"value": "demo.svc"},
        MESSAGE_TABLE: {"body": "m"},
    }
    await run(
        connection,
        f"CREATE type::record('{table}', $id) CONTENT $content",
        {"id": row_id, "content": content_by_table[table]},
    )


def _edge_set_clause(edge: str) -> str:
    """The edge-local ``SET`` clause a legal RELATE onto ``edge`` must carry.

    Each flipped edge is SCHEMAFULL with required, non-``option`` fields, so a bare
    ``RELATE a->e->b`` is rejected for a reason that has nothing to do with
    ``ENFORCED``.  Spelling them here keeps every rejection below attributable to the
    endpoint — the probe's own lesson (§6.2: an instrument that fails for the wrong
    reason reads exactly like one that fails for the right one).
    """
    clauses = {
        BRIEFED_RELATION: "SET via = 'register', at = time::now()",
        REFERS_RELATION: (
            "SET kind = 'calls', resolved = true, src_tier = 'custom', "
            "src_file_path = 'demo/svc.py'"
        ),
        ANSWERS_TO_RELATION: "SET tier = 'custom', file_path = 'demo/svc.py'",
    }
    return clauses[edge]


async def _relate(
    connection: SurrealConnection,
    edge: str,
    *,
    in_table: str,
    in_id: str,
    out_table: str,
    out_id: str,
) -> Any:
    """RELATE one ``edge`` with its endpoints bound as SDK ``RecordID`` objects.

    ``$from``/``$to`` bound, NEVER ``type::record()`` at the RELATE endpoint position
    — the latter is a PARSE ERROR (store reference §4, first bullet), a failure that
    would masquerade as an ``ENFORCED`` rejection in every negative pin below.
    """
    return await run(
        connection,
        f"RELATE $from->{edge}->$to {_edge_set_clause(edge)}",
        {"from": RecordID(in_table, in_id), "to": RecordID(out_table, out_id)},
    )


@pytest_asyncio.fixture()
async def migration_db() -> AsyncIterator[tuple[SurrealConnection, SurrealEnv]]:
    """A raw admin connection on a fresh unique database, reaped on exit.

    Cloned from ``test_surreal_store.py::migration_db`` (scout §S4), and for its
    reason: these pins own their schema themselves — they apply an OLD definition,
    dirty the store, then apply the CURRENT one — so they need a BARE connection,
    **never** a ledger or store that has already applied today's schema at
    ``ensure_ready``.  Calling ``ensure_ready`` would install the NEW schema before
    the pin could install the OLD one, destroying the exact condition under test.
    """
    env = make_env(database=unique_database(), dim=_MIGRATION_DIM)
    connection = await connect_admin(env)
    try:
        yield connection, env
    finally:
        await connection.close()
        await drop_database(env)


class TestTheOldWorldDerivationIsNotVacuous:
    """RED at ``28387a0``, and it is the pin that keeps section B honest.

    Every migration pin below applies an "old" DDL and then the current one.  If the
    two are IDENTICAL the pins migrate a schema to ITSELF and test nothing at all
    while looking perfectly green.  This states that hazard as its own assertion
    rather than burying it in a helper's exception.
    """

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator"),
        [(e, i, o, g) for e, i, o, g, _ in _FLIPPED_EDGES],
        ids=_FLIPPED_EDGE_IDS,
    )
    def test_the_old_world_DIFFERS_from_todays_generator(
        self, edge: str, in_table: str, out_table: str, generator: Callable[[], str]
    ) -> None:
        assert _old_world_ddl(edge, in_table, out_table, generator) != generator(), (
            f"re-emitting {edge!r} with enforced=False does not change the DDL, which "
            f"means today's generator ALREADY emits it un-enforced — the flip has not "
            f"happened. Once it has, this pin passes and every migration pin below "
            f"starts testing a real old->new transition instead of a no-op."
        )


class TestTheEnforcedFlipMigratesADirtyStore:
    """THE #107 SHAPE, per flipped edge.

    ``IF NOT EXISTS`` is a MEASURED silent no-op on an existing edge table and
    ``OVERWRITE`` is the only clause that lands the flip (probe §3 legs A/B, 3.2.1).
    A virgin-DB fixture cannot distinguish the two: on a fresh database the table is
    CREATED with whatever the generator says, so the migration is never exercised.
    These pins apply the OLD (un-enforced) definition, DIRTY the store with a
    dangling edge that is legal under it, then apply today's generator.

    RED at ``28387a0``: ``test_the_guard_is_LIVE_…``.
    GREEN at ``28387a0``: the BASELINE, survival and idempotence legs — they are
    controls and preserved behaviours, and they must stay green after the flip too.
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

        Returns ``(live_in_id, ghost_out_id)`` — a real IN endpoint and an OUT
        endpoint that is verified NOT to exist.
        """
        await _apply_ddl(connection, endpoint_generator(), url=env.url)
        await _apply_ddl(
            connection, _old_world_ddl(edge, in_table, out_table, generator), url=env.url
        )
        live_in = _ghost_id("live_in")
        await _seed_endpoint(connection, in_table, live_in)
        ghost_out = _ghost_id("ghost_out")
        assert not await _record_exists(connection, out_table, ghost_out), (
            "the negative fixture's OUT endpoint must genuinely NOT exist — an "
            "all-registered fixture cannot discriminate a guarded table from an "
            "un-guarded one"
        )
        await _relate(
            connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
            out_id=ghost_out,
        )
        return live_in, ghost_out

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator", "endpoint_generator"),
        _FLIPPED_EDGES,
        ids=_FLIPPED_EDGE_IDS,
    )
    async def test_BASELINE_the_old_world_really_ACCEPTS_a_dangling_edge(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """Without this control, "the guard is live after migrating" could be true
        because it was ALWAYS live — and the migration itself never tested.

        GREEN at ``28387a0`` and GREEN after the flip: it describes the OLD world.
        """
        connection, env = migration_db
        _live_in, ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator, endpoint_generator
        )
        rows = await run(connection, f"SELECT id FROM {edge}")
        assert rows, (
            f"the OLD (un-enforced) {edge} definition was supposed to ACCEPT a RELATE to "
            f"the non-existent {out_table}:{ghost_out} — if it did not, this fixture is "
            f"not installing the old world and every leg below is measuring the wrong "
            f"transition"
        )

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator", "endpoint_generator"),
        _FLIPPED_EDGES,
        ids=_FLIPPED_EDGE_IDS,
    )
    async def test_the_guard_is_LIVE_after_applying_todays_ddl_to_a_DIRTY_store(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """RED at ``28387a0``.  THE load-bearing pin of packet 04a.

        A definition that emits perfectly and never LANDS is invisible to every
        offline pin — this is the leg that catches it.  The rejection is demanded
        BEHAVIOURALLY (a new dangling RELATE is refused), never by reading back a
        stored DDL string: probe §3 leg A records that a stored-DDL diff alone could
        be a rendering artifact, so the behavioural confirmation is the measurement.
        """
        connection, env = migration_db
        live_in, _ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator, endpoint_generator
        )
        await _apply_ddl(connection, generator(), url=env.url)

        fresh_ghost = _ghost_id("still_absent")
        assert not await _record_exists(connection, out_table, fresh_ghost)
        with pytest.raises(Exception):  # noqa: B017 - the engine's NotFoundError surface
            await _relate(
                connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
                out_id=fresh_ghost,
            )

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator", "endpoint_generator"),
        _FLIPPED_EDGES,
        ids=_FLIPPED_EDGE_IDS,
    )
    async def test_POSITIVE_CONTROL_a_REAL_endpoint_is_still_accepted_after_the_flip(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """The control the rejection pin needs: a guard that refuses EVERYTHING is not
        a guard, it is an outage.

        GREEN at ``28387a0`` (nothing rejects today) and it must STAY green after the
        flip — which is exactly what makes it a control rather than decoration.
        """
        connection, env = migration_db
        live_in, _ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator, endpoint_generator
        )
        await _apply_ddl(connection, generator(), url=env.url)

        live_out = _ghost_id("live_out")
        await _seed_endpoint(connection, out_table, live_out)
        await _relate(
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
        _FLIPPED_EDGES,
        ids=_FLIPPED_EDGE_IDS,
    )
    async def test_the_PRE_EXISTING_dangling_edge_SURVIVES_the_flip(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """GREEN today and after: probe §3 P2b, MEASURED on 3.2.1 — the flip succeeds
        with a dangling row present and there is NO validation sweep over existing
        rows.

        Pinned because the opposite belief is the attractive one: "we turned ENFORCED
        on, so the ghosts are gone."  They are not.  Store reference §4: *turning it
        on and calling the ghost problem closed is a FALSE ALL-CLEAR* — cleanup is a
        separate data migration, ruled OUT of this packet as #236.
        """
        connection, env = migration_db
        _live_in, ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator, endpoint_generator
        )
        before = await run(connection, f"SELECT id FROM {edge}")
        await _apply_ddl(connection, generator(), url=env.url)
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
        _FLIPPED_EDGES,
        ids=_FLIPPED_EDGE_IDS,
    )
    async def test_the_migration_is_IDEMPOTENT_on_an_already_migrated_store(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """GREEN today and after.  ``ensure_ready`` re-applies this DDL on EVERY boot,
        so a second and third apply must be a clean no-op that neither raises nor
        loses the guard.
        """
        connection, env = migration_db
        live_in, _ghost_out = await self._dirty_old_world(
            connection, env, edge, in_table, out_table, generator, endpoint_generator
        )
        await _apply_ddl(connection, generator(), url=env.url)
        await _apply_ddl(connection, generator(), url=env.url)
        await _apply_ddl(connection, generator(), url=env.url)

        live_out = _ghost_id("live_out")
        await _seed_endpoint(connection, out_table, live_out)
        await _relate(
            connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
            out_id=live_out,
        )


# =========================================================================== #
# SECTION C — THE UN-ENFORCING DOOR (probe §3 item (a)).
#
# ``DEFINE TABLE OVERWRITE`` is FULL REPLACE for ``ENFORCED`` too: a re-emission
# that omits the keyword silently un-guards the table.  §1.2 states full-replace
# for ``ASSERT``; §4 does NOT state it for ``ENFORCED``, and this is a LIVE
# regression door — a DDL generator change, a copy-paste, or a new table-recreate
# path drops the guard with zero error and zero test signal ON A VIRGIN DB.
# =========================================================================== #


class TestTheUnEnforcingDoor:
    """The hazard, pinned so the next author meets it DELIBERATELY.

    Repo law, WHEN YOU CANNOT CLOSE A HOLE, PIN IT: this door cannot be closed —
    ``OVERWRITE`` full-replace is the engine's semantics and the very thing that makes
    the flip land.  What CAN be done is make it impossible to walk through unnoticed:
    the ∀ pin in section A refuses an un-enforced emission at the source, and the leg
    below demonstrates the mechanism live so nobody has to rediscover it from an
    outage.
    """

    @pytest.mark.parametrize(
        ("edge", "in_table", "out_table", "generator", "endpoint_generator"),
        _FLIPPED_EDGES,
        ids=_FLIPPED_EDGE_IDS,
    )
    async def test_re_emitting_the_edge_WITHOUT_ENFORCED_silently_un_guards_it(
        self,
        migration_db: tuple[SurrealConnection, SurrealEnv],
        edge: str,
        in_table: str,
        out_table: str,
        generator: Callable[[], str],
        endpoint_generator: Callable[[], str],
    ) -> None:
        """RED at ``28387a0`` — it cannot reach its own subject until the guard exists.

        Three legs in order, and the middle one is the control that makes the third
        meaningful: (1) today's DDL guards; (2) an ``OVERWRITE`` without ``ENFORCED``
        raises nothing at all; (3) the dangling RELATE it refused a moment ago is
        accepted again.
        """
        connection, env = migration_db
        await _apply_ddl(connection, endpoint_generator(), url=env.url)
        await _apply_ddl(connection, generator(), url=env.url)
        live_in = _ghost_id("live_in")
        await _seed_endpoint(connection, in_table, live_in)

        ghost_out = _ghost_id("ghost_out")
        assert not await _record_exists(connection, out_table, ghost_out)
        with pytest.raises(Exception):  # noqa: B017 - the engine's NotFoundError surface
            await _relate(
                connection, edge, in_table=in_table, in_id=live_in, out_table=out_table,
                out_id=ghost_out,
            )

        # The door: a full-replace re-emission that simply omits the keyword.
        await _apply_ddl(connection, _unenforced_ddl(edge, in_table, out_table), url=env.url)

        await _relate(
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
# The vendor says a dangling edge makes "a query on the relation return an empty
# array".  That is FALSE as a reader would apply it, on 3.1.5 AND re-confirmed on
# 3.2.1: the identity traversal returns the ghost as a FIRST-CLASS MEMBER.  A
# negative pin written to the vendor's sentence would be GREEN on a build that
# never wrote the edge at all.
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
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        connection, env = migration_db
        await _apply_ddl(connection, generate_agent_ddl(), url=env.url)
        await _apply_ddl(
            connection,
            _old_world_ddl(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, generate_brief_ddl),
            url=env.url,
        )
        agent_id = _ghost_id("live_agent")
        await _seed_endpoint(connection, AGENT_TABLE, agent_id)
        ghost_brief = _ghost_id("ghost_brief")
        assert not await _record_exists(connection, BRIEF_TABLE, ghost_brief)
        await _relate(
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
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        """The control that makes the pin above a real negative rather than a blind
        instrument: ``[]`` IS producible by this exact query shape, so the ghost-only
        row returning a member is evidence, not noise.

        Probe §2 records that this probe's ancestor reported the OPPOSITE of the truth
        on its first run and ONLY the control caught it.
        """
        connection, env = migration_db
        await _apply_ddl(connection, generate_agent_ddl(), url=env.url)
        await _apply_ddl(
            connection,
            _old_world_ddl(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, generate_brief_ddl),
            url=env.url,
        )
        lonely = _ghost_id("lonely_agent")
        await _seed_endpoint(connection, AGENT_TABLE, lonely)
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
# ⚠⚠ ``ENFORCED`` ALONE CANNOT SATISFY THE PACKET'S OWN EXIT CRITERION (probe
# §10.5, MEASURED).  What a caller actually receives from an ENFORCED rejection is
# ``statement N of M was rejected (unspecified rejection); see the server log`` —
# the engine's ``The record 'agent:x' does not exist`` is deliberately withheld by
# the seam's error-message hygiene (ledger #31).  "A bogus-recipient publish/send
# TEACHES instead of dangling" is therefore UNREACHABLE via the engine guard: the
# app-level check is the ONLY layer that can teach.  It is REQUIRED, not garnish.
#
# ONE IMPLEMENTATION (repo law, #102): ``send`` and ``publish`` need the SAME
# policy — "resolve these agent ids against the agent table; refuse, naming every
# missing one, BEFORE any write" — so it is a FUNCTION THEY CALL, never a pattern
# ``briefs.py`` clones from ``MessageLedger._reject_unknown_recipients``.
# =========================================================================== #

#: An agent id no fixture below ever registers.
UNREGISTERED_AGENT_ID = "unregistered_agent_0000000000000000"

_BRIEF_NAME = "project"
_BRIEF_BODY = "the standing law"
_PUBLISHER = "lead"


@pytest_asyncio.fixture()
async def brief_ledger_with_a_real_agent() -> AsyncIterator[tuple[BriefLedger, str, SurrealEnv]]:
    """A REAL :class:`BriefLedger` on a database where the ``agent`` table exists and
    holds exactly ONE registered row.

    Deliberately NOT ``test_brief_ledger.py``'s ``brief_ledger_factory``: that fixture
    applies ``generate_brief_ddl()`` alone, so the ``agent`` table never exists there
    and every ``briefed`` edge it writes is a dangling edge (this module's docstring,
    ⚠).  A fixture that guarantees the one condition under which the bug is invisible
    is exactly what THE TEST ENVIRONMENT IS A FICTION warns about — so this one
    guarantees the opposite: a real registered agent AND a genuinely absent one, in
    the same database, so the positive and negative legs share a fixture and neither
    can pass for a fixture reason.

    ⚠ The agent slice is applied FIRST.  After the flip ``briefed`` is
    ``IN agent … ENFORCED``, which makes ``generate_brief_ddl`` ORDER-DEPENDENT on
    ``generate_agent_ddl`` in a way it has never been —
    :class:`TestTheBriefSliceIsOrderDependentOnTheAgentSlice` pins that consequence.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup = await connect_admin(env)
    registered_id = f"registered_agent_{uuid.uuid4().hex}"
    try:
        await _apply_ddl(setup, generate_agent_ddl(), url=env.url)
        await _seed_endpoint(setup, AGENT_TABLE, registered_id)
        assert not await _record_exists(setup, AGENT_TABLE, UNREGISTERED_AGENT_ID), (
            "the negative fixture's agent id must genuinely NOT exist"
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

    Raw, because the question these pins ask is "did a row land at all", and the
    public readers raise or filter rather than answering it.
    """
    rows = await ledger._query(  # noqa: SLF001 - the raw-read seam the atomicity pins need
        f"SELECT id FROM {BRIEF_TABLE} WHERE name = $name", {"name": name}
    )
    return list(rows) if isinstance(rows, list) else []


async def _briefed_edge_count(ledger: BriefLedger) -> int:
    """The total ``briefed`` edge count — a RAW read that SEES orphan edges.

    ``acked_version``'s edge->brief join cannot: it drops a dangling target silently,
    which is the very defect #105 is about.  Cloned in intent from
    ``test_brief_ledger.py::_edge_count``.
    """
    rows = await ledger._query(  # noqa: SLF001 - see above
        f"SELECT count() FROM {BRIEFED_RELATION} GROUP ALL"
    )
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


class TestPublishRefusesAnUnregisteredAgent:
    """RED at ``28387a0``, all four legs — today ``publish`` writes the brief AND a
    dangling ack edge for an agent that does not exist (probe §10.2 leg A, MEASURED).

    THE QUANTIFIER LAW.  ``publish``'s ``agent_id`` has exactly THREE input classes and
    each one's fate is FORCED by its own fixture below — unregistered (refused),
    registered (written), ``None`` (accepted, no edge).  Not "no silent dangle on a
    bad id": every input, its stated fate.
    """

    async def test_an_UNREGISTERED_agent_id_is_REFUSED(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        ledger, _registered, _env = brief_ledger_with_a_real_agent
        with pytest.raises(Exception) as caught:  # noqa: B017 - the type is section E's job
            await ledger.publish(
                _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=UNREGISTERED_AGENT_ID
            )
        assert not isinstance(caught.value, SurrealStoreError), (
            "the refusal must come from the APP-LEVEL check, not from the engine: an "
            "ENFORCED rejection reaches the caller as 'statement N of M was rejected "
            "(unspecified rejection); see the server log' (probe §10.5), which cannot "
            "satisfy this packet's Exit criterion that a bogus publish TEACHES"
        )

    async def test_the_refusal_NAMES_the_bad_agent_id(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """The whole point of the app layer.  ``ENFORCED`` reports ONE bad endpoint,
        as untyped prose, only AFTER the write is attempted (store reference §4,
        error-ergonomics row) — and the seam withholds even that.  A refusal that does
        not name the offending id has taught the caller nothing.
        """
        ledger, _registered, _env = brief_ledger_with_a_real_agent
        with pytest.raises(Exception) as caught:  # noqa: B017
            await ledger.publish(
                _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=UNREGISTERED_AGENT_ID
            )
        assert UNREGISTERED_AGENT_ID in str(caught.value), (
            f"the refusal must name the offending agent id: {str(caught.value)!r}"
        )

    async def test_the_refused_publish_writes_NO_brief_row(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """RED at ``28387a0`` for the interesting reason: today the brief IS written
        (probe §10.2 leg A) and a dangling ack edge lands beside it.

        Note what this does NOT settle.  After the flip, ``ENFORCED`` alone would ALSO
        leave no brief row — but by ROLLING IT BACK after attempting the write
        (§10.2 leg B: ``SELECT id FROM brief WHERE id = brief:b_lost`` -> ``[]``).
        "No row afterwards" cannot tell refused-early from rolled-back-late; the
        version pin below is what does.
        """
        ledger, _registered, _env = brief_ledger_with_a_real_agent
        with pytest.raises(Exception):  # noqa: B017
            await ledger.publish(
                _BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=UNREGISTERED_AGENT_ID
            )
        assert await _brief_rows(ledger, _BRIEF_NAME) == []
        assert await _briefed_edge_count(ledger) == 0, (
            "a refused publish must leave NO ack edge — a dangling ack is a receipt for "
            "an agent that does not exist, which is finding #105 itself"
        )

    async def test_the_refusal_happens_BEFORE_the_version_is_minted(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """THE discriminator between "refused early" and "rolled back late".

        ``publish`` mints its version off the per-name counter hot row BEFORE the
        CREATE, and hands it back via ``_release_version`` when the write is rejected
        — a compensating path that is BEST-EFFORT and swallows its own failures.  An
        app check that runs first never enters that path at all, so the next real
        publish gets v1.  A build that merely lets ``ENFORCED`` reject would take the
        release path and this pin would still see v1 only if the release succeeded;
        forcing the check upstream removes the question.
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
    """THE POSITIVE CONTROL, without which every pin above passes on a build that
    refuses EVERYTHING.

    GREEN at ``28387a0`` — but not for the right reason: today it passes because
    nothing is checked at all.  After the flip it passes because the agent genuinely
    resolves.  A pin can be green in both worlds and still be load-bearing; what it
    forbids is the wrong build BETWEEN them.
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
        """The third input class.  ``None`` means "a ledger-level caller with no agent
        row in play" and must stay a legal, edge-free publish — a check that refused it
        would break the ~50 call sites that pass no ``agent_id`` at all, and would be
        the quantifier law violated in the other direction (an invariant conditioned on
        the failure mode that prompted the work).
        """
        ledger, _registered, _env = brief_ledger_with_a_real_agent
        result = await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER)
        assert result.brief.version == 1
        assert await _briefed_edge_count(ledger) == 0


class TestTheIdempotentReAckSignalIsNotConfusedWithAnUnknownAgent:
    """§G — the SHARED-CATCH hazard, and the reason this section demands the app check
    run UPSTREAM rather than merely alongside.

    ``BriefLedger._relate_briefed`` catches ``SurrealStoreError`` as its
    IDEMPOTENT-RE-ACK SIGNAL: a ``UNIQUE(in, out)`` rejection means "already acked",
    disambiguated only by a follow-up read.  After the flip an ``ENFORCED`` rejection
    arrives through that SAME ``except``, leaving two distinct failure modes sharing
    one catch (probe §9, READ from source).  Today the follow-up read happens to
    re-raise correctly — but "happens to" is not a contract, and the operator's
    no-consumers ruling explicitly invites reshaping the seam so the two modes stop
    sharing a catch at all.

    RED at ``28387a0``: today neither call refuses anything.
    """

    async def test_an_ack_by_an_UNREGISTERED_agent_is_REFUSED_and_never_already_acked(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        ledger, registered, _env = brief_ledger_with_a_real_agent
        await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by=_PUBLISHER, agent_id=registered)
        with pytest.raises(Exception) as caught:  # noqa: B017
            await ledger.ack(
                agent_id=UNREGISTERED_AGENT_ID,
                agent_name="ghost",
                name=_BRIEF_NAME,
                version=1,
                via="explicit",
            )
        assert UNREGISTERED_AGENT_ID in str(caught.value)
        assert not isinstance(caught.value, SurrealStoreError), (
            "an unknown agent must be refused by the app check, never surface as the "
            "raw store rejection the idempotent-re-ack handler also catches — two "
            "distinct failure modes must not share one except clause"
        )

    async def test_POSITIVE_CONTROL_a_REGISTERED_agents_re_ack_is_still_already_acked(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """The control that keeps the pin above from being satisfied by breaking
        idempotence: the re-ack SIGNAL must still work for a real agent.

        GREEN today and after — a preserved behaviour, adjudicated
        ``preserved-with-pin`` in the removed-behaviour inventory.
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

    RED at ``28387a0``: an un-enforced ``briefed`` accepts the RELATE regardless of
    whether ``agent`` exists, so the "guard is live" half cannot be shown yet.
    """

    async def test_a_brief_slice_applied_WITHOUT_the_agent_slice_still_guards(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        connection, env = migration_db
        await _apply_ddl(connection, generate_brief_ddl(), url=env.url)
        ghost_agent = _ghost_id("ghost_agent")
        ghost_brief = _ghost_id("ghost_brief")
        with pytest.raises(Exception):  # noqa: B017
            await _relate(
                connection, BRIEFED_RELATION, in_table=AGENT_TABLE, in_id=ghost_agent,
                out_table=BRIEF_TABLE, out_id=ghost_brief,
            )


class TestTheUnknownAgentPolicyHasONEHome:
    """§E — ONE IMPLEMENTATION, proved by MUTATION and not by inspection.

    ``MessageLedger._reject_unknown_recipients`` already implements this policy for
    ``send``; ``briefs.py`` has none.  Writing a second copy is the #102 shape
    verbatim — a doc naming one method as "the reference pattern" got its bug
    faithfully cloned into a sibling.  So the policy is EXTRACTED to
    :data:`SHARED_POLICY_MODULE` and both ledgers CALL it.

    ⚠ ROUTING IS NOT SHARING.  A build where both modules import the shared symbol but
    each hand-rolls the decision underneath it passes every "did you call the driver"
    check.  The mutation pin below is the only one that can tell the difference: it
    replaces the shared function and demands BOTH verbs change behaviour.  A caller
    that stays working is a private copy wearing the shared name.

    RED at ``28387a0``: the module does not exist.
    """

    def test_the_shared_policy_module_exists_and_exports_the_policy(self) -> None:
        policy = _shared_policy()
        assert hasattr(policy, SHARED_POLICY_ATTR), (
            f"{SHARED_POLICY_MODULE} must export {SHARED_POLICY_ATTR!r} — the ONE "
            f"function both ledgers call. It lives in neither ledger module on purpose "
            f"(the loremaster.agent_ref precedent: a ledger owning the shared object "
            f"forces its sibling to import IT)"
        )

    @pytest.mark.parametrize("module_name", ["loremaster.briefs", "loremaster.messages"])
    def test_BOTH_ledgers_import_the_SHARED_policy_under_the_pinned_name(
        self, module_name: str
    ) -> None:
        """Fails CLOSED: a module that hand-rolled its own copy has no such attribute,
        so the mutation pin below could not patch it — and a mutation proof that cannot
        find its mutation point is a proof of nothing.  This states that precondition
        as its own assertion instead of letting it hide inside a monkeypatch.
        """
        import importlib

        module = importlib.import_module(module_name)
        assert hasattr(module, SHARED_POLICY_ATTR), (
            f"{module_name} must import {SHARED_POLICY_ATTR} from {SHARED_POLICY_MODULE} "
            f"and call it — never clone MessageLedger._reject_unknown_recipients' body"
        )

    async def test_MUTATION_replacing_the_shared_policy_changes_BOTH_verbs(
        self,
        monkeypatch: pytest.MonkeyPatch,
        brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv],
    ) -> None:
        """PROVE SHARING BY MUTATION — the only test that distinguishes DRY from
        looks-DRY.

        A sentinel replaces the shared policy in BOTH ledger modules; ``publish`` with
        a REGISTERED agent (an input the real policy would ACCEPT) must now raise it.
        If ``briefs.py`` carries a private copy, the sentinel never fires and this
        goes red — which is the whole point.

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

    async def test_BOTH_verbs_raise_the_SAME_error_type_for_an_unknown_agent(
        self, brief_ledger_with_a_real_agent: tuple[BriefLedger, str, SurrealEnv]
    ) -> None:
        """A value-level sharing proof that needs NO name at all.

        One policy raises one type.  Today ``send`` raises
        ``MessageLedger.UnknownRecipientError`` and ``publish`` raises nothing —
        two different fates for one question, which IS the duplication this section
        forbids.  Kept alongside the name-keyed mutation pin because it survives a
        rename of :data:`SHARED_POLICY_ATTR` and the mutation pin does not.
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
        assert type(publish_error.value) is type(send_error.value), (
            "one policy raises one type: publish and send must refuse an unknown agent "
            f"identically. Got {type(publish_error.value).__name__} vs "
            f"{type(send_error.value).__name__}"
        )


class _Ref:
    """A minimal ``AgentRefLike`` stand-in (``id`` + ``name``), read-only.

    Locally defined rather than imported from ``loremaster.agents``: the ledgers accept
    this Protocol STRUCTURALLY and never import their neighbours, and neither does this
    contract.
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

    GREEN at ``28387a0`` for the refusal itself (``_reject_unknown_recipients`` already
    exists and already names EVERY bad id, which is why it is the precedent the shared
    policy is extracted FROM) — these pins are here as the REGRESSION half: the
    extraction must not weaken ``send``.  The mutation leg is RED until the extraction
    lands.

    The mixed fixture is the discriminating one: a wholly-bogus recipient list cannot
    tell "refused because one was unknown" from "refuses every list".
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
        """Asserting "no message row afterwards" is what distinguishes REFUSED EARLY
        from ROLLED BACK LATE.

        Both leave zero rows (probe §10.3 leg D: one bad recipient loses the WHOLE
        fan-out, message row included), so the row count alone cannot tell them apart —
        the ERROR TYPE does, and it is asserted here too.  Stating both is the pin;
        stating only the row count would be a false gate.
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
                "the refusal must be the app check's, BEFORE the write — not the "
                "engine's rollback afterwards"
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
        """Without this, "refused" above is satisfied by a build that refuses every
        send."""
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
        """The ``send`` half of the sharing mutation.  RED at ``28387a0``.

        ``send`` must stop owning ``_reject_unknown_recipients``' BODY and call the
        shared function instead: with the shared policy replaced, an ALL-REGISTERED
        send (which the real policy accepts) must raise the sentinel.
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


# =========================================================================== #
# SECTION I — THE CONDITION P5's refers/answers_to VERDICT RESTS ON.
#
# Probe §6.5, FLAGGED AND NOT SETTLED: "SAFE TO FLIP requires every RELATE's
# endpoints be created by an EARLIER statement in the same transaction … For the
# code_node (IN) side it is an invariant of the DERIVATION, and I could not confirm
# it holds."  Today a violation is an invisible dangling edge; after the flip it is
# a HARD FAILURE of the whole file's index transaction (the graph slice rides the
# SAME store.apply as the chunk / file_text / manifest fragments, so the file is
# isolated ``failed`` and its chunks never update).
#
# ⚠ MEASURED 2026-07-26 (report §I): the condition holds for all 56 production
# modules AND for eight adversarial source shapes — but it is NOT structurally
# guaranteed.  It holds exactly while the CHUNK SET and the ON-DISK SOURCE agree,
# because ``_derive_nodes`` reads CHUNKS while ``_derive_edges``' reference half
# re-reads the FILE (``evict_resolved_file`` makes that read deliberately fresh).
# When they diverge the fragment RELATEs from a code_node it never created.
#
# So the contract does NOT pin "our corpus has no violation" — that is the
# quantifier law violated, an invariant conditioned on the inputs that happened to
# be tested.  It pins the ∀ property of the FRAGMENT: never RELATE from an endpoint
# this fragment did not create.
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
    deliberately unreachable: if any pin below ever opened one, it would fail loudly
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
    RELATE time, not deferred to COMMIT (leg L5 — the endpoint exists by the end of
    the transaction and the RELATE is still rejected because it ran first), and it is
    per-RECORD, not per-transaction (leg L8).  So "statement order" IS the contract,
    and an unordered set check would pass a fragment the engine rejects.

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
        relate = _FRAGMENT_RELATE_RE.match(statement)
        if relate is None:
            continue
        for param_name in (relate.group(1), relate.group(3)):
            rendered = str(fragment.params[param_name])
            if rendered not in created:
                unsatisfied.append((relate.group(2), param_name, rendered))
    return unsatisfied


def _relate_count(fragment: Any) -> int:
    """How many RELATEs the fragment carries (the anti-vacuity counter)."""
    return sum(1 for raw in fragment.statements if _FRAGMENT_RELATE_RE.match(raw.strip()))


class TestTheCodeGraphFragmentNeverRelatesFromAnUncreatedEndpoint:
    """§I — the property that makes the ``refers``/``answers_to`` flip SAFE, stated as
    a ∀ over the fragment rather than as a survey of a corpus.

    RED at ``28387a0``, on the divergent-input leg only.  The flip converts an
    invisible dangling edge into a loud indexing failure — which is the POINT of the
    flip — but only if the fragment is self-consistent for EVERY input, not for the
    inputs that happen to be in this repo.
    """

    def test_a_realistic_multi_chunk_file_is_self_consistent(
        self, code_graph: SurrealCodeGraph
    ) -> None:
        """The establishing leg.  GREEN at ``28387a0`` and it must stay green: this is
        the shape production actually indexes, and if it ever reddens the flip is
        breaking real indexing.
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
        """FIXTURES MUST DISCRIMINATE.  ``answers_to``'s src is a ``code_node`` CREATEd
        one statement earlier (structurally safe); ``refers``' src comes from a
        DIFFERENT derivation (``_derive_edges`` vs ``_derive_nodes``) and is the one at
        risk.  A fixture carrying only ``answers_to`` would pass the pin above while
        proving nothing about the edge the packet is actually flipping.
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
            f"the fixture must exercise BOTH flipped code-graph edges; got {sorted(edges)}"
        )

    def test_a_DIVERGENT_chunk_set_still_yields_a_self_consistent_fragment(
        self, code_graph: SurrealCodeGraph
    ) -> None:
        """RED at ``28387a0`` — THE §I finding, and the pin that closes it.

        The two derivations read DIFFERENT inputs: ``_derive_nodes`` reads the CHUNK
        SET the caller supplies, while ``_derive_edges``' reference half re-reads the
        FILE off disk (``_resolve`` calls ``evict_resolved_file`` to read it FRESH, on
        purpose).  ``Indexer.index_file(tier, path, source)`` takes ``source`` from its
        caller, so a save landing between the watcher's read and the derivation's read
        makes the two disagree — and MEASURED 2026-07-26, a divergent chunk set makes
        ``build_file_graph_fragment`` emit ``refers`` RELATEs whose ``src`` code_node
        no statement ever created.

        Today those become invisible dangling edges.  After the flip they abort the
        whole file's index transaction.  The fix belongs in the fragment builder —
        create the missing src node, or drop the edge — never in weakening the flip.

        The empty chunk set is the SMALLEST input that forces the divergence; it is
        not the only one, and the pin is written over the fragment's property rather
        than over this input so any other divergence is caught too.
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
        """A PROBE NEEDS A CONTROL.  ``_unsatisfied_relate_endpoints`` returning ``[]``
        is worthless until it has been shown returning something on a fragment that is
        known-inconsistent — otherwise a parser that matches no statement at all reads
        exactly like a perfectly self-consistent fragment.

        GREEN at ``28387a0`` and it must STAY green after the fix: it mutates a
        fragment by hand rather than relying on the production builder to be broken.
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
        """The second control, and the one an unordered implementation would fail.

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
    """The narrower, DERIVATION-level statement of the same condition (probe §8
    decision 6): ``{edge.src} ⊆ {node.qualified_name}``.

    GREEN at ``28387a0`` for a matching chunk set — kept because it localises a future
    failure.  If the fragment pin above reddens, this says whether the cause is the
    DERIVATION disagreeing with itself or the fragment builder losing a statement.
    """

    def test_every_edge_src_is_a_derived_node_for_a_matching_chunk_set(
        self, graph_project: Path
    ) -> None:
        graph = CodeGraph(
            tier_roots={_GRAPH_TIER: graph_project}, project_roots=[graph_project]
        )
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


# =========================================================================== #
# MUTATION_PROOF — the DECLARED-RED sets, written BEFORE the run (finding #196).
#
# Repo law: a declared set transcribed from output you just watched is the
# tautology in a new costume.  These ids were taken from ``pytest --collect-only
# -q`` and are recorded here so ``scripts/mutation_proof.py`` can diff BOTH ways —
# unexpected reds AND declared reds that stayed green.
#
# PROOF 1 — group C, "prove sharing by mutation".  After the flip lands, delete
# ``enforced=True`` from ONE ``_define_relation_table`` call in
# ``surreal_schema.py`` and every pin below whose edge that call owns must redden.
# Doing it for each of the four calls in turn is what proves the four edges route
# through ONE emitter rather than four private copies of the clause:
#
#   F=loremaster/tests/test_enforced_relations.py
#   C=TestEveryRelationEdgeIsEnforced
#   ./scripts/mutation_proof.py \
#     --file loremaster/loremaster/store/surreal_schema.py \
#     --anchor "_define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)" \
#     --replacement "_define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE)" \
#     --expect-red "$F::$C::test_EVERY_relation_table_the_schema_emits_is_ENFORCED" \
#     --expect-red "$F::$C::test_the_edge_carries_ENFORCED_in_its_own_slice[briefed-generate_brief_ddl]" \
#     -- uv run pytest -q "$F" -k "$C"
#
# (and the same for ``to``/``refers``/``answers_to``, swapping the parametrised id).
#
# PROOF 2 — group E, ONE IMPLEMENTATION.  Already MECHANISED IN-SUITE rather than
# left to a shell block: ``test_MUTATION_replacing_the_shared_policy_changes_BOTH_
# verbs`` and ``test_MUTATION_send_routes_through_the_same_shared_policy`` replace
# the shared function at runtime and demand each verb changes behaviour.  A private
# copy in either module leaves its verb working and reddens the pin.
# =========================================================================== #
