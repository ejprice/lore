# REPORT-builder-11ia-1 — packet 11-i-a, the production build

brief-base v7 read

**provenance (#140):** `loremaster.__file__` =
`/home/ejprice/PycharmProjects/lore-pkt11ia/loremaster/loremaster/__init__.py` — I made NO
scratch copy: every gate, probe and mutation receipt below ran against **this worktree**
(`/home/ejprice/PycharmProjects/lore-pkt11ia`, branch `pkt11-i-a-floor-machinery`, base HEAD
`71ead8c`), and the four mutation-receipt legs that perturb module state do so **in-process**, restoring
and re-asserting byte-exactness of the generated text rather than editing a file.
**I ran no git write command of any kind.**

---

## SUMMARY BLOCK

- **state:** done-with-deviations — the contract is GREEN; one pre-existing full-suite failure and
  one intermittent concurrency failure are ESCALATED, not waived.
- **gates, measured 2026-07-26 on the FINAL tree (base `71ead8c` + my 5 files):**
  - contract (4 files): **196 passed** in 11.4s. (`196`, not the fix-wave report's `186`:
    contract commit `2f22314` landed AFTER that report. Derived, not assumed: it ADDS 12 test defs
    and REMOVES 2 (the quarantine pins it deleted) = **net +10**, and `f052c6d` adds none.
    186 + 10 = 196.)
  - `test_retry_seam.py`: **561 passed** — exactly the number ruling O2/B1 predicted.
  - full suite: **1 failed, 7544 passed, 17 skipped, 3 xfailed** in 198.24s — and the SAME result
    line on all four runs of it this session. The one failure is **PRE-EXISTING and not mine** — a
    stale derived count in the test harness's own docstring, see **E-2**.
  - `./scripts/typecheck.sh`: `Success: no issues found in 162 source files` (loremaster) + lorescribe
    + loresigil OK. `uv run --no-sync ruff check .`: `All checks passed!`
  - concurrency repeats: **112 of 114** 4-file contract runs green, **including one uninterrupted
    run of 20 consecutive greens** (which discharges the contract's literal obligation), plus 60/60
    green on the contention classes alone and 16/16 under DOUBLED load. **2 failures, at runs 8–9 of
    the very first loop, which I could not reproduce in 94 subsequent runs across five designed
    conditions.** A failing concurrency test is a STOP: it is ESCALATED as **E-3** with everything I
    measured, including my own instrument failure. I am NOT calling it flaky.
- **deviations:**
  1. `head_identity` on `floor_measurement` ships **`option<string>`**, not the REQUIRED column
     ruling **O7** ordered — the frozen contract's own migration fixture creates a measurement row
     without it, so a required column reddens a pin I may not edit (**E-1**, with the exact fixture
     edit). The ledger enforces the ruling at its own layer.
  2. `measurement_history` returns an **explicit projection**, not raw `SELECT *` rows — which
     retires the carried `KeyError` residual rather than inheriting it (§2.8).
  3. I rewrote the five files' **"STUB"** banners into accurate prose. Leaving "STUB SURFACE …
     every NotImplementedError is a hole the builder fills" above shipped code is the
     stale-served-English defect class this repo instruments; no pin keys on that text (checked).
- **Packages considered:** §5 — 9 rows, each with what I READ. `orjson` → replace (O1) ·
  `kubernetes.leaderelection` → replace_with_adapter · `_txn.retry_on_conflict`/`run_query`/
  `execute_transaction`/`bootstrap_session` → keep_with_trigger (#111) · `surreal_schema._define_*`
  → replace · `records.sha512_hex` → replace · stdlib `json` → replace · `types.MappingProxyType`
  → replace · `uuid4` → replace · native `DEFINE SEQUENCE` for the head revision → **bespoke**
  (the counter-row UPSERT: sequences are documented NOT gapless and the slice's own pin forbids one).
- **decisions-needed (all in §4):** **E-1** O7 vs the frozen fixture · **E-2** the pre-existing
  harness-docstring failure · **E-3** the 2-in-114 contention failure · **E-4** copies #11/#12 of
  the connect/bootstrap boilerplate (a DESIGN question, with the trap that kills the naive fix) ·
  **E-5** `LeaseError` is declared by the frozen interface and raised by nothing · **E-6** store
  reference §8 teaches a retired claim about the retry budget · **E-7** two derivations I introduced
  have mutation RECEIPTS but no PIN.
- **receipt pointers:** what I built §1 · design decisions the contract left open §2 · the live
  probes and what they add to the store reference §3 · escalations §4 · packages §5 · gate tails §6
  · the concurrency repeats §7 · lore-vs-grep §8.

---

## 1. WHAT I BUILT

Five files, all inside the brief's writable set. Nothing else was touched.

| file | what landed |
|---|---|
| `store/surreal_schema.py` | `FLOOR_STATES` (8) · `FLOOR_NON_ADOPTION_CAUSES` (5) · `FLOOR_MEASUREMENT_COLUMNS` + the column-name constants · `_floor_measurement_statements` / `_floor_head_statements` / `_lease_statements` · `generate_floor_calibration_ddl` / `generate_lease_ddl` |
| `floor_calibration/domain.py` | the axis registry (`("scope","statistic")` + `MappingProxyType({"query_shape":"any"})`) · the 30/15/30 floors + `corpus_meets_validity_floors` · `head_identity` + `_serialised_axes` · `corpus_content_digest` |
| `floor_calibration/store.py` | the conventional seam (`_ensure_connection`/`_drop_connection`/`_query`/`close`) · `ensure_ready` · `record_measurement` (one transaction: fence guard → head mint → measurement CREATE) · `read_adopted_head` · `measurement_history` · `_validate_domain` · `_fence_verdict` |
| `store/lease.py` | the seam + `read`/`create_if_absent`/`compare_and_set`/`release_if_held` · `SurrealLeaderLock`'s six library members + `fence_epoch`/`release_if_held`/`stop` · `lease_election_config` |
| `store/surreal.py` | `CALIBRATION_POOL_COLUMNS` + the derived projection · `enumerate_calibration_pool` |

**The shapes that were forced, not chosen** (each is why a pin is green):

- **The fenced commit is ONE transaction** — guard `SELECT` bound to `(holder, fence_epoch)`, then a
  `THROW` that aborts it, then the head mint, then the measurement `CREATE`. R10.2's guard is
  *inside* the commit; there is no read-then-write pre-check anywhere (adversary W2).
- **The lost-fence verdict is read from store STATE** (`_fence_verdict`), never from engine text
  (E2/F8-C6; receipts #118/#111). Three fates, all forced by a fixture in the contract: moved →
  `FenceLostError from error`; intact → the original, re-raised **bare** so its own cause chain and
  traceback survive; confirming read cannot complete → the original, plus a loud
  `floor_calibration.fence.unconfirmable` log line.
- **The head revision is minted store-side and read back off the MEASUREMENT row**, not off the head
  row. The head is hot: a racer can advance it between the commit and any re-read, and two adopting
  runs would then report the same revision — which is exactly what the contention pin's "N distinct
  consecutive revisions" invariant catches. The `LET $rev = (UPSERT … RETURN AFTER)[0].revision`
  → `CREATE … object::extend($payload, {head_revision: $rev})` shape is `findings.py`'s own mint
  pattern, one statement longer.
- **`create_if_absent` needs no engine-text match** to tell a duplicate from a real rejection: the
  existence test is a guard *inside* the statement (`IF array::len((SELECT VALUE id FROM …)) = 0
  { CREATE … }`), so an already-present row is an EMPTY RESULT (a value) while any genuine rejection
  still raises. That is what makes M10 satisfiable under F8-C6.
- **The CAS is one round-trip** and both counters are minted store-side in the same `UPDATE`
  (`fence_epoch = fence_epoch + (IF holder_identity = $holder {0} ELSE {1})`).

---

## 2. THE DESIGN DECISIONS THE CONTRACT LEFT OPEN

Each one names the alternative reading, per scope law — including the ones I felt no doubt about.

1. **`head_identity` column optionality** — see **E-1**. Readings: (a) O7 literally (required column,
   fixture edited); (b) ship `option<>` + ledger-level enforcement and escalate. I shipped (b)
   because (a) reddens a frozen pin.
2. **`floor_head`'s axis columns are `option<string>`, derived from the registry.** The M14 head leg
   creates a `scope`-only row, so every other column must tolerate absence (§1.4 says a required NEW
   field on a possibly-populated table poisons every existing row and a `DEFAULT` does not rescue
   it). Derivation: `_floor_head_statements` imports `FLOOR_HEAD_ALWAYS_SERIALISED_AXES` **inside the
   function** so `surreal_schema` stays an import-time leaf. Alternative: mirror the tuple as a
   second constant in `surreal_schema` and rely on a SCHEMAFULL write failing loudly if they drift —
   rejected as ONE-IMPLEMENTATION's copy #2. Mutation receipt: §7 leg 1/leg 4.
3. **The head's `statistic` column is `option<>` for the same fixture reason** — worth stating
   because it is exactly O7's shape one table over: a fixture's convenience relaxing a column that
   is never legitimately absent. The `axes` object is the authority for the mapping, the id is a pure
   function of it, and the ledger always writes both.
4. **A cause on ANY state other than `measured_not_adopted` is refused.** The stub's `Raises` clause
   says "an adopted row carrying one" (narrower — only `adopt=True`); ruling E5 says the cause
   "appears **only** on `measured_not_adopted`" (wider). I implemented E5's reading. Under the narrow
   reading a `measuring` row could carry a non-adoption cause, which is the projection E5 forbids.
5. **`note` must be non-blank, not merely present.** §7 says "mandatory unless `measured`"; a
   whitespace-only note satisfies "present" and names nothing. Precedent: `command.kind`'s
   trim-aware ASSERT. Unpinned either way.
6. **`adopt=True` on a non-`measured` state is NOT refused.** The design implies adoption only
   happens on `measured`, but the contract's `Raises` enumeration does not include it and no pin
   forces it; adding an unpinned refusal risks a false gate for 11-i-b's runner. Flagged, not built.
7. **`measurement_history` refuses `limit < 1`** (`ValueError`). Unpinned addition; the alternative
   is to pass it through, where `LIMIT 0` reads as an empty history and a caller bug becomes "no
   measurements".
8. **`measurement_history` returns an EXPLICIT projection** (`FLOOR_MEASUREMENT_COLUMNS` +
   `record::id(id) AS measurement_id`), not raw `SELECT *` rows. This retires the fix-wave's carried
   residual 2 ("`SELECT *` OMITS a `NONE`-valued column, so every `option<>` column raises
   `KeyError` for a reader") instead of handing it to 11-i-b: under an explicit projection an unset
   column reads `None`. It also forced `created_at` into the projection, because `ORDER BY` a column
   absent from an explicit selection is a PARSE ERROR (§7; re-probed 2026-07-26). Nothing pins the
   raw-row shape, so this is a free trust win — but it IS a shape change from what that residual
   describes, so 11-i-b's brief should carry the *new* fact, not the old hazard.
9. **`CALIBRATION_POOL_COLUMNS` ships as `("point_id", "content_hash")`** — the C10 digest inputs and
   nothing else, per E6 ("membership beyond … is 11-i-b's to fix"). The projection is DERIVED from
   the constant, so 11-i-b extends one tuple. Note the stub's prose also mentions
   stratification/hold-out keys and probe text; those are 11-i-b's columns by that ruling.
10. **The pool's issued limit is `counted_total + 1`.** ⚠ **A DISCLOSED TRADE, not a tuned number.**
    With margin 1, a corpus that GREW between the count and the walk returns exactly `limit` rows and
    is reported as a **truncation** (`measurement_failed`) rather than as the gentler **count
    mismatch** (discard-requeue). A margin of *m* routes growth `< m` to the mismatch branch — which
    is F8-C8's own preference for "the corpus moved" — but the contract's truncation fixture
    (count monkeypatched to 5 against 12 real rows) bounds *m* ≤ 7, so any larger margin is fitted to
    a fixture rather than derived. I took the contract's literal wording ("a limit STRICTLY GREATER
    than that count"). **If the lead wants growth classified as a mismatch, that is a ruling plus a
    fixture change, not a builder tweak.**
11. **`SurrealLeaderLock.get` returns `(True, record)` for a row whose holder is NONE.** Required for
    decision 23: the algorithm's own next branch (any of the four fields `None` → `update_lock`) is
    what makes a released lease immediately acquirable. Reporting it ABSENT would send the candidate
    down the create path against a row that exists, and nobody would ever acquire it.
12. **A store failure inside the lock is reported through the LIBRARY's own failure channel, loudly
    logged** — `get` returns a **non-404** `LockAbsent` (the algorithm logs "Error retrieving resource
    lock" and returns `False` *without* creating), `create`/`update`/`release_if_held` return
    `False`. Raising instead would kill the election thread for the process's lifetime; the library's
    `retry_period` loop is the retry, so no private retry is introduced. Every swallow emits
    `lease.lock.{read,create,update,release}_failed`. Unpinned; the alternative (propagate) is
    strictly worse for liveness and equally unpinned.
13. **`update` with no observed revision returns `False`.** A lock that never did a `get` holds no
    CAS token; the contract's `test_the_adapters_fence_epoch_tracks_a_RENEW_and_a_SEIZE` explicitly
    accepts `True` or `False` there.
14. **`release_if_held` bumps `revision` but not `fence_epoch`.** Every successful write advances the
    optimistic token; releasing is not a holder CHANGE, so the next acquirer's own CAS is what bumps
    the fence (which is what the contract's `created.fence_epoch + 1` assertion after a
    release-then-seize requires).
15. **`_query`'s `label`/`noun` are module constants**, not literals at the call site, and they carry
    the O2-frozen values.

---

## 3. THE LIVE PROBES — and what they ADD to the store reference

**Order of authority, per CLAUDE.md: I read `docs/reference/surrealdb-31-capabilities.md` IN FULL
FIRST**, then probed to confirm it and to find what it omits. What it decided for me, cited not
re-transcribed: §1.1 (the clause rule — TABLE/INDEX `IF NOT EXISTS`, FIELD `OVERWRITE`), §1.3 (no
`ALTER`), §1.4 (a NEW field on a possibly-populated table is `option<>`; a `DEFAULT` does not rescue
it), §1.6 (the virgin-DB blind spot), §2 (`CONTENT` for protected-key writes; `object::extend` as the
only bound-payload-plus-computed shape; `SELECT *` omits a NONE column; `str(RecordID)`), §3
(`query()` validates statement[0] only → `execute_transaction` for all multi-statement DDL), §5 (the
hot-row mint law; sequences are NOT gapless), §7 (FLEXIBLE is trailing; the `ORDER BY` idiom rule;
a bare ASSERT on an `option<>` field).

**Six facts my probes establish that the reference does not carry.** Two of them changed the code;
all of them are cheap to re-run (`/tmp` probe scripts are unrecoverable by construction, so the
statements are quoted here rather than cited by path):

| # | probed 2026-07-26, spike-surreal 3.2.1 | result | why it mattered |
|---|---|---|---|
| P1 | `UPDATE l:s SET holder = $h, fence = fence + (IF holder = $h {0} ELSE {1}), …` — the holder clause placed **FIRST** | the fence STILL bumped (0→1→2 across holders) | **every `SET` right-hand side evaluates against the row's BEFORE state, regardless of clause order.** The CAS's conditional fence bump is correct in one statement; a build that "fixed" a non-existent ordering hazard by re-reading would have cost the one-round-trip pin |
| P2 | `SELECT … LIMIT $limit` | OK | the pool and the history bind their limits |
| P3 | `SELECT record::id(id) AS point_id, … ORDER BY point_id` vs `ORDER BY id` | alias OK; `id` → **parse error** *"Missing order idiom `id` in statement selection"* | §7's rule bites the C8 walk; ordering by the projected alias is the same order (the table prefix is constant) |
| P4 | `IF array::len((SELECT VALUE id FROM type::record('lease',$id))) = 0 { CREATE … }` | absent → the created row; present → `None` | a create-if-absent with **no engine-text match** (M10 under F8-C6) |
| P5 | `THROW 'x'` inside `BEGIN…COMMIT` via `query_raw` | `stmt[1]=ERR "was not executed due to"` (cascade), `stmt[2]=ERR "An error occurred: x"`, `stmt[3]` cancelled-cascade, `stmt[4]` COMMIT-aborted; the guarded CREATE **rolled back** | the fence guard aborts the transaction, and `_txn._domain_root_cause`'s first-non-cascade selector picks the THROWN text — so `execute_transaction` raises `SurrealStoreError`, which is what `_fence_verdict` classifies |
| P6 | `object::extend($caller, {k:'computed'})` where the caller also has `k` | `{'k': 'computed', …}` | **the second object WINS** — a caller cannot forge `head_identity` |
| P7 | `record::id(measurement)` where the column is NONE | **RAISES** *"Expected `record` but found `NONE`"* | an un-adopted head is a legitimate state, so the head read projects the raw link and coerces in Python (`_bare_record_id`) |
| P8 | `SELECT … FROM type::record('nope','x')` | **RAISES** `NotFoundError` | confirms ruling O3's premise on 3.2.1: it is why M5's third fate exists |
| P9 | `EXPLAIN` of the history read | `IndexScan` on `floor_measurement_head_created`, `direction: Backward`, `limit` pushed down | the composite `(head_identity, created_at)` index earns its keep; the newest-first read is not a table scan |

⚠ **A doc-worthy consequence of P1 and P6**, for whoever holds docs rights: the store reference has no
`SET`-evaluation-order row and no `object::extend` precedence row, and both are the kind of fact a
careful engineer would otherwise derive by guessing. Same for P7 (`record::id(NONE)`).

---

## 4. ESCALATIONS

### E-1 — ruling O7 cannot be implemented against the frozen contract. [BLOCKING A RULING, not the build]

O7 rules: *"`head_identity` is a REQUIRED column on every `floor_measurement` row, **and the
migration fixture supplies it**."* The fixture does **not** supply it. At HEAD (`2f22314`, which is
LATER than the Q3 ruling commit `3f33944`), `test_floor_calibration_schema.py`'s
`TestTheSchemaMigratesAnEXISTINGStore` still writes:

```
CREATE type::record('floor_measurement', 'legacy') CONTENT { state: 'measured' }
```

With `head_identity TYPE string` (no `option`, no `DEFAULT`) that CREATE fails — the pin goes RED and
I may not edit it. There is no third shape: an ASSERT on an `option<>` field is not evaluated when the
value is NONE (§7), and a `DEFAULT` would fabricate an identity, which is the opposite of the
ruling's intent.

**What I shipped:** `option<string>`, plus enforcement at the layer that CAN hold it —
`record_measurement` DERIVES `head_identity` from the axes on every write (never from the payload;
`object::extend`'s precedence, P6, means a caller cannot even override it), so **no lore-written row
can lack it.** Only a raw writer can — which is exactly the gap the store ASSERT was meant to
backstop. The schema docstring carries this in full so the next reader meets the bound deliberately.

**The edit that closes it (yours, or a contract author's):** add `head_identity: 'legacy_head'` (any
string) to that fixture's CONTENT, then flip the column to `string` in
`surreal_schema._floor_measurement_statements`. It is two lines. **I recommend doing it** — the
ruling's argument (an unattributable row in an append-only table is permanent) is sound, and the
migration pin's ∀ reach over OPTIONAL columns is untouched by supplying the one column that was never
optional.

### E-2 — the full suite's ONE failure is pre-existing and is a stale count in the harness's own docstring

```
FAILED loremaster/tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::
       test_the_harnesss_docstring_counts_are_the_DERIVED_counts
AssertionError: the harness docstring says 36 test files import it; 39 actually do.
```

**Derived, both numbers:** importers **39** (stated 36), `connect_admin` callers **24** (stated 22).
The three new importers are `test_floor_calibration_schema.py`, `test_floor_calibration_store.py`,
`test_store_lease.py`; two of them also call `connect_admin`. **Cause: the 11-i-a contract wave added
those files and did not update `_surreal_harness.py`'s docstring** — that file was last touched
2026-07-25 (`f65e062`), and `git log d6c0dd4..HEAD -- loremaster/tests/_surreal_harness.py` is EMPTY.
The pin reads only test-tree files and the harness docstring, so no production change can move it.

**The edit (test tree — not mine):** in `loremaster/tests/_surreal_harness.py`'s module docstring,
`36 test files import this harness` → **39**, and `22 test files — calls ``connect_admin``` → **24**.
Worth noting the pin worked exactly as designed: a derived-count gate caught prose drifting from
behaviour within a day.

### E-3 — a concurrency failure I could not reproduce. THIS IS A STOP, NOT A FLAKE VERDICT.

**What happened, exactly.** In the first 20-run repeat loop of the 4-file contract, **runs 8 and 9
failed** — both reporting `28 failed, 168 passed` with
`TestTheHeadMintUnderContention::test_no_adoption_is_lost_under_contention[32]` first in the
summary. Runs 1–7 and 10–20 passed 196/196.

**What I then measured — five DESIGNED conditions, not just repetition:**

| loop | condition (why) | result |
|---|---|---|
| 12 runs | 4-file contract, `--tb=line` | 12/12 green |
| 40 runs | 4-file contract, `--tb=long -rf`, stop-on-first-failure (keep the evidence this time) | 40/40 green |
| 60 runs | the contention classes ALONE, `-n 6` (maximise executions of the mechanism per minute) | 60/60 green — 540 executions of the 8/16/32-way mint |
| 16 runs | **TWO concurrent 4-file runs** (≈128 xdist workers, double the sockets and double the write load — tests the socket-exhaustion / store-saturation hypotheses) | 16/16 green (both processes, every iteration) |
| 6 + 20 runs | 4-file contract IMMEDIATELY after a full-suite run, then continuously across the **0–4 minute post-suite window** (tests the "post-heavy-suite RocksDB compaction / write-stall" hypothesis, which the original failure's timing fit) | 26/26 green — **hypothesis (a) is now tested and NOT supported** |

**My own instrument failure, stated plainly:** the loop that caught it captured only `tail -2`, so
**the 28 failing node ids and their tracebacks are gone.** That is this repo's own law — *"if step N
silently no-opped, would step N+1 still print something that reads as success?"* — turned around: my
step N *did* fail and my capture threw the evidence away. Every loop after that keeps full output.

**What the shape suggests, offered as hypotheses and NOT as a verdict:** an identical `28 failed` in
two consecutive runs, followed by 94 clean runs across those five conditions, reads as a transient
STORE-WIDE condition rather than as a lost update — a lost update in the mint fails ONE test, and 28
is a large fraction of the ~110 live-engine tests in those four files. Candidates and their status
after the table above:
**(a) a post-full-suite RocksDB compaction / write-stall window** on spike-surreal (`Sync mode:
every transaction commit`) — the original failure's timing fit it (≈2 min after a full suite);
**26 post-suite runs across that window say NO.**
**(b) socket exhaustion** — `-n auto` is 64 xdist workers on this box and each 32-way pin opens 32
live connections; **16 doubled-load runs (≈128 workers) say NO, though a doubling is not a proof of
the ceiling's location.**
**(c) genuine exhaustion of the shared 2 s conflict-retry budget** at 32-way × 3 adoptions, which
raises `TxnContentionExhaustedError` and would fail the pin at its `head_revision is not None`
assertion. **Untested as a mechanism** — 540 executions of the mint did not produce it, and without
the original tracebacks I cannot confirm it was the error. Note `test_findings.py` already pins a
16/32-way mint of the same shape, so the DEGREE is precedented; my transaction is one statement
longer.
**(d) something outside the store entirely** (a host-level hiccup in that ~25-second window). I
cannot rule this out and will not pretend the other three exhaust the space.

**What I recommend, and why it is not a builder decision:** if (c) is the mechanism, the answer is a
question about the SHARED budget (#102's territory), not a `deadline_seconds=` at one call site —
a private budget wearing the shared driver's name is exactly the #102/#120 shape. If (a)/(b), it is
an environment finding and the contention pins may be unreliable *as a checkpoint gate* right after
a full suite, which the lead needs to know before treating a red as a defect. **Recommended
instrument for the next wave:** a repeat loop that keeps every run's full output plus the store's
`podman logs` window, and a declared expected-RED set (`scripts/mutation_proof.py`'s discipline)
so an unexpected failure set is diffed rather than eyeballed.

### E-4 — I wrote copies #11 and #12 of the connect/bootstrap/close boilerplate. This is a DESIGN question.

`FloorCalibrationStore` and `SurrealLeaseStore` each carry `_ensure_connection` /
`_drop_connection` / `_safe_close` / `close`, byte-similar to `TaskLedger`'s. The POLICY is already
shared (`bootstrap_session`, `run_query`, `execute_transaction`, `retry_on_conflict`, the
classification); what is duplicated is the connect glue and the F4 disposition wrap. Standing law
says a caller may not quietly write copy #2, so: **I wrote it because the contract requires this
exact shape, and I am escalating it rather than pretending it is not duplication.**

⚠ **And the trap that kills the naive fix, which is probably WHY the repo keeps it inline:**
`test_retry_seam.py::_discover_socket_owners` enumerates classes by the PROPERTY *"its
`_ensure_connection` constructs `AsyncSurreal(...)`"*. Extract the body into a shared helper and
**all twelve owners fall out of that enumeration** — the double-checked-lock pin goes vacuously
green, which is #120's shape. Any extraction must therefore land WITH a re-keyed enumeration in the
same diff. That makes it a contract-plus-production change, i.e. yours to schedule.

### E-5 — `LeaseError` is declared by the frozen interface and raised by nothing

`store/lease.py` declares `class LeaseError(SurrealStoreError)` (the contract's interface freeze names
it). My build never raises it: the store seam raises the `_txn` types, and the lock reports failure
through the library's boolean/`LockAbsent` channel (§2.12). Either 11-ii's election thread is its
intended raiser, or it is dead surface. Flagged, not deleted — deleting a frozen interface member is
not a builder's call.

### E-6 — the store reference's §8 teaches a retired claim about the retry budget

`docs/reference/surrealdb-31-capabilities.md` §8 still says *"**[#102, OPEN]** The shared `_txn`
conflict-retry budget is 2-way-tuned and **completely un-jittered** (§5). Blocks `-n auto` as the
full-suite checkpoint gate."* §5 of the SAME file says the fix landed 2026-07-14 at `9d29111` with
fresh per-attempt jitter, and this repo now runs `-n auto` as its standard gate. A reader who lands
on §8 (a retrieval chunk arrives without its neighbours) is taught a mechanism that no longer exists
— the stale-prose class §8 itself catalogues. Docs are outside my writable set.

### E-7 — the derivations I introduced have mutation RECEIPTS but no PIN

Four derivations carry my manual mutation proofs (§7) and no test:
(a) `floor_head`'s axis columns follow `FLOOR_HEAD_ALWAYS_SERIALISED_AXES`; (b) the head mint's axis
assignments follow the same registry; (c) `measurement_history`'s projection follows
`FLOOR_MEASUREMENT_COLUMNS`; (d) the pool projection follows `CALIBRATION_POOL_COLUMNS`. A fix wave
can pin each in three lines (monkeypatch the constant, assert the emitted text moves) — the same
shape as the contract's existing `test_changing_the_state_tuple_changes_the_emitted_ASSERT`. **A fix
without an invariant is half a fix**, and I cannot write the invariant.

---

## 5. PACKAGES CONSIDERED

| mechanism | package / existing implementation | what I **READ** to decide | verdict |
|---|---|---|---|
| the two identity pre-images | **`orjson` 3.11** (`OPT_SORT_KEYS`) | the installed `orjson/__init__.pyi` `dumps` signature + `OPT_SORT_KEYS`; the frozen golden digest re-derived from it and matched byte-for-byte against the contract's literal | **replace** (operator ruling O1) |
| leader election | **`kubernetes.leaderelection` 36.0.3** | `leaderelection.py` (183 LOC, read END TO END — the create-if-absent `json.loads(body)['code']` branch, the four-field-None → `update_lock` branch, the `__dict__`-equality observation clock, `renew_loop`), `electionconfig.py` (six required positionals, `sys.exit` validation, the silent no-op `onstopped_leading`), `leaderelectionrecord.py` (exactly four attributes) | **replace_with_adapter** |
| retry / backoff / conflict classification / session bootstrap | **`_txn.retry_on_conflict` · `run_query` · `execute_transaction` · `bootstrap_session`** | `_txn.py` bodies: `run_query`'s classify-signal-self-heal ladder, `execute_transaction`'s `_rollback_verdict`, `_domain_root_cause`'s first-non-cascade selector, the attempt floor/ceiling/deadline, `_RETRYABLE_CONFLICT_MARKER` | **keep_with_trigger** — trigger: #111 (an `ErrorKind` retryable member would replace the substring) |
| DDL text | **`surreal_schema._define_table` / `_define_field` / `_plain_index`** | their bodies + the #107 docstring; the clause rule they encode | **replace** (and the contract mutation-pins the routing) |
| the digest hash | **`loremaster.index.records.sha512_hex`** | its body (`hashlib.sha512`, UTF-8 for `str`) | **replace** — one hash implementation in the repo |
| the `LockAbsent` body | **stdlib `json`** | the library calls `json.loads(record.body)`, so the body must be a `str` of JSON; `orjson.dumps` returns `bytes` and would need decoding for no gain | **replace** |
| an immutable closed registry | **`types.MappingProxyType`** | the stdlib docs' read-only-view guarantee | **replace** (vs a hand-rolled frozen mapping) |
| measurement ids | **`uuid.uuid4`** | the repo's own id idiom (`tasks.py`, `briefs.py`) | **replace** |
| the head's monotonic revision | the engine's **native `DEFINE SEQUENCE`** | store reference §5 + §1.1's SEQUENCE row: the VENDOR documents *"Sequences are never rolled back, even in a failed transaction"* (gaps are a guarantee, not an accident), and §1.1 records the un-migratable `BATCH`/`START` residual (#146). The contract requires revisions to be **exactly 1..N consecutive**, and the slice's own pin forbids a `DEFINE SEQUENCE` here | **bespoke** — the counter-row `UPSERT` riding the shared driver, which is §5's own proven shape (not a new mechanism) |

No dependency was missing, so nothing needed an install authorization.

---

## 6. GATE TAILS

**All four measured on the FINAL tree** (re-run after the last edit — §2's `read_adopted_head`
torn-pointer guard — so no number here predates the code it describes):

```
$ uv run --no-sync pytest -n auto -q  test_floor_calibration_{domain,schema,store}.py test_store_lease.py
196 passed in 11.41s

$ uv run --no-sync pytest -n auto -q loremaster/tests/test_retry_seam.py
561 passed, 1 warning in 9.26s          # exactly ruling O2/B1's predicted number

$ uv run --no-sync pytest -n auto -q          # the full suite
1 failed, 7544 passed, 17 skipped, 3 xfailed, 1 warning in 198.24s (0:03:18)
FAILED loremaster/tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts
                                              # PRE-EXISTING — escalation E-2
# ⚠ The full suite ran FOUR times across this session (192.59s / 194.03s / 189.00s / 198.24s) with a
# BYTE-IDENTICAL result line every time: the same single failure, 7544 passed. That reproducibility is
# the receipt that E-2 is deterministic and production-independent, not a flake.

$ ./scripts/typecheck.sh
Success: no issues found in 27 source files      / typecheck: lorescribe OK
Success: no issues found in 34 source files      / typecheck: loresigil OK
Success: no issues found in 162 source files     / typecheck: loremaster OK

$ uv run --no-sync ruff check .
All checks passed!
```

The one warning is `test_retry_seam.py`'s own pre-existing `_empty_subscription was never awaited`
RuntimeWarning, unrelated to this packet.

---

## 7. THE CONCURRENCY REPEATS AND THE MUTATION RECEIPTS

**Repeats (the contract's own obligation: "twenty consecutive greens are the BUILDER's obligation").
The obligation is DISCHARGED by loop 6 — twenty consecutive greens in one uninterrupted loop — and
that does NOT retire loop 1's two failures, which stay escalated.** Every run below, measured
2026-07-26 on this worktree:

```
loop 1 (20 runs, 4-file contract):        18 green · runs 8 and 9 FAILED (28 failed / 168 passed each)
loop 2 (12 runs, --tb=line):              12 green
loop 3 (40 runs, --tb=long -rf):          40 green
loop 4 (60 runs, contention classes -n6): 60 green   (540 executions of the 8/16/32-way mint)
loop 5 (16 runs × 2 CONCURRENT processes): 32 process-runs green (doubled sockets + write load)
loop 6 (6 + 20 runs, post-full-suite):    26 green   (covers the 0–4 min post-suite window)
                                          ---------
4-file contract total:                    112 / 114 green

post-final-edit (the two LIVE files, 5 runs): 120 passed × 5, plus the final 196-passed contract run
  — so the last edit's tree carries 6 green runs of the 8/16/32-way pins, not one.
```

Escalation **E-3** carries the analysis, the four hypotheses with their status, and my own instrument
failure. The honest summary: **112 of 114 contract runs green, 2 failures I cannot explain, and the
evidence for those two was destroyed by my own capture.**

**Mutation receipts for the four derivations this build introduces** (in-process perturbation of the
shared constant; each leg also asserts the generated text restores byte-exactly, and the script
prints its provenance path first):

```
provenance: /home/ejprice/PycharmProjects/lore-pkt11ia/loremaster/loremaster/floor_calibration/store.py
LEG 1 HELD — floor_head axis columns follow FLOOR_HEAD_ALWAYS_SERIALISED_AXES
LEG 2 HELD — the pool projection follows CALIBRATION_POOL_COLUMNS
LEG 3 HELD — the history projection follows FLOOR_MEASUREMENT_COLUMNS
LEG 4 HELD — the head mint's axis writes follow the registry the DDL emits from
ALL FIVE LEGS HELD
```

Each leg fails LOUDLY if the dependent text does not move — i.e. if the "derived, not hand-typed"
claim is false. They are receipts, not pins: see **E-7**.

---

## 8. LORE VS GREP

**I did not use lore at all this run, and I am saying so rather than implying I did.** lore's index
watches `/workspace` — the MAIN checkout, not this worktree (#125) — so it is structurally blind to
every file in this packet, which is where all of my questions lived. Everything came from `Read` and
`grep` over: the four frozen contract files, `_txn.py`, `tasks.py` (the house seam shape),
`surreal_schema.py`, `test_retry_seam.py`'s enumerations, and the **installed** `kubernetes` and
`surrealdb` sources. Two of the dogfood protocol's three sanctioned fallbacks apply — non-symbol
textual seams (DDL clause text, the O2-frozen label/noun literals, engine statement text) and
exhaustiveness where one missed site compiles-but-breaks (the two `test_retry_seam.py`
enumerations) — and #125 covers the rest. No friction filed: #125 is already ledgered, and I hit no
lore weakness that is not already recorded.
