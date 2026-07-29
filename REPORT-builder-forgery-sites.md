# REPORT-builder-forgery-sites

brief-base v8 read
brief project v7 read (comms `register`, session `pkt04b-20260728`, role `builder`, model `claude-opus-5`)

## CAPABILITY CHECK (brief-base §4 — first thing, as required)

Demanded vs. what I have: **no gap that blocks the mission; one that shapes a deliverable, disclosed below.**

| the brief demanded | what I actually have | what I did |
|---|---|---|
| register/drain/file findings via `lore_comms` / `lore_findings` | both tools reachable (loaded via `ToolSearch`) | registered, drained (empty), filed **#279** |
| gates `./scripts/typecheck.sh` and `uv run ruff check .` at EXIT=0 | both runnable | both EXIT=0 (tails below) |
| *"your module is inside the typechecked set"* **AND** *"`scripts/` … is the obvious home"* | **these two cannot both hold today.** `scripts/typecheck.sh` iterates `MEMBERS=(lorerunes lorescribe loresigil loremaster skills)`; `scripts` is deliberately excluded — `pyproject.toml`'s `testpaths` comment records why (**#188 measured 41 mypy errors there**). Adding `scripts` to `MEMBERS` turns the canonical gate RED on 41 errors I did not write. | Chose `scripts/`, made both files mypy-clean, and made that a **pin that runs in the gate** (`TestThisInstrumentIsTYPECHECKED`) instead of a claim in prose. Detail + the exact alternative edit in §D3. |
| tests hit spike-surreal `:18000` only | `LORE_TEST_SURREAL_URL` defaults to `ws://127.0.0.1:18000/rpc` via `_surreal_harness`; `:18500` never referenced | verified: the only URL source is the harness's env-driven default |

---

## SUMMARY BLOCK

- state: **done**
- deviations: (1) render adds two DERIVATION header lines + a derived `via <seam>` suffix per door, where the audit hand-wrote `# the mint`-style comments; (2) the closing line reads `no silent door in ensure_ready` where the audit's read `no silent backfill door`; (3) the sweep's `bootstrap_session` exclusion means a warm connection is NOT a precondition (the audit's harness needed one).
- `Packages considered:` **fault injection** → `pytest.MonkeyPatch` (READ: installed `_pytest/monkeypatch.pyi` + `setattr`/`undo` source) — **bespoke**, the CLI runs outside pytest and needs per-CALL k-th faulting, which no fixture API offers; `unittest.mock.patch` (READ: installed `unittest/mock.py` `_patch.__enter__`) — **bespoke**, patches by dotted NAME, and name-keyed patching is the exact defect this instrument exists to replace. **Interception mechanism** → `loremaster/tests/_sdk_guard.py` (READ: its full source) — `keep_with_trigger`: its derive-from-the-class posture is inherited, but it OBSERVES and cannot FAULT; trigger = the day it grows a fault hook, this should route through it. **Store construction** → `loremaster/tests/_surreal_harness.py` (READ: `make_env` / `unique_database` / `connect_admin` / `drop_database`) — **replace**: all connection topology, DB minting and retry-aware teardown come from it, none re-typed here.
- decisions-needed: **one — #279**, the store-seam derivation now exists twice (mine, and `test_blocks_edge.py::_degrade_every_STORE_seam`). Duplication is a design decision; I escalated rather than unifying, because unifying edits a contract file 04b-1 closed green.
- receipts: `scripts/forgery_door_sweep.py` (module) · `scripts/test_forgery_door_sweep.py` (20 pins) · §A reproduced output verbatim · §B gate tails with counts · §C two mutation proofs, both `PROOF HELD` · §E residuals.

---

## §A — THE REPRODUCED DOOR SWEEP, VERBATIM

`uv run python scripts/forgery_door_sweep.py 2>/dev/null` → `EXIT=0`, measured 2026-07-29 at `c549f89` + these two untracked files:

```
DERIVATION: 3 store seam(s) — execute_read_transaction, execute_transaction, run_query — bound at 3 site(s).
NOT SWEPT (public loremaster.store._txn coroutines executing no caller statement): bootstrap_session, retry_on_conflict.
POSITIVE CONTROL: ensure_ready made 4 store calls, raised=None, edges=2
DERIVED DOOR SET: 4 store calls during ensure_ready over a legacy store.
  door k=1: RAISED  InjectedStoreFault  (calls observed 1, edges after -1)  via execute_transaction
  door k=2: RAISED  InjectedStoreFault  (calls observed 2, edges after 0)  via execute_read_transaction
  door k=3: RAISED  InjectedStoreFault  (calls observed 3, edges after 0)  via run_query
  door k=4: RAISED  InjectedStoreFault  (calls observed 4, edges after 0)  via execute_transaction
ALL 4 DERIVED DOORS FAIL LOUD — no silent door in ensure_ready on the shipped build.
```

**The audit's result is reproduced exactly**: 4 doors, all `RAISED InjectedStoreFault`, `calls observed` = k for every k, `edges after` = `-1, 0, 0, 0`, positive control clean at `edges=2`. The `via <seam>` column is DERIVED from the call that was faulted — the audit carried the same information as hand-written comments (`# the mint`), i.e. a name-list one edit away from being wrong about its own output.

The stderr channel carries production's own `task.backfill.phantom_blocker_skipped` warnings (the legacy world holds one phantom blocker by construction). stdout is the render alone.

### The sweep DISCRIMINATES — the same command over a wrong build

`TaskLedger._backfill_blocks_edges` wrapped in `try/except Exception: return` at runtime (production not edited; restored by `monkeypatch`) — the single most-written defensive line in any migration:

```
POSITIVE CONTROL: ensure_ready made 4 store calls, raised=None, edges=2
DERIVED DOOR SET: 4 store calls during ensure_ready over a legacy store.
  door k=1: RAISED  InjectedStoreFault  (calls observed 1, edges after -1)  via execute_transaction
  door k=2: RETURNED  (calls observed 2, edges after 0)  via execute_read_transaction  ⛔ RETURNED NORMALLY — a store failure was swallowed at this door
  door k=3: RETURNED  (calls observed 3, edges after 0)  via run_query  ⛔ RETURNED NORMALLY — a store failure was swallowed at this door
  door k=4: RETURNED  (calls observed 4, edges after 0)  via execute_transaction  ⛔ RETURNED NORMALLY — a store failure was swallowed at this door
⛔ 3 OF 4 DERIVED DOORS DID NOT FAIL LOUD — ensure_ready serves a normal response over a failed store call at k=2, k=3, k=4.
```

**Door k=2 is `execute_read_transaction` — the mirror-state read.** That is the third door `BACKFILL_FAILURE_DOORS = ("existence-read", "mint")` cannot see, arrived at by derivation rather than by somebody remembering it. Pinned as `TestTheDoorSweepOverTheRealLedger::test_a_ledger_that_SWALLOWS_its_backfill_failure_is_CAUGHT`.

---

## §B — GATES (with counts)

```
typecheck: lorerunes OK / lorescribe OK / loresigil OK / loremaster OK / skills OK
TYPECHECK_EXIT=0            # ./scripts/typecheck.sh, all five members "Success: no issues found"
All checks passed!
RUFF_EXIT=0                 # uv run ruff check .
```

Scoped test set — `scripts/` (both new files plus every existing scripts test) **plus** `loremaster/tests/test_blocks_edge.py`, the contract whose subject this sweeps:

```
uv run pytest scripts loremaster/tests/test_blocks_edge.py -q -n auto
557 passed in 10.65s
```

The instrument's own contract alone: `20 passed in 2.44s` (2 live-store legs, 0.75s + 0.78s; the rest hermetic). Per brief-base §3 I did NOT run the full suite; nothing outside the two new files was modified (`git status --porcelain` shows exactly two `??` entries).

Targeted mypy over the two new files (the canonical gate cannot see them — §D3):

```
MYPYPATH="scripts:<pyproject mypy_path>" python -m mypy scripts/forgery_door_sweep.py scripts/test_forgery_door_sweep.py
Success: no issues found in 2 source files
```

---

## §C — MUTATION PROOFS (both via `scripts/mutation_proof.py`, both `PROOF HELD`)

Declared RED sets were written into the command **before** each run, from `pytest --collect-only -q` node ids.

**M1 — kill the fault injection.** `len(self.calls) == self.fail_at` → `len(self.calls) == -1`, i.e. the sweep still runs every leg and never faults anything.
Declared RED (4): `TestTheSweepDerivesTheDoorCountFromTheCONTROL::test_the_control_is_what_yields_N_and_every_door_is_faulted_at_its_own_k` · `TestASWALLOWEDDoorIsAFAILURE::test_a_subject_that_swallows_one_fault_is_reported_as_a_SILENT_door` · `TestTheDoorSweepOverTheRealLedger::test_every_store_door_in_ensure_ready_over_a_legacy_store_FAILS_LOUD` · `TestTheDoorSweepOverTheRealLedger::test_a_ledger_that_SWALLOWS_its_backfill_failure_is_CAUGHT`.
Observed: `4 failed, 16 passed`; `PROOF HELD — the declared RED set fired EXACTLY`; `tree restored byte-exact (md5 5c2b114e1bd1e012db0685cada64df70)`.

**M2 — break the type.** `TABLE_ABSENT = -1` → `TABLE_ABSENT = "-1"`.
Declared RED (1): `TestThisInstrumentIsTYPECHECKED::test_mypy_is_clean_over_the_sweep_and_its_contract`.
Observed: `1 failed, 19 passed`; `PROOF HELD`; same restore md5. This is what makes the typecheck pin a pin rather than a comment — and note the direction it proves: the mutation is invisible to every behavioural test in the file.

A third, unplanned proof arrived free: **the sweep's first live run REFUSED to report**, because `sweep_doors` derived its binding sites before the subject factory had imported `loremaster.tasks`, so `sys.modules` held nothing to patch. `SweepCannotSubstantiate: … the interception patched NOTHING and ensure_ready ran undisturbed.` A wrong build here would have printed *"ALL N DERIVED DOORS FAIL LOUD"* over an entry point nobody faulted. Fixed by deriving bindings **after** the world is built (`_run_leg`), and the refusal is pinned (`test_no_binding_site_is_a_REFUSAL_not_a_clean_report`).

---

## §D — WHAT WAS BUILT, AND THE DECISIONS I HAD TO MAKE

### D1 · The path, and why

`scripts/forgery_door_sweep.py` + `scripts/test_forgery_door_sweep.py`, alongside `registration_sites.py` and `mutation_proof.py`, matching the repo's `scripts/test_*.py` convention (`test_mutation_proof.py`, `test_token_survey.py` — the latter's `sys.path.insert` + `# noqa: E402` idiom is copied verbatim for importing a non-package module).

Decisive argument: **brief-base §1 ranks *"a committed script that regenerates a measurement"* as the most durable citation there is.** #278 exists because a measurement lived only in prose. A library buried in the test tree would be citable but not *runnable*; `./scripts/forgery_door_sweep.py` makes the 04b-1 §2.3 result a command. Both files are inside `testpaths` (`scripts` was added there 2026-07-25 for exactly this reason — *"a guard nobody runs is a hope with a filename"*).

### D2 · The derivation — the one real design decision, and the alternative I rejected

> **A DOOR IS ONE INVOCATION OF A STORE SEAM — a PUBLIC coroutine of `loremaster.store._txn` that EXECUTES A CALLER-SUPPLIED `statement` — made while the entry point is running.**

Two predicates, and each is load-bearing:

- *defined in `_txn`, public* — the seam registry, whose completeness is not an opinion: the #136 runtime SDK-escape guard proves nothing reaches a live connection without the driver above it.
- *takes a `statement`* — this is what separates a door from the machinery around it. It **excludes `retry_on_conflict`** (the driver RUNS every door; counting it would report 2N doors) and **excludes `bootstrap_session`** (the session's own DDL, not a caller's statement).

Binding sites are found **by function identity** across every imported `loremaster.*` module, never by attribute name — pinned in both directions: an aliased seam IS found, a same-named impostor is NOT (`TestTheBindingScanIsByIDENTITYNotByNAME`).

**The alternative I rejected, written down per brief-base §2:** intercept at the SDK connection level, the way `_sdk_guard` does — receiver-blind in the strongest sense. I rejected it because the door unit would then include `signin`, `use()` and the two bootstrap `DEFINE` statements, so `ensure_ready` would show **7–8** doors on a cold connect and **4** on a warm one — a door count that depends on connection state is not a derivation, it is a coin flip. The `statement` predicate gives 4 in both states. **The cost is stated in the module docstring and printed on every run:** `bootstrap_session` is a real door this sweep does not cover.

### D3 · The typecheck conflict, and the exact edit I did not make

`scripts/` is outside `scripts/typecheck.sh` (#188: 41 mypy errors). Three options:

1. add `scripts` to `MEMBERS` → gate goes RED on 41 errors I did not write. **Rejected.**
2. hand-list my two files inside the gate → an enumeration inside a gate, the artifact this repo has the most receipts against. **Rejected.**
3. **taken:** a pin in the instrument's own contract that runs `mypy` over exactly these two files and asserts exit 0, reading `mypy_path` **out of `pyproject.toml`** rather than re-typing it (a copied path list is a registration site that goes stale silently). Warm cost measured: **0.28s**.

**The exact edit, if the operator rules otherwise:** clear #188's 41 errors, then append `scripts` to `MEMBERS` in `scripts/typecheck.sh` and prepend `scripts:` to `mypy_path` in `pyproject.toml` — and delete `TestThisInstrumentIsTYPECHECKED` in the same commit rather than keeping both.

### D4 · The world it builds, and why this shape

Three legacy rows: `root` (no blockers), `dependent_a` (blocked by root), `dependent_b` (blocked by root **and a phantom**). Mintable edges = 2, which is why the control reads `edges=2` — the audit's number, and it falls out of the fixture rather than being asserted at it. The phantom is required: a world where every blocker resolves cannot tell a pre-filtered backfill from a naked one, and door k=3 (the existence read) would be decoration.

The OLD DDL is derived from the production emitter **by removal** (`generate_task_ddl()` minus the `blocks TYPE RELATION` statement) and raises if the removal removes nothing. That is what makes `edges after -1` at k=1 meaningful: with the DDL door faulted the relation table does not exist, and `_blocks_edge_count` distinguishes *no table* from *no edges* via `INFO FOR DB` — a plain `SELECT count()` reads both as `0`.

Store idioms per `docs/reference/surrealdb-31-capabilities.md` §2/§7 (read before writing any statement): `CREATE type::record('task', $id) CONTENT $content` with a bound object, tz-aware Python datetimes bound directly, edge ROWS counted rather than traversed (§6.4 — a traversal lists a dangling endpoint as a first-class member). **No schema, DDL or production file was changed.**

### D5 · Ambiguities in the brief I had to resolve, and how

1. **"receiver-blind: it must not key on method NAMES"** — two readings. (a) nothing anywhere may be keyed on any name; (b) the DOOR SET must not be a name list, while the SEAM registry (the small, evidence-backed SAFE set §12.1 names) may be identified. I took **(b)**, because (a) is unimplementable — some anchor must exist — and because §12.1 explicitly builds the derivation *on* the seam registry. Concretely: no receiver name, no method name, no door name appears anywhere; `_txn`'s membership is derived from the module and filtered by a signature property.
2. **"4 doors … if your count differs from 4, that is a FINDING"** — it is 4, so nothing to report. It is 4 **for a stated reason** (the `statement` predicate), and the count is pinned with a failure message saying a change in it is a finding, not a number to update.
3. **"assert the observed call count"** — read as two obligations, both implemented: the control's N *is* the door set (so reach is derived, not declared), and every faulted leg must observe exactly k calls (so the fault landed at its own door and stopped there).

---

## §E — RESIDUALS (one line each; no wholesale classification)

1. **#279 filed — the store-seam derivation now exists twice** (`scripts/forgery_door_sweep.py::store_seams` vs `loremaster/tests/test_blocks_edge.py::_degrade_every_STORE_seam`); the finding carries the exact unification edit and why I did not make it (contract file, closed packet, DESIGN decision).
2. **`bootstrap_session` is an uncovered door** — a namespace/database bootstrap failure is a genuine way `ensure_ready` can break; the sweep prints it as NOT SWEPT on every run, and closing it needs a second door unit (a bootstrap has no caller statement to fault).
3. **The clock and fs seams are uncovered and *uncoverable* today** — §12.3 says their "only door" status is reasoning rather than construction, so no derivation exists to build on; this sweeps the STORE class alone.
4. **The full `forgery_sites.py` verb × seam × mode matrix (§12.2) is NOT built** — deliberately, per the brief's scoping; this delivers the door sweep, which is one mode (store, faulted) for one caller-supplied entry point.
5. **Reach is bounded by what is imported** — a seam bound in a `loremaster.*` module nothing has imported when the sweep runs is invisible; the binding count is printed so the bound is visible, and a zero-binding state REFUSES rather than reporting clean.
6. **Ordering is observed at await time** — an entry point issuing store calls under `asyncio.gather` has no stable k-th call, and this sweep's per-door attribution would be meaningless for it; every entry point swept so far is sequential.
7. **`SweepCannotSubstantiate` covers three blindness states, not four** — empty seam set, no binding site, control raised-or-silent; a fourth (a subject factory that yields a world *different* from the one it built last leg) is not detectable by this instrument and is the caller's responsibility.
8. **`docs/design/2026-07-28-04b-model-consumer-audit.md` §12.3's *"No such script exists today"* is now stale** — it is a design doc and outside my writable set; the one-line correction is to point that sentence at `scripts/forgery_door_sweep.py` for the store row and keep the clock/fs claim unchanged.
9. **The `_sdk_guard` reuse trigger is recorded, not discharged** — if that guard ever grows a fault hook, this sweep's interception should route through it rather than keep its own; today it can only observe.
10. **The two live legs add ~1.6s to the standard gate** and require spike-surreal to be up; they fail LOUD rather than skipping when it is not, per harness policy — an unreachable engine must not read as a pass.
