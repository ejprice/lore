brief-base v6 read

# REPORT-merged-gate-03b — the MERGED-BUILD GATE for packet 03b

> **All measurements in this report were taken 2026-07-24 against lore branch
> `feat/surreal-unification` HEAD `6ed1a50`** — the POST-MERGE tree, i.e. after `be4c591`
> landed packets 10 / 10-d. Engine: spike-surreal **3.2.1** on `ws://127.0.0.1:18000`
> (`:18500` production was never contacted). Every claim below is a run against a COMPOSED
> build in scratch at that SHA — never a claim about any later state of these files.
>
> **PROVENANCE RECEIPT:**
> `loremaster.__file__ = /home/ejprice/scratch/merged-gate-03b/loremaster/loremaster/__init__.py`
> — built by `./scripts/scratch_copy.sh`, whose own output asserted all three members resolve
> inside the copy, and re-asserted by me with `uv run python -c "import loremaster; print(...)"`.
> **The repo was never edited by me** — this report is the only file I wrote inside it.

---

## SUMMARY BLOCK

- **VERDICT: GO — conditional on ONE named builder obligation (B-OBL-1), proven both
  necessary and sufficient on the composed build.**
- **state:** done-with-deviations.
- **THE COMPOSITION ITSELF WAS CLEAN: zero anchor failures, zero compose conflicts, zero
  re-anchors** (§2). Both references applied 3-way onto the post-merge tree, `git apply -3`
  reporting *"Applied … cleanly"* for all five files; line-level audit **0 missing adds,
  0 surviving removals** (§2.3).
- **THE ONE BLOCKER, found and resolved (§3): the CL3 paragraph-allowlist pin (`57d8677`)
  and the surface adversary's reference build CONTRADICT each other.** The reference deletes
  four `action=` prefixes from the `_INSTRUCTIONS` **MEMORY** paragraph — an **un-ruled**
  prose edit; CL3's `_DECLARED_NON_COMMS_PARAGRAPHS` declares that paragraph byte-exact to
  shipped production, prefixes intact. As-composed: **2 failed / 6530 passed**. Reverting the
  reference's un-ruled edit — the minimal fix — gives **0 failed** (§3.4).
- **ROOT CAUSE IS A C-DEF THAT ESCAPED (§3.5): CL3 shipped with NO satisfiability receipt
  against a correct build.** CL3 landed 12:19; the reference was frozen 11:49. Its only
  landing check was RED-against-production. **This gate is the first instrument that ever ran
  CL3 against a known-correct build** — and it found a violation on the first try.
- **GATES, corrected composition:** `uv run pytest -n auto -q` full repo → **6532 passed,
  17 skipped, 3 xfailed, 0 failed, exit 0** (§4.1, every skip/xfail individually attributed
  in §4.5) · `./scripts/typecheck.sh` → **0 errors, all 3 members** (§4.2) · `uv run ruff
  check .` → **All checks passed!**, no refactor needed (§4.3) · skill suite → **117 passed**
  (§4.4).
- **GLOBAL MYPY-ZERO IS REACHABLE. RG-R3 IS SETTLED.** Re-derived HEAD baseline **109 errors
  in 3 files** (102 / 6 / 1, all in the test tree); composed build **0**. The composition
  discharges the entire debt (§4.2).
- **SANITY LEGS (§5): 20/20 consecutive on both waves' concurrency pins; MP-H and MP-I green
  and MUTATION-PROVEN** — a W30 re-injection on the composed build reddens both (§5.3).
- **BUILDER OBLIGATIONS: §6** — 1 blocking, 4 informational. **Residuals with individual
  verdicts: §7.**
- **DECISIONS NEEDED:** one — §3.6 (confirm Reading A; the alternative requires editing a
  CERTIFIED contract, which a builder may not do).
- **Receipt pointers:** composition §2 · the blocker §3 · gate tails §4 · sanity legs §5 ·
  obligations §6 · residuals §7 · reproduction recipe §8.

---

## 1 — Method, and the controls on my own instruments

| leg | receipt |
|---|---|
| scratch provenance | `./scripts/scratch_copy.sh /home/ejprice/scratch/merged-gate-03b` → *"imports resolve INSIDE the copy: loremaster -> …/merged-gate-03b/loremaster/loremaster/__init__.py"*; independently re-asserted by importing in the copy's venv |
| composition is COMPLETE, not merely clean | a line-level audit (§2.3) over both reference diffs: every non-blank ADDED line present in the composed file at ≥ its multiplicity, every REMOVED line absent. `git apply` saying "cleanly" is not that claim |
| the merge's own work survived | the packet-10-d `CosineFloorStatus` docstring hunk is present in the composed `server.py` (`grep -c 'packet 10-d (2026-07-24) that is the SHIPPED state'` → 1); `search.py` carries the merge version untouched by the compose (`git diff --stat -- …/search.py` → empty) |
| restore integrity | every mutation restored from **content** (`cp -a` backups taken BEFORE the mutation), then verified by md5 against the pre-mutation hash — an md5 list is a detector, not a backup |
| **probe P0-FAILURE, self-caught and reported** | my first attempt at the HEAD mypy baseline ran `git checkout -- <files>`. Because `git apply -3` had **staged** the composition, that restored from the **INDEX**, not HEAD — and reported a "baseline" of **0 errors**, which is the composed build's number wearing the baseline's label. Caught by md5-ing the restored file (`318b6e47…` = my own pre-fix composition, not the HEAD blob). Re-run with `git checkout HEAD -- …` and verified by `git hash-object` == `git rev-parse HEAD:<path>` (`9d98026`) before the number was believed (§4.2) |
| positive control on the blocker | the blocker's fix is proven in BOTH directions **on the same tree**: 2 RED with the reference's edit, 0 RED without it, the four `action=` prefixes the only delta (§3.3–3.4) |
| positive control on the telemetry legs | MP-H/MP-I are not merely green — a W30 re-injection on the composed build reddens **both**, so their green is discrimination and not inertness (§5.3) |

**Tool honesty (brief-base §4):** this was a *textual-seam* task throughout — composing two
diffs, chasing a byte-difference in a prose paragraph, and reconciling commit timestamps. That
is case (b) of the repo's three grep-honest cases (non-symbol textual seams), so I used
`grep`/`git` directly rather than lore's graph tools, and I am saying so here. No lore weakness
was routed around; there is nothing to file.

---

## 2 — THE COMPOSITION

### 2.1 What each reference actually is

**Both adversary scratch trees are still on disk and both are at git base `03b93d3`.** In both,
the final reference is the WORKING TREE, not a replayable recipe:

| wave | files | recipe status |
|---|---|---|
| **surface** (`REPORT-adversary-surface-03b-r2.md` §1.1) | `loremaster/loremaster/server.py`, `config.py` | `REFBUILD/apply_reference.py` is **STALE** — mtime 09:26, while the reference `server.py.frozen` is 11:49. The adversary converged the reference by hand after running it (its §1.1 says so: *"converging the reference onto the contract's pinned SHAPES"*). **`apply_reference.py` does NOT reproduce the graded reference; the working tree does.** Verified: `md5sum` of the scratch working tree == `REFBUILD/FROZEN.md5` for both files (`36a6ca0d…` / `bdbda576…`) |
| **telemetry** | `loremaster/loremaster/server.py`, `store/surreal.py`, `store/surreal_schema.py` | no script; the working tree is the reference. `/home/ejprice/scratch/REFERENCE-telemetry-03b-v2.diff` is also **stale** (09:30 vs the prod files' 10:35) |

**Deviation, disclosed:** the brief said to read the recipes and compose them. Both recipes are
stale relative to the graded reference, so composing them would have graded a build **neither
adversary certified**. I composed the **frozen working trees** instead — the artifacts the
SUFFICIENT verdicts were actually rendered against. §8 carries the exact reproduction commands.

### 2.2 The compose — clean, first attempt

Each reference was extracted as a production-only diff against its own base `03b93d3`
(`git diff -- loremaster/loremaster/` inside the adversary's scratch), then applied to the
post-merge tree with `git apply -3` so the merge's `server.py` (+17) and `search.py` (+74)
deltas participate in a real three-way merge rather than a line-offset gamble.

```
$ git apply -3 --verbose <surface prod diff>
Checking patch loremaster/loremaster/config.py...
Applied patch to 'loremaster/loremaster/config.py' cleanly.
Checking patch loremaster/loremaster/server.py...
Applied patch to 'loremaster/loremaster/server.py' cleanly.

$ git apply -3 --verbose <telemetry prod diff>
Checking patch loremaster/loremaster/server.py...
Applied patch to 'loremaster/loremaster/server.py' cleanly.
Checking patch loremaster/loremaster/store/surreal.py...
Applied patch to 'loremaster/loremaster/store/surreal.py' cleanly.
Checking patch loremaster/loremaster/store/surreal_schema.py...
Applied patch to 'loremaster/loremaster/store/surreal_schema.py' cleanly.
```

- **ANCHOR FAILURES: NONE.** No re-anchoring was required, and therefore none is reported.
- **COMPOSE CONFLICTS: NONE.** Both references edit `server.py`, but their hunks are disjoint —
  and disjoint from the merge's. Measured hunk map (pre-image line numbers at `03b93d3`):
  - merge (`be4c591`): **1573–1604** only (`CosineFloorStatus` docstrings; no code).
  - telemetry: 40, 47, **1636**, 6587, 6666.
  - surface: 67, 124, 174, 1103, 1124, **1375**, 1873, 1912, 4382–5145 (the `AppContext.comms`
    body), 5404–5458, 5753–6075, 7365–7514.

  The closest approach is surface@1375 → telemetry@1636 → merge@1573: three distinct regions,
  no overlap. **The +17/+74 line shift the brief flagged as the re-anchor hazard was absorbed
  entirely by the 3-way apply.**
- **SEMANTIC CONFLICT: NONE between the two references.** (The one contradiction found is
  between the *surface reference* and the *CL3 pin* — §3 — not between the two references.)

### 2.3 Completeness audit (the control on "cleanly")

`git apply` reporting success does not prove the reference's content ARRIVED. Audited per
reference diff: every non-blank `+` line counted against its multiplicity in the composed file,
every `-` line checked absent.

| reference | file | +lines | −lines | MISSING ADDS | SURVIVING REMOVALS |
|---|---|---|---|---|---|
| surface | `config.py` | 4 | 0 | **0** | **0** |
| surface | `server.py` | 630 | 16 | **0** | **0** |
| telemetry | `server.py` | 119 | 6 | **0** | **0** |
| telemetry | `store/surreal.py` | 55 | 20 | **0** | **0** |
| telemetry | `store/surreal_schema.py` | 73 | 12 | **0** | **0** |

Plus: all four composed files parse (`ast.parse` OK), the telemetry marker `class TracingFastMCP`
is present, the surface post-lint extraction `AppContext._validate_comms_identities` is present
(defined and called), and the merge's own docstring hunk survived.

---

## 3 — THE BLOCKING FINDING (found, root-caused, and resolved to one builder obligation)

### 3.1 The failure

Full repo suite on the composition **as both adversaries froze it**:

```
FAILED loremaster/tests/test_comms_tool.py::TestTheInstructionsBlockTeachesTheMessageSurface::test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs
FAILED loremaster/tests/test_comms_tool.py::TestTheInstructionsBlockTeachesTheMessageSurface::test_CONTROL_the_declared_NON_comms_paragraphs_are_byte_exact
2 failed, 6530 passed, 17 skipped, 3 xfailed, 1 warning in 193.62s
```

Note which two: **CL3 and its own control**. The control firing is the instrument working
exactly as designed — its docstring promises to split *"the comms block is wrong"* from
*"somebody else's paragraph is off by a byte"*, and it correctly reported the second.

### 3.2 The exact byte-difference

`_INSTRUCTIONS`, the **MEMORY** paragraph (index 5 of 7; the comms block splices at index 6):

- **Shipped production at HEAD `6ed1a50`** (`server.py`, the `_INSTRUCTIONS` tuple):
  `"lore_comms coordinates a LIVE multi-agent fleet: action=register before anything else,`
  `action=heartbeat to stay current and learn brief skew, action=brief_get/brief_publish/`
  `brief_ack for standing instructions, action=fleet to see who else is active."`
- **CL3's declaration** (`test_comms_tool.py`, `_DECLARED_NON_COMMS_PARAGRAPHS`, member 6):
  **identical to production — the four `action=` prefixes intact.**
- **The surface adversary's reference build:** deletes all four. Its diff hunk at
  `@@ -1375,10 +1407,25 @@ _INSTRUCTIONS = (` is a `-`/`+` pair replacing
  `"…fleet: action=register before "` with `"…fleet: register before "`, and likewise for
  `action=heartbeat`, `action=brief_get/brief_publish/brief_ack`, `action=fleet`.

So the reference serves a MEMORY paragraph CL3 does not allow. CL3's diff output names it
precisely — *"first divergence at offset 1567"*, inside MEMORY, before the comms block.

**Is the deletion ruled anywhere? No.** Grepping `docs/plans/v2/03b-design-rulings-r2.md` and
`docs/plans/v2/03b-comms-message-surface.md` for `action=register` / `action=heartbeat` /
`MEMORY paragraph` returns exactly one hit — `03b-design-rulings-r2.md:206`, about
`action=heartbeat` in `AppContext.comms` step 7, which is code, not `_INSTRUCTIONS` prose. The
plausible motive is de-duplication (the reference's NEW comms paragraph teaches `action=send` /
`action=drain` / `action=ack`, so the MEMORY prefixes read as redundant) — **but no ruling asks
for it, and the reference author never had CL3 to check it against.**

### 3.3 Mutation proof, leg 1 — the pin discriminates

The composed build WITH the reference's un-ruled edit: **2 failed** (§3.1). That is the RED leg.

### 3.4 Mutation proof, leg 2 — the minimal fix is sufficient

Sole delta applied to the composed `server.py` (anchor asserted unique, one `str.replace`):
restore the four `action=` prefixes in the MEMORY paragraph. Nothing else touched.

```
$ uv run pytest -n auto -q loremaster/tests/test_comms_tool.py \
      loremaster/tests/test_comms_wiring.py \
      loremaster/tests/test_comms_promise_registry.py loremaster/tests/test_mcp_server.py
1630 passed in 108.69s (0:01:48)
```

and then the whole repo (§4.1): **6532 passed, 0 failed**.

**Both legs on the same tree, four prefixes the only variable.** The fix is necessary (leg 1)
and sufficient (leg 2). And it breaks nothing that WANTED the prefixes gone — in particular the
RG2-family selector `any(f"action={verb}" in paragraph for verb in ("send","drain","ack"))`
still does not select MEMORY, because `action=brief_ack` does not contain the substring
`action=ack` and none of `register`/`heartbeat`/`brief_get`/`brief_publish`/`fleet` matches
either. That was the one plausible reason to think the prefixes were load-bearing; it is
measured false.

### 3.5 ROOT CAUSE — a C-DEF that escaped, and how

Reconstructed from commit timestamps and file mtimes (all 2026-07-24):

| time | event |
|---|---|
| 11:49–11:50 | surface adversary FREEZES its reference (`REFBUILD/server.py.frozen` mtime 11:49, `FROZEN.md5` 11:50) |
| 12:10 | `6589d57` — surface final verdict; **CL3 RULED**. Adversary pre-commits SUFFICIENT to either exit: *"no fifth pass — the ruling is the certification, pending the pin landing verified."* |
| 12:19 | `57d8677` — **CL3 LANDS** in `test_comms_tool.py` |

**CL3 was written ~30 minutes after the only correct build in existence was frozen, and was
never run against it.** The landing receipt in `57d8677` is *"Lead-verified landing: 300F/885P
… neighbours 693/0"* — a **RED-against-production** check, and the contract author's own
appendix (added in the same commit) says it *"verified CL3 is now RED reporting `declared 8
paragraphs, served 7` — the missing block, **its only delta**."*

That last clause is the defect. It is true against **production**, from which the declaration
was generated — and *necessarily* true, since the tuple was derived from the very document it
was being compared to. It is **false against the reference build**, where the delta is the
missing block *plus* four `action=` prefixes. **A pin whose declaration is generated from the
build it is checked against cannot fail for a content reason; it can only ever report the one
delta the generator did not copy.** The check was structurally incapable of finding this.

This is exactly the class the repo legislates for — *"A CONTRACT SHIPS WITH A SATISFIABILITY
RECEIPT … prove the contract goes 0-failed against a known-correct build, before any builder
sees it"* (CLAUDE.md, the C-DEF class). The surface author's own §I.4 records catching a **fifth**
C-DEF inside this very edit and draws the right lesson — *"the edit that lands an instrument
needs its own control"* — and then the instrument landed with a control that could not see this
one. **Nothing between 12:19 and this gate could have caught it**, because the reference build
lived only in an adversary's scratch tree and no process step composes the two.

### 3.6 DECISION NEEDED — two readings, and my pick

- **Reading A (my pick, and the one I proved):** the reference's `action=`-prefix deletion is an
  un-ruled, gratuitous prose edit. The builder simply must not make it. CL3's declaration stands;
  the contract stays frozen; the composed build goes 0-failed. → **B-OBL-1.**
- **Reading B:** the deletion is intended de-duplication, and `_DECLARED_NON_COMMS_PARAGRAPHS`
  should be updated to match. CL3's own failure message explicitly names this path — *"another
  packet legitimately edited `_INSTRUCTIONS` … update the tuple; that is the deliberate decision
  CL3 exists to force."*

**I pick A**, for a reason that is procedural rather than aesthetic: under B the *builder* must
edit a **CERTIFIED contract**, which builders may not do — so B is not a builder action at all,
it is a contract amendment requiring the author and a re-certification. A costs nothing and is
proven green. **But the operator owns this: if the `action=` prefixes were meant to go (a
readability call about serving `action=` twice in adjacent paragraphs), that is B, and it is a
contract-author task to be scheduled BEFORE the builder starts, not a thing the builder discovers.**

---

## 4 — GATES on the corrected composition

### 4.1 Full repo suite — `uv run pytest -n auto -q`

```
6532 passed, 17 skipped, 3 xfailed, 1 warning in 301.67s (0:05:01)
PYTEST_EXIT=0
```

**0 failed.** Both waves' REDs are green under the composed references; the merge's own suites
are green; collection is complete (the as-frozen run collected the identical total: 2 failed +
6530 passed = 6532). Every skip and xfail is individually attributed in §4.5. The single warning
is a pre-existing `RuntimeWarning: coroutine '_empty_subscription' was never awaited` in
`test_retry_seam.py::TestEverySdkCallSiteActuallyRetries::test_scouts_live_subscription_is_retried`
— present in both runs, unrelated to either wave, filed as residual R4.

### 4.2 `./scripts/typecheck.sh` — and RG-R3, settled

```
Success: no issues found in 27 source files      typecheck: lorescribe OK
Success: no issues found in 32 source files      typecheck: loresigil OK
Success: no issues found in 149 source files     typecheck: loremaster OK
TC_EXIT=0
```

**0 errors, all three members.** And the coverage is checked, not assumed — mypy's own
`149 source files` for `loremaster` is *exactly* `find loremaster/loremaster -name '*.py'` (56)
`+ find loremaster/tests -name '*.py'` (93) = **149**. The whole test tree is in scope; a
"0 errors" that silently excluded the tests would show a smaller number.

**Baseline, re-derived by me at the post-merge HEAD `6ed1a50`** (per repo law: a number you did
not measure is a rumour — and the three inherited figures disagree):

```
$ git checkout HEAD -- <the 4 files>   # verified: git hash-object == git rev-parse HEAD:<path> == 9d98026
$ ./scripts/typecheck.sh
Found 109 errors in 3 files (checked 149 source files)
typecheck: loremaster FAILED
```

| file | errors at HEAD `6ed1a50` |
|---|---|
| `loremaster/tests/test_comms_tool.py` | 102 |
| `loremaster/tests/test_comms_promise_registry.py` | 6 |
| `loremaster/tests/test_comms_wiring.py` | 1 |

All 109 are in the TEST tree and all are the RED contract naming production symbols that do not
exist yet (`Unexpected keyword argument "grade"/"thread"/"to" for "comms"`,
`"type[AppContext]" has no attribute "_render_comms_send"/"_render_comms_drain"/"_render_comms_ack"`).
**The composition takes 109 → 0.**

> **RG-R3 IS SETTLED: global mypy-zero is REACHABLE, and 03b's owned exit debt is discharged in
> full by this composition — no residual debt is deferred to a later packet.**

Note on the inherited numbers, honestly: the surface adversary reported **92**, the telemetry
adversary's R8 reported **126**, the CL3 appendix reported **109 (unchanged)**. My 109 at
`6ed1a50` corroborates the third. The first two were stamped at `03b93d3` and disagree *with
each other* at what should be the same SHA; I did not adjudicate that, and it is residual R1.

### 4.3 `uv run ruff check .`

```
All checks passed!
RUFF_EXIT=0
```

**No lint refactor was needed by the composition.** The surface adversary's P14 warning — that
the ruled validation order pushes `AppContext.comms` to 13 branches and trips
`PLR0912 (13 > 12)` — is real, but its fix is **already embodied in the frozen reference**:
`AppContext._validate_comms_identities` exists as a separate method and `AppContext.comms`
calls it. The builder therefore inherits that extraction as an obligation to REPRODUCE, not a
surprise to discover (**B-OBL-2**). Ruff is clean on the composed build with it in place.

### 4.4 Skill suite (repo-law idiom)

```
$ cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests
117 passed in 14.76s
```

### 4.5 Every skip and xfail, individually attributed

Banned output would be "the rest are pre-existing". The full enumeration (`-rsx`):

| count | test | reason (as declared by the test) |
|---|---|---|
| 3 | `test_render.py::TestD14KnownGapSurvivors::test_known_survivor_is_stripped_like_every_other_threat_char[U+00AD / U+061C / U+E0001]` | **XFAIL** — *"D1.4 unicodedata category engine not landed yet (PKT-03)"*. A declared, packet-attributed known gap |
| 4 | `test_message_ledger.py:642` | SKIP — *"raw edge counts are a REAL-backend observation"* |
| 1 each | `test_message_ledger.py` at 768, 738, 2732, 2713, 2487, 2452, 1774, 1521, 1492, 1206 (10 total) | SKIP — REAL-backend observation / REAL-backend fixture gates (dangling-endpoint, raw-store row count, statement-seam, live DDL, edge deletion, unguarded-write control) |
| 2 | `test_caplog_isolation.py:78, :88` | SKIP — *"runs only inside the nested serial probe"* |
| 1 | `loresigil/tests/test_voyage_batch.py:1417` | SKIP — *"requires a real VOYAGE_API_KEY in the environment; never runs in CI"* |

**17 skips + 3 xfails, all condition-declared, none introduced by either wave or by the compose**
(the as-frozen run reported the identical 17/3).

---

## 5 — SANITY LEGS

### 5.1 Concurrency — at the repo's 20-consecutive law, not one green run

Both waves' concurrency pins, run together, **20 consecutive times** on the composed build
against the TEST store `ws://127.0.0.1:18000`:

- surface: `test_message_ledger.py::TestConcurrentSendsMintDistinctSeqs` (8-way distinct seqs ·
  all exceed the pre-race maximum · each readable by its recipient)
- surface: `test_message_ledger.py::TestConcurrentAcksOfOneEdgeProduceExactlyOneWinner`
- telemetry: `test_trace_telemetry.py::TestTheOrdinalIsMintedByTheStore` (incl.
  `test_eight_concurrent_writes_mint_eight_distinct_ordinals`)

```
run 1: 14 passed in 7.10s
…
run 20: 14 passed in 6.95s
TOTAL_RUNS_WITH_FAILURES=0
```

**20/20, 14 passed each.** This matches what the per-wave references showed (the telemetry
adversary's §8 reported 20/20 on its own reference).

### 5.2 MP-H / MP-I — green

```
$ uv run pytest -v loremaster/tests/test_trace_telemetry.py::TestADispatchLandsARealRowInTheRealTraceTable
5 passed in 4.26s
```
(the class carries MP-A's two legs plus MP-H `test_every_REAL_registered_tool_lands_a_real_row`
and MP-I `test_every_REAL_registered_tool_that_FAILS_lands_a_real_row`.)

### 5.3 MP-H / MP-I — MUTATION-PROVEN, because green alone proves nothing

Per repo law (*a pin that cannot be demonstrated failing is not a pin*), I re-injected the exact
defect MP-H was written to catch — adversary **W30**, a bad kwarg supplied only for real tools —
into the composed `TracingFastMCP._emit_trace`:

```python
transport_session=self._transport_session(request_context),
**({"request_id": "x"} if tool.startswith("lore_") else {}),  # W30 MUTATION
```

```
FAILED …::TestADispatchLandsARealRowInTheRealTraceTable::test_every_REAL_registered_tool_lands_a_real_row
FAILED …::TestADispatchLandsARealRowInTheRealTraceTable::test_every_REAL_registered_tool_that_FAILS_lands_a_real_row
FAILED …::TestCoverageIsACheckedVariable::test_every_registered_tool_dispatch_records_exactly_one_row[lore_diff … ×5 shown]
33 failed, 79 passed in 7.70s
```

**Both MP-H and MP-I redden on the post-merge composed build.** Restored from the `cp -a` content
backup and verified byte-exact (`md5sum` → `110ed773aa2170852ac1c48fbd1e3bd0`, the pre-mutation
hash), then re-run green: `112 passed in 7.63s`.

### 5.4 CL3 — mutation-proven in §3.3/§3.4

The blocker investigation is itself the third surface leg, and the strongest available: the pin
RED with the reference's edit, GREEN without it, both legs on one tree, four prefixes the only
variable.

---

## 6 — BUILDER OBLIGATIONS (this list rides the builder's brief)

| id | obligation | severity |
|---|---|---|
| **B-OBL-1** | **In `_INSTRUCTIONS`, the MEMORY paragraph is UNTOUCHED — keep `action=register` / `action=heartbeat` / `action=brief_get/brief_publish/brief_ack` / `action=fleet` exactly as shipped.** The surface reference deletes those four prefixes; that edit is un-ruled and reddens CL3 + its control. The ONLY legal `_INSTRUCTIONS` change in 03b is INSERTING the ruled comms paragraph at index 6. Pending the §3.6 ruling. | **BLOCKING** |
| **B-OBL-2** | Reproduce the post-lint extraction: the ruled validation order (B1 steps 2+6) pushes `AppContext.comms` to 13 branches and trips `PLR0912 (13 > 12)`. The reference extracts `AppContext._validate_comms_identities`. Not optional, and not specified by any pin — a builder who does not extract will fail ruff, and one who extracts *differently* still passes the four charset pins. Carried from the surface adversary's P14. | required for ruff |
| **B-OBL-3** | **Compose-order constraint: NONE.** Measured — the two references' `server.py` hunks are disjoint from each other and from the merge's, and 3-way apply is order-independent here (§2.2). The builder may implement the two waves in either order, or in one pass. Recorded so nobody invents a sequencing rule that does not exist. | informational |
| **B-OBL-4** | **Re-anchoring: NONE required.** The merge's `server.py` +17 / `search.py` +74 shifts are absorbed by 3-way merge; no anchor in either reference was invalidated. Recorded because the brief anticipated re-anchors and the honest answer is that there were zero. | informational |
| **B-OBL-5** | The references are the two adversary scratch WORKING TREES, not the checked-in recipe scripts — `REFBUILD/apply_reference.py` and `REFERENCE-telemetry-03b-v2.diff` are both stale and do NOT reproduce the graded builds (§2.1). Any brief pointing a builder at the scripts points at an uncertified build. | informational |

---

## 7 — RESIDUALS (every one with an individual verdict; nothing dropped)

| id | residual | verdict |
|---|---|---|
| **R1** | Three mutually inconsistent HEAD mypy figures are in the record: **92** (surface adversary §1.1, at `03b93d3`), **126** (telemetry adversary R8, at `03b93d3`), **109** (CL3 appendix; and my re-derivation at `6ed1a50`). Two of them claim the same SHA and disagree. | **unadjudicated, low harm now.** My 109 at `6ed1a50` is measured and per-file itemised (§4.2), and the composed build is 0, so no decision depends on which of 92/126 was right. Recorded because an un-derived count in the record is exactly what this repo's law says to re-derive rather than inherit. |
| **R2** | **The reference builds live only in scratch trees under `/home/ejprice/scratch/`** — an address the repo's own citation law forbids relying on. Two SUFFICIENT certifications currently rest on artifacts with no durable address, and this gate's composition does too. | **real process risk, not mine to close.** If the builder is expected to consult the references, they need a tracked home (a `docs/plans/v2/receipts/2026-07-24-03b/` diff pair would cost one `git add`). §8 gives a regeneration recipe as the stopgap, which works only while the scratch trees survive. **Recommend the lead land the two prod diffs before the scratch trees are reaped.** |
| **R3** | CL3 couples the comms contract to seven paragraphs owned by other packets. Its author states packets **04 and 05 will both meet a RED here**. | **known and deliberate** (the author's I.2 states the cost). Flagged forward: the same mechanism that caught B-OBL-1 will fire for 04/05, and the correct response there is to update the tuple — the decision CL3 exists to force. It is NOT a defect when it fires. |
| **R4** | `RuntimeWarning: coroutine '_empty_subscription' was never awaited` from `test_retry_seam.py::TestEverySdkCallSiteActuallyRetries::test_scouts_live_subscription_is_retried` | **pre-existing, unrelated to either wave** — identical in the as-frozen and corrected runs. A `contextlib.suppress(Exception)` around a never-awaited coroutine. Not investigated; surfaced rather than buried. |
| **R5** | The surface adversary's own report stands at **VERDICT: CONTRACT INSUFFICIENT** on disk, with the SUFFICIENT verdict living in later commit messages and an appended fix-wave section. A future reader retrieving a span of that report will read INSUFFICIENT as current. | **archival hazard, low.** The brief-base rule about retrieved chunks arriving without their header applies. Cheap fix at archive time: a one-line header noting the verdict was superseded by the fix waves + `6589d57`. |
| **R6** | `apply_reference.py`'s docstring/report describes it as the reference recipe, but it is stale by ~2.5 hours relative to the frozen reference it supposedly builds. | **a served-prose-vs-behaviour mismatch** — the repo's own most-cited defect class, in an adversary's own instrument. Harmless here only because I checked mtimes and md5s instead of trusting the label. Worth one line in the archived report. |

---

## 8 — REPRODUCTION RECIPE

Durable-as-commands, since the inputs have no tracked path (R2). From the repo root at
`6ed1a50`:

```bash
./scripts/scratch_copy.sh /abs/path/to/compose         # asserts provenance; non-zero if poisoned

# 1. extract each reference as a production-only diff against its own base 03b93d3
(cd /home/ejprice/scratch/adv-surface-03b-r2   && git diff -- loremaster/loremaster/) > surface.diff
(cd /home/ejprice/scratch/adv-telemetry-03b-r2 && git diff -- loremaster/loremaster/) > telemetry.diff

# 2. three-way apply onto the post-merge tree (order-independent, B-OBL-3)
cd /abs/path/to/compose
git apply -3 surface.diff
git apply -3 telemetry.diff

# 3. B-OBL-1: undo the surface reference's un-ruled MEMORY-paragraph edit
#    restore "action=register" / "action=heartbeat" /
#    "action=brief_get/brief_publish/brief_ack" / "action=fleet" in the _INSTRUCTIONS
#    MEMORY paragraph, exactly as shipped at HEAD.

# 4. gates
uv run pytest -n auto -q            # expect: 6532 passed, 17 skipped, 3 xfailed, 0 failed
./scripts/typecheck.sh              # expect: 0 errors, 3 members, 149 loremaster files
uv run ruff check .                 # expect: All checks passed!
(cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests)   # expect: 117 passed
```

⚠ Steps 1–2 depend on the two adversary scratch trees still existing. That is R2.

---

## 9 — VERDICT

# **GO**

**One composed build satisfies EVERYTHING at the post-merge tree** — both certified contract
waves, the packet-10/10-d merge's own suites, the entire rest of the repo, mypy across all
three members including the full test tree, ruff, and the skill suite — **conditional on
B-OBL-1**, a one-line un-edit that I proved is both necessary and sufficient, and which costs
the builder nothing because it is an instruction *not* to make a change.

**Global mypy-zero is reachable and this composition reaches it: 109 → 0.** 03b's owned exit
debt is dischargeable in full.

The composition mechanics the brief flagged as the risk — anchor drift from the merge's +17/+74,
and a semantic collision between two references that both patch `server.py` — **did not
materialise at all**. The real hazard was somewhere nobody was looking: a pin certified 30
minutes after the only correct build was frozen, checked only against the document its own
declaration was generated from, and therefore structurally unable to fail for the one reason it
turned out to be wrong.

---

*— merged-gate-03b, 2026-07-24, at `feat/surreal-unification` `6ed1a50`.*
