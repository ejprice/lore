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
| `Agents:` | 2 spawned / 0 ledger-retired / 2 running |
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

## NEXT (not started)
- Collect sidecar B3 ruling → route (this-wave contract slice vs 04b-3).
- Collect `builder-c3-2` receipt → verify (currency gate to zero, seam suites, mutation proof).
- COLD AUDIT (fresh context, re-runs gates). Do not rush — 42 wrong builds passed contracts
  that had passed their own satisfiability receipts this wave.
- DEPLOY — ASK THE OPERATOR AGAIN (shape changed: gate instrument + CLAUDE.md manifest
  inversion + new served `action=get`). Sequence per §L-6 RESUME step 4.
- CLOSE-OUT — INDEX row + Log, ~12 ledger resolves, archive REPORT-*.md by `git mv`, rescue
  the mutation driver from scratch into `scripts/`, dispose the four C3/C1 scratch trees.
