"""Contract — packet 63c wave i-a, the a28 FIX-PASS contract (amendments 26–29). Authored by
``contract-63c-i-a-a28`` (Opus 5.5 contract author — CONTRACT TESTS ONLY, no production code). The build
under repair is the checkpoint ``169925f`` (cold audit ``REPORT-coldaudit-63c-i-a-2.md`` @ ``8ae642f``:
NO-GO).

THE SPEC IS THE RULINGS (later wins):
* ``docs/design/2026-09-26-packet63c-amendment-26.md`` — the message leg's dangling + half-pair refusal is ONE
  refusal, dangling first (the audit's RS-1 fixture, verbatim).
* ``docs/design/2026-09-26-packet63c-amendment-27.md`` (``40c188d``) — FORK-1 (``backfilled`` = the rows the
  UPDATE stamped, ∀ legs, one byte-diff pin over the derived ``_migrate_legs``) and FORK-2 (ORDER → dangling →
  half-pairs in ONE refusal; the verb-level §2.1 refusal stays a separate, earlier answer).
* ``docs/design/2026-09-26-packet63c-amendment-28.md`` (``eb75f57`` + §Addendum ``17c52b7``) — §F-1 NO race
  compensation (the RS-2 8-way pin + the sequential leg; the race pin's winner is a same-principal HANDLER
  register that FOUND the keep, the ownerless winner only the tokenless control — Addendum A1); §F-2 the ORDER
  principal → READ-ONLY SF-63-1 gate → preflight → mint → post-mint re-check → register (the RS-3 pin: zero
  registry reads, byte-identical denials); A2 (an unexpected ``INFO FOR DB`` / precondition-row shape fails
  CLOSED); A4 (the refusal receipt serves the precondition's measured counts; the docstring says what the code
  does — FK-a28-1, Reading A pending a ruling); A5 (the message UPDATE self-guards on the SENDER).
* ``docs/design/2026-09-26-packet63c-amendment-29.md`` (``a92d33e``) — RS-5 (a concurrent identical first
  register is served the registry's result, never a raw ``TxnDomainRejectionError``) and F-8 (each count is
  attributed INSIDE its own clause).

STORE LAW (``docs/reference/surrealdb-31-capabilities.md`` — cited, never re-transcribed): §1.4 (legacy /
half-pair / dangling rows are SEEDED under the DDL, never constructed through a writer), §2 (``SELECT *``
omits
a NONE column, so byte-identity compares whole rows; ``str(RecordID)`` decodes ids), §5 (a concurrency pin
holds at ≥8-way and is cleared only by 20 consecutive greens — the round loops below run 20 rounds per
invocation, and the report records 20 consecutive invocations on the reference), §6.4 (a dangling sender
dereferences to NONE). Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500), one unique database per world,
reaped. No skip marker.
"""

from __future__ import annotations

import asyncio
import contextvars
import dataclasses
import inspect
import re
import typing
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Literal

import loremaster.agents as agents_module
import loremaster.governed as governed_module
import pytest
import test_fixwave_a19a_63c_i_a as a19a  # module-qualified: its Test* classes must not be re-collected here
from _governed_contract import (
    AGENT_TABLE,
    MEMORY_TABLE,
    MESSAGE_TABLE,
    credentialed_app_context,
    patch_shared_object_everywhere,
    seed_agent_governed,
    seed_agent_legacy,
    seed_memory_legacy,
    seed_message_legacy,
)
from _surreal_harness import run
from loremaster.agents import (
    AgentIdentityConflictError,
    AgentRegisterResult,
    AgentRegistry,
    AgentRegistryError,
)
from loremaster.governed import GovernedDenied, MigrateGovernedResult
from loremaster.store._txn import SurrealStoreError
from lorerunes.pdp import keep_scope
from pydantic import BaseModel
from surrealdb import RecordID
from test_fixwave_a19_63c_i_a import (
    _MIGRATE_TABLES,
    _redirect_the_shared_preconditions,
    _seed_foreign_principals,
    _snapshot,
)
from test_fixwave_a19_63c_i_a import (
    _bare as _bare,  # noqa: PLC0414 - an EXPLICIT re-export: a28b's AST-equal K-probes read `a28._bare`
)

from loremaster import principals

if TYPE_CHECKING:
    # The STATIC reference that owns this file's pending pins in scripts/pending_contracts.yaml (#461's shape
    # —
    # lead directive #17055): amendment 30's ruled, not-yet-built symbols. Runtime-inert; the pins read them
    # dynamically (``_counts_model`` / ``_counts``).
    from loremaster.governed import MigratePreconditionCounts

    def _typed_preconditions(result: MigrateGovernedResult) -> object:
        return (MigratePreconditionCounts, result.preconditions)


_DIM = a19a._DIM
#: THE concurrency degree (store-ref §5: ≥8-way, never 2-way) and the rounds per invocation (the audit's P5
#: rig: a FRESH session per round, so each round is an independent race).
_CONCURRENCY = 8
_ROUNDS = 20


async def _outcome(awaitable: Awaitable[Any]) -> tuple[str, str]:
    """``(class name, served text)`` of one call — ``OK`` for a returned render."""
    try:
        result = await awaitable
    except Exception as error:  # noqa: BLE001 - the pin classifies whatever is served
        return type(error).__name__, str(error)
    return "OK", str(result)


def _spy_delete_keep(monkeypatch: pytest.MonkeyPatch, ctx: Any) -> dict[str, int]:
    """Count every ``KeepStore.delete_keep`` call on the WIRED keep store (the removed compensation's verb —
    amendment 28 §F-1: nothing on the register path deletes a keep)."""
    keep_store = ctx._keep_store
    real = keep_store.delete_keep
    calls = {"count": 0}

    async def counting(*args: Any, **kwargs: Any) -> Any:
        calls["count"] += 1
        return await real(*args, **kwargs)

    monkeypatch.setattr(keep_store, "delete_keep", counting)
    return calls


async def _session_keep_ids(admin_conn: Any, session: str) -> list[str]:
    return [
        str(value)
        for value in await run(admin_conn, f"SELECT VALUE id FROM keep WHERE key = 'session:{session}'")
    ]


async def _live_keep_scopes(admin_conn: Any) -> set[str]:
    """``keep:<bare>`` for every keep that EXISTS (``str(RecordID)``, store-ref §7 — never a hand parse)."""
    return {str(value) for value in await run(admin_conn, "SELECT VALUE id FROM keep")}


async def _agent_scopes(admin_conn: Any, session: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = await run(
        admin_conn, f"SELECT name, role, scope FROM agent WHERE session = '{session}' ORDER BY name"
    )
    return rows


# =========================================================================== #
# amendment 28 §F-1 + Addendum A1 — NO race compensation. The register path never deletes a keep; every
# agent row's ``scope`` resolves to a LIVE keep. RS-2 (8-way, 20 rounds) + the deterministic sequential leg
# (the §F-1 construction recipe / the audit's P2), one leg per WINNER CLASS (fixtures must discriminate): a
# same-principal HANDLER winner that FOUND the keep (the only principal-bearing winner of the race — the
# compensation's victim), and the tokenless (ownerless) winner — through the handler seam, amendment 32 §5
# R-3 — as the CONTROL.
# =========================================================================== #


def _eight_way_register_calls(ctx: Any, session: str) -> list[Awaitable[Any]]:
    """The audit's P5 rig: 4 registers of ONE name (``dup``) with ALTERNATING roles (so role conflicts race
    the mint) + 4 distinct names — ``_CONCURRENCY`` handler registers by ONE principal into ONE session."""
    half = _CONCURRENCY // 2
    calls = [
        ctx.comms(action="register", agent="dup", session=session, role=("builder", "scout")[index % 2])
        for index in range(half)
    ]
    calls += [
        ctx.comms(action="register", agent=f"solo{index}", session=session, role="builder")
        for index in range(half)
    ]
    return calls


#: Per-call "this register's own keep mint returned" marker (amendment 32 §5 R-1). A ContextVar, because each
#: ``asyncio.gather`` child runs in its OWN task (its own context copy): the marker set inside one register
#: call is invisible to its seven concurrent siblings.
_MINT_RETURNED: contextvars.ContextVar[list[bool] | None] = contextvars.ContextVar(
    "a28b_mint_returned", default=None
)


def _arm_per_call_mint_marker(
    monkeypatch: pytest.MonkeyPatch, ctx: Any
) -> contextvars.ContextVar[list[bool] | None]:
    """Wrap the WIRED ``get_or_create_keyed`` so the CALLING register learns its own mint RETURNED."""
    keep_store = ctx._keep_store
    real = keep_store.get_or_create_keyed

    async def marking(*args: Any, **kwargs: Any) -> Any:
        keep = await real(*args, **kwargs)
        marker = _MINT_RETURNED.get()
        if marker is not None:
            marker.append(True)
        return keep

    monkeypatch.setattr(keep_store, "get_or_create_keyed", marking)
    return _MINT_RETURNED


async def _minted_then_outcome(
    marker: contextvars.ContextVar[list[bool] | None], call: Awaitable[Any]
) -> tuple[bool, Any]:
    """``(did THIS call's mint return, the call's result or raised exception)`` — run inside its own task."""
    minted: list[bool] = []
    marker.set(minted)
    try:
        outcome: Any = await call
    except Exception as error:  # noqa: BLE001 - the pin classifies whatever is served
        outcome = error
    return bool(minted), outcome


class TestTheRaceNeverStrandsAScope63cIAa28:
    """amendment 28 §F-1 (RS-2 + the §F-1 recipe + Addendum A1)."""

    async def test_RS2_eight_way_registers_never_strand_a_scope(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at ``169925f`` (the created-only compensation deletes the session keep a concurrent
        same-principal register FOUND and is scoped to — audit P5: 2/20, 8/20, 11/20 rounds stranded, HEAD
        before the patch 0/20). ``_ROUNDS`` rounds, each a FRESH session and ``_CONCURRENCY`` concurrent
        handler registers by ONE principal (≥1 same-name role conflict per round). ∀ rounds, ∀ agent rows of
        the session: ``scope`` is set and resolves to a LIVE keep, and that keep is THE one session keep of
        the session (one ``session:<s>`` keep, never a fresh ULID beside a dead one). ``delete_keep`` is never
        called (nothing on the register path deletes a keep — amendment 28 §F-1). Non-vacuity: every round
        registered all 5 names and EVERY round met ≥1 POST-MINT refusal — a register that raised AFTER its own
        keep mint returned, which is the path the removed compensation ran on (amendment 32 §5 R-1: the
        assertion now performs the check this docstring promises; a pre-mint preflight refusal does not
        count)."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            world["holder"]["email"] = world["emails"]["alice"]
            deletes = _spy_delete_keep(monkeypatch, ctx)
            minted_in_this_call = _arm_per_call_mint_marker(monkeypatch, ctx)
            stranded_rounds: list[dict[str, Any]] = []
            post_mint_refusal_rounds = 0
            for round_index in range(_ROUNDS):
                session = f"s-rs2-{round_index}"
                outcomes = await asyncio.gather(
                    *[
                        _minted_then_outcome(minted_in_this_call, call)
                        for call in _eight_way_register_calls(ctx, session)
                    ]
                )
                post_mint_refusal_rounds += any(
                    minted and isinstance(outcome, BaseException) for minted, outcome in outcomes
                )
                rows = await _agent_scopes(admin_conn, session)
                live = await _live_keep_scopes(admin_conn)
                session_keeps = await _session_keep_ids(admin_conn, session)
                assert sorted(row["name"] for row in rows) == ["dup", "solo0", "solo1", "solo2", "solo3"], (
                    f"round {round_index}: non-vacuity — every name must hold ONE row: {rows!r} / "
                    f"{outcomes!r}"
                )
                bad = [
                    row
                    for row in rows
                    if row.get("scope") is None or row["scope"] not in live or [row["scope"]] != session_keeps
                ]
                if bad or len(session_keeps) != 1:
                    stranded_rounds.append(
                        {"round": round_index, "stranded": bad, "session_keeps": session_keeps}
                    )
            assert not stranded_rounds, (
                f"amendment 28 §F-1: {len(stranded_rounds)}/{_ROUNDS} rounds left agent rows whose scope "
                "does not "
                "resolve to THE live session keep — a register path that deletes (or re-mints) a keep a "
                f"concurrent registration is scoped to strands it permanently: {stranded_rounds!r}"
            )
            assert deletes["count"] == 0, (
                f"the register path called delete_keep {deletes['count']}x — amendment 28 §F-1 deletes the "
                "race "
                "compensation outright (a guarded delete is REJECTED too: a delete is never correct on this "
                "path)"
            )
            assert post_mint_refusal_rounds == _ROUNDS, (
                f"non-vacuity (amendment 32 §5 R-1): only {post_mint_refusal_rounds}/{_ROUNDS} rounds met a "
                "POST-MINT refusal (a register that raised after its own keep mint returned) — the race path "
                "the "
                "removed compensation ran on was not exercised every round, so a clean round proves nothing"
            )

    @pytest.mark.parametrize("winner", ["handler-winner-found-the-keep", "tokenless-winner-control"])
    async def test_the_sequential_race_keeps_the_keep_and_serves_the_teaching(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, winner: str
    ) -> None:
        """The §F-1 construction recipe (deterministic — the audit's P2). ONE principal P (alice), session
        ``s``, name ``a``. The WIRED ``get_or_create_keyed`` is wrapped so that on its FIRST call, AFTER the
        real mint returns K (THIS call — X, ``role="builder"`` — CREATED K), the winner X' registers ``a``
        inline:
        * ``handler-winner-found-the-keep`` — ⚠ RED at ``169925f`` (X deletes K; X' is stranded — audit P2
          ``agent_scope_keep_exists: false``). X' is a COMPLETE handler ``comms(register, a, s,
          role="auditor")`` by P: it FINDS K, passes the gate, CREATEs its row scoped ``keep:K``.
        * ``tokenless-winner-control`` — the Addendum A1 CONTROL (the β-closed bound, amendment 28 §F-1
          residual): X' is an OWNERLESS register THROUGH THE HANDLER (an empty-subject token — amendment 32
          §5 R-3; it holds no scope). A pin-the-miss: when β refuses the handler's ownerless register, X'
          no longer wins and this leg reds by name.
        ∀ legs: X raises ``AgentIdentityConflictError`` naming X''s role (the registry's teaching,
        byte-identical
        to what the registry itself serves the same call — KP4's property, by construction); K still RESOLVES
        (``get_keep``); ``delete_keep`` is never called; and a THIRD register by P into ``s`` FINDS K (the
        session holds exactly ONE ``session:<s>`` keep, K). Handler leg: X''s ``scope == keep:K`` and the
        third
        agent's scope is ``keep:K`` too. Control leg: X''s scope is NONE (tokenless), and K is KEPT BY P with
        no scoped agent until the third register — the named β bound (re-open trigger, restated by amendment
        32 §5 R-3 as a code event this leg MEASURES: the day the handler's ownerless / post-mint refusal path
        changes, the tokenless X' stops winning and this leg reds)."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            world["holder"]["email"] = world["emails"]["alice"]
            session = "s-seq-race"
            keep_store = ctx._keep_store
            real_mint = keep_store.get_or_create_keyed
            calls = {"mint": 0}
            winner_outcome: dict[str, tuple[str, str]] = {}

            async def the_winner() -> None:
                if winner == "handler-winner-found-the-keep":
                    winner_outcome["x_prime"] = await _outcome(
                        ctx.comms(action="register", agent="a", session=session, role="auditor")
                    )
                else:
                    # amendment 32 §5 R-3: the tokenless winner is built THROUGH the handler seam (an
                    # empty-subject token), never at the registry — so this CONTROL is a real pin-the-miss:
                    # the day β closes the handler's ownerless register (i-b), X' is refused and the
                    # "X' must WIN" fixture assertion below reds, naming the KNOWN BOUND.
                    world["holder"]["email"] = None
                    try:
                        winner_outcome["x_prime"] = await _outcome(
                            ctx.comms(action="register", agent="a", session=session, role="auditor")
                        )
                    finally:
                        world["holder"]["email"] = world["emails"]["alice"]

            async def racing_mint(*args: Any, **kwargs: Any) -> Any:
                calls["mint"] += 1
                keep = await real_mint(*args, **kwargs)
                if calls["mint"] == 1:
                    await the_winner()
                return keep

            monkeypatch.setattr(keep_store, "get_or_create_keyed", racing_mint)
            deletes = _spy_delete_keep(monkeypatch, ctx)
            with pytest.raises(AgentRegistryError) as caught:
                await ctx.comms(action="register", agent="a", session=session, role="builder")
            assert winner_outcome.get("x_prime", ("?", ""))[0] == "OK", (
                f"fixture: X' must WIN: {winner_outcome!r}"
                + (
                    " — ⚠ tokenless-winner-control: this is the KNOWN BOUND (amendment 28 §F-1 residual, the "
                    "β bound; amendment 32 §5 R-3). If β closed the handler's ownerless register "
                    "deliberately, re-key or delete this control leg and say so."
                    if winner == "tokenless-winner-control"
                    else ""
                )
            )
            assert isinstance(caught.value, AgentIdentityConflictError) and "auditor" in str(caught.value), (
                f"X must be served the registry's role-conflict teaching naming X''s role: {caught.value!r}"
            )
            with pytest.raises(AgentRegistryError) as direct:
                await ctx.agent_registry.register("a", session=session, role="builder")
            assert (type(caught.value), str(caught.value)) == (type(direct.value), str(direct.value)), (
                f"the race must serve the registry's refusal UNALTERED: served={caught.value!r} "
                f"registry={direct.value!r}"
            )
            keeps = await _session_keep_ids(admin_conn, session)
            assert len(keeps) == 1, f"the session keep K must SURVIVE the refused register: {keeps!r}"
            keep_bare = _bare(keeps[0])
            assert await keep_store.get_keep(keep_bare) is not None, f"K ({keep_bare}) does not resolve"
            assert deletes["count"] == 0, (
                f"the register path called delete_keep {deletes['count']}x (amendment 28 §F-1)"
            )
            x_prime = await run(
                admin_conn, f"SELECT scope FROM agent WHERE session = '{session}' AND name = 'a'"
            )
            if winner == "handler-winner-found-the-keep":
                assert [row.get("scope") for row in x_prime] == [keep_scope(keep_bare)], (
                    f"X' (the handler winner that FOUND K) must stay scoped to the LIVE K: {x_prime!r}"
                )
            else:
                assert [row.get("scope") for row in x_prime] == [None], (
                    f"CONTROL: the tokenless X' holds no scope: {x_prime!r}"
                )
                keeper = await run(
                    admin_conn, f"SELECT VALUE keeper FROM keep WHERE key = 'session:{session}'"
                )
                assert [_bare(value) for value in keeper] == [world["pids"]["alice"]], (
                    "CONTROL (the named β bound): K is left kept by P with no scoped agent — never deleted: "
                    f"{keeper!r}"
                )
            third = await _outcome(
                ctx.comms(action="register", agent="third", session=session, role="builder")
            )
            assert third[0] == "OK", f"a third register by P into the session must succeed: {third!r}"
            assert await _session_keep_ids(admin_conn, session) == keeps, (
                "the third register must FIND K — no fresh session keep minted beside it"
            )
            third_scope = await run(
                admin_conn, f"SELECT VALUE scope FROM agent WHERE session = '{session}' AND name = 'third'"
            )
            assert third_scope == [keep_scope(keep_bare)], f"the third agent must join K: {third_scope!r}"


# =========================================================================== #
# amendment 29 RS-5 — a concurrent IDENTICAL first register is LEGAL and, sequentially, IDEMPOTENT: the loser
# is
# served the registry's own result (``re_registered=True``) or its own teaching, never a raw engine error.
# ONE implementation: the registry's CREATE conflict re-reads and takes its existing re-register path.
# =========================================================================== #


class TestAConcurrentIdenticalRegisterIsIdempotent63cIAa28:
    async def test_RS5_every_handler_caller_gets_a_registry_answer_never_an_engine_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at ``169925f`` (audit RS-5: the same-name same-role loser is served a raw
        ``TxnDomainRejectionError`` — 55 in 20 rounds, pre-existing). The RS-2 rig, ``_ROUNDS`` rounds: ∀
        callers the outcome is a render (OK) or a registry teaching (an ``AgentRegistryError``), never a store
        error; and for ``dup`` (roles builder, scout, builder, scout — the winner's role has exactly ONE
        same-role twin) EXACTLY one first register, EXACTLY one ``re-registered`` render and EXACTLY two
        ``AgentIdentityConflictError`` teachings; ``dup`` holds ONE row."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            world["holder"]["email"] = world["emails"]["alice"]
            failures: list[str] = []
            for round_index in range(_ROUNDS):
                session = f"s-rs5-{round_index}"
                outcomes = await asyncio.gather(
                    *[_outcome(call) for call in _eight_way_register_calls(ctx, session)]
                )
                dup, solos = outcomes[: _CONCURRENCY // 2], outcomes[_CONCURRENCY // 2 :]
                engine = [outcome for outcome in outcomes if outcome[0] not in ("OK", *_REGISTRY_CLASSES)]
                if engine:
                    failures.append(
                        f"round {round_index}: a raw non-registry error reached a caller: {engine!r}"
                    )
                    continue
                if any(outcome[0] != "OK" for outcome in solos):
                    failures.append(f"round {round_index}: a distinct-name register was refused: {solos!r}")
                first = [text for kind, text in dup if kind == "OK" and not text.startswith("re-registered")]
                again = [text for kind, text in dup if kind == "OK" and text.startswith("re-registered")]
                conflicts = [kind for kind, _text in dup if kind == "AgentIdentityConflictError"]
                if (len(first), len(again), len(conflicts)) != (1, 1, 2):
                    failures.append(
                        f"round {round_index}: dup must serve 1 first register, 1 re-register, 2 role "
                        "conflicts — "
                        f"got {len(first)}/{len(again)}/{len(conflicts)}: {dup!r}"
                    )
                rows = await run(
                    admin_conn, f"SELECT VALUE name FROM agent WHERE session = '{session}' AND name = 'dup'"
                )
                if rows != ["dup"]:
                    failures.append(f"round {round_index}: dup must hold ONE row: {rows!r}")
            assert not failures, (
                "amendment 29 RS-5 (CONSUMER LAW): a legal concurrent register is served the registry's own "
                "answer "
                "— the loser of an identical first register takes the registry's re-register path (re-read "
                "on the "
                "CREATE conflict), never a raw engine error:\n" + "\n".join(failures)
            )

    async def test_RS5_eight_identical_first_registers_all_succeed_at_the_registry(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at ``169925f``. The REGISTRY itself (where the ruled branch lives — never a handler retry):
        ``_ROUNDS`` rounds × ``_CONCURRENCY`` concurrent IDENTICAL ``AgentRegistry.register(name, session,
        role)`` calls into a fresh session: every call returns a result (none raises), EXACTLY one
        ``re_registered=False`` (the CREATE winner) and the rest ``re_registered=True``, and the session holds
        ONE row — exactly what ``_CONCURRENCY`` SEQUENTIAL calls return."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            failures: list[str] = []
            for round_index in range(_ROUNDS):
                session = f"s-rs5r-{round_index}"
                results = await asyncio.gather(
                    *[
                        ctx.agent_registry.register("same", session=session, role="builder")
                        for _ in range(_CONCURRENCY)
                    ],
                    return_exceptions=True,
                )
                raised = [
                    f"{type(result).__name__}: {result}"
                    for result in results
                    if isinstance(result, BaseException)
                ]
                if raised:
                    failures.append(
                        f"round {round_index}: {len(raised)} identical register(s) raised: {raised[:2]!r}"
                    )
                    continue
                flags = sorted(
                    result.re_registered for result in results if isinstance(result, AgentRegisterResult)
                )
                if flags != [False] + [True] * (_CONCURRENCY - 1):
                    failures.append(f"round {round_index}: re_registered flags {flags!r} (want one False)")
                rows = await run(admin_conn, f"SELECT VALUE name FROM agent WHERE session = '{session}'")
                if rows != ["same"]:
                    failures.append(f"round {round_index}: rows {rows!r}")
            assert not failures, "amendment 29 RS-5 at the registry:\n" + "\n".join(failures)


#: The registry's teaching family — the classes a legal register may be refused with (``AgentRegistryError``
#: and every subclass ``agents.py`` defines), DERIVED, never a hand-list.
_REGISTRY_CLASSES = tuple(
    sorted(
        {
            member.__name__
            for member in vars(agents_module).values()
            if inspect.isclass(member) and issubclass(member, AgentRegistryError)
        }
    )
)


# =========================================================================== #
# amendment 28 §F-2 — the ORDER: principal → READ-ONLY SF-63-1 gate → preflight → mint → post-mint re-check →
# register. A foreign credentialed principal learns NOTHING about another principal's agents: every probe is
# the SAME ``GovernedDenied`` (no existence oracle), with ZERO registry reads and zero mints (the RS-3 pin).
# =========================================================================== #


def _spy_registry_queries(monkeypatch: pytest.MonkeyPatch, registry: Any) -> list[str]:
    seen: list[str] = []
    real = registry._query

    async def counting(statement: str, params: Any = None) -> Any:
        seen.append(statement)
        return await real(statement, params)

    monkeypatch.setattr(registry, "_query", counting)
    return seen


def _count_calls(monkeypatch: pytest.MonkeyPatch, owner: Any, method: str, counter: dict[str, int]) -> None:
    real = getattr(owner, method)

    async def counting(*args: Any, **kwargs: Any) -> Any:
        counter[method] = counter.get(method, 0) + 1
        return await real(*args, **kwargs)

    monkeypatch.setattr(owner, method, counting)


async def _alice_keeps_a_session(ctx: Any, world: dict[str, Any], session: str) -> None:
    """alice keeps ``session`` with agent ``worker`` (role ``secretrole``, spawned_by ``alicelead``) and a
    RETIRED agent ``gone`` (the audit's P1 / amendment 28 §F-2 recipe)."""
    world["holder"]["email"] = world["emails"]["alice"]
    await ctx.comms(
        action="register", agent="worker", session=session, role="secretrole", spawned_by="alicelead"
    )
    await ctx.comms(action="register", agent="gone", session=session, role="builder")
    await ctx.agent_registry.touch("gone", session=session, status="retired")


_FOREIGN_PROBES: dict[str, dict[str, Any]] = {
    "role-conflict": {"agent": "worker", "role": "auditor"},
    "spawned-by-conflict": {"agent": "worker", "role": "secretrole", "spawned_by": "boblead"},
    "retired": {"agent": "gone", "role": "builder"},
    "absent-name": {"agent": "nobody", "role": "builder"},
}


class TestAForeignPrincipalLearnsNothingBeforeTheGate63cIAa28:
    async def test_RS3_every_foreign_probe_is_the_same_denial_with_zero_registry_reads(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at ``169925f`` (audit F-1 / P1: ``preflight`` runs BEFORE the SF-63-1 gate, so carol is
        served
        alice's agent's role ``secretrole``, its ``spawned_by`` ``alicelead`` and its retirement; only the
        absent
        name meets the gate). carol (credentialed, NOT householded in alice's session) registers four names
        into it: a role conflict, a ``spawned_by`` conflict, a retired name and an ABSENT name. ALL FOUR are
        ``GovernedDenied``, BYTE-IDENTICAL (no per-name existence oracle), naming none of ``secretrole`` /
        ``alicelead`` / ``retired``; during carol's four calls the registry's ONE query seam
        (``AgentRegistry._query`` — every registry read, through any method, rides it; amendment 32 C2) and
        the keep mint (``get_or_create_keyed``) are called ZERO times; the agent / keep / household tables are
        byte-identical."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member", "carol": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            session = "s-alice"
            await _alice_keeps_a_session(ctx, world, session)
            # DUAL (amendment 32 §4 C2 / K1): the hand-list of three registry methods is REPLACED by the spy
            # on
            # the registry's ONE query seam (every registry read rides ``AgentRegistry._query``); the mint
            # counter stays (zero mints is its own clause).
            registry_queries = _spy_registry_queries(monkeypatch, ctx.agent_registry)
            reads: dict[str, int] = {}
            _count_calls(monkeypatch, ctx._keep_store, "get_or_create_keyed", reads)
            before = {
                table: await run(admin_conn, f"SELECT * FROM {table} ORDER BY id")
                for table in ("agent", "keep", "member_of")
            }
            world["holder"]["email"] = world["emails"]["carol"]
            served = {
                label: await _outcome(ctx.comms(action="register", session=session, **probe))
                for label, probe in _FOREIGN_PROBES.items()
            }
            after = {
                table: await run(admin_conn, f"SELECT * FROM {table} ORDER BY id")
                for table in ("agent", "keep", "member_of")
            }
            classes = {label: kind for label, (kind, _text) in served.items()}
            assert set(classes.values()) == {GovernedDenied.__name__}, (
                "amendment 28 §F-2: a foreign principal must meet the SF-63-1 denial on EVERY probe: "
                f"{served!r}"
            )
            texts = {text for _kind, text in served.values()}
            assert len(texts) == 1, (
                "the four denials must be BYTE-IDENTICAL — a difference between them is a per-name existence "
                f"oracle (63-rulings §6): {served!r}"
            )
            leaked = [word for word in ("secretrole", "alicelead", "retired") if word in next(iter(texts))]
            assert not leaked, f"the denial serves another principal's agent facts {leaked}: {texts!r}"
            assert registry_queries == [] and reads == {}, (
                "the read-only SF-63-1 gate must deny BEFORE any registry read or keep mint — observed "
                f"registry queries {registry_queries!r}, mints {reads} "
                "(amendment 28 §F-2: ZERO registry reads, through ANY door — amendment 32 C2)"
            )
            assert after == before, "a denied foreign register WROTE"

    async def test_RS3_CONTROLS_a_householded_member_proceeds_and_the_keeper_is_still_taught(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """CONTROLS (a probe needs a control — the denial above must not be a gate that denies everyone): bob,
        HOUSEHOLDED in alice's session keep, registers his own agent and re-registers it (both OK); alice's
        OWN
        role conflict is still taught with the role (``secretrole``) — the registry's teaching reaches the
        keeper's household."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member", "bob": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            session = "s-alice"
            await _alice_keeps_a_session(ctx, world, session)
            keep_bare = _bare((await _session_keep_ids(admin_conn, session))[0])
            await ctx._keep_store.add_household_member(keep_id=keep_bare, member_email=world["emails"]["bob"])
            world["holder"]["email"] = world["emails"]["bob"]
            first = await _outcome(
                ctx.comms(action="register", agent="bobagent", session=session, role="builder")
            )
            again = await _outcome(
                ctx.comms(action="register", agent="bobagent", session=session, role="builder")
            )
            assert (first[0], again[0]) == ("OK", "OK") and again[1].startswith("re-registered"), (
                first,
                again,
            )
            world["holder"]["email"] = world["emails"]["alice"]
            own = await _outcome(
                ctx.comms(action="register", agent="worker", session=session, role="auditor")
            )
            assert own[0] == AgentIdentityConflictError.__name__ and "secretrole" in own[1], (
                f"CONTROL: the keeper's own conflict must still teach the role: {own!r}"
            )

    async def test_the_handler_ORDER_is_gate_then_preflight_then_mint_then_register(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at ``169925f`` (order preflight → mint → gate). amendment 28 §F-2: for a valid credentialed
        register, the FIRST ``KeepStore.get_by_key("session:<s>")`` (the READ-ONLY gate) precedes
        ``AgentRegistry.preflight``, which precedes ``get_or_create_keyed`` (the mint), which precedes
        ``register``. Driven twice — into a FRESH session (no keep yet: the gate reads a miss and proceeds)
        and
        into an EXISTING session the caller keeps (the gate reads a hit and passes)."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx = world["ctx"]
            world["holder"]["email"] = world["emails"]["alice"]
            keep_store = ctx._keep_store
            events: list[str] = []
            real_get_by_key, real_mint = keep_store.get_by_key, keep_store.get_or_create_keyed
            real_preflight, real_register = AgentRegistry.preflight, ctx.agent_registry.register

            async def recording_get_by_key(key: str, *args: Any, **kwargs: Any) -> Any:
                events.append(f"get_by_key:{key}")
                return await real_get_by_key(key, *args, **kwargs)

            async def recording_mint(*args: Any, **kwargs: Any) -> Any:
                events.append("mint")
                return await real_mint(*args, **kwargs)

            async def recording_preflight(self: Any, *args: Any, **kwargs: Any) -> Any:
                events.append("preflight")
                return await real_preflight(self, *args, **kwargs)

            async def recording_register(*args: Any, **kwargs: Any) -> Any:
                events.append("register")
                return await real_register(*args, **kwargs)

            monkeypatch.setattr(keep_store, "get_by_key", recording_get_by_key)
            monkeypatch.setattr(keep_store, "get_or_create_keyed", recording_mint)
            monkeypatch.setattr(AgentRegistry, "preflight", recording_preflight)
            monkeypatch.setattr(ctx.agent_registry, "register", recording_register)
            for label, agent in (("fresh-session", "first-agent"), ("existing-session", "second-agent")):
                events.clear()
                await ctx.comms(action="register", agent=agent, session="s-order", role="builder")
                gate = "get_by_key:session:s-order"
                assert (
                    gate in events and "preflight" in events and "mint" in events and "register" in events
                ), f"{label}: {events}"
                assert (
                    events.index(gate)
                    < events.index("preflight")
                    < events.index("mint")
                    < events.index("register")
                ), (
                    f"{label}: amendment 28 §F-2 ORDER is read-only gate (get_by_key) → preflight → mint → "
                    f"register: {events}"
                )

    async def test_the_POST_MINT_recheck_denies_a_keep_minted_meanwhile_by_another_principal(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """GREEN at ``169925f`` (its only gate IS post-mint); RED on a build that keeps only the read-only
        gate
        (amendment 28 §F-2: "the existing post-mint visibility re-check (kept, for the keep-minted-meanwhile
        race)"). Construction: alice registers into a session with NO keep (her read-only gate reads a miss);
        between her gate and her mint, bob's complete handler register mints the session keep (kept by bob);
        alice's mint then FINDS bob's keep. alice must be DENIED (``GovernedDenied``) and write no agent
        row."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member", "bob": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            session = "s-meanwhile"
            keep_store = ctx._keep_store
            real_mint = keep_store.get_or_create_keyed
            calls = {"mint": 0}
            bob_outcome: dict[str, tuple[str, str]] = {}

            async def bob_mints_first(*args: Any, **kwargs: Any) -> Any:
                calls["mint"] += 1
                if calls["mint"] == 1:
                    world["holder"]["email"] = world["emails"]["bob"]
                    bob_outcome["bob"] = await _outcome(
                        ctx.comms(action="register", agent="bobs-agent", session=session, role="builder")
                    )
                    world["holder"]["email"] = world["emails"]["alice"]
                return await real_mint(*args, **kwargs)

            monkeypatch.setattr(keep_store, "get_or_create_keyed", bob_mints_first)
            world["holder"]["email"] = world["emails"]["alice"]
            alice = await _outcome(
                ctx.comms(action="register", agent="alices-agent", session=session, role="builder")
            )
            assert bob_outcome.get("bob", ("?", ""))[0] == "OK", (
                f"fixture: bob must mint the keep: {bob_outcome!r}"
            )
            assert alice[0] == GovernedDenied.__name__, (
                f"the post-mint re-check must deny alice (bob keeps the keep her mint FOUND): {alice!r}"
            )
            rows = await run(admin_conn, f"SELECT VALUE name FROM agent WHERE session = '{session}'")
            assert rows == ["bobs-agent"], f"a denied register wrote an agent row: {rows!r}"


# =========================================================================== #
# amendment 27 FORK-1 — ``backfilled`` is the rows the UPDATE STAMPED, ∀ legs (the DERIVED ``_migrate_legs``,
# memory included), measured by a byte-diff of ``SELECT *`` before/after — never a re-read of the predicate.
# The gap is made reachable by redirecting THE shared preconditions at a clean store (the F-3 race: the leg
# proceeds while a row its self-guarding WHERE skips is present).
# =========================================================================== #


async def _seed_agent_leg(world: Any) -> None:
    """2 legacy agents + 1 operator-owned-but-unscoped agent (the E3 half-pair — its ``scope IS NONE``
    pre-count includes it, the self-guarding WHERE skips it)."""
    for index in range(2):
        await seed_agent_legacy(
            world.connection, row_id=f"legacy_{index}", name=f"legacy-{index}", session="f1"
        )
    await seed_agent_governed(
        world.connection,
        row_id="owned_unscoped",
        name="owned-unscoped",
        session="f1",
        owner_principal=world.operator_bare,
        owner_agent=None,
        scope=None,
    )


async def _seed_memory_leg(world: Any) -> None:
    """3 legacy memory rows (memory's WHERE equals its count predicate — no gap, NOT excluded: ∀ means ∀)."""
    for index in range(3):
        await seed_memory_legacy(world.connection, row_id=f"legacy_memory_{index}", dim=_DIM)


async def _seed_message_leg(world: Any) -> None:
    """Migrated senders + 2 sound legacy messages + 1 operator-owned-but-unscoped message (half i)."""
    await a19a._seed_migrated_senders(world)
    for index in range(2):
        await seed_message_legacy(
            world.connection, sender_id="sender_operator", session="gs", seq=index + 1, row_id=f"m{index}"
        )
    await seed_message_legacy(
        world.connection,
        sender_id="sender_operator",
        session="gs",
        seq=3,
        row_id="m_half",
        owner_principal=RecordID("principal", world.operator_bare),
    )


#: leg → (table, population). Every DERIVED leg must appear here — a new leg with no population reds by name.
_LEG_POPULATIONS: dict[str, tuple[str, Callable[[Any], Awaitable[None]]]] = {
    "_migrate_agent_owner": (AGENT_TABLE, _seed_agent_leg),
    "_migrate_memory_scope": (MEMORY_TABLE, _seed_memory_leg),
    "_migrate_message_owner": (MESSAGE_TABLE, _seed_message_leg),
}


def _rows_changed(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> int:
    """How many rows differ between two ``SELECT * … ORDER BY id`` reads (same id set — a backfill adds
    none)."""
    by_id = {str(row["id"]): row for row in before}
    assert {str(row["id"]) for row in after} == set(by_id), "the backfill added or removed rows"
    return sum(1 for row in after if by_id[str(row["id"])] != row)


class TestBackfilledIsMeasuredOnEveryLeg63cIAa28:
    @pytest.mark.parametrize("leg", sorted(a19a._migrate_legs()))
    async def test_FORK1_backfilled_equals_the_rows_the_run_changed(
        self, monkeypatch: pytest.MonkeyPatch, leg: str
    ) -> None:
        """⚠ RED at ``169925f`` for ``_migrate_agent_owner`` (audit F-3 / P4: serves the scope-keyed pre-count
        3 while 2 rows changed); GREEN there for memory and message (their counts are measured / have no gap)
        — the pin is ∀ legs, so a leg that regresses reds by name. Parametrised over THE derived leg set
        (``test_fixwave_a19a_63c_i_a.py::_migrate_legs``). THE shared preconditions redirected at a clean
        store;
        two runs (the second is the idempotent re-run): ``backfilled`` == the number of rows whose bytes
        CHANGED (``SELECT *`` before/after), and the run proceeds."""
        if leg not in _LEG_POPULATIONS:
            pytest.fail(
                f"governed leg {leg!r} has no FORK-1 population — add one (∀ legs, amendment 27 FORK-1)"
            )
        table, seed = _LEG_POPULATIONS[leg]
        async with a19a._governed_world() as world, a19a._governed_world() as clean:
            await seed(world)
            await a19a._seed_clean_single_principal_store(clean)
            calls = _redirect_the_shared_preconditions(monkeypatch, clean.handle)
            changed_per_run = []
            for run_label in ("first", "second"):
                before = await run(world.connection, f"SELECT * FROM {table} ORDER BY id")
                result = await world.migrate(table)
                after = await run(world.connection, f"SELECT * FROM {table} ORDER BY id")
                changed = _rows_changed(before, after)
                changed_per_run.append(changed)
                assert calls["count"] >= 1, "the redirect never landed (#194)"
                assert result.refused is False, f"{leg} ({run_label}): the leg must proceed: {result!r}"
                assert result.backfilled == changed, (
                    f"{leg} ({run_label}): backfilled={result.backfilled} but {changed} row(s) changed — a "
                    "served "
                    "count must be the rows the UPDATE STAMPED, measured, ∀ legs (amendment 27 FORK-1; "
                    "CONSUMER "
                    f"LAW): {result!r}"
                )
            assert changed_per_run[0] >= 2 and changed_per_run[1] == 0, (
                f"{leg}: non-vacuity — the first run must stamp ≥2 rows, the idempotent re-run none: "
                f"{changed_per_run}"
            )


# =========================================================================== #
# amendments 26 / 27 FORK-2 / 29 F-8 — the message leg's preconditions are ONE refusal naming every failing
# check in CHECK ORDER: the agent-first ORDER guard, then dangling senders, then the message half-pairs. The
# verb-level §2.1 refusal stays a SEPARATE, EARLIER answer. Every count is attributed INSIDE its own clause.
# =========================================================================== #


def _clause_count(reason: str, marker: str) -> int | None:
    """The count ATTRIBUTED to the clause containing ``marker`` (amendment 29 F-8): the LAST integer in the
    span
    between the previous sentence boundary (``". "``) and the first occurrence of ``marker`` — the clause's
    own
    number, never any integer anywhere in the reason. ``None`` when the marker is absent."""
    position = reason.find(marker)
    if position == -1:
        return None
    head = reason[:position]
    sentence = head[head.rfind(". ") + 2 :] if ". " in head else head
    numbers = re.findall(r"\d+", sentence)
    return int(numbers[-1]) if numbers else None


#: The served markers of each clause (read from the served text — amendment 26: the order is read from nothing
#: but the text): the ORDER guard's un-migrated agents, the dangling senders, and each message half.
_ORDER_MARKER = "un-migrated"
_DANGLING_MARKER = "dangling sender"
_HALF_I_MARKER = "carry an owner but no scope"
_HALF_II_MARKER = "carry a scope but no owner"


async def _seed_rs1(world: Any) -> None:
    """The audit's RS-1 fixture, VERBATIM (``REPORT-coldaudit-63c-i-a-2.md`` §9 RS-1)."""
    conn = world.connection
    await a19a._seed_migrated_senders(world)
    await seed_message_legacy(conn, sender_id="ghost_sender", session="gs", seq=1, row_id="m_dangling")
    await seed_message_legacy(
        conn,
        sender_id="sender_operator",
        session="gs",
        seq=2,
        row_id="m_half_i",
        owner_principal=RecordID("principal", world.operator_bare),
    )
    await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=3, row_id="m_sound")


#: FORK-2's DISCRIMINATING population (F-8: every clause a DIFFERENT count, so a build that swaps or pools
#: counts reds): 2 un-migrated agents, 3 dangling senders, 4 half-i messages, 5 half-ii messages.
_FORK2_COUNTS = {"order": 2, "dangling": 3, "half_i": 4, "half_ii": 5}


async def _seed_fork2(world: Any) -> None:
    conn = world.connection
    await a19a._seed_migrated_senders(world)
    for index in range(_FORK2_COUNTS["order"]):
        await seed_agent_legacy(conn, row_id=f"legacyagent{index}", name=f"legacyagent{index}", session="gs")
    seq = iter(range(1, 1000))
    for index in range(_FORK2_COUNTS["dangling"]):
        await seed_message_legacy(
            conn, sender_id=f"ghost{index}", session="gs", seq=next(seq), row_id=f"m_dangling{index}"
        )
    for index in range(_FORK2_COUNTS["half_i"]):
        await seed_message_legacy(
            conn,
            sender_id="sender_operator",
            session="gs",
            seq=next(seq),
            row_id=f"m_half_i{index}",
            owner_principal=RecordID("principal", world.operator_bare),
        )
    for index in range(_FORK2_COUNTS["half_ii"]):
        await seed_message_legacy(
            conn,
            sender_id="sender_operator",
            session="gs",
            seq=next(seq),
            row_id=f"m_half_ii{index}",
            scope=keep_scope("sessionkeepother"),
        )
    await seed_message_legacy(
        conn, sender_id="sender_operator", session="gs", seq=next(seq), row_id="m_sound"
    )


def _assert_refused_byte_inert(result: MigrateGovernedResult, before: Any, after: Any, *, label: str) -> None:
    assert result.refused is True, f"{label}: expected a refusal: {result!r}"
    assert (result.scanned, result.already_migrated, result.backfilled) == (None, None, 0), (
        f"{label}: a refusal serves None for what it did not measure and backfilled 0: {result!r}"
    )
    assert before == after, f"{label}: the refusal WROTE (the sound row must not be stamped either)"


class TestTheMessageLegServesOneRefusalInCheckOrder63cIAa28:
    async def test_am26_RS1_dangling_and_half_pair_are_ONE_refusal_dangling_first(self) -> None:
        """GREEN at ``169925f`` for the am-26 part (audit P3 — ``dangling_pos=27 < half_pos=244``); the
        amendment-26 pin, on the audit's RS-1 fixture verbatim: refused, ``None`` counts, ``backfilled == 0``,
        ``SELECT *`` byte-identical (``m_sound`` NOT stamped), BOTH diagnoses present with the dangling one
        FIRST (read from the served text only), each count (1 / 1) attributed INSIDE its own clause."""
        async with a19a._governed_world() as world:
            await _seed_rs1(world)
            before = await _snapshot(world.connection)
            result = await world.migrate(MESSAGE_TABLE)
            reason = str(result.reason or "")
            _assert_refused_byte_inert(result, before, await _snapshot(world.connection), label="RS-1")
            assert reason.find("dangling") != -1 and reason.find("half-applied") != -1, reason
            assert reason.find("dangling") < reason.find("half-applied"), (
                f"dangling must come first: {reason!r}"
            )
            assert (
                _clause_count(reason, _DANGLING_MARKER) == 1 and _clause_count(reason, _HALF_I_MARKER) == 1
            ), reason

    async def test_FORK2_order_then_dangling_then_half_pairs_in_ONE_refusal(self) -> None:
        """⚠ RED at ``169925f`` (audit F-4 / P3: only the ORDER refusal is served — ``dangling_pos=-1``; two
        round
        trips). amendment 27 FORK-2 on a DISCRIMINATING population (``_FORK2_COUNTS``): ONE refusal naming the
        ORDER guard's un-migrated agents, the dangling senders, and BOTH message halves — in THAT order — each
        with its own count INSIDE its own clause (F-8: a build that swaps or pools the counts reds),
        byte-inert,
        ``None`` receipts. CONTROL: migrate ``agent`` (the ORDER remedy the operator must run first), re-run
        ``message`` → the remaining clauses only, same counts, still byte-inert."""
        async with a19a._governed_world() as world:
            await _seed_fork2(world)
            before = await _snapshot(world.connection)
            result = await world.migrate(MESSAGE_TABLE)
            reason = str(result.reason or "")
            _assert_refused_byte_inert(result, before, await _snapshot(world.connection), label="FORK-2")
            positions = [
                reason.find(marker)
                for marker in (_ORDER_MARKER, _DANGLING_MARKER, _HALF_I_MARKER, _HALF_II_MARKER)
            ]
            assert -1 not in positions and positions == sorted(positions), (
                f"FORK-2: ONE refusal, every check in CHECK ORDER (ORDER → dangling → half i → half ii): "
                f"positions={positions}: {reason!r}"
            )
            attributed = {
                "order": _clause_count(reason, _ORDER_MARKER),
                "dangling": _clause_count(reason, _DANGLING_MARKER),
                "half_i": _clause_count(reason, _HALF_I_MARKER),
                "half_ii": _clause_count(reason, _HALF_II_MARKER),
            }
            assert attributed == _FORK2_COUNTS, (
                f"F-8: each clause must state ITS OWN count: attributed={attributed} want={_FORK2_COUNTS}: "
                f"{reason!r}"
            )
            agent_result = await world.migrate(AGENT_TABLE)
            assert agent_result.refused is False and agent_result.backfilled == _FORK2_COUNTS["order"], (
                agent_result
            )
            before_again = await _snapshot(world.connection)
            again = await world.migrate(MESSAGE_TABLE)
            reason_again = str(again.reason or "")
            _assert_refused_byte_inert(
                again, before_again, await _snapshot(world.connection), label="FORK-2 control"
            )
            assert _ORDER_MARKER not in reason_again, (
                f"CONTROL: the ORDER clause must be gone: {reason_again!r}"
            )
            assert {
                "dangling": _clause_count(reason_again, _DANGLING_MARKER),
                "half_i": _clause_count(reason_again, _HALF_I_MARKER),
                "half_ii": _clause_count(reason_again, _HALF_II_MARKER),
            } == {key: _FORK2_COUNTS[key] for key in ("dangling", "half_i", "half_ii")}, reason_again

    async def test_FORK2_the_verb_level_refusal_stays_a_separate_EARLIER_answer(self) -> None:
        """GREEN at ``169925f``; RED on a build that folds the store-class refusal into the message leg's one
        refusal (amendment 27 FORK-2: "the verb-level §2.1 refusal is a STORE fact and stays a separate,
        earlier
        answer — the only precedence this packet keeps"). The FORK-2 population plus ONE foreign-owned-but-
        unscoped agent: the §2.1 teaching (adjudicate BY HAND before migrating ANY governed table) is served
        ALONE — no message-leg clause — byte-inert."""
        async with a19a._governed_world() as world:
            await _seed_fork2(world)  # its migrated senders already provisioned the two foreign principals
            foreign = await world.principal_store.get_by_email("foreign-a@example.com")
            assert foreign is not None, "fixture: _seed_migrated_senders provisions foreign-a"
            await seed_agent_governed(
                world.connection,
                row_id="owned_unscoped",
                name="owned-unscoped",
                session="gs",
                owner_principal=_bare(foreign.id),
                owner_agent=None,
                scope=None,
            )
            before = await _snapshot(world.connection)
            result = await world.migrate(MESSAGE_TABLE)
            reason = str(result.reason or "")
            _assert_refused_byte_inert(result, before, await _snapshot(world.connection), label="verb-level")
            assert "by hand" in reason.lower() and "any governed table" in reason.lower(), reason
            assert "before migrating `message`" not in reason, (
                "the verb-level refusal must stand ALONE — the message leg's own refusal (its by-hand remedy "
                f"for `message`) is a LATER answer (amendment 27 FORK-2): {reason!r}"
            )


# =========================================================================== #
# amendment 28 Addendum A5 — the message backfill self-guards on the SENDER's state: its WHERE gains
# ``sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE`` (a dangling sender dereferences to NONE
# —
# store-ref §6.4 — and is excluded by the same clause). The golden (``test_message_enforcement_63b_ii_a.py::
# _MIGRATE_MESSAGE_GOLDEN``) carries it; the redirect leg proves it on rows.
# =========================================================================== #


class TestTheMessageBackfillGuardsTheSender63cIAa28:
    async def test_A5_an_ownerless_or_dangling_senders_message_is_never_stamped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at ``169925f`` (the WHERE does not read the sender: every unsound message is stamped). THE
        shared preconditions redirected at a clean store (so the refusals in front of the write cannot fire —
        the race the guard exists for). Population — one unsound sender per conjunct, so a guard missing
        EITHER
        conjunct reds: a message from an OWNERLESS-UNSCOPED (legacy) sender and from a DANGLING sender (both
        conjuncts exclude them), from an OWNED-BUT-UNSCOPED sender (only ``sender.scope IS NOT NONE`` excludes
        it) and from an OWNERLESS-BUT-SCOPED sender (only ``sender.owner_principal IS NOT NONE`` excludes it),
        plus one SOUND message from a migrated sender. The leg proceeds, ``backfilled == 1`` (== the rows that
        changed), the sound row is stamped, and the four unsound rows are byte-identical."""
        async with a19a._governed_world() as world, a19a._governed_world() as clean:
            conn = world.connection
            await a19a._seed_migrated_senders(world)
            await seed_agent_legacy(conn, row_id="ownerless_sender", name="ownerless-sender", session="gs")
            await seed_message_legacy(
                conn, sender_id="ownerless_sender", session="gs", seq=1, row_id="m_ownerless_sender"
            )
            await seed_message_legacy(conn, sender_id="ghost_sender", session="gs", seq=2, row_id="m_ghost")
            await seed_agent_governed(
                conn,
                row_id="owned_unscoped_sender",
                name="owned-unscoped-sender",
                session="gs",
                owner_principal=world.operator_bare,
                owner_agent=None,
                scope=None,
            )
            await seed_message_legacy(
                conn, sender_id="owned_unscoped_sender", session="gs", seq=4, row_id="m_owned_unscoped_sender"
            )
            await seed_agent_governed(
                conn,
                row_id="ownerless_scoped_sender",
                name="ownerless-scoped-sender",
                session="gs",
                owner_principal=None,
                owner_agent=None,
                scope=keep_scope("sessionkeepgs"),
            )
            await seed_message_legacy(
                conn,
                sender_id="ownerless_scoped_sender",
                session="gs",
                seq=5,
                row_id="m_ownerless_scoped_sender",
            )
            await seed_message_legacy(
                conn, sender_id="sender_operator", session="gs", seq=3, row_id="m_sound"
            )
            await a19a._seed_clean_single_principal_store(clean)
            calls = _redirect_the_shared_preconditions(monkeypatch, clean.handle)
            unsound = (
                "SELECT * FROM message WHERE id IN [message:m_ownerless_sender, message:m_ghost, "
                "message:m_owned_unscoped_sender, message:m_ownerless_scoped_sender] ORDER BY id"
            )
            unsound_before = await run(conn, unsound)
            before = await run(conn, "SELECT * FROM message ORDER BY id")
            result = await world.migrate(MESSAGE_TABLE)
            after = await run(conn, "SELECT * FROM message ORDER BY id")
            assert calls["count"] >= 1, "the redirect never landed (#194)"
            assert result.refused is False, f"the leg must proceed under the redirect: {result!r}"
            assert await run(conn, unsound) == unsound_before, (
                "amendment 28 A5: a message whose SENDER is ownerless/unscoped or dangling was stamped — the "
                "backfill WHERE must guard sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE"
            )
            assert result.backfilled == 1 == _rows_changed(before, after), (
                f"exactly the sound message is stamped, and backfilled says so: {result!r}"
            )


# =========================================================================== #
# amendment 28 Addendum A2 — an unexpected ``INFO FOR DB`` shape (non-dict, or a dict without ``tables``) and
# a
# non-list precondition-row answer FAIL CLOSED: a typed STORE error naming the dependency and the shape
# received, byte-inert — never a clean-store verdict (Leg 2: dependency × wrong-shape ⇒ identical bytes = a
# false clear). The forgery legs; the real answer is the control.
# =========================================================================== #

_INFO_SHAPES: dict[str, Any] = {"list": [], "str": "garbage", "keyless-dict": {"analyzers": {}}}
_ROW_SHAPES: dict[str, Any] = {"dict": {"id": "x"}, "str": "garbage"}


def _forge(monkeypatch: pytest.MonkeyPatch, *, match: Callable[[str], bool], forged: Any) -> dict[str, int]:
    """Rebind ``principals.run_query`` so a statement ``match`` accepts returns ``forged`` (the real query
    still
    RUNS first — the dependency answered, in the wrong shape). Returns a landed-counter (#194)."""
    real = vars(principals)["run_query"]
    landed = {"count": 0}

    async def forging(*args: Any, **kwargs: Any) -> Any:
        answer = await real(*args, **kwargs)
        if match(str(kwargs.get("statement", ""))):
            landed["count"] += 1
            return forged
        return answer

    monkeypatch.setattr(principals, "run_query", forging)
    return landed


async def _seed_fail_open_population(world: Any) -> None:
    """A legacy agent + its legacy message + a legacy memory row: a fail-OPEN build (every precondition read
    empty) runs the message leg and stamps the message with owner NONE."""
    await seed_agent_legacy(world.connection, row_id="legacy_0", name="legacy-0", session="s1")
    await seed_message_legacy(world.connection, sender_id="legacy_0", session="s1", seq=1, row_id="m1")
    await seed_memory_legacy(world.connection, row_id="legacy_memory", dim=_DIM)


class TestAWrongShapedDependencyFailsClosed63cIAa28:
    @pytest.mark.parametrize("shape", sorted(_INFO_SHAPES))
    @pytest.mark.parametrize("table", _MIGRATE_TABLES)
    async def test_A2_an_unexpected_INFO_FOR_DB_shape_raises_byte_inert(
        self, monkeypatch: pytest.MonkeyPatch, table: str, shape: str
    ) -> None:
        """⚠ RED at ``169925f`` (``defined = … else {}``: the verb reads an empty store and proceeds). The
        ``INFO FOR DB`` answer forged to ``shape``: ``migrate_governed`` RAISES a ``SurrealStoreError`` whose
        text names ``INFO FOR DB`` and the type received; every governed table (and keep / household /
        principal) is byte-identical. CONTROL: the real answer returns a receipt (no raise)."""
        async with a19a._governed_world() as control_world, a19a._governed_world() as world:
            await _seed_fail_open_population(control_world)
            control = await control_world.migrate(table)
            assert isinstance(control, MigrateGovernedResult), (
                f"CONTROL: the real answer returns a receipt: {control!r}"
            )
            await _seed_fail_open_population(world)
            landed = _forge(
                monkeypatch,
                match=lambda statement: statement.strip().upper() == "INFO FOR DB",
                forged=_INFO_SHAPES[shape],
            )
            before = await _snapshot(world.connection)
            with pytest.raises(SurrealStoreError) as caught:
                await world.migrate(table)
            assert landed["count"] >= 1, "the forgery never landed (#194)"
            text = str(caught.value)
            assert "INFO FOR DB" in text and type(_INFO_SHAPES[shape]).__name__ in text, (
                f"the store error must name the dependency and the shape received: {text!r}"
            )
            assert await _snapshot(world.connection) == before, (
                f"--table {table}: a wrong-shaped INFO answer WROTE"
            )

    @pytest.mark.parametrize("shape", sorted(_ROW_SHAPES))
    @pytest.mark.parametrize("table", [AGENT_TABLE, MESSAGE_TABLE])
    async def test_A2_a_non_list_precondition_row_answer_raises_byte_inert(
        self, monkeypatch: pytest.MonkeyPatch, table: str, shape: str
    ) -> None:
        """⚠ RED at ``169925f`` (``_governed_select`` reads a non-list as "no rows"). Every precondition ROW
        read (a ``SELECT id, …`` through ``principals.run_query``) forged to ``shape``: ``migrate_governed``
        RAISES a ``SurrealStoreError`` naming the type received; byte-inert."""
        async with a19a._governed_world() as world:
            await _seed_fail_open_population(world)
            landed = _forge(
                monkeypatch,
                match=lambda statement: statement.strip().upper().startswith("SELECT ID"),
                forged=_ROW_SHAPES[shape],
            )
            before = await _snapshot(world.connection)
            with pytest.raises(SurrealStoreError) as caught:
                await world.migrate(table)
            assert landed["count"] >= 1, "the forgery never landed (#194)"
            assert type(_ROW_SHAPES[shape]).__name__ in str(caught.value), str(caught.value)
            assert await _snapshot(world.connection) == before, (
                f"--table {table}: a wrong-shaped row answer WROTE"
            )


# =========================================================================== #
# amendment 28 Addendum A4 as RULED by amendment 30 (FK-a28-1 = Reading B): the counts a precondition MEASURED
# are TYPED fields — ``MigrateGovernedResult.preconditions: MigratePreconditionCounts | None`` (six ``int |
# None``
# fields; ``None`` = not measured on this run) — and the ``reason`` text restates them DERIVED from the fields
# by
# ONE render function (never a second source). Pins: shape; measured values per population; (1) perturb each
# field (∀ ``model_fields``, derived) → the reason follows; (2) every integer in the reason (id samples and
# citations stripped) is a field value; (3) the MP-E legs read the fields (a19b KP2/KP3). The docstrings say
# what the code does.
# =========================================================================== #

#: The RULED field SPEC — amendment 30's six + amendment 31's two, name → annotation, VERBATIM from the
#: rulings.
#: Read ONLY by the SHAPE pin (a spec check: deriving a shape from the model it checks is a tautology). Every
#: BEHAVIOUR pin below iterates the model's OWN ``model_fields`` (amendment 32 §3), and every population dict
#: is
#: completeness-checked against ``model_fields`` — a new field reds each population by name.
_OWNER_CLASSIFICATIONS = Literal["operator", "foreign", "mixed", "unclassified"]
_RULED_FIELD_SPEC: dict[str, object] = {
    "unscoped_agents": int | None,
    "owned_but_unscoped_agents": int | None,
    "scoped_but_ownerless_agents": int | None,
    "dangling_sender_messages": int | None,
    "owned_but_unscoped_messages": int | None,
    "scoped_but_ownerless_messages": int | None,
    "distinct_owner_principals": int | None,
    "owner_classification": _OWNER_CLASSIFICATIONS | None,
}
#: THE perturbation of an ``int | None`` field (pin (1)): large enough that ``base + _PERTURBATION`` collides
#: with
#: no fixture count, no id sample and no citation.
_PERTURBATION = 1000
#: FK-a28b-2 (report §F): amendment 31's owner sentences — "owned by the operator …" names NO count; "owned by
#: N
#: other principal(s) …" names ``distinct_owner_principals``; "owners not classified …" names none. ``mixed``
#: is
#: unruled (my pick: it names N). GENERATED over the enum — completeness-checked against ``typing.get_args``.
_OWNER_SENTENCE_STATES_N: dict[str, bool] = {
    "operator": False,
    "foreign": True,
    "mixed": True,
    "unclassified": False,
}


def _counts_model() -> Any:
    """``loremaster.governed.MigratePreconditionCounts`` — read DYNAMICALLY (the static reference lives in the
    module's ``TYPE_CHECKING`` block, which is what registers this file's pending pins, #461's shape), so a
    build without it reds each pin with the ruling's name rather than failing collection."""
    model = getattr(governed_module, "MigratePreconditionCounts", None)
    if model is None:
        pytest.fail(
            "loremaster.governed.MigratePreconditionCounts does not exist — amendments 30/31: ONE nested "
            "model "
            f"of the measured precondition counts {tuple(_RULED_FIELD_SPEC)}, carried on "
            "MigrateGovernedResult.preconditions"
        )
    return model


def _counts(result: Any) -> dict[str, Any] | None:
    """``result.preconditions`` as a plain dict (``None`` stays ``None``) — failing by name if the field is
    absent."""
    if not any(item.name == "preconditions" for item in dataclasses.fields(result)):
        pytest.fail(
            "MigrateGovernedResult has no `preconditions` field — amendment 30: `preconditions: "
            "MigratePreconditionCounts | None`"
        )
    counts = result.preconditions
    return None if counts is None else {name: getattr(counts, name) for name in _counts_model().model_fields}


def _literal_members(annotation: object) -> tuple[Any, ...]:
    """The members of the ``Literal[...]`` inside ``annotation`` (``()`` when there is none) — derived by
    ``typing.get_args``, never a hand-picked pair (amendment 32 §3 F-3)."""
    return tuple(
        member
        for argument in typing.get_args(annotation)
        if typing.get_origin(argument) is Literal
        for member in typing.get_args(argument)
    )


def _perturbation_kind(annotation: object) -> str | None:
    """``"int"`` for ``int | None``, ``"literal"`` for ``Literal[...] | None``, else ``None`` — the
    completeness
    leg reds on ``None`` (a third field type must EXTEND the perturbation table, never be skipped)."""
    arguments = set(typing.get_args(annotation))
    if arguments == {int, type(None)}:
        return "int"
    if type(None) in arguments and _literal_members(annotation):
        return "literal"
    return None


def _perturbed_value(annotation: object, value: Any) -> Any:
    """The value pin (1) moves ``value`` to, chosen BY ANNOTATION: an int moves by ``_PERTURBATION``; a
    Literal
    member swaps to the next member (derived); anything else is returned unchanged."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value + _PERTURBATION
    members = _literal_members(annotation)
    if value in members:
        return members[(members.index(value) + 1) % len(members)]
    return value


def _states_its_count(field: str, expected: dict[str, Any]) -> bool:
    """Whether the ruled prose names ``field``'s value (pin (1) movement / pin (2) ⊇): every measured non-zero
    int does, except ``distinct_owner_principals`` under a classification whose ruled sentence names no count
    (FK-a28b-2, ``_OWNER_SENTENCE_STATES_N``)."""
    value = expected.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value == 0:
        return False
    if field == "distinct_owner_principals":
        return _OWNER_SENTENCE_STATES_N.get(str(expected.get("owner_classification")), False)
    return True


def _collection_time_fields() -> dict[str, object]:
    """name → annotation for pin (1)'s generated cases: THE model's own ``model_fields`` when it exists
    (amendment
    32 §3 — derived), else the ruled spec (at ``169925f`` there is no model to derive from at COLLECTION time;
    every case then reds by name on ``_counts_model``)."""
    model = getattr(governed_module, "MigratePreconditionCounts", None)
    if model is None:
        return dict(_RULED_FIELD_SPEC)
    return {name: info.annotation for name, info in model.model_fields.items()}


async def _seed_agent_population(world: Any) -> dict[str, int]:
    """P_agent — a VERB-level refusal on every table, every agent count DISTINCT: 2 legacy agents, 3
    operator-owned-but-unscoped agents (the E3 population — no foreign principal, so no owner-classification
    clause beyond the operator's), 4 ownerless-but-scoped agents. ⇒ unscoped 5, owned-but-unscoped 3,
    scoped-but-ownerless 4."""
    for index in range(2):
        await seed_agent_legacy(
            world.connection, row_id=f"legacy{index}", name=f"legacy{index}", session="pa"
        )
    for index in range(3):
        await seed_agent_governed(
            world.connection,
            row_id=f"owned{index}",
            name=f"owned{index}",
            session="pa",
            owner_principal=world.operator_bare,
            owner_agent=None,
            scope=None,
        )
    for index in range(4):
        await seed_agent_governed(
            world.connection,
            row_id=f"scopedonly{index}",
            name=f"scopedonly{index}",
            session="pa",
            owner_principal=None,
            owner_agent=None,
            scope=keep_scope("sessionkeeppa"),
        )
    return {"unscoped_agents": 5, "owned_but_unscoped_agents": 3, "scoped_but_ownerless_agents": 4}


async def _seed_foreign_owner_population(world: Any) -> None:
    """P_foreign — amendment 31's owner diagnosis on FOREIGN owners (a19's two real member principals): 2 + 3
    owned-but-unscoped agents across the two, 1 legacy agent ⇒ unscoped 6, owned-but-unscoped 5, distinct
    owners 2, classification ``foreign`` (every count DISTINCT from every other)."""
    foreign = await _seed_foreign_principals(world)
    for index in range(5):
        await seed_agent_governed(
            world.connection,
            row_id=f"fowned{index}",
            name=f"fowned{index}",
            session="pf",
            owner_principal=foreign[0] if index < 2 else foreign[1],
            owner_agent=None,
            scope=None,
        )
    await seed_agent_legacy(world.connection, row_id="flegacy", name="flegacy", session="pf")


async def _seed_mixed_owner_population(world: Any) -> None:
    """P_mixed — the operator owns 2 owned-but-unscoped agents and each of a19's two foreign principals owns
    1;
    2 legacy agents ⇒ unscoped 6, owned-but-unscoped 4, distinct owners 3, classification ``mixed``."""
    foreign = await _seed_foreign_principals(world)
    for index, owner in enumerate((world.operator_bare, world.operator_bare, foreign[0], foreign[1])):
        await seed_agent_governed(
            world.connection,
            row_id=f"mowned{index}",
            name=f"mowned{index}",
            session="pm",
            owner_principal=owner,
            owner_agent=None,
            scope=None,
        )
    for index in range(2):
        await seed_agent_legacy(
            world.connection, row_id=f"mlegacy{index}", name=f"mlegacy{index}", session="pm"
        )


async def _seed_unclassified_owner_population(world: Any) -> None:
    """P_unclassified — a SECOND admin makes the operator unresolvable (a19a's fixture shape): the second
    admin
    owns 2 owned-but-unscoped agents, a foreign member 1; 2 legacy agents ⇒ unscoped 5, owned-but-unscoped 3,
    distinct owners 2, classification ``unclassified``."""
    second_admin = await world.principal_store.create(email="second-admin@example.com", role="admin")
    foreign = await _seed_foreign_principals(world)
    for index, owner in enumerate((_bare(second_admin.id), _bare(second_admin.id), foreign[0])):
        await seed_agent_governed(
            world.connection,
            row_id=f"uowned{index}",
            name=f"uowned{index}",
            session="pu",
            owner_principal=owner,
            owner_agent=None,
            scope=None,
        )
    for index in range(2):
        await seed_agent_legacy(
            world.connection, row_id=f"ulegacy{index}", name=f"ulegacy{index}", session="pu"
        )


#: population → (seeder, table, expected fields — COMPLETE over ``model_fields``, checked by every pin).
#: P_message is FORK-2's discriminating population.
_POPULATIONS: dict[str, tuple[Callable[[Any], Awaitable[Any]], str, dict[str, Any]]] = {
    "P_agent": (
        _seed_agent_population,
        AGENT_TABLE,
        {
            "unscoped_agents": 5,
            "owned_but_unscoped_agents": 3,
            "scoped_but_ownerless_agents": 4,
            "dangling_sender_messages": None,
            "owned_but_unscoped_messages": None,
            "scoped_but_ownerless_messages": None,
            "distinct_owner_principals": 1,
            "owner_classification": "operator",
        },
    ),
    "P_foreign": (
        _seed_foreign_owner_population,
        AGENT_TABLE,
        {
            "unscoped_agents": 6,
            "owned_but_unscoped_agents": 5,
            "scoped_but_ownerless_agents": 0,
            "dangling_sender_messages": None,
            "owned_but_unscoped_messages": None,
            "scoped_but_ownerless_messages": None,
            "distinct_owner_principals": 2,
            "owner_classification": "foreign",
        },
    ),
    "P_mixed": (
        _seed_mixed_owner_population,
        AGENT_TABLE,
        {
            "unscoped_agents": 6,
            "owned_but_unscoped_agents": 4,
            "scoped_but_ownerless_agents": 0,
            "dangling_sender_messages": None,
            "owned_but_unscoped_messages": None,
            "scoped_but_ownerless_messages": None,
            "distinct_owner_principals": 3,
            "owner_classification": "mixed",
        },
    ),
    "P_message": (
        _seed_fork2,
        MESSAGE_TABLE,
        {
            "unscoped_agents": _FORK2_COUNTS["order"],
            "owned_but_unscoped_agents": 0,
            "scoped_but_ownerless_agents": 0,
            "dangling_sender_messages": _FORK2_COUNTS["dangling"],
            "owned_but_unscoped_messages": _FORK2_COUNTS["half_i"],
            "scoped_but_ownerless_messages": _FORK2_COUNTS["half_ii"],
            "distinct_owner_principals": 0,
            "owner_classification": None,
        },
    ),
}

#: RS-1's measured counts (the audit's fixture: one ghost-sender legacy message, one owned-but-unscoped
#: message, one sound legacy message; every agent migrated — so the agent facts were MEASURED as ``0``,
#: amendment 32 §2 Reading A; no owned-but-unscoped agent, so no owner to classify — FK-a28b-2).
_RS1_COUNTS: dict[str, Any] = {
    "unscoped_agents": 0,
    "owned_but_unscoped_agents": 0,
    "scoped_but_ownerless_agents": 0,
    "dangling_sender_messages": 1,
    "owned_but_unscoped_messages": 1,
    "scoped_but_ownerless_messages": 0,
    "distinct_owner_principals": 0,
    "owner_classification": None,
}

#: FK-a28b-3 (report §F): the UNCLASSIFIED population serves the unresolved-operator teaching, whose principal
#: /
#: admin counts ("(N principals, M admins)") are no field — so it is EXCLUDED from pin (2)'s ⊆ leg (amendment
#: 31
#: is silent; surfaced) and exercised by the served-fields pin and pin (1) (the classification swap must move
#: the owner sentence even with no operator resolved: "no prose branch keys on anything but the enum").
_UNCLASSIFIED_POPULATION: dict[str, tuple[Callable[[Any], Awaitable[Any]], str, dict[str, Any]]] = {
    "P_unclassified": (
        _seed_unclassified_owner_population,
        AGENT_TABLE,
        {
            "unscoped_agents": 5,
            "owned_but_unscoped_agents": 3,
            "scoped_but_ownerless_agents": 0,
            "dangling_sender_messages": None,
            "owned_but_unscoped_messages": None,
            "scoped_but_ownerless_messages": None,
            "distinct_owner_principals": 2,
            "owner_classification": "unclassified",
        },
    ),
}
_ALL_POPULATIONS = {**_POPULATIONS, **_UNCLASSIFIED_POPULATION}

#: Integers the served text may carry that are NOT counts (amendment 30: "the bounded id samples … are the
#: ONLY
#: integers reason may carry that are not in the fields"; amendment 31: principal-id samples likewise) — the
#: row-id sample phrase, the principal-id sample phrase, plus CITATION shapes (§2.1, pkt-62–63b, amendment-1,
#: E3), which are references, not numbers.
_NON_COUNT_SHAPES = (
    r"First \d+ of \d+ (?:ids )?shown",
    r"\(first \d+ named",
    r"§\d+(?:\.\d+)*",
    r"pkt-[\w–-]+",
    r"amendment[- ]\d+",
    r"\bE\d+\b",
)


def _count_integers(reason: str, identifiers: list[str]) -> list[int]:
    """Every integer ``reason`` states once the stored ids and the non-count shapes are stripped."""
    residue = reason
    for identifier in sorted(identifiers, key=len, reverse=True):
        residue = residue.replace(identifier, " ")
    for shape in _NON_COUNT_SHAPES:
        residue = re.sub(shape, " ", residue)
    return [int(token) for token in re.findall(r"\d+", residue)]


async def _population_identifiers(world: Any) -> list[str]:
    """Every stored id / principal id / keep marker a refusal may name (stripped before counting integers)."""
    ids: list[str] = ["sessionkeeppa", "sessionkeepgs", "sessionkeepother"]
    for table in (AGENT_TABLE, MESSAGE_TABLE, "principal"):
        ids += [_bare(value) for value in await run(world.connection, f"SELECT VALUE id FROM {table}")]
        ids += [str(value) for value in await run(world.connection, f"SELECT VALUE id FROM {table}")]
    ids += [f"ghost{index}" for index in range(10)] + ["ghost_sender"]
    return ids


def _perturbed_counts_class(real: type[BaseModel], field: str) -> type[BaseModel]:
    """A subclass of THE counts model whose construction moves ``field`` by ANNOTATION (``_perturbed_value``)
    —
    the mutation instrument of amendment 30 pin (1), generalised by amendment 32 §3: a reason DERIVED from the
    served model moves with it; a reason composed from private values does not."""
    from pydantic import model_validator  # noqa: PLC0415 - scaffold-local

    annotation = real.model_fields[field].annotation

    class PerturbedCounts(real):  # type: ignore[misc, valid-type]
        @model_validator(mode="before")
        @classmethod
        def _perturb(cls, data: Any) -> Any:
            if isinstance(data, dict) and field in data:
                return {**data, field: _perturbed_value(annotation, data[field])}
            return data

    return PerturbedCounts


def _assert_complete(label: str, expected: dict[str, Any]) -> None:
    """A population must name EVERY field of the model (amendment 32 §3) — a new field reds it by name."""
    fields = set(_counts_model().model_fields)
    assert set(expected) == fields, (
        f"{label}: the population's expected dict must cover exactly the model's fields — missing "
        f"{sorted(fields - set(expected))}, surplus {sorted(set(expected) - fields)}"
    )


class TestTheMeasuredCountsAreTypedFields63cIAa28:
    def test_am30_the_counts_model_has_exactly_the_ruled_fields(self) -> None:
        """⚠ RED at ``169925f`` (no model). amendments 30 + 31: ``MigratePreconditionCounts`` carries EXACTLY
        the
        eight ruled fields, in the ruled order, each with its ruled annotation (``int | None`` ×7 and the
        owner-classification ``Literal[...] | None``); every field defaults to ``None`` (not measured); it is
        ``extra="forbid"`` (an unknown count is REFUSED, never carried); ``MigrateGovernedResult`` carries it
        as
        ``preconditions``, defaulting to ``None``. DUAL (amendment 32 §3 F-1): was six names; the values below
        are DERIVED from the spec's annotations, never a hand-typed six-element list."""
        from pydantic import ValidationError  # noqa: PLC0415 - scaffold-local

        model = _counts_model()
        assert tuple(model.model_fields) == tuple(_RULED_FIELD_SPEC), (
            f"amendments 30/31 name exactly these fields, in this order: {tuple(_RULED_FIELD_SPEC)}; got "
            f"{tuple(model.model_fields)}"
        )
        for name, annotation in _RULED_FIELD_SPEC.items():
            assert model.model_fields[name].annotation == annotation, (
                f"{name}: ruled annotation {annotation!r}, got {model.model_fields[name].annotation!r}"
            )
        all_none = model()
        assert all(getattr(all_none, name) is None for name in _RULED_FIELD_SPEC), all_none
        measured = {
            name: (index if _perturbation_kind(annotation) == "int" else _literal_members(annotation)[0])
            for index, (name, annotation) in enumerate(_RULED_FIELD_SPEC.items())
        }
        assert {name: getattr(model(**measured), name) for name in _RULED_FIELD_SPEC} == measured
        with pytest.raises(ValidationError):
            model(surplus_count=1)
        field = {item.name: item for item in dataclasses.fields(MigrateGovernedResult)}.get("preconditions")
        assert field is not None and field.default is None, (
            "MigrateGovernedResult.preconditions must exist and default to None (amendment 30)"
        )

    def test_am32_every_field_has_a_perturbation_by_annotation(self) -> None:
        """⚠ RED at ``169925f`` (no model). amendment 32 §3 F-3 COMPLETENESS: pin (1) perturbs a field BY ITS
        ANNOTATION — ``int | None`` moves by ``_PERTURBATION``, ``Literal[...] | None`` swaps members. A field
        of any OTHER annotation must extend the perturbation table, never be silently skipped: this reds by
        name.
        Also: the owner-sentence table covers EXACTLY the classification enum (generated over its members)."""
        model = _counts_model()
        unperturbable = {
            name: info.annotation
            for name, info in model.model_fields.items()
            if _perturbation_kind(info.annotation) is None
        }
        assert not unperturbable, (
            f"fields with no perturbation by annotation {unperturbable!r} — extend `_perturbation_kind` / "
            "`_perturbed_value` (amendment 32 §3: never skip a field)"
        )
        members = {
            member for info in model.model_fields.values() for member in _literal_members(info.annotation)
        }
        assert members == set(_OWNER_SENTENCE_STATES_N), (
            "the owner-sentence table must cover exactly the classification members: "
            f"enum {sorted(members)}, table {sorted(_OWNER_SENTENCE_STATES_N)}"
        )

    @pytest.mark.parametrize("population", sorted(_ALL_POPULATIONS))
    async def test_am30_the_served_fields_are_the_measured_counts(self, population: str) -> None:
        """⚠ RED at ``169925f``. Each population's refusal serves, in ``preconditions``, what its precondition
        MEASURED — the agent facts on every table (read at the verb), the message facts only on ``--table
        message`` (``None`` elsewhere: the read was gated off), and amendment 31's owner diagnosis (the
        distinct
        owners and the classification). DUAL (amendment 32 §3 F-2): expectations cover ``model_fields``."""
        seed, table, expected = _ALL_POPULATIONS[population]
        _assert_complete(population, expected)
        async with a19a._governed_world() as world:
            await seed(world)
            result = await world.migrate(table)
            assert result.refused is True, result
            assert _counts(result) == expected, (
                f"{population} (--table {table}): served {_counts(result)!r}, measured {expected!r}"
            )

    @pytest.mark.parametrize(
        ("label", "table", "expected"),
        [
            pytest.param("invalid-table", "agnet", None, id="invalid-table"),
            pytest.param(
                "clean-memory-proceeds",
                MEMORY_TABLE,
                {
                    "unscoped_agents": 0,
                    "owned_but_unscoped_agents": 0,
                    "scoped_but_ownerless_agents": 0,
                    "dangling_sender_messages": None,
                    "owned_but_unscoped_messages": None,
                    "scoped_but_ownerless_messages": None,
                    "distinct_owner_principals": 0,
                    "owner_classification": None,
                },
                id="clean-memory-proceeds",
            ),
        ],
    )
    async def test_am30_None_means_not_measured(self, label: str, table: str, expected: Any) -> None:
        """⚠ RED at ``169925f``. An invalid ``--table`` evaluates NO precondition (zero store I/O) ⇒
        ``preconditions is None``; a PROCEEDING run evaluated the verb's agent reads ⇒ measured zeros for the
        agent facts, ``None`` for the message facts it never read (``--table memory``)."""
        if expected is not None:
            _assert_complete(label, expected)
        async with a19a._governed_world() as world:
            await a19a._seed_clean_single_principal_store(world)
            result = await world.migrate(table)
            assert _counts(result) == expected, f"{label}: served {_counts(result)!r}, want {expected!r}"

    async def test_am30_pin1_every_field_is_exercised_by_some_population(self) -> None:
        """⚠ RED at ``169925f`` (no model). ∀ ``model_fields`` (DERIVED): some population MEASURES the field
        at a
        value pin (1) can move and the prose names — else pin (1) is vacuous for it (a field no population
        exercises reds by name)."""
        model = _counts_model()
        unexercised = [
            name
            for name, info in model.model_fields.items()
            if not any(
                _states_its_count(name, expected)
                or (_perturbation_kind(info.annotation) == "literal" and expected.get(name) is not None)
                for _seed, _table, expected in _ALL_POPULATIONS.values()
            )
        ]
        assert not unexercised, f"no population exercises {unexercised} for pin (1) — add one (∀ fields)"

    @pytest.mark.parametrize(
        ("field", "population"),
        [
            pytest.param(field, population, id=f"{field}-{population}")
            for population, (_seed, _table, expected) in sorted(_ALL_POPULATIONS.items())
            for field, annotation in _collection_time_fields().items()
            if _states_its_count(field, expected)
            or (_literal_members(annotation) and expected.get(field) is not None)
        ],
    )
    async def test_am30_pin1_perturbing_a_field_moves_the_reason(
        self, monkeypatch: pytest.MonkeyPatch, field: str, population: str
    ) -> None:
        """⚠ RED at ``169925f`` (no model). amendment 30 pin (1), generalised by amendment 32 §3 F-3: THE
        counts
        model is rebound EVERYWHERE (by identity) to a subclass that moves ``field`` BY ANNOTATION at
        construction. The served ``preconditions.<field>`` is the moved value (the mutation LANDED, #194) AND
        the reason follows — an int field's moved value is STATED (a reason composed from private ints does
        not
        move); a classification swap changes the owner SENTENCE (the reason differs from the same store's
        unperturbed reason, and every other served field is unchanged). The (field, population) cases are
        generated from the populations, over the ruled spec (the completeness of the spec vs ``model_fields``
        is the shape pin; the exercise completeness is the pin above)."""
        model = _counts_model()
        assert field in model.model_fields, f"{field} is not a field of the counts model"
        seed, table, expected = _ALL_POPULATIONS[population]
        async with a19a._governed_world() as world:
            await seed(world)
            baseline = await world.migrate(table)
            with monkeypatch.context() as patch:
                patched = patch_shared_object_everywhere(
                    patch,
                    "MigratePreconditionCounts",
                    model,
                    _perturbed_counts_class(model, field),
                    expect_in=("loremaster.governed",),
                )
                result = await world.migrate(table)
            served = _counts(result)
            moved = _perturbed_value(model.model_fields[field].annotation, expected[field])
            assert served is not None and served[field] == moved, (
                f"{population}: the perturbation never LANDED on the served field (patched {patched}) — the "
                f"counts must be constructed through THE model's constructor: {served!r}"
            )
            assert {name: value for name, value in served.items() if name != field} == {
                name: value for name, value in expected.items() if name != field
            }, f"{population}: only {field} may move: {served!r}"
            if isinstance(moved, int):
                identifiers = await _population_identifiers(world)
                assert moved in _count_integers(str(result.reason or ""), identifiers), (
                    f"{population}: preconditions.{field} was perturbed to {moved} and the reason did NOT "
                    "follow — its count clause is not DERIVED from the served field (amendment 30: ONE "
                    f"render function over the model, never ints passed alongside): {result.reason!r}"
                )
            else:
                assert result.reason != baseline.reason, (
                    f"{population}: owner_classification was swapped {expected[field]!r} → {moved!r} and the "
                    "reason did NOT change — the owner sentence is not derived from the field (amendment 31: "
                    f"'no prose branch keys on anything but the enum'): {result.reason!r}"
                )

    @pytest.mark.parametrize("population", [*sorted(_POPULATIONS), "RS-1"])
    async def test_am30_pin2_every_count_in_the_reason_is_a_field_value(self, population: str) -> None:
        """⚠ RED at ``169925f`` (no fields to read). amendment 30 pin (2), BOTH directions: (⊆) every integer
        the reason states — stored ids, the bounded row-id / principal-id sample phrases and citation shapes
        stripped (amendment 31) — is the value of some served ``preconditions`` field; (⊇) every count the
        population MEASURES non-zero and the ruled prose names is stated (``_states_its_count``; a reason that
        renders a count clause as ``None`` / omits it would pass ⊆ alone — measured: wrong build M19, a28 §6).
        The ⊇ leg iterates the expected dict, which covers ``model_fields`` (amendment 32 §3)."""
        async with a19a._governed_world() as world:
            if population == "RS-1":
                await _seed_rs1(world)
                table, expected = MESSAGE_TABLE, _RS1_COUNTS
            else:
                seed, table, expected = _POPULATIONS[population]
                await seed(world)
            _assert_complete(population, expected)
            result = await world.migrate(table)
            served = _counts(result) or {}
            values = {
                value for value in served.values() if isinstance(value, int) and not isinstance(value, bool)
            }
            stated = _count_integers(str(result.reason or ""), await _population_identifiers(world))
            stray = [number for number in stated if number not in values]
            assert result.refused is True and not stray, (
                f"{population}: the reason states {stray} — integers that are no field value "
                f"{served!r} (amendment 30 pin (2) ⊆): {result.reason!r}"
            )
            unstated = {
                name: expected[name]
                for name in expected
                if _states_its_count(name, expected) and expected[name] not in stated
            }
            assert not unstated, (
                f"{population}: measured counts {unstated} are NOT stated in the reason (amendment 30: the "
                f"reason RESTATES the counts, derived from the fields — pin (2) ⊇): {result.reason!r}"
            )

    def test_A4_no_docstring_claims_a_refusal_scans_nothing(self) -> None:
        """⚠ RED at ``169925f`` (``MigrateGovernedResult`` and ``principals._refused`` say "a refusal returns
        before any scan of the target table" — false for ``agent`` and ``message``, blindreader F-6). The
        prose
        that describes the receipt says what the code DOES."""
        for owner, doc in (
            ("MigrateGovernedResult", MigrateGovernedResult.__doc__),
            ("principals._refused", principals._refused.__doc__),
            ("principals.migrate_governed", principals.migrate_governed.__doc__),
        ):
            assert "before any scan" not in (doc or "").lower(), (
                f"{owner}'s docstring still claims a refusal returns before any scan of the target table — "
                "amendment 28 A4: derive the prose from the behaviour"
            )


# =========================================================================== #
# amendment 32 §2 (FK-ADV-2, Reading A) — a ``preconditions`` field is ``None`` IFF ITS READ WAS GATED OFF, on
# EVERY outcome (verb-level refusal, leg refusal, success). ``_agent_migration_preconditions`` has exactly two
# gates: the agent facts run iff ``agent`` is DEFINED; the message facts run iff ``--table message`` AND
# ``message`` is DEFINED. The describe names every MEASURED, NON-ZERO problem in check order (agent problems,
# dangling senders, message half-pairs) — so a verb-level refusal on ``--table message`` NAMES the message
# half-pairs it measured. (Amendment 31 FK-a28-4 is an ERRATUM, both halves — amendment 32 §2.)
# =========================================================================== #

#: The two gated READS (amendment 32 §2: "gated by exactly two facts"): the table each read needs DEFINED, and
#: the ``--table`` it additionally needs (``None`` = every table). A field belongs to the message read iff its
#: name ends ``_messages`` — every other field is an agent fact (distinct owners and the classification are
#: read from the agent rows); the partition is completeness-checked against ``model_fields`` below.
_GATED_READS: dict[str, tuple[str, str | None]] = {
    "agent": (AGENT_TABLE, None),
    "message": (MESSAGE_TABLE, MESSAGE_TABLE),
}
#: The four store shapes (amendment 32 §2.2): which of the two gated tables are REMOVED from the store.
_STORE_SHAPES: dict[str, tuple[str, ...]] = {
    "both-defined": (),
    "agent-only": (MESSAGE_TABLE,),
    "message-only": (AGENT_TABLE,),
    "neither-defined": (AGENT_TABLE, MESSAGE_TABLE),
}
_LEG_TABLES = (AGENT_TABLE, MEMORY_TABLE, MESSAGE_TABLE)
#: The two message half-pair clause markers, TABLE-qualified: the agent half-pair clause carries the same
#: "carry an owner but no scope" words, so a verb-level refusal naming BOTH needs the noun to tell them apart.
_AGENT_HALF_I_MARKER = f"agent row(s) {_HALF_I_MARKER}"
_MESSAGE_HALF_I_MARKER = f"message row(s) {_HALF_I_MARKER}"


def _read_of(field: str) -> str:
    """Which gated read measures ``field`` (see ``_GATED_READS``)."""
    return "message" if field.endswith("_messages") else "agent"


def _read_ran(read: str, table: str, removed: tuple[str, ...]) -> bool:
    needs_defined, needs_table = _GATED_READS[read]
    return needs_defined not in removed and (needs_table is None or table == needs_table)


async def _seed_both_half_pairs(world: Any, *, agent_rows: int, message_rows: int) -> None:
    """``agent_rows`` operator-owned-but-unscoped agents (the §2.1 half-pair → a VERB-level refusal) beside
    ``message_rows`` owned-but-unscoped messages (message half-pair (i)) from a migrated sender."""
    await a19a._seed_migrated_senders(world)
    for index in range(agent_rows):
        await seed_agent_governed(
            world.connection,
            row_id=f"hp_agent{index}",
            name=f"hp-agent{index}",
            session="hp",
            owner_principal=world.operator_bare,
            owner_agent=None,
            scope=None,
        )
    for index in range(message_rows):
        await seed_message_legacy(
            world.connection,
            sender_id="sender_operator",
            session="gs",
            seq=index + 1,
            row_id=f"hp_message{index}",
            owner_principal=RecordID("principal", world.operator_bare),
        )


async def _seed_message_half_pair_behind_a_migratable_agent(world: Any, *, message_rows: int) -> None:
    """Migrated senders + ONE legacy agent (so ``--table agent`` PROCEEDS) + ``message_rows``
    owned-but-unscoped
    messages: after the agent leg, ``--table message`` meets the message LEG's own refusal."""
    await a19a._seed_migrated_senders(world)
    await seed_agent_legacy(world.connection, row_id="lone_legacy", name="lone-legacy", session="gs")
    for index in range(message_rows):
        await seed_message_legacy(
            world.connection,
            sender_id="sender_operator",
            session="gs",
            seq=index + 1,
            row_id=f"leg_message{index}",
            owner_principal=RecordID("principal", world.operator_bare),
        )


class TestAFieldIsNoneIffItsReadWasGatedOff63cIAa28b:
    def test_am32_the_read_partition_covers_every_field(self) -> None:
        """⚠ RED at ``169925f`` (no model). COMPLETENESS of the gating pin's domain: every ``model_fields``
        member belongs to exactly one of the two gated reads, and both reads own ≥1 field."""
        fields = tuple(_counts_model().model_fields)
        owners = {read: [field for field in fields if _read_of(field) == read] for read in _GATED_READS}
        assert all(owners.values()), f"a gated read owns no field: {owners}"
        assert sorted(field for group in owners.values() for field in group) == sorted(fields), owners

    @pytest.mark.parametrize("shape", sorted(_STORE_SHAPES))
    @pytest.mark.parametrize("table", _LEG_TABLES)
    async def test_am32_a_field_is_None_iff_its_read_was_gated_off(self, table: str, shape: str) -> None:
        """⚠ RED at ``169925f`` (no field). amendment 32 §2.2, GENERATED over ``{agent, memory, message}`` ×
        the four store shapes (the two gated tables REMOVED or not; a memory-only store is ``INFO FOR DB``
        without ``agent``): ∀ ``model_fields``, the served field is ``None`` iff its read was gated off — a
        clean single-principal store (the VALUE of a measured count is not this pin's clause — removing
        ``agent`` makes the legacy message's sender dangle, and that IS measured); ``owner_classification`` is
        ``None``
        throughout (no owner to classify — FK-a28b-2). Where the verb RAISES, the pin requires the raise to
        come only when the ``--table`` target itself is undefined (the leg reads its own table — report
        residual R-a28b-3), never a raise from the precondition read."""
        removed = _STORE_SHAPES[shape]
        async with a19a._governed_world() as world:
            await a19a._seed_clean_single_principal_store(world)
            for gone in removed:
                await run(world.connection, f"REMOVE TABLE {gone}")
            try:
                result = await world.migrate(table)
            except SurrealStoreError as error:
                assert table in removed, (
                    f"--table {table} on a {shape} store RAISED {type(error).__name__}: {error} — only a leg "
                    "whose OWN target table is undefined may raise; the precondition read is gated"
                )
                return
            served = _counts(result)
            assert served is not None, f"{table}/{shape}: a valid table must serve preconditions: {result!r}"
            wrong = {
                field: value
                for field, value in served.items()
                if field != "owner_classification"
                and (value is None) == _read_ran(_read_of(field), table, removed)
            }
            assert not wrong, (
                f"--table {table} on a {shape} store: fields {wrong} break 'None iff the read was gated off' "
                f"(amendment 32 §2.1) — served {served!r}"
            )
            assert served["owner_classification"] is None, served

    async def test_am32_a_verb_level_refusal_on_message_names_every_measured_problem(self) -> None:
        """⚠ RED at ``169925f``. amendment 32 §2.2 (i): an agent half-pair (2) AND a message half-pair (3) on
        ``--table message`` → the VERB-level refusal (the decision is unchanged: the verb refuses on the agent
        half-pair); every field is MEASURED (the verb read both); the reason names BOTH problems, agent first
        (check order), each count inside its own clause and equal to its field; it keeps the verb's ANY-table
        remedy and never the leg's "before migrating `message`" one; byte-inert."""
        async with a19a._governed_world() as world:
            await _seed_both_half_pairs(world, agent_rows=2, message_rows=3)
            before = await _snapshot(world.connection)
            result = await world.migrate(MESSAGE_TABLE)
            reason = str(result.reason or "")
            _assert_refused_byte_inert(
                result, before, await _snapshot(world.connection), label="verb+message"
            )
            served = _counts(result)
            assert served is not None and all(value is not None for value in served.values()), (
                f"amendment 32 §2: the verb READ both the agent and the message facts, so every field is "
                f"measured (the owners: the operator): {served!r}"
            )
            assert served["owner_classification"] == "operator", served
            assert served["owned_but_unscoped_agents"] == 2 and served["owned_but_unscoped_messages"] == 3, (
                served
            )
            positions = [reason.find(_AGENT_HALF_I_MARKER), reason.find(_MESSAGE_HALF_I_MARKER)]
            assert -1 not in positions and positions == sorted(positions), (
                f"amendment 32 §2.1: the verb-level refusal names every MEASURED problem, agent first — "
                f"positions={positions}: {reason!r}"
            )
            assert (
                _clause_count(reason, _AGENT_HALF_I_MARKER),
                _clause_count(reason, _MESSAGE_HALF_I_MARKER),
            ) == (
                served["owned_but_unscoped_agents"],
                served["owned_but_unscoped_messages"],
            ), reason
            assert "any governed table" in reason.lower() and "before migrating `message`" not in reason, (
                reason
            )

    @pytest.mark.parametrize("grown", ["agent", "message"])
    async def test_am32_one_more_half_pair_row_moves_its_count_and_sentence(self, grown: str) -> None:
        """⚠ RED at ``169925f``. amendment 32 §2.2 perturbation: the same store with ONE more half-pair row in
        ``grown``'s table → exactly the matching served count AND its clause's count move by one; the other
        stays."""
        base, plus = {"agent_rows": 2, "message_rows": 3}, {"agent_rows": 2, "message_rows": 3}
        plus[f"{grown}_rows"] += 1
        served_texts: list[tuple[dict[str, Any] | None, str]] = []
        for rows in (base, plus):
            async with a19a._governed_world() as world:
                await _seed_both_half_pairs(world, **rows)
                result = await world.migrate(MESSAGE_TABLE)
                served_texts.append((_counts(result), str(result.reason or "")))
        (base_counts, base_reason), (plus_counts, plus_reason) = served_texts
        assert base_counts is not None and plus_counts is not None, served_texts
        field, marker = {
            "agent": ("owned_but_unscoped_agents", _AGENT_HALF_I_MARKER),
            "message": ("owned_but_unscoped_messages", _MESSAGE_HALF_I_MARKER),
        }[grown]
        other_field, other_marker = {
            "agent": ("owned_but_unscoped_messages", _MESSAGE_HALF_I_MARKER),
            "message": ("owned_but_unscoped_agents", _AGENT_HALF_I_MARKER),
        }[grown]
        assert plus_counts[field] == base_counts[field] + 1, (base_counts, plus_counts)
        assert plus_counts[other_field] == base_counts[other_field], (base_counts, plus_counts)
        assert _clause_count(plus_reason, marker) == plus_counts[field], plus_reason
        assert _clause_count(plus_reason, other_marker) == _clause_count(base_reason, other_marker), (
            plus_reason
        )

    async def test_am32_the_message_leg_refusal_serves_measured_agent_zeros(self) -> None:
        """⚠ RED at ``169925f``. amendment 32 §2.2 (ii): after ``--table agent`` PROCEEDS, ``--table message``
        meets the message LEG's own refusal (a message half-pair): the agent facts are MEASURED ``0`` (the
        verb
        read them — Reading A; amendment 31's "agent fields None" is the erratum), the message facts measured;
        the reason names only the message problem (its count = its field) and the leg's own remedy."""
        async with a19a._governed_world() as world:
            await _seed_message_half_pair_behind_a_migratable_agent(world, message_rows=3)
            agent_result = await world.migrate(AGENT_TABLE)
            assert agent_result.refused is False, agent_result
            before = await _snapshot(world.connection)
            result = await world.migrate(MESSAGE_TABLE)
            reason = str(result.reason or "")
            _assert_refused_byte_inert(result, before, await _snapshot(world.connection), label="message leg")
            served = _counts(result)
            expected = {
                "unscoped_agents": 0,
                "owned_but_unscoped_agents": 0,
                "scoped_but_ownerless_agents": 0,
                "dangling_sender_messages": 0,
                "owned_but_unscoped_messages": 3,
                "scoped_but_ownerless_messages": 0,
                "distinct_owner_principals": 0,
                "owner_classification": None,
            }
            _assert_complete("message-leg refusal", expected)
            assert served == expected, f"served {served!r}, measured {expected!r}"
            assert (
                _AGENT_HALF_I_MARKER not in reason and _clause_count(reason, _MESSAGE_HALF_I_MARKER) == 3
            ), reason
            assert "before migrating `message`" in reason, reason

    @pytest.mark.parametrize("table", [AGENT_TABLE, MESSAGE_TABLE])
    async def test_am32_success_serves_the_measured_object(self, table: str) -> None:
        """⚠ RED at ``169925f``. amendment 32 §2.2 success: a PROCEEDING run serves what it measured — on
        ``--table message`` every count field measured (sound store: all ``0``), on ``--table agent`` the
        message
        fields ``None`` (never read). A measured count does not become a lie on the happy path."""
        async with a19a._governed_world() as world:
            await a19a._seed_migrated_senders(world)
            await seed_agent_legacy(world.connection, row_id="ok_legacy", name="ok-legacy", session="gs")
            await seed_message_legacy(
                world.connection, sender_id="sender_operator", session="gs", seq=1, row_id="m_ok"
            )
            if table == MESSAGE_TABLE:
                assert (await world.migrate(AGENT_TABLE)).refused is False
            result = await world.migrate(table)
            assert result.refused is False, result
            served = _counts(result)
            assert served is not None, result
            expected = {
                "unscoped_agents": 1 if table == AGENT_TABLE else 0,  # read BEFORE the agent leg stamped it
                "owned_but_unscoped_agents": 0,
                "scoped_but_ownerless_agents": 0,
                "dangling_sender_messages": 0 if table == MESSAGE_TABLE else None,
                "owned_but_unscoped_messages": 0 if table == MESSAGE_TABLE else None,
                "scoped_but_ownerless_messages": 0 if table == MESSAGE_TABLE else None,
                "distinct_owner_principals": 0,
                "owner_classification": None,
            }
            _assert_complete(f"success --table {table}", expected)
            assert served == expected, f"--table {table}: served {served!r}, measured {expected!r}"
