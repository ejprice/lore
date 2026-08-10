# REPORT-cold-audit — defect-class-prevention 8-packet build

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK

- **VERDICT: NO-GO** — the build introduces **15 NEW test failures** over the #333 auth-WIP
  baseline, all from ONE root cause: the new `partition_tools_by_posture` (packet C / #291)
  trips the exec-seam scanner at `loremaster/loremaster/server.py:9477`.
- state: done (independent cold audit; I did not build, fix, or commit)
- Graded: working tree over `003a337` · HEAD-at-report: `003a337` · SAME
- **Root cause (one line):** the new function's local variable `annotations` (server.py:9476)
  shadows the module's `from __future__ import annotations` import, so `getattr(annotations,
  "readOnlyHint", None)` at :9477 reads to the `_deny_namespace_doors` AST scan (#125/#131) as
  `getattr(<imported-module>, …)` — a namespace-door escape. Fix is a one-line rename.
- Gate counts: typecheck **FAIL** (191, all #333) · ruff **CLEAN** · pytest **459 failed / 9567
  passed / 44 skipped / 3 xfailed** · currency **FAIL** (pytest RED_ORPHANED ×15).
- Baseline delta (the load-bearing number): **OUR-NEW-FAILURES = 15** (bar is 0).
- All 8 packets' OWN contracts are GREEN (zero defect-class test files in the failure set).
- Mutation spot-check: **5/5 pins discriminate** (#348/B, G/#344, C/#291, F/#279 both callers,
  A-SUB adopters+coverage) — provenance asserted inside the scratch copy.
- Diff-honesty: **clean** — no re-introduced defect / over-claim in the reviewed surfaces; the
  D/#346 docstring in fact *corrects* a prior over-claim.
- Deviations verified: **5/5 sound** (store re-export · A-SUB `_sdk_guard` generalization ·
  test_link5 158/0 · comms dead-entry · test_blocks_edge F5-granted edit).
- Packages considered: none — no new mechanism specified; this is an audit.
- decisions-needed: the fix is trivial and known (§7). Operator/lead call whether the fix wave
  also re-runs a full currency before commit — I recommend yes (§7).
- receipt POINTERS: gate counts §1 · baseline delta + NEW-failure proof §2 · diff-honesty §3 ·
  mutation spot-checks §4 · deviations §5 · the fix §7. Instruments: junit at
  `/tmp/cold-audit/full-suite.xml`; scanner repro pasted verbatim §2.

---

## 1. Gate counts (re-run from scratch, working tree over HEAD `003a337`)

| gate | command | result |
|---|---|---|
| typecheck | `./scripts/typecheck.sh` | **FAIL** — 191 mypy errors, ALL in auth/posture files |
| ruff | `uv run ruff check .` | **CLEAN** — `All checks passed!` (exit 0) |
| pytest | `uv run pytest -q -n auto --junit-xml=…` | **459 failed, 9567 passed, 44 skipped, 3 xfailed** in 376.93s (exit 1) |
| currency | `uv run python scripts/pending_contract_gate.py --currency` | **FAIL** (exit 1) |

**typecheck breakdown** (per-leg, from the runner):
- `lorerunes` FAILED — 89 errors in 3 files: `test_roster_parser.py` (36), `test_posture.py` (35),
  `test_email_normalisation.py` (18) — all posture/roster (#333).
- `loremaster` FAILED — 102 errors in 8 files: `test_auth_composition.py` (40),
  `test_permission_resolver_seam.py` (20), `test_hosted_readonly_posture.py` (13),
  `test_allowlist_roster.py` (10), `test_google_token_verifier.py` (7), `test_auth.py` (7),
  `_auth_fixtures.py` (3), `test_auth_identity_seam.py` (2) — all auth (#333).
- `lorescribe` OK · `loresigil` OK · `skills` OK · `docs/eval` OK · **`scripts` OK** (all
  defect-class scripts — `wave_gate.py`, `_harness_guards.py`, `_newline_matrix.py`,
  `wrong_builds.py`, `pending_contract_gate.py`, `forgery_door_sweep.py` — typecheck clean) ·
  `shellcheck` OK.
- Total 89 + 102 = **191**, matching the ~191 #333 baseline exactly; NONE in a defect-class file.
  Zero NEW mypy failures.

**currency verdict:**
```
typecheck    RED_ADJUDICATED — 191 residual(s), owned by: packet-39-pending-build (…trigger: #296 / pkt39 build start)
ruff         GREEN
pytest       RED_ORPHANED — 15 residual(s) with NO owner
CURRENCY   : FAIL — RED with nobody's name on it: pytest
```
Currency behaved correctly: it adjudicated the 191 typecheck + 444 auth-pytest residuals to
packet 39, and surfaced exactly the **15 unowned pytest orphans** as RED_ORPHANED. This is the
#306/#312 instrument catching the regression on its own.

---

## 2. BASELINE DELTA — the load-bearing check (NO-GO here)

459 pytest failures group into 13 files. Ten are the #333 baseline; three are NEW.

| # failures | file | classification |
|---|---|---|
| 81 | `test_auth_composition.py` | #333 auth ✓ |
| 75 | `test_google_token_verifier.py` | #333 auth ✓ |
| 70 | `lorerunes/…/test_posture.py` | #333 posture ✓ |
| 57 | `test_hosted_readonly_posture.py` | #333 posture ✓ |
| 46 | `test_allowlist_roster.py` | #333 auth ✓ |
| 37 | `lorerunes/…/test_roster_parser.py` | #333 auth ✓ |
| 25 | `test_auth.py` | #333 auth ✓ |
| 21 | `lorerunes/…/test_email_normalisation.py` | #333 auth ✓ |
| 18 | `test_auth_identity_seam.py` | #333 auth ✓ |
| 14 | `test_permission_resolver_seam.py` | #333 auth ✓ |
| **7** | **`test_shellout_allowlist.py`** | **NEW — this session** |
| **6** | **`skills/lore-deploy/tests/test_workspace_probe.py`** | **NEW — this session (cascade)** |
| **2** | **`test_shellout_seam_perimeter.py`** | **NEW — this session** |

- Auth/posture subtotal: 81+75+70+57+46+37+25+21+18+14 = **444** = exactly the #333 baseline.
- **OUR-NEW-FAILURES = 7 + 6 + 2 = 15** (the bar is **0**).
- No defect-class test file appears in the failure set — all 8 packets' own contracts are GREEN.

### 2.1 The single root cause of all 15

Every one of the 9 `test_shellout_*` failures raises the identical error, and the 6
`test_workspace_probe` failures cascade from it (`required_binaries()` invokes the same scan):

```
loremaster.shellout.UnresolvedExecSiteError: loremaster/loremaster/server.py:9477:
reaches into the NAMESPACE of the imported module 'annotations' via getattr() —
which can hand out a spawner without ever naming one (findings #125/#131)
```

`server.py:9477` is inside the new `partition_tools_by_posture` (packet C / #291):
```python
9476        annotations = getattr(tool, "annotations", None)
9477        read_only_hint = getattr(annotations, "readOnlyHint", None) if annotations else None
```
The local `annotations` (9476) shadows the module-level `from __future__ import annotations`.
The exec-seam scan `_deny_namespace_doors` is NAME-based (it cannot tell a local from the import),
so `getattr(annotations, …)` at 9477 reads as a namespace-door escape — exactly the "honest
developer trips the exec-seam gate" class the gate exists to catch (CLAUDE.md: *a gate needs a
threat model — the exec-seam gate catches the honest developer, #131 verbatim*).

### 2.2 Proof it is NEW, not pre-existing (scanner run against HEAD vs working tree)

```
=== HEAD (committed 003a337) ===
  'annotations' in imported names: True
  _deny_namespace_doors: CLEAN (no raise)
=== WORKING TREE (this session's build) ===
  'annotations' in imported names: True
  _deny_namespace_doors: RAISED -> loremaster/loremaster/server.py:9477: reaches into the
  NAMESPACE of the imported module 'annotations' via getattr() … (findings #125/#131)
```
(Repro: `git show HEAD:loremaster/loremaster/server.py` → `ast.parse` → `shellout._deny_namespace_doors`
vs the same over the working-tree file. HEAD is clean; the working tree raises at the new line.)
I could not `git stash` to prove this by re-run (git-mutation forbidden by brief-base §2), so I
reproduced the scan's decision on both source versions directly, which is dispositive.

---

## 3. Diff-honesty verdict — CLEAN (no re-introduced defect / over-claim)

Reviewed every production/harness surface in the working-tree diff; all are honest:

- **#348 fleet-row `task_id` → `render_attributed`** (server.py `_render_comms_fleet_row`, ~line
  7061): confirmed routed through `render_attributed`, NOT `safe_str`. Docstring states the DOOR
  provenance (caller free text) correctly; the `blocked_by` docstring (~4628) is upgraded from a
  fragile "repr() saves us" claim to "render_attributed is PRIMARY containment" — an honesty
  improvement, not an over-claim.
- **G "SCOPED RUN" flag** (`scripts/wave_gate.py`): a `--wave <selector>` run renders the pytest
  gate `SCOPED — ran … (N tests); NOT a currency clear`, never GREEN, and appends a `SCOPED RUN —
  … does NOT certify the full gate` trailer; `--wave` with no selector is an argparse error
  (`nargs="+"`); zero-collection surfaces as `BrokenInstrumentError` → exit 2 (never swallowed).
  The old `--checkpoint` mode is removed (an unrecognised arg errors). Un-mistakable for a full pass.
- **Corrected docstrings state exactly what is covered** — no over-claim/stale prose:
  - **D/#346** (`test_refusal_observes_effect.py` + `_refusal_effect.py`): the R4 docstring
    *corrects* an over-claim — R4 removes only the DIRECT `.mcp` handle; the `call.__self__.mcp`
    back-door is closed by R16 (receiver-blind scan), "the two legs together cover the door;
    neither alone does." This is the audit-desired direction (a shipped over-claim would be the
    defect).
  - **A-SUB** (`_logging_fixtures.py`): `parse_production_trees` / `assert_scan_reached_every_member`
    / `install_parse_guard` docstrings state the #349/#351 bounds explicitly; `install_parse_guard`
    honestly refuses to certify blindness (`require_observations`, #136).
- **`partition_tools_by_posture` is the single source** — the old `_MUTATING_TOOLS` /
  `_READ_ONLY_TOOLS` hand-lists in `test_mcp_server.py` are RETIRED; the suite derives both
  partitions via `derive_tool_postures → partition_tools_by_posture`. Deny-by-default
  (`readOnlyHint is not True`) is in the production helper. No drifted hand-list remains.
- **`_txn_coroutines` is one derivation** — `store/_txn.py` defines it; `store/__init__.py`
  re-exports it; `forgery_door_sweep.store_seams` / `public_coroutines_not_swept` / `seam_bindings`
  and `test_blocks_edge._degrade_every_STORE_seam` all route through it (mutation-proven, §4).
- **`_currencies_for` extraction** (`pending_contract_gate.py`): the per-gate verdicts are one
  derivation both `_render_currency` and `wave_gate.main` consume — no second copy deciding
  green-or-owned.
- **comms dead-entry removed** (`test_comms_promise_registry.py`): the `{}…` `safe_str` literal is
  no longer emitted (task_id moved to `render_attributed`), so its `_SAFE_STR_PROMISE_FREE` entry
  is correctly removed with a reason.

---

## 4. Mutation spot-check — 5/5 pins discriminate

Blessed scratch (`./scripts/scratch_copy.sh /tmp/cold-audit/scratch`), provenance asserted:
`loremaster.__file__ → /tmp/cold-audit/scratch/loremaster/loremaster/__init__.py` (#140 satisfied).
Each: mutate the production line → run the pin → confirm RED → restore.

| pin | mutation | result |
|---|---|---|
| **#348 / B** | fleet-row `task_id` `render_attributed`→`safe_str` | RED — `test_render_slot_inventory::…test_every_uncontained_served_field_is_justified` names `_render_comms_fleet_row:7066 serves 'task_id' UNCONTAINED` |
| **G / #344** | neuter the SCOPED-not-GREEN override in `wave_gate._render` | RED — `test_wave_gate::test_scoped_receipt_is_unmistakably_scoped` (`PYTEST GREEN` on a scoped run) |
| **C / #291** | flip `_TASK_TOOL_ANNOTATIONS` `readOnlyHint` False→True | RED — `test_mutating_set_derivation::test_the_known_mutating_tools_are_in_the_mutating_partition` (lore_tasks/lore_claim_task leave the derived mutating set) |
| **F / #279** | break `_txn_coroutines` core `__module__` match | RED — 18 pins across BOTH callers (store_seams door pins + seam_bindings + `_degrade` wide-set + surface-equality) |
| **A-SUB** | force `parse_production_trees` to drop `scripts` | RED — `assert_scan_reached_every_member` ("declared-not-scanned: ['scripts']"), the adopter `test_anchored_pattern_seam::TestScanCoverage`, AND the substrate's own `TestSharingProvenByMutation` |

F and A-SUB confirm SHARING by mutation (not routing): a change to the shared core reddens every
caller together, exactly the DRY proof the design required.

---

## 5. Disclosed deviations — 5/5 sound

1. **`store/__init__.py` re-exports `_txn_coroutines`** — sound. It is the operator-ruled home (b)
   for the ONE derivation at the package level (`loremaster.store._txn_coroutines`), imported by
   both `forgery_door_sweep` and `test_blocks_edge`. Package `__init__` was previously empty;
   `from ._txn import _txn_coroutines as _txn_coroutines` is a clean re-export.
2. **A-SUB guard generalizes `_sdk_guard`** — sound. `install_parse_guard` mirrors
   `_sdk_guard.install` (plain-`def` wrapper so the stack walk happens at CALL time, arm-time
   `_require_parse_root_runs` precondition, shared `GuardCannotSubstantiate` #136 type,
   `require_observations` blindness-refusal). Generalizes the SDK-connection primitive to
   `builtins.compile`; spelling/alias-agnostic by construction.
3. **`test_link5_render_containment.py` edits (claimed 158/0)** — sound; passed in the full suite
   (not in the failure set). The substantive change is the #348 ROOT fix: `Agent.task_id` and
   `Message.task_id` moved SAFE→DOOR (they were mis-classified "system id"; they are caller free
   text), and `_forge` now drives `Agent.task_id` with a forgery token instead of the hardcoded
   `task_id="tid12345"` — the literal #345 "hardcoded driver param" artifact, removed.
4. **`test_comms_promise_registry` dead-entry fix** — sound (§3).
5. **`test_blocks_edge._degrade_every_STORE_seam` (F5-granted closed-file edit)** — sound. Now
   derives from `_txn_coroutines` intersected-by-identity with `loremaster.tasks` bindings (not a
   second private walk), and adds `assert "bootstrap_session" in patched` (the WIDE-only seam). The
   F5 ruling explicitly granted this closed file in the writable set; mutation-proven (§4, F row).

---

## 6. Scope / observations surfaced (nothing narrowed)

- The 15 new failures are collateral: they are NOT in defect-class files, but they ARE caused by a
  defect-class production module (`server.py`, packet C). The bar is "zero NEW failures", so this
  is a NO-GO regardless of which file surfaces the red.
- The irony is instructive and worth the operator's eye: a *defect-class-prevention* session was
  caught by the exec-seam gate doing exactly its stated job (#131 — the honest developer adds a
  reach the image-binary scan can't vouch for). The gate is not buggy; the local variable name is.

---

## 7. The fix (known, trivial, verified) — for the fix wave, NOT applied here

**Rename the local `annotations` so it no longer shadows the `from __future__ import annotations`
import** in `partition_tools_by_posture` (server.py 9476–9477), e.g. `tool_annotations`:
```python
        tool_annotations = getattr(tool, "annotations", None)
        read_only_hint = getattr(tool_annotations, "readOnlyHint", None) if tool_annotations else None
```
Verified: with this rename, `_deny_namespace_doors` over the working-tree `server.py` goes CLEAN
(no raise). One-line-per-occurrence, mechanical, no logic change.

- **Do NOT "fix" it by allowlisting `server.py` in the exec-seam scanner** — that weakens exactly
  the gate that just worked (server.py is a plausible future host of a real shell-out). The insult
  here is a bad variable name, not honest code the gate should tolerate.
- **After the rename, re-run currency** (`pending_contract_gate.py --currency`) and confirm pytest
  returns to RED_ADJUDICATED-only (no RED_ORPHANED) before commit. The rename touches only pytest's
  scanner path; a targeted re-run of `test_shellout_allowlist.py test_shellout_seam_perimeter.py
  skills/lore-deploy/tests/test_workspace_probe.py` should go 0-failed, and the full currency then
  reduces to the #333-adjudicated baseline.
- This is inside the packet-C writable set (server.py was already edited by this build), so it is a
  fix-in-place, not a scope fork.

---

## 8. Housekeeping

- A blessed scratch copy remains at `/tmp/cold-audit/scratch` (disposable `cp -a`, not a git
  worktree). My `rm -rf` was permission-denied; operator may remove it. It is a copy of the
  working-tree build, harmless.
- Gate artifacts under `/tmp/cold-audit/` (junit XML `full-suite.xml`, per-gate logs). The
  scanner-repro and each mutation are re-runnable from the descriptions above; nothing load-bearing
  lives only in a lost tool.

**Graded: `003a337` (working tree over it) · HEAD-at-report: `003a337` · SAME.**
