"""Contract tests for wiring the "voyage-context" backend key through the
loremaster config -> loresigil factory seam (v0.4, feat/contextualized-embedder).

Four things are pinned here:

1. **Config plumbing.** ``loremaster.config.EmbeddingConfig`` (and, through it,
   ``LoreConfig``) accepts ``backend: "voyage-context"`` — today the Literal is
   ``["tei", "voyage-cloud"]`` and rejects it. The hyphenated key mirrors the
   loresigil-level dispatch key (``loresigil/tests/test_factory_voyage_context.py``);
   the underscore near-miss (``"voyage_context"``) stays a rejected typo.
2. **A working embedder gets constructed.** ``make_embedder_from_config`` builds
   a ``VoyageContextEmbedder`` that advertises ``supports_contextualized is
   True``, and the project's configured ``dim`` — the SAME single knob every
   other backend uses (no duplicate ``output_dimension`` field added to
   ``lore.yaml``) — flows through to the constructed embedder's ``.dim``,
   rather than silently falling back to the loresigil factory's own default.
   (Discovery: ``loresigil.factory.make_embedder``'s voyage-context arm reads
   its OWN ``output_dimension`` field, not ``dim``, to build the embedder — so
   the loremaster->loresigil translation must route loremaster's one ``dim``
   field onto loresigil's ``output_dimension``, or the configured dim is
   silently dropped.)
3. **Prompt-name policy — investigated, then pinned for consistency.**
   ``loresigil.factory`` already documents (and implements) prompt names as
   TEI-only: the voyage-cloud dispatch arm accepts ``query_prompt_name`` /
   ``document_prompt_name`` in its config but never forwards them to
   ``VoyageCloudEmbedder`` (whose constructor doesn't even accept them) — a
   silent, deliberate no-op ("Prompt name fields are TEI-only; the cloud call
   is left exactly as-is."). ``VoyageContextEmbedder`` has the identical
   "no prompt-name concept" shape. For CONSISTENCY across the two non-TEI
   backends this pins the SAME silent-ignore for voyage-context, rather than a
   loud rejection that would only apply to the newest sibling.
4. **Fingerprint regression guard.** Switching ``embedding.backend`` (e.g.
   ``tei`` -> ``voyage-context``, same ``dim``) changes
   ``embedding_schema_fingerprint`` — the schema-rebuild trigger this whole
   deploy path depends on to safely re-embed everything on a backend swap.

These run fully offline (construction never touches the network; only
``probe()`` does, and nothing here calls it).
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from loremaster.config import EmbeddingConfig, LoreConfig
from loremaster.embedding import make_embedder_from_config, to_loresigil_config
from loremaster.index.schema import embedding_schema_fingerprint
from loresigil.base import Embedder
from loresigil.factory import MissingApiKeyError
from loresigil.tei import DEFAULT_DIM as _LORESIGIL_FACTORY_DEFAULT_DIM
from loresigil.voyage_context import VoyageContextEmbedder
from pydantic import ValidationError

_CONTEXT_KEY_ENV = "LORE_VOYAGE_CONTEXT_KEY_TEST"
_CONTEXT_KEY_VALUE = "voyage-context-secret-24680"

# A production-realistic voyage-context-4 embedding block. 1024 is a genuinely
# SUPPORTED Matryoshka output_dimension for voyage-context-4 (the documented
# family supports 256/512/1024/2048) and is DELIBERATELY not the loresigil
# factory's own default (imported below, never hardcoded) — a config that
# happened to equal the default would not catch a translation that silently
# drops the configured dim and falls back to it.
_CONTEXT_EMBEDDING_FIELDS: dict[str, Any] = {
    "backend": "voyage-context",
    "base_url": "https://api.voyageai.com/v1/contextualizedembeddings",
    "endpoint": "/v1/contextualizedembeddings",
    "model": "voyage-context-4",
    "dim": 1024,
    "max_input_tokens": 32_000,
    "max_batch_texts": 128,
    "concurrency": 4,
    "connect_timeout_s": 5.0,
    "api_key_env": _CONTEXT_KEY_ENV,
    "tokenizer": "voyage-context-4",
    "truncate": False,
}

# A production-realistic TEI embedding block (mirrors test_config.py's
# canonical shape), used ONLY as the isolation control for the fingerprint
# backend-switch test below.
_BASE_TEI_EMBEDDING_FIELDS: dict[str, Any] = {
    "backend": "tei",
    "base_url": "http://tei.example:8080",
    "endpoint": "/embed",
    "model": "voyageai/voyage-4-nano",
    "dim": 2048,
    "max_input_tokens": 8192,
    "max_batch_texts": 32,
    "concurrency": 2,
    "connect_timeout_s": 5.0,
    "api_key_env": "LORE_TEI_KEY",
    "tokenizer": "voyage-4-nano",
    "truncate": False,
}


def _base_lore_config_payload(
    embedding_fields: dict[str, Any], *, slug: str = "demand_intelligence"
) -> dict[str, Any]:
    """A minimal, valid full ``LoreConfig`` payload carrying ``embedding_fields``."""
    return {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": embedding_fields,
        "include": ["src/**/*.py"],
        "exclude_dirs": [".git", ".venv"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True, "observer": "inotify", "debounce_ms": 1500, "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
    }


@pytest.fixture(autouse=True)
def _set_context_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide the context-backend key for every test; isolate the real env."""
    monkeypatch.setenv(_CONTEXT_KEY_ENV, _CONTEXT_KEY_VALUE)


# --------------------------------------------------------------------------- #
# 1. Config plumbing — backend Literal accepts "voyage-context"
# --------------------------------------------------------------------------- #
class TestEmbeddingConfigAcceptsVoyageContextBackend:
    """``EmbeddingConfig`` / ``LoreConfig`` accept ``backend="voyage-context"``."""

    def test_embedding_config_accepts_voyage_context(self) -> None:
        config = EmbeddingConfig(**_CONTEXT_EMBEDDING_FIELDS)
        assert config.backend == "voyage-context"

    def test_lore_config_accepts_voyage_context_backend(self) -> None:
        payload = _base_lore_config_payload(_CONTEXT_EMBEDDING_FIELDS)
        config = LoreConfig.model_validate(payload)
        assert config.embedding.backend == "voyage-context"
        assert config.embedding.dim == _CONTEXT_EMBEDDING_FIELDS["dim"]

    def test_underscore_lookalike_backend_still_rejected(self) -> None:
        # Consistency guard with the loresigil-level dispatch key (hyphenated,
        # never the underscore near-miss) — adding the arm must not loosen the
        # typed Literal into accepting a lookalike.
        payload = {**_CONTEXT_EMBEDDING_FIELDS, "backend": "voyage_context"}
        with pytest.raises(ValidationError):
            EmbeddingConfig(**payload)

    def test_unrelated_unknown_backend_still_rejected(self) -> None:
        payload = {**_CONTEXT_EMBEDDING_FIELDS, "backend": "openai"}
        with pytest.raises(ValidationError):
            EmbeddingConfig(**payload)


# --------------------------------------------------------------------------- #
# 2. make_embedder_from_config builds a WORKING contextualized embedder
# --------------------------------------------------------------------------- #
class TestMakeEmbedderFromConfigVoyageContextBackend:
    """The translation seam constructs a real, correctly-dimensioned embedder."""

    def test_returns_a_contextualized_capable_voyage_context_embedder(self) -> None:
        config = EmbeddingConfig(**_CONTEXT_EMBEDDING_FIELDS)
        embedder = make_embedder_from_config(config)
        assert isinstance(embedder, Embedder)
        assert isinstance(embedder, VoyageContextEmbedder)
        assert embedder.supports_contextualized is True

    def test_configured_dim_flows_through_not_the_loresigil_default(self) -> None:
        config = EmbeddingConfig(**_CONTEXT_EMBEDDING_FIELDS)
        embedder = make_embedder_from_config(config)
        # Sanity precondition: the fixture's dim must actually differ from the
        # loresigil factory's own default, or a silent-default-fallback bug
        # would be invisible to the assertion below.
        assert _CONTEXT_EMBEDDING_FIELDS["dim"] != _LORESIGIL_FACTORY_DEFAULT_DIM
        assert embedder.dim == _CONTEXT_EMBEDDING_FIELDS["dim"]

    def test_missing_api_key_env_fails_loud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(_CONTEXT_KEY_ENV, raising=False)
        config = EmbeddingConfig(**_CONTEXT_EMBEDDING_FIELDS)
        with pytest.raises(MissingApiKeyError):
            make_embedder_from_config(config)


# --------------------------------------------------------------------------- #
# 3. Prompt-name policy for the context backend (investigated, then pinned)
# --------------------------------------------------------------------------- #
class TestPromptNamePolicyForVoyageContextBackend:
    """Prompt names are TEI-only by established, documented design.

    ``loresigil.factory`` already treats voyage-cloud this way (accepted,
    silently unused — see the factory's own "Prompt name fields are TEI-only;
    the cloud call is left exactly as-is." comment). voyage-context has the
    identical "no prompt-name concept" shape as voyage-cloud, so for
    CONSISTENCY this pins the SAME behaviour rather than a loud rejection that
    would make one non-TEI backend behave differently from its sibling for an
    otherwise-identical config surface.
    """

    def test_prompt_names_configured_with_context_backend_do_not_raise(self) -> None:
        config = EmbeddingConfig(
            **_CONTEXT_EMBEDDING_FIELDS,
            query_prompt_name="query",
            document_prompt_name="document",
        )
        embedder = make_embedder_from_config(config)  # must not raise
        assert embedder.supports_contextualized is True

    def test_prompt_names_still_translate_faithfully_to_the_loresigil_seam(self) -> None:
        # The translation layer stays backend-agnostic — it must not
        # special-case voyage-context by silently DROPPING the fields at THIS
        # seam. Whether the factory then consumes them is that layer's
        # decision (it doesn't, for this backend), not this seam's.
        config = EmbeddingConfig(**_CONTEXT_EMBEDDING_FIELDS, query_prompt_name="query")
        loresigil_config = to_loresigil_config(config)
        assert loresigil_config.query_prompt_name == "query"


# --------------------------------------------------------------------------- #
# 4. Fingerprint regression guard — a backend switch MUST change the fingerprint
# --------------------------------------------------------------------------- #
class TestEmbeddingSchemaFingerprintBackendSwitch:
    """Switching ``embedding.backend`` changes the embedding-schema fingerprint."""

    def test_switching_backend_to_voyage_context_changes_the_fingerprint(self) -> None:
        # Isolation control: hold EVERY OTHER schema-relevant field constant —
        # change ONLY `backend` — so a fingerprint MATCH here could only be
        # explained by the fingerprint function silently ignoring the backend
        # field. (Not a realistic voyage-context config on its own — see
        # _CONTEXT_EMBEDDING_FIELDS above for the realistic one used elsewhere
        # in this file — this is deliberately an isolated single-field diff.)
        shared_fields = dict(_BASE_TEI_EMBEDDING_FIELDS)
        tei_payload = _base_lore_config_payload(shared_fields)
        context_payload = _base_lore_config_payload({**shared_fields, "backend": "voyage-context"})

        tei_config = LoreConfig.model_validate(tei_payload)
        context_config = LoreConfig.model_validate(context_payload)

        fingerprint_tei = embedding_schema_fingerprint(tei_config)
        fingerprint_context = embedding_schema_fingerprint(context_config)

        assert fingerprint_tei != fingerprint_context

    def test_identical_configs_produce_the_same_fingerprint(self) -> None:
        # Positive control for the negative assertion above: proves the
        # fingerprint function is deterministic, so a mismatch there is
        # attributable to the backend field and not to non-determinism.
        payload = _base_lore_config_payload(dict(_BASE_TEI_EMBEDDING_FIELDS))
        config_a = LoreConfig.model_validate(payload)
        config_b = LoreConfig.model_validate(copy.deepcopy(payload))
        assert embedding_schema_fingerprint(config_a) == embedding_schema_fingerprint(config_b)
