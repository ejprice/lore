# Extending loremaster

A domain-specific MCP (e.g. a future `odoo-code`) plugs into `loremaster` by
subclassing `loremaster.extension.Extension` and handing the instance to
`LoreServer.register_extension()`. This document describes that surface as it
stands at the **P6 close-out** (task #16) — the unified SurrealDB read path is
live for search + symbols; memory is still on Qdrant until P7.

**Pre-1.0 stance:** breaking changes to this surface are allowed. No extension
ships against loremaster yet, so a seam can be renamed or reshaped between
releases without a deprecation cycle — see the `FieldIndexSpec` rename in this
same cycle (§3) for the precedent. Do not treat anything below as a stability
guarantee; treat it as "true as of this commit."

For the *lower* layer — writing the `Chunker` / `SchemaProfile` / `JsProfile`
the seams contribute — see `lorescribe/EXTENDING.md`.

## The composition model

```python
from loremaster.server import LoreServer

(
    LoreServer.from_config("lore.yaml")    # load + validate config → bare generic RAG
    .register_extension(MyExtension())     # compose a domain extension (chainable)
    .run()                                 # configure logging + serve (FastMCP streamable-http via uvicorn)
)
```

- **`LoreServer.from_config(path)`** loads and validates `lore.yaml` and stands
  up a **bare** server. A bare server is the generic RAG: its `registry` is the
  default `lorescribe` registry, its citation format is the base default, and
  no extension hook fires.
- **`register_extension(ext)`** composes an extension and **returns `self`**
  for chaining, so you can register zero or more. The order inside is
  deliberate: the config slice validates **first** (seam 7 —
  `LoreServer._validate_extension_config` — fail loud before mutating any
  registry state), then chunkers register under the register guard (§8), then
  profiles and the remaining seams (8/10) are collected.
- **`run()`** configures the lore-namespace structured-logging handler
  **before** `build_mcp_server` (FastMCP's own `__init__` installs a root
  `RichHandler`; configuring first keeps every startup event on the JSON
  sink), registers the twelve MCP tools, builds the ASGI app (an
  Origin-validation guard runs always; Bearer auth additionally wraps it when
  an enabled `auth` block is configured), and serves the FastMCP
  streamable-http app via uvicorn on the configured host/port. FastMCP enters
  the lifespan once per MCP **session**, so the heavy startup (probe-gate /
  initial reconcile / watcher) and the extension lifespan hooks are made
  idempotent per **process** by `_ProcessLifespanGuard` — a reference-counted
  lease: the first session builds the shared `AppContext`, concurrent sessions
  reuse it, and the last to exit tears it down.

The wired surface a composed server exposes:

| Accessor / method | What it yields |
|---|---|
| `server.registry` | the composed `ChunkerRegistry` (default + extension chunkers/profiles) |
| `server.payload_index_specs` | extension-declared extra field indexes (seam 8, §3) |
| `server.source_providers` | extension-contributed source providers (seam 10, §7) |
| `server.tool_specs(ctx)` | every extension's declarative `ToolSpec`s, over the shared context — used at **registration** time to derive each tool's FastMCP schema (§2) |
| `server.extension_tool_specs(ctx)` | the same specs, but each resolved over its own extension's **child** context — what the live server calls at invocation time |
| `server.format_result(result, ctx)` | resolved citation/format, first non-`None` wins (seam 5) |
| `server.chunk_key(payload, ctx)` | resolved semantic memory-key, first non-`None` wins (seam 6) |
| `server.classify_detail(chunk_type)` | resolved detail level (seam 11), falling back to base |
| `server.augment_candidates(query, candidates, ctx)` / `server.rerank(candidates, ctx)` | each extension's hook, chained (seam 4, §4) |
| `await server.run_startup_hooks(ctx)` / `run_shutdown_hooks(ctx)` | lifespan (seam 9; shutdown runs in **reverse** order, unwinding on partial startup failure) |
| `server.extension_config(name)` | the validated per-extension config slice (seam 7, §6) |

## The eleven seams

`Extension` is an ABC (`loremaster/extension.py`) with a required `name`
property and eleven seams, each shipping a safe, inert default (`[]` / `None`
/ identity / async no-op) so a server with zero extensions registered behaves
as the generic code/docs RAG:

1. `chunkers() -> list[Chunker]` — contribute `lorescribe.base.Chunker`s.
   Override when your domain has file types the generic chunkers don't cover.
2. `xml_profiles() -> list[Any]` / `js_profiles() -> list[Any]` — contribute
   XML `SchemaProfile`s / `JsProfile`s. Override to retag, skip, or force
   standalone granularity for domain-significant elements.
3. `tools(ctx: ExtensionContext) -> list[ToolSpec]` — declarative, index-backed
   tools (§2). Override when your domain has structured lookups beyond
   semantic search.
4. `augment_candidates(query, candidates, ctx)` /
   `rerank(candidates, ctx)` — the search-pipeline hook (§4). Override to bias
   retrieval toward domain-significant candidates.
5. `format_result(result, ctx) -> str | None` — a custom citation/format;
   `None` falls through to the base's `[SOURCE:file:line]` format.
6. `chunk_key(payload, ctx) -> str | None` — the versioned semantic
   memory-key for correction matching; `None` falls through to the base's
   structural point-id. Fold `self.key_version` into the output so a
   keying-scheme change is detectable and migratable.
7. `config_model() -> type[BaseModel] | None` — validates the extension's
   `extensions[name]` config slice (§6); `None` means no extra config.
8. `payload_indexes() -> list[FieldIndexSpec]` — extra field indexes to
   declare (§3).
9. `on_startup(ctx)` / `on_shutdown(ctx)` — async lifespan hooks. Override
   when your domain holds a resource needing setup/teardown.
10. `source_providers() -> list[Any]` — indexer-side acquisition providers
    (`SourceProvider` Protocol, §7).
11. `classify_detail(chunk_type) -> DetailLevel | None` — chunk-type →
    `"summary"`/`"source"` detail-level classification; `None` defers to the
    base default.

An extension also carries `key_version: int` (default `1`,
`loremaster.extension.DEFAULT_KEY_VERSION`), which it should fold into its
`chunk_key()` output so a keying-scheme change is detectable and migratable.

## §2 — Declarative tools (seam 3)

`ToolSpec` (`loremaster.extension.ToolSpec`) is a plain pydantic model
(`extra="forbid"`) so seam 3 is testable without any FastMCP machinery:

```python
class ToolSpec(BaseModel):
    name: str
    handler: Callable[..., Any]
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
```

The server build (`LoreServer.register_extension` /
`_register_extension_tools`, `loremaster/server.py`) derives the
FastMCP tool's `inputSchema` from the **handler's own signature** (types,
optionality, `list`/`dict` shapes), not from `input_schema`, which is
supplemental description only. Two registration-time guards apply to every
extension tool:

- The tool name must not collide with one of the twelve built-in tool names
  (all under the `lore_` prefix) — registration raises if it does.
- The handler must not declare a `context` parameter — that name is reserved
  for FastMCP's own injected `Context`; registration raises naming the
  offending `ToolSpec` if it does.

A handler closes over an `ExtensionContext` built specifically for its own
extension (`LoreServer._child_context`): every shared service is the same
object as the parent context, but `state` is swapped for a **private,
per-extension namespace** — one extension's `on_startup` cannot leak state
into a sibling's tool handler, and vice versa.

## §3 — `FieldIndexSpec` (seam 8, P6 close-out rename)

Renamed this cycle from the Qdrant-specific spec/kind pair this seam used to
hand back (both old names are now fully removed — no half-rename) to the
backend-neutral `FieldIndexSpec`:

```python
FieldIndexKind = Literal["keyword", "bool", "fulltext"]

class FieldIndexSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field_name: str
    kind: FieldIndexKind
```

An extension's `payload_indexes()` declares fields beyond the base's
`tier`/`file_path`/`content_hash`/`chunk_type` indexes. All three kinds:

| kind        | intent                                            | current wiring |
|-------------|----------------------------------------------------|----------------|
| `keyword`   | exact-match string field (e.g. `model_name`)       | consumed today by the legacy `QdrantStore` construction in `build_app_context` (`extra_keyword_indexes`) |
| `bool`      | boolean flag field (e.g. `is_installed`)           | consumed today by the same legacy `QdrantStore` construction (`extra_bool_indexes`) |
| `fulltext`  | a BM25-indexable text field (e.g. an `llm_summary` enrichment column) | **declared, not yet consumed** — the unified store's schema already fulltext-indexes a fixed set of columns (`ident_text`, `source_text`, `llm_summary` — `loremaster/store/surreal_schema.py::CHUNK_FULLTEXT_FIELDS`), but nothing today reads an extension's `fulltext`-kind `FieldIndexSpec` to extend that set dynamically |

Be honest with yourself about that last row before depending on it: declaring
a `fulltext` `FieldIndexSpec` today records intent on `LoreServer.
payload_index_specs`, but the unified SurrealStore does not (yet) act on it.

`LoreServer.payload_index_specs` (a property, not a seam) collects every
registered extension's specs, in registration order:

```python
server = LoreServer(config).register_extension(MyExtension())
specs = server.payload_index_specs  # list[FieldIndexSpec]
```

## §4 — The search-pipeline hooks and `Candidate`

Seams 4/5/6/11 (`augment_candidates`, `rerank`, `format_result`, `chunk_key`,
`classify_detail`) all trade in `loremaster.store.candidate.Candidate` — the
**only** search-result type any of these seams see, never a
`qdrant_client.ScoredPoint` or a raw `surrealdb` row:

```python
CandidateOrigin = Literal["vector", "fulltext", "fused"]

class Candidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str        # the chunk's bare uuid5 point id
    score: float     # RRF fusion score for a fused hit
    payload: dict[str, Any]  # stored chunk fields (tier, file_path, source_text, …)
    origin: CandidateOrigin
```

`extra="forbid"` on `Candidate` is load-bearing: no stray backend attribute
(a leaked `ScoredPoint.version`, a raw `RecordID`) can ride along and couple
a caller back to a concrete storage engine.

`augment_candidates(query, candidates, ctx) -> list[Candidate]` injects extra
candidates; `rerank(candidates, ctx) -> list[Candidate]` adjusts order/score;
both default to identity. `format_result(result, ctx) -> str | None` renders
off `result.key` / `result.payload`; `None` defers to the base's
`[SOURCE:file:line]` citation. `chunk_key(payload, ctx) -> str | None` takes
the chunk's stored payload dict (not a `Candidate`) and returns the versioned
semantic memory-key correction matching keys off; `None` defers to the base's
structural point-id.

`SearchPipeline` (`loremaster/search.py`) is the owner that resolves these
hooks through the registered `LoreServer`:

```python
class SearchPipeline:
    def __init__(
        self, *, store: SurrealStore, embedder: Embedder, server: LoreServer,
        manifest: SurrealManifest, config: LoreConfig,
        extension_context: ExtensionContext, code_graph: SurrealCodeGraph,
        memory_store: MemoryStore | None, reranker: Any | None,
    ) -> None: ...
```

`store` here is always the unified `SurrealStore` — its `hybrid_search`
(HNSW ⊕ BM25 via `search::rrf`) is the read path every search seam sits on
top of.

## §5 — `ExtensionContext.store` — the unified SurrealDB store

`ExtensionContext` (`loremaster/extension.py`) is the shared-services bundle
handed to every context-taking seam:

```python
class ExtensionContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
    store: Any
    embedder: Any
    config: Any
    count_tokens: Callable[[list[str]], list[int]]
    manifest: Any
    state: dict[str, Any] = Field(default_factory=dict)
```

`count_tokens` here is the embedder's **batch** counter (`list[str] ->
list[int]`) — distinct from the **single-string** `count_tokens` on
`lorescribe`'s `ChunkContext` (`str -> int`), which a `Chunker`'s `ctx` carries
instead. Don't confuse the two contexts if you're writing both a chunker (seam
1) and a context-taking seam.

As of this cycle's **`ctx.store` flip**, the *runtime* `ExtensionContext` an
extension's hooks receive carries the SAME unified `SurrealStore` object the
search pipeline reads (`AppContext.write_store`) — never the legacy
`QdrantStore` (`AppContext.store`). Concretely, `ctx.store` exposes
`hybrid_search(...)` and `scroll(filters, limit)` (§4, §above); the legacy
`QdrantStore`'s `search()`/`scroll()` API is a different shape and is not
what a hook sees.

**Do not treat `ctx.store`'s internals as stable across P7.** Memory is still
served through a *separate* Qdrant-backed `MemoryStore` handle — not reachable
through `ctx.store` — and moves onto the unified store in a future P7 cycle.
Whatever changes then is explicitly **not** covered by this document today.

### Runtime vs. composition `ExtensionContext`

Two distinct construction paths produce an `ExtensionContext`, and they are
**not interchangeable**:

- **Composition-time** — `LoreServer.extension_context(*, store: Any) ->
  ExtensionContext`. Built during server composition (e.g. metadata
  collection, `server.tool_specs(...)` at registration time) with `embedder`
  and `manifest` as placeholders (`None`) and a tokenizer that refuses to
  count (`NotImplementedError`). It exists to let composition-only code
  (deriving tool schemas, etc.) run without live services.
- **Runtime** — built once, in `build_app_context`, over the real embedder,
  the real (Surreal-backed) manifest, and the embedder's working
  `count_tokens`; carries the unified `SurrealStore` per §above. Exposed as
  `AppContext.extension_ctx` (a property, `None` until the lifespan's startup
  hooks have run — the tool-invocation path guards against calling it early).
  The search pipeline and every extension tool handler resolve against
  **this** object, not the composition placeholder — so a tool's `ctx.state`
  sees whatever an `on_startup` hook stashed there.

A hook or handler that receives the composition-time context and expects a
functional `embedder`/`manifest` will fail; always confirm which path handed
you the context you're holding.

## §6 — The `extensions:` config namespace + `config_model()`

`lore.yaml` is strict (`extra="forbid"`) for every *known* section — a typo'd
or stale key fails at load time. The **single sanctioned escape hatch** is the
`extensions:` block:

```yaml
# lore.yaml
extensions:
  odoo:                 # keyed by the extension's `name`
    image: "registry.example.com/ppt-apps15:latest"
    installed_modules: ["sale", "purchase", "stock"]
```

The base treats `extensions:` as an **opaque pass-through** — it neither
interprets nor rejects its contents (it *cannot* know every extension's
schema). A typo *inside* a known section still fails; a typo in an extension's
*own* slice is the extension's job to catch, via `config_model()`:

- On `register_extension`, the server calls `ext.config_model()`
  (`LoreServer._validate_extension_config`). If it returns a model, the server
  validates the `extensions[<name>]` slice (absent ⇒ `{}`) with
  `model.model_validate(...)` — **first**, before any registry mutation. A bad
  key or a missing required field raises `pydantic.ValidationError` **at
  registration** (fail loud), not as an opaque failure later.
- The validated instance is retrievable via `server.extension_config(name)`
  (raises `KeyError` if the extension declared no model or isn't registered).

```python
from pydantic import BaseModel, ConfigDict

class OdooConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")   # typo in the slice fails loud
    image: str
    installed_modules: list[str] = []

class OdooExtension(Extension):
    @property
    def name(self) -> str:
        return "odoo"
    def config_model(self) -> type[BaseModel] | None:
        return OdooConfig
```

## §7 — Source providers — the static-tier acquisition layer (seam 10)

A **static tier** (vendored community / enterprise / pip trees, or an Odoo
image's extracted source) is batch-indexed, **frozen, and version-stamped** —
distinct from a **live** tier (a watched host checkout). A `SourceProvider` is
the seam-10 object that **materialises a static tier's files into the
snapshot layout** so the server can serve them.

```python
from pathlib import Path
from typing import Protocol, runtime_checkable

@runtime_checkable
class SourceProvider(Protocol):
    tier: str                                            # the tier identity it acquires

    def acquire(self, tier: str, snapshot_root: Path) -> None:
        """Materialise `tier`'s files into the snapshot layout under snapshot_root."""
```

A provider **materialises files** (it does *not* stream bytes): the pipeline
later walks and `read_text`s real files. `runtime_checkable` makes a
structural conformance check (`isinstance(obj, SourceProvider)`) meaningful —
an object missing `acquire` is rejected.

`SnapshotLayout` (`loremaster/source/snapshot.py`) is the **single source of
truth** for where a tier's files live, in both directions:

- **Forward:** `tier_locations(tier)` returns an **ordered list** of physical
  directories under the snapshot root. The mapping is many-to-one in reality —
  the built-in `TIER_SUBDIRS` maps `pip` to `("pip-packages",
  "apt-packages")` (the apt+pip→`pip` merge), and known tiers
  `custom`/`community`/`enterprise`/`thirdparty`/`stdlib` to a single
  same-named subdir. **An unknown tier falls back to a single
  `<snapshot_root>/<tier>` subdir**, so a generic project's arbitrary tier
  name works with no registration.
- **`materialization_dir(tier)`** is the **first/canonical** location —
  *where a provider writes*.
- **Reverse:** `resolve(tier, rel_path)` tries the tier's locations **in
  order** and returns the first that *contains* the file as a **safe
  absolute path**, or `None` (the clean not-found / rejected sentinel — no
  exception-as-control-flow).

The reverse lookup applies a **two-tier containment check** so the
file-serving boundary stays safe even when a tier base is itself a directory
symlink: input sanitisation (reject absolute paths and `..` components), then
a lexical `normpath`-containment against the *normalised* base, then a
`resolve()`-check of the *full* candidate (following every link) against the
*resolved* base — catching escapes via a symlinked intermediate *or* final
component (CWE-59 / CWE-22).

The built-in `LocalDirectorySourceProvider` acquires a static tier from a
plain **local directory** — no podman, no containers:

```python
from pathlib import Path
from loremaster.source.local_directory import LocalDirectorySourceProvider

provider = LocalDirectorySourceProvider(tier="thirdparty", source=Path("/vendor/oca"))
```

Its `acquire`:

- **COPIES** the source tree into the tier's `materialization_dir` (a genuine
  point-in-time snapshot the server can bind-mount `:ro`, independent of the
  source's later mutation), via `shutil.copytree(..., dirs_exist_ok=True,
  symlinks=True)`. It is **idempotent** — re-acquiring overwrites the tier's
  subtree with the current source (the per-version-bump rebuild).
- Uses `symlinks=True` to **preserve** symlinks rather than follow them:
  following a link would content-bake its *target* (e.g. a vendored `evil ->
  /etc/passwd`) into the snapshot as a regular file the read-time resolver
  could never detect. Preserved, an escaping link is rejected by the resolver
  at read time, while internal-staying links resolve normally.
- Raises **`FileNotFoundError`** if `source` does not exist — a misconfigured
  static tier fails loud, naming the missing source, rather than producing an
  empty snapshot.

The matching `lore.yaml` `roots:` entry (a static root declares `source` +
`version` + `provider`):

```yaml
roots:
  - tier: thirdparty
    watch: static
    source: /vendor/oca
    version: "2024.1"        # a change triggers a rebuild
    provider: local_directory
```

## §8 — The register guard (seam 1)

When you contribute chunkers via seam 1, `register_extension` enforces a
guard (`LoreServer._register_extension_chunker`): **a chunker may not shadow
an existing suffix-owner** in the registry's predicate tier. The base
suffixes are seeded first (so an extension can't claim `.py`, `.xml`, etc.),
and each registered chunker's suffixes are recorded. The guard refuses, with a
`ValueError`, **two** forms of shadowing:

1. **Declared overlap.** A chunker's `default_suffixes` entry is already
   owned by a registered chunker. (`getattr(chunker, "default_suffixes",
   ())` — omit the attribute and you declare none.)
2. **Greedy predicate.** A chunker that declares no (or a different) suffix
   but whose `handles()` accepts an owned suffix's files anyway. The guard
   catches this by **probing every owned suffix** with a synthetic sentinel
   path (`/__lore_suffix_probe__/sentinel<suffix>`); if `handles` returns
   `True`, the chunker is greedy and is refused.

A chunker claiming **only fresh suffixes**, or a **basename/pattern** chunker
whose `handles` returns `False` for those probes (the seam-1 use case — e.g. a
`Makefile` claimant), registers cleanly and is reached via the predicate tier.
`handles()` is arbitrary code; the probe catches the realistic greedy forms,
not a pathologically path-specific predicate.

The remedy the error messages point at: **use a config override** to
re-route an extension to a different chunker, or a **basename predicate** for
a filename-keyed chunker. On a clean registration the chunker's registry key
is namespaced as `f"{ext.name}:{type(chunker).__name__}"`, so two extensions'
chunkers never collide on a logical key.

## Seam 9 — lifespan and per-extension state

`on_startup(ctx)` / `on_shutdown(ctx)` run over a **child context**
(`LoreServer._child_context`) whose `state` is that extension's own private
namespace (keyed by `ext.name`), reachable later via
`LoreServer.extension_state(ctx, name)`. A `state` write in `on_startup` is
visible to that same extension's tool handlers and to its own `on_shutdown` —
never to a sibling extension's context.

`run_startup_hooks` unwinds on partial failure (fix A): if one extension's
`on_startup` raises, every already-started extension's `on_shutdown` runs
before the exception propagates, so a failing hook never leaks a live
resource another extension acquired.

## Worked sketch: an `odoo-code` extension (DEFERRED)

> **This is an illustrative SKETCH, not code to ship.** It shows how a future
> `odoo-code` MCP *would* plug into loremaster as a thin extension. It is
> deferred and unbuilt. The method bodies are sketches; only the seam
> **signatures** are real (verified against this cycle's `FieldIndexSpec` /
> `Candidate` types). A real implementation would be developed test-first.

The point of the sketch: **everything Odoo-specific lives in the extension;
the generic core never imports anything Odoo.** A bare loremaster server is a
generic RAG; registering `OdooExtension()` turns it into the Odoo code
server.

```python
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from loremaster.extension import (
    Extension, ExtensionContext, FieldIndexSpec, ToolSpec,
)
from loremaster.store.candidate import Candidate
from lorescribe.base import Chunker


# --- config slice (seam 7) ------------------------------------------------
class OdooConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")     # typo in the slice fails loud
    image: str                                     # the podman image to extract source from
    installed_modules: list[str] = []


class OdooExtension(Extension):
    """Sketch: the deferred odoo-code MCP as a loremaster extension."""

    # Seam 6 stamps this version into the semantic memory-key (vs odoo-code's
    # old UNVERSIONED build_chunk_key — the orphan hazard a version closes).
    key_version = 3

    @property
    def name(self) -> str:                         # also the `extensions:` config key
        return "odoo"

    # Seam 1 — Odoo-specific chunkers (manifest + CSV) the generic core lacks.
    def chunkers(self) -> list[Chunker]:
        return [OdooManifestChunker(), OdooCsvChunker()]   # __manifest__.py, ir.model.access.csv

    # Seam 2 — an Odoo XML SchemaProfile that claims <record>/<menuitem>/<template>
    # and forces each into its own chunk (force_own_chunk) even in a small file.
    def xml_profiles(self) -> list[Any]:
        return [OdooRecordProfile()]

    # Seam 3 — index-backed structured tools beyond semantic search.
    def tools(self, ctx: ExtensionContext) -> list[ToolSpec]:
        def _list_modules(installed_only: bool = True) -> list[str]:
            # closes over ctx.store to query the index by the is_installed payload
            ...
        return [
            ToolSpec(
                name="list_modules",
                handler=_list_modules,
                description="List indexed Odoo modules.",
                input_schema={"installed_only": "bool"},
                output_schema={"modules": "list[str]"},
            )
        ]

    # Seam 4 (C3) — bias retrieval toward INSTALLED modules.
    def rerank(
        self, candidates: list[Candidate], ctx: ExtensionContext
    ) -> list[Candidate]:
        # boost candidates whose payload says is_installed; stable within a tier
        return sorted(
            candidates,
            key=lambda c: (bool(c.payload.get("is_installed")), c.score),
            reverse=True,
        )

    # Seam 5 — the richer Odoo citation.
    def format_result(self, result: Candidate, ctx: ExtensionContext) -> str | None:
        module = result.payload.get("module", "?")
        file_path = result.payload.get("file_path", "?")
        line = result.payload.get("line_start", "?")
        return f"[SOURCE:{module}/{file_path}:{line}]"

    # Seam 6 — versioned semantic key folding in key_version (migratable, not orphaned).
    def chunk_key(self, payload: dict[str, Any], ctx: ExtensionContext) -> str | None:
        return f"odoo:{payload.get('model_name', '?')}:v{self.key_version}"

    # Seam 7 — fail-loud validation of the extensions.odoo slice.
    def config_model(self) -> type[BaseModel] | None:
        return OdooConfig

    # Seam 8 — the Odoo facet fields the base doesn't index.
    def payload_indexes(self) -> list[FieldIndexSpec]:
        return [
            FieldIndexSpec(field_name="model_name", kind="keyword"),
            FieldIndexSpec(field_name="is_installed", kind="bool"),
        ]

    # Seam 10 — extract a frozen static tier OUT OF a podman image.
    def source_providers(self) -> list[Any]:
        cfg: OdooConfig = ...   # ctx-less here; the validated slice is on the server
        return [PodmanImageSourceProvider(tier="community", image=cfg.image)]

    # Seam 11 (C2) — classify Odoo chunk types the base can't.
    def classify_detail(self, chunk_type: str) -> Literal["summary", "source"] | None:
        if chunk_type in {"odoo_record_summary", "view_arch"}:
            return "summary"
        if chunk_type in {"odoo_method", "odoo_record"}:
            return "source"
        return None   # defer to the base
```

A `PodmanImageSourceProvider` would conform to the `SourceProvider` Protocol
(§7) — a `tier` attribute and `acquire(tier, snapshot_root)` extracting the
image's source into `SnapshotLayout(snapshot_root).materialization_dir(tier)`
— the image-backed analogue of the built-in `LocalDirectorySourceProvider`.

Composition is unchanged from any other extension:

```python
LoreServer.from_config("lore.yaml").register_extension(OdooExtension()).run()
```

### What stays a SEPARATE concern

The **live-Odoo RPC** path (querying a running Odoo instance for actual
record values, `fields_get`, etc.) is **NOT a loremaster extension**.
loremaster indexes and serves *source code and docs* from frozen tiers and
watched checkouts; "what does the system DO right now" is a different
runtime concern with its own tooling. The extension above provides the *code
search* surface; live RPC is orthogonal and out of scope for the extension
framework. Keep them distinct.
