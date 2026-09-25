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
import asyncio
import contextlib
import re
import tomllib
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar
from weakref import WeakKeyDictionary

import _sdk_guard
import yaml
from _logging_fixtures import module_level_bindings_of
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


# --------------------------------------------------------------------------- #
# MEMORY seeders — the real ``memory`` table shape (survey-63a-store: _MEMORY_FIELD_SPECS).
# A memory row REQUIRES note_text, kind, source (object), created_at, embedding (array<float>
# of width dim). Governed columns owner_principal/owner_agent (option<record<>>), scope
# (option<string>) exist only on the NEW (retrofitted) DDL.
# --------------------------------------------------------------------------- #

MEMORY_TABLE = "memory"
MESSAGE_TABLE = "message"  # 63b-ii-b: the message node table (seed_message_legacy's target).
AGENT_TABLE = "agent"  # 63c-i-a: the agent node table (seed_agent_* target; the Q1(c) population).
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
# MESSAGE seeder (63b-ii-b §12.6 step 0) — the ONE raw legacy-``message`` writer both dirty-store
# legs share (F-DUP / ONE IMPLEMENTATION: a second raw-CREATE clone is the #102 seam).
# --------------------------------------------------------------------------- #


async def seed_message_legacy(
    connection: SurrealConnection,
    *,
    sender_id: str,
    session: str,
    seq: int,
    row_id: str | None = None,
    **overrides: Any,
) -> str:
    """A RAW ``CREATE message`` that BYPASSES the ledger's app caps — the hypothesis under test in the
    §12.6 dirty-store legs (a row the app cap would REFUSE). Writes every REQUIRED birth column with a
    legal default, binds ``sender`` as a ``record<agent>`` LINK (store-ref §2), leaves the governed
    columns (``owner_principal``/``owner_agent``/``scope``) UNSET (a pre-cutover legacy row — an
    ``option<>`` unset reads NONE), and applies any ``**overrides`` VERBATIM (e.g.
    ``body="z"*(MESSAGE_BODY_MAX_CHARS+1)``, ``grade="urgent"``, ``refs=[...]``). ``CONTENT`` (never
    ``SET session=$session``) — ``session`` is a PROTECTED variable name (store-ref §2). Returns the
    bare message id.

    ONE IMPLEMENTATION (63b-ii-b §12.6 step 0): both dirty-store legs + Leg B call THIS, never a second
    raw-CREATE clone (``test_comms_schema.py::_create_message`` predates it; this is the shared home so
    the two files cannot drift about what a legacy row's shape is)."""
    message_id = row_id if row_id is not None else uuid.uuid4().hex
    content: dict[str, Any] = {
        "seq": seq,
        "session": session,
        "thread": overrides.pop("thread", session),
        "sender": pdp_record(_AGENT_TABLE, sender_id),
        "grade": overrides.pop("grade", "signal"),
        "body": overrides.pop("body", f"legacy body {seq}"),
        "refs": overrides.pop("refs", []),
        "task_id": overrides.pop("task_id", None),
        "question": overrides.pop("question", False),
        "created_at": overrides.pop("created_at", datetime.now(UTC)),
    }
    # governed overlay columns, only when a caller stamps them (a legacy row leaves them NONE):
    for governed_col in ("owner_principal", "owner_agent", "scope"):
        if governed_col in overrides:
            content[governed_col] = overrides.pop(governed_col)
    content.update(overrides)  # any remaining explicit column, verbatim.
    await run(
        connection,
        f"CREATE type::record('{MESSAGE_TABLE}', $id) CONTENT $content",
        {"id": message_id, "content": content},
    )
    return message_id


# --------------------------------------------------------------------------- #
# AGENT seeders (63c-i-a §4.4 / §6) — the ONE raw legacy/governed-``agent`` writers, lifted here
# beside the message seeders (F-DUP / ONE IMPLEMENTATION: a second raw-CREATE clone is the #102 seam;
# the probe's ad-hoc ``_downgrade`` helpers were the precedent, NOT the home). Every 63c agent
# dirty-store / migrate leg calls THESE, so the schema + migrate contract files cannot drift about
# what a legacy agent row's shape is.
# --------------------------------------------------------------------------- #


def _agent_content(*, name: str, session: str, role: str, status: str) -> dict[str, Any]:
    """The REQUIRED (non-``option``) birth columns for an ``agent`` CREATE — ``name``/``session``
    (identifier charset at HEAD), ``role`` (non-empty at HEAD), ``status`` (the closed domain,
    KEPT — §4.2), and the two app-stamped datetimes. Every other ``_AGENT_FIELD_SPECS`` column is
    ``option<>`` (unset ⇒ NONE, un-poisoning), so a birth-only content is a valid row."""
    now = datetime.now(UTC)
    return {
        "name": name,
        "session": session,
        "role": role,
        "status": status,
        "registered_at": now,
        "heartbeat_at": now,
    }


async def seed_agent_legacy(
    connection: SurrealConnection,
    *,
    row_id: str,
    name: str,
    session: str,
    role: str = "builder",
    status: str = "active",
    **overrides: Any,
) -> str:
    """A RAW ``CREATE agent`` that BYPASSES ``AgentRegistry``'s app caps — the hypothesis under test in
    the §4.4 dirty-store legs (a row the writer would REFUSE: ``role=""`` / a hostile ``name``). Writes
    the REQUIRED birth columns with the given values, leaves the governed columns
    (``owner_principal``/``owner_agent``/``scope``) UNSET unless a caller stamps them (a pre-cutover
    legacy row — an ``option<>`` unset reads NONE), and applies any ``**overrides`` VERBATIM (e.g.
    ``role=""``, ``name="Bad Name!"``, ``status="urgent"``). ``CONTENT`` (never ``SET session=$session``)
    — ``session`` is a PROTECTED variable name (store-ref §2). Returns the bare agent id.

    ONE IMPLEMENTATION (§4.4 step 0): the Leg-A / Leg-B / heartbeat legs call THIS, never a second
    raw-CREATE clone (``test_agent_owns_principal_schema.py::_create_agent`` predates it; this is the
    shared home so those files cannot drift about a legacy agent's shape)."""
    agent_id = row_id
    content = _agent_content(name=name, session=session, role=role, status=status)
    for governed_col in ("owner_principal", "owner_agent", "scope"):
        if governed_col in overrides:
            content[governed_col] = overrides.pop(governed_col)
    content.update(overrides)  # any remaining explicit column, verbatim (role=""/name=hostile/...).
    await run(
        connection,
        f"CREATE type::record('{AGENT_TABLE}', $id) CONTENT $content",
        {"id": agent_id, "content": content},
    )
    return agent_id


async def seed_agent_governed(
    connection: SurrealConnection,
    *,
    row_id: str,
    name: str,
    session: str,
    role: str = "builder",
    status: str = "active",
    owner_principal: str | None,
    owner_agent: str | None,
    scope: str | None,
    **overrides: Any,
) -> str:
    """A retrofitted ``agent`` row carrying the governed columns. ``None`` ⟺ the store column is NONE
    (the dirty-row shapes — e.g. ``scope=None, owner_principal=<a 2nd principal>`` for the R-Q5-1
    row-precondition). Owners bind as ``type::record`` links (store-ref §2 — no live target needed for
    a ``record<>`` equality). ``**overrides`` apply verbatim (a hostile ``role``/``name`` under a
    governed shape). Returns the bare agent id."""
    agent_id = row_id
    content = _agent_content(name=name, session=session, role=role, status=status)
    if owner_principal is not None:
        content["owner_principal"] = pdp_record(_PRINCIPAL_TABLE, owner_principal)
    if owner_agent is not None:
        content["owner_agent"] = pdp_record(_AGENT_TABLE, owner_agent)
    if scope is not None:
        content["scope"] = scope
    content.update(overrides)
    await run(
        connection,
        f"CREATE type::record('{AGENT_TABLE}', $id) CONTENT $content",
        {"id": agent_id, "content": content},
    )
    return agent_id


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


def frozen_asserted_message_ddl() -> str:
    """A FROZEN capture of ``message``'s ASSERT-bearing DDL as ``generate_message_ddl()`` emitted it
    at ``0566587`` — the five ASSERT-bearing rows verbatim + the governed overlay (63b-ii-b §12.6).
    ⚠ HAND-CAPTURED, NOT re-derived from the emitter: the whole point is that this OLD world SURVIVES
    the emitter dropping the asserts (an emitter-derived old world would drop them too). ONE
    IMPLEMENTATION — Leg A (drop lands, ``test_comms_schema.py``) and Leg B's C-control (migrate
    raises, ``test_message_migrate_dirty_store_63b_ii_b.py``) BOTH call this, so the two files cannot
    drift about what production's asserted shape is. A
    ``test_the_frozen_old_world_is_a_faithful_asserted_capture`` control pins that this constant still
    carries all four length/grade ASSERT literals (self-consistency — NEVER a comparison to the live
    emitter, which the ii-b build is designed to change; see that control's docstring)."""
    table = MESSAGE_TABLE
    return (
        f"DEFINE TABLE IF NOT EXISTS {table} SCHEMAFULL;\n"
        f"DEFINE FIELD OVERWRITE seq ON {table} TYPE int;\n"
        f"DEFINE FIELD OVERWRITE session ON {table} TYPE string;\n"
        f"DEFINE FIELD OVERWRITE thread ON {table} TYPE string ASSERT string::len($value) <= 256;\n"
        f"DEFINE FIELD OVERWRITE sender ON {table} TYPE record<{_AGENT_TABLE}>;\n"
        f"DEFINE FIELD OVERWRITE grade ON {table} TYPE string ASSERT $value IN ['signal', 'directive'];\n"
        f"DEFINE FIELD OVERWRITE body ON {table} TYPE string ASSERT string::len($value) <= 4000;\n"
        f"DEFINE FIELD OVERWRITE refs ON {table} TYPE array<string> DEFAULT [] "
        f"ASSERT array::len($value) <= 20;\n"
        f"DEFINE FIELD OVERWRITE refs[*] ON {table} TYPE string ASSERT string::len($value) <= 256;\n"
        f"DEFINE FIELD OVERWRITE task_id ON {table} TYPE option<string> "
        f"ASSERT string::len($value) <= 256;\n"
        f"DEFINE FIELD OVERWRITE question ON {table} TYPE bool DEFAULT false;\n"
        f"DEFINE FIELD OVERWRITE created_at ON {table} TYPE datetime;\n"
        f"DEFINE FIELD OVERWRITE owner_principal ON {table} TYPE option<record<principal>>;\n"
        f"DEFINE FIELD OVERWRITE owner_agent ON {table} TYPE option<record<{_AGENT_TABLE}>>;\n"
        f"DEFINE FIELD OVERWRITE scope ON {table} TYPE option<string>;\n"
    )


def unbounded_message_ddl() -> str:
    """The ``message`` node + governed overlay with NO ASSERT on any field — a world that NEVER
    shipped (it exists to ACCEPT the violators Leg B migrates). Every birth field, ``refs`` DEFAULT [],
    ``question`` DEFAULT false, the three governed columns option<>. Leg B seeds its six legacy
    violators under THIS, then migrates the SCHEMA with the current emitter (63b-ii-b §12.6 Leg B)."""
    table = MESSAGE_TABLE
    return (
        f"DEFINE TABLE IF NOT EXISTS {table} SCHEMAFULL;\n"
        f"DEFINE FIELD OVERWRITE seq ON {table} TYPE int;\n"
        f"DEFINE FIELD OVERWRITE session ON {table} TYPE string;\n"
        f"DEFINE FIELD OVERWRITE thread ON {table} TYPE string;\n"
        f"DEFINE FIELD OVERWRITE sender ON {table} TYPE record<{_AGENT_TABLE}>;\n"
        f"DEFINE FIELD OVERWRITE grade ON {table} TYPE string;\n"
        f"DEFINE FIELD OVERWRITE body ON {table} TYPE string;\n"
        f"DEFINE FIELD OVERWRITE refs ON {table} TYPE array<string> DEFAULT [];\n"
        f"DEFINE FIELD OVERWRITE refs[*] ON {table} TYPE string;\n"
        f"DEFINE FIELD OVERWRITE task_id ON {table} TYPE option<string>;\n"
        f"DEFINE FIELD OVERWRITE question ON {table} TYPE bool DEFAULT false;\n"
        f"DEFINE FIELD OVERWRITE created_at ON {table} TYPE datetime;\n"
        f"DEFINE FIELD OVERWRITE owner_principal ON {table} TYPE option<record<principal>>;\n"
        f"DEFINE FIELD OVERWRITE owner_agent ON {table} TYPE option<record<{_AGENT_TABLE}>>;\n"
        f"DEFINE FIELD OVERWRITE scope ON {table} TYPE option<string>;\n"
    )


# --------------------------------------------------------------------------- #
# AGENT dirty-store DDL (63c-i-a §4.4) — the OLD-world captures the two agent dirty-store legs need,
# mirroring frozen_asserted_message_ddl / unbounded_message_ddl. Both are MINIMAL (the six birth
# columns the seeders write + the governed overlay) — SCHEMAFULL, so seeding writes exactly these,
# and applying the CURRENT emitter OVERWRITES them (adding the real emitter's option<> columns as
# NONE — un-poisoning, §1.4). The frozen one carries the four BIRTH ASSERTs the current emitter drops
# on name/session/role (KEEPS status); the unbounded one carries NONE (it exists to ACCEPT violators).
# --------------------------------------------------------------------------- #

# The four birth ASSERTs at HEAD (surreal_schema _IDENTIFIER_CHARSET_ASSERT / _NON_EMPTY_STRING_ASSERT
# / _AGENT_STATUS_ALLOWED), HAND-CAPTURED verbatim — the whole point is that this OLD world SURVIVES
# the emitter DROPPING the name/session/role asserts (an emitter-derived old world would drop them too,
# so it could never be the C-control). Kept as literals here, NOT imported from the emitter.
_AGENT_NAME_CHARSET_ASSERT = "ASSERT string::matches($value, '^[a-z0-9][a-z0-9_-]{0,63}$')"
_AGENT_ROLE_NONEMPTY_ASSERT = "ASSERT string::len(string::trim($value)) > 0"
_AGENT_STATUS_DOMAIN_ASSERT = "ASSERT $value IN ['active', 'idle', 'input_required', 'retired']"


def frozen_asserted_agent_ddl() -> str:
    """A FROZEN capture of ``agent``'s ASSERT-bearing birth DDL at ``699a6e9`` — the four birth ASSERTs
    verbatim (``name``/``session`` charset, ``role`` non-empty, ``status`` domain) + the two datetimes +
    the governed overlay. The OLD asserted world Leg A's BASELINE proves rejects the violators, and Leg
    B's C-CONTROL proves the REAL migrate RAISES against (63c-i-a §4.4). HAND-CAPTURED, NOT re-derived
    from the emitter (an emitter-derived old world would drop the asserts the ii build removes, so it
    could never be the control). A ``test_the_frozen_old_world_is_a_faithful_asserted_capture`` control
    pins this constant still carries the four birth ASSERT literals (self-consistency — NEVER a compare
    to the live emitter, which this wave is designed to change).

    ⚠ KNOWN BOUND (63c-i-a r2 / adversary R1, amendment-2 §D item 12): this capture — and
    :func:`unbounded_agent_ddl` — model only 6 of the ~16 ``agent`` columns (the four ASSERTed birth
    columns + the two datetimes) plus the governed overlay. The dirty-store legs built on them are
    therefore BLIND to a TYPE change on any of the other columns (``model``, ``spawned_by``,
    ``task_id``, ``checkpoint``, ``last_note``, the capability columns, …). That is outside 63c-i-a's
    change set (it drops ASSERTs; it retypes nothing). RE-OPEN TRIGGER: *any change to the type of an
    existing ``agent`` column* — that wave extends both captures with the retyped column."""
    table = AGENT_TABLE
    return (
        f"DEFINE TABLE IF NOT EXISTS {table} SCHEMAFULL;\n"
        f"DEFINE FIELD OVERWRITE name ON {table} TYPE string {_AGENT_NAME_CHARSET_ASSERT};\n"
        f"DEFINE FIELD OVERWRITE session ON {table} TYPE string {_AGENT_NAME_CHARSET_ASSERT};\n"
        f"DEFINE FIELD OVERWRITE role ON {table} TYPE string {_AGENT_ROLE_NONEMPTY_ASSERT};\n"
        f"DEFINE FIELD OVERWRITE status ON {table} TYPE string {_AGENT_STATUS_DOMAIN_ASSERT};\n"
        f"DEFINE FIELD OVERWRITE registered_at ON {table} TYPE datetime;\n"
        f"DEFINE FIELD OVERWRITE heartbeat_at ON {table} TYPE datetime;\n"
    ) + governed_overlay_ddl(table)


def unbounded_agent_ddl() -> str:
    """The ``agent`` birth columns with NO ASSERT on any field + the governed overlay — a world that
    NEVER shipped (it exists to ACCEPT the violators Leg B migrates). ``status`` too carries no ASSERT
    here so the junk-status P-A3 row can be SEEDED (its refusal is proven when the CURRENT emitter —
    which KEEPS the status ASSERT — is applied over it). Leg B seeds its legacy violators under THIS,
    then migrates the SCHEMA with the current emitter (§4.4 Leg B)."""
    table = AGENT_TABLE
    return (
        f"DEFINE TABLE IF NOT EXISTS {table} SCHEMAFULL;\n"
        f"DEFINE FIELD OVERWRITE name ON {table} TYPE string;\n"
        f"DEFINE FIELD OVERWRITE session ON {table} TYPE string;\n"
        f"DEFINE FIELD OVERWRITE role ON {table} TYPE string;\n"
        f"DEFINE FIELD OVERWRITE status ON {table} TYPE string;\n"
        f"DEFINE FIELD OVERWRITE registered_at ON {table} TYPE datetime;\n"
        f"DEFINE FIELD OVERWRITE heartbeat_at ON {table} TYPE datetime;\n"
    ) + governed_overlay_ddl(table)


def agent_case() -> GovernedTableCase:
    """The ``agent`` :class:`GovernedTableCase` (design §3.2 parametrisation) — lazily built so the
    shared substrate does not import the production schema emitter at module load. ``make_ddl`` is the
    REAL emitter (``generate_agent_ddl``); the seeders are the F5 home's agent writers. ``read_verbs``/
    ``write_verbs`` are left empty here — the agent READ-verb (F3) / WRITE-verb (F4) families are
    63c-i-b's (serving/security), not this data-layer wave's."""
    from loremaster.store.surreal_schema import generate_agent_ddl

    return GovernedTableCase(
        table=AGENT_TABLE,
        make_ddl=generate_agent_ddl,
        seed_legacy=seed_agent_legacy,
        seed_governed=seed_agent_governed,
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


# --------------------------------------------------------------------------- #
# The ONE shared CREDENTIALED-AppContext harness (ii-a §11.3 F-DUP) — the wire_world / cred idiom
# lifted here so every governed test agrees on the token-switching seam's SHAPE, instead of 4 private
# copies (wire_world + the 3 ii-a cred fixtures). ADD-only: the F5 substrate above is UNTOUCHED.
# --------------------------------------------------------------------------- #


def _credentialed_config(slug: str, *, dim: int) -> Any:
    """A minimal valid :class:`~loremaster.config.LoreConfig` pointed at the spike TEST store
    (``ws://127.0.0.1:18000``, NEVER :18500) — the ``cred`` / ``wire_world`` local-config idiom,
    lifted. The surreal user/pass are read from ``SURREAL_USER``/``SURREAL_PASS`` (set by
    :func:`credentialed_app_context`)."""
    from loremaster.config import LoreConfig

    return LoreConfig.model_validate(
        {
            "schema_version": 1,
            "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
            "project": {"slug": slug, "root": "."},
            "embedding": {
                "backend": "tei", "base_url": "http://localhost:8080", "endpoint": "/embed",
                "model": "voyageai/voyage-4-nano", "dim": dim, "truncate": False,
                "max_input_tokens": 8192, "max_batch_texts": 32, "concurrency": 2,
                "connect_timeout_s": 5, "api_key_env": "LORE_TEI_KEY", "tokenizer": "voyage-4-nano",
            },
            "surreal": {
                "url": _surreal_test_url(), "namespace": "lore_test",
                "user_env": "SURREAL_USER", "password_env": "SURREAL_PASS",
            },
            "roots": [], "include": [], "exclude_dirs": [".git"], "exclude_globs": [],
            "chunkers": {".py": {"chunker": "python_ast"}},
            "watcher": {"enabled": False, "observer": "inotify", "debounce_ms": 1500,
                        "reconcile_interval_s": 600},
            "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9235},
        }
    )


def _surreal_test_url() -> str:
    from _surreal_harness import surreal_url

    return str(surreal_url())


@contextlib.asynccontextmanager
async def credentialed_app_context(
    monkeypatch: Any, tmp_path: Path, *, principals: dict[str, str], dim: int = 8
) -> AsyncIterator[dict[str, Any]]:
    """ONE shared credentialed-AppContext harness (ii-a §11.3 F-DUP): a REAL booted
    :class:`~loremaster.server.AppContext` with a SWITCHABLE ambient transport token + ``principals``
    provisioned. ``principals`` maps ``name -> role`` (emails ``<name>@example.com``); set
    ``holder['email']`` to a provisioned email to ACT AS that principal, or ``None`` for an
    empty-subject token (identity-less → ``GovernedDenied``). Yields
    ``{ctx, holder, pids, emails, admin_conn, env}`` — ``pids``/``emails`` map name→bare principal id /
    email, ``admin_conn`` is a signed-in ADMIN connection on the SAME db (for raw seeding), ``env`` the
    ``SurrealEnv``. Reaped on exit (NEVER :18500).

    SHARING is provable BY MUTATION (§11.3): change how ``holder`` feeds ``access_token`` (the token
    shape) and EVERY caller's resolved identity flips — pinned by the F-DUP mutation test. This lift
    is the shared HOME; ``wire_world`` + the 3 ii-a ``cred`` fixtures are the private copies the BUILD
    wave converges onto it (report §F-DUP: not churned in the RED contract before the adversary)."""
    import loremaster.server as server_mod
    from _surreal_harness import (
        connect_admin,
        drop_database,
        make_env,
        surreal_password,
        surreal_user,
        unique_database,
    )
    from loremaster.server import LoreServer, build_app_context
    from loresigil.testing import FakeEmbedder

    monkeypatch.setenv("SURREAL_USER", surreal_user())
    monkeypatch.setenv("SURREAL_PASS", surreal_password().get_secret_value())
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-credentialed-harness-dummy")
    monkeypatch.setenv("LORE_TEI_KEY", "credentialed-harness-dummy")

    holder: dict[str, str | None] = {"email": None}

    def _patched_get_access_token() -> Any:
        email = holder["email"]
        return access_token(subject=email if email is not None else "")

    monkeypatch.setattr(server_mod, "get_access_token", _patched_get_access_token)

    slug = unique_database()
    context = await build_app_context(
        server=LoreServer(_credentialed_config(slug, dim=dim)),
        embedder=FakeEmbedder(dim=dim),
        manifest_path=tmp_path / f"{slug}-m.db",
        snapshot_root=tmp_path / f"{slug}-snap",
        start_tasks=False,
    )
    env = make_env(database=slug, dim=dim)
    admin_conn = await connect_admin(env)
    principal_store = context._principal_store  # noqa: SLF001 - provision the credentialed principals
    assert principal_store is not None, (
        "the composition root did not wire the principal store — the credentialed harness needs a real "
        "AppContext with a principal store"
    )
    pids: dict[str, str] = {}
    emails: dict[str, str] = {}
    for name, role in principals.items():
        email = f"{name}@example.com"
        principal = await principal_store.create(email=email, role=role)
        pids[name] = _bare(principal.id)
        emails[name] = email
    try:
        yield {
            "ctx": context,
            "holder": holder,
            "pids": pids,
            "emails": emails,
            "admin_conn": admin_conn,
            "env": env,
        }
    finally:
        await admin_conn.close()
        await context.aclose()
        await drop_database(env)


#: Value types whose instances CPython may intern or share by value — an identity sweep over one of
#: these would rebind every unrelated binding that happens to hold the same small int / string. The
#: instrument refuses them LOUDLY rather than clobbering the interpreter (a probe needs a control).
_IDENTITY_SWEEP_REFUSED_TYPES: tuple[type, ...] = (str, bytes, int, float, bool, type(None), tuple)


def patch_shared_object_everywhere(
    patcher: Any,
    attribute: str,
    original: object,
    replacement: object,
    *,
    expect_in: Sequence[str] = ("lorerunes",),
) -> list[str]:
    """DUAL (r3, amendment-4 MP-G): the r2 body keyed on NAME ∧ identity and returned bare module names;
    re-keyed to IDENTITY ALONE with a caller EXPECTATION. The r2 virtue ("an unrelated same-named
    attribute is never clobbered") is PRESERVED — identity alone still never touches a different object.

    Rebind EVERY module-level binding of THE shared object ``original`` — whatever NAME it is bound
    under — to ``replacement``, and return the patched bindings as ``"<module>.<name>"``. The mutation
    instrument for "prove sharing by MUTATION" (CLAUDE.md ONE IMPLEMENTATION).

    **Keyed on IDENTITY ALONE** (amendment-4 MP-G, 63c-i-a r3): ``for name, value in vars(module):
    if value is original``. The r2 version keyed on NAME ∧ identity (``getattr(module, attribute) is
    original``), so a CORRECT build binding the shared object under an alias (``from lorerunes import
    keep_scope as _format_keep_scope`` — ordinary hygiene) was never patched and its pin went RED
    with a message accusing a private copy: a false RED with a lying message (adversary-r2 MP-G,
    measured). The name-keyed ``_patch_everywhere`` copies had the mirror-image FALSE CLEAR: they
    rebind a caller's PRIVATE same-named copy too, so a build that shares nothing passes. Identity
    alone closes both: an aliased binding of THE object moves; a private copy (a DIFFERENT object) is
    never patched, whatever it is named — including a copy wearing the shared NAME.

    ``attribute`` is the caller's EXPECTATION, not the key: the name under which THE object must be
    found in every module named by ``expect_in`` (default: its ``lorerunes`` home). If an expected
    ``"<module>.<attribute>"`` binding was not patched, the sweep RAISES ``AssertionError`` — the probe
    could not land where the caller said the object lives, so any "did not move" verdict after it
    would be about a mutation that never happened (#194). Pass ``expect_in=()`` only for an object
    with no fixed home (a pin that asserts on the returned list itself).

    ⚠ KNOWN BOUND — MODULE-LEVEL bindings only. A class attribute, a container member (a dict of
    handlers, a list of predicates), a default argument or a closure cell that holds THE object is
    NOT rebound, so a build that holds the shared object only there reads as "did not move". That is
    why every calling pin's failure text says *either a private copy, or a binding the sweep cannot
    reach* (:func:`identity_sweep_miss_message`) — never a bare accusation. RE-OPEN TRIGGER: a
    CORRECT build that holds the shared object in a non-module binding → the PIN gets a ruling; this
    helper is NEVER widened by guessing (widening back to NAMES re-opens the false clear above).

    The bindings come from ``_logging_fixtures.module_level_bindings_of`` — the ONE by-identity
    finder, shared with ``_rebind_everywhere`` (so a change to the reach moves both instruments).

    Refuses (``TypeError``) an ``original`` of an interned/value type (``str``/``int``/``tuple`` …):
    identity over those is not a statement about sharing and would rebind unrelated bindings.
    Self-tests: ``test_agent_governance_63c_i_a.py::TestThePatchSharedObjectInstrument63cIA``."""
    if isinstance(original, _IDENTITY_SWEEP_REFUSED_TYPES):
        raise TypeError(
            f"patch_shared_object_everywhere sweeps by IDENTITY; a {type(original).__name__} may be "
            f"interned/shared by value, so identity over it proves nothing about sharing"
        )
    patched: list[str] = []
    # THE ONE binding-finder (shared with ``_logging_fixtures._rebind_everywhere`` — never a second
    # copy of the sys.modules/vars/``is`` loop; 63c-i-a r3 DRY row).
    for module_name, module, binding_name in module_level_bindings_of(original):
        patcher.setattr(module, binding_name, replacement, raising=True)
        patched.append(f"{module_name}.{binding_name}")
    missing = [
        f"{module_name}.{attribute}"
        for module_name in expect_in
        if f"{module_name}.{attribute}" not in patched
    ]
    if missing:
        raise AssertionError(
            f"the identity sweep did not find THE shared object at its expected home(s) {missing} — "
            f"the mutation could not land where the caller said it lives, so no verdict about "
            f"'moving' is possible; patched: {patched}"
        )
    return patched


def identity_sweep_miss_message(what_did_not_move: str, patched: Sequence[str]) -> str:
    """The ONE honest failure text for a pin whose behaviour did not move under
    :func:`patch_shared_object_everywhere` (amendment-4 MP-G rider 2). It names BOTH causes the
    instrument cannot tell apart — a PRIVATE copy, or a binding the MODULE-LEVEL sweep cannot reach —
    and lists what WAS patched, so a reader can see whether the consumer's module was among them. ONE
    function, so the stated bound cannot drift between the pins that quote it."""
    return (
        f"{what_did_not_move}: behaviour did not move under the MODULE-LEVEL identity sweep — either "
        f"a private copy, or a binding the sweep cannot reach (class attribute / container / "
        f"call-time alias); patched: {list(patched)}"
    )


def registry_level_session_keep_id(session: str) -> str:
    """A SYNTHETIC bare session-keep id for a REGISTRY-LEVEL fixture that has no keep store (the
    capability / stamp-owner harnesses build a bare ``AgentRegistry`` + ``PrincipalStore`` only).

    63c-i-a r2 (amendment-2 A3): ``register`` refuses an owner without a session keep, and the registry
    treats ``session_keep_id`` as an OPAQUE server-derived bare id (it formats ``keep_scope(id)``; it
    never reads the keep). So a fixture that exercises the capability/owner seams — never scope — may
    hand it this deterministic stand-in. A fixture that HAS a keep store must use
    :func:`session_keep_id_for` (the real keep production mints) instead."""
    return f"registrylevel_{session}"


async def session_keep_id_for(
    keep_store: Any, principal_store: Any, *, owner_principal_id: str, session: str
) -> str:
    """The bare id of the ``session:<session>`` keep KEPT BY ``owner_principal_id`` — minted (or
    joined) exactly as ``AppContext._comms_register`` mints it (``get_or_create_keyed(key=
    f"session:{session}", type="session", keeper_email=<owner email>, name=session)``).

    63c-i-a r2 (amendment-2 A2 + A3): ``AgentRegistry.register`` takes the server-derived provenance
    PAIR ``(owner_principal_id, session_keep_id)`` and REFUSES a half pair, so every fixture that
    registers an OWNED agent directly on the registry must also hand it THE session keep — the one
    production would have minted. ONE seam for every such fixture (never a per-file keep mint), so a
    change to how production mints the session keep is one edit here."""
    principals_list = await principal_store.list()
    owner = next(
        (principal for principal in principals_list if _bare(principal.id) == owner_principal_id),
        None,
    )
    assert owner is not None, f"no principal {owner_principal_id!r} to keep session {session!r}"
    keep = await keep_store.get_or_create_keyed(
        key=f"session:{session}", type="session", keeper_email=owner.email, name=session
    )
    return _bare(keep.id)


async def register_owned(
    ctx: Any, name: str, *, owner_principal_id: str, session: str, role: str = "builder"
) -> tuple[str, str]:
    """Register an agent OWNED by ``owner_principal_id`` DIRECTLY on the registry (the wire_world /
    ii-a ``_register_owned`` idiom), returning its one-time ``(capability, bare agent id)``. Until R7
    the tool ``register`` renders but does not RETURN the raw credential, so a credentialed call mints
    its capability here. Lifted (F-DUP §11.3) so the ii-a ``cred`` files + the ii-b tests share ONE
    minting seam.

    63c-i-a r2 (amendment-2 A3): the registry refuses an owner without a session keep, so this seam
    also hands it THE session keep (:func:`session_keep_id_for`) — the consistent pair production's
    ``_comms_register`` passes."""
    session_keep_id = await session_keep_id_for(
        ctx._keep_store,  # noqa: SLF001 - the wired AppContext's own keep store
        ctx._principal_store,  # noqa: SLF001 - the wired AppContext's own principal store
        owner_principal_id=owner_principal_id,
        session=session,
    )
    result = await ctx.agent_registry.register(
        name,
        session=session,
        role=role,
        owner_principal_id=owner_principal_id,
        session_keep_id=session_keep_id,
    )
    assert result.capability is not None, f"the first register of {name!r} must mint a capability"
    return str(result.capability), _bare(result.agent.id)


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
# every gate — the instrument lesson). REUSABLE, parametrised per governed table: the WHOLE-TREE
# deny-by-default allowlist (``TreeWriteAllowlistEntry`` / e.g. ``MEMORY_TREE_ALLOWLIST``, scanned by
# ``governed_table_raw_mutation_sites_in_tree``) is the shape 63b (message) / 64 (task/finding) reuse
# — NEVER a cloned module (design §3.2 RIDER).
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

# =========================================================================== #
# 63b-i-a (design §1.5a) — L1's verb list is INVERTED to a DERIVED grammar. The static scan's job
# is DEMOTED to a coverage floor (L2 detects by effect); its keyword set is no longer a hand list
# but the vendor's statement index, so a keyword the engine gains cannot silently escape L1's reach.
# ★CONTRACT SHAPES★ the 63b-i-a builder fills; RED-until-built so the currency + grammar pins fire.
# =========================================================================== #

#: The committed keyword constant the derived grammar keys on (design §1.5a). DERIVED + COMMITTED
#: 2026-09-03 (63b-i-a) from the ``surrealdb-docs`` 3.2 corpus by
#: :func:`derive_surrealql_statement_keywords_from_corpus` — the uppercased top-level statement page
#: stems + sub-statement DIRECTORIES (``define`` / ``alter``), first hyphen-segment, the ``overview``
#: navigation page excluded. The currency pin (``SURREALQL_STATEMENT_KEYWORDS == derive_…()``) reds
#: on drift, so this constant is REGENERATED from the corpus, never hand-edited: a keyword the vendor
#: adds → the derivation grows → RED "classify its operand position"; a keyword deleted → RED.
SURREALQL_STATEMENT_KEYWORDS: frozenset[str] = frozenset(
    {
        "ACCESS",
        "ALTER",
        "BEGIN",
        "BREAK",
        "CANCEL",
        "COMMIT",
        "CONTINUE",
        "CREATE",
        "DEFINE",
        "DELETE",
        "EXPLAIN",
        "FOR",
        "IF",
        "INFO",
        "INSERT",
        "KILL",
        "LET",
        "LIVE",
        "REBUILD",
        "RELATE",
        "REMOVE",
        "RETURN",
        "SELECT",
        "SHOW",
        "SLEEP",
        "THROW",
        "UPDATE",
        "UPSERT",
        "USE",
    }
)

#: The MUTATION keywords whose operand position the grammar MUST classify (a subset of the constant
#: above — the write/DDL verbs). A keyword here with no operand rule in ``_raw_mutation_of_table``
#: REDS "classify its operand position" (design §1.5a / §1.6-viii). The READ safe set (SELECT / INFO
#: / SHOW / LIVE) is the complement — never a mutation.
SURREALQL_MUTATION_KEYWORDS: frozenset[str] = frozenset(
    {"UPDATE", "UPSERT", "DELETE", "CREATE", "INSERT", "RELATE", "REMOVE", "DEFINE", "ALTER", "REBUILD"}
)
SURREALQL_READ_KEYWORDS: frozenset[str] = frozenset({"SELECT", "INFO", "SHOW", "LIVE"})

#: The ``lore.yaml`` tier whose ``source`` roots the SurrealQL statement corpus (design §1.5a — the
#: currency derivation is keyed on the CONFIG-named root, never a hardcoded path).
_SURREALDB_DOCS_TIER = "surrealdb-docs"


def derive_surrealql_statement_keywords_from_corpus(
    repo_root: Path | None = None,
) -> frozenset[str]:
    """DERIVE the SurrealQL statement keyword set from the ``surrealdb-docs`` corpus (design §1.5a).

    ★BUILDER DELIVERABLE★ (RED-until-built): read the ``surrealdb-docs`` tier ``source`` named in
    ``lore.yaml`` → its ``reference/query-language/statements/*.mdx`` PAGE STEMS → the uppercased
    keyword set (``update.mdx`` → ``UPDATE``; ``live-select.mdx`` → ``LIVE``; ``if-else.mdx`` →
    ``IF`` — the builder pins the normalisation). Keyed on the CONFIG-named root, never a hardcoded
    path. Where the corpus is UNREADABLE (the in-image conformance profile, packet 01a) this RAISES
    and the currency pin is ``RED_ADJUDICATED`` with that trigger (design §1.5a) — NEVER skipped.

    ⚠ Where the corpus is UNREADABLE (the in-image conformance profile, packet 01a — no
    ``lore.yaml`` tier source on disk) this RAISES a ``FileNotFoundError`` (NOT ``NotImplementedError``
    — the derivation IS built), so the currency pin is ``RED_ADJUDICATED`` with that trigger rather
    than skipped or vacuously green. On the dev host the corpus IS readable and this returns the set."""
    root = repo_root if repo_root is not None else _REPO_ROOT
    config = yaml.safe_load((root / "lore.yaml").read_text(encoding="utf-8"))
    source: Path | None = None
    for tier in config.get("roots", []):
        if isinstance(tier, dict) and tier.get("tier") == _SURREALDB_DOCS_TIER:
            source = Path(str(tier["source"]))
            break
    if source is None:
        raise FileNotFoundError(
            f"no {_SURREALDB_DOCS_TIER!r} tier declared in {root / 'lore.yaml'} — the SurrealQL "
            "statement-keyword grammar cannot derive its keyword set from the vendor corpus"
        )
    statements_dir = source / "reference" / "query-language" / "statements"
    if not statements_dir.is_dir():
        raise FileNotFoundError(
            f"the surrealdb-docs statement corpus is unreadable at {statements_dir} (the in-image "
            "conformance profile, packet 01a) — the keyword-currency pin is RED_ADJUDICATED with "
            "that trigger, never skipped (design §1.5a)"
        )
    keywords: set[str] = set()
    for entry in statements_dir.iterdir():
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            # A sub-statement DIRECTORY (``define/`` / ``alter/`` — each holds DEFINE FIELD, DEFINE
            # TABLE, … pages): the directory name IS the statement keyword.
            stem = entry.name
        elif entry.suffix == ".mdx":
            stem = entry.stem
        else:
            continue
        # Normalisation (pinned, design §1.5a): the FIRST hyphen-segment, uppercased —
        # ``update`` → UPDATE, ``live-select`` → LIVE, ``if-else`` → IF. The ``overview`` navigation
        # index page (present at every level of the docs tree) is NOT a statement keyword.
        keyword = stem.split("-", 1)[0].upper()
        if keyword == "OVERVIEW":
            continue
        keywords.add(keyword)
    return frozenset(keywords)


@dataclass(frozen=True, order=True)
class MutationSite:
    """A raw governed-table mutation, keyed by its enclosing function + the SurrealQL verb (design
    §10.9-A L1). The unit the allowlist classifies and the AST scan derives. ``order=True`` so a
    diagnostic ``sorted(derived - allowlist)`` renders deterministically."""

    function: str
    verb: str  # one of _MUTATION_VERBS (upper-cased)


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
    prose mentions carry no structural anchors, so anchor on the verb→target adjacency).

    63b-i-a (design §1.5a/§1.5b): the verb list is INVERTED to a DERIVED grammar keyed on
    :data:`SURREALQL_STATEMENT_KEYWORDS` (the vendor statement index), keeping the verb→operand
    ADJACENCY. The R4-c exotic verbs (``CREATE`` / ``INSERT`` / ``RELATE``) and the DDL verbs
    (``DEFINE`` / ``ALTER`` / ``REBUILD`` / ``REMOVE``) now DERIVE here, so a keyword the engine gains
    cannot silently escape L1's reach; L2's effect leg covers whatever the static grammar cannot see
    (a dynamically-named write, a concatenation-assembled verb — the #444 static bound STANDS at L1).
    The R4-a/R4-c ACCEPTED-BOUND pins are DELETED (their own instruction) — the statement-scoped exempt
    (§1.4) and the effect model close R4-a/R4-c at L2.

    The operand grammar (design §1.5a — the target must BE the verb's operand, never merely mentioned):
    ``UPDATE|UPSERT|DELETE|CREATE <t>`` · ``INSERT [IGNORE|RELATION] INTO <t>`` · ``RELATE …->…<t>…`` ·
    ``REMOVE TABLE <t>`` / ``REMOVE FIELD|INDEX|EVENT … ON [TABLE] <t>`` · ``DEFINE TABLE <t>`` /
    ``DEFINE FIELD|INDEX|EVENT … ON [TABLE] <t>`` · ``ALTER TABLE <t>`` · ``REBUILD INDEX … ON [TABLE]
    <t>``. ``<t>`` is the literal table name or its interpolated module constant ``{table_const_hint}``
    — the schema emitter's ``DEFINE … {table}``/``{name}`` param interpolations match NEITHER anchor
    (the #444 dynamic-name bound), so the widened grammar derives the SAME governed sites, not the
    emitter's own DDL literals (design §5.1 Q2 leg i)."""
    target = (
        rf"(?:type::record\(\s*['\"]?)?"
        rf"(?:{re.escape(table)}\b|\{{{re.escape(table_const_hint)}\}})"
    )
    # verb → operand-position pattern (ORDER-independent — each keys on one keyword's own operand
    # syntax). ``[^;]*?`` keeps a match WITHIN one statement (the reconstructed shapes carry no
    # embedded ``;``). READ keywords (SELECT/INFO/SHOW/LIVE) have no rule → the safe set, never a site.
    grammar: tuple[tuple[str, str], ...] = (
        ("UPDATE", rf"\bUPDATE\s+{target}"),
        ("UPSERT", rf"\bUPSERT\s+{target}"),
        ("DELETE", rf"\bDELETE\s+{target}"),
        ("CREATE", rf"\bCREATE\s+{target}"),
        ("INSERT", rf"\bINSERT\s+(?:IGNORE\s+|RELATION\s+)?INTO\s+{target}"),
        ("RELATE", rf"\bRELATE\b[^;]*?->[^;]*?{target}"),
        ("REMOVE", rf"\bREMOVE\s+TABLE\b\s+(?:IF\s+EXISTS\s+)?{target}"),
        ("REMOVE", rf"\bREMOVE\s+(?:FIELD|INDEX|EVENT|ANALYZER)\b[^;]*?\bON\s+(?:TABLE\s+)?{target}"),
        ("DEFINE", rf"\bDEFINE\s+TABLE\b\s+(?:OVERWRITE\s+|IF\s+NOT\s+EXISTS\s+)?{target}"),
        ("DEFINE", rf"\bDEFINE\s+(?:FIELD|INDEX|EVENT|ANALYZER)\b[^;]*?\bON\s+(?:TABLE\s+)?{target}"),
        ("ALTER", rf"\bALTER\s+TABLE\b\s+(?:IF\s+EXISTS\s+)?{target}"),
        ("REBUILD", rf"\bREBUILD\s+INDEX\b[^;]*?\bON\s+(?:TABLE\s+)?{target}"),
    )
    for verb, pattern in grammar:
        if re.search(pattern, shape, re.IGNORECASE):
            return verb
    return None


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


# =========================================================================== #
# 63b-i-a — THE EFFECT (design §1.2): detection is a before/after STATE DIFF of a governed
# population per SDK call, NEVER a statement classification. These are the ★CONTRACT SHAPES★ the
# 63b-i-a BUILDER fills (the observer BODY that produces them + the classifier that reads them);
# authored here as stubs so the RED contract COLLECTS (the 63a ``governed.py``-stub precedent). A
# RowDelta/SchemaDelta/ObservedEffect are pure DATA containers (no body to build); the builder-owned
# LOGIC is the observer that constructs them from ``SELECT *`` + ``INFO FOR TABLE`` diffs.
# =========================================================================== #


@dataclass(frozen=True)
class ExemptToken:
    """The token an active ``governed.governed_exempt(name, *, statement)`` block installs in
    ``_ACTIVE_EXEMPT`` (design §1.9 item 3c — SUPERSEDES the §1.4 ``(name, statement)`` tuple).
    ``active_exempt()`` returns THIS or ``None``. Frozen: the channel ``name`` + the GOLDEN
    ``statement`` + the ``origin`` ``(repo-relative file, co_name)`` of the frame that ENTERED the
    ``with`` block — captured by ``__enter__`` walking ``sys._getframe(1)`` (exactly one up, with NO
    ``contextlib`` frame between, so there is NO filename skip-list — the relocated-constant
    antipattern item 3c removes). WHY origin lives in the TOKEN, not in the observer's call-time walk
    (adversary GOTCHA-C, measured): at SDK-call time the immediate production caller is ALWAYS the
    ``store._txn`` driver, so leg-4's origin cannot come from the call-time stack; it must be captured
    where the business frame IS the immediate caller — context entry. The classifier's leg 4 matches
    ``token.origin == (entry.site.file, entry.site.function)``; a helper borrowing the token on
    another frame's behalf yields a foreign origin → leg 4 RED. ``write_guard`` NEVER consults origin
    (the label leg has none).

    ★CONTRACT SHAPE★ — the 63b-i-a builder builds a STRUCTURALLY IDENTICAL ``governed.ExemptToken``
    (the exempt-API value type, §1.9 item 5) that production ``active_exempt()`` returns; this
    test-side twin is what the pure-unit pins CONSTRUCT (production's type is unbuilt at HEAD). The
    classifier reads BOTH by attribute (``.name`` / ``.statement`` / ``.origin``), so the field names
    are the contract — the builder must match them."""

    name: str
    statement: str
    origin: tuple[str, str]  # (repo-relative file, co_name) of the frame that ENTERED the exempt block


@dataclass(frozen=True)
class SchemaSnapshot:
    """The engine's OWN rendering of a table's schema — the ``fields`` / ``indexes`` / ``events``
    maps ``INFO FOR TABLE`` reports, each ``name → the engine-rendered definition string``, taken
    VERBATIM (design §1.9 item 4). NO regex, no hand-model of the engine's implicit expansions: an
    array-element field renders however the engine renders it (``embedding[*]`` / ``embedding.*`` —
    the exact #107/#131 "the test environment is a fiction" class the retired DDL-text regex
    ``_memory_ddl_object_names`` fell to). Compared by DICT EQUALITY against the CONSTRUCTED
    ensure_ready oracle (the SAME emitter applied to a virgin DB, rendered the SAME way, §1.9 item 4)."""

    fields: dict[str, str]
    indexes: dict[str, str]
    events: dict[str, str]


def schema_snapshot_from_info(info: Any) -> SchemaSnapshot:
    """Normalise a raw ``INFO FOR TABLE`` result into a :class:`SchemaSnapshot`, tolerant of the two
    shapes its two readers hand it, so both render IDENTICALLY (design §1.9 item 4): the observer
    reads before/after schema via the UNWRAPPED ``query_raw`` (the ``[{"result": {…}, "status": …}]``
    envelope, §1.9 item 3a); the ensure_ready-oracle fixture reads via ``.query()`` (the bare
    ``{fields, indexes, events, …}`` dict, possibly single-element-list-wrapped). ONE normaliser is
    what makes ``after.schema == oracle.schema`` a FAIR, engine-rendered compare rather than a
    parse-vs-parse race. The per-object definition strings are taken VERBATIM — no parse, no regex."""
    node: Any = info
    # query_raw rpc envelope: {'id':.., 'result': [{'result': <map>, 'status': ..}]} (SDK 2.0.0).
    if isinstance(node, dict) and isinstance(node.get("result"), list):
        node = node["result"]
    if isinstance(node, list):
        node = node[0] if node else {}
    if isinstance(node, dict) and isinstance(node.get("result"), dict):
        node = node["result"]  # a wrapped statement result → the info map
    if not isinstance(node, dict):
        node = {}

    def _as_str_map(value: Any) -> dict[str, str]:
        return {str(k): str(v) for k, v in value.items()} if isinstance(value, dict) else {}

    return SchemaSnapshot(
        fields=_as_str_map(node.get("fields")),
        indexes=_as_str_map(node.get("indexes")),
        events=_as_str_map(node.get("events")),
    )


@dataclass(frozen=True)
class RowDelta:
    """One row's change across a SINGLE observed SDK call (design §1.2 — the effect, not the
    statement). ``kind`` ∈ {created, updated, deleted}; ``changed_columns`` the columns whose value
    differs (the full non-id column set for a create/delete, the diff for an update); ``before`` /
    ``after`` the row dicts (``before`` None for a create, ``after`` None for a delete). ``id`` is
    the bare row id. This is what an allowlist entry's effect predicate adjudicates PER changed row
    (design §1.4 leg 3: ``entry.effect`` holds ∀ changed row)."""

    id: str
    kind: str  # "created" | "updated" | "deleted"
    changed_columns: frozenset[str]
    before: dict[str, Any] | None
    after: dict[str, Any] | None


@dataclass(frozen=True)
class SchemaDelta:
    """The ``INFO FOR TABLE`` delta across ONE observed SDK call (design §1.2 DDL leg): the field /
    index / event names ADDED, REMOVED, or CHANGED. ``is_empty`` ⟺ the call made no DDL mutation of
    the table — a non-empty delta IS a DDL mutation (``REMOVE TABLE`` / ``DEFINE FIELD OVERWRITE``
    with a change / ``REMOVE INDEX`` …). store-ref §1 (INFO FOR TABLE) is the source; the builder
    fills the observer that computes it from before/after INFO snapshots."""

    added: frozenset[str]
    removed: frozenset[str]
    changed: frozenset[str]

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)


@dataclass(frozen=True)
class ObservedEffect:
    """The FULL state diff of ONE registered governed population across ONE observed SDK call
    (design §1.2): the per-row deltas + the schema delta. A GOVERNANCE EVENT ⟺ NOT ``is_empty`` —
    a no-effect write (``SET scope = scope``) yields an empty ObservedEffect and is NOT a governance
    event (§1.2 self-attack row 1). The unit an allowlist entry's ``effect`` predicate adjudicates
    (design §1.4 — a ROW entry checks per-row deltas + empty schema; a DDL frame like ``ensure_ready``
    checks the schema delta == its golden AND no rows moved, §5.1 Q1)."""

    row_deltas: tuple[RowDelta, ...]
    schema_delta: SchemaDelta
    # 63b-i-a (design §1.9 item 4): the FULL engine-rendered schema AFTER the call — ``INFO FOR
    # TABLE`` read via the UNWRAPPED ``query_raw`` and normalised by :func:`schema_snapshot_from_info`.
    # The ``ensure_ready`` DDL-frame effect predicate compares THIS against the CONSTRUCTED oracle
    # (``generate_memory_ddl`` on a virgin DB) by DICT EQUALITY — the retired ``_memory_ddl_object_
    # names`` regex is gone. ``None`` ⟺ the observer captured no schema (a pure row write) OR HEAD
    # (the effect-based observer is unbuilt). ``is_empty`` is unaffected (it is the row+delta test).
    schema_after: SchemaSnapshot | None = None

    @property
    def is_empty(self) -> bool:
        return not self.row_deltas and self.schema_delta.is_empty


@dataclass(frozen=True)
class ObservedWrite:
    """One governed-population state change observed at the SDK-connection seam under test.

    63b-i-a WIDENS this (design §1.2 / §1.3): detection is the EFFECT, so an observed write carries
    its ``effect`` (the ObservedEffect state diff) — the classifier reads THAT, never the statement.
    ``statement`` is captured EVIDENCE ONLY (the failure message + the exempt golden match, §1.4);
    it is NEVER consulted for detection. ``exempt`` is the :class:`ExemptToken` that
    :func:`governed.active_exempt` returns under the statement-scoped exemption (design §1.9 item 3c:
    ``name`` + golden ``statement`` + the context-entry ``origin`` — SUPERSEDES the §1.4
    ``(name, statement)`` tuple; the LEG-4 origin now lives IN the token, not in a call-time walk).
    ``origin_site`` is the guard's own CALL-TIME attributed ``(repo-relative file, function)`` — for
    an exempt write that is the ``store._txn`` driver (GOTCHA-C), so it is EVIDENCE ONLY now; leg-4
    reads ``exempt.origin`` instead. ``verb`` / ``seam`` default to None (a pure-DDL call has no row
    verb) and are retained only as coarse evidence — the effect KIND lives in ``effect.row_deltas[].kind``.

    ★CONTRACT SHAPE★ — the 63b-i-a builder's rewritten observer constructs these from the guard
    hook (§1.8); at HEAD the fields default so the contract COLLECTS and the effect-based pins RED
    behaviorally (``effect`` is None / statement-derived, never a real state diff)."""

    label: str | None  # the active write_guard label, or None (an UNCLASSIFIED write — the red signal)
    verb: str | None = None  # coarse evidence only (the effect KIND lives in effect.row_deltas[].kind)
    seam: str | None = None  # coarse evidence only (retired as a classified field)
    # active governed_exempt token. §1.9 item 3c: the build carries an ExemptToken (name + golden
    # statement + context-entry origin) — what active_exempt() returns on the build. The union admits
    # the bare-name str the CURRENT (2-leg) active_exempt returns at HEAD, so the observer body stays
    # type-valid until the builder narrows active_exempt to ExemptToken — the absent_scope Any-bridge
    # idiom, one field over. The classifier reads ExemptToken by attribute (.name/.statement/.origin),
    # so production's structurally-identical governed.ExemptToken flows through unchanged.
    exempt: str | ExemptToken | None = None
    # call-time guard-attributed site — EVIDENCE ONLY now (leg 4 reads exempt.origin, §1.9 item 3c):
    origin_site: tuple[str, str] | None = None
    statement: str | None = None  # the executed SurrealQL — EVIDENCE ONLY, never classified on (§1.2)
    effect: ObservedEffect | None = None  # the observed state diff (§1.2 — the EFFECT the classifier reads)


# --------------------------------------------------------------------------- #
# THE EFFECT OBSERVER (design §1.2 / §1.3 / §1.8 / §1.9 item 3) — ONE persistent dispatcher on the
# ``_sdk_guard`` hook chain + a per-block registry. Detection is a before/after STATE DIFF of each
# registered governed population per ``query_raw`` call: verb-agnostic, shape-agnostic, table-generic.
# --------------------------------------------------------------------------- #

#: The active ``(table, sink)`` registrations the persistent dispatcher consults (design §1.9 item
#: 3b). ``observe_governed_table_writes`` appends/removes; the dispatcher is appended to
#: ``_sdk_guard._CALL_HOOKS`` ONCE at import (below) — NEVER per-observe (GOTCHA-B: a per-observe
#: append would re-arm behind the detach pin's ``_CALL_HOOKS.clear()`` and red it on a correct build).
_F5_REGISTRY: list[tuple[str, list[ObservedWrite]]] = []

#: ONE serialising lock PER EVENT LOOP (design §1.6-iv / §1.9 item 3d). Per-loop, NOT module-global:
#: pytest-asyncio mints a fresh function-scoped loop per test under ``-n auto`` and an ``asyncio.Lock``
#: reused across a finished loop raises. A ``WeakKeyDictionary`` lets a dead loop's lock be collected.
_F5_OBSERVER_LOCKS: WeakKeyDictionary[Any, asyncio.Lock] = WeakKeyDictionary()


def _f5_observer_lock() -> asyncio.Lock:
    """The serialising lock for the CURRENT running event loop — created lazily so it binds to the
    live loop. Held across before→await→after so a ``gather`` of two writes attributes each to its OWN
    per-call delta (§1.6-iv: without it, two interleaved calls SMEAR each other's deltas)."""
    loop = asyncio.get_running_loop()
    lock = _F5_OBSERVER_LOCKS.get(loop)
    if lock is None:
        lock = asyncio.Lock()
        _F5_OBSERVER_LOCKS[loop] = lock
    return lock


def _f5_unwrapped_query_raw(connection: Any) -> Any:
    """The UNWRAPPED ``query_raw`` door — ``type(conn).query_raw.__wrapped__`` (``_sdk_guard`` sets
    ``_guarded.__wrapped__ = original``, §1.9 item 3a). The observer's own ``SELECT *`` / ``INFO FOR
    TABLE`` reads go through THIS, so they never re-enter the guard, the hook chain, or the observer
    (no re-entry, no deadlock — §1.2 "the observer's own reads are excluded"). Falls back to the class
    door when the guard is not armed (no ``__wrapped__``). Returns ``Any`` — a bound method or the
    guard wrapper, both callable."""
    door: Any = type(connection).query_raw
    return getattr(door, "__wrapped__", door)


def _f5_unwrap_query_raw_rows(envelope: Any) -> list[dict[str, Any]]:
    """The row list out of a ``query_raw`` rpc envelope ``{'result': [{'result': <rows>}]}`` (SDK
    2.0.0) — the SAME digging :func:`schema_snapshot_from_info` does over ``INFO FOR TABLE``, so both
    readers normalise identically and the diff is a fair, engine-rendered compare (C-DEF #1)."""
    node: Any = envelope
    if isinstance(node, dict) and isinstance(node.get("result"), list):
        node = node["result"]
    if isinstance(node, list):
        node = node[0] if node else {}
    if isinstance(node, dict) and "result" in node:
        node = node["result"]
    return [row for row in node if isinstance(row, dict)] if isinstance(node, list) else []


async def _f5_read_state(
    connection: Any, table: str
) -> tuple[dict[str, dict[str, Any]], SchemaSnapshot]:
    """The governed population's full state — rows keyed by BARE id + the schema snapshot — read via
    the UNWRAPPED ``query_raw`` (never re-entering the guard or the observer, §1.2)."""
    query_raw = _f5_unwrapped_query_raw(connection)
    rows_envelope = await query_raw(connection, f"SELECT * FROM {table}")
    rows = {
        _bare(row["id"]): row for row in _f5_unwrap_query_raw_rows(rows_envelope) if "id" in row
    }
    info_envelope = await query_raw(connection, f"INFO FOR TABLE {table}")
    return rows, schema_snapshot_from_info(info_envelope)


def _f5_row_deltas(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> tuple[RowDelta, ...]:
    """The per-row diff across ONE observed call — created / updated / deleted by id. A row present in
    both with NO differing column yields NO delta (a no-op write is not a governance event, §1.2 self-
    attack row 1). ``SELECT *`` OMITS a NONE column (store-ref §2), so an absent key reads as None —
    a legacy row's NONE scope compares equal to Python ``None`` and unequal to a backfilled value, so
    the migrate diff yields ``changed_columns == {scope}``."""
    deltas: list[RowDelta] = []
    for row_id in sorted(set(before) | set(after)):
        before_row = before.get(row_id)
        after_row = after.get(row_id)
        if before_row is not None and after_row is None:
            columns = frozenset(key for key in before_row if key != "id")
            deltas.append(RowDelta(row_id, "deleted", columns, before_row, None))
        elif before_row is None and after_row is not None:
            columns = frozenset(key for key in after_row if key != "id")
            deltas.append(RowDelta(row_id, "created", columns, None, after_row))
        elif before_row is not None and after_row is not None:
            changed = frozenset(
                key
                for key in (set(before_row) | set(after_row)) - {"id"}
                if before_row.get(key) != after_row.get(key)
            )
            if changed:
                deltas.append(RowDelta(row_id, "updated", changed, before_row, after_row))
    return tuple(deltas)


def _f5_schema_delta(before: SchemaSnapshot, after: SchemaSnapshot) -> SchemaDelta:
    """The ``INFO FOR TABLE`` delta across one observed call — field / index / event names added,
    removed, or changed (prefixed by kind so a field and an index of the same name never collide)."""
    added: set[str] = set()
    removed: set[str] = set()
    changed: set[str] = set()
    for kind, before_map, after_map in (
        ("field", before.fields, after.fields),
        ("index", before.indexes, after.indexes),
        ("event", before.events, after.events),
    ):
        for name in set(after_map) - set(before_map):
            added.add(f"{kind}:{name}")
        for name in set(before_map) - set(after_map):
            removed.add(f"{kind}:{name}")
        for name in set(before_map) & set(after_map):
            if before_map[name] != after_map[name]:
                changed.add(f"{kind}:{name}")
    return SchemaDelta(frozenset(added), frozenset(removed), frozenset(changed))


def _f5_statement_of(args: tuple[Any, ...], kwargs: dict[str, Any]) -> str | None:
    """The ``query_raw`` statement text, EVIDENCE ONLY (never consulted for detection, §1.2). The SDK
    passes it positionally (``query_raw(query, params)``), as does the ``.query`` delegation."""
    candidate = args[0] if args else kwargs.get("query")
    return candidate if isinstance(candidate, str) else None


async def _f5_observed_call(
    event: _sdk_guard.CallEvent,
    coro: Any,
    registrations: list[tuple[str, list[ObservedWrite]]],
) -> Any:
    """Diff every registered governed population before/after ONE observed ``query_raw`` call, under
    ONE lock held across before→await→after (§1.6-iv). Records an :class:`ObservedWrite` per
    registration whose effect is NON-EMPTY — a read / no-op / rolled-back txn nets an empty effect and
    is NOT a governance event (§1.2 self-attack rows 1 & 4)."""
    import loremaster.governed as governed_mod

    connection = event.connection
    async with _f5_observer_lock():
        # label / exempt captured at CALL time in this task's contextvars (§1.8) — the issuing
        # ``with write_guard(...)`` / ``with governed_exempt(...)`` block is active across the await.
        # ``active_exempt`` returns production's ``governed.ExemptToken``, a class DISTINCT from this
        # substrate's structurally-identical twin — the classifier reads BOTH by attribute (duck-typed,
        # C-DEF #2). The getattr Any-bridge keeps the assignment type-valid across that class split.
        label = governed_mod.active_write_guard()
        read_exempt = getattr(governed_mod, "active_exempt", lambda: None)
        exempt = read_exempt()
        statement = _f5_statement_of(event.args, event.kwargs)
        before = {table: await _f5_read_state(connection, table) for table, _sink in registrations}
        result = await coro
        after = {table: await _f5_read_state(connection, table) for table, _sink in registrations}
        for table, sink in registrations:
            before_rows, before_schema = before[table]
            after_rows, after_schema = after[table]
            effect = ObservedEffect(
                row_deltas=_f5_row_deltas(before_rows, after_rows),
                schema_delta=_f5_schema_delta(before_schema, after_schema),
                schema_after=after_schema,
            )
            if effect.is_empty:
                continue  # a no-effect call is not a governance event (§1.2)
            sink.append(
                ObservedWrite(
                    label=label,
                    verb=effect.row_deltas[0].kind if effect.row_deltas else None,
                    seam=event.method,
                    origin_site=None,  # EVIDENCE ONLY, unused (leg 4 reads exempt.origin, §1.9 item 3c)
                    exempt=exempt,
                    statement=statement,
                    effect=effect,
                )
            )
    return result


def _f5_dispatcher(event: _sdk_guard.CallEvent, coro: Any) -> Any:
    """The ONE persistent hook (appended to ``_sdk_guard._CALL_HOOKS`` at import, §1.9 item 3b). Acts
    on ``query_raw`` ONLY — ``.query`` DELEGATES to ``.query_raw`` through the patched door, so a hook
    firing on ``.query`` re-enters and DEADLOCKS on the observer lock (#454 / GOTCHA-A). When no
    population is registered it returns the coroutine UNCHANGED (zero overhead on the suite's whole
    ``query_raw`` traffic)."""
    if event.method != "query_raw":
        return coro
    registrations = list(_F5_REGISTRY)
    if not registrations:
        return coro
    return _f5_observed_call(event, coro, registrations)


# Append the ONE persistent dispatcher to the guard's hook chain at IMPORT (design §1.9 item 3b) —
# idempotent against a module reload; NEVER per-observe (GOTCHA-B, above).
if _f5_dispatcher not in _sdk_guard._CALL_HOOKS:
    _sdk_guard._CALL_HOOKS.append(_f5_dispatcher)


@contextlib.contextmanager
def observe_governed_table_writes(table: str) -> Iterator[list[ObservedWrite]]:
    """Register ``table`` as a governed population the F5 EFFECT observer watches for the block, and
    yield the list of :class:`ObservedWrite`\\ s it records (design §1.2 / §1.3 / §1.8 / §1.9 item 3).
    Detection is a before/after STATE DIFF per SDK call — verb-, shape- and table-generic — NEVER a
    statement classification.

    THE BUILT MECHANISM (a per-block registry + ONE persistent dispatcher; the 63a-v seam-name-patching
    + ``extra_modules`` shape is RETIRED, design §1.3 / §1.7 — once the reach is the SDK ``query_raw``
    door, "does the patch-set cover this module?" is UNASKABLE):

    - **Registration, not hooking.** This CM only appends ``(table, sink)`` to the module registry
      :data:`_F5_REGISTRY` and removes it on exit. The hook itself, :func:`_f5_dispatcher`, is appended
      to ``_sdk_guard._CALL_HOOKS`` ONCE at import (§1.9 item 3b) — NEVER per-observe: a per-observe
      append would re-arm behind the detach pin's ``_CALL_HOOKS.clear()`` and RED it on a CORRECT build
      (GOTCHA-B). With no population registered the dispatcher returns the coroutine unchanged (zero
      overhead on the suite's ``query_raw`` traffic).
    - **``query_raw`` door ONLY** (§1.9 item 3a; #454). The dispatcher acts on ``query_raw`` and skips
      ``.query``, which DELEGATES to ``.query_raw`` through the patched door — a hook firing on
      ``.query`` would re-enter and DEADLOCK on the observer's held lock. ``query_raw`` is the narrow
      waist every SurrealQL statement passes through, and THE OBSERVER'S REACH ≡ THE ``query_raw`` DOOR
      is a CHECKED variable, not a hidden constant:
      ``test_the_UNCOUNTABLE_door_set_is_DERIVED_from_the_SDK_and_DENIES_BY_DEFAULT``
      (``test_query_tasks_bounded.py``) partitions the SDK doors, so a door the SDK adds that bypasses
      ``query_raw`` lands in UNCOUNTABLE and REDS that pin — the seventh defeat caught one instrument over.
    - **Reads via the UNWRAPPED door.** :func:`_f5_observed_call` diffs each registered population's
      ``SELECT *`` rows + ``INFO FOR TABLE`` schema across the call, reading through
      ``type(conn).query_raw.__wrapped__`` (:func:`_f5_unwrapped_query_raw`; the ``_sdk_guard`` extension
      sets ``_guarded.__wrapped__ = original``, §1.9 item 3a/5) — so the observer's own reads NEVER
      re-enter the guard, the hook chain, or the observer (§1.2 self-attack: the observer's reads are
      excluded). Schema is normalised through :func:`schema_snapshot_from_info` into
      ``ObservedEffect.schema_after``.
    - **One :class:`ObservedWrite` per NON-EMPTY effect.** The dispatcher captures ``label =
      governed.active_write_guard()`` and ``exempt = governed.active_exempt()`` (the :class:`ExemptToken`
      carrying the leg-4 origin, §1.9 item 3c) from the call's contextvars, records the ``statement`` as
      EVIDENCE ONLY (never classified on, §1.2), and builds ``effect`` = the :class:`ObservedEffect`
      before/after state diff. It holds ONE per-loop ``asyncio.Lock`` across before→await→after so a
      ``gather`` of two writes attributes each to its OWN per-call delta (§1.6-iv / §1.9 item 3d). A
      read / no-op (``SET scope = scope``) / rolled-back txn nets an EMPTY effect and is NOT recorded
      (§1.2 self-attack rows 1 & 4)."""
    sink: list[ObservedWrite] = []
    registration = (table, sink)
    _F5_REGISTRY.append(registration)
    try:
        yield sink
    finally:
        _F5_REGISTRY.remove(registration)


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
    """One WHOLE-TREE deny-by-default allowlist entry (design §10.9-A CORRECTION). A tree site is
    (file, function, verb) — the whole-tree shape (superseding the retired per-file local.py entry)
    — plus the L2 ATTRIBUTION CHANNEL:

    - ``exempt_name`` — the NAMED ``governed.governed_exempt`` token a non-``write_guard`` admin site
      carries (design step 4: migrate-governed uses ``governed_exempt("migrate-governed")`` rather
      than ``write_guard``, because it is NOT member-reachable — exempt-WITH-JUSTIFICATION, never
      silently dropped). ``None`` ⟺ the site attributes via ``write_guard`` frames instead.
    - ``runtime_observed`` — whether the L2b battery exercises the site. Since 63b-i-a §5.1 Q1 the
      memory table's ``_recreate_memory_table`` and ``_replay_record`` ARE driven under observation
      (the rebuild / replay batteries), so both carry ``runtime_observed=True`` (the #445 boot/admin
      bound shrank to nothing); ``runtime_observed=False`` remains for a site no battery can reach,
      carrying its named re-open trigger."""

    site: TreeMutationSite
    justification: str
    pin: str
    frames: tuple[str, ...]
    exempt_name: str | None = None
    runtime_observed: bool = True
    # 63b-i-a (design §1.4): the STATEMENT-scoped exemption + effect-based classification. ★SHAPE★:
    #   ``statement`` — the GOLDEN adjudicated SurrealQL (an oracle the adjudicator wrote down), compared
    #     whitespace-normalised against BOTH the exempt token's statement AND the observed executed
    #     statement (leg 2). "" ⟺ this entry is a plain write_guard LABEL frame (no exempt golden).
    #   ``effect`` — the adjudicated EFFECT predicate over the WHOLE ObservedEffect (rows + schema delta;
    #     see the report's "Substrate-shape decision" — one field serves a row entry AND a DDL frame).
    #     A row entry's predicate checks per-row deltas + an empty schema delta; a DDL frame's checks the
    #     schema delta == its golden AND no rows moved (§5.1 Q1). None ⟺ no effect adjudication yet (the
    #     builder wires the classifier to REQUIRE it for every 63b-new frame; §1.4).
    statement: str = ""
    effect: Callable[[ObservedEffect], bool] | None = None
    # 63b-i-a (design §5.1 Q1): a DDL/LABEL frame carries an effect predicate but has NO L1 raw
    # mutation LITERAL — ``ensure_ready`` passes ``generate_memory_ddl()`` (a call result), not a
    # literal SurrealQL string, so the L1 AST scan never derives it as a site. ``l1_site=False``
    # marks such a label-only entry so the L1 containment ghost-check EXCLUDES it (it is covered by
    # the L2 effect leg + L2a ``function_calls_named``, never by a derived L1 site). Default
    # True — a site-backed entry (a raw literal L1 derives). Substrate-shape (report §decision).
    l1_site: bool = True


def classify_tree_observed_write(
    observed: ObservedWrite, allowlist: Sequence[TreeWriteAllowlistEntry]
) -> bool:
    """True iff the observed mutation is ATTRIBUTED (design §10.9-A CORRECTION L2b, §1.4, §1.9 item 3
    — deny-by-default). Two channels; the LABEL leg is NARROWED by §1.4 (it now RUNS the matched
    entry's effect predicate) and the EXEMPT leg is FOUR-leg:

    - **LABEL leg** — the write carries a ``write_guard`` label that MATCHES an allowlist entry's
      ``frames``, AND that entry's ``effect`` predicate HOLDS for ``observed.effect``. A labeled
      write whose effect FAILS its entry predicate is UNCLASSIFIED (adversary MISSING PIN #1 / §1.4:
      "the classifier RUNS a label entry's effect predicate ∀ label frame" — the naive
      ``if observed.label is not None: return True`` re-widens the R2/#138 bound this narrows).
    - **EXEMPT leg** — the write carries an :class:`ExemptToken` and its entry (keyed
      ``entry.exempt_name == token.name``) satisfies ALL FOUR legs: (1) name; (2) golden text —
      ``normalise(token.statement) == normalise(entry.statement) == normalise(observed.statement)``;
      (3) effect — ``entry.effect(observed.effect)`` holds; (4) origin —
      ``token.origin == (entry.site.file, entry.site.function)`` (the origin captured at CONTEXT
      ENTRY, §1.9 item 3c — NOT ``observed.origin_site``, which at runtime is the call-time ``_txn``
      driver). Legs 2 and 3 are INDEPENDENT (2 catches a different-shaped statement smuggled under
      the token; 3 catches a golden edited to bless a seizure). A site BORROWING another's token
      yields a foreign ``token.origin`` → leg 4 RED.

    The token is read BY ATTRIBUTE (``.name`` / ``.statement`` / ``.origin``), so production's
    structurally-identical ``governed.ExemptToken`` and this substrate's :class:`ExemptToken` flow
    through the SAME classifier. A mutation matching NEITHER channel is UNCLASSIFIED (the red signal).

    ★CONTRACT SHAPE★ — the 63b-i-a builder REWRITES the body to the above; at HEAD it is the retired
    2-leg rule (``if label is not None: return True`` — the exact re-widening MISSING PIN #1 REDs —
    plus a bare-name exempt compare), getattr-tolerant so ``active_exempt`` unbuilt → ``exempt`` None
    → the migrate write is unclassified → RED-until-built.

    ⚠ NAMED ACCEPTED BOUND, NARROWED (finding #138 class — the HAND-SET-LABEL bound; §10.9-A step 6
    R2 STANDS narrowed by §1.4/§1.7 + CLAUDE.md "A GATE NEEDS A THREAT MODEL — WRITE DOWN WHO IT IS
    FOR"). Under the LABEL leg a hand-set ``write_guard`` label still classifies a write WHOSE EFFECT
    ITS ENTRY PREDICATE ALLOWS — so a production site that hand-sets a label without routing through
    ``governed.guarded_write`` can launder an effect the predicate PERMITS (e.g. an ``importance``-only
    bump under ``_reinforce``). The effect predicate NARROWS what such a hand-set label can launder
    (it can no longer seize a governed column under ``_reinforce`` — MISSING PIN #1) but does NOT
    CLOSE the class. That is an ACCEPTED bound, NOT a defect: F5 is a static net for the HONEST
    developer (#131), never a boundary against the HOSTILE author (#138, who already ships arbitrary
    code). RE-OPEN TRIGGER: the threat model changing to an untrusted contributor / hosted deployment
    (task 571ef1a's own territory)."""
    if observed.label is not None:
        return _label_leg_classifies(observed, allowlist)
    return _exempt_leg_classifies(observed, allowlist)


def _normalise_statement(statement: str) -> str:
    """Whitespace-collapse a SurrealQL statement for the golden compare (design §1.4 leg 2) — the SAME
    rule the contract module's ``_normalise`` applies, so the classifier's leg-2 match and the golden
    both-ways proof agree by construction."""
    return " ".join(statement.split())


def _label_leg_classifies(
    observed: ObservedWrite, allowlist: Sequence[TreeWriteAllowlistEntry]
) -> bool:
    """The LABEL leg (§1.4 / adversary MISSING PIN #1) — NARROWED: a labeled write classifies iff its
    label matches a (non-exempt) entry's ``frames`` AND that entry's ``effect`` predicate HOLDS for the
    observed effect. A labeled write whose effect FAILS its entry predicate is UNCLASSIFIED — the naive
    ``if observed.label is not None: return True`` re-widens the R2/#138 hand-set-label bound."""
    for entry in allowlist:
        if entry.exempt_name is not None or observed.label not in entry.frames:
            continue
        if entry.effect is None:
            return True  # a legacy label frame carrying no effect predicate classifies on the label
        if observed.effect is not None and entry.effect(observed.effect):
            return True
    return False


def _exempt_leg_classifies(
    observed: ObservedWrite, allowlist: Sequence[TreeWriteAllowlistEntry]
) -> bool:
    """The EXEMPT leg (§1.4 / §1.9 item 3c) — FOUR legs, read BY ATTRIBUTE so production's
    ``governed.ExemptToken`` and this substrate's twin flow through the SAME classifier. Legs 2 (golden
    text == token == observed) and 3 (the effect predicate) are INDEPENDENT; leg 4 is the context-entry
    origin match (a borrowed token from a foreign frame fails). A missing ``name`` (HEAD's bare-name
    ``str`` exempt) is unclassified."""
    exempt = observed.exempt
    token_name = getattr(exempt, "name", None)
    if token_name is None:
        return False
    token_statement = getattr(exempt, "statement", None)
    token_origin = getattr(exempt, "origin", None)
    for entry in allowlist:
        if entry.exempt_name != token_name:  # leg 1 — the channel name
            continue
        legs_2_and_3_hold = (
            token_statement is not None
            and observed.statement is not None
            # leg 2 — golden text (catches a different-shaped statement smuggled under the token):
            and _normalise_statement(token_statement)
            == _normalise_statement(entry.statement)
            == _normalise_statement(observed.statement)
            # leg 3 — effect (catches a golden EDITED to bless a seizure whose text matched):
            and entry.effect is not None
            and observed.effect is not None
            and entry.effect(observed.effect)
        )
        # leg 4 — origin captured at CONTEXT ENTRY (§1.9 item 3c): a borrowed token yields a foreign one.
        return legs_2_and_3_hold and token_origin == (entry.site.file, entry.site.function)
    return False


def exempt_entry_is_self_contained(entry: TreeWriteAllowlistEntry, *, source: str) -> bool:
    """True iff an EXEMPT allowlist entry is SELF-CONTAINED — its L1-derived literal site IS its
    seam-call site: the function enclosing the raw mutation literal (``entry.site.function``) ALSO
    calls the store seam (``run_query`` / ``execute_transaction``) in ``source`` (design §10.9-A
    CORRECTION step 6, RIDER R1 — ``lore_comms #8044`` / this doc's step 6).

    WHY THIS IS THE PREMISE THE EXEMPT-ORIGIN MATCH RESTS ON: the both-ways classifier
    (:func:`classify_tree_observed_write`) matches an exempt token by the RUNTIME ``(file, symbol)``
    origin against the allowlist entry's registered ``site``. That match is SOUND only when the
    literal (what L1 derives the site FROM) and the seam call (what the runtime origin walk sees) are
    the SAME symbol — true of ``_migrate_memory_scope`` (the ``UPDATE {MEMORY_TABLE} … WHERE scope IS
    NONE`` literal AND its ``run_query`` both live in it). For a NON-self-contained future candidate —
    a fragment-builder whose literal is in ``_build_X`` but whose seam fires from ``_drain`` (63b/64) —
    L1's site (``_build_X``) and the runtime origin (``_drain``) DIFFER, so the origin match would be
    UNSOUND (a red with no design signal, or a mis-sited entry dodging it). Making self-containment a
    CHECKED VARIABLE ∀ exempt entries surfaces that design question at allowlist-VALIDITY time — the
    reach-as-hidden-constant class one level up, inside the exempt channel (adversary-63a-v §P1c REACH
    ATTACK's own finding; THE LEVER: an askable premise, not a remembered property).

    ONE IMPLEMENTATION (design §3.2 RIDER): reuses :func:`function_calls_named` (the channel-agnostic
    'does this frame call ``<name>``' scan) — the SAME seam already used for the ``write_guard`` /
    ``governed_exempt`` L2a checks. Source-parametrised (pure): the live pin reads ``entry.site.file``;
    the R1 discrimination mutation-proof passes a SYNTHETIC non-self-contained source. 63b/64 exempt
    entries reuse this predicate — a governed table's contract is a parametrisation, never a copy."""
    return function_calls_named(source, entry.site.function, "run_query") or function_calls_named(
        source, entry.site.function, "execute_transaction"
    )


def exempt_frame_raw_memory_mutations(
    entry: TreeWriteAllowlistEntry,
    *,
    source: str,
    table: str = MEMORY_TABLE,
    table_const_hint: str = "MEMORY_TABLE",
) -> list[str]:
    """EVERY raw SurrealQL mutation STATEMENT of ``table`` co-located in an EXEMPT entry's frame
    (``entry.site.function``), as reconstructed statement SHAPES — the ∀-SET the both-ways
    classifier trusts the WHOLE frame for (design §10.9-A CORRECTION step 6 R3 /
    adversary-63a-v2 §R3 / finding #448).

    WHY A LIST OF STATEMENTS, NOT A SET OF SITES: the both-ways classifier
    (:func:`classify_tree_observed_write`) blesses ANY mutation running under a matching exempt
    token whose runtime origin equals the entry's registered ``(file, symbol)`` — so it trusts the
    frame's ENTIRE raw-mutation set, not the ONE statement the allowlist adjudicated. But the
    whole-tree scanner :func:`governed_table_raw_mutation_sites` keys by (function, VERB) and
    COLLAPSES two same-verb writes in one function to ONE :class:`MutationSite`; and the base-3
    justification pin reads only the FIRST ``UPDATE … SET scope`` shape. A SECOND co-located memory
    write (a seizure ``UPDATE {table} SET scope … WHERE scope = <owned>``) therefore launders past
    L1 (collapsed) and the first-match shape pin (shadowed) while the exempt token classifies it
    (co-located ⇒ origin match holds) — adversary-63a-v2 §R3, the reach-as-hidden-constant class ONE
    LEVEL DOWN inside the exempt channel R1 hardened. This returns the shape of EVERY matching
    statement (a LIST — never a verb-keyed set, never first-match), so the R3 pin can make the
    frame's raw-mutation SET a CHECKED VARIABLE ∀: exactly one, and that one the allowlisted shape.

    ONE IMPLEMENTATION (design §3.2 RIDER): reuses the SAME statement-shape primitives as the
    whole-tree scan — :func:`_statement_shape` / :func:`_raw_mutation_of_table` /
    :func:`_enclosing_functions` / :func:`_docstring_node_ids` — so the #444 concatenation static
    bound and the docstring/prose exclusion are inherited, table-parametrised. It DIFFERS from
    :func:`governed_table_raw_mutation_sites` in exactly the axis R3 turns on: it aggregates
    STATEMENTS (order-independent list), never (function, verb) sites, so two same-verb UPDATEs
    are TWO entries, not one. Source-parametrised (pure): the live pin reads ``entry.site.file``;
    the R3 discrimination mutation-proof passes a SYNTHETIC frame source. 63b/64 exempt entries
    reuse this predicate — a governed table's contract is a parametrisation, never a copy.

    ⚠ NAMED ACCEPTED BOUND (finding #449 — the R4-a SHAPE-SUBSTRING bound): this returns the frame's
    raw-mutation STATEMENTS, but the callers that adjudicate the blessed SHAPE (the R3 exempt-frame
    single-shape pin + the base-3 justification pin) match ``WHERE scope IS NONE`` by SUBSTRING, not by
    an exact ``WHERE == scope IS NONE``. So a single OR-extended statement ``… WHERE scope IS NONE OR
    scope = $victim`` is ONE statement (the count leg passes) that CONTAINS the substring (the shape
    leg passes) yet seizes OWNED rows. Accepted under F5's HONEST-DEVELOPER threat model (the #138
    HOSTILE-AUTHOR class is out of scope); the exact-shape / statement-scoped root-fix is 63b (task
    571ef1a). PINNED by ``TestTheAcceptedF5BoundsArePinned::
    test_r4a_the_shape_leg_matches_where_scope_is_none_by_substring`` (RED the day 63b closes it —
    delete the pin + this clause then, and say so). RE-OPEN TRIGGER: 63b's statement-scoped exemption,
    or the first time an exempt frame becomes member-reachable or served."""
    tree = ast.parse(source)
    owner = _enclosing_functions(tree)
    docstrings = _docstring_node_ids(tree)
    shapes: list[str] = []
    for node in ast.walk(tree):
        if id(node) in docstrings or not isinstance(node, (ast.Constant, ast.JoinedStr)):
            continue
        if owner.get(id(node), "<module>") != entry.site.function:
            continue
        shape = _statement_shape(node)
        if not shape:
            continue
        if _raw_mutation_of_table(shape, table, table_const_hint) is None:
            continue
        shapes.append(shape)
    return shapes


# =========================================================================== #
# 63b-i-a (design §1.5c-iii) — THE GOVERNED-POPULATION SET is DERIVED from ``surreal_schema``'s EMITTED
# DDL (63c-i-a r3 re-key, amendment-4 MP-D — the dated history below speaks of the retired AST form), so a
# new governed table joins F5's reach by the SAME derivation that governs it (the growth detector
# ONE LEVEL UP: reach as a checked variable over the SET of populations, not only over sites within
# one). At ``e4b8945`` the derivation yields ``{memory}`` (§5.1 Q2 iii — ``_message_statements`` does
# not yet call ``_governed_field_specs``); ii-a's DDL grows it to {memory, message, to}. A governed
# population with no F5 case is RED (deny-by-default over the population SET).
# =========================================================================== #


# DUAL (63c-i-a r3, amendment-4 MP-D): the AST resolver over ``surreal_schema``'s SOURCE —
# ``_GOVERNED_FIELD_SPECS_EMITTER`` / ``_DEFINE_RELATION_EMITTER`` / ``_schema_string_constants`` /
# ``_resolve_schema_table`` / ``_governed_node_tables`` / ``_governed_relation_tables`` — is RETIRED.
# Its reach was a hand-list of SPELLINGS (Constant, Name→Assign, r2's Name→ImportFrom); keyword
# endpoints, an ``Attribute``, an ``AnnAssign``, a relative or failed import resolved to None and the
# relation silently never joined (adversary-r2 N4/N4h: 2521 passed / 0 failed), and the node leg keyed
# on a helper NAMED ``_<t>_statements`` (a governed slice built in another helper never joined): the
# reach receded one level per round. Its VIRTUES — (1) an OUTPUT, never a hand-list; (2) keyed on
# something a field-presence walk cannot fake (a lone packet-62 ``agent.owner_principal``, F-TRAP-1,
# never joins) — are carried by the emitted-DDL derivation below: (1) by
# ``schema_ddl_generators`` (every ``generate_*_ddl``, by inspection) + the growth pins; (2) by the
# FULL-TRIO node leg (one governed column of three does not join), pinned both ways on synthetic DDL.
# Which EMITTER produced the trio is W1-1's rewrite kill-pin's job, never this resolver's (a hand-rolled
# trio IS governed data: it joins here AND reds W1-1).
# r4 (amendment-6 R-5): the retired resolver's third virtue — (c) node membership keyed on the CALLERS of
# ``_governed_field_specs`` (emitter provenance) — survives OUTSIDE this derivation, in the per-table
# emitter-provenance pins (``test_governed_schema_63a.py``, ``test_message_governed_ddl_63b_ii_a.py``) and
# W1-1's rewrite kill-pin (adversary-r3 §3.1).

#: ``DEFINE FIELD [OVERWRITE|IF NOT EXISTS] <column> ON [TABLE] <table>`` — the node leg's reader over
#: EMITTED statements (the ``DEFINE`` keyword forms our generators emit; store-ref §1.1).
_DEFINE_FIELD_ON_RE = re.compile(
    r"^DEFINE\s+FIELD\s+(?:OVERWRITE\s+|IF\s+NOT\s+EXISTS\s+)?(?P<column>\S+)\s+ON\s+(?:TABLE\s+)?"
    r"(?P<table>[^\s;]+)",
    re.IGNORECASE,
)


def governed_trio_columns() -> frozenset[str]:
    """The governed column NAMES, DERIVED from ``surreal_schema._governed_field_specs()`` (the ONE
    emitter of the governed trio) — never a hand-list of three strings (amendment-4 MP-D point 2)."""
    from loremaster.store import surreal_schema  # noqa: PLC0415 - lazy: no schema import at module load

    columns = frozenset(spec[0] for spec in surreal_schema._governed_field_specs())  # noqa: SLF001
    assert len(columns) >= 2, f"the governed field spec set is implausibly small: {sorted(columns)}"
    return columns


def governed_node_tables(emitted_ddl: str) -> set[str]:
    """The governed NODE tables of ``emitted_ddl``: a table is governed iff the DDL defines EVERY column
    of the governed trio ON it (matched ``DEFINE FIELD … <col> ON <table>`` over its statements). A lone
    ``owner_principal`` (the packet-62 ``agent`` field, F-TRAP-1) is one of three and does NOT join."""
    from _enforced_relations_scaffold import statements  # noqa: PLC0415

    trio = governed_trio_columns()
    columns_by_table: dict[str, set[str]] = {}
    for statement in statements(emitted_ddl):
        match = _DEFINE_FIELD_ON_RE.match(statement)
        if match is not None:
            columns_by_table.setdefault(match.group("table"), set()).add(match.group("column"))
    return {table for table, columns in columns_by_table.items() if trio <= columns}


def governed_relation_tables(emitted_ddl: str, nodes: set[str]) -> set[str]:
    """The relation tables of ``emitted_ddl`` whose IN or OUT endpoint is a governed node — endpoints
    PARSED from the emitted ``TYPE RELATION IN <t> OUT <t>`` text (``relation_endpoints``, which FAILS
    CLOSED on an unparseable statement), so no source spelling exists at this level."""
    from _enforced_relations_scaffold import relation_endpoints  # noqa: PLC0415

    return {
        edge
        for edge, (in_tables, out_tables) in relation_endpoints(emitted_ddl).items()
        if (in_tables | out_tables) & nodes
    }


def synthetic_field_ddl(table: str, columns: Iterable[str]) -> str:
    """SYNTHETIC emitted-DDL text defining ``columns`` on ``table`` (one ``DEFINE FIELD OVERWRITE`` each) —
    the growth/reach pins' fixture for :func:`governed_populations` (pass ``governed_trio_columns()`` for
    a governed table, a proper subset for the F-TRAP-1 negative). Derived column names, never a restated
    trio, so a change to ``_governed_field_specs`` moves every fixture built on it."""
    return "".join(
        f"DEFINE FIELD OVERWRITE {column} ON {table} TYPE option<string>;\n" for column in sorted(columns)
    )


def governed_populations(*, emitted_ddl: str | None = None) -> frozenset[str]:
    """DERIVE the governed table population set from the EMITTED schema DDL (design §1.5c-iii, §1.9 item
    2 — mechanism re-keyed by amendment-4 MP-D, intent preserved).

    ``{t : the emitted DDL defines every governed-trio column ON t}`` ∪ ``{relation tables whose emitted
    IN or OUT endpoint is in that set}``. The corpus is the union of EVERY ``surreal_schema``
    ``generate_*_ddl`` (``_enforced_relations_scaffold.emitted_schema_ddl`` — by inspection, required
    arguments from the signature, fail closed), i.e. the ARTIFACT, never the source spelling.

    REACH IS A CHECKED VARIABLE: pass ``emitted_ddl`` — SYNTHETIC DDL TEXT — to derive from THAT instead
    (the growth pins seed a synthetic table carrying the trio / a synthetic relation over it and assert the
    output GROWS). KEYWORD-ONLY and RENAMED from r2's ``schema_source`` on purpose: its meaning changed
    from Python source to emitted DDL, so an old caller passing source text fails loudly (``TypeError``)
    instead of silently deriving nothing."""
    if emitted_ddl is None:
        from _enforced_relations_scaffold import emitted_schema_ddl  # noqa: PLC0415

        emitted_ddl = emitted_schema_ddl()
    nodes = governed_node_tables(emitted_ddl)
    return frozenset(nodes | governed_relation_tables(emitted_ddl, nodes))
