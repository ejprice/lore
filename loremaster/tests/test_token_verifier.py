"""CONTRACT (contract-39-w1) — the packet-39 RE-CUT wave-1 verifier: ``LoreTokenVerifier``.

FRESH contract for the standalone-fastmcp resource-server design
(``docs/design/2026-08-21-packet39-recut-oauth.md``). The prior 2026-07-31 SDK-FastMCP
contract (``test_auth.py`` Google pins, ``test_auth_identity_seam.py``,
``test_auth_composition.py``) is RETIRED (§9) and awaits lead archival — see
``REPORT-contract-39-w1.md``. This module pins §13 GROUPS 1 (admission), 2 (Google
verification), 3 (#206 identity mint), the AUTH ∀, and the design ADD (role-as-data,
the ``(principal, agent)`` seam, ``role → capability`` as a function). Groups 4 (the #295
enforcement middleware — wave 2), 5/6 (composition/config — wave 3), and group 7 (the
child-table seam, in ``test_oauth_identity_seam.py``) are OUT of this file.

⚠ HEEDS THE READ-ONLY-HOSTED BANNER: hosted principals (member AND admin) get
``{lore:read}`` — NO hosted write scope is minted here (write → RBAC packets 60-65). The
role is carried as forward-compat DATA. ``admin ⇒ +lore:write`` on the hosted branch is a
DEFECT this file pins against.

CONTRACT-FIRST: every pin fails BEHAVIOURALLY against the ``LoreTokenVerifier`` stub
(``verify_token`` raises ``NotImplementedError``), never on an ImportError. The
satisfiability receipt (0-failed on a correct build) comes from the contract-adversary's
reference build (design §13); the discrimination rationale — the WRONG build each pin
catches — is stated at each pin.

The Google HTTP call is driven through an injected ``TokeninfoSpy`` (``httpx.MockTransport``
— no live socket); the admission path runs against the REAL 48/49 stores on a unique
throwaway SurrealDB database (``principal_stores`` fixture). Every fixture is
production-shaped and no branched-on value is a monoculture (≥2 distinct emails, ≥2 distinct
key names, member AND admin).
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from _token_verifier_fixtures import (
    API_KEY_NAME_ONE,
    API_KEY_NAME_TWO,
    API_KEY_SECRET_ONE,
    API_KEY_SECRET_TWO,
    GOOGLE_CLIENT_ID,
    GRANTED_SCOPE_STRING,
    LORE_READ,
    LORE_WRITE,
    OMIT,
    OPERATOR_EMAIL,
    OPERATOR_SUBJECT,
    OTHER_OAUTH_CLIENT_ID,
    SCOPE_STRING_WITHOUT_EMAIL,
    SECOND_PRINCIPAL_EMAIL,
    UNLISTED_EMAIL,
    CountingPrincipalStore,
    TokeninfoSpy,
    admitted_payload,
    always_json,
    always_status,
    create_principal,
    google_access_token,
    make_lore_token_verifier,
    mint_credential,
    scripted,
    tokeninfo_payload,
)
from loremaster.principal_keys import PrincipalKeyStore
from loremaster.principals import PrincipalStore
from loremaster.token_verifier import agent_of

# The readied (PrincipalStore, PrincipalKeyStore, env) triple the ``principal_stores``
# fixture yields — an alias so every test method's fixture param is typed once (E1d;
# behaviour-preserving — this changes no assertion, so the adversary SUFFICIENT verdict holds).
PrincipalStores = tuple[PrincipalStore, PrincipalKeyStore, SurrealEnv]

# A stable wall-clock anchor for the deterministic cache-expiry pin (design §4.2).
_FIXED_NOW = 1_700_000_000.0


def _google_token() -> str:
    """A realistically-shaped, unique Google bearer (opaque ``ya29.`` string)."""
    return google_access_token("w1")


@pytest_asyncio.fixture()
async def principal_stores() -> AsyncIterator[tuple[PrincipalStore, PrincipalKeyStore, SurrealEnv]]:
    """A readied ``(PrincipalStore, PrincipalKeyStore, env)`` on a fresh unique database.

    Defined LOCALLY (the house idiom — ``test_principals_store.py`` does the same) rather
    than imported, so the fixture name never shadows an import (F811). Both stores are
    readied and reaped on exit via a fresh admin connection, so no test leaks a database on
    the shared dev server. ``dim`` is irrelevant to an identity store (it embeds nothing) —
    ``PRODUCTION_DIM`` is passed only because ``make_env`` requires it.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()

    principal_store = PrincipalStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    principal_key_store = PrincipalKeyStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    try:
        await principal_store.ensure_ready()
        await principal_key_store.ensure_ready()
        yield principal_store, principal_key_store, env
    finally:
        await principal_key_store.close()
        await principal_store.close()
        await drop_database(env)


# ======================================================================================
# GROUP 1 — ADMISSION (design §3.2 / §13 group 1). email-keyed; email_verified is an
# explicit precondition; status/expiry re-checked on EVERY request; admission NEVER cached.
# ======================================================================================
class TestAdmission:
    async def test_active_principal_is_admitted(self, principal_stores: PrincipalStores) -> None:
        # POSITIVE CONTROL — an active principal presenting a well-formed, aud-matching,
        # email-verified Google token is admitted. Every deny pin below needs this to prove
        # the verifier is capable of saying yes.
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        result = await verifier.verify_token(_google_token())

        assert result is not None, "an active, email-verified, aud-matching principal must be admitted"
        assert result.subject == OPERATOR_EMAIL, (
            "the admitted identity's subject must be the PRINCIPAL (its stable admission "
            "key), so two logins of one human are one identity (#206)"
        )

    async def test_no_principal_is_denied(self, principal_stores: PrincipalStores) -> None:
        # A verified Google identity with NO active principal row gets in? BLOCKER. The
        # principal table is the admission authority; a verified token is not admission.
        principal_store, key_store, _env = principal_stores
        # No principal created for UNLISTED_EMAIL.
        spy = always_json(admitted_payload(email=UNLISTED_EMAIL, sub="999000111222333444555"))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is None

    async def test_suspended_principal_is_denied(self, principal_stores: PrincipalStores) -> None:
        # A suspended principal presenting a perfectly valid Google token is denied. A build
        # that checks existence but not status admits a revoked user.
        principal_store, key_store, _env = principal_stores
        await create_principal(
            principal_store, email=OPERATOR_EMAIL, role="member", status="suspended"
        )
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is None

    async def test_expired_principal_is_denied(self, principal_stores: PrincipalStores) -> None:
        # A principal whose expires_at is in the PAST is denied — even active, even verified.
        from datetime import UTC, datetime, timedelta

        principal_store, key_store, _env = principal_stores
        past = datetime.now(UTC) - timedelta(days=1)
        await create_principal(
            principal_store, email=OPERATOR_EMAIL, role="member", expires_at=past
        )
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is None

    async def test_future_expiry_principal_is_admitted(self, principal_stores: PrincipalStores) -> None:
        # The CONTROL for the expiry pin: a principal expiring in the FUTURE is still
        # admitted, so the expiry check is a real comparison, not "reject anything with an
        # expiry set".
        from datetime import UTC, datetime, timedelta

        principal_store, key_store, _env = principal_stores
        future = datetime.now(UTC) + timedelta(days=365)
        await create_principal(
            principal_store, email=OPERATOR_EMAIL, role="member", expires_at=future
        )
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is not None

    async def test_email_verified_false_is_denied_before_principal_lookup(
        self, principal_stores: PrincipalStores
    ) -> None:
        # F1 (BLOCKER): email_verified == true is an EXPLICIT admission precondition, checked
        # BEFORE any principal lookup. The principal EXISTS and is active — so if it were
        # admitted the ONLY thing wrong is email_verified. The CountingPrincipalStore proves
        # the ORDERING: an unverified email must never reach the store lookup (a plain deny
        # cannot distinguish this from a no-principal deny — both return None).
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        counting = CountingPrincipalStore(principal_store)
        spy = always_json(
            tokeninfo_payload(
                aud=GOOGLE_CLIENT_ID,
                email=OPERATOR_EMAIL,
                email_verified=False,
                scope=GRANTED_SCOPE_STRING,
                sub=OPERATOR_SUBJECT,
            )
        )
        verifier = make_lore_token_verifier(
            principal_store=counting,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is None
        assert counting.lookup_calls == 0, (
            "email_verified=false must be denied BEFORE any principal lookup (design F1); "
            "a build that keys admission before checking email_verified consulted the store"
        )

    async def test_email_verified_absent_is_denied(self, principal_stores: PrincipalStores) -> None:
        # F1: an ABSENT email_verified is not an admission fact either — distinct from the
        # false case (a build might guard `== False` and let `None`/absent through).
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        spy = always_json(
            tokeninfo_payload(
                aud=GOOGLE_CLIENT_ID,
                email=OPERATOR_EMAIL,
                email_verified=OMIT,
                scope=GRANTED_SCOPE_STRING,
                sub=OPERATOR_SUBJECT,
            )
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is None

    @pytest.mark.parametrize(
        ("email_verified", "expect_admit"),
        [
            ("true", True),  # Google's REAL wire form (a STRING) — must admit
            (True, True),  # a JSON bool true — must admit
            ("false", False),  # Google's real wire form for UNVERIFIED — must deny (WB4a admits it)
            (False, False),  # a JSON bool false — must deny
            (OMIT, False),  # absent — must deny (WB4b denies "true", this covers absent)
        ],
    )
    async def test_email_verified_string_and_bool_representations(
        self, principal_stores: PrincipalStores, email_verified: object, expect_admit: bool
    ) -> None:
        # BLOCKER (adversary WB4a/WB4b, finding #394). Google's v3 /tokeninfo returns
        # email_verified as the STRING "true"/"false", not a JSON bool (stated in the
        # _auth_fixtures docstring). This forces BOTH representations so the ONLY passing
        # build interprets truth correctly:
        #   • `bool(email_verified)`  ADMITS "false" (bool("false") is True) → an UNVERIFIED
        #     email admitted (§1 BLOCKER) → reddens the "false"→deny case.
        #   • `email_verified is True` DENIES "true" (the wire form) → 100% denial of every
        #     real Google login (#107 class) → reddens the "true"→admit case.
        # No single-representation fixture (that IS the monoculture the adversary caught).
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        spy = always_json(
            tokeninfo_payload(
                aud=GOOGLE_CLIENT_ID,
                email=OPERATOR_EMAIL,
                email_verified=email_verified,
                scope=GRANTED_SCOPE_STRING,
                sub=OPERATOR_SUBJECT,
            )
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        result = await verifier.verify_token(_google_token())
        if expect_admit:
            assert result is not None, (
                f"email_verified={email_verified!r} is GENUINE verification (string 'true' or "
                f"bool True) — it must ADMIT; a `email_verified is True` build denies the "
                f"string wire form (100% real-login denial)"
            )
        else:
            assert result is None, (
                f"email_verified={email_verified!r} is NOT genuine verification — it must DENY; "
                f"a `bool(email_verified)` build admits the string 'false' (unverified email)"
            )

    async def test_returning_login_fast_path_equals_email_result(
        self, principal_stores: PrincipalStores
    ) -> None:
        # design §3.2/§13 g1: get_by_subject fast-path == get_by_email result. A FIRST login
        # (subject NONE) admits via email and binds the subject; a RETURNING login (subject
        # bound) admits via the O(1) get_by_subject fast-path and yields the SAME identity. A
        # build whose subject fast-path resolves wrong (or to None) denies the returning user.
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        first = await verifier.verify_token(_google_token())  # email path, binds subject
        returning = await verifier.verify_token(_google_token())  # subject fast-path

        assert first is not None and returning is not None
        assert returning.subject == first.subject == OPERATOR_EMAIL, (
            "the returning-login fast-path must resolve to the same principal the first "
            "(email-keyed) login did"
        )

    async def test_admission_is_never_cached_suspend_takes_effect_next_request(
        self, principal_stores: PrincipalStores
    ) -> None:
        # design §4.4 (BLOCKER-shaped): admission is re-evaluated on EVERY request against the
        # live principal table — a suspend takes effect on the NEXT request, no residual
        # window. The Google VERDICT may be cached (a HIT: call_count stays 1), but the
        # ADMISSION decision must NOT be cached. Mutation: cache the admission decision → the
        # second call admits a suspended principal (this pin reds).
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )
        token = _google_token()

        first = await verifier.verify_token(token)
        assert first is not None, "the active principal must be admitted first (control)"

        await principal_store.set_status(email=OPERATOR_EMAIL, status="suspended")
        second = await verifier.verify_token(token)

        assert second is None, (
            "a principal suspended mid-session must be denied on the NEXT request — "
            "admission must never be cached (design §4.4)"
        )
        assert spy.call_count == 1, (
            "the Google verdict SHOULD be cached (same token) — this HIT is what makes the "
            "deny above prove admission was re-checked from the store, not re-verified from "
            "Google; call_count > 1 means the cache is absent and this pin proves less"
        )

    async def test_admission_normalisation_matches_a_lowercase_stored_principal(
        self, principal_stores: PrincipalStores
    ) -> None:
        # design §3.4: the admission email and the token email pass through the SHARED
        # lorerunes.normalize_email, so a mixed-case Google email admits against a
        # lowercase-stored principal. A build that compares raw strings denies the match.
        # (The normaliser's SEMANTICS are pinned in lorerunes/tests/test_email_normalisation.py;
        # this pin is that ADMISSION routes through it — the shared-mutation half.)
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")  # lowercase
        mixed_case = "EJPrice@FireHawkTransAm.ORG"
        spy = always_json(admitted_payload(email=mixed_case, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is not None, (
            "a mixed-case Google email must admit against the lowercase-stored principal via "
            "the shared lorerunes.normalize_email (design §3.4)"
        )


# ======================================================================================
# GROUP 2 — GOOGLE VERIFICATION (design §4.1 / §13 group 2). ⚠ HAND-ROLLED, not fastmcp's
# GoogleTokenVerifier (finding #393). Every pin here discriminates against a naive reuse.
# ======================================================================================
class TestGoogleVerification:
    async def _admittable(self, principal_store: PrincipalStore) -> None:
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")

    async def test_different_client_aud_is_denied(self, principal_stores: PrincipalStores) -> None:
        # BLOCKER — the aud check is the ONLY thing distinguishing OUR consent from any other
        # app's. The principal EXISTS and email_verified is true, so the sole reason to deny
        # is that the token was minted for a DIFFERENT OAuth client. ⚠ Discriminates against
        # fastmcp GoogleTokenVerifier, which checks only that aud is PRESENT (google.py:123-133)
        # and would ADMIT this token (finding #393).
        principal_store, key_store, _env = principal_stores
        await self._admittable(principal_store)
        spy = always_json(
            tokeninfo_payload(
                aud=OTHER_OAUTH_CLIENT_ID,  # a real, well-formed, DIFFERENT Google client
                email=OPERATOR_EMAIL,
                email_verified=True,
                scope=GRANTED_SCOPE_STRING,
                sub=OPERATOR_SUBJECT,
            )
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            google_client_id=GOOGLE_CLIENT_ID,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is None, (
            "a Google token whose aud is a DIFFERENT OAuth client must be denied — the aud "
            "check is not decorative (finding #393: fastmcp's GoogleTokenVerifier accepts it)"
        )

    async def test_absent_aud_is_denied(self, principal_stores: PrincipalStores) -> None:
        # A MISSING aud is a hard reject, never a skipped check.
        principal_store, key_store, _env = principal_stores
        await self._admittable(principal_store)
        spy = always_json(
            tokeninfo_payload(
                aud=None,  # omit the key entirely
                email=OPERATOR_EMAIL,
                email_verified=True,
                scope=GRANTED_SCOPE_STRING,
                sub=OPERATOR_SUBJECT,
            )
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is None

    async def test_matching_aud_is_admitted(self, principal_stores: PrincipalStores) -> None:
        # CONTROL: aud == the configured client_id admits (proves the aud check is not
        # "reject everything").
        principal_store, key_store, _env = principal_stores
        await self._admittable(principal_store)
        # admitted_payload sets aud=GOOGLE_CLIENT_ID (the configured client) — the match case.
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            google_client_id=GOOGLE_CLIENT_ID,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is not None

    async def test_google_client_id_is_the_configured_oauth_client_not_the_sub(
        self, principal_stores: PrincipalStores
    ) -> None:
        # adversary WB20 (finding #394): the minted Google-branch client_id must be the
        # CONFIGURED OAuth client (design §3.3), not the Google `sub`. ⚠ fastmcp's
        # GoogleTokenVerifier sets `client_id=sub` (google.py:176) — the exact reuse trap —
        # which makes client_id vary per USER instead of naming the OAuth app. All Google
        # principals share ONE client_id (the app); they are distinguished by SUBJECT.
        principal_store, key_store, _env = principal_stores
        await self._admittable(principal_store)
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            google_client_id=GOOGLE_CLIENT_ID,
            http_client=spy.client(),
        )

        result = await verifier.verify_token(_google_token())
        assert result is not None
        assert result.client_id == GOOGLE_CLIENT_ID, (
            "the Google-branch client_id must be the configured OAuth client, not the sub "
            f"(fastmcp's GoogleTokenVerifier sets client_id=sub — got {result.client_id!r})"
        )
        assert result.client_id != OPERATOR_SUBJECT, "client_id must not be the Google sub"

    async def test_missing_email_scope_is_denied(self, principal_stores: PrincipalStores) -> None:
        # design §4.1: an email scope MUST be granted or there is no verified email to key
        # admission on. Google omits `email` when the email scope was not consented, so this
        # fixture carries a real no-email grant.
        principal_store, key_store, _env = principal_stores
        await self._admittable(principal_store)
        spy = always_json(
            tokeninfo_payload(
                aud=GOOGLE_CLIENT_ID,
                email=None,  # Google omits email without the email scope
                email_verified=OMIT,
                scope=SCOPE_STRING_WITHOUT_EMAIL,
                sub=OPERATOR_SUBJECT,
            )
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        assert await verifier.verify_token(_google_token()) is None

    async def test_sub_is_extracted_and_used_as_the_runtime_subject(
        self, principal_stores: PrincipalStores
    ) -> None:
        # design §3.1: the Google `sub` (from the tokeninfo `sub` field) is the runtime OAuth
        # identity — extracted and (a) bound to the principal (get_by_subject resolves it
        # after login) and (b) stamped into the minted token's claims["sub"]. A build that
        # uses the email as the sub, or leaves it None (the odoo-code port bug), binds wrong.
        principal_store, key_store, _env = principal_stores
        await self._admittable(principal_store)
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        result = await verifier.verify_token(_google_token())

        assert result is not None
        assert result.claims.get("sub") == OPERATOR_SUBJECT, (
            "the minted token must carry the Google sub from the tokeninfo `sub` field, not "
            "the email and not None"
        )
        bound = await principal_store.get_by_subject(OPERATOR_SUBJECT)
        assert bound is not None and bound.email == OPERATOR_EMAIL, (
            "first login must bind the Google sub as the principal's runtime subject "
            "(set_subject), so a returning login resolves via get_by_subject"
        )

    async def test_token_never_appears_in_the_request_url(self, principal_stores: PrincipalStores) -> None:
        # BLOCKER (finding #393). httpx logs method+URL at INFO — a token in a URL query
        # param leaked into a systemd journal once. ⚠ fastmcp's GoogleTokenVerifier sends the
        # token as `params={"access_token": token}` (google.py:108-112), i.e. IN THE URL. A
        # compliant build carries it out-of-URL (POST body or an Authorization header).
        principal_store, key_store, _env = principal_stores
        await self._admittable(principal_store)
        token = _google_token()
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        await verifier.verify_token(token)

        assert spy.requests, "the verifier must actually call the provider to verify the token"
        for recorded in spy.requests:
            assert token not in recorded.url, (
                f"the bearer token appeared in the request URL {recorded.url!r} — it must "
                f"travel in the body or an Authorization header, never a URL (finding #393)"
            )
        # And it IS transmitted (so the verification is real), out-of-URL:
        transmitted = any(
            token.encode() in recorded.content
            or token in recorded.headers.get("authorization", "")
            for recorded in spy.requests
        )
        assert transmitted, "the token must be transmitted to the provider (in body or header)"

    async def test_401_is_negative_cached(self, principal_stores: PrincipalStores) -> None:
        # design §4.2 split negative caching: a definitive-invalid (401) result is
        # negative-cached, so a bad token does not hammer Google on every request.
        principal_store, key_store, _env = principal_stores
        spy = always_status(401)
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )
        token = _google_token()

        assert await verifier.verify_token(token) is None
        first_outbound = spy.call_count
        assert await verifier.verify_token(token) is None
        assert spy.call_count == first_outbound, (
            "a 401 (definitive invalid) must be negative-cached — the second call must make "
            "NO new outbound request"
        )

    async def test_5xx_is_not_cached(self, principal_stores: PrincipalStores) -> None:
        # design §4.2: a 5xx/transport blip must NOT be cached — caching it would lock a
        # VALID token out for the cache TTL. ⚠ Discriminates against a build that caches every
        # non-200 the same way (finding #393: fastmcp collapses 401 and 5xx to one None).
        principal_store, key_store, _env = principal_stores
        spy = always_status(503)
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )
        token = _google_token()

        assert await verifier.verify_token(token) is None
        first_outbound = spy.call_count
        assert await verifier.verify_token(token) is None
        assert spy.call_count > first_outbound, (
            "a 5xx must NOT be cached — the second call must make a fresh outbound request "
            "(a valid token must not be locked out by a transient blip)"
        )

    async def test_transient_5xx_then_success_admits(self, principal_stores: PrincipalStores) -> None:
        # The recovery half of the split: a 503 then a 200 admits — proving the 5xx was not
        # negative-cached into a permanent denial of a good token.
        principal_store, key_store, _env = principal_stores
        await self._admittable(principal_store)
        import httpx

        spy = scripted(
            [
                httpx.Response(503, text="upstream busy"),
                httpx.Response(200, json=admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)),
            ]
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )
        token = _google_token()

        # First attempt hits the 503; the second sees the 200. Whether a build retries
        # in-call or across calls, the token must ULTIMATELY admit — proving the 503 was not
        # negative-cached into a permanent denial of a good token.
        await verifier.verify_token(token)
        assert await verifier.verify_token(token) is not None, (
            "after a transient 503 then a 200, the token must admit — the 503 must not have "
            "been negative-cached"
        )

    async def test_malformed_json_denied_and_not_cached(self, principal_stores: PrincipalStores) -> None:
        # A 200 with a non-JSON body → None (never a crash), and NOT cached (a provider
        # returning garbage transiently must not lock a token out).
        principal_store, key_store, _env = principal_stores
        import httpx

        spy = TokeninfoSpy(
            responder=lambda _request: httpx.Response(200, text="<html>not json</html>")
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )
        token = _google_token()

        assert await verifier.verify_token(token) is None
        first_outbound = spy.call_count
        assert await verifier.verify_token(token) is None
        assert spy.call_count > first_outbound, "malformed provider JSON must not be cached"

    async def test_expires_at_is_absolute_not_relative(self, principal_stores: PrincipalStores) -> None:
        # THE UNIT TRAP (_auth_fixtures docstring): Google returns expires_in (seconds
        # REMAINING) and exp (an ABSOLUTE unix ts). A build that puts expires_in (3599) into
        # AccessToken.expires_at yields 1970-01-01 and the token is rejected as expired — a
        # 100% denial no verifier-level unit sees. The minted expires_at must be an ABSOLUTE
        # timestamp in a sane band around now.
        principal_store, key_store, _env = principal_stores
        await self._admittable(principal_store)
        lifetime = 3599
        spy = always_json(
            admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT, lifetime_s=lifetime)
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )

        before = int(time.time())
        result = await verifier.verify_token(_google_token())
        after = int(time.time())

        assert result is not None and result.expires_at is not None
        assert before + lifetime - 5 <= result.expires_at <= after + lifetime + 5, (
            f"expires_at {result.expires_at} is not an absolute unix timestamp ~{lifetime}s "
            f"in the future — a build that stored the relative expires_in ({lifetime}) here "
            f"yields 1970 and denies every token"
        )

    async def test_expired_token_is_not_served_from_cache(self, principal_stores: PrincipalStores) -> None:
        # design §4.2: expires_at is re-checked on a positive-cache read. A token admitted at
        # t0 and cached must NOT be served from the cache once the clock passes its expiry —
        # the verifier re-verifies (call_count grows). A build that serves the stale-valid
        # cache entry (call_count stays 1) fails.
        principal_store, key_store, _env = principal_stores
        await self._admittable(principal_store)
        lifetime = 3599
        clock_holder = [_FIXED_NOW]
        spy = always_json(
            admitted_payload(
                email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT, lifetime_s=lifetime, now=_FIXED_NOW
            )
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
            clock=lambda: clock_holder[0],
        )
        token = _google_token()

        assert await verifier.verify_token(token) is not None, "admitted at t0 (control)"
        outbound_after_admit = spy.call_count
        clock_holder[0] = _FIXED_NOW + lifetime + 100  # advance past the token's expiry
        await verifier.verify_token(token)

        assert spy.call_count > outbound_after_admit, (
            "an expired token must not be served from the positive cache — the verifier must "
            "re-verify (a fresh outbound) once the clock passes expires_at (design §4.2)"
        )


# ======================================================================================
# GROUP 3 — IDENTITY MINT, #206 (design §3.3 / §13 group 3). The api-key branch resolves to
# the PRINCIPAL via PrincipalKeyStore.verify — never the key name, never a constant.
# ======================================================================================
class TestApiKeyIdentityMint:
    async def test_api_key_resolves_to_the_principal_not_the_key_name(
        self, principal_stores: PrincipalStores
    ) -> None:
        # #206: the identity of an api-key request is the PRINCIPAL (email), never the key's
        # label. A build that mints identity from the key name reads two keys of one human as
        # two principals.
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        credential = await mint_credential(
            key_store, email=OPERATOR_EMAIL, name=API_KEY_NAME_ONE, secret=API_KEY_SECRET_ONE
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            google_client_id=None,  # api-key-only posture
        )

        result = await verifier.verify_token(credential)

        assert result is not None, "a valid api-key credential must authenticate"
        assert result.subject == OPERATOR_EMAIL, "the identity is the principal, not the key name"
        assert API_KEY_NAME_ONE not in (result.subject or ""), "the key name must not be the identity"
        assert result.client_id == f"api_key:{OPERATOR_EMAIL}", (
            "the api-key client_id must name the principal (design §3.3), so two humans are "
            "two client_ids"
        )

    async def test_two_keys_of_one_human_are_one_principal(self, principal_stores: PrincipalStores) -> None:
        # THE #206 PIN. Two DIFFERENT keys of the SAME principal resolve to ONE identity.
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        cred_one = await mint_credential(
            key_store, email=OPERATOR_EMAIL, name=API_KEY_NAME_ONE, secret=API_KEY_SECRET_ONE
        )
        cred_two = await mint_credential(
            key_store, email=OPERATOR_EMAIL, name=API_KEY_NAME_TWO, secret=API_KEY_SECRET_TWO
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            google_client_id=None,
        )

        first = await verifier.verify_token(cred_one)
        second = await verifier.verify_token(cred_two)

        assert first is not None and second is not None
        assert first.subject == second.subject == OPERATOR_EMAIL, (
            "two keys of one human must be ONE principal identity (#206); a build keying on "
            "the key name yields two identities"
        )
        assert first.client_id == second.client_id, "and one client_id"

    async def test_distinct_principals_get_distinct_identity(self, principal_stores: PrincipalStores) -> None:
        # F3 at the verifier level: two DIFFERENT humans get DIFFERENT identities, so whatever
        # the transport derives for session ownership cannot collapse them. (The wire-level
        # "X cannot resume Y's session" enforcement is wave-2/3, against the assembled app.)
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        await create_principal(principal_store, email=SECOND_PRINCIPAL_EMAIL, role="member")
        cred_x = await mint_credential(
            key_store, email=OPERATOR_EMAIL, name=API_KEY_NAME_ONE, secret=API_KEY_SECRET_ONE
        )
        cred_y = await mint_credential(
            key_store, email=SECOND_PRINCIPAL_EMAIL, name=API_KEY_NAME_ONE, secret=API_KEY_SECRET_TWO
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            google_client_id=None,
        )

        identity_x = await verifier.verify_token(cred_x)
        identity_y = await verifier.verify_token(cred_y)

        assert identity_x is not None and identity_y is not None
        assert identity_x.subject != identity_y.subject, "distinct principals, distinct identity"
        assert identity_x.client_id != identity_y.client_id

    async def test_api_key_branch_routes_through_principal_key_store_verify(
        self, principal_stores: PrincipalStores, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ROUTING-IS-NOT-SHARING (design §3.3 rider): the api-key branch resolves through
        # PrincipalKeyStore.verify. Breaking verify (forcing it to deny) must red api-key
        # auth. A build that hand-rolls its own hash check underneath (not routing) would
        # still admit — and this pin catches it.
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        credential = await mint_credential(
            key_store, email=OPERATOR_EMAIL, name=API_KEY_NAME_ONE, secret=API_KEY_SECRET_ONE
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            google_client_id=None,
        )
        # Sanity: it authenticates before the break (control).
        assert await verifier.verify_token(credential) is not None

        async def _broken_verify(_presented: str) -> None:
            return None

        monkeypatch.setattr(key_store, "verify", _broken_verify)

        assert await verifier.verify_token(credential) is None, (
            "breaking PrincipalKeyStore.verify must deny api-key auth — proving the branch "
            "ROUTES through it rather than hand-rolling a private hash check"
        )

    async def test_a_google_token_falls_through_to_the_google_branch(
        self, principal_stores: PrincipalStores
    ) -> None:
        # The branch ORDER (design §4.1): a colon-free Google bearer is not an api-key
        # credential (PrincipalKeyStore.verify denies a no-colon credential), so it falls
        # through to Google. With no google_client_id configured (api-key-only), it is denied
        # — proving the api-key branch did not somehow admit it.
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            google_client_id=None,  # no Google branch
        )

        assert await verifier.verify_token(_google_token()) is None


# ======================================================================================
# THE DESIGN ADD — role carried as DATA, the (principal, agent) seam, role → capability as
# a FUNCTION, and READ-ONLY hosted regardless of role (banner). Write → RBAC (60-65).
# ======================================================================================
class TestMintedIdentityCarriesRoleAndSeams:
    async def _google_admit(
        self, principal_store: PrincipalStore, key_store: PrincipalKeyStore, *, role: str
    ) -> Any:
        await create_principal(principal_store, email=OPERATOR_EMAIL, role=role)
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            http_client=spy.client(),
        )
        return await verifier.verify_token(_google_token())

    async def test_hosted_member_gets_read_only_scope(self, principal_stores: PrincipalStores) -> None:
        # The EXACT hosted scope set is {lore:read} (adversary WB21 / MISSING PIN #3): a
        # build minting `[lore:read, "lore:bogus"]` or any extra scope reds here, while the
        # write property (no lore:write) is still enforced.
        principal_store, key_store, _env = principal_stores
        result = await self._google_admit(principal_store, key_store, role="member")
        assert result is not None
        assert set(result.scopes) == {LORE_READ}, (
            f"a hosted member's scope set must be EXACTLY {{lore:read}} — got {result.scopes!r}"
        )

    async def test_hosted_admin_is_ALSO_read_only_regardless_of_role(
        self, principal_stores: PrincipalStores
    ) -> None:
        # ⚠ THE ANTI-PREMATURE-RBAC PIN (design ADD / banner). role → capability is a
        # FUNCTION, and in THIS packet the hosted surface is read-only for EVERY role. A build
        # that hard-codes `admin ⇒ +lore:write` (jumping ahead to RBAC) reds HERE. Hosted
        # write is RBAC's (packets 60-65), never this packet's.
        principal_store, key_store, _env = principal_stores
        result = await self._google_admit(principal_store, key_store, role="admin")
        assert result is not None
        assert set(result.scopes) == {LORE_READ}, (
            "a HOSTED admin's scope set must be EXACTLY {lore:read} in packet 39 — hosted is "
            "read-only regardless of role; `admin ⇒ +lore:write` is a DEFECT (write → RBAC "
            f"60-65). got {result.scopes!r}"
        )

    async def test_minted_identity_carries_the_role_as_data(self, principal_stores: PrincipalStores) -> None:
        # design ADD: the resolved identity carries principal.role (forward-compat DATA for
        # RBAC). member AND admin, so a build cannot hard-code one value (monoculture law).
        principal_store, key_store, _env = principal_stores
        member = await self._google_admit(principal_store, key_store, role="member")
        assert member is not None and member.claims.get("role") == "member"

    async def test_minted_identity_carries_the_admin_role_as_data(
        self, principal_stores: PrincipalStores
    ) -> None:
        principal_store, key_store, _env = principal_stores
        admin = await self._google_admit(principal_store, key_store, role="admin")
        assert admin is not None and admin.claims.get("role") == "admin", (
            "the admin role must be carried as data (so RBAC can act on it) even though it "
            "grants no hosted write here"
        )

    async def test_minted_identity_exposes_the_agent_binding_seam(
        self, principal_stores: PrincipalStores
    ) -> None:
        # design ADD + sidecar E3: the OPTIONAL (principal, agent) binding SEAM (forward-compat
        # for the anti-spoofing packet 62). In packet 39 there is no agent binding, so the slot
        # is present and the typed accessor `agent_of` reads None (fail-closed). The slot must
        # EXIST (anti adversary WB14) so packet 62 EXTENDS rather than rewrites; consumers read
        # it through `agent_of`, never a scattered claims["agent"] lookup.
        principal_store, key_store, _env = principal_stores
        result = await self._google_admit(principal_store, key_store, role="member")
        assert result is not None
        assert "agent" in result.claims, (
            "the (principal, agent) seam slot must exist in the minted claims — a build with "
            "no slot forces a packet-62 rewrite (adversary WB14)"
        )
        assert agent_of(result) is None, (
            "the typed accessor agent_of must read the unbound seam as None (fail-closed) in "
            "packet 39"
        )

    def test_agent_of_is_the_typed_fail_closed_accessor(self) -> None:
        # sidecar E3: `agent_of` is THE read seam for the (principal, agent) binding. It READS
        # a bound agent (proving it is not a hard-coded None), and FAIL-CLOSES (returns None)
        # on an unbound/absent binding — so a packet-62 agent-scoped op that requires a bound
        # agent treats None as DENY. A pure unit over the accessor (no verify_token needed).
        from fastmcp.server.auth import AccessToken

        bound = AccessToken(
            token="t", client_id="c", scopes=[LORE_READ], claims={"agent": "agent:pkt62-x"}
        )
        explicit_none = AccessToken(
            token="t", client_id="c", scopes=[LORE_READ], claims={"agent": None}
        )
        absent = AccessToken(token="t", client_id="c", scopes=[LORE_READ], claims={})
        assert agent_of(bound) == "agent:pkt62-x", "agent_of must READ a bound agent, not a constant None"
        assert agent_of(explicit_none) is None
        assert agent_of(absent) is None, "an ABSENT binding fail-closes to None (packet-62 deny)"

    async def test_api_key_principal_keeps_full_write(self, principal_stores: PrincipalStores) -> None:
        # ⚠ FLAGGED READING (see REPORT-contract-39-w1.md, escalation E2): the banner keeps
        # LAN/api-key principals at FULL write (F7 role-gating deferred to RBAC), so the
        # api-key branch mints lore:write. If the operator/lead rules api-keys are ALSO
        # read-only in packet 39, this single pin flips to `LORE_WRITE not in scopes`.
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")
        credential = await mint_credential(
            key_store, email=OPERATOR_EMAIL, name=API_KEY_NAME_ONE, secret=API_KEY_SECRET_ONE
        )
        verifier = make_lore_token_verifier(
            principal_store=principal_store,
            principal_key_store=key_store,
            google_client_id=None,
        )

        result = await verifier.verify_token(credential)
        assert result is not None
        assert LORE_READ in result.scopes
        assert LORE_WRITE in result.scopes, (
            "an api-key (LAN) principal keeps FULL write in packet 39 (banner; F7 deferred) "
            "— see the flagged escalation E2 in REPORT-contract-39-w1.md"
        )


# ======================================================================================
# THE AUTH ∀ (design §13). Every (token, provider-response, principal-state) triple yields
# EITHER None OR a well-formed AccessToken — no third fate, no exception. Each denial cause
# is FORCED with a fixture (quantifier law).
# ======================================================================================
class TestAuthQuantifier:
    async def test_every_google_fate_is_none_or_a_wellformed_access_token(
        self, principal_stores: PrincipalStores
    ) -> None:
        principal_store, key_store, _env = principal_stores
        await create_principal(principal_store, email=OPERATOR_EMAIL, role="member")

        # (label, tokeninfo-payload-or-status, expect_admit)
        deny_payloads = {
            "aud-mismatch": tokeninfo_payload(
                aud=OTHER_OAUTH_CLIENT_ID, email=OPERATOR_EMAIL, email_verified=True,
                scope=GRANTED_SCOPE_STRING, sub=OPERATOR_SUBJECT,
            ),
            "aud-absent": tokeninfo_payload(
                aud=None, email=OPERATOR_EMAIL, email_verified=True,
                scope=GRANTED_SCOPE_STRING, sub=OPERATOR_SUBJECT,
            ),
            "email_verified-false": tokeninfo_payload(
                aud=GOOGLE_CLIENT_ID, email=OPERATOR_EMAIL, email_verified=False,
                scope=GRANTED_SCOPE_STRING, sub=OPERATOR_SUBJECT,
            ),
            "email_verified-false-string": tokeninfo_payload(  # Google's REAL wire form (WB4a)
                aud=GOOGLE_CLIENT_ID, email=OPERATOR_EMAIL, email_verified="false",
                scope=GRANTED_SCOPE_STRING, sub=OPERATOR_SUBJECT,
            ),
            "email_verified-absent": tokeninfo_payload(
                aud=GOOGLE_CLIENT_ID, email=OPERATOR_EMAIL, email_verified=OMIT,
                scope=GRANTED_SCOPE_STRING, sub=OPERATOR_SUBJECT,
            ),
            "no-email-scope": tokeninfo_payload(
                aud=GOOGLE_CLIENT_ID, email=None, email_verified=OMIT,
                scope=SCOPE_STRING_WITHOUT_EMAIL, sub=OPERATOR_SUBJECT,
            ),
            "no-principal": admitted_payload(email=UNLISTED_EMAIL, sub="900000000000000000001"),
        }
        for label, payload in deny_payloads.items():
            spy = always_json(payload)
            verifier = make_lore_token_verifier(
                principal_store=principal_store, principal_key_store=key_store,
                http_client=spy.client(),
            )
            result = await verifier.verify_token(_google_token())
            assert result is None, f"fate {label!r} must deny (return None), got {result!r}"

        # The single ADMIT fate: a well-formed AccessToken mapping to the active principal,
        # carrying role, with NO write derived from role (hosted read-only).
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier = make_lore_token_verifier(
            principal_store=principal_store, principal_key_store=key_store,
            http_client=spy.client(),
        )
        admitted = await verifier.verify_token(_google_token())
        assert admitted is not None
        assert admitted.subject == OPERATOR_EMAIL
        assert admitted.claims.get("role") == "member"
        assert set(admitted.scopes) == {LORE_READ}, (
            "the admit fate maps to an active principal, carries role, and derives NO write "
            "capability from role — exactly {lore:read} (design ADD / banner)"
        )
