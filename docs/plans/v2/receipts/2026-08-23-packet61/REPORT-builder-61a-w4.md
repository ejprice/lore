# REPORT — builder-61a-w4 · the append-only `audit` store substrate

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done (round 2, lead-ruled delta applied). The **76-pin** revised w4 contract is
  GREEN (identity-at-write added); the 2 tripwires I escalated are now GREEN via the lead's
  authorized test edits (§9 dangle-tolerated ruling + the execute_transaction owner roster);
  fold-guard 29 + shape-guard 56 green; mypy 0; ruff clean; **5/5 mutation proofs**
  RED-then-restored byte-exact. Solo full-suite count filled under Gate receipts.
- **Round history:** round 1 built the 71-pin substrate + escalated the 2 tripwires; round 2
  (this) applied the operator/sidecar-ruled identity-at-write delta + the 2 authorized test
  edits + the new link-only mutation proof.
- **Mission:** greened the SUFFICIENT-graded RED contract for packet 61a-w4 (the append-only
  `audit` table substrate) — the last 61a wave. Wrote MINIMAL production code; did NOT touch
  the contract tests or the live guards.
- **Deviations:** none.
- **Packages considered:** `python-ulid` (`from ulid import ULID`) → **keep** — already the
  house id-mint (`keeps.create_keep`); reused, no new dep. Txn/retry/backoff →
  **reused** `loremaster.store._txn` (`execute_transaction`/`compose`/`wrap_store_rejection`),
  no bespoke policy. No new external package introduced.
- **Reuse ledger:** 8 new symbols, all dispositioned (see DRY ledger) — every one a MIRROR of
  the packet-60 `KeepStore`/`_keep_statements` precedent, as the brief instructed.
- **Graded:** n/a — this report renders no verdict on another artifact (it is a build report).
  Built at HEAD `e92bd0f` (branch `feat/surreal-unification`); `git rev-parse HEAD` at write =
  `e92bd0f` (working tree, uncommitted — the lead commits after a cold audit).
- **Decisions needed:** none.
- **Receipt pointers:**
  - Schema slice: `loremaster/loremaster/store/surreal_schema.py` — `AUDIT_TABLE` /
    `_AUDITED_ACTIONS` / `_AUDIT_FIELD_SPECS` / `_audit_statements` / `generate_audit_ddl`, and
    the fold in `generate_ddl` (after `_member_of_statements()`).
  - Store: NEW `loremaster/loremaster/audit.py` — `AuditStore` + `AuditStoreError`.
  - Gate receipts + mutation table + #410 handling + DRY ledger: sections below.

## RESOLUTION — the 2 tripwires (lead-ruled 2026-08-23, edits authorized)

Round 1 escalated 2 deliberate coverage tripwires my correct build fired. The lead ruled the
`PrincipalStore.delete` disposition (operator/sidecar §9) and authorized the two test edits as
disclosed §2 coverage edits (my audit code fired the pins). Both applied and GREEN:

### Tripwire 1 — `test_principal_keys_schema.py::TestTheCascadeForwardScopeIsPinned`
The `audit.actor_principal record<principal>` link is added to the pin's expected set, and all
THREE `record<principal>` links are now CLASSIFIED (not flat-absorbed):
- `principal_key.principal` — **CASCADE-DELETE-OWNED-DATA**;
- `keep.keeper` — **REFUSE-LIVE-DEPENDENCY**;
- `audit.actor_principal` — **DANGLE-TOLERATED** (§9 RULED): audit is immutable history —
  cascade would let an admin erase their own trail (the §9 hole), refuse would make every actor
  un-deletable; the human identity is instead preserved by the DENORMALIZED `actor_email`/
  `actor_agent_name` VALUE columns (survives-delete pin proves it). The tripwire STAYS ARMED for
  the next new link (63/64 `owner_principal` = live-dependency-class → cascade-or-refuse, NOT
  dangle), with that guidance written inline.

### Tripwire 2 — `test_retry_seam.py::TestEveryProductionOwnerThreadsITSOWNUrl`
`AuditStore` is recorded as an **EXECUTE_TRANSACTION owner** (`_EXECUTE_TRANSACTION_OWNERS`
roster) — a class bootstrap owner with `_ensure_connection` but NO `_query` seam (its writes
thread the url through `execute_transaction`, not a single-statement `_query`; NO dead `_query`
added). It is genuinely DRIVEN by a new pin
(`test_each_execute_transaction_owner_logs_ITS_OWN_url_on_bootstrap_exhaustion`, same machinery
as the `_QUERY_SEAMS` owners), added to the coverage `driven` set and the pairwise-distinct url
list — so coverage stays a checked variable, not a widened exclusion. (Counts elsewhere use
`>= MIN` floors and `test_every_bootstrap_session_call_passes_a_url` passes — my
`_ensure_connection` threads `url=self._url` — so no other retry_seam pin moved.)

## WHAT I BUILT (minimal — to green the pins)

### 0. Identity-at-write (round-2 delta — operator §9 forensics / Fork G addendum)
`actor_email` + `actor_agent_name` added to the audit schema as **DENORMALIZED required
non-empty string VALUE columns** (NOT links — `_CHUNK_STRING_TYPE` + `_NON_EMPTY_STRING_ASSERT`,
the `target_table` idiom). `append`/`append_fragment` take them as CALLER-PROVIDED required
kwargs (no internal principal fetch — the capture pin reds a store-side-derive build), written as
bound `$audit_email`/`$audit_agent_name` VALUE columns. Payoff: on a principal-delete the
`actor_principal`/`actor_agent` LINKS dangle but the identity VALUES survive (proven by
`TestTheDenormalizedIdentitySurvivesActorDelete`).

### 1. The `audit` table schema (`store/surreal_schema.py`)
Mirrors the packet-60 `_keep_statements`/`generate_keep_ddl` house format exactly.
- `AUDIT_TABLE = "audit"`.
- `_AUDITED_ACTIONS = ("WRITE", "DELETE", "SET_SCOPE", "SET_OWNER")` — the MUTATING actions
  only (Fork G/C). READ is NEVER audited. The `action` ASSERT is **derived at CALL TIME** from
  this tuple in `_audit_statements` (the `_principal_statements`/`_keep_statements` idiom), so a
  tuple change moves the emitted ASSERT (mutation-provable — pin
  `test_changing_the_AUDITED_ACTIONS_tuple_changes_the_emitted_ASSERT`).
- `_AUDIT_FIELD_SPECS`: `actor_principal record<principal>` + `actor_agent record<agent>`
  (REQUIRED links — greenfield, store §1.4 N/A), `target_table`/`target_row` (`string` +
  `_NON_EMPTY_STRING_ASSERT`, open domain — NOT a closed `$value IN [...]` reach-trap),
  `old_value`/`new_value` (`option<object>` + `FLEXIBLE` — the `finding.checkpoint` precedent,
  store §1.7), `created_at datetime DEFAULT time::now()` (engine-stamped, store OMITS).
- `action` field-def is emitted at call time (closed-domain ASSERT, **NO DEFAULT**).
- Every FIELD routes through the shared `_define_field` (→ `OVERWRITE`, #107) and the table
  through the shared `_define_table` (→ `SCHEMAFULL IF NOT EXISTS`) — proven by the two
  route-through mutation pins.
- NO index — Fork G defers it (pin `test_the_audit_slice_emits_NO_index`; re-open trigger: the
  first audit-listing verb).
- `generate_audit_ddl()` returns the house `";\n".join(...) + ";\n"` shape.
- **Folded into `generate_ddl` AFTER `_member_of_statements()`** (Fork G). `record<agent>` over
  an absent `agent` table is fine (a `record<t>` field-def needs no target at DDL time —
  proven live by `TestTheFullDdlWithAuditFoldedApplies`).

### 2. `AuditStore` (NEW `loremaster/loremaster/audit.py`)
Mirrors `KeepStore`'s connection-owner lifecycle (`_ensure_connection`/`ensure_ready`/`close`/
`_drop_connection`/`_safe_close`) but composes **NO** `PrincipalStore` (decision (3): `append`
takes already-resolved actor ids).
- **Narrow append-only surface:** the only public members across the FULL MRO are `append`,
  `append_fragment`, `ensure_ready`, `close`. No mutator, own or inherited (`AuditStore(object)`
  — no base carries a public member). Proven by the MRO-resolved surface pins.
- `append_fragment(...) -> TxnFragment`: ONE composable `CREATE` (no `BEGIN`/`COMMIT`), a
  client-minted `str(ULID())` id (creation-ordered), actor ids bound via `type::record`,
  `old_value`/`new_value` written only when provided (omitted → NONE), all params namespaced
  under `audit_*` (`_AUDIT_FRAGMENT_PARAM_PREFIX`) so a co-composed 63/64 mutation can't collide.
- `append(...) -> str`: executes `compose(self.append_fragment(...))` through the VERIFIED
  `execute_transaction` seam (store §3), returns the created row's `str(RecordID)` (`audit:<ulid>`).
  `append`'s write **IS** the composable fragment (ONE path — proven by
  `test_append_write_IS_the_composable_fragment_one_path`).
- **Born WRAPPED (Fork I, the 9th consumer of #400's ONE seam):** routes engine rejections
  through `_txn.wrap_store_rejection` → `AuditStoreError`; transport/exhausted-contention pass
  through untouched. NOT a hand-rolled clone (the live w2 shape-guard confirms).

### 3. Threat-model docstring (on `AuditStore`)
Append-only is IN-PROCESS, two layers: Layer 1 (this wave — the narrow MRO-clean surface),
Layer 2 (61b — the PDP admin `audit` carve-out). NOT a boundary against direct-store/ROOT
access (lore is root, Version A) — an ACCEPTED BOUND, with the Version-B re-open trigger
(per-principal record auth). Written so a future auditor meets "root can delete audit rows" as a
deliberate trade, not a hole. (Pins: `TestTheThreatModelIsStatedInTheInstrument`.)

## #410 LANDMINE HANDLING (coldaudit-61a-w3 R1)
There was **no** stub in the tree at `e92bd0f` (no `RED-STUB`/"emits nothing" comment existed to
retire) — the schema symbols and `audit.py` did not exist, so the RED baseline was an
`ImportError`, and I wrote the emitting slice fresh. `_audit_statements`'s docstring and the
line directly above its `def` (a blank line) contain **none** of the guard's
`KNOWN_EMPTINESS_PHRASES` (`emit []`, `emits nothing`, `red stub`, `not folded`,
`do not implement`, `raises notimplementederror`). The w3 fold-guard's prose backstop
(`scan_stale_emptiness_prose`) and structural leg (`scan_schema_fold_coverage`) are both GREEN
(29/29 in `test_schema_fold_coverage.py`).

## MUTATION-PROOF TABLE (real tree, `cp -a` content backup, byte-exact restore)
`audit.__file__` = `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/audit.py` (real
tree; provenance printed via `uv run`). `audit.py` md5 `cd5e9698bc7c1e97dd6eb77120d8bcb0`
identical before every mutation and after every restore; `surreal_schema.py`
`cb5c7afec32efbed39bf3d0e308b35d1` untouched throughout.

Round-2 baseline md5s (identical before every mutation and after every restore): `audit.py`
`c8004eedafbb37ea41408c4c610ecdc1`, `surreal_schema.py` `95e4fa0dd51caa13911053191188a657`.
`audit.__file__` resolves inside the real tree (printed via `uv run`).

| # | mutation (production, real tree) | pin(s) that RED | observed |
|---|---|---|---|
| 1 | `AuditStore(_MutationProbeBase)` inheriting `async def purge` | `test_the_reachable_public_surface_is_within_the_safe_allowlist` + `test_no_mutator_member_is_reachable` | RED — `inherits mutator method(s) ['purge']` |
| 2 | `record_id = uuid.uuid4().hex` (non-creation-ordered) | `test_sequential_appends_produce_creation_ordered_ids` | RED — ids not sorted |
| 3 | hand-rolled full-#400 `try/except (Conn, Contention): raise; except SurrealStoreError: raise Audit… from e` | w2 `test_no_full_idiom_wrap_appears_outside_the_seam` + `test_append_routes_through_the_shared_wrap_seam` | RED — full-idiom clone flagged; `wrap_store_rejection` absent from `append` |
| 4 | `append_fragment` always records `new_value` (`{}` when None) | `test_append_writes_a_DELETE_record_with_a_NONE_new_value` | RED — `assert {} is None` |
| 5 (NEW) | **link-only build** — `append_fragment` drops the denormalized values + schema cols → `option<string>` | `TestTheDenormalizedIdentitySurvivesActorDelete::test_actor_identity_survives_a_hard_principal_delete` | RED — `assert None == 'compromised-admin@example.com'` (identity lost after principal-delete) |

All five restored byte-exact; the full 76-pin contract re-run GREEN post-restore (76 passed).
Mutation 5 spans both production files (`audit.py` + `surreal_schema.py`); both restored to the
baseline md5s above.

## GATE RECEIPTS (round 2)
- **Contract (the 76 pins):** `test_audit_schema.py` (45) + `test_audit_store.py` (31) →
  **76 passed** (`… test_audit_schema.py test_audit_store.py -q` → `76 passed in 5.49s`).
- **Tripwires now GREEN:** `test_retry_seam.py::TestEveryProductionOwnerThreadsITSOWNUrl` +
  `test_principal_keys_schema.py::TestTheCascadeForwardScopeIsPinned` → 23 passed; the FULL two
  files (`test_retry_seam.py` + `test_principal_keys_schema.py`) → **698 passed** (`-n auto`; the
  one `RuntimeWarning` is a pre-existing scout-subscription coroutine warning, unrelated).
- **`./scripts/typecheck.sh` → 0** (every member OK incl. `loremaster` with new `audit.py`;
  shellcheck OK). **`uv run ruff check .` → `All checks passed!`** (my `test_retry_seam.py`
  import was auto-sorted by `ruff --fix` into the module import block).
- **LIVE guards stay green:** `test_schema_fold_coverage.py` (29) + `test_engine_rejection_seam.py`
  (56) → **85 passed** (audit slice folded, no false-positive prose; born-wrapped `audit.py` not
  flagged).
- **Full suite `loremaster/tests` SOLO (`-p no:xdist`, per #405 / lead directive):**
  **8574 passed, 0 failed**, 50 skipped, 3 xfailed in 2334.06s (38m54s). The honest solo count
  is clean — 0 failures. (Round-1 `-n auto` was 8566 passed / 2 failed; the 2 were the tripwires,
  now green, and the count rose by the new identity/owner pins.)

## FILES TOUCHED
- `loremaster/loremaster/store/surreal_schema.py` — the audit slice (`AUDIT_TABLE`,
  `_AUDITED_ACTIONS`, `_AUDIT_FIELD_SPECS` incl. `actor_email`/`actor_agent_name`,
  `_audit_statements`, `generate_audit_ddl`) + the fold into `generate_ddl`.
- `loremaster/loremaster/audit.py` — NEW: `AuditStore` + `AuditStoreError` (with the
  identity-at-write kwargs).
- `loremaster/tests/test_principal_keys_schema.py` — **tripwire 1** (lead-authorized §2 coverage
  edit): the classified 3-link cascade adjudication.
- `loremaster/tests/test_retry_seam.py` — **tripwire 2** (lead-authorized §2 coverage edit): the
  `_EXECUTE_TRANSACTION_OWNERS` roster + its driving pin + coverage/distinctness updates + the
  `AuditStore` import.
- `REPORT-builder-61a-w4.md` — this report.
- **Not touched:** the w4 contract test files (`test_audit_schema.py`/`test_audit_store.py` — my
  spec), the w2/w3 live guard tests, git state (the lead commits after a cold audit).
- **⚠ FLAG (not mine):** `git status` shows `M docs/design/2026-08-22-packet61-pdp-audit-rulings.md`.
  I did NOT edit that file this session — it is presumably the operator/sidecar §9 identity-at-write
  ruling edit that authorized this round-2 delta. Surfaced per scope law; the lead owns it.

## REGISTRATION SITES
`./scripts/registration_sites.py` → 54 co-occurrence sites, 22 incomplete — **all pre-existing
STALE member-prose sites, none introduced by this wave**. `audit.py` is a NEW MODULE inside the
EXISTING `loremaster` workspace member, not a new workspace member — so no `pyproject`/`mypy_path`/
`typecheck.sh MEMBERS`/`_SCANNED_MEMBERS`/`Containerfile`/`conformance_provenance.EXPECTED_MEMBERS`/
`scratch_provenance.WORKSPACE_MEMBERS` change applies (those track MEMBERS). Fork G explicitly
does NOT wire `AuditStore` into `build_app_context` (the table is readied via the `generate_ddl`
fold), so no DI registration either.

## DRY LEDGER (§6 — new reusable symbols; all mirror the packet-60 KeepStore precedent)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `AUDIT_TABLE` | `lore_get_symbol _keep_statements` (KEEP_TABLE precedent) | table-name constant idiom | HAND-ROLLED (new table name; mirrors `KEEP_TABLE`/`PRINCIPAL_TABLE`) |
| `_AUDITED_ACTIONS` | `_principal_statements`/`_keep_statements` (call-time domain idiom) | `_KEEP_TYPES`/`_PRINCIPAL_STATUSES` derive-at-call-time pattern | HAND-ROLLED (new domain tuple; mirrors `_KEEP_TYPES`) |
| `_AUDIT_FIELD_SPECS` | `_keep_statements` source | `_KEEP_FIELD_SPECS` `(name, type_expr, constraint)` triples | HAND-ROLLED (new field set; mirrors `_KEEP_FIELD_SPECS`) |
| `_audit_statements` | `_keep_statements` source | the slice-assembler idiom (routes `_define_table`/`_define_field`) | HAND-ROLLED (mirrors `_keep_statements`); REUSES `_define_table`, `_define_field`, `_NON_EMPTY_STRING_ASSERT`, `_CHUNK_STRING_TYPE`, `PRINCIPAL_TABLE`, `AGENT_TABLE` |
| `generate_audit_ddl` | `generate_keep_ddl` source | the standalone-slice generator idiom | HAND-ROLLED (mirrors `generate_keep_ddl`) |
| `AuditStore` | `keeps.py` (KeepStore) | the connection-owner store idiom | HAND-ROLLED (mirrors `KeepStore`); REUSES `bootstrap_session`, `signin_credentials`, `_CONNECTION_ERRORS`, `_SurrealConnection`, `execute_transaction`, `compose`, `TxnFragment`, `wrap_store_rejection`, `str(ULID())`, `str(RecordID())` |
| `AuditStoreError` | `KeepStoreError` (grep) | the domain-error base idiom | HAND-ROLLED (mirrors `KeepStoreError`; a `RuntimeError` subclass) |
| `_AUDIT_FRAGMENT_PARAM_PREFIX` | `graph_surreal.purge_file_fragment` (`GRAPH_FRAGMENT_PARAM_PREFIX`) | the fragment param-prefix idiom | HAND-ROLLED (mirrors `GRAPH_FRAGMENT_PARAM_PREFIX`) |

**Key REUSES (not forked):** `wrap_store_rejection` (born-wrapped, the ONE #400 seam — the w2
shape-guard proves no clone), the shared `_define_field`/`_define_table` emitters (the two
route-through mutation pins prove sharing), `compose`+`execute_transaction` (the verified txn
seam), `str(ULID())` id-mint (from `keeps.create_keep`).
