# REPORT-adversary-cycle-04b3-2 — fresh adversarial grade of the REVISED (variant-D) CYCLE contract

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first)
- **lore tools:** reachable and used (registered `adversary-cycle-04b3-2`/`pkt04b3`; `lore_get_symbol`
  resolved `_refuse_a_cycle`/`_read_dependency_graph`/`_record_legacy_cycles`/`_drop_one_cycle_edge`/
  `find_blocked_by_cycle`/`transitive_blockers`; `lore_comms` registered). No grep fallback for a
  structure question except `_read_dependency_graph` caller-exhaustiveness (grep's honest case,
  corroborated by lore: one real caller `_refuse_a_cycle` + one docstring ref).
- **spike-surreal :18000:** reachable (`/health` → 200; every reference/wrong build + the durable
  MP-1 fixture + two bespoke probes ran against `ws://127.0.0.1:18000`, never :18500).
- **`./scripts/scratch_copy.sh`:** ran clean; provenance ASSERTED.
  **`loremaster.__file__ = /tmp/adv_cyc_d/loremaster/loremaster/__init__.py`** (#140 receipt — every
  build below graded the SCRATCH tree, not the original).
- No unmeetable demand.

## SUMMARY BLOCK
- **VERDICT: CONTRACT SUFFICIENT.** I tried hard to break it and could not: no WRONG build survives
  the full contract. The prior trilemma is RESOLVED by variant D, and every horn is caught by exactly
  its intended pin.
- **P1 headline — did any wrong build survive?** NO. Variant **S** (single-witness, unsound) fails
  EXACTLY **MP-1**; variant **R** (from-minted 2nd detector) fails EXACTLY **R6**; a hand-roll
  (Dhandroll) fails **MP-4 + count**; a no-op fix fails the bounded-read/MP-4 pins.
- **SATISFIABILITY RECEIPT: POSITIVE (both legs).** Variant **D** (R7 one-round-trip bounded read +
  `networkx.simple_cycles` swap in `_record_legacy_cycles`, KEEPING the guard drop-loop and
  `_drop_one_cycle_edge`) = **213 passed / 0 failed**; harder leg after `ruff --fix` (import
  organization, the lint the swap demands) = **213 passed / 0 failed**, ruff clean. Collateral
  `test_task_ledger.py` = **240 passed** (no `_read_dependency_graph` test refs; concurrency intact).
- **THE PRIOR TRILEMMA MUST NOT REGRESS — reconfirmed on the REVISED contract:**
  (R) from-minted → **1 failed = R6** (`test_MUTATION_neutralising_the_SHARED_detector...`).
  (S) single-witness → **1 failed = MP-1** (`test_a_MINTED_cycle_COEXISTING_with_a_LEGACY_cycle...`,
  DID NOT RAISE). (D) drop-loop → **0 failed**. Each horn caught by its pin; D is the clean build.
- **MP-1 is the load-bearing pin and it WORKS:** variant S passes all 212 OTHER pins (incl. the
  isolation persisted-cycle pin) and dies ONLY on MP-1 — the QUANTIFIER-LAW fix operating exactly as
  designed.
- **MP-4 × import-form (author-flagged hole VERIFIED):** SAFE — no false-green (Dhandroll hand-roll
  fails MP-4). But it FALSE-REDs a `from networkx import simple_cycles` correct-routing build (Dfrom):
  MP-4 patches `networkx.simple_cycles`, which no-ops on the import-time local binding. Documented by
  the pin/import docstrings (module form required); over-strict, not a hole. Residual R-1.
- **FORK-C tripwire:** LIVE WIRE — control `[]` → future-verb world 2 ids → `after==set()` would
  redden. Honest deferral.
- **Packages considered:** `networkx` 3.6.1 (READ: `networkx.simple_cycles` = Johnson's
  all-simple-cycles, the exact enumeration #273 needs; installed) → **replace** (agree w/ author);
  `graphlib.TopologicalSorter` (READ: `.prepare()` raises `CycleError` with `args[1]`=the cycle) →
  **keep** as the shared one-witness detector (agree). No mechanism marked `bespoke` that a library
  covers. **P-PKG diff clean.**
- **Graded:** `e22c43a` · HEAD-at-report: `4d81f76` · **DIFFERENT (2 behind)** — but the 2 commits
  are the `lore_comms` body-cap (#327), a SEPARATE task; `git diff --stat e22c43a..HEAD` over the
  graded surface (both test files, `tasks.py`, `scripts/cycle_coexisting_legacy_soundness_probe.py`)
  is EMPTY. This grade holds byte-identical at HEAD.
- **Residuals (non-blocking, none admits a wrong build):** R-1 MP-4 false-RED on from-form; R-2 R7
  one-snapshot claimed-not-pinned (2-round-trip bounded read passes; verb-unreachable per FORK-C);
  R-3 `Cost:` docstring is DERIVED — a multi-round-trip build obliges a bump §ESC-1-FLAGS omits (the
  one-round-trip build avoids it). §5 quantifier table · §6 residuals.
- receipt pointers: satisfiability + trilemma §1 · MP-1/§2 · MP-4 import-form §3 · FORK-C §4 ·
  quantifier table §5 · residuals §6 · instruments §7 (pasted). Durable MP-1 fixture
  `scripts/cycle_coexisting_legacy_soundness_probe.py` (REFUSED @HEAD real tree, exit 0 — sound).

---

# §1 · SATISFIABILITY + the trilemma (P1 wrong-build results)

**Method.** `scratch_copy.sh` → `/tmp/adv_cyc_d` (provenance asserted, `loremaster.__file__` in-scratch).
A patch generator (`/tmp/adv2_patch.py`, pasted §7) builds each production variant from the pristine
`tasks.py` (HEAD `e22c43a`, `/tmp/tasks_pristine.py`), asserting every anchor lands exactly once
(#194). Graded set = the two whole contract files (matching the lead's 4-RED/209-passed baseline):
```
loremaster/tests/test_cycle_write_path_04b3.py
loremaster/tests/test_blocks_edge.py
```

### RED honesty (P7) — reproduced EXACTLY on the pristine scratch tree
```
4 failed, 209 passed in 8.84s
FAILED …TestTheAllCycleEnumeratorIsNetworkxInPRODUCTION::test_networkx_is_imported_by_the_PRODUCTION_tasks_module
FAILED …TestTheEnumerationEQUALSNetworkxAfterTheSwap::test_MUTATION_neutralising_networkx_simple_cycles_SILENCES_the_record
FAILED …TestTheEnumerationEQUALSNetworkxAfterTheSwap::test_the_RECORDED_cycle_count_equals_networkx_simple_cycles[complete-triangle]
FAILED …TestCreateRefusesToFormACycle::test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE
```
Each RED for the right reason: networkx absent from `tasks.py` source; MP-4 hand-roll ignores the
patch (records 4); complete-triangle 4≠5; bounded-read 63 rows vs 8 (whole-population scan).

### Variant D — the RULED build (bounded read + networkx swap, KEEP drop-loop + `_drop_one_cycle_edge`)
```
213 passed in 8.63s          # full contract, both files
```
Harder leg (`ruff check --fix loremaster/loremaster/tasks.py` moved `import networkx` to the
third-party group — 1 fixed, All checks passed), re-run:
```
213 passed in 8.49s
```
Collateral (the sibling tasks suite, to prove the rename/read-swap breaks nothing):
```
loremaster/tests/test_task_ledger.py … 240 passed in 6.31s
```
The bounded read is ONE round trip (R7-faithful): `SELECT record::id(id) AS id, blocked_by FROM task
WHERE id IN array::distinct(array::flatten(array::concat([$starts], (SELECT VALUE
@.{1..32+collect}(<-blocks<-task) FROM $starts))))` — proven against the store to return the exact
ancestor closure for a real seed and 0 rows (no error) for ghost batch-sibling seeds (§7 probe).
**The satisfiability receipt is POSITIVE — a correct build achieves 0-failed, before AND after lint.**

### Variant S — single `find_blocked_by_cycle` witness + `minted.intersection` (NO drop-loop)
```
1 failed, 212 passed in 8.03s
FAILED …TestCreateRefusesToFormACycle::test_a_MINTED_cycle_COEXISTING_with_a_LEGACY_cycle_in_the_closure_is_REFUSED
E   Failed: DID NOT RAISE <class 'loremaster.tasks.TaskLedgerError'>
```
**S dies on EXACTLY MP-1 and NOTHING ELSE** — it passes the isolation persisted-cycle pin, the
batch/self pins, the bounded-read pin, networkx, count, R6, everything. This is the single most
important result of the grade: MP-1 is precisely the pin the whole revision turns on, and it reddens
the unsound single-witness build that passed the pre-revision contract. Confirmed at the store level
too (durable fixture, §7): S ACCEPTS `N→seed→X→N` when a legacy `P↔Q` coexists.

### Variant R — from-minted reachability via a NEW `_cycle_through` (second detector)
```
1 failed, 212 passed in 9.06s
FAILED …TestTheCyclePolicyHasONEImplementation::test_MUTATION_neutralising_the_SHARED_detector_lets_BOTH_shapes_through
E   loremaster.tasks.TaskCycleError: blocked_by cycle among task ids: … (raised with find_blocked_by_cycle neutralised)
```
**R dies on EXACTLY R6** — with `find_blocked_by_cycle` monkeypatched to accept-everything in both
modules, R's private `_cycle_through` still refuses, proving a SECOND ledger detector. R6 stands; the
from-minted horn is correctly rejected by the operator-ruled ONE-IMPLEMENTATION pin.

**Trilemma verdict:** the three horns are exhaustive and each is caught by ITS pin — (S)→MP-1,
(R)→R6, (D)→0-failed. The revision does not regress; it RESOLVES the trilemma. Variant D is the clean
correct build, and it is the one HEAD already implements for detection (drop-loop) — ESC-1's only
guard change is the bounded read.

---

# §2 · MP-1 — the coexisting-legacy-cycle soundness pin (the load-bearing horn)

MP-1 (`test_a_MINTED_cycle_COEXISTING_with_a_LEGACY_cycle_in_the_closure_is_REFUSED`) is GREEN on
HEAD/D and RED on S (§1). Why it discriminates, verified by construction:

- The fixture seeds a legacy 2-cycle `P↔Q` (ids `aaap`/`aaaq`) AND a minted cycle `N→seed→X→N`
  (`X.blocked_by=[P, new_id]` is the COLUMN-ONLY closing link; no edge, `ENFORCED` forbids it), with
  `blocks` edges so the bounded EDGE-walk from `seed` reaches `{X,P,Q}`.
- `find_blocked_by_cycle` SORTS nodes, so `aaa* < zzz*` ⇒ it returns the LEGACY cycle first.
- **Variant S** takes that single witness, `minted∩{aaap,aaaq}=∅`, and ACCEPTS the create → an
  unclaimable-forever task. **Variant D** drops one legacy edge, loops, finds the minted cycle,
  `minted∩≠∅`, REFUSES.
- The id-ordering is LOAD-BEARING and correctly matched to the SHARED detector's actual sort — so the
  pin catches the natural single-`find_blocked_by_cycle`-witness build (the only build the revision's
  soundness is threatened by). Robust.

**QUANTIFIER-LAW check:** the sibling `..._through_PERSISTED_tasks_is_REFUSED` (isolation) is a
∀-over-inputs claim evaluated on the one input where EVERY build agrees — S passes it (§1). MP-1 adds
the input where they DIVERGE. The two together are ∀ over {isolated cycle, cycle-coexisting-with-
legacy}. The fix is correct.

---

# §3 · MP-4 × import-form — the author-flagged hole, VERIFIED (residual R-1)

Substring ground truth (`/tmp/substr_check.py`, §7): the import pin asserts `"import networkx" in
source`.

| import form | `"import networkx" in source` |
|---|---|
| `import networkx` | **True** |
| `from networkx import simple_cycles` | **False** |
| `import networkx` + `from networkx import simple_cycles` | **True** |

So a **pure `from` build fails the import pin** (hole closed for pure-from). The reachable case is the
**combo**, tested by two builds:

- **Dfrom** (`import networkx` decorative + `from networkx import simple_cycles`, CALL via the local
  binding — genuinely routes through the library): import pin GREEN, count-equality GREEN (5 records,
  incl. complete-triangle), member-coverage GREEN, **MP-4 RED** — MP-4 patches `networkx.simple_cycles`
  but the call uses the import-time-bound local `simple_cycles`, so the patch no-ops and the record
  stays 5. **MP-4 false-REDs a CORRECT routing build.**
- **Dhandroll** (`import networkx` + hand-rolled enumeration KEPT): count-equality[complete-triangle]
  **RED** (4≠5) AND **MP-4 RED** (records 4≠0). **MP-4 catches the actual hand-roll — TRUE POSITIVE.**

**Verdict:** MP-4 is SAFE — it has NO false-green (no hand-roll passes it; Dhandroll dies on it). Its
only imperfection is a false-RED on the `from`-combo correct-routing build, which the import-pin and
MP-4 docstrings already declare requires the `import networkx` MODULE form. Since a correct build
(module form, variant D) passes MP-4, this is NOT a C-DEF — it over-constrains the builder to the
module form rather than admitting a wrong build. **Residual R-1**, minor.

> Optional hardening (author's call, not a blocker): make MP-4 robust to import form by neutralising
> the enumeration at the point of use (e.g. patch a module-level alias `_SIMPLE_CYCLES` that
> `_record_legacy_cycles` calls) OR add a pin that the swap uses the module-attribute call
> `networkx.simple_cycles(...)`. Today the two docstrings carry the requirement in prose; a false-RED
> steers the builder correctly, so this is a refinement.

---

# §4 · FORK-C — the deferral tripwire is HONEST (re-confirmed, not a finding)

`/tmp/forkc_probe.py` (§7) constructs the future-verb world on spike :18000:
```
CONTROL (today's verbs): transitive_blockers(blocker) = []   -> tripwire assertion 'after==set()' holds
FUTURE VERB world:       transitive_blockers(blocker) = ['786e…','eef7…']
VERDICT: tripwire assertion 'after==before==set()' would REDDEN (live wire ✓)
```
Creating dependents of a blocker adds NOTHING to the blocker's ancestor set today (control), but a
raw `blocked_by` mutation + mirrored edge (standing in for an `add_blocker`/re-parent verb) grows it —
so `test_PIN_THE_MISS_a_tasks_blocked_by_is_FIXED_at_birth` reddens the day that verb lands. CA-11
stays legitimately DEFERRED on that trigger; nothing owed.

---

# §5 · The QUANTIFIER TABLE (P1b)

| invariant (pin) | ∀-over-inputs or guarded | receipt |
|---|---|---|
| persisted-id cycle refused in ISOLATION (`…PERSISTED_tasks_is_REFUSED`) | **GUARDED — "a cycle in isolation"** | variant S PASSES it (§1) yet is unsound; MP-1 closes the gap. |
| **minted cycle coexisting with legacy cycle refused (MP-1)** | **∀ over the coexisting input** | variant S FAILS it (§1/§2), D passes. The QUANTIFIER-LAW fix. Store-level control in §7. |
| write-path read is BOUNDED (`…BOUNDED_by_the_ancestor_CLOSURE`) | **∀ over dependency-bearing population** | RED 63 vs 8 @HEAD, constant on D. `small.rows>0` blocks the read-nothing build; `large.rows<60` sibling blocks the whole-table build. Discriminates. |
| batch-key / self cycle refused | ∀ over pending-OVERLAY cycles | green on D/S/R (overlay-based, independent of the read). Adequately pinned. |
| recorded ENUMERATION count == `networkx.simple_cycles` | **GUARDED — 3 FIXED topologies (only complete-triangle discriminates)** | Dhandroll fails ONLY complete-triangle (§3); disjoint/overlapping agree hand-roll==networkx. Backstopped by MP-4 (routing) — a hand-roll cannot escape both. |
| #273 ROUTES through the library (MP-4) | **∀ over the ENUMERATION, module-form only** | Dhandroll RED (true positive, §3). SAFE: no false-green. False-RED on the from-form (R-1). |
| ONE ledger-owned detector (R6 MUTATION pin) | ∀ (neutralise → both shapes accepted) | variant R reddens it (§1); D passes. |
| member coverage ∀ topology | ∀ over topology | green both sides of the swap (D + Dhandroll). |
| a task's ancestor set is FIXED at birth (FORK-C tripwire) | ∀ over creates | live wire (§4). |
| ≥8-way liveness, no storm/no loss | ∀ over ≥8 racers | green on D across ~4 full runs. |

---

# §6 · Residuals — refinements, none admits a wrong build (SUFFICIENT stands)

- **R-1 — MP-4 false-RED on a `from networkx import simple_cycles` correct-routing build (§3).**
  SAFE (no false-green); documented (module form required); over-strict, not a hole. Optional
  hardening in §3.
- **R-2 — R7 "one snapshot" is CLAIMED but not PINNED.** The bounded-read pin's docstring and
  `test_the_cycle_WALK_is_ONE_round_trip` assert the read is "still ONE round trip, sharing one
  snapshot," but the pin only checks round-trip constancy ACROSS DEPTH. A 2-round-trip bounded read
  (separate traversal + column query, NO shared snapshot) passes every pin — with the `Cost:`
  docstring updated to its measured count. Its TOCTOU is **verb-unreachable today** (FORK-C: no verb
  mutates `blocked_by` after birth; fresh sinks), so it is NOT a live hole — it is the SAME risk class
  as the accepted CA-11 deferral and inherits the same trigger. I built variant D as a genuine
  one-round-trip read (cost unchanged at 3), so R7 IS achievable; the contract simply does not FORCE
  it. Optional hardening: pin exactly ONE `query_raw` round trip for the guard's read. Minor.
- **R-3 — `TestTheCREATEPathsCostIsSTATED` is DERIVED and out of the author's scoped set.** A
  multi-round-trip bounded read changes `create_task`'s measured cost (3→4) and obliges a one-line
  `Cost:` docstring bump that §ESC-1-FLAGS does not name; the one-round-trip build (variant D) leaves
  the cost at 3 and the pin green with no edit. Informational — the pin self-documents the obligation
  on a full-suite run, and the author's scoped 4-RED/16-green run never touched it. Worth one line in
  §ESC-1-FLAGS: "a multi-round-trip bounded read obliges a `Cost:` docstring bump."

None of R-1/R-2/R-3 is a MISSING PIN in the sense the role defines it (a WRONG build surviving the
contract): R-1 is a false-RED (over-strict), R-2/R-3 concern a build that is SOUND and BOUNDED and
differs from the design only in round-trip count, whose sole divergence is verb-unreachable today.

---

# §7 · Instruments (deliverables — pasted so every claim is re-runnable)

## `/tmp/adv2_patch.py` — the build generator (R / S / D / Dfrom / Dhandroll)
Reads `/tmp/tasks_pristine.py` (HEAD `e22c43a`'s `tasks.py`), applies ONE variant, asserts each anchor
lands exactly once (#194), writes `/tmp/adv_cyc_d/loremaster/loremaster/tasks.py`.
- **D** (correct): `import networkx`; `_record_legacy_cycles` → `networkx.simple_cycles` (its own
  drop-loop deleted); guard reads `_bounded_dependency_graph(seeds)` (ONE query: `SELECT record::id(id)
  AS id, blocked_by FROM task WHERE id IN array::distinct(array::flatten(array::concat([$starts],
  (SELECT VALUE @.{1..32+collect}(<-blocks<-task) FROM $starts))))`); guard drop-loop +
  `_drop_one_cycle_edge` UNCHANGED.
- **S** = D but guard is a SINGLE `find_blocked_by_cycle` witness + `minted.intersection` (no drop-loop).
- **R** = D but guard routes through a NEW `_cycle_through(graph, minted)` (from-minted DFS), not
  `find_blocked_by_cycle`.
- **Dfrom** = D but `import networkx` (decorative) + `from networkx import simple_cycles`; the CALL is
  the local `simple_cycles(graph)`.
- **Dhandroll** = D's bounded read + `import networkx`, but `_record_legacy_cycles` KEEPS the
  hand-rolled `find_blocked_by_cycle`+`_drop_one_cycle_edge` drop-loop.

```python
# key bodies (full file retained at /tmp/adv2_patch.py):
NETWORKX_ENUM = (build a networkx.DiGraph from columns; for cycle in networkx.simple_cycles(graph):
                 logger.warning(_BACKFILL_CYCLE_EVENT, extra={... "cycle": " -> ".join(cycle),
                 "members": sorted(set(cycle))}))
BOUNDED_READ_BODY = (starts=[RecordID(TASK_TABLE, s) for s in sorted(seeds)];
                     rows = _as_rows(_query("SELECT record::id(id) AS id, blocked_by FROM task WHERE "
                       "id IN array::distinct(array::flatten(array::concat([$starts], (SELECT VALUE "
                       "@.{1..32+collect}(<-blocks<-task) FROM $starts)))) TIMEOUT 5s", {"starts":starts}));
                     return {id: [str(b) for b in blocked_by]})
SINGLE_WITNESS = (minted=set(pending); cycle=find_blocked_by_cycle(graph);
                  if cycle is None: return; if minted.intersection(cycle): raise_cycle_refusal(...); return)
FROM_MINTED = (minted=set(pending); if _cycle_through(graph, minted): raise_cycle_refusal(...); return)
_cycle_through = (for source in sources: DFS over graph; return True iff source reaches itself)
```

## `scripts/cycle_coexisting_legacy_soundness_probe.py` (the DURABLE MP-1 fixture — already committed)
Run against the REAL HEAD tree (spike :18000): `REFUSED (correct) … rows before=4 after=4 … VERDICT:
guard REFUSED the cyclic create — SOUND (HEAD / variant D). [exit 0]`. It ACCEPTS (exit 2) only on
variant S. This is the store-level control for MP-1.

## `/tmp/forkc_probe.py` (FORK-C tripwire liveness) — §4 output. Full source retained at the path.
## `/tmp/probe2.py` (one-query closure read validation — real seed → full closure; ghost seed → 0 rows, no error). Full source retained.
## `/tmp/substr_check.py` (import-pin substring truth table — §3). Full source retained.

*Note (brief-base §1 perversity clause): `/tmp/adv2_patch.py`, `/tmp/forkc_probe.py`, `/tmp/probe2.py`,
`/tmp/substr_check.py` live in `/tmp` (unrecoverable by construction). Their load-bearing shapes are
reproduced above and in §1–§4; if the lead wants them durable they belong in `scripts/` — say the word
and I will hand back their full text for commit. The MP-1 fixture is ALREADY durable in `scripts/`.*

---

# VERDICT: **CONTRACT SUFFICIENT**

The satisfiability receipt is POSITIVE on both legs (variant D 213/0 pre- and post-ruff; sibling suite
240/0). The prior trilemma is RESOLVED, not regressed: the unsound single-witness build (S) dies on
EXACTLY MP-1, the from-minted second-detector build (R) dies on EXACTLY R6, and the drop-loop build
(D) is 0-failed — each horn caught by its intended pin, MP-1 being the pin the whole revision turns on
and doing its job. MP-4 is safe (no false-green; it catches the hand-roll) with a documented false-RED
on the from-import form (R-1). The FORK-C deferral tripwire is a live wire. I could not construct a
WRONG build — unsound, hand-rolled, unbounded, or no-op — that survives the full contract. The three
residuals are refinements (an over-strict pin and a verb-unreachable-today unpinned R7 claim), none of
which admits a wrong build passing.

*Written 2026-08-04 by `adversary-cycle-04b3-2` (Opus 4.8, session pkt04b3) against
`feat/surreal-unification` @ `e22c43a` (surface byte-identical at HEAD `4d81f76`; the 2 intervening
commits are #327 comms-cap, disjoint from the CYCLE surface). Every build/probe graded the scratch
tree (`loremaster.__file__ = /tmp/adv_cyc_d/loremaster/loremaster/__init__.py`). Reference builds +
store probes ran on spike :18000, never :18500.*
