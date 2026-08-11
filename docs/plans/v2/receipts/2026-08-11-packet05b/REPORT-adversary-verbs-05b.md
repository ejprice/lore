brief-base v11 read
brief project v7 read

# REPORT-adversary-verbs-05b — CONTRACT ADVERSARY for #174 (supersede blocked_by) + #262 (register liveness notice)

---
## ⭐ ROUND 2 — DELTA RE-GRADE (revised contract, 26 tests) — VERDICT: CONTRACT SUFFICIENT
The lead revised the contract to close BOTH round-1 findings. I re-graded against the revised
`test_blocks_edge.py` + `test_comms_register_notice.py` in scratch (same provenance-asserted tree).
**All five delta tasks pass; the revision holds.** One cosmetic residual, non-blocking.

| delta task | probe | result |
|---|---|---|
| 1. self-ref BLOCKER now pinned | re-ran my round-1 ACCEPT build against the new explicit + inherited pins | **both REDDEN** — `DID NOT RAISE TaskLedgerError` (§D-new) |
| 2. explicit vs inherited discriminate | built a guard that refuses the EXPLICIT override but not the resolved/inherited set | `test_supersede_REFUSES_an_INHERITED_self_block` **REDDENS**, explicit passes (§D-W1) — the inherited pin forces the guard over RESOLVED deps |
| 3. predicate-share MINOR now pinned | re-ran my round-1 fleet-inline build against `test_both_surfaces_share_the_EXTRACTED_predicate` | **REDDENS** — patching `_heartbeat_is_stale` flips the notice but not the inline fleet → `assert "STALE" not in fleet_line` fails (§D-new) |
| 4. NEW holes — attack the new pins | built a "fix-it-wrong" that SILENTLY DROPS the self-ref (avoids the bug, but not loudly) | **both self-ref pins REDDEN** — they require LOUD refuse-and-teach, not silent correction (§D-W2). Predicate pin is airtight (both surfaces must route through the ONE patched helper — no divergence survivable). |
| 5. satisfiability | corrected reference (self-ref guard over resolved deps + fleet routed through `_heartbeat_is_stale`) | **26 passed**; no-regression **252 passed** (`test_comms_footer` fleet/AST/footer + `TestConcurrentSupersession`) |

- **Round-1 BLOCKER (self-ref) — CLOSED.** Pinned BOTH ways (explicit override + raw-seeded inherited self-loop), each asserting refuse + nothing-minted + row-count-unchanged (atomicity leg is real — the silent-drop build reddens it). The pins are mechanism-agnostic (assert `TaskLedgerError` + a teaching message, not a specific subclass) — correctly pins behavior, not implementation.
- **Round-1 MINOR (predicate-share) — CLOSED.** `test_both_surfaces_share_the_EXTRACTED_predicate` mutates `_heartbeat_is_stale` LOGIC (not just the constant) and forces BOTH surfaces through it. This is exactly the pin I recommended.
- **RESIDUAL (cosmetic, non-blocking):** the inherited pin (`test_supersede_REFUSES_an_INHERITED_self_block`) asserts only `original in str(caught.value)`, where the explicit pin also asserts `"supersede" in message.lower()`. A natural single-guard build (`if task_id in dependencies`) produces the same teaching message on both paths, so this is covered in practice; only a contrived two-guard build with a bare inherited message would slip. Recommend adding the `"supersede" in message` assertion to the inherited pin for parity. Construction-inspection (assertion-text diff), not a wrong-build door.
- All round-1 wrong-build receipts (W1–W10) still apply — those pins are unchanged in the revision (23 original + 3 new = 26).

**SUFFICIENT. Releases the builder.** (Round-1 detail below is retained for provenance; its INSUFFICIENT verdict is SUPERSEDED by this section.)

---

## SUMMARY BLOCK
- receipt: `brief-base v11 read` · `brief project v7 read`
- role: CONTRACT ADVERSARY (Opus-4.8, `opus48-worker`/`contract-adversary` frontmatter — attest; REFUTE posture). Read-only: NO repo code/tests edited. All wrong builds live in scratch `/home/ejprice/scratch-adv-verbs-05b` (provenance-asserted, `loremaster.__file__` under scratch root — receipt §PROVENANCE).
- **VERDICT: CONTRACT INSUFFICIENT** — one BLOCKER missing pin (a wrong build that fixes-it-wrong survives), one MINOR missing pin, plus residuals.
- **P1 headline:** a WRONG build survived — actually the CORRECT reference build itself waves through `supersede(X, blocked_by=[X])`: the successor is minted `blocked_by=[X]` while X is stamped superseded in the same txn → **`claim(successor).claimed == False` — UNCLAIMABLE FOREVER** (the #174/#130 shape #174 exists to abolish, through the ONE door neither pre-check guards). Empirical receipt §W5. The author flagged this as residual R1; it is a real defect, not a hypothetical → MISSING PIN.
- **MISSING PIN 1 (BLOCKER, #174):** `test_supersede_self_referential_override_is_refused` — `supersede(X, blocked_by=[X])` must REFUSE (mint nothing, X un-stamped). Catches the unclaimable-forever successor. Reachable via the served `lore_tasks supersede` tool (Consumer Law).
- **MISSING PIN 2 (MINOR, #262):** the ONE-IMPL threshold pin proves the shared CONSTANT, not the shared PREDICATE. A notice that reads `config.stale_heartbeat_s` but uses a private `>=` (vs fleet `>`) SURVIVES `test_both_surfaces_flip_at_one_threshold` (§W6). Recommend a pin that mutates the shared PREDICATE (`AppContext._heartbeat_is_stale`) and asserts BOTH surfaces flip — forcing both to route through the one function.
- **Satisfiability:** #174 contract → **9 passed**; #262 contract → **14 passed**; against a provenance-asserted reference build. Builder-obligation #1 (`FakeTaskLedger` lockstep) is REAL and DISCHARGEABLE (16 passed after the fake accepts `blocked_by`) — and auto-enforced by MORE than the author named: `test_comms_footer.py` reddens 3 supersede pins too, not just `test_mcp_server::TestTasksTool` (§SAT).
- **RED honesty:** reproduced independently — #174 **8 failed / 1 passed** (the 1 = the vacuous ONE-IMPL discriminator), #262 **8 failed / 6 passed** (the 6 = the disclosed no-notice regression guards, positive controls are the RED notice pins). Total **16f/7p**, matching the author's claim exactly (§RED).
- **Every other attack is genuinely pinned:** W1 always-inherit, W2 no-surface-render, W3 validate-override-only, W4 private-clone (caught by BOTH the AST + the mutation guard), W7 get_agent, W8 self-held-emits, W9 false-active, W10 refuse — all reddened. Receipts §PROBE RECORD.
- Packages considered: **none** — both contracts reuse in-repo policy (reject_unknown_rows→graphlib, get_task, resolve_holder over `_select_rows_by_name`, extracted STALE predicate). Independent P-PKG enumeration found no library opportunity (most-recent-heartbeat = `max(key=…)`, STALE = `age>threshold` — trivia, not mechanisms). Author's `none` verdict confirmed.
- Graded: contract @HEAD `c0071cd` · HEAD-at-report `c0071cd` · **SAME**.
- decisions-needed: (1) ratify MISSING PIN 1 (self-ref → refuse, consistent with the two existing refuse-and-teach doors) — thin design call, trust-consistent default is clear; (2) MISSING PIN 2 severity (minor; primary risk already caught).
- receipt pointers: quantifier table §P1b; reach table §P1c; wrong builds §PROBE RECORD (W1–W10); satisfiability §SAT; RED §RED; the fatal finding §W5.

---

## PROVENANCE (#140)
`scripts/scratch_copy.sh /home/ejprice/scratch-adv-verbs-05b` — provenance-asserted; every probe ran with
`loremaster.__file__ = /home/ejprice/scratch-adv-verbs-05b/loremaster/loremaster/__init__.py` (printed in the
first probe, §W5). Reference build = the author's §REFERENCE BUILD edits, re-derived independently (tasks.py
`supersede_task`, server.py supersede dispatch + `_render_supersede_result` + `_holder_liveness_notice` +
`_heartbeat_is_stale`, agents.py `resolve_holder`). Backups `*.ref` let each wrong build mutate + run + restore.
Scratch is DISPOSABLE by design; the exact edits are captured in this report's fences.

---

## P1b — QUANTIFIER TABLE (every invariant: ∀-over-inputs vs guarded-by-failure-mode)

### #174 — "supersede never mints a dependency-inconsistent / unclaimable successor; the successor's `blocked_by` is the sentinel-disciplined resolution, mirrored to the edge"
| invariant | classification | receipt |
|---|---|---|
| sentinel resolution INHERIT/CLEAR/REPLACE | **∀ over {None, [], [ids]}** | W1 (always-inherit) reddens CLEAR **and** REPLACE — §W1 |
| resolved `blocked_by` mirrored to `blocks` edge | ∀ (column == edge, both directions) | flipped corpse + CLEAR/REPLACE assert edge set — GREEN on ref |
| shared blocker/cycle policy reuse (ONE-IMPL) | ∀, proven by AST + mutation | W4 private-clone reddens BOTH guards — §W4 |
| result NAMES the successor's resolved `blocked_by` | ∀ (served surface, real ledger) | W2 no-surface reddens; render genuinely lacks the id — §W2 |
| **"no unclaimable successor from a bad blocker"** | **GUARDED — 2 of 3 doors** | inherited-superseded (W3 ✓) + phantom-override (✓); **self-reference door UNGUARDED (W5 ✗)** |
| exactly-one-successor + zero orphan edges under race | ∀ (2-way × 12, matches existing pattern) | TestConcurrentSupersession GREEN on ref — §SAT |

The one **guarded** row is the finding. "A supersede must never mint a successor that can never be claimed" is
pinned for the two doors the author enumerated (an inherited blocker that was since superseded; an override
naming a phantom) and OPEN on the third (an override naming the task **being superseded**). Same bad outcome,
different cause, no engaged pin — the PR93 quantifier shape verbatim.

### #262 — "register discloses the holder's ACCURATE liveness; never a false clear; never refuses"
| invariant | classification | receipt |
|---|---|---|
| disclose iff holder ≠ registering agent (self/other/unheld) | **∀ over the triple** | W8 self-held-emits reddens — §W8 |
| liveness render set {live, STALE, retired, unresolvable, no-such-task, ambiguous} | **∀ over fates, each fixture-forced** | W7 (get_agent) reddens retired+ambiguous; W9 (false-active) reddens unresolvable — §W7/§W9 |
| never refuse / never raise, in every holder state | ∀ | W10 refuse-build reddens — §W10 |
| STALE threshold shared with fleet | **GUARDED at the CONSTANT level only** | W6b hardcode reddens (✓) but W6 config-reading `>=` clone SURVIVES (✗) — §W6 |

The one **guarded** row is MINOR: mutating the config VALUE catches a hardcoded clone but not a private predicate
that reads config and diverges only in the comparison (`>=` vs `>`), which is invisible except at the exact
boundary `age == threshold`.

---

## P1c — REACH TABLE (every guard/scan the contract introduces or relies on)

| instrument | reach DERIVED vs hand-list | coverage a checked var? | effect vs proxy | ONE-source proven by MUTATION? | leg | verdict |
|---|---|---|---|---|---|---|
| `test_supersede_source_calls_BOTH_shared_blocks_edge_prechecks` (AST) | scans `TaskLedger.supersede_task`'s own source (single function, keyed on 3 method NAMES) | n/a (structural) | observes CALLS present (a proxy for "runs the shared policy") — braced by the behavioral mutation pin below | the 3 names resolve to the SAME-class methods `create_task` calls (no same-name private clone possible on one class) | empirical (W4) | **SAFE** — name-key is sound here because they're methods on ONE class; behavioral pin covers "called correctly" |
| `test_supersede_ROUTES_THROUGH_the_SHARED_blocker_check` (mutation of `reject_unknown_rows`) | the module symbol `loremaster.tasks.reject_unknown_rows` | yes — neutralise → supersede MUST mint | **effect** (mint actually happens) | yes — a private clone keeps refusing → reddens | empirical (W4) | **SAFE** |
| `test_both_surfaces_flip_at_one_threshold` (mutation of `config.comms.stale_heartbeat_s`) | the two render surfaces (fleet row + register notice) | partially — catches a hardcoded constant, NOT a private config-reading predicate | effect (rendered "STALE" token) | **CONSTANT proven; PREDICATE FUNCTION not** | empirical (W6/W6b) | **MISSING PIN 2** — routing-is-not-sharing at the predicate level |

Legs run: all three EMPIRICAL (guards are in-tree; I built the wrong versions and observed). The P1c question-5
("mutate the ONE shared thing → does every caller redden?") is where MISSING PIN 2 lives: the ONE shared thing the
contract mutates is the CONSTANT, not the predicate FUNCTION, so a caller that hand-rolls the DECISION while reading
the same constant is a private copy wearing the shared name — #102/#120's exact shape, one level below the value.

---

## MISSING PINS (the tests the author should add)

### MISSING PIN 1 — BLOCKER (#174): the self-referential override
- **The test that should exist:** `TestSupersedeCarriesBlockedBy174::test_a_self_referential_override_is_REFUSED_and_nothing_is_minted` — `supersede(X, blocked_by=[X])` raises `TaskLedgerError`, `get_task(X).superseded_by is None`, row-count unchanged.
- **The defect it catches:** the successor is minted `blocked_by=[X]`; X is stamped `superseded` (status non-terminal) in the SAME txn; `_is_blocked(successor)` is `True` forever → **unclaimable-forever successor**, the exact #174/#130 harm this whole packet exists to abolish, reached through the one door neither `_reject_unusable_blockers` (X is not-yet-superseded at pre-check time) nor `_refuse_a_cycle` (a fresh successor has no incoming edge, so no column cycle closes) can see.
- **Reachable via the served surface:** `lore_tasks(action="supersede", task_id=X, blocked_by=[X], …)` — an honest agent mistake ("supersede X, keep depending on X"). Consumer Law: the consumer is an agent, and the served tool threads it straight through.
- **Recommended behavior = REFUSE**, consistent with the two existing refuse-and-teach doors (inherited-superseded, phantom) — all three are "a resolved blocker that can never resolve." Thin design call; the trust-consistent default is unambiguous. Reference-build guard is one line: reject an override (or inherited set) containing `task_id` before the write.

### MISSING PIN 2 — MINOR (#262): predicate-sharing, not just constant-sharing
- **The test that should exist:** monkeypatch `AppContext._heartbeat_is_stale` (invert it) and assert BOTH a fleet row AND the register notice change their STALE verdict together. (Requires the builder to also route `_render_comms_fleet_row` through `_heartbeat_is_stale` — a builder obligation the current contract does not force.)
- **The defect it catches:** a notice with a private predicate (reads `config.stale_heartbeat_s` but uses `>=` where the fleet uses `>`, or later grows a grace period the fleet doesn't) — two surfaces disagreeing about one holder's liveness at the boundary, which is precisely the "two surfaces disagreeing, only one saying so" class #262 exists to close. SURVIVES the current pin (§W6).
- **Honest bound:** the current pin MATCHES the design's own stated proof ("perturb `stale_heartbeat_s` → both move", A-262), so this is as much a design-spec gap as a contract gap, and the PRIMARY risk (a hardcoded 600 in the notice) IS caught (§W6b). Low severity; recommend for completeness given #102/#120 history.

---

## RESIDUALS (individual verdicts)
- **R-a (#262, minor looseness):** `test_no_such_task_discloses_and_still_registers` asserts `"not found" in text` and `test_unheld_task_emits_NO_notice` asserts `"not found" not in text` on the FULL render, not scoped to `_notice_line()`. Both are RED-at-HEAD and discriminating (HEAD never renders "not found"), so not a hole today — but they'd pass a build that renders the no-such-task disclosure as a NON-`note:` bare line, unlike the held-by pins which require the `note:` prefix. Recommend scoping the no-such-task assertion to `_notice_line()` for consistency. **VERDICT: cosmetic, not a wrong-build door.**
- **R-b (#262, design-inherent):** self-held is decided by `owner == agent` (bare-name compare). `owner` is a bare string (claim_task takes a bare owner), so a same-named holder in another session reads as "self" and suppresses the notice. This is the design's accepted best-effort-by-name (fork 3) — not a contract gap. **VERDICT: known design bound; note only.**
- **R-c (#174, concurrency degree):** the new atomicity pin is 2-way × 12; store-law §5's ≥8-way is for hot-row NUMBER mints (retry/jitter). Supersede mints a uuid4 successor and CASes the old row — the existing `TestConcurrentSupersession` is ALSO 2-way, and the orphan-edge property is detectable with a single loser. **VERDICT: consistent with the established pattern; not a finding.**
- **R-d (builder obligation, confirmed non-skippable):** `FakeTaskLedger.supersede_task` lockstep reddens `test_comms_footer.py` (3 pins) in addition to the `test_mcp_server::TestTasksTool` pins the author named. Dischargeable (§SAT). **VERDICT: the RED contract correctly leaves it out; auto-enforcement is BROADER than claimed — a positive.**
- **R-e (author R2):** task ids `adefe9a4…`/`087d321c…` — not adversary-relevant; lead's workstream bookkeeping. **VERDICT: noted, non-blocking.**

---

## PROBE RECORD (commands + real output)

Every wrong build: mutate a `.ref`-backed reference file in scratch, run the targeted pin(s), restore. Pipe-lie
guard: counts read from the pytest tail, never an exit code through a pipe.

### W5 — BLOCKER: self-referential override mints an unclaimable successor (against the CORRECT reference build)
Probe `loremaster/tests/test_adv_selfref_probe.py`, run with `-s`:
```
PROBE: supersede(X, blocked_by=[X]) SUCCEEDED — minted 5449a92cff3e46699ed328a537d96590
PROBE: successor.blocked_by = ['620a059897ba498cbf6f08cab8e22109']
PROBE: X.superseded_by = 5449a92cff3e46699ed328a537d96590 ; X.status = open
PROBE: claim(successor).claimed = False
1 passed in 0.30s
```
The successor depends on X; X is superseded and non-terminal; the claim CAS can never resolve it. No contract pin
fires. `_reject_unusable_blockers([(X,X)])` passes (X not-yet-superseded at pre-check); `_refuse_a_cycle({new:[X]})`
passes (fresh `new` has no incoming edge). Confirmed by construction + execution.

### W1 — always-INHERIT (ignores the sentinel) → CLEAR + REPLACE reddened ✓
Mutation: `dependencies = list(dict.fromkeys(row.get(_COL_BLOCKED_BY) or ()))` unconditionally.
```
FAILED …::test_CLEAR_with_an_explicit_empty_list_drops_dependencies
FAILED …::test_REPLACE_with_a_new_blocker_list_is_not_a_merge
2 failed in 0.79s
```

### W2 — threads deps to ledger but does NOT surface them → served-surface pin reddened ✓
Mutation: `blocked_clause = ""` always (drop the render).
```
E   assert 'fbf9e42b05da4433bf9e92694d70c3d9' in 'superseded task ```a3ac…```; successor ```de2d…``` (status open)'
FAILED …::test_tool_seam_supersede_threads_blocked_by_and_SURFACES_it
1 failed in 1.02s
```
The rendered bytes genuinely lack the id — the pin is discriminating, not satisfied via another path.

### W3 — validate ONLY explicit overrides (trust inherited deps) → inherited-superseded pin reddened ✓
Mutation: `if blocked_by is not None:` wrap around both pre-checks.
```
E   Failed: DID NOT RAISE <class 'loremaster.tasks.TaskLedgerError'>
FAILED …::test_an_INHERITED_SUPERSEDED_blocker_is_REFUSED_and_nothing_is_minted
1 failed in 0.54s
```

### W4 — private-clone blocker check (routing-is-not-sharing) → BOTH guards reddened ✓
Mutation: hand-rolled per-dep `_select_row` existence/superseded check instead of `_reject_unusable_blockers`.
```
FAILED …::test_supersede_ROUTES_THROUGH_the_SHARED_blocker_check
FAILED …::test_supersede_source_calls_BOTH_shared_blocks_edge_prechecks
2 failed in 0.63s
```
AST guard: `'_reject_unusable_blockers' in {…}` fails (clone removed the call). Mutation guard: neutralising
`reject_unknown_rows` no longer disarms the refusal (the clone doesn't use it) → `assert successor` fails.

### W6 — private STALE predicate reading config, `>=` vs fleet `>` → ONE-IMPL pin SURVIVES ✗ (MISSING PIN 2)
Mutation: `if age_s >= self.config.comms.stale_heartbeat_s:` inline (not the shared `_heartbeat_is_stale`).
```
1 passed in 1.08s
```
### W6b — crude clone (hardcoded `age_s > 600`) → ONE-IMPL pin reddened ✓
```
E   'STALE' is contained here: …⚠ STALE, last seen 21m ago) — registering the association anyway.
FAILED …::test_both_surfaces_flip_at_one_threshold
1 failed in 1.12s
```
W6 vs W6b on the SAME test is the P0 control: the pin fires on the hardcode and misses the config-reading
predicate-divergence — so it discriminates "reads config" but not "shares one predicate function".

### W7 — wiring `get_agent` (excludes retired, raises on ambiguity) → retired + ambiguous reddened ✓
Mutation: `holder = await self.agent_registry.get_agent(owner)` in a `try/except _AgentRegistryError: holder=None`.
```
E   assert 'active' in 'note: task ```…``` is held by ```dupe-y``` (```claimed```; not found in registry) — …'
FAILED …::test_retired_holder_renders_retired
FAILED …::test_ambiguous_holder_picks_most_recent_heartbeat
2 failed, 1 passed in 1.72s
```
(The unresolvable pin coincidentally passes — `get_agent`'s UnknownAgentError → None → "not found in registry" is
correct for the ghost case.) Confirms the F1 ruling (wire `resolve_holder`, not `get_agent`) is genuinely pinned.

### W8 — self-held EMITS a notice (drops the discriminator) → reddened ✓
Mutation: `if owner is None:` (removed `or owner == agent`).
```
E   'is held by' is contained here: …a166… is held by ```reg-agent``` (```claimed```; active) — …
FAILED …::test_self_held_emits_NO_notice
1 failed in 1.16s
```

### W9 — false "active" on an unresolvable holder (the fatal false clear) → Forgery pin reddened ✓
Mutation: `if holder is None: liveness = safe_str("active")`.
```
E   assert 'not found in registry' in 'note: task ```…``` is held by ```ghost-owner``` (```claimed```; active) — …'
FAILED …::test_unresolvable_holder_never_says_active
1 failed in 1.18s
```
The `_notice_line()` scoping holds: the false "active" is caught inside the note line (the register HEAD's own
"status active" on the head line does not satisfy this pin).

### W10 — REFUSES on an other-held task (Reading 2) → never-refuses pins reddened ✓
Mutation: `raise ValueError(...)` when `owner not in (None, agent)`.
```
E   ValueError: task d9ae5eb5… is already held by ghost-owner
FAILED …::TestRegisterNeverRefuses::test_registration_succeeds_regardless[holder-y]
FAILED …::TestRegisterNeverRefuses::test_registration_succeeds_regardless[ghost-owner]
2 failed, 1 passed in 2.11s
```

---

## SAT — SATISFIABILITY + no-regression (positive controls)
- #174 contract (reference build): **9 passed** (`TestSupersedeCarriesBlockedBy174` ×8 + the flipped corpse).
- #262 contract (reference build): **14 passed** (full `test_comms_register_notice.py`).
- `TestConcurrentSupersession` (my added RELATE preserves exactly-one-successor atomicity): **passed** (within the noreg run).
- `test_comms_footer.py` against the reference WITHOUT the fake update: **249 passed, 3 failed** — all 3 `FakeTaskLedger.supersede_task() got an unexpected keyword argument 'blocked_by'`. After giving the fake the sentinel-disciplined `blocked_by` param: the 3 (and their siblings) go **16 passed**. Confirms builder-obligation #1 is real, dischargeable, and auto-enforced by test_comms_footer too.

## RED — RED-at-HEAD honesty (independently reproduced)
- #174 selection at HEAD (pristine scratch, no reference edits): **8 failed, 1 passed** — the 1 pass is `test_supersede_ROUTES_THROUGH_the_SHARED_blocker_check`, vacuously green at HEAD (nothing to neutralise). Flipped-corpse RED reason confirmed empirically: `assert [] == ['eb91…']`. The `blocked_by=`-passing pins RED via `TypeError` (param absent at HEAD — a code fact: HEAD's `supersede_task` sig has no `blocked_by`); INHERITED-SUPERSEDED via "DID NOT RAISE"; AST via "calls none"; concurrent + tool_seam via edge/column assertion.
- #262 with the notice neutered to HEAD behavior (`return None`): **8 failed, 6 passed** — the 8 RED are exactly the notice-present pins; the 6 GREEN are the disclosed no-notice regression guards (self-held, unheld, no-task-id, never-refuses ×2, bogus-id), whose positive controls are the RED pins. No notice-present pin passes for a fixture reason.
- Combined **16 failed / 7 passed**, matching the author's claim exactly.

## P-PKG — package survey diff
Independent enumeration BEFORE reading the author's: #174 mechanisms = row-existence policy (already `reject_unknown_rows`), acyclicity (already `graphlib.TopologicalSorter` via `find_blocked_by_cycle`), edge mirror (`_relate_fragment`) — all in-repo reuse, no library gap. #262 mechanisms = single-row task fetch (`get_task`), owner→registry best-effort resolve (`max(rows, key=heartbeat)` over `_select_rows_by_name` — stdlib `max`, no library), STALE derivation (`age > threshold` — trivia). No `bespoke` verdict hides a library. DIFF vs author's `Packages considered: none`: **identical**. No finding.

## CONTRACT SUFFICIENT / INSUFFICIENT (ROUND 1 — SUPERSEDED by the ROUND 2 delta at the top)
**[ROUND 1] CONTRACT INSUFFICIENT** — MISSING PIN 1 (self-referential override → unclaimable-forever successor, a wrong-outcome the CORRECT reference build produces and the served tool exposes) is a concrete pin the author can write, with an empirical reproduction (§W5). MISSING PIN 2 (predicate-sharing) and the residuals accompany it. Every other #174/#262 attack in the brief is genuinely pinned, with wrong-build receipts showing each guard fire.
**Both round-1 pins were added in the revision → ROUND 2 verdict CONTRACT SUFFICIENT (see the top of this report).**

---

## ROUND 2 PROBE RECORD (delta re-grade — revised 26-test contract, corrected reference `.ref2`)

### D-new — the three new pins REDDEN my round-1 wrong builds (they close the round-1 findings)
Ran the 2 new self-ref pins + the new predicate pin against my round-1 reference (accepts self-ref; fleet-inline):
```
FAILED …::test_supersede_REFUSES_a_successor_blocked_by_the_task_it_SUPERSEDES   (DID NOT RAISE TaskLedgerError)
FAILED …::test_supersede_REFUSES_an_INHERITED_self_block                         (DID NOT RAISE TaskLedgerError)
FAILED …::test_both_surfaces_share_the_EXTRACTED_predicate  (assert 'STALE' not in '- holder-y …' — fleet inline ignores the patch)
3 failed in 1.85s
```

### D-W1 — explicit-only guard → the INHERITED pin discriminates ✓
Mutation: `if blocked_by is not None and task_id in blocked_by:` (guard only the explicit override).
```
FAILED …::test_supersede_REFUSES_an_INHERITED_self_block
1 failed, 1 passed in 0.74s
```
The inherited pin forces the guard over the RESOLVED (post-inherit) deps, not just the explicit arg.

### D-W2 — "fix-it-wrong" silent-drop → both self-ref pins REDDEN ✓
Mutation: `dependencies = [dep for dep in dependencies if dep != task_id]` (avoid the bug silently, no refusal).
```
E   Failed: DID NOT RAISE <class 'loremaster.tasks.TaskLedgerError'>   (×2)
FAILED …::test_supersede_REFUSES_a_successor_blocked_by_the_task_it_SUPERSEDES
FAILED …::test_supersede_REFUSES_an_INHERITED_self_block
2 failed in 0.76s
```
The pins require a LOUD refuse-and-teach; a silent correction (which does fix the unclaimable bug) is rejected — the Consumer-Law-correct behavior.

### Satisfiability + no-regression (corrected reference)
Corrected reference = round-1 reference + `if task_id in dependencies: raise TaskLedgerError(…naming id + "supersede"…)` over the RESOLVED deps + `_render_comms_fleet_row` routed through `AppContext._heartbeat_is_stale`.
```
26 passed in 7.78s     # full revised contract (both files)
252 passed in 7.05s    # test_comms_footer.py (fleet render + AST template pins + footer) + TestConcurrentSupersession
```

### ROUND 2 residual (cosmetic, non-blocking)
`test_supersede_REFUSES_an_INHERITED_self_block` asserts `original in str(caught.value)` but NOT `"supersede" in message.lower()` (the explicit pin asserts both). A single-guard build teaches identically on both paths, so this is covered in practice; recommend adding the teaching assertion to the inherited pin for parity. Assertion-text diff (construction-inspection), not a wrong-build door.

### ROUND 2 VERDICT: **CONTRACT SUFFICIENT** — releases the builder.
