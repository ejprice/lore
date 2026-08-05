# REPORT-contract-fix-04b4-2

brief-base v10 read

## SUMMARY BLOCK
- state: **done** — the dropped R-4 mypy satisfiability rider is closed; whole-repo typecheck has ZERO errors in any file I touched.
- Capability check: lore tools + write test files + `scripts/typecheck.sh` + store — all available/used.
- Packages considered: none — no mechanism specified (one-line test rider).
- Graded: authored HEAD `37d4adc` (my committed contract + fix) · the builder's R-4/#309/#319 work is UNCOMMITTED in the working tree (server.py, +85/−21) · my test_comms_footer.py edit is UNCOMMITTED (lead commits).
- decisions-needed: none — but see the HONESTY FLAG (§3): the pre-existing typecheck red is much larger than "only test_auth_composition.py."
- receipt pointers: the fix §1 · verify §2 · honesty flag §3.

## §1 · The fix (the ONLY change)
The R-4 negative test `test_comms_footer.py::TestTheCommsIdentitySeamHasNoDefaultForNameOrTo::test_omitting_name_and_to_FAILS_LOUD` deliberately calls `AppContext._validate_comms_identities(CALLER_A[0], session=CALLER_A[1])` — omitting `name`/`to` — inside `pytest.raises(TypeError)`, to assert the RUNTIME raise. The builder's R-4 change (removing the `name`/`to` defaults — now live in the working tree; signature reads `name: str | None,` / `to: list[str] | None,` with no `= None`) makes that omission a real mypy `[call-arg]` on this line (×2: missing `name`, missing `to`) — 2 errors the whole-repo `scripts/typecheck.sh` catches but a targeted `mypy server.py` structurally cannot (both adversaries disclosed skipping the whole-repo run).

**FIX:** added `# type: ignore[call-arg]` to that call line, with a load-bearing docstring note. This is the SAME satisfiability rider I used at `test_task_read_surface.py` on `TaskListing(..., total=99)  # type: ignore[call-arg]`, dropped here. It does NOT weaken the pin — the runtime `TypeError` is still asserted; the ignore only tells mypy the bad call is intentional.

**Only ONE line needed it.** Re-scanned: `_validate_comms_identities` is CALLED (omitting name/to) at exactly this one test site; other test references are prose (`:1663`), a string constant (`:1682`), and a docstring-scan iteration over the function object (`:2805`, not a call). No sibling `[call-arg]` from the R-4 change.

## §2 · VERIFY (the lead's criterion)
- `scripts/typecheck.sh`: **ZERO errors in all 5 files I touched** (`test_task_read_surface.py`, `test_comms_footer.py`, `test_mcp_server.py`, `test_task_ledger.py`, `_task_fakes.py`) — `test_comms_footer.py` went from 2 `[call-arg]` errors to 0.
- The ignore is **USED** — no `[unused-ignore]` anywhere (the builder's default-removal is live, so the suppressed errors are real).
- R-4 pins now **2 GREEN** (`test_name_and_to_are_keyword_required_with_NO_default`, `test_omitting_name_and_to_FAILS_LOUD`) — the builder removed the defaults, so the RED went GREEN as designed. `ruff` clean.

## §3 · HONESTY FLAG — the pre-existing red is NOT "only test_auth_composition.py"
Your brief said "only the pre-existing packet-39 `test_auth_composition.py` errors may remain." The ACTUAL remaining set is **191 errors across ~11 files in BOTH the loremaster and lorerunes typecheck legs**, all in the auth/posture/roster cluster — `test_auth_composition.py` (40), `test_permission_resolver_seam.py` (20), `test_hosted_readonly_posture.py` (13), `test_allowlist_roster.py` (10), `test_auth.py` (7), `test_google_token_verifier.py` (7), `test_auth_identity_seam.py` (2), `_auth_fixtures.py` (3), and `lorerunes/tests/{test_roster_parser.py (36), test_posture.py (35), test_email_normalisation.py (18)}`. They are about production symbols `loremaster.config.resolve_posture` / `resolve_secret` / `PostureConfigError`, `lorerunes.Posture` / `SCOPE_READ`, roster/email — an in-progress auth/posture refactor. NONE of these files is one I touched, and NONE of these symbols is affected by the builder's task-surface changes (task display cap, comms identities, tool descriptions), so they are pre-existing and unrelated to 04b4. **My work introduced zero new errors — but the gate is NOT green overall, because that separate pre-existing red remains.** Surfacing so it is not mistaken for a small residual.

## §4 · Scope honesty
- Test-only change (one `# type: ignore` comment + a docstring note). No production edits, no other pin touched.
- No git state changes (lead commits).

There are 191 failing-typecheck errors unrelated to our present scope (the auth/posture/roster refactor cluster). Do you want to examine them more closely?
