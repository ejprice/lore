"""Contract — packet 62 Wave 2: the SHARED SEAMS (``parse_credential`` + ``stamp_owner``).

Author: ``contract-62w2`` (Opus 4.8 CONTRACT author — tests ONLY, no production code).
Sibling of ``test_agent_capability.py`` (the mechanism) and ``test_agent_capability_reach.py``
(the reach pin + register owner-derivation + prose sweep).

SPEC: ``docs/design/2026-08-24-packet62-agent-identity-rulings.md`` — the WAVE-2 ADDENDUM
W2.4/W2.6 (the ``resolve_agent`` seam + the DRY ledger), FORK 1 riders R1.1 (the ONE
``stamp_owner`` seam) / R2.1 (fail-closed on absent credential), and the FINAL SCOPE LINE item 3.

TWO shared things this file pins, each a POLICY that MUST agree everywhere (ONE IMPLEMENTATION,
CLAUDE.md §"ONE IMPLEMENTATION" + brief-base §6):

1. ``lorerunes.parse_credential(presented) -> tuple[str, str] | None`` — the wire-format PARSE
   (the ``is_blank`` reject → ``partition(":")`` on the FIRST colon → blank-half reject sequence
   currently INLINE in ``principal_keys.py:519-525``). EXTRACTED to ``lorerunes`` and shared by
   BOTH ``PrincipalKeyStore.verify`` AND ``AgentRegistry.verify_capability``, so a credential
   minted one way parses the other and the two cannot drift. Proven by MUTATION: change the parse
   and BOTH verifies change behaviour; proven by IDENTITY: both consumers reference the ONE
   ``lorerunes`` object, never a private clone (ROUTING-IS-NOT-SHARING).

2. ``stamp_owner(...)`` — the ONE server-derived owner-stamp seam (R1.1). The owner on a governed
   write is ``(owner_principal from the credential, owner_agent from the VERIFIED capability)``,
   NEVER from a tool argument; FAIL-CLOSED when the credential is absent/invalid (R2.1). It lives
   in ``loremaster`` (ESC-1 RULED — see below).

✅ ESC-1 RULED (operator, 2026-08-24; ruling doc v5 — the changelog note + R1.1 + W2.6). The
prior contract author (``contract-62w2``) surfaced that the spec was INTERNALLY INCONSISTENT about
``stamp_owner``'s home: scope-line item 3 / R1.1 said ``lorerunes``, but W2.4 has it CALL
``resolve_agent``, which reads the store — and ``lorerunes`` imports NO sibling, ever. The operator
RULED: ``stamp_owner`` lives in ``loremaster``, NOT ``lorerunes`` (overriding the author's (A)
lean). Two reasons (W2.6 / R1.1): (1) the ``lorerunes`` entry-criterion is CROSS-MEMBER policy, and
BOTH consumers of ``stamp_owner`` (the register/verifier side AND 63/64's governed-store side) are
``loremaster`` → intra-member sharing = a shared ``loremaster`` module; (2) it is I/O-ORCHESTRATION
that drives a store read via ``resolve_agent`` and knows ``loremaster`` types (``AccessToken``,
``AgentRegistry``, the owner columns) — an ENTRY POINT, not a PREDICATE (CLAUDE.md #222).

The ``lorerunes`` ↔ ``loremaster`` split (W2.6): general pure predicates (``is_blank``,
``parse_credential``) → ``lorerunes``; store-reading orchestration (``stamp_owner``,
``resolve_agent``) → ``loremaster``. So LEG 1 (``parse_credential``) STAYS in ``lorerunes`` (a
general predicate); LEG 2 (``stamp_owner``) is pinned in ``loremaster``. ``stamp_owner`` leaving
``lorerunes`` STRENGTHENS the lorerunes-purity invariant — it is no longer a lorerunes symbol.

LOCATION PIN — the exact ``loremaster`` module is the BUILDER's choice, so the pin below asserts
only the PACKAGE surface ``loremaster.stamp_owner`` (mirroring how LEG 1 pins
``lorerunes.parse_credential`` at the OWNING package's top level), never a private module path. The
CALL SIGNATURE is UNCHANGED from the prior contract: the registry is injected (``registry=...``) so
the live-store behavioural pins exercise the per-test DB — isolated in ``_call_stamp_owner`` so any
further signature ruling stays a ONE-function edit.

RED-until-built symbols are referenced through GUARDS so COLLECTION succeeds and each pin REDs at
RUNTIME for its OWN reason.

Live store: ws://127.0.0.1:18000 (NEVER :18500). NO skip marker.
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
from loremaster.principal_keys import PrincipalKeyStore
from loremaster.principals import PrincipalStore

import loremaster
import lorerunes
from loremaster import principal_keys as principal_keys_mod

# RED-until-built (wave 2): ``parse_credential`` is EXTRACTED to ``lorerunes`` (a general pure
# predicate); ``stamp_owner`` is created in ``loremaster`` (store-reading orchestration — ESC-1
# RULED, see the module docstring). Resolved DYNAMICALLY (getattr, not a static ``from … import``)
# so the typecheck gate is GREEN at HEAD (a static forward-ref import errors ``attr-defined`` until
# the symbol exists — the wave-1 contract avoided that the same way); the pins below RED at RUNTIME
# while the symbol is None. ``stamp_owner`` is pinned at the ``loremaster`` PACKAGE surface (the
# defining module is the builder's choice), mirroring the ``lorerunes.parse_credential`` idiom.
_lorerunes_parse_credential = getattr(lorerunes, "parse_credential", None)
_loremaster_stamp_owner = getattr(loremaster, "stamp_owner", None)

_EMAIL_ALICE = "alice@example.com"
_EMAIL_BOB = "bob@example.com"


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
async def seam_env() -> Any:
    """A unified DB with a real ``AgentRegistry`` + ``PrincipalStore`` and one owned+minted agent —
    enough to exercise the SHARED seams over live behaviour. Mirrors cap_env (trimmed)."""
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


# --------------------------------------------------------------------------- #
# LEG 1 — parse_credential: the extracted wire-format parse (W2.6 DRY).
# --------------------------------------------------------------------------- #
class TestParseCredentialBehaviour:
    """W2.6 / principal_keys.py:519-525 — ``is_blank`` reject → ``partition(":")`` on the FIRST
    colon → blank-half reject. Returns ``(name, secret)`` or ``None``."""

    def test_parse_credential_exists_in_lorerunes(self) -> None:
        """⚠ RED at HEAD — ``lorerunes.parse_credential`` is unbuilt. The existence CONTROL."""
        assert _lorerunes_parse_credential is not None, (
            "lorerunes.parse_credential is unbuilt — the shared wire-format parse must be EXTRACTED "
            "to lorerunes (W2.6) so both verifies call ONE implementation"
        )

    def test_a_well_formed_credential_splits_on_the_first_colon(self) -> None:
        """⚠ RED at HEAD. ``name:secret`` -> ``(name, secret)``; a secret CONTAINING a colon keeps
        its tail (FIRST-colon split — the packet-49 ``partition(':')`` semantics, never last-colon)."""
        assert _lorerunes_parse_credential is not None, "unbuilt"
        assert _lorerunes_parse_credential("alice_worker:s3cr3t") == ("alice_worker", "s3cr3t")
        assert _lorerunes_parse_credential("n:a:b") == ("n", "a:b"), "must split on the FIRST colon"

    @pytest.mark.parametrize(
        "presented",
        ["", "   ", "no-colon", "name-only:", ":secret-only", "  :  "],
        ids=["blank", "whitespace", "no-colon", "blank-secret", "blank-name", "blank-halves"],
    )
    def test_a_malformed_credential_is_none(self, presented: str) -> None:
        """⚠ RED at HEAD. Blank, no-colon, or a blank half (name or secret) -> ``None`` — the
        malformed reject shared by both verifies. REDDENS a build that accepts a blank half."""
        assert _lorerunes_parse_credential is not None, "unbuilt"
        assert _lorerunes_parse_credential(presented) is None, presented


class TestParseCredentialIsTheONEImplementation:
    """ONE IMPLEMENTATION proven by IDENTITY: both credential stores reference the SAME
    ``lorerunes`` object as a module attribute, never a private clone (a hand-rolled parse in
    either store would fail these identity pins even if it behaved identically today —
    ROUTING-IS-NOT-SHARING). The module-attribute idiom (``from lorerunes import parse_credential``)
    is what makes the mutation pins below reach the consumers."""

    def test_principal_keys_references_the_lorerunes_parse(self) -> None:
        """⚠ RED at HEAD — ``PrincipalKeyStore``'s verify still INLINES the parse; wave 2 must
        replace the inline sequence with the shared ``lorerunes.parse_credential`` (imported as a
        module attribute). REDDENS a build that keeps a private inline/clone parse."""
        assert _lorerunes_parse_credential is not None, "unbuilt"
        referenced = getattr(principal_keys_mod, "parse_credential", None)
        assert referenced is _lorerunes_parse_credential, (
            "loremaster.principal_keys must reference the SHARED lorerunes.parse_credential (as a "
            "module attribute), not a private inline/clone parse (ONE IMPLEMENTATION, W2.6)"
        )

    def test_agents_references_the_lorerunes_parse(self) -> None:
        """⚠ RED at HEAD — ``agents`` does not import ``parse_credential`` yet; wave 2's
        ``verify_capability`` must parse through the SHARED object. REDDENS a private clone in
        ``agents``."""
        import loremaster.agents as agents_mod

        assert _lorerunes_parse_credential is not None, "unbuilt"
        referenced = getattr(agents_mod, "parse_credential", None)
        assert referenced is _lorerunes_parse_credential, (
            "loremaster.agents must reference the SHARED lorerunes.parse_credential (as a module "
            "attribute), not a private clone (ONE IMPLEMENTATION, W2.6)"
        )

    async def test_breaking_the_shared_parse_denies_PrincipalKeyStore_verify(
        self, seam_env: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ MUTATION (the PrincipalKeyStore side). Patch the parse the store references to reject
        everything; ``verify`` of a would-be-valid credential now DENIES — proving verify ROUTES
        through the shared parse. RED at HEAD (``principal_keys.parse_credential`` does not exist to
        patch → AttributeError). On a correct build, GREEN (verify denies once the parse is broken)."""
        assert _lorerunes_parse_credential is not None, "unbuilt"
        key_store = PrincipalKeyStore(
            url=seam_env.env.url,
            namespace=seam_env.env.namespace,
            database=seam_env.env.database,
            user=seam_env.env.user,
            password=seam_env.env.password,
        )
        try:
            monkeypatch.setattr(principal_keys_mod, "parse_credential", lambda _presented: None)
            # A broken parse rejects the credential as malformed BEFORE any hash/DB step -> None.
            assert await key_store.verify("some_key:some_secret") is None, (
                "PrincipalKeyStore.verify did not route through the shared parse — breaking the "
                "parse must deny (it still inlines its own parse; ONE IMPLEMENTATION violated)"
            )
        finally:
            await key_store.close()

    async def test_breaking_the_shared_parse_denies_verify_capability(
        self, seam_env: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ MUTATION (the AgentRegistry side). Patch the parse ``agents`` references to reject
        everything; ``verify_capability`` of a valid capability now DENIES — proving it ROUTES
        through the SAME shared parse. Together with the identity pins, this is the full
        change-the-parse-→-BOTH-verifies-red proof (W2.6). RED at HEAD."""
        import loremaster.agents as agents_mod

        verify = getattr(seam_env.registry, "verify_capability", None)
        assert verify is not None, "AgentRegistry.verify_capability is unbuilt (W2.2)"
        result = await seam_env.registry.register(
            "alice_worker", session="s1", role="worker", owner_principal_id=seam_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        # positive control: the real capability resolves BEFORE the parse is broken.
        assert await verify(capability, _token(_EMAIL_ALICE)) == result.agent.id
        monkeypatch.setattr(agents_mod, "parse_credential", lambda _presented: None)
        assert await verify(capability, _token(_EMAIL_ALICE)) is None, (
            "verify_capability did not route through the shared parse — breaking the parse must "
            "deny (a private clone; ONE IMPLEMENTATION violated, W2.6)"
        )


# --------------------------------------------------------------------------- #
# LEG 2 — stamp_owner: the ONE server-derived owner-stamp seam (R1.1, R2.1).
# ⚠ Home RULED ``loremaster`` (ESC-1); call signature UNCHANGED — see the module docstring.
# --------------------------------------------------------------------------- #
def _call_stamp_owner(env: Any, token: AccessToken, capability: str) -> Any:
    """Invoke ``stamp_owner`` (ESC-1 RULED: it lives in ``loremaster``): ``(access_token,
    agent_capability, *, registry)`` — the registry is INJECTED so the live-store pins exercise the
    per-test DB. Isolated here so any further signature ruling stays a ONE-function edit."""
    assert _loremaster_stamp_owner is not None, "loremaster.stamp_owner is unbuilt (R1.1 / scope item 3)"
    return _loremaster_stamp_owner(token, capability, registry=env.registry)


async def _assert_stamp_owner_fail_closed(env: Any, token: AccessToken, capability: str) -> None:
    """Fail-closed (R2.1) = ``stamp_owner`` RAISES, or returns a clearly-deny value — NEVER a
    valid ``(owner_principal, owner_agent)`` pair (both parts truthy) for an unverifiable
    credential. The existence assert is OUTSIDE the try so it REDs at HEAD for the right reason
    (a bare ``pytest.raises(Exception)`` would swallow the unbuilt-guard AssertionError — a
    false green, exactly the FIXTURES-MUST-DISCRIMINATE trap)."""
    assert _loremaster_stamp_owner is not None, "loremaster.stamp_owner is unbuilt (R1.1)"
    try:
        result = await _call_stamp_owner(env, token, capability)
    except Exception:  # noqa: BLE001 - fail-closed is loud; the exception TYPE is a builder choice.
        return  # raised -> fail-closed, acceptable (the happy-path pin proves it is not always-raise)
    assert result is None or (isinstance(result, tuple) and not all(result)), (
        f"stamp_owner returned a VALID owner pair {result!r} for an unverifiable credential — it "
        f"must fail-closed (raise, or return a clearly-deny value), never a fabricated owner (R2.1)"
    )


class TestStampOwnerSeam:
    """R1.1 / R2.1 — the owner on a governed write is (owner_principal from the credential,
    owner_agent from the VERIFIED capability), never a tool argument; FAIL-CLOSED on an absent or
    invalid credential (never a default/sentinel/NULL-as-live pair)."""

    def test_stamp_owner_exists_in_loremaster_not_lorerunes(self) -> None:
        """⚠ RED at HEAD — the shared owner-stamp seam is unbuilt. ESC-1 RULED (2026-08-24):
        ``stamp_owner`` lives in ``loremaster`` (store-reading I/O-orchestration, an ENTRY POINT),
        NOT ``lorerunes``. The LOCATION pin has two legs: PRESENT at the ``loremaster`` package
        surface AND ABSENT from ``lorerunes`` (stamp_owner is no longer a lorerunes symbol — the
        purity invariant, now STRENGTHENED). The defining ``loremaster`` module is the builder's
        choice; only the package surface ``loremaster.stamp_owner`` is pinned, mirroring LEG 1's
        ``lorerunes.parse_credential``."""
        assert _loremaster_stamp_owner is not None, (
            "loremaster.stamp_owner is unbuilt — the ONE server-derived owner-stamp seam (R1.1, "
            "scope item 3, ESC-1 RULED loremaster). Expose it at the loremaster package surface "
            "(loremaster.stamp_owner); the defining module is your choice."
        )
        assert getattr(lorerunes, "stamp_owner", None) is None, (
            "stamp_owner must NOT live in lorerunes (ESC-1 RULED loremaster: it is store-reading "
            "I/O-orchestration — an ENTRY POINT, not a lorerunes PREDICATE; CLAUDE.md #222). "
            "lorerunes stays pure: only parse_credential (a general predicate) belongs there."
        )

    async def test_stamp_owner_returns_the_verified_owner_pair(self, seam_env: Any) -> None:
        """⚠ RED at HEAD. THE POSITIVE CONTROL: for a valid capability under its owner's token,
        stamp_owner returns ``(owner_principal, owner_agent)`` where owner_agent is the VERIFIED
        agent id and owner_principal names the owning principal — the pair a governed write stamps.
        REDDENS a build whose owner_agent does not follow the verified capability."""
        result = await seam_env.registry.register(
            "alice_worker", session="s1", role="worker", owner_principal_id=seam_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        owner_principal, owner_agent = await _call_stamp_owner(seam_env, _token(_EMAIL_ALICE), capability)
        assert owner_agent == result.agent.id, (
            f"owner_agent must be the VERIFIED agent id {result.agent.id!r}, got {owner_agent!r}"
        )
        assert seam_env.alice_bare in str(owner_principal), (
            f"owner_principal must name the owning principal ({seam_env.alice_bare}), got "
            f"{owner_principal!r} — it is derived from the credential, never a tool argument"
        )

    async def test_stamp_owner_fail_closes_on_a_binding_mismatch(self, seam_env: Any) -> None:
        """⚠ RED at HEAD (R2.1 fail-closed). A valid capability presented under a DIFFERENT
        principal's token has no verified agent (the binding denies) — stamp_owner must FAIL-CLOSED
        (raise), never return a (owner_principal, owner_agent) pair a governed write would stamp.
        REDDENS a build that returns a live/partial pair when the capability does not verify."""
        result = await seam_env.registry.register(
            "alice_worker", session="s1", role="worker", owner_principal_id=seam_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"
        await _assert_stamp_owner_fail_closed(seam_env, _token(_EMAIL_BOB), capability)

    async def test_stamp_owner_fail_closes_on_an_absent_or_garbage_credential(
        self, seam_env: Any
    ) -> None:
        """⚠ RED at HEAD (R2.1 fail-closed). No/garbage capability -> no verified agent ->
        stamp_owner must FAIL-CLOSED, never stamp a default/sentinel/NULL-as-live owner (the
        confused-deputy hole §3.2.2 forbids). REDDENS a build that returns a pair for garbage."""
        await _assert_stamp_owner_fail_closed(seam_env, _token(_EMAIL_ALICE), "not-a-real-capability")
        await _assert_stamp_owner_fail_closed(seam_env, _token(_EMAIL_ALICE), "")

    async def test_stamp_owner_routes_through_the_shared_verify_capability_owner(
        self, seam_env: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RE-KEYED for #425 (design §10.3; adversary-63a-2 §CORPSE B; folded 2026-08-29 by
        contract-63a-5). The PRE-#425 form patched ``verify_capability`` and expected stamp_owner to
        break — but §10.3 COLLAPSES the double read: ``stamp_owner`` consumes the SHARED
        ``_verify_capability_owner(presented, token) -> (agent_id, owner_principal_id)`` pair-path
        DIRECTLY (ONE round-trip), and ``verify_capability`` returns its ``[0]``. So on the correct
        #425 build stamp_owner NO LONGER calls ``verify_capability`` — the old pin FALSE-RED on a
        correct build, and a builder could 'fix' it WRONG by re-routing stamp_owner back through
        ``verify_capability`` (reintroducing the second ``owner_principal_of`` read — the #425 TOCTOU
        this packet closes). Two legs pin the correct routing and RED that wrong re-route.

        ⚠ RED-until-#425-built (both legs) for the RIGHT reason: at HEAD ``_verify_capability_owner``
        is unbuilt and stamp_owner still routes through ``verify_capability`` (the pre-#425 world),
        so leg A cannot surface the boom (the shared path is not called) and leg B DOES surface it
        (stamp_owner calls verify_capability). GREEN on the correct #425 build; leg B is the
        discriminator that REDDENS the wrong re-route."""
        result = await seam_env.registry.register(
            "alice_worker", session="s1", role="worker", owner_principal_id=seam_env.alice_bare
        )
        capability = getattr(result, "capability", None)
        assert capability, "capability mint unbuilt"

        async def _boom(*_a: Any, **_k: Any) -> Any:
            raise RuntimeError("stamp-owner-routes-through-shared-pair-path")

        # LEG A (positive) — stamp_owner reads the owner pair through the SHARED
        # ``_verify_capability_owner`` (§10.3). Patch it to a loud sentinel; stamp_owner must SURFACE
        # it. ``raising=False`` because at HEAD the shared path is unbuilt (RED-until-built).
        with monkeypatch.context() as patched:
            patched.setattr(seam_env.registry, "_verify_capability_owner", _boom, raising=False)
            with pytest.raises(RuntimeError, match="stamp-owner-routes-through-shared-pair-path"):
                await _call_stamp_owner(seam_env, _token(_EMAIL_ALICE), capability)

        # LEG B (discriminator) — stamp_owner does NOT route through ``verify_capability`` (§425: ONE
        # read via the shared path, never verify_capability + a second ``owner_principal_of`` read).
        # Patch verify_capability to the boom; stamp_owner must COMPLETE with a valid owner pair, NOT
        # surface it. A build that re-routes stamp_owner through verify_capability surfaces the boom
        # (or returns no valid pair) → RED, catching the exact wrong 'fix' the corpse warns of.
        with monkeypatch.context() as patched:
            patched.setattr(seam_env.registry, "verify_capability", _boom)
            owner_principal, owner_agent = await _call_stamp_owner(
                seam_env, _token(_EMAIL_ALICE), capability
            )
        assert owner_agent == result.agent.id and seam_env.alice_bare in str(owner_principal), (
            "stamp_owner routed through verify_capability (its boom surfaced, or it returned no valid "
            "pair) — §425 requires stamp_owner to read ONCE via the SHARED _verify_capability_owner, "
            f"NOT verify_capability + a second read: got ({owner_principal!r}, {owner_agent!r})"
        )
