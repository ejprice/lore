# REPORT-lead-04b2-wavec-r2 — the RESUME lead's orchestration log, packet 04b-2 wave C

lead-base v1 read
brief project v7 read

Resume of `REPORT-lead-04b2-wavec.md` (§L-1..§L-6, still standing). §L-6 is the entry point.
This file carries THIS session's rulings, sequencing, and acceptance. Both archive to
`docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/` at close-out.

Written against `feat/surreal-unification` @ `379c2c5` (HEAD at resume).

## SUMMARY BLOCK (running — fields fill as the wave proceeds)

| field | value |
|---|---|
| `Verdicts acted on:` | §L-6 written at `0d24c12`; `git merge-base --is-ancestor 0d24c12 379c2c5` = SAME (ancestor). Not STALE. C-DEF retraction (`c131686`/`8b0933d`) landed; not resurrected. |
| `Directives:` | 0 ledger / 0 wake / 0 prose-duplicated (spawns carry full briefs via the Agent prompt, the guaranteed-read channel) |
| `Rulings:` | 0 body-only (this file is the artifact) |
| `Agents:` | 3 spawned (sidecar-r2, builder-c3-2, cdef-1) / 0 ledger-retired / sidecar standing-by · builder-c3-2 done · cdef-1 running |
| `Uncommitted at stop:` | 0 (tree clean at resume) |

## R2-1 · RESUME ENTRY — state verified, not inherited

- lore-lore, spike-surreal, lore-surreal all UP (podman ps). lore index fresh, watched
  branch `feat/surreal-unification` @ `379c2c5`.
- HEAD `379c2c5` is a descendant of `0d24c12` (§L-6's base) — the C-DEF-retraction and
  builder-final-report commits are landed. §L-6's state table is current.
- **Operator request handled: pushed `feat/surreal-unification` to origin** (`5a850c3..379c2c5`,
  ~24 commits). Tree was clean; all wave work committed.
- **Ground-truthed the built state of C3** (grep at HEAD, not the builder's stale §8):
  COMMITTED — `COMMS_FOOTER_PREFIX`, `AppContext._comms_footer`, `messages.py`
  `PendingTraffic`/`pending_traffic`/`pends`, `#219`'s four prose sites + link-4 fenced
  refusal, `R-5` (`MessageLedgerError` in `.comms` Raises:), the partition fix
  (`TASK_READ_ACTIONS = ("query","rollup","get","blockers")`). UNBUILT — dispatcher wiring,
  link 1b call sites, `agent=`/`session=` params + `@mcp.tool` registrations, `_INSTRUCTIONS`,
  MP-6. Matches builder §6.3.
- C3 contract collected count re-derived: **225 collected** (matches brief).

## R2-2 · ORPHAN PROCESS FROM A DEAD SESSION — flagged, not cleared

`adversary-c3-delta-1` (pid 1758364, ~2.25h, parent session `4d471ed8` — NOT mine) is still
running. Its delta audit is committed (`b40e84d`) and superseded by the C-DEF retraction; it
is inert debris (§L-6: prior-session fleet does not survive). My `kill` was blocked by the
auto-mode classifier. Risk is low (tree clean; modern probes use `scratch_copy.sh` copies, not
the real tree; its session is dead so nothing drives it to wake). Flagged to the operator
(`! kill 1758364` to clear). Proceeding — it will not interfere with the builder.

## R2-3 · SEQUENCE STARTED

1. **Fable design sidecar spawned** — `design-sidecar-04b2-wavec-r2` (general-purpose on fable,
   long-running). Front-loaded with B3's attribution leak (the one genuinely-open item from
   §L-6): `owner=`/`actor=`/`created_by=` are free text (un-refusable by link 1b) but reach the
   dispatcher's own render; `lore_claim_task(owner=HOSTILE)` served a forgery verbatim. Asked
   under the Consumer Law: does link 4 extend, through what seam, this-wave-or-04b-3, and the
   DERIVED surface predicate. It will persist to `REPORT-design-sidecar-04b2-wavec-r2.md` + send
   a ledger pointer.
2. **`builder-c3-2` spawned** (Opus) to finish C3 against the FROZEN committed contract. B3 is
   NOT in that contract (the author escalated rather than extending), so the builder is
   independent of B3's routing — whatever the sidecar rules, B3 is a follow-on packet or a
   separate new contract slice, never a correction to this builder. Brief points at the derived
   design (builder-c3-1 §4c/§6.3/§7; c3fix §5.2/§7; sidecar Ruling 10/8/5.3). Reference build
   withheld (builder ≠ grader).

## R2-4 · RULING 11 (sidecar, B3 attribution leak) — ADOPTED; routed 04b-3; four riders owed

The sidecar re-measured (did not relay) and the door is WIDER than B3 reported: **six free-text
render doors leak**, all with clean controls, **all green under the existing render-injection
oracle** (`assert_render_injection_safe` checks control-chars + row-shape only — blind to
same-line instruction forgery, and its docstring reads as completeness). **Two doors are MINTED
THIS WAVE** by C1's `_render_task_detail` (`action=get`, `0ff05ed`); the `repr` teaching Ruling 10
forbade by name is live at 8 tasks.py sites. Sidecar graded `1486cb2` = HEAD (SAME, not stale).

**RULING (adopted under delegation):** Link 4 NAMES the door as a predicate but cannot CLOSE it —
its naming allowance is bought entirely by Link 1b's charset gate, which free text cannot have. The
chain gains **LINK 5**: every caller-supplied string reaching a served answer is EITHER
charset-gated (Link 1b) OR render-contained; the two sets PARTITION the registered string params;
the partition is DERIVED (complement of the Link-0 scan over the inputSchema universe); a param in
neither half is a door. Seam = a NEW inline primitive `render.render_attributed` (composes
`sanitise_line` + `render_fenced`'s width rule; second consumer of Ruling 9's `sanitise.fence_width`)
— NOT `sanitise_line` (control-char policy, 122 accidental sites) and NOT `render_fenced`
(line-structural, destroys inline rows).

**ROUTING: the FIX is 04b-3-or-later, ONE indivisible, all-or-nothing slice** — recommended as
04b-3's FIRST slice ahead of C2/#309. Decisive reason is CONSUMER LAW, not cost: a partial
containment MANUFACTURES a false clear on every surface it skips (the delimiter becomes a trust
signal the consumer then applies to bare renders). I adopt this; it is sound.

**Builder-c3-2 is UNAFFECTED** — Ruling 11 explicitly forbids touching attribution renders this
wave; the builder's scope is footer/identity-params only. No correction sent to the busy builder.

**Four riders land THIS WAVE (§11.6), all cheap, minting nothing:**
1. asserted-bound pin (#137/#138 shape) — RED the day someone closes the hole — **OWED (post-builder)**
2. retire `assert_render_injection_safe`'s over-claim docstring + `TestRenderInjectionRegistry` — **OWED (post-builder)**
3. `_render_task_detail`'s archetype docstring ("BODY fenced, trailers SANITISED" instructs cloning
   a shape with a measured hole — #102) — amend to state what SANITISED does NOT buy — **OWED (post-builder; server.py single-writer)**
4. file the finding with the derivation — **DONE: finding #321.**
Riders 1-3 sequenced AFTER `builder-c3-2` lands (rider 3 edits server.py; single-writer discipline).
Adversary note: rider 1 is a bound pin on a SEPARATE attribution surface, not a C3-contract edit —
it does not move the contract `builder-c3-2` builds against.

**§11.7 item 2** (Ruling 10 Link 4 amended in scope, not overturned) — the sidecar did not re-read
every c3fix pin; it asserts none is invalidated because C3's Link-4 legs are all identity-param.
I will spot-verify after the build. Low risk.

**§11.7 item 1 — OPERATOR DECISION, surfaced (not mine):** a measured prompt-injection vector ships
with this deploy KNOWINGLY, and the deploy WIDENS its reach (`action=get`'s detail render + two new
repr consumers). Pre-existing (production has served the class since before this packet), so the
sidecar's routing defers it whole to 04b-3 with the bound pinned. But if the operator judges the
widened exposure unacceptable before deploy, that is a packet-sized scope grant and **the deploy
waits** — it cannot be bought as a rider (§11.4). Recommendation: accept-with-bound-pinned (routing
is sound; the C3 build + cold audit proceed regardless, only the deploy gate turns on this). To be
formally confirmed at the deploy gate with full context.

## R2-5 · C3 BUILD ACCEPTED (`46a5933`); the C-DEF is REAL and routed contract-side

`builder-c3-2` reported C3 BUILT: 217 passed / 8 failed of 225. Verified, not relayed:
- **Random receipt re-run (lead):** `test_comms_footer.py` → 217 passed / 8 failed, reproduced
  exactly. The build is solid — good ONE-IMPLEMENTATION discipline (`_is_comms_charset_legal`
  extracted, not cloned; MP-6 serves the registry's OWN classification; footer at a single exit;
  counts CALLED). Mutation proofs honest (MP-B's prediction-miss reported as a miss, exit 4, not
  re-declared — #194/#196 respected).
- **Deviations reviewed + RATIFIED (judgment read on the diffs):** (1) `test_query_tasks_bounded.py`
  `_tool_seam` — the SECOND copy of the seam the ruled R-4 co-edit missed (#102 in a fixture);
  mirrored the ruled fix verbatim (empty fakes, not a missing-service guard). (2)
  `test_comms_promise_registry.py` — three new served literals classified through the file's
  designed deny-by-default workflow + a `PromiseProof` whose NO-EMIT leg is the fallback render
  (catches W21). Both are build-necessitated and correct.
- **Currency gate (builder-run):** 202 C3 orphans → 8, ZERO non-C3 orphans repo-wide, ruff green.
- Build committed `46a5933`; report `cbe1982`.

**THE C-DEF — VERIFIED REAL (not a repeat of the stale-base false C-DEF).** Read
`_task_action_kwargs` at HEAD: it seeds create/create_many/transition/supersede/rollup and falls
through to `return {}` for the NEW `get`/`blockers` read actions, so `_require_arg` raises before
any footer decision. The 8 pins are un-drivable on ANY build — a satisfiability/fixture defect, not
a build defect. It is CONTRACT-side (`test_comms_footer.py`, builder's do-not-touch) — routed to a
fresh contract agent `contract-04b2-cdef-1`, NOT the builder (independence: the fixture that grades
the build cannot be authored by the build's author). The fix-agent must PROVE the 8 pins pass AND
still discriminate (mutation non-vacuity), and settle the `blockers`/`transitive_blockers` backend
question (that method lives only on the real `TaskLedger`, not the fakes).

**Residuals carried to the cold audit / close-out (builder §9, committed):** §4.4 link-2
name-mismatch serves SILENCE (I accept the builder's reading A — teaching a false claim about a
misbehaving registry would be worse); §4.1/§9.5 the branch-chain-in-dispatcher constraint is
undefended for `findings` (no structural scan — a future extraction goes undetected); §9.6
`create_many` write-count rides a docstring atomicity claim not empirically proven; §9.8
`_validate_comms_identities` gained defaults for name/to (surface widening). None blocking; the
cold audit scrutinises them.

## NEXT (not started)
- Collect sidecar B3 ruling → route (this-wave contract slice vs 04b-3).
- Collect `builder-c3-2` receipt → verify (currency gate to zero, seam suites, mutation proof).
- COLD AUDIT (fresh context, re-runs gates). Do not rush — 42 wrong builds passed contracts
  that had passed their own satisfiability receipts this wave.
- DEPLOY — ASK THE OPERATOR AGAIN (shape changed: gate instrument + CLAUDE.md manifest
  inversion + new served `action=get`). Sequence per §L-6 RESUME step 4.
- CLOSE-OUT — INDEX row + Log, ~12 ledger resolves, archive REPORT-*.md by `git mv`, rescue
  the mutation driver from scratch into `scripts/`, dispose the four C3/C1 scratch trees.
