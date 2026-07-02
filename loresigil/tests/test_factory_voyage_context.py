"""Contract tests for the ``voyage_context`` backend key in ``make_embedder``.

v0.4 adds one dispatch arm to the config-only backend seam:

* ``backend == "voyage-context"`` -> a :class:`VoyageContextEmbedder` built from
  the config (api_url, model, output_dimension, concurrency), with the bearer
  key resolved from the env var named by ``api_key_env`` — secrets are env-refs,
  NEVER inline, and a missing/empty variable is a loud
  :class:`~loresigil.factory.MissingApiKeyError` at construction.
* The embedder's ``dim`` follows ``output_dimension`` (the single Matryoshka
  knob for this backend).
* Unknown-backend behaviour is UNCHANGED: a typo'd key is still rejected by the
  typed config, never silently defaulted.

Construction must NOT touch the network — the factory wires the object;
``probe()`` is the thing that hits the endpoint, and it is not called here.

Key naming (operator decision, 2026-07-01): the dispatch key is
``"voyage-context"`` — hyphenated, consistent with ``"voyage-cloud"``. The
underscore lookalike ``"voyage_context"`` is a rejected near-miss.
"""

from __future__ import annotations

from typing import Any

import pytest
from loresigil.base import Embedder
from loresigil.factory import EmbeddingConfig, MissingApiKeyError, make_embedder
from loresigil.voyage_context import DEFAULT_API_URL as CONTEXT_DEFAULT_API_URL
from loresigil.voyage_context import DEFAULT_DIM as CONTEXT_DEFAULT_DIM
from loresigil.voyage_context import DEFAULT_MAX_INPUT_TOKENS as CONTEXT_DEFAULT_MAX_INPUT_TOKENS
from loresigil.voyage_context import DEFAULT_MODEL as CONTEXT_DEFAULT_MODEL
from loresigil.voyage_context import VoyageContextEmbedder

CONTEXT_KEY_ENV: str = "LORE_VOYAGE_CONTEXT_KEY_TEST"
CONTEXT_KEY_VALUE: str = "voyage-context-secret-13579"

# Mirrors a realistic lore.yaml embedding block for the contextualized backend
# (S8-verified endpoint/model; 2048 is the model's default output dimension).
# ``dict[str, Any]``: unpacked as **kwargs into the typed EmbeddingConfig —
# same precedent as test_factory.py.
CONTEXT_CONFIG_FIELDS: dict[str, Any] = {
    "backend": "voyage-context",
    "api_url": "https://api.voyageai.com/v1/contextualizedembeddings",
    "model": "voyage-context-4",
    "dim": 2048,
    "output_dimension": 2048,
    "concurrency": 4,
    "api_key_env": CONTEXT_KEY_ENV,
}


@pytest.fixture(autouse=True)
def _set_context_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide the context-backend key for every test; isolate the real env."""
    monkeypatch.setenv(CONTEXT_KEY_ENV, CONTEXT_KEY_VALUE)


class TestFactoryVoyageContextDispatch:
    """``backend == "voyage-context"`` constructs a VoyageContextEmbedder."""

    def test_voyage_context_backend_returns_context_embedder(self) -> None:
        config = EmbeddingConfig(**CONTEXT_CONFIG_FIELDS)
        embedder = make_embedder(config)
        assert isinstance(embedder, VoyageContextEmbedder)
        assert isinstance(embedder, Embedder)

    def test_config_output_dimension_flows_to_dim(self) -> None:
        config = EmbeddingConfig(**CONTEXT_CONFIG_FIELDS)
        embedder = make_embedder(config)
        # dim follows the configured output_dimension — the single knob.
        assert embedder.dim == CONTEXT_CONFIG_FIELDS["output_dimension"]

    def test_factory_product_advertises_contextualized_capability(self) -> None:
        # Downstream consumers feature-detect through the factory product, so
        # the capability flag must survive the config-only seam.
        config = EmbeddingConfig(**CONTEXT_CONFIG_FIELDS)
        embedder = make_embedder(config)
        assert embedder.supports_contextualized is True

    def test_underscore_lookalike_backend_rejected(self) -> None:
        # Guard: adding the new arm must not loosen the typed dispatch — the
        # underscore lookalike of the canonical hyphenated key is a loud
        # rejection, never a silent alias.
        with pytest.raises(ValueError):
            EmbeddingConfig(backend="voyage_context", api_key_env=CONTEXT_KEY_ENV)  # type: ignore[arg-type]

    def test_unrelated_unknown_backend_still_rejected(self) -> None:
        # The pre-existing unknown-key behaviour is unchanged by the new arm.
        with pytest.raises(ValueError):
            EmbeddingConfig(backend="qdrant-magic", api_key_env=CONTEXT_KEY_ENV)  # type: ignore[arg-type]


class TestFactoryVoyageContextEndpointResolution:
    """A factory-built context embedder must target the CONTEXTUALIZED endpoint.

    Live-deployment bug (Odoo A/B eval arm, 2026-07): the shared config
    field's cloud default (``/v1/embeddings``) leaked through the factory into
    the voyage-context arm, so contextualized payloads 400ed against the flat
    endpoint. These pins assert the OBSERVABLE effective URL; the resolution
    mechanism (e.g. an unset-able shared field with per-backend class-default
    fallback) is GREEN's choice. NOTE: the effective URL is currently exposed
    only as the private ``_api_url`` (the exact seam the live traceback showed
    posting) — if a public accessor lands, migrate these pins to it.
    """

    def test_omitted_api_url_targets_contextualized_endpoint(self) -> None:
        # A realistic minimal lore.yaml block: no api_url key at all.
        config_fields = {key: value for key, value in CONTEXT_CONFIG_FIELDS.items() if key != "api_url"}
        embedder = make_embedder(EmbeddingConfig(**config_fields))
        assert isinstance(embedder, VoyageContextEmbedder)
        # The backend's OWN default (the S8-verified contextualized endpoint),
        # never the sibling cloud arm's flat-embeddings URL.
        assert embedder._api_url == CONTEXT_DEFAULT_API_URL

    def test_explicit_api_url_override_wins(self) -> None:
        # The operator override path (e.g. an egress proxy) must still win.
        override_url = "https://voyage-proxy.internal.example/v1/contextualizedembeddings"
        config_fields = {**CONTEXT_CONFIG_FIELDS, "api_url": override_url}
        embedder = make_embedder(EmbeddingConfig(**config_fields))
        assert isinstance(embedder, VoyageContextEmbedder)
        assert embedder._api_url == override_url


class TestFactoryVoyageContextModelResolution:
    """A factory-built context embedder must resolve ITS OWN model default.

    Same cross-backend default leak as api_url (audited 2026-07-02): the
    shared config field's default is imported from voyage_cloud
    ("voyage-4-large") and passed to the context arm — a config omitting
    ``model`` would post a flat-embeddings model name to the contextualized
    endpoint. Observables: the private ``_model`` (drives the request body,
    same style as the accepted ``_api_url`` pins) corroborated by the PUBLIC
    ``name`` property (pinned elsewhere to contain the model verbatim).
    """

    def test_omitted_model_targets_context_default(self) -> None:
        config_fields = {key: value for key, value in CONTEXT_CONFIG_FIELDS.items() if key != "model"}
        embedder = make_embedder(EmbeddingConfig(**config_fields))
        assert isinstance(embedder, VoyageContextEmbedder)
        # The backend's OWN model ("voyage-context-4", spec-pinned in
        # test_voyage_context), never the cloud sibling's default.
        assert embedder._model == CONTEXT_DEFAULT_MODEL
        assert CONTEXT_DEFAULT_MODEL in embedder.name  # public corroboration

    def test_explicit_model_override_wins(self) -> None:
        # The operator override path (e.g. pinning a newer model snapshot).
        override_model = "voyage-context-4-lite"
        config_fields = {**CONTEXT_CONFIG_FIELDS, "model": override_model}
        embedder = make_embedder(EmbeddingConfig(**config_fields))
        assert isinstance(embedder, VoyageContextEmbedder)
        assert embedder._model == override_model


class TestFactoryVoyageContextSharedDefaultGuards:
    """Green guards from the shared-field audit: leaks that are HARMLESS today
    stay harmless.

    ``output_dimension`` (config default 2048) coincidentally equals the
    context backend's own default, and ``max_input_tokens`` (TEI's 8192) is
    simply not wired into the context arm. Neither is a live bug — these pins
    exist so a future "helpful" rewiring or a default divergence cannot leak
    silently the way api_url/model did.
    """

    def test_omitted_output_dimension_resolves_context_default(self) -> None:
        config_fields = {
            key: value for key, value in CONTEXT_CONFIG_FIELDS.items() if key != "output_dimension"
        }
        embedder = make_embedder(EmbeddingConfig(**config_fields))
        assert isinstance(embedder, VoyageContextEmbedder)
        # Public dim property — must stay the backend's own default even if
        # the shared config default ever diverges from 2048.
        assert embedder.dim == CONTEXT_DEFAULT_DIM

    def test_tei_token_cap_never_leaks_into_context_arm(self) -> None:
        # config.max_input_tokens defaults to TEI's 8192; wiring it into the
        # context arm would spuriously fail every 8k-32k-token document. The
        # context embedder must keep its own 32k doc window.
        embedder = make_embedder(EmbeddingConfig(**CONTEXT_CONFIG_FIELDS))
        assert isinstance(embedder, VoyageContextEmbedder)
        assert embedder.max_input_tokens == CONTEXT_DEFAULT_MAX_INPUT_TOKENS


class TestFactoryVoyageContextKeyResolution:
    """The bearer key is an env-ref; missing or empty fails loud at construction."""

    def test_missing_env_var_raises_naming_the_variable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DEFINITELY_UNSET_CONTEXT_KEY_ENV", raising=False)
        config_fields = {**CONTEXT_CONFIG_FIELDS, "api_key_env": "DEFINITELY_UNSET_CONTEXT_KEY_ENV"}
        config = EmbeddingConfig(**config_fields)
        # Pinned to the SPECIFIC failure (missing key), not "any exception" —
        # otherwise a stub's NotImplementedError would pass this.
        with pytest.raises(MissingApiKeyError) as exc_info:
            make_embedder(config)
        # The error names the offending env var so the operator can fix it.
        assert "DEFINITELY_UNSET_CONTEXT_KEY_ENV" in str(exc_info.value)

    def test_empty_env_var_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # An empty string is as useless as an unset variable — same loud failure
        # (an ``export KEY=`` typo must not build a client with a blank bearer).
        monkeypatch.setenv(CONTEXT_KEY_ENV, "")
        config = EmbeddingConfig(**CONTEXT_CONFIG_FIELDS)
        with pytest.raises(MissingApiKeyError):
            make_embedder(config)
