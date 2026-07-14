> **SUPERSEDED (finding #102, 2026-07-13):** `_apply_mint` was deleted; its
> deterministic, id-derived jitter **IS** the defect #102 fixed. Do not use as
> a pattern. See `_txn.execute_transaction`.

brief-base: not applicable (read-only inventory task, no spawn brief). Report follows.

# Plan-doc inventory — lore v2 "DeadReckoning+" (5 RESUME docs)

Receipts are `file:line`. Every `#N` disambiguated as **ledger #N**, **finding #N**, or **old-ledger #N**. "LIVE?" = my confidence it survived the P7–P8d′+SLATE closure wave.

---

## 1. lore-v2-RESUME.md — P7 takeover

**A. Identity.** P7 takeover spec (Memory v2 / MemoryBackend seam + orchestration `task` ledger). Written 2026-07-04 at the P6→P7 boundary.

**B. Still-live obligations**
- **`v1.1` decay sweeps** — memory importance ships with defaults-by-kind + reinforcement-on-recall, but *decay sweeps* are explicitly punted to v1.1 (`:72-73`). LIVE (post-1.0 queue).
- **P9 tier-compare** (old-ledger **#5**, "P9 tier-compare — was #5", `:114-115`). This is the tier-compare feature, NOT the config-dynamism scout. LIVE → P9.
- **Spectron waitlist** — gates the P7 backend *re-decision* only; local backend shipped regardless (`:229`). Open operator item, recurs in all five docs. LIVE.
- **lore-demand_intelligence lockstep surreal config before any recreate** (`:230`) — folded into P8f DI migration; DI was *partially* recreated on migrated config 2026-07-06 (see P8d), so this specific warning is largely spent but the full P8f migration is not.
- lore_map polish P7-vs-P8 fork (`:114-116`, `:231`) — CONSUMED by P8b/P8d map work; not live.

**C. Standing law binding future work**
- **Graph composition invariant (NOT in CLAUDE.md):** graphs must be built *with* `project_roots` (resolution on) + astroid cache reset at sweep boundaries; any NEW composition path must supply both or verdicts drift false-dead; bare-name queries ride the `answers_to` bridge (297194e) — keep fake-vs-real parity pinned (`:222-224`).
- **Recall consumer contract (semantic pin):** the recall→cite→remember loop's chunk-key refs "must not change shape"; only `valid_until=null` rows boost/inject; drift renders `(drifted — re-verify)` (`:76-78`). uuid5 content-derived memory ids = idempotency invariant (`:73`).

**D. Superseded/history.** P6 deploy state, ledger-reconstruction inventory, Memory-v2/task-ledger mission — all built+shipped.

---

## 2. lore-v2-P8a-RESUME.md — P8a takeover

**A. Identity.** P8a takeover (substrate purge: kuzu-shell surgery + Qdrant purge + hygiene + eval baseline). Written 2026-07-04, P7→P8a boundary.

**B. Still-live obligations**
- **Revisit-later TODO — air-gapped opt-out for the hard Anthropic-key boot requirement** "after P8c mileage" (`:110-111`). The hard key requirement shipped (P8c/P8d); the air-gapped *opt-out* was never built. LIVE, no owning phase assigned.
- **DI migration = P8f** — Shape D runbook + `docs/design/2026-07-04-migration-concurrency.md` **§8 operator questions 1–4 unresolved** (`:107-109`). LIVE → P8f.
- Spectron waitlist (`:105`). LIVE.

**C. Standing law**
- **Never delete the shared Qdrant pod** (127.0.0.1:16333, shared with DI) — the purge removes lore's *dependency*, not the pod; binding until P8f-soak cleanup (`:50`).
- Graph `project_roots` + astroid-cache-reset invariant restated (`:92-93`).

**D. Superseded/history.** Kùzu/Qdrant deletion, `_query` hygiene, sanitiser residual, eval-baseline capture — all done.

---

## 3. lore-v2-P8b-RESUME.md — P8b takeover

**A. Identity.** P8b takeover (four additive verbs: lore_verify / lore_read / lore_diff / lore_findings). Written 2026-07-04, P8a→P8b boundary.

**B. Still-live obligations**
- **`raise_issue` stays P9** (`:99`) — the findings-surface `raise_issue` verb was explicitly deferred out of P8b to P9. LIVE → P9.
- **lore's orphaned Qdrant collections** in the shared pod await **post-P8f-soak cleanup** (`:67`, `:148`). LIVE, operator-scheduled.
- DI migration P8f + §8 questions 1–4 (`:147-148`). LIVE (dup of P8a item).
- Idle-gate hook "promotion to project settings.json" (`:38`) — RESOLVED at P8b close (committed @ b53b7a0, `:138-139`). NOT live.
- 8 upstream claude-code issues carrying operator 👍 (50779, 74113, 74112, 70087, 71429, 67165, 73489, 73118) (`:149-150`) — external tracking, not lore work.

**C. Standing law / measurement pins**
- **Eval-harness pin (binds all future eval incl. P9 tier-compare):** MUST reuse `docs/eval/evaluation_harness_p8a.py` + `connections_p8a.py` + the exact pinned model `claude-sonnet-4-5-20250929`; the stock mcp-builder harness is BROKEN vs real MCP servers (TextContent serialization); `evaluation.xml` has **11 pairs, not the plan's stale "23"** (`:74-76`).
- **uv virtual-root idiom:** always `uv sync --all-packages` (also in fresh worktrees); a bare `uv sync`/`uv run` PRUNES member deps and breaks imports (`:121-122`).
- Uniform error posture: every `_query` domain branch classifies + logs server-side + launders (b262ab4/7793eff) — new store code must match (`:123-124`).

**D. Superseded/history.** The four verbs (shipped as 20-tool surface, later flipped to 14), comms-doctrine block (now in global CLAUDE.md).

---

## 4. lore-v2-P8c-RESUME.md — P8c takeover

**A. Identity.** P8c takeover (boot token-calibration engine + config-dynamism scout). Written 2026-07-04, P8b→P8c boundary.

**B. Still-live obligations**
- **ledger #13 — config-dynamism scout disposition table** (`:107-109`): the *table itself* shipped and was RULED accepted as-is (see P8d `:238-243`), but its **approved items are implemented in P8e/P8f**: 5 derive-at-boot fields, the validate-against-reality set, 9-dead-field cleanup, binding hazard guards. LIVE → P8e/P8f. ⚠ This is **ledger #13** (config-dynamism), distinct from **finding #13** (lore-deploy manifest, see file 5).
- **P8d sweep inputs still filed** (`:159-161`): impact.py shares the unsanitised-identity render exposure; `_sanitise_line` + `read_file._resolve_span` "need promotion to public seams"; `lore_references(name)` vs `lore_get_symbol(qualified_name)` param inconsistency; verify polish P2/P3 (path-format hints, empty-string semantics). Most likely consumed by P8d/SLATE — but the `_sanitise_line` promotion is *still referenced as pending* in repo CLAUDE.md ("until finding #34 promotes it"), so at least that arm appears LIVE.
- Verify rebuild-caveat: "Revisit if a harder gate is preferred" (`:154-156`) — small open revisit item.
- Legacy-snapshot GC (`:162-163`) — later EXECUTED (P8d `4e1511b`); NOT live.

**C. Standing law**
- **Single-hot-row N-way txn contention** exhausts the shared 5-attempt retry (43% @ N=8); `findings.py _apply_mint` (bounded app-retry, deterministic id-derived jitter) is the **reference pattern** for any new hot-row minting (`:141-143`).
- **FLEXIBLE-array in-place migration idiom:** a non-option field added to FLEXIBLE array items rejects new writes lacking it while legacy rows survive (IF-NOT-EXISTS never retro-validates) (`:139-140`). (SELECT-missing-col→None and CONTENT-datetime idioms here are already in repo CLAUDE.)
- `smoke_p8b.py` is render-shape-coupled to server.py renderers — render changes must update it in step (`:144`).

**D. Superseded/history.** Calibration engine + dim-gate full symmetry — built, live, receipts in P8d.

---

## 5. lore-v2-P8d-RESUME.md — P8d takeover

**A. Identity.** P8d takeover (THE SURFACE FLIP: 20→14 tools + instructions block + eval A/B gate). Written 2026-07-05, carries a 2026-07-06 chunkers-wiring update.

**B. Still-live obligations** (this doc holds the most)
- **★ Chunker DETECTION LAYER — the operator-agreed queued feature** (`:173-187`), ordering RULED **AFTER P8d** (explicit operator fork). This is the lead's "chunker detection layer" sequencing item. Contract details to preserve: the `identify` package becomes default dispatch authority (.yml≡.yaml, shebang, binary peek); the bcba046 config-override wiring stays as tier-1 operator escape hatch; binaries skipped; prose-ish stragglers → text chunker + **suspect flag** with an **OPEN FORK** (in-text vs metadata+serve-time injection — "open fork for that contract's review", `:182-183`) + WARN in logs/index_status; existing chunker set confirmed sufficient; Chonkie/tree-sitter parked. Own TDD cycle. LIVE — highest-value.
- **finding #11 — dot-less chunkers extension key boots clean but silently never routes** (`:121-122`): "OPERATOR RULING PENDING, default = your work item"; **folds into the detection-layer contract** as fail-loud validation (`:184`). LIVE (rides detection layer). ⚠ finding #11.
- **finding #10 — route-change non-retroactivity**: reconcile skip is sha-based, so a *new* route never re-dispatches unchanged files (DI's 19 yaml needed an explicit `lore_reindex`) (`:118-121`). No resolution recorded → LIVE candidate. ⚠ finding #10.
- **finding #13 — lore-deploy `status` verb reads the LEGACY SQLite manifest** (printed 169 vs true 196; the P8a migration moved the manifest into SurrealDB's file table) — **routed to P8e** (`:123-126`). LIVE → P8e. ⚠ finding #13 (NOT ledger #13).
- **finding #12** — stamped #13-disposition doc row now stale (apply_overrides IS called from prod since bcba046; "annotate, don't rewrite") (`:122-123`). Small; likely done, verify.
- **Inherited findings #1–#4** (`:93-96`), "ALL yours to consume": **#1** tests_for indirect-coverage gap (canonical), **#2** tests_for misses config.py (a *bug*), **#3** references attribute-access granularity gap, **#4** calibration integrity-state string collision. Probably consumed by P8d/SLATE (S2 = map/get_symbol coherence), but **#2 (tests_for/config.py bug)** and **#3** are the ones most likely to have survived a surface-flip that didn't touch tests_for internals — worth a live-status check.
- **P8e scaffold rework** — the post-close scaffold fix (`b8e41a8`) is a *base* P8e builds ON, not instead of; scaffold-defect routing "defaults to the P8e scaffold rework window unless the operator says sooner" (`:242-251`). LIVE → P8e.
- **DI migration P8f** — §8 operator questions 1–4 still open; **`QDRANT__SERVICE__API_KEY` must STAY in lore.env until post-P8f-soak** (DI's live container consumes it — verified) (`:273-275`). Shared-pod orphan cleanup post-P8f-soak. LIVE → P8f.
- Note reconciliation: the "scaffold does NOT template the anthropic block yet (P8e)" worry (`:152-156`) is **superseded** by the post-close template fix (`:247-251`); DI's lore.yaml key gap is the surviving P8f arm.

**C. Standing law binding future work**
- **map-test-segregation is semantic law** — the 2026-07-04 record; map format changes "need a fresh operator decision" (`:199`). Binds all future map work. (Not in repo CLAUDE.md.)
- **SurrealDB two-step table recreate is MANDATORY** (single REMOVE+DEFINE tx conflicts with async HNSW build) AND the window must be lock-excluded from concurrent writers — a raced write auto-creates the table SCHEMALESS and the DDL rolls back (FLEXIBLE needs SCHEMAFULL); ref memory `eea2c3a1` + `memory/local.py::_rebuild_lock` (`:217-220`). Binds any future table recreate.
- **Counting-client error split:** `TerminalCountError` (4xx≠429, stop) vs plain `RuntimeError` (retry exhaustion, retry) — catch subclass to stop, base to retry (`:221`).
- **Never substitute the in-memory engine for the `[real]` test tier** — 29 concurrency/snapshot tests legitimately fail on engine semantics; a down spike-surreal = ~861 loud errors by design, not a regression (`:163-168`).
- (Mandatory mypy/pylint-via-ruff-PL/pydantic gates `:53-71` and the accumulation-flake — both already migrated into repo CLAUDE.md / cured; not re-reported.)

**D. Superseded/history.** The surface flip itself (20→14, shipped), calibration LIVE receipts, P8d′ overflow-valve window, legacy-snapshot GC execution, accumulation-flake cure, two-mypy-error clearance.

---

### Cross-cutting live threads (appear in ≥3 docs, report once)
- **Spectron waitlist** — open in all five; local backend shipped, only the backend re-decision waits (RESUME `:229`, P8a `:105`, P8b `:147`, P8c `:164`, P8d `:273`).
- **P8f DI migration + §8 operator questions 1–4 + post-soak shared-Qdrant orphan cleanup** — every P8x doc.
- **Graph `project_roots` + astroid-cache-reset false-dead invariant** — RESUME `:222`, P8a `:92`; not in CLAUDE.md.
