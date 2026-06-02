"""Thin config→embedder seam: ``loremaster.config`` → ``loresigil.make_embedder``.

This is the THIN translation layer the plan calls for (Deliverable 3: "embedding.py
— THIN: config → loresigil.make_embedder(); holds the active Embedder. No
embedding logic here."). It maps loremaster's validated
:class:`~loremaster.config.EmbeddingConfig` (the ``embedding:`` block of
``lore.yaml``) onto loresigil's :class:`~loresigil.factory.EmbeddingConfig` and
delegates to :func:`~loresigil.factory.make_embedder`, so the server lifespan and
the batch-indexer CLI construct the active embedder through ONE call rather than
each duplicating the field mapping (the drift the shared-module discipline
exists to prevent).

There is deliberately NO embedding logic here: backend selection, the resilient
request handling, token counting and the startup probe all live in
``loresigil``. This module only carries the config fields across faithfully —
``dim`` / ``max_input_tokens`` / ``max_batch_texts`` / ``concurrency`` come from
the project config, never from the loresigil factory defaults, so a wrong-dim or
wrong-cap deployment cannot slip through by silently inheriting a default.
"""

from __future__ import annotations

from loresigil.base import Embedder
from loresigil.factory import EmbeddingConfig as LoresigilEmbeddingConfig
from loresigil.factory import make_embedder

from loremaster.config import EmbeddingConfig


def to_loresigil_config(config: EmbeddingConfig) -> LoresigilEmbeddingConfig:
    """Translate a loremaster ``EmbeddingConfig`` into a loresigil one.

    Every field the loresigil factory consumes is carried across verbatim so the
    constructed embedder reports the project config's values (NOT factory
    defaults). Secrets stay indirected: only ``api_key_env`` (the env-var name)
    crosses, never a key value.

    The asymmetric prompt-name fields (``query_prompt_name`` /
    ``document_prompt_name``) are passed through verbatim, including ``None``,
    so the no-prompt default path is preserved byte-identically.

    Args:
        config: The validated loremaster embedding configuration.

    Returns:
        The equivalent loresigil :class:`~loresigil.factory.EmbeddingConfig`.
    """
    return LoresigilEmbeddingConfig(
        backend=config.backend,
        base_url=config.base_url,
        endpoint=config.endpoint,
        api_key_env=config.api_key_env,
        dim=config.dim,
        max_input_tokens=config.max_input_tokens,
        max_batch_texts=config.max_batch_texts,
        model=config.model,
        concurrency=config.concurrency,
        query_prompt_name=config.query_prompt_name,
        document_prompt_name=config.document_prompt_name,
    )


def make_embedder_from_config(config: EmbeddingConfig) -> Embedder:
    """Construct the active :class:`~loresigil.base.Embedder` from project config.

    Translates the config (:func:`to_loresigil_config`) and delegates to
    :func:`loresigil.factory.make_embedder`. Construction does NOT touch the
    network — only :meth:`~loresigil.base.Embedder.probe` reaches the endpoint.

    Args:
        config: The validated loremaster embedding configuration.

    Returns:
        The concrete embedder for the configured backend.

    Raises:
        loresigil.factory.MissingApiKeyError: If the env var named by
            ``api_key_env`` is unset or empty (loud failure, no keyless embedder).
    """
    return make_embedder(to_loresigil_config(config))
