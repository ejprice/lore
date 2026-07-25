# REPORT-builder-03b-1-wave3 — packet 03b, the final pre-deploy wave

brief-base v6 read

## SUMMARY BLOCK

- **state:** done-with-deviations. Items 1–4 landed; item 5 was a ruled NO-ACTION. Plus one
  addition I made on my own judgement (§5 W1) after a correction landed mid-wave.
- **verdict:** all five mutation proofs discriminate. **One mutation silently did not RUN** (a bad
  anchor) and I nearly reported its green as a proof — §4.1.
- **gates (final tree, HEAD `daad8ec` STABLE across the whole run):** full suite **6605 passed,
  0 failed, 17 skipped, 3 xfailed** · typecheck **0, all three members, 149 files** · ruff **All
  checks passed** · skill **117 passed** · concurrency **20/20, TOTAL_RUNS_WITH_FAILURES=0**
- ⚠ **A sibling commit landed DURING my first gate run** (`daad8ec`) — reported and interpreted
  rather than hidden (§3.1), and the gates were re-run afterwards. It also changed what I had to
  build (§5 W1).
- **deviations:** W1 I added a `to`/`ack_note` dirty-store class the brief did not list, because the
  mid-wave correction moved the danger there · W2 the trace write path TRUNCATES where message
  pointers REJECT — a policy divergence, with both readings written down
- **decisions needed:** none blocking. One judgement (W1) is stated so it can be reversed cheaply.
- **receipt pointers:** §1 the five items · §2 what I did NOT do · §3 gates + the mid-run commit ·
  §4 mutation proofs incl. the one that did not run · §5 deviations · §6 residuals

---

## 1 — The five items

### Item 1 (C1/D1) — the peek re-ask now CONVERGES

`_render_comms_drain` renders a DIFFERENT SENTENCE for the peek × over-cap cell:

> `+{more} more unread — a peek cannot reach past limit={cap}; re-run without peek=true to consume
> this window, then peek again`

Duplicated `render_line` calls, not a ternary — the AST template pin requires `args[0]` to be an
`ast.Constant`, and the sibling fleet render carries the same shape for the same reason.

**Why a sentence and not a number.** The clamp is right and `total_pending` is right for a peek;
above the cap they are simply not jointly expressible as a `limit=`. A peek stamps nothing, so
`min(total_pending, cap)` advertises the limit the caller just used — a fixed point. Measured on the
shipped build: 100 pending → `[50, 50, 50, 50, 50, 50, 50]`, 50 rows unreachable at any limit.

**The new pin follows the instruction rather than asserting its text.** It obeys what the render
says — dropping `peek` when told to, using the advertised limit when given one — and requires every
counted row to be reached within K rounds. K is a BOUND, not a target: a fixed point never converges
at any K, so a generous K still fails the defect while a rewording does not.

**On sharing (the lead asked me to say which I did and why): I did NOT extract a shared helper.**
Fleet and drain both need "if the re-ask would be a dead end, say something else", but their
MESSAGES legitimately differ — fleet discloses the cap, drain teaches the peek escape — and their
predicates differ too (`shown == cap` vs `peeked and reachable > cap`). Extracting a render for two
call sites whose only commonality is the SHAPE of a decision would be sharing for its own sake, and
the DRY law is about POLICY that must agree everywhere, which this is not. No cheap shared predicate
fell out either: the two conditions read different quantities. The shared rule is named in a comment
at each site.

**Registry:** the new template needed a co-emission EXEMPTION, which is the sanctioned case rather
than a silenced red — the escape renders IFF the drain is a peek, and a peek ALWAYS renders the
peeked header, so no fixture can separate them: one's emit predicate IMPLIES the other's. (Contrast
the committed `_render_send_03b` note, where a distinct fixture VALUE was chosen instead precisely
because that collision was accidental.) Both lines keep their own discriminating NO-EMIT leg.

### Item 2 (C4) — the LIVE dirty-store legs, both tables

`body`'s instrumentation has two parts — an offline DDL pin and a LIVE behavioural pin — and
"mirroring `body` exactly" means both. The design wave shipped only the offline half.

* **`message`** (`TestThePointerBoundsMigrateADIRTYStore`): the §1.6 shape — apply the OLD unbounded
  DDL, write a row under it, apply the new DDL, then assert the bound is LIVE, the pre-existing row
  SURVIVES unrewritten, and a re-apply is a clean no-op. A virgin fixture cannot see any of this by
  construction.
* **`to`/`ack_note`** (`TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge`) — see §5 W1. This one is
  the half that can actually hurt, and the brief did not list it.

### Item 3 (C3/D2/D3/D5) — the stale prose

Four sites in the lead's list, plus C3c which the item header names:

| site | was | now |
|---|---|---|
| `_render_comms_drain` docstring | "the REMAINDER in both slots" | three cases, stated as three because two are not expressible as the third |
| same, `Args:` | `limit` "unused by the arithmetic (the honest re-ask is the remainder, never the cap)" | still unused, for a reason the parenthetical got wrong twice |
| `_render_comms_drain_row` | "refs are uncapped at the ledger" | the ledger bounds them now; this is the DISPLAY half of the same policy |
| `MessageLedger.send` | `Raises:` omitted `MessagePointerError`; `Args:` documented no bounds | both stated, including why `thread` takes a length bound and no charset |
| **C3c** — `TestParamsHashIsTheRuledRecipeAndLeaksNothing` | "the ONLY thing that crosses … the whole privacy boundary … nowhere else" | struck in place, with what the pins DO assert (free text reaches the row only as the digest) |

⚠ **C3c was not in the lead's four-site list** but C3 is named in the item header and C3c is part of
C3. It is a docstring in a class named `…LeaksNothing` making a claim the fix wave already retired
in production — retrievable by an agent asking whether the trace row leaks arguments. Fixed and
disclosed; if only C3a/C3b were meant, reverting is one docstring.

**And I swept from the GREP, not from the report's list**, which is what the round-2 audit says the
fix wave failed to do: `grep -rn "nowhere else\|whole privacy boundary" --include=*.py loremaster/`
now returns only the corrected production copy and four unrelated uses of the ordinary phrase.

### Item 4 (D4) — the trace write path is bounded

`TRACE_IDENTITY_MAX_CHARS = 256` on `tool` / `agent` / `session` / `action` / `transport_session`,
at BOTH layers: the writer truncates, the store ASSERT backstops. See §5 W2 for the policy
divergence and why.

### Item 5 (C2) — NO ACTION, as ruled

`1a6010f`'s message under-describes its contents. History not rewritten; the contents are documented
in two audit reports, my design-wave §1, and now here.

---

## 2 — What I did NOT do

The lead's calibration was explicit — no fourth audit round, do not gold-plate, do not hunt for more
— so the boundary matters as much as the work:

- **No deploy.** No container touched. `:18500` never opened; every probe and test ran against
  `ws://127.0.0.1:18000` on throwaway databases.
- **Did not build**: trace GC/retention, D6's cost-claim docstring, the round-2 residuals, the
  packet-05/06 items, or anything else I noticed while in these files.
- **Did not rewrite history** (item 5), and made no bare `git commit` — `git status` before each
  one, `--only` with explicit paths, per #191.
- **Did not extract a shared render helper** for two call sites (§1 item 1).
- **Did not re-probe** DD-3.g's settled DDL syntax.

---

## 3 — Gates, with #192 fingerprints

```
BEFORE   HEAD=daad8ec  STATUS_LINES=7  (my own 7 modified files)
AFTER    HEAD=daad8ec  STATUS_LINES=7

ruff        All checks passed!
typecheck   Success: no issues found in 149 source files   (all three members OK)
full suite  6605 passed, 17 skipped, 3 xfailed, 1 warning in 195.43s
skill       117 passed in 13.79s
concurrency 20 runs × 14 passed — TOTAL_RUNS_WITH_FAILURES=0
```

HEAD and the status count are IDENTICAL at both ends, and the seven modified files are my own
in-flight work. These numbers describe a tree that did not move under them.

### 3.1 — A sibling commit DID land during my FIRST gate run, and I am not hiding it

My first full run started at `95dd80a` and ended with `HEAD=daad8ec`. Under #192's own
interpretation rules that is the "a sibling commit landed mid-run" case — the one the lead predicted
should not happen, since the auditors were briefed report-only.

What it was: `daad8ec docs(03b): DD-3.c's migration safety claim is FALSE — struck and corrected`,
touching two DOCS files (`REPORT-coldaudit-03b-2.md`, the deferred-design rulings) and no code.
All ten per-file code MD5s were identical at both ends of that run.

**Composed, per the detection/diagnosis split: the tree moved, the code under test did not, and it
moved by a commit rather than an edit.** So the numbers were not wrong — but "not wrong" is a
conclusion I could only reach BECAUSE the fingerprint was there, which is the entire argument for
#192. I re-ran the full gate set afterwards anyway (the block above), because a receipt that needs
a paragraph of interpretation is weaker than one that does not.

⚠ **And it was not merely noise: that commit changed what I had to build.** See §5 W1.

---

## 4 — Mutation proofs

`cp -a` content backups, restore from content, md5-verified identical after every proof
(`server.py 5fdd8e1c…`, `messages.py 59c75feb…`, `surreal_schema.py 4cbbe933…`,
`surreal.py 2bfd445f…`).

| # | mutation | result |
|---|---|---|
| **MP-W1** | drop the peek-escape branch (restore the single arithmetic) | **1 failed** — the new convergence pin; the two sibling legs stayed GREEN, which is the uncovered cell made visible |
| **MP-W2** | flip `_define_field` to `IF NOT EXISTS` (the #107 clause) | **1 failed** in the new `message` dirty-store class — `test_the_bound_is_LIVE_after_applying_the_new_ddl_to_a_dirty_store`. (First attempt: DID NOT RUN — §4.1.) |
| **MP-W3** | drop the write-path truncation | **2 failed** — the tool-name and declared-identity legs |
| **MP-W4** | drop the `trace.tool` ASSERT | **1 failed** — the store-backstop leg, and only the `tool` parametrisation |
| **MP-W5** | drop the `ack_note` bound | **1 failed** — the whole-window denial leg; the BASELINE and the clean-edge CONTROL stayed green, so the pin is discriminating rather than merely red |

**Honest scope on MP-W2:** the offline pins also redden under that flip, because they string-match
`DEFINE FIELD OVERWRITE`. So it proves the live leg FIRES on a real migration failure; it does not
prove the live leg is the only detector of *that* mutation. What the live leg uniquely covers — and
what no offline pin can reach by construction — is a definition that emits correctly and never
lands. That is an argument, not a measurement, and I am labelling it as one.

### 4.1 — A mutation that silently did not run

MP-W2's first attempt used a guessed anchor for `_define_field`'s return statement. The helper
asserted the anchor count, printed `AssertionError: anchor 0`, and the test command in the same
block then ran against the **UNMUTATED** tree and printed `4 passed`.

**That green was not a proof of anything, and it is exactly the shape that gets reported as one** —
a passing tail beside a mutation that never happened. I caught it because the helper prints its
failure, and because "4 passed" for a mutation I expected to redden something did not match. Re-ran
with the real anchor (`grep`-derived, not guessed) and it discriminated.

The generalisable bit: **a mutation proof needs its own positive control — evidence the mutation
LANDED — or a silent no-op reads as "the pin is fine".** The cheap version is asserting the anchor
count and treating a failed assert as fatal to the whole block, which mine did not do (it printed
and continued).

---

## 5 — Deviations

**W1 — I added a `to`/`ack_note` dirty-store class the brief did not list.** The brief's item 2 said
"the message-slice dirty-store pin"; I built that AND a second class for the delivery edge.

Why: the sibling commit that landed mid-wave (§3.1) STRUCK DD-3.c's claim that a later narrowing
"cannot write-poison (message rows are never UPDATEd)" — true of `message`, **false of `to`**, where
DD-3.f puts `ack_note`. `drain` UPDATEs `to` on every call in ONE guarded statement over the whole
window, and the engine re-validates the whole record on write, so a single legacy edge with an
over-cap note fails that statement and the agent cannot drain ANY of its inbox. Total denial.

Building the instrument for the table that provably cannot hurt us while omitting the one that can
would have repeated the exact rider-skipping the correction is about. Production exposure is ZERO
today, so this is not a live defect — it is so the next narrowing on `to` meets the mechanism
deliberately. ~110 lines with its baseline and its discriminating control, mutation-proven.

**If the lead judges this outside the wave, it is one class to delete** and nothing else depends on
it.

**W2 — the trace write path TRUNCATES where message pointers REJECT.** The brief said "bound them at
the same LAYER the message pointers are bounded", which fixes the layers and not the policy. Both
readings:

- *Reject* (consistent with `body`/pointers): a rejected write raises inside the emission, is
  swallowed by the ruled failure posture, and the row is LOST. That lets a caller suppress its own
  measurement by sending a giant name, and it drops a row from the denominator packet 06 reads.
- *Truncate* (**chosen**): the row lands, bounded. A truncated group key is still a usable group key;
  an absent row is not. The store ASSERT stays as the backstop for a writer that skips the
  truncation.

The reject-never-truncate law exists because a shortened POINTER is a broken pointer that only the
caller can fix. A trace row is telemetry ABOUT a call and the caller is not fixing anything, so the
law's premise does not hold here. Stated rather than assumed; reversible in one function.

---

## 6 — Residuals

| id | residual | verdict |
|---|---|---|
| **R1** | Truncation can COLLIDE: two distinct 300-char tool names sharing a 256-char prefix become one group. | **ACCEPTED, named.** Deterministic (a plain prefix, pinned), and a >256-char tool name is already pathological. The alternative — hashing the overflow — buys distinctness nobody reads and costs legibility. |
| **R2** | `_MESSAGE_FIELD_SPECS`'s `refs[*]` element row exists only because `TYPE array<T>` implicitly defines `<field>.*`. A future array field with a per-entry ASSERT must repeat that trick. | **DOCUMENTED where it lives** (the spec comment and the store reference §7). Not generalised into a helper: one instance is not a pattern, and a premature helper here would be a second thing to keep in sync. |
| **R3** | DD-1.c's retention findings row and the client-battery re-run remain the lead's. | **UNCHANGED from the design wave.** Neither is a builder's to file or run. |
| **R4** | `TestParamsHashIsTheRuledRecipeAndLeaksNothing`'s NAME still says "LeaksNothing" while three columns are stored plaintext. | **DOCSTRING CORRECTED, NAME LEFT.** Renaming a committed contract class is a wider edit than this wave authorised, and the docstring now states the truth in the first line a reader sees. Flagged so it is a deliberate leftover, not an oversight. |
| **R5** | The round-2 residuals and D6's cost-claim docstring. | **OUT OF SCOPE, ledgered by the lead.** Named so this report cannot be read as "all round-2 findings closed". |
| **R6** | Six rider clauses have now been implemented without their "and pin it like this" half across three waves. | **THE PATTERN, not a residual — and it is mine.** Three were mine and self-caught, one was caught by the round-2 audit, and this wave's C4 is the one that cost something: a false safety claim survived a design wave, a self-audit and two review rounds because the instrument naming it was never built. **A ruling's rider is part of the ruling.** |

---

*Measured 2026-07-25 at commits `768c8a7`..`01a0cc1` on branch `feat/surreal-unification`, gates at
HEAD `daad8ec` with the fingerprints in §3. Every number was produced by the command shown beside
it, in this session, on a tree proven not to have moved under it.*
