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
