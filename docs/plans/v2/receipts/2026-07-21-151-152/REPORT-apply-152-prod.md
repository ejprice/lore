# REPORT-apply-152-prod

brief-base v5 read

- **state**: done-with-deviations
- **deviations**:
  - Declined the `finding #108` half of `REPORT-adj-152-txn.md`'s site-14 proposal — #108 is
    briefs.py's version-mint retry, NOT scout's unwrapped bootstrap. Citing it would be the exact
    un-derived citation this task removes. (§3, D-1)
  - Dropped the `:178` / `:192` LINE NUMBERS from `REPORT-adj-152-txn.md`'s site-20 proposal; cited
    module + symbol instead. A line number manufactures the next dangling address. (§3, D-2)
  - `render.py` repoint names the tracked path explicitly rather than "the ruling doc" — render.py's
    OWN spec path is dead (#154), so "the ruling doc" is ambiguous inside this module. (§3, D-3)
  - Three edits rewrapped their sentence to stay inside `line-length = 110`. Formatting consequence
    of the address swap, not a prose rewrite. (§2 rows 6, 8, 9)
- **decisions-needed**:
  - `TestFleetLimitBounds` (my `server.py` repoint target) is currently RED — blocked by the
    PRE-EXISTING packet-03 `loremaster.messages` contract, not by anything here. Cite anyway or
    wait? Both readings written. (§5, FLAG-1)
  - Three `scratchpad/` probes cited in MY files were archived at `1666856` and NOW RESOLVE at a
    tracked path — one-line repoints each, outside my named work order. Grant or defer? (§5, FLAG-2)
- **receipt pointers**: §1 what I verified before editing · §2 the 12-site ledger · §3 deviations
  from the adjudicators · §4 the 41 residual PROVENANCE sites, individually · §5 flags · §6 gates

**Headline**: 12 edits at 12 load-bearing sites across 7 production files. **AST-proven prose-only**
against `98980bd` (§6). Gates: **531/0** on the named suites, **1822 passed** across every touched
module's suite with the 237 failures ALL the pre-existing packet-03 contract, ruff clean, typecheck
55 errors and **zero in any file I touched**.

---

## 1. What I verified before editing (not inherited)

**The `_txn.py` sites were STALE, exactly as the brief warned.** Re-derived against the current
tree: the adjudicator's `:904` is now `:914`, its `:954` is now `:977`, its `:1064` is now `:1113`.
Applying the report's line numbers would have edited the wrong lines. Every edit below was anchored
on QUOTED TEXT, never a line number.

**Every repoint target was opened and confirmed to carry the claim.** A repoint at an address that
does not support the claim is worse than a dangling one:

| target | carries the claim? |
|---|---|
| `test_retry_seam.py::TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType` | **YES, both halves.** Asserts `connection.closes >= 1` (the socket-leak claim) AND `not isinstance(exc_info.value, SurrealConnectionError)` with a failure message naming `W1-SCOUTKILL` verbatim. Its own block comment says the two halves are pinned in ONE test on purpose. |
| `test_retry_seam.py::TestScoutsConnectFailureReachesTheReconnectLadder` | **YES.** Drives the REAL `CommandSubscriber.run()` with the REAL `_open_command_connection`; oracle is that the gap command is eventually dispatched after a backoff + reconnect. |
| `TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set` | **YES — it is the authority for the count FOUR.** `_GUARDED_CAS_DOORS` holds exactly four entries and the test asserts `found.keys() == _GUARDED_CAS_DOORS.keys()` as an EXACT SET. |
| `test_comms_tool.py::TestFleetLimitBounds::test_a_rejected_limit_never_touches_the_callers_row` | **YES.** Docstring opens "Contract-adversary §2"; asserts the rejected call neither flips `status` nor stamps `heartbeat_at`. ⚠ Currently RED — see FLAG-1. |
| `scripts/survey_txn_contention_102.py` | **YES, tracked**, and it does print a full JSON receipt (`print("=== FULL REPORT (json) ===")` at `:217-218`). |
| `docs/reference/surrealdb-31-capabilities.md` §7 | **YES.** §7 row: `RELATE endpoints | RELATE $from->edge->$to (bound RecordIDs) | RELATE type::record(..)->edge->type::record(..) — PARSE ERROR`. |
| `docs/design/2026-07-11-render-safety-foundation-ruling.md` | **YES, tracked.** Its v2 CHANGELOG (lines 3-9) records the LiteralString refutation and the working exploit; its "Environment facts (CORRECTED v2)" block carries `audit §PROBE-A, ls_matrix.py`. |
| `loremaster/logging_setup.py` | **YES.** `class JsonFormatter` at `:178`, `"logger": record.name` at `:192`. |
| `scripts/search_score_survey.py` | **YES, tracked** — and already cited in the same sentence. |

**The struck 30.2% figure — I checked the archive BEFORE striking, per the brief.** The
`1666856` archive under `docs/plans/v2/receipts/2026-07-20-probes/` does **not** rescue it. The
closest archived instrument, `102-recovery/probe_conflict_kind.py`, is a *different protocol*
(conflict-KIND introspection, `MAX_ROUNDS_PER_WORKER = 60`) — not the "16 racers × 40 rounds on ONE
hot row, raw SDK, 193/640" measurement. `grep -rn "193" docs/plans/v2/receipts/` returns nothing
related. The instrument is genuinely gone, so the operator's STRIKE ruling stands on verified
ground, not on the report's say-so.

**The inline-protocol EXCEPTION was honoured — both sites PRESERVED, untouched:**
`_txn.py:965` (`**6.2%–34.4%** … across three 160-connect runs` of `16-way concurrent` virgin
first-connects, "a RANGE, stated with its protocol, never a point estimate") and its sibling
`surreal.py:412`. These state their protocol inline, so they are reproducible without the absent
script. Neither is in my work order and neither was edited.

**`blindreader-150` citations: ZERO in production.** `git grep -nE "blindreader-150|audit-150" --
loremaster/loremaster/` returns nothing, so the `7d2ff44` archive changes nothing on the production
side and I had no now-resolving citation to leave alone.

---

## 2. The 12-site ledger

Line numbers are POST-EDIT. Verdict source: `T` = `REPORT-adj-152-txn.md`, `P` =
`REPORT-adj-152-prod.md`, `R` = `REPORT-adj-152-rep-prod.md`, `OP` = the operator ruling in my brief.

### `store/_txn.py` — 4 sites, all RE-DERIVED (the report's line numbers were stale)

**1 · `_txn.py:466`** — source `T §4` (LOAD-BEARING; the report's most explicit dangler).
```
- # (full JSON receipt in ``REPORT-builder-102.md``). ZERO exhaustions across all
+ # (regenerate the full JSON receipt with the survey script above). ZERO exhaustions across all
```
Target: `scripts/survey_txn_contention_102.py`, TRACKED, named 13 lines above at `:453` **with its
exact reproduce command at `:454-455`** — the durable address was already in the block; only the
pointer to the raw JSON dangled. A committed script that regenerates the measurement is the
strongest address available, per the brief.

**2 · `_txn.py:914-916`** (report said `:904`) — source `T §3` site 12 + **`OP` STRIKE ruling**.
```
- # is the NORMAL case — blindreader-dry-1's live probe (16 racers x 40 rounds on
- # ONE hot row, raw SDK): 193/640 attempts = 30.2% conflicted (a single
- # measurement at 16-way, not a general constant) — and a line per retried
- # attempt would be a log storm in production.
+ # is the NORMAL case — the committed survey (``scripts/survey_txn_contention_102.py``,
+ # cited above) measures a p50 of TWO attempts per mint at every N >= 8 — and a line
+ # per retried attempt would be a log storm in production.
```
**Which way I went and why:** STRUCK, not repointed. The instrument is gone and is not in the
`1666856` archive (§1). The number's only job in this comment is to justify "don't log every
retry", and the committed survey justifies that just as well **with an instrument anyone can
re-run**. The replacement claim is verified against the in-tree table at `_txn.py:461-464`:
`N=8 p50=2`, `N=16 p50=2`, `N=32 p50=2`. This is the same distinction the `search.py` site turns on,
applied in the opposite direction — there the instrument is committed, so the number stays (site 12).

**3 · `_txn.py:976-979`** (report said `:954`) — source `T §3` site 14, **minus its `#108` half**.
```
- anything. That is load-bearing (contract adversary P-1, ``W1-SCOUTKILL``): scout's
+ anything. That is load-bearing (``W1-SCOUTKILL`` — pinned by
+ ``TestScoutsConnectFailureReachesTheReconnectLadder`` and
+ ``TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType`` in
+ ``test_retry_seam.py``): scout's
```
`W1-SCOUTKILL` is KEPT — it is durable (it appears in `test_retry_seam.py` twice). Only
`contract adversary P-1` is dropped. Two pins because this docstring makes BOTH claims: the ladder
recovers (pin 1) and the raw type survives a failed bootstrap (pin 2). Both verified GREEN (§6).
See D-1 for why `finding #108` was declined.

**4 · `_txn.py:1113`** (report said `:1064`) — source `T §3` site 20.
```
- in that seam's file) — blindreader-dry-2 F6: ``JsonFormatter`` writes
+ in that seam's file) — ``JsonFormatter`` in ``loremaster/logging_setup.py`` writes
```
Target verified: `class JsonFormatter` (`logging_setup.py:178`) and `"logger": record.name` (`:192`).
Line numbers deliberately NOT written into the prose — see D-2.

### `scout.py` — 2 sites

**5 · `scout.py:207-208`** (report said `:199`) — source `P` LB-1.
```
- Deliberately UNWRAPPED (adversary P-1, ``W1-SCOUTKILL``): unlike the ten
+ Deliberately UNWRAPPED (``W1-SCOUTKILL`` — pinned by ``test_retry_seam.py``'s
+ ``TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType``): unlike the ten
```

**6 · `scout.py:218-221`** (report said `:210`) — source `P` LB-2. ⚠ *sentence rewrapped*.
```
- It DOES self-heal the half-open socket on a failed bootstrap
- (blindreader-dry-2 F7 / audit-fix-1 B1): every one of the ten ledger seams
+ It DOES self-heal the half-open socket on a failed bootstrap (pinned by
+ ``test_retry_seam.py``'s
+ ``TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType``): every one
+ of the ten ledger seams  …[remainder of the sentence rewrapped, no words changed]
```
**No finding number invented.** The adjudicator refused to cite `#120` here because it could not
substantiate that #120 covers the socket leak; I honoured that refusal rather than quietly closing
the gap with a plausible number.

### The rest

**7 · `store/surreal.py:425-429`** — source `P` LB-3. Same claim as site 5, stated store-side;
same address. ⚠ *sentence rewrapped*.
```
- (adversary P-1, ``W1-SCOUTKILL``): scout's reconnect ladder needs the
+ (``W1-SCOUTKILL`` — pinned by ``test_retry_seam.py``'s
+ ``TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType``):
+ scout's reconnect ladder needs the …
```

**8 · `server.py:4449-4452`** — source `P` LB-4. ⚠ *comment rewrapped to 110 cols*.
```
- # (contract-adversary §2). Below 1 teaches the valid range; above the
+ # (pinned by ``test_comms_tool.py::TestFleetLimitBounds::
+ # test_a_rejected_limit_never_touches_the_callers_row``). Below 1 teaches …
```
Note the block ALREADY opens with `# v7 / finding #97:` five lines above, so this comment now
carries a durable finding number AND an executable pin. See FLAG-1 for the pin's current RED state.

**9 · `briefs.py:940-945`** — source `P` LB-5, **the hyphen-wrapped site no line-oriented grep can
see** (`audit-` ended one line, `fix-1 A6` started the next). ⚠ *comment rewrapped*.
```
- # …in the package (audit-
- # fix-1 A6: a hand-list here once named only two and quietly dropped a
+ # …in the package (an EXACT-SET
+ # pin — ``test_retry_seam.py::TestNoGuardedCasHandlerReinterpretsExhaustedContention
+ # ::test_the_door_enumeration_matches_the_canonical_set``: a hand-list here once
```
The repoint makes the count **FOUR** checkable against the pin that enforces it as an exact set.
**Verified closed as a class:** the hyphen-wrap sweep
`git grep -nE "(audit|blindreader|adversary|REPORT|builder|contract|probe|slate|phase|cold)-$" --
'loremaster/loremaster/*.py'` now returns **NONE** (it returned exactly this one site before).

**10 · `briefs.py:900-901`** — source `R` R1.
```
- Live 3.1.5 gotcha (verified this session, see
- ``REPORT-c1-contract-schema.md``): ``RELATE type::record(...)->edge->
+ Live 3.1.5 gotcha (see ``docs/reference/surrealdb-31-capabilities.md``
+ §7): ``RELATE type::record(...)->edge->
```
"verified this session" also dropped — a temporal reference with no session left to name. The
store reference is the CLAUDE.md-mandated home for probed engine facts.

**11 · `render.py:16-17`** — source `R` R5. See D-3 for the wording deviation.
```
- audit (REPORT-phase0-audit-1.md §PROBE-A) refuted that with a working exploit
+ audit (docs/design/2026-07-11-render-safety-foundation-ruling.md, its v2
+ CHANGELOG and §PROBE-A environment facts) refuted that with a working exploit
```
The ruling doc's CHANGELOG cites `REPORT-phase0-audit-1.md` itself, so the provenance survives at a
tracked address rather than being erased.

**12 · `search.py:574`** — source `R` R6. **Strike the dangling half, keep the number.**
```
- # (scripts/search_score_survey.py run, 2026-07-06, REPORT-slate-fixer-
- # survey.md / search_score_survey_summary.md): 9/15 nonsense queries
+ # (scripts/search_score_survey.py run, 2026-07-06): 9/15 nonsense queries
```
**Which way I went and why:** the 9/15 and 40% figures STAY. Unlike `_txn.py`'s 30.2%, this
instrument is **present and committed** — the figure is re-derivable, not inherited, so the "a
figure you didn't measure is a rumor" rule does not bite. That is the distinction the operator's
precedent turns on, applied deliberately in the opposite direction from site 2.
⚠ This site was also invisible to any `.md`-anchored grep (`REPORT-slate-fixer-` wrapped mid-name).

---

## 3. Deviations from the adjudicators' proposals

**D-1 · Declined `finding #108` at `_txn.py:977`** (`REPORT-adj-152-txn.md` §3 site 14 proposed
`(finding #108; pinned by …)`). I read #108 before citing it: it is *"briefs.py's version-mint
retry is control-flow COUPLED TO AN ERROR-MESSAGE STRING and its jitter is fixed-per-call over 4
slots"* — briefs.py's mint, resolved at `9d29111`. It says **nothing** about scout's unwrapped
bootstrap or the W1-SCOUTKILL counterfactual. Citing it would manufacture false confidence, which is
strictly worse than the dangler I am removing — and it is the same discipline `REPORT-adj-152-prod.md`
applied when it refused to cite `#120` for the socket leak. **The test pins alone carry the claim.**

**D-2 · Dropped the `:178` / `:192` line numbers** (`T` §3 site 20 proposed
`` ``JsonFormatter`` (``loremaster/logging_setup.py:178``) … (``:192``) ``). I verified both line
numbers are correct TODAY — and did not write them, because a line number in prose is an address
that drifts on the next edit to `logging_setup.py`. That would manufacture the next #152. Module +
symbol is stable, is what `go-to-definition` resolves, and is what every other pin in these files
uses. The verified line numbers live here, in the report, where staleness is harmless.

**D-3 · `render.py` names the path, not "the ruling doc"** (`R` R5 proposed
`(the ruling doc's v2 CHANGELOG, §PROBE-A)`). Inside `render.py` the phrase "the ruling doc" is
ambiguous: the module's own `Spec:` line at `:4` names `docs/plans/v2/PKT-28-agent-comms.md`, which
is **DEAD** (finding #154, explicitly not mine). A relative reference resolving to a dead path is no
improvement, so I wrote the tracked path explicitly.

---

## 4. The 41 residual sites in my 7 files — individually, per repo law

"All remaining hits are provenance" is banned output. Every residual hit under the bare sweep
`git grep -nE "blindreader|audit-102|audit-fix-1|adversary|REPORT-"` over my seven writable files,
with the report that ruled it and its verdict. **All 41 are PROVENANCE = LEAVE.** I edited none of
them; the ~87% leave-it ratio is intact.

| file:line | ruled by | verdict |
|---|---|---|
| `briefs.py:24` | `R` row 2 | PROVENANCE |
| `briefs.py:82` | `R` row 3 | PROVENANCE |
| `briefs.py:417` | `P` row 4 | PROVENANCE (points at a live symbol docstring) |
| `briefs.py:423` | `P` row 5 | PROVENANCE (reason stated in full inline) |
| `briefs.py:510` | `P` row 6 | PROVENANCE (carries `#120`/`#108` in the same parenthetical) |
| `briefs.py:935` | `P` row 7 | PROVENANCE |
| `briefs.py:1015` | `R` row 5 | PROVENANCE |
| `render.py:2` | `R` row 16 | PROVENANCE |
| `scout.py:189` | `P` row 27 | PROVENANCE (claim re-derived TRUE by `P` D-2) |
| `search.py:603` | `R` row 20 | PROVENANCE (tracked `client-needs-consult §S3` co-cited) |
| `search.py:744` | `R` row 21 | PROVENANCE |
| `server.py:1341` | `R` row 22 | PROVENANCE (instrument `loresigil.tokens.VoyageTokenCounter` is in-tree) |
| `server.py:2394` | `R` row 23 | PROVENANCE |
| `server.py:3998` | `R` row 24 | PROVENANCE (finding `#60` named inline) |
| `server.py:4403` | `R` row 25 | PROVENANCE |
| `server.py:4534` | `R` row 26 | PROVENANCE |
| `server.py:7835` | `R` row 27 | PROVENANCE (the gate's result is re-checkable against the tree) |
| `store/_txn.py:5` | `T` row 1 | PROVENANCE |
| `store/_txn.py:71` | `T` row 2 | PROVENANCE |
| `store/_txn.py:414` | `T` row 3 | PROVENANCE |
| `store/_txn.py:427` | `T` row 4 | PROVENANCE (cites a live test too) |
| `store/_txn.py:690` | `T` row 5 | PROVENANCE (`#93` durable, cited inline) |
| `store/_txn.py:716` | `T` row 6 | PROVENANCE ⚑ carries a second orphan (`design addendum Ruling 3`) |
| `store/_txn.py:845` | `T` row 7 | PROVENANCE (rule stated inline) |
| `store/_txn.py:856` | `T` row 8 | PROVENANCE |
| `store/_txn.py:878` | `T` row 9 | PROVENANCE (five-line comment states the whole rationale) |
| `store/_txn.py:899` | `T` row 10 | PROVENANCE |
| `store/_txn.py:908` | `T` row 11 | PROVENANCE (cites a live test too) |
| `store/_txn.py:953` | `T` row 13 | PROVENANCE |
| `store/_txn.py:990` | `T` row 16 | PROVENANCE |
| `store/_txn.py:997` | `T` row 17 | PROVENANCE |
| `store/_txn.py:1088` | `T` row 18 | PROVENANCE |
| `store/_txn.py:1095` | `T` row 19 | PROVENANCE ⚑ two readings admitted — `T` FLAG-3; I concur with A |
| `store/_txn.py:1135-1136` | `T` row 21 | PROVENANCE (one citation, two grep lines) |
| `store/_txn.py:1208` | `T` row 22 | PROVENANCE |
| `store/_txn.py:1225` | `T` row 23 | PROVENANCE |
| `store/_txn.py:1255` | `T` row 24 | PROVENANCE |
| `store/surreal.py:166` | `P` row 31 | PROVENANCE |
| `store/surreal.py:411` | `P` row 32 | PROVENANCE (the 6.2%–34.4% protocol-inline site — PRESERVED) |
| `store/surreal.py:568` | `P` row 34 | PROVENANCE |

⚑ `_txn.py:716` and `_txn.py:1095` each carry a SECOND dangling address beyond the swept token
(`design addendum Ruling 3`, and the `adversary R-3, latent` receipt). Both were ruled PROVENANCE
with substance inline; I flag them here rather than let the ⚑ disappear into a table.

---

## 5. Flags

**FLAG-1 · My `server.py` repoint target is currently RED — and it is NOT my doing.**
`test_comms_tool.py::TestFleetLimitBounds` fails 7/7 with
`ModuleNotFoundError: No module named 'loremaster.messages'` — the PRE-EXISTING packet-03
committed-RED contract the brief named. The test SOURCE carries the claim verbatim (§1); it simply
cannot execute until packet 03 lands the `messages` module. My three `test_retry_seam.py` pins are
all GREEN (§6). **Two readings:**
- **A (what I did):** cite it. The pin is committed, carries the claim, and goes live when packet 03
  ships. Meanwhile the comment block still opens with `finding #97` five lines above, whose
  resolution note states the very property — *"limit now validates, teaches, and clamps — **and
  mutates nothing on rejection**"* — so the reader is never without a resolvable address.
- **B:** wait for packet 03 and repoint then, leaving `(contract-adversary §2)` dangling until.
**I pick A.** A committed pin that is red for an unrelated in-flight contract is strictly better
than an address that will never resolve, and B kicks a two-minute edit into a future context.

**FLAG-2 · Three `scratchpad/` probes cited in MY files were ARCHIVED at `1666856` and NOW
RESOLVE — outside my work order, one line each.** The brief told me to check before striking; I
checked, and found the converse case. These are not strikes, they are cheap repoints I did **not**
make because they are not in my named site list and scope is the operator's:

| site | current citation | now tracked at |
|---|---|---|
| `store/_txn.py:516` | `scratchpad/probe_long_query_66b.py` | `docs/plans/v2/receipts/2026-07-20-probes/probe_long_query_66b.py` |
| `store/surreal.py:202` | `scratchpad/probe_long_query_66*.py` | same dir — ⚠ only `66b` was archived, so the GLOB would over-promise; I would write the exact filename |
| `store/surreal.py:289` | `scratchpad/probe_cosine_projection_s4b.py` | `docs/plans/v2/receipts/2026-07-20-probes/probe_cosine_projection_s4b.py` |

Not archived, still dangling, in my files: `render.py:17` (`scratchpad/audit1/row3_exploit.py` —
the ruling doc I now point at names the same path, so the provenance is at least co-located),
`_txn.py:412` (`scratchpad/contract-v5/capture_engine.py` — gone from disk entirely),
`search.py:235` / `search.py:248` (`scratchpad/survey_out_rerun/…`, `scratchpad/survey_out_74w/…`).
The two `search.py` ones back MEASURED numbers (`floor=0.5828`, false-fire `4.0%`, nonsense catch
`100.0%`) whose instrument `scripts/search_score_survey.py` **is committed** — so by site 12's
precedent the numbers stay and the dangling output paths add nothing checkable.
**Say the word and I will apply all of these; each is a one-line substitution.**

**FLAG-3 · An asymmetry I created deliberately, and the alternative edit.** The three sites that
state the same W1-SCOUTKILL claim now cite different numbers of pins: `_txn.py:977` cites **two**
(per `T`), `scout.py:207` and `surreal.py:425` cite **one** (per `P` and the brief's explicit
wording). Both readings produce different edits, so per scope law: **Reading A (applied)** — follow
each adjudicator's own verdict, which is what the brief named site-by-site. **Reading B** — cite
BOTH pins at all three, since all three prose blocks mention the reconnect ladder. **I would pick
B** on consistency grounds if the operator wants uniformity; it is three one-line additions. I did
not apply it because the brief was explicit about LB-1/LB-3, and a silent widening is the defect.

**FLAG-4 · Load-bearing sites the brief EXCLUDED from my writable set — still dangling.**
`REPORT-adj-152-rep-prod.md` §3 ruled three more LOAD-BEARING sites in
`store/surreal_schema.py` (R2 `:403` `string::matches`, R3 `:525` bug `#7061`, R4 `:652` the
migration matrix), all repointing at `docs/reference/surrealdb-31-capabilities.md`. That file is
**not in my writable set**, so #152 will look closed while three probed-engine-fact citations still
name deleted reports. Same for `R`'s FORK-1 at `symbols.py:556` (the only pointer to a deferred
design change, needing a finding filed first). Neither touched; both flagged.

**FLAG-5 · `render.py:4` is #154, untouched.** I edited `render.py:16`, twelve lines below the dead
`Spec: docs/plans/v2/PKT-28-agent-comms.md` binding path. Per the brief I did not fix it. Noting
that I was adjacent to it, since the brief asked me to flag if I touched nearby lines. Its verified
successor is `docs/design/2026-07-11-render-safety-foundation-ruling.md` — the same doc my site-11
repoint now names, so a reader landing on `:4` and failing will find the live address four lines
below at `:16`. That is luck, not design.

**FLAG-6 · No false claims found — and I checked rather than assumed.** The brief warned a
citation's claim may be FALSE (as #151's was). Every claim attached to a site I edited was verified
against the tree: the count FOUR (exact-set pin, four entries), the socket-leak and raw-type halves
(both asserted), the `JsonFormatter` field (`record.name`, confirmed), the `p50=2` replacement
(in-tree table), the RELATE parse-error gotcha (store reference §7), the LiteralString refutation
(ruling doc CHANGELOG). **Bounded claim:** this is a static consistency check plus the test runs in
§6 — I did not probe the engine, and the Mezmo half of the `_txn.py:1113` claim (external alerts
keyed on `logger:loremaster.tasks`) remains unverifiable from this repo. I deliberately invented no
address for it, exactly as the adjudicator declined to.

---

## 6. Gates — output tails WITH counts

**Prose-only proof (the strongest instrument here, run BEFORE the suites).** Parsed every touched
file at `98980bd` and at HEAD, stripped module/class/function docstrings from both ASTs, compared
`ast.dump`. Comments never enter an AST at all, so any surviving difference would be code:
```
OK    loremaster/loremaster/store/_txn.py
OK    loremaster/loremaster/scout.py
OK    loremaster/loremaster/store/surreal.py
OK    loremaster/loremaster/server.py
OK    loremaster/loremaster/briefs.py
OK    loremaster/loremaster/render.py
OK    loremaster/loremaster/search.py
VERDICT: PROSE-ONLY (all files AST-identical modulo docstrings)
EXIT=0
```
**No code, no logic, no signature, no constant changed.** (Script: `/tmp/apply152prod_astcheck.py`.)

**Gate 1 — the brief's named suites. Expected 531/0, got 531/0:**
```
cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest \
    tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly
EXIT=0
531 passed, 1 warning in 19.03s
```

**Gate 2 — every touched module's suite (`-n auto`, per repo law):**
```
uv run pytest tests/test_scout.py tests/test_surreal_store.py tests/test_txn_contention.py \
  tests/test_brief_ledger.py tests/test_comms_tool.py tests/test_comms_wiring.py \
  tests/test_comms_fleet_grouping.py tests/test_comms_render_architecture.py tests/test_render.py \
  tests/test_render_seam_pins.py tests/test_search.py tests/test_mcp_server.py -q -n auto -p no:randomly
EXIT=1
237 failed, 1822 passed, 3 xfailed in 106.11s
```
**All 237 failures are in `test_comms_tool.py` alone** (that file alone: `237 failed, 466 passed`);
the other eleven suites are 100% green. Failure reasons, counted rather than asserted:
```
104  ModuleNotFoundError: No module named 'loremaster.messages'
 63  AttributeError: type object 'AppContext' has no attribute '_render_comms_drain'
 42  AttributeError: … no attribute '_render_comms_send'
 21  AttributeError: … no attribute '_render_comms_ack'
  7  KeyError: 'send' / 'drain' / 'ack'  +  the actions-set assertion
```
That is the **pre-existing packet-03 committed-RED contract**, exactly as the brief predicted, and
**zero** of the 237 failure texts mention anything I edited (grep for `W1-SCOUTKILL |
survey_txn_contention | surrealdb-31-capabilities | render-safety-foundation | search_score_survey |
TestNoGuardedCasHandler | JsonFormatter` over the full output → **0 hits**).

**Every pin I cited, run directly:**
```
uv run pytest \
  "tests/test_comms_tool.py::TestFleetLimitBounds" \
  "tests/test_retry_seam.py::TestNoGuardedCasHandlerReinterpretsExhaustedContention" \
  "tests/test_retry_seam.py::TestScoutsFailedConnectClosesItsSocketWithoutChangingTheType" \
  "tests/test_retry_seam.py::TestScoutsConnectFailureReachesTheReconnectLadder" -q -p no:randomly
7 failed, 10 passed in 3.64s
```
The 10 passed are ALL three `test_retry_seam.py` pins. The 7 failed are ALL `TestFleetLimitBounds`,
every one `ModuleNotFoundError: No module named 'loremaster.messages'` — see FLAG-1.

**Gate 3 — ruff:**
```
cd /home/ejprice/PycharmProjects/lore && uv run ruff check .
RUFF EXIT=0
All checks passed!
```

**Gate 4 — typecheck (expected exit 1, exactly 55, zero in my files):**
```
./scripts/typecheck.sh
TYPECHECK EXIT=1
Found 55 errors in 5 files (checked 146 source files)
--- errors in files I touched ---   (grep over _txn|scout|surreal|server|briefs|render|search)
(none)
```
Exactly 55, all packet-03 comms, **zero in any file I touched**. The count did not grow.

**Residual sweeps:**
```
hyphen-wrapped citation class (was exactly 1 site):   NONE REMAIN
residual swept tokens in my 7 files:                  41  (all PROVENANCE — enumerated in §4)
inline-protocol number sites (must be preserved):     _txn.py:965, surreal.py:412  — both intact
blindreader-150 / audit-150 in production:            0 hits (nothing to leave alone)
```

---

## 7. Compliance

- **Writable set respected.** Seven production files, at the named load-bearing sites only, plus this
  report. No test file touched (`apply-152-tests-b` owns `test_retry_seam.py` and
  `_surreal_harness.py` — I only READ them). No `docs/`, no `pyproject.toml`, no `.claude/`.
- **No git state mutated** — no add, no stash, no commit, no worktree. I deliberately did NOT use
  `git stash` to build a test baseline (it mutates git state); the AST proof plus the failure-reason
  classification establish the same ground truth without it.
- **CWD trap:** it fired once on me — a `docs/plans/v2/receipts/` glob run after `cd …/loremaster`
  returned "No such file or directory". I caught it on the exit line and re-ran with an absolute
  path; every conclusion here comes from the absolute-path re-run.
- **Tool honesty:** grep, not lore, for the entire sweep, and I say so per base protocol §4. This is
  prose inside comments and docstrings — a **non-symbol textual seam** (dogfood case b) and an
  **exhaustiveness** question (case a). The code graph cannot own it. `lore_findings` WAS used as
  intended, for #152/#153/#154/#108/#97. No friction filed: lore behaved correctly and was simply
  the wrong instrument for prose, which is a documented bound, not a gap.
- **Store reference read first**, per CLAUDE.md, before touching anything under
  `loremaster/loremaster/store/` — and it earned its keep: §7's SYNTAX GOTCHAS table is what let me
  confirm the `briefs.py` R1 target actually carries the RELATE parse-error claim.
