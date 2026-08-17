# REPORT-fable-sidecar-07 — design sidecar, packet 07 (store error-honesty CLASSIFICATION)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **standing by** (first-read pass complete; #144 posture recommendation ready; awaiting contract-author-07 questions)
- role: design sidecar (advisory / read-only) — I recommend, I do not write code or tests
- deviations: none
- Packages considered: none — I built no mechanism (advisory). One packages-question RAISED for the contract author: the #144 pin's multi-statement detector should look for a SurrealQL statement-splitter in the installed `surrealdb` SDK before hand-rolling one (§Pin design, note D).
- Reuse ledger: none — I introduce no symbols. My pin recommendation EXTENDS an existing guard (`TestNoSdkCallEscapesTheDriverAtRuntime`), it does not clone one.
- Graded: 82e2587 · HEAD-at-report: 82e2587 · SAME. (All code-state claims below are grepped/read at 82e2587.)
- decisions-needed:
  1. #144 posture — my recommendation is **PIN THE BOUND, do not sweep** (operator/lead may overrule; it is in-scope as classification+invariant, not a retry-policy change). Fork framed below.
  2. Engine-version staleness in the packet file (`3.2.1` → live is `3.2.4`) — a flag, not a fork; contract author must label fixtures at the version actually probed.
- receipt pointers: §1 (posture recommendation) · §2 (engine-version flag) · §3 (#124/§5 amendment guidance) · §4 (deliverable-3 probe shape) · code sites in §1.

---

## First-read pass (done)
1. `docs/plans/v2/07-store-error-honesty.md` — the packet (mission: fix classification at the seam so served errors teach the truth; #118 dead ASSERT marker, #119 cascade root-cause, #144 rediagnosis + validation posture).
2. `docs/reference/surrealdb-31-capabilities.md` — read in FULL. Key sections held: §3 (transactions, the `query()` statement[0]-only gap, `_domain_root_cause` semantic selector), §5 (#124/#144 mechanism correction), §6.1 (the `must conform to` ASSERT text — the #118 marker), §6.5 (SDK doc names the WRONG statement — returns FIRST not last), §8 (open hazards incl. #105/#144 reconciliation note).
3. Findings #118, #119, #144 — re-fetched verbatim via `lore_findings get`.
4. Registered on `lore_comms` as `fable-sidecar-07` (session `packet07-20260817`).

---

## §1 — THE #144 POSTURE: PIN THE BOUND, DO NOT SWEEP

**#144 asks:** sweep every remaining `.query()` call site to `execute_transaction`/full validation, or document the accepted bound with a pin?

**Recommendation: PIN.** Four grounds, each measured at 82e2587.

### A. The gap is STRUCTURALLY MOOT for a single statement.
`.query()` validates `response["result"][0]` only (§3; [CODE] SDK 2.0.0). For a **single-statement** call, statement[0] IS the whole statement — so `.query()` DOES fully validate it. The gap bites ONLY a multi-statement string where `BEGIN` sits at index 0 and later `ERR`s are discarded (exactly #124/#144's mechanism). So a legitimate narrower bound genuinely exists: *single-statement `.query()` is safe; multi-statement must go through `execute_transaction`.*

### B. Every remaining raw-SDK `.query()` site in production is provably single-statement.
Grep (`\.query(` over `loremaster/loremaster` + siblings, excl. tests, excl. `query_raw`, excl. `FindingLedger.query`) at 82e2587 yields exactly these raw-SDK families — each single-statement:
- `store/_txn.py:1207` — `run_query`'s `_attempt`; docstring: *"The ONE single-statement attempt body."* Every ledger `_query` routes here.
- `inbox_awaiter.py:216` — `_live_query`; docstring: *"Run ONE statement on the LIVE connection."* (one `LIVE SELECT`).
- `scout.py:162-163` — `_scout_query_once`; its four call sites (bootstrap DDL, pending-command drain, command CAS, LIVE subscribe) are each a single statement.
- `store/_txn.py:1099`, `:1115` — bootstrap `DEFINE NAMESPACE IF NOT EXISTS` / `DEFINE DATABASE IF NOT EXISTS`; each a single DEFINE, each ridden by `retry_on_conflict`.
- (The `server.py:2642/2644/3776` hits are `FindingLedger.query(area=…, status=…)` — a high-level ledger API, **not** the SDK method. False positives.)

### C. The sweep is a NO-OP — there is nothing to sweep.
Exhaustiveness grep for `BEGIN`/`COMMIT` multi-statement bodies (grep is the honest instrument here — a `BEGIN…COMMIT` string is a non-symbol textual seam, dogfood case (b); **said out loud**). Every production multi-statement string already routes through `execute_transaction`/`execute_read_transaction`: `findings.py:503`, `tasks.py:891/993/1316`, `agents.py:484`, `messages.py:600`, `briefs.py:498`, `memory/local.py:404`, `graph_surreal.py:462`, `index/surreal_manifest.py:246`, `store/lease.py:394` — all the `f"BEGIN;\n{ddl}COMMIT;\n"` shape. `surreal_manifest.py:42-57` even DOCUMENTS the discipline in prose. **The #144 posture is already the de-facto architecture;** the only open question is whether to make it an enforced invariant.

### D. The sweep is HARMFUL where naively applied.
`scout._scout_query` and the two bootstrap DEFINEs deliberately do **not** wrap transport faults as `SurrealConnectionError` (scout.py:142-149; `_txn.py:1084-1089`). Scout's reconnect ladder catches the RAW SDK types; `SurrealConnectionError` is a `RuntimeError` outside that tuple, so routing these through `execute_transaction`/`run_query` (which wrap) would fly a socket drop straight past the ladder and kill scout's reconnect. Forcing single-statement sites through the multi-statement seam breaks deliberate seam architecture. Sweep is not merely out-of-scope — it is wrong for these sites.

**Conclusion:** the bound is real, already-honored, and the risk is a FUTURE regression (someone adds a multi-statement string to a raw `.query()` site → silent partial apply). "A convention no gate checks" is precisely the defect class this packet exists to kill (#118/#119 were conventions no gate checked). So: **PIN it.**

### The pin design (my invented recommendation — contract author implements)
- **Property to enforce:** *no raw SDK `.query()` call in production carries a multi-statement string* (multi-statement bodies must ride `query_raw`-via-`execute_transaction`, which verifies every statement).
- **Home — EXTEND, don't clone (DRY):** the existing runtime SDK-escape guard family in `test_retry_seam.py` — `TestNoSdkCallEscapesTheDriverAtRuntime` (:2294) already wraps the SDK connection and OBSERVES every `.query()` call, and `test_every_production_sdk_call_site_was_OBSERVED_by_the_guard` (:2480) is a **derived-reach coverage pin**. Add, on each observed `.query()` (not `.query_raw()`), an assertion that the statement is single-statement. Because the coverage pin already proves the guard observed every production SDK call site, the single-statement assertion **inherits complete reach** — reach stays a *checked variable*, not a hand-list. This is the instrument-lesson-correct shape (runtime enforcement where an AST cannot see runtime f-strings) AND reuses the one guard.
- **⚠ Note D — the detector must ALLOWLIST THE SAFE, not enumerate the forbidden.** Do NOT key the detector on the literal `BEGIN` — that is the "enumerate the forbidden" antipattern (defeated by a `;`-joined non-`BEGIN` statement pair, which also hits the `.query()` gap). Enforce the positive property: *exactly one top-level SurrealQL statement.* Packages-question for the contract author: check whether the installed `surrealdb` SDK exposes a statement splitter/parser before hand-rolling a `;`-tokeniser (a hand-rolled splitter is a mini-parser — over-engineering unless nothing exists). Whatever detector ships, **state its bound + a named re-open trigger** (per WHEN-YOU-CANNOT-CLOSE-A-HOLE-PIN-IT) and hand it to the contract-adversary with the explicit REACH ATTACK question: *"what multi-statement string would this detector still wave through?"*
- **Mutation proof:** break it by adding a `BEGIN;…;COMMIT;` string at a raw `.query()` site in a scratch copy → the pin must go RED. (Use `scripts/scratch_copy.sh` — do not grade the original tree.)

---

## §2 — FLAG: engine-version staleness in the packet file
The packet says *"spike-surreal, NOW 3.2.1"* and *"every fixture probe here runs on 3.2.1."* **Live spike-surreal is 3.2.4** (`3.2.4+20260803.93ab219`, image `docker.io/surrealdb/surrealdb:v3.2`, up 34h — grounded host-side 2026-08-17). The reference §0 header already records the floating-`v3.2`-tag drift (3.2.1→3.2.4, #336). Consequence for the contract author: **label every fixture at the version actually probed (3.2.4), not the packet's 3.2.1**, per the reference's version-provenance-honesty rule (a fact is never silently relabelled to a newer engine). Not a fork — a correctness note that keeps the fixtures honest. The #107/#118/#119 facts should be re-probed on 3.2.4 anyway since these are served-error surfaces.

---

## §3 — GUIDANCE for the #124 / §5 amendment (deliverable 2 of #144)
- The original reconciliation harness **still exists**: `scratchpad/102-recovery/` (incl. `probe_txn_control_no_sequence.py`, `probe_txn_control_predefined_table.py`, `probe_txn_control_warmup.py`, `probe_conflict_kind.py`) — so #144's OPEN reconciliation IS dischargeable, contra any worry it was lost. **Read it FIRST and reconcile** before overwriting #124 — the #144 honesty bound is explicit that two harnesses can each be right about their own run, and there may be a third mechanism the 2026-07-19 probe did not reproduce.
- ⚠ `scratchpad/` is unrecoverable-by-construction (repo CLAUDE.md). Whatever the harness teaches must be **transcribed into a durable receipt** under `docs/plans/v2/receipts/<date>-packet07/`; the amended finding #124 and §5 must cite the DURABLE receipt, never the scratchpad path.
- Keep #124's **conclusion** (declare every table before first write — now on two measured reasons, incl. the undeclared-edge `TYPE ANY` downgrade). Correct only the **mechanism** (retryable conflicts hidden by `query()`'s statement[0]-only validation, NOT silent committed-row loss). Do not cite #124 as evidence SurrealDB loses committed data.

---

## §4 — GUIDANCE for "verify the classifier sees a LATER-statement conflict" (deliverable 3)
This is a PROBE, probe-derived per the packet's fixture law (§Entry check). Shape:
- Construct `BEGIN; <non-conflicting stmt>; <CAS/write that genuinely conflicts>; COMMIT;` under REAL concurrent contention on spike-surreal (**3.2.4**), run through `execute_transaction`.
- **Positive control:** the later-statement conflict is classified retryable (`is_retryable_conflict_error` → `RetryableConflictSignal`) and the shared driver retries it to a successful land. This confirms `_rollback_verdict` reads the marker where §3 says it lives — on the **COMMIT/last** entry — even when the ROOT conflict originated in a non-first statement.
- **Negative control** (a probe needs a control): a later-statement DOMAIN rejection (an `ASSERT` violation) is classified non-retryable → `SurrealStoreError`, NOT retried. Proves the classifier discriminates retryable-vs-domain when both surface past index 0.
- Commit the probe transcript as a durable receipt.
- Ties to #118/#119: the domain-rejection leg exercises exactly the `_domain_root_cause` semantic (non-cascade) selector (#119) and the corrected ASSERT marker (`must conform to`, #118) — so this one probe can carry the positive controls for all three findings if the contract author wants the economy.

---

## Consult log
- **2026-08-17 — #144 posture fork (comms directive #5005, thread q:pkt07-144-posture).** contract-author-07 ground-truthed deeper than my first pass: #118/#119 CODE already fixed at `8f24e11`; #144 misdiagnosis confirmed live on 3.2.4; "retry sees a later-statement conflict" already pinned (`test_surreal_store.py:2921`); and the multi-statement-through-bare-`.query()` bound is enforced only by a SCATTERED PER-MODULE HAND-LIST of pins. **My answer (full):** `docs/plans/v2/receipts/2026-08-17-packet07/DESIGN-sidecar-144-posture.md`. TL;DR: **PIN via Option A in its CHEAP form** — extend the autouse runtime `_sdk_guard` with a single-statement assertion on bare `.query()` and DELETE the scattered pins (fixes the hand-list-reach defect at ~B's cost; net simplification; STOP-rule doesn't fire). Detector = positive "exactly one top-level statement", packages-checked, stated `;`-in-literal bound + re-open trigger, scoped to `.query()` not `.query_raw()`. **#124 coverage pin: keep DEFERRED** (operator deferred 2026-07-14; pulling it in re-opens an operator scope decision) but carry it forward as a named still-open item in the #124-row amendment. Fallback if `_sdk_guard` extension entangles: B + file the hand-list as a finding; never build a bespoke AST guard. Ack'd #5005; replied #5006 (signal).

- **2026-08-17 — #144 follow-up (3 sharpenings).** Answered in `DESIGN-sidecar-144-posture.md` §5, grounded by reading `test_retry_seam.py`. (1) Distinguish legit `query_raw` from bare-`query()` escape **by method name** (guard already records `escape.method`); assert single-statement on EVERY intercepted `query` call, not just escapes (orthogonal to the escape property). (2) **YES pair a derived-reach AST leg** — mirror the retry-escape guard's existing two-leg (AST lint + runtime) structure; the AST leg is REQUIRED to safely retire the scattered offline pins without a coverage regression, reusing `_unseamed_sdk_call_sites` (derived reach), not a new hand-list. (3) #124 coverage pin stays deferred. Replied on thread `q:pkt07-144-posture`.

- **2026-08-17 — item 4 (query-too-complex classifier branch, dead on 3.2.4; comms #5011).** Answered in `DESIGN-sidecar-144-posture.md` §6. **Recommend Opt 3 (HYBRID):** keep the defensive branch + retire the 2 lying hand-typed "recursion depth" fixtures (`test_memory_backend.py:2056`, `test_surreal_store.py:1362` — #118 disease verbatim) + add a [real]-tier inverse-live-provocation pin with a pin-tied re-open trigger. Grounds: asymmetry (trivial keep vs delete-and-be-wrong = the packet's own #118/#119 defect), floating-`v3.2` drift (#336) makes re-introduction a live risk, Consumer/Trust (keep the teaching label; deleting ripples into the served closed-set pin `test_surreal_store.py:3600`). Marker-fragility defused by the inverse pin. Fixtures MUST change regardless (defect, not fork). ⚠ `scripts/probe_query_complexity_07.py` is UNTRACKED — commit for a durable citation; store-ref docs update owed (in-packet scope). Returns to OPERATOR to settle (operator opened the fork). Ack'd #5011; replied #5013 on thread `q:pkt07-item4-querycomplex`.

- **2026-08-17 — item 4 RETRACTED (contract-author #5012/#5015; lead #5017).** My §6 recommendation was built on a false-negative premise: the query-too-complex branch is LIVE on 3.2.4 (the real BM25 `@@` RRF query trips #66's ~120-clause limit; parser recursion is NOT operator-agnostic — my §6 endorsed that wrong reasoning). No design change; the inverse-unreachable pin must NOT be built; fixtures are NOT #118-disease (provenance refresh only). Marked §6 RETRACTED with a banner.
- **2026-08-17 — DOC CORRECTION (adversary-07 F1; lead directive #5023). OWNING AN ERROR:** my `DESIGN-sidecar-144-posture.md` §5.2 (and other sections) carried a FABRICATED count — "5 scattered per-module pins" — which I inflated from contract-author-07's #5005 phrasing (itself wrong) and which PROPAGATED into the contract. The exact un-derived-count defect this repo has the most receipts against. RE-DERIVED independently (grep of the whole test tree): exactly ONE pin (`TestNoMultiStatementDdlRidesABareQuery`, floor_calibration.store + lease); the other "pins" are docstring prose / unrelated bare-NAME lookups. The real subsumer is the pre-existing retry-escape lint/guard, not the new offline leg (narrower in 3 dims). Corrected the doc at every occurrence (self-contained top header + per-sentence fixes, since retrieval chunks lose headers; verified by grep no uncorrected fabrication prose remains). Also annotated the #124-defer one-liner as operator-OVERRULED (pulled in as item 3, #5010/#5017). Two-leg recommendation itself was operator-ratified and stands. Ack'd #5023.
- **Lesson for myself:** every count I state must be DERIVED by me from the tree, not inherited from a teammate's message — I inherited "separate pins in comms_schema/message_ledger/graph_surreal" from #5005 and reported it as fact without grepping. Verify-don't-assume applies to counts in teammate messages exactly as to docs.

## Standing by
Idle-between-questions is benign. Contract-author-07 will SendMessage design questions; I answer in a design doc / here + reply via lore_comms. Retire on the lead's word.
