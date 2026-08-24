# REPORT-contract-62w1 — packet 62 Wave 1 CONTRACT (the `owns` edge store foundation)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read: `docs/reference/surrealdb-31-capabilities.md` — cited by § below
  (§1.1 DDL clause rule, §1.4 new-field-on-populated-table-must-be-`option<>`, §1.6
  dirty-store blind spot, §2 `record<t>` links do-not-auto-clean + protected `session`
  variable + `SELECT *` omits NONE `option<>`, §4 traversal-not-index-served). Never
  re-transcribed.

## SUMMARY BLOCK
- **State:** done-with-deviations (contract RED at HEAD, satisfiable by argument; no
  reference build run — the adversary's reference build discharges the receipt per brief).
- **Deviation 1 (brief fact stale — verify-don't-assume):** the brief says the exact-set pin
  "currently certifies exactly TWO links (`principal_key.principal`, `keep.keeper`)". Ground
  truth at HEAD: it certifies **THREE** — `audit.actor_principal` was added by packet 61a-w4
  (DANGLE-TOLERATED). So `agent.owner_principal` is the **FOURTH** link; my expected set has 4
  entries, not 3. Trusting "two→three" would have DELETED `audit.actor_principal` from the set
  and reddened a correct build.
- **Deviation 2 (instrument reach fix, in-scope):** the exact-set pin scanned only
  `generate_ddl`, which does **NOT** fold the standalone `agent` slice (`generate_agent_ddl`)
  — so it was structurally BLIND to any `record<principal>` link on `agent`, i.e. blind to
  `agent.owner_principal`. Broadened it to scan `_all_schema_ddl()` — the DERIVED union of
  every `generate_*_ddl` surface (reach law #344/#345 / Fork 4 R4.1). Added a reach-control pin.
- **Deviation 3 (writable-set path):** brief said tests live under `loremaster/loremaster/tests/`;
  the real test dir is `loremaster/tests/`. Wrote there (where all sibling schema tests live).
- **Deviation 4 (Wave-1 isolation decision):** agent rows in the live/dangle tests are built by
  a raw `CREATE` that sets `owner_principal` directly, NOT `AgentRegistry.register` — the
  register-time owner STAMP is SCOPE item 2 (a LATER wave), so `register` does not populate
  `owner_principal` yet. Wave 1 pins the SCHEMA + DELETE semantics in isolation.
- **Packages considered:** none — no mechanism specified (contract TESTS only). The field/index
  the build adds routes through `surreal_schema`'s existing in-house `_define_field` / `_plain_index`
  emitters (pinned by the routing-mutation test); no library choice.
- **Reuse ledger:** 1 new reusable symbol (`_all_schema_ddl`), dispositioned below; the rest are
  test-local scaffolding per the established per-file `_create_*`/`_one`/`_bare` convention.
- **Graded:** n/a (I authored a contract; I rendered no verdict on another agent's artifact).
  Contract authored at HEAD `29e15f2`; `git rev-parse HEAD` = `29e15f2` at report time.
- **Decisions-needed:** none open (all four forks operator-ruled). Deviations 1 & 2 are
  corrections I resolved within scope, surfaced here for the lead/adversary — not open forks.
- **Receipt pointers:** new file `loremaster/tests/test_agent_owns_principal_schema.py`;
  edited pin `test_principal_keys_schema.py::TestTheCascadeForwardScopeIsPinned` +
  helper `_all_schema_ddl`; RED/GREEN run tail in §"RED verification".

---

## Scope executed (FINAL PACKET-62 SCOPE LINE items 1 & 4 ONLY)

Wave 1 = the store foundation. Contracted:
- **Item 1** — `agent.owner_principal : option<record<principal>>` field-link on the comms
  `agent` table (the `owns` edge, Fork 3 — SCALAR field-link, NOT a relation edge) + its
  non-unique index; `DEFINE FIELD OVERWRITE` (§1.1), `option<record<principal>>` because it is
  a NEW field on the POPULATED `agent` table (§1.4, R3.4); index `IF NOT EXISTS` never
  `OVERWRITE`; dirty-store migration pinned (§1.6).
- **Item 4** — `PrincipalStore.delete` accounts for `agent.owner_principal` as a new
  `record<principal>` link, DANGLE-TOLERATED (R3.2 / I4): the exact-set pin in
  `test_principal_keys_schema.py` is updated (RED at HEAD) + a live dirty-store DANGLE test.

**NOT contracted (later waves / non-obligations, per the scope line):** the register-time owner
STAMP (item 2, R3.3), the `stamp_owner` seam (item 3), `agent_of` resolution, the anti-injection
DERIVED reach pin (item 5), any governed-column retrofit (63/64), and any deploy/posture work
(65). No production code written.

---

## Files delivered (writable set)

1. **NEW `loremaster/tests/test_agent_owns_principal_schema.py`** (16 tests) — items 1 & 4's
   behavioural + offline contract.
2. **EDIT `loremaster/tests/test_principal_keys_schema.py`** — `TestTheCascadeForwardScopeIsPinned`
   exact-set pin updated to 4 links + broadened reach; added helper `_all_schema_ddl` and reach
   control `test_the_scanned_corpus_covers_the_standalone_comms_slices`; `import inspect`.

---

## Declared expected-RED node ids (fixed from `--collect-only` BEFORE any result)

These flip **RED→GREEN** on a correct build; `mutation_proof.py` / the builder diff both ways.

```
# --- test_agent_owns_principal_schema.py (13) ---
TestTheOwnerPrincipalFieldDdl::test_the_owner_principal_field_is_emitted
TestTheOwnerPrincipalFieldDdl::test_the_owner_principal_field_is_option_wrapped_record_principal
TestTheOwnerPrincipalFieldDdl::test_the_owner_principal_field_is_OVERWRITE
TestTheOwnerPrincipalFieldDdl::test_the_owner_principal_field_carries_no_default_and_no_assert
TestTheOwnerPrincipalFieldDdl::test_the_owner_principal_field_routes_through_the_shared_emitter
TestTheOwnerPrincipalIndex::test_the_owner_principal_index_is_emitted
TestTheOwnerPrincipalIndex::test_the_owner_principal_index_is_IF_NOT_EXISTS_never_OVERWRITE
TestTheOwnerPrincipalIndex::test_the_owner_principal_index_is_NOT_unique
TestTheOwnerPrincipalFieldOnTheLiveEngine::test_an_owned_agent_stores_and_reads_back_its_principal_link
TestTheOwnerPrincipalFieldOnTheLiveEngine::test_a_principal_may_own_many_agents
TestOwnerPrincipalMigratesOntoAPopulatedAgentTable::test_a_new_owned_agent_is_writable_after_the_migration
TestPrincipalDeleteDanglesTheOwnedAgentBackLink::test_deleting_a_principal_that_owns_an_agent_succeeds_and_the_agent_survives
TestPrincipalDeleteDanglesTheOwnedAgentBackLink::test_deleting_a_principal_that_owns_MANY_agents_dangles_them_ALL
# --- test_principal_keys_schema.py (1) ---
TestTheCascadeForwardScopeIsPinned::test_the_record_principal_link_set_matches_the_cascade_adjudication
```

**GREEN-at-HEAD by design (POSITIVE CONTROLS / DISCRIMINATORS — the [fake]-leg pattern; must
STAY green through the build):**
```
# test_agent_owns_principal_schema.py
TestTheOwnerPrincipalFieldOnTheLiveEngine::test_an_ownerless_agent_reads_owner_principal_as_none   # option<> vs required
TestTheOwnerPrincipalFieldOnTheLiveEngine::test_the_agent_slice_is_safely_re_appliable              # OVERWRITE-index boot-crash
TestOwnerPrincipalMigratesOntoAPopulatedAgentTable::test_a_legacy_agent_survives_the_field_add_and_reads_owner_none
TestOwnerPrincipalMigratesOntoAPopulatedAgentTable::test_the_field_add_does_not_write_poison_the_legacy_row  # §1.4 required-poison
# test_principal_keys_schema.py
TestTheCascadeForwardScopeIsPinned::test_the_forward_scope_regex_has_nonzero_reach                  # pre-existing regex control
TestTheCascadeForwardScopeIsPinned::test_the_scanned_corpus_covers_the_standalone_comms_slices      # NEW reach control (INSTRUMENT-0)
```

---

## RED verification (run at HEAD `29e15f2`, spike-surreal `ws://127.0.0.1:18000`)

`pytest tests/test_agent_owns_principal_schema.py tests/test_principal_keys_schema.py -p no:randomly -q`:

```
14 failed, 36 passed in 5.15s
```

- 14 failed = the 14 declared expected-RED nodes (13 new-file + the exact-set pin). Each reds
  BEHAVIOURALLY, never on collection: the offline pins on `assert statement is not None`
  ("unbuilt"); the live pins on the store's own `Found field 'owner_principal', but no such
  field exists for table 'agent'`; the exact-set pin on `found` (3 real links) ≠ `expected` (4).
- 36 passed = the 6 controls above + every OTHER `test_principal_keys_schema.py` pin (no
  regression from the exact-set edit).

**Gates on the two files:** `uv run ruff check …` → *All checks passed!* · canonical
`bash scripts/typecheck.sh` → *loremaster OK* (236 source files, incl. the new test file). The
bare `uv run mypy tests/<file>` shows only the known `_surreal_harness` unfollowed-import
resolution artifact (every harness-importing test file shows it — CLAUDE.md: the per-member
runner is canonical); zero real errors.

---

## Satisfiability ARGUMENT (what a correct build does to green each pin)

The build adds ONE `("owner_principal", "option<record<principal>>", "")` triple to
`_AGENT_FIELD_SPECS` and one `_plain_index(AGENT_TABLE, f"{AGENT_TABLE}_owner_principal",
("owner_principal",))` to `_agent_statements()`; updates the `PrincipalStore.delete` cascade
docstring to name the new DANGLE-TOLERATED link (item 4 needs NO delete code change — dangle =
do nothing to agents). Then:

- **Offline field pins** — `_define_field(AGENT_TABLE, "owner_principal", "option<record<principal>>")`
  emits `DEFINE FIELD OVERWRITE owner_principal ON agent TYPE option<record<principal>>` → the
  emitted/OVERWRITE/`option<record<principal>>`/no-DEFAULT-no-ASSERT pins green; the routing
  mutation pin greens because the field goes through `_define_field` (the perturbed marker appears).
- **Offline index pins** — `_plain_index` emits `DEFINE INDEX IF NOT EXISTS agent_owner_principal
  ON agent FIELDS owner_principal` (no `UNIQUE`) → emitted / IF-NOT-EXISTS / NOT-UNIQUE green.
- **Exact-set pin** — `_all_schema_ddl()` now includes `generate_agent_ddl()`, so `_RECORD_PRINCIPAL`
  (already proven to match `option<record<principal>>` by the passing `…regex_has_nonzero_reach`
  control) finds `("owner_principal","agent")` → `found` == the 4-entry `expected` → green.
- **Live pins** — the declared column accepts a `record<principal>` value; the owned-agent read,
  the many-agents-per-principal read, the migration new-owned write, and the dangle all succeed;
  the ownerless-None and re-appliability controls stay green (§1.4/§1.1/§2).
- **Migration pins** — `_agent_ddl_without_owner_principal()` strips the field+index; applying
  the real slice OVER it lands the field via `OVERWRITE` on a POPULATED table; §1.4: the legacy
  row survives, reads None, is NOT poisoned (option<>); a new owned agent is writable.
- **Dangle pins** — the delete never touches `agent`, so an owned-principal delete succeeds
  (cascades 0) and every owned agent row survives (∀ owned agents, N=1 and N=2 fixtures) with a
  stale `owner_principal` record link (§2) — never refused, never cascaded, never nulled.

**C-DEF check (no pin RED on a correct build):** verified no existing test certifies the OLD
agent field-set (`_declared_fields` is used only for BRIEFED/TO relations; the agent field pins
are per-field, not exact-set), and `AgentRegistry._row_to_agent` reads only KNOWN columns via
`row.get(...)` — the unwired `owner_principal` (omitted by `SELECT *` when unset, §2) never
reaches the `extra="forbid"` `Agent` model. `test_schema_fold_coverage.py`'s slice-fn count is
unaffected (owner_principal is a field within `_agent_statements`, not a new slice fn). So the
field-add reddens nothing outside my writable set.

---

## Reuse ledger (brief-base §6)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_all_schema_ddl` (test_principal_keys_schema.py) | read `test_schema_fold_coverage.py` + `lore_search`/grep for DDL-corpus/`generate_*_ddl` enumerators | `derive_slice_fns` / `scan_schema_fold_coverage` (`_schema_fold_guard`) derive slice-fn NAMES from AST SOURCE for FOLD-coverage — they do NOT return concatenated DDL TEXT for a `record<principal>` regex scan | **HAND-ROLLED** — the existing helper answers a different question (names, not DDL text; source-AST-based, not runtime-generate-based). `_all_schema_ddl` is the analogous DERIVATION on the `generate_*_ddl` naming PROPERTY (never a hand-list), matching the reach law the packet elevates. |

Test-local scaffolding (`_create_agent`, `_agent_statements`, `_owner_field_statement`,
`_owner_index_statement`, `_agent_ddl_without_owner_principal`, `_apply_agent_ddl`, `_one`,
`_bare`, `dangle_env`): **HAND-ROLLED per the established per-file convention** — each schema
test module in this repo (`test_comms_schema.py`, `test_principal_keys_schema.py`,
`test_principal_delete_cascade_61.py`) defines its OWN local `_create_*`/`_one`/`_bare`; these
are not shared across test modules. `_create_agent` deliberately mirrors
`test_comms_schema._create_agent`'s bound-`$content` idiom (store §2: `session` is a PROTECTED
variable — caught live during RED verification, first draft used a top-level `$session` param and
the engine rejected it).

---

## Decisions / notes for the adversary + lead

1. **Deviations 1 & 2 (above) are corrections, not open forks** — all four packet-62 forks are
   operator-ruled. But the exact-set pin now (a) has **4** entries (the brief's "two→three" was
   stale by one — `audit.actor_principal`), and (b) scans a **derived generate_*_ddl union**, not
   `generate_ddl` alone. If either should differ, that is a lead/adversary call; my reasoning is
   in the pin docstring + `_all_schema_ddl` docstring.
2. **Over-reach of `_all_schema_ddl` is SAFE for a PIN-THE-MISS tripwire.** It scans every
   `generate_*_ddl`, including slices possibly applied to a different database. At correct-build
   the found set is exactly the 4 unified-store links (no other `record<principal>` exists —
   grep-verified: only lines 1908/2037/2187 in `surreal_schema.py`). If a FUTURE link appears in
   any slice, the pin reds and forces a human to adjudicate — the safe direction.
3. **The two `owner_principal` links are DIFFERENT.** THIS one (`agent.owner_principal`, the
   agent-NODE's owner) is DANGLE-TOLERATED. 63/64's future GOVERNED-ROW `owner_principal` (a
   governed row's owner) is a LIVE-DEPENDENCY → cascade-or-refuse. The pin docstring and re-open
   trigger say so, so a reader does not conflate them.
4. **Dangle test uses a raw `CREATE`, not `register`** (Deviation 4) — pins schema + delete
   semantics without depending on the item-2 stamp. The adversary should confirm this isolation
   is the intended Wave-1 boundary.
5. **Adversary frontier to attack:** (a) can a wrong build green the migration `not-poison`
   control while shipping a REQUIRED field? (b) does the dangle test truly discriminate
   refuse/cascade/null-the-link (it forces each fate)? (c) is `_all_schema_ddl`'s reach a genuine
   derivation or a hand-list in disguise (the reach control guards it — attack that)? (d) the
   regex `_RECORD_PRINCIPAL` on a hostile spelling (`record<principals>`, nested option).
