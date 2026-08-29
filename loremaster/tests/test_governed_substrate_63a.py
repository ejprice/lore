"""Contract — packet 63a: the SHARED GOVERNED SUBSTRATE seams (design §1.2 items 1–3) —
``resolve_subject`` / ``read_filter`` / ``guarded_write``. RED before the 63a build; authored by
``contract-63a`` (Opus 4.8 contract author — tests ONLY).

SPEC: ``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §1.2 (the six seams by SHAPE),
§1.3 riders R-a.2 (ONE ``Subject`` constructor) / R-a.3 (ONE splice), §6 item 7 (guarded-write
single-brain, no write on an excluded row). The seams are stubs (``NotImplementedError``) until
the builder wires them; every behavioural pin here is RED at HEAD by construction.

STORE LAW cited: §2 (record<> links; CONTENT), §3 (execute_transaction). Live TEST store
``ws://127.0.0.1:18000`` (NEVER :18500); per-test unique DB, reaped; NO skip marker.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    MEMORY_TABLE,
    FakeRegistry,
    access_token,
    admin,
    apply_ddl,
    build_principal_and_keep_stores,
    member,
    seed_memory_governed,
)
from _surreal_harness import (
    PRODUCTION_DIM,  # noqa: F401 - kept for parity; module uses a tiny dim
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.store import surreal_schema

import lorerunes as pdp
from loremaster import governed

_DIM = 8
_EMAIL_ALICE = "alice@example.com"


# =========================================================================== #
# resolve_subject (design §1.2 item 1) — fail-closed + the ONE Subject constructor.
# =========================================================================== #


@pytest_asyncio.fixture()
async def governed_world() -> Any:
    """A unified test DB carrying: a principal (alice, member) + a keep alice keeps + the
    ``memory`` table (governed DDL). ``resolve_subject``'s happy path resolves alice's principal
    (get_by_email), verifies her agent (fake registry), and reads her visible keeps."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    admin_conn = await connect_admin(env)
    await principal_store.create(email=_EMAIL_ALICE, role="member")
    keep = await keep_store.create_keep(keeper_email=_EMAIL_ALICE, type="project", name="lore")
    await apply_ddl(admin_conn, surreal_schema.generate_memory_ddl(dim=_DIM), url=env.url)
    try:
        yield principal_store, keep_store, admin_conn, env, keep
    finally:
        await admin_conn.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


class TestResolveSubjectIsFailClosed:
    """§1.2 item 1 — an absent/unverified capability, an unknown principal, or a keep-resolution
    failure → :class:`GovernedDenied` naming the missing step; NEVER an empty or partial Subject."""

    async def test_an_unverified_capability_denies(self, governed_world: Any) -> None:
        """⚠ RED at HEAD (``resolve_subject`` is a stub → NotImplementedError, not GovernedDenied).
        A capability the registry does NOT verify → the stamp fails-closed → GovernedDenied.
        REDDENS a build that returns a Subject (or an empty one) for an unverified capability."""
        principal_store, keep_store, _c, _e, _k = governed_world
        registry = FakeRegistry(verify_result=None)  # unverified
        with pytest.raises(governed.GovernedDenied):
            await governed.resolve_subject(
                access_token(subject=_EMAIL_ALICE),
                "cap:bogus",
                registry=registry,
                principal_store=principal_store,
                keep_store=keep_store,
            )

    async def test_an_unknown_principal_denies(self, governed_world: Any) -> None:
        """⚠ RED at HEAD. The capability verifies, but ``access_token.subject`` names a principal
        that does not exist (``get_by_email`` → None) → GovernedDenied. REDDENS a build that
        constructs a Subject with an empty/guessed principal_id (SEC-F3)."""
        principal_store, keep_store, _c, _e, _k = governed_world
        registry = FakeRegistry(verify_result=("ag_ghost", "principal:ghost"))
        with pytest.raises(governed.GovernedDenied):
            await governed.resolve_subject(
                access_token(subject="nobody@example.com"),
                "cap:verified",
                registry=registry,
                principal_store=principal_store,
                keep_store=keep_store,
            )

    async def test_a_keep_resolution_failure_denies(self, governed_world: Any) -> None:
        """⚠ RED at HEAD. If the keep resolver raises (a wrong-instance/dead store), the subject
        must fail-closed (GovernedDenied), NEVER be built with a SHORTER keep set (which would
        under- or, worse, MIS-authorize). REDDENS a build that swallows the resolver error."""
        principal_store, _keep_store, _c, _e, _k = governed_world
        registry = FakeRegistry(verify_result=("ag_a1", "principal:alice"))

        class _BrokenKeepStore:
            async def list_keeps_for_member(self, *, member_email: str) -> list[str]:
                from loremaster.keeps import KeepStoreError

                raise KeepStoreError("keep store unreachable (wrong-instance / dead)")

        with pytest.raises((governed.GovernedDenied, Exception)):  # noqa: B017,PT011 - see below
            subject = await governed.resolve_subject(
                access_token(subject=_EMAIL_ALICE),
                "cap:verified",
                registry=registry,
                principal_store=principal_store,
                keep_store=_BrokenKeepStore(),
            )
            # If it did NOT raise, it must at least not have swallowed the failure into a subject.
            assert subject is None, "resolve_subject must fail-closed on a keep-resolution failure"

    async def test_the_happy_path_builds_a_correct_subject(self, governed_world: Any) -> None:
        """⚠ RED at HEAD. A verified capability + a known member principal + resolvable keeps →
        a :class:`lorerunes.Subject` carrying THIS principal, THIS agent, role member, and the
        keep scopes alice is householded in. REDDENS a build that mis-wires any field (the field
        order is principal_id, agent_id, role, keeps — survey-63a-pdp)."""
        # ⚠ A REAL registry + a REAL minted capability (NOT a FakeRegistry) — so this happy-path is
        # ROBUST to #425's resolution (FORK 3): resolve_subject → the REAL stamp_owner → the real
        # registry works whether verify_capability's return changes or a sibling pair-path is added.
        # (The fail-closed pins keep FakeRegistry — the deny path is form-agnostic.)
        from loremaster.agents import AgentRegistry

        principal_store, keep_store, _c, env, keep = governed_world
        alice = await principal_store.get_by_email(_EMAIL_ALICE)
        assert alice is not None
        registry = AgentRegistry(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        try:
            await registry.ensure_ready()
            result = await registry.register(
                "alice_worker", session="s1", role="worker", owner_principal_id=_bare(alice.id)
            )
            capability = getattr(result, "capability", None)
            assert capability, "capability mint unbuilt (62 wave 2)"
            subject = await governed.resolve_subject(
                access_token(subject=_EMAIL_ALICE),
                capability,
                registry=registry,
                principal_store=principal_store,
                keep_store=keep_store,
            )
        finally:
            await registry.close()
        assert subject.role == pdp.PRINCIPAL_ROLE_MEMBER
        assert subject.agent_id == result.agent.id
        assert subject.principal_id == _bare(alice.id)
        assert pdp.keep_scope(_bare(keep.id)) in subject.visible_keep_ids, (
            f"the subject must see alice's keep {keep.id} in visible_keep_ids, got {subject.visible_keep_ids}"
        )


class TestResolveSubjectIsTheOneSubjectConstructor:
    """R-a.2 — ``Subject(`` is constructed in PRODUCTION code ONLY inside ``resolve_subject``
    (test/oracle fixtures are exempt by tree). Structural pin: an AST scan over the shipped
    ``loremaster`` package. RED at HEAD (the stub constructs none → ZERO production constructors);
    GREEN once ``resolve_subject`` is the ONE; REDDENS a second constructor added anywhere else."""

    def test_exactly_one_production_subject_constructor_and_it_is_in_resolve_subject(self) -> None:
        sites = _subject_construction_sites()
        assert len(sites) == 1, (
            f"expected EXACTLY ONE production Subject(...) constructor (in governed.resolve_subject); "
            f"found {len(sites)}: {sites!r}. Zero ⇒ resolve_subject unbuilt (RED at HEAD); >1 ⇒ a "
            f"second constructor forks the identity-resolution path (R-a.2 — allowlist the ONE site)."
        )
        file_path, _lineno = sites[0]
        assert file_path.name == "governed.py", (
            f"the sole production Subject constructor must live in governed.py (resolve_subject), "
            f"not {file_path}"
        )


# =========================================================================== #
# read_filter (design §1.2 item 2) — the ONE splice over authorize_filter(READ).to_surql().
# =========================================================================== #


class TestReadFilterIsTheOneSplice:
    """R-a.3 — ``read_filter(subject, table)`` is a THIN wrapper that returns exactly
    ``authorize_filter(subject, Action.READ, table).to_surql()``. Pinned by DELEGATION (byte
    equality): a hand-rolled fragment would DIFFER → RED. RED at HEAD (NotImplementedError)."""

    @pytest.mark.parametrize(
        "subject_label",
        ["member/no-keeps", "member/2-keeps", "admin"],
    )
    def test_read_filter_equals_authorize_filter_read(self, subject_label: str) -> None:
        """⚠ RED at HEAD. ``read_filter`` MUST return the SAME (fragment, params) as
        ``authorize_filter(subject, READ, table).to_surql()`` — the ONE splice, not a private
        copy. Includes a ≥2-keep subject (the #413 expansion) and admin (AllRows='true')."""
        subject = _subject_for(subject_label)
        expected = pdp.authorize_filter(subject, pdp.Action.READ, MEMORY_TABLE).to_surql()
        got = governed.read_filter(subject, MEMORY_TABLE)
        assert got == expected, (
            f"read_filter({subject_label}) diverged from authorize_filter(READ).to_surql() — a "
            f"read that stays green under a to_surql change is a private copy (R-a.3). "
            f"got={got!r} expected={expected!r}"
        )


# =========================================================================== #
# guarded_write (design §1.2 item 3) — single-brain on writes: no write on an excluded row;
# GovernedConflict on a 0-row guarded mutation; audit compose on an admin bypass.
# =========================================================================== #


class TestGuardedWriteIsSingleBrainOnWrites:
    """§1.2 item 3 / §6 item 7 — the Python gate and the store guard are the SAME tree evaluated
    twice, so a write CANNOT land on a row the filter excludes; a 0-row guarded mutation is a LOUD
    :class:`GovernedConflict`, never a silent no-op."""

    async def test_a_member_write_on_a_foreign_owned_row_denies_and_does_not_mutate(
        self, governed_world: Any
    ) -> None:
        """⚠ RED at HEAD. bob writes a row OWNED BY ALICE (agent-private): ``authorize`` DENIES →
        GovernedDenied, AND the row is UNCHANGED (single-brain on writes — a denied write never
        touches the store). REDDENS a build that mutates before/without the gate."""
        _p, _k, connection, _env, _keep = governed_world
        await seed_memory_governed(
            connection, row_id="alice_row", dim=_DIM, owner_principal="alice", owner_agent="ag_a1",
            scope="agent-private", note_text="original",
        )
        bob = member("bob", "ag_b1", frozenset())
        with pytest.raises(governed.GovernedDenied):
            await governed.guarded_write(
                bob, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="alice_row",
                set_fragment="note_text = 'hijacked'", audit=None,
            )
        row = _one(await run(connection, "SELECT note_text FROM type::record('memory', 'alice_row')"))
        assert row["note_text"] == "original", (
            "a DENIED guarded_write mutated the row — the store guard must exclude it (single-brain)"
        )

    async def test_a_member_write_on_its_own_row_succeeds(self, governed_world: Any) -> None:
        """⚠ RED at HEAD. alice/ag_a1 writes her OWN agent-private row → GuardedWriteResult with
        ``row_count == 1`` and the column IS updated. The positive control for the deny pin."""
        _p, _k, connection, _env, _keep = governed_world
        await seed_memory_governed(
            connection, row_id="own_row", dim=_DIM, owner_principal="alice", owner_agent="ag_a1",
            scope="agent-private", note_text="original",
        )
        alice = member("alice", "ag_a1", frozenset())
        result = await governed.guarded_write(
            alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="own_row",
            set_fragment="note_text = 'updated'", audit=None,
        )
        assert result.row_count == 1, f"the guarded write must report 1 row, got {result!r}"
        row = _one(await run(connection, "SELECT note_text FROM type::record('memory', 'own_row')"))
        assert row["note_text"] == "updated"

    async def test_a_guarded_write_on_a_vanished_row_raises_conflict(self, governed_world: Any) -> None:
        """⚠ RED at HEAD. GovernedConflict is the 0-row signal: a guarded mutation whose WHERE
        (id AND authorize_filter) matches ZERO rows is a LOUD conflict, never a silent no-op. Here
        the row_id names a row that does not exist → the guard matches 0. (The full TOCTOU race —
        a re-scope landing between the read and the write — is the security-auditor's §6-item-7
        construction; this pins the 0-row → conflict contract deterministically.) REDDENS a build
        that returns a 0-count result silently."""
        _p, _k, _connection, _env, _keep = governed_world
        alice = member("alice", "ag_a1", frozenset())
        with pytest.raises(governed.GovernedConflict):
            await governed.guarded_write(
                alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="does_not_exist",
                set_fragment="note_text = 'x'", audit=None,
            )


class TestGuardedWriteComposesAudit:
    """§1.2 item 3 — an admin BYPASS write (a mutation a member could not make) is AUDITED: the
    ``requires_audit`` flag composes ``AuditStore.append_fragment`` into the SAME transaction (61a
    built it *"for what 63/64 compose"*)."""

    async def test_an_admin_bypass_write_appends_an_audit_row(self, governed_world: Any) -> None:
        """⚠ RED at HEAD. An admin writes a row owned by a DIFFERENT principal (a bypass a member
        could not do) → the write lands AND an ``audit`` row is appended in the same txn. REDDENS a
        build that mutates without auditing the bypass (the erasable-trail hazard)."""
        _p, _k, connection, env, _keep = governed_world
        audit_store = _build_audit_store(env)
        await audit_store.ensure_ready()
        try:
            await seed_memory_governed(
                connection, row_id="bypass_row", dim=_DIM, owner_principal="bob", owner_agent="ag_b1",
                scope="agent-private", note_text="original",
            )
            before = _count(await run(connection, "SELECT count() FROM audit GROUP ALL"))
            await governed.guarded_write(
                admin("alice", "ag_a1"), pdp.Action.WRITE, table=MEMORY_TABLE, row_id="bypass_row",
                set_fragment="note_text = 'admin-touched'", audit=audit_store,
            )
            after = _count(await run(connection, "SELECT count() FROM audit GROUP ALL"))
            assert after == before + 1, (
                f"an admin bypass write must append exactly one audit row, before={before} after={after}"
            )
        finally:
            await audit_store.close()


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _one(rows: Any) -> Any:
    assert rows, f"expected one row, got {rows!r}"
    return rows[0]


def _count(rows: Any) -> int:
    return rows[0]["count"] if rows else 0


def _bare(record_id: str) -> str:
    return record_id.partition(":")[2] or record_id


def _subject_for(label: str) -> Any:
    if label == "member/no-keeps":
        return member("alice", "ag_a1", frozenset())
    if label == "member/2-keeps":
        return member("alice", "ag_a1", frozenset({pdp.keep_scope("k1"), pdp.keep_scope("k9")}))
    if label == "admin":
        return admin("alice", "ag_a1")
    raise KeyError(label)


def _build_audit_store(env: Any) -> Any:
    from loremaster.audit import AuditStore
    from pydantic import SecretStr

    password = env.password if isinstance(env.password, SecretStr) else SecretStr(str(env.password))
    return AuditStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=password
    )


def _subject_construction_sites() -> list[tuple[Path, int]]:
    """Every PRODUCTION ``Subject(...)`` construction site in the shipped ``loremaster`` package
    (tests excluded by tree). A call whose func is ``Subject`` or ``*.Subject``. R-a.2 allowlists
    the ONE (governed.resolve_subject)."""
    package_root = Path(inspect.getsourcefile(governed) or "").parent  # loremaster/loremaster/
    sites: list[tuple[Path, int]] = []
    for path in sorted(package_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                is_subject = (isinstance(func, ast.Name) and func.id == "Subject") or (
                    isinstance(func, ast.Attribute) and func.attr == "Subject"
                )
                if is_subject:
                    sites.append((path, node.lineno))
    return sites
