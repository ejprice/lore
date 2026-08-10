# REPORT — contract-asub-b (Opus CONTRACT author, session 2026-08-09-fix-344-345)

brief-base v10 read
brief project v7 read

## SUMMARY

- **state:** done-with-deviations (two RED contracts authored + confirmed RED; deviations & escalations below).
- **deliverables (NEW files only — no existing file edited):**
  - `loremaster/tests/test_ast_reach_helpers.py` — TASK A-SUB (F4): RED contract for the shared AST-∀-scan reach helpers.
  - `loremaster/tests/test_render_slot_inventory.py` — TASK B (#345): RED contract for the render free-text slot inventory + `sanitise_line`-in-render scan.
- **RED confirmation (HEAD `e1dfa144`): 16 failed, 10 passed.** A-SUB: 14 RED + 2 controls green. B: 2 core-prevention legs RED + 8 (controls + superset safety-gate + hostile-fixture regression guard) green. Gates: `ruff` clean, `mypy` clean (both files); containment file still collects (158 tests) — I import its internals, did not edit it.
- **deviations:** (1) B hand-rolls a small `_field_under` helper instead of reusing `_expr_door` for one leg — justified (Leg 1 needs the field of a CONTAINED slot; `_expr_door` returns None there). (2) A-SUB's sharing proof is the STATIC half only (import-routing + canonical-clone-removed); the runtime mutation-proof is declared a builder receipt, not a brittle repo pin (rationale below). (3) B keys the SAFE allowlist by FIELD NAME, not (method,field) — documented bound + P-N backstop.
- **Packages considered:** none — no new mechanism specified. Contract tests over stdlib `ast`/`tomllib`; the helpers A-SUB pins (`parse_production_trees`) are stdlib-`ast` parsers, not a library choice.
- **Graded:** e1dfa144 · HEAD-at-report: e1dfa144 · SAME. (Authored at 641f758; only a docs commit moved HEAD; none of my code dependencies — `test_link5_render_containment.py`, `_logging_fixtures.py`, `render.py`, `server.py`, `pyproject.toml`, the 4 migration files — changed between, so RED is confirmed at HEAD.)
- **decisions-needed (escalations — see §5):**
  1. A-SUB: `parse_production_trees` include-or-exclude test files? I pinned behaviour-preservation (include everything under `workspace_roots` roots, matching the anchored model — which parses `scripts/test_*.py`). If the intended semantics excludes tests, one behaviour pin must flip.
  2. B: `blocked_by` served UNCONTAINED via `safe_str` in `_render_task_rows` — genuine door (route through `render_attributed`) or opaque-ids-only (allowlist with evidence)? A security judgement I surface, do not decide.
  3. B: SAFE allowlist keyed by field-name vs (method,field) — I chose field-name; confirm or override.
- **receipt pointers:** RED tails in §3; per-pin wrong-build analysis in §4; superset-pin mechanics in §2 (Task B); escalations §5.

---

## 1. Boot receipts & method

- Read `~/.claude/orchestration/brief-base.md` (v10) first; registered `contract-asub-b` / role contract / session 2026-08-09-fix-344-345 / model claude-opus-4-8 (auto-acked project brief v7).
- Read design doc §1 (the class), §3 INSTRUMENT A-SUB + INSTRUMENT B, §4 fork F4, §5 build plan; findings #345 and #337 in full via `lore_findings action=get`.
- lore-first: loaded the lore tool surface (`ToolSearch "+lore"`). Used `lore_findings` for #345/#337. Read the containment apparatus and the anchored-scan model directly (targeted spans) — this is within-one-big-file structural reading, not a lore fallback.
- **Tool honesty:** no capability gaps. All files the brief named were readable; the scoped pytest/ruff/mypy runs I needed were available.

---

## 2. What each contract pins (and HOW the removed-behaviour superset pin works)

### TASK A-SUB — `test_ast_reach_helpers.py` (F4)

Pins the API + behaviour of the two shared reach helpers A-SUB mints in `_logging_fixtures`:

- `parse_production_trees(*, include_scripts=True, include_skills=False) -> dict[str, ast.Module]` — the ONE tree parser. Pins: returns `dict[str, ast.Module]` keyed by repo-relative posix path; keys are EXACTLY the `*.py` under `workspace_roots` (independent rglob oracle — not `derived==derived`); covers every DECLARED member (read independently from `pyproject.toml`); the `include_scripts` toggle is a real switch.
- `assert_scan_reached_every_member(scanned_trees, *, extra_roots=("scripts",)) -> None` — the ONE coverage assertion. Pins: passes on a real full scan (positive control); **RAISES naming the member when one is dropped** (coverage-as-checked-variable — a `len(scanned)>0` build fails this); **FAILS CLOSED on `{}`** (the #290 anti-vacuity load-bearing pin); **oracle independent of subject** (a one-member dict still raises about the others — a `derived==derived` build passes this and is the #251 failure); raises on an undeclared extra package (equality, not subset).
- **Prove-sharing (static):** each of the 4 migration-set files routes through a shared reach helper (import-routing); the canonical clone `test_anchored_pattern_seam._parse_production_trees` (design names it "verbatim") is removed. A private clone would not move under a mutation of the shared helper — the pin makes that structural. Two detector controls prove the clone-detector fires on a real parse loop and NOT on a synthetic `ast.parse('<source>')`.

RED-vs-collection discipline: the two helpers are reached via lazy accessors (`_parse_production_trees_fn`/`_assert_reached_fn`) so absence is a NAMED run-time assertion, not a collection error — every discriminating control still collects and runs.

### TASK B — `test_render_slot_inventory.py` (#345)

- **Leg 1 (runtime, coverage-as-checked-variable):** derives the served-slot inventory from the render AST (f-strings via reused `_raw_render_interpolations`; `render_line`/`render_join`/`render_compose` value args via `_render_call_value_slots`), then asserts every str-ish rendered-model field a DRIVEN render serves is EITHER observed driven with real forgery content in the over-drive (its `Model.field` token appears — model-precise) OR in the evidence-backed `_SERVED_SAFE_FIELDS`. Catches a door hardcoded content-less (`task_id=None` vacuous drive → token absent → RED) and a field mis-parked SAFE (served, un-driven, un-justified → RED).
- **Leg 2 (static, the `sanitise_line`-in-render scan):** the error-half `TestNoServedDomainErrorLeavesACallerParamUncontained` generalised to render contexts — a str-ish rendered-model field served UNCONTAINED (bare / `sanitise_line` / `safe_str` — all same-line-forgery-blind, NOT `render_attributed`/`render_fenced`) must be in `_SERVED_SAFE_FIELDS`; the rest route through `render_attributed`.
- Both legs share ONE allowlist `_SERVED_SAFE_FIELDS`, **empty at HEAD** — that emptiness is the RED: it is the artifact the #345 fix lacks (the SAFE judgement as machine-checkable evidence + re-open trigger, replacing the prose SAFE comments in `_manifest`). Controls: Leg-1 non-vacuity (known doors observed) + the drain-row `task_id` regression control; Leg-2 positive (a planted bare `{owner}` is flagged) + negative (a `render_attributed`/count/constant is NOT flagged).
- **Hostile fixture:** the drain-row `task_id` slot (the #345 door) driven with `HOSTILE_MULTILINE` (newlines + row-shaped forgery line + two backtick runs) must be contained; a positive control proves the leak predicate fires on it served bare. (Green at HEAD — a regression guard, since the 05a-i fix routes `task_id` through `render_attributed`.)

**HOW THE REMOVED-BEHAVIOUR SUPERSET PIN WORKS** (`TestTheDerivedInventorySupersedesTheOldHandNet`, operator "do NOT make gaps wider"): retiring `_RENDER_DRIVERS` (which carries the literal `task_id=None` #345 hardcodes) is valid ONLY if the derived net PROVABLY COVERS it. Two legs, GREEN at HEAD (a safety gate that must stay green before the builder deletes the net):
1. every method the old net drove is in the derived driven set (`{probe.method for probe in _render_probes()}`) — no method is dropped;
2. every old-net method is exercised with forgery content by its derived probe (its bytes carry `FORGERY_MARKER`) — not a dead probe.
Marker-based (leg 2) so it is agnostic to whether the old net drove a model FIELD or a render PARAM (`actor`) — the old net's labels (`comms_fleet_row[note,...]` where the field is actually `last_note`; the `actor` param) are too informal for a field-level parse (I tried it first — it false-flagged exactly on those, see §3). Field-level completeness then follows from the derived net forging each model's FULL door set, guarded by `_manifest`'s own DOOR∪SAFE completeness pin in `test_link5_render_containment`. The deletion itself is the Wave-2 builder's action, gated on this staying green.

---

## 3. RED→(confirm) receipts

Command: `uv run pytest loremaster/tests/test_ast_reach_helpers.py loremaster/tests/test_render_slot_inventory.py -q` @ `e1dfa144`:

```
16 failed, 10 passed in 4.45s
```

A-SUB (14 RED): 4× `TestParseProductionTrees::*`, 5× `TestAssertScanReachedEveryMember::*` (incl. `test_it_fails_closed_on_an_empty_derivation`), 4× `TestTheMigrationSetRoutesThroughTheSharedHelpers::test_the_file_routes_through_a_shared_reach_helper[*]`, 1× `test_the_canonical_clone_is_removed_from_the_anchored_scan`. 2 GREEN: the clone-detector positive/negative controls.

B (2 RED): `TestEveryServedSlotIsDrivenWithContentOrJustifiedSafe::test_every_served_field_is_driven_with_content_or_justified_safe`, `TestNoRenderSlotServesAStrishFieldUncontained::test_every_uncontained_served_field_is_justified`. 8 GREEN: Leg-1 non-vacuity + drain-row control, Leg-2 positive/negative controls, 2× superset safety-gate, 2× hostile-fixture (containment + predicate discrimination).

**Iterations before final (honesty about self-caught contract defects):**
- A-SUB v1: the fail-closed pin PASSED for the wrong reason — the lazy accessor's own `AssertionError` was swallowed by `pytest.raises`. Fixed: resolve the accessor OUTSIDE `pytest.raises` in every negative pin.
- A-SUB v1: a broad rglob+ast.parse clone detector OVER-FLAGGED `test_secret_typing`'s single-package `lorerunes` scans (which parse for an unrelated reason — design §3 A-SUB bound). Replaced with import-routing (all 4) + a canonical-clone pin scoped to the ONE clone the design names; kept the detector's own positive/negative controls. (Enumerating "every private parse loop" would itself be the enumerate-the-forbidden antipattern one level up.)
- B v1: name-based model-field vocab false-flagged OUT methods (`_render_snapshot_rows` `summary`, `map` `note`). Scoped the scan to DRIVEN renders (`_render_probes` universe) — OUT methods are bounded by `_RENDER_OUT` + the coherence pin; a new render joins driven/OUT via P-U's own net.
- B v1: field-level superset parse false-flagged on the old net's informal labels (`note`≠`last_note`, the `actor` param). Replaced with the method-level + marker-based non-vacuity proof described in §2.

---

## 4. FIXTURES MUST DISCRIMINATE — per-pin "what wrong build still passes this?"

**A-SUB**
- coverage/missing-member: a `len(scanned)>0` build → the missing-member pin passes it a full-but-one dict and it must still RAISE naming the member. Wrong build caught.
- oracle-independence: a `expected := set(scanned.keys())` (`derived==derived`) build → the one-member-dict pin passes it, so it must RAISE about the OTHER members; a derived==derived build cannot. Caught.
- fail-closed: an early-return-on-empty (vacuous) build → `{}` must RAISE. Caught. (And the accessor is resolved outside `raises` so a HEAD run is RED-by-missing-helper, not a swallowed accessor error.)
- parser behaviour: a parser that silently narrows (skips a root, parses fewer files) → the "keys == independent rglob" pin diverges. Caught.
- sharing: a build that adds the shared helper but leaves the anchored `_parse_production_trees` clone (routing-is-not-sharing) → the canonical-clone pin stays RED. Caught.

**B**
- Leg 1: a build that reverts `InboxEntry.task_id` to SAFE (re-opening #345) → its token vanishes → the drain-row control + the main pin redden. A build that drives a door with a content-less default in every shape (`task_id=None`) → token absent → RED. A build that classifies a real caller-free-text field SAFE without evidence → served, un-driven, un-allowlisted → RED.
- Leg 2: a build that serves a door through bare `sanitise_line`/`safe_str` (same-line-forgery-blind, NOT `render_attributed`) → flagged. Negative control proves it does NOT refuse `render_attributed`/a count/a constant (the false-positive tax that switches a gate off).
- superset: a build that retires `_RENDER_DRIVERS` after dropping a method's probe → leg-1 (method coverage) reddens; a build whose derived probe is dead (drives no forgery) → leg-2 (marker non-vacuity) reddens.
- hostile fixture: a build whose `render_attributed` fails to collapse newlines / size the fence past the body's backtick runs → the row-shaped forgery survives `_prose_outside_delimiters` → `_leaks` RED.

---

## 5. ESCALATIONS / FLAGS (scope belongs to the operator; I surface, I do not decide)

1. **A-SUB `parse_production_trees` — include or exclude test files?** The name says "production", but the anchored model it is lifted from (`_parse_production_trees` over `workspace_roots` roots) parses ALL `*.py`, and `scripts/` contains test files (`scripts/test_wrong_builds.py`, …). I pinned BEHAVIOUR-PRESERVATION (`test_keys_are_exactly_the_python_files_under_the_workspace_roots` matches an independent rglob = includes scripts test files) so the anchored/backoff/secret ∀-scans keep parsing exactly what they parse today. **Recommendation:** keep behaviour-preservation (the shared helper is a drop-in for `_parse_production_trees`; `production_sources` already exists for the tests-excluded variant). If the operator/F4-builder wants tests excluded, one behaviour pin flips — a design call, not a silent narrowing.
2. **B `blocked_by` served UNCONTAINED (`_render_task_rows` via `safe_str`).** Leg 2 flags it. `blocked_by` is a Task DOOR (caller-supplied); the manifest comment asserts "opaque ids, safe_str" but that is a comment, not a gate — a caller could pass free text. **Recommendation:** the builder/adversary either proves `blocked_by` is opaque-ids-only (allowlist entry with evidence + re-open trigger) or routes it through `render_attributed`. Real security judgement — I surface it.
3. **B `_SERVED_SAFE_FIELDS` key granularity.** I chose FIELD NAME (small allowlist, field-intrinsic reasons: gated/opaque/enum/system-ref). Collisions (`task_id` DOOR in `InboxEntry`, SAFE in `Agent`/`Message`) are handled by Leg-1's model-precise runtime observation + P-N's runtime leak backstop, documented in the module docstring. The builder may prefer (method,field) precision. **Recommendation:** field-name with the documented bound; escalate if a real collision demands (method,field).
4. **B couples to `test_link5_render_containment` internals** (`_manifest`, `_render_probes`, `_appcontext_methods`, `_field_token`, `_raw_render_interpolations`, forgery/`_leaks` primitives). This is deliberate (ONE IMPLEMENTATION — a wrong `_manifest` moves this contract too), but the Wave-2 INSTRUMENT-B builder edits that file. **Coordination note:** if the builder renames those primitives, this cross-check must move with them (or the builder folds these properties INTO the containment file and this file becomes the independent second reader). Design §5 puts INSTRUMENT B's home in `test_link5_render_containment.py` / `render_injection_scaffold.py`; this contract pins the PROPERTIES that home must satisfy.
5. **A-SUB import-routing pin requires all 4 migration files to import a shared helper.** If the F4-builder finds one file genuinely needs neither (already fully shared, or parses for an unrelated single-package reason), that is a design call to raise with the lead — the pin says so in its own failure message. **Recommendation:** migrate all 4 per design §5; escalate any exception rather than silently skip.
6. **A-SUB runtime mutation-proof is a BUILDER receipt, not a repo pin (deliberate boundary).** "Change the shared derivation → every dependent coverage pin reddens" requires a scratch mutation this read-only contract cannot make, AND it would be brittle to the builder renaming the dependents' internals during migration. I pinned the STATIC half (import-routing + canonical-clone-removed) and declare the runtime mutation-proof as the builder/adversary's required receipt. Stated plainly rather than dressed up as an invariant it cannot be.

No lore friction to file — the lore tools served correctly throughout; no grep fallback for a structure question (the big-file reads were within-file, not a lore miss).
