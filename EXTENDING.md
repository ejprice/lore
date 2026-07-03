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

## The eleven seams

`Extension` is an ABC (`loremaster/extension.py`) with a required `name`
property and eleven seams, each shipping a safe, inert default (`[]` / `None`
/ identity / async no-op) so a server with zero extensions registered behaves
as the generic code/docs RAG:

1. `chunkers() -> list[Chunker]` — contribute `lorescribe.base.Chunker`s.
2. `xml_profiles() -> list[Any]` / `js_profiles() -> list[Any]` — contribute
   XML `SchemaProfile`s / `JsProfile`s.
3. `tools(ctx: ExtensionContext) -> list[ToolSpec]` — declarative, index-backed
   tools (§2).
4. `augment_candidates(query, candidates, ctx)` /
   `rerank(candidates, ctx)` — the search-pipeline hook (§4).
5. `format_result(result, ctx) -> str | None` — a custom citation/format;
   `None` falls through to the base's `[SOURCE:file:line]` format.
6. `chunk_key(payload, ctx) -> str | None` — the versioned semantic
   memory-key for correction matching; `None` falls through to the base's
   structural point-id.
7. `config_model() -> type[BaseModel] | None` — validates the extension's
   `extensions[name]` config slice; `None` means no extra config.
8. `payload_indexes() -> list[FieldIndexSpec]` — extra field indexes to
   declare (§3).
9. `on_startup(ctx)` / `on_shutdown(ctx)` — async lifespan hooks.
10. `source_providers() -> list[Any]` — indexer-side acquisition providers
    (`SourceProvider` Protocol).
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

Renamed this cycle from the Qdrant-specific `PayloadIndexSpec` /
`PayloadIndexKind` (both names are now fully removed — no half-rename) to the
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
  count. It exists to let composition-only code (deriving tool schemas, etc.)
  run without live services.
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
