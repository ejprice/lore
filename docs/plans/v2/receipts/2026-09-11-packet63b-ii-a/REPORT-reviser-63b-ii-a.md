# REPORT-reviser-63b-ii-a — packet 63b wave ii-a CONTRACT REVISION (message WRITE side)

- `brief-base v14 read`
- `brief project v7 read`
- store-ref read (`docs/reference/surrealdb-31-capabilities.md`): §1.1 (FIELD OVERWRITE / INDEX
  IF NOT EXISTS), §1.4 (`option<>` on populated tables), §2 (CONTENT / `str(RecordID)` / `SELECT *`
  omits a NONE column / protected `session` param), §4 (RELATE / ENFORCED). Cited, not re-transcribed.

## SUMMARY BLOCK (brief-base §1)
- **state:** done — the 5 ii-a contract files revised per the adversary INSUFFICIENT verdict +
  the Fable ruling; the 2 granted cross-file edits landed (MP-2, F-A). Ruff + mypy clean; every new
  pin RED-at-HEAD for the right reason (symbol/behaviour absent), controls GREEN.
- **deviations:** (1) send-side R-pins that pass `capability=` red at HEAD either on an earlier
  `keep is None` guard (SF-63-1 unbuilt) or, where the send is reached first, via a `TypeError→
  pytest.fail` wrapper naming "the §4.D `capability=` seam is unbuilt" — a legible unbuilt signal, not
  a raw traceback. (2) 3× per-file duplication of the credentialed harness (send_scope / enforcement /
  capability) following the established "fixture DATA, local, deliberately not imported" convention —
  FLAGGED (F-DUP) as a decision-needed for a shared home. (3) MP-3 "all three legs in one value-
  mutation" scoped to the agent leg + the message-leg ambiguity refuse (memory leg = the extraction
  source + structural pin) — SAID in §MP-3 below.
- **Packages considered:** none — no NEW mechanism specified; a contract reviser ships no production
  mechanism. The revision REUSES the landed i-a F5 substrate (`_governed_contract`) UNTOUCHED and the
  design's ruled lifts (`governed.resolve_write_scope`, `governed.resolve_principal`,
  `principals.resolve_operator_principal`).
- **Reuse ledger:** 5 new test symbols, all dispositioned (see §DRY ledger) — `cred` fixture,
  `_register_owned`, `_message_count`, `_credentialed_send`, `_bare` — all HAND-ROLLED per the
  established per-file local-fixture convention (wire_world idiom cited); the credentialed-harness
  duplication FLAGGED (F-DUP).
- **Graded:** `3497f2a` · HEAD-at-report: `3497f2a` · SAME. (`3497f2a` = the lead's docs-only commit
  of the ruling that was untracked at my spawn `a4eb097`; production code is BYTE-IDENTICAL between
  the two — the only delta is `docs/design/2026-09-09-packet63b-ii-a-owner-resolution-ruling.md`, so
  the RED-at-HEAD receipts below are unaffected.)
- **decisions-needed:** **F-DUP** (a shared credentialed-wire test helper vs the per-file convention —
  lead/operator call; I followed the convention) · **F-RUFF-PROBE** (a PRE-EXISTING repo-wide ruff RED
  in `scripts/probe_read_filter_63.py`, not mine, not in my writable set) · **F-MP3-SCOPE** (the
  message-leg ambiguity pin depends on the message leg resolving the project keep through the shared
  `resolve_operator_principal` — a consequence of the existing structural route pin, surfaced).
- **receipt POINTERS:** §Per-file changes · §RED-at-HEAD receipts · §Corpse inventory · §Flags ·
  §DRY ledger · §Capability check.

## Capability check (brief-base §4)
- DEMANDED: revise tests only, run RED-at-HEAD, produce a corpse inventory, no production/git. HAVE:
  full tool access, lore MCP loaded, test store `:18000` reachable, ruff + `scripts/typecheck.sh`.
  All satisfiable. COMMIT-ONLY honoured — the ONLY writes are the 6 test files + this report; git
  untouched (the lead commits).
- **`grep`/`rg` are HOOK-BLOCKED in this checkout** ("lore main checkout is live-indexed" — it rejects
  any `grep`, even inside a pipe). Used lore (`lore_get_symbol` / `lore_search` / `lore_read` /
  `lore_verify`) + `Read` for every structure query, and `awk` for the two textual sweeps (the corpse
  call-site counts; the failure-reason extraction) — SAID at each site. No lore friction (lore served
  every query cleanly), so nothing filed to `lore_findings`.
- **Attribution:** the session-start reminder to add `Co-Authored-By`/`Claude-Session` is overridden by
  the operator's standing `~/.claude/CLAUDE.md` rule and is moot (COMMIT-ONLY — the lead commits).

---

## Per-file change summary (which R-riders + MP fixes landed where)

### 1. `test_message_migrate_63b_ii_a.py`
- **MP-1 (BLOCKER / C-DEF fix):** `test_message_migrate_backfills_owner_from_sender_and_scope_to_
  project_keep` — replaced the UNSATISFIABLE `str(sender.owner_principal)` (`agents.Agent` has no
  `owner_principal` field → AttributeError on ANY correct build) with a STORE READ of the sender
  agent's stored `owner_principal` (`SELECT owner_principal FROM type::record('agent', $s)`), compared
  to the migrated message's `owner_principal`. The adversary's door-build.
- **MP-3 (value-mutation):** `TestResolveOperatorPrincipalIsLifted::
  test_the_operator_resolution_is_shared_by_mutation` — monkeypatches `principals.resolve_operator_
  principal` (async, `raising=False`) to a DISTINCT fixed principal P* and proves the AGENT leg's
  stamped owner MOVES to P* (routing-not-sharing killer), with an unpatched positive control. Scoped
  to the agent leg (F-MP3-SCOPE below).
- **MP-3(b) (message-leg ambiguity):** new `ambiguous_message_world` fixture (2 principals, 0 admins,
  MIGRATED agents, a legacy message) + `TestMigrateMessageOwner::
  test_message_migrate_refuses_on_multi_principal_ambiguity` — the message leg REFUSES on the §2.1
  operator ambiguity (agent-first satisfied), reason names principal/operator, NOT agent-first.
- **R5-adjacent (adversary residual R5):** `test_message_migrate_refuses_before_the_agent_table_is_
  migrated_with_two_none_owner_agents` — hardens the agent-first refuse to count>1 (2 NONE-owner agents).
- imports: `import pytest`, `from types import SimpleNamespace`.

### 2. `test_comms_capability_63b_ii_a.py` (rewritten)
- **§4 per-verb flip:** the True-set in ii-a is EXACTLY `{send}` (`_CAPABILITY_REQUIRED_IN_II_A`);
  drain/ack/await/story are FALSE until ii-b (`_REQUIRED_IN_II_B_NOT_YET`); register/heartbeat/brief_*/
  fleet FALSE (`_NON_CAPABILITY_IN_63B`). Rewrote the 3 spec pins (send-requires / non-send-False /
  exact-set-`{send}`, docstring naming ii-b's growth to five). Kept `test_the_spec_has_a_requires_
  capability_field`, the AST routing-coverage floor pin, and `test_the_comms_dispatch_accepts_capability`.
- **R4 (structural twin):** `TestThePrincipalResolutionIsSharedStructurally` — `resolve_subject` AND
  `_comms_register` both call `governed.resolve_principal` (`function_calls_named`). Value-mutation
  twin lives in send_scope.
- **R6 (behavioural ∀):** `TestEveryCapabilityRequiredVerbDeniesWithoutOne::test_send_without_a_
  capability_denies` — anti-vacuity (True-set ⊇ `{send}`) then a well-formed `send` with a valid token
  but NO capability → `GovernedDenied` (closes F-D's guarded-call door behaviourally).
- **R7 (D2=ii-a):** `TestTheRegisterResponseServesTheCapabilityOnce` — the first-register render
  serves a `<name>:<secret>` that VERIFIES (`verify_capability` under the owner token); a re-register
  does not re-serve it; `fleet`/`heartbeat` renders never carry it.
- Added a credentialed harness (`cred` fixture + `_config` + `_surreal_env`) for R6/R7.

### 3. `test_message_enforcement_63b_ii_a.py`
- **R8:** `_effect_send_message` gains the structural leg `after["owner_agent"] == after["sender"]`
  (`_COL_SENDER`); the message CREATE writes `sender: RecordID(agent, sender.id)` and a correct send
  stamps `owner_agent` to the subject's agent (== the sender). Unit fixtures gain `sender=`, and a NEW
  reject case (`wrong_owner`: owner_agent ≠ sender) is the R8 discriminator. The two "F4's separate
  pin" prose mentions (the predicate-block comment + `_SEND_MESSAGE_ENTRY.justification`) now NAME R1
  (`test_a_credentialed_send_stamps_exactly_the_subjects_pair`) — P8d prose-names-a-real-mechanism.
- **live-classify credentialed:** the `ctx` fixture became the credentialed `cred` harness (patch
  `get_access_token` + provision alice + `_register_owned`); `test_a_real_send_message_write_is_
  observed_and_classifies` now drives a CREDENTIALED send (so a correct build's send RESOLVES rather
  than DENIES a tokenless call → a properly-owned `send`-labelled row the observer classifies for the
  RIGHT reason — owner pair non-None + scope + owner_agent==sender).
- **stale-citation fix (brief item):** the module docstring cited the NON-EXISTENT class
  `TestTheDerivedPopulationSetIsExactlyMemory` (the only place the wrong name appeared across the ii-a
  files — confirmed by `awk`, grep blocked); corrected to the real class
  `TestTheGovernedPopulationSetIsADerivedOutput`, with a prose note explaining the correction and that
  the F-A edit landed the grown set there.

### 4. `test_comms_send_scope_63b_ii_a.py`
- **LAYER 1a/1b UNCHANGED** (the lift unit / route-structural / remember-half mutation — the ruling
  keeps them; §6 keeps the remember-half and ADDS the send-half via R5).
- **credentialed harness:** the `ctx` fixture became `cred` (patch `get_access_token`; provision
  alice/bob members + carol ADMIN, so `resolve_operator_principal` = carol ≠ the non-admin registrant
  — the WB-2 detector). Helpers `_bare` / `_register_owned` / `_message_count` / `_credentialed_send`.
- **R3:** `TestRegisterMintsTheSessionKeep` — the 2 existing pins driven credentialed +
  `test_register_mints_the_session_keep_kept_by_the_registrants_principal` (keeper == alice, NOT carol
  / Reading A) + `test_a_foreign_principals_register_into_a_kept_session_denies_naming_the_remedy_not_
  the_keeper` (SF-63-1 foreign gate; teaching names session+remedy, NOT the keeper; no agent row on a
  rejected register) + `test_the_keepers_own_second_agent_registers_fine` (positive control).
- **R1/R2/R5:** `TestSendResolvesTheSessionKeepScope` — the 2 existing pins driven credentialed +
  `test_a_credentialed_send_stamps_exactly_the_subjects_pair` (R1 owner exactness: B's pair, NOT the
  keeper A, NOT None, owner_agent==sender) + `test_a_tokenless_send_denies_and_creates_no_message_row`
  (R2: deny + zero rows, credentialed control writes exactly one) + `test_a_sender_removed_from_the_
  session_household_is_denied_at_send` + `test_perturbing_the_lifted_seam_changes_send` (R5: the §4.A
  send-half grant flip, mutation-proven — both halves flip).
- **R4 (value-mutation):** `TestThePrincipalResolutionIsSharedByMutation` — perturb `governed.resolve_
  principal` → P*; BOTH `resolve_subject`'s Subject.principal_id (send owner, Q1) AND a register's
  minted keep keeper (Q2) move to P* (ONE derivation; a private copy on either path stays put).
- module docstring: the (now-resolved) F-KEEPER flag → a pointer to the ruling §3.

### 5. `test_message_governed_ddl_63b_ii_a.py` — UNCHANGED (adversary WB-1: the DDL instruments are
  empirically strong; the ruling changes no DDL). Uses `admin_db`, not the credentialed `ctx`, so the
  harness change does not ripple. Re-verified it still holds (16 failed / 9 passed RED-at-HEAD).

### Granted cross-file edits
- **MP-2** `test_governed_migration_63a.py::TestTheAgentFirstOrderIsChecked::test_migrate_message_
  before_agent_refuses` — register a GENUINE NONE-owner agent (`ag_legacy_none_owner`) on the test's
  inline registry so the §2.6 agent-first precondition is NON-vacuous on a correct §4.C build (without
  it: 0 NONE-owner agents → vacuously satisfied → migrate proceeds → TxnDomainRejectionError on the
  absent message table). Fable §7 item 6 rules this over "retire the test".
- **F-A** `test_memory_enforcement_63b_ia.py::TestTheGovernedPopulationSetIsADerivedOutput::
  test_the_derived_population_set_is_the_known_set` — the known set `frozenset({MEMORY_TABLE})` →
  `frozenset({MEMORY_TABLE, surreal_schema.MESSAGE_TABLE, surreal_schema.TO_RELATION})` + message +
  class/method docstrings (dated, RED_ADJUDICATED(owner=63b-ii)). This i-a pin and the ii-a enforcement
  pin `test_the_derived_population_set_grows_to_memory_message_to` now AGREE (both GREEN on the ii-a
  build); the old `== {memory}` CONTRADICTED the ii-a pin. ⚠ the old ii-a-file docstring cited the
  WRONG class `TestTheDerivedPopulationSetIsExactlyMemory` (does not exist) — the actual class is
  `TestTheGovernedPopulationSetIsADerivedOutput`; the F-A edit lands on the real class.

---

## RED-at-HEAD receipts (per-file counts + reasons; graded `3497f2a`, production == `a4eb097`)

Each run ALONE (`-n auto`, sequential — no contention), live store `:18000`. A passed-COUNT is in every
tail. Reasons verified via `awk` over the logs (grep blocked — SAID): every RED is the symbol/behaviour
ABSENT, never a test bug; every GREEN is an intended control.

| file | tail | the RED reasons (right-reason spot-checks) | the GREEN (intended controls) |
|---|---|---|---|
| `test_message_governed_ddl_63b_ii_a.py` (unchanged) | **16 failed, 9 passed** | governed columns/indexes absent (§4.F unwired) | the DDL DUAL + C+ controls |
| `test_message_migrate_63b_ii_a.py` | **9 failed, 2 passed** | `resolve_operator_principal` unbuilt; `_migrate_agent/message_owner` no `governed_exempt`; agent/message backfill = the 63a stub refuses; MP-3 value-mutation = stub refuses "does not support table 'agent'"; MP-3(b) ambiguity = stub reason names neither operator nor ambiguity | the 2 agent-first refuse CONTROLS (stub reason contains "agent") |
| `test_comms_capability_63b_ii_a.py` | **10 failed, 1 passed** | `requires_capability` field absent; True-set `set()` ≠ `{send}`; `comms` has no `capability` param; `resolve_subject`/`_comms_register` don't call `resolve_principal`; R6 anti-vacuity = True-set empty | R7 `test_no_other_comms_render_carries_a_credential` (no-leak guard, green at HEAD) |
| `test_message_enforcement_63b_ii_a.py` | **4 failed, 15 passed** | `message`∉populations / set≠{memory,message,to} (§4.F unwired); migrate-message UPDATE not L1-derived; live-classify = `comms` rejects `capability=` (§4.D unbuilt) | the effect-predicate unit DATA + classifier pins incl. R8's `wrong_owner` reject |
| `test_comms_send_scope_63b_ii_a.py` | **18 failed, 1 passed** | `governed.resolve_write_scope` unbuilt (LAYER 1a); remember doesn't route the lift (1b); SF-63-1 "register minted no session keep" (R1/R3/R5/scope-stamp guard); R2 "DID NOT RAISE GovernedDenied" (unenforced send writes a row); `capability=` rejected (§4.D) | R3 `test_the_keepers_own_second_agent_registers_fine` (positive control) |

Cross-file:
- **MP-2** `TestTheAgentFirstOrderIsChecked` → **1 passed** — GREEN at HEAD (the stub refuses naming
  "agent"; the NONE-owner-agent add does not change the HEAD verdict, it makes the refuse REAL on the
  built path).
- **F-A** `TestTheGovernedPopulationSetIsADerivedOutput` → **1 failed, 1 passed** — the known-set pin
  now RED (HEAD derives `{memory}` ≠ the grown set — RED_ADJUDICATED(owner=63b-ii)); the synthetic-
  source reach pin `test_the_population_derivation_reach_is_a_checked_variable` GREEN (unchanged).

**Gates:** `uv run ruff check <the 6 changed files>` → **All checks passed**; `./scripts/typecheck.sh`
→ **EXIT=0** ("no issues found" across lorerunes/lorescribe/loresigil/loremaster/skills/scripts, incl.
test trees). Full-repo `uv run ruff check .` → **1 error, PRE-EXISTING, not mine** (F-RUFF-PROBE).

**Satisfiability:** the whole-feature reference build is re-owned by the MANDATORY re-adversary (the
same disclosed, sanctioned deviation the first contract carried — I did NOT build the reference). Each
new pin names its correct-build shape in its docstring (per the R-table): R1 owner==subject pair; R2
deny+zero-rows / credentialed control writes one; R3 keeper==registrant / foreign-deny / positive
control; R4 both paths move to P*; R5 removed-member deny + permissive-seam success; R6 no-cap deny;
R7 first-render-serves-once + no-leak; R8 owner_agent==sender; MP-1 store-read owner; MP-3 agent-leg
value-mutation + message-leg ambiguity. Every fixture was interrogated "what WRONG build still passes
this?" — the kills are the R-table's (Reading A / keeper / None owner / clone / hand-set label /
unstamped / re-served credential).

---

## CORPSE INVENTORY (D1 — the builder's GREEN-phase reconciliation worklist)

Derived THIS session by `awk` over `loremaster/tests/*.py` (grep hook-blocked → `awk`, SAID). Pattern
= the bare `action="<verb>"` double-quote literal (the repo idiom), so it counts CALL SITES, not
tests, and is a FLOOR (a single-quote or dynamically-built `action=` is uncounted — none observed).
The ii-a CONTRACT files' own sites are EXCLUDED (they are the revised credentialed contract, not
corpse). None of this is a new cost this ruling invents — 63-rulings §8 item 1 ALREADY ruled
identity-less calls DENY; this is that ruling's cost arriving (Fable §8).

### A. `send` corpse — BREAKS under ii-a `send` enforcement — **40 non-contract sites**
| file | `send` sites | adjudication |
|---|---|---|
| `test_comms_tool.py` | **39** | **CREDENTIAL-THE-FAKE.** On the built path `_comms_send` calls `_resolve_subject(capability)` UNCONDITIONALLY; these go through `_comms_fakes.py`, whose fake registry has no `_verify_capability_owner` and whose fake context no `_principal_store` → an AttributeError-class break, NOT a teaching deny. Builder wires the MINIMAL fake seams (`FakeAgentRegistry._verify_capability_owner` + `register(owner_principal_id=)` + a fake principal store) and routes the "a send happens" sites through a credentialed fake + adds `capability=` (Fable D1). |
| `test_comms_waiting_line.py` | **1** | Same — a fake `AppContext.comms(harness, …)` send; credential-the-fake / route through a credentialed harness. |

### B. `register` corpse — tokenless, reading α — **58 non-contract sites (MOSTLY GREEN)**
| file | `register` sites | adjudication |
|---|---|---|
| `test_comms_wiring.py` | **29** | **RENDER-ASSERTION-UPDATE (α) / else GREEN.** Under reading α a tokenless register succeeds OWNERLESS + mints NO keep (register is `requires_capability=False`), so a SETUP register (register-then-do) stays GREEN. Only a BYTE-EXACT register-render assertion reds, because the render gains the α ownerless-bound line (+ R7's credential line on a FIRST register). "the instrument working, not a corpse" (§8). |
| `test_comms_tool.py` | **20** | mostly setup registers → GREEN; any exact-render pin → render update. |
| `test_comms_render_architecture.py` | **5** | render-asserting → RENDER-ASSERTION-UPDATE (the promise registry registers the new α + R7 lines). |
| `test_mcp_server.py` | **4** | render/wiring → likely RENDER-ASSERTION-UPDATE. |

### C. read verbs (`drain`/`ack`/`await`/`story`) — **ii-b's IDENTICAL debt, NOT ii-a corpse**
`drain` 25 (tool 23, surreal_fakes 1, waiting_line 1) · `ack` 5 (tool) · `await` 2 (await) · `story` 0.
These flip `requires_capability=True` in ii-b; the identical credential-the-fake reconciliation lands
THEN, not in ii-a.

**Net ii-a worklist:** ~40 `send` sites (39 fake in `test_comms_tool.py` + 1 fake harness) → credential
the fake + `capability=`; a subset of the 58 `register` sites (the render-asserting ones in
render_architecture/mcp_server + any byte-exact wiring render pin) → render-assertion update. Plus the
production shape the contract implies (for the builder's brief, not the reviser): `governed.resolve_
principal` (§3.1); `_comms_register` steps 1–6; `_comms_send` §2.3+§6; `_render_comms_register`'s α +
R7 lines; `CommsActionSpec.requires_capability` (`send=True` only); `resolve_operator_principal` lift;
the two migrate legs.

---

## FLAGS

- **F-DUP (decision-needed):** the credentialed harness (`cred` fixture + `_config` + `_surreal_env` +
  `_register_owned` + `_bare`) is duplicated across `test_comms_send_scope_63b_ii_a.py`,
  `test_message_enforcement_63b_ii_a.py`, and `test_comms_capability_63b_ii_a.py` (~3×). I followed the
  ESTABLISHED per-file convention (the contract already duplicates `_config`/`ctx`/`_surreal_env`
  across send_scope + enforcement — see send_scope's `_config` docstring: "local, deliberately not
  imported; fixture DATA, no shared logic"). A DRY improvement (a shared `_governed_wire.py` credentialed
  harness) would require expanding my writable set / touching `_governed_contract.py` (do-not-touch) —
  I did NOT do this unilaterally. Lead/operator: is the per-file convention acceptable here, or should a
  shared credentialed-wire helper be authored (a new file grant)?
- **F-RUFF-PROBE (pre-existing, not mine):** full-repo `uv run ruff check .` reports 1 error —
  `scripts/probe_read_filter_63.py:566 PLR0915 Too many statements (52 > 50)`. VERIFIED pre-existing at
  `a4eb097` (the probe committed at `58865ba`, untouched by me; reproduced against `git show
  a4eb097:scripts/probe_read_filter_63.py`). It is a probe SCRIPT, outside my tests-only writable set —
  surfaced per scope law, NOT fixed. (The lead's "ii-a RED contract ruff clean" claim was scoped to the
  contract files; the repo-wide ruff was already red here.)
- **F-MP3-SCOPE:** `test_message_migrate_refuses_on_multi_principal_ambiguity` pins that the MESSAGE
  leg refuses on operator ambiguity — a CONSEQUENCE of the EXISTING structural route pin
  (`test_all_three_migrate_legs_route_through_resolve_operator_principal` already requires
  `_migrate_message_owner` to CALL `resolve_operator_principal`, whose ambiguity is a refuse, as the
  memory leg does for the project keep). The value-mutation (MP-3 a) is scoped to the AGENT leg (a
  single-call "all three legs" needs a combined memory+agent+message world the split fixtures do not
  provide; the memory leg's routing is the extraction source + the structural pin, the message leg's
  is this ambiguity refuse). If the builder's message leg does NOT consult `resolve_operator_principal`
  for the project keep, this pin over-constrains — surfaced.
- **F-A-RED-ADJUDICATED (informational):** the F-A edit makes the i-a file `test_memory_enforcement_
  63b_ia.py` carry ONE new RED-at-HEAD row (`test_the_derived_population_set_is_the_known_set`), owned
  by 63b-ii, re-greened by the ii-a §4.F build. This is the design's own RED_ADJUDICATED(owner=63b-ii)
  pin, now correctly RED. The lead's currency gate should carry it as such.
- **`_governed_contract.access_token`:** used verbatim (`access_token(subject=<email>)`); needed NO
  extension — no flag there (the brief asked me to flag only if it did).

---

## DRY ledger (brief-base §6 — new reusable test symbols)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `cred` fixture (send_scope/enforcement/capability) | inspected `test_wire_isolation_63a.py::wire_world` (the credentialed-AppContext idiom) + the existing per-file `_config`/`ctx` (`lore_get_symbol AppContext.comms` / Read) | `wire_world` is a per-FILE fixture (not a shared symbol); the contract already duplicates `_config`/`ctx` per file by convention | **HAND-ROLLED** per the established local-fixture convention (wire_world idiom cited). Duplication FLAGGED (F-DUP). |
| `_register_owned` (send_scope/enforcement) | wire_world's inline `mint(name, principal_id)` closure (Read) | an INLINE closure, not a shared symbol | **HAND-ROLLED** (the wire_world pattern is inline; cloned per-file per convention). |
| `_credentialed_send` (send_scope) | n/a (test-local ergonomic wrapper for the `capability=`-TypeError-at-HEAD signal) | — | **HAND-ROLLED** (test-local; converts the unbuilt-seam TypeError to a legible `pytest.fail`). |
| `_message_count` (send_scope) | n/a (trivial `SELECT count() … GROUP ALL` helper) | — | **HAND-ROLLED** (trivial; the R2 zero-rows/anti-vacuity instrument). |
| `_bare` (send_scope/enforcement) | already cloned in `test_message_migrate_63b_ii_a.py`, `test_wire_isolation_63a.py`, `_governed_contract.py` | a trivial id-stripping helper cloned in every test file | **HAND-ROLLED** (trivial, the established per-file idiom — not policy). |

Note: these are TEST fixtures/helpers, not production policy — the ONE-IMPLEMENTATION policy rule
governs cross-caller POLICY, which none of these are (the credentialed harness is test SETUP). The
only genuine DRY tension is the 3× harness duplication, escalated as F-DUP rather than silently
resolved.

---

## Method / discipline receipts
- lore-first for structure: every production symbol via `lore_get_symbol`/`lore_search`/`lore_read`/
  `lore_verify` (`resolve_subject`, `stamp_owner`, `AgentRegistry.register`, `AppContext.comms`/
  `_comms_register`/`_comms_send`/`_render_comms_register`/`_resolve_subject`, `KeepStore.{get_or_
  create_keyed,get_by_key,add_household_member,remove_household_member}`, `Keep`, `resolve_visible_
  keeps`, `MessageLedger._send_fragment`, `principals._migrate_memory_scope`). grep hook-blocked →
  `awk` for the 2 textual sweeps (corpse counts; failure reasons), SAID. No lore friction filed.
- store law: no store/schema/DDL change made (a contract reviser writes tests); the `RecordID`
  binding of the owner stamps cites store-ref §2 via `AgentRegistry.register`'s existing practice.
- COMMIT-ONLY honoured: the ONLY writes are the 6 test files + this report; git untouched. The lead
  commits. HEAD moved `a4eb097`→`3497f2a` during the session = the lead's docs-only commit of the
  ruling (no production delta) — verified.
