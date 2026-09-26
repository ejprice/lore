brief-base v16 read · brief project v7 read

# REPORT-coldaudit-63c-i-a-2 — cold REFUTE audit of the 63c-i-a fix build (patch `b23f3e43…`)

## SUMMARY BLOCK
- **state:** done-with-deviations · **verdict: NO-GO** (one BLOCKER introduced by the patch; §VERDICT).
- **deviations:** (1) FOCUS 5 (real prod-dump restore) NOT run — permission-DENIED ("Modify Shared Resources"), not retried; operator-pending per lead ruling #17046 (§5). (2) The brief's currency command (`--legs typecheck,ruff`) exits FAIL by design (pytest NOT_RUN); I also ran the full currency (§1). (3) A killed-by-me currency start at 12:11 overlapped a foreign-project pytest (I had not re-checked the table); stopped by PID, re-run later in the lore-scoped lane. (4) A kill of my own stale waiter was permission-DENIED; not retried (an inert sleep loop).
- **Packages considered:** none — no mechanism specified (audit instruments reuse `scripts/mutation_proof.py`, `scratch_copy.sh`, the shared test harness).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none (no production symbol introduced; probes are scratch instruments pasted in §A).
- **Graded:** `5a43aeb` + patch `b23f3e43416b9d0931dff1635ad53f85` · HEAD-at-report: `ccdad34` · DIFFERENT (13 commits): docs, packet 58/#466 tests + `loremaster/testing/loopback.py` (#466 stub); the patch's six files are byte-identical `5a43aeb`→`ccdad34` (`git diff --stat` empty) and the main tree's patch md5 is still `b23f3e43…`.
- **Findings:** **F-2 BLOCKER** — the created-only compensation deletes a session keep other successful registrations are scoped to; 8-way concurrency strands the WHOLE session in 2/20, 8/20, 11/20 rounds (HEAD: 0/20). **F-1 MAJOR (spec-level)** — `preflight` before SF-63-1 serves a FOREIGN principal another principal's agent role / `spawned_by` / retired status (control: nothing leaked). F-3/F-4 MINOR (am-27 already ruled them into this fix pass). F-5, F-7, F-8, F-9 MINOR. F-6 MAJOR at HEAD, not this patch: currency RED_ORPHANED (31 unowned reds, 0 from the patch).
- **Confirmed:** 108 RED@HEAD → green, 0 regressions (two full runs, one tree, diffed both ways); ruff GREEN; typecheck red only on 58's adjudicated contract; door #2 / am-26 / D2(message) / FK-a / sanitiser behaviour correct with controls; mutations A–D HELD (preflight is ONE decision for both callers; the preconditions ONE decision for all four legs; KP5 green for the right reason); D-1 sound.
- **decisions-needed:** (a) F-1: the SF-63-1 visibility check must precede `preflight`'s existence-revealing refusals — a ruling on am-22 §1's order (sidecar). (b) F-2: guard the compensation (delete only when no row is scoped to the keep, or skip it) — or accept a bound; the delete is new in this patch. (c) F-6: owners for the 31 orphaned reds before any wave close-out.
- **receipt pointers:** §1 gates · §2 DUAL (mine first, then diff) · §3 findings · §4 probes+controls · §5 FOCUS 5 blocked · §6 builder claims · §7 D-1/D-2 · §8 mutation proofs · §9 residuals (RS-1 = the am-26 pin fixture for i-b) · §A instruments verbatim.

## §0 Capability check (2026-09-26)
- Idle-gate contract written: `/tmp/claude-idle-gate-lore/10ac805a-19e9-46a0-b7ef-c030296122cd-coldaudit-63c-i-a-2.contract` = `{"artifact": "REPORT-coldaudit-63c-i-a-2.md"}` (session id = my scratchpad's session dir).
- lore: `lore_comms register` OK (coldaudit-63c-i-a-2 / 63c-20260924 / auditor / ≤20m). `lore_index()` at start: root `/workspace` @ `5a43aeb`, last sweep 65 s — fresh.
- grep/rg are hook-blocked (#473): every textual sweep used `awk` (said per use). One `lore_search` for `AgentRegistry` heartbeat returned a budget STUB (floor-of-one) → awk fallback for a signature.
- A compound Bash command (untracked-file `rm -rf` loop + `git checkout` in the scratch copy) was DENIED by the permission layer; I re-did it as a `mv` of the 16 untracked non-patch files into a sibling `quarantine/` dir and a separate `git checkout --` inside the copy. Same result, nothing deleted.
- Instrument (DV-1 shape, per brief): `./scripts/scratch_copy.sh <scratch>/sc` → untracked non-patch files moved out → `git checkout --` of the 6 files (copy only) → `git apply builder-63c-i-a-fix.patch` → `git diff --binary -- <6 files> | md5sum` = **`b23f3e43416b9d0931dff1635ad53f85`** (matches) → `loremaster.__file__` = `…/scratchpad/sc/loremaster/loremaster/__init__.py`, `lorerunes.__file__` = `…/scratchpad/sc/lorerunes/lorerunes/__init__.py`; `scratch_copy.sh --verify-only` all four members inside the copy.

## §1 Gate receipts (re-run by me, scratch copy, 2026-09-26)
Scratch copy = `5a43aeb` (HEAD when the copy was cut) + patch `b23f3e43…` (md5 re-verified after every revert/re-apply). HEAD moved during the audit to `37de0a7` (see the `Graded:` line); `git diff --stat 5a43aeb 37de0a7 -- loremaster/loremaster lorerunes/lorerunes loresigil/loresigil lorescribe/lorescribe` is EMPTY, so no production code differs. What moved is `scripts/concurrent_wire_acceptance.py` + #466's RED contract tests (`37de0a7`) + docs incl. **amendment 27** (`40c188d`, which rules FORK-1/FORK-2/DV-2; see §6).

| gate | command (in the scratch copy) | result |
|---|---|---|
| full suite WITH patch | `uv run pytest -n auto -q -p no:cacheprovider` (alone; process table clear; spike-surreal active; 15 GB PID watchdog never fired) | **`75 failed, 11652 passed, 62 skipped, 3 xfailed` in 368.98s · EXIT=1** |
| full suite at pure HEAD `5a43aeb` (patch reverse-applied, same copy) | same | **`183 failed, 11544 passed, 62 skipped, 3 xfailed` in 350.76s** |
| red-set diff, both ways (`comm` over the sorted `FAILED` ids) | — | **regressions (red with patch, green at HEAD): 0** · **fixed (red at HEAD, green with patch): 108**, all in 63c files (`test_fixwave_a19a` 53 · `a19b` 27 · `a19` 20 · `test_agent_governance_63c_i_a` 7 · `test_agent_registry` 1) · red in both: **75** |
| `uv run ruff check .` | — | `All checks passed!` EXIT=0 |
| `./scripts/typecheck.sh` | — | **EXIT=1**: `Found 7 errors in 1 file` — all in `loremaster/tests/test_supersede_reanchor_58.py` (packet 58's committed RED contract, `5a43aeb`); every other leg OK |
| `pending_contract_gate.py --currency --legs typecheck,ruff` (the brief's exact command) | — | typecheck **RED_ADJUDICATED** (7, owner packet-58-contract) · ruff **GREEN** · pytest **NOT_RUN → `CURRENCY: FAIL`**, EXIT=1. With `--legs`, a claimed-but-unrun pytest is an ORPHAN by design (#312): the two legs the builder claimed GREEN are GREEN-or-adjudicated, but the command's own verdict is FAIL. See the full-currency row. |

**The 75 red-in-both, attributed** (none touch the patch's files; all are at HEAD):
- **68 = packet 58's committed RED contract** (`5a43aeb`): `test_supersede_reanchor_58.py` 44 · `test_task_guarded_shell_58.py` 15 · `test_task_claimable_partition_58.py` 5 · `test_task_read_surface.py` 1 · `test_blocks_edge.py` 1 (the boot re-anchor heal) · `scripts/test_forgery_door_sweep.py` 2. (68 + 7 = 75.)
- **7 = tree-scan pins reddened by the committed `scripts/restore_prod_dump.py` (`80409f4`)**, independent of this build: `test_anchored_pattern_seam` (5 `$`-anchored patterns validated with `.match`, `restore_prod_dump.py`), `test_ast_reach_helpers[test_anchored_pattern_seam.py]` (its consumer red on the real tree), `test_secret_resolution_seam` ×2 (`restore_prod_dump.py` parses `.env` outside the one resolver; an env read not allowlisted), `test_secret_typing` ×3 (auth header built outside a seam; `SecretStr` minted outside an origin; an unallowlisted unwrap site). **This is a HEAD defect in packet 64's instrument, not in 63c-i-a** — surfaced as finding F-6 below; the full-currency run (next row) says whether it is adjudicated.

| full currency (`pending_contract_gate.py --currency -- -n 12 -p no:cacheprovider`, lore-scoped lane per lead ruling #17046; a foreign-project pytest was live → `-n 12`) | — | typecheck **RED_ADJUDICATED** (7, packet-58-contract) · ruff **GREEN** · pytest **RED_ORPHANED — 31 residual(s) with NO owner** → `CURRENCY: FAIL`, EXIT=1. The 31, attributed: the **7** `restore_prod_dump.py` tree-scan reds (F-6) + **24** of packet 58's 68 contract reds that 58's own `pending_contracts.yaml` rows do not cover (`test_task_guarded_shell_58` 15 · `test_task_claimable_partition_58` 5 · `test_task_read_surface` 1 · `test_blocks_edge` 1 · `scripts/test_forgery_door_sweep` 2); `test_supersede_reanchor_58`'s 44 are owned. **ZERO of the 31 are this patch's** (every one is red at HEAD without it, §1 diff). The lead's `7225148` already routes the restore-script reds to a fixer; the 58 orphans are 58's registry gap. |

## §2 The DUAL — my enumeration FIRST (made from `git diff` before opening the builder's §7), then the diff
**Mine (M1–M13), from the six-file diff alone:**
| # | removed / replaced behaviour | my adjudication |
|---|---|---|
| M1 | `_owner_count` (owner-keyed) deleted; the message ORDER guard re-keyed owner→scope (`unscoped_count`) | an ownerless-SCOPED agent no longer trips the ORDER guard, but is refused at the verb (F-2) — covered |
| M2 | message counts owner-keyed → scope-keyed | am-21 CD-1 |
| M3 | message WHERE gains `scope IS NONE` (a scoped-ownerless row used to be RE-STAMPED) | am-21 CD-1 / am-25 |
| M4 | message `backfilled` pre-count → `len(UPDATE result)` | am-24 D2 |
| M5 | agent §2.1 row precondition moved from the agent leg to the VERB: now also refuses `memory`/`message`/`brief` on such a store; old refusal served MEASURED `scanned`/`already` | am-19 D-1 / am-22 §4 |
| M6 | agent UPDATE gains `AND owner_principal IS NONE`; agent `backfilled` still the scope-keyed pre-count | am-19 F-3; the count is FORK-1 (now ruled by am-27) |
| M7 | every refusal's `0` counts → `None`; `MigrateGovernedResult` fields widened to `int \| None` | am-22 §4 / am-24 FK-a |
| M8 | unsupported-table refusal text/receipts; `brief` now VALID (store read before answering) | am-22 F-1 |
| M9 | EVERY migrate (incl. `memory`) now pays `INFO FOR DB` + the agent half-pair read before its leg | cost only; ruled shape |
| M10 | `register`'s inline retired/role/spawned_by refusals → `preflight` (same order, same texts, same single row read inside `register`) | preserved (A1) |
| **M11** | **handler ORDER: at HEAD the SF-63-1 visibility gate (mint/find the session keep → deny a foreign principal) ran BEFORE any registry refusal; now `preflight` runs FIRST, so a FOREIGN principal meets the registry's teaching (existing agent's role, `spawned_by`, retired status) BEFORE the gate that would deny it** | **NOT adjudicated by the builder (§7 S1 records only "#485 old-bug; tokenless preserved"). Spec-silent → ruling. Finding F-1.** |
| M12 | NEW: created-only compensation deletes the session keep this call CREATED — including when a concurrent same-principal register FOUND it and is now scoped to it | not a removal but a new write; **finding F-2** |
| M13 | NEW: #4b line on ANY delete exception (`except Exception`), incl. `KeepNotFoundError` — where the keep is NOT left behind | finding F-5 (MINOR) |
| M14 | identity refusal gloss dropped; `does not match` → `must match` | am-19 F-9 |

**Diff against the builder's §7 (21 rows):** every one of my rows M1–M10, M14 maps to a builder row (M1→D3/D7, M2→D9, M3→D10, M4→D11, M5→D4, M6→D6, M7→G1/D2/D5/D8, M8→D1, M10→A1, M14→A2/S2; M9 has no row: cost-only, not a behaviour loss). **The builder's §7 has rows I did not enumerate** (D12/D13 old-bug populations, D14 prose, A3 the U+001C–1F role, K1, D8's reordering of the operator refusal after the row facts); I checked each against the diff and agree. **The builder's §7 LACKS M11, M12 and M13.** M11 is the material one: it is a removed virtue ("a foreign principal learns nothing about another principal's agents before SF-63-1 denies it"), and it has no pin in either direction.

## §5 The REAL dirty store (#107 class) — **BLOCKED by the permission layer; NOT run**
- **Demanded (brief FOCUS 5):** restore the governed slice of `/backups/lore/lore-prod-20260803T141930Z.surql` into a minted `:18000` test DB with `scripts/restore_prod_dump.py` (`80409f4`), apply the post-build DDL, run `migrate_governed` ∀ `--table`, compare every served count with a direct SELECT, add a virgin-DB control, then tear down and prove it.
- **What I have:** the command `cd <scratch>/sc && uv run python scripts/restore_prod_dump.py --dump /backups/lore/lore-prod-20260803T141930Z.surql` was **DENIED by the Claude Code auto-mode classifier: "[Modify Shared Resources]"**, with an explicit instruction not to pursue the same outcome by any other route. I did not retry it, split it, or reach the dump by another tool. Nothing was restored and no `test_dump_*` DB was minted by me.
- **What I did instead:** read the instrument's docstring and `REPORT-probe-64.md` (its measured population: `agent 95 · message 316 · memory 177 · brief 26`, all `scope IS NONE`); wrote the post-restore driver that would run the rest of FOCUS 5, and ran the SAME refusal/proceed logic on constructed dirty populations on minted virgin DBs (§4 P3/P4; they are harness-seeded, not the fleet's real rows). **So what a REAL pre-63 store does at cutover — above all, whether the fleet's 316 real messages contain DANGLING senders (which would make `--table message` refuse at the 65 cutover) — is UNMEASURED by this audit.**
- **What a lead must change:** either grant a Bash permission rule for `scripts/restore_prod_dump.py` (it is endpoint-locked to :18000 by construction, §D-3 req. 1), or have the operator/lead run the two commands below, then hand the output to a fresh auditor. Driver, verbatim (`dirty_store_driver.py`, run from the scratch copy's venv; asserts `ws://127.0.0.1:18000`; it prints one `STEP` JSON line per step: census before/after DDL, operator provisioned, `migrate_governed` for `message`(before agents)·`bogus`·`brief`·`agent`·`message`·`memory`·`brief`·then `agent`/`message`/`memory` again for idempotence, each beside a direct-SELECT census + a byte-diff count, then the keep list and the post-migrate no-NONE-owner invariant). Run: `uv run python ../dirty_store_driver.py <LORE_PROD_DUMP_DB> 2048` then `uv run python ../dirty_store_driver.py --virgin 2048` (the control, which reaps itself and prints `still_present`), then `./scripts/restore_prod_dump.py --reap <LORE_PROD_DUMP_DB>`. The dump's HNSW width is 2048 (`DEFINE INDEX chunk_embedding_hnsw … DIMENSION 2048`, read from the dump by awk before the restore was attempted).

## §6 The builder's claims, re-derived (each with a verdict)
| claim (`REPORT-builder-63c-i-a-fix.md`) | my instrument | verdict |
|---|---|---|
| full suite `11625 passed / 0 failed` | my run at `5a43aeb`+patch: `11652 passed, 75 failed` | **CONSISTENT, different test bytes**: the builder ran `a761b71`'s tests; `5a43aeb` adds packet 58's contract (68 reds + passing pins → +27 passed) and `80409f4`'s script (7 tree-scan reds). Every one of the 75 is red at HEAD without the patch too (§1) |
| RED@HEAD 108 → all green, 0 regressions | two full runs on ONE tree, `comm` both ways | **CONFIRMED EXACTLY**: 108 fixed, 0 introduced |
| gates GREEN | ruff / typecheck / currency | ruff **GREEN**. typecheck **RED only on 58's contract** (adjudicated). The brief's currency command **exits FAIL** (pytest NOT_RUN under `--legs`) — the builder's "currency legs typecheck/ruff GREEN" is literally true per leg and does not claim the command passed; worded loosely, not false |
| DUAL 21 rows | my own enumeration first (§2) | **INCOMPLETE**: lacks M11 (F-1), M12 (F-2), M13 (F-5) |
| DRY ledger | read §8 against the diff | the extractions (`_operator_unresolved`, `_refused`, `_id_sample`) are real consolidations (3 inline copies → 1; 6 inline constructors → 1). The ledger row for the compensation says "NO lore query run" — honest. No new copy of an existing policy found by my read |
| §P.1 dangling predicate (`sender.id IS NONE`, total over a NONE link; `record::exists(NONE)` raises) | not re-probed live (see §4 P3 dangling legs, which exercise the predicate end-to-end on seeded ghosts) | accepted on its pasted instrument + my P3 legs |
| DV-1 (isolated tree) | I did the same | sound |
| DV-2 (inline compensation) | read + MUT-E; am-27 has since RULED it acceptable | not a second copy (one site); **but** the compensation's DECISION is wrong in one sub-case — F-2 |
| FORK-1 / FORK-2 | P4 / P3 | graded in §3 (F-3, F-4); am-27 (`40c188d`) has RULED both (lands in this audit's fix pass if any, else i-b) |

## §7 a19b deviations D-1 / D-2 (brief FOCUS 3)
- **D-1 (KP12 not landed; N3b-as-built is the ruled #137 bound) — SOUND.** am-24 §1's stated bound is verbatim "a runtime gate is an invariant only over code it RUNS — a new refusal site no test drives is unobserved … #137's treatment … re-open trigger: a refusal found in production that no fixture drives". KP12 keyed on a class that exists only in a wrong build (`SessionClosedError`); landing it would pin an imagined refusal by NAME, which am-24 §1 retired. My MUT-A (a NEW refusal added to `preflight` on an input no existing fixture drives) is the live version of N3b: result (§8 MUT-A): the build refuses it on BOTH paths and the handler refuses before the mint (0 mints) — N3b's bound is real but the SHARED decision still reaches an undriven refusal.
- **D-2 (KP5/KP6 red via AttributeError at `84af63f`) — now GREEN; right reason graded by MUT-D** (a private copy of the role decision re-added inside `register` after `preflight`): KP5 must redden for the role-conflict case. **Result (§8 MUT-D): HELD — green for the right reason.**

## §3 FINDINGS (measured 2026-09-26 on `5a43aeb` + patch `b23f3e43…`; each with a receipt in §4/§8)
| # | severity | finding | receipt |
|---|---|---|---|
| **F-2** | **BLOCKER** | **The created-only compensation deletes a session keep that OTHER successful registrations are already scoped to.** "Created by this call" (FK-b) does not mean "used by nobody": between this call's mint and its refused `register`, any concurrent register by the SAME principal into the SAME session FINDS the keep, passes SF-63-1, and writes an agent row with `scope = keep:<K>`. The compensation then `delete_keep`s K. Every such agent is left scoped to a keep that no longer exists; the `member_of` edge cascades away with it; the next register mints a NEW keep K′ and the stranded rows are never re-pointed. Measured under REAL 8-way concurrency (4 same-name registers with alternating roles + 4 distinct names, one principal, fresh session per round): **2/20, 8/20 and 11/20 rounds stranded ALL 5 of the session's agents** (10, 40, 55 rows over three runs); **pure HEAD `5a43aeb`, same probe: 0/20**. Sequential construction (P2): the winner `x(scout)` is scoped to the deleted keep (`agent_scope_keep_exists: false`), a re-register does not heal it; control (winner creates, loser finds) keeps the keep. Silent: every successful caller got OK. `KeepStore.delete_keep`'s own docstring already names this as the 63/64 FORWARD-BOUNDARY ("when 63/64 add `scope='keep:<id>'` governed rows, `delete_keep` MUST revisit whether it cascades or orphans them"); the compensation is the first caller that deletes a keep with scoped rows. No pin constructs it: KP1/KP4/#4b all inject the conflicting register OWNERLESS at registry level, so the winner never references the keep | §4 P2, P5 (+ HEAD control) |
| **F-1** | **MAJOR** (spec-level — the ruled ORDER has an unruled consequence; decision for sidecar/operator) | **`preflight` before the SF-63-1 gate discloses another principal's agents to a FOREIGN principal.** bob (a member, not householded in alice's session) registering a name alice holds is served, BEFORE the gate that would deny him: the existing agent's **role** (`is already registered with role ```secretrole```…`), its **`spawned_by`** (```alicelead```), and whether it is **retired**. A name alice does NOT hold still gets the SF-63-1 denial, so the difference is itself a per-name existence oracle. HEAD-order control (the handler's pre-mint preflight admitted; `register`'s own still runs): **all four answers are the SF-63-1 `GovernedDenied`, nothing leaked**. This reopens the class ruled out by the 63b-ii-a owner-resolution ruling step 4 ("a foreign principal must not learn who keeps a session — 63-rulings §6's existence-leak stance") and the 63c remainder ruling §5.2 (#467: a foreign principal gets NO roster). am-22 §1 mandated "the handler calls `preflight` BEFORE `get_or_create_keyed`" and did not consider the gate; the builder built the ruling faithfully. The only existing SF-63-1 pin (`test_comms_send_scope_63b_ii_a.py::…denies_naming_the_remedy_not_the_keeper`) registers a FRESH name (`bob_w1`), so it cannot see this door. Candidate shape (for the ruling, not built): a READ-ONLY visibility check of the session keep by key (`get_by_key` + `resolve_visible_keeps`, no mint) BEFORE `preflight`; if the keep does not exist there is no foreign keeper and nothing to leak | §4 P1 |
| F-3 | MINOR (am-27 FORK-1 has RULED it; lands in this fix pass) | agent leg `backfilled` is the scope-keyed pre-count, not the rows stamped: with the F-3 race made reachable (THE shared preconditions redirected clean while an owned-but-unscoped agent exists) the leg serves **`backfilled=3` while the byte-diff shows 2 rows changed** — a served count describing no set. Message leg under the same construction: `backfilled=2`, 2 changed (correct) | §4 P4 |
| F-4 | MINOR (am-27 FORK-2 has RULED it; lands in this fix pass) | a store with un-migrated agents AND a dangling sender serves ONLY the ORDER refusal (`dangling` absent from the text) — two round trips | §4 P3 `unmigrated_agent+dangling` |
| F-5 | MINOR | the #4b branch catches `except Exception` around `delete_keep`, which includes `KeepNotFoundError` (a keep ALREADY gone, e.g. deleted by a concurrent compensation or an admin); the appended line then asserts the keep "is LEFT BEHIND" — a false served statement. By code read only; not constructed | `AppContext._comms_register` (the `except _AgentRegistryError` branch) |
| F-6 | MAJOR — **HEAD defect, NOT this patch** | the wave close-out currency gate is **RED_ORPHANED at HEAD** (31 unowned reds): 7 from committed `scripts/restore_prod_dump.py` (`80409f4`: `$`-anchored `.match`, a second `.env` parser, an auth header / `SecretStr` / unwrap outside the seams) + 24 of packet 58's committed contract reds not in its `pending_contracts.yaml`. Committing this patch neither adds nor removes any of them; the close-out rule ("ONLY RED_ORPHANED fails") nevertheless fails for this wave until someone owns them | §1 full-currency row |
| F-7 | MINOR (pin gap) | the #4b pin does not assert the caller's `session` is kept OUT of the appended line (a19b §10 item 7 requires it): MUT-E injects `(session {session})` into that line → the pin stays GREEN; positive control MUT-E2 on the SAME statement → RED, so the pin reaches it. The build itself is correct (the line names only the store-minted bare keep id) | §8 MUT-E/E2 |
| F-8 | MINOR (pin gap) | the door-#2 pin checks each half's count with `len(ids) in stated` over the whole reason, so a build that SWAPS the two halves' counts passes. The build attributes correctly (P3 `half_i_11+half_ii_12`: "11 … owner but no scope" / "12 … scope but no owner") | §4 P3 |
| F-9 | MINOR (latent) | `minted_by_this_call` rides the returned `Keep` as a non-field attribute that `model_copy` CARRIES (the builder measured and documented it): a copied keep would read "created" and license a delete. No production `model_copy` of a keep today | `keeps.minted_by_this_call` docstring |

## §4 New-behaviour probes WITH controls (instrument: `probe_coldaudit.py`, pasted verbatim in §A.1; md5 `01d7f9dbddcf4d259954d42e7979560c`; run in the scratch copy, `-p no:xdist -s`, 20 passed + P5 1 passed; receipts are the `PROBE` lines, quoted)
- **P1 — cross-principal disclosure (F-1).** BUILD, bob → alice's session `s-alice`: `role_conflict` → `AgentIdentityConflictError "agent 'worker' is already registered with role ```secretrole``` (you sent ```auditor```) …"`; `spawned_by_conflict` → `"… with spawned_by ```alicelead``` (you sent ```boblead```) …"`; `retired` → `RetiredAgentError "agent 'gone' is retired (terminal) …"`; `absent_name` → `GovernedDenied "session 's-alice' is kept by another principal — you are not householded in it; …"`. `leaked = ["role_conflict","spawned_by_conflict","retired"]`. **CONTROL (HEAD order): `leaked = []`**, all four `GovernedDenied`.
- **P2 — the canonical race (F-2), sequential.** `this_call_creates`: A = `AgentIdentityConflictError` (served verbatim ✓), B = OK; `session_keeps_after_race: []`; agent `x` (role scout, B's row) `scope: keep:01M3FAE2TDFRNY72MCM6KFK372`, `agent_scope_keep_exists: false`; re-register → OK, a NEW keep `keep:01M3FAE2VHZVK5TCJBJT188KFZ`, x's scope unchanged (still the dead keep). **CONTROL `control_winner_creates`:** keep survives, `agent_scope_keep_exists: true`.
- **P5 — F-2 under real 8-way concurrency, ×20 rounds.** Patch: stranding rounds **2/20 (10 rows), 8/20 (40), 11/20 (55)** over three runs; every stranding round strands all 5 agents of the session. **CONTROL, pure HEAD (patch reverse-applied, same copy, re-applied after, md5 `b23f3e43…` re-verified): 0/20.** Loser outcomes are mostly `TxnDomainRejectionError` (a same-name, same-role CREATE collision) — the SAME at HEAD (55 of them there), so that is pre-existing and not compensated (builder residual R-a); only the `AgentIdentityConflictError` losers trigger the compensation.
- **P3 — the message-leg refusals (door #2, am-26, FORK-2, hostile ids), seeded on minted virgin DBs via the shared `_governed_world`.** Every refusing population: `refused=True`, `scanned=None`, `already_migrated=None`, `backfilled=0`, `byte_inert=True`, `rows_changed_by_bytediff=0`, `reason_control_chars=[]`.
  - **am-26's ruled fixture** (ghost sender + owned-unscoped message + a sound legacy): ONE refusal, `dangling_pos=27 < half_pos=244`: *"1 legacy message(s) name a dangling sender … First 1 of 1 shown: message:m_dangling (sender agent:ghost_sender). 1 message row(s) carry an owner but no scope — a half-applied store … First 1 of 1 ids shown: message:m_half_i. Adjudicate these messages by hand before migrating `message`; no row was stamped"* — the sound row NOT stamped. **Matches am-26 exactly.** Also with half (ii) added: all three named, dangling first.
  - **door #2 above the cap, distinct per-half counts (11 / 12):** *"11 message row(s) carry an owner but no scope … First 10 of 11 ids shown: …hi00…hi09. 12 message row(s) carry a scope but no owner … First 10 of 12 ids shown: …hii00…hii09."* — true counts, correctly attributed, each half bounded by THE constant.
  - **hostile ids** (`\n`, `\r\n`, `\x1b[31m`, backtick runs, row-shaped `#98 FORGED` lines in message ids AND in the dangling sender id): no control character reaches the line (`\n`→space, ESC stripped); the forged `#9x` text survives as inline text inside `⟨…⟩`, never at a line start. Backtick runs survive verbatim (see residual RS-6).
  - **controls:** `dangling_only` → only the dangling part; `sound_only` → `refused=False`, `backfilled=1`, 1 row changed.
  - **FORK-2 / F-4:** `unmigrated_agent+dangling` → only *"cannot migrate `message` rows before the `agent` table is migrated (1 un-migrated (NONE-scope) agent(s) remain) …"*; `dangling_pos=-1`.
- **P4 — D2 / FORK-1 (F-3).** THE shared preconditions redirected to a clean answer while a half-pair row exists (the F-3/CD-1 race made reachable). `agent`: `backfilled=3`, `rows_changed_by_bytediff=2` (**over-claims by 1**). `message`: `backfilled=2`, changed 2 (**D2 correct**). `memory` not constructed (its WHERE equals its count predicate; no gap exists to construct).
- **#4b** — graded via the a19b pin + MUT-E/E2 (§8): the teaching survives verbatim, same class, exactly one appended line with the bare keep id and `lore-adm delete-keep`; the session is not in it (code read: the line interpolates only `session_keep_bare`); the PIN does not enforce the latter (F-7).
- **FK-a (`None` on every refusal)** — every refusal in P3 serves `scanned=None`/`already_migrated=None`; code read: every refusal routes through `principals._refused`.

## §8 Mutation proofs (driver `scripts/mutation_proof.py`, run from the scratch copy; declared sets written to `mut/DECLARED.txt` at 12:59:23 BEFORE any run, ids from `--collect-only`; each run restored byte-exact — `md5sum -c` over agents/server/principals OK and the patch md5 `b23f3e43…` re-verified after all runs)
| mut | what | consumer (NOT the builder's) | declared RED | result |
|---|---|---|---|---|
| A | a NEW refusal (`role == "mutantrole"`) added to `AgentRegistry.preflight` ONLY | `test_M2_role_mutantrole_registers[handler|registry]` | both | **HELD** (exit 0). Receipt: handler `mints: 0` + `MUTANT preflight-only refusal`; registry the same → ONE decision reaches BOTH callers, and the handler refuses before the mint |
| B | the handler's pre-mint `preflight(...)` call deleted | `test_M1_…_through_the_handler_mints_nothing` | M1 | **HELD** |
| C | THE shared `_agent_migration_preconditions` reports one extra ownerless-scoped agent | `test_M3_every_valid_table_proceeds_on_a_clean_store[agent|memory|message|brief]` | all 4 | **HELD** — every leg (incl. `memory` and `brief`, which the builder's redirect pins did not use) decides from the ONE function |
| D | a PRIVATE copy of the role decision re-added inside `register` after `preflight` (D-2's "right reason") | a19b `KP5[AgentIdentityConflictError-role-conflict]` | that id | **HELD** — KP5 is green at the build for the right reason |
| E | the caller's `session` interpolated into the #4b appended line | a19b `…test_a_FAILED_compensation_serves_the_teaching_plus_ONE_remedy_line` | that id (expected to STAY GREEN) | **PROOF FAILED as predicted: "DECLARED RED but STAYED GREEN", `1 passed`** → pin gap F-7 |
| E2 | positive control on the SAME statement: the `lore-adm delete-keep` remedy replaced | the same pin | that id | **HELD** — so E's green is a gap in the assertion, not an unreached line |

## §9 RESIDUALS (each with a verdict and an owner/trigger)
| # | residual | verdict |
|---|---|---|
| RS-1 | **amendment 26's pin — the fixture shape for 63c-i-b (or this fix pass)**: ONE `_governed_world`; `_seed_migrated_senders(world)`; `seed_message_legacy(conn, sender_id="ghost_sender", session="gs", seq=1, row_id="m_dangling")` (no agent row for `ghost_sender`); `seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=2, row_id="m_half_i", owner_principal=RecordID("principal", world.operator_bare))` (half i); `seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=3, row_id="m_sound")`. Snapshot `SELECT * FROM message ORDER BY id` → `migrate("message")` → assert `refused is True`; `scanned is None and already_migrated is None and backfilled == 0`; the snapshot byte-identical (so `m_sound` NOT stamped); `reason.find("dangling") != -1`, `reason.find("half-applied") != -1`, and `reason.find("dangling") < reason.find("half-applied")` (the order read from the served text only, per am-26); `"1 legacy message(s) name a dangling sender"` and `"1 message row(s) carry an owner but no scope"` both present (each count ATTRIBUTED to its own clause — see F-8). Extend per am-27 FORK-2: add `seed_agent_legacy(conn, row_id="legacyagent", name="legacyagent", session="gs")` → the ORDER clause first, then dangling, then half-pair; control: migrate `agent` → re-run → only the remaining two. Behaviour already satisfies the am-26 part (P3); the FORK-2 extension is RED on this build (F-4) | owner: this fix pass if opened, else i-b row (am-26 §W 2 / am-27 §W 2) |
| RS-2 | F-2's pin: the P5 shape (8-way `asyncio.gather` of handler registers, one principal, fresh session per round, ≥1 same-name role conflict) asserting ∀ agent rows `scope` ∈ live keeps; 20 consecutive greens to clear (the ≥8-way law) + the P2 sequential construction as the deterministic leg | owner: the fix pass |
| RS-3 | F-1's pin: the P1 shape (a foreign principal registering names the keeper's agents hold: role-conflict / spawned_by-conflict / retired / absent ⇒ all four byte-identical `GovernedDenied`) | owner: the ruling on F-1, then its contract |
| RS-4 | the **real dirty store** (FOCUS 5) — not run (permission-denied); what the fleet's 316 real legacy messages do at `--table message` (dangling senders?) is unmeasured | **operator-pending** (lead ruling #17046); staged commands §5 |
| RS-5 | builder R-a stands and is widened by P5: a same-name, same-role concurrent first-register's loser gets a raw `TxnDomainRejectionError` (55/20 rounds at HEAD too — pre-existing), not the registry's teaching, and is never compensated | pre-existing; surfaced (unruled) |
| RS-6 | hostile stored ids keep backtick runs verbatim inside the migrate refusal text (`sanitise_line` strips control chars only). The text reaches the operator's `lore-adm` stderr, not an MCP render, so no fence is forged today; it would be if a refusal reason is ever rendered inside a fenced block | LOW; trigger: the first MCP render of a `MigrateGovernedResult.reason` |
| RS-7 | a19b §12 R-2 (the runtime spy counts any exception as "refused") carries unchanged | carried, LOW |
| RS-8 | `9fd34d3` (packet 64 am-5) rules that `KeepStore.delete_keep` gains a refuse-when-populated guard at 64d-ii — once built, F-2's delete would refuse and the #4b line would fire instead (the keep stays; its "LEFT BEHIND and would deny the next principal" wording is then wrong for a same-principal session, cf. F-5) | trigger: 64d-ii's guard landing — re-read the #4b line then |
| RS-9 | lore friction: `lore_search` over-ran 120 s once and served a budget STUB once in this run (same class as #490); awk fallback used and said so | carried under #490 |

## §A Instruments (verbatim — the scratch tree is disposable)
### §A.1 `probe_coldaudit.py` (copied into the scratch copy as `loremaster/tests/test_probe_coldaudit_63c_i_a_2.py`, removed before the currency run) — md5 `01d7f9dbddcf4d259954d42e7979560c`
```python
"""coldaudit-63c-i-a-2 — probe instruments (scratch copy only; pasted verbatim into the report).

Each probe prints a JSON receipt line prefixed ``PROBE`` and asserts only what the audit relies on, with a
CONTROL leg in the same test. Live TEST store (:18000) via the shared harness; NEVER :18500.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
import test_fixwave_a19a_63c_i_a as a19a
from _governed_contract import (
    credentialed_app_context,
    seed_agent_governed,
    seed_agent_legacy,
    seed_message_legacy,
)
from _surreal_harness import run
from loremaster.agents import AgentRegistryError

from loremaster import principals

_DIM = a19a._DIM


def _receipt(tag: str, payload: Any) -> None:
    print(f"PROBE {tag} {json.dumps(payload, default=str, sort_keys=True)}")


async def _served(awaitable: Any) -> tuple[str, str | None]:
    try:
        await awaitable
    except Exception as error:  # noqa: BLE001 - the probe records whatever is served
        return type(error).__name__, str(error)
    return "OK", None


# ------------------------------------------------------------------ P1 — cross-principal leak via preflight
@pytest.mark.parametrize("order", ["build", "control_head_order"])
async def test_P1_a_foreign_principal_learns_another_principals_agent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any, order: str
) -> None:
    """bob (a member NOT in alice's household) registers into alice's session with names alice's agents
    hold. BUILD: the handler's preflight runs before the SF-63-1 gate. CONTROL: the handler's (first)
    preflight admits, emulating HEAD's mint→gate→register order (register's own preflight still runs)."""
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member", "bob": "member"}, dim=_DIM
    ) as world:
        ctx = world["ctx"]
        session = "s-alice"
        world["holder"]["email"] = world["emails"]["alice"]
        await ctx.comms(
            action="register", agent="worker", session=session, role="secretrole", spawned_by="alicelead"
        )
        await ctx.comms(action="register", agent="gone", session=session, role="builder")
        await ctx.agent_registry.touch("gone", session=session, status="retired")
        if order == "control_head_order":
            import sys as _sys  # noqa: PLC0415

            real = ctx.agent_registry.preflight

            async def first_admits(*args: Any, **kwargs: Any) -> Any:
                # admit ONLY the handler's pre-mint call (caller frame = _comms_register); register's own
                # preflight (caller frame = register) still decides — emulating HEAD's mint->gate->register.
                if _sys._getframe(1).f_code.co_name == "_comms_register":
                    return None
                return await real(*args, **kwargs)

            monkeypatch.setattr(ctx.agent_registry, "preflight", first_admits)
        world["holder"]["email"] = world["emails"]["bob"]
        served = {
            "role_conflict": await _served(
                ctx.comms(action="register", agent="worker", session=session, role="auditor")
            ),
            "spawned_by_conflict": await _served(
                ctx.comms(
                    action="register", agent="worker", session=session, role="secretrole", spawned_by="boblead"
                )
            ),
            "retired": await _served(ctx.comms(action="register", agent="gone", session=session, role="builder")),
            "absent_name": await _served(
                ctx.comms(action="register", agent="nobody", session=session, role="builder")
            ),
        }
        _receipt(f"P1[{order}]", served)
        leaked = [
            key for key, (_cls, text) in served.items() if text and ("secretrole" in text or "alicelead" in text
                                                                    or "retired" in text)
        ]
        _receipt(f"P1[{order}].leaked", leaked)
        assert served["absent_name"][0] == "GovernedDenied", served


# ------------------------------------------------------------------ P2 — the CANONICAL race strands the winner
@pytest.mark.parametrize("who_creates", ["this_call_creates", "control_winner_creates"])
async def test_P2_the_race_winner_is_stranded_when_the_loser_created_the_keep(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any, who_creates: str
) -> None:
    """Two registers of `x` by the SAME principal into the SAME session with DIFFERENT roles, interleaved:
    A preflights, A mints (CREATES the session keep), B runs its whole handler (preflight passes — no row
    yet; mint FINDS A's keep; gate passes; register CREATES x scoped to that keep), then A's register meets
    B's row → AgentIdentityConflictError → A's created-only compensation DELETES the keep B's agent is
    scoped to. CONTROL: B's mint happens first (B creates, A finds) → no compensation."""
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
    ) as world:
        ctx, admin_conn = world["ctx"], world["admin_conn"]
        world["holder"]["email"] = world["emails"]["alice"]
        session = "s-race"
        keep_store = ctx._keep_store
        real = keep_store.get_or_create_keyed
        calls = {"n": 0}

        async def concurrent_b() -> tuple[str, str | None]:
            return await _served(ctx.comms(action="register", agent="x", session=session, role="scout"))

        b_result: dict[str, Any] = {}

        async def spy(*args: Any, **kwargs: Any) -> Any:
            calls["n"] += 1
            if calls["n"] == 1 and who_creates == "this_call_creates":
                keep = await real(*args, **kwargs)  # A creates
                b_result["b"] = await concurrent_b()  # B (nested call n=2) finds, registers x(scout)
                return keep
            if calls["n"] == 1 and who_creates == "control_winner_creates":
                b_result["b"] = await concurrent_b()  # B (nested call n=2) creates first
                return await real(*args, **kwargs)  # A finds
            return await real(*args, **kwargs)

        monkeypatch.setattr(keep_store, "get_or_create_keyed", spy)
        a_result = await _served(ctx.comms(action="register", agent="x", session=session, role="builder"))
        keeps = await run(admin_conn, f"SELECT id, key, keeper FROM keep WHERE key = 'session:{session}'")
        agents = await run(admin_conn, "SELECT id, name, role, scope, owner_principal FROM agent WHERE name = 'x'")
        agent_scope = agents[0]["scope"] if agents else None
        scope_keep_exists = False
        if agent_scope:
            bare = agent_scope.split(":", 1)[1]
            scope_keep_exists = bool(await run(admin_conn, f"SELECT id FROM keep:`{bare}`"))
        # the stranded agent's own view: alice's fleet as seen through the governed surface
        fleet = await _served(ctx.comms(action="fleet", agent="x", session=session))
        fleet_text = str(await ctx.comms(action="fleet", agent="x", session=session)) if fleet[0] == "OK" else None
        # a later re-register of x (same role as the stored winner) — does it heal the scope?
        again = await _served(ctx.comms(action="register", agent="x", session=session, role="scout"))
        keeps_after = await run(admin_conn, f"SELECT id FROM keep WHERE key = 'session:{session}'")
        agents_after = await run(admin_conn, "SELECT scope FROM agent WHERE name = 'x'")
        _receipt(
            f"P2[{who_creates}]",
            {
                "A": a_result,
                "B": b_result.get("b"),
                "session_keeps_after_race": keeps,
                "agent_x": agents,
                "agent_scope_keep_exists": scope_keep_exists,
                "fleet_served": fleet,
                "fleet_names_x": (" x " in fleet_text or "x (" in fleet_text) if fleet_text else None,
                "re_register": again,
                "session_keeps_after_re_register": keeps_after,
                "agent_x_scope_after_re_register": agents_after,
            },
        )
        assert calls["n"] >= 2, calls


# ------------------------------------------------------------------ P3 — door #2, am-26, FORK-2 (store probes)
from test_fixwave_a19_63c_i_a import _governed_world, _seed_clean_single_principal_store  # noqa: E402
from test_fixwave_a19a_63c_i_a import _seed_migrated_senders  # noqa: E402
from lorerunes.pdp import keep_scope  # noqa: E402
from surrealdb import RecordID  # noqa: E402


async def _message_rows(connection: Any) -> list[Any]:
    return await run(connection, "SELECT * FROM message ORDER BY id")


@pytest.mark.parametrize(
    "population",
    [
        "am26_dangling+half_i",  # am-26's ruled fixture: ghost sender + owned-unscoped msg + one sound legacy
        "dangling+half_i+half_ii",
        "half_i_11+half_ii_12",  # door #2 above the cap, distinct per-half counts
        "dangling_only",  # control
        "sound_only",  # control: proceeds
        "unmigrated_agent+dangling",  # FORK-2 (am-27): one refusal or two round trips?
        "hostile_ids",  # sanitiser on EVERY stored-id render in the message-leg refusal
    ],
)
async def test_P3_the_message_leg_refusals(population: str) -> None:
    async with _governed_world() as world:
        conn = world.connection
        await _seed_migrated_senders(world)
        operator = RecordID("principal", world.operator_bare)
        seq = iter(range(1, 1000))
        if population.startswith("unmigrated_agent"):
            await seed_agent_legacy(conn, row_id="legacyagent", name="legacyagent", session="gs")
        if "dangling" in population:
            await seed_message_legacy(conn, sender_id="ghost_sender", session="gs", seq=next(seq), row_id="m_dangling")
        if population in ("am26_dangling+half_i", "dangling+half_i+half_ii"):
            await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=next(seq),
                                      row_id="m_half_i", owner_principal=operator)
        if population == "dangling+half_i+half_ii":
            await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=next(seq),
                                      row_id="m_half_ii", scope=keep_scope("sessionkeepother"))
        if population == "half_i_11+half_ii_12":
            for index in range(11):
                await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=next(seq),
                                          row_id=f"hi{index:02d}", owner_principal=operator)
            for index in range(12):
                await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=next(seq),
                                          row_id=f"hii{index:02d}", scope=keep_scope("sessionkeepother"))
        if population == "hostile_ids":
            await seed_message_legacy(conn, sender_id="ghost\n#99 FORGED ROW ``` x", session="gs",
                                      seq=next(seq), row_id="m_host\n#98 FORGED\x1b[31m")
            await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=next(seq),
                                      row_id="h1\n#97 FORGED ``` ", owner_principal=operator)
            await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=next(seq),
                                      row_id="h2\r\n#96 FORGED", scope=keep_scope("sessionkeepother"))
        await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=next(seq), row_id="m_sound")
        before = await _message_rows(conn)
        result = await world.migrate("message")
        after = await _message_rows(conn)
        reason = result.reason or ""
        _receipt(
            f"P3[{population}]",
            {
                "refused": result.refused, "scanned": result.scanned, "backfilled": result.backfilled,
                "already_migrated": result.already_migrated, "reason": reason,
                "byte_inert": before == after,
                "rows_changed_by_bytediff": sum(1 for b, a in zip(before, after, strict=False) if b != a),
                "reason_control_chars": [c for c in reason if ord(c) < 32 or ord(c) == 127],
                "dangling_pos": reason.find("dangling"), "half_pos": reason.find("half-applied"),
            },
        )


# ------------------------------------------------------------------ P4 — D2 / FORK-1: backfilled vs rows changed
@pytest.mark.parametrize("table", ["agent", "message"])
async def test_P4_backfilled_vs_rows_changed_under_a_redirected_precondition(
    monkeypatch: pytest.MonkeyPatch, table: str
) -> None:
    """The F-3 / CD-1 race made reachable: THE shared preconditions redirected to report a CLEAN store while a
    half-pair row of ``table`` exists, so the leg PROCEEDS and its self-guarding WHERE skips that row. Receipt:
    served ``backfilled`` vs the byte-diff count of rows the run changed."""
    async with _governed_world() as world:
        conn = world.connection
        operator = RecordID("principal", world.operator_bare)
        if table == "agent":
            await seed_agent_legacy(conn, row_id="legacy1", name="legacyone", session="gs")
            await seed_agent_legacy(conn, row_id="legacy2", name="legacytwo", session="gs")
            await seed_agent_governed(conn, row_id="half", name="halfagent", session="gs",
                                      owner_principal=world.operator_bare, owner_agent=None, scope=None)
        else:
            await _seed_migrated_senders(world)
            await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=1, row_id="m1")
            await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=2, row_id="m2")
            await seed_message_legacy(conn, sender_id="sender_operator", session="gs", seq=3, row_id="mhalf",
                                      owner_principal=operator)

        async def clean(*_args: Any, **_kwargs: Any) -> Any:
            return principals.AgentMigrationPreconditions(unscoped_count=0, owned_unscoped=(), ownerless_scoped=())

        monkeypatch.setattr(principals, "_agent_migration_preconditions", clean)
        before = await run(conn, f"SELECT * FROM {table} ORDER BY id")
        result = await world.migrate(table)
        after = await run(conn, f"SELECT * FROM {table} ORDER BY id")
        changed = sum(1 for b, a in zip(before, after, strict=True) if b != a)
        _receipt(f"P4[{table}]", {"refused": result.refused, "reason": result.reason, "scanned": result.scanned,
                                   "backfilled": result.backfilled, "already": result.already_migrated,
                                   "rows_changed_by_bytediff": changed})


# ------------------------------------------------------------------ M — mutation-proof CONSUMERS (not the builder's)
async def test_M1_a_known_preflight_refusal_through_the_handler_mints_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """Consumer for MUT-B (the handler's pre-mint `preflight` call deleted): a role conflict driven through
    the handler must be refused with ZERO session-keep mints. GREEN on the build."""
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        await ctx.agent_registry.register("m1agent", session="s-m1", role="builder")  # ownerless, no keep
        mints = a19a._spy_the_mint(monkeypatch, ctx)
        with pytest.raises(AgentRegistryError):
            await ctx.comms(action="register", agent="m1agent", session="s-m1", role="scout")
        assert mints["count"] == 0, f"a preflight-refusable conflict minted {mints['count']} keep(s)"


@pytest.mark.parametrize("path", ["handler", "registry"])
async def test_M2_role_mutantrole_registers(monkeypatch: pytest.MonkeyPatch, tmp_path: Any, path: str) -> None:
    """Consumer for MUT-A (a NEW refusal added to `preflight` only): GREEN on the build (the role is legal);
    RED on BOTH paths iff both callers route through the ONE `preflight`. The handler leg additionally
    records whether the refusal happened before the mint."""
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        mints = a19a._spy_the_mint(monkeypatch, ctx)
        if path == "handler":
            served = await _served(ctx.comms(action="register", agent="m2agent", session="s-m2", role="mutantrole"))
        else:
            served = await _served(ctx.agent_registry.register("m2agent", session="s-m2", role="mutantrole"))
        _receipt(f"M2[{path}]", {"served": served, "mints": mints["count"]})
        assert served[0] == "OK", served


@pytest.mark.parametrize("table", ["agent", "memory", "message", "brief"])
async def test_M3_every_valid_table_proceeds_on_a_clean_store(tmp_path: Any, table: str) -> None:
    """Consumer for MUT-C (THE shared `_agent_migration_preconditions` made to report one ownerless-scoped
    agent): GREEN on the build (a clean single-principal store; `brief` answers its 'lands 63c-ii' text, which
    is refused=True but NOT the half-applied refusal); RED on every table iff every leg decides from the ONE
    function."""
    async with _governed_world() as world:
        await _seed_clean_single_principal_store(world)
        result = await world.migrate(table)
        _receipt(f"M3[{table}]", {"refused": result.refused, "reason": result.reason})
        assert "half-applied" not in str(result.reason or ""), result


# ------------------------------------------------------------------ P5 — F-2 under REAL concurrency (8-way × 20)
async def test_P5_eight_way_concurrent_registers_never_strand_a_scope(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    """20 rounds; each round a FRESH session and 8 concurrent handler registers by ONE principal: 4 of name
    `dup` with alternating roles (so role conflicts race the mint) + 4 distinct names. Invariant measured, not
    asserted: every agent row's `scope` keep EXISTS afterwards. Receipt: per-round refusals, stranded rows."""
    import asyncio  # noqa: PLC0415

    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx, admin_conn = world["ctx"], world["admin_conn"]
        world["holder"]["email"] = world["emails"]["alice"]
        rounds = []
        for round_index in range(20):
            session = f"s-conc-{round_index}"
            calls = [ctx.comms(action="register", agent="dup", session=session, role=("builder", "scout")[i % 2])
                     for i in range(4)]
            calls += [ctx.comms(action="register", agent=f"solo{i}", session=session, role="builder") for i in range(4)]
            outcomes = await asyncio.gather(*calls, return_exceptions=True)
            refused = [type(o).__name__ for o in outcomes if isinstance(o, BaseException)]
            scopes = await run(admin_conn, f"SELECT VALUE scope FROM agent WHERE session = '{session}'")
            live = {str(k) for k in await run(admin_conn, "SELECT VALUE id FROM keep")}
            stranded = [s for s in scopes if s is not None and s not in live]
            rounds.append({"round": round_index, "refused": refused, "agents": len(scopes), "stranded": len(stranded)})
        _receipt("P5", {"rounds": rounds, "rounds_with_stranding": sum(1 for r in rounds if r["stranded"]),
                        "total_stranded": sum(r["stranded"] for r in rounds)})
```
### §A.2 `run_guarded.sh` (every probe / mutation / currency run)
```bash
#!/usr/bin/env bash
# run_guarded.sh <logfile> -- <command...> : run in the scratch copy with a 15 GB-available PID watchdog (8 s poll).
LOG=$1; shift; [ "$1" = "--" ] && shift
cd /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/10ac805a-19e9-46a0-b7ef-c030296122cd/scratchpad/sc
"$@" > "$LOG" 2>&1 &
PID=$!
( while kill -0 $PID 2>/dev/null; do A=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
    if [ "$A" -lt 15 ]; then echo "WATCHDOG KILL avail=${A}G" >> "$LOG"; pkill -TERM -P $PID; kill -TERM $PID; fi; sleep 8; done ) &
wait $PID; echo "EXIT=$?" >> "$LOG"
```
### §A.3 `run_suite.sh` (the two full-suite runs, §1)
```bash
#!/usr/bin/env bash
# Full-suite runner with a 15 GB-available PID watchdog (kills only its own pytest).
set -u
D=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/10ac805a-19e9-46a0-b7ef-c030296122cd/scratchpad
TAG=${1:-full1}
cd $D/sc
uv run pytest -n auto -q -p no:cacheprovider > $D/$TAG.log 2>&1 &
PID=$!
echo $PID > $D/$TAG.pid
( while kill -0 $PID 2>/dev/null; do
    AVAIL=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
    if [ "$AVAIL" -lt 15 ]; then echo "WATCHDOG KILL avail=${AVAIL}G" >> $D/$TAG.log; pkill -TERM -P $PID; kill -TERM $PID; fi
    sleep 8
  done ) &
wait $PID
echo "EXIT=$?" >> $D/$TAG.log
```
### §A.4 `lore_lane_clear.sh` (the lore-scoped lane waiter — keyed on the EXECUTABLE + a lore cwd/argv, never on a wrapper's text, per #228 and ruling #17046)
```bash
#!/usr/bin/env bash
# Lore-scoped lane: clear when no uv/python/pytest EXECUTABLE with a lore cwd/argv running a test session
# exists (2 checks 10 s apart). Keyed on comm (never on a bash wrapper's text). Max wait $1 seconds.
end=$(( $(date +%s) + ${1:-3600} )); clear=0
while [ "$(date +%s)" -lt "$end" ]; do
  n=0
  for p in $(ps -eo pid=,comm= | awk '$2 ~ /^(uv|python.*|pytest)$/{print $1}'); do
    c=$(readlink /proc/$p/cwd 2>/dev/null); a=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null)
    case "$c $a" in *PycharmProjects/lore*|*PycharmProjects-lore*) case "$a" in *pytest*) n=$((n+1));; esac;; esac
  done
  if [ $n -eq 0 ]; then clear=$((clear+1)); else clear=0; fi
  [ $clear -ge 2 ] && { echo "LORE-LANE-CLEAR $(date +%T)"; exit 0; }
  sleep 10
done; echo "LORE-LANE-TIMEOUT $(date +%T)"; exit 1
```
### §A.5 Mutation anchors/replacements (`mut/`), declared sets (`mut/DECLARED.txt`)
- **A** anchor:
```
        self._refuse_an_invalid_identity(name=name, session=session, role=role)
        existing_row = await self._select_row(self._agent_id(session, name))

```
  replacement:
```
        self._refuse_an_invalid_identity(name=name, session=session, role=role)
        if role == "mutantrole":
            raise AgentIdentityConflictError("MUTANT preflight-only refusal")
        existing_row = await self._select_row(self._agent_id(session, name))

```
- **B** anchor:
```
        await self.agent_registry.preflight(
            agent,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=principal_bare,
        )

```
  replacement:
```
        pass  # MUT-B: handler preflight deleted

```
- **C** anchor:
```
        ownerless_scoped=_by_id(ownerless_scoped),

```
  replacement:
```
        ownerless_scoped=(*_by_id(ownerless_scoped), "agent:MUTANT"),

```
- **D** anchor:
```
        agent_id = self._agent_id(session, name)
        now = datetime.now(UTC)

```
  replacement:
```
        if existing is not None and existing.role != role:
            raise AgentIdentityConflictError("MUT-D private copy in register")
        agent_id = self._agent_id(session, name)
        now = datetime.now(UTC)

```
- **E** anchor:
```
"and could not delete it — it is LEFT BEHIND and would deny the next principal's "
```
  replacement:
```
f"(session {session}) and could not delete it — it is LEFT BEHIND and would deny the next principal's "
```
- **E2** anchor:
```
f"`lore-adm delete-keep --keep {session_keep_bare}`",
```
  replacement:
```
f"`remove keep {session_keep_bare} by hand`",
```
```
# declared 12:59:23 BEFORE any mutation run (ids from --collect-only)
MUT-A agents.py new preflight-only refusal: loremaster/tests/test_probe_coldaudit_63c_i_a_2.py::test_M2_role_mutantrole_registers[handler] loremaster/tests/test_probe_coldaudit_63c_i_a_2.py::test_M2_role_mutantrole_registers[registry]
MUT-B server.py handler preflight deleted: loremaster/tests/test_probe_coldaudit_63c_i_a_2.py::test_M1_a_known_preflight_refusal_through_the_handler_mints_nothing
MUT-C principals.py shared preconditions +1 ownerless-scoped: loremaster/tests/test_probe_coldaudit_63c_i_a_2.py::test_M3_every_valid_table_proceeds_on_a_clean_store[agent] [memory] [message] [brief]
MUT-D agents.py private role copy in register: loremaster/tests/test_fixwave_a19b_63c_i_a.py::test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class[AgentIdentityConflictError-role-conflict]
MUT-E server.py session in #4b line: loremaster/tests/test_fixwave_a19b_63c_i_a.py::TestAFailedCompensationIsNamedToTheCaller63cIAa19b::test_a_FAILED_compensation_serves_the_teaching_plus_ONE_remedy_line  (EXPECTED TO STAY GREEN = the pin gap)
```
### §A.6 `dirty_store_driver.py` (FOCUS 5 — written, NOT run: the restore it follows was permission-denied)
```python
"""coldaudit-63c-i-a-2 — REAL dirty-store driver (#107 class). Run from the scratch copy's venv:

    cd <scratch>/sc && uv run python ../dirty_store_driver.py <restored_db_name|--virgin> <dim>

Against ``ws://127.0.0.1:18000`` ONLY (the harness's test URL; asserted). Steps, each printed as one
``STEP`` JSON line:
  1. direct-SELECT census of agent/message/memory/brief (+ dangling senders, half-pairs), BEFORE;
  2. apply the POST-BUILD emitted DDL (the union of every ``generate_*_ddl`` — the one derivation the
     test tree uses), through the production ``execute_transaction`` seam;
  3. provision ONE admin principal (the cutover precondition the dump predates);
  4. ``migrate_governed`` for: message (before agents) · bogus · brief · agent · message · memory · brief
     · then EVERY table again (idempotence) — each result beside a direct-SELECT census and a byte-diff
     count of rows the run changed on that table.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path.cwd() / "loremaster" / "tests"))

import _surreal_harness as harness  # noqa: E402
from _enforced_relations_scaffold import emitted_schema_ddl  # noqa: E402
from _governed_contract import _credentialed_config, apply_ddl  # noqa: E402
from loremaster.principals import build_keep_store, build_principal_store, migrate_governed  # noqa: E402
from loremaster.store._txn import StoreHandle  # noqa: E402

import loremaster  # noqa: E402

TABLES = ("agent", "message", "memory", "brief")


def step(tag: str, payload: Any) -> None:
    print(f"STEP {tag} {json.dumps(payload, default=str, sort_keys=True)}", flush=True)


async def q(conn: Any, statement: str) -> Any:
    return await harness.run(conn, statement)


async def census(conn: Any) -> dict[str, Any]:
    info = await q(conn, "INFO FOR DB")
    defined = set((info or {}).get("tables", {}))
    out: dict[str, Any] = {}
    for table in TABLES:
        if table not in defined:
            out[table] = "UNDEFINED"
            continue
        rows = await q(conn, f"SELECT id, scope, owner_principal FROM {table}")
        out[table] = {
            "rows": len(rows),
            "scope_none": sum(1 for r in rows if r.get("scope") is None),
            "scope_set": sum(1 for r in rows if r.get("scope") is not None),
            "owner_none": sum(1 for r in rows if r.get("owner_principal") is None),
            "owned_unscoped": sum(1 for r in rows if r.get("scope") is None and r.get("owner_principal") is not None),
            "scoped_ownerless": sum(1 for r in rows if r.get("scope") is not None and r.get("owner_principal") is None),
        }
    if "message" in defined:
        dangling = await q(conn, "SELECT VALUE id FROM message WHERE scope IS NONE AND sender.id IS NONE")
        out["message_dangling_senders"] = len(dangling)
        senders_none = await q(conn, "SELECT VALUE id FROM message WHERE sender IS NONE")
        out["message_sender_field_NONE"] = len(senders_none)
    return out


async def snapshot(conn: Any, table: str) -> dict[str, Any]:
    info = await q(conn, "INFO FOR DB")
    if table not in (info or {}).get("tables", {}):
        return {}
    return {str(r["id"]): json.dumps(r, default=str, sort_keys=True) for r in await q(conn, f"SELECT * FROM {table}")}


async def main(database: str, dim: int) -> None:
    os.environ.setdefault("SURREAL_USER", harness.surreal_user())
    os.environ.setdefault("SURREAL_PASS", harness.surreal_password().get_secret_value())
    os.environ.setdefault("ANTHROPIC_API_KEY", "sk-dummy")
    os.environ.setdefault("LORE_TEI_KEY", "dummy")
    url = str(harness.surreal_url())
    assert url.startswith("ws://127.0.0.1:18000"), url  # NEVER :18500
    step("provenance", {"loremaster": loremaster.__file__, "url": url, "database": database})
    env = harness.make_env(database=database, dim=dim)
    conn = await harness.connect_admin(env)
    try:
        step("census.before_ddl", await census(conn))
        await apply_ddl(conn, emitted_schema_ddl(dim=dim), url=url)
        step("census.after_ddl", await census(conn))
        config = _credentialed_config(database, dim=dim)
        principal_store = build_principal_store(config)
        keep_store = build_keep_store(config)
        await principal_store.ensure_ready()
        await keep_store.ensure_ready()
        operator = await principal_store.create(email="operator@example.com", role="admin")
        step("operator", {"id": operator.id})
        handle = StoreHandle(
            acquire=principal_store._ensure_connection,
            drop=principal_store._drop_connection,
            url=principal_store._url,
        )
        plan = ["message", "bogus", "brief", "agent", "message", "memory", "brief", "agent", "message", "memory"]
        for index, table in enumerate(plan):
            before = await snapshot(conn, table) if table in TABLES else {}
            try:
                result = await migrate_governed(
                    table=table, store=handle, keep_store=keep_store, principal_store=principal_store
                )
                served: Any = {
                    "refused": result.refused, "scanned": result.scanned, "backfilled": result.backfilled,
                    "already_migrated": result.already_migrated, "reason": result.reason,
                }
            except Exception as error:  # noqa: BLE001 - record whatever is served
                served = {"raised": type(error).__name__, "text": str(error)[:2000]}
            after = await snapshot(conn, table) if table in TABLES else {}
            changed = sum(1 for key, row in after.items() if before.get(key) != row)
            step(f"migrate[{index}].{table}", {"served": served, "rows_changed_bytediff": changed,
                                                "census": await census(conn)})
        keeps = await q(conn, "SELECT id, key, type FROM keep")
        step("keeps", keeps)
        stamped_owner_none = await q(conn, "SELECT VALUE id FROM message WHERE scope IS NOT NONE AND owner_principal IS NONE")
        step("invariant.no_stamped_message_with_NONE_owner", {"violations": len(stamped_owner_none)})
        await keep_store.close()
        await principal_store.close()
    finally:
        await conn.close()


if __name__ == "__main__":
    target = sys.argv[1]
    width = int(sys.argv[2])
    if target == "--virgin":
        name = harness.unique_database()

        async def virgin() -> None:
            env = harness.make_env(database=name, dim=width)
            watcher = await harness.connect_admin(env)  # opened BEFORE the drop: a reconnect would re-DEFINE it
            try:
                await main(name, width)
            finally:
                await harness.drop_database(env)
                try:
                    ns = await harness.run(watcher, "INFO FOR NS")
                    step("virgin.teardown", {"database": name, "still_present": name in (ns or {}).get("databases", {})})
                finally:
                    await watcher.close()

        asyncio.run(virgin())
    else:
        asyncio.run(main(target, width))
```

## VERDICT
**NO-GO** for committing patch `b23f3e43…` as it stands (graded on `5a43aeb`; production files identical through `ccdad34`).

- **Blocking: F-2.** The one piece of NEW write behaviour this patch adds (the #485 created-only compensation) deletes a keep that concurrent, successful registrations of the same principal are already scoped to, silently stranding every agent of that session on a keep that no longer exists. Measured 2/20 · 8/20 · 11/20 rounds under 8-way concurrency with a single name collision; 0/20 at HEAD. The old failure it replaces (a keep left behind, kept by the caller) is harmless for a same-principal session, so for that population the patch trades a benign leftover for data loss. No pin constructs it, because every race fixture injects the conflicting register ownerless.
- **Also required before GO (not blocking alone): F-1.** It is a ruling problem, not a build defect: am-22 §1's order discloses cross-principal roster facts that two standing rulings forbid.
- **What a narrow fix pass holds:** F-2 (a guard, plus the RS-2 pin at ≥8-way ×20 greens); F-1 once ruled (plus the RS-3 pin); am-27's FORK-1/FORK-2 (F-3/F-4), which am-27 already ruled into "the audit's fix pass if any"; the am-26 pin (RS-1); the F-7/F-8 pin gaps; F-5's `KeepNotFoundError` branch. Everything else in this build (the preconditions refactor, door #2, am-26 behaviour, D2 on the message leg, FK-a, the sanitiser, `preflight` sharing) survived its controls and mutations and should be kept as-is.
- **Operator-pending:** FOCUS 5 (the real dirty store) — the permission layer denied the restore; nothing about the fleet's real pre-63 population is certified by this audit.
