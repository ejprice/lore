# REPORT-adversary-63a — CONTRACT-ADVERSARY grade of the packet-63a RED contract

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted AS NEEDED — `docs/reference/surrealdb-31-capabilities.md` §1.8
  (UNIQUE over `option<>` = many NONE coexist; a `key IS NONE` row is not matched by `key = $k`),
  §2 (record<> link equality; `SELECT *` omits a NONE column). Cited, never re-transcribed.

## SUMMARY BLOCK

- Receipt: `brief-base v14 read` · `brief project v7 read`
- **VERDICT: CONTRACT INSUFFICIENT** — 4 concrete missing/defective pins named below; each a
  builder-invisible hole or a builder trap.
- **P1 headline — did a wrong build survive / does a correct build fail?** BOTH.
  (a) a build that leaves the memory **`invalidate`/supersede** write path un-governed survives the
  ENTIRE contract (no pin exercises it); (b) a build that trusts a caller's **`scope=`** without
  `_grantable` validation survives (no pin); (c) the ruled §2.2 default-scope build **CANNOT pass**
  `test_a_remembered_note_defaults_to_the_project_keep_scope` — a **C-DEF** (fixture mints the
  project keep via `create_keep`, which sets no `key`, so the ruled `get_by_key('project:lore')`
  resolution can never name it).
- **State:** done. RED baseline reproduced on the REAL tree at `6dd2600`: **60 failed / 16 passed**
  (matches the author's claim exactly), no collection errors, store-backed tests ran (spike-surreal
  `:18000` up). RED reasons spot-verified RIGHT (schema absent-column / `NotImplementedError` seams /
  `Resource(scope=None)` raises / tool-layer "DID NOT RAISE" / constants unbuilt).
- **Satisfiability receipt:** NOT a clean 0-failed — and that is a FINDING, not an omission: the
  C-DEF (MISSING PIN 1) makes a §2.2-compliant 0-failed build IMPOSSIBLE without a fixture fix. No
  full scratch reference build was run; the C-DEF is proven from source + the ruling + store law
  (see §SATISFIABILITY). `loremaster.__file__` provenance: N/A — I graded the REAL tree read-only
  and mutated nothing (no scratch copy needed; findings are absence-proofs + RED reproduction, not
  wrong-build mutations).
- **Packages considered:** none — the contract specifies no mechanism a package supplies (pure
  test-contract grade; the design already adjudicated the migration verb `bespoke`).
- **Graded: 6dd2600 · HEAD-at-report: 6dd2600 · SAME** (`git rev-parse HEAD` = `6dd2600`; nothing
  committed this session).
- Decisions-needed: the 4 missing pins (below) are contract fixes the author must make; MISSING PIN 1
  additionally needs the lead to confirm the fixture edit (a frozen-test change, not a builder edit).
- Receipt POINTERS: verdict drivers → §MISSING-PINS; quantifier table → §P1b; reach table → §P1c;
  the C-DEF → §SATISFIABILITY; deletion diff → §P6b; residuals → §RESIDUALS.

---

## §MISSING-PINS (the verdict drivers — each: the test that should exist + the defect it catches)

### MISSING PIN 1 — C-DEF: the default-project-keep-scope pin is UNSATISFIABLE by the §2.2-ruled build
- **Pin:** `test_memory_retrofit_63a.py::TestRememberStampsTheOwnerAndDefaultsToProjectScope::
  test_a_remembered_note_defaults_to_the_project_keep_scope` (asserts the note's scope ==
  `keep:{project_keep.id}`), against the `retrofit_world` fixture
  (`test_memory_retrofit_63a.py`, `retrofit_world`).
- **The defect:** `retrofit_world` mints its project keep with
  `keep_store.create_keep(keeper_email=alice, type="project", name="lore")`. `KeepStore.create_keep`
  (`keeps.py:444`, body `keeps.py:480-518`) writes ONLY `keeper` + `type` (+ optional `name`) — it
  **sets no `key`**. But design §2.2 RULES that the write path resolves the project keep by ONE
  indexed read `KeepStore.get_by_key('project:lore')` (and §2.2 explicitly REJECTS a `(type,name)`
  lookup and a bare-`project` value). Store law §1.8 / §2: a row with `key IS NONE` is not returned
  by `WHERE key = $k`. So on a §2.2-compliant build, `remember`'s default-scope resolution finds NO
  keyed keep → it either **mints a new keyed keep** (`get_or_create_keyed`, a DIFFERENT id) → scope
  `≠ keep:{project_keep.id}` → RED, or **refuses LOUD** (§2.2 "a LOUD refusal if absent") → the test
  errors → RED. Either horn fails a correct build. The ONLY build that PASSES resolves the project
  keep by `type='project'`/name — the exact §2.2-forbidden path — so the pin blesses a violation or
  traps a compliant builder (the C-DEF "a pre-existing pin the reshape structurally contradicts").
- **Smoking gun — the contract is internally inconsistent:** the migration module's own
  `test_governed_migration_63a.py::TestMigrateGovernedBackfillsAndIsIdempotent::
  test_the_verb_backfills_the_project_keep_scope` asserts the project keep is found via
  `SELECT id FROM keep WHERE key = 'project:lore'` (line 176) — i.e. the author KNOWS the project keep
  is key-addressed — yet the retrofit fixture mints it keyless.
- **The fix (mechanical):** `retrofit_world` must mint the project keep via
  `keep_store.get_or_create_keyed(key='project:lore', type='project', keeper_email=alice, name='lore')`
  (`keeps.py:520`, the SF-63-4 verb built for exactly this), so the §2.2 `get_by_key` resolution
  names the SAME keep. `get_or_create_keyed` is a builder-GREEN symbol, so the fixture can call it
  once the schema lands — the same pattern `test_the_verb_backfills_the_project_keep_scope` relies on.
  (Or: assert `row["scope"]` names the keep found by `get_by_key('project:lore')` instead of the raw
  `project_keep.id` — but the fixture must still carry the key, else there is no keyed keep to find.)

### MISSING PIN 2 — the `invalidate`/supersede write path (a NAMED 63a obligation) has ZERO coverage
- **Missing pin:** a member `invalidate`-ing (or `remember(supersedes=…)`-closing) a **foreign-owned**
  memory row must be DENIED — the close routes through `governed.guarded_write`, which authorizes the
  WRITE on the EXISTING (possibly foreign) row. Plus a positive control (an owner closing its own
  row succeeds).
- **The defect:** design §1.1 puts *"the backend's invalidate/supersede write path"* in 63a
  explicitly, and §2.5 rules *"`lore_remember(supersedes=…)` is a WRITE on the old row (close it) …
  both route through `guarded_write`/the stamp."* **No test in the 63a tree exercises `invalidate` or
  `supersedes`** (grep proof below). `GovernedTableCase.write_verbs=("remember","invalidate")` is set
  in `_memory_case()` (retrofit line 688, migration line 323) but is **dead decoration** — NO runner
  iterates `case.write_verbs` (grep proof below), so the design §3.2-F4 *"∀ write verbs, derived from
  the dispatch table"* quantifier is not realised. `guarded_write` (the read-authorize-mutate seam)
  therefore has **zero retrofit consumers exercised** — its ONLY 63a consumer is invalidate/supersede,
  which is untested — so the R-a.1 "substrate-with-a-real-consumer" claim is unmet FOR `guarded_write`.
- **Wrong build that survives:** `remember`-CREATE is owner-stamped (passes the stamp pin) but
  `invalidate(memory_id)` / the supersede-close issues a **bare** `UPDATE/DELETE` bypassing
  `guarded_write` — a member closes/erases ANOTHER principal's note by id. The whole contract stays
  green. This is the more dangerous verb (it mutates an EXISTING, possibly foreign-owned row), and it
  is the one with no pin.

### MISSING PIN 3 — the `scope=` `_grantable` write-time validation is unpinned (F4 hole)
- **Missing pin:** `remember(scope=<a keep the caller is NOT householded in>)` (and `scope=<a foreign
  private scope>`) must DENY via `lorerunes.pdp._grantable` with a teaching error naming
  `lore-adm add-household` — plus the MUTATION leg (change `_grantable` → this write-time validation
  moves, the ROUTING-IS-NOT-SHARING proof design §9-rider-3 demands).
- **The defect:** design §2.4 rules an explicit `scope=` is *"a PDP-VALIDATED REQUEST … checked by
  the SAME `_grantable` predicate the SET_SCOPE action uses"*, and §9-rider-3 requires the mutation
  proof. The contract's ONLY F4 test, `test_a_hostile_owner_argument_does_not_move_the_stamp`
  (retrofit line 575), fuzzes **only `owner_principal=`** and swallows a `TypeError` as a pass. **No
  test passes an un-grantable `scope=`** (grep proof below: zero `_grantable`/household-DENY/hostile-
  scope hits). The author's own §9-RIDER-MAP claims *"F4 hostile-scope (the `_grantable` predicate…)"*
  — the claim is a dropped rider: the pin does not exist.
- **Wrong build that survives:** `remember` writes the row with the caller's `scope=` verbatim, never
  calling `_grantable`. A member files a note into a keep it is not householded in (unauthorized scope
  assignment / cross-keep injection). Green suite.

### MISSING PIN 4 — the F3 served-count==served-set pin is a near-tautology (trust Leg 1 UNguarded)
- **Pin (defective):** `test_memory_retrofit_63a.py::TestF3ServedCountEqualsServedSet::
  test_read_filter_count_equals_read_filter_set_size` (retrofit lines 317-333).
- **The defect:** it builds ONE `fragment` from `governed.read_filter(subject, MEMORY_TABLE)` and uses
  the SAME fragment for both the `SELECT count() … WHERE {fragment} GROUP ALL` and the
  `SELECT id … WHERE {fragment}` — so `count == size` holds **trivially** on any build where
  `read_filter` is deterministic. Its docstring PROMISES it *"REDDENS a build that counts over the
  whole table (`SELECT count() FROM memory`) beside a filtered id listing"* — but the assertion can
  never red that build, because the pin **never exercises the `recall` render** where the false clear
  would live (the "failure message promises a check the assertion does not perform" pattern,
  CLAUDE.md). The real trust-Leg-1 property — the actual `recall`/render's reported count equals its
  served set — is **unpinned** (the §8 render-bound-line was explicitly deferred by the author).
- **Missing pin:** exercise the real `recall` (or its render) over the hostile ≥2-principal fixture
  and assert the count it REPORTS equals its served-set size, with a wrong-build control that reports
  the unfiltered total.

---

## §P1b — QUANTIFIER TABLE (every invariant: ∀-over-inputs vs guarded-by-known-failure-mode)

| invariant | classification | receipt |
|---|---|---|
| F2 READ single-brain (`read_filter` == `authorize` ∀ subjects, real memory DDL incl. dirty rows) | **∀-over-inputs** (5 subjects × hostile rows m1–m11; NONE-owner m10/m11 forced) | SOUND. `test_read_filter_equals_authorize_over_the_real_table` + its GREEN control (`authorize_filter`==`authorize`) isolate a divergent `read_filter` from a wrong PDP. |
| F2 NONE-scope member-invisible / admin-visible (m12) | ∀ members + admin | SOUND, and FORK-1-agnostic (store-side; no `Resource(scope=None)`). |
| F2 DELETE single-brain on dirty rows (m12/m13 owner + non-owner) | ∀ owner/non-owner forced | SOUND — m13 (owner deletes own NONE-scope) positive, m12 (unowned) negative, non-owner empty. Discriminates the `None→deny-everything` build. |
| FORK-1 Resource NONE-scope invisible/admin-visible + `""` still raises | ∀ 3 members + admin, empty-string control | SOUND. |
| F3 cross-principal isolation **∀ READ verbs** | **GUARDED** — a single `recall` test, ONE direction (bob→alice); `read_verbs=("recall",)` is never iterated | store-level ∀ is carried by F2 `read_filter`; the TOOL-level recall test is a 1-verb / 1-direction smoke. Acceptable at 63a (memory has one read verb) — flagged as thin, not a blocker. |
| F4 anti-injection **∀ WRITE verbs** | **GUARDED / BROKEN** — only `remember`, only `owner_principal=` | **MISSING PIN 2** (`invalidate` unfuzzed) + **MISSING PIN 3** (`scope=` `_grantable` unpinned). Wrong builds survive both doors. |
| verb-routing coverage (`derived == routed ∪ pending`) | **∀-over-derived-verbs**, DERIVED from `partition_tools_by_population` × dispatch tables | SOUND at 63a (all 6 governed tools covered); reach caveat in §P1c. |
| #425 one round-trip | single call counted at `_query` | SOUND — `test_stamp_owner_still_returns_the_correct_owner_pair` is the positive control that the closure cannot pass by simply not reading the owner. |

## §P1c — REACH TABLE (per guard: reach DERIVED vs hand-list · coverage a checked variable · effect vs proxy · one-source-by-mutation). Legs: routing/emitter/AST pins run IN-tree (empirical); the meta-pin proxy is construction-inspection.

| guard | reach source | coverage a checked variable? | effect vs proxy | verdict |
|---|---|---|---|---|
| `test_every_governed_verb_is_routed_or_adjudicated` | `governed` = `partition_tools_by_population(live)` (DERIVED) × `_dispatch_verbs` | YES — `derived == routed ∪ pending` reds when a `_COMMS/_TASK/_FINDING_ACTIONS` grows | effect (live tables) | **MISS #5 (residual):** `_dispatch_verbs`'s `{lore_comms→_COMMS_ACTIONS, lore_tasks→_TASK_ACTIONS, lore_findings→_FINDING_ACTIONS}` map (routing lines 53-57) is a HIDDEN HAND-LIST. A NEW multi-verb governed tool with its own `_X_ACTIONS` falls to the fallback `(tool,)` (lines 58-62) → its individual verbs never join the derived set. §10.4 blesses the fallback as "fail-closed", so the tool is detected at TOOL granularity — but its verbs are silently under-covered. Latent (no such tool at 63a); recommend deriving the dispatch-table attribute or pinning the map's completeness, with a re-open trigger. |
| `@observes_routing` meta-pin (`TestEveryRoutedVerbHasABehaviouralObservation`) | AST scan of `test_*.py` for the marker (DERIVED, xdist-safe) | YES — `routed ⊆ observed` reds a routed-without-marker | **PROXY** — the scan collects the marker's `(tool,verb)` args but never verifies the DECORATED test actually observes THAT verb's routing | **MISS #6 (residual):** sound at 63a (memory markers sit on genuine, frozen behavioural tests); the proxy gap opens for future waves (a marker on any test satisfies it). Re-open trigger: 63b/63c/64 adding routed verbs. |
| R-a.2 ONE `Subject` constructor | AST scan of the shipped `loremaster` pkg (DERIVED) | YES — `== 1`, reds on a 2nd constructor | effect (AST over shipped source) | SOUND — verified RED at HEAD (zero constructors → stub). |
| R-a.3 ONE splice | byte-equality `read_filter` == `authorize_filter(READ).to_surql()` | YES | effect | SOUND — a private-copy `read_filter` diverges → RED. |
| governed DDL emitter (schema mutation pins) | monkeypatch `_governed_field_specs`/`_governed_index_statements` → marker must appear in emitted DDL | YES | effect + MUTATION (perturb emitter → memory DDL moves) | SOUND — proves memory routes through the ONE emitter, not a hand-written copy. |
| EXPLAIN index pins (P1/P2/P6) | the shipped walker + C+ TableScan controls in the SAME test | YES — C+ proves the walker CAN see a TableScan | effect | SOUND — a pin that cannot see a TableScan is not a pin; the controls are present. |

---

## §SATISFIABILITY — no clean 0-failed receipt, and why (the C-DEF)

The role/brief require the satisfiability receipt for a SUFFICIENT verdict. It **cannot exist** for
this contract as written: MISSING PIN 1 proves a §2.2-compliant reference build fails
`test_a_remembered_note_defaults_to_the_project_keep_scope`. A "0-failed" build would have to resolve
the project keep by `type`/`name` — the exact path §2.2 rejects — i.e. a 0-failed run would certify a
ruling VIOLATION. So the honest satisfiability answer is: **INSUFFICIENT — the contract is not
satisfiable by the ruled build until the `retrofit_world` fixture mints its project keep by
`key='project:lore'`.**

- **Provenance/discipline honesty:** I did NOT stand up a full scratch reference build
  (`scratch_copy.sh` / `loremaster.__file__`), and I mutated nothing in the real tree. My findings are
  **absence proofs** (no pin references `invalidate`/`supersedes`/`scope=`-validation — greps below)
  and a **source-derived C-DEF** (`create_keep` sets no `key` `keeps.py:480-518` · §2.2 rules
  `get_by_key` · store law §1.8 forbids `key=$k` matching a NONE-key row · the contract's own
  migration pin proves the project keep is key-addressed). None of these require a wrong-build
  mutation, so no scratch copy was warranted. The one leg I did NOT run empirically is a full
  reference build proving the OTHER 56 REDs go green — stated as an honest bound: I verified the RED
  baseline (below) and each finding's mechanism, not the green side of the un-blocked pins.

---

## §PROBE RECORD (commands + real output)

### P7 — RED honesty (reproduced on the REAL tree @ `6dd2600`)
```
$ uv run pytest -n auto -q <the 8 63a modules>
60 failed, 16 passed in 10.61s          # matches the author's 60R/16G claim EXACTLY; no collection errors
```
Spot-checked RED reasons (RIGHT, not import/path/fixture errors):
- schema: `generate_memory_ddl emits no DEFINE FIELD for memory.scope` (governed columns absent).
- substrate: `resolve_subject`/`read_filter`/`guarded_write` → `NotImplementedError` (stub).
- FORK-1: `Resource(scope=None)` → `_is_valid_scope(None)` raises (widening unbuilt).
- routing: `_GOVERNED_VERBS_PENDING_ROUTING … is unbuilt` (constants absent).
- tool-layer deny: `Failed: DID NOT RAISE <GovernedDenied>` — the real `AppContext` BOOTS and the
  handler answers identity-less (a genuine behavioural RED, not a boot error — D1 in the author's
  report is honest).
- #425: `AgentRegistry.owner_principal_of still exists` (RED at HEAD).

### absence proofs (the missing pins)
```
$ grep -rnE "invalidate|supersed" <8 63a modules>
# only docstring mentions + the DEAD write_verbs=("remember","invalidate") tuple; NO exercise.
$ grep -rnE "for .* in .*(read_verbs|write_verbs)" loremaster/tests/
# (empty) — the GovernedTableCase verb lists are never iterated: the ∀-verb quantifier is decoration.
$ grep -rnE "_grantable|not householded|add-household|scope=.*keep:" \
      test_memory_retrofit_63a.py test_governed_substrate_63a.py | grep -iE "scope|grant|household"
# (empty) — no scope= _grantable validation pin exists.
```

### §P6b — independent deleted-code enumeration (`AgentRegistry.owner_principal_of`)
Enumerated from source `agents.py:954-` BEFORE re-reading the design §8 inventory:
- **Behavior:** given a bare `agent_id`, returns the owning principal's bare record id, else `None`
  (fail-closed for ownerless/unknown). It is the SECOND `_query` round-trip #425 removes.
- **Its virtue (agent→owner-principal mapping) is already produced elsewhere:** `verify_capability`
  (`agents.py:869`) *"returns all of them via the `owner_principal` link dereference — the binding
  check is FREE"* — it ALREADY projects `owner_principal`. So the deletion loses no capability; the
  #425 closure exposes what the verified SELECT already reads.
- **Diff vs the design §8 inventory (item 5) + §5:** MATCH — deleted, virtue absorbed, adjudicated
  DROPPED with the positive control `test_stamp_owner_still_returns_the_correct_owner_pair` preserving
  the owner-pair correctness, and the `_query`-count pin preserving the one-read property. **No
  orphaned virtue** (`lore_impact` @ `8128c50`: `stamp_owner` is the sole prod consumer; re-confirm at
  build). The #425 pins are adequate.

### corpse sweep (P6) — tests still pinning the retired world
- `verify_capability -> str | None` (post-#425 additive shape, §10.3): the `FakeRegistry`
  (`_governed_contract.py:383-417`) mirrors the ruled pair-path (`_verify_capability_owner` +
  delegating `verify_capability`) — the LITERAL tuple-return §10.3 rejects is NOT present. Corpse-free.
- `owner_principal_of`: the #425 module asserts its ABSENCE (not its presence) — no corpse.
- Resource domain pin `test_pdp_core.py::test_resource_rejects_a_scope_outside_the_domain` is
  parametrised over `"" "Server"` etc. but NOT `None` (§10.1 confirmed): it stays green after the
  widening — a compatible pin, not a corpse.

---

## §RESIDUALS (every item an individual verdict — "the rest look fine" is banned)

| # | item | verdict |
|---|---|---|
| R1 | `_dispatch_verbs` `table_name` hand-list (P1c MISS #5) | **RESIDUAL / harden.** Fires at tool granularity for a new tool (not silent) but under-counts a new multi-verb tool's verbs. Recommend a derived dispatch-table lookup or a completeness pin + re-open trigger. Not a 63a blocker (6/6 tools covered). |
| R2 | `@observes_routing` meta-pin observes a MARKER, not the effect-for-that-verb (P1c MISS #6) | **RESIDUAL.** Sound at 63a (frozen genuine tests); proxy gap for 63b/63c/64. Recommend the meta-pin (or a review step) confirm the decorated test names that tool/verb in its body. |
| R3 | `guarded_write` DELETE / SET_SCOPE branches unexercised (only WRITE tested; substrate lines 233-315) | **RESIDUAL (latent, 64).** `set_fragment=None` DELETE path has no pin; 64 is its first real consumer. Note the branch-reachability gap; not a 63a blocker (63 builds no re-scope/DELETE consumer, §2.5). |
| R4 | F3 recall isolation is 1-direction (bob→alice), depends on `FakeEmbedder` returning matching vectors for identical text | **OK, mildly thin.** `FakeEmbedder` is deterministic-by-text (`loresigil/testing.py:90`), so an unfiltered recall WOULD surface the note — the test is not vacuous. Store-level ∀ isolation is carried by F2. A reverse-direction (alice-can't-see-bob) leg would strengthen it. |
| R5 | `test_a_hostile_owner_argument_does_not_move_the_stamp` swallows `TypeError` as a pass | **OK (accepted).** A tool that exposes no `owner_principal=` param is the strongest anti-injection — the except is legitimate. (The GAP is `scope=`, MISSING PIN 3, not this.) |
| R6 | R-a.2 AST scan counts `*.Subject` attribute calls too | **OK.** Correct — an `x.Subject(...)` construction is a construction; the allowlist-the-one-site invariant holds. |
| R7 | `_governed_field_specs`/`_governed_index_statements` are stubs NOT yet called by `generate_memory_ddl` | **OK / RED-honest.** Confirmed unwired (`surreal_schema.py`: only the two defs, no call sites) → schema pins RED at HEAD for the right reason; the mutation pins drive the builder to wire them. |
| R8 | #425 round-trip pin assumes the verified SELECT can project the owner-principal *id* in one read | **OK.** `verify_capability` already dereferences the `owner_principal` link (`agents.py:869` docstring); §10.3's `_verify_capability_owner -> (agent_id, owner_principal_id)` is satisfiable in one SELECT. |

---

## §HANDOFF — the contract fix is mechanical (for contract-63a / lead-63)

1. **MISSING PIN 1 (C-DEF, blocks a valid build):** in `retrofit_world`, replace the `create_keep`
   project-keep mint with `keep_store.get_or_create_keyed(key='project:lore', type='project',
   keeper_email=alice, name='lore')` so the §2.2 `get_by_key` default-scope resolution names it.
   (Lead: this is a FROZEN-test edit — the builder cannot make it.)
2. **MISSING PIN 2:** add a `guarded_write`-routing pin for `invalidate`/`remember(supersedes=…)` — a
   member closing a FOREIGN-owned row DENIES; owner-closes-own succeeds (positive control); add an
   `@observes_routing("lore_remember","lore_remember")`/backend-invalidate observation so the write
   verb's routing is a checked variable.
3. **MISSING PIN 3:** add an F4 `scope=` pin — `remember(scope=<a keep alice is not householded in>)`
   → `GovernedDenied` via `_grantable`, plus the mutation leg (perturb `_grantable` → this validation
   moves).
4. **MISSING PIN 4:** replace the tautological served-count pin with one over the real `recall`
   render's REPORTED count vs its served set, with an unfiltered-count wrong-build control.

Residuals R1/R2 (reach hardening) and R3 (guarded_write DELETE branch) are recommend-and-trigger, not
blockers. **VERDICT: CONTRACT INSUFFICIENT.**
