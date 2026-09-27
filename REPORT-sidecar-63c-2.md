# REPORT-sidecar-63c-2 — 63c-i-a CONTRACT FIDELITY READ (ruling `699a6e9` vs contract `0b8ce37`)

brief-base v16 read · brief project v7 read

## Summary block (brief-base §1)

- **state:** done — Task 1 delivered; standing by for 63c follow-ups (long-running sidecar; idle is benign).
- **deviations:** none. Writable set honoured (this report + one new amendment doc `docs/design/2026-09-24-packet63c-amendment-1.md`; no code, no tests, no store touched). Idle-gate contract written under BOTH the lead's session id (`297217bd…`, the id the hook reads) and my own (`56658a55…`).
- **Capability check (brief-base §4):** everything demanded was reachable — lore MCP served every symbol (no drops this run); `Read`/`sed`/prefix-`awk`; `git`/`podman inspect` read-only. grep/rg are hook-blocked as briefed; every textual sweep below is `awk` over an explicit file list and is SAID where used. `loremaster/tests/test_comms_tool.py` (the un-indexed file) was not needed.
- **Packages considered:** none — no mechanism specified (a grading report).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none — no new symbols.
- **Graded:** `0b8ce37` · HEAD-at-report: `d0c9946` · DIFFERENT (2 behind: `f04916d` `.claude/agents/` only; `d0c9946` `docs/plans/v2/receipts/` only — NO code or test moved; every verdict below rests on symbols identical at both shas).
- **decisions-needed:** THREE forks, each with my recommendation (§4): **D1** which sub-wave owns the F5 write-attribution rows of ruling §2.2 (ORPHANED between i-a and i-b — rec: i-b, named in its brief); **D2** the R-Q5-1 row-precondition's KNOWN BOUND vs pkt-62-era rows (rec: pin the bound + trigger now, widen never unless the trigger fires); **D3** fold `test_agent_owns_principal_schema.py::_create_agent` onto `seed_agent_legacy` (rec: yes, in the i-a build's refactor step).
- **headline:** 5 GAPs (2 dropped riders — THE RIDER law instances: P2 `[agent]` still serves MESSAGE prose; the heartbeat leg has no positive control — plus 3 consumer-law/prose gaps), 5 GAP-minor (cheap pins), 2 ORPHANED, 0 CONTRADICTS, everything else FAITHFUL. Three errata in MY OWN ruling found by this read, amended in the doc above.
- **receipt pointers:** §1 verdict table · §2 findings in detail (fix per finding, for the contract author) · §3 consumer-law read of the teaching surfaces · §4 forks · §5 what I verified against production symbols (satisfiability) · §6 discipline.

---

## 1. Verdict table — every §8 rider / §9 item in 63c-i-a scope

Legend: **FAITHFUL** (pinned in the ruling's sense) · **GAP** (the "and pin it like this" half is missing or weaker than ruled) · **ORPHANED** (owned by neither i-a nor i-b) · **CONTRADICTS** (none found).

| # | ruling § | contract pin (file::test) | verdict | one-line |
|---|---|---|---|---|
| 1 | §4.3 failure message "gains the agent wording" | `test_comms_schema.py::TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate::…[agent]` | **GAP (dropped rider)** | the `[agent]` row's RED serves MESSAGE-only prose (`drain stamps to…`, `MessageLedger is the ONE implementation`) |
| 2 | §4.4 heartbeat leg positive control | `test_agent_governance_63c_i_a.py::TestAgentHeartbeatOnALegacyRoleRow63cIA` | **GAP (dropped rider)** | no control proving the leg can SEE a store denial; the ruling's own "junk status" shape for it is wrong (erratum E2) |
| 3 | §2.2 rows 1–3: register stamp inside `write_guard("register")` + CREATE-OWNS-IT allowlist evidence; touch label | — | **ORPHANED** | `_comms_register` enters no `write_guard` at HEAD; `agent_case().write_verbs` is empty "63c-i-b's"; the lead's i-b list does not name the F5 WRITE side |
| 4 | §9 item 6, F12 fate "`test_agent_owns_principal_schema.py:173` docstring → re-dated" | `test_agent_owns_principal_schema.py::_create_agent` docstring | **GAP** | still says name/session carry "the identifier-charset ASSERT", role "non-empty ASSERT" — a prose corpse |
| 5 | §4.2 MOVE pins "TEACHING" | `test_agent_registry.py::TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::test_register_refuses_a_hostile_identifier_before_any_store_write` / `…_blank_role_…` | **GAP (consumer law)** | pins only `"assert violation" not in message`; `AgentRegistryError("invalid")` passes — no field, rule or remedy is pinned |
| 6 | §8 regex-twin (i-a half: register consults `AGENT_NAME_PATTERN` for name AND session) | `…::test_register_charset_check_is_the_ONE_spelling_agent_name_pattern` | **GAP-minor** | the mutated pattern rejects both values → a build routing `name` through the global and `session` through a private copy passes |
| 7 | §4.4 Leg B "all three columns … idempotent on the second call" | `…::TestTheRealAgentMigrateSurvivesLegacyViolators63cIA::test_the_real_migrate_survives_…` | **GAP-minor** | checks `owner_principal` + `scope` only (`owner_agent` unchecked on violators); no second run |
| 8 | §6 R-Q5-1 "naming the count and the rows (ids, bounded)" | `…::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_…` | **GAP-minor** | `re.search(r"\b1\b", reason)` only — any "1" passes; the row id is not asserted; no remedy asserted |
| 9 | §6 row precondition itself | same | **FAITHFUL + KNOWN BOUND in MY ruling** (erratum E3) | a pkt-62+ image's credentialed register stamps owner with no scope → the precondition would refuse the cutover; MEASURED not present today (§2 F9) — pin the bound |
| 10 | §4.3 `_ConstraintSpec` "gains a `ddl` member" | `test_comms_schema.py::_ConstraintSpec.make_ddl` | **GAP-minor** | defaults to `generate_message_ddl` — the fixture-default law; backstopped by the non-vacuity `assert fields`, so no false clear today |
| 11 | §4.3 P-A2 "extend an existing status pin if one holds two of three legs; ONE pin" | `test_comms_schema.py::TestAgentDdlOffline::test_status_ddl_vocabulary_aligns_with_the_reader_literal` | **FAITHFUL** | the existing pin held ONE leg one-way (DDL ⊇ constant) → a new three-way pin is within the letter |
| 12 | §2.1 W1-1 byte-equal + once + routing mutations (field & index) + index names | `test_agent_owns_principal_schema.py::TestTheGovernedTripleShape63cIA` / `TestTheGovernedTripleRoutesThroughTheOneEmitter63cIA` | **FAITHFUL** | satisfiable: built with the SAME `_define_field(...)` construction `_memory_statements` uses; `_governed_index_statements` emits `agent_scope`/`agent_owner_principal` (verified §5) |
| 13 | §9 item 6 DUAL: DDL-text pins → DELETED-WITH-REPLACEMENT; `TestAgentCharsetAssert` → INVERTED; wiring agent leg → DELETED + prose | `test_comms_schema.py` (two in-place DUAL comments) / `test_comms_wiring.py` | **FAITHFUL** | each virtue carried: ∀-no-ASSERT → P2 `[agent]` + KEEP guard; hostile-refused → MOVE pins (7 shapes incl. `""`, 65-char); valid-accepted → MOVE control (4 values incl. 64-char) + Leg A clean-lands; conditional on #6's fix for the session half |
| 14 | wiring `TestSchemaIsActuallyAppliedNotJustConstructed` after 63c-ii | `test_comms_wiring.py::TestSchemaIsActuallyAppliedNotJustConstructed` | **ORPHANED (cross-wave heads-up)** | rests solely on the BRIEF leg now; 63c-ii drops `brief.name`'s ASSERT → the "ensure_ready RAN on THIS connection" virtue dies with nobody's name on it |
| 15 | §4.4 Leg A (frozen capture control · BASELINE ×4 · clean-lands · drop-lands ×3 · status-STAYS) | `…::TestTheAgentAssertsDropFromADirtyStore63cIA` | **FAITHFUL** | hand-captured frozen literals (correct — an emitter-derived old world could never be the control); the contract's THREE violators are right, the ruling's "four non-aligned" is erratum E1 |
| 16 | §2.2 Q1 stamps · §6 R-Q5-2/3 · idempotence · §4.4 P-A3 + control · Leg B C-control | `…::TestRegisterStampsTheGovernedTriple63cIA` / `TestAgentMigrateScopeKeyed63cIA` / `TestAJunkStatusLegacyRowRefusesTheAgentBackfill63cIA` | **FAITHFUL** | concrete values after BOTH register calls; scope read from the keep store; P-A3's heal protocol lives in the docstring exactly as the P-G3 precedent (my "failure message" wording was loose — no action) |
| 17 | contract deviation: all agent DD-3.c legs in ONE file | `test_agent_governance_63c_i_a.py` | **ACCEPTABLE** | reasoning in §2 F17 |
| 18 | §6 `LegacyMapping("agent", "OWNED-BY-THE-OPERATOR")` | — | **note** | `LegacyMapping` has 0 references at HEAD (`lore_impact`) — a docstring-shape dataclass, not a table to "join"; builder adds the agent disposition to `governed.py`'s docstring; nothing pinnable |
| 19 | §8 rows owned by i-b / ii (EXPLAIN-A, ∀-readers, R-a.3, R-β1–6, §3.5, R-467-1–7, P5, flips, regex-twin DELETION, `migrate_governed("brief")` succeeds pin, P2 `[brief]`) | — | **owned, not orphaned** | each named in the lead's i-b list or ruled 63c-ii (F-regex-twin, F-briefs-import) |

---

## 2. Findings in detail — the fix for the contract author

### F1 — GAP (dropped rider): P2 `[agent]` serves message-only prose (§4.3, THE RIDER law)
- **What the ruling says:** §4.3 *"The failure message gains the `agent` wording: `agent` is UPDATE-hot per agent (`touch` re-validates…) and UPDATE-able whole-window (the cutover backfill)… The app cap in `AgentRegistry.register`/`touch` is the ONE implementation…"*.
- **What the contract does:** `_ConstraintSpec` gained `make_ddl` (the derivation half — implemented) but the assertion message at `test_no_field_carries_a_constraint_a_legacy_row_can_violate` still reads *"drain stamps `to` in one statement over the window; the §4.C cutover migrate re-validates every `message` row… The app cap in `MessageLedger` is the ONE implementation… the §6/§12.6 dirty-store pin"* for EVERY table, including `[agent]`. The clause BEFORE "and the failure message gains…" was implemented; the clause after was not.
- **Consumer-law cost:** a builder who re-adds an agent ASSERT is told to look at `MessageLedger` and the message dirty-store pin — the wrong writer and the wrong pin.
- **Fix:** add a **no-default** `hazard: str` member to `_ConstraintSpec` (per-table prose: the writer that is the ONE implementation + the UPDATE-hot mechanism + the dirty-store pin's address) and interpolate it; pin it with a message-content leg — for `[agent]` the served message names `AgentRegistry.register`/`touch`, `heartbeat`, and `test_agent_governance_63c_i_a.py`; mutation: swap the `to`/`agent` hazard strings → the `[agent]` content leg reds. (One spec, one message template, N prose slots — never a second copy of the assertion.)

### F2 — GAP (dropped rider): the heartbeat leg has no positive control (§4.4) — and the ruling's shape for it is WRONG (erratum E2)
- **What the ruling says:** *"Positive control: a row seeded with a junk `status` under a downgraded-`status` DDL → `touch` is refused by the engine (the KEEP's mechanism, proving the leg can see a denial) — and that row is P-A3."*
- **What the contract does:** `TestAgentHeartbeatOnALegacyRoleRow63cIA` has the one RED-at-HEAD pin and no control; P-A3 covers the BACKFILL's denial, not `touch`'s.
- **Why my ruling's shape cannot work (verified against `AgentRegistry.touch` at HEAD):** `touch` runs `_resolve_row` → `_row_to_agent(row)` (pydantic `Agent.status: AgentStatus` Literal) BEFORE the UPDATE — a junk-status row is refused at DECODE, never reaching the store ASSERT. That is F6 (the reader rejects) operating exactly as ruled; it makes junk-status the wrong control for a STORE-denial leg. The ruling conflated the two ("that row is P-A3"); they are two pins.
- **Wrong build the missing control admits today:** small — `touch` reads back via `_select_row`, so a no-op touch fails `updated.last_note == "alive"`. But a leg whose only demonstration of "can see a denial" is its own RED-at-HEAD loses that demonstration the day it goes green (the fixture-liveness class).
- **Fix:** ONE control, immune to the build: seed `role=""` under `unbounded_agent_ddl()`, apply **`frozen_asserted_agent_ddl()`** (never the current emitter), then the REAL `registry.touch` → `pytest.raises(SurrealStoreError)` (the driver's typed rejection; the contract's own MOVE docstring already establishes that hierarchy) — the Leg B C-control's twin, through the `touch` seam. Amendment doc E2 re-words the ruling.

### F3 — ORPHANED: the F5 WRITE-attribution rows of §2.2 (D1 — lead call)
- **What the ruling says (§2.2 table):** the register CREATE stamps *"inside `write_guard("register")`; the F5 allowlist's CREATE-OWNS-IT entry with evidence …"*; re-register *"the same allowlist entry (self-row by id)"*; the dispatcher touch *"`write_guard("heartbeat")` / a per-verb label the dispatcher sets"*.
- **Measured at HEAD:** `_comms_register` (`server.py`) calls `agent_registry.register(... owner_principal_id=…)` with NO `write_guard` (awk over the function span, said); `agent_case()` in `_governed_contract.py` sets `write_verbs` empty with the comment *"63c-i-b's (serving/security)"*; the lead's accepted i-b scope line (`REPORT-lead-63c.md` RESUME ANCHOR) names read_filter wiring, EXPLAIN-A, β + corpse, #467 dispatcher, flips — not the F5 write side. `observe_governed_table_writes(table)` is per-block registration, so either wave CAN observe `agent`; nobody is briefed to.
- **Why it matters:** the i-a build adds two governed columns to a CREATE that today runs unattributed. A memory/message write with `label=None` is UNCLASSIFIED (deny-by-default, L2b) under the F5 seam — but only if `agent` is REGISTERED as a population when the observer runs. An unobserved population is the seventh-defeat shape (reach as a hidden constant).
- **Recommendation:** assign to **i-b**, named explicitly in its brief: the F4 write-verb family for `agent` — register CREATE (label `register`, CREATE-OWNS-IT evidence per §2.2), re-register UPDATE (same entry), dispatcher touch (per-verb label) — observed via `observe_governed_table_writes("agent")`, with the allowlist rows and their evidence strings. i-b already owns the dispatcher that sets the per-verb label, so the register label lands beside it. Alternative: i-a takes the register/re-register half now (it is building that CREATE) — smaller but splits one family across two waves.

### F4 — GAP: the `_create_agent` docstring in `test_agent_owns_principal_schema.py` was not re-dated (§9 item 6 F12 fate)
- **Ruling:** *"`test_agent_owns_principal_schema.py:173` docstring → re-dated"*. **Contract:** unchanged — it still teaches *"`name`/`session` (the identifier-charset ASSERT), `role` (non-empty ASSERT)"* as REQUIRED store constraints. After the i-a build that sentence is false (P8d prose-corpse class; the contract's own DUAL comment in `test_comms_schema.py` shows the author knew the class).
- **Fix:** rewrite: *"`name`/`session`/`role` were store-ASSERTed until 63c-i-a (`699a6e9`); after Q3 only `status` keeps a store ASSERT — the identifier charset and non-empty role are validated by `AgentRegistry.register` (the ONE implementation), and a RAW CREATE here bypasses that on purpose."* Also add: this helper predates `seed_agent_legacy` (see D3).

### F5 — GAP (consumer law): the Q3 MOVE teaching content is not pinned
- **Ruling §4.2:** a *"teaching `AgentRegistryError` subclass BEFORE any store I/O"*; §8 MOVE row: *"TEACHING, before any store I/O"*.
- **Contract:** `test_register_refuses_a_hostile_identifier_before_any_store_write` asserts `pytest.raises(AgentRegistryError)`, `"assert violation" not in message.lower()`, row count 0. Its docstring promises *"naming the illegal shape + the charset"*; the assertion checks neither. `raise AgentRegistryError("invalid")` passes every pin. Same for the blank-role pin.
- **Consumer-law read (§3 below):** the register refusal is the FIRST thing a freshly-spawned agent with a typo'd name will ever read from lore; a bare error is a route-around trigger.
- **Fix:** pin three content facts per refusal — (i) the FIELD (`name` / `session` / `role`) appears; (ii) the RULE — for charset the pattern text (`AGENT_NAME_PATTERN.pattern`, so a pattern change moves the message with it — derived, not restated); for role the word `blank` (or `non-empty`); (iii) the REMEDY — *register again* with a legal value. Assert the offending VALUE is rendered attributed (`render_attributed`, the house sanitiser — the hostile set includes `"colon:here"` and whitespace; a raw echo is a forgery door). Keep the row-count-zero leg (adequate for a CREATE on a virgin store; the ruling's "F5 observes zero writes" wording is satisfied in effect — D1 decides where the observer runs).

### F6 — GAP-minor: the regex-twin pin cannot see a private `session` copy
- The mutation `^ZZZ_NO_MATCH$` rejects `fixer-b` AND `wave7`, so `register("fixer-b", session="wave7")` reds on a build that consults the global for `name` only. **Fix:** parametrize over two mutated patterns, each matching exactly one of the two fixture values — `^fixer-b$` (name accepted, session refused ⇒ session consults the global) and `^wave7$` (name refused ⇒ name consults it). Two legs, one pin.

### F7 — GAP-minor: Leg B checks two of three columns and never re-runs
- Ruling §4.4 Leg B: *"every row stamped (agent: all three columns) … idempotent on the second call"*. Contract asserts `owner_principal is not None and isinstance(scope, str)`. **Fix:** add `str(row["owner_agent"]) == f"agent:{ids[shape]}"` on each violator (R-Q5-3's shape, on the DIRTY population — a build that stamps three columns for clean rows and two for violators is unrepresentable under ONE statement, but the pin is the proof, not the design) and a second `_migrate_agent` → `backfilled == 0`, `refused is False`.

### F8 — GAP-minor: R-Q5-1's reason is under-pinned
- Ruling §6: *"REFUSE naming the count and the rows (ids, bounded)"*. Contract: `re.search(r"\b1\b", reason)` — `"table=agent scanned 1"` satisfies it. **Fix:** assert `"already_owned"` (the seeded id) appears, the count appears as `1 ` adjacent to a noun (`1 agent row`), and a remedy is named (see D2 for what the remedy IS — the reason must teach it). With TWO trap rows the count leg discriminates from stray digits; keep one seeded owner distinct from the operator so a widened precondition (D2) would still refuse.

### F9 — KNOWN BOUND in MY OWN ruling (§6) — erratum E3, fork D2
- **The hole:** §6 says a NONE-scope row with a non-NONE owner is *"either a multi-principal store … or a half-applied prior run (impossible after this ruling)"*. There is a THIRD population: a credentialed `register` under pkt 62 (`66b5fa4`, 2026-08-24) through 63b stamps `owner_principal` on a table that has no `scope` column. Every such row is owner=operator, scope=NONE — exactly what R-Q5-1 refuses — and it is neither multi-principal nor half-applied.
- **Measured (2026-09-24):** `podman inspect lore-lore` → image `localhost/lore:latest` created **2026-08-17 20:13 -0400**, i.e. BEFORE pkt 62 landed; production `:18500` therefore carries NO `owner_principal` column, so no such rows exist today. The plan of record is COMMIT-ONLY until pkt-65, which ships 62 + 63a/b/c in one image; under 63c code every register stamps all three columns, so the population cannot arise between boot and the operator's `migrate-governed`.
- **Ruling (amended, not widened):** the precondition stands as written — KNOWN BOUND with a named re-open trigger: *"a pkt-62-through-63b image deployed before the 63c cutover"*. If it fires, the precondition narrows to `owner_principal IS NOT NONE AND owner_principal != <the resolved operator>` and operator-owned NONE-scope rows are stamped `scope` + `owner_agent` only. **Contract fix:** R-Q5-1's docstring carries the bound + trigger (a bound that is unpinned is indistinguishable from an unknown one); the refusal reason names the remedy (*adjudicate by hand: `lore-adm …`* — the builder names the verb).

### F10 — GAP-minor: `_ConstraintSpec.make_ddl` has a default
- `make_ddl: Callable[[], str] = generate_message_ddl` — CLAUDE.md: *"Fixture factories must not default a parameter the code branches on."* A 63c-ii `[brief]` row that forgets it derives over the MESSAGE DDL, finds zero `ON brief` fields, and the non-vacuity `assert fields` reds — so no false clear, but by backstop, not by construction. **Fix:** no default; `to`/`message` pass `generate_message_ddl` explicitly.

### F11–F13, F15–F16 — FAITHFUL (receipts in §5)

### F14 — ORPHANED across waves: the wiring "schema actually applied" proof
- After the i-a DUAL, `TestSchemaIsActuallyAppliedNotJustConstructed` has ONE leg (`brief.name`'s charset ASSERT via `brief_ledger`). 63c-ii DROPs that ASSERT (§4.2) → the class becomes empty and its virtue (*"`ensure_ready` RAN on THIS connection"*) dies unowned. Nothing in the ruling or the i-a contract names it for ii.
- **Recommendation (for the 63c-ii contract brief):** replace the proof with a store fact no ledger app-validates: `INFO FOR TABLE agent` through the registry's OWN connection listing `scope`/`owner_agent` (schema presence), or a raw duplicate `capability_hash` CREATE rejected by the UNIQUE index (`test_agent_owns_principal_schema.py` already has the idiom). Recorded in the amendment doc so it is not rediscovered.

### F17 — the DD-3.c consolidation deviation: ACCEPTABLE
- The message precedent split Leg A into `test_comms_schema.py` because it EXTENDED existing schema pins there; the agent legs share seeders, the frozen/unbounded DDL and the live idiom, all in the F5 home. Mutation-proof declarations are node-id based (`scripts/mutation_proof.py --collect-only`), so file locality is irrelevant to M; the Leg A docstring declares the cross-file set (re-add `role` → Leg A `[role]` + P2 `[agent]`). The wave-suffixed filename follows the house idiom (`test_message_migrate_dirty_store_63b_ii_b.py`). No condition attached.

### F18–F20 — notes (no contract action unless the lead rules otherwise)
- **F18** `LegacyMapping`: 0 prod / 0 test references (`lore_impact`, heuristic) — a docstring-shape; the i-a builder adds *"OWNED-BY-THE-OPERATOR (agent)"* to its docstring (§9 item 9's replacement). Amendment note.
- **F19** ruling erratum E1: §4.4 Leg A says *"the four non-aligned shapes on `agent`"* — there are THREE (name/session/role); the fourth birth ASSERT is `status`, KEPT. The contract is right.
- **F20 (D3)** `test_agent_owns_principal_schema.py::_create_agent` is a second raw-CREATE beside `seed_agent_legacy` (the contract's own docstring: *"predates it"*). Duplication is a design decision (brief-base §6) — rec: fold `_create_agent` onto `seed_agent_legacy` in the i-a build's refactor step (it is the F5 home's purpose); the pkt-62 pins keep their behaviour.

---

## 3. Consumer-law read — the teaching surfaces this contract pins (or should)

| surface | who reads it | what the contract pins | would the agent know what to do? | verdict |
|---|---|---|---|---|
| register refuses hostile `name`/`session` | a freshly-spawned agent, first call | `AgentRegistryError`, not `(assert violation)`, 0 rows | **NO** — no content pinned; a bare error is legal | F5 |
| register refuses blank `role` | same | same | **NO** | F5 |
| P2 `[agent]` RED | the builder who re-adds an ASSERT | message-only prose | **WRONG writer named** | F1 |
| R-Q5-1 refusal reason | the operator at cutover | a `1` somewhere | **NO** — no ids, no remedy | F8/F9 |
| P-A3 refusal (junk status) | the operator | `TxnDomainRejectionError (assert violation)`, zero stamped; heal protocol in the docstring | as P-G3 — the driver redacts the field; the sibling control isolates it | FAITHFUL |
| heartbeat on a `role=""` legacy row | a legacy agent | succeeds after the drop | yes (no denial to read) | F2 for the control |
| KEEP-status guard / P-A2 RED | a builder widening statuses | three-surface drift named | yes | FAITHFUL |

Leg-1 / Leg-2 note: none of the i-a surfaces is a SERVED render (that is i-b's ∀-readers + bound line); the two served texts here are ERRORS, and an error that names no field, rule or remedy is the existence-oracle's benign twin — it leaks nothing and teaches nothing.

---

## 4. Forks (the lead relays; the operator rules scope — I decide nothing)

- **D1 — who owns the F5 write rows (F3).** Options: (a) i-b, named in its brief (rec — the dispatcher sets the per-verb label there; one family, one wave); (b) i-a takes register/re-register now (smaller, splits the family); (c) the security-auditor at 63c close (too late — a build wave would ship an unobserved CREATE).
- **D2 — R-Q5-1's KNOWN BOUND (F9).** Options: (a) pin the bound + trigger now, precondition unchanged (rec — measured absent; widening now is tuning blind); (b) widen now to `owner != operator` (adds a branch for an empty set); (c) neither (an unpinned bound — rejected by standing law).
- **D3 — fold `_create_agent` onto `seed_agent_legacy` (F20).** Rec: yes, in the i-a build's refactor step; alternatively ledger it.

---

## 5. What I verified against production symbols (satisfiability, at `d0c9946` ≡ `0b8ce37` for these files)

- `_governed_index_statements(table)` → `_plain_index(table, f"{table}_scope", …)`, `_plain_index(table, f"{table}_owner_principal", …)` — the contract's index-once names `agent_scope`/`agent_owner_principal` are the emitter's, and `agent_owner_principal` is byte-identical to the pkt-62 inline name (`_agent_statements`) → the IF-NOT-EXISTS no-op the ruling §2.1 relies on holds.
- `_define_field(table, name, type_expr, *, constraint="")` → `DEFINE FIELD OVERWRITE …`; `_memory_statements` builds the governed trio as `_define_field(MEMORY_TABLE, name, type_expr, constraint=constraint) for … in _governed_field_specs()` — the byte-equal pin uses the identical construction → satisfiable on the correct build.
- `AgentRegistry.touch` → `_resolve_row` → `_row_to_agent` (pydantic decode) → UPDATE by `agent.id` → `_select_row` read-back → the heartbeat leg's `last_note == "alive"` is a real read-back (no-op touch reds); junk-status is decode-rejected before the store (F2).
- `AgentRegistry.register` at HEAD: `_agent_id(session, name)` mints; no charset/role check; a hostile value reaches `CREATE … CONTENT` → the store ASSERT → the MOVE pins' RED-at-HEAD reason is as the contract states. `""` as name mints an id and reaches the store too.
- `_migrate_agent_owner` at HEAD: refuses only on operator ambiguity; `UPDATE agent SET owner_principal … WHERE owner_principal IS NONE` → R-Q5-1's RED-at-HEAD reason (stamps the clean rows, skips the trap row, `refused=False`) is as stated; `report_unmigrated_governed_rows(store, table)` is `WHERE scope IS NONE` → R-Q5-2's before/after shape is right.
- `governed_overlay_ddl(table)` emits the three columns + two indexes → the i-a fixtures' "scope exists regardless of the emitter" isolation is real.
- `observe_governed_table_writes(table)` is per-block registration → `agent` can be observed by any wave (F3 is an ownership gap, not a capability gap).
- Deploy state for F9: `podman inspect lore-lore` image created 2026-08-17 20:13 -0400; pkt-62 stamp commit `66b5fa4` 2026-08-24; `a8c17c1` (63a) 2026-08-29.

## 6. Discipline receipts
- lore-first: `lore_index()` (fresh at `f04916d`, then `d0c9946` via git), `lore_get_symbol` ×10, `lore_impact` ×1, `lore_search` ×1 (a stub hit — fell back to `awk` over `governed.py`, SAID). `awk`/`sed` fallbacks, said: the P2 test body + status pins (`test_comms_schema.py`), the P-G3 precedent, `_AGENT_FIELD_SPECS`/`_agent_statements` spans, `_comms_register`'s write_guard absence, `_comms_fakes.py` (no agent charset mirror), the docstring at F4.
- Store law: read §1.1–§1.8 before any DDL verdict; cited, not re-transcribed.
- No worktree; nothing outside the writable set; idle-gate contract written (→ null after this delivery); registered `sidecar-63c-2` (session `63c-20260924`), heartbeats at milestones.
- Attribution: the session-start reminder is overridden by the operator's standing `~/.claude/CLAUDE.md` rule — no trailer on any commit.
- 2026-09-26 am-32 (#17081, read from the lead report — lore client still ECONNREFUSED): FK-ADV-1 Reading B (`TxnRecordExistsError` typed in the ONE driver, both raise sites; RS-5 + keeps catch the class), FK-ADV-2 Reading A (`None` iff the read was gated off — am-31 FK-a28-4 ERRATUM both halves), C1–C3 class routing (K1/K5/K6/K7/K8 AST-equal, K9 with the class), am-31 fold by annotation, R-1..R-6 ruled. `docs/design/2026-09-26-packet63c-amendment-32.md`.
- 2026-09-26 am-33 (#17083, from the native wake; lore client still down): FK-a28b-1 Reading 1 — one class over record-id AND unique-index shapes; text keyed ONLY in the one classifier (two marker pairs), generated pin (c) over {R,U}x{sdk,txn} + controls, pin-the-miss on the untyped InternalError; class RENAMED `TxnUniqueViolationError`. Erratum on am-32 §1.2 (quantifier law). `docs/design/2026-09-26-packet63c-amendment-33.md`.
- 2026-09-26 Task 34 — CONCUR with packet 58 amendment 7 (`01565f9`) against am-32/33: ONE instrument = my import-resolved DOMAIN (Name/Attribute/Tuple, derived re-read, whole tree) + 58 am-5 PARTITION (door iff the caught closure contains TxnContentionExhaustedError, else `_TYPED_CAS_CATCHES`); 63c-i-a lands the scanner with ONE set first, 58 partitions as a delta; `_ROLLBACK_LOG_TIERS` keyed by class with TxnUniqueViolationError → WARNING is consistent with am-33 (text becomes a class ONCE, in the driver). ERRATUM ACCEPTED (am-32 §1.3(f)): "the canonical set gains the RS-5 door and the keeps door" named as DOORS two handlers whose caught class closure cannot contain exhaustion — a28b's `has_guard`-by-`issubclass` makes them TYPED catches with a vacuous guard; the intent (the scanner must SEE both handlers) stands, the classification was wrong. No amendment.
- 2026-09-26 am-34 (Task 35, from the native wake; lore client still down): FK-a28b-4 two sets NOW (58 delta = claim_task, union completeness, runtime cross-check, tier re-key); FK-a28b-2 fifth member `"empty"` + model validator (None keeps one meaning), `mixed` states the total as its only integer; FK-a28b-3 `total_principals`/`admin_principals` are fields, no pin-(2) carve-out; F-5 FIX in i-a (`defined_tables`, `table_defined`, one-read pin); one-scanner pin owned by 63c-i-a. `docs/design/2026-09-26-packet63c-amendment-34.md`.
- 2026-09-27 am-35 (Task 36, from the native wake; lore client still down — `lore_verify` unavailable, names verified by awk over source): THIRD strikes re-open the rulings. STOP-rule applied: neither property is receding (C2 finite domain → generated product; RS-5 under-specified → now fully specified); a28c is the LAST contract round for both by rule (4th strike → pinned bound). C2 = the visibility seam (`resolve_visible_keeps`) as the gate predicate, relation-set powerset × mint orders, both verdicts, seam mutation pin, KE. am-33 §(a) mechanism: R typed on BOTH paths via `parse_query_error` (FK-ADV-3; am-32 §1.1 item 3 erratum), record text pair deleted, U prefix-anchored first, every marker anchored/ordered, KB generated, KA + `_domain_rejection_error` mutation, pin-the-miss. Scanner keyed per HANDLER; F-4 scope restored (D6 DUAL loss); R-2 one-line widening; S1–S3 confirmed 58 am-10. `docs/design/2026-09-27-packet63c-amendment-35.md`.
