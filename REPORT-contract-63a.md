# REPORT-contract-63a — packet 63a governed substrate + memory retrofit CONTRACT (RED)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read FIRST (this is store/schema/DDL/migration contract work):
  `docs/reference/surrealdb-31-capabilities.md` — cited by § below (§1.1 OVERWRITE-for-fields /
  IF-NOT-EXISTS-for-indexes; §1.4 option<> on a populated table + "a DEFAULT does not rescue a
  legacy row" + the write-the-legacy-row-UNDER-THE-OLD-DDL fixture trap; §1.5 a DEFINE INDEX
  builds; §1.6 the dirty-store blind spot; §1.8 UNIQUE over option<> = multiple NONE coexist;
  §2 CONTENT / protected names `session`/`scope` / record<> links do not auto-clean; §3
  statement[0]-only validation → execute_transaction; §5 hot-row CAS mint). Never re-transcribed.

## SUMMARY BLOCK

- Receipt: `brief-base v14 read` · `brief project v7 read` · store reference read FIRST (cited by §)
- State: **done-with-deviations** — the runnable-RED contract is written, gate-clean, RED-verified.
- RED count: **`pytest -n auto <the 6 new modules>` → 52 failed / 12 passed** (the 12 are GREEN
  positive-controls/discriminators that MUST be green at HEAD — §1.4 option<> survival, C+ TableScan
  controls, the F2 PDP-soundness control, the #425 correctness control, the routing anti-vacuity +
  grows-and-reds discriminators). Every RED verified for the RIGHT reason (per-module runs in the body).
- Deviations (2, both directly-caused + disclosed): **(D1)** relaxed the 62 pin
  `test_agent_capability_reach.py::test_every_governed_tool_is_pending_owner_stamp_and_adjudicated`
  from `governed == pending` to `pending ⊆ governed` (FORK 4 — 63a de-pends 2 tools; orphan-detection
  RELOCATED to the #420 verb pin). **(D2)** the `resolve_subject` happy-path uses a REAL registry +
  minted capability (not a FakeRegistry) so it is robust to #425's resolution (FORK 3).
- **Packages considered:** none — no new mechanism specified. I consume the design §8 ledger (the
  migration verb is `bespoke` — design read the `surrealdb` 2.0.0 SDK exposes no migration API; no
  package targets SurrealQL DDL/DML). Test-side: the EXPLAIN plan-walker is **MIRRORED** from the
  shipped `test_keeps_schema.TestTheKeeperIndexFires` (cited, not forked — instrument parsing).
- **Reuse ledger:** 12 new production STUB symbols (the builder implements; all dispositioned by the
  design §8 reuse ledger — I only stub them RED) + the shared test substrate (design §1.2 item 6
  mandates it). Full DRY ledger in §DRY below.
- Graded: N/A (contract authoring — renders no verdict on another artifact) · authored against
  design `docs/design/2026-08-28-packet63-retrofit-rulings.md` + `REPORT-probe-63.md` · HEAD-at-report
  `d37044f` (branch `feat/surreal-unification`; `lore_index` watched root `/workspace` @ `d37044f`).
- Decisions-needed (5 forks — ALL surfaced below, NONE silently resolved): FORK 1 (Resource NONE-scope
  representation) · FORK 2 (the #420 adjudication home — NOT pending_contracts.yaml) · FORK 3 (#425
  verify_capability return breaks ~14 shipped 62 assertions — additive vs literal) · FORK 4 (the
  reach-pin relax, HANDLED) · FORK 5 (the retrofit seam shape — `capability=` vs `subject=`, isolated).
- ⚠ **I did NOT commit** (brief-base §2 "The lead commits"; the spawn brief describes the target
  commit but is ambiguous on WHO runs git — I defer to the standing law). The lead commits the 13-file
  set (§COMMIT below) as ONE concern with the brief's message + trailers.
- Receipt POINTERS: the pin inventory → §9-RIDER-MAP; the satisfiability plan → §SATISFIABILITY; the
  forks → §ESCALATIONS; the gate receipts → §GATES; the commit set → §COMMIT.

## GATES (receipts)

- `uv run ruff check <12 files>` → **All checks passed!**
- `bash scripts/typecheck.sh` → **PASS (exit 0)** — loremaster OK + all legs OK (the stubs +
  test trees typecheck; the async seams + `option<>` Sequence types fixed).
- `pytest -n auto <6 new modules>` → **52 failed / 12 passed** (runnable-RED; passed-count present).
- Regression: `pytest -n auto test_agent_capability_reach.py test_agent_owns_principal_schema.py
  test_keeps_schema.py` → **86 passed** (the D1 relax + the surreal_schema/keeps/principals stubs
  break NO existing 60/62 test).

---

## PLAN (the pin inventory, mapped to design §9's rider roll-up)

The design authority is `docs/design/2026-08-28-packet63-retrofit-rulings.md`. My spec is its
§0/§1.2/§2/§3.2/§4.1/§4.3/§5/§9. This contract is **63a only**: the shared governed substrate +
the MEMORY retrofit + #425 + the #420 routing pin + the migration verb + SF-63-4. It is
COMMIT-ONLY (deploy = packet 65); no pin assumes a live-fleet reconfig.

### Test modules (all under `loremaster/tests/`)
1. `_governed_contract.py` — the shared test substrate: the FOUR parametrised pin families
   (F1 dirty-store migration, F2 single-brain oracle, F3 cross-principal isolation ∀ read verbs,
   F4 anti-injection fuzz ∀ write verbs), parametrised by (table, verb list, seed fn) so a
   governed table's contract is a parametrisation, never a copy.
2. `test_governed_schema_63a.py` — the store-law DDL via the ONE emitter (§4.1): offline clause
   pins + live round-trip + P1/P2/P3/P6 EXPLAIN schema pins (the shipped walker + C+ controls) +
   SF-63-4 keep.key UNIQUE.
3. `test_governed_substrate_63a.py` — the six seams (§1.2): resolve_subject (fail-closed, ONE
   Subject constructor R-a.2), read_filter (splice, R-a.3 mutation), guarded_write (guard +
   audit compose + 0-rows GovernedConflict + single-brain-on-writes).
4. `test_memory_retrofit_63a.py` — lore_remember/recall + backend remember/invalidate route
   through the substrate; default scope = project keep; identity-less DENY (removed-behavior 1).
5. `test_425_stamp_owner_63a.py` — #425 CLOSE (§5): verify_capability returns the pair,
   owner_principal_of DELETED, stamp_owner = ONE `_query` round-trip; 62 security fixture re-run.
6. `test_governed_migration_63a.py` — `lore-adm migrate-governed` + LegacyMapping: F1 dirty-store
   over memory (member-invisible→admin-visible BEFORE; project-keep-visible AFTER; idempotent;
   agent-first ORDER precondition), boot WARNING NONE-count, project keep mint (key='project:lore').
7. `test_governed_routing_63a.py` — the #420 verb-routing coverage pin (DERIVED set × dispatch,
   RUNTIME-observed; grows-and-reds).

### Stubs (runnable-RED; NO real implementation logic)
- `loremaster/loremaster/governed.py` (NEW) — resolve_subject / read_filter / guarded_write +
  GovernedDenied / GovernedConflict / GuardedWriteResult / LegacyMapping (NotImplementedError
  bodies / minimal dataclasses).
- `surreal_schema.py` — `_governed_field_specs()` / `_governed_index_statements(table)` stub
  symbols (exist so mutation pins can monkeypatch; NOT yet wired into the generators → schema
  pins RED).
- `keeps.py` — `KeepStore.get_or_create_keyed` stub (NotImplementedError).
- `principals.py` — the `migrate-governed` verb stub (NotImplementedError).
- #425: NO stub — verify_capability / owner_principal_of / stamp_owner already exist; the pins
  assert the NEW shape (RED at HEAD, GREEN when the builder edits).
- `scripts/pending_contracts.yaml` — the #420 verb-routing adjudications (owner + trigger).

### §9 rider → pin map  *(filled as pins land)*

(§9.1 R-a.1–R-a.5; §9.2 migration; §9.3 defaults; §9.4 63↔64 routing; §9.5 store law;
§9.6 #425; §9.7 §9 isolation; §9.8 renders; §9.9 prose currency.)

---

## CONSUMED SHIPPED SIGNATURES (60/61/62 — verified via `survey-63a-pdp`, lore_get_symbol/HIGH)

`lorerunes.pdp` (stdlib-only, `@dataclass(frozen, slots)`):
- `Subject(principal_id: str, agent_id: str, role: str, visible_keep_ids: frozenset[str])` —
  ⚠ order (principal_id, agent_id, role, keeps); `__post_init__` raises on empty principal_id
  OR agent_id (SEC-F3) and role∉PRINCIPAL_ROLES.
- `Resource(table: str, owner_principal: str|None, owner_agent: str|None, scope: str)` —
  ⚠ **scope is `str`, no default; an invalid scope RAISES `ValueError` (`_is_valid_scope`);
  owners None-legal (absent/option<>) but present-empty-string RAISES (forgery)**. No None-scope.
- `authorize(subject, action, resource, *, target_scope: str|None=None) -> Decision(.allowed,
  .requires_audit)`; `authorize_filter(subject, action, table, *, target_scope=None) -> Predicate`.
  `Predicate.to_surql() -> tuple[str, dict[str,str]]` (self-contained parenthesised fragment +
  content-addressed params); `Predicate.matches(resource) -> bool`.
- `Action` = {READ, WRITE, DELETE, SET_SCOPE, SET_OWNER} (5). `_AUDITED_ACTIONS` = all−READ (derived).
- `SCOPE_SERVER='server'`, `SCOPE_PRINCIPAL_PRIVATE='principal-private'`,
  `SCOPE_AGENT_PRIVATE='agent-private'`; `keep_scope(id)->'keep:id'`; `_is_valid_scope`;
  `_grantable(subject, target_scope) -> bool` (None→False; fixed→True; else target∈visible_keeps).
- IR nodes: ScopeEq/OwnerPrincipalEq/OwnerAgentEq/ScopeInKeeps/And/Or/AllRows/NoRows.
  admin READ→AllRows('true'); admin mutating on AUDIT_TABLE→NoRows; member→_member_filter.
- Single-brain pins: `lorerunes/tests/test_pdp_core.py::TestAuthorizeIsAuthorizeFilterMatches`
  (in-mem) + `loremaster/tests/test_pdp_oracle_61b.py` (live-store oracle over synthetic `gov`).
- `resolve_visible_keeps(keep_store, *, member_email) -> frozenset[str]` lives in
  **`loremaster.visible_keeps`** (NOT pdp); uses `keep_store.list_keeps_for_member`.

Packet 62 / server:
- `stamp_owner(access_token, agent_capability, *, registry) -> tuple[str,str]`
  (owner_principal, owner_agent — bare `str` ids) in `owner_stamp.py`; **TWO round-trips today**
  (verify_capability → owner_principal_of); raises `OwnerStampError`.
- `AgentRegistry.verify_capability(presented, access_token) -> str|None` (agent id only; its
  SELECT already projects `owner_principal.email AS owner_email` for the binding) —
  `AgentRegistry.owner_principal_of(agent_id) -> str|None` (ONLY consumer = stamp_owner).
- `partition_tools_by_population(tools) -> (shared_read: frozenset[str], governed: frozenset[str])`
  in **`loremaster.server`**; governed = every live tool ∉ shared_read (fail-closed).
- `_COMMS_ACTIONS: dict[str, CommsActionSpec]` (server.py; CommsActionSpec(handler, params,
  required, requires_registration, limit_cap)); iterated by
  `test_render_seam_pins.py::assert_actions_covered`.
- `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` = {lore_comms, lore_recall, lore_remember, lore_tasks,
  lore_claim_task, lore_findings} → pending trigger; KEYS must equal
  `partition_tools_by_population(...).governed` (coverage-as-checked-variable). Self-destructs per tool.
- `AppContext.remember(text, *, refs, metadata, kind, trust, importance, supersedes, labels) -> str`
  and `AppContext.recall(query, k, *, kind, labels) -> str` and `AppContext.comms(*, action, agent,
  …)` — ALL carry NO identity/capability arg today. `token_verifier` sets `access_token.subject =
  principal.email` (confirmed).

---

## ⚠ ESCALATIONS / FORKS (surfaced per brief-base §2 — not silently resolved)

**FORK 1 — F2 single-brain over a NONE-SCOPE dirty row requires representing scope=None on the
Python side; today `lorerunes.Resource(scope=…)` RAISES `ValueError` on a non-domain scope and
`scope` is a required `str` (no None).** Design §2.3 RIDER: *"the substrate's Python leg must map a
NONE-scope row to DENY (never raise on Resource construction, never skip it) so authorize(row) ≡
filter.matches(row) holds on dirty rows too."* For the single-brain oracle to run over a NONE-scope
legacy row, `matches(Resource(scope=None))` must be evaluable and DENY for a member / be AllRows-true
for admin — which is exactly what `matches` already computes IF the Resource can hold scope=None.
Two readings: **(1)** widen `lorerunes.Resource.scope` to `str|None` (None = a legal LEGACY scope,
distinct from the empty-string forgery `__post_init__` still rejects) — minimal, additive, PRESERVES
single-brain, emits byte-identical SurrealQL (so it does NOT violate §4.2 "63 adds nothing to the
predicate"); **(2)** keep Resource unchanged and have the substrate short-circuit a NONE-scope row to
member-DENY/admin-allow WITHOUT calling `authorize` — which reintroduces a SECOND decision path (the
#102 defect single-brain exists to prevent). **RECOMMENDATION: reading (1)** — it is the only one that
keeps `matches` the sole decider. This touches `lorerunes` (outside my do-not-touch's "additive
substrate" if read narrowly), so it is a WHERE-does-shared-code-change design call for lead-63/operator.
**Contract stance:** I pin the OUTCOME property through the substrate seams (read_filter excludes the
NONE-scope row for a member and includes it for admin; guarded_write DENYs a member on it) — NEVER a
raw `pdp.Resource(scope=None)` call — so the pin is implementation-agnostic and does not trap the
builder (C-DEF). Confirm reading (1) is in 63a's writable set, or route the Resource widening as a
named lorerunes touch.

**FORK 2 — the #420 per-VERB routing adjudication cannot live in `scripts/pending_contracts.yaml`.**
Design §3.1 + my brief say un-routed verbs are "RED_ADJUDICATED in `scripts/pending_contracts.yaml`
with owner + trigger." But that file is a pydantic model with **`extra="forbid"` at the top level**
(`pending_contract_gate.py::_PendingRegistry`, `version:int` + `bounds:tuple[...]`), and `bounds` is a
mypy-typecheck-bound schema (`missing_symbols`/`unsymboled_codes`) — a verb-routing adjudication is a
category mismatch, and adding a new top-level key FAILS the gate's validation. **RECOMMENDATION:** home
the per-verb adjudication in a NEW `loremaster.server` constant `_GOVERNED_VERBS_PENDING_ROUTING:
dict[tuple[str,str], str]` ((tool, verb) → trigger), a direct SIBLING of the existing per-TOOL
`_GOVERNED_TOOLS_PENDING_OWNER_STAMP` (the established, machine-checkable, self-destructing precedent) —
NOT pending_contracts.yaml. My routing pin (`test_governed_routing_63a.py`) reads that constant. If
lead-63 wants it in a dedicated yaml instead, the pin moves; the coverage-as-checked-variable INVARIANT
is identical either way. (This mirrors 62's own note at `test_agent_capability_reach.py:22-32`.)

**FORK 3 — #425 changing `verify_capability`'s return type falsifies ~14 shipped 62 assertions.**
Design §5 literally says "Have verify_capability return the verified (agent_id, owner_principal_id)
pair." But **~14 assertions across `test_agent_capability.py` (13) + `test_agent_capability_seams.py`
(1) pin `verify_capability(cap, token) == result.agent.id`** (a bare `str`). Changing the return to a
pair breaks every one — a large edit to TWO shipped 62 test files, and it contradicts the §5 rider "the
62 security fixture re-run green" (they can't re-run green if their return-shape assertions break).
**RECOMMENDATION:** close #425 the ADDITIVE way — keep `verify_capability -> str|None` backward-
compatible and give `stamp_owner` a single-read pair-yielding path (both sharing ONE internal SELECT so
there's no duplicate query), then DELETE `owner_principal_of`. This achieves the identical
one-read/no-TOCTOU property with ZERO breakage. My #425 pins are deliberately **FORM-AGNOSTIC** (they
pin "exactly ONE `_query` round-trip" + "owner_principal_of deleted", never `verify_capability`'s return
shape), so they trap NEITHER reading. If lead-63/operator wants the literal return change, the ~14 sites
must be updated (directly-caused) — flag which agent owns that.

**FORK 4 (interaction) — 63a de-pending memory tools breaks the existing tool-level coverage pin.**
`test_agent_capability_reach.py::test_every_governed_tool_is_pending_owner_stamp_and_adjudicated` pins
`governed == frozenset(_GOVERNED_TOOLS_PENDING_OWNER_STAMP)`. Design R-a.5 removes lore_remember/
lore_recall from that dict at 63a GREEN (they become ROUTED, still governed) → the equality breaks
(`governed`=6, `pending`=4). This is a directly-caused consequence of 63a. **HANDLED:** I minimally
relax that existing pin to `frozenset(pending) <= governed` (+ the non-empty-trigger check), and RELOCATE
the full orphan-detection (governed == observed ∪ adjudicated) to the finer #420 verb pin in
`test_governed_routing_63a.py` (disclosed as a directly-caused edit; the removed-behavior — tool-level
orphan detection — is PRESERVED by #420).

**FORK 5 — the exact seam by which identity flows into the retrofitted recall/remember is a
builder/design ruling.** The design (§0 item 2) says memory verbs "route through the substrate" but
does not fix the SIGNATURE: a `capability=` arg resolved to a Subject inside the backend, vs a
`subject=` arg resolved at the AppContext, and required (TypeError) vs optional-with-DENY. **HANDLED
(the 62 `_call_stamp_owner` precedent):** the retrofitted call is ISOLATED in `_exercise_recall` /
`_exercise_remember` (test_memory_retrofit_63a.py), so a signature ruling is a ONE-function edit and
traps no build. The design's stated shape is `capability=`; the pins assert OBSERVABLE behaviour
(isolation, owner stamp, default scope, identity-less DENY) never the wiring. **The identity-less-DENY
pin pins the design's "teaching error" (GovernedDenied, NOT a TypeError)** — a builder who makes
identity a required positional (TypeError) violates the removed-behavior-1 ruling; the adversary
should confirm the DENY is a teaching error.

---

## §9-RIDER-MAP — every design §9 rider → the pin that enforces it

| §9 rider | pin(s) |
|---|---|
| **R-a.1** substrate-with-consumer coverage (memory routed, rest adjudicated) | `test_governed_routing_63a::test_the_memory_verbs_are_routed_not_adjudicated` + `test_every_governed_verb_is_routed_or_adjudicated` |
| **R-a.2** ONE `Subject` constructor (allowlist resolve_subject) | `test_governed_substrate_63a::TestResolveSubjectIsTheOneSubjectConstructor` (AST scan) |
| **R-a.3** ONE splice (read_filter delegates to authorize_filter, mutation-proven) | `test_governed_substrate_63a::TestReadFilterIsTheOneSplice` (byte-equality delegation) |
| **R-a.4** 63b→63c dependency | N/A at 63a (63b/63c contracts cite 63b symbols; adjudicated in the routing pin) |
| **R-a.5** tool-level vs verb-level adjudication (two granularities) | the relaxed `test_agent_capability_reach` (tool) + `test_governed_routing_63a` (verb) |
| **§2 migration** F1 legacy-under-OLD-DDL; member-invisible/admin-visible BEFORE; project-visible + idempotent AFTER; agent-first ORDER; boot WARNING count; option<> no-poison | `test_governed_migration_63a::*` (all 6 classes) |
| **§2.4 defaults** memory default = project keep; `scope=` `_grantable`-validated | `test_memory_retrofit_63a::test_a_remembered_note_defaults_to_the_project_keep_scope` + F4 hostile-scope (the `_grantable` predicate is the SAME the SET_SCOPE action uses — 61) |
| **§3 63↔64** routed-verb set DERIVED (tool population × dispatch) + RUNTIME-observed; grows-and-reds | `test_governed_routing_63a::*` (structural) + retrofit F3-isolation/owner-stamp (behavioural runtime obs) |
| **§4.1 store law** exact DDL via `_define_field`/`_plain_index`; two indexes; owner_agent bound; P1/P2/P6 EXPLAINs with C+ controls | `test_governed_schema_63a::*` (offline clause + live EXPLAIN + C+ controls) |
| **§4.3 two-step drain** served-set == stamped-set; await count = wake | 63b (out of 63a scope; the substrate does not preclude it — `message` has no owner/scope column yet, survey-confirmed) |
| **§5 #425** exactly ONE store round-trip; 62 security fixture re-run | `test_425_stamp_owner_63a::*` (round-trip count at `_query` seam; owner_principal_of deleted) + the 62 suite re-run (a builder/adversary gate) |
| **§6 §9 isolation** F3 ∀ read verbs + served-count==served-set; foreign-principal DENY (63b); Leg-2 CONSTRUCTED | F3 (`test_memory_retrofit_63a::TestF3*`) + F2 dirty-row single-brain; SF-63-1 foreign-principal is 63b |
| **§8 renders** governed list-read render names its bound (DERIVED); hostile fixture for stored text | DEFERRED to the build (the render is 63a-build; the F3 count-==-set pin is the Leg-1 seed). ⚠ flagged below |
| **§9 prose currency** BARE grep for retired premises at wave close | a wave-close-out step (the lead/cold-audit runs it — not a unit pin); flagged below |

**Two §9 riders NOT fully pinned at 63a, flagged per scope law (not silently dropped):**
- **§8 render-bound line** ("every governed list-read render carries ONE line naming the bound it
  applied, DERIVED from the Subject"): the memory retrofit's RENDER (what `lore_recall` prints) is a
  63a-BUILD surface; a contract pin needs the render to exist. I pinned the load-bearing Leg-1 seed
  (served-count == served-set), and FLAG the render-bound line as a builder deliverable the
  cold-audit/adversary must confirm carries the DERIVED bound (never hand-written prose). The hostile
  fixture for rendered stored text stays standing law.
- **§9 prose-currency grep** (bare grep for `owner_principal_of` / "free-form created_by" / "no governed
  tool routes"): a wave-CLOSE-OUT step, not a unit pin (it sweeps `loremaster/`, `docs/`, tool
  descriptions). Flagged for the lead/cold-audit at 63a close.

---

## §SATISFIABILITY — the shape of a correct build the adversary confirms the contract goes 0-failed against

The adversary must BUILD the reference implementation to grade the contract (C-DEF class). The
correct build: (1) `_governed_field_specs`/`_governed_index_statements` return the §4.1 specs, wired
into `_memory_statements` (+ `keep.key` into `_keep_statements`); (2) `resolve_subject`/`read_filter`/
`guarded_write` implemented per §1.2; (3) `LocalMemoryBackend.remember`/`recall` gain identity + route;
(4) `migrate_governed` + `KeepStore.get_or_create_keyed` + the CLI verb + the boot-count surface;
(5) #425 (one round-trip, owner_principal_of deleted); (6) `_GOVERNED_VERBS_ROUTED`/
`_GOVERNED_VERBS_PENDING_ROUTING` constants.

**RED-for-the-right-reason vs RED-on-a-correct-build (the C-DEF audit):**
- **All 52 RED go GREEN on that build** — EXCEPT where a fork's resolution changes the seam:
- ⚠ **The retrofit tool pins (FORK 5)** go GREEN only if the build's recall/remember accept the seam
  `_exercise_recall`/`_exercise_remember` call (`capability=`). A different kwarg → the isolated
  helper is a ONE-function edit (flagged). NOT a hidden C-DEF: the coupling is named + isolated.
- ⚠ **The identity-less-DENY pins** go GREEN only if the build DENIES (GovernedDenied) rather than
  TypeErrors on an identity-less call — the design's "teaching error" ruling. Named.
- ⚠ **The F2 NONE-scope observable + the single-brain-on-dirty-rows** depend on FORK 1's resolution
  (Resource representing scope=None). I pinned them OBSERVABLY (read_filter member-excludes / admin-
  includes m12; guarded_write member-DENY), never via `Resource(scope=None)` — so they go GREEN under
  EITHER reading of FORK 1. Not a C-DEF.
- ✅ **The 12 GREEN controls are GREEN on HEAD AND the correct build** (they discriminate wrong builds:
  a required governed column reddens the option<> survival pins; an owner_agent index reddens the C+
  control; an indexed-composite reddens the two-not-three; a count-over-the-whole-table reddens the
  served-count pin).
- **Satisfiability caveat the adversary must check:** the reference build must satisfy the contract
  AFTER the ruff cleanups it will demand (no orphaned imports) — the C-DEF harder leg.

---

## §DRY — new reusable symbols (brief-base §6)

**Production STUB symbols** (the builder implements GREEN; every one is dispositioned by the design's
own §8 reuse ledger — I only stub them RED, so the search was done by the designer and I cite it):

| new symbol | home | design §8 disposition (cited) |
|---|---|---|
| `governed.resolve_subject` | governed.py | HAND-ROLLED (the constructor 61 Fork D deferred) |
| `governed.read_filter` | governed.py | EXTENDED `authorize_filter` (a splice wrapper) |
| `governed.guarded_write` | governed.py | EXTENDED `AuditStore.append_fragment` + `execute_transaction` |
| `governed.GovernedDenied`/`GovernedConflict`/`GuardedWriteResult`/`LegacyMapping`/`MigrateGovernedResult` | governed.py | HAND-ROLLED (new substrate types) |
| `surreal_schema._governed_field_specs`/`_governed_index_statements` | surreal_schema.py | EXTENDED the `_*_statements` emitter idiom (audit-table precedent, survey-63a-store) |
| `KeepStore.get_or_create_keyed` | keeps.py | EXTENDED `create_keep` (same txn + CAS re-read, store-ref §5) |
| `principals.migrate_governed` | principals.py | HAND-ROLLED (the first row-backfill; `lore-adm` family) |

**Test-substrate symbols** (`_governed_contract.py` — design §1.2 item 6 MANDATES the shared substrate
so a governed table's contract is a parametrisation, never a copy; 64 reuses it for task/finding):
- `operators`/`scans_table`/`explain` — **MIRRORED** from `test_keeps_schema.TestTheKeeperIndexFires`
  (cited; the same stance the probe + 61b oracle took — a throwaway test helper, not production policy).
- `GovernedTableCase`, `member`/`admin`, `seed_memory_legacy`/`seed_memory_governed`, `read_filter_ids`/
  `authorize_filter_ids`/`python_allowed_ids`, `FakeRegistry`, `access_token`, `apply_ddl`,
  `governed_overlay_ddl`, `build_memory_backend`, `build_principal_and_keep_stores`,
  `field_statement`/`index_statement` — **HAND-ROLLED** shared test machinery (query run: `lore_search`
  for existing governed-test helpers returned only per-table copies in 60/61/62; the design's ONE-
  IMPLEMENTATION ruling is precisely to stop those becoming N clones).

---

## §COMMIT — for the lead (I did NOT commit; brief-base §2)

ONE concern. Message: `test(63a): governed substrate + memory retrofit contract (RED)`.
Trailers: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` + the `Claude-Session:` line.
Stage EXACTLY these 13 (NOT `docs/design/2026-08-28-packet63-retrofit-rulings.md` — not mine — nor
`resume/`):
- new: `REPORT-contract-63a.md`, `loremaster/loremaster/governed.py`,
  `loremaster/tests/_governed_contract.py`, `loremaster/tests/test_governed_schema_63a.py`,
  `loremaster/tests/test_governed_substrate_63a.py`, `loremaster/tests/test_425_stamp_owner_63a.py`,
  `loremaster/tests/test_memory_retrofit_63a.py`, `loremaster/tests/test_governed_migration_63a.py`,
  `loremaster/tests/test_governed_routing_63a.py`
- modified: `loremaster/loremaster/store/surreal_schema.py`, `loremaster/loremaster/keeps.py`,
  `loremaster/loremaster/principals.py`, `loremaster/tests/test_agent_capability_reach.py`

**Next in the pipeline: the contract-adversary** (design authority names it the grader). Point its
REACH ATTACK at §3.1's derived verb set (`test_governed_routing_63a`) and its QUANTIFIER ATTACK at
F3/F4's ∀-verbs. The 5 forks above are operator/lead rulings the adversary/builder need resolved.
