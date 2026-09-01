"""Shared test substrate for the packet-63a GOVERNED contract (the FOUR parametrised pin
families) — authored by ``contract-63a`` (Opus 4.8 contract author; tests ONLY).

WHY THIS FILE EXISTS (design §1.2 item 6, §3.2): a governed table's contract is a
PARAMETRISATION, never a copy. The family LOGIC lives here ONCE; each table's test module
supplies a :class:`GovernedTableCase` and calls the shared runners. That is what makes the
families provably SHARED (design §3.2 RIDER — mutation-proven at 63a close: change
``read_filter``'s splice → every table's F3 reds; a family with a green consumer under
mutation is a clone wearing the shared name). 64 adds a ``TASK_CASE``/``FINDING_CASE`` and
calls the SAME runners — never a copied module.

THE FOUR FAMILIES (design §3.2):
- F1 DIRTY-STORE MIGRATION — seed legacy rows UNDER THE OLD DDL (store-ref §1.4 trap), apply
  NEW DDL, prove member-invisible/admin-visible BEFORE the verb and project-keep-visible AFTER;
  idempotent; agent-first ORDER precondition.
- F2 SINGLE-BRAIN ORACLE — ``{r: authorize(s,a,r).allowed}`` == ``SELECT … WHERE <read_filter>``
  over the REAL table DDL incl. DIRTY rows (NONE-owner, NONE-scope), per action per role.
- F3 CROSS-PRINCIPAL ISOLATION ∀ read verbs — ≥2 principals × ≥2 agents; served set == caller's
  visible set; served COUNT == served set size (trust Leg 1).
- F4 ANTI-INJECTION FUZZ ∀ write verbs — no hostile ``owner_*``/``as_agent``/``scope=<foreign>``
  argument moves the stamp; only a VERIFIED capability moves ``owner_agent``.

STORE LAW (``docs/reference/surrealdb-31-capabilities.md`` — cited, never re-transcribed):
§1.1 (FIELD OVERWRITE / INDEX IF NOT EXISTS), §1.4 (option<> on a POPULATED table + the
write-the-legacy-row-UNDER-THE-OLD-DDL fixture trap), §1.8 (UNIQUE over option<> = multiple NONE
coexist), §2 (CONTENT for protected names; ``SELECT *`` omits a NONE column so project
explicitly; record<> links do not auto-clean), §3 (execute_transaction — statement[0]-only
validation), §5 (hot-row CAS mint).

Live TEST store: ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique database, reaped on
exit. NO skip marker for an unreachable store — that is a LOUD failure, not a skip.
"""

from __future__ import annotations

import ast
import contextlib
import importlib
import re
import sys
import tomllib
from collections.abc import Awaitable, Callable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, TypeVar

from _surreal_harness import SurrealConnection, run

# lorerunes (61) is BUILT — import the PDP surface directly (unlike the 61b oracle's importlib
# gate, which loaded a not-yet-built package). The 63a substrate under test lives in
# ``loremaster.governed`` (stubbed → NotImplementedError until the builder wires it).
import lorerunes as pdp

_F = TypeVar("_F", bound=Callable[..., Any])

# --------------------------------------------------------------------------- #
# FORK 1 (design §10.1) — the ABSENT (unmigrated legacy) scope as a typecheck-safe value.
# --------------------------------------------------------------------------- #


def absent_scope() -> Any:
    """The ABSENT (unmigrated legacy) scope value — ``None``, typed ``Any`` DELIBERATELY.

    FORK 1 (design §10.1) WIDENS ``lorerunes.pdp.Resource.scope`` to ``str | None`` (a BUILDER
    task); ``None`` means one thing: an unmigrated legacy row's absent scope. A pin must construct
    ``Resource(scope=absent_scope())`` to prove the widening — but at HEAD ``Resource.scope: str``,
    so a LITERAL ``scope=None`` would fail ``scripts/typecheck.sh`` (and a ``type: ignore`` would
    flip to an *unused-ignore* error the day the builder widens it). Returning ``Any`` keeps the
    typecheck gate GREEN in BOTH worlds while the runtime pin stays RED-until-built: at HEAD
    ``Resource.__post_init__`` calls ``_is_valid_scope(None)`` which RAISES (a behavioural RED for
    the right reason — the widening is unbuilt), and on the correct build it constructs."""
    return None


# --------------------------------------------------------------------------- #
# Routing OBSERVATION marker (design §3.1, §10.2(i)) — the STRUCTURAL half of the #420 instrument.
# --------------------------------------------------------------------------- #


def observes_routing(tool: str, verb: str) -> Callable[[_F], _F]:
    """MACHINE-READABLE marker: the decorated test BEHAVIOURALLY observes that ``(tool, verb)``
    routes through the governed substrate (``read_filter`` on a read verb; ``stamp_owner`` /
    ``guarded_write`` on a write verb — observed by its EFFECT: isolation holds, the stamp is the
    resolved subject, a hostile ``owner_*=`` is ignored).

    A NO-OP at runtime (returns the function unchanged, so it is xdist-safe — no cross-worker
    module state); its VALUE is the AST-visible decorator CALL that the routing META-PIN collects
    (``test_governed_routing_63a`` ::``TestEveryRoutedVerbHasABehaviouralObservation``). INSTRUMENT-0
    (design §10.2(i)): a verb declared routed in ``_GOVERNED_VERBS_ROUTED`` with NO
    ``@observes_routing`` decorator ANYWHERE in the test tree is the hidden-constant reach defect —
    a routed declaration nobody observes. The decorated test's own assertions are the BEHAVIOURAL
    half; this marker is the STRUCTURAL half that makes the coverage a checked variable."""

    def _decorate(func: _F) -> _F:
        return func

    return _decorate


# --------------------------------------------------------------------------- #
# The EXPLAIN plan-walker — MIRRORED from the shipped
# ``test_keeps_schema.py::TestTheKeeperIndexFires`` / ``test_pdp_oracle_61b.py`` walker
# (instrument parsing, not production policy; ROUTING-IS-NOT-SHARING does not demand two test
# helpers share a walker — the shared PRODUCTION walker is TestTheKeeperIndexFires, cited).
# A pin that cannot SEE a TableScan is not a pin, so every EXPLAIN pin carries a C+ control.
# --------------------------------------------------------------------------- #


def operators(plan: Any) -> list[str]:
    """Every ``operator``/``operation`` string in an EXPLAIN plan tree."""
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("operator", "operation"):
                value = node.get(key)
                if isinstance(value, str):
                    found.append(value)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(plan)
    return found


def scans_table(plan: Any, table: str) -> bool:
    """True iff the plan TableScans ``table`` (operator==TableScan, attributes.table==table)."""
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


async def explain(connection: SurrealConnection, statement: str, params: dict[str, Any]) -> Any:
    """The EXPLAIN plan tree for ``statement`` (the shipped walker's ``… EXPLAIN`` idiom)."""
    return await run(connection, f"{statement} EXPLAIN", params)


async def apply_ddl(connection: SurrealConnection, ddl: str, *, url: str) -> None:
    """Apply a multi-statement DDL string through the production ``execute_transaction`` seam
    (store-ref §3: ``.query()`` validates statement[0] ONLY — a later failing statement is a
    SILENT partial apply; ``execute_transaction`` checks EVERY statement). Mirrors
    ``LocalMemoryBackend.ensure_ready`` / the 61b oracle's ``_apply_ddl``."""
    from loremaster.store._txn import execute_transaction

    async def _acquire() -> Any:
        return connection

    async def _never_drop(_c: Any) -> None:
        raise AssertionError("a DDL rejection must never drop the connection")

    await execute_transaction(
        f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_acquire, drop=_never_drop, url=url
    )


# --------------------------------------------------------------------------- #
# Offline DDL introspection (the ``test_agent_owns_principal_schema`` idiom — pin the emitter's
# output at string level, tolerant of the OVERWRITE clause).
# --------------------------------------------------------------------------- #

_DEFINE_FIELD = re.compile(r"^\s*DEFINE\s+FIELD\b", re.IGNORECASE)
_DEFINE_INDEX = re.compile(r"^\s*DEFINE\s+INDEX\b", re.IGNORECASE)


def ddl_statements(ddl: str) -> list[str]:
    """The DDL's individual statements, as the transaction sees them."""
    return [line.strip() for line in ddl.split(";") if line.strip()]


def field_statement(ddl: str, table: str, column: str) -> str | None:
    """The single ``DEFINE FIELD`` for ``<table>.<column>`` (None if absent); at-most-one."""
    matches = [
        statement
        for statement in ddl_statements(ddl)
        if _DEFINE_FIELD.match(statement)
        and re.search(
            rf"\bFIELD\s+(?:OVERWRITE\s+)?{re.escape(column)}\s+ON\s+{re.escape(table)}\b", statement
        )
    ]
    assert len(matches) <= 1, f"expected ≤1 DEFINE FIELD for {table}.{column}, got {matches!r}"
    return matches[0] if matches else None


def index_statement(ddl: str, table: str, column: str) -> str | None:
    """The single ``DEFINE INDEX`` over ``<table>.<column>`` (None if absent); at-most-one.

    Matches an index whose FIELDS clause LEADS with ``<column>`` as its SOLE column (a
    single-column index) so a composite that merely mentions the column is not mistaken for it
    (the §4.1 two-separate-indexes ruling — a composite is leading-column-only).

    ⚠ BLOCKER 1 (adversary-63a-2 #431, folded 2026-08-29): the pattern is NOT end-anchored. The
    governed-INDEX mutation pin (``test_the_governed_indexes_route_through_the_shared_emitter``)
    APPENDS ``COMMENT '…'`` to the whole ``DEFINE INDEX`` statement, so ``FIELDS scope`` is no
    longer at end-of-string — an end-anchored ``…$`` returned None on a CORRECT ``_plain_index``
    build and reddened the mutation pin (schema 23/24). ``FIELDS\\s+<col>\\b\\s*(?:UNIQUE\\b)?
    (?!\\s*,)`` TOLERATES a trailing clause (``COMMENT``, ``SEARCH ANALYZER``, …) while still
    rejecting a composite ``FIELDS scope, owner`` (the negative lookahead vetoes a following
    comma). Adversary-proven → schema 24/24."""
    matches = [
        statement
        for statement in ddl_statements(ddl)
        if _DEFINE_INDEX.match(statement)
        and re.search(rf"ON\s+{re.escape(table)}\b", statement, re.IGNORECASE)
        and re.search(
            rf"FIELDS\s+{re.escape(column)}\b\s*(?:UNIQUE\b)?(?!\s*,)", statement, re.IGNORECASE
        )
    ]
    assert len(matches) <= 1, f"expected ≤1 single-column DEFINE INDEX over {table}.{column}, got {matches!r}"
    return matches[0] if matches else None


# --------------------------------------------------------------------------- #
# Subjects — the identities. ≥2 principals × ≥2 agents each (F3/F4 quantifier law).
# --------------------------------------------------------------------------- #

# principal ↦ its agents; disjoint keep households wired in the fixtures.
PRINCIPAL_ALICE = "alice"
PRINCIPAL_BOB = "bob"
AGENTS = {
    PRINCIPAL_ALICE: ("ag_a1", "ag_a2"),
    PRINCIPAL_BOB: ("ag_b1", "ag_b2"),
}


def member(principal_id: str, agent_id: str, keeps: frozenset[str] = frozenset()) -> Any:
    """A member :class:`lorerunes.Subject` (SEC-F3: empty ids refused by construction)."""
    return pdp.Subject(
        principal_id=principal_id,
        agent_id=agent_id,
        role=pdp.PRINCIPAL_ROLE_MEMBER,
        visible_keep_ids=keeps,
    )


def admin(principal_id: str = PRINCIPAL_ALICE, agent_id: str = "ag_a1") -> Any:
    return pdp.Subject(
        principal_id=principal_id,
        agent_id=agent_id,
        role=pdp.PRINCIPAL_ROLE_ADMIN,
        visible_keep_ids=frozenset(),
    )


# --------------------------------------------------------------------------- #
# The governed table CASE — the parametrisation. 63a supplies MEMORY_CASE; 64 supplies
# TASK_CASE / FINDING_CASE and calls the SAME runners.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GovernedTableCase:
    """One governed table's contract inputs (design §3.2 — a family is parametrised by this)."""

    table: str
    #: Build the REAL current DDL (the emitter under test — e.g. ``generate_memory_ddl``).
    make_ddl: Callable[[], str]
    #: Seed one LEGACY row (no governed columns — a pre-retrofit row under the OLD DDL).
    seed_legacy: Callable[..., Awaitable[Any]]
    #: Seed one GOVERNED row with (owner_principal|None, owner_agent|None, scope|None).
    seed_governed: Callable[..., Awaitable[Any]]
    #: The tool's READ verbs and WRITE verbs (derived from its dispatch table; F3/F4 ∀).
    read_verbs: tuple[str, ...] = field(default_factory=tuple)
    write_verbs: tuple[str, ...] = field(default_factory=tuple)
    #: F5 (design §10.9-A): the SOURCE of the module whose raw mutations of ``table`` are enforced
    #: (e.g. ``lambda: Path(local.__file__).read_text()``), and the deny-by-default WRITE ALLOWLIST —
    #: one (site, justification, pin) triple per raw (unguarded) mutation of ``table``. A raw mutation
    #: NOT in the allowlist is a violation (deny-by-default). 64 supplies its table's own pair.
    mutation_source: Callable[[], str] | None = None
    write_allowlist: tuple[GovernedWriteAllowlistEntry, ...] = ()


# --------------------------------------------------------------------------- #
# MEMORY seeders — the real ``memory`` table shape (survey-63a-store: _MEMORY_FIELD_SPECS).
# A memory row REQUIRES note_text, kind, source (object), created_at, embedding (array<float>
# of width dim). Governed columns owner_principal/owner_agent (option<record<>>), scope
# (option<string>) exist only on the NEW (retrofitted) DDL.
# --------------------------------------------------------------------------- #

MEMORY_TABLE = "memory"
_PRINCIPAL_TABLE = "principal"
_AGENT_TABLE = "agent"


def _memory_content(dim: int, note_text: str) -> dict[str, Any]:
    """The REQUIRED (non-option, no-DEFAULT) memory columns for a seed CREATE."""
    now = datetime.now(UTC)
    return {
        "note_text": note_text,
        "kind": "fact",
        "source": {"kind": "test", "ref": None, "trust": "experiential"},
        "created_at": now,
        "embedding": [0.0] * dim,
    }


async def seed_memory_legacy(
    connection: SurrealConnection, *, row_id: str, dim: int, note_text: str | None = None
) -> Any:
    """A pre-retrofit memory row — NO governed columns (writable under OLD and NEW DDL)."""
    content = _memory_content(dim, note_text or f"legacy_{row_id}")
    return await run(
        connection,
        f"CREATE type::record('{MEMORY_TABLE}', $id) CONTENT $content",
        {"id": row_id, "content": content},
    )


async def seed_memory_governed(
    connection: SurrealConnection,
    *,
    row_id: str,
    dim: int,
    owner_principal: str | None,
    owner_agent: str | None,
    scope: str | None,
    note_text: str | None = None,
) -> Any:
    """A retrofitted memory row carrying the governed columns. ``None`` ⟺ the store column is
    NONE (the dirty-row shapes). Owners bind as ``type::record`` links (store-ref §2 — no live
    target needed for a record<> equality; the F2 plan is structural)."""
    content = _memory_content(dim, note_text or f"gov_{row_id}")
    if owner_principal is not None:
        content["owner_principal"] = pdp_record(_PRINCIPAL_TABLE, owner_principal)
    if owner_agent is not None:
        content["owner_agent"] = pdp_record(_AGENT_TABLE, owner_agent)
    if scope is not None:
        content["scope"] = scope
    return await run(
        connection,
        f"CREATE type::record('{MEMORY_TABLE}', $id) CONTENT $content",
        {"id": row_id, "content": content},
    )


def pdp_record(table: str, bare_id: str) -> Any:
    """A bound :class:`~surrealdb.RecordID` for a ``record<>`` column value (store-ref §2)."""
    from surrealdb import RecordID

    return RecordID(table, bare_id)


# --------------------------------------------------------------------------- #
# Store-side visibility helper — the SUBSTRATE read splice under test.
# --------------------------------------------------------------------------- #


def _bare(value: Any) -> str:
    text = str(getattr(value, "id", value))
    return text.split(":", 1)[-1] if ":" in text else text


async def read_filter_ids(
    connection: SurrealConnection, subject: Any, case: GovernedTableCase
) -> set[str]:
    """The ids a ``subject`` may READ over ``case.table`` — spliced via the SUBSTRATE seam
    ``governed.read_filter`` (design §1.2 item 2), NOT ``authorize_filter`` directly. RED until
    the substrate is built (``read_filter`` raises NotImplementedError). This is what makes F3
    a pin of the SUBSTRATE, and mutation-proves the ONE splice (R-a.3)."""
    from loremaster import governed

    fragment, params = governed.read_filter(subject, case.table)
    rows = await run(connection, f"SELECT id FROM {case.table} WHERE {fragment}", params)
    return {_bare(row["id"]) for row in (rows if isinstance(rows, list) else [])}


async def authorize_filter_ids(
    connection: SurrealConnection, subject: Any, action: Any, table: str
) -> set[str]:
    """The ids the PDP's ``authorize_filter`` (READ/mutating) selects over ``table`` — the
    store's own verdict, used by the F2 oracle. (Uses the PDP directly: F2 pins the PDP's
    correctness ON THE REAL DDL incl. dirty rows; the substrate leg is F3.)"""
    predicate = pdp.authorize_filter(subject, action, table)
    fragment, params = predicate.to_surql()
    rows = await run(connection, f"SELECT id FROM {table} WHERE {fragment}", params)
    return {_bare(row["id"]) for row in (rows if isinstance(rows, list) else [])}


# --------------------------------------------------------------------------- #
# Integration helpers — real stores on ONE unified test DB + a fake AgentRegistry (the seams
# resolve_subject / guarded_write depend on). Used by the substrate / retrofit / migration
# modules so each builds the same world without cloning the wiring.
# --------------------------------------------------------------------------- #


class FakeRegistry:
    """A minimal ``AgentRegistry`` stand-in for the substrate seams, mirroring the POST-#425 real
    seam SHAPE (design §10.3(iii) / FORK 3).

    The #425 closure keeps ``verify_capability -> str | None`` byte-compatible (13 shipped 62 call
    sites pin the BARE agent id) and moves the four admission conditions + the single verified
    SELECT into ONE internal pair-yielding path
    ``_verify_capability_owner(presented, token) -> (agent_id, owner_principal_id) | None`` that
    ``stamp_owner`` consumes in ONE round-trip. So the fake exposes EXACTLY that pair of methods,
    with ``verify_capability`` delegating to ``_verify_capability_owner()[0]`` — never a
    tuple-returning ``verify_capability``, the LITERAL shape §10.3 rejects: *a fake whose signature
    differs from the real seam is a fake that cannot fail.*

    A test wires the PAIR it wants (``(agent_id, owner_principal_id)``); the fail-closed pins wire
    ``None``. ``verify_calls`` counts LOGICAL round-trips — ONE increment per pair-path call,
    surrogate for the real registry's ONE-read #425 property (the round-trip count itself is pinned
    on the REAL registry in ``test_425_stamp_owner_63a.py``, form-agnostic)."""

    def __init__(self, verify_result: tuple[str, str] | None) -> None:
        self._verify_result = verify_result
        self.verify_calls = 0

    async def _verify_capability_owner(
        self, presented: str, access_token: Any
    ) -> tuple[str, str] | None:
        """The shared pair-path #425 collapses the double read into (design §5 / §10.3). ONE
        logical round-trip → ONE increment; ``stamp_owner`` consumes the returned pair."""
        self.verify_calls += 1
        return self._verify_result

    async def verify_capability(self, presented: str, access_token: Any) -> str | None:
        """Byte-identical to the real seam's shape: the BARE agent id (or ``None``), derived from
        the shared pair-path's first element — never the tuple (§10.3(iii))."""
        pair = await self._verify_capability_owner(presented, access_token)
        return None if pair is None else pair[0]


def access_token(*, subject: str, role: str = "member") -> Any:
    """A minimal transport :class:`~fastmcp.server.auth.AccessToken` whose ``subject`` is the
    principal email (``token_verifier`` sets ``subject = principal.email`` — survey-63a-pdp)."""
    from fastmcp.server.auth import AccessToken

    return AccessToken(
        token="t",
        client_id=f"api_key:{subject}",
        scopes=["lore:read"],
        subject=subject,
        claims={"role": role},
    )


def governed_overlay_ddl(table: str) -> str:
    """The §4.1 governed overlay (three columns + two indexes) as raw DDL — HAND-TRANSCRIBED
    verbatim from design §4.1 (exactly as ``probe_read_filter_63.py`` did), DELIBERATELY decoupled
    from the ``_governed_field_specs`` emitter. Rationale: the F2/F3/F4 filter/oracle pins test the
    FILTER over a real governed table; the EMITTER's correctness is the schema module's job
    (test_governed_schema_63a). Applying this overlay lets those pins seed governed rows + RED on
    the SUBSTRATE seam (read_filter/guarded_write), not on the emitter's absence. On a GREEN build
    the emitter ALSO emits these (OVERWRITE fields / IF NOT EXISTS indexes ⇒ a safe idempotent
    double-apply)."""
    return (
        f"DEFINE FIELD OVERWRITE owner_principal ON {table} TYPE option<record<principal>>;\n"
        f"DEFINE FIELD OVERWRITE owner_agent ON {table} TYPE option<record<agent>>;\n"
        f"DEFINE FIELD OVERWRITE scope ON {table} TYPE option<string>;\n"
        f"DEFINE INDEX IF NOT EXISTS {table}_scope ON {table} FIELDS scope;\n"
        f"DEFINE INDEX IF NOT EXISTS {table}_owner_principal ON {table} FIELDS owner_principal;\n"
    )


async def build_memory_backend(env: Any) -> Any:
    """A ready :class:`LocalMemoryBackend` on a fresh unified DB (a :class:`FakeEmbedder` +
    a no-op chunk oracle — the ``make_backend`` idiom, trimmed). Caller owns close + drop."""
    from loremaster.memory.local import LocalMemoryBackend
    from loresigil.testing import FakeEmbedder

    async def _no_chunks(_keys: Sequence[str]) -> set[str]:
        return set()

    backend = LocalMemoryBackend(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        dim=env.dim,
        user=env.user,
        password=env.password,
        embedder=FakeEmbedder(dim=env.dim),
        existing_chunks=_no_chunks,
    )
    await backend.ensure_ready()
    return backend


async def build_principal_and_keep_stores(env: Any) -> tuple[Any, Any]:
    """Construct a :class:`PrincipalStore` + :class:`KeepStore` on the SAME unified test DB and
    ``ensure_ready`` both (the 62 ``dangle_env`` idiom). Caller owns closing them + dropping."""
    from loremaster.keeps import KeepStore
    from loremaster.principals import PrincipalStore

    principal_store = PrincipalStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    keep_store = KeepStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await principal_store.ensure_ready()
    await keep_store.ensure_ready()
    return principal_store, keep_store


def store_handle(
    connection: SurrealConnection,
    *,
    url: str,
    on_acquire: Callable[[int], Awaitable[None]] | None = None,
) -> tuple[Any, dict[str, int]]:
    """A test :class:`~loremaster.store._txn.StoreHandle` over a shared, signed-in test connection,
    plus an ACQUIRE COUNTER — the BLOCKER-2 (design §10.6) substrate/migration seam. The
    substrate/migration modules build a handle THIS way so ``governed.guarded_write(store=…)`` /
    ``governed.report_unmigrated_governed_rows(store, …)`` reach the SAME per-test DB the fixture
    seeded, through the ONE retry/self-heal driver (never a raw connection — R4).

    Returns ``(handle, calls)``:
    - ``calls['acquire']`` counts every acquire the driver made through this handle — the
      MUTATION-PROOF instrument for §10.6 rider (iv): every guarded_write pin asserts
      ``calls['acquire'] >= 1``, so a build that bypasses the handle for ANY statement (a
      hand-rolled ``connection.query`` inside guarded_write) reddens.
    - ``on_acquire(n)`` (optional) fires BEFORE the n-th acquire returns the connection — the §10.6
      rider (iii) TOCTOU injection point: land a re-scope UPDATE on acquire #2, deterministically
      between guarded_write's pre-read (``run_query`` = acquire #1) and its guarded mutation
      (``execute_transaction`` = acquire #2), with NO 8-way race.

    ``drop`` is a no-op: the fixture owns the connection's lifecycle, so a substrate self-heal must
    NOT close it out from under the test (the real ``LocalMemoryBackend.handle`` wires the backend's
    own ``_drop_connection`` — that is the accessor the retrofit invalidate route uses)."""
    from loremaster.store._txn import StoreHandle

    calls = {"acquire": 0}

    async def _acquire() -> Any:
        calls["acquire"] += 1
        if on_acquire is not None:
            await on_acquire(calls["acquire"])
        return connection

    async def _drop(_connection: Any) -> None:
        return None

    return StoreHandle(acquire=_acquire, drop=_drop, url=url), calls


def python_allowed_ids(
    rows: Sequence[tuple[str, str | None, str | None, str | None]], subject: Any, action: Any
) -> set[str]:
    """The Python ``authorize`` verdict over a fixture row set (the ``matches`` side of F2).

    ⚠ Rows whose scope is NONE are EXCLUDED from the Python side here because
    ``lorerunes.Resource`` currently RAISES on a non-domain scope and ``scope`` is a required
    ``str`` (survey-63a-pdp; FORK 1 in REPORT-contract-63a.md). The NONE-scope single-brain leg
    is pinned OBSERVABLY through the substrate (``assert_dirty_scope_is_member_invisible``),
    NEVER by constructing ``Resource(scope=None)`` here — that would trap the builder (C-DEF)."""
    allowed: set[str] = set()
    for row_id, owner_principal, owner_agent, scope in rows:
        if scope is None:
            continue  # FORK 1 — pinned observably, not via Resource(scope=None)
        resource = pdp.Resource(
            table=MEMORY_TABLE,
            owner_principal=owner_principal,
            owner_agent=owner_agent,
            scope=scope,
        )
        if pdp.authorize(subject, action, resource).allowed:
            allowed.add(row_id)
    return allowed


# =========================================================================== #
# F5 — GOVERNED-TABLE WRITE-ENFORCEMENT COMPLETENESS (design §10.9-A, packet 63a-iv)
#
# The deny-by-default, coverage-as-a-checked-variable instrument that closes the
# enumerate-the-forbidden CLASS (memory write verbs were guarded ONE AT A TIME, each round green at
# every gate — the instrument lesson). REUSABLE, parametrised per governed table via
# GovernedTableCase.mutation_source + .write_allowlist; 63b (message) / 64 (task/finding) supply
# their own pair and call the SAME runners — NEVER a cloned module (design §3.2 RIDER).
#
# THREE layers (design §10.9-A):
#  L1 STRUCTURAL (AST, derived): every RAW SurrealQL mutation of the table, keyed by enclosing
#     function, must be ∈ the ALLOWLIST. A new unclassified raw mutation site REDS (deny-by-default).
#  L2a STRUCTURAL guard-context coverage: every allowlisted FRAME + guarded_write wraps its mutation
#     in ``governed.write_guard`` (reach as a checked variable — the allowlist grows → this covers it).
#  L2b RUNTIME (in the suite): the store seam is instrumented; every OBSERVED table mutation carries
#     a non-None ``governed.active_write_guard()`` context (a context-LESS mutation is UNCLASSIFIED),
#     across every seam path exercised. RED until the guard-context is built + wired.
# =========================================================================== #

_MUTATION_VERBS = ("UPSERT", "UPDATE", "DELETE", "REMOVE")


@dataclass(frozen=True, order=True)
class MutationSite:
    """A raw governed-table mutation, keyed by its enclosing function + the SurrealQL verb (design
    §10.9-A L1). The unit the allowlist classifies and the AST scan derives. ``order=True`` so a
    diagnostic ``sorted(derived - allowlist)`` renders deterministically."""

    function: str
    verb: str  # one of _MUTATION_VERBS (upper-cased)


@dataclass(frozen=True)
class GovernedWriteAllowlistEntry:
    """One deny-by-default allowlist entry (design §10.9-A layer 3): a (site, justification, pin,
    frames) 4-tuple. ``pin`` is the EVIDENCE — a test node/name whose existence justifies the raw
    write; an entry whose pin is deleted leaves the allowlist. ``frames`` are the functions that must
    wrap the statement's execution in ``governed.write_guard`` (the statement's enclosing function
    for a self-contained mutation; the CALLERS for a shared fragment-builder like _upsert_fragment)."""

    site: MutationSite
    justification: str
    pin: str
    frames: tuple[str, ...]


def _statement_shape(node: ast.expr) -> str | None:
    """Reconstruct a statement's SHAPE string from a Constant/JoinedStr — literal parts verbatim,
    ``{name}`` for a ``{var}`` interpolation, ``{EXPR}`` otherwise. Enough to recognise a SurrealQL
    mutation targeting a table whose name is an interpolated MODULE CONSTANT (``{MEMORY_TABLE}``)."""
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                inner = value.value
                parts.append("{" + inner.id + "}" if isinstance(inner, ast.Name) else "{EXPR}")
        return "".join(parts)
    return None


def _raw_mutation_of_table(shape: str, table: str, table_const_hint: str) -> str | None:
    """The mutation VERB iff ``shape`` is a raw SurrealQL statement whose verb IMMEDIATELY targets
    ``table`` (its literal name or interpolated module constant ``{table_const_hint}``), else None.

    ⚠ TABLE-TARGETED, not merely table-MENTIONING (packet 63a-v precision fix, finding #446 sibling):
    the verb's operand must BE the table — ``UPSERT/UPDATE/DELETE (type::record('<t>'|{HINT}) | <t> |
    {HINT})`` or ``REMOVE TABLE|FIELD|INDEX <t>``. This REJECTS prose that merely names a verb and the
    table in the same sentence. Live receipt: principals.py's SF-63-5 refusal message *"…the delete
    is refused … they own N governed {MEMORY_TABLE} row(s)…"* was matched by the OLD loose
    ``\\b(UPSERT|UPDATE|DELETE)\\s+(?:type::record\\(|\\{?\\w)`` (``delete`` + ``is``) AS A MEMORY
    DELETE — a false positive INVISIBLE while F5 scanned only ``memory/local.py``, surfaced the
    instant the whole-tree scan reached ``principals.py``. Docstrings are already excluded by
    :func:`_docstring_node_ids`; this closes the NON-docstring prose f-string hole (the P8d law:
    prose mentions carry no structural anchors, so anchor on the verb→target adjacency)."""
    target = (
        rf"(?:type::record\(\s*['\"]?)?"
        rf"(?:{re.escape(table)}\b|\{{{re.escape(table_const_hint)}\}})"
    )
    write = re.search(rf"\b(UPSERT|UPDATE|DELETE)\s+{target}", shape, re.IGNORECASE)
    if write is not None:
        return write.group(1).upper()
    remove = re.search(
        rf"\b(REMOVE)\s+(?:TABLE|FIELD|INDEX)\b\s+(?:IF\s+EXISTS\s+)?{target}",
        shape,
        re.IGNORECASE,
    )
    return "REMOVE" if remove is not None else None


def _enclosing_functions(tree: ast.AST) -> dict[int, str]:
    """Map each AST node id → the name of its nearest enclosing FunctionDef (``<module>`` if none)."""
    owner: dict[int, str] = {}

    def walk(node: ast.AST, current: str) -> None:
        name = node.name if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else current
        for child in ast.iter_child_nodes(node):
            owner[id(child)] = name
            walk(child, name)

    owner[id(tree)] = "<module>"
    walk(tree, "<module>")
    return owner


def _docstring_node_ids(tree: ast.AST) -> set[int]:
    """The node ids of every module/class/function docstring Constant (so prose naming a verb —
    'UPSERT the new row' — is never mistaken for a statement)."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                ids.add(id(body[0].value))
    return ids


def governed_table_raw_mutation_sites(
    source: str, table: str, *, table_const_hint: str = "MEMORY_TABLE"
) -> frozenset[MutationSite]:
    """AST-derive every RAW SurrealQL mutation STATEMENT of ``table`` in ``source``, keyed by
    enclosing function (design §10.9-A L1 — the ``_SCANNED_MEMBERS`` statement-shape idiom, NEVER a
    name list). Docstrings/prose excluded; only real SurrealQL mutation syntax counted. This is what
    makes a NEW unclassified write site RED — the derived set GROWS and the allowlist does not.

    ⚠ NAMED BOUND (finding #444 — WHEN YOU CANNOT CLOSE A HOLE, PIN IT): the scan targets the
    LITERAL table name or its interpolated module CONSTANT (``{MEMORY_TABLE}``). A raw write whose
    table name is a runtime VARIABLE (``tbl = self._which_table(); f"UPDATE type::record('{tbl}',
    …)"``) renders ``{tbl}`` in :func:`_statement_shape`, matches NEITHER anchor, and is never
    derived — so deny-by-default never fires for it (adversary-63a-iv §F-2, wrong-build D'). NOT
    closed deliberately: all real memory sites use the ``MEMORY_TABLE`` constant, so widening the
    scan to a dynamic table name buys nothing and adds false-positive risk. This bound is PINNED by
    ``test_memory_enforcement_bounds_63a_iv.py`` (it goes RED the day the scan is widened to catch a
    dynamically-named site — delete the pin then and say so). RE-OPEN TRIGGER: any production write
    that constructs a governed table name dynamically (a non-constant table argument)."""
    tree = ast.parse(source)
    owner = _enclosing_functions(tree)
    docstrings = _docstring_node_ids(tree)
    sites: set[MutationSite] = set()
    for node in ast.walk(tree):
        if id(node) in docstrings or not isinstance(node, (ast.Constant, ast.JoinedStr)):
            continue
        shape = _statement_shape(node)
        if not shape:
            continue
        verb = _raw_mutation_of_table(shape, table, table_const_hint)
        if verb is None:
            continue
        sites.add(MutationSite(function=owner.get(id(node), "<module>"), verb=verb))
    return frozenset(sites)


def governed_table_guarded_write_frames(
    source: str, table: str, *, table_const_hint: str = "MEMORY_TABLE"
) -> frozenset[str]:
    """Every function calling ``guarded_write(table=<table>)`` — the GUARDED (safe-by-construction)
    set. A guarded_write call carries no raw mutation string (governed.py builds it), so it is NOT a
    raw site; this set is reported for completeness / the L1 anti-vacuity leg."""
    tree = ast.parse(source)
    owner = _enclosing_functions(tree)
    frames: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or call_name(node) != "guarded_write":
            continue
        for keyword in node.keywords:
            if keyword.arg == "table":
                value = keyword.value
                hit = (isinstance(value, ast.Name) and value.id == table_const_hint) or (
                    isinstance(value, ast.Constant) and value.value == table
                )
                if hit:
                    frames.add(owner.get(id(node), "<module>"))
    return frozenset(frames)


def call_name(call: ast.Call) -> str | None:
    """The called name of an ``ast.Call`` — the attribute (``a.b()`` → ``b``) or the bare id
    (``f()`` → ``f``), else None. ONE implementation for every AST scanner here (and the per-table
    modules), so a scanner never re-hand-rolls the func-name idiom."""
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def function_calls_named(source: str, function: str, called: str) -> bool:
    """True iff ``function`` (in ``source``) calls ``<called>(...)`` / ``<x>.<called>(...)`` anywhere
    in its body. ONE implementation for every "does this frame enter a named context manager" scan
    (design §10.9-A L2a — a frame that sets its own attribution channel): ``write_guard`` for a
    guarded local write, ``governed_exempt`` for the admin-CLI migrate site (§10.9-A CORRECTION
    step 4). Keyed on the CALLED name only, so it is table- and channel-agnostic (63b/64 reuse)."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function:
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call) and call_name(inner) == called:
                    return True
    return False


def function_calls_write_guard(source: str, function: str) -> bool:
    """True iff ``function`` (in ``source``) calls ``write_guard(...)`` / ``governed.write_guard(...)``
    (design §10.9-A L2a — the frame sets its own guard context). RED at HEAD (unwired). ONE
    IMPLEMENTATION: delegates to :func:`function_calls_named` (the channel-agnostic scan)."""
    return function_calls_named(source, function, "write_guard")


@dataclass(frozen=True)
class ObservedWrite:
    """One governed-table mutation observed at the store seam under test (design §10.9-A L2b).

    ``exempt`` and ``origin_site`` are the §10.9-A CORRECTION (packet 63a-v) both-ways channel: a
    non-``write_guard`` admin site (the migrate-governed backfill) carries a NAMED
    :func:`governed.governed_exempt` token instead of a label, and the observer records the
    ORIGINATING production ``(file, symbol)`` INDEPENDENTLY from the call stack (the ``_sdk_guard``
    precedent) — so a site BORROWING another site's exempt token fails the ``(file, symbol)`` match
    (design step 4) and F5's own runtime reach becomes a checked variable (finding #446). Both
    default so the 63a-iv construction ``ObservedWrite(label=…, verb=…, seam=…)`` is unchanged."""

    label: str | None  # the active write_guard label, or None (an UNCLASSIFIED write — the red signal)
    verb: str
    seam: str  # which seam function ran it (execute_transaction / run_query / execute_read_transaction)
    exempt: str | None = None  # the active governed_exempt NAME (or None) — the admin-attribution channel
    origin_site: tuple[str, str] | None = None  # (repo-relative file, function) of the originating prod frame


def _mutation_verb_for_table(statement: str, table: str) -> str | None:
    """The mutation verb if ``statement`` (a RESOLVED runtime statement, possibly a BEGIN…COMMIT
    block) mutates ``table`` — else None (a read, or a mutation of another table). The audit CREATE
    inside a composed guarded txn targets ``audit`` (not ``table``), so it is correctly ignored."""
    for verb, pattern in (
        ("UPSERT", rf"\bUPSERT\s+type::record\('{re.escape(table)}'"),
        ("UPDATE", rf"\bUPDATE\s+type::record\('{re.escape(table)}'"),
        ("DELETE", rf"\bDELETE\s+type::record\('{re.escape(table)}'"),
        ("REMOVE", rf"\bREMOVE\s+TABLE\s+(?:IF\s+EXISTS\s+)?{re.escape(table)}\b"),
        # table-form (UPDATE <table> SET … / DELETE <table> …), tolerated for 64's verbs.
        ("UPDATE", rf"\bUPDATE\s+{re.escape(table)}\b"),
        ("DELETE", rf"\bDELETE\s+{re.escape(table)}\b"),
    ):
        if re.search(pattern, statement, re.IGNORECASE):
            return verb
    return None


@contextlib.contextmanager
def observe_governed_table_writes(
    table: str, *, extra_modules: Sequence[ModuleType] | None = None
) -> Iterator[list[ObservedWrite]]:
    """Instrument the STORE SEAM (design §10.9-A L2b): patch the ``execute_transaction`` / ``run_query``
    / ``execute_read_transaction`` names IMPORTED INTO ``loremaster.memory.local`` +
    ``loremaster.governed`` so every statement mutating ``table`` is recorded together with the active
    ``governed.active_write_guard()`` label at call time. Patching the imported names (not the source
    module) is required — the seams are bound by name in each module (finding: monkeypatch the imported
    name). getattr-tolerant on the guard-context: at HEAD ``active_write_guard`` is unbuilt → every
    observed mutation records label=None → the F5 runtime pin reds (deny-by-default).

    ⚠ NAMED BOUND (finding #445 — L2b runtime reach): the L2b battery observes the three
    MEMBER-VERB seam paths (remember→execute_transaction, _reinforce→run_query,
    guarded_write→execute_read_transaction). The two remaining allowlisted frames — ``_replay_record``
    and ``_recreate_memory_table`` — are boot/admin/replay paths NOT exercised by the battery, so
    they carry L2a (structural ``function_calls_write_guard``) coverage ONLY; a runtime-escape inside
    them would pass both layers unobserved. Right-sized (design §10.9-A: "a production-mode assert is
    OPTIONAL") — both are boot/admin, never member verbs, and every member-reachable write carries
    BOTH structural + runtime coverage. RE-OPEN TRIGGER: either frame becoming member-reachable, or
    the L2b battery being asked to certify a boot/admin write path.

    ⚠ 63a-v EXTENSION (design §10.9-A CORRECTION, finding #446): ``extra_modules`` widens the seam
    reach BEYOND the two default modules — the 63a-v L2b battery passes the modules DERIVED from the
    whole-tree allowlist files (:func:`seam_modules_for_tree_allowlist`), so ``principals`` (the
    migrate-governed backfill seam) is instrumented too. This makes the OBSERVER's OWN reach a
    checked variable (F5's reach was a hidden constant `local.py` — the class #446 closes): a NEW
    allowlisted site in a NEW file joins the observer's patch-set by the same derivation. Each
    observed mutation also records its NAMED ``governed.active_exempt()`` token (the admin channel,
    getattr-tolerant → None at HEAD) and its ORIGINATING production ``(file, symbol)`` from the call
    stack, so :func:`classify_tree_observed_write` can catch a site borrowing another's exempt token
    (design step 4)."""
    import loremaster.governed as governed_mod
    import loremaster.memory.local as local_mod

    observed: list[ObservedWrite] = []
    read_guard = getattr(governed_mod, "active_write_guard", lambda: None)
    read_exempt = getattr(governed_mod, "active_exempt", lambda: None)

    def _statement_of(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str | None:
        candidate = kwargs.get("statement", args[0] if args else None)
        return candidate if isinstance(candidate, str) else None

    def _wrap(original: Callable[..., Any], seam: str) -> Callable[..., Any]:
        async def _instrumented(*args: Any, **kwargs: Any) -> Any:
            statement = _statement_of(args, kwargs)
            if statement is not None:
                verb = _mutation_verb_for_table(statement, table)
                if verb is not None:
                    observed.append(
                        ObservedWrite(
                            label=read_guard(),
                            verb=verb,
                            seam=seam,
                            exempt=read_exempt(),
                            origin_site=_originating_prod_site(),
                        )
                    )
            return await original(*args, **kwargs)

        return _instrumented

    default_targets = [
        (local_mod, "execute_transaction", "execute_transaction"),
        (local_mod, "run_query", "run_query"),
        (governed_mod, "execute_read_transaction", "execute_read_transaction"),
        (governed_mod, "run_query", "run_query"),
    ]
    extra_targets = [
        (module, attr, attr)
        for module in (extra_modules or ())
        for attr in ("execute_transaction", "run_query", "execute_read_transaction")
    ]
    patches: list[tuple[Any, str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for module, attr, seam in default_targets + extra_targets:
        key = (id(module), attr)
        if key in seen:
            continue  # dedupe so a module passed in extra_modules is not double-patched (breaks restore)
        seen.add(key)
        original = getattr(module, attr, None)
        if original is None:
            continue
        patches.append((module, attr, original))
        setattr(module, attr, _wrap(original, seam))
    try:
        yield observed
    finally:
        for module, attr, original in patches:
            setattr(module, attr, original)


# =========================================================================== #
# F5 WHOLE-TREE REACH (design §10.9-A CORRECTION, packet 63a-v, finding #446)
#
# #446: F5's OWN reach was a hidden constant — L1 scanned ``memory/local.py`` ONLY (the
# ``_local_source`` hand-pick), so the governed ``scope`` write in
# ``principals.py::_migrate_memory_scope`` was INVISIBLE to all three layers. The class §10.9
# exists to close (reach-as-hidden-constant), reproduced INSIDE the instrument built to close it.
#
# THE CORRECTION (design §10.9-A CORRECTION): L1's file set is an OUTPUT, never an input. The
# scanner takes NO file list — it walks the production source of EVERY workspace member, the member
# roots DERIVED from ``[tool.uv.workspace] members`` (the ``registration_sites.py`` seam), so a NEW
# file gaining a governed write of ``table`` grows the derived set and REDS until classified
# (deny-by-default over the whole tree). Parametrised by TABLE — 63b passes MESSAGE_TABLE/TO_RELATION,
# 64 passes task/finding; the memory instance is its first parametrisation (ONE implementation).
# =========================================================================== #

#: The workspace repo root — ``loremaster/tests/_governed_contract.py`` → parents[2]. The ONE place
#: the whole-tree scan and the stack-origin walk derive member roots from (never a hand-list).
_REPO_ROOT = Path(__file__).resolve().parents[2]


def declared_workspace_members(repo_root: Path = _REPO_ROOT) -> tuple[str, ...]:
    """The workspace members, read from the ONE file that defines them — ``[tool.uv.workspace]
    members`` in ``pyproject.toml`` (the SAME from-truth seam as
    ``scripts/registration_sites.py::declared_members``; a member joins F5's reach by the same
    derivation that registers it everywhere else). Sorted for determinism."""
    manifest = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    members: list[str] = manifest["tool"]["uv"]["workspace"]["members"]
    return tuple(sorted(members))


def derive_member_source_roots(repo_root: Path = _REPO_ROOT) -> tuple[Path, ...]:
    """The PRODUCTION package root of every workspace member, DERIVED from the members list (design
    §10.9-A CORRECTION step 1). For a member dir ``<m>`` the production package is ``<m>/<m>`` (the
    uv-workspace convention here — verified: all four members carry ``<m>/<m>/__init__.py``); the
    test tree ``<m>/tests`` is a sibling, excluded by walking the package dir. NEVER a hand-picked
    file or a ``[local.py, principals.py]`` list: a builder that hard-codes such a list makes this
    derivation FALSE (pinned). Resolved, existence-filtered."""
    roots: list[Path] = []
    for member in declared_workspace_members(repo_root):
        package = (repo_root / member / member).resolve()
        if package.is_dir():
            roots.append(package)
    return tuple(roots)


def _iter_member_python_files(roots: Sequence[Path]) -> Iterator[Path]:
    """Every production ``.py`` under the member roots, EXCLUDING test trees (a ``tests`` path
    component / ``test_*.py`` / ``conftest.py`` — the existing convention). Deterministic order."""
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            if "tests" in path.parts or path.name.startswith("test_") or path.name == "conftest.py":
                continue
            yield path


@dataclass(frozen=True, order=True)
class TreeMutationSite:
    """A raw governed-table mutation across the WHOLE workspace tree, keyed by (repo-relative posix
    file, enclosing function, verb) — the whole-tree analog of :class:`MutationSite` (design §10.9-A
    CORRECTION L1). ``file`` distinguishes same-named functions in different modules; ``order=True``
    renders a deterministic diagnostic ``sorted(derived - allowlisted)``."""

    file: str
    function: str
    verb: str


def governed_table_raw_mutation_sites_in_tree(
    table: str,
    *,
    repo_root: Path = _REPO_ROOT,
    table_const_hint: str = "MEMORY_TABLE",
) -> frozenset[TreeMutationSite]:
    """AST-derive every RAW SurrealQL mutation of ``table`` across the production source of EVERY
    workspace member (design §10.9-A CORRECTION step 1). Takes NO file list: the member roots are
    DERIVED from ``[tool.uv.workspace] members`` under ``repo_root`` (the live call passes the real
    repo; the fixture-tree discriminator passes a synthetic repo whose ``pyproject.toml`` declares
    synthetic members — so the discriminator exercises the from-truth root derivation END-TO-END,
    not a ``roots=`` override). Per-file derivation reuses the local.py-scoped
    :func:`governed_table_raw_mutation_sites` (ONE implementation of the statement-shape scan — the
    #444 concatenation bound + the docstring/prose exclusion are inherited, table-parametrised).

    This is what makes F5's reach a CHECKED VARIABLE (finding #446): a NEW file anywhere in the tree
    gaining a governed ``table`` write GROWS the derived set → deny-by-default reds until it is
    classified. A builder that keeps a hand-list (``local.py`` only, or ``[local, principals]``)
    fails the from-truth roots pin AND the whole-tree grows-and-reds discriminator."""
    walk_roots = derive_member_source_roots(repo_root)
    sites: set[TreeMutationSite] = set()
    for path in _iter_member_python_files(walk_roots):
        rel = path.relative_to(repo_root).as_posix() if path.is_relative_to(repo_root) else path.as_posix()
        for site in governed_table_raw_mutation_sites(
            path.read_text(encoding="utf-8"), table, table_const_hint=table_const_hint
        ):
            sites.add(TreeMutationSite(file=rel, function=site.function, verb=site.verb))
    return frozenset(sites)


@dataclass(frozen=True)
class TreeWriteAllowlistEntry:
    """One WHOLE-TREE deny-by-default allowlist entry (design §10.9-A CORRECTION). Extends the
    local.py :class:`GovernedWriteAllowlistEntry` with the FILE (a tree site is (file, function,
    verb)) and the L2 ATTRIBUTION CHANNEL:

    - ``exempt_name`` — the NAMED ``governed.governed_exempt`` token a non-``write_guard`` admin site
      carries (design step 4: migrate-governed uses ``governed_exempt("migrate-governed")`` rather
      than ``write_guard``, because it is NOT member-reachable — exempt-WITH-JUSTIFICATION, never
      silently dropped). ``None`` ⟺ the site attributes via ``write_guard`` frames instead.
    - ``runtime_observed`` — whether the L2b battery exercises the site. The #445 boot/admin bound:
      ``_recreate_memory_table`` / ``_replay_record`` carry L2a structural coverage ONLY (never
      member verbs), so they are ``runtime_observed=False`` with their named re-open trigger."""

    site: TreeMutationSite
    justification: str
    pin: str
    frames: tuple[str, ...]
    exempt_name: str | None = None
    runtime_observed: bool = True


def _originating_prod_site() -> tuple[str, str] | None:
    """The ORIGINATING production ``(repo-relative file, function)`` for the mutation being observed
    — the nearest call-stack frame executing under a workspace-member PRODUCTION root (design
    §10.9-A CORRECTION step 2; the ``_sdk_guard`` ``co_filename`` walk). This substrate and the test
    trees live under ``<m>/tests`` (a sibling of ``<m>/<m>``), so they are NOT under a production
    root and are skipped — the first matching frame is the real caller (e.g.
    ``_migrate_memory_scope``). ``None`` when no production frame is on the stack (a mutation issued
    directly by a test — an escape with no production origin)."""
    roots = derive_member_source_roots()
    frame: Any = sys._getframe(1)
    while frame is not None:
        try:
            resolved = Path(frame.f_code.co_filename).resolve()
        except (OSError, ValueError):  # pragma: no cover - defensive on a synthetic/exec frame
            frame = frame.f_back
            continue
        if any(resolved.is_relative_to(root) for root in roots):
            rel = (
                resolved.relative_to(_REPO_ROOT).as_posix()
                if resolved.is_relative_to(_REPO_ROOT)
                else resolved.as_posix()
            )
            return (rel, frame.f_code.co_name)
        frame = frame.f_back
    return None


def classify_tree_observed_write(
    observed: ObservedWrite, allowlist: Sequence[TreeWriteAllowlistEntry]
) -> bool:
    """True iff the observed mutation is ATTRIBUTED (design §10.9-A CORRECTION L2b, deny-by-default,
    ONE uniform rule): EITHER it carries a ``write_guard`` label, OR it carries a NAMED
    ``governed_exempt`` token whose allowlist entry's site MATCHES the stack-derived origin. A site
    BORROWING another site's token fails the ``(file, symbol)`` match (design step 4). A mutation
    matching neither is UNCLASSIFIED (the red signal). getattr-tolerant at HEAD: ``active_exempt`` is
    unbuilt → ``exempt`` is None → the migrate write is unclassified → RED-until-built."""
    if observed.label is not None:
        return True
    if observed.exempt is None or observed.origin_site is None:
        return False
    for entry in allowlist:
        if entry.exempt_name == observed.exempt:
            return (entry.site.file, entry.site.function) == observed.origin_site
    return False


def _module_for_repo_relative_file(rel: str, repo_root: Path = _REPO_ROOT) -> ModuleType | None:
    """Import the module for a repo-relative production file path (e.g.
    ``loremaster/loremaster/principals.py`` → ``loremaster.principals``). Derives the dotted name
    relative to the member DIR, so the observer's patch-set is DERIVED from the allowlist files (not
    a hand-list of modules) — the observer's own reach a checked variable (#446). None if the path
    is under no known member dir."""
    parts = Path(rel).with_suffix("").parts
    for member in declared_workspace_members(repo_root):
        if len(parts) >= 2 and parts[0] == member:
            return importlib.import_module(".".join(parts[1:]))
    return None


def seam_modules_for_tree_allowlist(
    allowlist: Sequence[TreeWriteAllowlistEntry], repo_root: Path = _REPO_ROOT
) -> tuple[ModuleType, ...]:
    """The distinct modules whose store seam the L2b observer must patch — DERIVED from the
    whole-tree allowlist entries' files (design §10.9-A CORRECTION step 2, the observer's reach a
    checked variable). Passed as ``observe_governed_table_writes(..., extra_modules=…)`` so a NEW
    allowlisted site in a NEW file joins the observer's patch-set by the same derivation that
    classifies it (never a hand-list of modules)."""
    modules: list[ModuleType] = []
    seen: set[str] = set()
    for entry in allowlist:
        module = _module_for_repo_relative_file(entry.site.file, repo_root)
        if module is not None and module.__name__ not in seen:
            seen.add(module.__name__)
            modules.append(module)
    return tuple(modules)
