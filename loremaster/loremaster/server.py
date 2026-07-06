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
import contextlib
import importlib.metadata
import inspect
import json
import logging
import math
import os
from collections.abc import Awaitable, Callable, Iterable, MutableMapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, cast

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
from pydantic import BaseModel, ConfigDict, Field

from loremaster.config import WATCH_LIVE, WATCH_STATIC, LoreConfig, load_config
from loremaster.extension import (
    DEFAULT_KEY_VERSION,
    DetailLevel,
    Extension,
    ExtensionContext,
    FieldIndexSpec,
    ToolSpec,
)
from loremaster.findings import DEFAULT_KIND as _DEFAULT_FINDING_KIND

# The consumer-visible tool RETURN models, imported at RUNTIME (not just under
# TYPE_CHECKING): each built-in tool wrapper is annotated with its real model
# return type so FastMCP derives a FIELD-LEVEL outputSchema + structuredContent
# (mcp-builder structured-output standard). FastMCP resolves a wrapper's return
# annotation via ``get_type_hints`` at registration time, so these names MUST live
# in this module's runtime namespace — a TYPE_CHECKING-only import would resolve to
# nothing and silently fall back to an opaque schema. None of these modules import
# ``server`` at runtime (only under TYPE_CHECKING), so the import is acyclic.
from loremaster.graph import (
    DEFAULT_DEAD_CODE_MAX_RESULTS,
    MAX_DEAD_CODE_MAX_RESULTS,
    DeadCodeNode,
)
from loremaster.impact import _DEFAULT_MAX_CONSUMERS as _IMPACT_DEFAULT_MAX_CONSUMERS
from loremaster.impact import _DEPTH_MAX as _IMPACT_DEPTH_MAX
from loremaster.impact import _DEPTH_MIN as _IMPACT_DEPTH_MIN

# P6-tail (lore_impact / lore_map): ImpactEngine/MapEngine and their scalar
# result models. The bound/cap constants are IMPORTED (not re-typed) from the
# engines' own modules -- single source of truth for the tool-surface Field
# constraints below (mirrors the ``_PYTHON_SUFFIX as PYTHON_SUFFIX`` pattern
# already used for the indexer's constant just below).
from loremaster.impact import ImpactEngine, ImpactResult
from loremaster.index.indexer import _PYTHON_SUFFIX as PYTHON_SUFFIX
from loremaster.index.indexer import IndexSummary
from loremaster.map import _BUDGET_CAP as _MAP_BUDGET_CAP
from loremaster.map import _BUDGET_DEFAULT as _MAP_DEFAULT_BUDGET
from loremaster.map import _BUDGET_FLOOR as _MAP_BUDGET_FLOOR
from loremaster.map import MapEngine, MapResult

# P7 memory cutover: the memory + task tool handlers speak the SurrealDB-backed
# wire vocabulary. ``IMPORTANCE_DEFAULTS_BY_KIND`` is the single source of truth
# for the valid memory-kind set + the by-kind importance defaults; ``MemorySource``
# is built at runtime when a save carries an explicit ``trust``.
from loremaster.memory.backend import (
    IMPORTANCE_DEFAULTS_BY_KIND,
    MemorySource,
    TrustLevel,
)
from loremaster.search import DetailSelector, SearchResult
from loremaster.store.candidate import Candidate
from loremaster.store_read import StoreFileSpan
from loremaster.symbols import VERIFY_REBUILD_CAVEAT, ResolvedSymbol, VerifyResult

if TYPE_CHECKING:
    from loresigil.base import Embedder

    from loremaster.calibration.engine import CalibrationEngine
    from loremaster.diff import DiffEngine, SnapshotSummary
    from loremaster.findings import ChainHead, Finding, FindingLedger
    from loremaster.graph_surreal import SurrealCodeGraph
    from loremaster.index.indexer import Indexer
    from loremaster.index.reconcile import ReconcileEngine
    from loremaster.index.surreal_manifest import SurrealManifest
    from loremaster.memory.backend import (
        ExistingChunksFn,
        MemoryBackend,
        RecalledMemory,
    )
    from loremaster.search import SearchPipeline
    from loremaster.store.surreal import SurrealStore
    from loremaster.store_read import StoreReadTool
    from loremaster.symbols import SymbolTool, VerifyTool
    from loremaster.tasks import ClaimResult, Task, TaskLedger

# The parent-context ``state`` key under which the per-extension lifespan-state
# namespaces live (fix B / §A1.10). ``ctx.state[_EXTENSION_STATE_KEY][name]`` is
# extension ``name``'s private state dict; the leading double underscore keeps it
# from colliding with a key an extension itself writes into its OWN namespace.
_EXTENSION_STATE_KEY = "__extension_state__"

logger = logging.getLogger(__name__)

# The env var the container build bakes `git describe --tags --always --dirty`
# into at image-build time, and the installed distribution name the metadata
# fallback resolves. Named so the producer↔consumer seam (image build → running
# server) reads the SAME string in both places. ``UNKNOWN_VERSION`` is the
# degrade-don't-crash sentinel when neither source yields a version.
_LORE_VERSION_ENV = "LORE_VERSION"
_LOREMASTER_DIST_NAME = "loremaster"
UNKNOWN_VERSION = "unknown"


def _resolve_version() -> str:
    """The lore server version, baked at container-build time.

    Precedence: the ``LORE_VERSION`` env (set from `git describe` in the image at
    build time) wins; else the installed package metadata; else ``"unknown"``.
    An empty ``LORE_VERSION`` falls through (a blank build-arg must not win).
    """
    baked = os.environ.get(_LORE_VERSION_ENV)
    if baked:  # non-empty wins; an empty mis-bake falls through
        return baked
    try:
        # Attribute access (not a bound local) so a monkeypatched
        # ``importlib.metadata.version`` is honoured.
        return importlib.metadata.version(_LOREMASTER_DIST_NAME)
    except importlib.metadata.PackageNotFoundError:
        # No installed dist (e.g. a bare source tree) — degrade, don't crash.
        return UNKNOWN_VERSION


# The module-level constant: the resolver's value for the import-time env.
__version__ = _resolve_version()

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

# The ``lore.yaml`` ``chunkers`` block projects onto the registry's override
# seam: each ENTRY is ``extension -> inner mapping`` and the boot wiring reads
# ONLY the inner ``chunker`` key naming a registered chunker (permissive-ignore
# -- extra inner keys are tolerated). Both names are the operator-facing yaml
# identifiers the loud-failure messages must cite so a fix is a one-step edit.
_CHUNKERS_CONFIG_FIELD: str = "chunkers"
_CHUNKER_INNER_KEY: str = "chunker"

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
        self._payload_index_specs: list[FieldIndexSpec] = []
        self._source_providers: list[Any] = []
        # Validated per-extension config slices (seam 7), keyed by extension name.
        self._extension_configs: dict[str, BaseModel] = {}
        # The registry, built with the base chunkers + (initially no) profiles.
        self._registry = ChunkerRegistry()
        self._build_default_registry()
        # Route the ``lore.yaml`` ``chunkers`` block onto the now-populated
        # registry: ordering matters -- the override targets (e.g. ``python_ast``)
        # only exist AFTER ``_build_default_registry()``, so the wiring runs last.
        self._apply_config_chunker_overrides()

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

    def _apply_config_chunker_overrides(self) -> None:
        """Project ``config.chunkers`` onto the registry's ``apply_overrides`` seam.

        The ``lore.yaml`` ``chunkers`` block maps a file extension to an inner
        mapping carrying a ``chunker`` key that names an already-registered
        chunker. This projects each entry to ``{extension: inner["chunker"]}`` and
        hands the WHOLE batch to :meth:`ChunkerRegistry.apply_overrides` in a
        single call, so its two-pass validation gives all-or-nothing atomicity (a
        single bad target leaves the routing table untouched). Only ``chunker`` is
        read; any extra inner keys are tolerated and ignored (permissive-ignore),
        and the source mappings are never mutated (no popping) so the block folds
        into the embedding-schema fingerprint verbatim.

        An empty block is a no-op. Failures are LOUD at construction:

        Raises:
            ValueError: If an inner mapping is missing the required ``chunker``
                key (message names the extension and the key), or if an override
                targets a chunker key that was never registered -- the registry's
                ``KeyError`` is wrapped as a ``ValueError`` naming the yaml field,
                the offending extension, and the offending key.
        """
        # Project extension -> inner["chunker"], failing loud on a missing key so
        # the operator sees ``chunker`` by name rather than a downstream
        # ``None is unregistered`` confusion.
        projected_overrides: dict[str, str] = {}
        for extension, inner in self._config.chunkers.items():
            if _CHUNKER_INNER_KEY not in inner:
                raise ValueError(
                    f"config field {_CHUNKERS_CONFIG_FIELD!r} entry for extension "
                    f"{extension!r} is missing the required {_CHUNKER_INNER_KEY!r} key "
                    f"naming a registered chunker."
                )
            projected_overrides[extension] = inner[_CHUNKER_INNER_KEY]
        # One call for all-or-nothing atomicity. The registry raises a bare
        # KeyError on an unregistered target; wrap-and-rename it (precedent:
        # ``load_config``, config.py:620) into a ValueError that also cites the yaml
        # field the operator edits (the KeyError already names the extension/key).
        try:
            self._registry.apply_overrides(projected_overrides)
        except KeyError as error:
            raise ValueError(
                f"config field {_CHUNKERS_CONFIG_FIELD!r}: {error.args[0]}"
            ) from error

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
    def payload_index_specs(self) -> list[FieldIndexSpec]:
        """The extension-declared extra field indexes (seam 8), in registration order."""
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

    def format_result(self, result: Candidate, ctx: ExtensionContext) -> str | None:
        """Resolve the citation/format for a result (seam 5).

        The first registered extension whose ``format_result`` returns a non-
        ``None`` string wins; if none claims it, returns ``None`` so the caller
        uses the base default citation format.

        P6 read-path cutover (§6 item 3): the seam formats the backend-neutral
        :class:`~loremaster.store.candidate.Candidate`, never a ``ScoredPoint``.

        Args:
            result: The candidate hit to format.
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
        self, query: str, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
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
        self, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
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

# Default ``k`` for the search/recall tools when the caller does not specify one.
_DEFAULT_SEARCH_K = 8
_DEFAULT_RECALL_K = 5

# Lower/upper bounds the numeric tool params publish (mcp-builder: constrain inputs
# at the schema, so a zero/negative or absurd value is rejected at validation rather
# than producing a confusing empty/over-large result). A count or hop-depth below 1
# is meaningless; the upper caps keep a single call's result + traversal bounded so a
# typo (k=100000) cannot blow the context budget.
# P8d Wave 2: _DEFAULT_BLAST_DEPTH/_DEFAULT_BLAST_MAX_RESULTS/_MAX_BLAST_DEPTH/
# _MAX_BLAST_MAX_RESULTS were REMOVED here — lore_blast_radius folded into
# lore_impact, whose own depth bound is _IMPACT_DEPTH_MIN/_IMPACT_DEPTH_MAX.
_MIN_COUNT = 1
_MAX_SEARCH_K = 100
_MAX_RECALL_K = 100
# The memory collection's slug suffix → ``lore_<slug>_memory``.
_MEMORY_SLUG_SUFFIX = "_memory"

# P7 memory cutover — the valid memory-kind vocabulary + the default kind a bare
# ``remember`` records. Derived from the backend's by-kind importance table so
# the two never drift; a kind outside this set is a caller error the handler
# rejects BY NAME (never a silent default to ``fact``).
_VALID_MEMORY_KINDS = frozenset(IMPORTANCE_DEFAULTS_BY_KIND)
_DEFAULT_MEMORY_KIND = "fact"
# The provenance ``kind`` a save carries when the caller marks an explicit
# ``trust`` but no richer source (an operator note — matches the local backend's
# own default source kind).
_MEMORY_SOURCE_KIND_OPERATOR = "operator"
# lore denominates map/read budgets in VOYAGE tokens (the pinned voyage-4
# tokenizer counts every rendered block), but the CONSUMER pays in CLAUDE tokens.
# TOKEN_BUDGET_CALIBRATION is the live-measured voyage->claude ratio: SURVEY-FINAL
# 2026-07-04 against the Anthropic count_tokens endpoint on claude-sonnet-5 -- the
# MAX per-project TOKEN-WEIGHTED p95 over a deterministic 10% stratified sample,
# 1,116 files (lore 1.704 / odoo 1.776 / di 1.729); tool scripts/token_survey.py;
# supersedes the six-sample pilot (1.61-1.72). Pinned at the observed MAXIMUM --
# CEILING semantics: a budget is a promise that must hold for the WORST observed
# content shape, so an uncalibrated budget never silently under-counts the
# consumer's real cost (up to ~78%). Applied in the budget-counting path
# (AppContext._count_tokens_single): counted = ceil(voyage_count * calibration).
TOKEN_BUDGET_CALIBRATION = 1.78
# The rendered digest lines for an empty memory recall / task query — a plain,
# honest "nothing matched" rather than a bare empty string.
_NO_MEMORIES_RECALLED = "(no project memories matched this query)"
_NO_TASKS_MATCHED = "(no tasks matched this query)"
# P8b wire-up: the same honest "nothing matched" convention for the lore_diff
# snapshot listing and the lore_findings query.
_NO_SNAPSHOTS_FOUND = "(no snapshots recorded yet)"
_NO_FINDINGS_MATCHED = "(no findings matched this query)"

# lore_diff's default snapshot-listing page size (the DiffEngine clamps out-of-range
# values to its own [1, 500] bound, so this is a best-effort default, not a hard cap).
_DEFAULT_DIFF_LIST_LIMIT = 20
# lore_findings' default query page size — the head of the number-ordered log
# (mirrors the ledger's own ``DEFAULT_QUERY_LIMIT``).
_DEFAULT_FINDINGS_QUERY_LIMIT = 100
# P7 recall render — the visible marker on a recalled ref whose chunk no longer
# exists (a refactor deleted it), so the agent re-verifies rather than trusting a
# stale pointer. Contains "drifted" so a case-insensitive scan finds it.
_DRIFT_MARKER = "(drifted — re-verify)"

# The four fleet task-tool actions ``lore_tasks`` dispatches on.
_TASK_ACTION_CREATE = "create"
_TASK_ACTION_QUERY = "query"
_TASK_ACTION_TRANSITION = "transition"
_TASK_ACTION_SUPERSEDE = "supersede"
_TASK_ACTIONS = (
    _TASK_ACTION_CREATE,
    _TASK_ACTION_QUERY,
    _TASK_ACTION_TRANSITION,
    _TASK_ACTION_SUPERSEDE,
)

# A generic "required argument" narrower for the task-tool dispatch (a create
# needs a subject, a transition needs a target status, …). Kept generic so one
# helper serves every action without per-arg boilerplate.
def _require_arg[REQUIRED_ARG](value: REQUIRED_ARG | None, name: str) -> REQUIRED_ARG:
    """Return ``value`` when present; raise a caller-error naming a missing arg.

    A task action that omits a field it needs (e.g. ``create`` with no
    ``subject``) is a caller error surfaced as a tool-level error naming the
    missing argument — never a silent write of a ``None`` field.
    """
    if value is None:
        raise ValueError(f"the {name!r} argument is required for this task action")
    return value


# The seven finding-ledger actions ``lore_findings`` dispatches on (report + the
# two read verbs + the four state-machine edges), mirroring ``_TASK_ACTIONS``.
_FINDING_ACTION_REPORT = "report"
_FINDING_ACTION_QUERY = "query"
_FINDING_ACTION_GET = "get"
_FINDING_ACTION_CHAIN_HEAD = "chain_head"
_FINDING_ACTION_ACKNOWLEDGE = "acknowledge"
_FINDING_ACTION_RESOLVE = "resolve"
_FINDING_ACTION_WONTFIX = "wontfix"
_FINDING_ACTIONS = (
    _FINDING_ACTION_REPORT,
    _FINDING_ACTION_QUERY,
    _FINDING_ACTION_GET,
    _FINDING_ACTION_CHAIN_HEAD,
    _FINDING_ACTION_ACKNOWLEDGE,
    _FINDING_ACTION_RESOLVE,
    _FINDING_ACTION_WONTFIX,
)


def _require_finding_arg[REQUIRED_ARG](value: REQUIRED_ARG | None, name: str) -> REQUIRED_ARG:
    """Return ``value`` when present and NON-EMPTY; raise a caller-error naming it.

    The finding-tool counterpart of :func:`_require_arg`, stricter on strings: a
    ``report`` needs a subject / body / area / category / created_by that are not
    merely present but non-blank (an empty ``subject`` is a caller error, never a
    silently-stored empty field).
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(
            f"the {name!r} argument is required and must be non-empty for this findings action"
        )
    return value


def _require_finding_ref(value: int | str | None) -> int | str:
    """Narrow a finding ``id_or_number`` to its non-empty ``int | str`` form.

    The address a ``get`` / ``chain_head`` / status-edge action needs: a stable
    ``number`` (an ``int``) OR an opaque ``id`` (a ``str``). Rejected when ``None``
    or a blank string — a caller error naming the argument, never a lookup on an
    empty id. Kept CONCRETE (not the generic :func:`_require_finding_arg`) so the
    ``int | str`` the ledger expects is preserved through the type checker.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(
            "the 'id_or_number' argument is required and must be a non-empty finding "
            "number or id for this findings action"
        )
    return value


def _refs_to_labels(refs: list[str]) -> list[str]:
    """Translate bare chunk-key refs into the backend's ``lore_ref=`` labels.

    Reuses :meth:`~loremaster.memory.local.LocalMemoryBackend._lore_ref_label` — the
    single source of truth for the ``lore_ref=<chunk_key>@<version>`` seam — so a
    save's refs fold into the SAME deterministic id the v0.3 store minted (an OLD
    ``(text, refs)`` re-saves to the same memory). Bare refs carry the base
    :data:`~loremaster.extension.DEFAULT_KEY_VERSION`.
    """
    from loremaster.memory.local import LocalMemoryBackend

    return [LocalMemoryBackend._lore_ref_label(ref, DEFAULT_KEY_VERSION) for ref in refs]


def _metadata_to_labels(metadata: dict[str, Any] | None) -> list[str]:
    """Flatten the DEPRECATED free-form ``metadata`` into flat ``key=value`` labels.

    The v0.3 ``save_memory`` carried a free-form ``metadata`` dict; the v2 backend
    speaks flat labels instead. A still-supplied ``metadata`` is flattened to
    ``key=value`` labels (plain labels — NOT ``lore_ref=``, so they never affect
    the deterministic id) rather than silently dropped.

    N1 guard (cutover-audit): a flattened label whose text starts with the
    backend's RESERVED ``lore_ref=`` prefix would be indistinguishable from a real
    chunk ref and would silently fold into the deterministic id — a silent
    promotion of decorative metadata into a chunk ref. Such a label is REJECTED
    loudly here, NAMING the reserved prefix, BEFORE any ledger/store write. The
    predicate keys on the flattened LABEL's prefix (not an exact ``key ==
    "lore_ref"`` match) so a key that itself embeds the separator (label
    ``lore_ref=nested=…``) is caught too. The prefix is imported from the backend's
    own source of truth (never restated) so the two can never drift. The sanctioned
    ``refs=`` param is unaffected — it flows through :func:`_refs_to_labels`.
    """
    if not metadata:
        return []
    from loremaster.memory.local import _LORE_REF_LABEL_PREFIX

    labels = [f"{key}={value}" for key, value in metadata.items()]
    for label in labels:
        if label.startswith(_LORE_REF_LABEL_PREFIX):
            raise ValueError(
                f"metadata flattens to the label {label!r}, which starts with the "
                f"reserved {_LORE_REF_LABEL_PREFIX!r} prefix — that prefix is "
                f"reserved for chunk refs that fold into the deterministic memory "
                f"id; pass chunk references through the refs= parameter instead."
            )
    return labels


def _make_existing_chunks(store: SurrealStore) -> ExistingChunksFn:
    """Build the memory backend's BATCH drift oracle over the unified chunk store.

    Returns an async ``chunk_keys -> set[str]`` closure delegating to the store's
    PUBLIC batch existence read (:meth:`SurrealStore.existing_point_ids`) — ONE
    query resolves every referenced chunk-key in a recall, never one point-fetch
    per ref. A recalled ref whose key this omits from the returned subset is
    drift-flagged (never filtered), so a refactor that deleted a referenced chunk
    surfaces as "re-verify", not a silent stale pointer; a DOWN store RAISES
    rather than silently reporting the whole batch missing.
    """

    async def _existing_chunks(chunk_keys: Sequence[str]) -> set[str]:
        return await store.existing_point_ids(chunk_keys)

    return _existing_chunks


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
    "- lore_search(query, ...): semantic, memory-boosted search across code + "
    "docs. Your default entry point when you don't already know the exact name/path. "
    "Returns ranked, cited hits.\n"
    "- lore_get_symbol(qualified_name): the EXACT stored definition + on-disk location "
    "of a named Python symbol (class / method / function). Use this — NOT "
    "lore_search — when you know the name and want the authoritative definition "
    "(it is collision-correct, not a fuzzy ranked guess).\n"
    "- lore_verify(qualified_name, expected_file_path=None, expected_signature_fragment=None): "
    "the anti-hallucination check — confirm a symbol/signature/location CLAIM against the "
    "stored truth BEFORE you repeat it. Returns confirmed / mismatch / not_found with the "
    "stored facts (a mismatch names the ACTUAL path or header). Unlike lore_get_symbol, a "
    "miss is a plain not_found RESULT, not an error.\n"
    "- lore_read(tier, path, ...): the EXACT bytes lore INDEXED for a file span, with "
    "a [SOURCE:...] header, hash-verified and FRESHNESS-flagged — the single read "
    "verb. Use after a lore_search / lore_get_symbol hit to read surrounding context. "
    "Its header carries a visible STALE notice when the index is behind the file on "
    "disk; pass wait_for_fresh=True to lore_search (or run lore_index(reconcile=True)) "
    "to refresh.\n"
    "- lore_dead_code(...): CANDIDATE dead/orphaned definitions in the project's live tiers "
    "— zero production references (test-only consumers count as dead). A HEURISTIC detector, "
    "not proof: dynamic dispatch, decorators, and public API used outside the tree can evade "
    "it. By default excludes test nodes, dunder methods, and __main__/__init__ entrypoints.\n"
    "- lore_impact(target, depth=1): who depends on target, in ONE call — production/test "
    "reference counts, covering tests, DIRECT importers/callers (depth 1) or a TRANSITIVE "
    "per-module rollup of the wider ripple (depth > 1), plus a live / dead (heuristic) "
    "verdict carrying an explicit astroid-bounds caveat. The single graph-read verb — "
    "absorbs what were previously separate direct-importer / transitive-closure / "
    "reference-count / covering-test tools. A 'dead' verdict is a LEAD to investigate, "
    "never a deletion order. Reach for this before removing or refactoring something "
    "lore_dead_code flagged.\n"
    "- lore_map(budget=2500, focus=None): a PageRank-ranked, token-budgeted map of which "
    "modules matter most in this project (each with its rendered symbol names), optionally "
    "re-centered on one symbol's own neighbourhood via focus. Reach for this FIRST when you "
    "don't yet know where to look.\n"
    "- lore_index(reconcile=False, tier=None): the freshness/health roll-up (indexed / "
    "in-flight / failed counts, embedding-schema + calibration state, last-sync/"
    "last-sweep ages, newest-snapshot age, per-tool trace-call aggregates) — "
    "zero embeds, cheap: manifest counts plus bounded trace/snapshot lookups, and "
    "NEVER sweeps by default. "
    "Pass reconcile=True (optionally with tier=<one tier>) to force a whole-tier "
    "reconcile sweep FIRST — the heavy 'make everything current now' hammer, not a "
    "per-file wait — then render the same status over the just-settled index.\n"
    "- lore_diff(since=None, until=None): what changed between two index SNAPSHOTS. Call it "
    "with no 'since' FIRST to list the recorded snapshot ids, then pass a 'since' (and "
    "optionally 'until'; omit 'until' to diff against the live 'now') to see the "
    "added/removed/modified files + per-function chunk deltas. The view names its 'legacy' "
    "(reduced-precision) and 'in-flight' (mid-reindex, excluded) markers — expect them.\n"
    "- lore_findings(action, ...): the durable, fleet-visible FINDING ledger (friction / "
    "capability gaps / bugs), dispatched on 'action' like lore_tasks: 'report' a finding "
    "(subject/body/area/category/created_by; kind defaults 'friction'), 'query' by "
    "status/kind/area, 'get'/'chain_head' one, or drive its review state machine with "
    "'acknowledge'/'resolve'/'wontfix' (by id_or_number + actor). Renders summarised rows.\n"
    "- lore_remember(text, ...) / lore_recall(query, ...): the project-memory "
    "store (see MEMORY below).\n"
    "\n"
    "WORKFLOW LADDER when you don't already know exactly where to look: orient with "
    "lore_map, locate specifics with lore_search, pin the exact definition with "
    "lore_get_symbol, then verify safety with lore_impact before you touch anything — "
    "lore_map -> lore_search -> lore_get_symbol -> lore_impact is the default chain.\n"
    "\n"
    "TOOL LOADING: if your harness exposes MCP tools behind a deferred loader (a ToolSearch- "
    "style tool that must select these before they are callable), load lore's tools "
    "explicitly up front — a lore tool that never gets ToolSearch-loaded is invisible to "
    "you, so ask for it rather than assuming lore is unavailable.\n"
    "\n"
    "CITATIONS: every lore_search / lore_read result carries a "
    "[SOURCE:file:line] citation plus a stable 'Key:' line (the chunk key) and a fenced "
    "source block. Echo the [SOURCE:...] citation when you quote code, and pass a "
    "'Key:' value back to lore_remember to pin a correction to a specific chunk.\n"
    "\n"
    "FRESHNESS / READ-YOUR-WRITES: a live inotify watcher re-indexes an edited file "
    "within ~seconds of a save — the normal freshness path. A periodic reconcile sweep "
    "(default ~10 min) is ONLY the backstop for events the watcher missed (downtime, "
    "queue overflow), not the edit-to-fresh latency. If you edit a file and "
    "IMMEDIATELY query it, you can race the embed window: pass "
    "lore_search(..., wait_for_fresh=True) — it bounded-waits for the in-flight "
    "file(s) matching your path filter, then serves fresh (or stale-flagged on timeout; "
    "it never hangs). Use lore_index(reconcile=True, tier=...) only to force a whole "
    "tier current; for the edit-then-query case wait_for_fresh is the right, cheaper "
    "tool.\n"
    "\n"
    "MEMORY: lore_remember / lore_recall is PROJECT-SCOPED memory about THIS "
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
    """Raised by ``index(reconcile=..., tier=...)`` on a bad ``tier`` argument.

    Two cases (P8d Wave 3 — this class survives the ``reindex``/``index_status``
    merge unchanged, now guarding the merged ``index`` handler): (1) ``tier``
    names a tier the project does not declare — the message NAMES the
    offending tier AND the valid ones, so a typo (which would otherwise be
    silently ignored — a false-success sweep over every tier) is caught and
    remediable; (2) ``tier`` is given without ``reconcile=True`` — a
    status-only call would otherwise silently ignore it. Subclasses
    :class:`ValueError` (a bad argument value). ``tier=None`` (sweep all)
    never raises.
    """


async def run_probe_gate(*, embedder: Embedder, config: LoreConfig) -> int:
    """Probe the embedder and verify dim coherence before the server starts.

    The gate (plan Deliverable 3 "startup probe gate"):

    1. ``await embedder.probe()`` — reaches the live endpoint (the embedder owns
       the connect timeout + fp32-warmup polling). A raise means the endpoint is
       unreachable → REFUSE.
    2. The observed dim must equal ``config.embedding.dim`` → else REFUSE (a
       wrong-dim deploy would silently corrupt retrieval).

    The existing-store vector-size coherence check is now owned downstream, not
    here: a populated chunk store whose dim drifted from ``config.embedding.dim``
    is caught by the embedding-schema-fingerprint rebuild machinery
    (``embedding_schema_fingerprint`` folds ``dim`` in, so a mismatch triggers a
    rebuild), and the memory backend refuses a wrong-dim memory table in its own
    ``ensure_ready``. The gate itself is now store-agnostic.

    Args:
        embedder: The active embedder to probe.
        config: The validated project config (``embedding.dim`` is the source of
            truth the probe must agree with).

    Returns:
        The observed embedding dimension (== ``config.embedding.dim`` on success).

    Raises:
        ProbeGateError: On an unreachable embedder or a probe/config dim mismatch.
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
    logger.info("startup.probe_gate.pass", extra={"observed_dim": observed})
    return observed


class SchemaRebuildingError(RuntimeError):
    """Raised by a corpus read tool whose result is EMPTY while a rebuild is in flight.

    The agent-visible, serialization-ROBUST way the corpus read tools surface
    a schema rebuild: an exception propagates through the MCP SDK as a ``ToolError``
    the agent SEES, whereas a custom attribute on a returned list is DROPPED by the
    SDK's ``convert_result`` (the result serialises to a bare ``[]``) and never
    reaches the agent. The message carries the rebuilding notice (mentioning the
    rebuild + the done/total progress) so the agent knows to retry shortly.

    Raised only when a tool's substantive result would be empty AND
    :func:`~loremaster.index.schema.rebuilding_notice` reports an in-progress
    rebuild — a genuine no-match while idle stays a plain empty result (no raise).
    """


class CalibrationStatus(BaseModel):
    """The boot token-calibration status surfaced by ``index_status`` (P8c).

    A structured mirror of :meth:`~loremaster.calibration.engine.CalibrationEngine.
    status` — its keys map 1:1 onto these fields, so ``CalibrationStatus.
    from_engine_status(engine.status())`` round-trips (that classmethod, not a raw
    ``CalibrationStatus(**engine.status())`` splat, is the production construction
    site — see its docstring for why: a FUTURE engine ``status()`` key must not
    brick the render, audit finding 4 / F3). The ``state`` string surfaces VERBATIM
    (the deployed exit criterion: ``index_status`` visibly shows ``cached`` /
    ``measured`` / ``drift_adopted`` / ``cached_retrying``). Attached as an optional
    nested section on :class:`IndexStatusSummary`, mirroring the ``embedding_schema``
    / ``schema_rebuild`` idiom.

    Attributes:
        state: The serving state — one of ``cached`` / ``measured`` /
            ``drift_adopted`` / ``cached_retrying``.
        served_constant: The float the budget path multiplies by right now.
        committed_constant: The generation-anchored constant shipped in ``server.py``.
        model: The yardstick model the probe counts against.
        ratio_shift: The measured ``live/baseline − 1`` shift, or ``None`` until a
            probe lands.
        last_probe_at: ISO timestamp of the last probe, or ``None``.
        baseline_generated_at: ISO timestamp the baseline was generated at, or ``None``.
        note: A human-readable note (e.g. an adopted-scaled-constant explanation), or
            ``None``.
    """

    model_config = ConfigDict(extra="forbid")

    state: str
    served_constant: float
    committed_constant: float
    model: str
    ratio_shift: float | None = None
    last_probe_at: str | None = None
    baseline_generated_at: str | None = None
    note: str | None = None

    @classmethod
    def from_engine_status(cls, payload: dict[str, Any]) -> CalibrationStatus:
        """Construct from :meth:`CalibrationEngine.status`'s snapshot dict, resiliently.

        The model stays ``extra="forbid"`` on the wire — this constructor does
        not weaken that (a genuinely malformed agent-facing payload must still
        be rejected). But ``engine.status()`` is an internal seam a FUTURE
        engine version could grow a new key on without this model growing in
        lockstep — a raw ``CalibrationStatus(**engine.status())`` splat would
        then brick every status read (audit finding 4 / F3). This selects only
        the fields the model declares; any OTHER key present is logged
        loudly, named, as a drift signal (new engine data this model doesn't
        yet expose) rather than crashing the render. A payload MISSING a
        known field still raises (unchanged) — that is a genuine regression
        worth surfacing, not extra-field drift.
        """
        known_fields = set(cls.model_fields)
        extras = sorted(set(payload) - known_fields)
        if extras:
            logger.warning(
                "index.calibration_status.unknown_engine_fields",
                extra={"extras": extras},
            )
        selected = {key: value for key, value in payload.items() if key in known_fields}
        return cls(**selected)


class AgeStatus(BaseModel):
    """A single "since when" fact: an ISO-8601 timestamp plus its age in seconds.

    Both fields are ``None`` when the underlying event has never happened yet —
    rendered honestly as "never" rather than crashing (a pre-existing deployment
    has no ``last_sync``/``last_sweep`` stamp before its first live-apply/sweep,
    and a fresh corpus has no snapshot yet). ``age_seconds`` is the RAW elapsed
    time; the caller phrases it (e.g. "42m ago") — lore does not hand-roll a
    duration formatter (no existing dependency does this either; the codebase's
    idiom elsewhere, e.g. :attr:`CalibrationStatus.last_probe_at`, is likewise a
    raw ISO timestamp, not a pre-rendered phrase).
    """

    model_config = ConfigDict(extra="forbid")

    at: str | None = None
    age_seconds: float | None = None


class ToolTraceCount(BaseModel):
    """One tool's call count from the ``trace`` table aggregate."""

    model_config = ConfigDict(extra="forbid")

    tool: str
    calls: int


class TraceSummary(BaseModel):
    """The ``trace`` table's aggregate, as surfaced by ``lore_index`` (P8d Wave 3).

    ``total``/``by_tool``/``latest_at`` are ``0``/``[]``/``None`` when nothing has
    ever been traced — which is EVERY boot today, since no caller yet wires the
    per-invocation :meth:`~loremaster.store.surreal.SurrealStore.record_trace`
    emission (that wiring is a later phase per its own docstring; this section
    only reads whatever rows already exist).

    Attributes:
        total: The total trace-row count across every tool (the sum of
            ``by_tool``'s ``calls``).
        by_tool: Per-tool call counts, sorted by tool name for a deterministic
            render.
        latest_at: The ISO-8601 timestamp of the single most recent trace row
            across every tool, or ``None`` when the table is empty.
    """

    model_config = ConfigDict(extra="forbid")

    total: int = 0
    by_tool: list[ToolTraceCount] = Field(default_factory=list)
    latest_at: str | None = None


class IndexStatusSummary(IndexSummary):
    """``lore_index``'s return shape (P8d Wave 3 merge) — an
    :class:`~loremaster.index.indexer.IndexSummary` plus the server-level
    ``calibration``/``last_sync``/``last_sweep``/``newest_snapshot``/``traces``
    sections.

    Calibration is a SERVER-BOOT concern (the Anthropic token yardstick), not an
    indexer concern, so the section is added here as a subclass rather than on the
    indexer's own model. The inherited base fields (``files_indexed`` …) surface
    unchanged; FastMCP publishes each new section additively under ``$defs``.

    F3 safety pattern (auditor finding, closed here): every field below carries a
    ``default_factory``/``None`` default, so constructing this model with ONLY the
    base :class:`IndexSummary` fields (as the pre-existing
    ``test_calibration_wiring.py`` unit tests do) still validates — adding a field
    here is an explicit schema edit, but never a BREAKING one for an existing
    caller that doesn't yet know about it. The NEXT field addition should follow
    the same shape: a typed section with its own sane "nothing recorded" default,
    never a bare required field that forces every existing construction site to
    change in lockstep.
    """

    calibration: CalibrationStatus | None = None
    last_sync: AgeStatus = Field(default_factory=AgeStatus)
    last_sweep: AgeStatus = Field(default_factory=AgeStatus)
    newest_snapshot: AgeStatus = Field(default_factory=AgeStatus)
    traces: TraceSummary = Field(default_factory=TraceSummary)


class _CalibrationFindingsAdapter:
    """Adapt the durable :class:`~loremaster.findings.FindingLedger` to the calibration
    engine's narrow :class:`~loremaster.calibration.engine.FindingsPort`.

    The engine files at most ONE drift finding per drift episode, deduped against a
    live one. ``has_open_drift_finding`` treats an ``open`` OR ``acknowledged``
    finding as still-live (an acknowledged-but-unresolved drift must not be re-filed);
    the ledger's ``query`` filters a single exact status, so both are checked.
    ``report_drift_finding`` forwards to ``FindingLedger.report`` (kwargs line up 1:1,
    minus ``supersedes``).
    """

    def __init__(self, finding_ledger: FindingLedger) -> None:
        self._finding_ledger = finding_ledger

    async def has_open_drift_finding(self, area: str) -> bool:
        """True iff an ``open`` OR ``acknowledged`` finding exists for ``area``."""
        from loremaster.findings import STATUS_ACKNOWLEDGED, STATUS_OPEN

        if await self._finding_ledger.query(area=area, status=STATUS_OPEN):
            return True
        return bool(await self._finding_ledger.query(area=area, status=STATUS_ACKNOWLEDGED))

    async def report_drift_finding(
        self,
        *,
        subject: str,
        body: str,
        area: str,
        category: str,
        kind: str,
        created_by: str,
    ) -> None:
        """File a drift finding on the durable ledger (kind/area/category from the engine)."""
        await self._finding_ledger.report(
            subject,
            body,
            kind=kind,
            area=area,
            category=category,
            created_by=created_by,
        )


class AppContext:
    """The live runtime services bundle the MCP tools dispatch through.

    Built by :func:`build_app_context` after the probe gate passes. Holds every
    runtime service (embedder, stores, manifest, graph, the search pipeline, the
    read tools, the SurrealDB memory backend, the fleet task ledger, the indexer,
    the reconcile engine, the watcher)
    plus the spawned background tasks, and exposes one async HANDLER per MCP tool.
    The FastMCP tool functions are thin wrappers that fetch this context from the
    lifespan and call the matching handler — so the handlers are the single, fully
    end-to-end-testable surface (a test drives them directly with a FakeEmbedder +
    a real SurrealDB store; the FastMCP tools just re-expose them).
    """

    def __init__(
        self,
        *,
        server: LoreServer,
        embedder: Embedder,
        write_store: SurrealStore,
        manifest: SurrealManifest,
        code_graph: SurrealCodeGraph,
        snapshot_stamper: Any,
        indexer: Indexer,
        reconcile_engine: ReconcileEngine,
        watcher: Any,
        search_pipeline: SearchPipeline,
        symbol_tool: SymbolTool,
        verify_tool: VerifyTool,
        store_read_tool: StoreReadTool,
        diff_engine: DiffEngine,
        finding_ledger: FindingLedger,
        memory_backend: MemoryBackend,
        task_ledger: TaskLedger,
        calibration_engine: CalibrationEngine | None = None,
    ) -> None:
        self._server = server
        self._config: LoreConfig = server.config
        self.embedder = embedder
        self.write_store = write_store
        self.manifest = manifest
        self.code_graph = code_graph
        # The server-owned snapshot stamper (C4-audit #2): constructed, readied,
        # injected into the indexer + reconcile engine, and closed on aclose.
        self._snapshot_stamper = snapshot_stamper
        self.indexer = indexer
        self.reconcile_engine = reconcile_engine
        self.watcher = watcher
        self.search_pipeline = search_pipeline
        self._symbol_tool = symbol_tool
        self._verify_tool = verify_tool
        # P8b wire-up: the store-backed span reader (lore_read) and the snapshot
        # diff engine (lore_diff). ``store_read_tool`` is a pure tool over the
        # store + manifest (no connection of its own); ``diff_engine`` owns its OWN
        # SurrealDB connection (like ``_snapshot_stamper``), closed in ``aclose``.
        self._store_read_tool = store_read_tool
        self._diff_engine = diff_engine
        # P7 cutover — plain, settable public attributes (like ``search_pipeline``):
        # the SurrealDB memory backend the memory tools dispatch through, and the
        # durable fleet task ledger the two task tools ride.
        self.memory_backend = memory_backend
        self.task_ledger = task_ledger
        # P8b wire-up: the durable, fleet-visible finding ledger the lore_findings
        # tool rides — the second ledger alongside ``task_ledger`` (same posture:
        # a settable public attribute owning its OWN SurrealDB connection).
        self.finding_ledger = finding_ledger
        # P8c wire-up: the boot token-calibration engine (voyage->claude budget
        # scaling). The budget path reads its ``served_constant`` (falling back to
        # the committed ``TOKEN_BUDGET_CALIBRATION`` when absent), ``index_status``
        # renders its ``status()``, and the lifespan starts/stops its background
        # probe. ``None`` when a test builds a context without one (the probe never
        # runs, so the committed constant serves).
        self._calibration_engine = calibration_engine
        # The parent extension context (per-extension namespaced state lives here),
        # set when the lifespan ran the startup hooks, so shutdown reuses it.
        self._extension_ctx: ExtensionContext | None = None
        # Background-task handles + a flag the tests/lifespan inspect.
        self.reconcile_task: Any = None
        self.watcher_started: bool = False
        # The background schema-rebuild asyncio.Task (A7); None when no rebuild is running.
        self.schema_rebuild_task: Any = None
        # P6-tail (lore_impact / lore_map): both engines compose over THIS SAME
        # rooted ``code_graph`` (never a separately-built or rootless one -- a
        # rootless graph silently disables astroid resolution and every
        # reference-backed verdict drifts toward false-dead, the P6-impact-green
        # FRICTION lesson) and share the SAME ``_rebuild_notice`` probe method
        # below, so a verdict/ranking is never served mid-rebuild -- the identical
        # gating discipline the corpus-read tool handlers above apply (search via
        # ``_raise_if_empty_during_rebuild``; get_symbol/read via
        # ``_rebuilding_error_or``; verify inline against the same probe), just
        # enforced INSIDE the engine (it checks before running any query) rather
        # than wrapped around an already-computed result. P8d Wave 2 follow-on
        # (fixer-w2f): what_imports's AppContext handler -- the last tool that
        # rode ``_raise_if_empty_during_rebuild`` alongside search -- is deleted;
        # test_schema_rebuild.py's shared-seam A8c pin now targets ``impact``
        # (this proactive-gate mechanism) instead.
        self._impact_engine = ImpactEngine(graph=code_graph, rebuild_notice=self._rebuild_notice)
        self._map_engine = MapEngine(
            graph=code_graph,
            count_tokens=self._count_tokens_single,
            rebuild_notice=self._rebuild_notice,
        )

    # -- tool handlers (the single end-to-end surface) ---------------------

    async def search(
        self,
        query: str,
        k: int = _DEFAULT_SEARCH_K,
        filters: dict[str, str] | None = None,
        *,
        wait_for_fresh: bool = False,
        detail_level: str = "auto",
    ) -> list[SearchResult]:
        """Memory-boosted semantic search; returns summarised, cited results."""
        results = await self.search_pipeline.search_code(
            query, k, filters, wait_for_fresh=wait_for_fresh, detail_level=detail_level
        )
        await self._raise_if_empty_during_rebuild(results)
        return results

    async def get_symbol(self, qualified_name: str) -> ResolvedSymbol:
        """Resolve a qualified Python name to its exact stored definition + location."""
        from loremaster.symbols import GetSymbolError

        try:
            return await self._symbol_tool.get_symbol(qualified_name)
        except GetSymbolError as exc:
            # An unresolved symbol DURING a rebuild may simply be not-yet-re-embedded
            # — raise the rebuilding error so the agent retries. When idle, the
            # not-found is genuine and re-raised unchanged.
            raise await self._rebuilding_error_or(exc) from exc

    async def verify(
        self,
        qualified_name: str,
        expected_file_path: str | None = None,
        expected_signature_fragment: str | None = None,
    ) -> VerifyResult:
        """Verify a symbol/signature/location CLAIM against the stored truth.

        Delegates to the :class:`~loremaster.symbols.VerifyTool` (which rides the
        SAME resolver as ``get_symbol``, so a name resolves to the same row through
        both). ``not_found`` is a RESULT here, never an exception — answering
        "does this exist?" is verify's whole job — so, unlike ``get_symbol``, there
        is no not-found error to route through the rebuilding gate. A downed store
        still surfaces LOUDLY: ``SurrealConnectionError`` propagates unchanged, so
        an outage can never masquerade as a ``not_found`` verdict.

        REBUILD CAVEAT (P8b, operator-dispositioned serve-and-say-so): a
        ``not_found`` DURING an active schema rebuild may be a TRANSIENT false
        negative (the symbol not-yet-re-embedded). Unlike the other corpus read
        tools (search/get_symbol/read/impact/map, post-P8d-Wave-2 -- what_imports
        was the sixth before its handler was deleted) — which RAISE a rebuilding
        error so the agent retries — verify still ANSWERS
        ``not_found`` (that is its whole job) but stamps the
        :data:`~loremaster.symbols.VERIFY_REBUILD_CAVEAT` line onto the result (via
        ``model_copy``) so the caller knows the absence may be transient. A
        ``confirmed`` / ``mismatch`` verdict resolved a real row, so it is
        trustworthy mid-rebuild and NEVER carries the caveat. Reads the SAME rebuild
        signal (:meth:`_rebuild_notice`) the sibling read paths gate on.
        """
        result = await self._verify_tool.verify(
            qualified_name, expected_file_path, expected_signature_fragment
        )
        if result.status == "not_found":
            notice = await self._rebuild_notice()
            if notice is not None:
                return result.model_copy(
                    update={"rebuilding_caveat": f"{VERIFY_REBUILD_CAVEAT} ({notice})"}
                )
        return result

    async def read(
        self,
        tier: str,
        path: str,
        line_start: int | None = None,
        line_end: int | None = None,
    ) -> StoreFileSpan:
        """Read a span straight from the unified store — the hash-verified read verb.

        The single, store-backed read verb (P8d): it serves the EXACT bytes lore
        INDEXED (the ``file_text`` row) rather than the live filesystem, hash-verified
        against their stored digest and flagged ``stale`` when the index is behind
        disk. ``tier`` is VALIDATED FIRST via :meth:`_validate_tier` — the audit found
        :class:`~loremaster.store_read.StoreReadTool` alone reports an unknown tier as
        a bare not-found, so the wiring gives it the sibling tools' unknown-tier error
        NAMING the configured tiers (a correctable typo, not a silent miss). A
        not-found DURING a rebuild is routed through :meth:`_rebuilding_error_or` (as
        the corpus-read tools do), so a not-yet-re-embedded body reads as a retryable
        rebuilding signal, not a genuine absence.

        Args:
            tier: The source tier to read from (validated against the configured tiers).
            path: The tier-relative file path.
            line_start: First line (1-based, inclusive); ``None`` ⇒ 1.
            line_end: Last line (1-based, inclusive); ``None`` ⇒ EOF.

        Returns:
            The resolved :class:`~loremaster.store_read.StoreFileSpan` (its ``header``
            carries a visible STALE notice when the served bytes are behind disk).

        Raises:
            ReindexTierError: ``tier`` is not a configured tier (names the valid ones).
            StoreReadError: A not-found / containment / integrity / out-of-range
                failure — surfaced as a tool error, never a raw traceback (a
                not-found mid-rebuild is re-cast as a retryable rebuilding error).
            SurrealConnectionError: The store or manifest connection is down.
        """
        from loremaster.store_read import StoreReadError

        self._validate_tier(tier)
        try:
            return await self._store_read_tool.read(tier, path, line_start, line_end)
        except StoreReadError as exc:
            # A not-found span DURING a rebuild may be a not-yet-re-embedded body —
            # raise the rebuilding error (so the agent retries) rather than let a
            # bare not-found mislead it. When idle, the original error is re-raised.
            raise await self._rebuilding_error_or(exc) from exc

    async def diff(
        self,
        since: str | None = None,
        until: str | None = None,
        limit: int = _DEFAULT_DIFF_LIST_LIMIT,
    ) -> str:
        """List snapshots (no ``since``) or diff two generations, RENDERED summarised.

        A thin dispatcher over the :class:`~loremaster.diff.DiffEngine`:

        * ``since`` omitted ⇒ ``list_snapshots(limit)`` rendered as a summarised
          listing (never a raw store dump), so a caller learns the real snapshot ids
          to diff between.
        * ``since`` given ⇒ ``diff(since, until)`` rendered (``until`` omitted = the
          live "now" state). The rendered view names the legacy / in-flight markers.

        The engine's typed errors (:class:`~loremaster.diff.SnapshotNotFoundError`
        for a malformed/unknown id) and infrastructure faults
        (:class:`~loremaster.store.surreal.SurrealConnectionError`) surface unchanged.
        """
        if since is None:
            summaries = await self._diff_engine.list_snapshots(limit)
            return self._render_snapshot_rows(summaries)
        result = await self._diff_engine.diff(since, until)
        return result.render()

    @staticmethod
    def _render_snapshot_rows(summaries: list[SnapshotSummary]) -> str:
        """Render snapshot summaries as a compact digest (id/created/counts/git).

        Never a raw SurrealDB row — just the headline facts a caller needs to pick a
        ``since``/``until`` id: the exact snapshot id, its creation time, the file /
        chunk totals, and the git ref/branch when the codebase is a git checkout.
        """
        if not summaries:
            return _NO_SNAPSHOTS_FOUND
        rows: list[str] = []
        for summary in summaries:
            git = (
                f", {summary.git_branch or '?'}@{summary.git_ref[:12]}"
                if summary.git_ref
                else ""
            )
            rows.append(
                f"- {summary.id} (created {summary.created_at}, "
                f"{summary.files_total} files / {summary.chunks_total} chunks{git})"
            )
        return "\n".join(rows)

    async def findings(  # noqa: PLR0911 - P8d rewrites this render; restructuring now would churn
        self,
        *,
        action: str,
        id_or_number: int | str | None = None,
        subject: str | None = None,
        body: str | None = None,
        area: str | None = None,
        category: str | None = None,
        created_by: str | None = None,
        kind: str | None = None,
        actor: str | None = None,
        note: str | None = None,
        status: str | None = None,
        limit: int = _DEFAULT_FINDINGS_QUERY_LIMIT,
        supersedes: int | str | None = None,
    ) -> str:
        """Dispatch a finding-ledger action, rendering SUMMARISED results as a string.

        A thin dispatcher over the durable :class:`~loremaster.findings.FindingLedger`
        (dispatch style mirrors :meth:`tasks`), over the seven actions:

        * ``report`` — file a finding (``subject`` / ``area`` / ``category`` /
          ``created_by`` required and NON-EMPTY; ``body`` OPTIONAL — an omitted or
          ``None`` body reports as ``""``, matching the ledger's documented
          plain-string domain that allows a subject-only quick capture; ``kind``
          defaults ``"friction"``; optional ``supersedes``). Renders the new
          finding's ``#number`` + id.
        * ``query`` — browse by ``status`` / ``kind`` / ``area`` / ``limit`` filters.
        * ``get`` / ``chain_head`` — one finding by ``id_or_number`` (chain_head follows
          the supersedes chain forward to the newest record).
        * ``acknowledge`` / ``resolve`` / ``wontfix`` — drive a legal status edge by
          ``id_or_number`` + ``actor`` (+ optional ``note`` on the terminal edges).

        The ledger's typed errors (:class:`~loremaster.findings.FindingNotFoundError`
        / :class:`~loremaster.findings.IllegalTransitionError` /
        :class:`~loremaster.findings.FindingChainCycleError`) surface unchanged.
        """
        if action == _FINDING_ACTION_REPORT:
            report = await self.finding_ledger.report(
                _require_finding_arg(subject, "subject"),
                # body is OPTIONAL (audit-waveb-1 finding #1): the schema + ledger
                # deliberately allow an empty body (a subject-only finding is a
                # valid quick capture), so the MCP boundary must match that domain
                # rather than be stricter than it — an omitted/None body reports
                # as "", never rejected.
                body if body is not None else "",
                kind=kind or _DEFAULT_FINDING_KIND,
                area=_require_finding_arg(area, "area"),
                category=_require_finding_arg(category, "category"),
                created_by=_require_finding_arg(created_by, "created_by"),
                supersedes=supersedes,
            )
            return f"reported finding #{report.number} (id {report.id}, status open)"
        if action == _FINDING_ACTION_QUERY:
            rows = await self.finding_ledger.query(
                status=status, kind=kind, area=area, limit=limit
            )
            return self._render_finding_rows(rows)
        if action == _FINDING_ACTION_GET:
            finding = await self.finding_ledger.get(_require_finding_ref(id_or_number))
            return self._render_finding_rows([finding])
        if action == _FINDING_ACTION_CHAIN_HEAD:
            head = await self.finding_ledger.chain_head(_require_finding_ref(id_or_number))
            return self._render_chain_head(head)
        if action == _FINDING_ACTION_ACKNOWLEDGE:
            acked = await self.finding_ledger.acknowledge(
                _require_finding_ref(id_or_number),
                _require_finding_arg(actor, "actor"),
            )
            return self._render_finding_transition(acked, actor)
        if action == _FINDING_ACTION_RESOLVE:
            resolved = await self.finding_ledger.resolve(
                _require_finding_ref(id_or_number),
                _require_finding_arg(actor, "actor"),
                note,
            )
            return self._render_finding_transition(resolved, actor)
        if action == _FINDING_ACTION_WONTFIX:
            closed = await self.finding_ledger.wontfix(
                _require_finding_ref(id_or_number),
                _require_finding_arg(actor, "actor"),
                note,
            )
            return self._render_finding_transition(closed, actor)
        raise ValueError(
            f"unknown findings action {action!r}; valid actions are {list(_FINDING_ACTIONS)}"
        )

    @staticmethod
    def _render_finding_transition(finding: Finding, actor: str | None) -> str:
        """Render a finding status transition (names the number, new status, actor)."""
        return f"finding #{finding.number} transitioned to {finding.status} by {actor}"

    @classmethod
    def _render_chain_head(cls, head: ChainHead) -> str:
        """Render a supersedes-chain head, SURFACING a fork rather than hiding it.

        The concurrent hardening builder made :meth:`~loremaster.findings.FindingLedger.
        chain_head` fork-aware — it returns the head of the lowest-numbered branch
        plus the sibling successors the deterministic walk did NOT follow. Rendering
        only the head would silently drop that signal, so a forked chain appends a
        line naming the other branches' entry numbers (call chain_head on each to
        reach its own head).
        """
        rendered = cls._render_finding_rows([head.finding])
        if head.forked:
            others = ", ".join(f"#{number}" for number in head.fork_successor_numbers)
            rendered += (
                f"\n(chain FORKED — this is the head of the lowest-numbered branch; "
                f"other branches start at {others} — call chain_head on each to reach its head)"
            )
        return rendered

    @staticmethod
    def _render_finding_rows(findings: list[Finding]) -> str:
        """Render finding rows as a summarised digest (never a raw SurrealDB row).

        Mirrors :meth:`_render_task_rows`: the opaque id carries no ``finding:``
        record prefix and no ``RecordID`` leaks — just the fleet-visible fields
        (number / status / subject / kind / area / category / author).
        """
        if not findings:
            return _NO_FINDINGS_MATCHED
        return "\n".join(
            f"- [#{finding.number} {finding.status}] {finding.subject} "
            f"(id {finding.id}, kind {finding.kind}, area {finding.area}, "
            f"category {finding.category}, by {finding.created_by})"
            for finding in findings
        )

    async def remember(
        self,
        text: str,
        *,
        refs: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        kind: str = _DEFAULT_MEMORY_KIND,
        trust: str | None = None,
        importance: float | None = None,
        supersedes: str | None = None,
        labels: list[str] | None = None,
    ) -> str:
        """Persist a project-memory note via the SurrealDB backend; returns its id.

        The id is the v0.3 deterministic ``uuid5`` (text + refs stamp), so a re-save
        of the same ``(text, refs)`` collapses to one memory across the cutover.
        ``refs`` (bare chunk keys) become ``lore_ref=`` labels that fold into the id;
        the DEPRECATED ``metadata`` dict is flattened to ``key=value`` labels; an
        explicit ``trust`` builds an operator :class:`MemorySource`. Validation is
        HONEST: an unknown ``kind`` (or, via the backend, an out-of-range
        ``importance``) raises a tool-level error NAMING the offending value — never
        a silent default.

        Args:
            text: The note to remember (a durable fact/correction about this project).
            refs: Bare chunk keys the note pins to; each folds into the id.
            metadata: DEPRECATED free-form dict, flattened to ``key=value`` labels.
            kind: The memory kind (one of :data:`_VALID_MEMORY_KINDS`).
            trust: Optional two-value trust ("authoritative"/"experiential").
            importance: Optional importance override in ``[0, 1]``.
            supersedes: The id of an existing memory this note replaces.
            labels: Extra flat labels stored alongside the note.

        Returns:
            The deterministic ``uuid5`` memory id.

        Raises:
            ValueError: ``kind`` is outside :data:`_VALID_MEMORY_KINDS`, or the
                backend rejects an out-of-range ``importance``.
        """
        if kind not in _VALID_MEMORY_KINDS:
            raise ValueError(
                f"unknown memory kind {kind!r}; valid kinds are "
                f"{sorted(_VALID_MEMORY_KINDS)}"
            )
        # An explicit trust rides an operator-note source; no trust ⇒ let the
        # backend apply its own default source (never fabricate one here).
        source = (
            # A bad trust string is still rejected at runtime by MemorySource's
            # pydantic validation (surfacing as a tool error) — the cast only
            # satisfies the static Literal type at this call site.
            MemorySource(
                kind=_MEMORY_SOURCE_KIND_OPERATOR, trust=cast(TrustLevel, trust)
            )
            if trust is not None
            else None
        )
        composed_labels = [
            *_refs_to_labels(refs or []),
            *_metadata_to_labels(metadata),
            *(labels or []),
        ]
        return await self.memory_backend.remember(
            text,
            kind=kind,
            importance=importance,
            source=source,
            labels=composed_labels or None,
            supersedes=supersedes,
        )

    async def recall(
        self,
        query: str,
        k: int = _DEFAULT_RECALL_K,
        *,
        kind: str | None = None,
        labels: list[str] | None = None,
    ) -> str:
        """Recall the nearest saved notes for ``query`` as a summarised markdown digest.

        Delegates to the backend's ``recall`` (superseded/expired rows never
        surface — the backend already excludes them, so this NEVER re-filters) and
        renders each note's text + kind + importance + score + refs, drift-marking a
        ref whose chunk no longer exists. ``kind`` and ``labels`` are pass-through
        filters onto the backend's own semantics (``kind`` an exact match,
        ``labels`` an ALL-match); omitting both leaves the unfiltered recall path
        byte-identical to before their addition.
        """
        recalled = await self.memory_backend.recall(query, k=k, kind=kind, labels=labels)
        return self._render_recalled_memories(recalled)

    @staticmethod
    def _render_recalled_memories(recalled: list[RecalledMemory]) -> str:
        """Render recalled memories as a compact markdown digest (never a raw row)."""
        if not recalled:
            return _NO_MEMORIES_RECALLED
        blocks: list[str] = []
        for memory in recalled:
            # Drift-mark each ref whose chunk the oracle reported missing so the
            # agent re-verifies; the chunk key itself always stays visible.
            rendered_refs = ", ".join(
                f"{ref.chunk_key} {_DRIFT_MARKER}" if ref.drifted else ref.chunk_key
                for ref in memory.refs
            )
            lines = [
                f"- {memory.text}",
                f"  kind: {memory.kind} · importance: {memory.importance:.2f} · "
                f"score: {memory.score:.4f}",
            ]
            if rendered_refs:
                lines.append(f"  refs: {rendered_refs}")
            blocks.append("\n".join(lines))
        return "\n".join(blocks)

    async def claim_task(self, task_id: str, owner: str) -> str:
        """Atomically claim ``task_id`` for ``owner`` (the fleet-coordination primitive).

        Delegates to the durable :class:`~loremaster.tasks.TaskLedger`'s
        compare-and-set and renders the outcome: a WIN names the new owner + claim
        time; a LOSS names the current holder and mutates nothing. An unknown id
        surfaces the ledger's typed :class:`~loremaster.tasks.TaskNotFoundError`
        (naming the id) unchanged.
        """
        result = await self.task_ledger.claim_task(task_id, owner)
        return self._render_claim_result(result)

    @staticmethod
    def _render_claim_result(result: ClaimResult) -> str:
        """Render an atomic-claim outcome (win names owner+time; loss names holder)."""
        task = result.task
        if result.claimed:
            return (
                f"claimed: task {task.id} is now owned by {task.owner} "
                f"(claimed_at {task.claimed_at})"
            )
        return (
            f"not claimed: task {task.id} is already held by {task.owner} "
            f"(status {task.status})"
        )

    async def tasks(
        self,
        *,
        action: str,
        task_id: str | None = None,
        subject: str | None = None,
        description: str | None = None,
        created_by: str | None = None,
        actor: str | None = None,
        status: str | None = None,
        owner: str | None = None,
        blocked: bool | None = None,
        blocked_by: list[str] | None = None,
    ) -> str:
        """Dispatch a fleet task action (create|query|transition|supersede).

        A thin dispatcher over :class:`~loremaster.tasks.TaskLedger` that renders
        SUMMARISED results (never a raw SurrealDB row) and lets the ledger's typed
        errors (:class:`~loremaster.tasks.IllegalTransitionError` /
        :class:`~loremaster.tasks.TaskNotFoundError`) surface unchanged.
        """
        if action == _TASK_ACTION_CREATE:
            new_id = await self.task_ledger.create_task(
                _require_arg(subject, "subject"),
                _require_arg(description, "description"),
                blocked_by=blocked_by,
                created_by=_require_arg(created_by, "created_by"),
            )
            return f"created task {new_id} (status open)"
        if action == _TASK_ACTION_QUERY:
            rows = await self.task_ledger.query_tasks(
                status=status, owner=owner, blocked=blocked
            )
            return self._render_task_rows(rows)
        if action == _TASK_ACTION_TRANSITION:
            task = await self.task_ledger.transition(
                _require_arg(task_id, "task_id"),
                _require_arg(status, "status"),
                actor=_require_arg(actor, "actor"),
            )
            return f"task {task.id} transitioned to {task.status} by {actor}"
        if action == _TASK_ACTION_SUPERSEDE:
            successor_id = await self.task_ledger.supersede_task(
                _require_arg(task_id, "task_id"),
                subject=_require_arg(subject, "subject"),
                description=_require_arg(description, "description"),
                created_by=_require_arg(created_by, "created_by"),
            )
            return f"superseded task {task_id}; successor {successor_id} (status open)"
        raise ValueError(
            f"unknown task action {action!r}; valid actions are {list(_TASK_ACTIONS)}"
        )

    @staticmethod
    def _render_task_rows(rows: list[Task]) -> str:
        """Render task rows as a summarised digest (id/subject/status/owner/blockers).

        Never a raw SurrealDB row: the opaque id has no ``task:`` record prefix and
        no ``RecordID`` leaks — just the fleet-visible fields.
        """
        if not rows:
            return _NO_TASKS_MATCHED
        return "\n".join(
            f"- [{task.status}] {task.subject} (id {task.id}, owner {task.owner}, "
            f"blocked_by {task.blocked_by})"
            for task in rows
        )

    async def index(
        self,
        *,
        reconcile: bool = False,
        tier: str | None = None,
    ) -> IndexStatusSummary:
        """Read the index freshness/health status, optionally sweeping first.

        The single merged index tool (P8d Wave 3 — folds the former ``reindex``
        + ``index_status`` handlers into one). ``reconcile=False`` (the
        default) is a PURE STATUS READ — it NEVER sweeps, so a plain health
        check stays cheap and side-effect-free. ``reconcile=True`` runs the
        SAME "make everything current now" sweep the old ``reindex`` ran
        (optionally scoped to ``tier``), THEN renders the freshness status over
        the just-settled index (sweep-then-status).

        Design of the two params (rationale for the report): a bool
        ``reconcile`` flag plus a separate optional ``tier`` filter, rather
        than overloading ONE ``reconcile: str | None`` parameter with an
        "all tiers" sentinel value that would look exactly like a real tier
        name. The bool spells its own intent (sweep or don't) and ``tier``
        keeps its pre-merge meaning verbatim (``None`` = every configured
        tier), so the agent-facing schema never needs a magic string that
        could be mistaken for a tier. ``tier`` is inert unless paired with
        ``reconcile=True`` — passing one without the other is refused loudly
        (see the raise below) rather than silently ignored.

        P8e seam: in a future split-mode deployment this handler's sweep half
        becomes a command row a remote role executes rather than an in-process
        call (plan §5) — this wave sweeps in-process locally only.

        Args:
            reconcile: When ``True``, run a reconcile sweep before rendering
                the status (the former ``reindex`` behaviour). ``False``
                (default) never sweeps.
            tier: Limit the sweep to one configured source tier. Only
                meaningful with ``reconcile=True``; validated the same way the
                old ``reindex(tier=...)`` was (an unknown tier raises
                :class:`ReindexTierError` naming the valid ones).

        Returns:
            The :class:`IndexStatusSummary` — files_indexed/failed/skipped,
            the embedding-schema/schema-rebuild/calibration sections, the
            last-sync/last-sweep/newest-snapshot ages, and the trace
            aggregates.

        Raises:
            ReindexTierError: ``tier`` is given without ``reconcile=True`` (a
                status-only call would silently ignore it), or ``tier`` names
                a tier the project does not configure.
        """
        if tier is not None and not reconcile:
            raise ReindexTierError(
                f"tier={tier!r} was given but reconcile=False — a status-only "
                "call never sweeps and would silently ignore it. Pass "
                "reconcile=True to sweep that tier (or omit tier to sweep "
                "every configured tier)."
            )
        if reconcile:
            self._validate_tier(tier)
            # The forced-refresh hammer waits for an in-flight schema rebuild
            # to settle first: a rebuild re-embeds every tier, so reconciling
            # on top of a half-finished rebuild would race it. Awaiting it
            # here makes the sweep the deterministic "everything is current
            # now" barrier the callers expect.
            await self._settle_schema_rebuild()
            if self.watcher is not None and self.watcher_started:
                await self.watcher.run_sweep()
            else:
                await self.reconcile_engine.reconcile()
        return await self._build_index_status()

    async def _settle_schema_rebuild(self) -> None:
        """Await a pending background schema-rebuild task so the index is settled.

        A no-op when no rebuild was spawned or it has already finished. Any
        exception the rebuild raised is surfaced here (the rebuild's failure is not
        silently swallowed by a later reindex). After this returns, the manifest's
        rebuild status reflects the rebuild's terminal state (``done`` on success).
        """
        task = self.schema_rebuild_task
        if task is None or task.done():
            return
        await task

    def _validate_tier(self, tier: str | None) -> None:
        """Reject a ``tier`` the project does not declare (fail loud on a typo).

        ``None`` (sweep all) is always valid. Otherwise ``tier`` must match one
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
                f"unknown tier {tier!r}; the tier must be a configured tier "
                f"({valid}) or None (all tiers). Check for a typo, or omit the tier "
                f"to reconcile everything."
            )

    async def _build_index_status(self) -> IndexStatusSummary:
        """Assemble the full freshness/health status — the render both a plain
        status read and a post-sweep read share (P8d Wave 3).

        Attaches the :class:`~loremaster.index.indexer.EmbeddingSchemaStatus`,
        :class:`~loremaster.index.indexer.SchemaRebuildStatus`, P8c
        :class:`CalibrationStatus`, and the P8d Wave 3 ages/traces sections —
        all cheap reads (no embeds):

        * ``embedding_schema`` carries the stamped fingerprint (``None`` until the
          first rebuild completes) and the current epoch constant.
        * ``schema_rebuild`` parses the ``schema_rebuild_status`` JSON blob into the
          model, defaulting to ``state="idle"`` when no rebuild has been recorded.
        * ``calibration`` is the boot calibration engine's
          :meth:`~loremaster.calibration.engine.CalibrationEngine.status` snapshot
          (``None`` when no engine is wired), so the ``state`` string surfaces
          verbatim (``cached`` / ``measured`` / ``drift_adopted`` /
          ``cached_retrying`` / ``integrity_failed``).
        * ``last_sync``/``last_sweep`` are ages since the manifest's
          ``META_LAST_SYNC_AT_KEY``/``META_LAST_SWEEP_AT_KEY`` stamps (the
          watcher's live-apply chokepoint and the reconcile engine's sweep-
          completion chokepoint, respectively) — "never" (all-``None``) before
          the first stamp, honestly, not a crash.
        * ``newest_snapshot`` is the age of the newest ``DiffEngine.list_snapshots``
          row (reused verbatim, ``limit=1`` — no new snapshot query).
        * ``traces`` is the store's ``trace`` table aggregate (per-tool call
          counts + the latest trace timestamp); "none recorded" (all-empty) on
          a fresh/never-traced table.
        """
        from loremaster.index.indexer import (
            META_LAST_SWEEP_AT_KEY,
            META_LAST_SYNC_AT_KEY,
            EmbeddingSchemaStatus,
            SchemaRebuildStatus,
        )
        from loremaster.index.schema import (
            EMBEDDING_SCHEMA_VERSION,
            SCHEMA_FINGERPRINT_META_KEY,
            SCHEMA_REBUILD_STATUS_META_KEY,
        )

        summary = await self.indexer.index_status()
        embedding_schema = EmbeddingSchemaStatus(
            fingerprint=await self.manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY),
            version=EMBEDDING_SCHEMA_VERSION,
        )
        # The rebuild status: parse the stored JSON blob into the model, or fall
        # back to the idle default when absent / malformed (a corrupt blob must
        # not crash a status read).
        raw_status = await self.manifest.meta_get(SCHEMA_REBUILD_STATUS_META_KEY)
        if raw_status is None:
            schema_rebuild = SchemaRebuildStatus()
        else:
            try:
                schema_rebuild = SchemaRebuildStatus.model_validate_json(raw_status)
            except (ValueError, TypeError):
                schema_rebuild = SchemaRebuildStatus()
        engine = self._calibration_engine
        calibration = (
            CalibrationStatus.from_engine_status(engine.status()) if engine is not None else None
        )
        last_sync = await self._age_status(META_LAST_SYNC_AT_KEY)
        last_sweep = await self._age_status(META_LAST_SWEEP_AT_KEY)
        newest_snapshot = await self._newest_snapshot_age()
        traces = await self._trace_summary()
        return IndexStatusSummary(
            files_indexed=summary.files_indexed,
            files_failed=summary.files_failed,
            files_skipped=summary.files_skipped,
            tiers_rebuilt=summary.tiers_rebuilt,
            tiers_skipped=summary.tiers_skipped,
            outcomes=summary.outcomes,
            embedding_schema=embedding_schema,
            schema_rebuild=schema_rebuild,
            calibration=calibration,
            last_sync=last_sync,
            last_sweep=last_sweep,
            newest_snapshot=newest_snapshot,
            traces=traces,
        )

    async def _age_status(self, meta_key: str) -> AgeStatus:
        """Read a manifest ISO-timestamp meta key and compute its age since now."""
        raw = await self.manifest.meta_get(meta_key)
        return self._age_status_from_iso(raw)

    @staticmethod
    def _age_status_from_iso(raw: str | None) -> AgeStatus:
        """Parse a stored ISO timestamp into an age-since-now.

        Renders honestly "never" (an all-``None`` :class:`AgeStatus`) on
        absence OR corruption — a pre-existing deployment has no stamp yet,
        and a malformed stamp must not crash a status read (mirrors
        ``schema_rebuild``'s malformed-blob-falls-back-to-idle idiom above).

        A stamp that PARSES but is timezone-NAIVE is not "malformed" — every
        writer in this codebase stamps ``datetime.now(UTC).isoformat()``
        (tz-aware), so a naive stamp is honestly assumed to be UTC (this
        codebase's own convention) rather than rendered "never" (it DID
        parse; "never" would be a lie) or left to crash the aware−naive
        subtraction below (audit finding 2). It is still data drift worth a
        loud, named log line — something wrote a stamp outside the normal
        path.
        """
        if raw is None:
            return AgeStatus()
        try:
            stamped = datetime.fromisoformat(raw)
        except ValueError:
            return AgeStatus()
        if stamped.tzinfo is None:
            logger.warning("index.age_status.naive_stamp", extra={"raw": raw})
            stamped = stamped.replace(tzinfo=UTC)
        age_seconds = (datetime.now(UTC) - stamped).total_seconds()
        return AgeStatus(at=raw, age_seconds=max(age_seconds, 0.0))

    async def _newest_snapshot_age(self) -> AgeStatus:
        """The newest snapshot's age — reuses ``DiffEngine.list_snapshots(1)``
        verbatim (no new query; ``lore_diff`` already reads through the same
        method with a caller-supplied limit)."""
        snapshots = await self._diff_engine.list_snapshots(1)
        if not snapshots:
            return AgeStatus()
        return self._age_status_from_iso(snapshots[0].created_at)

    async def _trace_summary(self) -> TraceSummary:
        """The store's ``trace`` table aggregate, sorted by tool name for a
        deterministic render (the store itself makes no ordering promise)."""
        rows = await self.write_store.trace_aggregates()
        if not rows:
            return TraceSummary()
        by_tool = sorted(
            (ToolTraceCount(tool=row["tool"], calls=row["calls"]) for row in rows),
            key=lambda item: item.tool,
        )
        total = sum(item.calls for item in by_tool)
        latest_values = [row["latest"] for row in rows if row.get("latest") is not None]
        latest_at = max(latest_values).isoformat() if latest_values else None
        return TraceSummary(total=total, by_tool=by_tool, latest_at=latest_at)

    async def dead_code(
        self,
        *,
        include_tests: bool = False,
        include_dunders: bool = False,
        include_entrypoints: bool = False,
        max_results: int = DEFAULT_DEAD_CODE_MAX_RESULTS,
    ) -> list[DeadCodeNode]:
        """Return the candidate dead/orphaned nodes in the project's LIVE tiers.

        Computes the live tiers from ``self._config.effective_roots`` (only
        ``WATCH_LIVE`` tiers are swept — static-snapshot tiers are skipped). Then
        delegates to ``CodeGraph.dead_code``.

        Not wrapped in ``_raise_if_empty_during_rebuild``: an empty result is the
        SUCCESS case for this tool — it means no dead code was found, NOT that a
        rebuild masked real results. Raising on an empty list would falsely alarm
        on a healthy codebase.
        """
        live_tiers = [
            root.tier for root in self._config.effective_roots if root.watch == WATCH_LIVE
        ]
        return await self.code_graph.dead_code(
            live_tiers,
            include_tests=include_tests,
            include_dunders=include_dunders,
            include_entrypoints=include_entrypoints,
            max_results=max_results,
        )

    async def impact(
        self,
        target: str,
        depth: int = 1,
        max_consumers: int = _IMPACT_DEFAULT_MAX_CONSUMERS,
    ) -> ImpactResult:
        """Return the full "who depends on this?" impact profile of ``target``.

        Delegates to ``self._impact_engine`` (constructed in ``__init__`` over
        THIS context's own ``code_graph`` + ``_rebuild_notice`` probe), which
        gates itself on that probe BEFORE running any query — a verdict is never
        served mid-rebuild, even for a target that would otherwise resolve
        cleanly. ``ImpactRebuildingError`` / ``ImpactTargetNotFoundError``
        propagate UNCHANGED (each already carries a caller-actionable message —
        the rebuilding one names the retry hint, the not-found one names the
        target plus the ``lore_search`` next step), mirroring how ``get_symbol``
        above lets ``GetSymbolError``'s detail reach the agent verbatim.
        """
        return await self._impact_engine.impact(target, depth, max_consumers)

    async def map(
        self,
        budget: int = _MAP_DEFAULT_BUDGET,
        focus: str | None = None,
        tests: bool = False,
    ) -> MapResult:
        """Return the rank-ordered, budget-fitted "orient me here" map of the graph.

        Delegates to ``self._map_engine`` (constructed in ``__init__`` over the
        SAME ``code_graph`` + ``_rebuild_notice`` probe ``impact`` uses above) —
        a ranking is never served mid-rebuild. ``MapRebuildingError`` /
        ``MapFocusNotFoundError`` propagate UNCHANGED, mirroring ``impact``'s
        error-passthrough convention immediately above. ``tests=True`` appends the
        segregated, ``[test]``-marked test-infra section (the default map excludes
        it, surfacing an always-on ``tests=true`` affordance line instead).
        """
        return await self._map_engine.map(budget, focus, tests)

    # -- rebuilding-notice seam (shared by the surviving corpus read tools) -
    #
    # Every corpus read tool surfaces a rebuild UNIFORMLY by RAISING — the only
    # agent-visible, serialization-robust channel (a raised exception becomes an
    # MCP ToolError the agent sees; a custom attribute on a returned list is
    # dropped by the SDK's convert_result, so the agent would see a bare []).
    # P8d Wave 2 (the impact fold): blast_radius/tests_for/references/what_imports
    # are all gone (folded into lore_impact, which gates via its OWN
    # _rebuild_notice probe — see impact()/map() below — never this seam).
    # ``what_imports``'s AppContext handler briefly survived unregistered, kept
    # alive only by test_schema_rebuild.py's TestRebuildingNoticeSeam A8c pin —
    # that test now targets ``impact`` instead (proving the SAME underlying
    # rebuilding_notice signal reaches a second tool family via the engines'
    # proactive gate), so the handler was deleted outright. ``search`` (the
    # published corpus search) is now the SOLE caller of
    # _raise_if_empty_during_rebuild below. The two not-found-raising tools
    # (get_symbol / read) route their own error through _rebuilding_error_or.
    # All three still gate on rebuilding_notice being non-None (state
    # in_progress), so an idle no-match stays a plain empty result / a plain
    # not-found — never a false-positive rebuild signal.

    async def _raise_if_empty_during_rebuild(self, results: list[Any]) -> None:
        """Raise a :class:`SchemaRebuildingError` when ``results`` is empty mid-rebuild.

        The shared seam for the sole surviving list-returning corpus read tool
        (search — what_imports/blast_radius/tests_for were folded into
        lore_impact in P8d Wave 2; what_imports's handler was the last to go).
        An empty result while a rebuild is in progress would mislead the agent
        into believing the project genuinely has no match; raising instead
        surfaces the rebuilding notice on a wire-survivable channel so the
        agent retries. A non-empty result, or an idle store, is a no-op (the
        caller returns the plain result unchanged).

        Args:
            results: The substantive list result of a corpus read tool.

        Raises:
            SchemaRebuildingError: When ``results`` is empty and a rebuild is in
                progress (the message carries the rebuild + progress notice).
        """
        from loremaster.index.schema import rebuilding_notice

        if results:
            return
        notice = await rebuilding_notice(self.manifest)
        if notice is None:
            return
        raise SchemaRebuildingError(notice)

    async def _rebuilding_error_or(self, error: Exception) -> Exception:
        """Return a rebuilding error during a rebuild, else the original error.

        The not-found-tool counterpart of :meth:`_raise_if_empty_during_rebuild`
        for get_symbol / read: a not-found DURING a rebuild may be a
        not-yet-re-embedded file, so the returned error is a
        :class:`SchemaRebuildingError` carrying the rebuilding + progress notice
        alongside the original message (agent-visible, so it retries). When idle,
        the ORIGINAL error is returned so a genuine not-found is reported verbatim.

        Args:
            error: The tool's original not-found exception.

        Returns:
            The original error (idle), or a :class:`SchemaRebuildingError` whose
            message carries the rebuilding notice (rebuild in progress).
        """
        from loremaster.index.schema import rebuilding_notice

        notice = await rebuilding_notice(self.manifest)
        if notice is None:
            return error
        return SchemaRebuildingError(f"{error} ({notice})")

    async def _rebuild_notice(self) -> str | None:
        """The zero-arg rebuild probe injected into ``_impact_engine`` / ``_map_engine``.

        Both engines call this BEFORE running any query and raise their own
        typed rebuilding error (carrying this notice verbatim plus a retry hint)
        when it is non-``None`` — the SAME manifest-meta signal
        (:func:`~loremaster.index.schema.rebuilding_notice`) the corpus read
        tools above probe too (search via ``_raise_if_empty_during_rebuild``;
        get_symbol/read via ``_rebuilding_error_or``; verify inline), just read
        directly rather than only on an already-empty result (lore_impact/
        lore_map gate UNCONDITIONALLY, per their own docstrings).
        """
        from loremaster.index.schema import rebuilding_notice

        return await rebuilding_notice(self.manifest)

    def _count_tokens_single(self, text: str) -> int:
        """Adapt the embedder's BATCH token counter to ``MapEngine``'s single-string form.

        The embedder counts a batch (``list[str] -> list[int]``); ``MapEngine``
        wants a single-string counter (``str -> int``) to measure its growing
        rendered block. Mirrors the SAME adapter shape
        :meth:`~loremaster.index.indexer.Indexer._chunk_context`'s ``count_one``
        already uses for the identical embedder-batch-to-single seam. The
        explicit ``int()`` cast keeps this typecheck-clean: ``loresigil`` ships
        no ``py.typed`` marker, so ``count_tokens``'s real ``list[int]`` return
        type is unfollowed and widens to ``Any`` at the call site.

        The raw voyage count is re-denominated into ~Claude-token currency via a
        multiplicative calibration constant (ceiling semantics: ``math.ceil`` so a
        fractional remainder always rounds the promised cost UP, never down) so a
        budget of B buys at most ~B Claude tokens for the worst observed content
        shape -- the consumer pays in Claude tokens, not voyage tokens.

        The constant is the boot :class:`~loremaster.calibration.engine.
        CalibrationEngine`'s live ``served_constant`` when an engine is wired (so a
        detected token-generation drift is adopted without a redeploy), falling back
        to the committed :data:`TOKEN_BUDGET_CALIBRATION` when no engine is present
        (a test/context that builds none). ``getattr`` — not a plain attribute read
        — so the ``TestTokenBudgetCalibration`` guard's ``SimpleNamespace(embedder=
        ...)`` stand-in (no engine attribute) resolves to the committed constant
        rather than raising ``AttributeError``.
        """
        voyage_count = int(self.embedder.count_tokens([text])[0])
        engine = getattr(self, "_calibration_engine", None)
        calibration = engine.served_constant if engine is not None else TOKEN_BUDGET_CALIBRATION
        return math.ceil(voyage_count * calibration)

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

    async def start_calibration_probe(self) -> None:
        """Start the boot token-calibration probe (non-blocking) and log the wiring.

        Called from the PRODUCTION lifespan after the context is built (never from
        ``build_app_context`` itself, so a test that drives the DI core directly
        never fires the network probe). The engine's ``start`` schedules its probe
        as a background task and returns at once — boot never blocks on the count.
        Emits the structured ``startup.calibration.committed`` boot log line (state
        read AFTER adopting any prior-run cache). A context built without a
        calibration engine (a test seam injecting ``None``) is a silent no-op.
        """
        engine = self._calibration_engine
        if engine is None:
            return
        await engine.start()
        status = engine.status()
        logger.info(
            "startup.calibration.committed",
            extra={
                "committed": status["committed_constant"],
                "state": status["state"],
                "served": status["served_constant"],
                "model": status["model"],
            },
        )

    async def aclose(self) -> None:
        """Stop background tasks, run extension shutdown hooks, close clients.

        Mirrors the lifespan teardown: the background schema-rebuild task (if any)
        and the periodic reconcile task are cancelled, the watcher observer +
        worker are stopped, the extension ``on_shutdown`` hooks run in reverse
        order, and the SQLite handles are closed. The schema-rebuild task is
        cancelled BEFORE the manifest is closed because it writes the rebuild
        status to that manifest — closing it out from under a live rebuild would
        raise on the closed connection. Idempotent enough to be called once at
        lifespan exit (or by a test's ``finally``).
        """
        if self.schema_rebuild_task is not None:
            self.schema_rebuild_task.cancel()
            try:
                await self.schema_rebuild_task
            except (asyncio.CancelledError, Exception):
                # A cancelled or already-failed rebuild is expected at teardown;
                # swallow it so aclose stays idempotent and never re-raises a
                # background failure the caller did not ask about.
                pass
            self.schema_rebuild_task = None
        if self.reconcile_task is not None:
            self.reconcile_task.cancel()
            try:
                await self.reconcile_task
            except asyncio.CancelledError:
                pass
            self.reconcile_task = None
        # P8c: cancel the boot calibration probe cleanly (idempotent — a no-op when
        # the probe was never started, e.g. a test that built the context but did
        # not run the lifespan). An engine stuck retrying an unreachable endpoint
        # must not wedge shutdown; ``stop`` cancels + awaits the parked task.
        if self._calibration_engine is not None:
            await self._calibration_engine.stop()
        if self.watcher is not None and self.watcher_started:
            await self.watcher.stop()
            self.watcher_started = False
        if self._extension_ctx is not None:
            await self._server.run_shutdown_hooks(self._extension_ctx)
        # The stamper owns its OWN connection — close it too, or it outlives
        # the server as a leaked socket (readied last, closed first).
        await self._snapshot_stamper.close()
        # P8b wire-up: the diff engine owns its OWN connection (like the stamper) —
        # close it too. The store-read tool holds no connection of its own (it rides
        # the store + manifest, closed below), so it needs no explicit close.
        await self._diff_engine.close()
        await self.manifest.close()
        await self.code_graph.close()
        await self.write_store.close()
        # The P7 memory backend + task ledger each own a SurrealDB connection —
        # close them too, or they outlive the server as leaked sockets. The P8b
        # finding ledger is the same (its own connection alongside the task ledger).
        await self.memory_backend.close()
        await self.task_ledger.close()
        await self.finding_ledger.close()


# The ``in_progress`` rebuild-status state value the read-tools' rebuilding-notice
# keys on — shared with the schema module's vocabulary (clause 5: one literal for
# the status blob across the producer and the consumers).
_REBUILD_STATE_IN_PROGRESS = "in_progress"

# The ``reason`` recorded in the divergence-heal status blob, distinguishing it from
# the schema-rebuild's ``fingerprint_mismatch`` reason so an operator reading the
# status during a heal sees WHY the rebuilding window is open.
_HEAL_REBUILD_REASON = "store_divergence_heal"


# The rebuild-status state the divergence heal restores the meta to on completion
# when there was NO prior status blob (a fresh boot). It must be ANY value OTHER
# than ``in_progress`` so the read-tools' rebuilding-notice reads idle once the heal
# finishes — a heal that left ``in_progress`` set would wedge every read into a
# phantom rebuilding-notice. ``done`` mirrors the terminal state a completed schema
# rebuild leaves (clause 5: one vocabulary for the status blob).
_HEAL_REBUILD_STATE_DONE = "done"


async def _open_rebuilding_window(manifest: Any) -> str | None:
    """Open the divergence-heal rebuilding-notice window; return the PRIOR status blob.

    Sets ``SCHEMA_REBUILD_STATUS_META_KEY`` to an ``in_progress`` blob so a read
    landing mid-heal sees the rebuilding signal (the read-tools raise
    ``SchemaRebuildingError`` on an empty result while a rebuild is in progress)
    rather than a silent empty result. Returns the raw status blob that was present
    BEFORE the heal so :func:`_restore_rebuilding_window` can put it back verbatim on
    completion (the heal must not clobber a genuine prior rebuild's blob).

    Args:
        manifest: The manifest whose status meta the heal window writes through (the
            same handle the read-tools consult — clause 5: one source of truth).

    Returns:
        The raw ``SCHEMA_REBUILD_STATUS_META_KEY`` value before the window opened, or
        ``None`` when no status was recorded yet.
    """
    from loremaster.index.schema import SCHEMA_REBUILD_STATUS_META_KEY

    prior: str | None = await manifest.meta_get(SCHEMA_REBUILD_STATUS_META_KEY)
    await manifest.meta_set(
        SCHEMA_REBUILD_STATUS_META_KEY,
        json.dumps(
            {
                "state": _REBUILD_STATE_IN_PROGRESS,
                "reason": _HEAL_REBUILD_REASON,
            }
        ),
    )
    return prior


async def _restore_rebuilding_window(manifest: Any, prior_status: str | None) -> None:
    """Close the divergence-heal rebuilding-notice window (out of ``in_progress``).

    Restores the status blob to exactly what it was before the heal opened the
    window: a genuine prior rebuild's blob is put back verbatim; an absent prior
    status becomes a terminal :data:`_HEAL_REBUILD_STATE_DONE` blob (NOT
    ``in_progress``) so a read AFTER the heal does not get a phantom rebuilding
    notice for a finished heal. Either way the final state is never ``in_progress``.

    Args:
        manifest: The manifest whose status meta the window is closed on.
        prior_status: The raw status blob :func:`_open_rebuilding_window` captured
            before the heal — restored verbatim when present.
    """
    from loremaster.index.schema import SCHEMA_REBUILD_STATUS_META_KEY

    if prior_status is not None:
        await manifest.meta_set(SCHEMA_REBUILD_STATUS_META_KEY, prior_status)
        return
    await manifest.meta_set(
        SCHEMA_REBUILD_STATUS_META_KEY,
        json.dumps({"state": _HEAL_REBUILD_STATE_DONE, "reason": _HEAL_REBUILD_REASON}),
    )


async def reconcile_store_divergence(
    *,
    store: Any,
    manifest: Any,
    code_graph: Any,
    config: Any,
    indexer: Any | None = None,
) -> None:
    """Heal a corpus index whose LIVE store/graph diverged from the manifest.

    The idempotent-startup step that runs after the store's ``ensure_ready()`` and before
    the index is declared live. For every configured tier it compares the LIVE
    oracle — ``store.count_points(tier)`` and ``code_graph.indexed_file_count()``
    — against the manifest's honest expectation
    (``manifest.expected_chunks(tier)`` / ``manifest.indexed_file_count(tier)``),
    and heals a divergence:

    * A wiped/short or orphan-over-counted tier (live count != expected) is purged
      (``store.delete_by_tier``) and re-embedded, with ``manifest.reset_tier`` so
      the subsequent sweep re-embeds regardless of the mtime fast-path (FP-02 /
      FP-03 / count-vs-mtime).
    * A wiped graph the manifest still calls indexed (graph count ``0`` over a
      positive manifest count) is repopulated (FP-04).

    Critically idempotent and tier-scoped: a HEALTHY tier (the counts already
    agree) is NEVER purged, so the incremental startup the feature exists to
    provide is not defeated, and a sibling healthy tier is left untouched.

    Args:
        store: The :class:`~loremaster.store.surreal.SurrealStore` (the WRITE-path
            store) the live point-count oracle + the ``delete_by_tier`` purge
            primitive run against.
        manifest: The :class:`~loremaster.index.surreal_manifest.SurrealManifest`
            (the honest expected-count source + the ``reset_tier`` heal trigger).
        code_graph: The :class:`~loremaster.graph_surreal.SurrealCodeGraph` (the
            graph row-count oracle for the FP-04 wiped-graph heal).
        config: The :class:`~loremaster.config.LoreConfig` enumerating the tiers
            to reconcile.
        indexer: The :class:`~loremaster.index.indexer.Indexer` (graph-wired) the
            graph-only heal drives — when the graph is wiped but the live point
            count still AGREES with the manifest (collection healthy, graph-only
            loss), the graph is rebuilt via ``indexer.rebuild_graph_only(tier)``
            WITHOUT a vector purge or re-embed (the FP-04 follow-up efficiency win).
            ``None`` falls back to the count-driven purge+reset path for that case.
    """
    # FP-04: a WIPED/EMPTY graph the manifest still calls indexed is a GLOBAL fact
    # (the graph's file count carries no tier filter). The graph is "wiped" only
    # when it is EMPTY (0 files) AND the manifest holds indexed graph-ELIGIBLE
    # (``.py``) files — because only Python files contribute graph nodes
    # (indexer.py skips non-Python in its graph refresh). A DOCS-ONLY corpus (pure
    # Markdown / text, zero ``.py``) has a LEGITIMATELY empty graph while its rows
    # are indexed in the manifest + store; gating on the ``.py`` indexed count tells
    # that healthy-but-graphless shape apart from a genuinely wiped graph and so
    # avoids false-healing (purging + re-embedding) the whole corpus on every boot.
    # A real wiped graph over a Python corpus still heals (Python files indexed,
    # graph empty → reset → the sweep re-graphs them).
    graph_wiped = (
        await code_graph.indexed_file_count() == 0
        and await manifest.indexed_file_count(suffix=PYTHON_SUFFIX) > 0
    )

    # PASS 1 — PLAN the heal per LIVE tier WITHOUT mutating anything yet, so the
    # rebuilding-notice window (below) is opened ONLY when there is real work. The
    # heal targets the LIVE corpus tiers only — a static tier's snapshot
    # re-acquisition is a separate concern, and the partial-divergence contract
    # requires a healthy sibling tier to be left strictly untouched.
    #
    # Two heal shapes per tier:
    #   * count_diverged (live count != expected): a wiped/short tier (FP-02) or an
    #     orphan over-count (FP-03) — PURGE (delete_by_tier) + reset_tier so the
    #     subsequent sweep re-embeds the REAL content (and rebuilds the graph too).
    #   * graph-only loss (count AGREES but the graph is wiped): the vectors were
    #     never lost, so re-graph from the on-disk source ALONE via the indexer's
    #     rebuild_graph_only — NO purge, NO re-embed (the FP-04 follow-up win). When
    #     no indexer is supplied this falls back to the count-driven purge+reset.
    tiers_to_purge: list[str] = []
    tiers_to_regraph: list[str] = []
    for root in config.effective_roots:
        if root.watch != WATCH_LIVE:
            continue
        tier = root.tier
        # The manifest's HONEST expectation (the indexed-row n_chunks sum) versus
        # the LIVE server count — never a manifest read for the live truth (the
        # manifest is precisely what lies after a wipe). The reconcile only DETECTS
        # + TRIGGERS; it never fabricates points to game this count. After a heal it
        # is the SWEEP that restores the rows to ``indexed`` and the real points to
        # the store, so a SECOND reconcile over the truly-healed index reads the
        # count back in agreement (idempotent) without any placeholder trickery.
        expected = await manifest.expected_chunks(tier)
        live = await store.count(tier)
        # ANY inequality is a heal trigger: a short count is a wiped/short tier
        # (FP-02), an over-count is orphan leftovers (FP-03).
        count_diverged = live != expected
        if count_diverged:
            tiers_to_purge.append(tier)
        elif graph_wiped and indexer is not None:
            # Collection healthy (count agrees) but the graph was lost: re-graph
            # WITHOUT touching the intact vectors. Requires the graph-wired indexer.
            tiers_to_regraph.append(tier)
        elif graph_wiped:
            # No indexer to do the cheap graph-only re-graph — fall back to the
            # count-driven full rebuild so a wiped graph still heals.
            tiers_to_purge.append(tier)
        # else HEALTHY: the live count agrees and the graph is whole — leave the
        # tier strictly alone (the no-false-heal guard). A wasteful purge here would
        # defeat the incremental startup the feature exists to provide.

    if not tiers_to_purge and not tiers_to_regraph:
        # No divergence anywhere — a HEALTHY no-heal reconcile leaves the schema
        # rebuild-status meta strictly UNTOUCHED (no phantom rebuilding window on a
        # clean boot would otherwise wedge every read into a needless notice).
        return

    # PASS 2 — open the rebuilding-notice window for the heal duration, do the work,
    # then restore the prior status. A read landing mid-heal sees ``in_progress`` (so
    # the read-tools' rebuilding-notice covers it) instead of a silent empty result;
    # the status is restored to whatever it was before (idle/absent or a prior real
    # rebuild's blob) on completion, so a finished heal leaves no phantom notice. The
    # heal runs synchronously here, BEFORE _maybe_spawn_schema_rebuild, so it never
    # collides with the background rebuild's own use of the same meta key.
    prior_status = await _open_rebuilding_window(manifest)
    try:
        # PURGE path (FP-02/FP-03/count-vs-mtime): purge the whole tier (clearing
        # orphans and any wiped/partial remnant) and reset its rows out of
        # ``indexed`` so the subsequent build_app_context sweep's ``needs_reindex``
        # returns True and re-embeds the REAL content + rebuilds the graph regardless
        # of the unchanged mtime+size fast-path — the COUNT/graph divergence, not a
        # file change, drives the rebuild. The reconcile upserts NOTHING: restoring
        # the count is the sweep's job, never the reconcile's (a bare reconcile that
        # re-seated fake points would read as 'healthy' after a crash-before-sweep
        # and reintroduce the blind-index bug undetectably).
        for tier in tiers_to_purge:
            await store.delete_by_tier(tier)
            await manifest.reset_tier(tier)
        # GRAPH-ONLY path (FP-04 follow-up): re-graph the tier's indexed .py files
        # from disk WITHOUT a vector purge or re-embed — the collection is intact.
        # tiers_to_regraph is only ever populated when an indexer was supplied (the
        # planning pass gates on ``indexer is not None``), so this is non-None here.
        if tiers_to_regraph:
            assert indexer is not None
            for tier in tiers_to_regraph:
                await indexer.rebuild_graph_only(tier)
    finally:
        await _restore_rebuilding_window(manifest, prior_status)


async def build_app_context(  # noqa: PLR0915 - P8d rewrites this render; restructuring now would churn
    *,
    server: LoreServer,
    embedder: Embedder,
    manifest_path: Path,
    snapshot_root: Path,
    start_tasks: bool = False,
    calibration_engine: CalibrationEngine | None = None,
) -> AppContext:
    """Run the probe gate, construct the runtime services, optionally spawn tasks.

    The dependency-injected core of the lifespan: every collaborator the real
    lifespan builds from config (the embedder, the memory-ledger anchor path, the
    snapshot root) is a parameter, so a test wires a
    :class:`~loresigil.testing.FakeEmbedder` + a throwaway SurrealDB database and
    drives the SAME construction path the server runs.

    Sequence (plan Deliverable 3 lifespan):

    1. Run the **probe gate** (:func:`run_probe_gate`) — refuse on an unreachable
       embedder or a probe/config dim mismatch — then ready the SurrealDB write
       stack (store + manifest + graph + snapshot stamper + memory backend + task
       ledger) against the config dim.
    2. Construct the embedder-injected indexer (with the graph wired in), the
       reconcile engine (with the graph), the search pipeline, and the tier-aware
       read tools.
    3. Run the extension ``on_startup`` hooks — UNWINDING on partial failure (fix
       A): a failing hook aborts the build after tearing the started hooks down.
    4. When ``start_tasks``: run the store-divergence heal + the initial delta
       sweep unconditionally (the corpus is always indexed at startup), then —
       ONLY when ``config.watcher.enabled`` is also ``True`` — start the live
       watcher and create the periodic reconcile asyncio task. A ``watcher:
       {enabled: false}`` corpus is thus indexed once at startup but never
       live-watched afterward (no inotify observer, no periodic reconcile).

    Args:
        server: The composed :class:`LoreServer` (config + extensions).
        embedder: The active embedder (probed by the gate).
        manifest_path: The state-dir anchor whose ``.with_name()`` derives the
            memory-ledger SQLite path (``<slug>.memory.db``) — NOT a manifest
            path; the manifest itself lives in SurrealDB (``config.surreal.*``).
            Retired at P7 when memory moves onto the unified store too.
        snapshot_root: Static-tier snapshot root (also the read-file static base).
        start_tasks: When ``True``, run the initial sweep and — if
            ``config.watcher.enabled`` — start the watcher + periodic reconcile
            task.

    Returns:
        The fully-wired :class:`AppContext`.

    Raises:
        ProbeGateError: If the probe gate refuses.
        Exception: Re-raises a failing extension ``on_startup`` (after unwinding).
    """
    from loremaster.config import resolve_secret
    from loremaster.diff import DiffEngine
    from loremaster.findings import FindingLedger
    from loremaster.graph_surreal import SurrealCodeGraph
    from loremaster.index.indexer import Indexer, graph_roots
    from loremaster.index.reconcile import ReconcileEngine
    from loremaster.index.snapshots import SnapshotStamper
    from loremaster.index.surreal_manifest import SurrealManifest
    from loremaster.index.watcher import LiveWatcher
    from loremaster.memory.ledger import MemoryLedger
    from loremaster.memory.local import LocalMemoryBackend
    from loremaster.search import SearchPipeline
    from loremaster.source.local_directory import LocalDirectorySourceProvider
    from loremaster.store.surreal import SurrealStore
    from loremaster.store_read import StoreReadTool
    from loremaster.symbols import SymbolTool, VerifyTool
    from loremaster.tasks import TaskLedger

    config = server.config
    slug = config.project.slug

    # 1) PROBE GATE (store-agnostic): refuse on an unreachable embedder or a
    # probe/config dim mismatch BEFORE any store is readied. The former READ-path
    # QdrantStore (memory-interim) is gone — memory now serves from the SurrealDB
    # ``memory_backend`` (P7), search + symbols read the unified SurrealStore (P6),
    # and the Qdrant client/deps retired at P8a. Existing-store dim coherence is
    # owned downstream now (the embedding-schema-fingerprint rebuild folds ``dim``
    # in; the memory backend refuses a wrong-dim memory table in ``ensure_ready``).
    #
    # SEAM-8 FOLLOW-UP (P8+): extension-declared keyword/bool payload indexes
    # (``server.payload_index_specs``) were applied to the retired QdrantStore. The
    # unified SurrealStore does not yet apply them (the same declared-not-consumed
    # state the fulltext kind already awaits — EXTENDING.md §3), so a future phase
    # must re-home this index application onto SurrealStore. No current live
    # deployment declares payload indexes, so this is inert today.
    await run_probe_gate(embedder=embedder, config=config)

    # 1b) WRITE-path store: the unified SurrealDB database (SurrealConfig) that
    # holds chunks + file_text + manifest + code graph — the same database a
    # cold `python -m loremaster.index` populates. Credentials resolve by
    # env-var NAME (never inlined), failing loudly when unset.
    surreal_user = resolve_secret(config.surreal.user_env)
    surreal_password = resolve_secret(config.surreal.password_env)
    surreal_database = config.effective_surreal_database
    write_store = SurrealStore(
        url=config.surreal.url,
        namespace=config.surreal.namespace,
        database=surreal_database,
        dim=config.embedding.dim,
        user=surreal_user,
        password=surreal_password,
    )
    # The Surreal WRITE-STACK ready guard (C6-audit follow-up #3): readying the
    # four write backends below can fail PARTWAY through (e.g. the code graph's
    # socket refuses after the store + manifest already came up) — a bare
    # sequence of ``await X.ensure_ready()`` calls would leak every backend that
    # readied successfully before the failure, since the pre-existing
    # ``except BaseException`` further down this function only guards the
    # extension-hooks-and-later phase. Track what has readied so far and close
    # it (newest-first) before re-raising the typed error, mirroring
    # ``Scout.start()``'s identical "close what already opened" pattern.
    write_stack_readied: list[Any] = []
    try:
        await write_store.ensure_ready()
        write_stack_readied.append(write_store)

        # FP-06 durable write-through: the memory ledger lives alongside the
        # manifest on the state volume (``<slug>.memory.db``) — the SAME durable
        # spine the retired Qdrant MemoryStore wrote, so the P7 backend replays the
        # exact rows an older deploy left on disk (durable-spine continuity).
        memory_ledger = MemoryLedger(str(manifest_path.with_name(f"{slug}.memory.db")))

        # 2) Core services — the Surreal write stack (manifest + code graph live in
        # the SAME database as the chunks; ``manifest_path`` survives only as the
        # anchor for the SQLite memory LEDGER above, until P7 moves memory).
        manifest = SurrealManifest(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=surreal_database,
            user=surreal_user,
            password=surreal_password,
        )
        await manifest.ensure_ready()
        write_stack_readied.append(manifest)
        # Wire astroid resolution into the code-graph: it resolves each tier's files on
        # disk under these roots so in-project references become FQNs and external ones
        # are dropped. Derived from the SAME effective roots the indexer walks.
        graph_tier_roots, graph_project_roots = graph_roots(config, snapshot_root)
        code_graph = SurrealCodeGraph(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=surreal_database,
            user=surreal_user,
            password=surreal_password,
            tier_roots=graph_tier_roots,
            project_roots=graph_project_roots,
        )
        await code_graph.ensure_ready()
        write_stack_readied.append(code_graph)
        # The server-side snapshot stamper (C4-audit #2): the CLI/scout wire one, and
        # the server must too, or a live server's periodic reconcile never records a
        # snapshot generation. ONE stamper, readied here and injected into BOTH the
        # indexer AND the reconcile engine below (an unwired stamper stamps nothing).
        # Resolved from ``loremaster.index.snapshots`` at call time (the lazy-import
        # pattern the other write-stack collaborators use).
        snapshot_stamper = SnapshotStamper(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=surreal_database,
            user=surreal_user,
            password=surreal_password,
            store=write_store,
            manifest=manifest,
            project_root=Path(config.project.root),
        )
        await snapshot_stamper.ensure_ready()
        write_stack_readied.append(snapshot_stamper)
        # P8b wire-up: the snapshot diff engine (lore_diff). Mirrors the stamper's
        # construction — the SAME url/ns/db/creds + the store + manifest — but owns
        # its OWN connection for the ``snapshot`` / ``snapshot_entry`` READ queries,
        # readied here and closed in aclose like its sibling ports.
        diff_engine = DiffEngine(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=surreal_database,
            user=surreal_user,
            password=surreal_password,
            store=write_store,
            manifest=manifest,
        )
        await diff_engine.ensure_ready()
        write_stack_readied.append(diff_engine)

        # P7 memory cutover: the SurrealDB-backed memory backend over the SAME
        # per-project database + resolved credentials the write stack uses. Its
        # drift oracle is the cheapest HONEST existence check — a BATCH existence
        # read over the chunk table of the live write store (``_make_existing_chunks``),
        # so a whole recall's refs resolve in ONE query; its durable spine is the
        # ledger above.
        memory_backend = LocalMemoryBackend(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=surreal_database,
            dim=config.embedding.dim,
            user=surreal_user,
            password=surreal_password,
            embedder=embedder,
            existing_chunks=_make_existing_chunks(write_store),
            ledger=memory_ledger,
        )
        await memory_backend.ensure_ready()
        write_stack_readied.append(memory_backend)
        # The durable, fleet-visible task ledger over the same unified database.
        task_ledger = TaskLedger(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=surreal_database,
            user=surreal_user,
            password=surreal_password,
        )
        await task_ledger.ensure_ready()
        write_stack_readied.append(task_ledger)
        # P8b wire-up: the durable, fleet-visible FINDING ledger (lore_findings) —
        # the second ledger over the same unified database, constructed exactly like
        # ``task_ledger`` (its DDL is applied by ``ensure_ready``).
        finding_ledger = FindingLedger(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=surreal_database,
            user=surreal_user,
            password=surreal_password,
        )
        await finding_ledger.ensure_ready()
        write_stack_readied.append(finding_ledger)
        # Replay the durable ledger into the backend ONCE at boot (FP-06): the
        # first boot re-embeds the seeded rows, a second over an in-sync store is a
        # pure no-op (zero document embeds — the divergence guard). Inside the ready
        # guard so a restore failure closes the whole write stack.
        await memory_backend.restore_from_ledger()
    except BaseException:
        # Close what opened, newest-first, before re-raising the typed error —
        # so a mid-ready failure leaks no live write-stack connection.
        for backend in reversed(write_stack_readied):
            with contextlib.suppress(Exception):
                await backend.close()
        raise
    providers = _build_source_providers(server, config, LocalDirectorySourceProvider)
    indexer = Indexer(
        store=write_store,
        embedder=embedder,
        manifest=manifest,
        registry=server.registry,
        source_providers=providers,
        config=config,
        snapshot_root=snapshot_root,
        code_graph=code_graph,
        snapshot_stamper=snapshot_stamper,
    )
    reconcile_engine = ReconcileEngine(
        indexer=indexer, manifest=manifest, store=write_store, config=config,
        code_graph=code_graph, snapshot_stamper=snapshot_stamper,
    )
    # The RUNTIME extension context over the LIVE services — the real embedder,
    # manifest, and the embedder's working ``count_tokens`` (NOT the composition
    # placeholder from LoreServer.extension_context, whose embedder/manifest are
    # None and whose tokenizer refuses to count). The search pipeline carries this
    # so every context-taking search seam (4/5/6/11) sees functional services; the
    # SAME object is reused for the startup hooks below, so seam-9 ``state`` set at
    # startup is visible to the search seams.
    extension_ctx = ExtensionContext(
        # ctx.store is the UNIFIED SurrealStore (P6 close-out ctx.store flip):
        # the same ``write_store`` object the search pipeline reads, so an
        # extension hook that queries ctx.store sees the live corpus, not the
        # legacy Qdrant handle the indexer stopped writing at P5. Memory now lives
        # in the SurrealDB ``memory_backend`` (P7 cutover) — a SEPARATE object,
        # never reachable through ctx.store.
        store=write_store,
        embedder=embedder,
        config=config,
        count_tokens=embedder.count_tokens,
        manifest=manifest,
    )
    search_pipeline = SearchPipeline(
        # P6 read cutover (§6 item 1): the read path is the unified SurrealDB
        # store's ``hybrid_search`` (HNSW ⊕ BM25 via RRF), so the pipeline reads
        # from ``write_store`` (the SurrealStore), NOT the legacy Qdrant handle.
        store=write_store,
        embedder=embedder,
        server=server,
        manifest=manifest,
        config=config,
        extension_context=extension_ctx,
        # §6 item 7: per-hit graph enrichment joins the SAME SurrealCodeGraph the
        # indexer/reconcile write into (already in scope above).
        code_graph=code_graph,
        memory_store=memory_backend,
        # §6 item 9: the reranker seam is config-gated. P6 ships no live reranker
        # client (seam-only), so pass ``None`` — even a configured ``search.
        # reranker`` stays inert until a future build injects the client here.
        reranker=None,
    )
    # P6 store port: SymbolTool's get_symbol reads through the unified
    # SurrealDB store's scroll() primitive, so it depends on write_store
    # (the SurrealStore), NOT the legacy Qdrant handle.
    symbol_tool = SymbolTool(store=write_store)
    # lore_verify's anti-hallucination check rides the SAME resolver as get_symbol
    # over the SAME unified store — so a claim resolves to the identical row.
    verify_tool = VerifyTool(store=write_store)
    # P8b wire-up: lore_read's store-backed span reader — a PURE tool over the SAME
    # unified store + manifest (it owns no connection of its own; both collaborators
    # are already readied above), so it serves the exact bytes lore INDEXED.
    store_read_tool = StoreReadTool(store=write_store, manifest=manifest)

    watcher = LiveWatcher(
        indexer=indexer,
        manifest=manifest,
        store=write_store,
        config=config,
        loop=asyncio.get_running_loop(),
        reconcile_engine=reconcile_engine,
        code_graph=code_graph,
    )

    # P8c: the boot token-calibration engine (closes config-audit F3 — the first
    # prod consumer of ``config.anthropic``). CONSTRUCTED here (loads the packaged
    # baseline + corpus — no network), but its background probe is NOT started here:
    # the lifespan calls ``AppContext.start_calibration_probe`` so a test that drives
    # this DI core directly never reaches the network. Tests inject their own engine
    # (``calibration_engine``); production passes ``None`` → the real engine over
    # ``config.anthropic`` + a findings-ledger adapter, cached at the shared per-slug
    # state dir (``manifest_path.parent``; the engine namespaces its own file by model).
    if calibration_engine is None:
        from loremaster.calibration.engine import CalibrationEngine

        calibration_engine = CalibrationEngine(
            committed_constant=TOKEN_BUDGET_CALIBRATION,
            model=config.anthropic.yardstick_model,
            api_key=resolve_secret(config.anthropic.api_key_env),
            state_dir=manifest_path.parent,
            findings_port=_CalibrationFindingsAdapter(finding_ledger),
        )

    app_context = AppContext(
        server=server,
        embedder=embedder,
        write_store=write_store,
        manifest=manifest,
        code_graph=code_graph,
        snapshot_stamper=snapshot_stamper,
        indexer=indexer,
        reconcile_engine=reconcile_engine,
        watcher=watcher,
        search_pipeline=search_pipeline,
        symbol_tool=symbol_tool,
        verify_tool=verify_tool,
        store_read_tool=store_read_tool,
        diff_engine=diff_engine,
        finding_ledger=finding_ledger,
        memory_backend=memory_backend,
        task_ledger=task_ledger,
        calibration_engine=calibration_engine,
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

        # 4a) Background tasks (watcher + INITIAL reconcile + periodic reconcile).
        # ``start_tasks`` gates the whole startup-tasks path (the test seam this
        # parameter exists for — many tests build with ``start_tasks=False`` to
        # skip ALL of this and drive the manifest/store directly). WITHIN that
        # path, ``config.watcher.enabled`` additionally gates ONLY the live
        # inotify watcher (its observer thread + drain worker) and the periodic
        # reconcile task it schedules below — NOT the initial sweep. A
        # ``watcher: {enabled: false}`` corpus is "static, non-live-watched": it
        # must still be indexed at startup (the divergence heal + initial delta
        # sweep run unconditionally, just below), it just never live-updates
        # afterward (the schema-rebuild decision is independent of both).
        if start_tasks:
            if config.watcher.enabled:
                await watcher.start()
                app_context.watcher_started = True
                logger.info("startup.watcher.started")
            # STORE-DIVERGENCE RECONCILE (idempotent startup, FP-02/03/04/10): heal
            # a corpus whose LIVE store chunk count or graph row count diverged from
            # the manifest BEFORE the initial sweep declares the index live. A wiped/
            # short/over-counted tier (or an empty graph) is purged and its rows
            # reset out of ``indexed`` so the sweep below re-embeds the REAL content
            # + rebuilds the graph regardless of the unchanged-mtime fast-path; a
            # healthy tier is left strictly untouched (no false heal). The reconcile
            # only detects + triggers — it fabricates nothing, so the count is
            # restored by the sweep, not faked. Runs after the store's ensure_ready() + the
            # manifest/graph are built, and before run_sweep, so the heal is
            # effective by the time the context is returned.
            await reconcile_store_divergence(
                store=write_store,
                manifest=manifest,
                code_graph=code_graph,
                config=config,
                indexer=indexer,
            )
            # Capture whether the index was EMPTY *before* the initial sweep — the
            # discriminator the post-sweep stamp gates on (Fix #1). An empty index
            # whose every file the sweep then BUILDS is genuinely current-schema
            # afterwards (safe to stamp without a rebuild); a POPULATED index whose
            # files the sweep merely fast-path-SKIPS is NOT proven current and must
            # NOT be silently stamped. The manifest is read before the sweep walks.
            index_was_empty = len(await manifest.all_files()) == 0
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
            # A fresh deploy over a genuinely EMPTY index (no prior stamp, no prior
            # rows) whose initial sweep just BUILT every file under the current
            # schema already holds CURRENT-schema vectors — it lacks only the stamp.
            # Stamp it now so the rebuild decision below finds the fingerprint
            # matching and does NOT trigger a redundant background rebuild (which
            # would purge the freshly-built index out from under the first reads).
            # This is sound ONLY for an index that was empty before the sweep: a
            # POPULATED-but-unstamped (legacy / unknown-provenance) index was merely
            # fast-path-skipped — its stored vectors are NOT proven current, so it is
            # NOT stamped here (Fix #1) and falls through to a real rebuild below.
            await _stamp_fingerprint_after_fresh_initial_sweep(
                manifest=manifest, config=config, index_was_empty=index_was_empty
            )
            if config.watcher.enabled:
                app_context.reconcile_task = asyncio.get_running_loop().create_task(
                    _periodic_reconcile(watcher, config.watcher.reconcile_interval_s)
                )

        # 4b) Embedding-schema rebuild decision (runs REGARDLESS of start_tasks).
        # If the stored fingerprint is absent or differs from the current config's
        # fingerprint, every stored vector is from a stale embedding schema and
        # must be re-embedded. On a genuine mismatch the manifest status is flipped
        # to in_progress BEFORE spawning (so an immediate index_status() reports the
        # rebuild), then _run_schema_rebuild is spawned as a background asyncio.Task
        # and serves immediately. It re-embeds under the watcher's single-writer
        # lock, so it serialises with the periodic reconcile rather than racing it.
        await _maybe_spawn_schema_rebuild(
            app_context=app_context,
            indexer=indexer,
            manifest=manifest,
            watcher=watcher,
            config=config,
        )
    except BaseException:
        # Tear down whatever started, then close the Surreal handles (idempotent).
        if app_context.schema_rebuild_task is not None:
            app_context.schema_rebuild_task.cancel()
        if app_context.reconcile_task is not None:
            # Without this, a failure AFTER the periodic task spawns leaks a task
            # that later runs a sweep against the just-closed manifest/store —
            # the same orphan-task-vs-closed-DB failure task #16 fixed (audit #2).
            app_context.reconcile_task.cancel()
        # P8c: the calibration probe is started by the lifespan, not here, so this
        # is a no-op on the ordinary build-failure path — but stop it defensively so
        # the invariant "a built engine is always cleanly cancelled" holds regardless.
        with contextlib.suppress(Exception):
            await calibration_engine.stop()
        if app_context.watcher_started:
            await watcher.stop()
        await memory_backend.close()
        await task_ledger.close()
        # P8b wire-up: the finding ledger + diff engine each own a connection —
        # close them on the failure path too (both readied before this point).
        await finding_ledger.close()
        await snapshot_stamper.close()
        await diff_engine.close()
        await manifest.close()
        await code_graph.close()
        await write_store.close()
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


# The reason recorded in the rebuild-status blob when the rebuild is driven by a
# fingerprint mismatch (the only trigger today). Mirrors the indexer's constant so
# the producer (server) and the indexer's own status writes agree on the literal.
_REBUILD_REASON_FINGERPRINT_MISMATCH = "fingerprint_mismatch"


async def _stamp_fingerprint_after_fresh_initial_sweep(
    *, manifest: SurrealManifest, config: LoreConfig, index_was_empty: bool
) -> None:
    """Stamp the current fingerprint after a fresh deploy's initial sweep built the index.

    Called only on the ``start_tasks`` path, right after the initial delta sweep.
    The stamp is the "this index is current-schema, no rebuild needed" optimisation
    — but it is sound ONLY when BOTH hold:

    * the manifest had NO prior fingerprint (unknown provenance), AND
    * the index was EMPTY before the sweep (``index_was_empty``).

    An empty index whose initial sweep BUILT every file embedded everything under
    the current schema, so the stored vectors ARE current — they simply lacked the
    stamp; stamping lets the subsequent rebuild decision skip a redundant rebuild.

    A POPULATED-but-unstamped index (legacy / pre-feature: rows + points present,
    no stamp) is NOT stamped here (Fix #1): the delta sweep merely fast-path-SKIPS
    its unchanged files — it re-embeds NOTHING — so the stored vectors are not
    proven to be the current schema. Stamping it would MASK a needed rebuild, so
    instead it is left unstamped and the fail-safe ``rebuild_needed(None, ·)=True``
    in the rebuild decision spawns the real rebuild.

    A manifest that ALREADY held a fingerprint is likewise left untouched: if it
    matched, nothing to do; if it DIFFERED, the genuine schema mismatch must drive
    a real rebuild — stamping here would falsely mask that.

    Args:
        manifest: The manifest holding (and possibly receiving) the fingerprint stamp.
        config: The validated config the current fingerprint is computed from.
        index_was_empty: Whether the index had no rows BEFORE the initial sweep.
    """
    from loremaster.index.schema import (
        SCHEMA_FINGERPRINT_META_KEY,
        embedding_schema_fingerprint,
    )

    if await manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY) is not None:
        return
    if not index_was_empty:
        # Populated-but-unstamped: unknown provenance over real rows the sweep only
        # skipped — do NOT stamp; let the rebuild decision fail safe into a rebuild.
        return
    await manifest.meta_set(SCHEMA_FINGERPRINT_META_KEY, embedding_schema_fingerprint(config))


async def _maybe_spawn_schema_rebuild(
    *,
    app_context: AppContext,
    indexer: Indexer,
    manifest: SurrealManifest,
    watcher: Any,
    config: LoreConfig,
) -> bool:
    """Decide on the embedding-schema rebuild and spawn it when needed (the A7 wiring).

    Compares the manifest's stored fingerprint against the current config's
    fingerprint. When :func:`~loremaster.index.schema.rebuild_needed` is True
    (absent or differing stamp), the manifest's ``schema_rebuild_status`` is
    flipped to ``in_progress`` BEFORE the task is spawned — so an immediate
    ``index_status`` already reports the rebuild — then :func:`_run_schema_rebuild`
    is launched via ``asyncio.create_task`` and stashed on
    ``app_context.schema_rebuild_task`` (NOT awaited; the server serves at once).

    The spawn is independent of ``start_tasks`` (the periodic watcher loop's
    gate): a fresh deploy with ``start_tasks=False`` must still rebuild on a
    schema mismatch.

    Args:
        app_context: The context the spawned task handle is recorded on.
        indexer: The indexer whose ``rebuild_all`` the task drives.
        manifest: The manifest read for the stored stamp and the status write.
        watcher: The live watcher whose single-writer lock the rebuild holds.
        config: The validated config the current fingerprint is computed from.

    Returns:
        ``True`` when a rebuild task was spawned, ``False`` when the fingerprint
        matched (no rebuild needed).
    """
    from loremaster.index.schema import (
        SCHEMA_FINGERPRINT_META_KEY,
        SCHEMA_REBUILD_STATUS_META_KEY,
        embedding_schema_fingerprint,
        rebuild_needed,
    )

    current_fingerprint = embedding_schema_fingerprint(config)
    stored_fingerprint = await manifest.meta_get(SCHEMA_FINGERPRINT_META_KEY)
    if not rebuild_needed(stored_fingerprint, current_fingerprint):
        app_context.schema_rebuild_task = None
        return False

    # Flip the status to in_progress BEFORE spawning ONLY when a PRIOR fingerprint
    # was stamped — the genuine "the stored vectors are from an older schema epoch"
    # mismatch, where an immediate index_status() must already report the rebuild.
    # A manifest with NO stamp yet (a fresh deploy or a legacy index) is the
    # provenance-unknown case: the rebuild is still spawned (fail safe), but the
    # status blob is left for the background task to write once it actually starts,
    # so a freshly-built context that has not yet touched the index reads as idle
    # rather than claiming an in-progress rebuild that has done no work.
    # Whether the index has NO stored content right now (no manifest rows). An
    # EMPTY index has no stale vectors to fix, so the spawned task only stamps the
    # fingerprint (the empty-index optimisation, uniform with the start_tasks=True
    # post-sweep stamp) rather than churning an in_progress purge+re-embed — which
    # over an empty index would be pointless and would race a direct caller's
    # index_all(). A POPULATED-but-unstamped (legacy / unknown-provenance) index
    # DOES carry stale vectors, so its task does the full re-embed.
    index_was_empty = len(await manifest.all_files()) == 0
    total = indexer.count_files_to_rebuild()
    if stored_fingerprint is not None:
        await manifest.meta_set(
            SCHEMA_REBUILD_STATUS_META_KEY,
            json.dumps(
                {
                    "state": "in_progress",
                    "done": 0,
                    "total": total,
                    "reason": _REBUILD_REASON_FINGERPRINT_MISMATCH,
                    "from_fingerprint": stored_fingerprint,
                    "to_fingerprint": current_fingerprint,
                }
            ),
        )
    logger.info(
        "startup.schema_rebuild.spawn",
        extra={
            "from_fingerprint": stored_fingerprint,
            "to_fingerprint": current_fingerprint,
            "total": total,
            "index_was_empty": index_was_empty,
        },
    )
    app_context.schema_rebuild_task = asyncio.get_running_loop().create_task(
        _run_schema_rebuild(
            indexer=indexer,
            memory_backend=app_context.memory_backend,
            watcher=watcher,
            fingerprint=current_fingerprint,
            index_was_empty=index_was_empty,
            # Re-embed memory only on a GENUINE schema change (a prior fingerprint
            # was stamped and now differs) — not on a fresh / legacy index, where
            # the boot restore already built the memory table at the current schema.
            reembed_memory=stored_fingerprint is not None,
        )
    )
    return True


async def _run_schema_rebuild(
    *,
    indexer: Indexer,
    memory_backend: Any,
    watcher: Any,
    fingerprint: str,
    index_was_empty: bool,
    reembed_memory: bool,
) -> None:
    """Re-embed every tier + the memory table under the writer lock (the rebuild task).

    The concurrency-critical coroutine: it acquires the SAME
    :class:`asyncio.Lock` the watcher's live drain and periodic ``run_sweep`` use
    (``watcher.writer_lock``) and holds it for the WHOLE rebuild, so
    ``rebuild_all`` (which purges + re-embeds every tier) can never run
    concurrently with a live ``index_file`` or a periodic reconcile. The
    fingerprint is stamped by ``rebuild_all`` only after all tiers succeed; a
    failure propagates out of the task (logged by the asyncio default handler /
    awaited at shutdown) WITHOUT stamping, so the next startup re-triggers.

    An index that was EMPTY at spawn time has no stale vectors to fix, so this just
    stamps the fingerprint (the empty-index optimisation) instead of running a
    full, in_progress purge+re-embed — which over an empty index would be a no-op
    purge plus a re-embed that races a direct ``index_all()`` and would leave a
    misleading ``in_progress`` status for reads. A POPULATED-but-unstamped index
    (legacy / unknown provenance) carries genuinely stale vectors, so it gets the
    full :meth:`~loremaster.index.indexer.Indexer.rebuild_all`.

    The MEMORY table joins the SAME pass: ``memory_backend.rebuild_embeddings``
    re-embeds every note from its durable ledger text at the new schema BEFORE the
    fingerprint is stamped, so the stamp is the COMBINED completion evidence for both
    arms (an interrupted memory rebuild re-triggers on the next boot). Unlike the
    chunk arm, the memory arm recreates its table at the current dim, so it also
    heals a DIM change in place — never fail-loud, never a lost memory.

    Args:
        indexer: The indexer whose ``rebuild_all`` performs the chunk re-embed.
        memory_backend: The memory backend whose ``rebuild_embeddings`` re-embeds
            every stored note from its durable ledger text at the new schema.
        watcher: The live watcher exposing the single-writer lock.
        fingerprint: The target fingerprint stamped on successful completion.
        index_was_empty: Whether the index had no stored rows when the task was
            spawned (captured at spawn time so the decision is deterministic, not
            racing a concurrent populate).
        reembed_memory: Whether to run the memory arm — ``True`` only on a genuine
            schema change (a prior fingerprint was stamped and now differs). On a
            fresh / legacy index (no prior stamp) the boot's ``restore_from_ledger``
            already built the memory table at the current schema, so the memory
            re-embed is skipped as redundant (recreating would also needlessly
            block a concurrent recall on the rebuild lock).
    """
    async with watcher.writer_lock:
        try:
            # The MEMORY arm: re-embed every note from its durable ledger text at
            # the new schema (recreating the memory table at the current dim, so a
            # dim change heals in place). Gated on ``reembed_memory`` — a GENUINE
            # schema change, where a PRIOR fingerprint was stamped and now differs
            # (independent of ``index_was_empty``, a chunk-side discriminator: the
            # memory table can be non-empty when the CODE index is empty). When NO
            # prior fingerprint existed (a fresh deploy, or a legacy pre-feature
            # index), the boot's own ``restore_from_ledger`` has ALREADY populated
            # the memory table at the current schema, so re-embedding would be
            # redundant — and recreating would needlessly block concurrent recalls
            # on the rebuild lock that now serialises the drop→re-define window —
            # so it is skipped, mirroring the status
            # semantics (``_maybe_spawn_schema_rebuild`` surfaces ``in_progress``
            # only when a prior fingerprint existed). Runs BEFORE the stamp, so the
            # stamp stays the COMBINED completion evidence for both arms: an
            # interrupted memory rebuild leaves it un-advanced and the next boot
            # re-triggers (crash-safety, mirroring the chunk arm below).
            if reembed_memory:
                await memory_backend.rebuild_embeddings()
            if index_was_empty:
                # Nothing stale to re-embed — just stamp the current fingerprint so
                # the index is marked current-schema (the same end state the
                # empty-index post-sweep stamp produces on the start_tasks=True
                # path). No in_progress churn, so a concurrent / subsequent read
                # never sees a phantom rebuild.
                await indexer.stamp_schema_fingerprint(fingerprint)
                return
            await indexer.rebuild_all(fingerprint)
        except Exception:
            # The rebuild's underlying work raised (e.g. a TEI endpoint down mid-
            # rebuild). Settle the status to the terminal FAILED state so
            # index_status / lore_index report a dead rebuild instead of a
            # perpetual phantom in_progress (FP-11). The fingerprint is left
            # UNSTAMPED (mark_rebuild_failed only touches the status blob), so the
            # next startup re-detects the mismatch and re-triggers — crash-safety
            # unchanged. Re-raise so the failure still propagates out of the task
            # (logged / surfaced by _settle_schema_rebuild at the next reindex).
            await indexer.mark_rebuild_failed(fingerprint)
            raise


async def _periodic_reconcile(watcher: Any, interval_s: int) -> None:
    """Run the reconcile sweep every ``interval_s`` seconds (under the watcher lock).

    The downtime / ``IN_Q_OVERFLOW`` backstop: the sweep re-walks the filesystem
    and re-discovers any change the live watcher dropped. Cancelled at shutdown.
    """
    while True:
        await asyncio.sleep(interval_s)
        try:
            await watcher.run_sweep()
        except Exception:
            # The Surreal store has NO retry layer (fail-fast + reconnect-on-next-
            # call by design), so a transient server blip makes the sweep raise.
            # Swallow-and-log so ONE blip cannot permanently kill the downtime/
            # overflow backstop for the process lifetime (audit #3); the next
            # interval retries over the self-healed connection.
            logger.exception("reconcile.periodic.sweep_failed")


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
    :class:`AppContext` (probe gate + SurrealDB write stack + watcher + tasks);
    every subsequent concurrent lease REUSES the same context (no second
    probe/watcher); and the LAST lease to release tears the context down (plus any
    process-owned client, though the SurrealDB stack self-closes via
    ``AppContext.aclose``). An ``asyncio``
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
        ``AppContext.aclose`` (tasks/watcher/hooks/SurrealDB), then any
        process-owned client (``None`` since the SurrealDB stack self-closes).
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
    """Construct the FastMCP server: lifespan + the built-in tools + extension tools.

    The lifespan builds the live :class:`AppContext` from config (the real
    embedder via :func:`~loremaster.embedding.make_embedder_from_config`, the
    SurrealDB write stack, the default SQLite paths, the snapshot root) and starts
    the watcher + reconcile tasks; teardown closes it. Each tool is a thin wrapper
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

    from loremaster.embedding import make_embedder_from_config

    config = server.config

    async def _build_context() -> tuple[AppContext, Any]:
        """Run the heavy startup once: build the AppContext (SurrealDB write stack).

        Returns:
            The built ``(app_context, None)`` pair the guard reuses across
            sessions. The second element is the process-owned client the guard
            closes on the last release; the SurrealDB stack is owned and torn down
            by ``AppContext.aclose`` itself, so there is no separate client to hand
            back — ``None`` (the guard's release tolerates it).
        """
        app_context = await build_app_context(
            server=server,
            embedder=make_embedder_from_config(config.embedding),
            manifest_path=_DEFAULT_MANIFEST_DIR / f"{config.project.slug}.db",
            snapshot_root=_DEFAULT_SNAPSHOT_ROOT,
            start_tasks=True,
        )
        # P8c: start the boot token-calibration probe HERE (the production lifespan),
        # not inside build_app_context — so the DI core the tests drive directly
        # never fires the network probe. Non-blocking (schedules a background task).
        await app_context.start_calibration_probe()
        return app_context, None

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
    # FastMCP takes no ``version=`` kwarg; the low-level server it wraps carries
    # the wire ``serverInfo.version`` (``create_initialization_options().server_version``).
    # Left as None, the MCP SDK would advertise its OWN version — so set lore's
    # here. Resolve at CONSTRUCTION time so an env baked after import is honoured.
    mcp._mcp_server.version = _resolve_version()
    # Surface the SAME process-lifespan guard on the returned server so the ASGI
    # composition (build_asgi_app) can take the EAGER process-startup lease through
    # it — running the heavy build once at uvicorn startup rather than lazily on the
    # first session. Additive (an attribute), so the single-FastMCP return signature
    # the ~25 callers depend on is unchanged.
    mcp._lore_eager_guard = guard  # type: ignore[attr-defined]
    return mcp


def _app_context(context: Context[Any, AppContext, Any]) -> AppContext:
    """Fetch the live :class:`AppContext` off a request's lifespan context."""
    return context.request_context.lifespan_context


# Tool annotations (mcp-builder: set readOnlyHint / idempotentHint / openWorldHint
# appropriately so a host can reason about a tool before calling it). Every lore
# tool is read-only EXCEPT lore_remember (persists a note) and lore_index's
# reconcile=True path (mutates the index state). openWorldHint is False
# throughout: lore queries THIS project's own closed index, not an open external
# world. The read tools are idempotent (same args → same observable result,
# modulo a live edit re-indexing underneath).
_READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True, idempotentHint=True, openWorldHint=False
)
# lore_remember writes (a new note text creates a new point), so not read-only and
# not idempotent — re-saving the SAME text dedups by deterministic id, but a new
# text is a new write, so we do not advertise idempotency.
_SAVE_MEMORY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False
)
# lore_index CAN mutate index state (reconcile=True re-embeds changed files into
# the store) — a tool that CAN write is annotated by its strongest capability
# even though the default (reconcile=False) call never does, exactly like
# lore_findings/lore_tasks below. The sweep is non-destructive and idempotent
# over an unchanged tree (re-running settles to the same indexed state). Not
# read-only — it can write vectors. (P8d Wave 3: renamed from
# _REINDEX_ANNOTATIONS — lore_reindex no longer exists as a separate tool.)
_INDEX_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False
)
# The fleet task tools mutate the durable ledger (claim / create / transition /
# supersede), so they are NOT read-only; a claim is a compare-and-set and a
# create mints a fresh row each call, so neither is idempotent.
_TASK_TOOL_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False
)
# lore_findings (P8b) mutates the durable finding ledger (report / acknowledge /
# resolve / wontfix), so — like the task tools — it is NOT read-only; a report
# mints a fresh finding each call and a transition drives a state edge, so neither
# is idempotent. (Its query/get/chain_head actions read, but a dispatch tool that
# CAN write is annotated by its strongest capability, exactly as lore_tasks is.)
_FINDINGS_TOOL_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False
)


def _register_tools(mcp: FastMCP, server: LoreServer) -> None:
    """Register the built-in MCP tools, then the extension-contributed tools.

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

    After the built-ins, every registered :class:`Extension`'s seam-3
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
        name="lore_search",
        description=(
            "Semantic, memory-boosted search across THIS project's indexed code and "
            "docs. Your default entry point when you don't already know the exact "
            "symbol name or file path: it ranks by meaning, not by string match. "
            "Returns summarised, [SOURCE:file:line]-cited hits (each with a stable "
            "Key:), never a raw dump. For the EXACT definition of a name you already "
            "know, prefer lore_get_symbol; to read surrounding lines, follow up with "
            "lore_read."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def search(
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
        return await _app_context(context).search(
            query, k, filters, wait_for_fresh=wait_for_fresh, detail_level=detail_level
        )

    @mcp.tool(
        name="lore_get_symbol",
        description=(
            "Resolve a Python symbol name to its EXACT stored definition + on-disk "
            "location (file_path / line span / tier). Use this — NOT lore_search "
            "— when you know the name and want the authoritative definition: it is "
            "collision-correct (a module-qualified name resolves the RIGHT file when "
            "the bare name exists in several), where lore_search is a fuzzy "
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
        name="lore_verify",
        description=(
            "Verify a symbol / signature / location CLAIM against the stored truth "
            "BEFORE you repeat it — the anti-hallucination check. Give the qualified "
            "name (and optionally the file path and/or a signature fragment you "
            "believe are true) and it answers 'confirmed' / 'mismatch' / 'not_found' "
            "with the stored facts: the on-disk anchor + the definition header, and "
            "for a mismatch the ACTUAL path or header. Unlike lore_get_symbol (which "
            "raises when nothing resolves), a miss here is a plain 'not_found' result "
            "— its whole job is answering 'does this exist, exactly as I think?'."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def verify(
        context: Context[Any, AppContext, Any],
        qualified_name: Annotated[
            str,
            Field(
                description=(
                    "A Python dotted name to verify — either MODULE-QUALIFIED "
                    "(e.g. 'loremaster.symbols.SymbolTool.get_symbol') or a BARE "
                    "identity (e.g. 'SymbolTool.get_symbol'). Resolved exactly as "
                    "lore_get_symbol; module-qualify it to disambiguate a name that "
                    "collides across files."
                )
            ),
        ],
        expected_file_path: Annotated[
            str | None,
            Field(
                description=(
                    "Optional: the tier-relative file path you believe defines the "
                    "symbol (e.g. 'loremaster/symbols.py'). Matches if it is a "
                    "whole-path-segment suffix of the stored path in either direction; "
                    "a mismatch names the ACTUAL path. Omit to skip the location check."
                )
            ),
        ] = None,
        expected_signature_fragment: Annotated[
            str | None,
            Field(
                description=(
                    "Optional: a substring you believe appears in the definition's "
                    "header (the class/def signature, kept whole across multiple "
                    "lines). A mismatch shows the ACTUAL header. Omit to skip the "
                    "signature check."
                )
            ),
        ] = None,
    ) -> VerifyResult:
        return await _app_context(context).verify(
            qualified_name, expected_file_path, expected_signature_fragment
        )

    @mcp.tool(
        name="lore_remember",
        description=(
            "Persist a durable note to THIS project's shared memory store; returns "
            "its deterministic id. Use it to record a lasting fact or correction "
            "about this codebase — it is embedded, semantically recalled by "
            "lore_recall, SHARED across every agent on this project, and "
            "survives restarts. Re-saving the same text dedups (same id). This is the "
            "project's shared notebook, distinct from your own cross-project memory."
        ),
        annotations=_SAVE_MEMORY_ANNOTATIONS,
    )
    async def remember(
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
        refs: Annotated[
            list[str] | None,
            Field(
                description=(
                    "Optional chunk Key:s this note pins to (the stable bare-uuid5 keys "
                    "from a search hit). Each folds into the note's deterministic id, so "
                    "the same text pinned to a different chunk is a distinct memory. "
                    "Omit if the note is not about a specific chunk."
                )
            ),
        ] = None,
        metadata: Annotated[
            dict[str, Any] | None,
            Field(
                description=(
                    "DEPRECATED free-form metadata (e.g. {'topic': 'pricing'}); it is "
                    "flattened to flat key=value labels. Prefer 'labels' / 'refs'. Omit "
                    "if none."
                )
            ),
        ] = None,
        kind: Annotated[
            str,
            Field(
                description=(
                    "The memory kind: one of fact / decision / gotcha / uncertainty / "
                    "ongoing (default 'fact'). An unknown kind is rejected by name."
                )
            ),
        ] = _DEFAULT_MEMORY_KIND,
        trust: Annotated[
            str | None,
            Field(
                description=(
                    "Optional trust level of the note's provenance: 'authoritative' (a "
                    "spec/doc) or 'experiential' (an operator note, the default). Omit "
                    "to leave the backend default."
                )
            ),
        ] = None,
        importance: Annotated[
            float | None,
            Field(
                description=(
                    "Optional importance override, a fraction in [0, 1]. Omit to take "
                    "the by-kind default. An out-of-range value is rejected by name."
                )
            ),
        ] = None,
        supersedes: Annotated[
            str | None,
            Field(
                description=(
                    "Optional id of an existing memory this note replaces; the old note "
                    "is kept for audit, closed, and wired forward. Omit for a plain save."
                )
            ),
        ] = None,
        labels: Annotated[
            list[str] | None,
            Field(
                description=(
                    "Optional flat labels stored alongside the note (e.g. ['topic=fees']) "
                    "for later label-filtered recall. Omit if none."
                )
            ),
        ] = None,
    ) -> str:
        return await _app_context(context).remember(
            text,
            refs=refs,
            metadata=metadata,
            kind=kind,
            trust=trust,
            importance=importance,
            supersedes=supersedes,
            labels=labels,
        )

    @mcp.tool(
        name="lore_recall",
        description=(
            "Recall the nearest saved project-memory notes for a query — the read "
            "side of lore_remember. Returns summarised notes (text + metadata + "
            "refs + score) from THIS project's shared, restart-surviving memory. Query "
            "it early when you want prior corrections or durable facts about this "
            "codebase before you start searching the code itself."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def recall(
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
        kind: Annotated[
            str | None,
            Field(
                description=(
                    "Optional exact-match filter on the memory kind: one of fact / "
                    "decision / gotcha / uncertainty / ongoing. Omit to recall every kind."
                )
            ),
        ] = None,
        labels: Annotated[
            list[str] | None,
            Field(
                description=(
                    "Optional ALL-semantics label filter (every requested label must be "
                    "present on a note for it to match, e.g. ['topic=fees']); composes "
                    "with 'kind' as an intersection. Omit for no label filter."
                )
            ),
        ] = None,
    ) -> str:
        return await _app_context(context).recall(query, k, kind=kind, labels=labels)

    @mcp.tool(
        name="lore_claim_task",
        description=(
            "Atomically CLAIM a task for yourself from the project's shared, durable "
            "fleet task ledger — the coordination primitive that lets many agents work "
            "the same backlog without colliding. Exactly one claimant ever wins an open, "
            "unblocked task: a win names you as owner; a loss names the agent already "
            "holding it and changes nothing. Use it to take ownership of a unit of work "
            "before starting it. Create / query / transition tasks with lore_tasks."
        ),
        annotations=_TASK_TOOL_ANNOTATIONS,
    )
    async def claim_task(
        context: Context[Any, AppContext, Any],
        task_id: Annotated[
            str,
            Field(
                description=(
                    "The opaque id of the task to claim (as returned by lore_tasks "
                    "create/query). Must be an open, unblocked, unowned task to win."
                )
            ),
        ],
        owner: Annotated[
            str,
            Field(
                description=(
                    "Your agent/session identity to record as the task's owner on a "
                    "winning claim (e.g. 'agent-alpha')."
                )
            ),
        ],
    ) -> str:
        return await _app_context(context).claim_task(task_id, owner)

    @mcp.tool(
        name="lore_tasks",
        description=(
            "Manage the project's shared, durable fleet task ledger: dispatch on "
            "'action' to CREATE a task, QUERY the ledger (by status / owner / blocked), "
            "TRANSITION a task through its legal state machine, or SUPERSEDE (reframe) a "
            "task. Returns summarised rows, never a raw store dump. This is the "
            "create/read/change side of fleet coordination; to atomically take ownership "
            "of a task, use lore_claim_task."
        ),
        annotations=_TASK_TOOL_ANNOTATIONS,
    )
    async def tasks(
        context: Context[Any, AppContext, Any],
        action: Annotated[
            str,
            Field(
                description=(
                    "The operation: 'create' (mint an open task), 'query' (list tasks), "
                    "'transition' (drive a legal status edge), or 'supersede' (reframe a "
                    "task, minting a successor)."
                )
            ),
        ],
        task_id: Annotated[
            str | None,
            Field(
                description=(
                    "The target task id — required for 'transition' and 'supersede'. "
                    "Omit for 'create' / 'query'."
                )
            ),
        ] = None,
        subject: Annotated[
            str | None,
            Field(
                description=(
                    "The task's short title — required for 'create' and 'supersede'."
                )
            ),
        ] = None,
        description: Annotated[
            str | None,
            Field(
                description=(
                    "The task's longer free-text description — required for 'create' and "
                    "'supersede'."
                )
            ),
        ] = None,
        created_by: Annotated[
            str | None,
            Field(
                description=(
                    "The identity creating the task, recorded in provenance — required "
                    "for 'create' and 'supersede'."
                )
            ),
        ] = None,
        actor: Annotated[
            str | None,
            Field(
                description=(
                    "The identity performing a 'transition', recorded in provenance — "
                    "required for 'transition'."
                )
            ),
        ] = None,
        status: Annotated[
            str | None,
            Field(
                description=(
                    "For 'transition', the target status to move the task to. For "
                    "'query', an optional exact-status filter. Omit otherwise."
                )
            ),
        ] = None,
        owner: Annotated[
            str | None,
            Field(
                description=(
                    "For 'query', an optional filter to tasks currently owned by this "
                    "identity. Omit otherwise."
                )
            ),
        ] = None,
        blocked: Annotated[
            bool | None,
            Field(
                description=(
                    "For 'query', an optional filter to genuinely blocked (True) or "
                    "unblocked (False) tasks. Omit for no dependency filter."
                )
            ),
        ] = None,
        blocked_by: Annotated[
            list[str] | None,
            Field(
                description=(
                    "For 'create', optional ids of tasks the new task depends on (it "
                    "cannot be claimed until every blocker is done/wontfix)."
                )
            ),
        ] = None,
    ) -> str:
        return await _app_context(context).tasks(
            action=action,
            task_id=task_id,
            subject=subject,
            description=description,
            created_by=created_by,
            actor=actor,
            status=status,
            owner=owner,
            blocked=blocked,
            blocked_by=blocked_by,
        )

    @mcp.tool(
        name="lore_read",
        description=(
            "Read a file span — the single read verb. Serves the EXACT bytes lore "
            "INDEXED (a store-backed span) with a [SOURCE:tier:path:start-end] "
            "provenance header, hash-verified against its stored digest, so you quote "
            "real source rather than recalling it. Reach for it after a lore_search / "
            "lore_get_symbol hit to read the surrounding context. Because it serves "
            "the embedded bytes rather than re-reading disk, its header carries a "
            "visible STALE notice whenever the index is behind the file on disk — when "
            "it does, pass wait_for_fresh=True to lore_search (or run "
            "lore_index(reconcile=True)) to bring the span current. Path is "
            "containment-guarded (a '../' traversal, absolute path, or escaping "
            "symlink is rejected)."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def read(
        context: Context[Any, AppContext, Any],
        tier: Annotated[
            str,
            Field(
                description=(
                    "The source tier (root) the file lives in, as named in the project "
                    "config — validated against the configured tiers (an unknown tier "
                    "lists the valid ones). It is the 'tier' in a [SOURCE:tier:...] citation."
                )
            ),
        ],
        path: Annotated[
            str,
            Field(
                description=(
                    "Tier-relative path of the file (e.g. 'pkg/router.py'). "
                    "Containment-guarded — never an absolute path or a '../' escape."
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
                    "Last line to read, 1-based inclusive. Omit to read to EOF; an end "
                    "past EOF is clamped (a tolerant 'from line N onward' read)."
                )
            ),
        ] = None,
    ) -> StoreFileSpan:
        return await _app_context(context).read(tier, path, line_start, line_end)

    @mcp.tool(
        name="lore_diff",
        description=(
            "Show what changed between two index SNAPSHOTS. Call it with NO 'since' "
            "first to LIST the recorded snapshots (their ids, timestamps, file/chunk "
            "counts) — then pass a 'since' id (and optionally 'until'; omit 'until' to "
            "diff against the live 'now' state) to see the added / removed / modified "
            "files plus per-function chunk deltas. The rendered view names its 'legacy' "
            "(reduced-precision, pre-window-ledger) and 'in-flight' (mid-reindex, "
            "excluded from the comparison) markers, so expect them. Read-only."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def diff(
        context: Context[Any, AppContext, Any],
        since: Annotated[
            str | None,
            Field(
                description=(
                    "The BASE snapshot id to diff FROM (e.g. 'snapshot:sn<hex>', exactly "
                    "as the listing returns it). Omit to LIST snapshots instead of diffing."
                )
            ),
        ] = None,
        until: Annotated[
            str | None,
            Field(
                description=(
                    "The TARGET snapshot id to diff TO. Omit (when 'since' is given) to "
                    "diff against the live 'now' state. Ignored when 'since' is omitted."
                )
            ),
        ] = None,
        limit: Annotated[
            int,
            Field(
                description=(
                    "For the LISTING (no 'since'), the max number of snapshots to return, "
                    f"newest first (default {_DEFAULT_DIFF_LIST_LIMIT}; clamped to the "
                    "engine's [1, 500] bound). Ignored when diffing."
                )
            ),
        ] = _DEFAULT_DIFF_LIST_LIMIT,
    ) -> str:
        return await _app_context(context).diff(since=since, until=until, limit=limit)

    @mcp.tool(
        name="lore_findings",
        description=(
            "Manage the project's durable, fleet-visible FINDING ledger (friction, "
            "capability gaps, bugs) — dispatch on 'action' like lore_tasks: 'report' a "
            "finding (needs subject / area / category / created_by; body is optional "
            "and defaults to an empty string — a subject-only quick capture is valid; "
            "kind defaults 'friction'), 'query' by status / kind / area, 'get' or "
            "'chain_head' one by id_or_number, or drive its review state machine — "
            "'acknowledge' / 'resolve' "
            "/ 'wontfix' (by id_or_number + actor, with an optional note). Returns "
            "summarised rows, never a raw store dump."
        ),
        annotations=_FINDINGS_TOOL_ANNOTATIONS,
    )
    async def findings(
        context: Context[Any, AppContext, Any],
        action: Annotated[
            str,
            Field(
                description=(
                    "The operation: 'report' (file a finding), 'query' (list by filters), "
                    "'get' / 'chain_head' (one finding), or a status edge — 'acknowledge' "
                    "/ 'resolve' / 'wontfix'."
                )
            ),
        ],
        id_or_number: Annotated[
            int | str | None,
            Field(
                description=(
                    "The target finding — its stable number (an int, e.g. 7) OR its opaque "
                    "id (a str). Required for 'get' / 'chain_head' / the status edges."
                )
            ),
        ] = None,
        subject: Annotated[
            str | None,
            Field(
                description=(
                    "The finding's short title — required (non-empty) for 'report'."
                )
            ),
        ] = None,
        body: Annotated[
            str | None,
            Field(
                description=(
                    "The finding's longer free-text description — OPTIONAL for "
                    "'report'; an omitted or None body reports as an empty string "
                    "(a subject-only quick capture is a valid finding)."
                )
            ),
        ] = None,
        area: Annotated[
            str | None,
            Field(
                description=(
                    "The tool/subsystem the finding is about (e.g. 'lore_impact') — "
                    "required (non-empty) for 'report'; an optional exact filter for 'query'."
                )
            ),
        ] = None,
        category: Annotated[
            str | None,
            Field(
                description=(
                    "The finding category (e.g. 'capability_gap') — required (non-empty) "
                    "for 'report'."
                )
            ),
        ] = None,
        created_by: Annotated[
            str | None,
            Field(
                description=(
                    "The identity filing the finding, recorded in provenance — required "
                    "(non-empty) for 'report'."
                )
            ),
        ] = None,
        kind: Annotated[
            str | None,
            Field(
                description=(
                    "For 'report', the finding kind (defaults to 'friction' when omitted). "
                    "For 'query', an optional exact-kind filter (omit for every kind)."
                )
            ),
        ] = None,
        actor: Annotated[
            str | None,
            Field(
                description=(
                    "The identity performing a status edge, recorded in provenance — "
                    "required for 'acknowledge' / 'resolve' / 'wontfix'."
                )
            ),
        ] = None,
        note: Annotated[
            str | None,
            Field(
                description=(
                    "An optional free-text note recorded with a 'resolve' / 'wontfix' "
                    "transition. Ignored by the other actions."
                )
            ),
        ] = None,
        status: Annotated[
            str | None,
            Field(
                description=(
                    "For 'query', an optional exact-status filter (open / acknowledged / "
                    "resolved / wontfix). Omit otherwise."
                )
            ),
        ] = None,
        limit: Annotated[
            int,
            Field(
                description=(
                    "For 'query', the max number of findings to return, ordered by number "
                    f"ascending (default {_DEFAULT_FINDINGS_QUERY_LIMIT})."
                )
            ),
        ] = _DEFAULT_FINDINGS_QUERY_LIMIT,
        supersedes: Annotated[
            int | str | None,
            Field(
                description=(
                    "For 'report', an optional id OR number of an existing finding this "
                    "one reframes; the new finding links back to it."
                )
            ),
        ] = None,
    ) -> str:
        return await _app_context(context).findings(
            action=action,
            id_or_number=id_or_number,
            subject=subject,
            body=body,
            area=area,
            category=category,
            created_by=created_by,
            kind=kind,
            actor=actor,
            note=note,
            status=status,
            limit=limit,
            supersedes=supersedes,
        )

    @mcp.tool(
        name="lore_index",
        description=(
            "Index freshness/health status, with an optional force-sweep (merges the "
            "former separate reindex + index-status tools into this one). With NO "
            "arguments: a CHEAP status-only read (files indexed / in-flight / failed "
            "counts, embedding-schema + calibration state, last-sync/last-sweep ages, "
            "newest-snapshot age, per-tool trace-call aggregates) — zero embeds, NEVER "
            "sweeps. Pass reconcile=True to first force a whole-tier reconcile sweep "
            "(optionally scoped via tier) — the heavy 'make everything current now' "
            "hammer, NOT a per-file wait — THEN render the same status over the "
            "just-settled index. You rarely need reconcile=True: the live watcher keeps "
            "the index fresh on save. For the edit-then-immediately-query case, prefer "
            "lore_search(..., wait_for_fresh=True), which is cheaper and targeted."
        ),
        annotations=_INDEX_ANNOTATIONS,
    )
    async def index(
        context: Context[Any, AppContext, Any],
        reconcile: Annotated[
            bool,
            Field(
                description=(
                    "Force a reconcile sweep before reading status. False (default) is "
                    "a pure status read that NEVER sweeps and never mutates anything. "
                    "True runs the sweep (scoped by 'tier'), THEN reads status over the "
                    "just-settled index."
                )
            ),
        ] = False,
        tier: Annotated[
            str | None,
            Field(
                description=(
                    "Limit the sweep to one source tier (e.g. 'custom'). Only honoured "
                    "with reconcile=True — omit (None) to sweep every tier. Passing "
                    "tier without reconcile=True raises (it would otherwise be silently "
                    "ignored by the status-only read)."
                )
            ),
        ] = None,
    ) -> IndexStatusSummary:
        return await _app_context(context).index(reconcile=reconcile, tier=tier)

    # P8d Wave 2 (the impact fold): the lore_what_imports / lore_blast_radius /
    # lore_tests_for / lore_references @mcp.tool registrations were REMOVED
    # here — their capability is absorbed by lore_impact's depth parameter
    # (depth=1 direct consumers, depth>1 transitive rollup) + its
    # covering_tests/production_references/test_references fields. Deletion
    # gate (REPORT-builder-flip-w2.md): grep-confirmed nothing outside these
    # wrappers + their own tests called the corresponding AppContext handlers
    # (impact.py/map.py call the graph_surreal ENGINE methods directly, never
    # these handlers). The what_imports HANDLER itself briefly survived
    # unregistered purely for test_schema_rebuild.py's shared-seam pin; P8d
    # Wave 2 follow-on (fixer-w2f) repointed that pin at lore_impact (which
    # rides the identical rebuilding_notice signal via its own proactive gate)
    # and deleted the handler outright — no residual what_imports surface
    # remains anywhere in AppContext.

    @mcp.tool(
        name="lore_dead_code",
        description=(
            "List CANDIDATE dead/orphaned definitions in the project's live tiers — "
            "nodes with zero PRODUCTION references (a symbol whose only consumers are "
            "its own tests is dead, reason 'only_referenced_by_tests'; one with no "
            "consumers at all is reason 'no_references'). This is a HEURISTIC / "
            "CANDIDATE detector, NOT proof of actual deadness: dynamic dispatch, "
            "decorators, reflection, and symbols used by consumers outside the indexed "
            "tree can evade it. By default excludes test nodes (their own test files), "
            "dunder methods (__init__, __repr__, …), and __main__/__init__ entry modules "
            "— these are always excluded to suppress known false positives; use the "
            "include_* flags to include them. Use lore_impact to investigate a "
            "specific suspect symbol before removing it."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def dead_code(
        context: Context[Any, AppContext, Any],
        include_tests: Annotated[
            bool,
            Field(
                description=(
                    "When True, include nodes whose own file_path is a test file "
                    "(test_*.py, *_test.py, or under a tests/ directory). Default False "
                    "— test nodes are excluded because they are not dead by definition."
                )
            ),
        ] = False,
        include_dunders: Annotated[
            bool,
            Field(
                description=(
                    "When True, include method nodes whose bare name is a dunder "
                    "(__init__, __repr__, __str__, …). Default False — dunders are "
                    "runtime/protocol-invoked and never carry an explicit call edge."
                )
            ),
        ] = False,
        include_entrypoints: Annotated[
            bool,
            Field(
                description=(
                    "When True, include __main__ entry modules and __init__ package "
                    "modules. Default False — these are run as scripts or imported by "
                    "the Python import system, not by dotted-name import edges."
                )
            ),
        ] = False,
        max_results: Annotated[
            int,
            Field(
                ge=_MIN_COUNT,
                le=MAX_DEAD_CODE_MAX_RESULTS,
                description=(
                    f"Maximum number of dead nodes to return (default "
                    f"{DEFAULT_DEAD_CODE_MAX_RESULTS}, min {_MIN_COUNT}, max "
                    f"{MAX_DEAD_CODE_MAX_RESULTS}). Raise it for a broader sweep; "
                    "lower it to keep the result set reviewable."
                ),
            ),
        ] = DEFAULT_DEAD_CODE_MAX_RESULTS,
    ) -> list[DeadCodeNode]:
        return await _app_context(context).dead_code(
            include_tests=include_tests,
            include_dunders=include_dunders,
            include_entrypoints=include_entrypoints,
            max_results=max_results,
        )

    @mcp.tool(
        name="lore_impact",
        description=(
            "Answer 'who depends on this, and is it safe to touch?' for ONE symbol "
            "or module in a single call: production/test reference counts, the "
            "covering tests, and — depending on 'depth' — either the DIRECT "
            "consumer names (depth 1, 'who imports/calls this') or a per-module "
            "TRANSITIVE rollup of the wider ripple (depth > 1, 'what could a change "
            "here break'), plus an explicit verdict ('live' or 'dead (heuristic)') "
            "that always carries an astroid-bounds caveat: a 'dead' verdict is a "
            "LEAD to investigate, never a deletion order, since dynamic / "
            "framework-mediated call sites can undercount. The single graph-read "
            "verb for this project — absorbs what were previously separate "
            "direct-importer / transitive-closure / reference-count / covering-test "
            "tools. Reach for this before removing or refactoring something "
            "lore_dead_code flagged."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def impact(
        context: Context[Any, AppContext, Any],
        target: Annotated[
            str,
            Field(
                description=(
                    "The symbol or module to profile — a dotted name "
                    "(e.g. 'pkg.router.ChampionRouter' or 'pkg.router') or a bare "
                    "identity. Raises a clean not-found (naming the target and "
                    "pointing at lore_search) if it matches nothing indexed."
                )
            ),
        ],
        depth: Annotated[
            int,
            Field(
                ge=_IMPACT_DEPTH_MIN,
                le=_IMPACT_DEPTH_MAX,
                description=(
                    f"Reverse-hop depth for the ripple computation (default 1, min "
                    f"{_IMPACT_DEPTH_MIN}, max {_IMPACT_DEPTH_MAX}). Depth 1 renders "
                    "the direct production consumer names; depth greater than 1 "
                    "switches to a per-module consumer-count rollup of the wider "
                    "ripple instead."
                ),
            ),
        ] = 1,
    ) -> ImpactResult:
        return await _app_context(context).impact(target, depth)

    @mcp.tool(
        name="lore_map",
        description=(
            "Orient yourself in this codebase in one call: a PageRank-style, "
            "token-budgeted rollup of which modules matter most (each with its "
            "rendered symbol names), optionally re-centered on one symbol's own "
            "neighbourhood via 'focus'. Reach for this FIRST when you don't yet "
            "know where to start — before lore_search (which needs a query) "
            "or lore_impact (which needs a known target) — to get the lay "
            "of the land, or re-run it focused to see what surrounds a symbol "
            "you're about to change."
        ),
        annotations=_READ_ONLY_ANNOTATIONS,
    )
    async def map(
        context: Context[Any, AppContext, Any],
        budget: Annotated[
            int,
            Field(
                ge=_MAP_BUDGET_FLOOR,
                le=_MAP_BUDGET_CAP,
                description=(
                    f"Token ceiling for the rendered map (default "
                    f"{_MAP_DEFAULT_BUDGET}, min {_MAP_BUDGET_FLOOR}, max "
                    f"{_MAP_BUDGET_CAP}). Modules squeezed out by the budget are "
                    "counted and named in an explicit elision trailer, never "
                    "silently dropped."
                ),
            ),
        ] = _MAP_DEFAULT_BUDGET,
        focus: Annotated[
            str | None,
            Field(
                description=(
                    "An optional bare or dotted symbol name to re-center the "
                    "ranking on its own neighbourhood (its defining module plus "
                    "the modules that reference it), instead of ranking the whole "
                    "graph uniformly. Omit for an unfocused, whole-corpus map."
                )
            ),
        ] = None,
        tests: Annotated[
            bool,
            Field(
                description=(
                    "Include the segregated, [test]-marked test-infra section. The "
                    "default map excludes test modules from the rendering (their "
                    "import edges still feed production rank) and surfaces an "
                    "always-on 'tests=true' affordance line naming the top test "
                    "hub(s); set true to append the rolled-up test section."
                )
            ),
        ] = False,
    ) -> MapResult:
        return await _app_context(context).map(budget, focus, tests)

    # After the built-ins, register the extension-contributed seam-3 tools.
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
        mcp: The FastMCP server (the built-ins are already registered).
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
                f"tool name must be unique across the built-ins and every extension)."
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


# ASGI typing aliases for the eager-startup interceptor. An ASGI app is
# ``(scope, receive, send) -> awaitable[None]`` and needs no Starlette import.
# These are byte-for-byte identical to the ones in loremaster.auth, but kept
# LOCAL on purpose rather than imported: auth's copies are module-PRIVATE
# (underscore-prefixed), so reusing them would reach into another module's
# private surface, and server.py deliberately imports auth only LAZILY inside
# build_asgi_app — a module-level ``from loremaster.auth import _Scope, ...``
# would add an eager import edge to dedup five trivial stdlib-typed lines. If a
# shared ASGI-types home is ever wanted, promote them to a public module; that
# is an API-surface (CONTRACT) decision, not this refactor's call.
_Scope = MutableMapping[str, Any]
_Message = MutableMapping[str, Any]
_Receive = Callable[[], Awaitable[_Message]]
_Send = Callable[[_Message], Awaitable[None]]
_ASGIApp = Callable[[_Scope, _Receive, _Send], Awaitable[None]]

# ASGI lifespan protocol message types (server <- uvicorn / server -> uvicorn).
_LIFESPAN_SCOPE = "lifespan"
_LIFESPAN_STARTUP = "lifespan.startup"
_LIFESPAN_STARTUP_COMPLETE = "lifespan.startup.complete"
_LIFESPAN_STARTUP_FAILED = "lifespan.startup.failed"
_LIFESPAN_SHUTDOWN = "lifespan.shutdown"
_LIFESPAN_SHUTDOWN_COMPLETE = "lifespan.shutdown.complete"
# Operator-safe FIXED message for an eager-build failure surfaced as the ASGI
# lifespan.startup.failed event. WHY a constant and not str(exc): uvicorn logs
# this message UNREDACTED at process startup, so a credentialed config (e.g. a
# surreal.url or embedding base_url with user:pass@host surfacing in a transport
# exception) would leak verbatim into the startup log. The real detail is logged
# through the module logger (the redaction-backstopped lore sink) instead — see
# _drive_lifespan.
_EAGER_BUILD_FAILED_MESSAGE = "eager startup build failed; see server logs"

# FP-07 — bounded retry-with-backoff for the eager heavy build at process startup.
# A TRANSIENT SurrealDB/TEI outage at boot makes the eager build raise once ->
# lifespan.startup.failed -> uvicorn aborts -> the container EXITS with no
# auto-retry. A brief dependency blip should not permanently down the container, so
# the eager startup retries the build up to ``_DEFAULT_EAGER_MAX_ATTEMPTS`` times
# (> 1, so the default is BOUNDED, not single-shot), sleeping
# ``_DEFAULT_EAGER_BACKOFF_BASE_S`` seconds between attempts. Failing EVERY attempt
# still surfaces lifespan.startup.failed (fail-closed after exhausting the budget)
# so uvicorn aborts a genuinely-down dependency rather than looping forever. These
# are the PRODUCTION defaults; tests inject a tiny N + zero backoff to stay fast.
_DEFAULT_EAGER_MAX_ATTEMPTS = 5
_DEFAULT_EAGER_BACKOFF_BASE_S = 2.0


class _EagerStartupLifespan:
    """ASGI lifespan-interceptor that runs loremaster's heavy build EAGERLY.

    Today the heavy startup (probe gate -> initial reconcile -> schema self-heal ->
    file watcher) runs in FastMCP's per-MCP-SESSION user lifespan, so a freshly
    (re)started container does nothing heavy until the FIRST client connects — a
    dead index that *looks* up. This wrapper hoists that build to the ASGI/uvicorn
    PROCESS startup (the ``lifespan.startup`` event): it drives the inner streamable
    app's own session-manager lifespan (so the server still serves) AND takes a
    PROCESS-LIFETIME eager lease against the guard ``build_mcp_server`` surfaced — so
    the heavy build runs ONCE at startup and the shared :class:`AppContext` survives
    between sessions (no per-session build/teardown churn; every per-session lease
    just reuses the eager one). On ``lifespan.shutdown`` it releases the eager lease
    (-> AppContext teardown, incl. the SurrealDB write stack) and exits the inner
    lifespan.

    Only the ``lifespan`` scope is intercepted; every other scope (``http``) is
    delegated straight to the inner app, so the Origin/Bearer wrapping that sits
    OUTSIDE this interceptor (and the inner app's HTTP routing) is untouched.
    """

    def __init__(
        self,
        inner: _ASGIApp,
        guard: Any | None,
        *,
        max_attempts: int = _DEFAULT_EAGER_MAX_ATTEMPTS,
        backoff_base_s: float = _DEFAULT_EAGER_BACKOFF_BASE_S,
    ) -> None:
        """Wrap the inner streamable app + (optionally) the eager lease guard.

        Args:
            inner: The inner streamable-http (Starlette) ASGI app — its own ASGI
                lifespan starts/stops the session manager / task group.
            guard: The :class:`_ProcessLifespanGuard` ``build_mcp_server`` surfaced
                on the FastMCP object (via ``mcp._lore_eager_guard``), or ``None``.
                Tolerated as ``None`` defensively — the inner lifespan still runs,
                the eager lease is simply skipped (no heavy build hoisted).
            max_attempts: The BOUNDED retry budget for the eager heavy build at
                ``lifespan.startup`` (FP-07). A transient SurrealDB/TEI blip is retried
                up to this many times before failing closed; the production default
                is ``_DEFAULT_EAGER_MAX_ATTEMPTS`` (> 1, so it is never single-shot).
            backoff_base_s: Seconds slept between failed eager-build attempts. The
                production default is ``_DEFAULT_EAGER_BACKOFF_BASE_S``; tests inject
                zero so the suite never sleeps on a deliberately-failing build.
        """
        self._inner = inner
        self._guard = guard
        # The bounded retry policy is honoured ONLY when there is a guard to retry
        # against — a max_attempts below 1 is clamped to a single attempt so the
        # eager build always runs at least once.
        self._max_attempts = max(1, max_attempts)
        self._backoff_base_s = backoff_base_s

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        """Intercept only the ``lifespan`` scope; delegate everything else.

        Non-lifespan scopes (HTTP) pass straight through to the inner app so this
        interceptor never touches request routing — the security middleware wrapping
        it stays in force verbatim.
        """
        if scope.get("type") != _LIFESPAN_SCOPE:
            await self._inner(scope, receive, send)
            return
        await self._drive_lifespan(scope, receive, send)

    async def _drive_lifespan(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        """Drive the ASGI lifespan protocol with the eager build composed in.

        Runs the inner app's own lifespan in a background task (bridged by
        per-direction message queues) so the eager lease can be sequenced AROUND it:
        the inner session manager starts first, THEN the eager lease is taken (the
        heavy build) before reporting startup complete; on shutdown the eager lease
        is released BEFORE the inner lifespan exits, so the AppContext teardown never
        outlives the session manager. A failed eager build is reported as
        ``lifespan.startup.failed`` and nothing is cached (the guard does not cache
        failures), so a later startup retries.
        """
        # Bridge queues: the inner app pulls its lifespan messages from inbox and
        # pushes its replies to outbox; this coroutine sequences both.
        inbox: asyncio.Queue[_Message] = asyncio.Queue()
        outbox: asyncio.Queue[_Message] = asyncio.Queue()

        async def inner_receive() -> _Message:
            return await inbox.get()

        async def inner_send(message: _Message) -> None:
            await outbox.put(message)

        # create_task (not ensure_future): this coroutine always runs under a live
        # event loop, and the modern idiom returns a concrete asyncio.Task. The
        # inner call is wrapped so its broad _ASGIApp Awaitable return is awaited as
        # a coroutine (what create_task requires) without narrowing the alias.
        async def _run_inner() -> None:
            await self._inner(scope, inner_receive, inner_send)

        inner_task: asyncio.Task[None] = asyncio.create_task(_run_inner())
        try:
            # The first lifespan message from uvicorn must be the startup event.
            # A hard check (not an ``assert``): asserts are stripped under
            # ``python -O``, and an out-of-protocol first message must surface as a
            # real error rather than silently driving the inner startup over it.
            message = await receive()
            if message["type"] != _LIFESPAN_STARTUP:
                raise RuntimeError(
                    f"expected {_LIFESPAN_STARTUP} first, got {message['type']!r}"
                )
            # 1) Start the inner session-manager lifespan and await its reply.
            await inbox.put({"type": _LIFESPAN_STARTUP})
            inner_startup = await outbox.get()
            if inner_startup["type"] == _LIFESPAN_STARTUP_FAILED:
                # The inner app itself failed to start — relay the failure verbatim
                # WITHOUT taking the eager lease, and do not report complete.
                await send(inner_startup)
                await inner_task
                return
            # 2) Take the PROCESS-LIFETIME eager lease — the heavy build. Skipped
            #    when no guard was surfaced (defensive), so the inner still runs.
            #    FP-07: a transient SurrealDB/TEI outage at boot must not permanently
            #    down the container, so the build is RETRIED with bounded backoff —
            #    up to self._max_attempts acquires, sleeping self._backoff_base_s
            #    between failures. A build that fails K < N times then succeeds comes
            #    up cleanly; failing ALL N attempts surfaces lifespan.startup.failed
            #    (fail-closed) so uvicorn aborts a genuinely-down dependency.
            if self._guard is not None:
                last_exc = await self._acquire_eager_lease_with_retry()
                if last_exc is not None:
                    # Every retry was exhausted — surface the failure so uvicorn
                    # aborts; nothing is cached (the guard rolls each failed acquire
                    # back), so a later startup retries. Tear the already-started
                    # inner lifespan back down before failing.
                    await self._shutdown_inner(inbox, outbox, inner_task)
                    # Log the REAL detail (with traceback) through the module logger,
                    # which is the redaction-backstopped lore sink, so operators
                    # still learn WHY startup failed. The ASGI message below stays a
                    # FIXED operator-safe phrase — never str(exc) — because uvicorn
                    # logs that message UNREDACTED at startup, so any secret-bearing
                    # exception text (e.g. a credentialed surreal.url) must not reach
                    # it.
                    logger.error("eager startup build failed", exc_info=last_exc)
                    await send(
                        {
                            "type": _LIFESPAN_STARTUP_FAILED,
                            "message": _EAGER_BUILD_FAILED_MESSAGE,
                        }
                    )
                    return
            # 3) Both the inner session manager and the eager build are up.
            await send({"type": _LIFESPAN_STARTUP_COMPLETE})

            # Block until uvicorn signals shutdown. Hard check (asserts are stripped
            # under ``python -O``): an out-of-protocol message here must error, not
            # silently fall through into the shutdown-and-release path.
            message = await receive()
            if message["type"] != _LIFESPAN_SHUTDOWN:
                raise RuntimeError(
                    f"expected {_LIFESPAN_SHUTDOWN}, got {message['type']!r}"
                )
            # 4) Release the eager lease (-> teardown) BEFORE exiting the inner
            #    lifespan, so the AppContext teardown does not outlive the session
            #    manager unexpectedly.
            if self._guard is not None:
                await self._guard.release()
            await self._shutdown_inner(inbox, outbox, inner_task)
            await send({"type": _LIFESPAN_SHUTDOWN_COMPLETE})
        finally:
            # Never leak the inner lifespan task if this coroutine unwinds early
            # (e.g. a test stops the handshake by raising from its send). Cancel it
            # AND await its settling so the CancelledError is retrieved deterministically
            # within this scope — leaving it to loop-teardown timing risks a
            # "Task was destroyed but it is pending" warning.
            if not inner_task.done():
                inner_task.cancel()
                try:
                    await inner_task
                except asyncio.CancelledError:
                    pass

    async def _acquire_eager_lease_with_retry(self) -> BaseException | None:
        """Acquire the eager lease, retrying a transient failure with bounded backoff.

        FP-07. Attempts ``self._guard.acquire()`` up to ``self._max_attempts``
        times, sleeping ``self._backoff_base_s`` seconds between failures. Returns
        ``None`` the instant an acquire SUCCEEDS (the eager lease is then held — the
        heavy build ran). Returns the LAST exception when every attempt failed, so
        the caller can surface ``lifespan.startup.failed`` (fail-closed) after the
        budget is exhausted — never an unbounded retry loop that would stop uvicorn
        ever aborting a genuinely-down dependency.

        The guard's own no-cache-on-failure contract makes the retry safe: a failed
        ``acquire`` rolls back without caching, so a subsequent attempt rebuilds
        cleanly rather than re-serving a half-built context.

        Returns:
            ``None`` on success (lease held), or the last :class:`BaseException`
            raised when all ``self._max_attempts`` attempts failed.
        """
        # The caller only invokes this helper when a guard was surfaced, so the
        # guard is non-None here (mypy can't see the caller's guard-check).
        assert self._guard is not None
        last_exc: BaseException | None = None
        for attempt in range(self._max_attempts):
            try:
                await self._guard.acquire()
                return None
            except BaseException as exc:  # noqa: BLE001 — surface any build failure
                last_exc = exc
                # Sleep between attempts ONLY when another attempt remains, so a
                # final-attempt failure fails closed immediately. A zero backoff
                # (the test policy) makes this a no-op delay.
                if attempt + 1 < self._max_attempts:
                    logger.warning(
                        "eager startup build attempt failed; retrying",
                        extra={
                            "attempt": attempt + 1,
                            "max_attempts": self._max_attempts,
                        },
                    )
                    if self._backoff_base_s > 0:
                        await asyncio.sleep(self._backoff_base_s)
        return last_exc

    @staticmethod
    async def _shutdown_inner(
        inbox: asyncio.Queue[_Message],
        outbox: asyncio.Queue[_Message],
        inner_task: asyncio.Task[None],
    ) -> None:
        """Drive the inner app's lifespan shutdown and await its clean exit."""
        await inbox.put({"type": _LIFESPAN_SHUTDOWN})
        # Drain the inner shutdown reply so its lifespan_context fully exits.
        await outbox.get()
        await inner_task


def build_asgi_app(mcp: Any, config: LoreConfig) -> Any:
    """Assemble the streamable-http ASGI app: Origin-guarded, Bearer-gated if auth.

    The single place the served app is built and gated. Two layers wrap the
    streamable-http app:

    * **Origin (DNS-rebinding) guard — ALWAYS on (D11/mcp-builder).** The local
      streamable-HTTP server binds loopback, but a browser tricked by DNS rebinding
      still reaches it carrying an attacker ``Origin``; the
      :class:`~loremaster.auth.OriginValidationMiddleware` rejects any non-loopback,
      non-configured Origin with 403 while ALLOWING an absent Origin (a non-browser
      local client) and loopback — so the no-auth localhost default is unbroken.
    * **Bearer auth — when an enabled ``auth`` block is configured (D9/D11).** The
      app is additionally wrapped in
      :class:`~loremaster.auth.BearerAuthMiddleware` over the configured named-key
      set; Bearer is the OUTERMOST layer so a request is authenticated, then
      Origin-checked, then served.

    Args:
        mcp: The FastMCP server (its ``streamable_http_app`` is the inner app).
        config: The project config (its ``auth`` block decides the Bearer gating;
            ``server.host`` provides the loopback bind the Origin guard defends).

    Returns:
        The ASGI app to serve: ``Origin(app)`` (no auth) or
        ``Bearer(Origin(app))`` (auth enabled).
    """
    from loremaster.auth import OriginValidationMiddleware

    inner: Any = mcp.streamable_http_app()
    # The heavy build runs EAGERLY at process startup: wrap the inner streamable app
    # in a lifespan-interceptor that, on lifespan.startup, both enters the inner
    # session-manager lifespan (so the server serves) AND takes the process-lifetime
    # eager lease through the guard build_mcp_server surfaced. HTTP scopes pass
    # straight through, so the Origin/Bearer wrapping below is untouched.
    eager_guard = getattr(mcp, "_lore_eager_guard", None)
    # FP-07: wire the PRODUCTION-default BOUNDED retry policy (N > 1 + a real
    # backoff) so a brief boot-time SurrealDB/TEI blip is retried rather than aborting
    # the container on the first failure. Passed explicitly so the production
    # composition's bounded-not-single-shot behaviour is unmistakable at the seam.
    app: Any = _EagerStartupLifespan(
        inner,
        eager_guard,
        max_attempts=_DEFAULT_EAGER_MAX_ATTEMPTS,
        backoff_base_s=_DEFAULT_EAGER_BACKOFF_BASE_S,
    )
    # The Origin guard runs for every deployment (DNS-rebinding defense), with the
    # configured server bind's own origin implicitly covered by the loopback allow
    # (the local single-user deploy binds 127.0.0.1). Extra trusted origins can be
    # threaded here in a future config knob; loopback + absent is the secure default.
    app = OriginValidationMiddleware(app)
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
