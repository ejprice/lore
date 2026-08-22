"""CONTRACT (contract-39-w23) — the packet-39 RE-CUT config surface (design §6 / §13 g6).

Pins the recut ``OAuthProviderConfig`` + the amended ``AuthConfig`` fail-closed validation.
This is the RE-PIN of the deleted ``GoogleOAuthConfig`` config-validation virtues the cold
audit routed as **R2** (``REPORT-cold-audit-39-w1.md`` §Verdict / row R2) and the
``TestGoogleOAuthConfigFailsClosed`` virtues finding **#395** tracks as wave-3's deferred
config obligation: *"blank client_id fails closed; non-https base_url refused"*.

⚠ SCOPE. This file pins the CONFIG-LAYER (pydantic) validation ONLY — pure, no wire, no store.
The POSTURE-coherence checks (an ``oauth`` block required for ``mode == "hosted_oauth"``; an
email scope required in ``required_scopes``; ``HOSTED_OAUTH`` requires a loopback host) live in
``lorerunes``'s ``derive_posture`` and are pinned in ``lorerunes/tests/test_posture.py``
(design §6). The removed ``tls_terminated_upstream`` flag's retirement pins live in
``test_auth.py`` beside the kept-surface control (finding #395). The composition that HANDS this
config to ``FastMCP(auth=…)`` is ``test_auth_composition_recut.py``.

⚠ ESC-2 (design fork, contract-author recommendation A — see ``REPORT-contract-39-w23.md``):
lore is a RESOURCE SERVER whose hand-rolled tokeninfo verification (#393) needs NO
``client_secret`` (it validates a token with only the presented ``access_token`` + the ``aud``
check). So ``OAuthProviderConfig`` carries NO ``client_secret`` field, and ``extra="forbid"``
REFUSES an inline ``client_secret`` by construction — the strongest "never inline / never
logged". If the operator rules reading B (a ``client_secret_env`` field), ONE pin flips
(``test_client_secret_cannot_be_inlined`` becomes a holds-a-name-not-a-secret pin).

CONTRACT-FIRST: every pin fails BEHAVIOURALLY against the config stub (the fields exist so the
import resolves; the validators the pins demand are absent, so a ``pytest.raises`` that should
fire does not) — never on an ImportError. The satisfiability receipt (0-failed on a correct
build) comes from the contract-adversary's reference build (design §13).
"""

from __future__ import annotations

import pytest
from _auth_fixtures import (
    GOOGLE_CLIENT_ID,
    GOOGLE_EMAIL_SCOPE_URI,
    RESOURCE_SERVER_URL,
)
from loremaster.config import AuthConfig, OAuthProviderConfig
from pydantic import ValidationError

# A well-formed required-scopes grant carrying an email scope (the value production configures —
# an email scope MUST be present or admission has no verified email to key on, design §4.1).
_VALID_SCOPES = [GOOGLE_EMAIL_SCOPE_URI, "openid"]


def _valid_oauth() -> OAuthProviderConfig:
    """A constructible OAuthProviderConfig — the positive control for every reject pin."""
    return OAuthProviderConfig(
        kind="google", client_id=GOOGLE_CLIENT_ID, required_scopes=list(_VALID_SCOPES)
    )


class TestOAuthProviderConfigFailsClosed:
    """R2 — the deleted ``GoogleOAuthConfig`` fail-closed virtues, re-pinned on the recut model.

    Each reject pin is paired with the positive control (:func:`_valid_oauth`) so "fails closed"
    is a genuine negative, never a model that refuses everything.
    """

    def test_a_wellformed_provider_block_constructs(self) -> None:
        # POSITIVE CONTROL — a valid block MUST construct, or every reject pin below is vacuous.
        provider = _valid_oauth()
        assert provider.kind == "google"
        assert provider.client_id == GOOGLE_CLIENT_ID
        assert GOOGLE_EMAIL_SCOPE_URI in provider.required_scopes

    def test_blank_client_id_is_refused(self) -> None:
        # R2 BLOCKER: a blank client_id is fail-OPEN — every token's ``aud`` would be compared
        # against ``""``. WRONG BUILD THIS CATCHES: an ``OAuthProviderConfig`` with ``client_id:
        # str`` and no non-blank validator (constructs an empty client_id).
        with pytest.raises(ValidationError):
            OAuthProviderConfig(kind="google", client_id="", required_scopes=list(_VALID_SCOPES))

    def test_whitespace_only_client_id_is_refused(self) -> None:
        # The DISCRIMINATOR that a bare truthiness guard (``if not client_id``) does NOT satisfy:
        # a single space has length 1, so ``not "   "`` is False and a truthiness check ADMITS it.
        # The builder must route blankness through ``lorerunes.is_blank`` (the ONE blankness rule),
        # exactly as ``resolve_secret`` does — so "configured to whitespace" is "not configured".
        with pytest.raises(ValidationError):
            OAuthProviderConfig(
                kind="google", client_id="   ", required_scopes=list(_VALID_SCOPES)
            )

    def test_client_secret_cannot_be_inlined(self) -> None:
        # ESC-2 reading A: lore holds NO client_secret (resource-server tokeninfo needs none), so
        # the field does not exist and ``extra="forbid"`` refuses an inline ``client_secret`` by
        # construction — the strongest "never inline". WRONG BUILD THIS CATCHES: a build that
        # added a ``client_secret`` field (reading B) and thereby lets a raw secret be inlined
        # into ``lore.yaml``. (If the operator rules B, this flips to a holds-a-name pin.)
        with pytest.raises(ValidationError):
            OAuthProviderConfig(
                kind="google",
                client_id=GOOGLE_CLIENT_ID,
                required_scopes=list(_VALID_SCOPES),
                client_secret="super-secret-should-be-rejected",  # type: ignore[call-arg]
            )

    def test_an_unknown_provider_key_is_refused(self) -> None:
        # extra="forbid" CONTROL — proves the client_secret refusal above is the strict-model
        # behaviour (a typo'd/stale key fails loud), not a one-off special-case. A DIFFERENT
        # unknown key than client_secret, so the two pins cannot both pass on one narrow guard.
        with pytest.raises(ValidationError):
            OAuthProviderConfig(
                kind="google",
                client_id=GOOGLE_CLIENT_ID,
                required_scopes=list(_VALID_SCOPES),
                issuer_url="https://accounts.google.com",  # type: ignore[call-arg]
            )

    def test_provider_kind_is_a_closed_domain(self) -> None:
        # ``kind`` is the extend-at-provider-#2 seam (design §3.6/§5), a ``Literal["google"]``,
        # NOT a free ``str``. WRONG BUILD THIS CATCHES: ``kind: str`` — which would silently
        # accept ``"azure"`` today, before the Azure verifier branch exists (a dead posture).
        with pytest.raises(ValidationError):
            OAuthProviderConfig(
                kind="azure",  # type: ignore[arg-type]
                client_id=GOOGLE_CLIENT_ID,
                required_scopes=list(_VALID_SCOPES),
            )


class TestAuthConfigBaseUrlIsHttpsOnly:
    """R2 — ``base_url`` (the advertised public resource URL) is https-only.

    The RFC 9728 protected-resource metadata advertises this URL to claude.ai; a plaintext
    ``http://`` (or any non-TLS scheme) endpoint is a downgradeable resource, so it is refused
    at config load — loud and remediable — rather than silently advertised.
    """

    def _hosted(self, *, base_url: str | None) -> AuthConfig:
        return AuthConfig(
            enabled=True, mode="hosted_oauth", oauth=_valid_oauth(), base_url=base_url
        )

    def test_https_base_url_is_accepted(self) -> None:
        # POSITIVE CONTROL — the real public resource URL constructs.
        config = self._hosted(base_url=RESOURCE_SERVER_URL)
        assert config.base_url == RESOURCE_SERVER_URL

    def test_http_base_url_is_refused(self) -> None:
        # R2: a plaintext resource URL is refused. WRONG BUILD: no scheme validator on base_url.
        with pytest.raises(ValidationError):
            self._hosted(base_url="http://lore.firehawktransam.org/mcp")

    def test_a_non_https_scheme_base_url_is_refused(self) -> None:
        # The DISCRIMINATOR that a ``not startswith("http://")`` guard does NOT satisfy: a
        # ``ws://`` (or ``ftp://``) URL is not http:// yet is still non-TLS. The builder must
        # POSITIVELY require the https scheme, never merely exclude http.
        with pytest.raises(ValidationError):
            self._hosted(base_url="ws://lore.firehawktransam.org/mcp")

    def test_a_non_url_base_url_is_refused(self) -> None:
        # A value with no scheme at all ("lore.firehawktransam.org/mcp") is not a usable resource
        # URL — refused, not silently advertised as-is.
        with pytest.raises(ValidationError):
            self._hosted(base_url="lore.firehawktransam.org/mcp")


class TestAuthConfigRecutFieldsAreBackwardCompatible:
    """The recut ADDS optional fields — an existing api-key ``lore.yaml`` still validates.

    The DUAL law (a rewrite must not silently drop the OLD world's virtues): the LAN api-key
    deploy that ships TODAY carries only ``enabled`` + ``keys`` (no ``mode``/``oauth``/
    ``base_url``). It must keep validating, defaulting to the api-key branch.
    """

    def test_a_bare_api_key_auth_block_still_validates(self) -> None:
        from loremaster.config import AuthKey  # noqa: PLC0415

        config = AuthConfig(
            enabled=True, keys=[AuthKey(name="local-agent", key_env="LORE_KEY_LOCAL_AGENT")]
        )
        # mode defaults to the api-key branch; the hosted fields default off.
        assert config.mode == "api_key"
        assert config.oauth is None
        assert config.base_url is None
        assert config.allowed_origins == []

    def test_mode_is_a_closed_domain(self) -> None:
        # ``mode`` is ``Literal["api_key", "hosted_oauth"]`` — the STALE 2026-07-31 value
        # ``"google_oauth"`` (still emitted by ``_auth_fixtures.hosted_auth_block`` until the
        # harness recut) is NOT a legal recut mode. WRONG BUILD: ``mode: str``.
        with pytest.raises(ValidationError):
            AuthConfig(enabled=True, mode="google_oauth")  # type: ignore[arg-type]

    def test_allowed_origins_carries_the_configured_extra_origins(self) -> None:
        # ``allowed_origins`` feeds OriginValidationMiddleware (design §6/§8). A hosted deploy
        # adds claude.ai; the field must round-trip the list, not drop it.
        config = AuthConfig(
            enabled=True,
            mode="hosted_oauth",
            oauth=_valid_oauth(),
            base_url=RESOURCE_SERVER_URL,
            allowed_origins=["https://claude.ai", "https://claude.com"],
        )
        assert config.allowed_origins == ["https://claude.ai", "https://claude.com"]
