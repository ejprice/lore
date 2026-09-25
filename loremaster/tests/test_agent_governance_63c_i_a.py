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

REVISION r3 (``contract-63c-i-a-r3``, 2026-09-24) — executes ``docs/design/2026-09-24-packet63c-
amendment-4.md`` §W (commit r3a = GATING items 1–6: A4-bis decision consumers, NF-2, MP-B, MP-F, MP-C,
MP-G; commit r3b = NON-GATING items 7–11). Per-item receipts: ``REPORT-contract-63c-i-a-r3.md``.

REVISION r4 (``contract-63c-i-a-r4``, 2026-09-24 — the LAST pre-build round, amendment-6 STOP-rule) —
executes ``docs/design/2026-09-24-packet63c-amendment-6.md`` §W items 1–6 with amendment-7 (FORK-D). In
THIS file: MP-2 (R-Q5-1's ``perturbed-bound`` population). Per-item receipts:
``REPORT-contract-63c-i-a-r4.md``.

BUILDER NOTES — docstring rows the contract cannot pin (amendment-1 N2 / amendment-2 §D items 14-15):
* amendment-4 MP-F: extend ``AgentRegistry.register``'s ``owner_principal_id`` docstring sentence
  ("A re-register does NOT re-stamp it (mint-once-on-create …)") to the PAIR — ``session_keep_id`` /
  ``scope`` / ``owner_agent`` are likewise never stamped on a re-register, for EVERY row (an ownerless or
  legacy row included); ownerless rows are ``migrate-governed``'s to stamp.
* amendment-4 MP-C: the refusal's id bound is the NAMED module constant
  ``principals._REFUSAL_ID_SAMPLE_SIZE`` (the R-Q5-1 pin READS it, and — r4, amendment-6 MP-2 — PERTURBS
  it) — never a literal slice; the builder writes exactly one line reading it. amendment-6 R-3: its
  DOCSTRING states WHY its value (a screenful; the full count is served beside the sample) — the value is
  not normative, so no pin can hold that sentence.
* amendment-4 A4-bis: ``AppContext._is_comms_charset_legal``'s body becomes ``return
  is_legal_identifier(value)`` (the server's ONE decision home; ``_validate_comms_charset`` and the
  ``_comms_traffic_line`` SKIP gate keep reading the home and are NOT rewired).
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
import sys
import types
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    AGENT_TABLE,
    _normalise_statement,
    access_token,
    agent_case,
    apply_ddl,
    build_principal_and_keep_stores,
    credentialed_app_context,
    frozen_asserted_agent_ddl,
    governed_overlay_ddl,
    identity_sweep_miss_message,
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
from loremaster.agents import AGENT_NAME_PATTERN, AgentRegistry, AgentRegistryError
from loremaster.governed import PROJECT_KEEP_KEY
from loremaster.store import surreal_schema
from loremaster.store._txn import SurrealStoreError, TxnDomainRejectionError
from lorerunes.pdp import keep_scope
from surrealdb import RecordID
from test_comms_schema import _HOSTILE_IDENTIFIERS

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

    # r4b-fix (amendment 13 §W-4, KB-RS1srvT CLOSED): the JOINER's argument SHAPE is parametrised. r4b drove
    # ONE shape (agent/session/role — parameter monoculture on the optional arguments), so a takeover
    # conditioned on an optional register argument survived the full suite (adversary-r4b RS1srvT:
    # ``… and task_id is not None``, 11486/0). ``every-optional`` sets ALL FOUR optional register arguments
    # the tool accepts (``model``, ``spawned_by``, ``task_id``, ``cadence``) — additive (no param deleted).
    @pytest.mark.parametrize(
        "joiner_register_extras",
        [
            pytest.param({}, id="required-only"),
            pytest.param(
                {
                    "model": "claude-opus-5-5",
                    "spawned_by": "lead-rs1",
                    "task_id": "rs1-task-7",
                    "cadence": "≤20m",
                },
                id="every-optional",
            ),
        ],
    )
    async def test_a_householded_joiners_re_register_of_the_keepers_agent_leaves_its_ownership_untouched(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, joiner_register_extras: dict[str, Any]
    ) -> None:
        """r4b (amendment-11 MP-A3, GATING) — ruling §2.2 row 2 ("a re-register leaves owner_principal /
        owner_agent / scope UNTOUCHED, from ANY caller") pinned at the OUTERMOST seam: the whole
        ``AppContext.comms(action="register")`` tool call. alice (the keeper) registers ``keeper-a`` in
        ``shared``; bob is householded into the session keep; bob re-registers ``keeper-a`` WITH THE SAME
        ROLE (a different role is refused earlier by the identity-conflict rule, which would make this pin
        blind — adversary-r4a's C-3 probe, first draft) → the row's three governed columns are
        BYTE-IDENTICAL to before. The row is read back AFTER the call returns, so every inner seam —
        registry, tool, render, any helper ``_comms_register`` calls — is covered by construction; this is
        why the ownership family's recession ENDS here (adversary-r4a RS1srv: the tool re-stamping
        ``owner_principal`` after a correct registry call survived the full suite). The registry-seam twin
        (``test_agent_registry.py::…::test_the_REAL_writer_never_re_stamps_a_stamped_row_from_a_DIFFERENT_
        householded_principal``) stays: it tells a builder WHICH seam broke.

        DATA invariance ONLY — the joiner's call outcome is deliberately NOT asserted: amendment-10 C-3's
        served REFUSAL of this re-register is i-b's (its own adversary + the #467 battery row), and this
        pin must stay green across that change. GREEN at HEAD (owner_agent / scope are NONE before and
        after — invariance holds) and on a correct build.

        P0 controls (the pin can SEE both halves): a FOREIGN principal (carol, not householded) is DENIED
        by SF-63-1 and leaves the row unchanged (the probe sees a refusal); the joiner's OWN fresh agent is
        created owned by the joiner (the probe sees a joiner's stamp — so a takeover would read bob, not a
        blind NONE); and the keeper's row is owned by alice beforehand (a takeover is distinguishable).

        r4b-fix (amendment 13 §W-4): ∀ JOINER ARGUMENT SHAPES — ``required-only`` and ``every-optional``
        (all four optional register arguments set). Control 2 registers the joiner's OWN agent with the SAME
        extras, so the ``every-optional`` shape is proven ACCEPTED end to end (a shape the tool refused
        outright would make the pin blind, since the re-register's outcome is not asserted).

        ⚠ KNOWN BOUND (adversary-r4b-fix RS1combo; amendment 16, recorded): two points of the joiner's 2⁴
        optional-argument lattice; a takeover conditioned on a MIXED argument shape (``… and task_id is not
        None and model is None``) survives the full suite. RE-OPEN TRIGGER: a register path found branching
        on an optional argument. CLOSURE-IF-REOPENED (the adversary's, UNMEASURED): four more params, each
        setting exactly ONE optional argument (kills every single-argument and every ``X set ∧ Y unset``
        condition with X's param). MOOT AT i-b: amendment-10 C-3's served refusal (a householded joiner may
        not re-register another principal's agent) closes the whole 2⁴ lattice at once, because no joiner
        re-register succeeds at all — i-b's author deletes this bound deliberately when C-3 lands."""
        from loremaster.governed import GovernedDenied

        projection = f"SELECT id, owner_principal, owner_agent, scope FROM {AGENT_TABLE} WHERE name = $n"
        async with credentialed_app_context(
            monkeypatch,
            tmp_path,
            principals={"alice": "member", "bob": "member", "carol": "member"},
            dim=_DIM,
        ) as world:
            ctx, admin = world["ctx"], world["admin_conn"]
            world["holder"]["email"] = world["emails"]["alice"]
            await ctx.comms(action="register", agent="keeper-a", session="shared", role="builder")
            keep = await ctx._keep_store.get_by_key("session:shared")  # noqa: SLF001
            assert keep is not None, "the keeper's register did not mint the session keep"
            await ctx._keep_store.add_household_member(  # noqa: SLF001
                keep_id=_bare(keep.id), member_email=world["emails"]["bob"]
            )
            before = await run(admin, projection, {"n": "keeper-a"})
            assert len(before) == 1, before
            assert str(before[0]["owner_principal"]) == f"principal:{world['pids']['alice']}", (
                f"CONTROL: the keeper's agent must be owned by the keeper before the joiner acts: {before!r}"
            )
            # CONTROL 1 — a FOREIGN principal is refused (SF-63-1) and writes nothing.
            world["holder"]["email"] = world["emails"]["carol"]
            with pytest.raises(GovernedDenied):
                await ctx.comms(action="register", agent="keeper-a", session="shared", role="builder")
            assert await run(admin, projection, {"n": "keeper-a"}) == before, (
                "CONTROL: a REFUSED foreign register mutated the keeper's agent row"
            )
            # CONTROL 2 — the joiner's OWN fresh agent is stamped as the joiner's.
            world["holder"]["email"] = world["emails"]["bob"]
            await ctx.comms(
                action="register",
                agent="joiner-b",
                session="shared",
                role="builder",
                **joiner_register_extras,
            )
            own_rows = await run(admin, projection, {"n": "joiner-b"})
            assert own_rows and str(own_rows[0]["owner_principal"]) == f"principal:{world['pids']['bob']}", (
                f"CONTROL: the joiner's own fresh agent must be owned by the joiner: {own_rows!r}"
            )
            # THE PIN — the joiner re-registers the KEEPER's agent (same role); outcome not asserted (i-b's).
            try:
                outcome = str(
                    await ctx.comms(
                        action="register",
                        agent="keeper-a",
                        session="shared",
                        role="builder",
                        **joiner_register_extras,
                    )
                )
            except Exception as error:  # noqa: BLE001 - a served refusal is i-b's to rule; DATA is pinned here
                outcome = f"raised {type(error).__name__}: {error}"
            after = await run(admin, projection, {"n": "keeper-a"})
            assert after == before, (
                f"a householded JOINER's re-register through the comms TOOL changed the keeper's agent row "
                f"— an ownership TAKEOVER through an ordinary tool call (ruling §2.2 row 2: owner_principal "
                f"/ owner_agent / scope are UNTOUCHED by a re-register, from ANY caller; amendment-11 MP-A3 "
                f"/ adversary-r4a RS1srv). before={before!r} after={after!r} joiner's call: {outcome[:300]!r}"
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
        """⚠ RED at HEAD — ONE IMPLEMENTATION, proven by MUTATION (A2): rebind EVERY module-level
        binding of THE ``keep_scope`` object (``patch_shared_object_everywhere`` — identity ALONE since
        r3 / amendment-4 MP-G, so ``from lorerunes import keep_scope as _format_keep_scope`` — a CORRECT
        aliased build — moves too; the r2 name-keyed sweep false-REDed it) and the STAMPED scope must
        move with it. A private ``f"keep:{…}"`` in the registry is a different object, is not patched,
        does not move, and reds here. BASELINE leg first (unpatched → the real formatter's output), so a
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
        )  # raises if lorerunes.keep_scope (its home) was not among the patched bindings
        mutated = await registry.register(
            "fixer-c", session="wave7", role="builder",
            owner_principal_id="alice_pid", session_keep_id="kpmut",
        )
        rows = await run(
            connection,
            f"SELECT scope FROM type::record('{AGENT_TABLE}', $id)",
            {"id": _bare(mutated.agent.id)},
        )
        assert rows[0].get("scope") == "mutkeep:kpmut", identity_sweep_miss_message(
            f"the STAMPED scope (A2: ONE formatter, lorerunes.keep_scope) got {rows!r}", patched
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


    # ------------------------------------------------------------------------------------------- #
    # r3 (amendment-4 MP-B / MP-F) — the registry's provenance invariants hold on the RE-REGISTER path
    # too, for EVERY row (not just the one a first register stamped): the quantifier law applied to A3
    # and to ruling §2.2's mint-once row. Adversary-r2 kill-pins KP-N2 / KP-N10, promoted.
    # ------------------------------------------------------------------------------------------- #

    @pytest.mark.parametrize(
        ("owner_principal_id", "session_keep_id"),
        [
            pytest.param("alice_pid", None, id="owner-without-keep"),
            pytest.param(None, "sessionkeep7", id="keep-without-owner"),
        ],
    )
    async def test_an_inconsistent_provenance_pair_is_refused_on_the_RE_REGISTER_path_too(
        self, registry_world: Any, owner_principal_id: str | None, session_keep_id: str | None
    ) -> None:
        """⚠ RED at HEAD (``session_keep_id`` kwarg absent → ``TypeError``) — amendment-4 MP-B: A3's
        XOR sits BEFORE ``_select_row`` on EVERY path. After a CONSISTENT first register, a RE-register
        of the same agent with either mixed pair is refused (``AgentRegistryError``) and the row is
        BYTE-IDENTICAL (full ``SELECT *``). Kills N2 (the XOR moved inside the CREATE branch — a mixed
        pair on re-register silently accepted; survived r2 at 2521/0)."""
        registry, connection = registry_world
        await registry.register(
            "fixer-b", session="wave7", role="builder",
            owner_principal_id="alice_pid", session_keep_id="sessionkeep7",
        )
        before = await _agent_rows(connection)
        assert len(before) == 1, before
        with pytest.raises(AgentRegistryError) as exc_info:
            await registry.register(
                "fixer-b", session="wave7", role="builder",
                owner_principal_id=owner_principal_id, session_keep_id=session_keep_id,
            )
        assert "nothing was written" in str(exc_info.value), str(exc_info.value)
        assert await _agent_rows(connection) == before, (
            "a refused (mixed-pair) RE-register changed the agent row — A3 refuses BEFORE _select_row "
            "on every path (amendment-4 MP-B)"
        )

    @pytest.mark.parametrize("prior_row", ["alpha-register", "legacy-seed"])
    async def test_a_credentialed_re_register_never_stamps_an_UNSTAMPED_row_mint_once_for_every_row(
        self, registry_world: Any, prior_row: str
    ) -> None:
        """⚠ RED at HEAD (``session_keep_id`` kwarg absent) — amendment-4 MP-F: MINT-ONCE ∀ rows. A row
        born OWNERLESS and UNSCOPED — an α register ``(None, None)`` or a ``seed_agent_legacy``
        pre-cutover row — re-registered with a CONSISTENT CREDENTIALED pair keeps ``owner_principal`` /
        ``owner_agent`` / ``scope`` byte-identical to what it was born with. Why ∀ rows: a
        re-register that heals ``scope`` + ``owner_agent`` but not ``owner_principal`` mints the REVERSE
        half-pair A3 forbids at create, and ``WHERE scope IS NONE`` then skips the row FOREVER; healing
        all three would let any credential CLAIM an ownerless name it never minted (a takeover door).
        Ownerless rows are ``migrate-governed``'s to stamp, never the re-registering caller's. Kills N10
        (the heal-scope build; survived r2 at 2521/0). The ``test_re_register_does_not_restamp_…`` pin
        above is this ∀'s guarded door (a row the first register stamped); this is the unguarded one."""
        registry, connection = registry_world
        if prior_row == "alpha-register":
            first = await registry.register(
                "fixer-b", session="wave7", role="builder",
                owner_principal_id=None, session_keep_id=None,
            )
            bare_id = _bare(first.agent.id)
        else:
            bare_id = await seed_agent_legacy(
                connection,
                row_id=AgentRegistry._agent_id("wave7", "fixer-b"),  # noqa: SLF001 - the production id mint
                name="fixer-b",
                session="wave7",
            )
        projection = f"SELECT owner_principal, owner_agent, scope FROM type::record('{AGENT_TABLE}', $id)"
        before = await run(connection, projection, {"id": bare_id})
        # FIXTURE precondition — the population MP-F names: an OWNERLESS, UNSCOPED row. (``owner_agent``
        # is not constrained here: whether the α CREATE stamps ``owner_agent = self`` is ruling §2.2's
        # business, pinned elsewhere; this pin asserts only that a RE-register changes NONE of the three.)
        assert before and before[0].get("owner_principal") is None and before[0].get("scope") is None, (
            f"FIXTURE: the {prior_row} row must be born ownerless and unscoped: {before!r}"
        )
        result = await registry.register(
            "fixer-b", session="wave7", role="builder",
            owner_principal_id="alice_pid", session_keep_id="sessionkeep7",
        )
        assert result.re_registered is True, "the credentialed call must take the RE-register path"
        after = await run(connection, projection, {"id": bare_id})
        assert after == before, (
            f"a credentialed RE-register STAMPED an unstamped ({prior_row}) row's governed columns — "
            f"mint-once is CREATE-only for EVERY row (ruling §2.2 row 2, amendment-4 MP-F); a "
            f"scope-without-owner row escapes the migrate's WHERE scope IS NONE forever. "
            f"before={before!r} after={after!r}"
        )


# =========================================================================== #
# amendment-4 MP-G (r3 item 6) — the SHARED mutation instrument ``patch_shared_object_everywhere`` is
# keyed on IDENTITY ALONE. Self-tests on SYNTHETIC modules (so they are build-independent and GREEN
# at HEAD): an ALIASED binding of THE object moves (the r2 name∧identity sweep false-REDed exactly
# this — a correct ``from lorerunes import keep_scope as _format_keep_scope`` build); a private copy
# (a DIFFERENT object) never moves, whatever it is named — including a copy wearing the SHARED NAME
# (the name-keyed ``_patch_everywhere`` copies' false CLEAR, now unrepresentable); the caller's
# EXPECTATION is enforced (a sweep that cannot find THE object at its stated home RAISES, #194).
# =========================================================================== #


def _mpg_shared_decision(value: str) -> bool:
    """THE shared object the synthetic modules bind (a stand-in for a ``lorerunes`` predicate)."""
    return bool(value)


def _mpg_private_copy(value: str) -> bool:
    """A PRIVATE copy — behaviourally identical, a DIFFERENT object."""
    return bool(value)


def _mpg_replacement(value: str) -> bool:
    """The mutation the sweep installs."""
    return not value


class TestThePatchSharedObjectInstrument63cIA:
    """amendment-4 MP-G rider 3 — three self-tests + the expectation leg + the refused-type leg. Each
    registers throwaway synthetic modules in ``sys.modules`` (``monkeypatch.setitem`` — undone at
    teardown) so the sweep's reach is observed on bindings whose shape the test chose."""

    @staticmethod
    def _synthetic_world(monkeypatch: pytest.MonkeyPatch) -> dict[str, types.ModuleType]:
        """``_mpg_home.shared`` IS the object (the home); ``_mpg_alias_user._aliased`` IS the object
        under ANOTHER name (a correct aliased build); ``_mpg_private_other.check`` is a private copy
        under another name; ``_mpg_private_same_name.shared`` is a private copy WEARING THE SHARED
        NAME (the name-keyed false-clear shape)."""
        modules = {
            "_mpg_home": ("shared", _mpg_shared_decision),
            "_mpg_alias_user": ("_aliased", _mpg_shared_decision),
            "_mpg_private_other": ("check", _mpg_private_copy),
            "_mpg_private_same_name": ("shared", _mpg_private_copy),
        }
        world: dict[str, types.ModuleType] = {}
        for module_name, (binding, value) in modules.items():
            module = types.ModuleType(module_name)
            setattr(module, binding, value)
            monkeypatch.setitem(sys.modules, module_name, module)
            world[module_name] = module
        return world

    def test_an_ALIASED_binding_of_the_shared_object_MOVES(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The MP-G receipt, inverted into a pin: a module binding THE object under a different name
        is rebound. RED on the r2 name∧identity sweep (it skipped every binding not named
        ``attribute``)."""
        world = self._synthetic_world(monkeypatch)
        patched = patch_shared_object_everywhere(
            monkeypatch, "shared", _mpg_shared_decision, _mpg_replacement, expect_in=("_mpg_home",)
        )
        assert world["_mpg_alias_user"]._aliased is _mpg_replacement, identity_sweep_miss_message(
            "an ALIASED module-level binding of THE shared object", patched
        )
        assert "_mpg_alias_user._aliased" in patched, patched
        assert world["_mpg_home"].shared is _mpg_replacement, patched

    def test_a_private_copy_under_ANOTHER_name_does_NOT_move(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A DIFFERENT object is never rebound — the property every sharing pin rests on (a private
        copy must stay put so the pin that watches its behaviour can red)."""
        world = self._synthetic_world(monkeypatch)
        patched = patch_shared_object_everywhere(
            monkeypatch, "shared", _mpg_shared_decision, _mpg_replacement, expect_in=("_mpg_home",)
        )
        assert world["_mpg_private_other"].check is _mpg_private_copy, patched
        assert not any(entry.startswith("_mpg_private_other.") for entry in patched), patched

    def test_a_private_copy_WEARING_THE_SHARED_NAME_does_NOT_move(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The name-keyed instruments' FALSE CLEAR (amendment-3 F-3), now unrepresentable: a private
        copy bound under the SHARED NAME is not rebound, so a build that shares nothing cannot pass a
        sharing pin by having its copy moved for it. RED on any name-keyed sweep."""
        world = self._synthetic_world(monkeypatch)
        patched = patch_shared_object_everywhere(
            monkeypatch, "shared", _mpg_shared_decision, _mpg_replacement, expect_in=("_mpg_home",)
        )
        assert world["_mpg_private_same_name"].shared is _mpg_private_copy, (
            f"the sweep rebound a PRIVATE copy because it wore the shared name — a name-keyed reach "
            f"(the false clear MP-G exists to kill); patched: {patched}"
        )
        assert "_mpg_private_same_name.shared" not in patched, patched

    def test_the_callers_EXPECTATION_is_enforced_the_sweep_raises_if_the_home_was_not_patched(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``attribute`` + ``expect_in`` are the caller's EXPECTATION: naming a home that does not
        hold THE object under ``attribute`` RAISES (the mutation could not land where the caller
        said it lives — #194), both for a module that holds a private copy under that name and for a
        module that holds THE object under a DIFFERENT name. CONTROL: the true home does not raise
        (the first self-tests)."""
        self._synthetic_world(monkeypatch)
        with pytest.raises(AssertionError, match="expected home"):
            patch_shared_object_everywhere(
                monkeypatch, "shared", _mpg_shared_decision, _mpg_replacement,
                expect_in=("_mpg_private_same_name",),
            )
        with pytest.raises(AssertionError, match="expected home"):
            patch_shared_object_everywhere(
                monkeypatch, "shared", _mpg_shared_decision, _mpg_replacement,
                expect_in=("_mpg_alias_user",),
            )

    @pytest.mark.parametrize("interned", ["agent", 7, None, ("a",)], ids=["str", "int", "None", "tuple"])
    def test_an_interned_value_type_is_REFUSED_loudly(
        self, monkeypatch: pytest.MonkeyPatch, interned: object
    ) -> None:
        """Identity over an interned / value-shared object says nothing about sharing and would
        rebind unrelated bindings across the interpreter — the instrument refuses it (TypeError)
        rather than clobbering ``sys.modules``."""
        with pytest.raises(TypeError, match="IDENTITY"):
            patch_shared_object_everywhere(monkeypatch, "x", interned, object(), expect_in=())


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

    @staticmethod
    def _integers_stated_beside_the_seeded_identifiers(
        reason: str, *, before: list[dict[str, Any]], full_count: int
    ) -> list[int]:
        """Every integer ``reason`` states once every IDENTIFIER the fixture seeded (each ``before`` row's
        string values and record ids, longest first), the FULL count (every occurrence) and the section
        citations (``§2.1``) are stripped. Purely-digit seeded strings are NOT stripped — they would erase
        the very tokens the callers read. r4b-fix: extracted from ``test_R_Q5_1_…`` unchanged, so the F-1
        leg and the birth-value leg read ONE residue."""
        seeded_identifiers: set[str] = set()
        for row in before:
            for value in row.values():
                if isinstance(value, RecordID):
                    seeded_identifiers.update((str(value), str(value.id)))
                elif isinstance(value, str):
                    seeded_identifiers.add(value)
        residue = reason
        for seeded in sorted(seeded_identifiers, key=len, reverse=True):
            if seeded and not seeded.isdigit():
                residue = residue.replace(seeded, " ")
        # Section citations FIRST: stripping the count first turns "§2.1" into "§ .1" when the count is 2 (the
        # ``below-cap`` population) and leaves a phantom "1" — a correct refusal false-REDs (r4b-fix SAT leg,
        # measured on both reference shapes before this order was fixed).
        residue = re.sub(r"§\d+(?:\.\d+)*", " ", residue)
        residue = re.sub(rf"\b{full_count}\b", " ", residue)
        return [int(token) for token in re.findall(r"\d+", residue)]

    # DUAL (r3, amendment-4 MP-C): the r2 pin (ONE fixture, 2 traps, "EVERY trap id named") is RE-KEYED
    # to three populations. Virtue kept: at 2 traps every id is still named (below-cap leg); the r2
    # assertion "every id named" is INVERTED above the cap (bound + 15 → exactly ``bound`` named), because
    # at N > cap it contradicted the ruled bound (arithmetic alignment — adversary-r2 MP-C / N3).
    # r4 (amendment-6 MP-2): a FOURTH population, ``perturbed-bound`` — the mutation leg (additive; no pin
    # deleted, so no DUAL row).
    @pytest.mark.parametrize("trap_population", ["below-cap", "at-cap", "above-cap", "perturbed-bound"])
    async def test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent(
        self, agent_migrate_world: Any, trap_population: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD (finding #470 / F10) — §2.1's ROW precondition: an ``agent`` row with
        ``scope IS NONE`` but ``owner_principal IS NOT NONE`` means a multi-principal or half-applied
        store, so the migrate REFUSES (``refused=True``, ZERO stamped). At HEAD ``_migrate_agent_owner``
        is owner-keyed and refuses ONLY on operator ambiguity, so it does NOT refuse this store → RED.

        r2 (amendment-2 §D item 6 — MP-7 / MP-11 / sidecar F8): the refusal is BYTE-INERT and TEACHES.
        The FULL ``SELECT *`` of the table is identical before and after (not a ``scope`` proxy — WB10
        stamped owners FIRST, then refused, and a scope-only observation missed it); the reason names
        the COUNT beside its noun, the offending rows (WB8), and the remedy (§6: adjudicate BY HAND).
        The CONTROL (same store WITHOUT the trap rows) is the sibling test below.

        r3 (amendment-4 MP-C — "naming the count and the rows (ids, bounded)", ruling §6): the id BOUND
        is a NAMED constant, ``principals._REFUSAL_ID_SAMPLE_SIZE`` (no literal ``[:10]``), READ here —
        derived, never restated. The reason names the FULL count and EXACTLY ``min(bound, count)`` of the
        trap ids. Three populations, so the arithmetic cannot align (CLAUDE.md FIXTURES MUST
        DISCRIMINATE): ``below-cap`` = 2 (every id named; a count of 2 cannot be satisfied by a stray
        "1" such as the "§2.1" citation — WB9), ``at-cap`` = the bound (every id named — the boundary),
        ``above-cap`` = bound + 15 (only ``bound`` ids named — kills N3, the unbounded
        ``', '.join(every_id)`` that survived r2 at 2521/0, and kills a build that names NONE above the
        cap). Trap ids are fixed-width (``owned_trap_000``…) so no id is a substring of another.

        r4 (amendment-6 MP-2 — "prove sharing by MUTATION" applied to a constant): ``perturbed-bound``
        PATCHES ``principals._REFUSAL_ID_SAMPLE_SIZE`` to a value ≠ its birth value (3, or 4 if the build
        chose 3) and seeds bound + 15 traps: the reason must name the FULL count and EXACTLY the PATCHED
        number of ids. A build that defines the constant but slices with a restated literal (``[:10]``)
        holds ONE policy in TWO sources that agree only at birth — invisible to a read, visible to this
        perturbation (adversary-r3 X2 / KP-X2). R-3 (amendment-6): the VALUE is not normative — pinned
        only as a positive ``int`` that is READ; no upper ceiling pin (a ``≤ N`` here would be a second
        magic number restating a design choice in the wrong home). The count is asserted INDEPENDENTLY of
        the id sample (its own assertion below), so the reader loses nothing at any bound.

        r4a (amendment-9 MP-R4-7 — PX2, the PROSE twin of the bound; the P8d rule inside the served refusal):
        under ``perturbed-bound``, after stripping every identifier the fixture seeded, the full count and
        section citations (``§2.1``), the reason carries NO integer equal to the constant's BIRTH value (read
        BEFORE patching — derived, never a literal in this test). A builder writing *"(first 10 ids shown)"*
        beside a constant-read slice serves a false number the day the constant changes — adversary-r4 PX2
        passed 2905/0 because this leg checked only ``len(named)``. Prose describing the bound is DERIVED
        from the constant (``f"first {shown} of {count} ids shown"``, shown = the ids ACTUALLY named) or
        absent, never restated.
        r4b (amendment-11 MP-A2): r4a's sample-size PHRASE leg is DELETED (it refused the correct prose
        *"(first 3 of 18 ids shown)"* — adversary-r4a SH1; DUAL comment at its old site), and every count
        this fixture introduces is kept off the birth value (a correct refusal may state any of them).
        ⚠ KNOWN BOUND (amendment-11 PX2w, accepted): the leg is ∀ over DIGIT spellings only — the birth value
        restated IN WORDS (*"first ten ids shown"*) survives it (adversary-r4a PX2w, full-suite survivor).
        RE-OPEN TRIGGER: a served refusal found restating a bound in words.
        r4b-fix (amendment 13 §F-1, as amended by amendment 14 — reading B): a served count must describe the
        set it names. In EVERY population, after stripping every seeded identifier and the section citations,
        every integer the reason states is a TRUE count of one of the fixture's sets — ``admitted`` =
        {len(shown), count, count − len(shown), legacy_count, count + legacy_count}, derived per population —
        and the constant's birth value is kept OUT of that set wherever ``birth ≠ len(shown)`` (wherever
        "N = the constant" would BE a lie). This kills adversary-r4b PXlie, ``(first 10 of 2 ids shown)``
        below the cap, for every birth > 2. ⚠ KNOWN BOUND (amendment 14, accepted): a lie that coincides with
        a DIFFERENT true count — ``(first 3 of 2 ids shown)`` when ``legacy_count == 3`` — is admitted; no
        honest build derives N from the legacy count, and the only plausible wrong derivation (the constant)
        is guarded out. RE-OPEN TRIGGER: a served refusal found stating a sample size that equals another
        fixture count and not ``len(shown)``.
        r4b-fix2 (amendment 16 §W-1; adversary-r4b-fix F-A1, its fix landed verbatim): ``admitted`` ALSO
        carries the result's own TRUE counts — rows ALREADY migrated, rows STAMPED (``result.backfilled``)
        and the scanned total (count + legacy + already) — so a correct refusal stating *"0 already
        migrated"* or *"no row was stamped (0 rows)"* is not refused; none can be the birth value.
        ⚠ KNOWN BOUND (adversary-r4b-fix F-A1): the admitted set is the agent-table counts and the result's
        own counts; a true count of another table (principals, keeps) is refused. RE-OPEN TRIGGER: a correct
        refusal stating a non-agent count.

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
        id_bound = principals._REFUSAL_ID_SAMPLE_SIZE  # the NAMED bound (MP-C) — derived, never restated
        assert isinstance(id_bound, int) and not isinstance(id_bound, bool) and id_bound >= 1, (
            f"id bound must be a positive int: {id_bound!r}"
        )
        birth_bound = id_bound  # r4a (MP-R4-7): the BIRTH value, read BEFORE any perturbation
        if trap_population == "perturbed-bound":  # amendment-6 MP-2: the slice must FOLLOW the constant
            # never the birth value: a no-op perturbation proves nothing
            id_bound = 3 if id_bound != 3 else 4
            monkeypatch.setattr(principals, "_REFUSAL_ID_SAMPLE_SIZE", id_bound)
        trap_count = {
            "below-cap": 2,
            "at-cap": id_bound,
            "above-cap": id_bound + 15,
            "perturbed-bound": id_bound + 15,
        }[trap_population]
        legacy_count = 3
        if trap_population == "perturbed-bound":
            # r4b (amendment-11 MP-A2 — SATISFIABILITY): every COUNT this fixture introduces is kept OFF the
            # birth value, so a correct refusal that states one of them ("first 3 of 18 ids shown", "3 legacy
            # rows") can never trip the birth-value leg below (arithmetic alignment — CLAUDE.md FIXTURES MUST
            # DISCRIMINATE, axis 3). The builder picks the birth value (R-3: not normative), so the guard
            # is derived from it, never assumed.
            # r4b-fix (amendment 13 §W-1, adversary-r4b F-2 — SATISFIABILITY): the DERIVED remainder
            # ``trap_count − id_bound`` ("…, 15 more") is a count a correct refusal may state too, so it is
            # kept off the birth value as well (birth 15 + remainder prose was a correct build refused here).
            while trap_count in (birth_bound, birth_bound - legacy_count, birth_bound + id_bound):
                trap_count += 1
            while legacy_count in (birth_bound, birth_bound - trap_count):
                legacy_count += 1
            fixture_counts = {
                id_bound, trap_count, legacy_count, trap_count + legacy_count, trap_count - id_bound
            }
            assert birth_bound not in fixture_counts, (
                f"fixture self-check: a fixture count {sorted(fixture_counts)} equals the birth value "
                f"{birth_bound}"
            )
        # r4b-fix (amendment 13 §F-1 / amendment 14 — reading B): the counts a CORRECT refusal may state, per
        # population — every one a TRUE count of a set the fixture seeds. ``shown_count`` is the number of ids
        # the refusal must name (the assertion below pins it), so a stated sample size must equal it.
        shown_count = min(id_bound, trap_count)
        if birth_bound != shown_count:
            # Wherever "N = the constant" would be a LIE, keep the constant's birth value off every admitted
            # count (``below-cap``: move legacy off ``birth`` and ``birth − count``; ``perturbed-bound``: the
            # r4b / F-2 loops above already did it). ``at-cap`` / ``above-cap``: shown == birth, legitimately.
            while legacy_count in (birth_bound, birth_bound - trap_count):
                legacy_count += 1
        admitted_counts = {
            shown_count,
            trap_count,
            trap_count - shown_count,
            legacy_count,
            trap_count + legacy_count,
        }
        assert birth_bound == shown_count or birth_bound not in admitted_counts, (
            f"fixture self-check: the birth value {birth_bound} is an admitted TRUE count "
            f"{sorted(admitted_counts)} in a population where it is not len(shown)={shown_count} — the F-1 "
            f"leg could not tell 'N = the constant' from a true count"
        )
        await self._seed_clean_legacy(connection, count=legacy_count)
        trap_ids = [f"owned_trap_{trap_index:03d}" for trap_index in range(trap_count)]
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
        assert re.search(rf"\b{trap_count}\s+(?:agent\s+)?rows?\b", reason), (
            f"the refusal must NAME the FULL count of owned-but-unscoped rows beside its noun "
            f"('{trap_count} agent row(s)'), got {reason!r}"
        )
        named = [trap_id for trap_id in trap_ids if trap_id in reason]
        expected_named = min(id_bound, trap_count)
        assert len(named) == expected_named, (
            f"the refusal must name EXACTLY min(_REFUSAL_ID_SAMPLE_SIZE={id_bound}, count={trap_count}) "
            f"= {expected_named} of the offending row ids (§6 'ids, bounded' — every id up to the bound, "
            f"never an unbounded list above it); it named {len(named)}"
            + (
                " — the bound was PATCHED, so the slice does not read _REFUSAL_ID_SAMPLE_SIZE at CALL time "
                "(a restated literal, or a value captured at def time — amendment-6 MP-2 / X2; amendment-9 "
                "R-4)"
                if trap_population == "perturbed-bound"
                else ""
            )
            + f": {reason[:400]!r}"
        )
        assert "by hand" in reason.lower(), (
            f"the refusal must TEACH the remedy (§2.1/§6: adjudicate the rows BY HAND before migrating) "
            f"— an operator at cutover reads this first. got {reason!r}"
        )
        # r4a (amendment-9 MP-R4-7) / r4b (amendment-11 MP-A2): strip every IDENTIFIER the fixture seeded —
        # derived from ``before`` snapshot (each row's string values and record ids, longest first so no
        # seeded string is left half-stripped), never a hand-list of columns — so a correct refusal naming a
        # row's id, name or owner (``other_principal_10`` at a birth value of 10) cannot false-RED.
        # Purely-digit strings are NOT stripped (they would erase the very token these legs read).
        # r4b-fix (amendment 13 §F-1 / amendment 14): the residue is now computed in EVERY population (it fed
        # only ``perturbed-bound`` before — additive: no leg deleted, so no DUAL row for the move).
        # adversary-r4b-fix F-A1 (SAT, F-2's class): the result's own counts are TRUE counts a correct refusal
        # may state — rows ALREADY migrated (scope set; derived from ``before``, where ``SELECT *`` omits a
        # NONE column), rows STAMPED (``result.backfilled``, asserted 0 above: the ruling's own "ZERO
        # stamped"), and the scanned total. None can be the birth value (birth >= 1; the total is count +
        # legacy + already).
        already_migrated_count = sum(1 for row in before if row.get("scope") is not None)
        admitted_counts |= {
            already_migrated_count,
            result.backfilled,
            trap_count + legacy_count + already_migrated_count,
        }
        assert birth_bound == shown_count or birth_bound not in admitted_counts, (
            f"fixture self-check: the birth value {birth_bound} is an admitted TRUE count "
            f"{sorted(admitted_counts)}"
        )
        stated_integers = self._integers_stated_beside_the_seeded_identifiers(
            reason, before=before, full_count=trap_count
        )
        untrue_counts = sorted(set(stated_integers) - admitted_counts)
        assert not untrue_counts, (
            f"the refusal states {untrue_counts} — not a TRUE count of any set this fixture seeds "
            f"(admitted {sorted(admitted_counts)}: the {shown_count} ids shown, the {trap_count} offending "
            f"rows, the {trap_count - shown_count} not shown, the {legacy_count} clean legacy rows, their "
            f"{trap_count + legacy_count} total). A served count must describe the set it names — the sample "
            f"size is the number of ids ACTUALLY named, min(_REFUSAL_ID_SAMPLE_SIZE, count), never the "
            f"constant itself (amendment 13 §F-1 / adversary-r4b PXlie: '(first 10 of 2 ids shown)'): "
            f"{reason[:400]!r}"
        )
        if trap_population == "perturbed-bound":  # r4a (amendment-9 MP-R4-7): the PROSE follows the constant
            assert birth_bound not in stated_integers, (
                f"the refusal PROSE restates the BIRTH sample size {birth_bound} while the slice follows the "
                f"PATCHED constant {id_bound} — two sources of one policy, in served text (amendment-9 "
                f"MP-R4-7 / adversary-r4 PX2). Derive the number from _REFUSAL_ID_SAMPLE_SIZE at call time "
                f"(f\"first {{shown}} of {{count}} ids shown\", shown = the ids ACTUALLY named) or leave it "
                f"out: {reason[:400]!r}"
            )
            # DUAL (r4b-fix, amendment 13 §F-1 (i) — RE-KEYED prose, D5): this message taught
            # ``first {sample_size} of {count}`` — read as N = the CONSTANT, it is adversary-r4b PXlie's
            # form. It now teaches ``first {shown} of {count}``. The assertion is unchanged.
            # DUAL (r4b, amendment-11 MP-A2 — DELETED, not re-keyed): r4a's SAMPLE-SIZE PHRASE leg (the
            # ``first N`` / ``N … shown`` / ``showing N`` regex asserting each stated size == the PATCHED
            # bound). Virtue it carried: a stated sample size that is neither the birth value NOR the patched
            # bound (a THIRD number) was refused. Dropped DELIBERATELY: it read the TOTAL in the correct,
            # derived prose "(first 3 of 18 ids shown)" as a sample size and REFUSED a correct build
            # (adversary-r4a SH1 — a satisfiability defect; the builder may not edit tests), and every patch
            # to a phrase regex is another phrase a correct build can trip. The birth-value leg above is what
            # kills PX2 (measured, adversary-r4a §4.1); a third, unrelated wrong number is not a two-sources-
            # of-one-policy defect and is not ruled.

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
            # Token == executed under the SHARED F5 leg-2 rule (``_normalise_statement``) — never widened.
            token_statement = _normalise_statement(str(getattr(write.exempt, "statement", "")))
            executed = _normalise_statement(str(write.statement or ""))
            assert token_statement == executed, (
                "the migrate-governed token's GOLDEN statement is not the statement the migrate "
                f"EXECUTED (statement-scoped exempt — leg 2): token={token_statement!r} "
                f"executed={executed!r}"
            )
            _assert_the_backfill_statement_shape(executed)


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



def _statement_shape(statement: str) -> str:
    """amendment-4 R-6 (r3 item 10) — NORMALISE, don't widen: the §6 SHAPE asserts read the executed
    statement through the shared leg-2 whitespace rule, then strip ONE trailing ``;`` and collapse
    ``\\s*=\\s*`` to `` = ``, so a correct build writing ``WHERE scope IS NONE;`` or ``SET scope=$scope``
    is not refused for a spelling. The token-vs-executed EQUALITY above is untouched (it is F5's rule)."""
    shaped = _normalise_statement(statement).rstrip()
    shaped = shaped.removesuffix(";").rstrip()
    return re.sub(r"\s*=\s*", " = ", shaped)


def _assert_the_backfill_statement_shape(statement: str) -> None:
    """§6: the agent backfill is ONE scope-keyed UPDATE that SETs all three governed columns — asserted
    on the R-6-normalised shape."""
    shaped = _statement_shape(statement)
    upper = shaped.upper()
    assert upper.startswith(f"UPDATE {AGENT_TABLE.upper()} ") and upper.endswith("WHERE SCOPE IS NONE"), (
        f"the agent backfill must be ONE scope-keyed UPDATE (§6), got {statement!r}"
    )
    for column in ("owner_principal", "owner_agent", "scope"):
        assert f"{column} = " in shaped, (
            f"the agent backfill must SET all three governed columns (§6); {column!r} is not set in "
            f"{statement!r}"
        )


class TestTheBackfillShapeAssertNormalisesSpellingNeverWidens63cIA:
    """r3 item 10 (amendment-4 R-6) — the shape assert's CONTROLS, build-independent. Spelling variants
    of the CORRECT statement pass (trailing ``;``, ``col=$v`` without spaces, extra whitespace); the WRONG
    statements still fail (owner-keyed WHERE, a missing column, a missing WHERE — WB2's shape)."""

    _CORRECT = (
        "UPDATE agent SET owner_principal = type::record('principal', $owner), owner_agent = id, "
        "scope = $scope WHERE scope IS NONE"
    )

    @pytest.mark.parametrize(
        "variant",
        [
            pytest.param(_CORRECT, id="canonical"),
            pytest.param(_CORRECT + ";", id="trailing-semicolon"),
            pytest.param(_CORRECT.replace(" = ", "="), id="no-spaces-around-equals"),
            pytest.param(_CORRECT.replace(" ", "  ") + " ;", id="doubled-whitespace-and-spaced-semicolon"),
        ],
    )
    def test_a_correct_statement_passes_in_any_spelling(self, variant: str) -> None:
        _assert_the_backfill_statement_shape(variant)

    @pytest.mark.parametrize(
        "wrong",
        [
            pytest.param(
                _CORRECT.replace("WHERE scope IS NONE", "WHERE owner_principal IS NONE"), id="owner-keyed"
            ),
            pytest.param(_CORRECT.replace("owner_agent = id, ", ""), id="two-of-three-columns"),
            pytest.param(_CORRECT.replace(" WHERE scope IS NONE", ""), id="no-where-WB2"),
        ],
    )
    def test_a_wrong_statement_still_fails(self, wrong: str) -> None:
        with pytest.raises(AssertionError):
            _assert_the_backfill_statement_shape(wrong)


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
        """POSITIVE CONTROL (amendment-1 E2, as corrected by amendment-3 E2-bis) — the leg CAN see a
        store denial through ``touch``: seed ``role=""`` under ``unbounded_agent_ddl()``, apply the
        CURRENT emitter to declare every column ``touch`` writes, then apply ``frozen_asserted_agent_ddl()``
        LAST — the frozen capture is the ONLY source of the refusing ASSERT (``DEFINE FIELD OVERWRITE`` is
        a full replace; store-ref §1.1/§1.2) — then the REAL ``touch`` → the driver's typed store rejection
        (``SurrealStoreError`` matching ``(assert violation)``) and the row is byte-identical (zero rows
        changed). GREEN at HEAD AND after the build. What it KILLS (E2-bis(2) — every write form
        re-validates the whole record, store-ref §1.4, so a "validation-skipping UPDATE" is not a
        constructible build): (i) a ``touch`` that stops WRITING the row (an in-memory/cached heartbeat, an
        early return on a legacy-shaped row); (ii) a ``touch`` that swallows the driver's
        ``SurrealStoreError`` into a success (the narrowed-``except`` class); (iii) a ``touch`` that writes
        a different row or table. The Leg B C-control's twin, through the heartbeat seam."""
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


class TestAHostileNamedLegacyAgentCannotReRegisterButStillTouches63cIA:
    """amendment-4 NF-2 (reading a — the MOVE is ∀ calls): ``register`` refuses a hostile ``name`` /
    ``session`` BEFORE ``_select_row`` on EVERY path — first register and RE-register alike — so a
    legacy row carrying a hostile identity (seeded under ``unbounded_agent_ddl()``, the DD-3.c survivor
    population) can NEVER be re-minted through the writer whose job after the MOVE is to refuse that
    shape. Its SURVIVOR virtue is the ROW — reads, ``touch``, migrate, drain — never a right to
    re-register (the teaching already says *respawns register a fresh name*). Production cost NIL:
    through ``lore_comms`` a hostile name is refused at ``_validate_comms_charset`` before the registry.

    Parametrised over the SHARED ``_HOSTILE_IDENTIFIERS`` corpus × {name, session} (one corpus, no
    narrower local copy; the two fields carry different legal values so a per-field build is seen).

    RED at HEAD for the RIGHT reason: HEAD's register has no app-side check, so the re-register reaches
    its whole-row UPDATE, which the STILL-ASSERTED current emitter refuses in the STORE
    (``SurrealStoreError`` — not the teaching ``AgentRegistryError``); and the survivor ``touch`` is
    refused by the same store ASSERT. GREEN on the build (refused app-side, byte-inert; the touch
    lands because the Q3 DROP removed the name/session ASSERTs)."""

    @pytest.mark.parametrize("field", ["name", "session"])
    @pytest.mark.parametrize("hostile_value", _HOSTILE_IDENTIFIERS)
    async def test_a_hostile_legacy_row_is_refused_on_re_register_and_still_touches(
        self, field: str, hostile_value: str
    ) -> None:
        identity = {"name": "legacy-agent", "session": "wave7"}
        identity[field] = hostile_value
        env = make_env(database=unique_database(), dim=_DIM)
        connection = await connect_admin(env)
        registry = AgentRegistry(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        try:
            await apply_ddl(connection, unbounded_agent_ddl(), url=env.url)
            await seed_agent_legacy(
                connection,
                row_id=AgentRegistry._agent_id(identity["session"], identity["name"]),  # noqa: SLF001
                name=identity["name"],
                session=identity["session"],
            )
            await apply_ddl(connection, surreal_schema.generate_agent_ddl(), url=env.url)
            before = await _agent_rows(connection)
            assert len(before) == 1, before
            try:
                await registry.register(identity["name"], session=identity["session"], role="builder")
            except AgentRegistryError as error:
                message = str(error)
            except SurrealStoreError as error:  # RED-at-HEAD surface ONLY
                pytest.fail(
                    "RED-at-HEAD (right reason): the hostile legacy row's RE-register reached the store "
                    "and was refused by the STILL-PRESENT charset ASSERT — the register MOVE is unbuilt "
                    f"(amendment-4 NF-2 wants an app-side refusal before _select_row). engine: {error}"
                )
            else:
                pytest.fail(
                    f"a legacy row with a hostile {field} ({hostile_value!r}) was RE-REGISTERED — the MOVE "
                    f"is ∀ calls (amendment-4 NF-2): refuse before _select_row on every path"
                )
            assert field in message, f"the refusal does not name the FIELD {field!r}: {message!r}"
            assert AGENT_NAME_PATTERN.pattern in message, f"the refusal does not state the RULE: {message!r}"
            assert "register again" in message, f"the refusal does not teach the REMEDY: {message!r}"
            assert await _agent_rows(connection) == before, (
                "a refused hostile RE-register changed the agent table (byte-inert: zero new rows, the "
                "legacy row untouched)"
            )
            try:
                touched = await registry.touch(identity["name"], session=identity["session"], note="alive")
            except SurrealStoreError as error:  # RED-at-HEAD surface ONLY
                pytest.fail(
                    "RED-at-HEAD (right reason): the SURVIVOR leg — the hostile legacy row could not "
                    "heartbeat because the store charset ASSERT still re-validates the whole row on the "
                    f"touch UPDATE (the Q3 DROP is unbuilt). engine: {error}"
                )
            assert touched.name == identity["name"] and touched.last_note == "alive", touched
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
