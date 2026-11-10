# coldaudit-58-ca58-receipts — packet 58 cold audit, dimension: RECEIPT VERIFICATION

brief-base v27 read · brief project v7 read

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read · **State: done-with-deviations** (2026-11-10).
- **Verdict (dimension: receipt verification), measured 2026-11-10 on a scratch_copy of `aa4ea04`:** the PRODUCTION
  claim holds: `fa073bc..aa4ea04 -- loremaster/loremaster` is `tasks.py` only, 5+/3−, one f-string whose evaluated text
  equals the old concatenation (`'DELETE $ssx_old_rec->blocks'` both), plus a docstring that no test reads. **No builder
  receipt has a TREE= equal to the graded commit's**, because the builder ran its gates in the shared live tree. So I
  reran the mismatched gates, targeted: **29 files / 1977 ids → 2 failed / 1974 passed / 1 skipped**. The 2 reds are
  both registry-owned by `packet-64b-i-contract`, and the result is identical to contract-58-r53 §CLEANUP's
  before/after counts. Currency `--legs typecheck,ruff` gives **RED_ORPHANED 0** (typecheck RED_ADJUDICATED 50 to
  64b-i, ruff GREEN). Every contract and adversary receipt I was asked to check exists, has a TREE= header, and has the
  count and EXIT it claims.
- **Deviations:** (1) I have no Agent tool, so there was no haiku-runner fan-out. I ran every command myself. (2) During
  setup I moved the copy's `REPORT-*.md` files aside to fingerprint a clean tree. That moved 25 TRACKED files too. I
  restored them (`git status` then showed only the 4 untracked reports again) and re-fingerprinted. The clean TREE below
  comes from the 4 untracked reports held aside in `ca58/ca58-receipts-hold/`. (3) I used grep for textual seams (which
  tests name the two changed hunks or quote the docstring numbers; the scratch copy has no index). That is grep case
  (b), and I am saying so here.
- Packages considered: none — no mechanism specified.
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: none (one read-only junit helper, pasted in §INSTRUMENTS).
- **Graded:** aa4ea04 · HEAD-at-report: 96ea7f5 · DIFFERENT (1 ahead: a docs-only erratum, no `loremaster/loremaster` change).
- Decisions needed: (1) should the lead require builders to run gates in a scratch_copy, so that TREE= can ever match
  (F-1)? (2) close-out: 9 packet-58 `REPORT-*.md` files are still TRACKED at the repo root at aa4ea04 (R-4).
- Pointers: §RECEIPT TABLE · §PRODUCTION DIFF · §RERUNS · §FINDINGS · §INSTRUMENTS.

## ROUTING TABLE (written before the first sweep)
| step | tier | who |
|---|---|---|
| scratch copy, checkout, provenance | 1 | self (no Agent tool in this run, deviation 1) |
| log header/count extraction (≈25 logs) | 1 | self (one command each, output short) |
| currency gate + targeted reruns | 1 | self (should be a haiku-runner; not available) |
| receipt validity verdicts, production-equivalence judgement | 3 | self (an audit verdict, which sampling cannot catch) |

## Copy provenance
- `scratch_copy.sh` → `…/27ef6c0a-…/scratchpad/ca58/ca58-receipts`, then `git checkout aa4ea04 -- .`, `rev-parse HEAD` =
  `aa4ea0426e53dadd0e905f83092d764b350e4d46`. Status showed only the 4 untracked REPORT files.
- `loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58/ca58-receipts/loremaster/loremaster/__init__.py`.
- Clean graded-commit fingerprint (4 untracked reports held aside): `HEAD=aa4ea04…`, `DIRTY_FILES=0`,
  `TREE=74f0aff3da7badf310543d4942dc4951972c6e205314b2052bd3da76d5f4ade6`. With the 4 reports present: `TREE=40f080f6…`.
  `tasks.py` md5 at aa4ea04 = `cb9b15f7…`; at fa073bc = `ee791e44…`.

## §PRODUCTION DIFF (the brief's claim, checked with git)
- `git merge-base --is-ancestor`: fa073bc, 1d1e8e3, 9e2f59d, a77f72e, 99389cd, 548fe54, 54c7595, a494ae2 and 83359e9 are
  all ancestors of aa4ea04.
- `git diff --stat <c>..aa4ea04 -- loremaster/loremaster` gives exactly `tasks.py | 8 +++++---` for c ∈ {fa073bc,
  1d1e8e3, a77f72e, 99389cd, 54c7595}. The hunks:
  1. `_supersede_transaction`: `"DELETE $ssx_old_rec->" + BLOCKS_RELATION` → `f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"`.
     Evaluated in the copy: both give `'DELETE $ssx_old_rec->blocks'`, `==` True.
  2. `_pack_heal_chunks` docstring: the two measured timings, each with its conditions.
- The changed text reaches no test. grep over `loremaster/tests` + `scripts` for `_pack_heal_chunks|_supersede_transaction|ssx_old_rec`
  finds 0 files, and for `7\.25|12\.2 s|quiet host` finds 0 relevant hits (3 unrelated `§12.2` prose hits).
- Non-test, non-doc paths changed in fa073bc..aa4ea04: `tasks.py`, `scripts/pending_contracts.yaml` (−370, the 58
  entry deleted), `scripts/probe_{heal_curve,heal_delete_plan,hub_txn,supersede_delete}_58.py`,
  `scripts/test_forgery_door_sweep.py` (+1), `scripts/test_parked_contracts.py` (another session). No `pyproject`/`uv.lock` change.

## §RECEIPT TABLE
Log roots: B = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs`,
C = `…/27ef6c0a-…/scratchpad/c58r53/logs`, A = `…/27ef6c0a-…/scratchpad/a58r53/logs`.

| report § | gate | log | header HEAD / DIRTY / TREE | count line (read from log) | EXIT | claim matches log? | tree vs aa4ea04 |
|---|---|---|---|---|---|---|---|
| builder final3 | targeted pytest (119-file runset + r53 file) | B/final3.log | 9e2f59d / 31 / 18b4d3ef… | 188 failed, 8456 passed, 47 skipped | 1 | yes | **MISMATCH** (live tree; header 22:50:57 local, checkpoint fa073bc 22:54:01, mid-run) |
| builder final3 | base 60b51c4 | B/base2.log | 60b51c4 / 0 / b64e788c… | 426 failed, 7755 passed, 47 skipped | 1 | yes (scratch copy of 60b51c4) | n/a (base) |
| builder final3 | "0 new / 238 fixed" | junit set-diff (mine) | — | 0 new; 238 = **237 now green + 1 no longer collected** | — | partly (F-3) | — |
| builder final3 | typecheck | B/typecheck_final3.log | 9e2f59d / 31 / 18b4d3ef… | Found 50 errors in 15 files | 1 | yes | MISMATCH |
| builder final3 | ruff | B/ruff_final3.log | same | All checks passed! | 0 | yes | MISMATCH |
| builder final3 | currency | B/currency_final3.log | same | typecheck RED_ORPHANED 30 (the 58 self-destructs), ruff GREEN | 1 | yes | superseded (registry changed in a77f72e) |
| builder §REGREEN | targeted pytest, 4 files | B/regreen.log | 54c7595 / 5 / c21f0479… | 1 failed, 318 passed | 1 | yes | **MISMATCH** (live tree) |
| builder §REGREEN | ruff | B/ruff_regreen.log | 54c7595 / **6** / 6b2f94ca… | All checks passed! | 0 | yes | MISMATCH; the tree changed DURING the pytest run (ruff ran at 23:49:09, inside pytest's 23:48:55–23:49:38 window) |
| builder §REGREEN | typecheck | B/typecheck_regreen.log | 54c7595 / 5 / c21f0479… | Found 50 errors in 15 files | 1 | yes | MISMATCH |
| builder §REGREEN | currency | B/currency_regreen.log | 54c7595 / **7** / 84ddd3d6… | typecheck RED_ADJUDICATED 50 (64b-i), ruff GREEN | 1 | yes | MISMATCH |
| contract §RIDER3 | plus | C/rider3-plus.log | 1d1e8e3 / 15 / d5c221ce… | 1 failed, 437 passed | 1 | yes | production = fa073bc exactly (cp `tasks.py` ee791e44, no `loremaster/loremaster` diff vs HEAD); tests = a77f72e bytes |
| contract §RIDER3 | minus (mutation_proof) | C/rider3-minus.log | same | 34 failed, 404 passed; LANDED once; restored ee791e44; PROOF HELD | 0 | yes | as above |
| contract §SAT | SAT on REF2 | C/sat-r53.log | 9e2f59d / 31 / 6314ea4b… | 315 failed, 9323 passed, 47 skipped | 1 | yes | a reference (REF2 tasks.py e5d19642), not the build, by design |
| contract §GATES g2 | verify-registry · currency · secret typing | C/{verify-registry,currency,secret-typing}-g2.log | 1d1e8e3 / 16 / 69c07373… · dad3a318… · dad3a318… | EXIT 0 · RED_ADJUDICATED 50 + ruff GREEN · 69 passed | 0 · 1 · 0 | yes | live tree; superseded by g3 and by my currency run |
| contract §CLEANUP | before | C/cleanup-before.log | a77f72e / 3 / 6678c8bb… | 2 failed, 1974 passed, 1 skipped | 1 | yes | scratch copy of a77f72e |
| contract §CLEANUP | after | C/cleanup-after.log | a77f72e / 25 / 2ace38ca… | 2 failed, 1974 passed, 1 skipped | 1 | yes; `compare_runs.py` re-run by me: 1977/1977, 0 changed | live tree, MISMATCH, so rerun (§RERUNS) |
| contract §CLEANUP | gates g3 | C/{verify-registry,currency,secret-typing}-g3.log | a77f72e / 25 / 2ace38ca… | EXIT 0 · RED_ADJUDICATED 50 + ruff GREEN · 69 passed | 0 · 1 · 0 | yes | live tree; superseded by my currency run |
| adversary REFERENCE/SAT | SAT on own reference | A/a77f72e/sat-ref.log (byte-identical to A/sat-ref.log) | 40535c9 (scratch commit over d5ec901 over a77f72e) / 5 / 0bd93f0e… | 1 failed, 716 passed (714 + 3 probes = 717) | 1 | yes | a reference (tasks.py c6378f09), by design. The test swap to 99389cd bytes happened at 23:44:07, after the SAT (23:33), so the SAT used a77f72e test bytes |

Corroboration that final3 ran am-17 production: all 33 of contract-58-r53's declared r5.3 ids
(`c58r53/declared_red_r53.txt`) PASS in `B/final3.xml`. These are the ids that `rider3-minus` proved red on pre-am-17
`tasks.py` 3447cd97. My `junit_outcomes.py` gives `{'pass': 33}`. This shows final3 had the am-17 properties. It does
not show byte equality with fa073bc.

## §RERUNS (mismatched receipts, targeted, on the clean aa4ea04 copy, TREE 74f0aff3…)
| gate | command | log | EXIT | count line |
|---|---|---|---|---|
| currency typecheck,ruff | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `…/scratchpad/ca58/logs/ca58-receipts-currency.log` | 1 | typecheck RED_ADJUDICATED 50 (packet-64b-i-contract) · ruff GREEN · pytest NOT_RUN (leg-filtered; #621) → **RED_ORPHANED 0** |
| am-17 targeted set (adversary's 15-file `sat_set.txt`, ⊇ REGREEN's 4 and RIDER3's 11; collect-only 714 first) | `systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 .venv/bin/python -m pytest -q -n 8 --timeout=300 -p no:cacheprovider -rfE --junitxml=… $(cat ca58-receipts.set.txt)` | `…/scratchpad/ca58/logs/ca58-receipts-regreen-rerun.log` | 1 | **1 failed, 713 passed**. The 1 = `test_reanchor_58_r4_state.py::…[findings.py::_run_guarded -> findings.py::_run_guarded]`, owned at `scripts/pending_contracts.yaml` (packet-64b-i-contract) |
| cleanup-set remainder (14 files, collect-only 1263 first) | same shape, `ca58-receipts.cleanup-extra.txt` | `…/scratchpad/ca58/logs/ca58-receipts-cleanup-rerun.log` | 1 | **1 failed, 1261 passed, 1 skipped**. The 1 = `test_reanchor_58_r3_cas_seam.py::…[findings.py::_run_guarded]`, owned by packet-64b-i-contract |
Union: 1977 ids → 2 failed / 1974 passed / 1 skipped. This equals contract §CLEANUP before and after, now on the
graded bytes.

## §FINDINGS
- **F-1 (minor, HIGH): the builder's final3 and §REGREEN receipts cannot be verified against the graded commit.**
  The builder ran them in the shared live tree (`haiku-run-KBS16k.log.sh`: `cd /home/ejprice/PycharmProjects/lore`).
  - Their TREE= values (18b4d3ef…; c21f0479… / 6b2f94ca… / 84ddd3d6…) cannot equal aa4ea04's (74f0aff3…).
  - In §REGREEN the tree changed during the pytest run itself: DIRTY went 5 → 6 → 7 across the gates.
  - The fa073bc checkpoint was committed 3 minutes into final3's 22.5-minute run.
  - By brief-base §1 these receipts are void. The production claim behind them is TRUE (§PRODUCTION DIFF).
  - The targeted rerun on aa4ea04 re-establishes them: RED_ORPHANED 0; 1974/1977 passed, 2 reds both 64b-i-owned.
- **F-2 (residual, HIGH): the builder's final3 covered fa073bc production with OLDER test bytes.**
  - a77f72e, 99389cd and 83359e9 changed tests/probes afterwards: 6 of the rider-3 files plus `_reanchor_58_support.py`
    differ (md5 table in my notes command).
  - My rerun covers the am-17 and cleanup sets (29 files) on the graded bytes. The 119-file declared set at aa4ea04
    bytes is covered only by the packet's one full suite (another agent).
- **F-3 (minor, HIGH on the count, MEDIUM on whether it matters): "238 BASE reds now green" is 237 green + 1 no longer
  collected.**
  - The missing id: `test_reanchor_58_r4_state.py::TestTheFiredLedgerEqualsTheDerivedDomain::test_every_root_verb_and_write_index_fires_and_the_caller_gets_the_SAME_instance[tasks.py::_reanchor_stragglers -> tasks.py::_reanchor_stragglers]`.
  - It is red in base2 and absent from final3. The derived domain re-keyed (adversary-58-r53 names
    `[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]` as WB2's killer).
  - Likely benign, but the report's sentence counts a vanished member as "now green".
- **R-1 (residual): contract §SAT says REF2 was copied "at ~03:51Z".** REF2's `tasks.py` mtime is 22:44:57 local
  (03:44:57Z), and the SAT started 03:45:23Z. The md5 (3447cd97 base + delta → e5d19642) is right; the time is off by
  about 6 minutes. That matters only because final3 (03:50:57Z) already had the am-17 build.
- **R-2 (residual): contract §GATES says "TREE moves between rows only by this report's appends".** I cannot verify
  that in a live tree (g2 rows 12 s apart: 69c07373… → dad3a318…). It is superseded by g3 and by my currency run.
- **R-3 (residual, pre-existing, #621 open): `--currency --legs typecheck,ruff` exits 1 and prints "CURRENCY: FAIL"
  on a clean run.** It renders the deliberately excluded pytest leg as an orphan. Every receipt of this gate in this
  packet is EXIT=1 for that reason, so EXIT alone cannot tell a clean run from a real failure. Already filed as #621.
- **R-4 (close-out, HIGH): aa4ea04 TRACKS 25 `REPORT-*.md` files at the repo root.** Nine of them are packet 58's own
  (`REPORT-{adversary,contract}-58*.md`). CLAUDE.md "ARCHIVE REPORTS" requires them `git mv`'d to
  `docs/plans/v2/receipts/…` before an image build.
- **R-5 (not verified by me): the adversary's §INCIDENT may have left TEST-store debris on `:18000` (#486 class).**
  I did not enumerate the store.

## §INSTRUMENTS (pasted verbatim; scratch, read-only helpers)
`ca58/junit_outcomes.py` (declared ids → outcome in a junit xml):
```python
"""junit_outcomes.py <junit.xml> <ids-file>: print each declared id's outcome in the junit file (pass/fail/skip/ABSENT)."""
import sys
import xml.etree.ElementTree as ET
def node_id(tc):
    cls = tc.get("classname", ""); name = tc.get("name", "")
    parts = cls.split(".")
    for i in range(len(parts), 0, -1):
        path = "/".join(parts[:i]) + ".py"
        rest = parts[i:]
        yield "::".join([path, *rest, name])
outcomes = {}
for tc in ET.parse(sys.argv[1]).getroot().iter("testcase"):
    o = "fail" if tc.find("failure") is not None or tc.find("error") is not None else ("skip" if tc.find("skipped") is not None else "pass")
    for nid in node_id(tc):
        outcomes[nid] = o
ids = [l.strip() for l in open(sys.argv[2]) if l.strip()]
from collections import Counter
c = Counter(outcomes.get(i, "ABSENT") for i in ids)
print(dict(c))
for i in ids:
    if outcomes.get(i, "ABSENT") != "pass": print(outcomes.get(i, "ABSENT"), i)
```
The final3-vs-base2 set-diff: an inline `python3 -I -` over both junit files that keys testcases on `classname::name`.
It computes final-fails − base-fails (0), base-fails − final-fails (238), and base-fails absent from final (1).
