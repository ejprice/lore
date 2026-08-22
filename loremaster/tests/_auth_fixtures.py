"""Shared, production-realistic fixtures for the packet-39 auth contract.

ONE home for the values and instruments every auth-contract module needs, so the six
test modules cannot drift into six slightly-different ideas of what a Google tokeninfo
response looks like or which client id is ours. Design reference:
``docs/design/2026-07-31-packet39-google-oauth.md``.

WHERE THE VALUES COME FROM (they are recorded/production shapes, not conveniences):

* ``GOOGLE_CLIENT_ID`` — the REUSED Price Paper OAuth client (design R2). A public
  identifier per RFC 6749 §2.2; it lives on this host as ``GOOGLE_CLIENT_ID`` in
  ``~/docker/mcp/.env`` and is already serving odoo-code's production connector.
* ``TOKENINFO_URL`` / ``GOOGLE_ISSUER`` — the endpoints design §4 rules HARDCODED
  (a configurable issuer is a downgrade attack).
* The tokeninfo payload SHAPE — Google's v3 ``/tokeninfo`` returns its numeric and
  boolean fields as JSON **strings** (``"3599"``, ``"true"``), and its ``scope`` as a
  space-delimited list of full scope URIs. Building fixtures with real ``int``s and
  real ``bool``s is the convenience that hides the coercion bug.
* Addresses — firehawktransam.org / pricepaper.com identities of the shape the R12
  roster will actually carry.
* ``server`` bind ``127.0.0.1:9202`` + path ``/mcp`` — the live ``lore.yaml``.
* ``RESOURCE_SERVER_URL`` — ``https://lore.firehawktransam.org/mcp`` (design R3/R4).

⚠ THE UNIT TRAP THIS MODULE EXISTS TO EXPOSE. Google returns BOTH ``expires_in``
(seconds REMAINING, relative) and ``exp`` (an ABSOLUTE unix timestamp). The MCP SDK
compares ``AccessToken.expires_at`` against ``int(time.time())``. A build that puts
``expires_in`` into ``expires_at`` yields ``3599``, i.e. 1970-01-01 — and the SDK
rejects EVERY token, a 100% denial that no verifier-level unit test sees. A build that
treats ``exp`` as relative yields a token good for fifty millennia. Both fields are
therefore emitted CONSISTENTLY by :func:`tokeninfo_payload`, and the contract asserts
the derived ``expires_at`` lands in an absolute-time sanity band.
"""

from __future__ import annotations

import contextlib
import time
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine, MutableMapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from asgi_lifespan import LifespanManager

# --------------------------------------------------------------------------- #
# Identity / endpoint constants
# --------------------------------------------------------------------------- #

# Design R2 — the reused Price Paper client. Public by RFC 6749 §2.2.
GOOGLE_CLIENT_ID = "185677973635-e6jah4ogtbdv7k051550v4aj2r1ei288.apps.googleusercontent.com"

# A DIFFERENT, well-formed Google OAuth client. The negative control for the ``aud``
# check: a token Google issued and will happily verify, minted for somebody else's
# app. Without the ``aud`` check, any Google app's token would open lore.
OTHER_OAUTH_CLIENT_ID = "944217630518-p2q7m4knd8v1sc0jr6xhg3taeu9wblz5.apps.googleusercontent.com"

GOOGLE_ISSUER = "https://accounts.google.com"
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"

# The scope URIs Google actually returns for an ``email``-granting consent. Note they
# are FULL URIs, not the bare alias ``email`` a client may have REQUESTED — a build
# that literally checks ``"email" in scope.split()`` denies every real token.
GOOGLE_EMAIL_SCOPE_URI = "https://www.googleapis.com/auth/userinfo.email"
GOOGLE_PROFILE_SCOPE_URI = "https://www.googleapis.com/auth/userinfo.profile"
GRANTED_SCOPE_STRING = f"openid {GOOGLE_EMAIL_SCOPE_URI} {GOOGLE_PROFILE_SCOPE_URI}"
# The same grant as some Google surfaces echo it — the bare alias. A correct build
# must accept BOTH forms; this is the superset property, not a preference.
GRANTED_SCOPE_STRING_ALIAS_FORM = "openid email profile"
# A real grant that does NOT include the email scope.
SCOPE_STRING_WITHOUT_EMAIL = f"openid {GOOGLE_PROFILE_SCOPE_URI}"

# A Google access token's real lifetime, in seconds, as tokeninfo reports it.
GOOGLE_ACCESS_TOKEN_LIFETIME_S = 3599

# --------------------------------------------------------------------------- #
# Principals. At least TWO distinct emails and TWO distinct api-key names appear in
# every principal-shaped pin (the value-monoculture law: 37 calls at one value let a
# build branch on that value and pass an entire contract).
# --------------------------------------------------------------------------- #
OPERATOR_EMAIL = "ejprice@firehawktransam.org"
SECOND_PRINCIPAL_EMAIL = "dana.whitfield@pricepaper.com"
UNLISTED_EMAIL = "someone.else@gmail.com"

# Google's opaque ``sub`` — a 21-digit numeric string, stable per (issuer, user).
OPERATOR_SUBJECT = "104938271650283746192"
SECOND_PRINCIPAL_SUBJECT = "117264839025617384029"

API_KEY_NAME_LOCAL_AGENT = "local-agent"
API_KEY_NAME_LAN_CLIENT = "lan-client"
API_KEY_ENV_LOCAL_AGENT = "LORE_KEY_LOCAL_AGENT"
API_KEY_ENV_LAN_CLIENT = "LORE_KEY_LAN_CLIENT"
API_KEY_VALUE_LOCAL_AGENT = "lk_9f2c41d8b7e34a5f8c1d6e0a2b7f4938"
API_KEY_VALUE_LAN_CLIENT = "lk_3a7e60c9d1f84b2e95a08c6d4b1e7f52"

# --------------------------------------------------------------------------- #
# Server / edge constants (design R3/R4 + the live lore.yaml)
# --------------------------------------------------------------------------- #
LOOPBACK_HOST = "127.0.0.1"
SERVER_PORT = 9202
MCP_PATH = "/mcp"
PUBLIC_HOSTNAME = "lore.firehawktransam.org"
RESOURCE_SERVER_URL = f"https://{PUBLIC_HOSTNAME}{MCP_PATH}"
WELL_KNOWN_PATH = f"/.well-known/oauth-protected-resource{MCP_PATH}"
CLAUDE_AI_ORIGIN = "https://claude.ai"
CLAUDE_COM_ORIGIN = "https://claude.com"
HOSTILE_ORIGIN = "https://lore-firehawktransam.attacker.example"

# The embedding dimensionality the rest of the loremaster suite pins — the real
# production curve dimensionality for the voyage-4-nano deploy, not a round number.
EMBEDDING_DIM = 2048


def google_access_token(label: str) -> str:
    """Mint a realistically-shaped, unique Google access token.

    Real tokens are opaque ``ya29.``-prefixed strings of ~200 characters. Length and
    prefix matter: a fixture token of ``"tok"`` would let a build that (say) slices a
    fixed prefix, or that trips a length guard, pass every pin.

    Args:
        label: A stable label so a failure message says WHICH principal's token.

    Returns:
        An opaque token string unique to this call.
    """
    filler = uuid.uuid4().hex + uuid.uuid4().hex + uuid.uuid4().hex + uuid.uuid4().hex
    return f"ya29.a0Af{label}-{filler}"


def tokeninfo_payload(
    *,
    aud: str | None,
    email: str | None,
    email_verified: object,
    scope: str | None,
    sub: str | None = None,
    lifetime_s: int = GOOGLE_ACCESS_TOKEN_LIFETIME_S,
    now: float | None = None,
) -> dict[str, object]:
    """Build a Google ``/tokeninfo`` 200 body in the shape Google actually returns.

    NOTHING THE VERIFIER BRANCHES ON IS DEFAULTED. ``aud``, ``email``,
    ``email_verified`` and ``scope`` are REQUIRED keyword arguments, so every call
    site must state them — a factory that defaults a branched-on parameter
    manufactures the blind spot where every fixture silently tests the one value for
    which the code happens to be right.

    Args:
        aud: The audience claim, or ``None`` to omit the key entirely (a MISSING
            ``aud`` must be a hard reject, never a skipped check).
        email: The verified address, or ``None`` to omit the key.
        email_verified: Emitted verbatim — pass ``True``, ``"true"``, ``False``,
            ``"false"`` or the sentinel :data:`OMIT` to leave the key out.
        scope: The space-delimited granted-scope string, or ``None`` to omit.
        sub: Google's opaque subject, or ``None`` to omit (design §4 rules a fallback
            to the normalised email in that case).
        lifetime_s: Seconds of life remaining. Both ``expires_in`` (relative) and
            ``exp`` (absolute) are emitted CONSISTENTLY from this one number.
        now: Wall-clock override for deterministic expiry assertions.

    Returns:
        A JSON-serialisable dict with Google's real string-typed numeric fields.
    """
    issued_at = time.time() if now is None else now
    payload: dict[str, object] = {
        "azp": GOOGLE_CLIENT_ID,
        "access_type": "offline",
        # Google returns these as STRINGS. A fixture using ints hides a coercion bug.
        "expires_in": str(lifetime_s),
        "exp": str(int(issued_at) + lifetime_s),
    }
    if aud is not None:
        payload["aud"] = aud
    if email is not None:
        payload["email"] = email
    if email_verified is not OMIT:
        payload["email_verified"] = email_verified
    if scope is not None:
        payload["scope"] = scope
    if sub is not None:
        payload["sub"] = sub
    return payload


class _Omitted:
    """Sentinel type for "this key is absent from the response entirely"."""

    def __repr__(self) -> str:
        return "<OMIT>"


OMIT = _Omitted()


def admitted_payload(
    *,
    email: str = OPERATOR_EMAIL,
    sub: str | None = OPERATOR_SUBJECT,
    lifetime_s: int = GOOGLE_ACCESS_TOKEN_LIFETIME_S,
    now: float | None = None,
) -> dict[str, object]:
    """The tokeninfo body of a token that SHOULD be admitted (the positive control).

    Every negative pin in this contract needs a companion showing the probe can also
    say yes; this is that companion. ``email``/``sub`` are defaulted here deliberately
    — they are IDENTITY, not a branch condition — while ``aud``, ``email_verified``
    and ``scope`` are fixed at their admitting values because that is what "should be
    admitted" MEANS.
    """
    return tokeninfo_payload(
        aud=GOOGLE_CLIENT_ID,
        email=email,
        email_verified=True,
        scope=GRANTED_SCOPE_STRING,
        sub=sub,
        lifetime_s=lifetime_s,
        now=now,
    )


# --------------------------------------------------------------------------- #
# The outbound-call spy. ``httpx.MockTransport`` ships with the existing httpx
# dependency and supports async handlers, so nothing here hand-rolls a fake client.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RecordedRequest:
    """One outbound HTTP attempt, captured for assertion.

    Attributes:
        method: The HTTP method.
        url: The FULL request URL including any query string — the pin that proves a
            token never travelled in a URL (httpx logs method+URL at INFO, and that
            leaked tokens into a systemd journal once).
        content: The raw request body bytes.
        headers: The request headers, lower-cased keys.
    """

    method: str
    url: str
    content: bytes
    headers: dict[str, str]


@dataclass
class TokeninfoSpy:
    """Records every outbound tokeninfo attempt and serves a programmed reply.

    Attributes:
        responder: Called per request to produce the reply; may raise an
            ``httpx`` transport exception to simulate a network fault.
        requests: Every attempt, in order.
    """

    responder: Callable[[httpx.Request], httpx.Response | Coroutine[Any, Any, httpx.Response]]
    requests: list[RecordedRequest] = field(default_factory=list)

    @property
    def call_count(self) -> int:
        """How many outbound attempts were made (0 proves a cache served the call)."""
        return len(self.requests)

    async def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(
            RecordedRequest(
                method=request.method,
                url=str(request.url),
                content=request.content,
                headers={key.lower(): value for key, value in request.headers.items()},
            )
        )
        outcome = self.responder(request)
        if isinstance(outcome, httpx.Response):
            return outcome
        return await outcome

    def client(self) -> httpx.AsyncClient:
        """An ``httpx.AsyncClient`` whose transport is this spy."""
        return httpx.AsyncClient(transport=httpx.MockTransport(self._handle))


def always_json(payload: dict[str, object], status_code: int = 200) -> TokeninfoSpy:
    """A spy that returns the same JSON body for every attempt."""
    return TokeninfoSpy(responder=lambda _request: httpx.Response(status_code, json=payload))


def always_status(status_code: int, body: str = "") -> TokeninfoSpy:
    """A spy that returns a bare status for every attempt (the 401 / 5xx legs)."""
    return TokeninfoSpy(responder=lambda _request: httpx.Response(status_code, text=body))


def always_raises(exception: Exception) -> TokeninfoSpy:
    """A spy whose transport raises — a timeout or connection failure."""

    def _raise(_request: httpx.Request) -> httpx.Response:
        raise exception

    return TokeninfoSpy(responder=_raise)


def scripted(
    outcomes: Sequence[httpx.Response | Exception],
) -> TokeninfoSpy:
    """A spy that serves ``outcomes`` in order, then repeats the last one.

    Used for the transient-outage pins: a 503 followed by a 200 proves the verifier
    RETRIED rather than negative-caching a good token out of existence.
    """
    remaining = list(outcomes)

    def _next(_request: httpx.Request) -> httpx.Response:
        outcome = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return TokeninfoSpy(responder=_next)


# --------------------------------------------------------------------------- #
# Roster files (design R12 — a flat file OUTSIDE the repo and the image, bind-mounted
# read-only; host-side sibling of the verified ``~/docker/mcp/lore-secrets/`` idiom).
# --------------------------------------------------------------------------- #

ROSTER_FILENAME = "lore-allowed-emails.txt"


def write_roster(directory: Path, *emails: str, header: bool = True) -> Path:
    """Write a roster file the way an operator's editor would leave it.

    Args:
        directory: The mount-point stand-in (a ``tmp_path``).
        emails: The addresses to list, one per line.
        header: Whether to include the comment header a real roster carries — kept
            switchable so a comments-only / bare file can also be produced.

    Returns:
        The roster path.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ROSTER_FILENAME
    lines: list[str] = []
    if header:
        lines.append("# lore hosted-read allowlist — one Google identity per line.")
        lines.append("# Revoke by deleting a line; effective on the next verification.")
        lines.append("")
    lines.extend(emails)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Config payloads. Mirrors the production ``lore.yaml`` shape (and the ``_config``
# helper the rest of the loremaster suite uses) so a fixture config is the same object
# ``load_config`` produces, never a hand-built stand-in.
#
# ⚠ DUPLICATION FLAG: this is the fourth copy of the base payload in the suite
# (test_mcp_server, test_eager_startup, test_lifespan_framework each carry one). It is
# written here so the SIX auth-contract modules share ONE builder rather than adding
# six more; consolidating all of them is a separate, flagged design decision.
# --------------------------------------------------------------------------- #


def base_config_payload(slug: str, live_path: Path) -> dict[str, Any]:
    """The auth-free ``lore.yaml`` payload every posture fixture starts from."""
    return {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": EMBEDDING_DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "roots": [
            {"tier": "custom", "watch": "live", "path": str(live_path), "include": ["**/*.py"]}
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": False,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": LOOPBACK_HOST, "path": MCP_PATH, "port": SERVER_PORT},
    }


def hosted_auth_block(roster_path: Path, *, keys: bool = True) -> dict[str, Any]:
    """The ``auth`` block for the ``HOSTED_OAUTH`` posture (design §5)."""
    block: dict[str, Any] = {
        "enabled": True,
        "mode": "google_oauth",
        "google": {
            "client_id": GOOGLE_CLIENT_ID,
            "resource_server_url": RESOURCE_SERVER_URL,
            "allowed_emails_file": str(roster_path),
        },
    }
    if keys:
        block["keys"] = [
            {"name": API_KEY_NAME_LOCAL_AGENT, "key_env": API_KEY_ENV_LOCAL_AGENT},
            {"name": API_KEY_NAME_LAN_CLIENT, "key_env": API_KEY_ENV_LAN_CLIENT},
        ]
    return block


def lan_bearer_auth_block() -> dict[str, Any]:
    """The ``auth`` block for the ``LAN_BEARER`` posture (today's networked deploy)."""
    return {
        "enabled": True,
        "mode": "api_key",
        "keys": [
            {"name": API_KEY_NAME_LOCAL_AGENT, "key_env": API_KEY_ENV_LOCAL_AGENT},
            {"name": API_KEY_NAME_LAN_CLIENT, "key_env": API_KEY_ENV_LAN_CLIENT},
        ],
    }


def slug() -> str:
    """A unique throwaway project slug per test (namespaces the per-test store)."""
    return f"test_{uuid.uuid4().hex}"


# --------------------------------------------------------------------------- #
# ASGI driving. The composition pins must exercise the ASSEMBLED app, because the
# SDK's whole auth branch is ``# pragma: no cover`` upstream — a verifier-level unit
# test proves nothing about ``streamable_http_manager``.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class AsgiResponse:
    """A captured ASGI response.

    Attributes:
        status: The HTTP status code.
        headers: Response headers with lower-cased byte keys decoded to ``str``.
        body: The concatenated response body.
    """

    status: int
    headers: dict[str, str]
    body: bytes

    def header(self, name: str) -> str:
        """Return one header's value (empty string when absent)."""
        return self.headers.get(name.lower(), "")


def _scope(
    *,
    method: str,
    path: str,
    headers: list[tuple[bytes, bytes]],
    query_string: bytes = b"",
) -> dict[str, Any]:
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": query_string,
        "root_path": "",
        "headers": headers,
        "client": (LOOPBACK_HOST, 54321),
        "server": (LOOPBACK_HOST, SERVER_PORT),
        "state": {},
    }


async def drive(
    app: Any,
    *,
    method: str = "POST",
    path: str = MCP_PATH,
    headers: list[tuple[bytes, bytes]] | None = None,
    body: bytes = b"",
) -> AsgiResponse:
    """Drive an ASGI app once over a synthetic HTTP scope and capture the response."""
    sent: list[MutableMapping[str, Any]] = []
    delivered = False

    async def receive() -> MutableMapping[str, Any]:
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: MutableMapping[str, Any]) -> None:
        sent.append(message)

    await app(_scope(method=method, path=path, headers=headers or []), receive, send)
    start = next(message for message in sent if message["type"] == "http.response.start")
    payload = b"".join(
        bytes(message.get("body", b""))
        for message in sent
        if message["type"] == "http.response.body"
    )
    return AsgiResponse(
        status=int(start["status"]),
        headers={
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in start.get("headers", [])
        },
        body=payload,
    )


# The bound on lifespan startup/shutdown in a contract pin. The hand-rolled predecessor
# had NO timeout at all: an app whose startup never completed hung the suite instead of
# failing it.
LIFESPAN_TIMEOUT_S = 5.0


def running_asgi_app(app: Any) -> LifespanManager:
    """Run an ASGI app's lifespan for the duration of an ``async with`` block.

    ⚠ THIS IS `asgi_lifespan.LifespanManager`, NOT A HAND-ROLL (lead ruling, 2026-07-31).
    An earlier revision of this module carried ~30 lines that drove the ASGI lifespan
    protocol by hand, with a `keep_with_trigger` verdict whose trigger was *"the first pin
    needing lifespan state the stand-in does not model"*. `asgi-lifespan` 2.1.0 was then
    installed (`93bd193`) and the trigger fired without anyone re-running the decision —
    the delta adversary caught it. The twin is deleted rather than kept beside the package:
    NEVER MAINTAIN BOTH.

    This wrapper is a POLICY function, not a second implementation — it exists so the
    timeout policy has one home rather than being re-typed at each of the call sites
    (ONE IMPLEMENTATION: if two call sites need the same policy, it is a function they
    call). `httpx.ASGITransport` cannot do this job: its source carries no lifespan
    handling at all (read, `httpx/_transports/asgi.py`).

    Args:
        app: The composed ASGI application.

    Returns:
        An async context manager that completes `lifespan.startup` on entry and drives
        `lifespan.shutdown` on exit, both bounded by :data:`LIFESPAN_TIMEOUT_S`.
    """
    return LifespanManager(
        app, startup_timeout=LIFESPAN_TIMEOUT_S, shutdown_timeout=LIFESPAN_TIMEOUT_S
    )


def bearer(token: str, *, scheme: str = "Bearer") -> tuple[bytes, bytes]:
    """An ``Authorization`` header tuple; ``scheme`` varies the RFC 7235 casing pin."""
    return (b"authorization", f"{scheme} {token}".encode("latin-1"))


def json_rpc_initialize(request_id: int = 1) -> bytes:
    """A wire-legal MCP ``initialize`` request body.

    Creating a real session is the only way to reach
    ``StreamableHTTPSessionManager``'s ownership check — the seam finding F3 lives in.
    """
    return (
        b'{"jsonrpc":"2.0","id":' + str(request_id).encode("ascii") + b',"method":"initialize",'
        b'"params":{"protocolVersion":"2025-06-18","capabilities":{},'
        b'"clientInfo":{"name":"lore-contract-probe","version":"1.0"}}}'
    )


MCP_POST_HEADERS: list[tuple[bytes, bytes]] = [
    (b"content-type", b"application/json"),
    (b"accept", b"application/json, text/event-stream"),
]


# --------------------------------------------------------------------------- #
# Verifier construction. Lazy imports throughout: the production symbols do not
# exist while this contract is RED, and a module-level import would break
# COLLECTION of every module that shares these fixtures rather than failing the
# individual pins.
# --------------------------------------------------------------------------- #


class _StubAppContext:
    """A no-op stand-in for ``AppContext`` in lifespan-driven AUTH pins.

    The heavy build (probe gate → SurrealDB write stack → watcher) has its own
    contract in ``test_eager_startup.py``; reproducing it here would make every auth
    pin depend on a live SurrealDB for no auth-related reason. The MCP ``initialize``
    handshake — the only protocol traffic these pins drive — never touches the
    lifespan context, so substituting it leaves the ENTIRE SDK auth + session stack
    real, which is the part under contract.
    """

    async def aclose(self) -> None:
        """Match the teardown the process-lifespan guard performs on last release."""
        return None


def stub_heavy_startup(mcp: Any) -> None:
    """Neutralise the heavy build by replacing the fastmcp lifespan with a stub.

    PACKET 59 (fastmcp 3.x, design §5b-C2): fastmcp enters the user ``lifespan=`` (stored as
    ``mcp._lifespan``) ONCE per process; the ``_ProcessLifespanGuard`` + the
    ``mcp._lore_eager_guard`` attribute the old stub swapped are DELETED. So replace the
    lifespan wholesale with one that yields a :class:`_StubAppContext` instead of running the
    real build (probe gate → SurrealDB write stack → watcher). The MCP ``initialize``
    handshake — the only protocol traffic these auth pins drive — never touches the lifespan
    context, so substituting it leaves the ENTIRE SDK auth + session stack real, which is the
    part under contract.

    Args:
        mcp: The ``FastMCP`` returned by ``build_mcp_server``.
    """

    @contextlib.asynccontextmanager
    async def _stub_lifespan(_server: Any) -> Any:
        yield _StubAppContext()

    mcp._lifespan = _stub_lifespan


def mcp_session_id(response: AsgiResponse) -> str:
    """Pull the session id the streamable transport minted, or fail loudly."""
    session_id = response.header("mcp-session-id")
    assert session_id, (
        f"the server did not mint an mcp-session-id (status {response.status}, body "
        f"{response.body[:400]!r}); without a session there is nothing to hijack and "
        f"the ownership pin would pass vacuously"
    )
    return session_id


# --------------------------------------------------------------------------- #
# R16 — ONE handler-set derivation, feeding BOTH of R16's instruments.
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# The WIRE harness. Under R16 every posture/refusal assertion drives a real MCP
# session, because an in-process `mcp.<handler>(...)` call cannot tell a live guard
# from one that is dead on the wire.
# --------------------------------------------------------------------------- #


@dataclass
class WireSession:
    """One live, authenticated MCP session driven by the SDK's OWN CLIENT.

    ⚠ NOT A HAND-ROLLED JSON-RPC CLIENT (lead ruling, 2026-07-31). An earlier revision of
    this harness assembled ``tools/list`` / ``tools/call`` envelopes by hand. The SDK ships
    ``mcp.client.streamable_http.streamable_http_client(url, *, http_client=)`` plus
    ``ClientSession``, and — MEASURED, not assumed — it drives an in-process ASGI app
    perfectly when handed an ``httpx.AsyncClient`` over ``httpx.ASGITransport``: real
    handshake, real protocol, typed results. Packages over hand-rolling, in its ordinary
    direction, in test code. The hand-roll is deleted rather than kept beside it.

    Attributes:
        session: The SDK ``ClientSession``.
        mcp: The composed FastMCP, for STRUCTURAL assertions only — never to drive a
            posture claim, which R16's AST invariant enforces mechanically.
        token: The Bearer credential, or ``None`` for the unauthenticated shape.
    """

    session: Any
    mcp: Any
    token: str | None

    async def served_tool_names(self) -> set[str]:
        """The tool names this principal is OFFERED, read off the wire `tools/list`."""
        listing = await self.session.list_tools()
        return {tool.name for tool in listing.tools}

    async def call(self, name: str, arguments: dict[str, Any] | None = None) -> str:
        """Dispatch `name` over the wire; return the rendered text of the result."""
        result = await self.session.call_tool(name, arguments or {})
        return "".join(
            getattr(block, "text", "") for block in result.content
        )


@contextlib.asynccontextmanager
async def wire_session(
    tmp_path: Path,
    *,
    posture: str,
    principal: str | None,
    with_extension: bool = False,
    prepare: Callable[[Any], None] | None = None,
    verdict_override: Any = None,
) -> AsyncIterator[WireSession]:
    """Open a real MCP session against the composed server and yield the wire surface.

    NOTHING IS DEFAULTED THAT THE CODE BRANCHES ON: ``posture`` and ``principal`` are
    required keyword arguments, so every call site states the shape it exercises.

    Args:
        tmp_path: Per-test directory for the roster and the live root.
        posture: ``"hosted"`` | ``"lan_bearer"`` | ``"loopback"``.
        principal: ``"google"`` | ``"api_key"`` | ``None`` (unauthenticated).
        with_extension: Register one extension, so the second registration path is live.
        prepare: Called with the composed FastMCP before the app is built — used to
            register adversarial fixture tools (an UNANNOTATED one, for WB72).
        verdict_override: An ``AccessToken`` the verifier is forced to mint for any
            credential. The ONLY way to drive an adversarially-shaped principal (a forged
            ``client_id``) all the way to the wire, since a real principal's identity is
            whatever the verifier decides.

    Yields:
        A :class:`WireSession` whose `initialize` handshake has completed.
    """
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_asgi_app, build_mcp_server
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
    payload = base_config_payload(slug(), tmp_path / "live")
    if posture == "hosted":
        payload["auth"] = hosted_auth_block(roster)
    elif posture == "lan_bearer":
        payload["auth"] = lan_bearer_auth_block()
    elif posture != "loopback":  # pragma: no cover - guards the caller
        raise AssertionError(f"unknown posture {posture!r}")
    config = LoreConfig.model_validate(payload)

    google_token = google_access_token("wire-principal")

    def _respond(request: httpx.Request) -> httpx.Response:
        if google_token.encode() in request.content:
            return httpx.Response(
                200, json=admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)
            )
        return httpx.Response(401)

    spy = TokeninfoSpy(responder=_respond)
    server = LoreServer(config)
    if with_extension:
        from _extension_helpers import CounterExtension

        server.register_extension(CounterExtension())
    # The tokeninfo spy is injected ONLY where a Google branch exists. Passing it to a
    # posture with no google block would be meaningless — and it keeps the loopback and
    # LAN wire pins runnable TODAY, which is what proves this harness works at all rather
    # than leaving every wire pin red for an unrelated reason.
    mcp = (
        build_mcp_server(server, http_client=spy.client())
        if posture == "hosted"
        else build_mcp_server(server)
    )
    # PACKET 59: fastmcp's FastMCP has no ``.settings`` — the JSON-vs-SSE response mode is an
    # ``http_app(json_response=…)`` param (production's build_asgi_app leaves it at the
    # negotiated default). The MCP SDK streamable-http client handles the negotiated response,
    # so no per-response-mode override is needed here.
    if verdict_override is not None:

        async def _forced(_token: str) -> Any:
            return verdict_override

        mcp._token_verifier.verify_token = _forced
    if prepare is not None:
        prepare(mcp)
    stub_heavy_startup(mcp)
    app = build_asgi_app(mcp, config)

    token = {
        "google": google_token,
        "api_key": API_KEY_VALUE_LOCAL_AGENT,
        None: None,
    }[principal]

    # The Host the wire actually carries. Hosted traffic arrives through lore-caddy with
    # the PUBLIC hostname; loopback/LAN traffic carries the bind. Using the real Host
    # keeps the SDK's transport-security layer in the path of every wire pin.
    origin_url = (
        f"https://{PUBLIC_HOSTNAME}" if posture == "hosted"
        else f"http://{LOOPBACK_HOST}:{SERVER_PORT}"
    )
    headers = {"Authorization": f"Bearer {token}"} if token is not None else {}

    async with running_asgi_app(app):
        http_client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url=origin_url,
            headers=headers,
        )
        async with streamable_http_client(
            f"{origin_url}{MCP_PATH}", http_client=http_client
        ) as (read_stream, write_stream, _get_session_id):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield WireSession(session=session, mcp=mcp, token=token)


# --------------------------------------------------------------------------- #
# IN-PROCESS dispatch helpers. LEGITIMATE ONLY OUTSIDE THE POSTURE MODULES.
#
# ⚠ R16 part 2 bans in-process handler calls in the posture test modules, because an
# in-process call cannot distinguish a live guard from one that is dead on the wire
# (WB30/WB48/WB93, three waves, one root cause). These two helpers exist for the modules
# where in-process dispatch is the SUBJECT rather than a shortcut — the permission-resolver
# seam, whose contract is about the resolver being consulted, not about a served posture.
# The R16 AST invariant treats any posture module importing them as a violation.
# --------------------------------------------------------------------------- #


