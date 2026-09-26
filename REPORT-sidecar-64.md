# REPORT-sidecar-64 — packet 64 kickoff rulings (design sidecar, Fable 5.1)

brief-base v16 read
brief project v7 read

## Summary block (brief-base §1)

- **state:** done — Task 1 delivered: F1–F9 + the #417 fork RULED (each a question → answer → reason →
  rider in the same bullet), the 64b-first contract worklist (a), the contract-ahead boundary (b), the
  removed-behaviour inventory seeds (c), and four operator forks (d). STANDING BY for follow-ups
  (contract fidelity reads, forks from contract authors / adversaries) via `lore_comms` thread `64` +
  a native wake; answers land as dated `docs/design/2026-09-*-packet64-amendment-N.md`.
- **deviations:** none. Writable set honoured (this report, ONE new design doc, the idle-gate contract);
  no production code, no tests, no INDEX, no 63c file, no store touched; no pytest run (#466). The idle-
  gate contract is flipped to `{"artifact": null}` after this report (standing-by sidecar).
- **Capability check (brief-base §4):** everything demanded was reachable — lore MCP served every symbol
  (`lore_get_symbol` × 46, `lore_verify` × 4, `lore_recall` × 3, `lore_findings` get × 13 / report × 2,
  `lore_comms` register/heartbeat), `Read`/`sed`/`awk`, read-only `git`. Text-search binaries are hook-
  blocked (#473) — every textual sweep is `awk` over an explicit file list and is SAID so in the doc. No
  live probe was needed (the store reference carried every engine fact used).
- **Packages considered:** none — no NEW package mechanism is specified; every mechanism is an EXTENSION of
  a shipped seam (`authorize_guarded`/`GuardedPlan`, `read_filter`, `resolve_write_scope`,
  `migrate_governed`/`LegacyMapping`, the DDL emitter, `CommsActionSpec`, the F5 substrate,
  `AuditStore.append_fragment`). The 61/62 bespoke-PDP verdict stands, cited.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 0 production symbols ruled by final name; 9 candidate symbols, each with its DRY row
  (doc §17 — all EXTEND or REUSE of a named existing symbol; none hand-rolled).
- **Graded:** `ae54f20` · HEAD-at-report: `e5fa7f9` · DIFFERENT (1 ahead — my own doc commit; no
  production symbol moved). ⚠ The 63c fix wave (`test_fixwave_a19a/a19b_63c_i_a.py`) is UNCOMMITTED in
  the shared tree; nothing ruled rests on it.
- **decisions-needed (operator, via the lead):** doc §15 — **OF-1** tasks' default scope (§10-N
  amendment; recommend PROJECT keep — under the 3-way rule a `principal-private` task is claimable only
  by its creator's agent, which breaks lead-creates/agent-claims); **OF-2** the 65 served-break shape for
  the three tools (recommend: `capability=` required is the ONLY break; `created_by`/`actor`/`owner` stay
  as optional self-consistency checks); **OF-3** §10.7-Z orphaning as a 64 wave (64d; recommend YES);
  **OF-4** carrying the finding `number` count-leak bound into a HOSTED 65 (recommend ACCEPT, pinned).
  OF-1 must be decided before 64a's contract; 64b is unaffected by all four.
- **receipt pointers:** the doc `docs/design/2026-09-26-packet64-kickoff-rulings.md` (committed
  `e5fa7f9`) — §0 one screen · §1 facts F-1…F-18 · §2–§10 F1–F9 · §11 #417 + the 13 owned findings
  adjudicated · §12 (a) worklist · §13 (b) boundary + re-verification list · §14 (c) inventory seeds ·
  §15 (d) forks · §16 riders · §17 flags/DRY/discipline. Findings filed: **#487** (stale 63b #420
  adjudication — enforced verbs still pending, no markers; the pin is one-directional), **#488**
  (amendment-25 half (ii) × §10.7-Z orphaning collision).

## Headline (for the lead's triage, ≤10 lines)

1. **64b (findings) contracts first** — unaffected by 58 and by every operator fork; NEW files only
   (`_governed_contract_64.py` + five `test_findings_*_64b.py` + `test_governed_substrate_64b.py`);
   the held patch is enumerated by file in doc §13 with the five re-verification steps on 63c's base.
2. **Two things the lead should route NOW:** #487 to the 63c lead (the 63b legs never self-destructed
   from `_GOVERNED_VERBS_PENDING_ROUTING`; 64's contract carries the reverse pin regardless) and #488 to
   the 63c sidecar (amendment 25's message half (ii) refuses the exact state orphaning produces).
3. **58's landed shape is a 64a entry check:** 64a is written against 58's RULED task-side shell; a
   shape difference at 64a kickoff is a STOP.
4. **Wave shape recommended:** 64b → 64a (post-58) → 64d (orphaning + #404, ≈0.10, OF-3) → 64c
   security-auditor over all; 64b's split trigger (>0.30) = write side + substrate vs read side.

## Discipline receipts

- Registered `sidecar-64` (session `64-20260926`, role `sidecar`, cadence `≤30m`); heartbeat at the
  read/draft milestone; ledger pointer posted on thread `64` after this report.
- Commits: `e5fa7f9` (the doc), plus this report's own commit — my paths only, no attribution trailer
  (the operator's standing `~/.claude/CLAUDE.md` rule + the brief override the session reminder).
- No worktree used or created.

## Task 2 (2026-09-26) — OF-3 directive ruled: amendment 1 committed `6797d63`

- **state:** done — `docs/design/2026-09-26-packet64-amendment-1.md`. §10.7-Z orphaning WITHDRAWN (operator
  directive); `lore-adm delete` takes a REQUIRED `--delete-obj | --archive-obj | --change-owner
  <agent-name>@<session>`; no option ⇒ a byte-inert refusal that IS the preview (per-table counts +
  consequences). ARCHIVE = a 4th governed column `archived_at` via the ONE emitter + a `NotArchived` PDP
  node ANDed by `authorize_filter` (hidden by default for everyone, admin included; FROZEN for every
  mutating action; `lore-adm unarchive` the one door); `include_archived` on the DERIVED read-verb set with
  a derived bound-line token; pending counts exclude archived deliveries. Per-table dispositions (§4);
  agents retired+archived under all three, NEVER transferred (a credential transfer wearing a data
  transfer's name); `--change-owner` target = an admitted agent, both owner columns from one link.
- **#404 closes; #488 MOOT** under OF-3 (no orphan state is produced; am-25 stands) — I annotate #488
  once the lead confirms the directive is final. 64d re-sized ≈0.20–0.25 → split **64d-i archive
  substrate** / **64d-ii delete verb**, both after 64a/64b; 64c extends over both.
- **Two readings chosen, written down (amendment §0):** hidden-by-default for ADMIN too; the target is an
  AGENT not an email (the email form is given as the CLI resolution rule if the operator prefers it).
- **Flags:** `MemoryLedger.tombstone` is a new verb on a ledger packet 18 retires (the "rebuild does not
  resurrect" pin is the invariant either way); agent hard-delete stays 57 F-B / #412.
- **Graded:** `0ca5bdb` · HEAD-at-report: `6797d63` · DIFFERENT (1 ahead — my own commit; no production
  symbol moved). Standing by.

## Task 3 (2026-09-26) — OF-2 = RETIRE AT 65 ruled: amendment 2 committed `2ea52fe`

- **state:** done — `docs/design/2026-09-26-packet64-amendment-2.md`. The three args LEAVE the served
  schemas with each tool's retrofit wave (64b: `lore_findings` created_by/actor; 64a: `lore_tasks` all
  three + `lore_claim_task` owner); the MCP layer's extra-input refusal names the field; ONE shared
  teaching sentence (field · derived-not-declared · remedy `capability=`) rides the three descriptions
  and the refusal itself iff FastMCP exposes an input-validation hook (the builder reads the installed
  source — `Packages considered` row; absent ⇒ accepted pinned bound). Provenance := the Subject's agent
  row name (+ `actor_agent` id). Riders: F4 hostile set gains the three names (refused, 0 writes, positive
  control); exact-set schema pin per tool; bare prose sweep (server.py, both CLAUDE.md, smoke_p8b, INDEX,
  the comms brief). §14 rows 1–7 replaced. The 65 re-brief table lists every surface (descriptions,
  instructions block, comms brief v7→v8, repo + global CLAUDE.md — the global one is the OPERATOR's,
  smoke_p8b, a superseding memory note, the fleet's habit via the description sentence).
- **§12 CONFIRMED as amended by am-1/am-2** for the 64b author (amendment §7): only the F5 row changes;
  am-1's archive/delete scope is 64d-i/ii, not 64b; 64b builds `resource_from_row` on the 4-field
  `Resource`.
- **#488 annotated moot** (OF-3 final per the lead's entry).
- **Graded:** `f4511ef` · HEAD-at-report: `2ea52fe` · DIFFERENT (1 ahead — my own commit). Standing by.

## Task 4 (2026-09-26) — packet 58 kickoff rulings committed `c8d3241`

- **state:** done — `docs/design/2026-09-26-packet58-kickoff-rulings.md`. **F-1** refuse-and-teach at a
  DERIVED cap (the ledger builds the fragments and counts the composed statements against
  `TXN_STATEMENT_HARD_CAP`; `max_reanchor_dependents(k)` is the accessor the cap−1/cap/cap+1 pin asks;
  the 800 WARN stays a log; never batched). **F-2** rewire ∀ dependents incl. `done`/`wontfix`
  (`edge ≡ blocked_by` ∀ rows — the backfill's own law). **F-4** 58 extracts `TaskLedger._guarded_
  append_fragment`, 57 consumes; pinned by an AST one-producer allowlist over `tasks.py`. **The shell**
  (§4): keyword-only `event / set_parts / params / where_conjuncts / preamble / throw_message`; the
  conjunct list is the seam 64a passes `plan.guard()` through — no second shell, no signature break;
  claim routes through it (loss = THROW + rollback, served `ClaimResult` byte-unchanged; a win gains a
  `claim` event). **#130** (a) superseded rows match no `status=` and leave `blocked=False`, unfiltered
  `query`/`get` keep the marker; (c) the loss render's `superseded by` branch is VERIFIED PRESENT at
  `f4511ef` → pinned, not built (P58's UNVERIFIED closed). F-3 moot.
- **Boundary (§8):** NEW files `test_supersede_reanchor_58.py`, `test_task_guarded_shell_58.py`,
  `test_task_claimable_partition_58.py`, `scripts/probe_reanchor_58.py` (the live strand repro + the
  `array::map`/`IF…THEN…ELSE…END` closure spelling probe — UNPROBED on 3.2.4, fallback named);
  **held patch:** `server.py` (`tasks()` supersede branch consumes `SupersedeResult`; `_render_supersede_
  result` loses the STRANDED sentence) + its render pin file. Existing task test files are 58's own
  domain (DUAL rows adjudicated in the contract).
- **Filed #489** (P58 entry check 4): the cross-module guarded-append DRY item, home `loremaster.store`,
  trigger "the third ledger that needs a guarded append".
- **Graded:** `f4511ef` · HEAD-at-report: `c8d3241` · DIFFERENT (1 ahead — my own commit). Standing by.

## Task 5 (2026-09-26) — 64b split rulings: amendment 3 committed `aea2a9d`

- **state:** done — `docs/design/2026-09-26-packet64-amendment-3.md`. **D-1b = Reading A:** 64b-i flips
  the 7 write verbs + `set_scope`; `query`/`get`/`chain_head` flip in 64b-ii WITH their filter (ii-a §4's
  letter; B would have `query` deny without a capability and serve unfiltered with one). Interim (the
  ii-a shape, reused): the tool gains `capability=` in 64b-i; on a read verb it is a FOREIGN param with the
  strict-param teaching, never accepted-and-ignored nor resolved-and-unused; 64b-ii inverts that pin. The
  F5 retirement is wholly write-side in 64b-i (reads never carried the args); read handlers do nothing
  for F5 until 64b-ii. **D-3:** build the instrument — a one-shot `probe-64` writes
  `scripts/restore_prod_dump.py` NOW (endpoint `:18000` by construction, a minted `test_dump_` DB,
  governed-slice extraction of the `surreal export` by its `-- TABLE:` sections, `POST /import` per the
  vendor doc, read-back receipts, a self-test with precision/recall/missing-section controls); the S2 leg
  is marker-gated on `LORE_PROD_DUMP_DB` and RUNS at 64b-i's and 64a's close-outs and 65's dress
  rehearsal — a close-out without its receipt is `done-with-deviations`.
- **Facts:** `/backups/lore/` holds two pre-63 full dumps (2.7 GB / 3.6 GB); no host `surreal` binary;
  the store image ships `/surreal` 3.2.4; the vendor documents `POST /import`; 63a's migration module
  promised the script and no wave wrote it.
- **Graded:** `6a09954` (the contract report) · HEAD-at-report: `aea2a9d` · DIFFERENT (my own commits). Standing by.
