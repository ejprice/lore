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

# ``resolve_secret`` is imported into THIS module's namespace (not called through
# ``config.resolve_secret``) so the composition-root translation below binds the
# shared resolver at ``embedding.resolve_secret`` — the one attribute a caller,
# or a mutation pin, can substitute to prove the routing is real.
from loremaster.config import EmbeddingConfig, resolve_secret


def to_loresigil_config(config: EmbeddingConfig) -> LoresigilEmbeddingConfig:
    """Translate a loremaster ``EmbeddingConfig`` into a loresigil one.

    Every field the loresigil factory consumes is carried across verbatim so the
    constructed embedder reports the project config's values (NOT factory
    defaults). Secrets stay indirected: only ``api_key_env`` (the env-var name)
    crosses, never a key value.

    Loremaster exposes a SINGLE ``dim`` knob regardless of backend (no
    duplicate ``output_dimension`` key on ``lore.yaml``). The loresigil factory,
    however, reads ``dim`` for the TEI arm but ``output_dimension`` for the
    voyage-cloud/voyage-context arms (the Matryoshka knob) — so ``config.dim``
    is routed onto BOTH loresigil fields here, backend-agnostically, rather
    than only the one today's TEI-only deploys happen to need. Omitting
    ``output_dimension`` would silently fall back to the loresigil factory's
    own default and drop the configured dim for any non-TEI backend.

    The asymmetric prompt-name fields (``query_prompt_name`` /
    ``document_prompt_name``) are passed through verbatim, including ``None``,
    so the no-prompt default path is preserved byte-identically. This layer
    stays backend-agnostic: whether a given backend's constructor actually
    consumes them is that backend's decision, not this translation seam's.

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
        output_dimension=config.dim,
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
