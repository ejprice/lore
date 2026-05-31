# Extending the lorescribe chunker core

`lorescribe` is the **generic, domain-agnostic** chunking layer. It knows about
*file structure* — Python ASTs, Markdown headings, XML elements, JavaScript
declarations — and nothing about any product, framework, or business domain.
This document describes the three extension points the core exposes so a
downstream package can add domain knowledge **without the generic core ever
importing anything domain-specific**:

1. A custom [`Chunker`](#1-writing-a-custom-chunker) — claim and split a new file type.
2. An XML [`SchemaProfile`](#2-xml-schemaprofile) — customise how the generic XML chunker treats particular elements.
3. A JavaScript [`JsProfile`](#3-javascript-jsprofile) — the analogous hook for `.js` source.

Everything here is pure `lorescribe`. The `loremaster` extension framework (the
`Extension` ABC, the `LoreServer` composition) is documented separately in
`loremaster/EXTENDING.md`; it is the thing that *wires* the hooks below into a
running server. This document is the lower layer: the contracts a hook must
satisfy.

> **Source of truth.** Every signature and constant below is taken verbatim from
> `lorescribe/lorescribe/{base,registry,models,xml_generic,javascript}.py`. If
> this document and the code disagree, the code wins — file a docs bug.

---

## The data models everything emits

Both chunkers and profiles ultimately produce / customise
[`Chunk`](lorescribe/models.py) objects. Three models in `lorescribe.models`
matter for extension authors.

### `Chunk` — the atomic embeddable record

```python
from lorescribe.models import Chunk

class Chunk(BaseModel):
    model_config = ConfigDict(extra="forbid")   # a typo'd field name fails loudly

    chunk_type: str            # the chunker's category, e.g. "markdown_section"
    source_text: str           # the raw text split from the document
    identity: str              # within-file natural key (REQUIRED, non-blank)
    sub_ordinal: int = 0       # disambiguates siblings sharing an identity
    line_start: int            # 1-based first line covered
    line_end: int              # 1-based last line covered
    metadata: dict[str, Any] = Field(default_factory=dict)  # arbitrary chunker-attached metadata
    metadata_header: str = ""            # breadcrumb prepended to source_text
```

Load-bearing rules:

- **`identity` must be non-empty and not whitespace-only.** A `field_validator`
  rejects a blank value and stores the surrounding-whitespace-trimmed form, so
  `"  payroll  "` and `"payroll"` derive the *same* downstream point-ID. A blank
  identity would collapse sibling chunks' point-IDs — the model boundary refuses
  it.
- **`(identity, sub_ordinal)` is the within-file natural key.** Downstream,
  `loremaster` combines it with `(slug, tier, file_path, chunk_type, key_version)`
  into a deterministic UUID5 point-ID. Two siblings that legitimately share an
  `identity` (e.g. one heading split into N pieces) MUST carry distinct
  `sub_ordinal`s or one silently overwrites the other.
- **`embedding_text` is computed, not set.** It is the exact string handed to the
  embedder: `f"{metadata_header}\n{source_text}"` when `metadata_header` is
  non-empty, else exactly `source_text` (no leading newline). You control it
  indirectly through `metadata_header` and `source_text`.
- **`extra="forbid"`** — passing an unknown kwarg (a typo'd field name) raises at
  construction rather than silently dropping data.

### `ChunkContext` — per-file context the framework injects

```python
from lorescribe.models import ChunkContext

class ChunkContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    slug: str                            # the project identifier
    file_path: str                       # the on-disk path being chunked
    count_tokens: Callable[[str], int]   # the embedder's injected token counter
    max_input_tokens: int                # the embedder's HARD token cap
```

`count_tokens` is a genuine callable supplied by the embedder side. Your chunker
calls through it to size its output and **must keep every emitted chunk at or
below `max_input_tokens`** — over-length inputs are rejected (HTTP 422), never
silently truncated.

### `ProfileResult` — the return shape of both profile hooks

```python
from lorescribe.models import ProfileResult

class ProfileResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_type: str                       # the category the profile selected
    extra_metadata: dict[str, Any]        # merged OVER the generic metadata block
    skip: bool = False                    # True ⇒ drop the element/block entirely
    force_own_chunk: bool = False         # XML granularity control (see §2)
```

Note `chunk_type` and `extra_metadata` are **required** (no defaults) — a profile
that claims something must say what type it becomes and supply a metadata dict
(use `{}` for none).

---

## 1. Writing a custom `Chunker`

A chunker is anything that satisfies the [`Chunker`](lorescribe/base.py) ABC's
two-method protocol:

```python
from abc import ABC, abstractmethod
from lorescribe.models import Chunk, ChunkContext

class Chunker(ABC):
    @abstractmethod
    def handles(self, path: str) -> bool:
        """Report whether this chunker claims the given file path."""

    @abstractmethod
    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Split a source string into Chunk objects."""
```

`Chunker` is **genuinely abstract**: a subclass missing either method cannot be
instantiated, which stops a half-finished chunker from registering. There is no
concrete logic at this layer — the abstract methods exist solely to enforce the
protocol.

### The `handles(path)` predicate

`handles` answers *"is this chunker responsible for `path`?"* It receives the
on-disk (or relative) path and returns a bool. It is the basis of the registry's
**predicate dispatch tier** (below), and it is what lets a chunker claim a file
**by basename or pattern** — a case no extension→chunker map can express:

```python
def handles(self, path: str) -> bool:
    return path.rsplit("/", 1)[-1] == "Makefile"   # claim by basename
```

A suffix-keyed chunker just tests the extension (the built-in `XmlChunker` does
exactly this):

```python
def handles(self, path: str) -> bool:
    return path.lower().endswith(".xml")
```

### The `chunk(source, ctx)` contract

`chunk` receives the full text and the per-file `ChunkContext`, and returns a
`list[Chunk]`. Each chunk MUST carry a **non-empty `identity`** and a
`sub_ordinal` distinguishing siblings. Use `ctx.count_tokens` /
`ctx.max_input_tokens` to keep every chunk embeddable — split anything over the
cap.

### Registry dispatch & the precedence tiers

The [`ChunkerRegistry`](lorescribe/registry.py) maps a file to its chunker and
dispatches the source. It is a **thin router, not a re-chunker**. You register a
chunker under a logical key with the suffixes it claims:

```python
from lorescribe.registry import ChunkerRegistry

registry = ChunkerRegistry()
registry.register("python", PythonAstChunker(), [".py"])
registry.register("makefile", MakefileChunker(), [])   # basename-keyed: no suffix
```

`dispatch_file(path, source, ctx)` selects the chunker by an **explicit
four-tier precedence**:

| Tier | Rule | Why |
|------|------|-----|
| **1. Config override** | An extension re-routed via `apply_overrides` wins outright. | Operator config is the strongest, most explicit signal — it must overrule a greedy predicate. |
| **2. Predicate / `handles()` match** | The first registered chunker (in registration order) whose `handles(path)` returns `True` — **excluding** the chunker the suffix map already binds to `path`'s extension. | This is the tier that lets a basename/pattern-keyed chunker be reached, without a generic suffix chunker shadowing it. |
| **3. Default suffix map** | The chunker bound to `path`'s extension by its default registration. | The common case. |
| **4. Unknown → `[]`** | Nothing claims the file → return `[]`, **not an exception**. | Directory walks skip unregistered files silently. |

Two subtleties worth internalising:

- **Tier 2 excludes the suffix-owner.** A chunker already bound to `path`'s
  extension is a *tier-3* citizen; letting it win in tier 2 would just be the
  suffix map by another name and would let a generic suffix chunker (whose
  `handles` is itself a suffix test) shadow a more-specific basename claimant.
  Tier 2 is precisely *"claim a file the suffix map would NOT route to me."*
- **Registration order breaks ties in tier 2.** First registered, first asked.

Other registry facts:

- **`register(key, chunker, extensions)`** — re-registering an existing key keeps
  its slot (overwrites in place); extensions are stored lower-cased so matching is
  **case-insensitive** (`.PY` == `.py`).
- **`apply_overrides(overrides)`** — re-route extensions to a different registered
  chunker key. It is **all-or-nothing**: every target key is validated *before any*
  routing entry is written, so a single unknown key raises `KeyError` and applies
  none of the batch.
- **The unknown→`[]` rule** also covers an extension-less path (no suffix, no
  predicate match).

### Worked example — a basename-keyed `Makefile` chunker

A generic chunker for `Makefile` (no extension to key on). It claims the file by
basename via `handles`, and emits one chunk per top-level `target:` rule. This is
real, verified code — it is the shape the `loremaster` test suite uses to prove
the predicate tier works.

```python
from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext


class MakefileChunker(Chunker):
    """Chunk a Makefile into one chunk per top-level rule (basename-keyed)."""

    chunk_type = "makefile"

    def handles(self, path: str) -> bool:
        # Basename match — the registry's predicate tier reaches this even though
        # the chunker owns no suffix.
        return path.rsplit("/", 1)[-1] == "Makefile"

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        chunks: list[Chunk] = []
        for lineno, line in enumerate(source.splitlines(), start=1):
            # A make rule starts at column 0 and contains a colon.
            if line and not line[0].isspace() and ":" in line and not line.startswith("#"):
                target = line.split(":", 1)[0].strip()
                if target:                       # identity must be non-blank
                    chunks.append(
                        Chunk(
                            chunk_type=self.chunk_type,
                            source_text=line,
                            identity=target,     # the rule name is the natural key
                            line_start=lineno,
                            line_end=lineno,
                        )
                    )
        return chunks
```

Register it with **no suffixes** so it is reached only through its predicate:

```python
registry.register("makefile", MakefileChunker(), [])
chunks = registry.dispatch_file("/project/Makefile", source, ctx)
```

> When this chunker is contributed through a `loremaster` `Extension`, the
> framework reads an optional `default_suffixes` class attribute (defaulting to
> `()`), namespaces the registry key, and enforces a guard that a chunker may not
> shadow an existing suffix-owner — see `loremaster/EXTENDING.md` §"The register
> guard". From pure `lorescribe`'s point of view, only `handles`/`chunk` matter.

---

## 2. XML `SchemaProfile`

The built-in [`XmlChunker`](lorescribe/xml_generic.py) is **schema-agnostic**. It
parses with `defusedxml` (so an XXE / billion-laughs document is *refused at parse
time*, never expanded) and emits chunks under a **size-tiered granularity
policy**:

- A **small** file (whole document fits under `ctx.max_input_tokens`) collapses
  to a **single whole-file chunk** rooted at the document element.
- A **larger** file splits into **one chunk per top-level child element**.
- A child still over the cap is **recursed into**, one chunk per its own children,
  carrying a `tag_path` breadcrumb in the metadata.

Every chunk carries a generic metadata block (`root_tag`, `element_tag`,
`tag_path`, `id_attr`, `name_attr`, `namespaces`, `attributes`, `depth`,
`line_range`, `child_count`, `depth_truncated`) and an `identity` of
`id_attr or tag_path`. The default `chunk_type` when no profile fires is
`"xml_element"`.

A profile rides on top to add domain knowledge **without the core importing
anything domain-specific.**

### The `SchemaProfile` protocol

A profile is **any callable** matching this signature — a class implementing the
Protocol *or* a bare function both work:

```python
import xml.etree.ElementTree as ElementTree
from lorescribe.models import ChunkContext, ProfileResult

class SchemaProfile(Protocol):
    def __call__(
        self, element: ElementTree.Element, ctx: ChunkContext
    ) -> ProfileResult | None:
        """Claim `element` with a ProfileResult, or decline with None."""
```

The `element` is a standard-library `xml.etree.ElementTree.Element`. Note its
`tag` is in **Clark notation** for namespaced elements (`{uri}localname`), so to
match a localname strip the namespace:

```python
element.tag.rsplit("}", 1)[-1] == "record"
```

### How a profile customises a chunk

For each candidate element the chunker consults **every registered profile in
order; the first non-`None` result wins** (`_first_profile_result`). When a
profile returns a `ProfileResult`:

- **`chunk_type`** replaces the generic `"xml_element"`.
- **`extra_metadata` merges OVER** the generic metadata block
  (`metadata.update(result.extra_metadata)`), so you can *augment* the generic
  keys, and they survive unless you deliberately override one.
- **`skip=True`** drops the element from the output entirely (`_build_chunk`
  returns `None`).
- **`force_own_chunk=True`** is the **granularity override** (below).

### `force_own_chunk` — the granularity override

By default the *size tier* decides whether an element collapses into a whole-file
chunk or stands alone. `force_own_chunk=True` overrides that **in one direction
only**:

- It **forces a small document to descend** so a profile-significant element
  becomes its **own** chunk instead of collapsing into the single whole-file
  chunk. (`_emit` checks `_child_forces_own_chunk` for each direct child and
  descends if any forces it.)
- It does **not** override the token cap the *other* way: an element that is
  itself over the cap is still split for embeddability. `force_own_chunk` only
  overrides *collapse-when-small*, never *split-when-big*.
- A profile that claims an element only to **skip** it (`skip=True`) does **not**
  force a descent — there is nothing to emit.

### The purity / idempotence contract (mandatory)

> **Profiles MUST be pure / side-effect-free and idempotent.**

`XmlChunker` may consult a profile **more than once for the same element** — once
to decide descent/granularity (`_child_forces_own_chunk`), again when actually
building the chunk (`_build_chunk`). A profile that mutates external state
(counters, caches, logging) would **double-fire**. Always return the *same*
`ProfileResult` for the same `(element, ctx)`.

### Worked example — claim a generic `<threshold>` element (NOT Odoo)

A profile that claims every `<threshold>` element, stamps a custom `chunk_type`
and metadata, and forces each into its own chunk even in a small file that would
otherwise collapse to one whole-file chunk. This is verified shape — it mirrors
the profile the `loremaster` test suite uses to prove seam 2 reaches the
constructed chunker.

```python
import xml.etree.ElementTree as ElementTree
from lorescribe.models import ChunkContext, ProfileResult


class ThresholdProfile:
    """Claim <threshold> elements as their own chunks; decline everything else."""

    THRESHOLD_TAG = "threshold"
    CHUNK_TYPE = "threshold_map"

    def __call__(
        self, element: ElementTree.Element, ctx: ChunkContext
    ) -> ProfileResult | None:
        # Strip Clark-notation namespace before comparing the localname.
        if element.tag.rsplit("}", 1)[-1] == self.THRESHOLD_TAG:
            return ProfileResult(
                chunk_type=self.CHUNK_TYPE,
                extra_metadata={"claimed_by": "threshold_profile"},
                force_own_chunk=True,   # stand alone even in a small file
            )
        return None   # decline → next profile, or the generic default
```

Wire it into a chunker (profiles are an ordered constructor argument):

```python
from lorescribe.xml_generic import XmlChunker

chunker = XmlChunker(profiles=[ThresholdProfile()])
chunks = chunker.chunk(xml_source, ctx)
# Each <threshold> is now its own chunk of type "threshold_map" carrying
# {"claimed_by": "threshold_profile"} merged over the generic XML metadata.
```

Given a small file:

```xml
<config>
  <threshold name="warn">80</threshold>
  <threshold name="crit">95</threshold>
</config>
```

Without the profile this collapses to **one** `xml_element` chunk. With it, you
get **two** `threshold_map` chunks (each `<threshold>` standalone) — `id_attr`
falls back through `(id, name, key, xml:id)`, so each chunk's `identity` is the
`name` attribute, keeping the siblings distinct.

---

## 3. JavaScript `JsProfile`

The built-in [`JavascriptChunker`](lorescribe/javascript.py) is **domain-agnostic**.
It detects only *generic* JS structure:

- top-level `function NAME(...) {...}` → `js_function`
- top-level `class NAME {...}` → `js_class`
- top-level `export` declarations → `js_module` (named from the exported symbol;
  an anonymous `export default` falls back to the file stem)
- the unstructured remainder → `window#N` line windows (`chunk_type == "window"`)

Minified bundles (a `.min.js` path, or content whose average line length exceeds
`MINIFIED_AVG_LINE_LENGTH == 800`) carry no semantic value and are **skipped
entirely** (`chunk` returns `[]`). Routing, though, is by `.js` extension only —
`handles` claims a `.min.js` path; the minified decision happens *inside* `chunk`.

### `JsBlock` — the granularity profiles see

The JS analogue of the XML chunker's `Element` is a **frozen dataclass**:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class JsBlock:
    kind: str            # "function" | "class" | "module" | "window"
    name: str | None     # declared/derived name, or None for an anonymous window
    source_text: str     # the block's own raw source
    line_start: int      # 1-based first line
    line_end: int        # 1-based last line
```

### The `JsProfile` protocol

```python
from lorescribe.javascript import JsBlock
from lorescribe.models import ChunkContext, ProfileResult

class JsProfile(Protocol):
    def __call__(self, block: JsBlock, ctx: ChunkContext) -> ProfileResult | None:
        """Claim `block` with a ProfileResult, or decline with None."""
```

Same first-non-`None`-wins semantics as the XML hook: a claimed block's
`chunk_type` replaces the generic one, `extra_metadata` merges over the generic
metadata, and `skip=True` drops the block entirely.

> **Difference from the XML hook:** `JsProfile` does **not** use
> `force_own_chunk` — there is no size-collapse-when-small tier for JS. The JS
> chunker scans the source into ordered blocks (structural units interleaved with
> `window` remainders) and emits each; profiles only retag/skip a block, they do
> not change block granularity. `force_own_chunk` is an XML-only concept. (The
> field exists on the shared `ProfileResult`, but the JS chunker ignores it.)

The same **purity / idempotence** expectation applies — keep a profile
side-effect-free and deterministic for a given `(block, ctx)`.

### Worked example — claim a generic `function` block (NOT Odoo)

```python
from lorescribe.javascript import JsBlock
from lorescribe.models import ChunkContext, ProfileResult


class WidgetProfile:
    """Retag every top-level function block; decline everything else."""

    CHUNK_TYPE = "widget"

    def __call__(self, block: JsBlock, ctx: ChunkContext) -> ProfileResult | None:
        if block.kind == "function":
            return ProfileResult(
                chunk_type=self.CHUNK_TYPE,
                extra_metadata={"claimed_by": "widget_profile"},
            )
        return None
```

Wire it in via the constructor:

```python
from lorescribe.javascript import JavascriptChunker

chunker = JavascriptChunker(profiles=[WidgetProfile()])
chunks = chunker.chunk(js_source, ctx)
# Every top-level `function` block now has chunk_type "widget" with the merged
# metadata; classes, modules, and windows fall through to the generic defaults.
```

---

## Checklist for a new hook

- [ ] A `Chunker` implements **both** `handles` and `chunk` (or it can't be
      instantiated).
- [ ] Every emitted `Chunk` has a **non-blank `identity`**; siblings sharing an
      identity differ in `sub_ordinal`.
- [ ] Every chunk is **at or below `ctx.max_input_tokens`** (split anything over).
- [ ] A predicate-keyed chunker registered with **no suffixes** is reached via the
      tier-2 predicate; a suffix-keyed one via tier 3.
- [ ] A `SchemaProfile` / `JsProfile` is a **callable** returning
      `ProfileResult | None`, **pure and idempotent** (the XML chunker may call it
      twice for one element).
- [ ] Profile `extra_metadata` **merges over** the generic block — pick keys that
      augment rather than clobber unless you mean to.
- [ ] `skip=True` drops the element/block; `force_own_chunk=True` (XML only)
      forces standalone granularity in a small file.
