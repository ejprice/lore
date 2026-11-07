# SurrealDB Agent Memory (ex-Spectron): what lore should adopt

_Research and design recommendation. Written 2026-11-07 against lore `feat/surreal-unification` @ `74c4f40`
and the vendor docs at `surrealdb/docs` main @ `16046ab` (2026-11-07T12:52+09:00), `src/content/agent-memory`.
Every claim below is dated to those two commits; "today" means 2026-11-07._

## SUMMARY

- **Source open? NO for the service; YES for the thin clients.** The Rust server repo `surrealdb/spectron` is
  404 to us, and there is no public image or crate. Open (Apache-2.0): HTTP clients only, `surrealdb-memory`
  1.0.0b1 (`surrealdb[memory]`) and `@surrealdb/memory`, plus adapters (§4 P1, P2).
- **Deployment: REIMPLEMENT-IN-LORE, selectively. Do not use it directly.** It is SaaS on SurrealDB Cloud;
  self-hosting needs an Enterprise contract. Its embedder is fixed at `gemini-embedding-2`@3072 on every
  deployment, which cannot be voyage-4-nano@2048. Every `remember` makes an LLM call, and there is no
  in-process mode. Using it means sending all memory text to Google and an LLM vendor, plus a second store.
- **Top features for lore, ranked by value/cost:**
  1. ADOPT category lifecycle and drop recall reinforcement (S). lore's `importance` +0.05 per recall ranks
     nothing and saturates: 15 of 16 recalled notes were served at 1.00. Theirs: no reinforcement, daily decay
     (`context` ×0.95, `knowledge` ×0.995, `identity` ×1), `context` expires after 7 days.
  2. ADAPT the provenance rule on supersede (S). A cross-provenance clash never supersedes; it keeps both rows
     and mints an `uncertainty`. lore today lets an experiential note silently close an authoritative one.
  3. ADAPT automatic recall hooks on `SessionStart` and `UserPromptSubmit` (S–M), failing loud where theirs
     fail silent. Do not copy their `Stop` → remember capture.
  4. ADAPT write-time supersession/duplicate candidates (S–M), LLM-free: the agent decides. Their own
     duplicate audit is inactive.
  5. Then: supersession-chain read (S); section expansion for docs tiers (M); traces recording returned
     ids (M).
- **lore code to drop or modify:**
  - DROP: `LocalMemoryBackend._reinforce` and `REINFORCEMENT_STEP` with their pins; the unbuilt
    `recall(lens=…)` parameter (or build it); the never-written `memory_category` (or populate it); the
    Spectron-backend intent.
  - MODIFY: the supersede branch of `remember` (trust rule); `importance` (rank by it or stop serving it, U1).
- **KEEP-LORE:** findings, tasks, comms, briefs, keeps, code RAG, `lore_ref` drift and PDP governance.

## 1. What Agent Memory is

**Product.** Agent Memory is "a memory and knowledge layer for AI agents. It runs as an application tier in front of SurrealDB"
(`index/welcome/what-is-surrealdb-agent-memory.mdx`). It was renamed from Spectron. The env vars are still
`SPECTRON_*`, the log target is `RUST_LOG=spectron=info` and the OTEL service name defaults to `spectron`
(`index/enterprise/configuration.mdx` §Observability). It ships as a horizontally scaled Rust service with
four process kinds from one image: API (REST + MCP on one port, default `0.0.0.0:9090`), Worker (ingest +
background passes), Scheduler (exactly one; holds a DB lease) and Management API (REST + gRPC). It connects to
SurrealDB over the network as root (`SURREALDB_CONNECTION`) and needs object storage
(`SPECTRON_OBJECT_STORE_URL`: s3/gs/azure/file) (same page, §Processes, §Storage).

**Hosting and licence.** There are four shared plans (Sandbox, Lite, Standard, Plus), all of them Contexts on
shared SurrealDB Cloud. Enterprise adds single-tenant, self-hosted and air-gapped deployments, priced by
agreement (`index/enterprise/index.mdx`). The docs state no server licence: the server source is not public
(§4 P1). The client SDKs are Apache-2.0 (PyPI `surrealdb-memory` METADATA `License-Expression: Apache-2.0`).
Our open SurrealDB engine has one trace of it, a comment in `surrealdb/surrealdb`
`surrealdb/server/src/cnf/mod.rs` on `METRICS_ENABLED`: "Multi-tenant deployments (e.g. Spectron)…". The docs
name no required SurrealDB version (grep for `3.x`/`4.0` under `agent-memory/` finds nothing relevant).

**Models.** The language-model stages run on Google, OpenAI, Anthropic, Cerebras or OpenRouter. Enterprise adds
`openai_compatible`, and its endpoint must be `https://` (loopback and link-local addresses are always refused).
The built-in Anthropic models are API `claude-opus-4-8`, extraction `claude-haiku-4-5-20251001` and
consolidation `claude-sonnet-4-6`. **The embedding model is fixed: `gemini-embedding-2` at 3072 dims. A
Context's `models.embedding` accepts only this value** (`index/enterprise/configuration.mdx` §Fixed
behaviour). This replaces the 2026-07 memory's "OpenAI text-embedding-3-small@1536". The lock-in remains,
on a different model.

**Data model** (`architecture/eight-pillars-and-categories.mdx`, `reasoning/extraction-pipeline.mdx`,
`reasoning/reconciliation-and-supersession.mdx`):
- A Context is the hard isolation unit, with its own SurrealDB (namespace, database), keys and quotas.
- Inside a Context:
  - `entity` records are keyed `[normalised_type, normalised_name]`. Types come from a closed vocabulary of
    12, and unknown types become `other`.
  - Attributes (`key` / `value`) and relations (subject–label–object triples) hang off entities.
  - `actions`, `instructions` and `uncertainty` are separate record kinds.
  - Sessions and turns hold the episodic transcript.
  - Documents and chunks hold the authoritative side.
  - Three graph-resident trace kinds: `retrieval_trace`, `decision_trace` and `response_trace`.
- Every fact carries the following:
  - `memoryCategory`: `identity`, `knowledge` or `context`. Unknown labels are bucketed to `context`.
  - `source.*`: `kind` is `turn | document | upsert | reflect | elaboration | consolidation`, plus `span`,
    `trust` and `derived_from`.
  - `valid_from` and `valid_until`, `confidence`, and scope.
- The documented invariants: "provenance is mandatory, supersession is non-destructive, and uncertainty is
  representable" (`welcome/how-it-works.mdx`).

**Write path.** `POST /facts` (or `/chat`, or MCP `remember`) creates a session turn. Extraction cuts the text
into 8,000-char windows with a 256-char overlap, at most 10 windows (80,000 chars); text beyond that is
dropped with a warning. It makes one structured-output LLM call per window, then merges. Extraction runs
**synchronously, before the API returns**. Reconciliation is one function in one ACID transaction per write:
- **Entity match** is an exact composite-key lookup. There is no fuzzy or embedding match, no alias field
  and no auto-merge. A `same_as` alias table exists, "but nothing in the product writes to it yet".
- **Same scope, same `source.kind`:** the new value supersedes the old one. This is subject to
  `reconciliation.confidence_floor` (default 0.7), and only when the new value carries a score.
- **Different `source.kind`:** neither value supersedes the other. Both stay live, plus an `uncertainty`
  record.
- **Different scopes** coexist.
- **An explicit negation** closes the row with `valid_until`.
- **Unresolved relation objects** become `unknown`-typed placeholders.
- **On a parse failure** the turn text is still stored (a chunk-only diff). Agent Memory does not use
  last-write-wins.

**Lifecycle** (`mental-model/memory-lifecycle.mdx`, fixed on every deployment):
- **Supersession** keeps history.
- **Decay** runs daily: `context` ×0.95, `knowledge` ×0.995, `identity` ×1. "Recall does not currently
  raise a fact's importance."
- **`context` expiry** comes 7 days after known time. It sets `valid_until` and is checked hourly. Relations
  are exempt.
- **Forget:** the default is soft (expired from recall, kept for audit). `purge: true` hard-erases.
  `POST /scopes/forget` erases a whole subtree. Both need the `memory:forget` grant.
- **Background passes:**
  - Hourly: expiry, consolidation, elaboration, conversation-chunk dedup, document clean-up and trace retention.
  - Daily: decay and document reconciliation.

**Read path** (`architecture/coherence-retrieval-and-tiers.mdx`, `retrieve/hybrid-search.mdx`,
`retrieve/recall.mdx`). A four-tier ladder:
- **Tier 2, response reuse.** Used on `/chat` only. It needs cosine ≥ 0.92 to a prior `response_trace`,
  every cited fact still current, and a 3600 s freshness window.
- **Tier 1, structured seed reads.** Graph key lookups with no LLM. They never answer alone; they seed tier 3.
- **Tier 3, hybrid.** Vector + BM25 RRF (`rrfK` 60, `vectorWeight` 0.5) plus graph hops, RAKE keyword
  bridges, section vectors, personalised PageRank and trace-derived boosts. It searches a 256-candidate
  pool, independent of `k` (default 10, max 50).
- **Tier 4, escalated.** Runs when there are fewer than `k/2` hits, or the top fused score is below 0.40 with
  no cosine ≥ 0.80, or the classifier asks. It does a HyDE rewrite, doubles the pool to 512 and re-ranks.

Further read-path details:
- `/query` returns `hits`, plus `contextHits` that are not counted against `k`: section-expansion siblings,
  neighbouring conversation chunks and tier-1 rows.
- Read modifiers: `lens` (a DNF scope filter), `labels`, `asOf` (known time), `atInstant`, `validFrom` /
  `validUntil`, `include` and `includeDuplicates` (SimHash near-duplicates).
- `/context` returns a pre-formatted prompt block.
- `/profile` returns grouped `selfFacts`, `static`, `dynamic`, `preferences` and `instructions`.
- `--min-trust` is "not supported yet": `/query` does not expose per-hit trust.

**Scoping and governance** (`mental-model/contexts-and-scope.mdx`):
- Scope tags are a DNF of hierarchical paths: OR across clauses, AND within one. Paths must be registered
  before use.
- The chain is key → principal → grants (`memory:read`, `memory:write`, `memory:forget`, `grant:manage`,
  `scope:create`) → scope.
- Keys are attenuated subsets of their principal. A key's scope floor clamps requests.
- `lens` filters by involvement and never widens access.
- Their own documented trap: a grant on `org/acme` does **not** cover `org/acme/team/eng`. A mismatched grant
  makes scoped reads return empty, not refused.

**Surface.**
- REST under `/api/v1/{context_id}/…`, with `Authorization: Bearer sp-…`. Writes send an `Idempotency-Key`
  header (sha256 hex), observed in §4 P2.
- An MCP server at `/mcp` on the same port.
- SDKs for Python, TS, Go, Kotlin, Swift, Dart, Elixir and Haskell, plus adapters for LangChain, Mastra,
  Vercel AI, OpenAI Agents, CrewAI, Pydantic AI and a Claude Code hook.
- The endpoint/tool inventory and the sessions and ingest specifics are in §1a below.

### 1a. Surface specifics

Drafted by a Sonnet extraction pass (scratch `agentmemory/extract-sonnet.md`, every line cited
`relpath:line`). I checked 4 claims against the source; all 4 held: the MCP tool list, the trust
defaults, the Claude Code plugin and the hook table.
- **MCP tools (7)**, Streamable HTTP at `/mcp`: `remember` (→`POST /facts`), `recall` (→`/query`), `context`,
  `reflect`, `forget`, `upload` (→`/documents`, base64) and `inspect` (`entity:` / `trace:` / `document:` refs).
  `remember.infer` is one of `full | triples | preview | none`. `infer: "triples"` writes structured
  `entity{type,name}` + key/value or relation without an LLM (`reference/mcp-tools.mdx`,
  `integrations/mcp-server/tools-reference.mdx`).
- **Default trust by `source.kind`:** `upsert` 0.95, `document` 0.80, `turn` 0.50, `reflect` 0.40,
  `consolidation` 0.35, `elaboration` 0.30 (`index/mental-model/provenance-and-traceability.mdx:31-38`). This
  is a numeric trust. lore's `trust` is a two-value enum (`authoritative` / `experiential`), and the backend
  docstring records the float column as a deliberate retirement.
- **Sessions:** `POST /sessions {scopes, metadata}`. Turns carry roles `user | assistant | system | tool` and
  are added through `POST /facts` (+`session_id`, `role`) or `/facts/batch`. Extraction is synchronous per write;
  each write returns its own `extraction` diff, with no separate diff endpoint. There is no close step, only
  `DELETE`. Assistant turns from `/chat` are stored but not extracted.
- **CLI** `agent-memory` (config `~/.config/spectron/config.toml`). It has **no** serve/start verb, so the
  self-host procedure is not public.
- **Errors:** HTTP status plus `{"message": …}` only, with no machine-readable code field
  (`reference/errors.mdx`).
- **Claude Code integration** (`integrations/mcp-server/coding-assistants/claude-desktop-and-code.mdx`):
  - Plugin `surrealdb/ai-claude-plugin`, which connects over OAuth to the managed `https://mcp.surrealdb.com`.
  - Three hooks: `SessionStart` → `recall` (general memories into context), `UserPromptSubmit` → `recall`
    (memories relevant to the prompt into context), and `Stop` → `remember` (the latest exchange, with
    `infer: "full"`).
  - The hooks "fail open": they exit with no output on an error or timeout (default 8 s).
- **Doc self-contradictions found by the extract** (vendor docs can lie, the #107 class):
  - `reference/agents.mdx:88` lists `/sessions/{id}/chat`; `index/sessions/chat-sessions.mdx:52` says no such
    route exists.
  - `reference/agents.mdx:173` constructs `Memory` without `endpoint` and reads an env var;
    `integrations/sdks/python.mdx:51` says the SDK reads no env vars. The installed `_client.py` `Memory.__init__`
    requires `endpoint` (probe P2 passed it explicitly).

## 2. Capability map

Verdict key: **ADOPT** = replace lore's mechanism with theirs; **ADAPT** = implement their approach in lore;
**KEEP-LORE** = ours is better (evidence given); **N/A** = no counterpart is needed.
Cost: S (≤1 packet-day), M (a packet), L (several packets).

| # | Capability | Agent Memory (docs @16046ab) | lore counterpart (@74c4f40) | Verdict | lore code dropped / modified | Value · Cost · Deps | Conf |
|---|---|---|---|---|---|---|---|
| 1 | **Run it as our memory service** | Closed Rust SaaS. Self-host only on Enterprise. Fixed `gemini-embedding-2`@3072. LLM call on every `remember`. No in-process mode | `LocalMemoryBackend` on our SurrealDB 3.2.4, voyage-4-nano@2048, no LLM on the write path | **N/A (do not use directly)** | none | value nil until a self-host licence and a non-Gemini embedder exist · deps: Enterprise contract, Google + LLM vendor egress | HIGH |
| 2 | **Importance: reinforcement vs decay** | No reinforcement on recall. Daily category decay (×0.95 / ×0.995 / ×1). Fixed rates, fixed everywhere | `LocalMemoryBackend._reinforce` adds `REINFORCEMENT_STEP=0.05` per recall, capped at 1.0. `_hybrid_search` ranks by `rrf_score` only (`_row_score`), so importance affects **no** ranking. Observed: 15 of 16 recalled notes served `importance: 1.00` | **ADOPT** (no reinforcement; category decay) **+ decide importance's job** | DROP `_reinforce`, `REINFORCEMENT_STEP`, the reinforcement pins and the backend docstring promise. ADD a decay pass (or compute it at read time from `created_at` and category; no scheduler needed). Then either fold importance into the final ordering (e.g. `rrf_score × f(importance)`) or stop serving it | HIGH · S · none | HIGH (mechanism), MEDIUM (whether to rank by it) |
| 3 | **Category / retention axis** | `identity` / `knowledge` / `context` decides decay and expiry, separately from content type | `kind` = fact / decision / gotcha / uncertainty / ongoing, which mixes type with retention: `ongoing` has a 7-day TTL via `expires_at` (`ONGOING_DEFAULT_TTL`). `memory_category` column (`store/surreal_schema.py` `_MEMORY_FIELD_SPECS`) is read in `_row_to_recalled` but **never written** | **ADAPT** | MODIFY: derive `memory_category` from kind, or accept it on `lore_remember`. Proposed map: `ongoing→context`; `fact`, `gotcha`, `uncertainty→knowledge`; `decision→identity`. Or DROP the column if #2 is decided without it | MED · S | MEDIUM (the mapping is a design call) |
| 4 | **Expiry** | `context` facts: `valid_until` set at known time + 7 d by an hourly pass; history kept | `ongoing`: `expires_at = created_at + 7d`, filtered at read time | **KEEP-LORE** (equivalent; no scheduler). Optional: render expired rows as closed in history | none | LOW · S | HIGH |
| 5 | **Supersession: provenance rule** | Same `source.kind` → supersede (confidence floor 0.7 if scored). Different kind → both live + `uncertainty`. No last-write-wins | `remember(supersedes=…)` closes the old row with `valid_until` + `superseded_by` in one txn (`LocalMemoryBackend.remember`). The checks are existence and PDP write authority only. **No trust check**: an `experiential` note can silently retire an `authoritative` one | **ADAPT** | MODIFY the supersede branch of `LocalMemoryBackend.remember`: when `old.source.trust == authoritative` and the new trust is `experiential`, write the new row live, **do not close** the old one, and mint a `kind=uncertainty` row that names both ids. The response says so | HIGH · S | HIGH |
| 6 | **Write-time reconciliation / dedup** | LLM extraction plus exact `(type, name)` entity match. Duplicate audit `fsck duplicates` (cosine 0.95) "currently returns no candidates" | Deterministic id dedups identical (owner, text, refs) only. No near-duplicate or contradiction detection | **ADAPT (LLM-free)** | ADD to `lore_remember`: after the write, run the existing hybrid recall over the new text in the writer's scope. Return the live notes above a cosine floor as "possible supersession candidates #id…". The agent decides. Floor calibrated like the weak-match floor | HIGH · S–M · voyage floor calibration | MEDIUM |
| 7 | **LLM extraction of entities, attributes and relations from free text** | Core of the product: one structured LLM call per 8k window, synchronous | None. Agents author atomic notes; the code graph supplies entities (symbols) | **N/A** | none. lore's writers *are* LLMs (CLAUDE.md, the consumer law), so a second LLM re-extracting their deliberate notes adds cost and a new failure mode. Revisit only if lore ingests raw transcripts (#11) | LOW · L · LLM dependency | MEDIUM |
| 8 | **Entity graph / cross-layer linking** | Facts hang on entities. Documents and turns land in one graph | Memory → code via `lore_ref=<chunk_key>@ver` labels with **drift flags** (`RecalledRef.drifted`, chunk-existence oracle) | **KEEP-LORE** | none. Ours links memory to versioned code and flags drift; Agent Memory has no drift concept | — | HIGH |
| 9 | **Uncertainty as a record kind** | System-minted on conflict or weak extraction; stored separately | `kind="uncertainty"`, agent-authored only | **ADAPT** (system-minted, via #5 and #6) | covered by #5 | — | HIGH |
| 10 | **Instructions (behavioural memory, applied at prompt assembly)** | Extracted `instructions`, superseded like facts, served in `/profile` | Briefs: versioned, race-safe, ack coverage, skew notices (`briefs.py` `BriefLedger`) | **KEEP-LORE** | none. Briefs add ack and coverage, which Agent Memory lacks | — | HIGH |
| 11 | **Sessions / turns (episodic transcript)** | First-class sessions and turns; extraction on each turn; `/state` diffs; Claude Code hook adapter | None. Claude Code keeps transcripts in `~/.claude/projects/*.jsonl` | **N/A now** (operator fork, §5 U3) | none | MED? · L · needs an LLM summariser | LOW |
| 12 | **Consolidation / elaboration / reflection (background LLM passes)** | Hourly consolidation and elaboration; on-demand `/reflect` | None (`loresage` enrichment is code summaries, not memory) | **ADAPT consolidation-lite only** | ADD a periodic, LLM-free memory housekeeping report: near-duplicate clusters, supersession candidates and stale `lore_ref` drift. It is filed as a finding or served on `lore_index`. Reflection is N/A: the agent reflects | MED · S | MEDIUM |
| 13 | **Retrieval ranking for memory** | Vector + BM25 RRF + graph + PPR + trace features; 256 pool; k=10 | Vector + BM25 `search::rrf` (`_RRF_K=60`), overfetch ×4; k default 5 | **KEEP-LORE now**; ADAPT trace-fed boosts later (#16) | none now | — | MEDIUM |
| 14 | **Tiered escalation (HyDE, rewrite, re-rank when thin)** | Tier 4: an LLM rewrite when the hit set is thin or low-confidence; reported `tier=escalated` | Weak-match floor plus a hedged absence verdict tells the agent the result is thin (DESIGN-LAW §3) | **KEEP-LORE** | none. Our caller is an LLM that can re-query after an honest "thin" verdict; a server-side HyDE call adds cost and an opaque rewrite (trust doctrine) | — | MEDIUM |
| 15 | **Response cache with entity-aware invalidation** | Tier 2, `/chat` only | lore does not synthesise answers | **N/A** | none | — | HIGH |
| 16 | **Traces as memory** | `retrieval_trace` (candidates, per-signal scores, returned set), `decision_trace` and `response_trace` as graph nodes; they feed the ranker and calibration | `trace` table: tool, params hash, hit count, latency, session (`surreal_schema._TRACE_FIELD_SPECS`). No returned set; not linked to memories | **ADAPT (stage 1 only)** | MODIFY `trace`: record the returned memory ids for `lore_recall` and the search hit keys. Feedback ranking waits on a "was it used" signal, which lore does not have | MED · M | LOW (value unproven) |
| 17 | **Supersession-chain history and time travel** | `GET …/entities/{type}/{name}/history/{key}`; `asOf` known-time, `atInstant`, `validFrom` / `validUntil` | `recall(as_of=…, include="superseded")`; rows carry `supersedes` / `superseded_by` | **ADAPT** | ADD a chain walk (`lore_recall` `history_of=<id>`, or a render of the chain on hits that have one) | MED · S | HIGH |
| 18 | **Forget levels** | Soft expire (default), `purge`, scope-subtree erase | `invalidate` (soft close) | **KEEP-LORE** (single-operator fleet; no compliance driver) | none. Ledger it: purge appears with the first external consumer (CLAUDE.md pre-production re-open trigger) | LOW · S | HIGH |
| 19 | **Scoping, multi-tenancy, principals, grants** | Context = (ns, db); DNF scope sets; principals; attenuated keys; scope floor; `lens` | Per-project DB; `principals.py`, `keeps.py`, `lorerunes.pdp` grants, `governed.py` read_filter / guarded_write, `audit.py` | **KEEP-LORE** (convergent, already built through packet 63c) | DROP or BUILD `recall(lens=…)`. Today it raises `ValueError` ("unsupported in P7") yet stays on the protocol | — | HIGH |
| 20 | **Provenance fields** | `source.kind` + `span` + `trust` + `derived_from`; `decision_trace` names the principal and on-behalf-of | `source{kind,ref,trust}` + `owner_principal` / `owner_agent` + audit trail | **ADAPT (small)** | ADD an optional `derived_from: list[memory_id]` (for consolidation and uncertainty rows from #5, #6, #12) | LOW · S | HIGH |
| 21 | **Calibration / confidence** | Per-value `confidence`; floor 0.7 | none | **ADAPT only with #5** (optional `confidence` on `lore_remember`) | — | LOW · S | MEDIUM |
| 22 | **Document ingest (authoritative stream)** | Multimodal: PDF, OCR, STT, image embeddings; chunk by section; RAKE keywords; `content_hash` + SimHash dedup | Static and live tiers; AST chunking for `.py`; markdown chunker for `.md` / `.mdx` | **KEEP-LORE** for code. **ADAPT section expansion** (`contextHits`) for markdown tiers | ADD sibling-section passages beside ranked hits in `SearchPipeline`, outside `k`, counted and labelled | MED · M | MEDIUM |
| 23 | **Findings / tasks / comms / keeps** | Not offered. Agent Memory is "not … a full agent runtime" | `findings.py`, `tasks.py`, `messages.py`, `briefs.py`, `keeps.py` | **KEEP-LORE** | none | — | HIGH |
| 24 | **`/profile` / `/context` (prompt-ready block)** | Grouped `selfFacts` / `static` / `dynamic` / `preferences` / `instructions`; `/context` string | `brief_get` plus `lore_recall` | **N/A** (briefs cover the session-start load) | none | — | MEDIUM |
| 25 | **Automatic recall via Claude Code hooks** | Plugin hooks: `SessionStart` → recall, `UserPromptSubmit` → recall of memories relevant to the prompt, injected into context. They fail open, silently | None. Recall happens only when an agent chooses to call `lore_recall`. The project CLAUDE.md tells agents to, which is a hope, not an instrument (CLAUDE.md "FILING A RULE DOES NOT INSTALL IT") | **ADAPT** (recall hooks only; NOT the `Stop` → remember capture, see U3) | ADD a `UserPromptSubmit` (and optionally `SessionStart`) hook in the lore-deploy skill. It calls lore's recall over HTTP with a small `k` and a token budget, and prints cited hits only above the weak-match floor. **Fail LOUD in one line**, not silent (trust doctrine: a missing recall must be visible). Opt-out env var like `AGENT_MEMORY_HOOKS` | HIGH · S–M · auth for a non-MCP caller (the hook is a separate process); context cost per prompt must be measured | MEDIUM |

## 3. Recommended implementation plan

**Phase A: honesty fixes. Packet-sized; contract → adversary → build → cold audit.**
1. **Drop reinforcement.** Delete `LocalMemoryBackend._reinforce`, `REINFORCEMENT_STEP` and their pins. Removed-behaviour
   inventory: the stored importance no longer rises on recall. No ranking changes, because importance ranked
   nothing (verified by reading `_row_score`; re-verify with `lore_impact` before deletion).
2. **Give importance one job, or stop serving it** (operator fork U1). Recommendation: adopt Agent Memory's
   rates and compute decay **at read time**: `importance_now = prior(kind) × rate(category)^days_since(created_at)`.
   That needs no scheduler and no write amplification, and it is deterministic. Fold it into the ordering as
   a tiebreak or multiplier, then measure on the eval tasks before keeping the multiplier.
3. **Populate `memory_category`** from kind, using the mapping in §2 row 3 (operator fork U2), or delete the column.
4. **Trust rule on supersede** (§2 row 5). A cross-trust supersede writes the new row plus a system-minted `uncertainty`
   row carrying `derived_from=[old, new]`, and the response names it. Contract fixtures must use BOTH trust
   values on both sides; this is the parameter-monoculture law.

**Phase B: write-time candidates and history. One packet.**
5. `lore_remember` returns the top live notes in the writer's scope above a calibrated cosine floor as
   supersession candidates (§2 row 6). The floor is calibrated on voyage-4-nano like the weak-match floor.
   It is a FLAG, never an auto-merge.
6. Supersession-chain read (§2 row 17).
7. `derived_from` provenance field (§2 row 20).
7b. Recall hooks (§2 row 25): a `UserPromptSubmit` and optional `SessionStart` hook shipped by the
    lore-deploy skill. Gate: measure the added tokens per prompt and the precision of injected hits on a sample
    of real prompts before turning it on by default.

**Phase C: housekeeping and retrieval. One or two packets, after A and B land.**
8. A memory housekeeping report (§2 row 12): near-duplicate clusters, uncertainty rows still open, drifted
   `lore_ref`s and expired-but-referenced notes.
9. Section expansion for markdown tiers (§2 row 22).
10. Record the returned memory ids and hit keys in `trace` (§2 row 16). Ranking feedback becomes a separate
    decision once a use signal exists.

**Not built:** LLM extraction, sessions/turns capture, HyDE escalation, response cache, purge, DNF scope
sets. Each is either an N/A by the consumer law or waits on a named trigger (§5).

**Engine versions:** all of the above runs on our current SurrealDB 3.2.4. Nothing here needs 3.3 or 4.0;
another agent covers engine features. Agent Memory's "system time" clock relies on SurrealDB MVCC history.
lore does not need it for any recommended item.

## 4. Probes run

P1: source openness (2026-11-07):
```
gh repo list surrealdb --limit 300   -> 0 server repos; clients/adapters only (surrealdb.py, surrealdb.js, surrealdb.go,
                                        agent-memory-{crew-ai,google-adk,openai-agents-sdk,pydantic-ai,…}, claude-agent-memory; Apache-2.0)
gh api repos/surrealdb/spectron       -> 404 Not Found      (the URL the surrealdb-memory README links as "Spectron, a memory service")
gh api repos/surrealdb/agent-memory   -> 404 Not Found
curl ghcr.io/token?scope=repository:surrealdb/{agent-memory,spectron}:pull + /v2/…/tags/list -> NAME_UNKNOWN (both)
PyPI surrealdb 3.0.0 extras ["embedded","memory","pydantic"]; surrealdb-memory 1.0.0b1 (Apache-2.0, requires aiohttp, requests)
npm @surrealdb/memory 1.0.0-alpha.11, @surrealdb/spectron 1.0.0-alpha.8 (Apache-2.0, repo surrealdb.js)
crates.io: no SurrealDB-owned memory crate ("agent-memory" 0.1.0 is an unrelated SQLite MCP server)
surrealdb/surrealdb server/src/cnf/mod.rs:475: "Multi-tenant deployments (e.g. Spectron) that do not want to expose…"
```
Raw sweep outputs: scratch `agentmemory/sweep/` (the brief-named scratch dir; not durable).

P2: the SDK is a thin HTTP client; wire capture against a local stub. No SurrealDB and no Agent Memory server
were involved; there was no container to run, because no image is public. Port 19101 was checked free with
`ss -ltn`. The stub ran in-process and stopped at exit. The instrument is pasted verbatim because it backs a
claim:
```python
"""Probe: is surrealdb[memory] a thin HTTP client, or does it embed any memory engine?
Run with the scratch venv:  .venv/bin/python -I probe/sdk_probe.py <free-port>"""
import ast, json, pathlib, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import surrealdb_memory
from surrealdb.memory import Memory
PORT = int(sys.argv[1])
pkg = pathlib.Path(surrealdb_memory.__file__).parent
imports = set()
for f in sorted(pkg.glob("*.py")):
    for node in ast.walk(ast.parse(f.read_text())):
        if isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imports.add(node.module.split(".")[0])
print("modules:", sorted(p.name for p in pkg.glob("*.py")))
print("third-party imports:", sorted(i for i in imports if i not in sys.stdlib_module_names))
seen = []
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        seen.append((self.path, {k: v for k, v in self.headers.items() if k.lower() in ("authorization", "idempotency-key", "x-on-behalf-of", "content-type")}, json.loads(body or b"{}")))
        out = {"tier": "hybrid", "hits": [], "queryMs": 1, "trace": {"traceId": "t1"}} if self.path.endswith("/query") else {"sessionId": "s1", "turnId": "u1", "extraction": {"entities": [], "attributes": [], "relations": [], "actions": [], "instructions": [], "uncertainties": [], "corrections": []}}
        data = json.dumps(out).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self, *a): pass
srv = HTTPServer(("127.0.0.1", PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
m = Memory(context="probe-ctx", endpoint=f"http://127.0.0.1:{PORT}", api_key="sp-probe")
try:
    r = m.remember("Alice is CTO at Acme.", infer="full", scopes=["org/acme/user/alice"], memory_category="identity")
    print("remember ->", type(r).__name__)
except Exception as e:
    print("remember raised", type(e).__name__, e)
try:
    q = m.recall("What is Alice's role?", k=5, lens=["org/acme/user/alice"], as_of="2026-11-01T00:00:00Z")
    print("recall ->", type(q).__name__, getattr(q, "tier", None))
except Exception as e:
    print("recall raised", type(e).__name__, e)
srv.shutdown()
for path, hdrs, body in seen:
    print("WIRE", path, json.dumps(hdrs), json.dumps(body))
dead = Memory(context="probe-ctx", endpoint=f"http://127.0.0.1:{PORT}", api_key="sp-probe")
try:
    dead.recall("x"); print("closed-port recall: returned (unexpected)")
except Exception as e:
    print("closed-port recall raised", type(e).__name__)
```
Output (`surrealdb==3.0.0`, `surrealdb-memory==1.0.0b1`, Python 3.14, 2026-11-07):
```
modules: ['__init__.py', '_client.py', '_errors.py', '_idempotency.py', '_retry.py', '_scope.py', '_streaming.py', '_transport.py', '_util.py']
third-party imports: ['aiohttp', 'requests', 'surrealdb_memory']
remember raised ValueError Missing required field 'mode' for RememberResponse        <- my stub's reply lacked `mode`; the request itself was captured
recall -> RecallResponse hybrid
WIRE /api/v1/probe-ctx/facts {"Authorization": "Bearer sp-probe", "Content-Type": "application/json", "Idempotency-Key": "d65a0042…f88"} {"text": "Alice is CTO at Acme.", "infer": "full", "scopes": [["org/acme/user/alice"]], "memory_category": "identity"}
WIRE /api/v1/probe-ctx/query {"Authorization": "Bearer sp-probe", "Content-Type": "application/json"} {"query": "What is Alice's role?", "k": 5, "asOf": "2026-11-01T00:00:00Z", "lens": [["org/acme/user/alice"]]}
closed-port recall raised MemoryAPIError
```
What P2 shows: the SDK contains no memory engine, no embedder and no SurrealDB client (its only third-party
imports are HTTP libraries). Every capability lives in the closed server. A flat `scopes=["a"]` is sent as
DNF `[["a"]]`.

P3: lore-side reads (2026-11-07, `74c4f40`):
- `LocalMemoryBackend._row_score` returns `rrf_score` only.
- `_hybrid_search` sorts by that score.
- `_reinforce` issues `UPDATE … SET importance = math::min([$ceiling, importance + $step])`.
- `memory_category` appears in `memory/local.py` only as the `_COL_MEMORY_CATEGORY` constant and one read in
  `_row_to_recalled`; nothing writes it.
- The supersede branch of `remember` checks `_row_exists` and `governed.authorize_guarded` only, with no trust
  comparison.
- Live: the two `lore_recall` calls this study made served 16 notes, 15 of them at `importance: 1.00`.
- Tool note: from midway through the study, lore MCP calls failed with ECONNREFUSED (`lore-lore` showed
  `Exited (143)`; I did not stop it and did not touch it), so the later lore-side reads used grep and sed over
  the tree. That fallback is acknowledged here; this read-only study filed no finding.

No pytest was run. No container was created. :18000, :18500 and :18324 were not touched.

## 5. Unknowns and forks for the operator

- **U1 (fork):** importance's job. Option (a): read-time category decay folded into the ranking, measured on
  the eval tasks. Option (b): stop serving importance at all. Recommendation: (a). Agent Memory's docs say decay
  changes importance and that "a decayed fact can still be retrieved". They do NOT say how importance enters
  their ranker; that is MEDIUM-confidence inference.
- **U2 (fork):** the kind → category mapping (§2 row 3). The two readings differ: is `decision` stable
  (`identity`, no decay) or slowly fading (`knowledge`)? I would pick `identity`, because decisions are
  superseded explicitly rather than faded.
- **U3 (fork):** episodic capture, meaning a Claude Code hook that records sessions so memory does not depend
  on agent discipline. Agent Memory ships exactly this, as the "Claude Code hook" adapter and the public
  `surrealdb/ai-claude-plugin`. It would need an LLM summariser (cost L) and conflicts with "atomic facts, not
  digests". Not recommended now. Named trigger: the first measured case of a durable fact lost because no agent
  called `lore_remember`.
- **U4:** the SurrealDB version Agent Memory needs. The docs are silent.
- **U5:** whether a self-host Enterprise licence would allow a non-Gemini embedder. The docs say the embedding
  model is fixed on every deployment, so probably not; HIGH on the docs, unknown on contract terms.
- **U6:** Agent Memory's "Collective" promotion, its trace-fed ranking and its `same_as` aliases are design
  targets, not shipped behaviour (the docs say so for each). Nothing here recommends copying unshipped
  behaviour.
- **Stale memory to supersede:** the lore memory "SPECTRON STATUS UPDATE (2026-07-23)" still says
  "text-embedding-3-small@1536". The current docs say `gemini-embedding-2`@3072. This study did not write lore
  memory: it is read-only, and the lore server was down for the second half. The lead should supersede that
  note.

## 6. Routing table (brief-base v25 §3)

This table was written into this file before the first sweep. The full-document rewrite later overwrote it,
so it is restored here verbatim in substance.

| step | tier | who |
|---|---|---|
| 1 prior context (`lore_recall` ×2, `lore.yaml`) | 3 | me (three cheap calls) |
| 2a current docs sparse clone → scratch | 1 | haiku-worker (done; HEAD `16046ab`, 182 files) |
| 2b doc-tree diff staged 3.3-era vs current | 1 | haiku-worker (0 removed, 42 added, 37 changed of 140) |
| 2c read sessions/ingest/API/MCP/SDK/CLI pages; answer named questions | 2 | Sonnet (`extract-sonnet.md`, 4 claims spot-checked) |
| 2c' read the load-bearing pages (deployment, retrieval, reconciliation, lifecycle, scope) | 3 | me (a sampled draft would miss the mechanism detail the verdicts rest on) |
| 3a source-openness sweep (gh, PyPI, npm, crates, ghcr) | 1 | haiku-worker |
| 3b SDK install + read; P2 probe | 3 | me (the open/closed verdict seals itself if wrong) |
| 4 capability map + verdicts; lore citations | 3 | me |

