# design-sidecar-66 — ruling 16: the audit DELTA — S1 (h3 false for a non-MIN truncated leg) + S2–S6, right-sized to one tiny wave

brief-base v25 read · 2026-11-08 · HEAD at writing: 672b6d6 (the graded delta commit) · the operator rules; this recommends.
Read: `audit66/REPORT-audit-66.md` §DELTA (the S1 bullet, the items table, D-1..D-4) and `REPORT-delta-r17-66.md` (checks 1–4, the S1 probe output); `server._rollup_leg_header` / `_rollup_next_cursor` / `_render_rollup` (header calls precede the cursor computation) / `_rollup_message_activity_lines` (h2, h2-held); the two h3 pins (`test_sdk3_rollup_ties_r15.H3_OTHER_LEGS_RESERVE` + the literal in `test_mcp_server::test_truncated_leg_header_shows_n_of_total_and_teaches_resume`); `_txn.required_datetime` (the R34 text) and its 20 callers (every `row_id=row.get(…)`); `messages.message_activity_since`'s projection and `_row_to_stored_message` (explicit fields, never `**row`); `_txn.record_text` (a `str` passes through); `scripts/snapshot_gc._to_aware_utc` + its two callers, `diff.SnapshotSummary.created_at` (a `str`, rendered from an aware datetime at `diff.py` `created_at.isoformat()`); RULING-1 Q5 and RULING-14 R-12. No code, no edits, no runs.
Packages considered: none — wording and one projection token. Reuse ledger: none.

**S1 is MY defect.** RULING-15 §3 rider 3 / §4 Q2 wrote the h3 clause over the ONE-truncated-leg case I derived it on and let it be served on every truncated leg — THE QUANTIFIER LAW in the shape CLAUDE.md names for design-sidecar-03b-1 (DD-3.c): a property derived on one member of the set the ruling governs, stated over the whole set. The askable form I did not ask: *"does this header's claim still hold for every leg that renders it, or only the leg I derived it on?"* Recorded so the archive reads it as a correction, not a new finding.

## S1 — verdict: **ONE leg-agnostic h3 string, true in every state, actionable by id. Not the per-leg derivation.**

**Why not per leg.** The consumer cannot use the extra precision: rollup rows render NO stamp (`(id …, owner …)` / `[#n status] …`), so "this leg's rows above the cursor are served again" is not a rule an agent can apply — it can only dedupe by id across calls. Two variants would also mean two spellings, two pins, and a header that depends on a global (`next_cursor`) computed over all legs — the exact coupling that produced S1. **The closing rule (fix the class):** a leg header states leg-local facts (shown, total, its held group) plus ONE global sentence whose truth does not depend on which leg renders it; the cursor's value lives on the `next cursor:` line alone (unchanged — consumers hand that text back, so it gains no suffix).

**The exact string (h3), one constant, pinned once:**

```
{label} (showing {shown} of {total} — the next cursor is the earliest resume point of any leg, so rows above it in any leg, this one included, are served again next call: dedupe by task id or finding number; re-call rollup with it, or raise limit):
```

True in every state, checked: (i) this leg is the MIN leg → no row of this leg lies above the cursor, so "this one included" is vacuous and nothing is wrongly promised; the other legs' rows above it ARE re-served; (ii) another truncated leg is the MIN → this leg's rows above the cursor are re-served — named; (iii) a held leg beside this one → the cursor is `since` (a held leg's resume point IS `since` — "earliest resume point of any leg" covers it, where "elision point" did not), and every served row re-serves — named. "Dedupe by task id or finding number" is the one instruction an agent can act on without stamps. h1 (held) is already state-independent ("this cursor does not advance" is true whenever any leg holds, by `_rollup_next_cursor`'s min) — unchanged.

**Rider — pins, servicer first (R23), RED at 672b6d6, then the builder re-words the render:**
- **P7 (two truncated legs — the audit's state, live on :18000):** task leg truncated at HIGH, finding leg at LOW (the `probe_h3_two_truncated.py` fixture, forced stamps); both headers equal the new constant formatted per leg; `next cursor` = LOW; **then the walk:** the next call with that cursor re-serves the task row above LOW — the "this one included" clause MEASURED, not asserted. Kills: the 672b6d6 text (RED by string), and a build that advances the cursor to HIGH (the re-serve does not happen).
- **P8 (truncated beside held):** task leg held (3 rows at one stamp, `limit=1`) beside a finding leg truncated (2 rows); task header = `H1_HELD`, finding header = the new h3, served cursor = `since`; next call re-serves the finding row. Render-seam (the `_stamp_page_fakes` windows) is acceptable here — the hold mechanics are already live-pinned by P1/P5; the new claim is the finding leg's header text in this state.
- Rename the constant (`H3_OTHER_LEGS_RESERVE` is stale prose as a name once the clause no longer says "other legs"): `H3_EARLIEST_RESUME`. The `_rollup_leg_header` docstring's h3 sentence and the `#592 Q2` comment follow (stale-prose class).

## S2 — collapse to one spelling: the `test_mcp_server` pin IMPORTS the constant

`test_mcp_server::test_truncated_leg_header_shows_n_of_total_and_teaches_resume` keeps its behaviour (the dispatcher path on natural stamps, `limit=2`, "showing 2 of 3") but asserts `H3_EARLIEST_RESUME.format(label="tasks transitioned", shown=2, total=3) in lines`, imported from `test_sdk3_rollup_ties_r15` (importing a sibling test module is the existing idiom — r15 itself imports `_RollupCtx` from `test_rollup_extension`). Two tests, two fixtures (natural vs forced stamps), ONE spelling — which is what "pinned once at the render" meant. The h1/h2/h2-held pins are already single-spelled (audit 4a); leave them.

## S3 — R-12 `snapshot_gc._to_aware_utc`: **no edit — now RULED, with its bound and trigger**

The builder's reason is right and neither branch of RULING-14's rule applies: the script is not an SDK-shape user (it reads through `loremaster`'s own models — `SnapshotSummary`, `DiffEngine`, `SurrealStore` — so Q5's "written for SDK 2.0 result shapes" header would be a false claim), and `_to_aware_utc` is not an S2 coercer: its inputs are TEXT — the operator-typed `--epoch` (a naive epoch meaning UTC is a documented CLI convenience, docstring "a naive value is UTC") and `SnapshotSummary.created_at`, a `str` the manifest renders from an ALREADY-VALIDATED aware datetime (`required_datetime` → `.isoformat()` in `diff.py`), so the naive branch is unreachable from the store by construction, not by belief. Named bound in the function's docstring: *"inputs are CLI text and `SnapshotSummary.created_at` text (aware by construction); re-open trigger: the day `SnapshotSummary.created_at` becomes a `datetime`, route it through `required_datetime` and delete this normaliser's naive branch."* Builder, one docstring; no pin (a docstring bound, LOW).

## S4 — R34 "the store's other rows are intact": **fix now — a served false clause of S1's class, and MY wording (RULING-11 rider 3)**

The refusal knows one value in one row failed; "the store's other rows are intact" asserts what it did not read — under schema drift (a column retyped) every row fails and the text promises health: a false clear in a refusal. The INTENT stays (tell the agent this is not a transport failure, so it does not route around lore). Exact replacement, one string in `required_datetime`:

```
{table} {record} is unreadable: column {column!r} holds {held}, a tz-aware datetime was required — a store-integrity fault on that row, not a connection failure; this call could not be completed, and this read says nothing about other rows — report it with lore_findings
```

Servicer: the two-shape R34 pins (2666ade: `get_task` + `query_tasks` + finding `get`) move to the new text — one spelling (a module constant beside them, as r15 does), RED first. Builder: the string + the docstring sentence that paraphrases it.

## S5 — h2 false-CONSERVATIVE when the cursor holds: **no edit — ruled a named bound**

h2 says the elided messages "are not covered by the next cursor; raise limit on THIS call to see them". When the cursor holds (`= since`) the next call reads the same window — still elided at the same `limit`, so "not covered" stays TRUE; the only omission is a second remedy (raise `limit` on the NEXT call too). An omitted extra option is not "wrong in a way the response did not name" — the stated remedy works in every state. Making h2 state-aware would couple it to `next_cursor`, the coupling S1 just paid for. Trigger: if h2 ever gains a cursor-state branch, it derives from `next_cursor` in the render and keeps one spelling per state.

## S6 — "(id unknown)" on a refused message row: **fix now — one projection token**

`message_activity_since`'s SELECT omits `id` (`seq, grade, body, refs, thread, question, task_id, sender.name AS sender_name, created_at`), so `_row_to_stored_message` passes `row_id=row.get("id") = None` and the refusal cannot name the row. The mapper builds `StoredMessage` from explicit fields (never `**row`), so adding `id` to the projection is safe; `record_text` renders it `message:<key>`. Builder: the token. Servicer: one live pin — a message row whose `created_at` is forced to a string; the rollup's refusal names `message:<key>` (assert the record text, not the absence of a literal). **Class note for the audit, not a scanner:** 20 `required_datetime` callers all pass `row_id=row.get(…)`; a projection that omits `id` is the hole, and `(id unknown)` is its symptom. Rider: the cold audit greps each caller's SELECT for `id` once (a one-off reach check, said out loud); the `'(id unknown)'` arm stays as the loud fallback — deleting it would turn a missing projection into a `None` in served text.

## Shape of the wave
Servicer first: P7, P8 (RED at 672b6d6), the S2 import collapse, the R34 pins on the new text, the S6 pin. Builder second: three strings (h3, R34, the `H3` docstring/comments), one projection token, one docstring bound (S3). Delta re-check limited to these items plus the currency legs that do not start pytest; the targeted set is the r15 file, `test_mcp_server`'s rollup class, the R34 two-shape pins, the message-activity pins. D-2 is settled as the lead states (r_a3_floor16 = ADVERSARY4 R4-10 by name); D-4 rides the owed #25 packet. Nothing here is for the operator beyond the record.
