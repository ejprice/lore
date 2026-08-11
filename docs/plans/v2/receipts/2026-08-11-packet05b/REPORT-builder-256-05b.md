brief-base v11 read
brief project v7 read

# REPORT-builder-256-05b — BUILDER for #256 (`lore_findings action=annotate`)

Model attestation: **claude-opus-4-8** (Opus 4.8), pinned by the `opus48-worker` frontmatter (`model:` key).
Role: BUILDER (production code only). I did NOT touch any test — the contract is FROZEN law.

## SUMMARY BLOCK
- receipt: `brief-base v11 read` · `brief project v7 read`
- state: **done** — the FROZEN #256 contract greens end to end. FULL affected suite
  **1188 passed / 1 skipped / 0 failed** under `-n auto`; `ruff` clean; `scripts/typecheck.sh`
  contributes **ZERO** new errors from my two files (the 102 `loremaster` errors are the
  pre-existing auth-WIP `test_auth_composition.py` baseline).
- deviations: none. Writable set honoured exactly: `loremaster/loremaster/findings.py` +
  `loremaster/loremaster/server.py` ONLY (`git diff --stat` = 2 files; no other production `.py` touched).
- Capability check: full tool access; lore MCP loaded (`ToolSearch "+lore"`); test store spike-surreal
  `:18000` UP (systemd `active`, port open). No blocking gaps. Brief fully satisfiable.
- Packages considered: **`lorerunes.is_blank` — REUSE (verdict `replace` of a hand-rolled blank check).**
  READ: `lorerunes/lorerunes/blankness.py::is_blank` (`return not value or not value.strip()`) — the ONE
  shared "what counts as blank?" predicate `report`/config use. `annotate`'s note guard CALLS it (bare
  `from lorerunes import is_blank`, the house idiom in `config.py`), never a hand-rolled `strip`. No
  third-party mechanism specified.
- Graded: **n/a** — I am a BUILDER shipping code, not rendering a verdict on another artifact. Built against
  HEAD `299e69a` (working tree = `299e69a` + the frozen contract's uncommitted test edits + my 2-file build).
- decisions-needed: **none.**
- receipt pointers: shared shell = `findings.py::FindingLedger._guarded_append_fragment` (`_transition_fragment`
  delegates); verb = `findings.py::FindingLedger.annotate`; dispatch = `server.py::AppContext.findings`
  (`_FINDING_ACTION_ANNOTATE` branch, `_render_finding_detail`, `writes=1`); descriptions = the served
  `lore_findings` tool-`description` string + the `note`-param `Field`; green run = §Verification; F2
  mutation-pin pass = §F2 share-by-mutation; store law = `docs/reference/surrealdb-31-capabilities.md` §2
  (server-side `+=` append, silent-no-op enemy), §5 (hot-row ≥8-way overlapping lifetimes).

---

## What I built (the documented reference shape, implemented independently)

### `findings.py` — the SHARED guarded-append shell + the verb
1. **Extracted `_guarded_append_fragment(finding_id, event, *, status_target=None, expected_from=None)`**
   — the ONE guarded, THROW-on-zero-rows, server-side-append CAS shell (`provenance.events += [$event]`
   inside `LET $tr_updated = (UPDATE … ) … IF array::len($tr_updated) == 0 { THROW … }`). The two
   OPTIONAL keyword guards are exactly what a transition ADDS and an annotate DROPS: `status_target` →
   the `status = $` SET; `expected_from` → the `WHERE status = $expected_from` compare-and-set predicate.
2. **`_transition_fragment` now DELEGATES** to it (`status_target=target, expected_from=expected_from`) —
   it does NOT clone. The composed transition SQL is **byte-identical** to before (status SET first, then
   append, then WHERE), which is why every pre-existing transition/concurrency pin in `test_findings.py`
   stayed green (188/188 in-file). Sharing is the point: F2 forbids a byte-identical clone.
3. **`annotate(id_or_number, actor, note: str | None) -> Finding`** (placed after `wontfix`):
   - reject `None`/blank note via **`is_blank`** (`if note is None or is_blank(note): raise ValueError(...)`)
     BEFORE any resolve/write — R3 reuse, pin 6 behaviour;
   - `_resolve_or_raise(id_or_number)` (pin 5 — raises `FindingNotFoundError`, never a silent no-op);
   - build event `{actor, action:"annotate" (`_ACTION_ANNOTATE`), at, note}` with **NO `to`/status key**
     (pin 3 / #104 — nothing for a render to fabricate a `-> status` arrow from);
   - `_apply([self._guarded_append_fragment(finding_id, event)])` — `status_target=None`/`expected_from=None`,
     so status is UNCHANGED in EVERY state (pin 1) and the WHERE-less append always matches the addressed
     row and rides the shared retry driver, so 8-way concurrent annotates lose ZERO events (pin 4);
   - belt-and-braces `except SurrealStoreError` re-select → `FindingNotFoundError` on a vanished row
     (mirrors `_transition`'s discipline; findings are never hard-deleted, so defensive — surface, never swallow);
   - re-select + `_row_to_finding`.
   - Added `_ACTION_ANNOTATE = "annotate"` next to `_ACTION_TRANSITION`; added `annotate` to the module
     public-surface docstring (hygiene).

### `server.py` — the served surface
- `_FINDING_ACTION_ANNOTATE = "annotate"` + its `_FINDING_ACTIONS` entry **in dispatch order** (after
  `wontfix`, before `resolve_many`) — matches `test_task_read_surface.py::_EXPECTED_FINDING_ACTIONS`.
- Dispatch branch in `AppContext.findings`: `finding_ledger.annotate(_require_finding_ref(id_or_number),
  _require_finding_arg(actor,"actor"), _require_finding_arg(note,"note"))`, rendered via
  **`_render_finding_detail`** (NOT `_render_finding_transition` — S2/#104: no fabricated "transitioned
  to"), **`writes=1`** (F3 → footers via the existing `_with_comms_footer`). `_require_finding_arg(note,
  "note")` makes the served `note` REQUIRED+non-blank with a message naming `'note'` (S3).
- Widened the served **`lore_findings` tool-`description` string** to name `annotate` (F4 teaches pin —
  keyed on `tools["lore_findings"].description`, the SEPARATE registered string, not the docstring).
- Widened the **`note`-param `Field` description** to name `'annotate'` and tell the truth (REQUIRED for
  annotate, OPTIONAL on the transitions) — the derived recorder pin
  `test_the_finding_note_description_names_every_action_that_RECORDS_it` now derives
  `{acknowledge, resolve, wontfix, annotate}` from the dispatcher and each is named. Removed the now-false
  "Ignored by the other actions" (annotate records it — that would be a #319 served lie).

## WRONG builds avoided (all adversary-caught — shipped NONE)
status-flip via `_transition` · state-machine loosening · client-side read-modify-write of whole
`provenance` · fabricated `→status` via `_render_finding_transition` · **byte-identical CLONE of the shell
(I SHARE via delegation — F2 pin proves it)** · `writes=0` · blank note accepted · hand-rolled blankness.

## Verification (receipts)

### FULL affected suite, `-n auto` — the brief's gate
```
uv run python -m pytest -q -n auto \
  loremaster/tests/test_findings.py loremaster/tests/test_mcp_server.py \
  loremaster/tests/test_task_read_surface.py loremaster/tests/test_comms_footer.py
→ 1188 passed, 1 skipped in 104.60s (0:01:44)
```
(The 1 skip is pre-existing, unrelated to annotate. 1188 matches the adversary's SUFFICIENT
reference-build figure.)

### Key load-bearing pins (verbose, real store)
```
TestAnnotateRidesTheGuardedAppendSeam::test_mutating_the_shared_shell_reddens_both_annotate_and_transition PASSED
TestAnnotateRidesTheGuardedAppendSeam::test_annotate_and_transition_emit_the_same_guarded_append          PASSED
TestConcurrentAnnotate::test_concurrent_annotates_lose_no_events[real]                                    PASSED
TestConcurrentAnnotate::test_concurrent_annotates_lose_no_events[fake]                                    PASSED
TestAnnotateRidesTheGuardedAppendSeam::test_annotate_reuses_the_shared_blankness_predicate_...            PASSED
→ 5 passed in 1.14s
```
- New annotate ledger classes (TestAnnotate/Concurrent/RidesSeam/HostileNote): **37 passed** (real+fake).
- Served pins (S1/S2/S3×4 + F4 teaches + recorder pin): green inside the full-suite run.

### F2 — SHARING PROVEN BY MUTATION (not by inspection)
The committed pin `test_mutating_the_shared_shell_reddens_both_annotate_and_transition` monkeypatches the
ONE shell `FindingLedger._guarded_append_fragment` to inject a sentinel into its composed statement, then
asserts the sentinel reaches **BOTH** annotate's AND a transition's captured `_apply` SQL. It **PASSES on my
build** — annotate routes through the shared shell (both `annotate` and `_transition_fragment` look
`_guarded_append_fragment` up on the class at call time, so mutating the one shell reddens both). The
opposite leg is the adversary's: a byte-identical CLONE reddens this pin (REPORT-adversary-256-05b.md
§DELTA RE-GRADE F2). Both directions ⇒ sharing is a CHECKED variable, per brief-base §6 / ONE-IMPLEMENTATION.

### Gates
- `uv run ruff check .` on the two files → **All checks passed!** (auto-fixed one isort ordering of my
  `from lorerunes import is_blank` — `lorerunes` sorts after `loremaster` as a workspace sibling).
- `scripts/typecheck.sh` → `loremaster` reports **102 errors, ALL in `test_auth_composition.py`** (the
  auth-WIP baseline: `resolve_posture`/`derive_edge_policy`/`SCOPE_READ`/`Posture`/`PostureConfigError`).
  Grep of the output for `loremaster/loremaster/{findings,server}.py:` → **ZERO** hits. My two files add no
  new mypy errors (ZERO-NEW confirmed; 102 == the contract's documented baseline).

### Diff scope
`git diff --stat` → `findings.py` (+162/−…), `server.py` (+29/−…); no other production `.py` modified.

## R1 fix (cold-audit blocker — applied post-audit, scope widened by lead)
The cold audit (`REPORT-cold-audit-05b-batch1.md` §BLOCKER-256) found ONE blocker: `annotate` is an
UNREGISTERED guarded-CAS door → `test_retry_seam.py::…test_the_door_enumeration_matches_the_canonical_set`
RED → currency RED_ORPHANED. It was outside my original scoped set (`test_retry_seam.py` was in neither my
run nor my writable set), so my 1188-green did not see it. The lead widened my writable set to include
`loremaster/tests/test_retry_seam.py`. The audit's proven 2-part fix (+ R4, + R3), applied verbatim:
- **Part 1 (prod `findings.py`):** the door-scanner's `has_guard` only counts a bare-`ast.Name` `except`
  type; my combined `except (SurrealConnectionError, TxnContentionExhaustedError):` is an `ast.Tuple` →
  read as `has_guard=False`. **Reshaped into two separate single-name clauses** (matching `_transition`'s
  canonical shape) — functionally identical (both re-raise), now the scanner sees the guard.
- **Part 2 (test `test_retry_seam.py`):** registered the fifth door
  `"findings.py::annotate": "FindingNotFoundError — a row that vanished (defensive)"` in the canonical
  `_GUARDED_CAS_DOORS` set (a deliberate, reviewer-visible entry — exactly what the invariant demands).
- **Part 3 / R4 (test):** added `findings.py::annotate` to the hardcoded behavioral list in
  `test_the_transactional_doors_never_re_read_after_exhaustion` (behavioral coverage of the new door:
  its `except TxnContentionExhaustedError` body is a bare `raise`, re-reads nothing).
- **R3 (prod prose):** widened the `note`-param "ignored by" list to name the batch edges
  `resolve_many`/`acknowledge_many` (they carry per-item notes via `items`), so the served surface is honest.

Receipts (self-verify per lead checklist):
- `uv run pytest loremaster/tests/test_retry_seam.py -n auto` → **564 passed / 0 failed** (the door
  enumeration, the `[findings.py::annotate]` guard param, and the `[findings-annotate]` behavioral param all
  green). ⚠ +2 vs the lead's 562 estimate = the guard test's new `findings.py::annotate` param (Part 2) +
  the behavioral test's new `findings-annotate` param (R4/Part 3), both PASSING.
- `scripts/pending_contract_gate.py --currency` → **`CURRENCY : PASS — every claimed gate is GREEN or
  OWNED`**, EXIT=0, **ZERO RED_ORPHANED** (typecheck 191 / pytest 444 residuals RED_ADJUDICATED to packet 39).
- #256 affected suite re-run (guard reshape must not regress) → **1188 passed / 1 skipped / 0 failed**.
- ruff clean on all 3 files; `scripts/typecheck.sh` → **0 errors in `findings.py` / `server.py` /
  `test_retry_seam.py`** (102 loremaster + 89 lorerunes errors are the auth-WIP baseline).

Final diff scope: `loremaster/loremaster/findings.py` + `loremaster/loremaster/server.py` +
`loremaster/tests/test_retry_seam.py` (the lead-widened set). Idle-gate files untouched.

## Notes / flags surfaced (scope law)
- **None open.** The adversary's two LOW residuals on the R3 pin (aliased-import false-RED; cosmetic
  `is_blank(...)` proxy false-GREEN) do not bite my build: I use the bare house idiom `is_blank(note)` as
  the ACTUAL guard, so R3 passes for the right reason. No aliasing; the call gates the write.
