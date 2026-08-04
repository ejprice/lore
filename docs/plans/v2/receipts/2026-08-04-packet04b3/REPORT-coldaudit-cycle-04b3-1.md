# REPORT-coldaudit-cycle-04b3-1 — cold REFUTE audit of the variant-D CYCLE change

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first)
- **lore tools:** reachable + used (registered `coldaudit-cycle-04b3-1`/`pkt04b3`; `lore_index`
  confirms lore watches `/workspace` @ branch `feat/surreal-unification`, ref
  `496a95e` — EXACTLY the graded HEAD; 3265 files, 0 failed/in-flight, last sync ~7 min pre-audit).
  `lore_get_symbol`/`lore_impact`/`lore_search`/`lore_findings` all returned.
- **spike-surreal :18000 (TEST store):** TCP open; the CYCLE contract, `test_task_ledger.py`, the
  ESC-1 harness, the MP-1 probe, and my own FORK-A probe all ran against it. **Never touched :18500.**
  (Both stores are `Up`; I confirmed the test/prod split before any run.)
- **`./scripts/scratch_copy.sh`:** present + executable; produced an isolated copy whose
  `loremaster.__file__` resolves INSIDE the copy (#140 provenance printed on every mutation run).
- **No unmeetable demand.** Grep used only for the bare rename/retired-name sweep and for git-history
  attribution of pre-existing reds (the honest exhaustiveness/history cases, said out loud in §6).

## SUMMARY BLOCK
- **state: done.** VERDICT below.
- **VERDICT: GO on the CYCLE PRODUCTION CHANGE** (496a95e's `tasks.py` + `pyproject`×2 + `uv.lock`
  diff). It is correct, sound, mutation-proven, store-law-compliant, and its own diff adds ZERO reds.
- **⚠ GO carries prominent RESIDUALS the builder did NOT flag** — the 04b-3 PACKET (not 496a95e's
  own diff) introduced **3 RED_ORPHANED pytest failures** via its committed probe scripts + contract
  file (filed **finding #329**). These do not affect production correctness, but the packet's gate
  CURRENCY is RED until they are fixed or adjudicated. See §6 + RESIDUALS.
- deviations: (1) filed **finding #329** for the 3 packet-introduced pytest orphans. (2) my FORK-A
  probe `scripts/coldaudit_cycle_04b3_fork_a_refute.py` reads the test-store URL from `os.environ`
  (cloned from the builder's own probes) — it inherits the same `test_secret_*` red class as
  `esc1`/`mp1`; it does NOT change those pins' red state (already red from the packet's scripts) —
  lead decides commit-vs-paste (§6, #329). (3) disposable scratch copy left at
  `/tmp/coldaudit-cyc-scratch` (rm was permission-blocked; inert, safe to delete).
- **Packages considered:** none — no NEW mechanism specified (audit only). I DID verify the graded
  change's package swap: `networkx.simple_cycles` (Johnson all-simple-cycles) correctly REPLACES the
  hand-rolled drop-an-edge enumeration in `_record_legacy_cycles` — mutation-proven that the hand-roll
  undercounts a fully-connected component (4 vs 5) and that the MODULE-attribute call is what makes
  MP-4 provable (§3 MUT-B). `graphlib.TopologicalSorter` (stdlib) is correctly KEPT as the shared
  `find_blocked_by_cycle` detector, UNCHANGED.
- **Graded:** `496a95e` · HEAD-at-report: `496a95e` · **SAME** (`git merge-base --is-ancestor` clean;
  working tree carries only my untracked probe — production/test files pristine vs HEAD).
- decisions-needed: **one** — the design tension in #329 (brief-base §1 "commit your instruments" vs
  packet-42's secret-seam pin flagging every probe that reads `os.environ`). Operator/lead ruling:
  allowlist / route-through-helper / adjudicate. Not a production blocker.
- receipt pointers: gate re-runs §2 · mutation proofs §3 · REFUTE constructions + soundness §4
  (`scripts/coldaudit_cycle_04b3_fork_a_refute.py`, exit 0) · store-law §5 · pre-existing reds +
  currency §6 (finding #329) · RESIDUALS table at end.

---

# §1 · What I graded (496a95e, variant D)
Three production edits in `loremaster/loremaster/tasks.py` plus a dep re-scope:
1. **`_refuse_a_cycle`** now seeds from the pending task's blockers and reads via
   **`_bounded_dependency_graph`** (the ancestor closure over persisted `blocks` edges) instead of the
   retired whole-backlog `_read_dependency_graph`. The overlay of pending columns, the `minted` set,
   and the **drop-loop through the shared `find_blocked_by_cycle` + `_drop_one_cycle_edge` are KEPT**
   (variant D / R6) — that is what keeps the guard sound when a legacy cycle coexists with the minted
   one (MP-1).
2. **`_record_legacy_cycles`** enumeration swapped hand-rolled drop-loop → `networkx.simple_cycles`
   (MODULE form; #273/#272).
3. networkx moved dev→runtime (`loremaster/pyproject.toml`), mypy-override re-scoped
   (`pyproject.toml`), `uv.lock` re-locked.

# §2 · Gate re-runs — REPRODUCED as my own instrument (not trusting builder counts)
All run against the REAL tree / spike :18000. Passed-COUNTs pasted:
- **CYCLE contract** (`test_cycle_write_path_04b3.py` + `test_blocks_edge.py`, `-n auto`):
  **`213 passed in 11.93s`** (builder claimed 213 ✓).
- **`test_task_ledger.py`** (`-n auto`): **`240 passed in 9.88s`** (builder claimed 240 ✓).
- **ESC-1 harness** `scripts/esc1_write_path_cycle_closure.py`: **exit 0**, `loremaster.__file__` = real
  tree, every check PASSED, negative-control DB2 CATCHES an injected `blocks`-edge deletion (RETURN
  BEFORE proves the mutation landed), residue limited to the named phantom + batch-local siblings.
- **MP-1 probe** `scripts/cycle_coexisting_legacy_soundness_probe.py`: **exit 0**, real tree, guard
  **REFUSED** the minted cycle `zzzx → zseed → zzzn → zzzx` while legacy `aaap↔aaaq` coexisted; 0 rows.
- **Concurrency legs** (a single green never clears a concurrency test): the 8-way liveness test +
  the whole `TestCreateRefusesToFormACycle` refusal class re-run **10/10 consecutive GREEN** (9 tests
  each), on top of the builder's 20/20. The liveness test drives 8 concurrent `asyncio` creates on a
  shared blocker internally, so real contention is exercised regardless of the runner.

# §3 · Mutation proofs — 3/3, each in an isolated scratch copy (provenance printed)
Method: `./scripts/scratch_copy.sh /tmp/coldaudit-cyc-scratch` (asserts `loremaster.__file__` INSIDE
the copy — #140), mutate, run the target pin, restore byte-identical from a `cp -a` backup between
each. Every run printed `prov: /tmp/coldaudit-cyc-scratch/loremaster/loremaster/__init__.py`.

- **MUT-A — revert the bounded read → whole-backlog scan** (`WHERE array::len(blocked_by) > 0`,
  ignoring seeds): `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` → **RED**,
  `assert 63 == 8` (63 rows read by the whole-population scan vs 8 by the bounded closure). The pin
  measures ACTUAL store traffic (`StoreTraffic.rows`), not query text — it discriminates. Reproduces
  the builder's RED baseline exactly.
- **MUT-B — revert `networkx.simple_cycles` → hand-rolled drop-loop**: two pins RED —
  `test_the_RECORDED_cycle_count_equals_networkx_simple_cycles[complete-triangle]` (hand-roll records
  4 vs networkx's 5 for the fully-connected component — #273's exact undercount) AND
  `test_MUTATION_neutralising_networkx_simple_cycles_SILENCES_the_record` (`assert 4 == 0`: with the
  module attr patched to enumerate nothing, the hand-roll still records 4 → proves routing-is-not-
  sharing, #102). The `[disjoint-1-2-3]` and `[overlapping]` cases stayed GREEN — the fixture
  discriminates precisely on the fully-connected case.
- **MUT-C — neutralise the drop-loop (single-witness / variant S)**: the MP-1 pin
  `test_a_MINTED_cycle_COEXISTING_with_a_LEGACY_cycle_in_the_closure_is_REFUSED` → **RED**,
  `Failed: DID NOT RAISE TaskLedgerError`. The guard accepts a real minted cycle because
  `find_blocked_by_cycle` returns the legacy cycle first — exactly the unsoundness the KEPT drop-loop
  prevents. Confirms the drop-loop is load-bearing, not vestigial.

# §4 · REFUTE the soundness claims — by CONSTRUCTION
**Instrument (committed, brief-base §1): `scripts/coldaudit_cycle_04b3_fork_a_refute.py`, exit 0.**
This is MY independent construction (not the builder's confirming harness) — it ATTEMPTS to break
FORK-A by placing a cycle-closing row where the bounded read cannot reach.

- **(a) FORK-A — "does bounding to the closure lose a cycle?"** A multi-hop world where the
  cycle-closing row `far` (whose column names the pending id `N`) is TWO hops upstream of the seed:
  - **World A (edges present):** the closure read reaches `far`; guard **REFUSES**
    `far → mid → seed → N → far`. Multi-hop closure works.
  - **World B (one intermediate `blocks` edge MISSING, no backfill):** the read **TRUNCATES at `mid`**
    and the guard **ACCEPTS**. This pins the *exact* soundness dependency: variant D is sound **iff the
    edge==column invariant holds** (every real-persisted `blocked_by` column link has a `blocks` edge).
  - **World B + `ensure_ready` backfill:** the missing edge is minted, the read reaches `far`, guard
    **REFUSES**. Self-healing.
  **Could NOT construct a cycle-closing row the guard misses on an invariant-satisfying store.** The
  refutation succeeds only by VIOLATING the invariant — which production does not do (below).
- **Why the invariant HOLDS in production (I traced it, did not assume):**
  1. **Writes are atomic** — `create_task`/`create_many` write the `blocked_by` COLUMN and the `blocks`
     EDGE in ONE `BEGIN…COMMIT` (`_create_fragment`/`_relate_fragment`; pinned by
     `TestCreateTaskIsAtomic::test_a_create_whose_RELATE_cannot_land_writes_NO_task_row`). No column-
     without-edge can appear via the ledger's own writes.
  2. **Legacy rows are healed before any guard** — `_backfill_blocks_edges` mints the edge for every
     real-persisted column pair (skipping only phantoms, which name no row and contribute no onward
     path), and it runs inside `ensure_ready`, which `build_app_context` calls **unconditionally at
     startup** (`server.py:7726`) on the same `task_ledger` instance whose `create_task`(`:3783`)/
     `create_many`(`:4341`) handlers serve the tools. So the backfill ALWAYS precedes any guarded
     create. World B is unreachable on the served path.
  **Conclusion: FORK-A's soundness claim is HONEST and well-guarded.** The docstring's own framing
  ("resting on ESC-1's measured YES that every persisted ancestor is edge-reachable after
  `ensure_ready`") is exactly right; I add the missing half — *why* the invariant it rests on is
  maintained (atomicity + backfill-before-guard).
- **(b) MP-1 coexistence:** re-ran the builder's live-store probe (exit 0, REFUSED) AND independently
  proved via MUT-C that the drop-loop is what makes it sound — a single-witness build ACCEPTS the same
  world. Two instruments, same conclusion.
- **(c) COLUMN-vs-edge:** in World A the closing link `far.blocked_by ∋ N` is column-only by
  construction (`N` has no row → `ENFORCED` forbids the `blocks` edge → an edge-traversal cycle check
  returns "acyclic"). The shipped guard reads the COLUMN and refuses. If it read edges only it would
  accept — which is precisely what
  `test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED` (GREEN) pins.

# §5 · Store-law compliance (`docs/reference/surrealdb-31-capabilities.md` §4 / §6.4)
The assembled bounded read (`_bounded_dependency_graph`):
`SELECT record::id(id) AS id, blocked_by FROM task WHERE id IN array::distinct(array::flatten(
array::concat([$closure_starts], (SELECT VALUE @.{1..32+collect}(<-blocks<-task) FROM
$closure_starts)))) TIMEOUT 5s`, params `{closure_starts: [RecordID("task", seed), …]}`.
- **Bounded depth:** `@.{1..32+collect}` — bounded form (`TASK_BLOCKER_MAX_DEPTH = 32`), NOT open
  `@.{..}`. ✓ (§4 recursive-path rule.)
- **TIMEOUT:** `TIMEOUT 5s` (`_TRAVERSAL_TIMEOUT`). ✓ (§4 "Add a TIMEOUT".)
- **RecordID bounds:** starts are bound `RecordID(TASK_TABLE, seed)` params, never bare strings (§4:
  a bare-str endpoint is rejected loudly). ✓
- **Direction:** `<-blocks<-task` walks INCOMING `blocks` (blocker→blocks→blocked), i.e. upstream to
  the seed's ancestors/blockers — correct. ✓
- **No §6.4 dangling-endpoint hazard:** the traversal's result feeds ONLY a `WHERE id IN (…)`
  membership set that then reads `task` rows; it is **not projected as first-class output**. A phantom
  / dangling id in the set matches NO `task` row → contributes no row and no error. The ESC-1 harness
  cross-checks the raw traversal vs the column closure and they AGREE, with phantom residue named
  individually. ✓ (This is the robust design — §6.4's trap is projecting the traversal directly, which
  this query does not do.)

# §6 · Pre-existing reds + gate currency (`scripts/pending_contract_gate.py --currency`)
Ran the manifested currency gate (authoritative per `scripts/gates.yaml`). **496a95e's own diff adds
ZERO reds** (`tasks.py` ruff-clean + mypy-clean; 0 networkx typecheck errors; only 4 non-report files
touched, none a test/script). Per-gate:
- **ruff — RED_ORPHANED, 6** (all prior-packet audit scripts:
  `scripts/audit_probes/coldaudit_wavec_r2_probe2.py` PLC0206; `scripts/c3_wrongbuild_driver.py`
  E501×3 + PLW1510×2). Known at HEAD (#312). Not the CYCLE diff. *(My probe first tripped a 7th —
  PLR0915 — which I refactored away; `ruff check .` is back to the 6.)*
- **typecheck — RED_ADJUDICATED(packet-39) + RED_ORPHANED(6 scripts).** The 102 auth/posture errors
  (`test_auth*`, `test_permission_resolver_seam`, `test_hosted_readonly_posture`, `lorerunes` posture
  tests — `resolve_posture`/`PostureConfigError`/`Posture`/`SCOPE_READ` absent from source) are owned
  by `packet-39-pending-build` (reopen: operator #296 or packet-39 build start). The 6 scripts errors
  (`coldaudit_wavec_r2_probe3/4`, `c3_harness_repair`) are orphaned prior-packet debt. None touch
  `tasks.py`/networkx.
- **pytest — RED_ORPHANED, 3 → FILED finding #329.** ⚠ **The builder's report §6 flagged only ruff +
  typecheck and MISSED these.** All 3 were GREEN pre-04b-3 (baseline `7db4362`: the offending files
  were ABSENT) and are RED at HEAD 496a95e — introduced by the 04b-3 PACKET's committed instruments,
  though not by 496a95e's own diff:
  1. `test_secret_resolution_seam::test_every_environment_read_is_the_entry_point_or_allowlisted` —
     `scripts/esc1_write_path_cycle_closure.py` + `scripts/cycle_coexisting_legacy_soundness_probe.py`
     read `os.environ` for the test-store URL outside the ONE secret module (packet-42), no allowlist.
  2. `test_secret_typing::test_secretstr_is_minted_only_where_a_credential_ORIGINATES` — the same two
     scripts mint `SecretStr(os.environ.get(...))` at a call site (attack shape S6).
  3. `test_surreal_harness::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` — the 04b-3
     contract file `test_cycle_write_path_04b3.py` became the 48th `_surreal_harness` importer while the
     docstring still says 47 (`assert 47 == 48`). The P8d natural-language-surface class — here a gate
     exists and is red.
  Per brief: a RED_ORPHANED is a **finding to FILE, not a CYCLE NO-GO** — but the packet's currency
  cannot go GREEN until these are fixed or adjudicated (owner + trigger in `pending_contracts.yaml`).
  My own FORK-A probe inherits the pins-1/2 pattern (cloned idiom); it does not change their red state.

# §7 · RESIDUALS (the lead reads residuals, not just the summary)
| # | residual | severity | attribution | action |
|---|---|---|---|---|
| R1 | 3 RED_ORPHANED pytest failures (`test_secret_resolution_seam`, `test_secret_typing`, `test_surreal_harness` count) | **blocks packet currency, NOT production** | 04b-3 PACKET's committed probe scripts + contract file; builder missed them | **finding #329** — lead/operator: allowlist / route-through-helper / adjudicate |
| R2 | networkx runtime dep not yet baked into image | deploy-time | 496a95e is COMMIT-ONLY (rides 05a's deploy) | 05a smoke owes the in-image `import networkx` line (builder's own §4 flag) — verify at deploy |
| R3 | FORK-A probe reads `os.environ` / mints `SecretStr` (same class as R1) | cosmetic (audit instrument) | mine (cloned from builder probes) | lead: commit as-is (already-red class) or paste verbatim + drop; resolve with R1 |
| R4 | ruff 6 orphans + 6 scripts-typecheck orphans | pre-existing debt | prior packets (#312, 04b-2 rescues) | not the CYCLE work; separate cleanup |
| R5 | soundness is CONDITIONAL on the edge==column invariant (well-guarded, not a defect) | none (documented + traced) | design | none — bound is honest; noted so a future engineer meets it deliberately |
| R6 | disposable scratch left at `/tmp/coldaudit-cyc-scratch` (rm permission-blocked) | none | mine | inert; `rm -rf` when convenient |

---
*Written 2026-08-04 by `coldaudit-cycle-04b3-1` (Opus 4.8, session pkt04b3), fresh context, against
`feat/surreal-unification` @ `496a95e`. Builder ≠ grader: I re-ran every gate as my own instrument,
mutation-proved all three load-bearing pins in an isolated #140-safe scratch copy, and constructed an
independent FORK-A refutation rather than reasoning from the invariant. The CYCLE production change is
GO; the packet has a currency debt (finding #329) that is the lead's/operator's to resolve.*
