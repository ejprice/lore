# REPORT-adversary-63b-ii-b — CONTRACT ADVERSARY grade of the ii-b RED contract

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK (brief-base §1)

- **VERDICT: CONTRACT INSUFFICIENT** — 1 C-DEF (a pin RED on the correct build, empirically
  confirmed) + 3 missing pins, the first of which lets a wrong build survive the core §4.B property.
- **P1 result — did a wrong build survive?** YES on the read side: a `drain(subject=)` that resolves
  the Subject (satisfying R6 + the P4 bound line) but does NOT splice the read_filter into its SELECT
  (serves the unfiltered set) passes P1 / P4 / F-1 — **the drain read_filter FILTERING is unpinned**
  (Finding 2). The schema/migrate + R6 sides survived every wrong build I could construct.
- **state:** done-with-deviations. Full empirical build ran for the SCHEMA/MIGRATE (DDL-drop) and R6
  (spec-flip) pins; the full read-governance reference build (drain/ack `subject=`, renders, one-txn)
  was NOT built (out of proportion to the adversary budget) — those pins are graded by
  interface-reasoning + by-construction fixture analysis, and I SAY which legs ran (§Legs).
- **QUANTIFIER TABLE:** §Q. Load-bearing rows: P2/P2-m ∀-emitted-fields (derived) ✓; Leg A/B ∀-6-shapes
  (enumerated, reach pinned by P2-m) ✓; R6 ∀-True-set (derived + coverage assert) ✓; **read-filter
  FILTERING ∀: covered for ACK (P7), UNCOVERED for DRAIN (Finding 2).**
- **REACH TABLE:** §R. P2/P2-m, R6-driver, P-G2 reaches are DERIVED + coverage-checked (empirically
  reddened by adding a site). P5 render-coverage reach is from-truth BUT its write_guard exclusion +
  hand-list floor leave a latent hole for a future read-that-writes render (Finding 6).
- **MISSING PINS (each: test that should exist + defect it catches):** §Findings 2, 3, 4.
- **Fixture-discrimination:** DD-3.c legs discriminate per-shape BY NAME (wrong-build A: body caught,
  4 others green); R19 grade discriminates (wrong-build B: 4 pins red, positive control green); R6
  coverage + behavioural + AST all discriminate. F-1 has a vacuity residual (Finding 5).
- **Satisfiability receipt:** the ruled DDL-drop reference build → schema/migrate **22 live PASS + 7
  offline PASS**, EXCEPT `test_frozen_old_world_matches_the_emitters_current_asserts` which is a
  **C-DEF (Finding 1)**. `loremaster.__file__` inside scratch: proven (§Legs).
- **Dev-3 (P-G3 construction isolation):** SOUND — discriminates the drop-grade build (empirical).
- **Dev-4 (P5 write_guard exclusion):** SOUND for the 6 named renders (the floor is a checked
  non-vacuity guard); residual hole for future read-that-writes renders (Finding 6).
- **Graded:** `8000385` · HEAD-at-report: `8000385` · SAME. (`8000385` touched only
  `scripts/probe_drain_read_63b_ii_b.py`; the contract is `4aaf45f` and is byte-identical at both.)
- **Packages considered:** none — no production mechanism specified (the contract is tests; the fix is
  a DDL-constraint drop + a read-governance wiring that rides the existing emitter/ledger).
- **Reuse ledger:** none — I authored no reusable production/test symbols (adversary probes are
  scratch mutations of the reference build, discarded).
- **decisions-needed (for the contract author / lead):** Findings 1–4 below — each names the exact fix.

---

## Findings

### Finding 1 — **C-DEF (BLOCKER): `test_frozen_old_world_matches_the_emitters_current_asserts` is RED on the correct build**

`test_comms_schema.py::TestTheMessageAssertsAreDroppedFromADIRTYStore::test_frozen_old_world_matches_the_emitters_current_asserts`
asserts that four ASSERT literals (`string::len($value) <= 4000`, `<= 256`, `array::len($value) <= 20`,
`$value IN ['signal','directive']`) each appear in the LIVE `generate_message_ddl()`. But the ii-b
ruling (§12.3/§13.3, W9 + R1) DROPS exactly those length ASSERTs from `message.{thread,body,refs,refs[*],
task_id}` **and** from `to.ack_note`. After the ruled drop, three of the four literals are GONE from the
emitter (`grade`'s survives). The pin compares a FROZEN constant against a LIVE emitter that the build
is *designed* to change, so it cannot distinguish "the frozen capture rotted" (its stated purpose) from
"the emitter dropped the ASSERTs" (the ii-b build) — and reds on the latter.

**Reproduction (empirical, on the EXACT ruled DDL-drop reference build):**
```
tests/test_comms_schema.py::TestTheMessageAssertsAreDroppedFromADIRTYStore::test_frozen_old_world_matches_the_emitters_current_asserts
E  AssertionError: the frozen 0566587 old world carries 'ASSERT string::len($value) <= 4000' but the current emitter does NOT …
1 failed, 7 passed, 245 deselected in 1.90s     # the 7 pass = P2/P2-m[to,message], P-G2, D-M11×2, thread×2
loremaster.__file__ = /tmp/.../scratchpad/ref_build/loremaster/loremaster/__init__.py   (provenance proven)
```
**Internal contradiction proving this is a C-DEF, not my misconfiguration:** on the SAME reference
build, `test_BASELINE_the_asserted_old_world_refuses_every_violator` (which applies
`frozen_asserted_message_ddl()` and asserts all 6 violators are refused) is GREEN — i.e. the frozen
world is still fully asserted — WHILE `test_frozen_old_world_matches_the_emitters_current_asserts` is
RED. The frozen constant is (correctly) independent of the emitter; the "matches" pin demands they agree,
which the ii-b build makes impossible.

**The test that should replace it:** assert the frozen constant is self-consistent (its OWN text
contains the four ASSERT literals — proving the capture is a faithful *asserted* world), NOT that the
live emitter still emits them. A frozen fact is verified against the git-pinned snapshot it froze
(0566587), never against a moving emitter. As written it traps the builder between the ruling and the
contract with every production gate green — the exact "a pin RED on the correct build for a fixture
reason" class (C-DEF, PKT-28).

### Finding 2 — **MISSING PIN (BLOCKER): the DRAIN read_filter FILTERING is unpinned**

The core §4.B property is that the ii-b `drain(subject=)` SERVES only the messages the Subject may see.
The `read_gov_world` fixture (`test_comms_read_governance_63b_ii_b.py`) is built PRECISELY for this — a
VISIBLE message (server scope, `visible_seq=0`) and an INVISIBLE one (a foreign principal's
principal-private, addressed to me by a `to` edge but excluded by my read_filter, `invisible_seq=1`).
But the invisible message is exercised ONLY by:
- `TestAnAckOfAnInvisibleSeqIsUnknownMessage` — an **ACK** (P7), not a drain;
- `TestTheDrainDecodesBeforeItStamps` — a drain, but it FORCES a decode failure (monkeypatches
  `_row_to_inbox_entry` to raise), so it never inspects WHICH messages are served.

**No test asserts that a drain serves the visible message and EXCLUDES the invisible one.** The two
drain-serves fixtures both hold only VISIBLE messages: `P1`'s `dirty_to_world` seeds two `scope="server"`
messages (both member-visible); `P4`'s `test_a_multi_entry_drain…` sends two SELF-addressed messages
(visible to self). So a **wrong build** whose `drain(subject=)` resolves the Subject (to satisfy R6's
deny-without-capability and to render the P4 bound line) but *forgets to splice the read_filter into the
SELECT* — serving all of the agent's edges, invisible ones included — passes **P1** (both its messages
are visible → both served+stamped), **P4** (bound line once), and **F-1** (decode fails). This is the
"partial fix" wrong build (right on the resolve/deny/bound, unfixed on the filter), and it is exactly
the brief's §6 "served-COUNT-is-over-the-served-SET" / F4 "no argument moves the visible set beyond the
Subject's authz" attack — with NO pin.

**The test that should exist:** `test_a_drain_serves_only_the_visible_message` over `read_gov_world` —
`result = drain(subject=subject)`; assert `visible_seq ∈ {e.seq for e in result.entries}` AND
`invisible_seq ∉ {e.seq …}`; and the invisible edge's `seen_at` stays NONE (§4.3 "neither served nor
stamped"), with a control that a drain by the FOREIGN subject serves the invisible one (proving the
fixture message is drainable — the read_filter, not deadness, excludes it). Reproduction is
by-construction (the pin does not exist; every drain fixture lacks an invisible message in its window —
verified by reading all four drain tests, §Legs). This is the dual of P7 for the DRAIN verb, and the
one that guards the property this whole wave turns on.

### Finding 3 — **MISSING PIN: P4's once-per-response count pins only DRAIN**

Ruling §9.1/R7 + worklist W6 specify P4 "render pins **per verb** — once-per-response". The contract
implements the count (`rendered.count("visible via") == 1`) ONLY for `drain`
(`TestTheServedReadResponseCarriesTheBoundLineExactlyOnce`). The other row-bearing top-level renders —
`_render_comms_await` (shares the drain row), `_render_comms_story` (message rows), `_render_comms_ack`
(per-fate rows) — have NO once-per-response count. P5's coverage derivation only checks each top-level
render *references* `render_subject_bound` (presence, not count), and does NOT forbid a SUB-render from
carrying it. So a build that clones the bound into `_render_story_message`/`_render_comms_await`'s row
render (bound-per-row) reds only for drain; for story/await/ack it survives.
**Test that should exist:** the drain once-per-response count, parametrized over
`{drain, await(non-empty), story, ack}` (each driven to a multi-row response), asserting the marker
count is exactly 1.

### Finding 4 — **MISSING PIN: the WITH-capability rollup filtered-count is unpinned**

`TestTheRollupMessageLegNamesTheCapabilityBound` pins ONLY the TOKENLESS leg (`messages: identity
required`, no count). §9.4's OTHER case — a verified capability yields a **FILTERED** count `messages
activity (k)` whose `total` "describes the set its label claims (Leg 1)" — has no pin. A build whose
capability-bearing rollup serves an UNFILTERED count under the filtered label (the §6 count-over-set
leak, one level up from Finding 2) passes. **Test that should exist:** a credentialed rollup over a
world with N visible + M invisible message-activity rows asserts the served count is N (not N+M) and the
scope bound heads the LEG.

### Finding 5 — **RESIDUAL: F-1 lacks a positive control that the decode was reached**

`test_a_decode_failure_does_not_leave_the_row_stamped` monkeypatches `_row_to_inbox_entry` to raise, then
asserts every edge `seen_at IS NONE`. It never asserts the forced `ValueError` was actually raised (the
`except ValueError: pass` swallows it silently). If the drain serves NOTHING (e.g. an over-filtering
build — the inverse of Finding 2), `_row_to_inbox_entry` is never called, no ValueError, and the
`seen_at IS NONE` check passes VACUOUSLY. The primary hazard (stamps-then-decodes) IS caught, but the
pin should assert the decode was reached (e.g. `pytest.raises(ValueError)` around the drain, or that the
served set was non-empty) so it cannot pass for a no-rows-served reason.

### Finding 6 — **RESIDUAL (bounded): P5 write_guard exclusion is safe now but its ⊇ floor is a hand-list**

Dev-4 judgment: the from-truth `write_guard` exclusion correctly drops `_comms_send`'s WRITE receipt
render (`_render_comms_send` takes no `subject`, so its inclusion would false-RED the coverage pin) and
does NOT drop the reference read handlers — because `_comms_drain`/`_comms_ack` do NOT call
`write_guard` at HEAD (their `to`-stamp is attributed inside the ledger, not by a handler-level guard),
so the ii-b build that only ADDS `_resolve_subject` keeps them in the derived set, and the checked floor
`test_the_derivation_reaches_the_ii_b_comms_renders` reds if any of the 6 named renders is excluded.
**The bound:** a FUTURE governed read render whose handler DOES wrap a write in a handler-level
`write_guard` (a read-that-writes, exactly drain/ack's shape) would be silently excluded by the
predicate AND absent from the hand-list floor — neither instrument catches it, contradicting §9.3's
"⊇ floor so a seventh joins without churning". **Re-open trigger:** the first governed read render that
carries a handler-level `write_guard`. (Not a current-wave defect — the 6 ii-b renders are protected.)

---

## §Q — QUANTIFIER TABLE (per load-bearing invariant)

| invariant | ∀-over-inputs or guarded? | receipt |
|---|---|---|
| P2/P2-m: no field carries a legacy-violable constraint | **∀ over emitted DDL fields** (derived via `_overwrite_field_statements`) + non-vacuity floor + exemption non-vacuity | wrong-build A red per-field BY NAME; wrong-build B red on grade exemption (empirical) |
| Leg A: the drop LANDS | ∀ over 6 enumerated shapes; reach pinned by P2-m | wrong-build A: `[body]` red, 4 others green |
| Leg B: real migrate survives | ∀ over 6 seeded rows; C-CONTROL proves the instrument sees the hazard | wrong-build A: main leg red; ref build: 6 stamped |
| P-G2: grade one-source | equality of 3 surfaces; sharing proven by mutation | wrong-build B: red |
| P-G3: junk grade refuses (KNOWN BOUND) | guarded-by-the-junk-grade case + positive control | wrong-build B: red, control green (Dev-3 SOUND) |
| R6: capability required | **∀ over derived True-set** + coverage assertion | R6-a: coverage red on 6th verb; R6-b: behavioural+AST red |
| P7: invisible-seq ACK → unknown | guarded-by-the-invisible case + visible control | (interface graded; RED-at-HEAD via TypeError) |
| **read_filter FILTERING (drain)** | **NEITHER — UNPINNED** | **Finding 2 — no drain test excludes an invisible message** |
| P4: bound once-per-response | guarded — DRAIN only | Finding 3 |
| F-1: decode before stamp | guarded-by-forced-decode; vacuity residual | Finding 5 |

## §R — REACH TABLE (per guard the contract introduces/relies on)

| guard | reach DERIVED vs hand-list | coverage a checked variable? | effect vs proxy | verdict |
|---|---|---|---|---|
| P2/P2-m field ∀ (`_overwrite_field_statements`) | DERIVED from emitted DDL | YES (floor + non-vacuity; reddens when a field joins) | effect (the emitted statement) | SAFE (empirical) |
| R6 driver table coverage (`required - drivers.keys()`) | DERIVED True-set vs hand driver-map, diffed | YES (`assert not uncovered`; anti-vacuity `assert required`) | effect (real `GovernedDenied`) | SAFE (R6-a red on uncovered 6th verb) |
| R6 handler-resolves-subject (AST floor) | DERIVED over True-set | YES | AST presence (proxy) — closed behaviourally by the driver table | SAFE (R6-b: both red) |
| P3 single-writer floor | DERIVED (`derive_member_source_roots` + `governed_table_raw_mutation_sites`) | YES (non-vacuity per row) | effect (source scan) | SAFE (ref build green; not mutation-tested — leg not run) |
| P5 render coverage (`_governed_read_render_methods`) | DERIVED read-render set (from-truth `_resolve_subject`) | partial — write_guard exclusion is an *assumption*, floor is a **hand-list of 6** | AST presence | **HOLE for future read-that-writes render (Finding 6)** |
| P-G2 grade one-source | 3 surfaces | mutation-provable | effect | SAFE (wrong-build B red) |
| Leg A/B shape set | hand-list of 6 shapes, backed by P2-m's derived reach | YES via P2-m | effect (engine accept/reject) | SAFE (ruling-acknowledged split) |

Legs run empirically: P2/P2-m, P-G2, Leg A, Leg B, P-G3, single-writer floor, R6 coverage/behavioural/AST,
the Finding-1 C-DEF. Legs graded by reasoning/construction (reference build NOT fully built): P1, P4, P6,
P7, F-1, P5 satisfiability + Findings 2–6. Said out loud per role.

---

## Probe record

### Satisfiability receipt — the ruled DDL-drop reference build
Scratch: `./scripts/scratch_copy.sh` (provenance-asserted). Edit = the EXACT ruling: `_MESSAGE_FIELD_SPECS`
`thread/body/refs[*]/task_id → ""`, `refs → "DEFAULT []"`, **grade ASSERT KEPT (R19)**; `_TO_FIELD_SPECS`
`ack_note → ""`. `loremaster.__file__` = `…/scratchpad/ref_build/loremaster/loremaster/__init__.py`.
- Offline schema pins: `1 failed, 7 passed` — the 1 failure is Finding 1 (C-DEF); the 7 pass are
  P2/P2-m[to,message], P-G2, D-M11 `refs`/`refs[*]`, thread×2.
- Live schema/migrate (`-k "not test_frozen_old_world_matches"`): **`22 passed, 1 deselected in 42.81s`**
  — Leg A drop legs + BASELINE + clean-control + grade-STAYS + idempotent; single-writer floor ×3;
  Leg B main + idempotent + C-CONTROL; P-G3 + legal-grade control. So the DDL-drop half is satisfiable
  EXCEPT Finding 1.

### DD-3.c two-leg discrimination (wrong builds)
- **Wrong-build A** (re-add ONLY `body`'s length ASSERT): `3 failed, 5 passed` —
  `test_the_length_assert_DROPS[body]` red (the other 4 length shapes green — caught BY NAME),
  `P2-m[message]` red, Leg B main leg red (`SurrealDB … backfill rejected (assert violation)`),
  `P2[to]` green.
- **Wrong-build B** (drop `grade`'s ASSERT): `4 failed, 2 passed` — `P-G2` red, `P2-m[message]`
  (exemption non-vacuity) red, Leg A `grade_assert_STAYS` red, `P-G3` red; positive controls green
  (`P2[to]`, `test_CONTROL_a_legal_grade_fixture_migrates_cleanly`). R19 grade-KEEP is well pinned.

### R6 reach attack (the load-bearing one)
- **R6-a** (flip `heartbeat` True — a 6th True verb with NO driver row):
  `test_every_capability_required_verb_denies_without_one` red at the COVERAGE ASSERTION:
  `AssertionError: requires_capability verbs ['heartbeat'] have NO driver row …`. Reach IS a checked
  variable — the True-set cannot outrun the driver map.
- **R6-b** (flip `drain` True with NO handler change): `test_every_capability_verb_handler_resolves_the_subject`
  (AST floor) red naming `_comms_drain`; `test_every_capability_required_verb_denies_without_one`
  (behavioural) red with `Failed: DID NOT RAISE GovernedDenied` — the typed-applicability lie is caught
  behaviourally (right reason), not just structurally.

### Fixture / interface analysis (read-governance)
- `read_gov_world` has visible+invisible messages; invisible used only by P7(ack) + F-1(decode). No
  drain-serves-only-visible pin exists (Finding 2). P1/P4 drain fixtures hold only visible messages.
- `_comms_send` calls `governed.write_guard("send")` (server.py, resolves subject at its head); the
  ii-b read handlers do NOT at HEAD — the Dev-4 basis for Finding 6.
- Contract interfaces the reference build must match (RED-at-HEAD via TypeError, legible `pytest.fail`):
  `ledger.drain(agent_id,limit,peek,subject=)→.stamped_seqs/.entries[.seq]`;
  `ledger.ack(agent_id,seqs,subject=)→.entries[.seq/.outcome/.acked_at]/.acked_count`;
  `AppContext.comms(...,capability=)`; `AppContext.render_subject_bound(subject)`. No interface C-DEF
  found among these (they are additive to HEAD).

## Deviations (brief-base §1/§4)
- Full read-governance reference build NOT undertaken (drain/ack `subject=`, one-txn, renders, rollup) —
  ~the entire builder wave; out of proportion to the adversary budget. Those pins graded by interface
  reasoning + by-construction fixture analysis; legs said out loud (§R). The schema/migrate + R6 halves
  were fully built and mutation-tested.
- Capability check: lore tools loaded (`ToolSearch +lore`); `Read`/`awk` for spans (grep/rg hook-blocked
  on this live-indexed checkout — every textual sweep is `awk` over an explicit file list, said so);
  `scratch_copy.sh` + spike-surreal `ws://127.0.0.1:18000` (never :18500) reachable. No worktree.
- No production or contract file edited in the repo; all probes live in the scratch copy.
