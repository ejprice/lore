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

## Task 6 (2026-09-26) — packet 58 amendment 1 committed `f4e96b4`

- **state:** done — `docs/design/2026-09-26-packet58-amendment-1.md`. **FORK-A = A1:** a terminal X
  re-anchors ∀ dependents (one class; the only reopen path today); the render SERVES the re-blocked
  subset K (derived from the pre-write read; absent when 0). **FORK-C:** R1 CLOSED in-transaction (a
  closing guard — any row still naming X → THROW → whole supersede rolls back, typed teaching refusal,
  never an auto-retry); R2 write-skew = a NAMED bound (**#491**) healed at boot by `_reanchor_stragglers`
  (the backfill's sibling: idempotent, recorded, to the chain head, ONE txn through the ONE shell — it
  also heals the fleet's legacy #356 strands at the 65 boot) and taught in-window by the existing
  R10(iii) claim-loss render; the blocker-touch close (a guarded write on every blocker of every
  create — the hot-row shape) is costed and rejected for now, named as the trigger's close. Index rider:
  `blocked_by.*` element-path index (held patch, EXPLAIN pin) — not blocking. Neither fork is MAJOR
  (FYI to the operator; no fork).
- **Graded:** `1206233` (the contract report) · HEAD-at-report: `f4e96b4` · DIFFERENT (my own commits).
  Standing by.

## Task 7 (2026-09-26) — packet 58 amendment 2 `e0760fd` + packet 64 amendment 4 `17b7101`

- **58 am-2 (contract DECISIONS):** (a) `query owner=<me>` SERVES a held superseded row, decorated
  `[superseded → X']` (`owner=` asks "what do I hold" — a claimant-column fact supersession never
  touches); `status=` still EXCLUDES it (a live-state label supersession falsifies) and so does
  `blocked=False`; the holder's way to let go is 57's release verb (named). (b) the boot heal CHUNKS at
  the derived F-1 cap (same accessor — one constant, two consumers, mutation-proven), NEVER refuses,
  each chunk one txn, a chunk fault is isolated + WARNING + continue (the next boot is the retry); the
  65 boot's worst case is the legacy population (task 116 → one chunk); receipt against probe-64's
  restored DB at 58 close.
- **64 am-4 (probe-64 D1/D2):** D1 — Reading B ratified (the test-tree derivation is the home until 64d
  promotes `governed_node_tables` to `surreal_schema`); `PENDING_GOVERNED_TABLES` kept as a 3-entry
  hand-list made a CHECKED VARIABLE (decay pin `pending ∩ derived == ∅`; growth pin derived ⊆ slice;
  floor; open-packet non-vacuity; delete-when-empty as a builder constraint per wave). D2 — the
  required/ABSENT split ratified; the ABSENT reason DERIVED from a `TABLE_PROVENANCE` constant that
  must cover the slice; the S2 leg asserts required populations ≥ the pasted floor. D3 ratified.
  **Erratum (mine):** amendment 3 cited `surreal_schema.governed_node_tables` as existing — it is 64d's
  promise; the probe's `lore_verify` caught it.
- **Graded:** `5a43aeb` / `80409f4` · HEAD-at-report: `17b7101` · DIFFERENT (my own commits). Standing by.

## Task 8 (2026-09-26) — store reference §6.7 (import/export) committed `aa1d3d6`

- **state:** done — `docs/reference/surrealdb-31-capabilities.md` §6.7 + an addition-pass note: the ten
  measured import facts (not atomic; ERR entries inside HTTP 200 and the import continues; a mid-file
  parse error stops silently under 200; the vendor's `-d file.surql` example is broken, `--data-binary
  @file` works; export files carry log lines → 400 until stripped; an absent DB silently downgrades the
  schema; field processing disabled → restored rows are §1.4 legacy rows; Accept unenforced; auth
  checked; `OPTION IMPORT;` the one loud refusal) + the probe's own control lesson + the driver's house
  rules. Cited by the SHA-qualified path `80409f4:REPORT-probe-64.md` (§3 + Appendix A, verbatim
  instrument) and the committed `scripts/restore_prod_dump.py` / `test_restore_prod_dump.py`.
- **deviation (lead-granted):** the store reference is outside my brief's writable set; the lead's Task 8
  directive extended it for this one file. **Not re-probed:** my live re-verification (three legs + a
  control on a throwaway `:18000` DB) was permission-denied at the secrets-env read; the entry carries
  probe-64's `[PROBED 2026-09-26, 3.2.4]` provenance, not mine.
- **Graded:** `80409f4` · HEAD-at-report: `aa1d3d6` · DIFFERENT (my own commit). Standing by.

## Task 9 (2026-09-26) — packet 64 amendment 5 committed `9fd34d3`

- **state:** done — **REFUTED:** amendment 1 §4's keep row governs keeps kept by the principal being
  deleted only; the standalone `lore-adm delete-keep` (`KeepStore.delete_keep`) cascades `member_of` and
  leaves every keep-scoped governed row carrying `scope = keep:<dead id>` — invisible to every member,
  admin-only, silently (the class 63c am-28 §E names is LIVE at HEAD for memory/message rows). **Ruled
  into 64d-ii:** `delete-keep` takes the same required choice (`--delete-obj | --archive-obj |
  --change-scope <keep:id>`), required iff scoped rows exist (a zero-row keep deletes as today); ONE
  disposition engine `dispose_population(RowPredicate ∈ {OwnedBy(principal), ScopedTo(keep)})` drives
  BOTH verbs (per-table pre-checks, statements, audit rows, receipts, preview written once —
  mutation-proven: drop one refusal → both verbs red); `KeepStore.delete_keep` gains a refuse-when-
  populated guard so a non-CLI caller cannot orphan; the docstring's forward boundary is discharged.
  64d-ii grows ≈0.03; not MAJOR. #488 annotated.
- **Graded:** `eb75f57` · HEAD-at-report: `9fd34d3` · DIFFERENT (my own commit). Standing by.

## Task 10 (2026-09-26) — packet 58 amendment 3 committed `7266c1b`

- **state:** done — adversary-58's five decisions ruled; **none MAJOR** (each a HOW inside 58's scope; (2)
  re-affirms a standing invariant; (3) a log level). **(1) ERRATUM, mine:** am-2 sized heal chunks by the
  SUPERSEDE's accessor (one shared DELETE) — a heal chunk spans many blockers (PR19 never converges;
  PR18's one-blocker pin was arithmetic-aligned). Ruled: a greedy packer sized by the heal's OWN composed
  count via ONE counting function both consumers share; the one-blocker pin re-keyed to the packer's
  prediction; a ≥6-blocker fixture; the supersede accessor counts the REAL fixed part per K (WB2/PR16).
  **(2)** a heal STORE fault RAISES (the FAILS_LOUD sweep stays unedited and green); only a chunk's DOMAIN
  rejection is isolated + WARNING + continue; a compose cap refusal is a packer bug and RAISES; order
  RULED backfill → heal (K17's world; D12 keeps its edit for the ruled reason). **(3)** a claim loss is a
  typed `claim_lost:` THROW marker → `TxnClaimLostError` at DEBUG in the driver (the `governed_conflict:`
  mechanism by call set); other THROW rollbacks WARNING; ERROR for engine faults; 8-way race → 0
  ERROR/WARNING for losers. **(4)** refuse only a cycle THROUGH X' (`minted = {new_id}`; rewired rows in
  the graph, legacy loops stepped over). **(5)** a phantom chain head is SKIPPED + RECORDED every boot
  (the backfill's phantom posture), never a chunk/boot failure. **SAT for r2:** SD1 `≥ N+1` via a compose
  spy; SD2 pins the ruled order; SD3 `_GUARDED_CAS_DOORS` gains `tasks.py::claim_task` (DUAL row); the
  enumerator's two reach bounds → the reviser files them.
- **Graded:** `ee4b80d` (the adversary report) · HEAD-at-report: `7266c1b` · DIFFERENT (my own commit). Standing by.

## Task 11 (2026-09-26) — packet 58 amendment 4 committed `fd6497d`

- **state:** done — **Reading A, and SD3 is my erratum** (the third this packet, same class: a clause
  written before the mechanism moved under it). Decision 3's typed catch (`TxnClaimLostError`, a
  `TxnDomainRejectionError` subtree — a SIBLING of `TxnContentionExhaustedError`) is not the enumerator's
  door and cannot reinterpret exhausted contention by hierarchy; `_GUARDED_CAS_DOORS` stays at five;
  Reading B would install the very door the invariant polices. Pins: exhausted contention propagates
  unread from claim; a lost race → `ClaimResult(False)`; a hierarchy pin. **Reach question — YES, widen,
  but to SEE typed and tuple catches and partition them by hierarchy** (a caught class whose subclass
  closure contains `TxnContentionExhaustedError` → a door needing the guard; otherwise → a listed
  `_TYPED_CAS_CATCHES` entry), so a future re-parenting flips a typed catch into the door set by
  derivation; r2's item, not a 58 blocker; the helper-indirected re-read stays the filed bound.
- **Graded:** contract-58-r2 (working tree) · HEAD-at-report: `fd6497d` · DIFFERENT (my own commit). Standing by.

## Task 12 (2026-09-26) — packet 64 amendment 6 committed `c8147d9`

- **state:** done. **(1) RATIFIED as an evidence-backed exemption:** no SurrealDB-HTTP auth seam exists in
  `loremaster` (the six existing unwraps authenticate Anthropic, Voyage, the SDK signin and two auth.py
  guards); the driver is the FIRST HTTP consumer, so its `httpx.BasicAuth` builder IS the seam; the
  shared `loremaster/store` seam is a NAMED trigger ("the second SurrealDB-HTTP consumer" — 65's
  production export driver is the candidate) and the entry moves with it; the bound now sits at its
  `<= 7` ceiling — stated in the entry's comment so the next unwrap meets it deliberately. **Who adds
  the line:** the fix agent (`fix-restore-seams`, or a fresh `fix-restore-seams-2` if retired) — one line +
  the evidence comment; the lead commits. **(2) FORK A = A3 ratified:** the harness's
  `surreal_user()/surreal_password()` is the repo's ONE answer to "what authenticates to :18000"; the
  stores' env file carries PRODUCTION secrets (least privilege, #422-class blast radius) and R3 forbids a
  new env-file reader; a wrong credential is a live 401 → exit 2. The 65 production-export driver is a
  different tool under its own R3 grant. **(3) DROP** the `EnvironmentFile=` half (it certifies a file the
  script no longer reads) and delete `STORES_ENV_FILE`; KEEP the ports cross-check, renamed.
- **Graded:** `441f3b0` · HEAD-at-report: `c8147d9` · DIFFERENT (my own commit). Standing by.

## Task 13 (2026-09-26) — packet 58 amendment 5 committed `67bf2cc`

- **state:** done — **(A) REJECTED** (a builder constraint that installs the very door shape the
  invariant polices, to satisfy a scanner keyed on a code shape — the lead's flag is right, CLAUDE.md
  instrument-lesson row 7 applied to its sibling). **(C) is the ∀:** inject `TxnContentionExhaustedError`
  at the ONE apply seam ∀ CAS verbs — derived as the production callers of the two shells (+ the briefs
  relate door) — and assert it propagates UNREAD (zero reads observed, one apply, no reinterpretation);
  control per verb: the verb's own domain THROW → its ruled verdict; coverage checked both ways
  (driven ⊇ derived; driven ⊆ derived). **(B) stays as the static index re-keyed to the caught CLASS:**
  door iff the closure contains exhausted contention (bare/tuple excepts now seen), safe-by-type
  otherwise, two exact sets, re-read presence irrelevant; hierarchy pins kept; cross-checked with (C) in
  both directions; mutations agree across the two instruments. **Erratum (mine, am-4):** its widening
  kept the `_select*` shape key one level down. r2 STOPS proceeding on A; `test_retry_seam.py`'s re-key
  is a held-patch-class edit if the lead so classifies it.
- **Graded:** contract-58-r2 (working tree) · HEAD-at-report: `67bf2cc` · DIFFERENT (my own commit). Standing by.

## Task 14 (2026-09-26) — packet 58 amendment 6 committed `dcf6b0f`

- **state:** done. **FORK-3:** the tier is keyed on WHO decided the rollback — ONE prefix-marker table in
  `_txn` (the existing `governed_conflict:` mechanism generalised): `claim_lost:` DEBUG; `governed_
  conflict:` / `cas_lost:` / `reanchor_straggler:` / `heal_chunk:` WARNING (app-authored, planned for —
  **yes, the WARNING tier reaches 63's governed conflict**; §HELD part 3 stands, with a DUAL row for any
  63 pin asserting ERROR); the engine's own refusals (assert violation, coercion, parse, recursion) and
  contention exhaustion ERROR — an ASSERT rollback is the app writing what the schema refused, the
  #107/DD-3.c alarm; ANY unrecognised root cause ERROR (deny-by-default). The ledgers' THROW constants
  gain the `cas_lost:` prefix (no consumer parses THROW text — pinned by AST); the table's keys ==
  the AST-swept THROW prefixes, both directions; per-tier `caplog` legs + a mutation. **FORK-4:**
  `array::distinct` over the WHOLE column — `[A, A, X]` → `[A, X']` (the T5 hazard is not preserved on
  a row already being rewritten; the edge set is a SET); E11 CHANGED-DELIBERATELY, pinned with a
  control and the same fixture through the boot heal.
- **Graded:** `c42eeaf` · HEAD-at-report: `dcf6b0f` · DIFFERENT (my own commit). Standing by.

## Task 15 (2026-09-26) — #497 landed in the store reference (§3 bullet + §6.2 silence row + anchors)

- **state:** done — commit named in the lead message. **Docs-first check changed the entry's class:** the
  vendor DOCUMENTS the break (`return.mdx` §*Return breaks execution*: `BEGIN; RETURN 1; CREATE a; -- Is
  not executed; COMMIT;`) — a §6.1 "lie" it is not; this repo had never read that section. The vendor is
  SILENT on the two load-bearing halves, which the probe measured: the statements before the `RETURN`
  COMMIT, and every skipped statement reports `status: OK` (so `execute_transaction`'s per-statement
  verification cannot see the truncation); plus a `THROW` after a `RETURN` never fires. Filed **#501**:
  `compose`'s envelope-integrity guard should refuse a top-level `RETURN` fragment statement (58's
  builder is the natural owner — its §HELD already touches `_txn`). **Re-probed by me** this time
  (harness defaults `root`/`spikeroot` — the sanctioned test-store source per am-6; no secrets file read;
  throwaway DB `test_dump_probe497_eeb29295`, reaped). Verbatim instrument:
  ```bash
  H=http://127.0.0.1:18000; NS=lore_test; DB="test_dump_probe497_$(python3 -c 'import uuid;print(uuid.uuid4().hex[:8])')"
  A="-u root:spikeroot"; hdr="-H Surreal-NS:$NS -H Surreal-DB:$DB -H Accept:application/json"
  curl -s $A -H "Surreal-NS:$NS" -H "Accept:application/json" --data-binary "DEFINE DATABASE $DB;" $H/sql
  # P1 RETURN mid-txn → only a; all four statements OK
  curl -s $A $hdr --data-binary "BEGIN; CREATE probe_ret:a; RETURN NONE; CREATE probe_ret:b; COMMIT;" $H/sql
  curl -s $A $hdr --data-binary 'SELECT VALUE id FROM probe_ret;' $H/sql        # ["probe_ret:a"]
  # P2 CONTROL LET → a and b
  curl -s $A $hdr --data-binary "BEGIN; CREATE probe_ctl:a; LET \$pad = NONE; CREATE probe_ctl:b; COMMIT;" $H/sql
  curl -s $A $hdr --data-binary 'SELECT VALUE id FROM probe_ctl;' $H/sql        # ["probe_ctl:a","probe_ctl:b"]
  # P3 RETURN then THROW → a committed, THROW never runs
  curl -s $A $hdr --data-binary "BEGIN; CREATE probe_ret2:a; RETURN NONE; THROW 'should not run'; COMMIT;" $H/sql
  curl -s $A $hdr --data-binary 'SELECT VALUE id FROM probe_ret2;' $H/sql       # ["probe_ret2:a"]
  # P4 CONTROL THROW without RETURN → aborted (table never exists)
  curl -s $A $hdr --data-binary "BEGIN; CREATE probe_ret3:a; THROW 'abort'; COMMIT;" $H/sql
  curl -s $A $hdr --data-binary 'SELECT VALUE id FROM probe_ret3;' $H/sql       # ERR: table does not exist
  curl -s $A -H "Surreal-NS:$NS" -H "Accept:application/json" --data-binary "REMOVE DATABASE $DB;" $H/sql
  ```
  Measured 2026-09-26, engine `surrealdb-3.2.4+20260803.93ab219`: P1 `["probe_ret:a"]` with statements
  2–4 all `status: OK` (the skipped `CREATE b` → `result: null`); P2 both rows; P3 `["probe_ret2:a"]`, no
  error; P4 `The table 'probe_ret3' does not exist`.
- **deviation (lead-granted, as Task 8):** the store reference is outside my brief's writable set.
- Standing by.

## Task 16 (2026-09-26) — packet 58 amendment 7 (cross-packet, cited by 58 and 63c) committed `01565f9`

- **state:** done. **(1) ONE key from two halves:** 63c am-32's DOMAIN (every `except` in the whole production
  tree whose caught expression resolves BY IMPORT — Name/Attribute/Tuple — to a store-error class, AND
  re-reads per a28b's derived definition) + 58 am-5's PARTITION (DOOR iff the class closure contains
  `TxnContentionExhaustedError`, must carry the passthrough; else SAFE-BY-TYPE in `_TYPED_CAS_CATCHES`).
  Two errata: mine (am-5 retired re-read as the DOMAIN filter — wrong; it is only not the DOOR test) and
  am-32's (typed catches listed as doors — a28b's own `issubclass` guard says they cannot be). 58's
  shell-caller scope WITHDRAWN (it lost `record_measurement`). Lifted to the property per the new
  CLAUDE.md rule with a completeness pin over the union {door, typed, #400 translate seam, passthrough}.
  **Membership:** RS-5 and keeps `get_or_create_keyed` → typed-safe once am-33's class lands (keeps is a
  tuple-guarded DOOR at HEAD until then); `floor_calibration/store.py::record_measurement` →
  `_GUARDED_CAS_DOORS`, ALREADY guarded (tuple passthrough; helper re-read via `_fence_verdict`) — no code
  fix, a real door the old `ast.Name` scanner could never see. **(2) Order:** 63c-i-a lands a28b's
  scanner with ONE set first; 58's §HELD is REBASED as a DELTA (the partition, the two moves, the union
  pin, the runtime↔static cross-check) — never a second scanner; a28b's "REPLACE" DRY row → EXTEND.
  **(3) Tier:** `_ROLLBACK_LOG_TIERS` re-keyed from marker prefix to the classified CLASS (am-6
  corrected — the driver already maps every marker AND the engine's identity-taken text to classes,
  am-33's own rule); `TxnUniqueViolationError` → WARNING (planned-for, rare, may also carry a real
  defect); no marker needed; the table's keys == the classifier's producible classes (completeness both
  ways); default ERROR.
- **Graded:** `f66a190` (am-33) · HEAD-at-report: `01565f9` · DIFFERENT (my own commit). Standing by.

## Task 17 (2026-09-26) — packet 58 amendment 8 (r2 adversary INSUFFICIENT @ 821be62) committed `03cb6d0`

- **state:** done. Rules `REPORT-adversary-58-r2.md` per the lead's list. **PKG:** the lead's ruling
  ratified — heal packer = `more_itertools.constrained_batches(items, max_size=TXN_STATEMENT_HARD_CAP,
  get_len=<the ONE counter>, strict=True)`; `more-itertools` a DECLARED direct dependency; items are
  `(row, fragments, weight)` built ONCE (fragments carried, never re-priced); the `strict` ValueError is
  re-raised at the one call site as a typed loud boot fault (F10 pinned). **ERRATUM, mine:** am-3 §1's
  "no library does this" / `Packages considered: none` — a limitation asserted without reading an
  installed API (brief-base §1's named failure). **CLASS (third strike):** the lead's property CONFIRMED
  and sharpened to CONVERGENCE — ∀ straggler populations with resolvable heads, ONE boot heals ALL
  (`count == |population|`, every sent txn ≤ cap), weight = each row's OWN composed count from the ONE
  shared counter; pinned by a GENERATED sweep over the straggler SHAPE space (entries 1/2/k × distinct/
  shared heads × head absent/present × healable/phantom/cyclic × pure/mixed) at cap−1/cap/cap+1 per
  class, F10 single-over-cap refusal as the edge; ingredients DERIVED from the heal's fragment builder.
  **(1) F5/F8/N20:** no builder shape constraint (am-5 (A), rejected twice). The ∀ MOVES to the STATE:
  fault injection at the DRIVER seam (`execute_transaction`/`run_query`), identity assertion (`is` the
  injected instance), coverage a runtime-derived checked variable (observed store-writing entry points ⊆
  ⊇ the static call-graph CAS set, both directions RED). The static index stays reviewer-visible: learns
  `ast.TryStar` + `with contextlib.suppress(...)` as catch forms; `derive_cas_verbs` re-derived from the
  CALL GRAPH (verb reaches the shell AND the driver transitively), whole production tree, no module list.
  Not a receding reach — the sequence ends at the chokepoint every write passes. BC-r2-3/BC-r2-9 deleted.
  **(2) F3:** reading (b) — ANY `loremaster` logger, nothing ≥ WARNING for a routine loss. **(3) F2:**
  missing pin under am-6/am-7, generated over the tier table's classes + completeness. **F4:** the ROW is
  the unit — skip WHOLE, uncounted, one WARNING per unresolvable ENTRY; generated over row shapes.
  **F11:** missing pin under am-1's rider — generated over every RELATE-composing verb (`create_task`,
  `create_many`, `supersede_task`, `_reanchor_stragglers`), spy-derived. **(4) esc1:** owner = 58's
  builder (r1 §FLAGS 1 confirmed): re-key to the current contract or ARCHIVE with a DUAL header; never
  left red. **am-7 folded into r3:** §HELD = DELTA over 63c-i-a's a28b scanner + this amendment's §3.
  **Loop cost for the operator:** round 3; two properties each routed as a class — a 4th instance of
  either re-opens the RULING, not the contract.
- **Graded:** `821be62` (adversary-58-r2) · HEAD-at-report: `03cb6d0` · DIFFERENT (my own commit).
- No code/tests/store touched. Standing by.
