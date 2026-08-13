# REPORT-builder-45 — packet 45 tool-allowlist BUILD (GREEN)

`brief-base v13 read` · `brief project v7 read`

## Summary block
- **state:** done. All 30 contract pins GREEN; coupled existing pins GREEN; ruff clean;
  typecheck green-delta (zero in changed files). Two phase commits + 4 mutation proofs.
- **deviations:**
  - Committed the work myself at each phase boundary (spawn brief: "COMMIT at each phase
    boundary"; OVERRIDES brief-base §2 "the lead commits" by precedence — spawn brief > base).
    Two commits, explicit paths, never `git add -A`. Mutation proofs mutated the REAL tree
    with a `cp -a` content backup and restored byte-exact (md5-verified); NO git state mutated.
  - Param descriptions that drop a cross-reference live inside `Annotated[...]` metadata,
    which FastMCP RE-EVALUATES via `inspect.signature(func, eval_str=True)` in the MODULE
    globals (this module has `from __future__ import annotations`) — so a closure-local
    `enabled` is invisible there (`NameError`). Not anticipated by the brief; I published the
    in-progress enabled set on a `ContextVar` (`_REGISTERING_ENABLED`) the param builders read.
    See §"The Annotated-metadata constraint".
- **Packages considered:** registration filter → FastMCP's own `mcp.tool` (kept; the filter
  is a no-register decorator, no package does per-deploy tool gating for us). Ambient
  per-registration state → stdlib `contextvars.ContextVar` (`replace` a `global`/`threading.local`
  hand-roll; READ the contextvars docs + the observed `inspect.signature` eval path — ContextVar
  is the async-correct primitive: each asyncio task gets its own copy, so concurrent builds never
  tear). Boot validation → pydantic already at the boundary (`ToolsConfig`); the universe/empty
  checks are a plain set-difference (`bespoke`, no package fits). Prose assembly → stdlib `str`.
- **Reuse ledger:** 4 new reusable symbols, all dispositioned (§DRY ledger). Others are
  packet-45-specific served-prose builders or contract-authored stubs I filled.
- **Graded:** n/a (this is a build, not a verdict on another artifact).
- **decisions-needed:** none blocking. Two ruled bounds re-surfaced for visibility (§Flags):
  (1) IDENTITY over-claim on a reduced surface (Fork A, ruled → pkt 54 authors `config.identity`);
  (2) single-disable WITNESS-surface grammar quirks (test-only, never on a real deploy).
- **receipt pointers:** phase commits `7358ff4` (A) + `92286c6` (B); 30/30 §"Gate receipts";
  mutation proofs §"Mutation proofs"; typecheck delta §"Gate receipts"; lore-dnd surface
  §"Reduced-surface coherence".

---

## What changed (file:symbol) — `loremaster/loremaster/server.py` only

### Phase A — mechanism (commit `7358ff4`)
- `_register_tools`: computes `enabled` (`_ALL_BUILTIN_TOOL_NAMES` when `config.tools is None`,
  else `frozenset(config.tools.enabled)`), publishes it on `_REGISTERING_ENABLED`, defines the
  inner `_gated_tool(name, description, annotations)` decorator (registers via `mcp.tool` iff
  `name ∈ enabled`, else a no-op `_skip`). ALL 15 `@mcp.tool(...)` sites converted to `@_gated_tool`.
- `_validate_tool_allowlist(config, extension_tool_names)`: unknown enabled name → `ValueError`
  naming the unknown set AND the known universe; empty TOTAL surface
  `(built-ins ∩ enabled) ∪ extensions` → `ValueError` (Fork B). Wired into `build_mcp_server`
  BEFORE registration (`extension_tool_names` collected over the composition context).
- `_register_extension_tools` collision guard: now `spec.name in _ALL_BUILTIN_TOOL_NAMES or
  mcp._tool_manager.get_tool(spec.name) is not None` (a DISABLED built-in's name stays reserved,
  L2-4); docstring rewritten to teach the declared-universe reservation (prose-consistency pin G).
- `render_sample_tools_section()`: derives a commented `tools:`/`enabled:` sample from
  `sorted(_ALL_BUILTIN_TOOL_NAMES)` (tokens == universe exactly, H).

### Phase B — served prose (commit `92286c6`)
- `build_instructions(enabled, *, identity=None)`: thin assembler over 9 module-level
  `_instr_*` section builders (`_instr_ladder/_citations/_freshness/_honest_failure/_memory/
  _comms/_pending_traffic/_tool_loading`) + the Fork-A identity line. `build_instructions(ALL)`
  reproduces the historical `_INSTRUCTIONS` BYTE-EXACT (E1 + CL3 oracle). Helpers: `_enabled_phrase`
  (compound tool-alternative phrase, drops disabled alternatives), `_DEFAULT_IDENTITY`.
- §8 rewire: module-scope `_INSTRUCTIONS = build_instructions(_ALL_BUILTIN_TOOL_NAMES)` (keeps CL3
  a live derivation anchor); interp site serves `instructions=build_instructions(enabled_tool_names,
  identity=config.identity)`.
- DESCRIPTION SURGERY — all 24 cross-references (enumerated live from the built full server, matches
  adversary-45's count) restructured into guarded segments: 14 top-level via `_guarded_description`,
  the 6 cross-ref params via `_guarded_description(_REGISTERING_ENABLED.get(), …)`, the compound
  `lore_read` description via bespoke `_read_description`, and the shared `agent=` identity clause via
  `_comms_identity_agent_description` (replacing the deleted `_COMMS_IDENTITY_AGENT_DESCRIPTION`
  constant; its one docstring `:data:` ref updated to `:func:`). Byte-exact on the FULL universe (so
  every description substring pin stays green), dropping a disabled neighbour's name on a reduced
  surface (E2 forward ⊆ + MP-1).

## The Annotated-metadata constraint (why `_REGISTERING_ENABLED` is a ContextVar)
Top-level descriptions are passed to `@_gated_tool(description=…)` — a plain value, safe with the
closure-local `enabled`. PARAM descriptions live inside `Annotated[str|None, Field(description=…)]`;
FastMCP's `func_metadata` calls `inspect.signature(func, eval_str=True)`, which (under
`from __future__ import annotations`) re-parses and re-executes that `Field(...)` in `func.__globals__`
— the closure local `enabled` is not there → `NameError`. So the enabled set of the in-progress
registration is published on `_REGISTERING_ENABLED` (a module-global `ContextVar`), set synchronously
at the top of `_register_tools` and read via `.get()` inside the param builders. Registration is
synchronous (no await between set and the decorator pass), and each asyncio task carries its own
ContextVar copy, so concurrent builds cannot tear. Original static f-string params (referencing
module globals like `_DEFAULT_SEARCH_K`) were always re-evaluated this way too — they just referenced
globals, which is why they worked; `enabled` is the only local that ever reached that metadata.

## Gate receipts
- **Contract:** `test_tool_allowlist.py` — **30 passed** (`-p no:randomly`).
- **Final scoped set (`-n auto`):** `test_tool_allowlist test_mcp_server test_comms_tool
  test_mutating_set_derivation test_text_hygiene` → **1646 passed in 105.55s**. Includes CL3/CL1
  (`test_comms_tool.py::TestTheInstructionsBlockTeachesTheMessageSurface`), the every-token &
  instructions pins (`test_mcp_server::{TestServerInstructions,TestNoDeadToolNamesInAgentFacingText,
  TestToolRegistration,TestToolDescriptions,TestToolInputFieldDescriptions}`), and the #291
  partition (`test_mutating_set_derivation`).
- **Also green (coupled, run separately):** `test_workspace_status` (lore_index desc "branch"),
  `test_comms_footer` (CL1), `test_task_read_surface`, `test_extension` collision seam.
- **ruff:** `uv run ruff check .` → **All checks passed!** (fixed PLR0915 by extracting section
  builders to module level; PLW0603 by using a ContextVar instead of `global`).
- **typecheck (`scripts/typecheck.sh`):** exit 1 = the #333 RE-2 baseline — **102 errors across 8
  files, ALL packet-39 auth/posture/roster WIP** (`test_auth*`, `test_allowlist_roster`,
  `test_permission_resolver_seam`, `test_hosted_readonly_posture`, `test_google_token_verifier`,
  `_auth_fixtures`). **ZERO errors in `loremaster/loremaster/server.py` or `config.py`** (derived by
  grepping the runner output for my files — empty). GREEN DELTA: my changes add no mypy errors.

## Mutation proofs (expected-RED node ids declared from `--collect-only` BEFORE each; REAL tree,
`cp -a` backup, byte-exact restore verified by md5 `d86cb869…`)
1. **Un-gate the `lore_map` `@_gated_tool` site** → `@mcp.tool` ⇒ `TestNeverRegisterFilter::
   test_empty_enabled_registers_EXACTLY_zero_builtins_reach_check` + `…test_registered_builtins_
   are_EXACTLY_the_enabled_set[subset]` + `[lore-dnd]` RED; `[full]` GREEN (map enabled there). ✓
2. **Leak `lore_get_symbol` into `lore_search`'s description** (guard `None`) ⇒
   `TestServedProseNamesExactlyTheEnabledTools::test_served_lore_tokens_equal_the_enabled_set[lore-dnd]`
   + `TestEveryDescriptionCrossRefDropsItsDisabledReferent::test_every_crossref_drops_its_disabled_
   referent` (MP-1) RED; `[full]`+`[subset]` GREEN (get_symbol enabled there). ✓ — MP-1 catches
   exactly the E2-unexercised leak the adversary named.
3. **Drop a wrap-point space** in `_instr_tool_loading` (`lore's ` → `lore's`) ⇒
   `TestBuildInstructionsFullSetIsByteExact::test_full_set_reproduces_todays_instructions_byte_exact`
   (E1) + `test_comms_tool.py::…::test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs`
   (CL3) RED. ✓
4. **Guard collision on the REGISTERED set only** (drop the `_ALL_BUILTIN_TOOL_NAMES` check) ⇒
   `TestCollisionGuardChecksTheDeclaredUniverse::test_disabled_builtin_name_not_claimable_by_an_
   extension` (G) RED. ✓
After all restores: `test_tool_allowlist.py` → 30 passed.

## Reduced-surface coherence (lore-dnd = {search, read, index, diff, findings})
The served surface is clean and coherent — LADDER collapses to exactly the design's worked example:
`LADDER: lore_search (locate) -> lore_read (exact def/span) -> write.`; FRESHNESS drops the
Impact/dead_code clause; HONEST FAILURE drops the HEURISTIC clause; MEMORY collapses to
`MEMORY: lore_findings (kind=friction) files gaps.`; COMMS + PENDING TRAFFIC omitted; `lore_search`
desc drops its lore_get_symbol ref (keeps lore_read); `lore_findings.agent` param drops its lore_comms
clause. No gutted headers, no dangling arrows, no disabled tool named anywhere.

## §DRY ledger (new reusable symbols)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_guarded_description` | `lore_search "helper that assembles a string from conditional segments dropping disabled parts"` | only this new symbol; no pre-existing guarded-prose assembler (`_sanitise_line` is for untrusted STORED text, not static prose) | HAND-ROLLED (no existing equivalent) |
| `_enabled_phrase` | same search + `grep _enabled_phrase` | none | HAND-ROLLED (compound tool-alternative phrase; the byte-exact analogue of the LADDER/MEMORY compounds) |
| `_comms_identity_agent_description` | replaced deleted `_COMMS_IDENTITY_AGENT_DESCRIPTION` constant; `grep` all tests → 0 refs | the old constant, used by 3 tools | REUSED-as-shared-function (one home, guarded; proved by MUTATION — mutating its lore_comms guard drops the clause across all 3 tools' agent params) |
| `_REGISTERING_ENABLED` | `contextvars` docs read (§constraint) | ContextVar | HAND-ROLLED (stdlib primitive; the only async-correct home for the re-eval-visible enabled set) |
| `partition_tools_by_posture` (I reused, did not touch) | `lore_impact partition_tools_by_posture` (not re-run — design §6 named it) | the #291 single source | REUSED (packet 45 only narrows its INPUT; pin I confirms disabled tools contribute no annotation) |

Section builders `_instr_*`, `_read_description`, `_DEFAULT_IDENTITY`, `_gated_tool` are
packet-45-specific served-prose / registration mechanics (not general-purpose reuse); `build_instructions`,
`render_sample_tools_section`, `_validate_tool_allowlist`, `ToolsConfig`, `LoreConfig.{tools,identity}`,
`_ALL_BUILTIN_TOOL_NAMES` (prod) are contract-authored stubs/fields I filled, not new inventions.

## Flags / things noticed (scope law — surfaced, not decided)
- **IDENTITY over-claim on a reduced surface (ruled bound, not a defect).** On lore-dnd the default
  IDENTITY still reads "code+docs+graph RAG, durable memory, and fleet ledgers" — an over-claim for a
  search-only instance, catchable by NO `lore_`-token pin (the P8d natural-language class). This is
  Fork A, RULED/accepted: default = today's exact string (so it does not AUTO-generate an over-claim
  and CL3 stays green); the operator authors the true `config.identity` at packet 54 (re-open trigger:
  the first reduced deploy that ships a real instance identity). Pin F pins the mechanism (default =
  today's paragraph; custom served verbatim). No action for packet 45.
- **Single-disable WITNESS-surface grammar quirks (test-only).** For descriptions with a mid-sentence
  cross-ref to a tool NOT on lore-dnd (e.g. `lore_map`'s "— before lore_search or lore_impact —"), a
  `_FULL − {one tool}` witness can leave a mildly ungrammatical connector (e.g. "— or lore_impact —").
  These are E2/MP-1-CORRECT (no disabled token named) and appear only on `_FULL − {single}` witness
  configs that MP-1 constructs — NEVER on lore-dnd or any planned real deploy. I prioritised clean
  grammar on the lore-dnd-served tools (search/read/index/findings) and byte-exact-on-full everywhere.
  Noting it so a future reduced deploy that serves such a tool knows to revisit that description.
- **`ToolsConfig.enabled` default `[]` footgun** (contract author already noted): writing `tools: {}`
  (present but empty) disables ALL built-ins → empty-total boot loud-fail unless extensions exist.
  Consistent with deny-by-default within the section; the loud-fail is the intended guard.
- **The design's §2.4 over-claim is now CLOSED by MP-1** (green): cross-ref coverage is a checked
  variable over the DERIVED cross-ref graph (mutation proof 2 confirms it discriminates the
  E2-unexercised `lore_search→lore_read`-class leak). No residual.

## Deploy / #296 note
Packet 45 touches NO store/DDL. The #296 receipt (a disabled tool is absent from `list_tools()` AND
uncallable via the SDK dispatch — "Unknown tool") is pin `TestDisabledToolIsUncallableOnTheWire`
(green); never-registration makes it immune to the wire-vs-instance split by construction. No deploy
performed by this build (per design §1 note (h), the dogfood recreate/#296-demonstration is a separate
step — flagged for the lead).
