"""The resource-server bearer-token verifier (packet 39 RE-CUT): ``LoreTokenVerifier``.

Implemented CONTRACT-FIRST against ``docs/design/2026-08-21-packet39-recut-oauth.md``
(§4 auth path, §3 identity model) and the FROZEN wave-1 contract
(``test_token_verifier.py`` + ``test_oauth_identity_seam.py``), which the
contract-adversary graded SUFFICIENT (``REPORT-adversary-39-w1.md``).

WHAT lore IS (design §1/§2): a RESOURCE SERVER. It VERIFIES a bearer token that
claude.ai obtained from the IdP; it never runs an OAuth authorization flow. The gate has
TWO layers, never conflated: the PROVIDER authenticates (token → verified identity), the
``principal`` table (packets 48/49) authorizes (identity → active principal → role).

TWO BRANCHES, tried in this order (design §4.1):

1. **API key** — ``PrincipalKeyStore.verify(presented)`` → ``KeyVerification(principal,
   key_name)`` → mint per-PRINCIPAL (finding #206). No network. A presented ``<name>:
   <secret>`` credential with a colon is an api-key attempt; a colon-free bearer (a
   Google ``ya29.`` token) is denied by ``verify`` (no colon) and falls through to the
   Google branch.
2. **Google** — verify the Google token, then admit against the ``principal`` table.
   Any non-admission → ``None`` (fastmcp maps ``None`` → 401).

⚠ GOOGLE VERIFICATION IS HAND-ROLLED, NOT ``fastmcp.GoogleTokenVerifier`` (finding #393,
contract-time READ of ``.venv/.../fastmcp/server/auth/providers/google.py``, re-confirmed
by the adversary). That class FAILS three BLOCKER properties this module upholds: it
sends the token as a URL QUERY PARAM (``google.py:108-112``, the journal-leak the threat
model forbids), it never checks ``aud`` against a configured ``client_id``
(``:123-133`` — a different-client token is ACCEPTED), and it collapses 401 and 5xx to
the same ``None`` (``:114-119`` — lore's cache cannot split negative caching). The
design's §4.1/§9/F3 authorised exactly this fallback ("hand-roll the tokeninfo POST only
with a cited READ"). So lore owns its own tokeninfo call: token NOT in the URL (POST
body), ``aud == google_client_id`` enforced, an email scope required, 401-vs-5xx
distinguished. It takes an injected ``http_client`` (design §4.3) so that call is
hermetic under test (``httpx.MockTransport``).

────────────────────────────────────────────────────────────────────────────────
THE MINTED ``AccessToken`` CONTRACT (what a correct build produces):

* **Google branch** (admitted hosted principal):
  ``AccessToken(token=<presented>, client_id=<google_client_id>, scopes=["lore:read"],
  subject=<principal.email>, expires_at=<absolute unix ts from the token's exp>,
  claims={"iss": <google_issuer>, "email": <normalised email>, "sub": <google sub>,
  "role": <principal.role>, "agent": None})``.
  ⚠ ``scopes`` is ``["lore:read"]`` — READ-ONLY, **regardless of role** (the
  READ-ONLY-hosted banner: hosted write moves to the RBAC packets 60-65). A hosted
  ``admin`` gets NO ``lore:write``; hard-coding ``admin ⇒ +lore:write`` is a DEFECT this
  packet pins against. ``role`` is carried in ``claims`` as forward-compat DATA for RBAC
  (design ADD), not acted on for capability here. ``agent`` is the optional
  ``(principal, agent)`` binding SEAM (forward-compat for packet 62), ``None`` in this
  packet — read through :func:`agent_of`, never a scattered ``claims["agent"]`` lookup.

* **API-key branch** (LAN/local principal — design §3.3, banner "LAN keeps full write"):
  ``AccessToken(token=<presented>, client_id=f"api_key:{principal.email}",
  scopes=["lore:read", "lore:write"], subject=<principal.email>,
  claims={"role": <principal.role>, "agent": None, "key_name": <key_name>})``.
  The identity is the PRINCIPAL (email), never the key name (#206): two keys of one human
  resolve to ONE identity. LAN api-keys keep FULL write (F7 role-gating deferred to RBAC).

WHERE THE SHARED PRIMITIVES LIVE (design §3.4/§3.5, ``lorerunes`` — the stdlib-only shared
home): the email normaliser is :func:`lorerunes.normalize_email`; the scope constants
``"lore:read"`` / ``"lore:write"`` and the ``role → capability`` functions
(:func:`lorerunes.hosted_scopes_for_role` / :func:`lorerunes.lan_scopes_for_role`) live
ONCE in ``lorerunes`` so the verifier that mints them, the wave-2 guard that checks them,
and the instructions renderer that names them share one home. This module REUSES them; it
re-declares none of them. The verdict cache is ``cachetools.TTLCache`` (design §4.2), the
token→verdict key is the shared :func:`loremaster.index.records.sha512_hex` digest (raw
tokens are never stored), never a hand-rolled ``hashlib`` clone (#102/#120 DRY law).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

import httpx
from cachetools import TTLCache
from fastmcp.server.auth import AccessToken, TokenVerifier

from loremaster.index.records import sha512_hex
from loremaster.principal_keys import PrincipalKeyStore
from loremaster.principals import Principal, PrincipalStore
from loremaster.store.surreal_schema import _PRINCIPAL_STATUS_ACTIVE
from lorerunes import (
    hosted_scopes_for_role,
    lan_scopes_for_role,
    normalize_email,
)

# Google's public tokeninfo endpoint (the hand-rolled verification's default target).
# A parameter, not a bake-in, because the recut made the issuer/endpoint CONFIG (the
# operator dismissed the "configurable issuer = downgrade" rationale — design §0/§4).
_DEFAULT_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
_DEFAULT_GOOGLE_ISSUER = "https://accounts.google.com"

# The claim key the OPTIONAL (principal, agent) binding lives under (design ADD / §3.3;
# sidecar E3). Spelled ONCE so the mint that writes it and :func:`agent_of` that reads it
# cannot drift.
_AGENT_CLAIM = "agent"
# The claim key carrying the authenticating api-key's label (audit only, api-key branch).
_KEY_NAME_CLAIM = "key_name"
# The identity claim keys the Google branch stamps (design §3.3 minted-AccessToken shape).
_ISSUER_CLAIM = "iss"
_EMAIL_CLAIM = "email"
_SUBJECT_CLAIM = "sub"
_ROLE_CLAIM = "role"

# HTTP status partition for the split negative cache (design §4.2). A 400/401 is a
# DEFINITIVE-invalid verdict (negative-cache it — a bad token must not hammer Google every
# request); every other non-200 (5xx / gateway) is a TRANSIENT blip (never cached — a
# Google outage must not lock a VALID token out for the cache TTL). Named constants (not
# bare literals) keep the PLR2004 magic-value gate satisfied and the split legible.
_HTTP_OK = 200
_HTTP_BAD_REQUEST = 400
_HTTP_UNAUTHORIZED = 401

# The per-verifier verdict cache bound (design §4.2 — ``cachetools.TTLCache``, per-instance,
# never module-global). The TTL is a coarse memory bound; a positive entry additionally
# carries its token's absolute ``exp``, re-checked against the injected clock on every
# cache read (design §4.2), so a token is never served past its own expiry regardless of
# the TTL. These are config-shaped defaults; the composition root (wave 3) may tune them.
_CACHE_MAXSIZE = 4096
_CACHE_TTL_S = 300.0

# The tagged shapes stored in the verdict cache. A positive entry carries the verified
# identity + its absolute expiry; a negative entry marks a definitively-invalid token.
_CACHE_OK = "ok"
_CACHE_BAD = "bad"


class _TokeninfoOutcome:
    """A non-dict tokeninfo outcome sentinel (transport blip / malformed / definitive).

    Distinguishes the three non-identity results the caching split branches on, without
    conflating them with a real (dict) tokeninfo body or with ``None``. Spelled as
    singletons below so identity comparison (``is``) is exact.
    """

    def __init__(self, name: str) -> None:
        self._name = name

    def __repr__(self) -> str:
        return self._name


# A transient failure (5xx, timeout, transport error) — deny WITHOUT caching (design §4.2:
# a Google blip must not lock a valid token out for the cache TTL).
_TRANSPORT_BLIP = _TokeninfoOutcome("<transport-blip>")
# A 200 whose body is not JSON — deny WITHOUT caching (a provider returning garbage
# transiently must not lock a token out).
_MALFORMED = _TokeninfoOutcome("<malformed>")
# A definitive-invalid verdict (400/401) — deny AND negative-cache (design §4.2).
_DEFINITIVE_INVALID = _TokeninfoOutcome("<definitive-invalid>")

__all__ = ["LoreTokenVerifier", "agent_of"]


def agent_of(access_token: AccessToken) -> str | None:
    """THE typed accessor for the ``(principal, agent)`` binding — ``identity.agent`` (E3).

    A resolved identity carries an OPTIONAL agent binding (forward-compat for the
    anti-spoofing packet 62, which mints server-bound ``(principal, agent)`` credentials).
    RBAC/packet-62 consumers read it through THIS ONE accessor — never a scattered
    ``token.claims["agent"]`` lookup — so the binding has one read seam and one place to
    evolve (sidecar E3: "expose it via ONE typed accessor identity.agent -> str | None, not
    scattered dict lookups").

    FAIL-CLOSED SEMANTICS (documented for packet 62): a missing or unresolvable binding
    returns ``None`` — the SAME value as an explicitly-unbound identity. So an agent-SCOPED
    operation in packet 62 that requires a bound agent must treat ``None`` as DENY (no
    agent → no agent authority), never as "any agent". In THIS packet (39) nothing binds an
    agent, so this always returns ``None`` — the seam exists so packet 62 is an EXTENSION,
    not a rewrite.

    Returns:
        The bound agent identity string, or ``None`` when unbound / absent (fail-closed).
    """
    claims = access_token.claims
    if not claims:
        return None
    return claims.get(_AGENT_CLAIM)


class LoreTokenVerifier(TokenVerifier):
    """The lore resource-server bearer-token verifier (a fastmcp ``TokenVerifier``).

    Args:
        principal_store: The ``principal`` admission authority (packet 48) — the Google
            branch reads ``get_by_subject`` / ``get_by_email`` / ``set_subject`` and the
            ``status`` / ``expires_at`` admission checks against it, on EVERY request (no
            admission caching — design §4.4).
        principal_key_store: The per-user API-key store (packet 49) — the api-key branch
            resolves a presented ``<name>:<secret>`` through its ``verify`` to a
            ``KeyVerification(principal, key_name)`` (#206). Breaking ``verify`` must red
            the api-key pins (ROUTING-IS-NOT-SHARING mutation proof).
        google_client_id: The configured OAuth client the token's ``aud`` MUST equal, or
            ``None`` for an api-key-only verifier (the ``LAN_BEARER`` posture — no Google
            branch). A ``None`` here means a presented Google token is never admitted.
        google_required_scopes: The scopes the token's grant must be a superset of; MUST
            include an email scope, or admission has no verified email to key on
            (design §4.1). ``None`` only when ``google_client_id`` is ``None``.
        google_issuer: The issuer stamped into the minted token's ``claims["iss"]``
            (config, per the recut). Defaults to Google's.
        tokeninfo_url: The tokeninfo endpoint the hand-rolled verification calls. Defaults
            to Google's; overridable so the composition root can point it at config.
        http_client: The injected ``httpx.AsyncClient`` the Google verification calls
            through (design §4.3). Tests pass an ``httpx.MockTransport``-backed client so
            no live socket is opened; ``None`` lets the build lazily construct its own
            (bounded ``httpx.Limits`` + explicit timeouts wired by the composition root).
        clock: A ``() -> float`` unix-time source, injected so the verdict-cache expiry
            checks are deterministic (design §4.2: ``expires_at`` minted and re-checked on
            a positive-cache read). ``None`` uses wall-clock time.
    """

    def __init__(
        self,
        *,
        principal_store: PrincipalStore,
        principal_key_store: PrincipalKeyStore,
        google_client_id: str | None = None,
        google_required_scopes: Sequence[str] | None = None,
        google_issuer: str = _DEFAULT_GOOGLE_ISSUER,
        tokeninfo_url: str = _DEFAULT_TOKENINFO_URL,
        http_client: httpx.AsyncClient | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        # Initialise the fastmcp ``TokenVerifier`` base so ``required_scopes`` / ``base_url``
        # exist as attributes (packet 39 wave 2/3, OBSERVATION-A): ``RemoteAuthProvider.__init__``
        # reads ``token_verifier.required_scopes`` UNCONDITIONALLY when the composition root wraps
        # this verifier for the HOSTED_OAUTH posture, and ``FastMCP(auth=…)`` handling likewise
        # expects an initialised base. ``required_scopes=None`` so fastmcp does NOT double-enforce
        # scopes against the minted ``lore:read`` — this verifier does its OWN Google-scope check
        # (``google_required_scopes`` in ``_verified_identity``); a fastmcp-level scope requirement
        # would reject the minted read scope. This does not change ``verify_token`` behaviour (the
        # wave-1 contract stays green).
        super().__init__(required_scopes=None)
        self._principal_store = principal_store
        self._principal_key_store = principal_key_store
        self._google_client_id = google_client_id
        self._google_required_scopes = (
            list(google_required_scopes) if google_required_scopes is not None else None
        )
        self._google_issuer = google_issuer
        self._tokeninfo_url = tokeninfo_url
        self._http_client = http_client
        self._clock = clock if clock is not None else time.time
        # The Google-verdict cache (design §4.2): SHA-512(token) → tagged verdict. Holds
        # the PROVIDER's verdict ONLY — admission is NEVER cached (design §4.4), so it is
        # re-evaluated against the live ``principal`` table on every request. Per-instance
        # (never module-global). The lock guards the sync cache ops so no ``await`` is ever
        # held across a mutation (design §4.2 "no await while the lock is held").
        self._verdict_cache: TTLCache[str, tuple[Any, ...]] = TTLCache(
            maxsize=_CACHE_MAXSIZE, ttl=_CACHE_TTL_S, timer=self._clock
        )
        self._cache_lock = asyncio.Lock()

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify a presented bearer ``token`` → an ``AccessToken`` or ``None``.

        Two branches in order (design §4.1): the api-key branch first (no network, routes
        through :meth:`PrincipalKeyStore.verify`), then — for a credential ``verify``
        rejects (e.g. a colon-free Google bearer) — the Google branch. A ``None`` from
        either branch is an authentication failure fastmcp maps to 401.
        """
        # 1. API-key branch — resolve the PRINCIPAL through the shared store verify (#206,
        #    ROUTING-IS-NOT-SHARING). A colon-free Google bearer is rejected here (no
        #    colon) and falls through to the Google branch.
        verification = await self._principal_key_store.verify(token)
        if verification is not None:
            return self._mint_api_key_identity(token, verification)

        # 2. Google branch — only when a Google client is configured (design §6 postures).
        if self._google_client_id is None:
            return None
        identity = await self._verified_identity(token)
        if identity is None:
            return None
        email_norm, sub, expires_at = identity
        principal = await self._admit(email_norm, sub)
        if principal is None:
            return None
        return self._mint_google_identity(token, principal, email_norm, sub, expires_at)

    # -- identity minting (design §3.3) ------------------------------------

    def _mint_api_key_identity(self, token: str, verification: Any) -> AccessToken:
        """Mint the api-key branch's ``AccessToken`` — identity is the PRINCIPAL (#206).

        The subject/client_id name the PRINCIPAL (email), never the key label — two keys
        of one human resolve to ONE identity. LAN api-keys keep FULL write in packet 39
        (banner; F7 role-gating deferred to RBAC), so scopes come from
        :func:`lorerunes.lan_scopes_for_role`.
        """
        principal: Principal = verification.principal
        return AccessToken(
            token=token,
            client_id=f"api_key:{principal.email}",
            scopes=sorted(lan_scopes_for_role(principal.role)),
            subject=principal.email,
            claims={
                _ROLE_CLAIM: principal.role,
                _AGENT_CLAIM: None,
                _KEY_NAME_CLAIM: verification.key_name,
            },
        )

    def _mint_google_identity(
        self,
        token: str,
        principal: Principal,
        email_norm: str,
        sub: str,
        expires_at: int | None,
    ) -> AccessToken:
        """Mint the Google branch's ``AccessToken`` — READ-ONLY hosted, role as DATA.

        ``client_id`` is the configured OAuth client (design §3.3), NEVER the Google
        ``sub`` (the fastmcp ``google.py:176`` reuse trap). ``scopes`` come from
        :func:`lorerunes.hosted_scopes_for_role` — exactly ``{lore:read}`` for EVERY role
        (READ-ONLY-hosted banner); ``role`` rides ``claims`` as forward-compat DATA for
        RBAC, not acted on for capability. ``agent`` is the packet-62 seam (``None`` here).
        """
        return AccessToken(
            token=token,
            client_id=self._google_client_id or "",
            scopes=sorted(hosted_scopes_for_role(principal.role)),
            subject=principal.email,
            expires_at=expires_at,
            claims={
                _ISSUER_CLAIM: self._google_issuer,
                _EMAIL_CLAIM: email_norm,
                _SUBJECT_CLAIM: sub,
                _ROLE_CLAIM: principal.role,
                _AGENT_CLAIM: None,
            },
        )

    # -- Google verification (hand-rolled, #393) ---------------------------

    async def _verified_identity(  # noqa: PLR0911
        self, token: str
    ) -> tuple[str, str, int | None] | None:
        """Verify a Google bearer → ``(normalised email, sub, absolute exp)`` or ``None``.

        The verified-IDENTITY layer only (design §3.1 AUTHENTICATION) — admission
        (§3.2 AUTHORIZATION) is a separate, never-cached step in :meth:`_admit`. Split
        negative caching (design §4.2): a definitive-invalid (400/401) is negative-cached;
        a transient blip / malformed body is denied WITHOUT caching; a positive verdict is
        cached under its absolute ``exp`` and re-checked against the injected clock on read.
        """
        now = self._clock()
        key = sha512_hex(token)
        cached = await self._cache_get(key)
        if cached is not None:
            if cached[0] == _CACHE_BAD:
                return None
            identity: tuple[str, str, int | None] = cached[1]
            exp = identity[2]
            if exp is None or exp > now:
                return identity
            # A positive entry whose token has EXPIRED: fall through and re-verify (design
            # §4.2 — an expired token is never served from the positive cache).

        data = await self._call_tokeninfo(token)
        if data is _TRANSPORT_BLIP or data is _MALFORMED:
            return None  # transient / garbage — NOT cached (design §4.2)
        if data is _DEFINITIVE_INVALID:
            await self._cache_put(key, (_CACHE_BAD,))
            return None
        assert isinstance(data, dict)

        aud = data.get("aud")
        if not aud or aud != self._google_client_id:
            return None  # a missing OR different-client aud is a hard reject (#393 BLOCKER)
        if not _is_verified(data.get("email_verified")):
            return None  # BEFORE any principal lookup (design F1 ordering)
        email = data.get("email")
        if not email:
            return None  # no email scope was granted → no verified email to key on
        if self._google_required_scopes:
            granted = set(str(data.get("scope") or "").split())
            if not set(self._google_required_scopes).issubset(granted):
                return None
        sub = data.get("sub")
        if not sub:
            return None  # the runtime OAuth identity is required (design §3.1)

        identity = (normalize_email(str(email)), str(sub), self._absolute_expiry(data, now))
        await self._cache_put(key, (_CACHE_OK, identity))
        return identity

    async def _call_tokeninfo(self, token: str) -> Any:
        """POST the token to the tokeninfo endpoint and classify the outcome (#393).

        ⚠ The token travels in the POST BODY, never a URL query param (httpx logs
        method+URL at INFO — a query-param token leaked into a systemd journal once, the
        threat model forbids it). Returns the parsed JSON dict on a clean 200, else one of
        the tagged sentinels the caching split in :meth:`_verified_identity` branches on.
        """
        client = self._client()
        try:
            response = await client.post(self._tokeninfo_url, data={"access_token": token})
        except httpx.HTTPError:
            return _TRANSPORT_BLIP  # timeout / connection error — transient, not cached
        status = response.status_code
        if status in (_HTTP_BAD_REQUEST, _HTTP_UNAUTHORIZED):
            return _DEFINITIVE_INVALID
        if status != _HTTP_OK:
            return _TRANSPORT_BLIP  # 5xx / gateway — transient, not cached (design §4.2)
        try:
            return response.json()
        except (ValueError, httpx.HTTPError):
            return _MALFORMED

    def _client(self) -> httpx.AsyncClient:
        """Return the injected client, lazily constructing (and caching) one if absent.

        Production wires a bounded ``httpx.AsyncClient`` (``httpx.Limits`` + explicit
        timeouts) at the composition root (design §4.3); tests always inject a
        ``MockTransport``-backed spy. The lazy construction is a fallback so a Google
        branch with no injected client does not crash — it is cached on the instance
        (never re-created per call) so the fallback carries no per-request leak.
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient()
        return self._http_client

    @staticmethod
    def _absolute_expiry(data: dict[str, Any], now: float) -> int | None:
        """Derive the minted token's ABSOLUTE ``expires_at`` (design / the unit trap).

        Google returns BOTH ``exp`` (an ABSOLUTE unix ts) and ``expires_in`` (seconds
        REMAINING, relative), both as STRINGS. ``exp`` is authoritative (an absolute ts is
        exactly what ``AccessToken.expires_at`` wants); ``expires_in`` is the fallback,
        made absolute by adding ``now``. A build that stored the RAW relative ``expires_in``
        (3599) would mint a 1970 timestamp and deny every token — the trap this guards.
        """
        exp = data.get("exp")
        if exp is not None:
            try:
                return int(exp)
            except (TypeError, ValueError):
                pass
        expires_in = data.get("expires_in")
        if expires_in is not None:
            try:
                return int(now) + int(expires_in)
            except (TypeError, ValueError):
                pass
        return None

    # -- admission (NEVER cached, design §4.4) -----------------------------

    async def _admit(self, email_norm: str, sub: str) -> Principal | None:
        """Admit a verified identity against the LIVE ``principal`` table — never cached.

        Re-evaluated on EVERY request (design §4.4), so a ``lore-adm suspend`` / expiry
        takes effect on the principal's NEXT request with no residual window. Resolution
        order (design §3.2): the returning-login O(1) ``get_by_subject`` fast path, then
        the first-login ``get_by_email`` fallback that binds the subject. Admission
        requires an ACTIVE, unexpired principal.
        """
        principal = await self._principal_store.get_by_subject(sub)
        if principal is None:
            principal = await self._principal_store.get_by_email(email_norm)
        if principal is None:
            return None
        if principal.status != _PRINCIPAL_STATUS_ACTIVE:
            return None
        if principal.expires_at is not None and principal.expires_at <= datetime.now(UTC):
            return None
        if principal.subject is None:
            # First login: bind the Google sub so a returning login resolves via the
            # O(1) get_by_subject fast path (packet-48 fill-on-login; idempotent re-login
            # is safe — setting a subject to its own value is not a UNIQUE conflict).
            await self._principal_store.set_subject(email=principal.email, subject=sub)
        return principal

    # -- verdict cache (design §4.2 — no await held across a mutation) ------

    async def _cache_get(self, key: str) -> tuple[Any, ...] | None:
        """Read one verdict-cache entry under the lock (a sync op, no ``await`` held)."""
        async with self._cache_lock:
            return self._verdict_cache.get(key)

    async def _cache_put(self, key: str, value: tuple[Any, ...]) -> None:
        """Write one verdict-cache entry under the lock (a sync op, no ``await`` held)."""
        async with self._cache_lock:
            self._verdict_cache[key] = value


def _is_verified(value: Any) -> bool:
    """Report whether a tokeninfo ``email_verified`` value is GENUINE verification.

    ⚠ Google's v3 ``/tokeninfo`` returns ``email_verified`` as the STRING ``"true"`` /
    ``"false"``, not a JSON bool (though a bool may appear on other surfaces). Both
    representations must be interpreted correctly (adversary WB4a/WB4b, finding #394): a
    ``bool(value)`` build ADMITS the string ``"false"`` (an UNVERIFIED email admitted — a
    §1 BLOCKER), while a ``value is True`` build DENIES the string ``"true"`` (100% denial
    of every real Google login — the #107 class). So truth is exactly ``True`` (the bool)
    OR a case-insensitive ``"true"`` (the string wire form); everything else — ``False``,
    ``"false"``, ``None``/absent — is NOT verification.

    Args:
        value: The raw ``email_verified`` value from the tokeninfo body (bool, string, or
            ``None`` when the key was absent).

    Returns:
        ``True`` only for genuine verification; ``False`` otherwise (fail-closed).
    """
    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() == "true"
