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

import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
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

    Matches an index whose FIELDS clause is EXACTLY ``<column>`` (a single-column index) so a
    composite that merely mentions the column is not mistaken for it (the §4.1 two-separate-
    indexes ruling — a composite is leading-column-only)."""
    matches = [
        statement
        for statement in ddl_statements(ddl)
        if _DEFINE_INDEX.match(statement)
        and re.search(rf"ON\s+{re.escape(table)}\b", statement, re.IGNORECASE)
        and re.search(rf"FIELDS\s+{re.escape(column)}\s*(?:UNIQUE)?\s*$", statement, re.IGNORECASE)
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
