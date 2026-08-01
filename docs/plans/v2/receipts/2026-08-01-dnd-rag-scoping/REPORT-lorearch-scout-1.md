# REPORT-lorearch-scout-1 — reuse map of the lore workspace for a D&D rules RAG

brief-base v9 read
state: done
deviations: (1) grep fallbacks used for four non-symbol/textual questions — disclosed in §0; (2) read-only, so every claim below is a READ of source, never a run.
Packages considered: none — no mechanism specified (this is a discovery/reuse survey; it specifies no new mechanism). The one package-relevant observation is recorded in §2 (lorescribe's markdown chunker already delegates to `langchain_text_splitters`).
decisions-needed:
  - FORK A/B is genuinely open and hinges on ONE fact: the extension framework is COMPLETE and UNWIRED (§6.4) — 0 production call sites of `LoreServer.register_extension`.
  - Whether `lore_map` / `lore_impact` / `lore_dead_code` / `lore_get_symbol` / `lore_verify` returning EMPTY on a code-free corpus is a Consumer-Law violation that the allowlist must cover (§10).
receipt pointers: §1 workspace · §2 lorescribe/non-code path · §3 loresigil · §4 tiers+ingest · §5 store · §6 MCP+allowlist hook · §7 cross-cutting · §8 deploy · §9 multi-user proposal · §10 minimal tool set · §11 verdict table · §12 flags

Measured 2026-08-01 against `feat/surreal-unification` @ `a049118`, lore index synced
2026-08-01T14:26Z (`lore_index()` roots: tier `lore` → `/workspace`, branch
`feat/surreal-unification`, ref `a0491183ca6fd623f55cc125104e28cb43f13e42`). Every
present-tense claim below is a claim about that ref.

---

## §0 — Capability check + tool honesty

Brief demanded: `lore_search`, `lore_get_symbol`, `lore_map`, `lore_read`, `lore_impact`,
`lore_index`. All six loaded in one `ToolSearch` call and all six were available. No
demand in the brief was unmeetable.

**Grep/Read fallbacks, said out loud** (all four are cases the CLAUDE.md dogfood protocol
names as legitimate — non-symbol textual seams and cross-cutting maps):

| # | Question | Why not lore | What I ran |
|---|---|---|---|
| 1 | "does ANY tool-gating config exist?" | An **absence** proof over a textual seam. A semantic search cannot establish non-existence. | `grep -rn "allowlist\|enabled_tools\|tool_gating\|disable.*tool" --include=*.py loremaster/loremaster/` — every hit is `logging_setup`'s auth-scheme allowlist, `shellout`'s spawner allowlist, or `config`'s unwrap-allowlist prose. **No tool gating exists.** |
| 2 | the registered tool NAME set | The names live in `@mcp.tool(name=...)` decorator kwargs, not symbols. | `grep -n 'name="lore_' server.py` → 15 names |
| 3 | the exact-set / instructions pins | Test-file constants, not symbols. | `Read` of `test_mcp_server.py` around `_ALL_BUILTIN_TOOL_NAMES` |
| 4 | corroborating the `register_extension` dead verdict | `lore_impact`'s own caveat says a "dead" verdict is a lead, never proof. | `grep -rn "register_extension" --include=*.py .` excluding tests — corroborated (§6.4) |

No lore weakness was routed around; no `lore_findings` friction row was warranted (each
fallback is a documented, sanctioned case rather than a gap).

---

## §1 — Workspace layout and dependency direction

`pyproject.toml` `[tool.uv.workspace] members = ["lorerunes", "lorescribe", "loresigil", "loremaster"]`.
Dependency direction is stated as law in `CLAUDE.md` ("`lorerunes` — THE HOME FOR SHARED CODE"):

```
lorerunes/     shared stdlib-only primitives   (depends on NO sibling)
lorescribe/    the transcriber (chunkers)      -> lorerunes
loresigil/     the embedder clients            -> lorerunes
loremaster/    the keeper (server/store/index) -> all three
```

| Member | What it is | Size | Verdict for a rules corpus |
|---|---|---|---|
| `lorerunes` | Exactly one module today: `lorerunes.blankness` (`is_blank`). A shared-predicate address, deliberately tiny. | ~1 file | **GENERIC** |
| `lorescribe` | Source→`Chunk` transcription. `ChunkerRegistry` + 8 concrete chunkers. | 12 modules | **GENERIC** (see §2) |
| `loresigil` | Embedder clients + resilience (`Embedder` ABC, `TEIEmbedder`, `ResilientEmbedder`, `VoyageTokenCounter`, `FakeEmbedder`). | 14 modules | **GENERIC** (see §3) |
| `loremaster` | Everything else: config, index/watcher, SurrealDB store+schema, search, code graph, memory, ledgers, MCP server. ~34 modules; `server.py` alone is 9931 lines. | large | **MIXED** — see §4–§7 |

**Key structural fact for the A/B decision:** the three lower members are importable as
libraries by anything, and carry no lore-repo or code-corpus coupling. A separate D&D MCP
that imports `lorescribe` + `loresigil` + `lorerunes` is a *supported* dependency shape
today; only `loremaster` would have to be forked or re-implemented.

---

## §2 — lorescribe: what it actually transcribes (**GENERIC**)

`lorescribe` is **not** AST-only. `ChunkerRegistry.dispatch_file` (`lorescribe/registry.py`)
routes by extension/predicate with a four-tier precedence (config override > chunker
`handles()` predicate > default suffix map > `[]`). The concrete chunkers on disk:

`astroid_parse.py` (Python resolution core) · `python_ast.py` · `markdown.py` ·
`javascript.py` · `sql.py` · `stylesheet.py` · `xml_generic.py` · `text.py`.

**The non-code path is completely code-free.** `MarkdownChunker` (`lorescribe/markdown.py`)
splits on the ATX heading hierarchy (h1–h4), preserves fenced code blocks whole, size-splits
prose via `RecursiveCharacterTextSplitter.from_language(Language.MARKDOWN)`, and enforces the
embedder's hard token cap against the *composed* embedding text. It emits
`chunk_type="markdown_section"`, `identity` = the `h1 > h2 > h3` breadcrumb (with a `#N`
occurrence ordinal on repeats), and `metadata_header = "File: <path>\nSection: <breadcrumb>"`.
Nothing in it touches Python, imports astroid, or knows what a symbol is.

**The doc tiers prove it in production, at scale.** `lore.yaml` declares three static
non-code tiers — `surrealdb-docs` (`**/*.mdx`), `surrealql-tests` (`**/*.surql`),
`spectron-docs` (143 `.mdx`, added 2026-07-23) — routed by the `chunkers:` map
(`".md": markdown`, `".mdx": markdown`, `".surql": text`). The `spectron-docs` comment
records the load-bearing detail: adding that root **did not change the chunkers map**, so the
embedding-schema fingerprint was unchanged and no re-embed was triggered — only the new files
indexed incrementally.

**Verdict: GENERIC.** ~141 markdown D&D rulebooks need **zero** lorescribe work. The
`Chunk` model (`lorescribe/models.py`) is domain-neutral: `chunk_type`, `source_text`,
`identity`, `sub_ordinal`, line span, a free-form `metadata: dict[str, Any]`, and a
`metadata_header`. The only chunker-side *opportunity* (not a requirement) is a bespoke
rules chunker that splits on a stat-block boundary rather than a heading — that would be a
new `Chunker` subclass, the same shape as the eight already there.

---

## §3 — loresigil: the embedder client (**GENERIC**)

`Embedder` (`loresigil/base.py`) is a content-agnostic ABC: `embed_query` /
`embed_documents` / `embed_document_chunks` / `count_tokens` / `dim` / `normalized` /
`probe` / the batch quartet. `TEIEmbedder` (`loresigil/tei.py`) POSTs
`{"inputs": [text, ...]}` to `{base_url}{endpoint}` with a bearer token and reads back a
bare `[[float × 2048], ...]`. There is **no code-shaped preprocessing anywhere** in the
member — no identifier splitting, no language detection, no AST awareness. The only
"tuning" is *retrieval-asymmetric prompting*: `query_prompt_name` / `document_prompt_name`
are config strings passed straight through as TEI's `prompt_name` (lore.yaml uses
`query`/`document`), which is a voyage-4-nano feature, not a code feature.

Resilience lives in `ResilientEmbedder` (429 backoff, 422 sub-split backstop, `isfinite`
quarantine) and `VoyageTokenCounter` (the exact pinned tokenizer). All content-neutral.

**Where the embedder container lives / sharing:** `lore.yaml` points at
`http://mbpsrv.firehawktransam.org:8080` `/embed` — an **external, host-level TEI service**,
not a per-project container. The lore-deploy skill's own description calls it "the
self-hosted voyage-4-nano embedder" and treats it as shared infrastructure alongside the
shared SurrealDB store; `setup` "hard-probes `/embed`" rather than starting anything.
`lore.yaml.sample` documents a drop-in alternative backend (`voyage-context`, hosted).

**Verdict: GENERIC, shared as-is.** A D&D instance points at the same TEI endpoint and
costs nothing extra. Note the sample's own caution, which cuts the other way for prose: an
internal eval found contextualization "does not out-perform flat chunk embedding for
AST-chunked code" — that finding is scoped to code and does **not** transfer to rules prose,
so if anyone reaches for `voyage-context` on the D&D corpus it must be re-measured, not
inherited.

---

## §4 — loremaster ingestion: the tier system (**GENERIC-WITH-WORK**, and the work is small)

### 4.1 The config surface (`loremaster/config.py`)

`LoreConfig` is `extra="forbid"` at every known section. The tier system is `roots:` — a
list of `RootConfig`, each with:

- `tier: str` — a first-class key dimension; records, manifest, store and graph all
  partition by it, so two tiers' copies of one path coexist.
- `watch: Literal["live", "static"]` — the only two tier TYPES.
- `live` requires `path`; `static` requires `source` + `version` + `provider`
  (`RootConfig._check_policy_fields` enforces this at load, per-policy).
- per-root `include` / `exclude` glob lists.

`LoreConfig.effective_roots` synthesises ONE live root from the top-level `include` when
`roots:` is empty, so single-tree configs still index.

### 4.2 **Could a D&D corpus be declared as a tier TODAY? YES — verbatim, no code.**

Both shapes work with the code as it stands:

```yaml
# live (watched, edits re-index in seconds)
- tier: dnd2024
  watch: live
  path: /workspace/rules
  include: ["**/*.md"]

# static (frozen, version-stamped, materialised into the snapshot layout)
- tier: dnd2024
  watch: static
  source: /home/ejprice/docker/mcp/lore-corpora/dnd-2024
  version: "2024.1"
  provider: local_directory
  include: ["**/*.md"]
```

`provider: local_directory` resolves to `LocalDirectorySourceProvider`
(`loremaster/source/local_directory.py`) — wired as the generic default for a static root at
`server.py::_build_source_providers` and `index/cli.py`. It `copytree(symlinks=True)`s the
source into `SnapshotLayout.materialization_dir(tier)`; the server bind-mounts that `:ro`
and `SnapshotLayout.resolve` does the two-tier containment check on every read. The `.md`
chunker mapping already exists. `lore_search(tier="dnd2024", …)` and `lore_read(tier=…)`
work immediately, because both take `tier` as a first-class parameter.

This is not speculation: it is the exact mechanism the three vendor doc tiers in `lore.yaml`
already run on.

### 4.3 The watcher and reconcile sweeps (**GENERIC**)

`WatcherConfig` (`enabled` / `observer` / `debounce_ms` / `reconcile_interval_s`) drives
`index/watcher.py` (inotify) and `index/reconcile.py`. Both operate on files+manifest rows,
not on language. `lore_index(reconcile=True)` forces a whole-tier sweep, optionally
tier-scoped. No corpus coupling.

### 4.4 Where a "structured entity extraction" step would plug in (**this is the real work**)

Today `Indexer` composes, per file, ONE atomic transaction of fragments:
`chunk → file_text → manifest → graph` (`index/indexer.py`, `_compose_*` /
`_graph_fragment`). The graph fragment is **conditional and Python-only**:
`_graph_fragment` returns `None` "when `path` is not a Python file (the graph is a Python
AST structure only)". A `.md` file therefore lands chunks + file_text + manifest and
nothing else.

A spells→typed-records+edges step has **exactly one natural seam**: a fourth fragment
alongside `_graph_fragment`, composed into the same `store.apply(fragments)` transaction, so
entity rows and their chunks commit or roll back together. Two ways to reach it:

- **In-repo (option A):** add `_entity_fragment(tier, path, chunks)` beside
  `_graph_fragment`, keyed on a per-tier extractor. Small diff, but it edits the hot path
  every existing lore instance runs.
- **Via the extension framework (the designed path):** an extension contributes a
  chunker + `payload_indexes` + tool specs. ⚠ **The extension ABC has no ingest-fragment
  seam.** Its eleven seams (`loremaster/extension.py`) cover chunkers, profiles, tools,
  search augment/rerank, format, chunk_key, config model, field indexes, lifespan,
  source providers, detail classification — but **nothing that contributes a
  write-fragment to the per-file index transaction**. So entity extraction is a
  *twelfth seam that does not exist*, in either option. That is the single largest
  unbudgeted item in this survey.

Cheaper interim: `Chunk.metadata` is `object FLEXIBLE` in the store (§5), so a bespoke rules
chunker can stamp `{"spell": "Fireball", "level": 3, "school": "evocation"}` onto each chunk
today, with **no** schema change — retrievable, but not graph-traversable and not indexed
(see §5.3).

---

## §5 — SurrealDB store layer (**GENERIC substrate; the symbol graph is CODE-SPECIFIC**)

### 5.1 Tables that exist (`store/surreal_schema.py`, module constants)

| Group | Tables |
|---|---|
| corpus | `chunk`, `file`, `file_text`, `meta` |
| snapshots | `snapshot`, `snapshot_entry` |
| memory | `memory` |
| ledgers | `finding`, `finding_counter`, `task`, `blocks` (relation), `command` |
| comms | `agent`, `brief`, `briefed` (relation), `brief_counter`, `message`, `to` |
| **code graph** | **`code_node`, `name`, `refers` (relation), `answers_to` (relation)** |
| telemetry / calibration | `trace`, `floor_measurement`, `floor_head`, `lease` |

### 5.2 How schema is defined and migrated (**GENERIC, and this is the good news**)

The schema is **already sliced per domain**, not monolithic. Each domain owns a
`_<domain>_statements() -> list[str]` emitter and a public `generate_<domain>_ddl()`:
`generate_ddl` (corpus), `generate_manifest_ddl`, `generate_memory_ddl`,
`generate_task_ddl`, `generate_finding_ddl`, `generate_agent_ddl`, `generate_brief_ddl`,
`generate_message_ddl`, `generate_graph_ddl`, `generate_floor_calibration_ddl`,
`generate_lease_ddl`. Field specs are declared as `(name, type, assert)` tuples and the
column/filter-key sets are **derived** from them (`CHUNK_COLUMNS` and `CHUNK_FILTER_KEYS`
are computed from `_CHUNK_FIELD_SPECS`, never hand-copied).

**Adding a D&D domain's tables is a well-trodden path with a recent precedent**
(`floor_measurement`/`floor_head`/`lease`, commit `7acbef4`): a `_SPELL_FIELD_SPECS` tuple,
a `_spell_statements()` emitter, a `generate_spell_ddl()` slice, and an owner class whose
`ensure_ready()` calls `_txn.execute_transaction` — the exact recipe the multi-user proposal
(§9) writes out for `principal`. Migration clauses are ruled and documented:
TABLE `IF NOT EXISTS`, FIELD **`OVERWRITE`**, INDEX `IF NOT EXISTS`; `ALTER` is a trap
(`docs/reference/surrealdb-31-capabilities.md` §1.1/§1.3 — the #107 outage).

`store/_txn.py` is the shared, reusable SurrealDB driver: `bootstrap_session`, `run_query`,
`execute_transaction`, `execute_read_transaction`, `retry_on_conflict`, `compose`,
`TxnFragment`, plus engine-error classification. Fully domain-neutral. **This is the single
most valuable reusable asset for "SurrealDB-native graph queries"** — it is the hardened
answer to retry/conflict/envelope handling that #102/#120 cost this project eleven
hand-rolled copies to learn.

### 5.3 ⚠ The store's PUBLIC surface has no arbitrary-query verb

`SurrealStore`'s public async methods are exactly: `ensure_ready`, `close`, `upsert`,
`record_trace`, `trace_aggregates`, `apply(fragments)`, `replace_file`, `delete_by_file`,
`delete_by_tier`, `delete_points`, `count`, `existing_point_ids`, `file_text`, `scroll`,
`hybrid_search`, `enumerate_calibration_pool`. **There is no `store.query(surql)`.** A
`spell→class→level` traversal therefore cannot be issued through the shared store handle
an extension receives in `ExtensionContext.store`.

The established pattern instead is a **domain-owning ledger class with its own connection**
— `FindingLedger.__init__(*, url, namespace, database, user, password)` opens its own
session and drives `_txn` directly; `TaskLedger`, the agent registry and the brief store do
the same. A `SpellStore` would follow that shape. This is a *pattern to follow*, not a
blocker — but it is **not** free reuse, and CLAUDE.md's ONE IMPLEMENTATION law means the
right move is to reuse `_txn`'s driver rather than clone a ledger's boilerplate.

### 5.4 Is the symbol graph code-specific? **YES, unambiguously.**

`loremaster/graph.py` module docstring: *"The derivation is GENERIC over any Python AST
chunks the `PythonAstChunker` emits — there is ZERO Odoo-specific handling."* Generic over
**Python**, not over corpora. Node kinds are `module`/`class`/`method`/`function`; edge
kinds are `defines`/`inherits`/`imports`/`calls`; resolution is astroid inference against
project roots. `index/indexer.py` states the constraint at the ingest seam: non-Python files
are given no graph slice.

**Consequence for D&D:** `code_node`/`refers` are unusable for spell→class edges. A
D&D graph is a NEW relation table — and the repo already has three precedents for exactly
that (`blocks` on tasks, `briefed` on briefs, `answers_to` on messages), plus a ruled
hazard note: RELATION edges self-delete on endpoint delete, `record<t>` links do not; and
`UPDATE` of an edge's `in`/`out` is a **silent no-op** (re-pointing = DELETE + re-`RELATE`)
— `surrealdb-31-capabilities.md` §1.4/§2.

Also note: `chunk.metadata` is `object FLEXIBLE` (round-trips arbitrary nested blobs) but
is **not** a filter key — `CHUNK_FILTER_KEYS` is derived to contain only plain-`string`
non-fulltext columns. So `metadata`-stamped spell attributes are *carried* but not
*queryable* as search filters. Extension seam 8 (`payload_indexes`, kinds
`keyword`/`bool`/`fulltext`) is the designed answer, and it is unexercised in production
(§6.4).

---

## §6 — MCP server and tool registration

### 6.1 The registered surface: exactly 15 tools

From `grep -n 'name="lore_' server.py` (in registration order): `lore_search`,
`lore_get_symbol`, `lore_verify`, `lore_remember`, `lore_recall`, `lore_claim_task`,
`lore_tasks`, `lore_comms`, `lore_read`, `lore_diff`, `lore_findings`, `lore_index`,
`lore_dead_code`, `lore_impact`, `lore_map`.

Registration is `_register_tools(mcp, server)` — **15 hardcoded `@mcp.tool(...)`-decorated
nested closures** over `mcp` and `server`. Not a registry, not a table. The server class is
`TracingFastMCP(FastMCP)`, which records one `trace` row per dispatch.

### 6.2 The two pins the brief names (`loremaster/tests/test_mcp_server.py`)

- **Exact-set pin** — `TestToolRegistration::test_the_registered_surface_is_exactly_the_expected_set`
  asserts `names == _ALL_BUILTIN_TOOL_NAMES` (an **equality**, deliberately, because the
  other two registration checks are subset-only and "catch a removal/rename but NOT a
  silent ADDITION"). `_ALL_BUILTIN_TOOL_NAMES = _EXPECTED_TOOLS | {"lore_claim_task",
  "lore_tasks", "lore_comms"}`, where `_EXPECTED_TOOLS` is `_BARE_TOOL_NAMES` prefixed.
- **Dead-name hygiene scan** — `TestNoDeadToolNamesInAgentFacingText` extracts every
  `lore_`-shaped token from **all** served text (server `instructions`, every tool
  `description`, **and** every per-parameter `inputSchema` description) and asserts each
  names a **currently registered** tool. Its docstring records why the parameter-level leg
  exists: a real defect (F2) lived in a parameter description and a top-level-only scan
  would have missed it.
- Companion: `test_instructions_names_every_tool` — the instructions block must name every
  tool in `_ALL_BUILTIN_TOOL_NAMES`.

### 6.3 `_INSTRUCTIONS` is **STATIC**, and that is the cost centre

`_INSTRUCTIONS` is a module-level string constant in `server.py` (six sections: IDENTITY /
LADDER / CITATIONS / FRESHNESS / HONEST FAILURE / MEMORY, plus a comms paragraph and a TOOL
LOADING coda), interpolated once into the `TracingFastMCP(...)` constructor. It hardcodes
14 of the 15 tool names in prose. Exactly **one** value in it is derived
(`_MESSAGE_BODY_MAX_CHARS`, f-string-interpolated so "the prose cannot drift from the
constant it describes").

**Cost of adding a NEW tool** (measured by what the pins demand, not estimated):
1. one `@mcp.tool(...)` block in `_register_tools`;
2. add the name to `_ALL_BUILTIN_TOOL_NAMES` (else the equality pin reddens);
3. name it in `_INSTRUCTIONS` (else `test_instructions_names_every_tool` reddens);
4. a substantial `description` + a `description` on **every** input field (two separate
   pins index `tools[name]`);
5. any `lore_`-token it mentions must be a live tool (dead-name scan).

That is a genuinely low per-tool cost — but note item 3: **the prose is a hand-written
constant, so every added tool edits a shared string.**

### 6.4 ⚠⚠ THE HEADLINE FINDING: the extension framework is COMPLETE and UNWIRED

`loremaster/extension.py` is a full plugin contract, written *for exactly this use case* —
its own docstring: *"the contract by which a domain-specific MCP (e.g. a future
`odoo-code`) plugs into `loremaster` as a thin extension"*, with *"a bare `LoreServer` with
zero extensions registered behaves as the generic code/docs RAG, because every seam ships a
safe, inert default."* Eleven seams: chunkers · XML/JS profiles · **declarative `ToolSpec`s**
· search augment+rerank · result format · versioned chunk_key · **`config_model` validating
the extension's `extensions[name]` slice** · **`payload_indexes`** · async lifespan ·
source providers · detail classification. `LoreConfig.extensions: dict[str, dict[str, Any]]`
is *"the ONLY sanctioned extra top-level key"*, deliberately opaque. The downstream half is
live: `_register_extension_tools(mcp, server)` IS called from `build_mcp_server`, with a
name-collision guard that raises rather than shadowing, and `_extension_tool_wrapper`
republishes the handler's real signature so the published `inputSchema` matches what the
handler accepts (it *raises* on an un-annotated param rather than silently publishing
`type: string`).

**But nothing ever registers an extension.** `lore_impact("LoreServer.register_extension")`
→ **verdict `dead (heuristic)`, 0 production references, 37 test references, 340 covering
tests**. Corroborated by grep (impact's own caveat says a dead verdict is a lead, not
proof): the only non-test occurrences of `register_extension` are its definition, its
docstring mentions, and the *unrelated* `_register_extension_chunker` / `_register_extension_tools`
helpers. Production construction sites are `LoreServer(config)` in `index/cli.py::_run`,
`scout.py::Scout.from_config`, and `main()` → `LoreServer.from_config(args.config).run()` —
**none of them registers anything.**

**So: there is no config→extension discovery path.** `extensions:` in `lore.yaml` is parsed
and passed through, and then no code reads it to instantiate anything. Wiring it is a small,
well-scoped addition (an entry-point/registry lookup in `from_config`), but it **does not
exist**, and the framework has never run in production — 340 tests are all that stand behind
it.

### 6.5 Where a `lore.yaml` tool allowlist hooks

**No tool gating exists today** (grep receipt in §0). The multi-user proposal (§9) already
scoped it precisely and its three cost centres are corroborated by what I read:

1. `build_mcp_server` already binds `config`, so **no signature change** is needed.
2. `_register_extension_tools` is already a `for` loop — a one-line `continue`.
3. The 15 built-ins are hardcoded decorators; `FastMCP.tool()` applies `add_tool` at
   *definition* time, so "register later" does not exist. The DRY spelling is a
   config-consulting `_tool` indirection replacing `mcp.tool` at 15 sites — **one decision
   point, not 15 obligations.**
4. **The real cost is served prose**, and it is unavoidable: `_INSTRUCTIONS` is static and
   names 14 tools; and every surviving tool's own description cross-references its
   neighbours (`lore_search`'s description says *"prefer `lore_get_symbol`… follow up with
   `lore_read`"*). The dead-name scan compares served text against the **runtime registered
   set**, so disabling `lore_impact` reddens on *other* tools' descriptions. **Instructions
   AND descriptions must become functions of the enabled set.** That pin is correct and must
   be satisfied, never waived.
5. ⚠ A door the allowlist opens, already flagged in the proposal and confirmed in the code:
   `_register_extension_tools`'s collision guard checks `mcp._tool_manager.get_tool(name)` —
   the *registered* set. Disable a built-in and an extension may legally claim the name
   `lore_search`. The guard must check the **declared universe**.

---

## §7 — Cross-cutting services (**GENERIC**, with one caveat)

| Service | Tools | Coupling | Verdict |
|---|---|---|---|
| memory | `lore_remember`, `lore_recall` | `memory` table + a SQLite ledger (`memory/ledger.py`) + embeddings. Facts are free text with `kind`/`labels`/`importance`/`refs`. Nothing code-shaped. | **GENERIC** |
| findings | `lore_findings` | `Finding` = `subject`/`body`/`kind`/`area`/`category`/`created_by`/`status`. `area` is documented as *"the tool/subsystem the finding is about (e.g. `lore_impact`)"* — a **doc-level** convention, not a constraint; both fields are validated only as non-empty. | **GENERIC** (docstring examples are lore-flavoured) |
| tasks | `lore_claim_task`, `lore_tasks` | `Task` + `blocks` relation + a `claimed→in_progress→done` state machine + `report_path`. About *agents doing work*, not about code. | **GENERIC** |
| comms | `lore_comms` | `agent`/`brief`/`briefed`/`message`/`to`. Fleet coordination: register/heartbeat/brief/send/drain/ack. | **GENERIC** |
| diff/snapshots | `lore_diff` | Snapshots of indexed **files** (added/removed/modified). Language-neutral. | **GENERIC** |

**Caveat, and it is a real one:** these four are *orchestration* infrastructure for a
multi-agent build fleet. For a D&D rules RAG whose consumers are players/DMs (or a single
agent answering rules questions), they are **domain-agnostic but purpose-irrelevant** —
they would be dead weight on the served surface, which is precisely the argument for the
allowlist. `lore_comms` alone is a large tool (its dispatch section of `_INSTRUCTIONS` is
the longest paragraph in the block).

---

## §8 — Deploy: what a second instance costs (**GENERIC**)

The model is already N-instances-on-one-image, by design:

- **One shared image** `localhost/lore:latest` (`Containerfile`: `python:3.14-slim`, COPYs
  the four members, `CMD ["/app/.venv/bin/python", "-m", "loremaster.server"]`, no
  `ENTRYPOINT`, no `EXPOSE`).
- **N config-driven containers**, `lore-<slug>`, one per project.
- **Shared** SurrealDB store (`lore-surreal`, namespace `lore`, one **database per slug** —
  `LoreConfig.effective_surreal_database` = explicit `database` or the slug).
- **Shared** TEI embedder (external host service, §3).
- Per-slug secrets at `~/docker/mcp/lore-secrets/<slug>.env`.
- `lore_deploy.py::_free_port(DEFAULT_PORT_BASE=9201)` auto-allocates the MCP port;
  `_scaffold_lore_yaml` seeds slug-from-dirname, a free port, and `exclude_dirs` from
  `.gitignore`; `.mcp.json` is merged.
- Verbs: `setup` / `start` / `stop` / `status` / `conform`, all idempotent. `conform` runs
  the **baked** pytest inside the deployed image with a provenance guard asserting the
  members import the baked artifact, not the mount (#139).

**Cost of a `dnd` instance: essentially zero new deploy machinery.** `slug: dnd` →
database `dnd` in the shared store, container `lore-dnd`, port 9202+. ⚠ Two real gotchas:
(a) `SLUG_PATTERN = ^[a-z0-9][a-z0-9_]*$` — **hyphens are rejected outright** at config
load (an unescaped hyphenated identifier breaks SurrealQL parsing), so it is `dnd_2024`,
never `dnd-2024`; (b) `MEMORY.md` records that `lore-lore` currently runs a hand-rolled
`/source` mount and is **not restart-durable** — a D&D instance must not inherit that
pattern.

**Option B's deploy cost is where B gets expensive:** a separate MCP would need its own
image, its own Containerfile, its own deploy skill verbs, its own conformance guard, its own
`registration_sites.py`-derived member registration. All of that exists and is *paid for*
under option A.

---

## §9 — The multi-user proposal (`docs/design/2026-08-01-multi-user-lore-proposal.md`)

Status: **PROPOSAL, not ruled**; author lead (Opus), 2026-08-01 at `cdec4ca`. Mechanism, in
≤15 lines:

1. **Part 2 — per-deploy tool enable/disable.** A `tools:` section in `lore.yaml`; absent ⇒
   all built-ins, deny-by-default **within** the section; enabled set checked against a
   *declared universe*, not a bare `list[str]`.
2. It resolves finding **#296** (the hosted read-only posture that could not be defended
   inside FastMCP): a **never-registered** tool is absent from `tools/list` *and* uncallable
   via `tools/call`, enforced by the SDK's own bound handlers (`mcp` 1.27.2 —
   `tool_manager.py:41-43` / `:88-93`). No handler to shadow, no dispatch order to author.
3. ⚠ Honest bound the proposal states about itself: the SDK returns a generic
   `Unknown tool` error, so a disabled tool teaches the agent nothing about *why* — a
   Consumer-Law miss to accept deliberately or fix by rendering the disabled set.
4. **Part 1A — `principal` table** (named `principal`, never `user`, which collides with
   `DEFINE USER`/`DEFINE ACCESS`): `email` unique, `subject`, `display_name`,
   `status ∈ {active,suspended}`, `expires_at`, `role ∈ {member,admin}`.
5. **Part 1B — a `python -m loremaster.principals` CLI** in the image (no Containerfile
   change; strict dry-run unless `--execute`), gated behind first extracting
   `build_store(config)` to kill an existing 3-way store-construction duplication.
6. **Part 1C — per-user API keys**: adopt odoo-code's *validation* shape (SHA-512 cache
   keys, never store the raw secret); **reject its identity mint**, which collapses every
   keyholder to one `client_id`. Store hashed keys in `principal_key`.
7. **Parts 3A/3B — scoped memory**: an `option<record<principal>>` owner column makes
   system-wide memories naturally `owner IS NONE`. ⚠ Trap: `rebuild_embeddings` drops and
   replays the whole `memory` table from the SQLite ledger, so any column not carried in
   `_ledger_metadata`/`_replay_record` is **silently destroyed on every schema rebuild**.
8. Sequencing: Part 2 first (independent, unblocks packet 39), then `build_store`, 1A, 1B,
   1C, 3A/3B last.

**How it composes with a per-deploy allowlist and a D&D instance:**

- **The allowlist IS Part 2** — it is not a separate feature. The operator's decision to add
  a tool allowlist to `lore.yaml` is precisely this proposal's first and cheapest item, and
  it is the one item that is *independent* of the principal work.
- **Two axes, and the proposal already reconciles them:** Part 2 filters *what exists*
  (static, per-deploy); packet 39 §7 filters *what a principal sees of what exists*
  (dynamic, per-request) and explicitly assumes registration stays full. Resolution stated:
  the partition function's input becomes *the registered set*, and `all_registered_tools()`
  keeps meaning "everything actually registered". A D&D instance uses **only the static
  axis** — one `lore.yaml`, one tool set, no principals needed — so it can ship on Part 2
  alone with zero dependency on 1A/1C/3A.
- **The D&D instance is the second-best argument for Part 2 that exists** (the first being
  #296): a rules RAG that serves `lore_dead_code` and `lore_impact` is serving five tools
  that can only ever return empty on its corpus — a Consumer-Law problem the allowlist
  solves by construction.
- ⚠ Fork 3 in the proposal ("per-project DB or shared?" → recommends **shared** for
  principals) matters here: every table today lives in `lore_<slug>`, so a shared principal
  DB is a *new connection topology*. A D&D instance that later wants multi-user rides that
  same unresolved fork.

---

## §10 — The minimal tool set for a rules corpus

**10 of the 15 tools are corpus-agnostic; 5 are Python-only and can never serve a rules
corpus.**

| Tool | Verdict | Why |
|---|---|---|
| `lore_search` | **KEEP** — corpus-agnostic | Hybrid vector+BM25 over `chunk`; takes `tier`, `path`, `detail_level`, `budget`. Doc tiers already prove it. |
| `lore_read` | **KEEP** — corpus-agnostic | Store-backed hash-verified span read by `(tier, path, lines)`. |
| `lore_index` | **KEEP** — corpus-agnostic | Freshness/health + reconcile sweep. |
| `lore_diff` | **KEEP** — corpus-agnostic | File-level snapshot diffs. |
| `lore_remember` / `lore_recall` | **KEEP** — corpus-agnostic | Free-text durable memory. Directly useful ("this table's house ruling"). |
| `lore_findings` | **OPTIONAL** — agnostic but fleet-flavoured | `area`/`category` are free strings; the *examples* are lore tools. |
| `lore_tasks` / `lore_claim_task` / `lore_comms` | **DROP for D&D** — agnostic but purpose-irrelevant | Multi-agent build-fleet orchestration. Large served-prose footprint. |
| `lore_get_symbol` | **DROP** — CODE-ONLY | Resolves a **Python dotted name** to a stored def; scoped to class/method/function chunks. |
| `lore_verify` | **DROP** — CODE-ONLY | Verifies a Python symbol/signature/location claim; same resolution path as `lore_get_symbol`. |
| `lore_impact` | **DROP** — CODE-ONLY | Reads `code_node`/`refers`; consumers + covering tests + astroid-bounded liveness. |
| `lore_map` | **DROP** — CODE-ONLY | PageRank over the Python import/call graph, rendering **modules and symbols**. |
| `lore_dead_code` | **DROP** — CODE-ONLY | Liveness heuristic over the same graph. |

**Minimal viable D&D set (6):** `lore_search`, `lore_read`, `lore_index`, `lore_remember`,
`lore_recall`, `lore_diff` — plus the domain tools (`get_spell`, …) that do not exist yet.
A comfortable set adds `lore_findings` (7).

⚠ **The five code-only tools do not merely under-serve a rules corpus — they would each
return an honest-looking EMPTY.** `lore_map` on a corpus with zero `.py` files renders an
empty module list; `lore_impact` renders `dead (heuristic)` for anything asked. Under the
Consumer Law that is a **false clear wearing an honest render**: a consumer acting on
"`lore_impact` says nothing references this" cannot tell "no references" from "this tool
structurally cannot see your corpus." **This is the strongest single technical argument for
the allowlist, and I recommend it be written into the allowlist's rationale rather than
treated as a tidiness feature.**

---

## §11 — Verdict table (the deliverable, one row per component)

| # | Component | Verdict | The exact work, if any |
|---|---|---|---|
| 1 | `lorerunes` | **GENERIC** | none |
| 1 | `lorescribe` (member) | **GENERIC** | none |
| 1 | `loresigil` (member) | **GENERIC** | none |
| 1 | `loremaster` (member) | **MIXED** | see rows 4–7 |
| 2 | `ChunkerRegistry` + `MarkdownChunker` + `Chunk`/`ChunkContext` | **GENERIC** | none. Optional: a stat-block-aware `Chunker` subclass. |
| 2 | non-code tier ingest path | **GENERIC** | none — three vendor doc tiers run on it in `lore.yaml` today |
| 3 | `Embedder` / `TEIEmbedder` / `ResilientEmbedder` / `VoyageTokenCounter` | **GENERIC** | none. Shared external TEI endpoint; re-measure if `voyage-context` is considered for prose. |
| 4 | `RootConfig` tier system (`live`/`static`, `local_directory`) | **GENERIC** | none — a D&D tier is declarable TODAY, no code |
| 4 | watcher + reconcile | **GENERIC** | none |
| 4 | **entity-extraction step** | **CODE-SPECIFIC GAP** | a 4th ingest fragment beside `_graph_fragment`; **no extension seam exists for it** — this is the twelfth seam |
| 5 | `store/_txn.py` driver (`execute_transaction`, `retry_on_conflict`, `compose`) | **GENERIC** | none — the highest-value reusable asset |
| 5 | `surreal_schema.py` per-domain DDL slices | **GENERIC-WITH-WORK** | `_SPELL_FIELD_SPECS` + `_spell_statements()` + `generate_spell_ddl()` + an owner class; follow `floor_*`/`lease` (`7acbef4`) |
| 5 | `SurrealStore` public surface | **GENERIC-WITH-WORK** | no arbitrary-query verb — a domain store owns its own connection, ledger-style |
| 5 | `code_node`/`name`/`refers` graph + `graph.py`/`graph_surreal.py` | **CODE-SPECIFIC** | unusable. A spell graph is a NEW relation table (precedents: `blocks`/`briefed`/`answers_to`) |
| 5 | `chunk.metadata` (`object FLEXIBLE`) | **GENERIC** | carries arbitrary entity data today, but is **not** a filter key |
| 6 | `_register_tools` (15 hardcoded decorators) | **GENERIC-WITH-WORK** | a config-consulting `_tool` indirection at 15 sites (one decision point) |
| 6 | `_INSTRUCTIONS` | **STATIC — must become derived** | it and every tool `description` become functions of the enabled set; the dead-name pin compares against the **runtime** set |
| 6 | exact-set + dead-name + instructions pins | **GENERIC-WITH-WORK** | parametrise over configs, both directions; ~9 pins index `tools[name]` and would `KeyError` |
| 6 | `extension.py` (11 seams) + `_register_extension_tools` | **GENERIC, BUT UNWIRED** | **0 production call sites of `register_extension`.** Needs a config→extension discovery step that does not exist. |
| 7 | memory / findings / tasks / comms / diff | **GENERIC** (agnostic) | none — but tasks/comms are purpose-irrelevant for D&D; allowlist them off |
| 8 | lore-deploy skill + Containerfile | **GENERIC** | none — N-containers-on-one-image is the existing model; slug must be `dnd_2024` (no hyphens) |
| 9 | multi-user proposal Part 2 | **IS the allowlist** | see §9 |

---

## §12 — Flags for the operator (scope law: raising, not deciding)

1. **The A/B decision turns on one unwired seam.** Option A (extend lore) is dramatically
   cheaper on every axis I measured — chunking, embedding, tiers, deploy, store driver,
   search — **except** that the mechanism designed to make it clean (the extension
   framework) has never run in production. Option B (separate MCP importing
   `lorescribe`/`loresigil`/`lorerunes`) buys isolation at the cost of re-building
   loremaster's index pipeline, watcher, store schema, MCP server and deploy skill. **A
   third shape exists and I recommend the operator consider it explicitly: option A with
   the extension framework WIRED FIRST** — i.e. spend one small packet making
   `extensions:` actually instantiate an `Extension`, then build D&D as the first real
   extension. That converts a 340-test-backed, zero-production-mileage framework into a
   proven one, and it is the thing lore's own design docs say the framework is for.
2. **The entity-extraction seam does not exist in either option.** No extension seam
   contributes a write-fragment to the per-file index transaction. This is the single
   largest unbudgeted item in this survey and it needs a design decision, not a build brief.
3. **The five code-only tools return honest-looking EMPTY on a rules corpus** (§10). I read
   this as a Consumer-Law/false-clear problem, not a tidiness one. It strengthens the
   allowlist's rationale materially and I flag it because the allowlist could otherwise ship
   framed as ergonomics.
4. **`_INSTRUCTIONS` and every tool description must become derived** (§6.5 item 4). This is
   the allowlist's true cost and it is unavoidable — the dead-name pin is correct and is
   catching a genuine over-claim.
5. **The extension-tool name-collision guard checks the registered set, not the declared
   universe** — with an allowlist, disabling `lore_search` lets an extension claim that
   name. Already flagged in the multi-user proposal; I confirmed it in the code.
6. **`chunk.metadata` is not a filter key.** `CHUNK_FILTER_KEYS` is derived to hold only
   plain-`string` non-fulltext columns, so metadata-stamped spell attributes are carried but
   not filterable. Extension seam 8 (`payload_indexes`) is the designed answer and is
   unexercised.
7. **Slug hygiene:** `SLUG_PATTERN` rejects hyphens at config load. `dnd_2024`, never
   `dnd-2024`.
8. **Do not inherit `lore-lore`'s deployment shape.** `MEMORY.md` records it runs a
   hand-rolled `/source` mount and is not restart-durable pending #165/#166.
9. **`voyage-context` guidance does not transfer.** The sample's "contextualization does not
   out-perform flat chunk embedding" finding is scoped to AST-chunked *code*; a rules-prose
   corpus is a different measurement, un-taken.
10. **Not verified by me (bounds on this report):** I ran no tests and started no container.
    Every claim is a source read at `a049118` plus one `lore_impact` verdict corroborated by
    grep. The `register_extension` dead verdict is heuristic-plus-grep — strong, but not a
    runtime observation. If a packet is planned on it, confirm at runtime that no
    dynamic/framework-mediated path registers an extension.
