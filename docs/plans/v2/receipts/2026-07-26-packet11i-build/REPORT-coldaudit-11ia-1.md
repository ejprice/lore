# REPORT — `coldaudit-11ia-1` · packet 11-i-a cold audit (REFUTE stance)

brief-base v7 read

**Provenance.** Gates and probes ran in the worktree `/home/ejprice/PycharmProjects/lore-pkt11ia`.
The mutation proof ran in a `scripts/scratch_copy.sh` copy whose provenance the tool asserted and
which I re-printed: `loremaster.__file__ = /home/ejprice/scratch-ca11ia/loremaster/loremaster/__init__.py`.
Per #185 the copy's 71-byte worktree `.git` pointer was renamed out of the way before any work; no
git command ran inside the copy. I ran **no git write command** anywhere.

**Freeze verification.** Measured 2026-07-26.

| | HEAD | `git status --porcelain` sha256 |
|---|---|---|
| start | `acd2b617d70fc6b795146e46cf4a4be0d0607e38` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty input ⇒ clean tree) |
| end (all measurement complete) | `acd2b617d70fc6b795146e46cf4a4be0d0607e38` | `e3b0c442…52b855` |
| after writing THIS file | `acd2b617d70fc6b795146e46cf4a4be0d0607e38` | one line: `?? REPORT-coldaudit-11ia-1.md` |

⚠ The only worktree change I made in the whole run is this report, written **after** every
measurement above was complete. Disclosed rather than glossed: the end-state hash differs from the
start-state hash for exactly that reason and no other.

The freeze was additionally re-checked **before and after each** of my 10 independent contention
iterations (head and worktree md5 identical on all 20 checks — `/tmp` log, reproduced in §6). Every
number below therefore describes a stationary subject.

---

## SUMMARY BLOCK

`Packages considered:` **none — no mechanism specified.** This audit built nothing; it re-ran
existing gates and used the repo's own committed instruments (`scripts/scratch_copy.sh`,
`scripts/mutation_proof.py`, `scripts/contention_hunt.sh`'s method) rather than writing new ones.
The one place a package question arose — the packet's own `orjson` adoption under ruling O1 — I
verified as **already correctly resolved** (declared dependency, not transitive) and re-derived its
one-place violation as F3.

**VERDICT: GO**, with one recommended pre-merge fix (F1) and eleven residuals. Nothing I found
causes a wrong served value, data loss, or a liveness failure. The three design defects the
contract caught are **not** reintroduced; the store law is obeyed; routing **is** sharing, proven
by mutation. Every gate number the brief predicted reproduced **exactly**.

**Gate numbers, re-measured by me on `acd2b61` (not relayed):**

| gate | expected | **my measurement** |
|---|---|---|
| contract (4 files, `-n auto`) | 210 passed | **210 passed** in 11.63 s |
| `test_retry_seam.py` (`-n auto`) | 561 passed | **561 passed**, 1 warning |
| full suite (`-n auto`) | 7559 / 0 / 17 skip / 3 xfail | **7559 passed, 0 failed, 17 skipped, 3 xfailed**, 194.92 s |
| `scripts/typecheck.sh` | 162 files clean | **162** loremaster (+27 lorescribe, +34 loresigil), exit 0 |
| `ruff check .` | clean | **`All checks passed!`**, exit 0 |

**Defects, ranked by the failure each causes**

- **F1 (should fix pre-merge — served English, this packet's own blast radius).** `test_retry_seam.py`'s
  prose says **ten** seams / *"five plain `query`, five that name their domain"* in six places, incl. a
  **served assert failure message**. Derived from the pin's own dicts: **13 entries, 5 plain, 8
  domain-naming** — and the message's enumerated list omits this packet's own two. Failure: an engineer
  or agent reading a red is told a wrong population and handed a list that excludes the new seams.
  ⚠ **Attribution, re-derived, because it is not all this packet's:** `_SEAM_REJECTION_EVENTS` was
  10 at `9d29111` and **already 13 at `71ead8c`** — the packet added the two *entries*, not the drift.
- **F2 (DEFECT, prose vs code).** `surreal_schema._floor_head_statements` docstring: *"Everything except
  the axis columns' own `scope` is optional"*. Wrong both ways — `scope` **is** `option<string>` (the
  inline comment four lines below says so), and `revision` is `int DEFAULT 0`, **not** optional.
  Failure: teaches a future author that a `floor_head` write need not set `revision`; store ref §1.4
  says a `DEFAULT` does not rescue an existing row lacking it. **Probed with a positive control (§4):
  no live impact today** — every write is the mint, which sets `revision`.
- **F3 (DEFECT, ONE IMPLEMENTATION).** `domain.py` declares *"the pre-image encoding, in ONE place"*
  and *"**BOTH** PRE-IMAGES ARE `orjson.dumps(..., option=OPT_SORT_KEYS)`"* — but
  `corpus_content_digest` calls `orjson.dumps(pairs)` with **no `option=`** and never touches
  `_PREIMAGE_OPTIONS`. Two encoding sites, one bypassing the named single place; O1 §4 says *"Row 9
  goes the same way"*. No divergence today (a list has no keys to sort) ⇒ nothing can go red.
- **F4 (MISLEADING, and the lead asked about exactly this).** `surreal.py`'s C8 banner still says
  *"WRITTEN BY THE CONTRACT AUTHOR … NOT BY A BUILDER"* — the word `STUB` was deleted two lines above
  and this was left. The 40-line body **was** written by the builder. The other four banners were
  rewritten correctly; this is the one half-fixed.
- **F5 (MISLEADING).** `lease.SurrealLeaderLock.__init__` docstring still says *"real even in **the
  stub**; the three METHOD members are **stubbed below**"* — nothing is stubbed.
- **F6 (unpinned load-bearing claim ×3).** Three integrity properties are asserted only in prose, with
  zero tests: (a) *"a caller cannot forge `head_identity`"* (`object::extend` precedence) — **I probed
  it TRUE with a control**, but a reshape of the statement would silently re-open it; (b)
  `head_identity`'s third `ValueError` (non-`str` axis value) is neither documented in the public
  docstring nor pinned; (c) **`LeaseError` has ZERO test references** — a documented KNOWN BOUND with a
  named delete-it trigger and no instrument ("a trigger nobody measures is a hope"), and a member of the
  frozen interface that can be deleted with every gate green.

- **F7 (report receipts that do not reproduce — no code impact, but this repo treats receipts as
  evidence).** Three, each re-derived by me: the closure's docs-sweep receipt claims *"no hits"* for a
  grep that returns **4** at its own spawn HEAD (substance survives — 0 in live `docs/`); the builder's
  transcribed gate command runs as **`no tests ran`, exit 0** (the silent-green shape); and #242's
  *"twelve copies … all twelve owners out of the AST enumeration that covers them"* matches **no**
  scoping of the enumeration (11 then, 13 now). Details and derivations in §8b.

**Residuals: see §7 — thirteen items, incl. a grep blind spot on the packet's own rulings and two
flaws in `contention_hunt.sh`, the instrument #241's disposition would lean on.**

---

## 1. The freeze, and what I discarded

Nothing was discarded. HEAD and the worktree hash were identical at every one of the 22 checks I made
(start, end, and before/after each of 10 contention iterations). `uv run --no-sync` was used
throughout so no lockfile or venv write could perturb the subject.

## 2. The three defects the contract caught — **none reintroduced** (verified in code)

Source of the list: `RULINGS-2026-07-26-contract-11ia.md`, closing section.

1. **Absent-`get` return shape.** `SurrealLeaderLock.get` returns `(False, _lock_absent())`, and
   `_lock_absent()` builds `LockAbsent(body=json.dumps({"code": 404, …}), reason=…, status=404)` —
   an object carrying `.body` as a JSON string with a `code` key, which is what the algorithm's
   `json.loads(old_election_record.body)['code'] != HTTPStatus.NOT_FOUND` branch requires. The
   store-failure path is a **separate** non-404 shape (`_lock_unavailable`, 503), so a read fault
   routes to the library's "error retrieving resource lock" channel and does **not** license a
   create against a row that may exist. Neither `(False, None)` nor a bare `ApiException` appears.
2. **No record decoration.** `get`'s TRUE branch returns
   `LeaderElectionRecord(holder_identity, lease_duration, acquire_time, renew_time)` — exactly the
   library's four positional fields, nothing appended. `revision` / `fence_epoch` are carried on the
   adapter (`_observed_revision` / `_observed_fence_epoch`), never on the record, so the algorithm's
   `__dict__` comparison cannot see a field that moves on an unrelated write. The wedge (a dead
   leader's lease never expiring) is closed.
3. **Forgeable digest concatenation.** `corpus_content_digest` is
   `sha512_hex(orjson.dumps([[point_id, content_hash], …]))` — a JSON list of pairs, delimited at both
   ends of every field, so `("ab","c")` and `("a","bc")` cannot collide. `head_identity` is
   `sha512_hex(orjson.dumps(mapping, OPT_SORT_KEYS))`. No bare concatenation survives, and the NUL
   refusal is correctly **absent** (O1 dissolved it). See F3 for the one-place violation.

Corollary confirmed for defect 3's sibling: `_LEASE_RECORD_STRING_COLUMNS` emits all four library
record fields as `option<string>`, so a `datetime`-typed `renew_time` cannot reject a renewal.

## 3. The store law — clause-by-clause, and the dirty-store question

`_define_table` → `DEFINE TABLE IF NOT EXISTS … SCHEMAFULL` ✓ (plain-table row) · `_define_field` →
`DEFINE FIELD OVERWRITE` ✓ (§1.1 FIELD row, #107) · `_plain_index` → `DEFINE INDEX IF NOT EXISTS` ✓
(never `OVERWRITE`) · no `ALTER`, no `TYPE RELATION`, no `DEFINE SEQUENCE` in either new slice (pinned).

**"What would a dirty store do that a virgin one cannot show?"** — each of the three new tables has a
REAL dirty-store migration leg, and all three follow the house shape (apply a **narrowed** definition →
insert a row → re-apply the real DDL → assert the widened definition landed AND the old row survived):

| table | pin | verdict |
|---|---|---|
| `floor_measurement` | `TestTheSchemaMigratesAnEXISTINGStore::test_a_narrowed_state_assert_MIGRATES_back_to_the_full_set` | real, discriminating |
| `lease` | `…::test_the_LEASE_slice_migrates_a_NARROWED_field_on_an_existing_store` (M14) | real; `holder_identity` chosen because decision 23 needs NONE |
| `floor_head` | `…::test_the_FLOOR_HEAD_slice_migrates_a_NARROWED_field_on_an_existing_store` (M14) | real |

The O7 required-column pin (`test_a_measurement_row_with_NO_head_identity_is_REFUSED`) uses a broad
`pytest.raises(Exception)` — but it carries a **positive control** (the *same* CONTENT shape plus
`head_identity` is accepted and read back), which rules out the pass-on-a-ParseError shape this repo
has a receipt for. It discriminates.

**The one gap, and it is INHERITED, not new:** the `floor_measurement_head_created` index is
`IF NOT EXISTS` — correct per §1.1, and therefore carrying store ref §8's documented silent-no-op
hazard for any future FIELDS change. Nothing pins that bound *for this index*. §8 records the class
repo-wide (*"the others are covered by nothing"*), so I log it as a residual, not a packet defect.

## 4. Live probes — mine, on the TEST store `ws://127.0.0.1:18000` only, each with a control

Throwaway `lore_test` databases, dropped in a `finally`. `assert "18500" not in URL` guarded every
script. All three load-bearing builder claims **hold**:

```
PROBE1 second-object-wins: head_identity = 'COMPUTED-TRUTH'   -> PASS (computed wins over caller)
PROBE1 control (no collision): payload's own key lands        -> 'caller-value'
PROBE2 holder CHANGES A->B: fence_epoch 7 -> 8                -> PASS (the IF saw the OLD holder)
PROBE2 control same holder B->B: fence_epoch -> 8             -> PASS (unchanged)
PROBE2 control stale CAS: result=[] row untouched             -> {'fence_epoch': 8, 'holder': 'B', 'revision': 5}
PROBE2 control released NONE->B: fence 8 -> 9                 -> PASS (bumped)
PROBE3 UPSERT (revision ?? 0) + 1 on absent row: 1, then 2    -> PASS
ORDER BY <alias of record::id(id)>  ==  ORDER BY id           -> SAME ORDER: True (mixed 0a/M1/_x/aa/m10/m9/zz)
LIMIT $param                                                   -> legal, 7 rows
```

**F2's probe, with a working positive control** (this is the leg that makes the "no live impact"
claim a measurement rather than an opinion): I emitted the real `generate_floor_calibration_ddl()`
with the `revision` field line removed (an "older deployment"), created a `scope`-only `floor_head`
row, then applied the real DDL.

```
legacy row after migration : {'id': floor_head:legacy, 'scope': 'pooled'}   revision key present? False
production mint on legacy row (UPSERT … revision = (revision ?? 0) + 1): OK, revision = 1
POSITIVE CONTROL (add a required `brand_new string`, then UPDATE the same legacy row):
    RAISED -> Couldn't coerce value for field `brand_new` of `floor_head:legacy3`:
              Expected `string` but found `NONE`
```

The control **fires**, so the probe can see §1.4 poisoning; it did not fire for `revision` because
every production write to `floor_head` is the mint, which sets it. F2 is a prose defect, not a
behavioural one — today.

## 5. Routing is not sharing — MUTATION PROOF

**Declared BEFORE the run**, taken from `pytest --collect-only -q` (collecting names tests without
running them, so the set was fixed before any result existed). Mutation:
`_RETRYABLE_CONFLICT_MARKER = "can be retried"` → `"ZZ-COLDAUDIT-11IA-MARKER-MOVED-ZZ"` in
`store/_txn.py`, via `scripts/mutation_proof.py` in the provenance-asserted scratch copy.

**Observed RED set == declared set, exactly 6/6:**

```
FAILED …TestEverySingleStatementSeamRetriesAConflict::test_a_retryable_conflict_is_retried_and_the_statement_succeeds[FloorCalibrationStore]
FAILED …                                             ::test_a_retryable_conflict_is_retried_and_the_statement_succeeds[SurrealLeaseStore]
FAILED …                                             ::test_sustained_conflict_raises_the_TYPED_error_not_a_bare_store_error[FloorCalibrationStore]
FAILED …                                             ::test_sustained_conflict_raises_the_TYPED_error_not_a_bare_store_error[SurrealLeaseStore]
FAILED …                                             ::test_the_seam_backs_off_through_the_SHARED_jitter[FloorCalibrationStore]
FAILED …                                             ::test_the_seam_backs_off_through_the_SHARED_jitter[SurrealLeaseStore]
6 failed, 10 passed, 88 deselected in 1.94s
tree restored byte-exact (loremaster/loremaster/store/_txn.py: md5 cbac5286186c96955860fd233906f135)
```

**Differently-broken control:** the **10** `test_a_non_conflict_rejection_is_raised_immediately_with_zero_retries[…]`
params (assert-violation · field-coercion · parse-error · transport-not-allowed · sdk-KeyError-routing-drop,
× both new seams) stayed **GREEN** — they are rejected for a *different* reason and the mutation
correctly does not touch them. **Positive control:** the same 16 on the unmutated copy → `16 passed`.

⚠ **Honest note on the instrument:** `mutation_proof.py` exited **4**, reporting two "unexpected reds"
that are not node ids at all — `loremaster.floor_calibration.store:_txn.py:1199 floor_calibration.query.rejected`
and its lease twin. Those are **`Captured log call` lines beginning with `ERROR `**, i.e. the tool's own
documented bound ("a line of a test's own captured output beginning with `FAILED ` is
indistinguishable from a summary line" — the same hole one keyword wider). I adjudicated it from the
`short test summary info` block, which matched my declared set exactly. **This is a real, small gap in
a committed instrument** — logged as residual R8.

Structural corroboration, independent of the mutation: a bare grep over the three new/changed
domain files finds **no** private retry loop, no private backoff, no private jitter, and no engine-text
match. Both new classes route `_query` → `_txn.run_query`, multi-statement work →
`_txn.execute_transaction` (which supplies the `BEGIN … COMMIT` envelope via `compose`), and session
setup → `_txn.bootstrap_session`.

**And the enumeration genuinely reaches them.** The AST scan discovers **13** classes owning an
`async def _query` (I re-derived the list with the pin's own logic); both new classes are in it, and
`observed.keys() == _SEAM_REJECTION_EVENTS.keys()` is an exact-set assertion **both ways**, so a seam
reshaped *out* of the enumeration reddens. `_MIN_KNOWN_SEAMS = 10` is a redundant vacuity floor, not
the discriminator — see R1.

## 6. #241 — I did **not** close it, and I did not combine populations

I read `FINDING-241-hunt-notes.md` before forming a view and I accept its central point: hunt #2's 30
greens describe a tree that is **not** the tree that failed.

**My own run is a THIRD population and I state it as such** — I do not combine it with the lead's 30
or the builder's 112/114. Ten frozen iterations of the four contract files on `acd2b61`, freeze
re-verified before and after every one:

```
run 1..10: 210 passed (11.72s – 13.85s)
           head=acd2b61…→acd2b61…  dirt=d41d8cd9…→d41d8cd9…   (all 10)
10 / 10 green.
```

**What I add is a mechanism, not a reproduction.** The shared budget, read out of `_txn.py`, is
`_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS = 2.0` · `_MAX_TXN_CONFLICT_ATTEMPTS = 5` (floor) ·
`_TXN_CONFLICT_ATTEMPT_CEILING = 64` · backoff base 0.005 s, cap 0.1 s. `record_measurement` passes
**no** deadline override, so the 32-way mint pin drives **32 × `_ADOPTIONS_PER_RACER`** transactions
fully serialised on ONE hot row, with **no test-level retry**, under that 2.0 s wall-clock deadline.
That is a concrete, checkable form of the notes' untested hypothesis (c), and it fits the observed
signature far better than a correctness defect: a **store-wide** slowdown (exactly the
post-full-suite window the original failure's timing fitted) pushes *many* live-store tests past the
*same shared* deadline at once, which is why 28 failed together rather than one.

**This is a hypothesis. I did not reproduce it and I am not asserting it.** The named instrument is
the one the notes already identify — count exhaustions at the driver — plus one cheaper leg: measure
the 32-way pin's wall-clock **headroom** against 2.0 s under load. If the lead's disposition is a
PINNED KNOWN BOUND, that headroom number belongs in the pin.

## 7. RESIDUALS — read this table, not just the summary

| # | item | why it matters |
|---|---|---|
| **R1** | `_MIN_KNOWN_SEAMS = 10` vs **13** discovered. Set at `9d29111`, never raised; margin grew 1 → 3 this packet. | Largely mitigated by the exact-set keys pin (§5), so **not** a defect — but the floor's own failure message tells you to *"lower this floor deliberately, in a diff a reviewer can see"*, and nobody has *raised* it in two population growths. Cheap fix: `= 13`. |
| **R2** | **The slice has ZERO production consumers.** Nothing outside the two new modules + tests constructs `FloorCalibrationStore` / `SurrealLeaseStore` / `SurrealLeaderLock`, or calls `enumerate_calibration_pool` / `head_identity` / `corpus_content_digest` / `lease_election_config`. Neither `ensure_ready()` is on any boot path. | Expected under `DEPLOY: no` — but it means store ref §5's *"every table production code writes to must be declared before first write"* is satisfied only **vacuously**. **11-ii's brief must carry this**: wiring a writer without wiring the slice's own `ensure_ready` gives an undeclared-table conflict storm (§5/#144) and, for `lease`, an undeclared-table **READ that RAISES** on 3.2.1 (ruling O3's own measurement). |
| **R3** | **`docs/plans/v2/receipts/2026-07-26-packet11i-build/RULINGS-2026-07-26-adversary.md` contains 2 literal NUL bytes** (in O1's `"pooled\x00statistic\x00forged"` example). Independently verified: `file` says `data`; `grep -rn "OPERATOR RULING" <dir>/` → **0 lines**; `grep -arn` → 1. | This repo's rename/consistency law is **entirely grep-based**, and the packet's own binding ruling record (O1–O7) is invisible to any sweep that omits `-a`. Recommend escaping the NULs as text. Operator's call. |
| **R4** | `record_measurement`'s public `Raises:` says *"an adopted row carrying one [a cause]"*. `_validate_domain` branches on **`state`**, never on `adopt`: it raises for a cause on any state ≠ `measured_not_adopted` (incl. `adopt=False`), and does **not** raise for `adopt=True` + `measured_not_adopted` + a cause. The private helper's docstring is correct; the public one — the consumer-facing surface — is not. |
| **R5** | `CALIBRATION_POOL_COLUMNS`' block comment still claims the projection carries *"the stratification/hold-out/self-retrieval keys, and the probe-derivable text"*. The tuple is `("point_id","content_hash")`. The builder **appended** a correcting ⚠ paragraph instead of fixing the false sentence; two adjacent paragraphs now contradict. |
| **R6** | Bare `REPORT-builder-11ia-1.md` citation inside `enumerate_calibration_pool`'s limit-margin comment — the address form this repo forbids (#152/#153). The report **is** tracked, so it is a one-string fix to the `docs/plans/v2/receipts/2026-07-26-packet11i-build/…` path. |
| **R7** | `_minted_head_revision`'s error says *"committed without a minted head revision"*; the same branch also fires when the **row is absent entirely**. The docstring names both fates; the served message names one. |
| **R8** | `scripts/mutation_proof.py` mis-parses a `Captured log call` line beginning with `ERROR ` as a summary ERROR node id (§5). Its docstring anticipates the `FAILED ` case only. Failure direction is **loud and wrong**, never silent — but it cost me an adjudication step and will cost the next agent one. |
| **R9** | `_CALIBRATION_POOL_ORDER_COLUMN`'s comment justifies alias-ordering by *"the table prefix is constant"*. That covers the prefix, not the fact that a RecordID orders by its **typed** `Id`. The conclusion holds for `chunk` (its `point_id` is a UUID5 string) and **I probed the two orders equal** — but the stated reason is not the reason it is true. |
| **R10** | `lease_election_config`'s docstring says `Config` *"silently substitutes its own **no-op** `onstopped_leading`"*. The substitute logs at INFO. Operational conclusion unaffected. Also: `except (SurrealStoreError, concurrent.futures.TimeoutError, TimeoutError)` — the last two are the **same class** on Python ≥3.11 (harmless redundancy, ×4 sites). |
| **R11** | `record_measurement`'s inline comment cites *"the **stub's** own warning"* for text that lives in `FenceLostError`'s class docstring — which was never a stub and still exists. Pointer to a category that no longer exists. |
| **R12** | `scripts/contention_hunt.sh` — **two flaws in the instrument the packet is about to lean on for #241's disposition.** (a) the failure detector is `grep -qE "^[0-9]+ failed\|error"`; the `error` alternative is **unanchored**, so the substring "error" anywhere in a `--tb=long` capture marks the run FAILED (errs toward over-reporting, so it *strengthens* the 0/30 — but it is a false-positive-prone gate). (b) the **collected count — the loop's own headline "checked variable"** — is derived by summing every `N passed`/`N failed` regex match in the output file, **not** from `--collect-only`; a traceback containing such a string corrupts it. Both matter if this script becomes the pinned instrument attached to a KNOWN BOUND. |
| **R13** | `LeaseError`'s new docstring contains the literal text `except LeaseError`, so a future bare grep for an `except` site now gets a **prose hit in the very file** the "no except site anywhere" receipt was written about. Harmless today; it is the retired-name-sweep trap pointed the other way. |

## 8. What I checked and found clean (so the absence is a result, not a gap)

- **No `STUB` / `NotImplementedError` / `packet 11-i-a:` placeholder survives in any of the five
  production files** (bare, anchor-free grep). The four other banners were correctly rewritten;
  `surreal.py`'s is F4.
- Bare, anchor-free sweep for the retired F4.1 state name across `loremaster/loremaster/` → **0 hits**.
- `_validate_domain` runs **before** any I/O (a build that wrote then raised would corrupt the
  append-only history) ✓. `note` mandatory unless `measured`, cause only on `measured_not_adopted` ✓
  (ruling E5).
- The fence guard is **inside** the commit transaction (`LET $fc_fence_held = SELECT …` + `THROW`),
  not a read-then-write pre-check (adversary W2) ✓; `_FENCE_REFUSAL_TEXT` carries no
  `BEGIN`/`COMMIT` word and no quote, so `compose`'s envelope check cannot reject it ✓.
- `_fence_verdict` classifies from **store state**, never from message text, and pins all three
  fates including *"the confirming read could not complete → re-raise the original untouched"*
  (E2's rider + M5) ✓. `SurrealConnectionError` / `TxnContentionExhaustedError` propagate **untouched**
  and are never re-dressed as a fence verdict ✓.
- `enumerate_calibration_pool` compares against `SurrealStore.count()`, which counts the **same**
  `CHUNK_TABLE` it scrolls ✓; the empty-corpus and N=1 cases were reasoned through and neither
  mis-fires ✓; the `limit = count + 1` margin's exactly-one-growth trade is disclosed in the comment
  (though not in the raised message — see R5's neighbour, logged by the sweep as a NIT).
- Contention pins are at **8 / 16 / 32-way** on separate live connections with overlapping racer
  lifetimes, and the invariants **discriminate** (head mint: `sorted(observed) == range(1, N+1)` —
  a lost update reads LOW, a double-apply HIGH; lease CAS: `final.revision == created.revision + N×3`
  plus *"the fence moved while the holder never changed"*). `test_exactly_one_racer_wins_the_FIRST_EVER_create`
  pins the guarded-CREATE atomicity claim at 8-way, and a genuine (non-duplicate) rejection would
  propagate out of the `gather` rather than be counted as a lost race ✓.
- In-suite mutation proofs exist and are real: monkeypatching `surreal_schema._define_field` must
  move both slices' DDL; monkeypatching `FLOOR_STATES` / `FLOOR_NON_ADOPTION_CAUSES` must move the
  emitted `ASSERT`. These make the derivations provable rather than readable ✓.
- The store-reference correction at `7b79a03` (§8's retired #102 claim) is accurate against §5 and
  against `CLAUDE.md`'s measured `-n auto` numbers ✓.

## 8b. Numbers I re-derived rather than relayed (the lead's ask #6 — including the lead's own)

| claim | source | my re-derivation | verdict |
|---|---|---|---|
| harness docstring: **39** test files import `_surreal_harness` | `_surreal_harness.py` module docstring, corrected 36→39 by the closure wave | ran the pin's OWN helper: `test_surreal_harness._harness_importer_files()` → **39** | **VERIFIED** — and the lead's grep-derived *"43"* was indeed wrong, because the helper counts `ast.Import`/`ast.ImportFrom` of the module, which a grep cannot scope |
| harness docstring: **24** test files call `connect_admin` | same | `test_surreal_harness._connect_admin_caller_files()` → **24** | **VERIFIED** |
| `test_retry_seam` prose: **ten** seams, *"five plain / five domain-naming"* | 6 sites incl. a served assert message | derived from the pin's own dicts: **13 / 13**, **5** plain, **8** domain-naming | **WRONG** → F1 |
| `_SEAM_REJECTION_EVENTS` population over time | — | `9d29111`: **10** · `71ead8c`: **13** · `acd2b61`: **13** | drift **pre-dates** this packet; the packet added the two *entries*, not the staleness |
| discovered `_query` seams | `_MIN_KNOWN_SEAMS = 10` | AST scan with the pin's own logic → **13** | floor never raised (R1) |
| **#242: "twelve copies of the connection glue … all twelve owners out of the AST enumeration that covers them"** | `REPORT-builder-11ia-1.md` E-4 (×3), commit `7acbef4` body, `REPORT-closure-11ia-1.md` §7.5 | I derived **four** populations: the pin's OWN enumerator `_discover_socket_owners()` (a class whose `_ensure_connection` *constructs* `AsyncSurreal`) → **13** at `acd2b61`, **11** at `71ead8c`; classes merely *defining* `_ensure_connection` → **14** / **12**; `_MIN_KNOWN_SOCKET_OWNERS` (a **floor**, not a count) → **10** | **SCOPING-AMBIGUOUS, and the sentence conflates two populations.** "Twelve" is right for exactly one reading — `_ensure_connection` definers *before* the builder's own two landed — and wrong for every other, including the tree the commit shipped (14). Worse, the clause *"all twelve owners out of the AST enumeration that covers them"* is false under **every** scoping: the enumeration covers **11** then, **13** now, never 12, because it deliberately excludes `CommandSubscriber` (scout receives its connection). ⚠ This is the #102/#120 two-populations shape inside the finding that documents duplication — and the closure **relayed** the builder's number instead of re-deriving it. ⚠ My own first pass reached a *different* wrong verdict by picking the definer population; that is the point. **State the enumerator's number, at a named commit, or state both with their definitions.** |
| closure §2.4's docs-sweep receipt: `grep -rn 'head_identity' docs/ \| grep -iE 'option\|nullable\|required'` → **"no hits"** | `REPORT-closure-11ia-1.md` §2.4 | `git grep` at the closure's own spawn HEAD `7b79a03` → **4 hits** (one in `REPORT-adversary-11ia-1.md`, three in `REPORT-contract-11ia-1.md`); at `acd2b61` → **14** | **FALSE AS WRITTEN.** The **substance survives** — restricted to live `docs/design` + `docs/reference` the count is **0**, which is what the sweep was for. But the receipt is the false-no-hits-gate shape this repo names, in a wave whose own headline catch was a probe passing for the wrong reason. |
| builder §6's transcribed gate command | `REPORT-builder-11ia-1.md` §6 | ran it verbatim from the repo root: **`no tests ran in 3.59s`, exit 0** | **NOT REPRODUCIBLE AS TRANSCRIBED** (brace expansion without the `loremaster/tests/` prefix). The number **196** is independently correct — but the receipt is the silent-green shape `CLAUDE.md` warns about. The closure's §5 command uses full paths and is fine. |
| hunt #1: *"3 of 30 runs failed … 24 collected 196, one collected 197, two died in collection"* | `FINDING-241-hunt-notes.md`, commit `a98f626` | 24 + 1 + 2 = **27**, not 30 | **DOES NOT SUM** — three runs unaccounted for in both texts. Hunt #1's raw output was never committed (only hunt #2's timeline), so it is **not re-derivable**. Hunt #1 is already declared INVALID, so nothing rests on it; flagged so nobody later mines it for a number. |
| the lead's grep, *"43 where the pin's own helper said 39"* | brief + closure §3 | `grep -rl "_surreal_harness" loremaster/tests/*.py \| wc -l` → **43** ✓; the analogous `connect_admin` grep → **25**, not the quoted 23 | the **point** stands exactly (a grep cannot see what the AST helper scopes); one of the two quoted grep figures does not reproduce |

## 9. Method notes (so a reader can redo this)

- Gates: `uv run --no-sync pytest -n auto -q …`, `./scripts/typecheck.sh`, `uv run --no-sync ruff check .`
  — each run unpiped, with the passed-COUNT read off the real tail (no `| tail` under `set -e`).
- Mutation proof: `./scripts/mutation_proof.py --file … --anchor … --replacement … --expect-red ×6 -- …`,
  declared set from `--collect-only`, in a `scripts/scratch_copy.sh` tree with printed provenance.
- Contention: a 10-iteration loop capturing `git rev-parse HEAD` and `git status --porcelain | md5sum`
  before **and** after every run (the detector hunt #1 lacked).
- Two fan-out agents ran the numeric re-derivation and the served-English sweep; every finding of
  theirs that appears above I re-derived or re-probed **myself** before reporting it (the NUL bytes,
  the `_PREIMAGE_OPTIONS` bypass, the socket-owner counts at two commits, the `revision`
  optionality, the closure's docs-sweep receipt, the builder's non-reproducing gate command).
- **Housekeeping the lead must decide:** the scratch copy at `/home/ejprice/scratch-ca11ia` is
  **still on disk** — my `rm -rf` was refused by the sandbox and I did not retry. It is a plain
  directory (not a git worktree; its 71-byte `.git` pointer is renamed to `.git-DISABLED-by-coldaudit`),
  it lives OUTSIDE the repo, and `_txn.py` in it was restored byte-exact (md5 `cbac5286…`). Delete it
  or keep it to re-run the mutation proof — the proof is one command either way (§9, bullet 2).

---

*Measured 2026-07-26 at `acd2b617d70fc6b795146e46cf4a4be0d0607e38`, worktree `lore-pkt11ia`,
branch `pkt11-i-a-floor-machinery`, SurrealDB 3.2.1 test store `ws://127.0.0.1:18000`.*
