"""Core data models for lorescribe.

These pydantic models define the data shapes every concrete chunker emits and
that the downstream consumer (loremaster) relies on for deterministic point-ID
derivation. The model layer is where the load-bearing invariants live:

* A :class:`Chunk` always carries a non-empty, non-whitespace ``identity`` and a
  ``sub_ordinal``; together with ``(slug, file_path, chunk_type, key_version)``
  these form the natural key loremaster turns into a deterministic point-ID.
* ``embedding_text`` is the exact byte-for-byte string handed to the embedder.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

# Default ordinal for a chunk that is the sole piece of its identity. Sibling
# chunks split from the same identity increment from this base.
DEFAULT_SUB_ORDINAL: int = 0

# Default header: the empty string means "no breadcrumb context to prepend".
DEFAULT_METADATA_HEADER: str = ""

# Separator joining a non-empty ``metadata_header`` to its ``source_text`` when
# composing ``embedding_text`` — a single newline, pinned by the embedder spec.
EMBEDDING_TEXT_SEPARATOR: str = "\n"


class Chunk(BaseModel):
    """A single embeddable unit split out of a source document.

    Every chunk is the atomic record that flows from a chunker into the vector
    store. Its ``identity`` and ``sub_ordinal`` form the within-file natural key
    that loremaster combines with ``(slug, file_path, chunk_type, key_version)``
    to derive a deterministic, collision-free point-ID.

    Attributes:
        chunk_type: The chunker's category for this chunk (e.g.
            ``"markdown_section"``, ``"python_symbol"``). Routed downstream.
        source_text: The raw text content split from the document.
        identity: The within-file natural key (heading slug, function qualname,
            table name, ...). Required, and must be non-empty and not
            whitespace-only — a blank identity would collapse sibling chunks'
            point-IDs downstream.
        sub_ordinal: Disambiguates sibling chunks that share an ``identity``
            (e.g. one heading split into N pieces). Defaults to ``0``.
        line_start: First source line (1-based) this chunk covers.
        line_end: Last source line (1-based) this chunk covers.
        metadata: Arbitrary chunker-attached metadata (heading path, language,
            token counts, ...). Defaults to a fresh empty dict per instance.
        metadata_header: A human-readable breadcrumb prepended to
            ``source_text`` when forming ``embedding_text``. Defaults to ``""``.
    """

    # Forbid unknown kwargs: a typo'd field name (e.g. ``metadata_headr``) must
    # fail loudly rather than be silently dropped, which would derive a
    # point-ID from partial data with no signal.
    model_config = ConfigDict(extra="forbid")

    chunk_type: str
    source_text: str
    identity: str
    sub_ordinal: int = DEFAULT_SUB_ORDINAL
    line_start: int
    line_end: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    metadata_header: str = DEFAULT_METADATA_HEADER

    @field_validator("identity")
    @classmethod
    def _identity_must_be_non_blank(cls, value: str) -> str:
        """Reject a blank ``identity`` and store the surrounding-whitespace-trimmed form.

        A blank natural key would collapse sibling chunks' deterministic
        point-IDs downstream, so an empty or whitespace-only value is rejected
        at the model boundary. Otherwise the stripped value is stored so that
        ``"  payroll  "`` and ``"payroll"`` derive the SAME point-ID — stray
        surrounding whitespace (a trailing newline in a heading slug, an
        indented YAML scalar) must not produce a distinct natural key.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("identity must be non-empty and not whitespace-only")
        return stripped

    @computed_field  # type: ignore[prop-decorator]
    @property
    def embedding_text(self) -> str:
        """Compose the exact string handed to the embedder.

        Contract (pinned to the byte):

        * When ``metadata_header`` is non-empty:
          ``f"{metadata_header}\\n{source_text}"`` — header, a single newline,
          then the source text.
        * When ``metadata_header`` is empty: exactly ``source_text``, with NO
          leading newline.

        Returns:
            The header-plus-source composition described above.
        """
        # An empty header means "no breadcrumb": return the bare source so no
        # spurious leading newline is introduced.
        if not self.metadata_header:
            return self.source_text
        return f"{self.metadata_header}{EMBEDDING_TEXT_SEPARATOR}{self.source_text}"


class ChunkContext(BaseModel):
    """Per-file context the framework injects into every ``chunk`` call.

    Carries the project slug, the on-disk file path, the embedder's token
    counter, and the embedder's hard input-token cap. The token counter is a
    genuine callable supplied by the consumer (embedder side); chunkers call
    through it to size their output, and gate on ``max_input_tokens`` so every
    emitted chunk stays embeddable.

    Attributes:
        slug: The project identifier the file belongs to.
        file_path: The on-disk path of the file being chunked.
        count_tokens: The embedder's injected token counter, ``str -> int``.
        max_input_tokens: The embedder's hard token cap. Over-length inputs are
            rejected (HTTP 422), never silently truncated, so chunkers must
            keep every chunk at or below this count.
    """

    # ``arbitrary_types_allowed`` so the injected ``count_tokens`` callable is
    # accepted; ``extra="forbid"`` so a typo'd kwarg fails loudly.
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    slug: str
    file_path: str
    count_tokens: Callable[[str], int]
    max_input_tokens: int


class ProfileResult(BaseModel):
    """Return shape of the XML ``SchemaProfile`` hook.

    A profile inspects a document and decides how it should be chunked: which
    ``chunk_type`` to stamp, what extra metadata to carry, and whether the
    document should be skipped entirely.

    Attributes:
        chunk_type: The chunk category the profile selected for the document.
        extra_metadata: Additional metadata the profile derived (schema name,
            root element, ...) to attach to emitted chunks.
        skip: When ``True``, the document should be skipped entirely. Defaults
            to ``False``.
        force_own_chunk: Granularity control. When ``True``, an element the
            profile claims is emitted as ITS OWN chunk regardless of the XML
            chunker's size-tier decision — so a profile-significant element in a
            small file (which would otherwise collapse into the single
            whole-file chunk) becomes a standalone chunk. Defaults to ``False``,
            leaving the size-tiered behaviour untouched for elements that do not
            opt in.
    """

    # Forbid unknown kwargs so a typo in a profile's return shape fails loudly.
    model_config = ConfigDict(extra="forbid")

    chunk_type: str
    extra_metadata: dict[str, Any]
    skip: bool = False
    force_own_chunk: bool = False
