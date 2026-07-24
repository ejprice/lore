# REPORT-wording-es5c-03b — the E-S5(c) skew-wording amendment, applied everywhere

brief-base v6 read

- **state:** done-with-deviations · one-concern change: the E-S5(c) wording amendment across
  1 production file + 4 test suites, uncommitted (lead commits)
- **dev-1:** amended TWO production **comments** inside the amended skew block (they taught
  `heartbeat` as the sole surfacing verb). The brief scoped me to "the tail-literal sites"; both
  readings written out in §6.1 — revert those two hunks if the lead meant literals-only
- **dev-2:** re-derived sweep = **50 in-scope sites**, not Appendix A's 47 (§1) — and **2 of them
  are invisible to the bare `grep -rn "next heartbeat"`** because the phrase is line-WRAPPED
- **decisions-needed (1):** ⚠ **the amended production prose is an OVER-claim until FK-6's
  drain-serves-skew build lands** — it must ship in the same packet or be reverted (§6.3)
- **zero-green-broken:** baseline **270F/707P** → after **270F/707P**, **failure sets byte-identical**
  (`diff` clean, §3); every RED stayed RED for the same reason (§3.2)
- **gates:** `uv run ruff check .` → *All checks passed!* · `./scripts/typecheck.sh` → *Found 92
  errors in 2 files* (unchanged; **0 in any file I touched**, §4)
- **copy count:** executable copies of the sentence **4 prod + 38 test → 4 prod + 2 test** (§2)
- **sharing PROVEN BY MUTATION, not inspection:** mutating the ONE shared constant reddens pins in
  **all four** test modules (23 tests); mutating production alone still reddens the registry (§5)
- **receipts:** sweep table §1 · copy count §2 · zero-green-broken §3 · gates §4 · mutation §5 ·
  judgment calls + flags §6

---

*All measurements in this report were taken on 2026-07-24, on the `feat/surreal-unification`
working tree whose HEAD moved from `7a8e44f` to `c738d2f` mid-run (a parallel author's telemetry
wave was committed by the lead while I worked). Neither commit touches any of my five files —
verified `git diff --name-only 7a8e44f..c738d2f -- <my five>` → empty — so the baseline taken
before them is still apples-to-apples.*

## 0. What was applied

Design authority: `docs/plans/v2/03b-design-rulings-r2.md` §G row **E-S5(c)** (committed
`aa25e79`), whose mechanical replacement spec is:

- `"at their next heartbeat"` → `"at their next heartbeat or drain"`
- `"at next heartbeat"` → `"at next heartbeat or drain"`

Authorization: operator grant relayed via the lead (packet file §OPERATOR GRANT (second),
`1e3a249`). The four registry DESCRIPTIONS the spec also names were **already** action-agnostic
under E-S5(a) — they name the emitter set *"(heartbeat and, per FK-6, drain)"* — so per
Appendix A.6(b) of `REPORT-contract-surface-03b-r2.md` they needed no further edit and got none.
I added the `[E-S5(c)]` tag to the two that carried `[E-S5(a)]`.

## 1. The sweep — re-derived, never inherited

**Instrument A (the law's bare, anchor-free form):** `grep -rn "next heartbeat"` over the repo.

**Instrument B (my addition — and it earned its keep):** a wrap-tolerant regex
`next[\s"'#\\]*heartbeat`, because a phrase split across a source line break carries no contiguous
match. **It found 2 sites instrument A structurally cannot see:**

| site | shape | bare grep sees it? |
|---|---|---|
| `server.py`, `_render_comms_brief_publish` tail-1/2 comment | `…next\n # heartbeat…` (comment continuation) | **NO** |
| `test_comms_render_architecture.py`, `test_ninth_instances_promise_is_true_end_to_end` docstring | `…next\n heartbeat'…` (docstring wrap) | **NO** |

This is Appendix A.4's own lesson one turn further on: a bare pattern beats an anchored one, and a
**wrap-tolerant** pattern beats a bare one. Anyone re-running this sweep should use instrument B.

### 1.1 BEFORE — 50 in-scope sites across 5 files (re-derived, at `7a8e44f` + working tree)

| file | bare-grep lines | + wrapped | total | writable |
|---|---|---|---|---|
| `loremaster/loremaster/server.py` | 4 | 1 | **5** | yes (scoped) |
| `loremaster/tests/test_comms_promise_registry.py` | 13 | 0 | **13** | yes |
| `loremaster/tests/test_comms_tool.py` | 19 | 0 | **19** | yes |
| `loremaster/tests/test_comms_render_architecture.py` | 11 | 1 | **12** | yes |
| `loremaster/tests/test_comms_wiring.py` | 1 | 0 | **1** | yes |
| **total** | **48** | **2** | **50** | |

**Discrepancy with Appendix A, stated plainly:** Appendix A.2 reported **47 sites**, with
`test_comms_render_architecture.py` at **10**. My bare-grep re-derivation gives **11** there (and
48 overall); adding the two wrapped sites gives **50**. I did not reconstruct which line Appendix A
did not count — the re-derived number is what I worked from, per the brief and repo law. Appendix
A's *conclusion* (the map, the five files, the two incoherent-partial receipts, the
ONE-IMPLEMENTATION recommendation) is unaffected and was correct.

### 1.2 AFTER — every residual hit, file:line, individual verdict

Post-edit `grep -rn "next heartbeat"` (bare) + instrument B. **"All remaining hits are X" is banned
output** — so, one at a time.

**In-scope files (my writable set):**

| file:line | verdict |
|---|---|
| `server.py:5068` | **AMENDED** — tail-1 scoped literal, now `…surfaces at their next heartbeat or drain` |
| `server.py:5079` | **AMENDED** — tail-2 unscoped literal |
| `server.py:5093` | **AMENDED** — tail-3 scoped literal, now `…at next heartbeat or drain — …` |
| `server.py:5106` | **AMENDED** — tail-3 unscoped literal |
| `server.py` tail-1/2 branch comment (wrapped) | **AMENDED** — see dev-1 / §6.1 |
| `server.py` tail-3 branch comment (`ackers see it at heartbeat`) | **AMENDED** — see dev-1 / §6.1 |
| `test_comms_promise_registry.py` | **ZERO residual hits** — all 12 executable copies now read the shared constants |
| `test_comms_tool.py:2941` | **AMENDED** — docstring quoting the ugly `skew: 0 …` line; prose, cannot reference a constant |
| `test_comms_tool.py` (18 executable sites) | **ZERO residual hits** — all read the shared constants |
| `test_comms_render_architecture.py:217,219,220` | **AMENDED** — the (standing × has-unbriefed) → tail comment map; prose |
| `test_comms_render_architecture.py:242,243` | **THE ONE HOME** — `_SKEW_SURFACING_TEACH` / `_SKEW_ACKER_TEACH` |
| `test_comms_render_architecture.py:486` | **LEFT DELIBERATELY** — *"a prior acker's NEXT heartbeat (through the real tool)"* describes the ACTION this test drives (it drives `action="heartbeat"`), not the served wording. Amending it would make the docstring lie about the test |
| `test_comms_render_architecture.py` docstring quote (was wrapped) | **AMENDED** — now quotes `…next heartbeat or drain`, with a sentence saying the heartbeat leg is the one driven here and the drain leg (FK-6) is pinned with the drain surface |
| `test_comms_render_architecture.py:498` | **AMENDED** — the assertion MESSAGE (repo law: a message that promises a different check than the assertion performs is a false gate; this one now names both verbs and says which leg failed) |
| `test_comms_wiring.py` | **ZERO residual hits** — its one site reads the shared constant |

**Out-of-scope residuals (NOT in my writable set — listed, not touched):**

| file:line | what it is | verdict |
|---|---|---|
| `docs/design/2026-07-12-pkt28-c1-semantics.md:24` | the pkt-28 spec's own §9.4 tail inventory ("NINTH") | out of scope — **design doc, states the pre-E-S5(c) wording** |
| `…:905` | a worked-example rendered line | out of scope — same |
| `…:925, 928, 931, 934` | the §9.4 three-tail derivation | out of scope — same |
| `…:961, 963` | first-publish worked examples | out of scope — same |
| `…:1260` | END-TO-END test sketch ("a prior-acker's next heartbeat") | out of scope — and correct anyway: it names the ACTION |
| `docs/plans/v2/02-comms-render-architecture.md:26` | the #103 packet statement, quoting the then-shipped promise | out of scope — **historical quotation, true as history** |
| `docs/plans/v2/03b-design-rulings-r2.md:376` | B4.1's quotation of the shipped promise | out of scope — historical quotation |
| `…:382` | the struck-through keep-the-literal clause | out of scope — already struck |
| `…:1262` | the FK-6 adjudication quoting the shipped promise | out of scope — historical quotation |
| `…:1368` | **the E-S5(c) ruling itself** — it MUST quote both old and new wording | out of scope — **must not be amended** |
| `REPORT-contract-surface-03b-r2.md:203, 207, 457` | the surface author's finding + Appendix A | out of scope — **an archived report is a durable record; amending it would falsify the record** |

**Recommendation to the lead (not applied — outside my writable set):** the two `docs/plans/v2/`
and `docs/design/` files carry the pre-amendment wording as *live design prose*, not as
quotation-with-context (`02-comms-render-architecture.md:26` and the eight
`2026-07-12-pkt28-c1-semantics.md` sites). Under the rename-sweep law those are exactly the
"natural-language surfaces no gate checks". They are historically true (they describe the
pre-E-S5(c) world) but a future reader mining the spec for the served wording will find the retired
sentence. A one-line "superseded by E-S5(c)" banner at each cluster would discharge it; that is the
lead's call, not mine.

## 2. ONE IMPLEMENTATION — the copy count

The repo law (`CLAUDE.md §ONE IMPLEMENTATION`) and Appendix A.5 both required the change to REDUCE
the copy count, not preserve it.

| population | before | after |
|---|---|---|
| **production literals** (the served source of truth) | 4 | **4** (unchanged — see §2.1) |
| **test-side EXECUTABLE copies** (registry keys, proof literals, markers, assertion strings, the regex, the conditional) | **38** | **2** (`_SKEW_SURFACING_TEACH`, `_SKEW_ACKER_TEACH`) |
| **prose copies** (comments, docstrings, an assertion message — cannot reference a constant) | 8 | 6 |

Test-side breakdown of the 38 → 2:

- `test_comms_promise_registry.py` **12 → 0**: 4 registry keys, 4 `PromiseProof.literal=`, 4
  `marker=`. Dict keys are ordinary expressions, so `"…{breakdown}; " + _SKEW_SURFACING_TEACH` is a
  legal key with no f-string brace-doubling; markers use the constants inside their existing
  f-strings.
- `test_comms_tool.py` **18 → 0**: 15 byte-exact assertion tails, 1 regex (now
  `rf"…; {re.escape(_SKEW_SURFACING_TEACH)}"`), 2 branches of the `expected_tail` conditional.
- `test_comms_render_architecture.py` **7 → 2**: `_TAIL_SURFACES` and `_TAIL3_TEMPLATE` are now
  *derived* from the two new constants, and the 5 negative assertions (`assert … not in rendered`)
  reference the constants instead of re-typing the phrase.
- `test_comms_wiring.py` **1 → 0**.

Cross-module import is this repo's established test idiom, not an invention: `test_comms_tool.py`
already carried `from test_render_seam_pins import assert_actions_covered`, and `test_text_hygiene`
/ `test_trace_telemetry` do the same. pytest runs with `--import-mode=importlib` and the tests dir
importable, so the three importers resolve cleanly under `-n auto` (measured — §3).

**The re-open trigger is now discharged STRUCTURALLY.** E-S5(c)'s named trigger — *a THIRD
surfacing verb re-opens the wording; never accrete a verb list past two; at a third verb, reword to
name the mechanism generically* — is written into three places that a future author cannot miss
(the constants' block comment, the registry's block comment, and the production branch comment).
Acting on it is **2 string edits here + 4 production literals**, not a 50-site sweep. The line-142
`⚠ NOT touched here` comment in the registry (which recorded the tree state before this wave) is
**replaced** by that trigger note, as the brief required.

### 2.1 Why production's four literals were NOT collapsed to a shared constant

I checked this rather than assuming it, because the brief asked whether a shared tail-constant is
"structurally cheap". **It is not — it would break the promise-registry instrument.**

`test_comms_promise_registry.py::_scan_render_literals_over_tree` scans `server.py`'s AST and
accepts a `render_line` template only as a plain `ast.Constant` (implicit adjacent-literal
concatenation is already folded by the parser) or a `JoinedStr` canonicalised to `{}` placeholders.
A `"prefix" + _TAIL` template is an `ast.BinOp` whose `Name` operand is resolved only from
assignments **inside the same function** — a module-level constant does not resolve, so the site
lands in the scanner's `unclassifiable` bucket and `test_every_comms_render_literal_is_classified`
goes RED. The `JoinedStr` route is no better: it would rewrite the registry keys from
`{breakdown}`-style named placeholders to bare `{}`, destroying every existing key.

The upside was small anyway: the four literals differ in two dimensions (session-scoped vs not ×
tail-1/2 vs tail-3), so the shared sub-phrases are only 2, and a constant would have taken 4 → 2
copies at the price of the instrument. **Kept as four literals; the registry is what keeps them
honest, and §5's mutation proof shows it still does.**

## 3. The zero-green-broken property

### 3.1 Counts (`uv run pytest -n auto -q --tb=no -p no:randomly`, all four files in one run)

| | baseline (before any edit) | after |
|---|---|---|
| combined | **270 failed, 707 passed** in 10.68s | **270 failed, 707 passed** in 11.54s |
| `test_comms_tool.py` | 255F / 554P | **255F / 554P** |
| `test_comms_promise_registry.py` | 15F / 99P | **15F / 99P** |
| `test_comms_render_architecture.py` | 26P | **26P** |
| `test_comms_wiring.py` | 28P | **28P** |

Per-file baselines re-derived by me and independently equal to Appendix A.3/A.6's measured figures
(255F/554P, 15F/99P, 54 green).

### 3.2 Failure SETS, not just counts

```
$ diff /tmp/es5c_baseline_failures.txt /tmp/es5c_final_failures.txt && echo IDENTICAL
FAILURE SET IDENTICAL TO BASELINE
```
270 names in, 270 names out, zero added, zero removed.

**Same-reason check on the two pins that could plausibly have changed reason** (Appendix A.3
measured both directions of a partial application breaking exactly here):

- `TestEveryCommsRenderLiteralIsClassified::test_every_comms_render_literal_is_classified` —
  **GREEN at baseline, GREEN after** (`1 passed`). This is the pin Appendix A.3's Direction-2
  measured going RED under a registry-only amendment. Amending production and registry together
  keeps it green: production emits four literals and all four are classified (byte-checked
  independently via an AST read → `OK` on all four).
- `TestEveryCommsRenderLiteralIsClassified::test_no_dead_registry_entries` — **RED at baseline, RED
  after, for the SAME reason**: its dead list is 18 entries, all of them packet-03's unbuilt
  `_render_comms_drain` / `_render_comms_ack` / `_render_comms_send` literals. **None of my four
  skew literals appears in it** — i.e. the change added zero new dead entries, which was the
  specific regression Appendix A.3 warned about.

## 4. Gates

```
$ uv run ruff check .
All checks passed!

$ ./scripts/typecheck.sh
Found 92 errors in 2 files (checked 149 source files)
typecheck: loremaster FAILED
```
92 is **exactly** the figure Appendix A.6 measured before this wave — unchanged. Both files are the
known RED 03b contract files (`test_comms_tool.py`, `test_comms_promise_registry.py`), and every
error is an `attr-defined` on an unbuilt `_render_comms_*` / a param the unbuilt signature lacks.
**`loremaster/loremaster/server.py`, `test_comms_render_architecture.py` and `test_comms_wiring.py`
contribute ZERO errors**, and no error mentions `_SKEW` (grepped) — so the cross-module import of a
private test constant is clean under mypy.

## 5. Mutation proofs — sharing proven by mutation, never by inspection

Method: the real tree was mutated with a `cp -a` **content** backup, and restored from content with
`md5sum -c` proving byte-exactness after each leg (repo law — an MD5 list is a detector, not a
backup, so the content came first). No scratch copy was used, so the #140 provenance hazard does not
arise; the code under test is the working tree itself.

```
$ md5sum -c /tmp/es5c_backup/pre.md5      # after every restore
loremaster/tests/test_comms_render_architecture.py: OK
loremaster/loremaster/server.py: OK
```

**M1 — mutate the ONE shared constant `_SKEW_SURFACING_TEACH` (prefix `MUTANT `).**
270F → **293F**. The 23 new failures, by module:

| module | new REDs |
|---|---|
| `test_comms_tool.py` | 16 |
| `test_comms_promise_registry.py` | 3 |
| `test_comms_render_architecture.py` | 3 |
| `test_comms_wiring.py` | 1 |
| tests that STOPPED failing | **0** |

**All four modules move together — that is the DRY proof.** A module that had kept a private copy
would have stayed green here; none did.

**M2 — mutate `_SKEW_ACKER_TEACH`.** 270F → **278F**: 3 registry, 3 tool, 2 architecture. (Fewer
sites reference the acker tail, which is correct — only tail 3 uses it.)

**M3 — the independence control (the one that matters most).** Restore everything, then mutate
**production alone**: `…surfaces at their next heartbeat or drain` → `…or DRAINAGE` in one literal,
touching no test. Result:

```
FAILED …::test_every_comms_render_literal_is_classified
  a comms render template literal is UNCLASSIFIED …
  _render_comms_brief_publish:5077: 'skew: {behind} … surfaces at their next heartbeat or DRAINAGE'
```
The registry still catches production drift and **names the drifted literal**. Deriving the registry
keys from a test-side constant did NOT create a self-satisfying loop: production cannot import the
constant, so the keys remain an independent transcription and drift in **either** direction is RED.
M3 is also the positive control for M1/M2 — it shows the instrument firing on a differently-broken
input, for a different reason.

## 6. Judgment calls, deviations and flags

### 6.1 DEVIATION — two production COMMENTS amended (both readings, per brief-base §2)

The brief's writable set says `server.py` "(ONLY the tail-literal sites or their one shared build
point — nothing else in production)". That sentence admits two readings that produce different
edits, so per brief-base §2 both are written down rather than picked silently:

- **(a) literals-only** — "tail-literal sites" means the four string literals. The two adjacent
  comments stay as-is.
- **(b) the site including its governing prose** — the two comments sit *inside* the amended
  branches and exist solely to explain when those literals' promise comes true.

**I picked (b), and amended exactly two comments:**
1. the tail-1/2 branch comment — was *"the notice truly surfaces universally at every agent's next
   heartbeat"* → now *"…next heartbeat or drain"*, plus the E-S5(c) citation and the re-open trigger;
2. the tail-3 branch comment — was *"ackers see it at heartbeat"* → now *"ackers see it at heartbeat
   or drain"*.

Reasons: leaving them is precisely the audited defect class (`CLAUDE.md` §rename/reshape sweeps —
"natural-language surfaces whose consistency with code no gate checks"); the edits are
zero-behaviour and contribute zero gate delta; and the re-open trigger belongs where the next author
editing these literals will actually see it. **If the lead meant reading (a), revert those two hunks
— nothing else depends on them.** Note comment #2 contains `at heartbeat`, not `next heartbeat`, so
neither sweep instrument would ever have surfaced it: I found it by reading the block.

### 6.2 Judgment — where the shared constants live

The structurally ideal home is a shared non-test helper module. The three candidates in
`loremaster/tests/` are `_comms_fakes.py` (imported by tool / registry / architecture but **not**
wiring) and `render_injection_scaffold.py` (tool + wiring only) — **neither covers all four**, and
both are **outside my writable set** anyway. So I extended the seam the brief named
(`test_comms_render_architecture.py`, which already owned `_TAIL_SURFACES` / `_TAIL3_TEMPLATE`) and
imported from it. **FLAG for the lead:** if a `_comms_constants.py`-style module is ever created,
these two names are its first tenants; that is a one-line move and would drop the "a test module is
three other modules' dependency" smell.

### 6.3 ⚠ FLAG — the amended production prose is an OVER-claim until FK-6 is BUILT

E-S5(c) calls the amendment "strengthen-only … strictly MORE true". **That is true of the finished
packet, not of this commit in isolation.** FK-6 (drain also serves the shared skew block) is
*ruled*, not *built* — packet 03b is still in its RED contract phase, and `_render_comms_drain` does
not exist yet (it is one of the 18 unbuilt literals in §3.2's dead list). So between this commit and
03b's GREEN phase, `server.py` promises a `drain` surfacing that the shipped code does not perform —
the trust-doctrine failure in the opposite direction.

Why I applied it anyway rather than stopping: Appendix A.3 **measured** that every partial
application leaves the tree incoherent, and the lead's brief authorizes the amendment as one
coherent change now, before the adversary phase, so the adversary grades the final wording. The
exposure is bounded — an un-deployed feature branch.

**What the lead should carry forward:** this wording and FK-6's build must ship in the **same
packet**. If 03b's build phase is cut short, descoped, or FK-6 is dropped, **this amendment must be
reverted** — otherwise a served surface ships teaching a verb that does nothing. That is a named
decision point, not a hope. (It also strengthens the C5(c) battery's ruled skew-in-drain leg: that
leg is now the thing that makes this prose true, so it is not optional.)

### 6.4 Flag — Appendix A's site count, and the instrument that beats a bare grep

§1's discrepancy (47 vs my 48 bare / 50 wrap-tolerant) is reported not to score a point but because
Appendix A.4 is itself a confession about an inherited count, and the same trap has a second floor:
**a bare grep cannot see a wrapped phrase.** Two of the 50 sites — one in production — were invisible
to the exact instrument the rename-sweep law prescribes. Suggested addition to that law: for a
**phrase** (as opposed to a symbol), the sweep pattern tolerates intervening line-continuation noise
(`\s`, quotes, `#`, `\`), because prose wraps and symbols do not. The regex used here:

```
next[\s"'#\\]*heartbeat
```

### 6.5 Tool honesty

`lore_*` was **not** used for this task; the work was a whole-repo textual sweep for a
**non-symbol prose phrase**, which is sanctioned fallback case (b) in the repo's dogfood protocol
("non-symbol textual seams (config keys, log event names, prose in string literals)"). Saying so
out loud, per that protocol. No friction row filed — the tool was not routed around, it was the
wrong tool for a prose sweep.

### 6.6 Scope — nothing else was touched

`git status` after the work shows exactly my five files modified. The parallel author's files
(`_surreal_fakes.py`, `_surreal_harness.py`, `test_comms_schema.py`, `test_surreal_*.py`,
`test_trace_telemetry.py`) were never opened; the lead committed them mid-run as `bb64324` /
`c738d2f`, which is why they no longer appear as dirty. No git state was mutated by me.
