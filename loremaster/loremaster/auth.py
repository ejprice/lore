"""Pluggable Bearer-key request auth for the loremaster MCP server (D9/D11/§A1.12).

loremaster's auth is a **pluggable request verifier**. The seam is
:class:`AuthVerifier`; the backend that ships now is :class:`ApiKeyVerifier` — a
rotatable SET of named API keys validated against an ``Authorization: Bearer``
header. This covers the near-term consumers (Claude Code's static Bearer header
via ``--header`` / ``.mcp.json``; the Messages-API MCP connector's
``authorization_token``). An MCP OAuth 2.1 + Dynamic Client Registration backend
is the documented FUTURE plug-in behind the SAME seam (the Claude.ai-web surface,
deferred with the cloud deploy) — it satisfies :class:`AuthVerifier` and slots
into the same :class:`BearerAuthMiddleware` without re-architecting.

Security posture (D11): TLS is terminated UPSTREAM (the host's nginx-ingress), so
loremaster serves plain HTTP behind it and the key is the whole gate. There is no
per-content ACL — every authenticated developer sees the same indexed code (D9);
auth gates access to the *service*, not individual chunks.

Design points that make the gate sound:

* **Constant-time comparison.** A presented token is matched against each
  configured key with :func:`hmac.compare_digest`, never a dict lookup or ``==``
  on the secret, so a wrong key cannot be discovered by timing the rejection.
* **Rotation with zero downtime.** :meth:`ApiKeyVerifier.add_key` /
  :meth:`ApiKeyVerifier.remove_key` add or revoke ONE named identity without
  disturbing the others — rotate a developer out without restarting the server.
* **Secrets are env-refs.** :func:`build_api_key_verifier` resolves each key's
  VALUE from the env var the config NAMES (``key_env``); a configured key whose
  env var is unset/empty fails LOUD (a key silently resolving to empty would be
  an un-closable hole).
* **Fail closed.** With the middleware installed, a request with no/!Bearer/
  unknown credential is rejected with ``401`` BEFORE the wrapped app runs, and
  the presented key value is never logged.

A server with NO ``auth`` block (or ``enabled=False``) installs NO middleware —
the no-auth localhost single-user mode, unchanged for the local deploy.
"""

from __future__ import annotations

import hmac
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from loremaster.config import AuthConfig, resolve_secret

__all__ = [
    "ApiKeyVerifier",
    "AuthVerifier",
    "BearerAuthMiddleware",
    "build_api_key_verifier",
    "hmac",
]

# ASGI typing aliases — kept local so the module needs no Starlette import for
# the middleware (it is a plain ASGI app wrapping another ASGI app).
_Scope = MutableMapping[str, Any]
_Message = MutableMapping[str, Any]
_Receive = Callable[[], Awaitable[_Message]]
_Send = Callable[[_Message], Awaitable[None]]
_ASGIApp = Callable[[_Scope, _Receive, _Send], Awaitable[None]]

# The Bearer scheme prefix (case-insensitive per RFC 7235), the header name, and
# the challenge the 401 advertises.
_BEARER_PREFIX = "bearer "
_AUTHORIZATION_HEADER = b"authorization"
_WWW_AUTHENTICATE = b'Bearer realm="loremaster"'

_HTTP_SCOPE_TYPE = "http"
_UNAUTHORIZED_STATUS = 401
_UNAUTHORIZED_BODY = b"Unauthorized"


class AuthVerifier(ABC):
    """The pluggable request-verifier seam (API-key now; OAuth/DCR later).

    A backend maps a presented bearer ``token`` to an IDENTITY string (the
    authenticated principal, e.g. a developer name — for audit) or ``None`` when
    the token is invalid. Keeping the seam this small lets an OAuth 2.1 + DCR
    backend satisfy it identically (it would resolve a validated access token to
    its subject) and ride the same :class:`BearerAuthMiddleware`.
    """

    @abstractmethod
    def verify(self, token: str) -> str | None:
        """Return the identity for a valid ``token``, or ``None`` if invalid."""


class ApiKeyVerifier(AuthVerifier):
    """A rotatable set of named API keys, matched timing-safely (D9).

    Args:
        keys: A mapping of identity name → secret key value. Each name labels a
            developer/service so a verified request can be attributed; the value
            is the bearer token that authenticates as that identity.
    """

    def __init__(self, keys: dict[str, str]) -> None:
        # name → secret. A copy so a later mutation of the caller's dict cannot
        # silently change the live key set out from under the verifier. Every key
        # is validated non-empty (an empty key value would authenticate an empty
        # token — an un-closable hole), so a verifier can never carry one.
        self._keys: dict[str, str] = {}
        for name, value in keys.items():
            self.add_key(name, value)

    def verify(self, token: str) -> str | None:
        """Return the identity whose key equals ``token`` (timing-safe), else ``None``.

        Every configured key is compared with :func:`hmac.compare_digest` — a
        constant-time check, so a near-miss key cannot be distinguished by the
        time the rejection takes. An empty token is rejected up front (no key is
        ever empty, so it could never match, but rejecting early is the explicit
        belt-and-suspenders). All keys are checked (no early-out) to keep the
        timing independent of which key, if any, matches.

        Args:
            token: The presented bearer token.

        Returns:
            The matching key's identity name, or ``None`` if no key matches.
        """
        if not token:
            return None
        # Compare on UTF-8 BYTES, not str: ``hmac.compare_digest`` raises
        # ``TypeError`` on a non-ASCII ``str`` (the header is decoded latin-1
        # upstream, so a non-ASCII presented token IS reachable). A str-mode
        # compare would let that TypeError escape the middleware → a 500 instead
        # of the 401 contract. Encoding both sides keeps the check timing-safe and
        # byte-agnostic. The configured key is encoded once per check (cheap).
        token_bytes = token.encode("utf-8")
        matched: str | None = None
        for name, value in self._keys.items():
            if hmac.compare_digest(token_bytes, value.encode("utf-8")):
                matched = name
        return matched

    def add_key(self, name: str, value: str) -> None:
        """Add (or replace) a named key — it verifies immediately (rotation).

        Args:
            name: The identity name to register the key under.
            value: The secret key value that authenticates as ``name``.

        Raises:
            ValueError: If ``value`` is empty — an empty key would authenticate an
                empty token, an un-closable hole; rejecting it keeps the gate sound.
        """
        if not value:
            raise ValueError(f"refusing to register an empty key value for identity {name!r}")
        self._keys[name] = value

    def remove_key(self, name: str) -> None:
        """Revoke ONE named identity, leaving the others intact (rotation).

        Args:
            name: The identity name to revoke. A name not present is a no-op.
        """
        self._keys.pop(name, None)


def build_api_key_verifier(config: AuthConfig) -> ApiKeyVerifier:
    """Build an :class:`ApiKeyVerifier` from the config's named ``*_env`` keys.

    Each configured key's VALUE is resolved from the environment variable it
    NAMES (``key_env``) via :func:`~loremaster.config.resolve_secret` — never
    inlined. A configured key whose env var is unset or empty fails LOUD here
    (resolving it to empty would create an un-closable hole), so a misconfigured
    key is a startup error, not a silent open door.

    Args:
        config: The validated :class:`~loremaster.config.AuthConfig`.

    Returns:
        An :class:`ApiKeyVerifier` over the resolved name → value set.

    Raises:
        KeyError: If any configured key's env var is unset or empty.
    """
    resolved: dict[str, str] = {}
    for key in config.keys:
        resolved[key.name] = resolve_secret(key.key_env)
    return ApiKeyVerifier(resolved)


class BearerAuthMiddleware:
    """ASGI middleware that gates every HTTP request on a valid Bearer key.

    Wraps the MCP streamable-http app: a request bearing a valid
    ``Authorization: Bearer <key>`` passes through to the wrapped app; anything
    else (no header, a non-Bearer scheme, or an unknown key) is rejected with
    ``401`` + ``WWW-Authenticate: Bearer`` BEFORE the wrapped app runs (fail
    closed). Non-HTTP scopes (the ASGI ``lifespan`` startup/shutdown) pass
    straight through — only HTTP requests are gated. The presented key value is
    never logged.

    Args:
        app: The wrapped ASGI application (the MCP streamable-http app).
        verifier: The :class:`AuthVerifier` consulted for every HTTP request.
    """

    def __init__(self, app: _ASGIApp, verifier: AuthVerifier) -> None:
        self._app = app
        self._verifier = verifier

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        """Gate an HTTP request; pass non-HTTP scopes through untouched."""
        if scope.get("type") != _HTTP_SCOPE_TYPE:
            await self._app(scope, receive, send)
            return
        token = self._bearer_token(scope)
        if token is None or self._verifier.verify(token) is None:
            await self._reject(send)
            return
        await self._app(scope, receive, send)

    @staticmethod
    def _bearer_token(scope: _Scope) -> str | None:
        """Extract the Bearer token from the ``Authorization`` header, or ``None``.

        Returns ``None`` for a missing header or a non-Bearer scheme (the
        case-insensitive ``Bearer `` prefix per RFC 7235). The token is the header
        value after the scheme prefix.
        """
        headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
        for name, value in headers:
            if name.lower() == _AUTHORIZATION_HEADER:
                decoded: str = value.decode("latin-1")
                if decoded.lower().startswith(_BEARER_PREFIX):
                    return decoded[len(_BEARER_PREFIX):]
                return None
        return None

    @staticmethod
    async def _reject(send: _Send) -> None:
        """Send a ``401`` with a ``WWW-Authenticate: Bearer`` challenge."""
        await send(
            {
                "type": "http.response.start",
                "status": _UNAUTHORIZED_STATUS,
                "headers": [
                    (b"www-authenticate", _WWW_AUTHENTICATE),
                    (b"content-type", b"text/plain; charset=utf-8"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": _UNAUTHORIZED_BODY})
