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
* :class:`FieldIndexSpec` — the declarative extra-index spec seam 8 returns
  (backend-neutral ``keyword`` / ``bool`` / ``fulltext`` fields beyond the base's).
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
8. :meth:`Extension.payload_indexes` — extra field indexes to declare.
9. :meth:`Extension.on_startup` / :meth:`Extension.on_shutdown` — async lifespan.
10. :meth:`Extension.source_providers` — indexer-side acquisition providers.
11. :meth:`Extension.classify_detail` — chunk-type → ``"summary"``/``"source"``
    detail-level classification (C2); ``None`` ⇒ base default classification.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

from lorescribe.base import Chunker
from pydantic import BaseModel, ConfigDict, Field

# Seam 12 (ingest) — the composable fragment the entity producers build. A
# RUNTIME import (not TYPE_CHECKING): ``ResolvedScope`` below is a pydantic model
# with a ``TxnFragment`` field, which pydantic must resolve at class-build time.
# ``store._txn`` is low-level (never imports this module), so no cycle.
from loremaster.store._txn import TxnFragment
from loremaster.store.candidate import Candidate

# The two detail levels seam 11 (C2) partitions chunk types into: a coarse
# "overview" tier vs the full implementation tier. ``None`` from a classifier
# means "I have no opinion — fall through to the base / next classifier".
DetailLevel = Literal["summary", "source"]

# The backend-neutral field-index kinds seam 8 supports. "keyword" for
# exact-match string fields (e.g. ``model_name``); "bool" for flags (e.g.
# ``is_installed``); "fulltext" for a BM25-indexable text field (e.g. an
# ``llm_summary`` enrichment column) — the unified store maps each kind onto
# its own index primitive rather than a vector store's fixed KEYWORD/BOOL-only
# index vocabulary.
FieldIndexKind = Literal["keyword", "bool", "fulltext"]

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


class FieldIndexSpec(BaseModel):
    """An extension-declared extra field index (seam 8).

    Beyond the base ``tier``/``file_path``/``content_hash``/``chunk_type``
    indexes, an extension may declare extra fields the store should index (e.g.
    odoo's ``model_name`` keyword, ``is_installed`` bool, or an ``llm_summary``
    fulltext column). Backend-neutral by design: the field names the KIND the
    field should be indexed as, and the store maps that kind onto its own index
    primitive, rather than the model naming a backend-specific schema type. The
    :attr:`kind` is constrained to the kinds the store supports, so an unknown
    kind fails loudly at construction rather than silently skipping the index
    later.

    Attributes:
        field_name: The field to index.
        kind: The index kind — ``"keyword"``, ``"bool"``, or ``"fulltext"``.
    """

    model_config = ConfigDict(extra="forbid")

    field_name: str
    # Constrained to the supported kinds: an unknown kind (e.g. ``"geo"``) raises
    # a ``ValidationError`` here rather than being silently dropped downstream.
    kind: FieldIndexKind


class ExtensionContext(BaseModel):
    """The shared-services bundle handed to every context-taking seam.

    Injected by :class:`~loremaster.server.LoreServer` (tests pass fakes; the
    server passes the real resources). Carrying the bundle rather than wiring
    each service into every seam keeps the seam signatures stable as the set of
    shared services grows.

    Attributes:
        store: The unified :class:`~loremaster.store.surreal.SurrealStore` (the
            SAME store the search pipeline reads — ``hybrid_search``/``scroll``),
            or a test stand-in. Typed ``Any`` to avoid importing the store here
            and to let tests pass a lightweight handle.
        embedder: The active :class:`loresigil.base.Embedder`.
        config: The validated :class:`~loremaster.config.LoreConfig`.
        count_tokens: The embedder's batch token counter (``list[str] ->
            list[int]``), carried so a seam can size text without re-importing
            the tokenizer.
        manifest: The Surreal-backed manifest — :class:`~loremaster.index.
            surreal_manifest.SurrealManifest` in production, a fake in tests.
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


@runtime_checkable
class IngestBackend(Protocol):
    """A domain store an ingesting extension readies BEFORE any fragment build (seam 12, phase 0).

    The DDL/lifecycle collaborator an extension contributes via
    :meth:`Extension.ingest_backends` — e.g. a dnd ``DnDStore`` with its own
    signed-in connection and ``execute_transaction`` (packet 51). A STRUCTURAL
    :class:`typing.Protocol` (not a base class), mirroring
    :class:`SourceProvider`, so an extension's store satisfies it by shape —
    the same duck-typed lifecycle ``code_graph`` / ``manifest`` / the ledgers
    already present to ``build_app_context``'s ``write_stack_readied`` rail:

    * ``ensure_ready()`` — apply the domain schema DDL (store law §1.1),
      idempotent, on the write-stack ready rail so a partial-ready failure
      unwinds every earlier collaborator (Q4).
    * ``close()`` — release the connection, on both teardown paths + normal
      shutdown.

    ``runtime_checkable`` so a structural conformance check is meaningful in
    tests and at registration.
    """

    async def ensure_ready(self) -> None:
        """Apply the domain schema DDL — idempotent (store law §1.1)."""
        ...

    async def close(self) -> None:
        """Release the backend's connection."""
        ...

    def entity_tables(self) -> Sequence[str]:
        """The entity TABLE names this backend owns — the store's tier-purge channel.

        The information channel a bare :class:`~loremaster.store.surreal.
        SurrealStore` needs to co-purge an extension's entity rows in
        ``delete_by_tier`` (a `TYPE NORMAL` table is indistinguishable from a
        chunk table without it — DG1). Each named table MUST carry a ``tier``
        field so a `DELETE <table> WHERE tier=$tier` is not a silent no-op
        (#107 shape). Default: none.
        """
        ...


class ResolvedScope(BaseModel):
    """One phase-2 scope's resolved edge fragment, LABELLED with its scope id (DG2).

    ``resolve_edges`` returns these (not bare :class:`TxnFragment`\\ s) so the
    indexer's per-scope apply loop can name WHICH scope failed in
    :attr:`~loremaster.index.indexer.IndexSummary.scopes_failed` — a bare
    fragment list carries only POSITION, never the ``source_book`` scope id.

    Attributes:
        scope: The ``source_book`` scope this fragment resolves (the failure label).
        fragment: The purge-then-``RELATE`` :class:`TxnFragment` for that scope,
            applied via the shared ``SurrealStore.apply`` (ONE IMPLEMENTATION).
    """

    # ``arbitrary_types_allowed`` so the frozen dataclass ``TxnFragment`` is a
    # valid field; ``frozen`` mirrors the value-object idiom (IndexOutcome).
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    scope: str
    fragment: TxnFragment


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
        self, query: str, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
        """Inject extra candidates into the search candidate set (seam 4 / C3).

        Default: identity — return ``candidates`` unchanged.

        P6 read-path cutover (§6 item 3): the seam carries the backend-neutral
        :class:`~loremaster.store.candidate.Candidate` the unified SurrealDB
        store's hybrid search returns, never a raw vector-store point type (a
        ``ScoredPoint``-style object).

        Args:
            query: The user's search query.
            candidates: The current candidate hits.
            ctx: The shared-services bundle.
        """
        return candidates

    def rerank(
        self, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
        """Adjust the candidate order/score (seam 4 / C3).

        Default: identity — return ``candidates`` unchanged.

        P6 read-path cutover (§6 item 3): the seam carries
        :class:`~loremaster.store.candidate.Candidate`\\ s, never a raw
        vector-store point type (a ``ScoredPoint``-style object).

        Args:
            candidates: The candidate hits to (re)order.
            ctx: The shared-services bundle.
        """
        return candidates

    # -- seam 5: citation/result format ------------------------------------
    def format_result(self, result: Candidate, ctx: ExtensionContext) -> str | None:
        """Produce a custom citation/format for a result (seam 5).

        Default: ``None`` — the base supplies its default ``[SOURCE:file:line]``
        citation/format.

        P6 read-path cutover (§6 item 3): the seam formats a backend-neutral
        :class:`~loremaster.store.candidate.Candidate` (render off its ``key`` /
        ``payload``), never a raw vector-store point type (a ``ScoredPoint``-style
        object).

        Args:
            result: The candidate hit to format.
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

    # -- seam 8: field indexes -----------------------------------------------
    def payload_indexes(self) -> list[FieldIndexSpec]:
        """Declare extra field indexes (seam 8). Default: none."""
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

    # -- seam 12: ingest (entity records + two-phase edges) -----------------
    # ONE seam (ingest), five methods (phases 0/1/2). Each ships a safe inert
    # default so a zero-ingest extension — and a zero-extension server — is
    # byte-unchanged.
    def claims(self, tier: str, path: str) -> bool:
        """Does this extension own the ingest of ``(tier, path)`` (seam 12)? Default: False.

        PURE + cheap (a suffix/tier test) — called for every pending file. A
        claimed file skips chunking/embedding and is ingested via
        :meth:`entity_fragment` instead. At most one registered extension may
        claim a given ``(tier, path)``.
        """
        return False

    def entity_fragment(
        self, tier: str, path: str, text: str, ctx: ExtensionContext
    ) -> TxnFragment | None:
        """Build this file's phase-1 NODE fragment (purge-then-create), or None (seam 12).

        A PURE builder on the ``build_file_graph_fragment`` precedent: parse
        ``text`` (never a socket touch), emit a self-contained
        DELETE-this-file's-prior-entity-nodes + CREATE-new-nodes fragment, NO
        ``BEGIN``/``COMMIT``, every value a bound param namespaced under
        ``f"xt_{self.name}_"``. NODES ONLY — cross-file ``ENFORCED`` edges are
        phase 2 (:meth:`resolve_edges`). Default: None.
        """
        return None

    def entity_purge_fragment(self, tier: str, path: str) -> TxnFragment | None:
        """Build the standalone purge of one file's entity slice, or None (seam 12).

        The composable counterpart to :meth:`entity_fragment`'s internal purge,
        for the standalone DELETE sites (a removed file) — mirrors
        ``purge_file_fragment``. Default: None.
        """
        return None

    async def resolve_edges(
        self, ctx: ExtensionContext, changed_scopes: set[str] | None
    ) -> list[ResolvedScope]:
        """Phase 2: resolve cross-file edges per ``source_book`` scope (seam 12).

        READS committed phase-1 nodes to resolve each edge's endpoints, then
        returns ONE :class:`ResolvedScope` PER scope (its ``source_book`` id +
        the purge-then-``RELATE`` fragment — DG2, so the indexer can name a
        failed scope). The framework calls this ONLY with ``changed_scopes=None``
        (every scope this extension owns, at full-sweep completion). The ``set``
        form is RESERVED for the pinned non-feature (live per-file
        re-resolution) and is never passed today. The INDEXER applies each
        scope's fragment via ``SurrealStore.apply`` (ONE IMPLEMENTATION —
        never a private query path). Default: ``[]`` (no edges).
        """
        return []

    def ingest_backends(self, ctx: ExtensionContext) -> list[IngestBackend]:
        """Contribute the domain store(s) readied BEFORE any fragment build (seam 12, phase 0).

        Each :class:`IngestBackend` applies its schema DDL on
        ``build_app_context``'s ``write_stack_readied`` rail (like
        ``code_graph``) so a partial-ready failure unwinds. The extension
        retains the reference for its :meth:`entity_fragment` /
        :meth:`resolve_edges` seams to read through. Default: ``[]``.
        """
        return []


# --------------------------------------------------------------------------- #
# The static extension registry (packet 46 — config-driven discovery).
# --------------------------------------------------------------------------- #
# Maps an extension's stable ``name`` to its class. ``LoreServer.__init__``
# consults it to instantiate + ``register_extension`` each extension named in a
# project's ``extensions:`` config block.
#
# It ships EMPTY in production: no real extension exists yet (the ``dnd``
# extension is packet 51), so the generic RAG's default construction discovers
# nothing. A workspace-member extension registers its class here; ENTRY-POINT
# discovery is deliberately DEFERRED until an out-of-repo extension exists (a
# named re-open trigger), per the wave-D architecture ruling §3.
#
# It is a LIVE module global on PURPOSE: the discovery hook reads
# ``loremaster.extension.EXTENSION_REGISTRY`` at construction time (never a name
# bound at import into another module), so a test injects a fake registry via
# ``monkeypatch.setattr(loremaster.extension, "EXTENSION_REGISTRY", {...})`` and
# the very next ``LoreServer(...)`` sees it.
EXTENSION_REGISTRY: dict[str, type[Extension]] = {}
