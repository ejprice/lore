# REPORT-contractfix-04b1-r4 — closing packet 04b-1's contract under THE HARD DEFINITION of trust

brief-base v7 read
brief project v7 read

*Every claim in this file is scoped to branch `feat/surreal-unification`, measured
**2026-07-28**. The pristine baseline is commit **`70cc5a4`** — "RED at `70cc5a4`" means RED
against that commit's PRODUCTION code with this contract applied. All live probes ran
against spike-surreal `ws://127.0.0.1:18000` (TEST); `:18500` was never touched. Every
number below was DERIVED here by collecting/running, including numbers inherited from
`REPORT-contractfix-04b1-r3.md`, `REPORT-contractfix-04b1.md` and
`docs/design/2026-07-28-04b-model-consumer-audit.md`.*

---

## SUMMARY BLOCK

- **state: done-with-deviations.** Every worklist item A–D dispositioned in §RESIDUALS; one
  deviation, four escalations, one finding filed.
- **A — RULING R11 (the blocker): ✅ PINNED**, SECTION K, **23 pins** across seven classes
  (20 from the worklist, +3 from the lead's ESC-4 ruling on legacy cycles):
  the exact-set backfill, the byte diff against the un-backfilled world, the terminal-row
  leg, the phantom skip + its RECORD + the no-false-skip control, the naked-backfill
  BASELINE + its positive control, idempotence (two legs, opposite failure modes), and the
  shared-policy MUTATION proof + two controls.
- **B — the Leg-2 FORGERY CONSTRUCTIONS: ✅ PINNED**, SECTION L. Traversal-store-failure
  (2 legs, byte-diffed) · the pre-check's degraded read on the WRITE path (3 legs,
  byte-diffed, `{empty}` and `{error}` treated as DIFFERENT modes) · its MIGRATION-time half
  (SECTION K) · the `{empty}`-mode one-level-down control (2 legs) · **R9's honest total
  resolves to an ASSERTED EMPTINESS** (2 legs, `test_query_tasks_bounded.py`).
  **No construction produced identical bytes. There is no false clear to STOP on.**
- **C — LEG-1 SCOPE DIFF: ✅ WRITTEN AND PINNED.** The per-surface table is in the module
  docstring (§THE TRUST DEFINITION, APPLIED TO THIS PACKET); the one difference that
  SURVIVES R11 — a legacy `blocked_by` naming no task row — is pinned as a docstring
  requirement (`TestTheScopeOfTheTransitiveReadIsSTATED`).
- **D — THE INTERIM BOUND: ✅ RECORDED AS A FACT**, twice, in the contract's own prose
  (module docstring + SECTION L header): `scripts/forgery_sites.py` does not exist, §11.1 is
  a curated interim bounded to five surfaces and one reader's sight, and a later false clear
  is a RE-OPEN TRIGGER, never a retroactive pass.
- **⚠ DEVIATION 1 — I CORRECTED TWO OF MY OWN CLASS DOCSTRINGS' STATED RED/GREEN COLOUR**
  before running anything, because I DERIVED the colour instead of asserting it. Both said
  *"green before and after"* and both were wrong. §COLOUR.
- **`Packages considered:`** the degraded-dependency constructions → `pytest`'s own
  `monkeypatch` + `unittest.mock` (**READ**: `_pytest.monkeypatch.MonkeyPatch.setattr`'s
  signature, and this repo's existing `_neutralise_the_policy`) → **replace** a hand-rolled
  patcher with `monkeypatch`, and hand-roll ONLY the *derivation* of which names to patch,
  which no library can know (`bespoke`, minimal surface: two `vars(module)` comprehensions)
  · log-record assertion → `pytest`'s `caplog` (**READ**: `conftest.py`'s
  caplog-propagation-restoring autouse fixture, which exists precisely so a caplog
  assertion is not at the mercy of test order) → **replace**, no bespoke capture · the
  absent-table read → `surrealdb.errors.NotFoundError` (**READ**: the raised type in the
  live traceback) → **`keep_with_trigger`**: caught by MESSAGE rather than by TYPE, because
  a typed import of an SDK error class in a test that must stay collectable under an SDK
  bump is the #133 shape; re-open if the SDK stabilises its error taxonomy.
- **decisions-needed: NONE OUTSTANDING.** I raised four (ESC-1..ESC-4) with both readings
  and a recommendation each; **the lead RULED all four at `92577f1` while this wave was
  still running**, and **I have implemented the two that changed the contract** — ESC-3
  (reading B: a failed pre-check is CLASSIFIED, not merely distinguishable) and ESC-4
  (reading A, NOW PINNED: the backfill MINTS legacy cycles and RECORDS them). §ESCALATIONS
  carries each escalation, its ruling, and what changed.
- **Pin counts, DERIVED by collecting `70cc5a4`'s files and mine (never inherited):**
  `test_blocks_edge.py` **149 → 175** · `test_query_tasks_bounded.py` **38 → 40**.
  **Contract total 187 → 215 (+28)** — 25 from worklist A–D, plus 3 from the lead's ESC-4
  ruling.
- **DECLARED vs OBSERVED RED, diffed BOTH ways:** node ids declared from `--collect-only`
  and written to disk **before any run**, measured in a provenance-asserted scratch copy
  against pristine `70cc5a4` production, and RE-DECLARED + RE-RUN after the lead's ESC-3/4
  ruling added pins. **Final: 22 declared RED → 22 fired · 0 unexpected reds ·
  0 declared-reds-that-stayed-green · 0 declared-greens-that-went-red** (6 declared GREEN,
  6 green). §DECLARED.
- **SATISFIABILITY RECEIPT:** *(pending — §X-SAT)*
- **Gates (repo tree, unpiped, exits captured separately):** `./scripts/typecheck.sh`
  **EXIT=0** · `uv run ruff check .` **EXIT=0**. §GATES.
- **`loremaster.__file__` receipts:** `/home/ejprice/scratch/cfix04b1r4-red/loremaster/loremaster/__init__.py`
  (RED baseline) · `/home/ejprice/scratch/cfix04b1r4-ref/loremaster/loremaster/__init__.py`
  (reference build).
- **Findings filed: #263** — §11.1's traversal-timeout row prescribes an error *"naming the
  timeout"* that the ledger provably CANNOT produce. §T-TIMEOUT.
- **⚠ A MEASUREMENT THAT CONTRADICTED MY OWN ASSUMPTION, and it cost 13 fixture errors to
  find:** on 3.2.1 a `SELECT` from a table that does not exist **RAISES**, it does not
  return `[]`. §MEASURED. Recorded in lore memory (`lore_recall("absent table select")`).

---

## §A — RULING R11: what is pinned, and what each leg kills

SECTION K of `test_blocks_edge.py`. The fixture is `legacy_column_store`: the OLD DDL
applied (no `blocks` table at all — production's measured state at 04b's kickoff), then
`_seed_legacy_task` writing the 4-deep branching diamond as COLUMNS ONLY, plus a
phantom-bearing row and a TERMINAL-status row. The instrument existed; per S3's own words it
"was simply never pointed at the traversal".

| leg | the wrong build it kills |
|---|---|
| `test_WITHOUT_the_backfill_the_traversal_serves_a_CONFIDENT_EMPTY` | nothing — it MEASURES the false clear rather than asserting someone avoided it. Without it the section is self-congratulatory. |
| `test_ensure_ready_BACKFILLS_the_edges_from_the_EXISTING_columns` | no backfill (S3 verbatim) — and, because it is an EXACT set, also a backfill that mints the transitive CLOSURE as direct edges, which would serve the right traversal answer off a broken mirror |
| `test_the_BACKFILLED_answer_DIFFERS_from_the_UN_backfilled_one` | **the byte diff itself**: two stores seeded identically, differing only in whether the migration ran |
| `test_the_backfill_covers_a_TERMINAL_row_too_not_only_the_OPEN_ones` | *"backfill what is still open"* — invisible to an all-`open` fixture |
| `test_the_PHANTOM_edge_is_NOT_minted_and_the_MIGRATION_STILL_LANDS` | both halves at once: skip-everything, and roll-back-everything, each of which satisfies "no phantom edge" |
| `test_the_phantom_SKIP_is_RECORDED_never_silent` | **the dropped RIDER** — the clause after the "and" |
| `test_a_store_whose_blockers_ALL_RESOLVE_records_NO_skip` | a build that records a skip unconditionally, which satisfies the leg above while telling an operator nothing |
| `test_ONE_phantom_RELATE_rolls_back_the_REAL_edges_beside_it` | it MEASURES R11's own wrinkle. If this fails, the migration is not one transaction and the pre-filter would be optional |
| `test_POSITIVE_CONTROL_the_SAME_transaction_WITHOUT_the_phantom_LANDS` | a transaction that never works — the probe's §6.2 lesson |
| `test_a_SECOND_ensure_ready_neither_RAISES_nor_DUPLICATES` | both idempotence failures, which are opposite: double-mint (no `UNIQUE(in,out)`) and boot-crash (with one) |
| `test_the_backfill_does_NOT_re_mint_over_edges_a_WRITE_PATH_already_made` | a backfill keyed on *"did I already run"* rather than on the store's state |
| `test_MUTATION_neutralising_the_shared_policy_STOPS_the_backfill` | a SECOND copy of the existence policy (L3 / #102) — proved by MUTATION, never by inspection |
| `test_POSITIVE_CONTROL_a_store_with_NOTHING_to_backfill_never_reaches_it` | an `ensure_ready` that touches the policy for an unrelated reason, or once per boot regardless |
| `test_a_FAILED_existence_read_makes_ensure_ready_LOUD_not_SILENTLY_PARTIAL` | a swallowing `except` around the pre-filter — which boots the service and restores S3's defect through a degradation nobody constructed |
| `TestTheLegacyWorldIsGenuinelyTheDEGRADEDOne` (1 leg) | the whole section's anti-vacuity control: the fixture really does hold columns and really does hold no edges |

**Why the sharing proof is NAME-FREE.** `_patch_every_shared_policy_COROUTINE` derives its
targets — every public coroutine `loremaster.agent_existence` owns, patched at BOTH
addresses because `from … import name` copies the reference. Keying it on
`reject_unknown_rows` would have pinned a spelling nobody has chosen: R11's pre-filter needs
the ids that RESOLVED, and the shipped entry point RAISES instead of returning them
(→ ESC-2). Derived at `70cc5a4`: `{reject_unknown_agents}` — non-empty, so the helper's
fail-closed assert does not fire vacuously.

---

## §B — the Leg-2 forgery constructions, and their byte-diff verdicts

Each row is a CONSTRUCTED degraded state, byte-diffed against the healthy response through
`_served_shape`, which renders a result and a raised error into the same string so the
comparison is possible at all.

| # | surface | dependency × mode | construction | byte-diff verdict |
|---|---|---|---|---|
| F1 | `transitive_blockers` | store × error/timeout mid-traversal | every `_txn` coroutine in `loremaster.tasks` (DERIVED, not listed) replaced with one raising the seam's own laundered text | **DIFFER** — the healthy leg must render `OK …`, the degraded leg must not. Asserted three ways: `≠ healthy`, `not startswith("OK ")`, and the error names the task + the bound |
| F2 | `transitive_blockers` | store × **partial (LEGACY: column, no edges)** | §A's `legacy_column_store`, un-backfilled vs backfilled | **DIFFER** — this is the S3 headline; the un-backfilled world serves `OK ids=[] truncated=False`, verbatim, and is asserted BY VALUE so the diff cannot degenerate |
| F3 | blocker pre-check (WRITE path) | store × empty | seams return `[]` on a store that HAS the blocker | **fail-CLOSED**: refuse naming the blocker, write no row. Positive control (healthy read ⇒ the same create SUCCEEDS) kills refuse-everything |
| F4 | blocker pre-check (WRITE path) | store × error | seams raise | **DIFFER from F3's refusal** — a check that FAILED must not be served as the fact *"this id names no task row"*, which is what a caller would act on by minting a duplicate |
| F5 | blocker pre-check (MIGRATION path) | policy × error | the shared policy's coroutines raise | **LOUD** — `ensure_ready` must not complete. A swallowing build is the only way to serve S3's false clear here |
| F6 | `query`'s R9 honest total | store × error on the count | **none needed — the total does not exist at this layer** | **ASSERTED EMPTINESS + RECORDED BOUND** (§F6 below) |

**And the `{empty}` mode's honest problem, stated rather than papered over.** At the app
layer an existence read that returns `[]` because it FAILED and one that returns `[]` because
the rows are absent are the SAME BYTES, and no app-level care separates them. That would be a
false clear — *unless the mode cannot be produced by degradation at all.* It cannot, and
`TestTheSTORESeamRAISESRatherThanReturningEMPTY` says so with a measurement rather than an
argument: the seam RAISES on a rejected statement (leg 1) while a legal read matching nothing
returns `[]` (leg 2, the control that stops leg 1 being satisfied by a seam that raises on
everything). So `{empty}` at the app layer means *ran-and-empty* — a TRUE clear.

### §F6 — R9's honest total: why the answer is an asserted emptiness, not a construction

RE-DERIVED rather than inherited. `TaskLedger.query_tasks` serves `list[Task]`: rows, and
nothing beside them. R9's counted-elision line (*"+K more — re-run with limit=N"*) is a
RENDER, routed to 04b-2 by the previous wave (`REPORT-contractfix-04b1-r3.md` §RESIDUALS
R-7), and the store-side count that would feed it does not exist at this layer. **There is no
number here that could be fabricated.**

The law's §12.2 step 4 says exactly what to do with a derived pair that has no construction:
*"every derived pair carries either a CONSTRUCTED forgery pin or a RECORDED named bound … a
verb reaching no seam is pure-render — and that emptiness is ASSERTED, not assumed."* So
`TestNoTOTALIsServedThatWasNotMEASURED` asserts it, deny-by-default (the SAFE shape is one
thing; the names a fabricated total could wear are unbounded), with a positive control so
`return []` cannot satisfy it. The day someone wraps the answer in a result object carrying a
count, the pin goes RED **carrying its own re-open instruction** — which is what a pinned
bound is for (#137/#138).

### §T-TIMEOUT — a correction to §11.1's own prescription (finding #263)

That row asks for *"a TEACHING error naming the timeout"*. **The ledger provably cannot name
it.** Derived by READING `loremaster/loremaster/store/_txn.py`, not by assuming:
`_classify_engine_error`'s label set is
`{retryable conflict, assert violation, field coercion, query too complex, unspecified rejection}` —
there is **no timeout label** — and the seam's hygiene boundary (ledger #31) deliberately
withholds the raw engine text. A ledger that named the timeout would be GUESSING, which is
the fabrication class this packet already refused once (`TestTheResultIsSELFDESCRIBING`).

Pinned instead, as the achievable and honest form of the same requirement: the ledger's OWN
vocabulary (by TYPE, so a subclass counts and a raw store error does not), no hygiene marker,
and the failure NAMES the operation (the task id) and the BOUND it ran at
(`TASK_BLOCKER_MAX_DEPTH`) — which is the whole of what a caller needs in order to choose
between retrying smaller and giving up. Filed as **#263** with the alternative (teach `_txn` a
timeout CLASS, which is outside 04b-1's writable set and is arguably the better long-term
fix, since every other seam would get it too).

---

## §C — LEG 1: the scope diff, per served surface

Written into the module docstring so it travels with the contract rather than with this
report. Four surfaces; the full table is there. What matters here:

- **The only difference that SURVIVES R11** is a legacy `blocked_by` entry naming no task
  row. `ENFORCED` forbids the edge, R11 skips it, #236 rules the cleanup OUT, and new writes
  cannot create one (the pre-check refuses). It is therefore permanent, and it is carried by
  `TestTheScopeOfTheTransitiveReadIsSTATED` — a served-English pin in this file's established
  idiom, **with its bound stated**: it checks that the words are PRESENT, not that they are
  true; what makes them true is SECTION K's exact-set backfill pin.
- **Leg 1's own bound is restated in the docstring**, from the law: sound on *set* and
  *predicate-as-WRITTEN* only — time, environment and predicate-as-EXECUTED are BELIEVED.
  Every row of that table is a claim about what the code SAYS; only §B's constructions are
  claims about what it DOES.

## §D — the interim bound, recorded as a fact

In two places in the contract's own prose (module docstring, and SECTION L's header):
`scripts/forgery_sites.py` **does not exist**; §11.1's table is a **CURATED INTERIM bounded
to five served surfaces and one reader's sight** (§12.3 says so in its own words); the law
PERMITS a bounded interim and FORBIDS presenting it as complete; **a false clear found later
is a RE-OPEN TRIGGER, never a retroactive pass**. Ownership is stated in the same breath:
04b-1 owns the traversal-timeout row, the pre-check row and R9's honest-total row; 04b-2 owns
the fleet-column and footer rows.

---

## §MEASURED — the assumption that was wrong, and how it was caught

`SELECT … FROM blocks` on a store with **no `blocks` table** RAISES
`surrealdb.errors.NotFoundError: The table 'blocks' does not exist`. It does **not** return
an empty list. Store reference §5's auto-creation of an undeclared table is a property of a
**WRITE** (`RELATE`), never of a read.

I had assumed the opposite when writing the fixture. It surfaced as **13 fixture ERRORS on
the first run** — which is the law's own point: *"a missed world-state is discoverable …
CONSTRUCTION, NEVER REASONING."* The fix is `_blocks_edge_pairs_or_NO_TABLE`, used ONLY by
the pre-migration legs and narrowed to the absent-table message, with the reasoning written
at the site: after `ensure_ready` an absent edge table is a DEFECT and laundering it into
"zero edges" would be this file's own false-clear class. Recorded in lore memory.

---

## §COLOUR — Deviation 1: two of my own docstrings stated the wrong colour

Both were caught by DERIVING the colour before declaring the expected-RED set, not by a run.

1. `TestTheNakedBackfillWouldRollTheMigrationBack` said *"GREEN before and after"*. Its first
   leg is **RED at `70cc5a4`**, and for a reason worth knowing: today's `generate_task_ddl`
   emits no `blocks` table, so the phantom `RELATE` AUTO-CREATES one `TYPE ANY` (store
   reference §5) and is accepted. It goes green the moment the edge ships `ENFORCED`.
2. `TestNoTOTALIsServedThatWasNotMEASURED` said the same. **Both** legs are RED at `70cc5a4`
   for one reason unrelated to totals: `query_tasks` does not accept `limit` yet (ruling R5
   adds it). The cap is not decoration — §11.1's hazard is *"a total beside a CAPPED
   listing"*, so a leg without the cap describes a different surface.

Both docstrings now state the derived colour AND that an earlier draft got it wrong. A class
docstring that mis-states its own colour is a contract whose author cannot say why each pin
is red, which this file's own header forbids.

---

## §DECLARED — declared vs observed RED, both ways

Node ids taken from `pytest --collect-only -q` and written to `/tmp/r4_declared_red.txt` /
`/tmp/r4_declared_green.txt` **before any run** (a set read off failures you just watched is
the tautology in a new costume). Measured in `/home/ejprice/scratch/cfix04b1r4-red`, a
`scratch_copy.sh` copy whose only working-tree modifications are the two contract files
(`git status --porcelain` shown in the run), with production at pristine `70cc5a4`.

```
loremaster.__file__ = /home/ejprice/scratch/cfix04b1r4-red/loremaster/loremaster/__init__.py
18 failed, 7 passed in 4.84s        (PYTEST_EXIT=1)

UNEXPECTED REDS:                    (none)
DECLARED REDS THAT STAYED GREEN:    (none)
DECLARED-GREEN THAT WENT RED:       (none)
declared red=18   observed red=18
```

The 6 declared-GREEN pins are the controls and the two `{empty}`-mode measurements: the
legacy-world anti-vacuity leg, the naked-backfill positive control, the
nothing-to-backfill positive control, both store-seam legs, and the pre-check positive
control.

⚠ **ONE PIN MOVED FROM GREEN TO RED BECAUSE OF THE LEAD'S RULING, and that is the whole
point of escalate-then-pin.** Under my recommended reading A, the `{error}`-mode leg was
GREEN pre-build (a raw store error already differs from a phantom refusal, so it
discriminated only against a WRONG BUILT world). Under the ruled reading B it asserts
`pytest.raises(TaskLedgerError)` — measured: `SurrealStoreError` is NOT a subclass of
`TaskLedgerError` (both descend from `RuntimeError` independently), so the pin is now RED at
`70cc5a4` and discriminates against today's tree as well.

---

## §GATES — repo tree, UNPIPED, exits captured separately

```
$ uv run ruff check .
All checks passed!
RUFF_EXIT=0

$ ./scripts/typecheck.sh
typecheck: lorerunes OK · lorescribe OK · loresigil OK · loremaster OK (171 files) · skills OK
MYPY_EXIT=0
```

⚠ `mypy` initially FAILED on the two new `query_tasks(limit=…)` call sites — `limit` is a
parameter ruling R5 ADDS, so a typed call site is a mypy error TODAY rather than a red pin,
i.e. a contract that fails its own gate before a builder sees it (finding #133's sibling).
Routed through a `**filters: Any` helper (`_served_rows`), which is exactly why `_ids`
already existed in that shape.

### RED honesty — the WHOLE contract at pristine `70cc5a4`

```
$ uv run pytest -q -n auto --show-capture=no \
      loremaster/tests/test_blocks_edge.py loremaster/tests/test_query_tasks_bounded.py
152 failed, 63 passed in 8.45s        (PYTEST_EXIT=1)
  test_blocks_edge.py           142 RED / 33 GREEN   (of 175)
  test_query_tasks_bounded.py    10 RED / 30 GREEN   (of  40)
```

⚠ **AN INHERITED NUMBER THAT DID NOT SURVIVE RE-DERIVATION, disclosed rather than
quietly reconciled.** Subtracting my own 22 declared reds gives the pre-existing split
**122 / 8**. `REPORT-contractfix-04b1-r3.md` §GATES records **122 / 9** — the
`test_blocks_edge.py` half matches exactly, the `test_query_tasks_bounded.py` half is one
LOWER here. The baselines differ (r3 measured at `5a2dca9`; this is `70cc5a4`, which carries
r3's own committed contract plus two merges), so drift is the likely explanation and I did
NOT chase it — but *"likely"* is not a measurement, and a count nobody re-derives is how a
wrong number survives. The eight pre-existing bounded reds, listed so the next reader can
diff rather than re-guess: `TestLimitIsLEGALForQueryAtTheToolSeam::test_SINCE_on_action_
QUERY_is_STILL_REFUSED_…` · `TestTheBLOCKEDPathIsBoundedToo::test_rows_read_does_NOT_grow_
when_BLOCKED_is_also_asked[owner-filter]` and `[status-filter]` ·
`TestTheCapAppliesToTheANSWERNotTheCandidateScan::test_a_capped_BLOCKED_query_…` and
`::test_a_SHORT_answer_means_the_scan_was_EXHAUSTED_…` ·
`TestTheLimitIsPUSHEDINTOTheStatement::test_query_tasks_ACCEPTS_a_limit_…`,
`::test_the_LIMIT_bounds_the_ROWS_READ_…` and `::test_the_TOOL_SEAM_passes_the_limit_…`.

---

## §X-SAT — SATISFIABILITY RECEIPT

*(pending)*

---

## §ESCALATIONS — four raised, ALL FOUR RULED by the lead at `92577f1`, two implemented here

⚠ **READ THIS FIRST: the lead ruled these WHILE THIS WAVE WAS STILL RUNNING**, on an earlier
draft of this report, and committed the ruling into `docs/plans/v2/04-comms-blocks-footer.md`
(§*R11's FOUR ESCALATIONS — RULED*). Each escalation below therefore carries the reading I
recommended, the RULING, and **what I changed in response**. ESC-1 and ESC-2 confirmed what
was already pinned; **ESC-3 and ESC-4 changed the contract and are implemented.**

### ESC-1 — what does "RECORDED" mean for a phantom skip?

R11 says *"phantom skips are RECORDED, never silent"* and does not say where.

* **Reading A (PINNED): a structured LOG record at WARNING or above**, naming both the
  phantom id and the task it was skipped for. Cheap, matches the repo's
  `logger.<level>("event.name", extra={…})` idiom, and leaves `ensure_ready() -> None`
  alone — a return-type change would ripple through the five fakes that implement it.
* **Reading B: a typed migration summary returned by `ensure_ready`.** Stronger (a caller
  can act on it), but it retypes a method five test doubles implement and that DI calls at
  boot for effect, not for value.

**Recommendation: A.** ✅ **RULED A.** No contract change. The lead's rider is worth carrying
into the builder brief: *"the log serves the OPERATOR; the agent-facing bound is §C's pinned
scope statement"* — i.e. the two halves are deliberately on different surfaces, and a builder
that tries to serve the skip to the AGENT through the traversal result would be re-opening
the exact-field-set ban (`TestTheResultIsSELFDESCRIBING`).

### ESC-2 — R11's pre-filter needs a NON-RAISING probe the policy does not have

R11 says the backfill is *"pre-filtered through the L3 existence policy"*. That policy's
entry point (`reject_unknown_rows`) **raises**; a filter needs the SET of ids that resolved.

* **Reading A (recommended): the policy module grows a non-raising probe**, and
  `reject_unknown_rows` becomes a thin caller of it — one implementation, two callers, in
  the module L3 already names.
* **Reading B: the backfill calls the raising entry per row and catches.** N round trips, and
  it makes an exception the control flow of a migration.

The contract does not pin the NAME (`_patch_every_shared_policy_COROUTINE` is derived), so
both readings satisfy it; the pin only requires that the decision be made **inside that
module**. ✅ **RULED A** — *"one implementation, two callers, inside the module L3 already
names"*; B *"makes an exception the control flow of a migration"*. No contract change: the
derived, name-free pin already admits A and requires the module.

### ESC-3 — must a FAILED pre-check be LAUNDERED as well as distinguishable?

Ruling T2 bans a raw `(unspecified rejection)` reaching a caller *"on every verb this packet
touches"*. A store failure DURING the pre-check is not caller-input-provoked, so it is not in
T2's table — but it does reach a caller.

* **Reading A (PINNED): distinguishable is enough.** The pin requires only that the failed
  check not be served as the phantom refusal, and that no row be written. A build that lets
  `SurrealStoreError` propagate satisfies it. Rationale: that is what every other ledger read
  does today, so requiring more would be a NEW requirement invented by the contract, and a
  correct build could be RED on it — the C-DEF class two prior waves already hit.
* **Reading B: it must be classified into the ledger's vocabulary**, like every other T2 door.

**Recommendation: B eventually, A now.** ✅ **RULED B, AND IMPLEMENTED.** The lead's reason
is the part worth keeping: *"the author recommended 'B eventually, A now' out of well-placed
C-DEF caution — a contract must not invent a requirement a correct build fails. That caution
does not apply once the requirement is RULED: a correct build now classifies, so the pin is
satisfiable by construction."*

**CHANGED:** the pin is renamed
`test_a_FAILED_existence_read_is_CLASSIFIED_not_served_as_the_PHANTOM_refusal` and now
asserts `pytest.raises(TaskLedgerError)` plus the absence of BOTH hygiene markers. Its stub
was also strengthened to raise the seam's OWN laundered text rather than a friendly sentence
— otherwise the hygiene assertion would have been measuring a string the path never produces.
**Measured consequence:** `SurrealStoreError` is not a subclass of `TaskLedgerError` (both
descend from `RuntimeError` independently), so the pin moved from GREEN to **RED at
`70cc5a4`** — it now discriminates against today's tree, not only against a wrong built one.

### ESC-4 — legacy `blocked_by` CYCLES, on which R11 is silent

A legacy row can name itself, or two legacy rows can name each other: `blocked_by` was
fail-open, and the acyclicity guard R3 adds is a WRITE-time guard for NEW writes.

* **Reading A: the backfill mints them.** The edge mirrors the column ∀ rows; refusing would
  make edge ≢ `blocked_by` on exactly the rows the invariant is hardest to reason about, and
  `+collect` terminates on cycles (probe P4).
* **Reading B: the backfill refuses them** and records the skip like a phantom.

**Recommendation: A** — and it was **NOT PINNED EITHER WAY, deliberately**: pinning A while
it was unruled would have made a build that defensibly chose B RED on a correct
implementation. ✅ **RULED A, AND NOW PINNED.**

**CHANGED:** new class `TestALEGACYCycleIsMINTEDAndRECORDED`, 3 legs, in its own database so
SECTION K's acyclic fixture stays acyclic: the edge set MIRRORS the cyclic column exactly
(both directions), the cycle is RECORDED at WARNING naming both members, and the traversal
TERMINATES and DEDUPLICATES over it. The closing dependency is written by a raw `UPDATE`
because no public verb will mint it after this packet and `ENFORCED` could not carry it at
creation time anyway (adversary MP-4a).

⚠ **The third leg carries a STATED BOUND rather than over-claiming**: it does NOT assert
`truncated`, nor whether the root appears in its own reach — the first depends on how a build
derives truncation over a cyclic walk and the second on whether `+inclusive` is in play, and
**neither is ruled**. Pinning an unruled value there would re-create exactly the C-DEF risk
this escalation existed to avoid.

---

## RESIDUALS — every item, its own line, its own verdict

| # | item | verdict |
|---|---|---|
| R-1 | **A — R11's backfill from existing `blocked_by` columns** | ✅ **PINNED**, exact-set, plus the byte diff against the un-backfilled world. §A. |
| R-2 | **A — pre-filtered through the L3 existence policy** | ✅ **PINNED BY MUTATION**, name-free (derived patch over the policy module's coroutines at both addresses), with a positive control that a store with nothing to backfill never reaches it. |
| R-3 | **A — the naked-backfill rollback failure mode, "with a control"** | ✅ **PINNED**, and it MEASURES the engine claim rather than assuming it: one phantom RELATE in the transaction must take the real edge beside it down, and the positive control shows the same transaction without the phantom lands. |
| R-4 | **A — phantom skips RECORDED, never silent** | ✅ **PINNED**, over the log record's whole surface, **with the discriminating control** (a migration where everything resolves must record NOTHING). → ESC-1 for the shape. |
| R-5 | **A — idempotence, no duplicate edges** | ✅ **PINNED**, two legs on opposite failure modes (double-mint vs boot-crash), plus the mixed-provenance leg (backfill + a later `create_task` + a second boot). |
| R-6 | **A — the discriminating fixture is the legacy world CONSTRUCTED** | ✅ **DONE** via `_seed_legacy_task`, at the packet's non-negotiable floor (4 deep, branching, a diamond) plus a phantom-bearing row and a TERMINAL-status row. |
| R-7 | **B — traversal timeout ⇒ teaching error, never partial-as-complete** | ✅ **PINNED, 2 legs, byte-diffed** — 🔴 **and §11.1's prescription is CORRECTED**: "naming the timeout" is unachievable at the ledger. Finding **#263**. §T-TIMEOUT. |
| R-8 | **B — the pre-check's failed existence read ⇒ fail-CLOSED** | ✅ **PINNED on BOTH paths**: the WRITE path (3 legs, `{empty}` and `{error}` as different modes) and the MIGRATION path (1 leg). |
| R-9 | **B — R9's honest total, never invented** | ✅ **RESOLVED AS AN ASSERTED EMPTINESS** + a recorded bound naming 04b-2 as the owner of the construction. §F6. |
| R-10 | **B — "identical bytes = a false clear = STOP"** | ✅ **NO FALSE CLEAR FOUND.** Every construction's degraded bytes differ from its healthy bytes. The one mode where identity is unavoidable (`{empty}` at the app layer) is closed one level down and pinned there, not softened. |
| R-11 | **C — leg-1 scope diff** | ✅ **WRITTEN** (module docstring, four surfaces) and the one surviving difference **PINNED**. |
| R-12 | **D — the interim bound** | ✅ **RECORDED AS A FACT** in the contract's prose, twice, with the re-open-trigger clause. |
| R-13b | **The `{empty}` mode is indistinguishable AT THE APP LAYER** | 🟡 **STATED BOUND, closed one level down.** `TestTheSTORESeamRAISESRatherThanReturningEMPTY` measures that a rejected read raises rather than returning `[]`, so the mode cannot be manufactured by degradation. Written into the class docstring, not hidden. |
| R-14 | **`ensure_ready` stays in `VERBS_WITH_NO_NEW_ENGINE_REJECTION_PATH`** | 🟡 **RE-ADJUDICATED DELIBERATELY**, with the reasoning at the site: R11's new failure surface is provoked by a degraded dependency, never by caller input, so there is no offending token a refusal could carry back and no `provoke` lambda that is not an invention. |
| R-15 | **The served-English pin on the traversal docstring** | 🟡 **STATED BOUND.** It checks two tokens are PRESENT (`blocked_by`, `phantom`); it cannot check the sentence is true. Same idiom and same bound as the existing FLOOR-property pin. |
| R-16 | **`_served_shape` renders a result and an exception into one string** | 🟡 **DELIBERATE.** A byte diff between a healthy result and a degraded raise is impossible otherwise, and "what the caller got" is the right unit. Not a production surface. |
| R-17 | **The absent-table read is caught by MESSAGE, not by TYPE** | 🟡 **STATED CONSTRAINT.** A typed import of `surrealdb.errors.NotFoundError` in a test that must stay collectable under an SDK bump is the #133 shape; the catch asserts the message rather than swallowing, so a different failure re-raises loudly. |
| R-18 | **ESC-1 / ESC-2** | ✅ **RULED (`92577f1`), NO CONTRACT CHANGE** — both confirmed the reading already pinned. ESC-1's rider (log serves the OPERATOR; the agent-facing bound is the READ surface's scope statement) belongs in the builder brief. |
| R-19 | **ESC-3 — a failed pre-check must be CLASSIFIED** | ✅ **RULED B, IMPLEMENTED.** Pin renamed and strengthened to a `TaskLedgerError` type assertion + both hygiene markers; its stub now raises the seam's own laundered text. Moved GREEN→RED at `70cc5a4`. |
| R-20 | **ESC-4 — legacy `blocked_by` CYCLES** | ✅ **RULED A, NOW PINNED** — `TestALEGACYCycleIsMINTEDAndRECORDED`, 3 legs in its own database, with a stated bound on what the termination leg does NOT assert (`truncated`, root-in-own-reach: both unruled). |
| R-21 | **The cycle fixture writes its closing dependency with a RAW `UPDATE`** | 🟡 **NECESSARY, and documented at the site.** After this packet no public verb will mint it (the cycle guard refuses) and `ENFORCED` could not carry it at creation time (adversary MP-4a: the closing edge points at a task that does not exist yet). Production holds such rows because they were legal when written. |
| R-22 | **04b-2's owed constructions (fleet columns, footer)** | 🟡 **NOT MINE, and named as such** in SECTION L's header so 04b-2 inherits an address rather than a rediscovery. |
| R-23 | **ESC-1..ESC-5 of `REPORT-contractfix-04b1.md` and ESC-A..ESC-E of `-r3`** | 🟡 **UNCHANGED — not in my worklist and not touched.** They remain open exactly as those reports leave them; nothing here supersedes them. |
| R-24 | **Scratch trees** | 🟡 **DISPOSITION NEEDED — your call.** `/home/ejprice/scratch/cfix04b1r4-red` (the RED baseline) and `/home/ejprice/scratch/cfix04b1r4-ref` (the reference build). I did NOT touch `adv04b1-ref`, `contractfix-04b1-ref` or `cfix04b1r3-ref`. |
| R-25 | **The reference build was DELEGATED, and the scratch root carries prior waves' REPORTS** | 🟡 **STATED BOUND ON THE RECEIPT'S INDEPENDENCE.** I wrote no production code; a fresh Opus subagent did, to a front-loaded brief that FORBADE reading the three prior reference TREES. But `REPORT-contractfix-04b1*.md` and `REPORT-adversary-04b1.md` are tracked artifacts and therefore sit at the scratch root. Independent of the prior trees; not provably independent of their reports. Stated rather than claimed away. |
| R-26 | **I did not run the FULL suite** | 🟡 **DELIBERATE** (brief-base §3). Scoped to the two contract files plus, in the reference build, the neighbouring suites named in §X-SAT. |
| R-27 | **I could not drive my own ledger row** | 🟡 **UNCHANGED FROM r3.** Task `e48347a9…` is held by `lead-pkt04b`; this is finding **#262**, already filed by the previous wave. Not re-filed. |
| R-28 | **No git state was mutated BY ME** | ✅ Verified — I ran no `add`/`commit`/`stash`/`checkout`/`rebase`. |
| R-29 | **⚠ A SIBLING COMMITTED MY IN-FLIGHT CONTRACT AGAIN — the hazard r3 filed as ESC-E, recurring** | 🟡 **DISCLOSED, nothing lost.** Mid-wave, HEAD moved `70cc5a4` → `922f4c9` (*"test(04b-1): R11 backfill + the Leg-2 forgery constructions — the contract is complete"*) → `92577f1` (the escalation ruling). `922f4c9` carries my two test files and this report as they stood at that moment; my later edits (the ESC-3/ESC-4 pins, the id-redaction strengthening) are the current working-tree delta. **Consequence for anyone re-measuring: the pristine baseline is `70cc5a4`, NOT `HEAD~1` or `HEAD~2`** — `922f4c9` already contains part of this contract. It also means the commit message *"the contract is complete"* was true of a 212-pin snapshot and the contract is now 215. |
