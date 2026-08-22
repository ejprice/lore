"""Helpers for the packet-39 RE-CUT wave-1 contract (``LoreTokenVerifier``).

This module carries the PLAIN helpers (functions/classes/constants) the fresh contract
imports; the pytest FIXTURE (``principal_stores``) is defined LOCALLY in
``test_token_verifier.py`` (the house idiom — ``test_principals_store.py`` does the same —
so importing a fixture as a test parameter never trips F811).

It stands on two existing shared modules and adds only what the re-cut's
principal-substrate model needs:

1. **The model-AGNOSTIC Google-tokeninfo + transport-spy machinery is REUSED from
   ``_auth_fixtures.py``** (DRY — brief-base §6). Those helpers describe Google's REAL
   ``/tokeninfo`` response shape (string-typed numerics, the ``expires_in``-vs-``exp`` unit
   trap, scope URIs vs the bare alias) and a generic ``httpx.MockTransport`` spy — none of
   which is tied to the RETIRED roster/SDK-FastMCP model, and all of which packet 59
   refreshed for standalone fastmcp. Re-exported here (see ``__all__``) so the fresh test
   files import from ONE seam; if the lead retires ``_auth_fixtures.py`` wholesale, only
   this line changes. ⚠ ``_auth_fixtures.make_verifier`` / ``hosted_auth_block`` /
   ``GoogleOAuthConfig`` / ``wire_session`` / ``sdk_bound_handler_names`` are the RETIRED
   model (R12 roster + in-memory ``ApiKeyVerifier`` + SDK internals) and are NOT reused —
   see ``REPORT-contract-39-w1.md`` for the archival escalation.

2. **The 48/49 principal substrate** — the re-cut admits against the ``principal`` table
   (``PrincipalStore.get_by_email`` / ``get_by_subject`` / ``set_subject`` / ``set_status``)
   and resolves api-keys through ``PrincipalKeyStore.verify`` (#206). The
   ``principal_stores`` fixture runs them on a REAL unique throwaway SurrealDB database so
   the admission logic is exercised against the engine's real ``option<> subject`` UNIQUE
   behaviour — never a fake that cannot reproduce it.

The Google HTTP call is the ONLY thing stubbed out (``TokeninfoSpy`` → ``httpx.MockTransport``).
"""

from __future__ import annotations

from typing import Any

# --- REUSED model-agnostic fixtures (DRY; _auth_fixtures.py, packet-59-refreshed) ------
from _auth_fixtures import (  # noqa: F401 - re-exported (see __all__) for the fresh test files
    GOOGLE_ACCESS_TOKEN_LIFETIME_S,
    GOOGLE_CLIENT_ID,
    GOOGLE_EMAIL_SCOPE_URI,
    GOOGLE_ISSUER,
    GRANTED_SCOPE_STRING,
    GRANTED_SCOPE_STRING_ALIAS_FORM,
    OMIT,
    OPERATOR_EMAIL,
    OPERATOR_SUBJECT,
    OTHER_OAUTH_CLIENT_ID,
    SCOPE_STRING_WITHOUT_EMAIL,
    SECOND_PRINCIPAL_EMAIL,
    SECOND_PRINCIPAL_SUBJECT,
    TOKENINFO_URL,
    UNLISTED_EMAIL,
    RecordedRequest,
    TokeninfoSpy,
    admitted_payload,
    always_json,
    always_raises,
    always_status,
    google_access_token,
    scripted,
    tokeninfo_payload,
)
from loremaster.principal_keys import PrincipalKeyStore
from loremaster.principals import Principal, PrincipalStore

# The wire scope values (design §3.5). ⚠ String literals here on purpose: the constants
# themselves live ONCE in ``lorerunes`` (a pre-contracted, not-yet-implemented primitive),
# and the pins assert the WIRE value a consumer/guard actually sees, not a symbol import —
# so they discriminate even before the lorerunes constant exists. The builder REUSES the
# lorerunes constants (DRY); a pin asserting the literal cannot be fooled by a build that
# spells the scope differently.
LORE_READ = "lore:read"
LORE_WRITE = "lore:write"

# The email scope the re-cut verifier is configured to require (design §4.1 — an email scope
# MUST be in required_scopes or admission has no email to key on).
REQUIRED_GOOGLE_SCOPES = [GOOGLE_EMAIL_SCOPE_URI]

# A well-formed api-key credential shape (design §F4 / packet 49: ``<name>:<secret>``).
API_KEY_NAME_ONE = "agent-alpha"
API_KEY_NAME_TWO = "agent-beta"
API_KEY_SECRET_ONE = "lk_7c1e93a4d0b64f28a5e1c9d7b3f0a682"
API_KEY_SECRET_TWO = "lk_2f8b40e6a1c94d537e0a6b2c8d1f5934"

__all__ = [
    # re-exported model-agnostic _auth_fixtures machinery
    "GOOGLE_ACCESS_TOKEN_LIFETIME_S",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_EMAIL_SCOPE_URI",
    "GOOGLE_ISSUER",
    "GRANTED_SCOPE_STRING",
    "GRANTED_SCOPE_STRING_ALIAS_FORM",
    "OMIT",
    "OPERATOR_EMAIL",
    "OPERATOR_SUBJECT",
    "OTHER_OAUTH_CLIENT_ID",
    "SCOPE_STRING_WITHOUT_EMAIL",
    "SECOND_PRINCIPAL_EMAIL",
    "SECOND_PRINCIPAL_SUBJECT",
    "TOKENINFO_URL",
    "UNLISTED_EMAIL",
    "RecordedRequest",
    "TokeninfoSpy",
    "admitted_payload",
    "always_json",
    "always_raises",
    "always_status",
    "google_access_token",
    "scripted",
    "tokeninfo_payload",
    # recut-specific helpers
    "LORE_READ",
    "LORE_WRITE",
    "REQUIRED_GOOGLE_SCOPES",
    "API_KEY_NAME_ONE",
    "API_KEY_NAME_TWO",
    "API_KEY_SECRET_ONE",
    "API_KEY_SECRET_TWO",
    "CountingPrincipalStore",
    "create_principal",
    "make_lore_token_verifier",
    "mint_credential",
]


def make_lore_token_verifier(
    *,
    principal_store: Any,
    principal_key_store: Any,
    google_client_id: str | None = GOOGLE_CLIENT_ID,
    google_required_scopes: list[str] | None = None,
    http_client: Any = None,
    clock: Any = None,
) -> Any:
    """Build a ``LoreTokenVerifier`` for a wave-1 pin.

    ``google_client_id`` and ``http_client`` are stated per-call rather than defaulted to a
    single shape (fixture-monoculture law): a pin exercising the api-key-only posture passes
    ``google_client_id=None``, and every Google pin passes the ``TokeninfoSpy``'s client.
    ``google_required_scopes`` defaults to :data:`REQUIRED_GOOGLE_SCOPES` (an email scope) —
    the value production configures — because a verifier with no required email scope has no
    email to key admission on (design §4.1).

    Lazy import: ``LoreTokenVerifier`` is a contract-time stub; keeping the import local
    matches the house idiom and keeps this module importable even while the target is
    mid-build.
    """
    from loremaster.token_verifier import LoreTokenVerifier

    return LoreTokenVerifier(
        principal_store=principal_store,
        principal_key_store=principal_key_store,
        google_client_id=google_client_id,
        google_required_scopes=(
            google_required_scopes
            if google_required_scopes is not None
            else list(REQUIRED_GOOGLE_SCOPES)
        ),
        http_client=http_client,
        clock=clock,
    )


async def create_principal(
    principal_store: PrincipalStore,
    *,
    email: str,
    role: str | None = None,
    status: str = "active",
    subject: str | None = None,
    expires_at: Any = None,
) -> Principal:
    """Create a principal and (optionally) transition it off the ``active`` default.

    ``PrincipalStore.create`` always starts a principal ``active``; a ``status="suspended"``
    request is applied via ``set_status`` after create, so a test can mint a suspended
    principal in one call.
    """
    principal = await principal_store.create(
        email=email, role=role, subject=subject, expires_at=expires_at
    )
    if status != "active":
        principal = await principal_store.set_status(email=email, status=status)
    return principal


async def mint_credential(
    principal_key_store: PrincipalKeyStore,
    *,
    email: str,
    name: str,
    secret: str,
) -> str:
    """Mint an api-key for ``email`` and return the presentable ``<name>:<secret>`` credential.

    Mirrors the CLI's ``mint-key`` (packet 49): the stored hash is
    ``sha512_hex(f"{name}:{secret}")`` and the returned credential is what a client presents
    back. Uses the store's OWN hash helper so the fixture can never drift from the store.
    """
    from loremaster.index.records import sha512_hex

    credential = f"{name}:{secret}"
    await principal_key_store.mint(email=email, name=name, secret_hash=sha512_hex(credential))
    return credential


class CountingPrincipalStore:
    """A pass-through ``PrincipalStore`` wrapper that COUNTS the admission lookups.

    Used only by the ordering pin: ``email_verified`` false/absent must deny BEFORE any
    principal lookup (design F1), which is an ORDERING property a plain deny cannot prove
    (a no-principal deny and an unverified-email deny both return ``None``). Wrapping the
    real store and asserting ``lookup_calls == 0`` for an unverified token is the
    discriminating instrument. Every other attribute delegates to the real store, so the
    verifier sees a faithful ``PrincipalStore``.
    """

    def __init__(self, inner: PrincipalStore) -> None:
        self._inner = inner
        self.lookup_calls = 0

    async def get_by_email(self, email: str) -> Principal | None:
        self.lookup_calls += 1
        return await self._inner.get_by_email(email)

    async def get_by_subject(self, subject: str) -> Principal | None:
        self.lookup_calls += 1
        return await self._inner.get_by_subject(subject)

    def __getattr__(self, name: str) -> Any:
        # Delegate set_subject / set_status / ensure_ready / close / etc. to the real store.
        return getattr(self._inner, name)
