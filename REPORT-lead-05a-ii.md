lead-base v4 read
brief project v7 read

# REPORT-lead-05a-ii — comms `await` verb + Opus-4.8 LIVE leg + deploy the 05a split

## SUMMARY BLOCK (filled at close-out)
- Verdicts acted on: `<graded-sha> -> <HEAD-then> -> SAME|STALE`
- Directives: `<n> ledger / <n> wake / <n> prose-duplicated` (duplicated must be 0)
- Rulings: `<n> in a committed artifact / <n> body-only` (body-only must be 0)
- Agents: `<n> spawned / <n> ledger-retired / <n> left running`
- Uncommitted at stop: `<n> files`

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
