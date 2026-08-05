# REPORT-entrycheck-04b4-1

brief-base v10 read

## SUMMARY BLOCK
- state: done
- deviations: none
- **Capability check:** brief demanded lore tools + read-only ground-truth of source/tests/ledger — all available and used. lore index is FRESH and pinned to HEAD (root `/workspace`, branch `feat/surreal-unification`, git_ref `5c5ff7a` == HEAD; last_sweep 199 s at read). No fallback needed except the served-prose sweep (grep, disclosed below — served descriptions are prose in string literals, the honest grep case).
- Packages considered: none — no mechanism specified (read-only audit).
- Graded: 5c5ff7ae585bfcc4b9a507eafbd8a569c5aa7fba · HEAD-at-report: 5c5ff7ae585bfcc4b9a507eafbd8a569c5aa7fba · SAME
- decisions-needed: **#310 must be re-scoped before contract (PARTIAL — its concrete half is already shipped). #319's acute instance is already corrected (durable-fix half remains).** Both are lead calls — see BOTTOM LINE.
- receipt pointers: verdict table below; §D-#310 stale-premise detail in body; #304 informational in body.

---

## VERDICT TABLE

| Finding | Verdict | Receipt (symbol / file:line at 5c5ff7a) | Ledger status |
|---|---|---|---|
| **#319** — served `limit`/param descriptions false vs refusal matrix | **STILL-PRESENT** (durable fix unbuilt; acute instance already corrected — see note) | No derived description-vs-matrix pin exists: `test_mcp_server.py::TestToolDescriptions` asserts POSITIVE substrings only (self-documented, `test_mcp_server.py:1105-1106`); `TestNoDeadToolNamesInAgentFacingText` (`test_mcp_server.py:1092`) is dead-name hygiene, not matrix-derivation. Acute instance `lore_tasks.limit` now reads "For 'rollup' and 'query' ONLY" (`server.py:9372`) — **corrected in `0ff05ed`**. | **open** |
| **#309** — no-limit `lore_tasks action=query` serves whole ledger uncapped | **STILL-PRESENT** | `AppContext._task_listing` no-limit path returns `TaskListing(rows=…, more=False)` with NO default cap (`server.py:3865`, esp. the `if cap is None` branch); `AppContext._render_task_listing` emits NO line when `not listing.more` (`server.py:3926`). No `+K more — re-run with limit=N` grammar on the uncapped read. | **open** |
| **#310** — shared `validated_task_limit` / validate-before-transform | **PARTIAL** — concrete fix + 3-leg pin + sharing mutation-proof **ALREADY-FIXED**; only the CLASS instrument is undone | `validated_task_limit` is a module-level fn (`tasks.py:598-633`); `TaskLedger._validated_limit` DELEGATES to it (`tasks.py:1334`); `_task_listing` calls `cap = validated_task_limit(limit)` **before** `cap+1` (`server.py:3865`). Pin `TestTheCALLERSOwnLimitIsWhatGetsVALIDATED` (`test_task_read_surface.py:789`; limit=-1 @820, limit=0-serves-nothing @844) + sharing mutation-proof (`test_task_read_surface.py:~2560-2588`). All landed `0ff05ed`. **Concrete defect is NOT reproducible.** No AST transform-before-validate scan / PIN-THE-MISS exists (the CLASS half). | **open** |
| **#322** — name-free ∀ dispatch-fixture invariant | **STILL-PRESENT** | No dedicated "∀ action → drive `_*_action_kwargs` → assert no missing-arg `ValueError`" invariant exists. What exists: partition-MEMBERSHIP pin (`test_comms_footer.py:847`, tuples @257/278/282/292) and footer-property ∀ tests (`test_comms_footer.py:895/923/943/958`) that drive the fixtures but assert the FOOTER, reddening as an ambiguous `ValueError` on fall-through — the exact failure mode #322 exists to convert to a clear fail-closed. | **acknowledged** (routed 04b-2→04b-3→ now 04b4 per §D-#322) |
| **#324 R-2** — parity probe promoted to standing pin | **STILL-PRESENT (UNDONE)** | Probe lives at `scripts/audit_probes/coldaudit_wavec_r2_probe3.py` (and `scratchpad/`) as a `__main__` script — defines `probe_cycles`/`probe_phantom`/`main`, **no `def test_*`**, so pytest does NOT collect it despite `scripts/` ∈ testpaths (default `python_files = test_*.py`). `test_task_ledger.py` (91 tests) has NO transitive_blockers/cycle parity standing pin. | **open** (part of #324) |
| **#324 R-3** — `AppContext.findings` branch-scan pin | **STILL-PRESENT (UNDONE)** | `_dispatched_action_values` AST-scans `inspect.getsource(AppContext.tasks)` **only** (`test_task_read_surface.py:1802-1835`, used by `test_every_declared_action_BRANCHES_in_the_dispatcher` @1837). No `AppContext.findings` twin — the asymmetry R-3 names is present. | **open** (part of #324) |
| **#324 R-4** — `name`/`to` keyword-required on `_validate_comms_identities` | **STILL-PRESENT (UNDONE)** | `_validate_comms_identities(agent, *, session, name: str \| None = None, to: list[str] \| None = None)` — both defaulted (`server.py:5478-5484`). 4 call sites: 3 pass neither (`server.py:3154, 3597, 3739`), 1 passes both (`server.py:5150`). The 3 defaulted sites are exactly R-4's "3 sites." | **open** (part of #324) |

---

## BODY — evidence and the two re-scope forks

### #310 is the stale-premise trap the entry check exists to catch (PARTIAL)
The 04b-2 C1 build (`0ff05ed`, **DEPLOYED 2026-08-03**) already shipped the ENTIRE concrete half of
§D-#310:
- **The ONE implementation** — `validated_task_limit(limit)` is module-level (`tasks.py:598-633`); its
  docstring names itself "THE ONE IMPLEMENTATION". `TaskLedger._validated_limit` is a thin delegate
  carrying "no rule of its own" (`tasks.py:1334-1344`).
- **Validate-before-transform is correct** — `_task_listing` computes `cap = validated_task_limit(limit)`
  and only then over-fetches `cap + 1` (`server.py:3865`). Its docstring documents all three refusals
  preserved (limit=-1 → refused naming the caller's value; limit=0 → serves NOTHING; limit=True → not
  LIMIT 2). **The concrete defect the brief asked me to reproduce is NOT reproducible.**
- **The three-leg pin exists** (`test_task_read_surface.py:789`) AND the "prove sharing by MUTATION"
  rider is already a test (monkeypatches `validated_task_limit` and asserts BOTH seams reroute,
  `~2560-2588`).

⇒ Handing §D-#310 to a contract author verbatim would re-derive already-shipped code and likely mint a
pin that duplicates or contradicts `TestTheCALLERSOwnLimitIsWhatGetsVALIDATED`. **The residual 04b4 work
for #310 is ONLY the CLASS instrument** (an AST transform-before-validate scan over dispatch params, or
PIN-THE-MISS with a trigger). That instrument does not exist at HEAD.

### #319 — the acute lie is gone; the durable fix (the point) is owed (STILL-PRESENT)
The instance the finding was NAMED for — `lore_tasks.limit` "For 'rollup' ONLY" — was corrected by
builder-c1-1 in `0ff05ed`; it now reads "For 'rollup' and 'query' ONLY" (`server.py:9372`) and matches
the refusal matrix (`_TASK_ACTIONS_ACCEPTING_LIMIT`, `server.py:3751`). In a **bounded** anchor-free
sweep of the limit-bearing tools I found the action-scoped descriptions **consistent** with their
refusal logic: `lore_tasks` since/limit/max_depth/items (`server.py:9357-9404` vs raises @3749/3753/3759/3765),
`lore_comms.limit` (`9603`, clamp matches `_MAX_FLEET_LIMIT=200`/`_MAX_DRAIN_LIMIT`), `lore_diff.limit`
(`9807`), `lore_findings.limit` (`9940`). **I did NOT confirm a remaining live-false description** — the
full bare/anchor-free sweep across every param of every tool IS the §D-#319 deliverable, not the entry
check's job.
- **Fallback disclosed:** the served descriptions are prose inside `Field(description=…)` string
  literals — a non-symbol textual seam, so I used grep/Read, not the graph (per dogfood protocol §3b).
- **Verdict rationale:** #319 is STILL-PRESENT because the DURABLE fix (derived description-vs-matrix pin
  + full anchor-free sweep) is unbuilt and no such pin exists. But the lead should know the severity has
  shifted: 04b4 §D-#319 is now "build the derived pin + sweep the remainder" (class/durable), NOT "fix a
  live outage lie" (acute) — the acute instance is already fixed.

### #322 — membership ≠ the drive-no-raise invariant (STILL-PRESENT)
The four action tuples exist (`test_comms_footer.py:257/278/282/292`) and a MEMBERSHIP pin asserts their
union equals the dispatcher's action set (`:847`). The footer ∀ tests (`:895/923/943/958`) DO drive each
action through `_task_action_kwargs`/`_finding_action_kwargs` (`:3855/3918`) — but assert the footer
property. When a fixture falls through to `{}`, they redden as an ambiguous `ValueError` inside
`server._require_arg` (finding #322's own described failure mode: "a RED that looks like a build defect
and measures NOTHING"). The dedicated name-free invariant that asserts "no missing-arg ValueError" —
failing CLOSED with a naming message — does not exist. Sidecar §D-#322 (04b4) confirms it is to be built.

### §7-item-5 / §D-#304 ENTRY CHECK (informational, non-blocking for 04b4 — for 05a)
Measured at 5c5ff7a on `AppContext._render_comms_fleet` (`server.py:6591`) and
`_render_comms_fleet_row` (`server.py:6551`):
- **S1-a — session-scoped fleet header: LIVE.** Renders `"fleet (session {session}): {total} non-retired
  agents — …"` (`server.py:6591`, session branch). (Re-verified as the brief requested.)
- **S2 — AGE-render: LIVE.** Each row renders `hb {age}` via `_render_age(heartbeat_age_s)`
  (`_render_comms_fleet_row:6551`; `_render_age` @`server.py:6093`). The heartbeat age is served as a FACT.
- **R4 fleet UNREAD/UNACKED columns: UNSHIPPED.** `_render_comms_fleet` takes NO unread/unacked
  message-count parameters, and `_render_comms_fleet_row`'s cells are role/model/task/brief-ack/note —
  **no unread/unacked cell**. Per sidecar §D-#304's own logic ("if they are UNSHIPPED 04b-2 residue,
  re-home the columns + #304 together to 05a"), the columns + #304 (a)/(c) re-home together to **05a**.
- **⚠ Minor discrepancy for 05a (non-blocking):** the `⚠ STALE` badge is STILL rendered
  (`_render_comms_fleet_row:6551`, `if heartbeat_age_s > stale_after_s`), which contradicts sidecar
  §D-#304's premise that "S2 already retired the `⚠ STALE` badge." Note this badge is DERIVED-at-render
  from the age (not a latched self-declared status), so it is a weaker concern than #304's latched
  `input_required` — but the sidecar's stated premise does not hold verbatim at HEAD. Surfaced for the
  05a author.

---

## BOTTOM LINE
**Not all five are STILL-PRESENT — the lead must STOP on #310 (and note the shift on #319) before
contracting.** **#310 is PARTIAL:** its concrete half — the shared module-level `validated_task_limit`,
the validate-before-transform seam, the three-leg pin, and the sharing mutation-proof — is
**ALREADY-FIXED**, shipped in `0ff05ed` and deployed 2026-08-03; §D-#310 must be re-scoped to ONLY the
undone CLASS instrument (AST transform-before-validate scan, or PIN-THE-MISS with a trigger), or the
contract will re-build shipped code against a stale premise. **#309, #322, and #324 R-2 / R-3 / R-4 are
STILL-PRESENT and proceed to contract as written.** **#319 is STILL-PRESENT** (the derived
description-vs-matrix pin + full anchor-free sweep are unbuilt), but its acute named instance
(`lore_tasks.limit`) was already corrected in `0ff05ed`, so the 04b4 deliverable is the durable pin +
sweep, not a live-lie fix — a scope clarification, not a blocker. Informational for 05a: fleet
session-header (S1-a) and age-render (S2) are LIVE; R4 UNREAD/UNACKED columns are UNSHIPPED → re-home
with #304 to 05a; the `⚠ STALE` badge still renders, contradicting §D-#304's premise (flagged).
