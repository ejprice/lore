brief-base v26 read
STATE: done · read-only · measured 2026-11-09 at HEAD e1593d7 (feat/surreal-unification), every claim below dated to that sha
Deviations: none. Lore landmine recall returned 6 (<50, so none were cut off). I extracted finding numbers with `python3 -I` regex `#(\d+)` (no grep). For the doc set this was a fallback for a non-symbol textual seam, i.e. plan prose, which is case (b) of the dogfood protocol. I filed no lore finding because the task forbids lore writes.
Packages considered: none (no mechanism specified)
Odoo-20 portability: n/a (no Odoo seam touched)
Reuse ledger: none
Graded: n/a (scope extraction, not a verdict). HEAD-at-report: e1593d7
Decisions-needed: (1) the INDEX row 64 lists 10 findings the packet-64 file never names, so tell me which of the two is the source of truth (see 64 §3). (2) "64b §DRY" has no home in any packet-64 doc (see the §DRY answer).
Fan-out: haiku 0 · sonnet 0 · peak 0 (the routing table explains why)

## Routing table (written before the first read)
step · tier · who · reason
- extract #NNN from 3 packet files, INDEX rows 64–69, RULING-17 and the packet64 design docs · 1 · me, as one parallel python batch · about 600 lines in 5 small files; I read the output in full anyway and it was on the critical path
- read the packet files and Log entries, then judge each subsystem boundary · 3 · me · the deliverable IS the judgement of where each packet's boundary lies. A sampled Sonnet draft would miss sub-split ownership that lives in amendment docs rather than the packet file. That happened here: 64b-i/64b-ii and am-37 §8.3.

============================================================
## PACKET 64 — Governed-tool retrofit: tasks + findings
1. Status (INDEX row 64): open. The packet file was minted 2026-09-24 and pre-split into 64a/64b/64c. Log 2026-10-01 says "NEXT: 58, then 64b-i". The 64b-i contract has landed: its reds account for "530 failed, all owned by 58/64b-i" in the Log entries for packets 63c and 66.
2. Scope IN:
   - DDL: `_governed_field_specs` and `_governed_index_statements` on `task` and `finding`, with no ASSERT or DEFAULT
   - `capability=` and server-stamped identity on lore_tasks, lore_claim_task and lore_findings. The caller args `created_by`/`actor`/`owner` stop carrying identity (F5).
   - every read through `read_filter`, served counts included; every write, delete and re-scope through `guarded_write`
   - Keep semantics (any household member may claim or resolve); `SET_SCOPE` and admin `SET_OWNER` (§10.7-Z orphaning)
   - dirty-store `migrate_governed` legs for task and finding (UNOWNED-LEGACY), plus the DD-3.c ASSERT KEEP/DROP decision for each table
   - pin families F1–F5 parametrised for task, finding and `blocks`; the 19 #420 legs; `_TASK_ACTIONS`/`_FINDING_ACTIONS` gain `requires_capability` (F7)
3. Finding numbers named in the packet file (exhaustive, 8): #356 #404 #407 #420 #429 #446 #466 #467. Of these, #356 (packet 58) and #467 (63c) are listed under Scope OUT, and #446/#466 are citations only.
   - The file's "Findings owned" table also names, without a "#" prefix: 406, 408, 411, 414, 415, 417, 418, 419, 427, 428.
   - INDEX row 64 lists: #404 #406 #407 #408 #411 #414 #415 #417 #418 #419 #420 #427 #428 #429.
   - Log 2026-10-01 adds "#525 → 64".
   - The packet-64 design docs (kickoff-rulings plus amendments 1–11) also name #412 #416 #422 #425 #436 #453 #461 #473 #487 #488, among other citations. Their union is 38 numbers.
4. Sub-splits:
   - 64a TASKS covers lore_tasks ×8, lore_claim_task, the `task` table and `blocks`. It may split into 64a-i (writes plus migrate) and 64a-ii (reads plus counts). It waits on 58, ruled 58-FIRST on 2026-09-26.
   - 64b FINDINGS covers lore_findings ×10 and the `finding` table. It has been split (amendment-3):
     - 64b-i: substrate touches, the 7 write verbs plus `set_scope`, migrate, DD-3.c and the F5 retirement
     - 64b-ii: the read side (query, get, chain_head, rollup's finding leg, counts, F9 oracles)
   - 64c is a report-only security auditor over both ledgers.
5. Fit: a finding fits here if it is about `loremaster/tasks.py`, `findings.py`, their `server.py` dispatch, `surreal_schema` task/finding DDL, `governed.py`/`principals.migrate_governed` legs for those tables, the `_governed_contract` pins, or PDP/`guarded_write` branches first exercised by the ledgers.

============================================================
## PACKET 65 — Hosted-write enablement + JOINT deploy
1. Status (INDEX row 65): open. The packet file was minted 2026-09-24 and pre-split into 65-pre and 65-cut. Hard dependency on 11c (ruled, pool 29). Unattended migration was ruled YES (pool 28). P1 is UNDESIGNED (pool 31).
2. Scope IN: the hosted-write design (how `ReadOnlyGuardMiddleware` yields to the row-scoped PDP; a Fable sidecar rules it), plus the single joint rebuild and recreate of lore-lore. That deploy lands 39, 48/49 and 60–64, runs `migrate-governed` on PROD, flips posture, wires the edge and connector, and runs the proof ladder.
3. Finding numbers named (exhaustive, 18): #107 #131 #138 #139 #140 #165 #166 #236 #295 #299 #333 #355 #382 #386 #396 #420 #466 #467.
   - Owned: #396 (BLOCKER), #382, #386, #299 (decision), #355 (decision, ruled), #236 and #138 (consults), #467 (gate, resolved by 63c).
   - The rest are citations.
4. Sub-splits:
   - 65-pre is code: P1 hosted-write enablement · P2 #396 `config.auth.keys` reject plus a dual pin · P3 delete `ApiKeyVerifier`/`build_api_key_verifier` · P4 #382 conformance passed-count assert plus `-n auto`→12 · P5 #386 in-image env baseline · P6 `:18500` over-cap `to.ack_note` reads · P7 root REPORT archive sweep · P8 #299 rename to `lore` · P9 brief-base/lead-base `capability=` docs · P10 R5 sweep · P11 dress rehearsal (F4, unruled). It is expected to split again into 65-pre-a (P1) and 65-pre-b (P2–P5).
   - 65-cut is the 14-step ops runbook: backup → CreateCommand capture → build → conformance against a control → rollback receipts → recreate → migrate → posture flip → proof ladder → fresh-session smoke.
5. Fit: a finding fits here if it is about auth/posture (`readonly_guard.py`, `auth.py`, config auth), the in-image conformance harness (`conformance_run.sh`, the env baseline), deploy/runbook/backup or prod reachability, or a gate whose trigger is "the first non-local deploy".

============================================================
## PACKET 67 — memory-surface honesty (Q4 Agent-Memory review)
1. Status (INDEX row 67): MINTED 2026-11-07, open. Pre-split 67a–67d. 67a→b→c land after 64 and 65-pre and BEFORE 65-cut; 67d comes after 65-cut.
2. Scope IN: the memory surface only, meaning `lore_recall` and `lore_remember`, the memory backend, ledger and replay, and the memory DDL.
3. Finding numbers named (exhaustive, 2): #6 ("study #6", write-time duplicate candidates, routed to 33 and NOT adopted) and #107 (citation). The file owns no finding numbers. Its items are review IDs: D1–D4, U1, X3–X5, A1, A2.
4. Sub-splits:
   - 67a, deletions and read-side honesty:
     - D1 deletes `_reinforce` (recall writes despite `readOnlyHint`)
     - U1(b) drops importance (render, param, column, `IMPORTANCE_DEFAULTS_BY_KIND`) and re-homes kinds on a `MemoryKind` Literal
     - D2 removes `lens`; D3 removes `memory_category`; D4 removes the Spectron prose
     - adds Fable's Stop-hook `lore_remember`-count nudge
   - 67b, render honesty:
     - render trust, created date and supersedes through the sanitiser
     - `include="superseded"` and `as_of`
     - X3 relabels `score:`
     - X4 backfills `created_at` in the ledger
     - X5 retires `valid_until`
     - adds `source_ref` and its render (2026-11-08 ruling)
   - 67c, cross-trust supersede: allowed and NAMED in the response. Downgrades teach `kind=uncertainty`. The render derives the crossing.
   - 67d, auto-recall hooks: gated on 65 identity plus a relevance floor.
5. Fit: a finding fits here if it is about `loremaster/memory/*`, the recall/remember tool surface and render, the memory ledger and replay, the memory-table DDL, or memory hooks.

============================================================
## PACKET 68 — Retry loops onto tenacity (no file; INDEX row 68 plus Log 2026-11-07)
1. Status: MINTED 2026-11-07 (operator), open. Wave B, about 0.15. Runs after 66 lands and before 65-cut.
2. Scope IN: convert the five non-store hand-rolled loops to tenacity `AsyncRetrying`/`Retrying`. The loops are:
   - `loresigil.resilient._request_with_retry`
   - `loresigil.voyage_context._request_with_retry`
   - `calibration.engine` (`_backoff_delay`/`_enter_retrying`)
   - `calibration.counting._sleep_backoff`
   - `scripts/token_survey.py::_sleep_backoff`

   Each site's existing classifier becomes the `retry=` predicate. Retry-After is honoured via `additive_jitter`. Existing pins stay unchanged, and a removed-behaviour inventory is required. Then retire `jittered_backoff_delay`'s detached-`RetryCallState` shim if no caller remains. The store's `retry_on_conflict` and `scout._backoff` belong to packet 66 (R11).
3. Finding numbers named: #202 (its "deliberately NOT churned" fence is superseded). Ruling: `sdk3-rulings.md` R11.
4. Sub-splits: none.
5. Fit: a finding fits here if it is about retry/backoff loop mechanics in `loresigil` (resilient, voyage_context, backoff), `calibration` (engine, counting) or `scripts/token_survey.py`. Store-side retry belongs to 66, not here.

============================================================
## PACKET 69 — Boot-time stamp-integrity count (no file; INDEX row 69 plus RULING-17)
1. Status: MINTED 2026-11-09 (the operator accepted 66's pinned bound plus a follow-up), open. Wave B, about 0.15, after 66.
2. Scope IN:
   - At `ensure_ready()`, after DDL convergence, count once per boot, per stamp column, the non-datetime values (`WHERE col != NONE AND !type::is::datetime(col)`). The columns are `task.updated_at`, `finding.created_at`, `message.created_at`, plus any other column read by a `> $since` page.
   - N>0 is LOUD: refuse the cursor-paged legs with the R34 wording, naming table, column, N and "migrate the rows". Never a quiet log.
   - Delete 66d's pin-the-miss `TestANonDatetimeStampIsOutsideEveryLeg` with the build.
   - RULING-17 adds a first probe: does `option<datetime>` admit NULL?
   - It has its own contract and adversary, and the store reference is the first read.
3. Finding numbers named: #597 (the spec, owned). RULING-17 also cites #107 (door class) and #591 (contrast: introduced inside 66's fix wave).
4. Sub-splits: none.
5. Fit: a finding fits here if it is about boot-time store integrity in `ensure_ready()` or data-type drift in stamp columns read by `store.stamp_paging.read_stamp_page`. Fixes to stamp DDL or migrations also re-open #597 (RULING-17 §2.3 triggers).

============================================================
## Does 64b carry a "§DRY" section? NO.
- The packet file `64-governed-retrofit-tasks-findings.md` has no §DRY, and the strings "DRY", "_as_rows" and "GROUP ALL" do not appear in it (python check: all False).
- None of the 12 packet-64 design docs has a §DRY step for 64b. kickoff-rulings §17 has a "DRY ledger" table of nine EXTEND/REUSE candidates, e.g. `classify_zero_row_cas` for #407 and `resource_from_row` for #414/#415. That table does not include GROUP ALL or `_as_rows`. amendment-1 §9 is a "Flags · DRY · discipline" section, also without that sweep.
- The routing exists only on the 63c side:
  - `docs/design/2026-09-29-packet63c-amendment-37.md` §8.3 ("§DRY — the GROUP ALL count reader is ONE function") routes findings, messages and diff to `governed.group_all_count`, "owner 64b (its build already edits `findings.py`), decision point the 63c close-out". It has a STOP rule (a pin that expects `0` on a malformed count gets a DUAL re-key) and a mutation proof (all five call sites must move).
  - §10 (2) extends the sweep to "the `cascaded` audit count, `tasks`, `store/surreal.py`, `index/surreal_manifest.py`, findings, messages, diff → the 64b §DRY step".
  - The §13 residual table row reads: "GROUP ALL sweep (findings / tasks / messages / diff / store / manifest readers) → 64b §DRY step, ONE `group_all_count`".
  - INDEX Log 2026-10-01 (63c-i-a CLOSED) reads: "the GROUP ALL + foreign `_as_rows` sweep → 64b §DRY".
- "Foreign `_as_rows`" is not defined anywhere I read. am-37 §13.B maps `principals._as_rows` onto `rows_of`, and §13.3 (item 5) names "KeepStore's six `_as_rows` post-write sites" as in-domain by derivation. Reading the Log line as covering the copies outside 63c's files is my INFERENCE (MEDIUM).
- So "64b §DRY" is a forward reference to a step no 64 doc has written down. The work it names is the readers in `findings._extract_group_count`, `messages._extract_group_count`, `diff.py`, `tasks`, `store/surreal.py`, `index/surreal_manifest.py` and the cascaded audit count, plus the `_as_rows`-style tolerant row readers. All of them would move onto `governed.group_all_count`/`rows_of`.
- Note: some of those files (messages, diff, store, manifest) fall outside 64b's finding-table boundary.
- Decision for the lead: either write a §DRY into the 64b packet file or a 64b-i amendment, or give the sweep its own row.
