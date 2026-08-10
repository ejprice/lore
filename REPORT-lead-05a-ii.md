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

Rulings tally: 4 in a committed artifact / 0 body-only.

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
- Fable design sidecar `fable-sidecar-05aii` spawned (general-purpose + fable, standing) — producing
  `REPORT-fable-design-05a-ii.md` (contract-ready await design + Q5(ii) ruling + gap flag). Awaiting.
