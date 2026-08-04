# REPORT-adversary-cycle-04b3-1 — adversarial grade of the 04b-3 CYCLE contract

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first)
- **lore tools:** reachable and used (`lore_index` fresh — 3261 files, watching `/workspace`
  @ `1164133`; `lore_get_symbol`/`lore_read`/`lore_findings`/`lore_comms` all returned). No
  fallback to grep for a structure question except deletion-exhaustiveness of
  `_drop_one_cycle_edge`'s two callers (grep's honest case, corroborated by `lore_get_symbol`).
- **spike-surreal :18000:** reachable — every reference/wrong build + both store probes ran
  against it (`ws://127.0.0.1:18000`; never :18500).
- **`./scripts/scratch_copy.sh`:** ran clean; provenance ASSERTED.
  **`loremaster.__file__ = /tmp/adv_cycle_scratch_1/loremaster/loremaster/__init__.py`**
  (#140 receipt — every build below graded the SCRATCH tree, not the original).
- No unmeetable demand.

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 headline — a wrong build survives, AND no correct build passes.** The ONLY build that
  goes 0-failed (variant **S**, single `find_blocked_by_cycle` + `minted.intersection`) is
  **UNSOUND**: `create_many` ACCEPTS a create that forms a real persisted-id cycle
  `N→seed→X→N` when a legacy cycle coexists in the bounded closure (store-level probe, exit 2).
  The RULED design (variant **R**, from-minted reachability) is SOUND but **fails an existing
  HEAD-green pin the builder may not edit** — `test_MUTATION_neutralising_the_SHARED_detector_lets_BOTH_shapes_through`.
- **SATISFIABILITY RECEIPT: NEGATIVE.** No *correct* build achieves 0-failed. Variant S is
  0-failed but unsound; variant R is correct but 1-failed. (Receipts in §1.)
- **The TRILEMMA (the core defect), all three horns proven by scratch build + run:**
  1. **Ruled from-minted (R):** 22 passed / **1 FAILED** = the R6 shared-detector MUTATION pin.
  2. **Single-call (S):** 23/23 PASS but **unsound** (accepts a persisted cycle — store probe).
  3. **Drop-loop kept (D):** sound + passes MUTATION, but `_drop_one_cycle_edge` present ⇒
     helper-absence pin RED; **rename it → the helper-absence pin PASSES with the hand-rolled
     twin fully intact** (name-keyed instrument, the six-defeats class).
- **MISSING PINS (each = a test that should exist + the defect it catches):** §3.
  - **MP-1 (blocker):** nothing pins that `_refuse_a_cycle` stays SOUND when a **minted cycle
    coexists with a legacy cycle in the bounded closure** — the persisted-cycle pin tests a
    cycle in ISOLATION only (QUANTIFIER LAW). Variant S survives the whole contract.
  - **MP-2 (blocker/escalation):** the contract drives FORK-B (a SECOND ledger detector)
    while leaving R6's MUTATION pin green — **unsatisfiable by a correct build**; needs a
    Fable ruling (R6-routing vs from-minted) before a builder starts.
  - **MP-3:** helper-absence is keyed on the literal name `_drop_one_cycle_edge`; a
    behavioural/mutation pin is owed (the hand-rolled drop mechanism, not the name).
  - **MP-4 (minor):** the #273 swap is proven only by an import-STRING pin + count-equality
    over 3 fixed topologies — neither proves `_record_legacy_cycles` ROUTES through
    `networkx.simple_cycles` (routing-is-not-sharing); a neutralise-networkx mutation pin is owed.
- **FORK C deferral is HONEST** (not a finding): the CA-11 tripwire is a live wire (§4).
- **RED honesty (P7):** the claimed 4-failed baseline reproduced exactly, for the right
  reasons; `TestTheCyclePolicyHasONEImplementation` is GREEN at HEAD (§1).
- **Graded:** `1164133` · HEAD-at-report: `1164133` · **SAME**.
- Receipt pointers: satisfiability + trilemma §1 · unsoundness store-probe §2 (verbatim
  `/tmp/unsoundness_probe.py`, pasted §6) · missing pins §3 · FORK-C §4 · quantifier table §5 ·
  finding **#326**.

---

# §1 · SATISFIABILITY + the trilemma (the P1 wrong-build results)

**Method.** `scratch_copy.sh` → `/tmp/adv_cycle_scratch_1` (provenance asserted, path above).
A patch generator (`/tmp/patch_tasks.py`, pasted §6) builds each production variant from the
pristine `tasks.py.orig`, asserting every anchor lands exactly once (#194). Scoped run set =
the contract author's finalized set **plus** `TestTheCyclePolicyHasONEImplementation` (the pin
the author's own run omitted, and the one that decides this grade):

```
test_cycle_write_path_04b3.py
test_blocks_edge.py::TestCreateRefusesToFormACycle
test_blocks_edge.py::TestTheEnumerationEQUALSNetworkxAfterTheSwap
test_blocks_edge.py::TestEVERYLegacyCycleIsRECORDEDNotJustTheFIRST
test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation
```

### RED honesty (HEAD, unmutated scratch) — reproduced
`4 failed, 19 passed` — the same 4 RED pins the author claimed (networkx-import,
helper-GONE, bounded-closure, count-equality[complete-triangle]), each RED for the right
reason. The 15→19 delta is `TestTheCyclePolicyHasONEImplementation` (4 tests) GREEN at HEAD.

### Variant R — the RULED FORK-B design (bounded read + **from-minted reachability**, helper deleted, networkx swap)
```
1 failed, 22 passed
FAILED test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation::test_MUTATION_neutralising_the_SHARED_detector_lets_BOTH_shapes_through
```
The failure trace: with `loremaster.tasks.find_blocked_by_cycle` monkeypatched to `None`, the
LEDGER still raises `TaskCycleError` for a self-loop — because R's `_refuse_a_cycle` calls its
OWN `_cycle_through`, not the shared detector. **A correct, sound build reddens a HEAD-green
pin that is NOT in the builder's writable set.** Every other pin (bounded-read, persisted-cycle,
batch, self, networkx, helper-absence) is GREEN.

### Variant S — single `find_blocked_by_cycle` + `minted.intersection(cycle)` (routes through the shared detector)
```
23 passed
```
0-failed — the contract IS satisfiable, but ONLY by this build, which is **unsound** (§2).

### Variant D — keep the drop-loop, rename the helper
`test_the_hand_rolled_cycle_helper_drop_one_cycle_edge_is_GONE` → **PASSED** with
`_step_over_cycle_edge` (byte-identical drop-an-edge body) present. The pin checks
`not hasattr(tasks_module, "_drop_one_cycle_edge")` — a literal-name gate.

**The trilemma, stated once:** the R6 MUTATION pin *requires* the ledger's persisted-id cycle
detection to BE `find_blocked_by_cycle`; a sound loop-free from-minted check *cannot be
expressed as* a `find_blocked_by_cycle` call (I tried — any single-call reduction is either
unsound (S) or a false-positive restriction; any sound loop is edge-removal ≈ the helper). So
the three horns are exhaustive and none is a clean correct build.

### The lint "harder leg"
`ruff check loremaster/loremaster/tasks.py` on the swapped module: **All checks passed.** No
test references the now-orphaned `_read_dependency_graph`, so its deletion adds no
satisfiability trap (one dangling `:meth:` docstring cross-ref remains — a P8d prose residue,
not a gate). networkx 3.6.1 present in the venv. The `dev→runtime` dep move + mypy-override
re-scope (#272/§273-FLAGS) are `pyproject.toml` changes outside the test contract.

---

# §2 · The variant-S unsoundness — CONSTRUCTED, with a control

**Pure-algorithm proof** (deterministic): on the graph `_refuse_a_cycle` builds when a new
task `N` depends on a blocker whose bounded closure contains BOTH the minted cycle
`N→seed→X→N` (X's column names N — the column-only closing link) AND a legacy 2-cycle `P↔Q`:
`find_blocked_by_cycle` returns `['aP','aQ','aP']` (the legacy cycle), so `minted.intersection`
is empty ⇒ **S accepts**; from-minted reachability (**R**) reaches `zN` from itself ⇒ refuses.

**Store-level proof through the REAL write path** (`/tmp/unsoundness_probe.py`, verbatim §6):
constructs that world on spike :18000 (raw rows + `blocks` edges so the bounded EDGE-walk from
`seed` reaches `{X,P,Q}`; `X.blocked_by=[P, new_id]` is the column-only closing link) and calls
`ledger.create_many([blocked_by=[seed]], ids=[new_id])`:

```
CONTROL  variant R (from-minted, sound):
  REFUSED (correct): blocked_by cycle among task ids: zzzn… -> zseed… -> zzzx… -> zzzn…
  rows before=4 after=4  new task landed? False   [exit 0]

variant S (single-call — the ONLY contract-passing build):
  rows before=4 after=5  new task landed? True  new_id in store? True
  VERDICT: guard ACCEPTED a create that forms a persisted-id cycle (N -> seed -> X -> N).
  *** UNSOUND build the contract WAVES THROUGH. ***   [exit 2]
```

The landed task is on a `blocked_by` cycle ⇒ its claim CAS can never succeed ⇒ **unclaimable
forever** — the exact "silent black hole" `TestCreateRefusesToFormACycle` exists to prevent.
This scenario is **reachable**: FORK B itself states "a bounded read still contains legacy
cycles if the new task depends on a legacy-cyclic ancestor," and legacy cycles persist in
production (backfilled by `ensure_ready`, never removed).

---

# §3 · MISSING PINS (INSUFFICIENT requires these)

**MP-1 — a minted cycle coexisting with a legacy cycle in the bounded closure (BLOCKER).**
*The test that should exist:* a `TestCreateRefusesToFormACycle` leg that seeds a legacy 2-cycle
among the pending blocker's persisted ancestors AND a column-only closing link back to the
minted id, then asserts the create is REFUSED and writes NO row. *The defect it catches:* the
single-call build (variant S) — the only build that passes the current contract — accepts it
(§2). The existing `test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED`
tests a cycle in ISOLATION, so it is a ∀-over-inputs claim evaluated on exactly the one input
where every build agrees (QUANTIFIER LAW). *Construction is proven above — the fixture is
`/tmp/unsoundness_probe.py`'s world.*

**MP-2 — the R6-vs-FORK-B conflict is a DESIGN fork, and it must be ruled before a builder
starts (BLOCKER / ESCALATION).** The contract drives `_refuse_a_cycle` to a from-minted
reachability check (a SECOND cycle-detector in the ledger) while leaving R6's MUTATION pin
green (that pin exists to enforce ONE ledger-owned detector = `find_blocked_by_cycle`). These
cannot both hold. *The decision owed to Fable:* either (a) from-minted reachability is
sanctioned and `test_MUTATION_neutralising_the_SHARED_detector_lets_BOTH_shapes_through`'s
LEDGER-leg is a CORPSE certifying the retired single-detector world and must be revised (P6),
**with MP-1 added**; or (b) R6 stands and the guard must route through `find_blocked_by_cycle`,
in which case the FORK-B "NOT find_blocked_by_cycle" ruling is wrong AND MP-1 is mandatory to
kill the resulting unsound single-call. There is no third option that is sound, honest, and
0-failed.

**MP-3 — helper-absence is name-keyed (defeatable by rename).** *The test that should exist:* a
behavioural/mutation pin that the hand-rolled drop-an-edge MECHANISM is gone — e.g. assert the
guard refuses a legacy-cycle-adjacent create WITHOUT stepping-over (or that no module-level
function in `loremaster.tasks` has `_drop_one_cycle_edge`'s body signature). *The defect it
catches:* variant D keeps the twin as `_step_over_cycle_edge` and the pin PASSES (§1).

**MP-4 — the #273 swap is not proven to ROUTE through the library (minor, routing-is-not-
sharing).** *The test that should exist:* a mutation pin — neutralise `networkx.simple_cycles`
and the recorded legacy-cycle set must CHANGE — mirroring `TestTheCyclePolicyHasONEImplementation`'s
own approach for the detector. *The defect it catches:* a build that `import networkx`
(satisfies the string pin) but keeps a hand-rolled enumeration matching the library on the 3
fixed topologies. Lower severity: the count pin's complete-triangle leg already forces a real
change, and post-swap the enumeration IS the library.

---

# §4 · FORK C — the deferral is HONEST (verified, not a finding)
`/tmp/forkc_tripwire_probe.py` constructs the future-verb world (a blocker that GAINS a
dependency after birth, via a raw `blocked_by` mutate + mirrored edge) and confirms
`transitive_blockers(blocker)` grows from `[]` → 2 ids. So the CA-11 tripwire
`test_PIN_THE_MISS_a_tasks_blocked_by_is_FIXED_at_birth`'s assertion `after == before == set()`
holds today (control empty) and BREAKS the moment a `blocked_by`-mutating verb lands. The
deferral rests on a live wire — legitimate measure-then-tune, not a hope with a filename.

---

# §5 · The QUANTIFIER TABLE (P1b)

| invariant (pin) | ∀-over-inputs or guarded | receipt |
|---|---|---|
| persisted-id cycle is refused (`…PERSISTED_tasks_is_REFUSED`) | **GUARDED — by "a cycle in isolation"** | wrong build (variant S) walks the same bad outcome (a persisted cycle) through the legacy-cycle-coexists door → ACCEPTED (§2). **MP-1.** |
| batch-key / self cycle refused (`…each_others_IDS`, `…SELF_blocking…`) | ∀ over pending-overlay cycles | GREEN on R and S; the self/batch cycles exist ONLY in the pending overlay, so a build dropping `graph[task_id]=set(blockers)` fails these (by construction). Adequately pinned. |
| write-path read is BOUNDED (`…BOUNDED_by_the_ancestor_CLOSURE`) | ∀ over dependency-bearing population (5 vs 60) | RED on whole-population (HEAD), GREEN on bounded (R/S). Discriminates. Does NOT alone catch an edge-only reader (that is the persisted-cycle pin's job — see next row). |
| the closing link is read from the COLUMN (not edges) | GUARDED — by the persisted-cycle pin | the test writes the closing link as a raw column-only `UPDATE` with NO `RELATE` (`test_blocks_edge.py` L1954-1962) and `ENFORCED` forbids the edge, so an edge-only bounded read structurally cannot see it → the persisted-cycle pin catches an edge-only build. Verified by the test's construction. |
| recorded ENUMERATION == `networkx.simple_cycles` | ∀ over **3 fixed topologies** | RED on hand-rolled (complete-triangle 4≠5), GREEN post-swap. Does not prove ROUTING (MP-4). |
| ONE ledger-owned detector, `find_blocked_by_cycle` (R6 MUTATION pins) | ∀ (neutralise → both shapes accepted) | GREEN at HEAD; **variant R reddens it** — this is the pin FORK-B's design contradicts (MP-2). |
| a task's ancestor set is FIXED at birth (FORK-C tripwire) | ∀ over creates | live wire (§4). |
| ≥8-way liveness, no storm / no loss | ∀ over ≥8 racers | GREEN (FORK-C evidence; deferral-correct). |

---

# §6 · Instruments (deliverables — pasted so the claims are re-runnable)

## `/tmp/patch_tasks.py` (build generator — R / S / D-rename)
```python
# reads /tmp/tasks.py.orig, applies one variant, asserts every anchor lands exactly once (#194).
# R  = bounded read + from-minted reachability (_cycle_through), helper deleted, networkx swap.
# S  = bounded read + single find_blocked_by_cycle + minted.intersection, helper deleted, swap.
# D-rename = HEAD, but _drop_one_cycle_edge -> _step_over_cycle_edge (function + 2 call sites).
# _bounded_dependency_graph (shared by R and S): seed from pending's persisted blockers, walk
# the ancestor closure via @.{1..N+collect}(<-blocks<-task).id, read those bounded nodes'
# blocked_by COLUMNS (WHERE id IN $bounded_nodes). Full source retained at the path.
```

## `/tmp/unsoundness_probe.py` (variant-S unsoundness, with the variant-R control)
Constructs on spike :18000: rows `seed<-X<-P<->Q` with `blocks` edges, `X.blocked_by=[P,new_id]`
(column-only closing link), then `ledger.create_many([blocked_by=[seed]], ids=[new_id])`.
R → REFUSED (exit 0); S → ACCEPTED, task lands (exit 2). Full source retained at the path;
the load-bearing shape is in §2.

## `/tmp/forkc_tripwire_probe.py` (FORK-C deferral liveness)
Creates blocker + dependent via the ledger (control: `transitive_blockers(blocker)==[]`), then
raw-mutates `blocker.blocked_by=[dep]` + mirrors the edge (the synthetic future verb) and shows
`transitive_blockers(blocker)` grows → the tripwire assertion would redden. Exit 0.

*Note (brief-base §1 perversity clause): these three instruments live in `/tmp` (unrecoverable
by construction). If the lead wants them durable, they belong in `scripts/` beside
`esc1_write_path_cycle_closure.py` — say the word and I will hand back their full text for
commit; the load-bearing shapes are reproduced above and in §2/§4.*

---

# VERDICT: **CONTRACT INSUFFICIENT**

The satisfiability receipt is NEGATIVE: no *correct* build achieves 0-failed. The contract
drives FORK-B's from-minted reformulation, which reddens the R6 shared-detector MUTATION pin
(a HEAD-green pin outside the builder's writable set); the only 0-failed build routes through
`find_blocked_by_cycle` as a single call and is UNSOUND (accepts a real persisted cycle when a
legacy cycle coexists — proven through the real write path); and the sound-and-passing horn
keeps the hand-rolled drop mechanism the packet exists to delete, behind a name-keyed pin.
Before a builder starts, the contract author owes: (MP-2) a Fable ruling reconciling R6 with
FORK-B; (MP-1) a discrimination pin for the minted-cycle-plus-legacy-cycle closure; (MP-3) a
mechanism (not name) pin for the deleted helper; (MP-4) a routing mutation pin for the networkx
swap. FORK C's deferral is honest and needs nothing.

*Written 2026-08-03 by `adversary-cycle-04b3-1` (Opus 4.8, session pkt04b3) against
`feat/surreal-unification` @ `1164133`. Every build/probe graded the scratch tree
(`loremaster.__file__` asserted in-scratch). Reference builds + store probes ran on spike
:18000. Finding #326 filed.*
