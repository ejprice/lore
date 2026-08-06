# Packet 04b5 — INJECTION: #321 Link-5 render-site containment

**Minted 2026-08-04** by Fable's 04b-3 decomposition (design sidecar
`receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md` §A). Wave C.
Roster law: **property-to-invent — its own author attacks its own design.**
Order: **contract → adversary → build → cold audit** (Opus end to end).

> This file records SCOPE + the operator rulings. The RULED DESIGN is
> `receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md` **§B**
> (rulings B-1…B-5) — cited, never re-transcribed. Finding **#321** is the
> defect. `REPORT-scout-04b5-1.md` (archives → `receipts/2026-08-05-packet04b5/`)
> is the terrain inventory the contract author consumes.

## THE DEFECT (#321, a MEASURED prompt-injection class)
A caller-supplied FREE-TEXT value (owner/actor/created_by/subject/description/
summary/note/thread/refs/… and a caller `task_id`/`qualified_name`/`target`/
`path` through `!r` teaching errors) reaches another agent's served answer
**OUTSIDE any provenance delimiter**, so it reads as lore's own voice — an
INSTRUCTION agents obey, not a row they misread. The existing injection oracle
(`assert_render_injection_safe`) checks control-chars + row-shape only; it is
**BLIND to same-line instruction forgery**, and its docstring read as
completeness (false). Reachable across principals on the dnd instance
(player-reachable `lore_findings`), so the full fix is a **HARD PRECONDITION of
packet 56 go-live**.

## THE FIX (RULED, §B) — ONE indivisible, ALL-OR-NOTHING slice
Partial containment is **WORSE than none**: the delimiter becomes a trust signal
the consumer applies to every bare render, manufacturing a false clear on each
skipped surface. Therefore the sweep gate is **pass-iff-ALL**, never per-surface,
and this packet **cannot be split** even though it exceeds the ≤0.25 sizing
target — the all-or-nothing law is the harder law (sidecar §A).

- **B-1 THE PARTITION (derived, at the RENDER SITE):** every caller-origin string
  reaching a served answer is EITHER charset-gated at write (Link 1b) OR
  render-contained at read; a member in neither is a **door named `file:line`**.
  Render-containment is the **DEFAULT for all stored free text** (charset-gating
  exempts only fresh-in-call-never-persisted echoes). Derived as the complement
  of the Link-0 scan over the **registered `inputSchema` universe** — NOT a
  hand-list (the six-door list in #321's body is already a strict subset; counts
  in #321 are STALE — re-derive).
- **B-2 THE SEAM (extract before you compose):** step 0 = **EXTRACT**
  `sanitise.fence_width(text) -> int` = `max(MIN_FENCE_WIDTH, max_backtick_run(text)+1)`
  from `render_fenced`'s inline expression (`sanitise.fence_width` does NOT exist
  today — verified `not_found` @HEAD). `render_fenced` becomes its first consumer.
  Then a NEW inline primitive `render.render_attributed(value) -> Rendered`:
  `sanitise_line(value)` → wrap in an inline backtick delimiter of width
  `fence_width` → return `Rendered`. Do NOT clone the `max(...)`; **prove sharing
  by MUTATION** (perturb `fence_width`; ALL consumers' declared-RED pins redden).
  NOT bare `sanitise_line` (control-char only); NOT `render_fenced` (destroys
  inline rows). Errors route through the seam, **never `!r`**. Multi-line bodies
  (task.description / finding.body / message body / brief body / **memory.text**)
  → `render_fenced`; single-line attribution/id values → `render_attributed`.
- **B-3 THE OUTPUT-HALF SWEEP (RUNTIME):** `Rendered` subclasses `str`, so every
  static gate is blind to a demotion. **Reach is a CHECKED variable** —
  AST-enumerate every served-answer call site embedding a caller-origin byte; the
  runtime instrument asserts EACH was OBSERVED (an unobserved site is a named gap,
  not a silent pass — the six-defeats lesson). **Positive controls:** a
  `repr`/bare-f-string reference build MUST make the sweep FAIL, for the
  repr/forgery reason (not a parse error). Pass-iff-ALL.
- **B-4 THE DISCRIMINATING PIN IS BEHAVIOURAL:** a hostile fixture
  (footer/row-shaped forgery + newlines + backtick runs) must render NEUTRALISED
  in the served bytes; a bare-f-string build serves the forgery verbatim ⇒ RED.
  isinstance-on-return + mutation proof. Empty/whitespace value → empty inline
  span, pinned NEUTRAL.
- **B-5 BOUNDS + re-open triggers (name every one):** IN =
  registered-tool-parameter values reaching a served answer (fresh echoes AND
  reads of stored free text). OUT, each PIN-THE-MISS'd with its trigger: config
  values (trigger: a served render embeds a config string) · **indexed-source
  CONTENT** — the served source bytes, distinct from the caller PARAM (trigger: a
  served render embeds indexed source text outside a fence) · **older-schema
  stored rows written before Link 1b** (trigger: a migration proves all rows
  gated, OR a served surface renders such a value outside `render_attributed`).

## OPERATOR RULINGS (2026-08-05, batched checkpoint — lead-04b5)
The discovery scout surfaced three tensions with §B's premises; two were scope
forks put to the operator.

1. **DOOR SCOPE → FULL derived partition.** 04b5 contains ALL registered-tool
   served free-text params — comms/tasks/findings/memory **AND the code-RAG tool
   family** (`symbols`/`impact`/`store_read`/`read_file`/`map`/`diff`/`search`:
   `qualified_name`/`target`/`path`/`query` reflected into `!r` served errors,
   same forgery class as `task_id!r`). Honors B-1's derivation + B-5's in-scope
   definition; the all-or-nothing trust property means a single bare code-RAG door
   is a false-clear on the whole surface. (Stakes note: cross-principal SHARED
   surfaces — findings/memory/task attribution — are the high-stakes vector;
   per-caller `!r` self-echoes are lower-stakes but IN by the derivation.)
2. **FENCE UNIFY → Full route-through.** `sanitise.fence_width` is extracted
   (§B-2). `search.py`'s THIRD private width clone (`_fence_width`, under the
   OVERDUE `EXPIRES "04b-3"` exemption) is killed AND search.py's **entire fence
   construction routes through the shared render seam**, fully retiring search.py
   as a distinct fence site → the ONE-IMPLEMENTATION fence invariant
   (`test_task_read_surface.py::TestEveryFenceSiteInProductionResolvesToTheONEImplementation`)
   returns to a single construction home (render.py). **New search-output byte
   pins required** (search.py's fence format may differ from `render_fenced` —
   pin the before/after so the reshape is a KNOWN, not silent, output change). The
   invariant's pins are the OLD world's certification — **update them in the SAME
   diff** (P8d contract-first / rename-sweep law).
3. **LITERAL ALL-OR-NOTHING → the bare-`ValueError` SELF-ECHO doors are ROUTED**
   (2026-08-05, operator; closer-04b5-selfecho-1, thread `q:selfecho-enforce`).
   Ruling 1 declared the per-caller `!r` self-echoes IN by the derivation but "lower-
   stakes"; this ruling makes the containment UNIFORM. These self-echo a malformed
   caller param back to the SAME caller (NONE cross-principal): comms
   action/kind/set_status, memory kind, findings action, rollup `since`, plus the four
   code-RAG-tool boundary errors read_file `tier`/`path`, map `changed_since`/`focus`,
   reindex `tier`. **B-5 bound (formerly: "a served bare `ValueError` is wholesale OUT of
   type scope") is NARROWED**: it now covers only the genuinely-non-caller bare
   `ValueError` cases the name-blind classification cannot tell apart from a real door —
   chunker-registration `owner`, ext-tool `param.kind.description`, config `self.tier`,
   symbols `self.status`, and `tasks._validate_done_summary` closed-vocab `target`
   (validated by `_validate_transition` first — a spurious collision with lore_impact's
   free-text `target`), plus the infra `SurrealStoreError` `tier` (a corrupt-row error on
   a resolved, closed-vocab tier). Enforcement is TWO-CLASS:
   (a) the four CUSTOM caller-boundary error classes were added to the error-half scan's
   base set (7→11 in `test_link5_render_containment.py::_served_error_bases`) — a REDDENING
   scan, so a future un-routed door of those classes reddens; (b) bare `ValueError` is
   OVERLOADED with internal invariants, so a name-blind reddening scan over it is UNSOUND
   (the `target` closed-vocab collision has no syntactic tell). Per the operator's "not
   worth P-F/P-S machinery for a lower-stakes self-echo" it takes the sanctioned BOUNDED
   PIN-THE-MISS: every site ROUTED + behaviourally pinned (`TestBareValueErrorSelfEchoes
   AreContained`, forgery→neutralised, mutation-proven) + a NAMED re-open trigger (a new
   served bare `ValueError` reprfing a caller free-text param must be routed — the
   behavioural pin does NOT auto-detect a new site). Receipt: `REPORT-closer-04b5-
   selfecho-1.md`.
4. **`.format()` REACH BLIND SPOT → CLOSED (widen the instruments).** (2026-08-05, operator;
   closer-04b5-format-1.) The reach instruments detected interpolation via `ast.FormattedValue`
   (f-strings) ONLY and were **BLIND to `str.format()` renders** — a completeness gap that let a
   LIVE un-contained caller-byte self-echo door slip the recheck + cold audit:
   `server.py::_caller_model_note` served `_CALLER_MODEL_NO_RATIO_TEMPLATE.format(model=caller_model)`
   (a registered served_error-class param) OUTSIDE any delimiter. **BOTH instruments are now
   `.format()`-aware:** the error-half (`_served_error_door_sites` via extracted `_expr_door` +
   new `_format_call_door`/`_message_expr_doors`, door_vocab-filtered) and the render-half P-U
   (`_method_interpolates_a_nonconstant` gains a `.format(non-constant)` leg — so a `.format()`-only
   AppContext render joins the candidate universe). The two caller-param `.format()` doors are
   ROUTED through `render_attributed`: `_caller_model_note` (`caller_model`; now DRIVEN +
   branch-covered under P-S) and `map.py:487` `_CHANGED_SINCE_SUMMARY_TEMPLATE` (`changed_since`;
   closed-vocab-safe today — a bogus id raises `MapChangedSinceError` upstream — routed for UNIFORM
   containment, defence-in-depth). **B-5 UPDATE:** the reach-instrument completeness bound now
   covers `.format()` interpolation, not only f-strings — the class the D2/recheck/cold-audit
   sequence left open is closed. Every OTHER `.format()` site (24 total, re-derived) is
   int/float/indexed-source-content (B-5 OUT — `read_file`/`store_read` `_SOURCE_HEADER_TEMPLATE`,
   `impact`/`search` file renders)/closed-vocab (`detail_level` Literal)/system/the `render.py:227`
   seam-internal. Finding #335. Receipt: `REPORT-closer-04b5-format-1.md`.

### Lead rulings (within the ruled design + repo law; contract author executes)
- **`_render_recalled_memories` (scout §6.3):** `memory.text` renders fully bare
  (not even sanitised). IN scope by B-1 (stored free text → served answer);
  contain via `render_fenced` (body-like/multi-line). Not a fork.
- **The invariant rework is contract-first + mutation-proven:** the shared thing
  is the WIDTH POLICY (`sanitise.fence_width`); prove sharing by mutation across
  EVERY consumer (render_fenced, render_attributed, search.py).
- **`test_attribution_bound.py` retires WITH the fix** — its own re-open trigger
  (verbatim) is "the 04b5 link-5 slice"; a RED there means the slice landed →
  delete the file and SAY SO in the wave report. Its `_DOORS` is a self-labelled
  HAND LIST, never the derived inventory.
- **STOP-and-flag** if the full route-through proves search.py's fence format
  genuinely cannot match the shared seam without a served-behaviour change the
  operator did not price — escalate, never silently keep a private copy.

## DEPLOY POSTURE
**Commit-only this session, rides 05a's deploy** (sidecar §A-deploy). MUST land +
deploy **before packet 56 go-live** (the re-open trigger fires there). No image
build this session ⇒ the root need not be cleared of `REPORT-*.md` until archive.

## ENTRY-CHECK RECEIPTS (ground-truthed @HEAD 5cedb38 by lead-04b5)
- `sanitise.fence_width` = not_found · `render.render_attributed` = not_found.
- `render_fenced`@`render.py:230` inlines `FENCE_CHAR * max(MIN_FENCE_WIDTH,
  max_backtick_run(body)+1)`; `sanitise_line`@`sanitise.py:77`→`SafeLine`;
  `Rendered(str)`@`render.py:96` (AST mint-pin `TestSafeLineRenderedMintPin`).
- `sanitise.py` owns `FENCE_CHAR`/`MIN_FENCE_WIDTH`/`max_backtick_run`; `render.py`
  imports them.
- **STALE COUNTS re-derived:** #321 said "8 `task_id!r` / 154 `!r`"; @HEAD it is
  **19 `task_id!r` in tasks.py / 291 `!r}` pkg-wide**. The growth reinforces the
  derivation-based design; contract + build RE-DERIVE, never inherit a count.
- Branch is pre-existing RED (191 mypy + 316 pytest, ALL auth WIP pkt 39/45/48/49,
  #333, operator-accepted). 04b5 must add **ZERO NEW** to either.

## RENDER-REACH DESIGN (round-3, 2026-08-05) — the two-waves escalation
The contract went to a Fable cold audit (operator-directed) then a fix, then a Fable
delta-audit. History:
- **Round-1 cold audit INSUFFICIENT** (`REPORT-coldaudit-contract-04b5-1.md`, R1–R7): the
  per-SITE reach was absent (a build leaving the 19 `task_id!r` sites bare passed green);
  the partition universe was string-type-only (missed `refs`/`to`/`labels`/`blocked_by`).
- **Fix** (`REPORT-contract-04b5-2.md`): closed the ERROR half with a name-blind AST reach
  scan over served domain-error constructions (49 doors/7 modules) + the array universe.
- **Round-2 delta-audit INSUFFICIENT** (`REPORT-coldaudit-04b5-4.md`, D1/D2): ERROR half
  CONFIRMED sound; RENDER half is the blocker — **byte-proven** that two EXISTING un-driven
  production renders (`_render_transitive_blockers` `server.py:4121`,
  `_render_supersede_result` `server.py:4160`) leak a caller forgery outside any delimiter.
  Root: render reach is NOT a checked variable (a driven registry, no `_render_*` universe
  enumeration). **2nd INSUFFICIENT on reach-as-checked-variable → the two-waves tripwire
  fired → operator ruled a DESIGN SIDECAR first.**

**The ruled instrument** (`REPORT-design-sidecar-04b5-1.md` §4 — build to its pins). Render
half = 3 COUPLED CHECKED VARIABLES over a RUNTIME over-drive:
- **P-U** name-blind candidate universe derived by the **INTERPOLATION property**, NOT the
  `_render_` prefix — the prefix is itself a six-defeats name-list (measured: it misses
  serving helpers `_comms_traffic_line`/`_format_finding_ref`/…).
- **P-F** model-guarded field manifest (a `.model_fields` read; a NEW str field → RED).
- **P-S** branch/site observation — a caller-byte door in an un-exercised branch reddens
  (D1's own leak lives in exactly such a branch).
- Containment PROOF is RUNTIME `_leaks` (byte-diff), **never structural** — structural is
  unsound BOTH ways (measured §P1: over-flags ~40×, and mis-keys doors vs non-doors).
- Plus the 2 D1 drivers, the OUT-set machine-verified (P-C), and a partition-coherence pin
  with the error half (every served caller byte in exactly one of {error construction,
  render site, named B-5 bound}).

### OPERATOR RULINGS (2026-08-05, batch 2)
1. **Branch coverage = MECHANIZE with `coverage.py` (INSTALLED).** Operator authorized the
   install over the stdlib `sys.settrace` hand-roll (packages-over-hand-rolling). `coverage.py`
   is a **dev/test-only dependency** (root `[dependency-groups] dev`), **NOT an image dep**;
   it ships `py.typed` so no mypy override is needed. It proves an over-drive driver EXERCISED
   every branch of a render method, so a door cannot hide in an un-run branch.
2. **code-RAG file renders (map/diff/impact `_render_*`/`_format_*`) = B-5 indexed-source-
   content OUT for 04b5.** They echo INDEXED content (symbol names, `tier:file_path`) via
   `_sanitise_line`, not caller PARAMS. The OUT entry MUST state the residual explicitly:
   `_sanitise_line` is same-line-forgery-blind, so attacker-controlled indexed content is a
   LIVE surface owned by the **#138 / packet-39** threat-model review — met deliberately, not
   silently.

The third contract build lands the render-reach instrument to the sidecar §4 pins with
`coverage.py`; it PRESERVES the error-half scan + the closed R2/R4/R5; the R3 ripple (6
`test_task_ledger::TestDoneSummaryReportPath` exact-text pins) is a BUILDER update (P8d).
