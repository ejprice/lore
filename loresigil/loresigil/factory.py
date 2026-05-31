"""Backend-selecting factory: ``make_embedder(config) -> Embedder``.

The single seam through which a consumer (lore, odoo-code) picks an embedding
backend by **config only**, never by importing a concrete embedder class. A swap
is therefore a config edit, not a code change.

* ``backend == "tei"`` → :class:`~loresigil.tei.TEIEmbedder`.
* ``backend == "voyage-cloud"`` → :class:`~loresigil.voyage_cloud.VoyageCloudEmbedder`.

Secrets are env-refs: the bearer key is read from the environment variable named by
``api_key_env`` (never inlined in the config). A missing/empty key raises
:class:`MissingApiKeyError` — loud failure, no half-built client.
"""

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, ConfigDict

from loresigil.base import Embedder
from loresigil.tei import DEFAULT_DIM as TEI_DEFAULT_DIM
from loresigil.tei import DEFAULT_ENDPOINT, DEFAULT_MAX_INPUT_TOKENS, TEIEmbedder
from loresigil.voyage_cloud import DEFAULT_API_URL, DEFAULT_MODEL, VoyageCloudEmbedder
from loresigil.voyage_cloud import DEFAULT_CONCURRENCY as CLOUD_DEFAULT_CONCURRENCY

# Backend discriminators (kept as constants so dispatch and the schema agree).
BACKEND_TEI: str = "tei"
BACKEND_VOYAGE_CLOUD: str = "voyage-cloud"

_TEI_DEFAULT_CONCURRENCY: int = 2


class MissingApiKeyError(RuntimeError):
    """Raised when the env var named by ``api_key_env`` is unset or empty."""


class EmbeddingConfig(BaseModel):
    """Typed embedding configuration (the ``embedding:`` block of ``lore.yaml``).

    Secrets are never inlined — ``api_key_env`` names the environment variable that
    holds the bearer key. Fields not relevant to the selected backend are ignored
    by that backend's constructor.
    """

    model_config = ConfigDict(extra="forbid")

    backend: Literal["tei", "voyage-cloud"]
    api_key_env: str

    # TEI fields (with verified defaults).
    base_url: str | None = None
    endpoint: str = DEFAULT_ENDPOINT
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS
    max_batch_texts: int = 32

    # Cloud fields.
    api_url: str = DEFAULT_API_URL
    output_dimension: int = TEI_DEFAULT_DIM

    # Shared fields.
    model: str = DEFAULT_MODEL
    dim: int = TEI_DEFAULT_DIM
    concurrency: int | None = None


def _resolve_api_key(api_key_env: str) -> str:
    """Read the bearer key from the named env var, failing loud if unset/empty.

    Args:
        api_key_env: Name of the environment variable holding the key.

    Returns:
        The non-empty key value.

    Raises:
        MissingApiKeyError: If the variable is unset or empty.
    """
    key = os.environ.get(api_key_env)
    if not key:
        raise MissingApiKeyError(
            f"embedding api_key_env {api_key_env!r} is unset or empty in the environment"
        )
    return key


def make_embedder(config: EmbeddingConfig) -> Embedder:
    """Construct the concrete embedder selected by ``config.backend``.

    Construction does not touch the network — only ``probe()`` reaches the endpoint.

    Args:
        config: The embedding configuration.

    Returns:
        A concrete :class:`Embedder` for the selected backend.

    Raises:
        MissingApiKeyError: If the configured ``api_key_env`` is unset or empty.
    """
    api_key = _resolve_api_key(config.api_key_env)

    if config.backend == BACKEND_TEI:
        if config.base_url is None:
            raise ValueError("tei backend requires a base_url")
        return TEIEmbedder(
            base_url=config.base_url,
            api_key=api_key,
            endpoint=config.endpoint,
            dim=config.dim,
            max_input_tokens=config.max_input_tokens,
            concurrency=config.concurrency or _TEI_DEFAULT_CONCURRENCY,
        )

    # The only remaining Literal value is voyage-cloud.
    return VoyageCloudEmbedder(
        api_key=api_key,
        api_url=config.api_url,
        model=config.model,
        dim=config.dim,
        output_dimension=config.output_dimension,
        concurrency=config.concurrency or CLOUD_DEFAULT_CONCURRENCY,
    )
