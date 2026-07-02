"""Backend-selecting factory: ``make_embedder(config) -> Embedder``.

The single seam through which a consumer (lore, odoo-code) picks an embedding
backend by **config only**, never by importing a concrete embedder class. A swap
is therefore a config edit, not a code change.

* ``backend == "tei"`` → :class:`~loresigil.tei.TEIEmbedder`.
* ``backend == "voyage-cloud"`` → :class:`~loresigil.voyage_cloud.VoyageCloudEmbedder`.
* ``backend == "voyage-context"`` → :class:`~loresigil.voyage_context.VoyageContextEmbedder`
  (the contextualized, document-grouped endpoint).

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
from loresigil.voyage_cloud import DEFAULT_API_URL as CLOUD_DEFAULT_API_URL
from loresigil.voyage_cloud import DEFAULT_CONCURRENCY as CLOUD_DEFAULT_CONCURRENCY
from loresigil.voyage_cloud import DEFAULT_MODEL as CLOUD_DEFAULT_MODEL
from loresigil.voyage_cloud import VoyageCloudEmbedder
from loresigil.voyage_context import DEFAULT_API_URL as CONTEXT_DEFAULT_API_URL
from loresigil.voyage_context import DEFAULT_CONCURRENCY as CONTEXT_DEFAULT_CONCURRENCY
from loresigil.voyage_context import DEFAULT_MODEL as CONTEXT_DEFAULT_MODEL
from loresigil.voyage_context import VoyageContextEmbedder

# Backend discriminators (kept as constants so dispatch and the schema agree).
BACKEND_TEI: str = "tei"
BACKEND_VOYAGE_CLOUD: str = "voyage-cloud"
BACKEND_VOYAGE_CONTEXT: str = "voyage-context"

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

    backend: Literal["tei", "voyage-cloud", "voyage-context"]
    api_key_env: str

    # TEI fields (with verified defaults).
    base_url: str | None = None
    endpoint: str = DEFAULT_ENDPOINT
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS
    max_batch_texts: int = 32

    # Cloud fields (shared by voyage-cloud and voyage-context). None means
    # "unset" — each backend arm resolves its OWN class default (the same
    # pattern concurrency uses below); a shared literal default here would
    # leak one backend's endpoint/model into the other (the odoo15_ctx
    # deploy bug: contextualized payloads posted to the flat endpoint).
    api_url: str | None = None
    output_dimension: int = TEI_DEFAULT_DIM

    # Shared fields.
    model: str | None = None
    dim: int = TEI_DEFAULT_DIM
    concurrency: int | None = None

    # Asymmetric prompt-name fields (TEI only; both default to None so the
    # current no-prompt wire shape is preserved unless explicitly configured).
    query_prompt_name: str | None = None
    document_prompt_name: str | None = None


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
            query_prompt_name=config.query_prompt_name,
            document_prompt_name=config.document_prompt_name,
        )

    if config.backend == BACKEND_VOYAGE_CONTEXT:
        # output_dimension is the single Matryoshka knob for this backend —
        # the embedder's ``dim`` follows it (config.dim is not consulted).
        return VoyageContextEmbedder(
            api_key=api_key,
            api_url=config.api_url or CONTEXT_DEFAULT_API_URL,
            model=config.model or CONTEXT_DEFAULT_MODEL,
            output_dimension=config.output_dimension,
            concurrency=config.concurrency or CONTEXT_DEFAULT_CONCURRENCY,
        )

    # The only remaining Literal value is voyage-cloud.
    # Prompt name fields are TEI-only; the cloud call is left exactly as-is.
    return VoyageCloudEmbedder(
        api_key=api_key,
        api_url=config.api_url or CLOUD_DEFAULT_API_URL,
        model=config.model or CLOUD_DEFAULT_MODEL,
        dim=config.dim,
        output_dimension=config.output_dimension,
        concurrency=config.concurrency or CLOUD_DEFAULT_CONCURRENCY,
    )
