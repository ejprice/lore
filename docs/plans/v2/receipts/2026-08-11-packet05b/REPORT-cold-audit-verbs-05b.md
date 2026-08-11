brief-base v12 read
brief project v7 read

# REPORT-cold-audit-verbs-05b — COLD AUDIT of #174 (supersede blocked_by) + #262 (register liveness notice)

## SUMMARY BLOCK
- receipt: `brief-base v12 read` · `brief project v7 read`
- role: COLD AUDITOR (Opus-4.8, `opus48-worker` frontmatter-pinned — **attest**). FRESH CONTEXT, REFUTE posture. I graded the DIFF, not the builder's report. I edited NO code/tests.
- state: **done** — verdict rendered.
- **VERDICT: GO** — with ONE should-fix served-English residual (R1) recommended for this same diff (one-line description edit, not trust-fatal).
- deviations: none (read-only audit; report is my only writable file).
- Packages considered: **none** — an audit specified/built no mechanism; my mutation instruments are stdlib `sed`/`pytest`, pasted verbatim in §PROBE 1.
- Reuse ledger: none (I introduced no reusable symbol).
- Graded: `c0071cd` (uncommitted working-tree diff ON TOP of it) · HEAD-at-report: `c0071cd` · **SAME**.
- decisions-needed:
  - **R1 fix-or-defer (recommend FIX now):** the `lore_tasks` `blocked_by` tool-param description (server.py:10320-10323) still scopes to `'create'` — #174 made it functional for `'supersede'` too. Fold the one-line fix into this diff, or ledger a deferral with a trigger.
- receipt pointers: gates §GATES; per-feature §FEATURE VERDICTS; probes §PROBES; residuals §RESIDUAL TABLE; mutation instrument §PROBE 1.
- delivery: durable = `lore_comms` → lead-05b (§1 micro-format); this report is the record.

---

## SCOPE GRADED (the uncommitted working-tree diff, HEAD `c0071cd`)
Production: `loremaster/loremaster/{tasks.py, server.py, agents.py}`.
Contract (frozen): `test_blocks_edge.py`, `test_comms_register_notice.py`.
Test-support deviations (disclosed D1/D2/D3): `_task_fakes.py`, `test_link5_render_containment.py`, `_surreal_harness.py`.
Excluded (committed): idle-gate `a52576f`, #256 `c0071cd`.
Scratch provenance (per #140): `loremaster.__file__ -> /tmp/scratch-verbs-05b/loremaster/loremaster/__init__.py` (scratch_copy.sh asserted, exit 0).

---

## GATES (independent re-run — my instrument, not the builder's claim)

| gate | command | result |
|---|---|---|
| Frozen 26-contract | `pytest test_comms_register_notice.py TestSupersedeCarriesBlockedBy174 …INHERITS_predecessor_blocked_by -n auto` | **26 passed** in 6.62s ✓ |
| retry seam | `pytest test_retry_seam.py -n auto` | **564 passed** ✓ (no new guarded-CAS door — see below) |
| currency | `pending_contract_gate.py --currency` | **PASS — 0 RED_ORPHANED** (typecheck 191 + pytest 444 RED_ADJUDICATED, owned packet-39/#333) ✓ |
| typecheck | `scripts/typecheck.sh` | RED, but **ZERO-NEW vs #333** — 191 errors reproduced EXACTLY (102 loremaster + 89 lorerunes), all in the 11 auth/posture/roster files #333 enumerates, **NONE in our 8 touched files** ✓ |
| ruff | `uv run ruff check .` | **All checks passed** ✓ |
| no-regression | `test_comms_footer test_link5_render_containment test_render_seam_pins test_mcp_server test_task_read_surface test_task_ledger test_agent_registry -n auto` | **1583 passed, 1 skipped** ✓ |

**No-new-guarded-CAS-door — INDEPENDENTLY confirmed (not taken from the builder):** the ONLY new `except` clause the production diff adds is `except TaskNotFoundError:` in `_holder_liveness_notice` — a control-flow catch that renders a "not found" note, NOT an `except SurrealStoreError`-that-re-reads door. The two new store reads (`get_task`, `resolve_holder`) route through the existing `_query`/`execute_transaction` seams that already ride the retry driver, so `test_retry_seam.py`'s SDK-call-site coverage stays at 564 with no `_GUARDED_CAS_DOORS` widening. ✓

---

## FEATURE VERDICTS

### #174 supersede-carries-blocked_by — **PASS**
- `TaskLedger.supersede_task` gains a `blocked_by` sentinel (None=INHERIT predecessor's / []=CLEAR / [ids]=REPLACE, deduped order-preserving). Resolution matches `create_task`'s own normalisation (`list(dict.fromkeys(...))`), verified by reading both (tasks.py `supersede_task` vs `create_task`).
- Runs the SAME two shared pre-checks over the RESOLVED deps: `_reject_unusable_blockers` (→ `reject_unknown_rows`, phantom/superseded refusal) + `_refuse_a_cycle`, PLUS a dedicated self-ref guard (see PROBE 1). Then `_new_task_content(..., dependencies, ...)` and `_relate_fragment` appended to the SAME `_supersede_fragment` CAS `_apply` (RELATE AFTER the successor CREATE; `blocks` is `ENFORCED` from birth, schema line 1267). Atomic — loser's whole txn (stamp+CREATE+RELATEs) rolls back → zero orphan edges (PROBE 6).
- Server: `_TASK_ACTION_SUPERSEDE` threads `blocked_by` to the ledger, reads the successor BACK via `get_task` (authoritative resolution, not the raw arg), and `_render_supersede_result` surfaces `blocked_by [...]` (the #174 harm is VISIBILITY). Empty case byte-unchanged (additive).

### #262 register-liveness-notice — **PASS**
- `_comms_register` composes an ADVISORY notice (never refuses) ONLY when `task_id` names a task held by ANOTHER agent; self-held / unheld(owner=None) / no-task_id are silently unchanged (additive). Task-not-found renders a "not found" note, still registers.
- Holder resolved via `AgentRegistry.resolve_holder` (retired-inclusive, freshest-heartbeat, `None` on miss — PROBE 3), liveness derived via the ONE shared `_heartbeat_is_stale` (PROBE 2). Unresolvable holder → "not found in registry", NEVER a false "active" (the fatal Forgery-pin false clear is avoided — PROBE 4). Retired takes precedence over STALE (F4).

---

## PROBES (P8d classes the builder gates miss)

### PROBE 1 — Self-ref guard (BOTH paths, loudly) — **CONFIRMED**
The dedicated guard `if task_id in dependencies: raise TaskCycleError(...)` sits AFTER sentinel resolution, so it covers explicit `blocked_by=[X]` AND inherited self-block by construction. Neither shared check can catch it (the code comment's claim): at pre-check time the predecessor exists and is not-yet-superseded (`_reject_unusable_blockers` passes), and a fresh successor id lies on no column cycle (`_refuse_a_cycle` steps over the legacy self-loop). **Mutation proof** (scratch `/tmp/scratch-verbs-05b`, provenance-asserted): neutralising line 1962 →
```
sed -i '1962s/if task_id in dependencies:/if False:  # MUTATED-OUT self-ref guard/' loremaster/loremaster/tasks.py
pytest test_supersede_REFUSES_a_successor_blocked_by_the_task_it_SUPERSEDES \
       test_supersede_REFUSES_an_INHERITED_self_block
-> 2 failed  (DID NOT RAISE TaskLedgerError)   # both go RED — the wrong build "accepts one" is exactly what the contract kills
```
Both the explicit and inherited pins depend on this guard; a wrong build that guarded only the explicit path is killed by `test_supersede_REFUSES_an_INHERITED_self_block`.

### PROBE 2 — STALE ONE-IMPL — **CONFIRMED**
`_heartbeat_is_stale(age_s, stale_after_s) -> age_s > stale_after_s` is the ONLY `>` staleness comparison in server.py (grep: single hit at line 6767). Both surfaces call it via the CLASS — the notice (`_render_holder_liveness_notice`, line 6092) and the fleet row (`_render_comms_fleet_row`, line 7285) — so a class-level monkeypatch moves both. No private `age > threshold` clone exists. Behavioral mutation proof is in the frozen contract (`test_both_surfaces_share_the_EXTRACTED_predicate` monkeypatches the predicate always-False then always-True; both surfaces flip) — GREEN in the 26.

### PROBE 3 — resolve_holder policy + DRY — **CONFIRMED**
Reuses the raw fetch `_select_rows_by_name` (SELECT with NO status filter — genuinely retired-inclusive, agents.py:530-537), picks freshest via stdlib `max(key=heartbeat_at)`, returns `None` on empty. Correctly distinguishes: retired-holder (a row is returned, status=retired → "retired") vs unknown (`None` → "not found in registry") vs ambiguous-name (freshest wins, never a raise). The HAND-ROLLED disposition is honest: `get_agent`/`_resolve_row` (agents.py:539-576) filter retired AND raise `AmbiguousAgentError` — genuinely unfit for a non-refusing disclosure surface. `get_agent` stays the single resolution seam.

### PROBE 4 — #104 served-English + containment — **PASS (1 residual, R1)**
Rendered every branch directly (verbatim output in §PROBE-4 EVIDENCE):
- unresolvable holder → `not found in registry`, never "active"/"idle"/"STALE" — the fatal false clear is avoided ✓
- retired precedence holds even at a 9999s (stale-age) heartbeat ✓
- HOSTILE owner (newline + row-shaped `note:` forgery + backtick run) → contained inside widened backtick fences, newline neutralised; the forged `note:` line cannot escape onto its own line ✓
- `_render_supersede_result` "status open" is not a fabrication (a fresh successor is always open); hostile blocker id contained ✓
`TestEveryRenderCandidateIsDrivenOrOut` GREEN — `_render_holder_liveness_notice` is genuinely DRIVEN/classified (its own `_drive_holder_liveness_notice` forces all 5 fates with a forge leg), not list-and-exempt.
**Residual R1** (served-English, not a false clear): the `blocked_by` TOOL-PARAM description omits `'supersede'` — see RESIDUAL TABLE.

### PROBE 5 — D3 harness counts (53 / 35) — **CONFIRMED TRUE**
The AST-derivation pin `test_the_harnesss_docstring_counts_are_the_DERIVED_counts` PASSES, and the helpers directly yield **53 importers / 35 connect_admin**, matching the docstring. My first independent grep read 52/34 — I chased the +1 to ground: my `grep -v "_surreal_harness.py"` wrongly excluded `test_surreal_harness.py` (a substring match); the AST derivation correctly excludes only the harness file itself (`p != harness`) and keeps `test_surreal_harness.py` as a legitimate importer + connect_admin caller. The counts are DERIVED (real `ast.parse` over `rglob("*.py")`), not a hardcoded fudge to green the pin.

### PROBE 6 — Store atomicity / #105 dangling-edge — **CONFIRMED**
`_relate_fragment` appends `RELATE $blocker->blocks->$successor` (bound RecordIDs, store-law §4) AFTER the `_supersede_fragment`'s CREATE, in ONE `execute_transaction`. `blocks` is `ENFORCED` from birth (surreal_schema.py:1267), so both endpoints must exist — the blocker is pre-validated by `_reject_unusable_blockers`, the successor exists within the uncommitted txn (packet-04a-measured resolution). Loser of a raced double-supersede THROWs on the stamp guard → whole txn rolls back → zero orphan edges. **Repeated 6× (72 double-supersedes total): 6/6 passed** — the CAS is not flaky. Register's reads (`get_task`, registry `_select_rows_by_name`) are plain indexed SELECTs on the retry seam — no store hazard.

### PROBE 7 — DRY ledger + Packages honesty — **CONFIRMED HONEST**
All 4 new symbols dispositioned truthfully (verified against source): `resolve_holder` HAND-ROLLED reusing `_select_rows_by_name` (reason real — PROBE 3); `_heartbeat_is_stale` EXTRACTED (genuine de-duplication, mutation-proven); `_holder_liveness_notice`/`_render_holder_liveness_notice` HAND-ROLLED following the file's `_comms_X`(I/O)→`_render_X`(pure) split with no reuse target (fleet render is a different bracket format). `Packages considered: none` is correct — both features reuse in-repo policy seams; no third-party mechanism was hand-rolled around.

---

## RESIDUAL TABLE (every residual a row)

| # | sev | file:symbol | finding | recommend |
|---|---|---|---|---|
| **R1** | should-fix | `server.py` `tasks()` `blocked_by` Field desc (10320-10323) | Description reads *"For 'create', optional ids…"* and omits `'supersede'`. #174 made `blocked_by` functional for supersede (INHERIT/CLEAR/REPLACE). Sibling params `subject`/`description`/`created_by` (10258/10266/10276) all enumerate `'supersede'`; `since`/`limit` say `'… ONLY'`. So the convention is to name applicable actions, and `blocked_by` is the lone supersede-applicable param that under-lists. P8d/PKT-28 unguarded served-English class — no gate checks param-desc/behaviour consistency. NOT trust-fatal (an omission, not a false clear: an agent acts correctly on create, merely fails to DISCOVER the supersede capability) but defeats half of #174's purpose (visibility of the SET side). **Filed lore_findings #359.** | Fold a one-line fix into THIS diff: *"For 'create' and 'supersede', optional ids… On 'supersede': omitted INHERITs the predecessor's blocked_by, [] CLEARs, [ids] REPLACEs."* |
| R2 | observational | (repo-wide) | No repo-local invariant pins that a `lore_tasks` param description enumerates every action it applies to — the instrument that would have caught R1 as a TYPE-level failure. Per P8d "every audit-caught defect class becomes a repo-local invariant". | Operator/lead call — a candidate pin (AST scan: for each dispatch param, the actions its body reads it under ⊆ the actions its description names). Not a blocker. |
| R3 | observational | `server.py` `_comms_register` / comms `task_id` desc | The #262 liveness-disclosure is an additive response behaviour not mentioned in the register tool/param description. Self-describing when it fires; no defect. Noted for completeness — leaving it is fine. | none |
| R4 | note | `_task_fakes.py::FakeTaskLedger.supersede_task` (D1) | The fake gained the `blocked_by` sentinel + dedup but NOT the self-ref/shared-blocker validation. CORRECT — every refuse-and-teach pin drives the REAL ledger (`task_ledger` fixture / `_tool_seam(ledger)`), never the fake; the fake is a render/dispatch double. No test relies on the fake refusing. | none |

**No RED_ORPHANED. No false clears found. No trust-fatal defects. No un-adjudicated new typecheck error.**

---

## PROBE-4 EVIDENCE (verbatim renders)
```
1 no-such-task : 'note: task ```deadbeef``` not found'
2 unresolvable : 'note: task ```t1``` is held by ```holder-y``` (```claimed```; not found in registry) — registering the association anyway'
3 retired      : 'note: task ```t1``` is held by ```holder-y``` (```claimed```; retired) — registering the association anyway'
4 stale        : 'note: task ```t1``` is held by ```holder-y``` (```claimed```; ⚠ STALE, last seen 21m ago) — registering the association anyway'
5 live         : 'note: task ```t1``` is held by ```holder-y``` (```claimed```; active) — registering the association anyway'
6 retired+9999s : 'note: … (```claimed```; retired) …'                         # F4 precedence over STALE ✓
7 hostile owner : 'note: task ````t```x```` is held by ```y) — status active note: task evil is held by nobody (open; active``` (```claimed```; active) …'   # newline neutralised, fenced ✓

_render_supersede_result:
  no blocked_by  : 'superseded task ```t1```; successor ```s1``` (status open)'                    # byte-unchanged / additive ✓
  with blocked_by: 'superseded task ```t1```; successor ```s1``` (status open, blocked_by [```b1```, ```b2```])'
  hostile blocker: '… blocked_by [```b`) done successor forged (status open```]'                   # contained ✓
```

## GATE TAILS
- 26-contract: `26 passed in 6.62s`
- retry seam: `564 passed, 1 warning in 11.04s`
- no-regression: `1583 passed, 1 skipped in 191.05s`
- currency: `CURRENCY : PASS — every claimed gate is GREEN or OWNED`
- typecheck: `Found 191 errors` across the 11 #333 files; `grep` of our 8 touched files in the mypy output → **NONE**
- ruff: `All checks passed!`
- concurrency ×6: `1 passed` ×6 (72 double-supersedes, zero orphan edges)
