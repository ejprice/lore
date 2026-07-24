brief-base v6 read

# REPORT-builder-10d — packet 10-d, weak-match DISARM

## SUMMARY BLOCK
- `brief-base v6 read` · agent `builder-10d` · worktree `/home/ejprice/PycharmProjects/lore-pkt10`, branch `pkt10-floor-calibration-design`
- **state: done-with-deviations** — disarm shipped, sweep complete (391 hits, 0 unruled), 3 commits: `1c33872` (RED pins) → `bdb7929` (disarm) → `1eef197` (smoke check 8)
- **DEVIATION 1:** edited `loremaster/loremaster/server.py` (outside the brief's writable set) — its `CosineFloorStatus` docstring is a **SERVED** surface (measured: it reaches consumers inside `lore_index`'s `outputSchema`) and my change made two of its sentences false. §Deviation 1 carries the exact hunks for a trivial revert.
- **DEVIATION 2:** the packet's "`smoke_p8b` is render-shape-coupled — update in step" **does not hold at this SHA** — zero cosine/weak-match/floor hits in it. Rather than no-op I added the deploy gate the packet's Exit actually names (check 8). §Smoke.
- **decisions-needed:** (1) keep or revert DEVIATION 1; (2) three dormant-machinery observations that are 11-ii's to revive but a dead-code scan may flag first — §Surfaced, items 3–5; (3) one prose residual I chose to flag rather than edit — §Surfaced item 6.
- receipt POINTERS: provenance §Provenance · RED→GREEN §RED→GREEN · 3 mutation proofs §Mutation proofs · full 391-row sweep table §Sweep · gates with counts §Gates · smoke controls §Smoke
- ⚠ **51 mypy errors exist on this branch and are NOT mine** — identical count and identical 3 files at `cbf61ac` (pre-packet) and at `1eef197`. Zero delta. §Gates.

---

## Provenance (repo law: a run whose tree you cannot name is not a run — #24/#139/#140)

```
$ cd /home/ejprice/PycharmProjects/lore-pkt10 && uv run python -c "import loremaster; print(loremaster.__file__)"
/home/ejprice/PycharmProjects/lore-pkt10/loremaster/loremaster/__init__.py
```

Every test run and every mutation proof below was executed in that tree, after
`uv sync --all-packages` (not a plain `uv sync` — #140 mode 3). The path was re-printed
inside the mutation-proof run itself, not only once at setup.

**Tooling honesty (brief-base §4):** lore's index watches the MAIN checkout, not this
worktree (#125), so I used **grep for the entire exhaustiveness sweep** — a sanctioned
fallback, and the correct instrument regardless: the sweep's targets are prose and
string literals, which carry no symbol anchors. lore tools were not used for
orientation either; the packet spec named the seam precisely enough that a graph query
would have added nothing.

---

## What changed

### `loremaster/loremaster/search.py`
1. **`_COSINE_WEAK_MATCH_FLOOR: float | None = None`** — the constant's own designed
   rollback state. This is the whole functional change: it darkens BOTH the per-hit
   weak flag (`SearchPipeline._format_result`'s gate) and the aggregate absence verdict
   (`_cosine_absence_verdict`'s gate) through branches that already existed.
2. **`_COSINE_FLOOR_DISARMED_NOTE`** — new module constant, served by
   `apply_cosine_floor_drift_check`'s `disabled` branch in place of `None`:
   > weak-match confidence surfaces disarmed pending per-instance calibration (findings #83/#176/#179/#180; packets 11-i/11-ii) — per-hit similarity substrate remains served.
3. Prose my change falsified, corrected in step: the constant's own comment block (now
   carries the dated disarm rationale **without deleting** the 2026-07-06/07 measurement
   provenance), `CosineFloorDriftStatus.note`'s "present iff `state == "stale"`" (false —
   `disabled` now carries one too), `_cosine_absence_verdict`'s "the floor is measured
   and set by default" (false), `_format_result`'s "both dark until their gate constant
   is measured on" (the two gates now disagree deliberately), and a dated note on the
   stamp explaining that it now **intentionally disagrees** with the serving constant.

### Untouched, deliberately (Scope OUT — verified by diff, not by intent)
- `_COSINE_WEAK_MATCH_WARNING_TEMPLATE` and `_COSINE_ABSENCE_VERDICT_TEMPLATE` — **byte-identical**. They go dark unchanged; the F3 consult owns wording.
- `_COSINE_WEAK_MATCH_FLOOR_STAMP` — kept with its comment block, `floor=0.50649`, `measured_file_count=214`. Pinned by `test_the_measurement_stamp_survives_the_disarm`.
- `_COSINE_SUBSTRATE_ENABLED = True` — the `sim 0.62` line stays on. Pinned by `test_the_substrate_line_still_renders`.

### Tests
- **New** `test_search.py::TestWeakMatchDisarmedAtTheProductionDefault` (8 pins) and
  `test_mcp_server.py::TestCosineFloorStatusWiring::test_production_default_serves_the_disarm_note_through_lore_index`.
  Both **patch nothing** — that is the point. Every pre-existing cosine class
  monkeypatches its own floor, so a flip of the production constant was invisible to
  the entire suite. These are the only pins that can see it.
- **4 corpse/stale sites repaired** — §Sweep, Table A.
- `docs/eval/smoke_p8b.py` — check 8, §Smoke.

---

## RED→GREEN

**RED**, at `1c33872`, before any production line changed:
```
FAILED test_search.py::TestWeakMatchDisarmedAtTheProductionDefault::test_the_disarm_note_is_not_the_drift_note
FAILED test_search.py::TestWeakMatchDisarmedAtTheProductionDefault::test_the_disabled_state_serves_the_disarm_note_not_a_null
FAILED test_search.py::TestWeakMatchDisarmedAtTheProductionDefault::test_the_disarm_note_admits_the_condition_and_names_the_next_move
FAILED test_search.py::TestWeakMatchDisarmedAtTheProductionDefault::test_the_shipped_floor_is_none
FAILED test_search.py::TestWeakMatchDisarmedAtTheProductionDefault::test_no_per_hit_weak_flag_however_low_the_cosine
FAILED test_search.py::TestWeakMatchDisarmedAtTheProductionDefault::test_no_aggregate_absence_verdict_even_when_every_condition_holds
FAILED test_mcp_server.py::TestCosineFloorStatusWiring::test_production_default_serves_the_disarm_note_through_lore_index
7 failed, 2 passed in 7.61s
```
The 2 that passed at RED are the anti-over-correction controls
(`test_the_substrate_line_still_renders`, `test_the_measurement_stamp_survives_the_disarm`) —
correct: they pin what must **not** change, so they were green before and after.

**GREEN**, at `bdb7929`:
```
$ uv run pytest -n auto -q test_search.py::TestWeakMatchDisarmedAtTheProductionDefault \
                          test_mcp_server.py::TestCosineFloorStatusWiring
14 passed in 8.62s
```

---

## Mutation proofs (a pin you cannot demonstrate failing is not a pin)

Method: mutated the **real** tree with a `cp -a` **content** backup (brief-base §6's
always-sound alternative), restored from content, and proved byte-exactness by md5
after each restore — `9e5a389939da6abcd5f6ec099586742b` before, after mutation 1,
after mutation 2, after mutation 3. No scratch copy, so #140's three poison modes do
not apply; `loremaster.__file__` re-printed inside the run anyway.

| # | mutation | expected | observed |
|---|---|---|---|
| 1 | `_COSINE_WEAK_MATCH_FLOOR = 0.50649` (undo the disarm) | the disarm pins go RED | **5 failed, 4 passed** — `test_the_shipped_floor_is_none`, `test_no_per_hit_weak_flag_however_low_the_cosine`, `test_no_aggregate_absence_verdict_even_when_every_condition_holds`, `test_the_disabled_state_serves_the_disarm_note_not_a_null`, and the `lore_index` served-surface pin |
| 2 | `_COSINE_SUBSTRATE_ENABLED = False` (over-correct) | **only** the substrate pin goes RED | **1 failed, 7 passed** — `test_the_substrate_line_still_renders` alone |
| 3 | `_COSINE_WEAK_MATCH_FLOOR_STAMP = None` (retire the stamp early) | **only** the stamp pin goes RED | **1 failed, 7 passed** — `test_the_measurement_stamp_survives_the_disarm` alone |

Mutations 2 and 3 are the discrimination receipts: each wrong build is caught by
exactly the pin written for it and by nothing else, so neither pin is passing for a
fixture reason. Mutation 1's *four* green survivors are the same evidence in reverse —
undoing the disarm does not disturb what the disarm was not supposed to touch.

**What wrong build still survives this class?** One I could not close from inside the
suite: a build that leaves `_COSINE_WEAK_MATCH_FLOOR = None` in source but ships an
image where the constant is patched at runtime. That is #139's class, and check 8
(§Smoke) is exactly its instrument — it interrogates the deployed artifact, not the
source.

---

## Sweep (rename-sweep law)

**Patterns — BARE and anchor-free, no `lore_` prefix, no call-paren anchor:**
`COSINE_WEAK_MATCH_FLOOR` · `COSINE_FLOOR_DISARMED` · `cosine_floor` · `CosineFloor` ·
`weak[ _-]match` · `no confident match` · `0.50649` · `real-query hits` ·
`COSINE_SUBSTRATE_ENABLED` — case-insensitive, over every tracked `.py/.md/.sh/.yaml/.toml`.

**391 hits. 0 unruled.** Every one of the 281 code/test hits carries an individual
`file:line` verdict in Table C below; the 110 `docs/` + `REPORT-*.md` hits carry a
per-FILE verdict with its reason (they are the ruled, dated record and the brief's
explicit do-not-touch set — they *should* describe the pre-disarm world).

**On the bare word `floor`:** I ran it (702 hits, whole tree) and it is **not a usable
sweep axis here** — in this repo the word names four unrelated mechanisms: the
budget floor-of-one (#75/#79), `map.py`'s `_BUDGET_FLOOR`, `calibration/counting.py`'s
`_HTTP_SERVER_ERROR_FLOOR`, `memory/local.py`'s `_IMPORTANCE_FLOOR` — plus this one.
Rather than emit 702 rows of which ~95% concern other mechanisms, I swept the
mechanism's own names and served strings (above), which is the set that can express
the corpse. Stating the narrowing explicitly rather than performing it silently.

### Table A — sites that CERTIFIED THE OLD SERVING (repaired)

| file:line | what it certified | repair |
|---|---|---|
| `test_mcp_server.py::TestCosineFloorStatusWiring::test_measured_state_when_the_stamp_matches_the_live_corpus` | patched only the **STAMP**, so it relied on the module constant being a float; the `None` short-circuit makes `state == "measured"` unreachable | added `monkeypatch.setattr(..., "_COSINE_WEAK_MATCH_FLOOR", 0.5828)` |
| `test_mcp_server.py::TestCosineFloorStatusWiring::test_stale_state_and_teaching_note_when_file_count_drifts` | same | same |
| `test_mcp_server.py::TestCosineFloorStatusWiring::test_stale_state_when_the_embedding_schema_fingerprint_changed` | same | same |
| `test_mcp_server.py::TestCosineFloorStatusWiring::test_disabled_state_when_the_floor_itself_is_unset` | `assert status.cosine_floor.note is None` — **the finding-#4 corpse**: it pinned the exact rendering the packet exists to remove | now asserts `== _COSINE_FLOOR_DISARMED_NOTE` |
| `test_search.py::TestApplyCosineFloorDriftCheck::test_disabled_state_when_the_floor_itself_is_none` | `assert status.note is None` — same corpse, unit layer | same |

Prose in the test tree that taught the retired world, corrected in step:
`test_search.py` module comment (`"production now ships LIT by default"`) and
`TestCosineWeakMatchDark`'s docstring (`"the production default is LIT"`). Neither is
asserted by any test — which is exactly why no gate could see them.

### Table B — verdict counts (see Table C for every code/test row individually)

| verdict | n | meaning |
|---|---|---|
| DOC-RULED | 110 | dated design/plan/receipt prose; brief's do-not-touch set; correct as history |
| SELF-PATCHED-VALID | 91 | the enclosing class monkeypatches its OWN floor → stays valid per the packet ruling (it is 11-ii's regression cover) |
| PROD-MACHINERY | 66 | the machinery itself, kept and gated dark; each reviewed in §Production review |
| CHANGED-THIS-WAVE | 43 | in this wave's diff vs `cbf61ac` |
| SURVEY-TOOL | 30 | `scripts/search_score_survey.py` + its tests — the offline floor **chooser**; it imports `_cosine_absence_predicate` and **never** the serving constant (grep: zero `_COSINE_WEAK_MATCH_FLOOR` hits under `scripts/`) |
| VALID/budget-fixture | 12 | `TestSearchParamsCutBudgetAndTeachingMiss` — hand-builds a `"no confident match"` string and feeds it to `_enforce_search_budget` to test finding #71's reservation; never calls the verdict machinery, never reads the floor |
| VALID/pure-fn | 11 | `TestCosineFloorDriftCheck` — `_cosine_floor_drift_note` takes the stamp as an **argument**; floor-independent |
| COSINE-PLUMBING | 6 | `store/candidate.py`, `store/surreal.py`, the surreal fakes — carry/derive `vector_cosine` as **data**; make no claim, read no floor |
| DRIFT-STATE-RESET | 5 | `conftest.py`'s autouse leak guard; floor-independent |
| VALID/marker-def · helper-doc · prose · substrate · corpse-pin · banner | 17 | individually listed in Table C |
| **TOTAL** | **391** | **UNRULED: 0** |

### Production review — the 66 PROD-MACHINERY rows, read for false claims

Each was read against the post-disarm behaviour. Findings:
- `search.py` lines 245–272 (the measurement provenance), 367–368 (the stamp), 385–558
  (the drift machinery), 563 (substrate template), 567–573 (**the weak-match template —
  byte-identical**), 597 (`_ABSENCE_VERDICT_MARKER`), 791–853 (the absence predicate and
  verdict), 1390–1399 (the render block): **accurate**. The comment at 567–568 (`"fires
  unconditionally below _COSINE_WEAK_MATCH_FLOOR"`) describes the *rule*, which is
  unchanged — the gate is still `floor is not None and cosine < floor`. Not a false claim.
- `server.py` 139, 1761, 2580, 3886–3929: wiring; accurate. 1566–1594: **falsified by my
  change and fixed** — see §Deviation 1.
- One residual I chose to **flag rather than edit** — §Surfaced item 6.

### Table C — every code/test hit, individually
See the appendix at the end of this report.

---

## Gates

| gate | result |
|---|---|
| `uv run pytest -n auto -q` — `test_search.py test_mcp_server.py test_retired_symbols.py test_render_seam_pins.py test_render.py test_server.py test_text_hygiene.py` | **976 passed, 3 xfailed in 89.97s** |
| `uv run pytest -n auto -q` — `test_smoke.py test_surreal_store.py test_surreal_fakes.py test_store_read.py test_map.py test_impact.py` | **420 passed in 33.89s** |
| `cd scripts && uv run pytest -q test_search_score_survey.py` | **50 passed in 0.28s** |
| `uv run ruff check .` | `All checks passed!` (exit 0) |
| `./scripts/typecheck.sh` | `Found 51 errors in 3 files (checked 149 source files)` — **zero delta**, see below |

**The mypy 51 are not mine, and I measured that rather than asserting it.** I checked
out `cbf61ac` (the commit immediately before this packet's first commit) and ran the
same canonical runner: `Found 51 errors in 3 files`. Same count, same three files —
`loremaster/tests/test_comms_tool.py`, `loremaster/tests/test_trace_telemetry.py`,
`loremaster/tests/test_comms_promise_registry.py` — all from this branch's 03b RED
contract wave (`bb64324`, `7a8e44f`), which pins symbols not yet built. Mid-run my own
RED-pins commit briefly raised it to 55 in 5 files (`_COSINE_FLOOR_DISARMED_NOTE` not
yet existing); the disarm commit took it back to 51/3.

**No failing tests were observed** in any suite I ran. I did not run the full suite —
the brief scoped me to the changed suites plus the structural/AST pins, and repo law
reserves the full run for the lead's phase checkpoint.

---

## Smoke — `docs/eval/smoke_p8b.py` check 8 (DEVIATION 2)

The packet's Exit says *"`smoke_p8b` is render-shape-coupled — update in step."* **It is
not, at this SHA.** Receipt:

```
$ grep -n "cosine\|weak match\|weak_match\|sim 0\.\|floor" docs/eval/smoke_p8b.py
(no output)
```

Its only render-shape parser is `_FINDING_ROW_PATTERN` over **findings** rows
(`parse_finding_rows` / `parse_finding_detail`); it never asserts anything about a
`lore_search` hit's trailers, and `check_index_status_calibration` reads only the
`calibration` section, never `cosine_floor`. So the packet's own deploy smoke —
*"`lore_index` renders the disabled state WITH its note, not a null"* — was mechanised
**nowhere**, and would have been checked by eye or not at all.

`smoke_p8b` being explicitly in my writable set, I built that gate rather than
reporting a no-op: `check_index_status_cosine_floor_disarm` asserts
`cosine_floor.state == "disabled"` and a non-empty note containing `disarmed`, `#176`,
`11-ii`, `substrate remains served`. **Substrings, not the constant** — this script
talks to a deployed image over MCP, so importing
`loremaster._COSINE_FLOOR_DISARMED_NOTE` would prove the *host's* source rather than the
*artifact's* (#139, the whole point of a smoke). It rides `--mechanics` too, being a
side-effect-free `lore_index` read.

**Controls (a probe needs a control):** driven against the real `IndexStatusSummary`
`model_dump()` payload, in-process, with the shipped constants:

```
PASS: lore_index() admits the weak-match disarm -> state='disabled', note='weak-match confidence
      surfaces disarmed pending per-instance calibration (findings #83/#176/#179/#180;
      packets 11-i/11-ii) — per-hit similarity substrate remains served.'
POSITIVE CONTROL: real served payload PASSES
NEGATIVE 1 (note=null)       REJECTED: cosine_floor.note is None — a disabled state must EXPLAIN itself…
NEGATIVE 2 (state=measured)  REJECTED: cosine_floor.state is 'measured', expected 'disabled'…
NEGATIVE 3 (bland note)      REJECTED: note does not admit the condition — missing ['disarmed', '#176', '11-ii', …]
```

Three different wrong builds, rejected for three different reasons — the probe is not
passing for a parse-error reason (the C1 lesson). Negative 1 is precisely the
pre-disarm rendering, so this gate goes red if the image regresses.

**This check has NOT been run against a live server** — the brief forbids deploying
from a worktree (#134). It is the lead's step after the cold audit.

---

## Deviation 1 — `server.py` edited, and why I did not merely flag it

The brief's writable set is `search.py` + tests + `smoke_p8b` + this report. I edited
`loremaster/loremaster/server.py`'s `CosineFloorStatus` docstring anyway, under
brief-base §2's regression exception, and I am disclosing it prominently rather than
burying it.

**The reason, measured rather than assumed.** That docstring is not internal
documentation — it is a **served surface**. Pydantic lifts a model's class docstring
into its JSON schema `description`, and FastMCP serves that as `lore_index`'s
`outputSchema`, so a consumer agent reads it. Verified in this tree:

```
$ uv run python -c "…mcp.server.fastmcp… tool with -> IndexStatusSummary…"
HAS_OUTPUT_SCHEMA: True
CONTAINS_COSINE_DOCSTRING: True
```

Before my change it told that consumer two things that my change made **false**:
1. that `state == "stale"` is what "DISARMED" means — implying `disabled` is merely
   "never configured", when after this packet `disabled` is the *only* state any
   instance reports and it means the surfaces are dark;
2. `note: A human-readable explanation, present iff state == "stale"` — the `disabled`
   branch now carries one too.

Under THE CONSUMER LAW + THE TRUST DOCTRINE ("a served count describes the whole set its
label claims; teaching prose matches measured behavior"), shipping a served surface that
mis-teaches its own state was not a defensible way to respect a writable set. The edit
is confined to the two docstrings (`CosineFloorStatus` class docstring and its `note`
attribute doc) — **no logic, no field, no default changed**; `git diff` for `server.py`
is 17 lines, all docstring.

**To revert:** `git checkout cbf61ac -- loremaster/loremaster/server.py` restores it, and
nothing in the suite depends on the new wording (no test asserts docstring text). If the
operator reverts it, the honest consequence is that `lore_index`'s output schema teaches
a consumer agent that the disarmed state means "never turned on".

---

## Surfaced — things I noticed and am NOT deciding

1. **`smoke_p8b` is not render-shape-coupled** (Deviation 2, above). The packet's Exit
   line is wrong at this SHA. Worth correcting in the packet file, which I may not edit.
2. **The packet's smoke criterion had no instrument.** Now it does (check 8), but the
   general shape is worth noting: the Exit named a smoke assertion that no committed
   script performed.
3. **The finding-#71 budget-reservation path is now unreachable in production.**
   `_enforce_search_budget` protects the absence-verdict notice from elision — but the
   pipeline can no longer emit that notice, so the reservation cannot fire until 11-ii.
   The code is conditional on the notice's presence, so it is inert, not broken, and its
   12 tests build the notice by hand and still pass. Flagging because it will look like
   dead code to the next reader.
4. **`_cosine_weak_match_warning` and `_COSINE_WEAK_MATCH_WARNING_TEMPLATE` are now
   production-unreachable**, kept deliberately (Scope OUT: templates go dark unchanged).
   A `lore_dead_code` sweep may flag them; that would be a false positive against a
   deliberate bound. If the lead wants it pinned rather than rediscovered, the repo's own
   "WHEN YOU CANNOT CLOSE A HOLE, PIN IT" idiom applies — but that is a scope call, not mine.
5. **The drift machinery is fully dormant.** With the floor `None`,
   `apply_cosine_floor_drift_check` always short-circuits to `disabled` and always sets
   `disarmed_by_drift = False`; `_cosine_floor_drift_note` is now reachable only via
   monkeypatch. Expected — 11-ii revives it — but it means finding #74 part 3's mechanism
   is not exercised by any production path until then.
6. **One prose residual I flagged rather than edited.** `search.py`'s
   `CosineFloorMeasurement` class docstring opens *"The corpus snapshot
   `_COSINE_WEAK_MATCH_FLOOR` was measured against."* It is defensible as written (it
   describes what the *type* records, and the stamp instance's comment block now states
   the deliberate disagreement explicitly) but a hurried reader could take it as claiming
   the two agree. The edit I would make, if wanted:
   `"""The corpus snapshot a measured cosine floor was taken against."""` — plus keeping
   the existing body. I left it because it sits one line from the Scope-OUT template
   boundary and the gain is marginal; say the word and it is one line.
7. **Two `docs/design/` files describe the weak-match surface in the present tense**
   (`2026-07-06-weak-match-discrimination.md`, `2026-07-06-client-needs-consult.md`).
   They are dated design records and the brief's do-not-touch set, so I classified them
   DOC-RULED — but a future agent retrieving a chunk from them gets present-tense prose
   about a surface that is now dark. Whether they get a dated header is the operator's call.

---

## What I did NOT do
- No deploy, no podman, no container (brief; #134).
- No touch to `/home/ejprice/PycharmProjects/lore` (the main checkout) — not a read of
  anything load-bearing, not a git command.
- No packet or design doc edited; `docs/reference/` and `CLAUDE.md` untouched.
- No full-suite run (brief-base §3 — the brief scoped the suites).
- I am not the grader of this work. A cold audit by a separate fresh agent runs before
  anything ships.

---

# Appendix — Table C: every code/test sweep hit with its individual verdict
| file:line | verdict |
|---|---|
| `loremaster/loremaster/search.py:245` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:256` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:264` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:271` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:272` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:282` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:298` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:305` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:306` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:325` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:326` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:362` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:363` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:365` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:367` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:368` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:385` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:395` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:396` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:402` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:410` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:425` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:429` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:430` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:446` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:460` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:461` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:473` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:491` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:495` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:500` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:502` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:507` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:522` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:524` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:525` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:526` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:527` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:534` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:536` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:539` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:540` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:551` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:558` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:563` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:567` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:568` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:571` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:572` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:573` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:597` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:700` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:701` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:702` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:791` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:805` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:811` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:816` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:828` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:849` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:853` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:1387` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/search.py:1390` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:1393` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:1395` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/search.py:1399` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:139` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:1566` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:1567` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:1570` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:1571` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:1574` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:1579` | CHANGED-THIS-WAVE |
| `loremaster/loremaster/server.py:1761` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:2580` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:3886` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:3894` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:3898` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/server.py:3929` | PROD-MACHINERY — kept, gated dark; individually reviewed (see §Production review) |
| `loremaster/loremaster/store/candidate.py:49` | COSINE-PLUMBING — carries/derives vector_cosine as DATA; makes no claim, reads no floor |
| `loremaster/loremaster/store/candidate.py:51` | COSINE-PLUMBING — carries/derives vector_cosine as DATA; makes no claim, reads no floor |
| `loremaster/loremaster/store/surreal.py:285` | COSINE-PLUMBING — carries/derives vector_cosine as DATA; makes no claim, reads no floor |
| `loremaster/tests/_surreal_fakes.py:779` | COSINE-PLUMBING — carries/derives vector_cosine as DATA; makes no claim, reads no floor |
| `loremaster/tests/conftest.py:52` | DRIFT-STATE-RESET — autouse leak guard; floor-independent |
| `loremaster/tests/conftest.py:56` | DRIFT-STATE-RESET — autouse leak guard; floor-independent |
| `loremaster/tests/conftest.py:59` | DRIFT-STATE-RESET — autouse leak guard; floor-independent |
| `loremaster/tests/conftest.py:77` | DRIFT-STATE-RESET — autouse leak guard; floor-independent |
| `loremaster/tests/conftest.py:79` | DRIFT-STATE-RESET — autouse leak guard; floor-independent |
| `loremaster/tests/test_mcp_server.py:2739` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2740` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2743` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2766` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2773` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2775` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2791` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2799` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_mcp_server.py:2800` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2804` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2805` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2806` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2807` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2816` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2822` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_mcp_server.py:2823` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2827` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2828` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2829` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2833` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2841` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2847` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_mcp_server.py:2848` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2852` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2853` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2854` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2861` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2865` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2866` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2871` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_mcp_server.py:2890` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_mcp_server.py:2891` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_mcp_server.py:2892` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_mcp_server.py:2894` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:2905` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_mcp_server.py:5112` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:5131` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:5239` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:5260` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:5307` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:5330` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:5372` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:5389` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:5820` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:5842` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:5998` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_mcp_server.py:6038` | VALID/budget-fixture — hand-built notice string fed to _enforce_search_budget (#71 reservation); never calls the verdict machinery, never reads the floor |
| `loremaster/tests/test_search.py:166` | VALID/marker-def — the absence markers, used by BOTH the lit-machinery pins and the new disarm pins (which assert their absence) |
| `loremaster/tests/test_search.py:170` | VALID/marker-def — the absence markers, used by BOTH the lit-machinery pins and the new disarm pins (which assert their absence) |
| `loremaster/tests/test_search.py:172` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:179` | VALID/marker-def — the absence markers, used by BOTH the lit-machinery pins and the new disarm pins (which assert their absence) |
| `loremaster/tests/test_search.py:180` | VALID/marker-def — the absence markers, used by BOTH the lit-machinery pins and the new disarm pins (which assert their absence) |
| `loremaster/tests/test_search.py:767` | VALID/prose — conditional statement about the notice not inflating the k-ceiling; timeless |
| `loremaster/tests/test_search.py:1005` | VALID/prose — permissive ('may legitimately co-occur'); asserts nothing about the floor |
| `loremaster/tests/test_search.py:1570` | VALID/banner — section header comment |
| `loremaster/tests/test_search.py:1575` | VALID/helper-doc — describes pinning a cosine relative to a (patched) floor; accurate |
| `loremaster/tests/test_search.py:1576` | VALID/helper-doc — describes pinning a cosine relative to a (patched) floor; accurate |
| `loremaster/tests/test_search.py:1615` | VALID/helper-doc — describes pinning a cosine relative to a (patched) floor; accurate |
| `loremaster/tests/test_search.py:1617` | VALID/helper-doc — describes pinning a cosine relative to a (patched) floor; accurate |
| `loremaster/tests/test_search.py:1645` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:1646` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:1655` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:1671` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1683` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1690` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1695` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1707` | VALID/substrate — patches _COSINE_SUBSTRATE_ENABLED=True, the SHIPPED value; substrate stays on |
| `loremaster/tests/test_search.py:1723` | VALID/substrate — patches _COSINE_SUBSTRATE_ENABLED=True, the SHIPPED value; substrate stays on |
| `loremaster/tests/test_search.py:1735` | VALID/substrate — patches _COSINE_SUBSTRATE_ENABLED=True, the SHIPPED value; substrate stays on |
| `loremaster/tests/test_search.py:1746` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1772` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1779` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1784` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1791` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1798` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1805` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1810` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1817` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1825` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1837` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1839` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1843` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1869` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1910` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1937` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1938` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1963` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:1990` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2007` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2009` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2025` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2043` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2065` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2090` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2098` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2259` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2260` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2270` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2277` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2281` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2282` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2287` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2297` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2305` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2315` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2318` | VALID/pure-fn — _cosine_floor_drift_note takes the stamp as an ARGUMENT; never reads the serving constant |
| `loremaster/tests/test_search.py:2322` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2323` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2337` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2339` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2344` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2348` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2349` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2351` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2357` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2362` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2366` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2367` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2369` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2376` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2381` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2383` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2395` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2396` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2409` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2413` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2414` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2417` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2421` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2425` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2429` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2451` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2453` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2463` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2464` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2478` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2481` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2484` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2492` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2493` | SELF-PATCHED-VALID — the class monkeypatches its OWN floor; stays valid per the packet ruling (11-ii regression cover) |
| `loremaster/tests/test_search.py:2507` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2510` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2516` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2536` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2538` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2541` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2547` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2550` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2552` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2564` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2608` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2614` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2622` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2636` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2640` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2641` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2643` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2650` | CHANGED-THIS-WAVE |
| `loremaster/tests/test_search.py:2664` | VALID/corpse-pin — asserts S4's RETIRED names are absent (_weak_match_warning, not _cosine_weak_match_warning); unaffected |
| `loremaster/tests/test_search.py:2670` | VALID/corpse-pin — asserts S4's RETIRED names are absent (_weak_match_warning, not _cosine_weak_match_warning); unaffected |
| `loremaster/tests/test_search.py:2685` | VALID/prose — says the cosine machinery cannot fire there (candidates carry vector_cosine=None); still true |
| `loremaster/tests/test_surreal_fakes.py:259` | COSINE-PLUMBING — carries/derives vector_cosine as DATA; makes no claim, reads no floor |
| `loremaster/tests/test_surreal_store.py:433` | COSINE-PLUMBING — carries/derives vector_cosine as DATA; makes no claim, reads no floor |
| `scripts/search_score_survey.py:9` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:44` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:142` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:166` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:173` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:177` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:201` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:217` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:527` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:541` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:546` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:601` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:660` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:786` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/search_score_survey.py:966` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:3` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:4` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:342` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:359` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:361` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:369` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:392` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:403` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:410` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:414` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:440` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:461` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:468` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:476` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |
| `scripts/test_search_score_survey.py:482` | SURVEY-TOOL — offline floor CHOOSER; imports _cosine_absence_predicate only, never the serving constant (grep: zero _COSINE_WEAK_MATCH_FLOOR hits in scripts/) |

### docs/ + REPORT-*.md hits — per-FILE verdict (ruled record, brief's do-not-touch set)
- `REPORT-fable-design-pkt10.md` — 6 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/design/2026-07-06-client-needs-consult.md` — 8 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/design/2026-07-06-weak-match-discrimination.md` — 20 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/design/2026-07-06-weak-match-external-validation.md` — 5 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/design/2026-07-24-floor-calibration.md` — 37 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/10-d-weak-match-disarm.md` — 9 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/10-floor-calibration-design.md` — 3 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/11-i-floor-calibration-dark-machinery.md` — 1 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/11-ii-floor-calibration-cutover.md` — 2 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/28-graph-search-v11.md` — 1 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/DESIGN-LAW.md` — 3 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/INDEX.md` — 4 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/receipts/2026-07-10-design-docs-extraction.md` — 8 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/receipts/2026-07-19-packet03/REPORT-recon-pkt03.md` — 1 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/receipts/2026-07-20-probes/probe_cosine_projection_s4b.py` — 1 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.
- `docs/plans/v2/receipts/2026-07-24-packet03b/REPORT-scout-147-traces.md` — 1 hits — DOC-RULED: dated design/plan/receipt prose describing the pre-disarm world; correct as history, explicitly do-not-touch.

### verdict counts
- DOC-RULED: 110
- SELF-PATCHED-VALID: 91
- PROD-MACHINERY: 66
- CHANGED-THIS-WAVE: 43
- SURVEY-TOOL: 30
- VALID/budget-fixture: 12
- VALID/pure-fn: 11
- COSINE-PLUMBING: 6
- DRIFT-STATE-RESET: 5
- VALID/marker-def: 4
- VALID/helper-doc: 4
- VALID/prose: 3
- VALID/substrate: 3
- VALID/corpse-pin: 2
- VALID/banner: 1
- **TOTAL: 391**

### UNRULED residue: 0
