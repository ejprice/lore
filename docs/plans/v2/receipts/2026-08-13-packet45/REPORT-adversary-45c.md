# REPORT-adversary-45c — packet 45 DELTA adversary: verify MP-1 + wiring pins

`brief-base v13 read` · `brief project v7 read`

## Summary block (read first)
- **state:** done.
- **task:** DELTA pass — verify ONLY the two NEW pins added at `f48ad14` in
  `loremaster/tests/test_tool_allowlist.py`; do NOT re-grade the 5 already-CAUGHT attacks
  (those are graded in `REPORT-adversary-45.md`).
- **VERDICT: CONTRACT SUFFICIENT.** Both new pins are satisfiable on a correct build,
  MP-1 discriminates the unexercised leak E2 is structurally blind to, MP-1's reach is a
  CHECKED VARIABLE over the derived cross-ref graph, and the wiring pin discriminates both
  wrong wirings its docstring names.
- **P1 (satisfiability):** both GREEN on my minimal correct reference — `2 passed`
  (§Check-1). Neither is a C-DEF trap (red-for-wrong-reason).
- **discrimination:** with `ADV_LEAK=lore_search:lore_read` (the marquee E2-unexercised
  cross-ref): **MP-1 RED (2 leaks, both `lore_read`)**, **E2 all 3 non-empty params GREEN**
  (§Check-2). MP-1 catches exactly what E2 cannot.
- **reach is a checked variable:** derived count `24 → 25` when a synthetic `lore_search→
  lore_diff` cross-ref is injected (the new pair appears in the enumeration), and the
  `>= 20` anti-vacuity floor FIRES on graph collapse (`enumerated 0`) (§Check-3).
- **wiring discrimination (bonus P1 wrong-builds):** `ADV_WIRE=literal` (serve frozen
  `_INSTRUCTIONS`) → RED; `ADV_WIRE=full` (serve `build_instructions(_FULL)` regardless of
  enabled) → RED (§Check-4).
- **Packages considered:** none — no mechanism specified. The two pins use stdlib `re` +
  in-tree helpers; my scratch reference build uses stdlib `re` only. I concur with
  adversary-45 §P-PKG.
- **Reuse ledger:** none — I introduced no production symbol. My scratch instruments reuse
  the test's OWN `_builtin_crossref_map` (the exact enumeration MP-1 quantifies over) so the
  reach proof is faithful, not a parallel re-implementation.
- **Graded:** `f48ad14` · HEAD-at-report: `f48ad14` · SAME. (Contract-45c committed the two
  pins at `f48ad14`; my scratch copy is a `scratch_copy.sh` of the working tree at that sha.)
- **Scratch provenance (#140):** `loremaster.__file__ = /tmp/adv45c_s1/loremaster/loremaster/__init__.py`
  (INSIDE the scratch root; `scratch_copy.sh` assertion passed; `uv run` receipt §Provenance).
  No worktrees (NO-WORKTREES directive honoured).
- **decisions-needed:** none.
- **flag (not a blocker):** my *minimal* reference gates at `build_mcp_server` (not inside
  `_register_tools`), so the two EMPTY-reach pins that drive `_register_tools` directly
  (`test_empty_surface_names_no_tool`, `test_empty_enabled_registers_EXACTLY_zero_builtins_reach_check`)
  are RED on my reference. That is an artifact of WHERE my probe gates — NOT a contract
  defect and NOT one of my two target pins. E1 (byte-exact full-set) is out of scope per
  brief and also red on my minimal ref. The shipped builder gates inside `_register_tools`;
  none of this touches MP-1 or the wiring pin.
- **receipt pointers:** satisfiability §Check-1; discrimination §Check-2; reach §Check-3;
  wiring wrong-builds §Check-4; reference-build diff §Instrument-A; reach script
  §Instrument-B. Full probe record + commands below the summary.

---

## Milestones (incremental log — written as I went)
1. analysis: read both new pins + adversary-45 Attack 2 + `_adv_patch2.py`; mapped FastMCP
   seams (`_tool_manager._tools` / `remove_tool` / `list_tools`; `mcp.instructions` is a
   READ-ONLY property → the correct build must pass `instructions=` via the constructor).
2. scratch built + provenance-verified; stub RED baseline reproduced (MP-1 = 36 leaks via
   the leak assert — the RIGHT reason, not a `NotImplementedError`; wiring = RHS
   `NotImplementedError`).
3. built minimal correct reference (`_adv_patch2.py`'s approach on real seams) → both pins
   GREEN.
4. discrimination + reach + wiring wrong-builds all confirmed.

---

## What the two pins are (delta scope)

**MP-1** `TestEveryDescriptionCrossRefDropsItsDisabledReferent::test_every_crossref_drops_its_disabled_referent`
enumerates the A→B built-in description cross-references from the FULL built server
(`_builtin_crossref_map`, DERIVED — reuses `_TOOL_NAME_TOKEN`), asserts `len(pairs) >= 20`
(anti-vacuity), then for EACH distinct referent B builds the witness `_FULL − {B}` and
asserts B is absent from every referrer A's served description AND from the whole served
surface. It closes adversary-45 Attack 2: E2's ⊆ leg reddens only for a (referrer,referent)
pair some E2 fixture splits, and 18 of 24 cross-references are unexercised by all four E2
fixtures.

**wiring** `TestInstructionsInterpSiteWiresBuildInstructions::test_reduced_surface_instructions_are_build_instructions_of_enabled`
asserts, on the lore-dnd reduced surface, `mcp.instructions == build_instructions(registered,
identity=config.identity)` where `registered` is DERIVED from the actually-registered
built-in surface. It closes adversary-45 Attack-3 FLAG #2: E2 catches an interp-site fumble
only transitively via tokens.

---

## Per-invariant classification (P1b, focused on the two delta pins)

| invariant the pin guards | ∀-over-inputs or guarded? | receipt |
|---|---|---|
| MP-1: every disabled referent B is dropped from every referrer A's served text, ∀ A→B in the DERIVED cross-ref graph | **∀-over-inputs** (quantifies the whole enumerated graph, one witness build per referent; NOT keyed to the failure mode) | leak `lore_search→lore_read` — an UNEXERCISED pair no E2 fixture reaches — is caught (§Check-2); the enumeration is derived, so a new pair is quantified automatically (§Check-3 leg 1) |
| wiring: served `mcp.instructions` == `build_instructions(actually-registered set, identity)` at the interp site | **∀ over the argument** (RHS reconstructed from the REGISTERED surface, not an assumed enabled computation) | both wrong wirings (`_INSTRUCTIONS` literal / `build_instructions(_FULL)`) are caught (§Check-4) |

Both invariants are universals over their inputs, not conditionals keyed to the failure mode
that prompted them — the quantifier-law trap (PR93) is not present in either new pin.

## Per-instrument reach table (P1c, focused on MP-1 — the only new guard with a reach)

| axis | MP-1 verdict | evidence |
|---|---|---|
| reach set | the A→B pairs across ALL registered built-ins' top-level + per-param descriptions | `_builtin_crossref_map` iterates `mcp.list_tools()` |
| DERIVED or hand-list? | **DERIVED** from the built descriptions | synthetic `lore_search→lore_diff` injected on the full build → enumerated count `24 → 25`, new pair present (§Check-3 leg 1). A hand-list would not have grown. |
| coverage a CHECKED variable? | **YES** — a 16th tool or a new cross-ref extends the ∀ automatically; the `>= 20` floor fails CLOSED on collapse | anti-vacuity floor fires on `enumerated 0` (§Check-3 leg 2) |
| effect or proxy? | **EFFECT** — reads the actual served surface (`_served_lore_tokens` + `_builtin_crossref_map` off `mcp.list_tools()`), builds a real witness server per referent | §Check-2 reds on the served text of witness `_FULL−{lore_read}` |
| one source of truth? | reuses `_TOOL_NAME_TOKEN` (the every-token pin's own regex) + shared `_tool_description_texts` (shared with E2's `_served_lore_tokens`) | contract-45c §DRY; verified in the source read |

All three P1c legs for MP-1 were run EMPIRICALLY (not construction-inspection): I injected a
synthetic cross-ref and watched the derived count grow, and I collapsed the graph and watched
the floor fire, both against the real instrument.

---

## Check 1 — SATISFIABILITY (P1, the unverified leg — highest value)

Minimal CORRECT reference built in scratch (`_adv_patch2.py`'s approach on the real seams —
§Instrument-A): `build_instructions(enabled, identity) = identity_para + "\n\n" +
"\n".join(sorted(enabled))` (order-insensitive over a frozenset); `build_mcp_server` wires
`instructions=build_instructions(enabled, identity=config.identity)` at the interp site, then
gates — `remove_tool` for each disabled built-in, then token-strips disabled names from every
surviving description (top-level + per-param).

Expected-RED node ids declared from `--collect-only` BEFORE the run (both NEW at `f48ad14`):
- `…::TestEveryDescriptionCrossRefDropsItsDisabledReferent::test_every_crossref_drops_its_disabled_referent`
- `…::TestInstructionsInterpSiteWiresBuildInstructions::test_reduced_surface_instructions_are_build_instructions_of_enabled`

**Stub RED baseline (right reason confirmed):** MP-1 reds via the LEAK assert —
`AssertionError: disabled referents leaked into served text on reduced surfaces (36 leak(s))`
(24 `desc:` + 12 `surface:`), NOT a `NotImplementedError` — a live discriminating pin against
the stub's real served surface. Wiring reds via RHS `build_instructions` `NotImplementedError`.
(36 leaks reproduces contract-45c's count exactly.)

**Correct build → both GREEN:**
```
tests/…::TestEveryDescriptionCrossRefDropsItsDisabledReferent::test_every_crossref_drops_its_disabled_referent PASSED
tests/…::TestInstructionsInterpSiteWiresBuildInstructions::test_reduced_surface_instructions_are_build_instructions_of_enabled PASSED
============================== 2 passed in 1.39s ===============================
```
Neither pin is a C-DEF trap (neither stays red on a known-correct build). The wiring pin's
`LHS ≡ RHS` claim (reviser: `registered == enabled` ∧ `build_instructions` order-insensitive
over a frozenset) HOLDS — verified empirically: the pin is green because my `build_instructions`
sorts internally and my gated `registered` set equals the config-enabled set.

## Check 2 — DISCRIMINATION (MP-1 catches what E2 cannot)

On the correct build I leak EXACTLY ONE previously-UNEXERCISED cross-ref
(`ADV_LEAK=lore_search:lore_read` — re-inject `lore_read`'s token into `lore_search`'s
description only when `lore_read` is disabled). Expected: MP-1 RED, E2 GREEN.
```
…TestEveryDescriptionCrossRefDropsItsDisabledReferent::test_every_crossref_drops_its_disabled_referent FAILED [ 25%]
…TestServedProseNamesExactlyTheEnabledTools::test_served_lore_tokens_equal_the_enabled_set[full]     PASSED [ 50%]
…::test_served_lore_tokens_equal_the_enabled_set[subset]   PASSED [ 75%]
…::test_served_lore_tokens_equal_the_enabled_set[lore-dnd] PASSED [100%]
========================= 1 failed, 3 passed ==========================
```
MP-1 reds SURGICALLY — exactly the injected leak, no over-fire:
```
AssertionError: disabled referents leaked into served text on reduced surfaces (2 leak(s)):
  surface: disabled lore_read named on the served surface of witness _FULL−{lore_read}
  desc: lore_search→lore_read — lore_search's served description still names disabled lore_read
```
E2 stays GREEN because no E2 fixture (`{full, subset, lore-dnd}`) disables `lore_read` while
`lore_search` is enabled — the exact HIDDEN-CONSTANT blindness adversary-45 Attack 2 measured.
**MP-1 discriminates the leak E2 is structurally blind to.**

## Check 3 — REACH IS A CHECKED VARIABLE (P1c)

**Leg 1 — derived count grows with the graph** (reuses MP-1's own `_builtin_crossref_map`,
§Instrument-B):
```
-- baseline (no synthetic cross-ref) --
PAIRS_COUNT 24
HAS_search_diff False
-- with ADV_SYNTH=lore_search:lore_diff (a pair NOT in the original set) --
PAIRS_COUNT 25
HAS_search_diff True
```
The enumeration is DERIVED from the built descriptions: injecting a new cross-ref extends the
quantified set automatically (a hand-list would stay at 24). Baseline 24 corroborates
adversary-45's independent `_adv_xref.py` and contract-45c (three independent enumerations
agree).

**Leg 2 — anti-vacuity floor fires on collapse** (`ADV_NOXREF` strips every built-in name from
every description → 0 cross-refs):
```
assert len(pairs) >= 20
AssertionError: expected >= 20 derived description cross-references (adversary-45 found 24); enumerated 0: []
assert 0 >= 20
1 failed
```
A coverage collapse (descriptions that stopped naming neighbours) is CAUGHT by the floor, not
silently waved through as a passing ∀-over-nothing. This is the P0 positive control for the
anti-vacuity instrument.

## Check 4 — WIRING pin discriminates both wrong wirings (bonus P1 wrong-builds)

The wiring pin's docstring names two wrong wirings; I forced each (`ADV_WIRE`):
```
=== correct (no env): wiring + MP-1 GREEN ===          2 passed
=== ADV_WIRE=literal  (serve frozen _INSTRUCTIONS) ===  1 failed  (wiring RED)
=== ADV_WIRE=full     (serve build_instructions(_FULL)) === 1 failed (wiring RED)
```
Both wrong wirings are caught. The wiring pin is not a no-op and not a trap; the enabled-set
argument is a checked variable (the identity argument is covered separately by pin F
`test_custom_identity_is_served_verbatim`, so the two pins jointly cover the interp site).

---

## Provenance receipt (#140)
```
$ cd /tmp/adv45c_s1 && uv run python -c "import loremaster; print(loremaster.__file__)"
PROVENANCE loremaster.__file__ = /tmp/adv45c_s1/loremaster/loremaster/__init__.py
```
INSIDE the scratch root — I graded my own reference build, not the original tree.
`scratch_copy.sh` provenance assertion passed at copy time (exit 0). No worktrees used.

---

## Verdict

**CONTRACT SUFFICIENT** for the two delta pins.

- MP-1 is satisfiable, discriminates the marquee UNEXERCISED cross-ref (`lore_search→lore_read`)
  that all four E2 fixtures miss, quantifies over a DERIVED reach (count grows with the graph),
  and fails CLOSED on graph collapse via its `>= 20` anti-vacuity floor.
- The wiring pin is satisfiable, its `LHS ≡ RHS` claim holds empirically, and it catches both
  wrong wirings its docstring names.
- No missing pin. No C-DEF trap. I tried to break both pins with a correct build (satisfiability),
  a single-cross-ref leak (discrimination), a synthetic cross-ref + a graph collapse (reach), and
  two wrong wirings — and could not. The receipts are above.

The one flag (my minimal ref gates at `build_mcp_server`, so the two EMPTY `_register_tools`-reach
pins and E1 are red on it) is an artifact of my probe's gate LOCATION, not a contract defect, and
is out of the two-pin delta scope.

---

## Instrument-A — the correct reference build (server.py diff vs `f48ad14`, verbatim)

Applied in `/tmp/adv45c_s1/loremaster/loremaster/server.py` (scratch, disposable). The
`ADV_*` env branches are the wrong-build/probe toggles; with NO env set the build is the
minimal CORRECT reference. This is the EXACT `diff HEAD:server.py` vs the scratch server.py,
verbatim (line-anchored):
```diff
1796c1796,1800
<     raise NotImplementedError("packet 45: build_instructions — builder implements (STUB)")
---
>     # ADVERSARY-45c minimal CORRECT reference (satisfiability probe — NOT the shipped
>     # build). Names EXACTLY the enabled set; sorts internally so it is order-insensitive
>     # over a frozenset (the wiring pin's LHS≡RHS requirement).
>     _identity = identity if identity is not None else _INSTRUCTIONS.split("\n\n")[0]
>     return _identity + "\n\n" + "\n".join(sorted(enabled))
9840a9845,9873
>     # ADVERSARY-45c minimal CORRECT reference (satisfiability probe — NOT the shipped build).
>     import re as _adv_re
>
>     _adv_all_builtins = set(_ALL_BUILTIN_TOOL_NAMES)
>     if config.tools is None:
>         _adv_enabled = frozenset(_adv_all_builtins)
>     else:
>         _adv_enabled = frozenset(config.tools.enabled)
>     _adv_disabled = _adv_all_builtins - _adv_enabled
>
>     # WIRING-DISCRIMINATION probe: ADV_WIRE forces the two wrong wirings the wiring pin's
>     # docstring names — 'literal' serves the frozen _INSTRUCTIONS, 'full' serves
>     # build_instructions(_FULL) regardless of the enabled set. Both must red the wiring pin.
>     import os as _adv_os0
>
>     _adv_wire = _adv_os0.environ.get("ADV_WIRE")
>     if _adv_wire == "literal":
>         _adv_instructions = _INSTRUCTIONS
>     elif _adv_wire == "full":
>         _adv_instructions = build_instructions(
>             frozenset(_ALL_BUILTIN_TOOL_NAMES), identity=config.identity
>         )
>     else:
>         _adv_instructions = build_instructions(_adv_enabled, identity=config.identity)
>
9843c9876
<         instructions=_INSTRUCTIONS,
---
>         instructions=_adv_instructions,
9849a9883,9933
>     # Gate: never-register the disabled built-ins.
>     for _adv_name in _adv_disabled:
>         if mcp._tool_manager.get_tool(_adv_name) is not None:
>             mcp._tool_manager.remove_tool(_adv_name)
>     import os as _adv_os
>
>     # DISCRIMINATION probe: ADV_LEAK="<referrer>:<referent>" re-injects ONE disabled
>     # referent token into <referrer>'s served description (a wrong build that leaks a
>     # single cross-ref). REACH probe: ADV_SYNTH="<tool>:<name>" appends a synthetic
>     # cross-ref token to <tool>'s FULL-build description (tests coverage grows with graph).
>     _adv_leak = _adv_os.environ.get("ADV_LEAK")
>     _adv_synth = _adv_os.environ.get("ADV_SYNTH")
>     if _adv_disabled:
>         _adv_pat = _adv_re.compile(
>             r"\b(?:" + "|".join(_adv_re.escape(_n) for _n in _adv_disabled) + r")\b"
>         )
>         for _adv_tool in mcp._tool_manager.list_tools():
>             if _adv_tool.name not in _adv_all_builtins:
>                 continue
>             _adv_desc = _adv_pat.sub("", _adv_tool.description or "")
>             if _adv_leak:
>                 _lref, _lreferent = _adv_leak.split(":")
>                 if _adv_tool.name == _lref and _lreferent in _adv_disabled:
>                     _adv_desc = _adv_desc + " " + _lreferent  # LEAK the one referent
>             _adv_tool.description = _adv_desc
>             _adv_props = (_adv_tool.parameters or {}).get("properties", {})
>             for _adv_schema in _adv_props.values():
>                 if isinstance(_adv_schema, dict) and "description" in _adv_schema:
>                     _adv_schema["description"] = _adv_pat.sub("", _adv_schema["description"] or "")
>     # REACH probe: on the FULL build (nothing disabled), append a synthetic cross-ref.
>     if _adv_synth and not _adv_disabled:
>         _sref, _sname = _adv_synth.split(":")
>         for _adv_tool in mcp._tool_manager.list_tools():
>             if _adv_tool.name == _sref:
>                 _adv_tool.description = (_adv_tool.description or "") + " " + _sname
>     # ANTI-VACUITY control: ADV_NOXREF strips EVERY built-in name from EVERY description
>     # on the FULL build → the cross-ref graph collapses to 0 pairs → MP-1's `>= 20` floor fires.
>     if _adv_os.environ.get("ADV_NOXREF") and not _adv_disabled:
>         _adv_nox = _adv_re.compile(
>             r"\b(?:" + "|".join(_adv_re.escape(_n) for _n in _adv_all_builtins) + r")\b"
>         )
>         for _adv_tool in mcp._tool_manager.list_tools():
>             if _adv_tool.name not in _adv_all_builtins:
>                 continue
>             _adv_tool.description = _adv_nox.sub("", _adv_tool.description or "")
>             for _adv_schema in (_adv_tool.parameters or {}).get("properties", {}).values():
>                 if isinstance(_adv_schema, dict) and "description" in _adv_schema:
>                     _adv_schema["description"] = _adv_nox.sub("", _adv_schema["description"] or "")
```

## Instrument-B — the reach-count script (`/tmp/adv45c_s1/loremaster/adv45c_reach_count.py`, verbatim)
```python
import asyncio, sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests")
import test_tool_allowlist as T

async def pairs_for_full() -> list[tuple[str, str]]:
    with tempfile.TemporaryDirectory() as d:
        mcp = T._build(Path(d), enabled=T._FULL)
        crossrefs = await T._builtin_crossref_map(mcp)   # MP-1's OWN instrument
        return sorted((a, b) for a, rs in crossrefs.items() for b in rs)

pairs = asyncio.run(pairs_for_full())
print("PAIRS_COUNT", len(pairs))
print("HAS_search_diff", ("lore_search", "lore_diff") in pairs)
```
Run baseline vs `ADV_SYNTH=lore_search:lore_diff`: 24 → 25, new pair present.
