# Extending loremaster — the Extension framework

`loremaster` is the orchestration layer. **Out of the box, with zero extensions
registered, it is a generic code/docs RAG**: it indexes Python / Markdown / SQL /
XML / JavaScript / CSS / text with the default `lorescribe` chunkers, derives
deterministic point-IDs, and serves a base `[SOURCE:file:line]` citation. A
*domain* MCP (e.g. a future `odoo-code`) is built by **subclassing one ABC** and
**registering it on the server** — it never forks the core.

This document is the contract for that subclass. It covers:

- [The composition model](#the-composition-model) — `from_config` → `register_extension` → `run`.
- [The `Extension` ABC and its eleven seams](#the-extension-abc--the-eleven-seams) — signature, inert default, and when to override each.
- [`ExtensionContext`](#extensioncontext--the-shared-services-bundle) — the shared services every context-taking seam receives.
- [The `extensions:` config namespace + `config_model()`](#the-extensions-config-namespace--config_model).
- [`SourceProvider` + `LocalDirectorySourceProvider`](#source-providers--the-static-tier-acquisition-layer) — static-tier acquisition and the snapshot/tier↔location contract.
- [The register guard](#the-register-guard-nit-1) — why a chunker may not shadow a suffix-owner.
- [A worked Odoo-extension *sketch*](#worked-sketch-an-odoo-code-extension-deferred) — the documented target, deferred.

For the *lower* layer — writing the `Chunker` / `SchemaProfile` / `JsProfile`
the seams contribute — see `lorescribe/EXTENDING.md`.

> **Source of truth.** Every signature, default, and constant below is taken
> verbatim from `loremaster/loremaster/{extension,server,config}.py` and
> `loremaster/loremaster/source/{snapshot,local_directory}.py`. The code wins
> over this document.
>
> **Scope note.** `extension.py`/`server.py` are the *composition contract* **and the
> live server**. `LoreServer.run()` configures lore-namespace structured logging
> (`LoggingConfig` / `LORE_LOG_LEVEL`), registers the twelve MCP tools, runs the embedder
> probe-gate, builds the ASGI app (Bearer-key auth enforced when `auth` is enabled,
> else localhost no-auth), and serves the FastMCP streamable-http app via uvicorn.
> The heavy startup (probe-gate → initial reconcile → watcher) and the extension
> lifespan hooks run **once per process**, shared across concurrent MCP sessions
> (a reference-counted process guard — FastMCP enters the lifespan once per session).

---

## The composition model

```python
from loremaster.server import LoreServer

(
    LoreServer.from_config("lore.yaml")    # load + validate config → bare generic RAG
    .register_extension(MyExtension())     # compose a domain extension (chainable)
    .run()                                 # configure logging + serve (FastMCP streamable-http via uvicorn)
)
```

- **`LoreServer.from_config(path)`** loads and validates `lore.yaml` and stands up
  a **bare** server. A bare server is the generic RAG: its `registry` is the
  default `lorescribe` registry (`python_ast`, `markdown`, `sql`, `stylesheet`,
  `text`, plus profile-driven `xml` / `javascript`), its citation format is the
  base default, and **no extension hook fires**.
- **`register_extension(ext)`** composes an extension and **returns `self`** for
  chaining, so you can register **zero or more**. The order inside is deliberate:
  the config slice is validated **first** (fail loud before mutating any registry
  state), then chunkers are registered under the [register guard](#the-register-guard-nit-1),
  then profiles + the remaining seams are collected.
- **`run()`** configures structured logging, registers the twelve MCP tools, runs the
  embedder probe-gate, builds the ASGI app (Bearer auth when `auth` is enabled), and
  serves the FastMCP streamable-http app via uvicorn. Its heavy startup (probe-gate /
  initial reconcile / watcher) and the extension lifespan hooks (`on_startup` /
  `on_shutdown`, seam 9) run **once per process**, shared across concurrent MCP
  sessions, via a reference-counted process guard.

The wired surface a bare-or-extended server exposes (consumed by the later
indexer / search / server layers):

| Accessor / method | What it yields |
|---|---|
| `server.registry` | the composed `ChunkerRegistry` (default + extension chunkers/profiles) |
| `server.payload_index_specs` | extension-declared extra payload indexes (seam 8) |
| `server.source_providers` | extension-contributed source providers (seam 10) |
| `server.tool_specs(ctx)` | every extension's declarative `ToolSpec`s (seam 3) |
| `server.format_result(result, ctx)` | resolved citation/format, first non-`None` wins (seam 5) |
| `server.chunk_key(payload, ctx)` | resolved semantic memory-key, first non-`None` wins (seam 6) |
| `server.classify_detail(chunk_type)` | resolved detail level (seam 11), falling back to base |
| `server.augment_candidates(query, candidates, ctx)` | each extension's augmentation, chained (seam 4) |
| `server.rerank(candidates, ctx)` | each extension's rerank, chained (seam 4) |
| `await server.run_startup_hooks(ctx)` / `run_shutdown_hooks(ctx)` | lifespan (seam 9; shutdown runs in **reverse** order) |
| `server.extension_config(name)` | the validated per-extension config slice (seam 7) |

---

## `ExtensionContext` — the shared-services bundle

Every **context-taking** seam receives a single `ExtensionContext`. Carrying a
bundle (rather than wiring each service into every seam) keeps seam signatures
stable as the service set grows.

```python
from loremaster.extension import ExtensionContext

class ExtensionContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
    # NOT frozen — `state` must stay mutable for seam 9.

    store: Any                                       # the QdrantStore (or a test stand-in)
    embedder: Any                                    # the active loresigil Embedder
    config: Any                                      # the validated LoreConfig
    count_tokens: Callable[[list[str]], list[int]]   # the embedder's BATCH token counter
    manifest: Any                                    # the Manifest ledger
    state: dict[str, Any] = Field(default_factory=dict)  # mutable scratch a lifespan hook may stash on
```

Notes that bite if missed:

- `count_tokens` here is the **batch** counter (`list[str] -> list[int]`) — distinct
  from the **single-string** `ctx.count_tokens` on `lorescribe`'s `ChunkContext`
  (`str -> int`). Don't confuse the two contexts.
- `store` / `embedder` / `config` / `manifest` are typed `Any` so this
  composition layer never imports the runtime resources; tests pass lightweight
  fakes, the server build passes the real ones.
- `state` is a fresh dict per context; an `on_startup` hook may cache a derived
  value on it for later handlers. It is the *only* mutable field.

---

## The `Extension` ABC + the eleven seams

```python
from loremaster.extension import Extension

class Extension(ABC):
    key_version: int = 1   # DEFAULT_KEY_VERSION — folded into the seam-6 semantic key

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable name; also this extension's key in the `extensions:` config."""
```

`Extension` is a genuine **ABC** (not a bare Protocol — a unit-testable value, not
entry-point discovery). `name` is the **only** abstract member: a subclass that
does not implement it cannot be instantiated, so an unnamed extension can never
be registered. **Every other seam ships a safe, inert default** (`[]` / `None` /
identity / async no-op), so a subclass overrides **only what it needs**, and a
server with zero extensions is the generic RAG.

The seams, grouped by concern. Each is listed with its **exact signature**, its
**inert default**, and **when to override**.

### Group A — chunkers & profiles (ingestion)

These feed the `lorescribe` layer. See `lorescribe/EXTENDING.md` for how to write
the contributed objects.

#### Seam 1 — `chunkers()`

```python
def chunkers(self) -> list[Chunker]:
    return []   # default: none
```

Contribute `lorescribe.base.Chunker` instances (new file types). Each is
registered under the register guard. A chunker may expose an optional
`default_suffixes` class attribute (a tuple of extensions it claims); omitting it
means the chunker is basename/predicate-keyed (reached via the registry's
predicate tier). **Override when** your domain has file types the generic
chunkers don't cover (an Odoo `__manifest__.py`, a CSV access-rights file).

#### Seam 2 — `xml_profiles()` / `js_profiles()`

```python
def xml_profiles(self) -> list[Any]:   # SchemaProfile callables
    return []
def js_profiles(self) -> list[Any]:    # JsProfile callables
    return []
```

Contribute `SchemaProfile` / `JsProfile` callables. On registration the
`LoreServer` **accumulates** them and **rebuilds** the constructed `xml` / `js`
chunkers with the full accumulated set — re-registering the key keeps its registry
slot. **Override when** you want the generic XML/JS chunker to retag, skip, or
(XML) force standalone granularity for domain-significant elements/blocks
(Odoo `<record>` / `<menuitem>` / `<template>`).

### Group B — index-backed tools

#### Seam 3 — `tools(ctx)`

```python
def tools(self, ctx: ExtensionContext) -> list[ToolSpec]:
    return []   # default: none
```

Returns **declarative** `ToolSpec`s; the later FastMCP build registers them
(keeping the spec FastMCP-free makes seam 3 testable now). `ToolSpec`:

```python
class ToolSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")
    name: str
    handler: Callable[..., Any]      # a plain callable (closes over ctx in the server build)
    description: str
    input_schema: dict[str, Any]     # a small descriptive mapping, NOT a JSON Schema dialect
    output_schema: dict[str, Any]
```

**Override when** your domain has structured lookups the index can answer beyond
semantic search (`list_modules`, `find_field`).

### Group C — the search pipeline (C3)

#### Seam 4 — `augment_candidates(...)` / `rerank(...)`

```python
def augment_candidates(
    self, query: str, candidates: list[ScoredPoint], ctx: ExtensionContext
) -> list[ScoredPoint]:
    return candidates   # default: identity

def rerank(
    self, candidates: list[ScoredPoint], ctx: ExtensionContext
) -> list[ScoredPoint]:
    return candidates   # default: identity
```

`candidates` are `qdrant_client.models.ScoredPoint`s. `augment_candidates` may
**inject extra candidates** (each extension's output feeds the next); `rerank`
**adjusts order/score**. With no extensions both are the identity. **Override
when** your domain wants to bias retrieval — inject installed-module candidates, or
boost results from an installed module's source.

### Group D — citation / format

#### Seam 5 — `format_result(result, ctx)`

```python
def format_result(self, result: ScoredPoint, ctx: ExtensionContext) -> str | None:
    return None   # default: base supplies its `[SOURCE:file:line]` citation
```

The server resolves this **first non-`None` wins** across registered extensions;
`None` ⇒ base default citation. **Override when** your domain has a richer
citation (`[SOURCE:module/file:line]`).

### Group E — versioned semantic chunk_key (C... seam 6)

#### Seam 6 — `chunk_key(payload, ctx)`

```python
def chunk_key(self, payload: dict[str, Any], ctx: ExtensionContext) -> str | None:
    return None   # default: base uses its structural point-ID
```

This is the **semantic** key a correction / targeted-injection is matched on —
distinct from the base's **structural** point-ID. (The structural point-ID, in
`index/records.py`, is a UUID5 over
`"{slug}:{tier}:{file_path}:{chunk_type}:{identity}:{sub_ordinal}:{key_version}"`
with its own `KEY_VERSION = 2`; that derivation is *not* this seam.) An overriding
extension should **fold `self.key_version` into the key** so a keying-scheme
change is detectable and migratable — closing the orphan hazard that an
*unversioned* key (odoo-code's old `build_chunk_key`) left open. First non-`None`
wins. **Override when** your domain matches corrections semantically (by
`model_name`, by qualified symbol) rather than by exact point-ID.

```python
key_version = 3   # bump when you change the keying scheme

def chunk_key(self, payload, ctx):
    return f"odoo:{payload.get('model_name', '?')}:v{self.key_version}"
```

### Group F — config namespace (seam 7)

#### Seam 7 — `config_model()`

```python
def config_model(self) -> type[BaseModel] | None:
    return None   # default: extension declares no extra config
```

Returns a pydantic model that **validates this extension's `extensions[name]`
config slice** at registration. `None` ⇒ no extra config. See
[the config namespace](#the-extensions-config-namespace--config_model) below.
**Override when** your domain needs operator-supplied config (an Odoo image
reference, a list of installed modules).

### Group G — payload indexes (seam 8)

#### Seam 8 — `payload_indexes()`

```python
def payload_indexes(self) -> list[PayloadIndexSpec]:
    return []   # default: none
```

```python
class PayloadIndexSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field_name: str
    schema_type: Literal["keyword", "bool"]   # an unknown kind raises at construction
```

Declare extra payload indexes beyond the base
`tier`/`file_path`/`content_hash`/`chunk_type` set. `schema_type` is **constrained**
to `"keyword"` (exact-match strings, e.g. `model_name`) or `"bool"` (flags, e.g.
`is_installed`) — an unknown kind fails loud as a `ValidationError`. **Override
when** your domain filters/facets on fields the base doesn't index.

### Group H — lifespan (seam 9)

#### Seam 9 — `on_startup(ctx)` / `on_shutdown(ctx)`

```python
async def on_startup(self, ctx: ExtensionContext) -> None:
    return None   # default: async no-op
async def on_shutdown(self, ctx: ExtensionContext) -> None:
    return None   # default: async no-op
```

Async lifespan hooks. `on_startup` runs after core resources are up (it may stash
state on `ctx.state`); the server awaits each extension's `on_startup` in
**registration order** and each `on_shutdown` in **reverse** order (last-started,
first-stopped). **Override when** your domain holds a resource needing setup/teardown
(an RPC client pool, a cache warmed from the manifest).

### Group I — source providers (seam 10)

#### Seam 10 — `source_providers()`

```python
def source_providers(self) -> list[Any]:   # SourceProvider conformers
    return []   # default: none
```

Contribute indexer-side `SourceProvider`s that acquire a **static tier** into the
snapshot layout. See [the source-provider section](#source-providers--the-static-tier-acquisition-layer).
**Override when** your domain's static source needs custom acquisition (extracting
files out of a podman image) rather than the built-in local-directory copy.

### Group J — detail classification (C2, seam 11)

#### Seam 11 — `classify_detail(chunk_type)`

```python
def classify_detail(self, chunk_type: str) -> Literal["summary", "source"] | None:
    return None   # default: defer to the base's classification of ITS OWN types
```

Classifies a chunk type into the coarse `"summary"` tier vs the full `"source"`
tier. `None` ⇒ defer to the next classifier / the base. The base default
(`_base_classify_detail`) maps `{"imports", "class", "markdown_section",
"xml_element"}` ⇒ `"summary"` and **everything else** ⇒ `"source"`. The server
consults each extension first, then falls back to the base. **Override when** your
domain emits chunk types the base can't classify (an Odoo `view_arch` summary vs a
`method` body).

---

## The `extensions:` config namespace + `config_model()`

`lore.yaml` is strict (`extra="forbid"`) for every *known* section — a typo'd or
stale key fails at load time. The **single sanctioned escape hatch** is the
`extensions:` block:

```yaml
# lore.yaml
extensions:
  odoo:                 # keyed by the extension's `name`
    image: "registry.example.com/ppt-apps15:latest"
    installed_modules: ["sale", "purchase", "stock"]
```

The base treats `extensions:` as an **opaque pass-through** — it neither
interprets nor rejects its contents (it *cannot* know every extension's schema). A
typo *inside* a known section still fails; a typo in an extension's *own* slice is
the extension's job to catch, via `config_model()`:

- On `register_extension`, the server calls `ext.config_model()`. If it returns a
  model, the server validates the `extensions[<name>]` slice (absent ⇒ `{}`) with
  `model.model_validate(...)` — **first**, before any registry mutation. A bad key
  or a missing required field raises `pydantic.ValidationError` **at
  registration** (fail loud), not as an opaque failure later.
- The validated instance is retrievable via `server.extension_config(name)`
  (raises `KeyError` if the extension declared no model).

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

---

## Source providers — the static-tier acquisition layer

A **static tier** (vendored community / enterprise / pip trees, or an Odoo image's
extracted source) is batch-indexed, **frozen, and version-stamped** — distinct
from a **live** tier (a watched host checkout). A `SourceProvider` is the seam-10
object that **materialises a static tier's files into the snapshot layout** so the
server can serve them.

### The `SourceProvider` protocol

```python
from pathlib import Path
from typing import Protocol, runtime_checkable

@runtime_checkable
class SourceProvider(Protocol):
    tier: str                                            # the tier identity it acquires

    def acquire(self, tier: str, snapshot_root: Path) -> None:
        """Materialise `tier`'s files into the snapshot layout under snapshot_root."""
```

A provider **materialises files** (it does *not* stream bytes): the pipeline later
walks and `read_text`s real files. `runtime_checkable` makes a structural
conformance check (`isinstance(obj, SourceProvider)`) meaningful — an object
missing `acquire` is rejected.

### The snapshot / tier↔location contract

`SnapshotLayout` (in `source/snapshot.py`) is the **single source of truth** for
where a tier's files live, in both directions:

- **Forward:** `tier_locations(tier)` returns an **ordered list** of physical
  directories under the snapshot root. The mapping is many-to-one in reality — the
  built-in `TIER_SUBDIRS` maps `pip` to `("pip-packages", "apt-packages")` (the
  apt+pip→`pip` merge), and known tiers `custom`/`community`/`enterprise`/
  `thirdparty`/`stdlib` to a single same-named subdir. **An unknown tier falls
  back to a single `<snapshot_root>/<tier>` subdir**, so a generic project's
  arbitrary tier name works with no registration.
- **`materialization_dir(tier)`** is the **first/canonical** location — *where a
  provider writes*.
- **Reverse:** `resolve(tier, rel_path)` tries the tier's locations **in order**
  and returns the first that *contains* the file as a **safe absolute path**, or
  `None` (the clean not-found / rejected sentinel — no exception-as-control-flow).

The reverse lookup applies a **two-tier containment check** (C4) so the
file-serving boundary stays safe even when a tier base is itself a directory
symlink: input sanitisation (reject absolute paths and `..` components), then a
lexical `normpath`-containment against the *normalised* base, then a
`resolve()`-check of the *full* candidate (following every link) against the
*resolved* base — catching escapes via a symlinked intermediate *or* final
component (CWE-59 / CWE-22).

### The built-in `LocalDirectorySourceProvider`

```python
from pathlib import Path
from loremaster.source.local_directory import LocalDirectorySourceProvider

provider = LocalDirectorySourceProvider(tier="thirdparty", source=Path("/vendor/oca"))
```

It acquires a static tier from a plain **local directory** — no podman, no
containers. `acquire`:

- **COPIES** the source tree into the tier's `materialization_dir` (a genuine
  point-in-time snapshot the server can bind-mount `:ro`, independent of the
  source's later mutation), via `shutil.copytree(..., dirs_exist_ok=True,
  symlinks=True)`. It is **idempotent** — re-acquiring overwrites the tier's
  subtree with the current source (the per-version-bump rebuild).
- Uses `symlinks=True` to **preserve** symlinks rather than follow them: following
  a link would content-bake its *target* (e.g. a vendored `evil -> /etc/passwd`)
  into the snapshot as a regular file the read-time resolver could never detect.
  Preserved, an escaping link is rejected by the resolver at read time, while
  internal-staying links resolve normally.
- Raises **`FileNotFoundError`** if `source` does not exist — a misconfigured static
  tier fails loud, naming the missing source, rather than producing an empty
  snapshot.

The matching `lore.yaml` `roots:` entry (a static root declares
`source` + `version` + `provider`):

```yaml
roots:
  - tier: thirdparty
    watch: static
    source: /vendor/oca
    version: "2024.1"        # a change triggers a rebuild
    provider: local_directory
```

---

## The register guard (nit-1)

When you contribute chunkers via seam 1, `register_extension` enforces a guard:
**a chunker may not shadow an existing suffix-owner** in the registry's predicate
tier. The base suffixes are seeded first (so an extension can't claim `.py`, `.xml`,
etc.), and each registered chunker's suffixes are recorded. The guard refuses, with
a `ValueError`, **two** forms of shadowing:

1. **Declared overlap.** A chunker's `default_suffixes` entry is already owned by a
   registered chunker. (`getattr(chunker, "default_suffixes", ())` — omit the
   attribute and you declare none.)
2. **Greedy predicate.** A chunker that declares no (or a different) suffix but
   whose `handles()` accepts an owned suffix's files anyway. The guard catches this
   by **probing every owned suffix** with a synthetic sentinel path
   (`/__lore_suffix_probe__/sentinel<suffix>`); if `handles` returns `True`, the
   chunker is greedy and is refused.

A chunker claiming **only fresh suffixes**, or a **basename/pattern** chunker whose
`handles` returns `False` for those probes (the seam-1 use case — e.g. a `Makefile`
claimant), registers cleanly and is reached via the predicate tier. `handles()` is
arbitrary code; the probe catches the realistic greedy forms, not a pathologically
path-specific predicate.

The remedy the error messages point at: **use a config override** (`apply_overrides`)
to re-route an extension to a different chunker, or a **basename predicate** for a
filename-keyed chunker. On a clean registration the chunker's registry key is
namespaced as `f"{ext.name}:{type(chunker).__name__}"`, so two extensions' chunkers
never collide on a logical key.

---

## Worked sketch: an `odoo-code` extension (DEFERRED)

> **This is an illustrative SKETCH, not code to ship.** It shows how the future
> `odoo-code` MCP *would* plug into loremaster as a thin extension — the documented
> target. It is deferred and unbuilt. The method bodies are sketches; only the seam
> **signatures** are real. A real implementation would be developed test-first.

The point of the sketch: **everything Odoo-specific lives in the extension; the
generic core never imports anything Odoo.** A bare loremaster server is a generic
RAG; registering `OdooExtension()` turns it into the Odoo code server.

```python
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict
from qdrant_client.models import ScoredPoint

from loremaster.extension import (
    Extension, ExtensionContext, PayloadIndexSpec, ToolSpec,
)
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
        self, candidates: list[ScoredPoint], ctx: ExtensionContext
    ) -> list[ScoredPoint]:
        # boost candidates whose payload says is_installed; stable within a tier
        return sorted(
            candidates,
            key=lambda c: (bool((c.payload or {}).get("is_installed")), c.score),
            reverse=True,
        )

    # Seam 5 — the richer Odoo citation.
    def format_result(self, result: ScoredPoint, ctx: ExtensionContext) -> str | None:
        payload = result.payload or {}
        module = payload.get("module", "?")
        file_path = payload.get("file_path", "?")
        line = payload.get("line_start", "?")
        return f"[SOURCE:{module}/{file_path}:{line}]"

    # Seam 6 — versioned semantic key folding in key_version (migratable, not orphaned).
    def chunk_key(self, payload: dict[str, Any], ctx: ExtensionContext) -> str | None:
        return f"odoo:{payload.get('model_name', '?')}:v{self.key_version}"

    # Seam 7 — fail-loud validation of the extensions.odoo slice.
    def config_model(self) -> type[BaseModel] | None:
        return OdooConfig

    # Seam 8 — the Odoo facet fields the base doesn't index.
    def payload_indexes(self) -> list[PayloadIndexSpec]:
        return [
            PayloadIndexSpec(field_name="model_name", schema_type="keyword"),
            PayloadIndexSpec(field_name="is_installed", schema_type="bool"),
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

A `PodmanImageSourceProvider` would conform to the `SourceProvider` Protocol — a
`tier` attribute and `acquire(tier, snapshot_root)` extracting the image's source
into `SnapshotLayout(snapshot_root).materialization_dir(tier)` — the image-backed
analogue of the built-in `LocalDirectorySourceProvider`.

Composition is unchanged from any other extension:

```python
LoreServer.from_config("lore.yaml").register_extension(OdooExtension()).run()
```

### What stays a SEPARATE concern

The **live-Odoo RPC** path (querying a running Odoo instance for actual record
values, `fields_get`, etc.) is **NOT a loremaster extension**. loremaster indexes
and serves *source code and docs* from frozen tiers and watched checkouts;
"what does the system DO right now" is a different runtime concern with its own
tooling. The extension above provides the *code search* surface; live RPC is
orthogonal and out of scope for the extension framework. Keep them distinct.
