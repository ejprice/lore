"""lore's capability scopes and the ``role → capability`` policy — ONE home (design §3.5).

The scope constants and the ``role → capability`` function live ONCE here so the three
consumers that must agree share one home (design §3.5, prior §6 shared policy):

* the VERIFIER (packet 39) that MINTS a principal's scopes into its ``AccessToken``,
* the read-only enforcement GUARD (packet 39 wave 2, #295) that CHECKS the minted
  ``lore:write`` scope, and
* the ``instructions`` RENDERER (wave 3) that NAMES the scopes to a consumer agent.

⚠ THE READ-ONLY-HOSTED BANNER (design 2026-08-21 superseding update). In packet 39 the
HOSTED (OAuth) surface is READ-ONLY for EVERY role — member AND admin — because coarse
role-gated write is both useless and unsafe for lore's multi-writer tools; ALL hosted
write (member row-scoped AND admin superuser) moves to the RBAC packets (60-65). The
trusted LAN api-key fleet keeps full write (it is the coordination substrate; F7
role-gating is deferred to RBAC).

``role → capability`` is a FUNCTION, never a hardcoded ``admin = +lore:write`` (the
anti-premature-RBAC defect this packet pins against): the functions below take ``role`` as
the forward-compat seam so the RBAC packets EXTEND them (a richer mapping) rather than
rewriting a hardcoded constant. In packet 39 both map every role to a fixed set — the
hosted read-only floor and the LAN full-write set — and that packet-39 behaviour is what
``test_token_verifier.py`` pins.
"""

from __future__ import annotations

# The wire scope values a consumer/guard actually sees. Named ONCE here (design §3.5) so a
# rename is a single edit and the verifier that mints them, the guard that checks them and
# the renderer that names them cannot drift into three spellings.
LORE_READ = "lore:read"
LORE_WRITE = "lore:write"


def hosted_scopes_for_role(role: str) -> frozenset[str]:
    """The scopes a HOSTED (OAuth) principal of ``role`` is minted — ``role → capability``.

    Packet 39 (READ-ONLY-hosted banner): EVERY hosted role — ``member`` AND ``admin`` —
    is minted exactly ``{lore:read}``. Hosted write is the RBAC packets' (60-65), never
    this one, so this deliberately does NOT special-case ``admin``: hardcoding
    ``admin ⇒ +lore:write`` here is the anti-premature-RBAC defect
    (``test_hosted_admin_is_ALSO_read_only_regardless_of_role``). ``role`` is taken as the
    forward-compat seam so the RBAC packets EXTEND this function rather than replacing a
    hardcoded constant.

    Args:
        role: The principal's role (``member`` / ``admin``) — carried as the RBAC seam;
            not acted on for capability in packet 39.

    Returns:
        The hosted scope set — exactly ``{lore:read}`` in packet 39, for every role.
    """
    return frozenset({LORE_READ})


def lan_scopes_for_role(role: str) -> frozenset[str]:
    """The scopes a LAN/api-key principal of ``role`` is minted — ``role → capability``.

    Packet 39 (banner: the trusted LAN fleet keeps full write; F7 api-key role-gating is
    deferred to RBAC): EVERY role is minted ``{lore:read, lore:write}``. ``role`` is taken
    as the forward-compat seam so the RBAC packets EXTEND this function (least-privilege
    api-key gating) rather than replacing a hardcoded constant.

    Args:
        role: The principal's role (``member`` / ``admin``) — carried as the RBAC seam;
            not acted on for capability in packet 39 (LAN keeps full write regardless).

    Returns:
        The LAN scope set — ``{lore:read, lore:write}`` in packet 39, for every role.
    """
    return frozenset({LORE_READ, LORE_WRITE})
