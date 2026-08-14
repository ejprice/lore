# Configuring extensions in `lore.yaml`

How to enable and configure a lore **extension** — a domain-specific plug-in that
turns the generic code/docs RAG into a specialized MCP server.

> **Status note (as of packet 46, "extension discovery wiring").** The wiring
> described here is live, but **no extension is registered yet** — the registry
> ships empty and the first extension lands in a later packet. Practical upshot:
> adding an `extensions:` block *today* will fail boot (see
> [Boot behavior](#boot-behavior--what-fails-and-how)). Leave `extensions:` out
> until an extension exists; an absent block is the generic RAG, unchanged.

---

## What an extension is

lore is, by default, a generic code+docs RAG. An **extension** turns it into a
domain-specific MCP — for example a Dungeons & Dragons rules server, or an Odoo
code server — by plugging domain behavior into lore's `Extension` framework:
custom chunkers, domain-specific tools, extra field indexes, a search-rerank
hook, lifespan hooks, and so on. A lore server with **zero** extensions
configured behaves exactly as the generic RAG.

## The mental model: two halves must line up

Enabling an extension takes two independent things, and **both** are required:

1. **Code — the extension is *registered*.** The extension's `Extension`
   subclass must be listed in the static registry `EXTENSION_REGISTRY`
   (a `dict[str, type[Extension]]` in `loremaster/loremaster/extension.py`).
   Whoever ships the extension does this; you cannot conjure an extension from
   config alone.
2. **Config — you *name* it in `lore.yaml`.** You add the extension's name (and
   its config) under the top-level `extensions:` key.

When lore starts, it reads `extensions:`, looks each name up in the registry,
instantiates it, and composes it into the server. If a name isn't in the
registry, **lore refuses to start** — deliberately. A misconfigured extension is
a loud failure, never a silently-missing feature.

## Syntax

`extensions:` is a **top-level** key in `lore.yaml` — a mapping of *extension
name* → *that extension's config*:

```yaml
extensions:
  <extension-name>:      # MUST equal the extension's `name` (and be registered)
    <key>: <value>       # this extension's own config — validated by the extension
    ...
```

- **The key is the extension's name.** It must exactly match the extension's
  declared `name` *and* the key it is registered under in `EXTENSION_REGISTRY`.
  A mismatch fails boot.
- **The nested mapping is the extension's own config slice.** lore passes it
  through verbatim; the extension validates it with its *own* schema
  (its `config_model()`). That schema is strict (`extra="forbid"`), so a typo'd
  key *inside* the slice fails boot too.
- **If an extension declares no config**, give it an empty mapping (`{}`) — or
  whatever the extension's own docs say.

`extensions:` is **optional**. Absent ⇒ empty ⇒ generic RAG. Note the rest of
`lore.yaml` is strict: a typo'd *top-level* key (e.g. `extensionz:`) is itself an
error. `extensions:` is the one sanctioned pass-through the base config does not
interpret — everything under it is the extension's responsibility.

## Worked example

Where an `extensions:` block sits in a `lore.yaml`, using a **hypothetical `dnd`
extension** (⚠ illustrative only — not a real, registered extension, and the
`dnd:` config keys below are invented for the example). For the full, real
top-level structure of a `lore.yaml`, see this repo's own `lore.yaml`.

```yaml
schema_version: 1
project: {slug: dnd, root: .}
embedding:
  backend: tei
  base_url: http://localhost:8080
  # ... (the rest of the embedding config)
anthropic:
  api_key_env: ANTHROPIC_API_KEY
roots:
  - tier: rules
    watch: static
    source: /path/to/dnd/output
    provider: local_directory
    include: ["**/*.md"]
server: {host: 127.0.0.1, path: /mcp, port: 9210}

# The extension block — a top-level key, at the same level as `roots`/`server`:
extensions:
  dnd:                       # matches the dnd extension's `name` + registry key
    edition_default: "2024"  # <- the dnd extension's OWN config (it validates this)
```

## Boot behavior — what fails, and how

Discovery runs when lore starts. For **each** name under `extensions:`:

- **Unknown name** (not in `EXTENSION_REGISTRY`) → boot fails with a teaching
  error that names the *actual* registered set:

  > unknown extension `'X'` named in the `extensions:` config; no such extension
  > is registered. Known extensions: `<the real registered names>`. Register its
  > class in `loremaster.extension.EXTENSION_REGISTRY`, or remove the key.

  The known-set is derived from the registry (never a stale hand-list), so it
  tells you exactly what's available. With the registry empty, it reads
  `(none registered)`.

- **Name doesn't match the class** (registry key ≠ the extension class's `name`)
  → boot fails naming *both* sides — because a mismatch would otherwise validate
  the wrong config slice.

- **Bad config slice** (a key the extension doesn't accept, or a missing required
  field) → a validation error at boot, raised by the extension's own schema.

All three are **fail-loud by design**: lore stops rather than starting with an
extension silently missing or misconfigured.

## Quick reference

| Rule | Detail |
|---|---|
| Where | Top-level `extensions:` key in `lore.yaml` |
| Shape | `{ <name>: <config-mapping> }` |
| Optional? | Yes — absent ⇒ generic RAG |
| Name | Must match the extension's `name` **and** its `EXTENSION_REGISTRY` key |
| Config slice | Validated by the extension itself (`extra="forbid"`) |
| No config? | Use `{}` |
| Unknown / mismatched / invalid | **Boot fails loudly** — never silent |
| Today | Registry ships empty — don't add `extensions:` until an extension is registered |

## For extension authors (the code half)

To make a name valid in `extensions:`, register the `Extension` subclass in
`loremaster/loremaster/extension.py`:

```python
EXTENSION_REGISTRY: dict[str, type[Extension]] = {
    "dnd": DnDExtension,   # the key MUST equal DnDExtension().name
}
```

The subclass must implement the abstract `name` property (its stable name = its
config key). If it takes config, override `config_model()` to return a pydantic
model that validates its `extensions:` slice; if it takes none, leave
`config_model()` at its default (`None`) and configure it with `{}`. Every other
capability — chunkers, tools, field indexes, search hooks, lifespan hooks — is an
optional seam with a safe inert default, so an extension overrides only what it
needs. See the `Extension` base class in `loremaster/loremaster/extension.py` for
the full set of seams.
