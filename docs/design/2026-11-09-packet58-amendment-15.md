# Packet 58 — Amendment 15: the SDK3 re-base — the hub cap, the heal packer and the size WARN re-keyed to ROWS; 58's four classes on the typed classifier; r5 takes ONE delta grade

brief-base v27 read · brief project v7 read

**Author:** sidecar-58-1 (Fable design sidecar, fork ruler for packet 58) · **Date:** 2026-11-09 · HEAD `99044d0`
**Authority:** operator grant 2026-11-09 (verbatim, via lead-58): *"Work autonomously and do not pause for contract
approval. Forks and design questions go to the side car."* These rulings bind this session; the operator may overturn.
**Amends:** kickoff §1 (F-1's cap definition and rider iv), am-2 §(b) (WARN prose), am-3 §1 and §3 (the ONE counter;
the claim-loss classifier form), am-8 §1–§2 (the packer's `max_size` / `get_len`), am-12 §3 (the no-grade ruling, for
r5 only). **Does not amend:** am-12 §1 (`statements_after == 0`), am-13, am-14.
**Answers:** lead-58's Question 1 (a)–(e) and contract-58-r5's forks F-RB-1…4 (`REPORT-contract-58-r5.md` §INVENTORY,
read at its 2026-11-09 16:39 local state; lore_comms #20000, thread `q:58-sdk3-rebase`).

## SUMMARY BLOCK
- **State:** done.
- **Deviations:** one — I ran a store probe (TEST store `:18000` only, throwaway DBs, removed) because ruling (a)
  rested on a timing claim nobody had measured. Instrument pasted verbatim in §INSTRUMENT.
- **Packages considered:** `more_itertools.constrained_batches` — KEEP (am-8's verdict, read from the installed
  source by adversary-58-r2); only its `max_size`/`get_len` arguments change. `loremaster.store._txn.fragment_rows`
  (read at `99044d0`) — REUSE as the one counter; 58's private counter is never built.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 0 new symbols; 1 retired before it was built (`TaskLedger._composed_statement_count` →
  `_txn.fragment_rows`).
- **Graded:** n/a — a ruling, not a verdict on someone's artifact. Facts read at HEAD `99044d0`.
- **Decisions needed (operator may overturn, none blocks):** (1) §1.3's accepted bound: between roughly 12,000 and
  16,665 dependents a supersede times out instead of being refused; (2) §5: r5 takes one adversary delta grade.
- **Receipt pointers:** §0 rulings · §1 hub cap + probe table · §2 packer · §3 keep/re-key/retire table · §4 63c-i-a
  and SDK3 facts · §5 adversary scope · §6 the r5 FOLD LIST · §INSTRUMENT.

Fallbacks said out loud (brief-base §4): `grep` over the tree for the retired names `TXN_STATEMENT_*` (rename
exhaustiveness — the sanctioned case) and over `docs/` for ruling ids (non-symbol prose). `_txn.py` was read with
Read; no lore tool missed, so no friction finding.

## 0. The rulings in one screen

| # | question | ruling |
|---|---|---|
| **(a)** | F-1 hub cap | **Refuse-and-teach stays.** The cap is `max_reanchor_dependents(K)` = the largest N for which `_txn.fragment_rows(<the fragments this supersede builds>) <= _txn.TXN_ROW_HARD_CAP`, both read live. A ROW here is `fragment_rows`'s count: 58's fragments declare no `rows=`, so each statement counts one. Pinned at cap−1 / cap / cap+1 under a SHRUNK monkeypatched cap, plus real-cap legs that kill a surviving statement cap. One stated bound: a supersede near the real cap times out before it is refused (§1.3, measured). |
| **(b)** | heal packer | `constrained_batches(items, max_size=_txn.TXN_ROW_HARD_CAP (read at call time), get_len=<stored weight>, strict=True)`, weight = `fragment_rows(<that row's fragments>)`. am-3's one-counter rule holds and gets simpler: the counter is `_txn.fragment_rows`, the function `compose` itself calls. |
| **(c)** | every other statement-count fact | 14 rows in §3: 9 re-keyed, 4 kept, 1 retired. `statements_after == 0` is KEPT unchanged (it counts statements SENT after exhaustion, not transaction size). |
| **(d)** | 63c-i-a / SDK3 facts that are design questions | F-RB-1: 58's four classes use the landed TYPED idiom (THROWN kind + prefix anchored at the engine's THROW wrapping), built through the one mapping helper. 63c's closed exact-set pins that must grow for 58's classes are r5's to edit, as DUAL rows. Three build requirements are confirmed still owed at HEAD (§4.3). |
| **(e)** | adversary | **ONE delta grade of r5, scoped (§5).** am-12 §3's no-grade ruling does not carry to r5: its two premises (no new property; the audit's instruments apply) are both false on this base. After it, the cap is closed again. |
| F-RB-2 | the one counter | (i). A private `len(statements)` counter is indistinguishable by behaviour on un-annotated fragments, so sharing is proven by MUTATION at the cold audit, as a named bound (§2). |
| F-RB-3 | the size WARN | (i): cross a shrunk `TXN_ROW_WARN_THRESHOLD`, assert on `row_count`. |
| F-RB-4 | one cap governs both | Confirmed: the shrunk cap also shrinks `compose`'s own refusal; that is intended for the accessor and the packer alike. |

**Where I chose between readings (brief-base §2):**
1. *F12: "packet 58's packer … re-size by rows"* — reading A: keep 58's fragments un-annotated (one row per
   statement); reading B: annotate the shared `DELETE blocks WHERE in = $old` with `rows = N` because it removes N
   edges. I pick **A**. Counted un-annotated, a supersede is `4 + K + 3N`; its true row writes are `2 + K + 3N`
   (the N guard statements write nothing, the one DELETE removes N edges — they cancel to within 2). Reading B
   counts `3 + K + 4N`, which is further from the truth, and opens a `rows=` under-declaration family for no gain.
2. *Repo law "no contract revision skips the adversary" vs am-12 §3 "r4 needs no delta grade"* — reading A: r5 is
   a fold like r4, ungraded; reading B: r5 is graded. I pick **B**, scoped (§5).

## 1. (a) The hub cap

### 1.1 What a ROW is in a supersede + re-anchor transaction (derived from the code at `99044d0`)
- `_txn.fragment_rows(fragments)` returns, per fragment, `fragment.rows` when declared, else
  `len(fragment.statements)`. `compose` refuses when that sum exceeds `_txn.TXN_ROW_HARD_CAP` (50,000, read from
  the module global at call time) with `TxnRowCapExceededError`, before anything is sent.
- `TaskLedger._apply` composes the ledger's fragments as they are; `_relate_fragment` emits one `RELATE` statement
  per pair and declares no `rows`. Nothing in `tasks.py` declares `rows=` (sweep at `99044d0`: 0 hits).
- So for 58 a row is **one composed statement**: the guarded `LET … UPDATE`, its `IF … THROW`, the `CREATE`, the
  one shared `DELETE`, and each `RELATE` count one each. The arithmetic `cap = (CAP − fixed(K)) // per` keeps its
  form; the constant becomes `TXN_ROW_HARD_CAP` and the counter becomes `fragment_rows`.
- **Scope diff (Leg 1), stated once:** the count is `fragment_rows`'s one-per-statement fallback, not an engine
  row-write count. It over-counts the true writes by 2 at every N (§0 reading 1). The refusal and the accessor name
  "rows" in `compose`'s sense.

### 1.2 The definition and the shape
- `TaskLedger.max_reanchor_dependents(successor_blocked_by_count)` BUILDS the fixed part for that K and one
  dependent's fragments, prices both with `_txn.fragment_rows`, and returns
  `(_txn.TXN_ROW_HARD_CAP − fixed) // per`. No literal, no copied constant, no private counter (F21).
- **Refuse-and-teach is still the shape** (kickoff §1's reasons are unchanged: a batched supersede can strand,
  and `compose`'s bare error is not actionable). Above the cap the ledger refuses before any write, with its own
  teaching error — never `TxnRowCapExceededError` reaching the caller.
- **The refusal names only derived facts:** N dependents, the rows this supersede would compose, the row cap, and
  the cap in dependents as *the build-time row bound*. It does not say a smaller supersede succeeds (§1.3).
- **Rider — and pin it like this:** under `monkeypatch.setattr(_txn, "TXN_ROW_HARD_CAP", shrunk)` (F19, F21) with
  `shrunk` GENERATED from the builder's own measured `fixed(K)` and `per` as `fixed(K) + per·4 + r` for every
  `r ∈ range(per)` (all residues, so no arithmetic alignment) and K ∈ am-3 §1 (iv)'s set: cap−1 succeeds with every
  dependent re-anchored; cap succeeds; cap+1 is refused byte-inert (`SELECT *` before == after: X unstamped, no
  successor, rows and edges unchanged) with the ledger's teaching error; the row count the refusal serves ==
  `fragment_rows` of the fragments it built.

### 1.3 The stated bound: near the real cap, a supersede times out before it is refused
The statement cap (5,000) bounded a hub at 1,665 dependents. The row cap bounds it at 16,665, and a transaction
that size does not fit the 30 s request timeout (`SURREAL_REQUEST_TIMEOUT_SECONDS`; `TaskLedger._apply` carries
no long-operation override).

Measured 2026-11-09 at `99044d0`, SDK 3.0.0 + engine 3.3.5, TEST store, the kickoff §1 statement shape
(§INSTRUMENT; `task` SCHEMALESS and un-indexed there, so these are LOWER bounds on the real schema's cost):

| dependents | statements | wall-clock | outcome |
|---|---|---|---|
| 1,665 (the old cap) | 4,999 | 1.24 s | committed |
| 3,332 (crosses the 10,000-row WARN) | 10,000 | 3.44 s | committed |
| 8,000 | 24,004 | 12.63 s | committed |
| 16,665 (the row-derived cap) | 49,999 | 53.68 s | committed (timeout raised to 900 s) |
| 16,665 under the 30 s timeout, streaming ON | 49,999 | 30.16 s | `TransportTimeoutError`; after a 75 s settle: X unstamped, 0 rows rewired, 0 new edges, all 16,665 old edges present |
| 1,665 under the 30 s timeout (control) | 4,999 | 1.46 s | committed, all rewired |

- **What the consumer gets in the band** (interpolated from the table at roughly 12,000 dependents upward; NOT
  measured on the real schema, where it starts lower): `SurrealOutcomeUnknownError` — loud, and nothing commits
  (measured above for this shape; R7 measured the same for the factory's streaming setting).
- **Ruling: ACCEPT as a named bound.** Not closed, because every closing move is worse: a second, lower hub
  constant is the "statement cap kept somewhere" F12 forbids and a number nobody derived; a long-operation override
  cannot help a served verb past the ~60 s MCP ceiling; collapsing the per-dependent statements into set
  statements re-opens the shell contract four rounds graded. Production holds 116 task rows (am-2).
- **Re-open trigger, with the instrument that measures it (same bullet):** the house size WARN
  (`store.apply.large_transaction`, `row_count > 10,000` ≈ 3,332 dependents ≈ 3.4 s) emitted from the task ledger.
  It fires an order of magnitude in time before the band. The first such record from a supersede re-opens this
  bound. That is why §3 row 5 KEEPS the WARN on the task path.
- **Rider — and pin it like this:** (i) the bound, its trigger and the probe's path are stated in
  `max_reanchor_dependents`'s docstring (BUILDER CONSTRAINT; the cold audit reads it); (ii) the probe is committed
  as `scripts/probe_hub_txn_58.py` (§6 item 9) so the table above can be re-run; (iii) no huge-fixture pin (F19
  forbids it) — the timing is a measured receipt, not a standing test.
- The boot heal is not in this band: `TaskLedger.ensure_ready` is decorated `ensure_ready_operation` (300 s), and
  a full 50,000-row chunk measured 53.7 s on the lower bound.

### 1.4 What wrong build passes a shrunk-cap-only contract? (the pins F19 alone does not give)
A build that keeps a private 5,000 bound beside the row bound (`min(old, new)`) passes every shrunk-cap pin,
because every shrunk cap is below 5,000. **Riders — and pin them like this:**
- **L1 (no store):** at the UNPATCHED cap, `max_reanchor_dependents(K) == (_txn.TXN_ROW_HARD_CAP − fixed(K)) // per`
  for K ∈ {0, 2}, with `fixed`/`per` measured from the builder's fragments via `fragment_rows`.
- **L2:** at the unpatched cap, ONE supersede whose composed statements exceed the retired 5,000 (N = 1,666 at
  K = 0; about 1.5 s) SUCCEEDS with every dependent re-anchored. The 5,000 is one named constant citing F12 —
  `test_sdk3_row_bound`'s `_RETIRED_STATEMENT_CAP`, imported if importable, never a second literal.
- **L3:** at the unpatched cap, a straggler population whose total rows exceed 5,000 heals in ONE transaction.
- **L4 (live read):** shrink the cap by `per·d` → the accessor drops by exactly `d` (A-6's existing leg, re-keyed).

## 2. (b) The boot heal packer

- **Ruled shape (am-8 §1 with two arguments changed):** items are `(row, fragments, weight)` built once per
  straggler; `weight = _txn.fragment_rows(fragments)`; `constrained_batches(items, max_size=_txn.TXN_ROW_HARD_CAP,
  get_len=<the stored weight>, strict=True)`; the cap is read when the heal runs, never at import. `strict=True`'s
  `ValueError` still becomes `StragglerHealPackerError` at the one call site.
- **am-3 §1's one-counter rule: HOLDS, and the counter changes owner.** The supersede accessor, the heal packer
  and `compose`'s refusal all price with `_txn.fragment_rows`. `TaskLedger._composed_statement_count` (named in
  am-3/am-8, present only in the reference chain) is never built: it would be copy #2 of `fragment_rows`.
- **F-RB-2's bound, accepted and named:** 58 emits no annotated fragment, so a private `len(statements)` counter
  returns the same number as `fragment_rows` on every input 58 produces; no behaviour pin can tell them apart, and
  a pin on the import or call spelling is a banned source check. **Rider — the sharing proof is a cold-audit
  MUTATION run** (edit `fragment_rows`' body in the source, e.g. double the un-annotated count → the accessor, the
  packer's chunk boundary and `compose`'s refusal all move; a consumer that stays put is a private copy).
  Re-open trigger: the first 58-path fragment that declares `rows=`.
- **Rider — 58's fragments stay un-annotated, and pin it like this:** at the `compose` spy, for every transaction
  the supersede and the heal send, `fragment_rows(fragments) == sum(len(f.statements) for f in fragments)`. A
  fragment that under-declares `rows=` to slip the bound reds here.
- **The convergence property (am-8 §2) is unchanged:** one boot heals every resolvable straggler, and every sent
  transaction's `fragment_rows` is ≤ the cap. Its generated sweep now runs under a shrunk cap, so `fit` is a few
  rows and `SCALES = {fit−1, fit, fit+1, 2·fit+1}` are small fixtures (F19). The spy measures at `compose` (it sees
  fragments), never by counting statements in the sent text.
- **The single over-weight row (am-8 F10):** re-keyed to the shrunk cap — one row naming more superseded blockers
  than the shrunk cap admits → `StragglerHealPackerError` names the row and its weight, the boot fails loud.

## 3. (c) Every r1–r4 fact that rested on statement counts — keep / re-key / retire

Cross-checked against `REPORT-contract-58-r5.md` §INVENTORY (A-1…A-8, B-1…B-5, C none, D-1…D-8): its rows map onto
rows 1–9 and 13–14 below; it found nothing I had not listed, and I add rows 10–12.

| # | fact (where) | verdict | ruling + rider |
|---|---|---|---|
| 1 | F-1 derived cap (kickoff §1; A-5, A-6, D-2) | RE-KEY | §1.2 + §1.4 |
| 2 | "the count the refusal serves == `compose`'s count" (kickoff §1 rider iii) | RE-KEY | both sides are `fragment_rows` over the same fragments |
| 3 | per-dependent mutation moves the cap (kickoff §1 rider ii; am-2 mutation) | KEEP | unchanged in form; the cap moves because `fragment_rows` sees the added statement |
| 4 | accessor at K ∈ {0,1,2,3,per,per+1}; PR16's K-blind build (am-3 §1 iv) | RE-KEY | same K set, shrunk cap |
| 5 | the size WARN at 800 statements (kickoff §1 rider iv; am-2 §(b); A-4, A-5, D-3) | RE-KEY | R9 D2: a row warn. `TaskLedger._apply` logs through the ONE house function (`SurrealStore._log_transaction_size`, r1's own ruled shape, D-3) — no second comparison. Pin under a shrunk `TXN_ROW_WARN_THRESHOLD` generated as `fixed + per·2`: N = 3 dependents → exactly ONE WARNING with `row_count > threshold`, supersede succeeds; N = 2 (rows == threshold) → zero WARNINGs. Sharing: cold-audit mutation of the one comparison reds this pin AND `test_sdk3_row_bound`'s warn pin. It is also §1.3's trigger instrument. |
| 6 | heal `max_size` / `get_len` (am-3 §1, am-8 §1; A-1, B-3, B-4, D-6) | RE-KEY | §2 |
| 7 | the ONE counter `_composed_statement_count` (am-3 §1; B-2, D-4) | RETIRE | → `_txn.fragment_rows` (§2) |
| 8 | "every sent transaction ≤ cap" spies (A-2, A-7) | RE-KEY | `fragment_rows` at the `compose` spy, shrunk cap |
| 9 | convergence SCALES and `2·fit+1` (am-8 §2, am-12 F-E; A-3, D-7) | RE-KEY | `fit` measured under the shrunk cap; form unchanged |
| 10 | the over-weight single row, "1700 blockers" (am-8 F10) | RE-KEY | §2 last bullet |
| 11 | `statements_after == 0` (am-12 §1) | KEEP | counts statements the seam receives after exhaustion; no cap is involved. Unaffected by F12. |
| 12 | measured WRITES(R, v) and the heal's n ≥ 2 (am-12 §1) | KEEP | n counts transactions sent; the `2·fit+1` population still spans ≥ 2 chunks under the shrunk cap — the leg asserts n ≥ 2 as before |
| 13 | prose: "AM2C fits 4999 statements in one chunk", "116 × 3 = 348 under the 800 WARN", `cap_dependents(K) = (TXN_STATEMENT_HARD_CAP − (4+K)) // 3 ≈ 1665` (D-1, D-5, D-8; packet doc lines 35–36, 49–52, 72–74) | KEEP as history | dated rulings are not rewritten; this amendment supersedes them. The packet doc is outside my writable set — FLAG for the lead: its three cap sentences name deleted constants. |
| 14 | `test_exhaustion_fates.py`'s row-cap known-bound pin (A-8; R36 fork 2, `da24469`) | KEEP | already re-keyed by SDK3's servicer; r5 verifies it GREEN on its reference |

## 4. (d) What 63c-i-a's build (`34d0b6b`) and SDK3 changed — only the design questions

### 4.1 F-RB-1 — the classifier form for 58's four classes: reading (i)
`TxnClaimLostError`, `TxnCasLostError`, `TxnReanchorStragglerError`, `TxnHealChunkError` are classified the way
`_classify_engine_error` classifies the governed conflict at HEAD: `(untyped or kind == ErrorKind.THROWN)` AND the
lowered text STARTS WITH `_ENGINE_THROW_PREFIX + <marker>`. The substring form (`marker in lowered`) is forbidden
by 63c-i-a's landed decision (amendments 35 §2 / 36 §1.1) and is what kept am-13's 36 REF-ONLY reds.
- Each class subclasses `TxnDomainRejectionError`, carries `error_class` and `kind`, and names its own label via
  `_constructed_error_class` (am-37 §15.2). Each is built by `_domain_rejection_error` — the ONE mapping helper,
  extended, never a second `if label ==` at a raise site.
- Consequence, checked: a recognised label makes `proven_no_key` TRUE for these classes. Correct — a THROW rolled
  the transaction back. `_PROVEN_NO_KEY_CLASSES` is not edited.
- am-3 §3's rule stands: the ledger catches the TYPE, never the text; markers live once in `_txn`.
- **Rider — and pin it like this:** 63c-i-a's echoed-phrase sweep (`TestTheClassIgnoresEveryEchoedPhrase63cIAa28c`)
  runs over 58's four markers too and is GREEN on the reference: a marker echoed inside a non-THROW error, or
  anywhere but the anchored start, classifies `unspecified rejection`. Positive control: the real THROW classifies.

### 4.2 Who edits 63c's closed pins when 58 legitimately grows a set they pin
63c-i-a is landed and closed; its tests are now ordinary suite tests. Where one pins an EXACT set that 58's build
must grow (the `_txn` class lists, e.g. the hand-list in `test_am37_13_3_63c_i_a.py`; the marker domain above), the
member addition is **r5's edit, recorded as a DUAL row** naming the member, the ruling that admits it, and the test
id. A builder never edits them. If such a pin's set is hand-listed where it could be derived, r5 says so in its
report; converting it is not 58's work.

### 4.3 Three 58 build requirements re-measured at `99044d0` — all still owed
- **am-13 §1 (F-8):** `execute_transaction`'s `retry_on_conflict(_attempt, deadline_seconds=…)` still passes no
  `label=` / `url=`. Owed. The requirement is restated against the tenacity-backed driver (R11/F22): same property.
- **am-12 §2 / BC-r4-2 (lease `error_class`):** `store/lease.py` has 0 occurrences of `error_class`. Owed.
- **BC-r4-1 (`more-itertools` declared):** absent from both `pyproject.toml` files. Owed. (`pytest-timeout` is
  now declared.)

### 4.4 Re-derivations that are NOT design questions (r5 re-derives from HEAD, never from a report)
`FAULT_CLASS_NAMES` / `translate_targets()` (SDK3 added `SurrealOutcomeUnknownError`, a `SurrealConnectionError`
subclass: under am-3 §2 a heal door that meets it RAISES — it falls out of the existing fault-class rule);
the catch-site census and its non-vacuity floor (re-baselined 51 → 42 by R36's route); `UNLOGGED_SITES` after
SDK3 retired the 18 `_safe_close` wrappers (the classifier already reds an entry whose site is no longer a hole);
anchors A2 and A5 (constructor and raise-site reshape — mechanical).

## 5. (e) r5 takes ONE delta grade — and how that squares with am-12 §3

- **The two laws.** Repo CLAUDE.md (2026-07-28): contract → adversary → build; no revision skips the adversary.
  Global rule 3 and am-12 §3: after the initial grade and one re-grade, only a NEW property reopens the loop; r4
  was a fold with no grade.
- **They conflict only if "round" means "revision".** The cap bounds re-grading the SAME properties against the
  SAME world. am-12 §3 rested on two premises, both true for r4 and both false for r5:
  1. *"NEW PROPERTY = 0."* r5 pins properties no adversary has seen: no statement bound survives beside the row
     bound (§1.4), fragments stay un-annotated (§2), the WARN is the row warn through one function (§3 row 5), and
     58's four classes are recognised by a different mechanism than the one r1–r3 graded (§4.1).
  2. *"The cold audit runs the adversary's seven W-\* builds as its mutation set."* Those builds and the reference
     chain are anchored to the September tree. Measured by contract-58-r5 at `99044d0`: the chain fails to apply
     (5 anchor misses) and, where it applies, raises `AttributeError` on the deleted constant. An audit holding
     instruments that do not apply has no mutation set.
- **Scope of the delta grade (one `contract-adversary` run, Opus):**
  1. build its OWN reference on HEAD and produce the SAT receipt for the WHOLE r5 contract over the targeted set
     (every earlier SAT receipt is about a tree whose `_txn` has since been rewritten);
  2. wrong builds against the DELTA only: a surviving statement bound (`min(5000-derived, row-derived)`); a
     literal cap; a cap read at import; a `rows=` under-declaration; a private warn comparison; a substring
     classifier for any of the four markers; a refusal after the stamp at cap+1; a packer pricing rows at one unit;
  3. re-anchor its seven W-\* builds and kill probes onto that reference, RUN them against r5's pins, and paste the
     re-anchored instruments verbatim — they are the cold audit's mutation set (am-12 §3), and porting them is
     cheapest where the reference already exists;
  4. P1b/P1c tables for the NEW pins only. It does not re-attack the graded CAS-population, fates or tier
     properties beyond item 3's runs.
- **Loop cap, stated now:** this is the one grade. Its findings come to me for bucketing (rule 5). A NEW PROPERTY
  reopens; a pinned-property new case is an ungraded r6 fold; a W-\* survivor is a STOP naming the pin. After r6
  the next instrument is the build's cold audit. Cost so far on 58: 3 adversary runs + 4 author runs; this adds
  one of each.
- **What r5's author does meanwhile:** its provisional reference is a legitimate SAT host (a correct build is not
  a wrong build; r3/r4 precedent). It does not replay or re-anchor the adversary's W-\* builds (role boundary).

## 6. The r5 FOLD LIST (contract-58-r5 executes; every item carries its pin rider)

1. **Hub cap, shrunk.** Re-key the F-1 trio to `_txn.TXN_ROW_HARD_CAP`, monkeypatched. *Pin it like this:* shrunk
   caps generated as `fixed(K) + per·4 + r ∀ r ∈ range(per)`, K ∈ {0,1,2,3,per,per+1}; cap−1 / cap succeed fully,
   cap+1 refused byte-inert with the ledger's teaching error (not `TxnRowCapExceededError`); served row count ==
   `fragment_rows` of the built fragments (§1.2).
2. **Hub cap, real.** Add L1–L4 (§1.4). *Pin it like this:* L1 arithmetic at the unpatched cap for K ∈ {0, 2};
   L2 one 1,666-dependent supersede succeeds at the unpatched cap; L3 a >5,000-row straggler population heals in
   one transaction; L4 shrinking the cap by `per·d` drops the accessor by `d`. One retired-cap constant, cited.
3. **Un-annotated fragments.** *Pin it like this:* at the `compose` spy, every transaction the supersede and the
   heal send satisfies `fragment_rows(fragments) == Σ len(statements)` (§2).
4. **Heal packer.** Re-key A-1/A-2/A-3/A-7 and the over-weight row to rows under a shrunk cap. *Pin it like this:*
   the spy prices with `fragment_rows` at `compose`; every chunk ≤ the cap; `SCALES` from the measured `fit`;
   `count == |healable|` in one boot; the over-weight row raises `StragglerHealPackerError` naming row and weight;
   the `2·fit+1` leg still asserts n ≥ 2 transactions (§2, §3 rows 8–10, 12).
5. **Size WARN.** Re-key to `TXN_ROW_WARN_THRESHOLD`, shrunk to `fixed + per·2`. *Pin it like this:* N = 3 → exactly
   one WARNING with `row_count > threshold` and the supersede succeeds; N = 2 → zero WARNINGs; assert on
   `row_count`, not `statement_count` (§3 row 5).
6. **The four classes.** Re-key every pin and the reference to the typed, anchored-prefix classifier and the
   `error_class=` / `kind=` constructors. *Pin it like this:* 63c's echoed-phrase sweep covers the four markers and
   is GREEN on the reference, with the real THROW as positive control; each class is built by
   `_domain_rejection_error`; `proven_no_key` is TRUE for each (§4.1).
7. **63c exact-set pins.** Add 58's members where a landed pin's exact set must grow. *Pin it like this:* one DUAL
   row per member (member · admitting ruling · test id) in the r5 report; no other edit to those files (§4.2).
8. **Registry.** Remove the bare `TXN_STATEMENT_HARD_CAP` / `TXN_STATEMENT_WARN_THRESHOLD` `missing_symbols` from
   the five `packet-58-contract` entries in the same change that removes the reads, and drop the D′ sentence from
   the rationale. *Pin it like this:* `--verify-registry` OK and `--currency --legs typecheck,ruff` at
   RED_ORPHANED 0; a retired-name sweep (bare pattern `STATEMENT_HARD_CAP|STATEMENT_WARN`) over the 58 test files
   with every residual hit listed file:line with its own verdict.
9. **Commit the probe** as `scripts/probe_hub_txn_58.py` from §INSTRUMENT, byte-exact. *Pin it like this:* run it
   once with `3 1665` and paste the two output lines (both `outcome=committed`, `old_edges=[0]`) as the receipt
   that the committed copy runs.
10. **BUILDER CONSTRAINTS (r5 adds; r1–r4's stand unless §3 re-keys them):**
    (a) the accessor, the packer and the refusal price with `_txn.fragment_rows` and read `_txn.TXN_ROW_HARD_CAP`
    live — no private counter, no copied constant (cold-audit mutation: §2);
    (b) `TaskLedger._apply` logs its size through the one house function (cold-audit mutation: §3 row 5);
    (c) `max_reanchor_dependents`'s docstring states §1.3's bound, its WARN trigger and the probe's path;
    (d) the refusal text names N, rows needed, the row cap and the cap in dependents, and promises nothing about
    smaller supersedes;
    (e) still owed, re-measured at `99044d0`: am-13 §1 (F-8 label/url + typed carrier), the lease `error_class`
    rider, `more-itertools` declared (§4.3).
11. **Cold-audit set (r5's report lists it for the audit brief):** the adversary's re-anchored W-\* builds (§5
    item 3); the two sharing mutations (10a, 10b); the docstring read (10c); the real-population heal receipt
    (am-2) plus, new, the largest hub in that dump (`max` of `blocks` edges per `in`) pasted beside it — the
    first measurement of how far the fleet sits from §1.3's WARN trigger.
12. **§HELD and the reference.** Re-derive the reference on HEAD with items 1–6 (anchors A1–A5 per §4.1/§4.4);
    §HELD parts 1/3 already apply at `99044d0` (r5 §RE-BASE-STEP1). *Pin it like this:* the SAT receipt is 0
    attributable reds over the declared targeted set, with `loremaster.__file__` printed in the log header; the
    adversary's own reference (§5 item 1) is the second, independent SAT.

## 7. Surfaced, not ruled
- **For the lead:** `docs/plans/v2/58-supersede-reanchor.md` lines 35–36, 49–52 and 72–74 name the deleted
  constants and the 800/5000 numbers. It is the packet file, outside my writable set. Do you want it annotated to
  point here?
- **For the operator (via the lead):** §1.3's accepted bound and §5's one extra adversary run are the two calls
  made under the grant that cost something. Either can be overturned without touching the other.
- No production code, test, registry or store schema touched. The probe wrote only throwaway databases under
  `lore_test` on `:18000` and removed each. No attribution trailer on the commit.

## 8. Addendum (same day): contract-58-r5's A-9, A-10, A-11 and F-RB-5 (lore_comms #20001)

Rules the four items in `REPORT-contract-58-r5.md` §INVENTORY's addendum. **§8.1 SUPERSEDES the shrunk-cap VALUES
in §1.2, §3 row 5 and §6 items 1 and 5** (my generated `fixed(K) + per·4 + r` and `fixed + per·2`). Everything
else in those items stands, and §1.4's real-cap legs become load-bearing rather than supplementary.

### 8.1 F-RB-5 — ACCEPTED: one support fixture shrinks the bounds to the scales r1–r4 were graded at
- **Ruling.** ONE fixture in `_reanchor_58_support.py` monkeypatches `_txn.TXN_ROW_HARD_CAP` to 5,000 and
  `_txn.TXN_ROW_WARN_THRESHOLD` to 800, each a named constant citing F19/F21. 58's fragments are un-annotated, so
  rows == statements and every r1–r4 fixture keeps the scale and the discriminator it was graded with (AM2C's
  4,999-row single chunk, PR16's K-blind accessor, PR18/PR19's multi-blocker population, the 1,700-blocker row).
- **Why this beats my generated tiny caps.** Mine would have re-sized every graded fixture — new, ungraded
  arithmetic on three rounds of adversary-verified pins. F19 asks for a shrunk monkeypatched cap, not a minimal
  one; 5,000 is shrunk. The alignment worry I gave for generating residues is already met by the graded K set:
  `(5000 − (4 + K)) mod 3` is 1, 0, 2 for K = 0, 1, 2.
- **What wrong build passes this?** One that never left the statement cap: a literal 5,000, or
  `min(5000-derived, row-derived)`. At a 5,000 shrink it is indistinguishable everywhere. **Rider — so §1.4's
  L1–L3 are REQUIRED and run WITHOUT the fixture** (the unpatched 50,000): L1 the accessor's arithmetic, L2 a
  1,666-dependent supersede succeeds, L3 a >5,000-row straggler population heals in one transaction. L4 (shrink
  again by `per·d` from inside the fixture → the accessor drops by `d`) kills the literal from the other side.
- **Rider — and pin the fixture like this:** it is requested explicitly by each leg, never autouse; the L-legs
  assert `_txn.TXN_ROW_HARD_CAP` is the unpatched value before they run (a leg that silently inherited the shrink
  would pass for the fixture's reason); an import-time copy of either constant in the build reds the cap+1
  refusal and the WARN crossing, because the patch lands after import.
- **WARN boundary under 800:** the crossing N is computed as today from the builder's measured `fixed`/`per`;
  the zero-WARNING control is N = crossing − 1 (rows == threshold is not reachable at every K, so the control is
  "one dependent fewer", not "exactly at").

### 8.2 A-9 — the hub refusal's negative check: by TYPE, with a control
The check that the caller never sees `compose`'s bare refusal keyed on retired message text ("statements,
exceeding the hard cap"), so it can no longer fail. **Re-key to the type, and pin it like this:** at cap+1 the
raised error is the ledger's teaching error, `not isinstance(error, TxnRowCapExceededError)`, and neither is its
`__cause__`; positive control in the same leg — composing the fragments the ledger built for cap+1 directly
raises `TxnRowCapExceededError`, so the negative half is shown able to fire. No assertion on message text.

### 8.3 A-10 — PR13's private-warn kill leg: re-keyed by §8.1
At ~900 rows against the real 10,000 threshold the leg cannot cross and kills nothing. Under the fixture's 800 it
crosses as graded: a build with its own comparison (a private 800, a private 10,000, an import-time copy) emits
no WARNING or the wrong one and reds. No further ruling.

### 8.4 A-11 — PR14 monkeypatches the deleted constant: re-key to `TXN_ROW_HARD_CAP`
It becomes §1.4's L4. Same assertion, the live constant's name.

### 8.5 Fold-list deltas (amending §6)
- **Item 1** — shrunk cap = the §8.1 fixture's 5,000 (not generated values); K set and the three-point assertions
  unchanged; the negative check per §8.2.
- **Item 2** — L1–L3 run without the fixture and assert the unpatched cap first; L4 = A-11.
- **Item 5** — shrunk warn = the fixture's 800; control = crossing − 1.
- **New item 13** — the ONE fixture (§8.1), with its two riders (explicit request; L-legs assert unpatched).

## §INSTRUMENT — `probe_hub_txn_58.py`, pasted verbatim (run 2026-11-09 from the repo root with `uv run python`)

Runs: `… probe_hub_txn_58.py 3 1665 3332`, `… 8000 16665`, `PROBE_TXN_TIMEOUT=30 PROBE_SETTLE=75 … 16665`,
`PROBE_TXN_TIMEOUT=30 PROBE_SETTLE=1 … 1665`. Side receipt: the `array::map` closure with `IF … THEN … ELSE … END`
(kickoff §1's unprobed spelling) parses and rewrites correctly on 3.3.5 — every run's `rewired` equals N.

```python
"""Probe (sidecar-58-1, 2026-11-09): wall-clock of ONE supersede-shaped transaction at hub scale.

Question: under the ROW bound (TXN_ROW_HARD_CAP = 50_000, one row per un-annotated statement), a hub
supersede composes fixed + 3N statements. Does a cap-sized one finish inside the 30 s request timeout?

Shape (kickoff rulings §1): stamp shell (2) + CREATE successor (1) + DELETE blocks WHERE in = $old (1)
+ per dependent: guarded UPDATE in a LET (1) + IF .. THROW (1) + RELATE (1).
Store: the TEST store ws://127.0.0.1:18000 only; one throwaway database under lore_test, removed after.
Approximation, stated: `task` here is SCHEMALESS with no indexes (the real table is schemafull with
ASSERTs and indexes), so these timings are a LOWER bound on the real cost.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid

from surrealdb import AsyncSurreal, RecordID

URL = "ws://127.0.0.1:18000/rpc"
NAMESPACE = "lore_test"
SEED_BATCH = 2000
REQUEST_TIMEOUT_SECONDS = 900.0
#: PROBE_TXN_TIMEOUT=<seconds> runs the timed transaction under that request timeout (streaming ON, as
#: lore's shared factory sets it) and then re-reads the store after PROBE_SETTLE seconds on the same
#: connection: did a timed-out supersede commit anything?
TXN_TIMEOUT_SECONDS = float(os.environ.get("PROBE_TXN_TIMEOUT", "0")) or None
SETTLE_SECONDS = float(os.environ.get("PROBE_SETTLE", "75"))


async def run_one(dependents: int) -> None:
    database = f"test_{os.getpid()}_{uuid.uuid4().hex}"
    connection = AsyncSurreal(URL, timeout=REQUEST_TIMEOUT_SECONDS, streaming=True)
    await connection.connect()
    await connection.signin({"username": "root", "password": os.environ.get("SURREAL_PASSWORD", "spikeroot")})
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await connection.use(NAMESPACE, database)
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    await connection.use(NAMESPACE, database)
    try:
        await connection.query("DEFINE TABLE task SCHEMALESS")
        await connection.query("DEFINE TABLE blocks TYPE RELATION IN task OUT task ENFORCED")
        old, new = RecordID("task", "old"), RecordID("task", "new")
        await connection.query("CREATE $old CONTENT {status: 'open', blocked_by: [], events: []}", {"old": old})
        for start in range(0, dependents, SEED_BATCH):
            ids = range(start, min(start + SEED_BATCH, dependents))
            rows = [
                {"id": RecordID("task", f"y{i}"), "status": "open", "blocked_by": [old], "events": []} for i in ids
            ]
            edges = [{"in": old, "out": RecordID("task", f"y{i}")} for i in ids]
            await connection.query("INSERT INTO task $rows", {"rows": rows})
            await connection.query("INSERT RELATION INTO blocks $edges", {"edges": edges})

        statements = [
            "LET $stamp = (UPDATE $old SET superseded_by = $new, updated_at = time::now(), "
            "events += [$ev] WHERE (superseded_by IS NONE))",
            "IF array::len($stamp) == 0 { THROW 'stamp lost' }",
            "CREATE $new CONTENT {status: 'open', blocked_by: [], events: []}",
            "DELETE blocks WHERE in = $old",
        ]
        params: dict[str, object] = {"old": old, "new": new, "ev": {"action": "superseded"}}
        note = {"action": "dependency_reanchored", "from": "task:old", "to": "task:new"}
        for i in range(dependents):
            params[f"y{i}"] = RecordID("task", f"y{i}")
            params[f"n{i}"] = note
            statements.append(
                f"LET $u{i} = (UPDATE $y{i} SET blocked_by = array::distinct(array::map(blocked_by, "
                f"|$b| IF $b = $old THEN $new ELSE $b END)), updated_at = time::now(), events += [$n{i}] "
                f"WHERE (blocked_by CONTAINS $old))"
            )
            statements.append(f"IF array::len($u{i}) == 0 {{ THROW 'reanchor lost' }}")
            statements.append(f"RELATE $new->blocks->$y{i}")
        text = "BEGIN;\n" + ";\n".join(statements) + ";\nCOMMIT;"

        started = time.monotonic()
        outcome = "committed"
        try:
            if TXN_TIMEOUT_SECONDS is None:
                await connection.query(text, params)
            else:
                with connection.timeout(TXN_TIMEOUT_SECONDS):
                    await connection.query(text, params)
        except Exception as error:  # noqa: BLE001 - a probe reports whatever the engine says
            outcome = f"RAISED {type(error).__name__}: {str(error)[:200]}"
        elapsed = time.monotonic() - started
        if TXN_TIMEOUT_SECONDS is not None:
            await asyncio.sleep(SETTLE_SECONDS)

        rewired = await connection.query(
            "RETURN array::len((SELECT id FROM task WHERE blocked_by CONTAINS $new))", {"new": new}
        )
        new_edges = await connection.query("RETURN array::len((SELECT id FROM blocks WHERE in = $new))", {"new": new})
        old_edges = await connection.query("RETURN array::len((SELECT id FROM blocks WHERE in = $old))", {"old": old})
        stamped = await connection.query("RETURN (SELECT VALUE superseded_by FROM ONLY $old)", {"old": old})
        print(
            f"timeout={TXN_TIMEOUT_SECONDS} settle={SETTLE_SECONDS if TXN_TIMEOUT_SECONDS else 0} old.superseded_by={stamped} "
            f"N={dependents} statements={len(statements)} params={len(params)} text_bytes={len(text)} "
            f"elapsed_s={elapsed:.2f} outcome={outcome} rewired={rewired} new_edges={new_edges} "
            f"old_edges={old_edges} over_30s={elapsed > 30.0}",
            flush=True,
        )
    finally:
        await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
        await connection.close()


async def main() -> None:
    for dependents in [int(argument) for argument in sys.argv[1:]]:
        await run_one(dependents)


if __name__ == "__main__":
    asyncio.run(main())
```
