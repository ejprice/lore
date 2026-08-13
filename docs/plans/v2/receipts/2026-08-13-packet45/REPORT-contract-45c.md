# REPORT-contract-45c — packet 45 CONTRACT revision: MP-1 (derived cross-ref coverage)

`brief-base v13 read` · `brief project v7 read`

## Summary block (read first)
- **state:** done.
- **task:** add the ONE adversary-found missing pin (MP-1, adversary-45 attack 2) + RED-confirm +
  commit. Writer of TESTS + (already-present) stub only — no implementation logic added.
- **deviation (commit):** spawn brief instructs "Commit (explicit path, NOT `git add -A`)", which
  OVERRIDES brief-base §2's "the lead commits" (spawn brief > base by precedence). I committed ONLY
  `loremaster/tests/test_tool_allowlist.py` by explicit path. The report itself is NOT committed
  (root `REPORT-*.md` is lead-archived per repo law).
- **MP-1 added:** `TestEveryDescriptionCrossRefDropsItsDisabledReferent::test_every_crossref_drops_its_disabled_referent`
  — DERIVED cross-ref coverage pin. Enumerates the actual A→B description cross-references from the
  built full server and, per referent B, builds witness `_FULL−{B}` asserting B absent from each
  referrer's served description AND the whole surface. Coverage is a CHECKED VARIABLE over the graph.
- **OPTIONAL wiring pin added (my judgment — clean, non-duplicative):**
  `TestInstructionsInterpSiteWiresBuildInstructions::test_reduced_surface_instructions_are_build_instructions_of_enabled`
  — pins `mcp.instructions == build_instructions(registered, identity=config.identity)` on the
  lore-dnd reduced surface (closes adversary-45 attack-3 FLAG #2: interp-site wiring only transitively
  caught by E2).
- **Derived cross-ref count = 24** (measured, §RED-confirm) — EXACT match to adversary-45's
  independent `_adv_xref.py` enumeration. Anti-vacuity floor `>= 20` has margin.
- **Packages considered:** none — no external mechanism specified. Pins use stdlib `re` (via the
  reused `_TOOL_NAME_TOKEN`) + in-tree helpers only (I concur with the adversary's package survey §P-PKG).
- **Reuse ledger:** 2 new test symbols, both dispositioned (§DRY ledger) — `_tool_description_texts`
  (HAND-ROLLED, extracted-shared: consolidates the inline pattern so E2 and MP-1 scan ONE text set),
  `_builtin_crossref_map` (HAND-ROLLED: no in-tree cross-ref enumerator exists).
- **Graded:** `2e84d3a0` · HEAD-at-report: `2e84d3a0` · SAME. (Adversary graded `b9c1f93`; the only
  intervening commit `2e84d3a` is `docs(45)` — contract + stubs are byte-identical to `b9c1f93`, so my
  RED receipts equal what they'd be at the graded sha. My commit lands on top of `2e84d3a0`.)
- **decisions-needed:** none. The design-doc §2.0/§2.4 corrections are the LEAD's (already committed at
  `2e84d3a`); the §2.0 CL3-rewire is a BUILDER concern (lead carries it). Not mine per brief.
- **receipt pointers:** MP-1 shape §MP-1; RED receipts §RED-confirm; regression §Regression; DRY §DRY
  ledger. Instrument is IN-TREE (`_builtin_crossref_map` in the test file — a committed deliverable, not
  scratch).

## MP-1 — the derived cross-reference coverage pin
**File:** `loremaster/tests/test_tool_allowlist.py`
**Class/test:** `TestEveryDescriptionCrossRefDropsItsDisabledReferent::test_every_crossref_drops_its_disabled_referent`
**New helper it drives:** `_builtin_crossref_map(mcp)` — for each registered built-in A, the set of
OTHER built-in names named in A's top-level + per-parameter descriptions (A→B). Derived from the built
server exactly as adversary-45's scratch `_adv_xref.py` did; reuses `_TOOL_NAME_TOKEN`
(`re.compile(r"\blore_[a-z_]+\b")`, verified identical to the adversary's regex) and the shared
`_tool_description_texts` extractor.

**Mechanism (per adversary MISSING PIN spec):**
1. Build the full server (`_build(tmp_path, enabled=_FULL)`), enumerate cross-refs → `pairs` (24).
2. **Anti-vacuity:** `assert len(pairs) >= 20` (INSTRUMENT-0 / #291 — a build returning zero cross-refs
   is a coverage collapse, caught, not a silently-passing ∀-over-nothing). Floor, not the exact 24, so a
   legitimate reduction below 20 is a deliberate re-open, not a false red.
3. Group `pairs` by referent B; for each distinct B build witness `enabled = frozenset(_FULL) − {B}`
   (guarantees every referrer A≠B stays enabled, exactly B disabled — one reduced build per referent).
4. For each referrer A of B: assert B's token ABSENT from A's served description
   (`_builtin_crossref_map(witness)[A]`); and assert B ABSENT from the whole served surface
   (`_served_lore_tokens(witness)`). Violations accumulate into `leaks`; one final `assert not leaks`.

**Why coverage is now a CHECKED VARIABLE (the INSTRUMENT-0 fix):** the reach set is the DERIVED
description graph, not the (referrer,referent) pairs the two E2 fixtures happen to split. A 16th tool or
a new cross-reference is enumerated automatically; a single hardcoded cross-reference reddens. This is
the exact seventh-defeat class the adversary's P1c flagged E2 for (reach = hidden constant).

## RED-confirm (against the stub at HEAD 2e84d3a0)
Expected-RED node ids declared from `--collect-only` BEFORE running (both are NEW):
- `TestEveryDescriptionCrossRefDropsItsDisabledReferent::test_every_crossref_drops_its_disabled_referent`
- `TestInstructionsInterpSiteWiresBuildInstructions::test_reduced_surface_instructions_are_build_instructions_of_enabled`

**MP-1 RED for the RIGHT reason** — the LEAK assert fired (NOT the anti-vacuity floor, NOT a
`build_instructions` NotImplementedError; MP-1 never calls `build_instructions`). It is a live
discriminating pin against the stub's REAL served surface (stub serves full `_INSTRUCTIONS` + all 15
descriptions because the allowlist is ignored). Assertion tail:
```
AssertionError: disabled referents leaked into served text on reduced surfaces (36 leak(s)):
  ...
  desc: lore_search→lore_read — lore_search's served description still names disabled lore_read
  ...
```
- 36 leaks = **24 `desc:` cross-ref pairs + 12 `surface:` referents**.
- The 24 desc pairs EXACTLY reproduce adversary-45's `_adv_xref.py` enumeration (all 6 "exercised" + 18
  "unexercised" pairs). Two independent enumerations agree at 24 → the derived reach is corroborated.
- The adversary's marquee UNEXERCISED leak `lore_search→lore_read` (invisible to all four E2 fixtures)
  is caught. So is every other E2-unexercised cross-ref (e.g. `lore_map→{diff,impact,search}`,
  `lore_tasks→{claim_task,comms}`, `lore_recall↔lore_remember`).

**Wiring pin RED for the right reason** — `build_instructions` raises `NotImplementedError` (derivation
unbuilt), so the RHS errors before comparison. In a finished build it pins the interp-site wiring
byte-exact. It CANNOT be red-on-correct-build: LHS `mcp.instructions` is set by the server to
`build_instructions(enabled, identity=config.identity)`; RHS reconstructs `build_instructions(registered,
identity=config.identity)`; `registered == enabled` (pinned by C) and `build_instructions` is
order-insensitive (forced by E1's byte-exact-over-a-frozenset), so LHS ≡ RHS on the true wiring.

## Regression — full file, no existing pin flipped verdict
`uv run pytest tests/test_tool_allowlist.py -p no:randomly -q` → **21 failed, 9 passed** (30 collected).
- Baseline was 28 tests (19 stub-RED + 9 green). My 2 new pins are both RED → 21 RED + 9 green.
- **No existing pin changed verdict.** The 9 green are exactly the parse/default/control/single-source
  pins that were green in the stub (incl. E2`[full]` and the collision-guard pin that is green-in-stub
  for a different reason per its own docstring).
- **E2 refactor is behavior-preserving.** I extracted `_tool_description_texts` and routed the existing
  `_served_lore_tokens` through it (DRY). Verified E2 still `[full]` green / `[subset]`+`[lore-dnd]` RED
  with the ORIGINAL `AssertionError: ... Extra items in the left set` (a disabled token present) — NOT a
  new exception from the refactor.
- `uv run ruff check loremaster/tests/test_tool_allowlist.py` → `All checks passed!`

## DRY ledger (§6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_tool_description_texts(tool)` | `lore_search "helper extracting a tool's description and per-parameter descriptions served text"` | only the just-added symbol itself; the extraction pattern previously lived INLINE inside `_served_lore_tokens` (no shared callable) | **HAND-ROLLED (extracted-shared)** — consolidates the inline pattern so `_served_lore_tokens` (E2) and `_builtin_crossref_map` (MP-1) scan ONE text set; a change to WHICH text is scanned moves both by construction |
| `_builtin_crossref_map(mcp)` | same search + known that `test_mcp_server.TestNoDeadToolNamesInAgentFacingText` scans served text but builds no per-tool cross-ref map; adversary's `_adv_xref.py` was scratch-only (gone) | no in-tree cross-ref enumerator | **HAND-ROLLED** — reuses `_TOOL_NAME_TOKEN` + `_tool_description_texts` + `_ALL_BUILTIN_TOOL_NAMES` |

Reused without new symbols: `_TOOL_NAME_TOKEN`, `_ALL_BUILTIN_TOOL_NAMES`, `_build`, `_make_config`,
`_registered_builtins`, `_served_lore_tokens`, `build_instructions`/`build_mcp_server`/`LoreServer`.

## Flags / surfaced (per scope law — not blockers)
- The adversary's design-doc corrections (§2.4 exhaustiveness overclaim struck/scoped; §2.0 CL3 reads
  the module constant, not `mcp.instructions`) are the LEAD's — already committed at `2e84d3a`. MP-1 is
  the instrument that makes the (now-scoped) exhaustiveness claim TRUE rather than asserted.
- MP-1 mitigates the FUTURE-reduced-deploy gap (packet 54+ instance allowlists) the adversary named; the
  driving lore-dnd deploy was already covered by E2`[lore-dnd]`.
- The §2.0 CL3-rewire (`_INSTRUCTIONS = build_instructions(ALL)`) remains a BUILDER concern; my wiring
  pin does not touch `_DECLARED_NON_COMMS_PARAGRAPHS` and does not re-litigate the 5 caught attacks.
