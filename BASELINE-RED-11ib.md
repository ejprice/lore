# BASELINE-RED — packet 11-i-b, at branch base `2b8aa01`

**Measured 2026-07-28 by `lead-11ib`, in the worktree `/home/ejprice/PycharmProjects/lore-pkt11i-b`
(branch `pkt11-i-b-floor-runner`, base `2b8aa01`).** Date-stamped here rather than only at the top
of a report, because a retrieved chunk arrives without its header.

## Why this file exists

11-i-b branches from the shared integration branch `feat/surreal-unification`, which currently
carries **packet 04b-1's committed-but-unbuilt contract**. Contract-first TDD means those pins are
RED *on purpose* — but they are a DIFFERENT packet's red, and a builder that has to mentally
subtract 81 known failures is a builder who can talk itself past its own. This file makes the
subtraction mechanical instead of mental.

**The node ids are in `BASELINE-RED-nodeids.txt` (81 lines), derived from the run BEFORE any
11-i-b work existed — never transcribed from a later run's failures.** That direction matters: a
"declared" set read off the failures you just watched is the tautology in a new costume
(CLAUDE.md, `scripts/mutation_proof.py`'s reason for taking expected-RED ids as an argument).

## The measurement, both legs

| leg | command | result |
|---|---|---|
| full suite at base | `uv run --no-sync pytest -q -n auto` | **81 failed, 8029 passed**, 36 skipped, 3 xfailed, 225s |
| same, 81 deselected | same + `--deselect` × 81 (from `BASELINE-RED-nodeids.txt`) | **0 failed, 8029 passed**, 36 skipped, 3 xfailed, 210s |

The pass count is **8029 in both legs**. That equality is the point: the 81 are fully accounted
for, and nothing else in the tree is red. A green claim needs a passed-COUNT, and both legs have
one.

Regenerate:
```bash
cd /home/ejprice/PycharmProjects/lore-pkt11i-b
awk '{printf "--deselect\n%s\n", $0}' BASELINE-RED-nodeids.txt > /tmp/deselect.args
xargs -a /tmp/deselect.args -d '\n' uv run --no-sync pytest -q -n auto
```

## Attribution of all 81 — every file gets its own verdict

"All remaining hits are X" is banned output (CLAUDE.md). Each group, individually:

| n | file | verdict |
|---|---|---|
| 75 | `loremaster/tests/test_blocks_edge.py` | 04b-1's `blocks`-edge contract, added at `688621b` (*"80 pins, 72 RED"*). **Declared RED; unbuilt.** |
| 3 | `loremaster/tests/test_enforced_relations.py` | all three parametrised on `blocks` — the same 04b-1 contract, reaching an existing file. **Declared RED; unbuilt.** |
| 2 | `loremaster/tests/test_query_tasks_bounded.py` | 04b-1's #253 addendum, added at `09146bc` (*"14 pins, 3 RED"*). **Declared RED; unbuilt.** |
| 1 | `loremaster/tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` | **NOT a declared RED — a real, small 04b-1 defect.** See below. |

### The one that is not a declared RED

`_surreal_harness`'s docstring states a DERIVED count — *"43 test files import this harness"* —
and 04b-1's two new test files pushed the true count to **45**. The pin fires with
`AssertionError: the harness docstring says 43 test files import it; 45 actually do`.

**The pin is working exactly as designed.** It exists because that very sentence was once committed
at four sites with a FALSE number, one of them inside a failure message (audit-150 R2) — prose that
describes behaviour must be DERIVED from the behaviour or CHECKED against it. It caught a stale
count within hours of the staleness being introduced.

**Owner: packet 04b-1, not 11-i-b.** It is a one-line fix in the tree that caused it, and 11-i-b
does not edit another packet's surface. Recorded here so that whoever builds 04b-1 meets it as a
known item rather than as mystery noise, and so nobody in 11-i-b "helpfully" fixes it and muddies
two packets' diffs.

## Standing obligation for every 11-i-b gate run

Any suite run in this packet reports **either** `81 failed / N passed` with the 81 diffed against
`BASELINE-RED-nodeids.txt` **both ways** — unexpected reds *and* declared reds that went green —
**or** `0 failed` with the deselect list applied. A bare "81 failed, same as baseline" is not a
receipt; the set has to be compared, because a build that turns one declared-RED green while
breaking a different test shows the same count.

⚠ If the operator rebases this packet onto `0f4656c` (the commit immediately before 04b-1's
contract landed), this file becomes history: the baseline there is expected to be 0 failed, and
that expectation must itself be MEASURED before it is claimed.
