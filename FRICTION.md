# Lore friction log

Live dogfood record of every point where an agent (or the team-lead) hit a lore
limitation and worked around it. **Doctrine: if a lore call forces a workaround,
log it here FIRST, then work around.** Entry shape deliberately mirrors the
planned P8 `kind=friction` finding (plan §3 "Friction reporting"), so this file
seeds the findings table when that lands and retires afterward.

Harvest protocol (team-lead): subagent reports carry a `FRICTION:` line when a
lore call disappointed; the team-lead appends entries at each cycle close and
consumes open entries when specifying the NEXT cycle — friction found while
building phase N feeds the design of phase N+1, not a backlog.

Entry fields: date · reporter · tool · intent · what happened
(zero_hits | error | wrong_result | too_stale | distrust_unverified |
capability_gap | affordance_gap) · workaround taken · disposition (open /
consumed-by-<phase or commit> / superseded).

---

## Open

- **2026-07-04 · hygiene-7b (P8a wave 2b) · lore_tests_for · zero_hits/oversized** —
  asked for the covering tests of graph_surreal.py / index/surreal_manifest.py /
  index/snapshots.py while adding posture seam tests: returned empty for some
  inputs and an oversized undifferentiated dump for others (same
  file-vs-symbol input-shape family as the 2026-07-03 tests_for entry and the
  P7 bare-name fix — the file-path arm remains unreliable). Workaround: grep
  for the test files by import. **Feeds:** P8d input-resolution family — the
  file-path arm needs the same answers_to bridge the symbol arm got, or an
  explicit teaching miss.

- **2026-07-04 · hygiene-7 (P8a wave 2) · lore_get_symbol · zero_hits
  (stale on recently-touched file)** — `lore_get_symbol('loremaster.tasks._query')`
  returned not-found for a symbol that exists (tasks.py:430, grep-confirmed);
  the file had been edited minutes earlier by the same fleet wave, so the miss
  reads as index lag presented as authoritative absence. Workaround: grep.
  **Feeds:** P8d teaching-miss family — a get_symbol miss on a file with an
  in-flight/recent index state should say "file recently changed, index may
  lag — verify with read/grep", never a bare not-found. (Same family as the
  search-side wait_for_fresh affordance.)

- **2026-07-04 · sanitiser-residual (P8a wave 1) · lore_impact · wrong_result
  (private-leaf blast radius)** — `lore_impact("loremaster.search._sanitise_line",
  depth=2)` rolled up modules that never call it (test_qdrant_store 10,
  memory.store, server, store._txn, test_watcher, loresigil.tei): the depth>1
  rollup walks the transitive IMPORT ripple, which for a leaf-level private
  function overstates the blast radius to near-uselessness; depth=1
  `direct_consumers` came back `[]` for the same underscore-private function
  even though search.py calls it from 7 sites. Workaround: grep -rn for the
  authoritative call-site list. **Feeds:** P8d verdict-bearing-output doctrine —
  either resolve private-symbol consumers properly or render an explicit
  "private symbol — consumer resolution unreliable, use grep" notice instead of
  empty-and-confident.

- **2026-07-04 · sanitiser-residual (P8a wave 1) · lore_search_code ·
  zero_hits (module-level constant)** — the module-level tuple constant
  `_BIDI_AND_ZERO_WIDTH_CHARS` in test_search.py could not be surfaced via
  semantic search (fell back to grep -n for its line). Module-level
  assignments appear under-represented vs def/class chunks. **Feeds:** P8d
  chunker/coverage review — constants are legitimate search targets.

- **2026-07-03 · team-lead · lore_search_code · capability_gap** — P5's
  discovery questions were structural seam-sweeps ("every call site of the
  sync manifest," "which tests pin this behavior," "what breaks if X changes")
  that flat semantic hits cannot answer in one shot; v0.3's graph tools cover
  single edges (what_imports/tests_for) but not budgeted multi-file maps.
  Workaround: Explore/scout subagents + grep (thousands of tokens per sweep,
  every session). **Feeds:** P6/P8 — this is the live justification for
  lore_map / lore_impact rollups; measure them against exactly these three
  question shapes.

- **2026-07-03 · team-lead · (tool loading) · affordance_gap** — the lore MCP
  tools are deferred behind a ToolSearch load; any brief that doesn't pre-solve
  that one-line load loses to grep by default (grep is always loaded). Subagent
  briefs never mentioned lore → subagents never used it. Workaround: none
  (tools simply unused). **Feeds:** process (the lore-first TOOLS block in
  every brief — in force as of today) + P8 doctrine: the instructions block
  must assume deferred loading and say so.

- **2026-07-03 · team-lead · graph tools · affordance_gap (self-inflicted doc gap)** —
  the team-lead mis-scoped v0.3's own graph surface, attributing "structural
  seam-sweeps" wholesale to grep/Explore when `references`/`what_imports`/
  `blast_radius`/`tests_for` chains answer most symbol-level sweep questions at
  function granularity. The tool's own steward underestimated it → typical
  agents will too. Workaround: none (capability unused). Root cause: no single
  affordance says "chain these four for a seam map." **Feeds:** P8 tool
  descriptions + instructions block (teach the CHAIN, not just the tools);
  P6 lore_map/lore_impact are the one-call ergonomic. Residual truth: astroid-
  inference bounds mean exhaustiveness checks (renames/await migrations) still
  need mypy/grep verification — document that boundary in the tool text.

- **2026-07-03 · team-lead (P6) · lore_tests_for · zero_hits** — asked for the
  covering tests of a FILE (`loremaster/search.py`, then the fuller
  `loremaster/loremaster/search.py`): both returned `[]`, while the SYMBOL form
  (`loremaster.search.SearchPipeline`) returned 50+ test nodes and
  `what_imports` proves the `test_search.py → search` edge exists. The
  documented file-path input shape silently matches nothing. Workaround:
  re-asked with the symbol form. **Feeds:** P6/P8 — fix the path normalisation
  (or teach the miss: "no file match — try a symbol name"), and document the
  working input shape in the tool text.

- **2026-07-03 · parity-scout + team-lead (P6) · lore_references · wrong_result
  (NEAR-MISS: almost deleted a live production base class)** — profiling
  `loremaster.graph.CodeGraph` for the #34 dead-code cleanup returned
  `production_references: 0` (test_references: 25), and the cleanup plan
  accordingly scheduled the class for deletion — but
  `graph_surreal.py:213 class _AstroidDerivation(CodeGraph):` is a PRODUCTION
  inheritance reference (astroid-derivation reuse), and `server.py` +
  `graph_surreal.py` import the module's constants/models at module scope.
  Caught only by the mandatory grep cross-check before deletion. Likely root
  cause: the known installed-vs-mounted resolution gap (in-container astroid
  resolves project imports to the pip-installed copy, dropping in-project
  refs; TEST files aren't installed, so their refs resolve to the workspace —
  explaining prod=0/test=25 exactly). Workaround: grep cross-check remains
  MANDATORY before any deadness verdict; brief doctrine updated. **Feeds:**
  the v0.3 container fix (source must shadow the install on astroid's path —
  needs image rebuild+recreate) and P6/P8 verdict-bearing-output doctrine:
  reference counts on in-project symbols must be trustworthy before
  lore_impact/dead_code can carry liveness verdicts.

- **2026-07-03 · team-lead (P6) · lore_search_code · affordance_gap** — tried to
  scope a search to one package with `filters={"path": "lorescribe"}`; silent
  zero hits. The `path` filter is EXACT-file-match only (it maps to the
  `file_path` payload key), but "scope to this subtree/package" is the natural
  intent and there is no prefix affordance and no teaching miss ("path matched
  no file — it must be a full file path"). Workaround: re-ran unscoped.
  **Feeds:** P6 pipeline filters (a prefix/tier-aware path scope, or at least a
  teaching miss on a path that matches nothing) + P8 tool text documenting the
  exact-match semantics.

- **2026-07-04 · team-lead (v2 FIRST LIVE USE) · lore_map · wrong_result
  (ranking)** — the unfocused map's TOP modules are all TEST INFRASTRUCTURE
  (_surreal_harness, _surreal_fakes, _extension_helpers rank 1-2-4; server.py
  ranks 5th). PageRank over the raw import graph rewards test-consumed hubs,
  but orientation means PRODUCTION structure. Workaround: none needed yet
  (focus= re-centers usefully). **Feeds:** P7/P8 — rank should down-weight or
  segregate test-file nodes (the references() prod/test split already knows
  how); consider a default prod-only view with tests behind a flag.
  *Triaged 2026-07-04 (P7 cycle-1 close): proposed FIX-FORWARD as a P7-tail
  side-stream (ledger task #6) after the cutover wave, before the phase-close
  redeploy — operator to confirm P7 vs P8.*
  *CONSUMED-BY 9171021 (P7-tail polish, 2026-07-04) — fix shipped; entry retires to Consumed at the P8 friction-table migration.*

- **2026-07-04 · team-lead (v2 FIRST LIVE USE) · lore_map · capability_gap
  (rendering)** — per-module symbol lists render EVERY symbol (80+ names for
  _surreal_fakes) — a dump, not a rollup; the budget then starves module
  COVERAGE (155 elided) to afford symbol noise. **Feeds:** P7/P8 — cap
  symbols per module (top-N by rank + "+K more"), spending budget on breadth
  over depth. *Triaged 2026-07-04 (P7 cycle-1 close): same disposition as the
  ranking entry above — one serving-layer polish wave, ledger task #6.*
  *CONSUMED-BY 9171021 (P7-tail polish, 2026-07-04) — fix shipped; entry retires to Consumed at the P8 friction-table migration.*

- **2026-07-03 · team-lead (P7 prep) · lore_impact · wrong_result (bare-name
  covering-tests drop)** — `lore_impact("RecalledMemory")` (bare name) returned
  the correct 2 prod / 10 test reference counts via the answers_to bridge but
  `tests: 0`, while the qualified `loremaster.memory.store.RecalledMemory`
  form returned 137 covering tests from the same graph. The covering-tests
  join silently ignores bare-name input instead of riding the same bridge (or
  teaching the miss). Workaround: re-asked with the module-qualified name.
  **Feeds:** P7/P8 — route the tests_for join through the same answers_to
  resolution as the ref counts, or render an explicit "tests unresolved for
  bare names — qualify the name" notice. *Triaged 2026-07-04 (P7 cycle-1
  close): rides the same P7-tail polish wave as the two lore_map entries
  (ledger task #6) — operator to confirm P7 vs P8.*
  *CONSUMED-BY 9171021 (P7-tail polish, 2026-07-04) — fix shipped; entry retires to Consumed at the P8 friction-table migration.*

- **2026-07-04 · team-lead + cutover-contract (P7 cutover) · lore_impact ·
  affordance_gap (depth-2 rollup misread)** — the depth-2 module rollup for
  MemoryStore attributed 12 consumer refs to test_schema_rebuild; the
  team-lead briefed a fixture migration there, but ground truth shows the
  file constructs NO MemoryStore (the refs are transitive, through its
  server.py import). Depth>1 rollups count the RIPPLE, not direct
  consumers — nothing renders that distinction, so a reader naturally takes
  module counts as direct usage. Workaround: agent verified at ground truth
  and reported the empty migration. **Feeds:** task #6's polish wave — label
  depth>1 rollups explicitly ("transitive via …" or a direct/transitive
  split), or render depth-1 direct consumers alongside.
  *CONSUMED-BY 9171021 (P7-tail polish, 2026-07-04) — fix shipped; entry retires to Consumed at the P8 friction-table migration.*

- **2026-07-04 · operator + team-lead (P7) · token budgets (map/search/schemas) ·
  wrong_result (measured miscalibration)** — lore enforces token budgets in
  VOYAGE tokens (`_count_tokens_single` → the pinned voyage-4 tokenizer) but
  consumers pay in CLAUDE tokens. Measured live against the count_tokens
  endpoint (claude-sonnet-5) over six samples — three lore-shaped (map rollup,
  code span, search hit: 1.610–1.652) and three dense Odoo source files
  (1.7k–3.5k lines, operator-directed: 1.654–1.720; dense comment-light code
  runs highest). Full range 1.61–1.72. Every budget silently under-counts by
  ~64–72%: a "1500-token" map ≈ 2,400+ Sonnet-5 tokens. Harness:
  scratchpad/token_calibration.py. Workaround: none (defect stands until fixed).
  **Feeds:** task #6 polish wave. FINAL VALUE (operator-directed large-corpus
  survey, 2026-07-04 — the six-sample pilot was NOT accepted as gospel):
  **TOKEN_BUDGET_CALIBRATION = 1.78** = max of per-project token-weighted p95
  ratios over a deterministic 10% stratified sample (1,116 files, 2.85M claude
  tokens; lore 1.704 / odoo 1.776 / di 1.729; token-weighted means 1.53–1.62;
  file max 2.63; DI .sql hottest extension at p95 2.06). Tool committed as
  scripts/token_survey.py (+32 unit tests); receipts in
  scratchpad/token_survey/survey_summary.md + per-file JSONL. Re-run the survey
  at the P8 token-accounting eval gate and whenever the yardstick model changes.
  *CONSUMED-BY 9171021 (P7-tail polish, 2026-07-04) — fix shipped; entry retires to Consumed at the P8 friction-table migration.*

- **2026-07-04 · di-scout · watcher/config · capability_gap** — DI's deployed
  lore.yaml can't keep up with dirs born mid-project: `.venv-timesfm25` (3,394 dirs,
  all inotify-watched) and `demand/chronos-2-finetuned` (50 GB, walked each
  reconcile) are unexcluded because `exclude_dirs` is NAME-based and hand-curated;
  the name `data` also prunes `validation/findings/data`, and `models` would prune
  real source. Workaround: manual lore.yaml edits after the fact (nobody has).
  **Feeds:** P8 — path-anchored excludes; default heuristics (prune any dir with
  `pyvenv.cfg`; binary-majority dirs); watch-scope telemetry in `lore_index_status`
  (watch count + top offenders) so drift is visible instead of silent.

- **2026-07-04 · di-scout · chunkers/search_code · capability_gap** — DI's 20
  `demand/config/*.yaml` fleet definitions cannot be search-indexed: unclaimed
  suffix → dispatch tier-4 returns `[]` silently (verified live: yaml literals
  invisible to search; read_file serves the same file fine). Workaround:
  `chunkers: {".yaml": {chunker: text}}` override (flat, key-path-blind,
  undocumented). **Feeds:** a yaml/toml chunker (or document the text-override and
  make lore-deploy's generated lore.yaml include config files); surface
  "included-but-unclaimed" files in lore_index_status instead of silence.

- **2026-07-04 · di-scout · search_code vs read_file (walk scope) · affordance_gap** —
  load-bearing generated docs inside an excluded data dir
  (`demand/data/reports/*.md`, 15 files cited by STATE.md as audit receipts) are
  readable via lore_read_file but invisible to lore_search_code; there is no way to
  say "exclude this dir's blobs but index these globs" (include globs cannot pierce
  an exclude_dirs prune). Workaround: follow doc pointers by hand into read_file.
  **Feeds:** P8 — precedence rule (explicit include glob pierces exclude_dirs) or
  glob-granular excludes.

- **2026-07-04 · di-scout · lore_recall_memory / findings surface · capability_gap** —
  DI's decision + findings ledgers need ledger READS: enumerate-in-order, follow the
  supersedes chain to its head, address a record by stable number, export a
  reviewable doc. Memory v2 writes all the needed structure (kind, supersedes,
  trust, labels) but recall remains `query+k` semantic-top-k, so DECISIONS.md /
  INDEX.md must stay hand-maintained — and live probes show search answers chain
  questions only by piggybacking on those hand-maintained docs. Workaround: keep the
  md ledgers as source of truth. **Feeds:** P8 findings surface — generalise
  `kind=friction` to finding/decision records with chain-head + ordered-browse
  queries; a browse/enumerate affordance on the memory read side.

- **2026-07-04 · di-scout · lore_references (and input-resolution family) ·
  affordance_gap** — a bare symbol name that fails resolution returns a
  zeros-and-empty result indistinguishable from "genuinely unreferenced":
  `lore_references("CoverageCalibrator")` = 0/0/[] vs the qualified name = 1
  production / 5 test (live DI, grep-verified). An agent (or lore_impact's verdict)
  reads that as DEAD. Workaround: always pass fully-qualified names — nothing tells
  you to. **Feeds:** P7-tail/P8 — resolve-or-error (suffix-match candidates, "did
  you mean", or an explicit `unresolved` marker in the payload), never silent zeros;
  extend the existing tests_for path-normalisation fix to every name-input tool.
  *PARTIAL 9171021 (2026-07-04): tests_for bare-name now rides the answers_to bridge; the resolve-or-error family (references/get_symbol did-you-mean) remains open → P8.*

- **2026-07-04 · di-scout · lore_save_memory/lore_recall_memory · affordance_gap** —
  on a store of multi-KB session-digest notes (live DI), specific-fact recall
  missed 4/7 probes; atomic facts drown inside digests and recall offers no
  kind/label filter to narrow (v2 save writes labels the v2 read side cannot use).
  Workaround: none for the reader; the facts stay in doc files. **Feeds:** P7/P8 —
  recall filters (kind=, labels=) to close the save/recall asymmetry; save-side
  affordance against digest dumps (length guidance or auto-split); consider
  note-chunking at embed time.

- **2026-07-04 · warmup-1 · lore_tests_for · affordance_gap** —
  `lore_tests_for("loremaster.search._sanitise_line")` returns empty (`[]`)
  despite 19 passing tests in `TestRenderSanitiser` (test_search.py) exercising
  it every run — they drive it indirectly via the search-rendering pipeline
  (`_search_one_hostile_chunk`) rather than calling `_sanitise_line` by name, so
  the graph's naming/reference heuristic finds no edge to the covering tests.
  Workaround: `git show <prior commit>` + grep to locate the covering test class
  by hand (used here for the efa5da7 sanitiser-extension pattern). **Feeds:**
  P8 — widen tests_for to also credit a helper's tests via its containing
  module/class co-location or an indirect call chain, not just a direct
  reference edge to the exact symbol.

## Consumed
  *PARTIAL 9171021 (2026-07-04): read-side kind=/labels= recall filters SHIPPED; save-side digest guidance/auto-split remains open → P8.*

- **2026-07-03 · team-lead · (whole surface) · distrust_unverified** — avoided
  lore for an entire heavy build session on an unmeasured staleness prior;
  later measured FALSE (90-minute-old `CommandSubscriber` resolved perfectly,
  0 in-flight). Workaround: grep/subagent sweeps all session. Root cause:
  freshness is pull-only (agent must remember to ask `index_status`); trust
  decays on priors when nothing pushes freshness into results. **Consumed-by
  P6 commit 8ae67ab**: SearchPipeline v2 keeps the per-result staleness flag +
  warning line VISIBLE on every in-flight hit (annotate, never blanket-block),
  wait_for_fresh semantics preserved — contract-pinned in test_search.py's
  TestFreshnessFlags/TestWaitForFresh. (Doctrine half — push freshness into
  the tool text/instructions — still lands with P8's surface.)
