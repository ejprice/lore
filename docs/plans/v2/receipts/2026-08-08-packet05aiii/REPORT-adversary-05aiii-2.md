# REPORT-adversary-05aiii-2 — CONTRACT ADVERSARY re-grade, packet 05a-iii

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **VERDICT: CONTRACT SUFFICIENT — conditional on ONE one-line fixture fix (the A2
  creator/sender monoculture), the SOLE surviving residual.** Per the lead's pre-ruled
  path ("all 7 hold + no regression + its one-line fix is the only residual → SUFFICIENT,
  name the residual, close without a third full pass"). The residual IS a real missing
  pin — named below with its wrong-build receipt + the exact one-liner — NOT waved away.
- **P1 headline — did any wrong build survive the FIXED contract? ONE, narrowly:** a story
  build that renders the message SENDER but NEVER `created_by` passes A2 **and the whole
  story file (19/19)** — the A2 "creator" needle is a fixture-value monoculture
  (`created_by="lead"` == the message sender name "lead"). Every OTHER wrong build I
  rebuilt is now caught (F1–F7 all hold).
- **All 7 prior findings VERIFIED HOLDING, each door independently rebuilt & reddened:**
  F1 (A2 behavioural, not setup-crash) · F2 (per-field ∀ containment + coverage partition)
  · F3/F4 (runtime full-DB catches create/insert/merge; AST scan; constant scan stays
  blind) · F5 (3 counts scenarios) · F6 (D8 timing-independent unknown leg) · F7 (clone
  reddens only the mutation pin). Table §Door-rebuild.
- **NO REGRESSION:** fix touched ONLY the 3 test files; D9a/D9b, D5/D6, A4b, A3, A5 method
  DEFs are ABSENT from the diff (untouched → cannot regress) and green on correct builds;
  D6 reddens on blindstamp, D8 on fabzero. B4/#302/property-keying live in UNTOUCHED files.
- **SATISFIABILITY (the receipt that was FALSE last pass) RESTORED:** each leg's file goes
  0-failed on a correct build — story **19 passed**, age **8 passed**, CLI **13 passed**
  (= 40, the whole contract). Contract is ruff-clean (post-lint leg). §Satisfiability.
- **The one required fix (REQUIRED before build):** A2 fixture — change `created_by="lead"`
  → a creator that is NOT any message sender (e.g. `"planner"`) and the `"lead"` needle →
  `"planner"`. Then a sender-not-creator build reddens A2. §A2.
- **Packages considered:** none — test contract, no NEW mechanism (all seams reused
  in-house); F7 now mutation-pins the `SurrealConfig` `keep_with_trigger` reuse. §P-PKG.
- **Graded:** `dc54bbd` · HEAD-at-report `dc54bbd` · **SAME**. All builds in a
  provenance-verified `scratch_copy.sh` tree; `loremaster.__file__` =
  `/home/ejprice/scratch/adv05aiii2/loremaster/loremaster/__init__.py` (printed each leg).
  Store spike-surreal `:18000` ONLY; `:18500` never touched.
- **Receipt pointers:** door-rebuild table §Door-rebuild · quantifier table §P1b · the one
  missing pin §A2 · satisfiability §Satisfiability · full probe record §PROBES.

---

## The one missing pin (the sole residual)

| The test that should exist | The defect it catches | Sev |
|---|---|---|
| A2 (`test_story_renders_subject_creator_owner_messages_and_report_path`): make the task's `created_by` a value that is **not** any message sender (e.g. `create_task(..., created_by="planner")`) and assert `"planner"` in the render (in place of the `"lead"` needle). | A story build that renders the message **sender** but never the task's `created_by` passes A2 and the entire story file — the "creator" leg is unpinned. The QUANTIFIER-LAW monoculture: the invariant ("story renders the creator") is asserted on the one fixture value where creator == sender. | one-line residual (lead-closeable) |

Empirically confirmed (§A2): a `no_created_by` build (renders `sender_name` in the message
line, omits `created_by` entirely) → **A2 alone: 1 passed; whole story file: 19 passed.**
Nothing in the contract forces `created_by` to be rendered. The fix author already flagged
this as decisions-needed (REPORT-contract-fix-05aiii §Observation); this pass confirms it
empirically and gives the one-line fix. It is a genuine missing pin AND a one-line fixture
fix — the lead applies it and closes; **no third full adversary pass is warranted.**

---

## Door-rebuild — every prior finding re-attacked, pin reddens (independent rebuild)

Every row below: I built the exact wrong build in scratch and watched the pin(s) redden;
a correct/reference build greens. Commands + output in §PROBES.

| # | Wrong build I rebuilt | Pin(s) that reddened | Constant/old scan | Verdict |
|---|---|---|---|---|
| **F1** | untouched stub | A2 fails **behaviourally** (`'reticulate the splines' missing`), NOT `IllegalTransitionError` at setup; greens on correct build | — | **HOLDS** — satisfiability receipt restored |
| **F2** | `leak_description` (fences body, raw-renders description) | `[story.description]` param **+** `..._contained_end_to_end` (2 failed) | — | **HOLDS** |
| **F2** | `leak_done_summary` (fences description, raw-renders done_summary) | **only** `[story.done_summary]` (1 failed) | — | **HOLDS** — per-field, kills the "fences one field not another" monoculture |
| **F2** | `leak_ref` (raw-renders a message ref) | **only** `[message.refs]` (1 failed) | — | **HOLDS** |
| **F2** | add unclassified field `adversary_probe_note` to `CommsStory` | coverage partition RED (`unclassified={('story','adversary_probe_note')}`) | — | **HOLDS** — new free-text field cannot ship unfenced |
| **F3/F4** | `wb_create` (`conn.create("cli_audit",…)`, new table) | `read_only_full_db` RED + `no_typed_write_method` (AST) RED | `no_write_verb` **GREEN** (the F3 blindness) | **HOLDS** |
| **F3/F4** | `wb_othertable` (`conn.insert("hook_probe",…)`, new table) | `read_only_full_db` RED + AST RED | constant **GREEN** | **HOLDS** |
| **F3/F4** | `wb_merge` (`conn.merge` on existing `last_note` — **content UPDATE, no count change**) | `read_only_full_db` RED (content diff) + AST RED | constant **GREEN** | **HOLDS** — the count-invariant-evading case caught |
| **F5** | `hardcode` (`print("unread=1 unacked=1 skew=0")`) | counts scenario **B** (0/0/0) + **C** (2/2/1) RED | — | **HOLDS** — non-monoculture |
| **F6** | `fabzero` (NONE→"declared 0s") | D8 RED; the unknown-token leg catches it **timing-independently** (proven where `!= fresh` false-clears) | — | **HOLDS** |
| **F7** | `clone` (`yaml.safe_load` + `surreal["database"]`) | **only** `..._routes_through_the_shared_surrealconfig` RED | C-default + C-anthropic **GREEN** | **HOLDS** |

Correct/reference builds green their whole legs (§Satisfiability). No door I could build
survives the fixed contract — except the A2 creator/sender monoculture above.

---

## P1b — QUANTIFIER TABLE (every invariant classified; guarded rows carry a receipt)

| Invariant (pin) | ∀-over-inputs vs GUARDED | Receipt |
|---|---|---|
| story containment ∀ free text (A5 + `TestStoryFencesEveryFreeTextField`) | **∀-over-fields** (was the F2 BLOCKER; now 11 params + coverage partition + desc e2e) | `leak_description`→desc param+e2e RED; `leak_done_summary`→only done_summary RED; `leak_ref`→only refs RED; add-field→coverage RED |
| story arc: subject / owner / messages / report_path (A2) | ∀ — each forced by the fixture and by a distinct value | ref greens; stub reds behaviourally on each needle |
| **story arc: CREATOR (A2)** | **GUARDED** — `created_by` == the message sender name in the fixture | **THE ONE HOLE**: `no_created_by` build renders sender, omits created_by → A2 + whole file GREEN (§A2). One-line fix names it. |
| story question marker (A3) | ∀ over {question, signal} — both fates forced (q_task, s_task) | ref greens; marker structural from `message.question` |
| story scope (A4b) | ∀-over-tasks (global `WHERE task_id`) | method untouched by fix; green on ref; prior scope-blind→A4b RED |
| #304 write-on-change / no-restamp (D5/D6) | ∀ over {change, no-change} — both forced | `blindstamp`→D6 RED; correct write-side→8 passed |
| #304 age render / NONE honesty (D7/D8) | **∀** (was GUARDED by timing; F6 adds the timing-independent unknown-token leg) | `fabzero`→D8 RED; slow-render case: `!= fresh` PASSES but F6 leg CATCHES |
| #304 stored-status vocabulary pair (D9a/D9b) | ∀ over {active+question, input_required+no-question} — both forced | methods untouched; green on ref; prior conflate→both RED |
| #304 no-poison (D10) | ∀ (any field-less row); schema-guarded by D4 `option<datetime>` | green on ref |
| comms_cli read-only (C-readonly-runtime + AST source) | **∀ over all-tables × {create,insert,content-merge}** (was GUARDED by 3-table row-COUNT; F3/F4 → full-DB content snapshot + AST call-scan) | `wb_create`/`wb_othertable`/`wb_merge`→full-DB+AST RED; constant scan blind (GREEN) |
| comms_cli counts (C-counts) | **∀ over 3 scenarios** 1/1/0, 0/0/0, 2/2/1 (was GUARDED by one fixture; F5) | `hardcode`→B & C RED; correct→all 3 green incl. scenario C skew=1 real |
| comms_cli resolution + ONE-IMPLEMENTATION (C-default / C-anthropic / F7) | ∀ over {key-set, key-unset} + shared-vs-clone (F7 mutation pin) | `clone`→only F7 RED; correct→3 green |
| rollup sections + cursor (B1/B2/B3/B4) | ∀ over {pre-cursor, post-cursor} for B4 | UNTOUCHED file; prior-adversary-confirmed at 657a117 |

Every invariant is now ∀-over-inputs **except the A2 creator leg** (the one guarded row,
receipt attached). The three findings that were GUARDED last pass (F2 body-only, F3/F4
3-table count, F5 single fixture) are now ∀.

---

## P-PKG — package survey (independently built, diffed vs the author's "none")

Test contract; specifies no NEW mechanism. Independent survey agrees with the author's
`Packages considered: none`. The mechanisms the contract PINS are all shipped in-house
seams it REUSES:

| Mechanism the contract touches | in-house seam reused | verdict | what I READ |
|---|---|---|---|
| multi-line free-text containment | `render_attributed` / `render_fenced` (render.py) | `keep_with_trigger` | read both signatures + bodies (render.py:230-287) — `render_attributed` collapses newlines via `sanitise_line` into an inline delimiter; `render_fenced` wraps verbatim in a width-sized fence. **F2 is exactly the "new field a render reaches" trigger — now pinned ∀-field.** |
| pending-traffic counts | `MessageLedger.pending_traffic` | `keep_with_trigger` | read messages.py:1012-1055 — whole-inbox counts, not a window; the correct CLI reuses it (no re-derivation) |
| CLI store-coordinate resolution | `LoreConfig.effective_surreal_database` / `SurrealConfig` | `keep_with_trigger` | read the F7 pin + comms_cli docstring — F7 now MUTATION-pins the reuse (monkeypatch the property → only a routing build follows); the clone door reddens |
| full-DB read-only snapshot | `INFO FOR DB` + `SELECT *` (store) | `bespoke`(test-only) | read the F3/F4 pin — the snapshot is test-only assertion scaffolding, not production; verified it detects new tables AND content-only diffs |

Diff vs the author's line: **no disagreement.** No mechanism the contract specifies is a
library hand-roll. The one prior ONE-IMPLEMENTATION gap (F7 reuse unpinned) is now closed
by the mutation pin.

---

## A2 — the one surviving hole (creator/sender monoculture)

A2's fixture: `create_task("reticulate the splines", "the long description",
created_by="lead")`, then `send(sender=lead, …)`. So `created_by == "lead"` **and** the
message sender name is `"lead"` — the SAME value. A2's `"lead"` needle (the "creator" leg)
is therefore satisfiable by rendering EITHER field.

Wrong build `no_created_by` (renders `render_attributed(sender_name)` in the message line;
`created_by` deliberately not rendered):
```
A2 alone (test_story_renders_subject_creator_owner_messages_and_report_path):  1 passed
whole story file (test_comms_story.py):                                        19 passed
```
Nothing forces `created_by` to be rendered. This is the same QUANTIFIER-LAW class the repo
has shipped repeatedly (PKT-28 monoculture: `name="project"` at every call site). It is a
**one-line fixture fix** (distinct creator value + needle), the fix author already surfaced
it, and it does not warrant a third full pass — hence the SUFFICIENT-with-named-residual
verdict the lead pre-authorized.

Bound noted (not a separate finding): F2's ∀-containment is proven at the RENDER level
(`_render_comms_story` called on a directly-constructed hostile `CommsStory`) plus
END-TO-END for `description` only. A build that raw-renders a NON-description field OUTSIDE
`_render_comms_story` (in the handler) is not caught for that field. This is the right
instrument (the #131 "test the render directly" lesson; `done_summary`/`report_path` are
write-validated single-line so only direct construction can prove the render fences them),
the WB-A door the contract targets leaks IN the render and IS caught, and a full 11-field
end-to-end battery would need hostile fixtures the write path rejects. Adequate as built.

---

## Satisfiability (the receipt that was FALSE last pass — A2 unsatisfiable)

Each leg's production surface built correctly; each leg's file goes **0-failed**. Legs
touch independent surfaces (story: `_comms_story`/`_render_comms_story`; age: `agents.touch`
write-side + `_render_comms_fleet_row`; cli: `comms_cli.main`/`_run_pending`/
`_resolve_coordinate`), so per-leg 0-failed + no cross-leg contradiction ⇒ whole contract
satisfiable. Reference builds are my OWN (independent of the author's patchers), assembled
from the shipped seams:

- **Story leg** (`probe.py story ref`) → `test_comms_story.py`: **19 passed** (F1's A2 now
  greens behaviourally; every F2 containment param + coverage + desc e2e green).
- **Age leg** (`probe.py touch correct` + `probe.py fleet ref`) →
  `test_comms_status_age.py`: **8 passed** (D4–D10 all green together; write-side stamps on
  change only, render ages input_required + honest unknown for NONE).
- **CLI leg** (`probe.py cli full` = correct read + shared-SurrealConfig resolver) →
  `test_comms_cli.py`: **13 passed** (all 3 counts scenarios incl. scenario C skew=1 real;
  read-only full-DB; typed-write scan; C-default; C-anthropic; F7).
- **Post-lint leg:** `ruff check` on all 3 files → **All checks passed** (no builder trap
  between lint and an un-editable pin).

Total 19 + 8 + 13 = 40 = the entire contract across the 3 files. The A2-unsatisfiable false
receipt from last pass is fixed; no other pin is RED-for-the-wrong-reason on a correct build.

---

## PROBES — full record (commands, real output, provenance)

All runs: scratch copy `/home/ejprice/scratch/adv05aiii2` (built via
`scripts/scratch_copy.sh`, provenance asserted; `loremaster.__file__` =
`/home/ejprice/scratch/adv05aiii2/loremaster/loremaster/__init__.py`, printed on the story,
age, and CLI legs). Store spike-surreal `:18000`; `:18500` never touched. Graded sha
`dc54bbd`. The probe harness `probe.py` is pasted verbatim at the end (brief-base §1 — a
measurement's instrument is a deliverable).

### Baseline (untouched stub) — RED count reproduces, all behavioural

```
$ pytest test_comms_story.py test_comms_status_age.py test_comms_cli.py -n auto -q
13 failed, 27 passed in 7.71s
# A2 fails BEHAVIOURALLY (F1), not at setup:
E  AssertionError: story must reconstruct the task arc; 'reticulate the splines' missing
   from: 'story: arc of task ```…``` (stub — lineage not yet reconstructed)'
```
All 13 are pytest `failed` (assertion), zero `error` (setup/collection) — the satisfiability
leg-1 receipt (every RED pin fails behaviourally) holds. The 13 = the author's claimed set.

### Story (F1 + F2 + A2)

```
$ probe.py story ref        ; pytest test_comms_story.py           -> 19 passed   (satisfiability)
$ probe.py story leak_description ; pytest ...                     -> 2 failed, 17 passed
    FAILED ...TestStoryFencesEveryFreeTextField::...[story.description]
    FAILED ...::test_a_hostile_task_description_is_contained_end_to_end
$ probe.py story leak_done_summary ; pytest ...                    -> 1 failed, 18 passed
    FAILED ...[story.done_summary]                                 (per-field: fences desc, not done_summary)
$ probe.py story leak_ref ; pytest ...                             -> 1 failed, 18 passed
    FAILED ...[message.refs]
$ probe.py addfield commsstory ; pytest ...covers_every_free_text_field...
    AssertionError: ... unclassified={('story', 'adversary_probe_note')}; stale=frozenset()
    1 failed
$ probe.py story no_created_by ; pytest ...test_story_renders_subject_creator...  -> 1 passed   (THE HOLE)
$ probe.py story no_created_by ; pytest test_comms_story.py        -> 19 passed                 (THE HOLE)
```

### Age (#304: D5–D10, F6)

```
$ probe.py touch correct ; probe.py fleet ref ; pytest test_comms_status_age.py  -> 8 passed
$ probe.py fleet fabzero (touch correct) ; pytest ...             -> 1 failed, 7 passed
    FAILED ...TestFleetAgesTheDeclaration::test_none_status_set_at_renders_unknown_not_a_fabricated_zero  (D8)
$ probe.py fleet ref ; probe.py touch blindstamp ; pytest ...     -> 1 failed, 7 passed
    FAILED ...TestStatusSetAtWriteSide::test_the_same_status_does_not_restamp                             (D6)
# F6 timing-independence (real _AGE_TOKEN from the scratch test module):
SLOW-render fabzero:  != fresh PASSES (false-clear)? True  | F6 leg CATCHES (False=RED)? False
correct 'unknown':     F6 leg GREEN (True)? True
```

### CLI (F3/F4/F5/F7)

```
$ probe.py cli full ; pytest test_comms_cli.py                    -> 13 passed   (satisfiability)
$ probe.py cli wb_create ; pytest test_comms_cli.py               -> read_only_full_db RED + no_typed_write_method RED
    constant scan test_source_issues_no_write_verb                -> 1 passed    (F3 blindness)
$ probe.py cli wb_othertable ; pytest ...                         -> read_only_full_db RED + no_typed_write_method RED; constant GREEN
$ probe.py cli wb_merge ; pytest (full_db + AST + constant + counts_A)
    FAILED ...test_pending_is_read_only_full_db_content_unchanged             (content UPDATE, no count change)
    FAILED ...test_source_issues_no_typed_write_method
    (test_source_issues_no_write_verb PASSED; test_pending_reports_one_unread_directive PASSED — write landed, no crash)
$ probe.py cli hardcode ; pytest ...                              -> counts B (zero) RED + counts C (multiple) RED   (F5)
$ probe.py resolver correct ; pytest TestDefaultCoordinateResolution  -> 3 passed
$ probe.py resolver clone   ; pytest TestDefaultCoordinateResolution  -> 1 failed, 2 passed
    FAILED ...test_default_resolution_routes_through_the_shared_surrealconfig    (only F7; C-default+C-anthropic GREEN)
```

### No-regression

- Fix commit `dc54bbd` touches ONLY `test_comms_{story,status_age,cli}.py` (`git show
  --stat`). B4 (`test_rollup_extension.py`), #302 adjudication (`test_comms_wiring.py` /
  `test_task_read_surface.py` / `test_render_seam_pins.py`), property-keying domain trigger
  (`test_agent_registry.py`) are in UNTOUCHED files → cannot regress from this fix
  (prior-adversary-confirmed at 657a117).
- Every removed line in the diff is a REPLACEMENT with a STRONGER pin
  (`_seed_one_unread_directive`→`_seed_scenario`; `_comms_row_counts`→`_full_db_content`;
  single counts test→3 scenarios; row-count read-only→full-DB) or a constant refactor (A5's
  hardcoded forge prefix → `_FORGE_PREFIX`). D9a/D9b, D5/D6, A4b, A3, A5 method DEFs are
  ABSENT from the diff. D8 change is purely additive (kept `!= fresh`, added the F6 leg).

### Positive controls (P0 — the probes can SEE both directions)
- Story: `ref` is the accept-control (19 passed); each leak reddens ONLY its target
  field's param (`leak_done_summary`→only done_summary, `leak_ref`→only refs), so the
  parametrization discriminates PER FIELD rather than failing wholesale. `no_created_by`
  is a differently-broken build that passes A2 for a DIFFERENT reason (renders sender) —
  proving A2's creator leg cannot tell creator from sender.
- CLI: `wb_merge` shows the full-DB pin firing on a CONTENT change with no count change,
  while `test_pending_reports_one_unread_directive` PASSES on the same build (the CLI exited
  0 — the write LANDED, so the RED is a real content diff, not a crash artifact). The
  constant scan PASSES on all three write builds (proving it is blind by design, the exact
  gap the runtime pin closes).
- Age: `ref` greens all 8; `fabzero` reddens ONLY D8, `blindstamp` reddens ONLY D6 — the
  pins discriminate rather than failing wholesale.

### probe.py (verbatim — the load-bearing instrument, brief-base §1)

The harness splices one surface+mode into the scratch tree (restoring from a pristine
`.orig` first). Modes: `story {ref,leak_description,leak_done_summary,leak_ref,
no_created_by}`, `fleet {ref,fabzero}`, `touch {correct,blindstamp}`, `cli {correct,full,
wb_create,wb_merge,wb_othertable,hardcode}`, `resolver {correct,clone}`, `addfield
commsstory`, `restore all`. Reference builds are assembled from the shipped seams
(`render_attributed`/`render_fenced`, `pending_traffic`, `LoreConfig.
effective_surreal_database`), independent of the author's patchers. Full source lives at
`/home/ejprice/scratch/adv05aiii2-probes/probe.py` (disposable scratch) — reproduce any row
above with `python probe.py <surface> <mode>` then the pytest line shown. Key splices:
- story `_render_comms_story`: correct routes every field through `render_attributed`
  (single-line) / `render_fenced` (body verbatim); `leak_<field>` swaps ONE field to a raw
  `f"…{story.<field>}"` (the "never re-embed a Rendered in an f-string" footgun);
  `no_created_by` omits the created_by line while still rendering `sender_name`.
- touch: correct stamps `status_set_at` only when `new_status != agent.status`; blindstamp
  stamps every heartbeat.
- cli: `full` = SELECT-only reads (`pending_traffic` + brief head/ack skew) + resolver
  through `LoreConfig.effective_surreal_database`; `wb_*` open an `AsyncSurreal` conn and
  issue a typed write (`create`/`insert`/`merge`) during a "read-only" run.

## Scope law — nothing dropped
- The A2 creator/sender gap is a defect in a TEST FILE I may not edit; surfaced here with
  the exact one-line fix, not edited.
- I did NOT rebuild the D9-conflation, A4b-scope-blind, B4-nocursor, #302-removal, or
  property-keying doors: those pins are in files/methods the fix did not touch (proven
  absent from the diff), were confirmed-solid by the prior adversary at 657a117, and green
  on the correct builds here — rebuilding unchanged pins re-verifies prior work. Disclosed
  as a bound, not a silent skip.
- The F2 ∀-containment render-level-vs-handler bound (§A2) is surfaced, judged adequate,
  and explained — not dropped.
- Scratch tree `/home/ejprice/scratch/adv05aiii2` restored to pristine after the last leg;
  it is a `scratch_copy` (not a git worktree) — operator's call whether to reap it.

**VERDICT: CONTRACT SUFFICIENT** — all 7 prior findings hold and are mutation-proven, no
regression, satisfiability restored (each leg 0-failed on a correct build). The SOLE
residual is the A2 creator/sender monoculture: a real missing pin with a one-line fixture
fix (distinct creator value), which the lead applies and closes **without a third full
adversary pass** (the lead's pre-ruled path).
