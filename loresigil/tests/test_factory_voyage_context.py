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
