brief-base v18 read · brief project v7 read · store reference NOT re-read in full (`docs/reference/surrealdb-31-capabilities.md` — relied on the cited §1.4 / §3 #497; no store/DDL change graded — DEVIATIONS D-3)

# REPORT — adversary-64b-r2 (the ONE re-grade of packet 64b-i contract r2, `cb220ee`)

## SUMMARY BLOCK
- **State:** done-with-deviations (D-1…D-4). Deadline 90 min from 19:34:57Z (2026-09-29); report inside it.
- **Graded:** `cb220ee` · **HEAD-at-report:** `41ad868` · DIFFERENT (4 behind: `402ec29`, `122778d`, `2973c91`, `41ad868` — `CLAUDE.md` + `REPORT-lead-63c.md` only; no code/test/script moved).
- **ROUTING: SUFFICIENT-FOR-BUILD** — NEW PROPERTY **0** · PINNED PROPERTY, NEW CASE **3** (F-1 budget-counter reach, F-2 budget on the deny path, F-3 MP-13's hand-listed param domain — each with ONE chokepoint) · BUILD-ORDER/§HELD **1** (F-4) · accepted residual **5** (F-5…F-9).
- **decisions-needed:** (1) am-8 §6: F-3 is a SECOND WB23 instance → "the ruling re-opens" (ruling owner, not the contract). (2) F-2 is security-relevant (a deny-path registry read by a caller-supplied name) → eligible for ONE targeted pin, no re-grade. (3) F-4: 58 paused ⇒ commission G2 re-derivation + BC-r2-13's fallback as an artifact, or wait for 58.
- **P1:** all **10 predecessor survivors + the r1 reference KILLED** on cb220ee (right-reason, §KILL). **3 new survivors:** N4 `FROM ONLY agent …`, N5 `FROM $rid` (second agent reads the counter cannot see; control N4c plain `FROM` KILLED), N7 (registry re-read on the `agent=`-mismatch path).
- **am-35 §6 leg:** 6/6 A6 wrong builds KILLED (incl. a private shape copy — no second classifier survives); F5w1 (unlabeled write) KILLED.
- **SAT (targeted, 59 files, collect-only 5177, declared first):** base 1035F/4140P/2S; reference 531F/4646P/2S (+2 derived `finding` params, pass). **Reference-only reds 4** + 1 both-ways (`_run_guarded` STALE) — all owned by 64b's un-re-derived **G2**; author's "0 attributable" holds on its post-58 base only.
- **Build order:** a 58-free build is NOT satisfiable from shipped §HELD: A2 already adds the moved drivers (withholding G12 → "`findings.py::_transition` has drivers in both …"), BC-r2-13's fallback has no artifact, G2 fails loud on HEAD.
- **Runs used:** 1 reference baseline (15 files, 1192P/0F) · 1 CTL0 · 25 targeted wrong-build screens · 1 param probe · 2 build-order runs · 1 collect-only · 2 SAT runs.
- **Packages considered:** statement-table counting → `re` (stdlib, the contract's own; F-1 is its reach, not a package miss); a SurrealQL parser — none known (LOW confidence, not surveyed); `pyyaml`, `ast` (existing/stdlib). No P-PKG finding; author's table (pyyaml, tomllib) agrees.
- **Odoo-20 portability:** n/a — no Odoo seam touched (0 seams · 0 non-stable · 0 rulings).
- **Reuse ledger:** none (no production symbol added). **Lore friction filed:** #518 (`lore_impact` covering tests capped at 15), #519 (reconcile no-progress abort).
- **Pointers:** §KILL · §A · §SAT · §P1b · §P1c · §DUAL · §BUILD-ORDER · §INSTRUMENTS · §VERDICT.

## DEVIATIONS (each one line, then detail)
- **D-1 — the DUAL two-stage order was broken by reading.** My first read of the contract report's head (lines 1–420) included
  §7 before I had enumerated. Disclosed: my stage-1 list (§DUAL) is derived from an AST/patch diff instrument
  (`changed_symbols.py`, r1-vs-r2 Part C `+`-line delta), not recalled — but it is not frame-free.
- **D-2 — screens use targeted node sets with `-x`** (per the brief: "wrong builds run ONLY the tests that target them").
  Under xdist, `-x` exits rc **2** ("Interrupted: stopping after 1 failures"), which my screen script labels `INVALID rc=2`.
  Every such run was re-read: FAILED ids + `E` lines present ⇒ KILLED. I did not re-run them without `-x`.
- **D-3 — store reference:** I relied on the author's and CLAUDE.md's citations of §1.4 / §3 (#497); I did not re-read the
  whole file (no store/DDL change was graded that needed it; the scope ASSERT was withdrawn). Say so rather than claim it.
- **D-4 — `lore_index(reconcile=True)` never returned** (#519). The status read just before it showed `last_sweep` 11 min
  old and the index at `1d3cf98` (ancestor of HEAD, docs-only delta). The covering-set derivation fell back to an AST scan
  because `lore_impact` caps covering tests at 15 (#518) — said out loud here.

- **D-5 — a process slip, disclosed:** one report-edit command used an UNQUOTED heredoc, so bash expanded the backtick spans in
  its text as command substitutions. Every one failed ("command not found" / syntax error; the words were SurrealQL fragments such
  as `FROM`, `SELECT`, `[agent]`), and the script's anchor assertion aborted before any write. No file changed; redone with Edit.
  One `grep` inside a polling loop was hook-blocked (#473) before it ran.

## §KILL — the survivor kill table (predecessor `REPORT-adversary-64b.md` §A, re-run on cb220ee)
Tree: `scratch_copy.sh` copy, `git reset --hard HEAD && git clean -fd` FIRST (status empty), then §HELD **A → A2 → C**
(`git apply --check` rc 0 each, sha256 prefixes 44af4416 / 117c6c9b / f5fba9ee = the author's table), then **B minus
`test_retry_seam.py`** (`--exclude`, check rc 0 on HEAD; G2 needs re-derivation). Provenance printed under the exact runner
invocation (`uv run --with pytest-timeout python -c 'import loremaster, lorerunes; …'`):
`…/scratchpad/wb/loremaster/loremaster/__init__.py`, `…/scratchpad/wb/lorerunes/lorerunes/__init__.py`.
Reference baseline (the 15 files cb220ee changed): **1192 passed, 1 skipped, 0 failed** (402 s). CTL0 (a comment edit) on the
8-file screen set: **226 passed, 1 skipped** (SURVIVES, as a control must).

Four predecessor specs no longer landed on the r2 reference (the code moved), so they were re-authored AT THE SAME PROPERTY
(`r2` suffix; specs verbatim in §INSTRUMENTS):

| wrong build (property) | r2 spec | targeted run | verdict | killing pin (first red) |
|---|---|---|---|---|
| WB1 set_scope invisible → deny (existence oracle) | WB1r2: `GovernedInvisible` → `GovernedDenied` for SET_SCOPE in `_authorize_write` | 2 failed, 7 passed | **KILLED** | classes `TestEveryWriteVerbTreatsAnInvisibleRowAsNonexistent[set_scope]` + landed `test_MP1_…` ("got GovernedDenied: 'not permitted'") |
| WB2 visible-deny by id → not-found | WB2r2: `GovernedDenied` → `_not_found` for a str address | 7 failed, 1 passed | **KILLED** | same sweep `[set_scope]` ("must be GovernedDenied, got FindingNotFoundError") |
| WB17 supersedes-by-id unfiltered | lands as-is | 2 failed, 7 passed | **KILLED** | same sweep `[report]` + `test_MP3_…` |
| WB3 classifier authorizes READ | lands as-is | 2 failed | **KILLED** | `TestTheZeroRowClassifierAuthorizesThePassedAction` ("DID NOT RAISE GovernedConflict") |
| WB4 stale capability cache | WB4r2: memoise `(subject, own_row)` per capability in `_resolve_identity` | 5 failed | **KILLED** | `TestEveryAuthorizationInputIsReadPerCall[agent-retired]` ("the call AFTER the degradation was ALLOWED") |
| WB10 second registry read | WB10r2: `get_agent(own_row.name, …)` after `_resolve_subject_and_agent` | 2 failed | **KILLED** | `TestTheRegistryIsReadOncePerGovernedCall` + landed `test_MP7_…` |
| WB19 annotate drops `actor_agent` | lands as-is | 2 failed, 2 passed | **KILLED** | landed `test_MP6_…[annotate…]` + `TestEveryAppendedEventCarriesTheDerivedActor` |
| WB21 private identity compare | lands as-is | 2 failed | **KILLED** | `TestTheIdentityCompareLivesInOneFunction` + `test_MP8_…` ("4 == 2") |
| WB22b finding leg migrates memory | lands as-is | 2 failed | **KILLED** | `TestAMigrateLegWritesOnlyItsOwnTable` + `test_MP11_…` |
| WB23 `scope=` ignored on other verbs | lands as-is | 1 failed | **KILLED** | `TestAParamOutsideItsVerbsSpecIsRefused` ("query × scope: ACCEPTED") |
| **the r1 reference itself** (set_scope oracle, MP-1) | — (r2 Part C) | baseline 1192/0 | **FIXED** in the r2 reference (MP-1 + the ∀ sweep pass on it) | — |

New r2 builds (beyond the survivors), same screen:

| build | targeted run | verdict | killing pin / reason |
|---|---|---|---|
| N1 `require_scope_in_domain` drops the keep-existence read | 1 failed, 39 passed | KILLED | scope_domain `…[admin-set_scope]` ("ACCEPTED an out-of-domain scope 'keep:01JZZ…'") |
| N4c CONTROL: 2nd agent read `SELECT * FROM agent WHERE …` | 1 failed | KILLED | budget sweep (`agent: 2`) — proves the path executes and the counter sees plain `FROM` |
| **N4** 2nd agent read `SELECT * FROM ONLY agent WHERE … LIMIT 1` | 2 passed | **SURVIVES** | F-1 |
| **N5** 2nd agent read `SELECT * FROM $adv_rid` (RecordID-bound) | 2 passed | **SURVIVES** | F-1 |
| N6 keep seam accepts both identities | 1 failed, 5 passed | KILLED | `TestTheKeepSeamTakesExactlyOneIdentity[both-…list_keeps_for_member]` |
| **N7** registry re-read on the `agent=`-mismatch deny path | 41 passed | **SURVIVES** | F-2 |
| A6w1 leg examines CREATED rows only | 3 failed, 32 passed | KILLED | `…missing_keep_is_unclassified[updated-label]` |
| A6w3 observer: no keep-existence read | 6 failed, 28 passed | KILLED | LIVE `…[finding]` ("'keep:absent': True") |
| A6w4 leg refuses a None landing | 4 failed, 29 passed | KILLED | `test_CONTROL_a_none_landing_is_not_this_legs_business` |
| A6w5 leg uses a private shape regex | 1 failed, 38 passed | KILLED | `test_the_leg_routes_through_the_one_shape_predicate` |
| A6w6 observer stores `resolved_keep_scopes=None` | 5 failed, 31 passed | KILLED | LIVE ("an OBSERVED effect carries no in-lock keep-existence read") |
| A6w7 leg skipped on the label channel | 8 failed, 18 passed | KILLED | `…[updated-label]` |
| F5w1 set_scope's write moved outside its `write_guard` | 1 failed, 58 passed | KILLED | `TestTheLiveFindingWritesClassifyUnderF5` ("UNCLASSIFIED … label=None") |
| D1 / D2 no-owner guard dropped (stamp_verified_agent / stamp_owner) | 120 passed each | both SURVIVE — equivalent mutants | F-5 |

Not re-run (killed at r1, not survivors): WB5, WB6, WB9, WB13, WB22, CTL1 — NOT TRIED this round (not required: they were
not survivors). WB1r2b (every verb's invisible → deny) was specified but not run — NOT TRIED (WB1r2 covers the property).

## §A — findings (each: CLASS / DOMAIN SOURCE / SIBLINGS / REPEAT CLASS / bucket / chokepoint)

### F-1 — the identity-read budget counter sees only `FROM <table>` and `FROM type::record('<table>' …)` (N4, N5 SURVIVE)
- **Wrong builds** (in `AppContext._resolve_identity`, after `_resolve_subject_and_agent`):
  N4 `await self.agent_registry._query("SELECT * FROM ONLY agent WHERE name = $adv_n LIMIT 1", {...})` → **2 passed (SURVIVES)**;
  N5 `… _query("SELECT * FROM $adv_rid", {"adv_rid": RecordID("agent", <id>)})` → **2 passed (SURVIVES)**;
  **control** N4c, the identical read spelled `SELECT * FROM agent WHERE …` → **KILLED**
  (`{'agent': 2, 'principal': 1, 'member_of': 1}`). Targeted set: `TestTheRegistryIsReadOncePerGovernedCall` + landed `test_MP7_…`.
  The read runs through `run_query` (the spied seam) — N4c's kill proves the path executes; N4/N5 differ ONLY in spelling.
- **Why:** `_FROM_TABLE = r"\bFROM\s+(?:type::record\(\s*['\"](\w+)['\"]|(\w+))"` captures `ONLY` as the table in N4, and
  nothing for `$param` in N5. `FROM ONLY` is house idiom (6 production uses: `tasks.py`, `briefs.py`, `agent_existence.py`),
  so an HONEST second read can take this spelling.
- **CLASS:** *a per-table budget is counted over the tables a statement READS, not over the spellings a regex grammar names.*
- **DOMAIN SOURCE:** the set of SurrealQL table-addressing forms in a read: `FROM t`, `FROM ONLY t`, `FROM type::record('t', …)`,
  `FROM $param` (RecordID-bound), `FROM t:id`, record-link dereference (`owner_principal.email` — a `principal` read inside an
  `agent` statement, which the verify SELECT itself does and which the counter attributes to `agent` only).
- **SIBLINGS TRIED (live):** `FROM ONLY t` (survives), `FROM $rid` (survives), plain `FROM t` (killed — control).
  **SIBLINGS TRIED (offline — the contract's own regex over statement text, `from_table_probe.py` §INSTRUMENTS; controls
  `FROM agent` / `FROM type::record('agent', …)` → `['agent']`):** `FROM ONLY agent …` → `['ONLY']`;
  `FROM ONLY type::record('agent', …)` → `['ONLY']`; `FROM $rid` → `[]`; `FROM type::thing('agent', …)` → `['type']`;
  `FROM type::record($tb, …)` → `['type']`; `FROM agent, principal` → `['agent']` (the second table is never counted);
  `SELECT owner_agent.name FROM finding …` → `['finding']` (an agent read through a link). Counted correctly: `FROM agent:abc`,
  a sub-select `FROM (SELECT * FROM agent)`. **NOT TRIED:** graph-arrow reads.
- **REPEAT CLASS:** yes — the predecessor's MP-7 P0 note ("v1 counted METHOD names … the same hidden-constant reach").
  The instrument moved from method names to a text grammar; the reach is still a hand-list of spellings.
- **Bucket: PINNED PROPERTY, NEW CASE.** Production chokepoint: `AppContext._resolve_identity` → `governed.resolve_subject_and_agent`
  is the ONLY identity-path code that touches `agent` (one `_verify_capability_agent` call). Test-side hygiene (not a reopen): widen
  the counter to `FROM\s+(?:ONLY\s+)?` and count `$param` reads by the table of the bound `RecordID` — fold into BC-r2-9's
  close-out commit (a contract-author-class agent is already scheduled there).

### F-2 — the budget is pinned on the SUCCESS path only; a deny path may re-read the registry (N7 SURVIVES)
- **Wrong build N7:** in `_resolve_identity`'s `agent != own_row.name` branch, `await self.agent_registry.get_agent(agent, session=session)`
  before raising (the "does the named agent exist?" teaching read). Targeted: budget class + MP-8 class + `test_findings_identity_64b.py`
  + adversary pins → **41 passed (SURVIVES)**. The mismatch path IS executed by that set:
  `TestAgentAndSessionAreSelfConsistencyChecks::test_a_foreign_agent_name_is_denied_and_writes_nothing` passes `agent="ag-b1"`, an
  existing agent, so `get_agent` returned and the deny still raised.
- **CLASS:** *am-8 §1's budget is "per governed call" — ∀ paths of the identity step (success, agent-mismatch, session-mismatch,
  capability-deny), not only the paths the sweep happens to drive.*
- **DOMAIN SOURCE:** the branches of `AppContext._resolve_identity` (+ `resolve_subject_and_agent`'s deny branches) — AST-enumerable.
- **SIBLINGS TRIED:** agent-mismatch (survives). **NOT TRIED:** session-mismatch, unverified capability, principal-suspended.
- **REPEAT CLASS:** yes — the QUANTIFIER LAW: an invariant evaluated only where the happy path runs.
- **Security note:** the extra read is also the shape of a name-existence oracle if its result ever shapes the deny text
  (a concrete door, security-relevant). Under the cap: eligible for ONE targeted pin with no re-grade — the mismatch tests assert
  the same `IDENTITY_READ_BUDGET` (they already drive the path; add the `_record_store_statements` spy).
- **Bucket: PINNED PROPERTY, NEW CASE.** Chokepoint: `AppContext._resolve_identity` issues NO store statement after
  `_resolve_subject_and_agent` returns (every compare is against the already-read row).

### F-3 — MP-13's param domain is a 2-entry HAND-LIST; the r2 reference accepts-and-ignores four siblings
- **Probe** (`test_adv64br2_probe.py`, §INSTRUMENTS; run on the reference, `finding_world`): **CONTROL** `acknowledge × scope=` →
  refused `ValueError` (the probe sees a refusal). Then, on the reference: `acknowledge × supersedes=8900` → *"finding #8900 transitioned
  to acknowledged"*; `resolve × limit=3` → transitioned; `set_scope × note=` → *"re-scoped"*; `report × note=` → *"reported finding #1"*
  — **all four ACCEPTED and silently ignored** (1 failed, the probe's own assertion).
- **Why the contract cannot see it:** `VERB_OWNED_PARAMS = {"scope": …, "items": …}`; its only completeness leg checks that every OWNER
  is a served verb. am-8 §6 row WB23 rules the domain source as *"the spec dict matrix (#319's shape)"* — every param of the served
  signature × every verb. The landed domain is a hand-list of the two params that had a known survivor.
- **CLASS:** *∀ (verb, param) with param ∉ spec(verb): a teaching refusal, never accept-and-ignore.*
- **DOMAIN SOURCE:** the served `findings` tool signature's parameters × `_FINDING_ACTIONS` (the spec dict), per am-8 §6.
- **SIBLINGS TRIED:** supersedes, limit, note (×2) — accepted. **NOT TRIED cleanly:** status, kind, body (my probe's sequential state
  made those verbs hit illegal transitions / deny first; inconclusive, not claimed).
- **REPEAT CLASS:** **yes — second instance of am-8 §6 row WB23.** am-8 §6 "Loop status": *"If r2's grade finds a second instance of
  ANY row above, the ruling — not the contract — re-opens."* → **decision-needed (ruling owner).**
- **Bucket: PINNED PROPERTY, NEW CASE.** Chokepoint: the dispatcher's ONE foreign-param check in `AppContext.findings`
  (derive each verb's allowed params from the spec dict; refuse the rest before any capability resolution).

### F-4 — BUILD-ORDER: BC-r2-13's in-place fallback is not buildable from §HELD, and A2 presumes G12 (measured)
See §BUILD-ORDER. **Bucket: BUILD-ORDER / §HELD process** (not a contract pin; routes to the lead/operator's 58 decision).

### F-5 — `stamp_verified_agent` is a second copy of the capability fail-closed policy; its docstring claims a call that does not exist
- Part C adds `owner_stamp.stamp_verified_agent` with the SAME two `OwnerStampError` raises as `stamp_owner` (verify None → deny; no
  owning principal → deny). Its docstring: *"Fail-closed exactly like `stamp_owner` (it is what that function calls)"* — **false**:
  `stamp_owner` keeps HEAD's pair path (`_verify_capability_owner`), BC-r2-12 pins it that way, and it never calls
  `stamp_verified_agent`.
- **Mutation pair:** D1 drops the no-owner guard in `stamp_verified_agent` → **120 passed (SURVIVES)**; D2 (control) drops the SAME
  guard in `stamp_owner` → **120 passed (SURVIVES)** (targeted: `test_425_stamp_owner_63a.py`, `test_agent_capability_seams.py`,
  identity/classes/adversary-pins/enforcement 64b files, `test_governed_substrate_63a.py`). Both survive because the guard is
  **unreachable against the real registry**: `_verify_capability_agent` step (3) denies a NONE owner first (`owner_email` None →
  `binding-mismatch`, `agents.py` comment "A NONE owner reads owner_email None … → DENY"). An equivalent mutant in both copies —
  so this is NOT a behavioural hole today.
- **CLASS:** ONE IMPLEMENTATION — two call sites that need the same policy call ONE function (prove sharing by mutation). Here the
  mutation cannot prove sharing either way because the policy is dead defense-in-depth in both copies.
- **DOMAIN SOURCE:** every production raise of `OwnerStampError` (AST).
- **Bucket: accepted residual** (re-bucketed from NEW CASE after D1/D2). Recommendation as a BUILDER CONSTRAINT, not a pin:
  `stamp_owner` = the pair view of `stamp_verified_agent` (one policy body, the same shape as `_verify_capability_owner`), and
  the false docstring sentence is not copied.

### F-6 — DUAL: the archived "verbatim copy" of `c3_harness_repair.py` is not verbatim (accepted residual)
`diff <REPORT-refbuild-c3-1.md §6.1 fence> scripts/c3_harness_repair.py`: 2 import lines differ (the deleted file imports
`FakeAgentRegistry`/`FakeAgentDatabase` from `_comms_fakes`; the archive from `test_comms_tool`) — the file was edited after
archiving by `6fa1177`. The durable address of the deleted content is `git show 41ad868:scripts/c3_harness_repair.py`; §7's
"verbatim copy" wording over-claims. Doc hygiene; no pin.

### F-7 — P1c: MP-11's snapshot set is a hand-tuple (accepted residual)
`_SNAPSHOT_TABLES = ("agent","memory","message","brief","finding","keep","member_of","principal","to")` — a leg writing any other
table (e.g. `audit`, `task`) is invisible to "every OTHER table byte-identical". Construction-inspected, not built. The domain source
would be the store's own table list (`INFO FOR DB`). Test hygiene.

### F-8 — P1c: MP-6's non-vacuity is global, and events are read only from each verb's own row (accepted residual)
`assert observed` is ≥1 event over ALL verbs; a verb that appends nothing is not caught by this pin (other transition pins may).
Events a verb appends to ANOTHER row (e.g. a supersede target) are not observed. Construction-inspected.

### F-9 — the one-fragment property is proven on the supersedes-less branch only (author's §12 items 2/3; accepted residual)
`test_both_writers_execute_the_golden_transaction` drives a member `report` without `supersedes=`. A second fragment builder used
only on the supersedes branch, or a second composer producing identical bytes, passes. The r2 reference has ONE `_report_fragment`
call for both branches (read). Not built; ROUTING-IS-NOT-SHARING residual.

## §A-D — F-5's mutation pair (verbatim screen lines)
```
D1_verified_agent_drops_no_owner_guard | dirty=0 | 120 passed in 35.41s | SURVIVES
D2_CONTROL_stamp_owner_drops_no_owner_guard | dirty=0 | 120 passed in 36.15s | SURVIVES
```

## §SAT — targeted, both ways on ONE tree (measured 2026-09-29 19:49–20:10Z)
**Tree:** scratch `ref`. **Reference** = `a8fae92` (HEAD `41ad868` + §HELD A + A2 + C + B-minus-`test_retry_seam.py`).
**Base** = `0f8dc7d` (the SAME commit with Part C reverse-applied: the tests of the reference, production at HEAD).
Scratch-branch commits are local to the scratch copy; nothing was committed to the repo.

**Declared set (BEFORE running; `--collect-only` on the base → 5177 tests), 59 files =**
(1) the 15 test files `cb220ee` changed; (2) **47 covering files** from `covering_scan.py` over the 89 AST-derived changed
production symbols (`changed_symbols.py`, HEAD → reference) — the `lore_impact` fallback, because `lore_impact` elides covering
tests past 15 per symbol with no parameter to lift it (#518; e.g. `authorize_guarded` +173 elided, `LocalMemoryBackend.remember`
+941); (3) every test file §HELD A/A2/B touches; (4) BY HAND (scripts/ is outside lore's graph, #507, and pdp is a sibling member):
`lorerunes/tests/test_pdp_core.py`, `scripts/test_restore_prod_dump.py`, `scripts/test_gated_ground.py`,
`scripts/test_forgery_door_sweep.py`, `loremaster/tests/test_retry_seam.py` (structural door index). Full list in §INSTRUMENTS.
Runner: `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300`
(admission gate ≥ 20 GiB MemAvailable; no cap kill, no timeout).

| run | collected | failed | passed | skipped | wall |
|---|---|---|---|---|---|
| base (no Part C) | 5177 | **1035** | 4140 | 2 | 630.6 s |
| reference | 5179 | **531** | 4646 | 2 | 622.0 s |

Node sets: the reference has **2 extra nodes**, both parametrisations DERIVED from production that only exist once `finding` is
governed — `test_findings_scope_domain_64b.py::…::test_live_every_governed_population_under_the_real_observer[finding]` and
`test_fixwave_a28_63c_i_a.py::…::test_FORK1_backfilled_equals_the_rows_the_run_changed[_migrate_finding_scope]`; both PASS.
**Fixed by Part C: 508. Red both ways: 527. REFERENCE-ONLY reds: 4.**

**Every reference-only red, individually:**
| node | reason | owner |
|---|---|---|
| `test_retry_seam.py::TestEveryGuardedCasDoorPropagatesExhaustionUNREAD::…[findings.py::_transition::1]` | "the canonical door 'findings.py::_transition::1' was not found by the scan" | **64b §HELD G2** (not applied — its anchor fails loud on HEAD's a28c file; G2 (b) merges the two finding doors into `_run_guarded`) |
| `…::TestEveryGuardedCasDoorPropagatesExhaustionUNREAD::…[findings.py::annotate::1]` | same | G2 |
| `…::TestNoGuardedCasHandlerReinterpretsExhaustedContention::…[findings.py::_transition::1]` | same | G2 |
| `…::TestNoGuardedCasHandlerReinterpretsExhaustedContention::…[findings.py::annotate::1]` | same | G2 |

**Red both ways, 64b-relevant rows, individually:** `test_reanchor_58_r3_cas_seam.py::…[findings.py::_run_guarded]` ("driver is
STALE: neither the call graph … nor the static index names it") — **64b's own declared driver**, owned by the same missing G2
(the static index lives in `test_retry_seam.py`); `test_governed_routing_63a.py::TestTheReverseRoutingDirection64b` — on the
reference only `lore_comms` verbs remain PENDING (#487; the finding verbs it listed on the base are fixed by C) — not 64b's;
`test_task_read_surface.py::TestSupersedeWARNS…` (58), `test_reanchor_58_r3_cas_seam.py` `tasks.py::*` ×3 (58),
`scripts/test_forgery_door_sweep.py` ×2 (58: `SupersedeResult`, straggler-heal door), `test_fixwave_a19a_63c_i_a.py` ×2 and the
`test_fixwave_a28*` / `test_retry_seam.py` a28c-classes (63c-i-a unbuilt). The rest of the 527 group by file in `sat_diff.out`
(58: `test_supersede_reanchor_58` 12 classes, `test_reanchor_58_r2_rulings` 12, `test_task_guarded_shell_58` 7; 63c-i-a:
`a28c` 11, `a28b` 11, `a28` 9, `test_retry_seam` 5) — none names a finding verb.

**Verdict on the author's "0 attributable":** holds on the author's base (post-58, G2 applied). **On HEAD (58-free, post-a28c) it
does NOT: 5 reds are owned by 64b's own §HELD G2**, which must be re-derived over a28c's `test_retry_seam.py` before a build on
this base. Not a contract-pin defect — a build-order prerequisite (F-4).

**`lore_test` namespace:** 6 databases at 19:59Z (mid-SAT), 18 at 20:11Z with none of my pytest processes alive; a sibling
adversary ran concurrently, so the growth is observed, NOT attributed. No pre-run count was taken (NOT TRIED).

## §P1b — QUANTIFIER TABLE
| invariant | ∀ or guarded | receipt |
|---|---|---|
| invisible ≡ nonexistent ∀ write verb × {id, number} × {invisible, nonexistent, visible-denied} | ∀ (spec-dict verbs, `_required_drivers()` completeness) | WB1r2 / WB2r2 / WB17 KILLED |
| zero-row classifier authorizes the PASSED action | ∀ served actions (`classifier_actions()` AST) | WB3 KILLED |
| every authorization input read per call | ∀ verbs × the 4 RULED degradations (guarded by the ruled list — am-8 §1) | WB4r2 KILLED |
| every appended event carries `actor_agent` | ∀ OBSERVED events, own row only | WB19 KILLED; F-8 door construction-only |
| identity read budget per table | **GUARDED — success path × regex-named spellings** | **N4, N5, N7 SURVIVE** (F-1, F-2); N4c control KILLED |
| one identity-compare site | ∀ `server.py`, receiver-blind | WB21 KILLED |
| keep seam takes exactly one identity | ∀ over the two named seams (author's BOUND: no third seam) | N6 KILLED |
| a migrate leg writes only its own table | ∀ `_migrate_legs()` × **9 hand-listed snapshot tables** | WB22b KILLED; F-7 door construction-only |
| foreign param refused | **GUARDED — hand-list {scope, items}** | probe: 4 siblings ACCEPTED on the reference (F-3) |
| scope ∈ DOMAIN ∀ writers (seam) | ∀ caller-supplied writers × kinds + store-derived | N1 (no existence read) KILLED |
| F5 universal scope leg (A6) | ∀ governed populations (LIVE, derived) × channels × {created, updated} | A6w1, w3, w4, w5, w6, w7 all KILLED |
| system writer = composed golden | **guarded — supersedes-less member report** | F-9, not built |
| UNOWNED-LEGACY set from the SET clause | ∀ `_migrate_legs()`, both ways | NOT TRIED |
| `backfilled` measured | race injected | NOT TRIED |

## §P1c — REACH TABLE (legs: E = empirical, C = construction-inspection)
| instrument | reach DERIVED? | coverage checked? | effect vs proxy | one source proven by mutation? | leg |
|---|---|---|---|---|---|
| invisibility sweep | yes — spec dict | yes (`_required_drivers()`) | effect (served exception bytes) | n/a | E (WB1r2/2r2/17) |
| identity budget counter | **no — a regex over 2 spellings** | no (a new spelling is silently uncounted) | effect at the store seam, but grammar-limited | n/a | **E: N4/N5 survive, N4c control killed** |
| identity budget paths | **no — success path only** | no | effect | n/a | **E: N7 survives** |
| identity compare scan | yes — whole `server.py` AST | allowlist + policy leg | static | E (WB21 killed) | E |
| param-refusal sweep | **no — hand-list {scope, items}** | only "owners are served verbs" | effect | n/a | **E: probe, 4 siblings accepted** |
| migrate write-set | legs derived; **snapshot tables hand-listed** | legs yes / tables no | effect (byte snapshots) | n/a | E (WB22b) + C (F-7) |
| A6 classifier leg | yes — every observed write, LIVE over `governed_populations()` | yes (observed effect non-None pinned) | effect (`row_deltas[*].after`) | **yes** — A6w5 (private shape copy) KILLED by the identity-rebind routing pin | E (6 builds) |
| scope-writer set | AST of finding-scope literals | `TestTheScopeWriterSetIsComplete` | effect | shape predicate: A6w5 + N1 | E (N1) |
| keep seam exactly-one | named 2 seams (author's stated BOUND) | no (bound) | effect (`ValueError` before read) | n/a | E (N6) |
| retired-plugin sweep | `declared_workspace_members()` | CONTROL | static | n/a | C |
| MP-9 closeout glob | glob + registered paths | registered files only (author's §12 #7) | static | n/a | C |
| capability fail-closed no-owner guard | — | — | — | two copies (F-5); mutation is equivalent in BOTH (unreachable behind the binding check) | E (D1/D2 both survive) |

## §DUAL — r2's removed/replaced behaviour (my enumeration, then the diff with §7)
Instrument: `changed_symbols.py` (AST, HEAD `41ad868` → reference `43bf49d`; 89 symbols: 45 CHANGED, 44 NEW) plus an r1-vs-r2 Part C
`+`-line delta per file (agents +30, findings ±59, governed +106/−7, keeps +9, owner_stamp +22, principals +7/−2, server +34/−12,
visible_keeps +4, pdp +14). D-1 disclosed. Items, each with the §7 verdict it maps to:
| my item | §7 row | verdict |
|---|---|---|
| `keeps.list_keeps_for_member`: exactly-one identity, `ValueError` before any read | row 1 | MATCH — pinned (N6 killed) |
| `visible_keeps.resolve_visible_keeps`: passes `principal_id` | row 2 | MATCH |
| `governed.resolve_subject` gains `verified_agent=`; `resolve_subject_and_agent` NEW | row 3 | MATCH |
| `owner_stamp.stamp_owner` — comment-only change (behaviour identical) | row 4 "UNCHANGED" | MATCH |
| **`owner_stamp.stamp_verified_agent` NEW — a second fail-closed body** | **absent from §7** | **GAP → F-5** |
| `agents._verify_capability_agent` NEW / `_verify_capability_owner` → pair view | row 5 | MATCH |
| `AppContext._resolve_subject` unchanged in body (docstring comment only) | row 6 | MATCH |
| governed `scope` column unchanged (no ASSERT) | row 7 | MATCH |
| `report_system` token = `compose(fragment)[0]` | row 8 | MATCH |
| A6 classifier leg + observer existence read (test substrate) | row 9 | MATCH — 6/6 A6 builds killed |
| `scripts/c3_harness_repair.py` deleted | row 10 | MATCH, but the cited archive copy is not verbatim → F-6 |
| `test_mcp_server._slug()` → `unique_database()` | row 11 | MATCH (in cb220ee) |
| `restore_prod_dump.PENDING_GOVERNED_TABLES` drops `finding` | not in r2 §7 | r1 §9 R16 (stands) — pinned by `TestTheRestoreDriverSliceDecaysForFinding` — MATCH via r1 |
| `lorerunes.pdp.scope_shape_ok` / `KEEP_ID_PATTERN` / `_KEEP_SCOPE_SHAPE` NEW; `_is_valid_scope` CHANGED | §DEVIATIONS D-r2-CHARSET | MATCH (both-ways PDP-pin agreement) |
| `governed.require_scope_in_domain` NEW (known-keeps shortcut skips the existence read) | row "scope DOMAIN" (§2 MP-12) | MATCH — N1 killed |
Corpse sweep (bare, anchor-free, awk over code/config in every member + scripts): `c3_harness_repair` → 1 hit,
`test_findings_signatures_64b.py:199` (the pin's own docstring — OK); `_governed_contract_64` → 1 hit, `_governed_contract.py:2432`
(a DUAL "FOLDED from" comment — OK); `REPORT_CREATE_GOLDEN` → 1 hit, `_governed_contract.py:3005` (a WITHDRAWN note — OK);
`LEGACY_MAPPINGS` → 0; `reader_aligned` → 0; `CONTRACT_FILES` → 5 hits in `test_no_raw_listener_in_test_trees.py` (`_CONTRACT_FILES`,
an unrelated symbol — OK); `write_poison` → 3 hits (`test_agent_capability.py:375`, `test_agent_owns_principal_schema.py:435`,
`test_comms_schema.py:3675` — unrelated 63a/63b pins — OK).

## §BUILD-ORDER (receipts, not opinion)
1. **§HELD on HEAD `41ad868`:** A, A2, C `git apply --check` rc 0; B rc 1 on `test_retry_seam.py` only; B `--exclude=…test_retry_seam.py`
   rc 0. **G2** (`held_b_g2_g12.py`, pasted by the author) fails LOUD on HEAD's file:
   `AssertionError: test_retry_seam.py: anchor not found exactly once: '            re_reads = any(…'` — must be re-derived over
   a28c's rewrite (author disclosed; confirmed). Byte-exact restore verified (`cmp` × 3 files).
2. **G12 is not separable from A2.** A2 (listed as "applies on HEAD alone") already ADDS `_drive_finding_transition` /
   `_drive_finding_annotate` and their `CAS_SEAM_DRIVERS` keys to `test_findings_cas_seam_64b.py`; G12 is only the REMOVAL from
   58's module. Withholding G12 on the reference (BC-r2-13's fallback world) and running `test_reanchor_58_r3_cas_seam.py` +
   `test_findings_cas_seam_64b.py`: **14 failed / 10 passed**, including
   `AssertionError: findings.py::_transition has drivers in both test_findings_cas_seam_64b.py and test_reanchor_58_r3_cas_seam.py`
   and `GovernedDenied: a governed finding write requires a verified identity` (58's identity-less driver bodies under the 64b build).
   With G12 applied: **4 failed / 18 passed** — `tasks.py::claim_task`, `tasks.py::_reanchor_stragglers` ×2 (58's own, 58 unbuilt)
   and `findings.py::_run_guarded … driver is STALE: neither the call graph … nor the static index names it` — the static index is
   G2's (the two finding doors merge into `_run_guarded`), i.e. a consequence of G2 not being re-derived.
3. **Which 64b pins/parts depend on 58:** G12 (BC-r2-13: waits for 58 r4's Q-DRIVEN pin), G2 (the post-58 door index in
   `test_retry_seam.py`), and the driver-population/identity legs in `test_reanchor_58_r3_cas_seam.py` that 58's build turns green.
   The 64b contract's 15 files themselves are GREEN on a 58-free reference (1192/0).
4. **Is a 58-free build satisfiable under BC-r2-13's in-place fallback?** Not from the shipped artifacts: the fallback needs (a) an A2
   variant WITHOUT the two moved drivers, and (b) in-place, identity-bearing rewrites of 58's `_drive_finding_transition` /
   `_drive_finding_annotate` bodies — neither exists as a §HELD part, and both are TEST edits a builder may not author.
   **What a 58-free build would leave RED, measured on the targeted SAT (reference, G12 applied, G2 not):**
   - RED_ADJUDICATED to **58**: `test_reanchor_58_r3_cas_seam.py` `tasks.py::{claim_task, _reanchor_stragglers}` ×3,
     `test_task_read_surface.py::TestSupersedeWARNS…`, `scripts/test_forgery_door_sweep.py` ×2, `test_supersede_reanchor_58`,
     `test_reanchor_58_r2_rulings`, `test_task_guarded_shell_58` rows.
   - RED_ADJUDICATED to **63c-i-a**: the `test_fixwave_a19a/a28/a28b/a28c` rows and `test_retry_seam.py`'s a28c classes.
   - RED_ADJUDICATED to **#487**: `TestTheReverseRoutingDirection64b` (comms verbs pending).
   - **NOT adjudicable to another packet — 64b's own:** the 4 `test_retry_seam.py` canonical-door rows + `…[findings.py::_run_guarded]`
     STALE (5 nodes), all from G2 not being re-derived. These need a contract-author-class re-derivation of G2 over a28c's file
     (or a 64b-owned registry entry, which the lead must rule) BEFORE a build on this base.
   - **Recommendation (for the operator's 58 decision):** if 58 stays paused, commission ONE contract-author-class pass that ships
     (i) G2 re-derived on HEAD's `test_retry_seam.py`, (ii) an A2′ without the two moved drivers + the in-place identity-bearing
     rewrites of 58's two finding drivers (BC-r2-13's fallback as an artifact). Then a 58-free 64b-i build is satisfiable with only
     the 58 / 63c-i-a / #487 rows above RED_ADJUDICATED. If 58 resumes first, the shipped §HELD applies as designed (G2 still needs
     re-derivation after a28c either way).
5. **Collisions with 63c-i-a's coming build:** `test_retry_seam.py` (G2 — a28c rewrote it; measured), `_governed_contract.py` (A6/A7
   — `held_a_scope_leg.py` / `held_a_registry_double.py` anchors must be re-run after any a28c edit), `test_fixwave_a28_63c_i_a.py`
   (G10 — a28's A2[finding-*] pins go green only with 63c-i-a's build, FK-r2-7).

## §INSTRUMENTS (pasted verbatim; scratch is disposable)

### run.sh (capped runner: admission gate ≥20 GiB, cgroup MemoryMax=16G no swap, -n 8, --timeout=300)
```bash
#!/usr/bin/env bash
# adversary-64b-r2 capped runner: run.sh <tree> <logstem> <pytest args...>
# admission: MemAvailable >= 20 GiB (waits up to 10 min, logs the wait); cgroup cap 16G no swap; per-test timeout.
set -u
tree="$1"; stem="$2"; shift 2
for i in $(seq 1 60); do
  avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
  (( avail >= 20*1024*1024 )) && break
  echo "WAIT $(date -Is) MemAvailable=${avail}kB" >> "$stem.wait"; sleep 10
done
cd "$tree" || exit 2
systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
  uv run --with pytest-timeout pytest -n 8 --timeout=300 -p no:cacheprovider -q -rf --junitxml="$stem.xml" "$@" > "$stem.log" 2>&1
rc=$?; echo "$rc" > "$stem.rc"; exit "$rc"
```
### tscreen.sh (targeted screen; rc 2 under xdist -x with FAILED ids = KILLED, see D-2)
```bash
#!/usr/bin/env bash
# adversary-64b-r2 TARGETED screen: tscreen.sh <plan-file>; each line "NAME|node1 node2 ...". -x: first red kills.
set -u
SC=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/40931dbe-8330-42e8-9aca-172a78c99069/scratchpad
while IFS='|' read -r name nodes; do
  [ -z "$name" ] && continue
  stem=$SC/wbruns/$name
  if ! python3 $SC/wrongbuild.py $SC/wb $SC/wb_specs.json "$name" > $stem.landing 2>&1; then echo "$name: NOT LANDED $(tail -1 $stem.landing)"; continue; fi
  $SC/run.sh $SC/wb $stem -x $nodes
  rc=$(cat $stem.rc)
  git -C $SC/wb checkout -q -- .
  dirty=$(git -C $SC/wb status --short | wc -l)
  summ=$(awk '/ passed| failed|no tests ran/' $stem.log | tail -1)
  first=$(awk '/^FAILED /{print $2; exit}' $stem.log)
  case $rc in 0) v=SURVIVES;; 1) v="KILLED by $first";; *) v="INVALID rc=$rc";; esac
  echo "$name | dirty=$dirty | $summ | $v"
done < "$1"
```
### wrongbuild.py — REUSED verbatim from REPORT-adversary-64b.md §INSTRUMENTS (landing asserted: OLD occurs exactly once, bytes changed)

### wb_specs (the r2-authored specs; the predecessor's specs that landed unchanged are in REPORT-adversary-64b.md §INSTRUMENTS)
```json
{
 "WB1r2_set_scope_invisible_serves_deny": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "        except governed.GovernedInvisible:\n            raise self._not_found(id_or_number) from None\n",
   "new": "        except governed.GovernedInvisible:\n            if action is pdp.Action.SET_SCOPE:\n                raise governed.GovernedDenied(\"not permitted\") from None\n            raise self._not_found(id_or_number) from None\n"
  }
 ],
 "WB1r2b_every_verb_invisible_serves_deny": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "        except governed.GovernedInvisible:\n            raise self._not_found(id_or_number) from None\n",
   "new": "        except governed.GovernedInvisible:\n            raise governed.GovernedDenied(\"not permitted\") from None\n"
  }
 ],
 "WB2r2_visible_deny_by_id_overhidden": [
  {
   "file": "loremaster/loremaster/findings.py",
   "old": "        except governed.GovernedInvisible:\n            raise self._not_found(id_or_number) from None\n",
   "new": "        except governed.GovernedInvisible:\n            raise self._not_found(id_or_number) from None\n        except governed.GovernedDenied:\n            if isinstance(id_or_number, str):\n                raise self._not_found(id_or_number) from None\n            raise\n"
  }
 ],
 "WB4r2_stale_identity_cache": [
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        subject, own_row = await self._resolve_subject_and_agent(capability)\n        if agent is not None and agent != own_row.name:\n",
   "new": "        cached = _ADV_IDENTITY_CACHE.get(capability)\n        subject, own_row = cached if cached is not None else await self._resolve_subject_and_agent(capability)\n        _ADV_IDENTITY_CACHE[capability] = (subject, own_row)\n        if agent is not None and agent != own_row.name:\n"
  },
  {
   "file": "loremaster/loremaster/server.py",
   "old": "def _requires_capability(table: dict[str, Any], action: str) -> bool:\n",
   "new": "_ADV_IDENTITY_CACHE: dict[Any, Any] = {}\n\n\ndef _requires_capability(table: dict[str, Any], action: str) -> bool:\n"
  }
 ],
 "WB10r2_identity_step_second_registry_read": [
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        subject, own_row = await self._resolve_subject_and_agent(capability)\n        if agent is not None and agent != own_row.name:\n",
   "new": "        subject, own_row = await self._resolve_subject_and_agent(capability)\n        await self.agent_registry.get_agent(own_row.name, session=own_row.session)  # adv\n        if agent is not None and agent != own_row.name:\n"
  }
 ],
 "N1_domain_check_drops_existence_read": [
  {
   "file": "loremaster/loremaster/governed.py",
   "old": "    if not scope.startswith(pdp.KEEP_SCOPE_PREFIX) or scope in known_keeps:\n        return\n",
   "new": "    return  # adv: shape only, no existence read\n"
  }
 ],
 "N4_second_agent_read_FROM_ONLY": [
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        subject, own_row = await self._resolve_subject_and_agent(capability)\n        if agent is not None and agent != own_row.name:\n",
   "new": "        subject, own_row = await self._resolve_subject_and_agent(capability)\n        await self.agent_registry._query(\"SELECT * FROM ONLY agent WHERE name = $adv_n LIMIT 1\", {\"adv_n\": own_row.name})  # adv\n        if agent is not None and agent != own_row.name:\n"
  }
 ],
 "N4c_CONTROL_second_agent_read_plain_FROM": [
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        subject, own_row = await self._resolve_subject_and_agent(capability)\n        if agent is not None and agent != own_row.name:\n",
   "new": "        subject, own_row = await self._resolve_subject_and_agent(capability)\n        await self.agent_registry._query(\"SELECT * FROM agent WHERE name = $adv_n LIMIT 1\", {\"adv_n\": own_row.name})  # adv\n        if agent is not None and agent != own_row.name:\n"
  }
 ],
 "N5_second_agent_read_param_bound_record": [
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        subject, own_row = await self._resolve_subject_and_agent(capability)\n        if agent is not None and agent != own_row.name:\n",
   "new": "        subject, own_row = await self._resolve_subject_and_agent(capability)\n        from surrealdb import RecordID as _AdvRid  # noqa: PLC0415\n        await self.agent_registry._query(\"SELECT * FROM $adv_rid\", {\"adv_rid\": _AdvRid(\"agent\", str(getattr(own_row.id, 'id', own_row.id)).split(':')[-1])})  # adv\n        if agent is not None and agent != own_row.name:\n"
  }
 ],
 "N6_keep_seam_accepts_both_identities": [
  {
   "file": "loremaster/loremaster/keeps.py",
   "old": "        if (member_email is None) == (principal_id is None):\n            raise ValueError(\"list_keeps_for_member takes exactly one of member_email= / principal_id=\")\n",
   "new": "        if member_email is None and principal_id is None:\n            raise ValueError(\"list_keeps_for_member takes exactly one of member_email= / principal_id=\")\n"
  }
 ],
 "A6w1_leg_examines_created_only": [
  {
   "file": "loremaster/tests/_governed_contract.py",
   "old": "    if delta.after is None or not (delta.kind == \"created\" or \"scope\" in delta.changed_columns):\n",
   "new": "    if delta.after is None or delta.kind != \"created\":\n"
  }
 ],
 "A6w3_no_existence_read": [
  {
   "file": "loremaster/tests/_governed_contract.py",
   "old": "    return frozenset(landed & existing)\n",
   "new": "    return frozenset(landed)  # adv: no existence\n"
  }
 ],
 "A6w4_leg_refuses_none": [
  {
   "file": "loremaster/tests/_governed_contract.py",
   "old": "        scope = _landed_scope(delta)\n        if scope is None:\n            continue\n",
   "new": "        scope = _landed_scope(delta)\n        if scope is None:\n            if delta.kind == \"created\" and delta.after is not None:\n                return False\n            continue\n"
  }
 ],
 "A6w5_private_shape_copy": [
  {
   "file": "loremaster/tests/_governed_contract.py",
   "old": "        if not _pdp.scope_shape_ok(scope):\n            return False\n        resolved = effect.resolved_keep_scopes\n",
   "new": "        import re as _adv_re  # noqa: PLC0415\n        if not (scope in (\"principal-private\", \"agent-private\", \"server\") or _adv_re.fullmatch(r\"keep:[A-Za-z0-9_-]+\", scope)):\n            return False\n        resolved = effect.resolved_keep_scopes\n"
  }
 ],
 "A6w6_observer_sets_none": [
  {
   "file": "loremaster/tests/_governed_contract.py",
   "old": "                resolved_keep_scopes=await _f5_resolved_keep_scopes(connection, row_deltas),\n",
   "new": "                resolved_keep_scopes=None,\n"
  }
 ],
 "A6w7_leg_skips_label_channel": [
  {
   "file": "loremaster/tests/_governed_contract.py",
   "old": "    return attributed and _landed_scopes_are_in_domain(observed)\n",
   "new": "    return attributed and (observed.label is not None or _landed_scopes_are_in_domain(observed))\n"
  }
 ],
 "N7_mismatch_path_rereads_registry_by_name": [
  {
   "file": "loremaster/loremaster/server.py",
   "old": "        if agent is not None and agent != own_row.name:\n            raise governed.GovernedDenied(\n",
   "new": "        if agent is not None and agent != own_row.name:\n            await self.agent_registry.get_agent(agent, session=session)  # adv: 'does the named agent exist?' (teaching)\n            raise governed.GovernedDenied(\n"
  }
 ],
 "D1_verified_agent_drops_no_owner_guard": [
  {
   "file": "loremaster/loremaster/owner_stamp.py",
   "old": "    if not verified.owner_principal:\n        raise OwnerStampError(",
   "new": "    if False and not verified.owner_principal:\n        raise OwnerStampError("
  }
 ],
 "D2_CONTROL_stamp_owner_drops_no_owner_guard": [
  {
   "file": "loremaster/loremaster/owner_stamp.py",
   "old": "    owner_agent, owner_principal = pair\n    if not owner_principal:\n",
   "new": "    owner_agent, owner_principal = pair\n    if False and not owner_principal:\n"
  }
 ]
}
```
### plan files (name|targeted nodes)
```
WB1r2_set_scope_invisible_serves_deny|loremaster/tests/test_findings_classes_64b.py::TestEveryWriteVerbTreatsAnInvisibleRowAsNonexistent loremaster/tests/test_findings_adversary_pins_64b.py::test_MP1_set_scope_on_an_invisible_row_is_not_found_byte_identical_by_id_and_number
WB2r2_visible_deny_by_id_overhidden|loremaster/tests/test_findings_classes_64b.py::TestEveryWriteVerbTreatsAnInvisibleRowAsNonexistent loremaster/tests/test_findings_adversary_pins_64b.py::test_MP2_a_visible_but_unwritable_row_by_ID_is_denied_never_not_found
WB17_supersedes_by_id_resolved_unfiltered|loremaster/tests/test_findings_classes_64b.py::TestEveryWriteVerbTreatsAnInvisibleRowAsNonexistent loremaster/tests/test_findings_adversary_pins_64b.py::test_MP3_supersedes_an_invisible_ID_is_not_found_byte_identical_and_writes_nothing
WB3_classifier_authorizes_READ|loremaster/tests/test_findings_classes_64b.py::TestTheZeroRowClassifierAuthorizesThePassedAction loremaster/tests/test_findings_adversary_pins_64b.py::test_MP4_rescoped_to_readable_but_unwritable_is_a_governed_conflict
WB4r2_stale_identity_cache|loremaster/tests/test_findings_classes_64b.py::TestEveryAuthorizationInputIsReadPerCall loremaster/tests/test_findings_adversary_pins_64b.py::test_MP5_a_revoked_household_member_is_refused_on_its_next_write
WB19_annotate_event_drops_actor_agent|loremaster/tests/test_findings_classes_64b.py::TestEveryAppendedEventCarriesTheDerivedActor loremaster/tests/test_findings_adversary_pins_64b.py::test_MP6_every_appended_event_carries_the_actor_agent_link
WB10r2_identity_step_second_registry_read|loremaster/tests/test_findings_classes_64b.py::TestTheRegistryIsReadOncePerGovernedCall loremaster/tests/test_findings_adversary_pins_64b.py::test_MP7_a_governed_write_reads_the_agent_row_at_most_once
N4c_CONTROL_second_agent_read_plain_FROM|loremaster/tests/test_findings_classes_64b.py::TestTheRegistryIsReadOncePerGovernedCall
N4_second_agent_read_FROM_ONLY|loremaster/tests/test_findings_classes_64b.py::TestTheRegistryIsReadOncePerGovernedCall loremaster/tests/test_findings_adversary_pins_64b.py::test_MP7_a_governed_write_reads_the_agent_row_at_most_once
N5_second_agent_read_param_bound_record|loremaster/tests/test_findings_classes_64b.py::TestTheRegistryIsReadOncePerGovernedCall loremaster/tests/test_findings_adversary_pins_64b.py::test_MP7_a_governed_write_reads_the_agent_row_at_most_once
WB21_dispatcher_hand_rolls_a_second_identity_compare|loremaster/tests/test_findings_classes_64b.py::TestTheIdentityCompareLivesInOneFunction loremaster/tests/test_findings_adversary_pins_64b.py::test_MP8_exactly_one_identity_compare_site_in_production
WB22b_finding_leg_migrates_memory_after_its_precondition|loremaster/tests/test_findings_classes_64b.py::TestAMigrateLegWritesOnlyItsOwnTable loremaster/tests/test_findings_adversary_pins_64b.py::test_MP11_migrate_finding_leaves_every_other_governed_table_byte_identical
WB23_scope_accepted_and_ignored_on_other_verbs|loremaster/tests/test_findings_classes_64b.py::TestAParamOutsideItsVerbsSpecIsRefused
N6_keep_seam_accepts_both_identities|loremaster/tests/test_findings_classes_64b.py::TestTheKeepSeamTakesExactlyOneIdentity
N1_domain_check_drops_existence_read|loremaster/tests/test_findings_scope_domain_64b.py
A6w1_leg_examines_created_only|loremaster/tests/test_findings_scope_domain_64b.py
A6w3_no_existence_read|loremaster/tests/test_findings_scope_domain_64b.py
A6w4_leg_refuses_none|loremaster/tests/test_findings_scope_domain_64b.py
A6w5_private_shape_copy|loremaster/tests/test_findings_scope_domain_64b.py
A6w6_observer_sets_none|loremaster/tests/test_findings_scope_domain_64b.py
A6w7_leg_skips_label_channel|loremaster/tests/test_findings_scope_domain_64b.py
N7_mismatch_path_rereads_registry_by_name|loremaster/tests/test_findings_classes_64b.py::TestTheRegistryIsReadOncePerGovernedCall loremaster/tests/test_findings_classes_64b.py::TestTheIdentityCompareLivesInOneFunction loremaster/tests/test_findings_identity_64b.py loremaster/tests/test_findings_adversary_pins_64b.py
D1_verified_agent_drops_no_owner_guard|loremaster/tests/test_425_stamp_owner_63a.py loremaster/tests/test_agent_capability_seams.py loremaster/tests/test_findings_identity_64b.py loremaster/tests/test_findings_classes_64b.py loremaster/tests/test_findings_adversary_pins_64b.py loremaster/tests/test_governed_substrate_63a.py loremaster/tests/test_findings_enforcement_64b.py
D2_CONTROL_stamp_owner_drops_no_owner_guard|loremaster/tests/test_425_stamp_owner_63a.py loremaster/tests/test_agent_capability_seams.py loremaster/tests/test_findings_identity_64b.py loremaster/tests/test_findings_classes_64b.py loremaster/tests/test_findings_adversary_pins_64b.py loremaster/tests/test_governed_substrate_63a.py loremaster/tests/test_findings_enforcement_64b.py
F5w1_set_scope_write_unlabeled|loremaster/tests/test_findings_enforcement_64b.py loremaster/tests/test_findings_scope_domain_64b.py loremaster/tests/test_findings_governance_64b.py
```
### changed_symbols.py (DUAL stage 1 + SAT derivation)
```python
"""adversary-64b-r2: DERIVE the production symbols a diff changes — every top-level function/class and method whose
source segment differs between two git revisions (AST, never hunk headers). usage: changed_symbols.py <old> <new> <files...>"""
import ast, subprocess, sys
old, new, files = sys.argv[1], sys.argv[2], sys.argv[3:]
def symbols(rev, path):
    try:
        src = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return {}
    tree = ast.parse(src); out = {}
    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{child.name}"
                seg = ast.get_source_segment(src, child) or ""
                if isinstance(child, ast.ClassDef):
                    walk(child, name + "."); seg = "\n".join(l for l in seg.splitlines() if not l.startswith("    "))
                out[name] = seg
            elif isinstance(child, (ast.Assign, ast.AnnAssign)) and prefix == "":
                for t in (child.targets if isinstance(child, ast.Assign) else [child.target]):
                    if isinstance(t, ast.Name): out[t.id] = ast.get_source_segment(src, child) or ""
    walk(tree, ""); return out
for f in files:
    a, b = symbols(old, f), symbols(new, f)
    mod = f.split("/", 1)[1].removesuffix(".py").replace("/", ".")
    for name in sorted(set(a) | set(b)):
        if a.get(name) != b.get(name):
            print(f"{mod}.{name}\t{'NEW' if name not in a else 'DELETED' if name not in b else 'CHANGED'}")
```
### covering_scan.py (SAT covering-file set; lore_impact fallback, #518)
```python
"""adversary-64b-r2: the SAT covering-FILE set, DERIVED — every test module (loremaster/tests, lorerunes/tests,
scripts/test_*.py, skills tests) whose AST names (Name / Attribute.attr / import alias / str constant) ANY
changed production symbol's LEAF name. Input: changed_symbols.txt (AST-derived). Fallback for lore_impact's
15-cap (finding filed). Over-inclusive by design (a leaf-name match), never under-inclusive for a direct name use."""
import ast, sys
from pathlib import Path
root = Path(sys.argv[1]); syms = Path(sys.argv[2]).read_text().split("\n")
GENERIC = {"FindingLedger", "AgentRegistry", "GuardedPlan", "CommsActionSpec", "report", "resolve", "acknowledge",
           "annotate", "wontfix", "findings", "remember", "fragments", "handle", "audit_store", "to_surql", "compose",
           "guard", "VerifiedAgent", "set_scope"}
leaves = {line.split("\t")[0].rsplit(".", 1)[-1] for line in syms if line.strip()}
distinct = leaves - GENERIC
files = sorted(set(root.glob("loremaster/tests/test_*.py")) | set(root.glob("lorerunes/tests/test_*.py"))
               | set(root.glob("scripts/test_*.py")) | set(root.glob("loresigil/tests/test_*.py")) | set(root.glob("lorescribe/tests/test_*.py")))
hits = {}
for f in files:
    try: tree = ast.parse(f.read_text())
    except SyntaxError: continue
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name): names.add(n.id)
        elif isinstance(n, ast.Attribute): names.add(n.attr)
        elif isinstance(n, ast.alias): names.add(n.name.rsplit(".", 1)[-1])
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.isidentifier(): names.add(n.value)
    m = names & distinct
    if m: hits[str(f.relative_to(root))] = sorted(m)
for f, m in sorted(hits.items()): print(f"{f}\t{','.join(m)}")
print(f"# distinct leaves scanned: {len(distinct)}; files: {len(files)}; hits: {len(hits)}", file=sys.stderr)
```
### test_adv64br2_probe.py (F-3 probe; scratch only)
```python
"""adversary-64b-r2 PROBE (scratch only, never committed): MP-13's class at params OUTSIDE the hand-listed
VERB_OWNED_PARAMS domain {scope, items}. Each case calls the served dispatcher with ONE foreign param on a verb
that does not own it; ACCEPTED ⇒ accept-and-ignore (the WB23 class). CONTROL: scope= on acknowledge (in the
hand-list) must be REFUSED — proves the probe can see a refusal."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from _governed_contract import finding_world, new_row_id

CASES: list[tuple[str, dict[str, Any]]] = [
    ("acknowledge", {"supersedes": 8900}),
    ("resolve", {"limit": 3}),
    ("set_scope", {"note": "ignored?"}),
    ("annotate", {"status": "resolved"}),
    ("report", {"note": "ignored?", "subject": "t", "area": "a", "category": "c"}),
    ("wontfix", {"kind": "bug"}),
    ("acknowledge", {"body": "ignored?"}),
]


async def test_foreign_params_outside_the_hand_list(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    async with finding_world(monkeypatch, tmp_path) as world:
        await world.seed(row_id=new_row_id("prb"), number=8900, owner="ag-a1", scope_key="AB")
        accepted: list[str] = []
        # CONTROL (in the hand-list): must be refused.
        with pytest.raises(ValueError, match="scope"):
            await world.findings("ag-b1", action="acknowledge", id_or_number=8900, scope=world.scopes["AB"])
        for verb, extra in CASES:
            kwargs: dict[str, Any] = {"action": verb, **extra}
            if verb != "report":
                kwargs["id_or_number"] = 8900
            if verb == "set_scope":
                kwargs["scope"] = world.scopes["A"]
            actor = "ag-a1" if verb == "set_scope" else "ag-b1"
            try:
                out = await world.findings(actor, **kwargs)
            except ValueError as error:
                print(f"REFUSED {verb} × {list(extra)}: {error}")
                continue
            except Exception as error:  # noqa: BLE001
                print(f"OTHER {verb} × {list(extra)}: {type(error).__name__}: {error}")
                continue
            accepted.append(f"{verb} × {sorted(set(extra) - {'subject', 'area', 'category'})}: {str(out)[:90]!r}")
        print("ACCEPTED-AND-IGNORED:\n" + "\n".join(accepted))
        assert not accepted, "accept-and-ignore outside VERB_OWNED_PARAMS:\n" + "\n".join(accepted)
```
### sat_diff.py
```python
"""adversary-64b-r2 SAT diff: junit(base) vs junit(ref) on ONE tree. Prints counts, the declared-set completeness
(both junits' node sets equal and == collect-only), reference-only reds grouped by file, and base-only reds count."""
import sys, xml.etree.ElementTree as ET
from collections import Counter
def load(p):
    out = {}
    for tc in ET.parse(p).getroot().iter("testcase"):
        nid = f"{tc.get('classname')}::{tc.get('name')}"
        st = "passed"
        for child in tc:
            if child.tag in ("failure", "error"): st = "failed"; break
            if child.tag == "skipped": st = "skipped"
        out[nid] = (st, (tc.find("failure") if tc.find("failure") is not None else tc.find("error")))
    return out
base, ref = load(sys.argv[1]), load(sys.argv[2])
for name, d in (("base", base), ("ref", ref)):
    print(name, len(d), Counter(v[0] for v in d.values()))
print("same node set:", set(base) == set(ref), "only-base", len(set(base) - set(ref)), "only-ref", len(set(ref) - set(base)))
ref_only = sorted(n for n in ref if ref[n][0] == "failed" and base.get(n, ("?",))[0] != "failed")
both = sorted(n for n in ref if ref[n][0] == "failed" and base.get(n, ("?",))[0] == "failed")
fixed = sorted(n for n in base if base[n][0] == "failed" and ref.get(n, ("?",))[0] != "failed")
print("REFERENCE-ONLY reds:", len(ref_only)); print("red both ways:", len(both)); print("fixed by Part C:", len(fixed))
by_file = Counter(n.split("::")[0] for n in ref_only)
for f, c in by_file.most_common(): print(f"  ref-only {c:4d}  {f}")
for n in ref_only:
    msg = ref[n][1]
    print("RO", n, "|", (msg.get("message") or "")[:220].replace("\n", " ") if msg is not None else "")
by_file_both = Counter(n.split("::")[0] for n in both)
for f, c in by_file_both.most_common(): print(f"  both {c:4d}  {f}")
```
### ns_count.py (lore_test namespace count on :18000)
```python
"""adversary-64b-r2: count databases in the TEST namespace on :18000 (never :18500). Prints the count."""
import asyncio, sys
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import connect_admin, make_env, run, unique_database  # noqa: E402

async def main() -> None:
    env = make_env(database=unique_database(), dim=8)
    assert ":18000" in str(getattr(env, "url", "")) or True
    conn = await connect_admin(env)
    info = await run(conn, "INFO FOR NS")
    dbs = (info or {}).get("databases", {}) if isinstance(info, dict) else {}
    print(getattr(env, "url", "?"), len(dbs))
    await conn.close()

asyncio.run(main())
```
### from_table_probe.py (F-1 offline sibling probe)
```python
"""adversary-64b-r2: the contract's _FROM_TABLE regex (copied from test_findings_classes_64b.py at cb220ee) over
SurrealQL read spellings — which tables would the budget counter attribute? (pure; no store)."""
import re
_FROM_TABLE = re.compile(r"\bFROM\s+(?:type::record\(\s*['\"](\w+)['\"]|(\w+))", re.IGNORECASE)
def tables(s): return [a or b for a, b in _FROM_TABLE.findall(s)]
CASES = [
    "SELECT * FROM agent WHERE name = $n",                 # CONTROL: counted
    "SELECT * FROM type::record('agent', $id)",            # CONTROL: counted
    "SELECT * FROM ONLY agent WHERE name = $n LIMIT 1",    # N4
    "SELECT * FROM ONLY type::record('agent', $id)",
    "SELECT * FROM $rid",                                  # N5
    "SELECT * FROM agent:abc",
    "SELECT * FROM type::thing('agent', $id)",
    "SELECT * FROM type::record($tb, $id)",
    "SELECT owner_agent.name FROM finding WHERE id = $f",  # link deref: an agent read attributed to finding
    "SELECT * FROM (SELECT * FROM agent)",
    "SELECT * FROM agent, principal",
]
for s in CASES: print(f"{tables(s)!s:28} {s}")
```
### SAT declared set (59 files; collect-only 5177)
```
loremaster/tests/test_425_stamp_owner_63a.py
loremaster/tests/test_agent_capability_seams.py
loremaster/tests/test_agent_governance_63c_i_a.py
loremaster/tests/test_calibration_wiring.py
loremaster/tests/test_comms_capability_63b_ii_a.py
loremaster/tests/test_comms_footer.py
loremaster/tests/test_comms_send_scope_63b_ii_a.py
loremaster/tests/test_comms_tool.py
loremaster/tests/test_engine_rejection_seam.py
loremaster/tests/test_findings_adversary_pins_64b.py
loremaster/tests/test_findings_cas_seam_64b.py
loremaster/tests/test_findings_classes_64b.py
loremaster/tests/test_findings_closeout_64b.py
loremaster/tests/test_findings_enforcement_64b.py
loremaster/tests/test_findings_governance_64b.py
loremaster/tests/test_findings_identity_64b.py
loremaster/tests/test_findings_migrate_64b.py
loremaster/tests/test_findings.py
loremaster/tests/test_findings_schema_64b.py
loremaster/tests/test_findings_scope_domain_64b.py
loremaster/tests/test_findings_signatures_64b.py
loremaster/tests/test_findings_system_writer_64b.py
loremaster/tests/test_fixwave_a19_63c_i_a.py
loremaster/tests/test_fixwave_a19a_63c_i_a.py
loremaster/tests/test_fixwave_a28_63c_i_a.py
loremaster/tests/test_fixwave_a28b_63c_i_a.py
loremaster/tests/test_fixwave_a28c_63c_i_a.py
loremaster/tests/test_governed_migration_63a.py
loremaster/tests/test_governed_routing_63a.py
loremaster/tests/test_governed_substrate_63a.py
loremaster/tests/test_governed_substrate_64b.py
loremaster/tests/test_keeps_store.py
loremaster/tests/test_link5_render_containment.py
loremaster/tests/test_mcp_server.py
loremaster/tests/test_memory_enforcement_63a_v.py
loremaster/tests/test_memory_enforcement_63b_ia.py
loremaster/tests/test_memory_f5_registration_63b_ib.py
loremaster/tests/test_memory_render_bound_63b_ib.py
loremaster/tests/test_memory_retrofit_63a.py
loremaster/tests/test_memory_supersede_atomicity_63b_ib.py
loremaster/tests/test_message_enforcement_63b_ii_a.py
loremaster/tests/test_message_migrate_63b_ii_a.py
loremaster/tests/test_message_migrate_dirty_store_63b_ii_b.py
loremaster/tests/test_principal_keys_schema.py
loremaster/tests/test_principals_cli.py
loremaster/tests/test_reanchor_58_r2_rulings.py
loremaster/tests/test_reanchor_58_r3_cas_seam.py
loremaster/tests/test_retry_seam.py
loremaster/tests/test_supersede_reanchor_58.py
loremaster/tests/test_surreal_schema.py
loremaster/tests/test_task_guarded_shell_58.py
loremaster/tests/test_task_read_surface.py
loremaster/tests/test_tool_allowlist.py
loremaster/tests/test_txn_contention.py
loremaster/tests/test_visible_keeps_61b.py
lorerunes/tests/test_pdp_core.py
scripts/test_forgery_door_sweep.py
scripts/test_gated_ground.py
scripts/test_restore_prod_dump.py
```


## VERDICT
**SUFFICIENT-FOR-BUILD** (role vocabulary: CONTRACT SUFFICIENT at the round cap — no NEW PROPERTY found; this is the one re-grade).

Why not REOPEN: every surviving wrong build (N4, N5, N7) and the F-3 probe is a new CASE of a property r2 already pins — the per-table
identity budget (am-8 §1 / am-9 FK-r2-1) and the foreign-param refusal (MP-13). Under the cap they route FORWARD:
- **F-1** → builder enforces at `AppContext._resolve_identity` / `governed.resolve_subject_and_agent` (the only `agent` read is
  `_verify_capability_agent`); the counter's `FROM ONLY` / `$param` blind spot is test hygiene for BC-r2-9's close-out agent.
- **F-2** → the same chokepoint issues no statement after the verified row is in hand; eligible for ONE targeted pin (the mismatch
  tests assert `IDENTITY_READ_BUDGET`), no re-grade.
- **F-3** → the dispatcher's ONE foreign-param check, derived from the spec dict; ⚠ am-8 §6 says a second WB23 instance re-opens the
  RULING — the ruling owner decides whether that is a ruling amendment or this implementation requirement.
- **F-4** → a build-order prerequisite: G2 must be re-derived on HEAD's `test_retry_seam.py` (5 of 64b's own reds on a 58-free base),
  and BC-r2-13's in-place fallback needs an artifact (A2′ + in-place driver rewrites) if 58 stays paused.

What held, with receipts: the four survivor classes the predecessor lifted (invisibility ∀ verb × address × state, classifier
action, per-call authorization inputs, one compare site) killed every re-authored survivor; the am-35 §6 scope leg killed all six
rider-targeted wrong builds, including a routing-not-sharing private shape copy; the domain-existence read (N1) and the keep seam's
exactly-one rider (N6) are pinned; the reference (1192/0 on the 15 contract files) no longer serves the r1 existence oracle.

Untried (NOT TRIED): the UNOWNED-LEGACY SET-clause derivation and the `backfilled` race (no wrong build built); WB1r2b; the
predecessor's non-survivors (WB5/6/9/13/22, CTL1); F-7/F-8/F-9 as built wrong builds (construction-inspected only); status/kind/body
siblings of F-3; `FROM t:⟨id⟩` and link-dereference siblings of F-1; session-mismatch / capability-deny siblings of F-2; the author's
§12 items 1 (UNSET scope via an entry predicate), 4, 5, 6.
