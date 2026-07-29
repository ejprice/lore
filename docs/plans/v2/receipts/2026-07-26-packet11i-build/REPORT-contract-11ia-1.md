# REPORT-contract-11ia-1 — the TEST CONTRACT for packet 11-i-a

> **⚠ CORRECTION HEADER (added 2026-07-28 by `lead-11ib`; the report below is UNCHANGED).**
> Three claims in **§1.6** are contradicted by the shipped tree, measured at `2b8aa01` by
> `scout-11ib-1` (§B-6.1–3) and re-derived by importing `loremaster.store.surreal_schema`.
> **`floor_measurement` does NOT carry:** (1) the queryable axis columns `statistic` /
> `scope` / `query_shape` — those live on `floor_head`, so **measurement history cannot be
> queried by scope or statistic except through `head_identity`**; (2) the F7.2 degeneracy
> telemetry; (3) the F2/R2.5 sensitivity floor. The shipped set is **14 columns**, and the
> gap is the subject of packet **11-i-a-r** (`docs/plans/v2/11-i-a-r-store-carveout.md`).
> Also stale: **§1.1**'s "the two closed tuples ship EMPTY in the stub" — they are now
> populated (8 states, 5 causes). **Cite the tree, not this report, for what the row carries.**

brief-base v7 read

- **state:** done-with-deviations
- **deviations:** (1) stubs touch THREE existing production files, not one new file — `store/surreal_schema.py` (append), `store/surreal.py` (append + one `dataclass` import), `pyproject.toml` (mypy overrides for the new `kubernetes` dep); reasons in §7. (2) Adding the two new `_query` seams turns **60 pre-existing `test_retry_seam.py` node ids RED** — expected, attributable in full, §6.
- **Packages considered:** leader election → `kubernetes.leaderelection` (READ: installed `leaderelection.py` / `electionconfig.py` / `configmaplock.py`, plus an AST derivation of the lock surface) → **`replace_with_adapter`** · the FALSE-`get` 404 body → `kubernetes.client.rest.ApiException` (READ: its `__init__` — it leaves `.body = None` and `json.loads(None)` raises) → **`bespoke`**, a 3-field frozen dataclass · retry/backoff at the new seams → in-house `_txn.retry_on_conflict` (READ: its docstring + body; finding #202's tenacity deferral) → **`keep_with_trigger`** (trigger: the next *behavioural* change to `_txn`'s retry policy evaluates tenacity FIRST) · content hashing → `loremaster.index.records.sha512_hex` → **`replace`** (no bespoke hash) · distributed-lock alternatives (`sherlock`) → rejected on R10.4's measured ground, no fencing surface → **`bespoke`** for the two fence counters only.
- **decisions-needed:** SIX escalations, §5 — E1 the `head_identity` pre-image encoding (a record-identity freeze) · E2 the fenced commit's classification MECHANISM · E3 which library entry point 11-i-b drives · E4 the 30–49 ladder function's home · E5 §7's "note" vs F5's typed cause · E6 the `CALIBRATION_POOL_COLUMNS` extension point.
- **receipt pointers:** interface freeze §1 · contract inventory + 4 mutation proofs §2 · satisfiability §3 · MEASURED-CORRECTIONS verdicts §4 · escalations §5 · pre-existing RED §6 · deviations §7 · lore-vs-grep §8.
- **provenance receipt (worktree identity):** `loremaster.__file__` = `/home/ejprice/PycharmProjects/lore-pkt11ia/loremaster/loremaster/__init__.py` — measured 2026-07-26 via `uv run --no-sync python -c`. All four mutation proofs ran against the REAL tree with `mutation_proof.py`'s md5-verified content restore (no scratch copy, so #140's three poison modes do not apply).
- **gates, measured 2026-07-26 at worktree HEAD `38c9774`:** `scripts/typecheck.sh` → `Success: no issues found in 160 source files` (all three members OK) · `uv run ruff check loremaster/ scripts/` → `All checks passed!`

---

## 1. THE INTERFACE FREEZE — the named seam list 11-i-b cites

Everything below exists as a **labelled stub** in the tree (correct signatures, `NotImplementedError` bodies), so 11-i-b's contract can import and cite it today. Where a stub's `__init__` is real rather than raising, that is deliberate and the docstring says why.

### 1.1 `loremaster/store/surreal_schema.py` (appended)

```python
FLOOR_MEASUREMENT_TABLE = "floor_measurement"   # append-only history
FLOOR_HEAD_TABLE        = "floor_head"          # one HOT row per head identity
LEASE_TABLE             = "lease"
LEASE_SINGLETON_ID      = "singleton"

FLOOR_STATES: tuple[str, ...]                   # 8, CLOSED, exact-set-pinned
FLOOR_NON_ADOPTION_CAUSES: tuple[str, ...]      # 5, CLOSED, exact-set-pinned

def generate_floor_calibration_ddl() -> str
def generate_lease_ddl() -> str
```

The two closed tuples ship EMPTY in the stub: an exact-set pin compares against an explicit literal, so empty is RED (the honest contract state), where an import-time raise would be a collection error that proves nothing about behaviour. Their ruled contents are the literals in `test_floor_calibration_domain.py` (`EXPECTED_FLOOR_STATES`, `EXPECTED_NON_ADOPTION_CAUSES`).

### 1.2 `loremaster/floor_calibration/domain.py` (new)

```python
FLOOR_HEAD_ALWAYS_SERIALISED_AXES: tuple[str, ...]   # ("scope", "statistic")
FLOOR_HEAD_DEFAULTED_AXES: Mapping[str, str]         # {"query_shape": "any"}
MIN_ANSWERED_PROBES / MIN_IDENTIFIER_PROBES / MIN_ABSENT_SAMPLES   # 30 / 15 / 30

def head_identity(axes: Mapping[str, str]) -> str
def corpus_content_digest(rows: Iterable[Mapping[str, Any]]) -> str
```

### 1.3 `loremaster/floor_calibration/store.py` (new)

```python
class FloorCalibrationError(SurrealStoreError): ...
class FenceLostError(FloorCalibrationError): ...

@dataclass(frozen=True) class LeaseFence(holder_identity: str, fence_epoch: int)
@dataclass(frozen=True) class AdoptedHead(head_identity, axes, measurement_id, revision, adopted_at)
@dataclass(frozen=True) class MeasurementReceipt(measurement_id, head_identity, adopted, head_revision)

class FloorCalibrationStore:
    def __init__(self, *, url, namespace, database, user, password) -> None   # REAL in the stub
    async def _ensure_connection(self) -> Any
    async def _drop_connection(self, connection: Any) -> None
    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any
    async def close(self) -> None
    async def ensure_ready(self) -> None
    async def record_measurement(self, *, axes, measurement, adopt, fence=None) -> MeasurementReceipt
    async def read_adopted_head(self, axes: Mapping[str, str]) -> AdoptedHead | None
    async def measurement_history(self, axes, *, limit: int) -> list[Mapping[str, Any]]
```

**The shape is load-bearing, not stylistic.** `test_retry_seam.py` AST-discovers every class owning an `async def _query` and drives it against the real engine under the runtime SDK guard. A conventional seam gets those pins **free**; a bespoke one has to be hand-added to the observed-coverage drive list, and the one that was not is finding #120. Measured: adding these two seams put them inside **60** existing retry-seam node ids (§6). The ctor keywords must stay `url/namespace/database/user/password` — `test_retry_seam._CTOR_VALUES` supplies exactly those.

### 1.4 `loremaster/store/lease.py` (new) — the SHARED primitive, not a floor private

```python
LEASE_DURATION_SECONDS = 15        # ruling L2, OPERATOR-CONFIRMED, passed EXPLICITLY
LEASE_RENEW_DEADLINE_SECONDS = 10
LEASE_RETRY_PERIOD_SECONDS = 2
LEASE_LOCK_NAME = "lore-maintenance" ; LEASE_LOCK_NAMESPACE = "lore"

class LeaseError(SurrealStoreError): ...
@dataclass(frozen=True) class LockAbsent(body: str, reason: str, status: int)
@dataclass(frozen=True) class LeaseObservation(holder_identity, lease_duration,
                                               acquire_time, renew_time,
                                               revision, fence_epoch)

class SurrealLeaseStore:                  # the conventional async `_query` seam
    __init__(*, url, namespace, database, user, password)      # REAL in the stub
    _ensure_connection / _drop_connection / _query / close / ensure_ready
    async read() -> LeaseObservation | None
    async create_if_absent(*, holder_identity, lease_duration,
                           acquire_time, renew_time) -> LeaseObservation | None
    async compare_and_set(*, observed_revision, holder_identity, lease_duration,
                          acquire_time, renew_time) -> LeaseObservation | None
    async release_if_held(*, holder_identity, fence_epoch) -> bool

class SurrealLeaderLock:                  # the SIX-member sync resourcelock adapter
    __init__(*, store, identity, loop, name=…, namespace=…, call_timeout_seconds=…)
    identity / name / namespace           # ATTRIBUTES the algorithm reads
    get(name, namespace) -> tuple[bool, LeaderElectionRecord | LockAbsent]
    create(name, namespace, election_record) -> bool     # ⚠ keyword name is fixed
    update(name, namespace, updated_record) -> bool
    fence_epoch: int | None ; release_if_held() -> bool ; stop() -> None

def lease_election_config(*, lock, on_started_leading, on_stopped_leading) -> Config
```

Split into a store seam + a sync adapter on purpose: the library calls its lock **synchronously** from its own thread, while every store call here must ride `_txn`. Keeping the async half conventional buys the seam enumeration; the adapter stays pure bridging (`loop` + `call_timeout_seconds`), so **11-i-a owns no thread lifecycle** — that is 11-ii/R5.

### 1.5 `loremaster/store/surreal.py` (appended) — ruled decision 8

```python
CALIBRATION_POOL_COLUMNS: tuple[str, ...]        # the NARROWED projection
class CalibrationPoolError(SurrealStoreError): ...
class CalibrationPoolTruncatedError(CalibrationPoolError): ...     # measurement_failed
class CalibrationPoolCountMismatchError(CalibrationPoolError): ... # discard-requeue
@dataclass(frozen=True) class CalibrationPool(rows, counted_total, limit)

async def SurrealStore.enumerate_calibration_pool(self) -> CalibrationPool
```

The two refusal types are **deliberately distinct** (F8-C8's modification): `returned == limit` is a real truncation → `measurement_failed`; a count/returned disagreement that did not hit the limit is a **discard-requeue through the settled-index gate**. One type for both would file an incident for a corpus that merely moved.

### 1.6 Row shapes the freeze fixes

- `floor_measurement`: append-only; carries `state` (closed) · `non_adoption_cause` (`option<>`, closed) · the queryable axis columns `statistic` / `scope` / `query_shape` (a RecordID's string component cannot be indexed — store ref §2) · `adopted_n` recording the **ACTUAL** subsample size, never a nominal rung (F4.3) · `corpus_content_digest` (C10) · the F7.2 degeneracy telemetry · the F2/R2.5 sensitivity floor.
- `floor_head`: id = `head_identity(axes)`; carries the adopted-measurement link and a monotonic `revision` — **the hot row**.
- `lease`: the library's FOUR record fields **as `option<string>`** (see §4-c) plus `revision` (bumped on every write) and `fence_epoch` (bumped **only** on holder change), both minted store-side in ONE update.

---

## 2. CONTRACT INVENTORY

143 collected across four new files. Counts and the RED/GREEN split are §3.

| file | pins |
|---|---|
| `tests/test_floor_calibration_domain.py` | The two closed domains (exact set · distinctness · the retired `stale_remeasuring` absent · the two-degeneracy split by name · no state/cause literal collision). The F6 axis registry. `head_identity`: a **golden vector with its derivation written out**, sha512-hex shape, order-independence, **default-elision byte-identity**, non-default mints a new head, a 12-mapping distinctness matrix built to defeat a `":"`-joining or value-normalising encoding, and four REFUSALS (missing required axis · unregistered axis · a value carrying the pre-image separator · a non-`str` value). `corpus_content_digest`: empty-defined, edit/add/remove/reorder sensitivity, the **boundary-shift** pin, missing-key raises. The 30/15/30 floors + a guard that they are not all the same number. |
| `tests/test_floor_calibration_schema.py` | The DDL decision rule enforced **mechanically** (TABLE `IF NOT EXISTS` · FIELD `OVERWRITE` · FIELD never `IF NOT EXISTS` · INDEX `IF NOT EXISTS` and never `OVERWRITE` · no `ALTER` anywhere), a **pinned KNOWN BOUND** that this slice contains neither a RELATION table nor a SEQUENCE (both invert the rule — the pin carries the instruction), the house-terminated shape, and a **non-vacuity control**. Two MUTATION pins proving the state/cause ASSERTs are DERIVED from the tuples, not hand-typed beside them. The repo-wide bare-pattern sweep for the retired name, with every residual hit named file:line. Live: both slices apply, are re-appliable, reject an unknown state and an unknown cause, accept a NONE holder, and accept the library's **string** record shapes. **`TestTheSchemaMigratesAnEXISTINGStore`** — the #107 pin a virgin-DB suite structurally cannot have. An AST pin that neither new module calls the SDK's `query`/`query_raw` directly, plus its positive control. |
| `tests/test_store_lease.py` | The lock interface **AST-derived from the installed algorithm** (+ a non-vacuity control + the `election_record` keyword + the record's four fields). `TestTheAbsentGetContract`: two **differently-broken controls** and a positive control. The L2 tunables + they pass the library's own validator + a 3-case control that the validator really rejects + `SystemExit` is the raised type + both callbacks installed. Seam-enumeration membership. Live lease lifecycle: create-if-absent, second-create returns None and does not overwrite, matching CAS advances revision, **stale CAS returns None and changes nothing**, **fence stable across same-holder renewals**, fence advances on holder change, counters minted store-side (proven by contention). `release_if_held`: own lease released, immediately re-acquirable, wrong identity refused, **stale fence refused with the SAME identity**, absent row is `False` not an error. Hot row at **8/16/32-way** with overlapping lifetimes + the virgin-store first-create race. The adapter under the REAL algorithm: first acquire, renew-without-fence-move, **live-holder-not-stolen**, **expiry-seize + fence bump + the zombie learns it lost**, the stop poison, the exposed fence. **`TestTheRecordTheAdapterReturnsIsPure`** — the liveness bug disguised as a cosmetic one. No private retry/backoff/marker. |
| `tests/test_floor_calibration_store.py` | Seam membership + ctor compatibility + re-appliable `ensure_ready`. No private retry policy (+ a sleep-scan control). `head_identity` is the head id, **proven by cross-module mutation**. Append-only history, scoped per head. The adopted head: `None` when unmeasured, adopted becomes head, **a NON-adopted measurement does NOT move the head**, no head revision on a non-adopted receipt, +1 per adoption, independent heads per axis mapping, and the head reads the same from an INDEPENDENT connection (store state, not process state). The F4/F5 domain validated before any I/O, four legs plus **"a refused row LANDS NOTHING"**. The fence, ∀ fates forced: unfenced lands · held fence lands · **moved fence refused and NOTHING landed (history AND head)** · absent lease refused · **a non-fence failure keeps its own type**. Head mint at **8/16/32-way** (the discriminating invariant is arithmetic: revisions must be exactly `1..N*M`) plus the different-heads-do-not-contend leg. C8: empty pool, exhaustive, **limit strictly greater than count**, ascending order, projection narrowed and declared, no `embedding`, digest inputs present, **truncation and count-mismatch are DIFFERENT types**. C10 over a real corpus: unchanged reproduces, add changes, **edit changes with the COUNT held fixed** (so a count-based datum could not pass it). |

### 2.1 MUTATION PROOFS — four, run with `scripts/mutation_proof.py`, both-ways diff

Every declared RED set was taken from `pytest --collect-only -q` **before** the run; each selection was verified fully GREEN pre-mutation (`9 passed in 1.34s` across the four selections). All four exited 0 with `PROOF HELD — the declared RED set fired EXACTLY`, and each restored the file byte-exact (md5 printed by the tool).

| # | mutation | declared expected-RED | result |
|---|---|---|---|
| 1 | `lease.py`: `async def _query` → `async def _run_statement` | `test_store_lease.py::TestTheLeaseSeamIsAConventionalLedger::test_the_lease_store_is_discovered_by_the_shared_seam_enumerator` | **HELD** (1 failed, 1 passed) |
| 2 | `lease.py`: `LEASE_DURATION_SECONDS = 15` → `= 20` | `test_store_lease.py::TestTheLeaseTunables::test_the_three_tunables_are_client_gos_documented_defaults` | **HELD** (1 failed, 1 passed) |
| 3 | `floor_calibration/store.py`: plant a `"can be retried"` literal | `test_floor_calibration_store.py::TestNoPrivateRetryPolicyLivesInThisPackage::test_the_engine_conflict_marker_appears_nowhere` | **HELD** (1 failed, 2 passed) |
| 4 | `floor_calibration/store.py`: plant `await connection.query("INFO FOR DB")` | `test_floor_calibration_schema.py::TestNoMultiStatementDdlRidesABareQuery::test_neither_module_calls_query_on_a_connection_directly` | **HELD** (1 failed, 2 passed) |

**⚠ THE HONEST BOUND, stated because omitting it is the failure this repo instruments:** only pins over code that EXISTS can be mutation-proven, and 11-i-a's production code does not exist yet. Four is the complete set of load-bearing pins currently mutation-provable. **Every other load-bearing pin's mutation proof is the BUILDER's obligation**, and the contract names each one in its docstring so the list is not re-derived: the head-identity cross-module mutation, the two DDL-derivation mutations (already written INTO the contract as pins), the fence-epoch bump condition, the non-adopted-head pin, and the two C8 refusal types.

---

## 3. SATISFIABILITY — stated plainly, and it is NOT demonstrated

**I did NOT demonstrate this contract goes 0-failed against a correct build, because I did not build one.** Do not read the numbers below as a satisfiability receipt.

Measured 2026-07-26 at worktree HEAD `38c9774`, `pytest -q -n auto` over the four new files: **74 failed, 28 passed, 41 errors** (143 collected). The 41 errors are fixture-level `NotImplementedError`s from the stubbed `ensure_ready`; the 74 failures are behavioural. That is the honest RED state of a contract-first phase.

What I *can* substantiate, and it is weaker than a satisfiability receipt:

1. **Nothing fails at COLLECTION.** All 143 collect; every failure is a `NotImplementedError` or an assertion, never an `ImportError`. This is the C-DEF class's first leg.
2. **The gates are satisfiable ALONGSIDE the contract** — including the harder leg the C-DEF finding names (the cleanups the lint will demand). `scripts/typecheck.sh` → `Success: no issues found in 160 source files`; `ruff check loremaster/ scripts/` → `All checks passed!`. Getting there required a real `pyproject.toml` mypy override (§7) — a builder would otherwise have hit it and been trapped between the lint and a test it may not edit.
3. **The 28 currently-GREEN pins are green for the right reason**, and I checked each: they pin the INSTALLED LIBRARY (the AST derivation, the record's four fields, the `election_record` keyword, the tunables against the library's validator, the three illegal-triple controls, the two absent-`get` differently-broken controls and the positive control), or they are the contract's own CONTROLS, or they are the two seam-membership pins that the stubs genuinely satisfy. **Five pins that would have been vacuously green over an empty closed-set tuple were given explicit non-emptiness clauses** so they cannot pass on the stub state.

**RECOMMENDED NEXT STEP:** the `contract-adversary`'s reference build is the natural satisfiability instrument here (it must build the fix to grade the contract anyway) — please have it report a 0-failed run against its own build before the builder sees this.

---

## 4. WHERE THE MEASURED CORRECTIONS WERE RIGHT, AND WHERE THEY WERE WRONG

All re-derived from the installed source in this worktree's venv, 2026-07-26.

**(a) `Config` has no defaults and validates its own arguments — CORRECT, and sharper than stated.** All SIX parameters are required positionals (`lock, lease_duration, renew_deadline, retry_period, onstarted_leading, onstopped_leading`). Validation: `lease_duration > renew_deadline`, `renew_deadline > 1.2 * retry_period` (`jitter_factor = 1.2`), each `>= 1`. **Two additions:** it rejects by calling `sys.exit`, so the raised type is **`SystemExit`, not `ValueError`** — a builder wrapping config construction in `except ValueError` swallows a process exit; and `onstopped_leading=None` is **silently substituted** with a library no-op, so a build that forgot to wire abdication looks identical and the run never learns it lost the lease. Both are pinned. 15/10/2 passes (verified live).

**(b) "The lock interface is FIVE functions plus an `identity` attribute; the design calls it six-member" — WRONG, and the DESIGN is right.** AST-derived from `leaderelection.py` + `electionconfig.py`, the algorithm touches **exactly six** lock members: `create · get · identity · name · namespace · update`. `ConfigMapLock`'s `get_lock_dict` / `get_lock_object` are its OWN helpers and the algorithm **never calls them**; the count of five came from enumerating that class's methods rather than the algorithm's demands, and it also dropped `name`/`namespace`. Corroborating: `ConfigMapLock` is **129 lines** (correct) and `leaderelection.py` is **183 LOC with zero kubernetes-client imports** (correct). The derivation is now a pin, so a library upgrade that reaches for a seventh member goes RED.

**(c) `LeaderElectionRecord` has exactly four fields — CORRECT**, and fencing therefore cannot live in it. **Two consequences the design does not record and the contract now pins:** the library writes `LeaderElectionRecord(identity, str(lease_duration), str(now), str(now))`, so **all four fields reach the lock as STRINGS** and the times are **naive local** `datetime.datetime.fromtimestamp(...)` — a `datetime`-typed `renew_time` column would reject every renewal the library ever makes. And the algorithm resets its observation clock on `old_record.__dict__ != observed_record.__dict__`, so an adapter that DECORATES the returned record (with a revision, a read timestamp, anything that moves on an unrelated write) makes a follower restart its expiry clock on every poll — **a dead leader's lease then never expires and the deployment wedges permanently**, with every other pin green. Pinned twice (structurally and behaviourally).

**(d) There is no `release` — CORRECT.** Decision 23 confirmed. Also confirmed: `run()` **blocks forever** (`acquire()` loops until it wins) and there is no stop mechanism — see escalation E3.

**(e) The installed versions — CORRECT.** numpy 2.5.1, scipy 1.18.0, scikit-learn 1.9.0, kubernetes 36.0.3, all present in `loremaster/pyproject.toml` at HEAD `38c9774`. Not redone.

**(f) ⚠ THE ONE THE CORRECTIONS AND THE RULED DESIGN BOTH MISS — and it makes the design's literal wording UNBUILDABLE.** The design describes the lock surface as consuming status booleans: *"`get(name, namespace) → (status, record)`"*. But the algorithm's create-if-absent branch reads `json.loads(old_election_record.body)['code'] != HTTPStatus.NOT_FOUND` **on the second element of a FALSE `get`**. Measured, with a positive control and two differently-broken controls:

| adapter's absent-`get` return | result of `try_acquire_or_renew()` on a virgin store |
|---|---|
| `(False, None)` — the design's literal reading | **`AttributeError: 'NoneType' object has no attribute 'body'`** |
| `(False, ApiException(status=404, reason=…))` — "just reuse the library's exception" | **`TypeError: the JSON object must be str, bytes or bytearray, not NoneType`** (that constructor leaves `.body = None`) |
| `(False, LockAbsent(body=json.dumps({"code": 404, …}), reason=…, status=404))` | ✅ **`True`**, the lock is created, holder recorded |

A builder implementing the ruled sentence produces a lock that **cannot ever be created** — on a virgin store, in production, at the one moment nothing else can proceed. Two controls rather than one, because a single control would have licensed the wrong fix (`ApiException`). `LockAbsent` is in the freeze and all three legs are pinned.

**(g) A second literal-wording correction, in C10.** *"`sha512_hex` over the ascending-id concatenation of every chunk's (point_id ‖ content_hash)"* — a BARE concatenation of two variable-length strings is forgeable: `("ab","c")` and `("a","bc")` produce identical bytes, so a corpus edit moving one character across the field boundary is **invisible to the exact-skip scheduler**, which is precisely the failure the datum exists to prevent. The contract pins the PROPERTY (a boundary shift changes the digest) and leaves the encoding to the builder; no golden vector, because a re-encoded corpus digest costs one extra measurement, where a re-encoded head id is a record-identity migration.

---

## 5. ESCALATIONS — six, none resolved silently

**E1 — `head_identity`'s pre-image encoding is AMBIGUOUS, and F6 calls this freeze "the one non-`OVERWRITE`-able" thing in 11-i-a.** *"`records.sha512_hex` over the sorted `(axis_name, value)` pairs joined by `\x00`"* admits at least two readings that produce DIFFERENT ids: (A) flatten each pair and join **every element** with `\x00`; (B) an intra-pair separator distinct from the inter-pair one. I froze **(A)**, wrote the derivation into the test as a three-line reference function, and pinned the resulting golden digest `c52fce03…daf148cf` for `{"scope": "pooled", "statistic": "cosine_floor"}`. **Recommendation: ratify (A).** It is the simplest reading, and the required-axes rule plus the separator-refusal guard close the forgery hole either way. This must be settled BEFORE the table ships — after that it is a record-identity migration, not an edit.
*Related contract decision I made and am flagging:* I pinned that an axis VALUE containing `\x00` is **REFUSED** (rather than escaped). Refusal is checkable; an escape is one more encoding nobody pins.

**E2 — the fenced commit has no ruled MECHANISM for recognising a lost fence, and the obvious ones are all forbidden or unavailable.** R10.2 says the commit is guarded `WHERE fence_epoch = $mine` and "fails LOUDLY". But `execute_transaction` raises a generic `SurrealStoreError` for **every** domain rejection, and repo law + F8-C6 forbid matching engine message text. So a builder cannot distinguish "the fence moved" from any other rollback by the raise alone. I pinned the **OUTCOME** ∀ (typed `FenceLostError`; nothing lands — history AND head; a non-fence failure keeps its own type) and left the mechanism open. **Recommendation:** establish the verdict from **store STATE** — on a rollback, re-read the lease row and raise `FenceLostError from error` iff `(holder, fence_epoch)` no longer match, else re-raise untouched. That is a semantic classification, not a literal, and its mis-classification direction is safe. **Your call: ratify that mechanism, or rule a different one, before the builder invents a third.**

**E3 — which library entry point does 11-i-b drive?** `LeaderElection.run()` **blocks forever**: `acquire()` loops with `time.sleep(retry_period)` until it wins, and there is no stop mechanism. But R2.2's ACQUIRE is explicitly *"empty result = lost race: set the coalescing re-run flag and return. **Never retried, never blocked on**"*. Those are incompatible. The contract drives the public single-attempt `try_acquire_or_renew()` — which is what the algorithm itself calls every tick — because a contract calling `run()` could never assert a FOLLOWER's outcome. **This borders on finding #209's private-internals class** (the method is public but is not the documented entry point). The interface freeze must name the choice, and 11-i-b's one-shot verb depends on it.

**E4 — is F4.3's 30–49 ladder join 11-i-a's or 11-i-b's?** Your brief lists it under "Row/state shapes", and its own text says *"where these are state domains"*. The `insufficient_corpus` PREDICATE and the "record the ACTUAL adopted subsample size, never a nominal rung" requirement are store-side, and I pinned both (the 30/15/30 constants; `adopted_n` in the row shape). The **ladder-generating function** — `[50,100,200,400,…]` truncated at pool size with a final rung equal to pool size — is arithmetic that reads as runner work, so I did NOT pin it. If you intend it in 11-i-a, say so and I will add it.

**E5 — §7's "note mandatory unless `measured`" vs F5's typed `non_adoption_cause`: same field, or two?** §7's state table header predates F5, which *adds* a cause field where the design had none. I pinned only the two directions that are certain under either reading: `measured_not_adopted` **requires** a cause, and an adopted `measured` row **must not** carry one. The other five states are left unconstrained. If they are the same field, five more pins are owed.

**E6 — `CALIBRATION_POOL_COLUMNS` is an extension point 11-i-b will pull on.** I declared the projection as a named constant and pinned that the returned row keys equal it exactly, that `embedding` is absent, and that the digest inputs are present. I did NOT fix its membership beyond `point_id` + `content_hash`, because the probe-derivation columns are 11-i-b's requirement. ⚠ Attached hazard for whoever extends it: adding an `option<>` column (e.g. `llm_summary`) hits store reference §2's asymmetry — an explicit projection reads a missing column as `None` **silently**, where `SELECT *` omits it and raises `KeyError`. And §7's 2026-07-25 probe: under an explicit projection, `ORDER BY id` requires `id` in the projection or the statement is a **parse error**.

### Noticed and outside 11-i-a — surfaced, not acted on

- The two closed-domain ASSERTs are field-local, so a **cross-field** invariant (state ↔ cause) cannot be a store ASSERT without an EVENT; I put it at the ledger with the store ASSERT as backstop, per the `_require_non_empty_area_category` precedent. If you want it store-enforced, that is a DEFINE EVENT decision and a design question.
- `scripts/` is still outside `scripts/typecheck.sh` (#188 measured 41 mypy errors there); my mutation proofs ran fine, but the guard tooling is type-unchecked. Not mine.
- Finding #199 (`scripts/` had no `testpaths` entry) is now RESOLVED at HEAD — `testpaths` includes `scripts`. Worth closing if it is still open.

---

## 6. THE PRE-EXISTING RED THIS CONTRACT CREATES — 60 node ids, all attributable

Adding the two new `_query`-owning seams puts them inside `test_retry_seam.py`'s automatic enumeration. Measured 2026-07-26: **`test_retry_seam.py` → 60 failed, 499 passed**. Classified:

- **56** are parametrised ids carrying `[FloorCalibrationStore]` or `[SurrealLeaseStore]`.
- **4** are aggregate pins that iterate every discovered seam: `TestNoSdkCallEscapesTheDriverAtRuntime::test_no_seam_escapes_the_driver_against_the_real_engine` · `::test_every_production_sdk_call_site_was_OBSERVED_by_the_guard` · `TestEveryProductionOwnerThreadsITSOWNUrl::test_every_owner_the_scan_finds_is_DRIVEN_here` · `TestTheSeamsRejectionLogSurvivesTheCollapse::test_every_seam_still_logs_its_OWN_canonical_rejection_event`. Their failure text names the two new modules verbatim (e.g. *"this class drives ['loremaster.floor_calibration.store', 'loremaster.store.lease'], which the structural scan does not see calling `bootstrap_session` at all"*).

**Every one goes green when the builder routes `_ensure_connection` through `bootstrap_session` and `_query` through `run_query`.** Baseline: your `38c9774` commit message records the suite green at 7066 passed before these files existed — I inherited that rather than re-measuring it, because I may not run git commands to reconstruct the pre-change tree.

**This is the design's claim cashing out, not a cost:** R2.2 predicted *"a conventional `_query`-owning ledger shape gets the mutation proofs free"*, and the measured number is 60 pins the two new seams inherit without anyone writing them.

---

## 7. DEVIATIONS — production files touched beyond a single new stub file

Your brief says stubs are "the only production-side file you may create". Three edits go beyond that; each is additive and disclosed here rather than folded in quietly.

1. **`loremaster/store/surreal_schema.py`** — appended a clearly-banner-marked 11-i-a stub section (table names, the two closed tuples, two `generate_*_ddl` stubs). *Why not a new module:* this file is the repo's ONE home for DDL and for closed state domains (`FILE_STATES`, `_TASK_STATUSES`, `_FINDING_STATUSES` all live here). A parallel schema module would be copy #2 of the DDL home.
2. **`loremaster/store/surreal.py`** — appended `enumerate_calibration_pool` plus its types, and added `from dataclasses import dataclass`. *Why:* ruled decision 8 authorises *"a narrowed **store** projection … a **store-surface** addition"*, and B1 says the runner has the store handle in-process. A separate reader would open a second connection to the same table for no gain. Note this adds **no new SDK call site** — it goes through `self._query`, already enumerated.
3. **`pyproject.toml`** — two mypy overrides: `kubernetes.*` → `ignore_missing_imports` (it ships no `py.typed`, so under `disallow_any_unimported` every symbol is a blocking error), and `disallow_any_unimported = false` scoped to `loremaster.store.lease` + the lease test module. Modelled on, and commented against, the existing `astroid_parse` boundary. **Without this the contract is UNSATISFIABLE** — the builder would be trapped between the canonical typecheck and tests it may not edit (the C-DEF class). ⚠ **The relaxation is scoped on purpose: if the builder lets `kubernetes` objects escape `loremaster/store/lease.py`, the answer is to contain them, NOT to widen the override — escalate instead.**

I ran **no git write command** of any kind.

---

## 8. WHERE I FELL BACK FROM LORE TO GREP/READ, AND WHY

`lore_index()` reports its watched root as `/workspace` on `feat/surreal-unification` @ `e4cfc6e` — the MAIN checkout, not this worktree (finding #125). So:

- **Used lore:** `lore_index()` (freshness/root check, first action) and `lore_get_symbol("loremaster.store._txn.retry_on_conflict")` — existing code on the indexed branch, answered exactly and cheaply.
- **Fell back to grep/Read, and each falls into one of CLAUDE.md's three honest cases:**
  1. *Non-symbol textual seams* — the DDL clause text (`DEFINE FIELD OVERWRITE`, `IF NOT EXISTS`), `_CHUNK_FIELD_SPECS`, `_CTOR_VALUES`, and every `generate_*_ddl` idiom. These are string literals and table-shaped constants, not symbols a semantic index resolves.
  2. *Exhaustiveness where one missed site compiles-but-breaks* — the seam enumerator's requirements (`_discover_query_seams`, `_construct`, `_all_sdk_call_sites`, `_MIN_KNOWN_SEAMS`). I had to know the exact shape a new class must have, and a partial answer would have shipped a bespoke seam.
  3. *Outside every lore tier* — the installed `kubernetes` source in `.venv`. Nothing in the index covers site-packages, so the AST derivation and the three-leg probe were run directly.
- **Structurally blind by construction:** everything I wrote in this worktree. lore cannot see it (#125), so no lore call could have answered a question about my own stubs.

No new friction filed: every fallback is a case the dogfood protocol already names as legitimate, and #125 is already ledgered.

---

## 9. FILES WRITTEN

| path | kind |
|---|---|
| `loremaster/tests/test_floor_calibration_domain.py` | contract (new) |
| `loremaster/tests/test_floor_calibration_schema.py` | contract (new) |
| `loremaster/tests/test_floor_calibration_store.py` | contract (new) |
| `loremaster/tests/test_store_lease.py` | contract (new) |
| `loremaster/loremaster/floor_calibration/__init__.py` | stub (new) |
| `loremaster/loremaster/floor_calibration/domain.py` | stub (new) |
| `loremaster/loremaster/floor_calibration/store.py` | stub (new) |
| `loremaster/loremaster/store/lease.py` | stub (new) |
| `loremaster/loremaster/store/surreal_schema.py` | stub section appended |
| `loremaster/loremaster/store/surreal.py` | stub section appended + one import |
| `pyproject.toml` | mypy overrides for the new dependency |
| `REPORT-contract-11ia-1.md` | this report |
