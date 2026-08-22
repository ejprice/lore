# REPORT-contract-60-w1 — packet 60 wave 1 CONTRACT (the Keep substrate)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done-with-deviations
- **Capability check:** full — lore tools loaded (keyword form), spike + prod stores up, index not needed (source-map work). All demands satisfiable.
- **Deviations (one line each):**
  - **typecheck is GREEN, not RED** as the brief predicted — I wrote COMPLETE signature stubs (constants + assemblers returning `[]`/`""` + a full `KeepStore` skeleton), so mypy has nothing unbuilt to flag. No owned pending-contract typecheck bound is needed. (The better outcome.)
  - **2 stale references to the renamed exact-set pin remain in `test_blocks_edge.py`** (outside my writable set) — FLAGGED with exact edits in §Deviations below, NOT edited (scope law).
  - **1 build-dependency** baked into an atomicity pin (create_keep must resolve keeper email through the composed `PrincipalStore.get_by_email`) — declared in the pin + §Decisions.
- **Packages considered:** none — no new mechanism specified. The `KeepStore` reuses the shared `_txn` seams (`run_query`/`execute_transaction`/`bootstrap_session`/`retry_on_conflict`) and the installed `surrealdb` SDK; no new dependency. `str(ULID())` id-mint (builder's) reuses the already-installed `ulid` (the `message` table precedent) — not introduced here.
- **Reuse ledger:** see §DRY ledger — 8 new reusable symbols, all dispositioned (REUSED the shared emitters/seams; the store LIFECYCLE clones the house per-store idiom, POLICY stays shared).
- **Graded:** N/A — this is a contract (RED tests + stubs), not a verdict on someone's artifact. All work at `f0ebbf4` (HEAD-at-report `f0ebbf4`, SAME).
- **Fallbacks to grep (SAID OUT LOUD):** grepped for the retired pin-name references and module-level constants/fold lines (non-symbol textual seams + rename-exhaustiveness — the graph can't own these). Everything structural came from `lore_*` + direct reads. No lore friction to file.
- **Decisions needed:** 1 (the create_keep resolution seam the atomicity pin monkeypatches — §Decisions). Nothing blocking.
- **Pointers:** §What-I-built · §Gate receipts · §Load-bearing pins + fixtures-discriminate self-audit · §Satisfiability plan · §Deviations · §Decisions · §DRY ledger.

---

## §What I built

**Writable-set edits (all at `f0ebbf4`):**

| file | change |
|---|---|
| `loremaster/loremaster/store/surreal_schema.py` (M) | RED-STUB keep slice: constants `KEEP_TABLE`/`MEMBER_OF_RELATION`, domain tuples `_KEEP_TYPES=('project','team','session','dm')` / `_KEEP_RANKS=('contributor',)` + `_KEEP_RANK_CONTRIBUTOR`, field specs `_KEEP_FIELD_SPECS`/`_MEMBER_OF_FIELD_SPECS`, assemblers `_keep_statements()`→`[]` / `_member_of_statements()`→`[]`, `generate_keep_ddl()`→`""`, and the fold line in `generate_ddl` (keep + member_of, AFTER `_principal_key_statements()`). Emits NOTHING today so every pin fails behaviourally. |
| `loremaster/loremaster/keeps.py` (NEW) | `KeepStore` — REAL lifecycle (connect / `ensure_ready` applying `generate_keep_ddl` via `execute_transaction` / `close` / `_query` via `run_query` / composed `PrincipalStore` / `_resolve_principal_id` / `_to_aware_utc` delegating to `PrincipalStore`) + REAL frozen models `Keep`/`Membership` + typed errors `KeepStoreError`/`KeepNotFoundError`/`KeeperLockoutError`. All 7 CRUD verbs raise `NotImplementedError`. |
| `loremaster/tests/_enforced_relations_scaffold.py` (M) | registered `member_of: (principal, keep)` in `KNOWN_RELATION_EDGES` and `generate_keep_ddl` in `ALL_DDL_GENERATORS` (the ∀ sweep + exact-set pin now cover it). |
| `loremaster/tests/test_enforced_relations.py` (M) | bumped the exact-set pin name/count five→**six** (`test_the_relation_edge_set_is_EXACTLY_the_six_known_edges`) + a note on the `member_of` addition. |
| `loremaster/tests/test_keeps_schema.py` (NEW) | the schema contract — offline DDL clauses, call-time-derived domains (mutation pins), the member_of declaration/both-paths/guarded-from-birth pins, live round-trip, the keeper-index EXPLAIN pin, the member_of ENFORCED-flip dirty-store migration, the rank-widening dirty-store migration. |
| `loremaster/tests/test_keeps_store.py` (NEW) | the `KeepStore` CRUD contract — create_keep shape + the Fork-D atomic keeper auto-add + atomicity, get_keep, add_household (idempotent), remove_household (keeper-lockout), set_rank (trivial), list_household / list_keeps_for_keeper (discriminating), the shared-seam structural pins, the value-object/error pins. |

**Store-law citations (cited, never re-transcribed):** `docs/reference/surrealdb-31-capabilities.md` §1.1 (FIELD `OVERWRITE`; TABLE/INDEX `IF NOT EXISTS`; RELATION-table `OVERWRITE`; `ALTER` trap §1.3), §1.4 (the rank-widening hazard — the only §1.4-relevant leg, and it is FUTURE), §1.6 (virgin-DB blind spot → the dirty-store migrations), §1.8 (`name` `option<>` — multiple NONE coexist), §2 (CONTENT / `type::record` / missing-projection-reads-NONE), §3 (`execute_transaction`, not lax `query()`), §4 (`ENFORCED` validates both endpoints + `INSERT RELATION`; UNIQUE(in,out) legal; a traversal never indexes → keeper is a FIELD, index PROVEN to fire).

**Design authority:** every schema decision traces to `docs/design/2026-08-22-packet60-keep-substrate-rulings.md` Forks A–F + the Emission plan + the store-law checklist. No design ambiguity required escalation to the sidecar.

---

## §Gate receipts (all at `f0ebbf4`)

- **`ruff check` (6 touched files):** `All checks passed!`
- **`scripts/typecheck.sh`:** GREEN — `loremaster OK` (221 src files incl. keeps.py + tests), lorerunes/lorescribe/loresigil/skills/scripts all OK, shellcheck OK. **No mypy errors (deviation from the RED prediction — the stubs are signature-complete).**
- **`pytest -n auto` on the two new files:** **65 failed / 19 passed** (RED-by-design). Failures verified behavioural — sampled reasons: `NotImplementedError` (create_keep/get_keep stub), `generate_keep_ddl no longer emits 'member_of'` (`old_world_ddl`, migration pins), `The table 'keep' does not exist` / `created_at did not self-stamp` / `rank None != contributor` (empty DDL → no schema defaults). None fail on an ImportError, a collection error, or a fixture bug.
- **`pytest test_enforced_relations.py`:** **3 failed / 65 passed** — the 3 fails are EXACTLY the declared "turns RED in files it does not own" set: `test_the_relation_edge_set_is_EXACTLY_the_six_known_edges`, `test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS[member_of]`, `test_the_edge_declares_its_IN_and_OUT_endpoint_tables[member_of-endpoints3]`. All existing edges (briefed/to/blocks/refers/answers_to) + the ∀ ENFORCED pin stay GREEN.
- **No regressions elsewhere:** `test_blocks_edge.py` declaration/birth/both-paths classes → 13 passed; `test_derivation_source_unification.py` → 7 passed / 19 expected-skips (the packet-43-deferred refers/answers_to legs). The `generate_ddl` fold adds nothing at stub (`_keep_statements`/`_member_of_statements` → `[]`), so no existing generate_ddl consumer changed.

---

## §Load-bearing pins + fixtures-discriminate self-audit ("what WRONG build still passes this?")

1. **DDL clauses** — `TestTheKeepDdlDecisionRuleIsEnforcedMechanically`. IF-NOT-EXISTS-field build → RED (`test_every_field..._OVERWRITE`); no-fields build → the `test_the_generator_emits_keep_fields...` control REDS the vacuity; un-enforced/IF-NOT-EXISTS member_of → RED (`test_the_member_of_relation_table_is_OVERWRITE_and_ENFORCED`) AND the live ENFORCED-flip migration probes BEHAVIOUR, not string. Two mutation pins prove the slice ROUTES THROUGH `_define_field` / `_define_relation_table` (a hand-written string build → RED).
2. **Call-time domains** — a frozen-literal ASSERT build passes a naive membership check but REDS the monkeypatch mutation pins (`test_changing_the_KEEP_TYPES/RANKS_tuple_changes_the_emitted_ASSERT`).
3. **type NO default / rank DEFAULT / name option<>** — a build defaulting `type` REDS `test_type_has_NO_default`; a plain-string (non-option) or no-ASSERT `name` REDS `test_empty_string_name_rejected_while_none_is_accepted`, and `test_multiple_keeps_with_no_name_coexist` proves the NONE case; `test_the_ruled_type_domain_is_EXACTLY_the_closed_set` (∀, QUANTIFIER) REDS a WIDENED domain that the derivation+membership pins wave through.
4. **member_of ENFORCED + UNIQUE(in,out)** — the dirty-store ENFORCED-flip (BASELINE accepts / guard-LIVE refuses / positive-control real endpoint still accepted / pre-existing dangling SURVIVES / idempotent) catches "emits perfectly, never LANDS" (#107 shape). UNIQUE(in,out) live pin has a positive control (a DIFFERENT pair is accepted), so it is not "the store only ever writes one edge".
5. **rank widening-safe** — a narrowing build REDS the survive/writable legs; a build that "migrated" by DROPPING the ASSERT REDS the positive control (`_WIDER_not_GONE` — garbage rank still rejected).
6. **create_keep atomicity** — `test_create_keep_AUTO_ADDS_the_keeper_to_the_household_at_contributor` asserts BOTH the keeper FIELD == creator AND the keeper IS in the household at contributor, in ONE test → a "writes field, forgets edge" build (keeper lockout) REDS. The two atomicity pins (rejected-create + ghost-keeper-edge) catch a two-`_query` non-atomic build (an orphan keep leaks → count > before → RED); both now carry `assert not isinstance(caught.value, NotImplementedError)` so they are honestly RED-at-stub.
7. **keeper index fires** — EXPLAIN pin with a POSITIVE CONTROL (an unindexed `type =` predicate IS a `keep` TableScan, so the inspection is not vacuous) + the invariant (`keeper = $p` is an IndexScan, NOT a TableScan). A no-keeper-index build REDS; the field escapes store §4's traversal-never-indexes trap the FIELD LINK was chosen to avoid.
8. **add idempotent / remove refuses keeper / set_rank** — re-add writes exactly ONE edge (a second-edge or UNIQUE-ERR-escaping build REDS), with a 2-different-members positive control; remove refuses the keeper (`KeeperLockoutError`) with a non-keeper-removal positive control; set_rank exercised trivially (only `contributor` legal today — NOT gated on multi-rank, per Fork F rider).
9. **Shared-seam reuse** — `_query` is named EXACTLY `_query` (so `test_retry_seam.py`'s scan auto-discovers it and its shared-retry mutation pins bind KeepStore); the store COMPOSES a `PrincipalStore`. The retry/backoff/classification MUTATION proof lives in `test_retry_seam.py` (auto-scan), not re-cloned here.

**No over-reach into packet 63 (Fork E, checked):** no DM auto-creation-on-send pin, no 2-member cap on `dm` keeps, no `lore_comms` coupling. A `dm` keep is pinned only as `type='dm'` + a manually-populated household.

---

## §Satisfiability plan (for the contract-adversary's reference build)

The adversary must BUILD the reference impl to discharge 0-failed-against-a-correct-build. The correct build:
- **Schema:** `_keep_statements()` = `[_define_table(KEEP_TABLE)]` + `_define_field` per `_KEEP_FIELD_SPECS` + the call-time `type` field-def (`f"ASSERT $value IN [{types_allowed}]"`, NO DEFAULT) + `_plain_index(KEEP_TABLE, f"{KEEP_TABLE}_keeper", ("keeper",))`. `_member_of_statements()` = `[_define_relation_table(MEMBER_OF_RELATION, PRINCIPAL_TABLE, KEEP_TABLE, enforced=True)]` + `_define_field` per `_MEMBER_OF_FIELD_SPECS` (`since`) + the call-time `rank` field-def (`f"DEFAULT '{_KEEP_RANK_CONTRIBUTOR}' ASSERT $value IN [{ranks_allowed}]"`) + `_unique_index(MEMBER_OF_RELATION, f"{MEMBER_OF_RELATION}_in_out", ("in","out"))`. `generate_keep_ddl()` = `";\n".join(_keep_statements() + _member_of_statements()) + ";\n"`.
- **Store:** `create_keep` mints `str(ULID())`, resolves keeper via `self._principals.get_by_email` (the atomicity pin's seam), and in ONE `execute_transaction` composes a `TxnFragment` CREATE (`keeper` bound as `type::record('principal',$pid)`) + a `RELATE $keeper->member_of->$keep` (the compose/execute_transaction idiom from `tasks.py::_apply`). `add_household_member` dedupes-before-RELATE (or catches UNIQUE). `remove_household_member` refuses when the member == `keep.keeper` (`KeeperLockoutError`). `list_household` reads `member_of` as a PLAIN table (`WHERE out = $keep`). `list_keeps_for_keeper` uses `WHERE keeper = $p`.
- **Verified satisfiable in shape:** every pin's GREEN condition is a property the correct build above produces; every RED pin's failure at stub is a MISSING statement/method, not a contradiction. I found NO pin that is RED on the correct build (no C-DEF). ⚠ The adversary should still run the reference build to CONFIRM — I could not build it (contract author).

---

## §Deviations (detail)

**D-1 — typecheck GREEN not RED.** Reported above. No owned bound needed.

**D-2 — two stale pin-name references in `test_blocks_edge.py` (OUTSIDE my writable set — flagged, not edited).** My rename of the exact-set pin (five→six) left two INERT references to the old name `test_the_relation_edge_set_is_EXACTLY_the_five_known_edges`:
- `test_blocks_edge.py:211` — a docstring line listing the pins blocks reddens (historical). Exact edit: `five` → `six` in that name.
- `test_blocks_edge.py:8888-8890` — a COMMENTED-OUT `mutation_proof.py` recipe (inert). Its `--expect-red "$X::…_five_known_edges"` and its `endpointsN` suffixes are now stale (adding `member_of` also RENUMBERED the `endpointsN` parametrize suffixes, as the recipe's own comment @8895 warns). Exact edit: rename to `_six_known_edges` and re-derive the `endpointsN` ids from `--collect-only`.
Both are comment/docstring-only, affect NO test execution (I re-ran `test_blocks_edge.py`'s classes → green). I left them per scope law (the brief's writable set does not include `test_blocks_edge.py`); the lead/builder can apply the one-line fixes when convenient. I fixed the one reference in my OWN writable file (`_enforced_relations_scaffold.py:117`).

**D-3 — `_resolve_principal_id` added to the `KeepStore` stub as REAL plumbing.** The brief said "compose a PrincipalStore … (mirror `PrincipalKeyStore._require_principal_id`)"; I made the composition + a `_resolve_principal_id` helper REAL in the stub so the builder has the reuse wired and the atomicity pin has a stable seam. Not a CRUD verb; harmless.

---

## §Decisions needed (1)

**Q-1 (build-dependency, non-blocking) — the create_keep atomicity injection seam.** `test_create_keep_is_ATOMIC_a_failed_keeper_edge_leaves_NO_keep_row` forces the keeper's `member_of` RELATE to fail by monkeypatching **`keep_store._principals.get_by_email`** to return a ghost-id `Principal` (the keep CREATE tolerates the dangling `record<principal>` link; the ENFORCED RELATE refuses the ghost `IN`). This ASSUMES create_keep resolves the keeper email through the composed `self._principals.get_by_email` — which the brief mandates ("compose a PrincipalStore for email→id resolution"). If the builder resolves differently (e.g. a raw `_query` SELECT), the injection seam must move. Recommendation: **keep it** — it doubles as a "route resolution through the shared lookup" (ONE-implementation) expectation. The adversary/builder should confirm the seam holds on the reference build; if not, adjust the monkeypatch target (a one-line edit) rather than weakening the atomicity property.

---

## §DRY ledger (new reusable symbols)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `KeepStore._query` | read `PrincipalStore._query` / `principal_keys` | the shared `run_query` seam | **REUSED** `loremaster.store._txn.run_query` (named EXACTLY `_query` so `test_retry_seam.py` scan binds it) |
| `KeepStore.ensure_ready` / `_ensure_connection` / `_drop_connection` / `_safe_close` | read `PrincipalStore` lifecycle | the house per-store connection-owner idiom (cloned by Principal/PrincipalKey/Finding) | **EXTENDED** the house pattern (POLICY — retry/txn/classification — stays shared in `_txn`; only the lifecycle scaffold is cloned, the accepted convention; NOT copy #2 of any policy) |
| `KeepStore._resolve_principal_id` | read `PrincipalKeyStore._require_principal_id` | the composed `PrincipalStore.get_by_email` + id-part | **REUSED** `PrincipalStore.get_by_email` (composed, never a cloned resolver) |
| `KeepStore._to_aware_utc` | read `PrincipalStore._to_aware_utc` | the fleet-comparable datetime coercion | **REUSED** by delegation to `PrincipalStore._to_aware_utc` |
| `Keep` / `Membership` | `lore_search "keep collaboration space model"` | no existing keep/membership value object (greenfield) | **HAND-ROLLED** (new domain objects; frozen `extra="forbid"` per the `Principal` idiom) |
| `KeepStoreError` / `KeepNotFoundError` / `KeeperLockoutError` | read `PrincipalStoreError` hierarchy | no keep error hierarchy (greenfield) | **HAND-ROLLED** (mirrors the `PrincipalStoreError(RuntimeError)` shape; `KeeperLockoutError` is the Fork-F-rider typed error) |
| `_keep_statements` / `_member_of_statements` / `generate_keep_ddl` | read `_principal_statements` / `_briefed_statements` | the shared DDL emitters | **REUSED** `_define_table`/`_define_field`/`_define_relation_table`/`_plain_index`/`_unique_index` (proven by the two mutation pins) |
| `KEEP_TABLE` / `MEMBER_OF_RELATION` / `_KEEP_TYPES` / `_KEEP_RANKS` / field specs | greenfield (grepped — no keep scaffolding) | nothing | **HAND-ROLLED** (new single-source constants, the `PRINCIPAL_TABLE` idiom) |

---

## §STAND-BY
Task `d2db30818c4f40169fa7df35a9a48009` → done. Standing by for a contract revision from the adversary/lead (I stay done-but-available via `lore_comms`; #357 makes done→in_progress illegal, so I will not re-transition — I answer on-thread and edit in place if routed a revision).
