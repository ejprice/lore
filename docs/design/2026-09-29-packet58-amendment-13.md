# Packet 58 — Amendment 13: FK-r4-1 (admissions exact both ways), F-F's owner, the F-8 exhaustion-record rider

**Author:** sidecar-64 (Fable 5.1 design sidecar) · **Date:** 2026-09-29 · **Task 26** · contract r4 CLOSED at
`4d864c9` (no re-grade, am-12 §3). Each item below is a 58 BUILD requirement at one chokepoint (the cold audit
verifies it), a pinned bound, or a residual — never a contract round.
**Amends:** am-11 §2 (erratum: "the current 8 + 2" was an un-derived count). **Sources read:**
`REPORT-contract-58-r4.md@4d864c9` (§DEVIATIONS D-R4-3/D-R4-6, §FORKS FK-r4-1, §ITEMS row 3/7, BC-r4-5);
`docs/design/2026-09-29-packet63c-amendment-37.md` §6 row F-8; `store/_txn.py` `retry_on_conflict` (:965–:1098, the
`store.retry.exhausted` record at :1091 and the `label is not None` guard above it), `run_query`'s call (:1370,
label+url), the bootstrap's three calls (:1255–:1271, label+url), `execute_transaction`'s txn-path call (:1582,
NO label, NO url; the `last_conflict` re-log after); `_exhaustion_fates.py` (the text-only rows). Names
`lore_verify`'d (`retry_on_conflict` confirmed). grep is hook-blocked → awk/sed, said so.

## 0. Rulings in one screen

1. **FK-r4-1 — (A) confirmed: exact BOTH ways; the six admissions stay DELETED.** `FAULT_CLASS_NAMES` is the
   registry of translations that EXIST, not a catalogue of fault classes that could someday be targets. An
   admitted class with no translating site is a dormant door: a future translate to it would land without the
   adjudication the row's `why_fault` exists to carry. Erratum on am-11 §2: "the author derives the current
   8 + 2" presumed eight targets from the ledgers' fault-base names — a count I did not derive (my own errata
   class). Measured at `a77dc00`: four. **Build requirement:** none beyond the contract pin
   (`test_no_domain_site_translates_exhaustion_into_an_UNADMITTED_class`, BC-r4-5). **Cold-audit check:**
   `translate_targets()` over the built tree == `FAULT_CLASS_NAMES`, both ways. **64b-i consequence, stated so it
   is not a surprise:** if 64b-i's build translates exhaustion into `FindingLedgerError` anywhere, it adds the
   admission row with its `why_fault` in the same commit — one line, and it IS the adjudication. Reading the
   64b rulings (am-7 FK-6: `GovernedInvisible` → `FindingNotFoundError` maps a DENY, not exhaustion; `_transition`
   passes exhaustion through typed), I expect no such site; the pin tells the builder if I am wrong.
2. **F-F — BOUND with a named owner: the 64b pin pass.** The "elsewhere" half (evidence predicates resolved BY
   IMPORT to the marker object, one silent synthetic per predicate as the negative control) is a
   test-instrument proxy weakness in `_exhaustion_fates.py`, not a production defect, and 58's builder may not
   author contract tests. The pass that next touches that file is the **64b pin pass** (F-2 + F-3 + G2 + the
   #319 leg, after 58 lands): it must re-key 64b's own row (`findings dispatcher (64b)`, evidence
   `appends-failed` — one of the eight text-only rows), so the predicate rewrite lands there ONCE for all eight
   (ONE IMPLEMENTATION; a per-row fix is the clone). **Decision point:** that pass's commit, before 64b-i's
   build. **Interim, binding on 58's cold audit:** the adversary's `evidence_probe.py` result (three silent
   synthetics satisfy the predicates) is an ACCEPTED RESIDUAL recorded in the audit report, not a STOP.
   **Re-open trigger:** any NEW row citing a text-only predicate before the pass lands → that row's author writes
   the by-import predicate with it.
3. **F-8 rider — a 58 BUILD requirement at ONE chokepoint, verified by a generated check.** Property: *the ONE
   `store.retry.exhausted` record carries the same three facts on EVERY path into the driver — `label`, `url`,
   `engine_error` (non-empty).* Today the txn path (`execute_transaction`'s `_attempt` → `retry_on_conflict` at
   :1582) passes neither `label` nor `url`, so the `label is not None` guard just above the :1091 record drops all three, and its
   `RetryableConflictSignal()` is raised BARE (no exception in scope), so `last_conflict_cause` stays `None`.
   Chokepoint and mechanism in §1.

## 1. F-8 — the chokepoint

- **Mechanism (production, `_txn.py`, 58's exhaustion-record surface per am-8 §0 / TIERS):**
  (a) the txn path calls `retry_on_conflict(_attempt, deadline_seconds=…, label=<the txn label constant>,
  url=url)` — the `_log_rollback` event's own label is the natural constant, so the exhausted record and the
  rollback record an operator already correlates share the seam name; (b) the txn path's conflict signal carries
  its cause: `raise RetryableConflictSignal() from <typed carrier>(root_cause.raw_result)` — a small typed
  exception (name the builder's; it must NOT be a `SurrealStoreError` subclass, or the fate classifier's
  domain gains a phantom catch) whose `str` is the engine text — so the driver's `last_conflict_cause` is
  non-None and `engine_error` is the same text `_log_rollback` logs. **One record, three facts, both paths;
  no second logger call, no second driver.**
- **The §10 label allowlist (LEAD RULING 2026-07-20, cited in the driver's own comment at :1051) exempted
  exactly this body from `label=`.** With (a) the exemption is no longer needed: **delete the entry** —
  allowlist-the-safe with an empty exemption set is the correct end state. STOP condition for the build: if
  that allowlist pin (a28c's `test_retry_seam.py`, 63c's file, built by then) is exact both ways, the stale
  entry's deletion rides 58's build commit and the cold audit re-checks the pin; if it is one-way, nothing to
  edit. The builder reports which.
- **The generated check (the cold audit runs it; it is not a contract pin — the contract is closed):**
  (i) STATIC: every `retry_on_conflict(` call site in the production tree (AST over the whole tree, the
  am-9 walker) passes `label=` and `url=` — the domain is DERIVED (today five sites: `run_query`, the three
  bootstrap statements, the txn path); a new caller without them is RED by name. (ii) RUNTIME, per derived
  site: drive the path to exhaustion (the driver seam's injection, am-12 §1) and assert exactly ONE
  `store.retry.exhausted` record with `label`, `url` and a non-empty `engine_error`; reach is a checked
  variable (`len(sites driven) == len(sites derived)`). Positive control: the txn path at HEAD (the
  record carries `attempts`/`elapsed_seconds` only) → RED.
- **Ordering:** 63c-i-a's fix round lands am-37 §6 F-8's own half (`last_conflict = None` at `_attempt` entry,
  so the re-logged rollback describes THIS attempt). 58's builder rebases onto it; the two touch the same
  function and compose (reset at entry; carrier at the raise).

## 2. FYI items — agreed, one addition

- r4 §SAT REF-ONLY 36 (63c's generated sweeps over 58's reference `_txn` classes) → a STOP check at the §RE-BASE
  step, re-derived from HEAD: agreed. Addition: the re-base also re-derives `translate_targets()` (item 1) on
  HEAD + 63c-i-a's build — 63c-i-a's F-12 makes the migrate dispatch catch the BASE `SurrealStoreError`, which is a
  catch, not a translate, so no admission moves; the check is what says so.
- `test_task_ledger.py` ×10 red on HEAD + §HELD part 1 and green on the reference: consistent with a
  contract-ahead §HELD; the builder's §RE-BASE run names them.
- #522 (`lore_impact` renders `store.lease` as dead): noted; the lease's callers are the election library's
  thread (dynamic dispatch) — the verdict's astroid bound, not a deletion lead.

No code/tests/store touched; this doc only; no attribution trailer.
