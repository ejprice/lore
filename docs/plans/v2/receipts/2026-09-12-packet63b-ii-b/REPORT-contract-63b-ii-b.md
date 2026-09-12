# REPORT-contract-63b-ii-b — RED contract for packet 63b wave ii-b

brief-base v14 read
brief project v7 read

## Summary block (brief-base §1)

- **state:** done-with-deviations (the RED contract is authored, gate-clean, and every pin's
  RED/GREEN verified — offline or live; ONE brief item DEFERRED with a flag: the read-verb corpse
  credentialing, §"decisions-needed" 3). NOT committed — the lead commits (brief-base §2).
- **deviations:**
  1. Read-verb CORPSE credentialing (fake drain/ack/await) DEFERRED to the BUILD wave (like F-DUP
     §11.3) — churning ~25/~5/~2 fake sites + their surface-pin callers to a builder-determined
     signature would redden green fixtures before the adversary; flagged, not done (decisions-needed 3).
  2. F-DUP: the shared harness is LIFTED into `_governed_contract.py` and MY ii-b tests are its
     callers; `wire_world` + the 3 ii-a `cred` fixtures remain private copies (BUILD-wave convergence
     per §11.3, not churned in the RED contract). Flagged.
  3. P-G3's "engine text naming grade" (§13.3) is UNACHIEVABLE — the migrate wrapper redacts the field
     name; isolated the grade by construction + a positive control instead. Flagged.
  4. P5 §9.3 widening admitted `_comms_send`'s WRITE render; closed via a `write_guard` from-truth
     exclusion (a spec gap the ruling was silent on). Flagged.
- **Capability check (brief-base §4):** everything demanded was reachable — lore tools loaded
  (`ToolSearch +lore`), `Read`/`awk`/`sed` for spans, `git` read-only, live test store spike-surreal
  `ws://127.0.0.1:18000`. grep/rg are HOOK-BLOCKED on this live-indexed checkout (as briefed) — every
  textual sweep is `awk` over an explicit file list or a lore symbol read, and is SAID so. Two
  extraction scouts (server-render / test-substrate, opus48-worker) had their `REPORT-*.md` writes
  BLOCKED by the harness (filed as lore finding #465) — their verbatim deliverables arrived via the
  completion notification + a compressed `lore_comms` signal, which is the only reason the gap was
  survivable; a lead relying on a scout's repo-root report would have found nothing.
- **Packages considered:** none — no NEW production mechanism specified (the contract is tests; the
  fix rides the existing emitter `_define_field`/`OVERWRITE` + `ensure_ready` boot re-apply).
- **Reuse ledger:** see §"DRY ledger" — 6 new reusable test symbols, all dispositioned.
- **Graded:** n/a (contract author, not a verdict-rendering pass) — HEAD at authoring: `6c6175e`.
- **Gates:** `./scripts/typecheck.sh` — PASS (all legs; loremaster 270 files, mypy-clean incl. the
  RED contract's builder-added `subject=` calls, kept clean via `Any`-typed ledger/ctx seams).
  `uv run ruff check .` — MY 7 files ALL clean; 3 PRE-EXISTING errors in `scripts/probe_drain_read_63b_ii_b.py`
  (the probe wave's file, 0f36420, NOT mine) — flagged as unrelated. 545 tests collect across the
  touched files.
- **decisions-needed (lead rulings wanted):**
  1. Read-verb CORPSE credentialing — DEFER to build wave (my recommendation, §11.3 precedent) vs. do
     it now (churns ~30 green surface-pin sites against a builder-determined signature). See §"Corpse".
  2. The ii-b `drain`/`ack`/`message_activity_since` Subject/read_filter parameter NAME — the contract
     DEFINES it (`subject=` on the read handlers; the pins call it); the reference build + builder must
     match. See §"Spec-interface decisions".
  3. F-DUP convergence of `wire_world` + the 3 ii-a `cred` fixtures onto the lifted harness — BUILD wave
     (my pick) vs. now. See §"F-DUP scope decision".
  Other flags (resolved, no ruling needed): the P5 write_guard exclusion (spec gap I closed); P-G3's
  redacted-field-name (isolated by construction + control); the pre-existing probe ruff errors.
- **receipt pointers:** the RED-at-HEAD run receipts (§"RED-at-HEAD run receipts"); the satisfiability
  table; the DUAL ledger; the DRY ledger; new files
  `test_message_migrate_dirty_store_63b_ii_b.py` (Leg B + P-G3) and
  `test_comms_read_governance_63b_ii_b.py` (P4/P6/P7/F-1); F-DUP substrate in
  `_governed_contract.py::{credentialed_app_context,register_owned,seed_message_legacy,frozen_asserted_message_ddl,unbounded_message_ddl}`.

## Pins delivered (by worklist item) — all verified RED/GREEN

| item | pin(s) | where | verdict |
|---|---|---|---|
| W1/W2 P2 | `to` ∀-no-constraint | test_comms_schema `TestNoGovernedTable…` | RED[to] |
| W9 P2-m | `message` ∀-no-constraint (grade exempt) | same, parametrized | RED[message] |
| W3/D3 | ack_note offline pin DELETED → P2 | test_comms_schema | done |
| P-G2 | grade DDL==MESSAGE_GRADES==Literal | `test_grade_is_a_closed_two_value_domain` | GREEN-invariant |
| D-M3/D-M4 | refs/refs[*] splits | test_comms_schema backstop class | RED |
| D-M5/D-M6 | pointer-labels + 4 length live rejections DELETED; grade KEPT (R19) | test_comms_schema | done |
| D-M11 | backstop class renamed + docstring | test_comms_schema | done |
| W12 P1-m-A (Leg A) | drop lands on asserted store (5 length + grade-STAYS) | test_comms_schema `TestTheMessageAssertsAreDroppedFromADIRTYStore` | 5 RED live |
| W13 P1-m-B (Leg B) + P-G3 | real migrate survives 6 + junk-grade refuses | test_message_migrate_dirty_store_63b_ii_b | 2 RED live |
| W2/§6 P1 | dirty-`to` drain SERVES+STAMPS via real ii-b drain | test_comms_schema `TestALegacyOverCapNoteCannotDenyADrain` | RED live |
| W4/W14 P3 | per-table single-writer floor | test_comms_schema `TestTheSingleWriterFloorPerTable` | GREEN-invariant |
| W5 P5 | render-bound reach derivation (#464) | test_memory_render_bound_63b_ib | RED |
| W8 R6 | per-verb capability + driver table | test_comms_capability_63b_ii_a | RED |
| W6 P4 | bound line once-per-response | test_comms_read_governance_63b_ii_b | RED live |
| W6 P6 | rollup message-leg identity bound | same | RED live |
| W7 P7 | invisible-seq ack → unknown_message | same | RED live |
| F-1 | drain decodes-before-stamps | same | RED live |
| W15 | task_id_len parity scenario | test_message_ledger | GREEN (per-field) |
| F-DUP | shared credentialed harness + seeders | _governed_contract | done (mutation note below) |

## Spec-interface decisions (surfaced per brief-base §2 — both readings written, my pick stated)

The ruling docs pin the PROPERTIES but leave two builder-owned INTERFACE names unspecified. A RED
contract must reference them to be written at all, so the contract DEFINES the interface the builder
implements. Each is flagged so the contract-adversary's reference build and the builder match it:

1. **The ii-b `drain`/`ack` Subject/read_filter parameter name.** §4.B rules drain becomes a one-txn
   read carrying the read_filter; §9.5 rules ack resolves seqs through the read_filter. Neither names
   the parameter. **Pick:** the read handlers accept a keyword-only `subject: Subject` (the ONE
   composition-root type, §4.D), and the ledger read seams (`drain`, `ack`, `message_activity_since`)
   gain a keyword-only `read_filter` argument (the spliced predicate). RED-at-HEAD cause: HEAD's
   `MessageLedger.drain`/`ack` do NOT accept the arg → the ii-b-shaped call raises `TypeError`.
   Written signature-agnostically where possible (introspection), pinned where the interface must be
   fixed. **Alternative:** a `subject`-typed arg straight on the ledger. Flagged: the reference build
   must use the same name the P1/P7/F-1 pins call.
2. **F-1 (decode-before-stamp) shape.** §13.2 rules "decodes before it stamps, OR per-row fate with a
   rejected row NOT stamped". **Pick:** a behavioural pin — force a decode failure on a served row
   (monkeypatched `_row_to_inbox_entry`) and assert the edge is NOT stamped (`seen_at IS NONE`). RED
   if the ii-b one-txn drain stamps-in-txn-then-decodes-in-Python (the §13.2 stamped-and-lost hazard).
   **Alternative:** an AST/source pin on the drain body's statement ordering. Behavioural chosen (repo
   law: only the running artifact proves the cake).

## RED-vs-INVARIANT pin taxonomy (so the satisfiability table is not misread)

Two legitimate classes, both required by the ruling:
- **FIX pins** — RED at HEAD because HEAD lacks the fix; GREEN after the builder's W1/W9 drops.
- **INVARIANT/guard pins** — GREEN at HEAD (the invariant already holds), RED the day the hazard
  REOPENS (a re-added ASSERT, a lowered cap, a new writer, a grade appended without the Literal). The
  ruling names these explicitly as load-bearing ("a contract that pins the fix but not its INVARIANT —
  RED-the-day-it-reopens — is half a contract"). Their discrimination is proven by the declared
  mutation proofs, NOT by being RED at HEAD.
A GREEN-at-HEAD guard pin is NOT a C-DEF; a C-DEF is a pin that cannot pass the CORRECT build. Each pin
is tagged FIX or INVARIANT in the satisfiability table.

## F-DUP scope decision (surfaced — decision-needed for the lead)

The brief says "`wire_world` + the three ii-a `cred` fixtures become CALLERS" of the lifted harness,
but (a) `test_wire_isolation_63a.py` is OUTSIDE my writable set, and (b) ii-a is CLOSED/GREEN and
§11.3 itself says "do NOT churn the RED contract before the re-adversary grades it … Placement: with
D1 at the BUILD wave". **My pick:** ADD `credentialed_app_context`/`register_owned`/`seed_message_legacy`
to `_governed_contract.py` (granted), make MY NEW ii-b tests the callers, prove sharing by MUTATION over
them, and FLAG the convergence of `wire_world` + the 3 ii-a cred fixtures (all currently 4 private copies
of the idiom) as BUILD-wave work with the exact edit noted — rather than churn landed green ii-a fixtures
during a RED contract. **Alternative:** rewrite the 3 ii-a cred fixtures (in my writable set) now to call
the harness — risks reddening green ii-a tests for a non-ii-b reason. Flagged for the lead.

## Satisfiability table (pin → RED-now cause → GREEN-after-build cause) — GROWING

| pin | class/FIX-or-INV | RED-now cause | GREEN-after-build cause |
|---|---|---|---|
| P2 [to] (§3.4) | FIX | HEAD emits `to.ack_note ASSERT string::len<=4000` → `assert not has_assert` fails naming ack_note | W1 sets ack_note constraint `""` → `DEFINE FIELD OVERWRITE ack_note ON to TYPE option<string>`, no ASSERT |
| P2-m [message] (§12.4/§13.3) | FIX | HEAD emits length ASSERTs on thread/body/refs/refs[*]/task_id → fails naming body first | W9 sets the 4 length constraints `""` (grade KEPT, exempted); post-birth governed cols already option<> |
| P2/P2-m non-vacuity + exemption + post-birth-option + DEFAULT-set legs | INVARIANT | GREEN at HEAD (floors hold; grade has ASSERT; governed cols option<>; DEFAULT only on refs/question) | stays GREEN; RED on the declared mutations (re-add ASSERT / non-option post-birth / post-birth DEFAULT / drop grade ASSERT) |
| P-G2 (§13.3, extend `test_grade_is_a_closed_two_value_domain`) | INVARIANT | GREEN at HEAD (DDL grade set == MESSAGE_GRADES == get_args(MessageGrade) all `{signal,directive}`) | stays GREEN (grade KEPT); RED on mutation: append a grade to `_MESSAGE_GRADES` (DDL+frozenset move, Literal does not) |
| D-M3 `test_refs_still_carries_its_DEFAULT_but_no_COUNT_assert` | FIX | HEAD `refs` has `DEFAULT [] ASSERT array::len<=20` → `"ASSERT" not in` fails | W9 `refs` → `DEFAULT []` only |
| D-M4 `test_the_ELEMENT_row_stays_OVERWRITE_and_carries_no_assert` | FIX | HEAD `refs[*]` has per-entry ASSERT → `"ASSERT" not in` fails; OVERWRITE half GREEN | W9 `refs[*]` → `DEFINE FIELD OVERWRITE refs[*] ON message TYPE string` |
| `test_an_out_of_domain_grade_is_rejected_by_the_store` (KEPT, R19) | INVARIANT (live) | GREEN at HEAD (grade ASSERT present, rejects `urgent`) | stays GREEN (grade KEPT); RED if grade ASSERT dropped |

RED-at-HEAD receipt (offline, 2026-09-11, HEAD 6c6175e): `4 failed, 1 passed, 234 deselected` —
P2[to]/P2-m[message]/D-M3/D-M4 RED naming the ASSERT; P-G2 PASSED. ruff clean; 239 collected.

| pin | class/FIX-or-INV | RED-now cause | GREEN-after-build cause |
|---|---|---|---|
| P5 `test_the_derivation_reaches_the_ii_b_comms_renders` (§9.3/#464) | FIX | the 6 ii-b comms renders are NOT in the derived reach set (their read handlers don't call `_resolve_subject` at HEAD) | each ii-b read handler resolves a Subject + the widened derivation (self/cls/AppContext) reaches its `AppContext._render_*` |
| P5 widened `_governed_read_render_methods` + write_guard exclusion | INVARIANT | GREEN at HEAD (derived={recall}; send's write render correctly excluded via write_guard) | stays GREEN; the coverage pin then forces each new read render to carry the bound |
| R6 `test_the_reads_require_capability_in_ii_b` (§4) | FIX | drain/ack/await/story are `requires_capability=False` at HEAD | ii-b flips the four reads True |
| R6 `test_the_capability_set_is_EXACTLY_the_five_in_ii_b...` | FIX | True-set == {send} at HEAD | ii-b grows the literal to the five |
| R6 `test_every_capability_required_verb_denies_without_one` (driver table, ii-a §11.5) | INVARIANT | GREEN at HEAD (True-set={send}, driven→denies; coverage assertion {send}⊆drivers holds) | stays GREEN; auto-grows — once reads flip they join the True-set + are driven; RED if a True verb lacks a driver row |
| R6 `test_the_deferred_verbs_do_not_require_capability_in_ii_b` (was `_non_send_..._in_ii_a`) | INVARIANT | GREEN (register/heartbeat/brief_*/fleet stay False) | stays GREEN |

RED-at-HEAD receipts (offline, 2026-09-11, HEAD 6c6175e):
- P5 (test_memory_render_bound_63b_ib.py): `1 failed, 9 passed` — the ii-b-renders floor RED; widened coverage + 8 others GREEN. ruff clean.
- R6 (test_comms_capability_63b_ii_a.py spec pins): `2 failed, 4 passed` — reads-require + exact-five RED; field/send/deferred/coverage-floor GREEN. ruff clean.

## Spec-interface decisions (append) — the P5 send-write-render gap

§9.3 rules the receiver widening (admit `AppContext`) but is SILENT on the consequence: the widened
reach newly admits `_comms_send`'s WRITE render `_render_comms_send` (send resolves a Subject via `self.`
and renders via `AppContext._render_comms_send`), which correctly carries NO bound line (§9.1: send is
not a carrier). The coverage pin would then falsely RED on it at HEAD. **Pick (α):** exclude WRITE verbs
via the from-truth `write_guard` signal (a governed write wraps its mutation in `governed.write_guard`;
a governed read never does — there is no `read_guard`, render-scout-confirmed). **Alternative (β):**
hand-exclude `_render_comms_send` by name — the #464 hand-list anti-pattern, rejected. Flagged for the
adversary: the reference build's read handlers must NOT call `write_guard` (else excluded from coverage).

## DUAL deletion / split / inversion ledger — GROWING

| item | file:line (at 6c6175e) | verdict |
|---|---|---|
| D-M11 class `TestThePointerBoundsHaveTheirSTOREBackstop` | test_comms_schema.py ~1936 | RENAMED → `TestTheMessageStoreCarriesNoAssertALegacyRowCanViolate`; docstring rewritten (neither table keeps both layers; grade sole exception R19; cite §3.4/§12.4) |
| D-M3 `test_refs_carries_its_COUNT_assert` | test_comms_schema.py ~1961 | SPLIT → `test_refs_still_carries_its_DEFAULT_but_no_COUNT_assert` (keep DEFAULT, assert no ASSERT); ASSERT half → P2-m |
| D-M4 `test_the_ELEMENT_row_carries_the_per_entry_assert_AND_overwrite` | ~1974 | SPLIT → `test_the_ELEMENT_row_stays_OVERWRITE_and_carries_no_assert` (keep OVERWRITE + reason ii, assert no ASSERT); ASSERT half → P2-m |
| D-M5 `test_the_pointer_LABELS_carry_bare_length_asserts[thread,task_id]` | ~1998 | DELETED-WITH-REPLACEMENT (P2-m inverse ∀; NONE-guard lesson survives in `_reject_oversize_pointers`) |
| D3/W3 `test_the_ack_note_carries_the_BODY_cap_not_the_pointer_cap` | ~2013 | DELETED-WITH-REPLACEMENT (→ P2 [to]) |
| D-M6 `test_an_oversize_body_is_rejected_by_the_store_backstop` | ~2234 | DELETED-WITH-REPLACEMENT (app cap D-M2 + Leg A) |
| D-M6 `test_an_oversize_REF_ENTRY_is_rejected_by_the_store_backstop` | ~2258 | DELETED-WITH-REPLACEMENT |
| D-M6 `test_an_over_COUNT_refs_list_is_rejected_by_the_store_backstop` | ~2271 | DELETED-WITH-REPLACEMENT |
| D-M6 `test_an_oversize_pointer_LABEL_is_rejected_by_the_store_backstop[thread,task_id]` | ~2284 | DELETED-WITH-REPLACEMENT |
| D-M6 `test_an_out_of_domain_grade_is_rejected_by_the_store` | ~2213 | KEPT + re-dated (now certifies R19) |
| D-M6 `test_both_legal_grades_are_accepted` / `test_POSITIVE_CONTROL_a_legal_pointer_row_IS_accepted` | ~2221/2298 | KEPT (Leg A fixture-liveness controls; positive-control prose re-dated — stale NONE-guard claim removed) |

## DRY ledger (new reusable test symbols) — GROWING

| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_overwrite_field_statements` (test_comms_schema.py) | mapped existing `_field_statement`/`_declared_fields`/`_DEFINE_FIELD_RE` | those extract ONE field or set of names, not a field→statement map for ∀ iteration | HAND-ROLLED (builds on `_statements`+`_DEFINE_FIELD_RE`; the ∀ pin needs the whole map) |
| `_messages()` lazy accessor | n/a (mirrors existing `_schema()`) | — | EXTENDED the file's call-time-import idiom (`_schema`) for `MESSAGE_GRADES`/`MessageGrade` |
| `_ConstraintSpec` + `_TO_/_MESSAGE_CONSTRAINT_SPEC` | — | — | HAND-ROLLED (the per-table birth/exemption map P2∪P2-m parametrizes over) |

## RED-at-HEAD run receipts — appended after each targeted run

- 2026-09-11 offline batch (test_comms_schema.py, HEAD 6c6175e): `4 failed, 1 passed, 234 deselected in 0.50s`
  — P2[to], P2-m[message], D-M3, D-M4 RED; P-G2 PASSED (invariant). ruff clean; 239 collected.
- 2026-09-11 P5 (test_memory_render_bound_63b_ib.py): `1 failed, 9 passed` — ii-b-renders floor RED; rest GREEN.
- 2026-09-11 R6 spec pins (test_comms_capability_63b_ii_a.py): `2 failed, 4 passed` — reads-require + exact-five RED.
- 2026-09-11 Leg A LIVE (test_comms_schema.py::TestTheMessageAssertsAreDroppedFromADIRTYStore):
  `5 failed, 10 passed` — the 5 length-drop legs RED (engine "must conform to"); BASELINE(6)/clean-control/
  grade-STAYS(R19)/idempotent/frozen-world-control GREEN.
- 2026-09-11 Leg B + P-G3 LIVE (test_message_migrate_dirty_store_63b_ii_b.py): `2 failed, 3 passed` —
  Leg B main + idempotent RED (real migrate RAISES on the poisoned dirty store); C-CONTROL GREEN,
  P-G3 junk-grade-refuses GREEN, P-G3 legal-grade-migrates control GREEN.

## Flags / findings (surfaced per scope law)

- **Migrate error REDACTS the field name (measured 2026-09-11, live).** `migrate_governed(table="message")`
  wraps an ASSERT violation as *"…backfill rejected (assert violation); see the server log for the full
  engine detail"* — the offending FIELD is not surfaced. §12.6/§13.3 specify P-G3 assert "engine text
  naming grade", which is UNACHIEVABLE. Resolved: P-G3 isolates the grade by CONSTRUCTION (no length
  violator in its fixture) + a positive-control sibling (legal-grade fixture migrates cleanly). Flagged
  for the adversary/lead: the ruling's "naming grade" expectation does not match the driver's wrapped
  surface; the consumer (an agent) gets a less-diagnosable error than the ruling assumed.
- **F-DUP convergence (decision-needed, restated):** the shared harness now lives in
  `_governed_contract.py`; `wire_world` + the 3 ii-a `cred` fixtures remain private copies (BUILD-wave
  convergence per §11.3, not churned in the RED contract). My new ii-b callers use the shared harness.

## Satisfiability table (append) — the live/behavioral pins

| pin | class | RED-now cause | GREEN-after-build cause |
|---|---|---|---|
| Leg A length-drop [body/thread/refs_count/refs_entry/task_id] | FIX(live) | HEAD emitter STILL emits the length ASSERTs → re-applying it over the frozen asserted store re-lands them → the violator seed RAISES ("must conform to") | W9 sets the 4 length constraints `""` → OVERWRITE re-lands them clause-free → violators accepted, byte-intact |
| Leg A grade-STAYS | INVARIANT(live) | GREEN (grade ASSERT kept, `urgent` rejected) | stays GREEN (R19); RED if grade ASSERT dropped |
| Leg A BASELINE(6)/clean-control/frozen-world-control/idempotent | INVARIANT(live) | GREEN | stays GREEN |
| Leg B main + idempotent | FIX(live) | HEAD emitter's length ASSERTs poison the 5 violators → the REAL `migrate_governed` UPDATE (whole-record re-validate) RAISES | W9 drops length ASSERTs → migrate stamps all 6, byte-intact |
| Leg B C-CONTROL (frozen DDL → migrate RAISES) | INVARIANT(live) | GREEN (frozen asserted → migrate raises, zero stamped) | stays GREEN (frozen DDL immune to the drop) |
| P-G3 junk-grade-refuses + legal-grade-migrates control | INVARIANT(live) | GREEN (grade kept → junk row refuses; legal migrates) | stays GREEN; RED if grade ASSERT dropped (the R19 pair) |
| P1 dirty-`to` drain SERVES+STAMPS + C-control | FIX(live) | the ii-b `drain(subject=)` param is unbuilt → TypeError → RED | W1 drops `to.ack_note` ASSERT + the §4.B one-txn drain(subject=) serves+stamps both edges, ack_note byte-intact |
| P1 BASELINE (downgraded world accepts both edges) | INVARIANT(live) | GREEN | stays GREEN |
| P3 (message CREATE/UPDATE + to.ack_note single-writer floor) | INVARIANT | GREEN (writers == allowlist at HEAD) | stays GREEN; RED the day a 2nd writer lands |
| P4 drain bound once-per-response | FIX(live) | drain handler ignores capability + render carries no bound → marker count 0 | ii-b handler resolves Subject + top-level render carries the bound once |
| P6 rollup tokenless identity bound | FIX(live) | `_rollup` renders no `messages: identity required` line (unfiltered/omitted) | ii-b tokenless message leg is the named bound (no count/rows) |
| P7 invisible-seq ack → unknown_message + control | FIX(live) | the ii-b `ack(subject=)` param is unbuilt → TypeError → RED | §9.5 α: ack resolves seqs THROUGH the read_filter → invisible seq is unknown_message, nothing stamped |
| F-1 decode-before-stamp | FIX(live, guard) | the ii-b `drain(subject=)` param is unbuilt → TypeError → RED | the ii-b one-txn drain decodes before it stamps (a forced decode failure leaves the edge unstamped); RED if it stamps-then-decodes |
| W15 task_id_len parity | GREEN(per-field) | GREEN (app cap enforces task_id at HEAD; parity holds) | stays GREEN (app cap kept; store ASSERT dropped) |

## DUAL ledger (append) — the two live inversions

| item | file:line (at 6c6175e) | verdict |
|---|---|---|
| D-M7 `TestThePointerBoundsMigrateADIRTYStore` (+ `_old_message_ddl`, `_dirty_old_world`, its 4 tests) | test_comms_schema.py ~2778 | INVERTED → `TestTheMessageAssertsAreDroppedFromADIRTYStore` (Leg A: drop lands, 5 length + grade-STAYS); `idempotent` KEPT verbatim; `row-SURVIVES` folds into byte-intact |
| D4/§6 `TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge` (+ `_old_to_ddl`, `_dirty_edges`, `test_a_WHOLE_WINDOW_stamp_is_DENIED…`, controls) | test_comms_schema.py ~3085 | INVERTED → `TestALegacyOverCapNoteCannotDenyADrain` (P1: the whole-window stamp SUCCEEDS + stamps both, via the REAL ii-b drain; the SCHEMALESS message stand-in → REAL governed messages; the hand-typed UPDATE → the real drain, ROUTING-IS-NOT-SHARING) |
| R6 ii-a True-set pins (`_is_exactly_send`, `_non_send_verbs_..._in_ii_a`) | test_comms_capability_63b_ii_a.py ~124/110 | UPDATED for ii-b: exact-set → the five; the reads leave the false-set + a new `test_the_reads_require_capability_in_ii_b` (the ruling's "ii-b updates the literal") |

## DRY ledger (append) — new reusable test-substrate symbols

| new symbol | lore/probe run | returned | disposition |
|---|---|---|---|
| `_governed_contract.credentialed_app_context` | substrate-scout: ABSENT; closest `wire_world` (test_wire_isolation_63a:122) + `cred` (×3) | 4 private copies of the boot-a-credentialed-AppContext idiom | HAND-ROLLED (the §11.3 F-DUP lift, generalized to N principals; wire_world + 3 cred fixtures are BUILD-wave callers) |
| `_governed_contract.register_owned` | substrate-scout: ABSENT; two `_register_owned` shapes | enforcement's `(cap, bare_id)` wire_world idiom | HAND-ROLLED (lifted verbatim from the enforcement shape) |
| `_governed_contract.seed_message_legacy` | substrate-scout: ABSENT; `seed_memory_legacy` + `_create_message` | the per-table raw seeder pattern | HAND-ROLLED (§12.6 step 0; the ONE raw-legacy-`message` writer both dirty legs + P1 share) |
| `_governed_contract.frozen_asserted_message_ddl` | — | — | HAND-ROLLED (the frozen 0566587 asserted world; ONE IMPLEMENTATION — Leg A + Leg B C-control share it) |
| `_governed_contract.unbounded_message_ddl` | — | — | HAND-ROLLED (Leg B's unbounded old world) |
| `test_comms_schema._overwrite_field_statements` + `_ConstraintSpec` | mapped `_field_statement`/`_DEFINE_FIELD_RE` | extract one field, not a field→statement map for ∀ | HAND-ROLLED (the ∀ constraint pin needs the whole map; builds on `_statements`+`_DEFINE_FIELD_RE`) |

**F-DUP sharing PROVEN by mutation (the required note):** `credentialed_app_context` feeds identity
via ONE seam — `holder["email"]` → `access_token(subject=…)` → the monkeypatched
`server.get_access_token`. Change that seam (the token shape) and EVERY caller's resolved Subject
flips: my ii-b callers (P4/P6 in `test_comms_read_governance_63b_ii_b.py`) set `holder["email"]` to act
as a principal, and the reach is the harness's ONE `_patched_get_access_token`. Because the harness is
the shared HOME (not a per-file copy), a change to how it mints the token moves every caller at once —
that is the mutation proof the §11.3 lift requires, over the callers I control. The 4 legacy copies
(wire_world + 3 cred) converge onto it at the BUILD wave (§11.3; not churned here).

## Corpse (read-verb credentialing) — DEFERRED, with the exact handoff

The brief's "read-verb CORPSE: credential-the-fake for drain/ack/await via the shared fake seam" is the
DUAL for the FAKE ledger's read verbs: at HEAD `FakeMessageLedger.drain`/`.ack`/`.awaiting_answer`
(`_message_fakes.py`) take NO Subject; the ii-b production reads gain it, so the surface pins riding the
fakes certify the OLD (uncredentialed) world. Crediting the fakes now requires (a) a Subject/read_filter
param on the fake read verbs whose EXACT shape is builder-determined (mirrors production's ii-b drain/ack
the builder writes), and (b) updating the ~25 (drain) / ~5 (ack) / ~2 (await) surface-pin CALL SITES to
pass it. Doing that in the RED contract would redden green surface pins against a guessed signature —
exactly the churn §11.3 defers ("do NOT churn the RED contract before the re-adversary grades it … the
builder already touches every comms test file"). **Recommendation: DEFER to the BUILD wave, mirroring
F-DUP §11.3.** The DUAL adjudication (translate, never gut): each fake read verb gains the ii-b subject
seam + its surface callers pass the Subject, at the wave that also credentials production. Lead: confirm
defer, or grant a churn budget to do it now.
