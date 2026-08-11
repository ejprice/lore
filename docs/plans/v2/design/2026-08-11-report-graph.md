# The report graph — Consumer-Law-first (research reaches report reasoning FROM the code)

**Design doc.** Author: `fable-design-05b` (design sidecar). Date: 2026-08-11.
Grounded @HEAD `299e69a`. **DESIGN ONLY — no production code/tests; contract-adversary + build in a
later packet.** The operator rules; this doc recommends and decides nothing.

> **Companion to** `docs/plans/v2/design/2026-08-11-task-coordination-substrate.md`. The
> `report → task` and `report → agent` edges are SHARED: **ONE report-entity model serves both docs.**
> This doc maps to **packet 28a** (#163 ⊃ #160); the coordination doc maps to a coordination packet.
> Store law cited, never re-transcribed: `docs/reference/surrealdb-31-capabilities.md`.

---

## 0. THE FRAMING IS LOAD-BEARING — the Consumer Law dictates the shape
Do NOT start from storage or a tidy id. Start from **"how does a research agent actually REACH this
data?"** — and the answer is **never by report id**. A report id is an INTERNAL handle; the consumer
does not hold one. The entity, edges, and verbs are DERIVED from the real access patterns below.

**Two access patterns, PRIMARY first:**
1. **RESEARCH DISCOVERY** — semantic content + traversal from an entity the agent already holds.
   **This DICTATES the shape.**
2. **Stable inter-artifact CITATION by id** — the #152/#153 dangling-address / provenance concern.
   **Served, but it does NOT drive the shape.** (A report id/path is how a *citation* resolves; it is
   never how *discovery* begins.)

---

## PART 1 — THE EXISTING SUBSTRATE (verify — reports are ALREADY embedded)

- **Reports are already indexed and embedded.** `lore.yaml` `roots[tier=lore]` includes `**/*.md`
  over `/workspace` — so **root `REPORT-*.md`, `docs/plans/v2/receipts/**/*.md`, and every other `.md`
  are already chunked + embedded** in tier **`lore`**, the SAME tier as all Python code. So the job is
  NOT "make reports searchable" (done) — it is **structure + labeling**:
  - ⚠ **There is no distinct report tier and no report label today.** Reports share tier `lore` with
    code and all docs, so a consumer **cannot scope a search to reports**, and a report hit is not
    marked as report reasoning. That is the entry-point-1 gap (§2.1).
- **The chunk / markdown ingest pipeline** (verified): `lorescribe/markdown.py::MarkdownChunker` splits
  a `.md` along its heading hierarchy (byte-exact bodies, `chunk_type="markdown_section"`); `identity`
  is the heading-path breadcrumb (`h1 > h2 > h3`, + an occurrence ordinal / `(preamble)`); a per-chunk
  breadcrumb header (`File: … \n Section: …`) is folded into the embedding input. Stored `chunk` columns
  (`surreal_schema.py`, `CHUNK_COLUMNS`): `tier, file_path, chunk_type, identity, sub_ordinal,
  content_hash, mtime_ns, line_start, line_end, source_text, ident_text, llm_summary, metadata(FLEXIBLE),
  embedding`. **Embed-once seam:** `Indexer._index_chunks` embeds each new/changed file exactly once,
  keyed on `content_hash`, via `loresigil` (voyage-4-nano). **A report `.md` ALREADY rides this exact
  path** — the reuse point that makes a re-embed unnecessary (§3.1/§3.3).
- **The code graph** (verified — this is the key reuse target): derivation in `graph.py`
  (astroid-resolved), storage/query in `graph_surreal.py::SurrealCodeGraph`. A **NODE is a Python
  symbol** (`module`/`class`/`method`/`function`) in table `code_node` (composite id
  `[tier, file_path, qualified_name]`), **not a chunk or file.** Edges use a **`name`-node
  INDIRECTION, not direct node→node**: `refers` (`TYPE RELATION IN code_node OUT name`, edge field
  `kind ∈ {imports,calls,inherits,defines}` + `resolved:bool`) and `answers_to` (each node answers_to
  BOTH its FQN- and bare-name — the bridge that lets a bare query reach a resolved FQN). The `name`
  table (id `name:<string>`) is **UPSERTed idempotently, so an edge can be created BEFORE its endpoint
  `code_node` exists** (order-independence) and a repeated FQN stays distinct (collision-correctness).
  `refers`/`answers_to` are **NOT `ENFORCED`, NO `UNIQUE(in,out)`** (they target the UPSERTed `name`,
  which always exists). Edges are READ as **plain SELECTs on the `in`/`out` columns**
  (`SELECT VALUE in FROM refers WHERE out IN $names`), never `->refers->` traversal; this backs
  `lore_impact` (`ImpactEngine → SurrealCodeGraph.{what_imports, blast_radius, references, tests_for}`).
- **Doc bodies derive NO edges today — CONFIRMED with a hard gate.** `Indexer._graph_fragment` returns
  `None` for any non-`.py` file ("*the graph is a Python-AST structure only*"), so a `.md` never enters
  the graph builder and markdown chunks (`markdown_section`) are never nodes. **So `report → symbol`
  edges are NET-NEW** — but they REUSE the `name`-node indirection + the RELATE machinery (§3.2/§3.3).
- **#163 (28a's charter) ⊃ #160.** #163 already scoped this as ONE packet: Deliverable 1 = a
  section-aware chronological THREAD verb (closes #160 — "a retrieved chunk arrives without its
  header", so a dated/superseded report reads as current); Deliverable 2 = the DOCUMENT GRAPH
  (`report → finding/commit/symbol/path`). #163's load-bearing insight: **the #152/#153 durable-
  citation discipline turned report prose into a PARSEABLE EDGE SET** — reports now cite in-tree
  symbols, finding ids, commit SHAs, and tracked paths, not bare `REPORT-*.md`. #160's own preferred
  fix: **a PATH-DERIVED marker propagated into every chunk's served header** (cannot go stale).
- **The `story` verb (05a)** reconstructs ONE task's arc in one call (created → claim → messages →
  transitions → report_path) — the mirror for a **report-`story`** (§3.4).
- **Existing weak task→report pointer:** the task ledger's `done` edge already records
  `task.report_path` (a STRING). The report graph upgrades this to a RESOLVABLE edge (§3.5).

---

## PART 2 — THE ENTRY POINTS (the shape is built around these)

### 2.1 EP1 — SEMANTIC CONTENT (already embedded) → LABEL + FILTER report hits
The content path already works (vector search over the `.md` chunks). Today a report hit is
distinguishable **only by its `file_path`** (`…/receipts/…`, `REPORT-*.md`) — reports share tier `lore`
with all code and docs, `lore_search(tier=)` can't isolate them, and `lore_search(path=)` needs an
EXACT file path (no dir/prefix). Two DISTINCT jobs, at very different cost:
- **LABEL — CHEAP, path-derived, no re-index (recommend as an early slice).** Every report-chunk hit
  carries a served-header prefix `[report · author=<agent> · date=<YYYY-MM-DD> · packet=<pkt> ·
  <root|archived>]` DERIVED from `file_path` at RENDER time (in `search.py::_base_format`, which already
  holds the path). **This is also #160's fix** — the label travels WITH the span, so a dated/superseded
  report can never read as current. Path-derived ⇒ cannot go stale; needs no new field, no re-embed.
- **FILTER/SCOPE — needs new machinery (fork).** To scope a search TO / AWAY-FROM reports cleanly, the
  choice is (per the scout): a **new dedicated `report` tier** (a `lore.yaml` `roots:` entry over
  `**/REPORT-*.md` + `docs/plans/v2/receipts/**`, with those paths EXCLUDED from tier `lore` to avoid
  double-index; `tier=` then works, and it doubles as #161's "dated records in a separate semantic
  space" — one-time re-index of report files only) vs a **path-prefix filter** in `lore_search` (keeps
  reports in tier `lore`, adds a `path_prefix=`/`kind=report` scope; no re-index, but a new search
  capability). See Fork 1.

### 2.2 EP2 — TRAVERSAL FROM AN ENTITY THE AGENT ALREADY HOLDS (the core of the shape)
The agent is studying something and wants the reasoning attached to it:
- **task → its reports** (`report → task`)
- **finding → the reports that analyze/file it** (`report → finding`, from body `#NNN` refs)
- **packet / wave → its reports** (derivable from the `receipts/<date>-<packet>/` path — a *derived*
  grouping, not necessarily an edge)
- **agent → its reports** (`report → agent`, from the `REPORT-<agent>.md` filename)
- **★ THE PAYOFF EDGE — `report ↔ CODE SYMBOL / FILE`**, wired into the EXISTING code graph, so
  *"what reasoning exists about `_is_blocked`?"* surfaces the reports that analyzed it **ALONGSIDE the
  code**. This is the Consumer-Law win: research reaches report reasoning FROM the code it is already
  studying (§3.2 for derivation).
- **report ↔ report** — the supersession chain + chronological thread (#160/#163 Deliverable 1).

### 2.3 EP3 — BY WHO / WHEN
Author (agent), date + packet/wave (from the receipts path). These are FILTERS/FACETS on the above,
derived from path + filename — not separate machinery.

---

## PART 3 — THE DESIGN

### 3.1 The report ENTITY — a graph SPINE that POINTS at chunks, it does NOT re-embed
Reports are already chunked + embedded (§1). So the entity carries **structure + metadata + edges**,
and **points at the already-indexed `.md` chunks by `file_path`** — **no second embedding.** Semantic
hits keep coming from the chunks (unchanged); the entity adds the graph the chunks hang off.
- **`report` node fields (derived, not caller-supplied):** composite record id
  **`report:[tier, file_path]`** (reusing `code_node`'s deterministic-composite-id idiom, so re-ingest
  is idempotent and the internal `id` is never the consumer's entry point — Consumer Law §0);
  `author` (from `REPORT-<agent>.md`), `created_date` + `packet` (from the `receipts/<date>-<packet>/`
  path; a root report is "live/unarchived"), `current|superseded` (from an archive-header banner if
  present), `title` (first heading). **No embedding field** (the `chunk` rows own it — the entity POINTS
  at chunks by `file_path`).

### 3.2 The EDGES — TWO precedent-grounded styles (the `name` indirection is the key)
There are **two edge styles**, each matching an existing precedent, and the split is what makes the
payoff edge non-dangling:

**Style 1 — `report → <ledger row>`, ENFORCED + `UNIQUE(in,out)`** (precedent: `briefed`/`to`). The
OUT endpoint is a real row that must exist:
| edge | OUT | derived from |
|---|---|---|
| `report → task` | `task` row | the report's declared task / `receipts` context / `task.report_path` back-ref |
| `report → agent` | `agent` row | the `REPORT-<agent>.md` filename |
| `report → finding` | `finding` row | body `#NNN` refs (durable citations, #152/#153) |
| `report → report` | `report` node | supersession banner + chronological order |

**Style 2 — `report → name` (the SYMBOL/FILE payoff edge), NOT ENFORCED, targets the UPSERTed `name`
node** (precedent: `refers`/`answers_to`). **This is the crucial reuse.** The code graph already routes
every symbol reference through the idempotently-UPSERTed `name` table (§1), precisely so an edge is
**order-independent and never dangles** — the `name` node always exists (or is created on demand),
whether or not a `code_node` currently maps to it. So:
- **`report --mentions--> name`**, keyed on the symbol/path string the report CITES. Derive it from the
  report's EXPLICIT durable citations (repo law #152/#153 turned prose into a parseable edge set — #163's
  insight), **not NLP** (fuzzy mention-matching is an optional, noisy secondary). Optionally carry a
  `resolved: bool` edge field (does a `code_node` currently map to this name?), exactly as `refers` does.
- **Reads reuse the `name` bridge:** "reports about symbol X" resolves X → its name node(s) via the
  SAME `answers_to` bare↔FQN fan-out, then `SELECT VALUE in FROM mentions WHERE out IN $names` — byte-for-
  byte the `what_imports` read pattern. So a report citing a BARE name still surfaces for an FQN query.
- **⚠ This DISSOLVES the dangling/cascade fork I raised earlier.** Because the edge targets the stable
  `name` node (not `code_node`), it **never dangles and needs no cascade** (contrast: my earlier "resolve
  to live symbols + cascade on delete" reasoning — the name indirection is strictly better). A report
  citing a since-deleted symbol keeps a durable `mentions → name` edge; whether that name is currently
  live code is answered by joining `name → code_node` at read time (or the cached `resolved` flag). No
  re-ingest of the report is needed when the underlying symbol comes or goes — the fork is GONE.

**Secondary (citation pattern, not shape-driving):** `report → commit` (SHA) / `report → tracked-path`
serve the #152/#153 provenance access pattern; keep them as edges to a lightweight ref node or as
searchable body text, not ENFORCED.

### 3.3 INGEST — reuse the chunk pipeline + the code-graph resolver; NO parallel embedder
A file matching the report path pattern (root `REPORT-*.md`, `receipts/**`) gets, AFTER the existing
chunk+embed pass (which already runs — reports ride `Indexer._index_chunks`, embedded once by
`content_hash`; **no second embed**):
1. **mint/update the `report` node** (id `report:[tier, file_path]`); derive metadata from path+filename.
2. **derive + RELATE edges** — a NEW markdown ref-extractor parses the body for durable citations
   (`#NNN` findings, in-tree symbols/`file:symbol`, sibling report paths) and emits the Style-1/Style-2
   edges. **The extractor is genuinely net-new** (the Python-AST extractor cannot parse prose; today
   `Indexer._graph_fragment` hard-gates non-`.py` files to `None`, so this is the seam to EXTEND — a
   doc-graph fragment builder parallel to the Python one, gated on report paths instead of `.py`).
- **What it REUSES (do NOT clone):** the `name` table + the bound-`RecordID` id builder (`_name_id`) and
  the `RELATE $src->edge->$dst SET …` idiom (bound RecordIDs, never `type::record()` endpoints); the
  `_define_relation_table` DDL helper (`DEFINE TABLE OVERWRITE … TYPE RELATION … [ENFORCED] SCHEMAFULL`);
  the per-file **DELETE-then-RELATE rebuild** inside one `execute_transaction` `BEGIN…COMMIT`; and the
  chunk/embed pass for content. It LEANS ON the #152/#153 citation discipline, not NLP — so the extractor
  is a citation parser, not a mention-matcher.
- **Reuse boundary, stated honestly:** the code graph's *edge derivation* (astroid AST) cannot be
  reused (a report is prose); what is reused is the *storage substrate* (name indirection + RELATE +
  rebuild + composite ids) and the *read bridge* (`answers_to`). This is "reuse the machinery, author the
  new extractor" — the ONE-IMPLEMENTATION line is: no parallel embedder, no second `name` table, no
  cloned RELATE idiom.

### 3.4 RETRIEVAL VERBS — the consumer-facing surface (design for the agent reader)
1. **`lore_search` labels + scopes report hits** (EP1): every report-chunk hit carries the path-derived
   `[report · author · date · packet]` header (closes #160); a `kind=report` scope filters to/from/only
   reports. Lowest-surface, highest-frequency win — an agent doing ANY search now knows which hits are
   report reasoning.
2. **`lore_impact` gains a "reports" section** (EP2, ★ THE PAYOFF): `lore_impact(symbol)` already
   returns consumers + covering tests via `SurrealCodeGraph`; **add "reports analyzing this symbol"** as
   a `SELECT VALUE in FROM mentions WHERE out IN $names-for-X` — the SAME `name`-bridge read as
   `what_imports`, so a bare-name citation surfaces for an FQN query (§3.2). *The Consumer-Law win with
   the least new surface* — no new tool; research on a symbol surfaces its reasoning ALONGSIDE its code
   and tests. **Recommend this as the flagship integration.**
3. **A report-aware traversal** — "reports covering `<symbol | task | finding>`". Could be a small new
   verb (`lore_reports(about=…)`) or folded into `lore_impact`/`lore_map`. Fork: new verb vs fold
   (a new tool is a surface change with registration pins; #163 forks this too).
4. **A report-`story`** (mirror the 05a task `story`): report-anchored, one call → the report's task,
   author, findings, symbols, and supersession chain. Serves the SECONDARY citation pattern (given a
   report, reconstruct its context) without letting id drive discovery.
5. **The THREAD verb** (#163 Deliverable 1): a section-aware, document-grouped, chronological thread
   across reports on a topic — reconcile with #163 (do not build a second thread mechanism).

### 3.5 RECONCILE with the coordination-substrate doc — ONE model
`report → task` and `report → agent` are the SHARED edges. The coordination doc's close-out / orphan
detection READS them:
- **"task `done`, no report"** — a done task whose `report_path` resolves to no `report` entity.
- **"report filed, task still `in_progress`"** — a `report → task` edge whose task never reached a
  terminal state (a stuck claim the reaping surface, coord-doc §2B, already hunts).
This UPGRADES the coordination doc's weak `task.report_path` STRING into a resolvable edge. **ONE report
entity + `report ↔ task`/`report ↔ agent`** serve both. (Until the report graph lands, the coordination
packet's close-out checks use the `report_path` string; they upgrade to edge-resolution when 28a ships —
§Sequencing.)

---

## STORE LAW + ONE-IMPLEMENTATION COMPLIANCE
- **`report` table:** `DEFINE TABLE IF NOT EXISTS report SCHEMAFULL`; fields `DEFINE FIELD OVERWRITE`;
  any new field on the (eventually populated) table is `option<>` (§1.1/§1.4/§1.6 — migration pin).
- **Style-1 edges (`report → task|agent|finding|report`):** `DEFINE TABLE OVERWRITE <edge> TYPE RELATION
  IN report OUT <task|agent|finding|report> ENFORCED SCHEMAFULL` + `UNIQUE(in,out)` (precedent
  `briefed`/`to`) — §1.1 (relation tables need `OVERWRITE`; `IF NOT EXISTS` is a silent no-op on an
  existing edge table) + §4 (`ENFORCED` guards BOTH endpoints; RELATE with bound RecordIDs; dedupe before
  the RELATE loop since `UNIQUE(in,out)` makes a repeat a loud ERR). These OUT endpoints are real rows,
  so ENFORCED is correct and cannot dangle.
- **Style-2 edge (`report --mentions--> name`):** `DEFINE TABLE OVERWRITE mentions TYPE RELATION IN
  report OUT name SCHEMAFULL` — **NOT `ENFORCED`, NO `UNIQUE(in,out)`** (precedent `refers`/`answers_to`):
  the `name` node is UPSERTed on demand and always exists, so the edge is **order-independent and cannot
  dangle** — this is why #105 does not bite here (contrast a naive `report → code_node` edge, which
  would). Optional `resolved: bool` edge field (like `refers`).
- **Reads:** plain-table SELECTs on the edge tables (§4 — a graph traversal never uses a secondary
  index). "Reports about symbol X" = resolve X via `answers_to`, then `SELECT VALUE in FROM mentions
  WHERE out IN $names` (index on `out`).
- **ONE IMPLEMENTATION:** no parallel embedder (the entity points at the already-embedded chunks); reuse
  the `name` table + `_name_id` + the bound-RecordID RELATE idiom + `_define_relation_table` + the
  per-file DELETE-then-RELATE rebuild (author only the markdown citation-extractor — the AST derivation
  cannot be reused on prose); reuse the `answers_to` bridge for the read; reuse the `story` shape for
  report-`story`; reuse #163's thread mechanism (do not build a second).

---

## PACKET HOME + SEQUENCING
- **Home: packet 28a** (#163 ⊃ #160 — this is its charter). This doc is the Consumer-Law-first design
  28a builds to.
- **Early minimal slice (recommend landing FIRST, cheaply):** the **§2.1 path-derived report LABEL in
  `lore_search`** — it closes **#160** (the standing "chunk arrives without its header" defect), needs
  **no graph** (just a path-derived served-header prefix + a `kind` filter), and is the cheap half of
  #163's sequencing (D1-adjacent). High value, low surface.
- **Shared slice (coordination dependency):** the `report` entity + `report ↔ task` / `report ↔ agent`
  edges are consumed by the coordination doc's close-out checks. **Recommend they stay in 28a**; the
  coordination packet ships its close-out checks against the `report_path` STRING first and upgrades to
  edge-resolution when 28a lands (no hard ordering dependency — the coordination packet is not blocked).
- **The graph body** (`report → symbol/finding` edges + `lore_impact` reports section + report-`story`
  + the thread verb) = the bulk of 28a.
- **Sequencing recommendation:** coordination packet and 28a are INDEPENDENT (neither blocks the other);
  the #160 label slice can precede both. Operator sets priority between "research discovery" (28a) and
  "coordination/reaping" (coordination packet).

## FORKS FOR THE OPERATOR
1. **Report SCOPING mechanism** (the FILTER half of EP1; the LABEL half is cheap and un-forked — a
   path-derived render prefix, recommend shipping it regardless) — a **dedicated `report` tier** (clean
   `tier=` scoping, doubles as #161's separate-semantic-space; costs a `lore.yaml` include/exclude change
   + a one-time re-index of report files) vs a **path-prefix / `kind=report` filter** in `lore_search`
   (no re-index; a new search capability). Lean: tier if #161's "dated records shouldn't share code's
   semantic space" is wanted anyway; path-filter if minimal disruption is preferred.
2. **`report → symbol` derivation source** — durable CITATIONS only (#152/#153 in-tree symbol refs;
   RECOMMENDED — reliable, no NLP) vs additionally fuzzy MENTION-matching (broader recall, noisy). *(The
   dangling/lifecycle fork I raised in the first draft is DISSOLVED — Style-2's `name` indirection makes
   the edge non-dangling and re-derivation-free by construction, §3.2. No fork remains there.)*
3. **The report-traversal surface** — fold "reports about X" into `lore_impact` (RECOMMENDED flagship:
   the reports section) and/or `lore_map` vs a NEW `lore_reports(about=…)` tool (a surface change with
   registration pins).
4. **Thread ordering** (inherited from #163's own forks) — chronological (the correction-chain case:
   #93→#102→#107→#124→#144) vs relevance-ranked vs a parameter.
5. **Report-`story`** — build it (mirror the task story) now vs defer (the traversal + labeled search
   may already cover the discovery need; story mainly serves the SECONDARY citation pattern).
