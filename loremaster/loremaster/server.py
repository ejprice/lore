"""The :class:`LoreServer` composition skeleton (plan AMENDMENT 1, D1/D2/§A1.9).

``LoreServer`` is the layer that *composes* a deployment out of a
:class:`~loremaster.config.LoreConfig` and zero or more
:class:`~loremaster.extension.Extension` objects **and runs the FastMCP server**.
:meth:`LoreServer.run` configures structured logging, registers the MCP tools, runs
the embedder probe-gate, builds the (optionally Bearer-gated) ASGI app, and serves
the FastMCP streamable-http app via uvicorn — its heavy startup (probe-gate /
reconcile / watcher) runs once per process, shared across concurrent MCP sessions.

What it DOES do (the composition contract):

* :meth:`from_config` — load the config and stand up a bare server. A bare
  server (zero extensions) is the **generic code/docs RAG**: its
  :attr:`registry` is the default lorescribe registry (python/markdown/sql/xml/
  js/stylesheet/text), its citation format is the base default, and no extension
  hook fires.
* :meth:`register_extension` — compose an extension: validate its
  ``config_model()`` against the ``extensions[name]`` slice (fail loud on a bad
  or missing-required slice); register its ``chunkers()`` into the
  :class:`~lorescribe.registry.ChunkerRegistry` **applying the nit-1 register
  guard**; (re)construct the XML/JS chunkers WITH the accumulated profiles; and
  collect payload-index / source-provider / tool / detail-classification /
  format / chunk-key / search / lifespan hooks for the later layers to consume.
  Returns ``self`` for chaining; supports zero or more extensions.

**nit-1 register guard (both halves).** Registration RAISES when an extension
chunker would shadow an existing suffix-owner in the registry's predicate tier,
in EITHER form: (1) a ``default_suffixes`` entry that OVERLAPS an already-owned
suffix, or (2) a greedy ``handles()`` predicate that accepts an owned suffix's
files even though it declares no (or a different) suffix — caught by probing each
owned suffix with a synthetic sentinel path at registration. A chunker claiming
only fresh suffixes, or a basename/predicate-keyed chunker whose ``handles``
returns False for those probes (the seam-1 use case, e.g. a ``Makefile``
claimant), registers freely. (``handles()`` is arbitrary code; the probe catches
the realistic greedy forms, not a pathologically path-specific predicate.)
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import os
from collections.abc import Awaitable, Callable, Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

from lorescribe.javascript import JavascriptChunker
from lorescribe.markdown import MarkdownChunker
from lorescribe.python_ast import PythonAstChunker
from lorescribe.registry import ChunkerRegistry
from lorescribe.sql import SqlChunker
from lorescribe.stylesheet import StylesheetChunker
from lorescribe.text import TextChunker
from lorescribe.xml_generic import XmlChunker
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field
from qdrant_client.models import ScoredPoint

from loremaster.config import WATCH_STATIC, LoreConfig, load_config
from loremaster.extension import (
    DetailLevel,
    Extension,
    ExtensionContext,
    PayloadIndexSpec,
    ToolSpec,
)

# The consumer-visible tool RETURN models, imported at RUNTIME (not just under
# TYPE_CHECKING): each built-in tool wrapper is annotated with its real model
# return type so FastMCP derives a FIELD-LEVEL outputSchema + structuredContent
# (mcp-builder structured-output standard). FastMCP resolves a wrapper's return
# annotation via ``get_type_hints`` at registration time, so these names MUST live
# in this module's runtime namespace — a TYPE_CHECKING-only import would resolve to
# nothing and silently fall back to an opaque schema. None of these modules import
# ``server`` at runtime (only under TYPE_CHECKING), so the import is acyclic.
from loremaster.graph import GraphNode
from loremaster.index.indexer import IndexSummary
from loremaster.memory.store import RecalledMemory
from loremaster.read_file import FileSpan
from loremaster.search import DetailSelector, SearchResult
from loremaster.symbols import ResolvedSymbol

if TYPE_CHECKING:
    from loresigil.base import Embedder

    from loremaster.graph import CodeGraph
    from loremaster.index.indexer import Indexer
    from loremaster.index.manifest import Manifest
    from loremaster.index.reconcile import ReconcileEngine
    from loremaster.memory.store import MemoryStore
    from loremaster.read_file import ReadFileTool
    from loremaster.search import SearchPipeline
    from loremaster.store.qdrant import QdrantStore
    from loremaster.symbols import SymbolTool

# The parent-context ``state`` key under which the per-extension lifespan-state
# namespaces live (fix B / §A1.10). ``ctx.state[_EXTENSION_STATE_KEY][name]`` is
# extension ``name``'s private state dict; the leading double underscore keeps it
# from colliding with a key an extension itself writes into its OWN namespace.
_EXTENSION_STATE_KEY = "__extension_state__"

logger = logging.getLogger(__name__)

# The registry keys for the profile-driven chunkers, which are (re)constructed
# with the accumulated profiles every time an extension is registered.
_XML_KEY = "xml"
_JS_KEY = "javascript"

# The base (non-profile) chunkers and the default suffixes each owns. The keys
# match odoo-code / the plan's chunker names. The suffix sets feed both the
# registry's default extension map AND the nit-1 overlap guard.
_BASE_CHUNKER_SUFFIXES: dict[str, tuple[str, ...]] = {
    "python_ast": (".py",),
    "markdown": (".md", ".markdown"),
    "sql": (".sql",),
    "stylesheet": (".css", ".scss"),
    "text": (".txt", ".rst"),
}

# The profile-driven base chunkers' suffixes (registered separately because they
# must be rebuilt with profiles).
_XML_SUFFIXES: tuple[str, ...] = (".xml",)
_JS_SUFFIXES: tuple[str, ...] = (".js",)

# The base default detail-level classification (seam 11 / C2): the base
# classifies ITS OWN chunk types. Overview-ish types (signatures, imports,
# headings, the XML element record) read as ``"summary"``; everything else —
# bodies, statements, windows — reads as ``"source"``. An extension's
# ``classify_detail`` is consulted first; this is the fallback.
_BASE_SUMMARY_CHUNK_TYPES: frozenset[str] = frozenset(
    {
        "imports",  # python_ast import block — an overview of dependencies
        "class",  # python_ast class header line + docstring — a signature
        "markdown_section",  # a heading-rooted doc section — overview content
        "xml_element",  # a whole-record XML element — a structural overview
    }
)


class LoreServer:
    """Composition skeleton: a config + registered extensions → a wired surface.

    Construct via :meth:`from_config`. Register extensions with
    :meth:`register_extension` (chainable). The wired surface — :attr:`registry`,
    :attr:`payload_index_specs`, :attr:`source_providers`, :meth:`tool_specs`,
    the resolved :meth:`format_result` / :meth:`chunk_key` / :meth:`classify_detail`
    / :meth:`augment_candidates` / :meth:`rerank`, and the lifespan-hook runners —
    is what the later indexer / search / server layers consume.
    """

    def __init__(self, config: LoreConfig) -> None:
        """Initialise a bare server (the generic RAG) from a validated config.

        Args:
            config: The validated project configuration.
        """
        self._config = config
        self._extensions: list[Extension] = []
        # Accumulated profiles for the (re)constructed XML/JS chunkers.
        self._xml_profiles: list[Any] = []
        self._js_profiles: list[Any] = []
        # The suffixes each registered chunker owns, for the nit-1 overlap guard.
        # Seeded with the base chunkers' suffixes so an extension cannot shadow a
        # base suffix-owner (e.g. claim ``.py``).
        self._suffix_owner: dict[str, str] = {}
        # Collected seam outputs.
        self._payload_index_specs: list[PayloadIndexSpec] = []
        self._source_providers: list[Any] = []
        # Validated per-extension config slices (seam 7), keyed by extension name.
        self._extension_configs: dict[str, BaseModel] = {}
        # The registry, built with the base chunkers + (initially no) profiles.
        self._registry = ChunkerRegistry()
        self._build_default_registry()

    # -- construction -------------------------------------------------------

    @classmethod
    def from_config(cls, path: str | Path) -> LoreServer:
        """Load ``lore.yaml`` from ``path`` and return a bare :class:`LoreServer`.

        Args:
            path: Filesystem path to the project ``lore.yaml``.

        Returns:
            A bare server (zero extensions) — the generic code/docs RAG.
        """
        return cls(load_config(path))

    def _build_default_registry(self) -> None:
        """Register the default lorescribe chunkers into a fresh registry.

        The base (non-profile) chunkers register under their default suffixes;
        the profile-driven XML/JS chunkers are (re)built via
        :meth:`_register_profile_chunkers` so a later extension's profiles take
        effect. Records each suffix's owner for the nit-1 guard.
        """
        base_factories: dict[str, Any] = {
            "python_ast": PythonAstChunker,
            "markdown": MarkdownChunker,
            "sql": SqlChunker,
            "stylesheet": StylesheetChunker,
            "text": TextChunker,
        }
        for key, suffixes in _BASE_CHUNKER_SUFFIXES.items():
            self._registry.register(key, base_factories[key](), list(suffixes))
            self._claim_suffixes(key, suffixes)
        self._register_profile_chunkers()

    def _register_profile_chunkers(self) -> None:
        """(Re)register the XML and JS chunkers with the accumulated profiles.

        Called on construction (no profiles) and after every extension that
        contributes profiles, so the constructed chunkers always carry the full
        accumulated profile set. Re-registering a key keeps its registry slot
        (the registry's ``register`` overwrites the same key in place).
        """
        self._registry.register(
            _XML_KEY, XmlChunker(profiles=self._xml_profiles), list(_XML_SUFFIXES)
        )
        self._registry.register(
            _JS_KEY, JavascriptChunker(profiles=self._js_profiles), list(_JS_SUFFIXES)
        )
        self._claim_suffixes(_XML_KEY, _XML_SUFFIXES)
        self._claim_suffixes(_JS_KEY, _JS_SUFFIXES)

    def _claim_suffixes(self, key: str, suffixes: Iterable[str]) -> None:
        """Record ``key`` as the owner of each suffix (for the nit-1 guard)."""
        for suffix in suffixes:
            self._suffix_owner[suffix.lower()] = key

    # -- accessors ----------------------------------------------------------

    @property
    def config(self) -> LoreConfig:
        """The validated project configuration."""
        return self._config

    @property
    def extensions(self) -> list[Extension]:
        """The registered extensions, in registration order (empty for a bare server)."""
        return list(self._extensions)

    @property
    def registry(self) -> ChunkerRegistry:
        """The composed chunker registry (default chunkers + extension chunkers/profiles)."""
        return self._registry

    @property
    def payload_index_specs(self) -> list[PayloadIndexSpec]:
        """The extension-declared extra payload indexes (seam 8), in registration order."""
        return list(self._payload_index_specs)

    @property
    def source_providers(self) -> list[Any]:
        """The extension-contributed source providers (seam 10), in registration order."""
        return list(self._source_providers)

    def extension_context(self, *, store: Any) -> ExtensionContext:
        """Build an :class:`ExtensionContext` over the server's shared services.

        The store is passed in (the live store is constructed by the later server
        build); the embedder/manifest are likewise placeholders here. ``Any``
        keeps this composition-only layer free of the runtime resources, which
        the later layers inject.

        Args:
            store: The store handle to carry in the context.

        Returns:
            A fresh :class:`ExtensionContext`.
        """
        return ExtensionContext(
            store=store,
            embedder=None,
            config=self._config,
            count_tokens=_no_tokenizer,
            manifest=None,
        )

    def extension_config(self, name: str) -> BaseModel:
        """Return the validated config slice for the named extension (seam 7).

        Args:
            name: The extension name.

        Returns:
            The validated config model instance.

        Raises:
            KeyError: If the named extension declared no config model (or is not
                registered).
        """
        return self._extension_configs[name]

    # -- registration -------------------------------------------------------

    def register_extension(self, ext: Extension) -> LoreServer:
        """Compose ``ext`` into the server and return ``self`` for chaining.

        The order matters: the config slice is validated FIRST (fail loud before
        mutating any registry state), then chunkers are registered under the
        nit-1 guard, then profiles + the rest of the seams are collected.

        Args:
            ext: The extension to register.

        Returns:
            ``self``, so registrations chain.

        Raises:
            pydantic.ValidationError: If the extension's ``config_model`` rejects
                (or is missing) its ``extensions[name]`` config slice.
            ValueError: If one of the extension's chunkers declares a default
                suffix already owned by a registered chunker (the nit-1 guard).
        """
        # Seam 7 FIRST — fail loud before any registry mutation.
        self._validate_extension_config(ext)

        # Seam 1 — register chunkers under the nit-1 overlap guard.
        for chunker in ext.chunkers():
            self._register_extension_chunker(ext, chunker)

        # Seam 2 — accumulate profiles, then rebuild the XML/JS chunkers so the
        # profiles take effect on the constructed chunkers.
        new_xml = list(ext.xml_profiles())
        new_js = list(ext.js_profiles())
        if new_xml or new_js:
            self._xml_profiles.extend(new_xml)
            self._js_profiles.extend(new_js)
            self._register_profile_chunkers()

        # Seams 8 + 10 — collect declarative specs / providers.
        self._payload_index_specs.extend(ext.payload_indexes())
        self._source_providers.extend(ext.source_providers())

        self._extensions.append(ext)
        return self

    def _validate_extension_config(self, ext: Extension) -> None:
        """Validate the extension's ``extensions[name]`` slice with its model (seam 7).

        A ``None`` model means the extension declares no extra config — nothing to
        validate. Otherwise the slice (possibly absent ⇒ ``{}``) is validated by
        the model; a bad key or a missing required field raises a
        ``ValidationError`` here, at registration, rather than surfacing later.
        """
        model = ext.config_model()
        if model is None:
            return
        slice_data = self._config.extensions.get(ext.name, {})
        # ``model_validate`` on the (possibly empty) slice: a required field with
        # no value raises, which is the fail-loud behaviour for a missing slice.
        self._extension_configs[ext.name] = model.model_validate(slice_data)

    def _register_extension_chunker(self, ext: Extension, chunker: Any) -> None:
        """Register one extension chunker, enforcing the nit-1 shadow guard (both halves).

        nit-1 is "a chunker that claims an already-owned suffix shadows the
        suffix-owner in the registry's predicate tier". It has TWO forms, both
        refused loudly here:
          1. **Declared overlap** — a ``default_suffixes`` entry already owned by a
             registered chunker.
          2. **Greedy predicate** — a chunker that declares no (or a different)
             suffix but whose ``handles()`` accepts an owned suffix's files anyway;
             caught by probing each owned suffix with a synthetic sentinel path.
        A chunker claiming only FRESH suffixes, or a basename/pattern chunker whose
        ``handles`` returns False for the owned-suffix probes (the seam-1 case, e.g.
        a ``Makefile`` claimant), registers cleanly and is reached via the
        registry's predicate tier. (``handles()`` is arbitrary code; the probe
        catches the realistic greedy forms, not a pathologically path-specific one.)

        Args:
            ext: The owning extension (its name namespaces the registry key).
            chunker: The chunker to register.
        """
        suffixes: tuple[str, ...] = tuple(getattr(chunker, "default_suffixes", ()) or ())
        declared = {s.lower() for s in suffixes}
        for suffix in suffixes:
            owner = self._suffix_owner.get(suffix.lower())
            if owner is not None:
                raise ValueError(
                    f"extension {ext.name!r} chunker {type(chunker).__name__!r} claims default "
                    f"suffix {suffix!r}, already owned by registered chunker {owner!r}; "
                    f"refusing to shadow the suffix-owner (use a config override to re-route, "
                    f"or a basename predicate for a filename-keyed chunker)."
                )
        # A DECLARED suffix overlap is only half of nit-1. A chunker that declares
        # NO suffix can still carry a greedy ``handles()`` predicate that claims an
        # owned suffix's files, and the registry's predicate tier would let it shadow
        # the suffix-owner. Probe every already-owned suffix this chunker does not
        # itself claim: if its ``handles`` accepts such a file it is greedy — refuse
        # loudly. A well-behaved basename/pattern chunker (e.g. a Makefile claimant)
        # returns False for these synthetic probes and registers freely.
        for owned_suffix, owner in self._suffix_owner.items():
            if owned_suffix in declared:
                continue
            if chunker.handles(f"/__lore_suffix_probe__/sentinel{owned_suffix}"):
                raise ValueError(
                    f"extension {ext.name!r} chunker {type(chunker).__name__!r} has a handles() "
                    f"predicate that claims {owned_suffix!r} files (owned by {owner!r}); a greedy "
                    f"predicate shadows the suffix-owner via the registry's predicate tier. Narrow "
                    f"handles() to the chunker's own files (basename/pattern), or declare a fresh "
                    f"suffix via default_suffixes."
                )
        # Namespace the registry key by the extension so two extensions' chunkers
        # never collide on a logical key.
        key = f"{ext.name}:{type(chunker).__name__}"
        self._registry.register(key, chunker, list(suffixes))
        self._claim_suffixes(key, suffixes)

    # -- tool specs (seam 3) ------------------------------------------------

    def tool_specs(self, ctx: ExtensionContext) -> list[ToolSpec]:
        """Collect every registered extension's declarative tool specs (seam 3).

        Args:
            ctx: The shared-services bundle the tool handlers close over.

        Returns:
            The concatenated tool specs, in registration order.
        """
        specs: list[ToolSpec] = []
        for ext in self._extensions:
            specs.extend(ext.tools(ctx))
        return specs

    def extension_tool_specs(self, ctx: ExtensionContext) -> list[ToolSpec]:
        """Collect every extension's tool specs, each over its CHILD context (fix B).

        Like :meth:`tool_specs`, but each extension's ``tools`` is called with
        THAT extension's per-extension child context (the same private ``state``
        namespace its lifespan hooks populate, via :meth:`_child_context`) rather
        than the shared parent context. This is the context-correct collection the
        live FastMCP server build registers: a tool handler that reads ``ctx.state``
        sees the namespace its own ``on_startup`` seeded — not a sibling's, and not
        the bare parent state.

        Args:
            ctx: The parent runtime extension context (carries every namespace).

        Returns:
            The concatenated tool specs, in registration order, each handler bound
            to its extension's child context.
        """
        specs: list[ToolSpec] = []
        for ext in self._extensions:
            specs.extend(ext.tools(self._child_context(ctx, ext)))
        return specs

    # -- resolved behaviour hooks ------------------------------------------

    def format_result(self, result: ScoredPoint, ctx: ExtensionContext) -> str | None:
        """Resolve the citation/format for a result (seam 5).

        The first registered extension whose ``format_result`` returns a non-
        ``None`` string wins; if none claims it, returns ``None`` so the caller
        uses the base default citation format.

        Args:
            result: The scored point to format.
            ctx: The shared-services bundle.

        Returns:
            A custom format string, or ``None`` for the base default.
        """
        for ext in self._extensions:
            formatted = ext.format_result(result, ctx)
            if formatted is not None:
                return formatted
        return None

    def chunk_key(self, payload: dict[str, Any], ctx: ExtensionContext) -> str | None:
        """Resolve the versioned semantic memory-key for a payload (seam 6).

        The first registered extension whose ``chunk_key`` returns a non-``None``
        key wins; if none claims it, returns ``None`` so the base structural
        point-ID is used.

        Args:
            payload: The chunk's stored payload.
            ctx: The shared-services bundle.

        Returns:
            A custom semantic key, or ``None`` for the base default.
        """
        for ext in self._extensions:
            key = ext.chunk_key(payload, ctx)
            if key is not None:
                return key
        return None

    def classify_detail(self, chunk_type: str) -> DetailLevel | None:
        """Resolve the detail-level classification for a chunk type (seam 11 / C2).

        A registered extension's classification wins for the chunk types it
        claims; otherwise the base default classification of its own chunk types
        applies (summary types vs everything-else=source). A chunk type no one —
        extension or base — recognises returns ``None`` (no opinion).

        Args:
            chunk_type: The chunk's type tag.

        Returns:
            ``"summary"`` / ``"source"``, or ``None`` if unclassified.
        """
        for ext in self._extensions:
            level = ext.classify_detail(chunk_type)
            if level is not None:
                return level
        return self._base_classify_detail(chunk_type)

    @staticmethod
    def _base_classify_detail(chunk_type: str) -> DetailLevel:
        """The base default classification of the base's own chunk types (C2)."""
        if chunk_type in _BASE_SUMMARY_CHUNK_TYPES:
            return "summary"
        return "source"

    def augment_candidates(
        self, query: str, candidates: list[ScoredPoint], ctx: ExtensionContext
    ) -> list[ScoredPoint]:
        """Run every extension's candidate-augmentation in order (seam 4 / C3).

        Each extension may inject extra candidates; the output of one feeds the
        next. With no extensions this is the identity (the generic RAG).

        Args:
            query: The search query.
            candidates: The starting candidate list.
            ctx: The shared-services bundle.

        Returns:
            The (possibly augmented) candidate list.
        """
        result = candidates
        for ext in self._extensions:
            result = ext.augment_candidates(query, result, ctx)
        return result

    def rerank(
        self, candidates: list[ScoredPoint], ctx: ExtensionContext
    ) -> list[ScoredPoint]:
        """Run every extension's re-rank in order (seam 4 / C3).

        Args:
            candidates: The candidate list to (re)order.
            ctx: The shared-services bundle.

        Returns:
            The (possibly reordered) candidate list.
        """
        result = candidates
        for ext in self._extensions:
            result = ext.rerank(result, ctx)
        return result

    # -- lifespan hooks (seam 9) -------------------------------------------

    def extension_state(self, ctx: ExtensionContext, name: str) -> dict[str, Any]:
        """Return the per-extension ``state`` namespace within ``ctx`` for ``name`` (fix B).

        Each extension's lifespan hooks (seam 9) are handed a CHILD context whose
        ``state`` is a private sub-dict of the parent ``ctx.state``, keyed by the
        extension name under :data:`_EXTENSION_STATE_KEY`. This accessor returns
        that sub-dict (creating it on first access) so the server (and a test) can
        inspect what an extension stashed — isolation without loss. One
        extension's namespace is a distinct dict from another's, so a write to one
        is never visible in the other.

        Args:
            ctx: The parent extension context carrying every namespace.
            name: The extension name whose private state namespace to return.

        Returns:
            The named extension's private ``state`` dict (a sub-dict of
            ``ctx.state``).
        """
        namespaces = ctx.state.setdefault(_EXTENSION_STATE_KEY, {})
        per_extension: dict[str, Any] = namespaces.setdefault(name, {})
        return per_extension

    def _child_context(self, ctx: ExtensionContext, ext: Extension) -> ExtensionContext:
        """Build a child context whose ``state`` is ``ext``'s private namespace (fix B).

        Every shared service is carried over verbatim; only ``state`` is swapped
        for the extension's own namespace, so the hook can read/write its state
        without seeing — or being seen by — a sibling extension. pydantic copies
        a dict passed to a model field, so the child's ``state`` object is
        re-published into the parent's namespace map by identity AFTER
        construction — keeping ``extension_state`` and the hook pointed at the
        SAME dict (startup writes are visible to shutdown and to the server).
        """
        child = ExtensionContext(
            store=ctx.store,
            embedder=ctx.embedder,
            config=ctx.config,
            count_tokens=ctx.count_tokens,
            manifest=ctx.manifest,
            state=self.extension_state(ctx, ext.name),
        )
        # Re-publish the child's (copied) state object as the canonical namespace,
        # so the same dict the hook mutates is the one ``extension_state`` returns.
        namespaces: dict[str, Any] = ctx.state.setdefault(_EXTENSION_STATE_KEY, {})
        namespaces[ext.name] = child.state
        return child

    async def run_startup_hooks(self, ctx: ExtensionContext) -> None:
        """Await every extension's ``on_startup`` in order, UNWINDING on failure (fix A).

        Each extension is started with its own per-extension child context (fix B).
        If extension ``N``'s ``on_startup`` raises, every already-started
        extension ``0..N-1`` has its ``on_shutdown`` run — in REVERSE order
        (last-started, first-stopped) — before the original error re-raises, so no
        half-started state is left behind. The failed extension itself is NOT shut
        down (its startup never completed). A shutdown raised during the unwind is
        suppressed so the FIRST (root-cause) startup error is the one that
        surfaces, not a secondary teardown error.

        Args:
            ctx: The parent extension context (carries every namespace).

        Raises:
            Exception: Re-raises the first ``on_startup`` failure after unwinding.
        """
        started: list[Extension] = []
        for ext in self._extensions:
            try:
                await ext.on_startup(self._child_context(ctx, ext))
            except BaseException:
                # Unwind the already-started extensions, last-started first, then
                # re-raise the ORIGINAL error (teardown errors are suppressed so
                # they never mask the root cause).
                for prior in reversed(started):
                    try:
                        await prior.on_shutdown(self._child_context(ctx, prior))
                    except BaseException:  # noqa: BLE001 - never mask the startup error
                        pass
                raise
            started.append(ext)

    async def run_shutdown_hooks(self, ctx: ExtensionContext) -> None:
        """Await every registered extension's ``on_shutdown`` in REVERSE order (seam 9).

        Reverse order so shutdown unwinds startup (last-started, first-stopped) —
        the conventional teardown order for resources stacked on the context. Each
        extension's hook is handed its own per-extension child context (fix B), so
        a teardown reads the SAME private state its ``on_startup`` populated.

        Args:
            ctx: The parent extension context (carries every namespace).
        """
        for ext in reversed(self._extensions):
            await ext.on_shutdown(self._child_context(ctx, ext))

    # -- serving -----------------------------------------------------------

    def run(self) -> None:
        """Build and serve the FastMCP streamable-http server (Deliverable 3).

        Assembles the MCP server (:func:`build_mcp_server`) and the ASGI app
        (:func:`build_asgi_app` — Bearer-gated when an enabled ``auth`` block is
        configured, D9/D11) and serves it via uvicorn on the configured
        ``host``/``port``. The streamable-http app carries the
        :class:`AppContext` lifespan (probe gate + service construction + watcher/
        reconcile tasks + extension hooks), so the embedder is probed and the
        index made live as the server comes up. TLS is terminated upstream (D11) —
        loremaster serves plain HTTP behind the ingress.
        """
        import uvicorn

        # Configure the lore-namespace JSON handler FIRST — before build_mcp_server,
        # which constructs FastMCP, whose __init__ runs logging.basicConfig with a
        # root RichHandler (mcp.server.fastmcp.utilities.logging.configure_logging).
        # If our scoped handler is not installed by then, the early
        # ``loremaster.server`` startup events (probe gate / watcher / reconcile)
        # propagate to that root handler and render via the default formatter
        # instead of JsonFormatter — so Mezmo never indexes them. Installing our
        # handler (propagate=False) first keeps every lore event on the JSON sink.
        # The lifespan re-runs this (idempotent) so an env override still applies.
        configure_logging_from_config(self._config)
        mcp = build_mcp_server(self)
        app = build_asgi_app(mcp, self._config)
        uvicorn_config = uvicorn.Config(
            app,
            host=self._config.server.host,
            port=self._config.server.port,
            log_level="info",
        )
        uvicorn.Server(uvicorn_config).run()


# The MCP mount path is taken from ``config.server.path``; FastMCP's
# ``streamable_http_path`` must match so the app mounts where ``.mcp.json`` points.

# Default bounds for the graph-traversal tools (the plan's "bounded depth + result
# cap" so a pathological fan-out cannot blow the context budget).
_DEFAULT_BLAST_DEPTH = 3
_DEFAULT_BLAST_MAX_RESULTS = 50
# Default ``k`` for the search/recall tools when the caller does not specify one.
_DEFAULT_SEARCH_K = 8
_DEFAULT_RECALL_K = 5

# Lower/upper bounds the numeric tool params publish (mcp-builder: constrain inputs
# at the schema, so a zero/negative or absurd value is rejected at validation rather
# than producing a confusing empty/over-large result). A count or hop-depth below 1
# is meaningless; the upper caps keep a single call's result + traversal bounded so a
# typo (k=100000) cannot blow the context budget.
_MIN_COUNT = 1
_MAX_SEARCH_K = 100
_MAX_RECALL_K = 100
_MAX_BLAST_DEPTH = 25
_MAX_BLAST_MAX_RESULTS = 500
# The memory collection's slug suffix → ``lore_<slug>_memory``.
_MEMORY_SLUG_SUFFIX = "_memory"


# The in-band consumer guidance the FastMCP server advertises to the connecting
# agent (mcp-builder: a substantial, behavioral ``instructions`` block). This is
# the consumer's single source of truth — what lore is, when to reach for which
# tool, the citation convention, the freshness / read-your-writes model, and the
# project-memory stance — so a consumer needs zero out-of-band documentation. The
# odoo-code server proves the pattern (rich behavioral instructions delivered
# in-band); this is its generic-RAG analog. Edited here ⇒ keep the substring
# contracts in ``test_mcp_server.py::TestServerInstructions`` green.
_INSTRUCTIONS = (
    "lore is a PER-PROJECT semantic RAG over THIS repository's code and docs, plus a "
    "durable project-memory store. It indexes the project's source (Python, Markdown, "
    "SQL, XML, JS, CSS, text), keeps a manifest of per-file freshness, and builds an "
    "import/definition/test graph. Use it instead of guessing: it returns the EXACT, "
    "cited source on disk so you quote real code rather than recalling a plausible "
    "lookalike. Results are summarised value objects, NEVER raw store dumps.\n"
    "\n"
    "WHEN TO USE WHICH TOOL:\n"
    "- lore_search_code(query, ...): semantic, memory-boosted search across code + "
    "docs. Your default entry point when you don't already know the exact name/path. "
    "Returns ranked, cited hits.\n"
    "- lore_get_symbol(qualified_name): the EXACT stored definition + on-disk location "
    "of a named Python symbol (class / method / function). Use this — NOT "
    "lore_search_code — when you know the name and want the authoritative definition "
    "(it is collision-correct, not a fuzzy ranked guess).\n"
    "- lore_read_file(tier, path, ...): the EXACT on-disk text of a file span with a "
    "[SOURCE:...] header. Use after a lore_search_code / lore_get_symbol hit to read "
    "surrounding context.\n"
    "- lore_what_imports(target): the DIRECT importers of a module (one reverse import "
    "edge).\n"
    "- lore_blast_radius(target, ...): the TRANSITIVE reverse-dependency closure "
    "(bounded depth + result cap) — 'what could a change here break?'. Reach for "
    "lore_blast_radius (transitive) over lore_what_imports (direct) when you need the "
    "ripple, not just the neighbours.\n"
    "- lore_tests_for(symbol_or_file): the test nodes covering a symbol or file.\n"
    "- lore_index_status(): the freshness/health roll-up (indexed / in-flight / failed "
    "counts) read straight from the manifest — zero embeds, cheap.\n"
    "- lore_reindex(tier=None): force a whole-tier reconcile sweep (or all tiers). The "
    "heavy 'make everything current now' hammer — not a per-file wait.\n"
    "- lore_save_memory(text, ...) / lore_recall_memory(query, ...): the project-memory "
    "store (see MEMORY below).\n"
    "\n"
    "CITATIONS: every lore_search_code / lore_read_file result carries a "
    "[SOURCE:file:line] citation plus a stable 'Key:' line (the chunk key) and a fenced "
    "source block. Echo the [SOURCE:...] citation when you quote code, and pass a "
    "'Key:' value back to lore_save_memory to pin a correction to a specific chunk.\n"
    "\n"
    "FRESHNESS / READ-YOUR-WRITES: a live inotify watcher re-indexes an edited file "
    "within ~seconds of a save — the normal freshness path. A periodic reconcile sweep "
    "(default ~10 min) is ONLY the backstop for events the watcher missed (downtime, "
    "queue overflow), not the edit-to-fresh latency. If you edit a file and "
    "IMMEDIATELY query it, you can race the embed window: pass "
    "lore_search_code(..., wait_for_fresh=True) — it bounded-waits for the in-flight "
    "file(s) matching your path filter, then serves fresh (or stale-flagged on timeout; "
    "it never hangs). Use lore_reindex(tier=...) only to force a whole tier current; "
    "for the edit-then-query case wait_for_fresh is the right, cheaper tool.\n"
    "\n"
    "MEMORY: lore_save_memory / lore_recall_memory is PROJECT-SCOPED memory about THIS "
    "repository — embedded and semantically recalled, SHARED across every agent working "
    "this "
    "project, and it SURVIVES restarts (it persists in a dedicated collection). Use it "
    "for durable facts and corrections about this codebase (e.g. 'the order total lives "
    "in models/sale.py, not where it looks'). This is DISTINCT from your own global / "
    "cross-project assistant memory: lore-memory is the project's shared notebook, not "
    "your personal one."
)


def configure_logging_from_config(config: LoreConfig) -> None:
    """Configure structured logging from the project config (env overrides level).

    The run-time precedence: ``LORE_LOG_LEVEL`` (an operator's env override) beats
    ``config.logging.level`` (the config default). The format is taken from
    ``config.logging.format``. Delegates to
    :func:`~loremaster.logging_setup.configure_logging`, which is idempotent and
    scopes its handlers to the lore namespace (it does not touch uvicorn's root
    logger).

    Args:
        config: The validated project configuration carrying the ``logging`` block.
    """
    from loremaster.logging_setup import configure_logging

    level = os.environ.get("LORE_LOG_LEVEL", config.logging.level)
    configure_logging(level=level, fmt=config.logging.format)


class ProbeGateError(RuntimeError):
    """Raised when the startup probe gate refuses to start the server.

    The message carries a remediation hint (what was observed vs expected, and —
    for a collection mismatch — that the index was left INTACT, never
    auto-recreated). The server must NOT come up when this is raised.
    """


class ReindexTierError(ValueError):
    """Raised when ``reindex(tier=...)`` is given a tier the project does not declare.

    Subclasses :class:`ValueError` (a bad argument value). The message NAMES the
    offending tier AND the valid tiers, so a typo (which would otherwise be
    silently ignored — a false-success sweep over every tier) is caught and
    remediable. ``tier=None`` (reindex all) never raises.
    """


async def run_probe_gate(*, embedder: Embedder, store: QdrantStore, config: LoreConfig) -> int:
    """Probe the embedder and verify dim coherence before the server starts.

    The gate (plan Deliverable 3 "startup probe gate"):

    1. ``await embedder.probe()`` — reaches the live endpoint (the embedder owns
       the connect timeout + fp32-warmup polling). A raise means the endpoint is
       unreachable → REFUSE.
    2. The observed dim must equal ``config.embedding.dim`` → else REFUSE (a
       wrong-dim deploy would silently corrupt retrieval).
    3. If the collection ALREADY exists, its vector size must equal
       ``config.embedding.dim`` → else REFUSE with a remediation message, leaving
       the collection INTACT. We NEVER auto-recreate — that silently nukes the
       index.

    Args:
        embedder: The active embedder to probe.
        store: The project's :class:`QdrantStore` (for the existing-collection dim).
        config: The validated project config (``embedding.dim`` is the source of
            truth the probe and collection must agree with).

    Returns:
        The observed embedding dimension (== ``config.embedding.dim`` on success).

    Raises:
        ProbeGateError: On an unreachable embedder, a probe/config dim mismatch, or
            an existing-collection size mismatch.
    """
    expected_dim = config.embedding.dim
    try:
        observed = await embedder.probe()
    except Exception as exc:  # noqa: BLE001 - any probe failure is "unreachable"
        # Reason carries the exception repr only — never the URL's secret or the
        # bearer; the base_url is non-secret and aids triage.
        reason = f"embedding endpoint unreachable during startup probe ({exc!r})"
        logger.error("startup.probe_gate.refuse", extra={"reason": reason})
        raise ProbeGateError(
            f"{reason}; refusing to start — verify {config.embedding.base_url!r} is up and the "
            f"key env {config.embedding.api_key_env!r} is set."
        ) from exc
    if observed != expected_dim:
        reason = f"probe dim {observed} != config.embedding.dim {expected_dim}"
        logger.error("startup.probe_gate.refuse", extra={"reason": reason})
        raise ProbeGateError(
            f"embedder reports dim {observed} but config.embedding.dim is {expected_dim}; "
            f"refusing to start — fix the config or the model before indexing (a wrong dim "
            f"silently corrupts retrieval)."
        )
    existing_dim = await store.collection_dim()
    if existing_dim is not None and existing_dim != expected_dim:
        reason = f"existing collection size {existing_dim} != config.embedding.dim {expected_dim}"
        logger.error("startup.probe_gate.refuse", extra={"reason": reason})
        raise ProbeGateError(
            f"existing collection {store.collection_name!r} has vector size {existing_dim} "
            f"but config.embedding.dim is {expected_dim}; refusing to start and leaving the "
            f"collection INTACT (never auto-recreated). Re-create it deliberately, or fix the "
            f"config to match, then reindex."
        )
    logger.info("startup.probe_gate.pass", extra={"observed_dim": observed})
    return observed


class AppContext:
    """The live runtime services bundle the MCP tools dispatch through.

    Built by :func:`build_app_context` after the probe gate passes. Holds every
    runtime service (embedder, stores, manifest, graph, the search pipeline, the
    read tools, the memory store, the indexer, the reconcile engine, the watcher)
    plus the spawned background tasks, and exposes one async HANDLER per MCP tool.
    The FastMCP tool functions are thin wrappers that fetch this context from the
    lifespan and call the matching handler — so the handlers are the single, fully
    end-to-end-testable surface (a test drives them directly with a FakeEmbedder +
    real Qdrant; the FastMCP tools just re-expose them).
    """

    def __init__(
        self,
        *,
        server: LoreServer,
        embedder: Embedder,
        store: QdrantStore,
        memory_store_handle: QdrantStore,
        manifest: Manifest,
        code_graph: CodeGraph,
        indexer: Indexer,
        reconcile_engine: ReconcileEngine,
        watcher: Any,
        search_pipeline: SearchPipeline,
        read_file_tool: ReadFileTool,
        symbol_tool: SymbolTool,
        memory_store: MemoryStore,
        qdrant_client: Any,
    ) -> None:
        self._server = server
        self._config: LoreConfig = server.config
        self.embedder = embedder
        self.store = store
        self._memory_store_handle = memory_store_handle
        self.manifest = manifest
        self.code_graph = code_graph
        self.indexer = indexer
        self.reconcile_engine = reconcile_engine
        self.watcher = watcher
        self.search_pipeline = search_pipeline
        self._read_file_tool = read_file_tool
        self._symbol_tool = symbol_tool
        self._memory_store = memory_store
        self._qdrant_client = qdrant_client
        # The parent extension context (per-extension namespaced state lives here),
        # set when the lifespan ran the startup hooks, so shutdown reuses it.
        self._extension_ctx: ExtensionContext | None = None
        # Background-task handles + a flag the tests/lifespan inspect.
        self.reconcile_task: Any = None
        self.watcher_started: bool = False

    # -- tool handlers (the single end-to-end surface) ---------------------

    async def search_code(
        self,
        query: str,
        k: int = _DEFAULT_SEARCH_K,
        filters: dict[str, str] | None = None,
        *,
        wait_for_fresh: bool = False,
        detail_level: str = "auto",
    ) -> list[SearchResult]:
        """Memory-boosted semantic search; returns summarised, cited results."""
        return await self.search_pipeline.search_code(
            query, k, filters, wait_for_fresh=wait_for_fresh, detail_level=detail_level
        )

    async def read_file(
        self,
        tier: str,
        path: str,
        line_start: int | None = None,
        line_end: int | None = None,
    ) -> FileSpan:
        """Read a containment-guarded ``(tier, path)`` span with a provenance header."""
        return self._read_file_tool.read_file(tier, path, line_start, line_end)

    async def get_symbol(self, qualified_name: str) -> ResolvedSymbol:
        """Resolve a qualified Python name to its exact stored definition + location."""
        return await self._symbol_tool.get_symbol(qualified_name)

    async def save_memory(
        self, text: str, *, metadata: dict[str, Any] | None = None
    ) -> str:
        """Persist a project-memory note; returns its deterministic id."""
        return await self._memory_store.save_memory(text, metadata=metadata)

    async def recall_memory(self, query: str, k: int = _DEFAULT_RECALL_K) -> list[RecalledMemory]:
        """Recall the nearest saved notes for ``query`` (summarised)."""
        return await self._memory_store.recall_memory(query, k)

    async def reindex(self, tier: str | None = None) -> IndexSummary:
        """Force a reconcile sweep (optionally one tier) and return the summary.

        Runs under the watcher's single-writer lock so it never races a live
        event's ``index_file`` — the read-your-writes / forced-refresh escape
        hatch. With no watcher running (the test path), reconciles directly.

        A given ``tier`` is VALIDATED against the project's configured tiers
        first: an unknown value raises :class:`ReindexTierError` naming the bad
        tier and the valid ones (a typo would otherwise be silently ignored — a
        sweep over every tier reporting false success). ``tier=None`` means all.

        Args:
            tier: Limit the sweep to one configured source tier, or ``None`` for
                every tier.

        Returns:
            The :class:`~loremaster.index.indexer.IndexSummary` for the sweep.

        Raises:
            ReindexTierError: If ``tier`` is given but is not a configured tier.
        """
        self._validate_tier(tier)
        if self.watcher is not None and self.watcher_started:
            await self.watcher.run_sweep()
            return self.indexer.index_status()
        return await self.reconcile_engine.reconcile()

    def _validate_tier(self, tier: str | None) -> None:
        """Reject a ``tier`` the project does not declare (fail loud on a typo).

        ``None`` (reindex all) is always valid. Otherwise ``tier`` must match one
        of the configured tiers (:attr:`~loremaster.config.LoreConfig.effective_roots`,
        which synthesises the single-tree default tier when ``roots:`` is empty);
        an unknown value raises :class:`ReindexTierError` naming the valid tiers.

        Args:
            tier: The requested tier, or ``None``.

        Raises:
            ReindexTierError: If ``tier`` is not ``None`` and is not configured.
        """
        if tier is None:
            return
        valid_tiers = [root.tier for root in self._config.effective_roots]
        if tier not in valid_tiers:
            valid = ", ".join(repr(name) for name in valid_tiers)
            raise ReindexTierError(
                f"unknown tier {tier!r}; reindex accepts only a configured tier "
                f"({valid}) or None (all tiers). Check for a typo, or omit the tier "
                f"to reconcile everything."
            )

    async def index_status(self) -> IndexSummary:
        """Return the freshness roll-up read purely from the manifest (zero embeds)."""
        return self.indexer.index_status()

    async def what_imports(self, target: str) -> list[GraphNode]:
        """Return the module nodes that import ``target`` (reverse import edge)."""
        return self.code_graph.what_imports(target)

    async def blast_radius(
        self,
        target: str,
        depth: int = _DEFAULT_BLAST_DEPTH,
        max_results: int = _DEFAULT_BLAST_MAX_RESULTS,
    ) -> list[GraphNode]:
        """Return the BOUNDED reverse-edge transitive closure from ``target``."""
        return self.code_graph.blast_radius(target, depth, max_results)

    async def tests_for(self, symbol_or_file: str) -> list[GraphNode]:
        """Return the test nodes related to a symbol or file."""
        return self.code_graph.tests_for(symbol_or_file)

    # -- extension tools (seam 3) ------------------------------------------

    @property
    def extension_ctx(self) -> ExtensionContext | None:
        """The RUNTIME :class:`ExtensionContext` the lifespan built over live services.

        Set once the startup hooks ran (so an extension's per-extension lifespan
        ``state`` is reachable through it). A seam-3 extension tool's registered
        wrapper resolves its handler against THIS context — the real embedder /
        store / manifest, not the composition placeholder — so a future
        external-connection extension's handler can reach an extension-owned
        resource stashed at startup.
        """
        return self._extension_ctx

    def extension_tool_handler(self, name: str) -> Callable[..., Any]:
        """Resolve the named extension tool's handler, bound to the RUNTIME context.

        Re-derives the extension tool specs over the live runtime
        :class:`ExtensionContext` (each extension's ``tools`` called with ITS
        per-extension child context, fix B — so the handler closes over the same
        private ``state`` namespace its lifespan hooks populate) and returns the
        handler whose tool ``name`` matches. The registered FastMCP wrapper calls
        this at invocation time, so the handler always closes over the live
        services, not a build-time placeholder.

        Args:
            name: The extension tool name to resolve.

        Returns:
            The matching :attr:`ToolSpec.handler` callable, bound to the runtime
            context.

        Raises:
            RuntimeError: If the runtime context is not yet set (called before the
                lifespan startup), or no registered extension tool has ``name``.
        """
        if self._extension_ctx is None:  # pragma: no cover - defensive
            raise RuntimeError(
                f"extension tool {name!r} invoked before the runtime context was built"
            )
        for spec in self._server.extension_tool_specs(self._extension_ctx):
            if spec.name == name:
                return spec.handler
        raise RuntimeError(f"no registered extension tool named {name!r}")  # pragma: no cover

    # -- lifecycle ---------------------------------------------------------

    async def aclose(self) -> None:
        """Stop background tasks, run extension shutdown hooks, close clients.

        Mirrors the lifespan teardown: the periodic reconcile task is cancelled,
        the watcher observer + worker are stopped, the extension ``on_shutdown``
        hooks run in reverse order, and the SQLite handles are closed. Idempotent
        enough to be called once at lifespan exit (or by a test's ``finally``).
        """
        if self.reconcile_task is not None:
            self.reconcile_task.cancel()
            try:
                await self.reconcile_task
            except asyncio.CancelledError:
                pass
            self.reconcile_task = None
        if self.watcher is not None and self.watcher_started:
            await self.watcher.stop()
            self.watcher_started = False
        if self._extension_ctx is not None:
            await self._server.run_shutdown_hooks(self._extension_ctx)
        self.manifest.close()
        self.code_graph.close()


async def build_app_context(
    *,
    server: LoreServer,
    embedder: Embedder,
    qdrant_client: Any,
    manifest_path: Path,
    graph_path: Path,
    snapshot_root: Path,
    start_tasks: bool = False,
) -> AppContext:
    """Run the probe gate, construct the runtime services, optionally spawn tasks.

    The dependency-injected core of the lifespan: every collaborator that the
    real lifespan builds from config (the embedder, the Qdrant client, the SQLite
    paths, the snapshot root) is a parameter, so a test wires a
    :class:`~loresigil.testing.FakeEmbedder` + a throwaway Qdrant collection and
    drives the SAME construction path the server runs.

    Sequence (plan Deliverable 3 lifespan):

    1. Build the project store (with extension-declared payload indexes) and run
       the **probe gate** (:func:`run_probe_gate`) — refuse on unreachable / dim
       mismatch (never auto-recreate). THEN ``ensure_collection`` at the config
       dim (and the memory collection).
    2. Construct the manifest, the code-graph, the embedder-injected indexer (with
       the graph wired in), the reconcile engine (with the graph), the memory
       store, the search pipeline, and the tier-aware read tools.
    3. Run the extension ``on_startup`` hooks — UNWINDING on partial failure (fix
       A): a failing hook aborts the build after tearing the started hooks down.
    4. When ``start_tasks``: start the live watcher and create the periodic
       reconcile asyncio task.

    Args:
        server: The composed :class:`LoreServer` (config + extensions).
        embedder: The active embedder (probed by the gate).
        qdrant_client: The async Qdrant client the stores share.
        manifest_path: SQLite manifest path.
        graph_path: SQLite code-graph path.
        snapshot_root: Static-tier snapshot root (also the read-file static base).
        start_tasks: When ``True``, start the watcher + periodic reconcile task.

    Returns:
        The fully-wired :class:`AppContext`.

    Raises:
        ProbeGateError: If the probe gate refuses.
        Exception: Re-raises a failing extension ``on_startup`` (after unwinding).
    """
    from loremaster.graph import CodeGraph
    from loremaster.index.indexer import Indexer
    from loremaster.index.manifest import Manifest
    from loremaster.index.reconcile import ReconcileEngine
    from loremaster.index.watcher import LiveWatcher
    from loremaster.memory.store import MemoryStore
    from loremaster.read_file import ReadFileTool
    from loremaster.search import SearchPipeline
    from loremaster.source.local_directory import LocalDirectorySourceProvider
    from loremaster.source.snapshot import SnapshotLayout
    from loremaster.store.qdrant import QdrantStore
    from loremaster.symbols import SymbolTool

    config = server.config
    slug = config.project.slug

    # 1) Store + probe gate + collection.
    store = QdrantStore(
        client=qdrant_client,
        slug=slug,
        extra_keyword_indexes=[
            spec.field_name for spec in server.payload_index_specs if spec.schema_type == "keyword"
        ],
        extra_bool_indexes=[
            spec.field_name for spec in server.payload_index_specs if spec.schema_type == "bool"
        ],
    )
    await run_probe_gate(embedder=embedder, store=store, config=config)
    await store.ensure_collection(config.embedding.dim)

    memory_store_handle = QdrantStore(client=qdrant_client, slug=f"{slug}{_MEMORY_SLUG_SUFFIX}")

    # 2) Core services.
    manifest = Manifest(str(manifest_path))
    code_graph = CodeGraph(str(graph_path))
    providers = _build_source_providers(server, config, LocalDirectorySourceProvider)
    indexer = Indexer(
        store=store,
        embedder=embedder,
        manifest=manifest,
        registry=server.registry,
        source_providers=providers,
        config=config,
        snapshot_root=snapshot_root,
        code_graph=code_graph,
    )
    reconcile_engine = ReconcileEngine(
        indexer=indexer, manifest=manifest, store=store, config=config, code_graph=code_graph
    )
    memory_store = MemoryStore(store=memory_store_handle, embedder=embedder)
    await memory_store.ensure_ready()
    # The RUNTIME extension context over the LIVE services — the real embedder,
    # manifest, and the embedder's working ``count_tokens`` (NOT the composition
    # placeholder from LoreServer.extension_context, whose embedder/manifest are
    # None and whose tokenizer refuses to count). The search pipeline carries this
    # so every context-taking search seam (4/5/6/11) sees functional services; the
    # SAME object is reused for the startup hooks below, so seam-9 ``state`` set at
    # startup is visible to the search seams.
    extension_ctx = ExtensionContext(
        store=store,
        embedder=embedder,
        config=config,
        count_tokens=embedder.count_tokens,
        manifest=manifest,
    )
    search_pipeline = SearchPipeline(
        store=store,
        embedder=embedder,
        server=server,
        manifest=manifest,
        config=config,
        extension_context=extension_ctx,
        memory_store=memory_store,
    )
    snapshot_layout = SnapshotLayout(snapshot_root)
    live_roots = {
        root.tier: Path(root.path)
        for root in config.effective_roots
        if root.path is not None
    }
    # Every configured tier (live + static) is "known", so read_file can tell an
    # unknown-tier typo apart from a known tier whose file is merely missing.
    known_tiers = {root.tier for root in config.effective_roots}
    read_file_tool = ReadFileTool(
        live_roots=live_roots, snapshot_layout=snapshot_layout, known_tiers=known_tiers
    )
    symbol_tool = SymbolTool(store=store)

    watcher = LiveWatcher(
        indexer=indexer,
        manifest=manifest,
        store=store,
        config=config,
        loop=asyncio.get_running_loop(),
        reconcile_engine=reconcile_engine,
        code_graph=code_graph,
    )

    app_context = AppContext(
        server=server,
        embedder=embedder,
        store=store,
        memory_store_handle=memory_store_handle,
        manifest=manifest,
        code_graph=code_graph,
        indexer=indexer,
        reconcile_engine=reconcile_engine,
        watcher=watcher,
        search_pipeline=search_pipeline,
        read_file_tool=read_file_tool,
        symbol_tool=symbol_tool,
        memory_store=memory_store,
        qdrant_client=qdrant_client,
    )

    # 3) Extension startup hooks (fix A: unwind on partial failure). Reuse the
    # parent extension context built above over the LIVE services so a hook can
    # reach them — and so the SAME object (with any seam-9 ``state`` a hook
    # stashes) is the one the search pipeline already carries.
    # Any failure from here on (a refusing hook, a watcher that won't start) must
    # not leak the just-opened SQLite handles: close the manifest + graph before
    # re-raising, so a half-built server never holds file handles open (the
    # owner's degradation rule). The extension unwind itself lives in
    # run_startup_hooks (fix A); this guards the resources it doesn't own.
    try:
        await server.run_startup_hooks(extension_ctx)
        app_context._extension_ctx = extension_ctx

        # 4) Background tasks (watcher + INITIAL reconcile + periodic reconcile).
        if start_tasks:
            await watcher.start()
            app_context.watcher_started = True
            logger.info("startup.watcher.started")
            # INITIAL reconcile on start (the on-demand "start = delta-reconcile"
            # lifecycle): a fresh start after offline edits must delta-index NOW,
            # not wait out the periodic interval (default 600s) — otherwise the
            # index serves stale content for up to that long. Run it through the
            # watcher's run_sweep so it (a) holds the single-writer lock, (b)
            # respects tier policy (live walked, static skipped on version-stamp),
            # and (c) rides the manifest mtime+size fast-path (cheap — mostly skips
            # after a cold index). Done BEFORE the periodic task is spawned so the
            # very first read after start is already current.
            initial_summary = await watcher.run_sweep()
            logger.info(
                "startup.reconcile.initial",
                extra={
                    "files_indexed": initial_summary.files_indexed,
                    "files_failed": initial_summary.files_failed,
                    "files_skipped": initial_summary.files_skipped,
                    "files_purged": initial_summary.files_purged,
                },
            )
            app_context.reconcile_task = asyncio.get_running_loop().create_task(
                _periodic_reconcile(watcher, config.watcher.reconcile_interval_s)
            )
    except BaseException:
        # Tear down whatever started, then close the SQLite handles (idempotent).
        if app_context.watcher_started:
            await watcher.stop()
        manifest.close()
        code_graph.close()
        raise

    return app_context


def _build_source_providers(server: LoreServer, config: LoreConfig, provider_cls: Any) -> list[Any]:
    """Compose the extensions' providers + a built-in provider per static root.

    The generic default for a ``static`` root is a ``LocalDirectorySourceProvider``
    over its configured ``source`` — unless an extension already contributed a
    provider for that tier (the deferred odoo podman extractor), which wins.
    """
    providers: list[Any] = list(server.source_providers)
    covered = {provider.tier for provider in providers}
    for root in config.roots:
        if root.watch == WATCH_STATIC and root.tier not in covered and root.source:
            providers.append(provider_cls(root.tier, Path(root.source)))
    return providers


async def _periodic_reconcile(watcher: Any, interval_s: int) -> None:
    """Run the reconcile sweep every ``interval_s`` seconds (under the watcher lock).

    The downtime / ``IN_Q_OVERFLOW`` backstop: the sweep re-walks the filesystem
    and re-discovers any change the live watcher dropped. Cancelled at shutdown.
    """
    while True:
        await asyncio.sleep(interval_s)
        await watcher.run_sweep()


class _ProcessLifespanGuard:
    """Run the heavy lifespan startup exactly ONCE per process across MCP sessions.

    FastMCP's streamable-http composition enters the user lifespan once per
    ``MCPServer.run`` — and the session manager calls that once per MCP SESSION
    (``StreamableHTTPSessionManager._handle_stateful_request`` → ``run_server`` →
    ``self.app.run`` → ``lifespan(self)``). So in ONE uvicorn process every new
    client session would otherwise re-run loremaster's heavy startup (probe gate →
    initial reconcile → watcher start), spawning a second watcher + a second
    startup reconcile (wasteful; two watchers risk manifest contention).

    This guard makes the heavy startup idempotent per process. Each session takes
    a reference-counted *lease*: the FIRST lease builds the shared
    :class:`AppContext` (Qdrant client + probe gate + watcher + tasks); every
    subsequent concurrent lease REUSES the same context (no second probe/watcher);
    and the LAST lease to release tears the context + client down. An ``asyncio``
    lock serialises the build/teardown so two sessions racing the first lease
    cannot both build. Sequential sessions (build → release-to-zero → a later
    session) correctly rebuild — the guard tracks "currently live", not
    "ever-built", so a clean process that drops to zero active sessions and later
    gets a new one still comes up.

    A build failure (e.g. the probe gate refusing) is NOT cached: the partial
    state is cleaned up and the next lease retries, so a transient embedder outage
    does not wedge the process into a permanently-broken context.
    """

    def __init__(self, build: Callable[[], Awaitable[tuple[AppContext, Any]]]) -> None:
        """Initialise the guard around a context-build coroutine factory.

        Args:
            build: A zero-arg async factory returning ``(app_context, client)`` —
                the heavy startup. Called at most once per live generation (under
                the lock), and only when no context is currently live.
        """
        self._build = build
        self._lock = asyncio.Lock()
        self._refcount = 0
        self._app_context: AppContext | None = None
        self._client: Any = None

    async def acquire(self) -> AppContext:
        """Take a lease, building the shared context on the first live lease.

        Returns:
            The shared per-process :class:`AppContext` (built once, reused by every
            concurrent session).

        Raises:
            Exception: Re-raises a build failure (the refcount is rolled back and
                nothing is cached, so a later lease retries).
        """
        async with self._lock:
            if self._app_context is None:
                # First live lease — run the heavy startup once. On failure leave
                # nothing live so the next session retries (no wedged process).
                self._app_context, self._client = await self._build()
            self._refcount += 1
            return self._app_context

    async def release(self) -> None:
        """Release a lease, tearing the shared context down on the last release.

        Idempotent at zero: extra releases never drive the refcount negative or
        double-close. The teardown mirrors the original lifespan ``finally`` —
        ``AppContext.aclose`` (tasks/watcher/hooks/SQLite) then the Qdrant client.
        """
        async with self._lock:
            if self._refcount == 0:
                return
            self._refcount -= 1
            if self._refcount > 0 or self._app_context is None:
                return
            app_context, client = self._app_context, self._client
            self._app_context = None
            self._client = None
        # Tear down OUTSIDE the lock so a teardown never blocks a concurrent
        # acquire racing the next generation; the fields are already cleared.
        await app_context.aclose()
        if client is not None:
            await client.close()


def build_mcp_server(server: LoreServer) -> Any:
    """Construct the FastMCP server: lifespan + the ten built-ins + extension tools.

    The lifespan builds the live :class:`AppContext` from config (the real
    embedder via :func:`~loremaster.embedding.make_embedder_from_config`, a real
    Qdrant client, the default SQLite paths, the snapshot root) and starts the
    watcher + reconcile tasks; teardown closes it. Each tool is a thin wrapper
    that fetches the :class:`AppContext` from the request's lifespan context and
    calls the matching handler — every tool returns a pydantic value object (a
    filtered/summarised shape), never a raw store dump.

    **Run-once guard.** FastMCP enters this lifespan once per MCP SESSION (the
    streamable-http session manager calls ``MCPServer.run`` — and the user
    lifespan — for every new client session), so a single uvicorn process would
    otherwise run the heavy startup (probe gate / initial reconcile / watcher
    start) once per session. A :class:`_ProcessLifespanGuard` makes that startup
    idempotent per process: the first session builds the shared
    :class:`AppContext`, every concurrent session reuses it, and the last session
    to exit tears it down — exactly one probe gate, one initial reconcile, and one
    watcher per container start regardless of how many sessions connect.

    Args:
        server: The composed :class:`LoreServer`.

    Returns:
        The configured :class:`~mcp.server.fastmcp.FastMCP` instance.
    """
    from collections.abc import AsyncIterator
    from contextlib import asynccontextmanager

    from qdrant_client import AsyncQdrantClient

    from loremaster.config import resolve_secret
    from loremaster.embedding import make_embedder_from_config

    config = server.config

    async def _build_context() -> tuple[AppContext, Any]:
        """Run the heavy startup once: build the Qdrant client + the AppContext.

        Returns:
            The built ``(app_context, client)`` pair the guard reuses across
            sessions and closes on the last release.
        """
        client = AsyncQdrantClient(
            url=config.qdrant.url, api_key=resolve_secret(config.qdrant.api_key_env)
        )
        try:
            app_context = await build_app_context(
                server=server,
                embedder=make_embedder_from_config(config.embedding),
                qdrant_client=client,
                manifest_path=_DEFAULT_MANIFEST_DIR / f"{config.project.slug}.db",
                graph_path=_DEFAULT_MANIFEST_DIR / f"{config.project.slug}.graph.db",
                snapshot_root=_DEFAULT_SNAPSHOT_ROOT,
                start_tasks=True,
            )
        except BaseException:
            # build_app_context tears down its own half-built state; we still own
            # the client it never adopted, so close it before the error propagates.
            await client.close()
            raise
        return app_context, client

    # ONE guard per built server → one shared heavy startup per process. Captured
    # by the per-session lifespan closure below.
    guard = _ProcessLifespanGuard(_build_context)

    @asynccontextmanager
    async def _lifespan(_mcp: FastMCP) -> AsyncIterator[AppContext]:
        # Configure structured logging FIRST so every startup event (probe gate,
        # initial reconcile, watcher start) is captured in the chosen format with
        # the redaction backstop in place. Env (LORE_LOG_LEVEL) overrides the
        # config level; idempotent and scoped to the lore namespace. (Cheap +
        # idempotent, so it is fine to re-run per session even though the heavy
        # startup behind the guard runs once.)
        configure_logging_from_config(config)
        # The guard runs the heavy startup once per PROCESS; this per-session enter
        # only takes/releases a lease (the second session reuses the first's
        # context — no second probe gate, watcher, or initial reconcile).
        app_context = await guard.acquire()
        try:
            yield app_context
        finally:
            await guard.release()

    mcp: FastMCP = FastMCP(
        name=f"lore-{config.project.slug}",
        instructions=_INSTRUCTIONS,
        lifespan=_lifespan,
        host=config.server.host,
        port=config.server.port,
        streamable_http_path=config.server.path,
    )
    _register_tools(mcp, server)
    return mcp


def _app_context(context: Context[Any, AppContext, Any]) -> AppContext:
    """Fetch the live :class:`AppContext` off a request's lifespan context."""
    return context.request_context.lifespan_context


# Tool annotations (mcp-builder: set readOnlyHint / idempotentHint / openWorldHint
# appropriately so a host can reason about a tool before calling it). Every lore
# tool is read-only EXCEPT save_memory (persists a note) and reindex (mutates the
# index state). openWorldHint is False throughout: lore queries THIS project's own
# closed index, not an open external world. The read tools are idempotent (same
# args → same observable result, modulo a live edit re-indexing underneath).
_READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True, idempotentHint=True, openWorldHint=False
)
# save_memory writes (a new note text creates a new point), so not read-only and
# not idempotent — re-saving the SAME text dedups by deterministic id, but a new
# text is a new write, so we do not advertise idempotency.
_SAVE_MEMORY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False
)
# reindex mutates index state (it re-embeds changed files into the store) but is
# non-destructive and idempotent over an unchanged tree (re-running settles to the
# same indexed state). Not read-only — it writes vectors.
_REINDEX_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False
)


def _register_tools(mcp: FastMCP, server: LoreServer) -> None:
    """Register the ten built-in MCP tools, then the extension-contributed tools.

    Kept separate so the registration list is one readable place. Every built-in
    tool pulls the live :class:`AppContext` off the request's lifespan context and
    calls the matching handler; the handler's pydantic return value is serialised
    to a plain dict/list (a filtered/summarised shape — never a raw store dump, the
    Anthropic token-efficiency rule).

    Each built-in tool carries (mcp-builder standard): a BEHAVIORAL description
    (what it returns, when to reach for it, how it differs from its neighbour), a
    per-parameter input-schema description via :class:`pydantic.Field` (constraints
    + an example where useful), and :class:`~mcp.types.ToolAnnotations` (read-only
    vs mutating). The consumer-facing ``instructions`` block (:data:`_INSTRUCTIONS`)
    carries the cross-tool model (freshness, citations, memory stance).

    After the ten built-ins, every registered :class:`Extension`'s seam-3
    :class:`ToolSpec`\\ s are registered as real FastMCP tools
    (:func:`_register_extension_tools`) — purely additive, with a name-collision
    guard so an extension tool can never silently shadow a built-in or another
    extension's tool.

    Args:
        mcp: The FastMCP server to register tools on.
        server: The composed :class:`LoreServer` whose extensions contribute the
            seam-3 tools.
    """

    @mcp.tool(
        name="lore_search_code",
        description=(
            "Semantic, memory-boosted search across THIS project's indexed code and "
            "docs. Your default entry point when you don't already know the exact "
            "symbol name or file path: it ranks by meaning, not by string match. "
            "Returns summarised, [SOURCE:file:line]-cited hits (each with a stable "
            "Key:), never a raw dump. For the EXACT definition of a name you already "
            "know, prefer lore_get_symbol; to read surrounding lines, follow up with "
            "lore_read_file."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def search_code(
        context: Context[Any, AppContext, Any],
        query: Annotated[
            str,
            Field(
                description=(
                    "Natural-language description of what you're looking for "
                    "(e.g. 'where the order total is computed'). Meaning-ranked, so "
                    "phrase it as intent, not an exact identifier."
                )
            ),
        ],
        k: Annotated[
            int,
            Field(
                ge=_MIN_COUNT,
                le=_MAX_SEARCH_K,
                description=(
                    f"Maximum number of hits to return (default {_DEFAULT_SEARCH_K}, "
                    f"min {_MIN_COUNT}, max {_MAX_SEARCH_K}). Raise it for a broad "
                    "survey, lower it to conserve context."
                ),
            ),
        ] = _DEFAULT_SEARCH_K,
        filters: Annotated[
            dict[str, str] | None,
            Field(
                description=(
                    "Optional server-side payload filters to scope the search, "
                    "e.g. {'tier': 'custom'} or {'path': 'pkg/router.py'}. A 'path' "
                    "(or 'file_path') filter is also what wait_for_fresh waits on. "
                    "Omit for an unscoped search."
                )
            ),
        ] = None,
        wait_for_fresh: Annotated[
            bool,
            Field(
                description=(
                    "Read-your-writes flush: when True, bounded-wait for the in-flight "
                    "file(s) matching your path filter to finish indexing before "
                    "searching (serves stale-flagged on timeout, never hangs). Set "
                    "True right after editing a file you're about to query; needs a "
                    "'path' filter to know what to wait on."
                )
            ),
        ] = False,
        detail_level: Annotated[
            DetailSelector,
            Field(
                description=(
                    "Which chunk granularity to return: 'auto' (default — both), "
                    "'summary' (signatures / imports / headings only), or 'source' "
                    "(bodies / statements only). Only these three values are accepted."
                )
            ),
        ] = "auto",
    ) -> list[SearchResult]:
        return await _app_context(context).search_code(
            query, k, filters, wait_for_fresh=wait_for_fresh, detail_level=detail_level
        )

    @mcp.tool(
        name="lore_read_file",
        description=(
            "Read the EXACT on-disk text of a file span with a [SOURCE:tier:path:"
            "start-end] provenance header — the anti-hallucination way to quote real "
            "lines. Reach for this after a lore_search_code / lore_get_symbol hit to "
            "read the surrounding context. Path is workspace-relative and "
            "containment-guarded (a '../' traversal, absolute path, or escaping "
            "symlink is rejected)."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def read_file(
        context: Context[Any, AppContext, Any],
        tier: Annotated[
            str,
            Field(
                description=(
                    "The source tier (root) the file lives in, as named in the "
                    "project config — e.g. a live tier like 'custom' for the watched "
                    "workspace, or a static tier (community / enterprise / pip / "
                    "stdlib). It is the 'tier' shown in a [SOURCE:tier:...] citation."
                )
            ),
        ],
        path: Annotated[
            str,
            Field(
                description=(
                    "Tier-relative path of the file (e.g. 'pkg/router.py'). "
                    "Workspace-relative and containment-guarded — never an absolute "
                    "path or a '../' escape."
                )
            ),
        ],
        line_start: Annotated[
            int | None,
            Field(
                description=(
                    "First line to read, 1-based inclusive. Omit to start at line 1."
                )
            ),
        ] = None,
        line_end: Annotated[
            int | None,
            Field(
                description=(
                    "Last line to read, 1-based inclusive. Omit to read to EOF; an "
                    "end past EOF is clamped (a tolerant 'from line N onward' read)."
                )
            ),
        ] = None,
    ) -> FileSpan:
        return await _app_context(context).read_file(tier, path, line_start, line_end)

    @mcp.tool(
        name="lore_get_symbol",
        description=(
            "Resolve a Python symbol name to its EXACT stored definition + on-disk "
            "location (file_path / line span / tier). Use this — NOT lore_search_code "
            "— when you know the name and want the authoritative definition: it is "
            "collision-correct (a module-qualified name resolves the RIGHT file when "
            "the bare name exists in several), where lore_search_code is a fuzzy "
            "ranked guess. Scoped to class / method / function chunks; raises a clean "
            "not-found (naming the symbol) if nothing matches."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def get_symbol(
        context: Context[Any, AppContext, Any],
        qualified_name: Annotated[
            str,
            Field(
                description=(
                    "A Python dotted name — either MODULE-QUALIFIED "
                    "(e.g. 'loremaster.config.LoreConfig' or "
                    "'loremaster.symbols.SymbolTool.get_symbol') or a BARE identity "
                    "(e.g. 'LoreConfig', 'SymbolTool.get_symbol'). Module-qualify it "
                    "to disambiguate a name that collides across files."
                )
            ),
        ],
    ) -> ResolvedSymbol:
        return await _app_context(context).get_symbol(qualified_name)

    @mcp.tool(
        name="lore_save_memory",
        description=(
            "Persist a durable note to THIS project's shared memory store; returns "
            "its deterministic id. Use it to record a lasting fact or correction "
            "about this codebase — it is embedded, semantically recalled by "
            "lore_recall_memory, SHARED across every agent on this project, and "
            "survives restarts. Re-saving the same text dedups (same id). This is the "
            "project's shared notebook, distinct from your own cross-project memory."
        ),
        annotations=_SAVE_MEMORY_ANNOTATIONS,
    )
    async def save_memory(
        context: Context[Any, AppContext, Any],
        text: Annotated[
            str,
            Field(
                description=(
                    "The note to remember — a durable fact or correction about this "
                    "project (e.g. 'the discount logic lives in pricing/rules.py, not "
                    "sale.py'). Make it self-contained so a future recall is useful."
                )
            ),
        ],
        metadata: Annotated[
            dict[str, Any] | None,
            Field(
                description=(
                    "Optional structured metadata stored alongside the note "
                    "(e.g. {'topic': 'pricing'}). Pass a chunk Key: here to pin the "
                    "note to a specific indexed chunk. Omit if none."
                )
            ),
        ] = None,
    ) -> str:
        return await _app_context(context).save_memory(text, metadata=metadata)

    @mcp.tool(
        name="lore_recall_memory",
        description=(
            "Recall the nearest saved project-memory notes for a query — the read "
            "side of lore_save_memory. Returns summarised notes (text + metadata + "
            "refs + score) from THIS project's shared, restart-surviving memory. Query "
            "it early when you want prior corrections or durable facts about this "
            "codebase before you start searching the code itself."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def recall_memory(
        context: Context[Any, AppContext, Any],
        query: Annotated[
            str,
            Field(
                description=(
                    "Natural-language description of the fact you're trying to recall "
                    "(e.g. 'where does pricing live'). Semantically matched against "
                    "saved notes."
                )
            ),
        ],
        k: Annotated[
            int,
            Field(
                ge=_MIN_COUNT,
                le=_MAX_RECALL_K,
                description=(
                    f"Maximum number of notes to return (default {_DEFAULT_RECALL_K}, "
                    f"min {_MIN_COUNT}, max {_MAX_RECALL_K})."
                ),
            ),
        ] = _DEFAULT_RECALL_K,
    ) -> list[RecalledMemory]:
        return await _app_context(context).recall_memory(query, k)

    @mcp.tool(
        name="lore_reindex",
        description=(
            "Force a reconcile sweep that re-indexes any changed files NOW and "
            "returns the freshness summary. This is the heavy 'make everything "
            "current' hammer over a whole tier (or all tiers) — NOT a per-file wait. "
            "You rarely need it: the live watcher keeps the index fresh on save. For "
            "the edit-then-immediately-query case, prefer "
            "lore_search_code(..., wait_for_fresh=True), which is cheaper and targeted."
        ),
        annotations=_REINDEX_ANNOTATIONS,
    )
    async def reindex(
        context: Context[Any, AppContext, Any],
        tier: Annotated[
            str | None,
            Field(
                description=(
                    "Limit the sweep to one source tier (e.g. 'custom'). Omit (None) "
                    "to reconcile every tier."
                )
            ),
        ] = None,
    ) -> IndexSummary:
        return await _app_context(context).reindex(tier)

    @mcp.tool(
        name="lore_index_status",
        description=(
            "Return the index freshness + health roll-up (files indexed / in-flight "
            "/ failed counts) read straight from the manifest — zero embeds, cheap. "
            "Use it to check whether the index is current and healthy before "
            "trusting a search, or to confirm a lore_reindex settled. Takes no "
            "arguments."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def index_status(context: Context[Any, AppContext, Any]) -> IndexSummary:
        return await _app_context(context).index_status()

    @mcp.tool(
        name="lore_what_imports",
        description=(
            "Return the DIRECT importers of a target module — the modules one "
            "reverse import edge away. Use it to answer 'who imports this?'. For the "
            "full TRANSITIVE ripple (importers of importers, bounded), use "
            "lore_blast_radius instead."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def what_imports(
        context: Context[Any, AppContext, Any],
        target: Annotated[
            str,
            Field(
                description=(
                    "The imported module's dotted path (e.g. 'pkg.router') or an "
                    "importable name. Returns the modules that import it directly."
                )
            ),
        ],
    ) -> list[GraphNode]:
        return await _app_context(context).what_imports(target)

    @mcp.tool(
        name="lore_blast_radius",
        description=(
            "Return the bounded TRANSITIVE reverse-dependency closure of a symbol or "
            "module — everything that could be affected if you change it, following "
            "reverse edges up to 'depth' hops (capped at 'max_results'). Answers "
            "'what could a change here break?'. Use this over lore_what_imports when "
            "you need the ripple, not just the immediate importers."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def blast_radius(
        context: Context[Any, AppContext, Any],
        target: Annotated[
            str,
            Field(
                description=(
                    "The symbol or module to start from — a dotted name "
                    "(e.g. 'pkg.router.ChampionRouter' or 'pkg.router'). Traversal "
                    "follows reverse-dependency edges outward from here."
                )
            ),
        ],
        depth: Annotated[
            int,
            Field(
                ge=_MIN_COUNT,
                le=_MAX_BLAST_DEPTH,
                description=(
                    f"Maximum number of reverse-edge hops to follow (default "
                    f"{_DEFAULT_BLAST_DEPTH}, min {_MIN_COUNT}, max "
                    f"{_MAX_BLAST_DEPTH}). Higher = a wider ripple; bounded to keep "
                    "the result from blowing up the context budget."
                ),
            ),
        ] = _DEFAULT_BLAST_DEPTH,
        max_results: Annotated[
            int,
            Field(
                ge=_MIN_COUNT,
                le=_MAX_BLAST_MAX_RESULTS,
                description=(
                    f"Hard cap on the number of nodes returned (default "
                    f"{_DEFAULT_BLAST_MAX_RESULTS}, min {_MIN_COUNT}, max "
                    f"{_MAX_BLAST_MAX_RESULTS}), so a pathological fan-out stays "
                    "bounded."
                ),
            ),
        ] = _DEFAULT_BLAST_MAX_RESULTS,
    ) -> list[GraphNode]:
        return await _app_context(context).blast_radius(target, depth, max_results)

    @mcp.tool(
        name="lore_tests_for",
        description=(
            "Return the test nodes related to a symbol or file (via graph edges and "
            "a naming heuristic). Use it to find the tests covering code you're about "
            "to change, or to locate where a behavior is exercised. Returns a "
            "well-formed (possibly empty) list — never an error when nothing matches."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def tests_for(
        context: Context[Any, AppContext, Any],
        symbol_or_file: Annotated[
            str,
            Field(
                description=(
                    "A symbol's dotted name (e.g. 'pkg.router.ChampionRouter') or a "
                    "tier-relative file path (e.g. 'pkg/router.py') whose tests you "
                    "want."
                )
            ),
        ],
    ) -> list[GraphNode]:
        return await _app_context(context).tests_for(symbol_or_file)

    # After the ten built-ins, register the extension-contributed seam-3 tools.
    _register_extension_tools(mcp, server)


# The parameter name FastMCP reserves to inject the request :class:`Context` on the
# registered tool wrapper. A ToolSpec handler that ALSO declares a parameter named
# this would collide with the injected one (a cryptic FastMCP-internal "duplicate
# parameter name" crash); the registration path refuses it loudly instead.
_RESERVED_TOOL_PARAM = "context"


def _register_extension_tools(mcp: FastMCP, server: LoreServer) -> None:
    """Register each extension's seam-3 :class:`ToolSpec` as a live FastMCP tool.

    For every :class:`ToolSpec` an extension contributes (collected over the
    composition context purely for its STATIC metadata — name / description /
    input schema), a FastMCP tool is registered whose:

    * **parameters** are derived from :attr:`ToolSpec.input_schema` (translated via
      :func:`_extension_tool_wrapper` into a typed signature FastMCP introspects),
      so the consumer sees the declared args; and
    * **body**, at invocation time, fetches the live :class:`AppContext` off the
      request's lifespan context, resolves the handler bound to the RUNTIME
      :class:`ExtensionContext` (real embedder / store / manifest, plus the
      per-extension lifespan ``state``), and invokes it with the call's arguments.

    The handler is resolved at CALL time (not captured here) precisely because the
    runtime context does not exist until the lifespan startup runs — registering a
    thin wrapper now and binding the live handler later threads the runtime context
    through cleanly without blocking the later resource-channel seam.

    **Name-collision guard.** A tool whose name already exists on ``mcp`` — a
    built-in or an earlier extension's tool — raises a :class:`ValueError` at
    registration rather than silently shadowing it (FastMCP's own ``add_tool``
    would merely warn and keep the first registration, a silent shadow).

    Args:
        mcp: The FastMCP server (the ten built-ins are already registered).
        server: The composed :class:`LoreServer` whose extensions contribute tools.

    Raises:
        ValueError: If an extension tool name collides with an already-registered
            tool (a built-in or another extension's tool).
    """
    # Enumerate the specs over the COMPOSITION context for their static metadata
    # (names / descriptions / input schemas do not depend on the runtime ctx; only
    # the handler closure does, and that is resolved per-call against the live
    # AppContext). A placeholder store handle suffices — the metadata pass never
    # invokes the handler or the placeholder tokenizer.
    composition_ctx = server.extension_context(store=None)
    for spec in server.tool_specs(composition_ctx):
        if mcp._tool_manager.get_tool(spec.name) is not None:  # noqa: SLF001
            raise ValueError(
                f"extension tool {spec.name!r} collides with an already-registered tool; "
                f"refusing to shadow it on the MCP surface (rename the extension tool — a "
                f"tool name must be unique across the ten built-ins and every extension)."
            )
        wrapper = _extension_tool_wrapper(spec)
        mcp.add_tool(wrapper, name=spec.name, description=spec.description)


# The parameter kinds an extension tool handler may declare and have faithfully
# republished. ``*args`` / ``**kwargs`` / positional-only cannot be modelled as a
# named, typed JSON-schema property, so a handler using them is refused loudly
# rather than published with a wrong (or silently dropped) schema.
_SUPPORTED_PARAM_KINDS = frozenset(
    {inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY}
)


def _extension_tool_wrapper(spec: ToolSpec) -> Callable[..., Awaitable[Any]]:
    """Build the FastMCP tool function for an extension :class:`ToolSpec`.

    The published ``inputSchema`` MUST match what the handler actually accepts —
    silently telling a consumer the wrong type or a wrong required-set is the worst
    MCP failure class. The handler's own signature is the single source of truth, so
    this introspects :attr:`ToolSpec.handler` and threads each parameter's real
    annotation + default + kind onto the wrapper's constructed signature:

    * a parameter WITH a default publishes as NOT required (the consumer may omit
      it; the handler supplies the default);
    * a parameter WITHOUT a default stays required;
    * the real annotation is preserved, so container/complex types
      (``list[str]`` → ``array``, ``dict`` → ``object``, a pydantic model → its
      schema) publish their correct JSON-schema type rather than collapsing to
      ``string``.

    The ``input_schema`` mapping on the spec is now SUPPLEMENTAL description only
    (its keys/values no longer drive type or optionality) — the live signature wins.

    Fail-loud (never silently coerce):

    * a parameter named :data:`_RESERVED_TOOL_PARAM` collides with the injected
      request ``context`` → raise (a clear error, not FastMCP's cryptic internal
      "duplicate parameter name");
    * an UN-annotated parameter would be silently published as ``string`` → raise
      (FastMCP defaults a bare param to ``type: string``, the silent-wrong-schema
      hazard);
    * a ``*args`` / ``**kwargs`` / positional-only parameter cannot be modelled as a
      named JSON-schema property → raise.

    Args:
        spec: The declarative tool spec to wrap.

    Returns:
        An async function suitable for :meth:`FastMCP.add_tool`, whose signature
        mirrors the handler's so the published schema matches what it accepts.

    Raises:
        ValueError: If the handler declares a reserved ``context`` parameter, an
            un-annotated parameter, or an unsupported parameter kind — each message
            names the offending :class:`ToolSpec` and field.
    """

    async def _tool(context: Context[Any, AppContext, Any], **kwargs: Any) -> Any:
        handler = _app_context(context).extension_tool_handler(spec.name)
        result = handler(**kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    # The leading ``context`` parameter (FastMCP injects the request Context here,
    # NOT a consumer-visible arg), then one parameter PER HANDLER PARAMETER —
    # annotation + default + kind carried verbatim so the published schema matches.
    parameters: list[inspect.Parameter] = [
        inspect.Parameter(
            _RESERVED_TOOL_PARAM,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Context,
        )
    ]
    annotations: dict[str, Any] = {_RESERVED_TOOL_PARAM: Context, "return": Any}
    handler_signature = inspect.signature(spec.handler)
    for param in handler_signature.parameters.values():
        if param.name == _RESERVED_TOOL_PARAM:
            raise ValueError(
                f"extension tool {spec.name!r} handler declares a parameter named "
                f"{_RESERVED_TOOL_PARAM!r}, which is reserved for the injected request "
                f"context; rename that handler parameter."
            )
        if param.kind not in _SUPPORTED_PARAM_KINDS:
            raise ValueError(
                f"extension tool {spec.name!r} handler parameter {param.name!r} has "
                f"unsupported kind {param.kind.description!r}; an extension tool's inputs "
                f"must be named, typed parameters (no *args/**kwargs/positional-only) so "
                f"the published schema can faithfully describe them."
            )
        if param.annotation is inspect.Parameter.empty:
            raise ValueError(
                f"extension tool {spec.name!r} handler parameter {param.name!r} has no type "
                f"annotation; an un-annotated parameter would be silently published as a "
                f"string in the tool's input schema. Annotate it so the consumer sees the "
                f"correct type."
            )
        # KEYWORD_ONLY on the wrapper so FastMCP/pydantic builds named properties
        # regardless of the handler's original positional/keyword kind; the default
        # (present or absent) is what drives required vs optional in the schema.
        parameters.append(
            inspect.Parameter(
                param.name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=param.annotation,
                default=param.default,
            )
        )
        annotations[param.name] = param.annotation
    _tool.__signature__ = inspect.Signature(parameters)  # type: ignore[attr-defined]
    _tool.__annotations__ = annotations
    _tool.__name__ = spec.name
    _tool.__doc__ = spec.description
    return _tool


def build_asgi_app(mcp: Any, config: LoreConfig) -> Any:
    """Assemble the streamable-http ASGI app, Bearer-gated when auth is enabled.

    The single place the served app is built and (conditionally) gated: when an
    ``auth`` block is configured AND enabled (D9/D11), the streamable-http app is
    wrapped in :class:`~loremaster.auth.BearerAuthMiddleware` over the configured
    named-key set; otherwise it is returned ungated (the no-auth localhost mode).

    Args:
        mcp: The FastMCP server (its ``streamable_http_app`` is the inner app).
        config: The project config (its ``auth`` block decides the gating).

    Returns:
        The ASGI app to serve (the raw streamable-http app, or the gated wrapper).
    """
    app = mcp.streamable_http_app()
    if config.auth is not None and config.auth.enabled:
        from loremaster.auth import BearerAuthMiddleware, build_api_key_verifier

        return BearerAuthMiddleware(app, build_api_key_verifier(config.auth))
    return app


def main(argv: list[str] | None = None) -> int:
    """``python -m loremaster.server`` entry: load config, build, serve.

    Args:
        argv: Optional explicit argument vector (for tests); defaults to
            ``sys.argv[1:]``. Accepts ``--config <path>`` (defaults to the
            ``LORE_CONFIG`` env var, mirroring the container's
            ``-e LORE_CONFIG=/workspace/lore.yaml``).

    Returns:
        Process exit code (``0``; serving is blocking, so this returns on a clean
        shutdown).
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="loremaster.server",
        description="Serve a project's lore RAG over FastMCP streamable-http.",
    )
    parser.add_argument(
        "--config",
        default=os.environ.get("LORE_CONFIG"),
        help="Path to the project lore.yaml (default: $LORE_CONFIG).",
    )
    args = parser.parse_args(argv)
    if not args.config:
        parser.error("no config: pass --config or set LORE_CONFIG")
    LoreServer.from_config(args.config).run()
    return 0


# Default SQLite manifest/graph dir + static-tier snapshot root (plan D8). Kept in
# sync with the batch indexer CLI's defaults so the server and the indexer share
# one ledger + snapshot location for a slug.
_DEFAULT_MANIFEST_DIR = Path.home() / ".local" / "state" / "lore"
_DEFAULT_SNAPSHOT_ROOT = Path.home() / "docker" / "mcp" / "lore-snapshot"


def _no_tokenizer(texts: Sequence[str]) -> list[int]:
    """Placeholder token counter for a composition-only context.

    The composition layer does not embed; the later server build injects the real
    embedder's ``count_tokens``. This refuses to be used silently.

    Raises:
        NotImplementedError: Always — wired by the later server build.
    """
    raise NotImplementedError(
        "ExtensionContext.count_tokens is wired by the later FastMCP server build"
    )


# The ``__main__`` guard MUST be the LAST top-level statement in this module.
# Run as ``python -m loremaster.server`` it fires ``sys.exit(main())`` and main()
# blocks in uvicorn, so ANY module-level def/binding placed AFTER it never
# executes in the running process. That is exactly the bug that left
# ``_no_tokenizer`` unbound → ``search_code`` NameError'd in the container while
# every import-based test passed (the def is bound on import). Keep this last;
# ``test_main_guard_is_last_top_level_statement`` enforces it.
if __name__ == "__main__":
    import sys

    sys.exit(main())
