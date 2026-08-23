brief-base v14 read
brief project v7 read

# REPORT — coldaudit-61a-w1 (COLD AUDIT, packet 61a-w1, finding #402 / §FR-4 refuse-while-keeping + D1/D2/D3 remediation verbs)

## SUMMARY BLOCK
- receipt: `brief-base v14 read` · `brief project v7 read`
- state: **done** — independent REFUTE pass complete; verdict below.
- **VERDICT: GO** — all gates GREEN/PASS on independent clean re-runs; all 6 load-bearing
  mutations proven to discriminate; no orphaned virtue. Residuals surfaced, none block. Lead may commit.
- deviations: none in method. One process note: my FIRST full-suite run (launched before the
  scratch) OVERLAPPED my scratch mutation runs on the shared test store → 12 failed / 53 errors
  scattered across UNRELATED store-touching files; re-run alone (§Full-suite discrepancy).
- Packages considered: none — no mechanism specified (audit pass; the build reuses substrate seams).
- Reuse ledger: none — I wrote no repo symbols (scratch-only mutations, restored byte-exact).
- **Graded: 84d20a3 · HEAD-at-report: 84d20a3 · SAME** — every RED/GREEN/mutation claim is at this sha.
- decisions-needed: none.
- receipt pointers: §Gates (re-run counts) · §Mutation proofs (table + `loremaster.__file__`) ·
  §Reach-pins · §F2 · §check-first/wrap · §Exact-set re-arm · §Contract-blind inventory · §Residuals.

## CAPABILITY CHECK
Brief fully satisfiable. lore MCP loaded; live TEST store `ws://127.0.0.1:18000` reachable (never
:18500); `scratch_copy.sh` provenance tool worked. No unmet demand.

## Store reference citations (cited, never re-transcribed)
`docs/reference/surrealdb-31-capabilities.md`: §2 (`record<t>` FIELD links do NOT auto-clean on
target delete; `str(RecordID)` round-trips; UPDATE is update-only, never upserts a specific id),
§3 (delete is ONE `execute_transaction`), §4 (graph RELATION edges self-delete on endpoint delete),
§1.6 (virgin-DB blind spot — the #131 D3 dirty-store target).

---

## Gates (independently re-run — counts pasted)
| gate | result | note |
|---|---|---|
| 4-file contract (`test_principal_delete_cascade_61` + `test_keep_remediation_store_61` + `test_keep_remediation_cli_61` + `test_principal_keys_schema`) `-n auto` | **63 passed** (12.03s) | matches builder + contract (33 pkt-61 pins + rest of pkt-49 schema contract) |
| `./scripts/typecheck.sh` | **0 errors** ("Success: no issues found" all members incl. test trees + shellcheck) | |
| `uv run ruff check .` | **All checks passed!** | |
| full suite `loremaster/tests -n auto` (CLEAN, alone) | **8410 passed / 0 failed / 0 errors** (50 skipped, 3 xfailed, 258s) | contention noise GONE; F1 fixed, 3 `TestDelete` green |
| `scripts/pending_contract_gate.py --currency` (CLEAN, alone) | **PASS** — manifest `(typecheck, ruff, pytest)` all GREEN, exit 0, NO RED_ORPHANED | #402's RED_ORPHANED → GREEN (the renamed pin is green inside the now-clean pytest leg); resolved, not re-baselined |
| `scripts/probe_member_of_cascade.py` | **exit 0** (positive controls on every leg) | LEG A member_of auto-cascades in=member 1→0; LEG B keep.keeper DANGLES; LEG C member_of auto-cascades out=keep 2→0 |

### Full-suite discrepancy (why the first run does NOT count)
My FIRST `pytest loremaster/tests -n auto` (launched at audit start, real tree) reported
**12 failed / 8352 passed / 53 errors** in 650s. BUT it ran CONCURRENTLY with my scratch mutation
runs — both hammering `ws://127.0.0.1:18000` with `-n auto`. The failing/erroring set is scattered
across UNRELATED store-touching files — `test_mcp_server::TestRenderInjectionRegistry` (16 errors,
all params of one test), `test_migration_wire`, `test_surreal_store::TestHybridSearch`,
`test_trace_telemetry`, `test_ingest_entity_seam` — and NONE touch `principals`/`keeps`/the 61a-w1
change. That scatter over store-touching tests, none in scope, is the signature of store-connection
contention under concurrent load, NOT a 61a-w1 defect. The currency gate's own pytest leg (also run
under that concurrent load) FAILED for the same reason (`RED with nobody's name on it: pytest`, the
ORPHAN list = the same scattered store-touching tests). Re-running CLEAN (nothing else on the store)
to establish the trustworthy count — pasted above when it lands.

---

## Mutation proofs (independently re-derived — do NOT trust the builder table)
Provenance-asserting scratch: `./scripts/scratch_copy.sh /tmp/lore-ca61`.
**`loremaster.__file__ = /tmp/lore-ca61/loremaster/loremaster/__init__.py`** (proven testing the
copy, not the original — #140). Baseline: **63 passed** on the pristine scratch. Each mutation = one
production defect; the two files restored byte-exact from `/tmp/ca61-{principals,keeps}.orig` (md5
re-verified) between runs.

| # | mutation (production defect) | pins that RED | controls GREEN | verdict |
|---|---|---|---|---|
| a | disable refuse-while-keeping (`if False and …`) | `test_deleting_a_keeper_raises…` FAILED (DID NOT RAISE) + the whole refuse/cascade class non-green (1 failed / 7 errors) | — | **caught** |
| b | `[:1]`-slice the kept-keep list | `…keeper_of_MULTIPLE_keeps_names_them_ALL` FAILED (missing 2 of 3 ids) | the 3 keeper-of-1 refuse pins PASS | **caught — N=3 discriminates the slice bug** |
| c | `set_keeper` drops ghost-KEEP guard ENTIRELY (silent `None` — the adversary's exact BLOCKER WB10) | store `test_set_keeper_on_a_ghost_keep_is_loud` + CLI `…of_a_ghost_keep_is_loud_and_nonzero` FAIL (rc 0) | other 5 set_keeper pins PASS | **caught — #403 fix genuinely closes the blocker** |
| d | `set_keeper` swallows the ghost-NEW-KEEPER resolution raise | store `…ghost_email_is_refused…` + CLI `…ghost_email_is_loud…` FAIL (rc 0) | other 5 set_keeper pins PASS | **caught — surgical (only 2 red)** |
| e | skip the keep-slice `ensure_ready` on the delete dispatch | `test_delete_readies_the_keep_slice_on_the_fly_when_the_keep_table_is_absent` FAILED w/ the exact undeclared-table `SurrealStoreError` | full-schema fixtures | **caught — #131 dirty-store pin is NOT theater** |
| f | move `set_keeper`'s check-first `get_keep` OUTSIDE the wrap-try | FR-2 Q2b `test_each_write_path_wraps_engine_rejection_as_KeepStoreError[set_keeper]` FAILED (injected `SurrealStoreError` escaped unwrapped) | other 20 param-cases PASS (incl. `[delete_keep]`) | **caught — wrap covers the internal read** |

All six discriminate; each paired with its passing positive-control. A pin that cannot be shown
failing is not a pin — all six shown failing.

---

## Reach-pin discrimination (the 3 NON-contract test edits are legitimate, not pin-weakening)
The builder edited `test_keeps_store.py` / `test_keeps_cli.py` (packet-60 REACH pins,
coverage-as-checked-variable) — CONFIRMED they GREW the DERIVED-set coverage maps
(`_WRITE_PATH_INVOCATIONS` += `set_keeper`/`delete_keep`; `_KEEP_VERB_GHOST_KEEP_ARGV` += `set-keeper`/
`delete-keep`), NOT deleted/loosened any pin. Mutation-proved the pins still RED on a removed
registration (in scratch): deleting `set_keeper` from `_WRITE_PATH_INVOCATIONS` →
`test_the_derived_write_path_set_matches_the_coverage_map` FAILED (derived-from-AST includes
`set_keeper`, map doesn't); deleting `set-keeper` from `_KEEP_VERB_GHOST_KEEP_ARGV` →
`test_the_derived_keep_verb_set_matches_the_ghost_keep_coverage_map` FAILED ("Extra items in the
left set: 'set-keeper'"). Coverage-as-checked-variable intact. `test_principals_store.py::TestDelete`
fixture edit: readies the keep slice after `principal` (F2) — a fixture-readiness alignment for the
new keep-table dependency, NOT a behavior change (see §F2).

## F2 — the keep-table coupling is safe (single caller)
`PrincipalStore.delete` now hard-requires the `keep` table (the refuse read). SOLE production caller
= `_cmd_delete` via `_dispatch` — CONFIRMED by grep (`principal_store.delete` / `.delete(email=`
appears once, `principals.py:1114`). lore_impact's "5 prod refs" is a polluted bare-name UNION with
`SurrealManifest.delete` (its own caveat says so; the 4 `Indexer._…` consumers are `self._manifest.delete`
calls, a different symbol). `_dispatch` readies the keep slice (`generate_keep_ddl`) BEFORE any
handler; the `delete` docstring warns future non-CLI callers. No unsafe caller exists → not a NO-GO.

## check-first / wrap interaction (subtle — both legs hold)
Class hierarchy (read from source): `KeepNotFoundError(KeepStoreError(RuntimeError))` — NOT a
`SurrealStoreError` subclass; `SurrealConnectionError`/`TxnContentionExhaustedError` DO subclass
`SurrealStoreError`. So in `set_keeper`/`delete_keep`'s check-first-INSIDE-try:
- a GHOST keep → `KeepNotFoundError` raised inside the try, matches NEITHER `except` → propagates
  UNWRAPPED (raises `KeepNotFoundError`, NOT swallowed into a generic `KeepStoreError`). ✓
- an engine `SurrealStoreError` during the internal `get_keep` read → matches the second `except`
  → WRAPPED as `KeepStoreError`. ✓ (proven live by mutation f: moving `get_keep` outside the try
  reds the FR-2 Q2b wrap pin — so INSIDE the try the internal read's engine error IS wrapped.)
Both hold.

## Exact-set pin rename + re-arm (do BOTH halves)
- (a) adjudicates `keep.keeper`: expected set = `{("principal", PRINCIPAL_KEY_TABLE),
  ("keeper", KEEP_TABLE)}` (renamed `test_principal_key_is_the_ONLY_record_principal_link` →
  `test_the_record_principal_link_set_matches_the_cascade_adjudication`). ✓
- (b) RE-ARMS: injected a synthetic `owner_principal_SYNTH: record<principal>` field into
  `_KEEP_FIELD_SPECS` (scratch) → the pin FAILED (`found` grew to 3, `!= expected`, "Extra items:
  ('owner_principal_SYNTH','keep')"). So it will red the day 63/64 add `owner_principal`. ✓
- (c) old name grep-discoverable: `test_principal_keys_schema.py:426` docstring "FORMERLY
  ``test_principal_key_is_the_ONLY_record_principal_link``". ✓

## Contract-blind removed-behavior inventory (fresh FRAME — "what did the old delete do that the new one doesn't?")
Read ONLY the `delete`-cascade diff. Item-by-item adjudication:
| old `delete` behavior | disposition |
|---|---|
| `get_by_email` → `PrincipalNotFoundError` on None | **PRESERVED** (line 685, and it runs BEFORE the new keep-read — a bad email still raises NotFound, never a keep-read crash) |
| `principal_id_part` derivation | **PRESERVED** (line 686) |
| count keys-to-cascade (`SELECT count() … GROUP ALL`) | **PRESERVED** (711–719, byte-identical) |
| ONE `execute_transaction`: DELETE principal_key children FIRST, THEN principal | **PRESERVED** (723–728, unchanged) |
| return cascaded key count | **PRESERVED** (719; pinned by `…loner…cascades_only_its_keys` = `cascaded==2`) |
| — the ONLY additions — | refuse-while-keeping read + `PrincipalHasKeepsError` (ADDED, 687–707); new keep-table dependency (F2, ADDED — adjudicated/guarded by D3 readiness + the #131 pin) |
No orphaned virtue: every old behavior survives and is pinned; the additions are guarded.

---

## Residuals (surfaced, none block GO)
1. **The first full-suite run's 12 failed / 53 errors was SELF-INFLICTED store contention**, not a
   defect — established by the clean re-run (8410 passed / 0 failed / 0 errors) + the fact that the
   contended failures were entirely in UNRELATED store-touching files (test_mcp_server,
   test_migration_wire, test_surreal_store, test_trace_telemetry, test_ingest_entity_seam), NONE in
   principals/keeps. LESSON FOR THE FLEET: do not run the full `-n auto` suite while a scratch
   `-n auto` mutation battery hits the same `ws://127.0.0.1:18000` store — the shared store tolerates
   per-test unique DBs but not unbounded concurrent WS connection pressure. (This did not affect any
   verdict; the clean re-run is the ground truth.)
2. **lore's OWN comms/memory backend (`ws://127.0.0.1:18500`, lore-surreal PROD) failed every
   `lore_comms` query for the whole audit** ("no close frame received or sent" on agent/brief/message
   queries). This is lore's dogfood infra, NOT the test store (`:18000`, which worked throughout).
   Consequence: I could not `lore_comms send` the lead a signal; I reached the lead via this report +
   a native SendMessage wake. Worth a look — if the fleet coordinates through `lore_comms`, a down
   `:18500` blinds it. (Not a 61a-w1 build defect.)
3. **F2 keep-table coupling has no STRUCTURAL guard for a FUTURE non-CLI caller.** The sole caller
   today (`_cmd_delete` via `_dispatch`) readies the keep slice, and the #131 dirty-store pin guards
   THAT path; a future direct caller of `PrincipalStore.delete` that forgets to ready the keep slice
   would crash on the refuse-read (raw `SurrealStoreError`), guarded only by the method docstring, not
   a pin. This is the D3 ruling's accepted design (the CLI is the only caller at 61); named here so it
   is met deliberately if 63/64 add a caller. Not a blocker.
4. **`_dispatch`'s except tuple catches `SurrealConnectionError` but not bare `SurrealStoreError`**
   (pre-existing pkt-49 pattern, unchanged by this wave). On the correct build the keep slice is
   readied (line 1302) before the refuse-read, so this never fires via the CLI; it would only surface
   if `ensure_ready` itself raised a non-connection store error, which is a broader failure than 61a-w1.
   Noted for completeness (matches the adversary's WB11 aside); not a new weakness, not a blocker.

## What I did NOT re-verify (honesty bound)
- The IndexScan-vs-TableScan EXPLAIN on the `keep_keeper`-index refuse read is a Fork-A packet-60
  claim the FR-4 rider inherits; I did not re-run EXPLAIN (the refuse read is a bounded count-style
  read either way, and correctness — not plan — is what 61a-w1 gates). Named per the honesty bound.
- I ran the probe once (exit 0 with positive controls); I did not re-run it 20× — it is a
  deterministic construction proof (create → delete → count), not a concurrency race.

## Verdict
**GO.** Every gate re-run GREEN/PASS (contract 63p · full-suite 8410p/0f/0e clean · typecheck 0 ·
ruff clean · currency PASS, #402 resolved · probe exit 0). Every load-bearing pin mutation-proven to
discriminate (6/6, each with a passing positive control). The 3 non-contract test edits are legitimate
coverage-map growth, still RED on a removed registration. F2 coupling safe (single caller). check-
first/wrap interaction correct in both directions. Exact-set pin re-arms. No orphaned virtue in the
delete rewrite. Residuals above are surfaced and none block. The lead may commit.

## Scratch trees (for cleanup)
- `/tmp/lore-ca61` — provenance-asserted `scratch_copy.sh` tree, RESTORED to pristine (all 4 mutated
  files reverted from `/tmp/ca61-*.orig`; production diff in the real tree is UNTOUCHED by my work).
- Backups: `/tmp/ca61-principals.orig`, `/tmp/ca61-keeps.orig`, `/tmp/ca61-tks.orig`, `/tmp/ca61-tkc.orig`.
- The contract/adversary left `/tmp/lore-sat-61a` + `/tmp/adv-61a` (per their reports). All are
  disposable `/tmp` scratch; lead/operator may `rm -rf /tmp/lore-ca61 /tmp/lore-sat-61a /tmp/adv-61a /tmp/ca61-*`.
