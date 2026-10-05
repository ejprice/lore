# Packet 63c — ruling amendment 37 (sidecar-63c-2, 2026-09-29): a28c's three open decisions — FK-a28c-9 (the text-eligible kinds are a MEASURED allowlist; Reading A, with my am-36 erratum), F-15 (the pending-red masking window — accepted residual, mechanically bounded), F-11 (a transactional parse error served as transport — IN the i-a build at ONE chokepoint, no contract round)

Rules lead Task 38 over `REPORT-contract-63c-i-a-a28c.md` (`7017b54`) SUMMARY "Decisions needed" (1)–(3), §F FK-a28c-9,
§FLAGS F-11 / F-15, §A.2b (`probe_kinds.py`, 3.2.4). Lore client `ECONNREFUSED` for this task too: the directive was read
from the native wake; every symbol below was verified by `awk`/`sed` over the source and the a28c contract file
(`lore_verify` unavailable — said out loud). Constraint honoured (am-35 §0 / am-36 §E, lead Task 38): a28c is the LAST
contract round — every ruling lands as a builder requirement at one chokepoint, a pinned bound, or an accepted residual.
**None of the three is a NEW property; nothing here re-opens the contract.** Item (4), 58-r4, is parked with 58 and not
ruled. `adversary-63c-i-a-a28c` is grading a28c now; its routing table reaches me for triage afterwards and may cite this
doc.

## 1. FK-a28c-9 — Reading A, CONFIRMED as folded; the kind set is an ALLOWLIST whose every member is measurement-backed

**Erratum (mine, am-36 §1.1 and §1.2 pin 3):** I wrote *"text ONLY for `kind: Internal` — the U prefix, ASSERT, coercion,
recursion-depth"*. The kind was DERIVED on the a28b author's seven measured legs (U, ASSERT, T — all `Internal`) and
STATED over a fourth label nobody had measured. `probe_kinds.py` (§A.2b) measures the recursion-depth rejection as
`kind: Validation`, `details: None`, on both paths. The quantifier law again — derived on one member, stated over the set;
my sixth self-instance in this packet. A build following my letter would drop #66's *"query too complex"* teaching on
`run_query`, exactly as the author says.

**The lift (Fix-the-CLASS rule 1).** PROPERTY: *engine TEXT may decide a teaching LABEL — never the class, never the
retry — only for kinds the engine leaves untyped (`details` carries no decision), and the set of such kinds is an
ALLOWLIST OF THE SAFE, each member admitted by a live measurement, never by reasoning about what "should" be untyped.*
DOMAIN source of truth: the installed SDK's `surrealdb.errors.KIND_TO_CLASS` (nine kinds today; a28c's `_sdk_kinds()`
already derives it). a28c's fold IS the pin: `_TEXT_DECIDED_KINDS = frozenset({"Internal", "Validation", "Thrown"})`
(`test_fixwave_a28c_63c_i_a.py`, the block under *"amendment 36 §1.2 pin 3"*), with the positive control iterating
every OTHER derived kind carrying `_HOSTILE_TEXTS` → the text branch is never reached. Reading A stands; BUILDER
CONSTRAINTS item 1 is already worded for it (*"and `kind: Validation` (recursion depth — FK-a28c-9)"*). No pin changes.

**Two completeness legs, stated so the allowlist cannot silently become a hand-list:**
1. **Negative (exists):** ∀ kind ∈ `KIND_TO_CLASS` ∖ allowlist, hostile text moves nothing — the folded positive control.
2. **Positive — every allowlist member is LIVE-backed and `details is None` (pin-the-miss, generated over the
   allowlist):** `Internal` by U-sdk / ASSERT / coercion, `Validation` by recursion depth (#66) on `run_query`, `Thrown`
   by our governed prefix. The docstring carries the trigger *"the day the engine or SDK types this shape (`details`
   non-`None`, or a new kind in `KIND_TO_CLASS`), the typed branch goes ahead of the text and this member is
   re-examined."* This generalises am-33's U-sdk pin-the-miss over the whole allowlist instead of one member. **The
   adversary confirms a28c carries a LIVE `Validation` cell on `run_query` (the recursion-depth checkpoint named at its
   ~l.311/336), not only `test_surreal_store.py`'s bare-text #66 pin.** If the live cell is absent it is a
   test-self-hygiene residual under rule 5 — listed at close-out, not a reopen — because the typed-first ladder + the
   negative control + the bare-text pin already bound the loss to *"the recursion LABEL on a typed `Validation` error"*.

**The `Thrown` member, bounded.** Inside the allowlist the text ladder is flat (as folded and pinned). So a NON-governed
THROW whose message carries an ASSERT / coercion / recursion phrase can move the LABEL (never the class, never the
retry): am-36 §1.2 pin 4's stated bound is hereby extended verbatim over the whole allowlist `{Internal, Validation,
Thrown}`, same trigger. A builder MAY key the text tests by kind (`Thrown` → our anchored prefix only; `Internal` → U
prefix at position 0, then ASSERT / coercion; `Validation` → the recursion marker) — it satisfies every a28c cell and
makes that bound vacuous — but it is not required, because a pinned bound already covers it and the last round is
closed.

## 2. F-15 — the pending-red masking window: ACCEPTED RESIDUAL (rule 5, test-self-hygiene), with its mechanical end named

**What is true.** a28b's door-enumeration exact-set pins assert the POST-build set and are registry-owned RED at
`169925f`; a second unguarded door cannot make them redder until the build (adversary-58-r3 R-5; the #461 shape). Two
sharpenings the author's framing omits: (a) **the backstop R-5 credits is in the same window** — a28c's U-27 made
`test_exhaustion_fates.py` pending-red at base too (`server.py::_comms_register`'s deleted row), so a NEW silent site
is masked in the fate classifier exactly as a new door is masked in the door index; (b) the masking is LATENCY, not
loss — a pending-red exact-set pin still names every unexplained member the moment it is read, and at the build the
owner's explanation expires.

**Ruling: accept.** Not because it is small but because it CLOSES BY CONSTRUCTION: when the 63c-i-a build lands, the
`packet-63c-i-a-a28-contract` entry is retired from `scripts/pending_contracts.yaml`, and any member the build does not
own leaves the pin RED with nobody's name on it → `RED_ORPHANED` → the currency gate fails at packet close-out. The
window is therefore bounded to *"between now and the build"* by an instrument that already runs, not by a hope. Riders:
1. **The cold audit reads the exact-set pins' MEMBER DIFF, not their colour** — at the build both the door index and the
   fates pin must be GREEN; a residual member is a second door found late, adjudicated then, never "still pending".
2. **The lead does not read a28b's red as coverage** (R-5's own verdict) for any catch site landed in this window by
   58, 64b-i or #486 — those commits get the ordinary one-line "did this add an `except` over `_txn` classes?" read.
3. **Re-open trigger:** a SECOND 63c-i-a build wave (a fix wave) while these pins are still registry-owned, or the build
   slipping behind the next contract round that touches `_txn` / the CAS doors — then pin the expected-at-base set.

**The class, routed forward (out-of-authority — a fleet instrument, deferral shape 2):** an owned red is owned at TEST
granularity while the defect it masks is at MEMBER granularity. The general form is a declared-pending-delta exact
set: `observed ^ EXPECTED_AFTER == DECLARED_PENDING` — GREEN at base (the delta is exactly the build's own
adds/removes), RED on any second member (outside the declared delta), and RED at the build until the declaration is
emptied — so the pin is never blind and never needs a registry row. Owner: `pending_contract_gate.py`'s owner;
decision point: the 63c close-out (operator). To file as a finding when the lore client is back (it is down; said so).

## 3. F-11 — a transactional parse error served as `SurrealConnectionError`: IN the i-a build, ONE chokepoint, no round

**What is true (read from `_txn` at HEAD).** `run_query._attempt` catches `(*_CONNECTION_ERRORS, KeyError)` and then
SPLITS: `is_connection_error(error)` → drop + `SurrealConnectionError`; else `is_retryable_conflict_error` →
`RetryableConflictSignal`; else `_classify_engine_error` + `_domain_rejection_error`, connection KEPT, full text logged
server-side, raised message hygienic (#31). `_txn_query_raw` catches the SAME tuple and treats every member as
transport: any RPC-level `ServerError` — the a28c probe's `Validation` parse error, and equally an `Internal` / `Query`
kind — is served as `SurrealConnectionError` and the healthy socket is dropped. `_CONNECTION_ERROR_KINDS`'s own comment
states the property the txn path breaks: *"Every OTHER kind (`Internal` / `Query` / `Validation` / …) is a domain
rejection of the statement itself."* And `test_retry_seam.py`'s #120 block already records that `_txn` held two
disagreeing ladders (the bootstrap closures vs `_attempt`) — this is the third, in the module's other path. **ROUTING
IS NOT SHARING, on the driver's own second door.**

**Weight, measured from the callers (why it is in, and why it is not a round):** all seven production
`except SurrealConnectionError` sites propagate untouched (`findings.py`, `tasks.py` ×2, `keeps.py`,
`floor_calibration/store.py`), except `server.py` (~`_comms`/ack batch, ~l.3945) which SERVES *"ABORTED — store
connection lost; retry these"* — a false teaching for a parse error (the consumer law: a served instruction that
cannot be followed to a fix). No caller loops on it. A parse error on this path is developer-authored (params are
bound; no caller value can nest an expression), so this is the honest-developer gate: a malformed statement in a new
verb is reported as transport, with a reconnect and a re-signin per call. LOW-to-MEDIUM importance; the fix is one
clause.

**Ruling: a BUILDER requirement at ONE chokepoint, for the i-a build (rule 5: a new CASE — the second path — of the
already-pinned property "transport-vs-domain is decided by the ONE predicate `is_connection_error`"; the #120 wave
pinned it over the `_query` seams and the bootstrap closures, a domain that never included `_txn_query_raw` — no test
in the tree names `_txn_query_raw` for this property (awk: three files mention it, none for classification)).**
Mechanics, exactly:
1. **ONE ladder, written once.** The three-way decision inline in `_attempt` (transport → drop + `SurrealConnectionError`
   / conflict → `RetryableConflictSignal` / domain → `_classify_engine_error` + log + `_domain_rejection_error`) becomes
   ONE helper that BOTH `_attempt` and `_txn_query_raw` call. A second inline copy in `_txn_query_raw` is refused: it
   would be the #102 shape (copy #2 of a policy) inside the fix for the #102 shape.
2. **`_txn_query_raw`'s documented intent is PRESERVED by construction:** the auth-after-reconnect RPC error
   (`NotAllowed`) is in `_CONNECTION_ERROR_KINDS`, so it still self-heals as transport; the SDK's routing `KeyError`
   still self-heals. Only non-transport kinds change fate: connection KEPT, `TxnDomainRejectionError` (or the governed
   class through `_domain_rejection_error`), full engine text logged under `_txn`'s OWN logger, raised message carries
   the label + `_SERVER_LOG_HINT` only — the message on this path today echoes `{error}`; the domain branch must not.
3. **Bound, stated:** an RPC-level (envelope) `TransactionConflict` on the `query_raw` path is UNMEASURED (the a28c/a28b
   probes measured the conflict in the per-statement dict). The shared helper handles it identically by construction
   (`RetryableConflictSignal`, consumed by `execute_transaction`'s existing `retry_on_conflict`), so the fate is correct
   whether or not the shape exists; nobody probes it for this.
4. **Verification without a contract round — the cold audit's checked item, both ways:** with the fix, `probe_kinds.py`'s
   `BEGIN; <deep>; COMMIT;` on `execute_transaction` serves a domain rejection with the label
   `_ERROR_CLASS_QUERY_TOO_COMPLEX` (kind `Validation` is allowlisted, §1) and a `drop` spy records ZERO drops; with
   the one call site reverted it serves `SurrealConnectionError` and one drop. And the mutation that proves the sharing:
   move `Validation` INTO `_CONNECTION_ERROR_KINDS` in a scratch copy → BOTH paths serve transport (one constant, two
   paths move). The audit prints the receipt; the builder does not grade it.
5. **The pin, routed forward (not a reopen):** the reach of the #120 ladder pin is a hand-list that this finding shows
   short. The class-correct pin derives its domain — *every `except` in `_txn` whose caught tuple resolves to include
   `SurrealError`* — with a28c's own `_catch_sites.caught_classes` (import-resolved; it already flattens
   `_CONNECTION_ERRORS`) and asserts each handler calls the ONE helper or is allowlisted with a reason (the
   teardown/`_safe_close` sites, which never classify). One generated pin, ~20 lines on an instrument that exists. It
   is NOT added in a28c (the round is closed); it is the FIRST item of the next contract that touches `_txn` (58-r4 by
   collision forecast R-13, else the 63c close-out), named here so it is met deliberately. §E offers the alternative.

## §W
| # | item | lands |
|---|---|---|
| 1 | FK-a28c-9 Reading A; `_TEXT_DECIDED_KINDS` = measured allowlist over `KIND_TO_CLASS`; am-36 pin 4's bound extended over the allowlist; live-`Validation`-cell check | a28c as committed (adversary confirms the live cell) |
| 2 | F-15 accepted residual; closes via registry retirement → `RED_ORPHANED`; three riders; declared-pending-delta form routed to the gate's owner | close-out list + one finding to file |
| 3 | F-11 IN: ONE ladder helper shared by `_attempt` and `_txn_query_raw`; connection kept on domain kinds; hygienic message; audit receipt both ways + the sharing mutation | 63c-i-a build (builder constraint) + cold audit |
| 4 | the derived-domain ladder pin (every `SurrealError` handler in `_txn` → the ONE helper) | next `_txn`-touching contract (58-r4 / close-out) |

## §E — operator-visible
- **No contract round is added.** a28c stays at its one adversary round (in progress). Builder requirements added: ONE
  (F-11, one helper + one call site). Pins added to a28c: none.
- **The F-11 alternative, if you prefer a pin now:** the §3 item 5 generated pin costs one derivation on a28c's existing
  instrument and, under rule 5's "concrete door gap → ONE targeted pin, no re-grade" clause, could ride a28c without a
  round. I did not take it because F-11 is not security-relevant (developer-authored statements only) and the cold
  audit's both-way receipt covers the build; say the word and it moves from §W row 4 to row 3.
- **F-15's double blindness (the fate backstop is pending-red in the same window)** is the one fact in this doc I would
  want you to know even if you read nothing else: until the build, a new silent catch site over `_txn` classes anywhere
  in the tree is visible to NO green pin. Bounded by the build + `RED_ORPHANED`; not by vigilance.
- Errata this amendment (mine): am-36 §1.1 / §1.2 pin 3 (`kind: Internal` stated over recursion depth) — the quantifier
  law, caught by the author's probe, not by me.

## 4. Appended 2026-09-29 (lead FYI on `REPORT-adversary-63c-i-a-a28c.md@68a1011`, SUFFICIENT-FOR-BUILD): CONCUR on F-1 / F-2 routing, with the SHAPE of §W row 4 fixed so F-2 is not fixed by a longer spelling list

- **F-1 (WB-H, survivor — `_domain_root_cause` selects the cascade by an anchored compiled-pattern `.match`):** CONCUR —
  builder requirement, the typed `_CASCADE_KIND` (`NotExecuted`) constant already ruled in am-36 §1.1, no string test of
  any spelling; the cold audit runs the KF probe; no pin now. It is ROUTING-IS-NOT-SHARING in its purest form: same
  effect on 3.2.4, silent degradation to the all-cascade fallback under a reworded engine message. Low stakes (a
  logged root cause), correctly a bound-by-rule under am-36 §E's "any further instance after a28c".
- **F-2 (KG — `_text_testers_in` misses `re.compile(...).match` / `from re import` spellings; 2nd strike on that
  instrument after D-12):** CONCUR — accepted residual; the derivation change rides §W row 4. **But row 4's content is
  hereby fixed, because "widen the spellings" is the instrument lesson's eighth defeat pre-announced:** the tester
  derivation keys on SPELLINGS (`in`, `startswith`, `re.`…), an unbounded forbidden set; D-12 and KG are strikes one
  and two on the same hidden constant. The class-correct instrument is EFFECT-level and spelling-blind: a
  **garbage-text, correct-kind cell** in the KB matrix — a typed error / per-statement dict whose `details.kind` is the
  decision kind (`TransactionConflict`, `NotExecuted`, the record shape) and whose `message`/`result` text is
  NONSENSE (no engine words at all) — asserting the retry, the root cause and the class are decided anyway. WB-H
  fails it (its `.match` finds nothing and the selection degrades), and so does every spelling of every text reader
  that will ever be written, with no AST walk. Keep the exact-set pin as the honest-developer NAME gate (allowlist the
  safe, as folded); the garbage-text cell is the gate for the mechanism. Row 4 = the derived-domain ladder pin (§3
  item 5) + the garbage-text cells, both on the next `_txn`-touching contract; no widening of `_SEARCH_METHODS`.
- No objection to the build spawn; builder-63c-i-a-a28c carries am-27..37 as stated.

## 5. Appended 2026-09-29 (lead, over `REPORT-builder-63c-i-a-a28c.md@3e0553f` §DEV D-4 / D-5; contract closed): D-4 ACCEPTED as required by am-36, D-5 → a BUILDER requirement — the cascade kinds are the SDK's own measured SET

- **D-4 (`_domain_root_cause` no longer skips an EMPTY-TEXT entry) — ACCEPT; not spec-silent.** The old clause
  (`text and not cascade`) made the engine TEXT a selector input; am-36 §1.1 retires exactly that (*"text = EVIDENCE for
  the server-side log only, never a decision input"*). The typed selection is the rule; an ERR entry with empty text
  and a substantive `details.kind` is still classified by its kind — the record shape by `AlreadyExistsError.record_id`,
  the governed THROW by `Thrown`, anything else `unspecified rejection`, loud. **Bound, stated:** no 3.2.4 shape emits
  an ERR entry with empty text (unmeasured, not claimed); if one appears with a NON-cascade kind it is selected and
  served by its kind. No pin now (test hygiene; a `("", substantive kind) → selected` cell may join §W row 4). Cost 0.
- **D-5 (`details.kind: Cancelled` measured after the offender) — BUILDER REQUIREMENT, patch delta before commit:**
  `_CASCADE_KIND` becomes **`_CASCADE_KINDS = frozenset({QueryDetailKind.NOT_EXECUTED, QueryDetailKind.CANCELLED})`**
  — the SDK's OWN constants (packages over hand-rolling; `QueryError`'s docstring names the family *"timeout, cancelled,
  not executed"*), and `_is_domain_cascade_notice(failed)` is `_detail_kind(failed.typed) in _CASCADE_KINDS`, nothing
  else. Why a requirement and not a bound: with `NotExecuted` alone the DEGENERATE all-cascade list
  `[Cancelled…, NotExecuted-COMMIT]` selects the first `Cancelled` entry as the "substantive" root cause — a FALSE root
  cause served into the rollback log, and a contradiction of `_domain_root_cause`'s own docstring (*"degrades to the
  LAST entry: the engine's own final word"*). The builder's "selection unchanged in every measured shape" is true of
  the non-degenerate shapes only; the widening restores the documented fallback. **Adjudicated, all three members of
  the SDK's `QueryDetailKind` (the domain's source of truth):** `NOT_EXECUTED` → cascade (measured: before the offender
  AND the COMMIT notice, builder §REQ-3) · `CANCELLED` → cascade (measured: after the offender, §REQ-3 first run) ·
  `TIMED_OUT` → SUBSTANTIVE, deliberately excluded (a statement that RAN and timed out is the cause, never noise).
  The set's docstring carries those three lines. am-36 §1.1's *"`_is_domain_cascade_notice` decides `details.kind ==
  "NotExecuted"`"* is amended to *"∈ `_CASCADE_KINDS`"* — erratum mine: derived on the a28b/a28c probes' pre-offender
  shape, stated over every cascade entry (quantifier law; the builder's table-less run caught it). No pin mutates
  `_CASCADE_KIND` by name (awk over the test tree: zero hits), so the rename is free; the audit's KF probe is
  kind-decided and stays valid. **Completeness leg → §W row 4:** a generated pin over `QueryDetailKind`'s members
  (derived from the SDK) asserting each is adjudicated — cascade or substantive — so a fourth member reds by name.
- FK-B1 Reading A (prose-satisfied text pin, AST re-key on row 4): CONCUR, as the lead routed.

## 6. Appended 2026-09-29 (lead, over `REPORT-blindreader-63c-i-a-3.md@cdf840d` §4; contract closed; ONE post-audit fix round with §5 D-5): triage — each item FIX-IN-ROUND (chokepoint named) / BOUND / RESIDUAL, with its pin check

Method: every verdict below was checked by `awk` over the contract files (`test_fixwave_a28{,b,c}_63c_i_a.py`), the
builder's patch (`…/47c98d77…/scratchpad/builder-63c-i-a-a28c.patch`, md5 `956e4136` verified) and my own prior
rulings. **A fix that reddens a pin is a STOP** — each FIX-IN-ROUND carries the pin it was checked against and the STOP
condition the round's cold audit re-checks. Lore still `ECONNREFUSED`.

| # | verdict | chokepoint / bound | pin check |
|---|---|---|---|
| **M-1** store reference stale (§3 bullet "client-side conflict retry", its #111 sub-bullet, §6 item 3, the §3 "marker-seeking" sentence, the summary line "#111 answered (keep the substring…)") | **FIX-IN-ROUND** (docs, this wave; the fix round edits `docs/reference/surrealdb-31-capabilities.md`) | ONE edit per passage, facts below | no instrument reads `docs/reference` (blind reader §6: structurally uncovered); nothing reddens |
| **M-2** `MigrateGovernedResult.table_defined: bool \| None = True` | **FIX-IN-ROUND** | the field has **NO default**; it is DERIVED at ONE assembly point from the precondition read: `table in preconditions.defined_tables` whenever `INFO FOR DB` ran, `None` iff it did not (`_not_supported(store_was_read=False)`, any verb-level refusal that precedes the read). Every `_refused` / `_not_supported(store_was_read=True)` site receives the derived value — a refusal AFTER the read carries the measured truth; nothing carries a default (CLAUDE.md: never default a value the code branches on) | a28 `…:2098` asserts `is (table not in removed)` on proceeding legs — the derived value satisfies it; FK-4 invalid-table → `None` and am-34 §4 undefined → `False` unchanged; no test constructs `MigrateGovernedResult(` (awk over the test tree: one comment hit); `_RULED_FIELD_SPEC` pins the COUNTS model only. STOP condition: none found |
| **F-4 / F-5** stale `_txn` docstrings (`execute_transaction` "first entry whose text is non-empty … marker-less"; `TxnContentionExhaustedError` "`can be retried` marker"; the comment above `_ASSERT_VIOLATION_MARKER` "keys off of") | **FIX-IN-ROUND** | rewrite to the typed facts (§5 `_CASCADE_KINDS`, `_RETRYABLE_CONFLICT_KIND`; text = evidence; the marker ladder is the `Internal`/`Validation`/bare-text leg only) | a28 A4-style `__doc__` pins cover `governed` / `principals` docstrings, not `_txn`; a28c's exact-set text-reader pin is AST, not prose. STOP condition: none |
| **F-6** (= §5 D-5) | ruled §5 — `_CASCADE_KINDS` | — | KF probe kind-decided; no pin names `_CASCADE_KIND` |
| **F-8** RPC-level conflict on the txn path leaves `last_conflict` stale; exhaustion logs a prior attempt's cause | **FIX-IN-ROUND (minimal)** — latent on 3.2.4 (unmeasured shape: conflicts arrive per-statement) | `_run_verified_transaction._attempt` resets `last_conflict = None` at ENTRY, so it always describes THIS attempt; an RPC-level conflict then exhausts with no per-statement root (honest: none exists) instead of a stale one. The `label`/`url` for `retry_on_conflict` on the txn path (so `store.retry.exhausted` carries the engine cause) is 58-r4's surface (its exhaustion-record pins) → routed there, not this round | 58's tiers / exhaustion pins construct a per-statement conflict on EVERY attempt, so the reset changes nothing they see. STOP condition: a pin asserting exhaustion logs an EARLIER attempt's conflict (none found) |
| **F-9** mixed-owner sentence "other principal(s): N distinct owner(s) (first K named: …)" | **FIX-IN-ROUND** — it breaches am-34 §2 as written: TWO integers (N and `len(named)`), and the total labelled as "other" (Leg-1 label/set mismatch) | the ONE describe (`_owned_unscoped_part`'s mixed branch) renders am-34 §2's form: substring `owned by the operator` kept, the samples named, and its ONLY integer `distinct_owner_principals` rendered AS THE TOTAL — e.g. *"owned by the operator and by others — N distinct principal(s) in all: <samples>"*. The per-class ROW counts are dropped by am-34 §2's ruling (deliberate; not re-added). `foreign` is correct as built (the total IS the other-count there) | `_OWNER_SENTENCE_STATES["mixed"]` ∋ `distinct_owner_principals` ✓; stems `("owned by", "classif")` ✓; the `[mixed-owners]` substring pin ✓; pin (2) "every integer is a field value" is SATISFIED more strongly (one integer, one field); no test pins "distinct owner" / "first N named" (awk: zero hits in the 63c-i-a contracts; `test_agent_governance` pins a different sentence). STOP condition: none |
| **F-10** message backfill: rows excluded by the sender-soundness clause are un-migrated, unnamed, `refused=False`; a re-run stamps 0 forever | **FIX-IN-ROUND** — the input-fate law (every input emitted / reported / rejected-and-reported): a silent fate is the one forbidden shape | the message leg MEASURES the leftover after its UPDATE (ONE read: `count(message WHERE scope IS NONE AND owner_principal IS NONE)`) into a typed result field `unsound_sender_messages: int \| None` (`None` iff the leg did not run — am-32 §2.1's rule; `0` when it ran and none remain); the render DERIVES the sentence iff `> 0`: *"N message row(s) were not migrated: their sender has no owner or scope — a sender registered tokenless mid-migration, or a non-agent sender; re-run after `--table agent` for the former"*. Also the leg docstring's stale `WHERE scope IS NONE AND owner_principal IS NONE` is rewritten to the full predicate | a28 A5 pins `backfilled == 1` and the unsound row NOT stamped — unchanged (the field is additive); the result model is a dataclass with no field-set pin; pin (1)/(2) iterate the COUNTS model. **STOP condition: any pin counting the message leg's store reads on its success path** (none found by awk; the F-5 one-read pin is the undefined-table path only) — if one exists, the field is instead DERIVED as `scanned − already_migrated − backfilled` with the leg's `scanned` semantics verified first, no new read |
| **F-12** new bare `SurrealStoreError` raises escape `_dispatch_migrate_governed`'s catch (traceback instead of "stderr line + exit 1"); `_scope_count` keeps the tolerant policy for the same non-list shape | **FIX-IN-ROUND** (two chokepoints, one policy) | (a) the dispatch catch names the BASE `SurrealStoreError` (subsumes `SurrealConnectionError`; keep the tuple's other members) so every store fault reaches the operator as the docstring promises; (b) `_scope_count` adopts the ONE fail-closed policy — a non-list / non-int answer raises the same `SurrealStoreError` `_governed_select` raises (the a28 property "a wrong-shaped dependency never WRITES", pins `…:1216` / `…:1240`), never a silent `[]`/`0` | no pin names `_dispatch_migrate_governed`'s catch tuple or `_scope_count` (awk over the three contracts: zero hits). STOP condition: a pin feeding `_scope_count` a wrong shape and expecting `0` (none found) |
| **F-13** register's unique-violation branch: raw `TxnUniqueViolationError` re-raised when the row does not read back; recursion unbounded | **RESIDUAL — as RULED, both halves** (am-32 §1.2: confirmation re-read; row exists → the existing re-register path; row absent → *"the caught error propagates UNCHANGED, after exactly ONE CREATE"*) | **Wrap into `AgentRegistryError`: REFUSED — it reddens a pin.** a28b's `_CAUSE_CLASS` is an EXACT set of the registry's teaching classes (its comment: a new `AgentRegistryError` class reds the pin), and the base is reserved for "a just-CREATEd row that does not read back" — a different branch. A store-level race between conflict and re-read is a store fault the registry cannot teach about; the propagated class already teaches (*"unique violation … re-read the row"*). Recursion: `self.register(...)` re-enters only after the row EXISTS, where the re-register path performs NO CREATE — the ONE-CREATE pin (a28b `…:391`, count-keyed) bounds it; it recurses again only under a create/delete oscillation on the agent table (adversarial-only → STOP-rule: bound). Trigger: a measured create/delete oscillation on `agent` | ONE-CREATE pin + propagate-unchanged are pinned (a28b K-series); nothing changes |
| **F-14** kindless ERR entries take different paths (single: SDK resolves → `Internal`; txn: `typed=None` → bare-text ladder) | **RESIDUAL** (unobserved on 3.2.4; the forward-only store) | the ONE-parse rule already routes every ERR dict through `parse_query_error`; a kindless dict there resolves like the single path. Trigger: a kindless ERR entry observed on either path → then `_failed_statements` must never leave `typed=None` for an ERR entry (the bare-text ladder stays for CALLERS passing strings — a28c constraint) | a28c pins construct `_FailedStatement(index, raw_result)` with `typed` defaulted and expect the text ladder — untouched |
| **F-16** compensation dropped: the ALSO-line and `comms.register.compensation_failed` went with it | **RESIDUAL — no rider owed beyond am-28's letter.** am-28 §F-1 deleted the compensation AND its plumbing (`minted_by_this_call`), named the residual (tokenless-winner race → a keep with a keeper and zero scoped rows) with its CLOSER (63c-i-b β denies tokenless registers) and a trigger. The ALSO-line needed the deleted plumbing; restoring it reverses the ruling for a window β closes by construction | my recorded erratum stands: am-28's trigger is unmeasured until β (already in my errata list) — the audit query *"keeps with a keeper and zero scoped rows after a refused register"* is the operator's instrument until then, not a code rider | a19b KP1/KP4 pins as re-keyed by am-28's DUAL; unchanged |
| NOTE fixture drift (`"Exceeded expression recursion depth limit"` vs live `"Exceeded query recursion depth limit"`) | **RESIDUAL** → §W row 4 | the a28c fixture is not a capture; the marker `recursion depth` is common, so no verdict moves | test hygiene |

**M-1 — the corrected facts, exactly (so the fix round edits from a ruling, not from memory):**
1. §3 "Client-side conflict retry is MANDATORY": the retry signal is **TYPED** — `details.kind == "TransactionConflict"`
   on the per-statement COMMIT entry (transactional path) and on the raised `QueryError` (single-statement path);
   measured on 3.2.4, both paths (a28c §A.2; builder §REQ-3; blind-reader §7 P2). The text *"can be retried"* is
   EVIDENCE logged server-side, never consulted for a decision. Cite the symbol `_txn._RETRYABLE_CONFLICT_KIND`, never
   `_txn.py:326` (CLAUDE.md: symbols, not line numbers).
2. The #111 sub-bullet: **"#111 ANSWERED — trigger MET (2026-09-27)."** The typed alternative lives in `details.kind`,
   one level BELOW `ErrorKind` — which still has no retryable member, exactly as the 2026-07-19 read found; that read
   looked one level too high. The SDK ships `QueryDetailKind.{NOT_EXECUTED, TIMED_OUT, CANCELLED}` but NO constant for
   `TransactionConflict` (a bare literal in `_txn`, pinned by the live-shape cells).
3. The cascade selector is **kind-seeking**, not marker-seeking: a rollback's root cause is the first entry whose
   `details.kind ∉ _CASCADE_KINDS = {NotExecuted, Cancelled}` (§5); `TimedOut` is substantive; the degenerate
   all-cascade list degrades to the LAST entry.
4. §6 item 3 (vendor docs are false/silent): keep the framing, correct the claim — *"the retry marker appears in no
   vendor doc, and neither do the per-statement `details.kind` values `TransactionConflict` / `NotExecuted` /
   `Cancelled` — all three measured live; the SDK's `errors.py` names two of them. The typed alternative EXISTS (§3);
   the vendor prose is silent, not the engine."* Add the untyped set as a fact: the U prefix, ASSERT and coercion
   rejections arrive as `Internal` with `details: None`; recursion depth as `Validation` with `details: None` (§1).
5. The summary line ("#111 answered (keep the substring; the trigger is not met)") follows item 2.
6. Store version framing: forward-only at 3.2.4 (MEMORY.md); the reference's 3.1.5 measurements for these shapes are
   superseded where the doc says otherwise, and say so inline (a superseded claim is archived with a header, never
   silently preserved).

**Round accounting (rule 5):** FIX-IN-ROUND 8 items (M-1, M-2, F-4/5, F-8, F-9, F-10, F-12 + §5 D-5), RESIDUAL 4
(F-13, F-14, F-16, fixture drift), no BOUND that is not already ruled, no contract round, no new pin except F-10's
additive field (verified by the post-fix cold audit, which re-runs the pins named above). Not triaged here: the cold
audit's findings (next), and the lead's F-15 note (register ordering — a read, not a finding).

## 7. Appended 2026-09-29 (lead, over `REPORT-coldaudit-63c-i-a-3.md@535677a` §3 NO-GO; before the fix round spawns): F-C11 — the cascade predicate is the SDK's OWN typed predicates (no compare, no membership: the pin is met, not dodged); the five new MINORs triaged

### F-C11 — erratum mine (§5), and the ruling
§5's spelling `_detail_kind(failed.typed) in _CASCADE_KINDS` is an `ast.In` compare, so a28c's text-reader exact-set
pin reports `_is_domain_cascade_notice` as an unlisted tester. I checked §5 against pins that NAME the constant, not
against the pin that derives testers by SHAPE — the reach question (INSTRUMENT 0) asked of the wrong instrument.

**Ruling — neither the lead's `==` default nor an allowlist row: the SDK already ships the decision.** `parse_query_error`
returns a `QueryError` for every `kind: Query` entry, and `QueryError` carries `is_not_executed` / `is_cancelled` /
`is_timed_out` (measured on the installed 2.0.0: all three true exactly for their kind). So:
```
_is_domain_cascade_notice(failed) := isinstance(failed.typed, QueryError) and (failed.typed.is_not_executed or failed.typed.is_cancelled)
```
- **No `_CASCADE_KINDS` set, no `_CASCADE_KIND` constant, no `_detail_kind` call in this decision** (packages over
  hand-rolling: the SDK owns the kind strings; a constant nobody's decision reads would claim a sharing that does not
  exist). §5's "`_CASCADE_KINDS` constant" and §6 M-1 item 3's citation of it are superseded: the reference cites the
  SYMBOL `_txn._is_domain_cascade_notice` and states the adjudication (`NotExecuted`, `Cancelled` → cascade;
  `TimedOut` → substantive) in that function's docstring, which is the ONE place it lives.
- **Why not `==` twice:** two `==` compares over two literals is the a28c-sanctioned spelling for a typed decision, and
  it would pass — but it re-implements a predicate the dependency exports, which is the exact defect class the
  packages rule names, and it is the shape that silently forks when the SDK's own notion of "not run" changes.
- **Why not an allowlist row:** the contract's escalation path exists, but a row for a tester the SDK makes
  unnecessary would be a row that teaches the wrong mechanism.
- **Pin check:** the tester derivation keys on `ast.Compare(In/NotIn)`, `_SEARCH_METHODS` calls and `re` — attribute
  access and `or` are none of these → `_is_domain_cascade_notice` is not a tester; the exact set stays
  `{_classify_engine_error, _assert_envelope_integrity, compose, is_connection_error}` ✓. The KF probe is kind-decided
  (constructs dicts) ✓ and its degenerate cell now reads `(False, 1)` → the LAST entry ✓. `_RETRYABLE_CONFLICT_KIND`
  is unchanged (the SDK ships no conflict predicate; `==` stays there, as a28c constrains). §W row 4's completeness
  pin over `QueryDetailKind` is re-worded: ∀ members, the predicate answers per the docstring's adjudication; a fourth
  member (no predicate, no adjudication) reds by name.
- Builder receipt for the round: the one-liner above, run in the build tree — `parse_query_error({"kind":"Query",
  "details":{"kind":k},…})` for the three kinds → `QueryError`, the three predicates; plus the KF probe both ways.

### The new MINORs
| # | verdict | chokepoint / bound | pin check |
|---|---|---|---|
| **F-C4** a triple-backtick run survives `sanitise_line` into refusal reasons (owner list + `_id_sample`); pre-existing at HEAD | **BOUND — routed to the sanitiser's owner (finding #34's promotion), not this round.** The property (the auditor's own lift): *a stored id rendered into served prose passes ONE sanitiser that neutralises newlines AND fence runs.* The fix belongs INSIDE `loremaster.search._sanitise_line` (every render rides it; a 63c-local escape would be copy #2 of a sanitiser), and changing its output touches every render's pinned bytes — a blast radius this round does not own. Trigger: #34's promotion, or an MCP-served (not stderr) render of a principal id | a 63c fix would redden byte-exact render pins elsewhere — STOP by construction |
| **F-C7** keeps `get_or_create_keyed` `Raises:` docstring stale after the narrowed CAS (K1) | **FIX-IN-ROUND** (prose) | the docstring states the narrowed door: `TxnUniqueViolationError` re-read; every other `SurrealStoreError` propagates | no `__doc__` pin on keeps (awk); none |
| **F-C8** a malformed `cause` makes `parse_query_error` raise (`AttributeError`, measured) out of the verdict path; engine-shaped, unobserved | **FIX-IN-ROUND, paired with F-14 as the auditor suggests — ONE policy at ONE chokepoint:** `_failed_statements` never lets an SDK parse failure escape: an ERR entry the SDK cannot type is carried with `typed=None` (the bare-text ladder, loud `unspecified` at worst) and logged at WARNING naming the entry index — the builder reads `parse_rpc_error`/`parse_query_error`'s source for the exact exception classes it can raise and catches THOSE, never a bare `except`. F-14's residual narrows to "a kindless entry on the two paths classifies alike" (trigger unchanged) | a28c pins construct `_FailedStatement(typed=None)` and expect the text ladder — the same fate ✓; no pin asserts `_failed_statements` raises on a malformed dict. STOP condition: none |
| **F-C9** the `last_conflict_cause` comment over-generalises "the single-statement seams" | **FIX-IN-ROUND** (prose; with F-4/F-5) | say exactly which caller raises unchained and why | prose only |
| **F-C10** transport-branch `SurrealConnectionError` messages interpolate `{error}` (pre-existing); is a transport-kind `ServerError`'s text hygienic? | **BOUND, stated with its reason** — #31's hygiene is about engine text that ECHOES A BOUND VALUE of the rejected statement. The transport branch is reached only for `OSError` / `WebSocketException` / `KeyError` (socket and SDK-routing text) and the two transport KINDS `NotAllowed` / `Connection` — an auth or connection refusal, which the engine authors BEFORE evaluating the statement and which carries no statement value by construction. The interpolation is the operator's only address/auth clue and stays. Trigger: a transport-kind message observed carrying a bound value → then the transport branch logs the text server-side and raises the label, like the domain branch | no pin names the transport message's bytes beyond its prefix (`TestTxnSdkKeyErrorClassification` pins the drop leg); nothing changes |

**Round accounting:** + FIX-IN-ROUND 3 (F-C7, F-C8+F-14, F-C9) · BOUND 2 (F-C4 routed to #34; F-C10) · F-C11 settled
without a contract edit. The fix round carries: §5 D-5 in the §7 form, §6's eight, §7's three. No contract round.
Errata this appendix (mine): §5's set spelling and §6 M-1 item 3's citation of it.

## 8. Appended 2026-09-29 (lead, over `REPORT-builder-63c-i-a-fix2.md@1b219f9` §FORKS / §DRY): F-12(a) → option A (the registry row is the completeness pin working); F-a → stderr + exit 0 with a receipt-line rider; the GROUP ALL reader → ONE function, 63c's two copies collapse NOW, the three foreign copies are routed

1. **F-12(a) STOP — Option A: the base-class catch + the `REGISTERED_FATES` row.** `REGISTERED_FATES` is the DOMAIN's
   source of truth for exhaustion catch sites (58 am-10 §2, a closed classification set that already holds `cli-exit`
   with evidence `("stderr", "returns-named-outcome")`); its completeness pin went RED because a new site appeared —
   that is the pin doing its job, and the answer to a completeness red is the row, never a door around it. The row
   mirrors `principals.py::_dispatch_report_unmigrated`'s exactly (same classification, same evidence, the catch
   tuple as ruled in §6 F-12). **Ownership precedent (a28c F-13 / U-27): the row's owner is the SITE's owner** — 63c
   deleted `server.py::_comms_register`'s row when it deleted the site, and adds this one when it adds the site; the
   file is 58's, the row is 63c's. Option B is REFUSED: a `except TxnContentionExhaustedError: raise` above the base
   catch is a derived PASSTHROUGH that keeps a traceback for exhausted contention, contradicting §6 F-12(a)'s own
   property (*every store fault → stderr + exit 1*) and minting the very door shape 58's registry exists to classify.
   sidecar-64 is informed as a courtesy; if 58's law wants a different EVIDENCE tuple for the row, that is 58's to
   say and does not change the ruling.
2. **F-a (F-10's channel / exit) — CONFIRM stderr + exit 0, with ONE rider.** The run succeeded for every sound row; a
   named leftover is a diagnostic, not a refusal (a refusal means *no row was stamped* and exits non-zero — the two
   outcomes must stay distinguishable to a script). **Rider: the stdout RECEIPT LINE carries `unsound_sender_messages`
   as a typed count beside `scanned` / `backfilled` / `already_migrated`** (derived from the result like its siblings),
   so a script that never reads stderr still sees the leftover; the stderr sentence is the teaching, the receipt is the
   measurement. Pin check: the a28 CLI render pins assert the `table_defined is False` sentence; STOP condition: a pin
   asserting the receipt line's exact bytes (none found by awk) — if one exists, the count rides the sentence only and
   the line is routed to the next CLI-touching contract.
3. **§DRY — the GROUP ALL count reader is ONE function; 63c's OWN two copies collapse in fix2, the foreign three are
   routed.** Measured (awk over the package): the store-ref §5.1 idiom `SELECT count() … GROUP ALL` is read in FIVE
   places — `findings.FindingLedger._extract_group_count` (tolerant), `messages._extract_group_count` (tolerant),
   `diff.py` (inline), `governed._scope_count` (fail-closed since §6 F-12(b)) and `principals._group_all_count`
   (fail-closed, new). Two of the five were minted by THIS build — copy #2 born in the same wave the ONE-IMPLEMENTATION
   law was being applied to `_txn`. **The ONE policy:** an EMPTY result → `0` (a measured empty group — the engine's
   documented shape); a non-list, a non-dict first row, or a missing / non-int `count` → raise `SurrealStoreError`
   (fail closed — a `0` there is a served count describing no set, the shape `governed.py`'s own docstring forbids).
   **Home: `loremaster.governed.group_all_count(result) -> int`** — NOT `lorerunes` (no second workspace member reads
   store results; a capability there is a design decision, not a tidying) and **NOT `_txn`** (its body needs a
   `_COUNT_KEY in row` membership test, which would make it a new tester and redden a28c's exact-set pin — checked).
   **Fix now (fix2, before commit):** `_scope_count` and `_group_all_count` become calls to that one function (the
   builder's own DRY row named the duplication; this is its resolution). **Routed (out of 63c-i-a's granted files):**
   `findings` / `messages` / `diff` re-point to it — owner 64b (its build already edits `findings.py`), decision
   point the 63c close-out; STOP condition for that later step: any pin feeding those readers a malformed count and
   expecting `0` becomes a DUAL re-key, not a reason to keep the tolerant copy. Sharing is proven by MUTATION there:
   change the fail-closed predicate and all five call sites must move.
4. **FYI acknowledged:** F-b's consequence for 64b (`table_defined=` required, `unsound_sender_messages=None` passed)
   rides 64b's brief; D-2's `default=None` on `unsound_sender_messages` is accepted as the honest "not measured" under
   the closed a28c constructor pin, with the builder's named re-open (the next result-model contract drops it).
   The walker pin (am-34 §5) is mine: any re-key sidecar-64 proposes routes through this doc before it lands.

## 9. Appended 2026-09-30 (lead, over 58 am-14 §2 `a9be2c4`): CONCUR on the one-scanner pin's re-key, with ONE rider (import aliases)

**CONCUR.** The am-34 §5 property is unchanged (ONE handler walker, ONE `except`-expression evaluator); the proposed
derivation — resolvers by shape (`eval` ∧ `Expression`), then "resolver-reaching" as the fixed point over `ast.Call`
names within the scanned trees, `_RESOLVER_NAMES` DELETED — is exactly allowlist-the-safe with a derived domain. The
hand-list was my own instrument-lesson instance: am-34 §5 ruled the candidate set DERIVED and the pin shipped a
name-list for the resolver half; `catch_sites_in` → `resolve_caught` was a rename inside the property's own
one-implementation, and the list went blind. The two added controls (through-a-front; the `logger.handlers` negative)
are right. The "r4 renames back" alternative is refused for the reason am-14 gives.

**Rider (a28c-style completeness, one line of derivation):** the fixed point keys on called NAMES, so an IMPORT ALIAS
(`from _catch_sites import resolve_caught as rc`; `import _catch_sites as cs` + `cs.resolve_caught(...)`) breaks the
chain — an honest-developer door (aliasing on import is routine), not the dynamic-dispatch bound the docstring states.
Resolve `Import` / `ImportFrom` `asname` bindings per tree (alias → the bound name; attribute calls through a module
alias → the attribute name) BEFORE closing over calls, and add the control: a synthetic second walker calling the
resolver through an alias → derived. The docstring's bound then honestly reads *"dynamic dispatch, or a class tree
spelled without naming it"* — nothing else. Lands per am-14 §4 with §1 and the F-12(a) row (58's two riders on that
row — `catches=` equals `ast.unparse` of the production tuple; one commit — are accepted).

## 10. Appended 2026-09-30 (lead, over `REPORT-builder-63c-i-a-fix3.md@63c5c71` §FLAGS F-1 / §FORKS F-2): the two fail-OPEN readers — (a) FIX NOW, (b) same fate as a rejected read, never boot-FAIL; the receipt renders `None` explicitly; D-1's pin rides am-14 §1's gate tests if they land now

**Erratum (mine, §8.3):** "FIVE readers" was an un-derived count — awk finds at least eleven — inside a ruling about a
duplicated reader. The CLAUDE.md receipt shape exactly (#102/#120's "eleven copies" that was itself un-derived). The
§8 ruling (ONE policy, ONE home) stands; the DOMAIN is re-stated as *every `SELECT count() … GROUP ALL` consumer in
the package*, derived by sweep at the 64b step, never counted by hand again.

1. **(a) `PrincipalStore` delete path `owned_count` — FIX NOW, via `governed.group_all_count`.** A fail-OPEN guard
   (malformed answer → `0` → SF-63-5's refuse-while-owning gate bypassed → a delete that dangles owned governed rows)
   in 63c's own file is the one shape "known defects get fixed in the session that finds them" is written for.
   Fail-closed: a malformed count raises `SurrealStoreError` and the delete does NOT proceed (the store fault reaches
   the operator through §6 F-12's base-class catch). STOP check for the builder: any pin feeding the delete path a
   malformed count and expecting the delete to proceed (none expected — the 12 governance hits are the owning-refusal
   legs) — a wrong-shaped-dependency pin expecting a refusal is the a28 property and stays green.
   **(b) `governed.report_unmigrated_governed_rows` — same reader, same policy; the boot FATE is the one a REJECTED
   count query already has, never boot-FAIL.** The function is an ALARM (#131's lesson is SILENCE; its cure is
   loudness, not refusing to serve). `group_all_count` raises the same `SurrealStoreError` class `run_query` raises
   when the engine REJECTS that count (`governed.unmigrated_count.rejected`), so a malformed shape takes the path a
   rejected count already takes — ONE fate, no new policy. Rider: the builder READS that caller's fate and reports it;
   if a rejected count is today swallowed silently at boot, that is a finding of the same class (a silent alarm) and
   the fate becomes a logged ERROR with `exc_info` naming the remedy — still not a boot failure. The rest of the
   sweep (the `cascaded` audit count, `tasks`, `store/surreal.py`, `index/surreal_manifest.py`, findings, messages,
   diff) → the 64b §DRY step, decision point the 63c close-out (§8.3 unchanged).
2. **F-2 — render `unsound_sender_messages=None` EXPLICITLY on the agent / memory receipts; omit-when-None is
   REFUSED.** An omitted field is indistinguishable from a binary that never measured it (the #131 "a field nobody
   renders" shape) and gives a script a variable-shape line; `None` is the typed "not measured for this table"
   (am-32 §2.1), served as itself. ONE convention for the whole line: every `None`-bearing field of the result the
   receipt renders is rendered the same way — if the line already renders another `None` field by omission, that
   field moves to explicit `None` in the same delta (one convention, never two).
3. **D-1 (gate unsymboled, judged per path-union; fixed at `entries_for`, no pin) — residual ONLY if am-14 §1's
   gate-matcher tests do not land in the same test-side fix-up.** They do land there per am-14 §4; a path-union
   case is one generated row in those tests, so the pin rides WITH them now (the same commit, 58's file, the site's
   owner writes the row — §8.1's precedent). If the lead judges the gate tests are not that commit, then residual to
   the next gate-touching contract, named in the close-out.

## 11. Appended 2026-09-30 (lead, operator-directed fold before the re-check audit): R2-1 — lore-adm store faults surface as a traceback. ONE fault handler at the lore-adm entry; FR-2 D1 re-ruled; one fates row replaces two; one generated pin over the verb set

Read from the fix3 scratch tree (`…/5e3e72cf…/scratchpad/fix3`, patch md5 `f5897681` verified), not the main tree.

**1. The CLASS, and the domain.** PROPERTY: *every lore-adm verb translates every store or domain fault into
`f"{_CLI_PROG}: {error}"` on stderr + exit 1 — never a traceback, never a success.* It is already written in
`_dispatch`'s own docstring (*"Domain failures are laundered to a stderr line + non-zero exit; a transport fault
surfaces the same way"*) and violated by the code beneath it. DOMAIN source of truth: the verb set is
`build_parser()`'s subparsers, routed by `_dispatch` through the two named branches + `_KEEP_VERB_HANDLERS` +
`_VERB_HANDLERS`. **Sweep, every dispatcher today (fix3 left these NOT TRIED):**
| dispatcher | catch tuple | store faults it lets through as a traceback |
|---|---|---|
| `_dispatch` (principal / key verbs incl. `delete`) | `(PrincipalStoreError, PrincipalKeyStoreError, SurrealConnectionError, ValueError)` | every non-transport `SurrealStoreError` — the R2-1 delete read, any rejected `ensure_ready` DDL |
| `_dispatch_keep` | `(KeepStoreError, SurrealConnectionError, ValueError)` — FR-2 D1 | the same class on keep READS and on `ensure_ready` |
| `_dispatch_migrate_governed` | `(PrincipalStoreError, KeepStoreError, SurrealStoreError, ValueError)` | none (fixed §6 F-12) |
| `_dispatch_report_unmigrated` | `(PrincipalStoreError, SurrealStoreError, ValueError)` | none |
Four hand-written copies of one policy, two of them wrong — the #102 shape, again, in a CLI.
**FR-2 D1 re-ruled.** D1 kept the raw `SurrealStoreError` OUT of `_dispatch_keep`'s catch so that an engine rejection
escaping `KeepStore` un-wrapped would be a loud BUG signal (a missed wrap). Its premise is false for READS (wrapping
is a WRITE-boundary property; `delete`'s `owned_count` read and every `ensure_ready` are un-wrapped by design) — and
a traceback is never an honest operator surface for a store fault, whatever the cause. The missed-wrap property stays
enforced where it belongs: by the FR-2 wrap pins over KeepStore's write boundaries, never by leaking tracebacks to
operators. D1's INTENT (a missed wrap must be visible) is preserved by the handler's message: an un-wrapped
`SurrealStoreError` prints its driver class name in the stderr line (the label + `_SERVER_LOG_HINT`), which is
distinguishable from a `KeepStoreError` teaching — the wrap pins catch the class; the operator still sees the fault.

**2. Pinned property or new?** PINNED, over a hand-list domain of ONE verb
(`test_principals_cli.py::…test_report_unmigrated_on_an_absent_table_fails_loud_not_a_traceback`). R2-1 is a new
CASE — the same property over the other verbs. Under rule 5: an IMPLEMENTATION requirement at ONE chokepoint,
verified by the re-check audit — plus the completeness assertion rule 2 demands for a derived domain (item 4), which is
ONE generated pin, not a contract round.

**3. The ONE chokepoint — the lore-adm ENTRY.** The fault→exit translation lives ONCE, in `_dispatch`, wrapping the
whole verb routing; the three verb dispatchers keep their `try/finally` resource closes and LOSE their `except`
blocks. Exact fate: `print(f"{_CLI_PROG}: {error}", file=sys.stderr); return 1` — the existing shape, byte-identical
to what the four copies print today. It can never swallow a fault into success: the handler's only return is `1`;
`0` is returned only by a verb handler's own path. `_require_config` stays OUTSIDE (a missing `--config` is a
`SystemExit` by design, for every verb). The exception set (all lore-adm faults; the lazy imports move to the top of
`_dispatch`):
```
except (PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError, ValueError) as error:
```
Anything outside it (a `TypeError`, an `OSError` from the filesystem) is a programming defect and DOES traceback —
the honest-developer gate; the tuple is the allowlist of faults the CLI knows how to name.

**4. Exact edits.**
- PRODUCTION (`principals.py`): (i) `_dispatch` = `_require_config` → `load_surreal_only_config` → `try:` the
  existing routing (the two named branches, the keep branch, the principal/key branch with its own `try/finally`
  closes) `except <the tuple above>` → stderr + `return 1`; (ii) delete the `except` blocks of `_dispatch_keep`,
  `_dispatch_migrate_governed`, `_dispatch_report_unmigrated` (their `try/finally` closes stay); (iii) rewrite
  `_dispatch_keep`'s D1 docstring paragraph to this ruling (a docstring teaching a retired policy is the P8d class).
- TEST SIDE (`loremaster/tests/_exhaustion_fates.py`): DELETE the rows `principals.py::_dispatch_migrate_governed`
  and `principals.py::_dispatch_report_unmigrated` (their sites no longer catch — a row without a site reds the
  both-ways pin); ADD ONE row `"principals.py::_dispatch": (Fate("cli-exit", "principals", ("stderr",
  "returns-named-outcome"), catches="(PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError,
  ValueError)"),)` — `catches=` equal to `ast.unparse` of the production tuple (58's rider), same evidence as the
  rows it replaces. The §8.1 fates row for `_dispatch_migrate_governed` is thereby superseded before it lands.
- GENERATED completeness pin (`test_principals_cli.py`, 63c-owned): ∀ verb ∈ `build_parser()`'s subparser choices
  (DERIVED — never a list), with ONE injection point every verb reaches — a store whose `ensure_ready` raises
  `TxnDomainRejectionError("(assert violation); see the server log")` (monkeypatch `build_principal_store` /
  `build_keep_store`) — assert: exit `1`, stderr's first line starts with `f"{_CLI_PROG}: "`, stdout empty, and
  `capsys` shows no `Traceback`. Controls: the same store raising `SurrealConnectionError` (already-laundered class →
  same fate) and a verb succeeding (exit 0, stderr empty). Two-way: the pin reds at fix3-as-is on `delete` and every
  keep verb, green after the edit; a verb added to the parser without reaching `_dispatch`'s handler reds by name.

**5. STOP conditions for the builder / test-side agent.**
- The 58 runtime cross-check ("every listed handler has a runtime injection", am-5 §3 / am-7 §3 item 2): if a driver
  is keyed to the two DELETED sites, it is re-keyed to `principals.py::_dispatch` in the same test-side commit (the
  injection now lands one frame up). If that re-key is not possible in this fold, the FALLBACK is the per-verb form —
  widen the two wrong tuples to `SurrealStoreError` and register THREE rows — with the #102 cost named in the
  close-out (four copies of one policy) and a re-open at the next CLI-touching contract. The fallback is not the
  ruling; it is the escape hatch.
- Any pin asserting a specific dispatcher's `except` tuple by AST or by `__doc__` text (none found: the only tuple
  readers are the fates rows, re-keyed here; `test_principals_cli` pins fates, not tuples) → STOP and report.
- Any pin driving a fault into `_dispatch_migrate_governed` and asserting the catch happens IN that frame (rather than
  the observable exit/stderr) → STOP and report; the observable fate is unchanged either way.
- The production edit touches ONLY `principals.py`; the fates file and the CLI test file are the test side's; one
  commit each, in that order (test side first — the pin must red on fix3-as-is before it greens).

## 12. Appended 2026-09-30 (lead, operator fold, over `REPORT-fixup-tests-63c-i-a-2.md` §ROUND 2 R2-F1 / R2-5): the wrap-coverage class — the lead's lift is RIGHT and it is FALSE on production today: four unwrapped write boundaries in two 63c-owned stores. It rides this fold as a DERIVED pin + four one-line wraps, not as a residual

**1. CLASS and DOMAIN.** PROPERTY: *for every store a lore-adm verb reaches, every derived WRITE boundary sits inside
`wrap_store_rejection(<that store's domain error>, …)`* — so a store rejection reaches the operator as the store's
own teaching, never as a raw driver label; after §11 the raw label is laundered to a clean exit 1, which is honest
but teaches nothing about WHICH domain operation failed. DOMAIN, two levels, both derived:
- the STORE set = the `build_*_store` calls in `principals._dispatch`'s AST (today `PrincipalStore`,
  `PrincipalKeyStore`, `KeepStore`) — never a list;
- per store, the WRITE set = R2-5's derivation generalised over the class: sink (a) `self._query(<stmt>)` /
  `run_query(<stmt>)` whose literal text starts with a write verb (CREATE / RELATE / UPDATE / DELETE / UPSERT /
  INSERT / BEGIN) or is dynamic (`<dyn>` is a write until proven otherwise — allowlist the safe), and sink (b) any
  `execute_transaction(...)`. That derivation is the right domain; "methods referencing `wrap_store_rejection`" and
  the hand-listed `expected_wrappers` are exactly the reach-as-hidden-constant defect R2-F1 names.
- **Exemptions, each with a reason (an allowlist, not a hole):** `ensure_ready` — DDL readiness, raw by design in
  every store, and its fate is pinned by §11's generated CLI pin whose injection point IS `ensure_ready` (right,
  keep it). The governed migration (`governed.py` / the `_migrate_*` legs) — NOT in this domain: its writes are
  governed-guard transactions whose fault contract is the typed `MigrateGovernedResult` refusal + §6 F-12's catch,
  ruled am-30..36; a wrap there would be a second policy for one surface.

**2. Measured on the fix3 tree (the R2-5 derivation run over the three classes, 2026-09-30):**
| store | wrapped | **UNWRAPPED write boundary** |
|---|---|---|
| `KeepStore` | 7 / 7 (R2-1) | — |
| `PrincipalStore` | `create`, `set_subject` | **`set_status` (UPDATE), `set_expires` (2× UPDATE), `delete` (TXN)** |
| `PrincipalKeyStore` | `mint` | **`revoke` (UPDATE)** |
So the lead's premise ("GREEN on current production") fails: FR-2 Q2b established parity with `PrincipalStore.create`
only, and nobody derived the rest. Not a residual — a live gap in 63c's own files, found by the derivation the moment
it was run over the whole domain. **It rides THIS fold**, both halves:
- PRODUCTION (four one-line edits): wrap `set_status`, `set_expires`, `delete` in
  `wrap_store_rejection(PrincipalStoreError, "could not <verb> principal …")` and `revoke` in
  `wrap_store_rejection(PrincipalKeyStoreError, "could not revoke key …")` — the message shape of the existing
  wraps in each file. `delete`'s domain refusals (`PrincipalHasKeepsError`, `PrincipalOwnsGovernedRowsError`) are
  `PrincipalStoreError` subclasses, not `SurrealStoreError`, so the seam passes them untouched (STOP check below);
  §10.1(a)'s malformed-count `SurrealStoreError` becomes `PrincipalStoreError("could not delete …")` — still refused,
  still exit 1, now with the domain teaching.
- TEST (63c-owned, the fixup agent's files): ONE generated pin per store, `∀ store ∈ derived store set, ∀ boundary ∈
  derived write set ∖ {ensure_ready}: boundary is lexically inside a `wrap_store_rejection(<store error>)`` — the
  R2-5 instrument promoted from a scratch script to the pin's derivation (home: beside
  `TestTheRoutedSetIsDerivedAndComplete` in `test_engine_rejection_seam.py`). Two-way: RED on fix3-as-is naming
  exactly the four boundaries above (that receipt is the declared-RED set for the mutation proof), GREEN after the
  wraps; a fifth unwrapped write reds BY NAME. The existing routed-set pin's expectation
  (`expected_wrappers` / the invocation map) is RE-KEYED from a hand-list to *derived write set ∪ the declared
  read-wrappers* (reads that are wrapped by choice, e.g. `list_keeps_for_member`, listed WITH a reason — the only
  hand-written part, and it is the safe set); the fault-injection invocation map grows the four new boundaries the
  same way (`_inject_store_error` already covers both sinks).

**3. STOP conditions.**
- `wrap_store_rejection` must re-raise a non-`SurrealStoreError` untouched (the a19b delete pins assert
  `PrincipalHasKeepsError` / `PrincipalOwnsGovernedRowsError` by class). If the seam converts everything, STOP:
  the `delete` wrap moves to the TXN call alone (inside the method, after the domain checks), never around the checks.
- The routed-set exact pin (`…test_the_routed_set_equals_the_invocation_map[principal]` / `[principal_key]`) reds on
  the four new wraps until its expectation is derived — the test-side commit lands FIRST with the derived expectation
  (RED on the four at fix3-as-is, by name), then the production wraps; never the reverse.
- The 58 catch-site scanner / fates: a `with wrap_store_rejection(...)` adds no `except` in the method (the seam owns
  the handler; translate-seam population, 58 am-7 §1) — no new row. If the scanner nevertheless reports a new
  handler keyed to `delete`, STOP and report; do not register a row for a site that is the seam's.
- If `principal_keys.py` is outside the builder's writable set for this fold, `revoke` goes into the pin as a
  DECLARED pending member (the §2 declared-pending-delta form: green with the declaration, red on a fifth, red when
  the wrap lands without clearing it), owner the next `principal_keys`-touching contract — named in the close-out.

## 13. Appended 2026-09-30 (operator: FOLD classes A–D into 63c-i-a before the commit; over coldaudit-4 `8026854` GO on `5f2d7c43`, blindreader-4 `da24013`, lead triage): four classes, each with property / domain / routing / chokepoint / pins / edits / STOP

Read from the fix5 tree (`…/e1f81771…/scratchpad/fix5`, patch md5 `5f2d7c43` verified). Test side lands FIRST in every
class (RED on fix5-as-is by name, GREEN after), production second, one commit each.

### A. The lore-adm error line teaches the cause (D-3 + F-3 + F-13)
- **PROPERTY:** *every served pointer resolves to a surface the consumer can open, and a fault line names its cause.*
  Today `lore-adm: could not delete principal 'x'` hides the reason in `__cause__`, and *"see the server log"* points
  at nothing: lore-adm configures no logging handler, so Python's lastResort prints the bare event name and DROPS the
  `extra` carrying `engine_error` (§7.3 receipt, line "governed.agent_backfill.rejected"). **DOMAIN:** the fault
  classes are the §11 tuple (derived from `_dispatch`'s `except`); the pointer set is the `_SERVER_LOG_HINT` uses.
- **Routing:** NEW property (nothing pins served pointers) → folded by operator grant as a builder requirement + ONE
  generated pin; no contract round.
- **ONE chokepoint, two halves, no text surgery:** (i) `main()` installs a stderr `logging.StreamHandler` at WARNING on
  the `loremaster` logger with a CLI-local stdlib formatter rendering `%(message)s` plus the `error_class` /
  `engine_error` extras when present — so in lore-adm *"the server log"* IS stderr and the hint becomes TRUE (the
  driver's message is built ONCE for MCP and CLI alike; the CLI does not rewrite it). (ii) the §11 handler renders the
  cause chain: `lore-adm: {error}` then one ` ← caused by: {cause}` per `__cause__` link (messages only, consecutive
  duplicates collapsed). F-3's six collapsed faults are thereby distinguished by their causes; F-13's three
  over-claiming wrap contexts ("already exists") are REWORDED neutral ("could not create principal …") because the
  typed cause (`unique violation — …`) now prints itself — no per-class message map in the seam.
- **Secret guard (checked):** the handler prints exception MESSAGES only; the driver's rejection message already
  carries the creds-free RPC `url` (printed today, §7.3), and the seam's `extra` keys are `url` / `error_class` /
  `engine_error` — no credential. `engine_error` may echo the operator's OWN bound values to the operator's own
  terminal: allowed (#31 protects MCP consumers, not the operator's stderr). Builder receipt: awk over every
  `logger.*(..., extra={...})` in `_txn`/`principals`/`keeps` for `password|token|secret` → zero hits.
- **Pin (generated over the §11 tuple):** inject each fault class with a chained cause at `ensure_ready` → stderr
  contains the cause message and, for a raw domain rejection, the `engine_error` text; `Traceback` absent; exit 1.
- **STOP:** the CLI tests that assert an exact stderr line (`test_principals_cli`, `test_keeps_cli`) → DUAL: the
  first line is unchanged, the cause line is appended; any pin asserting stderr has EXACTLY one line reds and is
  re-keyed in the same test-side commit.

### B. Fail-closed shapes — ONE policy (F-1, F-6, F-7, F-5)
- **PROPERTY:** *a driver answer in the wrong shape never decides a served value or a write; it raises the ONE class
  the CLI launders (`SurrealStoreError`), never a `TypeError`, never `0`, never `[]`.* **DOMAIN (derived):** every
  function in `principals.py` / `governed.py` whose body tests `isinstance(<result>, list|dict)` on a store result —
  an AST-derived set; the allowlist is exactly TWO helpers in `governed`: `group_all_count(result, noun)` (exists)
  and **`rows_of(result, noun) -> list[dict]`** (new): non-list → raise; a non-dict MEMBER → raise (F-7, no silent
  drop). A third shape-tester reds by name.
- **Routing:** the property is pinned for `group_all_count`'s callers (§10) → new cases: implementation requirement +
  the allowlist pin as the completeness assertion.
- **Production:** `_rows_stamped` = `len(rows_of(update_result, noun))` (F-6: `SurrealStoreError`, not `TypeError`);
  `_governed_select` = `rows_of(...)` (F-7); `delete`'s `cascaded` = `group_all_count(count_rows, noun=…)` (F-1);
  `_as_rows` (tolerant `[]` behind `revoke` / `set_*` / `delete`'s NotFound) = `rows_of` (a non-list after an UPDATE
  is a fault, not "not found"). **F-5:** the message leg's post-commit leftover read runs under
  `wrap_store_rejection(PrincipalStoreError, f"the backfill landed ({stamped} message row(s) stamped) but the
  leftover count read failed")` — a failure after a committed write names the write; class A prints the cause.
- **STOP:** any pin feeding `_as_rows` a non-list and expecting `NotFound` → DUAL re-key to the raise; any pin
  asserting `_rows_stamped` raises `TypeError` → re-key (its docstring already calls it a contract break, i.e. a
  store fault).

### C. Honest labels and prose (F-4, N-1, N-2/F-10, N-3, F-2, F-14, F-15)
- **F-4 — the field is RENAMED to what it measures; the receipt KEY changes.** It counts rows still
  `scope IS NONE AND owner_principal IS NONE` AFTER the UPDATE (a separate statement), a superset of "unsound
  sender". Field + receipt key: **`messages_left_unmigrated: int | None`**. stderr sentence: *"N message row(s)
  remain un-migrated after the backfill — commonly their sender has no owner or scope (re-run after `--table agent`
  for those); a row inserted during the run is counted here too."* `MigrateGovernedResult` docstring: the same fact.
  Retired-name sweep: BARE pattern `unsound_sender_messages` over tests, docs and the reference → zero hits (the
  fixup's CLI pins and §6/§8/§10 of this doc are the known sites; this doc keeps its history and gains this line).
- **N-3 / F-15:** `--table` help for BOTH verbs is DERIVED from `_MIGRATE_VALID_TABLES` (`", ".join(...)`), and
  `report-unmigrated` validates `--table` against it BEFORE any I/O through the SAME validator `migrate-governed`
  uses (one function; the interpolated statement never sees an unvalidated name). The "STUB / runnable-RED" docstring
  on `report_unmigrated_governed_rows` and its boot-"alarm" prose (N-1: it has no boot caller — its ONLY caller is
  the verb) are rewritten to what the code does. Pin: ∀ verb with `--table` (derived from the parser), an invalid
  table → refusal with zero store calls (spy) — generated, two rows today.
- **N-2 / F-10:** the four §12-wrapped methods' `Raises:` name their wrap error. **F-2:** `group_all_count`'s false
  universal reworded to its measured scope. **F-14:** `_dispatch_keep`'s docstring states the policy the code has:
  *write boundaries are the PINNED minimum; a verb path may wrap its reads too (delete, get_or_create_keyed do)*.
- **STOP:** a pin asserting the receipt line's bytes with the old key → DUAL re-key in the same test-side commit.

### D. The pre-boot schema teaching precondition (D-2)
- **PROPERTY:** *every precondition a leg's write needs is measured and TAUGHT before the first write.* On the dump as
  restored (no server boot) `INFO FOR DB` passes (the table exists) and the UPDATE is an opaque `unspecified
  rejection` (§7.3) — the #107 fixture law: every test mints a full-DDL virgin DB, so no pin could see it.
  **DOMAIN (derived, drift-proof):** the columns each leg's own `UPDATE … SET` statement assigns (parsed from the
  statement text the leg already declares — the same source as the write, never a parallel column list) ×
  `INFO FOR TABLE <table>`'s `fields` map.
- **Routing:** NEW property → folded by grant; builder requirement + generated pins; no counts-model field (STOP
  below).
- **Chokepoint:** ONE `INFO FOR TABLE <table>` read in `_agent_migration_preconditions`, immediately after the
  `INFO FOR DB` gate and before ANY leg read/write; the result rides `AgentMigrationPreconditions` as
  `defined_fields: frozenset[str]` beside `defined_tables`. The verb-level refusal (no leg runs), text: *"the
  `<table>` table has no `<c1>, <c2>` column(s) — this store's schema predates the governed columns; boot the new
  image once (its DDL defines them), then re-run migrate-governed"* (`table_defined=True`, counts `None` as ruled).
- **Pins (generated, ∀ leg × its derived columns), the dirty-store leg #107 demands:** on the minted DB run `REMOVE
  FIELD <col> ON TABLE <table>` for ONE column → the refusal names exactly that column and a store spy shows zero
  writes; positive control: all columns present → the leg proceeds. Plus a completeness leg: the derived column set
  per leg is non-empty and equals what a bare-pattern read of the statement finds.
- **Acceptance receipt:** YES — coldaudit-4 §7.3's dirty-store probe (dump as restored, no boot) is the acceptance
  receipt for D: the FIRST run must print the teaching refusal and exit 1; then §7.4's boot-then-migrate receipt is
  byte-identical to today's. The re-check audit re-runs both.
- **STOP:** `MigratePreconditionCounts` gains NO field (`_RULED_FIELD_SPEC` exact pin); the `defined_tables` shape pin
  (a28c) must accept a sibling field on the preconditions dataclass — if it asserts the dataclass's exact field set,
  DUAL re-key first; the one-read pin (undefined table → exactly one `INFO FOR DB`) is unchanged because the table
  read short-circuits BEFORE the field read.

### Residuals confirmed, each with its trigger
| id | residual | trigger |
|---|---|---|
| R-1 / F-8 | a teardown `close()` fault masks the verb's outcome (§11's nested `try/finally`) | a teardown fault observed in the field, or the next lore-adm-touching contract |
| F-9 | exit code 1 for every failure class (operator-deferred) | the first script consumer that branches on lore-adm's exit code |
| F-11 | the gate's unsymboled-allowance COUNT leg assumes one path/one bound (fails closed) | packet 64 / the gate owner (D-1 filed there) |
| F-12 | an untypeable per-statement ERR entry loses its typed meaning (§7 F-C8 policy) | a malformed/kindless entry observed on 3.2.4 |
| F-16 | receipt/default notes | with §W row 4 |
| GROUP ALL sweep (findings / tasks / messages / diff / store / manifest readers) | → 64b §DRY step, ONE `group_all_count` | 63c close-out decision point (§8.3, §10 erratum) |
| §W row 4 | derived-domain ladder pin · garbage-text cells · `QueryDetailKind` adjudication pin · exact-set AST re-key (FK-B1) · fixture capture | the next `_txn`-touching contract (58-r4 / close-out) |
F-13 is NOT a residual: folded via class A (neutral contexts + printed cause). D-1 → packet 64 (filed by the lead).

### 13.1 Addendum 2026-09-30 (lead, over fixup-tests-63c-i-a-2 ROUND 4 `04a4149`): B-D1 → a third allowlisted helper `map_of`; B-D2 confirmed; D-fork one span per column; the two store facts go into the reference now; the "derived, not hand-mapped" pin is required

1. **B-D1 — (a), and it is a FAIL-OPEN guard, so it is a fix, not a hygiene item.** `_table_exists` reads a non-dict
   `INFO FOR DB` as "no tables" → `delete` SKIPS SF-63-5's owned-row guard on a garbage answer — the same shape as
   §10.1(a). The §13 B allowlist grows to THREE helpers in `governed`, all fail-closed, all raising the ONE class:
   `group_all_count(result, noun)` · `rows_of(result, noun) -> list[dict]` · **`map_of(result, noun) -> dict`** (an
   `INFO FOR …` answer: non-dict → raise; the `tables` / `fields` sub-map non-dict → raise). Callers routed:
   `PrincipalStore._table_exists`, `_agent_migration_preconditions`' `INFO FOR DB` read (the cloned third policy is
   DELETED), and class D's `INFO FOR TABLE` read (born routed). The `xfail(strict=True)` pins become plain pins in the
   same test-side commit; the allowlist pin's expected set is the three names. STOP: none new — a test feeding
   `_table_exists` a non-dict and expecting "absent" is the fail-open behaviour itself and is re-keyed to the raise.
2. **B-D2 — CONFIRMED: `governed.authorize_guarded` routes its pre-read through `rows_of` in this fold.** A guarded
   write that decides "row absent" from a wrong-shaped pre-read is the fail-open shape on the governed write path
   itself; it raises instead. STOP: an F5 `_governed_contract` pin that constructs a non-list pre-read and expects
   the guard's ABSENT verdict → DUAL re-key to the raise (test side first); no other pin reads that branch by shape.
3. **D-fork — one backtick span PER column** (`` `owner_principal`, `scope` ``). Each column is an identifier; one span
   around a comma list would teach a single false identifier. The worker's pick stands.
4. **D store facts — YES, into `docs/reference/surrealdb-31-capabilities.md` in this commit, with the probe pasted
   verbatim in the builder report and the commit cited** (the reference exists so the next agent reads instead of
   probing; a probed fact left in a report is the #107 gap re-opened). Two entries beside the governed facts:
   (i) `INFO FOR TABLE <undefined>` returns EMPTY maps, not an error — so a table gate must read `INFO FOR DB`'s
   `tables` (the existing gate), never infer definedness from `INFO FOR TABLE`; (ii) an `UPDATE` assigning a REMOVED
   field on a SCHEMAFULL table is SILENT over 0 rows and raises over ≥ 1 row — which is exactly why class D's
   precondition is derived from the SCHEMA, never from the write's outcome: a pre-boot store with zero legacy rows
   would otherwise "succeed" silently and the next legacy row would fail later, out of context.
5. **D flag — the pin IS required; the audit's mutation proof is the receipt that the pin discriminates, not a
   substitute for it.** A hand column map and a derivation are indistinguishable by any positive test; they diverge
   only when the statement changes. So: a ONE-DERIVATION pin — the test parses the SAME statement constant each leg
   executes (bare pattern over `SET <col> = …` in the production string) and asserts the precondition's required
   column set EQUALS it, ∀ legs (generated over `_MIGRATE_VALID_TABLES`' legs). It reds the day a leg's `SET` gains a
   column the precondition does not require, permanently; the audit's scratch mutation (add a column to one `SET`)
   is run ONCE to prove this pin fires. The worker's reference stays a SAT host, never a spec.

### 13.2 Addendum 2026-09-30 (lead, over builder-63c-i-a-fix6 FORK-1 `c8c3435`): reading B ACCEPTED — the schema gate is the leg's first act; `_verb_level_refusal` may precede it, and every refusal it can serve on a schema-behind store is TRUE

**Accept B.** §13 D's "verb-level (no leg runs)" meant *no leg READ or WRITE runs*; it did not require the gate to sit
lexically above `_verb_level_refusal`. Under §13.1 item 5 (columns derived from the leg's own statement) and
`test_memory_enforcement_63b_ia.py` §1.9 (the statement is a FUNCTION-LOCAL literal, no module constant, no helper),
the only place that can derive the columns is the leg — so the leg building its literal first and refusing before
any read, mint or operator resolution IS the ruled chokepoint. Hoisting the literal to satisfy a lexical ordering
would break §1.9 for an ordering that changes nothing false into something true.

**Why the ordering is harmless, by construction:** every `_verb_level_refusal` teaching is schema-INDEPENDENT truth —
a dangling sender (a `sender` pointing at no agent) and the agent-first order (agents still unscoped) exist whether or
not the governed columns are defined, and a half-pair (`scope` set, `owner_principal` NONE) CANNOT exist on a
pre-boot store (the columns are absent, every read is NONE). So a schema-behind store with a verb-level problem is
told a true prerequisite first and "boot the new image" on the next run; never a false teaching, never a write.
The precondition READS on a pre-boot store do not raise (measured: coldaudit-4 §7.3's first run passed every
precondition read and failed only at the UPDATE).

**§7.3 acceptance HOLDS under B:** on the dump as restored, after the operator bootstrap, `--table agent` has no
verb-level refusal to serve (agent-first is moot for agent; no half-pairs possible), so the FIRST run's first refusal
is the schema teaching, exit 1 — the acceptance receipt as written. Rider for the re-check audit: run `--table
message` on the same pre-boot dump too and record which teaching arrives first (expected: agent-first order) and that
the schema teaching arrives on the run after `--table agent`; both lines are receipts, neither is a defect.
Bound, stated in the leg docstring: *"a verb-level refusal may precede this gate; each such refusal is true
independently of the schema, and this gate runs before any leg read or write."*

### 13.3 Addendum 2026-09-30 (operator: the FINAL capped round; lead, over blindreader-5 `585388f` + coldaudit-5 `4774cce`, build `bec29190`): nine items ruled; after this round's delta audit anything below MAJOR is a residual

Read from `…/9744862d…/scratchpad/build-fix6` (patch md5 `bec29190` verified) and `logging_setup.py` at HEAD (untouched by the patch).

1. **F-1 (MAJOR, latent) — `_set_columns` narrows silently.** PROPERTY: *∀ statement, the parse is COMPLETE or it
   RAISES — never a subset.* DOMAIN: the three leg statements (function-local literals, §1.9) + the corpus. Parser
   shape, ONE scanner (no regex end-split beside a char loop — two grammars for one clause is how the narrowing got
   in): a single depth- AND quote-aware pass over the text after the top-level `SET`; `(`/`)` depth and `'`/`"`
   string state tracked together; an end keyword (`WHERE`/`RETURN`/`TIMEOUT`/`PARALLEL`) ends the clause ONLY at depth
   0 outside quotes; a comma splits ONLY at depth 0 outside quotes; at end-of-clause RAISE if depth ≠ 0, if a quote is
   open, or if the trailing item is non-empty without `<col> =`. Pins: (a) the corpus pin — every blind-reader-5 case
   (subquery-with-WHERE, `RETURN` inside a call, `SET` inside a string before the real SET, an unbalanced `)` in a
   string, `+=`, a quoted comma) asserts *exact expected set OR a raise, never a subset* (the subset assertion IS the
   property); (b) the shipped three parse to their exact sets; (c) the existing §13.1 one-derivation pin + mutation E
   stand. **A corpus alone is a hand-list; it is enough HERE only because (c) exists** — no new mutation beyond E.
2. **F-2 (MAJOR; operator-ruled).** (i) The CLI sink routes through THE seam: `_cli_logging` does
   `handler.addFilter(RedactingFilter())` exactly as `configure_logging` does — `RedactingFilter` already scrubs
   `msg`, `args` and EVERY extra (`engine_error` included) through `_scrub_text`/`_scrub_value`; no second redaction.
   (ii) `_fault_line` renders each message (the error's and every cause's) through the SAME scrub function the filter
   uses — promote `logging_setup._scrub_text` to a public `scrub_text` (one name, the filter calls it too), never a
   private import, never a second regex. (iii) The key-mint hash: the only surface that can carry it is the seam's
   `engine_error` extra on the mint rejection (the raised label never echoes; the typed cause is the label). Rule
   **the scrub learns the credential-hash SHAPE**: a 128-hex-character run (sha512 hex, `sha512_hex(f"{name}:{secret}")`)
   is redacted by `scrub_text` wherever it appears — ONE place, every sink, every cause line, no per-seam flag.
   Verification the builder owes: awk for every `sha512` producer in the package; if a 128-hex run is ever a legitimate
   content hash in a served line, the pattern narrows to the mint seam's record (the seam passes `secret_params=
   {"hash"}` and the driver withholds `engine_error` when a secret param's VALUE appears verbatim in it) — say which.
   Receipt for the delta audit: a live mint collision on `:18000` → stderr (log line + cause lines) contains no 128-hex
   run; control: the same with the scrub disabled shows it.
3. **#527:** a `seen` set of `id(exc)` on the `__cause__` walk (stdlib `traceback` shape); **`__cause__` ONLY** — the
   seams chain explicitly with `from error`, and `__context__` is the implicit "during handling of" link that would
   duplicate or mislead. Pin: the 2-cycle cell terminates with each message once + the control chain unchanged.
4. **#528:** validation moves INTO `report_unmigrated_governed_rows` (the §13 C ONE validator, called there), so the
   docstring makes NO caller claim; `_dispatch_report_unmigrated` keeps its pre-I/O call of the same validator (zero
   I/O on a typo). `scripts/restore_prod_dump.py` is covered by construction.
5. **F-3 + the audit's F-5 sibling — ONE chokepoint, no per-site text:** `rows_of(result, noun, *, landed: bool =
   False)`; with `landed=True` the ONE template reads *"the {noun} LANDED (committed) but answered a {type} instead
   of its rows — nothing was decided from the answer; a re-run is idempotent"*. DOMAIN (derived, §12's write-sink
   derivation): every shape read whose input is the result of a write sink. Generated pin: ∀ write boundary ∈ the
   three stores' derived write sets (+ the three legs' `_rows_stamped`), its post-write shape reader is called with
   `landed=True`; a boundary whose post-read lacks it reds by name. KeepStore's six `_as_rows` post-write sites are in
   the domain by derivation, not by list.
6. **F-5:** the remedy is DERIVED from membership: `table ∈ _MIGRATE_VALID_TABLES` → *"run `lore-adm migrate-governed
   --table <t>`"*; else → *"no migrate verb accepts `<t>` yet — N row(s) remain unscoped"*. Generated pin: ∀ table the
   report validator accepts, the rendered remedy either names a table the MIGRATE validator accepts or names none.
7. **F-6:** `_as_rows` loses its default `noun` (it is `rows_of` underneath; `noun` keyword-only, required) — every
   caller names its read. Pin (AST, generated over call sites): no call to `rows_of`/`_as_rows`/`map_of`/
   `group_all_count` without `noun=`.
8. **F-7 — pick: the defect class moves OUTSIDE the tuple.** `_set_columns`' raises (and F-1's new ones) become
   `GovernedStatementError(RuntimeError)` — a leg statement the gate cannot read is OUR bug and must TRACEBACK (the
   honest-developer gate), exactly as `_dispatch`'s docstring already says. `ValueError` stays in the tuple for the
   `--name` CLI-input check it was listed for. Pin: `GovernedStatementError` ∉ the handler tuple (AST), and an
   unparsable literal reaches `main()` as a traceback (control: a `ValueError` still launders).
9. **NITs #19 / #21 / #31 — FOLD** (prose and a hand-list in files this round already edits): #19 the agent-leg
   "(below)" direction; #21 the message-leg comment ("sender-skipped only" → the F-4 fact); #31 `_not_supported`
   derives its table list from `_MIGRATE_VALID_TABLES` (the derived-prose class). N-1/N-2/N-3 (duplicate engine text,
   `propagate`, the "wrote nothing" docstring vs `ensure_ready` DDL) → residuals, listed with the close-out.

**Delta-audit scope — CONFIRMED, plus two receipts:** the new changes above; the OWED mutation proofs (§A.12b A–E,
E = the §13.1 one-derivation mutation); a short contract-blind read; AND (a) the §13.2 rider (`--table message` on
the pre-boot dump, both teachings' order), (b) item 2's mint-collision secret receipt with its control. STOP for the
whole round: a finding below MAJOR after the delta audit is a residual by operator ruling — the audit records, the
lead ledgers, nobody re-opens.

### 13.4 Addendum 2026-10-01 (lead, over builder-63c-i-a-fix6 §RESUME 2 `b03423f`): §13.3 item 4 broke the restore read-back — erratum mine; the REPORT verb's domain is the GOVERNED set (derived from the slice deriver), the MIGRATE verb's is the leg set; ONE validator function, two derived domains

**Erratum (mine, §13.3 item 4):** *"`scripts/restore_prod_dump.py` is covered by construction"* was written without
reading what tables the restore passes. It passes every `governed_node=True` table of `SliceDeriver().governed_slice()`
(`agent, brief, finding, memory, message, task`); `_MIGRATE_VALID_TABLES` holds four of them, so the validator I moved
into the function raises on `finding` and `task` and the S2 restore's default read-back FAILS. A regression this round
introduced; the operator's cap does not cover it. Quantifier law: a domain derived on one caller (the CLI verb),
stated over every caller.

**Ruling — (B), with the domain DERIVED, not listed.** Two verbs, two questions, two domains:
- **REPORT** asks *"how many rows of a governed table are unscoped?"* — its domain is the GOVERNED SET: every table
  whose schema carries the governed triple. Source of truth: the SAME one the restore uses —
  `SliceDeriver().governed_slice()`'s `governed_node=True` tables (derived from the DDL generators; no second hand
  list). `governed.py` exposes it ONCE as a derived accessor (`governed_tables()`), and `report_unmigrated_governed_rows`
  validates against THAT.
- **MIGRATE** asks *"which tables have a backfill leg?"* — `_MIGRATE_VALID_TABLES` (the leg set, a strict subset).
- **ONE validator function, parametrised by domain** (`validate_governed_table(table, *, domain, verb)`), called by
  both verbs and by the report function itself; the refusal text names the verb and its domain (derived `", ".join`).
  `_dispatch_report_unmigrated`'s pre-I/O check uses the REPORT domain through the same function (zero I/O on a typo
  is preserved; `finding`/`task` pass). §13.3 item 6's remedy derivation already handles the non-migratable members
  (*"no migrate verb accepts `finding` yet — N row(s) remain unscoped"*), so the restore's read-back serves its two
  counts AND an honest remedy. Option (C) is refused: it drops two served counts to dodge a validator that was simply
  pointed at the wrong set.

**Pins (test side first):**
1. Generated: ∀ table ∈ `governed_tables()` (derived at test time from the slice deriver, never from a list),
   `report_unmigrated_governed_rows(handle, table)` ACCEPTS it (a minted full-DDL DB; the count returns an int);
   control: a table outside both domains (`principal`) → the validator's refusal with zero store calls.
2. Containment: `set(_MIGRATE_VALID_TABLES) ⊆ governed_tables()` — a leg for a non-governed table is a defect.
3. A restore read-back cell: `restore_prod_dump._read_back` over a minted DB with every governed table defined
   completes without raising and renders one line per governed table (the "scope NONE" column the operator saw).
4. The F-15 pin's "invalid table" sample for `report-unmigrated` must lie outside BOTH domains; if it used `finding`
   or `task`, DUAL re-key in the same commit.

**STOP conditions:** an import cycle `governed.py` → the slice deriver (then the accessor lives beside the deriver
and `governed.py` imports lazily, the house PLC0415 idiom — never a copied list); any pin asserting the report verb
REFUSES a governed-but-unmigratable table (re-key, it is the regression); the §13.3 item 6 remedy pin must stay
green over the WIDER report domain (it is written over "every table the report validator accepts", so it widens by
derivation — verify, do not assume).

#### 13.4.1 Erratum 2026-10-01 (lead): §13.4 pointed the dependency the WRONG way — `SliceDeriver` lives in `scripts/restore_prod_dump.py`, which is not a workspace member and is ABSENT from the image

**Erratum (mine, §13.4):** I had production `governed.py` derive `governed_tables()` FROM `SliceDeriver`, and the STOP
clause told the builder to import it lazily. `scripts/` is not packaged; that import passes every host test and raises
`ImportError` in the deployed image only — #131/#139 verbatim, "THE TEST ENVIRONMENT IS A FICTION", in a ruling
written the day after I cited it. Superseded as follows; everything else in §13.4 (two derived domains, ONE validator
function, the four pins, option C refused) stands.

- **The ONE source of truth is PRODUCTION.** `governed.py::governed_tables()` derives the governed set DIRECTLY from the
  DDL generators / schema — the SAME property `SliceDeriver` computes (*tables whose DDL defines the governed triple*),
  computed once, in the package, from the generators the image ships. No import crosses from `loremaster/` into
  `scripts/`, lazily or otherwise.
- **`SliceDeriver` CONSUMES `governed_tables()`** (`scripts/` may import `loremaster`; never the reverse) — the
  stronger of the two options, because it leaves ONE implementation of the property rather than two that a pin keeps
  equal. The equality pin is still written as the transitional receipt: `SliceDeriver().governed_slice()`'s
  `governed_node=True` set `== governed_tables()` — green the day the deriver consumes it, and it stays as the guard
  that nobody re-derives the set in the script later.
- **AST pin (generated over every module under `loremaster/loremaster/`):** no `Import` / `ImportFrom` names `scripts`
  or `restore_prod_dump` (bare name match, any alias, any depth — including inside functions, which is where my STOP
  clause would have put it). Positive control: a synthetic module with a function-local `from scripts.x import y` is
  caught. This is the in-image conformance guard's static twin: the runtime guard (#139) proves the artifact, this
  one catches the honest-developer import before it ships.
- **STOP, restated:** NO production import of `scripts/`, in any form. If `governed_tables()` cannot be derived from
  the generators without a cycle, the derivation moves to the lowest package module that already imports the
  generators — never to `scripts/`, never to a list.

#### 13.4.2 Addendum 2026-10-01 (lead, over fixup-tests-63c-i-a-2 ROUND 7 R7-1 `f94ec2f`): the governed set = DDL-derived ∪ a DECLARED pending set that self-destructs — CONFIRMED, with one render rider

**Measured conflict accepted:** the DDL carries the governed triple on `agent`, `memory`, `message` only; `brief`,
`finding`, `task` are governed-by-intent (63c-ii / 64) with no triple yet. A pure derivation cannot name them, and
the restore legitimately reports them. So the set has two parts, and the second is the honest kind of hand-list —
a DECLARED allowlist with a reason per member and a completeness pin that empties it by construction (the §2
declared-pending-delta form, applied to a table set):
- `governed.py` owns **`PENDING_GOVERNED_TABLES: Mapping[str, PendingGoverned]`** (moved from `scripts/`; each entry
  carries `reason` AND `owning_packet`) — in the package, so the image ships it and `scripts/` consumes it.
- `governed_tables()` = `ddl_governed_tables()` (derived) ∪ `PENDING_GOVERNED_TABLES.keys()`; the REPORT validator's
  domain is this union; the MIGRATE domain is unchanged (`_MIGRATE_VALID_TABLES ⊆ ddl_governed_tables()` — a
  tightened containment pin: a leg for a PENDING table is a defect, its columns do not exist).
- `SliceDeriver` consumes BOTH from `loremaster`; the equality pin (`governed_node` set `== governed_tables()`) stands.
- **SELF-DESTRUCT pin:** `ddl_governed_tables() ∩ PENDING_GOVERNED_TABLES.keys() == ∅`, named by member — the day
  63c-ii / 64 lands a table's triple, the pin reds until the entry is deleted; the declared set can only shrink.
  Positive control: a synthetic generator that defines the triple on a pending name reds the pin.
- The AST no-`scripts`-import pin (§13.4.1) is unchanged.

**Render rider (consumer law):** on a PENDING table every row reads `scope IS NONE` (the field is undefined, so each
read is NONE) — the served count is TRUE but would teach "N rows need migrating" when nothing can migrate them. The
report's remedy for a pending member is DERIVED from its entry: *"`<table>` has no governed columns yet (<reason>;
packet <owning_packet>) — N row(s) will be scoped by that packet's migration"*; for a DDL-derived table the §13.3
item 6 derivation stands. Generated pin: ∀ member of the union, the remedy names either an accepting migrate verb
or the pending entry's packet — never a verb that refuses, never silence. STOP: none new; the restore read-back cell
(§13.4 pin 3) now also asserts the pending remedy line for `finding` / `task`.

### 13.5 Addendum 2026-10-04 (operator: ONE handler around `mint`'s post-write path, then stop; lead): the handler is a class-preserving `add_note` passthrough over a window that starts at the CREATE CALL; the remedy has exactly one home and two wordings

**PROPERTY (as the lead states it, sharpened):** *every `mint` fault raised once the CREATE MAY have committed carries
the revoke repair — CERTAIN wording when the engine answered, CONDITIONAL when the outcome is unknown; a fault that
PROVES no key landed carries none.* DOMAIN: every raise point from the `_query(statement)` call through
`_row_to_key(rows[0])` (derived: every statement of `mint` after the statement is built).

1. **The window and the transport case.** The window opens at the CREATE **call**, not its return: a
   `SurrealConnectionError` raised DURING the await is the one pre-commit fault whose outcome is unknown (the engine
   may have committed and the answer been lost) → CONDITIONAL wording. Every OTHER pre-commit fault proves no key:
   `TxnDomainRejectionError` and subclasses (the engine evaluated and refused — UNIQUE included),
   `TxnContentionExhaustedError` (rolled back), `TxnParamCollisionError` / `TxnEnvelopeViolationError` (raised before
   sending) → NO remedy. After `_query` returns, EVERY fault (wrong shape, no row, each missing column, a programming
   defect) → CERTAIN wording. Allowlist the safe: pre-commit, exactly ONE class gets the (conditional) note.
   **HOW, without masquerade or class loss — PEP 678 `add_note`:** the handler is
   `except BaseException as error: error.add_note(<remedy>); raise` — a bare re-raise of the SAME object. A transport
   fault stays `SurrealConnectionError`, a store fault stays its class, `wrap_store_rejection` (outside the window)
   still translates domain rejections exactly as today. `_fault_line` gains one render: after the error's message
   and before the cause lines, one ` ↳ ` line per `__notes__` entry; Python's own traceback renderer already prints
   notes, which is what makes item 3 work.
2. **UNIQUE rejection = no key landed → NO revoke advice.** CONFIRMED by construction: it is a pre-commit
   `TxnDomainRejectionError`, excluded from the note; the existing wrap serves *"could not mint key …"* with the typed
   cause.
3. **F-7 tension — resolved by the note, not by laundering.** A `KeyError`/`TypeError` inside the window keeps its
   class and TRACEBACKS (§13.3 F-7 stands: our bug is visible as a bug), and the traceback prints the attached note,
   so the operator still reads the certain revoke remedy. No `PrincipalKeyStoreError from` the defect.
4. **58's exhaustion-fates registry — NO row: the handler is a PASSTHROUGH by construction** (bare `raise` of the
   same object; `add_note` mutates, it does not translate, chain or swallow). Exhaustion never even receives a note
   (pre-commit, excluded). Expected classification by 58's `derived_fate`: passthrough. STOP: if the classifier
   reads the `add_note` call as a non-passthrough exit, the lead routes the CLASSIFICATION question to 58 — no row
   is invented here.
5. **The two per-error messages fold into the ONE handler.** `_as_rows(..., remedy=)` (from `28395e0`) is DELETED —
   the landed template is the generic one; the no-row raise (`b90bd4b`) becomes
   `PrincipalKeyStoreError("key {name!r} for principal {email!r}: the mint answered no row")` with no remedy text.
   The remedy lives in exactly one place — the window's note — built from `_revoke_command` (kept, ONE helper):
   CERTAIN: *"the CREATE committed but the secret was never shown — key {name!r} is LIVE with no holder; revoke it
   (`{cmd}`) and mint a new key"*; CONDITIONAL: *"the mint's outcome is unknown (the connection failed during the
   CREATE) — if `lore-adm list-keys --email {email}` shows {name!r}, revoke it (`{cmd}`) and mint a new key"*.
6. **Pins.** (a) Generated ∀ raise point × zone: inject at `_query` a transport fault → conditional note, class
   unchanged; a domain rejection / exhaustion / param collision → NO note; inject after return: wrong shape, no row,
   row missing `created_at`, row missing each of `id` / `principal` / `name` (`KeyError` → the note appears in
   `traceback.format_exception` output and the class is `KeyError`) → certain note. (b) UNIQUE collision live on
   `:18000` → `PrincipalKeyStoreError`, no note, no `revoke-key` substring anywhere on stderr. (c) AST "one handler":
   exactly ONE `except` in `mint` calls `add_note`; its `try` body spans from the `_query` call to the `return`
   (no statement of `mint` lies after the `try`) — the window-covers-the-whole-path completeness leg. (d)
   `_fault_line` renders `__notes__` (one cell, with a no-notes control). STOP: a pin asserting the OLD remedy text in
   `_as_rows`' message or the no-row message → DUAL re-key to the note (same commit, test side first).

## 14. Appended 2026-10-04 (lead-63c-2, operator-directed: three design questions). Recommendations only — the operator rules

### Q1 — the mint CREATE cancelled in flight: YES, the conditional note; the domain is the PROVEN-no-key set, not a list of unknowns (erratum mine, §13.5 item 1)
**Recommendation:** cancellation (`asyncio.CancelledError`, an anyio cancel, `TimeoutError`, `KeyboardInterrupt`)
arriving while the CREATE is in flight gets the CONDITIONAL note. The request may have reached the engine exactly as
with a dropped socket; the outcome is unknown; the operator needs the same `list-keys`-then-revoke teaching.
**Reasoning / the lifted CLASS:** §13.5 item 1 wrote *"allowlist the safe: exactly ONE class gets the conditional
note"* — I allowlisted the wrong side. The SAFE set here is the set of faults that PROVE no key landed, and that set is
FINITE and DERIVABLE: the driver's own refusals and pre-send faults — `TxnDomainRejectionError` (+ subclasses, UNIQUE
included), `TxnContentionExhaustedError` (rolled back), `TxnParamCollisionError`, `TxnEnvelopeViolationError` — i.e.
`_txn`'s `SurrealStoreError` taxonomy MINUS the connection class. The "unknown outcome" set is UNBOUNDED (transport,
cancellation, interrupts, timeouts, a future SDK routing error) and must never be enumerated. So the rule inverts:
**pre-answer, the note is WITHHELD iff the fault is a member of the proven-no-key set; every other fault gets the
conditional note.** `_mint_fault_note`'s `isinstance(error, SurrealConnectionError)` becomes
`not isinstance(error, _PROVEN_NO_KEY_FAULTS)` — one tuple, derived in `_txn` (the taxonomy minus
`SurrealConnectionError`) and exported, so a new `_txn` subclass is adjudicated at birth. `except BaseException` already
catches cancellation; `BaseException.add_note` exists on it; the bare `raise` preserves cancellation semantics.
**Pin / rider:** fix531d's pin (a) is RE-KEYED by DUAL: its `CancelledError → no note` control flips to `→ conditional
note, class unchanged`; the generated taxonomy leg asserts ∀ `_txn` subclass: proven → no note, connection → note; plus
cells for `CancelledError`, `KeyboardInterrupt`, `TimeoutError`, an `anyio.CancelScope` cancel → conditional note.
Completeness: `_PROVEN_NO_KEY_FAULTS ∪ {SurrealConnectionError}` == the `_txn` taxonomy (derived) — a new subclass
nobody adjudicated reds by name. STOP: none (the handler shape, the fates passthrough and the UNIQUE no-advice pin are
untouched).

### Q2 — #486 R2's bound: (c)+(d) — keep anyio as the GRACEFUL inner bound and add a HARD outer bound from the stdlib, pinned by a subprocess cell; (a) and a bare (b) are refused
**Recommendation:** keep `anyio.fail_after` (it preserves pytest's verdict and the loud line for every cooperative
hang, measured 4/4), and wrap the session-end reap in **`faulthandler.dump_traceback_later(2 × budget, exit=True)`**
(stdlib; cancelled with `cancel_dump_traceback_later()` on the way out). It is a watchdog THREAD that needs no
cooperation from the hung code: on expiry it dumps EVERY thread's traceback to stderr and `_exit(1)`s. That is a
hard bound WITH forensics — strictly better than the old daemon thread, which abandoned the hang and told nobody
where it was.
**Reasoning / the lifted CLASS:** *a bound is a bound only over the behaviours it can interrupt; a cooperative bound's
reach is the cooperativeness of the path it guards — a hidden constant unless a non-cooperative outer bound exists.*
Option (a) leaves `pytest_sessionfinish` able to hang the whole fleet's gate on one `to_thread`. Option (b) alone — a
pin that the reap path has no sync call / shield / `to_thread` — is a name-list of the FORBIDDEN (the instrument
lesson's eighth defeat: the next blocking primitive has a name the pin does not know). Option (d) as "restore the
daemon thread" re-abandons. (c)+(d) enforces at the STATE (the process cannot hang past 2×budget) and keeps the
graceful path primary.
**Pin (exact):** a SUBPROCESS cell (the bound kills the process, so it cannot run in-process): `pytest_sessionfinish`'s
reap monkeypatched to a SYNC `time.sleep(10 × budget)` with a small budget → the child exits non-zero within
`2 × budget + ε` and its stderr carries `faulthandler`'s dump naming `_reap_within_budget`; CONTROL: the reap replaced
by a cooperative never-answering await → the child exits 0 within `budget + ε` with the existing loud
"no answer within the …s session-end reap budget" line and the verdict intact (anyio got there first). Both legs
declared before the run. The F-a re-open trigger is thereby retired: a non-cancellable block is no longer a bound,
it is a dumped stack. Secret/hygiene: the dump is stack frames only; the test store's URL already prints.
Lead note: coldaudit-486-3 judges the build; this is the design answer, and the pin is a test-tree change for #486's
implementer.

### Q3 — the un-awaited `_empty_subscription`: NOT a false clear of the pin's own claim; a FIXTURE-SHAPE defect that kills the success leg and a `suppress(Exception)` that hides it. Fix in the next test-side fix-up (test file only); ledger the production branch
**What I read (no pytest run; `:18000` not touched):** the fake's `subscribe_live` is `async def … return
_empty_subscription()`, and `_empty_subscription` is ITSELF `async def` returning the generator — so after production's
one `await`, `subscription` is a coroutine OBJECT, `async for` over it raises `TypeError`, `contextlib.suppress(
Exception)` swallows it, and the never-awaited coroutine is what the `RuntimeWarning` reports. The installed SDK's
`subscribe_live` is `async def … -> AsyncGenerator` (a coroutine returning the generator — MEDIUM: taken from
production's own comment, not re-derived from the SDK body); the fake is one level deeper than the thing it fakes.
**Verdict:** the pin asserts `subscribe_live` was attempted exactly 4 times (3 conflicts + 1 success) and that count IS
reached — the retry property it claims is genuinely exercised, so it is not a false clear OF THAT CLAIM. But (i) the
success leg (`async for` + `_drain_pending`) is dead in this test — a build that retries and then cannot iterate the
subscription passes; (ii) `suppress(Exception)` is a probe without a control: it also swallows the fake's own
`AssertionError("unbounded retry")`, leaving the `== 4` equality as the only guard; (iii) production's comment
("an async-generator FUNCTION under the test fake") describes a fake that does not exist — the `inspect.isawaitable`
branch is shaped by a test, and that test is wrong about itself.
**Fix (test file only, `test_retry_seam.py`, the next 63c test-side fix-up; ~6 lines):** `_empty_subscription` becomes
a plain function returning `_iterator()` (the SDK's success SHAPE: coroutine → async generator, one level); delete
`suppress(Exception)` — the consume returns cleanly on an exhausted iterator (`_drain_pending` then meets the fake's
`query`, which conflicts 3× and answers `[]`) — any exception is a real red; add the warning as an error for this test
(`pytest.warns`-free: `filterwarnings("error::RuntimeWarning")` on the test) so the fixture shape is pinned. **Ledger
(not 63c's file):** `scout._consume_live`'s "await it if awaitable" branch and its comment — re-derive from the SDK
body whether the branch is live in production; if the SDK returns the generator directly, the branch is dead code
shaped by a wrong fake and goes with the next scout-touching contract. CLASS: *a fake's success shape equals the
dependency's, and a pin never suppresses the exception class it exists to notice.*

## 15. RULED 2026-10-05 (operator directive: the sidecar rules forks; lead-routed) — coldaudit-mint-q1 R-1: `TxnDomainRejectionError` is NOT uniformly "proven no key"; the OUTCOME-UNKNOWN kinds are carved out by TYPE, safe side, with a re-open trigger

**Evidence, in the ruled order.** Lore MCP: still `ECONNREFUSED` this session — the on-disk reference was used. The
store reference carries NO per-kind commit-timing fact for a single statement (it states `TimedOut` is substantive
and `Cancelled` is a cascade notice — nothing about whether either can follow an implicit commit). The engine specs
and vendor docs were not reachable in the budget, and **no client-side probe can construct the state in question**: a
post-commit `Serialization` / `Internal` / `TimedOut` is raised by the engine after it has already persisted the row,
so a probe can only observe it by luck, never force it. **Undecidable quickly → option (c), the safe side.**

**Ruling (b)/(c): carve the kinds whose TIMING the kind itself does not prove out of the proven set.** Adjudication
over the SDK's own enumerations (`KIND_TO_CLASS` top-level kinds; `QueryDetailKind` for `Query`):
| kind | adjudication | why |
|---|---|---|
| `Validation` (parse), `Thrown` (our governed guard aborts the txn), `AlreadyExists` / UNIQUE, `NotFound` (table/record), `Configuration`, `Query:NotExecuted` | **proven no key** | raised at or before the write's evaluation, or as its refusal / rollback |
| `TransactionConflict` (→ exhaustion), `TxnParamCollisionError`, `TxnEnvelopeViolationError` | **proven no key** | rolled back / never sent (unchanged) |
| `NotAllowed`, `Connection` | transport (already conditional) | unchanged |
| **`Internal`, `Serialization`, `Query:TimedOut`, `Query:Cancelled`** | **OUTCOME UNKNOWN → conditional note** | the kind does not prove the fault preceded the implicit commit: result encoding is post-execution; an internal error or a timeout can fire during commit |

**Mechanics (ONE place, typed):** the ONE mapping helper `_domain_rejection_error` already receives the typed error;
`TxnDomainRejectionError` gains a typed `kind: str | None` attribute set there (never parsed from text). `_txn`
exports **`proven_no_key(error) -> bool`** — a PREDICATE, not a tuple: `isinstance(error, (TxnContentionExhaustedError,
TxnParamCollisionError, TxnEnvelopeViolationError))` or `isinstance(error, TxnDomainRejectionError) and error.kind
not in _OUTCOME_UNKNOWN_KINDS`, where `_OUTCOME_UNKNOWN_KINDS = frozenset({"Internal", "Serialization",
QueryDetailKind.TIMED_OUT, QueryDetailKind.CANCELLED})` (SDK constants where they exist). `_mint_fault_note` calls
the predicate; the class tree is untouched (no new class, every `except TxnDomainRejectionError` door unchanged;
no new catch site, no fates row). A kind-less rejection (`kind is None` — a bare-text input) is UNKNOWN (safe side).
**Pins:** (i) generated over `KIND_TO_CLASS ∪ QueryDetailKind`: every kind is adjudicated proven / unknown /
transport by the table above — an unadjudicated kind reds by name (completeness); (ii) mint cells: a
`TxnDomainRejectionError` of kind `Internal` / `Serialization` / `TimedOut` / `Cancelled` during the CREATE →
CONDITIONAL note, class unchanged; of kind `Validation` / UNIQUE → NO note (the live UNIQUE pin stands); (iii)
`proven_no_key` is the ONE predicate (mutation: flip one member of `_OUTCOME_UNKNOWN_KINDS` → the mint cell moves).
**Bound and re-open trigger:** the carve-out is the SAFE side of an unmeasured fact, not a measurement. Trigger: a
vendor/spec statement (or a reproduced observation) of per-kind commit timing for single statements — then a kind
moves between rows by evidence, and the reference gets the fact. A conditional note on a fault that was in truth
pre-commit costs the operator one `list-keys`; the reverse costs a live credential. That asymmetry is the ruling.

### 15.1 RULED 2026-10-05 (lead; N-3 gap): ONE predicate decides catch, message AND note — option (i): the seam's `catch=` accepts the predicate

**The contradiction:** with `catch=_PROVEN_NO_KEY_FAULTS` (a class tuple) a `TxnDomainRejectionError(kind="TimedOut")`
is still translated to *"could not mint key …"* while §15's predicate attaches the conditional note — a message that
claims a refusal beside a note that says the key may be live. N-3 (the message must agree) is violated by having TWO
deciders: classes for the catch, the predicate for the note.

**Ruling — (i).** `wrap_store_rejection(..., catch=)` (and the `lorerunes.reclassify` primitive beneath it) accepts a
`Callable[[BaseException], bool]` as well as the class tuple; the mint's inner wrap passes `catch=proven_no_key`. Then
by construction: a fault the predicate PROVES no-key is translated to `PrincipalKeyStoreError("could not mint key …")`
and gets NO note (the outer handler asks the same predicate); a fault it does not prove passes the wrap UNTOUCHED —
its own class (`TxnDomainRejectionError` of kind `TimedOut`, `SurrealConnectionError`, a cancellation) — reaches the
outer handler, gets the CONDITIONAL note, and is laundered by §11's base-class catch with the DRIVER's own message
(the typed label + hint), which claims nothing about minting. One predicate, three consequences, no second site.
(ii) is refused: it keeps the catch keyed on classes and the message on the predicate — the same two deciders, moved.
Adding predicate support to `lorerunes` is a capability decision, taken deliberately: *catch-by-property* is a
general need (every door that catches "the faults I can explain" rather than "these classes"), and a predicate catch
is the allowlist-the-safe form of a catch tuple.

**`_PROVEN_NO_KEY_FAULTS` is REPLACED by the predicate as the public target.** The class half survives only INSIDE
`proven_no_key` as the private `_PROVEN_NO_KEY_CLASSES` (exhaustion, param collision, envelope violation), beside the
kind half (`TxnDomainRejectionError` with `kind ∉ _OUTCOME_UNKNOWN_KINDS`). The Q1 completeness pins re-target
`proven_no_key`: the taxonomy leg asserts ∀ `_txn` subclass × ∀ adjudicated kind → the predicate's answer equals the
§15 table; the mutation leg flips one member of either half by name and watches the mint cell move.

**Pins:** (a) lorerunes: `reclassify` honours a predicate catch (translates iff true; passes through untouched iff
false), with the tuple form unchanged (DUAL control); (b) mint, ∀ kind cell: `proven_no_key` TRUE ⇒ the raised class
is `PrincipalKeyStoreError`, its message starts *"could not mint"*, no note; FALSE ⇒ the class is the fault's own,
the note is present, and the substring *"could not mint"* appears NOWHERE in `_fault_line` output or
`traceback.format_exception` (N-3's assertion, byte-level); (c) the AST one-handler pin is unchanged. STOP: a pin
asserting the inner wrap's `catch=` is a tuple by AST → re-key to "a name bound to `proven_no_key`".
