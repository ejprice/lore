# REPORT-probe-racer-contention

brief-base v5 read

- **state:** done
- **VERDICT: the single-operation pattern DOES reliably produce contention.** 0 zero-conflict runs out of 20, on every degree measured (8/16/32-way findings mint; 8-way brief publish), serial AND `-n auto`.
- **RECOMMENDATION: leave the existing suites alone.** No rewrite. One narrow, optional addition noted in §7.
- deviation: `test_brief_ledger.py` **cannot collect in the current working tree** — `_comms_fakes.py` (uncommitted, packet-03 in flight) imports `loremaster.messages`, which does not exist. Measured in a blessed scratch copy with that ONE file restored to HEAD. **Surfaced as a flag, §8 — not fixed (outside writable set).**
- deviation: no repo file was modified at any point; md5 receipts in §6 are a non-modification proof, not a restore proof.
- decisions-needed: none for this question. One flag for the operator (§8).
- receipts: distributions §3 · positive control §4 · negative controls §5 · instrument §2 · byte-exactness §6

---

## 1. The question, and the answer

The contract adversary's hypothesis was that N workers each doing **one** operation, released from a
start barrier, may finish before their siblings issue anything — so the retry machinery is never
exercised and the test passes for the wrong reason.

**Measured: false.** Every single run of every test, at every degree, drove multiple genuine
retryable conflicts through `retry_on_conflict`. The adversary's concern is a real failure mode in
general; it is not what these two suites do.

The counter-evidence cited in the brief (the #102 work's "zero exhaustions across 2900 mints") is
consistent with this: zero *exhaustions* is a statement about the retry budget never draining, not
about conflicts never occurring. Conflicts occur constantly; the driver absorbs them.

## 2. Instrumentation

**Single patch point:** `RetryableConflictSignal.__init__`
(`loremaster/loremaster/store/_txn.py:185`).

Chosen because every seam that classifies an engine response as a retryable write-write conflict
constructs this class — the transactional path (`_txn.py:1242`), the ten single-statement seams
(`_txn.py:1002/1010/1018/1103`), and `scout.py:163/560/587`. Patching the **class** sidesteps the
import-binding problem entirely: callers do `from ._txn import retry_on_conflict`, so patching a
module attribute would have missed them. One patch, complete coverage of the classify sites, zero
ambiguity about what is being counted.

Each construction records `(monotonic time, asyncio task name)`. Task names distinguish racers
because `asyncio.gather` wraps each racer coroutine in its own `Task`.

Files (all outside the repo — **nothing in the repo tree was modified**):
- `/tmp/racer_probe/conflict_probe.py` — pytest plugin, loaded via `-p conflict_probe` + `PYTHONPATH`
- `/tmp/racer_probe/control.py` — standalone positive-control harness
- `/tmp/racer_probe/summarise.py` — distribution summariser

Metrics per test: total conflicts · distinct workers that conflicted at least once · wall-clock span
between first and last conflict event (a direct measure of racer-lifetime overlap).

## 3. The 20-run distributions

### 3.1 `test_findings.py::TestConcurrentNumbering` — serial runner

| test | zero-conflict runs | conflicts (min/median/max) | distinct workers conflicted (median) | conflict window |
|---|---|---|---|---|
| 8-way | **0 / 20** | 5 / 7 / 10 | 5 of 8 | 4.6 ms |
| 16-way | **0 / 20** | 11 / 13 / 15 | 10 of 16 | 6.2 ms |
| 32-way | **0 / 20** | 25 / 29 / 34 | 17 of 32 | 15.6 ms |

Raw 8-way series: `[7,8,6,6,6,9,7,6,7,7,7,7,7,6,5,8,5,7,6,10]`

### 3.2 `test_brief_ledger.py::TestConcurrentPublishesLandDistinctVersions` — serial runner

| test | zero-conflict runs | conflicts (min/median/max) | distinct workers conflicted (median) | conflict window |
|---|---|---|---|---|
| 8-way | **0 / 20** | 3 / 4.5 / 9 | 4 of 8 | 2.0 ms |

Raw series: `[6,6,5,4,3,3,5,4,4,7,7,3,6,9,4,3,3,6,5,4]`

### 3.3 `-n auto` (pytest-xdist, the standing runner) — findings, 20 runs

| test | zero-conflict runs | conflicts (min/median/max) | distinct workers conflicted (median) |
|---|---|---|---|
| 8-way | **0 / 20** | 6 / 8 / 11 | 5.5 of 8 |
| 16-way | **0 / 20** | 13 / 15.5 / 20 | 11 of 16 |
| 32-way | **0 / 20** | 25 / 30 / 36 | 19 of 32 |

**Answer to Q5: `-n auto` does not change the answer.** If anything it contends *slightly harder*
(median 8 vs 7 at 8-way; 19 vs 17 workers at 32-way) — consistent with more CPU pressure widening
each racer's window. Either runner certifies the machinery.

### 3.4 The shape of the result

Conflicts scale roughly linearly with N (7 → 13 → 29 for 8 → 16 → 32), and roughly half the fleet
conflicts at least once at every degree. The conflict window (2–16 ms) shows racer lifetimes
overlapping tightly — the start barrier is doing its job on this hardware, and the wire round-trip
is long enough relative to Python's release jitter that the workers genuinely collide.

## 4. POSITIVE CONTROL (mandatory leg)

Same counter, same code path, same 8 racers, **only ops-per-racer varies**. 5 trials each, fresh
throwaway database per trial.

| ops per racer | total mints | conflicts per trial | median | distinct workers conflicted | zero-conflict trials |
|---|---|---|---|---|---|
| 1 | 8 | `[9,7,9,8,7]` | 8.0 | 6 of 8 (every trial) | 0/5 |
| **10** | 80 | `[40,40,40,39,40]` | **40.0** | **8 of 8 (every trial)** | 0/5 |

**The control fires.** Absolute conflicts rise **5×** and worker coverage rises from 6/8 to **100%**
of the fleet. The counter is demonstrably sensitive to increased lifetime overlap — it is not stuck
reporting a constant.

**An unexpected and load-bearing sub-result:** conflicts **per mint** *fall* from 1.000 to 0.500
under the repeated-op pattern. The single-op burst is the **more** contended shape per operation,
not the less. That is mechanically sensible — `asyncio.gather` releases all 8 racers into their
first mint simultaneously, whereas a sustained loop lets jittered backoff desynchronise them after
the first collision. So the repeated-op rewrite the adversary implied would be *safer* would in fact
**lower** per-operation contention pressure while raising total runtime. This is the strongest
argument against the rewrite, and it is a measurement, not an opinion.

## 5. NEGATIVE CONTROLS (the leg that makes the positive one mean something)

A counter that only ever goes up is worthless. Two legs proving it reads **exactly zero** when it
should:

| leg | expectation | measured |
|---|---|---|
| **fake backend**, same concurrent tests, 8/16/32-way | 0 (no wire, no engine) | **0, 0, 0** |
| **real backend, sequential writers** (`TestStableNumbering` + `TestReportAndGet`, 13 tests) | 0 (real store, no race) | **0 × 13** |

The second leg is the discriminating one: it proves the counter keys on **contention**, not merely
on "the real store was touched". Real store + no concurrency = 0. Real store + concurrency = 5–34.

## 6. Non-modification receipt

No repo file was edited. All instrumentation lived in `/tmp/racer_probe/`. md5 before → after:

```
loremaster/loremaster/store/_txn.py: OK
loremaster/tests/test_findings.py: OK
loremaster/tests/test_brief_ledger.py: OK
ALL BYTE-EXACT
```

`git status --porcelain` (tracked) after the run is identical to session start — the same 5
packet-03 files modified, nothing added by me. **No git state was mutated in the real tree.**

**Scratch-copy provenance** (brief-ledger leg, per the #140 law):
```
PROVENANCE loremaster.__file__ = /tmp/racer_probe/scratch/loremaster/loremaster/__init__.py
```
Built with the blessed `./scripts/scratch_copy.sh`. Inside that copy — and only there — I ran
`git checkout HEAD -- loremaster/tests/_comms_fakes.py` to make the module importable (§8).

Store: `ws://127.0.0.1:18000` (spike-surreal, test) throughout, via the harness's
`unique_database()` throwaway-per-test guarantee. **`:18500` was never contacted.**

## 7. RECOMMENDATION — leave the suites alone

**Do not rewrite.** Reasoning, in priority order:

1. **The premise is empirically false.** 0/100 zero-conflict runs across both suites, three degrees,
   two runners. There is no "passes for the wrong reason" window to close.
2. **The proposed fix would make the pin weaker on the axis that matters.** §4 measured that
   repeated-op racers contend *less per operation* (0.500 vs 1.000 conflicts/mint), because they
   desynchronise. A rewrite would trade a maximally-synchronised burst for a longer, more diffuse
   one — strictly worse discrimination per second of runtime.
3. **The existing 16/32-way scale legs already carry the fleet-size axis** that repeated-ops was
   meant to proxy for.

**Optional narrow addition (NOT required by this measurement, offered for the operator's judgement):**
the one thing this probe proves the suites *cannot see* is a regression in the retry machinery's
**engagement** — if a future change made the conflicts stop happening (e.g. the mint silently
serialising), the tests would still go green, having certified nothing. That is precisely the
"green over a dead mechanism" shape CLAUDE.md warns about. A pin asserting **conflicts > 0** during
the 8-way mint would convert this probe's finding into a standing invariant. It would need the
counter to become a small supported seam rather than a monkeypatch, so it is a real (if small)
design decision — **operator's call, not mine.** I flag it; I do not recommend it either way without
a ruling on whether that seam is wanted in production code.

## 8. FLAG — surfaced, not fixed (outside my writable set)

**`loremaster/tests/test_brief_ledger.py` currently fails at COLLECTION in the working tree:**

```
loremaster/tests/_comms_fakes.py:108: in <module>
    from loremaster.messages import (
E   ModuleNotFoundError: No module named 'loremaster.messages'
```

`_comms_fakes.py` is uncommitted (packet-03 work in flight) and imports a module that does not yet
exist. Any test module importing `_comms_fakes` is currently uncollectable — that is at minimum
`test_brief_ledger.py`, and plausibly the other modified comms test files. **This is a live
collection error in the tree right now, not a pre-existing condition I can attribute.** Whoever owns
packet 03 should know that a `pytest` over the comms/ledger area is currently erroring rather than
running, which is exactly the "no tests ran" shape repo law warns reads as green behind a pipe.

I did not touch it. I worked around it in a scratch copy only.

## 9. Inconclusive / not measured

- **`conflict_span_seconds` is a proxy**, not the brief's literal "spread between first and last
  worker's *first write*". I measured the span between first and last *conflict event*, which
  requires the writes to have already overlapped. It is sufficient to establish overlap (which is
  the question) but it is not the requested quantity, and I did not instrument first-write
  timestamps. Say INCONCLUSIVE if the exact first-write spread matters for something else.
- **One machine, one store, one load condition.** These numbers are this 64-core box against
  spike-surreal on loopback. A much faster engine or a much slower client could in principle shift
  the balance. The margin is not close (0/100 runs), but it is not infinitely wide either.
- I did not measure the other suites the brief alluded to ("several existing test suites") — only
  the two named. If the recommendation is to be applied to others, they should be spot-checked with
  this same plugin, which is ~40 lines and reusable as-is.
