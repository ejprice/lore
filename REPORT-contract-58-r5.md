brief-base v27 read · brief project v7 read

# REPORT — contract-58-r5 (packet 58 revision 5, re-base onto SDK3/66 + 63c-i-a)

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read · **BRIEF CONFLICT:** the brief's "§MUTATION (declared-RED both ways via `scripts/mutation_proof.py`)" — refused per the tdd-contract / brief-base §2 role boundary (building wrong builds is the adversary's; am-15 §5 routes exactly those builds to ONE delta grade).
- **State: done-with-deviations** (at HEAD-at-report `39f4c33`; tests only + the registry entry + the granted probe; no production code).
- **Deviations:** D-R5-1 I first built the generated tiny shrinks of am-15 §1.2; §8 superseded them → all 8 files restored to HEAD and re-keyed to §8's one 5 000/800 fixture (`r5_rekey.py`) · D-R5-2 reference re-anchored by me (reading A of "do not write one yourself" — §BRIEF CONFLICT note) · D-R5-3 A-9's positive control composes a synthetic cap+1-row fragment, not "the fragments the ledger built" · D-R5-4 the §9.2 63c member additions are DERIVED from `_txn` (empty pre-58), not spelled · D-R5-5 the committed probe adds type annotations + wraps vs §INSTRUMENT (gates) · D-R5-6 the q1c edit is unnecessary (it reads q1b's set) · D-R5-7 two bugs of mine caught by my own receipts and fixed: r4_state's pruned fixture import (13 setup errors), and the Step-2 sweep missing the `CAP` alias.
- **Packages considered:** `more_itertools.constrained_batches` keep (am-8; only `max_size`/`get_len` change) · `_txn.fragment_rows` reuse (read at `99044d0`) · no new mechanism.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 13 new test-support symbols, all dispositioned (§DRY LEDGER); 7 retired before shipping.
- **Graded:** n/a — authorship. Base `99044d0`; HEAD-at-report `39f4c33` (DIFFERENT, 6 ahead: amendment 15 + its §8/§9 + INDEX docs — **0 code files changed**, `git diff --stat 99044d0..HEAD -- loremaster lore* scripts` empty).
- **Decisions needed:** none blocking. Two findings for the lead's routing: **#613** (rrf ordering red once in 5 runs, unrelated) · **#614** (forgery-door sweep red at plain HEAD; its packet-58 registry entry would mask it as adjudicated). F-3: the packet doc still names the deleted constants (am-15 §7).
- **Headline receipts:** Step 1 — §HELD 1/3 + the r1–r4 chain re-extracted md5-exact; 5 anchor drifts (A1–A5) + 1 semantic drift no anchor sees (B-6, 640 REF reds) + 1 §HELD-part-1 drift (part 4 delivered); 63c's a28b sweep 29/29 and a28c echo sweep 211/212 GREEN over 58's classes. RED@HEAD: `declared=27 matched=27 mismatched=0` (base3). SAT: ref3 full + deltas → **0 r5-attributable reds**; all **67 am-15 §9 cells GREEN** on the reference (ref3d), ref4d `817 passed`. Gates: typecheck `RED_ADJUDICATED` (84, packet-58/64b-i), ruff GREEN, `--verify-registry` EXIT=0 (final4 receipt in §GATES-2).
- **Commit-ready paths (lead commits; `git commit -- <paths>`):** `loremaster/tests/{_reanchor_58_support.py, test_supersede_reanchor_58.py, test_reanchor_58_r2_am2.py, test_reanchor_58_r2_probes.py, test_reanchor_58_r2_rulings.py, test_reanchor_58_r2_scale.py, test_reanchor_58_r3_convergence.py, test_reanchor_58_r3_probes.py, test_reanchor_58_r4_state.py, test_reanchor_58_r5_rows.py, test_am37_13_3_63c_i_a.py, test_mint_kind_carveout_q1b.py, test_fixwave_a28c_63c_i_a.py}`, `scripts/pending_contracts.yaml`, `scripts/probe_hub_txn_58.py`, this report. §HELD stays a patch set (parts 1, 3 and NEW part 4 — §HELD).
- **Receipt pointers:** §RE-BASE-STEP1 · §INVENTORY · §STEP1-RESULT · §FOLD · §FLAGS · §DUAL / §DUAL-63c · §FORALL · §HELD (part 4) · §RE-BASE · §BUILDER CONSTRAINTS · §COLD-AUDIT SET · §SWEEP-R5 · §RED@HEAD · §SAT / §SAT-DELTA2 · §GATES · §RESIDUALS · §INSTRUMENTS · Fan-out line below.
- **Fan-out:** haiku 14 (test/gate runners; 3 reported the wrong log or prematurely — each re-read by me from the named log) · sonnet 0 · peak 3. Deadline: 150 min from spawn (~21:30Z → ~00:00Z); finished ~23:15Z.

## Capability check (brief-base §4)
- Demanded: lore tools, comms, scratch_copy.sh, haiku-runner/worker spawns, SendMessage wake to sidecar-58-1.
- Have: lore tools loaded (ToolSearch `+lore`), registered on comms (`contract-58-r5`, session pkt58-20261109).
  Agent tool present. SendMessage is deferred — loaded on demand.
- Landmine recall: k=50 returned 8 notes (< 50, not cut off).

## Routing table (written before first sweep — brief-base §3)
| step | tier | who | reason |
|---|---|---|---|
| read r4 SUMMARY/§HELD/§RE-BASE/§BUILDER CONSTRAINTS/§INSTRUMENTS | 3 | self | contract judgment input; short targeted reads |
| scratch copy + provenance assert | 1 | self (inline) | single command on critical path, output read whole |
| apply §HELD 1/3 + reference chain to scratch, record failing anchors | 1→3 | self | anchor-failure verdicts depend on 66's reshape (state elsewhere) |
| declare_set.py re-derive on new tree | 1 | self inline | one command, output feeds the runs |
| BASE / REF targeted pytest runs | 1 | haiku-runner ×2 (parallel) | test runs |
| classify reds (63c-owned GREEN legs, 66-attributable) | 3 | self | verdicts depend on cross-module state |
| Step 2 rename sweep (statement counts, deleted constants) over 58 tests/§HELD/ref chain/constraints | 1 | haiku-worker (literal grep, coverage line) | literal sweep; grep is the right tool (rename exhaustiveness) |
| adjudicate sweep hits | 2/3 | self | each hit's verdict depends on 66's rulings F12/F19/F21/R36 (state elsewhere) — a sampled draft would miss cross-doc rulings |
| Step 3 fold list → tests | 3 | self | contract authorship |
| RED@HEAD / SAT / mutation runs | 1 | haiku-runner | test runs |
| currency typecheck/ruff, --verify-registry | 1 | haiku-runner | gate runs |

## §RE-BASE-STEP1 — scratch, §HELD, reference chain on HEAD `99044d0` (measured 2026-11-09 21:3x–21:4xZ)
- **Scratch trees** (both `scripts/scratch_copy.sh`, EXIT=0, provenance asserted by the tool):
  - BASE `…/scratchpad/c58r5` — `loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/c58r5/loremaster/loremaster/__init__.py`
  - REF `…/scratchpad/c58r5ref` (same assertion; printed again in each SAT log header).
- **§HELD** re-extracted by address and md5-checked: part1 `5a43aeb:REPORT-contract-58.md` L173–557 = `dbba9753cbe960cda178f42687039c2d` ✔; part3 `c42eeaf:REPORT-contract-58-r2.md` L177–195 = `15f38e319cb8d3c25456084dda4989b1` ✔. `git apply --check` EXIT=0 both; APPLIED in both trees (8 paths dirty: server.py, surreal_schema.py, _task_fakes.py, test_link5_render_containment.py, test_mcp_server.py, test_surreal_store.py, + new test_supersede_render_58.py).
- **Reference chain** re-extracted by heading (`extract_fence.py`, §INSTRUMENTS) — every md5 equals its recorded value: build_ref58 `5915c12e…` ✔ · my_ref `de2d2801…` ✔ · my_ref_am6 `2176fb8e…` ✔ · my_ref_r3 `c5678ba7…` ✔ · my_ref_r4 `ec33542d…` ✔ (also declare_set `c6d0e1bc…`, member_diff `44bb1656…`, setdiff `8910cbe4…`, owners `2d99ea7f…` ✔).
- **Chain replay on HEAD, fail-fast (the scripts as written):** build_ref58 EXIT=0 · **my_ref EXIT=1** · my_ref_am6 EXIT=1 (cascade: its anchor is text my_ref adds) · my_ref_r3 EXIT=1 (cascade + own drift). Each script writes only at its end, so nothing partial landed.
- **Every anchor that no longer applies** — `anchor_audit.py` (§INSTRUMENTS), which replays the chain with each exact-once assert turned into RECORD-and-skip: `TOTAL-MISSES 5`, all in `store/_txn.py`'s classifier/raise path:

  | # | script | anchor (head) | count | drift attributed to | what moved |
  |---|---|---|---|---|---|
  | A1 | my_ref | `if _GOVERNED_CONFLICT_MARKER in lowered:` → `return _ERROR_CLASS_GOVERNED_CONFLICT` | 0 | **63c-i-a `34d0b6b`** (count 1 at `a77dc00`, 0 at `34d0b6b`) | the classifier is TYPED: `(untyped or kind == ErrorKind.THROWN) and lowered.startswith(_ENGINE_THROW_PREFIX + _GOVERNED_CONFLICT_MARKER)` (`_classify_engine_error`); HEAD docstring: "Nothing is parsed from text" |
  | A2 | my_ref | `if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:` / `return TxnGovernedConflictError(message)` | 0 | 63c-i-a / 66 (first line still present; the return now passes `error_class=…, kind=…`) | `_domain_rejection_error`'s constructors carry `error_class` + `kind` (am-37 §15.2) |
  | A3 | my_ref_r3 | `if CLAIM_LOST_MARKER in lowered:` | 0 | cascade of A1 (my_ref adds it) | — |
  | A4 | my_ref_r3 | `if error_class == _ERROR_CLASS_CLAIM_LOST:` … `return TxnDomainRejectionError(message)` | 0 | cascade of A2 + the same constructor reshape | — |
  | A5 | my_ref_r3 | `f"({error_class}); {_SERVER_LOG_HINT}",\n            )\n        last_conflict` | 0 | 66 / 63c-i-a: the non-conflict raise in `execute_transaction` now passes `kind=_typed_kind(typed_root),` before `)` | — |
- ⚠ **A1–A4 are not mechanical re-anchors — they are a DESIGN collision (STOP-class, am-12 §5 / am-13's 36 REF-ONLY reds):** the r1–r4 reference classifies 58's four classes (`TxnClaimLostError`, `TxnCasLostError`, `TxnReanchorStragglerError`, `TxnHealChunkError`) by **substring of the lowered engine text** (`CLAIM_LOST_MARKER in lowered`, …). 63c-i-a's landed typed decision forbids exactly that (its `TestTheClassIgnoresEveryEchoedPhrase63cIAa28c` sweep × 58's markers is the am-13 36-red set). HEAD's own idiom for a THROW-carried marker is `kind == THROWN and lowered.startswith(_ENGINE_THROW_PREFIX + MARKER)` (governed conflict). Re-anchoring onto that idiom is the obvious reading; re-anchoring with `in lowered` would keep the 36 red. **Routed to sidecar-58-1** (§INVENTORY F-RB-1) — I do not pick the classifier form for 58's classes silently.
- ⚠ **The chain also reads the DELETED constant at RUNTIME** (§INVENTORY B-rows): `build_ref58.py` (`max_reanchor_dependents`: `(_txn_module.TXN_STATEMENT_HARD_CAP - fixed) // per`), `my_ref.py` (`_composed_statement_count` "the count compose checks against TXN_STATEMENT_HARD_CAP"; heal packer `cap = _txn_module.TXN_STATEMENT_HARD_CAP`), `my_ref_r3.py` (the `constrained_batches(..., cap, ...)` packer). All anchors apply (they are 58's own inserted text), so the chain "applies" — **but the built reference raises `AttributeError` on every supersede-cap / heal-pack path at HEAD.** The r4 reference is therefore NOT a correct build at HEAD; a REF SAT leg on the unmodified chain measures that crash, not the contract.

## §INVENTORY — Step 2: every r1–r4 pin, §HELD hunk, reference-chain fact and BUILDER CONSTRAINT resting on statement counts or the deleted constants (measured 2026-11-09 at HEAD `99044d0`)
- **Instrument:** a literal `grep -nEi` (rename exhaustiveness for a deleted constant — the sanctioned grep case; said out loud), pattern `STATEMENT_HARD_CAP|STATEMENT_WARN|statement[ _-]?cap|statement[ _-]count|statements_per|per_statement|statement budget|STATEMENT_CAP|_statement_cap|max_statements|statements? per (chunk|txn|transaction)|ROW_HARD_CAP|ROW_WARN|row[ _-]cap`, bare/anchor-free. Corpus: every 58-owned test file at HEAD (`loremaster/tests/*58*.py` ×18 incl. held `test_supersede_render_58.py`, `_reanchor_58_support.py`, `_catch_sites.py`, `_exhaustion_fates.py`, `test_exhaustion_fates.py`), the 5 chain scripts + 2 §HELD patches, r1–r4 reports at their archival shas, the kickoff + 14 amendments, the packet doc. **Coverage: `files_opened=52 hits=88`.** Hits file: `…/scratchpad/sweep/hits.txt`.
- **HEAD facts the re-size rests on (read, `store/_txn.py` / `store/surreal.py` at `99044d0`):**
  - `TXN_ROW_HARD_CAP = 50_000`, `TXN_ROW_WARN_THRESHOLD = 10_000`; `compose()` reads the cap LIVE and raises `TxnRowCapExceededError` at build time.
  - `fragment_rows(fragments)` is "THE one row count": `fragment.rows` if declared, else `len(fragment.statements)`. **58's fragments (supersede/heal/claim) declare no `rows`, so for them rows ≡ statements**: the arithmetic `fit = (CAP − fixed) // per` keeps its form; only the constant (5000 → 50 000) and the counter (`_composed_statement_count` → `fragment_rows`) change.
  - The size WARN is `SurrealStore._log_transaction_size`: `extra={"statement_count", "param_count", "row_count"}`, WARNING iff `row_count > _txn.TXN_ROW_WARN_THRESHOLD` (R9 D2). The `statement_count` attribute 58's warn pins filter on is STILL emitted; the threshold it crosses is now the ROW threshold.
  - At the real cap, fit ≈ (50 000 − fixed)//3 ≈ 16 665 dependents, so r3/r4's `fit±1` / `2·fit+1` convergence SCALES become ~33k–100k-row fixtures — the reason F19 rules a SHRUNK monkeypatched cap.

### A — test pins (58-owned; every one is a bare read R36 D′ registered under `packet-58-contract`)
| id | file · symbol | rests on | proposed re-base (for the sidecar to rule) |
|---|---|---|---|
| A-1 | `test_reanchor_58_r2_am2.py` (L74/81) `predicted_chunks(cap+1, fixed, per, _txn.TXN_STATEMENT_HARD_CAP)` | packer chunk prediction vs the statement cap | read `_txn.TXN_ROW_HARD_CAP` live, under a shrunk monkeypatched cap (F19/F21) |
| A-2 | `test_reanchor_58_r3_probes.py` (L177) `all(len(s) <= TXN_STATEMENT_HARD_CAP …)` over heal calls | per-transaction size ≤ statement cap | `fragment_rows(...) <= TXN_ROW_HARD_CAP` (or `len(s)` ≡ rows for un-annotated) at the shrunk cap |
| A-3 | `test_reanchor_58_r3_convergence.py` (docstring L12–13; L136–141 `CAP = getattr(_txn, "TXN_STATEMENT_HARD_CAP", None)`) — the `SCALES` (fit−1, fit, fit+1, 2fit+1) | fit derived from the statement cap | fit from `TXN_ROW_HARD_CAP` at a shrunk cap; scales unchanged in form |
| A-4 | `test_reanchor_58_r2_rulings.py` (L154/200/204/236/357 cap/fit; L210 `hasattr(r, "statement_count")` WARN filter) | statement cap; statement-keyed warn | row cap; warn filter stays valid (field still emitted) but threshold is rows |
| A-5 | `test_supersede_reanchor_58.py` (L537/591/617/619: accessor == `(CAP − fixed)//per`, incl. the in-suite cap-MUTATION leg; L676–697: `crossing = (TXN_STATEMENT_WARN_THRESHOLD − fixed)//per + 1`, exactly ONE WARNING carrying `statement_count` > threshold) | F-1 derived hub cap; am-2 (b) size WARN | cap leg → `TXN_ROW_HARD_CAP`; mutation leg monkeypatches the ROW cap; warn leg → `TXN_ROW_WARN_THRESHOLD` (shrunk) and asserts `row_count` > threshold |
| A-6 | `test_reanchor_58_r2_probes.py` (L125 accessor; L330 warn filter; L342 `monkeypatch.setattr(_txn, "TXN_STATEMENT_HARD_CAP", … − 300)`) | statement cap (already a monkeypatched shrink) | same shrink on `TXN_ROW_HARD_CAP` |
| A-7 | `_reanchor_58_support.py` (L465 docstring; `ComposeSpy` reads "the count its hard cap checks") | the ONE counter = statement count | the spy must count what `compose` bounds = `fragment_rows`; for un-annotated fragments identical |
| A-9 | `test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED::test_one_past_the_cap_is_REFUSED_byte_inert_and_TEACHES` — `assert "statements, exceeding the hard cap" not in message` | the RETIRED `compose()` statement-cap error text | **VACUOUS at HEAD**: `compose` now raises `TxnRowCapExceededError("composed transaction writes {rows} rows, over the {cap}-row cap …")`, so the substring can never occur and a build serving the bare compose refusal passes this leg. Re-pin on the OUTCOME: the served error is `TaskLedgerError` naming the cap, NOT a `TxnRowCapExceededError` (nor chained from one), and `compose` was never asked to build the over-cap transaction (spy). Same class in the test-side `_spy` (`sum(len(fragment.statements) …)`) — a private counter beside `fragment_rows` (A-7). |
| A-10 | `test_reanchor_58_r2_probes.py::test_PR13_the_task_WARN_rides_the_ONE_telemetry_policy` — 300 dependents, house `_log_transaction_size` stubbed, assert NO `statement_count` WARNING | 300 × 3 ≈ 900 statements > the RETIRED 800-statement threshold | **VACUOUS at HEAD**: ~900 rows ≪ `TXN_ROW_WARN_THRESHOLD` 10 000, so a build with a PRIVATE warn copy (the wrong build PR13 exists to kill) is silent here too. Re-pin: shrink `_txn.TXN_ROW_WARN_THRESHOLD` (monkeypatch, F21 read-live) below the hub's rows, with a positive control that the UN-stubbed house policy DOES warn at that size (so the negative leg can see a warn). Same re-size for `test_crossing_the_WARN_threshold_logs_ONE_warning_and_SUCCEEDS` (A-5) and r2_rulings L210 (A-4). |
| A-11 | `test_reanchor_58_r2_probes.py::test_PR14_the_accessor_follows_the_shared_hard_cap` (`monkeypatch TXN_STATEMENT_HARD_CAP − 300 ⇒ baseline − 100`) | statement cap | `AttributeError` at HEAD (monkeypatch `raising=True` default); re-base onto `TXN_ROW_HARD_CAP` unchanged in form (per = 3 rows) |
| A-8 | `test_exhaustion_fates.py` (L579–609) | already re-keyed to `TxnRowCapExceededError` by 66's servicer (`da24469`, R36 Fork 2) | **no change** — verify GREEN in SAT |

### B — reference chain (a SAT host, not a spec — but it is what the SAT receipt is measured on)
| id | where | rests on | consequence at HEAD |
|---|---|---|---|
| B-1 | `build_ref58.py` `max_reanchor_dependents` → `(_txn_module.TXN_STATEMENT_HARD_CAP - fixed) // per` | deleted constant | `AttributeError` at runtime |
| B-2 | `my_ref.py` `TaskLedger._composed_statement_count` ("the count `compose` checks against `TXN_STATEMENT_HARD_CAP` — the ONE counter") | am-3 §1 ONE counter = statement count | compose now bounds `fragment_rows`; a second private counter is a #102-shape duplicate unless it IS `fragment_rows` |
| B-3 | `my_ref.py` heal packer `cap = _txn_module.TXN_STATEMENT_HARD_CAP` | deleted constant | `AttributeError` |
| B-4 | `my_ref_r3.py` `constrained_batches(items, cap, get_len=<stored weight>, strict=True)` (am-8 PKG) | `max_size` = statement cap | `max_size=_txn.TXN_ROW_HARD_CAP` read live, `get_len` = `fragment_rows` weight |
| B-5 | anchors A1–A5 (§RE-BASE-STEP1) | 63c-i-a typed classifier + 66 `kind=` | chain fails to apply |

### C — §HELD hunks
- **None.** 0 hits in `held_part1.patch` / `held_part3.patch`; both apply clean at `99044d0`.

### D — BUILDER CONSTRAINTS and contract-report facts (r1–r4)
| id | where | rests on |
|---|---|---|
| D-1 | r1 `REPORT-contract-58.md` §SUMMARY decision (b) + L580: heal transaction size vs `TXN_STATEMENT_HARD_CAP` | statement cap |
| D-2 | r1 L61 F-1 derived cap row `(HARD_CAP − fixed)//per` measured off a compose spy | statement cap |
| D-3 | r1 L149 "the WARN is the house telemetry record (a WARNING carrying `statement_count`) … `TaskLedger._apply` through `SurrealStore._log_transaction_size` — ONE policy"; L586 the WARN pin keys on `statement_count` | warn now row-triggered; field still present |
| D-4 | r2 BC-r2-2 (L147): "the supersede accessor and the heal packer consume ONE statement counter" (am-3 §1) | the ONE counter |
| D-5 | r2 L54 AM2C "a correct packer that fits 4999 statements in ONE chunk" (PR18r2) | 5000-statement cap |
| D-6 | r3 BC-r3-1 (L177) + L75: packer IS `constrained_batches(items, TXN_STATEMENT_HARD_CAP, get_len=…, strict=True)` | statement cap |
| D-7 | r4 BC-r4-3(a): heal driven at `2·fit+1` rows | fit from the statement cap |
| D-8 | rulings: kickoff L15/L21/L50/L248 (`cap_dependents(K) = (TXN_STATEMENT_HARD_CAP − (4+K)) // 3`, "REUSE `TXN_STATEMENT_HARD_CAP`"); am-2 L40; am-3 L15/36/39 (ONE statement-counting function, greedy packer vs the cap); am-8 L13/23/30/32/48 (PKG `max_size=TXN_STATEMENT_HARD_CAP`, `get_len` = the ONE counter); packet doc L35–36 | **rulings the sidecar re-rules** — I edit none |

### F — forks surfaced by the inventory (sidecar-58-1 rules; I pick nothing silently)
- **F-RB-1 (classifier form for 58's four classes).** Reading (i): HEAD's typed idiom — `(untyped or kind == THROWN) and lowered.startswith(_ENGINE_THROW_PREFIX + MARKER)`, constructors take `error_class=…, kind=…`. Reading (ii): keep r4's substring `MARKER in lowered`. (ii) contradicts 63c-i-a's landed decision and keeps the am-13 36 reds. **I would pick (i)**; the provisional reference below builds (i) so the 36 can be measured.
- **F-RB-2 (the ONE counter).** Reading (i): 58's `_composed_statement_count` is DELETED and every consumer (accessor, packer `get_len`, `ComposeSpy`) calls `_txn.fragment_rows` — one counter, owned by `_txn`. Reading (ii): keep 58's private counter renamed to rows. (ii) is copy #2 of `fragment_rows`'s policy. **I would pick (i).** Note: on 58's un-annotated fragments the two are indistinguishable by any behaviour test (rows ≡ statements), so a build keeping a private `len(statements)` counter survives every pin; a discriminating pin would need an annotated (`rows=`) fragment in 58's path, which 58 does not emit — so this is a sharing-by-MUTATION audit proof (global law: a run, not a standing test), not a pin. Ruling requested on whether that is acceptable as a named bound.
- **F-RB-3 (the size WARN).** 58's am-2 (b) WARN pins cross `TXN_STATEMENT_WARN_THRESHOLD` (800) and filter on `statement_count`. At HEAD the house WARN is row-triggered at 10 000 and carries `row_count`. Reading (i): pins cross a SHRUNK `TXN_ROW_WARN_THRESHOLD` (monkeypatched, F19/F21) and assert on `row_count`. Reading (ii): keep `statement_count` as the asserted field. **I would pick (i)** (D2: rows are the one strain measure).
- **F-RB-4 (shrink mechanics).** Monkeypatching `_txn.TXN_ROW_HARD_CAP` also shrinks `compose()`'s own refusal (read live). For the hub cap that is intended (accessor and compose must agree). For the heal packer at `2·fit+1` it is too: chunks must fit the shrunk compose bound. **No fork if ruled as F19 reads** — stated so the sidecar can confirm one cap governs both.

## §PROVISIONAL-REF — the r4 chain re-based onto HEAD with picks (i) for F-RB-1/2/3 (a SAT host, NOT A SPEC; pending amendment 15), built 2026-11-09 ~21:40Z
- Builder: `build_ref_r5.py` (§INSTRUMENTS, md5 `4e49adf7db449d718049360e56ab7ba9`) on `c58r5ref` (HEAD `99044d0` + §HELD 1/3). Replays the r1–r4 chain in place with the exact-once asserts turned into record-and-skip and **asserts the skipped set == the five declared drifts A1–A5** (output: `chain replayed; skipped exactly the 5 declared anchors`), then the r5 delta with exact-once anchors. EXIT=0.
- Result md5s: `tasks.py 263b249a…` · `_txn.py 1cb399c1…` · `findings.py 0a4c5738…` · `lease.py eebfb478…`. Import check: `len(_TYPED_DOMAIN_REJECTIONS) == 6`.
- ⚠ Residual (SAT host only): `ruff` on the four reference files reports 9 style errors (E501 ×6, I001, PLR0912/0915 on the heal) — the r1–r4 chain's own lines; a builder must be lint-clean, the SAT host is not graded on it. Satisfiability after the lint cleanups is NOT re-proved here (named).
- ⚠ Instrument defect found and fixed in-run: my first `build_ref_r5.py` split the SKIP records with `str.splitlines()`, which treats `\x1e` as a line break, so the skip-set check failed CLOSED (it aborted, nothing was trusted). Fixed to `split("\n")`; the four production files were restored to HEAD before the re-run.
- **F-RB-5 (the shrink VALUE, proposal).** Shrink `_txn.TXN_ROW_HARD_CAP` → **5 000** and `_txn.TXN_ROW_WARN_THRESHOLD` → **800** (monkeypatched per test through ONE `_reanchor_58_support` fixture), i.e. exactly the retired statement values. Because 58's fragments are un-annotated (rows ≡ statements), every r1–r4 fixture scale (fit ≈ 1 665, the 300-dependent warn hub, PR14's −300 ⇒ −100) is then reproduced byte-for-byte in arithmetic, so no re-measurement of fixture sizes is needed and run time stays at r4's. It also KILLS the import-time-copy wrong build (`from _txn import TXN_ROW_HARD_CAP` — the shrink does not reach it; its accessor answers ≈ 16 665 and every cap/cap±1 leg reds). Seeding (`bulk_seed_dependents` → `raw`/`ledger._query`) bypasses `compose`, so the shrink cannot refuse set-up. Alternative: smaller values (faster) at the cost of re-deriving every scale. **I would pick 5 000 / 800.**

## §STEP1-RESULT — the re-base legs on HEAD `99044d0` (BEFORE any r5 test edit), 2026-11-09
| leg | tree | log | count line | EXIT |
|---|---|---|---|---|
| BASE (`base1`) | `c58r5` = HEAD + §HELD 1/3 + r1–r4 tests (all committed at HEAD) | `…/scratchpad/sat-base1.log` | `418 failed, 7636 passed, 47 skipped, 48 warnings in 944.64s` | 1 |
| REF v1 (`ref1`) | `c58r5ref` = BASE + `build_ref_r5.py` v1 | `…/scratchpad/sat-ref1.log` | `698 failed, 7342 passed, 51 skipped, 46 warnings, 197 errors in 953.52s` | 1 |
- Both: `loremaster.__file__` inside the tree (log header), `Killed`/`MemoryMax`/`Timeout` = 0. Declared set `declare_set_r5.py` → 116 files (md5 `d77c9d31…`).
- `setdiff.py`: collected base 8101 / ref 8288; reds base 418 / ref 895; **REF-ONLY 515**.
- **REF-ONLY root cause (640 of the 895 REF reds, incl. all 197 setup errors): drift B-6** — `TypeError: SurrealStore._log_transaction_size() missing 1 required positional argument: 'row_count'`. The r1 chain's `TaskLedger._apply` calls the house size log with `(statement_count, param_count)`; 66 (R9 D2) made `row_count` required. It is 58's OWN inserted text, so every anchor applied — **a semantic drift no anchor check can see** (finding-class: anchors prove the text matched, not that the callee's signature still does). Fixed in `build_ref_r5.py` v3 (passes `_txn_module.fragment_rows(fragments)`). Added to §INVENTORY as B-6.
- **The 63c-owned expected-GREEN legs (r4 §RE-BASE step 3 + am-13's 36), measured on REF v1:**
  - `test_fixwave_a28b_63c_i_a::TestKeepsCasDecidesFromTheOneClass63cIAa28b`: **29/29 GREEN** (incl. the four `[Txn*Error-winner-landed]` legs over 58's classes).
  - `test_fixwave_a28c_63c_i_a::TestTheClassIgnoresEveryEchoedPhrase63cIAa28c`: **211/212 GREEN** — every echoed-phrase leg over 58's markers green on the typed classifier (F-RB-1 (i) holds). The ONE red is `test_am35_2_3_every_classifier_label_is_hosted_or_exempt_with_a_reason`: 63c's EXACT label set (`hosted | exempt`, hand-listed) does not contain 58's four new `_ERROR_CLASS_*` labels — exactly am-15 §4.2 / fold item 7's case (see §FLAGS F-1: the edit is outside my writable set).
  - `test_retry_seam.py`: 693/693 GREEN on both legs (a28b/a28c door pins green at HEAD — discharged by 63c-i-a's build).
  - `test_exhaustion_fates.py`: REF 28/28 GREEN; BASE 27/28 (the lease `error_class` rider leg — 58's own). The r4 `server.py::_comms_register` row red is GONE (63c-i-a discharged it).
  - `test_reanchor_58_r4_state.py`: BASE 2 red (58's unbuilt heal pair); REF v1 5 red — B-6 on the supersede/claim drivers (re-measured on REF v3, §SAT).
- **Reds attributable to 66 (on the unmodified r1–r4 contract):** the statement-cap reads (§INVENTORY A-1…A-11, all `AttributeError` on `_txn.TXN_STATEMENT_*`), the two vacuous legs A-9/A-10, and on the reference B-1…B-6. No 66-attributable red outside 58's own files and the reference chain.

## BRIEF CONFLICT (role boundary — brief-base §2, NON-OVERRIDABLE; tdd-contract role boundary)
- **Refused: the brief's Step 3 "§MUTATION (declared-RED both ways via `scripts/mutation_proof.py`)".** Building wrong implementations to see whether my own pins catch them is the contract-adversary's job; the brief quotes no operator grant with a date for this transfer. Amendment 15 §5 independently routes exactly these wrong builds (surviving statement bound, literal cap, import-time cap, `rows=` under-declaration, private warn comparison, substring classifier, refusal after the stamp, packer pricing rows at one unit) to ONE adversary delta grade. The "what wrong build it kills" column of §FORALL is analysis, not a build.
- **Two readings, written down (brief-base §2), on the reference:** my role text says "GREEN at a reference build the LEAD supplies … do not write one yourself". Reading A: re-anchoring the lead-supplied r1–r4 chain onto HEAD is maintaining the supplied reference (r3/r4 precedent; am-15 §5: "its provisional reference is a legitimate SAT host"). Reading B: any new reference code is "writing one". I took A — `build_ref_r5.py` only replays the supplied chain and re-lands its own five drifted edits + the ruled re-size. The adversary builds an independent reference (am-15 §5 item 1), so the SAT receipt does not rest on mine alone.

## §FOLD — amendment 15 §6 as amended by §8.5, item by item (base HEAD `99044d0`; amendment 15 committed at `a6dac9d`)
⚠ **History, stated once:** I first built items 1/4/5 to am-15 §1.2's GENERATED shrinks (`fixed(K)+per·4+r`); the sidecar's §8 (same day, answering my F-RB-5) SUPERSEDED those values with ONE explicitly-requested 5 000/800 fixture. I restored the eight affected files to HEAD and re-keyed them to §8 with one scripted pass (`r5_rekey.py`, §INSTRUMENTS). The generated version is kept only in scratch (`…/scratchpad/r5gen/`); nothing of it ships.

| # | item | where | status |
|---|---|---|---|
| 13 | ONE fixture, explicit, never autouse | `_reanchor_58_support.shrunk_row_caps` (`SHRUNK_ROW_HARD_CAP = 5_000`, `SHRUNK_ROW_WARN_THRESHOLD = 800`, `raising=True`, asserts the shrink is below the live value); requested per leg by `@pytest.mark.usefixtures("shrunk_row_caps")` on every async test of the 8 cap files EXCEPT the real-cap legs; `assert_unpatched_row_cap()` (vs `UNPATCHED_ROW_HARD_CAP`, captured at import) | DONE |
| 1 | hub cap at the 5 000 shrink, K set + three-point assertions unchanged, negative check per §8.2 | `test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED` (r1's legs, fixture); A-9: `not isinstance(error, TxnRowCapExceededError)` and not its `__cause__`, + positive control in the same leg (composing `TXN_ROW_HARD_CAP + 1` rows raises it); no message text for that check. r2's K-set leg same re-key (`test_reanchor_58_r2_rulings.py`), PR16 same (`test_reanchor_58_r2_scale.py`) | DONE — ⚠ deviation D-R5-3: the control composes a synthetic `cap+1`-row fragment, not "the fragments the ledger built" (the ledger refuses before building them through any public seam) |
| 2 | L1–L3 WITHOUT the fixture, unpatched asserted first; L4 = A-11 | L1 `…test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[0,2]`; L2 `…test_REAL_CAP_a_supersede_past_the_RETIRED_statement_cap_SUCCEEDS`; L3 `test_reanchor_58_r2_scale.py::test_L3_REAL_CAP_a_heal_past_the_RETIRED_statement_cap_is_ONE_transaction`; L4 `test_reanchor_58_r2_probes.py::test_PR14_the_accessor_follows_the_shared_hard_cap` (`TXN_ROW_HARD_CAP − 300` ⇒ −100, inside the fixture). Retired bound = `test_sdk3_row_bound._RETIRED_STATEMENT_CAP` via `_reanchor_58_support.RETIRED_STATEMENT_CAP` | DONE |
| 3 | un-annotated fragments | `test_reanchor_58_r5_rows.py::TestFiftyEightsFragmentsAreUnannotated` + control; `ComposeSpy.rows`/`annotated_calls()` | DONE |
| 4 | heal packer | spies price `fragment_rows` (`ComposeSpy.rows`/`heal_rows`; `measure_heal_shape`; convergence `_heal_chunks`; r2_rulings sizes; r3_probes PC); convergence's import-time `CAP` → `_cap()` read live (and r4_state's two imports of it); every heal leg at the 5 000 shrink, so r1–r4's graded scales (fit±1, 2·fit+1, the 1 700-blocker row, PR18/PR19) stand unchanged | DONE |
| 5 | size WARN at 800, control = crossing − 1 | r1's `test_crossing_the_WARN_threshold_logs_ONE_warning_and_SUCCEEDS` unchanged in form (it already used crossing−1), keyed on `row_count`; PR13 at 800 + NEW `test_PR13_CONTROL_the_house_policy_DOES_warn_at_that_size` | DONE |
| 6 | four classes typed | `test_reanchor_58_r5_rows.py::TestTheFourClassesAreTypedAndAnchored` ×4 ×2 (constructed label, the one mapping helper, `proven_no_key`, a real THROW led by the DERIVED marker raises the class, an echoed one does not); 63c's echo sweep over 58's markers 211/212 GREEN on the reference | DONE |
| 7 | 63c exact-set pins (am-15 §9.2, lead grant #20010) | four 63c files, derived member additions — §DUAL-63c | DONE |
| 8 | registry | five bare `TXN_STATEMENT_*` entries + D′ sentence removed; `test_reanchor_58_r5_rows.py` added on `loremaster.store._txn.TxnCasLostError` | DONE (§GATES) |
| 9 | the probe | `scripts/probe_hub_txn_58.py` byte-exact (grant item 5); run receipt: `3` and `1665` both `outcome=committed`, `old_edges=[0]` | DONE |
| 10 | BUILDER CONSTRAINTS | §BUILDER CONSTRAINTS | DONE |
| 11 | cold-audit set | §COLD-AUDIT SET | DONE |
| 12 | §HELD + reference | §HELD / §RE-BASE; `build_ref_r5.py` v3 | DONE |

## §FLAGS — edits outside my writable set (brief-base §2: exact edit, not made)
- **F-1 (fold item 7).** `loremaster/tests/test_fixwave_a28c_63c_i_a.py`, in `test_am35_2_3_every_classifier_label_is_hosted_or_exempt_with_a_reason`, the `hosted` set gains 58's four labels — but **only with a live host producing each** (the pin's own rule: "a new label needs a host or a reasoned exemption"). Two honest options, for the sidecar to pick (I pick (b) unless a host exists): (a) add `"_ERROR_CLASS_CLAIM_LOST"`, `"_ERROR_CLASS_CAS_LOST"`, `"_ERROR_CLASS_REANCHOR_STRAGGLER"`, `"_ERROR_CLASS_HEAL_CHUNK"` to `hosted` AND add a THROW host to `_ECHO_HOSTS` that drives each label; (b) add them to `exempt` with the reason `"a 58 guarded-shell THROW label — decided by the anchored THROW prefix (am-15 §4.1); its echo legs are 58's test_reanchor_58_r5_rows.py::TestTheFourClassesAreTypedAndAnchored"`. DUAL rows (am-15 §4.2): one per label · admitting ruling am-15 §4.1 · test id above. Note the set is HAND-LISTED where it could be derived from `vars(_txn)`'s labels minus a reasoned exemption map (am-15 §4.2 asks me to say so; converting it is not 58's work).
- **F-2 (fold item 9).** `cp …/scratchpad/probe_hub_txn_58.py scripts/probe_hub_txn_58.py` (byte-exact; md5 above).
- **F-4 (am-15 §4.2, MORE closed 63c exact-set pins than fold item 7 named — measured on REF v3's twin `ref2`, 2026-11-09).** Beyond F-1, three landed 63c pins hand-list `_txn`'s classes/labels and red ONLY on a correct 58 reference (BASE: the ids do not exist / are green):
  - `test_am37_13_3_63c_i_a.py` — 9 reds: `test_every_generated_store_class_is_adjudicated_by_the_ruling` ("store fault class(es) nobody adjudicated (am-37 §14 Q1)") + `test_a_fault_during_the_CREATE_call[{plain,needs-quoting}-Txn{ClaimLost,CasLost,ReanchorStraggler,HealChunk}Error]` ("… is not adjudicated (am-37 §14 Q1) — rule it before pinning its fate"). **Needs a RULING** (the CREATE-fault fate of each of 58's four classes under am-37 §14 Q1), then a map edit.
  - `test_mint_kind_allowlist_q1c.py` — 49 reds: `test_the_predicate_over_label_and_kind[_ERROR_CLASS_{CLAIM_LOST,CAS_LOST,REANCHOR_STRAGGLER,HEAL_CHUNK}-<kind>]` — its oracle treats an un-listed label as unrecognised (expects `proven_no_key` FALSE); am-15 §4.1 rules TRUE. Edit: add the four labels to its recognised-label set.
  - `test_mint_kind_carveout_q1b.py` — 8 reds: `test_a_kind_less_instance[<58 class>]` (hand-list `frozenset({'TxnGovernedConflictError', 'TxnUniqueViolationError'})` must gain the four) and `test_a_kind_less_rejection_during_the_CREATE[<58 class>]` (`assert 0 == 1` on an empty record list — the same adjudication gap; read with the am-37 ruling).
  - All outside my writable set; each member addition is a DUAL row (member · am-15 §4.1 · test id). Routed to sidecar-58-1 (lore_comms thread `q:58-sdk3-rebase`).
- **F-5 — a §HELD part-1 drift (58's own file, so NOT a flag: delivered as §HELD part 4).** `test_supersede_render_58.py::…test_CONTAINS_is_an_IndexScan_with_the_index_and_a_TableScan_without` reds on BOTH legs (`AttributeError: … 'TestTheKeeperIndexFires' has no attribute '_operators'`): `c9bc2c6` moved the EXPLAIN walker to `_governed_contract.{operators,scans_table,index_served}` (3.3 BitmapIndexScan). Part 4 below re-keys the held file onto it.
- **F-3 (am-15 §7, restated).** `docs/plans/v2/58-supersede-reanchor.md` L35–36 still name the deleted constants.

## §DUAL — r5's removed / changed-behaviour rows (continuing r4's numbering)
| # | what changed | adjudication |
|---|---|---|
| R5-D1 | hub refusal: `assert "statements, exceeding the hard cap" not in message` (r1) and `"exceeding the hard cap" not in …` (r2 K leg, PR16) | **old-bug** — retired wording, could no longer fail (A-9). Replaced by the TYPE check on the error and its `__cause__` + a same-leg positive control (am-15 §8.2); PR16 marked ⚠ DUAL in-file (no longer AST-equal to adversary-58 batch 2) |
| R5-D2 | the supersede/heal spies counted `len(statements)` | **changed** (am-15 §2 / §3 row 8): price with `_txn.fragment_rows`; the statement count kept only for `annotated_calls()` |
| R5-D3 | WARN legs keyed on `statement_count` above the retired 800-statement threshold | **re-keyed** (§3 row 5 / §8.1): `row_count` above `TXN_ROW_WARN_THRESHOLD` shrunk to 800 |
| R5-D4 | PR13 at 300 dependents (vacuous at the real 10 000-row warn) | **preserved at the 800 shrink** (§8.3) **+ positive control added** |
| R5-D5 | convergence's module-level `CAP` (read at import; imported by r4_state) | **dropped deliberately** (F21: an import-time copy is the forbidden build) → `_cap()` read live |
| R5-D6 | PR14 monkeypatched the deleted `TXN_STATEMENT_HARD_CAP` | **re-keyed** to `TXN_ROW_HARD_CAP` = L4 (§8.4) |
| R5-D7 | PE's weight check `"cap" or "statement"` in the message | **re-keyed** to `"cap" or "row"` (the convergence twin keeps its stronger numeric WEIGHT check) |
| R5-D8 | five bare `TXN_STATEMENT_*` `missing_symbols` (R39 D′) | **dropped deliberately** (§6 item 8), same change as the reads |

### §DUAL-63c — the §9.2 member additions (lead grant `#20010`, 2026-11-09; one row per member · ruling · test id)
All four sets grow by DERIVATION from `_txn` (`_reanchor_58_support.fifty_eight_classes()` / `fifty_eight_label_names()` / `fifty_eight_thrown_markers()`), so at a pre-58 tree they add NOTHING (63c's landed suites are byte-for-byte the same sets at HEAD) and on 58's build they add exactly the four ruled classes, their constructed labels and the one marker each maps to — never a spelling of the builder's label/marker names. ⚠ Deviation D-R5-4: §9.2 reads as literal member additions; I derived them for the reason just given (reading B — literal names — would pin my reference's internal names and red every correct build that spells them differently). Flag if the sidecar wants the literal form.
| file | set | members added (when `_txn` defines them) | ruling | test ids it turns GREEN on the reference |
|---|---|---|---|---|
| `test_am37_13_3_63c_i_a.py` | `_RULED_PROVEN_NO_KEY` | `TxnClaimLostError`, `TxnCasLostError`, `TxnReanchorStragglerError`, `TxnHealChunkError` | am-15 §9.1 (PROVEN, am-37 §15.2) | `…test_every_generated_store_class_is_adjudicated_by_the_ruling`, `…test_a_fault_during_the_CREATE_call[{plain,needs-quoting}-<each>]` |
| same | `_TYPED_PROVEN_SDK_ERROR` | one `{"kind": "Thrown", "result": "An error occurred: <marker> principal_key:k531d"}` per class (marker derived) | am-15 §9.2 | the `_typed_proven_instance` legs per class |
| `test_mint_kind_carveout_q1b.py` | `_RULED_CLASSIFIED_BY_CONSTRUCTION` | the four class names | am-15 §9.1 | `…test_a_kind_less_instance[<each>]`, `…test_a_kind_less_rejection_during_the_CREATE[<each>]` |
| same | `_RULED_CLASSIFIED_LABEL_NAMES` | the four `_ERROR_CLASS_*` names (derived from the constructed labels) | am-15 §9.1 | q1b's label legs AND `test_mint_kind_allowlist_q1c.py::…test_the_predicate_over_label_and_kind[<label>-<kind>]` ×48 + `…test_every_classifier_label_is_ruled` — **q1c needs no edit: it reads q1b's set** (§9.2 listed q1c; the set lives in q1b) |
| `test_fixwave_a28c_63c_i_a.py` | `hosted` (in `test_am35_2_3_…`) | the four label names | am-15 §9.2 F-1 (a) | `…test_am35_2_3_every_classifier_label_is_hosted_or_exempt_with_a_reason` |
| same | `_ECHO_HOSTS` | `fifty-eight-throw-<Class>`: `(None, "THROW '<marker>hx:' + $v", "<Class>")` — the governed host's shape | am-15 §9.2 F-1 (a) | the echoed-phrase × host legs for the four new hosts |
- `scripts/probe_hub_txn_58.py` placed byte-exact (md5 `14d02cf5184438659d4b1d7c17040d3b`, fold item 9, grant item 5).

## §FORALL — the ∀-vs-GUARDED table for r5's NEW / re-keyed pins
| invariant | property | ∀ / GUARDED | fixture forcing each fate | wrong build it kills (analysis — the adversary builds them, am-15 §5) |
|---|---|---|---|---|
| no statement bound survives | L1 arithmetic at 50 000; L2 one >5 000-row supersede; L3 one >5 000-row heal chunk — each asserts the unpatched cap first | GUARDED by size: a hidden bound ABOVE ~5 000 (say 10 000) is not killed. Reason: F19 forbids huge fixtures and am-15 §1.3's timeout band starts near ~12 000; named, not closed | N = (5000 − fixed)//per + 1 | literal 5 000; `min(5000-derived, row-derived)` |
| cap read live | shrunk-cap legs (the patch lands after import) + L4 (−300 ⇒ −100) | ∀ over every 58 cap consumer the legs reach | the fixture | import-time copy (accessor answers ≈16 665 under the shrink); literal cap (L4) |
| refusal is the ledger's, decided before compose | not `TxnRowCapExceededError`, nor its `__cause__`; control shows compose does raise it at that size | ∀ K in r2's set | cap+1 seeded per K | catch-and-rewrap of compose's refusal (`raise … from`) |
| WARN is the house row warn | crossing ⇒ exactly 1 on `row_count`; crossing−1 ⇒ 0; PR13 stubbed ⇒ 0, its control ⇒ 1 | ∀ over the boundary pair | the 800 shrink | private comparison (800 / 10 000 / import-time copy); statement-keyed warn |
| fragments un-annotated | ∀ transactions the supersede + heal send: rows == statements | ∀ over observed compose calls (non-vacuity asserted) | K=2 supersede + one heal boot | `rows=` under-declaration |
| four classes typed + anchored | ∀ 4 ruled classes: label, one helper, `proven_no_key`, led THROW ⇒ class, echoed ⇒ unspecified | ∀ over the RULED set (a 5th class is a new ruling) | marker DERIVED per class | substring classifier; `if label ==` at a raise site; class on the unspecified label |
| heal chunks ≤ cap by weight | r3 convergence ∀ shapes × SCALES at the 5 000 shrink | ∀ (generated shapes) | the fixture | packer pricing at one unit; cap read at import |
- **Reach check ("does the hostile fixture REACH the guard?"):** set-up is `raw` (bypasses `compose`) or single-task `create`s far below 5 000 rows, so the shrink cannot refuse set-up; the fixture asserts the shrink is below the live value (a no-op patch reds); the L-legs assert they did NOT inherit it.

## §HELD — re-derived at HEAD `99044d0` (2026-11-09); unchanged by r5
- **Part 1** = `5a43aeb:REPORT-contract-58.md` lines 173–557, md5 `dbba9753cbe960cda178f42687039c2d` ✔. **Part 3** = `c42eeaf:REPORT-contract-58-r2.md` lines 177–195, md5 `15f38e319cb8d3c25456084dda4989b1` ✔. Part 2 stays DELETED (r4).
- `git apply --check` EXIT=0 both at `99044d0`; applied in both SAT trees. r5 edits no file either part touches. §INVENTORY C: neither part rests on statement counts.
- **Part 4 (NEW in r5, F-5) — applies AFTER part 1** (it edits the file part 1 creates). `c9bc2c6` (SDK3-era, 2026-11-07) moved the EXPLAIN walker that part 1's `test_supersede_render_58.py` borrowed (`test_keeps_schema.TestTheKeeperIndexFires._operators/_scans_table`) into `_governed_contract` and retired the literal `"IndexScan"` check (3.3 BitmapIndexScan). Part 1 still `git apply`s clean — a semantic drift again (B-6's class), red on BOTH legs. Part 4 re-keys the held file onto `_governed_contract.{index_served, scans_table, operators}`. md5 `f4048e2d1850a670b4145d6df373f228`; ruff clean on the result. Its receipt is a targeted run of that file on both trees (§SAT).
```diff
--- a/loremaster/tests/test_supersede_render_58.py
+++ b/loremaster/tests/test_supersede_render_58.py
@@ -19,7 +19,7 @@
 from pathlib import Path
 from typing import Any
 
-import test_keeps_schema as keeps_schema  # module-qualified: its Test* classes must not be re-collected here
+from _governed_contract import index_served, operators, scans_table
 from _reanchor_58_support import (
     CLAIMANT,
     CREATOR,
@@ -37,7 +37,8 @@
 __all__ = ["ledger58"]
 
 SERVER_SOURCE = Path(importlib.import_module("loremaster.server").__file__ or "")
-_PLAN = keeps_schema.TestTheKeeperIndexFires  # the ONE plan walker (``_operators`` / ``_scans_table``)
+# contract r5 §HELD part 4: the ONE shared EXPLAIN walker moved to ``_governed_contract`` (c9bc2c6 —
+# 3.3 serves index reads as BitmapIndexScan, so the literal 'IndexScan' check retired with the old walker).
 
 
 def _render(*args: Any) -> str:
@@ -118,8 +119,8 @@
         await create(ledger, "a dependent", [blocker])
         statement = f"SELECT id FROM {TASK_TABLE} WHERE blocked_by CONTAINS $x EXPLAIN"
         plan = await raw(ledger, statement, {"x": blocker})
-        assert "IndexScan" in _PLAN._operators(plan) and not _PLAN._scans_table(plan, TASK_TABLE), (
-            f"`blocked_by CONTAINS $x` is not index-served: {_PLAN._operators(plan)}"
+        assert index_served(plan) and not scans_table(plan, TASK_TABLE), (
+            f"`blocked_by CONTAINS $x` is not index-served: {operators(plan)}"
         )
         # CONTROL — the SAME statement with the index removed IS a TableScan (the walker can see one).
         index_rows = await raw(ledger, f"INFO FOR TABLE {TASK_TABLE}")
@@ -127,6 +128,6 @@
         assert len(names) == 1, f"expected exactly one blocked_by index: {names}"
         await raw(ledger, f"REMOVE INDEX {names[0]} ON TABLE {TASK_TABLE}")
         control = await raw(ledger, statement, {"x": blocker})
-        assert _PLAN._scans_table(control, TASK_TABLE), (
-            f"CONTROL failed: without the index the walker saw no TableScan: {_PLAN._operators(control)}"
+        assert scans_table(control, TASK_TABLE), (
+            f"CONTROL failed: without the index the walker saw no TableScan: {operators(control)}"
         )
```

## §RE-BASE — the builder's FIRST step (replaces r4 §RE-BASE; r4's 63c-owned expectations are DISCHARGED — §STEP1-RESULT)
1. `git fetch`; confirm `34d0b6b` (63c-i-a), `88b06be` (SDK3/66 audit GO) and the r5 commit are ancestors of HEAD.
2. `git apply --check` §HELD parts 1 and 3, then part 4 on top of part 1 (addresses + md5s above).
3. Build to `build_ref_r5.py` v3's SHAPE (a SAT host, not a spec — the RULINGS are am-15 §1–§4): the four classes in the typed anchored-prefix idiom with `_constructed_error_class`; `_domain_rejection_error` the one mapping; the hub accessor / heal packer / refusal priced by `_txn.fragment_rows` against `_txn.TXN_ROW_HARD_CAP` read live; `TaskLedger._apply`'s size log passes `row_count` (drift B-6).
4. Re-run the declared targeted set (`declare_set_r5.py` on the new tree). Expected: 0 reds in 58-owned files except the bounds still owned elsewhere (64b-i's `_run_guarded`, 63c's exact label pin until §FLAGS F-1 lands).
5. If HEAD has moved `_txn`'s classifier, `fragment_rows`, `_log_transaction_size` or `TXN_ROW_*` again, re-derive from HEAD — and re-run `anchor_audit.py` (anchors) AND a REF leg (semantic drift like B-6 is invisible to anchors).

## §BUILDER CONSTRAINTS (r1–r4's stand unless re-keyed by am-15 §3; r5 adds)
- **BC-r5-0:** the first step is §RE-BASE above.
- **BC-r5-1 (am-15 §6 10a):** accessor, packer and refusal price with `_txn.fragment_rows` and read `_txn.TXN_ROW_HARD_CAP` LIVE — no private counter, no copied constant, no surviving statement bound. Sharing is proven at the cold audit by MUTATION of `fragment_rows` (am-15 §2 bound).
- **BC-r5-2 (10b):** `TaskLedger._apply` logs its size through the ONE house function `SurrealStore._log_transaction_size(statement_count, param_count, row_count)`; no second threshold comparison. Cold-audit mutation of that comparison must red `test_crossing_the_WARN_threshold…` AND `test_sdk3_row_bound`'s warn pin.
- **BC-r5-3 (10c):** `max_reanchor_dependents`'s docstring states am-15 §1.3's bound (≈12 000–16 665 dependents time out before refusal), its trigger (`store.apply.large_transaction` from the task ledger), and the probe path `scripts/probe_hub_txn_58.py`.
- **BC-r5-4 (10d):** the refusal names N, the rows it would compose, the row cap and the cap in dependents, each as a plain integer, and promises nothing about smaller supersedes.
- **BC-r5-5:** the four classes override `_constructed_error_class`; the classifier anchors each marker at `_ENGINE_THROW_PREFIX` under `kind THROWN` (or untyped); markers live once in `_txn`.
- **BC-r5-6 (10e, still owed at `99044d0` per am-15 §4.3):** am-13 §1 F-8 (`label=`/`url=` on the conflict driver); the lease `error_class` rider (BC-r4-2); `more-itertools` declared (BC-r4-1).
- **BC-r4-3…5 stand** (the §1 instrument binds every exhaustion door at every write; nothing escalates to a builder; admissions).

## §COLD-AUDIT SET (am-15 §6 item 11 — for the audit brief)
1. The adversary's re-anchored W-* builds (am-15 §5 item 3) — from the delta grade, not from me.
2. Mutation of `_txn.fragment_rows` (double the un-annotated count): the accessor, the packer's chunk boundary and compose's refusal must ALL move (BC-r5-1).
3. Mutation of the house warn comparison (BC-r5-2).
4. Read `max_reanchor_dependents`'s docstring (BC-r5-3).
5. The real-population heal receipt (am-2) plus the largest hub in that dump (`max` of `blocks` edges per `in`) beside it.

## §SWEEP-R5 — fold item 8's retired-name sweep (grep: rename exhaustiveness, the sanctioned case), FINAL tree, 2026-11-09
- Bare `STATEMENT_HARD_CAP|STATEMENT_WARN` over the 20 58-owned test/support files: **`files_opened=20 hits=0`**.
- Widened to the alias class (`\bCAP\b|statement[ _-]?cap|statement_count`), each residual with its own verdict:
  - `_reanchor_58_support.py` `RETIRED_STATEMENT_CAP` comment — **keep** (the one re-export).
  - `test_exhaustion_fates.py` L583 docstring ("the old statement-cap overflow's successor", servicer `da24469`) — **history, keep**.
  - `test_reanchor_58_r2_scale.py` L3 comment ×2 + test name — **keep** (names the retired bound the leg kills).
  - `test_supersede_reanchor_58.py` L2 test name, docstring ×2, task subject; the A-9 comment — **keep** (same).
  - `test_reanchor_58_r3_convergence.py` header comment ("the ROW bound replaced the statement cap") — **keep**.
  - Two residuals of MINE found by this sweep and FIXED in the same pass: the WARN leg's `getattr(warnings[0], "statement_count")` and its message (the scripted rename covered only `hasattr`).
- ⚠ **Sweep defect, mine (Step 2):** the inventory pattern keyed on the constants' NAMES, so `test_reanchor_58_r4_state.py`'s `from test_reanchor_58_r3_convergence import CAP` (an alias of the deleted value) was missing from §INVENTORY; it surfaced as typecheck orphans. Fixed (`_cap()`). Class: *a name-keyed rename sweep misses every alias that re-exports the value.*

## §DRY LEDGER (brief-base §6 — test-support symbols only; FINAL state after the §8 re-key)
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `_reanchor_58_support.shrunk_row_caps` (+ `SHRUNK_ROW_HARD_CAP`, `SHRUNK_ROW_WARN_THRESHOLD`) | `test_sdk3_row_bound.py` (read: its own shrink is an inline `monkeypatch.setattr(_txn, "TXN_ROW_HARD_CAP", …)` on a file-local constant); `conftest.py` | no shared fixture | **HAND-ROLLED** — the ONE fixture am-15 §8.1 rules, in 58's support module |
| `UNPATCHED_ROW_HARD_CAP` / `assert_unpatched_row_cap` | same | none | **HAND-ROLLED** (am-15 §8.1 rider: L-legs prove they did not inherit the shrink) |
| `RETIRED_STATEMENT_CAP` | `test_sdk3_row_bound._RETIRED_STATEMENT_CAP` | SDK3's ONE named constant | **REUSED** (re-exported, never a second literal) |
| `composed_rows` | `_txn.fragment_rows` | the one counter | **REUSED** (a thin call so no spy re-counts) |
| `ComposeSpy.rows` / `heal_rows` / `annotated_calls` | `ComposeSpy` (read in full) | `calls`, `heal_calls` | **EXTENDED** `ComposeSpy` |
| `test_reanchor_58_r3_convergence._cap` | convergence's module `CAP` | an import-time copy | **REPLACED** (F21) — r4_state imports it |
| `test_reanchor_58_r5_rows._ruled_class` / `_marker_for` / `_throw_through_the_ledger` | `test_sdk3_txn_classification.py` (`_query`/`_transact` over a lease owner), `test_fixwave_a28c_63c_i_a._driver_marker_phrases` (vars(_txn) marker derivation) | a lease-owner door; a marker-phrase dict keyed for echo hosts | **HAND-ROLLED**: the door here is the LEDGER's own `_apply` (58's path), and `_marker_for` inverts the classifier (marker → label) rather than enumerating phrases; sharing `_driver_marker_phrases` would import a 63c test module for one comprehension |
- Retired during r5 (built for the superseded generated-shrink pass, never shipped): `shrink_row_cap`, `shrink_row_warn`, `HUB_SHRUNK_DEPENDENTS`, `HEAL_SHRUNK_FIT`, `names_number`, `error_chain`, `measure_supersede_shape`.

## Packages considered
- `more_itertools.constrained_batches` — **keep** (am-8's verdict; am-15 §2 changes only `max_size`/`get_len`; I specified no new mechanism).
- `loremaster.store._txn.fragment_rows` — **reuse** (read at `99044d0`: `sum(len(f.statements) if f.rows is None else f.rows …)`).
- No new mechanism specified: the shrink is `pytest.MonkeyPatch.setattr` (installed pytest; read `raising=True` semantics).

## §INSTRUMENTS — pasted VERBATIM (brief-base §1; the scratch root is session-local)
Reference chain inputs (unchanged, re-extracted by heading and md5-verified at `99044d0`): `build_ref58.py` (`9f2f580:REPORT-adversary-58.md`, `5915c12e…`) → `my_ref.py` + `my_ref_am6.py` (`821be62:REPORT-adversary-58-r2.md`, `de2d2801…` / `2176fb8e…`) → `my_ref_r3.py` (`7130508:REPORT-contract-58-r3.md`, `c5678ba7…`) → `my_ref_r4.py` (`4d864c9:REPORT-contract-58-r4.md`, `ec33542d…`). r4's `setdiff.py` (`8910cbe4…`) is reused unchanged (pasted in r4). `probe_hub_txn_58.py` is am-15's §INSTRUMENT (md5 `14d02cf5…`), not re-pasted.
Reference result md5s: v3 `_txn.py 053081d8…` (ref3/ref3d) · v4 `_txn.py 8d37d2f4…` (delta2); `tasks.py 3360a9cf…` both (findings.py / lease.py as the r4 chain leaves them).

### `build_ref_r5.py` (md5 `c2c9a2739d1b0746b25485c0ea6b122b`, v4) — the re-based reference builder — a SAT host, NOT A SPEC; usage: build_ref_r5.py <chain-dir> <tree-root>
v1 `4e49adf7…` (§PROVISIONAL-REF) → v2 `7d88d76c…` (+`_constructed_error_class`) → v3 `7b37f766…` (+B-6 `row_count`) → v4 (+`TxnUniqueViolationError` tier). v4 result md5s: `tasks.py 3360a9cf3b7cc45960c051ecb5ff1134` · `_txn.py 8d37d2f4432276637bf9187bbcd21a6e`.
```python
#!/usr/bin/env python3
"""build_ref_r5.py <chain-dir> <tree-root> — contract-58-r5's PROVISIONAL reference on HEAD 99044d0 (a SAT host,
NOT A SPEC; F-RB-1/2/3 = reading (i), as amendment 15 rules; v2 adds its §4.1 `_constructed_error_class`; v3 passes `row_count` to the house size log — drift B-6; v4 gives 63c's now-built TxnUniqueViolationError its am-7 §0 row-3 WARNING tier).

1. Replays the r1–r4 chain (build_ref58 → my_ref → my_ref_am6 → my_ref_r3 → my_ref_r4) IN PLACE with each script's
   exact-once anchor assert turned into record-and-skip, and ASSERTS the skipped set is EXACTLY the five declared
   drifts A1–A5 (§RE-BASE-STEP1) — any other miss aborts (#194: a drift nobody declared is a STOP).
2. Applies the r5 delta, every anchor asserted exactly once:
   - F-RB-1 (i): 58's four THROW markers classified in HEAD's typed idiom
     (`(untyped or kind == ErrorKind.THROWN) and lowered.startswith(_ENGINE_THROW_PREFIX + marker)`);
     the label→class map `_TYPED_DOMAIN_REJECTIONS` (incl. HEAD's governed/unique) feeds `_domain_rejection_error`
     with HEAD's `error_class=` / `kind=` kwargs; `_ROLLBACK_LOG_TIERS` keyed by class (r3's am-7 §4 table);
     the non-conflict raise logs with `type(rejection)` then raises it (r3's edit re-anchored past `kind=`);
     my_ref's duplicate `_THROW_RESULT_PREFIX` (unused after r3) is deleted — HEAD's `_ENGINE_THROW_PREFIX` is the one.
   - F-RB-2 (i): `TaskLedger._composed_statement_count` is DELETED; every consumer calls `_txn.fragment_rows`.
   - F12/F21: the hub cap and the heal packer read `_txn_module.TXN_ROW_HARD_CAP` live."""
import re
import subprocess
import sys
from pathlib import Path

chain, root = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
DECLARED = {
    ("my_ref", "    if _GOVERNED_CONFLICT_MARKER in lowered:\n        return _ERROR_CLASS_GOVERNED_CONFLICT\n"),
    ("my_ref", "    if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:\n        return TxnGovernedConflictError(message)\n"),
    ("my_ref_r3", "    if CLAIM_LOST_MARKER in lowered:\n        return _ERROR_CLASS_CLAIM_LOST\n"),
    ("my_ref_r3", "    if error_class == _ERROR_CLASS_CLAIM_LOST:\n        return TxnClaimLostError(message)\n    return TxnDomainR"),
    ("my_ref_r3", '                f"({error_class}); {_SERVER_LOG_HINT}",\n            )\n        last_conflict'),
}
ASSERT = re.compile(r'^(\s*)assert count == 1, f"anchor (?:found|occurs) \{count\}x: \{old\[:80\]!r\}"$', re.M)
missed = set()
for name in ["build_ref58", "my_ref", "my_ref_am6", "my_ref_r3", "my_ref_r4"]:
    text = (chain / f"{name}.py").read_text()
    if name != "my_ref_r4":
        text, n = ASSERT.subn(lambda m: (f'{m.group(1)}if count != 1:\n{m.group(1)}    print("SKIP\\x1f" + {name!r} + "\\x1f" + old[:110].replace("\\n", "\\x1e"))\n'
                                         f'{m.group(1)}    return ' + ("None" if name == "build_ref58" else "src")), text)
        assert n == 1, (name, n)
    out = subprocess.run([sys.executable, "-c", text, str(root)], capture_output=True, text=True)
    # the scripts read sys.argv[1]; -c shifts argv so argv[1] is root
    assert out.returncode == 0, (name, out.stderr[-2000:])
    for line in out.stdout.split("\n"):
        if line.startswith("SKIP\x1f"):
            _, script, head = line.split("\x1f")
            missed.add((script, head.replace("\x1e", "\n")))
assert missed == DECLARED, ("undeclared drift", missed ^ DECLARED)
print(f"chain replayed; skipped exactly the {len(DECLARED)} declared anchors")

TXN = root / "loremaster/loremaster/store/_txn.py"
TASKS = root / "loremaster/loremaster/tasks.py"


def sub(src: str, old: str, new: str) -> str:
    count = src.count(old)
    assert count == 1, f"anchor occurs {count}x: {old[:100]!r}"
    return src.replace(old, new)


txn = TXN.read_text()
# F-RB-1 (i) — classify 58's markers in HEAD's typed THROW idiom (after the governed-conflict branch).
txn = sub(txn, """        _ENGINE_THROW_PREFIX + _GOVERNED_CONFLICT_MARKER
    ):
        return _ERROR_CLASS_GOVERNED_CONFLICT
""", """        _ENGINE_THROW_PREFIX + _GOVERNED_CONFLICT_MARKER
    ):
        return _ERROR_CLASS_GOVERNED_CONFLICT
    if untyped or kind == ErrorKind.THROWN:
        for marker, label in _THROWN_DOMAIN_MARKERS:
            if lowered.startswith(_ENGINE_THROW_PREFIX + marker):
                return label
""")
txn = sub(txn, '_ENGINE_THROW_PREFIX = "an error occurred: "\n', '''_ENGINE_THROW_PREFIX = "an error occurred: "
#: packet 58: each guarded shell's THROW marker → its classifier label, matched ONLY as the THROW's prefix
#: (63c-i-a's typed decision — never a substring of echoed text).
_THROWN_DOMAIN_MARKERS: tuple[tuple[str, str], ...] = (
    (CLAIM_LOST_MARKER, _ERROR_CLASS_CLAIM_LOST),
    (_CAS_LOST_MARKER, _ERROR_CLASS_CAS_LOST),
    (_REANCHOR_STRAGGLER_MARKER, _ERROR_CLASS_REANCHOR_STRAGGLER),
    (_HEAL_CHUNK_MARKER, _ERROR_CLASS_HEAL_CHUNK),
)
''')
txn = sub(txn, """    if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:
        return TxnGovernedConflictError(message, error_class=error_class, kind=kind)
    if error_class == _ERROR_CLASS_UNIQUE_VIOLATION:
        return TxnUniqueViolationError(message, error_class=error_class, kind=kind)
    return TxnDomainRejectionError(message, error_class=error_class, kind=kind)
""", """    typed = _TYPED_DOMAIN_REJECTIONS.get(error_class, TxnDomainRejectionError)
    return typed(message, error_class=error_class, kind=kind)


#: am-7 §4: the classifier's label → the typed class it raises (ONE mapping; HEAD's two + packet 58's four).
_TYPED_DOMAIN_REJECTIONS: dict[str, type[TxnDomainRejectionError]] = {
    _ERROR_CLASS_GOVERNED_CONFLICT: TxnGovernedConflictError,
    _ERROR_CLASS_UNIQUE_VIOLATION: TxnUniqueViolationError,
    _ERROR_CLASS_CLAIM_LOST: TxnClaimLostError,
    _ERROR_CLASS_CAS_LOST: TxnCasLostError,
    _ERROR_CLASS_REANCHOR_STRAGGLER: TxnReanchorStragglerError,
    _ERROR_CLASS_HEAL_CHUNK: TxnHealChunkError,
}
#: am-7 §4: the rollback log tier, keyed by the CLASSIFIED CLASS; anything else ERROR (deny-by-default).
_ROLLBACK_LOG_TIERS: dict[type[BaseException], int] = {
    TxnClaimLostError: logging.DEBUG,
    TxnGovernedConflictError: logging.WARNING,
    TxnUniqueViolationError: logging.WARNING,
    TxnCasLostError: logging.WARNING,
    TxnReanchorStragglerError: logging.WARNING,
    TxnHealChunkError: logging.WARNING,
}
""")
txn = sub(txn, """                kind=_typed_kind(typed_root),
            )
        last_conflict""", """                kind=_typed_kind(typed_root),
            )
            _log_rollback(root_cause, statement_count, failed_statements, type(rejection))
            raise rejection
        last_conflict""")
# am-15 §4.1: each of 58's classes names its own label by construction (am-37 §15.2), like HEAD's two.
for cls, label in (("TxnClaimLostError", "_ERROR_CLASS_CLAIM_LOST"), ("TxnCasLostError", "_ERROR_CLASS_CAS_LOST"),
                   ("TxnReanchorStragglerError", "_ERROR_CLASS_REANCHOR_STRAGGLER"),
                   ("TxnHealChunkError", "_ERROR_CLASS_HEAL_CHUNK")):
    pattern = re.compile(rf'(class {cls}\(TxnDomainRejectionError\):\n    """.*?"""\n)', re.S)
    assert len(pattern.findall(txn)) == 1, cls
    txn = pattern.sub(lambda m, label=label: m.group(1) + (
        "\n    @classmethod\n    def _constructed_error_class(cls) -> str:\n"
        '        """Classified by construction (am-37 §15.2): its own class IS the recognition."""\n'
        f"        return {label}\n"), txn, count=1)
txn = re.sub(r"# The engine's rendering of an application THROW[^\n]*\n_THROW_RESULT_PREFIX = \"an error occurred:\"\n", "", txn, count=1)
assert "_THROW_RESULT_PREFIX" not in txn, "duplicate THROW prefix still referenced"
TXN.write_text(txn)

src = TASKS.read_text()
# F-RB-2 (i) — ONE counter, owned by _txn.
src = sub(src, '''    @staticmethod
    def _composed_statement_count(fragments: Sequence[TxnFragment]) -> int:
        """The body-statement count ``compose`` checks against ``TXN_STATEMENT_HARD_CAP`` — the ONE counter."""
        return sum(len(fragment.statements) for fragment in fragments)

''', "")
src = sub(src, "            return TaskLedger._composed_statement_count(fragments)\n",
          "            return _txn_module.fragment_rows(fragments)\n")
src = sub(src, "            cost = self._composed_statement_count([*fragments, self._relate_fragment(relates)])\n",
          "            cost = _txn_module.fragment_rows([*fragments, self._relate_fragment(relates)])\n")
assert "_composed_statement_count" not in src, "a consumer of the deleted private counter remains"
# B-6 (am-15 §3 row 5 / R9 D2): the ONE house size function gained a required ``row_count`` (66) — a SEMANTIC drift
# no anchor check sees (the call is 58's own inserted text). Price it with the one counter.
src = sub(src, """        SurrealStore._log_transaction_size(
            sum(len(fragment.statements) for fragment in fragments), len(merged_params)
        )""", """        SurrealStore._log_transaction_size(
            sum(len(fragment.statements) for fragment in fragments),
            len(merged_params),
            _txn_module.fragment_rows(fragments),
        )""")
# F12 / F21 — the row cap, read live.
assert src.count("_txn_module.TXN_STATEMENT_HARD_CAP") == 2, src.count("_txn_module.TXN_STATEMENT_HARD_CAP")
src = src.replace("_txn_module.TXN_STATEMENT_HARD_CAP", "_txn_module.TXN_ROW_HARD_CAP")
assert "TXN_STATEMENT" not in src
TASKS.write_text(src)
print("contract-58-r5 provisional reference applied:", TXN, TASKS)
```

### `anchor_audit.py` (md5 `8f0f0bbca33577fb9047cfb25f1fe80a`) — replays the chain with record-and-skip anchors (§RE-BASE-STEP1's A1–A5)
```python
#!/usr/bin/env python3
"""anchor_audit.py <chain-dir> <head-tree> <audit-root> — contract-58-r5's re-base instrument.

Replays the packet-58 reference chain (build_ref58 → my_ref → my_ref_am6 → my_ref_r3 → my_ref_r4) against a COPY
of the four production files taken from <head-tree> at HEAD (git show), with each script's exact-once anchor
assert rewritten to RECORD (count, script, anchor head) and skip that edit instead of aborting.  Every miss is
printed as `ANCHOR <script> <count>x <repr>`; a skipped edit can cascade into later misses, so the list is the
ceiling of re-anchoring work, not a count of independent drifts.  Never touches <head-tree>."""
import re, shutil, subprocess, sys
from pathlib import Path

chain, head, root = (Path(a).resolve() for a in sys.argv[1:4])
FILES = ["loremaster/loremaster/tasks.py", "loremaster/loremaster/store/_txn.py",
         "loremaster/loremaster/findings.py", "loremaster/loremaster/store/lease.py"]
if root.exists():
    shutil.rmtree(root)
for rel in FILES:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(subprocess.run(["git", "-C", str(head), "show", f"HEAD:{rel}"], check=True,
                                           capture_output=True, text=True).stdout)
ASSERT = re.compile(r'^(\s*)assert count == 1, f"anchor (?:found|occurs) \{count\}x: \{old\[:80\]!r\}"$', re.M)
total = 0
for name in ["build_ref58", "my_ref", "my_ref_am6", "my_ref_r3", "my_ref_r4"]:
    text = (chain / f"{name}.py").read_text()
    text, n = ASSERT.subn(lambda m: (f'{m.group(1)}if count != 1:\n{m.group(1)}    print(f"ANCHOR {name} {{count}}x '
                                     f'{{old[:110]!r}}")\n{m.group(1)}    return '
                                     + ("None" if name == "build_ref58" else "src")), text)
    if name == "my_ref_r4":
        text = text.replace("assert text.count(anchor) == 4, text.count(anchor)",
                            'print(f"ANCHOR my_ref_r4 {text.count(anchor)}x(of 4) {anchor!r}") if text.count(anchor) != 4 else None')
    elif n != 1:
        print(f"INSTRUMENT {name}: expected 1 assert rewrite, got {n}"); sys.exit(2)
    script = root / f"_{name}_audit.py"
    script.write_text(text)
    out = subprocess.run([sys.executable, str(script), str(root)], capture_output=True, text=True)
    misses = [l for l in out.stdout.splitlines() if l.startswith("ANCHOR")]
    total += len(misses)
    print(f"== {name}: exit={out.returncode} misses={len(misses)}")
    for line in misses:
        print("  ", line)
    if out.returncode:
        print("   STDERR-TAIL:", out.stderr.strip().splitlines()[-3:])
print(f"TOTAL-MISSES {total}")
```

### `extract_fence.py` (md5 `a09c58e75fabb305e99e624eedf770b2`) — heading-addressed fence extractor (chain + instruments re-extracted by it)
```python
#!/usr/bin/env python3
"""extract_fence.py <rev:path> <heading-substring> <out> — write the FIRST fenced block after the first heading
line containing <heading-substring> (contract-58-r5's reference-chain extractor; heading-addressed, not line)."""
import subprocess, sys
spec, needle, out = sys.argv[1:4]
lines = subprocess.run(["git", "show", spec], check=True, capture_output=True, text=True).stdout.splitlines(keepends=True)
start = next(i for i, l in enumerate(lines) if l.startswith("#") and needle in l)
i = start + 1
while not lines[i].startswith("```"):
    i += 1
j = i + 1
while not lines[j].startswith("```"):
    j += 1
open(out, "w").write("".join(lines[i + 1:j]))
print(out, "heading@", start + 1, "lines", j - i - 1)
```

### `declare_set_r5.py` (md5 `c852349a66c7a30bbb016bb43ca08aef`) — the declared targeted set (r4's declare_set.py with MINE derived)
```python
#!/usr/bin/env python3
"""contract-58-r5's DECLARED targeted set (r4's declare_set.py, md5 c6d0e1bc…, with ONE change): MINE is DERIVED —
every `loremaster/tests/test_*.py` whose name contains `58` plus test_exhaustion_fates.py — instead of r4's
8-file hand-list (r4's list omitted 11 of packet 58's own files at HEAD 99044d0).  Covering = AST import scan of
every test module for the six production modules the 58 reference edits (lore_impact caps at 15, #518/#563 —
fallback said out loud).  Structural = r4's four.  Run from the tree root; one repo-relative path per line."""
import ast
from pathlib import Path

TARGETS = {"loremaster.store._txn", "loremaster.tasks", "loremaster.findings", "loremaster.briefs",
           "loremaster.keeps", "loremaster.store.lease"}
MINE = {p.as_posix() for p in Path("loremaster/tests").glob("test_*58*.py")} | {"loremaster/tests/test_exhaustion_fates.py"}
STRUCTURAL = """loremaster/tests/test_retry_seam.py loremaster/tests/test_mcp_server.py
loremaster/tests/test_reanchor_58_r3_relate.py scripts/test_forgery_door_sweep.py""".split()


def imports_target(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name in TARGETS for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module in TARGETS:
                return True
            if any(f"{node.module}.{alias.name}" in TARGETS for alias in node.names):
                return True
    return False


covering = [p.as_posix() for p in sorted([*Path("loremaster/tests").glob("test_*.py"), *Path("scripts").glob("test_*.py")])
            if imports_target(ast.parse(p.read_text()))]
missing = [p for p in STRUCTURAL if not Path(p).exists()]
assert not missing, f"structural pin file(s) absent: {missing}"
print("\n".join(sorted(MINE | set(covering) | set(STRUCTURAL))))
```

### `sat_run_r5.sh` (md5 `827677d5f72cb5e666dd9667c20f36fc`) — the SAT/RED leg runner (cgroup 16G, -n 8, --timeout=300, junit, tree_id header)
```bash
#!/usr/bin/env bash
# sat_run_r5.sh <tree-dir> <tag> — contract-58-r5's targeted SAT run (r4's sat_run.sh without the in-place file
# swap: BASE and REF are separate scratch_copy trees).  Header = tree_id.sh + loremaster.__file__ + md5 of the four
# reference-edited production files.  Cgroup-capped 16G, -n 8, per-test timeout 300, junit.  Exit line last.
set -uo pipefail
SP=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad
T=$1; TAG=$2; LOG=$SP/sat-$TAG.log; XML=$SP/sat-$TAG.xml
cd "$T"
{ ~/.claude/orchestration/tree_id.sh "$T"; echo "tag=$TAG $(date -u +%FT%TZ) MemAvailable=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)GiB";
  uv run python -c 'import loremaster; print("loremaster.__file__ =", loremaster.__file__)';
  md5sum loremaster/loremaster/tasks.py loremaster/loremaster/store/_txn.py loremaster/loremaster/findings.py loremaster/loremaster/store/lease.py; } > "$LOG" 2>&1
mapfile -t SET < "$SP/declared_set.txt"
systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
  uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider --junitxml="$XML" "${SET[@]}" >> "$LOG" 2>&1
echo "EXIT=$?" >> "$LOG"
```

### `red_diff.py` (md5 `462a632f79cfea0ef708f098a42c93a2`) — declared-vs-observed RED@HEAD diff, both ways
```python
#!/usr/bin/env python3
"""red_diff.py <declared.txt> <junit.xml> — contract-58-r5: compare a DECLARED (written before the run, from
--collect-only) `RED|GREEN <nodeid>` list with a junit result, both ways; print mismatches + counts."""
import sys
import xml.etree.ElementTree as ET
declared = {}
for line in open(sys.argv[1]):
    color, node = line.split(" ", 1)
    declared[node.strip()] = color
seen = {}
for case in ET.parse(sys.argv[2]).getroot().iter("testcase"):
    cls = case.get("classname").split(".")
    # loremaster.tests.<module>[.<Class>]
    mod_idx = next(i for i, p in enumerate(cls) if p.startswith("test_"))
    node = "/".join(cls[: mod_idx + 1]) + ".py" + "".join(f"::{p}" for p in cls[mod_idx + 1:]) + f"::{case.get('name')}"
    bad = case.find("failure") is not None or case.find("error") is not None
    seen[node] = "RED" if bad else ("SKIP" if case.find("skipped") is not None else "GREEN")
ok = miss = absent = 0
for node, color in declared.items():
    got = seen.get(node)
    if got is None:
        absent += 1; print("ABSENT", node)
    elif got != color:
        miss += 1; print(f"MISMATCH declared={color} got={got} {node}")
    else:
        ok += 1
print(f"declared={len(declared)} matched={ok} mismatched={miss} absent={absent}")
```

### `delta_run_r5.sh` (md5 `af87ab79e6f697c8b6afbc99eac63fc4`) — the delta-leg runner (files changed after a full leg started)
```bash
#!/usr/bin/env bash
# delta_run_r5.sh <tree-dir> <tag> — contract-58-r5's delta leg: the files changed AFTER base3/ref3 started
# (delta_files.txt). Same caps/header as sat_run_r5.sh.
set -uo pipefail
SP=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad
T=$1; TAG=$2; LOG=$SP/sat-$TAG.log; XML=$SP/sat-$TAG.xml
cd "$T"
{ ~/.claude/orchestration/tree_id.sh "$T"; echo "tag=$TAG $(date -u +%FT%TZ)";
  uv run python -c 'import loremaster; print("loremaster.__file__ =", loremaster.__file__)';
  md5sum loremaster/loremaster/tasks.py loremaster/loremaster/store/_txn.py; } > "$LOG" 2>&1
mapfile -t SET < "$SP/delta_files.txt"
systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
  uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider --junitxml="$XML" "${SET[@]}" >> "$LOG" 2>&1
echo "EXIT=$?" >> "$LOG"
```

### `r5_rekey.py` (md5 `b4410d655dcb7e8732ff570d8418582c`) — the am-15 §8 re-key, run once from `loremaster/tests` on the HEAD versions of the 8 files
Applied after it (by hand, recorded here so the tree is reproducible): the fixture marker's trailing comment was dropped by `sed` (line length); `ruff check --fix` sorted the inserted imports; four E501 rewraps (r2_scale ×2, supersede ×3) and the PR13 CONTROL leg were added by exact-once Python edits; the WARN leg's `getattr(…, "statement_count")` + message were re-keyed after §SWEEP-R5 caught them.
```python
"""contract-58-r5 — amendment 15 §8 re-key of packet 58's cap/warn pins onto the SDK3 row bound (tests only).
Run from loremaster/tests on the HEAD versions.  Every anchor asserted (#194)."""
import ast
import re
from pathlib import Path

MARK = '@pytest.mark.usefixtures("shrunk_row_caps")  # am-15 §8.1: the 5 000-row / 800-row shrink, requested explicitly'


def once(t, o, n, k=1, f=""):
    assert t.count(o) == k, (f, t.count(o), o[:80])
    return t.replace(o, n)


def mark_async_tests(t, skip=()):
    """Insert MARK above every `async def test_*` (its decorators included), except names in ``skip``."""
    tree = ast.parse(t)
    lines = t.split("\n")
    targets = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("test_") and node.name not in skip:
            first = min([d.lineno for d in node.decorator_list] + [node.lineno])
            targets.append((first, node.col_offset))
    for lineno, col in sorted(targets, reverse=True):
        lines.insert(lineno - 1, " " * col + MARK)
    return "\n".join(lines), len(targets)


def add_import(t, name, f):
    m = re.search(r"from _reanchor_58_support import \(\n", t)
    assert m, f
    return t[: m.end()] + f"    {name},\n" + t[m.end():]


def keep_fixture_name(t, f):
    if '__all__ = ["ledger58"]' in t:
        return t.replace('__all__ = ["ledger58"]', '__all__ = ["ledger58", "shrunk_row_caps"]', 1)
    raise AssertionError(f"no __all__ in {f}")


def generic(t):
    t = t.replace("_txn.TXN_STATEMENT_HARD_CAP", "_txn.TXN_ROW_HARD_CAP")
    t = t.replace("_txn.TXN_STATEMENT_WARN_THRESHOLD", "_txn.TXN_ROW_WARN_THRESHOLD")
    t = t.replace('hasattr(r, "statement_count")', 'hasattr(r, "row_count")')
    return t


counts = {}
# ---------------------------------------------------------------- test_supersede_reanchor_58.py
f = "test_supersede_reanchor_58.py"; t = Path(f).read_text(); t = generic(t)
t = once(t, "            counts.append(sum(len(fragment.statements) for fragment in fragments))",
         "            counts.append(composed_rows(fragments))  # r5: the ROW count compose bounds (am-15 §1.1)", f=f)
t = once(t, "``(TXN_STATEMENT_HARD_CAP − fixed) // per``.  A literal cap cannot survive the in-suite mutation leg.",
         "``(TXN_ROW_HARD_CAP − fixed) // per`` (r5: rows, am-15 §1.2).  A literal cap cannot survive the\n    in-suite mutation leg.", f=f)
t = once(t, '''        assert "statements, exceeding the hard cap" not in message, (
            "the bare compose() cap error was served — F-1 rules a TEACHING refusal before any write"
        )''', '''        # r5 (am-15 §8.2, A-9): r1's text check keyed on the RETIRED statement-cap wording and could no
        # longer fail. By TYPE now: neither the error nor its __cause__ is compose's own row-cap refusal …
        assert not isinstance(caught.value, _txn.TxnRowCapExceededError), (
            "the bare compose() row-cap refusal was served — F-1 rules a TEACHING refusal before any write"
        )
        assert not isinstance(caught.value.__cause__, _txn.TxnRowCapExceededError), (
            "the ledger re-wrapped compose()'s row-cap refusal — F-1 decides at the DERIVED cap, before compose"
        )
        # … and the positive control, same leg: composing cap+1 dependents' worth of rows DOES raise it, so the
        # negative half above is shown able to fire (no message text is asserted).
        rows_needed = _txn.TXN_ROW_HARD_CAP + 1
        with pytest.raises(_txn.TxnRowCapExceededError):
            _txn.compose(_txn.TxnFragment(statements=["RETURN NONE"] * rows_needed, params={}))''', f=f)
# L1: the accessor leg runs WITHOUT the fixture and asserts the unpatched cap first; L2 is new
t = once(t, '''        ledger, _env = ledger58
        fixed, per = await self._derive(ledger, monkeypatch, successor_deps)
        expected = (_txn.TXN_ROW_HARD_CAP - fixed) // per''', '''        ledger, _env = ledger58
        assert_unpatched_row_cap()  # am-15 §1.4 L1 / §8.1: this leg runs at the REAL row cap
        fixed, per = await self._derive(ledger, monkeypatch, successor_deps)
        expected = (_txn.TXN_ROW_HARD_CAP - fixed) // per''', f=f)
t = once(t, '''    async def test_MUTATION_an_extra_per_dependent_statement_MOVES_the_cap(''', '''    async def test_REAL_CAP_a_supersede_past_the_RETIRED_statement_cap_SUCCEEDS(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """am-15 §1.4 L2 (§8.1: REQUIRED, run WITHOUT the fixture): at the unpatched row cap, one supersede
        whose composed rows exceed SDK3's retired 5 000-statement cap re-anchors every dependent.  At the
        5 000 shrink a build that never left the statement cap (a literal, or ``min(old, new)``) passes
        every other pin — this leg refuses it."""
        ledger, _env = ledger58
        assert_unpatched_row_cap()
        fixed, per = await self._derive(ledger, monkeypatch, 0)
        dependents = (RETIRED_STATEMENT_CAP - fixed) // per + 1
        assert fixed + per * dependents > RETIRED_STATEMENT_CAP, "the leg must cross the retired bound"
        old = await create(ledger, "a hub past the retired statement cap")
        hub = await bulk_seed_dependents(ledger, old, dependents, tag="realcapx")
        result = await supersede(ledger, old)
        assert sorted(result.reanchored) == sorted(hub), (
            f"{dependents} dependents ({fixed + per * dependents} rows > the retired {RETIRED_STATEMENT_CAP}) "
            f"must re-anchor at the real row cap — a statement bound survives beside the row bound (F12)"
        )

    async def test_MUTATION_an_extra_per_dependent_statement_MOVES_the_cap(''', f=f)
t, counts[f] = mark_async_tests(t, skip={"test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies",
                                        "test_REAL_CAP_a_supersede_past_the_RETIRED_statement_cap_SUCCEEDS"})
for name in ("composed_rows", "shrunk_row_caps", "assert_unpatched_row_cap", "RETIRED_STATEMENT_CAP"):
    t = add_import(t, name, f)
t = keep_fixture_name(t, f)
assert "TXN_STATEMENT" not in t; Path(f).write_text(t)

# ---------------------------------------------------------------- test_reanchor_58_r2_probes.py
f = "test_reanchor_58_r2_probes.py"; t = Path(f).read_text(); t = generic(t)
t = once(t, "        counts.append(sum(len(f.statements) for f in fragments))\n", "        counts.append(composed_rows(fragments))\n", f=f)
t = once(t, '''    monkeypatch.setattr(_txn, "TXN_STATEMENT_HARD_CAP", _txn.TXN_ROW_HARD_CAP - 300)''',
         '''    # r5 (am-15 §8.4 = §1.4 L4): shrink the live ROW cap again by per·d from inside the fixture → −d.
    monkeypatch.setattr(_txn, "TXN_ROW_HARD_CAP", _txn.TXN_ROW_HARD_CAP - 300, raising=True)''', f=f)
t, counts[f] = mark_async_tests(t)
for name in ("composed_rows", "shrunk_row_caps"):
    t = add_import(t, name, f)
t = keep_fixture_name(t, f)
assert "TXN_STATEMENT" not in t and "statement_count" not in t; Path(f).write_text(t)

# ---------------------------------------------------------------- test_reanchor_58_r2_rulings.py
f = "test_reanchor_58_r2_rulings.py"; t = Path(f).read_text(); t = generic(t)
t = once(t, '''    """Composed body-statement count of a real supersede with ``dependents`` / ``successor_deps``."""''',
         '''    """Composed ROW count (``fragment_rows``, am-15 §1.1) of a real supersede with ``dependents`` /
    ``successor_deps``."""''', f=f)
t = once(t, "    return len(spy.calls[-1][0])\n", "    return spy.rows[-1]\n", f=f)
t = once(t, '''        assert "exceeding the hard cap" not in message and "nothing changed" in message.lower(), message''',
         '''        assert "nothing changed" in message.lower(), message
        # r5 (am-15 §8.2): compose's bare refusal by TYPE, never by the retired text
        assert not isinstance(caught.value, _txn.TxnRowCapExceededError), message
        assert not isinstance(caught.value.__cause__, _txn.TxnRowCapExceededError), message''', f=f)
t = once(t, '''        sizes = [len(statements) for statements, _params in chunks]''', '''        sizes = spy.heal_rows()  # r5: the ROW count of each heal chunk (am-15 §2)''', f=f)
t = once(t, '''{_txn.TXN_ROW_HARD_CAP}-statement "''', '''{_txn.TXN_ROW_HARD_CAP}-row "''', f=f)
t, counts[f] = mark_async_tests(t)
t = add_import(t, "shrunk_row_caps", f)
t = keep_fixture_name(t, f)
assert "TXN_STATEMENT" not in t; Path(f).write_text(t)

# ---------------------------------------------------------------- test_reanchor_58_r2_am2.py
f = "test_reanchor_58_r2_am2.py"; t = Path(f).read_text(); t = generic(t)
t = once(t, '''f"greedy packer against the {_txn.TXN_ROW_HARD_CAP}-statement cap''', '''f"greedy packer against the {_txn.TXN_ROW_HARD_CAP}-row cap''', f=f)
t, counts[f] = mark_async_tests(t)
t = add_import(t, "shrunk_row_caps", f)
t = keep_fixture_name(t, f)
assert "TXN_STATEMENT" not in t; Path(f).write_text(t)

# ---------------------------------------------------------------- test_reanchor_58_r2_scale.py
f = "test_reanchor_58_r2_scale.py"; t = Path(f).read_text()
t = once(t, "from loremaster.store._txn import SurrealStoreError\n", "from loremaster.store._txn import SurrealStoreError, TxnRowCapExceededError\n", f=f)
t = once(t, '''        assert "exceeding the hard cap" not in str(error), (''', '''        # ⚠ DUAL (contract r5, am-15 §8.2): by TYPE, not the retired text — no longer AST-equal to batch 2
        assert not isinstance(error, TxnRowCapExceededError) and not isinstance(error.__cause__, TxnRowCapExceededError), (''', f=f)
t += '''

# L3 (contract r5, packet 58 amendment 15 §1.4; §8.1: REQUIRED, run WITHOUT the fixture): at the UNPATCHED row
# cap, a straggler population whose heal composes MORE rows than SDK3's retired 5 000-statement cap heals in ONE
# transaction. A build that never left the statement cap chunks it and passes every 5 000-shrunk pin.
async def test_L3_REAL_CAP_a_heal_past_the_RETIRED_statement_cap_is_ONE_transaction(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    assert_unpatched_row_cap()
    fixed, per = await measure_heal_shape(ledger, env, "l3shape")
    count = (RETIRED_STATEMENT_CAP - fixed) // per + 1
    head = await create(ledger, "the L3 successor")
    legacy = "l3scalelegacyblocker000000000000"
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    stragglers = await bulk_seed_dependents(ledger, legacy, count, tag="l3scale")
    spy = ComposeSpy()
    booted = new_ledger(env)
    try:
        with spy.installed():
            await booted.ensure_ready()
    finally:
        await booted.close()
    chunks = spy.heal_rows()
    assert len(chunks) == 1 and chunks[0] > RETIRED_STATEMENT_CAP, (
        f"{count} one-blocker stragglers compose {fixed + per * count} heal rows (> the retired "
        f"{RETIRED_STATEMENT_CAP}) under the real row cap: ONE chunk expected, got {chunks}"
    )
    assert await column(ledger, stragglers[0]) == [head] and await column(ledger, stragglers[-1]) == [head]
'''
t, counts[f] = mark_async_tests(t, skip={"test_L3_REAL_CAP_a_heal_past_the_RETIRED_statement_cap_is_ONE_transaction"})
t = once(t, "from _reanchor_58_support import (\n", "import pytest\nfrom _reanchor_58_support import (\n", f=f)
for name in ("shrunk_row_caps", "assert_unpatched_row_cap", "RETIRED_STATEMENT_CAP", "ComposeSpy", "measure_heal_shape"):
    t = add_import(t, name, f)
t = keep_fixture_name(t, f)
Path(f).write_text(t)

# ---------------------------------------------------------------- test_reanchor_58_r3_convergence.py
f = "test_reanchor_58_r3_convergence.py"; t = Path(f).read_text()
t = once(t, "    every sent transaction ≤ ``TXN_STATEMENT_HARD_CAP`` — where each row's WEIGHT is its own composed\n    statement count (am-8 §2).",
         "    every sent transaction ≤ ``TXN_ROW_HARD_CAP`` — where each row's WEIGHT is its own composed ROW\n    count, ``_txn.fragment_rows`` (am-8 §2; r5: am-15 §2, at the §8.1 5 000-row shrink, read live).", f=f)
t = once(t, '''# SDK3 R8 F12 (round 4): the ROW bound REPLACES the statement cap; packet 58's packer re-sizes by ROWS when 58
# is revived (dormant — this file is RED on the unbuilt 58 API). Read without breaking COLLECTION once the
# statement cap is deleted (``None`` → every use raises; already RED). Re-size at 58's revival
# (packet doc §R4, fork F19). The ``cast`` keeps this file's (and its importers') arithmetic typed as
# today; at runtime it is ``None`` once the constant is gone.
CAP = cast("int", getattr(_txn, "TXN_STATEMENT_HARD_CAP", None))
''', '''# SDK3 R8 F12 / R12 F19 / F21 + packet 58 amendment 15 §2 / §8.1 (contract r5): the ROW bound replaced the
# statement cap. Every leg requests the 5 000-row shrink (``shrunk_row_caps``) and reads the cap LIVE through
# ``_cap()`` — never a module-level copy taken at import (the wrong build F21 forbids).


def _cap() -> int:
    """The row cap as ``compose`` and the packer see it right now (read live — F21)."""
    return _txn.TXN_ROW_HARD_CAP
''', f=f)
t = once(t, '''def _heal_chunks(spy: ComposeSpy) -> list[int]:
    return [len(statements) for statements, _params in spy.heal_calls()]''', '''def _heal_chunks(spy: ComposeSpy) -> list[int]:
    """The ROW count (``fragment_rows``) of each heal chunk the boot composed (am-15 §2)."""
    return spy.heal_rows()''', f=f)
t = re.sub(r"\bCAP\b", "_cap()", t)
t = t.replace("TXN_ROW_HARD_CAP", "TXN_ROW_HARD_CAP")  # no-op guard
assert "_cap()_cap()" not in t
t, counts[f] = mark_async_tests(t)
t = add_import(t, "shrunk_row_caps", f)
t = keep_fixture_name(t, f)
assert "TXN_STATEMENT" not in t; Path(f).write_text(t)

# ---------------------------------------------------------------- test_reanchor_58_r3_probes.py
f = "test_reanchor_58_r3_probes.py"; t = Path(f).read_text(); t = generic(t)
t = once(t, "    assert all(len(s) <= _txn.TXN_ROW_HARD_CAP for s, _p in spy.heal_calls())",
         "    assert all(rows <= _txn.TXN_ROW_HARD_CAP for rows in spy.heal_rows()), spy.heal_rows()", f=f)
t = once(t, '''    assert "cap" in str(caught.value).lower() or "statement" in str(caught.value).lower(), repr(caught.value)''',
         '''    assert "cap" in str(caught.value).lower() or "row" in str(caught.value).lower(), repr(caught.value)''', f=f)
t, counts[f] = mark_async_tests(t)
t = add_import(t, "shrunk_row_caps", f)
t = keep_fixture_name(t, f)
assert "TXN_STATEMENT" not in t; Path(f).write_text(t)

# ---------------------------------------------------------------- test_reanchor_58_r4_state.py
f = "test_reanchor_58_r4_state.py"; t = Path(f).read_text()
t = once(t, "    from test_reanchor_58_r3_convergence import CAP, SHAPES, seed_population\n",
         "    from test_reanchor_58_r3_convergence import SHAPES, _cap, seed_population\n", f=f)
t = once(t, "    assert CAP > 0\n", "    assert _cap() > 0\n", f=f)
t = once(t, "    from test_reanchor_58_r3_convergence import CAP, _heal_chunks, seed_population\n",
         "    from test_reanchor_58_r3_convergence import _cap, _heal_chunks, seed_population\n", f=f)
t = once(t, '''    """fit = ``(CAP − fixed) // weight``, MEASURED off ``compose`` (the convergence sweep's own helper)."""''',
         '''    """fit = ``(cap − fixed) // weight`` (cap read live; r5: the §8.1 shrink), MEASURED off ``compose``."""''', f=f)
t = once(t, "    return (CAP - fixed) // weight\n", "    return int((_cap() - fixed) // weight)\n", f=f)
t, counts[f] = mark_async_tests(t)
t = add_import(t, "shrunk_row_caps", f)
if '__all__ = ["ledger58"]' in t:
    t = keep_fixture_name(t, f)
Path(f).write_text(t)
print(counts)
```

## §GATES — gate receipts (brief-base §1; logs under the brief-named scratchpad `…/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/`)
| gate | exact command | log | EXIT | count / verdict line | TREE= |
|---|---|---|---|---|---|
| currency typecheck+ruff (final test files, BEFORE the §9 63c edits) | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `gate-currency-r5-final.log` | 1 | `typecheck RED_ADJUDICATED — 84 residual(s), owned by: packet-58-contract · packet-64b-i-contract` · `ruff GREEN` · the only orphan: `pytest NOT_RUN — claimed by the manifest` (the `--legs` filter by design: no pytest in a contract round, CLAUDE.md TEST SCOPE) | `69d97e2a…` (HEAD `e13b8c9`) |
| registry | `uv run python scripts/pending_contract_gate.py --verify-registry` | `gate-verify-r5-final.log` | 0 | no FAIL lines; `self-destruct: 19 import-checked absent · 46 UNCHECKED` | `69d97e2a…` |
| first currency run (superseded) | same as row 1 | `gate-currency-r5.log` | 1 | `typecheck RED_ORPHANED — 5` (all mine: the support re-export + r4_state's stale `CAP` import) — fixed, re-run as row 1 | `2f4680b8…` |
- ⚠ **Receipt bound, stated:** the §9 63c edits (4 files, member additions) and the r4_state fixture re-export landed AFTER rows 1–2 ran, so those receipts do NOT cover them; the re-run is §GATES-2 below (or, if absent at my deadline, owed — see §STATE).

### `scripts/probe_hub_txn_58.py` — the committed copy vs am-15 §INSTRUMENT (deviation D-R5-5)
The verbatim copy (md5 `14d02cf5…`) put 11 RED_ORPHANED on the per-commit gates (6 mypy `dict-item`/`arg-type`, 5 E501; `gate-currency-r5-final2.log`). Gates are per-commit law, so the committed copy (md5 `b82827855e68e8da5f5b8ab981928aa3`) adds type annotations (`from typing import Any`; `rows: list[Any]`, `edges: list[Any]`, `params: dict[str, Any]`) and line wraps — no statement, value or control-flow change. ruff clean, `mypy` "Success". **Receipt on the COMMITTED copy** (`uv run python scripts/probe_hub_txn_58.py 3 1665`, repo root, 2026-11-09 ~22:47Z): `N=3 statements=13 … outcome=committed rewired=[3] new_edges=[3] old_edges=[0]` and `N=1665 statements=4999 … elapsed_s=1.43 outcome=committed rewired=[1665] new_edges=[1665] old_edges=[0]`.
```diff
--- /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/probe_hub_txn_58.py	2026-11-09 17:00:55.038007036 -0500
+++ scripts/probe_hub_txn_58.py	2026-11-09 17:47:00.090517830 -0500
@@ -17,6 +17,7 @@
 import sys
 import time
 import uuid
+from typing import Any
 
 from surrealdb import AsyncSurreal, RecordID
 
@@ -44,13 +45,16 @@
         await connection.query("DEFINE TABLE task SCHEMALESS")
         await connection.query("DEFINE TABLE blocks TYPE RELATION IN task OUT task ENFORCED")
         old, new = RecordID("task", "old"), RecordID("task", "new")
-        await connection.query("CREATE $old CONTENT {status: 'open', blocked_by: [], events: []}", {"old": old})
+        await connection.query(
+            "CREATE $old CONTENT {status: 'open', blocked_by: [], events: []}", {"old": old}
+        )
         for start in range(0, dependents, SEED_BATCH):
             ids = range(start, min(start + SEED_BATCH, dependents))
-            rows = [
-                {"id": RecordID("task", f"y{i}"), "status": "open", "blocked_by": [old], "events": []} for i in ids
+            rows: list[Any] = [
+                {"id": RecordID("task", f"y{i}"), "status": "open", "blocked_by": [old], "events": []}
+                for i in ids
             ]
-            edges = [{"in": old, "out": RecordID("task", f"y{i}")} for i in ids]
+            edges: list[Any] = [{"in": old, "out": RecordID("task", f"y{i}")} for i in ids]
             await connection.query("INSERT INTO task $rows", {"rows": rows})
             await connection.query("INSERT RELATION INTO blocks $edges", {"edges": edges})
 
@@ -61,7 +65,7 @@
             "CREATE $new CONTENT {status: 'open', blocked_by: [], events: []}",
             "DELETE blocks WHERE in = $old",
         ]
-        params: dict[str, object] = {"old": old, "new": new, "ev": {"action": "superseded"}}
+        params: dict[str, Any] = {"old": old, "new": new, "ev": {"action": "superseded"}}
         note = {"action": "dependency_reanchored", "from": "task:old", "to": "task:new"}
         for i in range(dependents):
             params[f"y{i}"] = RecordID("task", f"y{i}")
@@ -92,11 +96,16 @@
         rewired = await connection.query(
             "RETURN array::len((SELECT id FROM task WHERE blocked_by CONTAINS $new))", {"new": new}
         )
-        new_edges = await connection.query("RETURN array::len((SELECT id FROM blocks WHERE in = $new))", {"new": new})
-        old_edges = await connection.query("RETURN array::len((SELECT id FROM blocks WHERE in = $old))", {"old": old})
+        new_edges = await connection.query(
+            "RETURN array::len((SELECT id FROM blocks WHERE in = $new))", {"new": new}
+        )
+        old_edges = await connection.query(
+            "RETURN array::len((SELECT id FROM blocks WHERE in = $old))", {"old": old}
+        )
         stamped = await connection.query("RETURN (SELECT VALUE superseded_by FROM ONLY $old)", {"old": old})
         print(
-            f"timeout={TXN_TIMEOUT_SECONDS} settle={SETTLE_SECONDS if TXN_TIMEOUT_SECONDS else 0} old.superseded_by={stamped} "
+            f"timeout={TXN_TIMEOUT_SECONDS} settle={SETTLE_SECONDS if TXN_TIMEOUT_SECONDS else 0} "
+            f"old.superseded_by={stamped} "
             f"N={dependents} statements={len(statements)} params={len(params)} text_bytes={len(text)} "
             f"elapsed_s={elapsed:.2f} outcome={outcome} rewired={rewired} new_edges={new_edges} "
             f"old_edges={old_edges} over_30s={elapsed > 30.0}",
```

## §RED@HEAD — BASE = HEAD `99044d0` + §HELD 1/3 (+ part 4 in the delta legs) + r5 tests (2026-11-09)
- **Declared BEFORE the run** from `--collect-only` (`collect_r5_final.txt`, 200 ids over the 9 r5-touched files; md5 `49cda452…`): 27 ids with their expected state (`declared_r5_head_final.txt`, md5 `b13322c053876b6c5371c33874b2e3ef`) — 25 RED (the r5 NEW / re-keyed pins: L1 ×2, L2, L3, PR14 = L4, the hub refusal ×2, the WARN crossing, PR13's control, r2's K legs ×6, PR16, the un-annotated pin, the four-class pins ×8) and 2 GREEN (PR13's stubbed leg; the un-annotated control).
- **base3** (`sat-base3.log`, TREE `f61a2b8e…`, full declared set, 117 files): `428 failed, 7623 passed, 47 skipped, 16 errors in 974.91s`. `red_diff.py` (§INSTRUMENTS): **`declared=27 matched=27 mismatched=0 absent=0`** — both directions.
- **Regression check vs base1** (pre-r5 HEAD + §HELD): GREEN→RED = 14 = 13 `test_reanchor_58_r4_state` setup errors (MY bug: the fixture import was pruned by `ruff --fix` because the file had no `__all__` entry for it — fixed, re-run in base3d: r4_state back to its base1 state, 16 green / 3 red, the same 3 as base1) + **1 unrelated**: `test_surreal_store.py::TestHybridSearch::test_rrf_ordering_is_deterministic` (GREEN in base1/ref1/base2/ref2, RED in base3; no r5/§HELD code on its path) → **finding #613**, not adjudicated as flaky by me. RED→GREEN = 0.
- **base3d** (delta: the 4 63c files + q1c, r5_rows, render_58 with §HELD part 4, r4_state; `sat-base3d.log`, TREE `cd65e4b6…`): `13 failed, 737 passed` — r5_rows ×9 (the ruled classes / heal unbuilt: declared RED), render_58 ×1 (now past the walker drift to the unbuilt `SupersedeResult`: right reason), r4_state ×3 (as base1). **The four 63c files: 0 red at BASE** (derived additions are empty pre-58; their landed behaviour is unchanged).
- Right-reason spot reads (failure text, base3/base3d): the four-class pins red on `packet 58 rules _txn.<Class> … got None`; the un-annotated pin on `non-vacuity: … 0 heal chunks`; L1/L2/PR14/K legs on the missing `max_reanchor_dependents`; PR13 CONTROL on "the house size WARN did not fire once" (HEAD's task ledger does not log through the house function — BC-r5-2).

## §SAT — REF = BASE + `build_ref_r5.py` (v3 for ref3/ref3d; v4 for the delta2 legs), 2026-11-09
- **ref3** (`sat-ref3.log`, TREE `d269dc4e…`, 117 files): `262 failed, 7973 passed, 51 skipped, 15 errors in 2077.73s`; `Killed/MemoryMax/Timeout` 0; `loremaster.__file__` inside `c58r5ref`. Reds by owner (`owners.py`):
  - packet-64b-i-contract: 186 (its 64b files + `test_mcp_server.py` ×28) — unbuilt 64b-i, as in r4.
  - packet-58-contract files: r4_state ×15 (13 my fixture bug, re-run in ref3d), r3_tiers ×4, r2_rulings ×1, cas_seam ×1 (64b `_run_guarded`), forgery sweep ×2.
  - UNOWNED: the 67 am-15 §9 cells (am37 ×9, q1c ×49, q1b ×8, a28c ×1) + render_58 ×1 (§HELD part-1 drift).
- **ref3d** (delta, same files as base3d; TREE `8ee0226a…`): **`1 failed, 1156 passed`**. **All 67 §9-owned ids GREEN** (per file: am37 9→9 green of 146, q1c 49→49 of 238, q1b 8→8 of 85, a28c 1→1 of 653), render_58 7/7 GREEN (part 4), r5_rows 10/10 GREEN, r4_state 17/18 — the one red is 64b-i's `findings.py::_run_guarded` leg (`FindingLedger.report() got an unexpected keyword argument 'title'`, 64b FK-1; registered under packet-64b-i-contract).
- **The remaining 58-owned REF reds, adjudicated:**
  - `test_reanchor_58_r3_tiers.py` ×4 (`TxnUniqueViolationError` has no tier) — a **reference** gap, not a contract one: 63c-i-a's am-33 class is now BUILT, so the r3 tier table must carry it (am-7 §0 row 3: WARNING). Reference v4 adds it → delta2 (§SAT-DELTA2).
  - `test_reanchor_58_r2_rulings.py::…test_the_ledger_catches_the_TYPE_never_the_text` — red on EVERY leg since base1: its stand-in `lambda _label, message:` cannot take the `kind=` HEAD's caller now passes (63c/66 drift in a 58 pin). Fixed (`**_typed`) → delta2.
  - `scripts/test_forgery_door_sweep.py` ×2 — red at **plain HEAD** too (no 58 code): **finding #614** (also: its packet-58 registry entry would mask it as RED_ADJUDICATED). Not attributable to r5 or the reference.
- **r5-attributable reds on the reference: 0** (pending delta2 for the two re-base cures above).

### §SAT-DELTA2 — reference v4 + the TYPE-pin fake fix (2026-11-09 ~22:56Z)
| leg | tree | files | log · TREE | count | EXIT |
|---|---|---|---|---|---|
| REF delta2 | `c58r5ref` (+ v4 `_txn.py 8d37d2f4…`) | r3_tiers, r2_rulings, r3_am6, r5_rows, a28b, a28c | `sat-ref4d.log` · `a45bb3b0…` | **`817 passed, 1 warning in 91.57s`** | 0 |
| BASE delta2 | `c58r5` | same | `sat-base4d.log` · `28b82d11…` | `60 failed, 421 passed` = 51 red at base1 too + 9 new r5_rows ids (declared RED); **GREEN→RED 0** | 1 |
- The one warning (REF): `RuntimeWarning: coroutine '_opens_its_own_socket.<locals>._drive' was never awaited` at `test_reanchor_58_r3_cas_seam.py:625` (`test_FK_r3_4…`) — pre-existing r3 test code, not touched by r5; residual R-5 below.
- **SAT verdict over the declared targeted set (ref3 full + ref3d + ref4d deltas, reference v3→v4): 0 r5-attributable reds.** Remaining REF reds are owned elsewhere: packet-64b-i (186 + r4_state/cas_seam `_run_guarded`), finding #614 (forgery sweep, red at plain HEAD), finding #613 (rrf ordering, BASE only, once).

## §RESIDUALS (named, not rounds)
- **R-1:** `measure_supersede_shape`-style duplication — three pre-existing private supersede-shape measurers (`test_supersede_reanchor_58._derive`, `test_reanchor_58_r2_rulings._supersede_count`, r2_probes PR2's `_count`) and r4_state's `_measure_fit` beside `convergence.measure_weight`. Fold at the next 58 contract touch.
- **R-2:** the four 63c hand-lists (am-15 §9.2 says so; sidecar asked the lead whether to file a finding — the commit message names **#612**).
- **R-3:** `build_ref_r5.py`'s reference keeps the r1–r4 chain's 9 ruff style errors (SAT host only; satisfiability after lint cleanups not re-proved).
- **R-4:** L1–L3 are GUARDED by size (a hidden statement-style bound above ~5 000 is not killed) — §FORALL row 1.
- **R-5:** the r3 cas_seam `RuntimeWarning` above.
- **R-6:** §INVENTORY's Step-2 sweep missed the `CAP` alias (§SWEEP-R5) — class noted; the sidecar's §3 cross-check did not catch it either.

## §GATES-2 — final gate receipts on the FINAL test/registry/probe bytes (HEAD `39f4c33`, 2026-11-09 ~23:12Z)
| gate | command | log | EXIT | verdict | TREE= |
|---|---|---|---|---|---|
| currency typecheck+ruff | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `gate-currency-r5-final4.log` | 1 | `typecheck RED_ADJUDICATED — 84 residual(s), owned by: packet-58-contract · packet-64b-i-contract`; `ruff GREEN`; **no RED_ORPHANED**; the only orphan is the leg-filtered `pytest NOT_RUN` (by design of `--legs`; the full suite is the packet close-out's) | `1c5a7ad9…` |
| registry | `uv run python scripts/pending_contract_gate.py --verify-registry` | `gate-verify-r5-final4.log` | 0 | clean | `99ac76a6…` |
- The two TREE values differ because `tree_id.sh` hashes every dirty file and this report was being written between the two runs; no test, registry or probe byte changed after row 1 started. ⚠ So any further edit to THIS REPORT changes `TREE=` without voiding what the gates checked; an edit to any other listed path voids them.

## §STATE (2026-11-09 ~23:15Z, inside the 150-min deadline)
Done. Every am-15 fold item (1–13, incl. §8.5 and §9.2) executed or delivered. NOT done by design: §MUTATION (BRIEF CONFLICT, the adversary's delta grade per am-15 §5). Open for the lead: findings #613 / #614, F-3 (packet doc).

## §R5.1 — amendment 15 §10 + finding #615 (lead directive #20014, 2026-11-09; base HEAD `89b26ae`)

### STEP 1 (§10.2) — every packet-58-contract entry lists its red node ids
- **Declared BEFORE the confirming run** (`declare_red.py` → `declared_final.json`, md5 `a936d28a6aa7e0885135792a38e21c35`): per file, the reds of my latest HELD-applied BASE leg (base4d > base3d > base3), restricted to ids that `pytest --collect-only` lists at plain HEAD (`collect_head.txt`, 1 855 ids over the 33 registered files, md5 `423858fb…`); the two shared files (r4_state, cas_seam) split by failure reason (64b-i's `_run_guarded` / `title=` → 64b-i, else 58); #614's two ids REMOVED. 58: 225 ids, 64b-i: 191 (+3 files I had never run: no prediction — said here).
- **Confirming run at PLAIN HEAD** (`head_run.sh`, main tree, no §HELD; `head_run.log`, TREE `21842aa4…`, `loremaster.__file__` = the main tree): `542 failed, 1311 passed, 2 skipped in 338.66s`, EXIT=1, no cap kill/timeout.
- **Diff both ways** (`diff_head.py`): `declared=416 observed_red=542 both=410 declared_not_red=6 red_not_declared=132`. Every mismatch adjudicated:
  - declared-but-GREEN 6 (`test_mcp_server.py` ×3, `test_task_read_surface.py` ×2, `test_blocks_edge.py` ×1): red in my legs only because §HELD part 1 edits `test_mcp_server.py` / `_task_fakes.py`; GREEN at plain HEAD → NOT listed (listing them would self-destruct).
  - undeclared-red 124 in `test_comms_footer.py` (80), `test_findings_scope_domain_64b.py` (24), `test_findings_identity_64b.py` (22) — the three 64b-i files outside my targeted set; every message is a 64b-i UNBUILT/`arm_finding_identity`/`title=` reason → 64b-i (Step 3).
  - undeclared-red 3 in `test_reanchor_58_r2_probes.py` (EXPLAIN plans `['SelectProject','Compute','TableScan']` / `['Aggregate','TableScan']`): index-served pins that need §HELD part 1's `blocked_by.*` index — red at plain HEAD for 58's reason → listed under 58.
  - undeclared-red 2 = #614's two ids, deliberately NOT listed (§10.2).
- **Registry written** (`write_red_ids.py packet-58-contract`, text-level, every id JSON-quoted, round-trip asserted against the json): 20 entries, **225 ids**; `missing_symbols` unchanged. `--verify-registry` EXIT=0 (`r51/verify_step1.log`).
- ⚠ **FORK for the sidecar/lead, found by the plain-HEAD run:** `test_forgery_door_sweep.py::…::test_every_store_door_in_ensure_ready_over_a_legacy_store_FAILS_LOUD` reds at plain HEAD on its FIRST assertion — `the derived door set for ensure_ready over a legacy store is 4, not the 5` — because 58's straggler-heal read (the 5th door) is unbuilt. That is a **58 reason**, raised BEFORE #614's `control_observation == 2` assertion. So `fix(614)` cannot green it at HEAD; after `fix(614)` it stays red and, unlisted, renders RED_ORPHANED. Readings: (A) list it under 58 AFTER `fix(614)` lands (its red is then 58's alone); (B) list it now (but then the gate cannot show #614's mask removed on it). I followed the directive (not listed now) and would pick (A). The SWALLOWS twin reds on #614's assertion (`the swallowing build's UNFAULTED control must still migrate correctly`) and should go GREEN with `fix(614)` — to be confirmed by the builder's run.
- **The mask, watched removed** (`scoped_gate.sh fds614 scripts/test_forgery_door_sweep.py` = `pending_contract_gate.py --currency --legs pytest -- scripts/test_forgery_door_sweep.py`, cgroup-capped, no `-n` forwarded; `r51/scoped-fds614.log`, TREE `4931a0df…`, EXIT=1): `pytest RED_ORPHANED — 2 residual(s) with NO owner` · `ORPHAN: …::test_a_ledger_that_SWALLOWS_its_backfill_failure_is_CAUGHT` · `ORPHAN: …::test_every_store_door_in_ensure_ready_over_a_legacy_store_FAILS_LOUD` — exactly #614's two ids; the listed 58 leg (`TestThisInstrumentIsTYPECHECKED::test_mypy_is_clean_over_the_sweep_and_its_contract`) is adjudicated (no orphan). (typecheck/ruff `NOT_RUN` there is the `--legs pytest` filter.)
- **STEP 1 commit-ready:** `scripts/pending_contracts.yaml` (+ this report). STOPPED here per the directive; posted on lore_comms.

### STEP 4 (§10.5) — §DECLINED: every proof I declined under the role boundary (proof · the pin it would prove · why declined)
Written BEFORE the adversary's enumeration; the adversary diffs its own list against this one (am-15 §10.5).
| # | declined proof (a wrong build, or a replay) | the r5 pin(s) it would prove | why declined |
|---|---|---|---|
| X1 | a statement bound kept beside the row bound (`min(5000-derived, row-derived)`; or a literal 5 000) | L1 `…test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[0,2]`, L2 `…test_REAL_CAP_a_supersede_past_the_RETIRED_statement_cap_SUCCEEDS`, L3 `test_reanchor_58_r2_scale.py::test_L3_REAL_CAP_…` | wrong build — the adversary's (role boundary) |
| X2 | the row cap copied at IMPORT (`from _txn import TXN_ROW_HARD_CAP`) in the accessor / packer | every `shrunk_row_caps` cap leg; PR14 = L4 | same |
| X3 | a private counter (`len(statements)`) instead of `fragment_rows` | none can (rows ≡ statements on 58's fragments) — am-15 §2's named bound; cold-audit mutation of `fragment_rows` | not provable by a behaviour pin at all; routed to the cold audit by the ruling |
| X4 | a `rows=` under-declaration on a 58 fragment | `test_reanchor_58_r5_rows.py::TestFiftyEightsFragmentsAreUnannotated::…` | wrong build |
| X5 | a private WARN comparison (800 / 10 000 / an import-time copy) in `TaskLedger._apply` | `…test_crossing_the_WARN_threshold_logs_ONE_warning_and_SUCCEEDS`, PR13 + `test_PR13_CONTROL_…` | wrong build |
| X6 | a substring classifier (`marker in lowered`) for any of 58's four markers | `TestTheFourClassesAreTypedAndAnchored::test_a_THROW_LED_by_the_marker_…` ×4; 63c's echo sweep over the four `fifty-eight-throw-*` hosts | wrong build |
| X7 | a raise site that bypasses `_domain_rejection_error` (`if label ==` locally), or a class left on the unspecified label | `…test_the_class_is_recognised_by_construction_and_built_by_the_one_mapping_helper` ×4; 63c's q1b/q1c/am37 legs | wrong build |
| X8 | the hub refusal re-wrapping compose's `TxnRowCapExceededError` (`raise TaskLedgerError(...) from error`) | `…test_one_past_the_cap_is_REFUSED_byte_inert_and_TEACHES[0,2]` (type + `__cause__`), r2 K legs ×6, PR16 | wrong build |
| X9 | a refusal AFTER the stamp at cap+1 (writes then rolls back / partially commits) | the byte-inert `snapshot` legs (same ids as X8) | wrong build |
| X10 | a packer pricing every row at one unit (or by the one-blocker weight) | r3 convergence SCALES × shapes, PC (two-blocker), PR18r2/PR19 | wrong build |
| X11 | the heal's chunk boundary read at import | convergence legs under the fixture | wrong build |
| X12 | the B-6 call left at two arguments (`_log_transaction_size(stmts, params)`) | every supersede/heal leg on a correct build (TypeError) — a crash, not a silent wrong | wrong build; also the SAT already exhibited it (ref1, 640 reds) |
| X13 | 58's `TxnUniqueViolationError` tier dropped from `_ROLLBACK_LOG_TIERS` | `test_reanchor_58_r3_tiers.py` ×4 (exhibited by ref3 before v4) | wrong build — exhibited only by my reference's own gap, not built on purpose |
| X14 | replaying adversary-58-r1..r3's seven W-* builds onto the re-based reference | the r1–r4 pins they killed | am-15 §5 item 3 assigns the re-anchoring to the adversary; the role boundary forbids it to me |
| X15 | (§10.2) a gate partition that still adjudicates an UNLISTED red in a 58 file | the registry's per-node lists (Step 1) | a wrong build of the GATE; the scoped run above shows the correct gate orphaning #614's two ids, which is the observation, not the mutation |
| X16 | (§10.3) a heal that swallows its APPLY store fault | Step 2's straggler-world legs (not yet written) + r2's `TestAHealStoreFaultIsLOUD::test_every_heal_door_after_the_backfill_RAISES[store,transport]` | wrong build |

### STEP 3 (#615) — every remaining entry per-node; the closing rule pinned contract-ahead
- **(a) packet-64b-i-contract** — same declaration (fixed before the plain-HEAD run) and the same confirming run as Step 1; 12 of its 15 files were predicted, 3 (`test_comms_footer.py`, `test_findings_identity_64b.py`, `test_findings_scope_domain_64b.py`) had no prediction (outside my targeted set) and take their reds from the run — every one an UNBUILT 64b-i message (`arm_finding_identity` import, `report(title=…)`, `capability=`, `scope_shape_ok` …). Shared files split by reason (r4_state / cas_seam: `_run_guarded`/`title=` → 64b-i). Written with `write_red_ids.py packet-64b-i-contract`: **15 entries, 315 ids**; `--verify-registry` EXIT=0 (`r51/verify_step3a.log`). ⚠ Scope note: I edited only that registry entry's `red_nodeids` (grant (a)); the 64b-i files, owner, trigger and rationale are untouched.
- **(b) other file-level entries:** **none.** The registry has exactly two bounds and, after (a), 0 entries without `red_nodeids` (checked by loading the yaml). #615's trigger "the last file-level entry converts" is met by this commit.
- **(c) the closing rule, contract-ahead** — in the gate's F6 module (`scripts/test_pending_contract_gate_f6.py`, the module that owns `red_nodeids` semantics): **`test_615_an_entry_with_no_red_nodeids_owns_NO_pytest_red`**. It is the EXISTING control `test_CONTROL_a_symbols_only_file_keeps_file_level_pytest_adjudication` inverted in place (same fixture: a symbols-only entry + a node-listed entry; a red in the symbols-only file must now be `RED_ORPHANED`; same-run control: the listed reds stay adjudicated) — a pin added BESIDE the old control would have been unsatisfiable together with it. The module docstring's bullet re-worded to match. DUAL row: R5-D9 below.
  - **Declared before the run** (`r51/declared_615.txt`): F6 module exactly 1 red (the #615 id); `scripts/test_pending_contract_gate.py` 0 red. **Run** (`r51/run_615.sh`, TREE `d1c69ecd…`): `1 failed, 108 passed in 1.46s`, EXIT=1 — matches. Right reason: `AssertionError: ('RED_ADJUDICATED', ())` — HEAD's file-level fallback owns the symbols-only red.
  - Registered under `packet-58-contract` as a per-node entry (`scripts/test_pending_contract_gate_f6.py` → that one id), with a comment naming #615 and "a builder removes the file-level fallback in `partition_pytest`". `--verify-registry` EXIT=0 (`r51/verify_step3c.log`).
  - ⚠ **SAT TRAP for the #615 builder — FLAG (outside my one-pin grant):** `scripts/test_pending_contract_gate.py::test_pytest_failure_inside_a_registered_file_is_expected` asserts a failure in a fixture-registered file is EXPECTED through the same file-level fallback; a correct #615 build reds it. Exact edit I would make (needs a grant): give that module's fixture entry a `red_nodeids` list naming `…::test_pin` (or re-point the test at a node-listed entry), keeping its CONTROL twin `test_pytest_failure_outside_the_registry_is_unexpected` unchanged. Without it the builder is trapped between the #615 pin and that test.
- **DUAL R5-D9:** `test_CONTROL_a_symbols_only_file_keeps_file_level_pytest_adjudication` → **dropped deliberately / inverted** (its premise — packet 58's file-level ownership — retired by steps 1 and 3(a)); spec: finding #615's closing rule, am-15 §10.2.

### STEP 2 (§10.3, fold item 14) — the straggler world and the heal-door legs (after `fix(614)` = `3e003ef`)
- **The world** (`scripts/forgery_door_sweep.py`, free per the lead's #20017): `legacy_task_store` and NEW `straggler_task_store` are two calls of one builder `_task_store_world(*, straggler)` (no second copy of the world); the straggler variant adds three rows — an open head, a legacy blocker `superseded_by` it, and a dependent whose `blocked_by` names the legacy row (`_seed_legacy_task` gained an optional `superseded_by`). The legacy world is unchanged in behaviour. ruff + `mypy scripts/forgery_door_sweep.py` clean.
- **Measured once at HEAD** (probe, before writing the pins): both worlds give the SAME 4 doors (`execute_transaction`, `execute_read_transaction`, `run_query`, `execute_transaction`) — without 58's heal the straggler adds nothing, exactly §10.3's premise.
- **The legs** (`scripts/test_forgery_door_sweep.py::TestTheHealDOORSAreOnTheStragglerPath`), every comparison against a DERIVED quantity (the legacy world's own door list; the write seam measured as the DDL door's seam), never a literal:
  - (i) `test_i_the_straggler_world_adds_EXACTLY_the_heal_APPLY_door_and_every_derived_door_fires` — straggler `control_calls == legacy + 1`; every derived door faulted (`len(doors) == control_calls`, reach checked); the legacy doors kept in order; the added door last and on the write seam.
  - (ii) `test_ii_every_door_over_the_straggler_world_FAILS_LOUD_the_heal_APPLY_included` — non-vacuity first (the apply door is on the path), then `all_doors_loud` and the apply door `loud and fault_traceable`.
  - (iii) `test_iii_a_heal_that_SWALLOWS_its_APPLY_fault_is_CAUGHT` — the instrument's positive control in its own idiom (catch-all wrapper over the captured `TaskLedger._reanchor_stragglers`, monkeypatched): the apply door is reported silent; the DDL door stays loud.
  - (iv) `test_iv_CONTROL_without_the_straggler_the_sweep_never_reaches_the_heal_APPLY` — the legacy world observes one FEWER write-seam door than the straggler world.
  - Cited, not twinned: the heal READ door on the legacy world (`…::test_every_store_door_in_ensure_ready_over_a_legacy_store_FAILS_LOUD`'s `control_calls == 5`), and a heal store fault raising at either door (`test_reanchor_58_r2_rulings.py::TestAHealStoreFaultIsLOUD::test_every_heal_door_after_the_backfill_RAISES`).
- **RED@HEAD, declared before the run** (`r51/declared_fds_red.txt`, md5 `39dc5594…`; from `--collect-only`, 24 ids): exactly 7 red — the 4 legs, the two former #614 ids (now 58's heal-door reason, lead ruling #20016/#20017, reading A), the existing typecheck leg. **Run** (`r51/run_fds.log`, TREE `666d33d4…`, HEAD `9bc5807`): `7 failed, 17 passed in 4.58s` — **declared == observed, both ways**. Right reasons: `door set … is 4, not the 5`; `assert 4 not in [2, 3, 4]` (the heal door after the swallowed backfill); `observed 4` (no apply door); `non-vacuity`; `'TaskLedger' has no attribute '_reanchor_stragglers'`; `2 vs 2`; the mypy leg on `SupersedeResult` (unchanged: standalone mypy over both files shows the same errors as HEAD's copies).
- **Registry:** the packet-58 `scripts/test_forgery_door_sweep.py` entry now lists all 7 (`--verify-registry` EXIT=0, `r51/verify_step2.log`). Receipt of the partition: §R5.1-GATES.

### §R5.1-GATES — final receipts (HEAD `9bc5807`, 2026-11-09; logs under `…/scratchpad/r51/`)
| gate | command | log | EXIT | verdict | TREE= |
|---|---|---|---|---|---|
| scoped pytest partition, sweep file (after Step 2) | `pending_contract_gate.py --currency --legs pytest -- scripts/test_forgery_door_sweep.py` (cgroup-capped, no `-n`) | `scoped-fds-final.log` | 1 | `pytest RED_ADJUDICATED — 7 residual(s), owned by: packet-58-contract`; **no ORPHAN on pytest** (typecheck/ruff NOT_RUN = the `--legs pytest` filter) | `76faefa7…` |
| currency typecheck+ruff | `pending_contract_gate.py --currency --legs typecheck,ruff` | `gate-currency-final.log` | 1 | `typecheck RED_ADJUDICATED — 84`; `ruff GREEN`; **no RED_ORPHANED** (only the leg-filtered pytest NOT_RUN) | `9ddad37a…` |
| registry | `pending_contract_gate.py --verify-registry` | `verify_step2.log` | 0 | clean | — |
| scoped pytest partition, sweep file (Step 1, BEFORE fix(614)) | same as row 1 | `scoped-fds614.log` | 1 | `pytest RED_ORPHANED — 2` = exactly #614's two ids (the mask, watched removed) | `4931a0df…` |

### §R5.1 — commit-ready paths and open items
- **Commit-ready (lead commits):** `scripts/pending_contracts.yaml` (64b-i 315 ids; the #615 pin's entry; the sweep entry's 6 new ids), `scripts/test_pending_contract_gate_f6.py` (#615 pin, inverted control), `scripts/forgery_door_sweep.py` (the straggler world), `scripts/test_forgery_door_sweep.py` (legs i–iv), this report.
- **Open, for the lead:** (1) the #615 SAT trap — `scripts/test_pending_contract_gate.py::test_pytest_failure_inside_a_registered_file_is_expected` relies on the fallback #615 removes; edit outside my grant (exact edit in STEP 3 (c)). (2) My §STATE line above said "finished ~23:15Z"; the clock read 23:03Z at r5.1's start — that line was a mis-stamp (corrected here; the r5 work ended before 23:03Z).
- **Runs used in r5.1:** collect-only ×4 (declarations), plain-HEAD confirming run ×1, scoped gate ×2, #615 RED@HEAD ×1, sweep-file RED@HEAD ×1, currency/registry ×3 (plus one HEAD probe of the two worlds' door sequences, to write the pins against measured shape). Fan-out: haiku runners 7.

### STEP 3 (c) follow-up — the #615 SAT trap, closed (lead grant #20021, 2026-11-09)
- **Edit (option a, the class fix):** `scripts/test_pending_contract_gate.py`'s shared `_REGISTRY_YAML` entry for `_REGISTERED_FILE` gains `red_nodeids: ['<file>::test_pin']` (+ a ⚠ DUAL comment). Nothing else in that file; its CONTROL twin `test_pytest_failure_outside_the_registry_is_unexpected` untouched.
- **Why (a) and not the re-point (b), measured:** I first re-pointed only `test_pytest_failure_inside_a_registered_file_is_expected` (b). The SAT run then showed **two more instances of the same class** — `test_a_deploy_receipt_requires_ALL_THREE_legs` and `test_healthy_run_passes_and_serves_partition_counts` also fail `test_pin` in that symbols-only entry and red on a fallback-removed reference (`UNREGISTERED pytest failure: lorerunes/tests/test_posture.py :: c::test_pin`; `r51/trap_sat.log`, REF `2 failed, 107 passed`). Reverted (b); (a) covers all three. Every gate-using `_REGISTERED_FILE` case fails `test_pin` (listed-and-failing ⇒ owned; no self-destruct); the one `test_a` case is reader-only.
- **Receipts** (`r51/trap_sat.sh` → `r51/trap_sat2.log`, TREE `543be59c…`; declaration `r51/declared_trap.txt` v2, written before the run): **HEAD** `1 failed, 108 passed` — only `test_615_an_entry_with_no_red_nodeids_owns_NO_pytest_red` (still RED at HEAD); **REF** (the one-line reference `file_level = False` in `partition_pytest`, applied to the real file under a `cp -a` backup) `109 passed`, EXIT=0 — the #615 builder's SAT; **restore** `RESTORED byte-exact`, `git diff --stat scripts/pending_contract_gate.py` empty.
- DUAL R5-D10: the shared fixture entry — symbols-only → node-listed + symbols (mixed claim; its typecheck self-destruct unchanged). Spec: #615's closing rule.

### §R5.1 — FULL commit-ready path list (all of r5.1; lead commits with `git commit -- <paths>`)
- `scripts/pending_contracts.yaml` — 64b-i 315 `red_nodeids` (step 3a); the #615 pin's packet-58 entry (3c); the sweep entry's 6 added ids (step 2). (Step 1's 225 ids are already in `3371e3b`.)
- `scripts/test_pending_contract_gate_f6.py` — the #615 pin (inverted control + docstring bullet).
- `scripts/test_pending_contract_gate.py` — the shared fixture entry's `red_nodeids` (trap closed).
- `scripts/forgery_door_sweep.py` — the straggler world (`straggler_task_store`, `_task_store_world`, `_seed_legacy_task(superseded_by=)`).
- `scripts/test_forgery_door_sweep.py` — `TestTheHealDOORSAreOnTheStragglerPath` legs (i)–(iv).
- `REPORT-contract-58-r5.md` — §R5.1 (steps 1–4, gates, DECLINED).
- **Final gate receipt (r5.1, after the trap edit):** `pending_contract_gate.py --currency --legs typecheck,ruff` → `typecheck RED_ADJUDICATED — 84`, `ruff GREEN`, no RED_ORPHANED (`r51/gate-currency-final2.log`, EXIT=1 only for the leg-filtered pytest NOT_RUN); `--verify-registry` EXIT=0 (`r51/gate-verify-final2.log`); both TREE `40dec4c3…`, HEAD `23a54cc`.

### #20022 — the probe's signin, routed through the shared seam (lead, 2026-11-09)
- **The orphan:** `scripts/probe_hub_txn_58.py` (committed in `bed62bd`) hand-rolled `connection.signin({"username": …, "password": …})`, which reds `loremaster/tests/test_secret_typing.py::TestSigninCredentialsIsTheOneUnwrapSeam::test_no_module_outside_the_seam_hand_rolls_the_payload` and no registry entry owned it (my wave introduced it — the verbatim §INSTRUMENT copy).
- **Fix (REUSE, two seams):** the payload is built by `loremaster.store._txn.signin_credentials` (THE one unwrap seam); the credential comes from the suite harness's `_surreal_harness.surreal_user()` / `surreal_password()` (TEST-store origin, env override else the spike default — the probe's own semantic), imported the way `scripts/forgery_door_sweep.py::_harness` does. ⚠ A first attempt minted `SecretStr(os.environ.get(…))` locally and redded the neighbour pin `TestOutgoingAuthHeadersGoThroughATypedSeam::test_secretstr_is_minted_only_where_a_credential_ORIGINATES` (attack shape S6) — replaced by the harness origin; no local mint, no dict literal remains. ⚠ Behaviour note: the env override is now the harness's `LORE_TEST_SURREAL_*` variables (the repo's TEST-store convention), not the probe's former ad-hoc `SURREAL_PASSWORD`.
- **Receipts** (`r51/run_secret.sh` → `r51/run_secret.log`, TREE `85bcfc83…`): `loremaster/tests/test_secret_typing.py` **69 passed**, EXIT=0 (both pins GREEN); the probe `3 1665` → PROBE_EXIT=0, `N=3 … outcome=committed rewired=[3] new_edges=[3] old_edges=[0]` and `N=1665 statements=4999 … outcome=committed rewired=[1665] new_edges=[1665] old_edges=[0]`. ruff + `mypy scripts/probe_hub_txn_58.py` clean. Committed-ready probe md5 `0ff0ca6fba13620cf8e7582eaec5dcb3`.
- **Added to the r5.1 commit-ready list:** `scripts/probe_hub_txn_58.py`.
- **Gate after the probe edit** (`r51/gate-currency-final3.log`, HEAD `c7f8f1d`, TREE `8ef7da2b…`): `typecheck RED_ADJUDICATED — 84`, `ruff GREEN`, no RED_ORPHANED (EXIT=1 only for the leg-filtered pytest NOT_RUN).
- **State at HEAD `c7f8f1d`:** r5.1 steps 1–4 + the trap edit are committed (`3371e3b`, `805a687`); `fix(615)` landed (`c7f8f1d`, pin GREEN, its entry deleted). **Remaining commit-ready:** `scripts/probe_hub_txn_58.py` (md5 `0ff0ca6f…`) and this report.

### #20024 — the F6 module's prose, after `fix(615)` (2026-11-09)
- `scripts/test_pending_contract_gate_f6.py`, prose only (the diff touches no `assert` line): the header bullet now states the per-node rule as fixed by `c7f8f1d`; the fixture's `packet-58-contract` rationale reads "a symbols-only entry: it owns its mypy claim, and (#615) NO pytest red" (was "file-level owner of its pytest reds today"); the #615 pin's docstring drops "CONTRACT-AHEAD — RED until a builder …" for "fixed by `c7f8f1d` … this pin keeps it gone" (its DUAL note kept). Left as-is, still accurate: L7 (F6's general contract-ahead rationale) and the MP-F6-3 comment (it names the `f6_mixed_file_level` wrong build).
- **Receipt** (`r51/run_gate_tests.sh` → `r51/run_gate_tests.log`, HEAD `5ff9209`, TREE `d83c6fe1…`): `scripts/test_pending_contract_gate.py` + `…_f6.py` **109 passed**, EXIT=0.
- **Commit-ready:** `scripts/test_pending_contract_gate_f6.py` (+ `scripts/probe_hub_txn_58.py` from #20022 if not yet committed, + this report).
