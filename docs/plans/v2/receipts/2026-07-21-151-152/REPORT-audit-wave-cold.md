# REPORT-audit-wave-cold — COLD AUDIT of the #151/#152 wave

brief-base v5 read

state: **done — NO-GO**
deviations:
- HEAD MOVED MID-AUDIT: a 17th commit `01e7885` (INDEX.md Log entry) landed while I worked. Audited; docs-only, no code/test delta. My findings stand at `01e7885`.
- Two mutation proofs mutated the REAL tree (not a scratch copy) with `cp -a` content backups; both restored and proven byte-exact by md5 + empty `git diff`. Backups: `/tmp/coldaudit/backup-3556869/`, `/tmp/coldaudit/bk2/`.
- CWD trap fired on me TWICE (tenth and eleventh instances in this work), once while restoring a mutated file. Caught both; tree verified clean.
decisions-needed:
- D1 — six false "RED today" claims survive `db9973b` ("retire the **last** false RED claims"); TWO were created by this wave. Fix now or ledger?
- D2b/D2c — a FALSE line citation `:1242` in PRODUCTION (`_txn.py:884`) plus 5 stale ones in `test_retry_seam.py`, all falsified by the wave's OWN `352db0e`, and a builder's explicit "Verified line-stable" that answered the wrong question.
- D3 — `test_retry_seam.py:5205-5209` still teaches the RETIRED report-deletion law; `968883d`'s own message queued this fix and it was never applied.
- D4 — `~/.claude/orchestration/brief-base.md` was NOT updated (outside repo); #153's own fix is half-shipped.
- (D2a — `CLAUDE.md:522`'s false "15 citations resolve at a stroke" — **already corrected by the lead mid-audit**; recorded, no action owed.)
receipt POINTERS: §1 targets 1–2 probes · §2 D1 · §3 D2 · §4 D3/D4 · §5 targets 5–7 · §6 gates · §RESIDUALS · §OVERLAP

---

## VERDICT: **NO-GO**

The behaviour half of #151 is **CONFIRMED FIXED**, measured end-to-end with controls (§1). The
prose half is not. **This wave shipped, at minimum, seven new or surviving false claims of the
exact class it exists to close — including one in PRODUCTION code, one in STANDING REPO LAW
(`CLAUDE.md`), and two born inside the wave's own commits.** Every one is green at ruff, mypy and
the entire test suite, because no gate reads English. That is the NO-GO class verbatim.

Nothing I found is a *behavioural* regression. The tree is functionally correct. It is the wave's
**completeness and honesty claims** that fail.

---

## 1. TARGETS 1 & 2 — #151 IS ACTUALLY FIXED. **CONFIRMED, by measurement.**

Probes: `/tmp/coldaudit/probe_151.py`, `/tmp/coldaudit/probe_scout_txn.py`.
Provenance receipt printed by both: `loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (the real tree — no scratch copy was used for these).

| seam | driven to exhaustion | label | url | ENGINE'S OWN TEXT | verdict |
|---|---|---|---|---|---|
| `bootstrap_session` DEFINE NAMESPACE | yes | `store.bootstrap.define_namespace.rejected` | `ws://probe-host:19999` | present | **PASS** |
| `bootstrap_session` `use()` | yes | `store.bootstrap.select_database.rejected` | present | present | **PASS** |
| `bootstrap_session` DEFINE DATABASE | yes | `store.bootstrap.define_database.rejected` | present | present | **PASS** |
| `scout._scout_query` | yes | `command_subscriber.query.rejected` | `None` (documented bound) | present | **PASS** |
| `CommandSubscriber._consume_live` | yes (swallowed, no raise) | `command_subscriber.live.rejected` | `None` | present | **PASS** |
| `CommandSubscriber._safe_kill` | yes (swallowed, no raise) | `command_subscriber.kill.rejected` | `None` | present | **PASS** |

Raised message on the bootstrap path, verbatim:
`SurrealDB operation gave up after 5 attempts over 0.036s (retryable conflict); see the server log for the full engine detail`
— and the record that hint points at now genuinely exists and carries the triple. **The
"see the server log" promise is kept.** (Pre-fix, measured by the control below, the record held
`{attempts, elapsed_seconds}` and nothing else.)

**POSITIVE CONTROL 1** (proves the probe can see the pre-fix hole): calling `retry_on_conflict`
with `label=None` — the literal pre-fix bootstrap shape — produced
`extras={"attempts": 5, "elapsed_seconds": 0.038}` with `label`/`url`/`engine_error` **all absent**,
and the probe reported it. The probe discriminates.

**MEASURED SIDE-FACT confirming #156's ruling**: on the swallowed `_consume_live` path the caught
`TxnContentionExhaustedError` has `__cause__ = None`. The retired allowlist clause ("the engine's
text rides the traceback") was indeed FALSE, and the operator's chosen repair (label both seams
rather than reword the clause) is the one that makes the artifact real.

### Target 2 — the exemption allowlist. **HONEST. Evidence MEASURED, not read.**

`_ATTRIBUTED_BY_ANOTHER_MECHANISM` contains exactly one entry: `("store/_txn.py", "execute_transaction")`, count 1. I enumerated all driver call sites independently: **8** (scout ×3, bootstrap ×3, `run_query` ×1 which threads `label`/`url` for all ten single-statement seams, `execute_transaction` ×1). Only `execute_transaction` is unlabelled. The floor `_MIN_KNOWN_RETRY_DRIVER_CALL_SITES = 8` matches.

I **RAN** `execute_transaction` to contention exhaustion rather than reading its evidence (this was the previous audit's entire finding):

```
LOG WARNING store.retry.exhausted        extras={"attempts": 5}
LOG ERROR   store.transaction.rolled_back extras={"statement_index": 1, "statement_count": 2,
            "status": "ERR", "engine_result": "...This transaction can be retried",
            "failed_statements": [...]}
```
`_log_rollback` **DOES** fire on the exhaustion path and **DOES** carry the engine's text plus the
failing statement index. **The exemption's evidence is TRUE when run.**

**POSITIVE CONTROL 2**: with `_log_rollback` monkeypatched to a no-op, the probe found **0**
rollback records. The probe can see the mechanism's absence.

### MUTATION PROOFS (both gates)

Both were run against the REAL tree with `cp -a` content backups; both restored byte-exact
(`md5sum -c` OK, `git diff --stat` empty).

- **§10 label gate.** Dropped `label=` from `scout._safe_kill`'s driver call → **3 pins RED**:
  `test_every_call_into_the_driver_passes_a_label`,
  `test_scouts_kill_exhaustion_carries_a_label_OF_ITS_OWN`,
  `test_scouts_kill_exhaustion_carries_the_ENGINES_OWN_TEXT`. (3 failed, 31 passed.)
  Bonus receipt: with the label gone, `engine_error` went **empty** — proving scout's comment
  ("the driver suppresses the engine's text unless a label is passed") is TRUE, not aspirational.
- **bootstrap `url=` gate.** Dropped `url=` from `tasks.py`'s `bootstrap_session` call →
  **10 pins RED**, including `test_every_bootstrap_session_call_passes_a_url` and
  `test_each_production_owner_logs_ITS_OWN_url_on_bootstrap_exhaustion[TaskLedger]`.

Independently verified: **11** production `bootstrap_session` call sites, **all 11** pass `url=`
(agents, briefs, diff, findings, graph_surreal, index/snapshots, index/surreal_manifest,
memory/local, scout, store/surreal, tasks). The INDEX's "eleven owners" claim is **CORRECT**.

---

## 2. **DEFECT D1 — six false "RED today" claims survive the commit titled "retire the LAST false RED claims". Two were created by this wave.**

`db9973b`'s message: *"24 of 26 false 'RED today' claims retired to past tense … **Two sites left untouched with reasons**."*

Derived (bare, anchor-free, per repo law) — `git grep -ciE 'red today' -- loremaster/`:

| rev | occurrences | files |
|---|---|---|
| `b3e7687` (pre-retirement) | **31** | 13 |
| `db9973b` → HEAD | **7** | 3 |

`git diff b3e7687..db9973b` removed exactly **24** such lines, added 0. So 31 − 24 = **7 survive,
not 2.** The population derivation (26) was **5 short of the tree** — the ninth time in this
session a hand-list lost to the grep, and it happened inside the commit whose own message names
"the name-list lesson recurring inside the fix for it".

Per-site verdict on all 7 (no wholesale classification):

| site | claim | test state | verdict |
|---|---|---|---|
| `test_retry_seam.py:7528-7533` | *"`url=`, which `bootstrap_session` **does not yet accept**, so all four fates die on a `TypeError` … Once the signature lands, this becomes a pure NON-REGRESSION pin"* | GREEN | **FALSE — BORN IN THIS WAVE.** Written by `d2d7b2c`; falsified by `352db0e` four commits later, in the same wave. |
| `test_retry_seam.py:8651` | `"""**RED TODAY.** … `_txn.py:1242` does not, and cannot"` | GREEN (531 passed) | **FALSE — BORN IN THIS WAVE.** Written by `d5fd333`; the pin passes, and the line number is wrong (see D2b). |
| `test_retry_seam.py:793` | *"Every pin here is red today with an ImportError naming `retry_on_conflict`/`RetryableConflictSignal` — **the names do not exist yet**"* | GREEN | **FALSE.** Pre-existing (`9d29111`); survived a commit that swept this file. |
| `test_retry_seam.py:196` | *"the ~20 pins here that **ARE behaviourally red today**"* | GREEN | **FALSE.** Pre-existing (`9d29111`); same file. |
| `test_retired_symbols.py:438` | *"""RED today at every site below."* | GREEN (38 passed) | **FALSE.** Pre-existing (`00f4301`). |
| `test_txn_contention.py:8` | *"this module cannot even be COLLECTED … `TxnContentionExhaustedError` **does not exist yet**"* | GREEN | **FALSE.** Pre-existing. |
| `test_retry_seam.py:5543` | *"The pin **was** red today for the RIGHT reason"* | GREEN | **OK** — past tense, correctly retired. |

**6 of 7 are false at HEAD.** Two of them the wave created itself. The commit's completeness claim
("the LAST") is false, and #157 — the finding that exists to carry the deliberate remainder — does
not list them.

### D5 — and the class is BIGGER than "RED today". The grep pattern could not see the other half.

`db9973b`'s message already noticed the hole and did not widen the sweep: *"two stale-tense section
banners in `test_graph_surreal.py` that the briefed patterns structurally could not see, because
`return [] today` carries no adjacent `RED` token — the name-list lesson recurring inside the fix for
it."* Correct diagnosis; the sweep was not re-run on the generalisation.

Swept for the sibling phrasing (`does not exist yet` / `does not yet accept` / `not yet exist`):
**22 sites in 19 files**. Individually verified against the tree — **11 are FALSE at HEAD**, each
naming a module that demonstrably exists:

| site | claims | module exists? |
|---|---|---|
| `test_map.py:55` | *"Expected RED: `loremaster.map` does not exist yet"* | **YES** — FALSE |
| `test_map.py:301` | *"the module under contract does not exist yet"* | **YES** — FALSE |
| `test_impact.py:46` | *"Expected RED: `loremaster.impact` does not exist yet"* | **YES** — FALSE |
| `test_impact.py:266` | *"the module under contract does not exist yet"* | **YES** — FALSE |
| `test_diff.py:47` | *"`loremaster.diff` does not exist yet"* | **YES** — FALSE |
| `test_scout.py:11` | *"the module does not exist yet"* | **YES** (`scout.py`) — FALSE |
| `test_scout.py:69` | *"`loremaster.scout` module does not exist yet"* | **YES** — FALSE |
| `test_snapshots.py:63` | *"`loremaster.index.snapshots` does not exist yet"* | **YES** — FALSE |
| `test_indexer_snapshot_wiring.py:47` | *"`loremaster.index.snapshots` also does not exist yet"* | **YES** — FALSE |
| `test_surreal_schema.py:25` | *"the module does not exist yet"* | **YES** (`store/surreal_schema.py`) — FALSE |
| `test_comms_schema.py:54` | *"`loremaster.store.surreal_schema` (the symbols do not exist yet)"* | **YES** — FALSE |

Individually verified as **NOT false** (no wholesale classification):
`test_message_ledger.py:32` — TRUE, `loremaster.messages` genuinely does not exist (that is the
packet-03 committed RED); `test_memory_ledger.py:172` — about a runtime fixture directory, not the
tree; `_sdk_guard.py:279` and `test_retry_seam.py:2071` — conditional/forward-looking, not assertions
about HEAD; `test_resilient_db.py:3` — past tense, correct.
The remaining 6 (`_finding_fakes.py:116`, `_task_fakes.py:139`, `test_comms_schema.py:196`,
`test_map.py:1498`, `test_map.py:1560`, `test_memory_backend.py:92`, `test_render_seam_pins.py:429`)
each need their own verdict from someone with the packet context; I am not classifying them
wholesale.

**Scope note for the operator:** these were never in the wave's declared scope (which was "RED
today"), so this is not a broken promise — but #157 is the row that exists to carry the remainder
and it does not mention this population either. It should.

---

## 3. **DEFECT D2 — new FALSE citations shipped by the fix for false citations.**

### D2a — `CLAUDE.md:522` (STANDING REPO LAW) carried a FALSE measured number. ✅ **FIXED BY THE LEAD MID-AUDIT.**

> ⚠ STATUS: while this audit was running, `CLAUDE.md:521-532` was rewritten to
> *"seven of the eight were cited ZERO times and the eighth once, so it repaired exactly ONE
> dangling address"*, plus a new paragraph recording the miss as its own receipt. **That matches
> my measurement exactly.** The finding below is preserved as the derivation; no action is owed.
> Finding **#153** and `968883d`'s commit message still carry the old "15".

> *"Archiving eight surviving #150-wave reports (`7d2ff44`) made **15 citations resolve at a stroke**, for one `git mv`."*

Measured, under **every** scoping I could construct:

| reading | measurement |
|---|---|
| citation sites naming any of the 8 archived reports, repo-wide, at `3222e84` (pre-archive) | **1** (a single `REPORT-blindreader-150.md`; the other **seven were cited ZERO times**) |
| resolving citation OCCURRENCES in `loremaster/`, `3222e84` → `7d2ff44` | 5 → 6 (**+1**) |
| distinct resolving NAMES in `loremaster/`, `3222e84` → `7d2ff44` | 3 → 4 (**+1**) |
| repo-wide resolving occurrences, `3222e84` → `7d2ff44` | 37 → 71 — but +33 of that is the archived reports **citing each other**, i.e. the archive resolving its own internal references. Circular; not "citations that would otherwise have needed repointing away". |
| bare-name prose form (`blindreader-150` etc.), pre-archive | **16** — and these are mentions of the AGENT'S NAME (`blindreader-150 F3`), not `REPORT-*.md` addresses. Archiving a file cannot make a prose mention of a name "resolve"; there is no address to follow. |

**No scoping yields 15.** Provenance, derived: an agent's report
(`docs/plans/v2/receipts/2026-07-21-151-152/REPORT-adj-152-tests.md:11`) claimed archiving *three*
reports "would resolve **17** sites at a stroke" — itself derived from the bare-name form. The
number in standing law is a third value that matches nothing, inherited without re-derivation.

**Why this is the most serious item.** CLAUDE.md's own text says *"Re-measure inherited numbers
before trusting them — a figure you didn't measure is a rumor"*, and records the #102 precedent of
*"an un-derived count inside the law about un-derived counts."* This is that, again, in the law
itself. It is also **self-contradictory within finding #153**, which states both *"made 15 in-tree
citations RESOLVE"* and *"seven of the eight are cited zero times"* — the eighth is cited once.

The same false number is in **three** places: `CLAUDE.md:522`, finding **#153**, and `968883d`'s
commit message.

### D2b — a FALSE line citation shipped into PRODUCTION code, wrong at birth.

`loremaster/loremaster/store/_txn.py:884` (written by `352db0e`, THE #151 FIX):

> `# ONE exception is ``execute_transaction``'s nested ``_attempt`` (:1242, LEAD RULING`

`_txn.py:1242` is, and was at `352db0e`, a **docstring line** (*"statement's index and raw result) immediately before EITHER raise; the"*). `execute_transaction`'s nested `_attempt` is at **1276**, its bare raise at **1293**. Derived:

| rev | the four `from error` sites | the bare raise |
|---|---|---|
| `352db0e~1` / `d2d7b2c` | 1002, 1010, 1018, 1103 | **1242** |
| `352db0e` … `98980bd` | 1036, 1044, 1052, 1152 | **1291** |
| HEAD | 1038, 1046, 1054, 1154 | **1293** |

`352db0e` itself added +34 lines above them. So the author copied `:1242` from the pre-fix
measurement **into the commit that invalidated it**. It has never been correct in production.

### D2c — the same five stale numbers in the test tree, in PRESENT-TENSE prose.

`test_retry_seam.py:8459-8462` (written by `d5fd333`, this wave):
> *"MEASURED: FOUR sites raise `from error` (`:1002`, `:1010`, `:1018`, `:1103`); `:1242`, inside `execute_transaction._attempt`, raises `RetryableConflictSignal()` BARE. THE LEAD INSPECTED `:1242` AND RULED…"*

and `test_retry_seam.py:8652`: *"`_txn.py:1242` does not, and cannot"*.

All five were TRUE when written and were falsified by `352db0e` **three commits later in the same
wave**. The lead's own INDEX entry records catching this exact pattern on scout
(`171→176, 571→576→578, 599→608→610` — I verified that chain is **correct**) and **missed the
`_txn.py` instance sitting in the same wave.** `e81a3ff`'s message even states *"5 [sites] closed by
`352db0e`, which is where `label=`/`url=` actually landed"* — the shift was known and the citations
were not re-derived.

### D2d — HOW IT GOT PAST EVERY GRADER (found only in the overlap pass, and it is the worst part)

The overlap check makes D2b/D2c **worse**, not better. The chain is fully documented in the wave's
own archive:

1. `REPORT-adversary-151b.md:226-230` measured `:1002/:1010/:1018/:1103/:1242` **CORRECTLY**,
   against the pre-fix tree. Good work.
2. `352db0e` (THE FIX) then added +34 lines above them, moving all five.
3. `REPORT-contract-151c.md:120` **pinned the now-wrong number into the contract's own expected
   failure text** — `store/_txn.py:1242 in execute_transaction._attempt()` — and reported it as
   the "RED reason at HEAD (checked against the failure message, not just redness)".
4. `98980bd`'s builder wrote, in `REPORT-builder-151b.md:100-108`:
   > *"My first draft was six [lines] and shifted every line below it by one, breaking five live
   > citations into this file (`_txn.py:876`, `:950`, `:1021`, `:1092`, `:1242`). **Verified
   > line-stable:** … `LINE-STABLE BELOW THE CLAUSE: True # old[861:] == new[861:], byte-for-byte`"*

   **That verification is correct and it answers the wrong question.** The builder proved *"my edit
   did not break these citations."* Nobody asked *"were they already broken?"* — and two of the five
   it named (`:1021`, `:1092`) plus `:1242` were **already stale**, falsified three commits earlier
   by the wave's own fix. A careful line-stability proof, run over an already-false list, reads as
   diligence and certifies nothing.
5. The number then shipped into **production** at `_txn.py:884`.

This is the wave's own lesson at one finer grain, and it is worth more than the fix: **a
verification whose scope is "did *I* break it" cannot see "was it already broken", and it looks
identical in a report.**

### (WITHDRAWN) the render.py repoint — I was wrong; it was properly adjudicated.

I initially flagged `render.py:2` and `sanitise.py:46` as an incomplete repoint (they still cite the
dangling `REPORT-phase0-audit-1.md` while `render.py:16`, 14 lines below, was repointed). **The
overlap pass refutes me**: `REPORT-adj-152-rep-prod.md` rows 16 and 18 give each of those two sites
its own individual verdict of **PROVENANCE**, deliberately left alone. The per-site discipline
worked exactly as designed. Withdrawn.

Likewise the *"§PROBE-A environment facts"* wording: the cited design doc has no §PROBE-A *heading*,
but it does carry an "Environment facts (CORRECTED v2)" block attributed to `audit §PROBE-A`, and
`REPORT-apply-152-prod.md:50` shows the applier checked exactly that. The phrasing is compressed,
not false. **Note only, not a defect.**

---

## 4. TARGET 4 — THE REPO LAW CHANGE. **SOUND but INCOMPLETE.**

The `968883d` text itself is coherent and does not contradict anything else in CLAUDE.md
(the surviving "Reports: `REPORT-<agent-name>.md` at repo root, EXACT name" bullet is compatible —
the new bullet governs disposal only). **Nothing in the repo mechanically DELETES reports**: I swept
`*.sh`, `*.py`, `*.toml`, Containerfile/Dockerfile/ignore files and `skills/` — the only automation
touching `REPORT-*` is `.claude/hooks/teammate-idle-gate.sh`, which only checks for *presence*. Good.

But:

- **D3 — `loremaster/tests/test_retry_seam.py:5205-5209` still teaches the RETIRED law**, in a live
  test file, at HEAD: *"Cite those, never the review reports of that wave — they are untracked
  scratch files at the repo root that **repo law requires be DELETED before any image build**."*
  `968883d`'s own commit message says: *"A second instance in `test_retry_seam.py` is queued behind
  the agent that owns it."* **Four commits followed and it was never applied**, and it is not in
  #157's remainder. This is a self-declared obligation that was dropped, not deferred — CLAUDE.md's
  "don't kick the can" rule requires a named decision point and there is none. It is also now
  doubly wrong: the reports of that wave WERE archived by `7d2ff44` and DO resolve.
- **`docs/orchestration/receipts/2026-07-19-comms/README.md:4`** states the retired rule in the
  present tense as the reason those files exist. Lower stakes (a receipts README), but it is a live
  doc, not an archived report, and it is outside the `docs/plans/v2/receipts/` carve-out the commit
  message named.
- **D4 — `~/.claude/orchestration/brief-base.md` was NOT updated.** Finding #153 explicitly says
  *"Both `brief-base.md` §1 and the repo CLAUDE.md would need the step; brief-base is versioned, so
  this is a v6."* Only CLAUDE.md changed. brief-base v5 §1 still mandates the repo root with no
  archival step, so **every future spawned agent is still briefed under the root-cause protocol.**
  Outside the repo and outside my writable set — flagged, not fixed.
- Repo root is clear of TRACKED `REPORT-*.md` (0), and 20 reports are correctly archived under
  `docs/plans/v2/receipts/2026-07-21-151-152/`. **But `REPORT-apply-152-tests-d.md` is sitting
  UNTRACKED at the repo root right now** — the wave's 21st report, unarchived. It is cited nowhere,
  so nothing dangles today, but it is exactly the unrecoverable address the new law forbids, left
  behind by the wave that wrote the law.

---

## 5. TARGETS 3, 5, 6, 7

### Target 3 — the past-tense commit markers. **HONEST: 72/72 CORRECT.** This is the wave's best work.

Delegated, exhaustively (not spot-checked), with two independent regexes agreeing on the population
before any verdict, and a mandatory positive control. Report: `/tmp/subaudit-markers.md`.

- **71** added lines under `loremaster/` carry a SHA citation; **72** occurrences; **19** distinct SHAs.
- **19/19** are real commits (`git cat-file -t`) and **19/19** are ancestors of HEAD.
- **72/72** name the commit that genuinely effected the claimed change, verified per site by
  `git log -S'<production symbol>' -- <prod file>` plus reading the diffs of
  `352db0e / 98980bd / 4afdbf4 / 297194e / 9171021 / 001f632 / 333ba50`.
- The highest-risk group — four sibling graph commits with near-identical "module-prefix arm" /
  "bare-name bridge" claims — **separates correctly**: `tests_for`'s bridge → `9171021`,
  `references`/`blast_radius` → `297194e`.
- **0** SHA citations were added to production code.
- **POSITIVE CONTROL**: three deliberately-false attributions pushed through the same instrument
  ("`_safe_kill`'s label landed at `352db0e`", "`bootstrap_session`'s `url` landed at `98980bd`",
  "`tests_for`'s prefix arm landed at `297194e`") **all returned MISMATCH**, and the instrument
  named the true commit each time. It discriminates.

`db9973b`'s claim that thirteen distinct closing commits were each derived by `git log -S`/`git blame`
rather than assumed **holds up**.

Three secondary observations from that pass, none a mis-attribution:

- **OBS-1 (5 sites, LOW):** `test_retry_seam.py:4087, :4434, :6769, :6817, :7010` name the right SHA
  but their *why*-clause asserts a prior behaviour that never existed at `9d29111^`. E.g. `:6817`
  says the exhaustion record *"carried `attempts` and `elapsed_seconds` and nothing else"* ×10 — at
  `9d29111^` there was no record at all, because `_query` had no retry branch. They were RED against
  an intermediate, never-committed build. Same defect class as D1, one grain finer.
- **OBS-4:** the two `7d2ff44` archive blocks disagree with each other — one names
  `REPORT-audit-150-cold.md` exactly (correct), the other keeps the glob `REPORT-audit-150*.md`
  while the surrounding prose claims "section-exactly".
- **OBS-5:** the wave added bare `REPORT-*.md` citations (`test_retry_seam.py:7147, :7537, :8221, :8722`),
  a form `CLAUDE.md` now forbids. **I verified they do not dangle** — all name files tracked under
  `docs/plans/v2/receipts/2026-07-21-151-152/` — and I separately confirmed the wave created
  **no net-new dangling citations**: the counts for every dangling name in `loremaster/` are
  unchanged or lower across `3222e84 → HEAD` (`REPORT-fix-audit.md` 3→3, `REPORT-pkt02-contract.md`
  5→5, `REPORT-pkt02-adversary.md` 1→1, `REPORT-c1-contract-ledgers.md` 10→9). The `+` lines were
  reflows. **Form violation only, not a new dangle.**

### Target 5 — the repointed citations. **ALL RESOLVE.**

Every new address followed and confirmed to exist AND carry the claim:

| new address | exists | carries the claim |
|---|---|---|
| `docs/reference/surrealdb-31-capabilities.md` §7 | ✓ (line 606 "## 7. SYNTAX GOTCHAS") | ✓ (`type::record` RELATE parse-error, lines 308/614) |
| `TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set` | ✓ (:6565/:6568) | ✓ |
| `TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType` | ✓ (:6936) | ✓ |
| `TestScoutsConnectFailureReachesTheReconnectLadder` | ✓ (:6236) | ✓ |
| `scripts/search_score_survey.py` | ✓ | ✓ |
| `JsonFormatter` in `loremaster/logging_setup.py` | ✓ (:178) | ✓ |
| `scripts/survey_txn_contention_102.py` + *"p50 of TWO attempts per mint at every N ≥ 8"* | ✓ | ✓ **and the number is right** — `_txn.py:461-464` carries the survey's own table: N=8/16/32 all `attempts p50=2`; N=2 is p50=1. "cited above" is true (`_txn.py:453-455`). This repoint is a genuine improvement: a regenerating script replaced a dangling report. |
| `test_comms_tool.py::TestFleetLimitBounds::test_a_rejected_limit_never_touches_the_callers_row` | ✓ (:2358/:2385) | **RED for the ruled reason** — `ModuleNotFoundError: No module named 'loremaster.messages'`, the pre-existing packet-03 committed contract. **Not this wave's.** ⚠ Residual: production prose now says "pinned by X" where X cannot execute until packet 03 lands. |

16 distinct dangling `REPORT-*.md` names remain in production. That is **deliberate and ledgered**
under #157 (adjudicated PROVENANCE) — not a defect.

### Target 6 — no logic changed under cover of prose. **CONFIRMED CLEAN.**

Delegated and independently instrumented (AST-with-docstrings-stripped **plus** an independent
`tokenize`-stream comparison), with controls proven in both directions:
- Positive control `352db0e`/`_txn.py` → DIFFERENT, naming `kwonlyargs=[arg(arg='url')]` on
  `bootstrap_session` plus the three new label constants.
- Reach control: all six non-prose commits read DIFFERENT on the same files the prose commits touch.
- Negative control `352c232` → EQUAL.

Result: **34/34 file-commit pairs structurally EQUAL**; cumulative `d2d7b2c~1..HEAD`, 23 files
touched only by prose commits, **23/23 EQUAL end-to-end**. The only non-docstring string change in
the whole set is the `msg` operand of two `assert`s in `e81a3ff` (`scout.py:571` →
`scout.py::_consume_live`) — assertion *conditions* untouched. `9601455`'s production edits are
comment-only; the served MCP surface is byte-identical (tool descriptions come from
`spec.description` constants, never from harvested docstrings). `db9973b`'s non-prose half is
confined to three `.md` SUPERSEDED banners.

Full report: `/tmp/subaudit-proseonly.md`.

**One new finding from that pass:** `db9973b`'s commit message says *"all **12** touched test files"*;
the derived count is **10**. A wrong numeric claim inside the commit retiring wrong claims.

### Target 7 — are the filed findings HONEST? **YES — every number I could re-derive is EXACT.**

| finding | claim | re-derived | verdict |
|---|---|---|---|
| #152 | 61 sites in 13 files (`blindreader\|audit-102\|audit-fix-1\|adversary` in prod) | `3222e84`: **61 sites, 13 files** | **EXACT** |
| #152 | test tree carries 139 sites | `3222e84`: **139** | **EXACT** |
| #153 | 57 distinct REPORT names cited, **3** resolve, **54** dangle | `3222e84`: **57 / 3 / 54** | **EXACT** |
| #157 | 60 names, **9** resolve, **51** dangle at `b3e7687` | `b3e7687`: **60 / 9 / 51** | **EXACT** |
| #157 | 116 line-number citations in tests | `b3e7687`: **116** occurrences (73 distinct) | **EXACT** |
| #157 | archives: 8 (`7d2ff44`) / 17 (`1666856`) / 20 (`b3e7687`) | **8 / 17 / 20 files changed** | **EXACT** |
| #157 | "26 remaining RED claims" | bare grep gives **31** at `b3e7687`; 24 retired, **7** survive | **UNDERCOUNT by 5** — see D1 |
| #156 | `scout.py:568-569` = raise site, `:577` = the log call | verified at `352db0e` (the tree the evidence described): **568-569** = `raise … from error`; **577** = `logger.debug("command_subscriber.live_unavailable", exc_info=True)` | **EXACT** |
| #156 | `_txn.py:920` = the bare raise | at `352db0e~1`/`d2d7b2c`: **920** = `raise TxnContentionExhaustedError(` | **EXACT for the tree it describes** (stale at HEAD) |
| #156 | `__cause__` is None on the swallowed path | **measured by me**: `TxnContentionExhaustedError, __cause__=None` | **CONFIRMED** |
| #151 | `:1021-1023`, `:857-859`, `:789-801`, `:876-880`, `:920`, `:929` | all verified against `352db0e~1` | **EXACT** |
| #155 | states an UNVERIFIED obligation and says so explicitly | reads honestly; scopes its own limits | **HONEST** |
| INDEX `01e7885` | "eleven owners thread their OWN url" | **11** prod call sites, all with `url=` | **EXACT** |

The findings are the strongest artifact of this wave. **#157's "already done" claims all check out.**
Its one flaw is the 26-vs-31 undercount, which is why D1 is not in its remainder.

**Observation, not a defect:** the test tree's `blindreader|audit-102|audit-fix-1|adversary` site
count went **139 → 157** across the wave (+18). Production went 61 → 54. The wave added 18 new
agent-name citations to the test tree while closing the class. They are almost certainly legitimate
provenance-with-substance-inline (`adversary MP4`, `adversary-151b R1`), but the number is moving in
the wrong direction and nobody counted it.

---

## 6. TARGET 8 — THE GATES. Re-run by me, not trusted from any report.

| gate | claimed | **measured by me** |
|---|---|---|
| `tests/test_surreal_harness.py tests/test_retry_seam.py` | 531 / 0 | **531 passed, 0 failed** (25.87s) ✓ |
| `uv run ruff check .` (absolute cd, re-run twice) | clean, exit 0 | **All checks passed! exit 0** ✓ |
| `./scripts/typecheck.sh` | exit 1, exactly 55 in 5 files | **Found 55 errors in 5 files (checked 146 source files), exit 1** ✓ |
| `test_retired_symbols.py` + `test_txn_contention.py` | — | **38 passed** ✓ |
| structural/AST pins: `test_render_seam_pins` `test_text_hygiene` `test_shellout_allowlist` `test_shellout_seam_perimeter` `test_render_mypy_layer` | — | **168 passed** ✓ |
| full suite (`-n auto`) | 5722 passed, packet-03 RED unmoved at 309/166 | *see §6a* |

**Sweep for gates nobody ran** (the brief's "assume there is another one"): I enumerated every test
that scans the tree rather than importing it —
`test_render_seam_pins`, `test_retired_symbols`, `test_retry_seam`, `test_search`,
`test_surreal_harness`, `test_surreal_store`, `test_text_hygiene` — plus the two shellout perimeter
gates. `test_retired_symbols` scans `docs/**` for `.py` and `.md`, which is exactly why `1666856`
broke it for 13 commits. The wave's three archive commits added **45 tracked files** under `docs/`,
all now in that gate's scan scope. **All of them pass at HEAD.** I found no second broken gate.

⚠ **A trap I hit and you should know about**: my first structural-pin run printed a pytest usage
error (`unrecognized arguments: --timeout=600`) and the shell reported **exit 0**, because the error
was behind a pipe. That is the "piped test run lies by omission" failure mode, live. Every number
above is from a run with a passed-COUNT in the tail.

### 6a. Full-suite result

*(appended below when the run completes — see §6a-RESULT)*

---

## RESIDUALS — read these, not just the verdict

1. **`execute_transaction` delivers 2 of #151's 3 facts.** Measured: `store.transaction.rolled_back`
   carries the failing statement index and the full engine result but **no `url`** and no `label`;
   the co-emitted `store.retry.exhausted` on that path carries only `{attempts, elapsed_seconds}`.
   An operator learns WHICH statement and WHAT the engine said, but not WHICH SERVER. The allowlist
   evidence says "strictly more detail than a label" — true as written, but it is *not* strictly more
   than `label` + `url`, and #151's own promise is a triple. Not a defect; a bound worth naming.
2. **Production prose now cites a committed-RED test.** `server.py` says "pinned by
   `TestFleetLimitBounds::test_a_rejected_limit_never_touches_the_callers_row`", which cannot
   execute until packet 03 lands (`ModuleNotFoundError: loremaster.messages`). The address resolves;
   the pin is inert. Cause verified as the pre-existing ruled contract, not this wave.
3. **`REPORT-apply-152-tests-d.md` is untracked at the repo root.** Uncited today. Archive it with
   the other 20 (`git mv` into `docs/plans/v2/receipts/2026-07-21-151-152/`) before anything cites it.
4. **`test_retry_seam.py:2691`** uses `"store/_txn.py:1092 in _attempt()"` as fixture data;
   `_txn.py:1092` is a docstring line and `_attempt` is at 1140. Decorative fixture text, no
   behaviour — but it reads like a real address and will confuse the next reader.
5. **`test_retry_seam.py:8246`** cites `_txn.py:857-859` while quoting the OLD docstring text that
   `352db0e` replaced at exactly those lines; `test_retry_seam.py:7309` cites `_txn.py:1021-1023`
   for the pre-fix bootstrap calls (now 1057/1063/1069); `test_txn_contention.py:489` cites
   `_txn.py:851` for a raise message that lives at 930. All three are historical statements whose
   addresses now point elsewhere — lower severity than D2b/D2c because the surrounding prose is
   explicitly past-tense, but they are the same class and they are in the **116** #157 ledgered.
6. **#151, #152, #153, #155, #156, #157 are all still `open` in the ledger** while
   `docs/plans/v2/INDEX.md` (`01e7885`) declares "**#151 + #152 CLOSED**". If the intent is to
   resolve at deploy, fine; as it stands the ledger and the plan disagree.
7. **The wave added 18 agent-name citations to the test tree** (139 → 157) while retiring 7 from
   production (61 → 54). Uncounted by anyone.
8. **#156's own scope caveat is unaudited by anyone**: it explicitly says the generalisation to the
   exec/shellout and SDK-call allowlists is NOT checked. Given that this audit confirmed the retry
   allowlist's evidence only by *running* it, those two allowlists' evidence strings remain
   unmeasured claims about runtime behaviour. That is a real open flank, honestly declared.
9. **One post-ban bare `REPORT-*.md` citation.** `968883d` banned bare report names; three
   citations were added after it. Two are fine — `_surreal_harness.py:50-51` names the directory
   path `docs/plans/v2/receipts/2026-07-20-150/` alongside the filenames, which is a valid archived
   address. One (`REPORT-contract-151b.md`, in `test_retry_seam.py`) is genuinely bare. It resolves
   (the file is tracked), so nothing dangles; form violation only, three commits after writing the
   rule.
10. **`REPORT-audit-150*.md` glob** (sub-auditor OBS-4): one of the two `7d2ff44` anchor blocks
   names the file exactly, the other keeps a glob while the surrounding prose claims
   "section-exactly". The two archived audit reports define a *different* R4 and R5, so the glob
   is genuinely ambiguous — that is exactly why `e81a3ff` disambiguated the other one.
11. **⚠ MY OWN INSTRUMENT ERROR, disclosed:** I briefly ran two full suites CONCURRENTLY against
   the same `spike-surreal` test store. Both degraded (339/407 and 364/411 vs the solo run's
   309/166). I do not know whether that is DB contention or simply ~124 xdist workers on a 64-core
   box, and I did not resolve it — but CLAUDE.md asserts the harness is parallel-safe *by
   construction* (`unique_database()` mints `test_<pid>_<uuid4>` so "a concurrent pytest process on
   the SAME server never collides"). **That invariant is asserted for concurrent *processes*, and
   my accidental experiment is weak evidence against it.** Worth a deliberate 2×-suite probe by
   someone with the budget; do not act on my confounded numbers.

---

## OVERLAP CHECK

**Order followed as briefed**: every finding above was formed from the diffs, the tree and my own
probes. Only afterwards did I open `docs/plans/v2/receipts/2026-07-21-151-152/` (20 reports) and
grep it for each of my findings. Results:

| my finding | already known to the wave? |
|---|---|
| D1 (six surviving false RED claims) | **NO.** No archived report mentions `7528`/`8651`/"does not yet accept"/"RED TODAY" as survivors. `db9973b` believed 2 remained; 7 do. **NEW.** |
| D2a (`CLAUDE.md` "15") | **PARTIALLY.** The "15" traces to `REPORT-adj-152-tests.md:11`'s *"would resolve 17 sites"* — nobody re-derived it. Independently corroborated by my second sub-auditor (OBS-3, a bare grep giving 16). Now fixed by the lead. |
| D2b (`_txn.py:884` `:1242` in production) | **NO — and worse.** `REPORT-adversary-151b.md` measured `:1242` correctly *pre-fix*; `REPORT-contract-151c.md:120` then pinned the stale number into the contract's expected text *post-fix*; `REPORT-builder-151b.md:104` proved "line-stable" over an already-false list. **Three graders touched it and none re-derived it.** NEW. |
| D2c (5 stale cites in `test_retry_seam.py`) | **NO.** Same chain. |
| D2d / `render.py` repoint | **YES — and I was WRONG.** `REPORT-adj-152-rep-prod.md` rows 16/18 give `render.py:2` and `sanitise.py:46` individual PROVENANCE verdicts. **Withdrawn.** |
| D3 (`test_retry_seam.py:5208` teaches retired law) | **KNOWN AND DROPPED.** `968883d`'s commit message says *"A second instance in `test_retry_seam.py` is queued behind the agent that owns it."* Four commits followed; never applied; not in #157. |
| D4 (`brief-base.md` not updated) | **KNOWN.** #153 names it explicitly as a required v6. Not done, and not tracked in #157's next-action list. |
| `db9973b` "12 touched test files" (actual 10) | **NO.** NEW. |
| `REPORT-apply-152-tests-d.md` unarchived at root | **NO.** NEW. |
| Test-tree agent-name citations 139 → 157 | **NO.** NEW (observation). |

**Reading the archive changed one verdict (D2d withdrawn) and strengthened two (D2b/D2c).** The
adjudication reports are genuinely good: per-site tables, individual verdicts, no wholesale
classification. The failure is not in the adjudication — it is that **nothing in the pipeline
re-derived a number or a line after the fix that invalidated it.**

---

## APPENDIX — instruments used

- `/tmp/coldaudit/probe_151.py` — bootstrap exhaustion, 3 legs + pre-fix control.
- `/tmp/coldaudit/probe_scout_txn.py` — scout ×3 + `execute_transaction` evidence + disabled-mechanism control.
- `/tmp/coldaudit/derive.sh`, `derive153.sh`, `sites.sh`, `sites_all.sh` — citation/name counts per rev.
- `/tmp/cite_check.py` — resolves every `file.py:NNN` citation in prod + tests and prints the cited line.
- Mutation backups: `/tmp/coldaudit/backup-3556869/`, `/tmp/coldaudit/bk2/` (both restored, md5-verified).
- Delegated: `/tmp/subaudit-proseonly.md` (AST/token prose-only proof), `/tmp/subaudit-markers.md` (commit-marker derivation).
