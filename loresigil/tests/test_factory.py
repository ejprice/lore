"""Contract tests for ``loresigil.factory.make_embedder`` and ``EmbeddingConfig``.

``make_embedder(config)`` is the single seam through which a consumer (lore,
odoo-code) selects a backend by **config only** — never by importing a concrete
embedder. The contract:

* ``backend == "tei"`` -> a :class:`TEIEmbedder` configured from the YAML fields
  (base_url, endpoint, dim, max_input_tokens, max_batch_texts, concurrency), with
  the bearer credential carried on the config as an already-resolved
  ``SecretStr`` (packet 42: ``loresigil`` resolves nothing).
* ``backend == "voyage-cloud"`` -> a :class:`VoyageCloudEmbedder` (api_url, model,
  output_dimension, dim, concurrency), credential likewise.
* Unknown backend -> ``ValueError`` naming the offending backend (fail loud, not a
  silent default).

The blank-credential property (*"no key, no client"*) moved with the resolution:
it is now enforced at the config boundary and lives in
``test_factory_secret_resolution.py::TestAnAbsentCredentialFailsLoudAndNeverBuildsAKeylessEmbedder``.

Construction must NOT touch the network — the factory wires the object; ``probe()``
is the thing that hits the endpoint, and it is not called here.
"""

from __future__ import annotations

from typing import Any

import pytest
from loresigil.base import Embedder
from loresigil.factory import EmbeddingConfig, make_embedder
from loresigil.tei import TEIEmbedder
from loresigil.voyage_cloud import DEFAULT_API_URL as CLOUD_DEFAULT_API_URL
from loresigil.voyage_cloud import DEFAULT_MODEL as CLOUD_DEFAULT_MODEL
from loresigil.voyage_cloud import VoyageCloudEmbedder
from pydantic import SecretStr

TEI_KEY_VALUE: str = "tei-secret-12345"
CLOUD_KEY_VALUE: str = "voyage-secret-67890"

# Mirrors the verified lore.yaml embedding block for the TEI backend.
# ``dict[str, Any]`` (not ``dict[str, object]``): these payloads are unpacked as
# ``**kwargs`` into the typed ``EmbeddingConfig`` model, and ``object`` values do
# not satisfy the model's concrete field types (Literal / str / int) under
# pydantic-mypy's ``init_typed``; ``Any`` is the accurate type for a kwargs map.
TEI_CONFIG_FIELDS: dict[str, Any] = {
    "backend": "tei",
    "base_url": "http://tei.example:8080",
    "endpoint": "/embed",
    "model": "voyageai/voyage-4-nano",
    "dim": 2048,
    "max_input_tokens": 8192,
    "max_batch_texts": 32,
    "concurrency": 2,
    "api_key": SecretStr(TEI_KEY_VALUE),
}

CLOUD_CONFIG_FIELDS: dict[str, Any] = {
    "backend": "voyage-cloud",
    "api_url": "https://api.voyageai.com/v1/embeddings",
    "model": "voyage-4-large",
    "dim": 2048,
    "output_dimension": 2048,
    "concurrency": 4,
    "api_key": SecretStr(CLOUD_KEY_VALUE),
}


class TestFactoryDispatch:
    """``make_embedder`` returns the right concrete class per backend."""

    def test_tei_backend_returns_tei_embedder(self) -> None:
        config = EmbeddingConfig(**TEI_CONFIG_FIELDS)
        embedder = make_embedder(config)
        assert isinstance(embedder, TEIEmbedder)
        assert isinstance(embedder, Embedder)
        # Config flowed through to the model parameters.
        assert embedder.dim == 2048
        assert embedder.max_input_tokens == 8192

    def test_voyage_cloud_backend_returns_cloud_embedder(self) -> None:
        config = EmbeddingConfig(**CLOUD_CONFIG_FIELDS)
        embedder = make_embedder(config)
        assert isinstance(embedder, VoyageCloudEmbedder)
        assert isinstance(embedder, Embedder)
        assert embedder.dim == 2048

    def test_unknown_backend_raises_value_error(self) -> None:
        # A typo'd / unsupported backend must fail loud, not silently default.
        # The invalid literal is the POINT of the test (it must be rejected at
        # runtime), so the static arg-type complaint is deliberately ignored.
        with pytest.raises(ValueError):
            EmbeddingConfig(backend="qdrant-magic", api_key=SecretStr(TEI_KEY_VALUE))  # type: ignore[arg-type]


# ``TestFactoryKeyResolution`` was DELETED by packet 42, not weakened: it pinned
# ``make_embedder`` raising ``MissingApiKeyError`` for an unset ``api_key_env``,
# and both the field and the exception are retired (inventory B1/B6/B8). The
# PROPERTY it protected — a missing or blank credential fails loud and never
# builds a keyless embedder — is re-established one layer earlier, at the config
# boundary, in
# ``test_factory_secret_resolution.py::TestAnAbsentCredentialFailsLoudAndNeverBuildsAKeylessEmbedder``.


class TestFactoryCloudEndpointResolution:
    """No-regression: the cloud arm resolves ITS OWN default endpoint.

    Companion to ``TestFactoryVoyageContextEndpointResolution`` (see
    ``test_factory_voyage_context.py`` for the live bug): whatever mechanism
    GREEN chooses to stop the shared api_url default leaking into the
    voyage-context arm must not disturb the cloud arm's resolution.
    """

    def test_omitted_api_url_targets_cloud_endpoint(self) -> None:
        config_fields = {key: value for key, value in CLOUD_CONFIG_FIELDS.items() if key != "api_url"}
        embedder = make_embedder(EmbeddingConfig(**config_fields))
        assert isinstance(embedder, VoyageCloudEmbedder)
        # Effective URL is currently exposed only as the private ``_api_url``
        # (see the voyage-context companion class note).
        assert embedder._api_url == CLOUD_DEFAULT_API_URL

    def test_explicit_api_url_override_wins(self) -> None:
        override_url = "https://voyage-proxy.internal.example/v1/embeddings"
        embedder = make_embedder(EmbeddingConfig(**{**CLOUD_CONFIG_FIELDS, "api_url": override_url}))
        assert isinstance(embedder, VoyageCloudEmbedder)
        assert embedder._api_url == override_url


class TestFactoryCloudModelResolution:
    """No-regression: the cloud arm resolves ITS OWN model default.

    Companion to ``TestFactoryVoyageContextModelResolution`` — whatever
    mechanism GREEN chooses for per-backend default resolution must leave the
    cloud arm's model untouched.
    """

    def test_omitted_model_targets_cloud_default(self) -> None:
        config_fields = {key: value for key, value in CLOUD_CONFIG_FIELDS.items() if key != "model"}
        embedder = make_embedder(EmbeddingConfig(**config_fields))
        assert isinstance(embedder, VoyageCloudEmbedder)
        assert embedder._model == CLOUD_DEFAULT_MODEL
        # Pin the constant to its documented value (the flat voyage-4 flagship)
        # so the shared source of truth cannot drift silently.
        assert CLOUD_DEFAULT_MODEL == "voyage-4-large"

    def test_explicit_model_override_wins(self) -> None:
        # Realistic override: the smaller sibling model of the same family.
        override_model = "voyage-4"
        embedder = make_embedder(EmbeddingConfig(**{**CLOUD_CONFIG_FIELDS, "model": override_model}))
        assert isinstance(embedder, VoyageCloudEmbedder)
        assert embedder._model == override_model
