# lore v2 — DeadReckoning+: A Code-Intelligence Platform (not just an MCP)

## Context

Large repos break AI assistants: context fills, recall degrades, APIs get hallucinated.
lore v0.3 fights this (per-project RAG, live watcher, astroid code graph, project memory)
but has structural ceilings: **three stores** (Qdrant + SQLite + Kùzu) needing cross-store
healing, **vector-only search**, **no orientation primitive**, **no version history**,
**no enrichment**, **no UI**, and full-source result bodies.

Goal: **DeadReckoning+** — everything dead-reckoning does (one-store hybrid search, graph
enrichment, version snapshots + auto-diff, LLM self-enrichment, agentic action loops, UI,
observability, resumable ingestion) PLUS everything lore does well (live freshness, exact
symbols, memory, extensibility, self-healing, multi-language chunking, dead-code analysis),
targeting Claude agents (Opus 4.8, Sonnet 5, Fable/Mythos 5): least tokens, most preserved
context, large-project work without hallucination/degradation.

**Operator decisions (2026-07-01):** best-final-product; extensibility survives (Odoo later);
**full SurrealDB unification**; embedders swappable (TEI voyage-4-nano reference, cloud
voyage-4-large / voyage-context-4); **anti-hallucination prime**; **client/server split
required** (cloud-hosted MCP for agents worldwide; scout watcher/indexer co-located with a
git-synced repo); **enrichment LLM configurable** (Claude API AND local backends);
**actions = findings table + issue-tracker escalation (both)**; **web UI with graph viz +
Agent-SDK chat**; **versioning full and first-class in v1.0**.

**Key research inputs:** dead-reckoning (SurrealDB one-query hybrid `search::rrf([$vs,$ft],k,60)`
+ graph enrichment cap 10; version snapshots with per-node diff_status; generate_docstring →
suggested_docstring stored AND BM25-indexed; raise_issue closes discover→act; Streamlit graph
viz + chat; checkpointed resumable ingestion). SurrealDB 3.x stable, RRF/HNSW/BM25 native.
Spectron memory (supersede-don't-delete, provenance, trust, uncertainty). Sonnet 5 (1M ctx,
new tokenizer ~30% more tokens/same text — compactness matters more; context rot means
precision matters at any window). voyage-context-4 (contextualized chunk embeddings, one
vector/chunk encoding whole-doc context, Matryoshka 2048→256, dedicated endpoint). Aider
repo-map (PageRank, token-budgeted). mcp-builder skill (schemas cost tokens every request;
teaching errors; eval harness). Note: lore's manifest already IS dead-reckoning's checkpoint
system — per-file states make ingestion resumable today; parity, not new work.

---

## 0. Platform shape (the "+" view)

```
                    ┌────────────────────────────────────────────┐
 repo host          │  SurrealDB (one ACID store)                │       cloud
┌─────────────┐     │  chunks·vectors·BM25·graph·manifest·       │  ┌──────────────┐
│ scout       │────▶│  file_text·snapshots·memory·findings·      │◀─│ mcp (N reps) │◀── agents
│ watch/sync  │     │  traces·commands·meta                      │  │ 12 MCP tools │    worldwide
│ chunk/graph │     └────────────────────────────────────────────┘  │ + /ui app    │◀── humans
│ embed/enrich│  (single-node "all" mode: embedded, one process)    └──────────────┘
└─────────────┘                                                    chat = Claude Agent SDK
                                                                   wired to lore's own MCP
```

Five layers: **store** (SurrealDB) · **ingest** (scout: watch/git-sync → chunk → graph →
embed → snapshot → enrich) · **serve** (MCP tools) · **act** (findings → issue escalation) ·
**observe/show** (trace table → UI: graph viz + chat + dashboards).

## 1. Storage architecture (full SurrealDB unification)

**Two-role decomposition (client/server split).** The write/read seam, store as the only coupling:
- **`scout` (write side, runs WHERE THE REPO LIVES** — forced: astroid + chunking need the
  tree on disk): watcher + reconcile + chunkers + graph derivation + document-side embedding
  + snapshot stamping + enrichment worker + transactional writes. `python -m loremaster.scout`,
  no FastMCP import.
- **`mcp` (read side, cloud-hostable, stateless → N replicas)**: the MCP tools + the UI app
  + query-side embedding + memory writes (ledger on MCP host) + trace writes.
- **`all` (single-node)**: both in one process, today's ergonomics, embedded SurrealDB.

**Topology (AMENDED by P0 spikes, 2026-07-02): SERVER-MODE EVERYWHERE.** Four independent
spike findings killed embedded surrealkv as a default: (1) the Python SDK embeds a
**2.3.10** engine — no `search::rrf`, older DDL dialect (`SEARCH ANALYZER`/`type::thing`);
(2) raw concurrent access **Rust-panics and core-dumps** (FastMCP serves concurrent
sessions; serialized-actor access passes but is a permanent tax); (3) ingest is **14×
slower** than server mode (28 vs 395 rows/s @1024-dim — 100k chunks ≈ 1h vs ~5min);
(4) surrealkv write amplification (~500× at per-row writes) + a single-process lock hazard
(concurrent open ⇒ deserialization errors). Every mode talks `ws://` to a **SurrealDB
≥3.1.x server on RocksDB** (floor raised from 3.0.5 → 3.1.x per operator directive
2026-07-02, matching Spectron's runtime floor so a self-hosted Spectron memory backend can
share lore's own SurrealDB server; retool verifies the dialect holds on 3.1 — detected via
HTTP `/version`): single-node = a local surreal
container (pod sidecar — the same operational shape as today's shared Qdrant pod, already
managed by lore-deploy); split = the same server placed near the mcp replicas, per-role
credentials + TLS. One engine dialect (3.x: `FULLTEXT ANALYZER`, `type::record`, native
`search::rrf` with INLINE subqueries — LET-variable args return None on 3.0.5 —,
`LIVE SELECT` after `DEFINE TABLE`). `SurrealConfig {url, ns, db, creds_env}`. The Qdrant
pod + its healing machinery still get deleted; spike receipts in
scratchpad/spikes/RESULTS.md.

**Reference split deployment (operator's example):** a pod/workstation keeps a synced git
repo and runs scout; SurrealDB server + stateless mcp replicas co-located with the store
serve remote agents worldwide (streamable-HTTP + Bearer + TLS). Git-sync ingestion: pulls
touch hundreds of files — watcher coalescing/debounce + reconcile absorb bulk; documented
`git_sync` pattern (sidecar pulls → post-sync reconcile command row as the deterministic
alternative to inotify storms; `.git/` pruned at watch-scheduling per bc752e7). Remote
freshness honesty: `lore_index` reports last-sync/last-sweep/snapshot ages — wait_for_fresh
covers scout→store lag, not agent→git lag.

**Schema** (SCHEMAFULL; DDL generated from config by `store/surreal_schema.py`; dim never
hardcoded):
- `chunk` — existing uuid5 point-ids survive. Fields: tier, file_path, chunk_type, identity,
  sub_ordinal, content_hash, mtime_ns, line_start/end, source_text, **ident_text** (derived:
  identity+bare name+file stem), **llm_summary** (option; enrichment, provenance-stamped),
  metadata (FLEXIBLE), embedding. Indexes: HNSW (COSINE, CONCURRENTLY) + BM25 SEARCH on
  ident_text (2×), source_text, **llm_summary** (the dead-reckoning suggested_docstring
  trick: generated docs improve keyword recall) + (tier,file_path).
- Analyzer: `DEFINE ANALYZER code_ident TOKENIZERS blank,class,camel,punct FILTERS lowercase,ascii`
  (camelCase/snake_case/digit-boundary; spike S3).
- **Graph (AMENDED: name-node indirection, native RELATE in v1.0)**: the referencing file
  can never know the target code_node's id (it's uuid5 over the DEFINING file's path) — so
  the NAME becomes the endpoint: `name:⟨dst-string⟩` nodes (UPSERTed idempotently in the
  same per-file txn — zero dangling edges ever), `refers` RELATION code_node→name (kind,
  resolved, src_tier, src_file_path + purge index), `answers_to` RELATION code_node→name
  (each node answers to its FQN name and its bare name — FQN-collision fan-out preserved).
  Reverse traversal is native from day one: `->answers_to->name<-refers<-code_node`.
  Resolved-vs-bare matching semantics identical to today (resolved dst=FQN lands only on
  FQN names; bare fallback on bare names). Astroid derivation + keep/drop rule move
  unchanged. **Fallback behind the same CodeGraph API**: plain ref-records (1:1 port) if
  RELATE traversal/purge perf at ~50k edges disappoints — measured in P4's contract tests
  against the 3.0.5 server. One-query graph-enriched search rides this in v1.0/v1.1.
  Per-file txn also asserts snapshot isolation for concurrent readers (P2 contract test:
  reader mid-txn sees old state, never a gap).
- `file` = manifest (composite id `file:[tier,path]`, states, **Manifest API preserved 1:1**);
  `file_text` (full text + sha512, same per-file txn) — split-mode `lore_read` serves
  store-backed spans everywhere, hash-verified; `meta` = fingerprint/stamps/rebuild status.
- **`snapshot` + `snapshot_entry` (VERSIONING, v1.0)**: snapshot stamped on every completed
  sweep/git-sync (id, created_at, git_ref+branch when repo is git, counts);
  snapshot_entry = one row per file (file_path, sha512, chunk_hashes: array<{identity,hash}>)
  → file-level diff from sha512 compare, **function-level diff** from chunk-hash compare.
  diff_status computed on demand between any two snapshots (or ref/date → nearest snapshot).
- **`finding` (ACTIONS)**: kind (dead_code|undocumented|drift|**friction**|custom), target
  (qualified_name + citation), evidence, status (open|acknowledged|resolved|wontfix),
  created_by (sweep|agent|**trace_monitor**), issue_url (option). Sweep auto-population opt-in
  per kind in lore.yaml. (kind=friction AMENDED 2026-07-03 — see "Friction reporting" below.)
- **`trace` (OBSERVABILITY)**: tool, params_hash, hit_count, latency_ms, session, ts —
  written async by mcp role; aggregates in lore_index + UI dashboards ("which queries return
  nothing" is the retrieval-improvement loop).
- `memory` — Spectron-informed: note_text, refs, kind (fact|decision|gotcha|uncertainty),
  trust (authoritative|experiential), embedding, created_at, valid_until, superseded_by,
  provenance. Hybrid recall filtered to live rows. **JSONL write-through ledger stays**
  (memories are the only non-derivable data).
- **`task` (ORCHESTRATION LEDGER, added 2026-07-03)**: the durable, project-scoped,
  fleet-visible multi-agent work ledger — the gap dead-reckoning and the harness both leave
  open (the harness todo is session-PRIVATE; no other agent/session sees it). Fields: subject,
  description, status (open|claimed|in_progress|done|blocked|wontfix), owner (agent/session id),
  claimed_at, blocked_by (deps), provenance (who created/changed), superseded_by (plan/decision
  revisions reuse the memory supersession model — a task's rationale can be superseded without
  deleting history). Memory-shaped (durable, provenanced, supersession-based, fleet-shared) →
  built in P7 on the SAME machinery as `memory`. THE LOAD-BEARING CORRECTNESS BIT: an atomic
  CLAIM (compare-and-set — claim only if still unclaimed) via a single-txn optimistic-concurrency
  guard reusing store/_txn.py's "can be retried" conflict-retry, so two concurrent agents can
  never double-claim one task. Boundary (same litmus as memory): holds PROJECT-shared
  orchestration state any agent on this project needs; the harness keeps agent-private ephemeral
  todos. Durable plan/architecture DECISIONS ride the existing `memory` kind=decision (surfaced
  in lore_map headers) — the `task` table is specifically the claim/assignment/status ledger.
- `command` — control channel: MCP inserts (reconcile, post-sync, enrich-now); scout
  subscribes via **LIVE SELECT** (poll fallback; spike S11).

**Atomicity win**: one BEGIN/COMMIT per file reindex (upsert chunks, delete stale
chunks+refs+nodes, insert nodes+refs, upsert file_text + manifest row). Embedding stays
outside the txn; failed embed writes only a small `state:'failed'` txn.

**Extension seams**: neutral `Candidate {key, score, payload, origin}` replaces leaked
ScoredPoint (seams 4/5); seam 8 → `FieldIndexSpec {field_name, kind: keyword|bool|fulltext}`;
other 9 seams unchanged (breaking OK — no extensions shipped).

**Self-healing shrinks to one path**: disk-vs-manifest reconcile + fingerprint rebuild +
ledger backfill + ONE resilient-open (corrupt dir → move aside, recreate, eager rebuild +
ledger restore). Keep **SchemaRebuildingError** (raise, never `[]`, during rebuilds).

**Survives untouched**: all lorescribe; loresigil (+ NEW voyage_context.py, optional
document-grouped `supports_contextualized` capability); auth, logging, read_file guards,
symbols, watcher (+ scheduling prune), reconcile semantics, records point-ids, ledger,
fingerprint logic, astroid derivation (+ cache warming).
**Deleted**: store/qdrant.py, index/kuzu_resilient.py, index/sqlite_resilient.py, deps
qdrant-client + kuzu. **Data migration: none** — indexes rebuild from source; memories via
the ledger.

## 2. Enrichment loop (NEW package: `loresage`)

The dead-reckoning generate_docstring pattern, generalized and made retrieval-serving:
- **`loresage`** = LLM-backend abstraction mirroring loresigil's embedder ABC: `ClaudeBackend`
  (anthropic SDK; default haiku-tier, model per lore.yaml) and `LocalBackend`
  (OpenAI-compatible/Ollama endpoint). Config: `enrichment: {backend, model, max_per_sweep,
  budget}`.
- **Scout-side background worker**: after a sweep, finds symbols lacking docstrings (chunk
  metadata knows) → LLM writes a 1–3 line summary → stored as `chunk.llm_summary`
  (provenance-stamped: model + ts), BM25-indexed → **retrieval improves for undocumented
  code**. Rate-limited, resumable (it's just rows), opt-in per project.
- **Anti-hallucination discipline**: generated text is ALWAYS rendered marked `(ai summary)`
  and never inside source fences; it can also seed `undocumented` findings (below) so the
  fix lands in the code, where it belongs. Vector-side re-embedding with summaries is v1.2+
  (schema-fingerprint implications; BM25-only first).

## 3. Actions (findings + escalation)

- Sweep detectors (opt-in per kind): dead_code (existing analysis), undocumented (chunk
  metadata), drift (symbol changed while memories/findings reference it — snapshot diff
  makes this cheap). Agents can also file findings explicitly.
- `lore_findings` tool: query by kind/status; act with `action: acknowledge|resolve|wontfix|
  raise_issue`. `raise_issue` escalates via `gh` CLI or Gitea API (config:
  `actions: {tracker: github|gitea, repo, …}`), stamps issue_url back on the finding —
  dead-reckoning's discover→act loop, with a persistent audit trail it lacked.

**Friction reporting (AMENDED 2026-07-03, operator-directed; lands with P8's tool surface).
WHY: good LLMs MASK MCP defects — an agent hits a bad result, silently works around it
(grep instead of search, param-thrash retries, tool abandonment), and the defect survives
forever while every future session re-pays the workaround in tokens and drift. The receipts
from our own dogfooding: the team-lead barely used lore during the P5 build — and the
freshness distrust behind that was later MEASURED FALSE (v0.3's watcher had kept up with
the session's churn; a 90-minute-old class resolved perfectly; the agent simply never spent
the one cheap index_status call that would have dissolved the doubt). UNVERIFIED DISTRUST
is itself a first-class friction category — the fix is affordance (v2's per-result
staleness flags push freshness into every answer instead of waiting to be asked) plus
doctrine, not backend code. The other half was real: structural seam-sweep questions
(call-site maps, covering tests) that v0.3's flat search can't answer — the v2
lore_map/lore_impact/tests_for gap. And
every historical v0.3 defect (silent-empty graph reads during rebuilds, the baked-image
stale-code gotcha, the pre-v0.3.4 embed failure) was hit-and-masked by agents before a human
noticed. Traces capture SYMPTOMS; only the agent knows intent, why the result was unusable,
and the workaround taken — that narrative is the maintainer's signal and it currently
evaporates at session end.** Design (rides existing machinery, no new tool, no new table):
- **Vehicle**: `finding` with `kind=friction` via the existing action surface —
  `lore_findings(action="report", kind="friction", …)`. Report shape (~5 fields, ≲100
  tokens, fire-and-forget, NEVER blocks the task): tool name; intent (one line); what
  happened (zero_hits|error|wrong_result|too_stale|other); workaround taken
  (grep|retried_variants|other_tool|gave_up|none); params_hash (joins to the trace for
  reproduction + prevalence).
- **Doctrine line (the load-bearing part — one sentence in P8's `instructions` block)**:
  "If a tool result forces a workaround, file a friction finding FIRST (one call), then work
  around." Without the explicit command, trained-in helpfulness defaults to silent masking.
- **Server-side backstop** (`created_by=trace_monitor`, P9/P10 with the trace aggregates):
  auto-file candidate friction findings from trace patterns agents won't report — the same
  params_hash re-called with rapid variations (retry storms) and zero-hit queries followed
  by tool abandonment. Agent narratives + auto candidates feed ONE queue.
- **Maintainer loop**: the P10 dashboard's findings queue (generalizing the planned
  "zero-hit queries" panel) + `raise_issue` escalation — friction reports land in the
  tracker with trace joins attached. Success metric: defects get FIXED from reports faster
  than agents can re-discover them; the report volume itself trends toward zero.

## 4. UI (graph viz + chat)

Served by the mcp role on `/ui` (same ASGI app, path-separated, stateless — replicas keep
working; Bearer/session auth):
- **Graph explorer**: dependency/impact visualization over code_node+ref (module collapse,
  reverse-edge focus, dead-code and diff_status overlays, snapshot slider).
- **Search + symbol views**: the same store queries the tools use — humans see exactly what
  agents see (citations, staleness flags, enrichment marks).
- **Chat**: **Claude Agent SDK** session server-side, wired to *this project's own lore MCP*
  (dogfooding the exact tool surface; ANTHROPIC_API_KEY on the mcp host; model per config).
- **Dashboards**: trace aggregates (query volume, zero-hit queries, latency), index health,
  findings queue, snapshot timeline.
- Implementation: small SPA (no build-system sprawl; one bundled page) + JSON endpoints in
  loremaster/ui/. Graph rendering via a lightweight lib (e.g. cytoscape.js vendored).

## 5. MCP tool surface (12 tools; ~2.5k schema tokens vs ~6–7k today)

Doctrine (once, in the server `instructions` block ~350 tokens — drafted; six sections:
identity, LADDER, CITATIONS, FRESHNESS, HONEST FAILURE, MEMORY; per-tool when-to-use moves
INTO tool descriptions, ending the current ~750-token duplication): citation grammar
`[S:tier:path:start-end@hash6]` everywhere; ladder **map → search → get_symbol/read →
impact → verify → write**; teaching misses (did-you-mean) on every miss; rollup + refine
guidance, no pagination; markdown-only (`response_format` cut); short stable keys
`k:xxxxxx`/`m:xxxxxx` (m: = uuid5 6-char prefix, collision-checked); `(ai summary)` marking;
honest staleness. **Graded honest-emptiness contract**: embedding-schema rebuild ⇒ corpus
reads RAISE (as today); verdict-bearing outputs (verify, dead_code, impact liveness) NEVER
run against a rebuilding graph — ToolError with retry hint; HNSW-warming ⇒ BM25-only
degraded with explicit per-result annotation; incremental in-flight files ⇒ ⚠ annotate +
`graph: settled|N pending` footer on impact/map/dead_code. **wait_for_fresh generalized**:
with no path filter it bounded-waits on the manifest's current dirty/embedding set (10s cap,
stale-flagged on timeout). **Caps revised**: search k 1–50 dflt 8; impact depth 1–4 dflt 1
(rollups replace max_results); map budget 200–6000 dflt 2500 (AMENDED 2026-07-04:
re-denominated from 1500 under the measured 1.78 claude-token calibration so DEFAULT
delivered content stays at the proven-useful level — ceiling honest, content preserved;
operator-approved); search default response target re-denominates ≈650→1100 the same way
when P8 enforces it; dead_code ≤1000 dflt 100.
**Memory drift detection**: recall compares each ref's key_version/content-hash against the
live chunk and renders `(drifted — re-verify)` — a stale memory confidently recalled is a
hallucination vector; only `valid_until=null` memories boost/inject. Ledger/backfill rows
without new columns default kind=fact, trust=experiential, valid_until=null.

| Tool | What it is |
|---|---|
| `lore_search` | ONE-query hybrid (HNSW + BM25 over ident/source/llm_summary, RRF k=60) + always-on graph enrichment scaled by `detail: refs\|signatures\|source` (default signatures ≈80 tok/hit: signature + `← N prod / M test · tests: K`); ≤2 matching memories injected as visible provenance-stamped lines; k def 5 max 20; path/tier; wait_for_fresh |
| `lore_map` | PageRank-ranked, token-budgeted orientation (default 1500, cap 6000); `focus` personalization; **`changed_since`** (ref/date/snapshot → diff_status highlighting, v1.0); pinned `decision` memories; explicit elision |
| `lore_get_symbol` | Exact stored definition + citation + hash + 1-hop context; teaching miss |
| `lore_verify` | Batch pre-write claim check `["pkg.Class.method(a,b,kw=…)"]` → ✓/~/✗/? always echoing real signature + citation (~35–60 tok/claim) — the anti-hallucination verb |
| `lore_read` | Span by citation string verbatim; store-backed (`file_text`), hash-stamped, containment-guarded |
| `lore_impact` | who-depends-on-this at `depth` (1..4): prod/test split, covering tests, liveness verdict; depth>1 = per-module rollup |
| `lore_diff` | **Versions + diffing (v1.0)**: no args → recent snapshots (id, ts, git_ref, counts); `since`/`until` (snapshot/ref/date) → file- AND function-level change summary (new/modified/deleted, rollup style, citations) |
| `lore_dead_code` | Repo-wide sweep; HEURISTIC banner; "investigate with lore_impact" |
| `lore_findings` | Query findings (kind/status) + `action: acknowledge\|resolve\|wontfix\|raise_issue` (issue_url stamped back) |
| `lore_remember` | kind (fact/decision/gotcha/uncertainty), trust, refs, `supersedes` (old kept, valid_until); provenance auto; ledger-first |
| `lore_recall` | Memory query; kinds filter; include_superseded audit |
| `lore_index` | Health: manifest states, last-sync/last-sweep/snapshot ages, trace aggregates; `reconcile=True` sweep (command row in split mode) |
| `lore_claim_task` | ATOMIC claim of an open task (compare-and-set — succeeds only if still unclaimed; concurrent double-claim impossible via the _txn conflict guard); sets owner + status=claimed/in_progress. The fleet-coordination primitive. |
| `lore_tasks` | Create / query / update the project orchestration ledger: query by status/owner/blocked_by, create a task (deps, provenance auto), transition status (→ in_progress/done/blocked/wontfix), supersede a task's rationale. Read-mostly + writes; fleet-shared, survives every session. |

Cut from v0.3: 4 graph tools → impact; reindex+status → index; response_format, search mode,
filters dict, dead_code flags → params removed; per-tool doctrine → instructions block.
The 12-tool anti-hallucination surface + the 2 orchestration-ledger tools = **14 tools**
(the ledger pair added 2026-07-03 — lore as the durable fleet-coordination substrate other
agent loops consume; see the `task` table above and the P7/P8 notes).

**Reconciliation deltas**: v1.0 BM25 fields = ident_text + source_text (+ llm_summary when
enrichment lands); python chunker stamps `signature` metadata (astroid args) in P6 for
verify/get_symbol; per-hit enrichment = ref-joins in v1.0, single RRF+RELATE query in v1.1;
PageRank on-demand per-scope v1.0, materialized rank column v1.1; docstring as separate
weighted BM25 field v1.1.

## 6. Phases (strict TDD, contract-first; existing test files are the port contracts)

Branch `feat/surreal-unification`; v0.3 maintenance-only meanwhile.

- **P0 — De-risking spikes** (throwaway): S1 HNSW persistence/boot-rebuild (docs say
  in-memory + 256MiB cache — THE unknown; mitigation: CONCURRENTLY + BM25-only degraded
  search while HNSW builds); S2 SDK embedded async + multi-statement txn; S3 analyzer vs
  code identifiers; S4 search::rrf in 3.0.5; S5 perf/RSS @100k chunks (2048-dim ≈ 820MB F32;
  Matryoshka lever); S6 filtered-KNN recall/overfetch; S7 txn size ceiling; S8
  voyage-context-4 live; S9 surrealkv kill-9 durability (#6872 fixed in 3.0.5?); S10
  watcher-thread/loop safety; S11 split-mode (LIVE SELECT in Python SDK, ws:// WAN
  write latency, reconnect resilience). **GO/NO-GO → operator checkpoint.**
- **P1 (v0.4, ships on CURRENT stack)** — loresigil contextualized capability +
  voyage_context.py + Matryoshka config.
- **P2** — store/surreal_schema.py + store/surreal.py (DDL/analyzer incl. snapshot/finding/
  trace/command tables, upserts, hybrid_search → Candidates, purges, resilient open).
- **P3** — Manifest port (file table; test_manifest.py reruns).
- **P4** — CodeGraph port (derivation untouched; SurrealQL query layer; bare_name;
  impact-shaped queries; test_graph.py is the contract).
- **P5** — Transactional indexer (atomic per-file apply incl. file_text) + watcher/reconcile
  rewiring + **scout entrypoint** (write-role daemon, command-channel subscriber) +
  **snapshot stamping on sweep completion** (git_ref capture).
- **P6** — Search pipeline v2 (RRF hybrid + enrichment ladder + visible memory injection +
  citation grammar + short keys + chunker signature metadata) + extension
  Candidate/FieldIndexSpec + EXTENDING.md.
- **P7 (AMENDED 2026-07-02, Spectron study)** — Memory v2 behind a **`MemoryBackend` seam
  speaking Spectron's exact wire vocabulary** (validFrom/validUntil/supersedes/supersededBy;
  source {kind, ref, trust}; importance; memoryCategory; labels as flat `key=value` strings
  — chunk refs become `lore_ref=<chunk_key>` labels; recall params {k, asOf, labels, lens,
  include}). Ship the `local` backend first (our SurrealDB tables + ledger + hybrid recall,
  as planned); a later `spectron` backend is a thin httpx adapter with lossless migration.
  Drift detection = label-reverse-lookup (identical on both backends). Traces + findings
  stay OURS (verified outside Spectron's scope). Why not reuse as-is: Spectron is a
  closed-source invite-gated preview (container verifiably not pullable — GHCR 403; no
  license/pricing), embeddings hard-coded OpenAI text-embedding-3-small @1536 (our
  TEI/voyage unusable), recall hits omit labels (memory-boost needs a bridge regardless).
  Re-decision trigger: invite arrives → run the study's spike list (pull, 3.0.5 compat,
  DB-privilege demands, label round-trip, supersede-via-conflict, TEI shim behind its
  embedding hook, /mcp tool catalogue, per-fact cost) → operator decides local vs spectron
  backend per project. Operator action item: join the waitlist (it IS the application).
- **P8** — Server: **12-tool surface** (incl. lore_diff + lore_findings query-side + map
  changed_since) + instructions + teaching misses + lore_map (on-demand PageRank;
  presentation BOUND by the P7 consult record docs/design/2026-07-04-map-test-segregation.md
  — production-first default, announced test elision, tests=/focus= inversion, symbol caps,
  impact bare-name tests bridge + transitive rollup labels; its P7-tail contract pins are
  semantic law — format-only changes without a fresh operator decision + consult) +
  lore_verify + store-backed lore_read + lore_index (sync/sweep/snapshot ages) + trace
  writes; role wiring (all|mcp|scout) + SurrealConfig + per-role creds; Containerfile;
  lore-deploy skill (role-aware, git-sync pattern, drop Qdrant verbs); deletions; eval
  harness rewrite. **v1.0 ships** (cutover: stop → deploy → eager rebuild; memories via ledger).

  **DYNAMIC TOKENIZER CALIBRATION (AMENDED 2026-07-04, operator-directed — future-proof
  the token currency).** P7 ships a static TOKEN_BUDGET_CALIBRATION = 1.78 (survey-final;
  cross-model delta within the current generation measured exactly 0%). The static
  constant silently rots when a future model generation forks the tokenizer — P8 builds
  SELF-CALIBRATION: ship a small pinned probe corpus + the survey-time baseline (probe
  ratio + ceiling); at boot, IF an Anthropic key is configured, count the probe set via
  the count_tokens endpoint per configured yardstick model, scale the ceiling
  proportionally (unchanged tokenizer ⇒ exactly the baked value), cache the measurement
  (model+date) in the state dir, and surface calibration status in lore_index
  (measured-this-boot / cached-from-<date> / baked-unverified). OFFLINE POSTURE IS
  LOAD-BEARING: the probe is optional-and-graceful — no key, endpoint down, or timeout
  ⇒ cached-else-baked, never a boot failure, never a blocking call in the read path.
  Drift beyond a threshold logs loudly + auto-files a finding (rides the P8 findings
  surface). Per-model probe caches enable an optional `consumer_model` hint (config
  default + per-call override, evaluated in the P8 tool-surface design against its
  schema-token cost) — inert while generations agree, automatic when they fork. The
  committed scripts/token_survey.py remains the full-corpus re-derivation instrument;
  the boot probe is the cheap drift detector between surveys.
  **RE-AMENDED 2026-07-04 (operator — probe is MANDATORY, not optional):** the Anthropic
  API key becomes a REQUIRED lore.yaml field (env-indirected per the house resolve_secret
  style); boot MEASURES token generation via the key and DYNAMICALLY ASSIGNS the
  calibration every startup — a baked constant is never trusted across boots, and log
  lines are not a control surface ("log files are never looked at unless there's a
  problem"). Budgeted calls take the CALLER'S MODEL NAME as a parameter (DECIDED — no
  longer a maybe): per-model ratios measured/cached at boot, the call's model selects its
  ratio. SETTLED (operator, 2026-07-04): (i) the Anthropic boot dependency is ACCEPTED
  for now — key missing ⇒ config validation fails fast; **REVISIT-LATER TODO:
  re-evaluate the hard key requirement** (e.g. an explicit opt-out for air-gapped
  deployments) once the subsystem has operational mileage. (ii) Endpoint UNREACHABLE at
  boot with a valid key: boot SERVES THE CACHED calibration values and starts a
  background RETRY LOOP until a live measurement lands; lore_index's status output
  states the condition explicitly (calibration: cached-retrying, with the cache's
  model+date) — never a boot failure, never a silent fallback.

  **CONFIG-DYNAMISM SCOUT (AMENDED 2026-07-04, operator-directed).** DI's lore.yaml went
  silently stale (missing venv excludes burning 3,394 inotify watches; no surreal block)
  — static config rots. P8 scout task: audit EVERY lore.yaml field for
  static-vs-dynamically-derivable; propose per field: derive-at-boot (e.g. venv/VCS/cache
  dir auto-detection for excludes, embedder dim/tokenizer from a live probe, port
  assignment, tier discovery), validate-against-reality (config says X, disk says Y ⇒
  loud mismatch), or must-stay-config (roots, slug, secret env names). Deliverable:
  field-by-field disposition table + implications for the lore-deploy scaffold/migrate
  verbs (auto-heal vs refuse-and-point).

  **v0.3→v2 FLEET MIGRATION TOOL (AMENDED 2026-07-04, operator-directed).** Live v0.3
  deployments (lore-demand_intelligence today; any project on the v0.3/v0.4-qdrant pin)
  hold valuable project data that must survive the v2 cutover. **Data inventory
  (verified): the ONLY non-derivable data is the project memory store** — the
  `lore_<slug>_memory` Qdrant collection, whose durable source of truth is the
  `<slug>.memory.db` SQLite write-through ledger on the state volume (v0.3.6+ boot
  backfill captures pre-ledger memories into it). Everything else (chunk vectors, graph,
  manifest, fingerprint/meta) rebuilds from source by design; re-embedding cost is
  accepted policy. **The tool** (a `lore-deploy` skill verb `migrate` and/or
  `scripts/lore_migrate.py`), per slug: (1) run ONE final `backfill_ledger_from_store`
  sweep against the old Qdrant collection so the ledger provably covers every stored
  memory (count parity receipt); (2) ensure the slug's `lore.yaml` gains its surreal
  block (the known DI lockstep prerequisite); (3) replay the ledger into the v2 Surreal
  `memory` table via the existing `restore_from_ledger` machinery (idempotent — uuid5
  ids overwrite in place; legacy rows take the plan-pinned defaults kind=fact,
  trust=experiential, valid_until=null); (4) verify: row-count parity + spot recalls
  before the v0.3 container/collection retires. Note: the lore slug itself already
  migrated this way by hand at the P6/P7 deploys — the tool formalizes it for the fleet.
  **THE lore-deploy SKILL OWNS THE WORKFLOW (operator-directed 2026-07-04):** the skill
  (in-repo at skills/lore-deploy/, symlinked into ~/.claude/skills) gains a `migrate`
  verb handling the whole version migration end-to-end, INCLUDING upgrading the
  project's `lore.yaml` in place — detect a v0.3-era deployment (config lacks the
  surreal block / container runs a pre-v2 pin), rewrite the config additively (surreal
  block with per-project port/namespace assignment, any new v2 keys) while PRESERVING
  every project-specific setting (roots/includes/excludes/embedding/chunker overrides),
  back up the prior lore.yaml beside it, then drive the data migration (steps 1–4
  above) and the container swap — old image pin retained as the rollback. The skill's
  existing verbs must refuse-and-point (never silently start a v2 container over an
  unmigrated v0.3 state dir): `start` on a version-mismatched deployment says
  "run migrate first."
  Distinct scope note: doc-file knowledge imports (e.g. DI's DECISIONS.md/GOTCHAS.md/
  salvaged_memory.md → kind-tagged memories) are a SEPARATE, per-project content
  migration, not part of this tool.
  **OPEN DESIGN ITEM — CONCURRENCY (deliberately unresolved here; assign to a dedicated
  agent before building):** the old instance may be LIVE and serving agents during
  migration — memories written mid-window must not be lost, and the serving story during
  cutover must be defined. Candidate shapes the design agent must evaluate (not decided):
  a declared freeze window; dual-write bridging; ledger-tail catch-up replay after
  cutover (the uuid5 idempotence makes repeated replay safe, so a second catch-up pass
  is cheap); MCP endpoint swap ordering. Deliverable: the no-loss guarantee, the
  serving-window behavior, and the failure/rollback story, each with receipts.

  **P8 EXECUTION DECOMPOSITION (Fable review, 2026-07-04).** P8's full inventory
  (§6 core + the three 2026-07-04 amendments + ledger #2/#4/#5/#7/#8/#9/#11/#12/#13
  + FRICTION.md open entries) measures ≈3.65 P7-window-units — far past one
  orchestrator window (P7 ≈ 1.0 unit: ~25 agents, 14–15 commits, 3 cold audits +
  2 fix cycles, 2 redeploys; near-full at close DESPITE aggressive externalization).
  Partition: SIX sequential components, each ≤ ~0.7 units, each ending suite-green +
  cold-audited + committed + (where possible) redeployed/smoke-verifiable, each
  EXITING BY WRITING the next component's resume doc (the lore-v2-RESUME.md shape:
  role, verified-state receipts, mission, starting orders, gotchas, open operator
  items) at `~/.claude/plans/lore-v2-P8<x>-RESUME.md`. Chain:
  **P8a → P8b → P8c → P8d → P8e → P8f** (hard order; rationale in
  REPORT-p8-decomp.md, repo root). Sizing reasoning + rejected alternatives: ibid.

  - **P8a — Substrate purge + hygiene + eval baseline (~0.6 wu).**
    Scope: ledger **#4** (graph.py Kùzu-shell surgery — port the 19 derivation
    tests, drop the kuzu dep); **#8** (move uuid5 helpers FIRST, then retire
    memory/store.py + the 2 Qdrant test files; impact+grep gate before every
    deletion); the **Qdrant purge** (store/qdrant.py, the probe-gate/
    ensure_collection boot path, qdrant-client dep — boot stops requiring Qdrant);
    **#7** (_query raw-error hygiene, 3 sites); **#9** (drift-fetch batching,
    coverage gaps, public point-get); **#5** (sanitiser residual LRM/RLM +
    U+2028/2029); **trace-table async write path** (store plumbing only, P2 DDL
    exists — no tool change); **RECORD THE EVAL BASELINE** (existing 23-pair
    harness vs the LIVE pre-flip surface: avg tool-calls/task + avg response
    tokens/task — §8.3's gate input; re-measure even if an older baseline exists;
    MUST exist before P8d).
    Entry: P7 closed @ 3dfcd21, MCP reloaded. Exit checkpoint: suite green + cold
    audit + commits + **REDEPLOY — first Qdrant-free/kuzu-free boot** (observable:
    lore-lore healthy with no Qdrant dependency); baseline receipts committed.
    Handoff: lore-v2-P8b-RESUME.md.
  - **P8b — New verbs: verify / read / diff / findings (~0.65 wu).**
    Scope: **lore_verify** + symbols.py shared resolver (the anti-hallucination
    verb); **store-backed lore_read** (file_text spans, hash-verified,
    containment-guarded); **lore_diff** (snapshot list + since/until file- AND
    function-level summaries — P5 snapshots are the data); ledger **#2 findings
    surface** (finding table live: lore_findings query + report/acknowledge/
    resolve/wontfix, kind=friction, chain-head + ordered-browse per the di-scout
    ledger-reads friction; raise_issue stays P9). ADDITIVE under current naming —
    no renames yet (independently deployable).
    Entry: P8a handoff. Exit checkpoint: green + cold audit + commit + redeploy;
    MCP smoke = verify/diff/findings round-trips; one real friction finding filed
    through the new surface; subagent-brief convention switches FRICTION: lines →
    lore_findings. Handoff: lore-v2-P8c-RESUME.md.
  - **P8c — Boot token-calibration engine + config-dynamism scout (~0.45 wu).**
    Scope: ledger **#12 in full** (REQUIRED Anthropic-key lore.yaml field,
    resolve_secret-style env indirection, fail-fast config validation; pinned probe
    corpus + survey baseline; boot MEASURES per configured yardstick model via
    count_tokens and DYNAMICALLY ASSIGNS every startup; per-model caches in the
    state dir; endpoint-unreachable-with-valid-key ⇒ serve cached + background
    retry loop, never a boot failure; drift threshold ⇒ auto-file a finding via
    P8b's surface; calibration status line in index_status). Ledger **#13**
    config-dynamism scout: field-by-field disposition table (derive-at-boot /
    validate-against-reality / must-stay-config) → **operator strikes the table**
    (approved items implement in P8e/P8f).
    Entry: P8b handoff (findings surface live — the drift auto-file dependency).
    Exit checkpoint: green + audit + commit + redeploy (boot logs the measured
    calibration; index_status shows measured/cached/cached-retrying); disposition
    table operator-dispositioned. Handoff: lore-v2-P8d-RESUME.md.
  - **P8d — THE SURFACE FLIP: 14 tools + instructions + eval A/B gate (~0.7 wu).**
    Scope: consolidation per §5 (4 graph tools → lore_impact; reindex+status →
    lore_index w/ last-sync/sweep/snapshot ages + trace aggregates + calibration
    line; renames; params cut); **caller-model param on budgeted calls** +
    re-denominated defaults (search ≈650→1100) riding P8c's ratios; **teaching
    misses / resolve-or-error family everywhere** (references silent-zeros vs
    unresolved, path-filter exact-match miss, save-side digest guidance — the open
    FRICTION affordance entries); map changed_since; **instructions block** (six
    sections ~350 tok; per-tool doctrine into descriptions; deferred-loading +
    friction doctrine lines); **eval harness rewrite → ~35 pairs**; **A/B GATE:
    flipped surface ≤ P8a baseline on both metrics (§8.3)**; FRICTION.md open
    entries migrate into finding rows, the file retires. CONSTRAINT: the
    2026-07-04 map-test-segregation record is semantic law — format changes need
    a fresh operator decision + consult.
    Entry: P8a baseline receipts + P8c ratios. Exit checkpoint: green + cold audit
    + commit + redeploy + A/B receipts; operator reloads MCP (renamed surface).
    **OVERFLOW VALVE:** if the A/B gate fails, close at flipped+green+audited with
    regressions ledgered → a P8d′ fix window runs before P8e.
    Handoff: lore-v2-P8e-RESUME.md.
  - **P8e — Roles, split topology, Containerfile, drills (~0.65 wu).**
    Scope: **role wiring (all|mcp|scout)** + SurrealConfig **per-role creds**;
    **Containerfile** rework (and VERIFY the installed-vs-mounted astroid shadow
    gap on the v2 image — the lore_references near-miss friction; fix here if it
    reproduces, since liveness verdicts depend on it); the **operator-approved
    subset of #13 dispositions** (path-anchored excludes / venv+binary-dir
    heuristics / watch-scope telemetry / yaml chunker-or-documented-override /
    include-glob-pierces-exclude precedence — SPLIT OUT as a P8e′ window if the
    approved subset exceeds ~1 build cycle); **§8.6 resilience drills**; **§8.7
    split-topology end-to-end** (Surreal server + scout container + mcp container;
    git-pull reconcile; independent kill/restart; degraded-honesty checks).
    Entry: P8d handoff (surface final — roles don't reopen schemas). Exit
    checkpoint: green + audit + commit; split topology DEMONSTRATED with receipts;
    single-node redeploy stays live. Handoff: lore-v2-P8f-RESUME.md.
  - **P8f — lore-deploy rework + fleet migration + v1.0 SHIP (~0.6 wu).**
    Scope: **lore-deploy skill rework** (role-aware verbs, git_sync pattern, drop
    Qdrant verbs, scaffold updated per #13 dispositions); ledger **#11 migrate
    verb** per docs/design/2026-07-04-migration-concurrency.md **Shape D** — build
    its §7 machinery (N1 skip-and-log replay fix + pre-flight embed dry-run, N2
    public count(), N3 scripts/lore_migrate.py driver, N6 lore.yaml upgrader +
    `start` refuse-and-point; N4 explicitly NOT built); **EXECUTE the DI
    migration** (lore-demand_intelligence; operator GO/NO-GO after Phase A; retire
    deferred to soak); **§8.5 token-accounting receipts**; §8.4 dogfood receipts
    on both projects; **v1.0 ships** (tag + cutover receipts).
    Entry: P8e handoff + operator answers to the migration design's §8 questions
    (1–4). Exit checkpoint: v1.0 tagged; DI serving on v2 with parity receipts +
    spot recalls; P9 resume doc written. Handoff: lore-v2-P9-RESUME.md.

  **NOT IN ANY COMPONENT (flagged; operator schedules):** the DI doc-content
  import (DECISIONS.md/GOTCHAS.md → kind-tagged memories — explicitly out of #11's
  scope, a per-project content migration); the Spectron backend re-decision
  (invite-gated); §8.8 UI smoke (P10). **Total estimate: ~3.65 window-units across
  6 components (+ optional P8d′/P8e′ valves).**
- **P9 (v1.1)** — **loresage + enrichment worker** (llm_summary live in BM25) + sweep
  detectors + `raise_issue` escalation (gh/Gitea) + materialized RELATE edges + one-query
  graph-enriched search + materialized PageRank + docstring BM25 field + **cross-tier
  compare** (below).

**Cross-tier compare (AMENDED 2026-07-03, operator-directed; P9 / post-P8). WHY: we are
prepping for a large ERP version migration — Odoo 15 EE custom code ports to Odoo 19/20 EE,
with agents working BOTH codebases concurrently. The decided topology is ONE lore project
holding both versions as TIERS (e.g. static `odoo15-core`/`odoo19-core`, live
`odoo19-custom`): one MCP schema cost, one shared memory (migration decisions apply to both
sides), and the name-node FQN fan-out already returns both versions of a symbol side by
side. The missing ergonomic is comparing them in ONE call.** Spec: extend `lore_diff` with a
tier mode — `lore_diff(tiers=("odoo15-core","odoo19-core"), target=…)` — NO new tool (the
14-tool surface and its schema budget hold; it's a parameter on the existing diff verb).
Two granularities, both citation-first: (a) **symbol compare** (`target` = qualified name):
each tier's stored definition — signature, content_hash, cited span — rendered side by side
with a same/differs verdict per chunk (hash compare is free; the chunk table already carries
content_hash per tier — C1 tier coexistence is pinned all the way down); (b) **file/module
rollup** (`target` = path prefix or omitted): files present only in tier A / only in B /
differing by manifest sha512, token-budgeted rollup style like `lore_map`. Data model: ZERO
schema change — reads chunks + manifest + graph name-nodes that already exist per tier.
Builder notes: reuse `lore_diff`'s snapshot-diff rendering (tier-diff is the same output
shape with tiers instead of times); tier pairs validate against configured roots (teaching
miss on a typo); respect the graded honest-emptiness contract (a tier mid-rebuild NEVER
yields a silent 'missing in B'). Until it ships, the documented prompt convention is:
`lore_get_symbol(fqn)` returns all tiers' hits via FQN fan-out — agents compare manually.

**Spectron coverage-audit adoptions (2026-07-02, 117/117 docs pages; full matrix in the
session record).** Accepted gaps: **P2 (applied mid-build)** memory.importance +
memory.expires_at + trace.token_cost + trace.model columns (additive, no behavior).
**P6**: config-gated cross-encoder reranker seam after RRF (`search.reranker: {url,model}|null`,
default off, TEI-servable, adopted only if the A/B eval shows accuracy gain) + a
render-sanitiser for non-fenced output fields (control-char/framing collapse on identities/
paths). **P7**: kind=`ongoing` (current-work memory with expires_at — the coding-agent
continuity pattern), importance defaults by kind + reinforcement-on-recall (decay/expiry
sweeps v1.1), invalidate-without-successor (`lore_remember` invalidate mode — wrong-memory
retirement, no replacement needed), uuid5 content-derived memory ids pinned for idempotency.
**P9**: token/model/cost stamping on enrichment traces + prompt-hygiene sanitiser for repo
text entering loresage prompts + markdown outbound-link extractor → refers edges (shares the
Odoo-XML extractor seam). **Deferred**: trace-feedback ranking (v1.2+, needs eval infra),
Prometheus /metrics (P10 optional), MCP-resources file tree over file_text for split-mode
remote agents (P10/v1.2 evaluation). Justified-OUT: LLM extraction/reconciliation/elaboration/
reflection ladders (agent-authored memories + deterministic astroid derivation), episodic
sessions/chat (harness-owned), T2 response cache + T4 HyDE (no LLM in lore's read path),
multi-tenant scope grants, geo/tri-temporal. **Spectron runtime floor is SurrealDB 3.1.x**
(vs our validated 3.0.5) — added to the spectron-backend re-decision spike list: verify
3.1.x coexistence or a dedicated instance before adopting that backend.
- **P10 (v1.2)** — **UI**: /ui SPA (graph explorer w/ diff overlays + snapshot slider,
  search/symbol views, findings queue, trace dashboards) + **Agent-SDK chat** wired to the
  project's own MCP. Vector-side enrichment embedding evaluated here.

## 7. Critical files

New: loremaster/loremaster/store/surreal.py + store/surreal_schema.py, scout.py (write-role
daemon + command subscriber), snapshots.py (stamping + diff), findings.py, trace.py,
ui/ (SPA + endpoints + Agent-SDK chat), **loresage/** (new workspace package: llm ABC +
claude + local backends), loresigil/loresigil/voyage_context.py.
Heavy modification: server.py (12 tools, _INSTRUCTIONS, AppContext, roles), search.py,
graph.py (query layer), index/indexer.py, index/manifest.py, memory/store.py + ledger.py,
extension.py, config.py (SurrealConfig, roles, enrichment, actions), symbols.py (shared
resolver for get_symbol/verify/did-you-mean), Containerfile, skills/lore-deploy/.
Deleted: store/qdrant.py, index/kuzu_resilient.py, index/sqlite_resilient.py.

## 8. Verification

1. **P0 spike receipts** reviewed at the operator checkpoint before any production code.
2. **TDD per phase** — contract tests first (fresh-context grader per tdd skill); ports keep
   existing test files green.
3. **Eval harness as A/B acceptance gate** — the existing 23 pairs are tool-name-agnostic
   and survive unchanged: record the v1 baseline (avg tool-calls/task + avg response
   tokens/task) BEFORE the port, gate v2 at ≤ v1 on both. Extend to ~35 pairs
   (orientation/map ×2, verify ×2 incl. wrong-arity + did-you-mean, impact ×2, memory
   supersede/provenance ×2, changed_since ×1, honest-failure negatives ×2).
4. **Dogfood** — deploy on lore itself + demand_intelligence; drive the ladder on real
   questions; wait_for_fresh after a live edit; enrichment sweep on an undocumented module;
   file a real finding → issue.
5. **Token accounting** — real schema+response costs measured with the Sonnet-5 tokenizer;
   budgets: schemas ≤2.5k, default search ≤650 tok, map ≤ its budget.
6. **Resilience drills** — kill -9 / corrupt-dir / wiped-store / fingerprint-change (FP-xx
   analogues on the unified store).
7. **Split-topology end-to-end** — SurrealDB server + scout container watching a checkout +
   mcp container: git pull touching many files → reconcile absorbs; snapshot stamped;
   lore_diff shows the pull's changes function-level; lore_read spans match disk hashes;
   reconcile command row round-trips; kill/restart each component independently (scout
   reconnect, MCP degraded-honesty while store down).
8. **UI smoke** — graph renders the real project; chat answers a repo question using lore
   tools end-to-end; dashboards show live traces.
