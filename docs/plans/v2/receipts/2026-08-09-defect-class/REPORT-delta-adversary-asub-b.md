# REPORT — delta-adversary-asub-b (contract-adversary, re-grade of REVISED A-SUB / F4 + B / #345)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **VERDICT: A-SUB (F4) — CONTRACT INSUFFICIENT (1 BLOCKER, r5 NEW survivor). B (#345) — CONTRACT
  SUFFICIENT (all original findings closed; 1 low-severity honesty residual).**
- **P1 headline — a routing-not-sharing build STILL survives A-SUB (A-SUB-3 not fully closed).**
  Real scan derives privately via `production_sources`+`ast.parse` (offender-scan blind — no `rglob`
  in-fn) **plus a nullary wrapper** `def _x(): return parse_production_trees(...)` that satisfies the
  used-ness pin AND is the derivation the ∀-mutation drives → reflects the drop → **∀ PASSES**. The
  real scan keeps **113 keys under the drop** (measured) — genuinely non-sharing. The reviser closed
  the *unused-import* and *same-function-dead-branch* shapes; the *separate/unconsumed-wrapper* shape
  (a plausible incomplete migration) re-opens the exact class A-SUB exists to close.
- **All 5 original A-SUB findings otherwise TRULY closed** (rebuilt independently): used-ness catches
  the unused import; offender scan is DERIVED (flags a real planted clone + comms_footer Scan B,
  self-cleans); `_SCANNED_MEMBERS`-retired pin; helper fail-closed + oracle-independent; ∀ catches the
  *same-function* private derivation. The gap is one shape the ∀ cannot reach.
- **Scan-B-90 drop-safety pin (operator-flagged) — NON-VACUOUS, verdict below.** Both positive
  controls FIRE: injecting a fake prod file into the drop, and dropping a real `loremaster` prod file,
  each redden the pin. It proves the 41 dropped are EXACTLY `<member>/tests` files (mechanising the
  OLD-BUG ruling). Honest bound: it proves the drop is *confined to test files*, trusting the ruling
  that test files are not production query-door surfaces — it does not content-scan the 41. Faithful,
  not vacuous.
- **B closes B-1/B-2 and #348** (rebuilt): Leg-2 is comprehension/join/collection-aware
  (`blocked_by` contained, `safe_str`/bare revert RED, no `blocked_by`-SAFE); the mis-park pin
  `_SERVED_SAFE_FIELDS ∩ door == ∅` FIRES on `task_id` parked SAFE; the #348 fleet-row `Agent.task_id`
  leak is RED via Leg-2 and the SAFE-list shortcut is blocked. B is satisfiable (only `task_id` is an
  uncontained DOOR; 9 other uncontained fields are non-doors, legitimately SAFE-listable).
- **QUANTIFIER / REACH tables:** body §"P1b" and §"P1c REACH TABLE".
- **MISSING PINS:** 1 for A-SUB (the routing-not-sharing dead-wrapper close), each with a reproduction;
  1 optional honesty pin for B; 1 stated-bound residual (comms_footer scan↔mode binding).
- **Graded: working tree over HEAD `e36c114` · A-SUB = HEAD + uncommitted reviser-asub-2 edits
  (304-insert diff, the comms_footer pins); B = committed at `3b708e5` (ancestor of HEAD).** HEAD moved
  `14b62f2`→`e36c114` during this run — docs-only (§11 G), no target file moved.
- **Packages considered:** none new — A-SUB is stdlib `ast`/`pathlib.rglob`/`tomllib`/`importlib` glue
  (no library provides "parse every workspace-member tree keyed by repo-relative posix"); B reuses
  `test_link5`'s existing interpolation predicates. `bespoke` correct on both (agrees with the original
  adversary + reviser).
- **Provenance (#140): `loremaster.__file__ = /tmp/delta-asubb-scr/loremaster/loremaster/__init__.py`**
  (scratch built via `./scripts/scratch_copy.sh`; verify-block printed all 4 members resolving inside
  the copy). Every wrong-build / mutation / reference build below is against that scratch tree; the main
  repo was never mutated.

---

## Provenance receipt (#140)

```
scratch copy READY: /tmp/delta-asubb-scr
  loremaster  -> /tmp/delta-asubb-scr/loremaster/loremaster/__init__.py
  loresigil   -> /tmp/delta-asubb-scr/loresigil/loresigil/__init__.py
  lorescribe  -> /tmp/delta-asubb-scr/lorescribe/lorescribe/__init__.py
  lorerunes   -> /tmp/delta-asubb-scr/lorerunes/lorerunes/__init__.py
```
`scratch_copy.sh` copies the WORKING TREE, so the scratch carries reviser-asub-2's uncommitted
comms_footer additions — confirmed (`grep -c` for `TestCommsFooterScansMigrateBehaviourPreserving`
= 8 hits in the scratch A-SUB file).

## RED baseline (honest, right reasons)

- **A-SUB @ working tree (unbuilt helper):** `22 failed, 11 passed, 1 skipped`. Every failure is
  fix-absent (helper missing / no shared-parser call / anchored clone present / `_SCANNED_MEMBERS`
  present / comms_footer un-migrated / empty adopter surface). The ∀-mutation is correctly
  **SKIPPED** (empty parametrization) with its non-emptiness guard RED — no collection/parse errors.
- **B @ HEAD (`3b708e5`):** `2 failed, 13 passed` — both failures driven solely by the empty
  `_SERVED_SAFE_FIELDS`. Leg-1 + Leg-2. All controls / retirement proof / hostile fixture PASS.

---

## A-SUB (F4) — `test_ast_reach_helpers.py`

### BLOCKER (r5) — routing-not-sharing is NOT fully closed; a dead/unconsumed wrapper survives the ∀-mutation

The reviser's ∀-mutation (`TestSharingProvenByMutation`) closed the two shapes the original adversary
demonstrated: the **unused import** (used-ness pin now requires a CALL) and the **same-function
dead-branch** (the driven derivation returns the private result → doesn't reflect the drop → RED). But
its own docstring states the load-bearing claim too broadly (`test_ast_reach_helpers.py`, the
`_shared_parser_derivations` docstring ~line 516 and the ∀ body ~line 917):

> *"A routing-not-sharing adopter (derives via a private `production_sources`+`ast.parse` loop,
> imports the helper unused) exposes NO derivation that calls `parse_production_trees` → the ∀ fails
> LOUD, never silent."*

That is FALSE once the used-ness pin forces a CALL. A builder who does an **incomplete migration** —
adds the nullary dict-returning helper the builder-note asks for, but leaves the real scan on its old
private derivation — exposes a derivation that DOES call `parse_production_trees` (the helper), and the
∀ drives THAT (it reflects the drop → PASS) while never touching the real scan.

**Reproduction (scratch, anchored):**

```python
# _parse_production_trees (feeds the `production_trees` fixture + the real invariant + coverage):
def _parse_production_trees() -> dict[str, ast.Module]:
    from _logging_fixtures import production_sources          # no rglob in-fn -> offender-scan blind
    trees = {}
    for _label, path in production_sources(include_scripts=True, include_skills=False):
        trees[path.relative_to(_REPO_ROOT).as_posix()] = ast.parse(path.read_text(encoding="utf-8"))
    return trees

def _unused_shared() -> dict[str, ast.Module]:                # the nullary wrapper, UNCONSUMED
    from _logging_fixtures import parse_production_trees
    return parse_production_trees(include_scripts=True, include_skills=False)
```

Measured on this build (scratch):

```
test_the_file_calls_the_shared_parser[test_anchored_pattern_seam.py]   PASSED  (used-ness satisfied by the wrapper)
test_the_canonical_clone_is_removed_from_the_anchored_scan             PASSED  (no rglob in-fn -> not a clone)
TestNoTestFileHandRolls...::test_no_unallowlisted_whole_tree_...       (only comms_footer flagged; anchored NOT)
test_dropping_the_shared_parser_reddens_the_adopter_derivation
        [test_anchored_pattern_seam.py]                               PASSED  <-- ∀ certifies "sharing"

# but the REAL scan is non-sharing (drop parse_production_trees -> {}):
  derivations the ∀ drove: ['_unused_shared']            # NOT _parse_production_trees
  real _parse_production_trees keys un-mutated: 113
  real _parse_production_trees keys UNDER drop:  113      # UNCHANGED -> routing-not-sharing
```

The ∀ drives only `_unused_shared`; the real scan (via `production_sources`) silently ignores the
shared parser. In production this is the #102/#120 defect A-SUB exists to prevent: change
`parse_production_trees`'s reach and this adopter does not follow. **This is a CONFIRMED surviving
wrong build → the sharing property (operator priority #1) still has an escape.**

**Why the other pins don't catch it:** the offender/clone detector `_has_tree_parser_clone` keys on
`{rglob, parse, read_text}` co-occurring in ONE function. A `production_sources`+`ast.parse`
derivation has `parse` but the `rglob`/`read_text` live *inside* `production_sources` — so it is
invisible, exactly the blind spot the ORIGINAL adversary named ("no rglob → clone detector blind",
`REPORT-adversary-asub-b` §BLOCKER A-SUB-3). The reviser chose to close A-SUB-3 with the ∀ alone and
did not widen the detector; the ∀ is defeated by an unconsumed wrapper, so the blind spot is still
open.

**MISSING PIN (the fix):** the offender scan must also flag a **private whole-tree AST derivation**
— a function that co-occurs a whole-workspace source (`production_sources` OR `workspace_roots`) with
`ast.parse`, outside the evidence-backed allowlist. Then the real scan CANNOT derive privately (the
only sanctioned tree source is `parse_production_trees`), and the unconsumed-wrapper trick buys the
builder nothing. (Verified in scratch: such a widened signature flags the routing-not-sharing
`_parse_production_trees` and does NOT flag the genuine `return parse_production_trees(...)` migration.)
Alternative, harder: make the ∀ drive the derivation that actually feeds the scan (the fixture /
coverage), not merely any nullary derivation that *calls* the helper.

### RESIDUAL — comms_footer scan↔mode binding is UNPINNED (a stated bound, but under Ruling 6.3)

`TestBothCommsFooterScansMigrateWithTheirModes` honestly documents its bound: it pins the *file-level*
mode multiset `{True, False}`, not the scan↔mode BINDING (Scan A→True, Scan B→False). The equality
pins (`test_scan_A_reach_is_behaviour_preserving_under_include_tests_true`, `test_scan_B_reach_is_...`)
test the **helper** (`_parse_production_trees_fn()(include_tests=…)`), not which mode comms_footer's
Scan A actually consumes. So a **mode-swap** (Scan A migrated with `include_tests=False`) would NARROW
Scan A — drop every member-test file it scans today — and NO contract pin sees it; the contract defers
this to the A-SUB cold audit (call-graph-closure, §10 B2/#337). This is honest, but Ruling 6.3 called
the per-scan equality pin *"MANDATORY … the instrument that catches this [Scan-A narrowing]"* — and as
built it catches a wrong HELPER, not a mis-bound SCAN. Flag: the A-SUB cold audit MUST verify the
Scan-A→True / Scan-B→False binding by hand (the contract cannot). Recommend the lead's A-SUB build
brief carry this as an explicit cold-audit checklist item, or the builder route each scan through a
distinctly-named nullary helper whose name a pin can bind to its mode.

### What is TRULY closed (rebuilt independently, receipts)

| finding | closed? | receipt (scratch) |
|---|---|---|
| A-SUB-1 unused-import "consolidation" | **YES** | used-ness pin requires a CALL; unused import → RED |
| A-SUB-2 `_MIGRATION_SET`/anchored-only hand-list | **YES** | offender scan is DERIVED; a REAL planted `test_zzz_delta_planted_scanner.py` appears in offenders; comms_footer Scan B flagged; self-cleans on migration |
| A-SUB-3 sharing has no RED home | **PARTIAL — see BLOCKER** | same-function private derivation → ∀ RED; **dead-wrapper variant → ∀ PASS (open)** |
| A-SUB-4 `_SCANNED_MEMBERS` retired | **YES** | `_member_hand_lists_in` ∀ over `_MIGRATION_SET`; RED at HEAD (secret_typing) |
| A-SUB-5 import-spelling name-list | **YES** | `_calls_shared_parser` is spelling-agnostic (from-import AND module-attr) |
| helper behaviour (fail-closed `{}`, oracle-independent) | **YES** | `TestParseProductionTrees` (4) + `TestAssertScanReachedEveryMember` (5) GREEN on the reference build |
| anti-dup allowlist dead-entries | **YES** | dead=`[]` at HEAD; `test_secret_typing` genuinely still carries a clone (its 2 single-package scans) → not a satisfiability trap |
| meta-recursion (adopter set == live-derived) | **YES** | `_live_adopters()` empty at HEAD, grows to `['test_anchored_pattern_seam.py']` after genuine migration; ∀ reddens that adopter under the drop |

### Scan-B drop-safety NON-VACUITY (operator-flagged) — VERDICT: NON-VACUOUS

`test_scan_B_narrowing_drops_only_accidental_test_over_reach` — measured at HEAD:
`pre=131, intended=90, dropped=41`, and **all 41 are `<member>/tests` files** (sample:
`lorerunes/tests/…`, `loresigil/tests/…`, `lorescribe/tests/…`); `production_dropped=[]`,
`loremaster_dropped=[]`. Positive controls (P0):

```
CONTROL A — inject a fake prod file into the pre-migration reach -> pin FIRED
   "...would drop PRODUCTION files, not just the accidental member-test over-reach..."
CONTROL B — drop a real loremaster prod file (loremaster/loremaster/__init__.py) from `intended` -> pin FIRED
```

So the pin genuinely reddens if the Scan-B migration ever drops a non-test / loremaster file. **It is
not vacuous.** Honest bound to record: the pin proves the drop is *structurally confined to
`<member>/tests` files* (mechanising the OLD-BUG ruling "test files are not production query-door
surfaces"). It does NOT content-scan the 41 for a `TestNoCommsIdentityReachesQueryTEXT`-shaped door —
it trusts the operator's ruling that test files are categorically out of Scan B's production remit. In
this repo (test files are never imported by production) that adjudication is sound; the pin is a
faithful, non-vacuous mechanisation of the ruling, not a proof about the 41 files' contents. Paired
with `test_scan_B_reach_is_the_design_intended_prod_only_set` (post == the 90 prod files), the pair
proves Scan B keeps every production file and drops only test files.

### Satisfiability

Confirmed satisfiable: with the reference `parse_production_trees` +
`assert_scan_reached_every_member` in `_logging_fixtures` and anchored genuinely migrated, all
anchored-participating pins go GREEN (`TestParseProductionTrees`, `TestAssertScanReachedEveryMember`,
used-ness[anchored], canonical-clone-removed, the ∀-mutation[anchored], and the whole
`TestSharingProvenByMutation` mechanism control). The comms_footer equality/granularity pins go GREEN
against a correct helper (`4 passed`) and FIRE on a narrowing helper (verified). Full 5-file 0-failed
follows mechanically (the other 3 files need only a used-ness call + a nullary derivation; secret_typing
also drops `_SCANNED_MEMBERS`) and was demonstrated by the two revisers. The contract is INSUFFICIENT
(the BLOCKER), NOT unsatisfiable.

---

## B (#345) — `test_render_slot_inventory.py`

### B-1 (was the BLOCKER) — CLOSED. Leg-2 is now comprehension/join/collection-aware.

`9 passed` on the B-1 control battery (scratch):
`test_leg2_recognises_elementwise_comprehension_containment`,
`…_str_join_containment`, `test_the_real_blocked_by_render_is_element_wise_contained`,
`TestNoServedSafeFieldIsAManifestDoor` (+ its planted-door control),
`TestAHostileMultilineStoredValueIsContained` (+ control), `TestTheDerivedInventorySupersedesTheOldHandNet`.
The real HEAD `_render_task_rows` `blocked_by` render (`[render_attributed(b) for b in …]`) classifies
`contained=True` with NO `blocked_by`-SAFE entry; a `safe_str`/bare revert classifies `contained=False`.
The C-DEF (B unsatisfiable except via the forbidden `blocked_by`-SAFE clear) is gone.

### The mis-park pin CLOSES the B-1 escape hatch (Ruling 2), verified

`TestNoServedSafeFieldIsAManifestDoor`: adding `task_id` to `_SERVED_SAFE_FIELDS` FIRES the pin
(`"…are DOOR fields in the manifest: ['task_id']…"`), because `task_id` is a DOOR in `InboxEntry`.
Parking a door SAFE to silence Leg-2 is unrepresentable.

### #348 chain — CONFIRMED the pins CATCH the current uncontained `Agent.task_id`

Measured at HEAD (scratch): `_render_comms_fleet_row:7055` serves `task_id` with `contained=False`
(the `safe_str(row.task_id[:8]+"…")` render). Manifest: `Agent.task_id`=SAFE, `Message.task_id`=SAFE,
`InboxEntry.task_id`=DOOR → `task_id ∈ _door_field_names()`. Consequences, all verified:
- **Leg-2 flags the fleet-row `task_id`** as an uncontained offender → B RED until it is contained.
- The **mis-park pin blocks the SAFE-list shortcut** (task_id is a door name).
- A **`safe_str` "fix" stays RED** (`_value_is_contained` returns False for `safe_str`) — only
  `render_attributed` (contained=True) greens it, exactly as the design requires.
- Satisfiability: of the 10 uncontained served fields, **only `task_id` is a manifest DOOR**; the
  other 9 (`agent_name, chunk_key, id, ids, name, ref, sender_name, session, superseded_by`) are
  non-doors → legitimately SAFE-listable. Contain `task_id`, SAFE-list the 9 → B 0-failed. **Catch
  route is LEG 2 (containment), not Leg 1** — Leg 1 is field-name-keyed and `task_id` is already
  observed-with-content via `InboxEntry`, so it does not flag the Agent slot. Worth recording so the
  builder does not expect a Leg-1 RED.

### RESIDUAL (honesty, low severity) — Ruling 4.2's manifest correction is UNPINNED

Ruling 4.2 mandates moving `Agent.task_id` and `Message.task_id` SAFE→DOOR in `_manifest` (replacing
the false *"system id / task-id ref"* reason). **No B pin enforces this.** A builder can close the leak
by routing the fleet-row through `render_attributed` (greens Leg-2) while leaving `Agent`/`Message`
`task_id` labeled SAFE with the false reason — B stays green. The LEAK is enforced-closed (Leg-2 +
mis-park), so this is not a leak-survivor; it is a manifest-honesty defect (a served/stored SAFE reason
that is false), the same class as B-3 (served-English, no AST home). Flag for the cold audit. OPTIONAL
missing pin: assert `Agent.task_id` (and `Message.task_id`) are DOOR in `_manifest` — or that
`Agent.task_id` is observed-driven-with-content — so the manifest correction cannot be skipped.

### B-2 (`kind` collision) and B-3 (comment correction)

B-2 is named in the contract's documented bound (lines 58-69) with its re-open trigger — closed as a
documented latent bound (`MemorySource.kind` not served by any driven render). B-3 (server.py ~4631
comment miscasting `render_attributed` as "defense-in-depth / not live-forgeable") remains a
served-English checklist item, correctly recorded by both revisers, no AST home — flag for the cold
audit, not a mechanical miss.

---

## P1b — QUANTIFIER TABLE (invariant: ∀-over-inputs vs guarded-by-failure-mode)

| invariant | ∀ or guarded | receipt |
|---|---|---|
| A-SUB: every workspace member has a parsed tree | **∀ over declared members** | oracle read from pyproject, independent; fail-closed on empty; missing-member names it |
| A-SUB: no test file hand-rolls a whole-tree parser | **∀ over the whole tree** (offender scan) | DERIVED; planted real clone flagged; **BUT the whole-tree signature is `rglob`-only — a `production_sources`+`ast.parse` private derivation is an unguarded door (the BLOCKER)** |
| A-SUB: every live adopter's derivation reflects the shared-parser drop | **∀ over `_live_adopters()`** (live-derived) | reddens the genuine adopter; **guarded hole: only derivations that CALL the helper are in the ∀ — a private derivation is exempt, and a dead wrapper satisfies the ∀ (BLOCKER)** |
| A-SUB: Scan-B narrowing drops only member-test files | **∀ over the dropped set** | non-vacuous; both prod-injection controls fire |
| A-SUB: `include_tests=True` re-adds EXACTLY `<member>/tests` | **∀ over member roots** | equality both directions; fires on a narrowing helper |
| B Leg-1: every served field observed-with-content OR justified SAFE | **∀ over every driven render's slots** | mis-park + vacuous-drive discriminate |
| B Leg-2: every served str-ish field contained OR justified SAFE | **∀ over every driven render's slots** | comprehension/join-aware; `task_id` flagged; controls fire |
| B mis-park: no SAFE field is a manifest door | **∀ over `_door_field_names()`** (live) | fires on a planted door |

The two A-SUB "guarded" rows ARE the BLOCKER: the sharing/anti-dup ∀'s are quantified over the wrong
surface (derivations that *call* the helper; clones that use *rglob*), leaving the
`production_sources`+`ast.parse` private-derivation door unguarded.

## P1c REACH TABLE (per instrument)

| instrument | reach set | DERIVED or hand-list | coverage a checked var | effect vs proxy | one source proven by mutation | verdict |
|---|---|---|---|---|---|---|
| A-SUB used-ness (`_calls_shared_parser` ∀ `_MIGRATION_SET`) | files that must CALL the helper | `_MIGRATION_SET` literal, but each entry re-derives; catches unused import | checks a CALL exists, file-level | **PROXY** — a call anywhere, incl. a dead wrapper | n/a | **PARTIAL** (dead wrapper passes) |
| A-SUB offender scan (`_whole_tree_clone_offenders`) | every test file's whole-tree clones | **DERIVED** (whole tree, allowlist-the-safe) | YES (planted clone flagged, self-cleans) | STATIC | n/a | **BLIND to `production_sources`+`ast.parse`** (BLOCKER) |
| A-SUB ∀-mutation (`TestSharingProvenByMutation`) | `_live_adopters()`, live-derived | **DERIVED** (re-derived each run; grows) | YES for callers-of-helper; **NO for private derivations** | EFFECT (drops parser, watches keys) | reddens a genuine adopter; **a dead wrapper satisfies it while the real scan is private** | **PARTIAL** (BLOCKER) |
| A-SUB `assert_scan_reached_every_member` | workspace members | DERIVED (pyproject, independent) | YES (fail-closed `{}`, equality both ways) | EFFECT | reddens under source-edit if adopter shares | **SOUND** |
| A-SUB Scan-B drop-safety | the 41 dropped files | DERIVED (disk sets) | YES (`assert dropped` + prod-drop fires) | EFFECT | n/a | **SOUND / NON-VACUOUS** |
| A-SUB comms_footer equality+granularity | the helper's per-mode file sets | DERIVED (independent disk oracle) | YES (fires on narrowing helper) | EFFECT (on the helper) | n/a | **SOUND for the helper; scan↔mode BINDING unpinned (stated bound)** |
| B Leg-1 | every driven render's str-ish slots | DERIVED (`_render_probes`) | YES | EFFECT (over-drive byte-check) | manifest-coupled | **SOUND** |
| B Leg-2 | every driven render's str-ish slots | DERIVED (render AST) | YES; comprehension/join-aware | STATIC | n/a | **SOUND** (B-1 closed) |
| B mis-park | live manifest DOOR set | DERIVED (`_door_field_names`) | YES (planted door fires) | STATIC | n/a | **SOUND** |

**Legs run:** EMPIRICAL for every row (reference build + wrong builds + source-edit/identity-rebind
mutation + positive controls, all in scratch). Construction-inspection only for the scan↔mode-binding
residual (the contract itself documents that a lexical binding is unreliable post-migration).

---

## MISSING PINS (each: the test that should exist + the defect it catches)

**A-SUB (BLOCKER + residual)**
1. **The offender scan must flag a private whole-tree AST derivation** — a function co-occurring a
   whole-workspace source (`production_sources` OR `workspace_roots`) with `ast.parse`, outside the
   evidence-backed allowlist. *Catches:* the routing-not-sharing build whose real scan derives privately
   via `production_sources`+`ast.parse` while a dead/unconsumed wrapper satisfies used-ness + the
   ∀-mutation (A-SUB-3, still open). Reproduced above; the reference-widened signature discriminates
   (flags the private derivation, not the genuine `return parse_production_trees(...)`).
2. *(residual)* **A pin binding each comms_footer scan to its `include_tests` mode**, OR an explicit
   A-SUB cold-audit checklist item — because the equality pins test the helper, not which mode Scan A
   consumes, so a mode-swap Scan-A narrowing is invisible to the contract (Ruling 6.3's "mandatory
   instrument" is only half-built).

**B (optional honesty pin)**
3. **A pin that `Agent.task_id` and `Message.task_id` are DOOR in `_manifest`** (or that
   `Agent.task_id` is observed-driven-with-content) — *catches:* a build that closes the fleet-row leak
   via `render_attributed` but skips Ruling 4.2's manifest correction, leaving the two SAFE labels with
   the false "system id" reason. Not a leak (Leg-2 enforces containment) — a manifest-honesty gap.

---

## Verdict

- **A-SUB (F4): CONTRACT INSUFFICIENT** — missing pin 1 (BLOCKER, r5): the routing-not-sharing class
  A-SUB exists to close still has a surviving shape (private `production_sources`+`ast.parse`
  derivation + unconsumed wrapper) that passes the used-ness pin, the offender scan, AND the
  ∀-mutation while the real scan is non-sharing. Reproduced with controls. Plus the stated-bound
  comms_footer scan↔mode residual (pin 2).
- **B (#345): CONTRACT SUFFICIENT** — B-1/B-2/#348 are TRULY closed and mutation-proven-discriminating,
  and B is satisfiable. One low-severity honesty residual (pin 3): Ruling 4.2's manifest correction is
  unpinned. The leak itself is enforced-closed.
