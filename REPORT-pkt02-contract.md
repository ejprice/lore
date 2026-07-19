brief-base v4 read

# REPORT — pkt02-contract (packet 02, comms render architecture)

## SUMMARY BLOCK (read first)

- **state:** done-with-deviations (RED contract authored + satisfiability-proven; ONE structured deferral flagged; a SIZING split recommended).
- **commit:** the single RED-contract commit on `feat/surreal-unification` (this report ships inside it; `git log -1` is it — hash relayed to the lead).
- **provenance receipt (#140 law):** the scratch reference build ran in the REAL tree — `loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (editable install; in-place edits exercised directly; production files then restored byte-exact — checksums in `scratchpad/pkt02/ref_backup/CHECKSUMS.txt`).

### Per-finding pin inventory (one line each)
- **#104 (root cause) — name the ROLE:** `TestStandingBriefIsOneSharedRole` (4 tests, one per surface) — mutation-proves all four standing-brief surfaces route through ONE `server.STANDING_BRIEF` (monkeypatch it → each surface must follow; a half-DRY build reds the precise surface).
- **#104 — TYPE the applicability:** `TestFirstVersionTailIsTypedNotNameDerived` — render takes `auto_ack_at_register: bool`; DISCRIMINATORS (name='project'+flag=False → brief_ack tail; name='wave9'+flag=True → register tail) red any build that compares the name.
- **#104 — structural:** `TestRendersNeverNameTheStandingBriefConstant` — no `_render_comms_*` helper may REFERENCE `BRIEF_NAME_PROJECT`/`STANDING_BRIEF` (AST scan; catches the `== BRIEF_NAME_PROJECT` at server.py:4936; coverage-checked).
- **#104 — kill the monoculture:** `_brief()` loses its `name` default (finding #104 part 3); every call site chooses; the new module's `_brief` has no default by construction.
- **#103 — three skew tails:** `TestSkewTailIsNameConditioned` — the ∀-quantifier pin over (is-standing, has-unbriefed), each fate forced; DISCRIMINATOR (name='project'+flag=False+unbriefed → tail 3) reds a name-keyed build.
- **#103 — heartbeat subscribed skew:** `TestHeartbeatSurfacesSubscribedNameSkew` — end-to-end (surfaces w/ explicit `name=` teach; UNSUBSCRIBED never nagged; project-unbriefed still noticed; the ninth's promise true end-to-end).
- **#100 — remove created_by:** `TestCreatedByIsGoneFromTheDispatcher` — signature pin + author==acting-agent.
- **fleet rename:** `TestFleetCellIsLabelledProject` — `project v…`/`project unbriefed` byte pins + bare anchor-free dead-name scan (`brief v`/`brief unbriefed` absent).
- **#101:** GREEN (fixed-by-4c2efbf) — 3/3 pass under full `-n auto --dist load`; the autouse `_restore_lore_logger_propagation` fixture is mutation-proven by `test_caplog_isolation.py`'s subprocess driver (removing the fixture reds it). NO new pin added; #101 resolves as fixed-by-4c2efbf.
- **promise instrument (E):** `test_comms_promise_registry.py` — allowlist-the-safe AST completeness guard (every comms render literal classified with its predicate or declared promise-free; default-FAIL; coverage-checked) + self-attack (catches an unregistered promise; positive control passes). 8 pins.

### RED-for-right-reason (against CURRENT/defective code — verified)
| pin | red? | reason |
|---|---|---|
| TestFirstVersionTailIsTypedNotNameDerived (×4) | RED | `TypeError: unexpected kwarg 'auto_ack_at_register'` — refactor pin; GREEN on reference (25/25). |
| TestSkewTailIsNameConditioned (×5) | RED | same TypeError; GREEN on reference. |
| TestStandingBriefIsOneSharedRole (×4) | RED (assertion) | each surface hardcodes 'project'; the role isn't centralised (e.g. register renders "no 'project' brief" instead of the 'governance' role brief). |
| TestHeartbeatSurfacesSubscribedNameSkew::subscribed / ninth | RED (assertion) | handler reads only 'project' skew (`'heartbeat author — status active'`). |
| ...::unsubscribed / project_unbriefed | GREEN (guard-rail) | current already doesn't nag / still notices — pins the invariant against a naive generalization. |
| TestRendersNeverNameTheStandingBriefConstant::no_render_ref | RED (assertion) | offender `_render_comms_brief_publish:4936`. |
| ...::scanner_reaches | GREEN (coverage check) | non-vacuity. |
| TestCreatedByIsGone::signature | RED (assertion) | `created_by` present at server.py:4361. |
| ...::publish_records_acting_agent | GREEN (guard-rail) | fallback already uses agent_row.name. |
| TestFleetCellIsLabelledProject (×4) | RED (assertion) | cell says `brief v…`, not `project v…`. |
| test_comms_promise_registry::* | mostly GREEN on both | completeness INVARIANT (self-attacked); `test_no_dead_registry_entries` is RED on current (tail-3/subscribed/collapse literals not emitted yet → the new lines must be added). |

### Satisfiability receipt (the CRITICAL check — C-DEF law)
Built a focused SCRATCH REFERENCE in the real tree (server.py/briefs.py/_comms_fakes.py — provenance `loremaster.__file__` asserted inside the real editable install), ran, then restored byte-exact.
- **DEFINITIVE run (mine, independent of the migration agent): 617 passed / 0 failed** — the FULL contract (my 2 new modules + the migrated `test_comms_tool.py`/`test_comms_wiring.py`) GREEN against the COMPLETE reference on the live store.
- Each TypeError-red refactor pin's assertion was VERIFIED to discriminate (the two `_render_comms_brief_publish` DISCRIMINATORS pass only because the render reads the flag, not the name). The reference caught TWO of my own test bugs before a builder would (a heartbeat assertion over-keyed on the role NAME where the line's label is byte-stable 'project'; a `_fleet_row` sequencing bug where register-time auto-ack pinned the agent at head) — both fixed.
- **The one PRODUCTION deliverable (Blocker 2, below):** `test_the_full_arc` (the sole wiring test on the REAL ledger) needed a real `BriefLedger.subscribed_name_skew` — I added it to the reference and it went GREEN (2.03s, live store). The validated reference implementation is in §"Reference impl for the builder" — the committed contract does NOT ship it (production is not my writable set); test_the_full_arc PINS it end-to-end.
- Contract RED-on-master (production restored): **132 failed / 485 passed, ZERO collection/import/syntax errors** — all assertion/TypeError reds, right reason (the migrated old-world tests now target the new world; my new pins red as tabled above).

### Promise-instrument SIZING / SPLIT recommendation (the brief's explicit ask)
The packet is scoped ~0.20 wu; the ACTUAL work is ~3–4× that. Evidence: **112 existing tests require old-world→new-world migration**; new production surface = STANDING_BRIEF role + 4-site routing, a NEW `BriefLedger.subscribed_name_skew` ledger method (no existing coverage, needs a store-backed contract), three skew tails, typed applicability, a heartbeat-render restructure, `_HEARTBEAT_SKEW_NAMES_CAP`; plus the promise instrument. **Recommendation to the operator:** re-size or split. The AST completeness-guard CORE is delivered + self-attacked here and FITS. The 02a split = (a) the FULL §9.7 mechanization — per-registry-entry EXECUTABLE-predicate emission proofs beyond the A2/B behavioural pins + the `safe_str(f"…")` literal-text coverage closure (documented residual `_SAFE_STR_LITERAL_RESIDUAL`); (b) the REAL `BriefLedger.subscribed_name_skew` store-backed contract (test_brief_ledger.py) — a distinct new-ledger-method chunk.

### DECISIONS NEEDED (operator)
1. **SIZING:** re-size packet 02 or split to 02/02a as above? (recommend: yes.)
2. **Structured deferral (out-of-authority, named owner/decision-point):** the REAL `BriefLedger.subscribed_name_skew` store-backed contract in `test_brief_ledger.py` is NOT written here — the dispatcher/render half is fully pinned via the FAKE (which IS the ledger-surface spec) + end-to-end behaviour. Owner = builder-with-contract-adversary; decision point = at the contract checkpoint. Fold into packet 02 builder scope, or into 02a? (recommend: builder scope, adversary-graded.)

### SPEC GAPS (STOP-and-flag) — none blocking
Everything pinned is spec-to-implement (spec v8 §5.3/§9.1/§9.2/§9.4/§9.5/§9.6/§9.7). One OBSERVATION (not a gap, no action): the register receipt line `echo in your report: brief project v{version} read` and the bootstrap notice `no 'project' brief published yet` carry the literal word "project" (NOT routed through STANDING_BRIEF) — §9.7 #3 / §1 rule them sound (protocol tokens, coextensive with the standing brief being 'project'). They are classified in the promise registry with that predicate. No change unless the operator ever wants a non-'project' standing brief (the finding rules exactly-one-mandatory-brief a real invariant — out of scope).

---

## DETAIL

### Contract decisions / prescriptions the builder + adversary should review
1. **`STANDING_BRIEF` (briefs.py, = `BRIEF_NAME_PROJECT`)** — the ONE named role. All four standing surfaces (register auto-ack, heartbeat universal skew, fleet project column, publish first-version tail applicability) route through it. Pinned by mutation (`server.STANDING_BRIEF` monkeypatch). The finding recommended this exact form ("a `STANDING_BRIEF` role constant"); prescribing the symbol makes the DRY provable. The builder MAY instead use an accessor, but the mutation pin targets `server.STANDING_BRIEF` — flagged.
2. **`auto_ack_at_register: bool` on `_render_comms_brief_publish`** — governs the first-version tail AND the skew-tail standingness (coextensive with the standing role; both mechanisms are true iff standing). Named per the finding's example + the brief's discriminating-fixture phrasing. The builder MAY split into two flags but must then update the two DISCRIMINATOR fixtures (name≠flag). Flagged.
3. **`_render_comms_heartbeat(..., subscribed_skew)` + `BriefLedger.subscribed_name_skew(*, agent_id, exclude) -> list[tuple[str,int,int]]`** — the subscribed-skew read. The COMMITTED contract pins this via the FAKE (`_comms_fakes.py::FakeBriefLedger.subscribed_name_skew`) + end-to-end behaviour; the fake IS the ledger-surface spec. TUPLE (not a pydantic model) chosen deliberately so the committed contract stays collection-clean (a new imported model would break `_comms_fakes.py`'s module import → the whole comms suite). The builder MAY promote to a named model, updating fake+render together. Flagged.
4. **`_HEARTBEAT_SKEW_NAMES_CAP = 3`** (server.py) — new render cap, §9.2.
5. **Fleet cell label stays the literal word "project"** (§9.6) while TRACKING the standing role — so the heartbeat/fleet mutation proofs key on the VERSIONS the role produces, not the label word (the register leg proves name-following directly, since its render echoes `brief.name`).

### #104 — the two-sided fix, both pinned
- **Handler side (re-derives the ROLE):** the mutation pin (`TestStandingBriefIsOneSharedRole`) — change the role in ONE place, every surface follows; a surface that keeps `== BRIEF_NAME_PROJECT` reds precisely.
- **Render side (re-derives APPLICABILITY):** the typed-flag discriminators + the AST "no render helper names the standing-brief constant" scan. The two converge (handlers stop re-deriving the role; renders stop re-deriving applicability) — the finding's evidence this is the real root cause.

### #103 — three skew tails + subscribed heartbeat skew
Implements spec v8 §9.4 (three name-conditioned tails, one inline literal each, 'project' tails byte-stable) and §9.2 (subscribed-name skew lines, explicit `name=` teach, cap + counted collapse, unsubscribed never nagged). The QUANTIFIER LAW is applied: the tail is pinned ∀ (is-standing, has-unbriefed) with each fate FORCED by a fixture. The ninth's promise is proven END-TO-END where it is made (publish wave9 → the acker's next heartbeat surfaces wave9).

### #100 — removed-behavior inventory (DUAL law)
`created_by` on `AppContext.comms`: **DROPPED-DELIBERATELY.** Was a test-only affordance (finding #100). The `lore_comms` MCP tool wrapper (server.py:7245-7384) never sends it; no production caller passes it (verified). Sole consumer: the publisher-name fallback in `_comms_brief_publish`, now always `agent_row.name`. #98's self-ack already asserts author == acting agent, so no behaviour is lost — the split identity it created (author X vs. self-ack for agent Y) is eliminated. Three test call sites migrated (register+publish AS the intended agent).

### #101 — determination (brief §D)
GREEN under the full-repo `-n auto --dist load` (3/3 named tests pass; run: `scratchpad/pkt02/full_run_101.log`, 4743 passed / 7 unrelated failures — see below). The autouse `_restore_lore_logger_propagation` (conftest.py:82-117, from 4c2efbf) restores lore-logger propagation per test across every module; `test_caplog_isolation.py`'s subprocess driver is the mutation proof (it runs the poison ordered pair with the real conftest loaded → GREEN with the fixture, and would go RED if the fixture were removed, because the nested run's returncode would flip). #101 resolves as fixed-by-4c2efbf; nothing added.

### Promise-string completeness instrument (E) — design + self-attack
`test_comms_promise_registry.py`. Allowlist-the-safe (NOT enumerate-the-forbidden): every `render_line`/`render_join` template literal inside a comms render/handler function must be in `_PROMISE_REGISTRY` (promise + the PREDICATE its mechanism runs under — §9.7's litmus made mechanical) OR `_PROMISE_FREE` (status/label/separator/advice + reason). Default-FAIL. Coverage-checked (`test_the_scan_reached_every_comms_render_helper` — a renamed/removed helper can't make it vacuously pass). Self-attack (`TestTheGuardActuallyCatchesViolations`): a NEW unclassified promise literal is caught; a POSITIVE control (a registered literal) passes; a render_line in a NON-comms function is ignored (a different-reason negative). The "emit IFF predicate" BEHAVIOURAL half lives in `test_comms_render_architecture.py` (the first-version tail + the three skew tails). Documented residual (`_SAFE_STR_LITERAL_RESIDUAL`): a promise smuggled through `safe_str(f"…")` literal text is NOT scanned — the 02a extension.

### Files (writable set: loremaster/tests/** only)
- NEW `loremaster/tests/test_comms_render_architecture.py` — the load-bearing #104/#103/#100 + fleet-rename pins.
- NEW `loremaster/tests/test_comms_promise_registry.py` — the promise-completeness instrument.
- EDIT `loremaster/tests/_comms_fakes.py` — `FakeBriefLedger.subscribed_name_skew` (the ledger-surface spec for #103; unused by current code, exercised by the fix).
- EDIT `loremaster/tests/test_comms_tool.py` + `test_comms_wiring.py` — old-world→new-world migration (render signatures, fleet rename, created_by, `_brief()` monoculture). See the migration section.
- Production files (server.py/briefs.py) were mutated ONLY for the scratch reference and RESTORED byte-exact — they are NOT in the commit.

### Reference impl for the builder — the ONE production deliverable my contract can't ship (Blocker 2)
`test_the_full_arc` (the real-ledger wiring test) needs `BriefLedger.subscribed_name_skew`. The FAKE (`_comms_fakes.py`) is the surface spec; the render/dispatcher half is fully pinned via fakes. This VALIDATED reference implementation (proven green on the live store) de-risks the builder — a per-name generalisation of `acked_version` (a builder should tighten the unbounded `SELECT * FROM brief` to a bounded per-name pair per §9.2, and the contract-adversary should grade it):
```python
async def subscribed_name_skew(self, *, agent_id: str, exclude: str) -> list[tuple[str, int, int]]:
    edge_rows = self._as_rows(await self._query(
        f"SELECT {_COL_EDGE_OUT} FROM {BRIEFED_RELATION} WHERE {_COL_EDGE_IN} = ${_ACKED_IN_PARAM}",
        {_ACKED_IN_PARAM: RecordID(AGENT_TABLE, agent_id)}))
    acked_brief_ids = {self._bare_id(r[_COL_EDGE_OUT]) for r in edge_rows if _COL_EDGE_OUT in r}
    if not acked_brief_ids: return []
    head_by_name, acked_by_name = {}, {}
    for row in self._as_rows(await self._query(f"SELECT * FROM {BRIEF_TABLE}", {})):
        n = str(row[_COL_NAME]);  v = int(row[_COL_VERSION])
        if n == exclude: continue
        head_by_name[n] = max(head_by_name.get(n, 0), v)
        if self._bare_id(row[_ID_KEY]) in acked_brief_ids:
            acked_by_name[n] = max(acked_by_name.get(n, 0), v)
    return [(n, head_by_name[n], a) for n, a in acked_by_name.items() if a < head_by_name[n]]
```

### ⚠ OBSERVED HAZARD (Blocker 1) — production reference edits were reverted to master mid-session
While the migration agent ran (~20 min), something reverted my uncommitted `server.py`/`briefs.py` reference edits back to master (byte-exact; no reflog; test files untouched) — signature of a concurrent `git restore`/`checkout -- loremaster/loremaster/*.py` by another process (a hook, another session, or an editor/linter — unidentified). The migration agent correctly detected it and re-verified in an ISOLATED provenance-asserted `scratch_copy.sh` copy instead of the live tree. Surfaced per the "surface everything" law and the "working tree is never the only copy" rule: it caused no data loss here (the reference lived in `ref_backup/` + the diffs), but a future session mutating an uncommitted production tree on this repo should assume the tree can be reverted underneath it — verify in an isolated copy, or commit first. (For THIS contract it was harmless — production-at-master is exactly the commit state I need.)

### Unrelated failures (operator visibility rule)
The full `-n auto --dist load` baseline run (before any of my edits) showed **7 failures unrelated to packet 02**, all `surrealdb.errors.NotAllowedError: There was a problem with authentication` (an env/auth issue against the store) in `test_extension.py` (5), `test_eager_startup_survives_unparseable_file.py` (1), `test_resilient_db.py` (1). These build a real AppContext and fail store auth; they are outside packet-02 scope and pre-exist my work.
