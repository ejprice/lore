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
