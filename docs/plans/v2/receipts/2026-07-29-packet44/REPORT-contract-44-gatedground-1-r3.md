brief-base v9 read

# REPORT-contract-44-gatedground-1-r3 — frozen-roster receipt, and a delivery-loss correction

*Measurements 2026-07-29 in worktree `.claude/worktrees/pkt44`, branch `pkt44/ungated-ground`,
at **`f033a87`**. This report supplies the receipt line the resend demanded. The substance was
already delivered — see `REPORT-contract-44-gatedground-1-r2.md` §0, which carries the full
adjudication table and the mutation-proof rows.*

---

ROSTER RULING APPLIED: FROZEN_SHA=f033a87 · roster size 19 · pins (all in `TestTheScriptsExemptionIsAFrozenRoster`): test_a_file_added_after_the_frozen_sha_is_flagged_not_grandfathered · test_a_file_present_at_the_frozen_sha_is_grandfathered · test_the_roster_is_derived_from_the_repository_not_from_a_committed_list · test_the_instrument_is_flagged_until_its_members_entry_exists_and_covered_once_it_does · test_the_row_carries_a_sha_a_finding_and_a_trigger_and_no_numeric_claim · test_an_unreachable_frozen_sha_is_blind_not_clean (+ its sibling test_a_roster_that_matches_nothing_is_blind_not_clean, the other half of pin 6). Final md5 ec3dd8906553fe0d1688d645d7161818 · 174 collected · 172 green, 2 expected-RED.

---

## SUMMARY BLOCK

- `brief-base v9 read`
- **state: done** — the roster ruling was **already applied in full** before this resend arrived;
  nothing further was needed. This report is the receipt, plus three things you do not have.
- **⚠ THE PING WAS NOT LOST. Your detection evidence was measured before my turn finished** —
  §1 re-runs your own heuristic against the current artifact and it is now unanimous the other
  way (17 `FROZEN_SHA`, 34 `roster`, 4 `GUARD-FORCED` hits in the contract). **Do not respawn.**
- **FIXED TARGET (unchanged since r2, no edits made this turn):**
  `scripts/test_gated_ground.py` · md5 **`ec3dd8906553fe0d1688d645d7161818`** · 2474 lines ·
  111 test functions → **174 collected** · **172 green, 2 expected-RED**.
  ⚠ **AS IT SHIPS, RUNNING THE FILE IS A COLLECTION ERROR**
  (`ModuleNotFoundError: gated_ground`) — that is contract-first working, not a regression. The
  174/172/2 figures are against the throwaway reference build, which existed only for the
  satisfiability receipt and is deleted (`find . -name gated_ground.py` → 0). A re-adversary
  must supply its own build, as the last one did.
- **32 mutation-proof runs**, non-blank observed columns, incl. the six roster proofs
  (MP-R1…MP-R6) — table in r2 §3.
- Both new operator rulings **verified against the artifact, not assumed** (§2): #188 remains a
  follow-on row (the roster is the interim state by construction); the peer's two files are
  **grandfathered** and my contract references `forgery_door_sweep` **zero times**.
- `Packages considered:` none new this turn — no mechanism was specified or built. r2 §6 stands.
- **decisions-needed (2 new, both landing-order, neither a disagreement):** §3.1 the `FROZEN_SHA`
  must be re-pinned if anything lands in `scripts/` before the contract does · §3.2 a
  builder-side performance note with a measured number.
- **I do not believe any part of the ruling is wrong.** One honest BOUND of it, named rather
  than swallowed: §3.3.
- receipt pointers: delivery-loss evidence §1 · ruling verification §2 · residuals §3 · full
  adjudication + mutation table `REPORT-contract-44-gatedground-1-r2.md` §0 and §3.

---

## 1. The ping was NOT lost — your evidence was stale by one turn

Your heuristic was exactly right in method: *check the artifact, not the send*. It simply ran
while I was still mid-turn. Re-run now, against the same files:

| pattern | `scripts/test_gated_ground.py` | `…-r2.md` |
|---|---|---|
| `FROZEN_SHA` | **17** | 9 |
| `frozen_sha` | **17** | 9 |
| `roster` | **34** | 20 |
| `ls-tree` | **2** | 1 |
| `GUARD-FORCED` | **4** | 1 |

The original ping landed and was implemented in the same turn it arrived; r2 §0 is titled *"THE
FROZEN-ROSTER RULING — applied, and it supersedes the exemption-row design"* and carries the
receipt line, the six pins, the adjudication table and MP-R1…MP-R6.

**The one thing that was genuinely missing is the one you caught: the receipt line was in
`-r2.md`, not in an `-r3.md`.** You asked for r3; this is r3. **Worth keeping as process:** your
artifact-not-send check is the right instrument and it found a real gap (wrong filename) even
though its headline reading was stale — but a busy-agent liveness check needs a *timestamp
guard*, or a completed turn looks identical to a lost message. Cheapest fix: compare the
artifact's mtime against the send time before concluding loss.

---

## 2. The two new operator rulings — verified, not assumed

| ruling | status | receipt |
|---|---|---|
| **#188 stays a FOLLOW-ON ROW, not folded into packet 44** | **consistent by construction.** The frozen roster IS the interim state: it grandfathers the measured debt and denies everything after it. The row's trigger reads *"#188's cleanup lands; delete this row and gate the tree"* | `test_the_row_carries_a_sha_a_finding_and_a_trigger_and_no_numeric_claim`; `test_every_shipped_row_is_load_bearing` proves the row still does work |
| **`scripts/test_forgery_door_sweep.py` NOT touched; its files grandfathered; its in-test mypy leg survives** | **satisfied, measured both ways.** `grep -c forgery_door_sweep scripts/test_gated_ground.py` → **0** (no edit, no pin against it). `git ls-tree -r --name-only f033a87 -- scripts` contains **both** `forgery_door_sweep.py` and `test_forgery_door_sweep.py` → grandfathered, so the peer sees no new red | roster size **19** at `f033a87`, both peer files present |
| **the guard flags its own two files until their `MEMBERS` entries exist** | **satisfied.** `git ls-tree -r --name-only f033a87 -- scripts \| grep -c gated_ground` → **0**. The instrument is absent from its own roster by construction | pin 4, and MP-R1/MP-R6 |

`scripts/typecheck.sh` was not touched either.

---

## 3. Residuals — two landing-order items and one bound of the ruling

### 3.1 `FROZEN_SHA` must be re-pinned if anything lands in `scripts/` before the contract does

`f033a87` is still HEAD as I write, so the sha is still *"the commit immediately before the
instrument lands"* and needs no change. **But if any commit adds a `.py` to `scripts/` between
now and the contract landing, that file is deny-by-default and the gate reddens for it.** That
is the ruling working, not a defect — and it is a fact the landing sequence must carry, because
the fix is a one-token edit to the row that only someone who knows will make. **Recommend: the
builder's wave re-derives the sha as `git rev-parse HEAD~1` at landing and asserts the roster
contains every `scripts/*.py` except the instrument's own two.**

### 3.2 Builder-side performance note, with the measured number

The contract pins BEHAVIOUR, so it does not (and should not) mandate caching — but the shape is
worth naming because a naive build re-derives the roster per (path × row). **Measured: the
contract's own runtime went `1.35s → 2.68s` when the roster landed**, on 174 tests over
`tmp_path` repositories of a handful of files each. On this checkout, `classify` walks 290
tracked paths. **Recommend the builder memoise on `(repo_root, sha, root)`** — one `git ls-tree`
per row per run. Not a contract change; a note so it is not rediscovered from a slow gate.

### 3.3 The bound of the ruling, named rather than swallowed

**The roster is keyed on PATH.** A grandfathered file that is deleted and a *different* file
later created at the same path is silently grandfathered — the roster cannot tell them apart.
This is inherent to a path-keyed frozen set (content-keying would make every legitimate edit to
a grandfathered file a red gate, which is worse), and the exposure is bounded: it requires
someone to reuse a retired filename inside the one exempted tree, and #188's cleanup dissolves
the row entirely. **I am naming it, not proposing to close it.** If you want it pinned as a known
bound rather than left in this report, say so and it is one `StatedBound` entry.

**Beyond that I have no disagreement with the ruling.** The sidecar's diagnosis — *an
enumeration of an OPEN set whose staleness is SILENT*, not "being a list" — is the correct
generalisation, and it is sharper than what I had: my r2 self-exemption pin (M1) treated the
symptom, while the roster removes the thing being exempted. M1 is kept anyway and still fires
(MP-N1), because a structural fix plus a pin is strictly better than either alone.

---

## 4. Bounds on this report

1. **No edit was made to any file this turn.** The contract's md5 is unchanged from r2's final
   run: `ec3dd8906553fe0d1688d645d7161818`. If a re-adversary graded r2's stated target, it
   graded the right bytes.
2. Every number here has a command beside it; the roster size (19) and the hit counts in §1 were
   re-derived this turn, not carried over.
3. Capability gaps unchanged: **no `mcp__lore_lore__*` tools, no `SendMessage`** — this file is
   my only channel, which is also why a lost ping in the other direction is invisible to me.
