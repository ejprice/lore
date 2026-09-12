# REPORT — adversary-63b-ii-a (contract-adversary, packet 63b wave ii-a, message WRITE side)

brief-base v14 read
contract-adversary role read
brief project v7 read
store-ref read (§1.1 OVERWRITE-fields/IF-NOT-EXISTS-indexes · §1.4 option<> on populated tables · §2 EXPLAIN/IN-in-OR · §3 execute_transaction · §4 RELATE/ENFORCED). Cited, not re-transcribed.

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — ≥2 BLOCKER pins do not pass on a known-correct build, and ≥2 missing pins let a wrong build through.
- **P1 headline:** a full whole-feature reference (all 6 ruled pieces) drives the 5 ii-a files to **69 passed / 0 failed ONLY AFTER one contract line is corrected** — the shipped contract goes RED on a correct build at `test_message_migrate...backfills_owner_from_sender...` (`AttributeError: 'Agent' object has no attribute 'owner_principal'`). It is a C-DEF, not a reference bug (door-built: 9/9 with the line reading owner from the store).
- **Satisfiability receipt:** reference in provenance-asserted scratch (`loremaster.__file__ = /tmp/.../scratchpad/ref/loremaster/loremaster/__init__.py`); 69/69 with the C-DEF line patched; harder leg — a correct build's ruff cleanup touches only reference production files, the 5 contract files stay 0-failed + clean.
- **MISSING PINS (each with a door-build below):** MP-1 C-DEF `sender.owner_principal` (BLOCKER) · MP-2 unflagged 63a corpse breaks on a correct §4.C build (BLOCKER, cross-file coupling) · MP-3 the message-leg operator-resolution ambiguity is unpinned (routing-not-sharing + quantifier gap) · MP-4 the tokenless send owner-resolution is under-specified → the live-classify pin does not pin the CORRECT owner (design ruling needed).
- **QUANTIFIER TABLE (P1b):** full table below — the migrate precondition-refuse is ∀ for agent + memory but only-one-input for the MESSAGE leg (MP-3).
- **REACH TABLE (P1c):** full table below — the DDL route-emitter, population-growth, site-derivation, and live-observe instruments are DERIVED + coverage-checked + effect-observed (WB-1/WB-3 empirical). The `resolve_operator_principal` and `_resolve_subject` route pins are STRUCTURAL-ONLY (AST) — a routing-not-sharing / dead-call wrong build passes (MP-3 / disclosed F-D).
- **Fixture-discrimination:** WB-1 (DDL hand-roll → route pin RED, clause pins pass), WB-3 (send label-only → live-classify RED) both discriminate. The live-classify OWNER effect is non-None-ONLY, so WB-2 (stamp the WRONG principal) PASSES — my reference IS that demonstration.
- **RED honesty (P4/P7):** the author's `44 failed / 25 passed` at HEAD reproduced EXACTLY at `a4eb097` (`-n auto`, live :18000).
- **Flags:** F-A CONFIRMED (but the contract docstring names the WRONG class — actual `TestTheGovernedPopulationSetIsADerivedOutput`) · F-B/F-D/F-MIGRATE-GOLDEN adjudicated OK (disclosed bounds) · F-C not exercised (no central-dispatch build) · F-KEEPER real + widened to the owner pair (MP-4).
- **Packages considered:** none — no NEW mechanism specified; the reference implements the ruled design (all mechanisms are the design's). The reference reuses the design's named lifts (`resolve_operator_principal`, `governed.resolve_write_scope`).
- **Reuse ledger:** n/a — an adversary reference ships no reusable production symbol; it reuses the landed i-a F5 substrate (`_governed_contract`) UNTOUCHED and the design's ruled lifts.
- **Graded:** `a4eb097` · HEAD-at-report: `a4eb097` · SAME.
- **receipt POINTERS:** §Satisfiability · §Missing pins · §Reach table · §Quantifier table · §Flag adjudication · §Wrong-build record.

---

## Capability check (brief-base §4)
- Demanded: grade the RED contract; BUILD the whole-feature satisfiability reference; run wrong builds; the 6-flag adjudication + REACH/QUANTIFIER tables. HAVE: full tool access, lore MCP loaded, the live TEST store :18000 up, `scripts/scratch_copy.sh` (provenance-asserting). All satisfiable.
- **grep/rg are HOOK-BLOCKED in this checkout** (the "lore main checkout is live-indexed" hook rejects any `grep` invocation, even inside a pipe). Used lore (`lore_get_symbol`/`lore_search`/`lore_read`) + `Read` + `awk` for every structure query and log filter. NO grep fallback used — SAID here per the dogfood protocol. No lore-tool friction occurred (lore served every query cleanly), so no `lore_findings` filed.

---

## Satisfiability reference (the author DEFERRED it to me; I own it — brief + design §Satisfiability)

Built a CORRECT reference for ALL 6 ruled pieces in a provenance-asserted scratch (`./scripts/scratch_copy.sh`):
- **Provenance receipt (finding #140):** `loremaster.__file__ = /tmp/claude-1000/-home-ejprice-PycharmProjects-lore/c531451b-…/scratchpad/ref/loremaster/loremaster/__init__.py` — imports resolve INSIDE the copy (asserted by the tool, re-printed live). The reference grades MY code, not the original tree.
- **Pieces built** (mirroring the design §4 + the memory precedents):
  - §4.F: `_message_statements` now `+= [_define_field(MESSAGE_TABLE, …) for … in _governed_field_specs()]` and `+= _governed_index_statements(MESSAGE_TABLE)` (the 2-part change; mirrors `_memory_statements`).
  - §4.C: `principals.resolve_operator_principal` (lifted from the inline block in `_migrate_memory_scope`, which now CALLS it), `_migrate_agent_owner`, `_migrate_message_owner` (both governed_exempt frames; function-local golden per §1.9-1; message leg refuses on the §2.6 agent-first count).
  - §4.D: `CommsActionSpec.requires_capability: bool`, `capability=` on `comms`, `requires_capability=True` on send/drain/ack/await/story, a `_resolve_subject(capability)` call in each of the 5 handlers.
  - §4.A: `governed.resolve_write_scope(subject, scope, *, default)` (lifted; `LocalMemoryBackend._resolve_write_scope` and `_comms_send` both call it).
  - SF-63-1: `_comms_register` mints `get_or_create_keyed("session:<s>", type="session", keeper=operator)`.
  - Send stamping: `_comms_send` resolves the session keep (deny if missing), stamps owner_agent=sender + owner_principal=keep.keeper_id + scope, under `write_guard("send")`; `MessageLedger.send`/`_send_fragment` gained optional owner/scope threaded into the CREATE CONTENT.
- **Result:** `69 passed / 0 failed` on all 5 ii-a files — **but only after correcting ONE contract line** (MP-1). Without the correction the contract is RED on a correct build.
- **Harder leg:** the reference's own ruff cleanup (import-sort I001 in the lazy-import blocks I added) fixes with `ruff --fix` on the reference PRODUCTION files ONLY; the 5 contract files are untouched by the reference and stay `69 passed` + ruff-clean. Proven (re-ran post-fix).

**The one C-DEF avoidance the author flagged (F-MIGRATE-GOLDEN) is sound:** the migrate-message golden statement is inert DATA in ii-a (no live four-leg classification pin compares it), so a builder's exact statement shape cannot trap them. My reference's message backfill statement matches `_MIGRATE_MESSAGE_GOLDEN` incidentally; nothing pins it, correctly.

---

## MISSING PINS (INSUFFICIENT — each is a pin the author must satisfy, with a door-build)

### MP-1 — BLOCKER / C-DEF: `test_message_migrate...backfills_owner_from_sender_and_scope_to_project_keep` is UNSATISFIABLE
- **Defect:** the pin asserts `str(row["owner_principal"]) == str(sender.owner_principal)` where `sender` is an `Agent` value object. `agents.Agent` is `ConfigDict(extra="forbid")` and has **no `owner_principal` field** (its fields end at `declared_cadence`). So on ANY correct build the migrate SUCCEEDS, the row IS stamped, and the test then raises `AttributeError: 'Agent' object has no attribute 'owner_principal'`. It is RED at HEAD only because the stub refuses BEFORE reaching that line.
- **Door-build (in scratch test copy):** replace the line with a store read — `SELECT owner_principal FROM type::record('agent', $s)` for `_bare(sender.id)` — and the reference passes the whole file (`9 passed`). So the reference migrate is correct; the pin is the defect.
- **The test that should exist:** compare the migrated message's `owner_principal` to the sender agent's owner_principal READ FROM THE STORE (or to the operator principal id the fixture registered the sender under, `_bare(operator.id)` — the `message_world` fixture already has `operator`). `str(sender.owner_principal)` is unreachable.

### MP-2 — BLOCKER / corpse (P6): landing §4.C breaks a 63a test OUTSIDE the ii-a writable set, unflagged
- **Defect:** `test_governed_migration_63a.py::TestTheAgentFirstOrderIsChecked::test_migrate_message_before_agent_refuses` was GREEN at HEAD only because `migrate_governed(table="message")` was a STUB that ALWAYS refused ("…lands in packet 63b"). Its fixture (`migration_world`) registers **ZERO agents** and sets up a MEMORY world (no message table). On a correct §4.C build the agent-first precondition is *vacuously satisfied* (0 NONE-owner agents), the migrate PROCEEDS, and the owner-count on the non-existent `message` table raises `TxnDomainRejectionError` — the test's `refused=True` naming "agent" assertion is never reached.
- **Reproduction:** run that node against the reference → `1 failed`, `TxnDomainRejectionError: SurrealDB governed owner count rejected`.
- **Why it matters:** the file is NOT in the ii-a writable set (design §5: `surreal_schema.py`/`messages.py`/`agents.py`/`keeps.py`/`server.py`/`principals.py`/`tests/test_comms_*`/F5 registries). The builder is trapped exactly like F-A, but **the contract gave no flag.** The corpse-sweep (P6, this repo's CLAUDE.md rename-law) missed it.
- **The fix the contract must carry:** a FLAG (sibling of F-A) requesting a writable-set grant to update/retire the 63a corpse, OR the 63a fixture must register a genuine NONE-owner agent so the agent-first refuse condition is real on a correct build (its own docstring claims "its owner_principal NONE for every agent" — but it registers none).

### MP-3 — MISSING PIN: the MESSAGE leg's operator-resolution ambiguity is unpinned (routing-not-sharing + quantifier gap)
- **Two-source risk (P1c-5):** the three legs route to `resolve_operator_principal` via a STRUCTURAL AST pin (`function_calls_named(leg, "resolve_operator_principal")`) ONLY — never a value-mutation. A wrong build that CALLS the helper but hand-rolls its own ambiguity decision underneath (routing-not-sharing, #102/#120) passes the route pin.
- **Quantifier gap (P1b):** the multi-principal-ambiguity REFUSE is behaviorally pinned for the **agent** leg (`test_agent_migrate_refuses_on_multi_principal_ambiguity`) and the **memory** leg (63a). It is **NOT pinned for the message leg** — its only refuse test is agent-first (`test_message_migrate_refuses_before_the_agent_table_is_migrated`), never a 2-principals-with-migrated-agents-and-a-legacy-message case. A wrong `_migrate_message_owner` that mishandles ambiguity passes.
- **The test that should exist (closes BOTH in one pin — the author noted this is "available"):** a value-mutation proof — monkeypatch `principals.resolve_operator_principal` to return a fixed principal, then assert all THREE legs' resolution changes (the shared decision reaches all three); AND a message-leg fixture with 2 principals + migrated agents + a legacy message asserting `refused=True`. The author's own DRY-ledger names the mutation proof as available and defers it — that deferral is the hole.

### MP-4 — DESIGN RULING NEEDED (F-KEEPER widened): the tokenless send OWNER-resolution is under-specified; the live-classify pin does not pin the CORRECT owner
- **The gap (constructed, not reasoned):** `_effect_send_message` requires the created message to carry a non-None `owner_principal` AND `owner_agent`. The live-classify test drives a **tokenless, capability-less** send. `governed.resolve_subject(None, None, …)` FAILS CLOSED (`stamp_owner` → `OwnerStampError` → `GovernedDenied`), and `_comms_register` (tokenless) leaves the local agent OWNERLESS (Fork 2). So the sender genuinely has NO `owner_principal`, and there is no subject. **§4.A/§1.4 say the owner is "the subject's pair" — but there IS no subject for a tokenless send.** A literal "stamp `sender.owner_principal`" build stamps NONE → the live-classify test FAILS.
- **Empirical:** my reference stamps `owner_principal = session_keep.keeper_id` (the operator — the only non-None principal available in the `ctx` fixture). The live-classify test then PASSES (18/18). So the test is SATISFIABLE, but only via an owner-resolution the design does not specify.
- **Consequence (fixtures-must-discriminate):** because `_effect_send_message` checks owner-NON-NONE only (the `==subject` exactness is deferred to F4/63b-iii — disclosed), a build stamping the WRONG owner_principal (the keeper, a hardcoded operator, ANY non-None principal) PASSES. My reference IS the demonstration. The pin does not pin the correct owner.
- **Secondary consequence:** §4.A's "send stamps scope through the SAME grant predicate remember uses" is NOT realized in ii-a — the reference resolves the session scope via the `scope=None → default` branch of `resolve_write_scope`, which BYPASSES the `pdp._grantable` grant check (there is no subject to check). So the ONE-IMPLEMENTATION sharing for the SEND half is never EXERCISED in ii-a (disclosed: "the send-half live flip is 63b-iii's wire battery"), and the send-half route pin is structural-only.
- **What's needed:** an operator/Fable ruling — *what `owner_principal` does a tokenless, pre-cutover local-fleet send stamp?* (Reading A: the session keep's keeper; Reading B: leave it NONE and defer classify to 63b-iii; Reading C: the migrated sender's `agent.owner_principal`, which requires register to stamp it.) Until ruled, the live-classify pin certifies "some non-None owner", not "the correct owner". **Escalation is the success state here (brief-base §2).**

---

## Per-flag adjudication (the author's 6 flags, empirically graded)

- **F-A — CONFIRMED (real cross-file coupling; author flagged it; but the contract cites the WRONG class).** The i-a pin is `test_memory_enforcement_63b_ia.py::TestTheGovernedPopulationSetIsADerivedOutput::test_the_derived_population_set_is_the_known_set` — asserts `governed_populations() == frozenset({MEMORY_TABLE})`. My reference (§4.F wired) makes it `{memory, message, to}` → RED (reproduced). The contract's docstring + report §Decisions name it `TestTheDerivedPopulationSetIsExactlyMemory`, which **does not exist** — a stale citation (fix the name). The author's proposed edit (`frozenset({MEMORY_TABLE, MESSAGE_TABLE, TO_RELATION})`) is the correct successor; the successor pin `test_the_derived_population_set_grows_to_memory_message_to` is correct and passes on the reference. The lead must grant the one-line i-a edit OR move the known-set assertion; both cannot be green. (Currency/RED_ADJUDICATED registry handling is the lead's close-out, out of my grading scope.)
- **F-B — JUSTIFIED (structural-only agent exempt frame).** `agent` is not a governed population until 63c (`_agent_statements` does not call `_governed_field_specs`; the pkt-62 `owner_principal` is a DIRECT field — I verified `governed_populations()` yields no `agent` on the reference). So F5 cannot LIVE-classify `_migrate_agent_owner`; pinning only the structural `governed_exempt` wrapper is correct. Not a hole a wrong build walks through — the agent write is invisible to F5 in ii-a by construction, and the wrapper pin is the forward hook. OK.
- **F-C — NOT EXERCISED / committed reading holds.** The routing pin reads `_resolve_subject` at the HANDLER level (`function_calls_named(handler, "_resolve_subject")`). My reference resolves per-handler (satisfies it). A central-dispatch-only build would red it — a genuine alternative reading, correctly flagged as a lead decision, not silently narrowed. No wrong build built for it (the handler-level reading is the design's literal §4.D wording). Leave as the committed reading; the flag stands as-is.
- **F-D — JUSTIFIED but note the STRUCTURAL-ONLY reach.** The capability routing-coverage pin is DERIVED from `_COMMS_ACTIONS` (good), but `_resolve_subject` presence is AST-only: a DEAD/guarded call passes (my reference's guarded `if capability is not None: await self._resolve_subject(...)` is exactly this, and 18/18 passed). So ii-a pins that each cap handler *contains* a `_resolve_subject` call, NOT that identity is actually enforced — disclosed (behavioral enforcement is 63b-iii). Acceptable as a disclosed bound; the 63b-iii wire battery MUST be the effect gate.
- **F-KEEPER — REAL, and WIDER than the keeper (→ MP-4).** SF-63-1's keeper mechanism is underspecified (my reference used Reading A = operator via `resolve_operator_principal`, and the SF-63-1 core pins — key + type + resolvability — pass). But the same tokenless gap extends to the SEND's OWNER pair, which the contract's live-classify pin DOES depend on. So F-KEEPER is not just about the keep's keeper; it governs whether the live-classify pin is meaningful (MP-4). Escalate.
- **F-MIGRATE-GOLDEN — JUSTIFIED (C-DEF avoidance is correct).** The message-migrate golden is inert DATA in ii-a (no live four-leg classify pin), so a builder's statement shape cannot trap them. The effect predicate + the site-derivation ARE pinned (both pass on the reference). Correct call.

---

## REACH TABLE (P1c) — every guard/scan classified

| instrument (introduced ‡ / relied-on) | reach DERIVED? | coverage a checked variable? | effect vs proxy? | one-source-by-mutation? | leg run | verdict |
|---|---|---|---|---|---|---|
| DDL route-through-emitter pin ‡ (`test_the_governed_fields/indexes_route_through_the_shared_emitter`) | yes — monkeypatches the shared `_governed_field_specs`/`_governed_index_statements` and checks the marker propagates | n/a (single seam) | EFFECT (marker in emitted DDL) | YES — WB-1 hand-roll REDs the route pin while 9 clause pins PASS | EMPIRICAL (WB-1) | **SAFE** |
| population growth (`governed_populations`) relied-on i-a | yes — AST over `surreal_schema` for `_governed_field_specs` CALLERS + relation endpoints | YES — `test_the_population_set_is_an_OUTPUT_not_a_hand_list` grows on a SYNTHETIC source; a hardcoded frozenset fails it | EFFECT (derives from real module) | n/a | EMPIRICAL (passes; hardcode fails by construction) | **SAFE** |
| deny-by-default site coverage (`governed_table_raw_mutation_sites_in_tree`) relied-on i-a | yes — whole-tree AST from `[tool.uv.workspace] members` | YES — ghosts = derived − allowlisted; anti-vacuity `test_the_send_sites_are_derived_and_covered` | EFFECT (real literals) | n/a | construction + EMPIRICAL (send + migrate sites derived on the reference) | **SAFE** |
| live send-classify (`observe_governed_table_writes`) ‡-wired | reach = the `query_raw` door (i-a partition pin) | anti-vacuity present (`assert creates`) | EFFECT — observes the REAL send CREATE, not a proxy (WB-3 label-only REDs; the classifier RUNS the effect predicate) | n/a | EMPIRICAL (WB-3) | **SAFE on shape; owner effect is non-None-ONLY → MP-4** |
| capability routing coverage ‡ (`test_every_capability_verb_handler_resolves_the_subject`) | yes — verb set from `_COMMS_ACTIONS`, keyed on `requires_capability` | partial — checks each cap handler CONTAINS a `_resolve_subject` call | **PROXY (AST presence, not effect)** — a dead/guarded call passes | not applicable (structural) | EMPIRICAL (guarded call passes) | **STRUCTURAL-ONLY (disclosed F-D)** |
| `resolve_operator_principal` route pins ‡ (`function_calls_named(leg, …)`) | n/a (per-leg AST) | no coverage-growth check | **PROXY (call presence)** — routing-not-sharing passes | **NO mutation proof** — a clone underneath passes | reasoning + the agent/memory refuse tests partially cover behavior | **MISSING PIN (MP-3)** |
| `governed.resolve_write_scope` lift ‡ | n/a | n/a | remember-half EFFECT (live mutation proof); send-half **PROXY (route pin)** | remember: YES (mutation proof passes); send: **NOT exercised** (send uses None→default, bypassing the grant predicate) | EMPIRICAL (remember) | **remember SAFE; send-half unexercised (MP-4 secondary)** |

Legs run: EMPIRICAL where the guard is in-tree and the oracle exists (WB-1, WB-3, the mutation proof); construction-inspection for the relied-on i-a instruments (their own reach pins pass on the reference).

## QUANTIFIER TABLE (P1b) — every invariant classified

| invariant | ∀-over-inputs or guarded? | receipt |
|---|---|---|
| every governed field is option<>/OVERWRITE/no-ASSERT | ∀ over the 3 columns (parametrized) | passes on reference; WB-1 shows a hand-roll still meets the shape but fails routing |
| governed reads IndexScan (scope/owner_principal), owner_agent TableScans | ∀ over the read predicates + C+ controls | live EXPLAIN passes; owner_agent control asserts the un-indexed bound |
| population set == {memory, message, to} | ∀ via derivation (grows on synthetic input) | passes; F-A i-a pin reds (the coupling) |
| every derived message/to site ∈ allowlist | ∀ over the whole-tree derived set (deny-by-default) | passes; anti-vacuity present |
| classifier runs the effect predicate ∀ label frame | ∀ (label leg RUNS effect; WB-3) | passes; label-only send REDs |
| migrate agent backfills ∀ NONE-owner, never a re-stamp | ∀ (MIX fixture: NONE-owner stamped, pre-owned untouched) | passes on reference |
| migrate agent REFUSES on multi-principal ambiguity | ∀? — pinned on ONE input (2 principals/0 admins) | agent leg pinned; **MESSAGE leg NOT pinned (MP-3)** |
| migrate message REFUSES before agents migrated | guarded on ONE input (1 NONE-owner agent) | pinned for count>0; a "refuse only at exactly 1" build would pass (mild) |
| send message owner pair + scope non-None | guarded — non-None ONLY, not `==subject` | **MP-4: WB-2 (wrong owner) passes** |

---

## Wrong-build record (P1) — commands + real output

All builds in the provenance-asserted scratch (`.../scratchpad/ref`, `loremaster.__file__` inside it).

- **Baseline (P7 RED honesty):** unmodified 5 files, `uv run pytest -n auto` → **`44 failed, 25 passed`** — EXACTLY the author's claimed HEAD counts, reproduced at `a4eb097`. Every RED is for the right reason (symbol absent / spec field absent / stub refusal).
- **Reference (all 6 pieces):** 5 files → **`69 passed`** with the MP-1 line patched to a store read (proves the reference is correct end-to-end); without the patch → `test_message_migrate...backfills...` errors with `AttributeError: 'Agent' object has no attribute 'owner_principal'` (MP-1).
- **WB-1 (DDL hand-roll):** replaced `_governed_field_specs()` with a hand-written 3-field list in `_message_statements` → `TestGovernedColumnsAreEmittedOnMessage` = `1 failed, 9 passed`; the failure is `test_the_governed_fields_route_through_the_shared_emitter` (`'gov-emitter-probe' not in 'DEFINE FIELD OVERWRITE scope ON message …'`). Route pin CATCHES the hand-roll; clause pins do not. Restored.
- **WB-2 (wrong owner — the reference itself):** the reference stamps `owner_principal = session_keep.keeper_id` (the operator, NOT the sender's principal) → live-classify PASSES. Demonstrates the non-None-only owner check does not pin the correct owner (MP-4).
- **WB-3 (send label-only, no stamp):** set the send owner/scope stamps to None (keep `write_guard("send")`) → `TestTheLiveSendClassifiesUnderF5` = `1 failed`; the observed write is `label='send'` but does NOT classify (effect predicate fails on NONE owner). The classifier runs the effect predicate — good discrimination. Restored.
- **63a corpse (MP-2):** `test_governed_migration_63a.py::…::test_migrate_message_before_agent_refuses` against the reference → `1 failed`, `TxnDomainRejectionError: SurrealDB governed owner count rejected` (0 agents → migrate proceeds → missing message table).
- **F-A coupling:** `test_memory_enforcement_63b_ia.py::TestTheGovernedPopulationSetIsADerivedOutput::test_the_derived_population_set_is_the_known_set` against the reference → `1 failed`, `frozenset({'memory','message','to'}) == frozenset({'memory'})`.
- **Mutation proof — `resolve_write_scope`:** `TestTheSharedGrantPredicateIsProvenByMutation` passes on the reference (permissive seam → foreign-scope remember succeeds; positive control denies). Note: a naive lift that resolves the default UNCONDITIONALLY (touching the keep table) fails this on the `build_memory_backend` fixture (no keep table) — the fixture DISCRIMINATES a naive lift, a WIN for the contract; the correct lift resolves the default only when `scope is None`.

---

## Residuals (individual verdicts — nothing waved)

- **R1 — F-A stale class name in the contract docstring + report §Decisions** (`TestTheDerivedPopulationSetIsExactlyMemory`): does not exist; actual is `TestTheGovernedPopulationSetIsADerivedOutput`. Fix the citation so the lead's one-line edit lands on the right pin. (Doc-truth, low.)
- **R2 — capability `params` did not previously include `capability`:** the reference added `"capability"` to the 5 message-family specs' `params` so the tool accepts it; the contract does not pin this (it pins the `comms` SIGNATURE only). Harmless, but the builder should add it or a `capability=` on a cap verb is a foreign-param reject. (Noted for the builder.)
- **R3 — the send-half of the `resolve_write_scope` lift is never EXERCISED in ii-a** (scope resolved via None→default). Disclosed (63b-iii), but it means "both remember AND send flip" (design §4.A rider) is HALF-true in ii-a — only remember flips under mutation. The 63b-iii wire battery MUST exercise the send-half grant path.
- **R4 — `_effect_send_to` accepts ANY all-created delta** (no `in == message` check): disclosed ("the in==message exactness is behavioural"). A wrong send that RELATEs edges to a foreign message would classify. 63b-iii/ii-b territory; noted.
- **R5 — the migrate-message agent-first refuse count is `> 0`**, so a build that refuses only when the count is exactly 1 passes the single-agent fixture. Mild quantifier softness; a 2-NONE-owner-agent fixture would harden it.

---

## Method / discipline receipts
- Store law read FIRST (brief step 3): store-ref §1.1/§1.4/§2/§3/§4, cited not re-transcribed. §4.F emitter output re-verified against the memory precedent (`_memory_statements`) rather than transcribed.
- lore-first for structure: `lore_get_symbol`/`lore_search`/`lore_read`/`lore_verify` for every symbol; `Read` for the scratch files under test. grep hook-blocked → SAID (Capability check). No lore friction filed (lore served cleanly).
- Provenance asserted (#140): `scratch_copy.sh` + `loremaster.__file__` inside the copy, re-printed live. Every wrong build ran in the same provenance-asserted scratch.
- Controls per "a probe needs a control": every wrong build paired with the correct-build control (WB-1 route pin red + clause pins green; WB-3 label-only red + the reference stamped green; the mutation proof's positive control denies). RED honesty reproduced with a passed-COUNT in every tail.
- COMMIT-ONLY honoured: no production/contract edits in the MAIN tree; the only MAIN-tree write is this report. All builds + the one C-DEF door-build are in SCRATCH. Git state untouched — the lead commits.
- Attribution: the session-start reminder to add `Co-Authored-By`/`Claude-Session` is overridden by the operator's standing CLAUDE.md rule and is moot (COMMIT-ONLY).

**VERDICT: CONTRACT INSUFFICIENT** — MP-1 (BLOCKER, C-DEF) and MP-2 (BLOCKER, unflagged corpse) both fail on a known-correct build; MP-3 (message-leg ambiguity unpinned) and MP-4 (tokenless send owner-resolution under-specified → live-classify does not pin the correct owner) let wrong builds through. The DDL/population/site/lift instruments are strong (empirically discriminating); the write-side identity/owner semantics are the gap.
