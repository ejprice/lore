> ⚠ **STRUCK AS AUTHORITY 2026-07-24** (operator; finding #181; reset commit 0941aab): produced in the self-certified 03b contract phase — the author built its own reference implementation and graded its own wave; no adversary re-graded the result. Preserved as history and as raw material for the blind-diff completeness check ONLY. Corpus at tag `pkt03b-tainted-corpus`.

brief-base v6 read

# REPORT — contract-surface-03b-2 (packet 03b, AMENDMENT 10: D2 → reading A)

*Successor to `contract-surface-03b`, whose report (the original wave + amendments 7/8/9) is the
inheritance this one builds on. Everything measured here was measured **2026-07-24 at `9a98cf3`**
(the branch point) through `ff9ed96`; the three contract files are RED ON PURPOSE at every one of
those commits — the 03b surface is unbuilt.*

## SUMMARY BLOCK

- **State: done-with-deviations.** Amendment 10 landed in three commits: `fab5549` (the ruled
  render pins), `1759ba4` (the WIRING leg), `ff9ed96` (the REQUIRED-not-defaulted pin).
- **D3: confirmed untouched.** `_is_placeholder_only` is exactly as my predecessor built it.
- **Satisfiability: 1092 passed / 12 skipped / 0 failed** across all three files against a
  reading-A REFERENCE BUILD (was 1063 before this wave; +29 = my new pins).
- **Harder post-lint leg PASSED:** with the reference build, `ruff check loremaster/` clean and
  `./scripts/typecheck.sh` **mypy-ZERO for the whole comms surface** — the only 6 remaining errors
  are the sibling's `test_trace_telemetry.py` (inherited D8). **That number is not lost.**
- **Mutation battery: 8/8 PROVEN**, each reported as a FULL-contract failure set (§3). The required
  proof — a build that IGNORES `session` — is **M1: 4 RED, and every one is a new pin; ZERO
  committed pins move.** The committed contract was totally blind to reading B.
- **Provenance receipt:** `loremaster.__file__ = /home/ejprice/scratch-03b-refbuild/loremaster/loremaster/__init__.py`
- **Deviation (reported, not asked):** two riders beyond the literal "discriminating pair" — the
  dispatcher WIRING leg and the REQUIRED-not-defaulted signature pin. Rationale + measurements in §2.
- **Decisions needed: ONE — D10** (§4): `_inbox_entry` defaults, and `_p03_entry` hardcodes, a
  parameter the render now branches on. Not a live false gate; the door amendment 8 shut, reopened
  on the neighbouring field. Exact edit supplied; NOT taken.
- Counts (before → after): promise_registry **14F/107P → 14F/107P** · comms_tool **200F/556P →
  228F/557P** · message_ledger **186P/12s → 186P/12s** (untouched) · ruff **clean** · mypy 46 → 52
  mine (all forward refs; the reference build pays every one) + 6 sibling's.
- Receipts: §1 what changed · §2 the two riders · §3 mutation battery · §4 D10 · §5 what the
  adversary will probe.

---

## 1. Amendment 10 — what changed

**The ruling** (`docs/plans/v2/03b-comms-surface-design-rulings.md` §S4.2 amendment note + §S8 D2):
`_render_comms_drain` gains a REQUIRED `session: str` kwarg; five committed drivers gain
`session="wave7"`. Reading B was refused because default-thread rows must stay bare or the thread
label stops meaning "a deliberate conversation" — the signal S5's one-thread-one-debt teaching
leans on.

### The five drivers (mechanical; every rendered value preserved)

| driver | file |
|---|---|
| `_render_drain` | `test_comms_promise_registry.py` |
| `_render_drain_body` · `_render_drain_sender` · `_render_drain_thread` | `test_comms_tool.py` |
| `TestRenderCommsDrainShape._render` | `test_comms_tool.py` |

`_render`'s `session` is the ONE parameter that had to become settable rather than hardcoded (the
pins vary it). It carries a default so its twenty committed call sites render exactly what they
rendered before — **and that default cannot manufacture a monoculture**, because
`test_the_SUPPRESSED_thread_is_the_SESSION_ARGUMENT_not_a_LITERAL` drives a different session and
inverts which row draws the cell. The reasoning is in the method's own docstring, not only here.

### The pins

1. **`test_a_SESSION_DEFAULT_thread_draws_no_cell_but_a_DELIBERATE_one_does`** — the ruled
   discriminating pair. ONE render, TWO rows (`#71` on `thread == session`, `#72` on
   `q:cap-boundary`). Two rows in one render makes the discrimination **per-row, not per-call**;
   measured, not assumed (M5).
2. **`test_the_SUPPRESSED_thread_is_the_SESSION_ARGUMENT_not_a_LITERAL`** — the monoculture killer.
   `session="wave9"`; the value suppressed in pin 1 is the value REQUIRED to render here, so no
   single literal satisfies both. Every other drain driver in the contract passes `"wave7"`, so
   without this a build spelling `entry.thread != "wave7"` passes the entire contract (M2).
3. **`test_a_TASK_row_on_the_SESSION_thread_STILL_draws_its_TASK_cell`** — **the wrong build reading
   A newly admits.** Branch 1 is unconditional; only branch 2 is gated. A builder wrapping the WHOLE
   cell in `if thread != session:` still passes the committed task-precedence pin (whose fixture
   rides a non-session thread, so its gate happens to be open) and drops the task anchor from every
   task row on the session-default thread — where most task traffic lives (M3).
4. **`TestDrainThreadInjectionCaseIsNotVACUOUS`** (21 params + baseline + positive control) — the
   ruling's own premise, CHECKED. The ruling keeps the `drain.thread` battery case valid on the
   grounds that hostile values never equal `"wave7"`. Reading A is what made that premise
   load-bearing: point the driver at a session thread and the cell vanishes, the injected value never
   reaches the output, and 21 battery cases report green while testing nothing. The positive control
   proves the check can SEE a suppressed cell — without it the class would certify a build in which
   branch 3 was never built at all.
5. **`test_the_dispatcher_HANDS_THE_RENDER_A_SESSION_and_it_is_the_right_one`** — the WIRING leg (§2).
6. **`test_the_session_kwarg_is_REQUIRED_and_never_DEFAULTED`** + its positive control (§2).

The class docstring's escalation note became the RULING of record — including *why reading B was
refused*, because that reason binds a builder and a builder reads the instrument, not the design doc.
Leaving the old text ("branch 3 is UNPINNED pending an operator/design ruling") would have been a
served-prose lie the moment the pin existed.

---

## 2. The two riders — deviations, reported not asked (standing authorization, close-out clause)

The literal amendment is "five drivers + the discriminating pair". I landed two further pins. Both
are strengthen-only and mutation-proven; **both are consequences of the ruling rather than
re-openings of it**, which is why they are reported here rather than round-tripped. If either reads
as a judgement call to the operator, they are the two commits to revert (`1759ba4`, `ff9ed96`) and
nothing else depends on them.

### Rider A — the WIRING leg (`1759ba4`)

**Every other amendment-10 pin calls `_render_comms_drain` DIRECTLY and hands it a session.** All of
them stay green for a dispatcher that forwards the wrong one — and the dispatcher is the only path
production takes. That is this repo's #131 shape in miniature: *the fixture guarantees the one
condition under which the bug is invisible.* A REQUIRED kwarg is only worth having if the one
production call site supplies the RIGHT value.

Measured: mutating the DISPATCHER (not the render) to forward `""` or `agent_row.name` fails
**exactly one pin in 1092** — this one. Without it, both defects ship green.

Its KNOWN BOUND is in its docstring, not left for an auditor: registration ties the caller to
`session="wave7"`, so a dispatcher forwarding a hardcoded `"wave7"` is indistinguishable AT THIS
SEAM. That discrimination is pinned one layer down (pin 2), and the docstring says so. The two
together cover the property; neither does alone.

### Rider B — REQUIRED-not-defaulted (`ff9ed96`)

D2 ruled the kwarg "REQUIRED, never defaulted" **and gave the reason**. Nothing enforced it. A
builder shipping `session: str = ""` satisfies every behavioural pin above — they all pass a session
explicitly — while leaving the door the ruling closed standing wide open for the next call site.
This is the same property amendment 8 pinned for `_p03_entry`'s `acked_at`, by the same precedent,
after the same class had already been paid for at `_brief()`'s `name`. Keyword-ONLY is pinned with
it (a positional `session` is the same silent wrong value from the other direction).

It ships with a positive control — a deliberately wrong-shaped local twin — so that `inspect`
reporting `empty` MEANS something. **This control is GREEN today** (it introspects a local function),
which makes it the one live assertion in the amendment.

---

## 3. Mutation battery — 8/8 PROVEN

Regenerated by ONE script: `amendment10_battery.py` in the scratch reference build (see §6 —
**not committed, because the scratch tree is outside my writable set; the table below is the durable
record and the lead's disposition is asked for**). It reports the **full-contract** failure set for
every mutation across all three files, so "fails there and only there" is a MEASUREMENT, not a claim.

Control: the correct reading-A reference build → **1092 passed / 12 skipped / 0 failed**.

| # | wrong build (mutated in `server.py`) | full contract | which pins fired |
|---|---|---|---|
| **M1** | render **IGNORES `session`** (reading B: always render the cell) | **4F / 1088P** | pair · killer · vacuity-control · wiring — **all four NEW; zero committed pins** |
| M2 | render suppresses on the **literal `"wave7"`**, not its argument | 1F / 1091P | killer, alone |
| M3 | render gates the **WHOLE cell** on `thread != session` | 1F / 1091P | task-cell pin, alone |
| M4 | render **NEVER** draws the thread cell (over-suppression) | 26F / 1066P | 25 new + `test_the_context_cell_falls_back_to_the_THREAD` (committed) |
| M5 | render decides the cell **ONCE for the whole drain** (from `entries[0]`) | 3F / 1089P | pair · killer · wiring — all new |
| **M6** | render **DEFAULTS** the kwarg (`session: str = "wave7"`) | 1F / 1091P | the REQUIRED pin, alone |
| **W1** | **dispatcher** forwards `session=""` | 1F / 1091P | wiring leg, alone |
| **W2** | **dispatcher** forwards `agent_row.name` | 1F / 1091P | wiring leg, alone |

Restored → **1092 passed / 0 failed.**

**Three readings worth keeping:**

- **M1 is the necessity proof.** Under reading B — the build a builder produces by DEFAULT, and the
  one my predecessor's reference build actually implemented — **not one committed pin moves.** The
  contract as it stood could not tell reading A from reading B at all.
- **M4 exposes an ASYMMETRY that justifies the pair.** The committed contract COULD see
  over-suppression (one pin fires) but was blind to under-suppression. Half a branch was guarded, and
  it was the half a builder is least likely to get wrong.
- **M5 turns a docstring claim into a measurement.** The pair's docstring asserts that both rows live
  in one render so a build deciding the cell once for the whole drain fails. I built that build: it
  does. This repo's law is that a failure message promising a check the assertion does not perform is
  a false gate — the same applies to a docstring promising a discrimination.

---

## 4. D10 — DECISION NEEDED (a hazard, not a live false gate). Not taken.

Reading A makes `thread` **a parameter the render branches on**. Two fixture factories predate that:

- `_inbox_entry(*, thread: str = "wave7", ...)` in `test_comms_tool.py` — **defaults** it.
- `_p03_entry(*, seq, acked_at, grade="signal")` in `test_comms_promise_registry.py` — **hardcodes**
  `thread="wave7"` with no parameter at all.

Repo law: *"Fixture factories must not default a parameter the code branches on."* That is precisely
amendment 8's ruling, on the neighbouring field of the same factory — `acked_at`'s default WAS R3's
root cause, and `thread`'s default is now the same shape one field over.

**It is NOT a live false gate today.** I checked: after amendment 10, every wrong build the default
could hide is caught by the pair (M1), the killer (M2) or the task pin (M3). The exposure is to the
NEXT pin an author adds — which is exactly the exposure amendment 8 was authorized to close.

**Why I did not take it:** it is a ruling about fixture design, not a mechanical consequence of D2,
and the standing authorization reserves rulings to the operator. It is also ~20 call sites in a
frozen file. **The exact edit, if authorized:** `_inbox_entry(*, thread: str, ...)` — required — with
each call site gaining `thread="wave7"` explicitly (values unchanged); `_p03_entry` gains
`thread: str` as a required kwarg, six call sites gaining `thread="wave7"`. Recommended, low risk,
mutation-provable exactly as amendment 8 was (a `TypeError` proof plus a both-values-expressible
positive control).

---

## 5. What I expect the adversary to probe (said here rather than left to be discovered)

1. **`_render`'s `session` default** — a defaulted branch-comparand in a driver, one layer below the
   signature the ruling required. Deliberate, justified in the method docstring, and neutralised by
   pin 2, which is the only pin that varies it. Measured: M2 shows pin 2 fires alone. The stricter
   alternative (required, 20 call sites) is the same fork as D10 and I would take them together or
   not at all.
2. **The wiring pin's hardcoded-`"wave7"` blind spot** — real, stated in its docstring, covered one
   layer down. Registration makes it unreachable at that seam; I did not manufacture a second session
   to chase it.
3. **`total_pending` / trailers in the new fixtures** — the pair and killer use two signal rows with
   `acked_at=None` and default `total_pending`, so no trailer or elision line can collide with
   `_drain_line_containing`'s exactly-one-line requirement. Deliberate.
4. **The vacuity class's 21-way parametrization** duplicates the battery's corpus but not its
   assertion (safety vs reachability). If the adversary calls that redundant: M4 shows the two are
   not — the battery stays green under a build that renders no cell, because a discarded value cannot
   forge a row.
5. **D9 (my predecessor's, inherited and untouched):** `CommsConfig.drain_limit` and
   `AppContext.message_ledger` are still missing from production and still pinned RED. Amendment 10
   does not touch that; the builder brief still owes both wirings.

---

## 6. Housekeeping, tool honesty, provenance

**Provenance receipt (repo law — prove which tree you are testing):**
`loremaster.__file__ = /home/ejprice/scratch-03b-refbuild/loremaster/loremaster/__init__.py`,
asserted before every satisfiability and mutation run. No worktree was used (standing directive,
#134/#125). The scratch copy is my predecessor's, made with `./scripts/scratch_copy.sh`; I re-asserted
its provenance rather than inheriting the claim, and re-synced the three contract files into it
byte-exactly (md5-compared) before every measurement. I backed up `server.py` to
`.a10_backup/server.py.pre10` (content, not a hash list) before mutating it.

**The reference build is now reading A.** I upgraded my predecessor's build in place:
`_render_comms_drain_row(entry, *, session)` implements the three-branch cell,
`_render_comms_drain` takes the required kwarg, and `_comms_drain` forwards the caller's session.
The real tree carries **no production change** — `loremaster/loremaster/**` is untouched, and
`git status` is clean at `ff9ed96`.

`/home/ejprice/scratch-03b-refbuild` holds the reading-A reference build plus `apply_refbuild.py`,
`mutation_battery.py` (my predecessor's 17), `amendment_battery.py` (its 5) and my
`amendment10_battery.py` (8), at **1092 passed / 0 failed** with the comms surface mypy-zero. It is
the fastest way for the contract-adversary or the builder to re-run any receipt in this report or my
predecessor's. **Lead: keep, archive the four scripts beside these reports, or delete — your call.**
Nothing in it is on any branch. (My predecessor made the same request; per brief-base §1 a committed
script that regenerates a measurement outranks a table, so archiving is what I would recommend.)

**Tool honesty.** `lore_index()` freshness was not consulted; this run needed no code-structure
search. Every file was point-read from paths the brief supplied, and every structural question was
answered by EXECUTING the real code against a reference build — stronger than any index read. Greps
were used for call-site enumeration (`_render_comms_drain`, `_inbox_entry`), for confirming no test
module actually imports the two files I edited (the `grep -l` hits were prose mentions, verified),
and for locating the injection corpus — exhaustiveness-critical sweeps and non-symbol textual seams,
the honest-grep categories, said out loud per the dogfood protocol. No lore friction encountered;
nothing filed.

## 7. Gate results

| | at `9a98cf3` (inherited) | at `ff9ed96` (mine) |
|---|---|---|
| `test_comms_promise_registry.py` | 14F / 107P | **14F / 107P** (driver + docstring only) |
| `test_comms_tool.py` | 200F / 556P | **228F / 557P** (+28 RED pins, +1 GREEN control) |
| `test_message_ledger.py` | 186P / 12s | **186P / 12s** (untouched — amendment 10 required nothing there) |
| all three | 214F / 849P / 12s | **242F / 850P / 12s** |
| `uv run ruff check .` | clean | **clean** |
| mypy | 46 mine + 6 sibling | **52 mine + 6 sibling** — all forward refs; the reference build pays every one |
| neighbouring suites (`test_comms_fleet_grouping`, `test_comms_render_architecture`, `test_comms_schema`, `test_comms_wiring`, `test_render`) | — | **437 passed, 3 xfailed** — no regression |
| **reference build (all three files)** | 1063P / 0F | **1092P / 12s / 0F**, ruff clean, comms surface **mypy-ZERO** |

**Zero passing pins moved in either direction** from amendment 10: 849 → 850 passed, and the +1 is
rider B's positive control, which is live today by construction.

The contract now FREEZES.

---
---

# D10 WAVE — the defect generator, killed on BOTH comparands (ruled 2026-07-24, landed under standing authority)

*Everything above this line is the amendment-10 wave and the record of WHY D10 exists. Nothing in it
is superseded; §4 above is the escalation this section answers. Measured 2026-07-24 at `db225d4`.*

## SUMMARY BLOCK (D10 wave)

- **State: done.** One commit, `db225d4`. The design sidecar ruled D10 **and** the paired
  driver-level default IN as ONE item — clause (a) of the standing authorization — so it landed
  without a further operator cycle.
- **Satisfiability: 1092 passed / 12 skipped / 0 failed**, UNCHANGED. D10 removes defaults; it adds
  no pins, so the number must hold rather than rise — and it does.
- **Harder leg PASSED, unchanged:** `ruff check loremaster/` clean, `./scripts/typecheck.sh`
  **mypy-ZERO for the comms surface**, only the sibling's 6 in `test_trace_telemetry.py`. **03b's
  exit criterion is intact.**
- **Provenance:** `loremaster.__file__ = /home/ejprice/scratch-03b-refbuild/loremaster/loremaster/__init__.py`,
  asserted inside the door proof itself (it exits non-zero on a poisoned copy) rather than eyeballed.
- **Door proofs: 4/4 shut, 3/3 controls green** (§D2 below) — amendment 8's shape on both factories
  AND the driver, plus amendment 8's own `acked_at` door re-asserted so this wave cannot have
  loosened it.
- **Mutation battery re-run: byte-identical to the pre-D10 run** — same 8 mutations, same failure
  counts, same node ids, control and restore both 1092. D10 cost the discrimination nothing.
- **Counts: every file identical before and after** — 242F / 850P / 12s. That is the whole claim of a
  value-preserving amendment, and it is the receipt for it.
- **One deviation, disclosed loudly:** the mechanical pass produced malformed-but-green code (§D4).
- **No D11.** Nothing newly found; nothing withheld.

## D1 — what landed

**48 call sites**, derived by re-running the transformation, not inherited from the estimate:

| target | change | call sites |
|---|---|---|
| `_inbox_entry` (`test_comms_tool.py`) | `thread: str = "wave7"` → **required** | **21** |
| `_p03_entry` (`test_comms_promise_registry.py`) | gains a **required** `thread: str` | **10** |
| `TestRenderCommsDrainShape._render` | `session: str = "wave7"` → **required** | **17** |

`_p03_entry` is the sharper of the two factories: it did not *default* `thread`, it **hardcoded** it —
a monoculture with no dial at all, which no call site could have escaped even deliberately. Harmless
while the render merely interpolated the thread; a generator the moment D2 made the render branch on it.

The two arguments that decided the shape are in the factories' own docstrings, not only here — a
future author meets them at the point of use:

1. **"Today's pins already discriminate" is a DATED RECEIPT, not a standing property.** The exposure
   of a defaulted comparand is definitionally to the NEXT pin — written on the one day nobody re-runs
   the coverage analysis. This packet's own S1 exists because an untested coverage premise hands a
   hole an alibi.
2. **The comparison has TWO comparands, so half the law is none of it.** Closing only the factory
   leaves the generator alive one layer down: a pin routed through a session-defaulting DRIVER tests
   one branch exactly as silently as one routed through a thread-defaulting FACTORY.

## D2 — door proofs (regenerated by `d10_door_proof.py`)

```
PROVENANCE: loremaster.__file__ = /home/ejprice/scratch-03b-refbuild/loremaster/loremaster/__init__.py

  DOOR SHUT   _inbox_entry(seq=1): TypeError: missing 1 required keyword-only argument: 'thread'
  CONTROL OK  _inbox_entry.thread: 'wave7' and 'q:cap-boundary' render differently
  DOOR SHUT   _p03_entry(seq=99, acked_at=None): TypeError: missing ... 'thread'
  CONTROL OK  _p03_entry.thread: 'wave7' and 'q:cap-boundary' render differently
  DOOR SHUT   _p03_entry(seq=99, thread=...): TypeError: missing ... 'acked_at'   [amendment 8, re-asserted]
  DOOR SHUT   _render(entries): TypeError: missing 1 required keyword-only argument: 'session'
  CONTROL OK  _render.session: 'wave7' and 'q:cap-boundary' render differently

ALL THREE DOORS SHUT, ALL CONTROLS GREEN
```

**The controls are the half that matters.** A required parameter that admits only one value in
practice is the same defect wearing a stricter signature, and a `TypeError` alone cannot tell the two
apart — so each control renders BOTH sides of the branch the parameter guards and requires the two
outputs to DIFFER. A control asserting merely that both values are *accepted* would pass on a build
where the branch does not exist.

The script asserts its own provenance (`is_relative_to(cwd)`) and exits non-zero on a poisoned copy,
so #140 cannot make it grade the original checkout silently.

## D3 — the mutation battery, re-run whole

Re-ran all 8 cases after D10 rather than reasoning that the anchors live in `server.py` and could
not have moved. Result: **byte-identical to the pre-D10 run** — same failure counts, same node ids,
control **1092 passed / 0 failed**, restored **1092 passed / 0 failed**. The §3 table above stands
unamended at `db225d4`; D10 preserved every discrimination it was required to preserve.

## D4 — DEVIATION, disclosed: a mechanical pass that was green and wrong

Adding 48 kwargs by hand invites transcription error, so I did it with a balanced-paren transformer.
Thirteen lines then exceeded the 110-char limit and I re-wrapped those thirteen — **and the wrapper
produced two hunks that were valid Python, ruff-clean, and count-identical while being malformed**:

```python
                _p03_entry(seq=62, acked_at=None, thread="wave7",
            )],
```

plus seven non-idiomatic bracket-hugs (`self._render([` with the list dangling across lines) and
three assert-message mangles that DID break the parse. The parse breaks were loud. **The malformed-
but-valid ones were not: ruff passed, mypy passed, and the suite returned 242F/850P/12s — exactly the
pre-change numbers — because the code was semantically identical.** Only reading the diff found them.
All repaired by hand; the final diff is in `db225d4`.

Recorded rather than quietly fixed because it is a clean instance of this repo's own law: a gate
sees what it is keyed on, and none of these three gates is keyed on *legible structure*. The
value-preservation claim of a mechanical amendment rests on the diff being read, not on the counts
matching — the counts match precisely when the transformation is semantically sound, which is the
condition under which the formatting damage is invisible.

## D5 — §5 revisited (the adversary list, updated as the lead asked)

| # (from §5) | status after D10 |
|---|---|
| 1. `_render`'s `session` default | **CLOSED.** It is now required; 17 call sites state it; `d10_door_proof.py` proves the door and the both-values control. The "stricter alternative" §5 named as a fork is what landed. |
| 2. wiring pin's hardcoded-`"wave7"` blind spot | **OPEN, unchanged, and NOT a thing D10 could close.** It is a property of the SEAM (registration ties the caller to one session), not of a fixture default. Stated in the pin's docstring, covered one layer down by the literal-vs-argument pin. |
| 3. trailer/elision collision in the new fixtures | Unchanged — still deliberate, still no collision. |
| 4. vacuity class duplicating the battery corpus | Unchanged — M4 still shows the two are not redundant. |
| 5. D9's two missing production wirings | Unchanged, still RED, still owed by the builder. |

**New, for the adversary, arising from this wave:** every one of the 48 call sites now states
`thread="wave7"` / `session="wave7"` explicitly, which makes the VALUE monoculture textually obvious
where it was previously hidden in two signatures. That is the intended outcome — the law's mechanism
is that every call site must CHOOSE, not that the choices must differ — but an adversary counting
literals will find 48 of them. The discrimination that makes the monoculture harmless is pins 2 and 3
of §1 (measured: M2 and M3 each fire alone), and it does not depend on any call site choosing a
different value.

## D6 — gate results (D10 wave)

| | before D10 (`ff9ed96`) | after D10 (`db225d4`) |
|---|---|---|
| `test_comms_promise_registry.py` | 14F / 107P | **14F / 107P** |
| `test_comms_tool.py` | 228F / 557P | **228F / 557P** |
| `test_message_ledger.py` | 186P / 12s | **186P / 12s** (untouched) |
| all three | 242F / 850P / 12s | **242F / 850P / 12s** |
| `uv run ruff check .` | clean | **clean** |
| mypy | 52 mine + 6 sibling | **52 mine + 6 sibling** |
| **reference build** | 1092P / 12s / **0F**, ruff clean, comms **mypy-ZERO** | **identical** |

Identical in every cell is the correct result for a value-preserving amendment, and it is the claim
this wave was authorized on.

**THE CONTRACT IS NOW FROZEN.**
