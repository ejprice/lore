# REPORT-coldaudit-04b5-3 — STANDING Fable delta-auditor, packet 04b5 (Link-5 render-site injection containment)

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (tool honesty, first)
Brief satisfiable with the tools granted. lore tools loaded first try (`ToolSearch "+lore"`,
no #334 flake). Registered `coldaudit-04b5-3` (session `pkt04b5`, role auditor,
model claude-fable-5). I EDIT nothing — this report is my only writable artifact. I re-run
gates with `-n auto` and CONSTRUCT wrong builds (via `./scripts/scratch_copy.sh`, asserting
`loremaster.__file__` provenance) when a litmus needs an empirical answer. lore-first for
production symbols; **grep via Bash is the honest tool** for `!r`/prose sweeps and I say so
per hit (`Grep`/`Glob` are disabled session-wide). I replace `coldaudit-04b5-2`, who died to a
transient API error mid-pre-load; I inherit its mission, not its (absent) work.

## SUMMARY BLOCK
- state: **standing by** — pre-load COMPLETE; no verdict rendered yet (reworked contract
  `contract-04b5-2` does not exist on disk at pre-load time).
- **Graded: n/a yet** · HEAD-at-pre-load: `4c5930d` · this is the same sha the prior cold
  audit (`REPORT-coldaudit-contract-04b5-1.md`) graded. The baseline on disk
  (`test_link5_render_containment.py` + `test_task_read_surface.py` fence rework;
  `test_attribution_bound.py` deleted) is exactly what R1–R7 audited.
- Packages considered: none — no mechanism specified (this is an audit).
- deviations: none yet.
- decisions-needed: none yet.
- receipt pointers: pre-load record §Round-0; the inherited R1–R7 live in
  `REPORT-coldaudit-contract-04b5-1.md` §R (I do NOT re-transcribe them).

---

## Round 0 — PRE-LOAD (dated 2026-08-05, HEAD `4c5930d`)

I have read and internalised the stable context. What I will DELTA-audit when signalled:

**The INSUFFICIENT verdict I inherit (the fix must close R1+R2; R3 is the adversary's leg):**
- **R1** — B-3 per-SITE reach absent. The partition (`TestTheDerivedPartitionHasNoDoor`)
  proves each free-text PARAM is in a CLASS a driver neutralises; it does NOT prove each
  SITE routes through the seam. Constructed litmus: classify `task_id` as `served_error`,
  route ONE `StoreReadTool._not_found_error` site, leave all 19 `task_id!r` sites in
  tasks.py (+ rollup summary/report_path + comms send/drain thread/refs) BARE → the WHOLE
  contract passes green. Contradicts B-3 "reach as a CHECKED variable" + the operator
  all-or-nothing ruling. Fix template already in-diff: the name-blind fence-site AST scan.
- **R2** — array-of-string universe hole. `_registered_string_params` admits a param only if
  `"string" in types`, so 6 array-of-string params are structurally invisible, incl. the
  CONFIRMED bare drain-row door `lore_comms.refs`. The author's §DIFF "refs IN as
  attribution" is FALSE (refs in neither the universe nor `_PARAM_CLASS`).
- **R3** (adversary's to exercise) — satisfiability receipt ran only the 50 new/reworked
  tests, not the pre-existing seam suites the reshape touches
  (`test_render_seam_pins::TestSafeLineRenderedMintPin`, `test_mcp_server`'s
  `TestRenderInjectionRegistry`, `test_comms_tool`'s RenderCase registry).
- **R4** (med-low) — `test_the_width_rule_is_not_cloned_in_render_attributed` name
  over-claims: output width==4 cannot distinguish consume-from-clone.
- **R5** (low) — 3 inert docstring refs to deleted `test_attribution_bound.py`
  (`server.py:4055`, `test_mcp_server.py:7941`, `render_injection_scaffold.py:112`).
- **R6/R7** (low/info) — charset-gated set derived from signature not body; recall/memory
  array params part of R2's class.

**What the prior audit ruled SOUND (I must check the fix did NOT regress these):**
§A mutation-sharing legs (independent literal widths); §C hostile fixture + the containment
predicate's own +/- controls + inner-backtick control; the 10-door benign controls + repr/bare
positive controls; the fence rework being contract-first (OLD dated-exemption + self-destruct
REPLACED not amended, two-home name-blind derivation, `test_search_py_is_RETIRED…` RED at HEAD,
before/after byte pins); the B-5 bounds with named re-open triggers; `test_attribution_bound.py`
deletion clean; zero-new mypy; behavioural well-formedness (25 RED / 25 GREEN, all REDs
feature-absent AssertionErrors).

**My GO/INSUFFICIENT priorities when the reworked contract lands (per the lead brief):**
1. R1 CLOSED? Per-SITE reach instrument — name-blind, RUNTIME-observed (not defeated by
   post-seam demotion re-embedded in an f-string), reddens on a bare-left site. RE-RUN at HEAD
   (must be RED, feature-absent) + CONSTRUCT a one-site-bare wrong build to confirm it reddens.
2. R2 CLOSED? `refs`/`to`/`labels`/`blocked_by` visible to the completeness net.
3. R3 CLOSED? Satisfiability receipt runs the pre-existing seam suites.
4. R4/R5 — over-claiming name fixed; stale `test_attribution_bound.py` prose swept.
5. REGRESSION — re-run the FULL contract at HEAD, RED/GREEN counts in the report; confirm the
   sound parts survived.

Standing by. Idle-between-rounds is benign; I will not stop.
