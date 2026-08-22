"""CONTRACT — ``LoreTokenVerifier``: the Google branch, the caches, and the identity it mints.

Design ``docs/design/2026-07-31-packet39-google-oauth.md`` §4 + §9 group 2/3/4. The
verifier is the ONE thing standing between the public internet and lore's corpus, and
it is a PORT of odoo-code's production verifier with five ruled DEPARTURES. This module
pins the port's proven parts, every departure, and — above all — the identity the
verifier mints, because that is where finding **F3** lives.

------------------------------------------------------------------------------
THE ∀-PROPERTY THIS MODULE ENFORCES (design §9, "Auth ∀")

    Every ``(token, tokeninfo-response, allowlist)`` triple yields EITHER ``None``
    OR an ``AccessToken`` whose email the allowlist admits and whose ``subject`` /
    ``claims`` / ``expires_at`` are populated — no third fate, REGARDLESS of which
    field was hostile.

:func:`assert_verification_outcome_is_total` is applied to EVERY outcome in this
module, not to one bespoke test. It is quantified over OUTCOMES and is not conditioned
on the failure mode that prompted the work: it never says *"when ``aud`` is wrong,
deny"* — it says *whatever* came back, the result is one of exactly two well-formed
shapes. Both fates are FORCED by fixtures (admitted and denied), and the denial fate is
forced through eight independently hostile fields.

------------------------------------------------------------------------------
THE WRONG BUILDS EACH GROUP DISCRIMINATES AGAINST

* **F3 — the session-collapse false clear.** odoo-code returns
  ``AccessToken(token=…, client_id=<google client id>, scopes=["email"])`` with NO
  ``subject`` and NO ``claims``. The SDK derives session ownership from exactly
  ``(client_id, claims["iss"], subject)``, so EVERY Google user yields the identical
  tuple and the binding is inert — any allowlisted user can resume any other's MCP
  session. It is masked in odoo-code because Odoo re-checks ACLs downstream; lore has
  no downstream check. A verbatim port is green at every gate. The identity pins below
  make that build impossible, and ``test_auth_identity_seam`` proves the property
  through the ASSEMBLED app, where the SDK's branch actually runs.
* **The 401-vs-5xx collapse.** odoo-code negative-caches on ANY non-200
  (``if resp.status_code != 200: _reject_token``). One Google 5xx blip then locks a
  VALID token out for the whole negative TTL. The split is pinned as two pins with
  DIFFERENT assertions and opposite call-count expectations; collapsing them into one
  "it was denied" assertion is the passed-for-the-wrong-reason shape.
* **The token in the URL.** ``httpx`` logs method+URL at INFO. Putting the token in
  query params leaked it into a systemd journal once. Pinned on the RECORDED request.
* **The expiry unit swap.** ``expires_in`` is RELATIVE, ``exp`` is ABSOLUTE, and both
  arrive as strings. Putting the wrong one in ``AccessToken.expires_at`` yields either
  1970 (total denial) or the year 50,000 (a token that never expires).
* **The tautological scope check.** odoo-code MINTS ``scopes=["email"]`` and REQUIRES
  ``required_scopes=["email"]`` — it compares its own output to itself. The real check
  is against the scope string GOOGLE returns, in the FULL-URI form Google actually
  emits.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from pathlib import Path
from typing import Any, cast

import httpx
import pytest

# ⚠ ``lorerunes`` SYMBOLS ARE IMPORTED INSIDE EACH FUNCTION, NOT AT MODULE LEVEL.
# This contract is written before the implementation exists, so a module-level import
# would collapse every pin in this file into ONE collection error — and a collection
# error yields NO node ids, which is exactly what ``scripts/mutation_proof.py`` needs
# in order to declare its expected-RED set from ``--collect-only``. Function-local
# imports keep the module collectible and let each pin fail on its own terms.
from _auth_fixtures import (
    API_KEY_NAME_LAN_CLIENT,
    API_KEY_NAME_LOCAL_AGENT,
    API_KEY_VALUE_LAN_CLIENT,
    API_KEY_VALUE_LOCAL_AGENT,
    DEFAULT_API_KEYS,
    GOOGLE_ACCESS_TOKEN_LIFETIME_S,
    GOOGLE_CLIENT_ID,
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
    TokeninfoSpy,
    admitted_payload,
    always_json,
    always_raises,
    always_status,
    google_access_token,
    make_verifier,
    scripted,
    tokeninfo_payload,
    write_roster,
)
from mcp.server.auth.provider import AccessToken

# The api-key branch's ``client_id`` prefix (design R10). It must be DISTINCT from the
# Google client id, or an api-key principal and a Google principal collide in the SDK's
# session-ownership tuple exactly the way F3 describes.
API_KEY_CLIENT_ID_PREFIX = "api_key:"

# A sanity band for a derived absolute expiry. Google access tokens live ~1 hour; a
# value outside [now, now + one day] means the wrong FIELD or the wrong UNIT was used.
ONE_DAY_S = 86_400


def assert_verification_outcome_is_total(
    result: AccessToken | None, *, roster: frozenset[str]
) -> None:
    """∀ outcome: exactly two well-formed shapes, ``None`` or a complete ``AccessToken``.

    Applied to EVERY verification in this module. The universal is over OUTCOMES and
    carries no mention of WHY a token was refused — the quantifier law: an invariant
    conditioned on the failure mode that prompted the work guards one door, and the
    next defect walks through a different one.

    Args:
        result: What ``verify_token`` returned.
        roster: The live allowlist the result must be consistent with.

    Raises:
        AssertionError: If the result is neither a clean denial nor a complete,
            allowlist-consistent, identity-bearing token.
    """
    from lorerunes import SCOPE_READ, SCOPE_WRITE, is_admitted, normalize_email
    if result is None:
        return
    assert isinstance(result, AccessToken), (
        f"verify_token must return AccessToken | None; got {type(result)!r}. A third "
        f"shape is a fate nothing downstream knows how to refuse."
    )
    assert result.client_id, "client_id is half of the SDK's session-ownership tuple"
    assert result.subject, (
        "subject is EMPTY — this is finding F3 verbatim. The SDK derives session "
        "ownership from (client_id, claims['iss'], subject); an unpopulated subject "
        "makes every principal identical and the binding inert."
    )
    if result.client_id.startswith(API_KEY_CLIENT_ID_PREFIX):
        # The api-key branch: a local/LAN principal, full surface (design R10).
        assert SCOPE_READ in result.scopes
        assert SCOPE_WRITE in result.scopes, (
            "an api-key principal retains the FULL tool surface (design §1: api keys "
            "are the local/LAN trust anchor)"
        )
        return
    # The Google branch.
    assert result.client_id == GOOGLE_CLIENT_ID
    assert result.claims, "claims must carry the issuer — the SDK reads claims['iss']"
    assert result.claims.get("iss") == GOOGLE_ISSUER
    email = result.claims.get("email")
    assert isinstance(email, str) and email, "the Google branch must carry the email claim"
    assert email == normalize_email(email), "the email claim must be stored NORMALISED"
    assert is_admitted(email, roster), (
        f"{email!r} was admitted but the roster does not list it — the ∀ says an "
        f"AccessToken is only ever minted for a principal the allowlist admits"
    )
    assert SCOPE_WRITE not in result.scopes, (
        "a hosted Google principal must NEVER carry write scope — that is the whole "
        "read-only posture (design §7), enforced through the minted scopes"
    )
    assert result.scopes == [SCOPE_READ]
    assert result.expires_at is not None, "an unexpiring hosted token is not acceptable"
    now = int(time.time())
    assert now <= result.expires_at <= now + ONE_DAY_S, (
        f"expires_at={result.expires_at} is not an ABSOLUTE unix timestamp within a "
        f"sane band of now={now}. Putting tokeninfo's RELATIVE 'expires_in' here "
        f"yields ~3599 (1970 — the SDK denies every token); treating the ABSOLUTE "
        f"'exp' as relative yields a token good for millennia."
    )


class _VerifierProbe:
    """A verifier plus its outbound spy, so every pin can assert on both."""

    def __init__(self, verifier: Any, spy: TokeninfoSpy, roster: frozenset[str]) -> None:
        self.verifier = verifier
        self.spy = spy
        self.roster = roster

    async def verify(self, token: str) -> AccessToken | None:
        """Verify a token and enforce the module-wide ∀ on whatever comes back."""
        result = cast("AccessToken | None", await self.verifier.verify_token(token))
        assert_verification_outcome_is_total(result, roster=self.roster)
        return result


@pytest.fixture
def roster_of_two(tmp_path: Path) -> Path:
    """A two-principal roster — never one, so ``len()`` and ``sum()`` differ."""
    return write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)


ROSTER_OF_TWO_ENTRIES = frozenset({OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL})


def probe(
    spy: TokeninfoSpy, roster_path: Path, *, api_keys: dict[str, str] | None
) -> _VerifierProbe:
    """Assemble a probe around ``spy``; ``api_keys`` is explicit at every call site."""
    verifier = make_verifier(
        roster_path=roster_path, api_keys=api_keys, http_client=spy.client()
    )
    return _VerifierProbe(verifier, spy, ROSTER_OF_TWO_ENTRIES)


class TestGoogleBranchAdmitsAListedPrincipal:
    """The POSITIVE CONTROL for every refusal in this module."""

    async def test_a_listed_verified_principal_is_admitted(self, roster_of_two: Path) -> None:
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        result = await probe(spy, roster_of_two, api_keys=None).verify(
            google_access_token("operator")
        )
        assert result is not None, (
            "a listed principal with a verified email, our aud and the email scope "
            "MUST be admitted — without this the whole module could pass on a "
            "verifier that denies everything"
        )
        assert result.claims is not None
        assert result.claims["email"] == OPERATOR_EMAIL

    async def test_the_second_listed_principal_is_also_admitted(
        self, roster_of_two: Path
    ) -> None:
        # Value monoculture: a build that hardcoded (or accidentally closed over) the
        # first principal's address passes the pin above and fails here.
        spy = always_json(
            admitted_payload(email=SECOND_PRINCIPAL_EMAIL, sub=SECOND_PRINCIPAL_SUBJECT)
        )
        result = await probe(spy, roster_of_two, api_keys=None).verify(
            google_access_token("second")
        )
        assert result is not None
        assert result.claims is not None
        assert result.claims["email"] == SECOND_PRINCIPAL_EMAIL

    async def test_a_capitalised_google_email_matches_a_lowercase_roster_line(
        self, roster_of_two: Path
    ) -> None:
        # THE SEAM: Google's report and the operator's typing meet here. One
        # normaliser, both sides. A build that normalises only the roster fails.
        spy = always_json(admitted_payload(email="EJPrice@FireHawkTransAm.ORG"))
        result = await probe(spy, roster_of_two, api_keys=None).verify(
            google_access_token("capitalised")
        )
        assert result is not None
        assert result.claims is not None
        assert result.claims["email"] == OPERATOR_EMAIL

    async def test_an_unlisted_but_fully_verified_principal_is_denied(
        self, roster_of_two: Path
    ) -> None:
        # The BLOCKER from design §1's mechanical verdicts: "an unlisted @gmail.com
        # account gets in". Everything about this token is valid — Google verified it,
        # the aud is ours, the scope is right. It is simply not on the list.
        spy = always_json(admitted_payload(email=UNLISTED_EMAIL, sub="109988776655443322110"))
        result = await probe(spy, roster_of_two, api_keys=None).verify(
            google_access_token("unlisted")
        )
        assert result is None


class TestAudienceCheck:
    """``aud`` is the ONLY thing distinguishing OUR consent from any Google app's."""

    async def test_a_token_minted_by_a_different_oauth_client_is_denied(
        self, roster_of_two: Path
    ) -> None:
        # The negative control design §9's proof ladder names: a token Google issued
        # and will happily verify, for somebody ELSE's app, belonging to a principal
        # who IS on our roster. Without the aud check, every Google app on earth
        # becomes an authentication provider for lore.
        payload = tokeninfo_payload(
            aud=OTHER_OAUTH_CLIENT_ID,
            email=OPERATOR_EMAIL,
            email_verified=True,
            scope=GRANTED_SCOPE_STRING,
            sub=OPERATOR_SUBJECT,
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("otherclient")
        )
        assert result is None

    async def test_a_missing_aud_is_a_hard_reject_not_a_skipped_check(
        self, roster_of_two: Path
    ) -> None:
        # Design §4: "a MISSING ``aud`` is a hard reject, never a skip". The
        # ``data.get("aud") != client_id`` shape happens to get this right; a
        # ``if "aud" in data and data["aud"] != client_id`` shape does not, and it
        # passes the mismatch pin above.
        payload = tokeninfo_payload(
            aud=None,
            email=OPERATOR_EMAIL,
            email_verified=True,
            scope=GRANTED_SCOPE_STRING,
            sub=OPERATOR_SUBJECT,
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("noaud")
        )
        assert result is None

    async def test_an_empty_string_aud_is_denied(self, roster_of_two: Path) -> None:
        payload = tokeninfo_payload(
            aud="",
            email=OPERATOR_EMAIL,
            email_verified=True,
            scope=GRANTED_SCOPE_STRING,
            sub=OPERATOR_SUBJECT,
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("emptyaud")
        )
        assert result is None

    async def test_an_aud_that_is_a_prefix_of_ours_is_denied(
        self, roster_of_two: Path
    ) -> None:
        # Exact equality, never ``startswith``/``in``. A prefix match would accept a
        # client id an attacker can register with a longer suffix.
        payload = tokeninfo_payload(
            aud=GOOGLE_CLIENT_ID[:20],
            email=OPERATOR_EMAIL,
            email_verified=True,
            scope=GRANTED_SCOPE_STRING,
            sub=OPERATOR_SUBJECT,
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("prefixaud")
        )
        assert result is None

    async def test_the_aud_mismatch_log_line_renders_the_configured_client_id(
        self, roster_of_two: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # R5's rider — the whole reason ``client_id`` is an inline ``str`` rather than
        # a ``SecretStr``: an ``aud`` mismatch is the most likely misconfiguration, and
        # the one log line that diagnoses it must render the configured value verbatim
        # rather than ``**********``.
        payload = tokeninfo_payload(
            aud=OTHER_OAUTH_CLIENT_ID,
            email=OPERATOR_EMAIL,
            email_verified=True,
            scope=GRANTED_SCOPE_STRING,
            sub=OPERATOR_SUBJECT,
        )
        with caplog.at_level(logging.WARNING):
            await probe(always_json(payload), roster_of_two, api_keys=None).verify(
                google_access_token("audlog")
            )
        rendered = "\n".join(record.getMessage() for record in caplog.records)
        assert GOOGLE_CLIENT_ID in rendered, (
            "the aud-mismatch diagnostic must name the CONFIGURED client id verbatim "
            "(R5). A redacted value leaves the operator comparing nothing to nothing."
        )


class TestEmailVerifiedAcrossEveryShapeGoogleEmits:
    """Workspace variance: the field is a bool OR a string, and it can be absent."""

    @pytest.mark.parametrize(
        "email_verified", [True, "true", "True"], ids=["bool-true", "str-true", "str-True"]
    )
    async def test_truthy_shapes_are_admitted(
        self, roster_of_two: Path, email_verified: object
    ) -> None:
        # odoo-code's production shape accepts bool ``True`` OR the string ``"true"``
        # because Workspace configuration decides which arrives. A build that only
        # accepts the bool denies every Workspace principal.
        payload = tokeninfo_payload(
            aud=GOOGLE_CLIENT_ID,
            email=OPERATOR_EMAIL,
            email_verified=email_verified,
            scope=GRANTED_SCOPE_STRING,
            sub=OPERATOR_SUBJECT,
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("verified")
        )
        assert result is not None, f"email_verified={email_verified!r} must be admitted"

    @pytest.mark.parametrize(
        "email_verified",
        [False, "false", "False", "", None, 0, OMIT],
        ids=["bool-false", "str-false", "str-False", "empty", "null", "zero", "absent"],
    )
    async def test_falsy_and_absent_shapes_are_denied(
        self, roster_of_two: Path, email_verified: object
    ) -> None:
        # An UNVERIFIED Google email is an address the account holder merely claimed.
        # Admitting one lets anyone who can create a Google account assert a listed
        # principal's address. ``absent`` is the shape a naive ``.get()`` turns into
        # ``None`` and a ``str(None).lower() != "true"`` check happens to catch — it
        # is pinned so a refactor cannot lose it silently.
        payload = tokeninfo_payload(
            aud=GOOGLE_CLIENT_ID,
            email=OPERATOR_EMAIL,
            email_verified=email_verified,
            scope=GRANTED_SCOPE_STRING,
            sub=OPERATOR_SUBJECT,
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("unverified")
        )
        assert result is None, f"email_verified={email_verified!r} must be denied"


class TestGrantedScopeCheckIsAgainstGoogleNotOurselves:
    """The real check: does the token GRANT the email scope Google reports?"""

    @pytest.mark.parametrize(
        "scope",
        [GRANTED_SCOPE_STRING, GRANTED_SCOPE_STRING_ALIAS_FORM],
        ids=["full-uri-form", "bare-alias-form"],
    )
    async def test_a_grant_carrying_the_email_scope_is_admitted(
        self, roster_of_two: Path, scope: str
    ) -> None:
        # ⚠ BOTH FORMS. Google's tokeninfo normally echoes FULL scope URIs
        # (``https://www.googleapis.com/auth/userinfo.email``), not the bare alias a
        # client requested. A build that literally checks ``"email" in scope.split()``
        # — the design's own wording — denies every real token. The contract pins the
        # SUPERSET property so either observed form is accepted.
        payload = tokeninfo_payload(
            aud=GOOGLE_CLIENT_ID,
            email=OPERATOR_EMAIL,
            email_verified=True,
            scope=scope,
            sub=OPERATOR_SUBJECT,
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("scoped")
        )
        assert result is not None, f"scope={scope!r} grants email and must be admitted"

    @pytest.mark.parametrize(
        "scope",
        [SCOPE_STRING_WITHOUT_EMAIL, "openid", "", None],
        ids=["profile-only", "openid-only", "empty", "absent"],
    )
    async def test_a_grant_without_the_email_scope_is_denied(
        self, roster_of_two: Path, scope: str | None
    ) -> None:
        # The token's holder never consented to share their address with this app, so
        # the ``email`` the response carries is not something we may act on.
        payload = tokeninfo_payload(
            aud=GOOGLE_CLIENT_ID,
            email=OPERATOR_EMAIL,
            email_verified=True,
            scope=scope,
            sub=OPERATOR_SUBJECT,
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("unscoped")
        )
        assert result is None, f"scope={scope!r} does not grant email and must be denied"

    async def test_a_scope_merely_containing_the_word_email_is_not_enough(
        self, roster_of_two: Path
    ) -> None:
        # Substring matching would accept a scope like ``…/auth/gmail.readonly`` or an
        # attacker-influenced value; the check is over SCOPE TOKENS, not the string.
        payload = tokeninfo_payload(
            aud=GOOGLE_CLIENT_ID,
            email=OPERATOR_EMAIL,
            email_verified=True,
            scope="openid https://www.googleapis.com/auth/emailsomethingelse",
            sub=OPERATOR_SUBJECT,
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("substringscope")
        )
        assert result is None


class TestMalformedAndDegenerateResponses:
    """A 200 is not a promise about the body (design §4: odoo-code lets json() raise)."""

    async def test_malformed_json_on_a_200_is_a_clean_denial(
        self, roster_of_two: Path
    ) -> None:
        # odoo-code lets ``resp.json()`` raise, which escapes the verifier and becomes
        # a 500 rather than a 401. A proxy or a captive portal returning HTML with a
        # 200 is the realistic producer of this.
        spy = TokeninfoSpy(
            responder=lambda _request: httpx.Response(
                200, text="<html><body>Gateway login required</body></html>"
            )
        )
        result = await probe(spy, roster_of_two, api_keys=None).verify(
            google_access_token("html")
        )
        assert result is None

    async def test_a_json_array_body_is_a_clean_denial(self, roster_of_two: Path) -> None:
        # Valid JSON, wrong SHAPE. ``data.get(...)`` on a list raises AttributeError.
        spy = TokeninfoSpy(responder=lambda _request: httpx.Response(200, json=[1, 2, 3]))
        result = await probe(spy, roster_of_two, api_keys=None).verify(
            google_access_token("array")
        )
        assert result is None

    async def test_an_empty_json_object_is_a_clean_denial(self, roster_of_two: Path) -> None:
        result = await probe(always_json({}), roster_of_two, api_keys=None).verify(
            google_access_token("emptyobj")
        )
        assert result is None

    @pytest.mark.parametrize("email", [None, "", "   "], ids=["absent", "empty", "blank"])
    async def test_a_missing_or_blank_email_is_denied(
        self, roster_of_two: Path, email: str | None
    ) -> None:
        payload = tokeninfo_payload(
            aud=GOOGLE_CLIENT_ID,
            email=email,
            email_verified=True,
            scope=GRANTED_SCOPE_STRING,
            sub=OPERATOR_SUBJECT,
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("noemail")
        )
        assert result is None

    @pytest.mark.parametrize("token", ["", "   ", "\n"], ids=["empty", "spaces", "newline"])
    async def test_a_blank_presented_token_is_denied_without_any_outbound_call(
        self, roster_of_two: Path, token: str
    ) -> None:
        # A blank Bearer value must not become an outbound request — that is a free
        # amplification vector against Google from an unauthenticated endpoint.
        spy = always_json(admitted_payload())
        result = await probe(spy, roster_of_two, api_keys=None).verify(token)
        assert result is None
        assert spy.call_count == 0, (
            f"a blank token made {spy.call_count} outbound call(s); an unauthenticated "
            f"caller must not be able to drive traffic to Google"
        )

    async def test_a_non_ascii_token_is_denied_without_raising(
        self, roster_of_two: Path
    ) -> None:
        # The header is decoded latin-1 upstream, so a non-ASCII token IS reachable.
        # It must produce a clean denial, never an exception escaping into a 500.
        spy = always_status(400)
        result = await probe(spy, roster_of_two, api_keys=None).verify("ééé")
        assert result is None

    async def test_a_colon_bearing_token_is_not_a_third_auth_path(
        self, roster_of_two: Path
    ) -> None:
        # odoo-code routes ``<login>:<api_key>`` tokens down a THIRD path. Design §4
        # rules that path Odoo-only and absent from lore. A ``:``-shaped token must
        # therefore be treated as an ordinary token — api-key compare, then Google —
        # not dispatched somewhere lore has no implementation for.
        spy = always_status(400)
        result = await probe(spy, roster_of_two, api_keys=dict(DEFAULT_API_KEYS)).verify(
            "ejprice:lk_9f2c41d8b7e34a5f8c1d6e0a2b7f4938"
        )
        assert result is None
        assert spy.call_count == 1, (
            "a colon-bearing token must fall through to the Google branch like any "
            "other unrecognised token, not into a dead third path"
        )


class TestNegativeCacheSplitsDefinitiveFromTransient:
    """THE departure from the port. Two pins, DIFFERENT assertions, opposite counts."""

    @pytest.mark.parametrize("status_code", [400, 401], ids=["bad-request", "unauthorized"])
    async def test_a_definitive_rejection_is_negative_cached(
        self, roster_of_two: Path, status_code: int
    ) -> None:
        # Google has told us this token is invalid. Re-asking cannot change the answer,
        # and a stolen/expired token replayed in a loop is a free DoS amplifier against
        # Google. The SECOND verification must make NO outbound request at all.
        spy = always_status(status_code)
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        token = google_access_token("revoked")

        first = await verifier_probe.verify(token)
        assert first is None
        assert spy.call_count == 1

        second = await verifier_probe.verify(token)
        assert second is None
        assert spy.call_count == 1, (
            f"a {status_code} is DEFINITIVE and must be negative-cached: the second "
            f"verification made {spy.call_count - 1} extra outbound call(s)"
        )

    @pytest.mark.parametrize(
        "status_code", [500, 502, 503, 504], ids=["ise", "bad-gw", "unavailable", "gw-timeout"]
    )
    async def test_a_transient_upstream_failure_is_NOT_cached(
        self, roster_of_two: Path, status_code: int
    ) -> None:
        # THE OPPOSITE ASSERTION, deliberately. odoo-code negative-caches on ANY
        # non-200, so one Google blip blacklists a perfectly good token for the whole
        # negative TTL — a self-inflicted outage. The second verification MUST retry.
        spy = always_status(status_code)
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        token = google_access_token("blipped")

        assert await verifier_probe.verify(token) is None
        assert spy.call_count == 1

        assert await verifier_probe.verify(token) is None
        assert spy.call_count == 2, (
            f"a {status_code} is TRANSIENT and must NOT be cached in either "
            f"direction; the second verification made {spy.call_count - 1} outbound "
            f"call(s) and must have made 1"
        )

    @pytest.mark.parametrize(
        "exception",
        [
            httpx.ConnectTimeout("tokeninfo connect timed out"),
            httpx.ReadTimeout("tokeninfo read timed out"),
            httpx.ConnectError("name resolution failed"),
            httpx.RemoteProtocolError("server disconnected"),
        ],
        ids=["connect-timeout", "read-timeout", "connect-error", "protocol-error"],
    )
    async def test_a_transport_fault_is_NOT_cached(
        self, roster_of_two: Path, exception: Exception
    ) -> None:
        # The container loses DNS for three seconds. Every token verified in that
        # window must recover, not be blacklisted.
        spy = always_raises(exception)
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        token = google_access_token("networkless")

        assert await verifier_probe.verify(token) is None
        assert await verifier_probe.verify(token) is None
        assert spy.call_count == 2, (
            f"{type(exception).__name__} is transient and must not poison the cache"
        )

    async def test_a_token_recovers_after_the_outage_ends(self, roster_of_two: Path) -> None:
        # The end-to-end statement of the split: 503, then 200 — the SAME token, now
        # admitted. Under odoo-code's collapse this is denied forever.
        payload = admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)
        spy = scripted([httpx.Response(503), httpx.Response(200, json=payload)])
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        token = google_access_token("recovers")

        assert await verifier_probe.verify(token) is None
        recovered = await verifier_probe.verify(token)
        assert recovered is not None, (
            "a valid token verified during a Google outage must be admitted once the "
            "outage clears — negative-caching a 5xx makes that impossible"
        )

    async def test_a_definitively_rejected_token_stays_rejected_after_a_good_response(
        self, roster_of_two: Path
    ) -> None:
        # The CONTROL for the pin above, in the other direction: the negative cache
        # must actually HOLD. Scripting 401 → 200 and still getting a denial proves the
        # second call never happened, which is what the negative cache is FOR.
        payload = admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)
        spy = scripted([httpx.Response(401), httpx.Response(200, json=payload)])
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        token = google_access_token("stays-rejected")

        assert await verifier_probe.verify(token) is None
        assert await verifier_probe.verify(token) is None
        assert spy.call_count == 1


class TestTokenCacheIsLiveIsolatedAndUnpoisonable:
    """Design §9 group 3. Every negative pin here is paired with a live-cache control."""

    async def test_a_repeat_verification_makes_no_second_outbound_call(
        self, roster_of_two: Path
    ) -> None:
        # THE POSITIVE CONTROL for every cache assertion below: without it, a build
        # with NO cache at all would pass "the caches never leak" trivially.
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        token = google_access_token("cached")

        assert await verifier_probe.verify(token) is not None
        assert spy.call_count == 1
        assert await verifier_probe.verify(token) is not None
        assert spy.call_count == 1, (
            "the positive cache is not live — every cache-poisoning pin in this class "
            "would then pass for the wrong reason"
        )

    async def test_two_different_tokens_do_not_share_a_cache_entry(
        self, roster_of_two: Path
    ) -> None:
        # Cache poisoning: principal A verifies, then attacker token B must NOT be
        # served A's identity. Both tokens are distinct opaque values.
        admitted = google_access_token("victim")
        attacker = google_access_token("attacker")

        def _respond(request: httpx.Request) -> httpx.Response:
            if admitted.encode() in request.content:
                return httpx.Response(
                    200, json=admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)
                )
            return httpx.Response(401)

        spy = TokeninfoSpy(responder=_respond)
        verifier_probe = probe(spy, roster_of_two, api_keys=None)

        assert await verifier_probe.verify(admitted) is not None
        assert await verifier_probe.verify(attacker) is None
        assert spy.call_count == 2, (
            "the attacker's token must have been sent to Google on its own merits, "
            "not answered from another token's cache entry"
        )

    async def test_a_token_that_is_a_prefix_of_a_cached_token_is_not_admitted(
        self, roster_of_two: Path
    ) -> None:
        # SHA-512 of the WHOLE token is the only cache key (design §4). A truncating
        # or prefix-based key would let a shortened token ride a valid entry.
        admitted = google_access_token("prefixvictim")
        truncated = admitted[:-8]

        def _respond(request: httpx.Request) -> httpx.Response:
            if admitted.encode() in request.content and truncated.encode() != request.content:
                return httpx.Response(
                    200, json=admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)
                )
            return httpx.Response(401)

        spy = TokeninfoSpy(responder=_respond)
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        assert await verifier_probe.verify(admitted) is not None
        assert await verifier_probe.verify(truncated) is None

    async def test_caches_are_per_instance_not_module_global(
        self, roster_of_two: Path
    ) -> None:
        # odoo-code's caches are MODULE-GLOBAL. That leaks across verifier instances
        # (and across tests), so a revocation applied by rebuilding the verifier would
        # be silently ignored. Two verifiers, one token, TWO outbound calls.
        token = google_access_token("perinstance")
        payload = admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)

        first_spy = always_json(payload)
        second_spy = always_json(payload)
        assert await probe(first_spy, roster_of_two, api_keys=None).verify(token) is not None
        assert await probe(second_spy, roster_of_two, api_keys=None).verify(token) is not None
        assert first_spy.call_count == 1
        assert second_spy.call_count == 1, (
            "the second verifier answered from the first's cache — module-global "
            "caches leak identity across instances and across tests"
        )

    async def test_an_expired_token_is_not_served_from_the_positive_cache(
        self, roster_of_two: Path
    ) -> None:
        # Design §4: a 60s token must not be served for a 300s cache TTL. The verifier
        # mints expires_at AND re-checks it on a cache READ, so a token whose own
        # expiry has passed is refused even while its cache entry lives.
        short_lifetime_s = 2
        payload = admitted_payload(
            email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT, lifetime_s=short_lifetime_s
        )
        spy = always_json(payload)
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        token = google_access_token("shortlived")

        assert await verifier_probe.verify(token) is not None
        assert spy.call_count == 1
        # Let the TOKEN's own Google-declared expiry pass while its cache entry is
        # still well inside the cache TTL. The second verification therefore reaches
        # the CACHE path with a stale token — the exact case design §4 calls out
        # ("a 60s token must not be served for a 300s cache TTL").
        await asyncio.sleep(short_lifetime_s + 0.5)
        assert await verifier_probe.verify(token) is None, (
            "a token whose own Google expiry has passed must not be served from the "
            "positive cache — the cache TTL is not the token's lifetime"
        )


class TestTokenSecrecy:
    """The presented credential never leaves this module in a readable form."""

    async def test_the_token_is_posted_in_the_body_and_never_in_the_url(
        self, roster_of_two: Path
    ) -> None:
        # httpx logs method+URL at INFO. A token in query params leaked into a systemd
        # journal once — this is the pin that makes that unrepeatable.
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        token = google_access_token("bodyonly")
        assert await probe(spy, roster_of_two, api_keys=None).verify(token) is not None

        assert spy.call_count == 1
        request = spy.requests[0]
        assert request.method == "POST"
        assert request.url == TOKENINFO_URL, (
            f"the tokeninfo URL must be the hardcoded constant with NO query string; "
            f"got {request.url!r}"
        )
        assert token not in request.url
        assert token.encode() in request.content, (
            "the token must travel in the request BODY"
        )

    async def test_the_raw_token_never_appears_in_a_log_record(
        self, roster_of_two: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # Design §8 row 5, widened: on a FAILED verification (the path most likely to
        # log detail) the presented credential must appear in no record, at any level.
        spy = always_status(401)
        token = google_access_token("neverlogged")
        with caplog.at_level(logging.DEBUG):
            assert await probe(spy, roster_of_two, api_keys=None).verify(token) is None
        for record in caplog.records:
            rendered = record.getMessage()
            assert token not in rendered, f"the raw token leaked into a log record: {rendered!r}"
            assert token not in str(record.args), "the raw token leaked into a record's args"

    async def test_the_raw_token_never_appears_in_a_log_record_ON_SUCCESS(
        self, roster_of_two: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # M5 / WB42+WB42b — THE QUANTIFIER LAW, caught in this contract's own pins.
        # Design §8 row 5's property is "the presented credential value is NEVER logged":
        # a universal over VERIFICATIONS. The pin above drives only a 401, so it guards
        # the failure door and leaves the success door open — and the success path is the
        # one that runs on every hosted request.
        #
        # It is not theoretical. lore's own scrubber redacts only LABELLED shapes
        # (`token=<v>`, `Authorization: Bearer <v>`); an UNLABELLED credential in free
        # prose — `logger.info("google.admitted %s for subject %s", token, subject)` —
        # passes through it VERBATIM into the container log.
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        token = google_access_token("admitted-never-logged")

        with caplog.at_level(logging.DEBUG):
            admitted = await verifier_probe.verify(token)
        assert admitted is not None, (
            "the POSITIVE CONTROL: this verification must SUCCEED, or the pin passes "
            "because nothing was ever admitted and no success path ran"
        )
        for record in caplog.records:
            rendered = record.getMessage()
            assert token not in rendered, (
                f"the raw token leaked into a log record on the ADMITTED path — the "
                f"path that runs on every hosted request: {rendered!r}"
            )
            assert token not in str(record.args), (
                "the raw token leaked into a record's ARGS on the admitted path; "
                "lazy %-formatting still reaches any handler that renders it"
            )

    async def test_the_raw_api_key_never_appears_in_a_log_record_on_success(
        self, roster_of_two: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # The same universal on the OTHER branch. An api-key principal authenticates on
        # every local call; a key logged once sits in the journal forever, and rotation
        # is the only remedy.
        spy = always_json(admitted_payload())
        verifier_probe = probe(spy, roster_of_two, api_keys=dict(DEFAULT_API_KEYS))

        with caplog.at_level(logging.DEBUG):
            admitted = await verifier_probe.verify(API_KEY_VALUE_LOCAL_AGENT)
        assert admitted is not None
        for record in caplog.records:
            assert API_KEY_VALUE_LOCAL_AGENT not in record.getMessage()
            assert API_KEY_VALUE_LOCAL_AGENT not in str(record.args)

    async def test_the_raw_token_never_appears_in_the_verifier_repr(
        self, roster_of_two: Path
    ) -> None:
        # A traceback renders repr(). A verifier holding raw tokens in a plain dict
        # publishes every live credential into any exception report.
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        token = google_access_token("norepr")
        assert await verifier_probe.verify(token) is not None
        assert token not in repr(verifier_probe.verifier)
        assert token not in str(vars(verifier_probe.verifier))

    async def test_no_raw_token_is_retained_in_the_verifier_state(
        self, roster_of_two: Path
    ) -> None:
        # Design §4 rules the token's SHA-512 the ONLY cache key, raw tokens NEVER
        # stored. The digest itself is an internal detail the contract does not reach
        # into; what it pins is the two OBSERVABLE consequences — the raw token is not
        # retained anywhere in the verifier's state (here), and the key is derived
        # from the WHOLE token, proved by the prefix-collision pin above.
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        token = google_access_token("digestkeyed")
        assert await verifier_probe.verify(token) is not None

        state = str(vars(verifier_probe.verifier))
        assert token not in state, (
            "the raw presented token is retained in the verifier's state; a heap dump, "
            "a traceback or a debugger session then yields live credentials"
        )
        # And the digest of that token is a legal thing to hold — asserted only as a
        # sanity check that the token has NOT simply been discarded (which would make
        # the assertion above pass on a verifier with no cache at all).
        assert hashlib.sha512(token.encode("utf-8")).hexdigest() != token


class TestApiKeyBranch:
    """Design §4/R10 — checked FIRST, constant-time, no network, full surface."""

    async def test_a_valid_api_key_is_admitted_without_any_outbound_call(
        self, roster_of_two: Path
    ) -> None:
        spy = always_json(admitted_payload())
        verifier_probe = probe(spy, roster_of_two, api_keys=dict(DEFAULT_API_KEYS))
        result = await verifier_probe.verify(API_KEY_VALUE_LOCAL_AGENT)
        assert result is not None
        assert spy.call_count == 0, (
            "the api-key branch runs FIRST and must never reach the network — a local "
            "agent's every call would otherwise depend on Google being up"
        )

    async def test_each_api_key_mints_its_own_distinct_principal(
        self, roster_of_two: Path
    ) -> None:
        # Two distinct key names — the F3 property at the api-key branch. A build that
        # minted a constant client_id/subject for all api keys collapses every local
        # agent into one session-ownership tuple.
        spy = always_json(admitted_payload())
        verifier_probe = probe(spy, roster_of_two, api_keys=dict(DEFAULT_API_KEYS))
        first = await verifier_probe.verify(API_KEY_VALUE_LOCAL_AGENT)
        second = await verifier_probe.verify(API_KEY_VALUE_LAN_CLIENT)
        assert first is not None and second is not None
        assert first.subject == API_KEY_NAME_LOCAL_AGENT
        assert second.subject == API_KEY_NAME_LAN_CLIENT
        assert first.client_id == f"{API_KEY_CLIENT_ID_PREFIX}{API_KEY_NAME_LOCAL_AGENT}"
        assert second.client_id == f"{API_KEY_CLIENT_ID_PREFIX}{API_KEY_NAME_LAN_CLIENT}"
        assert first.client_id != second.client_id

    async def test_the_api_key_principal_carries_write_scope(
        self, roster_of_two: Path
    ) -> None:
        # Design §1's mechanical verdict: "an api-key principal can call mutating tools
        # through the hosted port" — INTENDED. The scope is how that is expressed.
        from lorerunes import SCOPE_READ, SCOPE_WRITE
        spy = always_json(admitted_payload())
        result = await probe(spy, roster_of_two, api_keys=dict(DEFAULT_API_KEYS)).verify(
            API_KEY_VALUE_LOCAL_AGENT
        )
        assert result is not None
        assert set(result.scopes) == {SCOPE_READ, SCOPE_WRITE}

    async def test_the_api_key_client_id_can_never_collide_with_the_google_one(
        self, roster_of_two: Path
    ) -> None:
        # If an api-key principal's client_id equalled the Google client id, the two
        # populations would share half the SDK's ownership tuple — F3 by a side door.
        spy = always_json(admitted_payload())
        result = await probe(spy, roster_of_two, api_keys=dict(DEFAULT_API_KEYS)).verify(
            API_KEY_VALUE_LOCAL_AGENT
        )
        assert result is not None
        assert result.client_id != GOOGLE_CLIENT_ID

    async def test_the_api_key_branch_routes_through_ApiKeyVerifier(
        self, roster_of_two: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ROUTING IS NOT SHARING. A verifier that re-implements the comparison inline
        # passes every behavioural pin above while carrying its OWN timing behaviour
        # and its own empty-key policy. Break ``ApiKeyVerifier.verify`` and the api-key
        # branch must go dark — that is the proof it is the one implementation.
        from loremaster import auth as auth_module

        monkeypatch.setattr(
            auth_module.ApiKeyVerifier, "verify", lambda _self, _token: None, raising=True
        )
        spy = always_status(401)
        verifier_probe = probe(spy, roster_of_two, api_keys=dict(DEFAULT_API_KEYS))
        assert await verifier_probe.verify(API_KEY_VALUE_LOCAL_AGENT) is None, (
            "with ApiKeyVerifier.verify neutered the api-key branch must be dead; it "
            "still admitted a key, so the branch carries a private copy of the check"
        )

    async def test_an_unknown_key_falls_through_to_the_google_branch(
        self, roster_of_two: Path
    ) -> None:
        # The branch ORDER is contract: api key first, then Google. A token that is not
        # a key must reach Google exactly once.
        spy = always_status(401)
        verifier_probe = probe(spy, roster_of_two, api_keys=dict(DEFAULT_API_KEYS))
        assert await verifier_probe.verify(google_access_token("fallthrough")) is None
        assert spy.call_count == 1


class TestIdentityMinting:
    """F3 at the unit level. ``test_auth_identity_seam`` proves it through the SDK."""

    async def test_the_google_subject_comes_from_the_sub_claim(
        self, roster_of_two: Path
    ) -> None:
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        result = await probe(spy, roster_of_two, api_keys=None).verify(
            google_access_token("sub")
        )
        assert result is not None
        assert result.subject == OPERATOR_SUBJECT

    async def test_the_subject_falls_back_to_the_normalised_email_when_sub_is_absent(
        self, roster_of_two: Path
    ) -> None:
        # Design §4's ruled fallback. The important half is that it is never EMPTY —
        # an empty subject is F3.
        spy = always_json(admitted_payload(email="EJPrice@FireHawkTransAm.ORG", sub=None))
        result = await probe(spy, roster_of_two, api_keys=None).verify(
            google_access_token("nosub")
        )
        assert result is not None
        assert result.subject == OPERATOR_EMAIL

    async def test_two_google_principals_mint_distinct_subjects(
        self, roster_of_two: Path
    ) -> None:
        # THE F3 PIN, stated at its source. odoo-code's port yields identical identity
        # for both of these.
        first_spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        second_spy = always_json(
            admitted_payload(email=SECOND_PRINCIPAL_EMAIL, sub=SECOND_PRINCIPAL_SUBJECT)
        )
        first = await probe(first_spy, roster_of_two, api_keys=None).verify(
            google_access_token("p1")
        )
        second = await probe(second_spy, roster_of_two, api_keys=None).verify(
            google_access_token("p2")
        )
        assert first is not None and second is not None
        assert first.subject != second.subject, (
            "two distinct Google principals produced the SAME subject — the SDK's "
            "session binding degrades to the remaining components and becomes inert"
        )

    async def test_the_issuer_claim_is_the_hardcoded_google_issuer(
        self, roster_of_two: Path
    ) -> None:
        # Design §4: the issuer is HARDCODED, never config (a configurable issuer is a
        # downgrade attack). It is also the second component of the SDK's tuple.
        spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        result = await probe(spy, roster_of_two, api_keys=None).verify(
            google_access_token("iss")
        )
        assert result is not None
        assert result.claims is not None
        assert result.claims["iss"] == GOOGLE_ISSUER

    async def test_the_expiry_is_absolute_and_tracks_the_token_lifetime(
        self, roster_of_two: Path
    ) -> None:
        # THE UNIT PIN. Two lifetimes, so a build that hardcodes a constant TTL (rather
        # than reading Google's) fails: the two derived expiries must DIFFER by the
        # difference in lifetime, not merely both be "in the future".
        short_s = 300
        long_s = GOOGLE_ACCESS_TOKEN_LIFETIME_S
        before = int(time.time())

        short_spy = always_json(
            admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT, lifetime_s=short_s)
        )
        long_spy = always_json(
            admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT, lifetime_s=long_s)
        )
        short_result = await probe(short_spy, roster_of_two, api_keys=None).verify(
            google_access_token("short")
        )
        long_result = await probe(long_spy, roster_of_two, api_keys=None).verify(
            google_access_token("long")
        )
        assert short_result is not None and long_result is not None
        assert short_result.expires_at is not None and long_result.expires_at is not None

        # Independent expectation: the wall clock the test read, plus the lifetime the
        # fixture declared — not a restatement of any implementation formula.
        assert before + short_s <= short_result.expires_at <= before + short_s + 5
        assert before + long_s <= long_result.expires_at <= before + long_s + 5
        assert long_result.expires_at - short_result.expires_at >= long_s - short_s - 5, (
            "the two expiries barely differ — the verifier is inventing a constant TTL "
            "instead of deriving expiry from the tokeninfo response"
        )

    async def test_an_already_expired_token_is_denied(self, roster_of_two: Path) -> None:
        # Google can return 200 for a token whose exp has just passed (clock skew, a
        # cached response). ``expires_at`` in the past means the SDK would refuse it —
        # but the verifier must not mint it in the first place.
        payload = admitted_payload(
            email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT, lifetime_s=-60
        )
        result = await probe(always_json(payload), roster_of_two, api_keys=None).verify(
            google_access_token("expired")
        )
        assert result is None


class TestConcurrencyAndLifecycle:
    """No ``await`` under the lock; a dead client recovers (the lifecycle law)."""

    async def test_two_concurrent_verifications_overlap_their_outbound_calls(
        self, roster_of_two: Path
    ) -> None:
        # THE INSTRUMENTED-LOCK PIN, stated behaviourally so it names no internals: if
        # the cache lock were held across the ``await`` on Google, the two requests
        # would SERIALISE and this gate could never be satisfied. Under a correct
        # build both handlers are in flight together and the gate opens at once.
        first_token = google_access_token("concurrent1")
        second_token = google_access_token("concurrent2")
        both_in_flight = asyncio.Event()
        arrivals = 0

        async def _respond(request: httpx.Request) -> httpx.Response:
            nonlocal arrivals
            arrivals += 1
            if arrivals >= 2:
                both_in_flight.set()
            await asyncio.wait_for(both_in_flight.wait(), timeout=5)
            if first_token.encode() in request.content:
                return httpx.Response(
                    200, json=admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)
                )
            return httpx.Response(
                200,
                json=admitted_payload(
                    email=SECOND_PRINCIPAL_EMAIL, sub=SECOND_PRINCIPAL_SUBJECT
                ),
            )

        spy = TokeninfoSpy(responder=_respond)
        verifier_probe = probe(spy, roster_of_two, api_keys=None)
        results = await asyncio.gather(
            verifier_probe.verify(first_token), verifier_probe.verify(second_token)
        )
        assert all(result is not None for result in results), (
            "concurrent verifications of two different tokens must both complete; a "
            "timeout here means the cache lock is held across the outbound await"
        )

    async def test_a_closed_injected_client_does_not_wedge_the_verifier(
        self, roster_of_two: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # LIFECYCLE (degradation → recovery). The injected client is owned by the
        # process lifespan; a shutdown/restart race can close it under a live request.
        # The verifier must lazily obtain a replacement rather than erroring forever.
        # The replacement is built through ONE named seam so this pin stays HERMETIC —
        # a verifier that constructed a real client here would dial Google from the
        # test suite.
        from loremaster import auth as auth_module

        replacement_spy = always_json(
            admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)
        )
        monkeypatch.setattr(
            auth_module, "_new_http_client", replacement_spy.client, raising=True
        )

        dead_spy = always_json(admitted_payload(email=OPERATOR_EMAIL, sub=OPERATOR_SUBJECT))
        dead_client = dead_spy.client()
        await dead_client.aclose()
        verifier = make_verifier(
            roster_path=roster_of_two, api_keys=None, http_client=dead_client
        )

        result = await verifier.verify_token(google_access_token("afterclose"))
        assert_verification_outcome_is_total(result, roster=ROSTER_OF_TWO_ENTRIES)
        assert result is not None, (
            "a closed injected client must be replaced, not fatal — otherwise one "
            "shutdown race denies every principal until the process restarts"
        )
        assert dead_spy.call_count == 0
        assert replacement_spy.call_count == 1, (
            "the replacement must come from the single _new_http_client seam"
        )

    def test_the_http_client_seam_sets_explicit_timeouts(self) -> None:
        # Design §4: "bounded httpx.Limits, explicit timeout constants". httpx's
        # DEFAULT client would hang a request thread on an unreachable Google for as
        # long as the OS allows — an unauthenticated caller's request holding a worker.
        from loremaster.auth import _new_http_client

        client = _new_http_client()
        try:
            assert client.timeout.connect is not None, "a connect timeout must be set"
            assert client.timeout.read is not None, "a read timeout must be set"
            assert client.timeout.connect <= 30
            assert client.timeout.read <= 30
        finally:
            asyncio.run(client.aclose())
