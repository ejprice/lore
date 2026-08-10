# REPORT — reviser-asub-b (Opus CONTRACT reviser, A-SUB / F4 + B / #345)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State: done-with-decisions.** Both contracts revised per §9.7; RED at HEAD for the right
  reasons; new pins go 0-failed against a demonstrated fix (scratch receipt + sim).
- **Files edited (writable set, nothing else touched):**
  `loremaster/tests/test_ast_reach_helpers.py` (A-SUB), `loremaster/tests/test_render_slot_inventory.py` (B).
- **A-SUB closes A-SUB-1/-2/-3/-4/-5** — import-is-USED pin (call, not import), a DERIVED anti-dup
  clone scan (retry-seam offender shape, allowlist-the-SAFE), a `_SCANNED_MEMBERS`-retired pin, and a
  live-derived ∀-MUTATION via reused `_rebind_everywhere` that **empirically catches
  routing-not-sharing** (used-ness GREEN, ∀ RED). Spelling-agnostic used-ness dissolves A-SUB-5.
- **B closes B-1 + adds the mis-park pin + names `kind` (B-2)** — `_served_slots` is now
  COMPREHENSION/ join/collection-AWARE via `_value_is_contained` (extends test_link5's `_CONTAIN_VERBS`,
  no fork): the Ruling-2-correct `[render_attributed(b) for b in task.blocked_by]` is GREEN, a
  `safe_str`/bare revert is RED, WITHOUT any `blocked_by`-SAFE entry. New pin
  `_SERVED_SAFE_FIELDS ∩ manifest-DOOR == ∅` mechanises Ruling 2.
- **RED confirmed for the right reason:** A-SUB `17 failed / 9 passed / 1 skipped` (all 17 fix-absent:
  helper missing · no shared-parser call · anchored clone present · `_SCANNED_MEMBERS` present · empty
  adopter surface — no parse/collection errors; the ∀ is correctly skipped-not-green under a RED
  non-emptiness guard). B `2 failed / 13 passed` (Leg-1 + Leg-2 driven solely by the empty allowlist).
- **§9.6 symbols reused (generalise, not invent):** `_rebind_everywhere` (from
  `test_store_seam_one_derivation`, promotion-tolerant accessor) · the `_all_sdk_call_sites` /
  `_unseamed_sdk_call_sites` OFFENDER-enumeration SHAPE (anti-dup scan) · test_link5's
  `_CONTAIN_VERBS` / `_raw_render_interpolations` / `_manifest` / `_render_probes` / `_field_token` /
  `_leaks` (B, imported — not forked).
- **Satisfiability:** A-SUB **PROVEN in scratch** (`/tmp/asubb-sat2`, provenance
  `loremaster.__file__=/tmp/asubb-sat2/loremaster/loremaster/__init__.py`): reference helpers built +
  anchored migrated → every new A-SUB pin GREEN incl. the load-bearing ∀-reflection; a
  routing-not-sharing wrong build was CAUGHT (used-ness GREEN, ∀ RED). B satisfiability re-derived by
  sim (below) — 0-failed via containment of the fleet-row door + a non-door SAFE allowlist.
- **DECISIONS-NEEDED (3):** (1) comms_footer §5/§7 scope fork; (2) fleet-row `task_id` — a LIVE
  field-name collision the mis-park pin surfaces (contain-in-production vs model-precise keying);
  (3) `_rebind_everywhere` promotion (now ≥2 reusers). See §"Decisions-needed".
- **B-3 checklist item (recorded, not pinned):** the server.py `_render_task_rows` comment
  (lines 4631-4634, *"defense-in-depth, though this field is NOT live-forgeable"*) still miscasts
  `render_attributed` as secondary. Builder/cold-audit fix — served-English, no AST home.
- **Graded: 962eeb6 · HEAD-at-report: 962eeb6 · SAME.** Adversary graded 405d321 (ancestor of HEAD);
  the 2 intervening commits are docs-only (the design doc §9) — no target code moved.
- **Packages considered:** none — A-SUB is stdlib `ast`/`importlib`/`tomllib` test glue; B reuses
  test_link5's existing AST predicates. No mechanism a library provides. `bespoke` correct on both.

---

## A-SUB — `test_ast_reach_helpers.py` (F4)

### What changed (each pin → the wrong-build it closes)

| pin (class::test) | closes | RED-at-HEAD reason |
|---|---|---|
| `TestTheMigrationSetRoutesThroughTheSharedHelpers::test_the_file_calls_the_shared_parser` (∀ `_MIGRATION_SET`) | **A-SUB-1** (unused-import "consolidation") + **A-SUB-5** (import-spelling name-list) — now a CALL, spelling-agnostic | no file CALLs `parse_production_trees` yet |
| `TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist` (offender scan + vacuity/dead-entry/planted controls) | **A-SUB-2** (`_MIGRATION_SET`/anchored-only clone hand-lists; a new-file clone invisible) | `test_anchored_pattern_seam._parse_production_trees` is an un-migrated, un-allowlisted whole-tree clone |
| `TestTheMemberHandListsAreRetired` (∀ `_MIGRATION_SET`) | **A-SUB-4** (`_SCANNED_MEMBERS` survived green) | `test_secret_typing._SCANNED_MEMBERS` still declared |
| `TestSharingProvenByMutation` — non-emptiness guard + mechanism control + ∀ over `_live_adopters()` | **A-SUB-3** (sharing had NO RED home; routing-not-sharing survived static pins) | live adopter surface is empty (helper unbuilt) |

The two shared-helper behaviour blocks (`TestParseProductionTrees`, `TestAssertScanReachedEveryMember`)
and the two clone-detector controls are LEFT SOUND, unchanged (adversary graded them discriminating).

### The ∀-mutation is a genuine RUNTIME RED home (IDIOM 1 / LEG B, reusing `_rebind_everywhere`)

- **reach is a CHECKED VARIABLE (§9.1 meta-recursion):** the ∀ parametrizes over `_live_adopters()` —
  files that CALL `parse_production_trees`, re-derived from the tree each run, never a fixture constant.
  A `test_the_live_adopter_surface_is_non_empty` guard fails closed so the parametrization can never
  pass vacuously (RED at HEAD: empty).
- **reaches FROM-imports:** `_rebind_everywhere` rebinds by identity across `sys.modules`. **Verified
  empirically this cycle** (`test_the_rebind_mutation_reaches_a_from_import_binding`, GREEN now+after):
  a from-import router reddens under the drop, a private clone does not. The single-module monkeypatch
  the adversary flagged does NOT reach a from-import binding — measured.
- **drives the DERIVATION, not the coverage TEST (robustness):** anchored's coverage node takes a
  `production_trees` FIXTURE (not `self`-only), so I drive the adopter's own nullary tree derivation
  and prove its returned keys CHANGE under `parse_production_trees→{}`. A private
  `production_sources`+`ast.parse` copy does not change → caught. Bound stated in the docstrings: an
  adopter whose only shared-parser call sits in a fixture-taking node uses the `scripts/mutation_proof.py`
  receipt route (§9.7 OR-clause) — and the pin fails LOUD (never silent) when no in-process derivation
  exists, so the bound is never a false clear.

### Satisfiability RECEIPT (scratch, #140 provenance printed)

Scratch built via `./scripts/scratch_copy.sh /tmp/asubb-sat2`;
`loremaster.__file__ = /tmp/asubb-sat2/loremaster/loremaster/__init__.py` (isolated). Added the
reference helpers to `_logging_fixtures` + migrated `test_anchored_pattern_seam`
(`_parse_production_trees` → routes through `parse_production_trees`; `TestScanCoverage` → calls
`assert_scan_reached_every_member`). Result — every anchored-participating pin GREEN:

```
PASSED TestParseProductionTrees::*                                        (4)
PASSED TestAssertScanReachedEveryMember::*                                (5)
PASSED …::test_the_file_calls_the_shared_parser[test_anchored_pattern_seam.py]
PASSED …::test_the_canonical_clone_is_removed_from_the_anchored_scan
PASSED TestNoTestFileHandRolls…::test_no_unallowlisted_whole_tree_parser_clone_survives (+3 controls)
PASSED TestTheMemberHandListsAreRetired::…[anchored|backoff|secret_leak]
PASSED TestSharingProvenByMutation::test_the_rebind_mutation_reaches_a_from_import_binding
PASSED TestSharingProvenByMutation::test_the_live_adopter_surface_is_non_empty
PASSED TestSharingProvenByMutation::test_dropping_the_shared_parser_reddens_the_adopter_derivation[test_anchored_pattern_seam.py]
```
Only un-migrated files stayed RED (used-ness/member-retired for backoff/secret_typing/secret_leak) —
expected; mechanically identical once migrated. (Post-fix re-verification with the final contract:
`TestSharingProvenByMutation` + anchored used-ness + anti-dup = 5 passed.)

**Self-review correction (satisfiability across ALL adopters, not just anchored):** an early draft of
the ∀ pin also asserted each adopter routes its coverage through `assert_scan_reached_every_member` —
but per §7 only 2 files (anchored, secret_typing) adopt the coverage helper; `backoff`/`secret_leak`
adopt only the PARSER (for domain scans). That assertion would have made those two UNSATISFIABLE even
when correctly migrated (a C-DEF I would have shipped). Removed: the derivation-reflects-the-drop check
IS the sharing proof (a private copy does not reflect it), independent of whether the adopter feeds a
member-reach coverage or a domain scan.

**Discrimination proven:** a routing-not-sharing wrong
build (calls `parse_production_trees` in a dead branch to satisfy used-ness, derives via a private
`production_sources`+`ast.parse` loop) → used-ness GREEN, but the ∀ RED:
`…did NOT reflect the shared-parser drop (keys unchanged: 113) — routing-not-sharing… A-SUB-3.`

### The anti-dup allowlist (evidence, ground-truthed at HEAD)

Clone-signature (`rglob`+`ast.parse`+`read_text` co-occurring) offenders at HEAD are: anchored (migrate),
`test_comms_footer._scan` (§7 adopter, PROVISIONAL allowlist — see decision #1), and the single-package
scanners `test_link5`/`test_render_seam_pins`/`test_task_read_surface`/`test_text_hygiene`/`test_retry_seam`/
`test_retired_symbols`/`test_secret_typing` (allowlisted with §7 reasons). backoff/secret_leak already
route `production_sources` (no clone signature). File-keyed allowlist matches §7's "allowlist non-adopter
FILES"; a dead-entry pin self-cleans a stale entry (e.g. the day comms_footer migrates).

---

## B — `test_render_slot_inventory.py` (#345)

### What changed (each item → what it closes)

- **(a) Leg-2 is COMPREHENSION-AWARE (closes B-1, the BLOCKER / C-DEF).** New `_value_is_contained(expr)`
  — element-wise, recursive, reusing the file's existing `_CONTAIN_VERBS`: a direct
  `render_attributed(...)`, a comprehension whose `elt` is contained, a `str.join(...)` of contained
  content, and a literal collection of contain-calls are all CONTAINED; a bare / `safe_str` /
  `sanitise_line` leaf is not. `_render_call_value_slots` and `_served_slots` (via
  `_elementwise_contained_fstring_slots`) now route through it — **no fork of `_raw_render_interpolations`**.
  Conservative by construction (unproven ⇒ uncontained ⇒ a builder tax, never a leak greened).
  - **Result (measured):** `blocked_by` is no longer a Leg-2 offender; the real HEAD `_render_task_rows`
    `[render_attributed(blocker) for blocker in task.blocked_by]` classifies CONTAINED
    (`test_the_real_blocked_by_render_is_element_wise_contained`), while `safe_str`/bare reverts are RED
    (`test_leg2_recognises_elementwise_comprehension_containment` / `…_str_join_containment`) — the
    discriminating pin Ruling 2 mandates, WITHOUT a `blocked_by`-SAFE entry. B is no longer unsatisfiable.
- **(b) new pin `TestNoServedSafeFieldIsAManifestDoor` (mechanises Ruling 2).**
  `_SERVED_SAFE_FIELDS ∩ _door_field_names() == ∅`, reach = the LIVE manifest DOOR set re-derived each
  run (§9.1), + a positive control that the intersection catches a planted door. The B-1 escape hatch
  (park a door SAFE to silence Leg-2) is unrepresentable. GREEN at HEAD (empty allowlist) and after
  (a standing guard, not a fix-absent RED).
- **(c) `kind` named in the field-name-collision bound (B-2).** Docstring bound now names BOTH `task_id`
  (DOOR InboxEntry / SAFE Agent, Message — has a control) AND `kind` (DOOR Finding/RecalledMemory /
  SAFE MemorySource — currently moot, latent), each with its re-open trigger.

Left SOUND (adversary-verified discriminating): Leg-1 mis-park/vacuous-drive detection, the retirement
superset proof, the hostile-multiline fixture.

### B satisfiability (re-derived — the mis-park pin changed the path)

The adversary's satisfiability path *populated `_SERVED_SAFE_FIELDS` including `task_id`*. **The new
mis-park pin forbids that** (task_id is a DOOR name). Re-derived path (sim, `_all_served_slots()` at HEAD):
uncontained-offender fields = `{agent_name, chunk_key, id, ids, name, ref, sender_name, session,
superseded_by, task_id}`. Of these, **only `task_id` is a manifest DOOR**; the other 9 are genuinely-safe
(opaque ids / charset-gated identities). With SAFE = those 9 (blocked_by excluded, contained) →
**Leg-1 = [], mis-park = [], Leg-2 = {task_id}**. Containing the ONE residual door (fleet-row task_id,
below) → Leg-2 = [] → **B 0-failed**. So B is satisfiable via *containment of the door + a non-door SAFE
allowlist* — the correct #345 recovery, not the forbidden allowlist shortcut.

### FINDING surfaced by the mis-park pin — a LIVE field-name collision (decision #2)

`AppContext._render_comms_fleet_row` (server.py:7055, a driven probe) serves `Agent.task_id` via
`safe_str(row.task_id[:8] + "…")`. `safe_str` is same-line-forgery-blind (an 8-char truncation can still
carry a ` · ` cell-delimiter forgery), so Leg-2 flags it uncontained. `Agent.task_id` is manifest-SAFE,
but the field-NAME `task_id` is a DOOR (InboxEntry) — so the field-name-keyed mis-park pin (as §9.7
specifies, and consistent with Ruling 3(c): a field-name SAFE entry asserts safety in EVERY site, which
`task_id` cannot honour) **forbids allowlisting it**. This is Ruling-3's documented collision going LIVE
(the adversary noted only the moot `kind`). Empirically `safe_str` neutralises newlines
(`'aa\n- FOR…'`→`'aa - FOR…'`), so this is a same-line, not newline, exposure — genuine, small.

---

## Decisions-needed (operator/lead)

1. **comms_footer §5/§7 scope fork.** §7/§9.6 name `test_comms_footer._scan` a `parse_production_trees`
   adopter to MIGRATE; §5's A-SUB writable set OMITS the file. I allowlisted it PROVISIONALLY (so the
   anti-dup pin is satisfiable at the §5 writable set) with a re-open trigger. **Recommend:** add
   `test_comms_footer.py` to the builder's writable set and remove the provisional entry (the dead-entry
   pin then forces it). Ruling needed before the A-SUB build wave.
2. **fleet-row `task_id` — contain vs model-precise keying.** To satisfy Leg-2 + mis-park without a
   forbidden field-name-SAFE entry, `_render_comms_fleet_row` must route `task_id` through
   `render_attributed` (a server.py production fix — the B builder needs server.py in scope, which the
   #345 recovery requires anyway). **Alternative:** make `_SERVED_SAFE_FIELDS` + the mis-park pin
   MODEL-PRECISE (`(model, field)` keys) so `Agent.task_id`-SAFE ≠ `InboxEntry.task_id`-DOOR — but that
   reverses Ruling 3's DRY field-name-keying decision. **Recommend:** contain it (cheap, faithful to
   §9.7 + Ruling 3; render_attributed on a truncated id is harmless). Operator rules.
3. **`_rebind_everywhere` promotion (now ≥2 reusers: F + A-SUB).** My accessor `_rebind_everywhere_fn()`
   checks `_logging_fixtures` FIRST then `test_store_seam_one_derivation`, so it is tolerant if the
   builder promotes it to shared test-support (the §9.6 promotion, gated on ≥2 reusers + a mutation
   proof). Builder judgment; recommend promoting (this cycle is the 2nd reuser).

## Notes / housekeeping

- **B-3 (recorded, not pinned):** server.py `_render_task_rows` docstring (lines 4631-4634) still calls
  `render_attributed` "defense-in-depth" and the field "NOT live-forgeable" — Ruling 2 says
  `render_attributed` is the PRIMARY required containment and the repr-escaping is FRAGILE/secondary.
  Served-English (no AST home) → builder/cold-audit checklist item.
- **Fallback disclosure (dogfood):** I used `grep`/`ast` scans over the test tree for
  rename/exhaustiveness (clone-signature census, offender allowlist) and non-symbol textual seams —
  the honest cases (a) and (b) per CLAUDE.md's grep-remains-honest list; lore was used for symbol/graph
  lookups. No lore weakness routed-around.
- **Scratch:** `/tmp/asubb-sat2` is a disposable `scratch_copy.sh` tree (NOT a git worktree). Safe to
  delete; left for lead re-verification if wanted.
- **Gates:** ruff clean on both files; `mypy` clean on both files (`Success: no issues found in 2
  source files`). `scripts/typecheck.sh` has ONE unrelated failing leg —
  `lorerunes/tests/test_roster_parser.py` (a sibling RED contract for an unbuilt `lorerunes` roster
  parser), untouched by me and pre-existing.
