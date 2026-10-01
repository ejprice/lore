brief-base v18 read · brief project v7 read

# REPORT-coldaudit-63c-i-a-4 — cold RE-CHECK audit of the 63c-i-a FINAL patch (`5f2d7c43…`)

## SUMMARY BLOCK
- **VERDICT: GO** for patch `5f2d7c43` against its spec (am-37 §5–§12, 58 am-14, fix3 D-1): prior NO-GO items all CLOSED or named residuals (§1); rulings hold by construction + receipt (§2); mutations (a)–(d) fire (§3; (b) PROOF HELD exactly); targeted 101 files **340 failed / 7205 passed, 0 orphan reds** (§5); gates RED_ORPHANED 0 on typecheck/ruff, ruff clean (§6). **Dirty store RAN**: after boot DDL every served migration count = a direct SELECT, idempotent on re-run; dump reaped + proven absent (§7).
- **state:** done-with-deviations.
- **deviations:** (1) the dump DB name is refused by `SurrealConfig.database` (D-1), so the REAL `principals.main` was driven with the YAML loader swapped for validated-config + `model_copy` (§7.1, §A.2). (2) "fresh deploy" = the server's own DDL generators applied before migrating; the pre-boot attempt is recorded (§7.3). (3) mutation (b)'s pytest leg waited ~25 min at the ≥20 GiB gate (no bypass); (b) was also proven by the pin's own derivation for all 4 wraps (§3.1). (4) (c) via fix3's surviving caller probe; (d) via probes + `mutation_proof.py`. (5) two declaration errors of mine ((a) a swap in one fates class; (d) an over-declared control cell), recorded, not re-declared (§3).
- **Packages considered:** none — no mechanism specified (a grader; probes reuse the SDK, `lorerunes.reclassify`, `scripts/mutation_proof.py`).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none (no production symbol introduced; instruments pasted §A).
- **Graded:** `7bf2304` + patch `5f2d7c4366d469e5c2a34d53aa235d6e` · HEAD-at-report: `5332d93` (2 docs-only commits past `7bf2304`: the blindreader-4 report + a lead report; `git diff --stat` touches only REPORT-*.md) · SAME code base.
- **New findings (none introduced by this patch except N-2):** D-1 MAJOR (packet 64 dump name vs config) · D-2 MAJOR (migrate on a pre-boot schema = opaque "unspecified rejection", no teaching precondition) · D-3 MAJOR ("see the server log" points at nothing in lore-adm; §11's D1 docstring relies on it) · D-4/N-1/N-3 MINOR served/doc prose · N-2 MINOR (4 wrapped methods' `Raises:` stale) · R-1 MINOR (a raising close masks the outcome) (§4, §7, §8).
- **decisions-needed:** (a) D-2 — teaching precondition in 63c-i-a, a 65 runbook line, or residual; (b) D-3 — fix the hint/handler now or residual; (c) D-1 → packet 64; (d) N-2 — fix in the commit or residual; (e) commit mechanics: only `scripts/pending_contracts.yaml` conflicts with #486's WIP (every other file incl. the harness hunk applies to the working tree; `--cached` applies cleanly).
- **receipt pointers:** §1 prior findings · §2 rulings · §3 mutations · §4 R-1/R-2 · §5 targeted run · §6 gates · §7 dirty store · §8 NL sweep · §R residuals · §A instruments.

## §0 Capability check / setup
- Spawned 2026-09-30 02:53:43Z; hard deadline 04:23Z.
- lore_comms: registered `coldaudit-63c-i-a-4` (session `63c-20260924`, role audit, cadence ≤20m) — OK.
- grep/rg are hook-blocked (#473) → every text sweep is `awk`. `lore_impact` caps covering tests at 15 (#518) and
  lore indexes the MAIN tree, not my scratch copy → covering tests derived by an AST scan over the patch's changed
  symbols (instrument `changed_symbols.py`, pasted §A). Fallback said out loud; known shape (#518/#507), nothing new to file.
- Scratch: `scripts/scratch_copy.sh <sp>/audit4` → `git reset --hard HEAD && git clean -fd` → `git status --short`
  printed nothing → patch md5 `5f2d7c4366d469e5c2a34d53aa235d6e` ✅ → `git apply` clean (18 files, +1992/−703) →
  `git diff --binary HEAD | md5sum` = `5f2d7c43…` (re-verified at test admission).
- `loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/250031ad-e2d1-4797-8c2b-7b7ce1854232/scratchpad/audit4/loremaster/loremaster/__init__.py` (inside the copy).
- HEAD at spawn: `7bf2304` (= `5089146` + one lead-report-only commit; nothing under `loremaster/`/`scripts/` moved).

## §7 THE REAL DIRTY STORE — `test_dump_20260930T001125Z_a072e4789558446bb05abce309b4a4fb` on `ws://127.0.0.1:18000` (ns `lore_test`)
Measured 2026-09-30 ~02:58–03:05Z on HEAD `7bf2304` + patch `5f2d7c43`. Port asserted `18000` before every call (instruments §A.2/§A.3). `:18500` never addressed.

### §7.0 Baseline (direct SELECT, before any lore-adm call)
agent 95 / memory 177 / message 316 / brief 26 — every row `scope IS NONE` AND `owner_principal IS NONE` on all four
(95/177/316/26 on each predicate); messages with an unsound sender (`sender.owner_principal IS NONE OR sender.scope IS NONE`) 316; `sender IS NONE` 0. Matches the brief's table counts.

### §7.1 FINDING D-1 (MAJOR, tooling/served) — lore-adm CANNOT be pointed at a restored dump through its config
`load_surreal_only_config` → `LoreConfig.surreal.database` pattern `^[a-z0-9][a-z0-9_]*$` REFUSES the name
`restore_prod_dump.py` mints (`test_dump_<UTC stamp with T/Z>_<hex>`): `ValidationError … string_pattern_mismatch`,
and because `load_surreal_only_config` sits OUTSIDE §11's handler (by ruling) it surfaces as a **traceback**, exit 1.
The packet-64 S2 instrument mints names the product's own config rejects, so "point a lore-adm config at THAT
database" is impossible as briefed. **What I did instead:** drove lore-adm's REAL entry `principals.main(argv)` with
exactly one substitution — `principals.load_surreal_only_config` replaced by a loader that validates the repo
`lore.yaml` normally and then `model_copy`s the surreal block to the dump coordinate (instrument §A.2). Every verb,
`_dispatch`, the §11 handler and every store run unmodified. CLASS: *every name `restore_prod_dump.py` can mint is
addressable by every lore config consumer* (domain: `DATABASE_NAME_PATTERN` vs `SurrealConfig.database`'s pattern).
Owner: packet 64 (the S2 instrument) — fix is either side (mint lowercase, or widen the pattern); not a 63c-i-a defect.

### §7.2 report-unmigrated BEFORE (served vs direct)
```
report-unmigrated --table agent:   unmigrated=95    (direct scope IS NONE: 95)  exit=0 + WARNING governed.unmigrated_rows …
report-unmigrated --table memory:  unmigrated=177   (177)                         exit=0
report-unmigrated --table message: unmigrated=316   (316)                         exit=0
report-unmigrated --table brief:   unmigrated=26    (26)                          exit=0
```

### §7.3 Operator bootstrap + migrate-governed — verbatim receipt lines
Before the operator exists (0 principals) — a refusal fate on the dirty DB, clean:
```
$ lore-adm migrate-governed --table agent
  stderr| lore-adm: migrate-governed --table agent REFUSED: cannot resolve THE operator principal to own the fleet's agents (0 principals, 0 admins) — provision a single operator principal (or a single admin) before migrating
  exit=1
$ lore-adm add --email operator@audit4.test --role admin --display-name audit4-operator      exit=0
$ lore-adm list →  operator@audit4.test  audit4-operator  active  admin  expires=-
```
**FIRST run on the dump AS RESTORED (no server boot) — the #107 shape:**
```
$ lore-adm migrate-governed --table agent
  stderr| governed.agent_backfill.rejected
  stderr| lore-adm: SurrealDB governed agent backfill rejected against 'ws://127.0.0.1:18000/rpc' (unspecified rejection); see the server log for the full engine detail
  exit=1
$ lore-adm migrate-governed --table memory
  stderr| governed.memory_backfill.rejected
  stderr| lore-adm: SurrealDB governed memory-scope backfill rejected against 'ws://127.0.0.1:18000/rpc' (unspecified rejection); see the server log for the full engine detail
  exit=1
$ lore-adm migrate-governed --table message
  stderr| lore-adm: migrate-governed --table message REFUSED: cannot migrate `message` rows before the `agent` table is migrated (95 un-migrated (NONE-scope) agent(s) remain) — … run migrate-governed for `agent` first
  exit=1
```
Engine detail, recovered only by attaching a log handler that prints extras (§A.3):
`LOG ERROR loremaster.principals governed.agent_backfill.rejected {'error_class': 'unspecified rejection', 'engine_error': "Found field 'owner_agent', but no such field exists for table 'agent'"}`.
`INFO FOR TABLE agent` on the dump: SCHEMAFULL pre-63 fields only (no `owner_agent` / `owner_principal` / `scope`).

**FINDING D-2 (MAJOR, spec-silent → operator/sidecar) — `migrate-governed` on a store whose schema predates the governed
columns is an opaque engine rejection, not a teaching refusal.** The creds-free CLI readies only the principal/keep
slices; the governed-column DDL (`generate_agent_ddl` / `generate_memory_ddl`-in-`generate_ddl` / `generate_message_ddl`)
is applied only by a SERVER boot. The verb's preconditions read `INFO FOR DB` and PASS (the table is defined — only its
columns are missing), so the operator gets "unspecified rejection". The ordering *new image boots → then migrate* is
nowhere checked or taught. Every test mints a virgin DB with the full DDL, so no pin can see it (the #107 fixture law).
CLASS: *every precondition the verb's writes need is measured and taught before the first write* (domain: the
columns each leg's UPDATE sets × `INFO FOR TABLE`). Not introduced by this patch (the legs predate it) and the
cutover runbook may already sequence boot-first — **spec-silent: the operator/sidecar rules** whether it is a
63c-i-a fix, a 65 runbook line, or a residual.

**FINDING D-3 (MAJOR, served English / trust) — "see the server log for the full engine detail" points at nothing in a
CLI process.** In lore-adm the logger has no configured handler, so Python's last-resort handler prints only the
message (`governed.agent_backfill.rejected`) and DROPS the `extra` carrying `engine_error`. The operator is told the
detail is in a log that does not exist; the only way I recovered it was by instrumenting the process. §11 item 1's
FR-2-D1 re-ruling explicitly relies on this hint ("D1's INTENT survives in the stderr line: … driver label +
server-log hint"), so after §11 MORE faults route to this dead pointer. CLASS: *every served pointer resolves to a
surface the consumer can open* (Leg 1 scope diff: "the server log" ≠ what exists in lore-adm). Owner: 63c-i-a (§11's
surface) or the `_SERVER_LOG_HINT` owner; fix shape (not mine to build): lore-adm configures a stderr handler that
renders `engine_error`, or the CLI's hint names where the detail is.

### §7.4 After the "fresh deploy" boot step, migrate-governed per table (verbatim) + idempotence
Boot step simulated by applying exactly the server's DDL generators to the dump DB (`generate_ddl(dim=2048)` 175
statements, `generate_agent_ddl` 24, `generate_message_ddl` 28, `generate_brief_ddl` 14, `generate_audit_ddl` 11,
`generate_task_ddl` 15, `generate_finding_ddl` 16 — **0 errors on the dirty store**; §A.4).
```
$ lore-adm migrate-governed --table agent
  stdout| migrate-governed --table agent: scanned=95 backfilled=95 already_migrated=0 unsound_sender_messages=None
  exit=0
$ lore-adm migrate-governed --table memory
  stdout| migrate-governed --table memory: scanned=177 backfilled=177 already_migrated=0 unsound_sender_messages=None
  exit=0
$ lore-adm migrate-governed --table message
  stdout| migrate-governed --table message: scanned=316 backfilled=316 already_migrated=0 unsound_sender_messages=0
  exit=0
$ lore-adm migrate-governed --table brief
  stderr| lore-adm: migrate-governed --table brief REFUSED: migrate-governed does not yet migrate `brief` — its backfill lands at packet 63c-ii (today: `memory`, `agent` and `message`); the store's governed-table preconditions were read and passed, and nothing was written
  exit=1
=== RE-RUN
agent:   scanned=95  backfilled=0 already_migrated=95  unsound_sender_messages=None   exit=0
memory:  scanned=177 backfilled=0 already_migrated=177 unsound_sender_messages=None   exit=0
message: scanned=316 backfilled=0 already_migrated=316 unsound_sender_messages=0      exit=0
brief:   REFUSED (same line)                                                          exit=1
```
**Served vs direct (§A.3 `dq.py`, verbatim values):**
| table | served scanned / backfilled / already | direct count / scope NONE after / owner NONE after | other invariants |
|---|---|---|---|
| agent | 95 / 95 / 0 → re-run 95 / 0 / 95 | 95 / 0 / 0 | one group: owner `principal:rgbouzm1kdt7ub3q1w88` (the operator) × scope `keep:01M3R42KB0CQ8QQZQR2HH73D2Y` n=95; `owner_agent != id` 0 (CONTROL `owner_agent = id` 95) |
| memory | 177 / 177 / 0 → 177 / 0 / 177 | 177 / 0 / (owner NONE by design: 177) | one group: owner_principal NONE, owner_agent NONE, scope = the project keep, n=177 |
| message | 316 / 316 / 0 → 316 / 0 / 316; `unsound_sender_messages=0` | 316 / 0 / — ; `scope IS NONE AND owner_principal IS NONE` = 0 (= the field) | one group owner = operator × project keep n=316; `owner_agent != sender` 0 (CONTROL `= sender` 316); `owner_principal != sender.owner_principal` 0 |
| brief | refused, nothing written | scope NONE still 26 | — |
Project keep: exactly ONE row (`key project:lore`, type project, keeper = the operator, name `lore`) and one `member_of`
— the failed pre-boot memory run did not double-mint. `unsound_sender_messages=None` on agent/memory is rendered
explicitly (§10.2) ✓; `=0` on message is the measured leftover ✓.

### §7.5 report-unmigrated AFTER + the fault fate on the dirty DB (verbatim)
```
report-unmigrated --table agent: unmigrated=0     exit=0
report-unmigrated --table memory: unmigrated=0    exit=0
report-unmigrated --table message: unmigrated=0   exit=0
LOG WARNING … governed.unmigrated_rows: 26 brief row(s) carry a NONE scope (member-invisible until migrated) — run `lore-adm migrate-governed --table brief` to backfill
report-unmigrated --table brief: unmigrated=26    exit=0
$ lore-adm delete --email operator@audit4.test
  stderr| lore-adm: cannot delete principal 'operator@audit4.test': they keep 1 keep(s) (keep:01M3R42KB0CQ8QQZQR2HH73D2Y) — reassign the keeper (lore-adm set-keeper) or delete the keep (lore-adm delete-keep) first
  exit=1
$ lore-adm list → operator@audit4.test  audit4-operator  active  admin  expires=-      (state unchanged; direct count(principal)=1)
$ lore-adm delete --email nobody@audit4.test
  stderr| lore-adm: no principal with email 'nobody@audit4.test'
  exit=1
```
The §12 whole-body `delete` wrap passes the typed refusals through BY CLASS (`PrincipalHasKeepsError`,
`PrincipalNotFoundError` are `PrincipalStoreError` subclasses, NOT `SurrealStoreError` — MRO printed §2.3), reaching
§11's one handler: exit 1, one `lore-adm:` line, no traceback.

**FINDING D-4 (MINOR, served English)** — the brief alarm's remedy teaches a verb that refuses: `report-unmigrated
--table brief` → "run `lore-adm migrate-governed --table brief` to backfill", and that verb answers "does not yet
migrate `brief` … lands at packet 63c-ii". A consumer following the served instruction fails. CLASS: *a served remedy
names a verb that accepts the input* (domain: `_MIGRATE_VALID_TABLES` minus the legs that actually run). Owner 63c-ii
(closes by construction when brief's leg lands) — or a one-line derived remedy now.

## §1 Prior findings — coldaudit-3 NO-GO items and blindreader-3 findings (each by code read + receipt in the copy)
Probe instrument §A.5 (plain Python over the build's `_txn` / `governed` / `principals`; each negative paired with a control).
| # | status | receipt |
|---|---|---|
| F-C1 / F-6 / D-5 (degenerate all-cascade selects a false root) | **CLOSED** | `_is_domain_cascade_notice` = `isinstance(typed, QueryError) and (typed.is_not_executed or typed.is_cancelled)` (the am-37 §7 ruling, verbatim). `[Cancelled, NotExecuted]` → index **1** (LAST); `[NotExec, Internal, Cancelled, NotExec]` → 1; `[TimedOut, NotExecuted]` → **0** (TimedOut substantive); GARBAGE-TEXT `[NotExec 'zzz', Cancelled 'qqq', NotExec 'yyy']` → 2 (LAST, decided by kind); CONTROL garbage-text substantive `[NotExec, Internal 'qqq', NotExec]` → 1 |
| F-C11 (§5 spelling reddens the a28c text-reader pin) | **CLOSED** | no `in`/`==` compare in the predicate (SDK attribute access + `or`); the a28c exact-set pin is in my targeted set and its file has 0 reds (§5) |
| F-C2 / M-2 (`table_defined` defaults `True`) | **CLOSED** | `dataclasses.fields(MigrateGovernedResult)['table_defined'].default` = `MISSING` (no default); ONE derivation `table_defined = table in preconditions.defined_tables` in `_migrate_governed_resolved`; the invalid-table path passes `None`. Live on the dirty store the agent/memory/message receipts rendered for a DEFINED table (§7.4) |
| F-C3 / F-9 (mixed-owner label) | **CLOSED** | mixed branch now renders `others: {distinct_owner_principals} distinct principal(s) in all, the operator among them (a sample of the others: …)` — one integer, labelled as the total. `foreign` keeps "`N other principal(s) (first K named …)`", as §6 ruled correct |
| F-C4 (fence runs survive `sanitise_line`) | **RESIDUAL (BOUND)** — am-37 §7: owner #34's promotion; trigger an MCP-served principal-id render | not re-probed (bound unchanged, no code moved) |
| F-C5 (patch does not apply onto the main tree) | **STILL TRUE — commit mechanics, planned** | `git apply --check <patch>` in the main tree: `error: patch failed: scripts/pending_contracts.yaml:287` (the #486 WIP); `git apply --check --cached` → OK. Lead anchor v8 plans `--cached`. **See §6 note: `test_surreal_harness.py` is in BOTH the patch and the #486 WIP.** |
| F-C6 (FK-B1 pin 1 is decoration) | **RESIDUAL** — am-37 §W row 4 (next `_txn` contract) | unchanged |
| F-C7 (keeps `get_or_create_keyed` Raises stale) | **CLOSED** | `keeps.py` Raises now: "The CAS door is NARROW … ONLY a `TxnUniqueViolationError` from the CREATE is caught … Every other `SurrealStoreError` … is never re-read" |
| F-C8 (malformed `cause` escapes `parse_query_error`) | **CLOSED** | `_SDK_PARSE_FAILURES = (AttributeError, TypeError, RecursionError)`; an ERR entry with `cause: 12345` → `typed=None` + WARNING `store.transaction.untypeable_err_entry`, no raise; CONTROL a dict-shaped cause still parses |
| F-C9 (`last_conflict_cause` comment over-generalises) | **CLOSED** | the comment now enumerates every `RetryableConflictSignal()` raise site and names the ONE unchained raise (`_run_verified_transaction._attempt`) with why |
| F-C10 (transport `{error}` interpolation) | **RESIDUAL (BOUND)** — am-37 §7, trigger: a transport-kind message carrying a bound value | unchanged |
| M-1 (store reference stale) | **CLOSED** | `docs/reference/surrealdb-31-capabilities.md`: "#111 ANSWERED — trigger MET (2026-09-27)"; cascade section cites `_txn._is_domain_cascade_notice` and "the SDK's OWN" predicate; the §6-item-3 claim carries "*this item previously said there was 'no typed alternative'*"; the summary line is marked superseded 2026-09-29. No `_CASCADE_KINDS` citation survives (awk: 0 hits) |
| F-4 / F-5 (stale `_txn` docstrings) | **CLOSED** | awk for `marker-less` / `text is non-empty` / `keys off of`: 0 hits; the one `can be retried` hit in a docstring says it is "logged EVIDENCE" |
| F-8 (stale `last_conflict` on RPC-level conflict) | **CLOSED** | `_attempt` begins `nonlocal last_conflict; last_conflict = None` |
| F-10 (unsound sender rows silent) | **CLOSED** | field `unsound_sender_messages` measured + rendered (live: `=0` on the message receipt after agent migration, `=None` rendered explicitly on agent/memory, §7.4) |
| F-12 (bare `SurrealStoreError` escapes the migrate dispatcher; `_scope_count` tolerant) | **CLOSED (superseded by §11)** | the one handler catches `SurrealStoreError`; `_scope_count` → `governed.group_all_count` (fail-closed) — §2 |
| F-13 / F-14 / F-16 / fixture drift | **RESIDUAL** as ruled am-37 §6 (triggers there) | unchanged |
| coldaudit-3 §10 R-1 (real-dump leg unexecuted) | **CLOSED** by this audit's §7 (restored dump migrated, compared, reaped). R-2..R-10 map onto the rows above (F-C6, F-C4, F-C5, F-C7, F-C8, F-C9, F-C10) or were instrument/run notes of that audit | — |
| F-A / F-B / F-11 / F-15 / F-17 | confirmed-fixes / NOTEs (no action owed) | — |

## §2 Rulings by construction (code read + receipt; the builder's tables were not used as evidence)
### §2.1 am-37 §11 — ONE lore-adm handler
AST over `principals.py` (instrument §A.6, `check_dispatch.py`):
```
_dispatch handlers: ['(PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError, ValueError)']
_dispatch_migrate_governed handlers: []
_dispatch_report_unmigrated handlers: []
_dispatch_keep handlers: []
ROW principals.py::_dispatch  catches='(PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError, ValueError)'
EQUAL row.catches == ast.unparse(handler.type): True
```
Tuple order is exactly §11 item 3's. `_require_config` + `load_surreal_only_config` sit OUTSIDE the `try` (ruled). The only
`return` in the handler is `1`. The `_dispatch_migrate_governed` / `_dispatch_report_unmigrated` rows are gone from
`REGISTERED_FATES` (only `principals.py::_dispatch` remains under `principals.py::`). `_dispatch_keep`'s D1 paragraph is
rewritten to the re-ruling. Behaviour: mutation (a) (§3) + the generated pin (34 cells) + the live dirty-store fates (§7).

### §2.2 am-37 §12 — four wraps; `delete` whole-body; refusals pass by class
- `PrincipalStore.set_status` — UPDATE inside `wrap_store_rejection(PrincipalStoreError, "could not set status of principal {email!r} to {status!r}")` ✓
- `PrincipalStore.set_expires` — ONE wrap enclosing BOTH branches' UPDATEs ✓
- `PrincipalStore.delete` — ONE wrap from `get_by_email` THROUGH `execute_transaction` (whole body) ✓
- `PrincipalKeyStore.revoke` — the UPDATE wrapped in `PrincipalKeyStoreError`; `_require_principal_id` (a read) outside, as §12's domain says ✓
- Passthrough by class (MRO printed live): `PrincipalStoreError` / `PrincipalHasKeepsError` / `PrincipalOwnsGovernedRowsError` /
  `PrincipalNotFoundError` / `PrincipalKeyStoreError` / `KeepStoreError` are all `RuntimeError`s, `issubclass(…, SurrealStoreError)` False;
  `lorerunes.reclassify` re-raises passthrough first, translates only `catch`, lets everything else propagate (source read).
  Live on the dirty store: `delete` of a keeper → `PrincipalHasKeepsError` text, exit 1; unknown email → `PrincipalNotFoundError` text (§7.5).
- Mutation (b) (strip one wrap): §3.

### §2.3 am-37 §10 — fail-closed readers, alarm fate, `None` rendered
- (a) `PrincipalStore.delete`'s owned count = `governed.group_all_count(…, noun="governed owned-row count")`, inside the §12 wrap → a malformed answer is `SurrealStoreError` → `PrincipalStoreError("could not delete …")`; the delete does not proceed ✓ (code read; fix5 §2's probe; mutation (c) §3).
- (b) `report_unmigrated_governed_rows` reads through `group_all_count` → a malformed answer raises the class a rejected count raises ✓. Its ONLY production caller is the `report-unmigrated` verb (AST/awk: no boot caller) — so the "boot alarm" never runs at boot (see §8 N-1).
- (c) receipt renders `unsound_sender_messages=None` explicitly on agent/memory (live, §7.4) ✓.

### §2.4 am-37 §8.3 — ONE `group_all_count`
AST over every workspace member: ONE definition `governed.group_all_count`; callers `principals.py` ×3 (`_scope_count`, the
message leftover read, `delete`'s owned count) + `governed.report_unmigrated_governed_rows` = the 4 its docstring names ✓.
Other GROUP ALL readers remain — `messages._extract_group_count`, `findings._extract_group_count`, `tasks._extract_group_count`
(tolerant) and **`PrincipalStore.delete`'s own `cascaded` key-count read** (`int(count_rows[0].get("count", 0)) if count_rows else 0`,
tolerant, inline, in 63c's own file) — all routed to the 64b §DRY step by §10.1 (the `cascaded` count is named there). Residual, owned.

### §2.5 58 am-14 — every per-path registry lookup routes through `entries_for`
`PendingContractRegistry.entries_for(path)` is the one per-path lookup; `entry_for` is deleted. Per-path readers:
`partition_mypy` (`any(entry.admits(error) for _b, entry in entries_for(error.path))`) and the D-1 unsymboled leg
(`path_symbols` over `entries_for(entry.path)`) ✓. `partition_pytest` reads `registered_paths` (a path UNION — already
per-path-union, not first-match) ✓. The am-14 §1 TDD pair landed (`test_shared_path_error_is_expected_when_ANY_entry_admits_it`,
`…_naming_neither_entrys_symbol_is_unexpected`). **The D-1 site has NO pin** (fix3 deviation 1): am-37 §10.3 said it rides
with the am-14 tests; it did not → residual per the lead anchor ("the D-1 gate pin → the next gate contract"). Mutation (d): §3.

## §3 Mutation proofs (scratch `mut4` = HEAD + `5f2d7c43`, `loremaster.__file__` inside `mut4`; `cp -a` backups `mutbak_*`; every restore `cmp`-verified; `mut4` re-md5 `5f2d7c43…` after the last one)
| # | mutation (landing evidence) | instrument | declared (before the run) | observed | verdict |
|---|---|---|---|---|---|
| (a) | drop `SurrealStoreError` from `_dispatch`'s tuple (anchor matched exactly once; `mutation_proof.py` "mutation LANDED") | `scripts/mutation_proof.py` over `test_principals_cli.py` `test_exhaustion_fates.py` `test_keeps_cli.py` `test_keep_remediation_cli_61.py`; declared set md5 `71d28cd9` (37 ids, from `--collect-only`) | 17× `test_a_domain_rejection_in_ensure_ready…[verb]`, 17× `test_CONTROL_a_transport_fault…[verb]`, `test_report_unmigrated_on_an_absent_table_fails_loud…`, fates `…every_non_derived_site_has_a_row_and_every_row_a_site`, fates `…every_row_is_matched_to_ITS_site_by_the_caught_expression` | **37 failed / 140 passed**. 36 of 37 declared RED. Two-way diff: `…matched_to_ITS_site…` STAYED GREEN; `…evidence_that_HOLDS` went RED undeclared | **HOLDS.** Every generated-pin cell (34) and the absent-table pin fire. The one swap is MY declaration error inside ONE fates class: a row whose site vanished is unmatched, so the match-by-expression test does not iterate it, and the evidence test is the one that reds. The registry still reds. `mutation_proof` exit 4 records that mismatch honestly. Restored byte-exact (`ac7ffd09…`) |
| (b) | strip `set_status`'s §12 wrap (`with wrap_store_rejection(…):` → `if True:`) | `mutation_proof.py` over `test_engine_rejection_seam.py` `test_principals_cli.py`; declared set `declB.txt` (6 ids) | `…write_boundary_sits_inside_its_stores_wrap[principal::set_status]`, `…raw_store_error_surfaces_as_the_domain_error[principal-set_status]`, LAYER1 + LAYER2 `[principal-set_status]`, `routed_set_equals_the_invocation_map[principal]`, `routed_set_equals_the_known_wrapping_verbs[principal]` | **6 failed / 186 passed; `PROOF HELD — the declared RED set fired EXACTLY` (exit 0)** — admitted ~03:29Z once MemAvailable reached 25 GiB | **HOLDS** (plus §3.1: all four wraps, each by name). Restored byte-exact (`ac7ffd09…`) |
| (c) | `group_all_count` empty branch `return 0` → `return 7` (anchor count 1; "MUTATED (landed)") | fix3's surviving probe `probe_group_all_r2.py` (md5 `e3bfa3c4`; real caller bodies, only the driver seams faked), run unmutated → mutated → restored | every one of the 4 callers moves | unmutated: `_scope_count=0`, message `unsound_sender_messages=0`, `delete` PROCEEDED (executed=True), `report_unmigrated=0`. **mutated: `_scope_count=7`, `unsound_sender_messages=7`, `delete` → `PrincipalOwnsGovernedRowsError … they own 7` (executed=False), `report_unmigrated=7`** | **HOLDS — all four callers move; one policy.** The probe's Part B (fates) crashes on BOTH states because it expects `_dispatch_report_unmigrated` to catch (pre-§11); that is the probe predating §11, not a defect. Suite-level bound unchanged from fix3: no suite pin asserts the message leftover's value. Restored byte-exact |
| (d) | `entries_for` → first-match (`[...][:1]`; anchor count 1) | `probe_am14.py` (am-14 §1 shape) + fixup's `probe_shared_unsymboled.py` (D-1), module path printed = `mut4/scripts/pending_contract_gate.py` | the second bound's symbol turns orphan; the control stays unchanged; the D-1 shared path raises a false self-destruct | unmutated: `SECOND-bound symbol: expected=1 unexpected=0` · `CONTROL: expected=0 unexpected=1` · D-1 SHARED: no finding. **mutated: `SECOND-bound symbol: expected=0 unexpected=1`** · CONTROL unchanged · D-1 SHARED: `SELF-DESTRUCT: … declares 1 unsymboled 'attr-defined' error(s); 2 observed` | **HOLDS — both per-path readers move with the ONE lookup.** PLUS `mutation_proof.py` over `scripts/test_pending_contract_gate.py` (declared from `--collect-only`: both params of `test_shared_path_error_is_expected_when_ANY_entry_admits_it`): **1 failed / 43 passed**. `[named-by-second-entry]` RED ✓. `[named-by-first-entry]` STAYED GREEN (exit 4). That was MY over-declaration: first-match still admits a symbol owned by the FIRST entry, so that cell is the pin's own built-in control. I did NOT re-declare after seeing the output. Restored byte-exact (`1dcdfadf…`) |

## §4 fix4 R-1 / R-2 — probed (instrument §A.7, `probe_r12.py`: scripted fake stores, real `principals.main`)
```
[R1-control] rc=1  stderr='lore-adm: (assert violation); see the server log'
   events=[build_principal, build_key, build_keep, principal.ensure_ready, keep.close, key.close, principal.close]
[R1a close raises SurrealConnectionError] rc=1  stderr='lore-adm: socket gone'
   events=[… principal.ensure_ready, keep.close]                     ← original fault NOT printed; key/principal closes SKIPPED
[R1b close raises OSError] rc=RAISED OSError: EBADF (context=TxnDomainRejectionError)   ← traceback, original only as __context__
[R1c success + close raises] rc=1  stderr='lore-adm: socket gone'   ← the verb SUCCEEDED (all ensure_ready ran), exit 1
[R2a key factory ValueError] rc=1  stderr='lore-adm: bad coordinate'  events=[build_principal, build_key]
[R2b keep factory TypeError (out-of-tuple)] rc=RAISED TypeError: programming defect
```
- **R-1 — ACCEPTABLE per §11, with a named MINOR residual.** §11 item 4(i) prescribes the nested `try/finally`
  inside the handler. The property "never a traceback, never a success" holds for every in-tuple fault, including one
  raised by `close()` (R1a, R1c exit 1). Out-of-tuple (R1b) tracebacks, as §11 designates for programming defects. The
  cost: (i) an in-tuple close fault REPLACES the operator's view of the original fault (R1a prints `socket gone`, never
  the assert violation). (ii) A successful mutating verb whose close fails exits 1 (R1c), so a script may retry a
  write that landed. (iii) A raising close skips the remaining closes. Only (iii) is structurally the same as HEAD's
  sequential `finally`, and it is harmless in a one-shot CLI process. Before §11, (i) printed the original first and
  then tracebacked, and (ii) tracebacked. No pin exists. CLASS: *a teardown fault never masks the verb's own outcome*.
  Owner: the next lore-adm-touching contract. Trigger: a close/teardown fault observed in the field. A fix (not mine
  to build) would suppress-and-log teardown faults via `contextlib.AsyncExitStack` with a teardown-error policy.
- **R-2 — ACCEPTABLE (consistent with §11 item 1's property).** Factory faults inside the tuple are laundered; outside
  it they traceback. No leak: the factories are lazy (`PrincipalStore.__init__`: "Does not open any connection yet"),
  so a stranded, un-closed store object holds no socket. No pin; none needed beyond §11's generated pin's reach
  (its injection point is `ensure_ready`, one step later).

## §5 Targeted test run on the final build (NO full suite — the packet's full suite ran in coldaudit-3, `535677a`)
- **Set derivation (declared before the run, md5 `a7795901`, 101 files):**
  - my AST scan: 86 changed production symbols across the patch's 8 production/script files → 86 test files referencing any
    of them by name (Name / Attribute / import alias / string constant), instrument §A.1;
  - ∪ fix3's 74 (`declared_fix3.txt` md5 `00b6f268` ✓), fix4's 10 (`declared_files.txt`), fix5's 21 (`fix5-declared-files.txt` md5 `a3762004` ✓);
  - ∪ `scripts/test_pending_contract_gate.py` (added BY HAND: `scripts/` is outside lore's graph, #507);
  - ∪ the tree-scanning structural pins: `test_retry_seam.py`, `test_exhaustion_fates.py`, `test_mcp_server.py`,
    `test_render_seam_pins.py`, `test_render_slot_inventory.py`, `test_render.py`, `test_comms_render_architecture.py`,
    `test_link5_render_containment.py`, `test_memory_f5_registration_63b_ib.py`, `test_render_mypy_layer{,_optout}.py`.
- Command: `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --no-sync --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider --junitxml=… $(cat declared_audit4.txt)`.
  Admitted 02:55:51Z at 24 GiB, tree md5 `5f2d7c43` at admission. No cap kill.
- **Result: `340 failed, 7205 passed, 19 skipped, 3 xfailed, 5 warnings in 687.18s`** (junit: 7205 pass / 340 failure / 22 skip).
  No collection errors. The `ImportError: cannot import name 'arm_finding_identity'` lines are in-test failures inside
  64b-i-owned files (`arm_finding_identity` is a 64b-i pending symbol).
- **Ownership of every red, against the BUILD's `scripts/pending_contracts.yaml`** (loaded by the gate's own
  `PendingContractRegistry`; bounds present: `packet-58-contract`, `packet-64b-i-contract` — `packet-63c-i-a-a28-contract`
  is DELETED by the patch): **packet-64b-i 272 · packet-58 61 · both 7 · ORPHAN 0** (19 red files). No red was owned by the
  deleted a28 entry. The totals track fix3's measured base/build pattern (`64b-i 272 / 58 60 / both 7` at fix3 r2). The
  one-red difference in 58's column comes from the larger set I ran. It does not come from an orphan.

- **File-level ownership masks per-test causes (the F-15 window), so each red in a file that 63c ALSO touches was read by
  its CAUSE, not its file** (junit messages, §5 run):
  - 63c-owned pin files carry **0 reds**: `test_principals_cli` 85/0 · `test_engine_rejection_seam` 107/0 ·
    `test_retry_seam` 678/0 · `test_pending_contract_gate` 44/0 · `test_keeps_cli` 49/0 · `test_keep_remediation_cli_61`
    15/0 · `test_fixwave_a28c_63c_i_a` 333/0 · `test_render_seam_pins` 27/0 · `test_surreal_harness` 56/0.
  - `test_exhaustion_fates` 1 red, `…evidence_that_HOLDS`: all **6** named sites are `store/lease.py` (58's lease
    `error_class` rider, per the 58 entry's own prose). The `server.py::_comms_register` row the registry prose assigns to
    63c-i-a is NOT among them.
  - `test_reanchor_58_r4_state`: the `agents.py` RS-5 leg (the registry prose: "63c-i-a's, discharged by its build") is
    **GREEN**. Its reds are `findings` (`FindingLedger.report() … 'title'`, 64b-i) and `tasks._reanchor_stragglers` (58).
  - `test_mcp_server` 28 reds: 13× `AppContext.findings() got an unexpected keyword argument`, 12× ImportError, 3× the
    same TypeError asserted. The only ImportError symbol across ALL 340 reds is `arm_finding_identity` (59×), a 64b-i
    pending symbol.

## §6 Gates (in the `audit4` copy, tree md5 `5f2d7c43`)
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` → exit 1, verbatim (owner prose elided `[…]`):
```
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (owner: packet 58 […]) · packet-64b-i-contract (owner: packet 64b-i […])
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it would pass.
CURRENCY   : FAIL — claimed but never run: pytest
```
  **RED_ORPHANED legs among those run: 0** (typecheck RED_ADJUDICATED, ruff GREEN). The FAIL is the by-design `--legs`
  NOT_RUN of pytest, identical to fix5 §5. **Observation (gate UX, not 63c):** under `--legs` the render labels the
  deliberately-unselected pytest leg "ORPHAN" and exits 1, so a reader must know the `--legs` convention to read it as
  green-for-scope. CLAUDE.md's "show RED_ORPHANED 0" instruction and this render disagree in vocabulary. Owner: the gate
  (packet 58 / gates.yaml). It is surfaced here, not graded.
- `uv run ruff check .` → `All checks passed!` (exit 0).
- `./scripts/typecheck.sh` → lorerunes / lorescribe / loresigil / skills / docs/eval OK; `loremaster FAILED: Found 82
  errors in 31 files (checked 316 source files)`; `scripts FAILED: 1 error` (`scripts/test_forgery_door_sweep.py:42 …
  "SupersedeResult"`, a 58 pending symbol; that file is registered); shellcheck OK. 82 + 1 = 83 = the currency's
  RED_ADJUDICATED count. **Every error file is a test file** (awk over the error paths excluding `tests/` and
  `scripts/test_`: empty), so there are 0 errors in production files.

## §8 Natural-language surfaces (P8d) — bare awk sweep, every hit adjudicated individually
Sweep: `git diff -U0 HEAD` over `loremaster/loremaster`, `scripts/pending_contract_gate.py` and `docs`, ADDED lines only,
matching the bare patterns `_dispatch_keep|nothing was migrated|[Rr]aises|SurrealStoreError|D1|server log|see the server|_CASCADE_KIND|laundered|catches NOTHING|catch`
(no anchors) → 44 hits (`nl_sweep.txt`). Each hit below carries a verdict: OK = matches the code as built.
| file:line (at `5f2d7c43`) | text (abridged) | verdict |
|---|---|---|
| docs/reference/surrealdb-31-capabilities.md:454 | "a doc teaching a retired mechanism, which no gate will ever catch" (followed by the SUPERSEDED 2026-09-29 header) | OK — the superseded block is marked inline |
| governed.py:30 | import `SurrealStoreError` | OK (import) |
| governed.py:130 | "A contradiction raises (a pydantic `ValidationError`)" | OK (model validator) |
| governed.py:686 | `group_all_count` "raises SurrealStoreError naming the read" | OK (body raises exactly that) |
| governed.py:702–703 | Raises: SurrealStoreError — not empty list / int count | OK |
| governed.py:712 | `raise SurrealStoreError(` | OK (code) |
| governed.py:739–740 | "raises the SAME class `run_query` raises when the engine REJECTS this count … the `report-unmigrated` verb: stderr + exit 1" | OK — true since §11 (the fate is `_dispatch`'s handler, not a verb-local catch; the comment names the verb's observable fate, which holds) |
| keeps.py:548 | "Every other `SurrealStoreError` from the CREATE … is never re-read" | OK (F-C7 fix; matches the narrowed catch) |
| principals.py:770–771 | "(`PrincipalHasKeepsError` / `PrincipalOwnsGovernedRowsError`) are not SurrealStoreError, so the seam re-raises them untouched" | OK — MRO + `reclassify` source (§2.2) + live (§7.5) |
| principals.py:814–815 | owned count via the ONE fail-closed reader; a malformed answer raises SurrealStoreError → the §12 wrap → PrincipalStoreError | OK (code + fix5 probe) |
| principals.py:1157 | "the precondition read raises rather than answer without it" | OK (`_agent_migration_preconditions` raises on a non-dict INFO) |
| principals.py:1470 | `_scope_count`: wrong-shaped answer raises, "via `group_all_count`" | OK (it calls it; mutation (c) moved it) |
| principals.py:1537 | `_governed_select`: "a non-list answer RAISES … — the ONE fail-closed policy `group_all_count` applies" | **NOTE** — `_governed_select` is a ROWS reader with its own `isinstance(rows, list)` check, not a caller of `group_all_count`. The prose reads as if it shares that function. Same policy family, separate check. Harmless; flagged under the routing-is-not-sharing lens |
| principals.py:1551–1552 | `_governed_select`: "… not a list of rows — nothing was migrated" | OK — `_governed_select`'s only callers are inside `_agent_migration_preconditions` (awk: lines in the preconditions body), which runs before any write |
| principals.py:1598–1600 | INFO FOR DB malformed → "preconditions cannot be read, so nothing was migrated" | OK (precondition, pre-write) |
| principals.py:2130 | keep remediation verbs: "a KeepStoreError is laundered by `_dispatch`'s ONE lore-adm handler (am-37 §11)" | OK |
| principals.py:2273 | create-keep ValueError "laundered by `_dispatch`" | OK |
| principals.py:2320 | set-keeper ghost → "laundered by `_dispatch`" | OK |
| principals.py:2331 | delete-keep ghost → "laundered by `_dispatch`" | OK |
| principals.py:2368 | "none of them catches. The handler's only return is `1`" | OK (AST §2.1) |
| principals.py:2388 | `return await _dispatch_keep(args, config)` | OK (code) |
| principals.py:2415 | `SurrealStoreError,` (the tuple) | OK |
| principals.py:2518–2520 | `_dispatch_keep`: "This frame catches NOTHING … propagates to `_dispatch`'s ONE lore-adm handler" | OK (AST: 0 handlers) |
| principals.py:2525–2526 | "FR-2 D1 is RE-RULED (am-37 §11 item 1)" | OK — matches §11 item 1 |
| principals.py:2531–2532 | "D1's INTENT survives in the stderr line: an un-wrapped SurrealStoreError prints its driver label + server-log hint" | **FALSE IN EFFECT (D-3)** — the hint exists, but in lore-adm "the server log" holds nothing the operator can read (§7.3). The sentence claims an intent-preservation that depends on a dead pointer |
| _txn.py:235 | `TxnUniqueViolationError` "A SUBCLASS of TxnDomainRejectionError (every existing `except` keeps catching it)" | OK |
| _txn.py:748 | raw_result "must never be interpolated into a SurrealStoreError message" | OK (domain branch hygienic — coldaudit-3 §4) |
| _txn.py:1109 | "… a hint pointing at a server log that holds nothing" | OK, and **corroborates D-3**: the module's own comment names the dead-pointer shape (in the retry-exhaustion context) |
| _txn.py:1120 | "not by catching a raise, so it raises the signal BARE" | OK (F-C9 fix) |
| _txn.py:1388–1391 | `_raise_attempt_failure` Raises: Fate 1/2/3 | OK |
| _txn.py:1531 | "on an RPC-level error `_txn_query_raw` raises — is retried" | OK |
| _txn.py:1747, 1755 | `_txn_query_raw`: domain kinds keep the connection; Raises SurrealStoreError (domain kind) | OK (coldaudit-3 F-11 receipts; unchanged since) |

**The sweep over ADDED lines cannot see UNCHANGED context lines whose meaning the patch changed.** I read those directly:
- **N-2 (MINOR, P8d class — CONFIRMED by reading):** the four §12-wrapped methods' `Raises:` sections were NOT
  updated. `PrincipalStore.set_status` lists only `ValueError`, `PrincipalNotFoundError`. `set_expires` lists only
  `PrincipalNotFoundError`. `delete` lists `PrincipalNotFoundError`, `PrincipalHasKeepsError`,
  `PrincipalOwnsGovernedRowsError`. `PrincipalKeyStore.revoke` lists `PrincipalNotFoundError`,
  `PrincipalKeyNotFoundError`. None names the new `PrincipalStoreError("could not …")` /
  `PrincipalKeyStoreError("could not revoke …")` that the wrap now raises on a store rejection. The house idiom lists
  it: `set_subject`'s Raises names `PrincipalStoreError`. CLASS: *a method's documented raise set equals the set its
  body can raise* (domain: `wrap_store_rejection(<E>, …)` sites × the enclosing `Raises:`). Owner: 63c-i-a (prose
  only, 4 docstrings) or an accepted residual.
- **N-3 (MINOR, pre-existing at HEAD, served English):** `lore-adm migrate-governed --help` and `report-unmigrated
  --help` say `--table … (63a supports: memory)`. `_MIGRATE_VALID_TABLES` = agent, memory, message, brief, and 63c-i-a
  made agent + message real legs. Present at HEAD (`git show HEAD:…` has the same two lines), and it is a served
  surface 63c extended. Owner: 63c-i-a (one derived help string) or 63c-ii.
- **N-1 (MINOR, pre-existing):** `report_unmigrated_governed_rows`' docstring still says "STUB / runnable-RED … The
  builder fills the body" and calls it "the §2.3 forgotten-backfill alarm". It has a body, and its only caller is the
  CLI verb (no boot caller: §2.3). A reader could believe an alarm runs at boot. `migrate_governed`'s docstring
  likewise still says "packet 63a STUB / runnable-RED". Both are present at HEAD. Owner: whoever next edits `governed.py`.
- D-4 (§7.5): the brief alarm's remedy teaches a verb that refuses `brief`.

### §3.1 Mutation (b) — the four §12 wraps, each stripped in turn (instrument §A.8: the PIN'S OWN derivation `test_engine_rejection_seam.derived_write_boundaries`, driven without pytest; fresh process per state)
```
=== UNMUTATED   population: 14 | UNWRAPPED: []                                   (control)
MUTATED set_status  (principals.py)      → UNWRAPPED: ['principal::set_status']      restored byte-exact
MUTATED set_expires (principals.py)      → UNWRAPPED: ['principal::set_expires']     restored byte-exact
MUTATED delete      (principals.py)      → UNWRAPPED: ['principal::delete']          restored byte-exact
MUTATED revoke      (principal_keys.py)  → UNWRAPPED: ['principal_key::revoke']      restored byte-exact
mut4 md5 after: 5f2d7c4366d469e5c2a34d53aa235d6e
```
**HOLDS for the derived pin, BY NAME, for all four boundaries** (stronger than the one-wrap minimum). The
`mutation_proof.py` pytest leg (declared set `declB.txt`, 6 ids) first waited at the ≥ 20 GiB admission gate. The host
sat at 17.6–18.9 GiB from ~03:05Z under standing load (both surreal stores ≈ 14 GiB, postgres workers ≈ 2 GiB each),
none of it mine. The leg was re-armed behind the gate and admitted ~03:29Z: **PROOF HELD, 6 failed / 186 passed, exactly the declared set** (row (b) above).
The behavioural twin pins (`raw_store_error_surfaces_as_the_domain_error[principal-set_status]` and the LAYER1/LAYER2
cells) were GREEN in the §5 targeted run on the unmutated build.

## §A Instruments (pasted verbatim — brief-base §1; the scratch trees are disposable)

### §A.1 changed_symbols.py
```
"""Derive the production symbols a patch changes (AST: per-def source differs, added, or removed)
and the test files that reference any of them by bare name (Name id / Attribute attr / import alias).
Usage: changed_symbols.py <tree> <file>... ; reads HEAD version via `git show HEAD:<file>`."""
import ast, subprocess, sys, pathlib
tree = pathlib.Path(sys.argv[1]); files = sys.argv[2:]
def defs(src):
    out = {}
    mod = ast.parse(src)
    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = f"{prefix}{child.name}"
                body = child
                if isinstance(child, ast.ClassDef):
                    # class-level statements other than defs
                    seg = [ast.dump(s) for s in child.body if not isinstance(s,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
                    out[q] = "\n".join(seg) + ast.dump(child.bases and ast.Tuple(child.bases) or ast.Constant(None))
                else:
                    out[q] = ast.dump(child)
                walk(child, q + ".")
            elif isinstance(child, (ast.Assign, ast.AnnAssign)) and prefix == "":
                for t in (child.targets if isinstance(child, ast.Assign) else [child.target]):
                    if isinstance(t, ast.Name): out[t.id] = ast.dump(child)
    walk(mod, "")
    return out
changed = {}
for f in files:
    new = (tree / f).read_text()
    try: old = subprocess.run(["git","-C",str(tree),"show",f"HEAD:{f}"],capture_output=True,text=True,check=True).stdout
    except subprocess.CalledProcessError: old = ""
    a, b = defs(old) if old else {}, defs(new)
    for q in sorted(set(a) | set(b)):
        if a.get(q) != b.get(q):
            changed.setdefault(f, []).append(q)
names = set()
for f, qs in changed.items():
    print(f"## {f}: {len(qs)} changed symbols")
    for q in qs: print(f"   {q}"); names.add(q.split(".")[-1])
tests = sorted(p for p in (list((tree/"loremaster/tests").rglob("test_*.py")) + list((tree/"scripts").glob("test_*.py"))))
hit = {}
for p in tests:
    try: m = ast.parse(p.read_text())
    except SyntaxError: continue
    refs = set()
    for n in ast.walk(m):
        if isinstance(n, ast.Name) and n.id in names: refs.add(n.id)
        elif isinstance(n, ast.Attribute) and n.attr in names: refs.add(n.attr)
        elif isinstance(n, ast.alias) and n.name.split(".")[-1] in names: refs.add(n.name)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in names: refs.add(n.value)
    if refs: hit[str(p.relative_to(tree))] = refs
print(f"## covering test files: {len(hit)}")
for k in sorted(hit): print(f"COVER {k}  <- {','.join(sorted(hit[k]))[:160]}")
```

### §A.2 adm2.py (lore-adm REAL entry against the dump; the one loader substitution)
```
"""Drive lore-adm's REAL entry (`principals.main`) against the restored dump DB.

The ONLY substitution: `principals.load_surreal_only_config` is replaced by a loader that validates the
repo's lore.yaml normally and then `model_copy`s the surreal block to the dump coordinate — because
`SurrealConfig.database`'s pattern ^[a-z0-9][a-z0-9_]*$ refuses the uppercase name restore_prod_dump.py
mints (finding in REPORT-coldaudit-63c-i-a-4 §7). The port is asserted 18000 before every call.
Usage: adm2.py <verb> [args...]   (env AUDIT4_SURREAL_USER / AUDIT4_SURREAL_PASS set from the harness)."""
import os, sys, contextlib, io
sys.path.insert(0, "loremaster/tests")
from urllib.parse import urlparse
from _surreal_harness import surreal_user, surreal_password
from loremaster import principals, config as config_module
DUMP_DB = "test_dump_20260930T001125Z_a072e4789558446bb05abce309b4a4fb"
os.environ["AUDIT4_SURREAL_USER"] = surreal_user()
os.environ["AUDIT4_SURREAL_PASS"] = surreal_password().get_secret_value()
def dump_loader(path):
    base = config_module.load_surreal_only_config(path)
    surreal = base.surreal.model_copy(update={"url": "ws://127.0.0.1:18000/rpc", "namespace": "lore_test",
        "database": DUMP_DB, "user_env": "AUDIT4_SURREAL_USER", "password_env": "AUDIT4_SURREAL_PASS"})
    cfg = base.model_copy(update={"surreal": surreal})
    assert urlparse(cfg.surreal.url).port == 18000, "REFUSED: not the TEST store"
    assert cfg.surreal.database == DUMP_DB and cfg.surreal.namespace == "lore_test"
    return cfg
principals.load_surreal_only_config = dump_loader
argv = ["--config", "lore.yaml", *sys.argv[1:]]
out, err = io.StringIO(), io.StringIO()
print(f"$ lore-adm {' '.join(sys.argv[1:])}")
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    try:
        rc = principals.main(argv)
    except SystemExit as e:
        rc = f"SystemExit({e.code})"
    except BaseException as e:
        import traceback; traceback.print_exc(); rc = f"TRACEBACK {type(e).__name__}"
for line in out.getvalue().splitlines(): print(f"  stdout| {line}")
for line in err.getvalue().splitlines(): print(f"  stderr| {line}")
print(f"  exit={rc}")
```

### §A.3a logextra.py (prints log extras)
```
"""Run adm2 with a root log handler that prints each record's extras (engine_error etc.)."""
import logging, sys, runpy
class H(logging.Handler):
    def emit(self, r):
        extras = {k: v for k, v in r.__dict__.items() if k not in logging.LogRecord("", 0, "", 0, "", (), None).__dict__ and k not in ("message", "asctime")}
        sys.__stderr__.write(f"LOG {r.levelname} {r.name} {r.getMessage()} {extras}\n")
logging.getLogger().addHandler(H()); logging.getLogger().setLevel(logging.INFO)
sys.argv = [sys.argv[0], *sys.argv[1:]]
runpy.run_path(sys.argv[0].replace("logextra.py", "adm2.py"), run_name="__main__")
```

### §A.3b dq.py (direct SELECT probe, port-asserted)
```
"""Direct-count probe on the restored prod dump (TEST store :18000 ONLY). Usage: dq.py '<surql>' ..."""
import asyncio, sys, yaml, pathlib
from urllib.parse import urlparse
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import surreal_user, surreal_password
from surrealdb import AsyncSurreal
cfg = yaml.safe_load(pathlib.Path(__file__).with_name("lore.yaml").read_text())["surreal"]
assert urlparse(cfg["url"]).port == 18000, f"REFUSED: port {urlparse(cfg['url']).port} is not the TEST store"
async def main():
    db = AsyncSurreal(cfg["url"])
    await db.connect()
    await db.signin({"username": surreal_user(), "password": surreal_password().get_secret_value()})
    await db.use(cfg["namespace"], cfg["database"])
    for q in sys.argv[1:]:
        try: r = await db.query(q)
        except Exception as e: r = f"ERR {type(e).__name__}: {e}"
        print(f"{q}\n  => {r}")
    await db.close()
asyncio.run(main())
```

### §A.5 none — §1 probes were inline python; key lines reproduced in §1 (cells + controls)

### §A.6 check_dispatch.py
```
"""§11 structural check: the handler tuples of every lore-adm dispatcher + the fates row equality."""
import ast, pathlib, sys
sys.path.insert(0, "loremaster/tests")
src = pathlib.Path("loremaster/loremaster/principals.py").read_text()
mod = ast.parse(src)
for fn in [n for n in ast.walk(mod) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("_dispatch")]:
    handlers = [h for t in ast.walk(fn) if isinstance(t, ast.Try) for h in t.handlers]
    print(fn.name, "handlers:", [ast.unparse(h.type) if h.type else "<bare>" for h in handlers])
from _exhaustion_fates import REGISTERED_FATES
rows = {k: v for k, v in REGISTERED_FATES.items() if k.startswith("principals.py::")}
for k, v in rows.items(): print("ROW", k, [(f.kind if hasattr(f,'kind') else f, getattr(f,'catches',None)) for f in v])
disp = next(n for n in mod.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "_dispatch")
tup = [ast.unparse(h.type) for t in ast.walk(disp) if isinstance(t, ast.Try) for h in t.handlers]
print("EQUAL row.catches == unparse:", rows.get("principals.py::_dispatch", [None])[0].catches in tup)
```

### §A.7 probe_r12.py
```
"""R-1 / R-2 probes for principals._dispatch (am-37 §11). Fake stores; no socket, no store."""
import asyncio, contextlib, io, sys, types
from loremaster import principals, principal_keys
from loremaster.store._txn import SurrealConnectionError, TxnDomainRejectionError
events = []
class Fake:
    def __init__(self, name, *, ensure_raises=None, close_raises=None):
        self.name, self.ensure_raises, self.close_raises = name, ensure_raises, close_raises
    async def ensure_ready(self):
        events.append(f"{self.name}.ensure_ready")
        if self.ensure_raises: raise self.ensure_raises
    async def close(self):
        events.append(f"{self.name}.close")
        if self.close_raises: raise self.close_raises
    async def list(self): return []
def run(label, argv, *, principal=None, key=None, keep=None, factory_raises=None):
    events.clear()
    def mk(obj, which):
        def factory(config):
            events.append(f"build_{which}")
            if factory_raises and factory_raises[0] == which: raise factory_raises[1]
            return obj
        return factory
    principals.build_principal_store = mk(principal or Fake("principal"), "principal")
    principal_keys.build_principal_key_store = mk(key or Fake("key"), "key")
    principals.build_keep_store = mk(keep or Fake("keep"), "keep")
    principals.load_surreal_only_config = lambda path: types.SimpleNamespace()
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try: rc = principals.main(["--config", "x.yaml", *argv])
        except BaseException as exc: rc = f"RAISED {type(exc).__name__}: {exc} (context={type(exc.__context__).__name__ if exc.__context__ else None})"
    print(f"[{label}] rc={rc}\n   stderr={err.getvalue().strip()!r}\n   events={events}")
domain = TxnDomainRejectionError("(assert violation); see the server log")
# CONTROL: fault in ensure_ready, closes behave → original printed, all 3 closed
run("R1-control", ["list"], principal=Fake("principal", ensure_raises=domain))
# R-1a: fault + keep.close raises an IN-TUPLE class
run("R1a close raises SurrealConnectionError", ["list"], principal=Fake("principal", ensure_raises=domain), keep=Fake("keep", close_raises=SurrealConnectionError("socket gone")))
# R-1b: fault + keep.close raises an OUT-of-tuple class
run("R1b close raises OSError", ["list"], principal=Fake("principal", ensure_raises=domain), keep=Fake("keep", close_raises=OSError("EBADF")))
# R-1c: SUCCESS path but close raises in-tuple → a success turned into exit 1?
run("R1c success + close raises", ["list"], keep=Fake("keep", close_raises=SurrealConnectionError("socket gone")))
# R-2: factory raises (ValueError / store error) on the 2nd factory
run("R2a key factory ValueError", ["list"], factory_raises=("key", ValueError("bad coordinate")))
run("R2b keep factory TypeError (out-of-tuple)", ["list"], factory_raises=("keep", TypeError("programming defect")))
```

### §A.8a probe_wraps.py
```
"""Drive the am-37 §12 derived wrap-coverage pin's OWN derivation (test_engine_rejection_seam.derived_write_boundaries)
over every store case, without pytest. Prints every UNWRAPPED write boundary, plus the loremaster module path."""
import sys
sys.path.insert(0, "loremaster/tests")
import loremaster, test_engine_rejection_seam as t
print("loremaster.__file__:", loremaster.__file__)
unwrapped = []
for boundary in t._boundary_population():
    label, _, method = boundary.partition("::")
    case = t._CASES_BY_LABEL[label]
    if [line for line, wrapped in t.derived_write_boundaries(case)[method] if not wrapped]:
        unwrapped.append(boundary)
print("population:", len(t._boundary_population()), "| UNWRAPPED:", unwrapped)
```

### §A.8b wrapmut.py
```
import pathlib, sys
ANCH = {
 "set_status": ("loremaster/loremaster/principals.py", '        with wrap_store_rejection(\n            PrincipalStoreError,\n            f"could not set status of principal {email!r} to {status!r}",\n        ):'),
 "set_expires": ("loremaster/loremaster/principals.py", '        with wrap_store_rejection(\n            PrincipalStoreError,\n            f"could not set expiry of principal {email!r}",\n        ):'),
 "delete": ("loremaster/loremaster/principals.py", '        with wrap_store_rejection(\n            PrincipalStoreError,\n            f"could not delete principal {email!r}",\n        ):'),
 "revoke": ("loremaster/loremaster/principal_keys.py", '        with wrap_store_rejection(\n            PrincipalKeyStoreError,\n            f"could not revoke key {name!r} for principal {email!r}",\n        ):'),
}
f, a = ANCH[sys.argv[1]]; p = pathlib.Path(f); s = p.read_text()
assert s.count(a) == 1, (sys.argv[1], s.count(a)); p.write_text(s.replace(a, "        if True:  # MUTATION: wrap stripped")); print(f"MUTATED {sys.argv[1]} (landed in {f})")
```

### §A.9 probe_am14.py (mutation d)
```
"""am-14 §1 probe: two bounds share a path; the error names ONLY the second bound's symbol."""
from pathlib import Path
from pending_contract_gate import MypyOutputReader, PendingContractGate, PendingContractRegistry
P = "lorerunes/tests/test_posture.py"
def err(sym): return f'{P}:1: error: Module "lorerunes" has no attribute "{sym}"  [attr-defined]'
A = {"id": "a", "owner": "A", "reopen_trigger": "t", "ruling": "r", "rationale": "x", "files": [{"path": P, "missing_symbols": ["lorerunes.FirstOnly"]}]}
B = {"id": "b", "owner": "B", "reopen_trigger": "t", "ruling": "r", "rationale": "x", "files": [{"path": P, "missing_symbols": ["lorerunes.SecondOnly"]}]}
T = lambda lines: "\n".join(lines) + f"\nFound {len(lines)} errors in 1 file (checked 1 source files)\ntypecheck: loremaster FAILED\ntypecheck: shellcheck OK (7 tracked .sh)\n"
for label, lines in (("SECOND-bound symbol", [err("SecondOnly")]), ("CONTROL neither symbol", [err("Neither")])):
    gate = PendingContractGate(PendingContractRegistry.model_validate({"version": 1, "bounds": [A, B]}), Path("."))
    part = gate.partition_mypy(MypyOutputReader.read(T(lines)))
    print(f"{label}: expected={len(part.expected)} unexpected={len(part.unexpected)}")
```

### §A.10 mp.sh (memory-gated, cgroup-capped mutation_proof wrapper)
```
#!/bin/bash
# usage: mp.sh <declfile> <file> <anchorfile> <replfile> <testfiles...>  — memory-gated, cgroup-capped mutation_proof
decl=$1; file=$2; anchor=$3; repl=$4; shift 4
until [ $(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo) -ge 20 ]; do sleep 10; done
args=(); while read -r id; do [ -n "$id" ] && args+=(--expect-red "$id"); done < "$decl"
systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --no-sync python scripts/mutation_proof.py --file "$file" --anchor-file "$anchor" --replacement-file "$repl" "${args[@]}" -- uv run --no-sync --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider "$@"
echo "mutation_proof exit=$?"
```

### §A.11 probe_group_all_r2.py (fix3's instrument, reused for mutation c; md5 e3bfa3c4)
```
"""Round-2 probe (builder-63c-i-a-fix3, am-37 §10, 2026-09-30). Real bodies; only the driver seams
(`run_query` / `PrincipalStore._query` / `execute_transaction`) and non-count collaborators are faked.
Part A, the SHARING leg (run once per tree state: unmutated / mutated), feeds each caller an EMPTY
GROUP ALL answer:
  (1) principals._scope_count                       -> return value
  (2) principals._migrate_message_owner             -> unsound_sender_messages
  (3) PrincipalStore.delete owned_count (SF-63-5)   -> proceeds (0) / refuses naming N
  (4) governed.report_unmigrated_governed_rows      -> return value
Part B, the FATE leg: the `report-unmigrated` verb and `PrincipalStore.delete`, each given
  REJECTED (the driver raises SurrealStoreError, as run_query does on an engine rejection) vs
  MALFORMED ([{"cnt": 1}]) -> exit code / stderr / exception class / whether the delete executed."""
import argparse
import asyncio
import contextlib
import io
from types import SimpleNamespace

import loremaster
import loremaster.governed as governed
import loremaster.principals as principals
from loremaster.store._txn import SurrealStoreError

print("loremaster.__file__ =", loremaster.__file__)
calls = []


async def fake_run_query(*, noun, statement, **_):
    calls.append(noun)
    if noun == "governed scope count":
        return [{"count": 1}] if "IS NONE" in statement else []
    return []


async def fake_operator(_store):
    return SimpleNamespace(email="op@example.invalid")


class FakeKeepStore:
    async def get_or_create_keyed(self, **_):
        return SimpleNamespace(id="keep:probe")


principals.run_query = fake_run_query
principals._message_leg_refusal = lambda *_a, **_k: None
principals.resolve_operator_principal = fake_operator
handle = SimpleNamespace(acquire=None, drop=None, url="ws://probe.invalid")
executed = []


async def fake_execute_transaction(*_a, **_k):
    executed.append(1)


principals.execute_transaction = fake_execute_transaction


def principal_store(owned_answer):
    store = object.__new__(principals.PrincipalStore)

    async def get_by_email(_email):
        return SimpleNamespace(id="principal:p1")

    async def table_exists(_table):
        return True

    async def query(statement, _params=None):
        if "FROM keep" in statement:
            return []
        if "FROM memory" in statement:
            if isinstance(owned_answer, Exception):
                raise owned_answer
            return owned_answer
        return []  # the principal_key cascade count

    store.get_by_email, store._table_exists, store._query = get_by_email, table_exists, query
    store._ensure_connection, store._drop_connection, store._url = None, None, "ws://probe.invalid"
    return store


async def delete_outcome(owned_answer):
    executed.clear()
    try:
        cascaded = await principal_store(owned_answer).delete(email="p@example.invalid")
        return f"PROCEEDED cascaded={cascaded} executed={bool(executed)}"
    except Exception as error:  # noqa: BLE001 - the probe reports the class
        return f"{type(error).__name__} executed={bool(executed)}: {str(error)[:90]}"


async def report_verb(answer):
    async def governed_run_query(**_):
        if isinstance(answer, Exception):
            raise answer
        return answer

    governed.run_query = governed_run_query
    fake_store = SimpleNamespace(_ensure_connection=None, _drop_connection=None, _url="ws://probe.invalid")

    async def noop():
        return None

    fake_store.ensure_ready, fake_store.close = noop, noop
    principals.build_principal_store = lambda _config: fake_store
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = await principals._dispatch_report_unmigrated(argparse.Namespace(table="memory"), None)
    return f"exit={code} stdout={stdout.getvalue().strip()!r} stderr={stderr.getvalue().strip()[:110]!r}"


async def main():
    print("== A: sharing (EMPTY GROUP ALL answer to every caller)")
    print("  (1) _scope_count =", await principals._scope_count(handle, "memory", none=False))
    result = await principals._migrate_message_owner(
        handle, FakeKeepStore(), object(), object(), object(), table_defined=True
    )
    print(f"  (2) message leg unsound_sender_messages = {result.unsound_sender_messages}")
    print("  (3) delete owned_count:", await delete_outcome([]))
    saved = governed.run_query

    async def empty(**_):
        return []

    governed.run_query = empty
    print("  (4) report_unmigrated_governed_rows =", await governed.report_unmigrated_governed_rows(handle, "memory"))
    governed.run_query = saved
    rejected = SurrealStoreError("governed unmigrated-scope count rejected by the engine (probe)")
    print("== B: fate, REJECTED vs MALFORMED")
    print("  report-unmigrated REJECTED :", await report_verb(rejected))
    print("  report-unmigrated MALFORMED:", await report_verb([{"cnt": 1}]))
    print("  delete REJECTED :", await delete_outcome(SurrealStoreError("principal query rejected (probe)")))
    print("  delete MALFORMED:", await delete_outcome([{"cnt": 1}]))
    print("  delete NON-LIST :", await delete_outcome("oops"))
    print("  delete OWNS 2   :", await delete_outcome([{"count": 2}]))


asyncio.run(main())
```

### §A.12 probe_shared_unsymboled.py (fixup-tests-63c-i-a's instrument, reused for mutation d)
```
"""Probe (fixup-tests-63c-i-a, 2026-09-30): does the per-entry unsymboled-count self-destruct leg
miscount on a path shared by two bounds? Entry A: symbol FixturePlaceholder + 1 unsymboled attr-defined.
Entry B: symbol FixtureOtherPlaceholder. Errors: A's symbol, B's symbol, one genuinely unsymboled attr-defined.
CONTROL: same errors, B's bound removed and B's error dropped -> A's count must be exactly 1 (no finding)."""
import sys
from pathlib import Path
from pending_contract_gate import MypyOutputReader, PendingContractGate, PendingContractRegistry

P = "lorerunes/tests/test_posture.py"
def err(sym): return f'{P}:1: error: Module "lorerunes" has no attribute "{sym}"  [attr-defined]'
UNSYM = f'{P}:2: error: Something without a quoted symbol  [attr-defined]'
def transcript(lines):
    return "\n".join(lines) + f"\nFound {len(lines)} errors in 1 file (checked 1 source files)\ntypecheck: loremaster FAILED\ntypecheck: shellcheck OK (7 tracked .sh)\n"
A = {"id": "a", "owner": "A", "reopen_trigger": "t", "ruling": "r", "rationale": "x",
     "files": [{"path": P, "missing_symbols": ["lorerunes.FixturePlaceholder"],
                "unsymboled_codes": [{"code": "attr-defined", "count": 1, "reason": "probe"}]}]}
B = {"id": "b", "owner": "B", "reopen_trigger": "t", "ruling": "r", "rationale": "x",
     "files": [{"path": P, "missing_symbols": ["lorerunes.FixtureOtherPlaceholder"]}]}
for label, bounds, lines in (
    ("SHARED", [A, B], [err("FixturePlaceholder"), err("FixtureOtherPlaceholder"), UNSYM]),
    ("CONTROL", [A], [err("FixturePlaceholder"), UNSYM]),
):
    gate = PendingContractGate(PendingContractRegistry.model_validate({"version": 1, "bounds": bounds}), Path("."))
    run = MypyOutputReader.read(transcript(lines))
    part = gate.partition_mypy(run)
    print(label, "expected", len(part.expected), "unexpected", len(part.unexpected))
    for finding in gate.transcript_self_destruct_findings(run):
        print(label, "FINDING:", finding[:200])
```

### §A.4 boot-DDL application (inline, run once against the dump DB)
```
for name in [generate_ddl(dim=2048), generate_agent_ddl, generate_message_ddl, generate_brief_ddl, generate_audit_ddl, generate_task_ddl, generate_finding_ddl]: db.query_raw(<ddl>) on ws://127.0.0.1:18000 ns lore_test db <dump>; count statements with status != OK  → 0 errors each
```

### §A.13 declared test sets
- targeted set `declared_audit4.txt` (md5 a7795901, 101 files):
```
loremaster/tests/test_425_stamp_owner_63a.py
loremaster/tests/test_agent_capability.py
loremaster/tests/test_agent_capability_seams.py
loremaster/tests/test_agent_governance_63c_i_a.py
loremaster/tests/test_agent_owns_principal_schema.py
loremaster/tests/test_agent_registry.py
loremaster/tests/test_audit_store.py
loremaster/tests/test_auth.py
loremaster/tests/test_blocks_edge.py
loremaster/tests/test_brief_ledger.py
loremaster/tests/test_comms_await.py
loremaster/tests/test_comms_capability_63b_ii_a.py
loremaster/tests/test_comms_cli.py
loremaster/tests/test_comms_footer.py
loremaster/tests/test_comms_promise_registry.py
loremaster/tests/test_comms_read_governance_63b_ii_b.py
loremaster/tests/test_comms_register_notice.py
loremaster/tests/test_comms_render_architecture.py
loremaster/tests/test_comms_schema.py
loremaster/tests/test_comms_send_scope_63b_ii_a.py
loremaster/tests/test_comms_status_age.py
loremaster/tests/test_comms_story.py
loremaster/tests/test_comms_tool.py
loremaster/tests/test_comms_wiring.py
loremaster/tests/test_diff.py
loremaster/tests/test_engine_rejection_seam.py
loremaster/tests/test_exhaustion_fates.py
loremaster/tests/test_findings_classes_64b.py
loremaster/tests/test_findings_closeout_64b.py
loremaster/tests/test_findings_governance_64b.py
loremaster/tests/test_findings_migrate_64b.py
loremaster/tests/test_findings_schema_64b.py
loremaster/tests/test_findings_scope_domain_64b.py
loremaster/tests/test_findings_system_writer_64b.py
loremaster/tests/test_fixwave_a19_63c_i_a.py
loremaster/tests/test_fixwave_a19a_63c_i_a.py
loremaster/tests/test_fixwave_a19b_63c_i_a.py
loremaster/tests/test_fixwave_a28_63c_i_a.py
loremaster/tests/test_fixwave_a28b_63c_i_a.py
loremaster/tests/test_fixwave_a28c_63c_i_a.py
loremaster/tests/test_floor_calibration_store.py
loremaster/tests/test_governed_migration_63a.py
loremaster/tests/test_governed_substrate_63a.py
loremaster/tests/test_governed_substrate_64b.py
loremaster/tests/test_keep_remediation_cli_61.py
loremaster/tests/test_keep_remediation_store_61.py
loremaster/tests/test_keeps_cli.py
loremaster/tests/test_keeps_store.py
loremaster/tests/test_link5_render_containment.py
loremaster/tests/test_mcp_server.py
loremaster/tests/test_memory_backend.py
loremaster/tests/test_memory_enforcement_63a_v.py
loremaster/tests/test_memory_enforcement_63b_ia.py
loremaster/tests/test_memory_f5_registration_63b_ib.py
loremaster/tests/test_memory_replay_fidelity_63b_ib.py
loremaster/tests/test_memory_retrofit_63a.py
loremaster/tests/test_memory_supersede_atomicity_63b_ib.py
loremaster/tests/test_message_enforcement_63b_ii_a.py
loremaster/tests/test_message_ledger.py
loremaster/tests/test_message_migrate_63b_ii_a.py
loremaster/tests/test_message_migrate_dirty_store_63b_ii_b.py
loremaster/tests/test_pdp_oracle_61b.py
loremaster/tests/test_principal_delete_cascade_61.py
loremaster/tests/test_principal_delete_governed_63a.py
loremaster/tests/test_principal_keys_schema.py
loremaster/tests/test_principal_keys_store.py
loremaster/tests/test_principals_cli.py
loremaster/tests/test_principals_store.py
loremaster/tests/test_query_tasks_bounded.py
loremaster/tests/test_readonly_guard.py
loremaster/tests/test_reanchor_58_r2_rulings.py
loremaster/tests/test_reanchor_58_r3_am6.py
loremaster/tests/test_reanchor_58_r3_cas_seam.py
loremaster/tests/test_reanchor_58_r3_tiers.py
loremaster/tests/test_reanchor_58_r4_lease_fates.py
loremaster/tests/test_reanchor_58_r4_state.py
loremaster/tests/test_records.py
loremaster/tests/test_render_mypy_layer_optout.py
loremaster/tests/test_render_mypy_layer.py
loremaster/tests/test_render.py
loremaster/tests/test_render_seam_pins.py
loremaster/tests/test_render_slot_inventory.py
loremaster/tests/test_retry_seam.py
loremaster/tests/test_rollup_extension.py
loremaster/tests/test_startup_divergence_reconcile.py
loremaster/tests/test_store_seam_one_derivation.py
loremaster/tests/test_surreal_harness.py
loremaster/tests/test_surreal_manifest.py
loremaster/tests/test_surreal_store.py
loremaster/tests/test_task_read_surface.py
loremaster/tests/test_text_hygiene.py
loremaster/tests/test_token_verifier.py
loremaster/tests/test_txn_contention.py
loremaster/tests/test_visible_keeps_61b.py
loremaster/tests/test_wire_isolation_63a.py
scripts/test_forgery_door_sweep.py
scripts/test_gate_currency.py
scripts/test_gated_ground.py
scripts/test_pending_contract_gate.py
scripts/test_pytest_workers_503.py
scripts/test_snapshot_gc.py
```
- mutation (a) `declA.txt` (md5 71d28cd9) and (b) `declB.txt`:
```
loremaster/tests/test_principals_cli.py::TestReportUnmigratedVerb::test_report_unmigrated_on_an_absent_table_fails_loud_not_a_traceback
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[add]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[add-household]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[create-keep]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[delete]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[delete-keep]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[list]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[list-keys]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[migrate-governed]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[mint-key]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[remove-household]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[report-unmigrated]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[revoke-key]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[set-expiry]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[set-keeper]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[set-rank]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[suspend]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[unsuspend]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[add]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[add-household]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[create-keep]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[delete]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[delete-keep]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[list]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[list-keys]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[migrate-governed]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[mint-key]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[remove-household]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[report-unmigrated]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[revoke-key]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[set-expiry]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[set-keeper]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[set-rank]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[suspend]
loremaster/tests/test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_CONTROL_a_transport_fault_takes_the_same_fate[unsuspend]
loremaster/tests/test_exhaustion_fates.py::TestTheRegistryIsTheAdjudicationBothWays::test_every_non_derived_site_has_a_row_and_every_row_a_site
loremaster/tests/test_exhaustion_fates.py::TestTheRegistryIsTheAdjudicationBothWays::test_every_row_is_matched_to_ITS_site_by_the_caught_expression
loremaster/tests/test_engine_rejection_seam.py::TestEveryDerivedWriteBoundaryIsWrapped::test_the_write_boundary_sits_inside_its_stores_wrap[principal::set_status]
loremaster/tests/test_engine_rejection_seam.py::TestEngineRejectionWrappingBehaviourIsPreserved::test_a_raw_store_error_surfaces_as_the_domain_error[principal-set_status]
loremaster/tests/test_engine_rejection_seam.py::TestSharingProvenByMutation::test_dropping_LAYER1_reclassify_moves_every_routed_path[principal-set_status]
loremaster/tests/test_engine_rejection_seam.py::TestSharingProvenByMutation::test_dropping_LAYER2_wrap_store_rejection_moves_every_routed_path[principal-set_status]
loremaster/tests/test_engine_rejection_seam.py::TestTheRoutedSetIsDerivedAndComplete::test_the_routed_set_equals_the_invocation_map[principal]
loremaster/tests/test_engine_rejection_seam.py::TestTheRoutedSetIsDerivedAndComplete::test_the_routed_set_equals_the_known_wrapping_verbs[principal]
```

## §R Residual table
| # | class (the lifted property) | owner | re-open trigger |
|---|---|---|---|
| D-1 | every name `restore_prod_dump.py` can mint is addressable by every lore config consumer | packet 64 (S2 instrument) | the next S2 / 65 dress-rehearsal run through lore-adm |
| D-2 | every precondition a migrate leg's writes need (the governed columns) is measured and TAUGHT before the first write | operator ruling (63c-i-a fix / 65 runbook / residual) | the 65 cutover runbook review, or any migrate run before the new image boots |
| D-3 | every served pointer resolves to a surface the consumer can open ("see the server log" in a CLI) | operator ruling; candidate owner 63c-i-a (§11 surface) or the `_SERVER_LOG_HINT` owner | the next lore-adm-touching contract, or the next operator report of an undiagnosable lore-adm fault |
| D-4 | a served remedy names a verb that accepts the input (brief alarm → a refusing verb) | 63c-ii (closes by construction when brief's leg lands) | 63c-ii build |
| N-1 | a docstring describes the function as built (the "STUB / runnable-RED" and boot-"alarm" prose in `governed`/`principals`) | the next `governed.py` editor | any edit to `report_unmigrated_governed_rows` / `migrate_governed` |
| N-2 | a method's documented raise set equals what its body can raise (the 4 §12-wrapped methods) | 63c-i-a (fix in commit) or an accepted residual | the next `principals`/`principal_keys` contract |
| N-3 | CLI help derives from `_MIGRATE_VALID_TABLES` ("63a supports: memory" is stale) | 63c-i-a / 63c-ii | 63c-ii (adds brief) |
| R-1 | a teardown fault never masks the verb's own outcome (close() raising during/after the verb) | the next lore-adm-touching contract | a teardown fault observed in the field |
| D-1 gate pin (fix3) | the unsymboled self-destruct leg is judged per path-union — no pin (only probe §3 (d)) | the next gate contract (lead anchor v8) | the next `pending_contract_gate.py` edit |
| §W row 4 | derived `_txn` ladder pin, garbage-text KF cells, FK-B1 pin-1 AST re-key, `QueryDetailKind` completeness, fixture drift | next `_txn`-touching contract (58-r4 / close-out) | as am-37 §W |
| F-C4 | a stored id rendered into served prose passes ONE sanitiser neutralising newlines AND fence runs | #34's promotion | an MCP-served principal-id render |
| F-C10, F-13, F-14, F-16 | as ruled am-37 §6/§7 | as ruled | as ruled |
| GROUP ALL sweep | every `SELECT count() … GROUP ALL` consumer reads through `group_all_count` — remaining: `messages`/`findings`/`tasks._extract_group_count` + **`PrincipalStore.delete`'s own `cascaded` count** (inline, tolerant) | 64b §DRY step (am-37 §8.3/§10.1) | 63c close-out |
| (c) suite bound | no suite pin asserts the message-leftover caller's value (probe-only coverage, fix3 + §3 (c)) | next result-model contract | as fix3 |
| gate UX | `--legs` renders an unselected leg as "ORPHAN … FAIL" | packet 58 / gates.yaml owner | the next currency-gate edit |
