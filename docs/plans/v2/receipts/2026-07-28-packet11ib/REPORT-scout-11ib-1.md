# REPORT-scout-11ib-1 — packet 11-i-b build inventory, interface freeze, open decisions

brief-base v7 read

## SUMMARY BLOCK

- **state:** done-with-deviations
- **deviations (3):** (1) a delegated measurement agent ran `uv run --no-sync` in this worktree, which
  **created `/home/ejprice/PycharmProjects/lore-pkt11i-b/.venv`** (it did not exist — the worktree had
  never been synced). It is gitignored; `git status` stayed clean of it. It is now fully populated and
  I re-measured through it. (2) I ran read-only `pytest --collect-only` and `python -c` through that
  venv — no test executed, no store touched. (3) A file **untracked at `BASELINE-11ib-full.txt`** was
  being written by another process during my run and contains at least one `F`; it is not mine.
- **Packages considered:** none — no mechanism specified (this is an inventory, not a build). The
  *measured* package state of the tree is deliverable **E**.
- **decisions-needed (6, all for the operator/lead):**
  1. **The `floor_measurement` row is missing ~12 fields the rulings require b to populate** (§A-9, §B-6).
     Adding them edits `store/surreal_schema.py`, an 11-i-a-owned file under the Q4.1 assignment rule.
  2. **The leader-election THREAD LIFECYCLE is unassigned** — 11-i-a "owns no thread lifecycle … that is
     11-ii/R5", yet b's R2 verb is the first and only consumer of the lease (§C-open-3). This is a
     DESIGN question, not a build item.
  3. **Decision 15 (image git ≥2.48) is the one of the 23 with no line in `RULINGS-2026-07-25.md`** —
     it is re-dispositioned only *inside* decision 12's ruling ("No git bump") and by §R8 (§C-15).
  4. **Sizing exceeds the ≥0.30 split clause** on my re-derivation (~0.34, arithmetic in §G).
  5. Builder-flagged, still unruled: `adopt=True` on a non-`measured` state is NOT refused (§D-11);
     the pool's `counted_total + 1` margin classifies corpus GROWTH as `measurement_failed` (§D-12).
  6. `#237`'s reproduce recipe cites two files that **do not exist in the tree** (§D-19, §RAISED-3).
- **receipt pointers:** build inventory §A · shipped signatures + 6 divergences §B · all 23 decisions
  individually §C · 24 hazards §D · measured dependency table §E · consumer surfaces §F · sizing
  arithmetic §G · 9 raised items §RAISED.
- **Tool honesty:** lore's index watches the MAIN checkout at `2b8aa01`, byte-identical to this
  worktree's base, so it is accurate here. I used `lore_findings` for the ledger. **Every code and
  count claim below is grep/`Read`/`git`/live-`python` against this worktree** — the three sanctioned
  fallback cases all applied (rename/field exhaustiveness where one missed field is a silent `None`;
  non-symbol textual seams — field-name strings in DDL specs; a cross-cutting multi-question map).
- **Delegation honesty:** I used two subagents for fan-out (receipt-scraping, dependency measurement).
  **I re-derived their load-bearing claims myself, and TWO DID NOT SURVIVE** — a "live defect" about the
  image's testpaths (RAISED-4) and a "prose describes a mechanism that does not exist" about `cachetools`
  (RAISED-5). Both are retracted in place rather than dropped. Treat that as the calibration for how much
  of this report is measured: the tables in §A/§B/§E/§F and every count are mine; §D's quotations are
  theirs, spot-verified — including §D-0, which I reproduced independently.

**Everything below is measured 2026-07-28 against worktree `/home/ejprice/PycharmProjects/lore-pkt11i-b`,
branch `pkt11-i-b-floor-runner`, base commit `2b8aa01`.** Present-tense claims are claims about that tree
at that commit, not about any later one.

---

## A. THE BUILD INVENTORY — what 11-i-b owes

Assignment rule of record: `receipts/2026-07-26-packet11i-fixwave/REPORT-fable-design-11i-b.md` §Q4.1 —
*"11-i-a owns everything that touches `loremaster/store/*`, the schema, shared seams, and the engine's
persistent API. 11-i-b owns everything that is pure runner arithmetic, probes, and the R2 verb."*

**PORT** = code exists in `scripts/`, must move into `loremaster` (measured: the `Containerfile`'s COPY
allowlist is `pyproject.toml`, `uv.lock`, `lorerunes/`, `lorescribe/`, `loresigil/`, `loremaster/` —
**`scripts/` and `docs/` are absent**, so nothing in `scripts/` can run in-container). **NEW** = no
prior code.

| # | item | source | what 11-i-a ALREADY SHIPPED (verified symbol) | what remains for b | kind |
|---|---|---|---|---|---|
| A-1 | Core survey module port into `loremaster` | `REPORT-scout-11i.md` RAISED-3a; `CONTRACT-FREEZE-DECISIONS.md` §B ("`scripts/` is not COPYed into the image at all") | — nothing | move `scripts/search_score_survey.py` (999 LOC) into `loremaster`; **re-point `from token_survey import percentile` (a `sys.path`-insert import of a sibling SCRIPT) at `loremaster.stats.nearest_rank_percentile`** — that import cannot resolve in the image | **PORT** |
| A-2 | The 53 survey tests | R9.4 / `REPORT-scout-11i.md` RAISED-4 (both say "50") | `scripts` **IS** in root `testpaths` (measured, `pyproject.toml`) — #199 RESOLVED | re-home into `loremaster/tests/` with the code; **retarget**: dominance suite → ORACLE suite, arithmetic-helper tests retire with their helpers, the three `is`-identity pins carry verbatim | **PORT** |
| A-3 | The three production-identity pins | design §7; `test_search_score_survey.py::TestPredicateParityWithProduction` | — | carry verbatim: `query_tokens is search._query_tokens` · `has_verbatim_identifier_anchor is search._has_verbatim_identifier_anchor` · `cosine_absence_verdict_fires is search._cosine_absence_predicate` | **PORT** |
| A-4 | Percentile consumption | #198 (`ea7406e`), #237 | `loremaster/loremaster/stats.py` — `nearest_rank_quantile` / `nearest_rank_percentile` / `weighted_nearest_rank_percentile`, `QUANTILE_METHOD = "inverted_cdf"` | call the seam directly; add **#237's convention-discriminating pin** (interior percentile, n≥3, distinct values), mutation-proven | **PORT** |
| A-5 | Hash-stable pool sampling (D2) | design D2; `CONTRACT-FREEZE-DECISIONS.md` C12 | `SurrealStore.enumerate_calibration_pool() -> CalibrationPool`; `CALIBRATION_POOL_COLUMNS = ("point_id","content_hash")`; `CalibrationPoolTruncatedError` / `CalibrationPoolCountMismatchError` | membership keyed on `point_id`; identifier probes = first 15 identities in ascending `sha512_hex(identity)` order; **retire `every_nth` from the portable runner**; insertion-perturbation fixture | **NEW** (retires PORT code) |
| A-6 | `CALIBRATION_POOL_COLUMNS` extension | ruling E6 | the constant + `_calibration_pool_projection()` DERIVED from it | **add the probe-derivation columns** (stratification / hold-out / self-retrieval keys, probe-derivable text). Two attached hazards: §D-3, §D-4 | **NEW** |
| A-7 | Answered + hold-out legs; k′ | design §3; C9 | — | k′ = 30 named constant; absent leg = max cosine over first k of NON-source hits from the k′ capture; **all-source-hits probe contributes NO absent sample (dropped AND counted, never a synthetic 0.0)**; ≥30 minimum evaluated AFTER drops. Demand the all-source-hits fixture | **NEW** |
| A-8 | Self-retrieval match key (C13) | C13; Q4.3 | **`Candidate.key` already IS the bare `uuid5` point id** (`store/candidate.py`) — measured. 11-i-a shipped **no** change to `candidate.py` | add `point_id` to `HitCapture` (measured absent) and to `_write_jsonl`'s per-hit dict (measured absent). CHUNK-scoped match; file-path matching is NOT self-retrieval. Two-chunks-one-file fixture | **PORT + NEW** |
| A-9 | **The measurement row's remaining fields** | see §B-6 for the full derived gap list | 14 columns only: `head_identity, head_revision, state, non_adoption_cause, note, floor, ci_low, ci_high, adopted_n, instrument_version, corpus_content_digest, embedding_schema_fingerprint, trigger, created_at` | **~12 fields the rulings require are ABSENT.** b must add them (`DEFINE FIELD OVERWRITE` — the additive valve Q4.2 promised) AND populate them. **This edits an 11-i-a-owned file → operator fork** | **NEW** |
| A-10 | Bootstrap / interval machinery | D1; `RULINGS-2026-07-26-bootstrap.md` R-A…R-H | numpy/scipy/sklearn declared + locked (§E) | `scipy.stats.bootstrap` with **two index samples, `paired=False`**; statistic gathers both legs from group 1's drawn indices; **served interval = `np.percentile(.bootstrap_distribution, [5,95], method="inverted_cdf")`, NEVER `result.confidence_interval`**; explicit `method="percentile"`, `vectorized=False`, `batch=<pinned>`, `confidence_level=0.90`, `n_resamples>=1000`, `rng=` | **NEW** |
| A-11 | The D.1–D.10 bootstrap pin suite | `REPORT-probe-bootstrap-paired.md` §D | — | ten pins, each naming the wrong build it kills. **D.2 must instrument what the statistic RECEIVED — a CI-endpoint pin is measured identical on 21/30 corpora** and waves the wrong build through. D.5 = allowlist-the-safe AST pin (exactly one function may call `scipy.stats.bootstrap`). D.6 = byte-identical determinism, in-process AND subprocess, with a failing control. D.7 needs a CONTINUOUS leg | **NEW** |
| A-12 | ROC-path selection (decision 20) | R9.1–R9.3; ruling 20 = **THE ORACLE** | — | `sklearn.metrics.roc_curve`-derived selection becomes the ONE production path; `choose_cosine_floor` retained as executable SPEC + test ORACLE; the byte-exact equality pin re-derives agreement over randomised inputs every suite run | **NEW** (retires PORT code) |
| A-13 | The 30–49 ladder-generating function | ruling **E4** — explicitly b's | store-side pinned: `corpus_meets_validity_floors(...)`, `MIN_ANSWERED_PROBES=30` / `MIN_IDENTIFIER_PROBES=15` / `MIN_ABSENT_SAMPLES=30`, and `adopted_n` recording the ACTUAL adopted subsample size | `[50,100,200,400,…]` truncated at pool size, final rung = pool size. **Unowned and unpinned today** — nothing reddens if it snaps `adopted_n` to a nominal rung (§D-13) | **NEW** |
| A-14 | N-curve + ≥98% stability gate | D2; C2; C4 | — | denominator = every portable-union sample **WITHOUT a verbatim anchor** (ruling L1: anchored EXCLUDED, absent leg INCLUDED); nested first-N subsamples, RNG-free; record the anchored-excluded count in the row | **NEW** |
| A-15 | Paired decomposition (D4) | D4; C11 | — | fresh floor recomputed on the SURVIVING-probe subset (same `point_id` present AND unchanged probe-text sha) beside the full-pool floor; on a determinism re-run **surviving MUST equal full and paired floor MUST equal full floor** — a free discrimination fixture, pin it | **NEW** |
| A-16 | Probe manifest in-row (C11) | C11 | — | array of `(point_id, probe_text_sha512)` pairs over the run's answered pool, written in the same row-write. **No field exists** (§A-9) | **NEW** |
| A-17 | Cost capture (D5) + affordability receipt (R3.4) | D5; F-r2 §R3.4 | — | embeds + wall-clock per run; time one pool-scale call and record the projected ladder cost. **No field exists** | **NEW** |
| A-18 | Determinism control (E5's MUST-PROVE pin) | packet Exit; Q4.2 (*"lives in b … a must not be graded against a pin it cannot express"*) | — | prove an unchanged corpus reproduces bit-identically; **record WHICH leg held** (bit-exact vs within-CI). C1's rider: an arithmetic-replay control must run FIRST — a mismatch there is an arithmetic defect and may NEVER be recorded as the TEI leg | **NEW** |
| A-19 | The R2 verb | C7; §B (operator-ruled vehicle) | `python -m loremaster.index` is the in-repo precedent (`index/__main__.py` + `index/cli.py`) | `python -m loremaster.<floor_module>`; **NOT an MCP tool** (registering one changes a served byte via `test_instructions_names_every_tool`); **NO default store coordinate, refuses without an explicit one**; receipt prints `loremaster.__file__`, the store URL, and the run's corpus fingerprint | **NEW** |
| A-20 | R2 executes the COMPLETE engine path (C6) | C6; Q4.3 (*"b's verb must call them, never re-implement"*) | `FloorCalibrationStore.record_measurement(...)`, `.read_adopted_head(...)`, `.measurement_history(...)`, `.ensure_ready()`; `SurrealLeaseStore`, `SurrealLeaderLock`, `lease_election_config(...)` | measure → validity gates → adopt-or-decline → head mint. **b must call `ensure_ready()` on BOTH slices** — ruling O3 forbade the floor store from emitting the lease DDL (§D-1) | **NEW** |
| A-21 | The C6(a)–(f) evidence package | C6; C5 (address) | — | committed under `docs/plans/v2/receipts/<run-date>-packet11i/` in the SAME change as the run receipts; every citation uses that tracked path. Detail in §F | **NEW** |
| A-22 | C14's reconciling sentence | C14 | — | one sentence: steady-state runs embed O(adopted-N); the R2 run ALONE embeds the full derivable-text pool once, embed count + wall-clock in the row, ladder extends to pool size | **NEW** |
| A-23 | `--max-embeds` (required, no default) | F-r2 §R3.5 (SURVIVES UNCHANGED) | — | required CLI argument, no default | **NEW** |
| A-24 | Identifier probes have no hold-out leg | ruling **R-F** | — | **one line in the contract** saying so, plus the note that the expression generalises to N index samples with `paired=False` | **NEW** |
| A-25 | The #180 rider (C6f) | packet Exit ¶2; C6(f) | — | per-hit cosine distribution + over-flag decomposition from the run's own jsonl (zero extra embeds). **If it cannot be done, say so — do not synthesise it** | **NEW** |

**The "50 tests" figure is inherited and stale.** Measured: `scripts/test_search_score_survey.py` collects
**53** at base `2b8aa01` (`pytest --collect-only -q` → `53 tests collected`). `git show b4eb32a:` (the scout's
commit) → 50 test defs; `git show c7983e8:` → 53. The three additions are
`TestTheRealStoreFactoryBuildsSdkEncodableCredentials`, landed by `a265aff fix(#211)`. **And the "re-home
into the gate" half of that obligation is already DISCHARGED** — `scripts` is a `testpaths` entry at HEAD
(#199, closed `c9431ae`). What remains is the physical port, because `scripts/` is not in the image.

---

## B. THE INTERFACE FREEZE, AS IT ACTUALLY SHIPPED

Read from the tree, not from `REPORT-contract-11ia-1.md` §1. Every symbol below was verified to exist.
**All bodies are real implementations — no `NotImplementedError` survives.**

### B-1 `loremaster/loremaster/floor_calibration/domain.py` — pure, no I/O

| symbol | shipped signature / value | real or stub |
|---|---|---|
| `FLOOR_HEAD_ALWAYS_SERIALISED_AXES` | `tuple[str,...] = ("scope","statistic")` | real |
| `FLOOR_HEAD_DEFAULTED_AXES` | `Mapping[str,str] = MappingProxyType({"query_shape":"any"})` | real |
| `MIN_ANSWERED_PROBES` / `MIN_IDENTIFIER_PROBES` / `MIN_ABSENT_SAMPLES` | `30` / `15` / `30` | real |
| `corpus_meets_validity_floors` | `(*, answered_probes:int, identifier_probes:int, absent_samples:int) -> bool` | real |
| `head_identity` | `(axes: Mapping[str,str]) -> str` — `sha512_hex(orjson.dumps(serialised, option=OPT_SORT_KEYS))`. Raises `ValueError` on **three** fates: missing required axis · unregistered axis name · **non-`str` value**. No separator-refusal clause (JSON escapes NUL) | real |
| `corpus_content_digest` | `(rows: Iterable[Mapping[str,Any]]) -> str` — orjson over a LIST OF PAIRS `[point_id, content_hash]`, ascending-id walk. Subscripts (never `.get`) so a missing key is a loud `KeyError`. Empty corpus → DEFINED digest | real |

### B-2 `loremaster/loremaster/floor_calibration/store.py`

```
class FloorCalibrationError(SurrealStoreError)
class FenceLostError(FloorCalibrationError)

@dataclass(frozen=True) class LeaseFence(holder_identity: str, fence_epoch: int)
@dataclass(frozen=True) class AdoptedHead(head_identity: str, axes: Mapping[str,str],
                                          measurement_id: str, revision: int, adopted_at: datetime)
@dataclass(frozen=True) class MeasurementReceipt(measurement_id: str, head_identity: str,
                                                 adopted: bool, head_revision: int | None)

class FloorCalibrationStore:
    __init__(self, *, url, namespace, database, user, password: SecretStr) -> None   # opens NOTHING
    async ensure_ready() -> None                       # THIS SLICE ONLY — not the lease slice (O3)
    async record_measurement(*, axes: Mapping[str,str], measurement: Mapping[str,Any],
                             adopt: bool, fence: LeaseFence | None = None) -> MeasurementReceipt
    async read_adopted_head(axes: Mapping[str,str]) -> AdoptedHead | None
    async measurement_history(axes: Mapping[str,str], *, limit: int) -> list[Mapping[str,Any]]
    async close() -> None
```
All real. Ctor keywords **must** stay `url/namespace/database/user/password` — `test_retry_seam._CTOR_VALUES`
supplies exactly those, and the class is AST-discovered as an `async def _query` owner.

### B-3 `loremaster/loremaster/store/lease.py`

```
LEASE_DURATION_SECONDS = 15 ; LEASE_RENEW_DEADLINE_SECONDS = 10 ; LEASE_RETRY_PERIOD_SECONDS = 2
LEASE_LOCK_NAME = "lore-maintenance" ; LEASE_LOCK_NAMESPACE = "lore"

class LeaseError(SurrealStoreError)                       # ⚠ RAISED BY NOTHING — see §D-14
@dataclass(frozen=True) class LockAbsent(...)             # _lock_absent() / _lock_unavailable(msg)
@dataclass(frozen=True) class LeaseObservation(holder_identity, lease_duration, acquire_time,
                                               renew_time, revision, fence_epoch)

class SurrealLeaseStore:
    __init__(*, url, namespace, database, user, password) ; ensure_ready() ; close()
    async read() -> LeaseObservation | None
    async create_if_absent(*, holder_identity, lease_duration, acquire_time, renew_time)
                                                            -> LeaseObservation | None
    async compare_and_set(*, observed_revision: int, holder_identity, lease_duration,
                          acquire_time, renew_time) -> LeaseObservation | None
    async release_if_held(*, holder_identity: str, fence_epoch: int) -> bool

class SurrealLeaderLock:                                   # SYNC six-member adapter
    __init__(*, store, identity, loop, name=…, namespace=…, call_timeout_seconds=…)
    get(name, namespace) -> tuple[bool, Any]
    create(name, namespace, election_record) -> bool        # keyword name is INTERFACE
    update(name, namespace, updated_record) -> bool         # CASes on the revision from the LAST get
    @property fence_epoch -> int | None                     # updated after EVERY successful write
    release_if_held() -> bool ; stop() -> None

def lease_election_config(*, lock, on_started_leading, on_stopped_leading) -> Any   # kubernetes Config
```
All real. `lease_election_config` passes all three tunables **explicitly** because `Config` has no
defaults and **validates by calling `sys.exit`** — an illegal triple raises `SystemExit`, not `ValueError`.

### B-4 `loremaster/loremaster/store/surreal.py` (appended)

```
CALIBRATION_POOL_COLUMNS: tuple[str,...] = ("point_id", "content_hash")
class CalibrationPoolError / CalibrationPoolTruncatedError / CalibrationPoolCountMismatchError
@dataclass(frozen=True) class CalibrationPool(rows, counted_total, limit)
async def SurrealStore.enumerate_calibration_pool(self) -> CalibrationPool
```
Real. Issued limit = `counted_total + 1`. `ORDER BY` is on the **projected alias** `point_id`, never `id`.

### B-5 `loremaster/loremaster/store/surreal_schema.py` (appended)

`FLOOR_MEASUREMENT_TABLE="floor_measurement"` · `FLOOR_HEAD_TABLE="floor_head"` ·
`LEASE_TABLE="lease"` · `LEASE_SINGLETON_ID="singleton"` · `FLOOR_STATES` (8, closed) ·
`FLOOR_NON_ADOPTION_CAUSES` (5, closed) · `FLOOR_MEASUREMENT_COLUMNS` (14) ·
`generate_floor_calibration_ddl()` · `generate_lease_ddl()`. All real and populated.

### B-6 ⚠ WHERE THE SHIPPED CODE DIVERGES FROM `REPORT-contract-11ia-1.md`

**A report is a claim; the tree is the measurement.** Six divergences, all measured:

1. **§1.6 claims `floor_measurement` carries the queryable axis columns `statistic` / `scope` /
   `query_shape`. IT DOES NOT.** Measured `FLOOR_MEASUREMENT_COLUMNS` has no axis column; the axis
   columns live on `floor_head`, derived from `FLOOR_HEAD_ALWAYS_SERIALISED_AXES`. *Consequence for b:*
   **you cannot query the measurement history by scope or statistic without going through
   `head_identity`.** `measurement_history(axes, limit=…)` is the only supported path.
2. **§1.6 claims `floor_measurement` carries "the F7.2 degeneracy telemetry". IT DOES NOT.** `grep
   degenerac` over the schema + package returns 2 hits, both prose comments; no field.
3. **§1.6 claims `floor_measurement` carries "the F2/R2.5 sensitivity floor". IT DOES NOT.** `grep
   sensitivity` → 0 hits.
4. **The bootstrap rulings' row obligations are ABSENT.** Ruling **R-G** states in terms *"This is an
   11-i-a row-shape obligation"* for `scipy.__version__` / `numpy.__version__`; ruling **R-C** requires
   `batch` **RECORDED in the measurement row**. Measured: `scipy_version` 0 hits · `numpy_version` 0
   hits · `n_resamples` 0 hits · no `B` · no bootstrap `method` field. The `batch` grep hit is an
   unrelated comment at `surreal_schema.py:579`. **The R-G/R-C rulings landed 2026-07-26 and never
   reached the schema.** This is the RIDER-IS-PART-OF-THE-RULING class, verbatim.
5. **§1.1 says the two closed tuples "ship EMPTY in the stub."** They are now populated (8 states, 5
   causes) — the stub state is historical. Cite the tree, not §1.1.
6. **`REPORT-builder-11ia-1.md` deviation 1 says `head_identity` shipped as `option<string>`, not the
   REQUIRED column ruling O7 ordered. THAT IS STALE.** Measured at `2b8aa01`:
   `(FLOOR_MEASUREMENT_HEAD_IDENTITY_COLUMN, "string", "")` — REQUIRED. The audit fix wave (`675aab5`)
   closed it. Do not carry the builder's deviation forward.

**The derived field gap (deliverable A-9), each with its ruling:**

| missing field | required by |
|---|---|
| `scipy_version`, `numpy_version` | **R-G** (named an 11-i-a row-shape obligation) |
| `batch` | **R-C** / **D.9** |
| `B` (n_resamples), bootstrap `method` | **D1** ("reports floor_point, ci_low, ci_high, N, B, method"), **D8** pre-registration |
| probe manifest `(point_id, probe_text_sha512)[]` | **C11** |
| measured sensitivity floor | **R2.5 / F2** |
| paired-decomposition floor + surviving-subset size | **D4** |
| run cost: embeds, wall-clock | **D5**, §7 persistence |
| anchored-excluded count | **C2** |
| bars used; results (false-fire rate, hold-out catch, n per group, substrate spread median, self-retrieval drop-rate) | **§7 persistence**, **R3** |
| corpus snapshot: file/chunk/per-tier counts | **§7 persistence** |
| degeneracy telemetry | **F7.2** (per contract §1.6's own claim) |

Q4.2 pre-authorised the escape valve — *"B4's OVERWRITE rule is the additive escape valve if b discovers
a gap, and the contract SAYS so"* — but **exercising it means b edits `store/surreal_schema.py`, which
Q4.1 assigns to `a`.** That is decision-needed #1. Store law: FIELD → `OVERWRITE`; the existing
`floor_measurement_head_created` INDEX rides `IF NOT EXISTS` and must never be `OVERWRITE`.

---

## C. THE OPEN DECISIONS — every number, its own line, its own verdict

### C.1 The 23 (Addendum F's thirteen + F-r2's ten additions)

Ruling file of record: `docs/plans/v2/receipts/2026-07-24-packet11i/RULINGS-2026-07-25.md`.

| # | subject | status | gates b's contract? |
|---|---|---|---|
| **1** | F1+F2 adopted-N rule + calibrated bound | **RULED** — ADOPT (`RULINGS-2026-07-25.md` §2, "engineering; measured twice blind") | yes — b builds it |
| **2** | The ≥98% gate's sample population (Addendum-F "F3 denominator fork") | **RULED** — **R-PACKAGE**: anchored samples EXCLUDED, absent leg INCLUDED (`RULINGS-2026-07-25.md` §1 **L1**, a marked LEAD CALL; operator asked for detail, detail supplied there). Named re-open trigger: R2's real data | yes — decides A-14's denominator |
| **3** | F4 states + the 30–49 join | **RULED** — ADOPT (§2). Split further by **E4**: store side in `a`, ladder generator in **b** | yes — A-13 |
| **4** | F5 cause enum + two-degeneracy split | **RULED** — ADOPT (§2, P6) | no — shipped in `a` |
| **5** | F6 `head_identity(axes)` + reserved `query_shape` | **RULED** — ADOPT (§2, P2) | no — shipped in `a` |
| **6** | F7 pins, including the explicit drop | **RULED** — ADOPT (§2) | partly — b carries the surviving pins |
| **7** | F8's eleven surviving adjudications | **RULED** — ADOPT (§2, P0). C1 re-worded library-neutral; C7 re-homed to R4/R6; C14 VOID | yes — F8-C1's seed discipline is A-10/A-18 |
| **8** | C8 narrowed store projection inside `DEPLOY: no` | **RULED** — AUTHORIZE as an 11-i-a addition (§2, P0 "ruling to intent, not to letter") | no — shipped |
| **9** | C11 manifest size bound | **RULED** — ADOPT (§2, "measure-then-tune with a named decision point") | yes — A-16 |
| **10** | C13 bar re-registration point | **RULED** — ADOPT (§2; decision point named at **R2 review**, i.e. inside b) | yes |
| **11** | F9 bootstrap implementation | **RULED VOID** — replaced by R3 + R9 (`scipy.stats.bootstrap` + `roc_curve`, equality-proven) (§2, P1) | yes — A-10/A-12 |
| **12** | §B vehicle provenance | **RULED** — INTERIM path-identical mount + fail-loud-on-null; END-STATE lore-owned worktree root + real git identity; **"No git bump."** (§2, P5 + measured M1/M3) | yes — A-19's receipt |
| **13** | The lease | **RULED** — `kubernetes.leaderelection` + SurrealDB lock adapter (§2, P1+P4) | yes — b is its only consumer |
| **14** | Adopt numpy + scipy via uv | **RULED** — ADOPT (§2, row "numpy / scipy adoption record", P1). **Landed `38c9774`** | no — done (§E) |
| **15** | Bump the image's git to ≥2.48 | ⚠ **NO OWN LINE IN `RULINGS-2026-07-25.md`.** MOOTED/re-dispositioned twice: F-r2 **§R8.1** (*"R4.3's 'bump MANDATORY' is void with it … the bump reverts to optional hygiene"*) and decision **12**'s ruling text (*"No git bump."*). **Effective verdict: NOT ADOPTED.** But it is the one of the 23 with no numbered ruling — flagged so nobody reads its absence as an oversight in the other direction | no |
| **16** | Worktree-layout relocation + its config inventory | **PARTIALLY RULED** — §2's last row ADOPTs *"layout inventory"* under P3 (i.e. take the inventory). The **relocation itself** is explicitly still the operator's: §3.1, *"Whether packets 17/23 (worktree + index) are pulled ahead of 11-i's contract … the sequencing is a plan change, and plan changes are not mine."* | **no — deferrable.** b runs under the INTERIM (decision 12) |
| **17** | `StoreLease` tunables | **RULED** — **UPSTREAM DEFAULTS 15/10/2**, not the sidecar's 60/20/5 (§1 **L2**, ✅ OPERATOR-CONFIRMED *"use the defaults"*). Shipped verbatim as `LEASE_DURATION_SECONDS=15` / `10` / `2` | no — shipped |
| **18** | The R5 extraction plan | **RULED** — ADOPT (§2 last row, P3): lease in 11-i-a ✅ shipped; **loop helper (`MaintenanceLoop`) in 11-ii B7.3**; watcher re-home a later packet | ⚠ **see open item 3 below** |
| **19** | Adopt scikit-learn | **RULED** — ADOPT (§2, "P1, verbatim"). **Landed `38c9774`** | no — done |
| **20** | `choose_cosine_floor`: production path vs test oracle | **RULED** — **THE ORACLE** (roc-path production, `choose_cosine_floor` executable spec/oracle) (§2, P2) | yes — A-12 |
| **21** | BCa | **RULED** — **NOT ADOPTED**, kept as a named contingency (§1 **L3**, ✅ OPERATOR-CONFIRMED *"if you say so"*). ⚠ Carries a **lower-confidence flag**; re-open trigger = a coverage check failing on R2's real distribution | yes — forces explicit `method="percentile"` |
| **22** | Take the `kubernetes` dependency | **RULED** — TAKE IT (§2, P1 *"I don't care how big the container gets"*). **Landed `38c9774`** | no — done |
| **23** | The adapter's `release_if_held` | **RULED** — ADD IT (§2, P4). Shipped on both `SurrealLeaseStore` and `SurrealLeaderLock` | no — shipped |

**None of the 23 is OPEN in a way that blocks b's contract**, with the single caveat of #15's missing
line and #16's un-ruled relocation half (deferrable — b runs on the interim).

### C.2 The later ruling families (these DO gate b)

| id | subject | status |
|---|---|---|
| **E1** | `head_identity` pre-image encoding | **VOID** — *dissolved*, not overridden, by operator ruling **O1** (`orjson` + `OPT_SORT_KEYS`). Golden digest `c52fce03…daf148cf` re-pinned against the orjson pre-image |
| **E2** | Lost-fence classification mechanism | **RULED** — classify from store STATE, never message text. **Rider:** pin all three fates — fence moved · fence intact · re-read failed |
| **E3** | Library entry point | **RULED** — drive `try_acquire_or_renew()`, and pin the library surface. **Gates b directly** (§D-8) |
| **E4** | The 30–49 ladder function's home | **RULED — 11-i-b** [LEAD CALL] |
| **E5** | §7's `note` vs F5's `non_adoption_cause` | **RULED** — TWO DISTINCT FIELDS [LEAD CALL]. Carried obligation: `note` is stored FREE TEXT → sanitiser seam + hostile fixture the day anything renders it (11-ii, but b writes it) |
| **E6** | `CALIBRATION_POOL_COLUMNS` extension point | **RULED** — ratified as declared; **membership beyond `point_id`+`content_hash` is 11-i-b's to fix**, both hazards inherited (§D-3, §D-4) |
| **O1** | orjson identity encodings | **RULED (OPERATOR)** — supersedes E1 |
| **O2** | The 4 `test_retry_seam.py` entries | **RULED** — authorised explicitly in the build brief with values named. **b will hit the same shape** (§D-16) |
| **O3** | Lease-table fixture / cross-slice DDL | **RULED (b)** — the pin's fixture creates the `lease` table; **REJECTED**: the floor ledger emitting the lease slice. Third fate (table-absence re-read raises) gets pin M5 |
| **O4** | Retired-name sweep scope | **RULED** — delete the stub comment; widen the sweep to design docs or state+pin the bound |
| **O5** | M1–M14 all REQUIRED | **RULED** — M1–M4 BLOCKERS. Withdraws the lead's own "already pinned" clause on M9/M13 |
| **O6** | #238 `docs/eval` in testpaths | **DONE** (190 passed) |
| **O7** | `head_identity` REQUIRED on every measurement row | **RULED** [LEAD CALL] — shipped as `"string"` (verified §B-6.6). Re-open trigger: a genuine legacy corpus with head-less rows |
| **R-A** | Resampling unit | **RULED** — two index samples, `paired=False`. **`paired=True` cannot express it** |
| **R-B** | Seeding | **RULED** — `rng=`, never `random_state=`, never `None`. Allowlist-the-safe AST pin |
| **R-C** | Explicit bootstrap parameters | **RULED** — `method`, `vectorized`, `batch`, `confidence_level`, `n_resamples` all explicit **and asserted at the seam**; `batch` **RECORDED in the row** ⚠ (field absent — §B-6.4) |
| **R-D** | The served interval | **RULED** — `.bootstrap_distribution` + `np.percentile(method="inverted_cdf")`, never `result.confidence_interval`. **Rider: the pin MUST carry a continuous leg** |
| **R-E** | Hold-out leg's anchor flag | **RULED (a) RECOMPUTE** over the reduced hit set [LEAD CALL] → the paired unit carries **four** values. Re-open trigger: measure in R2 whether the two legs' anchors ever differ |
| **R-F** | Identifier probes' hold-out leg | **RULED** — carry one line saying they have none today; the expression generalises |
| **R-G** | Row records `scipy.__version__` + `numpy.__version__` | **RULED — ADOPT**, named an 11-i-a row-shape obligation ⚠ (field absent — §B-6.4) |
| **R-H** | Boundary fates | **RULED** — map scipy's <2-observation `ValueError` to `insufficient_corpus`; pin 0, 1, 2 for EACH group |

### C.3 GENUINELY OPEN, and each needs an owner

1. **The `floor_measurement` field gap** (§B-6). The rulings say b populates fields that do not exist,
   and adding them crosses the a/b assignment line. **Fix now vs. defer — the operator's call.**
   *Recommendation: authorise b to extend `surreal_schema.py` for these fields, explicitly, in its brief
   (the O2 precedent — pre-authorise and name the values), rather than leaving a builder trapped.*
2. **Decision 15 has no numbered ruling line** — only the two re-dispositions. Cheap to close: one line.
3. **⚠ THE LEADER-ELECTION THREAD LIFECYCLE IS UNASSIGNED.** `REPORT-contract-11ia-1.md` §1.4 states
   *"11-i-a owns no thread lifecycle — that is 11-ii/R5."* F-r2 §R5 puts `MaintenanceLoop` in **11-ii
   B7.3**, justified by *"11-i has no loop consumer (the verb is one-shot, synchronous)"*. But R10.3
   specifies the election must run in **ONE dedicated thread owning a PRIVATE event loop and a PRIVATE
   store connection**, with a cooperative-poison shutdown — and b's R2 verb is the **first and only**
   consumer of `SurrealLeaderLock` + `lease_election_config`. Either b builds a one-shot election
   harness (thread + loop + `call_soon_threadsafe` bridge + `stop()` + `release_if_held`), or b's verb
   runs **without single-flight**. **Neither is written down anywhere.** Per CLAUDE.md's routing rule
   this is a **property to INVENT, not a spec to IMPLEMENT** → it escalates as a design fork, it does
   not go to a builder with "figure out the general form".
   *Recommendation: rule explicitly whether the R2 one-shot verb takes the lease at all. A one-shot
   manual verb arguably needs no leader election — but that is a RULING, not a builder's shortcut, and
   C6 says the verb executes the COMPLETE engine path.*
4. **`adopt=True` on a non-`measured` state is NOT refused** (builder item 6, flagged-not-built
   *"adding an unpinned refusal risks a false gate for 11-i-b's runner"*). b can silently adopt a
   `measuring` or `insufficient_corpus` row.
5. **The pool's `counted_total + 1` margin** classifies ordinary corpus GROWTH as
   `measurement_failed` rather than the gentler count-mismatch/discard-requeue. Builder: *"If the lead
   wants growth classified as a mismatch, that is a ruling plus a fixture change, not a builder tweak."*
6. **`LeaseError` is declared by the frozen interface and raised by nothing** — dead surface or 11-ii's
   raiser. Builder flagged it, refused to delete a frozen member.
7. **#242 / builder E-4** (connection-glue duplication) is OPEN and unowned. b will add socket owners.

---

## D. INHERITED HAZARDS AND TRAPS

Each line ends with *what it does to a builder who doesn't know it.*

**⚠ D-0 — THE META-HAZARD, verified myself.**
`docs/plans/v2/receipts/2026-07-26-packet11i-build/REPORT-contract-11ia-1-fixwave.md` contains a literal
**NUL byte**; `file(1)` reports `data`; **plain `grep -n '11-i-b'` on it exits 1 with no output**, while
`grep -an` returns line 137 — a block titled *"Carried, unchanged, for 11-i-b's brief"*. Reproduced by me
at `2b8aa01`. → *You grep the receipts while writing b's brief, get a clean-looking result set, and
silently omit the one paragraph written expressly to be copied into it. (It also carries the ONLY mention
in the packet of E5's `note`-is-free-text sanitiser obligation.)* **Every sweep of these receipts must use
`grep -a`.**

**D-1 — The `ensure_ready` gap binds b, not just 11-ii.** The INDEX's *"11-ii MUST INHERIT (audit R2)"*
note reads: *"the slice has ZERO production consumers, so the store law is satisfied only VACUOUSLY —
wiring a writer without its `ensure_ready` gives an undeclared-table conflict storm, and for `lease` an
undeclared-table READ THAT RAISES."* **It binds b as well, and more directly.** Measured: `grep` for
`FloorCalibrationStore`, `SurrealLeaseStore`, `SurrealLeaderLock`, `enumerate_calibration_pool`,
`lease_election_config` outside tests returns **zero production call sites**; `SurrealStore.ensure_ready`
emits `generate_ddl(...)` only — **not** the floor or lease DDL; and ruling **O3** explicitly rejected the
floor store emitting the lease slice. **b's R2 verb is the first production writer**, and it must call
`FloorCalibrationStore.ensure_ready()` **and** `SurrealLeaseStore.ensure_ready()` itself. → *Your first
real run against `:18500` gets an undeclared-table conflict storm on write and a hard `NotFoundError` on
the lease read.*

**D-2 — The `SELECT *` hazard INVERTED; carry the NEW fact.** Three reports disagree in commit order:
adversary §12 residual 2 (*"latent trap for 11-i-b; flag in its brief"* — `SELECT *` omits a `NONE` column
→ `KeyError`, *"it works only because the fixture always sets `floor`"*) → contract-fixwave §6 repeats it
verbatim (`e8aa8f4`, NUL-hidden) → **builder §2 item 8 (`7acbef4`, later) RETIRES it**: `measurement_history`
ships an EXPLICIT projection, so **an unset column reads `None` and does NOT raise**, and *"11-i-b's brief
should carry the *new* fact, not the old hazard."* Verified in the tree: the shipped method projects
`FLOOR_MEASUREMENT_COLUMNS` + `record::id(id) AS measurement_id`. → *You write defensive `KeyError`
handling for a hazard that is gone, and miss the new one — a not-yet-populated column silently yields
`None` and propagates a null floor into a measurement.* **The failure direction flipped from LOUD to SILENT.**

**D-3 — E6 hazard 1: adding an `option<>` column under an explicit projection reads a missing column as
`None`, silently**, where `SELECT *` omits it and raises `KeyError` (store reference §2's asymmetry). →
*You extend `CALIBRATION_POOL_COLUMNS` (A-6), the column isn't populated on older chunks, every row reads
`None`, no error, wrong pool.*

**D-4 — E6 hazard 2: under an explicit projection, `ORDER BY id` requires `id` IN the projection or the
statement is a PARSE ERROR** (*"Missing order idiom `id` in statement selection"*, store reference §7,
probed 2026-07-25 and re-confirmed 2026-07-26). → *You add `ORDER BY id` for determinism and get a
runtime SurrealDB parse error, not a test failure.*

**D-5 — `record::id(measurement)` on a NONE column RAISES** (*"Expected `record` but found `NONE`"*,
builder probe P7). An un-adopted head is a legitimate, constant state. → *Your head read blows up on
every un-adopted head; the head read must project the RAW link and coerce in Python.*

**D-6 — `floor_head.revision` is the ONE required column, and only the mint's `??` rescues a legacy row.**
Fixwave §2.2: *"a legacy row IS write-poisoned for any write that does not set it, and the only reason
nothing breaks is that every production write is the mint, whose `(revision ?? 0) + 1` sets it — the `??`,
not the `DEFAULT`, is the rescue."* b is a candidate SECOND writer. → *Any head-write path you add that
does not set `revision` write-poisons every existing row, and the `DEFAULT` will not save you.*

**D-7 — Every schema guarantee you inherit is a VIRGIN-DB guarantee.** Closure §7.4: the O7 pin proves the
column is required on a fresh database and *"cannot prove a dirty-store migration of this column."* → *The
moment b's engine runs against a store that already carries `floor_measurement` rows, none of the
migration proofs apply — and that is exactly what the R2 vehicle does on `:18500`.* (#107's shape.)

**D-8 — `LeaderElection.run()` BLOCKS FOREVER with no stop mechanism.** Ruling **E3**: drive the public
single-attempt `try_acquire_or_renew()` instead; a contract calling `run()` could never assert a FOLLOWER's
outcome. Borders #209's private-internals class; the library surface is pinned so an upgrade reddens here.
→ *You call the documented entry point and your runner hangs forever on a lost race instead of setting the
coalescing flag and returning.*

**D-9 — A CI-endpoint pin does NOT discriminate the pairing mechanism.** Measured over 30 corpora at B=400:
the correct expression and the arm-independent one give **identical CI endpoints on 21 of 30**. → *You
write the obvious assertion, it goes green, and you ship a bootstrap that resamples the arms independently
— undetectable by your own suite on 70% of corpora.* **Instrument what the statistic RECEIVED.**

**D-10 — Three scipy defaults are silent traps.** `method` defaults to **`BCa`** — which decision 21 rules
out — and returns a materially narrower interval **with no warning**. `vectorized` is inferred from whether
your statistic merely *names* a parameter `axis`, so a harmless refactor changes the contract silently.
`batch` changes the answer whenever there is more than one sample (measured: CI moved on 6/25 corpora).
→ *An unnamed parameter ships an interval the design pre-registered against, and nothing warns.*

**D-11 — `rng=` and `random_state=` are NOT aliases**, and a third silent stream exists:
`rng=np.random.RandomState(3)` is **accepted** on numpy 2.5.1 and yields a distribution different from both.
The decorator's own docstring reads as though this is rejected; measurement falsifies that. → *A determinism
pin that only bans `random_state=` misses the third door. Allowlist the safe seam instead.*

**D-12 — The interval-convention fixture must carry a CONTINUOUS leg.** The floor statistic is discrete, so
`linear` and `inverted_cdf` coincide on **24/25 corpora**. → *A discrete-only fixture waves through a build
that serves `result.confidence_interval`.*

**D-13 — The ladder-generating function is unowned and unpinned** (E4 assigns it to b; nothing pins it).
The store-side pin `test_adopted_n_is_NOT_snapped_to_a_ladder_rung` forbids snapping. → *Nothing reddens
if your generator snaps `adopted_n` to a nominal rung until that one store pin fires.*

**D-14 — `LeaseError` is raised by nothing.** The store seam raises the `_txn` types; the lock reports
failure through the library's boolean / `LockAbsent` channel. → *You write `except LeaseError:` around
lease acquisition and catch nothing, ever.*

**D-15 — `test_a_non_adopted_receipt_carries_no_head_revision` does not guard what its name says.** Fixwave
§5, on the record: it stayed GREEN under a mutation and *"only guards the receipt, which is gated
separately."* → *You treat it as head protection and ship an unguarded head path.*

**D-16 — `test_retry_seam.py` carries hand-written dicts no production code can satisfy.** Ruling **O2**
had to pre-authorise four entries by value for 11-i-a, because the two moves a trapped builder makes are
both catastrophic (invent a bespoke seam that falls OUT of the enumeration = #120 verbatim; or declare the
reds "pre-existing"). **b will add socket owners and hit the same shape.** → *Your brief must pre-authorise
the `_SEAM_REJECTION_EVENTS` / `_SEAM_REJECTION_NOUNS` entries and name the values, or you will be trapped.*

**D-17 — Your collected-test count CHANGES AS YOU BUILD.** `test_retry_seam.py` collects 559 against a stub
and **561** against a correct build, because `_discover_socket_owners` only sees a class whose
`_ensure_connection` actually constructs a socket. → *A count-based gate disagrees with itself before and
after your production code lands.*

**D-18 — #242: a naive extraction of the connection glue BLINDS the enumeration covering it.** Any
extraction must ship WITH a re-keyed discovery mechanism in the same diff, with the discovered-owner count
as a CHECKED variable. **And every socket-owner count in these reports is contested** — the cold audit (F7)
withdrew "twelve" as un-derived and named three distinct populations. → *You DRY the glue and the
double-checked-lock guard silently goes vacuously green; or you quote "twelve" and carry a false number.*

**D-19 — #237's reproduce recipe cites files that DO NOT EXIST.** Its body names
`scripts/survey_stats.py` and `scripts/test_survey_stats.py`; measured: neither is in the tree. The #198
consolidation (`ea7406e`) landed at **`loremaster/loremaster/stats.py` + `loremaster/tests/test_stats.py`**
(three placement passes — `scripts/` → reverted → installed package). Its closing note *"docs/eval/ is NOT
in testpaths"* is also stale (#238/O6 added it). → *You run the ledgered mutation proof verbatim, it fails
on a missing path, and you cannot tell whether the pin or the recipe is broken.*

**D-20 — #241 is an OPEN STOP under b's runner.** An unreproduced 2-of-114 contention failure
(`28 failed / 168 passed`, led by `TestTheHeadMintUnderContention::test_no_adoption_is_lost_under_contention[32]`);
112/114 green across five designed conditions; **the lead's own hunt #1 was ruled INVALID** (the tree moved
under it — a sibling agent was editing the files). → *A red contention test is NOT yours to call flaky —
a builder verdict this repo forbids outright.*

**D-21 — Both instruments b will reuse mis-parse** (cold audit R8, R12). `scripts/mutation_proof.py`
mis-reads a `Captured log call` line beginning `ERROR ` as a summary ERROR node id (loud-and-wrong, never
silent). `scripts/contention_hunt.sh` has an **unanchored `error` alternative** in its failure detector, and
derives its headline collected count by summing `N passed`/`N failed` regexes rather than from
`--collect-only`. → *Your #241 hunt reports failures that aren't, and its "checked variable" isn't checked.*

**D-22 — Mutation proofs and a running repeat-loop corrupt each other's evidence** (closure §7.3): five
mutation runs would have injected ~10 spurious REDs into the #241 loop and *"would have looked exactly like
the recurrence the loop is hunting."* → *Your brief must name a coordination step (stop the loop, or use
`scripts/scratch_copy.sh`) — not leave it to the agent to notice.* ⚠ **And `scratch_copy.sh` must NEVER be
run from a worktree (#185).**

**D-23 — Two natural landing places for b's code are ungated.** `scripts/` is outside
`scripts/typecheck.sh` (**#188**, measured 41 mypy errors there) → **no mypy coverage**. → *Anything b puts
in `scripts/` type-checks against nothing.* (Both `scripts` and `docs/eval` ARE in pytest `testpaths` — the
gap is mypy only.)

**D-24 — The mypy relaxation is scoped ON PURPOSE.** `pyproject.toml` carries `kubernetes.* →
ignore_missing_imports` and `disallow_any_unimported = false` **scoped to `loremaster.store.lease`** plus its
test module. Contract §7: *"if the builder lets `kubernetes` objects escape `loremaster/store/lease.py`, the
answer is to contain them, NOT to widen the override — escalate instead."* → *You let a `kubernetes` type
into your runner, mypy blocks you, and the obvious fix is explicitly forbidden.*

**D-25 — The retirement-marker sweep is a LIVE gate over design docs.** It scans `docs/design/*.md`,
`docs/plans/v2/*.md`, `docs/reference/*.md`; the quarantine's second half requires **every quarantined doc
to STILL be stale**, so an entry goes RED the day someone fixes it and must then be deleted. → *Any 11-i-b
design doc mentioning the retired state name reddens the gate; so does FIXING a quarantined doc without
deleting its entry.*

**D-26 — The archived S1 probe is a WRONG TEMPLATE.**
`receipts/2026-07-24-packet11i/probe_bootstrap_degeneracy.py::ProcedureBootstrap`'s docstring says
*"Resamples the union AND the absent arm JOINTLY"* while `one_replicate` resamples them **independently**.
Correct for the instrument it measured (a fixed nonsense-query absent arm); **wrong as a template** for the
portable hold-out instrument, whose absent arm IS the answered probes. → *You copy the one archived,
citable probe in the tree and reintroduce the arm-independent build D.2 exists to kill.*

---

## E. THE DEPENDENCY FACTS — MEASURED TODAY

**⚠ Measurement hygiene, disclosed:** this worktree had **never been `uv sync`ed** — there was no `.venv`
at all. A delegated agent's `uv run --no-sync` created an empty one and (correctly) reported everything as
NOT IMPORTABLE. **That reading is an artifact of the empty venv, not a dependency fact** (its control:
`pydantic` also read NOT IMPORTABLE). The venv is now populated and **I re-measured through it directly**.
Both readings are recorded so neither is laundered.

`loremaster.__file__` receipt: `/home/ejprice/PycharmProjects/lore-pkt11i-b/loremaster/loremaster/__init__.py`
— the worktree's own source, correct tree.

| package | `pyproject.toml` | `uv.lock` | importable TODAY (re-measured) | verdict |
|---|---|---|---|---|
| **numpy** | `loremaster` `>=2.5.1` | `2.5.1` | **2.5.1** | **IN** |
| **scipy** | `loremaster` `>=1.18.0` | `1.18.0` | **1.18.0** (`scipy.stats.bootstrap` callable ✅) | **IN** |
| **scikit-learn** | `loremaster` `>=1.9.0` | `1.9.0` | **1.9.0** (`sklearn.metrics.roc_curve` imports ✅) | **IN** |
| **kubernetes** | `loremaster` `>=36.0.3` | `36.0.3` | **36.0.3** | **IN** |
| **orjson** | `loremaster` `>=3.11` (DECLARED per O1, no longer transitive) | present | **3.11.9** | **IN** |
| **tenacity** | `loresigil` `>=9.0` | `9.1.4` | ✅ | **IN** (not adopted by 11-i) |
| **cachetools** | absent | **NOT PRESENT** | ✅ absent | **NOT IN** — see RAISED-5 |

**Commit `38c9774`**, subject verbatim: *`deps(11-i): adopt numpy, scipy, scikit-learn, kubernetes — ruled
decisions 19/22/14`*, dated 2026-07-26. It touched **`loremaster/pyproject.toml`** (not the root) — exactly
four added lines — plus `uv.lock` (+204). Decisions **14, 19, 22 are LANDED, not proposals.**

**The image gets them by construction:** the `Containerfile` never names them; line 83 is
`RUN uv sync --locked --all-packages`, and `--locked` fails the build on a stale lock.

**⚠ Still PROPOSED, never adopted:** F-r2 §R10.3's *"vendoring the module is rejected by name"* stands;
nothing else in F-r2 §R3/§R9/§R10 remains un-landed on the dependency axis.

**Two dependency facts nobody has recorded:**
- **`scipy` and `scikit-learn` are declared and locked but IMPORTED NOWHERE in shipped code or tests.** A
  repo-wide grep outside `.venv` hits only an archived probe. They were adopted ahead of the code that
  uses them — which is 11-i-b's. Nothing is wrong; but any "the dependency works here" claim is currently
  unbacked by a single import, and b is the thing that will first prove it.
- The `Containerfile`'s binary-wheel audit comment (lines 12–15) predates `38c9774` and does **not** name
  numpy/scipy/scikit-learn — the three largest, most wheel-fragile additions. It still names Qdrant, which
  `04879f7` retired.

---

## F. THE CONSUMER-FACING SURFACES OF 11-i-b

The packet is dark, but three things are read by an LLM or a human.

### F-1. R2's C6(a)–(f) evidence package (design Addendum C §C6; address = **C5**)

| leg | specified shape | typed field behind it? |
|---|---|---|
| **(a)** two floors + selection receipts | F_legacy and F_portable, each with `choose_cosine_floor` output (false-fire rate, catch rate, n), plus both pre-registered acceptance legs (F_portable false-fire vs the HUMAN-labeled union ≤5%; legacy-nonsense catch at F_portable ≥60%) | **⚠ NO** — no `false_fire`, `catch_rate`, `n_per_group`, or `bars_used` column exists (§B-6) |
| **(b)** per-group response-best cosine DISTRIBUTIONS | **n, mean, median, p5, p25, p75, p95, min, max** for six named groups + the per-query jsonl rows | **⚠ PARTIAL** — `GroupCosineSummary` ships only mean/median/p5/p95 for two distributions. **p25, p75, min, max are absent** and must be added |
| **(c)** verbatim-anchor rates per group | one rate per group | **⚠ NO field** |
| **(d)** probe texts side by side | ten deterministic self-supervised probe texts beside ten human questions | prose artifact — no field needed |
| **(e)** the adopted row's typed provenance fields **with real values** | rendered so W-C's derived clause can be judged as a SHAPE | **⚠ THIS IS THE ONE THE FIELD GAP HURTS MOST.** C6(e) is unproducible for any field that does not exist |
| **(f)** the #180 rider | per-hit cosine distribution + over-flag decomposition (best-hit vs mid-list, conditional on the response being answered), from the run's own jsonl, zero extra embeds. Two bounds stated: it measures the SURVEY's query mix, not live traffic; and serving-relevant stats use the SHOWN-k slice only | **feasible** — `HitCapture.vector_cosine` is captured for every hit and `_write_jsonl` persists it (verified). ⚠ `point_id` is NOT persisted and must be added (A-8) |

**Design law that makes this load-bearing** (Q5.0, verbatim): *"a render can rename, merge, or re-word
states after a consult; it **cannot render a distinction the row never recorded**."* Every row in §B-6's
gap list is a distinction 11-ii will not be able to serve.

### F-2. The R2 verb's provenance receipt and stdout (C7; §B's riders; decision 12)

Specified: prints **`loremaster.__file__`**, the **store URL**, and the run's own **corpus fingerprint**;
**refuses to run without an explicit store coordinate — no default of any kind** (A2's mistyped-coordinate
hazard: a wrong ns/db against production is silently MATERIALIZED as empty, not rejected). Riders per
decision 12: INTERIM path-identical mount + **fail-loud on `(None, None)` git identity**; `LORE_VERSION`
refuse-on-`unknown` as belt-and-braces; `loremaster.__file__` demoted to a namespace check. F8-C7 also
requires **all three coordinates explicit**. ⚠ **No typed field** carries the receipt — it is stdout plus
whatever b persists.

### F-3. The typed row fields b POPULATES

Shipped and populatable today: `state` (8, closed, ASSERTed) · `non_adoption_cause` (5, closed, ASSERTed,
**only on `measured_not_adopted`** per E5) · `note` (free text, mandatory unless `measured`) · `floor` ·
`ci_low` · `ci_high` · `adopted_n` (ACTUAL, never a nominal rung) · `instrument_version` ·
`corpus_content_digest` · `embedding_schema_fingerprint` · `trigger` · `head_identity` · `head_revision` ·
`created_at`.

**Specified only as PROSE, with no typed field behind it** — the answer deliverable F asks for:
all ~12 rows of §B-6's gap table, plus **Q5.2's typed-cause-fields pin**, which is the whole of what the
dark half owes the Consumer Law: *"every non-`measured` state's CAUSE and NEXT-MOVE datum is a typed row
field, never only prose — `insufficient_corpus` carries the three deficit counts; `measurement_failed`
carries the failed gate's name and value; `invalidated_remeasuring` carries the invalidating leg and the
queued-run status; `measuring`/`unmeasured` carry queued/started markers."* **Measured: none of those
fields exists.** The states are pinned; their causes are prose in `note`.

⚠ **And `note` is stored FREE TEXT** (E5's carried obligation, surviving only in the NUL-poisoned file):
the day anything renders it, it routes through the shared sanitiser seam and its tests carry a hostile
fixture (newlines + a row-shaped forgery line + backtick runs). Nothing renders it in 11-i — *which is
exactly why this is easy to forget.*

---

## G. SIZING RE-CHECK

**Not a decision — an input to one.**

**Inherited figures, each re-derived:**
- Packet file header: `size ~0.20 wu`. Its own ⚠ block says the INDEX re-splits to **11-i-a ~0.15 /
  11-i-b ~0.24**. ⚠ `0.15 + 0.24 = 0.39` against a header that still reads `~0.20` — **the header was
  never updated**. Raised, not fixed.
- F-r2 §R9.5 supersedes 0.29 with **~0.24 ± 0.03**. Its own arithmetic, re-derived: deltas from 0.29 are
  bootstrap −0.03, N-curve −0.01, paired −0.01, port −0.01, library +0.02 ⇒ **0.29 − 0.04 = 0.25**, stated
  as ~0.24. A 0.01 rounding slip, inside its own ±0.03 band. **Base: 0.25.**

**What §R9.5 could not have known** — it was authored **2026-07-25**; the bootstrap rulings and the
adversary rulings are **2026-07-26**, and 11-i-a merged **2026-07-27**:

| new cost | why it is new | est. |
|---|---|---|
| The **D.1–D.10 bootstrap pin suite** (instrumented-statistic pairing pin, AST allowlist seam, subprocess byte-determinism with a failing control, continuous-leg convention fixture, 3×2 boundary fates, dtype assert) | `RULINGS-2026-07-26-bootstrap.md` postdates §R9.5 by a day | **+0.03** |
| The **`floor_measurement` field gap** (§B-6): ~12 fields to spec, `DEFINE FIELD OVERWRITE`, migration pins, DDL text pins, plus populating each | measured against the merged tree, which did not exist on 2026-07-25 | **+0.03** |
| The **election thread lifecycle** (§C.3-3) | an unassigned straddle — and a DESIGN question, not a build item | **+0.02** |
| **R2 vehicle mechanics** (worktree image build + ephemeral container against `:18500`, run-after-cold-audit ordering, the decision-12 provenance riders) | §B's ruled vehicle; §R9.5's "R2 verb + C6 package (0.06)" prices the VERB, not the vehicle | **+0.02** |
| **R-E's recompute-the-anchor** (paired unit arity 3 → **4**) + its R2 re-open measurement | ruled 2026-07-26 | **+0.005** |
| `ensure_ready` wiring for BOTH slices (§D-1) | ruling O3 forbade the coupling | **+0.005** |

**Arithmetic:** `0.25 + 0.03 + 0.03 + 0.02 + 0.02 + 0.005 + 0.005 = 0.34`.

**Verdict: ~0.34, which EXCEEDS the ≥0.30 split clause** — by roughly the same margin that triggered the
original 11-i split. Honest bounds on that number: the +0.02 for R2 mechanics may partly double-count
§R9.5's 0.06 "R2 verb + C6 evidence package" line; even zeroing it entirely gives **0.32**, still over.
And the **+0.02 election-thread line is the least reliable of the six** precisely because it is a design
question — if the operator rules the one-shot verb takes no lease, it drops to ~0, giving **0.30–0.32**,
i.e. *at the line*.

**If a further split is ruled**, the natural seam from this inventory is **b-1 "port + probes + pool"**
(A-1…A-9, A-13) vs **b-2 "statistics + R2"** (A-10…A-12, A-14…A-25) — the same store/arithmetic character
line the a/b split already used, one level down. **The operator decides; this is the number and its
arithmetic.**

---

## RAISED (scope law — nothing here is dismissed, and none of it is mine to settle)

1. **I mutated the worktree, indirectly.** A delegated agent's `uv run --no-sync` created
   `/home/ejprice/PycharmProjects/lore-pkt11i-b/.venv`, which did not exist. It is gitignored and `git
   status` never showed it; it is now fully populated. **Recommendation: keep it** (the worktree needs a
   synced venv to build in anyway) — but it is a state change I did not have authority to make, so it is
   the operator's to accept or `rm -rf`.
2. **`BASELINE-11ib-full.txt` is untracked in this worktree, was being written DURING my run, and contains
   at least one `F` at ~75%.** Not mine. If it is a baseline capture for b, **the baseline is not green**
   — and a run whose tree is being read/written concurrently is the "measurement of a moving subject"
   failure that invalidated the lead's #241 hunt #1. Worth confirming before it is trusted.
3. **#237's ledger body is stale in two ways** (§D-19): it cites `scripts/survey_stats.py` and
   `scripts/test_survey_stats.py` — **neither exists** — and it says `docs/eval/` is not in `testpaths`,
   which #238/O6 closed. Its substance stands; its reproduce recipe does not run. Recommend a correcting
   note on the finding.
4. **A second inherited claim I RETRACT after reading the harness.** A delegated agent reported a "live
   defect": the `Containerfile` copies `pyproject.toml` (hence `testpaths` naming `scripts` and
   `docs/eval`) but copies neither directory, so the in-image conformance pytest would target paths that
   cannot exist. **Measured and wrong.** `skills/lore-deploy/scripts/conformance_run.sh` mounts the
   **whole repo** at `/workspace:ro`, `cd /workspace`, and runs the BAKED interpreter's pytest over the
   mounted tree — *"mount the TESTS, import the ARTIFACT"*, #139's design, with
   `conformance_provenance.py` asserting the members resolve to site-packages BEFORE pytest runs. So
   `scripts/` and `docs/eval/` are present at conformance time by construction. **No defect.**
   *One real residual, much smaller, left for whoever owns the image:* the `Containerfile`'s
   binary-wheel audit comment (lines 12–15) predates `38c9774` — it does not name numpy/scipy/
   scikit-learn (the three largest, most wheel-fragile additions) and still names Qdrant, which `04879f7`
   retired. Stale served English beside code, the class this repo instruments; one comment edit.
5. **`cachetools` — an inherited claim I RETRACT after reading the source.** A delegated agent reported
   this as "prose describing a mechanism that does not exist". **It is not.** Read in context
   (`SurrealStore`'s analyzer round-trip note): the sentence is an honest *deferral* — *"sizing/eviction
   it correctly (a bounded `cachetools.TTLCache`, not an unbounded dict) is real design surface with its
   own test coverage — deferred as a P6 optimization"*. It names the package it WOULD use, and claims no
   cache exists. `cachetools` is correctly absent from every `pyproject.toml`, from `uv.lock`, and from
   the venv (measured). **No defect. Recorded because the retraction is the point** — I nearly relayed a
   subagent's over-read as a finding, which is the class this repo has the most receipts against.
6. **The packet file header still reads `size ~0.20 wu`** while its own ⚠ block and the INDEX carry
   `~0.15 / ~0.24` (sum 0.39). One-line fix; left alone because the packet file is not my writable set.
7. **`_bare_id` / `_bare_record_id` — a probable further instance of the ONE-IMPLEMENTATION class, with
   the count DERIVED and its scoping stated** (per the #242 correction: state the enumerator's number at
   a named commit, or state both with their definitions).
   **Scoping:** `grep -rn 'def _bare_id\|def _bare_record_id' --include='*.py' loremaster/loremaster/` at
   `2b8aa01` — i.e. DEFINITIONS in production only, excluding tests and the `_bare_id_or_none` variant.
   **Result: 9 definitions in 9 modules** — `agents.py`, `messages.py`, `briefs.py`, `tasks.py`,
   `findings.py`, `store/surreal.py`, `memory/local.py` (all `@staticmethod _bare_id`), plus
   `floor_calibration/store.py`'s module-level `_bare_record_id` — which is 11-i-a's addition, and the
   one that spells it **differently**, exactly the shape that defeated the `async def _query` enumerator
   in #120. (`findings.py` also defines `_bare_id_or_none`; counted separately, not in the 9.)
   ⚠ This is a **DIFFERENT population** from #242's connection glue and from #120's `_query` seam — do
   not merge the three counts. Whether these 9 share one policy is a question I did not answer (I did not
   diff the bodies); the count is the derived fact, the duplication verdict is not.
8. **`REPORT-contract-11ia-1.md` §1.6 makes three claims about the shipped row that are false** (§B-6.1–3).
   The report is archived and citable, so a future agent will read those claims as current. Per archive
   law, it should get a one-line header note saying which claims the tree contradicts — I did not edit it.
9. **The NUL byte in `REPORT-contract-11ia-1-fixwave.md` (§D-0) is a repo-wide instrument hazard, not just
   this packet's.** Every archived receipt is meant to be greppable; one NUL makes a file invisible to
   plain `grep`, silently. **Recommendation: (a) strip the NUL from that file, and (b) add a cheap
   repo-wide invariant — no tracked `.md` contains a NUL byte — because "a guard nobody runs is a hope with
   a filename", and this one was found by accident.** The cold audit's R3 found the same class in a
   *different* file and it recurred here unnoticed.
