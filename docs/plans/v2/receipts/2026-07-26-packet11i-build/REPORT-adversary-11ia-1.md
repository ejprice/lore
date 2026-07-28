# REPORT-adversary-11ia-1 — the CONTRACT ADVERSARY's grading of packet 11-i-a

brief-base v7 read

**Provenance receipt (#140).** Reference build + every wrong build ran in an isolated scratch
copy minted by `scripts/scratch_copy.sh`; `loremaster.__file__` =
`/home/ejprice/scratch-adv11ia/refbuild/loremaster/loremaster/__init__.py` (measured
2026-07-26, `uv run --no-sync python -c`). The copy's `.git` — a 71-byte WORKTREE POINTER,
confirming finding **#185** — was renamed out of the way before any work, so no git command
could reach the real worktree's metadata. The real worktree at
`/home/ejprice/PycharmProjects/lore-pkt11ia` was never written to: `git diff --stat d6c0dd4
HEAD` over the eight graded paths is EMPTY, i.e. the artifact I graded is byte-identical to
the frozen contract commit. I ran **no git write command of any kind**.

---

## SUMMARY BLOCK

**VERDICT: CONTRACT INSUFFICIENT.**

**P1 headline — 9 of 14 valid wrong builds SURVIVED the contract, 143 passed / 0 failed each.**
The five that were caught include a positive control, so the instrument demonstrably works.

**Satisfiability receipt (the contract's own stated gap, §3 — now produced).** Against my
reference build: contract **143 passed / 0 failed**; with the pre-existing suites the new seams
touch (`test_retry_seam.py` + `test_surreal_store.py`) **882 passed / 0 failed**;
`scripts/typecheck.sh` → `Success: no issues found in 160 source files`; `ruff` → `All checks
passed!`. **Two conditions had to be met that the contract does not disclose** — see B1/B2.

**THE 60 — verified, and the author's claim about them is FALSE.** 60 reproduced exactly
(`60 failed, 499 passed`); the 56/4 split is CORRECT. But *"Every one goes green when the builder
routes `_ensure_connection` through `bootstrap_session` and `_query` through `run_query`"* is
**wrong: 3 stay RED** on a perfectly-built seam, because `test_retry_seam.py` carries two
HAND-WRITTEN dicts (`_SEAM_REJECTION_EVENTS`, `_SEAM_REJECTION_NOUNS`) and one pin does a raw
`KeyError`-ing lookup. **No production code can fix them** — the builder needs explicit
authorisation to add 4 dict entries. With them: **561 passed / 0 failed**.

**MISSING PINS, ranked** (test that should exist → defect it catches):
| # | the test that should exist | the wrong build it admits today |
|---|---|---|
| M1 | a fenced commit whose fence moves BETWEEN the guard read and the write is refused | **W2**: the fence is a TOCTOU pre-check; R10.2's in-transaction guard is absent |
| M2 | two corpora with identical content hashes but DIFFERENT `point_id`s digest differently | **W5**: relocation-blind digest — exact-skip skips a changed corpus |
| M3 | the head `revision` across a REFUSED measurement (adopt→refuse→adopt = +1, not +2) | **W25**: the head advances on non-adopted rows; the "discriminating arithmetic" is fooled |
| M4 | a domain rejection that happens INSIDE the fenced transaction keeps its own type | **W31**: every rollback under a fence is reported as a benign lost race |
| M5 | E2's third fate: the confirming re-read FAILS ⇒ re-raise untouched | unpinned, and the existing "no lease row" pin **contradicts the ruling** (B2) |
| M6 | `measurement_history(limit=k)` with k < row count; and newest-first order | **W11**: `limit` ignored, order inverted |
| M7 | the lock adapter's `update` fails on a STALE observed revision | **W18**: the adapter's CAS token is discarded — two leaders in the get/update window |
| M8 | `SurrealLeaderLock.release_if_held()` (the ADAPTER verb) actually releases | **W29**: decision 23 is a no-op; every rolling update waits a full `lease_duration` |
| M9 | `adopted_n` is persisted, and records the ACTUAL subsample (F4.3) | **W30**: silently dropped — and the E4 ruling claims it is "already pinned" |
| M10 | `create_if_absent` RAISES on a non-duplicate rejection | **W26**: every failure becomes a lost race; the run silently never leads |
| M11 | the measurement CREATE and the head advance are ONE transaction | **W23b**: two transactions — orphan measurement on a crash |
| M12 | the two lease counters are computed by the ENGINE, in the same statement | **W7**: both client-computed from a separate read (**false gate**, see F1) |
| M13 | the `insufficient_corpus` predicate consuming 30/15/30 | nothing reads the three constants — E4 also claims this is "already pinned" |
| M14 | a dirty-store migration leg for the `lease` and `floor_head` slices | only `floor_measurement.state` has one (the clause pins are the ∀ backstop — W32 caught) |

**BLOCKERS (fix before a builder starts):** M1 · M2 · M3 · M4 · B1 · B2 · B3.
**P-PKG diff:** one missing survey row — the two IDENTITY ENCODINGS (`head_identity`
pre-image, `corpus_content_digest`) are hand-rolled with **no package row at all**, while
`orjson 3.11.9` is INSTALLED and `OPT_SORT_KEYS` supplies all three properties the bespoke
encoding buys with a refusal guard and a 12-mapping matrix (probed, §P-PKG).
**Corpse sweep:** 1 production hit — **the contract author's own stub comment**, which makes
its own sweep pin RED at `d6c0dd4` (B3) — plus **4 LIVE design-doc lines the sweep cannot
reach** (its scope stops at `.py`).
**Fixture discrimination:** 4 perturbations built, each proven on BOTH legs (RED on the named
wrong build, GREEN on the reference build). **Residual: the 6th vacuous pin the author missed**
is `test_the_states_are_a_tuple_not_a_mutable_set` (green over `()`), covered by a sibling.

---

## 0. WHAT I GRADED, AND HOW

- Contract frozen at `d6c0dd4`; rulings at `81db016`. Verified unchanged at grading time.
- Two isolated scratch trees: `refbuild` (my reference implementation) and `stub` (pristine).
  Both minted with `scripts/scratch_copy.sh`, both provenance-asserted, both git-neutered.
- Restore between wrong builds is `cp -a` from a content snapshot, verified with `md5sum -c`
  after the last restore (all 6 files `OK`). An md5 list is a detector; the snapshot is the
  backup.
- Test store: `spike-surreal ws://127.0.0.1:18000` (health 200). Production `:18500` never
  touched.

**Disclosure (P-PKG discipline).** My role spec says to build my own package table BEFORE
opening the author's. My spawn brief ordered the author's report as read #1, so I could not.
I compensated by re-deriving every row from the INSTALLED source rather than from the
author's prose, and by enumerating mechanisms the author's line does not mention — which is
where the one finding came from.

---

## 1. P7 — RED HONESTY (reproduced)

```
$ cd .../refbuild (stub state) && uv run --no-sync pytest -q -n auto -p no:randomly \
    loremaster/tests/test_floor_calibration_{domain,schema,store}.py loremaster/tests/test_store_lease.py
74 failed, 28 passed, 41 errors in 10.13s
```
Exactly the author's numbers. Nothing fails at COLLECTION; the 41 errors are the stubbed
`ensure_ready` at fixture time. The RED is honest.

**The 28 GREEN pins, each with an individual verdict** (the brief asked; "the rest look fine"
is banned). Legend: **L** = pins the installed LIBRARY (legitimate) · **C** = a contract
CONTROL (legitimate) · **S** = the stub genuinely satisfies it (legitimate) · **V** = VACUOUS.

1. `domain::test_the_states_are_a_tuple_not_a_mutable_set` — **V**. `isinstance((), tuple)`
   is true; it is green over an EMPTY closed set. This is the **sixth** pin the author's
   "five explicit non-emptiness clauses" missed. It admits no wrong build (the exact-set pin
   covers), so it is a control gap, not a defect.
2. `schema::test_the_only_test_mentions_are_the_two_pins_that_assert_its_ABSENCE` — **C**.
3. `schema::test_neither_module_calls_query_on_a_connection_directly` — **S** (and it is real
   later: it CAUGHT W28).
4. `schema::test_the_ddl_scan_can_actually_see_a_call` — **C**.
5. `store::test_the_ledger_is_discovered_by_the_shared_seam_enumerator` — **S**.
6. `store::test_the_ledger_constructs_from_the_shared_ctor_values` — **S**.
7. `store::test_the_engine_conflict_marker_appears_nowhere` — **S** (mutation-proven by the author).
8. `store::test_no_private_sleep_ladder` — **S**.
9. `store::test_the_sleep_scan_can_actually_see_a_sleep` — **C**.
10. `store::test_the_two_refusals_are_DISTINCT_types` — **S** (the stub declares both classes).
11–15. `lease::TestTheLockInterfaceIsDerived::*` (six-member derivation, non-vacuity control,
    instance `hasattr`, the `election_record` keyword, the record's four fields) — **L** ×4 + **C** ×1.
16. `lease::test_returning_None_on_absent_BREAKS_the_first_acquisition` — **L/C** (broken control #1).
17. `lease::test_a_bare_ApiException_on_absent_ALSO_breaks_it` — **L/C** (broken control #2).
18. `lease::test_the_LockAbsent_shape_lets_the_lock_be_created` — **L/C** (positive control).
19. `lease::test_LockAbsent_carries_a_json_body_naming_the_404_code` — **S**.
20. `lease::test_the_three_tunables_are_client_gos_documented_defaults` — **S** (real constants;
    mutation-proven by the author).
21. `lease::test_the_tunables_pass_the_librarys_OWN_validation` — **L**.
22–24. `lease::test_the_validator_really_rejects_an_illegal_triple[...]` ×3 — **C**.
25. `lease::test_the_lease_store_is_discovered_by_the_shared_seam_enumerator` — **S**.
26. `lease::test_the_lease_store_constructs_from_the_shared_ctor_values` — **S**.
27. `lease::test_the_conflict_marker_text_appears_nowhere` — **S**.
28. `lease::test_no_sleep_call_appears_in_the_module` — **S**.

**Verdict: 27 legitimate, 1 vacuous-but-harmless.** No pin is green because a closed tuple
ships empty except #1, and #1 is backstopped.

---

## 2. THE SATISFIABILITY RECEIPT (the contract's own §3 gap, closed)

I built the reference implementation the contract author declined to build: the two closed
domains + two DDL generators in `surreal_schema.py`, the two identity functions in
`floor_calibration/domain.py`, the ledger in `floor_calibration/store.py`, the store seam +
lock adapter + config in `store/lease.py`, and `enumerate_calibration_pool` +
`CALIBRATION_POOL_COLUMNS` in `store/surreal.py`.

```
143 passed in 29.29s          # the four contract files
882 passed, 1 warning         # + test_retry_seam.py + test_surreal_store.py
Success: no issues found in 160 source files   (scripts/typecheck.sh, all 3 members)
All checks passed!                             (ruff check loremaster/ scripts/)
```

**The contract IS satisfiable — but only after three things the contract does not disclose.
Each is a builder trap.**

### B1 — BLOCKER. Three `test_retry_seam.py` node ids CANNOT be made green by production code.

Reproduced on a seam built exactly as the contract prescribes:

```
FAILED ...::TestTheExhaustionRecordIsATTRIBUTABLE::test_the_exhaustion_record_names_the_seam_the_server_and_the_engine_text[SurrealLeaseStore]
FAILED ...::TestTheExhaustionRecordIsATTRIBUTABLE::test_the_exhaustion_record_names_the_seam_the_server_and_the_engine_text[FloorCalibrationStore]
FAILED ...::TestTheSeamsRejectionLogSurvivesTheCollapse::test_every_seam_still_logs_its_OWN_canonical_rejection_event
3 failed, 558 passed
```
The first two die on `KeyError: 'FloorCalibrationStore'` — a raw lookup into the hand-written
`_SEAM_REJECTION_EVENTS` dict. The third compares `observed_nouns == _SEAM_REJECTION_NOUNS` and
`observed.keys() == _SEAM_REJECTION_EVENTS.keys()` as EXACT SETS driven from the DISCOVERED
seams. Adding the four entries turns the whole file green:
```
561 passed, 1 warning in 9.03s
```
**Why this is a blocker and not a chore:** the contract report tells the builder all 60 go green
by routing correctly. When 3 do not, the two obvious moves are both bad — invent a bespoke seam
shape so the new classes fall OUT of the enumeration (that is finding **#120**, verbatim), or
call the reds "pre-existing" and ship (a builder verdict this repo forbids). The lead must
authorise the 4-line `test_retry_seam.py` edit **in the build brief**, and name the values.

### B2 — BLOCKER. The E2 ruling's RIDER and the contract's own fence pin CONTRADICT each other.

`test_a_commit_with_NO_lease_row_at_all_is_refused_when_fenced` uses the `floor_store` fixture
ALONE. Nothing in that fixture creates the `lease` table. On SurrealDB 3.2.1 a read from an
undeclared table does not return `[]` — it RAISES:
```
surrealdb.errors.NotFoundError: The table 'lease' does not exist
```
So the E2-ruled confirming re-read **cannot complete**, and E2's rider says verbatim: *"If the
confirming read itself fails, the code must re-raise the original error untouched — it must
never report `FenceLostError` on the strength of a read it could not complete."* The pin demands
`FenceLostError`. Measured, on the rider implemented verbatim plus the natural `ensure_ready`
(**W27**):
```
FAILED ...::TestTheFencedCommit::test_a_commit_with_NO_lease_row_at_all_is_refused_when_fenced
1 failed, 4 passed
```
My reference build only goes green because `FloorCalibrationStore.ensure_ready()` also emits
`generate_lease_ddl()` — an undisclosed cross-slice coupling that **no pin requires**. A builder
that does the obvious thing hits a red pin whose only "obvious" fix is to violate the rider.
**Rule one of three, and pin it:** (a) the floor ledger emits the lease slice, or (b) the pin's
fixture creates the lease table, or (c) the pin is re-specified.

### B3 — the contract's own sweep pin is RED for the contract author's own comment.

`test_no_production_module_mentions_the_retired_name` fires on
`store/surreal_schema.py` (the 11-i-a stub banner):
```
AssertionError: ['.../loremaster/store/surreal_schema.py:1790:
  # distinct; ``stale_remeasuring`` is RETIRED and must appear nowhere.']
```
The pin is doing its job; its subject is the stub the contract shipped. It means one of the 74
RED pins is not behavioural at all, and a builder must delete a comment the contract author
wrote. Cheap, but it belongs in the brief.

---

## 3. P1 — THE WRONG BUILDS

Every row is a real build, run against the REAL contract, in the scratch tree, restored to
byte-exactness afterwards.

| # | wrong build | contract verdict |
|---|---|---|
| **W1** | `record_measurement` uses a PRIVATE copy of the head-identity recipe with byte-identical output | **CAUGHT** — 1 failed (`test_perturbing_head_identity_moves_the_stores_head_id`). *This is my positive control: the instrument can see a wrong build.* |
| **W2** | the fenced commit is a **TOCTOU pre-check**; the write itself is UNFENCED (R10.2's `WHERE fence_epoch = $mine` deleted) | **SURVIVES — 143 passed** ⛔ |
| **W4b** | the closed cause domain reaches the DDL only as a `COMMENT`; no store ASSERT | **CAUGHT** — 1 failed (`test_an_UNKNOWN_non_adoption_cause_is_rejected_by_the_store`) |
| **W5** | `corpus_content_digest` reads `point_id` and DISCARDS it | **SURVIVES — 143 passed** ⛔ |
| **W7** | both lease counters computed CLIENT-SIDE from a separate read, then written as literals | **SURVIVES — 143 passed** |
| **W11** | `measurement_history` ignores `limit` and returns ASCENDING | **SURVIVES — 143 passed** |
| **W18** | the lock adapter discards the revision it observed at `get` and re-reads — its CAS can never fail | **SURVIVES — 143 passed** |
| **W23b** | measurement CREATE and head advance in TWO separate transactions | **SURVIVES — 143 passed** |
| **W25** | the head's monotonic `revision` advances on EVERY measurement; only `measurement_id` is guarded by `adopt` | **SURVIVES — 143 passed** ⛔ |
| **W26** | `create_if_absent` reports EVERY rejection as a lost race | **SURVIVES — 143 passed** |
| **W27** | the natural `ensure_ready` + E2's rider verbatim (i.e. **the RULED build**) | **CAUGHT** — see B2; this one convicts the contract, not the build |
| **W28** | ROUTING IS NOT SHARING: the lease seam rides `retry_on_conflict` but matches `"Resource busy"` locally (#102's shape) | **CAUGHT ×3 in the contract** + ×2 in the inherited `TestDetectionFollowsTheOneSharedMarker[SurrealLeaseStore]` |
| **W29** | `SurrealLeaderLock.release_if_held()` returns `False` unconditionally | **SURVIVES — 143 passed** |
| **W30** | `adopted_n` is stripped from the payload before the write | **SURVIVES — 143 passed** |
| **W31** | the fence classifier reports `FenceLostError` for EVERY rollback, never re-reading state | **SURVIVES — 143 passed** ⛔ |
| **W32** | the lease slice emits `DEFINE FIELD IF NOT EXISTS` (the #107 shape) | **CAUGHT** — 2 failed (both clause pins) |

*(One discarded probe, disclosed: a first attempt at W23 split the transaction per-statement and
died on an undefined `LET` variable — it failed for the WRONG reason, so it proves nothing and
was rebuilt as W23b.)*

### The four ⛔ blockers, explained

**W2 — the fence is not a fence.** A pre-check is exactly the race a fencing token exists to
close: a lapsed holder reads the lease, sees its epoch, and then commits after another pod has
seized. The design's ruled wording (R10.2, *"guarded `WHERE fence_epoch = $mine`"*) is the
atomic version; the contract pins only the OUTCOME on fixtures where nothing moves between the
check and the write. **M1**: force a fence move BETWEEN the guard and the commit (monkeypatch a
`compare_and_set` into the store's own transaction path, or drive it from a second connection
inside a slow statement) and require `FenceLostError` + nothing landed.

**W5 — the exact-skip datum is relocation-blind.** Proven directly, with a control:
```
W5 build   before == 4e712e37cf746ce34b5b2d18   after == 4e712e37cf746ce34b5b2d18   IDENTICAL -> True
ref build  before == ea57143a39376c3bd4080c99   after == 73ddebb9d80859f7f774b8a4   IDENTICAL -> False
```
(fixture: two chunks whose `content_hash` is unchanged and whose `point_id`s both changed — a
renamed symbol or a moved file). C10's contract is *"equal ⇔ zero chunks added, removed, or
edited ⇔ skip"*; membership churn with unchanged content is invisible, and 11-ii skips a
re-measure on a corpus that moved. Every existing digest pin varies `content_hash` and never
varies `point_id` alone. **M2** is one function.

**W25 — the "discriminating arithmetic" is fooled by its own fixture.** The contention pin
calls the revision-count invariant *"arithmetic, not 'it did not crash'"*, and
`test_each_adoption_advances_the_head_revision_by_exactly_one` runs **three consecutive
adoptions** — so "+1 per adoption" and "+1 per measurement" are indistinguishable, exactly the
small-N/arithmetic-alignment class this repo has now hit five times.
`test_a_NON_adopted_measurement_does_NOT_move_the_head` checks `measurement_id` and the history
length; it does not look at `revision`. **M3**: adopt → refuse → adopt, assert `+1`.

**W31 — the pin that names the defect never reaches the code that causes it.**
`test_a_NON_fence_failure_keeps_its_OWN_type` says *"a domain rejection under an INTACT fence
must surface as itself, or every real defect on this path gets reported as a benign lost
race"* — but it passes `state="nearly_measured"`, which raises `ValueError` **before any I/O**.
The classifier is never entered. A build that translates every rollback into `FenceLostError`
passes. **M4**: force a STORE-level rejection inside a FENCED transaction (an out-of-domain
value the ledger's own validator does not police, or a monkeypatched payload) with the fence
intact, and require the original type.

---

## 4. P1b — THE QUANTIFIER TABLE

∀ = universally quantified over the unit's inputs. **G** = guarded by a named failure mode.
Every G row carries a receipt: a surviving wrong build (the door), or the door-build that died.

| # | invariant | ∀ / G | receipt |
|---|---|---|---|
| 1 | the state set is exactly the ruled eight | ∀ | exact-set literal |
| 2 | the cause enum is exactly the ruled five | ∀ | exact-set literal |
| 3 | TABLE `IF NOT EXISTS` · FIELD `OVERWRITE` · INDEX `IF NOT EXISTS` · no `ALTER` | ∀ over both slices | **W32 CAUGHT** (door: the lease slice with `IF NOT EXISTS`) |
| 4 | the state/cause ASSERTs are DERIVED from the tuples | **G** | **W4b**: a `COMMENT` satisfies both derivation pins; only the LIVE rejection pin caught it |
| 5 | the schema migrates an EXISTING store (#107) | **G** (one field, one table) | backstopped ∀ by row 3 — **W32**. The lease/`floor_head` slices have no live migration leg (**M14**) |
| 6 | `head_identity` is the frozen function of its axes | ∀ | golden vector + 12-mapping matrix + 4 refusals |
| 7 | the STORE routes through `domain.head_identity` | ∀ (cross-module mutation) | **W1 CAUGHT** |
| 8 | the corpus digest detects a corpus change | **G** (edit / add / remove / reorder / boundary-shift) | **W5 SURVIVES** — the RELOCATION door is open ⛔ |
| 9 | rows are append-only | ∀ | two writes ⇒ two ids, two history rows |
| 10 | history is scoped to its own head | ∀ | two heads |
| 11 | history honours `limit`, newest-first | **G** — `limit` is monoculture (always > row count); order unpinned | **W11 SURVIVES** |
| 12 | a NON-adopted measurement does not move the head | **G** — only `measurement_id` is checked | **W25 SURVIVES** ⛔ |
| 13 | each adoption advances the head revision by exactly one | **G** — fixture is 3 consecutive adoptions | **W25 SURVIVES** ⛔ |
| 14 | the head is STORE state, not process state | ∀ | independent connection |
| 15 | the F4/F5 domain is validated BEFORE any I/O | ∀ over the 4 illegal shapes + "lands nothing" | strong |
| 16 | a moved fence refuses and lands NOTHING | **G** — outcome only, on fixtures where nothing moves mid-commit | **W2 SURVIVES** ⛔ |
| 17 | a non-fence failure keeps its OWN type | **G** — the only case raises pre-I/O, so the classifier is never entered | **W31 SURVIVES** ⛔ |
| 18 | E2's rider: a failed confirming re-read re-raises untouched | **NOT PINNED** | **W27** — and the existing pin CONTRADICTS the ruling (B2) |
| 19 | measurement + head advance are ONE transaction | **NOT PINNED** | **W23b SURVIVES** |
| 20 | the head mint loses nothing at 8/16/32-way | ∀ (revisions must be exactly `1..N×M`) | genuinely strong — the best pin in the contract |
| 21 | distinct axis mappings do not contend | ∀-ish | 8 distinct heads, all revision 1 |
| 22 | the C8 pool is exhaustive | ∀ (`count == returned`) | strong |
| 23 | the C8 limit is STRICTLY > count | ∀ | strong |
| 24 | the C8 walk is ascending | ∀ over returned rows; does NOT distinguish store-side `ORDER BY` from a client `sorted()` | not door-built — declared, not measured |
| 25 | the projection is narrowed and declared | ∀ (exact key-set) | strong |
| 26 | truncation ≠ count-mismatch | ∀ (both fates forced) | strong |
| 27 | a stale CAS returns None and changes nothing | ∀ | strong |
| 28 | the fence is stable on renew, moves on holder change | ∀ (both directions) | strong |
| 29 | both counters are minted STORE-SIDE in ONE update | **G / FALSE GATE** | **W7 SURVIVES** — see F1 |
| 30 | store `release_if_held` guards identity AND fence | ∀ (4 legs, incl. the same-identity zombie) | strong |
| 31 | ADAPTER `release_if_held()` releases | **NOT PINNED** | **W29 SURVIVES** |
| 32 | a lost create race is a VALUE, never an exception | **G** — only the duplicate cause | **W26 SURVIVES** |
| 33 | the record the adapter returns is PURE (4 fields) | ∀ (structural + behavioural) | strong |
| 34 | the adapter's `update` CASes on its observed revision | **NOT PINNED** | **W18 SURVIVES** |
| 35 | the stop poison ends renewals | ∀-ish | observable consequence, correctly |
| 36 | the adapter exposes its fence epoch | **G** — only after `create`, never after a renew or a seize | not door-built — declared |
| 37 | no private retry / backoff / marker in the new packages | ∀ (AST + text + inherited shared-marker mutation) | **W28 CAUGHT ×5** |
| 38 | the two new seams ride the ONE driver | ∀ (56 inherited parametrised pins) | **W28 CAUGHT** |
| 39 | `adopted_n` records the ACTUAL subsample (F4.3) | **NOT PINNED** | **W30 SURVIVES** |
| 40 | the `insufficient_corpus` predicate / the 30-15-30 floors | **NOT PINNED** — the constants are pinned as VALUES and nothing reads them | grep: `MIN_*` appear only at `test_floor_calibration_domain.py:380,386` |

**Rows 8, 12, 13, 16, 17 are the blockers.** Rows 18, 19, 31, 34, 39, 40 are unpinned outright.

---

## 5. P2 — FIXTURE DISCRIMINATION (perturbations, both legs)

Four perturbed pins, each the SAME assertion as a contract pin with ONE load-bearing fixture
value changed. **Leg 1** = RED on the named wrong build. **Leg 2 (control)** = GREEN on the
correct reference build — without which a perturbation is just a botched expected value.

| perturbation | leg 1 (wrong build) | leg 2 (reference build) |
|---|---|---|
| `P2A` head revision across a REFUSED measurement (adopt → refuse → adopt) | **RED on W25** | **GREEN** |
| `P2B` `measurement_history(limit=2)` over 4 rows — a limit BELOW the row count | **RED on W11** | **GREEN** |
| `P2C` history is newest-first (`[0.42, 0.41, 0.40]`) | **RED on W11** | **GREEN** |
| `P2D` a LONE non-adopted measurement leaves the head unmeasured | (W25 passes it) | **GREEN** |

```
--- leg 1, W25 --- 1 failed, 3 passed        (P2A)
--- leg 1, W11 --- 2 failed, 2 passed        (P2B, P2C)
--- leg 2, ref --- 4 passed                  (control, both times)
```

**The three axes, named:**
- **Arithmetic alignment** — `test_each_adoption_advances_the_head_revision_by_exactly_one`
  uses three consecutive ADOPTIONS, which makes "+1 per adoption" and "+1 per measurement"
  the same number. The perturbation that blinds it is *removing* the refusal; the contract
  never adds one.
- **Parameter-value monoculture** — every one of the contract's `measurement_history` calls
  passes `limit` GREATER than the row count (`limit=10` over ≤2 rows; `limit=expected+10`).
  The code branches on `limit`; no pin uses a discriminating value.
- **Small-N / single-instance** — the dirty-store migration pin covers ONE field on ONE of the
  three tables; the C8 truncation fixture is a single `count` value (5 against 12).

**Fixtures I interrogated and judged SOUND** (each with the reason):
- `_measurement(state=...)` correctly refuses to default a branched parameter, and
  `non_adoption_cause` has no silently-correct default — the repo's `_brief(name="project")`
  lesson is applied properly.
- `test_distinct_axis_mappings_mint_distinct_ids`'s 12-mapping matrix genuinely defeats a
  `":"`-joining and a value-normalising encoding (`tier:lore`/`cosine_floor` vs
  `tier`/`lore`; the trailing-space pair), and it is computed in ONE test rather than
  parametrised — the author explicitly avoided the `-n auto` sharded-accumulator trap.
- The hot-row pins are at 8/16/32-way with overlapping lifetimes (repeated operations per
  racer), and their invariant is arithmetic (`sorted(observed) == range(1, N*M+1)`), not
  "it did not crash". This is the strongest work in the contract.
- `test_a_STALE_FENCE_cannot_release_the_lease_it_no_longer_holds` deliberately re-uses the
  SAME identity so only the fence can discriminate. Correct by construction.
- `test_the_limit_is_STRICTLY_greater_than_the_counted_total` — the strictness IS the
  instrument, correctly reasoned.

---

## 6. F1 — FALSE GATES (assertion vs. its own message)

**F1a. `test_both_counters_are_minted_STORE_SIDE_in_one_update`.** Its docstring: *"A
client-computed `revision + 1` re-introduces the lost-update the CAS exists to prevent. Proven
by CONTENTION, not by reading the SQL."* **W7 is that exact build — both counters computed
client-side from a SEPARATE read — and it passes, at 8-way here and at 8/16/32-way in
`test_no_write_is_ever_lost_under_contention`.** Two things are wrong: the pin cannot
discriminate its named target, and the causal claim is itself false — the `WHERE revision =
$observed_revision` predicate is what serialises, so a client-computed increment cannot lose an
update while the CAS is present, and the genuinely dangerous build (drop the `WHERE`) is caught
by a *different* pin (`test_a_STALE_CAS_returns_None_and_changes_nothing`). **M12**: assert the
statement count, or read the two counters back after a write issued with a deliberately WRONG
client-side value.

**F1b. `test_a_NON_fence_failure_keeps_its_OWN_type`** — covered above as W31/M4. The message
promises a check over the classifier; the assertion never reaches it.

**F1c. `test_the_generators_emit_something_for_every_planned_table`** is labelled `CONTROL`
against vacuous clause pins, but it only checks that three table NAMES appear as substrings.
A slice emitting `DEFINE TABLE`s and zero `DEFINE FIELD`s passes it, and then
`test_every_field_definition_is_OVERWRITE` is vacuously green. (The live rejection pins are the
real backstop; W4b shows they fire.) Worth a one-line strengthening: assert at least one
`DEFINE FIELD` per table.

---

## 7. P6 — CORPSE SWEEP (`stale_remeasuring`), every hit individually

Bare, anchor-free pattern over the whole worktree.

| file:line | verdict |
|---|---|
| `loremaster/loremaster/store/surreal_schema.py:1790` | **DEFECT (B3)** — the contract author's own stub comment; makes the contract's own production sweep pin RED at `d6c0dd4`. Reproduced. |
| `loremaster/tests/test_floor_calibration_domain.py:28` | OK — docstring inside an allowed file |
| `loremaster/tests/test_floor_calibration_domain.py:78` | OK — the sweep constant, deliberately spelled out |
| `loremaster/tests/test_floor_calibration_schema.py:71` | OK — the sweep constant |
| `loremaster/tests/test_floor_calibration_schema.py:218` | OK — docstring inside an allowed file |
| `docs/design/2026-07-24-floor-calibration.md:336` | **STALE PROSE, LIVE DOC** — teaches the retired name as current behaviour |
| `docs/design/2026-07-24-floor-calibration.md:418` | **STALE PROSE, LIVE DOC** — §7's state TABLE row; this is the table 11-ii will read to build its served state projection |
| `docs/design/2026-07-24-floor-calibration.md:659` | **STALE PROSE, LIVE DOC** |
| `docs/plans/v2/receipts/2026-07-24-packet11i/CONTRACT-FREEZE-DECISIONS.md:100` | **STALE PROSE** in a ruled-decisions doc; superseded by F4.1, unmarked |
| `docs/design/2026-07-25-floor-calibration-addendum-F.md:178,183,433` | OK — the amending doc naming what it retires |
| `docs/plans/v2/receipts/2026-07-26-packet11i-fixwave/REPORT-design-blind-11i.md:187` | OK — archived, historical |
| `docs/plans/v2/receipts/2026-07-26-packet11i-fixwave/REPORT-fable-design-11i.md:34` | OK — archived, pre-rename |
| `docs/plans/v2/receipts/2026-07-26-packet11i-fixwave/REPORT-fable-design-11i-b.md:187` | OK — the report that proposed the rename |
| `docs/plans/v2/receipts/2026-07-26-packet11i-build/REPORT-contract-11ia-1.md:136` | OK — the contract report naming the corpse |

**The sweep's REACH is the finding.** `TestTheRetiredStateNameIsGoneFromTheTree._hits` globs
`*.py` under the package root and the tests root only. Four LIVE `.md` lines — including §7's
state table, which is the design of record 11-ii will implement from — still teach the retired
name and no gate can see them. Repo law says three of four audited green-at-gate defects lived
in exactly this class. **Escalation: widen the sweep to `docs/design/` (and the ruled-decisions
docs), or amend those four lines now.**

---

## 8. P-PKG — MY PACKAGE TABLE, DIFFED AGAINST THE AUTHOR'S

Derived from the INSTALLED source in this worktree's venv, 2026-07-26.

| # | mechanism the contract specifies | my verdict | author's row |
|---|---|---|---|
| 1 | leader-election ALGORITHM | `replace_with_adapter` → `kubernetes.leaderelection` (READ: `leaderelection.py`, 183 LOC, zero k8s-client imports; `try_acquire_or_renew` verified line by line) | same — **agree** |
| 2 | the resource LOCK backed by our store | `bespoke` (no library ships a SurrealDB lock; the six-member surface is derived from the installed algorithm, not guessed) | same — **agree** |
| 3 | the FENCING token | `bespoke` (READ: `leaderelectionrecord.py` — exactly four fields, so fencing structurally cannot live in the record) | same — **agree** |
| 4 | the FALSE-`get` body shape | `bespoke` 3-field dataclass (READ: `ApiException.__init__` leaves `.body = None`; `json.loads(None)` raises) | same — **agree, and this was excellent work** |
| 5 | retry / backoff at the two new seams | `keep_with_trigger` → in-house `_txn.retry_on_conflict`; trigger = the next behavioural change to `_txn`'s retry policy evaluates `tenacity` first (#202) | same — **agree; `keep_with_trigger` is the right verdict and the trigger is named and real** |
| 6 | content hashing | `replace` → `loremaster.index.records.sha512_hex` (READ: source; `hashlib.sha512`, UTF-8) | same — **agree** |
| 7 | distributed-lock alternatives (`sherlock` &c.) | `bespoke` — no fencing surface | same — **agree** |
| **8** | **canonical serialisation of an axis mapping → bytes (`head_identity`'s pre-image)** | **NO ROW IN THE AUTHOR'S SURVEY** | **MISSING** |
| **9** | **canonical serialisation of the corpus walk → bytes (`corpus_content_digest`)** | **NO ROW IN THE AUTHOR'S SURVEY** | **MISSING** |
| 10 | the DDL emission helpers | `replace` → `surreal_schema._define_table` / `_define_field` / `_plain_index` | not surveyed; the clause pins enforce the POLICY, so the risk is low — but nothing requires the new slice to ROUTE through the helpers, so a future change to `_define_field` would not reach it |

### The one real finding: rows 8 and 9 have no read-column at all.

`orjson 3.11.9` **is installed** in this worktree. Probed here, 2026-07-26:
```
order-independent  : True                       # OPT_SORT_KEYS
NUL is ESCAPED     : b'{"scope":"pooled\\u0000statistic\\u0000forged","statistic":"x"}'
no separator forge : True
boundary shift     : True                       # ("ab","c") != ("a","bc")
```
Those are precisely the three properties the bespoke `\x00`-joined pre-image buys with (a) a
`\x00`-refusal guard, (b) a 12-mapping distinctness matrix written to defeat separator-naive
encodings, and (c) escalation **E1**, which had to choose between two readings that mint
different record identities. A JSON-canonical pre-image has one reading.

**I am not saying "you must use orjson."** There is a real counter-argument the author never
had to make: a frozen RECORD IDENTITY depends on the serialiser being byte-stable across
library upgrades, and a fully-specified in-repo encoding is auditable in a way a dependency's
key-ordering is not. That is a legitimate `bespoke` verdict — **but it has to be argued from a
read, and it was not asked at all.** E1 was escalated and ruled without anyone checking whether
the ambiguity needed to exist. **Escalation: add the row, state the read, and let the operator
ratify (A) with the alternative on the record — this is a non-`OVERWRITE`-able freeze.**

---

## 9. P3 — BRANCH REACHABILITY

Branches the built code will have, and the pin that fails if the branch is deleted:

| branch | killed by |
|---|---|
| `head_identity`: required-axis missing | `test_a_missing_required_axis_is_REFUSED` |
| `head_identity`: unregistered axis | `test_an_UNREGISTERED_axis_name_is_REFUSED` |
| `head_identity`: separator in a value | `test_a_value_carrying_the_PREIMAGE_SEPARATOR_is_REFUSED` |
| `head_identity`: non-`str` value | `test_a_NON_STRING_axis_value_is_REFUSED` |
| `head_identity`: defaulted-axis ELISION | `test_registering_a_new_axis_AT_ITS_DEFAULT_changes_no_existing_head_id` |
| `record_measurement`: `adopt=True` / `adopt=False` | both forced |
| `record_measurement`: `fence=None` / held / moved / absent-row | all four forced |
| `record_measurement`: **fence moves mid-commit** | **NOTHING — M1** |
| `record_measurement`: **rollback under an INTACT fence** | **NOTHING — M4 (unreachable through the real entry point in the current fixtures)** |
| `record_measurement`: the confirming re-read FAILS | **NOTHING — M5** |
| `enumerate_calibration_pool`: empty / full / truncated / mismatch | all four forced |
| `compare_and_set`: match / stale / holder-same / holder-different | all four forced |
| `release_if_held`: held / wrong identity / stale fence / absent row | all four forced |
| `create_if_absent`: created / lost race / **other rejection** | first two forced; **the third — M10** |
| `SurrealLeaderLock.get`: present / absent | both forced |
| `SurrealLeaderLock.create`: success / lost / stopped | success and stopped forced; **lost-race branch not forced through the adapter** |
| `SurrealLeaderLock.update`: success / **stale revision** / stopped | success and stopped forced; **stale — M7** |
| `SurrealLeaderLock.release_if_held` | **NOTHING — M8** |

---

## 10. P5 — CAN THE TEST DOUBLES FAIL?

`TestTheAbsentGetContract` uses three in-memory `_Lock` subclasses varying only the absent-`get`
shape. **They can fail, and the author proved it the right way:** two differently-broken
controls raise DIFFERENT exception types (`AttributeError` vs `TypeError`) and a positive
control shows a SUCCESS is observable. They bind to production through `LockAbsent`'s field
names. This is the best-instrumented part of the contract and I could not break it.

`_reference_head_preimage` in the domain test is a three-line in-test derivation checked against
a literal digest — the derivation cannot silently drift to match a wrong build, because the
literal would have to change too. Sound.

The `admin_db` / `floor_env` / `lease_env` fixtures are real live-engine harness fixtures, not
fakes. No mocked store anywhere — correct for this packet.

---

## 11. P4 — CLAIMS VERIFIED, NOT RELAYED

| author's claim (§2.1/§3/§6) | my verdict |
|---|---|
| 143 collected across four files | **TRUE** |
| `74 failed, 28 passed, 41 errors`, nothing at collection | **TRUE**, reproduced exactly |
| "five pins given explicit non-emptiness clauses" | **TRUE** — and a **sixth is vacuous** (`test_the_states_are_a_tuple_not_a_mutable_set`), harmless |
| "the 28 GREEN pins are green for the right reason" | **TRUE for 27 of 28** (see §1) |
| four mutation proofs HELD | **not re-run** (they mutate the real worktree; the brief forbids me git writes and a sibling had uncommitted work at spawn). The two source-scan pins they cover CAUGHT W28 independently, which is the stronger receipt. **Declared, not measured.** |
| `test_retry_seam.py` → `60 failed, 499 passed` | **TRUE**, reproduced exactly |
| "56 parametrised + 4 aggregate" | **TRUE**; the 4 aggregate ids match verbatim. (Finer split, FYI: 48 bare `[Class]` ids + 8 compound `[Class-case]` ids from `TestTheBootstrapAlwaysSurfacesAsAConnectionFailure`.) |
| **"Every one goes green when the builder routes ... "** | **FALSE — 3 stay RED. See B1.** |
| "adding the seams buys 60 pins for free" | **TRUE and load-bearing** — W28 was caught by them |
| lead's E4: "`adopted_n` … already pinned" | **FALSE** — `adopted_n` appears only at `test_floor_calibration_store.py:85,102` as a fixture kwarg; **W30 survives** |
| lead's E4: "the `insufficient_corpus` predicate … already pinned" | **FALSE** — no predicate exists in the freeze; the three floors are pinned as VALUES that nothing reads |
| E5: "five further `note` pins ARE owed — add them" | **NOT LANDED** (the contract is frozen at `d6c0dd4`, before the ruling — expected). `note` appears in no contract file. Flagged so it is not lost. |
| E3: "pin the library surface `try_acquire_or_renew` depends on" | **PARTIALLY LANDED** — the six-member derivation and the record's four fields are pinned; **the existence/arity of `try_acquire_or_renew` itself is NOT** (it is only *used*). A library rename would surface as a bare `AttributeError` inside a live test rather than as the named RED the ruling asked for. |

---

## 12. RESIDUALS — everything else I noticed, each with a verdict

1. **`FloorCalibrationStore.ensure_ready()` must emit the lease slice** for the contract to be
   satisfiable (B2), and nothing pins it. → **pin it, or re-specify the fence pin.**
2. **`measurement_history` returns raw rows via `SELECT *`.** Store reference §2: `SELECT *`
   OMITS a `NONE`-valued column, so every `option<>` column raises `KeyError` for a reader.
   The contract's own history pin reads `row["floor"]` — it works only because the fixture
   always sets `floor`. → **latent trap for 11-i-b; flag in its brief.**
3. **The migration pin's fixture prescribes a weak schema.**
   `CREATE floor_measurement:legacy CONTENT { state: 'measured' }` must SUCCEED, which forces
   every other `floor_measurement` column to be `option<>` or `DEFAULT`-ed — so the store can
   never require a measurement row to name its own head. Silent design consequence. → **operator
   ruling: is a `head_identity`-less measurement row acceptable at the store layer?** (The
   upside: it is exactly why the two live rejection pins discriminate — W4b proves it.)
4. **`LEASE_LOCK_NAME` / `LEASE_LOCK_NAMESPACE` are in the interface freeze and unpinned.**
   11-ii cites the freeze. → one-line value pin.
5. **`_statements()` splits the DDL on a bare `";"`.** Any future statement containing a
   semicolon inside a string literal silently mis-parses and the clause pins go vacuous for it.
   → low probability, cheap to note.
6. **The C8 ascending-order pin cannot distinguish a store-side `ORDER BY` from a client-side
   `sorted()`.** Declared, not door-built. Matters only if truncation semantics ever change.
7. **`SurrealLeaderLock.fence_epoch` is pinned only after `create`** — never after a renew or
   a seize. A build that stops updating it after the first write passes.
8. **Nothing pins that the two new DDL slices route through `_define_table` / `_define_field`.**
   The clause pins cover today's policy; a future change to the shared helper would not reach
   the new slice. ONE-IMPLEMENTATION, mild.
9. **`close()` tolerance of a never-connected store** is promised in both stubs' docstrings and
   pinned by neither. My reference build satisfies it; a build that raises would only be caught
   by fixture teardown noise.
10. **`scripts/` is still outside `scripts/typecheck.sh` (#188)** — the author flagged it; I
    confirm it, and it is unchanged at HEAD `652943a`.
11. **The sibling agent's work landed mid-run.** HEAD moved `81db016 → 652943a` while I was
    grading. I re-verified that `git diff --stat d6c0dd4 HEAD` over the eight graded paths is
    EMPTY, so the artifact I graded is the frozen one. No action needed; recorded for honesty.
12. **`docs/plans/v2/receipts/2026-07-24-packet11i/CONTRACT-FREEZE-DECISIONS.md:100`** carries a
    live prescriptive sentence using the retired state name. → amend or mark superseded.

---

## 13. WHAT THE CONTRACT DOES EXCEPTIONALLY WELL (so a fix wave does not damage it)

Stated because a NO-verdict that reads as a blanket condemnation invites a rewrite, and a
rewrite would lose these:

- **The seam shape.** Choosing a conventional `_query`-owning class over a bespoke seam bought
  56 real parametrised pins that CAUGHT the #102 routing-not-sharing build (W28) five times
  over. This is the single best structural decision in the packet.
- **The three design defects it caught** — the absent-`get` return shape (with TWO
  differently-broken controls, which is the difference between finding the bug and licensing
  the wrong fix), the record-decoration liveness wedge, and the forgeable digest concatenation.
  All three verified real; all three pinned; all three would have shipped.
- **The hot-row pins.** 8/16/32-way, overlapping lifetimes, separate connections, and an
  ARITHMETIC invariant rather than "it did not crash". W23b's first (invalid) variant died on
  them instantly.
- **`TestTheSchemaMigratesAnEXISTINGStore`** — the pin a virgin-DB suite structurally cannot
  have, actually written, and W32 shows the clause pins give it ∀ reach.
- **The refusal-over-escape choice for the `\x00` guard**, and the asymmetry argument for a
  golden vector on the head id but only a property on the corpus digest. Both are correct.

---

## 14. VERDICT

**CONTRACT INSUFFICIENT.**

Nine of fourteen valid wrong builds passed the whole contract at 143/0, four of them walking a
mechanism the RULED DESIGN explicitly specifies straight out of the build with nothing to see
it: the fence is not atomic (W2), the exact-skip digest is relocation-blind (W5), the head's
monotonic revision counts the wrong events (W25), and the classifier E2 exists to constrain can
swallow every real defect on its path (W31). Separately, the contract as frozen is **not
satisfiable** without an undisclosed `test_retry_seam.py` edit (B1) and an undisclosed
cross-slice `ensure_ready` coupling forced by a direct collision between the contract and E2's
own rider (B2).

The fixes are cheap — M1–M14 are roughly one function each, and the contract's existing
scaffolding (live fixtures, the `_measurement` factory, the lease store) supports every one of
them without new machinery. They were expensive only to think of.

**Route back to CONTRACT with M1–M14 and B1–B3. Do not let a builder start on `d6c0dd4`.**
