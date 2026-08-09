# REPORT-contract-05ai-1 — packet 05a-i (comms CONSUME PATH) RED contract

brief-base v10 read
brief project v7 read

## Summary block
- **State:** done — four-leg contract written; directive #4002 set the oracle split (LANDED in `_message_fakes.py`); adversary INSUFFICIENT (#4005) → F1/F2/F3/F4 fixed; delta re-grade closed those and opened F5 (refs-variant path), now fixed. **Satisfiability receipt: `1275 passed / 0 failed / 17 skipped` across all 4 files** against the reference build + my `(question)` marker (incl. correct refs handling) in a provenance-verified `scratch_copy.sh` tree; the F5 mis-wire is mutation-proven RED. Working-tree contract state: **LEG A GREEN (12/12, incl. the new first-seq parity pin)** · **LEG B GREEN-on-fake / RED-on-real** · **LEG C RED-on-both** (production field pending) · **LEG D RED** (waiting helper pending, incl. the new F4 mutation pin) · **#195 GREEN**. NO production code touched.
- **Deviations:**
  - Brief's writable-set path `loremaster/loremaster/tests/` is wrong — the tests live at `loremaster/tests/` (code is `loremaster/loremaster/`). Wrote there.
  - Created a NEW file `loremaster/tests/test_comms_waiting_line.py` (permitted: "any new render-pin test file") for LEG C render + LEG D + LEG B/#195, importing drivers from `test_comms_tool.py`, to avoid widening #338 (that file is oversized/UN-INDEXED).
  - DD-2.b thread-required pin ALREADY EXISTS (`test_comms_schema.py::test_the_thread_spec_is_a_required_string`, + emitted-DDL companion) — CITED, not duplicated. That file is outside my writable set; untouched.
  - Fallback to grep/Read for the large test-file reconnaissance: `test_comms_tool.py` is the live index's `files_failed:1` (#338), so lore literally cannot serve it — forced, already ledgered.
- **Packages considered:** none — no mechanism specified (contract tests only; the one policy seam LEG A routes the fake through, `agent_existence.format_unknown_agent_refusal`, is already-shipped in-repo code the fake CALLS, not a package).
- **Graded:** authored at HEAD `git rev-parse` = `1d7296b` · no builder artifact graded (this IS the contract). Store law read: `docs/reference/surrealdb-31-capabilities.md` (§1.1 no-DDL, §2 silent-None/`SELECT *`, §5 hot-row/CAS), cited never re-transcribed. TEST store is 3.2.4 (brief-confirmed).
- **Decisions — ADJUDICATED by lead directive #4002 (drained + acked #4002):**
  1. **Oracle-fix ownership** — LANDED in `_message_fakes.py` (contract-author work by law): the 3 LEG-A prose fixes + `since=` on the fake drain. Production untouched; `InboxEntry.question` left to the builder (so LEG C stays RED-on-both).
  2. **Waiting-line thread rendering = `sanitise_line`** — CONFIRMED (Fable Q3 + fit: fence is for multi-line bodies; the mid-line length-bounded `thread` label wants `sanitise_line`). Kept the `sanitise_line` promise-proof marker.
  3. **`InboxEntry.question` default = `False`** — RATIFIED (required would redden ~7 constructions incl. the #338 file; a dropped projection is already caught by `test_a_drained_question_row_reports_question_True`).
- **Receipt pointers:** LEG A `test_message_ledger.py::TestTheOracleRendersProductionsErrorProse` · LEG B `::TestSinceServesAlreadySeenRows` / `::TestTheDrainPendingReadIsBounded` / `::TestStampedSeqsIsTheACTUALStampNotTheAttemptedWindow` · LEG C `::TestTheDrainRowCarriesTheQuestionMarker` + `test_comms_waiting_line.py::TestTheDrainRowVisiblyMarksAQuestion` · LEG D `test_comms_waiting_line.py::TestTheWaitingLine*` + `test_comms_promise_registry.py` (registry+proof+coverage) · #195 `test_comms_waiting_line.py::TestTheSinceReReadReusesTheDrainFence` · DD-2.b cite `test_comms_schema.py::test_the_thread_spec_is_a_required_string`.

## Fix wave — adversary INSUFFICIENT (#4005) → fixed, with a 0-failed satisfiability receipt

The contract-adversary (`REPORT-adv-05ai-1.md`) returned INSUFFICIENT with 4 real defects. All fixed in the CONTRACT (tests + oracle); production untouched.

- **F1/F2 (BLOCKER — seq-origin divergence, #190 class):** production `message.seq` is **0-based** (`sequence::nextval START 0`), the fake minted **1-based**, so the `since=0` recovery fixtures passed only in the fake's 1-based world (a strict-correct build lost seq 0 on `[real]`). Fixed: (1) fake now mints **0-based** (`_message_fakes.py` — assign-then-advance; `burn_seq` likewise); (2) NEW **first-seq real-vs-fake parity pin** (`test_a_fresh_ledgers_first_send_has_the_SAME_seq_on_both_backends` — same first seq on both, and it is 0); (3) `since=` fixtures derive the recover-all cursor as **`seqs[0]-1`**, never hardcoded 0; (4) NEW **`test_since_0_does_NOT_re_serve_a_processed_seq_0`** — kills the muddy `since==0 ⇒ >=` special-case (the only build that passed the pre-fix fixtures).
- **F3 (BLOCKER — LEG C marker had no classification home):** "glyph is builder latitude" was FALSE (the promise registry pins exact literals; `safe_str` strips leading whitespace so a context-slot marker can't be a standalone token). Fixed: chose the specific standalone token **`(question)`**, registered both drain-row `(question)` variants in `_PROMISE_FREE`, and updated the render pins to assert `(question)` exactly.
- **F4 (MEDIUM — "ONE shared helper" not mutation-proven):** a byte-identical heartbeat clone passed the output-identity pin. Fixed: NEW **`test_both_verbs_route_through_the_ONE_helper_PROVEN_BY_MUTATION`** — monkeypatches `_render_comms_waiting_line` to a sentinel and asserts BOTH drain and heartbeat move to it (a clone doesn't call the patched helper → RED).
- **F5 (delta-2, MEDIUM — the F3 refs-variant path was UNEXERCISED):** every LEG C render fixture used `refs=[]`, so a mis-wired refs branch (marks refs+NON-question rows, leaves refs+question rows UNMARKED — both `(question)` templates stay in source, so `test_no_dead_registry_entries` still passes) survived the whole contract. Fixed: NEW **`test_the_REFS_variant_ALSO_discriminates_question_from_non_question`** — a refs-carrying question/non-question pair with the SAME single ref on both rows, so the only token difference is `(question)` (exercising the `…(question) ({refs})` template); and `_q_entry`'s `refs` is now REQUIRED (AC-11: no default on a branched param). MUTATION-PROVEN in the scratch: the F5 mis-wire (swap the refs-branch templates) reds it with `q_tokens - plain_tokens == []`; the correct build passes.

**SATISFIABILITY RECEIPT (`scratch_copy.sh` tree `/tmp/adv-05ai-fixwave`, provenance `loremaster.__file__ = /tmp/adv-05ai-fixwave/loremaster/loremaster/__init__.py`, spike-surreal :18000, store 3.2.4):** the adversary's reference build (messages.py + server.py + the fake `question` passthrough) PLUS my `(question)` marker in `_render_comms_drain_row` (4 literal templates, duplicated-call form per the AST-literal pin) + the L1/L2 guards → **`1275 passed / 0 failed / 17 skipped`** across all 4 files (`-n auto`), ruff clean. The adversary's own reference was 1265/5-failed; the +10 delta is exactly the F1/F3 fixtures now passing on `[real]` plus the 4 new pins (first-seq parity, seq-0 discrimination ×2 backends, F4 mutation, F5 refs-discriminate). A known-correct build is 0-failed ⇒ the contract is satisfiable.

## #342 — gate close-out (post-build, integrated tree at `d9b151b` + builder production)
The build landed; the working tree now carries the builder's production (`messages.py` drain reshape + `InboxEntry.question`; `server.py` `_render_comms_waiting_line`) plus my contract. One gate-blocker remained: `test_message_ledger.py` shipped 6 redundant `# type: ignore[method-assign]` on the Any-typed `_query` monkeypatches (unused-ignore under `warn_unused_ignores`). Deleted all 6 (the targets are Any, so the bare assignment type-checks — no cast needed, matching the other Any-typed sites). Receipts:
- **`scripts/typecheck.sh`: ZERO errors in any 05a-i file** (`messages.py`, `server.py`, `_message_fakes.py`, `test_message_ledger.py`, `test_comms_waiting_line.py`, `test_comms_promise_registry.py`). The only residual is the **#333 auth-WIP baseline — 102 errors across 8 auth files** (`test_auth_composition.py`, `test_permission_resolver_seam.py`, `test_hosted_readonly_posture.py`, `test_allowlist_roster.py`, `test_google_token_verifier.py`, `test_auth.py`, `_auth_fixtures.py`, `test_auth_identity_seam.py` — all `Posture`/`resolve_posture`/`SCOPE_READ` not-yet-implemented), untouched by 05a-i.
- **4-file suite on the integrated tree: `1275 passed / 0 failed / 17 skipped`** (`-n auto`). Ruff clean on all 6 files. #342 closed.

## Landed oracle behaviour (`_message_fakes.py`, per directive #4002 — the ONLY file with non-test-pin edits)
- `IllegalMessageGradeError` → routes the grade through `render_attributed(grade)` (was `{grade!r}`).
- `EmptyRecipientSetError` → the ledger's OWN wording ("…is a caller error, not a broadcast"; was the dispatcher's "no other non-retired agent…").
- Added a sender-existence check raising `UnknownSenderError` via `format_unknown_agent_refusal({sender.id: sender.name})`, checked in PRODUCTION ORDER (after the empty-set check, before recipients) — byte-identical to production's `reject_unknown_rows(agent_identities([sender]))`.
- `drain(…, since=None)` → a non-stamping recovery read (seq > since STRICT, seen or unseen, oldest-first, bounded at limit), the independent LEG-B fake reference. Entry construction extracted to `_inbox_entry(message, agent_id)` so the builder's later `question=message.question` passthrough is a single-line change.
- NOT landed (builder's, by directive): `InboxEntry.question` (production model + real projection + real mapper + the fake's one-line passthrough) and the real `stamped_seqs` TOCTOU read-back.

---

## RED/GREEN confirmation (behavioural, verified 2026-08-08 at `1d7296b`, spike-surreal :18000, POST-adjudication)

| leg / suite | state | receipt |
|---|---|---|
| **LEG A parity** `test_message_ledger.py::TestTheOracleRendersProductionsErrorProse` | **GREEN 11/11** | 10 real-vs-fake scenarios (incl. the 3 formerly-divergent: grade / empty / sender) + the ∀-coverage pin, all pass after the oracle fix. |
| **LEG B** since= / #183 / stamped_seqs | **GREEN-on-fake / RED-on-real** | fake `drain(since=…)` models the designed semantics (3 `[fake]` pass); `[real]` reds on the unbuilt kwarg / unbounded read / over-describe. The **`stamped_seqs` TOCTOU injection fires deterministically** — real returns `[0,1,2]` claiming seq 1 a racer stamped. `[fake]` skips (already truth). |
| **LEG C** question marker (ledger + render) | **RED-on-both** | `question` → `extra_forbidden` (production model field pending, per D1); render marker absent. |
| **LEG D** waiting line + promise triple | **RED** | no `waiting:` line yet; `_render_comms_waiting_line` absent → promise `predicate_gates` + dead-entry + scan-coverage red (+ 4 cross-satisfaction meta-tests transitively, verified `AttributeError` not a collision). |
| **#195** since= fence reuse | **GREEN** | recovered hostile body is fenced by the shared `_render_comms_drain` (reuse, not a second containment) once the fake `since=` exists. |

**No regressions in the touched-file riders** (the `_message_fakes.py` change is used by both consumer suites): `test_message_ledger.py` send/drain/ack/vocab **117 passed / 7 skipped**; `test_comms_tool.py` send/drain/broadcast/fenced/skew/set-status **233 passed / 0 failed**; `test_comms_promise_registry.py` **112 passed** (non-LEG-D). No existing `UnknownSenderError` test conflicted (the parity battery is its first exerciser). Ruff clean on all four files.

---

## LEG A — #190 oracle↔production error-prose parity (THE ENTRY GATE)

**Pins (`test_message_ledger.py::TestTheOracleRendersProductionsErrorProse`):**
- `test_the_oracle_raises_the_same_TYPE_and_the_same_PROSE_as_production` — parametrized over 10 scenarios (`parity_pair` fixture builds a REAL ledger + the FAKE, seeded identically). Compares `type(exc)` and `str(exc)` real-vs-fake.
- `test_the_parity_battery_covers_every_message_ledger_error` — coverage as a CHECKED variable: the scenario set's error types == `_concrete_message_ledger_errors()` (recursive `__subclasses__()` walk). A new `MessageLedgerError` subclass with no scenario reddens here — no name-list to go stale.

**Discriminating fixtures / wrong builds stopped:**
- `illegal_grade` (RED): prod `render_attributed(grade)` vs fake `{grade!r}`. Wrong build: an oracle that clones prose instead of routing through the shared seam and drifts (D4's exact shape).
- `empty_recipients` (RED): prod "…is a caller error, not a broadcast" vs fake "no other non-retired agent…". Verified SAFE for `test_comms_tool.py`: the surface `_comms_send` raises its OWN `_EmptyRecipientSetError` before the ledger's is reached, so the solo-broadcast surface pins never see the fake ledger's prose.
- `unknown_sender` (RED): the fake never checks the sender, so it raises NOTHING where prod raises `UnknownSenderError` — the gap manifests in `_raised()` returning `None`.
- 7 matching legs GREEN (blank/over-cap body, refs-count/refs-len/thread-len pointers, unknown-recipient, ack-note cap) — already route through shared seams; pinned so a FUTURE prose change reddens.

**Satisfiability:** a correct build routes the fake's grade prose through `render_attributed(grade)`, its empty-set prose to the ledger's own wording, and adds a sender-existence check calling `format_unknown_agent_refusal({sender.id: sender.name})` raising `UnknownSenderError` (checked FIRST, matching production order). All matching legs already share seams (`_reject_oversize_pointers`/`_reject_oversize_note`/`format_unknown_agent_refusal`). The `question`-field parity is enforced by LEG C running on BOTH backends (parametrized `message_ledger`).

## LEG B — since= (DD-4.c) + #183 (bound the pending read) + stamped_seqs truth (DD-4 Q5)

**Decisions taken and pinned:**
- **since= seq semantics = `seq > since` (STRICT).** `since` names the last seq the caller ALREADY processed. `test_since_is_STRICTLY_greater_than_the_cursor` discriminates `>` from `>=` (fixture: `since=seqs[1]` must return only `[seqs[2]]`).
- **since= is a non-stamping RECOVERY READ** — serves rows > since (seen OR unseen), stamps NOTHING, consumes nothing (`test_since_does_not_re_stamp_and_does_not_consume_unseen`). A plain drain (no since) still serves only unseen.
- **stamped_seqs = TRUTH** (not delete): the field's docstring already promises "EXACTLY the seqs the served window stamped seen"; production sets it to the ATTEMPTED window and lies under a concurrent same-agent race. TRUTH aligns code with its shipped contract and is the safe direction. Pinned deterministically via a `_query`-seam TOCTOU injection (real-store; fake skips — it already models truth by construction).

**Wrong builds stopped:** a since= serving only UNSEEN rows (leaves D11/#214 open); a since= that stamps (consumes recovery rows); an unbounded pending read (#183 — `test_the_entries_read_never_materialises_more_than_the_limit` observes ≤ limit entry rows via a `_query` wrapper while `total_pending` still counts the whole set); an over-describing `stamped_seqs`.

**Satisfiability:** reshape drain's read into a bounded `ORDER BY seq LIMIT` entries read + a separate `count()` for `total_pending`; a `since=<seq>` recovery branch serving `seq > since` (seen or unseen), non-stamping, likewise bounded; and `stamped_seqs` read back from the guarded UPDATE's result (`RETURN`) rather than the attempted window. #195: since= returns a `MessageDrainResult` rendered by the ONE `_render_comms_drain` — `TestTheSinceReReadReusesTheDrainFence` proves a recovered hostile body is fenced by that shared seam, not a second containment.

## LEG C — per-row `question` marker on `InboxEntry` (R1, no DDL)

**Pins:** ledger-level (`TestTheDrainRowCarriesTheQuestionMarker`, real+fake) — `InboxEntry` has `question`; a drained question row reports `question is True`; a question AND a non-question row in ONE drain discriminate (parameter-value monoculture banned). Render-level (`test_comms_waiting_line.py::TestTheDrainRowVisiblyMarksAQuestion`) — a question row differs from a non-question row (all else equal); the marker is ON the question row and the non-question row carries nothing extra (glyph-agnostic, and it enforces question⊥grade orthogonality); the marker keys on the received row's flag, not the drainer's own debt (Leg-1 vs LEG D).

**Satisfiability:** add `question: bool` (recommend `= False`) to `InboxEntry`; project `in.question AS question` in the drain SELECT (no DDL — `message.question` is already `bool DEFAULT false`); populate it in `_row_to_inbox_entry`; mark question rows in `_render_comms_drain_row` (glyph is builder latitude). The fake mirrors `question=message.question`. Runs on BOTH backends = the #190 question-parity.

## LEG D — DD-2.a waiting line (drain AND heartbeat, ONE shared helper)

**Pins:** emit on drain and on heartbeat; derived from the typed `WaitingOnAnswer` (line names the question's own seq + thread — #104 law); ONE shared helper proven by the byte-IDENTICAL line from both verbs (mutation obligation stated for the builder+adversary); the **DD-2.a discriminating pair** (STORED `active` + question → renders; STORED `input_required` + no question → does NOT render — a status-keyed build fails both); a hostile-thread containment case; and the promise-registry triple (registry entry + `PromiseProof` emit/no-emit + full-line marker), with the helper NAMED `_render_comms_waiting_line` (`_render_comms_` prefix) so the scanner reaches it (#337) and added to `TestTheScanReachedEveryCommsRenderHelper`'s coverage set.

**Wrong builds stopped:** wiring "waiting" to the STORED `input_required` status (the two-vocabulary conflation — the pair fails it both ways); a private clone per verb (the identical-line pin); a re-derived flag instead of the typed state (the seq/thread pins); an off-prefix helper silently exempt from the scanner (#337); an unfenced/unsanitised thread.

**Satisfiability:** `_render_comms_waiting_line(waiting: WaitingOnAnswer | None, *, age_s) -> list[Rendered]` (empty when None, one line otherwise — the `_render_comms_skew_lines`/`registered_age_s` precedents; `age_s` pre-computed so the render is pure/deterministic); drain and heartbeat each read `awaiting_answer(agent_id)`, compute `age_s`, and compose the helper's lines. Exact template (contract author's, DD-2.a): `waiting: your question #{seq} on thread {thread} has no reply — asked {age} ago`. Waiting line is additive/conditional → existing drain/heartbeat pins in `test_comms_tool.py` stay green (their agents owe no question).

**DD-2.b:** verified pinned — `test_comms_schema.py::test_the_thread_spec_is_a_required_string` asserts `_MESSAGE_FIELD_SPECS["thread"] == "string"` citing the `awaiting_answer` IN-clause dependency, with an emitted-DDL companion. Cited, not duplicated.

## Store-ref sections relied on
`surrealdb-31-capabilities.md` §1.1 (R1/DD-2.a add NO DDL — `question` is a stored `bool DEFAULT false`, `thread` a required `string`) · §2 (a since= read over `option`/projection reads; `_row_to_inbox_entry`'s None-tolerance) · §5 (the guarded CAS / hot-row stamp — the `stamped_seqs` TOCTOU and the "gaps are real" ordering key). No new DDL asserted by this contract.
