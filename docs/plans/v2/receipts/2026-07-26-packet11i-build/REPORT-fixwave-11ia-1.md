# REPORT — `fixwave-11ia-1` · packet 11-i-a, closing the cold audit's findings

brief-base v7 read

`loremaster.__file__ = /home/ejprice/PycharmProjects/lore-pkt11ia/loremaster/loremaster/__init__.py`
— the worktree itself. **No scratch copy was made**: every mutation proof ran in the real
tree through `scripts/mutation_proof.py`, which takes a CONTENT backup and verifies a
byte-exact md5 restore (each proof's restore receipt is quoted in §3). `#185`'s
`scratch_copy.sh`/worktree hazard therefore never applied. **I ran no git write command of
any kind.** All work at parent HEAD `2b23862`, branch `pkt11-i-a-floor-machinery`.

---

## SUMMARY BLOCK

`Packages considered:` **none — no mechanism specified.** This wave specified no new
mechanism. Two package-adjacent facts were *read* rather than assumed, and both are recorded
below: the installed `kubernetes` 36.0.3 `electionconfig.py` source (R10 — its substitute
callback is not a no-op), and CPython's `concurrent.futures.TimeoutError is TimeoutError`
identity against this repo's `requires-python = ">=3.14"` (R10's second half). The packet's
own `orjson` adoption was re-verified as correctly resolved by the audit; F3 is a call-site
fix inside it, not a dependency question.

**State: done-with-deviations.** All 8 findings (F1–F6c) and all 10 in-scope residuals fixed.
**Three deviations, all additive and all disclosed in §5**: (1) three *sibling* `_MIN_KNOWN_*`
floors were stale in exactly R1's way and I raised them too; (2) F1's defect class extends
well past six sites, and I swept the whole file's SERVED messages plus present-tense
docstring claims rather than only the noun-split sentences; (3) R10's "harmless redundancy
×4" was a 4× clone of an error-classification POLICY, so it became one named tuple.

**Two items the audit described inexactly — reported, not quietly "closed":**
- **F6b is half wrong.** The third `ValueError` *was* pinned
  (`test_a_NON_STRING_axis_value_is_REFUSED`), just loosely — it accepts `ValueError` **or**
  `TypeError`. Only the *docstring* half of the finding was real. I fixed the docstring and
  added the discriminating pin; MP2 shows the pre-existing pin staying GREEN on a build that
  raises `TypeError`, which is the gap.
- **F2's live-impact reasoning needed a better fixture than mine.** My first probe reproduced
  the audit's "no live impact" and I nearly wrote it up — the fixture was wrong (§2.2).

**Gates — every number re-measured by me on the final, stationary tree** (`git status
--porcelain | md5sum` identical before and after the full run: `d3fa8d1a…`):

| gate | brief's expectation | my measurement | delta |
|---|---|---|---|
| contract (4 files, `-n auto`) | 210 passed | **218 passed** | +8 new pins |
| `test_retry_seam.py` (`-n auto`) | 561 passed | **562 passed** | +1 new pin |
| full suite (`-n auto`) | 7559 / 0 / 17 skip / 3 xfail | **7571 passed, 0 failed, 17 skipped, 3 xfailed**, exit 0, 232.40 s | +12 new pins |
| `scripts/` guards | — | **332 passed** | +3 (R8) |
| `scripts/typecheck.sh` | 162 clean | **162** loremaster (+27 lorescribe, +34 loresigil), exit 0 | — |
| `ruff check .` | clean | **`All checks passed!`**, exit 0 | — |

**+12 reconciles exactly**: domain +3, floor store +2, lease +3, retry seam +1, mutation-proof
guards +3. **Seven mutation proofs, all HELD, declared-set-from-`--collect-only`** (§3).

**Decisions needed — two, neither blocking:**
1. `surreal_schema.py` carries **four MORE bare `REPORT-*.md` citations** (R6's class), and
   unlike R6's they name reports that are **not tracked anywhere in this repo** — unfixable
   by me, since there is no path to point at. §5.4.
2. Whether the F1 sweep's boundary (SERVED messages + present-tense claims fixed; dated
   historical narrative kept) is where you want it. §2.1 lists every residual hit with an
   individual verdict, per the "all remaining hits are X is banned" rule.

**Receipts:** §1 per-item dispositions · §2 the two re-derivations that changed an answer ·
§3 the seven mutation proofs · §4 the F1 residual table (25 hits, individually verdicted) ·
§5 deviations and escalations.

---

## 1. Per-item disposition

| item | disposition | where |
|---|---|---|
| **F1** | **FIXED, and DERIVED rather than corrected.** The served assert message now COMPUTES the split from `_SEAM_REJECTION_NOUNS` (`_plain_noun_seams()` / `_domain_naming_seams()`), so it can never again hand a reader a hand-list that omits three seams. The prose claims lost their literals instead of gaining new ones. New pin `test_the_canonical_noun_map_is_not_a_MONOCULTURE` makes the "the values must differ" reasoning mechanical. §2.1 |
| **F2** | **FIXED — and the audit's "no live impact" is upheld for a *different, stronger* reason than my own first probe found.** §2.2 |
| **F3** | **FIXED + instrumented.** `corpus_content_digest` now passes `option=_PREIMAGE_OPTIONS`; byte-identical output verified before the change (a list has no keys), so no stored digest moved. Guarded by an AST allowlist pin. MP1. |
| **F4** | **FIXED.** The banner now says the signature was frozen by the contract author and the body was written by the builder. |
| **F5** | **FIXED.** No stub language survives in `lease.py`. |
| **F6a** | **FIXED (2 pins).** `TestACallerCannotForgeTheComputedColumns`, both legs with a positive control that the caller's payload still lands. MP3. |
| **F6b** | **PARTIALLY MISDESCRIBED — see summary.** Docstring fixed; discriminating pin added. MP2. |
| **F6c** | **FIXED (3 pins).** `TestLeaseErrorIsAKnownBoundNotAnAccident` — an absence pin, a positive control on its own walker, and a deletion guard. MP4. |
| **R1** | **FIXED, and three siblings with it.** §5.1. MP7 shows the raised floor is now tight. |
| **R4** | **FIXED.** The public `Raises:` now says "a cause on a row in ANY OTHER STATE" — keyed on `state`, not `adopt`, which is what `_validate_domain` actually branches on. |
| **R5** | **FIXED.** The false half of the comment is GONE rather than annotated; the two contradicting paragraphs are now one. |
| **R6** | **FIXED** → the tracked `docs/plans/v2/receipts/2026-07-26-packet11i-build/…` path. ⚠ Four more of the same class found; §5.4. |
| **R7** | **FIXED.** The message now names WHICH fate fired (absent row vs. present-row-no-revision) instead of naming one of two. |
| **R8** | **FIXED, contract-first** — the tests were RED before the change (tail quoted in §3.8) and the fix is an ALLOWLIST (pytest's `short test summary info` section), never a list of forbidden log prefixes. |
| **R9** | **FIXED.** The stated reason is now the real one: a RecordID sorts by its TYPED `Id`, and a chunk's is a `uuid5` **string**. Scoped to this table. |
| **R10** | **FIXED, both halves.** §5.3. |
| **R11** | **FIXED.** Cites `FenceLostError`'s class docstring, not "the stub". |
| **R13** | **FIXED.** The literal two-token catch clause no longer appears in the docstring, and the paragraph says WHY. |
| R2 · R3 · R12 · #241 · #242 · **F7** | **NOT TOUCHED**, per the brief. F7 is not in the brief's item list either; it concerns archived report text and I changed no report. |

---

## 2. The two re-derivations that changed an answer

### 2.1 F1 — the derived truth, re-derived (not relayed)

Run at `2b23862` with the module's own helpers, before any edit:

```
query seams 13 · nouns 13 total · plain 5 · domain-naming 8
plain  : DiffEngine, SnapshotStamper, SurrealCodeGraph, SurrealManifest, SurrealStore
domain : AgentRegistry, BriefLedger, FindingLedger, FloorCalibrationStore,
         LocalMemoryBackend, MessageLedger, SurrealLeaseStore, TaskLedger
```

The audit's `13 / 5 / 8` **reproduces exactly**. The retired served sentence hand-listed five
domain names and omitted **three** — `FloorCalibrationStore`, `SurrealLeaseStore` **and
`MessageLedger`**, the last of which pre-dates this packet, consistent with the audit's
attribution note (10 at `9d29111`, already 13 at `71ead8c`). No fix note blames this packet
for the drift.

**The fix is derivation, per your instruction.** The message now computes counts *and* both
name lists from the canonical map. **What cannot be derived, and why:** comments and
docstrings are static text — there is no expression to evaluate. So instead of re-typing a
correct number that will be wrong again in two packets, those sites lost the numeral
entirely ("the seams", "every seam", "one literal per seam"). The count now lives in exactly
two places that a gate reads: `_discover_query_seams()` and `_MIN_KNOWN_SEAMS`.

### 2.2 F2 — my first probe was wrong, and its fixture is why

The audit reports "probed with a positive control: no live impact today". My first
re-derivation appeared to *strengthen* that: a legacy `floor_head` row survived migration and
an `UPDATE` that never set `revision` was **ACCEPTED**. Taken at face value that would have
contradicted **store reference §1.4** ("a `DEFAULT` does NOT rescue an existing row"), which
is a load-bearing claim in this repo's most-read reference. I did not write it up.

An isolated probe with three legs and controls (`int DEFAULT 0` / bare `string` / `string
DEFAULT 'x'`, each added alone to a table holding one pre-existing row) says **§1.4 is
CORRECT on 3.2.1** — all three REJECT an unrelated `UPDATE` with `Expected <type> but found
NONE`. **My probe's "legacy" row was created AFTER the full DDL had been applied**, so
`DEFAULT 0` filled it at CREATE and the UPDATE passed trivially. *The fixture guaranteed the
one condition under which the hazard is invisible* — this repo's named failure mode,
committed by me, inside the wave about prose contradicting code. Caught by the control, not
by care.

Correctly fixtured (row written under the OLD DDL, then migrated):

```
legacy row survives migration : {'id': floor_head:legacy, 'scope': 'pooled'} | revision key: False
UPDATE without revision       : REJECTED -> Couldn't coerce value for field `revision` … Expected `int` but found `NONE`
the production mint           : ACCEPTED, revision = 1
CONTROL: same UPDATE post-mint: ACCEPTED   (so the reject was the missing column, not the statement)
```

So the docstring now states the sharper truth: `revision` is the ONE required column, §1.4
applies to it **in full**, a legacy row IS write-poisoned for any write that does not set it,
and the only reason nothing breaks is that **every production write is the mint, whose
`(revision ?? 0) + 1` sets it — the `??`, not the `DEFAULT`, is the rescue.** That is a
strictly more useful sentence for whoever writes the second writer.

---

## 3. Mutation proofs — seven, all HELD

Every declared RED set was taken from `pytest --collect-only -q` **before** the corresponding
run (node ids listed in one place, §3.0), and `scripts/mutation_proof.py` diffs the observed
set **both ways**. Every proof restored the file byte-exact (md5 quoted by the tool).

| # | pin proven | mutation | declared RED | result |
|---|---|---|---|---|
| MP1 | F3 AST allowlist | drop `option=_PREIMAGE_OPTIONS` from `corpus_content_digest` | 1 | **HELD** — and **39 other domain tests stayed GREEN**, which *is* F3's argument: no behavioural pin can see this |
| MP2 | F6b tightened pin | the non-str refusal becomes `TypeError` | 1 | **HELD** — the pre-existing loose pin stayed GREEN, which is the gap |
| MP3 | F6a ×2 | `object::extend` arguments SWAPPED (caller's payload wins) | 2 | **HELD** — 75 others green |
| MP4 | F6c absence pin | add a `raise LeaseError(...)` to `stop()` | 1 | **HELD** |
| MP5 | exact noun mapping | change ONE canonical noun | 1 | **HELD** |
| MP6 | monoculture guard | homogenise ALL 13 nouns to `"query"` | 2 | **HELD** |
| MP7 | R1 raised floor | rename one seam's `_query` out of the enumeration | 1 | **HELD** |

**MP7 is R1's whole argument, demonstrated rather than asserted:** with one seam dropped the
scan finds 12. `12 >= 13` is False → RED. Under the old floor, `12 >= 10` is True → the seam
would have vanished from the enumeration **with every gate green**. That is the vacuity the
floor exists to prevent, and the floor was carrying three slots of it.

**MP5 doubles as R8's live acceptance.** Its captured output contains
`ERROR    loremaster.store.lease:_txn.py:1199 lease.query.rejected` — byte-for-byte the shape
that made the cold audit's own proof exit 4 with phantom node ids — and the run reports
`PROOF HELD` with an exact declared set. §3.8 has the before/after.

### 3.8 R8, RED before the fix

`scripts/test_mutation_proof.py -k CapturedOutput`, on the unfixed helper:

```
FAILED …::test_an_ERROR_log_line_does_not_become_a_phantom_node_id
FAILED …::test_a_captured_FAILED_line_in_test_OUTPUT_is_also_ignored
2 failed, 1 passed, 11 deselected
  observed: ['test_target.py::test_alpha', 'tests/not_a_real_test.py::test_phantom']
```

The one that PASSED pre-fix is the **control**: `test_a_REAL_collection_ERROR_is_still_reported`.
It is not decoration — pytest reports collection failures as `ERROR <nodeid>` in the same
summary section, so a "fix" that simply stopped parsing `ERROR ` would trade a loud false
positive for a **silent blind spot**, which is strictly worse. All 3 green after the fix
(332 passed in `scripts/`).

**The bound this MOVES rather than closes**, stated in the tool's own `--help`: a command
that emits no `short test summary info` section now yields no node ids. That surfaces as the
existing loud `_EXIT_UNPARSEABLE`, or as a loud declared-but-green mismatch — never as a
quiet pass.

---

## 4. F1's residual table — every remaining hit, individually verdicted

Bare, anchor-free AST enumeration of every numeric word (`ten|five|eight|eleven|twelve|thirteen`)
in `test_retry_seam.py`, split by whether it is a **served message** (a string a reader sees on
a red) or a **docstring/narrative**. Before: **17 served + 28 docstrings**. After: **4 + 15**.
No hit is classified wholesale.

**The rule I applied, stated so you can overrule it:** a stale count in a *served failure
message* or in a *present-tense claim about what the tree contains* is a DEFECT and was fixed;
a count inside a *dated historical narrative* (`RED before 9d29111`, "the adversary built…",
"Measured: 489/0") is a RECORD and was kept — rewriting those to 13 would falsify history.

**Served messages still carrying a numeral (4):**

| line | text | verdict |
|---|---|---|
| L4619 | "The thirty closures and ten attempt bodies **this wave deleted (the population at `9d29111`)**" | KEEP — dated by me in this wave |
| L4761 | "Thirty closures and eleven copies **at `9d29111`**" | KEEP — dated by me in this wave |
| L8061 | "Measured: all eleven owners hardcoding one RPC address passed **the previous contract 489/0**" | KEEP — a dated measurement of a specific adversary build |
| L6133 | "the sentence that used to live here said 'five of the ten' and hand-listed five names" | KEEP — my own quotation of the corpse, deliberate |

**Docstrings still carrying a numeral (15):** L1 (×3, my own dated #120 account) · L928 and
L3656 ("five attempts" — the pre-#102 *retry budget*, a different quantity entirely) · L1041
(×2, the #120 wrong-build narrative) · L1602 (×2, "THE WRONG BUILD THIS EXISTS FOR") · L2066,
L4739, L5514, L5581 (×2) (all four open "RED before 9d29111") · L6194 (my own quotation of the
retired sentence) · L7524 ("twelve call shapes: six seen" — unrelated measurement) · L7812,
L8028 (×2), L8040 (×2), L8154 (×3) (the #151 url-blocker narrative, all carrying their own
measured receipts). **Two I flag as borderline rather than silently keep:** L1602's "there are
ten private copies wearing one name" and L8028's "Eleven owners, eleven urls" read
present-tense while sitting inside wrong-build narratives. I left them; say the word and they
go.

**Fixed in this sweep:** 13 served messages and 14 present-tense docstring claims — listed by
the diff, all de-numeralised rather than re-numbered.

---

## 5. Deviations, and everything else I noticed

### 5.1 DEVIATION — R1 had three siblings, and I raised them too

R1 names `_MIN_KNOWN_SEAMS`. Re-deriving every floor in the file against its own scan at
`2b23862`:

| floor | was | live | margin |
|---|---|---|---|
| `_MIN_KNOWN_SEAMS` | 10 | **13** | 3 |
| `_MIN_KNOWN_SOCKET_OWNERS` | 10 | **13** | 3 |
| `_MIN_KNOWN_BOOTSTRAP_OWNERS` | 11 | **14** | 3 |
| `_MIN_KNOWN_BOOTSTRAP_CALL_SITES` | 11 | **14** | 3 |
| `_MIN_KNOWN_RETRY_DRIVER_CALL_SITES` | 8 | 8 | 0 ✓ |
| `_MIN_KNOWN_CONFLICT_SIGNAL_RAISE_SITES` | 5 | 5 | 0 ✓ |

**Four stale, all by exactly 3.** Leaving three of them for the next agent while fixing the
fourth is the can-kick the law forbids, and each carries the same silent-vacuity exposure MP7
demonstrates. Set membership was measured, not assumed: `bootstrap_owners − query_seams =
{CommandSubscriber}` exactly, and `socket_owners == query_seams` exactly.

**⚠ A near-miss inside this fix, worth your attention.** I first wrote
`_MIN_KNOWN_BOOTSTRAP_OWNERS = _MIN_KNOWN_SEAMS + 1` — pleasingly DRY, and **wrong**:
`test_the_two_independent_owner_counts_AGREE` asserts that floor equals
`_MIN_KNOWN_BOOTSTRAP_CALL_SITES` precisely because two *independent* scans must corroborate
each other. Defining one in terms of the other turns that pin into `X == X` — a pin that
cannot fail, inside the wave about instruments that certify nothing. Caught by asking "what
wrong build would still pass this?" of my own edit. Both are literals, and the docstring now
says why.

### 5.2 DEVIATION — F1's blast radius is larger than six sites

See §4. Sixteen served messages (not six) carried a stale population count, plus ~14
present-tense docstring claims. The whole file's `ten`/`eleven` vocabulary was written when
there were ten seams. I swept it on the rule in §4 rather than stopping at the noun-split
sentences, because the class — not the instance — is what F1 is about. Nothing was
re-numbered; every fix removes a numeral or dates it.

### 5.3 DEVIATION — R10's "harmless redundancy ×4" was a cloned POLICY

`except (SurrealStoreError, concurrent.futures.TimeoutError, TimeoutError)` appeared at four
sites. Two facts, both READ rather than assumed: `concurrent.futures.TimeoutError is
TimeoutError` → **True** (same class object since 3.11; this repo's floor is
`requires-python = ">=3.14"`), and the installed `electionconfig.py` substitute logs at INFO.
Four hand-written copies of an error-classification tuple is duplicated *policy* — four places
a future class gets added to three of — so it is now one named `_LOCK_CALL_ERRORS`, and
`import concurrent.futures` is gone. Behaviour is identical; 218/218 contract and the full
suite confirm.

### 5.4 ESCALATION — four more forbidden `REPORT-*.md` addresses, and these are unfixable

R6's citation was one string from a tracked path. Sweeping the same writable files for the
same class found four more, all in `surreal_schema.py`, and **none of the reports they name
exists anywhere in this repo** (`git ls-files` → empty for each):

| site | cites | tracked? |
|---|---|---|
| `surreal_schema.py` :403 and :512 | `REPORT-c1-contract-schema.md` | **NO** |
| `surreal_schema.py` :525 | `REPORT-probe-7061-c1.md` | **NO** |
| `surreal_schema.py` :917 | `REPORT-c1f-contract-migration.md` | **NO** — and this one is cited *by the store reference itself* |
| `surreal_schema.py` :1373 | `REPORT-c1-builder-mint.md` | **NO** |

These are #152/#153's "54 dangled" population, still live and pre-dating this packet. I did
**not** touch them: a citation cannot be repaired by inventing a path, and the honest repairs
(delete the citation, or replace it with a finding number / commit SHA / in-tree symbol) are
content decisions that are yours, not mine. `REPORT-c1f-contract-migration.md` §4 is also
cited from `docs/reference/surrealdb-31-capabilities.md`, so whatever you decide should
probably cover both.

### 5.5 Other things I noticed and did not act on

- **The full suite's one warning** is the pre-existing `RuntimeWarning: coroutine
  '_empty_subscription' was never awaited` in `test_retry_seam.py`'s scout pin. Present at
  `2b23862` before my changes; unrelated to this wave.
- **`/home/ejprice/scratch-ca11ia` is still on disk** — the cold audit's scratch copy, which
  its own §9 flags for your decision. I did not touch it (it is outside the repo, and its
  `.git` pointer is renamed aside).
- **F7's three non-reproducing receipts** live in archived reports. I changed no report text;
  if you want the archived copies annotated, that is a separate, deliberate edit.

**There are 0 failing tests in the full suite.**

---

*Measured 2026-07-26 in the worktree `/home/ejprice/PycharmProjects/lore-pkt11ia`, branch
`pkt11-i-a-floor-machinery`, parent HEAD `2b23862`, against the SurrealDB 3.2.1 TEST store
`ws://127.0.0.1:18000` only (every probe script asserted `"18500" not in URL` before
connecting, and dropped its throwaway database in a `finally`).*
