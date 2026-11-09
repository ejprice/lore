brief-base v25 read
brief project v7 read

# REPORT — audit-sdk3-66 (cold audit, packet 66: surrealdb SDK 2.0.0 → 3.0.0)

## SUMMARY BLOCK
- **VERDICT: NO-GO.** Graded `7cc5837` (range c503bf7..7cc5837, 54 commits) · state: done.
- **BLOCKING 1 — the exit criterion fails:** the packet's ONE full suite (`--currency`, all 3 legs, at TREE `9e0f3ada…`) ends `pytest RED_ORPHANED 2` (§THE full suite):
  - ① `test_no_raw_listener_in_test_trees` vs `_sdk3_proxy.StoreBounceProxy._listen`: packet-66 contract infra, red since round 1, never in any targeted set;
  - ② `test_text_hygiene` vs `_txn`'s `ContextVar("lore_long_operation_seconds")`: introduced by the builder's `df84764`, green at c503bf7. A scanner firing on non-served text; it needs a ruling, never a dodge.
- **BLOCKING 2 — a served-surface regression (R17 false clear, CONSTRUCTED live):** drop #34's retirement (`ead3356`) breaks the rollup cursor's exclusive boundary. The SERVED `next cursor` text (µs) re-serves the row it was read from (stamp `…186697518Z` → served `…186697+00:00` → `reserved=True`; in-process control passes). Finding **#590**.
- Held: typecheck RED_ADJUDICATED 99 (58 / 64b-i, owned), ruff GREEN; 58/64b-i red set IDENTICAL both ways (530 = 530 once c503bf7 is measured over the 7 files the targeted baseline skipped); 6/6 sharing mutations HELD (full_jitter, R27-2a, MP-1, R34 ×14, R41-T awaiter re-run; R41-T scout + R41-S receipts VALID); check B PASS; R22 0 MIXED; R34 reach 12 = 12; replays 10 KILLED, W5/W6 survive as the named residuals with the builder on the right side; 20× loop VALID (19 on known content + 1 extra green run at 7cc5837).
- Deviations: (1) the full suite ran under a runpy wrapper that only copies the gate's junit out (§THE full suite); (2) item 7's ADVERSARY4 `loremaster/` wrong builds NOT TRIED (narrow reading, both written); (3) the 58/64b-i baseline was completed by my own c503bf7 run of 4 files.
- Packages considered: none — no mechanism specified (audit; I read installed `surrealdb` 3.0.0 `async_ws.py`/`datetime.py` and tenacity use for the bound checks).
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: none (no new symbols; prior-art findings: drop #5 private id parsers in `server.py` ×4 + `TaskLedger._traversal_ids`).
- Graded: 7cc5837 · HEAD-at-report: 7cc5837 · SAME.
- Decisions needed: ① and ② routes (port / exempt-with-evidence / adjudicate; whitelist vs rename); #590 fix shape; T3 fork (should a request timeout drop the SHARED connection?); promote W5/W6 demos to pins?; are ADVERSARY4's 15 `loremaster/` wrong builds owed?; reading of R22 "every test edit maps to a row" (3 additions-only commits unmapped).
- Receipt pointers: §THE full suite · §Both-ways 58/64b-i · §Contract-blind (row O1) · §R17 table · §Sharing by mutation · §Wrong-build replays · §Stated-bound verdicts · §Residuals · §Receipts · §Instruments.


## Capability check (brief-base §4)
- Bash, Read/Write, Agent (haiku-runner / haiku-worker / opus55-worker / general-purpose), lore MCP (loaded, registered as audit-sdk3-66). Nothing the brief demands is unreachable at start.
- Index currency at start: lore watched root `/workspace` @ `feat/surreal-unification` `7cc5837`, last sweep ~6 min old; I have edited nothing in the repo, so no reconcile needed.
- HEAD = `7cc5837e47…`, DIRTY_FILES=0, TREE=`9e0f3ada0ee84c1f…` (tree_id.sh, 2026-11-08). Branch is 689 commits ahead of `origin/feat/surreal-unification` (unpushed; not an audit gate, noted).

## Routing table (written before the first sweep — brief-base §3)
| step | tier | who | reason |
|---|---|---|---|
| 1 receipt verification (13 builder rows: log header / EXIT / count) | 1 | me, one parallel batch | 13 small logs, on critical path, I read every line of output anyway |
| 2 full currency suite (the ONE full suite) | 1 | haiku-runner | test run |
| 2b both-ways 58/64b-i node diff | 3 | me | red classification |
| 3 contract-blind diff pass | 3 | opus55-worker (brief-mandated) | fresh frame |
| 3b diff its findings vs X-inventory / drop list | 3 | me | judgment against the ruled inventory |
| 4 R22 commit classification + test-edit ↔ SERVICER-LOG ↔ inventory map | 2 | Sonnet (general-purpose) draft, I sample | classification of a listed set against a key I write; a sampled draft misses nothing here because every row is checkable from git + two files |
| 5 named check B (retry loops) | 3 | me | code reading, an error would seal itself |
| 6 mutation proofs (setup + verdicts) | 3 | me; runs → haiku-runner | mutation verdicts are never Haiku |
| 7 wrong-build replays (setup + verdicts) | 3 | me; runs → haiku-runner | same |
| 8 R34 reach: AST instrument run + grep | 1 | me, one parallel batch | two commands, small output, I diff it myself |
| 9 stated bounds (close() grep, record_text, mixin vs SDK, MP6-5, C10, R42 override) | 3 (grep: 1, inline batch) | me | honesty verdicts |
| 10 C-row log re-read (11 rows) + drop-list fates-as-ruled | 2 | Sonnet draft, I sample ≥3 rows and every KEPT row (#14,#19,#25,#26,#35) myself | a sampled draft would miss a row whose log contradicts it subtly — so the KEPT rows the brief names stay with me |
| 11 20× loop receipt | 1 | me, inline | 20 log headers + summary, small |

## Receipt verification (item 1) — measured 2026-11-08 against graded `7cc5837` (TREE `9e0f3ada0ee8…`)
Instrument: `audit66/tree_of_commit.sh <repo> <commit>` (pasted at §Instruments) recomputes tree_id.sh's TREE= over a commit's blobs without a checkout. **Control:** on `7cc5837` it prints `9e0f3ada…`, equal to `tree_id.sh` on the clean checkout — so the instrument reproduces tree_id.sh exactly.
| builder row | log header TREE | = content of | EXIT / count in log | vs graded TREE | verdict |
|---|---|---|---|---|---|
| targeted exit run, build | `1aa04470…` HEAD 7d44cf1 DIRTY 0 | 7d44cf1 ✓ (recomputed) | EXIT=1 · 524 failed, 10178 passed, 48 skipped, 3 xfailed | DIFFERENT: 7d44cf1→7cc5837 changes `loremaster/tests/test_exhaustion_fates.py` (769903c) + 4 docs | MISMATCH (one test file moved after the run) → superseded by my full suite (item 2) |
| targeted exit run, baseline c503bf7 | none (git-archive extract) | identity lines only (`loremaster.__file__` inside `head_c503bf7/`) | EXIT=1 · 842 failed, 9665 passed, 47 skipped, 3 xfailed, 4 errors | baseline, not the graded tree | VALID as a baseline (identity by `c503bf7^{tree}` + lore.yaml md5, stated) |
| currency typecheck + ruff | `1aa04470…` | 7d44cf1 ✓ | EXIT=1 (pytest NOT_RUN under `--legs`) | DIFFERENT (as row 1) | MISMATCH → rerun inside my full `--currency` (item 2) |
| F6 + gate suites | `6660bbca…` HEAD 6b43b65 DIRTY 1 | d7c880d ✓ (recomputed; claim holds) | EXIT=0 · 158 passed | d7c880d→7cc5837 under scripts/: only `pending_contracts.yaml` | VALID for d7c880d content; gate code identical at 7cc5837 (lead's random re-run also valid) |
| 20× loop FINAL | run 1 `2ed8af7b…` HEAD 7d44cf1 DIRTY 1; runs 2–20 `00c0df6e…` HEAD 8032c5b DIRTY 0 | 00c0df6e = 8032c5b ✓ (recomputed) | 20× EXIT=0, 35 passed each; `loremaster.__file__` main checkout, surrealdb 3.0.0 in every header | 8032c5b→7cc5837 = 3 docs files only; production 7d44cf1→7cc5837 = **empty** (verified: only `test_exhaustion_fates.py` + docs) | VALID for runs 2–20 (19 consecutive on known content). Run 1: log mtime 12:17:57, `769903c` committed 12:17:01 — consistent with the builder's "straddled the REQ-H commit" note; its one dirty file is UNIDENTIFIED (tree_id records a count). Bound accepted: the dirty file cannot be named, so run 1 is a green run on an unknown tree; I add one run on 7cc5837 after the full suite (§Receipts) |
| REQ-H confirm | `00c0df6e…` | 8032c5b ✓ | EXIT=1 · 1 failed, 27 passed | docs-only difference | VALID |
| close-path (FORK S) | `c8639f20…` HEAD 5e464bc DIRTY 18 | builder claims "= 6b43b65 content" — **FALSE**: 6b43b65 recomputes to `a6aada14…` | EXIT=0 · 1076 passed | DIFFERENT | MISMATCH (claim wrong; the tree is an unnamed dirty tree). Not an exit gate; superseded by the full suite |
| kill-path (FORK T) | `99b31add…` HEAD 314b9e0 DIRTY 3 | no claim | EXIT=1 · 1 failed, 823 passed | DIFFERENT | interim; superseded by the full suite |
| mutation M1b | `f0e604bc…` | mut_tree (scratch) | EXIT=0 · 2 failed / 2 passed, PROOF HELD | — | see §Mutations (I re-run MP-1 at 7cc5837) |
| mutation M2 | `d642ee88…` | mut_tree | EXIT=4 (declared 3, observed 4) | — | the builder's own declaration error; I re-run R27-2a with a fresh declaration |
| #102 survey | `48e4af15…` HEAD 20c5623 DIRTY 0 | 20c5623 ✓ | EXIT=0 | earlier tree | VALID for 20c5623 |

## R22 both-ways test-edit diff (item 4) — Sonnet draft `audit66/R22-draft.md`, sampled
- **I re-derived the load-bearing cell myself:** a loop over `git rev-list c503bf7..7cc5837` classifying each commit's paths found **0 MIXED** (no commit touches both a production path and a test path). The builder commits (16, incl. the lead's 7d44cf1) touch no test path.
- Classes (draft, sampled): BUILDER 16 · SERVICER 21 · DOCS 14 · REGISTRY 3 = 54.
- Every SERVICER commit is named in SERVICER-LOG (64fcdd6 only inside the #19037 block, not under its own #19030/#19033 heading — weak address, not missing).
- Edits with no R27-5 inventory row: `aea8344` (+19/−0), `20c5623` (new file +625/−0), `7135da4` (new file +360/−0) — **all additions-only** (numstat re-run by me). The inventory is titled *removed/rewritten*; additions need no row under that reading. Reading (b), "every test edit maps to a row" literally: these three are unmapped, while other additions-only commits (S9-3, SVC-S1) did get rows — inconsistent practice. I take reading (a): no finding. Reading (b) would make it a docs residual. The lead should rule; I pick (a).
- PARTIAL rows (d78baa3's `test_sdk3_native_retry.py` +18/−1, where the −1 is a docstring; 81f9cbd's four files, covered by SVC-T1 by content) do not hide a removed assertion.
- Row with no edit: SVC-302, which records that a planned registration was never filed. It describes a non-edit by design.
- **F6 timing:** the only commits before `58fd5df` touching F6 paths are `c01b114`, `64fcdd6` and `6ae8338`, all `scripts/test_pending_contract_gate_f6.py`. Nothing touches `pending_contract_gate.py` / `wave_gate.py` before 58fd5df. OPERATOR-F6.md has no in-file history; its mtime 10:31:28 is ~3 min before 58fd5df (10:34:32). The order is consistent with "ADV5: SATISFIED read before F6 landed", but it is proven only by mtime (MEDIUM).

## Named audit check B (item 5; §R8.3, R33) — read at `7cc5837`
- **`_txn.retry_on_conflict`: PASS.** The body builds ONE `tenacity.AsyncRetrying(stop=stop_any(stop_after_attempt(CEILING), stop_all(stop_after_delay(deadline), stop_after_attempt(FLOOR))), wait=backoff.full_jitter(BASE, CAP), retry=retry_if_exception_type(RetryableConflictSignal), retry_error_callback=_exhausted)` and returns `await retrying(_run)`. There is no `for`/`while` around the attempt. `full_jitter(...)` is passed as `wait=` and never invoked. `_run` only awaits `attempt()`.
- **`scout.CommandSubscriber.run`: PASS under reading (a).** The connect attempt lives only inside `async for connect_attempt in AsyncRetrying(retry=…, wait=backoff.full_jitter(base, max), sleep=self._sleep, stop=self._stopped, before_sleep=…, reraise=True)`. The outer `while self._running:` iterates OUTAGES (ladder → `_serve` → drop → a fresh ladder), not attempts. A mid-serve drop's error is re-raised as the new ladder's first failed attempt (`outage_opened_by`), so tenacity takes the backoff, and the outer loop contains no sleep or wait of its own.
  - Reading (b): "any loop that can re-reach the connect counts". The outer `while` would then be a loop around the attempt. I pick (a): it is the documented per-outage reset, and §R7.1's ladder pin requires it. Fork-flag only.
- **"No wait object is CALLED outside tenacity"**: true of both named loops. Workspace-wide it is false by design: `backoff.jittered_backoff_delay` calls `full_jitter(base, cap)(state)` directly (R20 A4 delegation, serving the non-SDK hand loops in calibration / resilient / token_survey, packet 68's). `additive_jitter` calls `wait_random(...)(state)` (pre-existing, unchanged). Neither sits inside the two named loops. Reading the parenthetical of B as workspace-wide would make R20 A4's own delegation a violation. I read it as scoped to the two loops.

## Sharing by mutation (item 6) — every run in a `scratch_copy.sh` copy at `7cc5837` (TREE `9e0f3ada…`, DIRTY 0), declarations written and sha256-stamped BEFORE any run (`audit66/mut/DECLARED.sha256`), ids from `--collect-only`; `loremaster.__file__` / `loresigil.__file__` / SDK path printed in each log header, all inside the copy
| proof | mutation (file · anchor → replacement) | declared RED (n) | observed | controls green | verdict | log |
|---|---|---|---|---|---|---|
| `loresigil.backoff.full_jitter` (R20 A4) | `backoff.py`: `return wait_random_exponential(…)` → `return tenacity.wait_fixed(cap_s)` | 9: native_retry ×3 (window, both tails, decorrelated racers) · test_surreal_store ×5 (`TestTxnConflictBackoffIsJittered` window, `TestConcurrentRacersDrawDistinctBackoffs` ×4) · test_backoff_seam `…backed_by_tenacity…` | 9 failed / 3 passed; PROOF HELD both ways; restored byte-exact (md5 `91f7708a…`) | 3: `TestTheOneWaitFactoryReachesEveryIn66Site` ×2 + scout's ladder-reset pin, all of which mutate the factory themselves | **HELD** (driver site + the jittered_backoff_delay delegation). ⚠ Bound, measured here: **no pin observes scout's ladder through the REAL factory body.** Every scout ladder pin monkeypatches `backoff.full_jitter` itself, so a source mutation of the factory reddens nothing on scout. Scout's sharing rests on its call-time module-attribute lookup, which `test_the_reconnect_ladder_sleeps_the_factorys_wait` proves. Equivalent for a body change; stated, not a defect | `logs/mut_fj.log` (its `DECLARED=18` line counts argv tokens, 2 per id; 9 ids) |
| R27-2a chunk-row builder | `store/surreal.py` `_chunk_rows_fragment`: `for record, vector in records_with_vectors` → `…records_with_vectors[:1]` (writes one row only) | 2: `test_surreal_store::TestUpsertAndScroll::test_reupsert_same_records_is_idempotent` (the **upsert** caller) · `test_sdk3_index_batching::TestALargeFileIndexesAndIsSearchable::…indexed_and_found` (the **replace_file_fragment** caller, through the indexer) | 2 failed / 3 passed; PROOF HELD; restored (md5 `bb0f368b…`) | 3 single-row `TestUpsertAndScroll` legs | **HELD**: both callers redden together on one content mutation (the builder's M2 was a row-COUNT mutation; this is a content one) | `logs/mut_r27.log` |
| MP-1 `Indexer._commit_or_isolate` | `index/indexer.py`: `if isinstance(error, TxnRowCapExceededError)` → `if not isinstance(…)` | 2: the refused-file row-cap pin `[batch]` + `[realtime]` | 2 failed / 2 passed; PROOF HELD; served text under mutation `'store_op_failed_after_retries'`, missing the cap `1009`; restored (md5 `a44f6f0e…`) | 2 embed-failure legs (not the store catch) | **HELD**: ONE catch site reaches BOTH sweep shapes | `logs/mut_mp1.log` |
| R34 `required_datetime` tz clause | `store/_txn.py`: `isinstance(value, datetime) and value.tzinfo is not None` → `isinstance(value, datetime)` | 14: the `naive` node of each of the 12 caller modules + the helper's 2 naive legs | 14 failed / 45 passed; PROOF HELD; restored (md5 `6d1517d3…`) | the `missing` / `string` legs, the controls | **HELD**: one red per caller module, all 12, plus the helper | `logs/mut_r34.log` |
| R41-T inbox_awaiter (re-run: `inbox_awaiter.py` changed in 7d44cf1 after the servicer's receipt) | `inbox_awaiter.py`: `with connection.timeout(TEARDOWN_KILL_TIMEOUT_SECONDS):` → `if True:` | 4: parked-kill `[InboxAwaiter._safe_kill]` · fake await budget+bound · real-SDK kill `[InboxAwaiter._safe_kill]` · real await store-down | 4 failed / 26 passed; PROOF HELD; restored (md5 `b8e0a3be…`) | CommandSubscriber legs, websocket-error legs | **HELD** | `logs/mut_t_awaiter.log` |
| R41-T scout | — (servicer receipt verified, not re-run) | servicer `build66/r13/logs/mut_T_scout.log`: declared 2 = observed 2, PROOF HELD, restored md5 `7610a42f…`, TREE `6660bbca…` = d7c880d (recomputed) | — | — | **VALID receipt**: `scout.py` is byte-unchanged d7c880d→7cc5837 (the production diff touches only `inbox_awaiter.py`). ⚠ The T logs print no `loremaster.__file__` line; copy provenance rests on TREE equality alone | — |
| R41-S close-raises | — (servicer receipt verified, not re-run) | `build66/reqS/mine/rerun_mutation.log`: SDK `async_ws.py` close() mutated to raise; declared 36 (sha256 `48a8c205…`) = observed 36, 3 controls green, PROOF HELD, SDK sha before = after `93d966e1…`; `loremaster.__file__` inside `reqS/ref` | — | — | **VALID receipt**: the 18 AST-derived owners' production is unchanged 16bb432→7cc5837 (only `inbox_awaiter.py` moved, and it is OUTSIDE the pin's owner set, servicer F-1; covered by the R42 grep below) | — |

## THE full suite — currency gate (item 2), measured 2026-11-08 12:5x–13:15 at `7cc5837`
- **Command** (brief's, with ONE stated deviation): `{ tree_id.sh <repo>; flock /tmp/lore-full-suite.lock systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python audit66/gate_keep_junit.py audit66/junit --currency -- --maxprocesses=12 -p no:cacheprovider; echo EXIT=$?; }`.
  - DEVIATION: `scripts/pending_contract_gate.py` runs UNCHANGED under `audit66/gate_keep_junit.py`, a runpy wrapper (pasted at §Instruments). In the gate process only, the wrapper subclasses `tempfile.TemporaryDirectory` so the gate's junit document is copied out before cleanup. No env var reaches pytest.
  - WHY: the gate keeps pytest's junit in a temp dir and prints no node ids, so a node-level both-ways diff is otherwise impossible.
  - `--help` checked first: a forwarded `-n` is refused; `--maxprocesses` passes through.
- Log `audit66/logs/currency_full.log`: `HEAD=7cc5837e47…` · `DIRTY_FILES=0` · `TREE=9e0f3ada0ee8…` (= graded) · **EXIT=1**. junit kept: `audit66/junit/junit_1.xml`, **14777 tests · 532 failures · 0 errors · 71 skipped**.
- Worker count: not observable in the log (the gate captures pytest stdout). `--maxprocesses=12` was forwarded (RAN line). The sampler saw ≤ 9 matching processes. The ≤ 12 claim is therefore MEDIUM.
- **Peak scope memory 10.44 GB (9.7 GiB) < 16 GiB** (`logs/currency_full_mem.txt`, 2-min samples). No RSS finding.

| leg | verdict | owners / orphans |
|---|---|---|
| typecheck | **RED_ADJUDICATED** — 99 residuals | packet-58-contract · packet-64b-i-contract (both named with triggers) |
| ruff | **GREEN** | — |
| pytest | **RED_ORPHANED — 2** | ① `test_no_raw_listener_in_test_trees.py::TestNoRawListenerInAnyTestTree::test_no_test_tree_opens_a_listener_outside_the_helper` — offender `loremaster/tests/_sdk3_proxy.py:193 (StoreBounceProxy._listen) — asyncio.start_server(…)` (finding #466 class). ② `test_text_hygiene.py::TestNoDeadToolTokensInRuntimeStrings::test_every_lore_prefixed_token_is_a_live_tool_or_whitelisted` — offender `store/_txn.py:700: dead/unknown tool token 'lore_long_operation_seconds'` (the `ContextVar` name of `_LONG_OPERATION_SECONDS`) |
| **CURRENCY** | **FAIL — RED_ORPHANED 2 ⇒ the exit criterion is NOT met** | |

**Attribution of the two orphans** (c503bf7 measured by me: `run_tree.sh` on the builder's `head_c503bf7/` git-archive extract, SDK 2.0.0, `logs/head_c503bf7_four.log`, 8 failed / 60 passed):
- ① is **RED at c503bf7 as well**, with the same offender line. `_sdk3_proxy.py` is packet-66 CONTRACT infrastructure (added by `2697974`/`496d745`/`b655971`, contract rounds 1–4, before the graded range). It has been red and unowned since round 1, and no targeted run ever contained it: the builder's 176-file exit set holds neither file (`grep -c` = 0 in both `target_set_b66_exit*.txt`). Owner: the packet-66 contract/servicer. Options for the lead:
  - (a) port `StoreBounceProxy._listen` onto `loremaster.testing.loopback` (a held `LoopbackPort`);
  - (b) an evidence-backed `_EXEMPT_SITES` entry with a re-open trigger;
  - (c) a registry adjudication.
  Re-spelling to dodge the scan is NOT an option (global CLAUDE.md).
- ② is **GREEN at c503bf7**, so the builder's `df84764` introduced it: `contextvars.ContextVar("lore_long_operation_seconds", …)`. The scanner reads a `lore_`-prefixed runtime string as a claimed tool name. The literal is a ContextVar debug name; it is never served to an agent.
  - So this is "a scanner firing on correct code" (global CLAUDE.md: report it, don't re-spell to get past it). The honest closes are a `_TIER1_FILE_TOKEN_WHITELIST` row with the reason, or a ContextVar name without the `lore_` tool prefix, if the lead rules the prefix carries no meaning there. That is the lead's/servicer's call, not mine.
  - Either way it is RED with nobody's name on it at the graded commit.
- Neither orphan is caused by my audit artifacts. Both files are in the repo at `7cc5837`; my files live outside the tree.

**Failing tests outside packet 66, by real number:** 532 pytest failures in all. 530 sit in packet-58 / packet-64b-i registered files (RED_ADJUDICATED). The 2 orphans above are packet-66's. 0 others.

### Both-ways 58 / 64b-i diff (item 2 receipt) — `reddiff_b66.py` (the builder's instrument) over the builder's c503bf7 baseline junit vs my full junit → `logs/reddiff_audit_full.txt`
- (a) owned-file reds: baseline 523 · HEAD 530 · HEAD∖baseline 7 · baseline∖HEAD 0.
- **The 7 are NOT new:** all sit in files the builder's 173-file targeted baseline never ran (0 cases in the baseline junit). Those are `test_reanchor_58_r4_lease_fates.py::TestExhaustionAtTheLeaseStoreIsNamedByEffect…[create|get|release_if_held|update]` and `scripts/test_forgery_door_sweep.py` ×3.
- My c503bf7 run of those files shows **all 7 RED at c503bf7** (`logs/head_c503bf7_four.log`). Completed baseline = 523 + 7 = **530 = HEAD's 530; set-identical both ways. VERDICT: IDENTICAL.**
- (c) green@baseline∖green@HEAD = 50. 49 are line-number-parametrised ids renamed by the build's edits (`test_am37_13_3…[<file>::<fn>::<line>]` ×31, `test_principals_cli…[<file>::<fn>::<line>]` ×18), absent at HEAD under the old line numbers. The 50th is `test_exhaustion_fates…NON_VACUITY…51_sites`, renamed by REQ-H (769903c). Matches the builder's own (c) and is not a regression.
- ⚠ The builder's "owned reds = c503bf7's 523" was true OVER ITS TARGETED SET ONLY. The full suite shows 530 at both trees; the builder's number is a scope, not the packet's count (CLAUDE.md: "I verified it" is a claim about a SCOPE).

## Contract-blind diff pass (item 3) — blindreader-sdk3-66 (opus55-worker), diffed against the X-inventory / drop list item by item
Report: `audit66/REPORT-blindreader-sdk3-66.md`. Its harness refused its Write; I persisted it with a provenance header. Each blind finding against the inventory:
| blind # | finding | inventory / ruling that covers it | my verification | verdict |
|---|---|---|---|---|
| **O1** | tasks' +1 µs ceiling dropped → rollup `next cursor` no longer exclusive | **drop #34** (C → R, `ead3356`), whose rider reads "retire iff the `updated_since` exclusive-boundary behaviour tests stay green". The tests stayed green because they re-bind the IN-PROCESS `PreciseDatetime` (ns kept); none round-trips the SERVED text | **CONSTRUCTED LIVE** (`audit66/probe_rollup_cursor_test.py`, run in copy c1 then removed; `logs/probe_rollup_cursor.log`). Control (the existing pin's shape) passed. The served-text leg FAILED: stamp `2026-11-08T18:17:45.186697518Z`, served cursor `2026-11-08T18:17:45.186697+00:00` (`server._render_rollup`: `next_cursor.isoformat()`), parsed back by the server's `since` parser → **the cursor re-serves the row it was read from** | **CONFIRMED DEFECT — BLOCKING** (R17 Leg 2: a broken state, an ns-tailed stamp, serves bytes identical to a correct cursor. A regression of PKT-06 §1, and the quantifier law: the boundary property was derived over the in-process bind, not over the path every agent uses) |
| T3 | a 30 s request timeout → `drop` → `close()` on the owner's SHARED socket → every sibling in-flight request fails as OUTCOME UNKNOWN | drop #31 rules the finite timeout; R7/R9 D1 rule outcome-unknown. **No ruling or inventory row addresses the collateral on siblings** (grep: no hit for this consequence) | Read the SDK path (`async_ws._request` → `TransportTimeoutError`; lore `_raise_attempt_failure` → drop → `close()`). Not executed (MEDIUM-HIGH, the reader's own label) | **NEW FORK** (design: should a `TransportTimeoutError` on a healthy, streaming-cancelled request drop the shared connection?). Not blocking by itself: the served text is honest ("may have landed — verify"), only over-broad |
| T4 | outage latency: first requests park the full 30 s in `_await_reconnect`, up to ~2× | F2b (`ReconnectOptions(attempts=-1…)`), drop #29/#30 "K-inherited, SDK defaults"; the 2·N worst case is stated at `TEARDOWN_KILL_TIMEOUT_SECONDS` for kill only | Read `_await_reconnect` (budget = request timeout) | **RESIDUAL**: unpinned latency bound against the MCP client's timeout, no ruling. Lead to route |
| T20 | indexer outcome-unknown read-back can serve `indexed` on a matching PRIOR row | R9 D1 rules the read-back; no inventory row discusses a pre-matching row | `index_file` SKIPS any file whose manifest row is already `indexed` at the same hash (`Indexer.index_file`, content-hash fast path), so no apply runs in that state; only a concurrent writer or a rebuild path that bypasses the fast path could reach it (unverified) | **RESIDUAL (LOW)**, re-open trigger: any path that applies a file whose manifest row is already `indexed` at the same hash |
| O3 / #5 | `server.py` still `str(x.id).split(":", 1)[-1]` at 4 sites | **drop #5** names these `server` sites (6723/6756/6771/7322 at c503bf7) as R | `git grep` at 7cc5837: `server.py` 6739, 6772, 6787, 7338. My probe (`logs/probe_record_text.log`) shows the engine and `record_text` render lore's ULID / `[a-z0-9]` keys BARE, and `Keep.id` / `Principal.id` are built from parts, so the split returns the right key today | **DIVERGES from ruling #5** (not a live defect today; a private copy of the id-to-key rule, ONE-IMPLEMENTATION) |
| O2 / T15 | `_RECORD_KEY_ESCAPES` comment says "`keep:⟨01J…⟩` (angle, SDK 3.0.0 **and the engine**)"; `record_text` docstring "equals the engine's `<string> id` for every key lore mints" | R7(d), R8 F15, R34's stated bound | **Probed** (control: `a-b` → engine ``keep:`a-b` ``, `42` → ``keep:`42` ``, both differ): the engine renders ULID keys BARE, so the comment's "and the engine" is FALSE. `record_text` ≠ engine for **memory's uuid5 keys** (``memory:`4cd6…` `` vs `memory:4cd6…-…`), and lore DOES mint those (and uuid4 `floor_calibration` measurement ids) | **STATED-BOUND OVER-CLAIM** (see §Stated bounds 9a) |
| O14 | `TaskLedger._traversal_ids` residual private id parser | drop #5 | not separately verified | residual (ONE-IMPLEMENTATION), reader-reported |
| T23 | scout `stop()` during a backoff sleep runs one more connect + LIVE + kill | X21 (ladder under R11) | path read | RESIDUAL (LOW) |
| O21 | `briefs._relate_briefed` serves `already_acked=True` for its own timed-out-but-committed RELATE | not in inventory (the outcome-unknown population is new) | not executed | RESIDUAL (LOW, MEDIUM confidence) |
| T17/T19/O10/O13 | strict stamp validation: one corrupt row fails the whole listing; the refusal's "other rows are unaffected" is true of the STORE, not of the response | R34 / RULING-11 (refusal text ruled) | text read | RESIDUAL (prose; LOW reachability under typed DDL) |
| O6–O8 | mappers now raise a generic `SurrealStoreError` (`governed.resolve_subject` catches only `KeepStoreError`) | R34 + 2c0d5ee: the governed path serves the store-integrity refusal BY DESIGN | — | AS RULED (the store-integrity text is the intended served surface) |
| T1, T2, T5–T14, T16, T18, T21–T22, T24–T29, O4/O5, O16, O20, O24 | preserved or replaced as ruled | drop #1, #2, #9, #11, #12, #15, #16, #22/#36, #31, #32, X1–X23 | — | AS RULED (the reader's own "fine"; matches the Sonnet fate table) |
- **What the inventory has and the blind pass did NOT see:** nothing load-bearing. Its rows map onto X1–X23 / #1–#36 except the four NEW items above (O1-as-measured, T3, T4, T20).
- **What the blind pass has and the inventory does NOT:** O1's failure mode (the rider's instrument cannot see it), T3's collateral, T4's latency, T20, O21.

## R34 audit-time reach (item 8)
- **AST instrument** `build66/reqE/scanner_instrument_test_stamp_validator_reach_66e.py::_derived_caller_modules()`, run at 7cc5837 (`logs/r34_reach_ast.log`, EXIT=0): **12** modules (agents, briefs, diff, findings, floor_calibration.store, index.surreal_manifest, keeps, memory.local, messages, principal_keys, principals, tasks).
- **grep** (said out loud: a textual cross-check, `git grep -lE 'required_datetime\(|stored_datetime\('` over every member + scripts, minus `_txn.py`; `logs/r34_reach_grep.log`): **12**, the same set.
- **Diff against the 12 in `test_stamp_validator_reach_66e.py`'s docstring: EMPTY both ways.** The R34 mutation reddened exactly one node per module (§Mutations), so every one of the 12 routes through the helper.
- **Rider-1 sweep for a 13th reader** that bypasses the helper (grep `isinstance(…, datetime)` / `_to_aware_utc` / `fromisoformat(` / `.tzinfo is None` / `replace(tzinfo`; files_scanned=172, hits=17; `logs/r34_rider1_sweep.log`). Every hit parses ISO TEXT, not a store datetime column:
  - `principals._parse_instant` (a CLI argument);
  - `server` rollup `since` (a caller cursor);
  - `server._age_status_from_iso` (a manifest META string; naive → UTC with a WARNING, documented);
  - `memory/local._parse_iso` (ledger JSON, labelled per R34);
  - `scripts/snapshot_gc._to_aware_utc` (a dry-run manifest's text; a converter of drop #8's class OUTSIDE the six #8 named, in a script — residual, the Sonnet draft also flagged it);
  - `_txn.py` itself.
  **No 13th datetime-column reader. VERDICT: reach HOLDS.**

## Stated-bound verdicts (item 9)
| bound | verdict | receipt |
|---|---|---|
| **9a** R34 refusal names the row by `record_text`, "equals the engine's `<string> id` for every key lore mints and differs only for a non-word key" | **PARTLY FALSE.** Equal for ULID, digit-led `[a-z0-9]`, hex and composite-array keys. **Different for `memory`'s uuid5 keys**: engine ``memory:`4cd605e7-…` `` vs record_text `memory:4cd605e7-…` (and the same applies to `floor_calibration`'s `str(uuid4())` measurement ids). Both tables are among the 12 R34 readers, so lore DOES mint non-word keys there. Consequence: the refusal for a corrupt memory row names an id that does not parse as SurrealQL (`memory:4cd6…-…` reads as subtraction). The failure is LOUD (parse error), not silent. The docstring claim is over-broad; the served text is not a false clear | `audit66/probe_record_text.py` (+ `_2`), `logs/probe_record_text{,_2}.log`, both with controls |
| 9b `SdkRequestTimeoutMixin` vs installed SDK 3.0.0 | **HONEST on both stated axes**: raise type `TransportTimeoutError` ✓; elapse point BEFORE the KILL is sent (`async_ws._await_reconnect`: `asyncio.wait({task}, timeout=budget)` → raise) ✓. Both named unmodelled behaviours exist (the `_send` reply-wait half; the `_closing` → `ConnectionUnavailableError` branch). **Two further unmodelled behaviours, not named:** the SDK's `timeout()` is CONTEXT-scoped ("including tasks it starts", `scoped_timeout`) while the mixin's budget is instance-wide; and `_send`'s uncorrelated-error branch. Both are LOW for a teardown-kill double | read `async_ws.py` `timeout` / `_await_reconnect` / `kill` / `_request` |
| 9c MP6-5 | see §Replays (replay agent) | — |
| 9d C10 `run()` rule ("answers the FIRST statement; SDK 3.0 raises a later failing one") | **HOLDS.** Probe on 3.3.5 + SDK 3.0.0: control `RETURN 1; RETURN 2;` → `[1, 2]`; later `THROW` → raises `ThrownError`; a later coercion failure → raises `InternalError`; in-transaction `THROW` → raises `QueryError` "not executed due to a failed transaction" (the cascade notice, not the cause: fine for a harness helper, which only needs to be loud) | `audit66/probe_c10_query.py`, `logs/probe_c10_query.log` |
| 9e R42 close reach — the grep IS the receipt | `git grep -n '\.close()'` over the members + scripts: 179 hits (`logs/r42_close_grep.log`). Direct SDK-connection closes in `loremaster/` live in exactly **19 modules = the 18 AST bootstrap owners** (the S pin's set: AgentRegistry, AuditStore, BriefLedger, CommandSubscriber, DiffEngine, FindingLedger, FloorCalibrationStore, KeepStore, LocalMemoryBackend, MessageLedger, PrincipalKeyStore, PrincipalStore, SnapshotStamper, SurrealCodeGraph, SurrealLeaseStore, SurrealManifest, SurrealStore, TaskLedger) **+ `inbox_awaiter.py:335`** (the teardown leg). The rest are owner-level `.close()` calls (server/CLI composition roots → covered by the owners), sqlite / socket closes (not SDK), and ~40 in `scripts/` probes (SDK users outside every pin — the Q5-headered bound). **I could not reproduce the ruling-time "12 hits"**, because the pattern that produced 12 is not recorded. My derivation is the receipt: no production SDK close outside {18 owners, awaiter} | `logs/r42_close_grep.log` |
| 9f R42 operator override: the awaiter teardown `close()` swallow REMOVED | **Verified in the diff** (`7d44cf1`: `try: await connection.close() except _SDK_AWAIT_BOUNDARY_ERRORS: pass` → `await connection.close()`; docstring updated). **R17, measured** (`audit66/probe_r42_close_raises.py`, `logs/probe_r42_close_raises.log`, store-free fakes): CONTROL, traffic found and close OK → `RETURNED entries=2`. CASE, traffic found and close raises → `await_inbox` **RAISES the raw `surrealdb.errors.SurrealError`**, which REPLACES the found result (the `finally:` teardown raises over the return). What an `await` caller is served: the raw SDK error through the tool layer, with no lore teaching text and no mention that traffic is waiting. Not a loss: await is a PEEK, so the traffic stays pending and the next `drain` serves it. Loud, so CALL_AGAIN is the likely consumer move. Measured context: the builder saw close() over a severed socket never raise on 3.0.0 (40/40), so the case is rare. Per the operator ruling: no test, by direction | — |
| 9g drop-list rows KEPT by measurement (#14, #19, #25, #26, #35) | **The builder's own measurement LOGS DO NOT EXIST** for #14, #19, #25, #26 and #35 (nor #15, X13): only the probe SCRIPTS were kept. The Sonnet drafter re-ran each script on `:18000` (`logs/crow_rerun_*.log`), reproducing the claimed results. #14: db.batch T6 → `QueryError … cancelled transaction`, control `ThrownError`. #19: `ValidationError … is_parse_error=False`. #25: native `record::id` prefix TableScan vs mirror IndexScan. #26: REBUILD cannot change DIMENSION (a code read). #35: `record::id(NONE)` raises, control `[1]`. **#25 is AMBIGUOUS**: the ruled row names TWO replacement candidates (`string::starts_with(record::id(id))` OR an id range); only the first was measured, so the KEEP rests on half the candidate set. **#34's measurement has no script and no log** — and #34 is exactly the row whose retirement is defective (above) | `audit66/CROW-DROP-draft.md` §KEPT; sampled by me: the #14 and #25 lines read in the draft against the re-run logs' existence |

## C-row table / drop list / X-inventory (item 10) — Sonnet draft `audit66/CROW-DROP-draft.md`, sampled
- C-rows: the packet table lists 11; the builder measured 13 (adds #34, #35). NOT SUPPORTED 0. LOG MISSING: most builder probe outputs were never saved (above), so rows are SUPPORTED **only via the audit-time re-run**; #34 has no script at all.
- Drop list #1–#37 + the R42 row:
  - AS RULED except **#5 DIVERGES** (4 `server.py` text splits remain) and **#7 DIVERGES (cosmetic)**: `graph_surreal.py`'s `import_names_by_key: dict[str, RecordID] = {str(name_id): name_id …}` remains `str`-keyed, behaviour-equivalent.
  - **#10: stale docstring.** `_names_with_value_prefix` still describes the retired half-open range.
  - **#29/#30: "recorded in store reference §0b" is NOT written.** The ruling assigns that to the lead at close-out. ⚠ Related: `docs/reference/surrealdb-31-capabilities.md` (the REQUIRED FIRST READ) still says "installed: 2.0.0" in its header and teaches SDK-2.0.0 mechanics in §3 (the KeyError routing, `.query()` statement[0]-only), both untouched by the range (`git diff --stat c503bf7..7cc5837 -- docs/reference` = empty). A close-out item, owner lead.
- X1–X23: all AS RULED (draft, sampled X8/X13/X21–X23 against the code by me).
- **Additional stale prose found by me:** `Indexer._compose_file_fragments`'s docstring still says the chunk-replace is "a DELETE + one UPSERT per record". It is now one batched `INSERT … ON DUPLICATE KEY UPDATE` (§R8.2 class "natural-language surfaces").

## Wrong-build replays against the BUILDER's F6 (item 7) — replay-sdk3-66 (opus55-worker) in copy c3 at 7cc5837; report `audit66/replay/REPORT-replay-sdk3-66.md` (instruments pasted verbatim there: `mkbuilds_replay.py`, `runreplay.sh`, `demo/w5w6_demo.py`)
- Setup: copy `--verify-only` VERIFIED and `loremaster.__file__` resolves inside it. TREE `9e0f3ada…` with DIRTY 0 before and after all 12 runs. The unmutated baseline passed 158/158 over the 4 F6 gate files. Declarations were sha256-stamped at 2026-11-08T18:17:38Z, before the batch. Every port is anchored on the builder's own text, matched once.
| build | KILLED / SURVIVED | how (sampled logs I read: Y2, W5, A4R1) |
|---|---|---|
| ADV5 Y2 (partition consults scope) | KILLED | PROOF HELD, 4 MP6-1 pins red (`logs/wb_Y2_…`) |
| ADV5 Y3 (prefix without `::`/`[` boundary) | KILLED | PROOF HELD |
| ADV5 Y7 (only first selector recorded) | KILLED | PROOF HELD |
| unfixed r10ref predicate (W2, MP6-2) | KILLED | PROOF HELD |
| ADV4 A4R2, A4R3, A4R4, A4R5 | KILLED | PROOF HELD (A4R3's two hunks are adjacent in the builder's file, so one anchor covers both) |
| ADV4 A4R1, A4scope (r8 reading (a)) | KILLED (with extra reds) | mutation_proof EXIT=4 only because MP5-4 pins ALSO went red beyond the declaration (`wb_A4R1…`: 3 failed vs declared fewer). A kill, not a survival |
| ADV5 W5 (walk reads only `selection[:1]`) | **SURVIVED** (158/158 green, EXIT=4 = declared pin stayed green) | the NAMED residual, as ruled |
| ADV5 W6 (partition drops a listed red no selector covers) | **SURVIVED** (158/158 green) | the NAMED residual, as ruled |
- **W5 / W6, the RIGHT side was shipped** (code read by the replay agent; demo `replay/logs/w5w6_demo.out` read by me):
  - W5, a renamed listed id in the SECOND `--wave` file: builder@7cc5837 serves `RED_ORPHANED ok=False` (a SELF-DESTRUCT line for the id), while the CONTROL W5 mutant serves `RED_ADJUDICATED ok=True`.
  - W6, `--wave loremaster/tests` with only listed reds: builder `RED_ADJUDICATED ok=True`, while the CONTROL W6 mutant serves `GREEN ok=True`.
  - Both sanity rows agree. `selecting_selector` checks every selector, `_run_selected_gates` records every selector, and `partition_pytest` never reads the selection.
- **MP6-5:** the re-open trigger ADVERSARY5 §RE-GRADE-2 §3 asked for is PRESENT in the F6 delta-3 comment block, beside the W5/W6 named bounds and their triggers. Its "0 of 59" reachability count is the adversary's grep at 2f07c0a, not re-measured.
- Deviations (the replay agent's own, accepted):
  - Item 7's "every wrong build ADVERSARY4 §INSTRUMENTS defines" was read as its 5 F6 gate builds plus the scope build. **ADVERSARY4's 15 retry/index wrong builds under `adv4/wb/` (they mutate `loremaster/`, not the F6 gate) are NOT TRIED.** The brief says "against the BUILDER'S F6", which supports the narrower reading, but both readings are written here.
  - The W5 demo registry was split one entry per file, because the builder's new R30 path-prefix check refuses the adversary's cross-file entry at load (that check is itself correct behaviour).
- Open question for the lead (the replay agent's): promote the W5/W6 demo cases to F6 pins? Each one discriminates. Today they are named bounds with triggers.

## R17 table (operator; Consumer Law + Trust Doctrine) — "what broken state would serve these exact bytes?"
| served surface | broken state constructed / reasoned | bytes identical to the healthy render? | verdict |
|---|---|---|---|
| **rollup `next cursor`** (`AppContext._render_rollup` + `TaskLedger.updated_since`) | a task stamped with a non-zero ns tail, the cursor round-tripped as served text | **YES**: the served cursor is the same µs text either way, and it re-serves its own row (CONSTRUCTED, `logs/probe_rollup_cursor.log`) | **FALSE CLEAR → STOP** (finding #590) |
| outcome-unknown vs failed (F14 / D1 / F18; `_batch_connection_loss_line`, briefs publish, calibration note) | (i) a request NEVER sent (`ConnectionUnavailableError` before send) → served "OUTCOME UNKNOWN, verify"; (ii) a healthy sibling killed by another request's 30 s timeout (blind T3) → served OUTCOME UNKNOWN | (i)/(ii) render like a genuinely lost write, but the advice is "verify", so a consumer acting without checking verifies first and cannot be wrong. The over-statement errs toward caution | honest (over-broad). T3 is a design fork. MP-1/served-reason mutations held |
| served record-id text (never `str(RecordID)`) | a digit-led ULID / engine-minted `[a-z0-9]` key; a uuid5 key; a non-word key | lore-minted word keys: record_text == engine (probe + controls). uuid5 memory ids DIFFER (`memory:4cd6…-…` vs engine ``memory:`…` ``), visible only in the R34 refusal text | honest for served ids; the R34 bound over-claims (9a) |
| refused-file reason, both sweep shapes | the reason losing the row-cap bound in one shape | NO: the MP-1 mutation reddened both shapes (`'store_op_failed_after_retries'` without `1009` is caught) | trustworthy |
| R34 store-integrity refusal (table · row · column · "report it; other rows unaffected") | naive / missing / string stamp in each of the 12 readers | NO (R34 mutation: every module's naive leg red). ⚠ "other rows are unaffected" is true of the STORE; the RESPONSE (a listing) fails whole (blind T17/T19) | trustworthy, with one over-claiming clause (residual prose) |
| governed identity path, corrupt keep/member_of row (2c0d5ee) | a corrupt `member_of.since` / keep stamp | served as the store-integrity refusal by design (R34), not as `GovernedDenied` | as ruled; MCP-layer bytes not separately probed (MEDIUM) |
| retry / teaching prose (exhaustion, row cap, envelope) | exhaustion after the ceiling; envelope violation | exhaustion text from the ONE `_exhausted` callback (code read); the factory mutation proves one policy | trustworthy (not separately byte-probed) |
| F6 gate verdicts (STALE / green-delete-it / KEPT / scoped) | Y2/Y3/Y7/W2/A4* wrong gates | NO: all KILLED. W5/W6 serve false verdicts ONLY in mutants (the named residuals); the builder's gate serves the right ones (demo) | trustworthy, two named residuals |
| `lore_comms await` teardown (R42 override) | close() raising after traffic was found | NO: it raises (loud), but a raw SDK error replaces the found result (probe) | loud, not a false clear; no loss (peek). Operator-ruled |
| **the gate's own currency verdict** | — | serves `RED_ORPHANED 2`, honestly | the gate is truthful; the packet fails it |

## Residuals (each with an owner and a re-open trigger)
| # | residual | owner | re-open trigger |
|---|---|---|---|
| R-1 | **BLOCKING** finding #590: rollup cursor re-serves its own row | builder (fix) + servicer (pin the served-text round trip) | — (blocks GO) |
| R-2 | **BLOCKING** pytest RED_ORPHANED ①: `_sdk3_proxy.StoreBounceProxy._listen` raw listener (red since contract round 1) | packet-66 contract/servicer; lead rules among port / exempt-with-evidence / adjudicate | — (blocks GO) |
| R-3 | **BLOCKING** pytest RED_ORPHANED ②: `ContextVar("lore_long_operation_seconds")` trips the dead-tool-token scan | builder/servicer; lead rules whitelist-with-reason vs non-`lore_` ContextVar name (a scanner firing on correct code, never a dodge) | — (blocks GO) |
| R-4 | T3: a 30 s timeout drops the SHARED connection, failing healthy siblings as OUTCOME UNKNOWN | design sidecar (fork) | a measured sibling failure, or any change to `_raise_attempt_failure`'s drop rule |
| R-5 | T4: outage latency (~30 s, up to 2×) vs the MCP client timeout, unpinned | lead → sidecar | first measured MCP timeout during a store outage |
| R-6 | drop #5 DIVERGES: 4 `server.py` `str(x.id).split(":", 1)[-1]` sites + `TaskLedger._traversal_ids` (private id parsers; correct today) | builder | any keep/principal key that is non-word, or any change to `record_key` |
| R-7 | 9a over-claim: `required_datetime`/`record_text` docstrings say "every key lore mints"; memory (uuid5) and floor_calibration (uuid4) ids differ from engine text; the `_RECORD_KEY_ESCAPES` comment's "and the engine" is FALSE for ULIDs | builder (prose) | — |
| R-8 | stale prose: `_names_with_value_prefix` (#10), `Indexer._compose_file_fragments` ("one UPSERT per record"), store reference header + §3 (SDK 2.0.0), §0b for #29/#30 not written | lead at close-out (store reference); builder (docstrings) | close-out |
| R-9 | builder C-row measurement logs never saved (#14, #15, #19, #25, #26, #35, X13); #34 has neither script nor log; #25 measured on 1 of 2 ruled candidates | builder (save logs / measure the id-range candidate) | close-out |
| R-10 | W5 / W6 named residuals (pinned only at the plumbing / via currency-ok); demo cases discriminate | servicer, if the lead promotes the demos | any edit to `selecting_selector` / `partition_pytest` |
| R-11 | T20 indexer read-back vs a pre-matching prior row (near-unreachable through `index_file`'s fast path) | builder | any apply path that bypasses the content-hash fast path |
| R-12 | scout `stop()` during backoff (T23); briefs `already_acked` on own timed-out write (O21); `snapshot_gc._to_aware_utc` (#8 class in scripts/) | builder | — (LOW) |
| R-13 | ADVERSARY4's 15 `loremaster/` wrong builds NOT replayed (narrow reading of item 7) | lead: rule whether they are owed | — |
| R-14 | the builder's "owned reds = 523" was a targeted-scope count; the packet's real count is 530 at both trees | lead (archive note) | — |
| R-15 | the full suite's worker count is not observable through the gate (it captures pytest stdout); ≤ 12 rests on the forwarded `--maxprocesses=12` | gate owner | — |

## Instruments (pasted VERBATIM per brief-base §1; also kept under `audit66/`)

### `audit66/gate_keep_junit.py`
```python
"""Run scripts/pending_contract_gate.py UNCHANGED, but keep a copy of each junit.xml it reads.

The gate writes pytest's junit document into a tempfile.TemporaryDirectory that is removed
as soon as it is read, so a node-level both-ways diff is impossible from its log. This
wrapper subclasses TemporaryDirectory IN THE GATE PROCESS ONLY (no env change reaches pytest)
so that, at cleanup, any junit.xml inside is copied to KEEP_DIR first. Gate logic is untouched.
Usage: python gate_keep_junit.py <KEEP_DIR> <gate args...>
"""
import runpy
import shutil
import sys
import tempfile
from pathlib import Path

keep_dir = Path(sys.argv[1])
keep_dir.mkdir(parents=True, exist_ok=True)
_Original = tempfile.TemporaryDirectory
_counter = [0]


class KeepingTemporaryDirectory(_Original):
    def cleanup(self):
        junit = Path(self.name) / "junit.xml"
        if junit.exists():
            _counter[0] += 1
            shutil.copy2(junit, keep_dir / f"junit_{_counter[0]}.xml")
            print(f"[gate_keep_junit] kept {junit} -> {keep_dir}/junit_{_counter[0]}.xml", file=sys.stderr)
        super().cleanup()

    def __exit__(self, *exc):
        self.cleanup()


tempfile.TemporaryDirectory = KeepingTemporaryDirectory
sys.path.insert(0, str(Path("scripts").resolve()))
sys.argv = ["scripts/pending_contract_gate.py", *sys.argv[2:]]
runpy.run_path("scripts/pending_contract_gate.py", run_name="__main__")
```

### `audit66/tree_of_commit.sh`
```bash
#!/usr/bin/env bash
# tree_of_commit.sh <repo> <commit> — tree_id.sh's TREE= algorithm over a COMMIT's blobs (no checkout):
# paths sorted exactly as tree_id.sh sorts them (`sort -z -u`, caller's locale), each line "<sha256 of content> <path>".
set -euo pipefail
cd "$1"
declare -A blob
while IFS= read -r -d '' entry; do
  meta="${entry%%$'\t'*}"; path="${entry#*$'\t'}"
  set -- $meta; [ "$2" = blob ] && blob["$path"]="$3"
done < <(git ls-tree -r -z "$2")
printf '%s\0' "${!blob[@]}" | sort -z -u | while IFS= read -r -d '' path; do
  printf '%s %s\n' "$(git cat-file blob "${blob[$path]}" | sha256sum | cut -d' ' -f1)" "$path"
done | sha256sum | cut -d' ' -f1
```

### `audit66/mut/run_mut.sh`
```bash
#!/usr/bin/env bash
# run_mut.sh <copy-dir> <log> <file> <name> <timeout> — one mutation_proof run in a scratch copy, receipts in the log.
set -uo pipefail
copy="$1"; log="$2"; file="$3"; name="$4"; to="$5"; M="$(dirname "$0")"
cd "$copy" || exit 9
{
  ~/.claude/orchestration/tree_id.sh "$copy"
  .venv/bin/python -c "import loremaster,loresigil,surrealdb.connections.async_ws as w;print('loremaster.__file__='+loremaster.__file__);print('loresigil.__file__='+loresigil.__file__);print('sdk='+w.__file__)"
  md5sum "$file"
  expects=(); while IFS= read -r id; do [ -n "$id" ] && expects+=(--expect-red "$id"); done < "$M/$name.expect"
  mapfile -t runargs < "$M/$name.run"
  echo "DECLARED=${#expects[@]} (from $M/$name.expect, sha256 in $M/DECLARED.sha256)"
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
    .venv/bin/python scripts/mutation_proof.py --file "$file" --anchor-file "$M/$name.anchor" --replacement-file "$M/$name.repl" "${expects[@]}" \
    -- .venv/bin/python -m pytest -q -rfE -p no:cacheprovider -n 4 --timeout="$to" "${runargs[@]}"
  echo "EXIT=$?"
  md5sum "$file"
  git -C "$copy" status --porcelain | head
} > "$log" 2>&1
```

### `audit66/probe_rollup_cursor_test.py`
```python
"""Audit probe (packet 66 cold audit; NOT a repo test): is the rollup cursor's exclusive boundary kept
when the cursor travels as the SERVED text (`next cursor: <datetime.isoformat()>`, server._render) and is
parsed back by the server (`datetime.fromisoformat`), as every agent actually uses it?
CONTROL leg = the existing pin's shape (the in-process PreciseDatetime re-bound): must EXCLUDE the row."""
from datetime import datetime

from test_task_ledger import AGENT_A, DESCRIPTION_XML, SUBJECT_XML, _create  # noqa: F401  (fixture module)
from test_task_ledger import *  # noqa: F403 — the task_ledger fixture and its dependencies


async def test_control_in_process_cursor_excludes_its_own_row(task_ledger) -> None:
    task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
    claimed = await task_ledger.claim_task(task_id, AGENT_A)
    window = await task_ledger.updated_since(claimed.task.updated_at, limit=20)
    assert task_id not in {t.id for t in window.rows}


async def test_served_text_cursor_excludes_its_own_row(task_ledger) -> None:
    task_id = await _create(task_ledger, SUBJECT_XML, DESCRIPTION_XML)
    claimed = await task_ledger.claim_task(task_id, AGENT_A)
    stamp = claimed.task.updated_at
    served = stamp.isoformat()                      # what server._render serves as `next cursor:`
    parsed = datetime.fromisoformat(served)         # what server's `since` parser binds
    ns = getattr(stamp, "isoformat_with_nanoseconds", lambda: "n/a")()
    window = await task_ledger.updated_since(parsed, limit=20)
    reserved = task_id in {t.id for t in window.rows}
    print(f"\nstamp_ns={ns} served={served} reserved={reserved}")
    assert not reserved, f"cursor {served!r} (true stamp {ns}) re-serves the very row it was read from"
```

### `audit66/probe_record_text.py`
```python
"""Stated bound 9a: does record_text (table:key from parts) equal the engine's <string> id for lore-minted keys?
TEST store ws://127.0.0.1:18000 only; RETURN-only, no table written. Control: a non-word key MUST differ."""
import asyncio, os, sys
from surrealdb import AsyncSurreal, RecordID
from ulid import ULID
sys.path.insert(0, "loremaster")
from loremaster.store._txn import record_text

URL = "ws://127.0.0.1:18000/rpc"
assert "18500" not in URL
KEYS = {"ulid": str(ULID()), "ulid2": str(ULID()), "engine_like_digit_led": "4558tcyfmwp3lj775pwi",
        "alpha_led": "abc123", "hex": "deadbeef0123", "CONTROL_non_word": "a-b", "CONTROL_all_digits": "42"}

async def main() -> int:
    db = AsyncSurreal(URL)
    await db.connect()
    await db.signin({"username": os.environ.get("SURREAL_USER", "root"), "password": os.environ.get("SURREAL_PASS", "spikeroot")})
    await db.use("lore_test", "audit66_probe_record_text")
    bad = 0
    for label, key in KEYS.items():
        rid = RecordID("keep", key)
        engine = await db.query("RETURN <string> $r", {"r": rid})
        engine = engine[0] if isinstance(engine, list) else engine  # SDK 3.0 query() answers a list for RETURN
        ours = record_text(rid)
        same = engine == ours
        print(f"{label:24} key={key!r:32} engine={engine!r:42} record_text={ours!r:36} equal={same}")
        if label.startswith("CONTROL") == same:
            bad += 1
    await db.close()
    print("PROBE", "PASS" if bad == 0 else f"FAIL ({bad})")
    return 0 if bad == 0 else 1

sys.exit(asyncio.run(main()))
```

### `audit66/probe_record_text_2.py`
```python
"""Bound 9a, second leg: lore-minted NON-word keys — the uuid5 memory id and the composite [tier, path] file id."""
import asyncio, sys, uuid
from surrealdb import AsyncSurreal, RecordID
sys.path.insert(0, "loremaster")
from loremaster.store._txn import record_text
from loremaster.memory.local import derive_memory_id  # noqa: F401 (shape witness)
URL = "ws://127.0.0.1:18000/rpc"; assert "18500" not in URL
CASES = {"memory_uuid5": RecordID("memory", str(uuid.uuid5(uuid.NAMESPACE_URL, "x"))),
         "file_array": RecordID("file", ["lore", "loremaster/loremaster/server.py"])}
async def main():
    db = AsyncSurreal(URL); await db.connect(); await db.signin({"username": "root", "password": "spikeroot"})
    await db.use("lore_test", "audit66_probe_record_text")
    for label, rid in CASES.items():
        engine = await db.query("RETURN <string> $r", {"r": rid}); engine = engine[0] if isinstance(engine, list) else engine
        print(f"{label:14} engine={engine!r} record_text={record_text(rid)!r} equal={engine == record_text(rid)}")
    await db.close()
asyncio.run(main())
```

### `audit66/probe_r42_close_raises.py`
```python
"""R42 override (7d44cf1), R17: what does await_inbox serve when traffic WAS found and the teardown close() raises?
Store-free: fake connect / drain. CONTROL: the same run with a close() that succeeds returns the found entries."""
import asyncio, contextlib, sys
from surrealdb.errors import SurrealError
from loremaster.inbox_awaiter import InboxAwaiter
from loremaster.messages import MessageDrainResult

class _Entry:
    thread = None; grade = "signal"

def _result(n):
    return MessageDrainResult.model_construct(entries=[_Entry()] * n, total_pending=n, directive_pending=0, stamped_seqs=[], peeked=True)

class _Conn:
    def __init__(self, close_raises): self.close_raises = close_raises; self.closed = False
    async def query(self, *a, **k): return ["live-uuid"]  # SDK 3.0: one per-statement result
    async def subscribe_live(self, *_):
        async def gen():
            await asyncio.Event().wait()
            yield None
        return gen()
    async def kill(self, *_): return None
    @contextlib.contextmanager
    def timeout(self, *_): yield
    async def close(self):
        self.closed = True
        if self.close_raises: raise SurrealError("close failed over a severed socket (injected)")

async def run(close_raises):
    calls = {"n": 0}
    async def drain(**_):
        calls["n"] += 1
        return _result(0 if calls["n"] == 1 else 2)   # nothing at the snapshot, traffic on the first poll
    async def connect(): return _Conn(close_raises)
    async def no_sleep(_): return None
    awaiter = InboxAwaiter(connect=connect, drain=drain, sleep=no_sleep, budget_s=5.0, poll_interval_s=0.01)
    try:
        result = await awaiter.await_inbox(agent_id="a1", limit=10)
        return f"RETURNED entries={len(result.entries)} total_pending={result.total_pending}"
    except BaseException as error:
        return f"RAISED {type(error).__module__}.{type(error).__name__}: {error}"

print("CONTROL close ok   :", asyncio.run(run(False)))
print("CASE    close raise:", asyncio.run(run(True)))
```

### `audit66/probe_c10_query.py`
```python
"""C10 bound: does SDK 3.0.0 query() RAISE when a LATER statement fails (so run()'s first-statement answer cannot hide it)?
TEST store only; throwaway db in lore_test. CONTROL: an all-OK multi-statement answers one result per statement."""
import asyncio
from surrealdb import AsyncSurreal
URL = "ws://127.0.0.1:18000/rpc"; assert "18500" not in URL
CASES = {"CONTROL ok;ok": "RETURN 1; RETURN 2;",
         "later THROW": "RETURN 1; THROW 'later';",
         "later DDL error": "DEFINE TABLE c10a SCHEMAFULL; DEFINE FIELD x ON c10a TYPE int; CREATE c10a:1 SET x = 'not-an-int';",
         "txn later THROW": "BEGIN; CREATE c10b:1; THROW 'in-txn'; COMMIT;"}
async def main():
    db = AsyncSurreal(URL); await db.connect(); await db.signin({"username": "root", "password": "spikeroot"})
    await db.use("lore_test", "audit66_probe_c10")
    for label, sql in CASES.items():
        try:
            print(f"{label:18} -> RETURNED {await db.query(sql)!r}")
        except Exception as error:
            print(f"{label:18} -> RAISED {type(error).__name__}: {str(error)[:100]}")
    await db.query("REMOVE DATABASE audit66_probe_c10;") if False else None
    await db.close()
asyncio.run(main())
```

Mutation declarations: `audit66/mut/{r27,mp1,r34,t,fj}.{anchor,repl,expect,run}` + `DECLARED.sha256` (stamped before the runs).

## Receipts (my runs; each log starts with tree_id.sh unless stated)
| run | command (abridged; exact in log/instrument) | log | EXIT | count line | TREE |
|---|---|---|---|---|---|
| full currency (THE packet suite) | `flock … systemd-run … MemoryMax=16G … gate_keep_junit.py audit66/junit --currency -- --maxprocesses=12 -p no:cacheprovider` | `logs/currency_full.log` + `junit/junit_1.xml` | 1 | junit: 14777 tests, 532 failures, 71 skipped; CURRENCY FAIL (pytest RED_ORPHANED 2; typecheck RED_ADJUDICATED 99; ruff GREEN) | `9e0f3ada…` (graded) |
| c503bf7 four-file baseline | `build66/run_tree.sh build66/head_c503bf7 … 300 4 <lease_fates, forgery_door_sweep, no_raw_listener, text_hygiene>` | `logs/head_c503bf7_four.log` | 1 | 8 failed, 60 passed | no TREE (git-archive extract; `loremaster.__file__` inside it, SDK 2.0.0) |
| both-ways diff | `uv run python build66/reddiff_b66.py build66/logs/exit_head_c503bf7.log audit66/junit/full.log` | `logs/reddiff_audit_full.txt` | 0 | (a) 523/530, +7 all red at c503bf7 ⇒ identical | — |
| mutation full_jitter | `mut/run_mut.sh copies/c3 … loresigil/loresigil/backoff.py fj 300` | `logs/mut_fj.log` | 0 | 9 failed, 3 passed · PROOF HELD | `9e0f3ada…` |
| mutation R27-2a | `run_mut.sh copies/c1 … store/surreal.py r27 300` | `logs/mut_r27.log` | 0 | 2 failed, 3 passed · PROOF HELD | `9e0f3ada…` |
| mutation MP-1 | `run_mut.sh copies/c1 … index/indexer.py mp1 300` | `logs/mut_mp1.log` | 0 | 2 failed, 2 passed · PROOF HELD | `9e0f3ada…` |
| mutation R34 | `run_mut.sh copies/c2 … store/_txn.py r34 120` | `logs/mut_r34.log` | 0 | 14 failed, 45 passed · PROOF HELD | `9e0f3ada…` |
| mutation R41-T awaiter | `run_mut.sh copies/c2 … inbox_awaiter.py t 120` | `logs/mut_t_awaiter.log` | 0 | 4 failed, 26 passed · PROOF HELD | `9e0f3ada…` |
| replays ×12 + demo | `replay/runreplay.sh` (replay agent) | `replay/logs/wb_*.log`, `w5w6_demo.out` | 0 ×8, 4 ×4 (A4R1/A4scope extra reds; W5/W6 survival) | baseline 158 passed | `9e0f3ada…` before/after |
| rollup cursor probe | pytest on `test_zz_audit66_probe_rollup_cursor.py` in copy c1 (removed after) | `logs/probe_rollup_cursor.log` | 1 | the served-text leg FAILED (`reserved=True`), control passed (the file's `import *` also re-ran test_task_ledger's own nodes: 248 passed) | `9e0f3ada…` (header) |
| extra timing-set run | `build66/run_tree.sh <main checkout> … 300 8 <loop20_final SET>` | `logs/loop_extra_7cc5837.log` | 0 | 35 passed in 105.79s | `9e0f3ada…` (graded, DIRTY 0) |
| store probes | `probe_record_text{,_2}.py`, `probe_c10_query.py` (`:18000` only; probe DBs REMOVED after) | `logs/probe_*.log` | 0 | PASS w/ controls | — |
| R42 probe | `probe_r42_close_raises.py` (store-free) | `logs/probe_r42_close_raises.log` | 0 | control RETURNED 2 · case RAISED | — |
| R34 reach | AST instrument + grep | `logs/r34_reach_{ast,grep}.log`, `r34_rider1_sweep.log` | 0 | 12 = 12 | — |

Fan-out: haiku-runner 8 (full suite, c1/c2/c3 mutations, c503bf7 baseline, extra timing run). I checked each runner's RAN line against my command, and read every runner's EXIT and count line in the REAL log myself; two runners first reported their own wrapper log instead, and I re-read the named log. sonnet 2 (R22 draft, C-row/drop draft, each sampled). opus 2 (contract-blind reader, replay). Peak 4.
Lore: registered `audit-sdk3-66`; index currency checked at start (`/workspace` @ 7cc5837, no edits of mine); grep fallbacks (textual seams: R34 reach, close() reach, rider-1 sweep, prose) said out loud above; finding **#590** filed.
DONE · (report in hand-back) · NO-GO · currency pytest RED_ORPHANED 2 + served rollup-cursor regression (#590)


---

## §DELTA — re-check of the R43/R44 fix wave (graded `672b6d6`, range 7cc5837..672b6d6), measured 2026-11-08 ~21:00–21:45Z
**DELTA VERDICT: NO-GO, on ONE item: S1, a served false clause in the new h3 header, found by construction (R17).** Every other listed item PASSES, including the ONE full suite (currency PASS, RED_ORPHANED 0). A narrow fix closes it: re-word h3 and pin it once.
- Graded: 672b6d6 · HEAD-at-report: 672b6d6 · SAME (DIRTY 0, TREE `c070a3526d34…`). Directive #19126 drained and acked. Earlier receipts stand. Only the listed items were re-verified.
- Packages considered: none — no mechanism specified. Odoo-20 portability: n/a. Reuse ledger: none.
- **The blocker — S1 (h3, `AppContext._rollup_leg_header` vs `_rollup_next_cursor`):**
  - Every TRUNCATED leg serves `"(showing n of N — the next cursor resumes at the elision point, and the other legs re-serve their rows above it; …)"`.
  - When TWO legs are truncated, the cursor is the MIN over their `resume_at`. The non-MIN leg's header is then false twice: the cursor does not resume at ITS elision point, and ITS OWN served rows above the cursor are re-served, not only "the other legs'" rows. The same holds for a truncated leg beside a HELD leg, where the cursor = `since`.
  - **Reproduced by me** with the reader's store-free probe (`audit66/delta_r17_probes/probe_h3_two_truncated.py`, sha256 `252cdf46…`, log `logs/probe_h3_two_truncated.log`, TREE = graded). The task leg is truncated at HIGH and the finding leg at LOW; both headers carry the clause; `next cursor: 2031-05-06T07:08:09.186697100Z` = the finding leg's LOW. The live state is exactly page 1 of the #593 pin `test_truncated_cursor_is_the_earlier_sub_microsecond_stamp`, which never asserts the header.
  - Harm: an UNNAMED re-serve (duplicates; never loss). An agent that trusts the header and dedupes by leg would read the re-served task row as new activity. That is "wrong in a way the response did not name", so it is a defect under the brief's R17-first rule.
  - h3 is also pinned TWICE (S2: `H3_OTHER_LEGS_RESERVE` in `test_sdk3_rollup_ties_r15.py` + a literal in `test_mcp_server::…test_truncated_leg_header_shows_n_of_total_and_teaches_resume`), against the "pinned ONCE at the render" rider.
  - Fix direction (lead / operator wording call, D1): derive the clause per leg from `resume_at` vs `next_cursor`, or a leg-agnostic wording ("the next cursor resumes at the EARLIEST elision point across legs; rows above it in ANY leg are re-served"). One pin at the render, plus a two-truncated-legs case.

### Delta items, each verdict
| # | item | verdict | receipt |
|---|---|---|---|
| 1 | THE ONE full suite (same wrapper, flock, `MemoryMax=16G`, `--maxprocesses=12`) | **PASS**: typecheck RED_ADJUDICATED 99 (58 / 64b-i), ruff GREEN, pytest **RED_ADJUDICATED 530**, **RED_ORPHANED 0**, CURRENCY PASS, EXIT=0. junit 14795 tests / 530 failures / 0 errors / 71 skipped. Both-ways vs my 7cc5837 full junit (`reddiff_b66.py`): owned 530 = 530, build∖HEAD = 0, HEAD∖build = 0, other reds 0, green lost 0. **IDENTICAL.** Memory not sampled this run; the scope cap was not hit (no exit 137) | `logs/currency_full_delta.log`, `junit_delta/junit_1.xml`, `logs/reddiff_delta.txt` |
| 2 | B1 (#590) | **PASS.** Servicer pins green in the full suite (`test_sdk3_rollup_cursor_66b1` ×2, the in-process control, 7 dispatch pins). Its two declared mutations re-run BY ME in copy d1: parse→`fromisoformat` = 2/2 red, render→`isoformat()` = 7/7 red, both PROOF HELD. Lead-added wrong builds: **WB-B1a** (no plain-datetime handling) = exactly the epoch / zero-row pins red (2/2), and **WB-B1b** (`since` header left in µs) = exactly the 3 header pins red incl. `test_cursor_normalises_a_trailing_z`, both HELD. My own probe through PRODUCTION's codec: served `…189051048Z` → **reserved=False** (live + fake), while the retired-codec leg still re-serves (positive control). Servicer receipts `fixb1/mine/mut_real_m{a,b}.log` read: PROOF HELD | `logs/dmut_b1{p,r,a,b}.log`, `logs/probe_rollup_cursor_delta.log` |
| 2b | tie probe → #591 (RULING-15 / R44) | **PASS.** My mutation (`cut_stamp_page`'s tie branch → `if True:`) = **8/8 red across all THREE legs** (task ×2 + shrink + cross-leg, finding ×1, message ×2 + governed ×1), PROOF HELD, with 3 green controls (the distinct-stamp message leg, 2 sub-µs pins). Servicer receipts: RED@9f3922f (the pin commit's parent, before helper b2214d7) = 10 declared = observed (`r15/mine/main_red.log`); #593 pins RED on pre-R44 production = 2 = 2 (`r34b593/pre_r44.log`) | `logs/dmut_r44.log` |
| 3 | the two former orphans | **GREEN** in the full suite. B2: two evidence-backed `_EXEMPT_SITES` rows. `_listen_held` says `sock=` binds nothing (CPython `create_server` read) and has a trigger. `_relisten_same_port` cites the MEASURED 0.5–45 s window as a correction and keeps the loud-collision trigger. `start()` serves from a held `LoopbackPort`. **RULING-14 trigger replayed by me:** control (port free) → comes back on the SAME port; trigger (port taken during `go_down`) → `OSError errno=98 EADDRINUSE`, loud. B3: whitelist row with RULING-14's reason and a named third-literal bound | `logs/probe_b2_eaddrinuse.log` (`audit66/probe_b2_eaddrinuse.py`) |
| 4 | R-13 derived subset (4 OWED ADVERSARY4 builds) | **3 KILLED** (n_lm1_double_retry 140/140, n_lm1_scout_handloop 2/2, r_lm1_handloop 26/26, all PROOF HELD). **r_a3_floor16 SURVIVED** (737 passed): the SAME survival as round 3 and ADVERSARY4 (residual **R4-10, NO ROUND**), not a new door; the lead should confirm R4-10 still covers it. NOT-OWED byte-equality: r_b2_owner_slice's killing file `test_sdk3_record_ids.py` has sha256 `7b1f888c…` at b4e5c77 = 672b6d6 = adv4's on-disk tree, so **EQUAL** (r13_subset.txt names no sha; b4e5c77 = ADVERSARY4's graded commit assumed) | `delta_replay/REPORT-delta-replay-66.md`, `delta_replay/logs/wb_*.log` |
| 5 | #25 (RULING-14 §ADDENDUM) | **CONFIRMED.** Production schema + production-shaped ids, 303 F9 values + 21 traps. Mirror path vs id-range path set-equal BOTH ways and equal to the oracle over one/two/three(unicode) prefixes, `[max_codepoint]`, next-bound-is-max and the surrogate gap. EXPLAIN over an allowlist (sources {RecordIdScan, IndexScan, BitmapIndexScan}; wrappers {ProjectValue, Union, UnionIndexScan, BitmapOr, BitmapResolve, Filter}; deny-by-default) with firing controls: the X11 old-bug range fails set equality (+293 keys); two TableScan shapes REJECTED; a synthetic unknown operator REJECTED; the mirror path ACCEPTED. Owed-packet notes: `INDEX_SCAN_OPERATORS` lacks RecordIdScan (a ruling to add); F9's fixture seeds random ids; the bound builder must strip trailing U+10FFFF and skip surrogates | `delta_replay/logs/probe_c25_{confirm,supplement}.log` (FAILS=[], EXIT=0) |
| 6 | the production diff under R17 | **PASS except S1** (above). R22: 7 BUILDER commits = exactly the lead's list (fda1411 5b4c138 f2327ef b411cab d41aa47 b2214d7 273bb69), 15 SERVICER, 0 MIXED (my own path loop). Codec PASS (edge inputs refused loudly). R-6's 5 routes PASS (consistent with `keeps.keeper_id`). R34 clause true for a listing AND a single read (two-shape pins 2666ade cover `query_tasks` + `get_task` + finding `get`). Prose PASS (engine backticks non-word and all-digit keys; ULID bare; measured live). R-12: scout / briefs bounds docstringed with triggers; **`snapshot_gc` left unedited** (builder's reason recorded, not ruled: S3, LOW). R-9 logs: all exist and support their rows; **#34's log is well-controlled** (ns=372 stamp; the old codec re-serves as control; the codec excludes) | `REPORT-delta-r17-66.md` |
| + | lead-added checks | P4 asserts **h2-held**, not h1: PASS. h1 / h2 / h2-held pinned once; **h3 twice (S2)**. #592 h2: PASS (S5: false-CONSERVATIVE when the cursor holds, LOW). W6 pin `test_W6_a_directory_selector_keeps_owned_listed_reds_RED_ADJUDICATED`: passed in the full suite; W5 a named bound. `_stamp_page_fakes.py`: builds INPUT windows only, and no P1–P6 / #593 pin derives EXPECTED values from it (PASS). F3 footer safe-door rows: evidence-backed, trigger named (PASS). Window-model fields: every test double changed only in servicer commits (PASS). #593 sweep re-derived (grep, said out loud): no other site compares engine-ns stamps in Python (PASS). **#595 `TestHybridSearch::test_rrf_ordering_is_deterministic`: PASSED in the full suite** (one run; no STOP) | junit, `REPORT-delta-r17-66.md` |

### Delta residuals
| # | residual | owner | trigger |
|---|---|---|---|
| D-1 | **BLOCKING** S1: the h3 clause is false for a non-MIN truncated leg / beside a held leg; S2: h3 pinned twice | lead (wording, D1) → builder (render) + servicer (one pin + a two-truncated-legs case) | — (blocks GO) |
| D-2 | r_a3_floor16 survives (= R4-10, NO ROUND) | lead: confirm R4-10 covers it | any edit to the jitter window pins |
| D-3 | S3 R-12 `snapshot_gc` "no edit" not ruled; S4 R34 "the store's other rows are intact" over-claims under schema drift; S5 h2 false-conservative; S6 a refused message row names "(id unknown)" | lead (rulings / wording) | — (LOW) |
| D-4 | #25 owed-packet notes (RecordIdScan allowlist ruling; F9 production-shaped ids; bound-builder edge rules) | owed #25 packet | when #25's RETIRE is built |

### Delta receipts (mine; every log starts with tree_id.sh = graded TREE unless stated)
| run | log | EXIT | count |
|---|---|---|---|
| full currency at 672b6d6 | `logs/currency_full_delta.log` + `junit_delta/junit_1.xml` | 0 | CURRENCY PASS; junit 14795 / 530 failures (all owned) |
| both-ways diff | `logs/reddiff_delta.txt` | 0 | 530 = 530, ∅ both ways |
| B1 parse / render / WB-B1a / WB-B1b mutations (copy d1) | `logs/dmut_b1{p,r,a,b}.log` | 0 ×4 | 2/7 · 7/2 · 2/4 · 3/5 failed/passed, all PROOF HELD |
| R44 tie mutation (copy d2) | `logs/dmut_r44.log` | 0 | 8 failed, 3 passed, PROOF HELD |
| rollup cursor probe (production codec) | `logs/probe_rollup_cursor_delta.log` | 1 (the retired-codec control leg fails BY DESIGN) | codec legs reserved=False |
| B2 EADDRINUSE replay | `logs/probe_b2_eaddrinuse.log` | 0 | control same port / trigger errno 98 |
| h3 two-truncated-legs probe | `logs/probe_h3_two_truncated.log` | 0 | the false clause rendered on both legs |
| R-13 ×4 + #25 (delta-replay-66, copy d3) | `delta_replay/logs/` | 0 / 0 / 4 / 0; probe 0 | see item 4 / 5 |
Declarations: `audit66/mut/{b1p,b1r,b1a,b1b,r44}.{anchor,repl,expect,run}`, sha256'd in `mut/DECLARED.sha256` before the runs. Copies d1/d2/d3: `scratch_copy.sh`-verified at 672b6d6, `git status` clean after.
Fan-out (delta): haiku-runner 4 (full suite, d1 ×4 mutations, d2 mutation, the earlier c503bf7 run excluded) · opus 2 (delta-r17-66, delta-replay-66; both had Write refused, so I persisted their reports as `REPORT-delta-r17-66.md` and `delta_replay/REPORT-delta-replay-66.md` with provenance headers) · peak 4.

DELTA: DONE · NO-GO · everything re-verified passes (currency PASS, RED_ORPHANED 0; B1/R44 mutations HELD; #25 CONFIRMED) except S1 — the new h3 header's "resumes at the elision point / the other legs re-serve" is false for a non-MIN truncated leg (reproduced)

---

## §DELTA-2 — re-check of the R45/R46 fix (graded `88b06be`, range 672b6d6..88b06be), measured 2026-11-08 ~22:40–23:00Z
**DELTA-2 VERDICT: GO.** The §DELTA blocker #596 is closed by construction and by mutation. S2 / S4 / S3 / S5 are as ruled, and the S6 fix is in. R46 / #597 is a pinned bound whose pin and mutation hold. No second full suite was owed: the production diff is strings, docstrings and ONE projection token, verified by hunk, so §DELTA's full suite at 672b6d6 stands. Non-blocking residuals are listed below. The two that need a lead decision are the S6 class at 5 sibling sites and the #597 operator-visibility question.
- Graded: 88b06be · HEAD-at-report: 88b06be · SAME (DIRTY 0, TREE `6cd9b1537a37…`). Directive #19142 drained and acked. Packages considered: none. Odoo-20: n/a. Reuse ledger: none.
- **Both readings, written down (brief-base §2), of finding #598** (below): (a) strict R17, "any false clause in served bytes is a defect", gives NO-GO again. (b) R17 as defined, "an agent acting WITHOUT CHECKING cannot be wrong in a way the response did not name", gives GO, because the false clause only over-predicts re-serves, the actionable instruction is true, and the cursor value is printed explicitly. I pick (b). It is the third round on one header string, and the reach-attack STOP rule applies (the class recedes one level per round). This is the lead's to overturn.

| # | item | verdict | receipt |
|---|---|---|---|
| 1 | S1 (#596) | **CLOSED.** h3 is now RULING-16 §S1's one leg-agnostic string. My `probe_h3_two_truncated.py` re-run at 88b06be serves on BOTH legs "the next cursor is the earliest resume point of any leg, so rows above it in any leg, this one included, are served again next call: dedupe by task id or finding number…", cursor `…186697100Z`, so the clause is now TRUE for the non-MIN leg. P7 (`TestTwoTruncatedLegsServeOneTrueHeader`, live, with the re-serve walk) and P8 (`TestATruncatedLegBesideAHeldLeg`) are green (63 passed over r15 + 66d + `TestRollupDispatch`, copy e1). **Mutation** (restore the 672b6d6 h3 text, declared first) = exactly P7, P8, `TestShrinkAtTheCut` and the dispatch h3 pin red (4/4), PROOF HELD, restored | `logs/probe_h3_two_truncated_d2.log`, `logs/delta2_pins.log`, `logs/d2mut_s1.log` |
| 2 | S2 | **PASS**: ONE spelling. `H3_EARLIEST_RESUME` lives in `test_sdk3_rollup_ties_r15.py`, and `test_mcp_server` imports it (`from test_sdk3_rollup_ties_r15 import H3_EARLIEST_RESUME`). grep for the retired h3 text over `loremaster/tests` + `scripts`: 0 hits | grep |
| 3 | S4 | **PASS**: `required_datetime`'s tail is RULING-16 §S4's string, byte-for-byte ("…a store-integrity fault on that row, not a connection failure; this call could not be completed, and this read says nothing about other rows — report it with lore_findings"). It asserts nothing about other rows. The two-shape R34 pins (listing `query_tasks`, single reads `get_task` / finding `get`) are green on the new text | diff + `logs/delta2_pins.log` |
| 4 | S6 | **FIX PASS; the reach check finds the class open at siblings.** `message_activity_since` projects `id`, and the live pin (`TestARefusedMessageRowIsNamed`, ARRAY stamp per R45's accepted deviation) is green. The **one-off reach grep** (RULING-16 rider, said out loud: a grep fallback; Sonnet draft `audit66/S6-reach-draft.md`, I sampled 3 NO rows against the code) covers **33 call sites: 26 YES, 7 NO**. Two NO sites still NAME the row via a caller-supplied key (`floor_calibration/store.read_adopted_head` → `head_identity`; `memory/local` close-out → `memory_id`). **Five serve `(id unknown)`:** `keeps._row_to_membership` (member_of edge projection `in, out, rank, since`), `messages.awaiting_answer` (`thread, seq, created_at`), `messages._row_to_stored_message` via `messages_for_task` (its SELECT omits `id`; the stamp-page feeder is fixed), and `principal_keys.verify` ×2 (`name, revoked_at, expires_at, principal.email`). The served text is HONEST: the loud `(id unknown)` fallback names its own gap, as RULING-16 keeps on purpose, so this is not a false clear. It is S6's class at 5 siblings (fix-the-class), a residual for the lead | `audit66/S6-reach-draft.md` |
| 4b | the S6 pin's ARRAY stamp / 3.3.5's `> $since` type set | **CONFIRMED** (my probe, `:18000`, datetime controls on both sides + NONE): ADMITTED {array, object, record, uuid, datetime-after}; EXCLUDED {string, number, float, bool, null, duration, datetime-before, NONE}. Exactly the servicer's measured set | `audit66/probe_since_type_set.py`, `logs/probe_since_type_set.log` |
| 5 | S3 / S5 | **PASS**: `snapshot_gc._to_aware_utc`'s docstring carries RULING-16 §S3's named bound and re-open trigger verbatim (8289bc5, docstring-only). S5 unchanged, as ruled (RULING-16: a named bound) | diff |
| 6 | production diff scope + R22 | **PASS**: 5 BUILDER commits = the lead's list (8509e14 · a535d2e · f289f5b · 8289bc5 · d2df34c), 2 SERVICER (15a553f, de6e116), 3 DOCS, **0 MIXED** (my path loop). Hunks: two f-string literals (h3, R34 tail), docstrings (`_rollup_leg_header`, `_rollup_next_cursor`, `required_datetime`, `read_stamp_page`, `_to_aware_utc`), and one projection token (`id,` in `messages.message_activity_since`). **No full suite owed** | diff |
| 6b | builder receipts | **VALID.** Closing receipt `build66/logs/r46_target.log`: HEAD d2df34c, DIRTY 0, TREE `b49278661ce4…` = d2df34c's content (recomputed by `tree_of_commit.sh`), 28 failed / 692 passed. All 28 reds are in `test_mcp_server.py`, owned by packet 64b-i (registry at 88b06be). `r46_currency.log` (`--legs typecheck,ruff`): typecheck RED_ADJUDICATED 99, ruff GREEN, pytest NOT_RUN (the known `--legs` quirk), 0 orphans on the run legs. The R45 run `r45_target.log` (HEAD 8289bc5, TREE `927e7ddd…`, 530F/11298P) straddled `de6e116` + `c8cf105`, which are test / docs paths ONLY, and d2df34c→88b06be is docs-only, so production was unchanged mid-run | `build66/logs/r4{5,6}_*.log` |
| 7 | R46 / #597 | **PASS (a pinned bound).** The pin-the-miss `TestANonDatetimeStampIsOutsideEveryLeg` (task + finding) exists, is green, and fails ONLY through `_KNOWN_BOUND_597` ("this is a KNOWN BOUND (#597) — … if you closed it deliberately, delete this pin and say so"). **My mutation** (widen the leg's row predicate to `(col > $since OR col != NONE)` so the string row is SEEN) = exactly the 2 pins red, PROOF HELD, restored. `read_stamp_page`'s docstring states the predicate ONCE with triggers. d2df34c is docstring-only (+13). RULING-17's un-probed sub-case, **closed by me:** a SCHEMAFULL `option<datetime>` column REJECTS a literal `NULL` (control: a string is rejected too), and Python `None` via the SDK stores NONE | `logs/d2mut_r46.log`, `audit66/probe_option_datetime_null.py`, `logs/probe_option_datetime_null.log` |
| 7b | #597 under R17 ("construct a string-stamp dirty row; the rollup must not serve the healthy idle bytes, or the ruled bound is named") | **The bytes ARE identical** to a healthy idle rollup for a leg whose only rows are string-stamped (the pin constructs it live: rows and `total` both omit the row). The bound is named in the docstring and the pin, **not in served text**. This is accepted as RULING-17's pinned bound: unreachable through every production write, by construction (re-confirmed: the type set above + the NULL leg), with re-open triggers. ⚠ R46 records "adopted by the lead", while RULING-17 itself says "the operator rules; this recommends". An accepted consumer-invisible state is the kind of trade the operator may want to see | pin + docstring |
| — | #598 (new, LOW) | The R45 h3 clause "the next cursor is the earliest resume point of any leg" is false beside an UNTRUNCATED or empty leg, because `_rollup_next_cursor` takes the MIN over TRUNCATED legs only. Constructed: task truncated at HIGH, finding untruncated with a row at LOW, so `next cursor:` = HIGH. The false belief only OVER-predicts re-serves; the actionable clause is true. One-word fix: "of any truncated leg". Reading (b) above: non-blocking | `audit66/probe_h3_one_truncated_earlier_untruncated.py`, `logs/probe_h3_one_truncated.log`; finding #598 |

### DELTA-2 residuals
| # | residual | owner | trigger |
|---|---|---|---|
| E-1 | S6's class at 5 sibling sites: `(id unknown)` served by `keeps._row_to_membership`, `messages.awaiting_answer`, `messages.messages_for_task`'s mapper feed, `principal_keys.verify` ×2. Honest, not a false clear | lead: fix-the-class (one projection token each) or a named bound | the next edit to any of those SELECTs |
| E-2 | #597 accepted as a consumer-invisible pinned bound by LEAD adoption; RULING-17 says the operator rules | lead → operator visibility | RULING-17's triggers (a stamp retype; SCHEMALESS / `TYPE any`; an untyped import door) |
| E-3 | #598 h3 "any leg" over-broad (LOW, consequence-free) | builder, at the next touch of `_rollup_leg_header` | — |
| E-4 | carried: r_a3_floor16 = ADVERSARY4 R4-10 (settled by the lead, per RULING-16 §Shape); #25 owed-packet notes | as before | as before |

### DELTA-2 receipts (mine)
| run | log | EXIT | count |
|---|---|---|---|
| DELTA-2 pin files, copy e1 at 88b06be (`run_tree.sh … r15 + 66d + TestRollupDispatch`) | `logs/delta2_pins.log` | 0 | 63 passed |
| S1 mutation (restore the 672b6d6 h3) | `logs/d2mut_s1.log` | 0 | 4 failed, 11 passed · PROOF HELD |
| R46 mutation (leg sees the string row) | `logs/d2mut_r46.log` | 0 | 2 failed, 11 passed · PROOF HELD |
| h3 probes (two truncated; one truncated + earlier untruncated) | `logs/probe_h3_two_truncated_d2.log`, `logs/probe_h3_one_truncated.log` | 0 | rendered as quoted |
| `> $since` type-set probe | `logs/probe_since_type_set.log` | 0 | CONTROLS PASS |
| `option<datetime>` NULL probe | `logs/probe_option_datetime_null.log` | 0 | NULL rejected; None → NONE |
Declarations: `mut/s1.*`, `mut/r46.*`, sha256'd in `mut/DECLARED.sha256` before the runs. Copy e1: `scratch_copy.sh`-verified at 88b06be, clean after. Store probes: `:18000` only, throwaway databases REMOVED. Fan-out: haiku-runner 1 · sonnet 1 (S6 reach draft, 3 rows sampled) · peak 2.

DELTA-2: DONE · GO · #596 closed (P7/P8 green, mutation HELD; h3 true for both legs); S2/S3/S4/S6 as ruled; #597 pinned bound (pin + mutation HELD, NULL sub-case closed); residuals: S6 class at 5 sibling sites, #597 operator visibility, #598 h3 "any leg" (LOW)
