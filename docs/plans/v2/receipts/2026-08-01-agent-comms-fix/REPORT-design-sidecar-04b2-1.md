# REPORT-design-sidecar-04b2-1 — the Fable design sidecar's rulings for the agent-comms fix + packet 04b-2

brief-base v9 read

## SUMMARY BLOCK
- state: **done** (all rulings issued; B2's measurement probe running at write time — see §B2 status line)
- deviations: (1) report written mid-session on the lead's explicit override of the original
  "write only when asked" instruction — the reply channel measurably failed to drain this
  session and the file is the durable channel; (2) I spawned and supervise one measurement
  probe (`probe-esc1-closure-1`) myself — design input, not build work, taken to spare the
  lead's exhausted context; disclosed, not assumed.
- Packages considered: `networkx.simple_cycles` → **replace** the hand-rolled all-cycle walk
  (read: finding #273's four-topology oracle table + the lead's five-shape verification in
  #273's ack note; package installed + operator-authorised at `54d0585`) — **routed to 04b-3**
  (§B4); `graphlib` (stdlib) **kept** for write-time cycle DETECTION (one witness suffices).
  No other mechanism specified.
- decisions-needed: the ⚠ OPERATOR-REVIEWABLE table in §7 — four items for the operator's
  return, none blocking under their standing delegation.
- receipt pointers: probes at `docs/plans/v2/receipts/2026-08-01-agent-comms-fix/`
  (`REPORT-probe-literal-mcp-1.md`, `REPORT-probe-plain-allowlist-1.md`,
  `REPORT-probe-confound-leg3-1.md`, `REPORT-probe-explore-grant-1.md`) · findings #298
  (grant-semantics taxonomy, supersedes #292), #294 (resolved), #299 (server rename,
  operator-ratifies) · lore memory `c4a060bb-9994-5f87-8be4-e11875c3e684` · commits
  `4729fb5`/`7ee7c74` (the fix), `f72e538` (Log correction) · packet file
  `docs/plans/v2/04-comms-blocks-footer.md` §04b-2.

**Authority note, dated 2026-08-01:** the operator went offline mid-session and delegated:
*"Have Fable make the decisions needed to progress."* Everything below is therefore a
RULING, not a recommendation. Items an on-line operator would normally decide are marked
⚠ OPERATOR-REVIEWABLE and collected in §7 for their return.

**Capability/verification bound, stated once:** the lore MCP was believed unreachable at my
spawn; I measured it reachable for freshly-spawned agents (`lore_index()` live, 2026-08-01,
3199 files, watching `/workspace` @ `fa12c11`) and the lead's own binding later reconnected.
Every ledger fact below was read from the live ledger, not from packet prose. Where I relied
on a measurement I did not take (the four probes), I cite the archived report.

---

# §1 · DECISION SET B — packet 04b-2

## B1 — THE SPLIT (the big one), three levels, sized to the lead's declared capacity

**The lead's context is heavily consumed. Ruling: THIS SESSION DOES NOT START THE 04b-2
BUILD WAVE.** A contract→adversary→build→audit chain the lead cannot finish is the
half-built-wave hazard; per §don't-kick-the-can, the structured handoff below — with the
next session's 04b-2 lead as the named owner and this file + the updated packet file as the
entry point — **is the deliberate, honourable stop, not an early one.** If you are the next
lead reading this: the previous session stopped CORRECTLY, on a ruling, with its remaining
capacity spent making your entry cheap.

### Level 1 — THIS SESSION lands (each slice small, safe, independently landable)
1. Record these rulings: this file + the packet file's 04b-2 section updated to cite it +
   the INDEX Log line + **mint the 04b-3 row in the INDEX NOW** (a split that exists only in
   a message is a ruling the next session never meets).
2. **ESC-1's measurement** (§B2) — runs via my spawned probe; verdict recorded when it lands.
3. **#263** — fix the packet text to the construction the landed contract actually uses (doc
   edit), or wontfix citing it.
4. **#277** — fold into close-out receipts and resolve there.
5. Archive strays to `docs/plans/v2/receipts/2026-08-01-agent-comms-fix/` via `git mv`
   (done for the four probe reports at write time; this file follows at close-out).
6. INDEX Log entry + handoff.

### Level 2 — NEXT SESSION: the 04b-2 wave proper, ONE contract→adversary→build→audit→deploy
Scope, consolidated from the packet's Scope IN + the ten inherited rows + the sweep
additions — nothing below is new; every item cites where its reasoning lives:
- the blocked-chain / critical-path render (packet Scope IN);
- fleet unread + unacked-directive columns (R4), counted over the row-unlimited `roster()`,
  **with S2's age-only render and NO stranded-imperative** (§SIDECAR RULING S2);
- **S1-a** — `fleet` defaults to the caller's session, lands WITH-or-BEFORE the columns
  (§SIDECAR RULING S1);
- **ESC-5** — the capped-listing false clear closes, as the packet's ENTRY CONDITION
  (§r6's TWO ESCALATIONS);
- `_comms_footer` + optional `agent`/`session` params + `_INSTRUCTIONS`, per R1/R8/L1/L2/T3,
  with the §B5 type ruling and its pin;
- **R10(iii)** — supersede/claim renders teach at the moment of causation (§R11's FOUR
  ESCALATIONS block);
- **#219** (all FOUR prose sites) · 04a residuals **R-5** and **R-12**;
- **#268** — contract-phase pin strengthening, both-ways mutation-proven (finding #268,
  cold audit CA-10);
- **#279** — the seam-derivation unification, build phase, riders in §B3;
- **#274/#276 close-out** — the cure is BUILT and GATED (`scripts/forgery_door_sweep.py`,
  committed, 20 pins inside `testpaths`); adoption is done in substance — resolve both with
  that receipt, re-derive nothing;
- at the deploy: **#253-verify** and **#260** (the `lore.yaml` lorerunes include lands at
  the recreate — the safe moment, per its ack-note routing);
- then **the deploy, per the §B6 gate below**.
The SIZING FENCE stays ruled: anything in this wave that turns out neither deploy-critical
nor a-few-lines-cheap SPLITS to 04b-3 rather than stretching the session.

### Level 3 — 04b-3 (minted now; each row carries its decision point)
| item | decision point / trigger |
|---|---|
| **#273 + #272** — `networkx.simple_cycles` swap, ONE edit (§B4) | 04b-3 kickoff, or any earlier wave touching `loremaster.tasks` |
| **ESC-1's MECHANISM** — ledger-independent write-path cycle read | conditional on §B2's verdict: YES ⇒ build it and DELETE the known-bound pin WITH the fix; NO ⇒ closed permanently, pin stays |
| **CA-11** — write-time cycle-guard TOCTOU vs a concurrent racer (a contract change) | same cluster as ESC-1's mechanism; 04b-3 kickoff |
| **CA-12** — no supporting index on the cycle-graph read | first measured claim/cycle-read latency, or ledger growth past the dependency-bearing population |
| anything 04b-2's fence ejects | recorded in 04b-2's close-out with its receipt |

## B6 — THE DEPLOY: **this session does NOT deploy — and not only for capacity**

Deploying HEAD now would ship 04b-1's listing surface WITHOUT ESC-5's fix, creating the
exact false-clear window whose provable absence is what made deferring ESC-5 legal
("nothing is served until 04b-2 deploys" — §r6's TWO ESCALATIONS). **A deploy this session
would therefore be a defect, not a convenience.** Production stays on image `e91e37b9`:
the old surface serves the old world honestly; S3's fix stays undeployed but so does the
surface that would serve the confident-wrong answer.

**The deploy is the EXIT of the next session's 04b-2 wave.** Precondition gate — copy this
into the packet file; every line is a receipt, not a vibe:
1. Full gates green with a passed-COUNT in the pasted tail + cold audit GO.
2. **FRESH production backup immediately before** — `surreal export`, EXIT=0, table count,
   engine success line verified. The 2026-07-28 backup (2.68 GB) is NOT the rollback for a
   migration run days later; re-take it.
3. **Re-derive both containers' `CreateCommand` at deploy time** (`podman inspect`, never a
   stale capture) and diff lore-lore's against #165's known-good mount shape: the snapshot
   mounted at the path the server READS, never `/source`; **never `lore-deploy start`**
   (#165/#166 standing — lore-lore is not restart-durable).
4. `forgery_door_sweep` EXIT=0 + the dirty-store legs asserted in the gate tail. **The R11
   backfill executes against the PRODUCTION store at this boot** — that is the deploy's
   riskiest line; its guard belongs in the receipts.
5. Rollback receipts written into the Log BEFORE the recreate: retained old image id,
   captured create commands, fresh-backup path.
6. Smoke after: `lore_index` healthy · `transitive_blockers` over a REAL legacy row (S3
   fixed in production — the packet's reason for existing) · #253-verify · #260-verify
   (`lore_search` serves lorerunes) · the smoke's own finding row resolved as
   duplicate-of-#1 per standing law.
7. Rollback triggers: any smoke leg fails ⇒ recreate from the old image immediately. Store
   restore ONLY if the backfill demonstrably corrupted state — it is one-transaction
   additive, so a failed txn self-rolls-back; succeeded-but-wrong is the restore case.
⚠ OPERATOR-REVIEWABLE (§7): the deploy runs a production data migration, unattended if the
operator is still offline. The gate above is the authority under the standing delegation,
but the next kickoff line should offer the operator the nod if they are back.

## B2 — ESC-1's measurement: RUNS THIS SESSION, taken by the sidecar

The packet names the decision point as "THIS kickoff"; it is met. The probe
(`probe-esc1-closure-1`, spawned 2026-08-01 by me, general-purpose, post-A toolset) answers
by CONSTRUCTION on spike-surreal throwaway DBs — never by reasoning from the invariant pins,
which were written for the mirror, not for the guard's read visibility:
- legacy world (old DDL by removal → column-bearing rows incl. ≥3-deep branching chain,
  cycle, phantom → `ensure_ready` backfill), then verb worlds (`create_task` chains,
  `create_many` with intra-batch deps hanging off persisted ancestors, `supersede_task`);
- both-ways edge≡column set diffs at every commit boundary (edge ROWS, never traversals —
  store reference §6.4);
- the load-bearing leg: ancestor closure by column-walk vs by persisted edges
  (shipped `transitive_blockers` + a raw reverse-arrow `+collect` closure as cross-check);
- **a negative control**: delete one edge row and prove the instrument SEES the divergence
  (a "no divergence" verdict from an instrument never shown to catch one is worthless).
**Verdict semantics:** YES ⇒ the write-path cycle read is achievable ledger-independent;
04b-3 builds it and the known-bound pin is a defect report DELETED WITH THE FIX (ESC-1's own
clause). NO ⇒ ESC-1 closes permanently as measured-NO; the bound and its pin stay.
**Status at write time: probe running; deliverable `REPORT-probe-esc1-closure-1.md` at the
repo root.** Whoever closes this session archives it beside this file and records the
verdict in the packet's ESC-1 row. If the probe dies unreported, the next session re-runs it
from the spec above before touching ESC-1 — the spec is the instrument; do not re-derive it.

## B3 — #279: UNIFY the store-seam derivation, in the 04b-2 build wave

Ruling: the builder's own pre-written edit is adopted — `store_seams()`/`seam_bindings()`
(in `scripts/forgery_door_sweep.py`) become the ONE derivation;
`test_blocks_edge.py::_degrade_every_STORE_seam` becomes a caller over the wide superset
(its own definition, i.e. without the `statement` predicate). Riders, same breath:
1. **Sharing proven by MUTATION, both ways** — perturb the seam predicate; BOTH the sweep's
   pins AND the contract's degradation pins must go RED, with the declared-RED sets taken
   from `--collect-only` BEFORE the run (the #194/#196 law).
2. The edit touches `test_blocks_edge.py`, a contract file 04b-1 closed green — **legal
   under this ruling**, one-concern commit, and the 04b-2 adversary re-grades the edited
   file's discrimination (DESIGN-LAW §15: instruments get an adversary).
3. If unification forces a worse API: STOP and eject to 04b-3 — L3's escalation clause, not
   a licence for copy #2.

## B4 — #273/#272: routed to 04b-3, with the edit spec attached

A MEASURED NON-DEFECT (zero mismatches vs the networkx oracle on nine adversarial shapes
across two independent checks — finding #273 + its ack note) earns zero urgency; moving
networkx from test-oracle to production import changes the IMAGE in the same deploy that
already carries a production data migration — those risks are deliberately separated.
The 04b-3 row carries the spec so nobody re-derives: swap `_record_legacy_cycles`'s
internals to `networkx.simple_cycles`; the DETECTION path stays `graphlib` (a write-time
refusal needs one witness; stdlib); **DELETE the hand-rolled helpers — never maintain
both**; resolve **#272 in the same edit** (the mypy override moves scope with the import).
⚠ OPERATOR-REVIEWABLE (§7): the operator authorised networkx "precisely for this" — this
is sequencing, not refusal.

## B5 — the `_comms_footer` type (the packet's D2 fork): CONCUR with L1, plus the pin L1 demanded

The footer is built through the SAME render seam family the comms surface already uses
(`Rendered` via `render_line` — buying the runtime control-char assert and the sanitiser
seam for the STORED identity text the footer embeds), then explicitly `str()`-ed at the
single append site. A bare f-string is REJECTED: it is a new un-sanitised served surface
carrying an identity-derived value — T3's exact forgery vector, and for a footer the forgery
is an INSTRUCTION agents obey, not a row they misread.
**The discriminating pin is BEHAVIOURAL, because `Rendered` subclasses `str` and every
static gate (mypy, the AST template pin, the mint pin) is blind to demotion:**
1. T3's hostile fixture — an identity value containing a FOOTER-SHAPED FORGERY plus newlines
   and backtick runs must render NEUTRALISED in the served string. A bare-f-string build
   serves the forgery verbatim ⇒ RED. This pin catches the wrong type choice by its
   consequence, which no type check can see.
2. An isinstance pin on `_comms_footer`'s return + a mutation proof: swap the `Rendered`
   build for a bare f-string; declared-RED = the forgery pin; diffed both ways.
3. L2's write-count trigger (footer iff ≥1 item actually wrote) and R8's third-person /
   no-drain-imperative grammar are pinned in the same file.
(Stated as properties — the builder maps exact class names; I did not read `server.py` and
do not rule on symbols I have not read.)

---

# §2 · DECISION SET A — consolidated record (ruled by me, APPLIED + VERIFIED by the lead, 2026-08-01)

Full reasoning traveled in-session; this is the durable record. Status: **landed** —
commits `4729fb5` (the fix) + `7ee7c74` (the pin comments), verified by execution (all seven
changed types spawned; 7/7 live `lore_comms` registrations in a `fleet` read; a post-edit
`contract-adversary` spawn proving the YAML still parses).

- **A1 — form:** DELETE the `tools:` key from the seven lore-facing definitions
  (tdd-family ×5, `contract-adversary`, `package-scout`); inherit the session toolset.
  Literal names rejected for lore (global files × per-project `mcp__lore_<slug>__*` = right
  for exactly one project) though they are MEASURED to work (probe 1 + leg 3, sonnet AND
  opus — the definition, not the model, is the variable); wildcard `mcp__*` measured inert;
  exclusion-list conversion rejected as UNMEASURED for file-defined agents (Explore/Plan are
  built-ins) with ~nil isolation delta while Bash is granted — recorded as the
  pre-authorised alternative behind one probe if grant-level `Agent` denial is ever wanted.
  Rider: replacement pin-comment in each file (never bare-deleted), prompt-level
  no-subagents line, verification by execution (done).
- **A2 — scope:** exactly the seven. Odoo scouts unchanged (probe 1/leg 3 are their live
  verification; re-open = the day odoo onboards to lore; `SendMessage` NOT added — harness
  primitives' grantability-by-name is unmeasured). `security-auditor` already correct;
  `Explore` measured GRANTED; `Plan` inferred from shape, stated as inference.
- **A3 — instrument:** RUNTIME, not static — a `tools:` list certifies nothing in either
  direction (Grep/Glob listed-yet-absent, probe 2 §5.2), so the derived check #292 asked for
  migrates to the only honest layer: brief-base §4 capability check (every spawn) + the
  spawn-probe protocol (on change) + the three-class error-string taxonomy (one-call
  diagnosis; **read the WHOLE string — all three classes share the
  `No such tool available:` prefix**). False #266 comment REPLACED in the same edit.
  Pin-the-miss: in-artifact comments, #298 (the class row), memory `c4a060bb…`.
- **A4 — acceptance:** met and exceeded (7/7 by execution). Bounds stated as facts: certified
  for these definitions, this project, harness 2.1.220, 2026-08-01; other slugs are covered
  by construction (no names to go stale) but each project's first post-fix session runs one
  spawn probe; future harness versions ride #298's re-open trigger.
- **A5 — retired-name sweep:** 35 corpses across 4 global files → 0, individually verdicted;
  the load line replaced by the name-free keyword form (`ToolSearch "+lore",
  max_results 20`) — slug-proof AND rename-proof, making the class unrepresentable in the
  load line; `scripts/lore_tool_name_currency.py` committed as the derived currency
  instrument (unanchored patterns — `_` defeats `\b`; no topic-line gate — its own v1
  false-clear is the docstring's receipt).
- **Ledger:** #298 filed (supersedes #292, carries the full taxonomy) · #292 + #294 resolved
  with receipts · #299 filed (fixed-`lore` server rename; adopted-in-principle, operator
  ratifies). Packet-44's overgeneralised Log sentence corrected by APPEND (`f72e538`) — the
  Log is append-only.

**Two defects flagged in the applied A5 edit of `~/.claude/CLAUDE.md` (open at write time,
owner: lead or next session):** (1) the "allowlisted MCP tools arrive DEFERRED …
`ToolSearch` is REQUIRED" paragraph CONTRADICTS the archived probe receipts — probe 1 and
leg 3 both measured literal-name grants arriving UP-FRONT, immediately callable, with no
ToolSearch granted at all; the paragraph must either state the narrower scope in which
deferred-arrival was actually measured, or be corrected to the measured claim.
(2) an editing artifact doubled `ToolSearch` and broke backtick pairing in the load-line
paragraph itself. Both flagged to the lead in-session.

---

# §3 · What THIS session lands vs what the NEXT session picks up

**THIS session (lead, small + safe):** the A-set (done) · this report · packet-file update
citing it + INDEX 04b-3 row + Log entry · #263 · #277 · the ESC-1 verdict recorded when the
probe lands · archives. **Nothing else.** In the lead's own words, adopted as the ruling:
a ruled, recorded, ready-to-build packet is the good outcome; a half-built wave is not.

**NEXT session (named owner: the 04b-2 lead):** first action = read this file (archived at
`docs/plans/v2/receipts/2026-08-01-agent-comms-fix/`) + the packet's §04b-2; then the
Level-2 wave and its exit deploy per the §B6 gate. The A-fix means every contract author,
adversary and builder it spawns has lore comms — verify nothing about that; it is receipted.

# §7 · ⚠ OPERATOR-REVIEWABLE — for the operator's return, none blocking
1. **The B6 deploy** will run the R11 backfill (a production data migration) possibly
   unattended, next session, behind the seven-receipt gate. What I'd want you to know: the
   backfill is one-transaction additive with a fresh-backup precondition and a
   named rollback; if you'd rather production migrations never run unattended, say so and
   the deploy waits for you.
2. **#273/#272 deferred to 04b-3** — you authorised networkx "precisely for this"; I
   sequenced it out of the migration-carrying deploy. If you want it sooner it can ride any
   wave touching `loremaster.tasks`.
3. **Edits to your global `~/.claude/CLAUDE.md` and agent definitions** were made under
   your delegation (A1/A2/A5) — diffs are in the named commits and the fix is
   spawn-verified; the two flagged doc defects in §2 await one small correcting edit.
4. **#299** (rename the fixed `lore` server) is adopted-in-principle with execution
   deliberately deferred to your ratification, as filed.

---
*Written 2026-08-01 by `design-sidecar-04b2-1` (Fable 5, general-purpose spawn) against
branch `feat/surreal-unification` @ `fa12c11` (+ the session's A-fix commits). Rulings
rest on: the live ledger (#294 #292 #266 #279 #273 #260 #165 #166, read via `lore_findings`
this session), the four archived probe reports, the 04b-1 cold audit §2.3/§10, the packet
file at HEAD, DESIGN-LAW §0/§1/§5/§8, and the store reference §0/§9. Where a mechanism
claim rests on a measurement I did not take, the archived report is cited; where on my own
live calls, they are named. The lore MCP was reachable to me throughout (measured, not
assumed); no structural claim herein fell back to grep except the retired-name sweep of
`~/.claude`, which is grep's honest territory (non-symbol textual seams).*
