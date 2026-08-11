lead-base v4 read
brief project v7 read

# REPORT-lead-05a-ii — comms `await` verb + Opus-4.8 LIVE leg + deploy the 05a split

## SUMMARY BLOCK
- **Verdicts acted on:** cold-audit delta graded `c1e1b31` (prod-identical to `5466b7b`) → HEAD-then
  `5466b7b` → **SAME** (no STALE acted on; deployed the graded code, image `65e36c8`).
- **Directives:** 0 ledger / ~9 native-to-AT-REST-warm-agent (contract ×3, adversary ×3, builder ×1,
  sidecar ×2 — the sanctioned at-rest / warm-reuse exception; in-process subagents woken + fed via
  SendMessage) / **0 prose-duplicated**. ⚠ REFLECTION: content rode native (not the ledger) because the
  recipients were in-process warm subagents at rest; strict 2026-08-10 hardening prefers ledger-content —
  the at-rest exception justifies it, but a cleaner run would route content through `lore_comms send`.
- **Rulings:** **8 in a committed artifact / 0 body-only** (kickoff F1/F2/Q5(ii)/roster + seam R-1/R-2/R-3
  + R-4 no-reconnect — all in `docs/plans/v2/05-comms-await-story.md`).
- **Agents:** **7 spawned / 9 ledger-retired / 0 left-running** (7 pipeline agents TaskStop-returned dead;
  ledger-retired the 6 registered pipeline agents + 2 smoke identities; the investigator held no ledger
  row — lore was down when it ran, used SendMessage).
- **Uncommitted at stop:** 0 files (after the close-out commit).

## Mission (reconciled scope)
05a-ii = the LAST piece of the 05a wait-surface: the **`await` action** on `lore_comms`, plus
the **Opus-4.8 LIVE receipt leg**, plus the **deploy** that ships the 05a commit-only backlog.

**Scope reconciliation (ground-truthed, NOT a silent narrowing).** The packet-05 spec's Scope IN
enumerates the whole 05a wait surface (await / DD-2.a / DD-4.c / R1 / #183 / #190 / #214 / #304 /
story / rollup / comms_cli). Ground truth (HEAD `83dba44`):
- **05a-i** (`d509980`→`53e28fc`, commit-only) already shipped: drain reshape, `since=` (DD-4.c/#214),
  #183 bound, #190 oracle parity, R1 question marker, and the **DD-2.a waiting-line helper**
  (`MessageLedger.awaiting_answer` → `WaitingOnAnswer`).
- **05a-iii** (image `a04a23ca`, DEPLOYED) already shipped: `story`, rollup messages/fleet/skew,
  `comms_cli`, #304/#332.
- **`await` is genuinely unbuilt** — zero hits in `messages.py`/`scout.py`/`comms_cli.py`; not a
  served `lore_comms` action.
This split is the **operator-adopted** Fable Q1 decomposition
(`receipts/2026-08-08-packet05aiii/REPORT-fable-design-05a.md` §Q1): "05a-ii — AWAIT (the heavy
Opus-4.8 LIVE leg) · `await` snapshot-first, re-uses 05a-i's drain read-only, filtered LIVE-on-edge +
poll fallback, honest empty on timeout, the LIVE-on-edge build probe, the injection pin (Q5(ii)),
and await's timeout render = first consumer of DD-2.a's waiting state." So 05a-ii's scope is the
already-ruled design, not an improvisation.

## Deploy backlog (git delta since the deployed image)
`4fc8b70..HEAD` (= image `a04a23ca`..`83dba44`): 05a-i (`d9b151b`,`d509980`,`53e28fc` + close-out
docs) + the **defect-class prevention wave** (`f49d668` + design/close-out docs) + brief/lead-base
docs. Deploying HEAD after the await build ships all of it. Verify the exact delta again at deploy.

## Design sources (canonical file GONE — reconstruction is sound)
`comms-subsystem.md:11-13` points the await state machine at
`~/.claude/plans/one-of-claude-codes-nifty-garden.md` §"await semantics" — **that file does not
exist** (the resume/plan chain was frozen and removed). The load-bearing await design survives,
reconstructed, in:
- `REPORT-fable-design-05a.md` §Q5 (the operator-consumed Consumer-Law review of await): honest-empty
  render + 3 conditions; injection = agent-id-only LIVE WHERE; timeout render consumes
  `awaiting_answer`; the load-bearing forgery pin.
- `receipts/2026-08-09-packet05ai/REPORT-probe-await-05a-1.md` (the LIVE-on-edge + socket-drop probe
  re-run on the live 3.2.4 engine): LIVE-on-edge FIRES on RELATE (whole-table + filtered
  `WHERE out=<literal>`) → await is LIVE-primary + poll-fallback; socket-drop in-flight →
  `KeyError(request-uuid)` at the SDK-await boundary, next call `ConnectionClosedError`.
- `loremaster/loremaster/scout.py::CommandSubscriber` — the existing LIVE-primary + poll-fallback
  reference shape await mirrors (catches `(*_CONNECTION_ERRORS, KeyError)`).

## Rulings (operator, 2026-08-10 — committed in `docs/plans/v2/05-comms-await-story.md`
§"05a-ii KICKOFF RULINGS", design of record `REPORT-fable-design-05a-ii.md`)
- **F1 — await does NOT stamp (PEEK + wait)**; caller consumes via a later `drain`. `stamped_seqs`
  empty; idempotency pin required. Keeps await off the DD-4.c/#214 loss path.
- **F2 — ≤55s = fixed named constant**, no `timeout=` param (property-pinned, not the magic number).
- **Q5(ii)/F3 — LIVE-WHERE = agent-id-only** (`out = agent:<uuid5-id>`), never `thread`;
  injection-safe by construction; `thread?` filtering is client-side on the snapshot.
- **Roster — Opus-4.8 via `opus48-worker`** (frontmatter pin; no per-invocation model override).

Seam forks (Fable sidecar ruled; lead-ratified 2026-08-10; none operator-level):
- **R-1** — wait-machine = STANDALONE `InboxAwaiter` (not `MessageLedger.await_inbox`); server handler
  constructs+calls+renders. **R-2** — share `_SDK_AWAIT_BOUNDARY_ERRORS=(*_CONNECTION_ERRORS,KeyError)`
  in `store._txn` (await + ≥1 CommandSubscriber site) + cross-suite mutation pin; **SCOPE ADD**: touches
  `scout.py`+`test_scout.py` (operator-surfaced). **R-3** — await non-empty render teaches `action=drain`
  via typed applicability (#104), never the peek re-run; mandatory render pin.

Rulings tally: 7 in a committed artifact / 0 body-only.

## DRY / reuse — operator directive (2026-08-10: "adhere to DRY. Reuse, don't reinvent.")
Reinforces ONE IMPLEMENTATION; enforced structurally (R-1/R-2/R-3) + empirically (adversary attacks
#7/#8/#9 = prove-sharing-by-mutation). **Reuse inventory `InboxAwaiter` MUST call (not clone):**
- `scout._open_command_connection` — the ALREADY-shared connect factory (1 prod/6 test); `InboxAwaiter`'s
  `connect` reuses it, no hand-rolled opener.
- `store._txn.{retry_on_conflict, _CONNECTION_ERRORS, TxnContentionExhaustedError}` + the new R-2
  `_SDK_AWAIT_BOUNDARY_ERRORS`.
- `CommandSubscriber._DEFAULT_BACKOFF_BASE_S/_MAX_BACKOFF_S` (backoff), `drain(peek=True)` (reads),
  `awaiting_answer`/`_comms_waiting_lines` (waiting line), `_render_comms_drain` fence + `render_attributed`.
- **R-2 WIDENED by the directive:** `scout.py` has ~7 inline `(*_CONNECTION_ERRORS, KeyError)` clones
  (L163/350/487/496/570/585/602; 3 are the `+TxnContentionExhaustedError` variant). DRY-complete =
  consolidate ALL onto the shared constant(s) with a REACH-CHECKED pin (AST: no inline clones remain =
  coverage a checked variable), not "≥1 site". Fold into the contract revision after the adversary verdict
  (its attack #7 probes exactly this). Builder brief carries a MANDATORY reuse-audit (name the seam or escalate).

## Remaining operator touchpoints
- Deploy go/no-go before the recreate (brief-directed; this deploy ships the 05a-i + defect-class backlog).
- The live-leg mechanism is settled (opus48-worker); the live receipt itself is a deploy-gated smoke.

## Log (chronological)
- Boot: read lead-base v4, CLAUDE.md (loaded), INDEX row-05 + Log tail, packet-05 spec §SPLIT,
  comms-subsystem.md, the 05a Fable design doc, the 05a-i await probe. Recalled #333 baseline,
  lore-lore mount, surreal systemd, Opus-4.8 mechanism. `lore_index()` fresh (watching /workspace
  @ 83dba44). Registered `lead-05a-ii` (session pkt-05a-ii). Ledger row `49e286a1105b4e23ae67d095116e289f` claimed.
- Entry-check probes (all verified): `await` genuinely unbuilt (zero hits in loremaster/ + tests/);
  store-ref current for the probe findings (§ line 835 PROBED 3.2.4 LIVE-on-edge FIRES; line 423
  RE-PROBED 3.2.4 socket-drop `KeyError` shape unchanged; #336 3.2.4 reconciliation landed).
- Seam map (for the contract brief): `await` = a new `CommsActionSpec` in the introspectable
  `_COMMS_ACTIONS` dispatch table (server.py; exact-set pinned `test_comms_tool.py:409/423`) +
  a `_comms_await` handler. Reuses `_comms_drain` (server.py:6434) read-only for the snapshot and
  `_comms_waiting_lines` (6479, the DD-2.a helper 05a-i wired) for the timeout render. Ledger seams:
  `MessageLedger.drain`/`awaiting_answer`/`WaitingOnAnswer` (messages.py). Transport reference:
  `scout.py::CommandSubscriber` (LIVE-primary + poll-fallback + reconnect; catches
  `(*_CONNECTION_ERRORS, KeyError)`) — ONE-IMPLEMENTATION question routed to the sidecar. Forgery-pin
  test-infra: `_comms_fakes.py`/`_message_fakes.py` need a droppable-LIVE fake.
- Fable design sidecar `fable-sidecar-05aii` spawned (general-purpose + fable, standing) — delivered
  `REPORT-fable-design-05a-ii.md`: await RECONSTRUCTABLE (canonical file gone, nothing invented), 6
  contract reqs §A.1–A.6 + 9-pin checklist, 2 forks (F1 stamp?, F2 bound?) + Q5(ii) re-affirm.
  Sidecar STANDING BY (exempt from idle-gate until its next doc is owed).
- Operator ruled (AskUserQuestion, 2026-08-10): **F1 = PEEK/no-stamp**, **Opus-4.8 via opus48-worker**.
  Adopted F2 (fixed 55s const) + F3 (agent-id-only LIVE WHERE) per sidecar recommendations. Rulings
  committed to the packet file + this report; commit `d64cd23`.
- Contract author `contract-05aii-1` (opus48-worker) DELIVERED `REPORT-contract-05a-ii.md`: **26 RED
  pins** (23 in new `test_comms_await.py` + 3 exact-set/param in `test_comms_tool.py`), all
  RED-for-the-right-reason (await unbuilt); **satisfiability 35/35 GREEN + 8 mutation proofs** all
  discriminate (vs a provenance-verified scratch reference; production untouched — `git status` shows
  only test files touched). F1/F2/F3 pinned as decided. Added `FakeMessageLedger.await_inbox`. ruff+mypy
  clean on its 3 files. Named builder reqs (registration + `_comms_await` handler + `await_inbox` wait
  machine + `await_live_select_statement` + `AWAIT_BUDGET_S` + the uuid5 record-id parse BUILD-PROBE +
  the `assert_actions_covered` render case). Kept WARM (likely to revise after the seam ruling/adversary).
  ⚠ Flagged 102 pre-existing mypy errors in the AUTH-test cluster = the #333 auth-WIP baseline
  (RED_ADJUDICATED→pkt39); 05a-ii zero-new. Scratch left in /tmp (sandbox-blocked rm; disposable).
- TWO design forks the contract raised → routed to the standing Fable sidecar (blocks the adversary):
  (5.1) wait-machine seam home — `MessageLedger.await_inbox` vs standalone `InboxAwaiter`/handler
  orchestration (concern boundary); (5.2 → my #2) ONE-IMPLEMENTATION vs `CommandSubscriber` transport
  policy (share vs distinct-with-shared-error-constant); (5.3 → my #3) the peek-teach nuance (await's
  non-empty render reuses `_render_comms_drain(peeked=True)`, which teaches a consume await can't honor).
  Sidecar to append its ruling to its design doc. AWAITING sidecar ruling before the adversary pass.
- Sidecar RULED (R-1/R-2/R-3, appended to design doc): all house-precedent + standing-law, none
  operator-level. Lead-RATIFIED, committed to packet file + design doc, commit `251c40f` (also
  committed the RED contract test files). Scope ADD granted+surfaced: R-2 touches scout.py+test_scout.py.
- Revision handed to warm `contract-05aii-1` (SendMessage): retarget wait-machine pins to standalone
  `InboxAwaiter`; add R-2 shared `_SDK_AWAIT_BOUNDARY_ERRORS` + cross-suite mutation pin (test_scout.py
  into writable set); add R-3 `action=drain` render pin; re-earn satisfiability + mutation receipts.
  AWAITING revised contract, THEN the contract-adversary pass (no builder before the adversary is satisfied).
- Contract REVISED to R-1/R-2/R-3 (`contract-05aii-1`): ~14 wait-machine pins → standalone `InboxAwaiter`;
  R-2 shared-constant + cross-suite anchor; R-3 drain-teach pin; satisfiability 38/38; 10 mutation proofs.
- Contract-adversary `adversary-05aii-1` (opus48-worker) verdict **INSUFFICIENT** (`REPORT-adversary-05a-ii.md`)
  — satisfiability 38/38 (no C-DEF trap), RED honesty confirmed, 9 invariants + waiting-line guard discriminate.
  TWO missing pins: **(§4.1 BLOCKER)** the R-2 sharing "pin" is a BEHAVIOR pin (green on HEAD before the
  constant exists) — two routing-≠-sharing builds (7a scout private clones / 7b await inline) pass all 38.
  Fix = runtime-mutation pin BOTH legs (patch `<module>._SDK_AWAIT_BOUNDARY_ERRORS` → recovery breaks) +
  AST reach-check belt (derived reach, consolidates all ~7 scout clones — the operator DRY directive) +
  builder-req reference-as-patchable-attribute. **(§4.2)** `TestThreadNarrowsClientSide` value-monoculture
  → add a 2nd thread value. §7 residuals: F1 idempotency/shape vacuous on attack 5 (peek_true covers it —
  verify), hyphenated-uuid5 parse = deploy build-probe (named). Revision handed to warm contract author,
  THEN re-adversary (no revision skips it).
- Contract fix committed `218c13f`: R-2 sharing now RUNTIME-MUTATION both legs (patch
  `_SDK_AWAIT_BOUNDARY_ERRORS`→await raises / scout stops recovering) + DERIVED AST reach-check belt
  (found 8 inline clones vs my hand-count of 7 — derived-reach earns its keep). Mutation-proven: 7a
  reddens scout-leg+belt, 7b reddens await-leg+belt. Thread parametrised {q:gate,q:other}; F1
  idempotency de-vacuous'd (`_StampingDrain`). Satisfiability 42/42; mislabel corrected.
- Re-grade handed to warm `adversary-05aii-1` (delta): JOB 1 = confirm 7a/7b/monoculture now redden;
  JOB 2 = attack the NEW pins (runtime-mutation vacuity? AST belt's OWN reach derived/spelling-proof?
  STOP-rule if it recedes). AWAITING re-verdict → on SUFFICIENT the Opus-4.8 builder (reuse-audit brief).
- Adversary re-verdict **SUFFICIENT** (`REPORT-adversary-05a-ii.md` §R3, HEAD `218c13f`): all 4 fixes
  verified (7a/7b/thread/stamping redden); scout-leg mutation RED on unwired HEAD = real standing guard;
  satisfiability 42/42, no C-DEF trap; runtime-mutation pins sound (non-vacuous controls); AST belt
  spelling-defeatable (concat) but the mutation pin backstops every inline spelling (redundant defense).
  ONE residual PINNED as a BOUND (not spiraled, per the pre-authorised STOP-rule): a same-named LOCAL
  re-definition of the constant in a consumer module (drift-only, correct today) + a 3rd-module clone.
  Builder-req: "import from `_txn`, do NOT re-define" + a re-open trigger. NOT a blocker.
- Contract-adversary SATISFIED → releasing the Opus-4.8 builder (lead-base v4: no builder before the
  adversary is satisfied — now met).
- Builder `builder-05aii-1` (opus48-worker) spawned: implement `InboxAwaiter` (reuse `_open_command_connection`
  /`retry_on_conflict`/backoff/`drain(peek=True)`/`awaiting_answer`/render fence) + shared `_SDK_AWAIT_BOUNDARY_ERRORS`
  (+`_WITH_CONTENTION`) in `store._txn` DRY-consolidating scout's 8 clones (import, don't re-define — the
  pinned bound) + `_comms_await` handler/registration + `action=drain` typed-applicability render + the
  uuid5 record-id live build-probe (:18000). MANDATORY reuse-audit table in its report. Commits its green
  build; reports SHA + passed-counts. AWAITING → then Opus-4.8 COLD AUDIT (fresh context, re-runs gates +
  the removed-behavior adjudication on the 8-site scout reshape) → deploy (go/no-go to operator) → live smoke.
- Builder DELIVERED commit `f5aec32`: await GREEN (test_comms_await 28/28, blast-radius 1989 passed,
  ruff clean, zero-new mypy, currency PASS 0 RED_ORPHANED); live uuid5 build-probe PASS on :18000 (3.2.4,
  backtick record-id parses hex+hyphenated, LIVE fires+discriminates). Files: `inbox_awaiter.py` (new 313),
  `scout.py` (8 clones→shared constant), `server.py` (handler/render), `store/_txn.py` (constants). Reuse-audit
  table complete (nothing cloned). TWO flags: (§6.1) **#353** contract missed `test_retry_seam.py` blast radius
  — a DRY WIN (the existing retry-seam guard forced routing InboxAwaiter's SDK calls through `retry_on_conflict`);
  (§6.2) **no LIVE reconnect** — deliberate per R-1 (drain on ledger conn, LIVE on separate ephemeral conn →
  dead LIVE never blocks re-drain; non-loss met by poll; forgery pin green). Early-wake-after-drop = optional
  latency add-on.
- Flag §6.2 → sidecar (design confirm: R-1 moots §A.6 reconnect? + the add-on classify). Cold audit
  `coldaudit-05aii-1` (opus48-worker, fresh) spawned: re-run gates + empirically verify non-loss holds w/o
  reconnect + mutation-prove R-2 sharing + adjudicate the 8-site scout reshape + DRY audit. Both AWAITING.
- Sidecar RATIFIED the no-reconnect deviation (Follow-up rulings #2; lead-ratified as packet §R-4): §A.6
  reconnect MOOTED by R-1's two-connection split (final snapshot always on the unaffected ledger conn);
  trust-correct on a ledger-conn drop (drain RAISES, not false-empty; F1=peek → loss-free); latency
  residual DEFERRED w/ named re-open trigger (lead-adjudicable). Recommends 2 cheap optional pins:
  raise-not-empty invariant (PIN-THE-MISS, load-bearing trust — I lean ADD) + known-bound. NOTHING blocks
  GO/deploy. Decide on the optional pins after the cold audit (fold into one addition if warranted).
  AWAITING cold audit.
- Cold audit `coldaudit-05aii-1` **NO-GO** (`REPORT-coldaudit-05a-ii.md`, HEAD `f5aec32` SAME): gates ALL
  GREEN re-derived (pytest 2476p/17s exit0, zero-new mypy, ruff clean, currency PASS 0 RED_ORPHANED); R-2
  sharing PROVEN by IDENTITY (same `_txn` object, no clone) + mutation; 8 scout sites preserved-EXACT;
  injection/R-3/live-probe clean. **BLOCKER #354:** LIVE-**connect** failure (`connect→OSError` /
  `→TxnContentionExhausted`, the #102 contention class) CRASHES `await_inbox` (line ~152 try/finally, NO
  except) — the shared opener re-raises by contract expecting the caller to catch (CommandSubscriber.run
  does), InboxAwaiter dropped that discipline. Reproduced w/ positive control (leg C recovers). Graceful-
  degradation defect (NOT data loss; snapshot-first protects pending-at-entry) but a served-surface trust
  violation + a deviation from design §A.1 step 2 (establish best-effort → poll). **DECISION: FIX NOW**
  (in-scope, required-by-design, ~3 lines mirror `CommandSubscriber._serve`, trust-critical) — not a bound.
  Residuals: R1 (snapshot-drain raises = trust-correct, lock via raise-not-empty pin) · R2 test-hygiene
  nit · R3 pointer-stub convention (intentional) · R4 scratch files → close-out clean.
- FIX CYCLE (delta): contract adds 3 pins (#354 connect-guard + raise-not-empty invariant + known-bound
  for the deferred latency) → adversary delta → builder fix (guard connect+establish → poll) → cold-audit
  delta. Surfaced to operator as FYI (fix-now per don't-kick-the-can; redirect to a bound if preferred).
- Operator APPROVED fix-now (2026-08-10): "This was a good decision to fix it. It affected the usability
  of the tool." → no bound; proceed with the #354 guard through the delta cycle.
- Contract pins committed `2e40b03` (PIN 1 connect-guard degrade-to-poll + PIN 2 raise-not-empty). Adversary
  delta-grading the 2 new pins (vacuity/reach). AWAITING → builder applies guard → cold-audit delta → deploy.
- Adversary delta INSUFFICIENT (bounded, not a spiral): PIN 1 SUFFICIENT (non-vacuous, both legs, 47/47);
  PIN 2 reach was a HIDDEN SINGLE-SITE (faulted only the snapshot drain step 1) — a poll/final drain-swallow
  build passed while genuinely false-emptying. Fix = parametrize fault-site over {snapshot,poll,final}.
- PIN 2 parametrized + committed `b18ed31`: per-site mutation receipts (guard exactly one drain → exactly
  that leg reddens; PIN 1 stays green); final isolated at budget=0; satisfiability 49/49; only 4 PIN-1 legs
  RED. Adversary FINAL confirm running. Pre-existing flags (NOT ours, d7e65bd ancestor — cold audit already
  validated the canonical gate at 191): bare `mypy loremaster` aborts (duplicate calibration.baseline);
  102 auth-cluster = #333 baseline. Surface at close-out.
- Adversary FINAL confirm **SUFFICIENT** (`f71760f`): PIN 2 reach complete (3 drain reads, grep-verified);
  builder released. Builder applied the #354 guard `7bc68f9` (docs `ae7fe18`): 19 lines, inbox_awaiter.py
  ONLY, connect-path-only (`except _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION → connection=None → poll`),
  shared constant reused, 3 drain reads unguarded. GREEN: PIN 1 (4 legs) + PIN 2 (3 sites) + SocketDropNonLoss
  + R-2 mutation; blast-radius 1838 passed; zero-new mypy. Lead verified diff scope (inbox_awaiter only).
  Removed the auditor's disposable `scratch_coldaudit_*.py` (cold-audit R4; the ruff RED_ORPHANED source) →
  `ruff check .` clean. Re-engaging cold auditor for the delta (verify #354 closed + gates + currency PASS).
- Cold-audit delta **GO** (`5466b7b`): #354 CLOSED empirically; gates 1838p, zero-new mypy, ruff, currency PASS.
- DEPLOY (operator GO): rollback `pre-05aii-rollback`=`a04a23ca`; built image `65e36c8` from HEAD `5466b7b`
  (await verified in artifact); recreated lore-lore (`f93aad91`, PID1=tini) via the captured mount command.
- ⚠ **DEPLOY BLOCKER — full lore-tier RE-EMBED at boot.** The recreate triggered a FULL lore-tier re-embed
  (~450 files, ~1.5hr), NOT a delta: cross-checked — 127 of 152 boot-indexed files are UNCHANGED (not in the
  122-file git delta). NOT explained by any code/config change (chunker/hash/indexer/reconcile untouched;
  lore.yaml unchanged) → likely a store↔manifest divergence self-heal (`reconcile_store_divergence` →
  `delete_by_tier`), #336-adjacent. Container HEALTHY (steady progress, no crash); uvicorn gated on it; lore
  MCP down for the fleet + THIS session (pre-production, no external risk). **Operator ruled: LET IT FINISH**
  (~1.5hr; correct current index; rollback neither clean nor certainly faster). Long boot monitor armed
  (`bqjkrshhh`, ~120min). **TO FILE once lore serves:** a deploy-mechanism finding — recreate → full lore-tier
  re-embed (every deploy costs ~1.5hr); root-cause the divergence (store point-count vs manifest); #336-adjacent
  → a follow-up packet. **Pending post-boot:** live-leg smoke (served await receipt) + close-out.
