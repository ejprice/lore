# Finding #241 — the two lead hunts, and why the green one does NOT close it

**Written 2026-07-26 by `lead-11ia`.** This file exists because **finding #129 is real and I hit
it**: `lore_findings` forbids an `acknowledged → acknowledged` edge, and only `resolve`/`wontfix`
carry a note — so an acknowledged row **cannot be annotated without falsely closing it**. #241 is an
open STOP; closing it to attach evidence would be exactly the falsification #129 describes. The
evidence lives here instead, and #241's ledger note points at this path.

**The instrument is `scripts/contention_hunt.sh`** — committed, not a `/tmp` path. A receipt whose
address is unrecoverable by construction is not a receipt (#152/#154).

---

## Hunt #1 — INVALID. Do not read it as a reproduction.

3 failing runs of 30, and **none of them were this defect.** Recorded because a false reproduction
is worse than none: it would have closed a real STOP on the wrong mechanism.

- The failures were 1–2 tests in `test_floor_calibration_schema.py`. **#241's signature is
  `28 failed, 168 passed` led by `TestTheHeadMintUnderContention::test_no_adoption_is_lost_under_contention[32]`.**
  Different tests, different file, different magnitude.
- **The tree moved under the loop, proven by the loop's own numbers:** 24 runs collected 196 tests,
  then one collected **197**. Two further runs died with pytest-xdist **collection errors**.
- A sibling agent (`closure-11ia-1`) was editing `test_floor_calibration_schema.py` and
  `store/surreal_schema.py` for the entire window, and every failure landed in exactly that file.

**Cause: the lead pointed a diagnostic loop at a tree another agent was mutating** — the HARD FREEZE
law, whose own receipt is a cold audit whose NO-GO reason #1 was that HEAD moved six times while it
ran. A measurement of a moving subject is not a measurement.

## Hunt #2 — VALID, and it came back 0 of 30

Method, with the detector hunt #1 lacked:
1. a **full suite first**, to recreate the post-full-suite window the original failure's timing fitted;
2. 30 iterations of the four contract files, **full per-run output retained** (hunt #1's ancestor kept
   only `tail -2`, which is why the original 28 tracebacks are gone — #159);
3. a `podman logs` window captured on any failure;
4. **`git rev-parse HEAD` and a hash of `git status --porcelain` compared before and after EVERY
   run**, aborting rather than reporting a number;
5. **the collected-test count asserted identical to run 1's** — a moving count is precisely how hunt
   #1 lied, so it is a *checked variable*, not an assumption.

**Result:** freeze held (head `0e99c1e`, empty worktree hash, `collected=210`) on all 30 runs.
**0 failing runs of 30.** Full suite in the same window: **7559 passed, 0 failed**.

## ⚠ WHY 0-OF-30 DOES NOT CLOSE #241

**THE TREE IS NOT THE ONE THAT FAILED.** The builder's 2-of-114 failures were measured **before** the
closure wave (`0e99c1e`) landed — which made `head_identity` a REQUIRED column, changed the emitted
DDL, and added 14 tests (**196 → 210 collected**). These 30 green runs measure the **current** build,
not the build that failed.

- Reporting "30/30, the contention defect is gone" would be a claim about a tree nobody tested.
- **Combining these 30 with the builder's 112 into a single "142 of 144" would be the same error
  wearing arithmetic** — two populations, two trees. That is the #102/#120 conflation this repo has
  now made a law about, and it would be very easy to write.

**What IS established:** the current tree survives 30 consecutive frozen runs including the
post-full-suite window, which discharges the repo's 20-consecutive-greens rule **for this tree**.

**What is NOT established:** the mechanism. Hypothesis **(c)** — genuine exhaustion of the shared 2 s
conflict-retry budget at 32-way — remains untested *as a mechanism*, and **more repetition cannot
test it**: it needs instrumentation counting retry exhaustions at the shared driver. That is
#102/#120 territory and wants its own owner, not an append to this packet.

## Decision point

The **cold audit** re-runs the gates as an independent instrument. If it does not surface this, the
disposition is a **PINNED KNOWN BOUND** with the instrument attached (`scripts/contention_hunt.sh`)
and a named **re-open trigger**: any recurrence of a multi-test contention failure in these files —
at which point the store-log window and full tracebacks now exist to diagnose it, which they did not
the first time.
