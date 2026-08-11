brief-base v11 read
brief project v7 read

# REPORT-contract-verbs-05b — CONTRACT for #174 (supersede blocked_by) + #262 (register liveness notice)

## SUMMARY BLOCK
- receipt: `brief-base v11 read` · `brief project v7 read`
- state: **done (revised after adversary round 1)** — both RED contracts written, RED-at-HEAD confirmed, satisfiability proven 0-failed against a scratch reference build (provenance-asserted). Adversary round 1 (`REPORT-adversary-verbs-05b.md`): 1 blocker (self-ref R1) + 1 minor (STALE predicate-vs-constant) — BOTH addressed here; all other W1–W10 attacks were genuinely pinned.
- role: CONTRACT author (Opus-4.8, `opus48-worker` frontmatter-pinned — attest). RED tests ONLY; NO production code touched in the repo tree. A throwaway reference build lives in a scratch copy (below).
- deviations:
  - **D1:** #174 served-surface pins placed in `test_blocks_edge.py` via its real-ledger `_tool_seam` (not `test_mcp_server.py`'s `FakeTaskLedger` harness) — avoids a fake-lockstep coupling AND is more honest (real store). F2's intent (the served surface IS pinned) is met; only the file differs. Disclosed per scope law.
  - **D2 (builder obligations my RED contract deliberately does NOT ship, because they can only exist AFTER the signature change — each is auto-enforced by an existing invariant, see §BUILDER OBLIGATIONS):** the `FakeTaskLedger.supersede_task(blocked_by=…)` lockstep + the `_render_supersede_result` containment-probe shape in `test_link5_render_containment.py`.
- Packages considered: **none — no third-party mechanism specified.** #174 reuses in-repo policy seams (`_reject_unusable_blockers`/`_refuse_a_cycle`/`_new_task_content`/`_relate_fragment`; `find_blocked_by_cycle` already `replace`s onto stdlib `graphlib`). #262 reuses in-repo `get_task` + a new `AgentRegistry.resolve_holder` over the existing `_select_rows_by_name` + the extracted STALE predicate. All INTERNAL/DRY.
- Graded: n/a (a contract, not a verdict on another artifact). All symbol/location claims verified @HEAD `c0071cd` via `lore_get_symbol`/`lore_read`/direct read + a live reference build.
- decisions-needed (LEAD/operator — the design forks were already ruled):
  - **R1 (was a residual, now RESOLVED as a pin):** the self-reference `supersede(X, blocked_by=[X])` — the adversary confirmed it reproduces on my correct reference build (unclaimable-forever successor, reachable via the served tool). NOW PINNED: supersede REFUSES-AND-TEACHES a `blocked_by` containing the superseded task's own id, on BOTH the explicit-override and inherited paths; the reference build implements the refusal (`TaskCycleError`, "a successor cannot be blocked by the task it supersedes"). In-scope for #174 (successor-`blocked_by` validation), NOT #356's dependent-rewire.
  - **R2 (minor): task ids `adefe9a4…`/`087d321c…`** (brief) do not resolve via `lore_tasks get` — lead tracks workstream state, so non-blocking; noting.
- receipt pointers: RED tail §RECEIPTS; reference-build edits §REFERENCE BUILD; forks §FORKS; #174 pins §#174; #262 pins §#262.

---

## RECEIPTS (measured 2026-08-11 @HEAD `c0071cd`; revised after adversary round 1)
- **RED at HEAD (real tree):** the 3 contract selections → **19 failed, 7 passed** of 26. The 7 passing are DISCRIMINATING GUARDS, not gaps: 6 #262 no-notice / never-refuse regression guards (HEAD emits no notice, so "no notice" is vacuously true — their positive controls are the RED notice-present pins) + 1 #174 ONE-IMPL mutation guard (`test_supersede_ROUTES_THROUGH_the_SHARED_blocker_check` — vacuously green at HEAD because HEAD has no refusal to neutralise; it discriminates the private-clone WRONG-BUILD, not HEAD).
- **Satisfiability (scratch reference build — `loremaster.__file__ = /home/ejprice/scratch-verbs-05b/loremaster/loremaster/__init__.py`, provenance-asserted by `scripts/scratch_copy.sh`):**
  - contract: `test_comms_register_notice.py` (15) + `TestSupersedeCarriesBlockedBy174` (10) + the flipped corpse → **26 passed**.
  - #174 no-regression: `TestSupersession` + `TestConcurrentSupersession` + `TestTasksTool` + `TestTheMirrorHoldsAtEveryWritePath` + the new class → **39 passed**.
  - #262 no-regression: `test_comms_tool` + `test_comms_status_age` + `test_comms_footer` + `test_agent_registry` + `test_comms_render_architecture` → **1359 passed** (incl. `test_comms_footer`'s Ruling-5.3 registry-reads pin — the F1 reconciliation holds).
  - containment: `test_link5_render_containment.py` → **158 passed** (after adding the `_render_supersede_result` non-empty-blocked_by forgery probe shape, §BUILDER OBLIGATIONS).
- **Gates (ZERO-NEW vs #333):** `ruff check` on both new/edited test files → **All checks passed**. `mypy` on both contract files IN SCRATCH (where the new APIs resolve) → **Success, no issues**. (At HEAD mypy flags the not-yet-existing `blocked_by` param — that IS the RED contract; the builder clears it.)

---

## GROUNDING (verified @HEAD `c0071cd`, cited not re-transcribed)
- Spec: `docs/plans/v2/design/2026-08-11-task-coordination-substrate.md` §2A/§2C + ADDENDUM A-174/A-262. Design sidecar: `REPORT-fable-design-05b.md` FOLLOW-UP A (#174), ADDENDUM A-262 (#262).
- Store law: `docs/reference/surrealdb-31-capabilities.md` §1.1 (`OVERWRITE` fields / `IF NOT EXISTS` indexes), §2 (silent-UPDATE-no-op enemy; `SELECT *` omits NONE column), §4 (RELATE bound-RecordID; `blocks` is ENFORCED from birth — `surreal_schema.py` `BLOCKS_RELATION`; #105), §5 (hot-row: retry in ONE driver, ≥8-way overlapping lifetimes).
- #174 seams: `TaskLedger.supersede_task` (`tasks.py:1876`), `_supersede_fragment` (`:1966`), `_new_task_content` (`:2485`), `create_task` (`:1135`, the template), `_reject_unusable_blockers` (`:2216`→shared `reject_unknown_rows`), `_refuse_a_cycle` (`:2268`→`find_blocked_by_cycle`), `_relate_fragment` (`:2190`).
- #262 seams: `_comms_register` (`server.py:5957`), `_render_comms_register` (`:6647`), `_render_comms_fleet_row` STALE predicate `heartbeat_age_s > stale_after_s` (`:7159`), `stale_after_s = config.comms.stale_heartbeat_s` (`DEFAULT_COMMS_STALE_HEARTBEAT_S = 600`, `config.py:455`), `AgentRegistry.get_agent`/`_resolve_row`/`_select_rows_by_name` (`agents.py:714`/`:539`/`:530`), `TaskLedger.get_task` (`tasks.py:1206`), `AppContext._render_age` (`server.py:6632`, single largest-fit unit).

---

## #174 — supersede inherits/overrides the SUCCESSOR's OWN `blocked_by`

### Defect (verified)
`supersede_task(task_id, *, subject, description, created_by)` calls `_new_task_content(subject, description, None, …)` (literal `None`) and `_apply([_supersede_fragment(…)])` with **no `_relate_fragment`** → successor born `blocked_by=[]`, no `blocks` edge. Dependency structure silently dropped; harm = VISIBILITY.

### Contract (tests, all in `test_blocks_edge.py`, real-only fixture)
| pin | test | RED-at-HEAD mode |
|---|---|---|
| INHERIT (default) | `TestTheMirrorHoldsAtEveryWritePath::test_the_SUPERSEDED_successor_INHERITS_predecessor_blocked_by` (flipped corpse) | assertion (`[] != [blocker]`) |
| CLEAR (`[]`) | `TestSupersedeCarriesBlockedBy174::test_CLEAR_…` | TypeError (param absent) |
| REPLACE (`[C]`, not merge) | `…::test_REPLACE_…_is_not_a_merge` | TypeError |
| inherited-SUPERSEDED blocker → refuse, mint nothing (headline/trust) | `…::test_an_INHERITED_SUPERSEDED_blocker_is_REFUSED_and_nothing_is_minted` | assertion (no raise) |
| override-phantom → refuse, mint nothing | `…::test_an_OVERRIDE_PHANTOM_blocker_is_REFUSED_…` | TypeError |
| **self-ref → refuse-and-teach, mint nothing (R1 blocker; explicit `blocked_by=[X]`)** | `…::test_supersede_REFUSES_a_successor_blocked_by_the_task_it_SUPERSEDES` | TypeError |
| **self-ref inherited (X's own blocked_by contains X; only the dedicated check sees it)** | `…::test_supersede_REFUSES_an_INHERITED_self_block` | assertion (no raise) |
| ONE-IMPL blocker-check reuse (mutate `reject_unknown_rows` → refusal vanishes) | `…::test_supersede_ROUTES_THROUGH_the_SHARED_blocker_check` | wrong-build discriminator (green at HEAD) |
| cycle route-through (STRUCTURAL — F3: a fresh successor can't close a cycle) | `…::test_supersede_source_calls_BOTH_shared_blocks_edge_prechecks` (AST) | assertion (calls none) |
| edge-aware atomicity: concurrent double-supersede-with-deps → 1 successor, its edges, 0 orphan edges | `…::test_concurrent_supersede_with_deps_mints_ONE_successor_zero_orphan_edges` | assertion (no edges) |
| served surface: `lore_tasks supersede` threads `blocked_by` AND names successor's resolved `blocked_by` | `…::test_tool_seam_supersede_threads_blocked_by_and_SURFACES_it` (real `_tool_seam`) | assertion |

Sentinel discipline is DISCRIMINATED as a triple: INHERIT (no arg → carries `[blocker]`) vs CLEAR (`[]` → empty) vs REPLACE (`[C]` → `[C]`, not `[blocker,C]`). A build conflating `None`/`[]` fails CLEAR-or-INHERIT.

### SCOPE
ONLY the successor's own `blocked_by`. NOT the dependents blocked_BY the superseded task (the separate #356). The existing `_render_supersede_result` stranded-dependents WARNING is the #356 surface — left untouched.

---

## #262 — register discloses the holder's LIVENESS (Reading 1: disclose, never refuse)

### Defect (verified)
`_comms_register` stores `task_id` verbatim and NEVER reads the task ledger. `register(task_id=X)` where X is held by another agent Y is silently accepted.

### Contract (`test_comms_register_notice.py`, live ctx: registry + task_ledger + brief_ledger on ONE store)
- **Discriminating triple:** self-held → NO notice · other-held → notice · unheld → NO notice.
- **Liveness render set (each fate forced; ∀ = quantifier law):** live→`active` · STALE(age>threshold)→`⚠ STALE, last seen Nm ago` · retired→`retired` · unresolvable holder→`Y not found in registry` (**never `active` — the fatal false-clear Forgery-pin**) · no-such-task→`task X not found` · ambiguous holder→most-recent-heartbeat wins, **never raises**.
- **TRUST:** register NEVER refuses / NEVER raises in ANY state (idempotent + cheap preserved).
- **ONE-IMPL (two-leg, sharpened after adversary MINOR):** (a) mutate `config.comms.stale_heartbeat_s` → BOTH surfaces flip at one threshold (`test_both_surfaces_flip_at_one_threshold`) — proves a shared THRESHOLD SOURCE (no cloned 600 constant). (b) mutate the extracted PREDICATE `AppContext._heartbeat_is_stale` logic (always-False then always-True) → BOTH surfaces flip together (`test_both_surfaces_share_the_EXTRACTED_predicate`) — proves shared LOGIC, not just the number (a private `age > threshold` clone in either surface would ignore the patch). Together: threshold-source AND predicate shared.
- **Assertion hygiene:** liveness-token asserts scope to the `note:` line via `_notice_line()` — the register HEAD always renders `— status active` for the REGISTERING agent, so a bare `"active" in text` is non-discriminating. (This weakness was caught BY the reference build and fixed — see §FORKS.)

### SCOPE
ONLY the register-path notice + the STALE-predicate share. NOT the query/fleet enrichment, `reap`, or `assign`/`assignee` (the coordination packet).

---

## FORKS (all four ruled by the lead; residuals surfaced)
- **F1 (#262, ruled):** `get_agent` CANNOT deliver the design's render set — it RAISES on ambiguity and EXCLUDES retired rows (a retired holder → `UnknownAgentError`, byte-indistinguishable from not-found). Lead ruled: pin BEHAVIOR, builder wires `_select_rows_by_name`, not `get_agent`. **New collision recon surfaced:** `test_comms_footer.py` Ruling 5.3 calls `get_agent` "the ONE resolution seam; a second path is a #102 escalation." **Reconciled** in the reference build: `resolve_holder` shares the raw FETCH (`_select_rows_by_name`) beneath a distinct DISCLOSE-not-refuse policy; `get_agent` stays the seam 5.3 governs. Proof: all 1359 comms tests incl. `test_comms_footer` pass with `resolve_holder` present. **Builder + adversary must affirm this reconciliation stands.**
- **F2 (#174, ruled):** `test_mcp_server.py` is in scope. I placed the served-surface pins in `test_blocks_edge.py` via the real `_tool_seam` instead (D1) — avoids fake-lockstep, keeps it real. F2's intent is met.
- **F3 (#174, ruled):** cycle route-through is STRUCTURAL (AST), not a behavioral `TaskCycleError` fixture — a fresh successor id has no incoming edges. The blocker-check reuse IS behaviorally mutation-proven. Confirmed.
- **F4 (#262, ruled):** retired-takes-precedence over STALE; fixtures keep the retired holder's heartbeat fresh to avoid the overlap. Confirmed.
- **Self-caught (assertion hygiene):** the reference build's first green run caught that 5 of my #262 liveness assertions were non-discriminating (the register HEAD's own `status active` satisfied `"active" in text`). Fixed by scoping to `_notice_line()`. This is the "assertions must discriminate" law, caught by building the reference — the value of the satisfiability receipt.

---

## BUILDER OBLIGATIONS (my RED contract does NOT ship these; each is AUTO-ENFORCED by an existing invariant, and each is proven dischargeable in the scratch build)
1. **`FakeTaskLedger.supersede_task(…, blocked_by: list[str] | None = None)` lockstep.** Once the dispatch passes `blocked_by=blocked_by`, the 2 existing `test_mcp_server.py::TestTasksTool` supersede tests (which use the fake) TypeError until the fake accepts it. Give the fake the SAME sentinel (INHERIT/CLEAR/REPLACE, deduped). Proven in scratch (`_task_fakes.py`).
2. **`_render_supersede_result` containment probe shape.** The new render branch (successor `blocked_by` via `render_attributed`) makes `test_link5_render_containment.py::TestEveryDrivenRenderBranchIsExercised` go RED (un-run branch) until the `_render_probes()` entry for `_render_supersede_result` gets a shape with a NON-EMPTY, forgery-carrying `successor_blocked_by` — which also discharges the served-free-text hostile-fixture law for the new render. Exact shape proven in scratch: `_served("_render_supersede_result", _tok(g,"sup","task_id"), _tok(g,"sup","successor_id"), [], [_tok(g,"sup","dependent")])`.

Both can only exist AFTER the signature/render change, which is why they are builder-phase, not RED-contract. The existing invariants make them non-skippable.

---

## REFERENCE BUILD (the instrument — durable form; scratch tree is disposable)
Exact edits that took the contract 0-failed (`/home/ejprice/scratch-verbs-05b`, provenance-asserted):
- `tasks.py::supersede_task`: add `blocked_by: list[str] | None = None`; resolve `dependencies` (None→`list(dict.fromkeys(row[_COL_BLOCKED_BY] or ()))`, else `list(dict.fromkeys(blocked_by))`); **self-ref guard: `if task_id in dependencies: raise TaskCycleError("a successor cannot be blocked by the task it supersedes …")`** (R1 — before the pre-checks, since neither sees it); `await self._reject_unusable_blockers([(e,e) for e in dependencies])`; `await self._refuse_a_cycle({new_id: dependencies})`; `_new_task_content(…, dependencies, …)`; `_apply([_supersede_fragment(…), _relate_fragment([(b, new_id) for b in dependencies])])`. (RELATE after CREATE — ENFORCED needs `out` to exist; the stamp-CAS envelope is preserved, NOT delegated to `create_task`.)
- `server.py` supersede dispatch (`:3938`): pass `blocked_by=blocked_by`; `successor = await self.task_ledger.get_task(successor_id)`; feed `successor.blocked_by` to the render.
- `server.py::_render_supersede_result`: 4th param `successor_blocked_by`; append `, blocked_by [ids]` (via `render_attributed` per id) when non-empty.
- `server.py`: add `AppContext._heartbeat_is_stale(age_s, stale_after_s)` (the extracted STALE predicate) and call it from `_render_comms_fleet_row`; add `AppContext._holder_liveness_notice(self, *, agent, task_id)`; compose it into `_comms_register`'s return via `render_compose`.
- `agents.py`: add `AgentRegistry.resolve_holder(name)` (retired-inclusive, most-recent-heartbeat, `None` on miss; shares `_select_rows_by_name`).
- `_task_fakes.py` + `test_link5_render_containment.py`: the two BUILDER OBLIGATIONS above.

**SCRATCH DISPOSITION:** `/home/ejprice/scratch-verbs-05b` holds a working reference build (a `scratch_copy.sh` tree — disposable by design; edits captured above). It has no git history and is NOT the repo tree. Recommend the builder read this section rather than the scratch; I can `rm -rf` it on the lead's word (leaving it as an optional builder reference otherwise).
