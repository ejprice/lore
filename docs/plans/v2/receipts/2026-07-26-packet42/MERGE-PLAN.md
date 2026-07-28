# Packet 42 — BASELINE + MERGE PLAN

> ⚠ **SUPERSEDED SYMBOLS (dated record):** mentions `_BRIEF_PUBLISH_`, a retired prefix (the
> private mint-retry constants deleted by finding #108 — `_txn.retry_on_conflict` owns that
> policy now). It appears here only inside REPRODUCED TEST OUTPUT: this record quotes the
> packet-11i/03b doc-banner failure that packet 42 inherited and verified as unrelated to its
> own work. Preserved as-written per the archive law; read it as history, not instruction.

Written 2026-07-27, before any merge. Every number below is a **measurement taken by the lead**,
not a recollection. The plan exists because the merge is the riskiest remaining step: it is the one
place where two packets' greens can be confused for each other.

---

## 1. BASELINE — the last known-good state of each side

| | branch `pkt42-prevent-the-leak` | primary `feat/surreal-unification` |
|---|---|---|
| head | **`2c7142b`** | **`de7c8c3`** |
| commits since `6a21fb6` | **28** | **52** |
| files changed since `6a21fb6` | **65** | **93** |
| **full suite** | **1 failed / 7403 passed** / 17 skipped / 3 xfailed | **0 failed / 7642 passed** / 36 skipped / 3 xfailed |
| typecheck | 0 errors, 5 members | (not re-measured — primary is not mine to gate) |
| ruff | clean | — |

**The branch's one failure is `test_retired_symbols.py::test_no_file_references_a_retired_symbol`** —
`_BRIEF_PUBLISH_` in three packet-11i/03b dated records lacking SUPERSEDED banners. **Primary fixed
it at `a7e6ea9`** (*"the suite's last red closes"*), so the merge is expected to CLOSE it, not
inherit it.

**Packet 42's leak probe at `2c7142b`** (the property the packet exists for, both directions):

```
SURREAL_PASS · client_secret · session_token · dict value · nested map · quoted Basic · Digest
    -> all redacted
uuid path · git SHA · function name
    -> all INTACT
```

### The number that makes attribution possible
**Primary is 0-failed.** I feared inheriting packet 04a's *"60 pins, 26 RED"* (`48537c3`) — but 04a
closed out at `7737c36` and those pins are green. **Therefore: the post-merge target is 0 FAILED,
and ANY failure after the merge is caused BY the merge.** No attribution guesswork, no reading
another packet's in-flight red as my own regression. This measurement is the whole reason to take a
baseline before merging rather than after.

---

## 2. THE CONFLICT SURFACE — 6 files, derived not guessed

`comm -12` over both changed-file sets (65 ∩ 93):

| file | mine | theirs | expected difficulty |
|---|---|---|---|
| `uv.lock` | regenerated | regenerated | **regenerate after merge; never hand-merge** |
| `pyproject.toml` | +`lorerunes` in members / `mypy_path` / `testpaths` | +numpy, scipy, scikit-learn, kubernetes (`38c9774`) | additive, different regions |
| `loremaster/pyproject.toml` | +`python-dotenv`, +`lorerunes` | +deps | additive, different regions |
| `scripts/token_survey.py` | 33+/33− — shape B, the resolver, dead constants | 17+/13− — `#198` one percentile implementation (`ea7406e`) | **different concerns; verify BOTH survive** |
| `loremaster/tests/_surreal_harness.py` | 1+/1− | 2+/2− | trivial |
| `docs/plans/v2/42-…-sanitizer.md` | riders applied by hand | same riders from `61c8964` | should converge; verify no rider is lost |

**Nothing in `logging_setup.py`, `config.py`, `factory.py`, `lorerunes/` or any packet-42 contract
test is touched by primary.** The packet's own surface is uncontested.

---

## 3. THE PLAN

**Direction: merge PRIMARY INTO THE BRANCH first.** Conflicts then resolve in the worktree, where
they can be tested in isolation, and **primary is never left in a broken state**. Only once the
branch is green on top of primary does the branch land. The reverse direction would put the
resolution work on the trunk.

1. **Commit everything.** Working tree clean before starting; the merge must be the only variable.
2. **Archive the reports FIRST** (`git mv` into `docs/plans/v2/receipts/2026-07-26-packet42/`, never
   `rm` — repo law, #152/#153). Twelve `REPORT-*.md` at root; they are cited by the ruling waves,
   and a merge is exactly when an uncited-and-deleted report becomes unrecoverable.
3. **`git merge de7c8c3`** into the branch. Resolve the six.
   - `uv.lock`: take neither side — `uv sync --all-packages` regenerates it.
   - The two `pyproject.toml`s: union of dependencies; **then verify `lorerunes` survives in all of
     `members`, `mypy_path`, `testpaths`** (its absence is silent — registration site #4 exempts a
     package from every ∀ pin).
   - `token_survey.py`: **both concerns must survive** — packet 42's shape-B/resolver work AND
     #198's single percentile implementation. Check `#198`'s pin passes, not just mine.
4. **Re-run `./scripts/registration_sites.py`** — the merge adds primary's 52 commits' files, and a
   new registration site may have arrived with them. Derive; do not assume.
5. **Full gates on the merged branch:** full suite (**target 0 failed**) · `./scripts/typecheck.sh`
   5 members · `uv run ruff check .`.
6. **Re-run the packet-42 leak probe.** The gates above do not prove the packet's own property; a
   merge can silently revert a regex. Both directions — leaks redacted AND recovered data intact.
7. **The R41 close-out check, and it is not optional:** diff every pin NAME cited in a report
   against the committed tree. R41 is the finding that a mutation-proven pin never landed and no
   gate could tell. A merge is the second-most-likely moment for that to happen.
8. **Fast-forward primary to the merged branch.** Primary was 0-failed before and must be 0-failed
   after.
9. **THEN deploy** — and only then, because of #134 (lore cannot deploy against a worktree: `.git`
   is a file naming a gitdir outside the container mount).

---

## 4. RISKS, each with its detection

| risk | why it is plausible | how it gets caught |
|---|---|---|
| `lorerunes` silently dropped from a registration site during conflict resolution | three of the sites are in files BOTH sides edited; absence fails nothing | step 4 (`registration_sites.py`) + step 5 typecheck |
| `#198`'s percentile fix lost while resolving `token_survey.py` | my diff there is 3× theirs, so mine "looks like" the whole file | step 3 — run #198's own pin, not just packet 42's |
| a packet-42 regex silently reverted | merge resolution of a file neither side conflicts on is not reviewed | step 6 — the leak probe is the only instrument that tests the property |
| a cited pin absent from the merged tree | R41's exact shape, and merges drop hunks | step 7 |
| the deploy fails on #134 | the worktree topology is unchanged by merging | step 9 runs from the PRIMARY checkout, not the worktree |

## 5. WHAT THIS PLAN DOES NOT COVER
The **deploy** itself — rebuild + recreate (never restart), the before/after traceback receipt, the
smoke, and the INDEX Log line. Those follow a green merge and are planned separately, because a
deploy plan written before the merge would be written against a tree that does not exist yet.
