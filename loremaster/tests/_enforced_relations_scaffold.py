"""Shared scaffolding for the `ENFORCED` relation-edge contracts (packets 04a + 43 + 04b-1).

Packet 04a's `ENFORCED` sweep was SPLIT on 2026-07-26 (operator ruling, packet 43
minted `a075e85`): 04a flips ``briefed``; the ``refers`` / ``answers_to`` flip waits on
`docs/plans/v2/43-derivation-source-unification.md`, which unifies the code graph's two
derivation SOURCES rather than patching the fragment locally.  The two contracts
therefore live in two files:

* ``test_enforced_relations.py`` — packet 04a
* ``test_derivation_source_unification.py`` — packet 43
* ``test_blocks_edge.py`` — packet 04b-1 (the FIFTH edge, ``task->blocks->task``)

**This module exists so they share ONE implementation of the migration idiom rather than
two copies of it.**  Repo law (#102): if two call sites need the same POLICY it is a
FUNCTION THEY CALL, never a pattern they clone — and the policy here is real, not trivia
(how DDL is applied, how an old world is derived, what counts as a genuinely-absent
endpoint).  A second copy is where the divergence starts, and a migration pin that
diverges from its sibling is a migration pin that stops testing the same thing.
Precedent for a shared, importable test-scaffold module: ``_surreal_harness`` (which
exports the ``admin_db`` fixture the same way), ``_comms_fakes``, ``_task_fakes``,
``render_injection_scaffold``.

Nothing here asserts anything.  Every pin lives in one of the two contract files; this
module holds only the vocabulary, the emitters' read surface, and the live-store helpers.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from typing import Any

import pytest_asyncio
from _surreal_harness import (
    SurrealConnection,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.store._txn import execute_transaction
from loremaster.store.surreal import _SurrealConnection
from loremaster.store.surreal_schema import (
    AGENT_TABLE,
    ANSWERS_TO_RELATION,
    BRIEF_TABLE,
    BRIEFED_RELATION,
    CODE_NODE_TABLE,
    MESSAGE_TABLE,
    NAME_TABLE,
    REFERS_RELATION,
    TASK_TABLE,
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
from surrealdb import RecordID

#: A tiny embedding width: every pin in both contracts exercises DDL or edge semantics,
#: never recall, and ``generate_ddl``/``generate_memory_ddl`` build HNSW indexes.
MIGRATION_DIM = 8

#: Every DDL generator that could emit a ``TYPE RELATION`` table, labelled.  The ∀ pins
#: in BOTH contracts sweep THIS, so a new slice generator is added here once and every
#: relation table it emits is guarded from birth.
ALL_DDL_GENERATORS: dict[str, Callable[[], str]] = {
    "generate_ddl": lambda: generate_ddl(dim=MIGRATION_DIM),
    "generate_manifest_ddl": generate_manifest_ddl,
    "generate_memory_ddl": lambda: generate_memory_ddl(dim=MIGRATION_DIM),
    "generate_task_ddl": generate_task_ddl,
    "generate_finding_ddl": generate_finding_ddl,
    "generate_agent_ddl": generate_agent_ddl,
    "generate_brief_ddl": generate_brief_ddl,
    "generate_message_ddl": generate_message_ddl,
    "generate_graph_ddl": generate_graph_ddl,
}

#: ⚠ **THE FIFTH EDGE, DECLARED BY PACKET 04b-1 ON 2026-07-28 — as a LITERAL, on purpose.**
#: ``loremaster.store.surreal_schema`` does not export a ``BLOCKS_RELATION`` constant yet, and
#: a module-level import of one that does not exist would make this scaffold — and therefore
#: BOTH ``test_enforced_relations.py`` and ``test_derivation_source_unification.py`` —
#: UNCOLLECTABLE rather than RED (finding #133: those are different states and the
#: uncollectable one is the dangerous one, because it DELETES pins from the run instead of
#: failing them).  So the name lives here as a string, and
#: ``test_blocks_edge.py::TestTheBlocksEdgeIsDeclared``'s
#: ``test_the_schema_exports_BLOCKS_RELATION_under_this_exact_name`` holds production's
#: constant equal to it.  The day the constant exists, this literal may be
#: replaced by the import in one edit.
BLOCKS_RELATION_NAME = "blocks"

#: The relation edges the schema declares, as ``edge -> (in_table, out_table)``.
#: An EXACT-SET pin reads this, so adding an edge is a deliberate act with a teaching failure
#: message, never a silent one.
#:
#: ⚠ ``blocks`` was ADDED here by packet 04b-1's contract BEFORE the edge exists, which is
#: what makes ``test_the_relation_edge_set_is_EXACTLY_the_five_known_edges`` RED until the
#: builder lands it.  That reddening **is the deliberate declaration the pin exists to
#: force** (04a contract §6.8), not a misfire — see ``test_blocks_edge.py``'s module
#: docstring, §"WHAT THIS CONTRACT TURNS RED IN FILES IT DOES NOT OWN".
KNOWN_RELATION_EDGES: dict[str, tuple[str, str]] = {
    BRIEFED_RELATION: (AGENT_TABLE, BRIEF_TABLE),
    TO_RELATION: (MESSAGE_TABLE, AGENT_TABLE),
    REFERS_RELATION: (CODE_NODE_TABLE, NAME_TABLE),
    ANSWERS_TO_RELATION: (CODE_NODE_TABLE, NAME_TABLE),
    BLOCKS_RELATION_NAME: (TASK_TABLE, TASK_TABLE),
}

#: ⚠ THE ONE DECLARED HOLE IN THE ∀ LAW, and the reason it is a NAMED CONSTANT rather
#: than silence.  These two edges are emitted UN-ENFORCED on purpose: their flip needs
#: the derivation-source unification of **packet 43**, because
#: ``build_file_graph_fragment`` can emit a ``refers`` RELATE whose ``src`` code_node no
#: statement of the same fragment creates (contract-04a §4.D2, MEASURED 2026-07-26).
#: Under ``ENFORCED`` that aborts the whole file's index transaction.
#:
#: A deny-by-default ∀ with a SMALL, ENUMERATED, ASSERTED safe-set is the shape repo law
#: prescribes (*allowlist the safe*) — it keeps "a fifth edge cannot arrive un-guarded"
#: true for packet 04b while making this specific deferral greppable, dated and
#: attributable.  **Packet 43 empties this set; that is its entry condition**, pinned in
#: ``test_derivation_source_unification.py``.
DEFERRED_TO_PACKET_43: frozenset[str] = frozenset({REFERS_RELATION, ANSWERS_TO_RELATION})

ENFORCED_CLAUSE = "ENFORCED"

_DEFINE_RELATION_RE = re.compile(
    r"^DEFINE TABLE (?:OVERWRITE |IF NOT EXISTS )?(?P<name>\S+) TYPE RELATION\b"
)


def statements(ddl: str) -> list[str]:
    """Split a generated DDL blob into its individual statements."""
    return [statement.strip() for statement in ddl.split(";") if statement.strip()]


def relation_table_statements(ddl: str) -> dict[str, str]:
    """``{edge name: its DEFINE TABLE statement}`` for every relation table in ``ddl``."""
    found: dict[str, str] = {}
    for statement in statements(ddl):
        match = _DEFINE_RELATION_RE.match(statement)
        if match is not None:
            found[match.group("name")] = statement
    return found


def every_emitted_relation_table() -> dict[str, tuple[str, str]]:
    """``{edge: (generator label, its DEFINE TABLE statement)}`` across ALL generators.

    The ∀ instrument.  It reads the emitted TEXT rather than a hand-list of edge names,
    so a relation table added by any generator — including one nobody thought to tell
    either contract about — is swept.
    """
    emitted: dict[str, tuple[str, str]] = {}
    for label, generator in ALL_DDL_GENERATORS.items():
        for edge, statement in relation_table_statements(generator()).items():
            emitted[edge] = (label, statement)
    return emitted


def is_enforced(statement: str) -> bool:
    """Whether a ``DEFINE TABLE … TYPE RELATION`` statement carries ``ENFORCED``."""
    return f" {ENFORCED_CLAUSE} " in f"{statement} "


async def apply_ddl(connection: SurrealConnection, ddl: str, *, url: str) -> None:
    """Apply ``ddl`` EXACTLY as production does — one ``BEGIN … COMMIT`` through
    :func:`~loremaster.store._txn.execute_transaction`.

    Cloned from ``test_surreal_store.py::_apply_ddl`` (scout §S4), including its
    ``_never_drop`` callback: a DDL rejection must never be mistaken for a dead socket.
    NOT a bare ``connection.query(ddl)`` — the SDK inspects only the FIRST statement's
    status (store reference §3), so a later DDL statement's rejection would roll the
    whole schema back server-side while ``query()`` raised nothing at all.  A pin that
    applied its DDL the lax way could report a GREEN migration over a schema the engine
    had just silently discarded.
    """

    async def _acquire() -> _SurrealConnection:
        return connection

    async def _never_drop(_connection: _SurrealConnection) -> None:
        raise AssertionError("a DDL rejection must never drop the connection")

    await execute_transaction(
        f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_acquire, drop=_never_drop, url=url
    )


def old_world_ddl(
    edge: str, in_table: str, out_table: str, generator: Callable[[], str]
) -> str:
    """``generator()``'s DDL with ``edge``'s relation clause re-emitted UN-enforced.

    DERIVED from the production emitter, never hand-written: the target statement is
    replaced by ``_define_relation_table(edge, in_table, out_table, enforced=False)`` —
    the same emitter production calls, with the OLD argument.  Scout §S4 names this the
    best thing in ``test_surreal_store.py``, and the reason is that a hand-copied
    old-DDL string tests a COPY of the code and passes while production stays broken.

    Deliberately does NOT raise when the replacement is a no-op.  The "is this fixture
    testing anything?" question gets its OWN pin in each contract file, so the BASELINE
    and survival controls stay readable-green and only the pins that describe the CHANGE
    go red.
    """
    current = generator()
    target = relation_table_statements(current).get(edge)
    if target is None:  # pragma: no cover - guarded by each contract's exact-set pin
        raise AssertionError(f"{generator.__name__} no longer emits the {edge!r} relation table")
    return current.replace(target, _define_relation_table(edge, in_table, out_table, enforced=False))


def unenforced_ddl(edge: str, in_table: str, out_table: str) -> str:
    """A bare ``OVERWRITE`` re-declaration of ``edge`` WITHOUT ``ENFORCED``.

    The un-enforcing door (probe §3 item (a)), spelled through the production emitter.
    """
    return f"{_define_relation_table(edge, in_table, out_table, enforced=False)};\n"


def ghost_id(prefix: str) -> str:
    """A record-id component for a record that is guaranteed NEVER to be created.

    FIXTURES MUST DISCRIMINATE: every negative pin in either contract needs an identity
    that genuinely does not exist — a fixture where every endpoint is registered cannot
    tell a guarded table from an un-guarded one (packet 04, "Negative fixtures
    REQUIRED").  A fresh uuid4 per call means it cannot collide with a real row even if a
    sibling pin seeded one.
    """
    return f"{prefix}_{uuid.uuid4().hex}"


async def record_exists(connection: SurrealConnection, table: str, row_id: str) -> bool:
    """Ground truth: does ``table:row_id`` actually exist?  (Never assumed.)"""
    rows = await run(connection, "SELECT id FROM $row", {"row": RecordID(table, row_id)})
    return bool(rows)


async def seed_endpoint(connection: SurrealConnection, table: str, row_id: str) -> None:
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
        # packet 04b-1: ``task`` becomes a RELATE endpoint (``task->blocks->task``), so it
        # needs a minimally-valid row here like every other endpoint table.  Every REQUIRED
        # (non-``option``) column of ``_TASK_FIELD_SPECS`` is present and ``status`` is
        # inside the closed-domain ASSERT — a row that failed the ASSERT would make every
        # negative pin fail for a reason that has nothing to do with ``ENFORCED``, which is
        # the probe's own §6.2 lesson.
        TASK_TABLE: {
            "subject": "seeded blocker",
            "description": "a task row seeded purely to be a live RELATE endpoint",
            "status": "open",
            "blocked_by": [],
            "provenance": {"created_by": "scaffold", "created_at": now.isoformat(), "events": []},
            "created_at": now,
        },
    }
    await run(
        connection,
        f"CREATE type::record('{table}', $id) CONTENT $content",
        {"id": row_id, "content": content_by_table[table]},
    )


def edge_set_clause(edge: str) -> str:
    """The edge-local ``SET`` clause a legal RELATE onto ``edge`` must carry.

    Each flipped edge is SCHEMAFULL with required, non-``option`` fields, so a bare
    ``RELATE a->e->b`` is rejected for a reason that has nothing to do with ``ENFORCED``.
    Spelling them here keeps every rejection attributable to the ENDPOINT — the probe's
    own lesson (§6.2: an instrument that fails for the wrong reason reads exactly like
    one that fails for the right one).
    """
    clauses = {
        # ``blocks`` carries NO edge-local field: it is a pure MIRROR of the ``blocked_by``
        # column, which holds no per-dependency metadata, so a required edge field would
        # make the edge carry state the column cannot and the mirror invariant could not be
        # stated at all.  Pinned in ``test_blocks_edge.py`` so this empty clause stays true.
        BLOCKS_RELATION_NAME: "",
        BRIEFED_RELATION: "SET via = 'register', at = time::now()",
        REFERS_RELATION: (
            "SET kind = 'calls', resolved = true, src_tier = 'custom', "
            "src_file_path = 'demo/svc.py'"
        ),
        ANSWERS_TO_RELATION: "SET tier = 'custom', file_path = 'demo/svc.py'",
    }
    return clauses[edge]


async def relate(
    connection: SurrealConnection,
    edge: str,
    *,
    in_table: str,
    in_id: str,
    out_table: str,
    out_id: str,
) -> Any:
    """RELATE one ``edge`` with its endpoints bound as SDK ``RecordID`` objects.

    ``$from``/``$to`` bound, NEVER ``type::record()`` at the RELATE endpoint position —
    the latter is a PARSE ERROR (store reference §4, first bullet), a failure that would
    masquerade as an ``ENFORCED`` rejection in every negative pin.
    """
    return await run(
        connection,
        f"RELATE $from->{edge}->$to {edge_set_clause(edge)}",
        {"from": RecordID(in_table, in_id), "to": RecordID(out_table, out_id)},
    )


@pytest_asyncio.fixture()
async def migration_db() -> AsyncIterator[tuple[SurrealConnection, SurrealEnv]]:
    """A raw admin connection on a fresh unique database, reaped on exit.

    Cloned from ``test_surreal_store.py::migration_db`` (scout §S4), and for its reason:
    these pins own their schema themselves — they apply an OLD definition, dirty the
    store, then apply the CURRENT one — so they need a BARE connection, **never** a
    ledger or store that has already applied today's schema at ``ensure_ready``.  Calling
    ``ensure_ready`` would install the NEW schema before the pin could install the OLD
    one, destroying the exact condition under test.
    """
    env = make_env(database=unique_database(), dim=MIGRATION_DIM)
    connection = await connect_admin(env)
    try:
        yield connection, env
    finally:
        await connection.close()
        await drop_database(env)
