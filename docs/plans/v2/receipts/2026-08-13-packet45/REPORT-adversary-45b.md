# REPORT-adversary-45 — packet 45 tool-allowlist CONTRACT adversary

`brief-base v13 read` · `brief project v7 read`

## Summary block (read first)
- **state:** done.
- **deviation (report name):** spawn brief specified `REPORT-adversary-45.md` (spawn brief > base by
  precedence), but my exact agent name is `adversary-45b`, so the generic idle-gate expects
  `REPORT-adversary-45b.md`. CANONICAL report = `REPORT-adversary-45.md` (this file; my comms signal
  points here). `REPORT-adversary-45b.md` is an IDENTICAL mirror so name-keyed lookups resolve — the
  lead may archive/delete either duplicate.
- **VERDICT: CONTRACT INSUFFICIENT** — 1 concrete missing pin (MP-1). 5 of 6 probed pins are
  individually satisfiable + discriminating; attack 2 found a real hole.
- **P1 headline — did any wrong build survive the contract? YES, ONE:** a build that leaves any of
  **18 (of 24) description cross-references** hardcoded is byte-identical to healthy across ALL four
  E2 fixtures (proved: `lore_search→lore_read` leak GREEN everywhere; positive control
  `lore_search→lore_get_symbol` reds `[lore-dnd]`). The E2 biconditional does NOT prove cross-ref
  exhaustiveness (design §2.4's claim is false). Attacks 1/3/4/5/6 + P2: wrong builds all CAUGHT.
- **MISSING PIN (MP-1):** a DERIVED cross-ref coverage pin — enumerate the actual description
  cross-refs, and for each A→B build the witness config `{A enabled, B disabled}` asserting B absent.
  Catches a builder leaving any of the 18 unexercised cross-refs hardcoded (a Trust Leg-1 over-claim).
- **Graded:** `b9c1f93` · HEAD-at-report: `b9c1f93` · SAME (contract + stubs at HEAD).
- **P1b quantifier table:** present (§P1b) — every invariant classified; only E2's ⊆ leg is a
  guarded-with-incomplete-guard row. **P1c reach table:** present (§P1c) — only E2 is reach=hidden-const.
- **Packages considered:** none — no external mechanism (I built my own survey table §P-PKG and
  CONCUR with the author's "none"; every mechanism is stdlib / pydantic-reuse / in-tree-reuse / bespoke).
- **Reuse ledger:** none — I author no production/test symbols; scratch probes only.
- **decisions-needed:** route MP-1 back to CONTRACT; strike/scope design §2.4 exhaustiveness claim;
  correct design §2.0 (CL3 reads the module constant, not `mcp.instructions`).
- **receipt pointers:** attacks §Attack 1–6; missing pin §MISSING PINS; tables §P1b/§P1c/§P-PKG;
  instruments §Appendix. Scratch `/tmp/adv45-scratch` (provenance: `loremaster ->
  /tmp/adv45-scratch/loremaster/loremaster/__init__.py`).

## Method
- ONE scratch copy via `scripts/scratch_copy.sh /tmp/adv45-scratch --force`; provenance asserted
  (`loremaster.__file__` inside scratch root — #140). No worktrees. Tests run in scratch:
  `cd /tmp/adv45-scratch/loremaster && uv run pytest tests/test_tool_allowlist.py::<node> -p no:randomly`.
- Per attack: (i) implement JUST the seam so the target pin PASSES (per-pin satisfiability leg);
  (ii) apply the specific WRONG build; (iii) `--collect-only` to declare expected-RED node ids
  BEFORE running (#196); (iv) run; (v) record RED (caught) or GREEN (MISSING PIN); heartbeat + append.
- Live store not needed: `build_mcp_server` registers tools synchronously and returns; the
  store-connecting lifespan runs only when the server serves. Confirmed no store contact in these pins.

---
## Attack 1 — G collision-guard discrimination (author's flagged weak spot) — **CAUGHT (pin sufficient)**

**Target pin:** `TestCollisionGuardChecksTheDeclaredUniverse::test_disabled_builtin_name_not_claimable_by_an_extension`
(expected-RED node declared via `--collect-only` before run).

**Seam built (both legs):** never-register filter — disabled built-ins truly removed from
`mcp._tool_manager._tools` BEFORE `_register_extension_tools` runs its collision guard.

| leg | build | result |
|---|---|---|
| WRONG | `--gate` only (filter applied; guard checks `get_tool(spec.name)` = registered set) | **RED** — `Failed: DID NOT RAISE ValueError` (lore_search unregistered → guard misses → extension shadows the name → no raise) |
| CORRECT (satisfiability + positive control) | `--gate --guard-universe` (guard also rejects `spec.name in _ALL_BUILTIN_TOOL_NAMES`) | **PASS** (1 passed) |

**Verdict:** the behavioral pin **discriminates** (RED on the exact wrong build §G names, GREEN on
the correct build). It is NOT a false gate. The author's decision-3 concern is resolved empirically:
in a finished build a guard that reverts to the registered set is CAUGHT, not waved through. The
docstring pin (`test_collision_guard_docstring_names_the_declared_universe`) is a redundant second
guard, not the only one. No missing pin here.

Run tail (WRONG): `Failed: DID NOT RAISE <class 'ValueError'>` at test_tool_allowlist.py:398.
Run tail (CORRECT): `1 passed in 0.79s`.

---
## Attack 2 — E2 biconditional QUANTIFIER coverage — **MISSING PIN (E2 does not prove cross-ref exhaustiveness)**

**Claim under test (design §2.4):** *"The builder greps each of the 15 descriptions for lore_ tokens
naming a different tool; only those get the guarded-sentence treatment. The subset biconditional
then proves exhaustiveness — a missed cross-ref reddens it."* **This claim is FALSE for the
contract's fixtures.**

**Instrument (enumeration, `/tmp/adv45-scratch/loremaster/_adv_xref.py`, pasted in appendix):** built
the FULL server, extracted every built-in's top-level + per-param description, found each lore_ token
naming a DIFFERENT built-in (a cross-ref A→B), and classified each by whether ANY non-empty reduced
fixture has A∈enabled ∧ B∉enabled (the only shape that can redden E2's ⊆ leg).

**Result: of 24 description cross-references, only 5 are exercised; 18 are UNEXERCISED** (E2-blind).

Exercised (caught by a fixture): `lore_findings→{comms,impact,tasks}` (lore-dnd), `lore_read→lore_index`
(subset), `lore_read→lore_get_symbol` (lore-dnd), `lore_search→lore_get_symbol` (lore-dnd).
UNEXERCISED (no fixture splits the pair): `lore_claim_task→{comms,tasks}`, `lore_comms→lore_tasks`,
`lore_dead_code→lore_impact`, `lore_get_symbol→lore_search`, `lore_impact→{dead_code,search}`,
`lore_index→lore_search`, `lore_map→{diff,impact,search}`, `lore_read→lore_search`,
`lore_recall→lore_remember`, `lore_remember→lore_recall`, `lore_search→lore_read`,
`lore_tasks→{claim_task,comms}`, `lore_verify→lore_get_symbol`.

**Empirical proof (REAL E2 pin, minimal real derivation `_adv_patch2.py` + env-controlled leak):**

| mode | build | E2 result |
|---|---|---|
| A — CORRECT (satisfiability) | derivation drops all disabled tokens | **4 passed** |
| B — POSITIVE CONTROL: leak `lore_search→lore_get_symbol` (EXERCISED by lore-dnd) | keep get_symbol token in search's desc | **RED** — `[lore-dnd]` `Extra items in the left set: 'lore_get_symbol'` (test_tool_allowlist.py:489) |
| C — THE LEAK: leak `lore_search→lore_read` (UNEXERCISED) | keep read token in search's desc | **4 passed** — the disabled-neighbour leak is INVISIBLE |

The positive control proves the instrument (and E2) CAN see a leak the fixtures exercise; mode C
proves E2 is blind to the 18 that no fixture exercises. This is the P1c REACH class: the biconditional
certifies only the (referrer,referent) pairs the two reduced fixtures happen to split — cross-ref-guard
coverage is a HIDDEN CONSTANT (which pairs subset/lore-dnd split), not a CHECKED VARIABLE derived from
the description graph. A builder who forgets to guard any of the 18 unexercised cross-refs ships a
disabled-tool name on a reduced surface (a Trust Leg-1 over-claim: the agent believes it can call a
tool that is not registered) with every contract pin GREEN.

**MITIGATION for the ACTUAL packet-45 consumer:** E2[lore-dnd] DOES catch lore-dnd's own cross-ref
leaks (findings→{comms,impact,tasks}, search/read→get_symbol). So the driving real deploy is covered.
The gap is FUTURE reduced deploys (packet 54+ instance allowlists) and the design's overclaimed
exhaustiveness guarantee.

**THE PIN THAT SHOULD EXIST (derived coverage, INSTRUMENT-0):** a pin that ENUMERATES the actual
cross-references from the built descriptions (as `_adv_xref.py` does) and, for EACH A→B, builds the
witness config `{A enabled, B disabled}` and asserts B's token is absent from the served surface.
That makes cross-ref-guard coverage a checked variable over the DERIVED cross-ref set — a 16th tool or
a new cross-ref extends coverage automatically, and a single missed guard reddens. **The defect it
catches:** a builder leaving any of the 18 unexercised cross-references hardcoded.

---
## Attack 3 — E1 + CL3 byte-exact full-set anchor — **CAUGHT (E1 sound); design-doc §2.0 inaccuracy flagged**

**Ground truth correction:** CL3's accessor is `_server()._INSTRUCTIONS`, and `_server()` returns the
`loremaster.server` MODULE (test_comms_tool.py:4827). So **CL3 reads the module constant `_INSTRUCTIONS`,
NOT `mcp.instructions`** — the design doc §2.0 assertion *"every … pin reads `mcp.instructions` from a
server built by the default `_config`"* is INACCURATE for CL3. This determines whether a
`build_instructions` drift reaches CL3.

**Seam built:** `build_instructions(full)` returns the frozen literal snapshot (byte-exact),
env-controlled wrap-point-space drop (`ADV_DROP_SPACE`) + env-controlled constant rewire (`ADV_REWIRE`
→ `_INSTRUCTIONS = build_instructions(ALL)`, the builder's planned wiring, report §wiring item 2).

| mode | E1 (`test_full_set_reproduces_todays_instructions_byte_exact`) | CL3 (`test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs`) |
|---|---|---|
| A byte-exact, no rewire (satisfiability) | **pass** | **pass** |
| B drop space, NO rewire | **RED** (test_tool_allowlist.py:465) | **GREEN** — decoupled: CL3 reads the untouched literal |
| C drop space + rewire | **RED** | **RED** (test_comms_tool.py:7747) |

**Verdict:** **E1 discriminates** full-set drift (RED on a single dropped wrap-point space, GREEN
byte-exact) and is the LOAD-BEARING full-set anchor — it tests `build_instructions(full)` directly, so
it holds regardless of the `_INSTRUCTIONS` wiring. CL3 only ALSO catches the drift when the builder
rewires the constant to `build_instructions(ALL)` (mode C). The interp site cannot be left as the
literal either: E2[subset]/E2[lore-dnd] redden if `build_mcp_server` serves the full literal on a
reduced surface. So the byte-exact property is guarded. **Not a missing pin.**

**FLAG (non-blocking):** (1) design §2.0's "CL3 reads mcp.instructions" is wrong — CL3 reads the module
constant; the builder MUST rewire `_INSTRUCTIONS = build_instructions(ALL)` (report §wiring item 2) for
CL3 to remain a live derivation anchor rather than a static literal check. (2) There is no pin asserting
`mcp.instructions == build_instructions(enabled)` for the DEFAULT/full build directly — E2[full] (token
equality, trivially true) and CL3 (constant) are the only full-default guards; a builder who fumbled
the interp wiring while keeping the constant correct would pass full/default and only redden on reduced
E2. Adequately covered by E2 reduced fixtures, but worth an explicit note.

---
## Attack 4 — D wire (#296 wrong-instance) — **CAUGHT (pin sufficient)**

**Target pin:** `TestDisabledToolIsUncallableOnTheWire::test_disabled_tool_is_absent_and_uncallable`.

| leg | build | D result |
|---|---|---|
| CORRECT (satisfiability) | true-gate: disabled built-ins removed from `_tool_manager` | **pass** (call_tool raises `Unknown tool: lore_map`) |
| WRONG (#296 wrong-instance) | register all 15, wrap `mcp.list_tools` to filter POST-construction, wire handler live | **RED** — first assert passes (filtered from list_tools) but `call_tool('lore_map', {})` raises `Error executing tool lore_map: Context is not available outside of a request`, which the `match=r"[Uu]nknown tool.*lore_map"` REJECTS |

**Verdict:** D's SECOND assertion (uncallable via the low-level dispatch, matched specifically on
`Unknown tool`, not the bare `ToolError` type) is the load-bearing discriminator. A registered tool
errors as `ToolError` too, so a match on the type alone would have waved the wrong-instance build
through; the string match kills it. The pin proves never-registration is immune to the wire-vs-instance
split #296 names. Not a missing pin.

---
## Attack 5 — empty reach-check (L2-1 / INSTRUMENT-0) — **CAUGHT (reach is a checked variable)**

**Target pin:** `TestNeverRegisterFilter::test_empty_enabled_registers_EXACTLY_zero_builtins_reach_check`
— drives `_register_tools` directly (bypassing `build_mcp_server`) at `enabled=∅` and asserts ZERO
built-ins register.

| leg | build | result |
|---|---|---|
| CORRECT (satisfiability) | all 15 sites gated | **pass** (`_register_only_builtins(∅) == set()`) |
| WRONG | 14 of 15 gated (`lore_search` site un-gated → survives even at ∅) | **RED** — `assert {'lore_search'} == set()` (test_tool_allowlist.py:344) |

**Verdict:** the pin makes filter coverage a CHECKED VARIABLE — the observed registered set at
`enabled=∅` must be empty, so ANY single un-gated `@mcp.tool` site surfaces as `count>0` (not a
hand-list of the 15 sites; derived from the actual registered surface). This is INSTRUMENT-0 done
right, and it discriminates.

**Empty biconditional is NOT the only empty pin (confirmed):** `test_empty_surface_names_no_tool`'s
first assert is the vacuous `∅==∅` token check, but the DEDICATED reach-check above is a separate,
`build_instructions`-INDEPENDENT pin carrying `_register_only_builtins(∅) == set()`. (Belt-and-braces:
`test_empty_surface_names_no_tool`'s SECOND assert is the same reach check, but it errors on the
`build_instructions` stub's NotImplementedError before reaching it — so the dedicated pin is the clean
isolator.) Anti-vacuity holds: the C-class `[full]/[subset]/[lore-dnd]` params assert NON-empty
registration, so "zero registered" cannot pass for the wrong reason (a totally-empty `_register_tools`).

---
## Attack 6 — boot loud-fail (A / Fork B) — **CAUGHT (both checks + control + message-content leg)**

**Seam built:** `_validate_tool_allowlist(config, extension_tool_names)` — unknown-name universe check +
empty-total-surface check — wired into `build_mcp_server`. Env skips drop one check at a time.

| mode | build | `unknown_name` | `empty_total` | `CONTROL_valid_boots` |
|---|---|---|---|---|
| A CORRECT | both checks live | pass | pass | pass |
| B `ADV_SKIP_UNKNOWN` | drop universe check | **RED** (DID NOT RAISE, :250) | pass | pass |
| C `ADV_SKIP_EMPTY` | drop empty-total check | pass | **RED** (DID NOT RAISE, :282) | pass |
| D bare message | raise names ONLY the unknown, not the known set | **RED** (:254 — 2nd assert) | — | — |

**Verdict:** both boot loud-fails are INDEPENDENTLY pinned and discriminating; the positive control
(`test_CONTROL_a_valid_allowlist_boots_without_raising`) passes in every mode, proving the loud-fails
are SPECIFIC to (unknown name / empty surface), not "any `tools:` section fails". Mode D confirms the
unknown-name pin's SECOND assertion is load-bearing (the message must NAME the known set as evidence it
validated against the universe — a bare rejection is caught). No missing pin.

**Note (decision 2, exception type):** the contract pins `ValueError` for both loud-fails (author's
decision 2, ruling silent → `ValueError`). The brief RULES Fork B's exception = `ValueError`, so this is
settled; the pins match the ruling.

---
## P2 — fixture-value perturbation (D's sole wire-witness `lore_map`) — **fixture discriminates**

Perturbed the D pin's single wire-witness from `lore_map` to `lore_get_symbol` (scratch test copy
`tests/test_p2_perturb.py`, pasted in appendix — REQUIRED scratch-copy mode for P2).

| leg | build | perturbed D | reach-check |
|---|---|---|---|
| A correct-build CONTROL | true-gate all | **pass** | pass |
| B uniform #296 wrong-instance | list_tools filtered, wire live | **RED** (`Error executing tool lore_get_symbol: …validation error`, not "Unknown tool") | — |
| C | post-construction filter | — | **RED** (`_register_tools` alone doesn't gate → 15 register) |

**Verdict:** D's `lore_map` value is NOT a discrimination-limiting monoculture — any disabled tool
witnesses the uniform #296 defect (B). The ONLY build where D's single value could hide a defect is a
non-uniform hybrid (truly-gate lore_map, post-filter the other 9 with live wires); that build is closed
by the reach-check (C), which drives `_register_tools` DIRECTLY and so FORCES the gating into
`_register_tools` (never-register) — uniformly killing the wire for all disabled tools. **Residual note
(not a missing pin):** D's sufficiency for the full disabled set RELIES on the reach-check forcing
gating into `_register_tools`; a future refactor that moved gating to `build_mcp_server` AND weakened
the reach-check would re-open D's single-value gap. The suite as written is sound.

---
## P-PKG — package survey (my table, diffed vs author's "none")

Author's line: *"Packages considered: none — no external mechanism specified (contract + stubs only)."*
I built my own table before accepting it:

| mechanism | library evaluated · what I READ | verdict |
|---|---|---|
| lore_ token extraction | `re` (stdlib), reused `_TOOL_NAME_TOKEN` regex | reuse (in-tree regex) |
| `tools:` config section | pydantic `_StrictModel` (installed; read `AuthConfig` idiom config.py:358) | reuse (pydantic) |
| never-register filter | FastMCP `ToolManager` (read installed API: `get_tool`/`remove_tool`/`_tools`) — no library offers config-gated MCP tool registration | bespoke (in-tree seam) |
| boot validation | stdlib set-difference + emptiness | bespoke-trivial |
| served-prose derivation | string assembly; reuses `_declared_instructions` (CL3 oracle) | bespoke (reuse oracle) |
| `render_sample_tools_section` | PyYAML (read: `yaml.dump` emits valid YAML but NOT comment-prefixed blocks; the sample is deliberately commented-out/inert) | bespoke (PyYAML unfit) |
| posture partition | `partition_tools_by_posture` (#291, in-tree) | reuse (in-tree) |

**Diff verdict: CONCUR with "none."** No external package is a fit; every mechanism is stdlib,
pydantic-reuse, in-tree-reuse, or bespoke-with-a-read-backed-reason. The author's terse "none" reaches
the right answer; my table adds the READ column (FastMCP filter, PyYAML sample) that the terse line
omitted. No package-substitution defect.

---
## P1b — per-invariant ∀-vs-guarded table (REQUIRED)

| invariant | pin(s) | ∀-over-inputs or GUARDED | receipt |
|---|---|---|---|
| filter SITE coverage (each of 15 sites gated) | reach-check `empty…reach_check` | **∀-over-sites** (observed==∅ is a checked variable) | attack 5: 14/15 reds |
| registered == enabled set | C `registered…EXACTLY_the_enabled_set[full/subset/lore-dnd]` | GUARDED-by-3-representative-fixtures (exact-set, both directions) | attack 1/5 gating legs; P2 |
| disabled tool uncallable ON WIRE | D `disabled_tool_is_absent_and_uncallable` | GUARDED-by-single-witness `lore_map` — generalized by the reach-check | attack 4 + P2 (perturbed witness reds; reach-check closes hybrid) |
| full-set instructions byte-exact | E1 `full_set_reproduces…byte_exact` | GUARDED-by-full-fixture (single anchor point) | attack 3 (dropped space reds) |
| served tokens == enabled (⊆: no disabled named) | **E2 `served_lore_tokens_equal_the_enabled_set[*]`** | **GUARDED-by-which-cross-refs-the-fixtures-split — INCOMPLETE (18/24 unexercised)** | **attack 2: MISSING PIN** |
| no gutted header / no dangling arrow | E3 `no_gutted_header_and_no_dangling_arrow[*]` | ∀-over-served-lines WITHIN each of 4 fixtures; GUARDED-by-4-fixtures | NOT empirically attacked (honest bound — build_instructions stub raises; lore-dnd exercises a reduced LADDER) |
| unknown enabled name loud-fails | A `unknown_enabled_name_fails_boot_LOUDLY` | ∀-over-enabled-names (set-difference vs universe), tested at 1 bogus value | attack 6 (skip reds; bare-message reds) |
| empty total surface loud-fails | A `empty_total_surface_fails_boot_LOUDLY` | GUARDED-by-empty-case | attack 6 (skip reds; control boots) |
| disabled built-in name reserved vs extension | G `disabled_builtin_name_not_claimable…` | ∀-over-universe (`spec.name in _ALL_BUILTIN_TOOL_NAMES`), tested at 1 witness (lore_search) | attack 1 (discriminates) |
| universe == registered full surface (anti-drift) | B `production_universe_equals…full_surface` | ∀-over-registered-surface (equality) | RE-1 identity verified: test IS prod object |
| test universe is prod object (single-source) | B `test_side_universe_is_the_SAME_object` | identity (`is`) — mutation of prod reddens all | verified: `suite._ALL… is prod` → True |
| sample section tokens == universe | H `sample_section_names_exactly_the_universe` | ∀-over-universe (exact-set) | NOT attacked (stub raises; H is 45b territory) |
| partition ⊆ enabled, ∅ ∩ disabled | I `partition_of_a_reduced_surface…` | GUARDED-by-lore-dnd-fixture; follows from C+gating | derived from gating; not separately attacked |
| default identity == today's paragraph | F `default_identity_is_todays_exact_paragraph` | single-point (GUARDED) | attack 3-adjacent (identity para stable) |
| custom identity served verbatim | F `custom_identity_is_served_verbatim` | GUARDED-by-one-custom-string | not separately attacked (Fork A ruled) |

**KEY:** every GUARDED row carries a receipt showing its guard FIRES, **except E2's ⊆ leg**, whose
guard (fixture cross-ref coverage) is demonstrably INCOMPLETE (attack 2) — that is the one missing pin.
F's default-identity row is a RULED bound, not a hole: the default is deliberately today's string
(which over-claims on a reduced surface — the design §3 Leg-1 defect), and the fix is the
operator-authored `config.identity` (Fork A). Packet 45's obligation is "do not auto-generate an
over-claim," met by keeping the default constant; the reduced-surface truthfulness is deferred to
packet 54 (operator authors the dnd identity). This is the ONLY invariant where the served surface can
still over-claim, and it is ruled/accepted — flagged, not a defect.

---
## P1c — per-instrument REACH table (REQUIRED)

Legs: E = empirical (guard in-tree, wrong-build run); C = construction-inspection.

| instrument | reach (SET of sites) | reach DERIVED or hand-list? | coverage a CHECKED var? | effect or PROXY? | one-source by mutation? | leg |
|---|---|---|---|---|---|---|
| reach-check (empty) | the 15 registration sites | **DERIVED** (observed registered surface at ∅) | **YES** (observed==∅; any un-gated site → count>0) | EFFECT (real registration) | n/a | **E** (attack 5) |
| anti-drift guard (B/L2-3) | the full registered surface | **DERIVED** (reads live registration) | YES (universe==surface; a 16th tool reds) | EFFECT | universe is the ONE prod const; test aliases it (`is`) | E (identity verified) |
| collision guard (G) | `spec.name ∈ universe` | **DERIVED** (the universe frozenset) | YES (checks full universe, not a name-list) | EFFECT (raise at registration) | one prod universe | **E** (attack 1) |
| **E2 biconditional (⊆ cross-refs)** | **the (referrer,referent) pairs the 2 reduced fixtures split** | **HAND-LIST / HIDDEN CONSTANT** (which pairs subset+lore-dnd happen to split) | **NO** (18/24 cross-refs unexercised; adding a cross-ref does NOT extend coverage) | EFFECT (served surface) | n/a | **E (attack 2 — MISSING PIN)** |
| every-token pin (existing) | served text of the DEFAULT full config | DERIVED (scans served text) but runs only at full → all live | NO for reduced surfaces (E2 was meant to extend it) | EFFECT | n/a | C (subsumed by E2) |
| E1 byte-exact anchor | `build_instructions(full)` | single point (full) | n/a (equality anchor) | EFFECT (calls the function) | vs `_declared_instructions` oracle | E (attack 3) |
| CL3 terminating pin | the MODULE constant `_INSTRUCTIONS` | single doc | n/a (equality) | **PROXY** — reads the constant, NOT served `mcp.instructions` (attack 3); live only if builder rewires the constant | vs `_DECLARED_NON_COMMS_PARAGRAPHS` | E (attack 3) |
| boot validation (A) | `enabled − universe` + total-surface | DERIVED (set-difference vs universe) | YES (∀ enabled names) | EFFECT (raises) | one universe | E (attack 6) |

**KEY:** every instrument is reach-DERIVED + coverage-checked + effect-observed **EXCEPT E2's cross-ref
⊆ leg**, whose reach is a HIDDEN CONSTANT (the pairs the fixtures split) and whose coverage is NOT a
checked variable — the seventh-defeat shape (INSTRUMENT-0). CL3 observes a PROXY (the module constant),
but E1 (direct call) + E2 (served `mcp.instructions`) backstop the served surface, so CL3's proxy nature
is not a hole — just a note that the builder MUST rewire `_INSTRUCTIONS` (report §wiring item 2) for CL3
to stay a live anchor. The reach-check, anti-drift, collision, and boot-validation instruments all pass
all four axes empirically.

---
## MISSING PINS (the fix the author can go write)

**MP-1 (from attack 2) — the derived cross-reference coverage pin.**
- *The test that should exist:* a pin that ENUMERATES the actual description cross-references from the
  built full server (as `_adv_xref.py` does — build full, for each built-in collect the lore_ tokens in
  its top-level + per-param descriptions naming a DIFFERENT built-in), and for EACH cross-ref A→B builds
  the witness config `{A enabled, B disabled}` (a single reduced deploy per pair) and asserts B's token
  is ABSENT from A's served description. Coverage becomes a CHECKED VARIABLE over the DERIVED cross-ref
  set — a 16th tool or a new cross-ref extends it automatically, and one missed guard reddens.
- *The defect it catches:* a builder who leaves any of the **18 unexercised cross-references** (listed
  in attack 2) hardcoded in a description — shipping a disabled tool's name on a `{A,¬B}` reduced
  deploy (a Trust Leg-1 over-claim: the consuming agent believes it can call a tool that is not
  registered), with every current contract pin GREEN.
- *Why the current E2 fixtures do not catch it:* the biconditional's ⊆ reach is the (referrer,referent)
  pairs that `{subset, lore-dnd}` happen to split — a hidden constant, not the description graph. Proved:
  leaking `lore_search→lore_read` stays GREEN across all 4 E2 fixtures; the positive control
  `lore_search→lore_get_symbol` reds `[lore-dnd]`.
- *Design-doc correction owed:* §2.4's claim *"the subset biconditional then proves exhaustiveness — a
  missed cross-ref reddens it"* is FALSE for these fixtures and should be struck or scoped.

## RESIDUALS / FLAGS (surfaced, not blockers)
- **§2.0 CL3 inaccuracy (attack 3):** CL3 reads the MODULE constant `_INSTRUCTIONS`, not
  `mcp.instructions`. The builder MUST rewire `_INSTRUCTIONS = build_instructions(ALL)` for CL3 to remain
  a live derivation anchor (report §wiring item 2). E1 is the load-bearing full-set guard regardless.
- **F default-identity over-claim (P1b):** the default IDENTITY paragraph is deliberately today's string,
  which over-claims on a reduced surface. RULED/accepted (Fork A → operator authors `config.identity`;
  reduced-surface truthfulness deferred to packet 54). Not a defect — a ruled bound with a re-open
  trigger (packet 54). No `lore_`-token pin can catch this natural-language over-claim.
- **D single-value dependence (P2):** D's `lore_map`-only wire test is sufficient ONLY because the
  reach-check forces gating into `_register_tools`. A future refactor moving gating to `build_mcp_server`
  + weakening the reach-check would re-open it.
- **E3 not empirically attacked (P1b honest bound):** I did not build a LADDER-strip wrong build (the
  minimal derivation named tools without arrows). E3's dangling-arrow leg is exercised by lore-dnd's
  reduced LADDER by construction, but I did not run a wrong-build receipt for it.

## VERDICT: **CONTRACT INSUFFICIENT**

Five of the six probed pins are individually SATISFIABLE and DISCRIMINATING (attacks 1, 3, 4, 5, 6 +
P2). One probe (attack 2) found a concrete MISSING PIN: the E2 biconditional does NOT prove
cross-reference exhaustiveness — 18 of 24 description cross-references are unexercised by the fixture
set, and a build leaking any of them is byte-identical to healthy across all four E2 fixtures (proved,
with a positive control). This is the INSTRUMENT-0 reach class the adversary exists to catch at CONTRACT
time: the guard's reach is a hidden constant, not a checked variable. Route MP-1 back to CONTRACT.

**Mitigation for the lead's sizing call:** the DRIVING consumer (lore-dnd) IS covered by E2[lore-dnd],
so this is not a blocker for the immediate dogfood deploy — but the contract's stated exhaustiveness
guarantee is false, and a future reduced deploy (packet 54+) would ship an unguarded cross-ref
silently. MP-1 is a single derived pin; cheap to add, and it CLOSES the class rather than adding N more
fixtures.

---
## Appendix — instruments (deliverables; pasted verbatim per brief-base §1)

All ran inside `/tmp/adv45-scratch` (provenance-verified copy; `loremaster.__file__` →
`/tmp/adv45-scratch/loremaster/loremaster/__init__.py`). Wrong builds applied via string-replace
patchers over `server.py.orig` (pristine). Key instruments:

### `_adv_xref.py` (attack 2 cross-reference enumerator)
```python
# build full server; for each built-in collect lore_ tokens in top-level + per-param
# descriptions naming a DIFFERENT built-in (a cross-ref A->B); classify each by whether
# any reduced fixture has A in enabled and B not in enabled (the only shape reddening E2 ⊆).
TOKEN = re.compile(r"\blore_[a-z_]+\b"); UNIVERSE = set(_ALL_BUILTIN_TOOL_NAMES)
SUBSET = {"lore_search","lore_read","lore_get_symbol","lore_remember","lore_recall"}
LORE_DND = {"lore_search","lore_read","lore_index","lore_diff","lore_findings"}
# xref[A] = {other built-ins named in A's description/params}; discard A itself.
# For each A->B: exercised iff (A in SUBSET and B not in SUBSET) or (A in LORE_DND and B not in LORE_DND).
```

### `_adv_patch2.py` (attack 2 minimal derivation) — env-controlled leak
```python
# build_instructions(enabled) = identity_para + "\n".join(sorted(enabled))  # names EXACTLY enabled
# _register_tools gates disabled built-ins (del from _tool_manager._tools) then token-strips
# each surviving description of disabled-tool names, EXCEPT keep {ADV_LEAK_REFERENT} in
# the description of tool named ADV_LEAK_REFERRER (the "leak one cross-ref" wrong build).
# build_mcp_server serves instructions=build_instructions(_adv_enabled(config)).
```
Modes: no env → CORRECT (E2 all green); `ADV_LEAK_REFERRER=lore_search ADV_LEAK_REFERENT=lore_get_symbol`
→ E2[lore-dnd] RED (positive control); `…REFERENT=lore_read` → E2 all green (the finding).

### `tests/test_p2_perturb.py` (P2 fixture-value perturbation) — see body committed in scratch; asserts
the D pin's wire-uncallability for `lore_get_symbol` (perturbed from `lore_map`): passes on the
true-gate build, reds on the #296 wrong-instance build.

Other patchers (`_adv_patch.py` gate/gate-14/guard-universe; `_adv_patch4.py` gate/wrong-instance;
`_adv_patch3.py` byte-exact+drop+rewire; `_adv_patch6.py` boot-validation+skips) applied the wrong
builds for attacks 1/3/4/5/6 exactly as tabulated above.
