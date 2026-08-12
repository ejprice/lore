brief-base v13 read
brief project v7 read

# REPORT — fixer-orphans-06b (packet 06b RED_ORPHANED cleanup)

## SUMMARY BLOCK
- **State:** BLOCKED on ONE lead ruling (B2) — 6 of 7 pins GREEN; B2 is a deeper defect the finding mis-scoped.
- Deviation A: the ruled `.fullmatch` fix for `_CADENCE_RE` is behaviorally IDENTICAL to `.match` here (trailing `\s*$` absorbs the newline) — greens the pin but does NOT reject `'≤2m\n'`. Requirement (ii) premise is empirically false. No false "rejected" test added. → FORK 2.
- Deviation B: harness docstring needed BOTH counts updated (importers 53→54 AND callers 35→37), not just 53→54 as the finding stated — the caller count was masked by assertion order. Re-derived live.
- **B2 (render-slot inventory) BLOCKED:** `declared_cadence` is a manifest DOOR whose only render is parse-gated → a forgery token can never reach it (un-observable in Leg 1), and the mis-park pin forbids parking a DOOR SAFE. BOTH finding options blocked. → FORK 1 (needs new instrument plumbing). Finding #368 filed. Concrete proposal in §B2.
- **Packages considered:** none — no mechanism specified (stale-expectation test updates + one 1-token production edit).
- **Reuse ledger:** none — no new reusable symbol introduced (only edited existing pins/docstring + one call-site verb).
- **Graded:** not an audit — this is a builder report. Base sha at report: 3e38a5a (HEAD, clean tree at spawn).
- **Decisions needed:** (1) FORK 1 — approve B2 proposal (§B2) or redirect (BLOCKING: currency check cannot show 0 RED_ORPHANED until B2 greens). (2) FORK 2 — accept cosmetic `.fullmatch` / tighten the anchor / add a truthful behavior pin (non-blocking).
- Receipt pointers: RED baseline §Baseline; GREEN receipts §A/§B1/§B3/§B4; B2 analysis §B2; forks §Forks.

---

## Baseline — all 7 pins RED at HEAD 3e38a5a (contract-first)
Ran the 7 target node-ids: `7 failed, 3 passed, 4 skipped in 9.57s`. The 7 failures:
- `test_anchored_pattern_seam.py::TestNoAnchoredPatternValidatedWithMatch::test_every_anchored_match_use_is_allowlisted` (A1)
- `test_ast_reach_helpers.py::TestSharingProvenByMutation::test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped[test_anchored_pattern_seam.py]` (A2)
- `test_agent_registry.py::TestNoForwardCompatFieldsOnAgent::test_agent_field_set_is_exactly_the_c1_slice` (B1)
- `test_render_slot_inventory.py::…::test_every_served_field_is_driven_with_content_or_justified_safe` (B2)
- `test_retry_seam.py::TestBriefMintSharesTheDriver::test_exhausted_contention_on_the_CREATE_still_burns_no_version` (B3a)
- `test_retry_seam.py::TestEveryCallerRunsTheSameRetryPolicy::test_the_brief_mint_obeys_them_too_end_to_end` (B3b)
- `test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` (B4)

Regression/GREEN run after the mechanical fixes (A + B1 + B3 + B4 + full anchored seam + 5 cadence/overdue regression classes): **42 passed, 4 skipped in 10.91s**.

---

## A — `_CADENCE_RE` `.match` → `.fullmatch` (ruled fix) — pins A1 + A2 GREEN
**Root cause:** `_CADENCE_RE = re.compile(r"^[≤<~=\s]*(?P<value>\d+)\s*(?P<unit>[smhd])\s*$")` at `loremaster/server.py` (in `_parse_cadence_seconds`) was validated with `.match`, which the #210 anchored-pattern seam forbids on a `$`-anchored pattern.

**Fix applied (ruled directive):** `_CADENCE_RE.match(cadence)` → `_CADENCE_RE.fullmatch(cadence)` (one token, `server.py`, inside `_parse_cadence_seconds`). This is an AST-level pin (checks the method NAME, not behavior), so the change greens A1; A2 (the meta-test) was RED only because its consumer A1 was RED, so it greens too. Confirmed: full `test_anchored_pattern_seam.py` GREEN, `TestSharingProvenByMutation` GREEN.

**⚠ Deviation / FORK 2 — the ruling's requirement (ii) premise is empirically FALSE.** The brief ruled `.fullmatch` on the belief it "now REJECTS a trailing-newline input." It does NOT, because THIS pattern ends in `\s*$` (unlike `AGENT_NAME_PATTERN`'s bare `$`), and `\s` matches `\n`, so the trailing `\s*` absorbs the newline. Measured (both directions):
```
'≤2m'    match=Y fullmatch=Y      _parse_cadence_seconds('≤2m')   -> 120
'≤2m\n'  match=Y fullmatch=Y      _parse_cadence_seconds('≤2m\n') -> 120   <-- NOT rejected
'2m\r\n' match=Y fullmatch=Y      (CRLF also absorbed by \s*)
'junk'   match=N fullmatch=N      _parse_cadence_seconds('junk')  -> None
```
For `_CADENCE_RE`, `.match` ≡ `.fullmatch` on EVERY input — they never disagree — so the fix is cosmetic/intent-revealing, not behavior-changing. I did NOT add a test asserting `'≤2m\n'` is rejected, because that assertion is empirically false. See §Forks for options.

Context (why the residual is benign): `_parse_cadence_seconds` is a TOLERANT PARSER (design §B.7 / W1c #360), not an identity guard — `'≤2m\n'` and `'≤2m'` both map to the same 120s (no identity forgery). The raw `declared_cadence` string is stored VERBATIM (never charset-validated; `test_mcp_server.py::TestRegisterPersistsDeclaredCadence` asserts "stored, never normalised") and its render safety is owned by `render_attributed` at `_render_comms_fleet_row` (server.py overdue branch), independent of this parser.

---

## B1 — agent field-set pin — GREEN
**Root cause:** 06a/W1 (#360) added `declared_cadence` to the `Agent` model (`agents.py:275`); the `test_agent_field_set_is_exactly_the_c1_slice` exact-set pin did not include it. Live `Agent.model_fields` = 14 fields (the C1 slice + `status_set_at` #304 + `declared_cadence` #360).
**Fix:** added `"declared_cadence"` to the pin's `expected` set with a comment citing #360 as a deliberate 06a addition (mirrors the existing `status_set_at`/#304 comment). Verified `declared_cadence` is a legitimately-ruled field (register/heartbeat `cadence` param → stored verbatim → drives fleet `overdue` verdict). Pin still fails on any FURTHER unintended field. GREEN.

## B3 — retry-seam brief bodies — GREEN
**Root cause:** two pins publish a brief with a 1–2-word body (`"a body"` / `"body"`); 06a's #257 floor (`BriefBodyTooThinError`, `len(body.split()) < 3`, `briefs.py:642`) rejects them BEFORE the mint, so `pytest.raises(TxnContentionExhaustedError)` saw the wrong exception. (Tests-certify-the-old-world: a semantic change [#257] broke pre-existing fixtures.)
**Fix:** bumped both bodies to `"a standing wave instruction"` (4 real words). The tests' actual assertions (`released` non-empty for B3a; `connection.calls == _MAX_TXN_CONFLICT_ATTEMPTS` for B3b) are unaffected by body text — verified by reading both. GREEN.

## B4 — harness docstring DERIVED counts — GREEN
**Root cause:** my 06b `tests/test_trace_retention_gc.py` both IMPORTS `_surreal_harness` AND calls `connect_admin` (lines 189/222/259/301). The `_surreal_harness` module docstring stated `53` importers and `35` callers.
**⚠ Re-derived (the finding only named 53→54):** live derivation via the pin's own instruments — `_harness_importer_files()` = **54**, `_connect_admin_caller_files()` = **37**. BOTH stale; the caller count (35→37, delta +2) was masked because the importer assertion fires first and pytest stops there. Do NOT trust the inherited "53→54".
**Fix:** docstring `53`→`54` and `35`→`37`. Pin re-derives both, so it confirms. GREEN.

---

## B2 — render-slot inventory (`test_every_served_field_is_driven_with_content_or_justified_safe`) — BLOCKED, FORK 1
**Exact offender:** `_render_comms_fleet_row:7352 serves 'declared_cadence' — a DOOR served but NEVER observed with content — a vacuous drive (the task_id=None class)`.

**Why BOTH finding options are blocked (this is a deeper defect, not a stale-expectation update):**
- `declared_cadence` is classified a manifest **DOOR** on `Agent` (`test_link5_render_containment.py:1729`) — correct, since at storage it is verbatim caller free text.
- Its ONLY driven render is the `_render_comms_fleet_row` **overdue branch** (server.py:7347–7355), which fires only when `_parse_cadence_seconds(row.declared_cadence) is not None` — i.e. only when the value matches the closed cadence charset `^[≤<~=\s]*\d+\s*[smhd]\s*$`.
- **Option "drive it with content" (finding's preferred) is IMPOSSIBLE.** Leg 1 observes a door by looking for its forge token `"Agent.declared_cadence…"` in the served bytes. A forge token contains letters/dots and CANNOT parse as a cadence, so it can never reach this gated render. The probe (test_link5:2490–2497) already exercises the overdue branch — but with `declared_cadence="≤1m"`, which carries no observation token. No probe shape can make the token both parse AND appear.
- **Option "justify it SAFE" is FORBIDDEN.** `TestNoServedSafeFieldIsAManifestDoor` reddens if ANY manifest door is added to `_SERVED_SAFE_FIELDS` (Ruling 2 / #345 mis-park). `declared_cadence` is a door, so SAFE is unrepresentable.
- **Reclassify-to-SAFE is WRONG:** the parse gate still admits a trailing newline (#210), which IS a forgery vector — so the slot genuinely needs CONTAINMENT (it has it: `render_attributed`). A field that needs containment is not "safe" (safe licenses UNCONTAINED rendering, reopening the newline leak).

So `declared_cadence` is a **contained door whose render is value-gated**, a third category the #345 Leg-1 binary (observed-door | safe-uncontained) has no slot for. The finding author (and 06a's manifest comment at test_link5:1734 "driven as a door regardless (over-drive overdue shape)") both assumed the over-drive counts as driving it; Leg-1's token observation does not agree.

**Concrete proposal (ready to apply on approval):**
1. Add a NEW evidence-backed exemption `_PARSE_GATED_DOOR_FIELDS: dict[str, tuple[reason, re_open_trigger]]` in `test_render_slot_inventory.py`, distinct from `_SERVED_SAFE_FIELDS` (so the mis-park pin is untouched), with one entry: `declared_cadence` — reason: "manifest DOOR (verbatim caller text) whose only driven render (_render_comms_fleet_row overdue branch) is gated by `_parse_cadence_seconds is not None`, restricting the rendered value to the closed cadence charset; a forge token cannot parse, so it is un-observable via a token by construction. The residual forgery vector (a trailing newline, #210) is CONTAINED by `render_attributed`." re-open trigger: "the overdue verdict begins rendering declared_cadence outside the parse gate, OR the cadence charset widens to admit a printable forgery char."
2. Add a DEDICATED CONTROL (mirroring `test_the_drain_row_task_id_slot_is_driven_with_content`): construct a fleet row with a hostile-but-PARSEABLE `declared_cadence` (`"≤1m\n"` — the only forgery vector a parseable cadence admits) + `heartbeat_age_s` past the threshold, render `_render_comms_fleet_row`, assert `not _leaks(rendered)` (the trailing newline is contained). This is the REAL proof the gated door is neutralized, replacing the (impossible) token observation.
3. Skip `_PARSE_GATED_DOOR_FIELDS` fields in the Leg-1 main pin's offender loop (alongside `observed`/`_SERVED_SAFE_FIELDS`). Leg 2 (containment) is unchanged and still requires `declared_cadence` to route through `render_attributed`.

This follows the repo's own "WHEN YOU CANNOT CLOSE A HOLE, PIN IT" pattern (evidence + named re-open trigger + a dedicated control). It IS new plumbing in a trust-critical (#345) instrument — hence escalated per the brief's explicit STOP-and-escalate trigger rather than forced. **I can apply it immediately on your GO, or route it to a design sidecar / contract-adversary if you prefer.**

---

## Forks (for the lead)
**FORK 1 (BLOCKING):** B2 — approve the §B2 proposal, or redirect. The wave-close currency check CANNOT show 0 RED_ORPHANED until B2 greens.
**FORK 2 (non-blocking):** A requirement (ii). `.fullmatch` is applied (A1/A2 GREEN) but is behaviorally identical to `.match` here, so `'≤2m\n'` is NOT rejected. Options: (a) **[recommended]** accept the cosmetic/intent-revealing `.fullmatch`, add NO "rejected" test (the residual newline is already contained by `render_attributed`); (b) also add a truthful behavior pin (`_parse_cadence_seconds('≤2m\n') == 120`, documenting the #210 nuance); (c) tighten the trailing anchor (e.g. `\s*$` → `[^\S\n]*$`) so `'≤2m\n'` genuinely returns None — a deliberate 06a-parser behavior change. No new test added pending your call.

---

## Discipline / receipts
- Commit-only: I have NOT run git add/commit/revert. The lead commits; this rides the next deploy.
- Tests hit `spike-surreal :18000` only (throwaway `unique_database()`); `:18500` never touched.
- `git diff --stat` (mechanical fixes only, B2 not yet applied):
```
 loremaster/loremaster/server.py         | 2 +-
 loremaster/tests/_surreal_harness.py    | 4 ++--
 loremaster/tests/test_agent_registry.py | 6 ++++++
 loremaster/tests/test_retry_seam.py     | 4 ++--
 4 files changed, 11 insertions(+), 5 deletions(-)
```
- ruff / typecheck / full currency-check verdict: PENDING (will run after B2 resolves; the currency check is the load-bearing close-out receipt and needs 0 RED_ORPHANED).
