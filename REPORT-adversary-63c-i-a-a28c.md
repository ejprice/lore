brief-base v18 read · brief project v7 read

# REPORT-adversary-63c-i-a-a28c: the narrow, final, past-the-cap delta grade of the 63c-i-a contract fold a28c (`7017b54`)

*Every claim here is scoped to the tree it names and dated 2026-09-29 (UTC). "The reference" means MY reference
(§0), built over `169925f` production. "The contract" means the committed test files at `7017b54`, which are
byte-identical at HEAD `bd017ee` (`git diff --stat 7017b54 bd017ee` over the graded files and `loremaster/loremaster`
is empty).*

## SUMMARY BLOCK
- **State:** done-with-deviations.
  - **DV-1:** only the `_txn` half of my reference is independent (`advref_txn.py`, §A.1): am-35 §2 + am-36 §1, the FOCUS-2 surface. The register / keeps / migrate / FK-8 halves are the a28 author's `reference_fix.patch` (md5 `0abdf6d8…`, verified), the a28b author's interdiff (applied with `--recount`, the fence-handling issue the a28c author also hit) and the a28c author's `myref_a28c_migrate.py` + `myref_a28c_fk8.py` (§A.5b/§A.5d, extracted). I did NOT read the author's `myref_a28c_txn.py` or `myref_a28c_am36.py` before writing mine.
  - **DV-2:** the §HELD harness patch was not applied, so `test_surreal_harness.py` runs HEAD's copy on both legs (§SAT).
- **Graded:** `7017b54` · HEAD-at-report: `bd017ee` · DIFFERENT (8 ahead; the graded contract files, `_engine_shapes.py` and `loremaster/loremaster` are unchanged `7017b54`→`bd017ee`).
- **ROUTING VERDICT: `SUFFICIENT-FOR-BUILD`**, with ONE builder requirement and ONE optional targeted pin. Buckets: **NEW PROPERTY 0** · **PINNED PROPERTY, NEW CASE 2** (F-1 WB-H, F-2 KG) · test-self-hygiene residuals 2 (R-1, R-2) · predecessor 7/7 KILLED.
- **P1 headline:** 19 wrong builds (11 am-36 + 7 predecessor ports + C2-b), 18 killed. **ONE SURVIVOR: WB-H**, which passes all **1469** tests of the 8 core contract files. In WB-H the root-cause selector decides "cascade notice" by TEXT, not by the typed `details.kind == "NotExecuted"` that am-36 rules. It does so through a compiled pattern's `.match` anchored at the engine's cascade openings, which no echo can spoof. Its sibling on the retry decision (WB-I) is killed 65×. KF kills WB-H (§A.4).
  - **Why it survives, in two parts:**
    - (a) The exact-set text-reader derivation (`_text_testers_in`) treats `.match`, `.search` and `.fullmatch` on a compiled pattern, and a `from re import search` call, as NOT testing text (KG, §A.4).
    - (b) Every forged fixture builds its `kind` FROM its text (`_engine_shapes.typed_err_entry`), and the live engine never disagrees. So no fixture exists in which a text selector and a typed selector choose differently.
  - **Why this is not a reopen:** it is a new case of am-36's ruled, pinned property (a text reader where the engine types its signal). It routes to an implementation requirement at ONE chokepoint.
- **Predecessor kill table:** B1, B3, MP-3 (the substring mechanism), S7, S8, B13 and B15 are ALL KILLED on the committed bytes. I re-ran them after porting them onto my reference (§P0-PRED). C2-b (post-mint gate deleted) is killed too.
- **SAT (targeted, 18 files, §SAT):** ref **60 failed / 1700 passed** · base **457 failed / 1349 passed**.
  - **base-only 434**, identical per file to the author's.
  - **shared 23**, all packet-58-owned.
  - **REF-ONLY 35**, all `test_surreal_harness.py` (§HELD D-9). With the held patch applied: **56 passed, 0 failed**. **63c-attributable 0: CONFIRMED.**
  - The core 8 files on my reference: **1469 passed, 0 failed**.
- **Runs used:** 36 pytest runs, all under `systemd-run MemoryMax=16G MemorySwapMax=0` with `--timeout`. Zero cap kills and zero timeouts. §RUNS.
- **Packages considered:** `surrealdb.errors.parse_query_error` / `ServerError.details` (installed source read, §P-PKG) → replace_with_adapter, agreeing with the author. There is ONE diff: the SDK already ships `surrealdb.errors._detail_kind(details)`, a private helper, which both my reference and the author's re-implement → `keep_with_trigger` (it is private API; trigger: it becomes public). No `bespoke` verdict without a read.
- **Odoo-20 portability:** n/a (no Odoo seam touched; my enumeration found 0 seams, and the author also says n/a, so we agree).
- **Reuse ledger:** none. This report adds no production or test symbol to the repo. The scratch kill probes reuse the contract's own `_text_testers_in`, `_failed_statements` and `_rollback_verdict`.
- **Decisions needed:**
  - (1) F-1 routing: builder requirement only (my recommendation), or ALSO the one targeted pin KF, whose cost is one test function (lead / sidecar call).
  - (2) R-3: lore's watched root reports `git_ref 1d3cf98` while this checkout's HEAD is `bd017ee` (§R).
- **Pointers:** §P0-PRED · §P1 · §FINDINGS · §P1b · §P1c · §DUAL · §SAT · §A (instruments, verbatim).

## §0 Setup and receipts
- lore_comms registered (`adversary-63c-i-a-a28c` / `63c-20260924` / adversary / `≤20m`). grep/rg are hook-blocked (#473), so every search is `awk`. `scripts/` is not in lore's graph (#507), so the scripts test file was added by hand, as I say here.
- Required first read: `docs/reference/surrealdb-31-capabilities.md`. I leaned on §3 (transactions) and §6 (where the vendor docs are wrong).
  - Every store touch ran on `ws://127.0.0.1:18000`. `:18500` was never touched, and the TEI embedder was never called.
- CLAUDE.md §Quality gates "TEST SCOPE" read in full. Per the brief's override, I made no full-suite run and no `--currency` run.
- **Scratch copy:** `./scripts/scratch_copy.sh …/scratchpad/ref`, then IN the copy `git reset --hard HEAD && git clean -fd` (removing #486's WIP). After that, `git status --short` was empty.
  - `loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dba90f35-f0c8-4241-8a8c-8bd751789310/scratchpad/ref/loremaster/loremaster/__init__.py`.
  - The main tree's uncommitted files were never touched.
- **Reference stack**, applied in order on `169925f` production (HEAD's production differs only in `testing/loopback.py`, #466):
  1. a28 `reference_fix.patch`, extracted with md5 `0abdf6d85342aec8af41572a2d4d0ba9`, which equals the stated md5;
  2. the a28b interdiff (`git apply --recount`);
  3. the author's `myref_a28c_migrate.py` + `myref_a28c_fk8.py` (extracted md5 `6515728a…` / `d0f3320b…`);
  4. **MY `advref_txn.py`** (§A.1, md5 `1debf256…`).

  The non-`_txn` stack diff is saved as `ref_nontxn_base.patch` (md5 `c0e68084…`).

## §P0-PRED — the predecessor kill table (the a28b adversary's survivors, RE-RUN on the committed bytes)
Each build was ported from `REPORT-adversary-63c-i-a-a28b.md` §A.6a / §A.6d onto my reference. Anchors were re-derived where `_txn` moved: B1/B3/MP-3 now hit the anchored U prefix. Driver: `drive_pb.sh`, which backs up content, applies the build, runs, restores, and runs `cmp`. All restores were byte-exact.
| build (a28b) | what it does on the a28c reference | targeted files | result | killed by |
|---|---|---|---|---|
| **B1** | U text read OUTSIDE the one classifier (`_text_says_unique`, both raise sites call it first) | a28c + store + a28b | **KILLED** 3 failed / 582 | `test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier` ×1, `test_KA_…` ×2 |
| **B3** | U check moved after ASSERT / coercion | same | **KILLED** 10 / 575 | `test_am36_1_2_an_echoed_phrase_moves_nothing` ×8, `test_KB_…` ×2 |
| **MP-3** | a28b's RULED substring mechanism (`"database index" in … and "already contains" in …`) | same | **KILLED** 6 / 579 | whole-reader KB ×4, KB ×2 |
| **S7** | RS-5's try gains a re-reading exhaustion clause above the typed catch | RS + a28c | **KILLED** 2 / 997 | the door and typed-catch enumeration exact sets |
| **S8** | a second `try` in `findings.annotate` with a re-reading exhaustion clause | same | **KILLED** 3 / 996 | F-4 `…never_re_read_after_exhaustion`, door enumeration, `…guards_the_typed_error_ABOVE…` |
| **B13** | the pre-gate compares against `min(visible)` (a multi-keep member is denied) | a28c + a28 + a28b | **KILLED** 5 / 485 | `test_am35_1_1_…_iff_THIS_keep_is_visible` ×3, `test_KC_…` ×2 |
| **B15** | a registry read bypassing `AgentRegistry._query`, before the gate | same | **KILLED** 1 / 489 | `test_KE_every_registry_store_call_rides_the_one_seam` |
| (new) C2-b | the POST-mint gate deleted | same | **KILLED** 1 / 489 | a28 `…POST_MINT_recheck_denies_a_keep_minted_meanwhile…` |

**§A.5 AST-equality:** I did not re-run the author's `ast_receipt.py`. Instead the KA/KB/KC/KE classes were proven to BITE by the table above, which is a stronger instrument than AST equality: an AST-equal probe that cannot fail would be worthless. KD landed ADAPTED (D-1), and S7/S8 are killed by the per-handler exact sets. Status: **NOT TRIED as an AST diff; superseded by the empirical kills.**

## §P1 — wrong builds against the REAL contract (am-36 focus; the targeted files per build are in §RUNS)
Declared before running: every build was predicted to be killed, except WB-D2 (predicted: exact-set only) and WB-H (predicted SURVIVOR, from reading `_text_testers_in` + `typed_err_entry`).

**Legend for the "killed by" column (am-36 test names):**
- **whole-reader KB** = `test_am36_1_2_an_echoed_phrase_moves_nothing` (a28c file)
- **exact-set** = `test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier` (a28c file)
- **RS detection pins** = `TestDetectionFollowsTheOneSharedMarker` (`test_retry_seam.py`)

| build | the defect | result | killed by |
|---|---|---|---|
| WB-A | `run_query` retry decision: typed OR `_RETRY_TEXT_PATTERN.search(str(error))` | KILLED | whole-reader KB ×5 · RS detection pins ×33 (**the exact-set pin stayed GREEN**: this is the KG door) |
| WB-A2 | the transactional retry decision reads text through a compiled pattern | KILLED | whole-reader KB ×5 · RS `test_the_transactional_caller_follows_the_marker_too` |
| WB-B | routing-not-sharing INSIDE the allowlisted reader: the retry decision = the classifier's label, and the classifier gains a `"can be retried" in` leg | KILLED | whole-reader KB ×4 |
| WB-C | a SECOND parse at the txn raise site, from the text only | KILLED | whole-reader KB ×24 · typed-txn R ×2 · mapping-helper ×1 · store governed-throw ×2 |
| WB-D | cascade selector: typed OR an UNANCHORED compiled-pattern text read | KILLED | whole-reader KB ×10 |
| WB-D2 | cascade selector by an ANCHORED `.startswith` text read (no typed read) | KILLED | exact-set ×1 (structural only, as predicted) |
| WB-E | governed prefix anchored at position 0 of the thrown text (ignores the engine's `An error occurred: ` wrap) | KILLED | whole-reader KB ×24 · store ×3 |
| WB-F | the classifier reads text for EVERY kind (the `_TEXT_DECIDED_KINDS` guard deleted) | KILLED | `test_am36_1_2_3_a_typed_kind_never_reaches_the_text_branch` ×20 |
| WB-G | a second, text-only parse on `run_query` before the classifier | KILLED | whole-reader KB ×24 · mapping-helper ×1 |
| **WB-H** | **cascade selector by TEXT through a compiled pattern's `.match`, anchored at the cascade openings (no typed read)** | **SURVIVED: 1469 passed / 0 failed** (all 8 core files) | none. Killed by my KF (§A.4) |
| WB-I | the `run_query` retry decision by TEXT through an end-anchored compiled pattern (no typed read) | KILLED | 65 failed, incl. the RS detection pins (`_RETRYABLE_CONFLICT_KIND` mutation) |

**P0 controls bracketing WB-H.** These show the survival is not an artifact of my build:
- **WB-D and WB-H use the same compiled-pattern spelling and differ only in the anchor.** WB-D (unanchored) is red on KB, so KB sees a text selector exactly when an echo can spoof it.
- **WB-D2 and WB-H use the same anchor and differ only in spelling** (`.startswith` vs `.match`). WB-D2 is red on the exact-set pin, so that pin sees `startswith` but not `.match`.
- **KF's control leg** (current engine wording) is GREEN on WB-H, and its reworded leg is RED. So WB-H is behaviourally correct today and wrong under exactly the #120 condition (the engine rewords its message but keeps its type). The typed reference passes both legs.

## §FINDINGS
### F-1 (WB-H): the root-cause selector's TYPED decision has no pin that can fail against an echo-proof text selector
- **Bucket:** **PINNED PROPERTY, NEW CASE.**
  - The property is am-36 §1: the cascade decision reads `details.kind == "NotExecuted"` and never text. It is pinned by the exact-set pin plus whole-reader KB.
  - This is the 4th instance of the RS-5 typed-classifier class (FK-ADV-1 → B1/MP-3 → FK-a28c-1 → this). **By ruling, a 4th instance of RS-5 is a PINNED BOUND, never a reopen**, and I say so explicitly.
- **Chokepoint (the ONE production site):** `loremaster.store._txn._domain_root_cause`. It must compare `_detail_kind_of(failed.typed) == <the NotExecuted constant>` and contain no string test. **Builder requirement:** hold the cascade kind in a named module constant beside `_RETRYABLE_CONFLICT_KIND`. **Post-GREEN audit check:** run KF (§A.4) against the build.
- **Optional targeted pin (lead's call; cheap):** KF `test_KF_the_root_cause_is_chosen_by_the_typed_cascade_kind[reworded-typed-cascade]`. It is a forged transactional response whose cascade entries are typed `NotExecuted` with reworded text around a governed THROW. The defect it catches: a selector that reads the engine's cascade wording, which silently misattributes the root cause (and loses the governed class) the day the engine rewords a notice. This is #120's failure shape.
- **CLASS:** *every driver decision the engine types is taken from the type, and a fixture in which text and type DISAGREE exists for each such decision.* Today the retry decision has one (the RS mutation pins, WB-I killed) and the cascade decision has none.
- **DOMAIN SOURCE:** the typed decisions in `_txn`, which are `details.kind` ∈ {TransactionConflict, NotExecuted} (am-36 §1.1) plus the classifier's typed kinds.
- **SIBLINGS TRIED:** retry decision text-only (WB-I, killed) · retry OR text (WB-A/A2, killed) · cascade OR unanchored text (WB-D, killed) · cascade anchored `startswith` (WB-D2, killed structurally) · classifier on all kinds (WB-F, killed) · second parse (WB-C/G, killed).
- **SIBLINGS NOT TRIED:** the classifier's `Thrown` branch reading text via a compiled pattern (governed is OUR protocol: am-36 allows text there) · the typed `AlreadyExists` branch replaced by an anchored record-text pattern (the typed-txn R pins forge a typed dict with `details.kind` and other-kind wording, so likely killed; not run).
- **REPEAT CLASS:** yes. RS-5 / text-decides-where-typed: a28b (B1, MP-3) and a28c's own FK-a28c-1. The fixture half repeats the "FIXTURES MUST DISCRIMINATE" law: `typed_err_entry` makes text and kind co-vary, so no fixture can tell a text decision from a typed one. It is the arithmetic-alignment axis wearing a forgery helper.

### F-2 (KG): the exact-set text-reader derivation's predicate is a hand-list of spellings
- `_SEARCH_METHODS = {startswith, endswith, find, index, count, partition}`, plus a receiver literally named `re`.
- **Reproduction** (§A.4, run with the CONTRACT's own `_text_testers_in`):
  - `compiled-match`, `compiled-search`, `compiled-fullmatch` and `from-re-import` all go RED (not seen).
  - The control `re.search` is GREEN (seen).
  - In production, WB-A (a compiled-pattern retry reader) left the exact-set pin GREEN.
- **This is an HONEST spelling:** `_txn` itself holds `_BEGIN_COMMIT_KEYWORD_PATTERN = re.compile(…)`.
- **Bucket:** **PINNED PROPERTY, NEW CASE** (the same RS-5 class and the same chokepoint as F-1). The whole-reader KB sees the EFFECT of every echo-spoofable spelling (WB-A killed). The only spelling it cannot see is the echo-proof one, which F-1/KF closes.
- **The pin's own fix is test-self-hygiene** (an accepted residual unless the lead routes it): add `search`, `match`, `fullmatch`, `findall`, `finditer`, `sub`, `split` to the attribute set (any receiver), and flag a bare-name call imported from `re`. Or invert it to allowlist the safe: every `ast.Call` / `ast.Compare` touching a `str` is reported.
- **CLASS:** a guard's reach is a hand-list of spellings (INSTRUMENT 0, defeat #8's shape).
- **DOMAIN SOURCE:** the `re` module's public matching API (`re.__all__`) plus `str`'s search methods (`dir(str)`).
- **SIBLINGS TRIED:** 4 regex spellings.
- **SIBLINGS NOT TRIED:** `operator.contains`, `str.__contains__`, `match` statements with string cases, `str.split()` + `==`.
- **REPEAT CLASS:** yes. The author's own D-12 (the first derivation was blind to `169925f`'s `text: str` helpers), so this is the second strike on this instrument. Per the STOP-rule heuristic its reach is receding. Accept it as a bound, with KB/KF as the effect layer.

## §P1b — QUANTIFIER TABLE (the invariants a28c introduces or re-keys)
| invariant | ∀ or guarded? | receipt |
|---|---|---|
| an echoed phrase never moves class / attempts / root cause (whole-reader KB) | ∀ hosts × derived phrases × both paths | guarded on "an echo can reach the decision". An echo-proof TEXT decision is outside it: **WB-H survives** (F-1). Door-builds WB-A/A2/B/D/E/G killed |
| exactly one engine-text reader in `_txn` | ∀ functions in `_txn` (derived) | guarded by the spelling list: **KG** shows 4 unseen spellings (F-2); WB-A leaves it green |
| a typed kind never reaches the text branch | ∀ SDK kinds (`KIND_TO_CLASS`) × hostile texts | ∀. WB-F killed ×20 |
| R typed on the txn path | ∀ `AlreadyExistsError` detail kinds × wording | ∀. WB-C killed ×2 |
| the retry decision follows ONE typed constant | ∀ seams (RS mutation) | ∀. WB-I killed ×65 |
| the gate proceeds iff THIS keep is visible | ∀ relation-set powerset × mint orders × probes | ∀. B13 killed ×5 (ported), C2-b killed |
| every CAS domain handler is its own entry | ∀ handlers (per-handler key) | ∀. S7/S8 killed |
| every registry store call rides the one seam (KE) | ∀ calls in `agents.py` (AST) | ∀ over `agents.py`. B15 killed; a read through ANOTHER store object is am-32's named bound (not tried) |
| F-5: an undefined target answers typed after ONE `INFO FOR DB` | ∀ {agent, memory, message} × {minimal, realistic} | NOT TRIED empirically (author's R2-MM6/6b/7) |
| the owner triple is consistent by construction; `"empty"` adds no owner sentence | ∀ enum × {None, 0, >0}² | NOT TRIED empirically (author's MM1/MM8) |

## §P1c — REACH TABLE
Legs: **E** = empirical (a wrong build / probe run), **C** = construction inspection.
| instrument | reach DERIVED? | coverage checked? | effect vs proxy | one source, proven by mutation? | verdict |
|---|---|---|---|---|---|
| exact-set text readers (a28c) | functions: DERIVED from `_txn`'s AST. Predicate: a **hand-list of spellings** | allowlist + non-vacuity + synthetic control | STRUCTURAL | n/a | **MISSING PIN** (F-2). E: KG + WB-A |
| whole-reader KB (a28c) | phrases DERIVED; hosts are a live table | label completeness | EFFECT (class, attempts, root cause) | the attempt spy is THE driver | safe for echo-spoofable doors (E: 7 kills). Blind to echo-proof text (F-1) |
| `_engine_shapes.typed_err_entry` (forgery helper) | kind DERIVED **from text** | — | **PROXY**: text and kind can never disagree | ONE home (good), and ONE coupling (the proxy) | **MISSING PIN** (F-1's fixture half). E: WB-H + KF |
| RS detection mutation (`_RETRYABLE_CONFLICT_KIND`) | ∀ seams | per-seam | EFFECT | **proven by mutation** (E: WB-I reds 65) | safe |
| cascade-decision mutation | **ABSENT** | — | — | — | **MISSING PIN** (F-1) |
| C2 product + seam mutation pin | powerset GENERATED | constructibility leg | EFFECT | seam identity sweep (C) | safe (E: B13, C2-b) |
| per-handler CAS index + F-4 | THE ONE walker over the tree | KD count | STRUCTURAL | THE ONE resolver (C) | safe (E: S7, S8) |
| KE | `agents.py` AST, allowlist | fails closed on 0 | STRUCTURAL | — | safe (E: B15) |
| one-scanner, F-5 driver spy, validator / "empty" pins | as the author's §P1c | — | — | — | **NOT TRIED** (C only; agree with the author's rows) |

## §DUAL (P6b) — my enumeration from `git show 7017b54` BEFORE reading §5, then the diff
**Mine** (removed / re-keyed assertions, by file):
- `_exhaustion_fates` `server.py::_comms_register` row deleted;
- a28 `_read_of`/`_read_ran`, the `owner_classification is None` exemption, `_perturbed_value` next-member, the `unclassified` Literal (→ `"empty"`), the `except SurrealStoreError: assert table in removed` leg;
- RS `_discover_cas_handlers` (function key), private `_caught_classes`, the per-`try` `located`/`door_classes`/`guards` checks, `_MARKER_NAME`/`_MARKER_TEXT`, `_conflict_rollback_response` text-only;
- store / contention `_RETRYABLE_CONFLICT_MARKER` imports and text-only rollbacks (the governed/retry `_FailedStatement` pair);
- 58-tiers' text-only conflict;
- 58-cas_seam's `_GUARDED_CAS_DOORS | _TYPED_CAS_CATCHES` key read.

**Diff vs the author's U-1…U-28:**
- Every item of mine maps to a U-row: U-1..8 · U-9..14 · U-16..19 · U-20/21 · U-26 · U-14 · U-27.
- The `located`/`guards` checks survive, re-keyed (`test_retry_seam.py` `assert len(door_site) == 1`, and `…guards_the_typed_error_ABOVE…` fired on S8).
- a28's gating pin survives, re-keyed (`test_am32_a_field_is_None_iff_its_read_was_gated_off` is still present).
- U-15/U-23/U-28 are prose / never-committed items, which I cannot ground in the diff. That is expected, not a finding.
- **One DUAL asymmetry (not a deletion):**
  - Old virtue: "ONE detection authority, proven by MOVING it" (U-17). It was re-keyed for the retry decision and not extended to the cascade decision.
  - At `7017b54^` the cascade markers had no mutation pin either, so nothing was LOST. But am-36 made the cascade decision a second typed authority, and it shipped unpinned. → F-1.
- **U-27 (the `_comms_register` compensation row deleted):** grounded. The a28 reference deletes `minted_by_this_call` and its compensation. Adjudicated by am-32 K5/K6 (dropped deliberately). Agree.

## §SAT — targeted, ONE tree, both ways
- **Declared before the run** (`sat_set.txt`, 2026-09-29T20:13Z; extended at 20:14Z, before the run started, by the two keeps / visible-seam covering files):
  - the 10 test files changed in `7017b54`, plus `_engine_shapes.py` (support, not collected);
  - plus a19a / a19b (contract);
  - plus the `lore_impact` covering tests of the symbols my reference touches. `_classify_engine_error` → a28c. `is_retryable_conflict_error`'s consumers (`scout`, `inbox_awaiter`, `bootstrap_session`) → `test_scout.py`, `test_comms_await.py`, `test_surreal_harness.py`. `_domain_root_cause` / `_failed_statements`: lore lists no covering tests; indirect coverage is via store / contention;
  - plus keeps / visible seam → `test_keeps_store.py`, `test_visible_keeps_61b.py`;
  - plus the structural pins (RS, fates, 58 cas_seam / tiers);
  - plus `scripts/test_forgery_door_sweep.py`, added **by hand** (#507).
- lore index status at the time: `last_sweep` 638 s old. My reference edits live in the scratch copy, not in the watched tree, so no reconcile was needed for HEAD symbols.

**Legs.** Base = `169925f`-production (restored from HEAD's git objects in the SAME tree). Ref = my reference.
Runner: `pytest -n 8 --timeout=300 --tb=no -rfE` under the cgroup cap (`sat.sh`, §A.8).
| leg | pytest's own tail |
|---|---|
| ref (my reference, 2026-09-29 ~20:10Z) | **60 failed, 1700 passed** in 177.41s |
| base (`169925f` production, same test tree) | **457 failed, 1349 passed** in 174.35s |

The collected totals differ by 46: a28c's derived phrase domain shrinks on a build that deletes the four text markers, as the author's §2 predicts.

**Both-way diff.** Ids are taken from pytest's `FAILED`/`ERROR` summary lines. Base: 457 lines = 457 unique ids. Ref: 60 lines → 58 unique ids, because my whitespace split collapses two `test_surreal_harness.py` ids whose parameter carries a space. All 60 lines are inside the harness file adjudicated below. The P0 miss is in my own parser, stated here.
- **base-only (red at base, green on ref): 434** = a28c 248 · a28 87 · RS 69 · a28b 24 · a19a 2 · a19b 2 · store 1 · fates 1. **This is identical, file by file, to the author's §8 FINAL 434.** I CONFIRM the author's RED-at-base partition on an independent `_txn` reference.
- **shared (red on both): 23**, all packet-58-owned:
  - `test_reanchor_58_r3_tiers.py` 16;
  - `test_reanchor_58_r3_cas_seam.py` 4 (`tasks.py::claim_task`, `tasks.py::_reanchor_stragglers` ×2, `findings.py::_run_guarded`). The author's final run named 3, and the 4th, `findings.py::_run_guarded`, is also red at base, so it is not 63c-attributable; flagged for 58's owner;
  - `scripts/test_forgery_door_sweep.py` 3.
  - Not compared message by message (time); the ids are identical on both legs.
- **REF-ONLY: 35 (60 summary lines), ALL in `test_surreal_harness.py`**, raising `QueryError: Transaction conflict … can be retried`. They are HEAD's harness copy, which forges an UNTYPED conflict. That is exactly the author's §HELD D-9 (the harness re-key rides the build wave, BUILDER CONSTRAINTS item 1).
  - **Adjudicated empirically:** with the author's `held_harness.patch` applied (extracted md5 `7343bf28…`, which equals the stated md5), `test_surreal_harness.py` on my reference gives **56 passed, 0 failed**. The file was restored and `cmp`-verified against HEAD afterwards.
  - **63c-attributable REF-ONLY after §HELD: 0.**
- **CONFIRMED:** the author's "REF-ONLY 0, shared reds all 58/64b-owned" holds over MY set, with one condition I make explicit. The §HELD harness patch is REQUIRED in the build wave: without it, 35 harness pins go red on a correct build. It is already in the author's builder constraints, and I restate it because a builder who skips it meets 35 reds that no contract file explains.

## §RUNS
36 pytest runs. Every one used `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n ≤8 --timeout=300|120`, after an admission gate of MemAvailable ≥ 20 GiB (one wait, logged: `wait mem 19:50:31`). **0 cap kills, 0 timeouts.**
- core-8 on the reference ×1;
- WB-A, WB-A2, WB-B, WB-C, WB-D, WB-D2, WB-E, WB-F, WB-G, the two-set drive (9 builds × 2 runs) = 18 runs;
- WB-H / WB-I, the core-8 run ×2;
- the kill probe ×3 (ref, WB-H, WB-D2), plus 1 against base `_txn` (collected nothing visible through my filter; not used);
- predecessor ports ×8;
- SAT ×2;
- §HELD harness adjudication ×1.
- **Test store:** every harness DB goes through `unique_database()` (minted and reaped). I did not measure the `lore_test` namespace's size before and after, so I can make no growth claim either way.

## §P-PKG
- Built before reading the author's line: `parse_query_error` (read `surrealdb/errors.py`: it resolves `kind`, unwraps the v3.0.0 double-wrap, and maps `KIND_TO_CLASS`) → replace_with_adapter.
- `ServerError.details` / `.kind` → replace.
- **`surrealdb.errors._detail_kind(details)`** exists in the installed SDK (used by `ValidationError.is_parse_error`). Both references re-implement it. It is private, so `keep_with_trigger`, trigger: the SDK exports it.
- `re` → n/a.
- Diff vs the author: 1 addition (`_detail_kind`), no disagreement.

## §R — residuals, each with an individual verdict
- **R-1** (attack item 10, `typed_err_entry` mis-typing a hostile echo). Checked all 5 call sites (`test_reanchor_58_r3_tiers.py`, `test_surreal_store.py` ×3, `test_txn_contention.py`). None forges an echoed value, so there is NO fixture-reason pass today. **Verdict:** latent. The unanchored `CONFLICT_WORDS in result_text` would mis-type a forged ASSERT echoing "can be retried". Routed as test-hygiene (anchor it to the engine's COMMIT wording).
- **R-2** (F-2's pin fix). Test-self-hygiene; accepted residual unless routed.
- **R-3** (friction). `lore_index()` names the watched root's `git_ref` as `1d3cf98` while this checkout's HEAD is `bd017ee`. The impact answers I used are symbol-level and the symbols are unchanged, so I relied on them anyway. I did not file this. Lead: file or dismiss.
- **R-4** (NOT TRIED within the deadline):
  - AST-diff re-run of §A.5 (superseded by the empirical kills);
  - F-5 / FK-8 / validator / "empty" wrong builds;
  - attack items 1, 3, 5, 6, 7, 8, 11;
  - the one-scanner derivation;
  - 20× concurrency on my reference;
  - the KE sibling "a read through another store object".
- **Noted, not graded (per the brief):** FK-a28c-9 (my reference sends `Validation` to the text ladder = Reading A; it passes) · F-15 · F-11 · 58-r4.

## §A — instruments (VERBATIM; the scratch tree is disposable by design)
### §A.1 `advref_txn.py` — my independent `_txn` reference delta (am-35 §2 + am-36 §1) — md5 `1debf2560101e6697d0bee154644e977`
````
"""advref_txn.py <tree>: adversary-63c-i-a-a28c's INDEPENDENT reference delta for `_txn` (am-35 §2 + am-36 §1),
applied over the a28 + a28b reference (a SAT / mutation HOST, never a spec). Written from the a28c BUILDER
CONSTRAINTS item 1 + the installed SDK source (surrealdb.errors.parse_query_error / ServerError.details), WITHOUT
reading the author's myref_a28c_txn.py / myref_a28c_am36.py. Exact-once anchors; fails loud on a miss."""
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
T = root / "loremaster/loremaster/store/_txn.py"
text = T.read_text()


def sub(old: str, new: str, count: int = 1) -> None:
    global text
    assert text.count(old) == count, (old[:100], text.count(old))
    text = text.replace(old, new)


def cut_def(name: str) -> None:
    """Delete a top-level def (through the line before the next top-level def/decorator/class)."""
    global text
    lines = text.split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith(f"def {name}("))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith(("def ", "async def ", "class ", "@")))
    del lines[start:end]
    text = "\n".join(lines)


sub("from surrealdb.errors import AlreadyExistsError, ErrorKind, ServerError, SurrealError",
    "from surrealdb.errors import AlreadyExistsError, ErrorKind, ServerError, SurrealError, parse_query_error")
# --- the text markers the decisions used: DELETED; the typed kinds replace them -----------------------------------
sub('_RETRYABLE_CONFLICT_MARKER = "can be retried"\n',
    '# am-36 §1: the engine TYPES a retryable write-write conflict (details.kind, measured 3.2.4, both paths).\n'
    '_RETRYABLE_CONFLICT_KIND = "TransactionConflict"\n')
sub('_CASCADE_NOT_EXECUTED_MARKER = "was not executed due to"\n'
    '_CASCADE_COMMIT_ABORTED_MARKER = "aborted due to a prior error"\n'
    '_DOMAIN_CASCADE_MARKERS = (_CASCADE_NOT_EXECUTED_MARKER, _CASCADE_COMMIT_ABORTED_MARKER)\n',
    '# am-36 §1: every rollback cascade notice is typed details.kind NotExecuted (measured 3.2.4).\n'
    '_CASCADE_KIND = "NotExecuted"\n')
sub('_UNIQUE_VIOLATION_MARKERS = (("database record", "already exists"), ("database index", "already contains"))',
    '# am-35 §2: the ONE untyped identity shape, anchored at position 0 of the engine-authored text.\n'
    '_UNIQUE_INDEX_PREFIX = "database index `"\n'
    '# am-35 §2 item 3: the governed marker, anchored at the start of the engine\'s THROW wrapping.\n'
    '_GOVERNED_THROW_PREFIX = "an error occurred: " + _GOVERNED_CONFLICT_MARKER\n'
    '_TEXT_DECIDED_KINDS = frozenset({"Internal", "Validation"})')

# --- the classifier: typed first; text only for the untyped kinds (and bare-text callers) ------------------------
sub('''    if isinstance(raw_result, AlreadyExistsError):
        # Typed beats text (amendment 32 §1.1 item 3): the SDK's own discriminator decides.
        return _ERROR_CLASS_UNIQUE_VIOLATION if raw_result.record_id is not None else _ERROR_CLASS_UNSPECIFIED
    text = str(raw_result)
    if _is_retryable_conflict_text(text):
        return _ERROR_CLASS_RETRYABLE_CONFLICT
    lowered = text.lower()
    if _GOVERNED_CONFLICT_MARKER in lowered:
        return _ERROR_CLASS_GOVERNED_CONFLICT
    if any(all(part in lowered for part in marker) for marker in _UNIQUE_VIOLATION_MARKERS):
        return _ERROR_CLASS_UNIQUE_VIOLATION
    if _ASSERT_VIOLATION_MARKER in lowered:''',
'''    if isinstance(raw_result, AlreadyExistsError):
        return _ERROR_CLASS_UNIQUE_VIOLATION if raw_result.record_id is not None else _ERROR_CLASS_UNSPECIFIED
    lowered = str(raw_result).lower()
    if isinstance(raw_result, ServerError):
        if _detail_kind_of(raw_result) == _RETRYABLE_CONFLICT_KIND:
            return _ERROR_CLASS_RETRYABLE_CONFLICT
        if raw_result.kind == "Thrown":
            return _ERROR_CLASS_GOVERNED_CONFLICT if lowered.startswith(_GOVERNED_THROW_PREFIX) else _ERROR_CLASS_UNSPECIFIED
        if raw_result.kind not in _TEXT_DECIDED_KINDS:
            return _ERROR_CLASS_UNSPECIFIED
    elif lowered.startswith(_GOVERNED_THROW_PREFIX):
        return _ERROR_CLASS_GOVERNED_CONFLICT
    if lowered.startswith(_UNIQUE_INDEX_PREFIX):
        return _ERROR_CLASS_UNIQUE_VIOLATION
    if _ASSERT_VIOLATION_MARKER in lowered:''')

# --- _FailedStatement carries the ONE parse ------------------------------------------------------------------------
sub('''    index: int
    raw_result: Any
''', '''    index: int
    raw_result: Any
    typed: ServerError | None = None
''')

# --- typed detection -------------------------------------------------------------------------------------------------
cut_def("_is_retryable_conflict_text")
cut_def("_is_domain_cascade_notice")
sub('''    return _is_retryable_conflict_text(str(error))
''', '''    return _detail_kind_of(error) == _RETRYABLE_CONFLICT_KIND


def _detail_kind_of(error: object) -> object:
    """The engine's typed ``details.kind`` of a parsed server error (None for anything untyped)."""
    if not isinstance(error, ServerError) or not isinstance(error.details, dict):
        return None
    return error.details.get("kind")
''')
sub('''            if _is_retryable_conflict_text(str(failed.raw_result))
''', '''            if _detail_kind_of(failed.typed) == _RETRYABLE_CONFLICT_KIND
''')
sub('''    for failed in failed_statements:
        text = str(failed.raw_result)
        if text and not _is_domain_cascade_notice(text):
            return failed
    return failed_statements[-1]''', '''    for failed in failed_statements:
        if str(failed.raw_result) and _detail_kind_of(failed.typed) != _CASCADE_KIND:
            return failed
    return failed_statements[-1]''')
sub('''        _FailedStatement(index=index, raw_result=statement_result.get("result"))''',
    '''        _FailedStatement(
            index=index, raw_result=statement_result.get("result"), typed=parse_query_error(statement_result)
        )''')
sub('''    return any(_is_retryable_conflict_text(str(failed.raw_result)) for failed in failed_statements)''',
    '''    return any(_detail_kind_of(failed.typed) == _RETRYABLE_CONFLICT_KIND for failed in failed_statements)''')
# the txn raise site classifies the TYPED error (the record shape is typed there too), text evidence only as fallback
sub('''            error_class = _classify_engine_error(root_cause.raw_result)''',
    '''            error_class = _classify_engine_error(
                root_cause.typed if root_cause.typed is not None else root_cause.raw_result
            )''')
T.write_text(text)
print("advref_txn ok")
````

### §A.2 `wb.py` — the am-36 wrong builds WB-A…WB-I — md5 `63a9eb47e84c4a6f659b3fb0fa966c44`
````
"""wb.py <tree> <build> : apply ONE wrong build to <tree>'s _txn.py (over advref_txn). Exact-once anchors.
Restoring is the driver's job (content backup + cmp)."""
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
build = sys.argv[2]
T = root / "loremaster/loremaster/store/_txn.py"
text = T.read_text()


def sub(old: str, new: str) -> None:
    global text
    assert text.count(old) == 1, (build, old[:100], text.count(old))
    text = text.replace(old, new)


PATTERN_DEF = '_RETRYABLE_CONFLICT_KIND = "TransactionConflict"\n'
if build == "WB-A":  # run_query retry decision: typed OR a compiled-pattern text read (the module's own idiom)
    sub(PATTERN_DEF, PATTERN_DEF + '_RETRY_TEXT_PATTERN = re.compile(r"can be retried")\n')
    sub("    return _detail_kind_of(error) == _RETRYABLE_CONFLICT_KIND\n",
        "    return _detail_kind_of(error) == _RETRYABLE_CONFLICT_KIND or bool(_RETRY_TEXT_PATTERN.search(str(error)))\n")
elif build == "WB-A2":  # the transactional retry decision reads text through a compiled pattern
    sub(PATTERN_DEF, PATTERN_DEF + '_RETRY_TEXT_PATTERN = re.compile(r"can be retried")\n')
    sub("    return any(_detail_kind_of(failed.typed) == _RETRYABLE_CONFLICT_KIND for failed in failed_statements)",
        "    return any(_detail_kind_of(failed.typed) == _RETRYABLE_CONFLICT_KIND"
        " or _RETRY_TEXT_PATTERN.search(str(failed.raw_result)) for failed in failed_statements)")
elif build == "WB-B":  # routing-not-sharing INSIDE the allowlisted reader: the retry decision = the classifier's label
    sub("    if lowered.startswith(_UNIQUE_INDEX_PREFIX):\n",
        '    if "can be retried" in lowered:\n        return _ERROR_CLASS_RETRYABLE_CONFLICT\n'
        "    if lowered.startswith(_UNIQUE_INDEX_PREFIX):\n")
    sub("    return _detail_kind_of(error) == _RETRYABLE_CONFLICT_KIND\n",
        "    return _classify_engine_error(error) == _ERROR_CLASS_RETRYABLE_CONFLICT\n")
elif build == "WB-C":  # a SECOND parse at the txn raise site, from the raw text only (drops kind/details)
    sub("                root_cause.typed if root_cause.typed is not None else root_cause.raw_result\n",
        '                parse_query_error({"status": "ERR", "result": root_cause.raw_result})\n')
elif build == "WB-D":  # the cascade selector: typed OR a compiled-pattern (unanchored) text read
    sub(PATTERN_DEF, PATTERN_DEF + '_CASCADE_TEXT_PATTERN = re.compile(r"was not executed due to|aborted due to a prior error")\n')
    sub("        if str(failed.raw_result) and _detail_kind_of(failed.typed) != _CASCADE_KIND:\n",
        "        if str(failed.raw_result) and _detail_kind_of(failed.typed) != _CASCADE_KIND"
        " and not _CASCADE_TEXT_PATTERN.search(str(failed.raw_result)):\n")
elif build == "WB-D2":  # the cascade selector ANCHORED (prefix) text instead of typed — echo-proof by position
    sub("        if str(failed.raw_result) and _detail_kind_of(failed.typed) != _CASCADE_KIND:\n",
        '        if str(failed.raw_result) and not str(failed.raw_result).startswith(("The query was not executed", "Cannot COMMIT: the transaction was aborted")):\n')
elif build == "WB-E":  # the governed marker anchored at position 0 of the THROWN text (ignores the engine wrapping)
    sub('_GOVERNED_THROW_PREFIX = "an error occurred: " + _GOVERNED_CONFLICT_MARKER\n',
        "_GOVERNED_THROW_PREFIX = _GOVERNED_CONFLICT_MARKER\n")
elif build == "WB-F":  # the classifier reads text for EVERY kind except the typed AlreadyExists (Thrown included, unanchored)
    sub("        if raw_result.kind not in _TEXT_DECIDED_KINDS:\n            return _ERROR_CLASS_UNSPECIFIED\n", "")
elif build == "WB-G":  # a second parse inside the classifier's caller on run_query (text only) — typed kinds lost there
    sub("            error_class = _classify_engine_error(error)\n",
        '            error_class = _classify_engine_error(parse_query_error({"status": "ERR", "result": str(error)}))\n')
elif build == "WB-H":  # the cascade selector decides by TEXT (not the typed kind), anchored at position 0 via a compiled
    # pattern's .match — echo-proof by position, invisible to the exact-set derivation (receiver not `re`, `match` not listed)
    sub(PATTERN_DEF, PATTERN_DEF + '_CASCADE_OPENING = re.compile(r"The query was not executed due to|Cannot COMMIT: the transaction was aborted")\n')
    sub("        if str(failed.raw_result) and _detail_kind_of(failed.typed) != _CASCADE_KIND:\n",
        "        if str(failed.raw_result) and not _CASCADE_OPENING.match(str(failed.raw_result)):\n")
elif build == "WB-I":  # the run_query retry decision by TEXT through an end-anchored compiled pattern (no typed read)
    sub(PATTERN_DEF, PATTERN_DEF + '_RETRY_TAIL = re.compile(r"This transaction can be retried$")\n')
    sub("    return _detail_kind_of(error) == _RETRYABLE_CONFLICT_KIND\n",
        "    return bool(_RETRY_TAIL.search(str(error)))\n")
else:
    raise SystemExit(f"unknown build {build}")
T.write_text(text)
print(f"{build} applied")
````

### §A.3 `pb.py` — the predecessor builds, ported (+ C2-b) — md5 `1f41e5871a29392ec38a06ebc1255a57`
````
"""pb.py <tree> <build>: the a28b adversary's wrong builds (B1/B3/B13/S7/S8/B15 + MP-3's substring mechanism) PORTED
onto adversary-63c-i-a-a28c's reference (advref_txn over the a28/a28b reference + the a28c author's migrate/fk8 halves),
plus C2-b. Exact-once anchors; the driver restores from content. Original builds: REPORT-adversary-63c-i-a-a28b.md
§A.6a / §A.6d (md5 2b239f54… / 953715a1…)."""
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
build = sys.argv[2]
TXN = "loremaster/loremaster/store/_txn.py"
AG = "loremaster/loremaster/agents.py"
SV = "loremaster/loremaster/server.py"
FN = "loremaster/loremaster/findings.py"

U_CHECK = "    if lowered.startswith(_UNIQUE_INDEX_PREFIX):\n        return _ERROR_CLASS_UNIQUE_VIOLATION\n"
RQ_SITE = "            error_class = _classify_engine_error(error)\n"
TXN_SITE = "            error_class = _classify_engine_error(\n                root_cause.typed if root_cause.typed is not None else root_cause.raw_result\n            )\n"
GATE1 = ("                visible = await resolve_visible_keeps(keep_store, member_email=principal.email)\n"
         "                if keep_scope(existing_bare) not in visible:\n                    raise governed.GovernedDenied(foreign_denial)\n")
RS5 = "            except TxnUniqueViolationError:\n                # amendment 29 RS-5"
BUILDS: dict[str, list[tuple[str, str, str]]] = {
    # B1: the U text read OUTSIDE the one classifier (a helper both raise sites call first) — same behaviour.
    "B1": [
        (TXN, U_CHECK, ""),
        (TXN, "def _classify_engine_error(raw_result: object) -> str:",
         "def _text_says_unique(raw: object) -> bool:\n    return str(raw).lower().startswith(_UNIQUE_INDEX_PREFIX)\n\n\n"
         "def _classify_engine_error(raw_result: object) -> str:"),
        (TXN, RQ_SITE, "            error_class = (\n                _ERROR_CLASS_UNIQUE_VIOLATION if _text_says_unique(error) else _classify_engine_error(error)\n            )\n"),
        (TXN, TXN_SITE, "            error_class = (\n                _ERROR_CLASS_UNIQUE_VIOLATION if _text_says_unique(root_cause.raw_result)\n"
                        "                else _classify_engine_error(root_cause.typed if root_cause.typed is not None else root_cause.raw_result)\n            )\n"),
    ],
    # B3: the U check moved AFTER ASSERT / coercion (order swap; anchored still).
    "B3": [(TXN, U_CHECK, ""),
           (TXN, "    if _QUERY_RECURSION_DEPTH_MARKER in lowered:", U_CHECK + "    if _QUERY_RECURSION_DEPTH_MARKER in lowered:")],
    # MP3: the a28b RULED substring mechanism (unanchored noun + verb pair) in place of the anchored prefix.
    "MP3": [(TXN, U_CHECK, '    if "database index" in lowered and "already contains" in lowered:\n        return _ERROR_CLASS_UNIQUE_VIOLATION\n')],
    # B13: the pre-gate compares against the caller's one "primary" (min) visible keep — a multi-keep member is denied.
    "B13": [(SV, GATE1, GATE1.replace("if keep_scope(existing_bare) not in visible:",
                                      "if keep_scope(existing_bare) != min(visible, default=None):"))],
    # C2-b: the post-mint gate deleted (the pre-gate alone decides; a concurrent first mint by a foreigner is not re-checked).
    "C2b": [(SV, "            visible = await resolve_visible_keeps(keep_store, member_email=principal.email)\n"
                 "            if keep_scope(session_keep_bare) not in visible:\n                raise governed.GovernedDenied(foreign_denial)\n", "")],
    # S7: KEY COLLISION — RS-5's try gains a RE-READING exhaustion clause ABOVE the typed catch (then re-raises).
    "S7": [(AG, RS5, "            except TxnContentionExhaustedError:\n                await self._select_row(agent_id)\n                raise\n" + RS5)],
    # S8: a re-reading exhaustion clause in a SECOND try of a canonical door function (findings annotate).
    "S8": [(FN, "        row = await self._resolve_or_raise(id_or_number)\n        finding_id = self._bare_id(row.get(_ID_KEY))\n        now = datetime.now(UTC)\n        event: dict[str, Any] = {\n            _PROV_ACTOR: actor,\n            _PROV_ACTION: _ACTION_ANNOTATE,",
            "        try:\n            row = await self._resolve_or_raise(id_or_number)\n        except TxnContentionExhaustedError:\n            row = await self._select_row_by_id(str(id_or_number))\n            if row is None:\n                raise\n        finding_id = self._bare_id(row.get(_ID_KEY))\n        now = datetime.now(UTC)\n        event: dict[str, Any] = {\n            _PROV_ACTOR: actor,\n            _PROV_ACTION: _ACTION_ANNOTATE,")],
    # B15: a registry READ that bypasses AgentRegistry._query, invoked BEFORE the gate.
    "B15": [(AG, "    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:",
             "    async def _peek_raw(self, name: str) -> Any:\n        return await run_query(acquire=self._ensure_connection, drop=self._drop_connection, url=self._url,\n"
             "                               noun='agent peek', label='agent.peek.rejected',\n"
             "                               statement='SELECT * FROM agent WHERE name = $n', params={'n': name}, logger=logger)\n\n"
             "    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:"),
            (SV, "        if principal is not None:\n            if keep_store is None:  # pragma: no cover",
             "        await self.agent_registry._peek_raw(agent)\n        if principal is not None:\n            if keep_store is None:  # pragma: no cover")],
}
for path, old, new in BUILDS[build]:
    p = root / path
    text = p.read_text()
    assert text.count(old) == 1, (build, path, old[:90], text.count(old))
    p.write_text(text.replace(old, new))
print(f"{build} applied")
````

### §A.4 `kp_copy.py` — the kill probes KF + KG (`loremaster/tests/test_adv_a28c_kill_probes.py` in the scratch tree only) — md5 `a6f497dfdc4edc922ea673aa5e779c52`
````
"""adversary-63c-i-a-a28c kill probes (scratch only — never committed to the repo tree).

KF — amendment 36 §1: the ROOT-CAUSE SELECTOR reads the engine's TYPED cascade signal (details.kind NotExecuted),
never the text. Every forged fixture in the contract derives its kind FROM its text (`_engine_shapes.typed_err_entry`),
so text and kind never disagree and a text-deciding selector anchored at the cascade openings (echo-proof by position)
is indistinguishable from the typed one (wrong build WB-H: 1469/1469 green). This probe makes them DISAGREE — the
#120 shape (the engine REWORDS a notice, keeps its type): cascade entries typed NotExecuted with reworded text around
a substantive entry. The typed selector names the substantive entry; a text selector names a cascade notice.

KG — the exact-set text-reader derivation (am-36 §1.2 pin 3) must SEE a compiled-pattern reader (`_PATTERN.match(text)` /
`.search` / `.fullmatch`), the idiom `_txn` itself uses (`_BEGIN_COMMIT_KEYWORD_PATTERN`), and a `from re import search`
bare call. Runs the CONTRACT's own `_text_testers_in` over synthetic source.
"""

from __future__ import annotations

import ast

import pytest

from loremaster.store import _txn
from loremaster.tests import test_fixwave_a28c_63c_i_a as a28c

_REWORDED = [
    {"status": "ERR", "kind": "Query", "details": {"kind": "NotExecuted"}, "result": "Statement skipped: an earlier statement failed"},
    {"status": "ERR", "kind": "Thrown", "result": "An error occurred: governed_conflict:t:1"},
    {"status": "ERR", "kind": "Query", "details": {"kind": "NotExecuted"}, "result": "COMMIT refused after an earlier failure"},
]
_CONTROL = [  # the engine's CURRENT wording: text and kind agree — every correct AND every text build passes this
    {"status": "ERR", "kind": "Query", "details": {"kind": "NotExecuted"}, "result": "The query was not executed due to a failed transaction"},
    {"status": "ERR", "kind": "Thrown", "result": "An error occurred: governed_conflict:t:1"},
    {"status": "ERR", "kind": "Query", "details": {"kind": "NotExecuted"}, "result": "Cannot COMMIT: the transaction was aborted due to a prior error"},
]


@pytest.mark.parametrize("entries", [_CONTROL, _REWORDED], ids=["control-current-wording", "reworded-typed-cascade"])
def test_KF_the_root_cause_is_chosen_by_the_typed_cascade_kind(entries: list[dict]) -> None:
    failed = _txn._failed_statements({"result": entries})
    is_conflict, root_cause = _txn._rollback_verdict(failed)
    assert not is_conflict
    assert root_cause.index == 1, f"root cause = statement {root_cause.index}: {root_cause.raw_result!r}"
    label = _txn._classify_engine_error(root_cause.typed if root_cause.typed is not None else root_cause.raw_result)
    assert isinstance(_txn._domain_rejection_error(label, "m"), _txn.TxnGovernedConflictError), label


_READERS = {
    "compiled-match": "import re\nP = re.compile('x')\ndef f(text):\n    return P.match(text) is not None\n",
    "compiled-search": "import re\nP = re.compile('x')\ndef f(text):\n    return bool(P.search(text))\n",
    "compiled-fullmatch": "import re\nP = re.compile('x')\ndef f(text):\n    return bool(P.fullmatch(text))\n",
    "from-re-import": "from re import search\ndef f(text):\n    return search('x', text) is not None\n",
    "control-re-dot-search": "import re\ndef f(text):\n    return re.search('x', text) is not None\n",
}


@pytest.mark.parametrize("shape", sorted(_READERS))
def test_KG_the_derivation_sees_every_regex_spelling(shape: str) -> None:
    assert a28c._text_testers_in(ast.parse(_READERS[shape])) == {"f"}, shape
````

### §A.5 `drive.sh` — the two-set wrong-build driver (content backup + cmp restore) — md5 `6a4b946d75b1df8b9c4773c1a5cefa9f`
````
#!/usr/bin/env bash
# drive.sh <build...>: for each wrong build: content-backup _txn.py, apply wb.py, run the targeted pins under the
# cgroup cap + per-test timeout, restore from content, cmp byte-exact (#509). One summary line per build.
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dba90f35-f0c8-4241-8a8c-8bd751789310/scratchpad
cd $S/ref || exit 2
F=loremaster/loremaster/store/_txn.py
T=loremaster/tests
cp -a $F $S/txn_advref_backup.py
for b in "$@"; do
  while [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -lt 20 ]; do echo "wait mem $(date -u +%T)"; sleep 30; done
  python3 $S/wb.py . "$b" || { cp -a $S/txn_advref_backup.py $F; echo "$b APPLY-FAILED"; continue; }
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -p no:cacheprovider -q -n 8 --timeout=300 --tb=no -rfE \
    $T/test_fixwave_a28c_63c_i_a.py -k "am36 or am35_2 or KA or KB" > $S/wb_$b.log 2>&1
  rc=$?
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -p no:cacheprovider -q -n 8 --timeout=300 --tb=no -rfE \
    $T/test_surreal_store.py $T/test_txn_contention.py $T/test_retry_seam.py -k "not cas and not scanner and not handler" > $S/wb2_$b.log 2>&1
  rc2=$?
  cp -a $S/txn_advref_backup.py $F; cmp $F $S/txn_advref_backup.py || echo "RESTORE MISMATCH $b"
  echo "$b rc=$rc [$(tail -1 $S/wb_$b.log)] rc2=$rc2 [$(tail -1 $S/wb2_$b.log)]"
done
````

### §A.6 `drive_full.sh` — the core-8 wrong-build driver — md5 `f628f72c233abbc6e242085cd8950bc9`
````
#!/usr/bin/env bash
# drive_full.sh <build...>: as drive.sh, but runs the 8 core contract files (the SAT-1 set) per build.
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dba90f35-f0c8-4241-8a8c-8bd751789310/scratchpad
cd $S/ref || exit 2
F=loremaster/loremaster/store/_txn.py; T=loremaster/tests
cmp $F $S/txn_advref_backup.py || { echo "tree not at advref"; exit 2; }
for b in "$@"; do
  while [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -lt 20 ]; do echo "wait mem $(date -u +%T)"; sleep 30; done
  python3 $S/wb.py . "$b" || { cp -a $S/txn_advref_backup.py $F; echo "$b APPLY-FAILED"; continue; }
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -p no:cacheprovider -q -n 8 --timeout=300 --tb=short -rfE \
    $T/test_fixwave_a28c_63c_i_a.py $T/test_fixwave_a28_63c_i_a.py $T/test_fixwave_a28b_63c_i_a.py $T/test_retry_seam.py $T/test_surreal_store.py $T/test_txn_contention.py $T/test_fixwave_a19a_63c_i_a.py $T/test_fixwave_a19b_63c_i_a.py > $S/full_$b.log 2>&1
  rc=$?
  cp -a $S/txn_advref_backup.py $F; cmp $F $S/txn_advref_backup.py || echo "RESTORE MISMATCH $b"
  echo "$b rc=$rc [$(tail -1 $S/full_$b.log)]"
done
````

### §A.7 `drive_pb.sh` — the predecessor-port driver — md5 `e04dd6febe3773977c8b76805780ed36`
````
#!/usr/bin/env bash
# drive_pb.sh <build:group>...: content-backup the 4 touched production files, apply pb.py, run the group's targeted
# contract files (cgroup cap + per-test timeout), restore from content, cmp byte-exact.
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dba90f35-f0c8-4241-8a8c-8bd751789310/scratchpad
cd $S/ref || exit 2; T=loremaster/tests
FILES="loremaster/loremaster/store/_txn.py loremaster/loremaster/agents.py loremaster/loremaster/server.py loremaster/loremaster/findings.py"
mkdir -p $S/pbk; for f in $FILES; do cp -a $f $S/pbk/$(basename $f); done
for spec in "$@"; do b=${spec%%:*}; g=${spec##*:}
  case $g in
    txn) SET="$T/test_fixwave_a28c_63c_i_a.py $T/test_surreal_store.py $T/test_fixwave_a28b_63c_i_a.py";;
    gate) SET="$T/test_fixwave_a28c_63c_i_a.py $T/test_fixwave_a28_63c_i_a.py $T/test_fixwave_a28b_63c_i_a.py";;
    scan) SET="$T/test_retry_seam.py $T/test_fixwave_a28c_63c_i_a.py";;
  esac
  while [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -lt 20 ]; do echo "wait mem $(date -u +%T)"; sleep 30; done
  python3 $S/pb.py . $b >/dev/null || { echo "$b APPLY-FAILED"; for f in $FILES; do cp -a $S/pbk/$(basename $f) $f; done; continue; }
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -p no:cacheprovider -q -n 8 --timeout=300 --tb=no -rfE $SET > $S/pb_$b.log 2>&1; rc=$?
  for f in $FILES; do cp -a $S/pbk/$(basename $f) $f; cmp $f $S/pbk/$(basename $f) || echo "RESTORE MISMATCH $b $f"; done
  echo "$b ($g) rc=$rc [$(tail -1 $S/pb_$b.log)]"
  awk '/^FAILED|^ERROR/{sub(/ - .*/,""); sub(/loremaster\/tests\//,""); split($2,a,"["); c[a[1]]++} END{for(k in c) print "    "c[k]" "k}' $S/pb_$b.log
done
````

### §A.8 `sat.sh` — the targeted SAT, one tree both ways — md5 `b64cdd6a04a19661b6999dada0824d07`
````
#!/usr/bin/env bash
# sat.sh: the targeted SAT, ONE tree both ways: ref (my reference) then base (HEAD production restored from git
# objects), then the reference restored from content + cmp. Kill probes moved out of the tree for both runs.
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dba90f35-f0c8-4241-8a8c-8bd751789310/scratchpad
cd $S/ref || exit 2
SET=$(head -1 $S/sat_set.txt)
mv loremaster/tests/test_adv_a28c_kill_probes.py $S/
P="loremaster/loremaster/agents.py loremaster/loremaster/governed.py loremaster/loremaster/keeps.py loremaster/loremaster/principals.py loremaster/loremaster/server.py loremaster/loremaster/store/_txn.py"
mkdir -p $S/refprod; for f in $P; do cp -a $f $S/refprod/$(basename $f); done
run(){ while [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -lt 20 ]; do echo "wait mem $(date -u +%T)"; sleep 30; done
  COLUMNS=400 systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -p no:cacheprovider -q -n 8 --timeout=300 --tb=no -rfE $SET > $S/sat_$1.log 2>&1; echo "$1 rc=$? $(tail -1 $S/sat_$1.log)"; }
run ref
for f in $P; do git show HEAD:$f > $f; done; git status --short
run base
for f in $P; do cp -a $S/refprod/$(basename $f) $f; cmp $f $S/refprod/$(basename $f) || echo "RESTORE MISMATCH $f"; done
echo "restored ref production"; git diff --stat | tail -1
````

### §A.9 `sat_set.txt` — the DECLARED SAT set (line 2 = declaration time) — md5 `073b14c90dcaf9bfe62a3030e26bddcc`
````
loremaster/tests/test_exhaustion_fates.py loremaster/tests/test_fixwave_a28_63c_i_a.py loremaster/tests/test_fixwave_a28b_63c_i_a.py loremaster/tests/test_fixwave_a28c_63c_i_a.py loremaster/tests/test_governed_migration_63a.py loremaster/tests/test_reanchor_58_r3_cas_seam.py loremaster/tests/test_reanchor_58_r3_tiers.py loremaster/tests/test_retry_seam.py loremaster/tests/test_surreal_store.py loremaster/tests/test_txn_contention.py loremaster/tests/test_fixwave_a19a_63c_i_a.py loremaster/tests/test_fixwave_a19b_63c_i_a.py loremaster/tests/test_scout.py loremaster/tests/test_comms_await.py loremaster/tests/test_surreal_harness.py scripts/test_forgery_door_sweep.py loremaster/tests/test_keeps_store.py loremaster/tests/test_visible_keeps_61b.py
2026-09-29T20:13:24Z
````

## VERDICT
**`SUFFICIENT-FOR-BUILD`.**
- **NEW PROPERTY: 0.**
- **PINNED PROPERTY, NEW CASE: 2**, both RS-5-class. Per the ruling, a 4th RS-5 instance is a PINNED BOUND, never a reopen:
  - F-1 (WB-H survives all 1469). This is a builder requirement at `_txn._domain_root_cause`: typed `NotExecuted`, no string test, the kind held in a named constant. The post-GREEN audit runs KF. KF is offered as ONE optional targeted pin.
  - F-2 (the exact-set derivation's spelling list). Accepted residual / test hygiene.
- **Predecessor 7/7 KILLED**, plus C2-b.
- **Past-cap cost note:** this round used 36 targeted runs and about 90 minutes of wall-clock.
