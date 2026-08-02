# REPORT-adversary-c3-1 — contract **C3** (`loremaster/tests/test_comms_footer.py`) graded by EXECUTION

**brief-base v9 read**
**brief project v7 read**

## SUMMARY BLOCK

```
state: done
VERDICT: ⛔ CONTRACT INSUFFICIENT
P1 HEADLINE — 26 DISTINCT WRONG BUILDS PASSED ALL 48 PINS (§2). Including: the footer's
  COUNTS swapped, or replaced by a constant 1/1 (W2/W12) · MessageLedger.pending_traffic
  DELETED FROM PRODUCTION ENTIRELY (§2.2) · the footer REPLACING the tool's answer instead
  of appending it (W6) · six of ~nine WRITE actions never footering (W5/W10/W24) · an inbox
  with 0 unread and 3 UNACKED DIRECTIVES serving no footer (W23) · session= ignored (W4).
  Six controls FIRED (C-B, C-C, C-D, refbuild-M3 repro, W1, a self.-call revert), so the
  GREENs are measurements, not a broken instrument.
QUANTIFIER TABLE (P1b): §3 — 24 invariants classified; 15 GUARDED, every guarded row
  carrying a surviving door-build; 4 invariants have NO pin at all.
MISSING PINS: §4, MP-1..MP-17, each with the test to write and the wrong build it kills.
deviation: my first 11-suite verification run overlapped my own mutations in the same tree
  and was DISCARDED, not reported. The clean re-run is §7.2: 2606 passed / 0 failed (vs
  refbuild's 2607 — the one-test delta is derived and fully explained there, not a defect).
deviation: my C-A control DIVERGED (green) — chased rather than dropped; it became finding
  MP-17. C-D is the working control.
Packages considered: §6 — `ruff` S608 (READ: rule docs + a live run, 113 hits / 15 files)
  vs the hand-rolled AST scanner => keep_with_trigger, trigger named; `unittest.mock`
  AsyncMock(wraps=) vs the hand-rolled registry-read counter => replace (§6.2).
decisions-needed: none held. Every fork is written up; the lead rules.
receipt pointers: headline table §2.1 · the DELETE probe §2.2 · quantifier table §3 ·
  missing pins §4 · perturbation pairs §5 · package diff §6 · claim re-derivation §7 ·
  fakes §8 · sweeps §9 · residuals §10 · instruments (committed paths) §11.
```

---

# §0 · CAPABILITY CHECK (brief-base §4 — first thing in the report)

Everything the brief demanded was reachable. `lore_comms register` succeeded (session
`packet-04b2-wavec`, role `adversary`; brief `project` v7 auto-acked). `ToolSearch "+lore"`
returned the 15-tool lore surface. `scripts/scratch_copy.sh`, `uv`, `pytest`, `ruff` and
`mypy` all ran. **No brief clause was unmeetable.**

One honest tool note (brief-base §4, last bullet): the structural questions in this run —
*"which fixture value reaches which branch"*, *"does this fake carry method X"*, *"which
files does this receiver name-list reach"* — were answered by `Read`, `grep` and **AST
scanning I wrote**, not by lore. That is not a route-around: the lore graph has nothing to
add to *"what does line N of this test file pass"*. `lore_comms` was used for coordination
only. No friction filed, because lore was not the right instrument rather than a failing one.

**Prohibitions honoured:** no repo file edited (this report is my only repo write) · **zero
git write commands** · no worktree · nothing under `scripts/**`, no packet-39 file, and
neither `test_task_read_surface.py` nor `test_query_tasks_bounded.py` touched.

---

# §1 · PROVENANCE — which tree I graded (#140)

`/home/ejprice/scratch-adv-c3`, created by the blessed tool and **re-verified after every
mutation wave**:

```
$ ./scripts/scratch_copy.sh --verify-only /home/ejprice/scratch-adv-c3
scratch copy VERIFIED: /home/ejprice/scratch-adv-c3
  loremaster  -> /home/ejprice/scratch-adv-c3/loremaster/loremaster/__init__.py

$ uv run python -c "import loremaster; print(loremaster.__file__)"
loremaster.__file__ = /home/ejprice/scratch-adv-c3/loremaster/loremaster/__init__.py
```

**Contract under grade:** `loremaster/tests/test_comms_footer.py` at `f6d8e47`, diffed
byte-exact into the scratch tree (`diff` clean against both the repo worktree and
`git show HEAD:`). The repo worktree copy is itself identical to `HEAD`.

**Build under grade:** the reference build from `refbuild-c3-1`'s scratch tree
(`/home/ejprice/scratch-c3-ref`, five modified files) ported in. That tree sits at `a88e7c5`;
`git diff --stat a88e7c5..HEAD` touches **none** of the five files, so the port carries no
drift. Baseline reproduced immediately:

```
$ uv run pytest loremaster/tests/test_comms_footer.py -q -p no:randomly
48 passed in 3.75s
```

**Backups are CONTENT, not hashes** (the 2026-07-14 MD5 near-miss): `/home/ejprice/
scratch-adv-c3-PRISTINE/` holds `cp -a` copies of `server.py`, `messages.py`,
`_message_fakes.py` and the contract. Every mutation restores from content and the restore
is re-verified by `diff -q` (§7.3). I did **not** mutate `/home/ejprice/scratch-c3-ref` —
Ruling 5.3 says keep it as the builder's diff oracle, and it is untouched.

---

# §2 · ⛔ P1 — THE HEADLINE: 26 WRONG BUILDS PASSED ALL 48 PINS

Every row below is an edit to the **reference build** — the build that goes 48/0 — run
against the **unmodified contract**. The driver asserts each edit LANDED before running
(finding #194) and diffs declared-vs-observed both ways.

## 2.1 · The table

| # | wrong build | result |
|---|---|---|
| **W2** | the two counts are **SWAPPED** — 7 unread / 3 unacked serve as *"3 unread and 7 unacked directive(s)"* | **48 passed** |
| **W12** | the counts are a **CONSTANT 1 and 1** whenever anything pends | **48 passed** |
| **W3** | the footer **hand-rolls its own count** and drops R4's `grade = 'directive'` conjunct; `pending_traffic` is never called | **48 passed** |
| **W23** | the footer fires on `unread > 0` **alone** — an inbox with 0 unread and 3 **unacked directives** gets nothing | **48 passed** |
| **W4** | `session=` is **ignored** — `agent=` resolves unscoped | **48 passed** |
| **W5** | findings' four single-item write verbs (`report`/`acknowledge`/`resolve`/`wontfix`) **never footer** | **48 passed** |
| **W10** | tasks' `transition` and `supersede` **never footer** | **48 passed** |
| **W24** | `acknowledge_many` footers **unconditionally**, ignoring L2's write-count | **48 passed** |
| **W6** | the footer **REPLACES** the dispatcher's render — the tool's actual answer is destroyed | **48 passed** |
| **W11** | the footer is appended **TWICE** | **48 passed** |
| **W20** | the footer is **PREPENDED**, above the answer it annotates | **48 passed** |
| **W7** | `unacked_directives` **clamps at 5** (a cap used as a denominator) | **48 passed** |
| **W8** | the footer only fires for identities **containing a hyphen** | **48 passed** |
| **W9** | R8(1)'s teaching degenerates to the **bare offending value**, no guidance | **48 passed** |
| **W17** | the teaching **leaks onto READ paths** (`query`/`rollup`) | **48 passed** |
| **W13** | `session=` **never lands on the tool schema** (R1's *"+session"*) | **48 passed** |
| **W14** | R1's closing sentence never lands — **no footer paragraph in `_INSTRUCTIONS` at all** | **48 passed** |
| **W15** | the one-read **ceiling is broken on `findings` and `claim_task`**, kept on `tasks` | **48 passed** |
| **W16** | the resolver falls back to `candidate.startswith(registered_name)` | **48 passed** |
| **C-A / W18** | link 2's in-code guard `if row.name != name` is **DELETED** | **48 passed** |
| **W19** | an **AMBIGUOUS** (registered-in-two-sessions) `agent=` is taught *"is not registered"* | **48 passed** |
| **W21** | the **RESOLVED** caller's footer loses its drain imperative | **48 passed** |
| **W22** | only the **FALLBACK** render is a bare f-string (the authenticated one stays `Rendered`) | **48 passed** |
| **W25** | `COMMS_FOOTER_PREFIX` becomes `"zzz"` — invisible by construction (the contract imports it) | **48 passed** |
| **DEL** | **`MessageLedger.pending_traffic` DELETED from production** (§2.2) | **48 passed** |
| **W1** | the counts are removed from the template | 12 failed — **but see §2.3: not a C3 assertion** |

## 2.2 · The single most damning probe: delete the seam

SECTION D is the *"ONE IMPLEMENTATION"* section. Its docstring instructs slice C2 to CALL
`MessageLedger.pending_traffic` and says *"PROVE SHARING BY MUTATION"*. So I deleted the
production method outright:

```
LANDED: production MessageLedger.pending_traffic DELETED
................................................                         [100%]
48 passed in 1.85s
```

**The seam the section exists to define need not exist in production.** Cause: `_pending_
traffic_for` builds a `FakeMessageLedger` (`_message_fakes.py:143` — an independent class,
**not** a subclass of `MessageLedger`) and calls the method **on the fake**. Every SECTION D
pin grades a fake `refbuild-c3-1` wrote itself. The helper's own docstring —
*"Driven against the REAL ledger class's contract via the adversarial fake, so a build that
satisfies this by counting in the SERVER rather than at the ledger seam fails here"* — is
**false as written**: W3 counts in the server and passes.

This is finding #94's shape verbatim (*"every pin tested a new method nothing required the
code to CALL"*), one level worse — here nothing requires it to **exist**.

## 2.3 · Why W1 is not a counter-example (P0 honesty)

W1 (delete `{unread}`/`{unacked}` from the template, leave the kwargs) goes RED — but the
failure is `RenderSafetyError` from `loremaster.render`'s own **unused-kwarg typo guard**,
not from any C3 assertion. **W2 proves the point cleanly**: swap the two values, both
placeholders still consumed, render seam satisfied, numbers wrong — 48 passed. **C3 asserts
nothing whatsoever about the footer's numeric content.**

## 2.4 · P0 — the controls that FIRED (so the GREENs above mean something)

| control | mutation | result |
|---|---|---|
| **C-B** | the charset gate in front of the registry read removed | **2 failed** — the charset-FAIL budget row + the gate leg |
| **C-C** | the footer built as a bare f-string (authenticated path) | **1 failed** — `test_the_footer_helper_returns_Rendered_not_a_bare_str` |
| **C-D** | resolution falls back to `registered.startswith(candidate)` | **1 failed** — `test_the_fallback_matches_EXACTLY_never_heuristically` |
| **M3-repro** | per-attribution SCAN on the tasks path | **1 failed** — `test_a_SECOND_attribution_is_NEVER_consulted_after_the_first` |
| **self.-revert** | one `AppContext._m(self,…)` reverted to `self._m(…)` | **2 failed** |
| **W1** | template placeholders removed | **12 failed** |

Six independent RED demonstrations. The instrument sees defects; the 26 GREENs are the
contract's silence, not mine.

⚠ **My C-A control DIVERGED (came back GREEN) and I chased it rather than dropping it.**
refbuild's M1 mutates the *lookup*; C-A mutated the *post-check*. That divergence is
itself finding **MP-17** — and it is the reason C-D exists.

---

# §3 · P1b — THE QUANTIFIER TABLE (every invariant, every guarded row with a receipt)

∀ = quantified over the unit's inputs. **GUARDED** = conditioned on the failure mode /
world the author happened to construct. **NONE** = no pin exists.

| # | invariant | class | receipt (door-build, or the pin that killed the door) |
|---|---|---|---|
| I1 | the footer is `Rendered`, not bare `str` | **GUARDED** — authenticated path only | **W22 GREEN** (fallback render as bare f-string) |
| I2 | a hostile identity cannot reach the footer | **GUARDED** — one hostile value, closed by construction | no forgery door found; the render always emits `row.name`. **But I2 rests on I11/I17 — see those rows.** |
| I3 | the footer is the REGISTERED name, not the raw caller string | ∀ over the padded fixture | no door found (belt pin; `row.name` is returned unconditionally) |
| I4 | the footer stays ONE line | ∀ (sanitise_line collapses) | no door found |
| I5 | a footer appears IFF the call actually **WROTE** | **GUARDED** — 2 of ~9 write actions driven | **W5, W10, W24 GREEN** |
| I6 | a LOSING claim never footers | ∀ over the real CAS outcome, with control | no door found — genuinely fate-forced |
| I7 | a batch footers IFF ≥1 item wrote | **GUARDED** — `resolve_many` only | **W24 GREEN** (`acknowledge_many` unconditional) |
| I8 | no traffic ⇒ no footer | **GUARDED** — only (7,3) and (0,0) constructed | **W23 GREEN** ((0,3) invisible) |
| I9 | ≤ 1 registry read per call | **GUARDED** — `AppContext.tasks` only | **W15 GREEN** (scan on findings/claim_task) |
| I10 | the charset gate sits in FRONT of the read | **GUARDED** — tasks only | **W15 GREEN**; C-B RED on tasks |
| I11 | the fallback matches EXACTLY, never heuristically | **GUARDED** — one direction | **W16 GREEN**; PB2 pair proves it (§5.2) |
| I12 | an omitted+unresolvable attribution ⇒ silence | ∀ over the three budget worlds | no door found |
| I13 | a supplied+unresolvable `agent=` TEACHES | **GUARDED** — "unregistered" is the only cause | **W19 GREEN** — ambiguity walks the same door and is told a FALSEHOOD (§4, MP-6) |
| I14 | the teaching carries no counts | ∀ | no door found |
| I15 | the teaching does not appear on READS | **NONE** | **W17 GREEN** |
| I16 | the fallback footer is third-person, no imperative | ∀ over the fallback fixture | no door found |
| I17 | the RESOLVED footer MAY be directive | **GUARDED** — only *"the two renders differ"* | **W21 GREEN** |
| I18 | the two counts are counted separately | **GUARDED** — over the FAKE only | **DEL probe GREEN** (§2.2) |
| I19 | a SIGNAL is never an unacked directive | **GUARDED** — over the FAKE only | **W3 GREEN** (server-side re-derivation drops the conjunct) |
| I20 | a cap is a WINDOW, not a denominator | **GUARDED** — over `unread` only | **W7 GREEN** (`unacked` clamped) |
| I21 | the teaching lands via the declared allowlist | **GUARDED** — negative only, no positive control | **W14 GREEN** (no paragraph at all) |
| I22 | #219's false rationale is gone | **GUARDED** — 3 of 4 named sites | §9.1: `test_comms_tool.py:4905` unpinned |
| I23 | no comms identity in query TEXT | **GUARDED** — receiver NAME-LIST | §6.1: `memory/ledger.py` never scanned |
| I24 | the `agent` description is SHARED | ∀ over the three tools | no door found ✅ |
| **N1** | **the footer renders the LEDGER'S counts** | **NONE** | **W2, W12 GREEN** |
| **N2** | **the footer is APPENDED, once, at the end** | **NONE** | **W6, W11, W20 GREEN** |
| **N3** | **`session=` scopes resolution and exists on the schema** | **NONE** | **W4, W13 GREEN** |
| **N4** | **the footer works for any legal identity shape** | **NONE** | **W8 GREEN** |

**15 of 24 named invariants are GUARDED, every one with a surviving door-build. Four
load-bearing properties have no pin at all.**

---

# §4 · MISSING PINS — the test to write, and the defect it catches

Each is a pin the author can go write. Ranked.

### MP-1 ⛔ BLOCKER — `test_the_footer_RENDERS_THE_LEDGERS_TWO_COUNTS`
**Write:** drive the resolved-caller dispatcher path and assert the served footer line
carries **both numbers in their correct roles** — e.g.
`re.search(rf"\b{UNREAD_COUNT}\b[^0-9]*unread", footer)` and
`re.search(rf"\b{UNACKED_DIRECTIVE_COUNT}\b[^0-9]*unacked", footer)` — **plus a second
parametrised leg at a DIFFERENT pair** (say 4 / 9) so a hard-coded literal fails.
**Catches:** W2 (swapped), W12 (constant 1/1), and the whole "the footer says nothing
useful" family. Today the contract asserts *nothing* about the footer's numeric content;
its entire purpose is un-pinned.

### MP-2 ⛔ BLOCKER — `test_the_footer_COUNTS_THROUGH_MessageLedger_pending_traffic`
**Write:** (a) spy the harness's `message_ledger.pending_traffic` and assert it is called
**exactly once** per footered write, with `agent_id=` **the registry row's id**; (b) an
existence/signature pin on the PRODUCTION class
(`inspect.signature(MessageLedger.pending_traffic)`), so the fake cannot stand in for it;
(c) assert `FakeMessageLedger.pending_traffic`'s signature matches production's.
**Catches:** W3 (a private re-derivation dropping R4's `grade='directive'` conjunct) and
the DELETE probe (§2.2) — today `MessageLedger.pending_traffic` need not exist, which
makes C2's instruction to *call* it unenforceable and SECTION D's ONE-IMPLEMENTATION
claim vacuous.

### MP-3 ⛔ BLOCKER — `test_EVERY_write_action_footers` (parametrised over the write set)
**Write:** parametrise the "wrote ⇒ footer" leg over **every** write action of each
dispatcher: `tasks` {create, create_many, transition, supersede} · `findings` {report,
acknowledge, resolve, wontfix, resolve_many, acknowledge_many} · `claim_task` {win}.
Derive the set from the dispatcher's own `_*_ACTIONS` constants so it cannot drift.
**Catches:** W5, W10, W24 — six of roughly nine write actions can silently never footer.

### MP-4 ⛔ BLOCKER — `test_UNACKED_ONLY_traffic_still_footers`
**Write:** two more traffic worlds — `(unread=0, unacked=3)` and `(unread=7, unacked=0)` —
both must footer.
**Catches:** W23. The contract constructs only (7,3) and (0,0), so the OR is never
separated from either operand — and the state R4 exists to surface (an unacked directive
owed to a teammate) is exactly the one that disappears.

### MP-5 — `test_the_session_scopes_the_footers_identity` + a schema leg
**Write:** (a) SECTION H asserts all three tools expose a `session` parameter carrying the
shared description; (b) register ONE name in TWO sessions with **different inboxes**, call
with `agent=name, session=<one>`, and assert the counts are that session's.
**Catches:** W4 (session ignored → the footer reports another agent's inbox to the caller —
R1's named hazard) and W13 (R1's *"+session"* never lands).

### MP-6 — `test_an_AMBIGUOUS_agent_is_taught_the_TRUTH`
**Write:** register one name in two sessions, call with `agent=` and **no** `session`;
assert the teaching does **not** contain `"is not registered"` and **does** name the
ambiguity plus the fix (`session=`).
**Catches:** the served falsehood measured in §8.2 — a REGISTERED agent told *"agent=… is
not registered — register it with lore_comms action=register, or fix the spelling"*. R8(1)
demands the teaching; the contract's only assertion is `typo in served`, so false prose
satisfies it. This is a trust-doctrine defect on a surface whose whole job is teaching.

### MP-7 — `test_the_footer_is_APPENDED_exactly_once_at_the_END`
**Write:** `assert served.splitlines()[-1].startswith(COMMS_FOOTER_PREFIX)`; assert exactly
one footer line; assert the underlying render survives (e.g. `"created task" in served`).
**Catches:** W6 (the footer *replaces* the tool's answer), W11 (doubled), W20 (prepended).

### MP-8 — the budget/ceiling worlds on the OTHER TWO dispatchers
**Write:** run `READ_BUDGET_WORLDS` and the second-attribution ceiling leg through
`AppContext.findings` (attributions `(actor, created_by)`) and `AppContext.claim_task`
(`(owner,)`).
**Catches:** W15. Today `findings` and `claim_task` have **zero** registry-read coverage.

### MP-9 — a SECOND near-miss, in the other direction
**Write:** add `_CHARSET_LEGAL_SUPERSTRING = OWNER_VALUE + "x"` and a leg asserting it does
not resolve.
**Catches:** W16 (`candidate.startswith(registered)`). Proven with both legs in §5.2.

### MP-10 — the type pin on the FALLBACK render
**Write:** use the already-defined-but-DEAD helper `_footer_for_owner` and assert
`type(...) is not str` / `isinstance(..., Rendered)`.
**Catches:** W22. The fallback is the path carrying a value matched against **free text** —
the higher-risk of the two — and it is the one with no type pin.

### MP-11 — a POSITIVE CONTROL for SECTION E
**Write:** assert `_INSTRUCTIONS` contains a paragraph naming `agent=` and the three tools,
and that the same paragraph is declared in `test_comms_tool._DECLARED_NON_COMMS_PARAGRAPHS`.
**Catches:** W14. SECTION E is a purely negative pin — the exact "measuring the absence of
an answer" shape the contract itself warns about three sections earlier.

### MP-12 — an over-cap fixture for `unacked_directives`
**Write:** a second SECTION D leg with `unacked=66`.
**Catches:** W7 — *"a cap is a WINDOW, not a DENOMINATOR"* is currently pinned over one of
the two counts.

### MP-13 — parametrise the dispatcher legs over CALLER_A **and** CALLER_B
**Write:** `@pytest.mark.parametrize("caller", [CALLER_A, CALLER_B])` on the resolved-caller
legs.
**Catches:** W8. The file's own header comment claims *"identities here vary in name,
session AND shape, and the parametrised legs below sweep them"* — **no parametrised leg
sweeps them**; `CALLER_B` appears at exactly one line (1068, the charset-validator control)
and never reaches a dispatcher. This is the file's stated anti-monoculture discipline
not applied to the file's own dispatcher fixtures.

### MP-14 — the teaching's CONTENT and its REACH
**Write:** assert the teaching names a remedy (register / spelling), and assert no teaching
line appears on `query`/`rollup`.
**Catches:** W9, W17.

### MP-15 — extend #219's false-rationale scan over the TEST tree
**Write:** an AST/text pin over `loremaster/tests/*.py` docstrings for
`FALSE_RATIONALE_MARKERS`.
**Catches:** the 4th of #219's four named sites (`test_comms_tool.py:4905`) — the contract's
own SECTION F header claims four sites and pins three (§9.1).

### MP-16 — the RESOLVED footer's imperative
**Write:** assert `"action=drain" in resolved_footer` (the converse of the fallback leg).
**Catches:** W21 — R8's split exists to let the authenticated path be actionable; the
current control only requires the two renders to *differ*.

### MP-17 — link 2's in-code guard
**Write:** call `_resolve_footer_identity` directly against a **deliberately lenient**
registry double whose `get_agent` returns a row whose `name` differs from the argument, and
assert `None`.
**Catches:** C-A / W18 — `if row.name != name: return None`, which the build's own docstring
calls *"the link, and why this check is a guard rather than a formality"*, can be **deleted
with all 48 green**. Link 2 is today held by the FAKE registry's exactness, not by anything
the builder writes. ⚠ This also bounds §3's I2: the forgery closure's middle link has no
in-code pin.

---

# §5 · P2 — FIXTURE DISCRIMINATION, WITH PERTURBATION AND CORRECT-BUILD CONTROLS

Each perturbation runs three legs: **leg 0** original contract + wrong build (non-vacuity),
**leg A** perturbed contract + wrong build, **leg B** perturbed contract + CORRECT build
(the control that stops a botched expected value reading as a finding).

## 5.1 · Verdicts, one per load-bearing fixture

| fixture | verdict |
|---|---|
| `UNREAD_COUNT=7` / `UNACKED_DIRECTIVE_COUNT=3` | **DISCRIMINATES at the seam, DECORATION at the dispatcher.** The coprime/distinct reasoning is real for SECTION D. But no dispatcher-level assertion ever reads either number (W2/W12), so at the footer they are arbitrary. |
| `over_cap = 66` | **DISCRIMINATES for `unread` only.** W7 clamps `unacked` at 5 and passes. |
| `_CHARSET_LEGAL_NEAR_MISS` (a proper prefix) | **DISCRIMINATES in ONE direction.** §5.2. |
| `f"  {OWNER_VALUE.upper()}  "` (the charset-gate leg) | **DISCRIMINATES** — C-B reddens it. Correctly renamed by refbuild after its meaning changed. |
| `HOSTILE_OWNER` | **DISCRIMINATES weakly.** It cannot resolve for a *charset* reason, so the leg passes on any build that resolves nothing at all; the positive control is what rescues it. Verdict: acceptable AS PAIRED. |
| `BATCH_SIZE=5` with fates 0/1/4/5 | **DISCRIMINATES** — the 1-of-5 and 4-of-5 legs genuinely kill `write_count == len(items)`. The best-shaped fixture in the file. |
| `CALLER_A` at every dispatcher call site | **MONOCULTURE — DOES NOT DISCRIMINATE.** W8. See MP-13. |
| `pending=True/False` (a single boolean for both counts) | **DOES NOT DISCRIMINATE** between the two counts. W23. See MP-4. |
| `_footer_harness(...)` returning a `SimpleNamespace` | **PRESCRIBES AN ARCHITECTURE** — §10, R-3. |

## 5.2 · PB2 — the near-miss fixture, both legs (the clean pair)

```
PB2 — link 2's near-miss: perturb the PREFIX fixture into a SUFFIX-EXTENSION
  leg 0  ORIGINAL contract  + WRONG build   -> RED=False   5 passed
  leg A  PERTURBED contract + WRONG build   -> RED=True    1 failed, 4 passed
  leg B  PERTURBED contract + CORRECT build -> RED=False   5 passed
```

Wrong build = `name.startswith(registered_name)`. The original fixture cannot see it (leg 0
green); a **one-token** fixture change sees it (leg A red); and the changed fixture is
satisfiable by the correct build (leg B green). That is MP-9, fully evidenced.

## 5.3 · PB1 / PB3 — reported honestly as INCONCLUSIVE

Both perturbations targeted SECTION D, and both **leg 0s came back GREEN because my
production mutation never executed** — SECTION D drives the FAKE. That miss is not noise:
it is how I found §2.2. The perturbation question for those two fixtures is superseded by
MP-2 (a fixture that grades a fake cannot discriminate a production build at all).

---

# §6 · P-PKG — MY TABLE, BUILT FIRST, THEN DIFFED

I enumerated C3's mechanisms before opening `REPORT-refbuild-c3-1.md`'s
`Packages considered:` line.

| mechanism C3 specifies | library evaluated | what I **READ** | verdict |
|---|---|---|---|
| footer line assembly + placeholder substitution | `loremaster.render.render_line` (in-tree) | its source + the four-instrument docstring; the `RenderSafetyError` unused-kwarg guard fired live in W1 | **replace** (in-tree, correct) |
| control-char sanitisation | `loremaster.sanitise.sanitise_line` | signature `str -> SafeLine`; measured behaviour on `HOSTILE_OWNER` | **replace** (in-tree) |
| identity charset check | stdlib `re.fullmatch` + `AGENT_NAME_PATTERN` | `loremaster/agents.py` pattern definition | already stdlib — no action |
| the two-count value object | `pydantic` `BaseModel` + `ConfigDict(extra="forbid")` | the house idiom in `messages.py` | **replace** (package in use) |
| whole-word case-insensitive match (`_has_word`) | stdlib `re` | the lookaround form is equivalent to `\b…\b` for word-char-delimited patterns | **bespoke, ACCEPTABLE** (trivia, not policy) |
| **query-text interpolation scan (SECTION F)** | **`ruff` S608** (flake8-bandit) — already installed, ruff 0.15.15 | ran it live: `--select S608` over the four members ⇒ **113 findings across 15 files**; and I diffed its file reach against `QUERY_RECEIVERS` (§6.1) | **`keep_with_trigger`** — trigger in §6.1 |
| **the registry-read counter (`_footer_harness`)** | **stdlib `unittest.mock.AsyncMock(wraps=…)`** | `AsyncMock` records `call_args_list`; the hand-rolled `_counting` closure records **only a count** | **replace** — §6.2 |

## 6.1 · The S608 diff — and a REAL reach gap it found in one command

`ruff`'s `S608` is **receiver-blind** — precisely the property the repo's six-defeats lesson
says a name-list lacks, and precisely the bound SECTION F states about itself (*"its
receiver set is a NAME LIST … a module spelling its query seam differently is invisible to
it"*). I measured the two reaches:

```
contract scanner: sites=123  doors=10          (122 at repo HEAD — I re-derived it: EXACT MATCH)
files the contract's receiver NAME-LIST reaches: 16
files ruff S608 flags:                          15
files S608 sees that the name-list NEVER SCANS:  1
    loremaster/loremaster/memory/ledger.py
```

**Individual verdicts on the gap** (no "the rest look fine"):

* `loremaster/loremaster/memory/ledger.py:151` — an **SQLite** `INSERT … ON CONFLICT` via
  `self._connection.execute(...)`. Receiver `execute` is absent from `QUERY_RECEIVERS`.
  Interpolations are `_COLUMN_*` **module constants**; `memory_id`/`text`/`metadata_json`/
  `refs_stamp` all travel as `?` bind params. **SAFE — no comms identity.**
* `loremaster/loremaster/memory/ledger.py:174` — the sibling `SELECT`. Same shape, **no
  caller value at all**. **SAFE.**

So the gap is benign **today** — but it is a whole SECOND STORE TECHNOLOGY that SECTION F's
invariant structurally cannot see, and it is wider than the bound the contract states for
itself (which names `scout.py`, a SurrealDB seam, as the precedent). And the served
`ValueError` prose SECTION F repairs will teach agents *"every comms identity travels as a
bound parameter"* — a claim over a set the pin does not cover.

**Verdict `keep_with_trigger`, and the trigger, named:** do **not** adopt S608 tree-wide —
113 hits against this codebase's `f"SELECT … FROM {TABLE}"` idiom is exactly the false-
positive rate that gets an instrument switched off (this repo's own threat-model law).
**Re-open the moment either happens:** (i) `QUERY_RECEIVERS` is ever defeated by a new
seam spelling — S608 in a targeted, per-file form is the receiver-blind fallback that
already exists; or (ii) any identity-bearing value appears in `memory/ledger.py` or another
non-Surreal store seam.

## 6.2 · The counter that cannot see arguments — and why it matters here

`_footer_harness`'s `count_registry_reads` wraps `registry.get_agent` in a closure that
increments an int and **discards `*args, **kwargs`**. `unittest.mock.AsyncMock(wraps=inner)`
is stdlib, is a drop-in, and records `call_args_list` — which would make MP-5's
session-scoping pin a two-line assertion (`assert spy.call_args.kwargs["session"] == …`)
instead of an unbuildable one. **The instrument's shape is why W4 is invisible.**

## 6.3 · Diff against `refbuild-c3-1`'s table

Its line reads *"none — no new mechanism … Verdict on all: replace (use in-tree)"* over
`render_line`, `sanitise_line`, `MessageLedger._as_rows/_query`, and pydantic. **Every
entry agrees with mine.** The two rows above are **absent from it** — legitimately, since
both are the CONTRACT's mechanisms, not the build's. They are absent from
`REPORT-contract-04b2-wavec-1.md` too. That is the diff: **the contract's own instruments
were never surveyed.**

---

# §7 · P4 — THE AUTHOR'S CLAIMS, RE-DERIVED (never relayed)

## 7.1 · Reproduced ✅

| claim | source | my measurement |
|---|---|---|
| C3 goes **48 passed / 0 failed** | refbuild §9.4 | ✅ `48 passed in 3.75s` (§1) |
| repo contract == refbuild's scratch contract, byte-identical | refbuild §1 | ✅ `diff` clean |
| **122** query-bearing call sites | contract SECTION F | ✅ **122 at HEAD, exactly.** (I measure 123 in the ported tree; the delta is the ref build's own added `_query` in `pending_traffic` — reconciles.) |
| M1 — a heuristic resolver reddens link 2 | refbuild §9.3 | ✅ as **C-D** (lookup direction). ⚠ **Not** in the post-check direction — C-A/MP-17. |
| M2 — charset gate removed reddens 2 pins | refbuild §9.3 | ✅ **C-B**, exactly the two named |
| M3 — the ceiling leg catches a per-attribution SCAN | refbuild §9.2(b) | ✅ reproduced RED on the tasks path. ⚠ **Only** there — W15. |
| M4 — a bare-f-string footer reddens the type pin | refbuild §9.3 | ✅ **C-C**. ⚠ Authenticated path only — W22. |
| R-5 is a REAL defect | contract SECTION G | ✅ `MessageLedgerError` absent from `AppContext.comms`' docstring at HEAD; the three pre-existing families present |
| Ruling 5.2 world (i) is UNREACHABLE | refbuild §9.1 | ✅ derived independently: every write action requires an attribution argument |

## 7.2 · The 11-suite claim — re-derived, and the one-test delta EXPLAINED

refbuild §9.4 claims **2607 passed, 14 skipped, 3 xfailed, zero failures**. My clean re-run
(pristine tree, provenance re-verified, `-n auto`), measured 2026-08-01 at `f6d8e47` + the
ported reference build:

```
2606 passed, 14 skipped, 3 xfailed in 124.54s (0:02:04)
```

**2606, not 2607** — and the difference is not a discrepancy to escalate. refbuild's tree
sits at `a88e7c5`; mine at `f6d8e47`, and `test_query_tasks_bounded.py` (slice C1's file,
303 diff lines) is one of the eleven. Collected directly at both revisions:

```
my tree (f6d8e47):        41 tests collected
refbuild tree (a88e7c5):  42 tests collected
```

**The delta is exactly one, exactly there.** refbuild's number was right for its tree and
mine is right for HEAD. Skips (14), xfails (3) and **zero failures** all reproduce.

⚠ **Scoped, per the brief: this is NOT a wave-level "gates green" claim.**
`scripts/typecheck.sh` is RED at HEAD from packet 39's unbuilt contract (#306 / #307) — not
mine, not touched. The green above covers exactly those eleven test files in my scratch
tree with the reference build ported in; it says nothing about the canonical typecheck, the
full suite, or any file outside that set.

## 7.3 · Restore integrity

After every wave, content-diffed against the pristine backup:

```
server.py IDENTICAL to pristine
messages.py IDENTICAL to pristine
_message_fakes.py IDENTICAL
contract IDENTICAL to repo worktree(==HEAD)
scratch copy VERIFIED: /home/ejprice/scratch-adv-c3
```

## 7.4 · One claim I could NOT reproduce as stated

**R-12 (`TestBriefAckTeachesAtTheToolSeam`) is ALREADY GREEN at HEAD, against a NO-OP
build.** The class docstring says *"nothing pins that it is taught"* — implying the teaching
is missing. Measured at `f6d8e47`: `lore_comms`' `version` parameter description already
reads *"Legal for any existing version, not just head."* So `"head" in description.lower()`
passes with zero builder work. **The pin is legitimate as a REGRESSION guard** — but its
framing will send a builder hunting for a repair that does not exist, and the residual R-12
claims a gap that is not there. Verdict: **KEEP, RE-FRAME the docstring.**

---

# §8 · P5 — CAN THE DOUBLES FAIL?

## 8.1 · `FakeMessageLedger.pending_traffic` — the fake IS the specification

`_message_fakes.py:143` — an independent class, not a `MessageLedger` subclass. Its
`pending_traffic` was written by `refbuild-c3-1` in the same session as production's, and
its docstring correctly says it is an *"INDEPENDENT count … so this fake stays able to FAIL
a wrong build."* **It can fail a wrong FAKE. It cannot fail a wrong PRODUCTION build**,
because SECTION D never touches production (§2.2). Verdict: the fake is well-written; the
*fixture wiring* is what makes it un-discriminating. MP-2.

## 8.2 · `FakeAgentRegistry` — the double is holding link 2

Deleting the production guard `if row.name != name` leaves 48 green, because the fake's
`get_agent` → `_resolve` is exact. **The contract's exactness property is a property of the
double.** MP-17.

The same double's `AmbiguousAgentError` path is never constructed — and that world produces
a served falsehood. Measured, against the reference build, with the contract's **own**
unmodified harness:

```
loremaster.__file__ = /home/ejprice/scratch-adv-c3/loremaster/loremaster/__init__.py
--- SERVED ---
created task 40e6824e59474e3b81618fe2fc63d749 (status open)
(no pending-traffic line: agent=builder-04b2-wavec-3 is not registered — register it with lore_comms action=register, or fix the spelling)
--- /SERVED ---
carries a footer?           False
claims 'is not registered'? True
the agent IS registered?    True
```

MP-6.

---

# §9 · P6 / P6b — SWEEPS, EVERY HIT INDIVIDUALLY VERDICTED

## 9.1 · P6 — the #219 corpse sweep (bare, anchor-free: `grep -rn "inlined into"`)

| site | verdict |
|---|---|
| `server.py` — `_validate_comms_identities` docstring | **CORPSE, PINNED** by `test_the_charset_DOCSTRINGS_do_not_claim_inlining` ✅ |
| `server.py` — `_validate_comms_charset` docstring | **CORPSE, PINNED** by the same ✅ |
| `server.py` — the served `ValueError` message | **CORPSE, PINNED** by `test_the_served_ValueError_does_not_claim_the_value_is_INLINED` ✅ |
| `loremaster/tests/test_comms_tool.py:4905` (class docstring) | ⛔ **CORPSE, UNPINNED** — MP-15. The ref build repairs it by hand; nothing forces that. |
| `loremaster/tests/test_message_ledger.py:940` | **NOT a corpse** — *"bound param at every site, never inlined into a WHERE"* is the TRUE statement. No action. |
| `loremaster/tests/test_comms_footer.py:1020,1031` | **NOT a corpse** — the detector's own marker constants. No action. |
| `docs/design/2026-07-12-pkt28-c1-semantics.md:691` | **CORPSE in docs** — quotes the false served string verbatim. Out of the contract's scope; **FLAGGED to the lead** (scope law), not dropped. |
| `docs/plans/v2/03b-design-rulings-r2.md:150` | **CORPSE in docs** — states the false rationale as a *ruling*. **FLAGGED**; a future reader greps this and re-installs the false model. |
| `docs/plans/v2/04-comms-blocks-footer.md:155` | **NOT a corpse** — this is the packet correctly naming the defect. No action. |

## 9.2 · P6b — code deleted or replaced

C3 **replaces the shape of two dispatchers**: `AppContext.tasks` / `AppContext.findings`
are split into a thin wrapper + `_tasks_dispatch` / `_findings_dispatch`, and
`_resolve_or_acknowledge_many` changes return type `str → tuple[str, int]`.

Enumerated from the source **before** reading any inventory, then diffed:

| removed/changed behaviour | verdict |
|---|---|
| every dispatch branch's return arity (str → (str, bool)) | preserved-with-pin — the render text is unchanged and its existing suite covers it ✅ |
| `_resolve_or_acknowledge_many`'s header `"{verb} {n} of {m}:"` | preserved — the count it now also returns is the one it already computed ✅ |
| the `# noqa: PLR0911` suppressions relocating to the inner dispatchers | preserved (ruff clean) ✅ |
| **12–15 `self._method(...)` call sites rewritten to `AppContext._method(self, ...)`** | ⚠ **not a behaviour change, but an unpinned architectural one forced by the FIXTURE** — §10 R-3 |
| `AppContext.claim_task`'s positional signature | preserved; new params are kw-only with defaults ✅ |

No Phase-0 removed-behaviour inventory was named in my brief for C3, so the diff above is
against my own enumeration only — stated as a bound, not a clean bill.

---

# §10 · RESIDUALS — every one with an individual verdict

**R-1 · `_footer_for_owner` is DEAD.** Defined at the helper block, called by **zero** pins
(`grep -n "_footer_for_owner"` → one hit, its own `def`). Verdict: **use it** — it is
exactly the vehicle MP-10 needs.

**R-2 · The file's own anti-monoculture comment is FALSE.** *"identities here vary in name,
session AND shape, and the parametrised legs below sweep them"* — no parametrised leg
sweeps `CALLER_A`/`CALLER_B`; `CALLER_B` reaches only the charset validator (line 1068).
Verdict: **fix the comment and/or write MP-13.** A false claim about a fixture's coverage
is the same class as a false claim in served prose.

**R-3 · The `SimpleNamespace` harness PRESCRIBES an architecture.** Because
`_footer_harness` returns a `SimpleNamespace` (not `AppContext.__new__(AppContext)`, the
house idiom `test_blocks_edge.py::_tool_seam` already uses), every internal `self._method(…)`
in the touched dispatchers must be rewritten unbound. **Proven forced:** reverting ONE site
reddens 2 pins (§2.4). My derivation of the size: **25 added `AppContext._…` call lines / 15
removed `self.…` call lines** in the ref build's `server.py` diff; design-sidecar Ruling 5.3
states **23** for the same rider — different scopings, both plausible; I report mine
derived and flag the discrepancy rather than adopting either. Verdict: **the ruling
acknowledges the rider but nothing PINS the design.** Recommend the lead either (a) rule
the unbound style deliberately, or (b) change the harness to `AppContext.__new__` and let
the production churn evaporate. Today a builder is made to churn 15+ production call sites
by a fixture's choice of double.

**R-4 · Required co-edits in files C3 does not name.** The contract cannot go green without
`test_comms_tool.py` (a docstring + a `_DECLARED_NON_COMMS_PARAGRAPHS` entry) and
`test_blocks_edge.py::_tool_seam` (two fake services + two `type: ignore`s). Ruling 5.3
routes both to the builder's brief; `refbuild` kept its `test_blocks_edge` edit
scratch-only. Verdict: **the lead must carry both into the builder's brief verbatim** —
otherwise the builder meets a red pin in a file it was not told it may edit (the documented
C-DEF trap).

**R-5 · `COMMS_FOOTER_PREFIX` is un-pinnable by construction (W25).** The contract imports
the marker, so any prefix — including `"zzz"` — is invisible. Verdict: **CORRECT trade,
state it.** Deriving the marker is right (repo law); the cost is that the footer's opening
bytes are unpinned. If the lead wants it pinned, one assertion on the constant's value in
`test_comms_tool.py` closes it. Not a blocker.

**R-6 · `MINIMUM_SITES_SCANNED = 100` vs a measured 122.** Verdict: **sound as a floor.** A
22-site collapse would pass, but a collapse to "a handful" reddens. Acceptable.

**R-7 · `test_all_three_tools_share_ONE_agent_description` cannot distinguish one shared
constant from three identical literals.** Verdict: **acceptable** — the moment one copy
drifts the pin fires, which is the property that matters. Noted, not a finding.

**R-8 · `_tasks_call_counting_registry` counts `get_agent` only.** The contract states this
bound itself. Verdict: **honestly stated, and Ruling 5.3 makes a second resolution path a
#102 escalation.** Accepted.

**R-9 · No pin covers the `_with_comms_footer` `str()` at the append site (§B5/L1).**
`"\n".join` coerces anyway, so the property is unobservable. Verdict: **unobservable ⇒
un-pinnable; say so rather than implying it is pinned.**

**R-10 · Two docs corpses (§9.1).** Verdict: **escalated to the lead**, outside C3's writable
set. They will teach the false #219 rationale to any future grep.

---

# §11 · THE INSTRUMENTS (brief-base §1 — a deliverable, not scratch)

All four live in `/home/ejprice/scratch-adv-c3/` (disposable by design), so they are
recorded here as **runnable files whose full text is short and whose logic is described
above**; the lead should take them into `scripts/` if the wave wants them re-runnable:

| file | what it establishes |
|---|---|
| `adv_c3_wrongbuild.py` | the driver: pristine restore → **landed-edit assertion** → run → declared-vs-observed diff → restore. Wave 1 (W1–W12). |
| `adv_c3_wave2.py` | the P0 CONTROLS (C-A/C-B/C-C) + W13–W17. |
| `adv_c3_wave3.py` | C-D (the working control) + W18–W21. |
| `adv_c3_wave4.py` | W22–W25, the remaining quantifier doors. |
| `adv_c3_perturb.py` | the P2 three-leg perturbation harness (leg 0 / leg A / leg B). |
| `adv_c3_ambiguity_probe.py` | the served bytes in §8.2, driven through the contract's OWN harness. |

⚠ **If the lead wants these kept, they must be `git mv`'d into `scripts/` before the scratch
tree is discarded** — that is the #278 perversity this protocol exists to stop, and I am
naming it rather than assuming someone will.

---

# ⛔ VERDICT: **CONTRACT INSUFFICIENT**

Twenty-six wrong builds — including one with the production seam **deleted**, one with the
counts **swapped**, one that **destroys the tool's answer**, and six write actions that
**never footer** — satisfy this contract perfectly while fixing nothing or fixing it wrong.
Four load-bearing properties have no pin at all; fifteen more are guarded by the failure
mode their author happened to construct, each with a door-build receipt above.

The contract is not weak work — its SECTION B batch fates, its budget worlds and its
SECTION F controls are among the better-shaped pins in this repo, and its author caught two
C-DEFs in itself. **It is a contract whose two most load-bearing surfaces — the numbers the
footer serves, and the seam it serves them from — are the two it never asserts.**

Route MP-1 through MP-4 back to CONTRACT as blockers; MP-5 through MP-17 as the same pass's
work. **This is the eighth defect the brief told me to assume, and the seventh through
twenty-sixth.**
