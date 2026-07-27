"""Backend-selecting factory: ``make_embedder(config) -> Embedder``.

The single seam through which a consumer picks an embedding backend by **config
only**, never by importing a concrete embedder class. A swap is therefore a config
edit, not a code change.

⚠ That sentence used to name *"(lore, odoo-code)"* as the consumers. Verified 2026-07-27
(ruling R36): **odoo-code is a DONOR, not a consumer** — ``batching.py`` and
``voyage_cloud.py`` record code *"ported from the odoo-code donor"*, and no sibling
project imports this package. The distinction is not pedantry: prose naming an external
consumer reads as a compatibility constraint, and this packet reshaped
:class:`EmbeddingConfig` on the strength of there being none.

* ``backend == "tei"`` → :class:`~loresigil.tei.TEIEmbedder`.
* ``backend == "voyage-cloud"`` → :class:`~loresigil.voyage_cloud.VoyageCloudEmbedder`.
* ``backend == "voyage-context"`` → :class:`~loresigil.voyage_context.VoyageContextEmbedder`
  (the contextualized, document-grouped endpoint).

Secrets ARRIVE RESOLVED. ``loresigil`` reads no environment variable and owns no
dotenv workflow (#222, operator ruling 2026-07-26): the consumer's composition root
resolves the credential and hands it over as a :class:`~pydantic.SecretStr`, so there
is exactly one place in a process where a secret enters. A blank credential is
rejected at config construction — loud failure, no half-built client.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

from lorerunes import is_blank
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


class EmbeddingConfig(BaseModel):
    """Typed embedding configuration (the ``embedding:`` block of ``lore.yaml``).

    The credential ARRIVES RESOLVED — the consumer's composition root reads the
    environment and hands over a :class:`SecretStr`. The env-var NAME still belongs
    in the consumer's own config (``loremaster.config.EmbeddingConfig.api_key_env``);
    what changed is that ``loresigil`` no longer reads it. Fields not relevant to the
    selected backend are ignored by that backend's constructor.
    """

    model_config = ConfigDict(extra="forbid")

    backend: Literal["tei", "voyage-cloud", "voyage-context"]
    #: The bearer credential, ALREADY RESOLVED by the caller. ``SecretStr`` is the
    #: protection rather than a convention — the value cannot render through a
    #: ``repr``, an f-string or a traceback frame, only through the deliberate unwrap
    #: at the client seam (:func:`loresigil.voyage_http.build_auth_headers`).
    api_key: SecretStr

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

    @field_validator("api_key")
    @classmethod
    def _reject_a_blank_credential(cls, credential: SecretStr) -> SecretStr:
        """Reject a credential that is empty or nothing but whitespace.

        This preserves the deleted ``_resolve_api_key``'s virtue — *a missing or
        empty key fails loud and never builds a keyless embedder* — at the boundary
        the value now enters through. It fires strictly EARLIER than the old check,
        which ran at ``make_embedder()`` time, and it covers every construction path
        rather than only the consumer's translator: ``scripts/search_score_survey.py``
        builds this model directly.

        ⚠ **``lorerunes.is_blank`` is called, never re-implemented (ruling R29).**
        ``loremaster.config.resolve_secret`` asks the same question at the
        composition root, and two copies of "what counts as blank" are two answers
        that can drift. A ``Field(min_length=1)`` was measured and rejected for this:
        it constrains LENGTH, so a single space (length 1) is accepted.

        The old resolver ACCEPTED a whitespace-only value (inventory B3). That was a
        bug, and it is deliberately not preserved.

        Args:
            credential: The candidate credential, already wrapped.

        Returns:
            The credential, unchanged and byte-exact — a key whose real bytes carry
            leading or trailing whitespace is NOT blank and must survive intact.

        Raises:
            ValueError: If the credential carries no real content. pydantic renders
                it as a ``ValidationError`` located at ``api_key``.
        """
        if is_blank(credential.get_secret_value()):
            raise ValueError(
                "api_key is empty or whitespace-only; the composition root must resolve a "
                "real credential before building an embedding config"
            )
        return credential


def make_embedder(config: EmbeddingConfig) -> Embedder:
    """Construct the concrete embedder selected by ``config.backend``.

    Construction does not touch the network — only ``probe()`` reaches the endpoint.

    Args:
        config: The embedding configuration, carrying an already-resolved credential.

    Returns:
        A concrete :class:`Embedder` for the selected backend.
    """
    api_key = config.api_key

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
