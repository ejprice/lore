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
"""

from __future__ import annotations

import re
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    AGENT_TABLE,
    agent_case,
    apply_ddl,
    build_principal_and_keep_stores,
    credentialed_app_context,
    frozen_asserted_agent_ddl,
    governed_overlay_ddl,
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
from loremaster.agents import AgentRegistry
from loremaster.governed import PROJECT_KEEP_KEY
from loremaster.store import surreal_schema
from loremaster.store._txn import TxnDomainRejectionError
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
        store, so the migrate REFUSES (``refused=True``, ZERO stamped), naming the count. At HEAD
        ``_migrate_agent_owner`` is owner-keyed and refuses ONLY on operator ambiguity, so it does NOT
        refuse this store — it stamps the NONE-owner rows and skips the owned one → ``refused=False``
        → RED. The CONTROL (same store WITHOUT that row) is the sibling test below."""
        principal_store, keep_store, connection, env, operator_bare = agent_migrate_world
        await self._seed_clean_legacy(connection, count=2)
        # the trap row: NONE scope but a NON-NONE owner (a different principal record link).
        await seed_agent_governed(
            connection, row_id="already_owned", name="owned-legacy", session="dead-session",
            owner_principal="some_other_principal", owner_agent=None, scope=None,
        )
        result = await _migrate_agent(
            connection, env, keep_store=keep_store, principal_store=principal_store
        )
        assert result.refused is True, (
            "the agent migrate must REFUSE a store with a NONE-scope row that already carries an owner "
            "(§2.1 row precondition / #470) — a multi-principal or half-applied store is adjudicated by "
            f"hand, never silently stamped. got refused={result.refused!r} reason={result.reason!r}"
        )
        assert result.backfilled == 0, f"a refused migrate must stamp ZERO rows, got {result!r}"
        assert re.search(r"\b1\b", str(result.reason or "")), (
            f"the refusal reason must NAME the count of owned-but-unscoped rows (1 here), got "
            f"{result.reason!r}"
        )
        # nothing was stamped on the clean rows either — a refusal is all-or-nothing.
        after = await run(
            connection,
            f"SELECT count() FROM {AGENT_TABLE} WHERE scope IS NOT NONE GROUP ALL",
        )
        assert (after[0]["count"] if after else 0) == 0, "a refused migrate stamped a scope somewhere"

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
            assert row[column] == value, (
                f"{shape}: the hostile {column} must survive byte-intact (store-ref §1.4), "
                f"got {row[column]!r}"
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
    self-denial reopening. GREEN after the build (role ASSERT dropped → touch succeeds)."""

    async def test_a_touch_succeeds_on_a_role_empty_legacy_row_after_the_drop(self) -> None:
        """⚠ RED at HEAD — seed a ``role=""`` legacy agent under the unbounded DDL, apply the current
        emitter, then the REAL ``AgentRegistry.touch`` on it SUCCEEDS (a bare heartbeat). At HEAD the
        role ASSERT still lands → the touch UPDATE re-validates ``role=""`` → RAISES → RED (right
        reason: the drop is unbuilt). RED the day the role ASSERT returns."""
        env = make_env(database=unique_database(), dim=_DIM)
        connection = await connect_admin(env)
        registry = AgentRegistry(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        try:
            await apply_ddl(connection, unbounded_agent_ddl(), url=env.url)
            await seed_agent_legacy(
                connection, row_id="role_empty", name="legacy-agent", session="wave7", role=""
            )
            await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
            try:
                updated = await registry.touch("legacy-agent", session="wave7", note="alive")
            except Exception as error:  # noqa: BLE001 - RED-at-HEAD surface (role ASSERT still lands)
                pytest.fail(
                    "RED-at-HEAD (right reason): touch on a role='' legacy row RAISED — the role "
                    "non-empty ASSERT is STILL on the store after the current emitter (the Q3 drop is "
                    f"unbuilt), so the whole-row heartbeat UPDATE self-denies (§4.4). engine: {error}"
                )
            assert updated.name == "legacy-agent", updated
            assert updated.last_note == "alive", updated
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
