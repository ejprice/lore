# REPORT-contract-04b5-1 — Packet 04b5 Link-5 render-site injection containment: the RED contract

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (tool honesty, first)
Brief satisfiable with the tools granted. lore tools loaded first try (`ToolSearch "+lore"`,
no #334 flake). `scratch_copy.sh` present and worked (provenance-asserting). No demand in the
brief exceeded my toolset. lore-first for structure (`lore_verify` confirmed both new symbols
`not_found` @HEAD; `lore_findings#321`); **grep is the honest tool** for the `!r`-population
sweep, fence-site exhaustiveness and prose-reference sweeps — used there and said so per hit.
No lore weakness forced a route-around; nothing filed.

## SUMMARY BLOCK
- state: **done-with-deviations** (contract written, RED-at-HEAD behaviourally, satisfiability proven).
- deviations:
  - `served_error` class (teaching-error + code-RAG `!r`) is neutralisation-driven on ONE
    store-free production site (`StoreReadTool._not_found_error`), not per-site; the full
    `!r`-population + rollup/comms-send-drain render sites are a **STATED RESIDUAL** (below), held
    IN scope by the derived partition. This is the honest bound of a store-free contract.
  - fixed ONE dangling prose reference in my own editable file (`test_task_read_surface.py:2965`,
    `test_attribution_bound.py` → the new contract); 3 more dangle in files I may not edit — flagged.
- Packages considered: none — the seam is stdlib string/`re` work over the repo's OWN sanitiser
  primitives (`sanitise.max_backtick_run`/`FENCE_CHAR`); no external mechanism was specified or built.
- Graded: n/a (this is a contract, not a verdict on another artifact). Authored against HEAD `5cedb38`;
  `git rev-parse HEAD` = `4c5930d` (the packet-mint commit) at report time — my base for all "RED at
  HEAD" claims is `5cedb38`/`4c5930d` (same tree state for the surfaces I touch; both pre-04b5-build).
- **DECISIONS-NEEDED (for the adversary / lead — surfaced, not resolved):**
  1. **Per-SITE served_error reach.** The partition proves every free-text PARAM is IN a class a
     driver neutralises; it does not, alone, prove every SITE routes through the seam ("routing is not
     sharing", #102). Undriven sites: the ~291-`!r` population (task_id!r ×19, findings/agents ledger
     not-found, `lore_get_symbol`/`lore_impact` errors), plus the ROLLUP (summary/report_path) and
     comms SEND/DRAIN (thread/refs) render sites. Recommend the adversary/builder add a store-backed
     per-site runtime sweep to reach full all-or-nothing SITE coverage. (§B/D residual note in-file.)
  2. **3 dangling prose references to the deleted `test_attribution_bound.py`** must be updated when
     the fix lands (P8d prose-consistency): `server.py:4055` (do-not-touch prod — builder edits this
     render anyway), `render_injection_scaffold.py:112`, `test_mcp_server.py:7941`. The oracle
     over-claim ("the bound is asserted by test_attribution_bound.py") is now false — the class is
     CONTAINED, not pinned-as-a-bound.
- receipt pointers: seam §A · behavioural §C · reach sweep + partition §B/D · fence rework §E ·
  bounds §F · deletion §G · satisfiability §SAT · door-set diff vs scout §DIFF.

---

## WHAT WAS BUILT (deliverables A–G)

All contract tests live in **`loremaster/tests/test_link5_render_containment.py`** (NEW, 45 tests)
except the fence-invariant rework (E) in **`test_task_read_surface.py`** (5 tests) and the deletion (G).

- **§A THE SEAM** — `TestFenceWidthIsTheONEExtractedWidthPolicy` +
  `TestRenderAttributedIsTheInlineContainmentSeam`. Pins `sanitise.fence_width(t) ==
  max(MIN_FENCE_WIDTH, max_backtick_run(t)+1)` by **independent literal** expectation (never by
  calling fence_width — that tautology a mutation could not redden); pins render_fenced and
  render_attributed each consume it (the mutation-sharing legs: perturb fence_width → each consumer's
  exact-width pin reddens). Both symbols reached via lazy accessors so a HEAD run fails BEHAVIOURALLY,
  never as a collection error.
- **§C BEHAVIOURAL DISCRIMINATOR** — `render_attributed -> Rendered` (isinstance pin forces it into
  render.py via the existing mint pin); a hostile footer/row-shaped fixture with newlines + TWO
  backtick runs renders NEUTRALISED; delimiter strictly longer than any inner run; empty/whitespace →
  neutral empty span. The **containment predicate** `_prose_outside_delimiters` strips BOTH block
  fences and inline backtick spans, and has its OWN positive/negative controls
  (`TestTheContainmentPredicateItselfDiscriminates`): it strips a render_fenced/render_attributed
  output and does NOT strip a bare/repr one.
- **§B/D REACH SWEEP + DERIVED PARTITION** — the property-to-invent core.
  - `TestEveryRenderLayerDoorNeutralisesAForgery`: 10 render-layer doors (task_rows / task_detail /
    claim_result / task_transition / finding_rows / finding_detail / finding_transition /
    recalled_memory / comms_fleet_row / served_error), each driven with the forgery → asserted
    NEUTRALISED; each with a BENIGN discrimination control. Pass-iff-ALL.
  - `TestThePositiveControlProvesTheSweepCanFail`: a repr door and a bare-f-string door MUST be
    detected leaking (for the forgery reason) — the sweep can fail.
  - `TestTheDerivedPartitionHasNoDoor`: the **reach-as-a-checked-variable** instrument. The free-text
    universe is DERIVED name-blind from `await mcp.list_tools()` inputSchema (measured live:
    ~50 string params across 15 tools). Every member is EITHER charset-gated (Link 1b, derived from
    `_validate_comms_identities`'s SIGNATURE) OR classified into a containment class a driver
    neutralises. A member in NEITHER is a door named `(tool, param)` → RED. Reverse leg guards stale
    classifications; a third leg guards that every assigned class has a driver.
- **§E FENCE INVARIANT REWORK** (`test_task_read_surface.py`) — `TestEveryFenceSiteInProduction…`
  reworked to TWO DERIVED homes (width-policy = module defining `fence_width`; construction = module
  defining `render_fenced`), read off the functions themselves. Retired the dated `search.py`/`04b-3`
  exemption + self-destruct pin; `test_search_py_is_RETIRED_as_a_distinct_fence_site` replaces it
  (RED until the full route-through lands). Added `TestSearchOutputFenceBytesArePinned…`: an AFTER
  byte pin on `render_fenced` (search routes through it, so its bytes ARE search's) + a BEFORE
  characterisation that search's current private width already equals the shared formula (so the
  route-through is byte-preserving — the STOP-and-flag did NOT trigger), which SKIPS once `_fence_width`
  is retired.
- **§F B-5 BOUNDS** — `TestTheLink5BoundsArePinnedWithTheirReOpenTriggers`: config values OUT
  (trigger: a served render embeds a config string) · indexed-source CONTENT held as a fenced body
  only (trigger: source text rendered outside a fence) · older-schema rows held by RENDER-containment
  NOT charset-gating (trigger: a migration proves all rows gated, or such a value renders outside
  render_attributed). Each #137/#138 PIN-THE-MISS with its named trigger.
- **§G RETIREMENT** — `test_attribution_bound.py` DELETED (its own re-open trigger was "the 04b5
  link-5 slice"; a RED there means the slice landed). Its `_DOORS` hand-list was NOT ported — the
  derived partition supersedes it.

---

## RECEIPTS

### RED at HEAD (`5cedb38`) — behavioural, never a collection error
```
pytest tests/test_link5_render_containment.py \
  tests/test_task_read_surface.py::TestEveryFenceSiteInProductionResolvesToTheONEImplementation \
  tests/test_task_read_surface.py::TestSearchOutputFenceBytesArePinnedAcrossTheRouteThrough -n auto
=> 25 failed, 25 passed          (all 25 failures are AssertionError = feature absent / door leaks)
pytest ... --collect-only => 45 tests collected in 0.21s   (clean; no import error)
```
The 25 RED = §A (7) + §C (4) + §B/D render-layer sweep (10) + §F older-rows (1) + §E fence rework (3).
The 25 GREEN = predicate controls (4) + positive controls (2) + benign controls (10) + partition (4) +
config/indexed-source bounds (2) + render_fenced-consumes + the two byte characterisation pins (3).

### Mypy — ZERO NEW errors (both files)
```
MYPYPATH=tests uv run mypy tests/test_link5_render_containment.py  => Success: no issues found
MYPYPATH=tests uv run mypy tests/test_task_read_surface.py         => Success: no issues found
```
(A bare `uv run mypy <file>` shows a spurious `test_mcp_server` import-not-found — a scoped-run
artifact that resolves in-context, exactly as the existing forwarding tests import it.)

### §SAT — SATISFIABILITY (I attacked my own design)
Reference build in a `scratch_copy.sh` copy (**provenance receipt: `loremaster.__file__ =
/tmp/lore-04b5-ref/loremaster/loremaster/__init__.py`** — INSIDE the scratch, #140-clean):
```
pytest <the full contract> -n auto  =>  49 passed, 1 skipped, 0 failed
```
The 1 skip is `test_search_current_private_width…` (correctly skipped: `SearchPipeline._fence_width`
was retired). **Harder leg (orphaned-import cleanup):** the reshape orphaned render.py's
`MIN_FENCE_WIDTH`/`max_backtick_run` imports; I deleted them, and `ruff check --select F401,F811,F821`
on the reshaped files (render/sanitise/search/store_read) = **All checks passed** — 0-failed survives
the lint the reshape demands. The contract does NOT trap the builder (no C-DEF pin RED on a correct build).

The reference build = extract `sanitise.fence_width`; render_fenced consumes it; add
`render.render_attributed`; route search.py's whole fence construction through `render_fenced` (delete
`_fence_width`); route the driven doors (task/finding renders → render_attributed, memory.text →
render_fenced, `StoreReadTool._not_found_error` → render_attributed); drop orphaned imports. It found
one wrong build my contract correctly rejected: a fenced body prefixed with `- ` (list marker on the
fence-open line) is NOT clean containment — the contract flagged it, I fixed the build. Reproduction
script: `/tmp/lore-04b5-ref/apply_ref_build.py` (scratch — disposable by design; the mechanical edit
list is above). Core seam it adds:
```python
# sanitise.py
def fence_width(text: str) -> int:
    return max(MIN_FENCE_WIDTH, max_backtick_run(text) + 1)
# render.py
def render_attributed(value: str) -> Rendered:
    sanitised = sanitise_line(value)
    if not sanitised:
        return Rendered(FENCE_CHAR + FENCE_CHAR)          # neutral empty inline span
    delimiter = FENCE_CHAR * fence_width(sanitised)
    return Rendered(f"{delimiter}{sanitised}{delimiter}")  # strictly longer than any inner run
```

### §DIFF — derived door set vs the scout's inventory
The scout's six-door hand-list and its §2/§5 tables are a strict SUBSET of my derived partition
(~50 string params). Reconciliation, no door omitted:
- code-RAG family (scout §6.2 / §5): IN as `served_error` (`qualified_name`/`target`/`path`/`tier`/
  `query`/`focus`/`caller_model`/`expected_*`).
- `memory.text` (scout §6.3, "fully bare"): IN as `body` (→ render_fenced per the lead ruling); driven.
- bare `actor` fields (scout §6.4): IN as `attribution`; driven (task/finding transition).
- `thread`/`refs`/`note`: IN as `attribution` (comms). `note` driven via fleet row; thread/refs are
  the send/drain SITE residual (decisions-needed #1).
The partition ADDS what the scout couldn't hand-enumerate: every registered free-text param, checked
live — so a NEW tool/param reddens the partition until classified. That is the whole point of deriving.

---

## SCOPE / FLAGS (nothing silently narrowed)
- No NEW spec ambiguity found: the scout's three tensions were already settled by the 2026-08-05
  operator rulings (FULL door scope, full fence route-through, memory.text → render_fenced). I executed
  those, did not re-open them.
- The STOP-and-flag on a search route-through byte change did NOT fire: search's current private width
  equals the shared formula (pinned), so the route-through preserves bytes.
- Working tree (for the lead to commit): `A loremaster/tests/test_link5_render_containment.py`,
  `M loremaster/tests/test_task_read_surface.py`, `D loremaster/tests/test_attribution_bound.py`,
  `A REPORT-contract-04b5-1.md`. No git state mutated by me.
- Scratch tree at `/tmp/lore-04b5-ref` (a `scratch_copy.sh` copy, NOT a git worktree) — disposable;
  safe to `rm -rf`. Flagging per the don't-abandon-a-worktree habit even though it is not one.
