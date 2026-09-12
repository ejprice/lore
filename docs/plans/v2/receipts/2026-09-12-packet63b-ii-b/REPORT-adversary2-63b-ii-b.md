# REPORT-adversary2-63b-ii-b — CONTRACT ADVERSARY round 2 (DELTA grade) of the ii-b RED contract

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK (brief-base §1)

- **VERDICT: CONTRACT SUFFICIENT (for the DELTA `4aaf45f`→`5a18951`).** Every one of the reviser's 10
  items + the D1 rework discriminates; I could not construct a wrong build that survives the revised
  pins. The two load-bearing round-2 questions both clear EMPIRICALLY.
- **P1 result — did any wrong build survive the delta? NO.** The three wrong builds I constructed all
  RED the pin that should catch them (B1's frozen-rot, B2's read-filter partial-fix, Dev-4's
  wrongly-exempted read), each paired with a positive control.
- **B1 (C-DEF) CLEARED, empirically:** the replacement `test_the_frozen_old_world_is_a_faithful_asserted_capture`
  is **GREEN on the ruled DDL-drop reference build** (the EXACT site round-1's C-DEF was RED) — the trap
  is gone. It compares the FROZEN constant (a hand-captured literal, emitter-independent) against ITSELF.
  P0: it REDs when the frozen capture drops a literal → a real anti-vacuity control, not a tautology.
  Round-1 name `test_frozen_old_world_matches_the_emitters_current_asserts` is GONE everywhere.
- **B2 (the pin the wave turns on) DISCRIMINATES, empirically:** the partial-fix wrong build
  (`drain(subject=)` resolves the Subject but does NOT splice the read_filter) reds
  `test_a_drain_serves_only_the_visible_message` (`served=[0,1]`, `assert 1 not in {0,1}`); the
  FOREIGN-subject CONTROL passes (the invisible edge is live/drainable — exclusion is the read_filter,
  not deadness). Round-1 Finding 2 CLOSED.
- **D1 (reworked drain P4 pin, DN1) RED-at-HEAD for the RIGHT reason:** full read-gov file at HEAD =
  **`12 failed, 0 passed`**, every RED a legible unbuilt-seam reason (missing `subject`/`capability`),
  **zero `no session keep`/`GovernedDenied`** — all credentialed SENDS succeed. The round-1 latent C-DEF
  (send-setup denial) is FIXED by the register-TOOL keep idiom.
- **Satisfiability:** the ruled DDL-drop reference build → **`47 passed, 0 failed`** on the schema/migrate
  half (round-1's single C-DEF failure is gone). `loremaster.__file__` proven inside scratch.
- **QUANTIFIER TABLE (delta):** §Q. **REACH TABLE (delta):** §R. All rows classified; guarded rows carry receipts.
- **MISSING PINS: NONE.** Residuals (flags, none blocking): §Residuals — B2 subject-owns-agent
  correct-build caveat · G2 substring-count fragility · G2 `_rollup(capability=)` interface (DN2) ·
  G1 hand-listed carrier set (a future row-bearing read verb needs its own once-count).
- **Graded:** `5a18951` · HEAD-at-report: `5a18951` · SAME. (The delta vs `4aaf45f`; round-1 graded `4aaf45f`.)
- **Packages considered:** none — no production mechanism specified (the artifact is a test contract;
  the build is a later wave). **Reuse ledger:** none — all probes are scratch mutations of the
  reference build, discarded.
- **decisions-needed (for lead/builder):** relay DN2 (`_rollup(capability=)` interface assumption) +
  the B2 subject-owns-agent caveat into the builder brief; both are correct-build satisfiability items
  the cold audit backstops. NOT blockers on the contract.

---

## What I re-graded vs. inherited

Per the brief, I graded the **DELTA** (`git diff 4aaf45f 5a18951`, 6 files) and did NOT re-grade the
round-1-confirmed-sound halves (schema/migrate + R6), EXCEPT that I rebuilt the schema/migrate reference
to confirm B1's C-DEF trap is gone (the single most important re-check). Round-1 report
`REPORT-adversary-63b-ii-b.md` (Findings 1–6) and the binding ruling §14 (`docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md`)
are the frame.

**Legs run EMPIRICALLY:** B1 (green on ref build + P0 rot-mutation) · satisfiability 47/0 · B2 (partial-fix
wrong build reds + control passes) · D1 (12/0 at HEAD, reasons inspected) · Dev-4 (two mutations: stale
reds, wrongly-exempted-read reds) · Dev-3 (passes at HEAD, type hierarchy analysed) · MP-7 (wider
independent sweep) · G1/G2 structural (shared-helper call-site enumeration) · capability nit + rename sweep.
**Legs graded BY-CONSTRUCTION (read-governance reference build out of budget, as round 1 → cold audit is
the satisfiability backstop):** the CORRECT-build greens of B2/G1/G2/F5 (the wrong-build/discrimination
direction WAS built for B2 and Dev-4; the correct-build handlers were not). Said out loud per role.

---

## Delta grades — item by item

### B1 (C-DEF fix) — **CLEARED.** ✅ (the round-2 load-bearing re-check #1)
- **Reference build = the ruled DDL-drop** (`_MESSAGE_FIELD_SPECS` thread/body/task_id/refs[*] → `""`,
  refs → `"DEFAULT []"`, **grade KEPT (R19)**; `_TO_FIELD_SPECS` ack_note → `""`), applied in scratch.
  `loremaster.__file__ = /tmp/…/scratchpad/ref_build/loremaster/loremaster/__init__.py` (INSIDE scratch — provenance proven).
- `test_the_frozen_old_world_is_a_faithful_asserted_capture` → **`1 passed`** on the DDL-drop reference
  build — the EXACT site where round-1's `test_frozen_old_world_matches_the_emitters_current_asserts` was
  RED. **The C-DEF trap is removed.** It now asserts the 4 literals against `frozen_asserted_message_ddl()`,
  which (`_governed_contract.py:526`, read) is a HAND-CAPTURED literal, genuinely emitter-independent — so
  the ii-b emitter's drop cannot make it red.
- **P0 control (proves it is not a tautology):** mutated the scratch frozen constant to drop `body`'s
  `<= 4000` literal → B1 **RED** for the right reason (`the FROZEN 0566587 asserted old world is MISSING
  'ASSERT string::len($value) <= 4000'`). So it discriminates a rotted capture. Restored.
- Round-1 C-DEF name **GONE** everywhere (awk over `loremaster/tests/*.py` + `_governed_contract.py`).

### Satisfiability — schema/migrate reference build goes FULLY 0-failed. ✅
- `test_message_migrate_dirty_store_63b_ii_b.py` (whole) + `test_comms_schema.py::{TestTheMessageAssertsAreDroppedFromADIRTYStore,
  TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate, TestMessageDdlOffline, TestTheSingleWriterFloorPerTable}`
  on the DDL-drop reference build → **`47 passed in 42.20s`, 0 failed.** Round-1's single C-DEF failure is
  gone. My selection is broader than round-1's counted subset (whole classes) — 0-failed is the receipt.
  The drop IS exercised: the Leg-A accept-over-cap legs + the P2-m ∀ are in the 47 and RED at HEAD without it.

### B2 (load-bearing NEW pin, §4.B) — **DISCRIMINATES.** ✅ (the round-2 load-bearing re-check #2)
- Fixture `read_gov_world` (`test_comms_read_governance_63b_ii_b.py:55`) seeds a visible (server-scope)
  AND an invisible (foreign-principal principal-private) message, **each with a `to` edge to the recipient**
  (`_relate_edge` lines 87 + 95). So an unfiltered drain WOULD serve both — the fixture discriminates.
- **Partial-fix WRONG build** (add `subject=` to `MessageLedger.drain`, accept it for R6/P4 but NEVER
  splice the read_filter — HEAD's `drain` already SELECTs `WHERE out=$agent AND seen_at IS NONE`, the
  unfiltered `to`-edge set): `test_a_drain_serves_only_the_visible_message` **RED** —
  `AssertionError: … was SERVED … served=[0,1]`, `assert 1 not in {0,1}`. CONTROL
  `test_CONTROL_a_foreign_subject_sees_the_invisible_message` **PASSED** (invisible edge is live/drainable
  → the exclusion is the read_filter, not deadness). Round-1 Finding 2 CLOSED.
- Correct-build leg (drain serves visible, excludes invisible) BY-CONSTRUCTION: `governed.read_filter`
  (`governed.py:242`) splices `AND ({fragment})` over the table's columns; mapping onto the `to`-relation
  `in.scope`/`in.owner_principal` is read-governance design → cold audit backstops. B2 is satisfiable by
  construction (server-scope served; foreign principal-private excluded; PDP "member sees own
  principal-private" gives the control its correct-build pass).

### D1 (reworked drain P4 pin, DN1) — **RED-at-HEAD FOR THE RIGHT REASON.** ✅
- Full read-gov file at HEAD (5a18951): **`12 failed, 0 passed in 23.98s`.** Reasons inspected (awk):
  ack/drain `does not accept a subject argument`; 5×G1/P4 reads reject `capability` (foreign param);
  `_rollup` rejects `capability`. **ZERO `no session keep`/`GovernedDenied`** → all sends succeed.
- The round-1 latent C-DEF (the landed drain pin denied at the send SETUP, `session 's1' has no session
  keep`, because `register_owned` bypasses the register TOOL) is FIXED: the credentialed
  `ctx.comms(action="register", …)` mints `session:s1`, and the RED is now at the READ (the real
  property), not the setup. A false-RED-that-greens-when-the-setup-is-fixed is gone.

### G1 (P4 siblings, §9.1) — **DISCRIMINATES (structural + by-construction).** ✅
- `_assert_bound_once` (def 345, `count == 1`) is ONE shared POLICY called by ALL 5 carriers: drain (435),
  non-empty await (472), empty await (519), multi-message story (560), multi-seq ack (601) — never cloned;
  the landed drain pin was refactored to call it too (DN1). `_rendered_read_or_red_at_head` (the RED-at-HEAD
  wrapper) likewise shared by all 5 (432/468/515/554/597).
- Discrimination (correct-build, by-construction): a sub-render clone (bound-per-row) → count > 1 → RED;
  a top-level render omitting the bound → count 0 → RED. The carriers cover the sidecar's named set
  incl. story's per-message sub-render (THE clone risk) and empty-await (Leg-1-matters-most, driven by a
  fake awaiter, no ~55s wait). Round-1 Finding 3 CLOSED for the named verb set.

### G2 (capability rollup, §9.4) — **DISCRIMINATES the named wrong builds.** ✅ (with fragility residual)
- RED-at-HEAD via `AppContext._rollup` no-`capability` TypeError (verified). Correct-build asserts (by
  construction): filtered count k=2 not the unfiltered N+M=3 (`"2" in activity_line and "3" not in`); the
  bound HEADS the LEG (immediately above `messages activity`), not the response head (which would
  over-claim about the ungoverned task/finding legs). Fixture seeds N=2 visible (send seam) + M=1 invisible
  (raw foreign principal-private) + 1 ungoverned task leg. Catches the §6 count-over-set leak + the
  response-head over-claim. Round-1 Finding 4 CLOSED.

### F5 (F-1 vacuity, Finding 5) — **CLOSED (by-construction).** ✅
- The `decode_reached` positive control asserts the forced decode was actually reached; an over-filtering
  build that serves nothing never calls `_row_to_inbox_entry`, raises no ValueError, and would pass the
  `seen_at IS NONE` check VACUOUSLY → now REDs. Correct-build-only (at HEAD the TypeError guard fires
  first). Round-1 Finding 5 CLOSED.

### Dev-4 (§14.2, the write_guard exclusion → exemption) — **DISCRIMINATES BOTH DIRECTIONS (empirical).** ✅
- write_guard EXCLUSION removed: `_render_comms_send` (a subject-resolving write_guard-caller) is now IN
  the derived set (`_governed_read_render_methods()` → `{_render_comms_send, _render_recalled_memories}`),
  exempted explicitly. This is the round-1 Finding 6 mechanism: a read-that-writes is no longer silently
  excluded.
- **Mutation (a) STALE exemption:** add `_render_ghost_that_is_not_derived` → `test_the_write_receipt_exemption_is_non_vacuous`
  **RED** (`exemption is STALE and silently exempts nothing`).
- **Mutation (b) wrongly-exempted READ:** exempt `_render_recalled_memories` (a genuine derived read,
  handler `recall` has no write seam) → **RED** (`handler AppContext.recall contains NO WRITE-family seam …
  a governed READ wrongly exempted … would look EXACTLY like this`). **Round-1 Finding 6 CLOSED** — the
  exemption cannot hide a read.
- Coverage pin GREEN at HEAD (governed = `{_render_recalled_memories}` already carries the bound); the
  floor RED at HEAD (the 6 ii-b renders unbuilt) — the growth property holds.

### Dev-3 (§14.1, typed raise) — **CORRECT (empirical + hierarchy analysis).** ✅
- P-G3 + Leg-B C-CONTROL + the legal-grade control → **`3 passed`** at HEAD (grade ASSERT present poisons
  the migrate; the `governed.message_backfill.rejected` ERROR log confirms the driver's wrapped domain
  rejection). The tightening `pytest.raises(TxnDomainRejectionError, match=r"\(assert violation\)")` is
  strictly narrower than the old bare `Exception` and discriminates ALL FOUR wrong-reason cases:
  transport (`SurrealConnectionError`) + contention (`TxnContentionExhaustedError`) are DISJOINT types →
  red; a fixture `TypeError` → disjoint → red; and — the subtle one — `TxnGovernedConflictError` is a
  **SUBCLASS** of `TxnDomainRejectionError` (`_txn.py:189`), so the TYPE alone would admit it, but its
  `governed_conflict:` message fails the `(assert violation)` match → red. The match carries the
  discrimination the type cannot, exactly as §14.1 anticipated.

### MP-7 / B3 (corpse deletion + re-sweep) — **CLEARED (wider than the reviser's).** ✅
- Deleted corpse `def test_body_carries_a_length_bound_the_store_itself_enforces` GONE; collection intact.
- Independent anchor-free `awk` sweep of `test_comms_schema.py` — literal-number AND cap-constant-NAME
  interpolation (`MESSAGE_{BODY_MAX_CHARS,POINTER_MAX_CHARS,REFS_MAX_COUNT}`) AND `_field_statement(…,dropped-field)`.
  The ONLY demanded-present `assert "ASSERT" in` sites are `agent.status` (479, KEPT, not a message field)
  and `message.grade` (1736, KEPT by R19 — the inverse of a corpse). All cap-constant hits are the NEW
  world's accept-over-cap fixtures. **No surviving message-field store-ASSERT corpse.**
- Cross-file sweep (test_message_ledger.py, migrate, enforcement, send_scope): 3 hits, all PROSE/docstrings
  acknowledging the drop or the KEPT grade bound — no corpse assertion. (Beyond the brief's scope; surfaced.)

### Nits (§14.4) — RESOLVED.
- Grade dup-name: schema renamed `test_grade_ddl_is_a_closed_two_value_domain` (1721); ledger keeps
  `test_grade_is_a_closed_two_value_domain` (test_message_ledger.py:347) — two distinct names, grep hazard gone.
- `_REQUIRED_IN_II_B_NOT_YET` → `_READS_REQUIRED_IN_II_B`: fully renamed (no dangling refs); the capability
  pin `TestCommsActionSpecCarriesRequiresCapability` still `2 failed, 3 passed` at HEAD (behaviour unchanged).
- Leg-B `scanned == 6` / `already_migrated == 0` first-call assert: present (in the 47-pass).

---

## §Q — QUANTIFIER TABLE (delta invariants)

| invariant | ∀-over-inputs or guarded? | receipt |
|---|---|---|
| **B2: drain serves ONLY the visible set** | guarded-by-the-invisible case + FOREIGN-subject control | **wrong build (resolve-subject-no-filter) RED** `assert 1 not in {0,1}`; control PASS (empirical) |
| B1: frozen capture is a faithful asserted world | ∀ over the 4 ASSERT literals (self-consistency) | GREEN on ref build; P0 mutation (drop `body` literal) → RED (empirical) |
| G1: bound EXACTLY once per served READ response | ∀ over the 5 named carriers (shared `_assert_bound_once`) | count-based (0/>1 both red); carrier reach hand-listed — see §R (structural) |
| G2: capability rollup serves the FILTERED count, bound heads the LEG | guarded-by-the-2-vs-3 + response-head cases | RED-at-HEAD via `_rollup` no-cap; correct-build by-construction (substring fragility — §Residuals) |
| F5: decode reached before the unstamped check | guarded-by-forced-decode + `decode_reached` positive control | by-construction (over-filtering build → RED); round-1 Finding 5 closed |
| **Dev-4: only a genuine WRITE receipt may omit the bound** | ∀ over derived set MINUS exemption; exemption honest BOTH directions | **stale RED + wrongly-exempted-read RED** (empirical, two mutations) |
| Dev-3: migrate refuses a junk grade for the ASSERT reason | guarded-by-the-junk-grade case; typed+match | `3 passed` at HEAD; type+match discriminates all 4 wrong-reason cases incl. the conflict SUBCLASS (empirical + hierarchy) |
| P2-m / Leg A / Leg B / R6 / P7 (round-1 confirmed-sound) | (not re-graded — round-1 §Q) | round-1 report; re-confirmed 0-failed in the 47-pass |

## §R — REACH TABLE (delta guards)

| guard | reach DERIVED vs hand-list | coverage a checked variable? | effect vs proxy | verdict |
|---|---|---|---|---|
| **Dev-4 render coverage** (`_governed_read_render_methods` − exemption) | DERIVED (subject-resolving handlers' `_render_*`, receivers self/cls/AppContext) | YES — floor reds if a render is undiscovered OR wrongly exempted; exemption non-vacuous BOTH directions | AST presence + from-truth write-seam on the SAFE side | **SAFE (empirical: 2 mutations red; `_render_comms_send` now derived — Finding 6 closed)** |
| Dev-4 exemption set `{_render_comms_send}` | hand-list, but ALLOWLIST-THE-SAFE with non-vacuity both directions | YES (stale reds; wrongly-exempted-read reds) | from-truth (handler write-seam) | SAFE (empirical) |
| §9.3 ⊇ floor (6 named ii-b renders) | hand-list of 6 (a ⊇ non-vacuity floor, NOT the coverage set) | YES (⊇ — a 7th joins coverage w/o edit) | AST presence | SAFE (§9.3-ruled; coverage, not the floor, is the reach) |
| G1 once-count carrier set | **hand-list of 5 verbs** (drain/await×2/story/ack) | NO — a future row-bearing read verb needs its own once-count | count of `_BOUND_MARKER` | bounded (round-1 Finding 3 set closed; §Residuals) |
| MP-7 corpse sweep | DERIVED (patterns: literals + constant-names + field-statement calls) | YES — every hit individually verdicted | text presence | SAFE (wider than reviser's; empirical) |
| B2 read-filter (drain SELECT) | (production guard, unbuilt) — `governed.read_filter` is THE one splice | (cold audit backstop) | effect (served set) | discrimination SAFE (empirical wrong build); correct-build by-construction |

---

## §Residuals — individual verdicts (flags, NONE blocking)

1. **B2 subject-owns-agent (correct-build caveat).** The B2 CONTROL drains `recipient_bare`'s inbox as a
   `foreign_subject` (a principal that does NOT own that agent). If the ii-b design gates `drain` on
   subject-OWNS-agent (not only read_filter visibility), the control's correct-build leg would RED for an
   ownership-denial reason rather than serving the invisible message — a false RED on the correct build.
   The main pin is unaffected (drained as the owning subject). **Verdict:** verify drain governs by
   read_filter VISIBILITY, not agent-ownership, or adjust the control's correct-build expectation.
   Relay to builder + cold audit.
2. **G2 substring count fragility.** `assert "2" in activity_line and "3" not in activity_line` catches the
   named unfiltered-count wrong build (line reads `messages activity (3)`), but a substring check is
   fragile to spurious digits. **Verdict:** functional for this fixture (seq 999, no stray 2/3 in the leg
   line); a `re.search(r"messages activity \((\d+)\)")` int-equality would be stronger. Nit, not a gap.
3. **G2 `_rollup(capability=)` interface (DN2).** The pin assumes the correct build exposes
   `AppContext._rollup(…, capability=)` (grounded in the tokenless leg's own `pass capability=` teaching).
   If the builder resolves rollup capability another way, G2 RED-on-correct-build. **Verdict:** same class
   as the drain/ack `subject=` seams — a correct-build interface assumption; flag in the builder brief.
4. **G1 hand-listed carrier set.** The once-count covers the 5 verbs §9.1/the sidecar name; a FUTURE
   row-bearing read verb (a `mark-read`, a view-recording story) would need its own once-count pin — the
   reach is not a checked variable. **Verdict:** not a current-wave defect (round-1 Finding 3's named set
   is delivered); bounded reach, re-open trigger = a new row-bearing governed read verb.

---

## Probe record (commands + real output)

### Scratch / provenance
`./scripts/scratch_copy.sh /tmp/…/scratchpad/ref_build` → provenance-asserted. `loremaster.__file__ =
/tmp/…/scratchpad/ref_build/loremaster/loremaster/__init__.py` (inside scratch). Ruled DDL-drop applied to
`surreal_schema.py` `_MESSAGE_FIELD_SPECS`/`_TO_FIELD_SPECS`. Test store `ws://127.0.0.1:18000` (never :18500). No worktree.

### B1
- ref build: `test_the_frozen_old_world_is_a_faithful_asserted_capture` → `1 passed in 1.76s`.
- P0 mutation (scratch `_governed_contract.py` frozen `body` → no ASSERT): `1 failed` —
  `AssertionError: … MISSING 'ASSERT string::len($value) <= 4000'`. Restored.

### Satisfiability
migrate file + 4 schema classes on ref build → `47 passed in 42.20s`, 0 failed.

### B2
partial-fix wrong build (`drain(…, subject: object = None)` ignored) → `TestADrainServesOnlyTheVisibleMessage`
`1 failed, 1 passed`: main pin RED `served=[0,1] … assert 1 not in {0,1}`; foreign-subject control PASS. Restored.

### D1 / RED-honesty
full read-gov file at HEAD → `12 failed in 23.98s`, 0 passed; reasons: `MessageLedger.{drain,ack}() got an
unexpected keyword argument 'subject'`, `… the <verb> verb does not accept a 'capability' param yet
('capability' applies only to action='send')`, `AppContext._rollup() got an unexpected keyword argument
'capability'`. No `no session keep` / `GovernedDenied` in output.

### Dev-4 (two mutations, scratch)
- exempt fake `_render_ghost_that_is_not_derived` → non-vacuity `1 failed` (STALE).
- exempt `_render_recalled_memories` (real read) → non-vacuity `1 failed` (`handler AppContext.recall
  contains NO WRITE-family seam`). Restored.
- derived set at HEAD: `{_render_comms_send, _render_recalled_memories}`; `_render_comms_send in derived = True`.

### Dev-3
P-G3 + Leg-B C-CONTROL + legal-grade control at HEAD → `3 passed in 2.24s`; `governed.message_backfill.rejected`
ERROR log confirms the driver's wrapped raise. `TxnGovernedConflictError` subclasses `TxnDomainRejectionError`
(`_txn.py:189`) — the `(assert violation)` match carries the conflict discrimination.

### G1 / MP-7 / nits
- `_assert_bound_once` def 345, called by 5 carriers (435/472/519/560/601); `_rendered_read_or_red_at_head`
  by 5 (432/468/515/554/597).
- MP-7 anchor-free `awk` (literals + constant-names + field-statement): only `agent.status`/`message.grade`
  demand an ASSERT (both KEPT); no message-field corpse. Cross-file: 3 prose/docstring hits only.
- `_REQUIRED_IN_II_B_NOT_YET` → `_READS_REQUIRED_IN_II_B` fully renamed; capability pin `2 failed, 3 passed`.
  Grade dup-name resolved (schema 1721 vs ledger 347).

## Discipline / deviations (brief-base §1/§3/§4)
- grep/rg HOOK-BLOCKED on this live-indexed checkout — every textual sweep is `awk` over an explicit file
  list, said out loud. lore (`lore_get_symbol`/`lore_search`/`lore_read`) for structure. No lore friction to file.
- Read-governance CORRECT-build reference NOT undertaken (as round 1; ~the builder wave, out of adversary
  budget) — its satisfiability is the cold audit's job; the DISCRIMINATION (wrong-build) direction WAS
  built for B2 and Dev-4. Legs said per role (§"What I re-graded").
- No production/contract file edited in the repo; all probes in the scratch copy, discarded.
