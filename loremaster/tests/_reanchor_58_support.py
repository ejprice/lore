"""Shared, NON-collected support for packet 58's contract files.

Packet 58 (``docs/plans/v2/58-supersede-reanchor.md``; kickoff rulings
``docs/design/2026-09-26-packet58-kickoff-rulings.md`` @ ``c8d3241``) is pinned by three NEW files —
``test_supersede_reanchor_58.py``, ``test_task_guarded_shell_58.py``,
``test_task_claimable_partition_58.py`` — that read the SAME store facts (a row's ``blocked_by``
column, the ``blocks`` edge set, a byte snapshot of the ledger).  ONE implementation of each reader
lives here and every pin calls it (repo law #102): a reader cloned per file is how two files come to
disagree about what "the edge set" means.

Scoped to the tree at ``1206233`` (branch ``feat/surreal-unification``), 2026-09-26.

⚠ **Nothing here imports a name packet 58 introduces** (``SupersedeResult``,
``_guarded_append_fragment``, ``max_reanchor_dependents``).  A module-level import of a name that
does not exist yet makes every importing file UNCOLLECTABLE rather than RED — and an uncollectable
file deletes its pins from the run instead of failing them (finding #133).  Those names are reached at
CALL time, inside the pins that need them.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import (
    STATUS_BLOCKED,
    STATUS_CLAIMED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_OPEN,
    STATUS_WONTFIX,
    TaskLedger,
)
from surrealdb import RecordID

#: The identity that CREATES fixture rows and PERFORMS supersedes.  Distinct from every
#: claimant below so an event's ``actor`` can be attributed to the verb that wrote it.
CREATOR = "creator-58"
#: The identity that performs the SUPERSEDE in the re-anchor pins — NOT ``CREATOR``: the
#: re-anchor note's ``actor`` must be the SUPERSEDER, and a fixture where creator ==
#: superseder cannot tell a build that stamps the dependent's own creator from one that
#: stamps the caller (parameter-value monoculture, CLAUDE.md FIXTURES MUST DISCRIMINATE).
SUPERSEDER = "superseder-58"
#: Claimants.  Two, so a claim pin never runs on the one owner value it was written for.
CLAIMANT = "claimant-58"
OTHER_CLAIMANT = "other-claimant-58"
WORKER = "worker-58"
DESCRIPTION = "packet 58 contract fixture"
#: A blocker id that names NO task row (a legacy PHANTOM — ``blocked_by`` was fail-open at
#: write before 04b-1).  Asserted absent by the fixtures that seed it.
PHANTOM_ID = "phantom0058deadbeef0000000000000"

#: The re-anchor note's action vocabulary — P58 Scope IN 1, verbatim.
ACTION_REANCHORED = "dependency_reanchored"
#: The claim event's action vocabulary — kickoff §4 (``event={actor, action:"claim", at}``).
ACTION_CLAIM = "claim"


@pytest_asyncio.fixture()
async def ledger58() -> AsyncIterator[tuple[TaskLedger, SurrealEnv]]:
    """A REAL :class:`TaskLedger` on a fresh throwaway database of the TEST store."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = new_ledger(env)
    await ledger.ensure_ready()
    try:
        yield ledger, env
    finally:
        await ledger.close()
        await drop_database(env)


def new_ledger(env: SurrealEnv) -> TaskLedger:
    """A SECOND, independent ledger on the same database — its own connection.

    The constructed-interleaving pins drive the racing writer through this one, so the racer's
    writes are real commits on a different connection, not calls re-entering the ledger under test.
    """
    return TaskLedger(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )


async def raw(ledger: TaskLedger, statement: str, params: dict[str, Any] | None = None) -> Any:
    """A RAW single-statement read/write through the ledger's own seam (bypasses every pre-check)."""
    return await ledger._query(statement, params or {})  # noqa: SLF001 - the store-truth readers need it


def successor_of(result: Any) -> str:
    """The successor id carried by ``supersede_task``'s result — FIXTURE PLUMBING, both worlds.

    Kickoff §7 item 7 changes the return from ``str`` to ``SupersedeResult(successor_id,
    reanchored)``.  This accessor accepts BOTH on purpose: it is used where a pin needs the successor
    id to assert something ELSE (a column, an edge, a note), so that pin fails at a pre-58 tree for
    ITS OWN reason rather than erroring in set-up.  The return TYPE is pinned by exactly one test
    (``test_supersede_reanchor_58.py::TestTheSupersedeItselfIsUnchanged::test_the_result_is_the_typed_carrier``)
    plus every pin that reads ``.reanchored`` — so a build that keeps returning ``str`` is RED there.
    ⚠ Re-open trigger: once 58 lands the ``str`` branch is dead — simplify it in the first change
    that touches this module.
    """
    if isinstance(result, str):
        return result
    return str(result.successor_id)


async def column(ledger: TaskLedger, task_id: str) -> list[str]:
    """``task_id``'s stored ``blocked_by`` — an EXPLICIT projection.

    Store ref §2: ``SELECT *`` omits a NONE column entirely; a projection reads ``None``.
    """
    rows = await raw(
        ledger, f"SELECT blocked_by FROM type::record('{TASK_TABLE}', $id)", {"id": task_id}
    )
    if not isinstance(rows, list) or not rows:
        return []
    return [str(entry) for entry in (rows[0].get("blocked_by") or [])]


async def all_columns(ledger: TaskLedger) -> dict[str, list[str]]:
    """EVERY task row's ``blocked_by``, keyed by bare id — the DERIVED set the ∀-row pins range over."""
    rows = await raw(
        ledger, f"SELECT record::id(id) AS id, blocked_by FROM {TASK_TABLE}"
    )
    return {
        str(row["id"]): [str(entry) for entry in (row.get("blocked_by") or [])]
        for row in (rows or [])
    }


async def edge_pairs(ledger: TaskLedger) -> list[tuple[str, str]]:
    """EVERY ``blocks`` edge as ``(blocker, blocked)``, as a LIST — duplicates are kept on purpose.

    A list, not a set: the edge table carries no ``UNIQUE(in, out)`` (``surreal_schema._task_statements``),
    so a rewire that RELATEs twice DOUBLES an edge, and a set would hide exactly that.
    ``record::id`` decodes the endpoints (store ref §7 — never a ``split(":")``).
    """
    rows = await raw(
        ledger,
        f"SELECT record::id(in) AS blocker, record::id(out) AS blocked FROM {BLOCKS_RELATION}",
    )
    return sorted((str(row["blocker"]), str(row["blocked"])) for row in (rows or []))


async def assert_edge_mirrors_column_for_every_row(ledger: TaskLedger, *, where: str) -> int:
    """THE INVARIANT ``edge ≡ blocked_by``, ∀ ROWS of the store — returns the row count checked.

    The expected edge multiset is DERIVED from the columns: exactly one ``(b, t)`` per DISTINCT
    ``b`` in ``t.blocked_by`` whose ``b`` names an existing row (a phantom entry cannot carry an
    ENFORCED edge — the documented legacy residue).  Compared as SORTED LISTS so a doubled edge is
    visible.  The row count is RETURNED so a caller can CHECK coverage (P1c: the reach is a checked
    variable, never a hidden constant).
    """
    columns = await all_columns(ledger)
    expected = sorted(
        (blocker, task_id)
        for task_id, blockers in columns.items()
        for blocker in dict.fromkeys(blockers)
        if blocker in columns
    )
    actual = await edge_pairs(ledger)
    assert actual == expected, (
        f"{where}: the blocks EDGE multiset does not mirror the blocked_by COLUMNS over all "
        f"{len(columns)} rows.\n  edges not implied by any column: "
        f"{sorted(set(actual) - set(expected)) or '(none)'}\n  columns with no edge: "
        f"{sorted(set(expected) - set(actual)) or '(none)'}\n  doubled edges: "
        f"{sorted({pair for pair in actual if actual.count(pair) > 1}) or '(none)'}\n"
        f"The re-anchor must DELETE every X→Y edge, RELATE exactly one X'→Y per dependent, and "
        f"leave every other edge alone — in the SAME transaction as the column rewrite"
    )
    return len(columns)


async def snapshot(ledger: TaskLedger) -> tuple[list[str], list[tuple[str, str]]]:
    """A byte-comparable picture of the WHOLE ledger: every row (``SELECT *``) + every edge.

    For the byte-inert pins (a refused / rolled-back supersede changed NOTHING).  ``repr`` of the
    id-sorted rows, so a changed ``updated_at``, an appended event or a new row all show.
    """
    rows = await raw(ledger, f"SELECT * FROM {TASK_TABLE}")
    rendered = sorted(repr(sorted(row.items(), key=lambda item: item[0])) for row in (rows or []))
    return rendered, await edge_pairs(ledger)


async def row_count(ledger: TaskLedger) -> int:
    rows = await raw(ledger, f"SELECT count() FROM {TASK_TABLE} GROUP ALL")
    return int(rows[0]["count"]) if rows else 0


async def events_of(ledger: TaskLedger, task_id: str) -> list[dict[str, Any]]:
    """``task_id``'s ``provenance.events`` (explicit projection)."""
    rows = await raw(
        ledger,
        f"SELECT provenance FROM type::record('{TASK_TABLE}', $id)",
        {"id": task_id},
    )
    if not rows:
        return []
    provenance = rows[0].get("provenance") or {}
    return list(provenance.get("events") or [])


async def updated_at_of(ledger: TaskLedger, task_id: str) -> Any:
    rows = await raw(
        ledger, f"SELECT updated_at FROM type::record('{TASK_TABLE}', $id)", {"id": task_id}
    )
    return rows[0].get("updated_at") if rows else None


async def drive_to(ledger: TaskLedger, task_id: str, status: str) -> None:
    """Drive an OPEN task to ``status`` along LEGAL edges only — WITHOUT a claim where possible.

    ``open → blocked → in_progress → done`` needs no claim, so a dependent whose blocker is still
    OPEN (hence unclaimable) can still reach ``in_progress`` / ``done`` through the public state
    machine (``LEGAL_TRANSITIONS``).  ``claimed`` is claim-only and therefore needs a claimable row.
    """
    if status == STATUS_OPEN:
        return
    if status == STATUS_WONTFIX:
        await ledger.transition(task_id, STATUS_WONTFIX, actor=WORKER)
        return
    if status == STATUS_CLAIMED:
        result = await ledger.claim_task(task_id, WORKER)
        assert result.claimed, f"fixture could not claim {task_id!r}"
        return
    await ledger.transition(task_id, STATUS_BLOCKED, actor=WORKER)
    if status == STATUS_BLOCKED:
        return
    await ledger.transition(task_id, STATUS_IN_PROGRESS, actor=WORKER)
    if status == STATUS_IN_PROGRESS:
        return
    if status == STATUS_DONE:
        await ledger.transition(task_id, STATUS_DONE, actor=WORKER, summary="fixture finished")
        return
    raise AssertionError(f"no legal claim-free path to {status!r}")


async def create(ledger: TaskLedger, subject: str, blocked_by: list[str] | None = None) -> str:
    return await ledger.create_task(
        subject, DESCRIPTION, blocked_by=blocked_by or [], created_by=CREATOR
    )


async def supersede(ledger: TaskLedger, task_id: str, **kwargs: Any) -> Any:
    """``supersede_task`` performed by :data:`SUPERSEDER` — returns the RAW result object."""
    return await ledger.supersede_task(
        task_id,
        subject=kwargs.pop("subject", f"successor of {task_id}"),
        description=DESCRIPTION,
        created_by=SUPERSEDER,
        **kwargs,
    )


async def raw_seed_row(
    ledger: TaskLedger,
    task_id: str,
    *,
    blocked_by: list[str],
    status: str = STATUS_OPEN,
    superseded_by: str | None = None,
    owner: str | None = None,
) -> None:
    """Seed ONE task row RAW — the only door to LEGACY shapes the verbs now refuse.

    Legacy shapes (a ``[X, X]`` duplicate that predates the birth-time dedupe; a phantom entry;
    a dependent stranded on a row superseded BEFORE 58 deployed — real on ``:18500``).  No edge is
    minted here; callers that want the mirror call :func:`raw_relate`.
    """
    content: dict[str, Any] = {
        "subject": f"raw {task_id}",
        "description": DESCRIPTION,
        "status": status,
        "blocked_by": blocked_by,
        "provenance": {"created_by": CREATOR, "created_at": datetime.now(UTC).isoformat(), "events": []},
        "created_at": datetime.now(UTC),
    }
    if superseded_by is not None:
        content["superseded_by"] = superseded_by
    if owner is not None:
        content["owner"] = owner
        content["claimed_at"] = datetime.now(UTC)
    await raw(
        ledger,
        f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $content",
        {"id": task_id, "content": content},
    )


async def raw_relate(ledger: TaskLedger, blocker: str, blocked: str) -> None:
    await raw(
        ledger,
        f"RELATE $from->{BLOCKS_RELATION}->$to",
        {"from": RecordID(TASK_TABLE, blocker), "to": RecordID(TASK_TABLE, blocked)},
    )


async def raw_force(ledger: TaskLedger, task_id: str, **fields: Any) -> None:
    """Force columns on an existing row RAW (a legacy / unreachable state, labelled at the call)."""
    sets = ", ".join(f"{name} = $f_{name}" for name in fields)
    await raw(
        ledger,
        f"UPDATE type::record('{TASK_TABLE}', $id) SET {sets}",
        {"id": task_id, **{f"f_{name}": value for name, value in fields.items()}},
    )


async def bulk_seed_dependents(ledger: TaskLedger, blocker: str, count: int, tag: str) -> list[str]:
    """Seed ``count`` open dependents of ``blocker`` in TWO statements (rows, then edges).

    The hub pins need up to ~1700 dependents; minting them one ``create_task`` at a time would cost
    minutes.  The shape is exactly what ``create_task`` writes (``_new_task_content`` + one mirrored
    ``blocks`` edge each), so the seeded world is the verbs' world at scale.
    """
    now = datetime.now(UTC)
    ids = [f"{tag}{index:05d}" for index in range(count)]
    rows = []
    for task_id in ids:
        content = TaskLedger._new_task_content(  # noqa: SLF001 - the verbs' own row shape
            f"hub dependent {task_id}", DESCRIPTION, [blocker], CREATOR, now
        )
        rows.append({"id": RecordID(TASK_TABLE, task_id), **content})
    await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows})
    edges = [
        {"in": RecordID(TASK_TABLE, blocker), "out": RecordID(TASK_TABLE, task_id)} for task_id in ids
    ]
    await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": edges})
    return ids


class ApplyHook:
    """Run ``before`` exactly ONCE, immediately before the ledger's FIRST ``_apply`` of a verb.

    (r2: typed ``Any`` — amendment 5's runtime family drives the FINDING ledger's ``_apply`` too.)

    The constructed-interleaving instrument: it models *"a concurrent writer committed between this
    verb's pre-reads and its transaction"* at the ONE seam every task write composes through
    (``TaskLedger._apply``).  It FAILS CLOSED: :attr:`fired` is asserted by every pin that uses it,
    so a build that stops routing the verb through ``_apply`` reddens rather than passing vacuously.
    """

    def __init__(self, ledger: Any, before: Callable[[], Awaitable[Any]]) -> None:
        self._ledger = ledger
        self._before = before
        self._original = ledger._apply  # noqa: SLF001
        self.fired = False

    async def __call__(self, fragments: Any) -> None:
        if not self.fired:
            self.fired = True
            await self._before()
        await self._original(fragments)

    @contextlib.contextmanager
    def installed(self) -> Any:
        self._ledger._apply = self  # noqa: SLF001
        try:
            yield self
        finally:
            self._ledger._apply = self._original  # noqa: SLF001


# =========================================================================== #
# contract-58-r2 additions (adversary-58 MP1–MP18; amendments 2 + 3 — docs/design/
# 2026-09-26-packet58-amendment-{2,3}.md @ e0760fd / 7266c1b).  Same rule as above: nothing
# here imports a name packet 58 introduces.
# =========================================================================== #

#: The heal's INFO receipt (amendment 1 R2) and the three WARNING records amendment 3 rules
#: (§2 a chunk's domain rejection; §5 a phantom chain head / a superseded_by cycle).
HEAL_EVENT = "task.backfill.stragglers_reanchored"
HEAL_CHUNK_REJECTED_EVENT = "task.backfill.straggler_chunk_rejected"
HEAL_PHANTOM_HEAD_EVENT = "task.backfill.straggler_phantom_head"
HEAL_CHAIN_CYCLE_EVENT = "task.backfill.straggler_chain_cycle"
HEAL_ACTOR = "boot-heal"
#: The driver's rollback record (``loremaster.store._txn._log_rollback``).
ROLLBACK_EVENT = "store.transaction.rolled_back"


async def boot(env: SurrealEnv) -> None:
    """ONE boot (``ensure_ready``) on a fresh ledger connection — the heal's only trigger."""
    booted = new_ledger(env)
    try:
        await booted.ensure_ready()
    finally:
        await booted.close()


class ComposeSpy:
    """Record every transaction ``loremaster.tasks`` composes: ``(statements, params)`` per call.

    The spy sits on ``compose`` — the ONE builder every task write goes through, the count its hard
    cap checks — so what it sees is what reached the store, never what a builder merely built.
    """

    def __init__(self) -> None:
        import importlib

        self._module = importlib.import_module("loremaster.tasks")
        self._real = self._module.compose
        self.calls: list[tuple[list[str], dict[str, Any]]] = []

    def __call__(self, *fragments: Any) -> Any:
        statements = [statement for fragment in fragments for statement in fragment.statements]
        params: dict[str, Any] = {}
        for fragment in fragments:
            params.update(fragment.params)
        self.calls.append((statements, params))
        return self._real(*fragments)

    @contextlib.contextmanager
    def installed(self) -> Any:
        setattr(self._module, "compose", self)  # noqa: B010 - the module attribute IS the seam
        try:
            yield self
        finally:
            setattr(self._module, "compose", self._real)  # noqa: B010

    def heal_calls(self) -> list[tuple[list[str], dict[str, Any]]]:
        """The composed transactions that carry a boot-heal re-anchor note (a heal CHUNK each)."""
        return [
            call for call in self.calls
            if any(
                isinstance(value, dict)
                and value.get("action") == ACTION_REANCHORED
                and value.get("actor") == HEAL_ACTOR
                for value in call[1].values()
            )
        ]


async def seed_stragglers(ledger: TaskLedger, total: int, blockers: int, tag: str) -> tuple[str, list[str]]:
    """``total`` raw stragglers spread over ``blockers`` DISTINCT legacy blockers, each superseded by
    ONE open head (adversary-58 batch 3's ``_stragglers`` shape).  Returns ``(head, straggler ids)``."""
    head = await create(ledger, f"{tag} head")
    ids: list[str] = []
    per = -(-total // blockers)
    for index in range(blockers):
        legacy = f"{tag}legacy{index:03d}0000000000000000"
        await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
        count = min(per, total - len(ids))
        if count <= 0:
            break
        ids += await bulk_seed_dependents(ledger, legacy, count, tag=f"{tag}{index:03d}x")
    return head, ids


async def measure_heal_shape(ledger: TaskLedger, env: SurrealEnv, tag: str) -> tuple[int, int]:
    """``(fixed, per)`` of ONE heal chunk over stragglers of ONE superseded blocker, MEASURED.

    Seeds 1, 2 and 3 stragglers of a fresh blocker (one boot each; every boot heals only the new
    ones), reads the heal chunk's composed statement count off :class:`ComposeSpy`, and checks
    linearity at n=3.  This is amendment 3 §1's "the packer's own count, read from the same counting
    function in the test — never a literal" (``compose`` spied — the ruling's second admitted form).
    """
    counts: list[int] = []
    for n in (1, 2, 3):
        await seed_stragglers(ledger, n, 1, f"{tag}{n}m")
        spy = ComposeSpy()
        with spy.installed():
            await boot(env)
        chunks = spy.heal_calls()
        assert len(chunks) == 1, f"measuring the heal shape: {len(chunks)} heal chunks for n={n}"
        counts.append(len(chunks[0][0]))
    per = counts[1] - counts[0]
    fixed = counts[0] - per
    assert per > 0 and counts[2] == fixed + 3 * per, (
        f"the heal chunk's composed count is not linear in its rows (c1..c3 = {counts})"
    )
    return fixed, per


def predicted_chunks(rows: int, fixed: int, per: int, cap: int) -> int:
    """A GREEDY packer's chunk count for ``rows`` one-blocker stragglers: ``(cap − fixed) // per`` rows
    fit a chunk (amendment 3 §1: close the chunk when the next row would exceed the cap)."""
    fit = (cap - fixed) // per
    assert fit > 0
    return -(-rows // fit)


# --------------------------------------------------------------------------- #
# ⚠ DUAL (packet 58 contract r3 — REPORT-contract-58-r3.md §DUAL R3-D1; amendment 8 §3 @ 03cb6d0): the
# guarded-CAS VERB population.  r2 derived it per METHOD BODY (a shell-ledger method that literally calls
# ``self._apply`` and reaches the shell) inside a HAND-LISTED module set (``SHELL_LEDGER_MODULES``) plus a
# named single-statement door (``SINGLE_STATEMENT_CAS_DOORS``).  Amendment 8 §3 retired all three keys: the
# ``_apply``-call SHAPE made a correct extract-method refactor RED (adversary-58-r2 F8) while a helper-applied
# NEW verb escaped (N20), and the module hand-list shrank the reach (F6).  The population is now DERIVED from
# the CALL GRAPH over the WHOLE production tree; the single-statement door comes from the static index's own
# derived door set (``test_retry_seam._GUARDED_CAS_DOORS``), never a list here.
# --------------------------------------------------------------------------- #

#: The shell every guarded-append ledger routes its CAS writes through — a RULED name (kickoff §4 / findings
#: #489), the one name key this derivation keeps.  Bound (stated): a CAS verb whose guard is NOT built by the
#: shell is invisible here; the one-producer pin (``test_task_guarded_shell_58``) is what forbids that shape.
CAS_SHELL = "_guarded_append_fragment"
#: The DRIVER seams amendment 8 §3 names — every store write reaches one of them.  Resolved BY IDENTITY
#: against ``loremaster.store._txn`` (an alias, a re-export or ``_txn_module.execute_transaction`` all count).
DRIVER_SEAM_NAMES = ("execute_transaction", "run_query")


def derive_cas_verbs(package_root: Any) -> set[str]:
    """``{"<module path>::<function>"}`` — every MINIMAL guarded-CAS verb of the production tree, from its
    call graph.

    Amendment 8 §3 (F8's proposal): a function is a CAS verb iff some same-module transitive call path from
    it reaches BOTH the shell (:data:`CAS_SHELL`) and a function that calls a driver seam
    (:data:`DRIVER_SEAM_NAMES`, resolved by identity).  MINIMAL (REPORT-contract-58-r3.md FK-r3-5, my pick):
    it is a verb only if no DIRECT callee of it already reaches both — so a public wrapper (``acknowledge`` →
    ``_transition``) or the boot (``ensure_ready`` → the heal) is not a second verb, while a verb that builds
    through the shell and applies through a driver-only helper (the extract-method refactor; 57's
    helper-applied ``assign``) IS one.

    Nodes are functions keyed by NAME per module (bound, stated: two classes in one module with a same-named
    method merge — RS-6 of adversary-58-r2; no production module holds two shell ledgers today).  Calls
    counted: ``self.f(…)`` / ``cls.f(…)`` / ``Klass.f(…)`` / ``f(…)``.  Dynamic dispatch (``getattr``) is
    invisible here — the driver-seam RUNTIME leg (``test_reanchor_58_r3_cas_seam.py``) is what observes it,
    and the two are cross-checked both ways.
    """
    import importlib
    from pathlib import Path

    from _logging_fixtures import _workspace_root, parse_production_trees

    # THE ONE tree parser (finding #279 / F4 — `test_ast_reach_helpers` forbids a hand-rolled whole-tree
    # parse); the package's slice is selected by its repo-relative prefix.
    prefix = Path(package_root).resolve().relative_to(_workspace_root().resolve()).as_posix() + "/"
    verbs: set[str] = set()
    for relative, tree in sorted(parse_production_trees(include_scripts=False).items()):
        if not relative.startswith(prefix):
            continue
        key = relative[len(prefix):]
        dotted = key[: -len(".py")].replace("/", ".")
        dotted = dotted[: -len(".__init__")] if dotted.endswith(".__init__") else dotted
        module = importlib.import_module(f"loremaster.{dotted}" if dotted != "__init__" else "loremaster")
        verbs |= {f"{key}::{name}" for name in cas_verbs_in(tree, vars(module))}
    return verbs


def cas_verbs_in(tree: Any, namespace: dict[str, Any], shell: str = CAS_SHELL) -> set[str]:
    """ONE module's minimal verbs that reach BOTH ``shell`` and a driver seam (see :func:`derive_cas_verbs`),
    by function NAME — split out so the derivation's discriminators run the SAME walk over a synthetic
    source (``namespace`` = the module's globals, which is what resolves a driver seam BY IDENTITY).
    ``shell`` is the CAS shell by default; amendment 8 §4 F11 derives the RELATE-composing verbs with
    the SAME walk over ``_relate_fragment`` (one derivation, two seeds — never a second walker)."""
    import ast

    from loremaster.store import _txn

    seams = {id(getattr(_txn, name)) for name in DRIVER_SEAM_NAMES}
    calls: dict[str, set[str]] = {}
    direct_seam: set[str] = set()
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        called = calls.setdefault(function.name, set())
        for call in ast.walk(function):
            if not isinstance(call, ast.Call):
                continue
            target = call.func
            if isinstance(target, ast.Name):
                called.add(target.id)
                if id(namespace.get(target.id)) in seams:
                    direct_seam.add(function.name)
            elif isinstance(target, ast.Attribute):
                called.add(target.attr)
                owner = namespace.get(target.value.id) if isinstance(target.value, ast.Name) else None
                if owner is not None and id(getattr(owner, target.attr, None)) in seams:
                    direct_seam.add(function.name)

    def _closure(seed: set[str]) -> set[str]:
        reached = set(seed)
        while True:
            grown = {name for name, called in calls.items() if called & reached} - reached
            if not grown:
                return reached
            reached |= grown

    reaches_shell = _closure({name for name, called in calls.items() if shell in called})
    reaches_seam = _closure(direct_seam)
    both = (reaches_shell & reaches_seam) - {shell}
    return {name for name in both if not any(callee in both for callee in calls[name] - {name})}
