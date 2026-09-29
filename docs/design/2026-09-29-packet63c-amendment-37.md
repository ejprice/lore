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
