"""Contract — packet 61a-w4, the append-only ``AuditStore`` surface (the store substrate).

Written by ``contract-61a-w4`` (session ``pkt61``, 2026-08-23). The builder builds FROM this;
it writes NO production code. *Every "RED before <sha>" claim is scoped to the tree at
``e92bd0f``: the tdd STUB phase creates ``loremaster/loremaster/audit.py`` with
``AuditStore.append``/``append_fragment`` raising ``NotImplementedError`` and
``AuditStoreError`` defined, so every behavioural pin fails BEHAVIOURALLY, never on an
ImportError.* The required stub surface is enumerated in ``REPORT-contract-61a-w4.md``.

SPEC: ``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` §Fork G (the ``AuditStore``:
append-only, narrow surface, composable ``TxnFragment``, threat model IN the instrument) +
§Fork I (born WRAPPED — ``AuditStore.append`` routes engine rejections through
``_txn.wrap_store_rejection`` from BIRTH, as the 9th consumer, NOT a hand-rolled clone). The
lifecycle (connect / ``ensure_ready`` / ``close``) MIRRORS ``KeepStore``; the composable
fragment MIRRORS the ``graph_surreal.purge_file_fragment`` return-a-``TxnFragment`` precedent.

STORE LAW (``docs/reference/surrealdb-31-capabilities.md``): §2 (CONTENT writes,
``type::record`` binds, ``str(RecordID)`` round-trips, an explicit projection reads NONE),
§3 (``compose`` + ``execute_transaction`` — a multi-statement ``query()`` validates
``statement[0]`` only; the wrap taxonomy, transport passes through untouched).

⚠ THE 61a/61b BOUNDARY (held): this contract pins Layer 1 (the narrow class SURFACE — no
mutator method) + the composable seam + born-wrapped. It does NOT pin Layer 2 (the PDP admin
short-circuit's ``audit`` carve-out — ``authorize(admin, DELETE, audit)=DENY``) NOR
``requires_audit`` — BOTH are 61b (PDP logic). Those Fork G pins live in the 61b contract.

⚠ DECISIONS surfaced (brief-base §2), see ``REPORT-contract-61a-w4.md``:
  (1) the composable seam is a PUBLIC ``append_fragment(...) -> TxnFragment`` (the dominant
      house precedent; ``append`` executes ``compose(self.append_fragment(...))``);
  (2) ``append(...) -> str`` returns the created row's ``str(RecordID)`` id (a useful handle,
      lets 61 tests target the exact row without a read verb, which Fork G DEFERS);
  (3) ``actor_principal``/``actor_agent`` are BARE ids (the resolved ``Subject`` stamp), bound
      via ``type::record``; ``AuditStore`` composes NO ``PrincipalStore`` (append takes
      already-resolved ids, unlike ``KeepStore``'s email verbs).

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). NO skip marker — an unreachable store is a
LOUD failure, not a skip.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import itertools
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import loremaster.audit as audit_module
import pytest
import pytest_asyncio
from _enforced_relations_scaffold import apply_ddl
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
from loremaster.audit import AuditStore, AuditStoreError
from loremaster.principals import PrincipalStore
from loremaster.store._txn import (
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
    TxnFragment,
    compose,
    execute_transaction,
)
from loremaster.store.surreal_schema import (
    AGENT_TABLE,
    AUDIT_TABLE,
    PRINCIPAL_TABLE,
    generate_ddl,
)

_ACTOR_PRINCIPAL = "admin_alice"
_ACTOR_AGENT = "agent_a1"
# The DENORMALIZED human identity captured at APPEND time (Fork G addendum, §9 forensics) —
# DISTINCT from the link ids, so a build that stored the id where the value belongs is caught.
_ACTOR_EMAIL = "alice@example.com"
_ACTOR_AGENT_NAME = "agent-alice-laptop"
_TARGET_TABLE = "task"
_TARGET_ROW = "task:t_9f3"


def _append_call_kwargs(**overrides: Any) -> dict[str, Any]:
    """The full required kwargs for ``append``/``append_fragment`` (the actor link ids + the
    denormalized identity + action + target), overridable per test.

    The identity columns are REQUIRED on the production method with NO default (Fork G addendum
    — never a fixture monoculture on a forensic column); this HELPER supplies them for the many
    writes that do not test identity, while the identity pins pass DISTINCT values explicitly."""
    base: dict[str, Any] = {
        "actor_principal": _ACTOR_PRINCIPAL,
        "actor_agent": _ACTOR_AGENT,
        "actor_email": _ACTOR_EMAIL,
        "actor_agent_name": _ACTOR_AGENT_NAME,
        "action": "WRITE",
        "target_table": _TARGET_TABLE,
        "target_row": _TARGET_ROW,
    }
    base.update(overrides)
    return base

# The ONLY public methods an append-only store may expose (allowlist-the-safe, #344/#345 —
# NEVER a denylist of mutators; the forbidden set is unbounded, the safe set is small). A
# NEW public method outside this set reds the surface pin until it is ruled safe.
_ALLOWED_PUBLIC_METHODS = frozenset({"append", "append_fragment", "ensure_ready", "close"})

# The mutator names an append-only store must NEVER expose — used ONLY to prove the allowlist
# genuinely EXCLUDES them (a meta-control on the allowlist itself), never as the primary gate.
# ⚠ THE ALLOWLIST IS THE PRIMARY GATE (#344/#345): the forbidden set is unbounded, so this
# denylist is a control, never the reach — the reachable-surface allowlist below is what binds.
_FORBIDDEN_MUTATOR_NAMES = frozenset(
    {"update", "delete", "remove", "purge", "set_scope", "set_owner", "set_rank",
     "upsert", "overwrite", "edit"}
)


def _bare(record_id: str) -> str:
    """The id portion of a ``str(RecordID)`` (``audit:xyz`` → ``xyz``); a bare id passes
    through (the ``KeepStore._record_id_part`` idiom)."""
    _, separator, id_part = record_id.partition(":")
    return id_part if separator else record_id


_AUDIT_READ_PROJECTION = (
    "actor_principal, actor_agent, actor_email, actor_agent_name, action, "
    "target_table, target_row, old_value, new_value, created_at"
)


async def _read_row(connection: SurrealConnection, record_id: str) -> Any:
    """Read one ``audit`` row through an EXPLICIT projection (store §2 — a NONE ``option<>``
    reads back as ``None`` under a projection, where ``SELECT *`` omits the key)."""
    rows = await run(
        connection,
        f"SELECT {_AUDIT_READ_PROJECTION} FROM type::record('{AUDIT_TABLE}', $id)",
        {"id": _bare(record_id)},
    )
    assert rows, f"expected one audit row for {record_id!r}, got {rows!r}"
    return rows[0]


async def _count(env: SurrealEnv) -> int:
    """Raw ``audit`` row count via a fresh admin connection (tolerant of an absent table)."""
    connection = await connect_admin(env)
    try:
        try:
            rows = await run(connection, f"SELECT count() FROM {AUDIT_TABLE} GROUP ALL")
        except Exception:  # noqa: BLE001 - an absent table is not the failure under test
            return 0
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            return 0
        return int(rows[0].get("count", 0))
    finally:
        await connection.close()


@pytest_asyncio.fixture()
async def audit_store_env() -> AsyncIterator[tuple[AuditStore, SurrealEnv]]:
    """A ready :class:`AuditStore` on a fresh unique database, reaped on exit.

    ``AuditStore.ensure_ready`` applies ``generate_audit_ddl`` on its OWN connection (the
    ``KeepStore`` lifecycle). NEITHER ``principal`` NOR ``agent`` is applied first — a
    ``record<t>`` field-def needs no target table at DDL time (``principal_keys.py``), and a
    ``record<t>`` link does not validate endpoint existence (store §4), so ``actor_principal``/
    ``actor_agent`` bind bare ids without seeding. ⚠ At the STUB stage ``ensure_ready`` applies
    the audit slice fine but ``append`` raises ``NotImplementedError`` → the RED is behavioural.
    """
    env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    store = AuditStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await store.ensure_ready()
    try:
        yield store, env
    finally:
        await store.close()
        await drop_database(env)


# =========================================================================== #
# The typed error + the append-only class SURFACE (Layer 1) — offline, AST/introspection.
# =========================================================================== #


def _reachable_public_members(cls: type) -> set[str]:
    """Every PUBLIC member reachable on ``cls`` across its FULL MRO (inherited included),
    excluding dunders and ``_private`` — runtime introspection over ``inspect.getmembers``,
    which walks ``__mro__``.

    ⚠ SECURITY-CRITICAL (adversary BLOCKER 1): a class-BODY AST scan sees only methods DEFINED
    on ``AuditStore`` — so a build where ``AuditStore(_Base)`` INHERITS a ``purge``/``delete``/
    ``update`` from ``_Base`` would pass a body-only surface pin while an admin could erase the
    trail through the inherited verb, DEFEATING append-only. Resolving the MRO closes that gap:
    an inherited mutator IS reachable on an instance, so it must be counted."""
    return {name for name, _member in inspect.getmembers(cls) if not name.startswith("_")}


def _class_body_public_methods(source: str, class_name: str) -> set[str]:
    """Every PUBLIC method defined in ``class_name``'s BODY (AST, no MRO) — used ONLY as the
    discrimination control proving the MRO detector is strictly stronger (a body scan MISSES an
    inherited mutator)."""
    cls = next(
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return {
        method.name
        for method in cls.body
        if isinstance(method, ast.AsyncFunctionDef | ast.FunctionDef)
        and not method.name.startswith("_")
    }


class TestTheErrorHierarchy:
    def test_audit_store_error_is_a_runtime_error(self) -> None:
        """``AuditStoreError`` is the domain error (the ``KeepStoreError``/``PrincipalStoreError``
        parity — a ``RuntimeError`` subclass)."""
        assert issubclass(AuditStoreError, RuntimeError)


class TestTheAppendOnlySurfaceLayer1:
    """⚠ APPEND-ONLY, LAYER 1 (Fork G) — the narrow class surface. You cannot CALL what is not
    there. This is w4's half; Layer 2 (the 61b PDP ``audit`` carve-out) is NOT pinned here.

    The surface is measured over the RESOLVED MRO (``_reachable_public_members``), NOT the class
    body — an INHERITED mutator is just as callable as a defined one and would equally defeat
    append-only (adversary BLOCKER 1, security-critical)."""

    def test_the_reachable_public_surface_is_within_the_safe_allowlist(self) -> None:
        """ALLOWLIST-THE-SAFE over the FULL MRO (#344/#345): the set of public members reachable
        on an ``AuditStore`` instance (inherited INCLUDED) ⊆ {append, append_fragment,
        ensure_ready, close}. A NEW member — a ``delete``/``update``/``purge``, OWN or INHERITED,
        or anything unforeseen — grows the reachable set past the allowlist and reds this pin
        until ruled. DERIVED (introspection) + allowlist-the-safe, never a denylist of the
        unbounded forbidden set."""
        reachable = _reachable_public_members(AuditStore)
        assert reachable, "AuditStore exposes NO public member across its MRO — introspection broke"
        extra = reachable - _ALLOWED_PUBLIC_METHODS
        assert not extra, (
            f"AuditStore exposes public member(s) OUTSIDE the append-only safe allowlist "
            f"{sorted(_ALLOWED_PUBLIC_METHODS)} (across its full MRO — inherited included): "
            f"{sorted(extra)}. An append-only store must expose no mutator — if a new member is "
            f"genuinely safe, add it to the allowlist and say so (Fork G Layer 1)."
        )

    def test_append_is_actually_present(self) -> None:
        """The allowlist is not vacuously satisfied by an empty class: ``append`` — the ONE
        write primitive — must be reachable."""
        assert "append" in _reachable_public_members(AuditStore), (
            "AuditStore must expose an `append` method (the append-only write primitive)"
        )

    def test_no_mutator_member_is_reachable(self) -> None:
        """The denylist READ FROM THE OTHER SIDE (a CONTROL on the allowlist, not the primary
        gate): none of the classic mutator/destroyer names is reachable across the MRO. An
        append-only store that grew (or inherited) an ``update``/``delete``/``purge``/``set_*``
        would let an in-process caller rewrite or erase the trail (Fork G Layer 1)."""
        offenders = _reachable_public_members(AuditStore) & _FORBIDDEN_MUTATOR_NAMES
        assert not offenders, (
            f"AuditStore exposes/inherits mutator method(s) {sorted(offenders)} — an append-only "
            f"store must expose none (Fork G Layer 1)"
        )

    def test_the_MRO_detector_sees_an_INHERITED_mutator(self) -> None:
        """⚠ MUTATION-PROOF / DISCRIMINATION (adversary BLOCKER 1): the MRO detector flags a
        mutator INHERITED from a base — the exact defeat a class-BODY scan misses. A synthetic
        store inheriting ``purge`` from a base: ``_reachable_public_members`` INCLUDES ``purge``
        (so the allowlist pin WOULD red on it), while the class-BODY scan does NOT — proving the
        MRO surface is strictly stronger and the security gap is closed."""

        class _MutatorBase:
            async def purge(self) -> None:  # a mutator living on a BASE, not the leaf class
                ...

        class _LeakyAuditStore(_MutatorBase):
            async def append(self) -> None:
                ...

        reachable = _reachable_public_members(_LeakyAuditStore)
        assert "purge" in reachable, (
            "the MRO detector FAILED to see an inherited mutator — the security gap is still open"
        )
        assert reachable - _ALLOWED_PUBLIC_METHODS, (
            "the allowlist pin would NOT red on a class that inherits a mutator — BLOCKER 1 unfixed"
        )
        # CONTROL: a class-BODY-only scan MISSES the inherited mutator (strictly weaker).
        leaky_source = (
            "class _MutatorBase:\n"
            "    async def purge(self) -> None: ...\n"
            "class _LeakyAuditStore(_MutatorBase):\n"
            "    async def append(self) -> None: ...\n"
        )
        body_only = _class_body_public_methods(leaky_source, "_LeakyAuditStore")
        assert "purge" not in body_only, (
            "control failed: a class-body scan should MISS the inherited mutator (it would not, "
            "so the discrimination proof is vacuous)"
        )

    def test_the_allowlist_itself_excludes_every_mutator(self) -> None:
        """META-CONTROL on the allowlist (a probe needs a control): the safe allowlist must
        contain NONE of the forbidden mutator names — so a build cannot "satisfy" the surface
        pin by ADDING ``delete`` to ``_ALLOWED_PUBLIC_METHODS``. Guards this contract's own
        instrument against being weakened."""
        assert _ALLOWED_PUBLIC_METHODS.isdisjoint(_FORBIDDEN_MUTATOR_NAMES), (
            f"the safe allowlist leaked a mutator name: "
            f"{sorted(_ALLOWED_PUBLIC_METHODS & _FORBIDDEN_MUTATOR_NAMES)}"
        )


class TestTheThreatModelIsStatedInTheInstrument:
    """⚠ A GATE NEEDS A THREAT MODEL, STATED IN THE INSTRUMENT (CLAUDE.md / Fork G). The
    append-only guard is a boundary against a COMPROMISED/INJECTED ADMIN acting THROUGH lore's
    governed tools — NOT against direct-store/root access (lore is root, Version A). That
    ACCEPTED BOUND, with its Version-B re-open trigger, must be written on ``AuditStore`` so a
    future auditor does not call "a root user can delete audit rows" a hole.

    ⚠ KNOWN BOUND (a prose pin): this checks the load-bearing CONCEPTS are present, not exact
    wording — a novel phrasing that still states the model would pass. It exists because Fork G
    RULES the threat model be stated in the instrument; the concept set is the safe minimum.
    The threat model may live on the ``AuditStore`` CLASS docstring OR the ``audit`` MODULE
    docstring (both are "on AuditStore" — a reader lands on either), so this reads both."""

    @staticmethod
    def _threat_doc() -> str:
        return f"{AuditStore.__doc__ or ''}\n{audit_module.__doc__ or ''}".lower()

    def test_the_auditstore_docstring_states_append_only_in_process(self) -> None:
        doc = self._threat_doc()
        assert "append-only" in doc or "append only" in doc, (
            "AuditStore must state it is APPEND-ONLY (Fork G threat model — class or module docstring)"
        )
        assert "in-process" in doc or "in process" in doc, (
            "AuditStore must state the append-only guard is enforced IN-PROCESS "
            "(native PERMISSIONS is inert under root — Fork G / store §2.3)"
        )

    def test_the_docstring_states_the_accepted_root_bound(self) -> None:
        doc = self._threat_doc()
        assert "root" in doc or "direct-store" in doc or "direct store" in doc, (
            "AuditStore must state the ACCEPTED BOUND: it is NOT a boundary against "
            "direct-store/root access (lore connects as root, Version A) — else a future auditor "
            "calls that a hole (Fork G)"
        )

    def test_the_docstring_names_the_version_b_reopen_trigger(self) -> None:
        doc = self._threat_doc()
        assert "version b" in doc, (
            "AuditStore's docstring must name the RE-OPEN TRIGGER (Version B: per-principal record "
            "auth would let native PERMISSIONS enforce append-only in-engine) — every accepted "
            "bound carries a named re-open trigger (Fork G / the deferral law)"
        )


# =========================================================================== #
# append — Fork G: writes the record; old→new capture; a useful id handle. (LIVE)
# =========================================================================== #


class TestAppendWritesTheRecord:
    async def test_append_writes_a_WRITE_record_with_old_and_new(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        """Fork G: a WRITE fixture records ``old_value`` + ``new_value``, plus the actor stamp,
        action and target. ``append`` returns a non-empty id targeting the exact row; the row
        reads back with the exact values through a FRESH store read (not the return object)."""
        store, env = audit_store_env
        record_id = await store.append(
            **_append_call_kwargs(old_value={"status": "open"}, new_value={"status": "done"})
        )
        assert isinstance(record_id, str) and record_id, "append must return a non-empty id handle"
        connection = await connect_admin(env)
        try:
            row = await _read_row(connection, record_id)
        finally:
            await connection.close()
        assert row["action"] == "WRITE"
        assert str(row["actor_principal"]).endswith(_ACTOR_PRINCIPAL)
        assert str(row["actor_agent"]).endswith(_ACTOR_AGENT)
        assert row["actor_email"] == _ACTOR_EMAIL, "the denormalized actor_email did not round-trip"
        assert row["actor_agent_name"] == _ACTOR_AGENT_NAME, (
            "the denormalized actor_agent_name did not round-trip"
        )
        assert row["target_table"] == _TARGET_TABLE
        assert row["target_row"] == _TARGET_ROW
        assert row["old_value"] == {"status": "open"}
        assert row["new_value"] == {"status": "done"}
        assert row["created_at"] is not None, "created_at did not self-stamp"

    async def test_append_writes_a_DELETE_record_with_a_NONE_new_value(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        """Fork G old→new: a DELETE records ``old_value`` + ``new_value=None`` (no after-state).
        Read through the explicit projection so the omitted ``option<>`` reads as ``None``."""
        store, env = audit_store_env
        record_id = await store.append(
            **_append_call_kwargs(
                action="DELETE",
                target_table="finding",
                target_row="finding:f_1",
                old_value={"body": "gone"},
                new_value=None,
            )
        )
        connection = await connect_admin(env)
        try:
            row = await _read_row(connection, record_id)
        finally:
            await connection.close()
        assert row["action"] == "DELETE"
        assert row["old_value"] == {"body": "gone"}
        assert row["new_value"] is None, "a DELETE's new_value must be NONE"

    async def test_append_writes_a_SET_OWNER_record_capturing_the_owner_change(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        """Fork G old→new: a SET_OWNER records the owner change (old owner → new owner). The
        mirror ``option<>`` direction to the DELETE (the discrimination the DELETE pin needs)."""
        store, env = audit_store_env
        record_id = await store.append(
            **_append_call_kwargs(
                action="SET_OWNER",
                target_table="memory",
                target_row="memory:m_7",
                old_value={"owner_principal": "member_bob", "owner_agent": "agent_b2"},
                new_value={"owner_principal": "member_carol", "owner_agent": "agent_c3"},
            )
        )
        connection = await connect_admin(env)
        try:
            row = await _read_row(connection, record_id)
        finally:
            await connection.close()
        assert row["action"] == "SET_OWNER"
        assert row["old_value"] == {"owner_principal": "member_bob", "owner_agent": "agent_b2"}
        assert row["new_value"] == {"owner_principal": "member_carol", "owner_agent": "agent_c3"}

    async def test_two_appends_produce_DISTINCT_ids(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        """The id is a per-append ``ulid()`` (Fork G) — two appends never collide. ≥2 so a
        build that reused one id (or a fixed id) is caught."""
        store, _env = audit_store_env
        first = await store.append(**_append_call_kwargs(new_value={"n": 1}))
        second = await store.append(**_append_call_kwargs(new_value={"n": 2}))
        assert first != second, "two appends produced the SAME id — the ulid mint is broken"

    async def test_a_rejected_append_leaves_NO_row(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        """The rejection path: an append with an UNAUDITED action (``READ``) is refused by the
        store-side ASSERT and surfaces the domain error; no partial row is left behind (a single
        CREATE, atomic)."""
        store, env = audit_store_env
        before = await _count(env)
        with pytest.raises(AuditStoreError):
            await store.append(**_append_call_kwargs(action="READ", new_value={"n": 1}))
        assert await _count(env) == before, "a rejected append left an audit row behind"


class TestTheDenormalizedIdentitySurvivesActorDelete:
    """⚠ THE LOAD-BEARING §9 FORENSICS PIN (Fork G addendum, fixtures-must-discriminate) — the
    whole reason the denormalized identity columns exist. Write an audit row, then HARD-DELETE
    the actor PRINCIPAL (``PrincipalStore.delete``): the audit row's ``actor_email`` +
    ``actor_agent_name`` VALUES survive intact (a deleted/offboarded compromised admin's identity
    stays recoverable) EVEN THOUGH the ``actor_principal``/``actor_agent`` record LINKS now dangle.
    A build that stored ONLY the links (no denormalized value) REDS this — that is the point. The
    dangle-tolerated cascade is RULED (immutable history outlives the actor); no cascade/refuse of
    audit rows is pinned."""

    async def test_append_captures_the_EXACT_identity_provided(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        """POSITIVE CONTROL + discrimination: ``append`` records the EXACT ``actor_email`` /
        ``actor_agent_name`` the caller passed (DISTINCT from the module default), not a fixed
        value nor one re-derived from the link. A build that hardcoded or dropped them reds."""
        store, env = audit_store_env
        distinct_email = "distinct-actor@example.com"
        distinct_name = "agent-distinct-7"
        record_id = await store.append(
            **_append_call_kwargs(
                actor_email=distinct_email, actor_agent_name=distinct_name, new_value={"n": 1}
            )
        )
        connection = await connect_admin(env)
        try:
            row = await _read_row(connection, record_id)
        finally:
            await connection.close()
        assert row["actor_email"] == distinct_email, "append did not capture the exact actor_email"
        assert row["actor_agent_name"] == distinct_name, (
            "append did not capture the exact actor_agent_name"
        )

    async def test_actor_identity_survives_a_hard_principal_delete(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        store, env = audit_store_env
        # ``PrincipalStore.delete`` READS the ``keep`` table (FR-4 refuse-while-keeping) AND
        # cascades ``principal_key`` rows — so the FULL substrate must exist. Ready it once via
        # generate_ddl (fast on an empty DB), then exercise the REAL create/delete path.
        setup_connection = await connect_admin(env)
        try:
            await apply_ddl(setup_connection, generate_ddl(dim=env.dim), url=env.url)
        finally:
            await setup_connection.close()
        principal_store = PrincipalStore(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )
        try:
            offboarded_email = "compromised-admin@example.com"
            offboarded_name = "agent-compromised-laptop"
            principal = await principal_store.create(email=offboarded_email)
            actor_id = _bare(principal.id)  # the bare principal id for the actor_principal link
            record_id = await store.append(
                actor_principal=actor_id,
                actor_agent="agent_offboarded",
                actor_email=offboarded_email,
                actor_agent_name=offboarded_name,
                action="DELETE",
                target_table="memory",
                target_row="memory:m_victim",
                old_value={"body": "another principal's private memory"},
            )
            # Hard-delete the actor principal — the compromised admin is offboarded. (``delete``
            # returns the count of cascaded principal_key rows — 0 here, a keyless principal —
            # NOT a principal count; the genuine-gone check below is the real assertion.)
            await principal_store.delete(email=offboarded_email)

            connection = await connect_admin(env)
            try:
                # The principal row is genuinely GONE.
                gone = await run(
                    connection,
                    f"SELECT id FROM type::record('{PRINCIPAL_TABLE}', $id)",
                    {"id": actor_id},
                )
                assert not gone, "the actor principal is not actually deleted (the premise fails)"
                # The dereferenced LINK now dangles → NONE (the target is gone).
                deref = await run(
                    connection,
                    f"SELECT actor_principal.email AS e FROM type::record('{AUDIT_TABLE}', $id)",
                    {"id": _bare(record_id)},
                )
                row = await _read_row(connection, record_id)
            finally:
                await connection.close()

            # THE FORENSICS: the denormalized human identity survives the delete as VALUES.
            assert row["actor_email"] == offboarded_email, (
                "the offboarded actor's email did NOT survive the principal delete — a link-only "
                "build loses the identity the trail exists to preserve (§9 forensics)"
            )
            assert row["actor_agent_name"] == offboarded_name, (
                "the offboarded actor's agent name did NOT survive the principal delete"
            )
            # The LINK still holds the now-dangling RecordID (record<> links do not auto-clean —
            # store §2), and its DEREF yields None: the identity is recoverable ONLY via the
            # denormalized value, never the dead link.
            assert str(row["actor_principal"]).endswith(actor_id), (
                "the actor_principal link value changed — the dangling-link premise is wrong"
            )
            assert deref and deref[0].get("e") is None, (
                "dereferencing the dangling actor_principal link did not yield NONE after the "
                f"target was deleted: {deref!r} (the whole reason the value is denormalized)"
            )
        finally:
            await principal_store.close()


class TestAppendDoesNotContendOnAHotRow:
    """⚠ Fork G: the id is a ``ulid()``, NOT a counter/sequence mint — an audit write must NOT
    contend on a hot row (the whole point is a cheap, non-blocking append). ≥8-way concurrent
    (the repo's hot-row discipline): a build that "helpfully" introduced a counter-row mint
    would contend (and risk exhaustion/loss) where the ulid mint does not."""

    async def test_eight_concurrent_appends_all_land_with_distinct_ids(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        store, env = audit_store_env

        async def _one(index: int) -> str:
            return await store.append(
                **_append_call_kwargs(target_row=f"{_TARGET_TABLE}:row_{index}", new_value={"n": index})
            )

        ids = await asyncio.gather(*[_one(index) for index in range(8)])
        assert len(set(ids)) == 8, f"8 concurrent appends did not yield 8 distinct ids: {ids!r}"
        assert await _count(env) == 8, "8 concurrent appends did not leave 8 rows (contention/loss)"


class TestTheAppendIdIsCreationOrdered:
    """⚠ Fork G rules ``ulid()`` SPECIFICALLY for CREATION-ORDER sortability (an audit log is
    append-ordered). A ``uuid4`` (or any non-creation-ordered id) passes every OTHER store pin —
    the round-trip, the distinctness, the concurrency — so the creation-order PROPERTY, not the
    id SHAPE, is the discriminator Fork G's ruling demands (adversary BLOCKER 2)."""

    async def test_sequential_appends_produce_creation_ordered_ids(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        """Sequential appends must produce ids whose LEXICAL order == their CREATION order — the
        defining property of a ULID (its leading bits are a millisecond timestamp). A ~2 ms sleep
        between appends forces distinct millisecond timestamps, so a real ULID mint is STRICTLY
        increasing (deterministic pass); a ``uuid4``/random id has no temporal order, so 8 of them
        land pre-sorted with probability 1/8! ≈ 2.5e-5 — effectively a deterministic RED."""
        store, _env = audit_store_env
        ids: list[str] = []
        for index in range(8):
            record_id = await store.append(
                **_append_call_kwargs(target_row=f"{_TARGET_TABLE}:row_{index}", new_value={"n": index})
            )
            ids.append(_bare(record_id))
            await asyncio.sleep(0.002)  # force a distinct ms so ULID timestamps strictly increase
        assert ids == sorted(ids), (
            "the append ids are NOT creation-ordered — a ulid() sorts by creation time (Fork G), "
            f"a uuid4/random id does not. ids in creation order = {ids!r}"
        )
        assert all(earlier < later for earlier, later in itertools.pairwise(ids)), (
            f"append ids are not STRICTLY creation-ordered (a random-id build reds here): {ids!r}"
        )


# =========================================================================== #
# The composable TxnFragment forward-compat seam (Fork G) — 63/64 land [mutation, audit]
# ATOMICALLY in ONE BEGIN…COMMIT.
# =========================================================================== #


class TestTheComposableFragmentSeam:
    """⚠ FORWARD-COMPAT (get it right at 61): ``AuditStore.append`` must be composable into a
    CALLER's transaction so 63/64 land ``[governed_mutation, audit_append]`` in ONE
    ``execute_transaction`` — a partial apply is a mutation with no trail OR a trail with no
    mutation. Realized as a PUBLIC ``append_fragment(...) -> TxnFragment`` (the
    ``purge_file_fragment`` precedent), consumed by ``append`` AND by 63/64."""

    def test_append_fragment_returns_a_single_statement_create_fragment(
        self,
    ) -> None:
        """Fork G: ``append`` is a SINGLE-statement CREATE that COMPOSES (not a standalone
        ``.query()``). ``append_fragment`` returns a ``TxnFragment`` carrying exactly one
        statement — a ``CREATE`` into the audit table — and NO ``BEGIN``/``COMMIT`` of its own
        (so ``compose`` can add the envelope once)."""
        store = AuditStore(
            url="ws://127.0.0.1:18000/rpc", namespace="ns", database="db", user="root",
            password=_dummy_secret(),
        )
        fragment = store.append_fragment(**_append_call_kwargs(new_value={"n": 1}))
        assert isinstance(fragment, TxnFragment), "append_fragment must return a TxnFragment"
        assert len(list(fragment.statements)) == 1, (
            f"append is a SINGLE-statement CREATE (Fork G) — got {list(fragment.statements)!r}"
        )
        statement = fragment.statements[0]
        assert "CREATE" in statement.upper(), f"the append statement must be a CREATE: {statement!r}"
        assert AUDIT_TABLE in statement, f"the append CREATE must target the audit table: {statement!r}"
        assert "BEGIN" not in statement.upper() and "COMMIT" not in statement.upper(), (
            f"a fragment carries no transaction envelope (compose adds it once): {statement!r}"
        )

    def test_append_fragment_params_are_namespaced(self) -> None:
        """A fragment's params must be producer-namespaced (a common prefix) so the merged
        transaction never collides with a sibling producer's params (63/64's governed mutation
        fragment) — the ``TxnFragment`` contract (``TxnParamCollisionError``)."""
        store = AuditStore(
            url="ws://127.0.0.1:18000/rpc", namespace="ns", database="db", user="root",
            password=_dummy_secret(),
        )
        fragment = store.append_fragment(**_append_call_kwargs(new_value={"n": 1}))
        assert fragment.params, (
            "the append fragment binds no params — it interpolates values (injection risk)"
        )
        assert all(key.startswith("audit") for key in fragment.params), (
            f"the append fragment's params must be namespaced under an `audit`* prefix so a "
            f"co-composed governed mutation fragment cannot collide: {sorted(fragment.params)}"
        )

    async def test_append_fragment_composes_atomically_with_a_governed_mutation_POSITIVE(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        """POSITIVE CONTROL: the audit fragment composed with a co-producer's (stand-in
        governed) mutation fragment into ONE ``execute_transaction`` — BOTH land. This is the
        exact shape 63/64 use: ``compose(mutation_fragment, audit_store.append_fragment(...))``
        then ``execute_transaction``."""
        store, env = audit_store_env
        audit_fragment = store.append_fragment(**_append_call_kwargs(new_value={"n": 1}))
        governed_ok = TxnFragment(
            statements=["CREATE type::record('audit_compose_probe', $gp_id) CONTENT { v: $gp_v }"],
            params={"gp_id": "gp_ok", "gp_v": 7},
        )
        statement_text, merged_params = compose(governed_ok, audit_fragment)
        await execute_transaction(
            statement_text, merged_params,
            acquire=store._ensure_connection, drop=store._drop_connection, url=store._url,
        )
        # BOTH producers landed.
        assert await _count(env) == 1, "the audit append did not land inside the composed txn"
        connection = await connect_admin(env)
        try:
            governed_rows = await run(
                connection, "SELECT v FROM type::record('audit_compose_probe', 'gp_ok')"
            )
        finally:
            await connection.close()
        assert governed_rows and governed_rows[0]["v"] == 7, "the co-producer mutation did not land"

    async def test_a_failed_co_producer_ROLLS_BACK_the_audit_append_NEGATIVE(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        """⛔ THE ATOMICITY PIN: if the co-composed mutation is REJECTED, the audit append rolls
        back too — NEITHER lands (no trail-without-mutation, no mutation-without-trail). The
        stand-in rejected mutation is an illegal-action audit CREATE (the audit ASSERT fires
        reliably, no scratch DDL); it stands in for a rejected governed mutation. RED against a
        build whose ``append`` is a standalone ``.query()``/CREATE that cannot be rolled into a
        caller's txn."""
        store, env = audit_store_env
        before = await _count(env)
        audit_fragment = store.append_fragment(**_append_call_kwargs(new_value={"n": 1}))
        # A co-producer statement the engine REJECTS: an audit CREATE with an UNAUDITED action
        # ('READ') violates the action ASSERT and aborts the whole transaction. Params are in a
        # DISJOINT namespace ('bad_*') so compose does not collide.
        rejected_mutation = TxnFragment(
            statements=[
                f"CREATE type::record('{AUDIT_TABLE}', $bad_id) CONTENT {{ "
                f"actor_principal: type::record('principal', $bad_ap), "
                f"actor_agent: type::record('{AGENT_TABLE}', $bad_aa), "
                f"action: $bad_action, target_table: $bad_tt, target_row: $bad_tr }}"
            ],
            params={
                "bad_id": "bad_row", "bad_ap": _ACTOR_PRINCIPAL, "bad_aa": _ACTOR_AGENT,
                "bad_action": "READ", "bad_tt": _TARGET_TABLE, "bad_tr": _TARGET_ROW,
            },
        )
        statement_text, merged_params = compose(rejected_mutation, audit_fragment)
        with pytest.raises(SurrealStoreError):
            await execute_transaction(
                statement_text, merged_params,
                acquire=store._ensure_connection, drop=store._drop_connection, url=store._url,
            )
        assert await _count(env) == before, (
            "the audit append LANDED despite its co-composed mutation being rejected — the append "
            "is not truly composable into the caller's atomic transaction (Fork G forward-compat)"
        )

    def test_append_executes_via_the_verified_transaction_seam_not_a_lax_query(self) -> None:
        """Store §3 / Fork G: ``append`` must execute through ``compose`` + the VERIFIED
        ``execute_transaction`` seam (which checks EVERY statement), never a lax multi-statement
        ``.query()`` (which validates ``statement[0]`` only — a silent partial apply). AST: the
        ``append`` method references ``execute_transaction`` (directly or via ``append_fragment``
        + ``compose``) and does NOT hand a multi-statement string to ``.query()``."""
        source = Path(audit_module.__file__).read_text(encoding="utf-8")
        cls = next(
            n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ClassDef) and n.name == "AuditStore"
        )
        append = next(
            m for m in cls.body
            if isinstance(m, ast.AsyncFunctionDef | ast.FunctionDef) and m.name == "append"
        )
        called = {
            node.func.id
            for node in ast.walk(append)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        } | {
            node.func.attr
            for node in ast.walk(append)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert "execute_transaction" in called, (
            "AuditStore.append must execute through the verified execute_transaction seam (store "
            f"§3), never a lax .query(); calls seen in append: {sorted(called)}"
        )

    async def test_append_write_IS_the_composable_fragment_one_path(
        self, audit_store_env: tuple[AuditStore, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ ROUTING-IS-NOT-SHARING (adversary RESIDUAL): prove ``append()``'s write IS the
        composable fragment (ONE path) — not a separate non-composable write beside a fragment
        method (Build E: a ``append_fragment`` PLUS a bypassing ``append`` that hand-rolls its own
        CREATE). Capture the statement ``append`` hands to ``execute_transaction``; it must EQUAL
        ``compose(append_fragment(SAME args))``'s statement TEXT — identical because both bind the
        same ``$audit_*`` params (only the ulid VALUE differs, and values are bound, not
        interpolated). A build whose ``append`` writes via a separate path (a raw CREATE, different
        params, or a lax ``.query()``) produces a different statement and reds."""
        store, _env = audit_store_env
        captured: dict[str, Any] = {}

        async def _capture(statement: str, params: dict[str, Any], **_kwargs: object) -> None:
            captured["statement"] = statement

        monkeypatch.setattr(audit_module, "execute_transaction", _capture, raising=False)
        call_kwargs = _append_call_kwargs(new_value={"n": 1})
        await store.append(**call_kwargs)
        assert "statement" in captured, (
            "append did not execute through execute_transaction at all — it bypasses the composed "
            "fragment path (store §3 / routing-is-not-sharing)"
        )
        expected_statement, _params = compose(store.append_fragment(**call_kwargs))
        assert captured["statement"] == expected_statement, (
            "append's executed statement is NOT the composed append_fragment — append writes via a "
            "SEPARATE non-composable path (Build E: a fragment method PLUS a bypassing append). "
            f"append executed: {captured['statement']!r}  expected: {expected_statement!r}"
        )


# =========================================================================== #
# Born WRAPPED (#400 / Fork I) — append routes engine rejections through the ONE shared seam.
# =========================================================================== #


class TestAppendIsBornWrapped:
    """Fork I: ``AuditStore.append`` is the 9th consumer of the extracted engine-rejection
    seam, WRAPPED from BIRTH — it routes through ``loremaster.store._txn.wrap_store_rejection``
    (NOT a hand-rolled full-#400-idiom clone, which the LIVE w2 shape-guard
    ``test_engine_rejection_seam.py`` would flag on the new module). A raw ``SurrealStoreError``
    surfaces as ``AuditStoreError``; transport faults pass through untouched."""

    def test_append_routes_through_the_shared_wrap_seam(self) -> None:
        """ROUTED-SET pin (the w2 ``_methods_routing_through_seam`` idiom, scoped to
        ``AuditStore``): ``append`` references ``wrap_store_rejection``. Born-wrapped means it
        NEVER hand-rolls the ``try/except (Conn, Contention): raise; except SurrealStoreError:
        raise Domain from e`` idiom — which the w2 guard's full-idiom scan of every loremaster
        module (now including ``audit.py``) would otherwise red."""
        source = Path(audit_module.__file__).read_text(encoding="utf-8")
        cls = next(
            n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ClassDef) and n.name == "AuditStore"
        )
        append = next(
            m for m in cls.body
            if isinstance(m, ast.AsyncFunctionDef | ast.FunctionDef) and m.name == "append"
        )
        names = {node.id for node in ast.walk(append) if isinstance(node, ast.Name)}
        assert "wrap_store_rejection" in names, (
            "AuditStore.append must route engine rejections through _txn.wrap_store_rejection "
            "(Fork I — born wrapped, the 9th consumer), never a hand-rolled clone"
        )

    async def test_a_raw_store_error_surfaces_as_AuditStoreError(
        self, audit_store_env: tuple[AuditStore, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """FAULT INJECTION: when the engine seam raises a raw ``SurrealStoreError``, ``append``
        surfaces ``AuditStoreError`` — never the raw engine error (consumer law). Patching the
        ``audit``-module ``execute_transaction`` seam."""
        store, _env = audit_store_env

        async def _raise_store_error(*_args: object, **_kwargs: object) -> object:
            raise SurrealStoreError("injected engine rejection (audit)")

        monkeypatch.setattr(audit_module, "execute_transaction", _raise_store_error, raising=False)
        with pytest.raises(AuditStoreError):
            await store.append(**_append_call_kwargs(new_value={"n": 1}))

    @pytest.mark.parametrize("transport", ["connection", "contention"])
    async def test_transport_faults_propagate_untouched(
        self,
        audit_store_env: tuple[AuditStore, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
        transport: str,
    ) -> None:
        """PASS-THROUGH / DISCRIMINATOR (the w2 discriminator): a ``SurrealConnectionError``
        (transport) or ``TxnContentionExhaustedError`` (exhausted retry) — both SUBCLASS
        ``SurrealStoreError`` — must PROPAGATE untouched, NOT be masked as ``AuditStoreError``
        (store §3 — they belong to the retry/lifecycle layer). REDS only against a WRONG wrap: a
        naive ``except SurrealStoreError: raise AuditStoreError`` omitting the passthrough-FIRST
        re-raise. The discriminator the AuditStoreError pin cannot see."""
        store, _env = audit_store_env
        expected: type[SurrealStoreError]
        instance: SurrealStoreError
        if transport == "connection":
            expected = SurrealConnectionError
            instance = SurrealConnectionError("injected transport fault")
        else:
            expected = TxnContentionExhaustedError
            instance = TxnContentionExhaustedError(
                "injected exhausted contention", attempts=8, elapsed_seconds=1.0
            )

        async def _raise_transport(*_args: object, **_kwargs: object) -> object:
            raise instance

        monkeypatch.setattr(audit_module, "execute_transaction", _raise_transport, raising=False)
        with pytest.raises(expected):
            await store.append(**_append_call_kwargs(new_value={"n": 1}))

    async def test_a_REAL_engine_rejection_surfaces_as_AuditStoreError(
        self, audit_store_env: tuple[AuditStore, SurrealEnv]
    ) -> None:
        """BEHAVIOURAL (a REAL engine rejection, no injection): an append with an UNAUDITED
        action is refused by the store-side ASSERT — a raw ``SurrealStoreError`` ``append`` must
        WRAP as ``AuditStoreError`` (the born-wrapped end-to-end proof)."""
        store, _env = audit_store_env
        with pytest.raises(AuditStoreError):
            await store.append(**_append_call_kwargs(action="READ", new_value={"n": 1}))


def _dummy_secret() -> Any:
    """A ``SecretStr`` for the offline (never-connected) fragment-builder tests."""
    from pydantic import SecretStr

    return SecretStr("unused-offline")
