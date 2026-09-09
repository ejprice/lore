# REPORT — adversary-63b-ib-fork2-2 (RE-adversary after the FORK-2 B1 revision)

brief-base v14 read · brief project v7 read

## SUMMARY BLOCK
- **VERDICT: CONTRACT SUFFICIENT.**
- **P1 headline — did any wrong build survive?** No. The load-bearing B1 question — *"if a builder
  satisfied this contract but the corpse inventory MISSED a site, or the invariant pin's reach were a
  hidden constant, or the helper weren't actually shared, would the tests still pass (the same false
  all-clear one level down)?"* — is answered EMPIRICALLY NO on all three legs (M6/M7/M9 below).
- **Whole-suite satisfiability (ALONE, ref build = `patch_ref.py ref`):** `9973 passed, 51 skipped,
  3 xfailed, 0 FAILED, 0 errors, EXIT=0` (323s) — reproduces the reviser exactly, and IS the
  exhaustiveness proof (any un-rewritten corpse reds here on the correct build).
- **Corpse inventory RE-DERIVED (not relayed):** from the B1 diff `a047eea..ae180c9`, **21 corpse
  lines removed** (all verbatim `type(x) is SurrealStoreError`), **19 → `assert_domain_rejection()`
  + 2 M → `type(x) is domain_type`, P=0**. Matches the reviser's inventory site-for-site.
- **QUANTIFIER TABLE (P1b)** and **REACH TABLE (P1c)** for the B1 additions: below; riders i–vii
  carried over from `REPORT-adversary-63b-ib-fork2.md` (unchanged by B1 — see M-riders row).
- **MISSING PINS: none.** Two forward-looking RESIDUALS surfaced (bounded, not blockers): the
  skipped-test / non-`type-is-base`-spelling gap, and the ban's exact-base-mint constraint.
- Fixture-discrimination: every B1 pin DISCRIMINATES (helper flip 19→19; disjointness reparent → red;
  reach plant → red; W4 → 2 M-pins + I-callers red; positive control at HEAD → all red for UNBUILT).
- Graded: `ae180c9` · HEAD-at-report: `ae180c9` · SAME.
- Packages considered: none — I graded a CONTRACT and specified no mechanism; probes reuse stdlib
  `ast`/`tomllib` + the repo's `scripts/scratch_copy.sh` and the first adversary's `patch_ref.py`.
- Reuse ledger: none — an adversary authors no reusable production/test symbols.
- decisions-needed (lead): none from me. #461 (pending_contract_gate mypy self-destruct) + #460
  (pre-existing ruff E501) are NOT docked (gate bug + pre-existing, per brief) — they do not bear on
  the contract's satisfiability or pins.
- receipt pointers: §"WHOLE-SUITE SATISFIABILITY" · §"CORPSE EXHAUSTIVENESS" · §"P1c REACH TABLE" ·
  §"P1b QUANTIFIER TABLE" · §"MUTATION RECEIPTS" (helper/disjointness/reach/W4/positive-control) ·
  §"RESIDUALS".

## CAPABILITY CHECK
- lore tools loaded via `ToolSearch "+lore"` (keyword form) — FIRST CHOICE (`lore_get_symbol`,
  `lore_index`, `lore_comms`). Fallbacks SAID OUT LOUD: `grep`/`rg` is HOOK-BLOCKED this session
  (whole repo AND pytest stdout), so the corpse re-derivation is a Python string-scan over `git diff`
  output (dogfood grep-class case (b): assertion-spelling sweep) and pytest tails use `--tb=line`/`tail`.
- Index FRESH at grade time: `lore_index` → `git_ref = ae180c93c500...` == HEAD, watched root
  `/workspace` branch `feat/surreal-unification`, swept 155s ago, 3733 files, 0 failed. I graded the
  tree lore indexed.
- Store: `ws://127.0.0.1:18000` (spike-surreal, TEST) only — never :18500. `lore_comms register`
  hit the prod-:18500 #422 error once, succeeded on the immediate retry.
- Scratch provenance (#140): `loremaster.__file__ =
  .../scratchpad/ref_ib_fork2_2/loremaster/loremaster/__init__.py` — INSIDE the copy; `scratch_copy.sh`
  asserted it non-zero for all four members.
- No production/store/DDL touched. COMMIT-ONLY; no git state mutated. No code or tests edited in the
  repo (all mutations lived in the scratch copy, restored after each).

---

## THE LOAD-BEARING B1 QUESTION, ANSWERED ON ALL THREE LEGS

The B1 blocker was INSTRUMENT-0's reach class caught at contract time: the retype's 2-file satisfiability
scope hid a suite-wide corpse surface. The revision's own fix could reproduce the SAME class one level
down. I attacked exactly that:

| the "one level down" false clear | would the tests still pass? | instrument that refutes it | receipt |
|---|---|---|---|
| a corpse the inventory MISSED survives unrewritten | **NO** | ref-build whole-suite (executed) **+** invariant pin GREEN at HEAD (textual, incl. skipped) | 9973/0; invariant 3 passed, 0 offenders |
| the invariant pin's REACH is a hidden constant (`loremaster/tests` only) | **NO** | reach DERIVED from `[tool.uv.workspace] members`; empirical plant in `lorerunes/tests` flagged | flagged `lorerunes/tests/_adversary_reach_probe.py:7` |
| the shared helper isn't actually shared (a private copy wears its name) | **NO** | flip `assert_domain_rejection`'s predicate → EVERY caller reds | 19 passed → 19 failed → restored |

No wrong build survived. The revision closes the class it was written to close.

---

## WHOLE-SUITE SATISFIABILITY (deliverable #1 — the C-DEF, suite-wide, ALONE)

Reference build = the first adversary's `patch_ref.py ref` (reused verbatim) applied to a
`scratch_copy.sh` copy of HEAD `ae180c9`. Verified faithful before the run:
- provenance INSIDE the copy (all four members resolve inside `ref_ib_fork2_2/`);
- MRO `TxnGovernedConflictError → TxnDomainRejectionError → SurrealStoreError → RuntimeError`;
- all four disjointness relations hold; the DOMAIN-scoped `isinstance(error, TxnDomainRejectionError)`
  compensation gate, the retire-P line, and the pair-guarded replay close are all present.

Run ALONE (nothing else store-touching concurrent — the reviser's spurious 48F/390E came from
contending runs; I never ran two store suites at once):
```
uv run pytest loremaster lorerunes loresigil lorescribe -n auto --tb=line -q   # in the ref scratch
9973 passed, 51 skipped, 3 xfailed, 7 warnings in 323.27s (0:05:23)
EXIT=0
```
0 FAILED, 0 collection errors (I kept the configured `--import-mode=importlib`; the smoke-collection
artifact the reviser saw under `-o addopts=""` did not appear). Every RED-until-built pin (the 21
corpse rewrites + the 2 M-pins + the disjointness pin + the committed §2.4 riders) goes GREEN on the
reference build; the invariant pin is GREEN (0 offenders). The **harder leg** (satisfiable after lint
cleanups) is carried by the reviser's ruff-clean receipt; I did not re-run ruff/mypy (the currency
verdict is #461/#460, lead-owned, explicitly out of my grading scope).

**Positive control** (my own probe can distinguish the builds): at HEAD, with no production change,
the same pins are RED for the RIGHT reason —
```
test_surreal_store.py::…test_the_domain_rejection_helper_maps_the_governed_label_to_the_typed_error
test_memory_supersede_atomicity_63b_ib.py::…test_the_typed_domain_class_exists_and_governed_conflict_subclasses_it
2 failed  →  "loremaster.store._txn.TxnDomainRejectionError is UNBUILT (§2.4-1) — RED-until-built"
```
via the `getattr(_txn, "TxnDomainRejectionError", None)` idiom (a legible assertion, never an
ImportError/collection error). So the ref-build greenness is a fact about the build, not a vacuous pass.

## CORPSE EXHAUSTIVENESS (deliverable #2 — re-derived from EXECUTION and the diff, not relayed)

Two independent enumerations, DIFFED (the P6/P6b discipline):

1. **From the B1 diff** `a047eea..ae180c9` (Python scan, grep hook-blocked): **21 removed corpse lines**,
   every one verbatim `assert type(<x>) is SurrealStoreError`, distributed:
   `test_surreal_store.py` 7 · `test_surreal_manifest.py` 4 · `test_graph_surreal.py` 2 · and 1 each in
   `test_agent_registry / test_brief_ledger / test_diff / test_findings / test_memory_backend /
   test_snapshots / test_surreal_apply / test_task_ledger`. Additions: **19 `assert_domain_rejection()`
   call statements** (one per I-site) **+ 2 `type(x) is domain_type`** (both in `test_surreal_store.py`,
   the M-sites). **P=0** — no removed corpse was left as a plain-base assertion.
2. **From execution:** the whole-suite ref run reds ZERO tests → no un-rewritten corpse survives among
   executed tests. The invariant pin GREEN at HEAD (0 offenders across the whole test tree, AST — so it
   covers the 51 skipped tests too) → no textual `type(x) is SurrealStoreError` survives anywhere.

The two agree. M/I classification spot-check (P-class honesty): the 2 M-sites (`:912` helper-mapping,
`:1036` seam ×2) genuinely assert what `_domain_rejection_error` MINTS, using variable refs
(`domain_type`/`governed_type`) — so exact-type on the leaf is the contract, and the invariant pin does
NOT false-flag them (`_is_banned_base_ref` only matches the `SurrealStoreError` name). Proven REAL, not
vacuous, by W4 (below): both red on a wrong mapping build. The 19 I-sites are intent pins ("a store
rejection, not a connection error; connection kept; hygiene") that keep their own
`not isinstance(..., SurrealConnectionError)` / hygiene lines and route the type check through the
shared helper.

## P1b — QUANTIFIER TABLE (the B1 additions; riders i–vii carried over)

| invariant | classification | receipt |
|---|---|---|
| **the domain-rejection classification is the TYPED class, ∀ domain-reject fixtures** (the 19 I-callers) | **∀ over the I-caller fixtures** — one shared predicate, forced at 19 real domain-reject sites across 11 files/8 subsystems | flip the ONE helper predicate → all **19 red**; helper intact → all 19 green (M7). A private copy would have stayed green — none did. |
| **`_domain_rejection_error` mints the typed leaf for EVERY domain label** (M-pins :912/:1036) | **∀ over {governed, non-governed} × {unit helper, both live seams}** — :912 forces the unit mapping (governed→governed leaf, non-governed→domain leaf); :1036 forces BOTH `execute_transaction` and `execute_read_transaction` | W4 (mapping→plain `SurrealStoreError` for non-governed) reds :912 AND both :1036 params → ROUTING-IS-SHARING: both raise sites route the one helper. |
| **the type hierarchy is disjoint** (`D<:S`, `G<:D`, `¬C<:D`, `¬X<:D`) | **∀ over the four required relations** — all asserted in one pin | reparent `SurrealConnectionError` under `TxnDomainRejectionError` → the `¬C<:D` leg reds with the delete-on-transport message (M8). The other three legs are forced by the ref-build MRO check. |
| **no test exact-type-checks the non-leaf base, ∀ test files in ∀ members** (invariant pin) | **∀ over the workspace test tree** — reach DERIVED, coverage a checked variable | plant a banned spelling in `lorerunes/tests` → flagged by file:line (M9); non-vacuity + discrimination legs green. |
| riders i–vii (transport-keeps-row / 2×2 ∀-shapes / one-mapping / typed-not-name-scan / pair-guard / foreign-rebuild / prose-sweep) | **unchanged by B1** | B1 touched no rider file (diff: only `_surreal_harness.py`, 11 corpse files, the new invariant pin, `test_surreal_harness.py`, `pending_contracts.yaml`). W4 confirms the mapping/routing discrimination still fires. First adversary's table stands. |

Every guarded row carries a surviving-or-killed receipt; no cell is vacuously green.

## P1c — REACH TABLE (each guard the B1 revision introduces or relies on)

| instrument | reach DERIVED vs hand-list | coverage a checked variable | effect vs proxy | one-source / mutation | verdict + leg |
|---|---|---|---|---|---|
| **invariant pin** `test_no_exact_type_check_on_surreal_store_error.py` | **DERIVED** — `parse_production_trees(include_tests=True)` re-adds `<member>/tests` for every `_declared_workspace_members()` read straight from `pyproject.toml` (never a hand-list; `loremaster/tests` is NOT special-cased) | **YES** — `assert_scan_reached_every_member` asserts `scanned == declared∪{scripts}` from an INDEPENDENT pyproject read, FAILS CLOSED on empty; non-vacuity `≥40 files` + `≥1 adoption` | **EFFECT** (AST offenders by file:line), not a proxy | single shared parser; a private clone is caught by `test_ast_reach_helpers.py` | **SOUND — EMPIRICAL.** Plant in `lorerunes/tests` → flagged `…:7`; M-leaf + isinstance NOT flagged; removed → 3 passed. `test_ast_reach_helpers.py` 50 passed (HOME accepts / private-parse narrowing guard live). |
| **`assert_domain_rejection` helper** | reach = the 19 I-call sites | **YES** — the invariant pin's non-vacuity leg reds if adoptions drop to 0; the ban reds if any I-site reverts | EFFECT (the raised exception's type) | **ONE source, proven by MUTATION** | **SOUND — EMPIRICAL.** 19→flip→19 (M7). |
| **disjointness pin** | reach = the 4 relations among the 5 store-error classes | forced by the ref-build MRO | EFFECT (`issubclass`) | n/a (a hierarchy assertion) | **SOUND — EMPIRICAL.** reparent → the `¬C<:D` leg reds (M8); stays GREEN under W4 (orthogonal to the mapping — not a false red). |
| **`pending_contracts.yaml` RED_ADJUDICATED bound** | reach = the **13** red files (11 corpse + 2 §2.4 contract) | file-level (`partition_pytest` matches `outcome.file`) — the masking window is DISCLOSED in the entry's rationale | self-destructs on `hasattr(TxnDomainRejectionError)` | one owned bound + reopen trigger | **SOUND — CONSTRUCTION.** 13 files match my re-derived red set exactly; owner + trigger named; #461 (mypy self-destruct misfire on a pytest-only bound) is a gate bug, not a contract defect — not docked. |
| **corpse-derivation textual scan (reviser's)** | assertion-spelling sweep, bare/anchor-free, both operand orders, `type()/.__class__/.type` | reconciled 3 ways (scan==AST==execution) | effect | — | **SOUND — RE-DERIVED.** My independent diff scan reproduces the 21/19/2/P=0 split. |

Legs run: invariant-reach, helper-sharing, disjointness, W4, and the positive control were EMPIRICAL
(scratch mutations, provenance-asserted). The registration and textual-scan rows are
construction-inspection + re-derivation. Every negative result is paired with a positive control (P0):
19 green before the flip; the M-leaf/isinstance NOT flagged; the disjointness pin GREEN under W4;
pins RED at HEAD for the UNBUILT reason.

## MUTATION RECEIPTS (commands + real output)

**M7 — helper sharing (store, ALONE).** 19 I-caller nodes collected by AST (functions whose body calls
`assert_domain_rejection`); count 19, matching the inventory (5 surreal_store, 4 surreal_manifest,
2 graph_surreal, 8×1).
```
BASELINE (helper intact, ref):  19 passed in 5.80s
MUTATED  (isinstance→not isinstance in _surreal_harness.assert_domain_rejection):  19 failed in 6.43s
RESTORED ok: True
```

**M8 — disjointness (no store).** Runtime hierarchy flip appended after both classes exist
(`SurrealConnectionError.__bases__ = (TxnDomainRejectionError,)` — a faithful stand-in for a source
reparent, which would be a forward-ref NameError given `SurrealConnectionError` is defined at L123
before `TxnDomainRejectionError` at L189; the pin checks `issubclass` at runtime, so the effect is
identical). `issubclass(SurrealConnectionError, TxnDomainRejectionError)` became True.
```
BASELINE: 1 passed
MUTATED:  1 failed — "SurrealConnectionError must NOT be a TxnDomainRejectionError — a transport
          failure is KEPT (the loss path §2.2 …)"   assert not True
RESTORED (no mutation marker left): True
```

**M9 — invariant-pin reach (no store).** Planted `lorerunes/tests/_adversary_reach_probe.py` with a
banned line + an M-leaf line + an isinstance line.
```
WITH PLANT:  1 failed — offenders == ['lorerunes/tests/_adversary_reach_probe.py:7']  (banned line only)
REMOVED:     3 passed  (ban 0 offenders, discrimination control, non-vacuity)
```

**W4 — mapping mutation (store, ALONE).** `patch_ref.py w4` (non-governed label → plain
`SurrealStoreError`):
```
5 failed, 1 passed:
  FAILED …TestDomainRejectionErrorType::test_the_domain_rejection_helper_maps_the_governed_label…   (M :912)
  FAILED …::test_a_governed_conflict_throw_via_the_transaction_seam…[execute_transaction]           (M :1036)
  FAILED …::test_a_governed_conflict_throw_via_the_transaction_seam…[execute_read_transaction]      (M :1036)
  FAILED …TestRecordTraceErrorPosture::test_domain_rejection_raises_store_error_and_keeps_connection (I)
  FAILED …test_task_ledger…TestQueryClassifiedErrorPosture::…never_echoes_the_raw_engine_text        (I)
  PASSED …TestDomainRejectionErrorType::test_the_typed_domain_class_exists…  (disjointness — orthogonal, correctly green)
```
The 2 M-pins are REAL discriminating pins; both `:1036` params red → both raise sites route the one
`_domain_rejection_error` (routing-is-sharing); the I-callers red through the shared helper; the
disjointness pin correctly does NOT false-red on a mapping-only change.

## RESIDUALS (each an individual verdict — scope law; NONE is a blocker)

- **R1 — the skipped-test / non-`type-is-base`-spelling gap (bounded).** The two exhaustiveness
  instruments together cover: all textual `type(x)/.__class__/.type is|== SurrealStoreError` (executed
  OR skipped, via the AST invariant pin) **+** all EXECUTED old-world assertions of any spelling (via
  the ref-build whole-suite). The single uncovered case is a SKIPPED test asserting a retired domain
  rejection via a spelling OTHER than the banned three (e.g. `x.__class__.__name__ == "SurrealStoreError"`).
  All 21 real corpses used exactly the `type(x) is SurrealStoreError` idiom (verified verbatim), so this
  is low-probability; I did not find one. **Verdict: named bound, not a missing pin.** Re-open trigger:
  a skipped test that pins a domain rejection by class-NAME string.
- **R2 — the ban forbids an exact-base MINT contract (forward-looking).** The invariant pin bans
  `type(x) is SurrealStoreError` unconditionally; its M-exception is only for LEAF subclasses. If
  production ever deliberately mints a BARE `SurrealStoreError` (base instance, not a subclass) that a
  test must pin EXACTLY ("this is the bare base, not any subclass"), the ban blocks the natural spelling.
  P=0 today (no such site; whole-suite green), and the ruling's intent is that the base become
  effectively abstract (every store error classified), so this is by design. **Verdict: named bound, not
  a missing pin.** Re-open trigger: production deliberately mints a bare `SurrealStoreError` a test must
  pin by exact type.
- **R3 — `assert_scan_reached_every_member` checks PACKAGE coverage, not TEST-DIR coverage directly.**
  It verifies each declared member's package entered the scan; a member's `<member>/tests` entering is
  guaranteed instead by the SHARED `parse_production_trees` derivation (same `_declared_workspace_members`
  source), which I proved reaches `lorerunes/tests` empirically (M9). So the reach is genuinely derived,
  just via the parser rather than the coverage assertion. **Verdict: SOUND, noted for transparency; not a
  gap.**
- **#461 / #460 (currency gate):** the mypy self-destruct misfire on a pytest-only bound (#461) and the
  pre-existing ruff E501 (#460) are gate/pre-existing issues, lead-owned, and per the brief NOT docked
  against this contract. The contract's pytest bound is RED_ADJUDICATED (owned) — correct.

## VERDICT: CONTRACT SUFFICIENT

The B1 revision is the reconciliation the retype always implied. I tried to break it on the exact axis
that born the blocker — a false all-clear one level down — and could not: the corpse set is complete
(re-derived + whole-suite + invariant pin, three ways), the shared helper is provably shared (mutation),
the invariant pin's reach is a checked variable derived from the workspace manifest (empirical plant in
a sibling member), the two M-pins and the disjointness pin are real discriminating pins (W4 + reparent),
and the whole suite is satisfiable ALONE against a faithful reference build (9973/0). The original riders
i–vii are untouched by the revision and their discriminations survive. No missing pin; two honest
forward-looking bounds surfaced.
