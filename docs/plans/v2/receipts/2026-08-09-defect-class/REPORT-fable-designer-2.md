# REPORT — fable-designer-2 (Fable design sidecar, continuing — reviser-asub-b fork rulings)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State: done.** Two design forks ruled + one confirmation recorded; appended as §10 to
  `docs/plans/v2/design/2026-08-09-defect-class-prevention.md`. No code/tests written (design only).
- **Ruling (fork #2 — the important one): fleet-row `task_id` is a forgery DOOR, un-contained
  TODAY — a LIVE production trust gap needing a fix THIS session.** `Agent.task_id` is UNCONSTRAINED
  caller free text (register stores it verbatim); the fleet row serves it via `safe_str` (same-line-
  forgery-blind) while 4 of 5 other `task_id` renders use `render_attributed`. → contain via
  `render_attributed` + manifest correction + the B contract's regression pins. The lead routes a
  B/#345-cycle builder task (server.py already in that cycle's scope).
- **Ruling (keying): field-name keying CONFIRMED sound — the collision is PROTECTIVE, not
  disqualifying.** `task_id` is a door in EVERY model that carries it (Agent/Message/InboxEntry all
  caller free text); the Agent/Message SAFE labels are MIS-PARKS, not a genuine safe instance.
  (model,field) keying is REJECTED — it would reverse §8 Ruling 3 AND re-permit the #345 mis-park.
- **Ruling (fork #1 — comms_footer): a DESIGN classification, ruled — NOT an operator scope-grant.**
  `test_comms_footer` IS a `parse_production_trees` adopter (confirmed: TWO whole-tree scans); §5's
  writable-set omission is a clerical inconsistency with §7/§8. It stays in the A-SUB cycle. Surfaced
  a NEW instance of the class: its second scan hand-lists a 4-member tuple (migration retires it).
- **#3 confirmed & recorded:** `_rebind_everywhere` promotion to shared test-support APPROVED (≥2
  reusers F+A-SUB); already the design of record (§9.6/§9.7).
- **Deviations: none.** No operator escalation needed for either fork (both resolve within the design
  + DRY-consolidation scope the operator already prioritized). No store/schema/DDL touched.
- **Packages considered:** none — no mechanism specified (design ruling only).
- **Graded: 3b708e5 · HEAD-at-report: 3b708e5 · SAME.** Index fresh (last sweep 2026-08-09T19:40Z,
  branch feat/surreal-unification).
- **Receipt POINTERS:** all rulings + evidence in the design doc **§10**
  (`docs/plans/v2/design/2026-08-09-defect-class-prevention.md`). Key evidence symbols:
  `agents.py::AgentRegistry.register` (task_id stored verbatim) · `server.py`
  `AppContext._render_comms_fleet_row` (safe_str, the gap) · `test_link5_render_containment.py`
  `_manifest` Agent/Message/InboxEntry entries · `test_comms_footer.py` scans (2958 derived / 3144
  hand-listed).

## Body

The full rulings, evidence, and the builder tasks each forces are in **§10 of the design doc**
(appended this run). This report is the pointer + the summary above; §10 is the design of record.

**One-line each:**
- **#2 DOOR + LIVE fix:** `Agent.task_id` = caller free text (register verbatim, no charset/shape/
  length gate; corroborated by the manifest's own InboxEntry comment citing `messages.py:865-871`
  "LENGTH only"). Served un-contained at `_render_comms_fleet_row` via `safe_str(row.task_id[:8]+"…")`;
  8 chars is enough to forge a ` · ` cell-delimiter (cells are ` · `-joined). Small but genuine trust
  leak, exactly #345 one model over (the `task_id=None` forge hardcode at test_link5:2413 is the
  literal artifact). Fix: `render_attributed(...)` at server.py:7055 + move Agent/Message `task_id`
  `safe→door` in `_manifest` + confirm the B regression pins (drive-all + mis-park pin close both
  escape routes).
- **Keying:** field-name keying stands (its first LIVE test — it works). A door-name is contained
  everywhere; over-containment is harmless (§8 R2); the mis-park pin makes SAFE-listing a door-name
  unrepresentable; (model,field) would make the mis-park representable again → rejected.
- **#1 comms_footer:** design-ruled adopter; add `test_comms_footer.py` to the A-SUB writable set
  (remove the provisional allowlist entry). BOTH its scans migrate (2958 `include_tests=True` /
  3144 `include_tests=False` + retire its hand-list), each pinned to exact pre/post scanned-set per
  §8 R1. ⚠ granularity hazard flagged (comms_footer's `_workspace_scan_roots` yields `<member>` incl.
  tests; `workspace_roots` yields `<member>/<member>` excl. tests — `include_tests=True` must re-add
  `<member>/tests` or Scan A narrows).

**Dogfood / fallback disclosure:** used lore (`lore_get_symbol`/`lore_read`/`lore_search`/`lore_index`)
for symbol resolution + provenance, and `grep`/`ast`-shape reads over the test tree for the
non-symbol textual seams (manifest door/safe literals, comms_footer scan structure) — the honest
grep case (b) per CLAUDE.md. No lore weakness routed-around.
