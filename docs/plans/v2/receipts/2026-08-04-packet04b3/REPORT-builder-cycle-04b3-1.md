# REPORT-builder-cycle-04b3-1 — the variant-D CYCLE production change (ESC-1 · #273/#272)

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first)
- **lore tools:** reachable and used (registered `builder-cycle-04b3-1`/`pkt04b3`; `lore_index`
  live — 3263 files, watching `/workspace` @ `415fa3d`, branch `feat/surreal-unification`;
  `lore_get_symbol`/`lore_read`/`lore_comms` all returned). Index fresh (last sweep this session
  pre-edit).
- **spike-surreal :18000:** reachable (`/dev/tcp` open; the CYCLE contract, the ESC-1 harness and
  the MP-1 probe all ran against it). Never touched :18500.
- **file writes:** yes (edited `tasks.py` + both `pyproject.toml` + `uv.lock`; wrote this report).
- **No unmeetable demand.** No grep fallback for a structure question except the bare rename-sweep
  for retired-symbol residue (grep's honest exhaustiveness case, P8d law) — said out loud in §5.

## SUMMARY BLOCK
- **state: done.** The FROZEN variant-D contract (graded SUFFICIENT by `adversary-cycle-04b3-2`) is
  GREEN: **213 passed** on both contract files (was **4 failed / 209 passed** at HEAD), **240 passed**
  on the concurrency collateral `test_task_ledger.py`. No contract test edited.
- deviations (all disclosed, none changes behaviour the contract pins):
  (1) **docstring rename-sweep** — deleting `_read_dependency_graph` dangled a `:meth:` cross-ref in
  `direct_dependents`; rephrased to generic prose (P8d natural-language-surface class). (2) **`_refuse_a_cycle`
  docstring** updated to describe the ancestor-closure bound + the KEPT drop-loop's MP-1 role (behaviour
  prose must match code). (3) **`uv.lock` re-locked** — a necessary consequence of the dep move; without
  it `uv sync --locked` (the Containerfile's install, `Containerfile:87`) would fail "lockfile out of
  date". No version changed (206ms, zero downloads — a metadata reshuffle). (4) added the named param
  constant `_CLOSURE_START_PARAM` (house idiom; no hand-copied literal).
- **Packages considered:** `networkx` 3.6.1 (READ: the count-oracle `_independent_cycles` in
  `test_blocks_edge.py` builds `DiGraph` edge `node -> blocker` then `simple_cycles`; adversary §PKG =
  Johnson's all-simple-cycles) → **replace** the hand-rolled drop-an-edge enumeration in
  `_record_legacy_cycles`; moved **dev → runtime** in `loremaster/pyproject.toml` (production import now).
  ⚠ MODULE-attribute call `networkx.simple_cycles(...)` REQUIRED (R-1): MP-4 patches the module attr, a
  `from networkx import simple_cycles` binding escapes it. `graphlib.TopologicalSorter` (READ:
  `CycleError.args[1]` is the cycle path) → **keep** — it is the shared `find_blocked_by_cycle` detector
  (R6, one ledger-owned detector), UNCHANGED. `_drop_one_cycle_edge` / `_txn.retry_on_conflict` (in-house)
  → **keep** unchanged (`_drop_one_cycle_edge` is now the guard's single legit caller — variant D).
- **Graded:** builder report (no verdict on another's artifact). HEAD-at-report: `415fa3d` (unchanged —
  I do not touch git; the lead commits). Contract graded SUFFICIENT @ `e22c43a`, byte-identical to
  `415fa3d` on the CYCLE surface.
- decisions-needed: **none.** Two pre-existing gate-reds flagged (NOT mine, NOT in my writable set): see §6.
- receipt pointers: RED→GREEN §2 · production edits §3 (`tasks.py` symbols) · pyproject/lock §4 · gates
  §5 · pre-existing reds §6 · store-law concurrency (20×2 greens) §5 · ESC-1 harness
  `scripts/esc1_write_path_cycle_closure.py` (exit 0) · MP-1 fixture
  `scripts/cycle_coexisting_legacy_soundness_probe.py` (exit 0, real tree).

---

# §1 · Mission (variant D, from the FROZEN contract) — what I built
Per `REPORT-design-sidecar-04b3-1.md` §CYCLE-TRILEMMA (variant D; from-minted RETRACTED) and
`REPORT-contract-cycle-04b3-1.md` §273-FLAGS / §ESC-1-FLAGS, the minimal production change is exactly two
things in `loremaster/loremaster/tasks.py` plus the dep re-scope:
1. **ESC-1 / FORK-A bounded read** — replace `_refuse_a_cycle`'s whole-dependency-bearing-population read
   with a closure-bounded read; KEEP the drop-loop + `find_blocked_by_cycle` + `_drop_one_cycle_edge`
   (detection UNCHANGED — that is what makes D sound under MP-1).
2. **#273/#272** — swap `_record_legacy_cycles`'s enumeration to `networkx.simple_cycles` (module form);
   move networkx dev→runtime + re-scope the mypy-override comment.

# §2 · RED → GREEN receipts (contract-first; @ `415fa3d`)
**RED baseline (both whole contract files, BEFORE any code change) — reproduces the adversary's baseline
exactly:**
```
$ .venv/bin/python -m pytest loremaster/tests/test_cycle_write_path_04b3.py \
    loremaster/tests/test_blocks_edge.py -n auto -q
4 failed, 209 passed in 8.89s
FAILED …TestTheAllCycleEnumeratorIsNetworkxInPRODUCTION::test_networkx_is_imported_by_the_PRODUCTION_tasks_module
FAILED …TestTheEnumerationEQUALSNetworkxAfterTheSwap::test_MUTATION_neutralising_networkx_simple_cycles_SILENCES_the_record
FAILED …TestTheEnumerationEQUALSNetworkxAfterTheSwap::test_the_RECORDED_cycle_count_equals_networkx_simple_cycles[complete-triangle]
FAILED …TestCreateRefusesToFormACycle::test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE
```
The bounded-read pin failed `63 == 8` (whole-population scan grew 8→63 as the ledger grew 5→60 blocked
pairs). Each RED is RED for the right reason — this is the HEAD "wrong build" that mutation-proves all
four pins (break-the-code = revert to HEAD → RED; my change → GREEN).

**GREEN (both files, AFTER the change):**
```
$ .venv/bin/python -m pytest loremaster/tests/test_cycle_write_path_04b3.py \
    loremaster/tests/test_blocks_edge.py -n auto -q
213 passed in 9.30s
```
All 4 RED pins flipped; MP-1 (soundness), the FORK-C tripwire, 8-way liveness, the two kept ESC-1
siblings, the count positive controls and the member-coverage class all stayed GREEN.

**Concurrency collateral (proves the rename/read-swap breaks nothing):**
```
$ .venv/bin/python -m pytest loremaster/tests/test_task_ledger.py -n auto -q
240 passed in 7.00s
```

**Live-store acceptance receipts (against spike :18000, the REAL tree):**
- ESC-1 acceptance harness `scripts/esc1_write_path_cycle_closure.py` → **exit 0**, every check PASSED
  (the shipped bounded closure read cross-checks byte-for-byte against a raw traversal; the diff catches
  an injected edge-deletion; residue limited to the named phantom + batch-local siblings).
- MP-1 durable fixture `scripts/cycle_coexisting_legacy_soundness_probe.py` → **exit 0**,
  `loremaster.__file__ = …/loremaster/loremaster/__init__.py (the REAL tree)`, guard **REFUSED** the
  create forming `zzzx → zseed → zzzn → zzzx` while a legacy `aaap↔aaaq` cycle coexisted; 0 rows written.
  Variant D's soundness is a FACT (the drop-loop steps over the legacy cycle and finds the minted one),
  not a hope.

# §3 · The production change — `loremaster/loremaster/tasks.py` (by symbol)
- **`import networkx`** added (third-party group; ruff-clean, no reordering needed).
- **`_CLOSURE_START_PARAM = "closure_starts"`** — the closure read's bound-param name (a LIST of
  `RecordID` starts, distinct from `_TRAVERSAL_START_PARAM`'s single start).
- **`_record_legacy_cycles`** — the hand-rolled `while True: find_blocked_by_cycle + _drop_one_cycle_edge`
  drop-loop DELETED; replaced by building a `networkx.DiGraph()` (edge `node -> blocker`, matching the
  test oracle `_independent_cycles`) and iterating `networkx.simple_cycles(graph)`, one WARNING record per
  cycle (event/`cycle`/`members` extras unchanged). The MODULE-attribute call is what MP-4's monkeypatch
  can neutralise (routing-is-not-sharing, #102 / R-1). DETECTION is untouched.
- **`_read_dependency_graph` → `_bounded_dependency_graph(self, seeds: Iterable[str])`** — the whole-
  population `SELECT … WHERE array::len(blocked_by) > 0` replaced by the ancestor-closure read. ONE
  `_query` round trip; seeds → `RecordID`s; walk `<-blocks<-task` (`@.{1..32+collect}`,
  `TASK_BLOCKER_MAX_DEPTH`, `TIMEOUT 5s`); read the `blocked_by` COLUMNS of exactly the closure rows.
  The assembled statement is byte-identical (param-name normalised) to the adversary's store-proven
  variant-D query. **The column is KEPT** (store reference §4: `ENFORCED` forbids the closing-link edge,
  so an edge-only read returns "acyclic"); the edge only bounds WHICH rows to read (a `GraphEdgeScan`,
  store reference §4). A phantom seed contributes no row and no error (store reference §4/§6.4).
- **`_refuse_a_cycle`** — computes `seeds = {blocker for blockers in pending.values() for blocker in
  blockers}` and calls `_bounded_dependency_graph(seeds)`. The overlay of pending columns, the `minted`
  set, and the drop-loop through the shared `find_blocked_by_cycle` are **UNCHANGED** (variant D). Its R7
  docstring paragraph updated to name the closure bound and the drop-loop's MP-1 role.
- **`direct_dependents`** docstring — the dangling `:meth:`_read_dependency_graph`` cross-ref rephrased to
  generic prose (rename-sweep; the pedagogical "store-side containment vs whole-graph read" point kept).

# §4 · Dependency re-scope (#272 / §273-FLAGS) — pyproject + lock
- `loremaster/pyproject.toml`: `"networkx>=3.6.1"` moved from `[dependency-groups] dev` (now removed —
  it was the only member) into `[project] dependencies`, with a comment stating it is a PRODUCTION import
  baked in by the image's `uv sync --locked --all-packages`.
- `pyproject.toml` (root): the `[[tool.mypy.overrides]]` networkx comment RE-SCOPED — the false
  "TEST-SIDE ORACLE only … PRODUCTION imports it nowhere" replaced with "RE-SCOPED to PRODUCTION at #273"
  (the module list is unchanged; P8d prose-surface class). #272 was already resolved for the test tree at
  `af3551c`; this promotes it.
- `uv.lock` re-locked (`uv lock`, exit 0): networkx now sits in loremaster's `[package.dependencies]` +
  `requires-dist` (runtime); its `dev-dependencies`/`requires-dev` rows are gone. `uv sync --locked
  --all-packages` validates (exit 0). No third-party version moved.

**COMMIT-ONLY — I did not deploy** (04b-3 rides 05a's deploy per design §A-deploy). The image now has the
networkx runtime dep to bake; 05a's smoke owes the "import networkx in the deployed image" line (design
rider). I did **not** edit the `Containerfile` or `conformance_provenance`: the runtime dep + re-lock is
sufficient for `uv sync --locked --all-packages` to install networkx, and `conformance_provenance`'s
`EXPECTED_MEMBERS` guards WORKSPACE members (lorerunes/…/loremaster), not third-party deps — networkx is
not a member. **FLAG for 05a:** add the in-image `import networkx` smoke line at deploy.

# §5 · Gates
- **ruff on the changed module:** `uv run ruff check loremaster/loremaster/tasks.py` → **All checks
  passed!**
- **mypy on the changed module:** `scripts/typecheck.sh` reports **ZERO** errors for
  `loremaster/loremaster/tasks.py` and **zero** networkx-related errors (the `[[tool.mypy.overrides]]`
  makes networkx `Any`; no unused-ignore). Verified by grepping the full typecheck output.
- **Store-law concurrency discipline (≥8-way, 20 consecutive greens — never a single run):**
  - `TestCreateRefusesToFormACycle` (batch/self/persisted refusals + MP-1 + one-round-trip): **20/20**
    consecutive GREEN.
  - `test_LIVENESS_eight_way_concurrent_creates_on_a_SHARED_blocker_all_land`: **20/20** consecutive
    GREEN.
- **Rename-sweep (bare, anchor-free):** the only files referencing `simple_cycles`/`_BACKFILL_CYCLE_EVENT`/
  `_record_legacy_cycles`/`_bounded_dependency_graph`/`_read_dependency_graph` are `tasks.py` + the two
  CYCLE test files (both green). `_read_dependency_graph`'s only remaining mentions are in ARCHIVED
  receipts (historical, out of scope, not rewritten). `find_blocked_by_cycle` + `_drop_one_cycle_edge`
  stay LIVE (guard caller + `server.py` batch-key check) — no dead code introduced.

# §6 · Two PRE-EXISTING gate reds — NOT mine, flagged not fixed (scope law)
Both are red at HEAD `415fa3d`, in files outside my diff (`git diff --name-only` = my 4 files only), and
neither involves tasks.py or networkx. Surfaced for the operator/lead, not silently ignored or silently
fixed:
- **`uv run ruff check .` → 6 errors**, all in prior-packet audit scripts:
  `scripts/audit_probes/coldaudit_wavec_r2_probe2.py:230` (PLC0206) and `scripts/c3_wrongbuild_driver.py`
  (E501 ×3, PLW1510 ×2). CLAUDE.md already records ruff red at HEAD (#312).
- **`scripts/typecheck.sh` → 102 errors** across an in-flight **auth/posture** feature
  (`loremaster/tests/test_auth*`, `test_permission_resolver_seam.py`, `test_hosted_readonly_posture.py`,
  `lorerunes/tests/test_posture.py`/`test_roster_parser.py`/`test_email_normalisation.py`) + 6 in prior-
  packet scripts (`c3_harness_repair.py`, `coldaudit_wavec_r2_probe3/4.py`). Confirmed pre-existing: the
  symbols the tests import — `resolve_posture`, `PostureConfigError`, `Posture`, `SCOPE_READ` — are ABSENT
  from source (tests written ahead of code = an in-flight packet's RED, independent of my change).

---
*Written 2026-08-04 by `builder-cycle-04b3-1` (Opus 4.8, session pkt04b3) against
`feat/surreal-unification` @ `415fa3d`. Variant D built faithfully from the adversary's store-proven
reference build (`REPORT-adversary-cycle-04b3-2.md` §7); the assembled bounded-read query is byte-
identical (param-name normalised) to it. Real tree mutated with a `/tmp/builder-cyc-backup` content
backup first (repo law). COMMIT-ONLY — the lead commits and verifies the diff.*
