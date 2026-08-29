"""Contract — packet 63a: #425 CLOSE — collapse ``stamp_owner``'s double read to ONE store
round-trip (design §5). RED before the 63a build; authored by ``contract-63a`` (Opus 4.8 contract
author — tests ONLY).

SPEC: ``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §5 (RULED CLOSE in 63a — the finding's
own re-open trigger, "63/64 introduces owner mutation", is pulled by §2.1's cutover ``owner_principal``
backfill, so carrying #425 as a bound would be a defect scheduled for discovery) + the §5 RIDER (the
62 security fixture re-run + ONE new leg: no window to inject a concurrent re-stamp into).

WHAT #425 CHANGES (survey-63a-pdp, confirmed against source): today ``stamp_owner`` makes TWO store
round-trips — ``registry.verify_capability`` (1 ``_query``) then ``registry.owner_principal_of`` (1
``_query``) — a TOCTOU window between them. The closure makes ``verify_capability``'s ONE verified
SELECT (which ALREADY projects ``owner_principal.email``) also yield the owner id, so ``stamp_owner``
reads ONCE and ``AgentRegistry.owner_principal_of`` is DELETED.

⚠ THE PINS ARE FORM-AGNOSTIC. The load-bearing property is "``stamp_owner`` issues EXACTLY ONE store
round-trip" + "``owner_principal_of`` is gone" — INDEPENDENT of whether the builder changes
``verify_capability``'s return type or adds a single-read pair path (see FORK 3 in
REPORT-contract-63a.md: literally changing ``verify_capability``'s return ``str → (str,str)`` would
falsify ~14 shipped 62 assertions of ``verify_capability(...) == agent.id``; the additive form closes
#425 with the SAME one-read/no-TOCTOU property and zero breakage — an operator/lead call). These pins
DO NOT pin ``verify_capability``'s return SHAPE, so they trap neither reading (C-DEF).

Live store: ws://127.0.0.1:18000 (NEVER :18500). Per-test unique DB, reaped; NO skip marker.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from fastmcp.server.auth import AccessToken
from loremaster.agents import AgentRegistry
from loremaster.principals import PrincipalStore

import loremaster

_EMAIL_ALICE = "alice@example.com"
_loremaster_stamp_owner = getattr(loremaster, "stamp_owner", None)


def _bare(record_id: str) -> str:
    return record_id.partition(":")[2] or record_id


def _token(email: str, *, role: str = "member") -> AccessToken:
    return AccessToken(
        token=f"tok-{email}",
        client_id=f"api_key:{email}",
        scopes=["lore:read", "lore:write"],
        subject=email,
        claims={"role": role, "agent": None, "key_name": "local"},
    )


@pytest_asyncio.fixture()
async def cap_env() -> Any:
    """A unified DB with a real ``AgentRegistry`` + ``PrincipalStore`` and alice as a principal —
    enough to register an owned agent (minting a real capability) and exercise ``stamp_owner``
    over live behaviour. Mirrors ``test_agent_capability_seams.seam_env``."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    principals = PrincipalStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    registry = AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await principals.ensure_ready()
    await registry.ensure_ready()
    alice = await principals.create(email=_EMAIL_ALICE)
    admin = await connect_admin(env)
    try:
        yield SimpleNamespace(
            env=env, registry=registry, principals=principals, admin=admin, alice_bare=_bare(alice.id)
        )
    finally:
        await admin.close()
        await registry.close()
        await principals.close()
        await drop_database(env)


async def _register_alice_worker(cap_env: Any) -> Any:
    result = await cap_env.registry.register(
        "alice_worker", session="s1", role="worker", owner_principal_id=cap_env.alice_bare
    )
    capability = getattr(result, "capability", None)
    assert capability, "capability mint unbuilt (62 wave 2) — cannot exercise stamp_owner"
    return result, capability


class TestOwnerPrincipalOfIsDeleted:
    """§5 — ``AgentRegistry.owner_principal_of`` is the SECOND read #425 removes; it is DELETED with
    the closure (``lore_impact`` @ 8128c50: its ONLY production consumer is ``stamp_owner``, which
    stops calling it). RED at HEAD (the method still exists)."""

    def test_owner_principal_of_no_longer_exists(self) -> None:
        """⚠ RED at HEAD. After #425 the method is GONE (its sole consumer no longer reads a second
        time). REDDENS a build that closes #425 but leaves the dead second-read method behind (a
        pattern a future mint would clone — ONE IMPLEMENTATION) OR that keeps calling it."""
        assert not hasattr(AgentRegistry, "owner_principal_of"), (
            "AgentRegistry.owner_principal_of still exists — #425 collapses stamp_owner to ONE read "
            "and DELETES this second-read method (design §5; re-derive its consumers with lore_impact "
            "at build time before deleting — the count is a heuristic)"
        )

    def test_stamp_owner_does_not_reference_owner_principal_of(self) -> None:
        """⚠ RED at HEAD — a source-level guard that ``owner_stamp.py`` no longer NAMES the deleted
        method (a stale call would be a NameError only at runtime). REDDENS a build that deletes the
        method but leaves a dangling reference, or that keeps the two-read shape."""
        import inspect

        source = inspect.getsource(loremaster.owner_stamp)
        assert "owner_principal_of" not in source, (
            "loremaster.owner_stamp still references owner_principal_of — #425 removes the second "
            "read; stamp_owner must derive the owner from verify_capability's ONE verified SELECT"
        )


class TestStampOwnerIssuesOneRoundTrip:
    """§5 + the RIDER (the ONE new leg) — the closure's WHOLE POINT: exactly ONE store round-trip,
    so there is NO window between two reads for a concurrent re-stamp to change the stamped owner.
    Counted at the ``_query`` seam (verify_capability AND owner_principal_of each ride it — source-
    confirmed). RED at HEAD (TWO round-trips)."""

    async def test_stamp_owner_issues_exactly_one_query_round_trip(
        self, cap_env: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD (== 2 today). Spy the retry seam ``AgentRegistry._query``; ONE
        ``stamp_owner`` call must trigger EXACTLY ONE round-trip. There is then no read-to-read
        TOCTOU to inject a concurrent ``owner_principal`` re-stamp into (the §5 rider's new leg,
        realised as a counted invariant rather than a race). REDDENS the two-read shape AND any
        build that adds a THIRD read."""
        assert _loremaster_stamp_owner is not None, "loremaster.stamp_owner is unbuilt (62 wave 2 / R1.1)"
        _result, capability = await _register_alice_worker(cap_env)
        original_query = cap_env.registry._query
        calls = 0

        async def _counting(*args: Any, **kwargs: Any) -> Any:
            nonlocal calls
            calls += 1
            return await original_query(*args, **kwargs)

        monkeypatch.setattr(cap_env.registry, "_query", _counting)
        await _loremaster_stamp_owner(_token(_EMAIL_ALICE), capability, registry=cap_env.registry)
        assert calls == 1, (
            f"stamp_owner issued {calls} store round-trips — #425 collapses it to EXACTLY ONE "
            f"(verify_capability's single verified SELECT already projects the owner). Two reads leave "
            f"a TOCTOU window; the closure removes it (design §5)."
        )

    async def test_stamp_owner_still_returns_the_correct_owner_pair(self, cap_env: Any) -> None:
        """⚠ POSITIVE CONTROL (GREEN at HEAD + on the correct build). The one-read closure must NOT
        sacrifice correctness: ``stamp_owner`` still returns ``(owner_principal, owner_agent)`` where
        owner_agent is the verified agent id and owner_principal names alice. REDDENS a build that
        collapses to one read but drops/None-s the owner_principal (the exact way a careless closure
        breaks) — proving the round-trip pin cannot be satisfied by simply not reading the owner."""
        assert _loremaster_stamp_owner is not None, "loremaster.stamp_owner is unbuilt"
        result, capability = await _register_alice_worker(cap_env)
        owner_principal, owner_agent = await _loremaster_stamp_owner(
            _token(_EMAIL_ALICE), capability, registry=cap_env.registry
        )
        assert owner_agent == result.agent.id, (
            f"owner_agent must be the verified agent id, got {owner_agent!r}"
        )
        assert cap_env.alice_bare in str(owner_principal), (
            f"owner_principal must still name alice ({cap_env.alice_bare}) after the one-read closure, "
            f"got {owner_principal!r}"
        )
