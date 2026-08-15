# REPORT — design-sidecar-47a (Fable design sidecar, packet 47a)

brief-base v14 read · brief project v7 read

**Role:** long-running design sidecar + escalation valve for packet 47a. Read-only/advisory —
I produce recommendations, not code or tests. This file is my durable consult record; each
question appends a section. Reply-to-lead is via SendMessage (sanctioned sidecar receipt),
but the reasoning lives HERE so it has a durable address.

**SUMMARY BLOCK**
- state: standing-by (Q1 answered)
- Graded: reasoning against `0bdc611` · HEAD-at-report `0bdc611` · SAME
- Packages considered: none — no mechanism specified (advisory only)
- Reuse ledger: none — advisory only, no new symbols
- decisions-needed: none from me — Q1 is a design/judgment fork I am answering; operator
  owns any importance-level override.
- receipt pointers: Q1 answer → §"Q1 — SIZING" below; design doc §8 (split pricing),
  §Q3.1/§Q6 (cross-phase coupling), §Q3.4 + §Q6 DDL (the two straddle problems in the cut).

---

## Q1 — SIZING: split 47a into 47a/47b, or one cohesive TDD cycle?

### RECOMMENDATION: **SINGLE cohesive TDD cycle** (do NOT split 47a/47b), with a ⅓ emergent
reserve and an internal phase-boundary commit. This agrees with the lead's lean — the extra
value below is (1) three concrete reasons the coupling is load-bearing, (2) **two places where
the proposed cut line is not even internally coherent**, and (3) the fallback that makes SINGLE
strictly dominant: you can split at the same seam *later, only if forced*, but you cannot
cheaply un-split.

### Why the coupling is real, not stylistic (weighing point (a))

1. **Phase-2 is defined by READING phase-1's committed output, and the crown-jewel pin is
   end-to-end by construction.** `resolve_edges` "reads committed phase-1 nodes to resolve each
   edge's endpoints" (§Q3.1). The F1 cross-book newer-wins fixture (§Q6) is specified as
   *"run a FULL sweep; assert the edge now points at the new node"* — a full sweep IS phase-1 +
   phase-2. That pin, the single most important correctness proof in the packet (edition
   supersession = full-sweep re-resolution), **cannot exist in a phase-2-only packet** without
   47b rebuilding the entire phase-1 ingest path as its precondition. A 47b that instead
   hand-builds node rows to test `resolve_edges` in isolation is testing against a *fiction* of
   phase-1's output — precisely the "test environment is a fiction" gap CLAUDE.md was written
   over (#107/#131).

2. **The fake-domain scaffold is one object per phase, not two.** `FakeIngestExtension`
   implements all five seams; `FakeDomainStore` defines both `fake_node` (phase-1) and
   `fake_link` (phase-2) in ONE `ensure_ready`. And `entity_fragment` (phase-1) already parses
   *edge intents* it does not emit — the intent-persistence design straddles the boundary and
   only pays off in phase-2. A split forces one of two bad shapes: build the whole fixture in
   47a (dead phase-2 scaffolding, unused ENFORCED table) or re-open the fixture contract in 47b
   (its adversary must re-grade the entire node fixture to grade `resolve_edges`). Either way
   the fixture is not cut — it is duplicated or re-absorbed.

3. **The split is strictly SEQUENTIAL — it buys zero parallelism.** Because phase-2 reads
   phase-1's committed nodes, 47b cannot build or test until 47a lands. A split here is the
   worst case: all of the coordination cost (a second contract → adversary → build → cold-audit
   pipeline, a re-established fixture contract) and none of the fan-out benefit that normally
   justifies one.

### The proposed cut line is not internally coherent (concrete evidence, beyond (a))

The lead's cut puts these in **phase-1 (47a)** yet they are inseparable from phase-2 objects:

- **The dirty-store ENFORCED migration pin (§Q3.4)** is listed under phase-1
  ("...dirty-store-migration pins"), but it tests `DEFINE TABLE OVERWRITE fake_link ... TYPE
  RELATION ... ENFORCED` — the **relation** table, which is phase-2's own object. You cannot
  test ENFORCED-migration on `fake_link` in a 47a that does not build `fake_link`. This is the
  #107-shape pin — the one pin no virgin-DB test can produce — and the cut orphans it at the
  seam.
- **The slug-leading index F6 (§Q6)** is listed under phase-2, but it is an index **on the
  phase-1 `fake_node` table** (`FIELDS slug, source_book`), motivated by phase-2's book-agnostic
  slug resolution. It lives on the phase-1 table and serves a phase-2 read. It belongs to
  neither half cleanly.

Two of the packet's load-bearing pins sit *across* the proposed boundary rather than on one
side of it. That is the tell that the phase-1/phase-2 seam is a boundary in the *runtime
lifecycle*, not in the *test surface* — and TDD cycles are cut along test surfaces.

### Coordination overhead vs. coupling cost (weighing point (b))

A second full pipeline has real fixed cost (contract author + Opus contract-adversary + Opus
builder + cold audit + lead orchestration + a re-established fixture contract). It pays for
itself only when the two halves are independent test surfaces graded by independent adversaries.
Here they are not: the hardest correctness — F1 cross-book supersession, the phase-1↔phase-2
atomicity **window bound** (§Q2.3/R1), the chunk-skip∧entity-present **conjunction** (§Q2.3
frontier-1) — is exactly the cross-phase behavior. Split it and each cross-phase pin lands at
the seam where "the rider is part of the ruling" fails hardest: two contract authors each assume
the other owns it. **One contract, one adversary owning the whole two-phase ENFORCED lifecycle**
is where this packet's rigor should concentrate — that is right-sized rigor, not less of it.
Running two pipelines over an un-separable surface is the *over*-machining failure (my own
memory: right-size-rigor-to-importance), the mirror of under-verifying.

### The 0.25 target and the reserve (weighing point (c))

0.25 is a guideline; §8 already priced the BUILD at 0.32–0.38 *knowing* the split from design
(47) had happened, and the design author — closest to the material — presented 47a as one build
unit, not two. With a ⅓ emergent reserve (~0.5) this is a large packet, but a BUILD packet for a
genuinely novel mechanism, where the thinking is front-loaded into the contract (building to a
good contract is comparatively mechanical, CLAUDE.md). Manage the size WITHIN one cycle, not by
splitting the pipeline:

- **Author the contract in two labelled sections** (phase-1 pins; phase-2 pins) so the adversary
  can attack each while still owning the cross-phase pins as a unit.
- **Builder implements phase-1 RED→GREEN → COMMIT at the natural boundary → phase-2 RED→GREEN →
  COMMIT** (CLAUDE.md "commit at natural boundaries"). This delivers the split's *incremental
  verification* benefit with none of its fixture-duplication or second-pipeline cost.

### The decisive asymmetry (why SINGLE dominates)

If the builder's context genuinely exhausts mid-cycle, phase-1 is already committed and green at
the natural boundary, and a **fresh builder can resume at phase-2 against real committed
phase-1 nodes** — the split, realized on-demand *only if forced*, at the same seam, for free.
The reverse is not true: pay for two pipelines up front and you cannot recover the coupling you
severed. SINGLE keeps the split option alive at zero cost; splitting now spends it whether or
not it was needed.

**Bottom line:** SINGLE. The two-phase ENFORCED edge lifecycle is one test surface with one
fake-domain fixture and one end-to-end sweep; the proposed cut orphans the #107 dirty-store pin
and the slug-leading index at the seam; the split is strictly sequential (no parallelism) and
puts the crown-jewel cross-phase pins where they are most likely to be dropped. Hold it as one
cycle with an internal phase-boundary commit as the on-demand escape hatch.

---

## D1 — P14 access path: how do watcher._purge / reconcile._purge_file reach the claiming extension?

**Grounded live at `0bdc611`.** The `code_graph` precedent is unambiguous and it **contradicts**
the contract-47a P14 fixture's `self._indexer._extensions` assumption.

**Ground truth (the graph slice — the exact thing §7 says to clone):**
- `LiveWatcher.__init__` (`loremaster/index/watcher.py:590`): `code_graph: Any = None` — a **direct,
  optional, keyword-only** ctor param → `self._code_graph`.
- `ReconcileEngine.__init__` (`loremaster/index/reconcile.py:97`): `code_graph: Any = None` →
  `self._code_graph`.
- `LiveWatcher._purge` (`watcher.py:1027`): `if self._code_graph is not None:
  fragments.append(self._code_graph.purge_file_fragment(tier, rel_path))` then
  `await self._store.apply(fragments)` — the graph purge composes into the **same atomic apply**
  as store/file_text/manifest deletes. Reconcile mirrors this (its `__init__` holds
  `self._code_graph`; `test_reconcile_deletion_sweep_purges_graph_slice` confirms the injected
  graph is what purges).

**The clinching precedent:** the **Indexer also holds `code_graph`** (§Q4:
`Indexer(..., code_graph=code_graph)`), so watcher/reconcile *could* have reached
`self._indexer._code_graph` — **they deliberately do NOT; they take their own direct injection.**
The codebase already faced this exact fork for the graph slice and chose direct injection over
reach-through-indexer. The symmetric answer for the entity slice is the same.

### RECOMMENDATION (D1): clone the precedent — direct ctor injection; the contract's P14 fixture is WRONG and must change

1. **Holder = a NEW optional keyword-only ctor param on BOTH `LiveWatcher.__init__` and
   `ReconcileEngine.__init__`**, defaulting empty (`extensions: Sequence[Extension] = ()` — match
   the Indexer's chosen default and name from §Q1.2 so all three extension-holders are identical),
   stored as `self._extensions`. **NOT** `self._indexer._extensions`.
   - Rejecting `self._indexer._extensions`: (a) asymmetric with the graph slice the design says to
     clone; (b) reaches into Indexer **privates** from a sibling collaborator, breaking the
     injected-collaborator pattern the code_graph wiring establishes; (c) the graph slice already
     rejected this exact shortcut.
2. **`_purge` composes the claiming extension's `entity_purge_fragment(tier, rel_path)` into the
   SAME `self._store.apply(fragments)`** — byte-for-byte the code_graph shape (append-to-fragments,
   one atomic txn per file; preserves the §Q2 one-composed-txn atomicity).
3. **⚠ The claim-exclusivity dispatch is now POLICY at THREE sites** — `Indexer._entity_fragment`,
   `watcher._purge`, `reconcile._purge_file` — each needing "given (tier, path), find the ONE
   claimant (loud error on two, §Q1.2)". Per ONE IMPLEMENTATION (#102/#120): **extract that
   decision into ONE shared helper** (e.g. `claiming_extension(extensions, tier, path)
   -> Extension | None`) that all three call — never re-clone the loop at each site. A build that
   injects the list to all three but hand-rolls the exclusivity check at each is the "routing ≠
   sharing" trap. **Prove by mutation:** change the exclusivity rule (e.g. make two-claimants
   raise) and all three sites' pins must redden.
4. **The P14 fixture must be corrected** to inject the param, cloning the graph test verbatim:
   `test_watcher_delete_purges_graph_slice` (`tests/test_graph_wiring.py:361`) constructs
   `LiveWatcher(..., code_graph=trio.graph)` and `ReconcileEngine(..., code_graph=trio.graph)` —
   the entity fixture does the identical thing with `extensions=[FakeIngestExtension()]`. The
   current `self._indexer._extensions` fixture pins an asymmetric, wrong access path — this is a
   contract defect to fold, not a builder choice.

Agrees with the lead's lean ("clone the code_graph precedent exactly"); adds that the contract's
current assumption is the *opposite* of the precedent and must be corrected, plus the
ONE-IMPLEMENTATION rider on the (now 3-site) claim-dispatch.

---

## D2 — P20 IndexSummary.scopes_failed shape: collection-of-ids vs bare int?

**Grounded live at `0bdc611`.** CONFIRM the contract's **collection-of-scope-identifiers**
reading. It is not merely defensible — it is the **established idiom of the very class**.

**Ground truth (`IndexSummary`, `loremaster/index/indexer.py:335`, `model_config
extra="forbid"`):** the class already carries BOTH shapes —
- counts: `files_indexed: int`, `files_failed: int`, `files_skipped: int`
- **collections of identifiers: `tiers_rebuilt: list[str]`, `tiers_skipped: list[str]`**

So `scopes_failed: list[str]` is a direct clone of the existing `tiers_rebuilt`/`tiers_skipped`
"which things were affected" pattern — same class, same shape, zero novelty. **Nothing forbids
it.** No operator ruling needed.

### RECOMMENDATION (D2): collection-of-ids, `scopes_failed: list[str]`, default empty

- **Why collection over int (trust doctrine, CLAUDE.md):** failures must be LOUD and a served
  value names the set its label claims. A bare int ("2 scopes failed") is a count with its set
  amputated — the consumer learns *something* broke but not *which book to re-crawl*. The design's
  own word is "list" (§Q3.1/F7); F7's intent is a *per-scope* failure signal. The int is strictly
  less informative and is the "named bound is a FACT (the set), never a disclaimer" anti-pattern.
- **Default empty (the one rider):** `IndexSummary` is `extra="forbid"` with multiple construction
  sites (real sweeps + the `index_status` manifest rollup + tests). Give the field a default —
  `scopes_failed: list[str] = Field(default_factory=list)` — so only the phase-2 sweep-completion
  summarizer populates it and the non-ingest / `index_status` paths inherit `[]` without churn.
  This mirrors how `outcomes=[]` already means "this is a rollup, not a run" for `index_status`;
  `[]` honestly reads "no scopes failed / not applicable", consistent with the existing convention.
  (`tiers_rebuilt`/`tiers_skipped` are required-no-default because they're always produced by a
  sweep; `scopes_failed` defaults empty because most sweeps have no failed scope and some paths
  never run phase-2.)
- No design or `IndexSummary` clause forbids it; **no operator escalation required** — the contract's
  reading is faithful to both the design's "list" and the class's own idiom.

---

## Design gaps (adversary REPORT-adversary-47a.md) — DG1/DG2/DG3, grounded live at `0bdc611`

For each: **does my resolution stay WITHIN ruled Q1.1/Q3.1 intent (lead proceeds), or CHANGE the
ruled seam surface (operator checkpoint)?** Verdicts up front, then the grounding.

| gap | resolution | verdict |
|---|---|---|
| DG1 (entity-table channel) | `IngestBackend.entity_tables()` + store union | **CHANGES seam surface** (adds a method to the §Q1.1 IngestBackend Protocol) → operator checkpoint, **recommend APPROVE** (compelled gap-fill: §7's ruled sink-purge is unimplementable without it) |
| DG2 (resolve_edges labeling) | `resolve_edges -> list[ResolvedScope]` | **CHANGES seam surface** (alters the §Q1.1 `resolve_edges` return type) → operator checkpoint, **recommend APPROVE** (compelled: F7 + confirmed D2 are unsatisfiable with bare fragments) |
| DG3 (phase-2 hook location) | hook union {`index_all`, `rebuild_all`, `reconcile.reconcile`} via ONE shared driver | **WITHIN ruled Q3.1 intent** (internal orchestration; no Extension-facing signature change) → **lead PROCEEDS**; correct the doc's `_sweep_two_pass` naming |

### DG1 — the entity-table info channel to the `delete_by_tier` sink

§7 RULED the tier entity-purge lives INSIDE `SurrealStore.delete_by_tier` (the sink, covering all
5 callers). It did NOT specify how the generic store learns which tables are entity tables. The
gap is real: `SurrealStore` is generic infra with no channel to an extension's DDL.

**Recommendation — adopt the lead's lean, backend-method form:**
- `IngestBackend.entity_tables() -> Sequence[str]` — a **backend** method, not an Extension
  method. The backend OWNS the DDL (it defines `fake_node`/`fake_link` in `ensure_ready`), so it
  is the authority on its own table names; an Extension method would be a step removed from the
  schema it must stay consistent with.
- `build_app_context` unions them across `server.extensions`' backends into a `frozenset[str]` →
  `SurrealStore(..., entity_tables=...)`; `delete_by_tier` iterates that set:
  `DELETE <table> WHERE tier = $tier` per table (node rows; **edges cascade** via node delete —
  store ref §2/§4, so `fake_link` needs no explicit tier-delete).
- **⚠ Contract RIDER (a checked assumption, not a silent one):** a table declared via
  `entity_tables()` MUST carry a `tier` field, or the generic tier purge cannot scope it. The
  fixture pins that `fake_node` has `tier`; a declared table lacking it is a loud contract
  violation. Without this, the store's `WHERE tier=$tier` silently no-ops on a mis-declared table
  (a false clear — the #107 shape).
- **Alternative considered + rejected:** a backend-built `delete_by_tier_fragment(tier)` keeps the
  store fully domain-agnostic, but it adds MORE seam surface (a fragment-builder method) and
  contradicts §7's explicit "delete_by_tier runs a single-statement `_query`, separate txn, need
  NOT be atomic with the chunk delete" note. The names-set form is the lighter, ruling-faithful
  choice.

**Why operator checkpoint:** this literally adds a method to the §Q1.1 IngestBackend Protocol =
a seam-surface change by the lead's own dichotomy. But it is COMPELLED — §7 already ruled the
purge goes in the sink, and the sink cannot act without the table set. So it is the *realization*
of a ruling, not a new design direction. Frame it to the operator as "notify + approve", not a
fork.

### DG2 — resolve_edges must return scope-LABELED fragments

Confirmed: my D2 (`scopes_failed: list[str]`) is UNSATISFIABLE against the ruled
`resolve_edges -> list[TxnFragment]` — the indexer sees only a fragment's list POSITION, so it can
report `'1'` but never `'B'`. F7's whole point (name WHICH book to re-crawl) and D2 are coupled:
both need the scope label to travel WITH each fragment.

**Recommendation — change the return type to a named frozen type:**
- `resolve_edges(ctx, changed_scopes) -> list[ResolvedScope]` where
  `ResolvedScope` is a frozen model `(scope: str, fragment: TxnFragment)`. §Q3.1 already specifies
  a 1:1 scope↔fragment ("ONE purge-then-RELATE TxnFragment PER scope"), so the scope is inherently
  a property of each returned item.
- **Named frozen type over a bare `tuple[str, TxnFragment]`:** self-documenting, matches the
  codebase's typed-model idiom (`IndexSummary`/`IndexOutcome` are pydantic models), and survives
  the §Q3.3-deferred future addition (a per-scope `edges_resolved` marker) without a signature
  churn. A bare tuple is the acceptable lighter fallback.
- The indexer's phase-2 driver records `resolved.scope` into `IndexSummary.scopes_failed` on that
  scope's apply failure (F7).

**Why operator checkpoint:** alters the ruled §Q1.1 `resolve_edges` signature = seam-surface
change. But COMPELLED by F7 (ruled) + D2 (confirmed) — bare fragments make both unsatisfiable, so
it is a necessary consequence, not a new choice. Notify + approve.

### DG3 — the real phase-2 completion points (the design's `_sweep_two_pass` is INCOMPLETE, not wrong)

**Grounded call graph (indexer.py / reconcile.py at `0bdc611`):**
- `index_all` (1163) → `if _sweep_uses_batch_dispatch(): _sweep_two_pass(is_rebuild=False)` **else**
  `_index_all_realtime()` (1183, loops `index_tier` per root → `_summarize`).
- `rebuild_all` (1696) → `if _sweep_uses_batch_dispatch(): _sweep_two_pass(is_rebuild=True)` **else**
  `_rebuild_all_realtime()` (1712, purge+`_walk_and_index` per root → `_summarize`).
- `ReconcileEngine.reconcile` (reconcile.py:121) → loops `self._indexer.index_tier(root)` →
  `_purge_deletions` → builds `ReconcileSummary` (a DIFFERENT type — never touches `_summarize`).

So `_sweep_two_pass` is reached **only in batch mode**; the adversary's realtime reference build
ran `_index_all_realtime`, leaving `_sweep_two_pass` dead — that is why it looked absent. The
design named ONE of several mode-dependent completion points.

**No single low-level convergence exists:**
- `_summarize` is shared by the three Indexer sweep bodies BUT also builds the `index_status`
  manifest rollup (no sweep, no files indexed) — hooking there fires resolve_edges on a pure
  status read. Rejected.
- `index_tier` is per-TIER (called by `_index_all_realtime` and `reconcile.reconcile` per root) —
  fires before other tiers/scopes commit, and resolve_edges(None) needs ALL scopes committed.
  Rejected.

**Recommendation — hook at the ORCHESTRATOR completion of all three full-crawl entries, via ONE
shared driver:**
1. The correct union is **`index_all`, `rebuild_all`, and `ReconcileEngine.reconcile`** — every
   full re-crawl entry. All three can re-walk the claimed static machine tier (a version-stamp
   bump drives `index_all`/`reconcile`; a full re-embed drives `rebuild_all`), so all three must
   re-resolve edges. **The adversary was right to hook `index_all` + `reconcile.reconcile` and
   right to flag the missing `rebuild_all` — the answer is all three.**
2. **ONE IMPLEMENTATION (#102/#120):** the phase-2 driver — for each ingesting extension,
   `await ext.resolve_edges(ctx, None)`, apply each `ResolvedScope` via `self._store.apply` with
   F7 per-scope loud isolation, accumulate `scopes_failed` — is POLICY. Extract it into a single
   `Indexer._resolve_all_extension_edges(...)` called from all three sites (two in `Indexer`, one
   in `ReconcileEngine` via `self._indexer`). Do NOT clone the loop per site. Prove by mutation.
3. **Ordering:** the driver runs AFTER all phase-1 nodes are committed and BEFORE
   `_maybe_stamp_snapshot` in each path (so the snapshot captures the resolved edges). Note
   `_rebuild_all_realtime` stamps internally, so its hook lands inside that method before its own
   `_maybe_stamp_snapshot`.
4. **⚠ Refinement rider (avoids a re-resolution storm):** `reconcile.reconcile` runs on every
   periodic tick; firing resolve_edges unconditionally re-resolves ALL edges each tick even when
   the machine tier was version-stamp SKIPPED (nothing changed). Recommend gating the driver on
   "at least one scope-bearing tier the extension owns was actually rebuilt this sweep" (i.e. in
   `rebuilt`, not `skipped_tiers`) — still full-sweep-triggered, just no-op-skipped. Idempotent
   either way (purge+re-RELATE the same set), so this is cost, not correctness — but on a frequent
   periodic tick the cost is real. Flag for the contract to decide.
5. **Doc-fidelity fix:** §Q3.1 and §8 name `_sweep_two_pass` specifically — correct them to name
   the orchestrator union (the natural-language-surface-no-gate-checks class). Not an operator
   decision; a doc correction.

**Why within-intent:** §Q3.1's RULED intent — "at full-sweep completion, after all phase-1 nodes
committed, resolve_edges(None)" — is preserved exactly. Only the internal call sites change; no
Extension-facing signature moves. Gap-fill, lead proceeds. (`IndexSummary` gaining `scopes_failed`
is additive-with-default on an internal/served rollup, not an extension-seam change — within
intent, D2 already confirmed.)

---

## Cold-audit residuals (REPORT-coldaudit-47a.md, GO) — R2/R1/R5, grounded live at `0bdc611`

| residual | disposition | why |
|---|---|---|
| R2 (HIGH, the fork) | **DEFER to packet 51 + a LOUD fail-fast guard NOW** (option iii, hardened) | cli/scout CAN index the machine tier (grounded), so (ii) server-only is unproven & (i) is speculative over-build; the guard removes the silent-hazard teeth |
| R1 (MED, register pin) | **ADD THE PIN NOW in 47a** — do NOT defer | load-bearing wiring, mutation-no-op stays green = the #131 class this repo has the most receipts against |
| R5 (LOW, DG3 cost-gate) | **ACCEPT the shipped `files_indexed>0` gate** + measure-then-tune re-open trigger | latent + LOW; the literal rider's value is unknowable until a real extension measures it |

### R2 — the cli/scout half-wiring fork (SCOPE call → operator, my rec attached)

**Grounded pivotal fact — cli AND scout CAN index the claimed/machine static tier; "server-only"
is NOT established:**
- `index/cli.py::_run` (cli.py:103): constructs `Indexer(..., extensions=server.extensions)` and
  runs `indexer.index_all()` (walks ALL `effective_roots`, static tiers included) OR
  `indexer.index_tier(root)` for `lore index --tier <machine>`. `main`'s docstring: it is a
  **deploy step**. So `lore index` over a config containing a machine tier WILL walk it, with
  `claims()` live but no backend readied and no `register_entity_tables`.
- `scout.py` (scout.py:660): a **daemon** holding `indexer` + `reconcile_engine` + `watcher` +
  `command_subscriber` with a `_reconcile_task` — it runs reconcile (→ `index_tier` per root) and
  a live watcher over the configured roots. Same half-wiring per the cold audit.

**Options weighed:**
- **(i) complete the full lifecycle in cli/scout now** — REJECT. Replicating build_app_context's
  phase-0 backend-ready loop + `register_entity_tables` + (scout) the watcher/reconcile extension
  wiring across TWO more composition roots is (a) speculative — HOW D&D's machine tier is indexed
  (server-only vs cli/scout too) is a **packet-51 deployment decision** not yet made; (b)
  untestable in 47a (no real ingesting extension); (c) re-blows the size we deliberately protected
  in Q1.
- **(ii) remove extensions= from cli/scout (server-only)** — REJECT as unsafe AND premise-unproven.
  It doesn't make cli/scout SAFE: with `claims()` unable to fire, a machine-tier file is treated as
  NORMAL → **chunked + embedded as prose** (garbage in the vector index) — arguably worse than
  orphaned nodes. And it forces weakening the P8 derived reach-scan to allowlist exempt Indexer
  sites — the enumerate-the-forbidden antipattern (CLAUDE.md instrument-lesson).
- **(iii) defer to 51 with a pinned bound** — ADOPT, hardened (below).

**Recommendation — DEFER the cli/scout lifecycle to packet 51, but add a LOUD fail-fast guard in
47a so the deferral is not a SILENT hazard (trust doctrine + pin-the-miss):**
1. The claim-dispatch (the shared `claiming_extension` / `_entity_fragment` seam) must **RAISE
   loudly if a file is claimed in a context where the claiming extension's ingest lifecycle is not
   complete** — never silently compose an entity fragment against an unready domain. Absent the
   guard the failure is silent: a `CREATE` on an un-DEFINEd table **auto-creates a SCHEMALESS
   table** in SurrealDB (non-strict) — no `ENFORCED`, no indexes — so entities land as silent
   corruption, not a loud error (store ref §1.1 SCHEMAFULL vs auto-schemaless).
2. **Natural readiness signal = the `register_entity_tables` set (R1/DG1).** build_app_context both
   readies backends AND registers entity tables (co-wired); cli/scout do NEITHER. So the guard keys
   on "the store has this claiming extension's entity tables registered" — set on the server path,
   empty on cli/scout. (Rider: pin that register + ready are co-wired in build_app_context, so the
   registration is a valid proxy for "lifecycle complete".)
3. **Inert today** — no ingesting extension exists in prod, so `claims()` never fires and the guard
   never trips (no regression for current dogfooding).
4. **Pin the bound** (a test: an Indexer with `extensions=` but no readied/registered lifecycle,
   fed a claimed file → asserts the LOUD raise) with the **re-open trigger:** *packet 51 dnd-wiring
   MUST either (a) complete the cli/scout ingest lifecycle, or (b) confirm the machine tier is
   server-indexed-only and remove `extensions=` from cli/scout (then re-scope the P8 scan).*
5. This answers the cold audit's sharp Q: `extensions=` stays at cli/scout for reach-scan
   uniformity, but the half-wiring can no longer silently misbehave — it fails LOUD until 51
   completes it. It also keeps 47a small (a guard + a pin, not two more full lifecycles).

**Verdict:** SCOPE decision (which packet owns the cli/scout lifecycle) → operator ruling; my rec
= defer-to-51 + the loud guard now. The guard itself is within 47a scope (an internal correctness
guard on the claim-dispatch seam, not a seam-surface change).

### R1 — register_entity_tables wiring pinned by ZERO tests

**Disposition: ADD THE PIN NOW in 47a. Do NOT defer.** This is the exact CLAUDE.md class with the
most receipts against it:
- The `register_entity_tables` prod wiring (build_app_context unions `entity_tables()` →
  `write_store.register_entity_tables` before `delete_by_tier`) is **load-bearing** — it is the
  mechanism that realizes §7's RULED sink-purge (F5). A no-op mutation of it staying 40/40 green
  (M1) is the **#131 "test environment is a fiction"** class: a wiring that works on the dev host
  but whose absence no test can see.
- "A guard nobody runs is a hope with a filename" / "every audit-caught defect class becomes a
  repo-local invariant test" (CLAUDE.md). An un-pinned load-bearing wiring is half a fix.
- The pin is cheap and mutation-provable: a probe extension with NON-empty `entity_tables()`,
  driven through the **real build_app_context path**, then a tier rebuild → assert its entity rows
  are purged through the register wiring; mutation: no-op `register_entity_tables` → pin reddens.
- **Don't-kick-the-can (CLAUDE.md):** the cold audit found it, it's cheap, and it's the 47a build's
  OWN wiring — fix it in the session that found it. Deferring an un-pinned load-bearing wiring is
  the anti-pattern the "fix it now" law names.
- **R2 interaction:** this pin proves the SERVER path's register wiring (the path we keep
  fully-wired) AND the same registration set is the readiness signal R2's guard keys on — so the
  pin is doubly load-bearing.

### R5 — the DG3 reconcile cost-gate (`files_indexed>0` vs the literal owned-tier rider)

**Disposition: ACCEPT the shipped `productive = files_indexed > 0` gate for 47a; record the literal
rider as a measure-then-tune deferral with a named trigger.**
- The shipped gate meets the PRIMARY purpose of my DG3 rider — no phase-2 re-resolution on a pure
  no-op sweep (the re-resolution-storm-every-periodic-tick concern).
- The residual (re-resolving all edges when an UNRELATED tier changes) is **latent** (no ingesting
  extension today → resolve_edges is a no-op regardless) and **LOW** (idempotent purge+re-RELATE;
  bounded by the machine tier's edge count).
- Tightening to the literal "an owned scope-bearing tier is in `rebuilt`, not `skipped_tiers`"
  needs the extension→owned-tiers mapping in the gate — more machinery for a LOW latent cost.
  **Right-size-rigor:** don't over-machine a latent LOW path; and the tightening's value is
  **unknowable until a real extension provides an edge-count/frequency measurement** (measure-then-
  tune, the legitimate deferral shape #1).
- **Re-open trigger:** if a real ingesting extension shows measured re-resolution cost on
  unrelated-tier sweeps, tighten the gate to owned-tier-rebuilt (my original rider stands as the
  eventual target). Record it as a one-line note at the gate so the next engineer meets it
  deliberately.

**Net for the operator checkpoint:** R2 → defer-to-51 + loud guard now (scope call, my rec);
R1 → pin now (not a scope call — just do it); R5 → accept + measure-then-tune trigger.

---

## R2 guard placement — A (`_entity_fragment` sink) vs B (narrower `_compose_file_fragments`)

**Verdict: BLESS A (the sink), reject B — this is reach-law parity with §7's F5 decision made in
THIS packet, and B is not merely a layering preference: as a single narrower site it is
CORRECTNESS-INCOMPLETE for batch mode.** Two refinements below make A clean.

### Why A, decisively

1. **Reach-law parity with §7 F5 (the clincher).** §7 put the entity PURGE at the SINK
   (`delete_by_tier`) rather than enumerate its 5 callers — "the guard is not a scan over call
   sites, it is a property of the sink every call site must pass through." The READINESS guard has
   the IDENTICAL structure: a claimed file is composed+applied at **≥2 sites** —
   `_compose_file_fragments` (realtime) AND `_commit_batch_file` (batch pass-two), both named in
   the design §Q1.2. A narrower placement must ENUMERATE those compose boundaries, and a 3rd
   compose site added later escapes → silent schemaless-corruption returns. Same six-defeats reach
   lesson (CLAUDE.md); same answer §7 already reached for its twin. Placing the guard at the sink
   `_entity_fragment` (which every claimed-file compose calls) covers all paths by construction.
2. **B is CORRECTNESS-INCOMPLETE, not just a style choice.** Option B as stated (guard at
   `_compose_file_fragments`) leaves `_commit_batch_file` UNGUARDED — a batch-mode `lore index` /
   scout sweep of a claimed file with an unready lifecycle still auto-creates a schemaless table.
   **If P10a (the batch pin) stays GREEN under B, that green is PROOF of the gap, not proof of
   safety.** To make B correct you must ALSO guard `_commit_batch_file` = the enumerate-the-compose-
   sites reach hazard A avoids.
3. **The purity cost is real but SMALLER than the reach gap, and it is inherent, not a mistake.**
   `_entity_fragment` mirrored `_graph_fragment`'s pure None-gate — but `_graph_fragment` never had
   a readiness precondition because `code_graph` is readied in EVERY composition root (cli readies
   it too — cli.py:103). The entity backend is the FIRST collaborator NOT readied in all roots
   (cli/scout skip it — that's the whole R2 fork). So the entity path carries a precondition the
   graph path never did; asserting it at the point of use is a defensible fail-fast pattern, not
   arbitrary impurity.

### Two refinements that make A clean

- **Put the raise in the shared `claiming_extension` DISPATCH seam, not inline in
  `_entity_fragment`'s body.** Per D1, the claim-dispatch ("which extension claims (tier,path), and
  is ingesting it safe?") is the ONE IMPLEMENTATION seam that BOTH compose sites AND watcher/
  reconcile call. Readiness is part of that DECISION, and a decision/dispatch seam is the natural
  home for a raise (unlike a value builder). `_entity_fragment` then stays a thin "ask the
  dispatcher, build if claimed" — the raise propagates but the builder's own body gains no branch.
  This keeps the `_graph_fragment` symmetry as far as the weaker precondition allows AND keeps the
  readiness policy in ONE place shared with the purge sites. (It does NOT un-redden P7/P10a — see
  below — but it is the cleaner layering.)
- **The P7/P10a reddening is the guard CORRECTLY exposing unrealistic fixtures — bless the
  adaptation, but VERIFY discrimination survives it.** P7 (namespacing) / P10a (batch) composed
  claimed files with NOTHING registered — a state that NEVER occurs in production, where
  build_app_context ALWAYS registers entity tables before composing. The author's fix (register the
  ext's tables in `_white_box_indexer`) makes those fixtures PRODUCTION-FAITHFUL — a correct
  fixture repair, not green-seeking tampering — **provided each pin still discriminates its
  original concern after the edit** (P7 still fails a build that breaks `xt_` namespacing; P10a
  still fails a build that breaks batch). Interrogate both: "what wrong build does this still
  catch post-adaptation?" If the answer is unchanged, the adaptation is blessed. Also confirm the
  adaptation went through the CONTRACT (documented in REPORT-contract-harden-47a.md), not a
  builder's silent test edit.

### One alternative pre-empted (why not a wiring-time startup check?)

A startup guard ("extensions threaded but backends not readied → fail at boot") is WRONG here:
cli/scout INTENTIONALLY thread `extensions=` without readying (the deferred-to-51 state), and
lore's own dogfooding threads `server.extensions` with NO ingesting extension. A boot check would
break both even when no machine tier is configured. The guard must fire at the moment a file is
actually CLAIMED (runtime, per-file) — which is exactly the sink. (A startup "any extension with a
non-empty `ingest_backends()` must be readied" check is a fine OPTIONAL belt-and-braces, but it is
a different, complementary guard — not a substitute for the per-file sink guard R2 needs.)

**Bottom line:** BLESS A (sink = `_entity_fragment`, raise sourced from the shared
`claiming_extension` dispatch). Reject B — it leaves the batch compose site unguarded, and covering
both boundaries is the reach hazard §7 already ruled against for the twin purge. Verify P7/P10a
still discriminate post-adaptation; that is the only open check.

---

## R2 guard SCOPE — compose-only (purge sites keep bare `claiming_extension`)

**Verdict: BLESS compose-only. I see no purge-path corruption; adding readiness to the purge sites
would be ACTIVELY WRONG, not merely redundant.** The builder's and lead's reasoning is sound and
principled; confirming it, plus ONE adjacent write-path flag to verify before commit.

### The write/delete asymmetry is the correct dividing line

The R2 guard exists for ONE corruption: a **CREATE** on an un-DEFINEd SCHEMAFULL table
auto-creates a SCHEMALESS table (silent, no ENFORCED/indexes). That hazard is WRITE-specific.
- **Purge = `entity_purge_fragment` = a DELETE.** A DELETE on an un-DEFINEd/empty table is a
  harmless no-op (nothing to materialize, nothing to auto-create — store §5). No corruption. ✓
- **No orphan risk from the no-op purge:** entity rows exist ONLY if a compose SUCCEEDED, which
  (post-guard) happens only on a READY store. On an unready store nothing was ever ingested → the
  purge has nothing to orphan. So the no-op purge never leaves entities behind. ✓
- **Guarding purge would REGRESS cleanup:** `_purge`/`_purge_file` compose MULTIPLE legs into one
  apply (store-delete + file_text-delete + manifest-delete + graph-purge + entity-purge —
  watcher.py:1027). A readiness RAISE on the entity leg would fail the WHOLE deletion cleanup,
  blocking the watcher/reconcile from removing the NON-entity data of a legitimately-deleted file.
  That is a real regression on exactly the unready-store paths (cli/scout) where nothing needed
  entity cleanup anyway. The lead's reasoning is exactly right.

### The wrapper layering is good (better than my literal "all sites")

My earlier "the shared seam that both compose sites + watcher/reconcile call" was about the
claim-DISPATCH being ONE IMPLEMENTATION — NOT about the readiness RAISE riding every caller. The
builder's `ready_claiming_extension` (wrapping bare `claiming_extension`) gets BOTH right:
- **Dispatch stays ONE IMPLEMENTATION at all sites** — every site (compose ×2, purge ×2) routes
  through `claiming_extension`, so CF8's mutation pin still reddens all of them (green preserved).
- **The readiness RAISE is layered only on the WRITE path** via the wrapper — scoping the raise
  precisely to where corruption can occur. This is CLEANER than putting the raise in the base
  dispatch (which would have forced it onto the harmless purge path too). The
  signature-change-impossible constraint (CF8's 3-arg monkeypatch) forced the wrapper, and the
  wrapper is the correct layering regardless. My open check from the prior answer PASSED (all 4
  mutation legs — guard→PIN A, register→PIN B, namespacing→P7, batch→P10a — discriminate).
- **Consistency bonus:** the F5 tier-purge (`delete_by_tier`) ALSO self-gates — on cli/scout the
  registered entity_tables set is EMPTY → it purges no entities → harmless no-op — so it needs no
  readiness guard either. The rule is principled and uniform: **WRITES (CREATE) get the guard;
  DELETES (per-file purge AND tier purge) are self-harmless.**

### One FLAG to confirm before commit (not a blocker) — the phase-2 RELATE is also a WRITE

`resolve_edges` does purge-then-**RELATE**; a RELATE is a WRITE. The DG3 driver hooks it into
`index_all`/`reconcile` — which ALSO run on unready cli/scout stores. So verify it cannot corrupt:
- My analysis says it cannot fire a corrupting RELATE on an unready store: with the compose guard
  active, no phase-1 nodes commit on an unready store → `resolve_edges` reads no nodes → resolves
  no intents → emits NO RELATE (resolve-or-drop, F2). And any failure reading through an unready
  backend degrades to F7 **loud per-scope isolation** (recorded in `scopes_failed`), not silent
  corruption. So no separate readiness guard on `resolve_edges` is needed.
- **CONFIRM (verify, don't assume):** that `resolve_edges` on the no-nodes / unready-backend case
  behaves LOUDLY (F7) rather than silently — i.e. it either emits nothing (no nodes → no RELATE) or
  surfaces a `scopes_failed` entry, never a silent partial. This is consistent with the
  compose-only bless; it just closes the one adjacent write path the purge question doesn't cover.

**Bottom line:** BLESS compose-only — the write/delete asymmetry is the right line, guarding purge
would regress deletion cleanup, and the `ready_claiming_extension` wrapper is the correct layering
(dispatch shared, raise write-scoped). Before commit, confirm phase-2 `resolve_edges` degrades
loudly (not silently) on an unready store — the one adjacent write path.
