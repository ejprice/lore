"""Contract tests for ``loremaster.embedding`` — the thin config→embedder seam.

``loremaster.embedding`` is the THIN translation layer (plan Deliverable 3:
"embedding.py — THIN: config → loresigil.make_embedder(); holds the active
Embedder. No embedding logic here."). It maps a validated
:class:`loremaster.config.EmbeddingConfig` (the ``embedding:`` block of
``lore.yaml``) onto a :class:`loresigil.factory.EmbeddingConfig` and calls
:func:`loresigil.factory.make_embedder`, so the server (and the CLI) construct
the active embedder in ONE place rather than duplicating the field mapping.

The contract these tests pin:

* **Faithful field translation.** Every field the loresigil factory needs —
  ``backend``/``base_url``/``endpoint``/``api_key_env``/``dim``/
  ``max_input_tokens``/``max_batch_texts``/``model``/``concurrency`` — is carried
  across verbatim, so the constructed embedder reports the config's ``dim`` /
  ``max_input_tokens`` (NOT the factory defaults). A dropped or mistranslated
  field is exactly the silent-misconfiguration this layer exists to prevent.
* **Backend dispatch.** A ``tei`` config yields a TEI embedder; the translation
  does not hard-code a backend.
* **Secret indirection preserved.** The API key is read from the env var NAMED by
  ``api_key_env`` — which stays on the LOREMASTER config — and this layer is the
  composition root that resolves it (packet 42 / #222): a missing key fails LOUD
  here, as a ``KeyError`` naming the variable, before any embedder exists.

These run fully offline: ``make_embedder`` does not touch the network at
construction (only ``probe()`` does), so the constructed embedder's reported
properties are asserted without an endpoint.
"""

from __future__ import annotations

import pytest
from loremaster.config import EmbeddingConfig
from loresigil.base import Embedder
from loresigil.tei import TEIEmbedder

# A distinctive, NON-default dim/token cap so a test can prove the values came
# from the config rather than the loresigil factory defaults (2048 / 8192).
_CONFIG_DIM = 1536
_CONFIG_MAX_TOKENS = 4096
_KEY_ENV = "LORE_EMBED_TEST_KEY"


def _embedding_config(api_key_env: str = _KEY_ENV) -> EmbeddingConfig:
    """A valid TEI :class:`EmbeddingConfig` with non-default dim/token cap."""
    return EmbeddingConfig(
        backend="tei",
        base_url="http://embed.example:8080",
        endpoint="/embed",
        model="voyageai/voyage-4-nano",
        dim=_CONFIG_DIM,
        max_input_tokens=_CONFIG_MAX_TOKENS,
        max_batch_texts=16,
        concurrency=3,
        connect_timeout_s=5,
        api_key_env=api_key_env,
        tokenizer="voyage-4-nano",
        truncate=False,
    )


class TestMakeEmbedderFromConfig:
    """``make_embedder_from_config`` translates the config and builds the embedder."""

    def test_returns_an_embedder_for_the_tei_backend(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from loremaster.embedding import make_embedder_from_config

        monkeypatch.setenv(_KEY_ENV, "secret-key")
        embedder = make_embedder_from_config(_embedding_config())
        assert isinstance(embedder, Embedder)
        assert isinstance(embedder, TEIEmbedder)

    def test_carries_dim_and_token_cap_from_config_not_defaults(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The constructed embedder must report the CONFIG's dim/token cap, not the
        # loresigil factory defaults (2048/8192) — proving the fields crossed over.
        from loremaster.embedding import make_embedder_from_config

        monkeypatch.setenv(_KEY_ENV, "secret-key")
        embedder = make_embedder_from_config(_embedding_config())
        assert embedder.dim == _CONFIG_DIM
        assert embedder.max_input_tokens == _CONFIG_MAX_TOKENS

    def test_missing_api_key_env_fails_loud(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The secret is an env-ref; an unset env var must fail loud through this
        # layer, never build a keyless embedder. Packet 42 moved the failure
        # EARLIER — to the translation step — and with it the exception type:
        # ``resolve_secret``'s ``KeyError``, which names the variable, replaces the
        # retired ``loresigil.factory.MissingApiKeyError``.
        from loremaster.embedding import make_embedder_from_config

        monkeypatch.delenv(_KEY_ENV, raising=False)
        with pytest.raises(KeyError) as excinfo:
            make_embedder_from_config(_embedding_config())
        assert _KEY_ENV in str(excinfo.value)
