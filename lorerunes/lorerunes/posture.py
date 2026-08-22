"""Deployment-posture derivation + the loopback predicate (packet 39 RE-CUT, design §6).

lore runs in exactly one of three deployment POSTURES, and which one is a pure function of a
handful of primitives (the bind host + the ``auth`` block's shape). Because the composition
root (``build_asgi_app``), the deploy verbs (``lore_deploy.py``), and ``load_config`` all need
the SAME answer, the derivation lives ONCE here in ``lorerunes`` (stdlib-only, importable by
every member) rather than being re-decided at each site — the ONE-IMPLEMENTATION law.

The three postures (design §6):

* ``LOOPBACK`` — a loopback bind with auth DISABLED. The unchanged local single-user mode; no
  auth provider is installed.
* ``LAN_BEARER`` — auth enabled, ``mode == "api_key"``. The ``LoreTokenVerifier`` api-key branch
  gates ``/mcp``; NO ``.well-known`` is served (there is no OAuth authorization server to
  advertise).
* ``HOSTED_OAUTH`` — auth enabled, ``mode == "hosted_oauth"``, the ``oauth`` block present, and a
  LOOPBACK bind (lore-caddy terminates TLS and proxies to loopback lore — "the proxy comes to
  us", design §6). Serves the RFC 9728 ``.well-known`` protected-resource metadata anonymously.

Anything else is an INCOHERENT posture and is a fail-LOUD :class:`PostureError` naming the
nearest posture and the exact missing/conflicting field — never a silently-degraded default (the
honest-failure idiom). The posture NAMES in that message are enumerated FROM :class:`Posture`, so
renaming a posture moves the message with it (no drifting hardcoded string).

⚠ STUB (contract-39-w23, wave-2/3): :class:`Posture` + :class:`PostureError` are the real
interface surface; :func:`host_is_loopback` and :func:`derive_posture` raise
``NotImplementedError`` so the contract in ``lorerunes/tests/test_posture.py`` fails
BEHAVIOURALLY, never on an ImportError. The builder implements both.
"""

from __future__ import annotations

import enum
import ipaddress

__all__ = ["Posture", "PostureError", "derive_posture", "host_is_loopback"]


class Posture(enum.Enum):
    """The three deployment postures lore runs in (design §6)."""

    LOOPBACK = "loopback"
    LAN_BEARER = "lan_bearer"
    HOSTED_OAUTH = "hosted_oauth"


class PostureError(ValueError):
    """A typed refusal — the configured shape matches no coherent :class:`Posture`.

    Raised by :func:`derive_posture` for an incoherent configuration. Its message names the
    NEAREST posture (a :class:`Posture` member, enumerated from the enum) and the exact
    missing/conflicting field, so an operator can fix the config in one step.
    """


def host_is_loopback(host: str) -> bool:
    """Report whether ``host`` is a loopback bind — the R15 FAIL-CLOSED predicate.

    ``True`` iff ``host`` is the literal ``"localhost"`` OR
    ``ipaddress.ip_address(host).is_loopback`` (the whole ``127.0.0.0/8`` block plus ``::1``).
    Every other value — a LAN/public address, ``0.0.0.0``, a hostname, a spoofed
    ``127.0.0.1.evil.com``, a malformed string — is ``False``. ⚠ An exception path (a value
    ``ipaddress`` cannot parse) MUST return ``False``, never leak the exception and never return
    ``True``: a predicate that fails OPEN here would admit a public bind as "loopback" and open
    the whole hosted gate.

    Args:
        host: The bind host string (an IP literal or a hostname).

    Returns:
        ``True`` only for a genuine loopback bind; ``False`` otherwise (fail-closed).
    """
    if host == "localhost":
        return True
    try:
        # ``ip_address`` covers the whole 127.0.0.0/8 block and ``::1`` in one predicate,
        # never a hand-rolled ``startswith("127.")`` (which admits ``127.0.0.1.evil.com``)
        # nor a spellings set (which misses ``127.0.0.2``). A value it cannot parse — a
        # hostname, a spoofed ``127.0.0.1.evil.com``, a blank string — raises ``ValueError``,
        # which we FAIL CLOSED to ``False``: a fail-OPEN ``True`` here would admit a public
        # bind as loopback and open the whole hosted gate.
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def derive_posture(
    *,
    host: str,
    auth_enabled: bool,
    mode: str | None,
    has_oauth_block: bool,
) -> Posture:
    """Derive the deployment :class:`Posture` from config primitives, or refuse (design §6).

    Pure over primitives (so ``lorerunes`` need not import ``loremaster.config``): the caller
    decomposes its ``AuthConfig`` into ``auth_enabled`` / ``mode`` / ``has_oauth_block`` and
    passes the bind ``host``. Returns a :class:`Posture` for a coherent configuration; raises
    :class:`PostureError` (naming the nearest posture + the fix) for an incoherent one — see the
    module docstring for the three coherent shapes.

    Args:
        host: The bind host (passed to :func:`host_is_loopback`).
        auth_enabled: ``AuthConfig.enabled``.
        mode: ``AuthConfig.mode`` (``"api_key"`` / ``"hosted_oauth"``), or ``None`` when auth is
            absent.
        has_oauth_block: Whether ``AuthConfig.oauth`` is present (an ``OAuthProviderConfig``).

    Returns:
        The derived :class:`Posture`.

    Raises:
        PostureError: The configuration matches no coherent posture (naming the nearest + fix).
    """
    if not auth_enabled:
        # LOOPBACK: the unchanged local single-user mode. It REQUIRES a loopback bind — an
        # auth-disabled deploy on a LAN/public interface is an open door (no gate, reachable
        # off-box), so refuse it loudly rather than silently running ungated off-loopback.
        if not host_is_loopback(host):
            raise PostureError(
                f"{Posture.LOOPBACK.name}: auth is disabled but the bind host {host!r} is not a "
                f"loopback address — an auth-disabled deploy on a non-loopback/public interface "
                f"is an open door. Fix: bind a loopback host (127.0.0.0/8 or localhost), or "
                f"enable auth."
            )
        return Posture.LOOPBACK
    if mode == "api_key":
        # LAN_BEARER: the networked api-key deploy. It may bind a LAN interface (no host
        # constraint — unlike HOSTED_OAUTH, the api-key IS the gate on any interface).
        return Posture.LAN_BEARER
    if mode == "hosted_oauth":
        if not has_oauth_block:
            raise PostureError(
                f"{Posture.HOSTED_OAUTH.name}: mode is 'hosted_oauth' but no oauth provider block "
                f"is configured. Fix: add the auth.oauth block (kind / client_id / "
                f"required_scopes)."
            )
        if not host_is_loopback(host):
            # HOSTED_OAUTH binds loopback: lore-caddy terminates TLS and proxies to loopback
            # lore ("the proxy comes to us", design §6). A public bind would expose lore
            # directly, bypassing lore-caddy.
            raise PostureError(
                f"{Posture.HOSTED_OAUTH.name}: mode is 'hosted_oauth' but the bind host {host!r} "
                f"is not a loopback address — lore-caddy terminates TLS and proxies to loopback "
                f"lore. Fix: bind a loopback host."
            )
        return Posture.HOSTED_OAUTH
    # auth is enabled but ``mode`` is neither closed-domain value — no coherent posture. (A
    # config-layer ``Literal`` refuses an unknown mode before this point; this is the
    # belt-and-suspenders for a caller passing a raw primitive.)
    raise PostureError(
        f"auth is enabled but mode {mode!r} matches no posture — expected one of the "
        f"coherent shapes: {Posture.LAN_BEARER.name} ('api_key') or "
        f"{Posture.HOSTED_OAUTH.name} ('hosted_oauth')."
    )
