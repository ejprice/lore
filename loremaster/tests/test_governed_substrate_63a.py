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
    build_memory_backend,
    build_principal_and_keep_stores,
    governed_overlay_ddl,
    member,
    seed_memory_governed,
    store_handle,
)
from _sdk_guard import SAFE_CONNECTION_METHODS, SDK_CONNECTION_CLASSES
from _surreal_harness import (
    PRODUCTION_DIM,  # noqa: F401 - kept for parity; module uses a tiny dim
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.store import surreal_schema
from loremaster.store._txn import StoreHandle

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
    (get_by_email), verifies her agent (fake registry), and reads her visible keeps.

    ⚠ The §4.1 governed overlay is applied HAND-TRANSCRIBED (``governed_overlay_ddl``, decoupled
    from the emitter — the schema module owns the emitter, per the retrofit ``oracle_conn`` idiom),
    so the guarded_write pins seed governed rows and RED on the SUBSTRATE seam (``guarded_write``
    NotImplementedError), NOT on the schema emitter's absence. Without it every guarded_write pin
    would red at the SEED (``no such field 'owner_agent'``) at HEAD, masking the precise RED. On a
    GREEN build ``generate_memory_ddl`` ALSO emits these columns (OVERWRITE/IF-NOT-EXISTS ⇒ a safe
    idempotent double-apply)."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    admin_conn = await connect_admin(env)
    await principal_store.create(email=_EMAIL_ALICE, role="member")
    keep = await keep_store.create_keep(keeper_email=_EMAIL_ALICE, type="project", name="lore")
    await apply_ddl(admin_conn, surreal_schema.generate_memory_ddl(dim=_DIM), url=env.url)
    await apply_ddl(admin_conn, governed_overlay_ddl(MEMORY_TABLE), url=env.url)
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
    """§1.2 item 3 / §6 item 7 / §10.6 — the Python gate and the store guard are the SAME tree
    evaluated twice, so a write CANNOT land on a row the filter excludes; a 0-row guarded mutation
    is a LOUD :class:`GovernedConflict`, never a silent no-op. Every call reaches the store through
    an injected :class:`~loremaster.store._txn.StoreHandle` (§10.6): a build that BYPASSES the
    handle for any statement observes 0 acquires and reds the counting leg (rider iv)."""

    async def test_a_member_write_on_a_foreign_owned_row_denies_and_does_not_mutate(
        self, governed_world: Any
    ) -> None:
        """⚠ RED at HEAD. bob writes a row OWNED BY ALICE (agent-private): ``authorize`` DENIES →
        GovernedDenied, AND the row is UNCHANGED (single-brain on writes — a denied write never
        touches the store). The gate must have READ the row (its owner drives the verdict) → at
        least ONE acquire through the injected handle (rider iv). REDDENS a build that mutates
        before/without the gate, and a build that reaches the store off the handle."""
        _p, _k, connection, env, _keep = governed_world
        handle, calls = store_handle(connection, url=env.url)
        await seed_memory_governed(
            connection, row_id="alice_row", dim=_DIM, owner_principal="alice", owner_agent="ag_a1",
            scope="agent-private", note_text="original",
        )
        bob = member("bob", "ag_b1", frozenset())
        with pytest.raises(governed.GovernedDenied):
            await governed.guarded_write(
                bob, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="alice_row",
                set_fragment="note_text = 'hijacked'", audit=None, store=handle,
            )
        row = _one(await run(connection, "SELECT note_text FROM type::record('memory', 'alice_row')"))
        assert row["note_text"] == "original", (
            "a DENIED guarded_write mutated the row — the store guard must exclude it (single-brain)"
        )
        assert calls["acquire"] >= 1, (
            "guarded_write denied WITHOUT reading the row through the injected handle — the deny "
            "must follow a handle-routed pre-read of the row's owner (§10.6 rider iv)"
        )

    async def test_a_member_write_on_its_own_row_succeeds(self, governed_world: Any) -> None:
        """⚠ RED at HEAD. alice/ag_a1 writes her OWN agent-private row → GuardedWriteResult with
        ``row_count == 1`` (read BACK from the guarded statement's RETURN, the messages.py ack-CAS
        precedent) and the column IS updated. The positive control for the deny pin. ≥1 acquire
        through the injected handle (rider iv)."""
        _p, _k, connection, env, _keep = governed_world
        handle, calls = store_handle(connection, url=env.url)
        await seed_memory_governed(
            connection, row_id="own_row", dim=_DIM, owner_principal="alice", owner_agent="ag_a1",
            scope="agent-private", note_text="original",
        )
        alice = member("alice", "ag_a1", frozenset())
        result = await governed.guarded_write(
            alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="own_row",
            set_fragment="note_text = 'updated'", audit=None, store=handle,
        )
        assert result.row_count == 1, f"the guarded write must report 1 row, got {result!r}"
        row = _one(await run(connection, "SELECT note_text FROM type::record('memory', 'own_row')"))
        assert row["note_text"] == "updated"
        assert calls["acquire"] >= 1, "the guarded write reached the store off the injected handle (rider iv)"

    async def test_a_guarded_write_on_a_vanished_row_raises_conflict(self, governed_world: Any) -> None:
        """⚠ RED at HEAD. §10.6 rider (i) — the vanished-conflict pin with a POSITIVE CONTROL in the
        SAME test, so a no-handle / dead-seam build cannot pass it (it fails leg one).

        Leg 1 (positive control): alice's guarded write on her EXISTING row returns
        ``row_count == 1`` READ BACK from the guarded statement's RETURN (the ACTUAL stamp, never a
        pre-read count). Leg 2: the row is DELETED, then the IDENTICAL call's guarded mutation
        (WHERE ``id`` AND ``authorize_filter``) matches ZERO rows → a LOUD :class:`GovernedConflict`,
        never a silent 0-count result. A build that could not reach the store at all (no handle,
        dead seam) reds leg one — the old form FALSE-PASSED because a no-store call raised
        GovernedConflict byte-identically to a real 0-row conflict (adversary-63a-2 R6/§P2)."""
        _p, _k, connection, env, _keep = governed_world
        handle, calls = store_handle(connection, url=env.url)
        await seed_memory_governed(
            connection, row_id="vanishing_row", dim=_DIM, owner_principal="alice", owner_agent="ag_a1",
            scope="agent-private", note_text="original",
        )
        alice = member("alice", "ag_a1", frozenset())
        # Leg 1 — POSITIVE CONTROL: the row is really there and the guarded write really lands.
        first = await governed.guarded_write(
            alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="vanishing_row",
            set_fragment="note_text = 'still here'", audit=None, store=handle,
        )
        assert first.row_count == 1, (
            f"leg 1 (positive control) — the guarded write on the EXISTING row must report 1 row "
            f"from its RETURN; a build that cannot reach the store fails HERE, so a raised "
            f"GovernedConflict in leg 2 can no longer false-pass. got {first!r}"
        )
        assert calls["acquire"] >= 1, "leg 1 reached the store off the injected handle (rider iv)"
        # Leg 2 — the row VANISHES, the identical call now matches ZERO rows → LOUD conflict.
        await run(connection, "DELETE type::record('memory', 'vanishing_row')")
        with pytest.raises(governed.GovernedConflict):
            await governed.guarded_write(
                alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="vanishing_row",
                set_fragment="note_text = 'x'", audit=None, store=handle,
            )

    async def test_a_rescope_between_the_read_and_the_write_raises_conflict(
        self, governed_world: Any
    ) -> None:
        """⚠ RED at HEAD. §10.6 rider (iii) — the TOCTOU leg, using the injected handle AS THE
        INSTRUMENT (deterministic, no 8-way race). alice owns an agent-private row; a re-scope
        ``UPDATE`` (moving the row to bob's agent) is landed on acquire #2 — BETWEEN guarded_write's
        pre-read (run_query = acquire #1, where alice still owns it → authorize allows) and its
        guarded mutation (execute_transaction = acquire #2). The guarded mutation's WHERE
        (``authorize_filter`` for alice WRITE) now excludes the moved row → ZERO rows →
        :class:`GovernedConflict`, and alice's intended ``note_text`` write NEVER lands (the row is
        untouched but for the injected re-scope). REDDENS a build that reads-then-writes with a
        TOCTOU window on the governed columns (it would write on the moved row)."""
        _p, _k, connection, env, _keep = governed_world
        await seed_memory_governed(
            connection, row_id="toctou_row", dim=_DIM, owner_principal="alice", owner_agent="ag_a1",
            scope="agent-private", note_text="original",
        )
        alice = member("alice", "ag_a1", frozenset())

        async def _rescope_on_second_acquire(acquire_number: int) -> None:
            # The mutation's acquire (design §10.6: pre-read=run_query #1, mutation=execute_transaction
            # #2). Re-scope the row OUT of alice's WRITE reach (idempotent SET), landing strictly
            # between the pre-read and the guarded mutation.
            if acquire_number == 2:
                await run(
                    connection,
                    "UPDATE type::record('memory', 'toctou_row') "
                    "SET owner_agent = type::record('agent', 'ag_b1')",
                )

        handle, _calls = store_handle(connection, url=env.url, on_acquire=_rescope_on_second_acquire)
        with pytest.raises(governed.GovernedConflict):
            await governed.guarded_write(
                alice, pdp.Action.WRITE, table=MEMORY_TABLE, row_id="toctou_row",
                set_fragment="note_text = 'won the race'", audit=None, store=handle,
            )
        row = _one(await run(connection, "SELECT note_text FROM type::record('memory', 'toctou_row')"))
        assert row["note_text"] == "original", (
            "guarded_write wrote on a row a re-scope moved out from under it — the store guard must "
            "re-evaluate ownership in the SAME statement (no read-then-write TOCTOU window, §10.6)"
        )


class TestGuardedWriteComposesAudit:
    """§1.2 item 3 / §10.6 rider (ii) — an admin BYPASS write (a mutation a member could not make)
    is AUDITED: the ``requires_audit`` flag composes ``AuditStore.append_fragment`` into the SAME
    transaction (61a built it *"for what 63/64 compose"*). BOTH legs prove the audit RIDES the same
    txn: a landed bypass appends exactly +1, and a REJECTED mutation appends ZERO."""

    async def test_an_admin_bypass_write_appends_an_audit_row(self, governed_world: Any) -> None:
        """⚠ RED at HEAD. §10.6 rider (ii) leg A. An admin writes a row owned by a DIFFERENT
        principal (a bypass a member could not do) → the write lands AND exactly ONE ``audit`` row
        is appended in the same txn. ≥1 acquire through the injected handle (rider iv). REDDENS a
        build that mutates without auditing the bypass (the erasable-trail hazard)."""
        _p, _k, connection, env, _keep = governed_world
        handle, calls = store_handle(connection, url=env.url)
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
                set_fragment="note_text = 'admin-touched'", audit=audit_store, store=handle,
            )
            after = _count(await run(connection, "SELECT count() FROM audit GROUP ALL"))
            assert after == before + 1, (
                f"an admin bypass write must append exactly one audit row, before={before} after={after}"
            )
            assert calls["acquire"] >= 1, "the audited bypass reached the store off the handle (rider iv)"
        finally:
            await audit_store.close()

    async def test_a_rejected_mutation_appends_no_audit_row(self, governed_world: Any) -> None:
        """⚠ RED at HEAD. §10.6 rider (ii) leg B — audit atomicity from the OTHER side. An admin
        bypass whose ``set_fragment`` VIOLATES the schema (``embedding`` is ``array<float>`` on the
        SCHEMAFULL memory table — a string coerces-fail) is REJECTED by the engine → the whole
        composed ``BEGIN … COMMIT`` rolls back → ZERO audit rows are appended (``before == after``).
        This PROVES the audit rides the SAME transaction, not a second round-trip. REDDENS a build
        that appends the audit in a SEPARATE round-trip BEFORE the mutation (the audit would survive
        the rolled-back mutation — a landed audit for a write that never happened, and the mirror of
        the §9 'compromised admin erases its trail' shape)."""
        _p, _k, connection, env, _keep = governed_world
        handle, _calls = store_handle(connection, url=env.url)
        audit_store = _build_audit_store(env)
        await audit_store.ensure_ready()
        try:
            await seed_memory_governed(
                connection, row_id="reject_row", dim=_DIM, owner_principal="bob", owner_agent="ag_b1",
                scope="agent-private", note_text="original",
            )
            before = _count(await run(connection, "SELECT count() FROM audit GROUP ALL"))
            with pytest.raises(Exception) as rejection:  # noqa: B017,PT011 - a store domain rejection
                await governed.guarded_write(
                    admin("alice", "ag_a1"), pdp.Action.WRITE, table=MEMORY_TABLE, row_id="reject_row",
                    set_fragment="embedding = 'not-a-float-array'", audit=audit_store, store=handle,
                )
            # ⚠ FIXTURES-MUST-DISCRIMINATE: the unbuilt stub raises NotImplementedError, which a bare
            # ``pytest.raises(Exception)`` would swallow — leaving ``before == after`` TRUE trivially
            # (guarded_write never ran). Require the raise to be a real STORE rejection, so this pin is
            # RED-until-built and only GREEN once guarded_write actually composes the rejected mutation.
            assert not isinstance(rejection.value, NotImplementedError), (
                "guarded_write is unbuilt (NotImplementedError) — the audit-atomicity ZERO leg is "
                "RED-until-built (§10.6 rider ii); it does not pass by the store never being reached"
            )
            after = _count(await run(connection, "SELECT count() FROM audit GROUP ALL"))
            assert after == before, (
                f"a REJECTED guarded mutation appended an audit row (before={before} after={after}) — "
                f"the audit did NOT ride the mutation's transaction (§10.6 rider ii: it must roll back "
                f"WITH the rejected mutation, not land in a separate round-trip)"
            )
        finally:
            await audit_store.close()


# =========================================================================== #
# §10.6 R4 — the whole governed substrate reaches the store through the injected driver, never a
# raw connection. Two instruments: the AUTOUSE runtime _sdk_guard (conftest) watches EXECUTED
# paths absolutely (any connection.query off the driver reds, in the pins above); this AST pin
# covers ALL of governed.py's code weakly (even branches no test runs), so a hand-rolled SDK call
# in a non-executed path is still caught. Together: the runtime guard for executed code, the AST
# lint for all code — the seam between them is the reach law's own posture (_sdk_guard docstring).
# =========================================================================== #


def _governed_source_tree() -> ast.Module:
    """The AST of the shipped ``loremaster/governed.py`` (the substrate's ONLY home for
    resolve_subject / read_filter / guarded_write / report_unmigrated_governed_rows)."""
    source_path = Path(inspect.getsourcefile(governed) or "")
    return ast.parse(source_path.read_text(encoding="utf-8"))


def _sdk_attribute_call_sites(tree: ast.Module) -> list[str]:
    """Every ``<recv>.<method>(...)`` call in ``tree`` whose ``method`` is a PUBLIC coroutine of a
    real SurrealDB connection class — DERIVED from the SDK classes (reach law #344/#345), never a
    hand-list, so a renamed/added SDK method is caught without editing this test. ``SAFE_CONNECTION_
    METHODS`` (signin/close — the deny-by-default safe set) are exempt."""
    sdk_methods = {
        name
        for connection_class in SDK_CONNECTION_CLASSES
        for name, function in inspect.getmembers(connection_class, inspect.isfunction)
        if not name.startswith("_") and name not in SAFE_CONNECTION_METHODS
    }
    return [
        f"{node.func.attr}() at governed.py:{node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in sdk_methods
    ]


class TestGovernedRoutesAllSdkThroughTheDriver:
    """§10.6 R4 — production code in ``governed.py`` issues NO direct SDK call: it takes a
    :class:`~loremaster.store._txn.StoreHandle` (acquire/drop/url callables, never a connection
    object) and routes every store access through ``run_query`` / ``execute_transaction``. Pin: an
    AST scan over ``governed.py``. This guards ``guarded_write`` AND
    ``report_unmigrated_governed_rows`` (the R4 targets) plus ``resolve_subject`` / ``read_filter``."""

    def test_governed_py_has_no_direct_sdk_call_site(self) -> None:
        """§10.6 R4. GREEN at HEAD (the stubs raise ``NotImplementedError`` — no SDK) and on the
        correct build (all store access via the driver seams); REDDENS a build that hand-rolls a
        ``connection.query(...)`` / ``.query_raw(...)`` / any SDK connection method inside
        ``governed.py``, and a build that imports the ``surrealdb`` SDK there (to construct a
        connection). Paired with a POSITIVE CONTROL so it is not a scanner that can see nothing."""
        tree = _governed_source_tree()

        # (a) no direct ``surrealdb`` import — with a connection object in hand, governed.py could
        #     bypass the driver; the design gives it a StoreHandle (callables) precisely so it holds
        #     no connection to call.
        sdk_imports = [
            node.lineno
            for node in ast.walk(tree)
            if (isinstance(node, ast.Import) and any(a.name.split(".")[0] == "surrealdb" for a in node.names))
            or (isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "surrealdb")
        ]
        assert not sdk_imports, (
            f"governed.py imports the surrealdb SDK directly (lines {sdk_imports}) — R4: the substrate "
            f"takes a StoreHandle and routes through loremaster.store._txn, it constructs no connection"
        )

        # (b) no SDK connection-method call (derived from the SDK classes, reach law #344/#345).
        escapes = _sdk_attribute_call_sites(tree)
        assert not escapes, (
            f"governed.py contains a direct SDK connection call — R4: every store access must route "
            f"through run_query/execute_transaction over the injected StoreHandle, never a raw "
            f"connection: {escapes}"
        )

    def test_the_sdk_call_site_scanner_is_not_blind(self) -> None:
        """POSITIVE CONTROL (a probe needs a control): the scanner FLAGS a known-bad synthetic
        source (a ``connection.query_raw(...)`` call) — so the GREEN above is cleanliness, not
        blindness. WITHOUT this, a scanner keyed on a mis-derived (empty) method set would pass the
        pin above vacuously."""
        bad = ast.parse(
            "async def leak(store):\n"
            "    connection = await store.acquire()\n"
            "    return await connection.query_raw('SELECT 1')\n"
        )
        flagged = _sdk_attribute_call_sites(bad)
        assert any("query_raw" in site for site in flagged), (
            f"the SDK call-site scanner did not flag a synthetic connection.query_raw(...) — it is "
            f"blind, so its clean verdict on governed.py is worth nothing. flagged={flagged!r}"
        )


class TestAGovernedStoreExposesAHandleAccessor:
    """§10.6 rider (v) / DRY — every governed store exposes its driver triple through ONE accessor
    (``LocalMemoryBackend.handle``), so a composed guarded write borrows the owner's real
    retry/self-heal lifecycle rather than cloning a connection. 64's ledgers expose the same."""

    async def test_the_backend_handle_is_a_storehandle_wired_to_its_own_url(
        self, governed_world: Any
    ) -> None:
        """⚠ RED at HEAD (``LocalMemoryBackend.handle`` raises ``NotImplementedError`` — stub). The
        accessor returns a :class:`StoreHandle` whose ``url`` is the backend's own RPC url (the
        SAME driver ``_query`` uses), so the retrofit invalidate route reaches the backend's store
        through it. REDDENS a build with no accessor, or one that fabricates a foreign handle."""
        _p, _k, _connection, env, _keep = governed_world
        backend = await build_memory_backend(env)
        try:
            handle = backend.handle
            assert isinstance(handle, StoreHandle), (
                f"LocalMemoryBackend.handle must return a store._txn.StoreHandle (§10.6), got {handle!r}"
            )
            assert handle.url == env.url, (
                f"the backend's handle must carry the backend's OWN url {env.url!r} (its real driver), "
                f"got {handle.url!r} — a foreign handle would guard-write against the wrong store"
            )
        finally:
            await backend.close()


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
