# 58 — Supersede RE-ANCHORS its dependents (#356) + the task-side guarded-append extraction
size ~0.20 wu · wave L · depends: 05b (#174 ✅ DONE); **sequencing vs packet 64 ruled at kickoff (Hazards)**
· DEPLOY: rides the next joint image (packet 65 cutover) unless the operator rules otherwise
FIRST READ (store law — MANDATORY): `docs/reference/surrealdb-31-capabilities.md` (§2 THROW-on-zero-rows
CAS + server-side `+=` append; §4 RELATE bound-RecordID form, `ENFORCED` edges, dangling-edge hazard #105)
Design of record: `docs/plans/v2/design/2026-08-11-task-coordination-substrate.md` **§ADDENDUM A-174**
(and §2C for the grounded mechanism). Recall: `lore_recall("#356 re-anchor")` (operator ruling 2026-08-11).
Own contract → adversary → build — never a drive-by on another packet's verb pass (design-problem rule).

**Provenance:** minted 2026-08-11 at 05b close-out — the re-anchor-with-note the operator chose over
refuse-and-teach. `treat-superseded-terminal` is **REJECTED** (X' may be unfinished → would prematurely
unblock Y). Refuse-and-teach is NOT shipped alongside: re-anchor makes the strand impossible.

## Mission
On `supersede(X → X')`, every dependent Y (`blocked_by ∋ X`) follows the work to X': `blocked_by`
rewired X→X', the `blocks` edge re-mirrored, a cycle re-check, and a provenance note on each Y naming
the original blocker — all in ONE transaction, so a dependent is never stranded on a superseded row.

## What exists today (read 2026-09-24 at `d237ad7` — cite symbols, not lines)
- `TaskLedger.supersede_task(task_id, *, subject, description, created_by, blocked_by=None)` — the #174
  sentinel landed (None inherits, `[]` clears, `[ids]` replaces). It composes
  `TaskLedger._supersede_fragment`: guarded stamp `superseded_by` (+ server-side
  `provenance.events += [$event]`) → `IF array::len(...) == 0 { THROW }` → `CREATE` successor. It does
  **nothing to dependents** (the #356 strand is live).
- `TaskLedger._is_blocked` resolves a blocker iff `status ∈ TERMINAL_STATUSES` and ignores
  `superseded_by`; the claim CAS (`_claim_fragment`) agrees. Reuse seams exist and are verified:
  `TaskLedger.direct_dependents`, `TaskLedger._relate_fragment`, `TaskLedger._refuse_a_cycle`.
- `blocks` edges are `ENFORCED` and mirrored from `blocked_by` ∀ verbs; `_backfill_blocks_edges` runs at
  EVERY boot and mints any missing edge the column implies — so a rewire that updates the column but
  forgets the edge is silently "healed" at next boot (an old-edge leftover is NOT healed — it is a
  stale extra edge). Write-time rule R10(ii) refuses a superseded blocker on `create`.
- **The DRY fact (#256), re-verified:** findings extracted `FindingLedger._guarded_append_fragment`
  (optional `status_target`/`expected_from`); the task side has **no** `_guarded_append_fragment`
  (`lore_verify` → not_found) and hand-rolls the guarded append in `_transition_fragment`,
  `_supersede_fragment`, `_claim_fragment` (3×). Compose cap: `TXN_STATEMENT_HARD_CAP = 5000`,
  `TXN_STATEMENT_WARN_THRESHOLD = 800` (`store/_txn.py`).

## Scope IN
1. **Re-anchor inside the supersede transaction**: for each Y in `direct_dependents(X)` — rewrite
   `blocked_by` (replace X by X', dedupe if Y already names X'), DELETE the `X→blocks→Y` edge, RELATE
   `X'→blocks→Y` via `_relate_fragment`, append `{actor, action: "dependency_reanchored", from: X, to:
   X', at}` to Y's `provenance.events`; `_refuse_a_cycle` over the rewired graph (a rewire CAN close a
   cycle: X' transitively blocked_by Y) → refuse + roll back the whole supersede, teaching which cycle.
2. **⚠ THE DRY ISSUE (operator-required citation): extract a TASK-side guarded-append shell**
   (mirroring `FindingLedger._guarded_append_fragment`) that `_transition_fragment`, the supersede stamp
   and the new re-anchor note ALL route through. **Never a 4th hand-rolled clone.** Prove sharing by
   MUTATION (perturb the shared append clause → transition, supersede AND re-anchor pins all redden).
   `_claim_fragment` routes through it too, or the contract states why not (ROUTING IS NOT SHARING).
3. **The HUB bound**: statements scale ~1 + ~3N (design estimate — the contract derives the exact
   per-dependent count). Crossing 800 warns; crossing 5000 is a build-time `SurrealStoreError` from
   `compose` — i.e. a hub supersede FAILS WHOLE. Fork F-1 rules the shape; either way it is PINNED
   (a known bound that goes RED the day someone changes it) and the refusal TEACHES.
4. **#130 residue** (acknowledged): `TaskLedger._candidate_statement` has NO `superseded_by` clause —
   `query_tasks(status="open", blocked=False)` still serves superseded rows the claim CAS refuses
   (ledger level confirmed by reading; the served render decorates `[superseded → id]` — whether the
   claim-LOSS render now names supersession: UNVERIFIED). IN: make the claimable partition agree with
   the CAS (finding's shape (a)) + the claim-loss render names the real reason (shape (c)); pin both
   directions by mutation ("everything served as claimable is claimable").

## Scope OUT (surface to operator if encountered)
- **The cross-module unification** (findings + tasks share ONE guarded-append shell, home
  `loremaster.store` — a SurrealQL `TxnFragment` builder, NOT `lorerunes`, which is stdlib-only and holds
  predicates). **58 does NOT do it — 58 LEDGERS it** as its own DRY item with a named trigger ("the third
  ledger that needs a guarded append"). Entry check confirms or mints that ledger row (existence UNVERIFIED).
- Packet 57's `assign`/release verbs; promoting `superseded` to a real status (#130 shape (b)).

## FINDINGS OWNED (IN / bound / fork)
- **#356** — IN (the mission). · **#130** — IN (item 4). · **#256** — the cited DRY precedent; not
  re-opened. · the cross-module DRY item — ledgered, not built (above).

## FORKS (questions — operator rules at kickoff)
- **F-1 hub bound**: cap dependents and refuse-and-teach above the cap · batch the rewire across txns
  (breaks atomicity — a partial rewire is worse than none, design A-174) · accept the 5000 cap as the
  bound. Rec: refuse-and-teach at an explicit cap below 5000, pinned.
- **F-2 terminal dependents**: skip a `done`/`wontfix` Y (legal optimisation, smaller txn) or rewire it
  for DAG consistency (`edge ≡ blocked_by` holds ∀ rows — the backfill mirrors ∀ blocker states)?
  Rec: rewire (the invariant is ∀-rows; an optimisation that breaks it is a false clear for the graph read).
- **F-3 governance under 64**: if a dependent Y lives in a scope the superseder cannot WRITE, does the
  supersede refuse, or rewire as a system effect? Only real if 58 lands after 64.
- **F-4 extraction owner vs 57**: 57's `assign`/release also want the shell. ONE extraction — whichever
  packet runs first builds it; the other consumes it.

## Hazards
- **File overlap with packet 64** (governed retrofit of tasks + findings — owner+scope, PDP routing,
  write allowlist). 58 rewrites the SAME fragments (`_transition_fragment`, `_supersede_fragment`) 64
  must govern, and adds a new multi-row write. Before 64: 64 inherits one shell to govern (cheaper) but
  must inventory 58's re-anchor write. After 64: 58's re-anchor must pass the governed write gate from
  birth and F-3 becomes live. **Rec: 58 BEFORE 64** (the extraction shrinks 64's surface) — operator rules;
  either way the later packet's Phase-0 inventory names the other's writes.
- Peer 63c work was uncommitted in the shared tree at this writing; start from a fetched, committed base.

## Entry check (RELATIVE facts only)
1. `lore_verify loremaster.tasks.TaskLedger._guarded_append_fragment` → still not_found (else the
   extraction already happened — re-scope item 2 to CONSUME it).
2. `supersede_task` still composes no dependent rewrite (read it); #356/#130 not resolved.
3. Reproduce the strand live on the TEST store (`:18000`): Y blocked_by X, supersede X → Y stays blocked.
4. The cross-module DRY ledger row exists, or mint it now.
5. Suite green at HEAD; `pending_contract_gate.py --currency` 0 RED_ORPHANED.

## Exit
**contract → contract-adversary (MANDATORY) → build → cold REFUTE audit → commit.** Gates: scoped
pytest + full suite ALONE `-n 12` (never `-n auto`, #466) + `scripts/typecheck.sh` + `uv run ruff check .`
+ `uv run python scripts/pending_contract_gate.py --currency` 0 RED_ORPHANED. Required pins: atomicity
(one injected failure at dependent k of N ⇒ X unstamped, X' absent, ALL N unchanged — constructed, with a
positive control); cycle-closing rewire refused + rolled back; `edge ≡ blocked_by` holds after re-anchor
(no stale `X→Y` edge); N ≥ 3 dependents with distinct statuses (no small-N monoculture); hub-bound pin at
cap−1 / cap / cap+1; shared-shell mutation proof. Findings resolved with receipts; INDEX row + Log.
