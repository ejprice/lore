# Packet 58 — Amendment 16: the r5 delta grade bucketed — five folds, one unsatisfiable pin of mine to correct, and the ONE re-grade that closes the cap

brief-base v27 read · brief project v7 read

**Author:** sidecar-58-1 (Fable design sidecar, fork ruler for packet 58) · **Date:** 2026-11-09 (local) · HEAD `d3344ad`
**Authority:** operator grant 2026-11-09 via lead-58 (forks and design questions go to the sidecar); the operator may
overturn. **Answers:** lead-58's Q4 (lore_comms #20027).
**Rules:** `REPORT-adversary-58-r5-2.md` (graded `805a687`, verdict INSUFFICIENT) — read: §SUMMARY BLOCK, §SAT FINDING,
§MISSING PINS MP-1…MP-5, §LOAD, §P1b, §P1c, §INDEPENDENCE, §P2, §RESIDUALS, §MUTATION, §SAT, MP-0. NOT read: §WB-OWN,
§DECLINED-DIFF, §RUNS in full, §W-STAR beyond its first row, §INSTRUMENTS.
**Amends:** am-15 §1.2 (the refusal's served facts — now typed, with a ruled text), §10.3 (i) (erratum, mine), §5 (the
loop cap, made exact), §9.2 / §4.2 (the 63c class, third instance).

## SUMMARY BLOCK
- **State:** done.
- **Deviations:** none.
- **Packages considered:** none — no mechanism specified (pins, a typed error carrier, a fixture size).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none — no new rule-deciding symbol. The typed attributes land on `HubSupersedeRefusedError` and
  `StragglerHealPackerError`, both already ruled.
- **Graded:** n/a (a ruling). The verdict I bucket was graded at `805a687`; HEAD `d3344ad` is 3 ahead (gate per-node
  fix, probe sign-in, f6 prose — the adversary states no 58 test or sweep file moved).
- **Decisions needed:** one for the lead — a writable-set grant for the 63c files §4's sweep names (same class as
  am-15 §9.3).
- **Pointers:** §0 buckets · §1 the over-fire and my erratum · §2 the five folds, each with its pin · §3 residuals ·
  §4 the 63c class · §5 the loop cap · §6 the r5.2 FOLD LIST.

## 0. The buckets in one screen

| item | adversary's tag | my bucket | goes to |
|---|---|---|---|
| **MP-0** legs (i)/(ii) red on the reference | unsatisfiable pin | **RULING ERRATUM (mine, am-15 §10.3 (i)) + contract over-specification** | r5.2, §1 |
| **MP-1** WD17, refusal's served facts | NEW PROPERTY | **DROPPED RIDER** of am-15 §1.2 — a property ruled inside this delta and never pinned; not new | r5.2, §2.1 |
| **MP-2** WD16B, plain re-raise | new case | PINNED PROPERTY, NEW CASE (the pin observes a proxy) | r5.2, §2.2 |
| **MP-3** WD9, kind guard | new case, repeat class | PINNED PROPERTY, NEW CASE — **third instance of one class → class fix, §4** | r5.2, §2.3 + §4 |
| **MP-4** WD15D, size-conditional `rows=` | new case | PINNED PROPERTY, NEW CASE (small-N) | r5.2, §2.4 |
| **MP-5** WD12K, swallow at chunk ≥ 2 | new case | PINNED PROPERTY, NEW CASE (the quantifier guarded by "first chunk") | r5.2, §2.5 |
| **NEW PROPERTY** | 1 (MP-1) | **0** | — |
| **SECURITY DOOR** | — | none | — |

**(c) in one line:** r5.2 gets ONE re-grade — a REPLAY by the same adversary, not a new enumeration. That is the
global cap's "initial grade + one re-grade" used exactly; after it only a NEW PROPERTY reopens (§5).

## 1. MP-0 — the over-fire: my erratum, and the door pins without a hand-number

- **What I wrote (am-15 §10.3 (i)):** the observed doors "include the heal's read and the heal's apply, **by
  name**". I never checked that the sweep can name a door. It cannot: it knows a door's ordinal and which seam was
  called. r5.1 turned "by name" into a count (`legacy + 1`) because a count was the only handle the instrument
  offered. The reference adds four doors (three heal reads and the apply), all loud, so the pin is red on a
  correct build. A rule written against an instrument I had not read — the same class as my am-3 packer erratum.
- **The property, restated so it needs no count:** *every store call the boot makes is a door that fails loud; and
  a straggler makes the boot do heal work it does not do without one.*
- **Ruling — no 58 leg in the sweep asserts a door COUNT as a literal or as `other + n`.** Counts are compared
  only between two MEASURED worlds, or between a world's own two measurements. **Pin it like this:**
  1. **Reach (each world):** `len(doors) == control_calls` — every call the unfaulted boot made was faulted in turn.
  2. **Loud (each world):** every derived door fails the boot loud.
  3. **Difference (the straggler world vs its twin without the straggler — leg (iv)'s pair):** the straggler world
     has strictly more WRITE-seam doors and strictly more READ-seam doors than the twin. That is the heal's apply
     and the heal's straggler reads, shown present by what the straggler changes.
  4. (ii)'s non-vacuity gate becomes item 3's write-door inequality, then item 2.
  - On the reference: 8 vs 5 calls, more read and more write doors, all loud → GREEN. At HEAD (no heal): the two
    worlds are equal → RED for 58's reason.
- **The former-#614 legacy leg's `control_calls == 5`** is the same hand-number (it breaks the day the heal makes
  one more boot read). Same rewrite: items 1 and 2. If that leaves it GREEN at HEAD, its id comes OFF 58's
  `red_nodeids` in the same change — the registry lists only what is red.
- **What wrong build passes the new legs?** A heal that swallows a fault at a door only a multi-chunk world
  reaches. That is MP-5, closed in §2.5, not here.

## 2. The five folds — each with its pin

### 2.1 MP-1 — the refusal's served facts are typed, derived, and rendered from one ruled sentence
- A dropped rider: am-15 §1.2 ("the row count the refusal serves == `fragment_rows` of the fragments it built")
  and §6 item 1 were marked done with nothing asserting them; the reference itself serves neither the rows nor
  the cap. Not a new property — it is this delta's own, graded here for the first time.
- **Ruling.** `HubSupersedeRefusedError` carries four integers: `dependents`, `rows`, `row_cap`, `cap_dependents`.
  Its message is rendered FROM them by the error itself, as exactly:

  > `task <X> has <dependents> dependents; re-anchoring them composes <rows> rows, over the <row_cap>-row
  > transaction cap (the build-time bound admits at most <cap_dependents> dependents) — refused, nothing changed.
  > This is a pinned KNOWN BOUND (58 F-1); file it with lore_findings.`

  This supersedes kickoff §1's wording. It states the fact refused and promises nothing about a smaller
  supersede (am-15 §1.3).
- **Pin it like this (the cap+1 leg, K ∈ {0, 2}, under the 5,000 fixture):** `dependents == cap + 1`;
  `rows == fixed(K) + per·(cap + 1)` with `fixed`/`per` measured at the compose spy at N = 1, 2, 3 (the class's
  existing derivation); `row_cap == _txn.TXN_ROW_HARD_CAP`; `cap_dependents == max_reanchor_dependents(K)`; and
  `str(error)` equals the sentence above built in the test from those four values and the task id. Exact text, so
  an appended promise or a re-spelled number reds; this also retires the substring checks (R-7).
- **Sibling, same class, same pass (R-3):** `StragglerHealPackerError` carries `row_id`, `weight`, `row_cap` as
  typed attributes; the pin asserts `weight == fragment_rows(<that row's fragments>)` and
  `row_cap == _txn.TXN_ROW_HARD_CAP`. Its text is a boot-failure message, not a served render: not pinned
  verbatim, but r5.2's reference stops saying "statements".

### 2.2 MP-2 — "decided before compose" observed at compose, not on an exception attribute
- The A-9 pin I ruled (am-15 §8.2) checks `__cause__`; a plain `raise` inside `except` sets `__context__`. My pin
  observed a proxy.
- **Pin it like this:** in the cap+1 leg the compose spy shows `compose` was never called with fragments whose
  `fragment_rows` exceeds the cap. Not "never called at all" — a correct build may compose small sample
  transactions while deriving. The `__cause__` check and R-6's synthetic positive control are replaced by this
  plus a control: the same spy DOES record an over-cap call when the test composes the ledger's own cap+1
  fragments directly.

### 2.3 MP-3 — the kind guard for the four markers
- **Pin it like this:** 63c's `test_am36_1_2_3_a_typed_kind_never_reaches_the_text_branch` gains, by DERIVATION
  from `_txn` (r5's `fifty_eight_thrown_markers()` and the constructed labels), one hostile text
  `An error occurred: <marker>…` per marker and the four labels in `text_labels`. GREEN on the reference, RED on
  WD9. The class behind it is §4.

### 2.4 MP-4 — un-annotated at every size the contract already builds
- **Pin it like this:** `spy.annotated_calls() == []` inside L2 (1,666 dependents) and L3 (the 1,251-row heal).
  No new fixture.
- Stated bound, accepted: a `rows=` under-declaration that only triggers above the largest size the contract
  builds (L2's 5,002 rows) is not killed. Its consequence is §1.3's WARN firing late. The cold audit reads every
  58 fragment builder for a `rows=` argument (a read, not a scanner).

### 2.5 MP-5 — a store fault at ANY heal door raises, for every chunk
- Both store-fault fixtures held one straggler, so one chunk. The multi-chunk legs inject exhaustion only.
- **Pin it like this:** r2's `test_every_heal_door_after_the_backfill_RAISES` runs over a world of `2·fit + 1`
  stragglers, where the row cap is shrunk INSIDE that test to four times one straggler's measured weight (so
  `fit` is 4, the world is 9 stragglers and 3 chunks — the 5,000 fixture exists to keep GRADED scales, and this is
  a new leg). Every derived door, the second and third chunk's applies included, raises and nothing more is
  written. Fault classes: store, transport, and `SurrealOutcomeUnknownError` (the adversary's untried sibling;
  SDK3 added the class after r2 was written).
- Non-vacuity, in the same leg: the control boot shows ≥ 3 write-seam doors, or the leg fails naming the count.

## 3. Residuals and the open runs

| item | ruling |
|---|---|
| R-1 a packer bound above L3's 5,004 rows | BOUND, accepted: more chunks, each atomic, convergence intact. Trigger: a heal `chunks` log above 1 on a population under 50,000 rows. |
| R-2 a private `len(statements)` counter | already ruled (am-15 §2): cold-audit mutation. |
| R-3 packer error says "statements" | folded, §2.1. |
| R-4 the adversary's own scaffolding reds one fates leg | instrument artifact; no action. |
| R-5 `more-itertools` undeclared | BUILDER CONSTRAINT stands (BC-r4-1); the cold audit checks the lockfile. |
| R-6, R-7 | subsumed by §2.2 and §2.1. |
| §INDEPENDENCE — the adversary re-ran r5's reference rather than building its own | ACCEPTED, named: SAT has been measured twice on ONE reference. The independent reference is the real build, at the cold audit. The over-fire shows the check still bites. |
| WD22 / WD22H / W-HEAL2 / W-F3-ROOT / W-F4-PREFIX / W-NOOP-DRIVERS — unresolved under load | **r5.2 does not close until each has a verdict from a quiet run.** A survivor is a STOP naming the pin (am-12 §3) and comes to me. |
| r4's heal leg `[ensure_ready -> _reanchor_stragglers]` timed out on the reference, slow vs hung undetermined | must be DETERMINED before any build: one isolated run with a long timeout. Hung = a reference or leg defect, to me. Slow = that leg takes §2.5's in-test shrink so it finishes inside the suite's per-test timeout on a quiet host. A pin that times out on a correct build is the C-DEF class. |

## 4. (d) The 63c exact sets — third instance, so the class, not the member

Fold item 7, then F-4's three files, now MP-3: three times a landed 63c pin's hand-list lacked 58's members, and
each was found by tripping over it. Two waves is the limit for instance fixes.
- **The derivable worklist:** 58's four classes are the same KIND of thing as the governed conflict (a THROW our
  guard authors, typed, anchored, mapped). So every test site that lists the governed member must list 58's four
  or say why not. r5.2 sweeps the test tree with the bare pattern
  `GOVERNED_CONFLICT|GovernedConflict|governed_conflict` (rename-class exhaustiveness — grep is right; coverage
  line), and gives every hit file:line and its own verdict: *covers 58's four* · *must grow (by derivation from
  `_txn`)* · *not a member list (reason)*.
- **Rider — and pin it like this:** each site that grows is a DUAL row (member · am-15 §4.1/§9.1 · test id), and
  the adversary's WD9 / WD8 / X7B builds are replayed against the grown sets at the re-grade (§5).
- **(d) answered: yes, a §9.3-style grant.** These are contract-author edits to landed 63c/SDK3 test files. The
  lead grants the writable set the sweep's *must grow* rows name, member additions only.
- am-15 §4.2 said converting those hand-lists to derived sets "is not 58's work". That stands for the lists'
  OTHER members; 58's own members go in by derivation, which is all three fixes so far already did.

## 5. (c) The loop cap, exact

- **The rule:** initial grade + one re-grade; after that only a NEW PROPERTY reopens (global rule 3; am-15 §5
  said "this is the one grade" and routed pinned-property cases to an ungraded fold).
- **Why r5.2 is not sent ungraded.** am-15 §5's ungraded-fold route assumed folds of things the adversary had
  verified. r5.2 instead writes seven new or rewritten pin families, one of them the replacement for a pin that
  was red on a correct build, and one from a ruling of mine that was wrong about the instrument. The last
  ungraded step in this packet (r5.1's heal-door legs) is exactly where the unsatisfiable pin came from.
- **Ruling: the ONE re-grade the cap allows, scoped as a REPLAY.** Same adversary (its trees and switches
  exist; if it cannot be resumed, a suffixed respawn works from its report's §INSTRUMENTS, which are pasted
  verbatim with md5s). Scope, exhaustive:
  1. SAT of r5.2's new and rewritten legs on the reference (which r5.2 updates to serve §2.1's typed facts);
  2. replay WD17, WD16B, WD9, WD15D, WD12K — each must now die, by the pin §2 names;
  3. the six unresolved builds of §3, on a quiet host;
  4. the §4 sweep's grown sets against WD8 / WD9 / X7B.
  It enumerates NO new wrong builds and writes no new P1b rows beyond the seven families.
- **After it, the cap is closed.** A survivor of item 2 or 3 comes to me once: if the pin is simply wrong, the
  author corrects that pin and the lead verifies the one replay himself (run, count line, diff) — no further
  adversary run. Anything else waits for the build's cold audit. Only a NEW PROPERTY reopens the loop.
- **Cost for the operator:** packet 58 stands at 4 adversary runs and 6 author runs (r1–r5.1). This adds one
  replay-scoped adversary run and one author run (r5.2).

## 6. The r5.2 FOLD LIST (contract-58-r5 executes; every item carries its pin)

1. **Door legs without counts (§1).** Rewrite (i), (ii) and the legacy `== 5` leg to reach + loud + difference.
   *Pin:* GREEN on the reference, RED at HEAD for the missing heal; any leg that goes GREEN at HEAD leaves
   `red_nodeids` in the same change, and `--verify-registry` stays OK.
2. **Typed refusal (§2.1).** Four attributes equal to derived values; `str(error)` equals the ruled sentence.
   *Pin:* WD17 and a build that omits rows/cap both red; the reference is updated to serve it.
3. **Packer error (§2.1 sibling).** `row_id`, `weight`, `row_cap` typed; `weight == fragment_rows(row fragments)`.
4. **Before compose (§2.2).** Spy: no compose call over the cap, with the direct-compose control. *Pin:* WD16B reds.
5. **Kind guard (§2.3)** in 63c's typed-kind pin, by derivation. *Pin:* WD9 reds, the reference is green.
6. **Un-annotated at size (§2.4).** `annotated_calls() == []` in L2 and L3. *Pin:* WD15D reds.
7. **Every chunk's door (§2.5).** 9 stragglers / 3 chunks under an in-test shrink; three fault classes; ≥ 3
   write doors asserted. *Pin:* WD12K reds; the leg finishes inside the per-test timeout on a quiet host.
8. **The governed-member sweep (§4).** Every hit file:line with its verdict; each grown site a DUAL row.
9. **The six unresolved builds and the slow-or-hung leg (§3).** r5.2's report carries each verdict, or names the
   one still open. The author runs no wrong build: the verdicts are the adversary's, pulled from its report.
10. **§DECLINED** is refreshed: any mutation proof these seven families need and the author may not build.
11. **SAT receipt:** 0 attributable reds over the declared targeted set on the updated reference,
    `loremaster.__file__` printed; `--currency --legs typecheck,ruff` at RED_ORPHANED 0.

No production code, test, registry or store touched by this amendment. No attribution trailer on the commit.
