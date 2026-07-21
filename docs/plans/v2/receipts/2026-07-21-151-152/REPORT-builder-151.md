# REPORT-builder-151

brief-base v5 read

- **state:** done-with-deviations
- **deviations:**
  - The brief's writable-set enumeration named **8** owner files; the contract requires **11**.
    Two owners were missing from the brief's list — `loremaster/loremaster/store/surreal.py`
    (`SurrealStore`) and `loremaster/loremaster/tasks.py` (`TaskLedger`) — both RED-listed in the
    contract's `_QUERY_SEAMS` parametrization. The brief said "verify the full set via the grep"
    and making `url` required directly TypeErrors these two, so I applied the exact sanctioned
    one-line edit (`url=self._url` at the call site) to both. Flagged in §FLAGS.
- **decisions-needed:** none. (The 55-error typecheck baseline is pre-existing packet-03 comms,
  unrelated — surfaced per §FLAGS, no action requested.)
- **receipts:**
  - Owner enumeration + count assertion → §OWNERS
  - RED→GREEN (scoped) → §RECEIPTS; broader suites → §BROADER
  - shared-mechanism mutation proofs (url + label) → §MUTATION
  - ruff / typecheck tails → §GATES
  - flags → §FLAGS

---

## What changed (file:line)

The driver `retry_on_conflict` already accepted `label`/`url` as keyword-only and already built
the `label`/`url`/`engine_error` extras when `label is not None`. The fix is entirely at the CALL
sites + constants + the two prose surfaces #151 names.

`loremaster/loremaster/store/_txn.py`
- **+3 label constants** (`:945-947`) — `_BOOTSTRAP_DEFINE_NAMESPACE_LABEL`,
  `_BOOTSTRAP_SELECT_DATABASE_LABEL`, `_BOOTSTRAP_DEFINE_DATABASE_LABEL`, values naming each
  statement in the engine's own SurrealQL vocabulary, pairwise distinct.
- **`bootstrap_session` signature** (`:950-952`) — added `*, url: str` (REQUIRED, KEYWORD-ONLY, R2).
- **the three `retry_on_conflict` calls** (formerly `:1021-1023`) — each now threads its own
  per-statement `label=` and the shared `url=url` (R1, R3).
- **HALF-2 prose** — `retry_on_conflict` docstring's `None`-default clause (`:857-861`) no longer
  names `bootstrap_session` as a label-less caller; it names only `execute_transaction` and states
  that every other caller passes its own label (R6, derived not restated).
- **the `last_conflict_cause` comment** (`:876-`) — the false ∀ (`every caller … from error`) is
  qualified to the handler-borne callers and NAMES `execute_transaction._attempt` (:1242) as the
  one unchainable raiser, with its reason (R7, lead ruling).
- `bootstrap_session` docstring gained the `url` Arg + the attribution note.

`loremaster/loremaster/scout.py`
- `_scout_query` (`:171`) — added `label="command_subscriber.query.rejected"`, **no url** (R4,
  known bound — partial attribution).
- `_open_command_connection` (`:223`) — `await bootstrap_session(connection, namespace, database, url=url)`.

Ten seam owners — one line each, `url=self._url` at the `bootstrap_session` call:
`agents.py:413 · briefs.py:442 · diff.py:544 · findings.py:453 · graph_surreal.py:416 ·
index/snapshots.py:275 · index/surreal_manifest.py:201 · memory/local.py:364 ·
store/surreal.py:454 · tasks.py:466`.

Test support (in writable set): `tests/_surreal_harness.py:339` — `url=env.url`.

No test file was edited. `tests/_surreal_harness.py:51-60` (the lead's pending fix) was NOT touched.

---

## OWNERS — the eleven bootstrap owners, enumerated and count-asserted

Sweep (bare, per repo law): `git grep -n "await bootstrap_session(" -- loremaster/`. Eleven
production call sites, each with its url in scope at the call:

| # | owner class / fn | file:line | url source |
|---|---|---|---|
| 1 | AgentRegistry | agents.py:413 | self._url |
| 2 | BriefLedger | briefs.py:442 | self._url |
| 3 | DiffEngine | diff.py:544 | self._url |
| 4 | FindingLedger | findings.py:453 | self._url |
| 5 | SurrealCodeGraph | graph_surreal.py:416 | self._url |
| 6 | SnapshotStamper | index/snapshots.py:275 | self._url |
| 7 | SurrealManifest | index/surreal_manifest.py:201 | self._url |
| 8 | LocalMemoryBackend | memory/local.py:364 | self._url |
| 9 | **SurrealStore** | **store/surreal.py:454** | self._url  ⚠ not in brief list |
| 10 | **TaskLedger** | **tasks.py:466** | self._url  ⚠ not in brief list |
| 11 | scout `_open_command_connection` | scout.py:223 | url (param) |

**Count assertion: 11 = 11.** The contract's own two independent floors agree
(`_MIN_KNOWN_BOOTSTRAP_CALL_SITES == _MIN_KNOWN_BOOTSTRAP_OWNERS == 11`), and its
`test_every_owner_the_scan_finds_is_DRIVEN_here` (coverage-as-a-checked-variable) is GREEN — so
the scanned owner set and the driven owner set match exactly. Plus one test-support caller
(`_surreal_harness.py:339`). All other `bootstrap_session(` hits in the tree are string-literal
AST fixtures inside `test_retry_seam.py` (7757/7758/7778/7799/7964/8001), not calls.

---

## RECEIPTS — RED → GREEN (scoped contract)

Command (from `loremaster/`): `uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q`

- **RED (committed baseline, before any edit):** `35 failed, 488 passed, 1 warning in 20.35s`
- **GREEN (after fix):** `523 passed, 1 warning in 18.69s`

523/0 is exactly the contract-adversary's published satisfiability receipt — a correct build was
proven to exist at 523/0, and this build reaches it.

## BROADER — collateral suites (all from `loremaster/`, `-n auto` where applicable)

| suite(s) | result |
|---|---|
| test_scout.py + test_txn_contention.py | **55 passed** |
| test_surreal_store.py (incl. `[real]` harness fixtures → my `url=env.url`) | **178 passed** |
| test_agent_registry, test_task_ledger, test_brief_ledger, test_diff, test_findings, test_graph_surreal, test_snapshots, test_surreal_manifest, test_memory_backend, test_memory_ledger | **1019 passed** |

Zero collateral failures across every owner-module suite and the retry/store suites.

---

## MUTATION — proving the shared mechanism (ONE-IMPLEMENTATION law)

The url/label attribution is a POLICY the eleven owners FEED into the ONE shared
`bootstrap_session` / `retry_on_conflict` driver — not a pattern cloned per owner. Proven by
mutation (change the shared thing; every caller's pin must move):

**Mutation 1 — hardcode the url inside the shared `bootstrap_session`** (`url=url` → a constant in
all three driver calls). Result on the per-owner url pins:
`TestEveryProductionOwnerThreadsITSOWNUrl` → **15 failed** — every one of the ten `_QUERY_SEAMS`
owners (AgentRegistry, BriefLedger, DiffEngine, FindingLedger, SurrealCodeGraph, SnapshotStamper,
SurrealManifest, LocalMemoryBackend, SurrealStore, TaskLedger), scout's command connection, the
two-owners-differ pin, and the harness caller's-url pins all went RED. A private per-owner copy
would NOT have moved — this is the definitive DRY proof that all eleven thread their own url
through one function. Restored → 523 passed.

**Mutation 2 — swap the NS↔DB label VALUES** (present, distinct, but naming the wrong statement —
the 489/0 wrong build the contract exists to catch). Result:
`test_each_bootstrap_label_NAMES_its_own_statement[DEFINE-NAMESPACE]` and `[DEFINE-DATABASE]` → RED;
`[use]` stayed green (correctly). Restored → constants verified byte-identical.

(The disposition non-regression — `TestAttributingTheBootstrapDoesNotChangeItsDisposition`, 4
fates — is GREEN because the fix adds attribution and SUBTRACTS nothing: no `except`/wrap was
introduced in `bootstrap_session`, so every failure still propagates UNWRAPPED and scout's
reconnect ladder still sees the raw type. That was the contract's disclosed
red-today-for-the-plumbing pin; it is now a live property pin, satisfied.)

---

## GATES

`uv run ruff check .` (repo root) → **All checks passed! (exit 0)**

`./scripts/typecheck.sh` (repo root) → **exit 1, exactly 55 errors in 5 files** — unchanged from
the stated baseline. Every error is in packet-03 comms test files
(`test_comms_tool.py`, `test_comms_promise_registry.py`, `test_message_ledger.py`, and the
`loremaster.messages` ModuleNotFoundError family). **Zero errors in any file I touched** — the
new required `url` kwarg type-checks clean at all 11 owners + the harness. The 55 did not grow.

---

## FLAGS

1. **Writable-set under-enumeration (raised, fixed, disclosed).** The brief's owner list named 8
   files; the contract requires 11. `store/surreal.py` (SurrealStore) and `tasks.py` (TaskLedger)
   were absent from the brief's explicit list but are (a) named in the contract's RED
   `_QUERY_SEAMS` parametrization, (b) found by the grep the brief instructed me to run to "verify
   the full set", and (c) hard compile-time TypeErrors the moment `url` became required. I applied
   the identical one-line `url=self._url` edit the brief authorized for the other owners. This is
   the exact "a lead's own grep silently under-matched and missed a call site" hazard the brief
   warned about, reproduced in the brief's own owner list. No behavioural change beyond passing
   the url.

2. **Pre-existing unrelated typecheck failures (surfaced, not chased).** 55 mypy errors in 5
   packet-03 comms files remain, exactly as the brief documented. Not touched, not grown.

Nothing else outside #151 surfaced during the change. No git state was mutated; the lead commits.
