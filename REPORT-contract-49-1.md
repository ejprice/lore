# REPORT — contract-49-1 (packet 49 CONTRACT AUTHOR)

`brief-base v14 read` · `brief project v7 read`

**CAPABILITY CHECK (first, per brief-base §4):** brief demands = read files, lore tools,
comms/task ledgers, run scoped pytest against spike-surreal `:18000`, write stubs+tests.
All satisfiable and exercised — no gap. **Model:** the brief asserts `claude-opus-4-8`; I
cannot read my own model, but the brief asserts 4.8 and the session env corroborates
(`CLAUDE_CODE_SUBAGENT_MODEL=claude-opus-4-8`). Proceeded on that basis.

---

## SUMMARY BLOCK

- **State:** done — contract (failing tests) + minimal STUBS written; **LEAD RULINGS #5070
  APPLIED** (§LEAD RULINGS APPLIED) + **ADVERSARY #5073 INSUFFICIENT → all fixes applied**
  (§ADVERSARY FIXES APPLIED). Suite is RED behaviourally (NEVER ImportError). No
  implementation logic written.
- **RED receipt (scoped, `-n auto`, per-file — AFTER adversary fixes):** schema 27F/5P ·
  keys-store 1F/2P/27E · cli 27F/14P · store-ext 4F/17P/4E → **aggregate 59 failed + 38
  passed + 31 errors (128 collected)**. The 38 green = interface freezes (value objects),
  structural standing-guards (`prog`, no-`--execute`, `__main__`-guard-last, no-`load_config`,
  the F2 regex-reach positive-control), vacuous-clause pins guarded by RED existence pins,
  and the 17 unchanged 48-B `PrincipalStore` tests. The 90 RED (F+E) are feature pins failing
  on `NotImplementedError` / empty-DDL / missing verbs — RED-for-the-right-reason. ruff + mypy
  clean on all touched files; no regression (retry_seam 605 green).
- **deviations:** (1) sibling factories placed in `principals.py`/`principal_keys.py`
  (my writable set), NOT `store/surreal.py` as design §F6's "next to `build_store`"
  suggested (that file is out of scope; module-ownership is cleaner) — see §Deviations.
  (2) principal_key DDL pins live in a new `test_principal_keys_schema.py` (cohesion),
  not appended to `test_principals_schema.py`.
- **Packages considered:** `secrets.token_urlsafe` — `keep` (stdlib; the CLI secret gen,
  design §F4; read: stdlib). `hashlib` — `replace` with `loremaster.index.records.sha512_hex`
  (read: its source @records.py:108). `argparse` — `keep` (stdlib house CLI idiom; read:
  `index/cli.py`). `cachetools`/TTL — **rejected** by R12 (revocation beats any cache; read:
  design §F3 / pkt-39 §3-R12). bcrypt/argon2 — **N/A** (256-bit high-entropy random secret,
  not a password; read: design §F4 + odoo-code `_validate_odoo_api_key` uses unsalted sha512).
- **Reuse ledger:** 6 new reusable symbols/families dispositioned (all HAND-ROLLED with a
  cited no-match search or an EXTENDED-idiom reason); 6 external reuses cited. See §DRY LEDGER.
- **Graded:** none (I authored; I graded no one else's artifact).
- **decisions-needed: 0 outstanding — all 7 RULED by lead (directive #5070, 2026-08-20).**
  #1/#3/#5/#7 confirmed as-authored; #2 tightened (exception taxonomy), #4 resolved (pin #19
  unflagged, canonical seam), #6 added (creds-free pin). See §LEAD RULINGS APPLIED. Original
  fork analysis retained in §AMBIGUITIES for provenance.
- **pointers:** stubs → `loremaster/loremaster/principal_keys.py`,
  `principals.py::{set_expires,delete,build_parser,build_principal_store,main}`,
  `store/surreal_schema.py::{PRINCIPAL_KEY_TABLE,_principal_key_statements,generate_principal_key_ddl}`.
  contract → `loremaster/tests/test_principal_keys_{schema,store}.py`,
  `test_principals_cli.py`, `test_principals_store.py::{TestSetExpires,TestDelete}`.
  Pin→test→mutation table → §PIN COVERAGE. Store-behaviour probe → §PROBE.

---

## The ONE message to lead

`STATE: done · REPORT: REPORT-contract-49-1.md · pkt-49 contract+stubs RED (54F/36P/30E, 120 collected); 7 decisions-needed flagged, none blocking`

---

## LEAD RULINGS APPLIED (directive #5070, 2026-08-20)

The lead ruled all 7 of my escalations. Net = 3 real changes + 4 confirmations; contract
revised, scoped RED re-run (counts above reflect the revision).

| # | ruling | change made |
|---|---|---|
| 1 | `delete -> int` — ACCEPT | none (as-authored) |
| 2 | **TIGHTEN taxonomy** — missing PRINCIPAL → `PrincipalNotFoundError`; missing KEY → `PrincipalKeyNotFoundError` | replaced the `raises((PrincipalNotFoundError, PrincipalKeyStoreError))` unions with the specific type per case (mint / list_for / revoke-unknown-principal → `PrincipalNotFoundError`; revoke-unknown-key → `PrincipalKeyNotFoundError`); **added** `test_revoke_unknown_principal_raises_principal_not_found` to distinguish the two revoke cases |
| 3 | pin 17b — ACCEPT route-through `_row_to_principal` | none (as-authored) |
| 4 | **pin #19 RESOLVED** — Fable F8=YES (terminal render IN scope, `075a1bd`); canonical seam `loremaster.sanitise.sanitise_line`/`safe_str` (finding #34) | UNFLAGGED `TestRenderSafety` (removed PENDING); retargeted the source-scan to `{sanitise_line, safe_str}`; **added** `test_render_routes_through_the_shared_sanitiser_by_mutation` (patches the canonical seam across every import style — proves sharing, catches a private clone); pinned the LINE sanitiser, NOT the fence machinery |
| 5 | `--email` flags — ACCEPT | none (as-authored) |
| 6 | **RULE creds-free** — CLI resolves ONLY the surreal block; MUST NOT require the Anthropic key | **added** `TestCredsFreeConfigResolution`: `test_the_cli_runs_with_no_anthropic_key_set` (delenv ANTHROPIC → a verb still succeeds — catches an eager `load_config` build) + `test_the_cli_does_not_call_load_config` (AST guard) |
| 7 | revoke idempotency — ACCEPT | none (as-authored) |

---

## ADVERSARY FIXES APPLIED (directive #5073 — INSUFFICIENT → revised)

adversary-49-1 graded INSUFFICIENT (a STRONG pass — it BUILT the reference and proved the
contract satisfiable **after** these fixes: 107 passed / 0 failed). All are CONTRACT/test
fixes; NO design change. Applied in full:

| # | finding | fix applied |
|---|---|---|
| F1 | **C-DEF** — `TestPerPrincipalIdentity206` + `TestUniformDenyNoOracle` reused IDENTICAL `(name, secret)` across principals → identical `sha512(name:secret)` → `UNIQUE(hash)` rejects the 2nd mint on a CORRECT build | gave every co-existing key a DISTINCT secret (`_SECRET_3`/`_SECRET_4`); the #206 property is about PRINCIPAL identity, orthogonal to the secret |
| F2 | **C-DEF + zero-reach** — pin 14's `record<principal>\b` never matches `record<principal>;` (non-word→non-word, no boundary): permanently `set()`, so the exact-set pin is always RED AND can never fire when a new link is added | dropped `\b` → `TYPE\b[^;]*?record<principal>(?![\w<])` (also catches an `option<record<principal>>` wrapper); **added** `test_the_forward_scope_regex_has_nonzero_reach` (positive control — matches a synthetic real+hypothetical `memory.owner` link, proving reach) |
| F3 | **C-DEF** — `test_add`'s pre-`main` `SELECT email FROM principal` RAISES on a virgin DB (3.2.4, table absent) | `_principal_emails` / `_db_snapshot` now check `INFO FOR DB` first and return `set()`/`[]` when the table is absent (`_table_names` helper) |
| F4 | **MISSING PIN** — pin 19 exercised only `list`/`display_name`; a `list-keys` verbatim/clone key-name render shipped green (§F8 names key `name` as must-launder) | **added** `test_hostile_key_name_does_not_forge_a_row_in_list_keys` (behavioural, from adversary APPENDIX-B) + `test_list_keys_render_routes_through_the_shared_sanitiser_by_mutation` (PER-RENDER mutation-proof — closes R3: the AST scan passes on ANY single sanitise call, so `list` AND `list-keys` each get their own mutation-proof) |
| F5 | **HARNESS** — the 8 CLI e2e pins called `main()` synchronously from `async def` tests, but §F6's idiom is `main = asyncio.run(...)` → `RuntimeError` from a running loop | added `_run_cli(argv) = await asyncio.to_thread(p_module.main, argv)` — runs the mandated `asyncio.run` `main` OFF-loop; replaced every e2e `main()` call. Design idiom UNCHANGED |
| R1 | pin 2 store-level leak probe is vacuous (`mint` takes an already-hashed secret; raw never reaches the store) | **added** `test_mint_key_stores_only_the_hash_never_the_raw_secret` at the CLI layer where the raw EXISTS: mint-key → the stored row holds ONLY the hash (positive control: hash present), raw in no row/log |
| R2 | pin 17c proved `_query` EXISTS, not that the retry suite USES it | **strengthened** to `test_principal_key_store_query_seam_is_covered_by_the_retry_suite` — asserts `PrincipalKeyStore` is in `test_retry_seam._discover_query_seams()` (so the shared retry/backoff pins parametrize over it, mutation-proving it rides `run_query`) |
| R4 | no timing-oracle pin — ACCEPTABLE (uniform hash-index lookup, §F4) | no action (adversary concurs) |

**Reachability of a CORRECT build:** the adversary already BUILT the reference and proved the
contract 107/0 satisfiable after F1–F3/F5 (its APPENDIX-C carries the reference `verify` /
`delete` / schema excerpts — verify uses the single link-deref query and maps the principal via
`get_by_email`→`_row_to_principal`, so my pin-17b mutation reaches it). The F4/R1/R2 ADDITIONS
are satisfiable against those same reference shapes by construction (list-keys sanitised via
`safe_str`; mint stores only the hash; `_query` present → discovered). I write NO implementation,
so I did not re-build the reference — the adversary delta-grades it. Every revised pin re-run
RED-for-the-right-reason (no C-DEF, no ImportError); the F2 positive-control is GREEN (non-zero reach).

---

## PROBE (de-risking a C-DEF — the one store-behaviour question my fixtures rest on)

Before writing the live schema fixtures I probed the `record<>` link CONTENT-write shape
against the 3.2.x test store (`ws://127.0.0.1:18000`), per store-ref order (§2/§4 first,
then probe). Verbatim results (a throwaway DB, `parent`/`child` tables):

- `type::record('parent','p1')` in a CONTENT value position → **OK** (the shape my
  `_create_key` helper uses).
- a bound `RecordID('parent','p1')` param → **OK**.
- link-deref projection `owner.label AS plabel` → **returns the parent field** (this also
  validates the design §F3 *preferred single-query verify* shape — a builder de-risk).
- a bogus-target link → **written with NO existence check** (confirms store-ref §4:
  `record<t>` does not enforce, which is WHY the delete cascade is explicit).

This is why the live pins are RED via a CLEAN "slice unbuilt" assertion (the stub's empty
`generate_principal_key_ddl` is guarded in `_apply_key_ddl`), never an opaque SDK error on a
correct build.

---

## STUBS written (NO logic — RED-for-the-right-reason)

| file | added | RED condition it encodes |
|---|---|---|
| `store/surreal_schema.py` | `PRINCIPAL_KEY_TABLE` (real name), `_PRINCIPAL_KEY_FIELD_SPECS=()`, `_principal_key_statements()->[]`, `generate_principal_key_ddl()->""` | empty slice + **not folded** into `generate_ddl` |
| `principal_keys.py` (NEW) | `PrincipalKey`, `KeyVerification` (real frozen models), `PrincipalKeyStoreError`/`PrincipalKeyNotFoundError` (real), `PrincipalKeyStore` (every method `raise NotImplementedError`; NO `_query` yet), `build_principal_key_store` (raises) | methods raise; `_query` absent (pin 17c) |
| `principals.py` | `PrincipalStore.set_expires`/`delete` (raise), `build_parser` (bare parser, `prog` set), `build_principal_store` (raises), `main` (raises), `__main__` guard LAST | verbs/factory/main raise; guard-last GREEN by construction |

`_query` is deliberately **absent** from the stub `PrincipalKeyStore` so `test_retry_seam.py`'s
package scan is unperturbed (measured: 14 seams before and after the stub; `_MIN_KNOWN_SEAMS=13`
still met). Pin 17c FORCES the builder to add `async def _query`, at which point the scan
auto-discovers it (→15) and its parametrised pins prove it rides the shared `run_query`
(#102/#120) — no new registration needed (`_CTOR_VALUES` already carries the std ctor params).

---

## PIN COVERAGE — 19 design pins → test → the exact production edit that reddens it

| # | pin | test (file::class::method) | mutation that reddens |
|---|---|---|---|
| 1 | revoked key denied next verify (same key) | keys-store `TestTheFourDenyConditions::test_revoked_key_is_denied_on_the_next_verify` | drop the `revoked_at IS NONE` check |
| 2 | never stored raw (+ positive control: hash present) | keys-store `TestSecretNeverStoredRaw` | store the raw secret in any column |
| 3 | every verb executes directly; NO `--execute`/dry-run | cli `TestParserSurface::{test_no_verb_accepts_an_execute_flag,test_source_contains_no_execute_flag_or_dry_run}` + `TestVerbsExecuteDirectly::{add,delete,suspend,list-control,mint-once,revoke}` | add a `--execute` flag / gate a verb behind it |
| 4 | suspended principal's key denied (+unsuspend re-allows) | keys-store `TestTheFourDenyConditions::test_suspended_principal_denies_a_live_key` | drop the `status == 'active'` check |
| 5 | expired principal AND expired key — SEPARATE (QUANTIFIER) | keys-store `test_expired_key_is_denied_principal_fine`, `test_expired_principal_denies_a_live_key`, `test_all_clear_key_is_allowed_the_positive_control` | drop the key-`expires_at`/principal-`expires_at` check (each independently) |
| 6 | verify returns PRINCIPAL, per-principal (#206) | keys-store `TestPerPrincipalIdentity206` (≥2 principals, 1 with 2 keys) | return a constant / per-key identity |
| 7 | blank/malformed denied | keys-store `TestBlankAndMalformedDenied` (8 cases) | drop the `is_blank`/split validation |
| 8 | uniform deny (no oracle) + no raw secret in log | keys-store `TestUniformDenyNoOracle` | raise/return a reason-bearing value for any mode; log the secret |
| 9 | `generate_principal_key_ddl` idempotent | schema `test_the_slice_is_safely_re_appliable` | flip an index to `OVERWRITE` (boot-crash on re-apply) |
| 10 | `UNIQUE(principal,name)` per-principal + `UNIQUE(hash)` | schema `TestThePrincipalKeyIndexes` + live `{test_duplicate_hash_rejected,test_same_principal_and_name_rejected,test_two_principals_may_share_a_key_name}` | index `name` alone (global) / drop `UNIQUE(hash)` |
| 11 | `option<datetime>` NONE round-trips (+`SELECT *` control) | schema `test_option_datetime_columns_read_back_as_none...` + `test_select_star_OMITS...` | give `expires_at`/`revoked_at` a DEFAULT (looks already-stamped) |
| 12 | DDL folded into `generate_ddl` (#131) | schema `TestThePrincipalKeyDdlIsFoldedIntoGenerateDdl` | fold into the slice only, not `generate_ddl` (`+= _principal_key_statements()` line removed) |
| 13 | delete cascades N keys + ONE transaction | store-ext `TestDelete::{cascade,only-named,one-transaction(AST)}` | drop the child DELETE / its WHERE / use two `_query` DELETEs |
| 14 | PIN THE MISS — cascade forward-scope | schema `TestTheCascadeForwardScopeIsPinned` (exact-set scan) | add ANY new `record<principal>` link (reds by intent) |
| 15 | `__main__`-guard-last for `principals.py` | cli `TestMainGuardIsLast` | move a def/binding after the guard |
| 16 | `build_parser` separately testable | cli `TestParserSurface::{prog,every_verb,unknown/missing}` | drop a verb / wrong `prog` |
| 17 | sharing by mutation: (a) `is_blank` (b) `_row_to_principal` (c) `_query` seam | keys-store `TestSharingProvenByMutation` (3 tests) | clone the predicate / clone the mapper / hand-roll queries |
| 18 | env-var indirection; no secret printed (except mint) | cli `TestSiblingStoreFactories` (resolution) + `test_the_raw_secret_is_never_printed_by_a_non_mint_verb` | hardcode a coordinate / print a secret from a non-mint verb |
| 19 | CLI render routes through canonical sanitiser seam (LEAD-surfaced; ruled IN, F8=YES) | cli `TestRenderSafety` (behavioural hostile-fixture + source-scan `{sanitise_line,safe_str}` + **mutation-proof**) | render `display_name` verbatim (forged row survives) / clone the sanitiser (mutation marker absent) |
| +6 | CLI resolves surreal block CREDS-FREE (no Anthropic key) | cli `TestCredsFreeConfigResolution` | use `load_config` (eager anthropic → KeyError with the var unset) |

Extra behavioural pins beyond the 19 (interface hardening): `verify` hashes the WHOLE
`name:secret` (keys-store `test_verify_hashes_the_WHOLE_wire_string`); mint/list_for unknown
principal raise; revoke unknown key → `PrincipalKeyNotFoundError`; revoke idempotency; live
schema rejection pins (empty/missing hash/name/principal, undeclared field); §1.6 dirty-store
re-appliability (schema `TestSchemaMigrationAgainstAnExistingStore`).

---

## DRY LEDGER (brief-base §6 — one row per new reusable symbol)

| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `PrincipalKeyStore` | `lore_search("per-user API key store: hash/verify/resolve principal")` | only the pkt-49 DESIGN doc (0.64) — no impl | **HAND-ROLLED** — clones `PrincipalStore`/`FindingLedger` connection-owner idiom verbatim; NO new retry policy |
| `KeyVerification` / `PrincipalKey` | same search + read `principals.py::Principal` | no key value-objects exist | **HAND-ROLLED** — frozen `extra=forbid` models (the repo value-object idiom) |
| `PrincipalKeyStoreError`/`PrincipalKeyNotFoundError` | read `principals.py::PrincipalStoreError` | mirror the principal taxonomy | **HAND-ROLLED** (mirrors the sibling error hierarchy) |
| `generate_principal_key_ddl`/`_principal_key_statements`/`_PRINCIPAL_KEY_FIELD_SPECS`/`PRINCIPAL_KEY_TABLE` | `lore_get_symbol(_principal_statements / generate_principal_ddl / _define_field / _unique_index)` | the emitter idiom | **HAND-ROLLED emitter that REUSES `_define_table`/`_define_field`/`_unique_index`** (mutation-pinned: `test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters`) |
| `PrincipalStore.set_expires` | read `principals.py::set_status` | the clone target | **HAND-ROLLED** (clones `set_status` shape; rides `_query`) |
| `PrincipalStore.delete` | read `scripts/snapshot_gc.py::_delete_snapshots` + `principals.py::ensure_ready` | the cascade + txn idiom | **HAND-ROLLED** — REUSES `execute_transaction` (pinned by AST) + the snapshot_gc children-first cascade |
| `build_principal_store`/`build_principal_key_store` | `grep build_principal_store` (empty) + `lore_get_symbol(build_store)` | none exist; `build_store` is the sibling | **HAND-ROLLED** (design §F6) — read the SAME config accessors as `build_store` (pinned: resolution + same-db) |
| CLI `build_parser`/`main` | read `index/cli.py::{build_parser,main}` + `snapshot_gc.py` | the house idiom | **HAND-ROLLED** (clones the `build_parser`/`main(argv)->int` idiom; drops snapshot_gc's struck `--execute`) |

**External reuses CITED (not re-implemented):** `lorerunes.is_blank` (verify blank check —
mutation-pinned 17a) · `loremaster.index.records.sha512_hex` (the key hash — used in fixtures
the CLI-way) · `loremaster.store._txn.{run_query,execute_transaction,bootstrap_session}` (shared
retry, via the `_query` seam) · `PrincipalStore._row_to_principal` (verify's principal map —
mutation-pinned 17b) · `loremaster.search._sanitise_line` (CLI render — pinned 19, pending) ·
`PrincipalStore.get_by_email`/`set_status`/`create` (49 builds on the 48-B surface).

---

## AMBIGUITIES (ALL RULED by lead #5070 — retained for provenance; both readings + my pick)

**Status: 0 outstanding.** Every fork below was escalated with a recommendation and RULED
(see §LEAD RULINGS APPLIED for the resolution + the change made). Kept here so a future
reader sees the alternative that was considered and rejected, not just the survivor.

1. **`PrincipalStore.delete` return type.** Design §F2b floated `-> None` **or** `-> Principal`.
   Neither carries the key-count the CLI's audit line needs ("the N keys removed"). **Pick:
   `-> int`** (cascaded-key count) — the CLI already has the email from argv, so `int` gives it N
   directly. *Alt:* `-> Principal` (+ CLI counts via `list_for` first). Pins `TestDelete` assert
   `removed == N`; retarget if the operator prefers `-> Principal`.
2. **Unknown-principal exception taxonomy (mint/list_for).** Design §F7 is silent. **Pick: a
   UNION** `pytest.raises((PrincipalNotFoundError, PrincipalKeyStoreError))` — either satisfies
   "does not silently create an orphan key / conflate no-such-person with no-keys". `revoke` of a
   MISSING key (principal exists) is pinned firmly to `PrincipalKeyNotFoundError`. *Fork:* do you
   want mint/list_for to reuse `principals.PrincipalNotFoundError` or raise a `PrincipalKeyStoreError`?
3. **Pin 17b — where the shared principal-mapper lives.** Design §F3 says *"promote to a shared
   function (preferred) OR delegate to a PrincipalStore lookup"* — two mechanisms, two mutation
   targets. **Pick: verify routes its principal mapping THROUGH `PrincipalStore._row_to_principal`**
   (delegate/keep-anchor), so the pin monkeypatches that method and both stores redden. *Alt:* a
   promoted standalone `_map_principal_row` function → the pin retargets to it. I ruled the
   route-through form because it gives a concrete, builder-agnostic mutation target; flag if the
   builder prefers the promote form.
4. **Pin #19 — sanitiser seam on TERMINAL output (PENDING).** The P8d law is written for
   AGENT-facing MCP renders; this CLI is HUMAN-facing. The design doc (as read 2026-08-20) carries
   NO pin #19 and no explicit ruling. Per the brief ("pin it pending that ruling") I WROTE it and
   FLAGGED it PENDING in the test class header. **Fork for the sidecar/operator:** does terminal
   `list`/`list-keys` output warrant the `_sanitise_line` seam? If EXEMPT (with a reason), delete
   `TestRenderSafetyPendingRuling` and say so; if IN, keep it.
5. **CLI arg surface = `--email` flags, not positional.** Pins 3b/3c wrote "delete <email>"
   informally, but §F1 `set-expiry` uses `--email`. **Pick: `--email` flags for every keyed verb**
   (consistency + the descriptive-naming discipline + index/cli flag style); `set-expiry
   --at/--clear`; `mint-key`/`revoke-key` `--name`. Flag if the operator wants positional.
6. **CLI config-load mechanism (anthropic-key coupling).** `index/cli.py` uses `load_config`
   (resolves `anthropic.api_key_env` EAGERLY); `comms_cli` deliberately uses a creds-free surreal
   parse (it's read-only). The design §F6 is silent. My CLI tests set a dummy `ANTHROPIC` env var
   so they pass either way (observation, not pinned). **Fork:** should this admin CLI require the
   Anthropic key, or resolve the surreal block creds-free like comms_cli?
7. **Revoke idempotency shape.** Design §F7: *"a second revoke is a no-op or re-stamps — pick one
   and pin it."* **Pick:** a second revoke SUCCEEDS (no `PrincipalKeyNotFoundError` — the row still
   exists) and the key STAYS denied. I pinned that security-relevant invariant; I did NOT
   brittle-pin the exact `revoked_at` re-stamp instant (matches the design's literal
   `SET revoked_at = time::now() WHERE ...` — a re-stamp — without a flaky timing assertion).

---

## DEVIATIONS (prominent)

- **Sibling factories placement (design §F6 said "next to `build_store`" in `store/surreal.py`).**
  `store/surreal.py` is OUTSIDE my writable set. I placed `build_principal_store` in `principals.py`
  and `build_principal_key_store` in `principal_keys.py` — each module owns its factory (arguably a
  cleaner home than `store/surreal.py`, which builds the embedding `SurrealStore`). The DRY property
  the design cares about (they read the SAME config accessors as `build_store`) is pinned regardless
  of file (`TestSiblingStoreFactories`). If the operator wants them consolidated in `store/surreal.py`,
  that is a one-move relocation + a one-line retarget of the test imports.
- **principal_key DDL pins in a NEW `test_principal_keys_schema.py`** (cohesion with the key
  behaviour file), not appended to `test_principals_schema.py`. The brief listed both options ("new
  files ... + extend"); I extended `test_principals_store.py` for `set_expires`/`delete` and kept
  principal_key schema in the dedicated file. No pin lost.
- **§1.6 dirty-store pin is the NEW-TABLE form.** `principal_key` is brand-new (no field CHANGE to
  migrate), so the §1.6 shape here proves the slice RE-APPLIES to a POPULATED store (`ensure_ready`
  re-runs every boot) — a dirtied row survives + `UNIQUE(hash)` still fires. A true field-migration
  §1.6 pin will be meaningful only once `principal_key` grows an evolving field.

---

## Verification receipts

- **RED tail (per file, `-n auto -p no:cacheprovider`):** schema `27 failed, 4 passed`;
  keys-store `1 failed, 2 passed, 26 errors`; cli `22 failed, 13 passed`; store-ext (whole file)
  `4 failed, 17 passed, 4 errors`. Every RED verified BEHAVIOURAL: fixture/method
  `NotImplementedError`, empty-DDL clean assertion, or missing-verb parse error — **no
  ImportError, no collection error** (120 collected).
- **ruff:** clean on all 8 touched files.
- **mypy (`scripts/typecheck.sh`):** MY files clean (one intentional `# type: ignore[call-arg]`
  on the `extra='forbid'` negative-construction pin). The gate's overall RED is the PRE-EXISTING
  packet-39 adjudicated typecheck + lorerunes tests (8 files: `test_auth_*`, `test_*posture*`,
  `_auth_fixtures`, `lorerunes/tests/*`) — none touched by packet 49.
- **No regression:** `test_principals_schema.py` + `test_retry_seam.py` = **641 passed** (the
  retry-seam scan is unperturbed; principal schema green); the 48-B `PrincipalStore` tests =
  **17 passed**.

There are 8 files with pre-existing mypy errors unrelated to our present scope (the packet-39
adjudicated typecheck bound + lorerunes suites). Do you want to examine them more closely?
