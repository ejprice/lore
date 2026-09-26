"""Contract — packet 63c wave i-a, the a19b ADDENDUM (the LAST contract round, amendment 24 §5's STOP-rule
close). Authored by ``contract-63c-i-a-a19b`` (Opus 5.5 contract author — CONTRACT TESTS ONLY, no production
code).

THE SPEC IS THE RULING: ``docs/design/2026-09-26-packet63c-amendment-24.md`` (``301f9b1``) §W 1–6.

TWO KINDS OF PIN LIVE HERE, and the difference is their GRADING:
* **Graded probes, landed AST-equal** (amendment 24 §5 / amendment 17's definition — the graded PROGRAM): the
  ``test_KP*`` functions and ``_admitting`` are the adversary's §A.3 kill probes from
  ``REPORT-adversary-63c-i-a-a19a.md`` (``58f73b4``), each GREEN on its reference build and RED on the wrong
  build it names (§4 there). KP1 = MP-B (created-vs-found raced against a concurrent winner, FK-b reading A);
  KP2/KP3 = MP-E (the two new id samples perturbed under THE constant); KP4 = MP-C (the race serves the
  registry's teaching); KP5/KP6 = MP-D (the reverse direction ∀ ``_REFUSAL_CASES``, registry AND handler);
  KP7a/b/c = MP-F (FK-a reading A: every refusal serves ``None`` for a count it did not measure); KP8 = door
  #1 (ONE refusal names BOTH agent half-pairs); KP13 = MP-A's property on its own input (the ∀ runtime form
  lives beside ``_REFUSAL_FIXTURES`` in ``test_fixwave_a19a_63c_i_a.py``); KP14 = MP-G (a failed session-keep
  mint is never an ownerless register). They read ``a19a.<helper>`` exactly as pasted; the receipt
  (``ast_equiv``) is in the a19b report.
* **Authored pins (NEW production behaviour — graded by the cold audit, amendment 24 §5):** door #2 (a message
  half-pair refuses the MESSAGE leg, through THE shared preconditions function) + its D2 leg (``backfilled`` =
  the rows the UPDATE STAMPED), and door #4b (a FAILED compensation serves the registry's teaching + ONE
  appended line naming the left-behind keep and its remedy). The D2 leg has no graded probe in the adversary's
  §A.3 either.

STORE LAW (``docs/reference/surrealdb-31-capabilities.md`` — cited, never re-transcribed): §1.4 (legacy /
half-pair rows are SEEDED under the DDL, never constructed through a writer — no writer produces a message
half-pair), §2 (``SELECT *`` omits a NONE column, so byte-identity compares whole rows). Live TEST store
``ws://127.0.0.1:18000`` (NEVER :18500), one unique database per world, reaped. No skip marker."""

from __future__ import annotations

import re
from typing import Any

import pytest
import test_fixwave_a19a_63c_i_a as a19a  # module-qualified: its Test* classes must not be re-collected
from _governed_contract import (
    AGENT_TABLE,
    MEMORY_TABLE,
    MESSAGE_TABLE,
    credentialed_app_context,
    seed_agent_governed,
    seed_agent_legacy,
    seed_message_legacy,
)
from _surreal_harness import run
from loremaster.agents import AgentRegistry, AgentRegistryError
from loremaster.sanitise import CONTROL_CHAR_PATTERN
from lorerunes.pdp import keep_scope
from surrealdb import RecordID
from test_fixwave_a19_63c_i_a import _bare, _redirect_the_shared_preconditions, _snapshot

from loremaster import principals

_DIM = a19a._DIM


# --------------------------------------------------------------------------- KP1 — created-vs-found
async def test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """A concurrent register of ANOTHER of alice's agents wins the session-keep mint between the handler's
    preflight and its own mint (so this call FINDS the keep), then the race refusal fires. The keep this call
    merely found must survive (amendment 22 §1.2: created-only, derived from the mint's RETURN)."""
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
    ) as world:
        ctx, admin_conn = world["ctx"], world["admin_conn"]
        world["holder"]["email"] = world["emails"]["alice"]
        session = "wave-winner"
        keep_store = ctx._keep_store
        real = keep_store.get_or_create_keyed
        calls = {"n": 0}

        async def spy(*args: Any, **kwargs: Any) -> Any:
            calls["n"] += 1
            if calls["n"] == 1:
                await real(*args, **kwargs)  # the concurrent winner's mint
                found = await real(*args, **kwargs)  # THIS call finds it
                await ctx.agent_registry.register("raced-agent", session=session, role="scout")
                return found
            return await real(*args, **kwargs)

        monkeypatch.setattr(keep_store, "get_or_create_keyed", spy)
        with pytest.raises(AgentRegistryError):
            await ctx.comms(action="register", agent="raced-agent", session=session, role="builder")
        assert calls["n"] == 1, calls
        keys = await run(admin_conn, f"SELECT VALUE key FROM keep WHERE key = 'session:{session}'")
        assert keys == [f"session:{session}"], (
            "the compensation deleted a session keep this call merely FOUND (a concurrent winner's): "
            f"{keys!r}"
        )


# ------------------------------------------------------------------------- KP2 / KP3 — ONE bound, perturbed
async def test_KP2_the_dangling_sender_sample_reads_THE_constant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(principals, "_REFUSAL_ID_SAMPLE_SIZE", 3)
    async with a19a._governed_world() as world:
        pairs = await a19a._seed_ghost_store(world, ghosts=5)
        reason = str((await world.migrate(MESSAGE_TABLE)).reason or "")
        by_message = sum(1 for message_id, _s in pairs if a19a._names(reason, MESSAGE_TABLE, message_id))
        by_sender = sum(1 for _m, sender_id in pairs if a19a._names(reason, AGENT_TABLE, sender_id))
        assert "dangling" in reason.lower(), reason
        assert max(by_message, by_sender) == 3 and by_message <= 3 and by_sender <= 3, (
            f"patched bound 3 over 5 ghosts: named by message {by_message}, by sender {by_sender}: {reason!r}"
        )


async def test_KP3_the_half_applied_id_sample_is_bounded_by_THE_constant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(principals, "_REFUSAL_ID_SAMPLE_SIZE", 3)
    async with a19a._governed_world() as world:
        ids = [f"half_{index:03d}" for index in range(5)]
        for index, row_id in enumerate(ids):
            await seed_agent_governed(
                world.connection,
                row_id=row_id,
                name=f"half-{index}",
                session="hp",
                owner_principal=None,
                owner_agent=None,
                scope=keep_scope("sessionkeephp"),
            )
        reason = str((await world.migrate(AGENT_TABLE)).reason or "")
        named = sum(1 for row_id in ids if a19a._names(reason, AGENT_TABLE, row_id))
        assert "half-applied" in reason.lower() and named == 3, f"named {named} of 5 (bound 3): {reason!r}"
        assert 5 in a19a._stated_integers(reason, identifiers=[*ids, "sessionkeephp"]), reason


# ------------------------------------------------------------ KP4 — the race serves the registry's teaching
async def test_KP4_the_race_refusal_is_the_registrys_own_teaching(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
    ) as world:
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        session = "wave-race-teach"

        async def conflicting_register() -> None:
            await ctx.agent_registry.register("raced-agent", session=session, role="scout")

        a19a._spy_the_mint(monkeypatch, ctx, after_real=conflicting_register)
        with pytest.raises(AgentRegistryError) as caught:
            await ctx.comms(action="register", agent="raced-agent", session=session, role="builder")
        with pytest.raises(AgentRegistryError) as direct:
            await ctx.agent_registry.register("raced-agent", session=session, role="builder")
        assert (type(caught.value), str(caught.value)) == (type(direct.value), str(direct.value)), (
            f"served={caught.value!r} registry={direct.value!r}"
        )


# ---------------------------------------------------------- KP5 / KP6 — reverse direction ∀ derived classes
async def _admitting(self: Any, name: str, *, session: str, **_kwargs: Any) -> Any:
    """Admits every refusal but still returns the existing row (so a re-register UPDATEs, never re-CREATEs).
    """
    row = await self._select_row(self._agent_id(session, name))
    return self._row_to_agent(row) if row is not None else None


@pytest.mark.parametrize(("class_name", "case"), a19a._REFUSAL_CASES)
async def test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any, class_name: str, case: Any
) -> None:
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
    ) as world:
        ctx = world["ctx"]
        kwargs = await case.setup(ctx)
        monkeypatch.setattr(AgentRegistry, "preflight", _admitting)
        direct = kwargs.copy()
        try:
            await ctx.agent_registry.register(
                direct.pop("agent"), session=direct.pop("session"), role=direct.pop("role"), **direct
            )
        except AgentRegistryError as error:
            pytest.fail(
                f"{class_name}/{case.variant}: register refused with preflight admitting — a PRIVATE "
                f"copy of the decision: {error}"
            )


@pytest.mark.parametrize(("class_name", "case"), a19a._REFUSAL_CASES)
async def test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any, class_name: str, case: Any
) -> None:
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
    ) as world:
        ctx = world["ctx"]
        kwargs = await case.setup(ctx)
        world["holder"]["email"] = world["emails"]["alice"]
        monkeypatch.setattr(AgentRegistry, "preflight", _admitting)
        try:
            await ctx.comms(action="register", **kwargs)
        except AgentRegistryError as error:
            pytest.fail(
                f"{class_name}/{case.variant}: the HANDLER refused with preflight admitting — a "
                f"PRIVATE copy of the decision: {error}"
            )


# ------------------------------------------------------------ KP7 — F-3 on the LEG-level refusals (door #3)
async def test_KP7a_the_order_refusal_serves_no_unmeasured_count() -> None:
    async with a19a._governed_world() as world:
        await seed_agent_legacy(world.connection, row_id="legacy_0", name="legacy-0", session="s1")
        await seed_message_legacy(world.connection, sender_id="legacy_0", session="s1", seq=1)
        a19a._assert_no_unmeasured_count(await world.migrate(MESSAGE_TABLE), label="order refusal")


async def test_KP7b_the_dangling_refusal_serves_no_unmeasured_count() -> None:
    async with a19a._governed_world() as world:
        await a19a._seed_ghost_store(world, ghosts=1)
        a19a._assert_no_unmeasured_count(await world.migrate(MESSAGE_TABLE), label="dangling refusal")


@pytest.mark.parametrize("table", [AGENT_TABLE, MEMORY_TABLE, MESSAGE_TABLE])
async def test_KP7c_the_operator_only_refusal_serves_no_unmeasured_count(table: str) -> None:
    async with a19a._governed_world() as world:
        await world.principal_store.create(email="second-admin@example.com", role="admin")
        if table == MESSAGE_TABLE:  # the order guard must pass, so the operator refusal is the one reached
            await a19a._seed_clean_single_principal_store(world)
        else:
            await seed_agent_legacy(world.connection, row_id="legacy_0", name="legacy-0", session="s1")
        result = await world.migrate(table)
        assert "operator" in str(result.reason or "").lower(), result
        a19a._assert_no_unmeasured_count(result, label=f"operator-only refusal ({table})")


# -------------------------------------------------------------- KP8 — both half-pairs: BOTH named (door #1)
async def test_KP8_both_half_pairs_are_both_named() -> None:
    async with a19a._governed_world() as world:
        foreign = await a19a._seed_foreign_principals(world)
        owned_ids = [f"owned_unscoped_{index}" for index in range(2)]
        for index, owner in enumerate(foreign):
            await seed_agent_governed(
                world.connection,
                row_id=owned_ids[index],
                name=f"owned-unscoped-{index}",
                session="hp",
                owner_principal=owner,
                owner_agent=None,
                scope=None,
            )
        half_ids = await a19a._seed_half_applied_store(world)
        reason = str((await world.migrate(AGENT_TABLE)).reason or "")
        stated = a19a._stated_integers(reason, identifiers=[*half_ids, *owned_ids, *foreign, "sessionkeephp"])
        assert "half-applied" in reason.lower() and 3 in stated, (
            f"the ownerless-scoped half is not named: {reason!r}"
        )
        assert re.search(r"carry an owner but no scope", reason) and 2 in stated, (
            f"the owned-but-unscoped half is not named: {reason!r}"
        )


# --------------------------------------------------------------- KP13 — a new raise SITE of a covered class
async def test_KP13_a_register_refused_on_a_cadence_conflict_mints_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """Property form (∀ refused registers ⇒ zero mints), driven on an input no a19a fixture uses: a
    re-register with a DIFFERENT cadence. A correct build ACCEPTS it (cadence is mutable); a build that
    refuses it must do so before the mint."""
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
    ) as world:
        ctx = world["ctx"]
        await ctx.agent_registry.register("shared-name", session="wave-cad", role="builder", cadence="≤5m")
        world["holder"]["email"] = world["emails"]["alice"]
        calls = a19a._spy_the_mint(monkeypatch, ctx)
        try:
            await ctx.comms(
                action="register", agent="shared-name", session="wave-cad", role="builder", cadence="≤9m"
            )
        except AgentRegistryError:
            assert calls["count"] == 0, (
                "a refused register reached the keep mint (#485 shape, a new raise SITE)"
            )


# ------------------------------------------------------------------------ KP14 — a failed keep mint is LOUD
async def test_KP14_a_failed_session_keep_mint_is_never_an_ownerless_register(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    from loremaster.keeps import KeepStoreError

    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
    ) as world:
        ctx, admin_conn = world["ctx"], world["admin_conn"]
        world["holder"]["email"] = world["emails"]["alice"]

        async def failing_mint(*_a: Any, **_k: Any) -> Any:
            raise KeepStoreError("injected: the session keep mint failed")

        monkeypatch.setattr(ctx._keep_store, "get_or_create_keyed", failing_mint)
        with pytest.raises(KeepStoreError):
            await ctx.comms(action="register", agent="mint-fail", session="wave-mint-fail", role="builder")
        rows = await run(admin_conn, "SELECT VALUE name FROM agent WHERE session = 'wave-mint-fail'")
        assert rows == [], f"a credentialed register whose keep mint FAILED wrote an agent row: {rows!r}"


# =========================================================================== #
# AUTHORED — door #2 (amendment 24 §2 + amendment 25 Reading A): a message row with exactly ONE column of the
# governed pair set is the message table's HALF-PAIR, both halves symmetric with agents — (i) owned-but-
# unscoped (``owner_principal`` set, ``scope`` NONE: CD-1's self-guarding WHERE never stamps it, so it would
# sit un-migrated forever beside ``refused=False`` — adversary a19a SP2, PROBED) and (ii) scoped-but-ownerless
# (``scope`` set, ``owner_principal`` NONE). THE shared preconditions function's message leg (beside FK-2's
# dangling check) REFUSES them in ONE refusal: each half with its own count + bounded ids, "half-applied",
# byte-inert, ``None`` receipts. Reachable through NO writer (a tokenless send is denied; the governed send
# stamps both columns; the legacy path writes all three NONE) — seeded, like E3.
# =========================================================================== #

_OWNED_UNSCOPED_MESSAGES = 2  # (i) — ≥2, ≠ (ii), ≠ the ONE sound legacy message: a stated count discriminates
_SCOPED_OWNERLESS_MESSAGES = 3  # (ii)
_HALVES = {
    "owned-unscoped": (_OWNED_UNSCOPED_MESSAGES, 0),
    "scoped-ownerless": (0, _SCOPED_OWNERLESS_MESSAGES),
    "both-halves": (_OWNED_UNSCOPED_MESSAGES, _SCOPED_OWNERLESS_MESSAGES),
}


async def _seed_message_half_pair_store(
    world: Any, *, owned_unscoped: int, scoped_ownerless: int = 0, hostile: bool = False
) -> tuple[list[str], list[str]]:
    """SP2's population (adversary a19a §A.3): two migrated senders (operator + foreign), ONE sound legacy
    message ``m_legacy``, ``owned_unscoped`` messages owned by the operator with no scope (half i) and
    ``scoped_ownerless`` messages carrying a scope with no owner (half ii). ``hostile`` makes the FIRST row of
    each half a hostile stored id. Returns ``(half-i ids, half-ii ids)``."""
    await a19a._seed_migrated_senders(world)
    await seed_message_legacy(
        world.connection, sender_id="sender_operator", session="gs", seq=1, row_id="m_legacy"
    )
    owned_ids = [f"m_owned_unscoped_{index:03d}" for index in range(owned_unscoped)]
    scoped_ids = [f"m_scoped_ownerless_{index:03d}" for index in range(scoped_ownerless)]
    if hostile:
        for ids, marker in ((owned_ids, "i"), (scoped_ids, "ii")):
            if ids:
                ids[0] = f"{a19a._HOSTILE_ID}_{marker}"
    sequence = 2
    for row_id in owned_ids:
        await seed_message_legacy(
            world.connection,
            sender_id="sender_operator",
            session="gs",
            seq=sequence,
            row_id=row_id,
            owner_principal=RecordID("principal", world.operator_bare),
        )
        sequence += 1
    for row_id in scoped_ids:
        await seed_message_legacy(
            world.connection,
            sender_id="sender_operator",
            session="gs",
            seq=sequence,
            row_id=row_id,
            scope=keep_scope("sessionkeepother"),
        )
        sequence += 1
    return owned_ids, scoped_ids


def _message_identifiers(*id_lists: list[str]) -> list[str]:
    ids = [row_id for id_list in id_lists for row_id in id_list]
    return [*ids, "m_legacy", "sender_operator", "sender_foreign", "sessionkeepgs", "sessionkeepother"]


def _named(reason: str, ids: list[str]) -> int:
    return sum(1 for row_id in ids if a19a._names(reason, MESSAGE_TABLE, row_id))


class TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b:
    @pytest.mark.parametrize("halves", sorted(_HALVES))
    async def test_a_message_half_pair_refuses_the_message_leg_byte_inert(self, halves: str) -> None:
        """⚠ RED at ``84af63f`` (the leg PROCEEDS — SP2: the half-pair is never stamped, the migrate reports a
        clean cutover). TWIN CONTROL first: the same population WITHOUT the half-pair rows proceeds and stamps
        ``m_legacy`` — so the refusal below is caused by the half-pair. Then: refused, byte-inert (the sound
        row and the project keep untouched too), "half-applied" (never "multi-principal" / "dangling"), the
        TRUE count of EACH present half stated, EXACTLY ``min(_REFUSAL_ID_SAMPLE_SIZE, count)`` rows named PER
        HALF (``both-halves``: ONE refusal names each — amendment 25), the hostile stored ids rendered through
        THE sanitiser, and ``None`` for the counts no scan measured (FK-a)."""
        owned_count, scoped_count = _HALVES[halves]
        async with a19a._governed_world() as twin, a19a._governed_world() as world:
            await _seed_message_half_pair_store(twin, owned_unscoped=0)
            baseline = await twin.migrate(MESSAGE_TABLE)
            assert (baseline.refused, baseline.backfilled) == (False, 1), f"TWIN CONTROL: {baseline!r}"
            owned_ids, scoped_ids = await _seed_message_half_pair_store(
                world, owned_unscoped=owned_count, scoped_ownerless=scoped_count, hostile=True
            )
            before = await _snapshot(world.connection)
            result = await world.migrate(MESSAGE_TABLE)
            reason = str(result.reason or "")
            lowered = reason.lower()
            assert result.refused is True, f"{halves}: the message leg PROCEEDED over a half-pair: {result!r}"
            assert before == await _snapshot(world.connection), f"{halves}: the half-pair refusal WROTE"
            assert "half-applied" in lowered, f"{halves}: diagnose the message table HALF-APPLIED: {reason!r}"
            assert "multi-principal" not in lowered and "dangling" not in lowered, reason
            stated = a19a._stated_integers(reason, identifiers=_message_identifiers(owned_ids, scoped_ids))
            bound = principals._REFUSAL_ID_SAMPLE_SIZE
            for label, ids in (("owned-but-unscoped", owned_ids), ("scoped-but-ownerless", scoped_ids)):
                if not ids:
                    continue
                assert len(ids) in stated, (
                    f"{halves}: the TRUE count of {label} messages ({len(ids)}) must be stated: {reason!r}"
                )
                assert _named(reason, ids) == min(bound, len(ids)), (
                    f"{halves}: EXACTLY min({bound}, {len(ids)}) {label} rows must be named, got "
                    f"{_named(reason, ids)}: {reason!r}"
                )
            assert CONTROL_CHAR_PATTERN.search(reason) is None, (
                f"a stored id reached the line raw: {reason!r}"
            )
            a19a._assert_no_unmeasured_count(result, label=f"message half-pair refusal ({halves})")

    async def test_each_halfs_sample_is_bounded_by_THE_constant(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """amendment 20 §8.2's rider on the new lists (one constant, one perturbation), per half (amendment
        25: each half its own bounded ids): THE bound patched to 2 over 3 + 3 half-pair messages ⇒ exactly 2
        named in EACH half (a global cap would name 2 in total) and the true 3 stated."""
        monkeypatch.setattr(principals, "_REFUSAL_ID_SAMPLE_SIZE", 2)
        async with a19a._governed_world() as world:
            owned_ids, scoped_ids = await _seed_message_half_pair_store(
                world, owned_unscoped=3, scoped_ownerless=3
            )
            reason = str((await world.migrate(MESSAGE_TABLE)).reason or "")
            named = (_named(reason, owned_ids), _named(reason, scoped_ids))
            assert "half-applied" in reason.lower() and named == (2, 2), (
                f"named {named} (bound 2 per half): {reason!r}"
            )
            assert 3 in a19a._stated_integers(
                reason, identifiers=_message_identifiers(owned_ids, scoped_ids)
            ), reason

    @pytest.mark.parametrize("table", [AGENT_TABLE, MEMORY_TABLE])
    async def test_a_message_half_pair_refuses_the_MESSAGE_leg_only(self, table: str) -> None:
        """GREEN at ``84af63f``; REDDENS a build that puts the message half-pair check at the VERB — it is the
        message leg's precondition (beside FK-2's dangling check), not a store-class fact about agents/memory.
        """
        async with a19a._governed_world() as world:
            await _seed_message_half_pair_store(
                world, owned_unscoped=_OWNED_UNSCOPED_MESSAGES, scoped_ownerless=_SCOPED_OWNERLESS_MESSAGES
            )
            result = await world.migrate(table)
            assert result.refused is False, f"--table {table} refused over a MESSAGE half-pair: {result!r}"

    async def test_the_message_half_pair_decision_is_THE_shared_functions(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at ``84af63f`` (no shared function). FORWARD direction of sharing: the world is SOUND while
        THE shared preconditions function reads a store holding BOTH halves ⇒ the message leg refuses
        "half-applied", byte-inert. (The REVERSE direction — the shared function reads a clean store while the
        world holds the half-pairs ⇒ it proceeds — is the D2 / WHERE pin below.) TWIN BASELINE: the sound
        world un-redirected proceeds."""
        async with (
            a19a._governed_world() as twin,
            a19a._governed_world() as world,
            a19a._governed_world() as other,
        ):
            for target in (twin, world):
                await _seed_message_half_pair_store(target, owned_unscoped=0)
            await _seed_message_half_pair_store(
                other, owned_unscoped=_OWNED_UNSCOPED_MESSAGES, scoped_ownerless=_SCOPED_OWNERLESS_MESSAGES
            )
            baseline = await twin.migrate(MESSAGE_TABLE)
            assert baseline.refused is False, f"BASELINE (no redirect): {baseline!r}"
            calls = _redirect_the_shared_preconditions(monkeypatch, other.handle)
            before = await _snapshot(world.connection)
            result = await world.migrate(MESSAGE_TABLE)
            assert calls["count"] >= 1, "the message leg never CALLED the shared function"
            assert result.refused is True and "half-applied" in str(result.reason or "").lower(), (
                "THE shared function reads message half-pairs, yet the message leg did not refuse them — its "
                f"decision is a private copy (routing is not sharing): {result!r}"
            )
            assert before == await _snapshot(world.connection), "the redirected refusal WROTE"


# =========================================================================== #
# AUTHORED — door #2's D2 leg (amendment 24 §2 "independently") + amendment 25's WHERE leg. ``backfilled`` is
# the rows the UPDATE STAMPED — a MEASURED count (amendment 22 §4's principle), never the scope-keyed
# pre-count. The adversary's D2 build differs from a correct one ONLY on a message half-pair, which a correct
# build now REFUSES — so the pin redirects THE shared function at a clean store (the refusal cannot fire) and
# lets the leg run over BOTH halves: CD-1's self-guarding WHERE (it STAYS, amendment 25) must leave every
# half-pair row byte-identical, and ``backfilled`` must equal what was actually stamped.
# =========================================================================== #


class TestBackfilledIsTheRowsStamped63cIAa19b:
    async def test_backfilled_is_the_rows_the_UPDATE_stamped_never_the_pre_count(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at ``84af63f`` (no shared preconditions function to redirect — ``pytest.fail`` names it). RED
        on the adversary's D2 build (``backfilled`` = the scope-keyed pre-count: serves 3 then 2 while
        stamping 1 then 0) and on a WHERE that drops either conjunct (``scope IS NONE`` alone re-stamps half
        i; ``owner_principal IS NONE`` alone re-stamps half ii). Population: ``m_legacy`` + BOTH halves; THE
        shared function redirected at a clean store (which also proves the leg's half-pair decision is the
        SHARED one — the reverse direction). On the first run AND the idempotent second: the leg proceeds,
        ``backfilled`` equals the rows whose ``scope`` the run actually set, the counts are SCOPE-keyed
        (``already_migrated`` = rows carrying a scope — CD-1's count virtue, re-pinned by the a19b DUAL; an
        owner-keyed count serves 2 then 3), and every half-pair row is byte-identical (``SELECT *``,
        store-ref §2)."""
        async with a19a._governed_world() as world, a19a._governed_world() as clean:
            owned_ids, scoped_ids = await _seed_message_half_pair_store(
                world, owned_unscoped=_OWNED_UNSCOPED_MESSAGES, scoped_ownerless=_SCOPED_OWNERLESS_MESSAGES
            )
            half_pair_rows = "SELECT * FROM message WHERE id != message:m_legacy ORDER BY id"
            half_pairs_before = await run(world.connection, half_pair_rows)
            assert len(half_pairs_before) == len(owned_ids) + len(scoped_ids), half_pairs_before
            await a19a._seed_clean_single_principal_store(clean)
            calls = _redirect_the_shared_preconditions(monkeypatch, clean.handle)
            stamped_per_run = []
            for run_label in ("first", "second"):
                scoped_before = await run(
                    world.connection, "SELECT VALUE id FROM message WHERE scope IS NOT NONE"
                )
                result = await world.migrate(MESSAGE_TABLE)
                scoped_after = await run(
                    world.connection, "SELECT VALUE id FROM message WHERE scope IS NOT NONE"
                )
                stamped = len(scoped_after) - len(scoped_before)
                stamped_per_run.append(stamped)
                assert calls["count"] >= 1, "the message leg never CALLED the shared function"
                assert result.refused is False, (
                    f"{run_label}: THE shared function reads a clean store, yet the message leg refused — a "
                    f"private copy of the half-pair decision (routing is not sharing): {result!r}"
                )
                total = len(await run(world.connection, "SELECT VALUE id FROM message"))
                assert (result.scanned, result.already_migrated) == (total, len(scoped_before)), (
                    f"{run_label}: the counts must be SCOPE-keyed (amendment 21 CD-1, re-pinned here by the "
                    f"a19b DUAL): already_migrated = the {len(scoped_before)} row(s) carrying a scope, "
                    f"scanned = all {total}: {result!r}"
                )
                assert result.backfilled == stamped, (
                    f"{run_label}: backfilled={result.backfilled} but the run stamped {stamped} row(s) — a "
                    "served count must be the MEASURED rows the UPDATE stamped, never the scope-keyed "
                    f"pre-count (amendment 24 §2 / D2): {result!r}"
                )
                assert await run(world.connection, half_pair_rows) == half_pairs_before, (
                    f"{run_label}: the backfill WROTE a half-pair row — CD-1's self-guarding WHERE "
                    "(scope IS NONE AND owner_principal IS NONE) must leave both halves untouched even when "
                    "the refusal in front of it cannot fire (amendment 25: defence at the write)"
                )
            assert stamped_per_run == [1, 0], f"exactly m_legacy stamped, then nothing: {stamped_per_run}"


# =========================================================================== #
# AUTHORED — door #4b (amendment 24 §2): the race's created-only compensation FAILS (its delete raises). The
# registry's teaching SURVIVES verbatim (same class, same text — N8, the delete error replacing it, is
# rejected) and ONE appended line names the left-behind keep and its remedy (``lore-adm delete-keep``), so the
# ruled re-open trigger — "a failed compensation observed" — is observable by the one reader who can act.
# =========================================================================== #


class TestAFailedCompensationIsNamedToTheCaller63cIAa19b:
    async def test_a_FAILED_compensation_serves_the_teaching_plus_ONE_remedy_line(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """⚠ RED at ``84af63f`` (no compensation at all: the teaching is served bare, the keep silently left).
        SP4's construction (adversary a19a §A.3): a conflicting register injected after the real mint, and the
        compensation's ``delete_keep`` patched to raise. The served error: the registry's own class; its text
        STARTS WITH the registry's teaching byte-for-byte; what follows is exactly ONE newline-separated line
        naming the left-behind keep's id and ``lore-adm delete-keep``. The keep IS left behind (the stated
        bound), and the delete WAS attempted (the compensation path ran)."""
        from loremaster.keeps import KeepStoreError  # noqa: PLC0415 - scaffold-local

        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            world["holder"]["email"] = world["emails"]["alice"]
            session = "wave-comp-fail"
            deletes = {"count": 0}

            async def conflicting_register() -> None:
                await ctx.agent_registry.register("raced-agent", session=session, role="scout")

            async def failing_delete(*_args: Any, **_kwargs: Any) -> None:
                deletes["count"] += 1
                raise KeepStoreError("injected: the compensation's delete failed")

            a19a._spy_the_mint(monkeypatch, ctx, after_real=conflicting_register)
            monkeypatch.setattr(ctx._keep_store, "delete_keep", failing_delete)
            with pytest.raises(AgentRegistryError) as caught:
                await ctx.comms(action="register", agent="raced-agent", session=session, role="builder")
            with pytest.raises(AgentRegistryError) as direct:
                await ctx.agent_registry.register("raced-agent", session=session, role="builder")
            left = await run(admin_conn, f"SELECT VALUE id FROM keep WHERE key = 'session:{session}'")
            assert deletes["count"] >= 1, (
                "the compensation never ATTEMPTED the delete — the failure was not reached"
            )
            assert len(left) == 1, f"the failed compensation must leave the keep behind (the bound): {left!r}"
            served, teaching = str(caught.value), str(direct.value)
            assert type(caught.value) is type(direct.value), (
                "the served refusal must be the registry's own class (N8 — the delete error replacing the "
                f"teaching — is rejected): served={caught.value!r} registry={direct.value!r}"
            )
            assert served.startswith(teaching), (
                f"the registry's teaching must SURVIVE verbatim at the head:\n  served={served!r}\n  "
                f"teaching={teaching!r}"
            )
            appended = served[len(teaching) :]
            assert appended.startswith("\n") and appended.count("\n") == 1 and appended.strip(), (
                f"exactly ONE appended line must follow the teaching: {appended!r}"
            )
            keep_bare = _bare(left[0])
            assert keep_bare in appended and "lore-adm delete-keep" in appended, (
                f"the appended line must name the left-behind keep ({keep_bare}) and its remedy "
                f"(`lore-adm delete-keep`): {appended!r}"
            )
