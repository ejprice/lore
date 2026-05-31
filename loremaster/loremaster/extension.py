"""The extension-framework composition contract (plan AMENDMENT 1, §A1.3/§A1.10).

This module defines the *contract* by which a domain-specific MCP (e.g. a future
``odoo-code``) plugs into ``loremaster`` as a thin extension. It is the
composition surface only — there is NO FastMCP serving and NO auth enforcement
here (those are the later ``server`` build). The deliberate consequence: a bare
:class:`~loremaster.server.LoreServer` with *zero* extensions registered behaves
as the generic code/docs RAG, because every seam below ships a safe, inert
default.

The surface:

* :class:`ExtensionContext` — the shared-services bundle handed to every
  context-taking seam (``store``, ``embedder``, ``config``, ``count_tokens``, and
  ``manifest``), plus a mutable :attr:`~ExtensionContext.state` dict a lifespan
  hook may stash on (seam 9 / §A1.3.9).
* :class:`Extension` — an **ABC base class** (NOT a bare Protocol, per D2) with a
  required ``name`` and the **eleven seams** (§A1.3 + the §A1.10 corrections C2
  and C3), EACH with a safe no-op / empty / identity default so a subclass
  overrides only what it needs.
* :class:`ToolSpec` — the small DECLARATIVE tool spec seam 3 returns, so the
  contract is testable WITHOUT FastMCP; the later server build registers them.
* :class:`PayloadIndexSpec` — the declarative extra-index spec seam 8 returns
  (KEYWORD / BOOL payload fields beyond the base's).
* :class:`SourceProvider` — the indexer-side acquisition Protocol (signature
  ONLY here; the concrete ``LocalDirectorySourceProvider`` + snapshot layout is
  the next batch).

The eleven seams (the numbering matches §A1.3, with C2 adding seam 11):

1. :meth:`Extension.chunkers` — contribute :class:`~lorescribe.base.Chunker`\\ s.
2. :meth:`Extension.xml_profiles` + :meth:`Extension.js_profiles` — contribute
   XML ``SchemaProfile``\\ s / ``JsProfile``\\ s.
3. :meth:`Extension.tools` — declarative, index-backed :class:`ToolSpec`\\ s.
4. :meth:`Extension.augment_candidates` + :meth:`Extension.rerank` — the
   search-pipeline hook (C3): inject extra candidates AND adjust order/score.
5. :meth:`Extension.format_result` — a custom citation/format; ``None`` ⇒ base.
6. :meth:`Extension.chunk_key` — the VERSIONED semantic memory-key for
   correction matching (carries :attr:`Extension.key_version`); ``None`` ⇒ base.
7. :meth:`Extension.config_model` — validates the extension's ``extensions[name]``
   config slice; ``None`` ⇒ no extra config.
8. :meth:`Extension.payload_indexes` — extra payload indexes to declare.
9. :meth:`Extension.on_startup` / :meth:`Extension.on_shutdown` — async lifespan.
10. :meth:`Extension.source_providers` — indexer-side acquisition providers.
11. :meth:`Extension.classify_detail` — chunk-type → ``"summary"``/``"source"``
    detail-level classification (C2); ``None`` ⇒ base default classification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

from lorescribe.base import Chunker
from pydantic import BaseModel, ConfigDict, Field
from qdrant_client.models import ScoredPoint

# The two detail levels seam 11 (C2) partitions chunk types into: a coarse
# "overview" tier vs the full implementation tier. ``None`` from a classifier
# means "I have no opinion — fall through to the base / next classifier".
DetailLevel = Literal["summary", "source"]

# The payload-index kinds Qdrant supports here (seam 8). KEYWORD for exact-match
# string fields (e.g. ``model_name``); BOOL for flags (e.g. ``is_installed``).
PayloadIndexKind = Literal["keyword", "bool"]

# The baseline key-version an extension stamps into its semantic memory-key
# (seam 6) unless it overrides :attr:`Extension.key_version`. odoo-code's
# ``build_chunk_key`` was UNVERSIONED — the orphan hazard a version stamp closes.
DEFAULT_KEY_VERSION: int = 1


class ToolSpec(BaseModel):
    """A declarative description of an index-backed MCP tool (seam 3).

    Declarative on purpose: an extension hands back ``ToolSpec``\\ s, and the
    *later* FastMCP server build registers them. Keeping the spec free of any
    FastMCP coupling means seam 3 is fully testable here — the :attr:`handler`
    is a plain callable invocable without any server machinery.

    Attributes:
        name: The tool name as exposed to the MCP client.
        handler: The callable backing the tool. It receives the tool's declared
            inputs (and, in the server build, closes over the
            :class:`ExtensionContext`); here it is just a callable.
        description: A human-readable description of what the tool does.
        input_schema: A declarative description of the tool's inputs
            (field name → type description). Not a JSON Schema dialect — a small
            descriptive mapping the server build translates.
        output_schema: A declarative description of the tool's output shape.
    """

    # ``arbitrary_types_allowed`` so a bare function/closure is accepted as the
    # handler; ``extra="forbid"`` so a typo'd field fails loudly.
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    name: str
    handler: Callable[..., Any]
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


class PayloadIndexSpec(BaseModel):
    """An extension-declared extra payload index (seam 8).

    Beyond the base ``tier``/``file_path``/``content_hash``/``chunk_type``
    indexes, an extension may declare extra KEYWORD/BOOL fields the store should
    index (e.g. odoo's ``model_name`` KEYWORD, ``is_installed`` BOOL). The
    :attr:`schema_type` is constrained to the kinds the store supports, so an
    unknown kind fails loudly at construction rather than silently skipping the
    index later.

    Attributes:
        field_name: The payload field to index.
        schema_type: The index kind — ``"keyword"`` or ``"bool"``.
    """

    model_config = ConfigDict(extra="forbid")

    field_name: str
    # Constrained to the supported kinds: an unknown kind (e.g. ``"geo"``) raises
    # a ``ValidationError`` here rather than being silently dropped downstream.
    schema_type: PayloadIndexKind


class ExtensionContext(BaseModel):
    """The shared-services bundle handed to every context-taking seam.

    Injected by :class:`~loremaster.server.LoreServer` (tests pass fakes; the
    server passes the real resources). Carrying the bundle rather than wiring
    each service into every seam keeps the seam signatures stable as the set of
    shared services grows.

    Attributes:
        store: The :class:`~loremaster.store.qdrant.QdrantStore` (or a test
            stand-in). Typed ``Any`` to avoid importing the store here and to let
            tests pass a lightweight handle.
        embedder: The active :class:`loresigil.base.Embedder`.
        config: The validated :class:`~loremaster.config.LoreConfig`.
        count_tokens: The embedder's batch token counter (``list[str] ->
            list[int]``), carried so a seam can size text without re-importing
            the tokenizer.
        manifest: The :class:`~loremaster.index.manifest.Manifest` ledger.
        state: A mutable scratch dict a lifespan hook (seam 9) may stash state on
            — e.g. an ``on_startup`` caching a derived value for later handlers.
            Defaults to a fresh empty dict per context.
    """

    # ``arbitrary_types_allowed`` so the live resources (store / embedder /
    # manifest) and the injected callable are accepted; ``extra="forbid"`` so a
    # typo'd kwarg fails loudly. NOT frozen: ``state`` must be mutable (seam 9).
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    store: Any
    embedder: Any
    config: Any
    count_tokens: Callable[[list[str]], list[int]]
    manifest: Any
    state: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class SourceProvider(Protocol):
    """How to acquire a static tier's source into the snapshot layout (seam 10 / D7).

    Signature ONLY here — the concrete ``LocalDirectorySourceProvider`` and the
    snapshot/tier↔location source-of-truth are the next batch. The pipeline walks
    and ``read_text``\\ s real files, so a provider *materialises a tier's files
    into its snapshot subdir* (it does NOT stream bytes).

    ``runtime_checkable`` so a structural conformance check (``isinstance(obj,
    SourceProvider)``) is meaningful in tests and at registration: an object
    missing ``acquire`` is rejected.

    Attributes:
        tier: The tier identity this provider acquires.
    """

    tier: str

    def acquire(self, tier: str, snapshot_root: Path) -> None:
        """Materialise ``tier``'s files into ``snapshot_root`` (the snapshot layout).

        Args:
            tier: The tier being acquired (matches :attr:`tier`).
            snapshot_root: The on-disk root the tier's files are materialised
                under, for the live server to bind-mount ``:ro`` and serve.
        """
        ...


class Extension(ABC):
    """The base class a domain MCP subclasses to plug into ``loremaster``.

    An **ABC** (per D2 — a unit-testable value, not entry-point discovery), with
    a required :attr:`name` and the eleven seams. Every seam ships a safe,
    *inert* default — ``[]`` / ``None`` / identity / async no-op — so a subclass
    overrides only the seams it needs, and a server with zero extensions is the
    generic code/docs RAG. The base class is genuinely abstract: a subclass that
    does not implement :attr:`name` cannot be instantiated, so an unnamed
    extension can never be registered.
    """

    # The version an extension stamps into its semantic memory-key (seam 6). A
    # subclass overrides this when it bumps its keying scheme, so stored
    # corrections/graph edges are migratable rather than silently orphaned.
    key_version: int = DEFAULT_KEY_VERSION

    @property
    @abstractmethod
    def name(self) -> str:
        """The extension's stable name; also its key in the ``extensions:`` config."""

    # -- seam 1: chunkers ---------------------------------------------------
    def chunkers(self) -> list[Chunker]:
        """Contribute chunkers (seam 1). Default: none."""
        return []

    # -- seam 2: profiles ---------------------------------------------------
    def xml_profiles(self) -> list[Any]:
        """Contribute XML ``SchemaProfile``\\ s (seam 2). Default: none."""
        return []

    def js_profiles(self) -> list[Any]:
        """Contribute ``JsProfile``\\ s (seam 2). Default: none."""
        return []

    # -- seam 3: tools ------------------------------------------------------
    def tools(self, ctx: ExtensionContext) -> list[ToolSpec]:
        """Contribute declarative, index-backed tool specs (seam 3). Default: none.

        Args:
            ctx: The shared-services bundle a tool handler closes over.
        """
        return []

    # -- seam 4: search-pipeline hook (C3) ----------------------------------
    def augment_candidates(
        self, query: str, candidates: list[ScoredPoint], ctx: ExtensionContext
    ) -> list[ScoredPoint]:
        """Inject extra candidates into the search candidate set (seam 4 / C3).

        Default: identity — return ``candidates`` unchanged.

        Args:
            query: The user's search query.
            candidates: The current candidate points.
            ctx: The shared-services bundle.
        """
        return candidates

    def rerank(
        self, candidates: list[ScoredPoint], ctx: ExtensionContext
    ) -> list[ScoredPoint]:
        """Adjust the candidate order/score (seam 4 / C3).

        Default: identity — return ``candidates`` unchanged.

        Args:
            candidates: The candidate points to (re)order.
            ctx: The shared-services bundle.
        """
        return candidates

    # -- seam 5: citation/result format ------------------------------------
    def format_result(self, result: ScoredPoint, ctx: ExtensionContext) -> str | None:
        """Produce a custom citation/format for a result (seam 5).

        Default: ``None`` — the base supplies its default ``[SOURCE:file:line]``
        citation/format.

        Args:
            result: The scored point to format.
            ctx: The shared-services bundle.
        """
        return None

    # -- seam 6: versioned semantic memory-key -----------------------------
    def chunk_key(self, payload: dict[str, Any], ctx: ExtensionContext) -> str | None:
        """Produce the versioned semantic memory-key for correction matching (seam 6).

        Distinct from the base's structural point-ID (``records.py``): this is the
        *semantic* key a correction/targeted-injection is matched on. An
        overriding extension should fold :attr:`key_version` into the key so a
        keying-scheme change is detectable and migratable.

        Default: ``None`` — the base uses its structural point-ID.

        Args:
            payload: The chunk's stored payload.
            ctx: The shared-services bundle.
        """
        return None

    # -- seam 7: config namespace ------------------------------------------
    def config_model(self) -> type[BaseModel] | None:
        """The pydantic model validating this extension's ``extensions[name]`` slice (seam 7).

        Default: ``None`` — the extension declares no extra config.
        """
        return None

    # -- seam 8: payload indexes -------------------------------------------
    def payload_indexes(self) -> list[PayloadIndexSpec]:
        """Declare extra payload indexes (seam 8). Default: none."""
        return []

    # -- seam 9: async lifespan --------------------------------------------
    async def on_startup(self, ctx: ExtensionContext) -> None:
        """Run after core resources are up (seam 9). Default: no-op.

        May stash state on the mutable :attr:`ExtensionContext.state`.

        Args:
            ctx: The shared-services bundle (mutable ``state``).
        """
        return None

    async def on_shutdown(self, ctx: ExtensionContext) -> None:
        """Run on shutdown (seam 9). Default: no-op.

        Args:
            ctx: The shared-services bundle.
        """
        return None

    # -- seam 10: source providers -----------------------------------------
    def source_providers(self) -> list[Any]:
        """Contribute indexer-side :class:`SourceProvider`\\ s (seam 10). Default: none."""
        return []

    # -- seam 11: detail-level classification (C2) -------------------------
    def classify_detail(self, chunk_type: str) -> DetailLevel | None:
        """Classify a chunk type as ``"summary"`` or ``"source"`` (seam 11 / C2).

        Default: ``None`` — defer to the base's default classification of its own
        chunk types (signatures/imports/headings ⇒ summary; bodies ⇒ source).

        Args:
            chunk_type: The chunk's type tag.

        Returns:
            The detail level, or ``None`` to defer to the base default.
        """
        return None
