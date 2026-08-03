# Wave-D architecture — the D&D extension track, packet by packet

**Status: RULED (operator, 2026-08-02/03).** The architecture for wave D's packets,
grounded in the extension-API scout's exact-signature verification at `2ce7eee` and
reshaped by the TRANSMUTE ruling (below). Companion docs: the scraper-side spec at
`dndlorescraper:SPEC-transmute.md` (self-contained for that repo) · the picks/rulings in
`2026-08-02-dnd-graph-scope-rulings.md` · multi-user proposal `2026-08-01-…` (Parts 1A/1B/
1C/2) · dnd proposal `2026-08-01-…`. Packet 50 consumes this doc as its ruled design; the
contract-adversary still attacks the contracts built from it (standing law).

## 1. The two rulings that reshape the track

**R-A — THE TRANSMUTE PIVOT.** The corpus splits into a prose tier (`output/`, unchanged,
vector search) and a machine tier (`output-graph/**/*.jsonl`) produced by an LLM
transcriber in the scraper repo under deterministic word-for-word fidelity gates,
HTML-first (recovering the destroyed cross-reference links). Full spec:
`dndlorescraper:SPEC-transmute.md`. Consequences here: the per-dialect grammar work is
GONE from lore; the 52-series collapses to two consumer packets; a new row 55 tracks the
scraper build; entities arrive in their OWN file tree, which reframes packet 47 (§4).

**R-B — AUTH TO THE END.** The operator soaks a working LAN-local instance before any
friend touches it. Execution order: **45 → 46 → 47 → 55 (∥-safe) → 50 → 51 → 52a → 52b →
53 → 54 (LOCAL deploy, no auth) → 48 → 49 → 39 → 07 → 07a → 56 (GO-LIVE)**. Packet 39's
"REQUIRED before off-LAN" holds — off-LAN happens only at 56; 07/07a's outside-users
rationale gates 56, not the operator's own soak.

## 2. Packet 45 — tool allowlist (= multi-user proposal §Part 2)

Architecture already in the proposal; the deltas that bind the build:

- Config: a `tools:` section on `LoreConfig` (config.py `_StrictModel` idiom), enabled
  set validated against the declared universe (`_ALL_BUILTIN_TOOL_NAMES`,
  test_mcp_server.py:1034 — promote it into production code; a test-only universe cannot
  gate a boot). Default: absent section ⇒ all built-ins; deny-by-default within.
- The `_tool` config-consulting indirection replaces `mcp.tool` at the 15 decorator
  sites — one decision point (the `TracingFastMCP` docstring's own argument).
- Served prose becomes f(enabled set): `_INSTRUCTIONS` (server.py:1472) and tool
  descriptions derive from the registered set; the every-lore-token pin
  (test_mcp_server.py:1122) is satisfied, not waived.
- **Fix here: the collision guard** at `_register_extension_tools` (server.py:10302)
  checks `mcp._tool_manager.get_tool(...)` — the REGISTERED set; it must check the
  declared universe, else a disabled built-in's name is claimable by an extension.

## 3. Packet 46 — extension discovery

- A STATIC registry `EXTENSION_REGISTRY: dict[str, type[Extension]]` in loremaster
  (entry-points deferred until an out-of-repo extension exists — named trigger).
- **The config surface already exists**: `LoreConfig.extensions: dict[str, dict]`
  (config.py:633, the opaque pass-through). Discovery: each key ⇒ registry lookup ⇒
  instantiate ⇒ `register_extension` (server.py:549 — chainable; seam-7 slice validation
  and the nit-1 chunker guard already inside it). Unknown key ⇒ loud boot failure naming
  the known set.
- **Placement: a helper called from `LoreServer.__init__`** — the four production
  construction sites (`from_config` server.py:384 · index/cli.py:105 · scout.py:769 ·
  comms_consumer_eval.py:804) all pass through `__init__`; hooking `from_config` alone
  would blind the indexer CLI and scout.
- Rider from packet 39's R14, paid here (one line): `_register_extension_tools` passes
  `annotations=ToolAnnotations(readOnlyHint=False)` on `mcp.add_tool` (today it passes
  none while all 15 built-ins do; server.py:10309).

## 4. Packet 47 — the twelfth seam, reframed: a per-file ENTITY-INGESTOR claim

Pre-transmute, the seam had to extract entities from the SAME file as chunks. Post-R-A,
entities arrive in their own `.jsonl` tree — so the seam is a per-file CLAIM over a
normal lore static tier, and **the entire file lifecycle (manifest rows, watcher,
reconcile, purge) is reused, not rebuilt**:

- New `Extension` seams (the framework's 12th):
  `claims(tier: str, path: str) -> bool` ·
  `entity_fragment(tier: str, path: str, text: str, ctx: ExtensionContext) -> TxnFragment | None` ·
  `entity_purge_fragment(tier: str, path: str) -> TxnFragment | None` — pure builders on
  the `SurrealCodeGraph` precedent (`build_file_graph_fragment` graph_surreal.py:817 /
  `purge_file_fragment` :885; own connection; injected optional collaborator like
  `Indexer(code_graph=…)` indexer.py:391).
- Composition point: `Indexer._compose_file_fragments` (indexer.py:653) — the extension
  fragment joins replace_file/file_text/manifest/graph fragments in ONE transaction per
  file via `store.apply` (surreal.py:1026 → `compose` + `execute_transaction`). A claimed
  file skips chunking/embedding (no chunks, manifest row with n_chunks=0) — the machine
  tier is never embedded.
- All FOUR purge sites gain the extension purge fragment: indexer per-file (:627) ·
  `_commit_batch_file` (:1638) · watcher `_purge` (watcher.py:1035) · reconcile
  (reconcile.py:267).
- Param prefixes are namespaced per extension (`xt_<name>_`) and claimed in `compose`'s
  collision registry beside `st_/ft_/mf_/gr_`.
- **Edges are two-phase** (the ENFORCED ordering problem): phase 1 = per-file NODE
  fragments, atomic with the file; phase 2 = an end-of-sweep hook (new seam or
  `on_startup`-adjacent) resolving edges per `source_book` scope — purge-then-RELATE in
  one transaction; the machine tier's `(target_kind, target_name/slug)` makes this a
  LOOKUP through the supersession function (§7), not a parse.
- **Ordering pin the 47 design must carry:** the extension's domain store `ensure_ready`
  (DDL) precedes any fragment build — it rides the write-stack readied list
  (server.py:7627–7788, `write_stack_readied`) like `code_graph.ensure_ready`
  (:7664), NOT the startup hook at :7926 (which runs after the Indexer is constructed).
- 47 remains a DESIGN packet under roster law; this section is its ruled input, its
  adversary still runs.

## 5. Packets 48/49/39 — the identity tail (unchanged in content, moved in time)

48 (build_store extraction FIRST, then `principal` per multi-user §1A) → 49 (CLI §1B +
keys §1C, packet-39 §4 mint, revocation-beats-cache) → 39 build (contract re-cut against
principals + FRESH adversary — standing law). All AFTER the local soak; nothing in 45–54
depends on them.

## 6. Packet 50 — contract-prep (shrunk by ruling)

Turns THIS doc + the transmute spec + the rulings doc into the 51/52/53 contracts; runs
the contract-adversary; rules the leftover forks at kickoff (proposal §9 forks 3/5/7/8 +
D3 + the edition-ranking read-the-2024-rules rider — a SERVING policy, lore-side). The
resolver work that survives in lore (52b) is scoped here: the normalization stack applies
to CLEAN machine-tier strings, not prose.

## 7. Packets 51 / 52a / 52b / 53 — the dnd extension

- **51 schema + DnDStore**: table-per-kind from the transmute record enum; every
  relation ENFORCED + UNIQUE(in,out) + `source_book` scope from birth; scalars as
  indexed FIELDS (element-path `.*` for arrays); composite ids `[source_book, slug]`;
  slice per the floor/lease recipe (spec tuples → emitters → `generate_dnd_ddl()`; owner
  clones `FloorCalibrationStore` — own connection, `execute_transaction`, O3: this slice
  only). Graph-probe scripts lift verbatim into `scripts/`.
- **52a machine-tier reader**: pydantic models MIRRORING `transmute/records.py` (the
  transmute spec pins that module as the extraction point for a future shared package);
  JSONL → validated records → node fragments via the 47 seam; tombstone records ingest
  as named bounds (renderable), never dropped; ingest-side spot-checks re-run the
  fidelity/count gates cheaply.
- **52b edge resolution + ingest — THE SUPERSESSION FUNCTION** (operator: cross-edition
  references "MUST be correct"): one pure, total resolver
  `resolve(kind, slug) -> NodeRef | Dangling` — prefer the 5.5/Core row → the 59-row
  2014→2024 rename-alias table (itself a machine-tier record family) → the 5.0 row →
  dangling tombstone with href preserved. **The reference's own edition is deliberately
  ignored** — that is what makes wrong-edition targeting unrepresentable rather than
  caught. Link-provenance edges resolve directly; name-provenance edges normalize first
  (the measured 8-rule stack, now over clean strings); prose-provenance edges gated per
  family. Instruments: a fixture leg per branch · the 19 D2 same-name spell pairs
  (5.0 link → 5.5 row) · the 59 rename rows · a per-item dangling audit at ingest.
- **53 domain tools**: per the client-side-composition ruling — rules retrieval + general
  graph FILTERS as declarative `ToolSpec`s (extension.py:80 — name/handler/description/
  input_schema/output_schema; the wrapper republishes the handler's real signature,
  server.py:10321): `dnd_get_spell(name, book?)` · `dnd_spells(…)` · `dnd_monsters(…)` ·
  `dnd_get_entity(name, kind?)`. Renders name book/edition + the 2014 base-rules bound;
  both trust legs per surface; acceptance = the Moon-Druid trace end-to-end incl. the
  retrieval-ranking leg (XGtE's 2014 pointer must not outrank the PHB rules).

## 8. Packet 55 — scraper transmute build (executes in dndlorescraper)

Tracked in lore's INDEX because 52a/52b's entry checks name its outputs (the machine
tier + green gate receipts) as preconditions. The work follows
`dndlorescraper:SPEC-transmute.md` in that repo — HTML cache change + one full re-crawl,
the one-page link probe FIRST, then the transmute pipeline on the transcribe-craig SDK
pattern (Max subscription; refuse-if-API-key-set). ∥-safe with 45–47.

## 9. Packets 54 / 56 — local deploy, then go-live

- **54 LOCAL deploy** (deps: 53 only): slug `dnd`, DB `dnd`, existing image, shared TEI
  embedder; TWO static roots, no new provider (`provider:` is declared-but-unread;
  `_build_source_providers` server.py:8057 gives every static root the built-in
  local_directory): prose tier at `dndlorescraper/output` (`**/*.md`), machine tier at
  `output-graph` (`**/*.jsonl`, claimed by the extension, never chunked). Instance
  lore.yaml carries the ruled allowlist (rulings doc §4). Always-on quadlet unit
  (surreal-stores precedent). **Access: LAN-local MCP connection; no auth; operator
  soak.**
- **56 GO-LIVE** (deps: 54 soak, 49, 39, 07a): auth wired (claude.ai principals, keys
  minted by 49); hades SNI/Caddy route (operator-side); the **#236/#138 consult**
  (standing first-non-local-exposure trigger); `lore_findings` write-gating note; smoke =
  register a real principal → mint key → run the Moon-Druid acceptance through the
  claude.ai path → revoked key denied live.

## 10. Bounds

Signature citations verified at `2ce7eee` by the extension-API scout (its bounds apply:
the 15 tool bodies, `AppContext` internals, and the batch machinery beyond
`_commit_batch_file` were not read). The transmute record shape is owned by the scraper
spec; if it drifts, 52a's mirrored models redden — that coupling is deliberate and the
future shared-package extraction is named in both docs.
