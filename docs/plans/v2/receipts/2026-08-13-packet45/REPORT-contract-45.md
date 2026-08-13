# REPORT-contract-45 — packet 45 tool-allowlist CONTRACT (RED) + stubs

`brief-base v13 read` · `brief project v7 read`

## Summary block
- **state:** done — RED contract + minimal stubs committed at `b9c1f93` (branch
  `feat/surreal-unification`). Builder does GREEN. 28 pins collected: **19 RED for
  behavioral reasons**, 9 green (self-checks / default-path / RE-1 alias / `[full]`
  fixture / green-in-stub G + control).
- **deviations:**
  - Committed the work myself (spawn brief: "Commit at phase boundaries") — this
    OVERRIDES brief-base §2 "the lead commits" by precedence (spawn brief > base). ONE
    commit, not two: Phase 2 consumes imports Phase 1 declares, so a split would ship a
    ruff-red intermediate. Explicit paths, never `git add -A`.
  - `build_instructions` stub signature is `(enabled, *, identity: str | None = None)` —
    the design's stated `build_instructions(enabled)` had no way to carry Fork A's
    config-authorable identity. See decisions-needed.
- **Packages considered:** none — no external mechanism specified (contract + stubs only).
  The GREEN builder reuses in-tree seams, not new deps: `partition_tools_by_posture`
  (#291), the `_TOOL_NAME_TOKEN` regex, `_declared_instructions` (CL3 oracle).
- **Reuse ledger:** 5 new *reusable* symbols, all dispositioned (§DRY ledger). Prod:
  `_ALL_BUILTIN_TOOL_NAMES` (RE-1 promotion, single-sourced), `build_instructions`,
  `render_sample_tools_section`, `_validate_tool_allowlist` (all STUBs). Test helpers
  reuse existing seams (`_config`/`_slug`, `_TOOL_NAME_TOKEN`, `CollidingExtension`).
- **decisions-needed (for the lead / contract-adversary):**
  1. Fork A wiring: `build_instructions(enabled, *, identity=None)` + `LoreConfig.identity`
     served VERBATIM as the WHOLE first paragraph. Confirm the field holds the whole
     paragraph (incl. any `IDENTITY:` prefix), not just the descriptive tail.
  2. Boot loud-fail EXCEPTION TYPE — ruling silent; I pinned `ValueError` (unknown name
     AND empty-total). Builder raises `ValueError` or flags a different type.
  3. G (collision-guard) behavioral pin is GREEN-in-stub (see §G) — its RED requires the
     filter present. Adversary should confirm it discriminates the final build.
- **receipt pointers:** commit `b9c1f93` · RED run §"RED receipts" below · regressions
  §"Regression" (240 existing pins green) · typecheck delta §"Gates".

---

## What changed (file:symbol)

### Stubs — production seams (builder implements)
- `loremaster/loremaster/config.py`:
  - `ToolsConfig(_StrictModel)` — `enabled: list[str] = []` (mirrors `AuthConfig`). REAL
    field (tests must construct configs); the ENFORCEMENT is builder work.
  - `LoreConfig.tools: ToolsConfig | None = None` — absent ⇒ all built-ins (mirrors `auth`).
  - `LoreConfig.identity: str | None = None` — Fork A; `None` ⇒ built-in default.
- `loremaster/loremaster/server.py`:
  - `_ALL_BUILTIN_TOOL_NAMES: frozenset[str]` — **RE-1 promotion** to production as ONE
    object (the 15 built-in names), hand-declared as the DECLARED UNIVERSE (anti-drift
    guard asserts it == registered surface, so it is NOT derived from that surface).
  - `build_instructions(enabled, *, identity=None) -> str` — STUB (`NotImplementedError`).
  - `render_sample_tools_section() -> str` — STUB (`NotImplementedError`).
  - `_validate_tool_allowlist(config, extension_tool_names) -> None` — STUB (no-op seam);
    the builder wires it into `build_mcp_server` and implements the loud-fail contract.
  - `Collection` added to the `collections.abc` import.

### RE-1 rewire (single-source the universe)
- `loremaster/tests/test_mcp_server.py`: `_ALL_BUILTIN_TOOL_NAMES` was a parallel hand-list
  (`_EXPECTED_TOOLS | {3}`); it is now `_PROD_BUILTIN_TOOL_NAMES` (imported from
  `loremaster.server`) — value byte-identical (verified), so `test_the_registered_surface_
  is_exactly_the_expected_set` and every consumer (`test_text_hygiene:207`,
  `test_task_read_surface`, `test_mutating_set_derivation`) now consume the prod object
  transitively, no edit needed. `test_tool_allowlist` pins the alias is the SAME object.

### The contract — `loremaster/tests/test_tool_allowlist.py` (new, 28 pins)

---

## Pin inventory → brief items A–I

| item | pin(s) | fixtures | RED-in-stub? |
|---|---|---|---|
| **A** config/boot | `TestConfigToolsSection::{parse, absent_registers_ALL, unknown_name_fails_boot_LOUDLY, CONTROL_valid_boots, empty_total_fails_boot_LOUDLY}` | none/empty | unknown_name ✓, empty_total ✓ (parse/absent/CONTROL green) |
| **B** RE-1 | `TestUniverseIsSingleSourced::{same_object, production_universe_equals_registered_full_surface}` | full | green (refactor pins) |
| **C** never-register filter | `TestNeverRegisterFilter::registered_builtins_are_EXACTLY_the_enabled_set[full/subset/lore-dnd]` + `::empty_enabled_registers_EXACTLY_zero_builtins_reach_check` | full,subset,lore-dnd,empty | [subset],[lore-dnd],empty_reach ✓ ([full] green) |
| **D** #296 wire | `TestDisabledToolIsUncallableOnTheWire::disabled_tool_is_absent_and_uncallable` | lore-dnd | ✓ |
| **E1** anchor | `TestBuildInstructionsFullSetIsByteExact::full_set_reproduces_todays_instructions_byte_exact` | full | ✓ (NotImplementedError) |
| **E2** biconditional | `TestServedProseNamesExactlyTheEnabledTools::served_lore_tokens_equal_the_enabled_set[full/subset/lore-dnd]` + `::empty_surface_names_no_tool` | full,subset,lore-dnd,empty | [subset],[lore-dnd],empty ✓ ([full] green) |
| **E3** structural | `TestServedProseIsStructurallyCoherent::no_gutted_header_and_no_dangling_arrow[full/subset/lore-dnd/empty]` | all 4 | ✓ all (NotImplementedError) |
| **F** Fork A identity | `TestIdentityLineIsConfigAuthorable::{default_identity_is_todays_exact_paragraph, custom_identity_is_served_verbatim}` | full/lore-dnd | ✓ |
| **G** collision universe | `TestCollisionGuardChecksTheDeclaredUniverse::{disabled_builtin_name_not_claimable_by_an_extension, collision_guard_docstring_names_the_declared_universe}` | — | docstring ✓; behavioral GREEN-in-stub (see §G) |
| **H** 2B sample | `TestSampleToolsSectionIsGeneratedFromTheUniverse::sample_section_names_exactly_the_universe` | — | ✓ (NotImplementedError) |
| **I** partition | `TestPartitionReadsOnlyRegisteredTools::partition_of_a_reduced_surface_excludes_disabled_tools` | lore-dnd | ✓ |
| **E4** | (no pin — documented) full-set substantial/rollup pins NOT parametrised over reduced sets (a reduced surface is legitimately shorter → padding = over-claim). | | |

### Fixtures (`{full, subset, lore-dnd, empty}`)
- `_FULL` = the 15-tool universe. `_SUBSET` = {search, read, get_symbol, remember, recall}
  (multi-tool, distinct from lore-dnd, exercises a compound LADDER step + MEMORY clause).
  `_LORE_DND_ENABLED` = rulings §4 = {search, read, index, diff, findings}. `_EMPTY` = ∅.
- `test_fixture_sets_are_coherent_with_the_declared_universe` self-checks: lore-dnd
  enabled ⊍ disabled == universe, disjoint; every non-empty fixture keeps search+read
  (so the EMPTY fixture is the ONLY one disabling them — the L2-1 reach argument).

### Expected-RED node ids + reddening mutation (load-bearing pins)
- `unknown_name_fails_boot_LOUDLY` — RED: `DID NOT RAISE ValueError` (no boot validation).
  MUTATION (finished build): drop the universe-membership check.
- `empty_total_fails_boot_LOUDLY` — RED: no raise. MUTATION: skip the total-empty guard.
  Positive control: `CONTROL_a_valid_allowlist_boots_without_raising` (one enabled tool boots).
- `registered_builtins_are_EXACTLY_the_enabled_set[subset|lore-dnd]` — RED: filter ignored,
  disabled tools leak in. MUTATION: a `@mcp.tool` site left un-gated.
- `empty_enabled_registers_EXACTLY_zero_builtins_reach_check` — RED: 15 register. MUTATION:
  ANY one of 15 sites un-gated (this is the reach = checked-variable, INSTRUMENT 0).
- `disabled_tool_is_absent_and_uncallable` — RED: `lore_map` present in `list_tools()`.
  MUTATION: filter `list_tools()` POST-construction while leaving the wire handler live
  (the #296 wrong-instance fix — this pin kills it; matches on `"Unknown tool"` not just
  the `ToolError` type, because a registered tool errors as `ToolError` too).
- `full_set_reproduces_todays_instructions_byte_exact` — RED: `NotImplementedError`.
  Oracle = `_declared_instructions(cap)` (CL3's independent transcription). MUTATION: any
  section-builder drift (lost wrap-point space, reordered clause).
- `served_lore_tokens_equal_the_enabled_set[subset|lore-dnd]` — RED: served surface is
  full `_INSTRUCTIONS` + all 15 descriptions (a surviving tool's own description names a
  disabled neighbour). MUTATION: leave a disabled name in a description (⊆), or drop an
  enabled tool's clause (⊇).
- `no_gutted_header_and_no_dangling_arrow[*]` — RED: `NotImplementedError`. MUTATION:
  strip LADDER steps without re-joining (`-> ->` / trailing `->`) or drop MEMORY's last
  clause keeping its header.
- `custom_identity_is_served_verbatim` — RED: `build_mcp_server` ignores `config.identity`.
  MUTATION: ignore/hardcode the identity.
- `partition_of_a_reduced_surface_excludes_disabled_tools` — RED: all 15 register, so the
  (correct) partition over the registered set includes disabled tools. MUTATION: un-gated site.

---

## §G — the one pin that is GREEN-in-stub (read this)
`disabled_builtin_name_not_claimable_by_an_extension` disables `lore_search` and registers
`CollidingExtension` (claims `lore_search`), expecting `build_mcp_server` to raise. In the
STUB the filter is unbuilt, so `lore_search` STILL registers and the *existing*
registered-set guard fires → the pin passes for the WRONG reason. Its TRUE discrimination:
a build where the filter IS applied but the guard still checks only the REGISTERED set —
then `lore_search` is unregistered, the guard misses, the extension shadows the name, no
raise. The docstring pin (`collision_guard_docstring_names_the_declared_universe`) gives the
immediate RED. Adversary: mutation-prove G by (filter on) + (guard on `get_tool` only) → G reds.

## §DRY ledger (new reusable symbols)
| new symbol | lore query | returned | disposition |
|---|---|---|---|
| `_ALL_BUILTIN_TOOL_NAMES` (prod) | grep prod for existing universe const | none in prod; only test-side | HAND-ROLLED as the RE-1 promotion; test-side now ALIASES it (single source) |
| `build_instructions` | `grep build_instructions server.py config.py` | none | HAND-ROLLED stub (builder GREEN; reuses `_TOOL_NAME_TOKEN`, `_declared_instructions`) |
| `render_sample_tools_section` | grep | none | HAND-ROLLED stub |
| `_validate_tool_allowlist` | grep `_validate` in server.py | `_validate_tier/_validate_comms_*` (unrelated) | HAND-ROLLED stub (no existing allowlist validator) |
| `ToolsConfig` | mirrors `AuthConfig(_StrictModel)` | `AuthConfig` idiom | REUSED the `_StrictModel` + optional-section idiom |
| test `_TOOL_NAME_TOKEN` | reused `TestNoDeadToolNamesInAgentFacingText._TOOL_NAME_TOKEN` | the every-token regex | **REUSED** (DRY) — no re-rolled tokenizer |
| test `_declared_instructions`/`_msg` | reused from `test_comms_tool` | CL3 oracle | **REUSED** as E1's byte-exact oracle |
| test `_config`/`_slug`, `CollidingExtension`/`BUILTIN_COLLISION_NAME` | reused from harness | config builder / collision harness | **REUSED** |

## Builder wiring (I did NOT pre-wire these — they are GREEN work; design doc §2 has shapes)
1. `_register_tools`: define a `_gated_tool(name, description, annotations)` indirection
   (NOT `_tool` — clashes with the extension wrapper's inner `_tool` at `_extension_tool_wrapper`)
   that returns `mcp.tool(...)` iff `name ∈ enabled`, else a no-register no-op; convert all
   15 `@mcp.tool(...)` sites. `enabled = _ALL_BUILTIN_TOOL_NAMES` when `config.tools is None`,
   else `frozenset(config.tools.enabled)`.
2. `build_mcp_server`: `instructions=build_instructions(enabled, identity=config.identity)`;
   keep the `_MESSAGE_BODY_MAX_CHARS` interpolation inside the comms section builder; and set
   `_INSTRUCTIONS = build_instructions(_ALL_BUILTIN_TOOL_NAMES)` (or equivalent) so CL3 stays
   green. Call `_validate_tool_allowlist(config, extension_tool_names)` before/at build.
3. `_register_extension_tools`: guard against `_ALL_BUILTIN_TOOL_NAMES` (∪ registered), and
   UPDATE its docstring to teach that a disabled built-in's name is reserved.
4. `render_sample_tools_section`: derive a commented `tools:`/`enabled:` sample from the universe.

## RED receipts (at `b9c1f93`)
```
19 failed, 9 passed in 2.40s   # uv run pytest tests/test_tool_allowlist.py -p no:randomly
```
Spot-verified RED reasons: E1 → `NotImplementedError` (build_instructions stub); D →
`assert 'lore_map' not in {..., 'lore_map', ...}` (filter unbuilt); unknown_name →
`Failed: DID NOT RAISE ValueError`. Full failing list in the run tail. call_tool confirmed
to fail FAST (no hang; `Unknown tool: lore_map` when unregistered vs `Error executing tool
lore_map` when registered — the `match` discriminates).

## Regression (RE-1 alias + config fields do NOT break existing pins)
- `TestToolRegistration` + `TestNoDeadToolNamesInAgentFacingText` + `TestServerInstructions`
  + `test_mutating_set_derivation` + `test_text_hygiene` → **38 passed**.
- CL3 anchor `TestTheInstructionsBlockTeachesTheMessageSurface` + `test_config` → **102 passed**.
- collision guard (`test_extension` seam-3, ×2) + `test_task_read_surface` → **100 passed, 1 skip**.
- `_INSTRUCTIONS` UNTOUCHED, so CL3/CL1 stay byte-exact green (the ADDITIVE reframe holds).

## Gates
- `ruff check` — clean on all 4 changed files.
- `scripts/typecheck.sh` — exit 1, but a **GREEN DELTA**: every mypy error is in packet-39
  auth/posture/roster WIP (`test_auth*`, `test_allowlist_roster`, `test_posture`,
  `test_roster_parser`, `test_permission_resolver_seam`, `test_hosted_readonly_posture`,
  `test_google_token_verifier`, `test_email_normalisation`, `_auth_fixtures`) = the #333
  RE-2 baseline. **ZERO errors in any of my 4 changed files** (derived, not assumed).

## Escalations / forks noticed
- **Commit authority** (deviation, resolved by precedence) — see summary.
- **Fork A signature + verbatim-identity semantics** (decision 1) — `build_instructions`
  gained an `identity` keyword; `config.identity` is served as the WHOLE first paragraph.
- **Boot loud-fail exception type** (decision 2) — pinned `ValueError`.
- **G behavioral pin green-in-stub** (decision 3 / §G).
- **`ToolsConfig.enabled` default `[]`** — writing `tools: {}` disables all built-ins
  (→ empty-total boot loud-fail if no extensions). Consistent with deny-by-default within
  the section; noting the footgun.
- **Empty-reach vs Fork B** — the L2-1 empty coverage check drives `_register_tools`
  directly (bypassing the empty-total boot loud-fail) so the filter's 15-site coverage is
  exercised at `enabled=∅`; Fork B's loud-fail is a separate pin via `build_mcp_server`.
