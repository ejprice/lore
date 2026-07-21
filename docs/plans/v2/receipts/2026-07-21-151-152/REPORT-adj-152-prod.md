# REPORT-adj-152-prod

brief-base v5 read

- **state**: done
- **deviations**:
  - `lore_findings action=get id_or_number=152` not run — lore's MCP tools were still connecting at
    spawn and I adjudicated from the tree, which is the durable source for this task. Flagged, not
    silently skipped.
  - Wrote no shared-`/tmp` scratch after `/tmp/adj152_base.txt` was overwritten mid-run by another
    process (see §6 D-1). All findings below are re-derived in-context, not read from that file.
- **decisions-needed**:
  - Ruling wanted on the EXTENSION population (§4): 23 production sites outside my 12 files name
    untracked `REPORT-*.md` files literally. Same defect class, not in my scope grant.
  - Ruling wanted on the 21 cloned docstring paragraphs (§5 O-1) — a DRY smell, not a citation bug.
- **receipt pointers**: §1 verification · §2 the 37-site verdict table · §3 the 5 LOAD-BEARING
  replacements · §4 population extension · §5 observations · §6 defects/flags

**Headline**: 37 base sites adjudicated — **33 PROVENANCE, 4 LOAD-BEARING**. Plus **1 LOAD-BEARING
site the brief's grep structurally could not see** (a citation hyphen-wrapped across a line break).
**No false claims found**: I independently re-derived the two numeric claims in scope ("the ten
ledger seams", "the ELEVENTH hand-rolled copy") and both are TRUE.

---

## 1. Verification — I did not inherit the lead's claim

```
$ git ls-files | grep -iE "blindreader|audit-102|audit-fix|adversary"
docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md
EXIT=0   (361 files tracked total)
```

**Observed, and it differs from the brief.** The brief said this returns NOTHING. It returns
**one** tracked file — a packet-03 adversary report archived under `docs/plans/v2/receipts/`.
That match is on the word "adversary" in a *filename*; nothing matching `blindreader`,
`audit-102`, or `audit-fix` is tracked. **The brief's conclusion holds** (every report cited in my
37 sites is untracked), but its stated evidence was slightly wrong, and the difference is
load-bearing: the repo **does** have a durable receipts directory. That is a real repointing target
the brief did not list, and it changes what "durable address" can mean here (§5 O-2).

I also confirmed the exit code before interpreting, per the brief. `EXIT=0` with one line of
output — a command that ran and matched, not a command that failed silently.

Separately, every `REPORT-*.md` filename named literally in production code was checked
individually against `git ls-files`: **17 distinct files, 17 UNTRACKED, 0 tracked.**

---

## 2. The 37-site verdict table

Population derived from the brief's bare grep, run by me:

```
$ git grep -nE "blindreader|audit-102|audit-fix-1|adversary" -- 'loremaster/loremaster/*.py' ':!loremaster/loremaster/store/_txn.py' | wc -l
37
```

Verdict key: **P** = PROVENANCE (leave it) · **LB** = LOAD-BEARING (repoint).

| # | file:line | quoted citation | verdict |
|---|---|---|---|
| 1 | `agents.py:385` | `calls (blindreader F3; see its docstring for the mechanism). This` | **P** |
| 2 | `agents.py:391` | `(adversary P-1): scout's reconnect ladder needs the RAW exhaustion` | **P** |
| 3 | `agents.py:482` | `(blindreader F3; see its docstring for the classify/self-heal/log` | **P** |
| 4 | `briefs.py:417` | `calls (blindreader F3; see its docstring for the mechanism). This` | **P** |
| 5 | `briefs.py:423` | `(adversary P-1): scout's reconnect ladder needs the RAW exhaustion` | **P** |
| 6 | `briefs.py:510` | `(blindreader F3; see its docstring for the classify/self-heal/log` | **P** |
| 7 | `briefs.py:935` | `# re-ack (blindreader F1): the RELATE never committed, so whatever` | **P** |
| 8 | `diff.py:519` | `(blindreader F3; see its docstring for the mechanism). This method's` | **P** |
| 9 | `diff.py:525` | `(adversary P-1): scout's reconnect ladder needs the RAW exhaustion` | **P** |
| 10 | `diff.py:611` | `(blindreader F3; see its docstring for the classify/self-heal/log` | **P** |
| 11 | `findings.py:426` | `(blindreader F3; see its docstring for the mechanism). This method's` | **P** |
| 12 | `findings.py:432` | `(adversary P-1): scout's reconnect ladder needs the RAW exhaustion` | **P** |
| 13 | `findings.py:538` | `(blindreader F3; see its docstring for the classify/self-heal/log` | **P** |
| 14 | `graph_surreal.py:385` | `(blindreader F3; see its docstring for the mechanism). This method's` | **P** |
| 15 | `graph_surreal.py:391` | `(adversary P-1): scout's reconnect ladder needs the RAW exhaustion` | **P** |
| 16 | `graph_surreal.py:505` | `(blindreader F3; see its docstring for the classify/self-heal/log` | **P** |
| 17 | `index/snapshots.py:250` | `(blindreader F3; see its docstring for the mechanism). This method's` | **P** |
| 18 | `index/snapshots.py:256` | `(adversary P-1): scout's reconnect ladder needs the RAW exhaustion` | **P** |
| 19 | `index/snapshots.py:343` | `(blindreader F3; see its docstring for the classify/self-heal/log` | **P** |
| 20 | `index/surreal_manifest.py:62` | `single-statement attempt (blindreader F3: the classify-and-signal decision` | **P** |
| 21 | `index/surreal_manifest.py:170` | `(blindreader F3; see its docstring for the mechanism). This method's` | **P** |
| 22 | `index/surreal_manifest.py:176` | `(adversary P-1): scout's reconnect ladder needs the RAW exhaustion` | **P** |
| 23 | `index/surreal_manifest.py:294` | `(blindreader F3; see its docstring for the classify/self-heal/log` | **P** |
| 24 | `memory/local.py:337` | `(blindreader F3; see its docstring for the mechanism). This method's` | **P** |
| 25 | `memory/local.py:343` | `(adversary P-1): scout's reconnect ladder needs the RAW exhaustion` | **P** |
| 26 | `memory/local.py:445` | `(blindreader F3; see its docstring for the classify/self-heal/log` | **P** |
| 27 | `scout.py:181` | `(blindreader F3). This function used to carry the ELEVENTH hand-rolled copy` | **P** |
| 28 | `scout.py:199` | ``Deliberately UNWRAPPED (adversary P-1, ``W1-SCOUTKILL``): unlike the ten`` | **LB** |
| 29 | `scout.py:210` | `(blindreader-dry-2 F7 / audit-fix-1 B1): every one of the ten ledger seams` | **LB** |
| 30 | `server.py:4449` | `# (contract-adversary §2). Below 1 teaches the valid range; above the` | **LB** |
| 31 | `store/surreal.py:166` | ``# :func:`~loremaster.store._txn.run_query` — blindreader F3) are called from`` | **P** |
| 32 | `store/surreal.py:411` | `(blindreader F3; see its docstring for the mechanism, including why a` | **P** |
| 33 | `store/surreal.py:425` | ``(adversary P-1, ``W1-SCOUTKILL``): scout's reconnect ladder needs the`` | **LB** |
| 34 | `store/surreal.py:566` | `(blindreader F3; see its docstring for the classify/self-heal/log` | **P** |
| 35 | `tasks.py:439` | `(blindreader F3; see its docstring for the mechanism). This method's` | **P** |
| 36 | `tasks.py:445` | `(adversary P-1): scout's reconnect ladder needs the RAW exhaustion` | **P** |
| 37 | `tasks.py:549` | `(blindreader F3; see its docstring for the classify/self-heal/log` | **P** |

**Totals: 33 P · 4 LB.** File counts reconcile with the brief's hand-list exactly
(surreal.py 4 · surreal_manifest.py 4 · briefs.py 4 · tasks.py 3 · scout.py 3 · memory/local.py 3 ·
snapshots.py 3 · graph_surreal.py 3 · findings.py 3 · diff.py 3 · agents.py 3 · server.py 1 = 37).

### Why the three big clusters are PROVENANCE — and why I checked before saying so

The brief specifically asked whether the repeated `blindreader F3` blocks are one claim repeated
across owners, and whether they should all repoint at the same address. **My answer: they are the
same claim repeated 21 times — and none of them should be repointed, because they already point at
a live in-tree address.**

The sentence is, verbatim: *"The session bootstrap is
`:func:`~loremaster.store._txn.bootstrap_session`` — the ONE shared implementation every connection
owner in the package calls (blindreader F3; **see its docstring for the mechanism**)."* The reader
is directed to a **symbol's docstring**, not to the report. `blindreader F3` is the historical
provenance of *who discovered it*; the mechanism itself is one `go-to-definition` away.

I did not take that on faith — **a PROVENANCE ruling on an empty pointer would be laundering**.
I read both targets in `store/_txn.py`:

- `bootstrap_session`'s docstring is ~45 lines and carries the entire mechanism: the thirty
  hand-rolled copies, the misclassification at HEAD, the measured **6.2%–34.4%** loss range with
  its protocol, the disposition rule, and the composed wall-clock budget.
- `run_query`'s docstring carries classify/self-heal/log, the `acquire`-inside-the-retry rule, and
  a full `Args:` block explaining why `label` and `logger` stay per-seam.

Both pointers resolve. Following `blindreader F3` would add **nothing** a reader cannot already
reach. That is the brief's PROVENANCE definition, met literally.

The same reasoning disposes of the `(adversary P-1)` cluster (rows 2, 5, 9, 12, 15, 18, 22, 25, 36):
the sentence *states its own reason in full* — *"scout's reconnect ladder needs the RAW exhaustion
type, so the wrap lives here, at the seam, not in the shared helper."* Nothing is left to look up.

And rows 3/6/10/13/16/19/23/26/34/37 already carry **durable finding numbers** — `finding #120/#108`
— sitting in the same parenthetical as the dangling token. A reader who wants the authority already
has it.

**Note the asymmetry with rows 28/33**, which look like the same cluster and are not: those carry
`W1-SCOUTKILL`, a *named wrong-build label*, and the claim attached to it is a counterfactual about
a build that was never shipped. That is not checkable from any docstring. See §3.

---

## 3. The 5 LOAD-BEARING sites — proposed durable addresses

Every proposed address was **verified to exist in the tree**, by name, before I proposed it.

### LB-1 · `scout.py:199` — `(adversary P-1, ``W1-SCOUTKILL``)`

The claim is a **counterfactual about a wrong build**: *"a wrap here would fly straight past that
ladder and kill the command channel dead, with no backoff and no reconnect."* No shipped code
demonstrates this; the only thing that can substantiate it is the test that builds the wrong version
and watches the ladder die. That test exists:

```
loremaster/tests/test_retry_seam.py:6884
  class TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType:
      async def test_the_socket_is_closed_and_the_raw_type_survives(...)
```

⚠ `W1-SCOUTKILL` is **itself durable** — it appears in `test_retry_seam.py:6884` and `:6964`. Only
`adversary P-1` dangles. **Minimal edit = drop that token, keep the label, add the pin:**

```
-    Deliberately UNWRAPPED (adversary P-1, ``W1-SCOUTKILL``): unlike the ten
+    Deliberately UNWRAPPED (``W1-SCOUTKILL`` — pinned by ``test_retry_seam.py``'s
+    ``TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType``): unlike the ten
```

### LB-2 · `scout.py:210` — `(blindreader-dry-2 F7 / audit-fix-1 B1)`

Authority for a **historical defect claim**: *"this function used to close nothing, leaking one
socket per failed connect — unbounded in a long-running process."* A reader cannot check a past leak
against present code; the regression pin is the only instrument. **Same test as LB-1** — it asserts
both halves ("socket is closed" **and** "raw type survives"):

```
-    (blindreader-dry-2 F7 / audit-fix-1 B1): every one of the ten ledger seams
+    (pinned by ``test_retry_seam.py``'s
+    ``TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType``): every one of the ten ledger seams
```

I deliberately do **not** propose a finding number here. `#120` was tempting and I could not
substantiate that it covers the socket leak specifically — proposing it would be exactly the
un-derived citation this task exists to remove.

### LB-3 · `store/surreal.py:425` — `(adversary P-1, ``W1-SCOUTKILL``)`

Same claim as LB-1, stated from the store side. Same address.

```
-        (adversary P-1, ``W1-SCOUTKILL``): scout's reconnect ladder needs the
+        (``W1-SCOUTKILL`` — pinned by ``test_retry_seam.py``'s
+        ``TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType``): scout's reconnect ladder needs the
```

### LB-4 · `server.py:4449` — `(contract-adversary §2)`

The citation is the authority for a **negative invariant**: *"that is a side effect a rejected call
must never have."* Nothing in the surrounding code shows the absence of a side effect — absence is
only demonstrable by a test. It exists:

```
loremaster/tests/test_comms_tool.py:2386
  class TestFleetLimitBounds:
      async def test_a_rejected_limit_never_touches_the_callers_row(...)
```

Token substitution (the comment will need rewrapping to 100 cols — a formatting consequence, not a
prose rewrite):

```
-        # (contract-adversary §2). Below 1 teaches the valid range; above the
+        # (pinned by ``test_comms_tool.py::TestFleetLimitBounds::
+        # test_a_rejected_limit_never_touches_the_callers_row``). Below 1 teaches
+        # the valid range; above the
```

### LB-5 · `briefs.py:940–941` — `(audit-fix-1 A6)` — **THE GREP COULD NOT SEE THIS ONE**

This site is **not** in the 37. It is invisible to the brief's grep — and to *any* line-oriented
grep — because the token is **hyphen-wrapped across a line break**:

```
briefs.py:940:  # ... one of FOUR guarded-CAS doors in the package (audit-
briefs.py:941:  # fix-1 A6: a hand-list here once named only two and quietly dropped a
```

Neither line contains the string `audit-fix-1`. I found it only by *reading* the block around
row 7. I then swept for the class:

```
$ git grep -nE "(audit|blindreader|adversary|REPORT|builder|contract|probe|slate|phase|cold)-$" -- 'loremaster/loremaster/*.py'
loremaster/loremaster/briefs.py:940
```

**Exactly one in production.** It is LOAD-BEARING: the citation is the authority for the count
**FOUR**, and for the history that a hand-list here once undercounted. The prose says *"the contract
quantifies over all four structurally"* — that structural pin is the durable address:

```
loremaster/tests/test_retry_seam.py:6551
  class TestNoGuardedCasHandlerReinterpretsExhaustedContention:
      def test_the_door_enumeration_matches_the_canonical_set(...)
```

```
-            # re-read. This is one of FOUR guarded-CAS doors in the package (audit-
-            # fix-1 A6: a hand-list here once named only two and quietly dropped a
-            # third) — its three siblings carry the identical guard, with the
+            # re-read. This is one of FOUR guarded-CAS doors in the package (an EXACT-SET
+            # pin — ``test_retry_seam.py::TestNoGuardedCasHandlerReinterpretsExhaustedContention
+            # ::test_the_door_enumeration_matches_the_canonical_set``: a hand-list here once
+            # named only two and quietly dropped a third) — its three siblings carry the identical guard, with the
```

---

## 4. Population extension — what the brief's pattern does not reach

The brief asked me to report other report-shaped citations. There are **three tiers beyond the 37**,
and tier C is larger than the assigned population.

### Tier A — line-wrapped (1 site, in scope)
`briefs.py:940` — see LB-5. Adjudicated above.

### Tier B — bare section-refs with no report name (in my 12 scope files)
These name a section of a report **without naming the report**. They are *more* dangling than the
37: a reader cannot even determine which document to fail to find. Each gets its own line per repo
law:

| file:line | citation | note |
|---|---|---|
| `agents.py:389` | `(the F4 ruling: ...)` | mechanism stated in full inline |
| `briefs.py:421` | `(the F4 ruling: ...)` | idem |
| `diff.py:523` | `(the F4 ruling: ...)` | idem |
| `findings.py:430` | `(the F4 ruling: ...)` | idem |
| `graph_surreal.py:389` | `(the F4 ruling: ...)` | idem |
| `index/snapshots.py:254` | `(the F4 ruling: ...)` | idem |
| `index/surreal_manifest.py:174` | `(the F4 ruling: ...)` | idem |
| `memory/local.py:341` | `(the F4 ruling: ...)` | idem |
| `tasks.py:443` | `(the F4 ruling: ...)` | idem |
| `store/surreal.py:420` | `(the F4 ruling)` | idem |
| `agents.py:297` | `the fix for the v4 audit's D1 defect` | names a defect id only |
| `agents.py:853` | `(the v4 audit's D1 finding: ...)` | idem |
| `briefs.py:149` | `(design doc §4/§7; v4 audit D2 fix)` | design doc ref is durable; `v4 audit D2` is not |
| `briefs.py:816` | `(v4 audit D2 fix)` | names no document |
| `server.py:4632` | `(v4 audit ...)` | idem |
| `server.py:4694` | `(v4 audit D1 fix)` | idem |
| `server.py:5218` | `(v4 audit ...)` | idem |
| `briefs.py:1120` | `cold-audit F1: measured 6.1× leaf-elapsed at 11× rows` | a MEASURED number with no durable receipt |
| `briefs.py:1145` | `pinned #103 / cold-audit F1` | `#103` **is** durable — token is redundant |
| `findings.py:579` | `(audit-findings #2)` | names no document |
| `findings.py:854` | `(audit-findings #1)` | idem |
| `index/snapshots.py:519` | `(docs-audit constraint)` | idem |
| `index/snapshots.py:535` | `(docs-audit constraint)` | idem |
| `scout.py:183` | `audit-polish-1 P1` | idem |
| `server.py:904` | `audit-w4a finding #3` | idem |
| `server.py:3081` | `audit-w4a finding #1 (fixed)` | idem |
| `server.py:2875` | `(audit-waveb-1 finding #1)` | idem |
| `server.py:1279` | `N1 guard (cutover-audit)` | idem |
| `server.py:6034` | `closes config-audit F3` | idem |

I did **not** assign P/LB verdicts to tier B — it is outside my scope grant, and assigning verdicts
would be me deciding scope. Two flagged as worth a look regardless: `briefs.py:1120` (a measured
performance number whose only authority is a deleted file) and `briefs.py:1145` (already durable via
`#103`; the token is pure redundancy and is the cheapest possible deletion).

### Tier C — literal `REPORT-*.md` filenames (36 production sites, 17 files, **all untracked**)

This is the **most dangling class in the tree** and the brief's pattern misses all of it. These do
not merely allude to a report — they name a file, in backticks, that a reader will try to open.

**12 sites in my 12 scope files**: `agents.py:23` · `briefs.py:24, 82, 901, 1014` ·
`graph_surreal.py:1652` · `server.py:1341, 2394, 3998, 4403, 4533, 7834`.

**23 sites in production files OUTSIDE my scope list**: `impact.py` ×6 · `surreal_schema.py` ×5 ·
`symbols.py` ×4 · `map.py` ×3 · `search.py` ×2 · `render.py` ×2 · `sanitise.py` ×1.
(Plus `_txn.py:466`, the other agent's.)

Untracked-status confirmed **individually, per file**, not in bulk:
`REPORT-audit-tweaks.md` · `REPORT-builder-102.md` · `REPORT-builder-flip-w2.md` ·
`REPORT-builder-flip-w4b.md` · `REPORT-c1-audit-fixwave.md` · `REPORT-c1-builder-mint.md` ·
`REPORT-c1-contract-ledgers.md` · `REPORT-c1-contract-schema.md` · `REPORT-c1f-contract-migration.md` ·
`REPORT-phase0-audit-1.md` · `REPORT-probe-7061-c1.md` · `REPORT-slate-audit-graphres.md` ·
`REPORT-slate-audit-searchstore.md` · `REPORT-slate-builder-s1.md` · `REPORT-slate-builder-s2.md` ·
`REPORT-slate-builder-search.md` · `REPORT-slate-scout-s2.md` — **17 of 17 UNTRACKED.**

**This needs an operator ruling.** It is the same defect, at ~equal volume, and #152 will look
closed while 23 out-of-scope sites still name deleted files.

---

## 5. Observations

**O-1 — 21 clones of one paragraph is a DRY smell, and repo law has a name for it.**
The `blindreader F3` mechanism paragraph is duplicated near-byte-identically across 11 files. I ruled
each PROVENANCE and I stand by that — but the *shape* is what `CLAUDE.md`'s ONE IMPLEMENTATION
section warns about: change how the bootstrap works and you must hand-edit 21 docstrings, and the
one you miss is a prose defect no gate can see. That is the P8d "natural-language surfaces whose
consistency with code no gate checks" class, pre-loaded. **Not a citation problem and not my call** —
but the cheapest fix is one sentence per seam pointing at `_txn.py`, with the mechanism living only
in `_txn.py`. Raising it, per scope law; not proposing an edit.

**O-2 — a durable repointing target the brief did not list.**
`docs/plans/v2/receipts/2026-07-19-packet03/` is a **tracked** directory holding four preserved
agent reports. If the operator prefers preserving the *original* authority over swapping in a test
name, the mechanism already exists: archive the report into `docs/plans/v2/receipts/<wave>/` and cite
that path. That is a genuinely different remedy from the one the brief assumed, and it is the only
one that keeps the reasoning a reader can actually read. **Operator's call** — I designed my §3
proposals for the brief's stated approach (test names / finding numbers).

**O-3 — the test tree carries this problem too, and already knows it.**
`test_surreal_harness.py:51–54` contains an explicit in-tree note: *"HOW TO RESOLVE THE
``blindreader-150 F*`` / ``audit-150 R*`` CITATIONS IN THIS FILE ... the reports they name
(``REPORT-blindreader-150.md``, ``REPORT-audit-150*.md``) are UNTRACKED"*. A prior wave met this
exact problem and solved it by **documenting the danglingness in place** rather than repointing.
That is a third remedy, cheaper than either, and it is already precedent in this repo.

---

## 6. Defects and flags

**D-1 · `/tmp` collision during my own run (process hygiene, not code).**
I wrote my base grep to `/tmp/adj152_base.txt`; a later read returned **test-tree** results I never
generated — another agent's output, same-named file. Nothing in my findings derives from it (I
re-derived everything in-context), but this is a live cross-agent collision hazard: two agents on one
box writing predictable `/tmp` names will silently overwrite each other's evidence. **A wrong count
read back from a clobbered file would have been undetectable.** Recommend per-agent scratch paths in
briefs.

**D-2 · No false claims found — and I checked rather than assumed.**
The brief warned that a citation's claim may be false (as #151's turned out to be). I re-derived the
two numeric claims in scope, from the tree:

- *"the ten store/manifest/ledger seams"* (`scout.py:199, 210`) — **TRUE.** `bootstrap_session` has
  exactly 11 call sites: 10 in `_ensure_connection` methods (`agents`, `briefs`, `diff`, `findings`,
  `graph_surreal`, `snapshots`, `surreal_manifest`, `memory/local`, `store/surreal`, `tasks`) + 1 in
  scout's module-level `_open_command_connection`.
- *"the ELEVENTH hand-rolled copy"* (`scout.py:181`) — **TRUE.** That is the 11th call site.

⚠ **A near-miss worth recording**: `git grep -l "async def _ensure_connection"` returns **11 files,
including `scout.py`** — which contradicts "the ten" on a first read. It is not a contradiction:
scout owns an `_ensure_connection` that does **not** call `bootstrap_session` (it is the *command*
channel's, distinct from `_open_command_connection`). The counts are two different populations, and
conflating them is precisely the error `CLAUDE.md`'s #102 section says it made itself. I nearly filed
it as a defect; keying the count on the actual `bootstrap_session` call sites resolved it.

**D-3 · The clean split between the two `blindreader F3` shapes was not obvious.**
Rows 28/33 sit inside blocks that read like the row-2 cluster, and a bulk pass keyed on
`(adversary P-1)` would have swept them into PROVENANCE with their nine siblings. They differ because
their claim is a **counterfactual about an unshipped build** — unverifiable from any docstring, only
from a test. If this adjudication is re-run or extended, that is the discriminator to key on:
*does the claim describe code that exists, or code that must never exist?* The second kind always
needs a test address.
