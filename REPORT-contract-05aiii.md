# REPORT-contract-05aiii — RED contract for packet 05a-iii (comms READS + FLEET honesty)

brief-base v10 read
brief project v7 read

## Summary block
- **State:** done. RED contract authored + verified: 4 new test files (25 pins) + minimal stubs in 4 production modules + the story #302-adjudication edits. Gates: ruff clean; zero NEW mypy in any touched file; my suites **12 failed / 13 passed** — every one of the 12 a *behavioural* `AssertionError` (RED for the right reason), the 13 the intended-GREEN structural/discrimination/Leg-1/decline pins. Zero NEW failures in existing non-auth files.
- **Deviations (disclosed):**
  1. Touched two files beyond the literal writable list — `test_comms_tool.py` and `test_task_read_surface.py` — to update the exact-set / #302 / render-completeness pins for the new `story` action. Explicitly authorized by Scope A ("the exact-set registration pins + the #302 'no action appears unadjudicated' pins must be updated — this packet is its adjudication").
  2. Added a `story` clause to the served `lore_comms` tool DESCRIPTION in `server.py` — required by `test_description_names_every_action` (a #302-family pin). Minimal, part of the adjudication.
  3. Rename-sweep hygiene: updated two `server.py` comments that named `story` as a "C2/C3 growth point" (now shipped) — the retired-name-in-a-comment class this repo pins.
- **Packages considered:** none — no mechanism specified. This is a TEST CONTRACT; every mechanism it pins is already-built lore code (`render_fenced`/`render_attributed` containment, `awaiting_answer` derivation, the agent-DDL house pattern `_define_field`, the rollup ledger). 05a-iii REUSES these; it hand-rolls no second copy (ONE IMPLEMENTATION verified per-section). The `status_set_at` field is a schema addition, not a package choice.
- **Graded:** authored against `ee1d19a` (HEAD == lore index `git_ref` == the `REPORT-fable-design-05a` graded sha — all aligned). Store live-read: spike-surreal `:18000` (3.2.1); `:18500` never touched.
- **Decisions-needed (operator/lead forks — surfaced, none silently resolved):**
  1. **D/#304 age SCOPE** (genuine spec ambiguity, PKT-28 C1 class). Age `input_required` ONLY (recommended, pinned) vs the WHOLE status cell. Whole-cell BREAKS existing green `test_comms_fleet_grouping.py:124-126` (`[idle]`/`[active]` brackets — a C-DEF trap) and is noisy (active/idle churn via the idle→active auto-flip); `retired` renders in the `+K retired` trailer, not a status-bracket row, so it is moot. **Recommend input_required-only.** (#304's own body flags this as UNMEASURED.)
  2. **C/comms_cli coordinate resolution** (genuine spec gap). The design specifies the command + "direct SELECTs" but NOT how a standalone CLI resolves its store coordinate + target DATABASE. Contract pins the EXPLICIT-override path (`--url/--namespace/--database/--user/--password`); the DEFAULT resolution (read lore config? require args? env contract?) is a fork.
  3. **A3 question-marker glyph** — contract-DEFINED as the word `"question"`; the exact glyph/spelling is builder/operator-adjustable within the pinned "structural, from `message.question`, present-for-question-absent-for-signal" property.
  4. **D8 NONE-render wording** — builder-flexible within the pinned property (a NONE `status_set_at` must render DIFFERENTLY from a 0-second one; never a fabricated `0s`).
- **Receipt pointers:** pin inventory §Pin inventory · satisfiability §Satisfiability · discrimination §Discriminating interrogations · mutation-proofs §Mutation-proof notes · gate counts §Gate counts · escalations §Escalations. Report is at repo root (will be archived per repo law at wave close-out).

---

## Ground-truth receipts (verified this session at `ee1d19a`, lore-first)

### Render / containment seam (04b5, #321/#102) — `loremaster/loremaster/render.py`
- `render_line(template: LiteralString, /, **values: SafeLine|Rendered|int) -> Rendered` (:147) — assembles ONE single-line render; RAISES `RenderSafetyError` on any control/newline char in the template OR a value.
- `render_fenced(body: str) -> Rendered` (:230) — wraps `body` VERBATIM (raw — byte-round-trips) inside a `\n`-delimited backtick fence sized by `fence_width` (strictly longer than any embedded backtick run). **THE seam for MULTI-LINE stored free text** (message bodies).
- `render_attributed(value: object) -> Rendered` (:249) — sanitises to ONE line + inline backtick delimiter. **THE seam for SINGLE-LINE attributions/ids** (sender names, refs, the `story` task-id anchor). ⚠ Never re-embed a `Rendered` in an f-string.

### Fleet render — `loremaster/loremaster/server.py`
- `_render_comms_fleet_row` (:6638) renders `- {name} [{status}] hb {age} · {cells}` (or `[{status} ⚠ STALE]`). The `{status}` cell is the #304 LATCH.
- `_render_comms_fleet` (:6678) + handler `_comms_fleet` (:5889): **ages arrive PRE-COMPUTED off ONE `datetime.now(UTC)` in the handler** (`heartbeat_age_seconds = {row.id: int((now - row.heartbeat_at)...)}`) → #304's declaration age is a sibling map off the same `now`.
- #332 confirmed: `⚠ STALE` is already derived-at-render via `_render_age`; #304 fixes the `{status}` cell only and MUST NOT touch STALE.

### Agent model + waiting derivation
- `Agent` (`extra="forbid"`, `agents.py:202`) gains `status_set_at: datetime | None = None`; decoder `_row_to_agent` (:907) threads it NONE-tolerantly (store §2: `SELECT *` omits a NONE option column).
- `MessageLedger.awaiting_answer` (`messages.py:1277`) — the DERIVED question-debt vocabulary (`message.question=true AND sender=me`, unanswered on-thread). DD-2 forbids conflating with the STORED `input_required` status. Seeds the D9 discriminating pair.

### Store law (cited, not re-transcribed) — `docs/reference/surrealdb-31-capabilities.md`
- §1.1 — FIELD uses `DEFINE FIELD OVERWRITE` (`_define_field` emits it; `IF NOT EXISTS` = #107 silent no-op).
- §1.4 — a NEW field on a POPULATED table must be `option<>`; a required/asserted field poisons every existing row's next UPDATE; only `option<>` + no-assert cannot. → `status_set_at option<datetime>` no-assert is the §1.4-safe shape (pinned by D10).
- §1.6 — the dirty-store pattern (D10 mirrors it: a row written WITHOUT the field survives a later UPDATE).

### Absence confirmed (deliverables) — `story`: no production `_comms_story`/`_render_comms_story` at HEAD (only growth-point comments). `comms_cli.py`: absent. Both now created as STUBS.

---

## Pin inventory (grouped A–E) — 25 pins across 4 new files + adjudication edits

Legend: **RED** = behavioural, fails against the stub for the right reason, greens on a correct build. **GREEN(inv)** = structural/discrimination invariant (passes vs stub AND a correct build; reddens against a specific wrong build).

### A — `story` (`test_comms_story.py`)
- **A2** `test_story_renders_subject_creator_owner_messages_and_report_path` — **RED**. Reconstructs the arc (subject/creator/owner/message-body/report_path).
- **A3** `test_a_question_message_is_marked_and_a_signal_is_not` — **RED**. Structural question marker from `message.question`; non-monoculture (question task marked, signal task not).
- **A4a** `test_story_names_its_set_the_task_arc` — **GREEN(inv)**. Leg-1: render NAMES its SET (task id + "arc").
- **A4b** `test_story_omits_other_tasks_traffic` — **GREEN(inv)**. Leg-1 boundary: a message on a DIFFERENT task never appears (reddens a scope-ignoring build).
- **A5** `test_a_hostile_message_body_is_fenced_verbatim` — **RED**. CONTAINMENT: a hostile multi-line body (newlines + row-forge + backtick run) round-trips verbatim inside a fence wider than any embedded run, no forged row outside. Clones `TestFencedBodyIntegrity`'s oracle (ONE IMPLEMENTATION — `render_fenced`).
- **A(reg)** `story.task_id` RenderCase in `C1_RENDER_CASES` (`test_comms_tool.py`) — **GREEN**. Satisfies the per-action completeness pins + drives the injection battery through `render_attributed`.

### B — rollup extension (`test_rollup_extension.py`) — all **RED**
- **B1** messages-activity section present. **B2** fleet-health section present. **B3** brief-ack-skew section present. **B4** messages section is cursor-bounded (a pre-`since` message excluded, a post-`since` one included — discriminating against a since-ignoring build).

### C — `comms_cli.py` (`test_comms_cli.py`)
- **C-cmd** (3, **GREEN**) — command surface `pending --agent` (+ coordinate overrides); missing `--agent` errors.
- **C-counts** `test_pending_reports_unread_unacked_and_skew` — **RED**. `unread=/unacked=/skew=` from a live-seeded store (register lead+x, send x a directive ⇒ `unread=1 unacked=1 skew=0`).
- **C-readonly-runtime** `test_pending_is_read_only_row_counts_unchanged` — **GREEN(inv)**. Row counts byte-identical before/after (reddens a writing build).
- **C-readonly-source** `test_source_issues_no_write_verb` — **GREEN(inv)**. AST scan (docstring-excluded) — no CREATE/UPDATE/DELETE/RELATE/UPSERT/INSERT in any code string.
- **C-coordinate-safety** `test_source_never_hardcodes_the_production_coordinate` — **GREEN(inv)**. AST scan — no `18500` literal in code.

### D — #304 age-the-declaration (`test_comms_status_age.py`)
- **D4** `test_status_set_at_is_option_datetime_via_overwrite` — **GREEN**. Schema pin: `_field_statement(generate_agent_ddl(), AGENT_TABLE, "status_set_at")` asserts the `DEFINE FIELD OVERWRITE` guard (house idiom) + `option<datetime>`.
- **D5** `test_a_status_change_stamps_status_set_at` — **RED**. A status CHANGE stamps it.
- **D6** `test_the_same_status_does_not_restamp` — **RED** (precondition) + discriminating. "Same status twice ⇒ unchanged" — reddens a blind-stamp-every-heartbeat build.
- **D7** `test_input_required_shows_the_declaration_age_beside_the_liveness_age` — **RED**. Declaration age (`47m`) in the status bracket, BEFORE + distinct from `hb`.
- **D8** `test_none_status_set_at_renders_unknown_not_a_fabricated_zero` — **RED** + discriminating. A NONE cell renders DIFFERENTLY from a 0-second cell (reddens a fabricate-zero build).
- **D9a** `test_active_with_an_outstanding_question_still_shows_active` — **GREEN(inv)**. Stored `active` + a real outstanding question → shows active (reddens an `awaiting_answer`-wired build).
- **D9b** `test_input_required_with_no_question_still_shows_input_required` — **GREEN(inv)**. Stored `input_required` + no question → shows input_required (reddens an `awaiting_answer`-wired build = false-not-waiting).
- **D10** `test_a_row_without_status_set_at_survives_a_later_update` — **GREEN(inv)**. §1.4 no-poison (reddens a required/asserted-field build).

### E — #195 (`test_comms_story.py::TestObedienceDecline`)
- **E** `test_195_obedience_is_declined_to_06_drill` — **GREEN** (statement). The obedience measurement is DECLINED to 06's drill, said OUT LOUD (docstring). 05a-iii's injection duty is the A5 fence + A3 legibility — measuring legibility, NEVER inertness. Not a silent third deferral.

### Adjudication edits (mandatory — the reshape reddens these unless updated)
- `_EXPECTED_COMMS_ACTIONS` (`test_task_read_surface.py`) += `story` (dispatch order). `TestCommsActionsTable._EXPECTED_ACTIONS` (`test_comms_tool.py`) += `story` + `test_story_params_and_required`. `C1_RENDER_CASES` += `story.task_id`. Served tool description names `story`.

---

## Satisfiability argument (the contract goes 0-failed against a known-correct build)

The adversary will build the reference; my obligations, discharged:
- **No pin RED-for-the-wrong-reason.** Every one of the 12 RED pins was RUN and fails on a *behavioural `AssertionError`*, NOT a setup/import/`TypeError` — proving the live-ledger seeds (register/send/create_task/claim/transition/publish), the live fleet-handler drive (`_comms_fleet(harness, …)`), the story-handler drive, and the CLI subprocess all WORK. A correct build (that stamps `status_set_at`, ages the render, reconstructs the arc, fences bodies, adds the rollup sections, greens the CLI, names `story` in the description) flips each RED → GREEN.
- **No two pins contradict.** The 13 GREEN(inv)/structural pins pass against the stub already; they are additive invariants. The existing `test_comms_fleet_grouping.py:124-126` (`[idle]`/`[active]`) stay green because #304 ages `input_required` only (the age-scope fork resolved consistently with them). No test hardcodes an `[input_required]` bracket (grepped), so the D7 age pin contradicts nothing.
- **No pin trapped between ruff and an un-editable test.** All new files ruff-clean; the story adjudication edits are in editable pin files (authorized by Scope A).
- **Existing surface intact (measured):** after the adjudication + the schema field, `test_comms_tool.py` + `test_task_read_surface.py` + `test_comms_schema.py` + `test_comms_fleet_grouping.py` + `test_comms_render_architecture.py` = **1298 passed / 1 skipped / 0 failed**; `test_mcp_server.py` registration+instructions subset = **22 passed**. ZERO new failures.

## Discriminating interrogations ("what WRONG build still passes this?")
- **D9 vocabulary pair** — a build wiring the fleet badge to `awaiting_answer` passes D9a alone (active agent, no question) but FAILS both real fixtures: D9a's active-WITH-a-question (badges input_required wrongly) and D9b's input_required-WITH-no-question (badges nothing). Two fixtures, different values, REAL awaiting_answer state (live store) — the DD-2 conflation is the wrong build both catch.
- **D8 NONE vs 0s** — a build that defaults NONE→0 fabricates a "just declared" age; D8 compares the two status cells and reddens on `==`. Single-value fixtures (only NONE, or only 0s) would pass a fabricate-zero build; the PAIR discriminates.
- **D6 same-status** — a blind-stamp-every-heartbeat build resets the declaration age to ~0; D6 pins `second == first` after a non-change heartbeat. A fixture with only ONE heartbeat can't see it.
- **A3 question marker** — bodies deliberately avoid the marker word ("please advise on the approach"), so the marker comes from the STRUCTURAL `message.question` flag, not the prose; a build that renders bodies but ignores the flag fails (absent) — a body-derived marker would be the fixture-reason pass this avoids.
- **A5 fence** — the hostile body is multi-line + backtick-run + row-forge; a build that sanitises-into-one-line (the single-line-fixture green path) fails the verbatim round-trip, and a raw-unfenced build fails the "no forged row outside the fence".
- **C-readonly** — the AST scan excludes docstrings (which legitimately NAME the write verbs / `:18500`) so it does not false-positive on its own explanatory prose; a build that adds a real write query string reddens.

## Mutation-proof notes (which RED pins the builder must be able to demonstrate failing)
- **D5/D6** are the mutation-provable write-side pins: break the stamp-on-change → D5 red; add stamp-on-every-heartbeat → D6 red. (Verified RED against the no-stamp stub now.)
- **D7/D8** mutation-prove the render: strip the declaration age → D7 red; render NONE as `0s` → D8 red.
- **A5** mutation-proves containment: replace `render_fenced` with a raw interpolation → the forged row escapes the fence → red.
- **B4** mutation-proves the cursor: drop the `since` filter on the messages leg → the pre-cursor sentinel appears → red.
- The GREEN(inv) pins (D9/D10/C-readonly/C-coordinate/A4b) are mutation-proven by construction (each names the specific wrong build it reddens against, above).

## Escalations (spec ambiguities NOT silently resolved — PKT-28 C1)
1. **D/#304 age SCOPE** — input_required-only (pinned, recommended) vs whole-cell (breaks grouping pins, noisy) vs latching-only. The contract PINS input_required-only via the D7 pin + the preserved grouping pins; adopting whole-cell requires editing `test_comms_fleet_grouping.py:124-126` and is the lead's/operator's call.
2. **C/comms_cli coordinate resolution** — the standalone CLI's DEFAULT store-coordinate + target-database resolution is unspecified. Contract pins the explicit-override path; default resolution is a fork.
3. **A3 marker glyph** / **B rollup section content shape** / **D8 NONE wording** — contract-shaping choices within builder latitude; flagged in each file's docstring, not blocking.

## Gate counts (failing-FILE classification — zero NEW non-auth failures)
- **ruff** `uv run ruff check` — **All checks passed** on every new/edited file.
- **mypy** `scripts/typecheck.sh` — **ZERO errors in any file I touched** (grep over all 10 paths returned nothing). Branch baseline ~191–219 mypy errors are ALL pre-existing auth WIP (pkt 39/45/48/49; #333, operator-accepted) — untouched, none added.
- **pytest** my 4 new files (`-n auto`, spike-surreal `:18000`): **12 failed / 13 passed** — the 12 are the intended behavioural-RED contract pins; the 13 the intended GREEN(inv)/structural/decline pins. No ERRORs.
- **pytest** existing NON-auth comms files (satisfiability): **1298 passed / 1 skipped / 0 failed** (5 files) + **22 passed** (mcp_server registration/instructions). ZERO new failures.
- **Failing-FILE classification:** the ONLY files carrying failures attributable to this contract are the 4 NEW RED-contract files (by design). No existing non-auth file gained a failure. The branch-wide auth-WIP RED baseline (#333) is unchanged.

---

## Writable set touched (full list)
Production stubs: `agents.py` (`status_set_at` field + `_COL_STATUS_SET_AT` + decoder), `store/surreal_schema.py` (`_AGENT_FIELD_SPECS` += `status_set_at option<datetime>`), `server.py` (`_COMMS_ACTION_STORY` + `CommsStory`/`StoryMessage` + `_comms_story`/`_render_comms_story` stubs + `_COMMS_ACTIONS` entry + tool-description clause + 2 growth-point comments), `comms_cli.py` (new read-only stub).
Tests: `test_comms_story.py`, `test_rollup_extension.py`, `test_comms_cli.py`, `test_comms_status_age.py` (new); `test_comms_tool.py` + `test_task_read_surface.py` (the story #302 adjudication — authorized by Scope A).
