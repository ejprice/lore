# REPORT-archive-466: close-out archival of the #466 / #503 cycle reports

## SUMMARY BLOCK
- `brief-base v17 read`
- **State:** done. Written 2026-09-26 on `feat/surreal-unification`, base HEAD `e557c65`.
- **Deviations:** none from the brief. One wording choice: the contract-503 header says #506 is *still open* and that the build corrected the *docstring*. The detector behaviour still matches argv text. See §Header 2.
- **Packages considered:** none. No mechanism specified. Documentation move plus comment and docstring repoints only.
- **Odoo-20 portability:** n/a. No Odoo seam touched.
- **Reuse ledger:** none. No new reusable symbol in the repo. The sweep and splitter instruments are pasted in §Instruments.
- **Decisions needed:** (1) Fork R-A/R-B in §Fork: should prose *agent-name* section citations such as `close-466 R1` / `T1–T4` become archived-path addresses too? I recommend yes, as a separate small pass. (2) `loremaster/tests/test_migration_wire.py` fails `ruff format --check` at HEAD `e557c65`. The drift predates this change. See §Flags.
- **Receipts:** §Sweep table (31 repointed, file:line each) · §Name-only mentions · §Gates (270 passed; ruff clean) · §Commit.

## Capability check (brief-base §4)
Everything the brief demanded was available. grep/rg are hook-blocked (#473), so the whole sweep uses awk as the brief directed. Lore was used for finding #506 (`lore_findings get`). The repoint sweep is grep-class work by design. It is a literal, anchor-free textual seam over prose, so the dogfood protocol's case (b) applies and no graph question was involved.

## Step 1: moves
All 17 files were confirmed TRACKED and clean (`git ls-files` + `git status --porcelain` per file, empty status) before the move, and each was then `git mv`'d into `docs/plans/v2/receipts/2026-09-26-466-503/`:
contract-466 · stub-466 · impl-466 · refactor-466 · contract-466-d1 · impl-466-d1 · refactor-466-d1 · close-466 · measure-503 · contract-503 · stub-503 · impl-503 · refactor-503 · contract-503-d1 · impl-503-d1 · refactor-503-d1 · contract-503-d2 (each `REPORT-<name>.md`). None was untracked. No other `REPORT-*.md` was touched.

## Step 2: sweep
Instrument: §Instruments A, run with the `REPORT-` prefix. It does a literal `index()` match on each bare basename, with no `.md` and no prefix anchor, over every tracked text file. It excludes the 17 archived reports and `REPORT-lead-63c.md`. A match is assigned to the longest sibling name, so `REPORT-contract-466` never double-counts `REPORT-contract-466-d1`.
- **Before:** 31 hits in 6 files. All were root-level `REPORT-<name>.md` addresses in comments or docstrings. None was in a runtime string.
- **Repoint:** `REPORT-<name>.md` → `docs/plans/v2/receipts/2026-09-26-466-503/REPORT-<name>.md`, done with a literal sed per name. Section anchors (`§Item 2`, `§Pins-d`, `§Forks F1`, …) are untouched. The longer path pushed 29 lines past ruff's E501 110 limit. The HEAD baseline for all 6 files was `All checks passed!`, checked via `git show HEAD:<f> | ruff check --stdin-filename`. Those 29 lines were split at a word boundary by §Instruments B, with each continuation keeping its own `# ` or indent prefix. The result is ragged, not reflowed, and every citation path stays on one line.
- **After:** the sweep still reports 31 hits outside the excluded set, and **all 31 are the archived-path form**, because the bare needle matches inside the new path by design. **Zero** bare root addresses remain. The only other hits are in the archived files themselves (43 lines across 14 of the 17; recounted before commit) and `REPORT-lead-63c.md` (lines 1358 and 1360, left as written because it is a live append-only log).

### Sweep table (post-edit line numbers)
| file:line | citation | verdict |
|---|---|---|
| loremaster/tests/test_loopback_serving.py:45 | `REPORT-refactor-466` | repointed |
| loremaster/tests/test_loopback_serving.py:59 | `REPORT-contract-466-d1` | repointed |
| loremaster/tests/test_loopback_serving.py:773 | `REPORT-refactor-466` | repointed |
| loremaster/tests/test_loopback_serving.py:844 | `REPORT-refactor-466` | repointed |
| loremaster/tests/test_loopback_serving.py:953 | `REPORT-refactor-466-d1` | repointed |
| loremaster/tests/test_loopback_serving.py:1014 | `REPORT-refactor-466-d1` | repointed |
| loremaster/tests/test_loopback_serving.py:1019 | `REPORT-close-466` | repointed |
| loremaster/tests/test_loopback_serving.py:1156 | `REPORT-refactor-466` | repointed |
| loremaster/tests/test_loopback_serving.py:1333 | `REPORT-refactor-466-d1` | repointed |
| loremaster/tests/test_loopback_serving.py:1436 | `REPORT-contract-503` | repointed |
| loremaster/tests/test_migration_wire.py:78 | `REPORT-measure-503` | repointed |
| loremaster/tests/test_migration_wire_budget_503.py:7 | `REPORT-measure-503` | repointed |
| loremaster/tests/test_migration_wire_budget_503.py:19 | `REPORT-contract-503` | repointed |
| loremaster/tests/test_migration_wire_budget_503.py:45 | `REPORT-measure-503` | repointed |
| loremaster/tests/test_no_raw_listener_in_test_trees.py:54 | `REPORT-refactor-466` | repointed |
| loremaster/tests/test_no_raw_listener_in_test_trees.py:71 | `REPORT-refactor-466-d1` | repointed |
| loremaster/tests/test_no_raw_listener_in_test_trees.py:622 | `REPORT-refactor-466` | repointed |
| loremaster/tests/test_no_raw_listener_in_test_trees.py:652 | `REPORT-refactor-466` | repointed |
| scripts/test_concurrent_wire_acceptance.py:20 | `REPORT-refactor-466` | repointed |
| scripts/test_concurrent_wire_acceptance.py:356 | `REPORT-close-466` | repointed |
| scripts/test_pytest_workers_503.py:7 | `REPORT-measure-503` | repointed |
| scripts/test_pytest_workers_503.py:21 | `REPORT-contract-503` | repointed |
| scripts/test_pytest_workers_503.py:41 | `REPORT-refactor-503` | repointed |
| scripts/test_pytest_workers_503.py:464 | `REPORT-refactor-503` | repointed |
| scripts/test_pytest_workers_503.py:513 | `REPORT-refactor-503` | repointed |
| scripts/test_pytest_workers_503.py:663 | `REPORT-contract-503-d1` | repointed |
| scripts/test_pytest_workers_503.py:851 | `REPORT-refactor-503` | repointed |
| scripts/test_pytest_workers_503.py:888 | `REPORT-refactor-503-d1` | repointed |
| scripts/test_pytest_workers_503.py:944 | `REPORT-refactor-503-d1` | repointed |
| scripts/test_pytest_workers_503.py:1012 | `REPORT-refactor-503-d1` | repointed |
| scripts/test_pytest_workers_503.py:1094 | `REPORT-refactor-503-d1` | repointed |
| REPORT-lead-63c.md:1358 | `REPORT-close-466` | left: live append-only log (brief) |
| REPORT-lead-63c.md:1360 | `REPORT-close-466` | left: live append-only log (brief) |

### Name-only mentions (swept with no `REPORT-` prefix; none is an address; none was edited)
Archiving a FILE cannot make a prose mention of a NAME resolve (CLAUDE.md, the #152/#153 two-populations note). Each line gets its own verdict:
| file:line | mention | verdict |
|---|---|---|
| loremaster/loremaster/testing/loopback.py:398 | `close-466 R1` | section cite by agent name. Fork R-B candidate |
| loremaster/tests/test_loopback_serving.py:3 | author ``contract-466`` | authorship credit. Left |
| loremaster/tests/test_loopback_serving.py:44 | author ``contract-466-d1`` | authorship credit. Left |
| loremaster/tests/test_loopback_serving.py:140 | `close-466 T2` | section cite by agent name. Fork R-B candidate |
| loremaster/tests/test_loopback_serving.py:200 | `contract-466 wrong build` | provenance of a wrong build. Left |
| loremaster/tests/test_loopback_serving.py:709 | `close-466 R1` | section cite by agent name. Fork R-B candidate |
| loremaster/tests/test_loopback_serving.py:922 | `close-466 T1` | section cite by agent name. Fork R-B candidate |
| loremaster/tests/test_loopback_serving.py:950 | `close-466 R1` | section cite by agent name. Fork R-B candidate |
| loremaster/tests/test_loopback_serving.py:1190 | `refactor-466-d1 R4` + author ``contract-503`` | R4 is an R-B candidate. The author part is a credit. |
| loremaster/tests/test_migration_wire_budget_503.py:3 | author ``contract-503`` | authorship credit. Left |
| loremaster/tests/test_no_raw_listener_in_test_trees.py:4 | author ``contract-466`` | authorship credit. Left |
| loremaster/tests/test_no_raw_listener_in_test_trees.py:69 | author ``refactor-466-d1`` | authorship credit. Left |
| loremaster/tests/test_no_raw_listener_in_test_trees.py:733 | `close-466 T3` | section cite by agent name. Fork R-B candidate |
| loremaster/tests/test_no_raw_listener_in_test_trees.py:813 | `close-466 T3` | section cite by agent name. Fork R-B candidate |
| loremaster/tests/test_no_raw_listener_in_test_trees.py:834 | `close-466 T4` | section cite by agent name. Fork R-B candidate |
| scripts/concurrent_wire_acceptance.py:191 | `close-466` | provenance mention. Fork R-B candidate |
| scripts/test_concurrent_wire_acceptance.py:3 | author ``contract-466`` | authorship credit. Left |
| scripts/test_concurrent_wire_acceptance.py:413 | `close-466 — the CLASS behind item 3` | section cite by agent name. Fork R-B candidate |
| scripts/test_pytest_workers_503.py:3 | author ``contract-503`` | authorship credit. Left |
| scripts/test_pytest_workers_503.py:34 | author ``contract-503`` | authorship credit. Left |
| scripts/test_pytest_workers_503.py:36 | author ``contract-503-d1`` | authorship credit. Left |
| scripts/test_pytest_workers_503.py:48 | author ``contract-503-d2`` | authorship credit. Left |
| scripts/test_pytest_workers_503.py:353 | `contract-503-d1, lead ruling 1` | provenance of a ruling. Left |
| scripts/test_pytest_workers_503.py:887 | author ``contract-503-d2`` | authorship credit. Left (same line wraps the repointed `REPORT-refactor-503-d1` cite onto :888) |
| skills/lore-deploy/tests/test_loopback_home.py:3 | author ``contract-466`` | authorship credit. Left |
| REPORT-contract-63c-i-a-a28.md:87 | `refactor-466's acceptance run` | a live report owned by another agent, mentioning an agent by name. Left (brief: do not touch other REPORTs) |

## Fork (surfaced, not settled)
The brief's step 2 says to "REPOINT every in-tree citation of those names" and gives the sweep pattern as the report basename (`REPORT-close-466`).
- **R-A (applied):** only the `REPORT-<name>.md` addresses are citations. That covers the 31 rows above.
- **R-B:** the 13 prose mentions of the form `close-466 R1` / `T1–T4` / `refactor-466-d1 R4` are also citations. They point at a report section, but without a file address. Converting them would mean writing e.g. `docs/plans/v2/receipts/2026-09-26-466-503/REPORT-close-466.md §Item 1 (R1)`. The labels are verified to exist: `REPORT-close-466.md` has §Item 1 (R1) and §Item 4 with a T1–T4 table, and `REPORT-refactor-466-d1.md` has §Step 1 with an R1–R10 table.
I recommend R-B as a follow-up one-concern commit. I stayed at R-A because the brief defined the sweep pattern with the `REPORT-` prefix.

## Step 3: headers
### Header 1: `REPORT-refactor-466-d1.md`
The brief's text was prepended verbatim as line 1, above the report's own `brief-base v16 read` receipt. Its claims were verified before writing. `REPORT-refactor-466-d1.md` §Step 4 line "Reading chosen … **(A, applied)** … no API change". `REPORT-close-466.md` §Item 2 has the heading "`serve_http(shutdown_timeout_s=…)` parity (already landed in `8d42c27`; verified here)". `git show 8d42c27 -- loremaster/loremaster/testing/loopback.py` adds `shutdown_timeout_s: float = DEFAULT_SHUTDOWN_TIMEOUT_S` and threads it into `_loud_teardown`.
### Header 2: `REPORT-contract-503.md`
Prepended text: *"⚠ PREMISE FALSE IN PART: the Phase-0 premise that the session detector keys on "executable plus lore path" was FALSE (it matches argv text; finding #506, still open 2026-09-26); corrected in the build (scripts/_pytest_sessions.py::other_pytest_sessions docstring states the argv-text rule) and in this report's own §Forks F2."*
Verification: `REPORT-contract-503.md` §Forks F2 (line 82 pre-header) says that description "is FALSE at HEAD `884ca63`". Finding #506 was read via `lore_findings get 506` on 2026-09-26 and is **open**, kind bug. `other_pytest_sessions` at HEAD matches `PYTEST_ARGV_MARKER in part` over argv, and its docstring says "whose argv mentions pytest".
**Wording note:** the brief said "corrected in the build". What the build corrected is the *description*, not the *behaviour*. The argv-text over-match is still live and ledgered as #506, so the header says so and does not imply that #506 is fixed.

## Step 4: gates (2026-09-26, working tree = HEAD + this change)
Other lore pytest sessions were live, observed via `ps` at launch, so the run used `-n 12` per the brief and #503.
```
uv run pytest -q -p no:cacheprovider -n 12 loremaster/tests/test_loopback_serving.py loremaster/tests/test_migration_wire_budget_503.py loremaster/tests/test_migration_wire.py loremaster/tests/test_no_raw_listener_in_test_trees.py scripts/test_concurrent_wire_acceptance.py scripts/test_pytest_workers_503.py scripts/test_gate_currency.py
...
270 passed, 20 warnings in 44.67s
exit=0
```
```
uv run ruff check <the 6 edited .py files>
All checks passed!
```
The post-edit sweep is described in §Step 2 "After". It found zero bare root addresses outside the archive and `REPORT-lead-63c.md`.

## Flags
- **`ruff format --check` drift, pre-existing:** `loremaster/tests/test_migration_wire.py` would be reformatted. The receipt is `git show HEAD:loremaster/tests/test_migration_wire.py | uv run ruff format --check --stdin-filename … -` → exit 1. The drift is `_BUILTIN_TOOLS` packed several names per line. It is not caused by this change and was not fixed, to avoid putting an unrelated hunk into a docs commit. `ruff format` is not one of the CLAUDE.md-listed gates (`ruff check` is). Lead's call.
- Untracked files were also swept for the old root addresses and there were 0 hits.

## Instruments (verbatim, brief-base §1)
### A: the bare sweep (`sweep.sh <prefix>`; `names.txt` = the 17 basenames minus `REPORT-`/`.md`, one per line)
```bash

#!/usr/bin/env bash
# usage: sweep.sh <prefix>   prefix "REPORT-" for addresses, "" for bare agent-name mentions
cd /home/ejprice/PycharmProjects/lore
S=$(dirname "$0")
git ls-files -z | xargs -0 -I{} sh -c 'test -f "{}" && printf "%s\n" "{}"' \
 | awk -v names="$S/names.txt" -v pfx="$1" '
BEGIN{ while((getline n < names)>0){ N[n]=1; X["REPORT-" n ".md"]=1 } X["REPORT-lead-63c.md"]=1 }
{ f=$0; b=f; sub(/.*\//,"",b); if (b in X && f==b) next; if (b in X && f ~ /receipts\/2026-09-26-466-503\//) next; print f }' \
 | while IFS= read -r f; do
   file -b --mime-encoding "$f" | awk '/binary/{exit 1}' || continue
   awk -v names="$S/names.txt" -v pfx="$1" -v F="$f" '
   BEGIN{ while((getline n < names)>0) N[n]=1 }
   { for (n in N) { s=$0; t=pfx n; while ((i=index(s,t))>0) { nxt=substr(s,i+length(t),3);
        # longest-match: skip if this hit is actually a longer sibling name (-d1/-d2)
        if (nxt ~ /^-d[0-9]/ && ((n substr(nxt,1,3)) in N)) { s=substr(s,i+length(t)); continue }
        print F ":" FNR ": [" n "] " substr($0,1,220); s=substr(s,i+length(t)) } } }' "$f"
 done | sort -u
```
### B — the long-line splitter (`split_long.py <files…>`)
```python
"""Split over-long comment/docstring lines that contain the archive path at a word boundary.

Only lines containing ARCHIVE and longer than LIMIT are touched; the continuation keeps the
line's own prefix (``# `` for comments, the leading whitespace otherwise).
"""
import re
import sys
from pathlib import Path

LIMIT = 110
ARCHIVE = "docs/plans/v2/receipts/2026-09-26-466-503/"


def split_line(line: str) -> list[str]:
    """Return the line split into pieces each <= LIMIT, continuation carrying the prefix."""
    comment = re.match(r"^(\s*#\s?)", line)
    prefix = comment.group(1) if comment else re.match(r"^(\s*)", line).group(1)
    pieces = []
    while len(line) > LIMIT:
        cut = line.rfind(" ", len(prefix) + 1, LIMIT + 1)
        if cut == -1:
            break
        pieces.append(line[:cut].rstrip())
        line = prefix + line[cut + 1 :]
    pieces.append(line)
    return pieces


for name in sys.argv[1:]:
    path = Path(name)
    out = []
    for line in path.read_text().split("\n"):
        out.extend(split_line(line) if ARCHIVE in line and len(line) > LIMIT else [line])
    path.write_text("\n".join(out))
```

## Commit
