# Packet 58 — kickoff rulings: F-1 hub cap · F-2 terminal dependents · F-4 extraction owner · the task-side guarded-append shell as 64 will govern it · #130 · the contract worklist · the contract-ahead boundary · inventory seeds (sidecar-64, 2026-09-26)

Directive: `REPORT-lead-63c.md@f4511ef` (last entry — 58 runs design + contract + adversary AHEAD, build
serial in the shared tree after 63c-i-a's commit; F-3 is MOOT because 58 lands before 64, pool 30).
Packet file: `docs/plans/v2/58-supersede-reanchor.md` (**P58**). Design of record:
`docs/plans/v2/design/2026-08-11-task-coordination-substrate.md` §2C + §ADDENDUM A-174 (**A-174**).
Findings: #356 (the strand), #130 (the served-claimable lie), #174 (landed), #256 (the findings-side
extraction precedent). Store law consulted (`docs/reference/surrealdb-31-capabilities.md` §2 THROW-on-zero
CAS + server-side `+=`, §4 RELATE bound RecordIDs / `ENFORCED` / edges cascade on endpoint delete, §5
retry driver, §7 closure syntax). HEAD at ruling: `f4511ef`; every symbol below read via lore this
session (`supersede_task`, `_supersede_fragment`, `_transition_fragment`, `_claim_fragment`,
`_relate_fragment`, `_refuse_a_cycle`, `_backfill_blocks_edges`, `direct_dependents`, `_is_blocked`,
`_candidate_statement`, `query_tasks`, `claim_task`, `_render_supersede_result`, `_render_claim_result`,
`_task_status_marker`, `FindingLedger._guarded_append_fragment`, `compose`); `awk` (said so) for the two
txn caps (`TXN_STATEMENT_WARN_THRESHOLD = 800`, `TXN_STATEMENT_HARD_CAP = 5000`) and 57's shell clause.

## 0. The rulings in one screen

| # | fork | ruling |
|---|---|---|
| **F-1** | the hub bound | **REFUSE-AND-TEACH at a DERIVED cap, pinned at cap−1 / cap / cap+1** — never batched across transactions (a partial re-anchor is worse than none, A-174), never the bare `compose` cap error. The cap is NOT a magic number: the ledger BUILDS the fragments, COUNTS the composed body statements (the same count `compose` checks), and refuses BEFORE sending when it would exceed `TXN_STATEMENT_HARD_CAP`, naming N dependents, the cap IN DEPENDENTS (`(HARD_CAP − fixed) // per_dependent`, derived from the builder's own counts), and the bound's re-open trigger. The WARN threshold (800 statements) stays a LOG, never a refusal. §1 |
| **F-2** | terminal dependents | **REWIRE ∀ dependents** — `done`/`wontfix` included. The invariant is `edge ≡ blocked_by` ∀ rows (the boot backfill mirrors ∀ blocker states — its docstring says so); a status-conditional skip creates a second class of rows whose column names a superseded task, which `direct_dependents`, `transitive_blockers` and the next boot's backfill would all read as truth. Terminal dependents COUNT toward the cap (the cap is about statements, not semantics). §2 |
| **F-4** | extraction owner | **58 EXTRACTS the task-side shell; 57 CONSUMES it** (the operator runs 58 now; 57's contract waits on 63c). Pinned STRUCTURALLY so the order cannot silently flip into two extractions: after 58, `tasks.py` contains EXACTLY ONE `IF array::len(…) == 0 { THROW …}` shell producer (an AST pin over the module's string constants — allowlist the one symbol); a 4th hand-rolled shell in 57 reds it. §3 |
| **the shell** | as 64a will govern it | `TaskLedger._guarded_append_fragment(row_id, *, event, set_parts, params, where_conjuncts, preamble, throw_message)` — keyword-only, a LIST of WHERE conjuncts (each parenthesised by the shell) as the ONE extension point; transition, the supersede stamp, claim, and the re-anchor all route through it (mutation-proven). 64a then passes `plan.guard()` as ONE MORE conjunct (kickoff §4.3) — no new shell, no signature break. Claim routes through it (P58 item 2's "or the contract states why not" — it routes) and thereby GAINS a provenance event. §4 |
| **#130** | the claimable partition | (a) a SUPERSEDED row matches NO `status=` filter and is EXCLUDED from `blocked=False` — the served "claimable" set agrees with the CAS; it is still served by an UNFILTERED `query` and by `get`, decorated `[superseded → id]`. (c) the claim-loss render ALREADY names supersession at HEAD (`_render_claim_result`'s `superseded by` branch — P58's UNVERIFIED is now VERIFIED: present) → pinned, not built. §5 |
| **F-3** | MOOT (58 before 64) | the shell's conjunct list is the seam 64a governs through; nothing else. |

**Where I CHOSE between readings (brief-base §2):**
1. P58 item 2 — *"`_claim_fragment` routes through it too, or the contract states why not"*: routing
   changes two claim behaviours (a loss THROWs-and-rolls-back instead of committing an empty UPDATE; a
   win now appends an event). I read ONE IMPLEMENTATION as the governing law and route it, inventorying
   both changes (§7) — the served `ClaimResult` is byte-unchanged. The alternative (a `throw=False`
   knob) would be a second behaviour wearing the shared name.
2. #130 (a) — *"exclude superseded rows from the open/claimable predicates"*: reading A excludes them
   only from `blocked=False`; reading B from every `status=` filter. I pick B: `status=open` is the
   label #130 measured lying, with or without `blocked=`.

---

## 1. F-1 — the hub bound: refuse-and-teach at a derived cap

- **The composed transaction (the shape the count derives from — the contract pins the exact numbers by
  building it, never from this table):** fixed = the supersede stamp through the shell (2: `LET … UPDATE`
  + `THROW`) + `CREATE` the successor (1) + `RELATE` per successor dependency (K, #174's resolved set)
  + ONE `DELETE blocks WHERE in = $old` (1 — every outgoing edge of X corresponds to a dependent, since
  `edge ≡ blocked_by`, so one statement retires them all; never N per-pair scans of the un-indexed edge
  table); per dependent = the re-anchor through the shell (2: `LET … UPDATE Y SET blocked_by =
  array::distinct(array::map(blocked_by, |$b| IF $b = $old THEN $new ELSE $b END)), updated_at =
  time::now(), provenance.events += [$note_i] WHERE blocked_by CONTAINS $old` + `THROW`) + `RELATE
  $new->blocks->$y` (1) = 3. So `cap_dependents(K) = (TXN_STATEMENT_HARD_CAP − (4 + K)) // 3` — ≈1665 at
  K=0. ⚠ The closure/`IF … THEN … ELSE … END` spelling is the contract's to PROBE on 3.2.4 before it is
  pinned (store-ref §7: closures in `array::map` are measured; the conditional inside one is not) — a
  parse failure there is a STOP that reshapes the rewrite to a client-computed array + a `blocked_by =
  $expected` CAS conjunct (the fallback, named; it costs one extra pre-read per dependent and a benign
  race on concurrent supersedes of two different blockers of the same Y).
- **The refusal (teaching, before any write):** *"task X has N dependents; one supersede re-anchors at
  most `cap` dependents (the store's transaction bound, derived) — refused, nothing changed. This is a
  pinned KNOWN BOUND (58 F-1); a hub this size is not expected in the fleet — file it, and the bound's
  re-open trigger is this refusal."* No remedy is invented (there is no dependent-rewire verb; a fake
  remedy is worse than a named bound).
- **Why not the alternatives:** BATCH across txns — a crash between batches strands SOME dependents,
  which A-174 names as worse than none, and it is unobservable from the render; ACCEPT the raw 5000 —
  `compose` refuses with a generic count message an agent cannot act on (CONSUMER LAW), and the refusal
  would come AFTER the pre-checks ran; a LOWER hand-picked cap (e.g. under the 800 WARN) — a constant
  nobody derived is the class this repo has the most receipts against, and the WARN is a log by design.
- **RIDERS — and pin it like this:** (i) `TaskLedger.max_reanchor_dependents(successor_blocked_by_count)`
  is the derived accessor the fixture asks; the pin seeds `cap−1` (succeeds, every dependent re-anchored),
  `cap` (succeeds), `cap+1` (refused, byte-inert: X un-stamped, no successor, every dependent's row +
  edge set unchanged — `SELECT *` before == after); (ii) mutation: change the per-dependent statement
  count in the builder (add a statement) → the derived cap moves and the three-point pin re-keys itself
  (a pin holding a literal cap reds — that is the point); (iii) the count the refusal serves == the count
  `compose` would have counted (build the fragments in the test and compare — no formula drift); (iv)
  the WARN threshold crossed (a fixture between 800 and the cap, sized from the same accessor) → ONE
  warning logged, the supersede SUCCEEDS.

## 2. F-2 — rewire every dependent

- **Ruling: ∀ dependents, whatever their status.** `_backfill_blocks_edges` mirrors the column *"∀ ROWS
  and ∀ BLOCKER STATES"* and says why; a re-anchor that skips terminal dependents leaves `Y.blocked_by ∋
  X` with `X→blocks→Y` intact — the next boot mints NOTHING (the edge exists) so the drift is permanent,
  `direct_dependents(X)` keeps listing Y forever, and any future read that walks `blocks` from X' misses
  Y. The "legal optimisation" saves 3 statements per done row and buys a second class of truth.
- **The provenance note is appended to terminal rows too** — `done` rows are the fleet's completion
  record and a rewired pointer on one is a fact worth recording (the rollup reads `updated_at`; a
  re-anchor stamps it, so a re-anchored done task re-appears in the next rollup window — ACCEPTED and
  inventoried: the activity signal is honest, the work MOVED under it).
- **RIDERS:** N ≥ 3 dependents with DISTINCT statuses (`open`, `claimed`, `done`) → all three rewired,
  all three noted, `edge ≡ blocked_by` holds ∀ (no `X→Y` edge survives; exactly one `X'→Y` per dependent);
  a dependent already naming X' → deduped (one entry, one edge — the `UNIQUE`-less edge table would
  otherwise double); the boot backfill after a re-anchor is a NO-OP (mints 0, records 0).

## 3. F-4 — 58 extracts, 57 consumes; pinned structurally

- 58 lands `TaskLedger._guarded_append_fragment` (§4) and routes its four callers. 57's `assign` /
  release verbs (P57 item 1 *"after packet 58 extracts … route through it"*) CONSUME it. The order is
  now a FACT (58 runs first, operator), so the *"if 57 lands first, 57 extracts"* clause is retired.
- **The structural pin (58's, inherited by 57):** an AST scan of `tasks.py` finds every string constant /
  f-string static part carrying the `THROW` keyword inside a guarded-CAS shape; the allowed set is EXACTLY
  `{_guarded_append_fragment}` (allowlist the safe). A second producer reds by symbol name. Its
  discriminator: a synthetic module with a hand-rolled `LET … THROW` in a second function is FOUND.
- **The cross-module unification (findings + tasks share ONE shell, home `loremaster.store`)** stays a
  LEDGERED DRY item with the trigger *"the third ledger that needs a guarded append"* — filed this session
  as a finding (§9) so P58 entry check 4 is met; NOT built here (A-174: *"do NOT bolt the cross-module
  lift onto #356"*).

## 4. The task-side shell — as 64a will govern it (so 58's shape pre-empts nothing)

```python
@staticmethod
def _guarded_append_fragment(
    row_id: str, *,
    event: dict[str, Any] | None,          # appended server-side (provenance.events += [$ev]); None = no append
    set_parts: Sequence[str] = (),         # extra SET clauses (status, owner, superseded_by, blocked_by rewrite, …)
    params: Mapping[str, Any],             # every bound value, NAMESPACED by the caller (compose refuses collisions)
    where_conjuncts: Sequence[str] = (),   # each wrapped "(…)" by the shell and AND-joined — THE extension point
    preamble: Sequence[str] = (),          # statements before the guarded UPDATE (claim's LET $clm_resolved)
    throw_message: str,                    # the ledger's own THROW text (its lost-race vocabulary)
) -> TxnFragment
```
- Emits `[*preamble, "LET $<var_i> = (UPDATE type::record('task', $id_i) SET <set_parts…>[, updated_at =
  time::now()][, provenance.events += [$ev_i]] WHERE (c1) AND (c2) …)", "IF array::len($<var_i>) == 0
  { THROW '<msg>' }"]`. The LET variable and every param name carry an INDEX (the `_relate_fragment`
  `{index}` idiom) so N re-anchor fragments compose in one transaction without `TxnParamCollisionError`.
- **The four callers and what each passes:** `_transition_fragment` → `set_parts=[status=$to, (owner =
  NONE, claimed_at = NONE on release), (summary, report_path on done)]`, `where_conjuncts=[status =
  $from, superseded_by IS NONE]`; the supersede STAMP → `set_parts=[superseded_by = $new]`,
  `where_conjuncts=[superseded_by IS NONE]`; `_claim_fragment` → `preamble=[LET $clm_resolved = …]`,
  `set_parts=[owner=$owner, status='claimed', claimed_at=time::now()]`, `where_conjuncts=[status =
  'open', owner IS NONE, superseded_by IS NONE, array::len(array::distinct(blocked_by)) =
  array::len($clm_resolved)]`, `event={actor, action:"claim", at}` (NEW — §7 item 3); the RE-ANCHOR →
  `set_parts=[blocked_by = <the replace expression>]`, `where_conjuncts=[blocked_by CONTAINS $old]`,
  `event={actor, action:"dependency_reanchored", from: X, to: X', at}`. `updated_at = time::now()` is
  appended by the shell unconditionally (every caller stamps it today; the re-anchor now does too — §2).
- **How 64a governs it without a second shell:** `where_conjuncts=[…, plan.guard_fragment]` with
  `plan.guard_params` merged into `params` (kickoff §4.3 step 2); the audit fragment is composed by
  `plan.compose(...)` around the shell's fragment (step 3); the ONE #407 helper classifies a rollback
  (step 4). Nothing in this signature changes at 64a. The kickoff's `authorize_guarded(projection=)`
  merge removes the ledger's pre-read then; 58 keeps `_select_row` as today.
- **Claim's THROW (the chosen reading, stated):** a LOSING claim now THROWs and rolls the transaction
  back; `claim_task` catches the store rejection (the `_transition`-shaped `except` ladder — transport /
  exhausted-contention pass through; a domain rollback → the post-CAS owner-identity read) and returns
  `ClaimResult(claimed=False, …)` exactly as before. Served bytes unchanged; `updated_at` untouched on a
  loss (it never was — the empty UPDATE matched nothing).
- **RIDERS — and pin it like this:** (i) mutation of SHARING: perturb the shell's `THROW` guard (e.g.
  `== 0` → `== -1`) → transition, supersede-stamp, claim (a loss no longer detected) AND re-anchor pins
  ALL red — a caller that stays green is a private copy; perturb the `provenance.events +=` clause → the
  three event-bearing callers' provenance pins red; (ii) the AST one-producer pin (§3); (iii) param-name
  isolation: N=3 re-anchors + the stamp + the CREATE compose without collision (a pin that composes the
  real fragments); (iv) `updated_at` stamped by the shell ∀ callers (a claim WIN stamps it — already true;
  the re-anchor now does — new).

## 5. #130 — the served claimable set agrees with the CAS

- **(a) the partition:** `_candidate_statement` gains `AND superseded_by IS NONE` whenever a `status=`
  filter is supplied (a superseded row's stored status is stale by construction — supersede never
  touches `status`; serving it under a status label is the lie #130 measured); `_is_blocked`'s partition
  treats a superseded row as NOT claimable (`blocked=False` excludes it; `blocked=True` does not claim it
  either — it is neither, it is superseded). An UNFILTERED `query` and `get` still serve it decorated
  `[superseded → id]` (the chain stays visible — finding #7's virtue preserved). `status=superseded` stays
  *"(no tasks matched)"* — promoting `superseded` to a status is #130 shape (b), 57's territory, not
  58's.
- **(c) the loss render:** VERIFIED PRESENT at `f4511ef` — `_render_claim_result` branches `task.
  superseded_by is not None` → `reason = "superseded by <id>"` (and the R10(iii) `superseded_blockers`
  branch names a superseded BLOCKER). 58 PINS both, edits neither. After 58 the `superseded_blockers`
  branch is reachable ONLY for LEGACY strands (rows superseded before 58 deployed — real on `:18500`);
  the pin seeds one raw (bypassing the ledger — the only door) and asserts the render still names it.
- **RIDERS — pin by MUTATION, both directions (#130's own invariant):** supersede X → X vanishes from
  `query status=open` and from `query blocked=False` (any status), remains in an unfiltered `query` with
  the marker and in `get`; ∀ rows served by `query status=open blocked=False` with `owner None`, a claim
  WINS (drive it — the "everything served as claimable is claimable" direction); a row the CAS refuses
  (superseded / owned / blocked) is never served there (the reverse). Fixture: ≥3 rows across the three
  refusal causes + 2 genuinely claimable.

## 6. The contract worklist — pins · wrong builds · discriminating fixtures (P58's exit list, made concrete)

| area | pins ("pin it like this") | wrong build it kills | fixture that discriminates |
|---|---|---|---|
| re-anchor mechanics | supersede(X→X') with N=3 dependents (open / claimed / done) → each `blocked_by` has X' and not X; one `X'→blocks→Y` edge each; NO `X→blocks→*` edge survives; one `dependency_reanchored` event per Y naming X, X', the actor; `updated_at` stamped on each Y; X stamped `superseded_by`; X' open with #174's resolved deps | a rewire that updates the column but not the edge (the boot "heals" it — the pin runs BEFORE any boot: assert the edge set directly); one that skips done rows; one that appends the note to X instead of Y | distinct statuses; a Y that ALSO names X' already (dedupe → one entry, one edge); a Y with two blockers (only the X entry rewritten) |
| atomicity | inject a store failure at dependent k of N (the injected-handle idiom, 63-rulings §10.6 rider iii) → X un-stamped, X' absent, ALL N unchanged (column + edges + provenance), no partial; positive control: the same fixture without the injection completes | a per-dependent txn; a stamp that commits before the rewire | N=3, k∈{1,2,3} |
| cycle-closing rewire | X' created with explicit `blocked_by=[Z]` where Z is transitively blocked_by Y (a dependent of X) → refused as `TaskCycleError` naming the cycle, rolled back whole (X un-stamped, no X') | a cycle check over the un-rewired graph (finds nothing) | the legacy-cycle step-over control from `_refuse_a_cycle`'s own pins (a pre-existing loop elsewhere does not refuse) |
| F-1 cap | cap−1 / cap / cap+1 from the derived accessor; byte-inert refusal; the served count == the composed count; the WARN-crossing fixture succeeds with one log line; mutation of the per-dependent count moves the cap | a literal cap; a refusal after the stamp; the bare `compose` error served | sized from `max_reanchor_dependents(k)` for k∈{0,2} |
| the shell | the sharing mutations (§4 rider i); the AST one-producer pin (§3) with its synthetic discriminator; param isolation (N=3 + stamp + create); claim loss = `ClaimResult(claimed=False)` + zero writes + NO event; claim win = +1 `claim` event | a fourth clone; a claim that raises on loss; a shared name over a private body | the three callers driven in one test module with the perturbation declared from `--collect-only` |
| #130 | §5's both-direction pins; the legacy-strand render pin (raw seed) | a `blocked=False` that still serves superseded rows; a `status=open` that does; a loss render that says "unowned … (status open)" for a superseded row | ≥3 refusal causes + 2 claimable |
| backfill idempotence | after a re-anchor, `_backfill_blocks_edges` mints 0 and records 0 phantoms; after a REFUSED hub supersede likewise (nothing changed) | a re-anchor that leaves the old edge for the boot to "heal" (it cannot — the edge exists; it would DOUBLE it) | one boot after each |
| the render (held patch) | `_render_supersede_result` names *re-anchored N dependent(s) to X'* from the ledger's `SupersedeResult.reanchored` (the pre-write list — post-write `direct_dependents(X)` is `[]` by construction); the *"STRANDED"* sentence is GONE (a sweep for `STRANDED` over `server.py` → 0 hits); the successor's `blocked_by` clause unchanged (#174) | a render that calls `direct_dependents` after the write (always empty → the receipt lies by omission); a render that keeps the stranded warning | N=0 (byte-identical to today's no-dependents render) and N=3 |
| DRY | the AST one-producer pin; the cross-module item ledgered (§9), not built | a lift into `lorerunes` | — |
| M | every mutation proof declared from `--collect-only`, diffed both ways (`scripts/mutation_proof.py`); scratch reference builds print `loremaster.__file__` | — | — |

**Required-green builds (am-14's lesson):** a supersede with ZERO dependents (byte-identical render to
today; K successor RELATEs only); a supersede whose successor inherits X's `blocked_by` (#174 None);
one with `[]`; one with `[ids]`; a double supersede race (the loser's whole txn rolls back — no
re-anchor lands for the loser, the winner's does); a supersede of a task whose dependents include a
LEGACY phantom-blocked row (the phantom entry is untouched; only the X entry is rewritten).

## 7. Removed-behaviour inventory seeds (Phase 0 / adversary P6b — the author enumerates; adjudicate each)

1. `_render_supersede_result`'s *"⚠ N task(s) … are now STRANDED — re-point them"* → REPLACED by the
   re-anchored receipt (dropped-deliberately: the strand no longer occurs; the pin that asserted the
   warning text is DELETE-WITH-REPLACEMENT; the *"WARNS, never rewrites"* docstring and R10(iv)'s
   *"dependency transfer is DEFERRED"* prose → REWRITTEN — the deferral is discharged).
2. `direct_dependents(X)` after a supersede returned the stranded ids → returns `[]` (CHANGED by
   construction; every reader that consumed it post-write — the render — moves to the receipt).
3. `_claim_fragment` wrote NO provenance event → a WIN appends `{actor, action:"claim", at}` (ADDED —
   the provenance render carries one more event; the rollup's leg-1 unaffected).
4. A losing claim committed an empty UPDATE → the txn rolls back via THROW (CHANGED mechanism; served
   `ClaimResult` PRESERVED-WITH-PIN; zero writes either way).
5. `query status=<s>` served superseded rows under that status → EXCLUDED (dropped-deliberately: #130);
   `query blocked=False` served them → EXCLUDED; the unfiltered `query`/`get` marker PRESERVED (#7).
6. The three hand-rolled task shells → ONE (`_transition_fragment`/`_supersede_fragment`/`_claim_
   fragment` become thin callers; their docstrings' *"mirrors `_supersede_fragment`'s shape"* prose →
   REWRITTEN).
7. `supersede_task` returned `str` (the successor id) → returns `SupersedeResult(successor_id,
   reanchored: list[str])` (CHANGED API; every caller — the dispatcher branch, scripts — adjudicated;
   `AppContext.tasks` supersede branch is a held-patch edit).
8. The supersede's transaction size was O(K) → O(K + 3N) (CHANGED cost; the cap + the WARN log name it).
9. A re-anchored `done` dependent gets `updated_at` stamped → re-appears in the next rollup window
   (ACCEPTED, §2).
10. R10(iii)'s `superseded_blockers` loss render → PRESERVED for legacy strands only (reachable by raw
    seed; pinned so it is not "cleaned up" as dead).

## 8. The contract-ahead boundary — by file

| lands NOW as NEW files (58 contract) | held integration patch (63c-shared files; applied after 63c-i-a's commit, before 58's build) |
|---|---|
| `loremaster/tests/test_supersede_reanchor_58.py` (§6 rows 1–4, 7 backfill) · `test_task_guarded_shell_58.py` (§4 riders, the AST one-producer pin + discriminator) · `test_task_claimable_partition_58.py` (#130 both directions + the legacy-strand render pin — the render pin reads the EXISTING `_render_claim_result`, no edit) · `scripts/probe_reanchor_58.py` (P58 entry check 3: reproduce the strand live on `:18000` — a throwaway DB, exit 0 with a positive control — AND the `array::map` + `IF…THEN…ELSE…END` closure spelling probe from §1, committed) | `loremaster/loremaster/server.py`: the `tasks()` supersede branch consumes `SupersedeResult`; `_render_supersede_result(task_id, successor_id, reanchored, successor_blocked_by)` rewritten (the STRANDED sentence gone); the `lore_tasks` description's supersede sentence (if it promises a warning); + the pins that assert the new render text (`test_supersede_render_58.py` — a NEW file, but RED-for-the-right-reason only once the patch lands, so it ships WITH the patch) |
| EXISTING task test files (`test_task_*`, `test_tasks_*` — 58's own domain, not 63c's) MAY be edited by the contract: every pin asserting the STRANDED text, the `str` return of `supersede_task`, the empty-UPDATE loss, or a claim with no event is a DUAL row (DELETE-WITH-REPLACEMENT / re-keyed), adjudicated in the contract report | — |

**Re-verification on 63c-i-a's committed base:** the NEW files' declared RED set re-run; `tasks.py` is
disjoint from 63c so no RED reason should move; the held patch's render pins are RED against the pre-
patch `server.py` for the right reason (the STRANDED text present) — checked, not assumed.

## 9. Flags · findings · DRY · discipline

- **Filed this session (P58 entry check 4):** the cross-module guarded-append DRY item — findings +
  tasks share ONE shell, home `loremaster.store` (a `TxnFragment` builder — never `lorerunes`), trigger
  *"the third ledger that needs a guarded append"* (finding number in the report).
- **FLAG:** the `array::map` closure with a conditional is UNPROBED on 3.2.4 (§1); the probe is a
  deliverable of the contract wave, and its fallback is named.
- **FLAG (57):** P57 item 1's *"if 57 lands first, 57 extracts it"* clause is retired by the operator's
  ordering; 57's contract cites `TaskLedger._guarded_append_fragment` by name.
- **FLAG (64a):** the kickoff §4.3 shape is confirmed against this shell (`where_conjuncts` is the
  guard's seam; `plan.compose` wraps the fragment); 64a's contract cites §4 here.
- **Packages considered:** none — every mechanism extends a shipped seam (`_relate_fragment`,
  `_refuse_a_cycle`, `direct_dependents`, `compose`, the findings shell's shape).
- **DRY ledger (candidates; the author owns names/rows):** `TaskLedger._guarded_append_fragment` —
  EXTEND the findings shell's shape (query `lore_get_symbol("FindingLedger._guarded_append_fragment")`;
  a parallel one per ledger until the ledgered unification); `max_reanchor_dependents` — a derived
  accessor over `compose`'s cap (REUSE `TXN_STATEMENT_HARD_CAP`); `SupersedeResult` — a typed carrier
  (HAND-ROLLED; `lore_search("supersede result successor reanchored")` → nothing to extend).
- No code/tests/store touched; no pytest; this doc only; no attribution trailer on the commit.
