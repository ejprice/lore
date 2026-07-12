# External Architecture Review: Dead Reckoning and Spectron Unification

**Reviewed branch:** `feat/surreal-unification`  
**Review date:** 2026-07-10  
**Review method:** MCP-first code exploration using the local `lore-lore` MCP, followed by narrow filesystem scans for negative assertions. MCP navigation friction was reported through `lore_findings` as finding **#88** before filesystem fallback.

## Executive verdict

The project substantially implements the valuable code-intelligence ideas from Dead Reckoning: SurrealDB-native hybrid retrieval, an AST-derived code graph, graph-enriched results, impact analysis, snapshots, function-level diffs, resilient ingestion, and a broad MCP tool surface.

It implements only a deliberately small subset of Spectron. The memory layer borrows provenance, trust, supersession, validity windows, uncertainty records, hybrid recall, and reinforcement, but it is not a full agentic-memory/reconciliation system.

Overall assessment:

- **Dead Reckoning design coverage:** approximately 75–85%
- **Spectron design coverage:** approximately 25–35%
- **“One unified ACID substrate” claim:** mostly, but not literally true
- **Web UI:** not implemented, as expected
- **Production maturity:** strong retrieval/indexing core; incomplete agent, security, trace-feedback, and advanced-memory layers

## Reference architectures

### Dead Reckoning

Dead Reckoning describes five main product capabilities and three architectural pillars: Python ingestion, resumable persistence, versioning, agent querying, visualization, plus a single SurrealDB backend, LangGraph orchestration, and LangSmith tracing. Its six agent tools are hybrid search, impact tracing, version diff, version listing, docstring generation, and issue creation.

Sources:

- [Dead Reckoning repository](https://github.com/atwmarshall/dead-reckoning)
- [Hybrid search inside SurrealDB: one query, vector + keyword + RRF](https://dev.to/atwmarshall/hybrid-search-inside-surrealdb-one-query-vector-keyword-rrf-5ade)

### Spectron

Spectron is broader than “memory in SurrealDB.” Its principles include a unified ACID substrate, first-class provenance and trust, tri-temporal non-destructive history, one reconciler for all fact sources, graph-resident traces, visible cost tiers, pluggable models, deterministic invalidation, and explicit APIs.

Sources:

- [Spectron overview](https://surrealdb.com/docs/spectron)
- [Principles and goals](https://surrealdb.com/docs/spectron/architecture/principles-and-goals)
- [Eight pillars and six categories](https://surrealdb.com/docs/spectron/architecture/eight-pillars-and-categories)
- [Coherence, retrieval, and cost tiers](https://surrealdb.com/docs/spectron/architecture/coherence-retrieval-and-tiers)
- [Traces and memory evolution](https://surrealdb.com/docs/spectron/architecture/traces-and-evolution)
- [Tri-temporal model](https://surrealdb.com/docs/spectron/architecture/tri-temporal-model)

## Dead Reckoning feature comparison

| Dead Reckoning feature | Local project | Assessment |
|---|---:|---|
| Parse Python files into files/classes/functions/imports/calls | Yes | Stronger implementation. Astroid resolves imports, inheritance, and calls to in-project qualified names rather than relying only on Python’s basic AST. See `loremaster/loremaster/graph.py:286`. |
| SurrealDB knowledge graph | Yes | `SurrealCodeGraph` stores per-file node and edge slices transactionally. See `loremaster/loremaster/graph_surreal.py:293`. |
| HNSW vector retrieval | Yes | Implemented on chunk and memory tables. |
| BM25 lexical retrieval | Yes | Identifier-aware full-text search rescues exact symbol/name queries. |
| Native `search::rrf()` fusion | Yes | Genuine single-query server-side RRF with inline subqueries, shared filters, overfetching, and query/DoS limits. See `loremaster/loremaster/store/surreal.py:1239`. |
| Graph-enriched search | Yes | Search results receive bounded reference/signature enrichment after retrieval. The pipeline also supports extension augmentation, memory boosting, and optional reranking. See `loremaster/loremaster/search.py:956`. |
| Blast-radius analysis | Yes | `lore_impact` combines production/test references, direct or transitive consumers, covering tests, and a caveated liveness verdict. This is broader than Dead Reckoning’s `trace_impact`. |
| Resumable ingestion | Mostly | There is no LangGraph per-node checkpoint. Instead, a manifest, eager reconcile sweep, last-good state, command ledger, watcher, and retryable single-writer scout recover interrupted work. Operationally resumable, but architecturally different. See `loremaster/loremaster/scout.py:649`. |
| Atomic per-file ingestion | Yes | Chunk rows, source text, manifest state, and graph slice are composed into one SurrealDB transaction. See `loremaster/loremaster/index/indexer.py:660`. |
| Local path ingestion | Yes | Core behavior. |
| GitHub URL auto-clone | Partial | Source-provider extensibility exists, but the generic core does not expose Dead Reckoning’s automatic GitHub URL ingestion as a first-class built-in workflow. |
| Version snapshots | Yes | Snapshots include Git identity, file hashes, and chunk/window hashes, written atomically. See `loremaster/loremaster/index/snapshots.py:364`. |
| File-level diff | Yes | Added, removed, modified, in-flight, and legacy-precision states are represented explicitly. |
| Function-level diff | Yes | Chunk identity, hash, and `sub_ordinal` provide function/window deltas. See `loremaster/loremaster/diff.py:713`. |
| Version listing | Yes | `lore_diff` without a base lists snapshots. |
| Agent query loop | No | The project is an MCP service, intentionally not a LangGraph agent runtime. Agent orchestration belongs to the MCP client. |
| Thread/conversation checkpoints | No | No equivalent of Dead Reckoning’s LangGraph conversation persistence. |
| Generate docstring tool | No | No implementation found. |
| Raise GitHub issue tool | Partial | The findings ledger supports durable discovery/review state, but direct GitHub/Gitea escalation remains plan-level rather than a shipped equivalent. |
| Streamlit graph/chat UI | No | Known and planned for a later phase. |
| LangSmith nested tracing | No | Local trace rows exist, but not LangSmith spans or full reasoning-chain traces. |
| Local model/Ollama operation | Partial | Embedding backends are pluggable and local deployment is possible, but the system is not packaged around Dead Reckoning’s Ollama agent stack. |

### Hybrid-search fidelity

This is one of the strongest parts of the unification. Dead Reckoning’s core insight is that vector and BM25 result scores should not be normalized together; they should be fused by rank inside SurrealDB using `search::rrf()`.

The local implementation follows that design closely and adds useful hardening:

- One SurrealDB query performs vector retrieval, BM25 retrieval, and native RRF.
- Both arms receive the same scope filters.
- The vector arm embeds the full query.
- Only the lexical arm is safely truncated/token-limited.
- Result count, HNSW overfetch, and `ef` are bounded.
- Invalid filter keys are rejected at the boundary.
- Raw cosine similarity is retained beside the RRF score.
- Empty healthy stores and unavailable stores are distinguished.
- Search then adds memory, extension hooks, optional reranking, freshness markers, and graph context.

This is a faithful and more production-conscious implementation of the Dead Reckoning article’s retrieval pattern.

## Spectron feature comparison

### Core principles

| Spectron design idea | Local project | Assessment |
|---|---:|---|
| One substrate for documents, graph, vectors, records, traces | Mostly | Code chunks, graph, manifests, snapshots, tasks, findings, memories, commands, and traces use SurrealDB. However, memory also writes through to SQLite, so this is not literally one substrate. |
| One ACID transaction per write | Mostly | Per-file indexing and memory supersession are transactionally strong. SQLite memory write-through is outside the SurrealDB transaction boundary. |
| Authoritative vs experiential trust | Yes, basic | `MemorySource.trust` is an enum with those exact two values. See `loremaster/loremaster/memory/backend.py:193`. |
| First-class provenance | Partial | Memory source kind/ref/trust and versioned chunk references exist. Principal, authored time, source confidence, extraction spans, and decision provenance are not modeled at Spectron depth. |
| Non-destructive supersession | Yes | A new memory can close an old record with `valid_until` and link both directions. See `loremaster/loremaster/memory/local.py:484`. |
| Valid-time querying | Yes, partial | `as_of` recall checks `[valid_from, valid_until)`. |
| Full tri-temporal model | No | Valid time is present, but distinct known time and system/MVCC history are not exposed as a three-axis model. |
| Unified reconciler | No | Callers explicitly create memories and may name `supersedes`; there is no extraction/reconciliation engine that detects conflicts and produces decisions automatically. |
| Explicit uncertainty | Partial | `uncertainty` is a supported memory kind, but the system does not automatically generate uncertainty from conflicting or low-confidence assertions. |
| Pluggable models | Yes, relevant subset | Embedders and rerankers are pluggable; the extension surface is broad. Extraction, reconciliation, synthesis, and chat models are not all implemented as independent context-level roles. |
| Deterministic behavior/invalidation | Partial | Deterministic memory IDs, versioned references, drift flags, schema fingerprints, and stale-index handling are strong. Entity-aware response invalidation is absent. |
| OpenAPI/SDK surface | No | MCP is the product surface; no Spectron-style OpenAPI-generated SDK contract was found. |

### Unified-substrate exception

A notable contradiction is `loremaster/loremaster/memory/ledger.py:76`: `MemoryLedger` is explicitly a durable SQLite write-through source of truth. This is pragmatic wipe recovery, but it means the plan’s “one ACID store replaces Qdrant+SQLite+Kùzu” statement is not fully achieved. Qdrant and Kùzu are gone; SQLite remains for memory durability.

The sequence is intentionally ledger-first and then SurrealDB. That protects memories against a SurrealDB failure or wipe, but the two writes cannot participate in one ACID transaction. The system should either document this as an intentional durability exception or replace the SQLite ledger if literal single-substrate unification is a requirement.

### Spectron’s eight pillars

| Pillar | Status |
|---|---|
| Authoritative | Partial: trust label exists; no authoritative document-to-fact reconciliation pipeline. |
| Experiential | Yes at note level: operator memories default to experiential. |
| Reconciliation | No automatic reconciler. Manual supersession is the primitive. |
| Elaboration | No background entity/fact linking process. Code-graph derivation is not the same concept. |
| Reflection | No `/reflect`-style synthesis-to-memory path. |
| Consolidation | No observation aggregation or proof-count history. |
| Calibration | Partial but different: token and retrieval-score calibration exist; fact/source confidence calibration does not. |
| Collective | No corroboration or scope-promotion model. |

### Six experiential categories

Spectron distinguishes episodic, identity, knowledge, context, instructions, and uncertainty. The local project instead uses:

- `fact`
- `decision`
- `gotcha`
- `uncertainty`
- `ongoing`

It therefore implements typed operational memory, but not Spectron’s experiential taxonomy. There are no sessions/turn transcripts, identity profiles, instruction-specific prompt assembly, or automatic context lifecycle.

### Retrieval and cost tiers

Spectron fuses vector, lexical, graph, keyword bridges, document structure, personalized PageRank, geography, and trace-derived features, then routes reads through four cost tiers.

The project implements:

- Vector + BM25 + RRF
- Code-graph enrichment/traversal
- PageRank-style repository maps
- Memory-based candidate boosting
- Optional extension and reranker seams
- Explicit token budgets
- Direct exact-symbol lookup versus semantic search
- A practical tool ladder: map → search → exact read/symbol → impact → verify

It does not implement:

- Automatic four-tier query cascading
- Semantic response reuse
- Entity-aware cache invalidation
- RAKE keyword bridges
- Section/document relation retrieval at Spectron depth
- Personalized PageRank seeded per memory query
- Geographic retrieval
- Trace-derived learning-to-rank feedback

The local tool ladder resembles Spectron’s “cheap first, expensive later” philosophy, but it is client guidance rather than an automatic query planner.

### Traces and feedback loops

Spectron treats retrieval, decision, and response traces as graph nodes connected to the facts and models involved. These traces subsequently affect ranking, calibration, elaboration, and consolidation.

The local project’s `SurrealStore.record_trace` at `loremaster/loremaster/store/surreal.py:733` records:

- Tool name
- Parameter hash
- Hit count
- Latency
- Session
- Optional token cost and model

That is useful operational telemetry, but it is not Spectron-style graph-resident memory:

- No candidate-by-signal trace
- No edges to returned chunks/entities
- No decision trace
- No response trace
- No parent/child reasoning chain
- No ranking feedback
- No correction-driven demotion
- No consolidation/calibration feedback loop

This should be described as **SurrealDB-resident tool observability**, not yet **Spectron trace memory**.

## Extensibility assessment

The home-grown extensibility architecture remains intact and is one of the project’s strongest differentiators.

The `Extension` ABC at `loremaster/loremaster/extension.py:205` exposes eleven safe-default seams:

1. Chunkers
2. XML/JavaScript profiles
3. MCP tools
4. Candidate augmentation and reranking
5. Result/citation formatting
6. Versioned semantic chunk keys
7. Extension-specific configuration
8. Payload indexes
9. Startup/shutdown lifecycle
10. Source providers
11. Detail-level classification

This is materially more extensible than Dead Reckoning’s hackathon architecture. It also provides clean attachment points for future Spectron-like extraction, provenance, reconciliation, and retrieval behavior without forcing those policies into the generic core.

One limitation is that extension discovery is intentionally programmatic rather than package/entry-point based. That is testable and explicit, but it means third-party installation is not yet a zero-configuration plugin experience.

## Architectural strengths

- The SurrealDB migration is substantive and end-to-end across retrieval, graph, manifests, snapshots, tasks, findings, commands, and memory.
- Per-file writes have a well-defined transaction boundary.
- Hybrid search faithfully implements the Dead Reckoning design and adds operational safeguards.
- Index freshness, stale reads, in-flight files, legacy snapshots, elision, and heuristic verdicts are surfaced honestly.
- Exact lookup, semantic search, repository map, impact, verify, read, and diff are separated by intent.
- The graph uses resolved names and test/production distinctions, making impact analysis more useful than a simple calls-edge demo.
- Memory keeps deterministic IDs, source trust, validity windows, supersession, expiry, reference versioning, and drift detection.
- The scout’s LIVE-plus-poll design avoids assuming that database subscriptions are a durable queue.
- The extension interfaces preserve the project’s original domain adaptability.

## Main gaps and risks

### 1. The “single ACID substrate” claim is overstated

SQLite remains a memory source of truth, and the write-through sequence cannot be atomic with the SurrealDB write.

### 2. Spectron terminology risks implying more than exists

The project has Spectron-derived memory records, not a Spectron-like reconciled agent-memory system.

### 3. Trace observability is too shallow for retrieval diagnosis

The current trace cannot determine whether vector retrieval, BM25, RRF, graph enrichment, memory boosting, or reranking caused a poor result.

### 4. No agent action loop

Findings are a good coordination primitive, but Dead Reckoning’s discover → generate suggestion → raise issue flow is not present.

### 5. Cloud authorization is incomplete

Bearer auth and origin checks exist, but OAuth/Dynamic Client Registration, tenant/context isolation, delegated principals, and edge-level scope enforcement are deferred.

### 6. Resumability is repository-state resumability, not workflow resumability

This is appropriate for an MCP indexer, but should not be described as equivalent to LangGraph checkpoints.

### 7. The structural graph is Python-centric

Chunking is extensible across formats, but high-fidelity structural graph derivation is chiefly Python/astroid.

### 8. The plan document is stale in places

It still narrates intermediate P7/P8 states even though the branch has progressed beyond them. A current architectural status document would reduce ambiguity.

## Recommended positioning

Recommended description:

> An extensible, MCP-native code and documentation intelligence platform using SurrealDB for hybrid retrieval, structural code graphs, versioned indexing, operational ledgers, and lightweight provenance-aware project memory.

Avoid describing it as a full merger with Spectron. A more accurate statement is:

> It adopts selected Spectron principles—provenance, trust classes, supersession, temporal recall, fused retrieval, and substrate-resident observability—without implementing Spectron’s full reconciliation, experiential-memory, trace-feedback, or multi-tenant security architecture.

## Recommended next priorities

1. Decide whether SQLite memory recovery is an explicit exception or must be removed to satisfy true SurrealDB unification.
2. Expand traces into per-stage retrieval records linked to returned chunks and memories.
3. Add automatic conflict detection and uncertainty generation before claiming Spectron-style reconciliation.
4. Implement issue escalation from findings if Dead Reckoning action parity matters.
5. Add hosted security and scope isolation before deploying the split MCP role beyond trusted environments.
6. Build the known UI after trace and authorization models stabilize.
7. Rewrite the plan into a concise “implemented / partial / deferred” architecture status record.

## MCP review feedback

The local MCP was effective for:

- Repository orientation through `lore_map`
- Semantic feature discovery through `lore_search`
- Exact implementation retrieval through `lore_get_symbol`
- Store-backed source spans through `lore_read`
- Inspecting graph and test relationships
- Providing stable source citations and freshness information

One navigation issue was encountered: exact-symbol lookup for plausible but incorrect class method names (`SearchPipeline.search` and `Indexer.apply`) suggested unrelated modules rather than listing nearest methods on the already-resolved classes. This was reported through the MCP itself as finding **#88**, category `nearest_symbol_guidance`, before filesystem search was used for negative assertions.

## Review limitations

- This was an architecture and implementation review, not a new full-suite certification run.
- The known unimplemented web UI was treated as expected rather than a newly discovered defect.
- Negative feature assertions were checked with narrow repository-wide text scans after MCP exploration and feedback filing.
- Feature percentages are architectural estimates, not mechanically weighted compliance scores.
