# REPORT-contract-04b5-2 — Packet 04b5 Link-5 render-site injection containment: the REVISED RED contract (cold-audit INSUFFICIENT fix)

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (tool honesty, first)
Brief satisfiable with the tools granted. lore tools loaded first try (`ToolSearch "+lore"`,
no #334 flake). `scratch_copy.sh` present and worked (provenance-asserting). spike-surreal
`:18000` reachable for the store-backed R3 suites (never touched `:18500`). lore-first for
the production symbols under the drivers (`lore_get_symbol` on `StoreReadTool._not_found_error`;
`lore_index` for currency — watched `/workspace`@`4c5930d`, my session had not edited when I
started). **grep is the honest tool** for the `!r`-population re-derivation and the
`test_attribution_bound` prose sweep — used there and said so per hit. **AST live-probes**
(pasted below, §R1) are the honest instrument for validating the derived door set against the
real tree BEFORE writing the scan. No lore weakness forced a route-around; nothing filed.

## SUMMARY BLOCK
- state: **done** — contract REVISED, RED-at-HEAD behaviourally, satisfiability proven on a
  reference build, the R1 litmus reddens (discrimination shown), R2–R7 closed or flagged.
- deviations:
  - The RENDER half stays a DRIVEN registry + a named bound, NOT an AST-derived reach net —
    **because a name-blind render-reach derivation is UNSOUND, measured (§R1b receipt)**: the
    sanitise-vocab property MISSES the bare-f-string doors (task/finding transition actor,
    memory.text) AND over-flags ~10 system renders. The ERROR half IS a sound derived AST
    site scan. This asymmetry is deliberate and pinned.
  - §SAT reference build required WIDENING `render_line` to accept `Rendered` values (it
    rejects non-`SafeLine`) — a genuine BUILD-DESIGN point surfaced for the builder (§SAT),
    not a contract change. `render_join` needed no change (it accepts control-char-free str).
- **Packages considered: none — the seam is stdlib `ast`/`re`/string over the repo's own
  `sanitise`/`render` primitives, which I read (`render_line` value check `render.py:211`,
  `render_join` `render.py:290`, `render_fenced` `render.py:230`) and did not re-mechanise.**
- Graded: `4c5930d` (HEAD; the tree I authored against — production surfaces byte-identical to
  contract-04b5-1's base) · HEAD-at-report: `4c5930d` · **SAME**. All "RED at HEAD" claims are
  against `4c5930d`; a reader after the build must re-derive.
- **DECISIONS-NEEDED (surfaced, not silently resolved):**
  1. **R3 RIPPLE — 6 pre-existing pins in `test_task_ledger.py::TestDoneSummaryReportPath`
     WILL go RED on the fix** (they assert exact error text `task '{id}'`; the fix contains
     `task ` + `` `{id}` ``). This is the P8d old-world certification. The BUILDER must update
     them in the SAME diff. NOT a contract defect; NOT blocking. Full detail + the exact
     transformation in §R3. Every OTHER door-module suite passes (2617 passed).
  2. **R6 (charset-gated half derives from the seam SIGNATURE, not its BODY)** — accepted as a
     residual, NOT cheap to close (needs body-AST proof each signature param is actually
     gated). Reasoning + the reason it is sound in §R6. Flagging per scope law.
- receipt pointers: R1 error-scan §R1 (+ live AST receipts) · render-reach unsoundness §R1b ·
  R2 array universe §R2 · R3 seam-suite ripple §R3 · R4 rename §R4 · R5 prose sweep §R5 ·
  R6/R7 §R6 · satisfiability §SAT · litmus discrimination §LITMUS · named bounds §BOUNDS.

---

## §R1 — THE PER-SITE REACH INSTRUMENT (the property-to-invent core; INSUFFICIENT → CLOSED)

The fix is a NEW class `TestNoServedDomainErrorLeavesACallerParamUncontained` plus supporting
module-level helpers, mirroring the fence-site AST scan template
(`test_task_read_surface.py::TestEveryFenceSiteInProductionResolvesToTheONEImplementation`).

**The instrument, stated as the question an agent asks:** *"Does any construction of a served
DOMAIN error interpolate a caller free-text param OUTSIDE the containment seam?"* Derived
name-blind by AST over a PROPERTY:
- **Scope = constructions of a served-error CLASS** — derived by `issubclass` off the seven
  domain-error bases (`TaskLedgerError`/`FindingLedgerError`/`AgentRegistryError`/
  `MessageLedgerError`/`StoreReadError`/`GetSymbolError`/`ImpactTargetNotFoundError`). This
  type-scoping is what keeps the scan OFF config/infra `{tier!r}` (raised as bare
  `ValueError`/`RuntimeError`), so the fix is never trapped into wrapping server-controlled
  values (#133). A new domain error subclassing any base joins the population automatically.
- **Door = a `FormattedValue` whose identifier is a registered free-text param** (string OR
  array-of-string, MINUS the charset-gated identities), and whose value is NOT the containment
  seam. Both interpolation shapes are covered: INLINE (`f"...{task_id!r}"`) and BUILD-THEN-RAISE
  (`message = f"...{target!r}"; message += ...; raise ImpactTargetNotFoundError(message)` —
  impact.py, which an inline-only scan MISSES).
- **SAFE = only** `render_attributed`/`render_fenced`/`render_line`/`render_join`/`render_compose`
  (the seam) or an int-returning builtin (`len`/…). `sanitise_line(task_id)` is a DOOR
  (control-char only, NOT containment — the exact #321 blindness); `{len(summary)}` is NOT
  (a count, not a forgery carrier).

**Why this is byte-sound despite the demotion hazard:** `f"...{render_attributed(x)}"`
re-demotes the `Rendered` to `str` but the DELIMITER BYTES are already in the output, so the
forgery is contained — I proved this with the reference build (§SAT). The AST proves every site
ROUTES through the seam; §A/§C prove at RUNTIME the seam NEUTRALISES; together they are
byte-sound for the direct-interpolation shape. The error sites are AST (not runtime-driven)
because a `TaskNotFoundError(f"...{task_id!r}")` bakes the forgery in AT CONSTRUCTION and
propagates as `str(error)` — there is no single catch point to re-contain, and driving all 19+
sites needs store state; the AST scan is site-complete where runtime driving is intractable.

**RED at HEAD (`4c5930d`) — the DERIVED door set, measured by the scan itself (47 unique
sites, ~50 FormattedValues):** `tasks.py` task_id×19 + target; `store_read.py` path×3/tier×3;
`symbols.py` qualified_name×4; `impact.py` target×4 (build-then-raise); `findings.py` (target,
id_or_number); `agents.py` (role, spawned_by incl. `existing.role`/`existing.spawned_by`
attribute forms); `messages.py` grade. The main door assertion is RED at HEAD; its guards
(non-vacuity, seven-base drift, positive control) are GREEN.

**Live AST receipts (the instrument I built to validate the scan BEFORE writing it — pasted so
re-runnable; run against `4c5930d`):** the derivation confirmed ZERO over-reach (no config/infra
site flagged), `len(summary)`/`sorted(TASK_STATUSES)`/`current`/`fresh_status` correctly NOT
flagged, and the full 47-site door set. The scan logic in the contract IS that receipt,
promoted from probe to committed test (`_served_error_door_sites` / `_formatted_value_door`).

**The Fable litmus fires RED and the correct build GREEN (§LITMUS).**

### §R1b — why the RENDER half is a driven registry, not an AST reach net (MEASURED)
I attempted a name-blind render-reach derivation and it is UNSOUND in both directions
(receipt: an AST scan keyed on the sanitise/containment vocab
`{sanitise_line,safe_str,render_fenced,render_attributed}` over `server.py`'s `_render_*`):
- **MISSES** the bare-f-string doors — `_render_task_transition`/`_render_finding_transition`
  actor and `_render_recalled_memories` text carry NONE of that vocab (they are the raw doors
  #321 names), landing in the "exempt" bucket.
- **OVER-FLAGS** ~10 system renders (`_render_age`, brief-version metadata) that carry no
  caller byte.
So renders use `_RENDER_DRIVERS` (a CHECKED registry: `TestTheRenderDriverRegistryCoversTheRenderDoors`
verifies each key is a real AppContext method and the litmus render sites are driven) with its
bound NAMED (a new render door not added is invisible; re-open trigger stated). The error half
IS soundly derivable, so it gets the AST scan. The asymmetry is the honest call, pinned in-file.

---

## §R2 — THE ARRAY-OF-STRING UNIVERSE HOLE (INSUFFICIENT → CLOSED)
`_registered_string_params` filtered on `"string" in types` only, so `refs`/`to`/`labels`/
`blocked_by` were structurally invisible. Fixed via `_schema_carries_string` (inspects
`items.type` and `anyOf[].items.type` — the two shapes pydantic emits for `list[str]` /
`list[str] | None`). Live universe now: 41 string + 4 array-of-string params. Classified:
- `to` → `_CHARSET_GATED` (a recipient IS an agent name; the seam gates it — signature check
  updated to include it).
- `refs`, `blocked_by` → `_PARAM_CLASS` "attribution" — DRIVEN: `refs` via
  `_drive_comms_drain_row` (refs=[FORGERY], the confirmed bare drain-row door), `blocked_by`
  via `_drive_task_rows` (blocked_by=[FORGERY] — arbitrary `list[str]`, no charset gate, so a
  real door; leaks the list-repr at HEAD, contained per-element on the fix).
- `labels` → `_NOT_SERVED_OUT` (a recall/memory FILTER, never rendered as free text — asserted,
  with re-open trigger; this is the B-5 config-shaped bound, not a class).

**§DIFF CORRECTION (cold audit R2):** contract-04b5-1's report claimed *"refs IN as
attribution"* — **FALSE at that time**: `refs` was in NEITHER the universe NOR `_PARAM_CLASS`.
It is now correctly IN (universe via the array fix, class attribution, driven).

---

## §R3 — SATISFIABILITY RECEIPT RUN THE PRE-EXISTING SEAM SUITES (#133 — the audit's demand)
I built a KNOWN-CORRECT reference impl in a `scratch_copy.sh` copy (provenance receipt:
`loremaster.__file__ = /tmp/lore-04b5-ref2/loremaster/loremaster/__init__.py`, INSIDE the
scratch — #140-clean) and ran the pre-existing suites the reshape touches. **Complete
counts (parallel `-n auto`, against the reference build):**
- `test_render_seam_pins.py` (incl. `TestSafeLineRenderedMintPin`) · `test_mcp_server.py::
  TestRenderInjectionRegistry` · `test_comms_tool.py` (RenderCase registry) · `test_findings.py`
  · `test_task_read_surface.py` (incl. the reworked fence invariant) · `test_task_ledger.py`
  → **1755 passed, 1 skipped, 6 FAILED**.
- `test_symbols.py` · `test_impact.py` · `test_store_read.py` · `test_agent_registry.py` ·
  `test_message_ledger.py` · `test_comms_footer.py` · `test_comms_render_architecture.py`
  → **868 passed, 14 skipped, 0 failed**.

**THE 6 FAILURES ARE THE P8d OLD-WORLD RIPPLE, ALL IN `test_task_ledger.py::
TestDoneSummaryReportPath`** (`test_multiline_summary_is_refused_with_the_exact_text`,
`test_over_cap_summary_is_refused_naming_the_actual_length`, `test_multiline_report_path_is_refused`,
`test_summary_on_a_non_done_target_is_a_value_error`, `test_done_without_summary_is_refused_with_the_exact_text`,
+1). They assert the EXACT error text with `{task_id!r}` as `task 'c830…'`; the fix contains it
as `task ` + `` ```c830…``` ``, so the exact-string assertion breaks. **This is the P8d dual
("tests written before a semantic change certify the OLD world"): the BUILDER updates these six
in the SAME diff as the fix** (replace the `task '{id}'` expectation with the contained form).
Every not-found / transition / findings / symbols / impact / store_read / agents / messages pin
SURVIVES because it asserts substring containment (`id in str(error)` — the id stays a substring
inside the delimiter). **This ripple is exactly what R3 exists to surface, and contract-04b5-1's
§SAT missed it by running only its 50 new tests.**

---

## §SAT — THE FULL REVISED CONTRACT GOES 0-FAILED ON A CORRECT BUILD (I attacked my own design)
Reference build (mechanical, in the scratch): extract `sanitise.fence_width`; `render_fenced`
consumes it; add `render.render_attributed`; route search.py's entire fence through
`render_fenced` (delete `_fence_width`); wrap all 47 error door sites (`{param!r}` →
`{render_attributed(param)}`, incl. the attribute forms) + import; route the 12 render doors;
**widen `render_line` to accept `Rendered` values** (the build-design point — `render_attributed`
returns `Rendered`, which `render_line` rejects at `render.py:211`; the builder must widen it or
restructure; `render_join` needed no change).

```
pytest tests/test_link5_render_containment.py \
  tests/test_task_read_surface.py::TestEveryFenceSiteInProductionResolvesToTheONEImplementation \
  tests/test_task_read_surface.py::TestSearchOutputFenceBytesArePinnedAcrossTheRouteThrough -n auto
=> 61 passed, 1 skipped, 0 failed        (the skip = test_search_current_private_width…, correct once _fence_width retired)
```
The contract DISCRIMINATED two wrong builds during the ref build: (a) the attribute-form doors
`existing.role`/`existing.spawned_by` (a regex-narrow wrap left them bare → the scan stayed
RED, correctly); (b) a naive `f"- {render_fenced(memory.text)}"` (the fence-open line carries
the `- ` list marker, so it is not a clean fence → the memory driver stayed RED until the body
was fenced on its own lines — the SAME discrimination contract-04b5-1's §SAT reported).

## §LITMUS — the R1 litmus reddens; the correct build greens (DISCRIMINATION PROVEN)
During the reference build, when tasks.py was wrapped but the two agents.py attribute-form
doors were NOT, the error scan stayed **RED naming exactly those two sites** — i.e. a build that
routes SOME task_id sites but leaves ANY door bare goes RED (the all-or-nothing property). At
HEAD (all bare) it is RED across the full 47; on the complete reference build it is GREEN. That
progression IS the litmus: a single bare door fails the whole scan.

---

## §R4 — the width pin's NAME no longer over-claims (MED-LOW → CLOSED)
`test_the_width_rule_is_not_cloned_in_render_attributed` renamed to
`test_render_attributed_delimiter_has_the_fence_width_OUTPUT_shape`; its docstring + failure
message now say it fixes an OUTPUT SHAPE and that non-cloning is proven ONLY by the
mutation-sharing leg (perturb `fence_width` → the shape reddens; a private `max()` clone would
not). No failure message promises a check its assertion does not perform (P2).

## §R5 — stale prose to the deleted `test_attribution_bound.py` swept (LOW → CLOSED)
Bare anchor-free grep found 5 references. Fixed the two editable stale ones:
`tests/render_injection_scaffold.py` (the oracle docstring — now teaches
`test_link5_render_containment.py` as the containment instrument) and
`tests/test_mcp_server.py::TestRenderInjectionRegistry` docstring. Two references are CORRECT
(they describe the deletion/supersession accurately: `test_task_read_surface.py:2967` and my
own `test_link5:17`) — left as-is. **BUILDER NOTE: `loremaster/server.py:4055` is a production
docstring naming `test_attribution_bound.py` (do-not-touch for me) — update it in the fix diff.**

## §R6 / §R7 (LOW / INFO)
- **R6:** `test_the_charset_gated_half` derives `_CHARSET_GATED` from the seam's SIGNATURE
  (`_validate_comms_identities`'s parameters), not its BODY. Accepted residual: it is sound
  because the seam's contract IS "gate every identity param I am given," pinned by the Link-1b
  tests; a body-AST proof each param is actually gated is not cheap and adds little. Named here
  per scope law.
- **R7:** `labels`/array free-text params are covered — `refs`/`blocked_by` by the site drivers
  (R2), `labels` by the `_NOT_SERVED_OUT` bound with its re-open trigger.

## §BOUNDS — the R1 scan's NAMED limitations (PIN-THE-MISS, in the class docstring)
1. A caller value LAUNDERED through a local named outside the registered universe
   (`x = task_id; f"{x!r}"`) is invisible — convention is direct-param interpolation, and the
   `served_error` runtime drive backstops driven sites; re-open trigger stated.
2. A served error NOT subclassing the seven bases is unscanned — guarded by the base-drift pin;
   re-open trigger: a new domain-error base.
3. A served bare `ValueError` (not a domain error) interpolating a caller param is out of the
   type scope — small, covered by render/runtime drives + the partition; re-open trigger stated.

## GATE RECEIPTS (at HEAD `4c5930d`)
```
pytest tests/test_link5_render_containment.py -n auto        => 26 failed, 31 passed  (57 collected)
   all 26 failures are behavioural AssertionError (feature-absent) — 0 TypeError/collection/import
pytest ... --collect-only                                    => 57 tests collected, clean
MYPYPATH=tests mypy tests/test_link5_render_containment.py tests/render_injection_scaffold.py => Success
uv run mypy loremaster  (full member)                        => 0 lines mention the 04b5 files → ZERO NEW
```
Branch is pre-existing RED (auth-WIP #333, operator-accepted); 04b5 adds ZERO NEW to either gate.

## WORKING TREE (for the lead to commit) + SCRATCH
- `M loremaster/tests/test_link5_render_containment.py` (revised contract)
- `M loremaster/tests/render_injection_scaffold.py`, `M loremaster/tests/test_mcp_server.py`
  (R5 prose sweep — docstrings only)
- `M loremaster/tests/test_task_read_surface.py`, `D loremaster/tests/test_attribution_bound.py`
  (unchanged from contract-04b5-1 — the fence rework + deletion the cold audit ruled SOUND)
- Scratch reference build at `/tmp/lore-04b5-ref2` (a `scratch_copy.sh` copy, NOT a worktree) —
  disposable, safe to `rm -rf`. Flagged per the don't-abandon habit; the ref-build edit list is
  above (§SAT), not committed.
