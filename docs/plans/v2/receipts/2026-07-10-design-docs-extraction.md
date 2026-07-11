brief-base v2 read — read-only inventory, no files touched. Report follows.

---

# Design/spec inventory — lore v2 DeadReckoning+ (as of f0616ed)

Numbering convention used below: **ledger #N** = lore_tasks row; **finding #N** = findings-ledger row. Disambiguated inline wherever a bare "#N" appeared in a source.

---

## docs/design/2026-07-04-map-test-segregation.md
**A.** RULING record + binding SPEC for map tool-surface semantics (2026-07-04 three-model consult; operator-directed). Implemented in P7-tail (ledger #6); semantics declared LAW for P8 (`:4-7`).

**B. Still-live obligations:** None unbuilt — the spec is implemented. Its *forward-binding* clause is a constraint, not a work item: P8/any future map redesign "may change rendering *format*, never these *semantics*, without a fresh operator decision + model consult" (`:5-7`, `:103-105`).

**C. Standing design law (binds all future map/impact surface work):**
- Default map EXCLUDES test nodes from rendering but keeps their edges feeding rank mass; test hubs surfaced via an ALWAYS-RENDERED elision line (`:72-76`).
- `focus=` on a test-shaped node/query AUTO-INVERTS to full test prominence (`:78-79`, named by both models as the non-negotiable safety valve `:57-59`).
- Symbol caps everywhere, but "the cap is never a dead end" — every `+K more` teaches its expansion verb; `focus=` lifts the focused module's cap; cap scales with `budget=` (`:83-92`).
- `lore_impact`: covering-tests join must ride the `answers_to` bare-name bridge (no silent `tests:0`); depth>1 rollups labeled TRANSITIVE (`:94-99`).
- **Do-not-relitigate list** (each rejected with reasons): down-rank-only in a unified list; silent test omission; tag-only fixes (`:108-110`).

**D. Resolved/shipped:** Whole spec shipped in P7-tail (ledger #6).

---

## docs/design/2026-07-04-migration-concurrency.md
**A.** SPEC for a future packet — the v0.3→v2 fleet-migration CONCURRENCY design (2026-07-04, "for operator review"; plan §6 P8 amendment, ledger #11). This is the buildable core of **P8f** (lore-deploy rework + DI migration).

**B. Still-live obligations — this doc IS the P8f migration spec:**
- **§8 numbered operator questions (unanswered, gate P8f entry)** (`:317-333`): **Q1** N1 fail-closed replay — fix v2 to skip-and-log (a) / pre-flight embed dry-run (b) / accept risk; recommends (a)+(b). **Q2** confirm the Surreal upgrader assigns namespace/database only (shared server `:18500`), no per-project surreal port. **Q3** seconds-long Phase-B outage (recommended) vs invest in N5 read-only flag. **Q4** DI first run: full Shape-D live vs dry-run Phases A+GO/NO-GO first.
- **Shape D runbook = the buildable scope** (`:165-271`): Phase A online pre-warm (steps 1–4) → OPERATOR GO/NO-GO (`:208-210`) → Phase B freeze (steps 5–7) → Phase C swap+verify (steps 8–9) → deferred operator-confirmed Retire (step 10). The `lore-deploy migrate` verb automates steps 1–8 + receipts; operator confirms GO/NO-GO, retire, and session reload (`:260-271`).
- **New machinery to build (§7)** (`:275-313`): **N1** align v2 boot replay to skip-and-log OR add pre-flight embed dry-run (~5 lines+test; recommended before fleet run). **N2** public `count()`/health read on `LocalMemoryBackend` for receipts. **N3** `scripts/lore_migrate.py` driver opening both stores against the shared ledger. **N6** the `lore.yaml` additive `surreal:` upgrader + `start` refuse-and-point guard. **N4 explicitly NOT built** (id-diffing makes catch-up incremental — recorded so it isn't re-raised, `:300-302`). **N5** v0.3 read-only flag — optional, NOT recommended (`:304-307`).
- Out of scope, routed elsewhere: the DI DECISIONS.md/GOTCHAS.md doc-content import is a separate per-project content migration the operator schedules (`:6-10`).

**C. Standing design law:** Migration invariants I1–I4 (no acknowledged memory lost; non-destructive until operator retire; no dupes; receipts before trust) (`:37-47`). Endpoint-swap is the LAST data step and the definition of "takes over" — must follow the final replay+parity receipt (`:117-119`, `:158-161`).

**D. Resolved/shipped:** N/A — nothing here is built yet (P8f is future in the forward sequence).

---

## docs/design/2026-07-04-p8-decomposition-rationale.md
**A.** RULING/planning record (Fable, 2026-07-04) — sizing evidence + dependency analysis for the P8a–P8f decomposition. Landed in the plan doc.

**B. Still-live obligations (forward routing for the not-yet-built tail):**
- P8e scope enumerated (`:40`): role wiring + creds, Containerfile/astroid-shadow, operator-approved config-disposition subset, drills, split-topology e2e verification.
- P8f scope enumerated (`:41`): lore-deploy rework + migrate verb + N1/N2/N3/N6 machinery + live DI run + ship close.
- Hard dependency still pending: "Migration design's §8 operator questions (1–4) answered at P8f entry" (`:72-73`).
- Flagged-not-fitting, still-open routing (`:111-120`): DI doc-content import = separate operator-scheduled content migration; **v0.3 astroid installed-vs-mounted fix folded as a VERIFY-then-fix item into P8e's Containerfile wave, "but if it reproduces deeply it may need its own escalation"** (conditional follow-up, `:118-120`); Spectron re-decision invite-gated/unschedulable; §8.8 UI smoke = P10.

**C. Standing design law:** Deployable-checkpoint criterion — each component ends suite-green + cold-audited + committed, most with a live redeploy; instructions block stays fused to the surface flip (`:80-84`, `:92-93`).

**D. Resolved/shipped:** P8a–P8d′ sizing/ordering all executed and closed.

---

## docs/design/2026-07-04-token-survey-results.md
**A.** RESULTS record (2026-07-04) — token-calibration survey summary.

**B. Still-live obligations:** None (deterministic survey output consumed as a constant).

**C. Standing design law / constant:** `CLAUDE_PER_VOYAGE_CEILING = 1.78` = max over projects of token-weighted p95 (lore 1.7041 / odoo 1.7760 / di 1.7291) (`:3-12`). This is the committed measure feeding calibration; per house rule it is re-measured, not assumed, if corpora change.

**D. Resolved/shipped:** Survey complete; constant in use.

---

## docs/design/2026-07-05-p13-config-dynamism-disposition.md
**A.** SPEC for a future packet + operator RULING record — config-dynamism disposition table (scout-13-1, ledger #13, P8c). **OPERATOR RULING 2026-07-05: ACCEPTED AS-IS** — all dispositions adopted; the approved P8e/P8f work list (`:1-11`, `:15`).

**B. Still-live obligations — this table IS the P8e/P8f config work list:**
- **5 highest-value derive-at-boot items to build** (`:89-99`): (1) `exclude_dirs` venv/binary/VCS additive auto-detection [P8e — the field whose staleness caused the DI 3,394-inotify incident; pairs with path-anchored excludes]; (2) `chunkers` — resolve fingerprint-vs-selection lie (derive from hardcoded map OR wire `config.chunkers→apply_overrides`); (3) `embedding.tokenizer` — derive from `model` or drop; (4) `watcher.observer` — derive from platform or drop; (5) `embedding.truncate` — derive from `backend` or make informational. Honorable mention: `server.port` boot free/collision check.
- **validate-against-reality set** to implement (boot assertions): `schema_version`, `project.root`, `embedding.model` (probe `/info` model_id — HAZARD: wrong model + right dim serves wrong embeddings silently), `embedding.max_input_tokens`/`max_batch_texts`, `embedding.{query,document}_prompt_name`, `roots[].path`, `roots[].source`, `anthropic.yardstick_model` (`:27-85`).
- **9-dead-field cleanup** (⚰️ DEAD — wire-or-drop): `embedding.connect_timeout_s`, `embedding.tokenizer`, `embedding.truncate`, `roots[].provider`, `watcher.observer`, `logging.destination`, `search.reranker.url`, `search.reranker.model`, `auth.tls_terminated_upstream` (each with file:line consumer-none receipts in the table).
- **Adjacent scaffold defect raised for operator routing (P8e or sooner)** (`:126-128`): `_scaffold_lore_yaml` still emits a `qdrant:` block and no `surreal:` block (lore_deploy.py:452-454); with `extra="forbid"` a freshly-scaffolded `lore.yaml` **fails to parse → onboarding via `lore-deploy setup` appears broken today** [lead-CONFIRMED against source]. Also must now template the required `anthropic:` block. Scaffold-defect routing "defaults to the P8e scaffold rework window" (`:9-11`).

**C. Standing design law (hazard guards, binding as written per the ruling):**
- `project.slug` derive-at-ONBOARD-only then FREEZE — never re-derive on a live index (cross-project DB clobber hazard) (`:107`).
- `surreal.database`/`namespace` derive strictly from the frozen slug via `effective_surreal_database`; slug charset guard is the backstop; add no other derivation source (`:108`).
- `exclude_dirs` auto-derivation must be ADDITIVE to operator config (union, never replace), LOGGED, and require a real dir-shape signal (e.g. `pyvenv.cfg`) not name heuristics alone (`:112`).
- `chunkers` wiring gated behind explicit operator opt-in; announce the re-chunk in `lore_index_status` before executing (`:113`).
- `surreal.database` is the proven derive-at-boot exemplar/template; `embedding.dim` probe-gate is the validate-against-reality exemplar (`:34`, `:49`).

**D. Resolved/shipped:** `anthropic:` block landed in P8c (`:84-85`). Table analysis complete; implementation is P8e/P8f-forward.

---

## docs/design/2026-07-06-client-needs-consult.md
**A.** SPEC of record for the (now-closed) SLATE cycle + standing client-design-law record + RESULTS record of three closure passes (2026-07-06/07). Operator ruling embedded (`:525-535`).

**B. Still-live obligations:**
- **Round-2 blind-retest residues — NOT listed as closed in the forward sequence; treat as OPEN** (`:646-653`): **finding #84 + #85** (same class, two clients: the PLAIN-bare `get_symbol` miss arm lacks the suffix knowledge the dotted-wrong arm has; the two miss texts can read as contradicting); **finding #86** (confirmed off-by-one in the at-cap visibility clause — "5 of 13" while 4 serve); **finding #87** (`lore_index` cosine_floor reports "measured" while its own file counts disagree, 214 vs 207 — the #74 re-measure-trigger surface needs its accounting verified at source). #87 directly feeds the forward **#83 per-corpus floor calibration** packet. *(Ledger vs finding: all four are findings.)*
- The doc explicitly frames the closure loop as still converging ("the class-informed hunt keeps finding smaller things," `:657`) — i.e. the surface is expected to keep yielding accounting/affordance edges under continued class-informed probing.

**C. Standing design law — the three-way convergences, binding on all surface work (`:449-473`, `:518-523`):**
1. Context/attention is the dominant client cost; **call count is NOT the bottleneck** — the A/B calls-leg is not a client-value metric. Client metrics: signal-per-token, tokens-per-correct-answer, taxed (mechanical) calls (`:450-457`).
2. Counted-elision grammar is the gold standard of limiting; the top-elided SCORE is the load-bearing datum; the re-ask value must be honest/clamped (`:458-462`).
3. Caveats shipped WITH verdicts raise trust; **under-claiming is nearly free, one confident-wrong costs authority for the session (authority→witness, ~doubles calls)** (`:463-466`).
4. Misses must teach a decision tree; silent anything (truncation/zeros/noise-as-hit/crowd-out) is the cardinal failure class (`:467-469`).
5. Strategy+invariants → read-once instructions; recovery moves/capability hints/confidence caveats → embedded per-response (`:470-473`).
- Structured/secondary fields must keep the primary render's discipline (the S1 reversal of the #39-era ruling: over MCP the model IS the consumer) (`:490-495`).

**D. Resolved/shipped:** SLATE S1–S7 all landed/cold-audited/committed (`2499b0c..94a9568`, 21 commits, `:537-579`); P8d/P8d′ CLOSED by operator ruling (`:525-535`); closure-wave findings #74–#78 and self-found #79/#81 fixed and verified in the blind retest (`:628-644`); findings #43/#63/#65/#66/#67/#69 closed alongside (`:571-578`).

---

## docs/design/2026-07-06-weak-match-discrimination.md
**A.** DESIGN RECORD + three-model consult for the weak-match S4b build (2026-07-06; consult ledger row `23af3c9b…`; finding-of-record #68) + close-out RESULTS (2026-07-07) (`:1-6`, `:623-636`).

**B. Still-live obligations:**
- **D4 wire-shape decision — carried to operator, still open** (`:551-557`, `:611-613`): whether to drop / rename (`fusion_rank`) / caveat-only the served fused `score` field. Close-out: "score stays on the wire demoted in render; **rename ledgered**" (`:634-635`) — the rename is a filed-but-unbuilt follow-up.
- **Exploratory signals unadopted, pending their own pre-registered follow-up rules** (`:565-567`, `:636`): source concentration + pre-budget candidate-pool size — measured but "any adoption requires its own pre-registered rule, never a post-hoc threshold."
- **Named future upgrade path:** relative-score fusion (Weaviate relativeScoreFusion / Qdrant DBSF) swap for the SurrealDB arm composition — deferred, ledgered (`:490-491` cross-ref to external-validation doc).

**C. Standing design law (weak-match floor bindings, binding on all search-confidence surface):**
- **No fused-RRF-score floor can ever discriminate** — the fused score is a rank-reciprocal CODE (`search::rrf`, `_RRF_K=60`, surreal.py:228), proven to machine precision (1/61); all magnitude info is discarded at fusion (`:37-67`). C3 (margin) measured INVERTED, C5 (percentile) launders a lie, C4 (arm-agreement) inverted — all three permanently rejected as confidence signals (`:490-496`).
- **Magnitude-or-nothing:** only pre-fusion cosine has a physical basis; the always-on per-hit cosine substrate reads relatively within one response (`:497-502`).
- **Two-tier false-flag asymmetry:** per-hit flags nearly free (10–20% tolerated); the aggregate absence verdict is the guarded surface — precision-first, ≤5% false-fire on real-query union, advisory wording MANDATORY (hardening voids the ruling) (`:503-510`, `:533-541`).
- **D3 carve-out:** verdict fires iff max shown-hit cosine < floor AND no shown hit carries a verbatim-identifier anchor (BM25 magnitude is NOT the gate — topic-word overlap launders wrong answers) (`:543-549`, `:453-457`).
- Constants are MEASURED (committed deterministic survey), never guessed; on the null branch, retire the corpse — no decorative confidence surface (`:511-514`, `:459-463`).

**D. Resolved/shipped:** Executed per §7.4; floor 0.5828, false-fire 4.0%, catch 100% → ADOPTED (commits d4f283f + 94a9568); substrate live; external validation passed (`:623-636`).

---

## docs/design/2026-07-06-weak-match-external-validation.md
**A.** RESULTS record — deep-research external validation of the weak-match design (2026-07-06; 104-agent workflow, 25 claims 3-vote verified). Raw preserved as `research-weakmatch-validation.json` in session scratchpad (`:1-8`).

**B. Still-live obligations:**
- **Element (d) — displaying scores to tool-using LLM consumers = OPEN** (`:63-66`): "No surviving direct evidence either way in the literature or vendor practice"; the three-model informant consult remains the only direct data known. An open research/design question, not adjudicated.
- **Ledgered follow-ups from this validation** (`:70-74`): relative-score fusion evaluation; the floor↔embedder-fingerprint invariant; reranker/utility-predictor as a future calibrated-magnitude layer (Azure semantic ranker path / 110M BERT passage-utility predictor named as candidates, `:56-61`).

**C. Standing design law:**
- **Binding amendment (adopted):** the cosine floor `_COSINE_WEAK_MATCH_FLOOR` is valid ONLY for the exact embedder + prompt configuration it was measured on — **any embedding-model or prompt_name change invalidates it and requires a survey re-run** (`:47-51`). This is the invariant that the forward **#83 per-corpus floor calibration** packet operationalizes.
- The sufficiency notice is justified by documented failure-without-signal, NOT by proven benefit-with-signal (the benefit claim was REFUTED 0-3) — keep the wording honest (`:52-54`).

**D. Resolved/shipped:** Design shipped as specced/measured (floor 0.5828, D3 carve-out, commit 94a9568); 21 of 25 claims confirmed (`:68-74`).

---

## docs/design/2026-07-06-p8dprime-fix-specs.md
**A.** SPEC record for findings #53/#52/#54 (designer-p8dprime, 2026-07-06) — handed-to-builders-verbatim fix specs. All three findings are now CLOSED (part of the P8d′ close), but the doc carries several operator-decision tweaks that were NOT auto-adopted.

**B. Still-live obligations — SPEC 3 §3.4 tweaks still marked OPERATOR-DECISION (`:480-491`):**
- **T7** — raise `lore_search` default budget 1100→~1600 (8/11 gate tasks hit elision at 1100); net token effect ambiguous — **OPERATOR-DECISION** (schema-visible default).
- **T8** — add a `memories=` include/exclude parameter on `lore_search` — **OPERATOR-DECISION** (schema/surface change; may be mooted by T3's memory-segregation render, which shipped).
- **T9** — re-expose `what_imports`/`tests_for` as standalone tools — **NOT RECOMMENDED** (SPEC 1 + T2 cover it), but flagged **OPERATOR-DECISION if the gate re-run still misses the efficiency legs** (`:490`). Conditional follow-up.
- Gate re-run prerequisites (lead-owned) if a re-run is ordered: fix the committed harness import line, rebuild+recreate both containers, re-derive pair 12/13 ground truths live, run 11-pair gate pinned to `claude-sonnet-4-5-20250929` (`:499-506`).

**C. Standing design law:** Reinforces the AST text-hygiene / no-dead-tool-names pin and the sanitiser-seam + hostile-fixture obligations for any new render of stored free text (T2 phrasing constraint `:483`; T3 memory bodies route through the shared sanitiser `:484`). Bare anchor-free sweep grep for retired/doubled names; "all remaining hits are X" is banned output (`:356-358`, `:392`).

**D. Resolved/shipped:** SPEC 1 (#53 from-import references arm), SPEC 2 (#52 canonical map labels + Appendix-A edge-restoration finding), and T1/#54 (13faa6a) all executed in the slate/P8d′ close. Tweaks T2–T6 marked "Ready" and shipped as part of that wave.

---

## docs/orchestration/2026-07-04-agent-comms-failures-research.md
**A.** RESEARCH/RULING record (2026-07-04) — multi-agent comms-failure solutions, verified against upstream issues (Claude Code 2.1.178→2.1.201).

**B. Still-live obligations:** No build packet of its own, but it is the evidence base for the forward **orchestration ledger verbs** packet (durable pull channel + acks). Concrete unimplemented-in-lore candidates it recommends: extend the ledger with an `ack`/`acked_at` column (cheapest, no new server) (`:56`); a lead-side "sent-row older than threshold → re-ping once" check (`:52-56`); optional `TeammateIdle` idle-gate hook (`:70-75`) — the last is already implemented in this repo per project memory, so verify before re-building.

**C. Standing design law (already promoted to global CLAUDE.md; restated here as the source):**
- The busy-agent message-drop is an OPEN, maintainer-unacknowledged upstream bug (#50779) gated on `stop_reason=end_turn`; no upgrade fixes it — the fix lives in the orchestration layer (`:8-9`, `:17-27`).
- Must-not-lose signals travel a durable pull channel; proof = recipient's own artifact, never the inbox `read` flag or SendMessage success (`:46-51`, `:101`).
- Never reuse a teammate name on respawn (pre-2.1.199 silent misroute) (`:64-67`); ground-truth filesystem/git before acting on a bare idle, then re-ping exactly once (`:58-62`).

**D. Resolved/shipped:** Its rules are codified in global + repo CLAUDE.md and MEMORY.md.

---

## docs/orchestration/2026-07-06-orchestration-context-retro.md
**A.** RULING/retro record (p8d-lead Fable, 2026-07-06, operator-directed) — where lead context went + fixes. **This is the design source for the forward "orchestration ledger verbs" packet.**

**B. Still-live obligations — the L-series lore-native candidates = the buildable orchestration-verbs scope (`:60-86`):**
- **L1** — orchestration rollup read (`lore_tasks action=rollup` / a `lore_fleet` view): ONE cursor-based call returning "since <cursor>: N tasks transitioned (ids→states), M findings filed (numbers+subjects), K reports registered (paths)"; rides existing task/finding tables.
- **L2** — batch mutations on task/finding ledgers: create-many (deps wired), transition-many, acknowledge/resolve-many with per-item notes (cuts single-row bookkeeping ~5×).
- **L3** — report registration (`lore_report register/list`): agents register report (path, agent, phase, summary-block); L1 rollup then carries the summary blocks — the durable, compact analogue of completion messages.
- **L4** — bounded await (`lore_tasks action=await`, sibling/ledger condition, timeout): thin read-side wrapper on the LIVE SELECT machinery already scoped for split mode; replaces agent-side bash until-loops.
- **L5 — explicitly NOT recommended:** a push message bus (would recreate the advisory-inbox failure inside lore) — the reviewer is asked to challenge this, but the standing recommendation is durable-pull only (`:81-86`).
- F1–F4 short-term fixes (`:32-52`): F1 structured report contract = brief-base v2 (shipped); F2 spec-pointer briefs; F3 delegated verification mechanics; F4 batch ledger etiquette (interim until L2 lands).

**C. Standing design law:** "Push is the enemy; pull is fine" — the lead's ideal inbound is nothing until asked, then a compact rollup (`:26-28`); content must flow agent-to-agent through disk, not transit the lead (`:24-25`); L1–L3 fit the plan's render doctrine (summarised value objects, never dumps) (`:65-66`).

**D. Resolved/shipped:** F1 (brief-base v2) and F5 (notification discipline) codified; F2/F3 proven in practice.

---

## docs/eval/ — instruments + results

**Markdown (read):**
- **2026-07-04-p8a-baseline.md** — RESULTS record. Standing obligations it pins: the P8d A/B gate MUST reuse the exact pinned harness files and model `claude-sonnet-4-5-20250929` (`:44-49`, `:84`). Two operator-flags raised, not resolved unilaterally: (a) the stock mcp-builder `evaluation.py`/`connections.py` has a `TextContent`-serialization bug that 0/11s any real MCP server — whether to report upstream is an operator call (`:123`, `:126-131`); (b) plan/resume docs say "23-pair harness" but the file has 11 `<qa_pair>` — flagged for operator reconciliation (`:86-94`). *(Now superseded: the 35-pair surface-neutral set is the standing bar per the client-needs ruling.)*
- **2026-07-04-p8a-baseline-raw.md** — RESULTS: full per-task verbatim transcripts of run 3 (11/11 · 5.45 · 1447.1).
- **p8d-flip-eval-raw.md** — RESULTS: 35-task post-flip transcripts (31/35 · 7.23 calls · 1626.8 tok); the raw basis for SPEC 3's per-task delta table.
- **p8dprime-rerun-raw.md** — RESULTS: 35-task rerun transcripts (33/35 · 5.69 · 1374.8) — the current standing-bar receipt.

**Instruments (by filename, bodies not read):**
- `evaluation_harness_p8a.py` — the pinned/patched mcp-builder Phase-4 eval harness (adds `_serialize_tool_result`, per-task token capture); canonical for A/B reuse.
- `connections_p8a.py` — vendored byte-identical MCP-connection sibling of the harness.
- `smoke_p8b.py` — the P8b MCP smoke-test instrument (per repo CLAUDE.md, full mode files a dogfood finding row each run, resolved as a smoke artifact = duplicate of finding #1).
- `__pycache__/` — build artifact, ignore.

**Live-obligation note on eval:** no unbuilt spec here; the standing bar going forward is the **35-pair surface-neutral set graded by accuracy / tokens-per-correct-answer / taxed-calls≈0** (the 11-pair calls-leg is retired), per the client-needs-consult operator ruling.

---

### Cross-cutting: where the forward sequence draws its still-live specs
- **#83 per-corpus floor calibration** ← weak-match-external-validation binding amendment (floor↔embedder+prompt invariant) + client-needs finding #87 (cosine_floor accounting) + the round-2 residues #84–#87.
- **chunker detection layer** ← not specced in these docs (per MEMORY it maps to existing chunkers; spec lives elsewhere).
- **orchestration ledger verbs** ← orchestration-context-retro L1–L4 + comms-failures-research ack/pull recommendations.
- **P8e** ← p13-config-dynamism (5 derive-at-boot + validate set + 9-dead-field cleanup + scaffold qdrant/anthropic defect) + p8-decomposition-rationale P8e scope (roles/creds/Containerfile/astroid-shadow) + the conditional astroid installed-vs-mounted escalation.
- **P8f** ← migration-concurrency Shape-D runbook + N1/N2/N3/N6 machinery + §8 Q1–Q4 operator answers.

One flag for the operator: **findings #84–#87 (client-needs blind-retest round-2 residues) are recorded as newly-filed and are NOT in your "closed" list** — they read as still-open accounting/affordance edges (zero trust-class), with #86 a confirmed off-by-one and #87 feeding #83. Want me to confirm their live ledger state before the packets are drawn?
