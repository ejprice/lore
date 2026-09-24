"""Contract — packet 63c wave i-a: the AGENT DATA layer's behavioural pins (register STAMPS, the
Q5 scope-keyed migrate + its ROW precondition, and the DD-3.c dirty-store legs). Authored by
``contract-63c-i`` (Opus 4.8 contract author — CONTRACT TESTS ONLY, no production code).

THE SPEC IS THE RULING: ``docs/design/2026-09-13-packet63c-remainder-ruling.md`` — §2.2 (register
stamps ``owner_principal``/``owner_agent=self``/``scope=keep:<session keep>``), §4.4 (the two-leg
DD-3.c shape + the heartbeat leg + P-A3), §6 (the agent migrate: ONE 3-column scope-keyed statement +
the §2.1 ROW-level precondition that F10 found UNIMPLEMENTED — finding #470). The lead RULED
Option 2 (63c-i split into i-a DATA + i-b serving/security); this file is i-a. EXCLUDED here (→ i-b):
the #467 dispatcher, ``read_filter`` ∀-readers, EXPLAIN-A, Q2 β + the corpse, the flips, P5.

WHY ONE FILE for all the agent DD-3.c legs (a deviation from the message precedent's schema/migrate
split, ``test_comms_schema.py`` Leg A + ``test_message_migrate_dirty_store_63b_ii_b.py`` Leg B):
every agent dirty-store leg shares the SAME seeders (``seed_agent_legacy``), the SAME frozen/unbounded
agent DDL, and the SAME live-store idiom — keeping the DD-3.c reasoning in one place is clearer than
sprinkling live tests across ``test_comms_schema.py``. The seeders themselves live in the ONE F5 home
``_governed_contract.py`` (ONE IMPLEMENTATION), so no idiom is cloned.

STORE LAW (``docs/reference/surrealdb-31-capabilities.md`` — cited, never re-transcribed): §1.1
(FIELD OVERWRITE / INDEX IF NOT EXISTS), §1.2 (OVERWRITE = FULL REPLACE drops a stored ASSERT — the
drop-lands mechanism Leg A proves), §1.4 (option<> on a POPULATED table; a migration converges the
SCHEMA never the DATA — over-cap/hostile values survive byte-intact), §2 (CONTENT for the protected
``session`` name; ``SELECT`` explicit projection reads NONE for an unset/absent column), §3
(execute_transaction — statement[0]-only; a whole-statement UPDATE aborts atomically on one ASSERT
violation, stamping NOTHING).

RED-AT-HEAD (measured @699a6e9): agent carries NO ``owner_agent``/``scope`` column and NO register
stamp of them; ``generate_agent_ddl()`` STILL emits the name/session charset + role non-empty ASSERTs
(so the DROP has not landed and a legacy ``touch`` on a ``role=""`` row is refused); and
``_migrate_agent_owner`` is OWNER-keyed with NO row-level precondition (F10 / #470). Live TEST store
``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip marker. pytest ``-n 12``.

REVISION r2 (``contract-63c-i-a-r2``, 2026-09-24) — executes ``docs/design/2026-09-24-packet63c-
amendment-2.md`` §D (15 items; A1 population/resolver, A2 the ``session_keep_id`` registry seam, A3 the
provenance-pair invariant, A4 ``lorerunes.is_legal_identifier``). Per-item receipts:
``REPORT-contract-63c-i-a-r2.md`` (archived with the wave).

BUILDER NOTES — docstring rows the contract cannot pin (amendment-1 N2 / amendment-2 §D items 14-15):
* ``LegacyMapping`` (``governed.py``) has 0 references — a docstring-shape dataclass. The i-a builder
  adds the agent disposition ``OWNED-BY-THE-OPERATOR`` to ITS DOCSTRING beside memory/brief/message
  (ruling §6); nothing here can observe it (R3/N2 — unpinnable by construction, named so it is not
  rediscovered at the cold audit).
* Operator ruling D3: fold ``test_agent_owns_principal_schema.py::_create_agent`` onto
  ``_governed_contract.seed_agent_legacy`` in the build's REFACTOR step (its docstring is re-dated
  here; the fold itself is a builder action, not a contract pin).
"""

from __future__ import annotations

import re
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    AGENT_TABLE,
    access_token,
    agent_case,
    apply_ddl,
    build_principal_and_keep_stores,
    credentialed_app_context,
    frozen_asserted_agent_ddl,
    governed_overlay_ddl,
    observe_governed_table_writes,
    patch_shared_object_everywhere,
    seed_agent_governed,
    seed_agent_legacy,
    store_handle,
    unbounded_agent_ddl,
)
from _surreal_harness import (
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture (live per-test store)
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.agents import AgentRegistry, AgentRegistryError
from loremaster.governed import PROJECT_KEEP_KEY
from loremaster.store import surreal_schema
from loremaster.store._txn import SurrealStoreError, TxnDomainRejectionError
from lorerunes.pdp import keep_scope

from loremaster import principals

_DIM = 8


def _bare(value: Any) -> str:
    text = str(getattr(value, "id", value))
    return text.split(":", 1)[-1] if ":" in text else text


# =========================================================================== #
# Q1 §2.2 — the register CREATE stamps: owner_principal = the registrant's principal, owner_agent =
# the row's OWN minted id (SF-63-2), scope = keep:<the session keep register mints>. Driven through
# the FULL tool path (``ctx.comms(action='register')`` mints the SF-63-1 session keep — a bare
# registry call does not), with a CREDENTIALED holder (β is 63c-i-b; a credentialed register works
# at HEAD). RED at HEAD: owner_agent/scope columns do not exist, so the read-back reads NONE.
# =========================================================================== #


class TestRegisterStampsTheGovernedTriple63cIA:
    """§2.2 — a credentialed ``register`` stamps the full governed triple onto the new agent row.
    ``owner_principal`` is already stamped at HEAD (pkt-62); ``owner_agent=self`` + ``scope=session
    keep`` are the 63c additions (RED at HEAD). Fixtures DISCRIMINATE: ≥1 real principal, a real
    session keep, and the row's OWN id read back from the store (not assumed)."""

    @staticmethod
    async def _register_and_read(
        world: dict[str, Any], *, agent: str, session: str, role: str = "builder"
    ) -> dict[str, Any]:
        """Drive the credentialed tool register, then read the row's governed triple + id via the
        admin connection (explicit projection — store-ref §2 reads NONE for an unset/absent column)."""
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        await ctx.comms(action="register", agent=agent, session=session, role=role)
        rows = await run(
            world["admin_conn"],
            f"SELECT id, owner_principal, owner_agent, scope FROM {AGENT_TABLE} WHERE name = $n",
            {"n": agent},
        )
        assert rows, f"the credentialed register wrote no agent row for {agent!r}"
        row: dict[str, Any] = rows[0]
        return row

    async def test_a_credentialed_register_stamps_owner_principal_self_agent_and_session_scope(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — a credentialed ``register`` stamps ``owner_principal`` = the registrant's
        principal (already true at HEAD), ``owner_agent`` = the row's OWN id (RED — column absent),
        and ``scope`` = ``keep:<session keep>`` (RED — column absent). The session keep is the one
        ``_comms_register`` mints (SF-63-1); its scope is read from the keep store, never assumed."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            row = await self._register_and_read(world, agent="fixer-b", session="wave7")
            bare_id = _bare(row["id"])
            assert str(row["owner_principal"]) == f"principal:{world['pids']['alice']}", (
                f"owner_principal must be the registrant's principal, got {row['owner_principal']!r}"
            )
            assert str(row.get("owner_agent")) == f"{AGENT_TABLE}:{bare_id}", (
                f"owner_agent must be the row's OWN id (SF-63-2 owner = (owner_principal, id)), got "
                f"{row.get('owner_agent')!r} — RED at HEAD (the owner_agent column is unbuilt)"
            )
            session_keep = await world["ctx"]._keep_store.get_by_key("session:wave7")  # noqa: SLF001
            assert session_keep is not None, "register did not mint the SF-63-1 session keep"
            assert row.get("scope") == keep_scope(_bare(session_keep.id)), (
                f"scope must be keep:<the session keep register minted>, got {row.get('scope')!r} — "
                f"RED at HEAD (the scope column is unbuilt)"
            )

    async def test_re_register_does_not_restamp_the_governed_triple_mint_once(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — the stamp is MINT-ONCE-ON-CREATE (§2.2 row 2): a re-register of the SAME
        ``(session, name)`` leaves the triple byte-identical. Asserts the CONCRETE stamped values
        after BOTH calls (not merely 'unchanged' — two NONEs would pass a bare unchanged check, the
        fixture-doesn't-discriminate trap), so a build that re-derives/clobbers the triple on
        re-register reds. RED at HEAD (owner_agent/scope absent → the concrete-value assert fails)."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            first = await self._register_and_read(world, agent="fixer-b", session="wave7")
            second = await self._register_and_read(world, agent="fixer-b", session="wave7")
            bare_id = _bare(first["id"])
            session_keep = await world["ctx"]._keep_store.get_by_key("session:wave7")  # noqa: SLF001
            expected_scope = keep_scope(_bare(session_keep.id))
            for label, row in (("first", first), ("re-register", second)):
                assert str(row["owner_principal"]) == f"principal:{world['pids']['alice']}", (label, row)
                assert str(row.get("owner_agent")) == f"{AGENT_TABLE}:{bare_id}", (label, row)
                assert row.get("scope") == expected_scope, (label, row)
            assert _bare(second["id"]) == bare_id, "re-register minted a NEW id — not the same row"


    async def test_scope_is_THE_session_keep_across_two_sessions(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — r2 (amendment-2 A2 / §D item 7 / adversary MP-8, WB4). Parameter-value
        monoculture breaker: ONE principal registers into TWO sessions; each row's scope is ITS OWN
        session's keep — never "a keep the registrant can see" (WB4 stamped ``sorted(visible)[0]``,
        which a one-session fixture cannot tell apart). The two scopes must also DIFFER (else the two
        sessions shared a keep and the leg discriminates nothing)."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            scopes: dict[str, Any] = {}
            for agent, session in (("fixer-b", "wave7"), ("fixer-c", "wave8")):
                row = await self._register_and_read(world, agent=agent, session=session)
                keep = await world["ctx"]._keep_store.get_by_key(f"session:{session}")  # noqa: SLF001
                assert keep is not None, f"register did not mint the session keep for {session!r}"
                assert row.get("scope") == keep_scope(_bare(keep.id)), (
                    f"{agent}@{session}: scope must be keep:<THIS session's keep>, got "
                    f"{row.get('scope')!r} (the {session!r} keep is {keep.id!r})"
                )
                scopes[session] = row.get("scope")
            assert scopes["wave7"] != scopes["wave8"], (
                f"two sessions stamped the SAME scope {scopes!r} — the stamp is not keyed on the session"
            )

    async def test_a_householded_joiners_agent_is_stamped_with_the_shared_session_keep(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — r2 (A2 / §D item 7 / MP-8, WB12). A SECOND principal admitted to the session
        via ``add-household`` (a joiner, not the keeper) registers into it: its agent is owned by ITS
        principal and scoped to the SHARED session keep. The keeper's own LATER agent likewise. WB12
        stamped the scope only for the keeper (``kept_by_me``), leaving a joiner's agent NONE-scope."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member", "bob": "member"}, dim=_DIM
        ) as world:
            ctx = world["ctx"]
            await self._register_and_read(world, agent="keeper-a", session="shared")
            keep = await ctx._keep_store.get_by_key("session:shared")  # noqa: SLF001
            assert keep is not None, "the keeper's register did not mint the session keep"
            await ctx._keep_store.add_household_member(  # noqa: SLF001
                keep_id=_bare(keep.id), member_email=world["emails"]["bob"]
            )
            world["holder"]["email"] = world["emails"]["bob"]
            await ctx.comms(action="register", agent="joiner-b", session="shared", role="builder")
            rows = await run(
                world["admin_conn"],
                f"SELECT owner_principal, scope FROM {AGENT_TABLE} WHERE name = 'joiner-b'",
            )
            assert rows, "the householded joiner's register wrote no agent row"
            assert str(rows[0]["owner_principal"]) == f"principal:{world['pids']['bob']}", rows
            assert rows[0].get("scope") == keep_scope(_bare(keep.id)), (
                f"a householded JOINER's agent must be scoped to the SHARED session keep, got {rows!r}"
            )
            later = await self._register_and_read(world, agent="keeper-a2", session="shared")
            assert later.get("scope") == keep_scope(_bare(keep.id)), (
                f"the keeper's own later agent must join the same session keep, got {later!r}"
            )

    async def test_the_tool_passes_session_keep_id_UNCONDITIONALLY(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at HEAD — r2 (A2 / §D item 8). ``_comms_register`` hands the registry the provenance
        PAIR on EVERY call — ``session_keep_id=None`` explicitly when no keep was minted (the tokenless
        α interim), never a conditional splat that omits the kwarg (the adversary's ref2 shape, REJECTED
        by A2: a conditional kwarg whose only purpose is to keep an un-updated fake from raising is a
        fixture guaranteeing the condition under which the seam mismatch is invisible). A spy on the
        REAL registry records the kwargs of a TOKENLESS and a CREDENTIALED register."""
        import loremaster.server as server_mod

        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx = world["ctx"]
            recorded: list[dict[str, Any]] = []
            real_register = ctx.agent_registry.register

            async def _spy(*args: Any, **kwargs: Any) -> Any:
                recorded.append(dict(kwargs))
                return await real_register(*args, **kwargs)

            monkeypatch.setattr(ctx.agent_registry, "register", _spy)
            monkeypatch.setattr(server_mod, "get_access_token", lambda: None)  # tokenless (α)
            await ctx.comms(action="register", agent="ownerless-a", session="wave7", role="builder")
            world["holder"]["email"] = world["emails"]["alice"]
            monkeypatch.setattr(
                server_mod, "get_access_token", lambda: access_token(subject=world["emails"]["alice"])
            )
            await ctx.comms(action="register", agent="owned-a", session="wave8", role="builder")
            assert len(recorded) == 2, f"expected two registry register calls, got {recorded!r}"
            tokenless, credentialed = recorded
            assert "session_keep_id" in tokenless and tokenless["session_keep_id"] is None, (
                f"a TOKENLESS register must pass session_keep_id=None EXPLICITLY (A2: unconditional, "
                f"never a conditional splat), got kwargs {sorted(tokenless)!r}"
            )
            assert tokenless.get("owner_principal_id") is None, tokenless
            keep = await ctx._keep_store.get_by_key("session:wave8")  # noqa: SLF001
            assert keep is not None
            assert credentialed.get("session_keep_id") == _bare(keep.id), (
                f"a credentialed register must pass THE session keep's BARE id (the keep the SF-63-1 "
                f"gate just checked), got {credentialed.get('session_keep_id')!r} vs {keep.id!r}"
            )
            assert credentialed.get("owner_principal_id") == world["pids"]["alice"], credentialed


# =========================================================================== #
# A2 + A3 — the REGISTRY seam: ``register(..., owner_principal_id, session_keep_id)`` forms
# ``scope = keep_scope(session_keep_id)`` through the ONE formatter and stamps ``owner_agent = self``
# inside the SAME CREATE (mint-once); an inconsistent provenance pair is REFUSED before any store I/O.
# Driven on the REAL registry (no tool layer) so the seam itself is pinned.
# =========================================================================== #


@pytest_asyncio.fixture()
async def registry_world() -> Any:
    """A REAL ``AgentRegistry`` on a fresh per-test DB (``ensure_ready`` applies the current emitter) +
    an admin connection for read-back. Yields ``(registry, connection)``. Reaped (NEVER :18500)."""
    env = make_env(database=unique_database(), dim=_DIM)
    registry = AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await registry.ensure_ready()
    connection = await connect_admin(env)
    try:
        yield registry, connection
    finally:
        await connection.close()
        await registry.close()
        await drop_database(env)


async def _agent_rows(connection: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
    return rows


class TestTheRegistryProvenanceSeam63cIA:
    """A2 (amendment-2) — the registry's provenance INPUT is the bare ``session_keep_id``; the registry
    forms the scope via ``lorerunes.pdp.keep_scope`` (the ONE formatter) and stamps ``owner_agent``
    itself. A3 — ``(owner_principal_id is None) != (session_keep_id is None)`` is REFUSED before any
    store I/O (a server-side caller bug), so R-Q5-1's trap population is unreachable through any writer."""

    async def test_the_registry_stamps_scope_from_session_keep_id_and_owner_agent_self(
        self, registry_world: Any
    ) -> None:
        """⚠ RED at HEAD (no ``session_keep_id`` kwarg → ``TypeError``). A consistent pair lands the full
        triple in the CREATE: ``owner_principal`` link, ``owner_agent`` = the row's OWN id, ``scope`` =
        ``keep_scope(session_keep_id)``."""
        registry, connection = registry_world
        result = await registry.register(
            "fixer-b", session="wave7", role="builder",
            owner_principal_id="alice_pid", session_keep_id="sessionkeep7",
        )
        rows = await run(
            connection,
            f"SELECT owner_principal, owner_agent, scope FROM type::record('{AGENT_TABLE}', $id)",
            {"id": _bare(result.agent.id)},
        )
        assert str(rows[0]["owner_principal"]) == "principal:alice_pid", rows
        assert str(rows[0].get("owner_agent")) == f"{AGENT_TABLE}:{_bare(result.agent.id)}", rows
        assert rows[0].get("scope") == keep_scope("sessionkeep7"), rows

    async def test_the_scope_is_formed_by_the_SHARED_keep_scope_formatter(
        self, registry_world: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD — ONE IMPLEMENTATION, proven by MUTATION (A2): perturb ``keep_scope`` in EVERY
        loaded module exposing it (import-style agnostic — the ``_patch_everywhere`` idiom of
        ``test_secret_typing.py``: a ``from lorerunes import keep_scope`` binding is patched too) and the
        STAMPED scope must move with it. A private ``f"keep:{…}"`` in the registry is not patched, does
        not move, and reds here. BASELINE leg first (unpatched → the real formatter's output), so a
        registry that never stamps a scope cannot pass by 'also not moving'."""
        registry, connection = registry_world
        baseline = await registry.register(
            "fixer-b", session="wave7", role="builder",
            owner_principal_id="alice_pid", session_keep_id="kpbase",
        )
        rows = await run(
            connection,
            f"SELECT scope FROM type::record('{AGENT_TABLE}', $id)",
            {"id": _bare(baseline.agent.id)},
        )
        assert rows[0].get("scope") == keep_scope("kpbase"), f"BASELINE: unpatched stamp wrong: {rows!r}"
        original_keep_scope = keep_scope
        patched = patch_shared_object_everywhere(
            monkeypatch, "keep_scope", original_keep_scope, lambda keep_id: f"mutkeep:{keep_id}"
        )
        assert patched, "keep_scope was not found in any loaded module (the probe could not land)"
        mutated = await registry.register(
            "fixer-c", session="wave7", role="builder",
            owner_principal_id="alice_pid", session_keep_id="kpmut",
        )
        rows = await run(
            connection,
            f"SELECT scope FROM type::record('{AGENT_TABLE}', $id)",
            {"id": _bare(mutated.agent.id)},
        )
        assert rows[0].get("scope") == "mutkeep:kpmut", (
            f"the stamped scope did NOT move when the SHARED keep_scope formatter was perturbed — the "
            f"registry formats the scope with a PRIVATE copy (A2: ONE formatter). got {rows!r}"
        )

    @pytest.mark.parametrize(
        ("owner_principal_id", "session_keep_id"),
        [
            pytest.param("alice_pid", None, id="owner-without-keep"),
            pytest.param(None, "sessionkeep7", id="keep-without-owner"),
        ],
    )
    async def test_an_inconsistent_provenance_pair_is_refused_before_any_store_io(
        self, registry_world: Any, owner_principal_id: str | None, session_keep_id: str | None
    ) -> None:
        """⚠ RED at HEAD — A3: a MIXED pair is refused with a teaching ``AgentRegistryError`` (an
        INTERNAL invariant worded for the engineer) and ZERO rows written. At HEAD the kwarg does not
        exist (``TypeError``, not ``AgentRegistryError``) → RED. Mutation: invert the XOR → these two
        RED and the consistent pairs below RED too."""
        registry, connection = registry_world
        with pytest.raises(AgentRegistryError) as exc_info:
            await registry.register(
                "fixer-b", session="wave7", role="builder",
                owner_principal_id=owner_principal_id, session_keep_id=session_keep_id,
            )
        message = str(exc_info.value)
        for token in ("owner", "session keep", "nothing was written"):
            assert token in message, (
                f"the A3 refusal must say what was inconsistent and that nothing was written "
                f"(missing {token!r}): {message!r}"
            )
        assert await _agent_rows(connection) == [], (
            "a refused (inconsistent-pair) register wrote an agent row — A3 refuses BEFORE any store I/O"
        )

    @pytest.mark.parametrize(
        ("owner_principal_id", "session_keep_id"),
        [
            pytest.param(None, None, id="alpha-interim-both-none"),
            pytest.param("alice_pid", "sessionkeep7", id="both-set"),
        ],
    )
    async def test_a_consistent_provenance_pair_registers(
        self, registry_world: Any, owner_principal_id: str | None, session_keep_id: str | None
    ) -> None:
        """⚠ RED at HEAD (``session_keep_id`` kwarg absent → ``TypeError``). CONTROL for A3: both
        consistent pairs stay legal AT THE REGISTRY — ``(None, None)`` (the α interim; β is the TOOL
        layer's rule, not the registry's) and ``(set, set)`` — each writing exactly one row whose
        governed columns match the pair. A registry that refuses everything fails here."""
        registry, connection = registry_world
        result = await registry.register(
            "fixer-b", session="wave7", role="builder",
            owner_principal_id=owner_principal_id, session_keep_id=session_keep_id,
        )
        rows = await _agent_rows(connection)
        assert len(rows) == 1, rows
        assert result.re_registered is False
        expected_scope = keep_scope(session_keep_id) if session_keep_id is not None else None
        assert rows[0].get("scope") == expected_scope, rows
        expected_owner = f"principal:{owner_principal_id}" if owner_principal_id is not None else None
        observed_owner = rows[0].get("owner_principal")
        assert (str(observed_owner) if observed_owner is not None else None) == expected_owner, rows


# =========================================================================== #
# Q5 §6 — the agent migrate: ONE 3-column scope-keyed statement + the §2.1 ROW-level precondition
# (finding #470, UNIMPLEMENTED at HEAD). Driven through the REAL migrate_governed(table='agent')
# via a StoreHandle (R4 — the verb borrows the store's own driver; ROUTING IS NOT SHARING). The
# governed overlay is applied so scope/owner columns EXIST regardless of the emitter (isolating the
# RED to the MIGRATE seam, not the DDL emitter — that is W1-1's job).
# =========================================================================== #


async def _migrate_agent(connection: Any, env: Any, *, keep_store: Any, principal_store: Any) -> Any:
    """Drive ``migrate_governed(table='agent')`` through a StoreHandle over the fixture connection
    (R4: the verb borrows the store's driver, never a raw connection — a copied ``UPDATE agent SET …``
    is a private copy that drifts from ``_migrate_agent_owner``)."""
    handle, _calls = store_handle(connection, url=env.url)
    return await principals.migrate_governed(
        table=AGENT_TABLE, store=handle, keep_store=keep_store, principal_store=principal_store
    )


@pytest_asyncio.fixture()
async def agent_migrate_world() -> Any:
    """A store whose ``agent`` table carries the current emitter + the governed overlay (so scope/owner
    columns exist for the migrate seam under test), a SINGLE operator principal (so
    ``resolve_operator_principal`` succeeds), and NO agents yet — each test seeds its own legacy rows.
    Yields ``(principal_store, keep_store, connection, env, operator_bare)``. Reaped (NEVER :18500)."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    case = agent_case()  # the F5 GovernedTableCase — its make_ddl is the REAL agent emitter.
    try:
        await apply_ddl(connection, case.make_ddl(), url=env.url)
        await apply_ddl(connection, governed_overlay_ddl(AGENT_TABLE), url=env.url)
        operator = await principal_store.create(email="operator@example.com", role="admin")
        yield principal_store, keep_store, connection, env, _bare(operator.id)
    finally:
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


class TestAgentMigrateScopeKeyed63cIA:
    """§6 (R-Q5-1..3) — the agent migrate is ONE 3-column scope-keyed statement guarded by the §2.1
    ROW-level precondition. ``report_unmigrated_governed_rows`` fits ``agent`` unchanged (scope-keyed)."""

    @staticmethod
    async def _seed_clean_legacy(connection: Any, *, count: int) -> list[str]:
        """``count`` clean legacy agents — NONE owner, NONE scope (a pre-cutover fleet row)."""
        ids: list[str] = []
        for index in range(count):
            ids.append(
                await seed_agent_legacy(
                    connection, row_id=f"legacy_{index}", name=f"legacy-{index}", session="dead-session"
                )
            )
        return ids

    async def test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent(
        self, agent_migrate_world: Any
    ) -> None:
        """⚠ RED at HEAD (finding #470 / F10) — §2.1's ROW precondition: an ``agent`` row with
        ``scope IS NONE`` but ``owner_principal IS NOT NONE`` means a multi-principal or half-applied
        store, so the migrate REFUSES (``refused=True``, ZERO stamped). At HEAD ``_migrate_agent_owner``
        is owner-keyed and refuses ONLY on operator ambiguity, so it does NOT refuse this store → RED.

        r2 (amendment-2 §D item 6 — MP-7 / MP-11 / sidecar F8): the refusal is BYTE-INERT and TEACHES.
        TWO trap rows (a count of 2 cannot be satisfied by a stray "1" such as the "§2.1" citation —
        WB9) + three clean legacy rows; the FULL ``SELECT *`` of the table is identical before and
        after (not a ``scope`` proxy — WB10 stamped owners FIRST, then refused, and a scope-only
        observation missed it); the reason names the COUNT beside its noun, EVERY trap row id (WB8),
        and the remedy (§6: adjudicate BY HAND). The CONTROL (same store WITHOUT the trap rows) is the
        sibling test below.

        ⚠ KNOWN BOUND (amendment-1 E3 / operator D2): a credentialed ``register`` on ANY pkt-62-through-
        63b image stamps ``owner_principal`` (= the operator) on an agent table with no ``scope`` column,
        so such a store carries owner=operator / scope=NONE rows that this precondition REFUSES —
        neither multi-principal nor half-applied. MEASURED EMPTY 2026-09-24 (production's image predates
        pkt 62; pkt-65 ships 62+63 in one image, and under 63c code every register stamps all three
        columns). RE-OPEN TRIGGER: *"a pkt-62-through-63b image deployed before the 63c cutover."* If it
        fires, the precondition narrows to ``… AND owner_principal != <the resolved operator>`` and
        operator-owned NONE-scope rows are stamped scope + owner_agent only. THEREFORE every trap row
        here is owned by a principal that is NOT the operator — this pin must never assert a refusal
        over an operator-owned row, or it would red the trigger's own remedy (amendment-2 §B conflict 2)."""
        principal_store, keep_store, connection, env, operator_bare = agent_migrate_world
        await self._seed_clean_legacy(connection, count=3)
        trap_ids = ["already_owned_a", "already_owned_b"]
        for trap_index, trap_id in enumerate(trap_ids):
            # NONE scope but a NON-NONE owner that is NOT the operator (E3: never pin the operator case).
            await seed_agent_governed(
                connection, row_id=trap_id, name=f"owned-legacy-{trap_index}", session="dead-session",
                owner_principal=f"other_principal_{trap_index}", owner_agent=None, scope=None,
            )
        before = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
        result = await _migrate_agent(
            connection, env, keep_store=keep_store, principal_store=principal_store
        )
        after = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
        assert result.refused is True, (
            "the agent migrate must REFUSE a store with a NONE-scope row that already carries an owner "
            "(§2.1 row precondition / #470) — a multi-principal or half-applied store is adjudicated by "
            f"hand, never silently stamped. got refused={result.refused!r} reason={result.reason!r}"
        )
        assert result.backfilled == 0, f"a refused migrate must stamp ZERO rows, got {result!r}"
        assert after == before, (
            "a REFUSED migrate MUTATED agent rows — the refusal must be byte-inert (§6 'ZERO rows "
            "stamped'): the precondition runs BEFORE any write, never after a stamp (WB10). "
            f"before={before!r} after={after!r}"
        )
        reason = str(result.reason or "")
        assert re.search(r"\b2\s+(?:agent\s+)?rows?\b", reason), (
            f"the refusal must NAME the count of owned-but-unscoped rows beside its noun ('2 agent "
            f"row(s)' — 2 here, so a stray digit cannot satisfy it), got {reason!r}"
        )
        missing_ids = [trap_id for trap_id in trap_ids if trap_id not in reason]
        assert not missing_ids, (
            f"the refusal must NAME the offending rows (ids, bounded — §6); missing {missing_ids} in "
            f"{reason!r}"
        )
        assert "by hand" in reason.lower(), (
            f"the refusal must TEACH the remedy (§2.1/§6: adjudicate the rows BY HAND before migrating) "
            f"— an operator at cutover reads this first. got {reason!r}"
        )

    async def test_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy(
        self, agent_migrate_world: Any
    ) -> None:
        """⚠ RED at HEAD — r2 (amendment-2 §D item 4 / adversary MP-6, WB2 + WB3; old-leg virtue C4).
        Production's cutover shape: agents registered AFTER 63c (the full triple: a MEMBER owner, their
        own owner_agent, THE session keep's scope) beside legacy NONE rows. The migrate must NOT refuse
        (a governed row is owned AND scoped — the precondition keys on ``scope IS NONE``, not on the
        owner alone: WB3 refused every post-63c store), must backfill EXACTLY the legacy rows, and must
        leave every governed row BYTE-IDENTICAL (∀ scoped rows untouched — WB2 lost the ``WHERE`` and
        re-stamped the member owner to the operator and the session scope to the project keep). RED at
        HEAD: the owner-keyed migrate backfills the NONE-owner rows but leaves ``scope`` NONE, so the
        legacy rows' scope read-back fails (and ``backfilled`` counts owner, not scope)."""
        principal_store, keep_store, connection, env, operator_bare = agent_migrate_world
        member = await principal_store.create(email="member@example.com", role="member")
        session_scope = keep_scope("sessionkeepmix")
        governed_ids = [f"gov_{index}" for index in range(2)]
        for index, governed_id in enumerate(governed_ids):
            await seed_agent_governed(
                connection, row_id=governed_id, name=f"gov-{index}", session="live",
                owner_principal=_bare(member.id), owner_agent=governed_id, scope=session_scope,
            )
        legacy_ids = await self._seed_clean_legacy(connection, count=3)
        governed_before = await run(
            connection, f"SELECT * FROM {AGENT_TABLE} WHERE scope IS NOT NONE ORDER BY id"
        )
        assert len(governed_before) == len(governed_ids), (
            f"fixture: the two governed rows must be seeded scoped, got {governed_before!r}"
        )
        result = await _migrate_agent(
            connection, env, keep_store=keep_store, principal_store=principal_store
        )
        assert result.refused is False, (
            f"a store of GOVERNED (owner AND scope) + legacy agents was REFUSED — the row precondition "
            f"must key on `scope IS NONE AND owner_principal IS NOT NONE`, never on the owner alone "
            f"(WB3): {result.reason!r}"
        )
        assert result.backfilled == len(legacy_ids), (
            f"the migrate must backfill EXACTLY the {len(legacy_ids)} legacy rows, got {result!r}"
        )
        governed_after = await run(
            connection,
            f"SELECT * FROM {AGENT_TABLE} WHERE id IN $ids ORDER BY id",
            {"ids": [row["id"] for row in governed_before]},
        )
        assert governed_after == governed_before, (
            "the migrate RE-STAMPED an already-governed agent (member owner / session scope clobbered) "
            f"— ∀ scoped rows must stay untouched (WB2): before={governed_before!r} "
            f"after={governed_after!r}"
        )
        project_keep = await keep_store.get_by_key(PROJECT_KEEP_KEY)
        assert project_keep is not None, "the migrate did not mint the canonical project keep"
        for legacy_id in legacy_ids:
            row = (
                await run(
                    connection,
                    f"SELECT scope FROM type::record('{AGENT_TABLE}', $id)",
                    {"id": legacy_id},
                )
            )[0]
            assert row.get("scope") == keep_scope(_bare(project_keep.id)), (
                f"legacy {legacy_id} was not scope-stamped to the project keep: {row!r}"
            )

    async def test_R_Q5_1_CONTROL_a_clean_store_backfills_every_none_scope_row(
        self, agent_migrate_world: Any
    ) -> None:
        """CONTROL for the precondition (fixtures-must-discriminate): the SAME store WITHOUT the
        owned-but-unscoped row migrates cleanly — ``refused=False``, ``backfilled == N``. The ONLY
        difference from the pin above is that trap row, so the pin above refuses BECAUSE OF it.
        ⚠ RED at HEAD only on the 3-column read-back is covered by R-Q5-3; here the leg is a
        green-discriminator for the precondition (at HEAD the owner-keyed migrate also backfills N)."""
        principal_store, keep_store, connection, env, operator_bare = agent_migrate_world
        await self._seed_clean_legacy(connection, count=3)
        result = await _migrate_agent(
            connection, env, keep_store=keep_store, principal_store=principal_store
        )
        assert result.refused is False, f"a clean legacy store must not be refused, got {result!r}"
        assert result.backfilled == 3, (
            f"every NONE-scope legacy agent must be backfilled (3 here), got backfilled="
            f"{result.backfilled!r}"
        )

    async def test_R_Q5_2_report_unmigrated_counts_none_scope_before_and_zero_after(
        self, agent_migrate_world: Any
    ) -> None:
        """⚠ RED at HEAD — ``report_unmigrated_governed_rows(store, 'agent')`` == the NONE-scope count
        before the migrate and 0 AFTER (scope-keyed, no agent-special branch). At HEAD the owner-keyed
        migrate stamps ``owner_principal`` but NOT ``scope``, so ``scope IS NONE`` still counts N after
        → RED. Mutation (builder): change the seam's ``WHERE scope IS NONE`` → BOTH [agent] and
        [memory] reds (the ONE scope-keyed unmigrated predicate ∀ governed tables)."""
        from loremaster.governed import report_unmigrated_governed_rows

        principal_store, keep_store, connection, env, operator_bare = agent_migrate_world
        await self._seed_clean_legacy(connection, count=4)
        handle, _calls = store_handle(connection, url=env.url)
        before = await report_unmigrated_governed_rows(handle, AGENT_TABLE)
        assert before == 4, f"before migrate: 4 NONE-scope legacy agents expected, got {before}"
        await _migrate_agent(connection, env, keep_store=keep_store, principal_store=principal_store)
        handle_after, _calls2 = store_handle(connection, url=env.url)
        after = await report_unmigrated_governed_rows(handle_after, AGENT_TABLE)
        assert after == 0, (
            f"after the agent migrate NO row may carry a NONE scope, got {after} — the migrate must be "
            f"SCOPE-keyed (stamp scope), not owner-keyed (which leaves scope NONE)"
        )

    async def test_R_Q5_3_every_migrated_row_reads_back_the_three_column_stamp(
        self, agent_migrate_world: Any
    ) -> None:
        """⚠ RED at HEAD — after the migrate each backfilled row reads back ``owner_agent == its own
        id``, ``scope == keep:<project keep>``, ``owner_principal == the operator``. At HEAD the
        owner-keyed migrate stamps ONLY owner_principal (owner_agent/scope stay NONE) → RED. The
        project keep's scope is read from the keep store (``PROJECT_KEEP_KEY``), never assumed."""
        principal_store, keep_store, connection, env, operator_bare = agent_migrate_world
        ids = await self._seed_clean_legacy(connection, count=3)
        result = await _migrate_agent(
            connection, env, keep_store=keep_store, principal_store=principal_store
        )
        assert not result.refused and result.backfilled == 3, result
        project_keep = await keep_store.get_by_key(PROJECT_KEEP_KEY)
        assert project_keep is not None, "the migrate did not mint the canonical project keep"
        expected_scope = keep_scope(_bare(project_keep.id))
        for row_id in ids:
            row = (
                await run(
                    connection,
                    f"SELECT id, owner_principal, owner_agent, scope "
                    f"FROM type::record('{AGENT_TABLE}', $id)",
                    {"id": row_id},
                )
            )[0]
            assert str(row.get("owner_agent")) == f"{AGENT_TABLE}:{row_id}", (
                f"{row_id}: owner_agent must be the row's OWN id (SF-63-2), got {row.get('owner_agent')!r}"
            )
            assert row.get("scope") == expected_scope, (
                f"{row_id}: scope must be the project keep (§2.2 grandfather), got {row.get('scope')!r}"
            )
            assert str(row["owner_principal"]) == f"principal:{operator_bare}", (
                f"{row_id}: owner_principal must be the operator, got {row['owner_principal']!r}"
            )

    async def test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement(
        self, agent_migrate_world: Any
    ) -> None:
        """⚠ RED at HEAD — r2 (amendment-2 §B R8-C5 / §D item 13). ``governed_exempt("migrate-governed",
        statement=…)`` is STATEMENT-SCOPED (``governed.py`` §F5 EXEMPT ATTRIBUTION): the 3-column
        backfill CHANGES the golden statement, so the token's evidence must MOVE WITH the executed
        statement or F5's leg 2 reds on the first observed run. The wave that changes the golden owns
        it (this one — D1's i-b rows are the per-caller ``write_guard`` labels, not this token). Driven
        under ``observe_governed_table_writes("agent")``: the backfill UPDATE is OBSERVED with an exempt
        token whose origin is ``principals._migrate_agent_owner``, whose (normalised) statement EQUALS the
        executed statement, and which is the ONE scope-keyed 3-column UPDATE (§6). RED at HEAD: the
        token carries the OLD owner-only statement (no ``owner_agent``/``scope`` SET, keyed
        ``WHERE owner_principal IS NONE``)."""
        principal_store, keep_store, connection, env, operator_bare = agent_migrate_world
        await self._seed_clean_legacy(connection, count=2)
        handle, _calls = store_handle(connection, url=env.url)
        with observe_governed_table_writes(AGENT_TABLE) as observed:
            await principals.migrate_governed(
                table=AGENT_TABLE, store=handle, keep_store=keep_store, principal_store=principal_store
            )
        principals_file = "loremaster/loremaster/principals.py"
        migrate_writes = [
            write
            for write in observed
            if getattr(write.exempt, "name", None) == "migrate-governed"
            and getattr(write.exempt, "origin", None) == (principals_file, "_migrate_agent_owner")
            and write.effect is not None
            and not write.effect.is_empty
        ]
        assert migrate_writes, (
            "the agent backfill was not OBSERVED as an effectful write carrying the migrate-governed "
            f"exempt token from principals._migrate_agent_owner: "
            f"{[(getattr(o.exempt, 'name', o.exempt), getattr(o.exempt, 'origin', None)) for o in observed]}"
        )
        for write in migrate_writes:
            token_statement = " ".join(str(getattr(write.exempt, "statement", "")).split())
            executed = " ".join(str(write.statement or "").split())
            assert token_statement == executed, (
                "the migrate-governed token's GOLDEN statement is not the statement the migrate "
                f"EXECUTED (statement-scoped exempt — leg 2): token={token_statement!r} "
                f"executed={executed!r}"
            )
            upper = executed.upper()
            assert upper.startswith(f"UPDATE {AGENT_TABLE.upper()} ") and upper.endswith(
                "WHERE SCOPE IS NONE"
            ), f"the agent backfill must be ONE scope-keyed UPDATE (§6), got {executed!r}"
            for column in ("owner_principal", "owner_agent", "scope"):
                assert f"{column} =" in executed, (
                    f"the agent backfill must SET all three governed columns (§6); {column!r} is not "
                    f"set in {executed!r}"
                )

    async def test_the_migrate_is_idempotent(self, agent_migrate_world: Any) -> None:
        """GREEN-DISCRIMINATOR — a SECOND migrate backfills ZERO (idempotent), never re-stamps or
        refuses. GREEN at HEAD AND on the built world (both are idempotent by construction); REDDENS
        a build whose second run re-scans/re-stamps the already-migrated rows."""
        principal_store, keep_store, connection, env, operator_bare = agent_migrate_world
        await self._seed_clean_legacy(connection, count=2)
        first = await _migrate_agent(connection, env, keep_store=keep_store, principal_store=principal_store)
        second = await _migrate_agent(connection, env, keep_store=keep_store, principal_store=principal_store)
        assert not first.refused and first.backfilled == 2, first
        assert not second.refused and second.backfilled == 0, (
            f"the SECOND migrate must backfill 0 (idempotent), got {second!r}"
        )


# =========================================================================== #
# DD-3.c §4.4 — the two-leg dirty-store shape + the heartbeat leg + P-A3. Leg A: the DROP LANDS
# (#107 direction). Leg B: the REAL migrate SURVIVES legacy violators (DD-3.c direction) + a
# C-control that RAISES under the frozen asserted DDL. The heartbeat leg: a real touch succeeds on a
# role="" legacy row (RED the day the role ASSERT returns). P-A3: a junk-status row refuses the
# backfill (a pinned KNOWN BOUND, status is KEPT).
# =========================================================================== #

# The three non-aligned agent ASSERTs Q3 DROPs → their violator shapes become ACCEPTED after the drop.
# ``status='urgent'`` is the KEPT one (stays rejected — §4.2).
_AGENT_DROP_VIOLATORS: dict[str, dict[str, Any]] = {
    "name": {"name": "Bad Name!"},
    "session": {"session": "Bad Session!"},
    "role": {"role": ""},
}


@pytest_asyncio.fixture()
async def unbounded_agent_world() -> Any:
    """A store whose ``agent`` table carries the UNBOUNDED old-world DDL + governed overlay (so the
    writer-refused violators can be SEEDED), a single operator principal, no agents yet. Module-level
    so both the Leg B and P-A3 classes share it. Yields ``(principal_store, keep_store, connection,
    env)``. Reaped (NEVER :18500)."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    try:
        await apply_ddl(connection, unbounded_agent_ddl(), url=env.url)
        await principal_store.create(email="operator@example.com", role="admin")
        yield principal_store, keep_store, connection, env
    finally:
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


class TestTheAgentAssertsDropFromADirtyStore63cIA:
    """DD-3.c Leg A (§4.4) — the #107 direction: the DROP must LAND on a store that ALREADY carries
    the ASSERTed agent definitions (production's shape). BASELINE: under the FROZEN asserted DDL every
    violator is refused; after re-applying the CURRENT emitter the three non-aligned shapes are
    ACCEPTED (values byte-intact), while ``status='urgent'`` STAYS rejected (KEEP). Leg A never runs
    the migrate, so it is blind to a re-added constraint denying it — that is Leg B's job.

    Mutation proof (declared, from ``--collect-only``): re-add ONE dropped ASSERT (say ``role``) →
    exactly the ``role`` accept-parametrization RED with the engine's text; the other two GREEN; P2
    [agent] RED; the frozen-capture control + the status-STAYS leg unaffected; restore → GREEN."""

    @staticmethod
    async def _seed_violator(connection: Any, shape: str) -> str:
        base: dict[str, Any] = {"name": "ok-name", "session": "ok-session", "role": "builder"}
        base.update(_AGENT_DROP_VIOLATORS[shape])
        return await seed_agent_legacy(connection, row_id=f"v_{shape}", **base)

    def test_the_frozen_old_world_is_a_faithful_asserted_capture(self) -> None:
        """CONTROL — the FROZEN asserted agent world (``frozen_asserted_agent_ddl()``, the 699a6e9
        capture) carries all four birth ASSERT literals. The BASELINE 'refused under the asserted DDL'
        legs REST on this; if the capture rotted, they would be vacuous. Verified against WHAT IT
        FROZE, NEVER against the live emitter (which this wave is designed to change — the C-DEF the
        message Leg A's own control warns of). GREEN at HEAD AND after the build (the constant is
        immutable)."""
        frozen = frozen_asserted_agent_ddl()
        for assert_literal in (
            "ASSERT string::matches($value, '^[a-z0-9][a-z0-9_-]{0,63}$')",
            "ASSERT string::len(string::trim($value)) > 0",
            "ASSERT $value IN ['active', 'idle', 'input_required', 'retired']",
        ):
            assert assert_literal in frozen, (
                f"the FROZEN 699a6e9 asserted agent world is MISSING {assert_literal!r} — the capture "
                f"in frozen_asserted_agent_ddl() has rotted, so the BASELINE 'refused under the asserted "
                f"DDL' legs it backstops are vacuous."
            )

    @pytest.mark.parametrize("shape", [*_AGENT_DROP_VIOLATORS, "status"])
    async def test_BASELINE_the_asserted_old_world_refuses_every_violator(
        self, admin_db: tuple[SurrealConnection, SurrealEnv], shape: str  # noqa: F811
    ) -> None:
        """Positive control: under the FROZEN asserted DDL EACH violator (hostile name/session, blank
        role, junk status) is REJECTED — without it 'accepted after the drop' could be true because
        the shape was never refused. GREEN at HEAD and after the build."""
        connection, _env = admin_db
        await apply_ddl(connection, frozen_asserted_agent_ddl(), url=_env.url)
        overrides = {"status": {"status": "urgent"}}.get(shape, _AGENT_DROP_VIOLATORS.get(shape, {}))
        base: dict[str, Any] = {"name": "ok-name", "session": "ok-session", "role": "builder"}
        base.update(overrides)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface
            await seed_agent_legacy(connection, row_id=f"baseline_{shape}", **base)

    async def test_CONTROL_a_clean_row_lands_under_the_asserted_old_world(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """Fixture-liveness control: a CLEAN legacy agent IS accepted under the asserted DDL — proving
        the table is live and the BASELINE rejections are the ASSERTs, not a dead table."""
        connection, _env = admin_db
        await apply_ddl(connection, frozen_asserted_agent_ddl(), url=_env.url)
        row_id = await seed_agent_legacy(connection, row_id="clean", name="clean-agent", session="wave7")
        assert row_id

    @pytest.mark.parametrize("shape", list(_AGENT_DROP_VIOLATORS))
    async def test_the_assert_DROPS_and_the_value_survives_byte_intact(
        self, admin_db: tuple[SurrealConnection, SurrealEnv], shape: str  # noqa: F811
    ) -> None:
        """⚠ RED at HEAD (the #107 direction) — apply the frozen asserted DDL, then re-apply the
        CURRENT ``generate_agent_ddl()``; under Q3 it re-lands ``{shape}`` CLAUSE-FREE (OVERWRITE =
        full replace drops the omitted ASSERT — store-ref §1.2), so a formerly-refused hostile value
        is now ACCEPTED and survives byte-intact (store-ref §1.4). At HEAD the emitter STILL emits the
        ASSERT → the seed RAISES → RED for the right reason (the OVERWRITE drop has not landed)."""
        connection, _env = admin_db
        await apply_ddl(connection, frozen_asserted_agent_ddl(), url=_env.url)
        await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=_env.url)
        try:
            row_id = await self._seed_violator(connection, shape)
        except Exception as error:  # noqa: BLE001 - RED-at-HEAD surface (the ASSERT still lands)
            pytest.fail(
                f"RED-at-HEAD (right reason): the {shape!r} ASSERT is STILL on the store after "
                f"re-applying generate_agent_ddl() — the Q3 OVERWRITE drop has not landed on the dirty "
                f"store (§4.4 Leg A / #107 direction). engine: {error}"
            )
        column, value = next(iter(_AGENT_DROP_VIOLATORS[shape].items()))
        row = (
            await run(
                connection,
                f"SELECT {column} FROM type::record('{AGENT_TABLE}', $id)",
                {"id": row_id},
            )
        )[0]
        assert row[column] == value, (
            f"{shape}: the migration converges SCHEMA not DATA (store-ref §1.4) — the hostile {column} "
            f"must survive byte-intact, got {row[column]!r} (expected {value!r})"
        )

    async def test_the_status_assert_STAYS_after_migrating_a_dirty_store(
        self, admin_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """§4.2 KEEP — ``status`` is the SOLE agent store ASSERT that SURVIVES: a junk status is a row
        the reader (``AgentStatus`` Literal) could never decode. After re-applying the current emitter,
        ``status='urgent'`` is STILL REJECTED. GREEN at HEAD AND after the build; a build that DROPS the
        status ASSERT (the wrong build) reds here (the seed would be accepted)."""
        connection, _env = admin_db
        await apply_ddl(connection, frozen_asserted_agent_ddl(), url=_env.url)
        await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=_env.url)
        with pytest.raises(Exception):  # noqa: B017 - engine ASSERT violation surface (status domain)
            await seed_agent_legacy(
                connection, row_id="junk_status", name="ok-name", session="ok-session", status="urgent"
            )


class TestTheRealAgentMigrateSurvivesLegacyViolators63cIA:
    """DD-3.c Leg B (§4.4) — the DD-3.c direction: the REAL ``migrate_governed(table='agent')`` survives
    the legacy rows the writer would refuse (hostile name/session, blank role), is NOT refused, stamps
    all three columns, and leaves every hostile value byte-intact. Its C-CONTROL proves the instrument
    CAN see the hazard (the frozen asserted DDL makes the migrate RAISE)."""

    @staticmethod
    async def _seed_violators_and_clean(connection: Any, *, count_clean: int = 1) -> dict[str, str]:
        """Seed the three non-aligned violators + one clean row UNDER the unbounded DDL (all NONE
        owner/scope). Returns ``{shape: id}`` (clean keyed ``clean``)."""
        ids: dict[str, str] = {}
        for shape, override in _AGENT_DROP_VIOLATORS.items():
            base: dict[str, Any] = {"name": "ok-name", "session": "s1", "role": "builder"}
            base.update(override)
            ids[shape] = await seed_agent_legacy(connection, row_id=f"legb_{shape}", **base)
        for index in range(count_clean):
            ids[f"clean_{index}"] = await seed_agent_legacy(
                connection, row_id=f"legb_clean_{index}", name=f"clean-{index}", session="s1"
            )
        return ids

    async def test_the_real_migrate_survives_the_legacy_violators_all_stamped(
        self, unbounded_agent_world: Any
    ) -> None:
        """⚠ RED at HEAD (DD-3.c direction) — seed the violators under the unbounded DDL, migrate the
        SCHEMA with the current ``generate_agent_ddl()``, then drive the REAL migrate: NOT refused,
        stamps all rows (3 columns), hostile values byte-intact. At HEAD the emitter STILL emits the
        name/session/role ASSERTs, so migrating the schema write-poisons the violators and the migrate
        UPDATE (SET owner/scope over every NONE-scope row — a WHOLE-record re-validation, store-ref
        §1.4) is REFUSED WHOLESALE. On the built world the ASSERTs are gone and every row stamps."""
        principal_store, keep_store, connection, env = unbounded_agent_world
        ids = await self._seed_violators_and_clean(connection)
        before = await run(connection, f"SELECT count() FROM {AGENT_TABLE} GROUP ALL")
        assert before and before[0]["count"] == len(ids), (
            f"BASELINE: the unbounded old world must accept all {len(ids)} legacy rows, got {before!r}"
        )
        await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
        try:
            result = await _migrate_agent(
                connection, env, keep_store=keep_store, principal_store=principal_store
            )
        except Exception as error:  # noqa: BLE001 - RED-at-HEAD surface (an ASSERT poisons it)
            pytest.fail(
                "RED-at-HEAD (right reason): migrate_governed(table='agent') RAISED on the dirty store "
                "— a legacy hostile row failed a name/session/role ASSERT the current emitter STILL "
                f"lands, so the whole cutover UPDATE aborted (§4.4 Leg B / DD-3.c). engine: {error}"
            )
        assert not result.refused, f"the agent migrate was REFUSED over the dirty store: {result.reason!r}"
        assert result.backfilled == len(ids), (
            f"the migrate must backfill all {len(ids)} legacy rows, got backfilled={result.backfilled!r}"
        )
        for shape, override in _AGENT_DROP_VIOLATORS.items():
            column, value = next(iter(override.items()))
            row = (
                await run(
                    connection,
                    f"SELECT owner_principal, owner_agent, scope, {column} "
                    f"FROM type::record('{AGENT_TABLE}', $id)",
                    {"id": ids[shape]},
                )
            )[0]
            assert row.get("owner_principal") is not None and isinstance(row.get("scope"), str), (
                f"{shape}: owner_principal/scope not backfilled, got {row!r}"
            )
            # r2 (§D item 12 / sidecar F7 / adversary R2): ALL THREE columns on the DIRTY population.
            assert str(row.get("owner_agent")) == f"{AGENT_TABLE}:{ids[shape]}", (
                f"{shape}: owner_agent must be the violator row's OWN id (the 3-column stamp holds on the "
                f"dirty population too — §4.4 Leg B 'all three columns'), got {row.get('owner_agent')!r}"
            )
            assert row[column] == value, (
                f"{shape}: the hostile {column} must survive byte-intact (store-ref §1.4), "
                f"got {row[column]!r}"
            )
        # r2 (§D item 12): idempotent on the SECOND call over the violators (§4.4 Leg B).
        second = await _migrate_agent(
            connection, env, keep_store=keep_store, principal_store=principal_store
        )
        assert second.refused is False and second.backfilled == 0, (
            f"a SECOND migrate over the (now stamped) dirty store must backfill 0 and not refuse — "
            f"§4.4 Leg B idempotence, got {second!r}"
        )

    async def test_C_CONTROL_the_frozen_asserted_ddl_makes_the_migrate_RAISE(
        self, unbounded_agent_world: Any
    ) -> None:
        """C-CONTROL (§4.4) — the instrument CAN see the hazard: seed the violators, then apply the
        FROZEN asserted DDL (not the current emitter) as the schema migrate, and the REAL migrate
        RAISES ``TxnDomainRejectionError`` matching ``(assert violation)`` with ZERO rows stamped (the
        DD-3.c mechanism reproduced on ``agent``). Immune to the emitter's drop (uses the frozen DDL),
        so it is GREEN at HEAD AND after the build — proving a poisoned row DOES abort the migrate."""
        principal_store, keep_store, connection, env = unbounded_agent_world
        ids = await self._seed_violators_and_clean(connection)
        await apply_ddl(connection, frozen_asserted_agent_ddl(), url=env.url)
        with pytest.raises(TxnDomainRejectionError, match=r"\(assert violation\)"):
            await _migrate_agent(connection, env, keep_store=keep_store, principal_store=principal_store)
        for row_id in ids.values():
            row = (
                await run(
                    connection,
                    f"SELECT owner_principal FROM type::record('{AGENT_TABLE}', $id)",
                    {"id": row_id},
                )
            )[0]
            assert row.get("owner_principal") is None, (
                f"the aborted migrate left a row STAMPED ({row_id}) — a whole-statement abort must stamp "
                f"NOTHING"
            )


class TestAgentHeartbeatOnALegacyRoleRow63cIA:
    """§4.4 heartbeat leg — the Part-C mechanism through the PRODUCTION ``touch`` seam. A legacy agent
    with ``role=""`` (seeded under the unbounded DDL) must be able to ``heartbeat`` (touch) after the
    Q3 drop lands. RED at HEAD: the current emitter STILL lands the role non-empty ASSERT, so ``touch``
    (a whole-row UPDATE, store-ref §1.4) re-validates ``role=""`` and is REFUSED — the per-agent
    self-denial reopening. GREEN after the build (role ASSERT dropped → touch succeeds).

    r2 (amendment-2 §D item 2 / MP-2 + E2): the r1 leg seeded ``row_id="role_empty"``, but ``touch``
    resolves the DETERMINISTIC ``AgentRegistry._agent_id(session, name)`` (a uuid5), so it raised
    ``UnknownAgentError`` on EVERY build and a broad ``except Exception`` relabelled that as the
    right-reason RED — a failure message promising a check the test never performed (CLAUDE.md's
    false-gate class; adversary §1). Fixed: the seed id IS the production mint; the ``except`` is
    narrowed to the driver's typed store rejection. The positive control below (E2's shape — NOT a
    junk status, which ``_row_to_agent`` decode-rejects before any UPDATE) proves the leg can SEE a
    store denial through the ``touch`` seam, immune to the build (frozen DDL, never the emitter)."""

    @staticmethod
    async def _seed_role_empty_legacy_row(connection: Any) -> str:
        """Seed the ``role=""`` legacy agent at the id ``touch`` will RESOLVE — the production mint
        ``AgentRegistry._agent_id("wave7", "legacy-agent")``, never a hand-picked id (MP-2)."""
        return await seed_agent_legacy(
            connection,
            row_id=AgentRegistry._agent_id("wave7", "legacy-agent"),  # noqa: SLF001 - the production id mint
            name="legacy-agent",
            session="wave7",
            role="",
        )

    async def test_a_touch_succeeds_on_a_role_empty_legacy_row_after_the_drop(self) -> None:
        """⚠ RED at HEAD — seed a ``role=""`` legacy agent under the unbounded DDL, apply the current
        emitter, then the REAL ``AgentRegistry.touch`` on it SUCCEEDS (a bare heartbeat). At HEAD the
        role ASSERT still lands → the touch UPDATE re-validates ``role=""`` → the driver raises its
        typed store rejection (``SurrealStoreError``, ``(assert violation)``) → RED (right reason: the
        drop is unbuilt). ANY other exception (e.g. ``UnknownAgentError`` from a mis-seeded id)
        propagates un-relabelled. RED the day the role ASSERT returns."""
        env = make_env(database=unique_database(), dim=_DIM)
        connection = await connect_admin(env)
        registry = AgentRegistry(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        try:
            await apply_ddl(connection, unbounded_agent_ddl(), url=env.url)
            await self._seed_role_empty_legacy_row(connection)
            await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
            try:
                updated = await registry.touch("legacy-agent", session="wave7", note="alive")
            except SurrealStoreError as error:  # RED-at-HEAD surface ONLY: the store ASSERT refusal
                pytest.fail(
                    "RED-at-HEAD (right reason): touch on a role='' legacy row was REFUSED BY THE STORE "
                    "— the role non-empty ASSERT is STILL on the store after the current emitter (the Q3 "
                    f"drop is unbuilt), so the whole-row heartbeat UPDATE self-denies (§4.4). engine: {error}"
                )
            assert updated.name == "legacy-agent", updated
            assert updated.last_note == "alive", updated
        finally:
            await registry.close()
            await connection.close()
            await drop_database(env)

    async def test_CONTROL_the_frozen_asserted_ddl_makes_the_touch_RAISE(self) -> None:
        """POSITIVE CONTROL (amendment-1 E2) — the leg CAN see a store denial through ``touch``: seed
        ``role=""`` under ``unbounded_agent_ddl()``, apply ``frozen_asserted_agent_ddl()`` (NEVER the
        current emitter), then the REAL ``touch`` → the driver's typed store rejection
        (``SurrealStoreError`` matching ``(assert violation)``) and the row is byte-identical (zero
        rows changed). GREEN at HEAD AND after the build (the frozen DDL is immutable). REDDENS a
        ``touch`` that stops re-validating the row (e.g. a MERGE that skips validation) — the Leg B
        C-control's twin, through the heartbeat seam."""
        env = make_env(database=unique_database(), dim=_DIM)
        connection = await connect_admin(env)
        registry = AgentRegistry(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        try:
            await apply_ddl(connection, unbounded_agent_ddl(), url=env.url)
            await self._seed_role_empty_legacy_row(connection)
            # The current emitter FIRST declares every column ``touch`` writes (the frozen capture
            # models 6 of the 16 agent columns — R1), THEN the frozen DDL re-lands the role ASSERT by
            # OVERWRITE. The ASSERT that refuses comes from the FROZEN capture on EVERY build, so the
            # control stays build-immune (E2: the refusing DDL is never the current emitter).
            await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
            await apply_ddl(connection, frozen_asserted_agent_ddl(), url=env.url)
            before = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
            with pytest.raises(SurrealStoreError, match=r"\(assert violation\)"):
                await registry.touch("legacy-agent", session="wave7", note="alive")
            after = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
            assert after == before, (
                f"a store-REFUSED touch changed agent rows — the whole-row UPDATE must abort atomically "
                f"(store-ref §3): before={before!r} after={after!r}"
            )
        finally:
            await registry.close()
            await connection.close()
            await drop_database(env)


class TestAJunkStatusLegacyRowRefusesTheAgentBackfill63cIA:
    """P-A3 (§4.4) — a PINNED KNOWN BOUND. ``status`` is KEPT (§4.2), so a legacy junk-``status`` row
    REFUSES the agent backfill (ONE statement, ZERO stamped) — BY DESIGN, because the reader
    (``AgentStatus`` Literal) could never serve it either. Heal a real occurrence FIRST with the §13.2
    three-step protocol: WIDEN ``AGENT_STATUSES`` → HEAL ``UPDATE agent SET status=… WHERE status=…``
    → NARROW. If you closed this deliberately (dropped the status ASSERT), delete this pin and say so.

    ⚠ The engine's FIELD NAME is redacted by the driver (measured on ``message`` P-G3), so the STATUS
    is isolated by CONSTRUCTION: the sibling positive control (same rows, LEGAL status → migrate
    SUCCEEDS) proves the ONLY refusing difference is the junk status."""

    async def test_a_legacy_junk_status_row_refuses_the_real_migrate(
        self, unbounded_agent_world: Any
    ) -> None:
        """KNOWN BOUND — seed ONE junk-``status`` legacy row + one clean under the unbounded DDL (NO
        other violator), migrate the schema with the CURRENT emitter (status ASSERT KEPT), then the
        REAL migrate RAISES and BOTH rows stay NONE-scope (zero stamped). GREEN at HEAD AND after the
        build (status kept throughout)."""
        principal_store, keep_store, connection, env = unbounded_agent_world
        junk_id = await seed_agent_legacy(
            connection, row_id="junk", name="junk-agent", session="s1", status="urgent"
        )
        clean_id = await seed_agent_legacy(
            connection, row_id="clean", name="clean-agent", session="s1"
        )
        await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
        with pytest.raises(TxnDomainRejectionError, match=r"\(assert violation\)"):
            await _migrate_agent(connection, env, keep_store=keep_store, principal_store=principal_store)
        for row_id in (junk_id, clean_id):
            row = (
                await run(
                    connection,
                    f"SELECT scope FROM type::record('{AGENT_TABLE}', $id)",
                    {"id": row_id},
                )
            )[0]
            assert row.get("scope") is None, (
                f"the aborted (junk-status) migrate left a row STAMPED ({row_id}) — zero rows must stamp"
            )

    async def test_CONTROL_a_legal_status_fixture_migrates_cleanly(
        self, unbounded_agent_world: Any
    ) -> None:
        """POSITIVE CONTROL for the KNOWN BOUND (the field name is redacted, so the status is isolated
        by construction): the SAME two-row fixture with a LEGAL status migrates SUCCESSFULLY. The ONLY
        difference from the pin above is the junk status, so the pin above refuses BECAUSE OF it. ⚠ RED
        at HEAD only if the 3-column stamp is checked (it is not here — this control asserts the migrate
        is NOT refused); at HEAD the owner-keyed migrate also succeeds on legal-status rows, so this is
        a green-discriminator for the P-A3 isolation."""
        principal_store, keep_store, connection, env = unbounded_agent_world
        await seed_agent_legacy(connection, row_id="ok1", name="ok-one", session="s1", status="idle")
        await seed_agent_legacy(connection, row_id="ok2", name="ok-two", session="s1", status="active")
        await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
        result = await _migrate_agent(connection, env, keep_store=keep_store, principal_store=principal_store)
        assert not result.refused and result.backfilled == 2, (
            f"a legal-status fixture must migrate cleanly — P-A3's refusal is the junk status, not a "
            f"fixture artifact. got {result!r}"
        )
