"""The ONE server-derived owner-stamp seam — ``stamp_owner`` (packet 62, R1.1 / W2.6).

The owner of a GOVERNED write is the pair ``(owner_principal, owner_agent)``, and it is
derived SERVER-SIDE from a VERIFIED capability under the transport token — NEVER from a
tool argument (§3.2.2 / W2.1: a raw ``owner=`` / ``as_agent=`` / ``created_by=`` claim
is an unverified assertion, the confused deputy). There is exactly ONE function that
performs this derivation, and 63/64's governed-store writes CALL it (ONE IMPLEMENTATION —
a cloned owner-derivation is where a security policy drifts).

⚠ HOME RULED ``loremaster``, NOT ``lorerunes`` (ESC-1, operator 2026-08-24). ``stamp_owner``
is store-reading I/O-ORCHESTRATION — it drives a live store read via
:meth:`~loremaster.agents.AgentRegistry.verify_capability` and knows ``loremaster`` types
(``AccessToken``, ``AgentRegistry``, the owner columns) — an ENTRY POINT, not a pure
PREDICATE. ``lorerunes`` holds only the general pure ``parse_credential`` predicate and
imports no sibling, ever, so a store-reading orchestrator cannot live there (CLAUDE.md
#222 — a shared package makes the wrong thing newly possible; putting a capability there
is a design decision, not a tidying).

FAIL-CLOSED (R2.1): an absent, garbage, unverified, or binding-mismatched capability has
NO verified agent, so ``stamp_owner`` RAISES — a governed write is NEVER stamped with a
default / sentinel / partial owner. The ONE credentialed path is: ``owner_agent`` from
``verify_capability`` (which also proves the ``(principal, agent)`` binding), and
``owner_principal`` from that verified agent's own owning-principal id (which the binding
has already proved equals the transport token's principal — so it IS "owner_principal from
the token", expressed as the record id the PDP stamps).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp.server.auth import AccessToken

    from loremaster.agents import AgentRegistry


class OwnerStampError(RuntimeError):
    """Raised when :func:`stamp_owner` cannot derive a verified owner pair.

    The fail-closed signal (R2.1): an absent / garbage / unverified / binding-mismatched
    capability yields no verified agent, so no owner may be stamped. A governed write that
    catches this must DENY, never fall back to a default owner.
    """


async def stamp_owner(
    access_token: AccessToken,
    agent_capability: str,
    *,
    registry: AgentRegistry,
) -> tuple[str, str]:
    """Derive the ``(owner_principal, owner_agent)`` a governed write stamps (R1.1).

    Routes through the ONE verification seam
    (:meth:`~loremaster.agents.AgentRegistry.verify_capability`) — never a hand-rolled
    lookup (ROUTING-IS-NOT-SHARING): that call BOTH resolves ``owner_agent`` AND enforces
    the ``(principal, agent)`` binding against ``access_token``. The ``owner_principal`` is
    then the verified agent's own owning-principal id, which the binding has already proved
    is ``access_token``'s principal.

    Args:
        access_token: The verified transport token whose principal owns the write.
        agent_capability: The raw ``<name>:<secret>`` capability presented for this call.
        registry: The :class:`~loremaster.agents.AgentRegistry` the verification and owner
            read route through (INJECTED so a governed tool wires its live registry, and
            the tests exercise the per-test DB).

    Returns:
        ``(owner_principal, owner_agent)`` — both bare record ids — the owner a governed
        write stamps.

    Raises:
        OwnerStampError: The capability did not verify under the transport token (absent,
            garbage, unverified, or binding-mismatch), or the verified agent has no owning
            principal — fail-closed (R2.1); no owner is fabricated.
    """
    # #425 (packet 63a §10.3): read the owner pair in ONE store round-trip through the SHARED
    # pair-yielding path — the verified SELECT already projects the owning principal id, so there
    # is NO second owner read and therefore NO read-to-read TOCTOU window a concurrent re-stamp
    # could exploit (design §5). ``verify_capability`` (which returns the pair's ``[0]``) is NOT
    # called here — routing stamp_owner back through it would reintroduce the second read this
    # closure removes (corpse B leg B catches exactly that wrong re-route).
    pair = await registry._verify_capability_owner(agent_capability, access_token)  # noqa: SLF001
    if pair is None:
        raise OwnerStampError(
            "capability did not verify under the transport token — fail-closed (R2.1); no "
            "owner is stamped for an absent / garbage / unverified / binding-mismatched "
            "capability (the confused-deputy door §3.2.2 forbids)"
        )
    owner_agent, owner_principal = pair
    if not owner_principal:
        raise OwnerStampError(
            "the verified agent has no owning principal — fail-closed (R2.1); a governed "
            "write is never stamped with a null owner"
        )
    return owner_principal, owner_agent
