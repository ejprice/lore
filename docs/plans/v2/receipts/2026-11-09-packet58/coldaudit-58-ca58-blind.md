# Cold audit, packet 58: contract-blind diff read (ca58-blind)

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read
- State: done-with-deviations. Verdict: **NO-GO on four major findings** (3 constructed live on the TEST store, 1 constructed by a mutation probe). None blocks every user, and none is a data-loss path.
- Deviations: (1) the scratch copy's HEAD is `96ea7f5`, not `aa4ea04`. `96ea7f5` is a docs-only commit (`docs/plans/v2/58-supersede-reanchor.md`, +5 lines, contents not read because the file is withheld); the tree content was checked out at `aa4ea04`. (2) The mutation probe (F4) is a store probe, not a pytest run, so it does not go through `scripts/mutation_proof.py`. Running tests was withheld from this dimension. Restore was proven byte-exact. (3) The probes take their TEST-store credential by EXECUTING `loremaster/tests/_surreal_harness.py`, the same way `scripts/probe_hub_txn_58.py` does. I did not open the file.
- Packages considered: none (no mechanism specified). The build's `more-itertools.constrained_batches` (strict=True) is a package already in use, not a hand-rolled packer.
- Odoo-20 portability: n/a (no Odoo seam touched).
- Reuse ledger: 22 new symbols, all dispositioned (§3). Two are One-Implementation violations: F4, and the duplicated claimable rule (R-3).
- Graded: aa4ea04 · HEAD-at-report: 96ea7f5 · DIFFERENT (1 behind; docs-only, so no production symbol moved).
- Decisions needed: F1 (should the heal run the cycle guard?), F2 (should superseded rows be hidden under a status filter, and how is that named?), F3 (should a re-anchor stamp `updated_at`, and should terminal dependents be re-anchored at all?). Each is a ruling for the lead or the operator.
- Receipts: §1 findings · §2 removed-behaviour inventory · §3 reuse table · §4 probe instruments (committed nowhere; pasted paths below are the scratch copies: see §4 note) · logs in `scratchpad/ca58/blind-notes/` (named in §4).

## Routing table (written before the first sweep)
| step | tier | who | why |
|---|---|---|---|
| read am17 patch + 8-file diff | 3 | me | the audit itself; a sampled draft would miss self-sealing semantic errors |
| removed-behaviour inventory | 3 | me | each verdict depends on state elsewhere (claim render, rollup, classifier): split rule keeps it with me |
| reuse lookups (lore_impact / lore_search, ~22 symbols) | 1-batch | me, one parallel batch | small set; I read all of it anyway |
| prose sweep for retired supersede claims | 1 | me, one grep (76 prod files, 30 hits, each adjudicated) | small output, on the critical path |
| store probes P1-P5 | 3 | me | construction for findings I am asserting |

## 1. Findings (each with its receipt). The probe logs carry tree_id `TREE=40f080f6…` (aa4ea04 content).

### F1 (major, HIGH): the boot straggler heal writes a `blocked_by` CYCLE, logs success, and nothing ever records it
- Where: `TaskLedger._plan_heal_rows` / `_reanchor_stragglers` (tasks.py, added in 60b51c4..aa4ea04). The heal rewrites `old → chain head` with no `_refuse_a_cycle` over the rewritten columns. The live supersede runs that guard (`supersede_task`: `_refuse_a_cycle({new_id: deps, **rewired}, minted={new_id})`).
- State: a pre-58 (un-re-anchored) supersede of X whose successor H has `blocked_by=[D]`, where D has `blocked_by=[X]`. Pre-58 code accepted this, because its cycle check saw only `{H:[D]}`. On the first boot of packet 58 the heal rewrites D `[X] → [H]`, giving H↔D.
- Receipt: `probe_blind.py` P2, logs `probe_blind.log` and `probe_blind_p2.log`:
  `P2-control: live supersede REFUSED: TaskCycleError` · `P2 cycle D<->H written by heal: True` · `P2 blocks edges: … ('D','H'), ('H','D')` · `P2 heal log events: INFO:task.backfill.stragglers_reanchored` · `P2 second-boot WARNING+ records from loremaster.tasks: NONE`.
- Consequences:
  - Before the heal, D's claim served the R10(iii) text "a SUPERSEDED blocker can never resolve … block on the successor", which is honest and permanent. After the heal it serves "blocked_by [H] unresolved", which invites polling, and H likewise waits on D, forever.
  - The heal reports the row as healed (INFO, counted).
  - `_refuse_a_cycle`'s docstring claims such a legacy loop is one "ensure_ready's backfill has already RECORDED". The second boot shows no record.
- Reachability: only on a store holding pre-58 supersedes of this shape. Production occurrence was not measured (I never touch :18500).
- Class: the heal is a second writer of `blocked_by` that bypasses the write-path invariant. Closing rule: route the heal's rewritten columns through the same `_refuse_a_cycle`, and skip and record a row that would close a cycle, as it already does for phantom and cyclic chain heads.

### F2 (major, HIGH): `query_tasks(status=…)` and `query_tasks(blocked=…)` now silently drop superseded rows. Neither the served description nor the docstring says so
- Where: `_candidate_statement`: `if exclude_superseded or status is not None: clauses.append("superseded_by IS NONE")`, plus `query_tasks` passing `exclude_superseded=blocked is not None`.
- Receipt: `probe_blind.py` P1: `P1 A.status=open A.superseded_by=<successor>` · `A in query()=True A in query(status=open)=False A in query(blocked=False)=False` · `counts: query()=2 query(status=open)=1`.
- Served text: the served `status` parameter says "For 'query', an optional exact-status filter" (server.py `tasks` Field). `query_tasks` Args: "status: … restrict to tasks in this exact status." Both are unchanged.
- Removed behaviour: a superseded row whose `status` is still open used to be listed under `status=open`, rendered `[superseded → <id>]` (finding #7's marker exists for exactly this). The unfiltered listing still shows it, so the two views disagree on membership. Excluding it from the `blocked` partition is defensible (it is not claimable). Hiding it under an equality filter is a Leg-1 scope diff that the render does not name.
- I make no ruling on which is right. Either name the exclusion in the served description and the render, or drop it from the `status` path.

### F3 (major, HIGH): a supersede (and the boot heal) re-stamps `updated_at` on EVERY re-anchored dependent, including DONE ones, so the rollup re-serves old completions as new activity
- Where: `_guarded_append_fragment` always appends `updated_at = time::now()`. `_reanchor_fragments` routes every dependent (any status, including superseded ones) through it, and so does the heal.
- Receipt: `probe_blind_p3.py`, log `probe_blind_p3.log`: `P3 reanchored=['D(done)']` · `updated_since(cursor) rows: [('X','done',True), ('D(done)','done',True)]` · `D in window=True E-control in window=False`. D was finished before the cursor.
- Served consequence: the rollup's leg 1 is headed "tasks transitioned" (server.py rollup render), and its "reports registered" line is built from `task_rows` filtered to `status == done and summary is not None`. A supersede of a hub with N done dependents re-registers N old reports. The first boot of packet 58 on a legacy store does the same for every straggler.
- False docstring: `updated_since` says the column is stamped by claim, transition and supersede-of-old only.
- X itself (the superseded predecessor) also re-appears. That predates packet 58 (supersede-of-old stamped `updated_at` before), so it is not new here.
- Design question for the ruling: should a dependency rewrite count as fleet activity, and should terminal or superseded dependents be re-anchored at all? They count toward the 16 665 hub cap and rewrite completed history.

### F4 (major, latent, HIGH): the THROW markers have TWO spellings, and editing "the ONE copy" breaks every losing claim
- Where:
  - `_txn.CLAIM_LOST_MARKER = "claim_lost:"` (commented "the ONE copy of the marker in this module") versus `tasks._CLAIM_LOST_PREFIX = "claim_lost:"`, which is what the claim THROW actually emits.
  - Likewise, `_txn._CAS_LOST_MARKER`, `_REANCHOR_STRAGGLER_MARKER` and `_HEAL_CHUNK_MARKER` are re-spelled literally in `tasks._SUPERSEDE_ALREADY_MESSAGE`, `_TRANSITION_ALREADY_MESSAGE`, `_REANCHOR_LOST_MESSAGE`, `_STRAGGLER_MESSAGE` and `_HEAL_CHUNK_MESSAGE`, and in `findings._TRANSITION_ALREADY_MESSAGE`.
- Receipt: `probe_blind_p5.py`, log `probe_blind_p5.log` (restore `RESTORED_BYTE_EXACT`):
  - healthy leg: `claim blocked D -> ClaimResult claimed=False`;
  - mutation leg (only `_txn.CLAIM_LOST_MARKER` edited): `RAISED TxnDomainRejectionError: … (unspecified rejection)`, logged at ERROR.
- Consequence: sharing fails by mutation. The classifier and the THROW sites agree only by convention (routing is not sharing). Closing rule: the THROW sites import the marker from `_txn`, or `_txn` exports a builder for the message.

### F5 (minor, HIGH): a create racing a supersede leaves a straggler until the next boot, and the claim render calls it permanent
- Where:
  - `create_task`'s superseded-blocker refusal (`_reject_unusable_blockers`) is a pre-read with no in-transaction guard. Every THROW in tasks.py is listed: none is on the create path.
  - The supersede's closing guard cannot see a create that commits after it.
- Receipt: `probe_blind_p4.py`, log `probe_blind_p4.log`:
  - `supersede reanchored=[]`
  - `D committed … names superseded X=True`
  - `claim D: claimed=False superseded_blockers={X: X2}`
  - control: `sequential create … REFUSED: UnknownBlockerError`
  - `after next boot heal: D blocked_by successor=True`
- False served text (server.py claim render, R10(iii) branch): "a SUPERSEDED blocker can never resolve, so this claim can never win: block on the successor instead". After packet 58 the boot heal re-anchors such a row, so "never" is false. The advice also invites a duplicate task. The stranded-until-next-boot bound is named nowhere a consumer reads.

### F6 (minor, HIGH, file reads): docstrings and comments that the diff made false
- `supersede_task`:
  - "Returns: The newly created successor task's opaque id." It now returns `SupersedeResult`.
  - Raises omits `HubSupersedeRefusedError` and `SupersedeStragglerError`.
- `direct_dependents` docstring:
  - "This is the read the supersede render's warning rides". It no longer is: server.py now renders `SupersedeResult`.
  - "dependency transfer itself is R10(iv) and is DEFERRED, because `blocked_by` is immutable after creation". Both are false now.
- `claim_task` comment: "Existence + the (immutable) dependency list. `blocked_by` never changes after creation". False. The same diff adds a `blocked_by = $clm_blocked_by` CAS conjunct precisely because it can change.
- `_refuse_a_cycle`:
  - Args: "pending: {the id about to be created: its deduped blocked_by}". The supersede now passes pre-existing rewired dependents.
  - "already RECORDED": see F1.
- `_render_supersede_result`: "a post-write `direct_dependents` read is `[]` by construction". F5 is a counterexample.

### F7 (minor, MEDIUM): code that exists for no production caller
- `TaskLedger._still_claimable` (new): 0 production references (grep over every production file, the scripts tree and the sibling members). `lore_impact` reports `0 prod / 0 test references, dead (heuristic)`, with the index current at `96ea7f5`. It re-implements the claim rule in Python (see R-3). Confidence is MEDIUM on "no test uses it", because I was withheld from the test tree.
- `_guarded_append_fragment`'s `namespace or f"ga{uuid4()…}"` default: every caller passes `namespace=` (claim `clmg`, transition `trg`, supersede `supg`, re-anchor `<prefix><i>g`), so the uuid branch is unreachable.

### F8 (minor, HIGH): the hub bound's re-open trigger cannot be attributed, and the bound is not named in the served surface
- `max_reanchor_dependents`' KNOWN BOUND names its trigger as "a `store.apply.large_transaction` record from the task ledger". But `SurrealStore._log_transaction_size` (surreal.py) logs on `loremaster.store.surreal`'s logger with only `statement_count`, `param_count` and `row_count` as extras. The index writer emits the same event from the same function, so a record cannot be told to come "from the task ledger". A trigger nobody can measure is a hope. A cheap fix: pass the caller identity or database.
- The 5 700–16 665-dependent band (a supersede times out instead of being refused) is recorded in a docstring that cites amendment sections. It names no lore finding number (CLAUDE.md, "WHEN YOU CANNOT CLOSE A HOLE, RECORD IT"), and it is not named in the served supersede surface (a served-surface hole must be named in the render, or closed).
- The served `HubSupersedeRefusedError` text ends "This is a pinned KNOWN BOUND (58 F-1); file it with lore_findings":
  - "pinned" is retired wording (operator, 2026-11-09);
  - "58 F-1" is an internal reference the consumer cannot resolve;
  - the instruction mints a duplicate finding on every refusal.
- Live recompute confirms the cap arithmetic: `max_reanchor_dependents(0)=16665`, priced at 50 000 rows, with 16 666 dependents priced at 50 003. The cost is 3 rows per dependent, and the WARN line sits at 3 331 dependents.

### F9 (minor, HIGH): the graded commit re-spells production to satisfy a source-shape check
- `aa4ea04` "re-green … the supersede DELETE fragment is an f-string (same text)": `"DELETE $ssx_old_rec->" + BLOCKS_RELATION` becomes `f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"`. The runtime bytes are identical.
- Ruff passes on the concatenated spelling: constructed in my copy, `ruff_concat.log` reads `All checks passed! EXIT=0`, and the restore is byte-exact.
- So whatever turned green distinguishes source spelling, not behaviour. The global §Tests rule says never re-spell to pass a scanner; fix the behaviour or report the scanner. I cannot name the test (withheld).

## 1b. Residuals (not defects I can show breaking anything; raised so they are not lost)
- R-1: The claim THROW interpolates `task_id` into a SurrealQL string literal (`THROW 'claim_lost:<id>'`). It is safe today only because `claim_task` first proves the row exists, and ledger-minted ids are hex. The tasks.py comment at `_SUPERSEDE_STAMPED_VAR` still says THROW messages are constants carrying no interpolated data (#31).
- R-2: `_dependent_rows` and `direct_dependents` run the same `blocked_by CONTAINS` read with two projections. The second could derive from the first.
- R-3: "is this task claimable" is now encoded four times: the claim CAS (SurrealQL), the `query_tasks` blocked partition, `_reblocked` (Python), and `_still_claimable` (dead). Drift between them would make the `reblocked` render lie.
- R-4: findings.py keeps its own guarded-CAS THROW statement. It is outside the "task-side" shell by its name, so this is a known second copy of the shell pattern, not a defect.
- R-5: The closing guard's `ssx_old` param is declared on the DELETE fragment and used only by the next fragment (which has `params={}`). This is cross-fragment coupling: reordering or dropping the DELETE fragment would leave `$ssx_old` unbound, and the guard would compare against NONE. I did not probe it.
- R-6: Each heal chunk-rejection WARNING carries every row id of the chunk (up to about 3 300 per 10 000-row chunk) in one record.

## 2. Removed-behaviour inventory (from code and docstrings only)
| # | removed / replaced | verdict |
|---|---|---|
| 1 | claim UPDATE that silently no-ops on zero rows | replaced by THROW + rollback (`TxnClaimLostError`, DEBUG). The verdict still comes from the post-CAS owner read, so it is preserved. It also passed P2/P5's healthy leg. |
| 2 | claim wrote no provenance event | new `claim` event (side effect added). No event consumer exists (grep over tasks.py, server.py). Deliberate. |
| 3 | claim CAS did not guard `blocked_by` | new `blocked_by = $clm_blocked_by` conjunct. Needed now that columns move. Deliberate. |
| 4 | transition / supersede-stamp / finding-transition rollbacks logged at ERROR, classified "unspecified rejection" | now `TxnCasLostError`, WARNING (am-7 tier table). Deliberate. Callers catch the `SurrealStoreError` superclass, so the IllegalTransitionError mapping is preserved. |
| 5 | supersede render's ⚠ STRANDED warning naming dependents to re-point | replaced by the re-anchored and reblocked lines. Deliberate. The stranding it named still occurs in F5's window, and the claim render still says "never" (F5). |
| 6 | supersede left dependents' columns and edges untouched (blocked_by immutable) | rewired in the same txn. Deliberate (#356), but see F3 for the `updated_at` side effect and F6 for the prose. |
| 7 | `query_tasks` listed superseded rows under every filter | dropped under `status` and `blocked` (F2): spec-silent, so it needs an operator or lead ruling. |
| 8 | `_run_verified_transaction` raised `RetryableConflictSignal` bare and passed no `label`/`url` | now chained from `_TransactionConflictCause` with `label` and `url`, so the exhaustion record gains the engine text. Deliberate (am-13 F-8). The docstring was updated consistently. |
| 9 | `_domain_rejection_error` if-chain | replaced by a dict lookup with the same default. Preserved. |
| 10 | heal: none existed | new behaviour. Input fates: healed, chunk-rejected+WARNING, phantom/cycle-head skip+WARNING, or a store fault RAISES. No silent drop found. The corrupting fate is F1. |

## 3. Reuse table (new symbols; what already does this job)
SupersedeResult · SupersedeStragglerError · StragglerHealPackerError · HubSupersedeRefusedError: new types; nothing prior (lore_search found no equivalent).
TxnClaimLostError · TxnCasLostError · TxnReanchorStragglerError · TxnHealChunkError · _TransactionConflictCause · _THROWN_DOMAIN_MARKERS · _TYPED_DOMAIN_REJECTIONS · _ROLLBACK_LOG_TIERS · _TXN_ROLLBACK_LABEL: they EXTEND the existing classifier and typed-rejection family. This is correct reuse, apart from F4's duplicated markers.
_guarded_append_fragment: it absorbs three prior task-side clones (transition, supersede stamp, claim). findings.py's clone remains (R-4).
_reanchor_fragments · _supersede_transaction · _supersede_rows · max_reanchor_dependents: they route through `_txn.fragment_rows` (THE row count). Correct.
_dependent_rows: duplicates the `direct_dependents` predicate (R-2).
_reblocked · _still_claimable: a re-encoding of the claim rule (R-3); `_still_claimable` is dead (F7).
_reanchor_stragglers · _plan_heal_rows · _pack_heal_chunks: they use `more_itertools.constrained_batches` and `resolve_existing_rows`. Correct. Missing: the shared `_refuse_a_cycle` (F1).
SurrealStore._log_transaction_size reused from the ledger: correct, but it is private cross-class access, and the record is unattributable (F8).

## 4. Probe instruments and logs
- The instruments live in the lead-named area under my scratch notes dir `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58/blind-notes/`:
  - instruments: `probe_blind.py` (P1, P2), `probe_blind_p3.py`, `probe_blind_p4.py`, `probe_blind_p5.py`;
  - logs: `probe_blind.log`, `probe_blind_p2.log`, `probe_blind_p3.log`, `probe_blind_p4.log`, `probe_blind_p5.log`, `ruff_concat.log`.
- ⚠ That dir is scratch (brief-base §1: instruments are deliverables). The lead should `cp` them into this receipts folder at archive time. I may write only this file.
- Every probe ran from `/var/tmp/.../scratchpad/ca58/ca58-blind` with `loremaster.__file__ = …/ca58-blind/loremaster/loremaster/__init__.py`. `tree_id`: `HEAD=96ea7f5… DIRTY_FILES=5 TREE=40f080f6b8185396394d862637256df9e17d67bbfaeff5bde0f030aae1580f24`.
- Store: ws://127.0.0.1:18000, namespace `lore_test`, one `test_ca58blind_<uuid>` database per probe, removed in `finally`. Each run was capped at `MemoryMax=16G`.
- No pytest was run (this dimension withholds test runs), and nothing was committed.
