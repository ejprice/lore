brief-base v10 read
brief project v7 read

# REPORT — contract-cd (session 2026-08-09-fix-344-345)

## SUMMARY
- **state: done** — both CONTRACT files written, RED confirmed, ruff clean, mypy clean except the two legitimately-absent deliverables.
- Role: contract author (CONTRACT TESTS ONLY — no production/implementation code). Wrote ONLY the two new files granted; edited no existing file; touched no git state.
- **Deliverables (2 new files):**
  - `loremaster/tests/test_mutating_set_derivation.py` — Task C / finding #291 / INSTRUMENT C.
  - `loremaster/tests/test_refusal_observes_effect.py` — Task D / finding #295 / INSTRUMENT D (auth-independent half).
- **RED confirmed:** `13 failed, 3 passed` (both files, `-p no:cacheprovider -o addopts=""`). All 13 RED are "deliverable ABSENT" (no infra errors); the 3 PASS are the GREEN-today supporting invariant + its control (C) and the proxy-blindness proof (D). Tail in §Receipts.
- **REVISED per lead ruling (2026-08-09, Fable DRY review §7 + operator; DRY = priority #1).** C now pins a **PRODUCTION** single-source helper `loremaster.server.partition_tools_by_posture(tools) -> (mutating, read_only)` — NOT a test-code derivation. Packet 39 later CONSUMES it (fold-in note; packet 39 WIP untouched). D stands as written.
- Deviations (one line each):
  - D helper signature generalized from the design-doc's illustrative `(mcp, tool_name, args)` to `(wire, tool_name, args, *, effect_count, refusal_marker)` — the effect observer is pluggable (counter / unchanged store / absent row), which the finding's own "(or unchanged store / absent row)" requires; the wire is passed in (reusing `_auth_fixtures.wire_session`) so the wire path is structural. Interface accepted by ruling #3.
  - C's `_spec_partition` is retained ONLY as the contract's independent GRADING ORACLE (not a consumer source) — the "oracle independent of subject" pattern; consumers use the prod helper.
- **Packages considered:** none new — no mechanism/library introduced. The D contract REUSES the installed SDK-client wire harness `_auth_fixtures.wire_session` (mcp `ClientSession` + `streamable_http_client` over `httpx.ASGITransport` + `asgi_lifespan.LifespanManager` — all already installed and the sanctioned R16 wire path); the C contract reuses `build_mcp_server` + `mcp.list_tools()` + `mcp.types.ToolAnnotations` (installed). Verdict for both: `keep` (reuse the existing tested harness; hand-rolling a second wire driver would be the exact ONE-IMPLEMENTATION defect `_auth_fixtures` warns against).
- **Graded:** e1dfa14 · HEAD-at-report: e1dfa14 · SAME. (Session-start snapshot showed `641f758`; HEAD has advanced — consistent with concurrent siblings on the shared tree. The C contract depends only on the six `*_ANNOTATIONS` constants + `_MUTATING_TOOLS`/`_READ_ONLY_TOOLS`, stable at HEAD.)
- **decisions-needed: none open — all 3 escalations RULED by lead (2026-08-09), contract revised accordingly:**
  1. **C derivation HOME — RULED: unify into ONE PRODUCTION helper** `loremaster.server.partition_tools_by_posture` (single source of truth); NO second derivation in test code; packet 39 folds its `mutating_tool_names` into a call to it (fold-in only, WIP untouched). Contract now imports + pins the production symbol; the mutation proof is on the prod helper ("a caller that stays green is a private copy").
  2. **D helper HOME — RULED: dedicated `_refusal_effect.py`.** Contract imports from there.
  3. **D effect-observer — RULED: pluggable + passed-in wire accepted.** Extracting packet 39's private `_run_entry_recorder` is DEFERRED to packet 39 (WIP untouched); D lands its OWN auth-independent effect observer (the per-tool counter controls), and packet 39 later consumes the shared effect-helper (fold-in).
- **RED-phase mypy note (not a defect):** canonical mypy (from repo ROOT, root `mypy_path`) = exactly 2 errors — module `_refusal_effect` absent (D) + `loremaster.server.partition_tools_by_posture` absent (C). Both are the builder's deliverables; creating them turns typecheck green. `_auth_fixtures`/`test_mcp_server`/`loremaster.server` resolve fine.
- **Receipt POINTERS:** RED tail → §Receipts; mechanism proofs → §Mechanism (measured this cycle); per-pin wrong-build analysis → §Per-pin.

---

## Mechanism (measured this cycle, HEAD e1dfa14 — the load-bearing claims the contracts rest on)

Two throwaway probes established the mechanisms; the durable instruments are the two committed contract files (the probes were removed). Reproductions:

**C — annotation derivation + mutation proof (store-free `build_mcp_server` + `list_tools()`):**
- 15 tools registered. Derived mutating (`readOnlyHint is not True`) = `{lore_claim_task, lore_comms, lore_findings, lore_index, lore_remember, lore_tasks}` (6); read-only = 9. Production annotations are CORRECT; the drift is in the test hand-list.
- MUTATION PROOF works: `monkeypatch.setattr(loremaster.server, "_TASK_TOOL_ANNOTATIONS", ToolAnnotations(readOnlyHint=True, …))` then rebuild → `lore_tasks` and `lore_claim_task` report `readOnlyHint=True` (moved partitions). A hand-list would not move.
- DENY-BY-DEFAULT: an unannotated `add_tool` yields `annotations=None`, `readOnlyHint=None` → `is not True` classifies it MUTATING; `== False` would leak it to read-only.
- Store-free: `build_mcp_server(LoreServer(config))` + `await mcp.list_tools()` needs no SurrealDB and no module-local surreal fixture (registration only).

**D — loopback wire + effect vs proxy (auth-independent, `wire_session(posture="loopback", principal=None, prepare=…)`):**
- The loopback wire path is HEALTHY at HEAD: `test_hosted_readonly_posture.test_the_loopback_posture_serves_the_full_surface_unauthenticated` PASSES (the 6 sibling failures are the #333 WIP — `Posture`/`HOSTED_REFUSAL_SECTION_HEADING` absent — NOT the wire).
- Over the wire: `refuse_first` tool → body=`MARKER`, effect_count=0; `run_then_refuse` tool → body=`MARKER` (BYTE-IDENTICAL), effect_count=1. A marker-observing proxy passes BOTH; only the effect counter separates 0 from 1. This is #295/WB48 constructed without auth.

---

## Per-pin — "what WRONG build still passes this?" (FIXTURES MUST DISCRIMINATE)

### Task C — `test_mutating_set_derivation.py` (8 RED / 2 GREEN-today)
- `test_the_production_partition_helper_exists` — RED (`loremaster.server.partition_tools_by_posture` absent). Kills: doing nothing, OR putting the derivation in test code (ruling: ONE production source).
- `test_every_registered_tool_carries_a_non_none_read_only_hint` — GREEN today. Kills: a tool shipped with `annotations=None` (silently writable under deny-by-default).
- `test_the_non_none_hint_pin_is_not_vacuous` — GREEN (positive control; an unannotated tool has `readOnlyHint=None`, proving the pin above can fire).
- `test_the_partition_covers_the_surface_exactly_and_is_disjoint` — RED. Kills: a partial partition (unclassified tools read as "nothing leaked").
- `test_deny_by_default_an_unannotated_tool_is_mutating` — RED. Kills BOTH `== False` (would leak a `None` to read-only) AND a hardcoded `return` that ignores `tools` (never sees the fresh probe).
- `test_the_derivation_equals_the_spec_predicate` — RED. Kills: a subtly different predicate (keying on `destructiveHint` / a name).
- `test_the_derivation_is_live_flipping_a_production_annotation_moves_the_tool` — RED. MUTATION PROOF (owed invariant b). Kills: a fixed hand-list (even one corrected to the right 6) AND a hardcoded return — neither tracks the flipped annotation.
- `test_the_known_mutating_tools_are_in_the_mutating_partition` — RED (import) / GREEN-once-derived. Independent CONTENTS oracle incl. `lore_claim_task`/`lore_tasks`. Kills: a real tool mis-annotated read-only.
- `test_the_known_read_only_tools_are_in_the_read_only_partition` — RED/GREEN-once-derived. Dual oracle (a mutating tool mis-annotated read-only = silently writable).
- `test_no_drifted_hand_list_survives_beside_the_derivation` — **RED on the #291 drift itself** (graded vs the contract's own `_spec_partition` oracle, deliverable-independent): `hand-list=['lore_comms','lore_findings','lore_index','lore_remember']` vs `derived=[…,'lore_claim_task',…,'lore_tasks']`. Kills: leaving the stale 4-name literal in place.

### Task D — `test_refusal_observes_effect.py` (5 RED / 1 GREEN-today)
- `test_the_helper_passes_a_refuse_first_build` — RED (helper absent). NEGATIVE control: a correct refusal (marker present, effect 0) must not be rejected (a gate that flags everything gets switched off).
- `test_the_helper_fails_a_run_then_refuse_build_on_the_effect_leg` — RED (helper absent). POSITIVE control (WB48): the helper MUST raise on the EFFECT leg (message names effect/run/invocation), not on a missing marker. Kills: a marker-only helper (it would pass this build).
- `test_a_marker_only_proxy_cannot_distinguish_the_two_builds` — **GREEN today** (self-contained #295 proof over the loopback wire): byte-identical bodies, proxy passes both, only the effect (0 vs 1) discriminates. Proves the controls are sound.
- `test_coverage_passes_when_the_sweep_observed_every_derived_pin` — RED (coverage primitive absent). Negative-space control.
- `test_coverage_fails_when_a_derived_pin_was_not_observed` — RED. Coverage-as-a-checked-variable: an un-swept derived refusal pin is RED and NAMED (`pin_d`). Kills: a sweep whose reach is a hidden constant.
- `test_coverage_fails_closed_on_an_empty_derived_set` — RED. Anti-vacuity: an empty enumeration is a broken sweep, not a pass.
- Recorded note in-file: the REAL `derived` set fed to the coverage check must itself be PROPERTY-derived + BOUND-stated (a refusal pin is not AST-crisp — #295 has no permanent structural gate; its standing guard is INSTRUMENT 0's reach-attack).

---

## Receipts

**RED tail (both files):**
```
FAILED tests/test_mutating_set_derivation.py::test_the_production_partition_helper_exists
FAILED …::test_the_partition_covers_the_surface_exactly_and_is_disjoint
FAILED …::test_deny_by_default_an_unannotated_tool_is_mutating
FAILED …::test_the_derivation_equals_the_spec_predicate
FAILED …::test_the_derivation_is_live_flipping_a_production_annotation_moves_the_tool
FAILED …::test_the_known_mutating_tools_are_in_the_mutating_partition
FAILED …::test_the_known_read_only_tools_are_in_the_read_only_partition
FAILED …::test_no_drifted_hand_list_survives_beside_the_derivation
FAILED tests/test_refusal_observes_effect.py::test_the_helper_passes_a_refuse_first_build
FAILED …::test_the_helper_fails_a_run_then_refuse_build_on_the_effect_leg
FAILED …::test_coverage_passes_when_the_sweep_observed_every_derived_pin
FAILED …::test_coverage_fails_when_a_derived_pin_was_not_observed
FAILED …::test_coverage_fails_closed_on_an_empty_derived_set
13 failed, 3 passed in 1.08s
```
**PASSED (3):** `test_every_registered_tool_carries_a_non_none_read_only_hint`, `test_the_non_none_hint_pin_is_not_vacuous` (C); `test_a_marker_only_proxy_cannot_distinguish_the_two_builds` (D).

**Gates on the two new files:** `ruff check` → All checks passed. Canonical mypy (repo root) → 2 errors = the 2 absent deliverables (RED-phase, builder resolves).

**lore usage:** lore-first throughout (`lore_findings action=get` for #291/#295; `lore_search`/`lore_read` for server + test scaffolding). Grep fallback SAID OUT LOUD and used ONLY for: (a) rename/textual-exhaustiveness — locating `_MUTATING_TOOLS`/`*_ANNOTATIONS` line sites + cross-import patterns (non-symbol textual seams), (b) confirming the #333 WIP boundary (git log/status). No lore weakness hit; nothing to file.

---

## What this does NOT claim (trust-doctrine self-check)
- The contracts are RED by design; I did not implement the deliverables. GREEN is the builder's, verified by the contract-adversary + cold audit.
- The D contract's controls model the WB48 shape with SYNTHETIC tools (refusal = a rendered marker in the body; effect = a per-tool counter). They do NOT exercise the auth posture guard (off-limits, #333 WIP). The general `Tool.run`-recorder observer for REAL tools is DEFERRED to packet 39 (ruling #3), not pinned here — it needs an external-guard scenario I cannot build auth-independently, and I say so rather than dress a reasoning bound as a structural pin.
- The coverage primitive is proven to discriminate on SYNTHETIC sets; the REAL enumeration of "refusal-shaped pins" is the builder's, property-derived and bound-stated (a note in-file), because a refusal pin is not AST-crisp.
- "SAME" grading is against e1dfa14; a concurrent sibling advancing HEAD past the C annotation constants would be the re-open trigger for the drift/mutation claims (they read `_MUTATING_TOOLS` + `_TASK_TOOL_ANNOTATIONS`).
