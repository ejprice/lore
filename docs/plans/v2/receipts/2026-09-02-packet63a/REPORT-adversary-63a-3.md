# REPORT-adversary-63a-3 — CONTRACT-ADVERSARY round-3 RE-GRADE of the packet-63a RED contract

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted AS NEEDED — `docs/reference/surrealdb-31-capabilities.md` §1.1 (FIELD
  OVERWRITE / INDEX IF NOT EXISTS), §1.4 (option<> on a populated table; no ASSERT/DEFAULT), §1.8
  (UNIQUE over option<> — many NONE coexist), §2 (record<> links; CONTENT; explicit projection reads
  NONE), §3 (execute_transaction / execute_read_transaction — statement[0]-only `.query()` trap; the
  BEGIN/COMMIT envelope carries None result entries), §5 (hot-row CAS mint). Cited, never re-transcribed.

## SUMMARY BLOCK

- **VERDICT: CONTRACT SUFFICIENT.** The two round-2 BLOCKERS are genuinely closed AND discriminate, the
  corpse B/C pins discriminate, and — the leg the re-grade required — the contract goes **0-failed /
  0-ERROR** on a provenance-asserted reference build I wrote to the §10 + §10.5 + §10.6 ruled shapes.
- **P1 headline — reference build result: 85 passed / 0 failed / 0 errors** across the 7 `test_*_63a.py`
  modules (round 2 was 76/80). The 11 formerly setup-erroring `retrofit_world` tests are GREEN; the
  BLOCKER-1 schema module went **23/24 → 24/24**; the BLOCKER-2 substrate module went **8/12 → 17/17**.
  No wrong build I could construct survives the contract.
- **BLOCKER 1 CLOSED + discriminates** (§B1): the de-anchored `_governed_contract.index_statement`
  matches `FIELDS scope` AND `FIELDS scope COMMENT '…'` (the mutation pin's appended clause) while
  still rejecting a composite `FIELDS scope, owner_principal` — proven by a standalone regex probe and
  by schema 24/24 on a correct `_plain_index` build.
- **BLOCKER 2 CLOSED + riders discriminate** (§B2): `guarded_write(store=StoreHandle)` reaches the
  store via the injected driver (`run_query` pre-read = acquire #1; `execute_read_transaction` mutation
  +audit = acquire #2), reads `row_count` back from the RETURN by SHAPE (envelope-safe). Rider (ii)
  ZERO-audit leg REDS a separate-round-trip build; R4 AST REDS a direct `connection.query()`; the
  no-handle FALSE-PASS is structurally closed (the frozen signature now REQUIRES a handle + row_count==1
  leg 1). Substrate 17/17.
- **Corpse B/C discriminate** (§CORPSE): corpse B (`test_stamp_owner_routes_through_the_shared_verify_
  capability_owner`) REDS a build re-routing stamp_owner through `verify_capability` (LEG B surfaced the
  boom); corpse C (`test_the_derived_write_path_set_matches_the_coverage_map`) is RED at HEAD (stub has
  no mutating literal) and GREEN once `get_or_create_keyed`'s CREATE/RELATE joins the derived set. Both
  corpse modules 83/83 on the correct build.
- **Satisfiability receipt:** `loremaster.__file__ = /tmp/adv63a3-ref/loremaster/loremaster/__init__.py`
  (provenance-asserted via `scratch_copy.sh`; I graded the ruled build, not the original — #140). 7
  modules **85/85**; corpse modules **83/83**; `uv run ruff check .` clean (after the one auto-fix the
  build demanded); `bash scripts/typecheck.sh` clean across all members incl. test trees. (§SAT)
- **HEAD RED honesty (P7):** I reproduced the contract's claimed HEAD count on the ORIGINAL tree —
  **58 failed / 16 passed / 11 errors = 85** — matching contract-63a-6 §COUNT exactly. The 11 errors are
  honest `retrofit_world` setup-errors (the `get_or_create_keyed` stub), not import/path bugs; that every
  red flipped GREEN on the correct build proves each was RED-until-built for the right reason.
- **P1b quantifier table** → §P1b (every invariant classified; every guarded row carries a receipt).
- **P1c reach table** → §P1c (11 guards; each DERIVED-vs-hand-list · coverage-checked · effect-vs-proxy ·
  one-source; legs marked empirical vs construction-inspection).
- **Packages considered:** none — no mechanism specified. This is a test-contract grade plus a reference
  build to ruled shapes; the design already adjudicated the migration verb `bespoke` and minted
  `StoreHandle` (§10.6). My reference build reused existing seams only (§Reuse).
- **Reuse ledger:** none new — I authored no shipped symbol; the scratch reference build lives only in
  `/tmp/adv63a3-ref` and is discarded. It reused `run_query`/`execute_read_transaction`/`compose`/
  `TxnFragment`, `authorize`/`authorize_filter`/`read_filter`/`_grantable`, `stamp_owner`,
  `resolve_visible_keeps`, `wrap_store_rejection`, `AuditStore.append_fragment`.
- **Graded: 2bf5769 · HEAD-at-report: 2bf5769 · SAME** (`git rev-parse HEAD` = 2bf5769; I committed
  nothing; the reference build is scratch-only).
- **Decisions-needed:** none. R1/R2 stay RED_ADJUDICATED→63b (design §10.5), confirmed honest at 63a;
  the AppContext capability-PRESENT path stays a documented honest bound (R7), unchanged from round 2.
- Receipt POINTERS: satisfiability → §SAT; BLOCKER 1 → §B1; BLOCKER 2 + riders → §B2; corpse → §CORPSE;
  quantifier → §P1b; reach → §P1c; fixture discrimination → §P2; deleted-code → §P6b; residuals → §RES;
  the wrong-build probe record → §PROBES.

---

## §SAT — the reference build + the 0-failed/0-error receipt (the leg the re-grade required)

I BUILT the ruled reference implementation in a provenance-asserted scratch copy and ran the REAL
contract against it. `./scripts/scratch_copy.sh /tmp/adv63a3-ref` →
`loremaster.__file__ = /tmp/adv63a3-ref/loremaster/loremaster/__init__.py` (imports resolve INSIDE the
copy — I graded the ruled build, never the original tree; #140).

**What I built, to the §10 + §10.5 + §10.6 ruled shapes** (production files touched, all in the scratch):
- `lorerunes/pdp.py` — §10.1 `Resource.scope: str | None`; `_is_valid_scope(None) → True`; `""` and every
  non-domain string still raise (a one-line widening; `to_surql`/`matches` unchanged).
- `agents.py` — §10.3 #425 additive close: `_verify_capability_owner(presented, token) -> (agent_id,
  owner_principal_id) | None` (the ONE verified SELECT now also projects `owner_principal`);
  `verify_capability` returns its `[0]`; `owner_principal_of` DELETED.
- `owner_stamp.py` — `stamp_owner` consumes the pair in ONE round-trip; no reference to the retired name
  (the corpse-B source pin caught my first docstring mention — fixed).
- `store/surreal_schema.py` — §4.1 `_governed_field_specs()` (3 option<> cols, no ASSERT/DEFAULT) +
  `_governed_index_statements()` (plain IF-NOT-EXISTS scope + owner_principal; owner_agent NOT indexed),
  WIRED into `_memory_statements`; SF-63-4 `keep.key option<string>` + `keep_key` UNIQUE index in
  `_keep_statements`.
- `keeps.py` — `get_or_create_keyed` (get_by_key → CREATE+RELATE with `key` set → CAS re-read on UNIQUE
  conflict) + `get_by_key`; the WHOLE verb wraps engine rejections as `KeepStoreError` (incl. its
  internal reads — corpse-C `test_each_write_path_wraps_engine_rejection` demanded it).
- `governed.py` — `resolve_subject` (stamp_owner → get_by_email → resolve_visible_keeps, fail-closed →
  `GovernedDenied`), `read_filter` (== `authorize_filter(READ).to_surql()`), `guarded_write`
  (StoreHandle; pre-read/authorize/guarded-mutation+audit as ONE `execute_read_transaction`; row_count
  from RETURN by SHAPE), `report_unmigrated_governed_rows` (StoreHandle; WARNING names the remedy).
- `memory/local.py` — `LocalMemoryBackend.handle` (its own `_ensure_connection`/`_drop_connection`/`_url`
  triple); `remember`/`recall`/`invalidate` take `subject=` (None → GovernedDenied), stamp owner + resolve
  scope on write, splice `read_filter` on read, route `invalidate` through `guarded_write(store=self.handle)`;
  `remember` scope is `_grantable`-validated or defaults to the project keep by `key='project:lore'`.
- `server.py` — `_GOVERNED_VERBS_ROUTED` (the 2 memory verbs) + `_GOVERNED_VERBS_PENDING_ROUTING`
  (DERIVED from the live dispatch tables — 30 pending w/ triggers); the ONE shared
  `_CAPABILITY_PARAM_DESCRIPTION` on `lore_recall`/`lore_remember`.
- `principals.py` — `migrate_governed(store: StoreHandle, …)` (memory scope backfill to the minted project
  keep; agent-first refusal for message; idempotent; dry_run) + the `migrate-governed` CLI subparser.

**The receipt** (`pytest -p no:cacheprovider`, TEST store `ws://127.0.0.1:18000`):

| module | reference build | round-2 | note |
|---|---|---|---|
| test_pdp_none_scope_63a.py | **4 / 4** | 4/4 | §10.1 Resource widening |
| test_425_stamp_owner_63a.py | **4 / 4** | 4/4 | #425 additive close, one round-trip |
| test_governed_routing_63a.py | **7 / 7** | 7/7 | 32 derived verbs; 2 routed, 30 pending |
| test_governed_schema_63a.py | **24 / 24** | **23/24** | **BLOCKER 1 CLOSED** |
| test_governed_substrate_63a.py | **17 / 17** | **8/12** | **BLOCKER 2 CLOSED** (+5 rider pins) |
| test_governed_migration_63a.py | **10 / 10** | 10/10 | backfill + idempotent + agent-first refuse |
| test_memory_retrofit_63a.py | **19 / 19** | 19/19 | PIN1–4 + §10.5 + identity-less deny |
| **TOTAL** | **85 / 85** | 76/80 | **0 failed / 0 error** |
| corpse: test_agent_capability_seams + test_keeps_store | **83 / 83** | (2 RED-until-built at HEAD) | corpse B + C GREEN on the correct build |

Gates on the reference build: `uv run ruff check .` → `All checks passed!` (after ONE `--fix` that isort-
reordered two in-function imports — the cleanup a builder would run); `bash scripts/typecheck.sh` → every
member OK incl. test trees. The receipt holds AFTER the ruff cleanups the build demanded.

**Honest bound (unchanged from round 2, R7):** the AppContext capability-PRESENT resolution (token +
principal/keep stores at the composition root) is NOT wired at 63a — `AppContext` holds neither store — so
a capability-bearing tool call reaches the backend with no subject and DENIES. The 63a-tested tool paths
(the identity-less DENY at both layers + the ONE shared `capability=` description) are wired and GREEN; the
present path lands with the 63b/64 composition-root wiring. Stated so this receipt does not over-claim.

---

## §B1 — BLOCKER 1 is CLOSED and discriminates

The round-2 defect: `index_statement`'s end-anchor (`…FIELDS scope$`) returned `None` when the mutation
pin appended ` COMMENT 'gov-index-probe'`, reddening `test_the_governed_indexes_route_through_the_shared_
emitter` on a CORRECT `_plain_index` build (schema 23/24). The fix (folded in `_governed_contract.py` at
HEAD) de-anchors to `FIELDS\s+{col}\b\s*(?:UNIQUE\b)?(?!\s*,)`.

**Discrimination proven by a standalone regex probe** (§PROBES P1):
- `FIELDS scope` → matches (True) — the plain index pin.
- `FIELDS scope COMMENT 'gov-index-probe'` → matches (True) — the mutation pin can now SEE its own marker.
- `FIELDS scope, owner_principal` → rejected (False) — the negative lookahead still vetoes a composite
  (the §4.1 single-column-index semantics).

On the correct build the schema module is **24/24** (round 2: 23/24). The two governed-emitter mutation
pins (FIELD + INDEX) both route through the ONE emitter and REDDEN a hand-rolled per-table copy (P1c).

## §B2 — BLOCKER 2 is CLOSED and every rider discriminates

`guarded_write(subject, action, *, table, row_id, set_fragment, audit, store: StoreHandle)` now reaches the
store through the injected owner driver: pre-read via `run_query(acquire=store.acquire, drop=, url=)`
(acquire #1) → build `Resource` → `authorize()` → guarded mutation carrying `authorize_filter(action)
.to_surql()` in its WHERE + a `RETURN`, composed with the audit fragment (when `requires_audit`) via
`compose(...) → execute_read_transaction(...)` (acquire #2) — ONE verified `BEGIN … COMMIT`. `row_count` is
read back from the mutation's RETURN by SHAPE (the engine's BEGIN/COMMIT envelope carries None entries;
`row_payloads = [r for r in results if isinstance(r, list)][0]` — the `tasks.py::_row_payloads` idiom;
0 → `GovernedConflict`).

**Substrate module 17/17** (round 2: 8/12). The five riders:
- **(i) vanished-conflict + positive control** — leg 1 asserts `row_count == 1` from the RETURN; the old
  no-handle FALSE-PASS (a no-store call raised `GovernedConflict` byte-identically) is now STRUCTURALLY
  closed: the frozen signature REQUIRES `store=handle`, and a build that could not reach the store fails
  leg 1 before leg 2 can false-pass. GREEN on the handle-routed build.
- **(ii) audit atomicity, BOTH legs** — leg A (admin bypass → +1) and leg B (rejected mutation → ZERO,
  before==after). **DISCRIMINATION PROVEN**: I mutated `guarded_write` to append the audit in a SEPARATE
  round-trip first — leg A still passed but leg B RED with `before=0 after=1` ("the audit did NOT ride the
  mutation's transaction"). This is the leg that catches a false safety claim leg A cannot see.
- **(iii) TOCTOU via the injected acquire** — `on_acquire(2)` lands a re-scope UPDATE between pre-read and
  guarded mutation; the WHERE excludes the moved row → `GovernedConflict`, row untouched. GREEN
  (deterministic, no 8-way race).
- **(iv) counting-acquire ≥1** — every guarded_write pin asserts `calls['acquire'] >= 1`; belt-and-braces
  with R4 (a build that bypasses the handle uses a raw connection, which R4 catches).
- **(v) DRY** — the reference build reuses `run_query`/`execute_read_transaction`/`compose`; no
  `run_governed_query(connection,…)` shim (the adversary's wrong-direction, raw-connection form).
- **R4 (governed.py issues no direct SDK call)** — the AST pin scans `governed.py` for SDK connection
  methods DERIVED from `_sdk_guard.SDK_CONNECTION_CLASSES`. **DISCRIMINATION PROVEN**: I added a direct
  `connection.query("SELECT 1")` to `governed.py` → the pin RED (`query() at governed.py:324`); the paired
  positive control (`test_the_sdk_call_site_scanner_is_not_blind`) stayed GREEN, so the clean verdict is
  cleanliness, not blindness. `migrate_governed` takes the SAME StoreHandle and routes through
  `run_query` (migration module 10/10).

## §CORPSE — the corpse B/C pins discriminate

- **Corpse B** (`test_stamp_owner_routes_through_the_shared_verify_capability_owner`, re-keyed for #425):
  GREEN on the correct build (stamp_owner reads once via `_verify_capability_owner`; patching
  `verify_capability` — LEG B — does not affect it). **DISCRIMINATION PROVEN**: I mutated `stamp_owner` to
  re-route through `verify_capability` (the #425 second-read regression the corpse warns of) → LEG B RED
  (`RuntimeError: stamp-owner-routes-through-shared-pair-path` surfaced). Exactly the wrong "fix" caught.
- **Corpse C** (`test_the_derived_write_path_set_matches_the_coverage_map`): RED at HEAD (the
  `get_or_create_keyed` stub carries no mutating literal → excluded from the DERIVED `_WRITE_PATHS` → the
  coverage map ⊋ derived). GREEN once the CREATE/RELATE lands it in the derived set and its 3 parametrized
  pins (coverage + rejection-wrap + transport-propagate) exercise it. The rejection-wrap pin additionally
  forced my `get_or_create_keyed` to wrap its internal `get_by_key` read (the injection hits the read
  first) — a real correctness constraint the pin enforces.
- **Corpse A** (the ~102 identity-less `test_memory_backend`/`test_memory_cutover` call sites) is the
  DOCUMENTED build-phase task (the adjudication is the spec — pass a subject, cold-audit no weakening). My
  reference build's backend deny makes those shipped tests red exactly as adversary-63a-2 §CORPSE-A
  predicted; NOT re-litigated as a 63a-contract blocker (per brief).

---

## §P1b — QUANTIFIER TABLE (every invariant: ∀-over-inputs vs guarded-by-known-failure-mode)

| invariant | classification | receipt (reference build) |
|---|---|---|
| guarded_write single-brain on writes (deny excludes → no mutate; 0-row → LOUD conflict) | **∀ over (subject, action, row-state)** | substrate own-row(+1)/foreign-row(deny+unchanged)/vanished(conflict)/rescope-TOCTOU(conflict) all GREEN; a bare-UPDATE invalidate wrong build REDS the retrofit foreign-deny pin (§PROBES P5) |
| audit atomicity (audit rides the SAME txn) | **∀ (landed → +1 / rejected → 0)** | rider (ii) both legs GREEN; the separate-round-trip wrong build REDS the ZERO leg (§PROBES P3) |
| F2 READ single-brain (`read_filter` == authorize ∀ subjects, real DDL incl. NONE-scope/owner dirty rows) | **∀ over inputs** | retrofit F2 pins + its GREEN control + pdp-none-scope 4/4 (member-invisible ∀ scope-dependent actions; admin AllRows incl. DELETE; `""` still raises) |
| F3 cross-principal isolation **∀ READ verbs** | **GUARDED (memory has 1 read verb, `read_verbs=("recall",)`)** | ACCEPTABLE at 63a: real recall isolation (bob→alice) + served-set < unfiltered_total both GREEN; store-level ∀ carried by F2. Thin, honest — not a blocker. |
| F4 anti-injection **∀ WRITE verbs** | **CLOSED at 63a** (remember: owner-stamp from subject + scope `_grantable`; invalidate: guarded_write) | owner-stamp F4 (hostile `owner_principal=` cannot move the stamp — TypeError, no such param); ungrantable-scope deny naming `lore-adm add-household`; invalidate foreign-deny. Both write verbs exercised. |
| verb-routing coverage (`derived == routed ∪ pending`, disjoint, non-blank triggers) | **∀-over-derived-verbs** (`partition_tools_by_population(live).governed` × dispatch tables) | routing 7/7; 32 derived (2 memory routed, 30 pending); the synthetic-VERB and synthetic-TOOL discriminators are GREEN (a grown set REDS) |
| #425 one round-trip | single `_query` counted | 425 4/4; the positive control `test_stamp_owner_still_returns_the_correct_owner_pair` is the leg the round-trip pin cannot pass by simply not reading the owner |
| migrate idempotent + agent-first ORDER | **∀ (memory backfill / message refuse)** | migration 10/10; second run backfills 0 (not refused); `--table message` before agent REFUSES naming the precondition |

No surviving wrong build walks a bad outcome through an unguarded door at 63a — every guarded row above
carries either a GREEN behavioural leg or a wrong-build that REDS it (§PROBES).

## §P1c — REACH TABLE (per guard: reach DERIVED vs hand-list · coverage a checked variable · effect vs proxy · one-source)

Legs: routing/AST/emitter/EXPLAIN/substrate run IN-tree → **EMPIRICAL** on the reference build; the
`@observes_routing` meta-pin proxy is **construction-inspection** (as at HEAD).

| guard | reach source | coverage a checked variable? | effect vs proxy | verdict |
|---|---|---|---|---|
| routing coverage pin `test_every_governed_verb_is_routed_or_adjudicated` | `partition_tools_by_population(live).governed` × dispatch tables (**DERIVED**) | YES — `derived == routed ∪ pending` REDS on growth; synthetic-verb + synthetic-tool discriminators GREEN; anti-vacuity pin (non-empty derived) GREEN | effect (live registry × live tables) | **SOUND at 63a.** R1 (`_dispatch_verbs` table-name hand-list) RED_ADJUDICATED→63b; 63a instance honest (all 32 verbs covered) |
| `@observes_routing` meta-pin (`routed ⊆ observed`) | AST scan of test tree for the marker (**DERIVED**) | YES — reds a routed-without-marker; anti-vacuity pin finds the memory markers | **PROXY** (scans the marker args, not the per-verb effect) | **SOUND at 63a** — the memory markers sit on GENUINE behavioural tests (F3 isolation, owner-stamp, invalidate deny) that PASS. R2 RED_ADJUDICATED→63b |
| tool-level fail-closed derivation | `_dispatch_verbs` defaults an unknown governed tool to `(tool, tool)` | YES — the synthetic-TOOL discriminator REDS a `()` derivation | effect | **SOUND** (a governed tool with no dispatch table → exactly 1 verb, never 0 — §10.4 rider) |
| R-a.2 ONE production `Subject(` constructor | AST scan of shipped `loremaster` pkg (**DERIVED**) | YES — `== 1`, must be in governed.py | effect (AST over shipped source) | **SOUND** — my build: exactly 1 site, `governed.resolve_subject` |
| R-a.3 ONE splice (`read_filter` == `authorize_filter(READ).to_surql()`) | byte-equality delegation pin | YES | effect | **SOUND** — substrate read_filter 3/3 (member/2-keeps/admin) |
| governed FIELD emitter mutation pin | monkeypatch `_governed_field_specs` → marker in emitted DDL | YES | effect + MUTATION | **SOUND** — routes through the ONE emitter; reds a hand-rolled per-table copy |
| governed **INDEX** emitter mutation pin (**BLOCKER 1**) | monkeypatch `_governed_index_statements` → marker | YES | effect + MUTATION | **SOUND — CLOSED.** The de-anchored `index_statement` now SEES the marker (schema 24/24); rejects a composite (regex probe) |
| EXPLAIN index pins (P1/P2/P6) | shipped walker + C+ TableScan controls in the SAME test | YES — C+ proves the walker sees a TableScan | effect | **SOUND** — live legs GREEN on the ruled DDL (scope/full-member IndexScan; keep.key IndexScan + NONE coexistence; owner_agent TableScan) |
| keeps write-path coverage-map pin (**corpse C**) | AST-derived `_WRITE_PATHS` == `_WRITE_PATH_INVOCATIONS` | YES — a new write path grows the derived set and reds the map | effect + fault-injection | **SOUND — CLOSED.** `get_or_create_keyed` (CREATE/RELATE) joins the derived set + the coverage map + its wrap/transport pins; RED at HEAD (stub, no mutating literal) |
| R4 SDK-escape AST pin | SDK methods **DERIVED** from `_sdk_guard.SDK_CONNECTION_CLASSES` | YES — the positive control flags a synthetic `query_raw` | effect (AST over governed.py) | **SOUND** — a direct `connection.query()` REDS it; positive control GREEN (§PROBES P4) |
| guarded_write counting-acquire (rider iv) | `store_handle` acquire counter | YES — every pin asserts `>= 1` | effect (runtime observation) | **SOUND** — belt-and-braces with R4; every guarded_write pin observes ≥1 acquire |

## §P2 — fixture perturbation / discrimination

The reference build IS the discrimination proof — each load-bearing fixture separated the correct build
from a plausible wrong one, empirically (§PROBES). Highlights:
- **BLOCKER 2 rider (ii) ZERO-audit** — the one fixture round-2 flagged as non-discriminating (the
  vanished-conflict FALSE-PASS) is now discriminating on TWO axes: the row_count==1 positive control (leg 1)
  and the rejected-mutation ZERO leg — the latter REDS a separate-round-trip build that passes leg A.
- **PIN4 `< unfiltered_total`** — alice's recall serves {alpha, beta} (2) < the seeded 3; bob's
  principal-private gamma is excluded at the SQL filter (ranking-robust). An unfiltered build serves 3 → RED.
- **F4 owner-stamp / scope** — the owner is server-derived from the resolved subject; a hostile
  `owner_principal=bob` arg is a TypeError (no such backend param); an ungrantable `scope=keep:<bob's>` DENIES
  via `_grantable` (mutation-provable against `lorerunes.pdp._grantable`, which my build calls via the module
  attribute so the patch lands).
- **DEV-2 vacuous-pass tighten** — `test_a_keep_resolution_failure_denies` narrowed to `pytest.raises(
  governed.GovernedDenied)` is RED-until-built at HEAD (the stub's `NotImplementedError` is no longer
  swallowed) and GREEN on the correct build (`resolve_subject` fails-closed on a `KeepStoreError`).

## §P6b — deleted-code enumeration (`AgentRegistry.owner_principal_of`, #425)

Independent enumeration from source BEFORE the §8 inventory: `owner_principal_of(agent_id)` returned the
owning principal's bare id (else None) — the SECOND `_query` #425 removes. Its virtue (agent→owner mapping)
is produced by the shared `_verify_capability_owner`'s ONE SELECT, which now also projects the owner id. On
the reference build: `owner_principal_of` DELETED (`test_owner_principal_of_no_longer_exists` GREEN);
`owner_stamp.py` NAMES it nowhere (the source pin caught my own docstring mention — fixed); one round-trip
pinned; the owner-pair correctness preserved (positive control GREEN). The deletion's orphaned virtues are
covered; no residual miss.

---

## §PROBES — the wrong-build probe record (each: mutation · pin · observed)

| # | wrong build (in scratch) | pin exercised | observed | verdict |
|---|---|---|---|---|
| P1 | (regex probe, no mutation) | `index_statement` de-anchored | `FIELDS scope`✓ · `FIELDS scope COMMENT '…'`✓ · `FIELDS scope, owner_principal`✗ | BLOCKER 1 discriminates |
| P2 | `_governed_index_statements` hand-rolled bypass would drop the marker | INDEX emitter mutation pin | (covered by construction; schema 24/24 GREEN on the emitter-routed build) | SOUND |
| P3 | `guarded_write` appends the audit in a SEPARATE round-trip first | `test_a_rejected_mutation_appends_no_audit_row` | **RED** `before=0 after=1`; leg A still GREEN | rider (ii) discriminates |
| P4 | add `connection.query("SELECT 1")` to `governed.py` | `test_governed_py_has_no_direct_sdk_call_site` | **RED** `query() at governed.py:324`; positive control GREEN | R4 discriminates |
| P5 | `invalidate` = a bare ungoverned `UPDATE` (bypass guarded_write) | `test_a_member_cannot_close_a_foreign_owned_row` | **RED** DID NOT RAISE GovernedDenied; owner positive control GREEN | invalidate-routing discriminates |
| P6 | `stamp_owner` re-routed through `verify_capability` | corpse B `…routes_through_the_shared_verify_capability_owner` | **RED** LEG B boom surfaced | corpse B discriminates |

Every mutation was applied in `/tmp/adv63a3-ref` and REVERTED; the final clean re-run of all 7 modules +
both corpse modules is **168 passed / 0 failed**. All probes ran against the TEST store
`ws://127.0.0.1:18000` (never :18500).

## §RES — residuals (every item an individual verdict — "the rest look fine" is banned)

| # | item | verdict |
|---|---|---|
| R1 | `_dispatch_verbs` `{lore_comms→_COMMS_ACTIONS…}` table-name hand-list (P1c) | **RED_ADJUDICATED → 63b** (design §10.5). 63a instance HONEST (all 32 verbs covered). Not re-litigated per brief. |
| R2 | `@observes_routing` observes a MARKER not the per-verb effect (P1c) | **RED_ADJUDICATED → 63b** (design §10.5). 63a markers sit on genuine passing behavioural tests. |
| R3 | F3 recall isolation is 1 read verb (memory has one) | **OK, mildly thin.** Real recall isolation + served-set-<-unfiltered pinned; store-level ∀ carried by F2. |
| R4 | `report_unmigrated_governed_rows` / `migrate_governed` take a StoreHandle; the R4 AST pin scans only `governed.py` | **OK.** governed.py is R4-clean and the AST pin discriminates; `principals.migrate_governed` routes through `run_query` (10/10) and is guarded on executed paths by the autouse `_sdk_guard` (contract-63a-6 §DEV1). A `principals.py` AST leg is a nice-to-have, not a 63a blocker. |
| R5 | `rebuild_embeddings`/`restore_from_ledger` reconstruct rows via direct `_upsert`/`_apply` (no governed columns) | **RESIDUAL (low).** A rebuild AFTER migration would re-strip scope/owner (the ledger carries neither) → rebuilt rows land NONE-scope (member-invisible until re-migrated). Out of the 63a retrofit's test surface; note for 63b/65 (unchanged from round 2). |
| R6 | AppContext capability-PRESENT resolution unexercised by 63a | **Honest bound (§SAT).** The identity-less tool DENY + the shared `capability=` description are the only 63a AppContext surfaces; the present path lands with the 63b/64 composition root. Unchanged from round 2 R7. |
| R7 | Corpse A (~102 identity-less shipped call sites) is a build-phase task | **DOCUMENTED build-phase (not a 63a-contract blocker).** The adjudication is the spec; the cold audit verifies no assertion is silently weakened. |

---

**VERDICT: CONTRACT SUFFICIENT.** Both round-2 blockers are genuinely closed AND discriminate; the corpse
B/C pins discriminate; the RED honesty holds at HEAD (58/16/11=85, reproduced); and the satisfiability
receipt shows the contract goes 0-failed / 0-error on a provenance-asserted reference build to the ruled
shapes, incl. after the ruff cleanups the build demands. This contract has been through two hardening
rounds and is ready for the build phase — I tried hard to break it and could not; the wrong builds I
constructed are each caught by a pin (§PROBES). Findings from prior rounds (#430 guarded_write, #431
index_statement, #432 corpse sweep) are RESOLVED by the folds this round grades.
