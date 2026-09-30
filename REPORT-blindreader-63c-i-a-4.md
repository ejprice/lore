brief-base v18 read

# REPORT — blindreader-63c-i-a-4 (contract-blind diff read, wave 63c-i-a, OLD a28c → NEW fix5)

## SUMMARY BLOCK
- **State:** done-with-deviations. 0 BLOCKER · 0 MAJOR · 9 MINOR · 7 NIT. No path found where a fault prints success. No new partial-write door found in a single-statement or cascade verb.
- **Deviation 1 (independence):** a retired-name sweep (awk over `docs/`) printed about 20 lines from withheld `docs/design/*amendment*` files (am-36, am-37 and packet58 am-14). The hits were about `_CASCADE_KIND(S)`, `QueryDetailKind` and `entry_for`. I did not open those files and did not use their content: every verdict below is derived from the code. I then excluded `docs/design` from all later sweeps. Treat my independence on the `_txn` cascade and gate `entries_for` items as slightly weakened.
- **Deviation 2 (tools):** I did not load lore. The code under review exists only in patched scratch trees, and lore indexes the main checkout, not those trees (the known #125 overlay gap, so I filed no new finding). Every structure read was `diff`/`awk`/`sed` over the two trees. No grep was used.
- **Packages considered:** none. I specified no mechanism.
- **Odoo-20 portability:** n/a. No Odoo seam was touched.
- **Reuse ledger:** none. No symbols were written.
- **Graded:** HEAD `5089146` + NEW patch md5 `5f2d7c43…` (diffed against HEAD + OLD md5 `956e4136…`) · HEAD-at-report: `7bf2304` · DIFFERENT (1 ahead). The only thing that moved is `REPORT-lead-63c.md` (+7 lines), so no production symbol differs.
- **Decisions needed:**
  - F-3/F-9: should lore-adm print the reason a wrapped store fault happened (`__cause__`) and/or use distinct exit codes for transient vs refused faults? This is an operator call.
  - F-4: should `unsound_sender_messages` be relabelled "remain un-migrated", or should its count predicate be narrowed?
- **Receipts:**
  - §2 inventory table, §3 fault walk and §4 findings, below.
  - The diff instrument is pasted verbatim in §1. It was re-runnable only while the scratch trees existed; they are disposable, so the recipe is the durable part.

## 1. Instrument (verbatim)
```bash
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/93b92a04-e27d-4942-8aea-fb3cb416bc8e/scratchpad/blind4
md5sum $OLD $NEW   # 956e4136b403d061cf60603c53def3ef / 5f2d7c4366d469e5c2a34d53aa235d6e — both matched
./scripts/scratch_copy.sh "$S/old"                                   # rc=0, provenance asserted
cd $S/old && git reset -q --hard HEAD && git clean -fdq && git apply $OLD      # HEAD 508914697a90
cp -a $S/old $S/new && cd $S/new && git reset -q --hard HEAD && git clean -fdq && git apply $NEW
cd $S && diff -ru old/loremaster/loremaster new/loremaster/loremaster -x __pycache__
diff -u old/scripts/pending_contract_gate.py new/scripts/pending_contract_gate.py
```
Production files changed OLD→NEW: `governed.py` (118 diff lines), `keeps.py` (37), `principal_keys.py` (27), `principals.py` (853), `store/_txn.py` (320) and `scripts/pending_contract_gate.py` (69). The `keeps.py` diff OLD→NEW contains only docstrings and comments. Its code change (the CAS door narrowed to `except TxnUniqueViolationError`) is HEAD→OLD, and I read it only for context.

## 2. Removed/changed-behaviour inventory (OLD a28c → NEW fix5), derived from the diff

| # | Site (symbol) | OLD behaviour | NEW fate |
|---|---|---|---|
| I-1 | `principals._dispatch` (principal/key branch) `except` | Caught `(PrincipalStoreError, PrincipalKeyStoreError, SurrealConnectionError, ValueError)`. A raw `SurrealStoreError` (rejected read, DDL rejection in `ensure_ready`, `TxnDomainRejectionError`, `TxnContentionExhaustedError`) escaped as a **traceback**. | **CHANGED (widened).** A single handler now wraps every verb and catches `(PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError, ValueError)`. It prints `lore-adm: {error}` and returns 1. Tracebacks for store faults are gone. |
| I-2 | `_dispatch` ordering of the handler and the closes | `try/except/finally` in one frame: on a fault the stderr line was printed **first**, then the closes ran. A close that raised would traceback *after* the original message was already on stderr. | **CHANGED.** The inner `try/finally` closes **before** the outer handler prints. A close raising a tuple class *replaces* the original fault: only the close's message is printed, and the original survives only as `__context__`. Reachability is low, because every `close()` → `_safe_close` swallows `(OSError, SurrealError, WebSocketException)` (`_txn._CONNECTION_ERRORS`). See F-8. |
| I-3 | `_dispatch` store construction | `build_principal_store` / `build_principal_key_store` / `build_keep_store` ran outside the `try`, so a `ValueError` from them was a traceback. | **CHANGED.** They now run inside the handler, so that fault is laundered to stderr + 1. `_require_config` / `load_surreal_only_config` stay OUTSIDE, as the comment says (a config `ValueError` / pydantic error still tracebacks, as before). |
| I-4 | `_dispatch_migrate_governed` `except (PrincipalStoreError, KeepStoreError, SurrealConnectionError, ValueError)` + its local `KeepStoreError` import | Raw `SurrealStoreError` from any leg (`governed.*.rejected` labels) → traceback. | **GONE from this frame.** Handled by the I-1 handler, so a leg rejection is now stderr + 1. The `REFUSED` stderr + 1 path is preserved in-frame, and `refused` is still checked before `table_defined is False`, so no refusal can render as "nothing to migrate". |
| I-5 | `_dispatch_report_unmigrated` `except (PrincipalStoreError, SurrealStoreError, ValueError)` + comment "SurrealStoreError subsumes SurrealConnectionError AND a rejected SELECT" | stderr + 1. | **PRESERVED** by the I-1 handler, whose catch set is a superset. The comment moved into the docstring. |
| I-6 | `_dispatch_keep` `except (KeepStoreError, SurrealConnectionError, ValueError)`; FR-2 D1 (a raw `SurrealStoreError` deliberately NOT caught → traceback as the missed-wrap bug signal) | A missed wrap in `KeepStore` crashed loudly. | **DROPPED DELIBERATELY** (the docstring says D1 was re-ruled at am-37 §11). The missed-wrap property now depends only on "the FR-2 wrap pins over KeepStore's write boundaries" (NOT verified by me). On the operator surface, a missed wrap now prints the driver label + server-log hint instead of a traceback. |
| I-7 | Laundered stderr format / exit code | `f"{_CLI_PROG}: {error}"`, exit 1. | **PRESERVED** byte-identical. |
| I-8 | `PrincipalStore.set_status` UPDATE | Unwrapped: a rejection was a raw `SurrealStoreError` (→ traceback via I-1 OLD). | **CHANGED.** `wrap_store_rejection(PrincipalStoreError, "could not set status of principal … to …")`. The message is the context ONLY (ledger #31); engine label/hint are only in `__cause__`. |
| I-9 | `PrincipalStore.set_expires`, both branches (clear `NONE` / set datetime) | Unwrapped. | **CHANGED.** One wrap covers both branches. Branch logic is preserved byte-for-byte (re-indented only). |
| I-10 | `PrincipalStore.delete`, whole body | Unwrapped. The owned-governed-row guard read `int(rows[0].get("count", 0)) if rows else 0` through `_as_rows`, which reads a non-list as `[]`. **A malformed count therefore read as 0 and the delete PROCEEDED, dangling owned rows** (a silent guard bypass). | **CHANGED.** One wrap from `get_by_email` through `execute_transaction`. The owned count goes through `governed.group_all_count`, which is fail-closed: a malformed count raises `SurrealStoreError` → wrapped → "could not delete principal …", and nothing is deleted. The OLD silent bypass is **gone** (correct). Refusals (`PrincipalNotFoundError` / `HasKeeps` / `OwnsGovernedRows`) are `RuntimeError`, not `SurrealStoreError`, so they pass the wrap untouched (checked: `principals.PrincipalStoreError(RuntimeError)`). |
| I-11 | `PrincipalStore.delete` key-cascade count (`count_rows` → `cascaded`) | Silent-zero reader. | **UNCHANGED.** It still reads `int(count_rows[0].get("count", 0)) if count_rows else 0`, while its sibling one statement above was moved. See F-1. |
| I-12 | `PrincipalKeyStore.revoke` UPDATE | Unwrapped. | **CHANGED.** Wrapped as `PrincipalKeyStoreError("could not revoke key …")`. `_require_principal_id` (a read) stays unwrapped. |
| I-13 | `principals._scope_count` | A non-list, empty-first-row, missing or `None` count read as `0`. A 0 `unmigrated` took the early "nothing to backfill" return, so **a malformed count silently skipped a leg's backfill.** | **CHANGED.** `group_all_count`: `[]`→0, `[{"count": int}]`→int, anything else raises `SurrealStoreError`, so the migrate verb exits with stderr + 1. The silent skip is gone. In the message and memory legs this raise can land AFTER the idempotent project-keep mint (documented, pre-existing). |
| I-14 | `governed.report_unmigrated_governed_rows` count | `int(… or 0)`: a malformed answer, `None`, or a missing count → 0. The alarm stayed silent. Also accepted a numeric STRING `"5"` via `int()`. | **CHANGED.** `group_all_count`, fail-closed: raises, so stderr + 1. A string count now raises too (the engine returns `int`, so benign). |
| I-15 | `_governed_select` docstring | Claimed "a non-list answer reads as no rows", but the code already raised. | **PROSE FIXED.** Code unchanged. It still silently drops non-dict list members (F-7). |
| I-16 | `MigrateGovernedResult.table_defined` default `True`; `_not_supported(store_was_read=…)`; `dataclasses.replace(..., table_defined=None)` for an invalid name | Every refusal after `INFO FOR DB` claimed `table_defined=True` even when the table was undefined, which was a false field. | **CHANGED.** No default; derived once as `table in preconditions.defined_tables` in `_migrate_governed_resolved` and threaded through every constructor. `None` means the zero-I/O invalid-name path. Checked: all 8 production `MigrateGovernedResult(` constructions state both `table_defined` and `unsound_sender_messages`. |
| I-17 | Message leg: rows the self-guarding UPDATE skips (`sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE` was already in OLD) | Skipped rows were a **silent fate**, re-skipped forever on every re-run. | **CHANGED.** One post-UPDATE `SELECT count() … WHERE scope IS NONE AND owner_principal IS NONE GROUP ALL` fills `unsound_sender_messages`. It is rendered on stdout for every table (`=None` for memory/agent), plus a stderr sentence iff > 0. Exit stays 0. See F-4 and F-5. |
| I-18 | `_owned_unscoped_part` mixed-owner sentence | "…AND by other principal(s): N distinct owner(s) (first k named: …)". N counted the operator too, so "other" over-stated it by 1. | **CHANGED.** "…and by others: N distinct principal(s) in all, the operator among them (a sample of the others: …)". Checked: `named` cannot be empty on this branch (classification and `owners` derive from the same full `owned_unscoped` set). |
| I-19 | `_txn._CASCADE_KIND = QueryDetailKind.NOT_EXECUTED`; `_is_domain_cascade_notice` = `_detail_kind(typed) == NotExecuted` | `Cancelled` (post-offender) entries counted as SUBSTANTIVE. The effect was harmless in the normal shape, because the offender precedes them. | **CHANGED.** `isinstance(typed, QueryError) and (is_not_executed or is_cancelled)`. The only behavioural difference is in degenerate shapes (no substantive entry before a `Cancelled` one): the root cause now falls to the LAST entry (the refused COMMIT) instead of the first `Cancelled`. `TimedOut` stays substantive. |
| I-20 | `_txn._failed_statements`: `parse_query_error(...)` unguarded | A malformed per-statement dict (non-dict `cause`, unhashable `kind`, a deep cause chain) raised a raw `AttributeError`/`TypeError`/`RecursionError` **out of `execute_transaction`** (a traceback). | **CHANGED.** `_parse_failed_statement` catches exactly those three, logs `store.transaction.untypeable_err_entry` at WARNING, and carries the entry untyped. The rollback raises as a domain rejection. Side effect: an untypeable entry that WAS a retryable conflict is no longer retried (F-12). |
| I-21 | `_run_verified_transaction._attempt` `last_conflict` | Survived across attempts, so exhaustion after a final RPC-level conflict logged an EARLIER attempt's stale root. | **CHANGED.** Reset to `None` at each attempt's entry, so a stale root is never logged. |
| I-22 | `_txn` comments (retry-signal raise-site census, `TxnContentionExhaustedError` docstring, marker comment) | The prose described text-marker decisions. | **PROSE CHANGED.** Checked against code: the `RetryableConflictSignal()` raise sites are `_raise_attempt_failure`, 3× `bootstrap_session`, `scout.py` ×3, `inbox_awaiter.py` ×3, and the one bare raise in `_run_verified_transaction._attempt`. The comment matches the code. |
| I-23 | Gate `Registry.entry_for` (first match) in `partition_mypy` + the unsymboled-allowance leg | On a path registered by two bounds, only the first entry could admit or claim symbols. | **CHANGED.** `entries_for` (union): admission is `any(entry.admits(e))`, and "unsymboled" is judged against every sibling's symbols. No other `entry_for` caller remains (awk over `scripts/`: only the docstring and a test comment). The allowance COUNT leg still has the one-path-one-bound shape (F-11). |
| I-24 | `keeps.get_or_create_keyed` docstring/comment | Said a rejection "re-raise[s] (an unruled type, a ghost keeper)" after the re-read. | **PROSE FIXED** to match the HEAD→OLD narrowed door: only `TxnUniqueViolationError` re-reads. Checked against the code; they match. |

## 3. Per-fault walk (NEW; exit codes are the process return from `_dispatch`)

Common to every verb:
- **(ii) `SurrealConnectionError`:** passes every wrap and is caught by the I-1 handler. Output is `lore-adm: <msg>` on stderr, nothing on stdout, exit 1. Same as OLD.
- **(iv) `TxnContentionExhaustedError`:** passes every wrap (`wrap_store_rejection` passthrough) and is caught by the handler as a `SurrealStoreError`: stderr, exit 1. **OLD:** a traceback for every verb except report-unmigrated.
- **(v) `close()` raising during fault handling:** `_safe_close` swallows `(OSError, SurrealError, WebSocketException)`, so only a non-SDK exception from a connection's `close()` could escape. If it did:
  - a tuple class would mask the original fault (F-8);
  - any other class would produce a traceback carrying the original as `__context__`.
- **`ensure_ready` DDL rejection:** a raw `SurrealStoreError` → stderr with the driver label + hint, exit 1. **OLD:** a traceback, except for report-unmigrated.

| Verb | (i) `SurrealStoreError` (domain/engine rejection) | (iii) domain refusal | Partial write possible? | Faults the operator cannot tell apart |
|---|---|---|---|---|
| `add` | `create` wrapped → "could not create principal …: a principal with that email or subject already exists" for **any** rejection (F-13) | — | no (single CREATE) | a UNIQUE clash vs an ASSERT/type rejection print the same "already exists" |
| `list` | raw read → label + hint, exit 1 (OLD: traceback) | — | no | — |
| `delete` | whole-verb wrap → "could not delete principal 'e'", exit 1 (OLD: traceback) | NotFound / HasKeeps / OwnsGovernedRows → their own teaching text, exit 1 | no: the guards run before the cascade, and the cascade is one transaction. A transport fault AT commit is ambiguous (pre-existing). | keep-read rejection, `INFO FOR DB` rejection, owned-count rejection, **owned-count malformed** (group_all_count's reason is never printed or logged), key-count rejection and cascade rollback all print ONE line (F-3). Success line `deleted e (N key(s) removed)`: N can be a silent 0 (F-1). |
| `suspend` / `unsuspend` | wrapped → "could not set status of principal …", exit 1 (OLD: traceback) | NotFound → exit 1 | no | engine rejection vs any other `SurrealStoreError` subclass (e.g. `TxnParamCollisionError`): same line |
| `set-expiry` | wrapped, both branches (OLD: traceback) | NotFound | no | as above |
| `mint-key` | wrapped → "…a key with that name already exists … (or the credential hash collides)" for ANY rejection (F-13). The credential is printed only after a successful mint. | NotFound | no | UNIQUE vs other rejection |
| `revoke-key` | UPDATE wrapped → "could not revoke key …"; `_require_principal_id` read rejection → raw label + hint | PrincipalNotFound / PrincipalKeyNotFound | no | — (the two steps produce distinct texts) |
| `list-keys` | raw read → stderr (OLD: traceback) | NotFound | no | — |
| keep verbs (create-keep, add/remove-household, set-rank, set-keeper, delete-keep) | writes wrapped as `KeepStoreError` (8 wrap sites in `keeps.py`; bodies not re-read); reads raw → stderr (OLD: traceback, per D1) | KeepNotFound / KeeperLockout / `--name` ValueError | not assessed per verb (NOT TRIED) | — |
| `migrate-governed` | raw `run_query` rejection (label + hint) or `group_all_count`/`_governed_select` shape error → stderr, exit 1 (OLD: traceback) | `REFUSED: <reason>` on stderr, exit 1 (in-frame, before any write) | **yes:** the project keep may be minted before a later failure (documented). **The backfill UPDATE can commit and then the leftover-count read fails** → exit 1 with no receipt (F-5). `_rows_stamped` `TypeError` after a committed UPDATE → traceback (F-6). | a post-commit failure reads the same as a pre-write failure |
| `report-unmigrated` | raw rejection or `group_all_count` shape error → stderr, exit 1 (OLD: same for a rejection; a malformed count was a **silent 0**) | — | no (read) | — |

**Could a fault print success?** Not reachable as far as I found.
- Every stdout success line (`deleted …`, `mint-key`'s credential, `create-keep`'s id, migrate's receipt) is printed after the write and before the closes, and the closes swallow every realistic exception.
- Refusals are checked before the `table_defined is False` "nothing to migrate" success line.
- The nearest miss is F-1: a success line carrying a count that may come from a default.

## 4. Findings

**F-1 — MINOR. `PrincipalStore.delete`'s served key-cascade count still falls back to 0.**
- **CLASS:** every served count that comes from a `GROUP ALL` read is fail-closed (a wrong-shaped answer is never read as 0).
- **Where:** `principals.PrincipalStore.delete`: `cascaded = int(count_rows[0].get("count", 0)) if count_rows else 0` via `_as_rows` (non-list → `[]`). `_cmd_delete` prints it as `deleted e (N key(s) removed)`.
- **Scenario:** the driver answers the key count in any shape other than `[{"count": int}]`, e.g. a dict. The cascade then deletes K keys, and the audit line reads `(0 key(s) removed)`. That is a served count describing no set.
- **Context:** the owned-row count one statement above WAS moved onto `group_all_count` in this diff, and the reader's docstring says the rest is routed to 64b.
- **SIBLINGS TRIED:** the 4 `group_all_count` callers (`_scope_count`, the message leftover, the delete owned-count, `report_unmigrated_governed_rows`), all fail-closed.
- **SIBLINGS NOT TRIED:** these each have their own extractor, which I did not read:
  - `findings.py` (count extractor near `_FILED_SINCE_PARAM`);
  - `tasks.py` (extractor near `_UPDATED_SINCE_PARAM`);
  - `messages.py` (the `count()…GROUP ALL` scalar reader and the `to`-edge count);
  - `diff.py` (`SNAPSHOT_TABLE` count);
  - `store/surreal.py` (the chunk count extractor);
  - `index/surreal_manifest.py` (`_COUNT_ALIAS` reads).

**F-2 — NIT (prose). `governed.group_all_count` states a false universal.**
- **CLASS:** docstrings describe behaviour the code has.
- **Where:** the docstring says "Every ``GROUP ALL`` count read calls THIS function rather than re-deciding the shape". Two sentences later it concedes "the rest of the sweep is routed to 64b". F-1 is a counter-example in the same module family as the callers it lists.
- **Fix:** "every count read *listed below*".
- **SIBLINGS TRIED:** the caller census matches the 4 named callers exactly.
- **SIBLINGS NOT TRIED:** none.

**F-3 — MINOR. `delete`'s whole-verb wrap collapses 6 distinct store faults into one message, and hides the fail-closed reader's reason.**
- **CLASS:** an operator-visible store failure says which step failed and why, or at least that the reason is logged.
- **Where:** `PrincipalStore.delete` under `wrap_store_rejection(PrincipalStoreError, "could not delete principal …")`, plus `wrap_store_rejection`, which builds `domain_error(context)` only (ledger #31).
- **The six faults:**
  1. keep-read rejection;
  2. `_table_exists` (`INFO FOR DB`) rejection;
  3. owned-count rejection;
  4. **owned-count malformed**;
  5. key-count rejection;
  6. `TxnDomainRejectionError` from the cascade.
- **Why it matters:** all six print `lore-adm: could not delete principal 'e'`. For (4), `group_all_count` raises WITHOUT logging and the query itself succeeded, so its reason ("…answered a dict without an integer `count` — nothing was decided from it") reaches no surface at all. It lives only in `__cause__`, which the handler never prints.
- **No partial write:** none of the six can leave a partial write.
- **SIBLINGS TRIED:**
  - `report-unmigrated` and `migrate-governed`: unwrapped, so the reason IS printed;
  - `set_status` / `set_expires` / `revoke`: single statement, so less ambiguous.
- **SIBLINGS NOT TRIED:**
  - `keeps.get_or_create_keyed` (same whole-verb shape);
  - whether `run_query` logs rejections at a level that lore-adm's (unconfigured?) logging shows. I am MEDIUM-confidence that Python's `lastResort` handler would surface WARNINGs on stderr.
- **Decision for the operator:** print `__cause__`'s message on the handler line, or accept this.

**F-4 — MINOR. `unsound_sender_messages` measures a superset of what its label and the stderr sentence claim.**
- **CLASS:** a served count describes the set its label names (Leg-1 scope diff).
- **Where:** `principals._migrate_message_owner` (the leftover `run_query`) and `_dispatch_migrate_governed` (the stderr sentence "their sender has no owner or scope").
- **Question actually answered:** "how many message rows have `scope IS NONE AND owner_principal IS NONE` at a moment AFTER the UPDATE". The UPDATE and the count are two separate statements, not one transaction.
- **Scenario:** a pkt-62–63b-image writer (or any legacy path) inserts a NONE-scope message whose sender is SOUND between the UPDATE and the count. That row is counted and attributed to "sender has no owner or scope", and the remedy printed ("re-run after `--table agent`") does not apply to it.
- **Also mis-described:** the same over-claim is in the `MigrateGovernedResult` docstring ("LEFT un-migrated because their sender has no owner or no scope").
- **Options:** relabel as "remain un-migrated (commonly: sender without owner/scope)", or add the negated soundness predicate to the count. The second would then let concurrent sound-sender rows go uncounted, so it moves the silent fate rather than removing it.
- **SIBLINGS TRIED:** the half-pair rows (`scope NONE, owner_principal NOT NONE`) are refused before the UPDATE (`_message_leg_refusal`), so they are not a silent fate.
- **SIBLINGS NOT TRIED:** the agent leg has no leftover measurement at all. Its UPDATE `WHERE scope IS NONE AND owner_principal IS NONE` has no skip clause, so there is no skip set, but concurrent inserts are equally unmeasured.

**F-5 — MINOR. A fault after a committed backfill reads the same as a fault before any write.**
- **CLASS:** a failure after a committed write says that the write landed.
- **Where:** `_migrate_message_owner`. The backfill UPDATE commits, then the leftover `run_query` is rejected or `group_all_count` raises. Result: stderr `lore-adm: the governed message-owner leftover count read answered … — nothing was decided from it` (or the label + hint), exit 1, and **no `backfilled=N` receipt.**
- **Why it matters:** "nothing was decided from it" reads as "nothing happened" while N rows were stamped. The migration is idempotent, so a re-run reveals the state (`already_migrated`), and that is why this is MINOR rather than MAJOR.
- **SIBLINGS TRIED:** `_rows_stamped` after each leg's UPDATE (F-6).
- **SIBLINGS NOT TRIED:** the memory leg's post-UPDATE steps. The diff showed none beyond `_rows_stamped`.

**F-6 — MINOR. Two policies for "the driver answered in the wrong shape".**
- **CLASS:** ONE fail-closed error class for wrong-shaped driver answers.
- **The two policies:**
  - `group_all_count` and `_governed_select` raise `SurrealStoreError`, which is laundered to stderr + 1.
  - `principals._rows_stamped` raises `TypeError`, which is outside the handler tuple, so it tracebacks. It fires AFTER the backfill UPDATE has committed, in all three legs.
- **Contradiction:** the new `_dispatch` docstring says "Anything OUTSIDE the tuple (a `TypeError`, …) is a programming defect". `_rows_stamped`'s own docstring calls its `TypeError` "an SDK contract break". Both cannot be true.
- **SIBLINGS TRIED:** the three shape readers above.
- **SIBLINGS NOT TRIED:** `_as_rows` (a silent `[]` on a non-list). It is used by `revoke`, `set_*` and `delete`, where a non-list after an UPDATE would read as "NotFound" (pre-existing).

**F-7 — MINOR. `_governed_select` is fail-closed only on a non-list answer, and silently drops non-dict members.**
- **CLASS:** as F-6.
- **Where:** `principals._governed_select`: `[row for row in rows if isinstance(row, dict)]`. Its new docstring promises "a wrong-shaped dependency never decides a write".
- **Scenario:** a list containing non-dict rows reads as fewer precondition rows. For example, a dangling-sender or half-pair row could vanish from the refusal inputs, and the refusal would not fire.
- **SIBLINGS TRIED:** `group_all_count` raises on a non-dict first row, so the two are inconsistent.
- **SIBLINGS NOT TRIED:** none.

**F-8 — NIT (low reachability). The new close-before-handler nesting can replace the original fault with the close's.**
- **CLASS:** fault handling never loses the root cause.
- **Where:** `_dispatch` (inner `try/finally`), `_dispatch_migrate_governed`, `_dispatch_keep` and `_dispatch_report_unmigrated`, each with a `finally` inside the outer handler.
- **Change from OLD:** OLD printed the original first. NEW prints only whichever tuple-class exception the `finally` raised last.
- **Reachability:** the `close()` → `_safe_close` swallow of `(OSError, SurrealError, WebSocketException)` makes this practically unreachable today. Also pre-existing: the first close that raises skips the remaining closes.
- **SIBLINGS TRIED:** all four dispatch frames.
- **SIBLINGS NOT TRIED:** none.

**F-9 — NIT (operator decision). Exit code 1 for everything.**
- **CLASS:** a script can tell a retryable fault from a refusal.
- **Where:** the handler's "only return is `1`". `SurrealConnectionError` and `TxnContentionExhaustedError` (retry later) share exit 1 with refusals and engine rejections (do not retry).
- **Context:** pre-existing, but the diff made this the ONE handler, so it is the natural place to decide.
- **SIBLINGS TRIED:** all verbs.
- **SIBLINGS NOT TRIED:** none.

**F-10 — NIT (prose). The `Raises:` sections of the four newly wrapped methods do not list the wrap error.**
- **CLASS:** docstrings name every raised class.
- **Where:** `PrincipalStore.set_status`, `set_expires` and `delete`, and `PrincipalKeyStore.revoke`. None names `PrincipalStoreError` / `PrincipalKeyStoreError` or the transport/contention pass-throughs. By contrast, `keeps.get_or_create_keyed` (rewritten in this diff) lists all three.
- **Also pre-existing:** `_txn._domain_rejection_error`'s docstring says "`TxnGovernedConflictError` iff … else `TxnDomainRejectionError`" but omits the `TxnUniqueViolationError` branch its code has.
- **SIBLINGS TRIED:** the 4 methods above.
- **SIBLINGS NOT TRIED:** the other 11 wrap sites.

**F-11 — MINOR (fails closed). The gate's unsymboled-allowance COUNT leg still assumes one path, one bound.**
- **CLASS:** every per-path registry read partitions by sibling (the am-14 class the diff fixed at `entries_for`).
- **Where:** `pending_contract_gate.transcript_self_destruct_findings`.
- **Scenario:** bounds A and B both register path P, each with `unsymboled_codes=[{code: X, count: 1}]`. mypy shows 2 unsymboled X errors. Each entry counts `unsymboled_seen = 2` against its own `count = 1`, so there is a false `SELF-DESTRUCT` on both.
- **Same shape:** the "produced NO mypy errors" leg, for an entry whose own errors are gone while a sibling's remain on the path, but only when the entry has no symbols and shares the code.
- **Admission is fine:** `partition_mypy` uses `any(admits)`, so it cannot over-refuse.
- **Severity:** fails loud (a false RED), never a false clear.
- **SIBLINGS TRIED:** `partition_mypy`, the symbol leg and the allowance leg.
- **SIBLINGS NOT TRIED:** the pytest partition and the `--currency` render paths.

**F-12 — NIT. An untypeable per-statement `ERR` entry loses its typed meaning.**
- **CLASS:** a parse failure degrades loud, never into a different decision.
- **Where:** `_txn._parse_failed_statement`. On `AttributeError` / `TypeError` / `RecursionError` the entry becomes `typed=None`. Consequences:
  - A malformed entry that was a `TransactionConflict` is NOT retried; it raises as a domain rejection. That is loud and acceptable.
  - A malformed UNIQUE violation becomes `TxnUniqueViolationError` only if `_classify_engine_error`'s text leg can yield the unique label (NOT TRIED). If it cannot, `keeps.get_or_create_keyed`'s narrowed CAS door (`except TxnUniqueViolationError`) skips the winner re-read and surfaces a `KeepStoreError` to a concurrent loser. The shapes involved are unobserved on 3.2.4, and the WARNING log names the index.
- **SIBLINGS TRIED:** the retry predicate.
- **SIBLINGS NOT TRIED:** the text ladder's unique label.

**F-13 — MINOR (pre-existing, same class as HEAD→OLD K1). Three wrap contexts assert a specific cause while catching every `SurrealStoreError`.**
- **CLASS:** a wrap's message names only what is known.
- **Where:**
  - `PrincipalStore.create`: "…a principal with that email or subject already exists";
  - `PrincipalStore.set_subject`: "…that subject is already bound to another principal";
  - `PrincipalKeyStore.mint`: "…a key with that name already exists … (or the credential hash collides)".
- **Scenario:** an ASSERT or type rejection, a `TxnGovernedConflictError` or a `TxnParamCollisionError` prints "already exists". The typed `TxnUniqueViolationError` now exists and could narrow these, exactly as the keeps CAS door was narrowed.
- **SIBLINGS TRIED:** the four new wraps (set_status, set_expires, delete, revoke), which all use neutral "could not …" texts.
- **SIBLINGS NOT TRIED:** the eight `keeps.py` wrap contexts.

**F-14 — NIT (prose vs code). Wrap-scope policy is described one way and implemented two ways.**
- **CLASS:** docstrings describe the policy the code has.
- **Where:** `_dispatch_keep`'s new docstring says "wrapping is a WRITE-boundary property; `ensure_ready` and the keep reads are un-wrapped by design".
- **Counter-examples:** in this same diff, `PrincipalStore.delete` wraps its reads (`get_by_email`, keep read, `_table_exists`, both counts), and so does `keeps.get_or_create_keyed`. `revoke` wraps only its write.
- **SIBLINGS TRIED:** delete, revoke, set_*, get_or_create_keyed.
- **SIBLINGS NOT TRIED:** the other keeps wraps.

**F-15 — MINOR (pre-existing, adjacent hunk). `report-unmigrated --table` is unvalidated before I/O and is interpolated into the statement.**
- **CLASS:** every governed verb validates its table before any I/O.
- **Where:** `governed.report_unmigrated_governed_rows`: `f"SELECT count() FROM {table} WHERE scope IS NONE GROUP ALL"`. `migrate-governed` refuses a table outside `_MIGRATE_VALID_TABLES` with zero I/O; `report-unmigrated` does not.
- **Under the honest-operator threat model:** a typo becomes an engine rejection, which is loud and fine.
- **Beyond it:** store-ref §"statement[0]-only validation" means a `;`-joined argument runs extra statements. The actor is the operator only, so this is hygiene, not a boundary.
- **Stale prose in the same function and its parser:** the docstring still says "STUB / runnable-RED … The builder fills the body", and the `--table` help says "(63a supports: memory)".
- **SIBLINGS TRIED:** migrate-governed validation.
- **SIBLINGS NOT TRIED:** none.

**F-16 — NIT. Two receipt/default notes.**
- **Receipt format:** `migrate-governed`'s stdout receipt now always carries `unsound_sender_messages=None` for memory/agent. This is an additive format change for any line-parser. No in-tree parser was checked (NOT TRIED).
- **Default:** `MigrateGovernedResult.unsound_sender_messages` keeps a `None` default "ONLY because a closed contract pin constructs this result without the field". That is a production default justified by a test, on a field the CLI branches on (`if result.unsound_sender_messages:`). It is mitigated: all 8 production constructions state it explicitly (checked).
- **CLASS:** never default a value the code branches on.

## 5. NOT TRIED (at the 45-minute deadline)
- Per-verb bodies of the 8 `keeps.py` wrap sites.
- `_classify_engine_error`'s text leg for the unique label (F-12).
- Whether lore-adm configures logging, i.e. whether `run_query`'s rejection logs reach the operator (F-3).
- The sibling count extractors listed in F-1.
- Whether `MigrateGovernedResult.table_defined` is served anywhere besides the CLI.
- Any test run (forbidden by the brief).
