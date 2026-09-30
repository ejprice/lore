brief-base v18 read

# REPORT — blindreader-63c-i-a-5 (contract-blind diff read, wave 63c-i-a, fix5 → fix6.r5)

## SUMMARY BLOCK
- **State:** done-with-deviations. Findings: 0 BLOCKER, 2 MAJOR, 6 MINOR, 4 NIT. **Verdict on the verify path: no ALLOW door.** A wrong-shaped lookup is now a 500 (fail-closed), where it used to be a 401 no-such-key deny.
- **Deviations:** (D1) the brief's `cp -a old new` recipe hands `$S/new` the OLD tree's editable `.pth` (#140 poison mode 1). My first probe imported `old/loremaster` and the provenance print caught it. Re-run with `PYTHONPATH` pinned to the new tree, and the receipt was re-printed (§6). The diff itself is text and was not affected. (D2) The rename-consumer sweep's awk glob matched root `REPORT-*.md` files and returned per-file hit COUNTS only; no content was displayed or read (§4). No `docs/design` in any sweep.
- **Packages considered:** none — no mechanism specified (read-only grader). Noted for the owner: the new CLI handler does not route through the house `logging_setup.RedactingFilter` (F-2).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none. No production symbols were written. One probe script is pasted verbatim in §6.
- **Graded:** patch `bec29190…` (fix6.r5) vs `5f2d7c43…` (fix5), both applied on `5746de5` · HEAD-at-report: `80bb0f4` · DIFFERENT (1 behind: `80bb0f4` touches only `REPORT-lead-63c.md`, +4 lines, and no graded symbol moved).
- **Decisions needed:** (1) F-1: should `_set_columns` refuse, not narrow, when its parse ends unbalanced? It is latent today and live the day a leg's SET uses a subquery. (2) F-2: should the lore-adm stderr handler attach `RedactingFilter`? (3) F-3: post-commit shape faults say "nothing was decided from it" after the write landed. Fix the class, or accept it?
- **Receipt pointers:** inventory §1 · CLI table §2 · verify trace §3 · rename consumers §4 · findings §5 · probe + output §6.
- **Capability check:** grep/rg are hook-blocked, so awk/sed/diff were used throughout. lore indexes the main tree, not my scratch trees, so I read the code from the trees directly (structure fallback stated per brief-base §4; no friction filed, because this is the brief-mandated mode). I ran no test suite.

---

## 0. Setup receipts (measured 2026-09-30)
- The md5s match the brief: fix5 `5f2d7c4366d469e5c2a34d53aa235d6e`, fix6.r5 `bec291900a49c2e5df0704ef912fd5b9`.
- Old tree: `scripts/scratch_copy.sh $S/old` passed provenance, then reset/clean/apply → OLD-OK. New tree: `cp -a` old → reset/clean/apply → NEW-OK.
- Production diff (`diff -ruN -x __pycache__ old/loremaster/loremaster new/loremaster/loremaster`): 1173 lines, 3 files (`governed.py`, `principal_keys.py`, `principals.py`).
- Store-ref diff: +22 lines. This is a new §1.9, with two probed facts about schema-behind stores.

## 1. Removed/changed-behaviour inventory
Fates are given per answer shape: (i) well-formed, (ii) empty `[]`/`{}`, (iii) wrong-shaped (non-list / non-dict / non-dict member).

| # | Site (symbol) | Change | (i) well-formed old→new | (ii) empty old→new | (iii) wrong-shaped old→new |
|---|---|---|---|---|---|
| 1 | `governed.rows_of` (NEW) | the one row-list reader | returns the list | `[]` | raises `SurrealStoreError` "the {noun} read answered a X … nothing was decided from it" |
| 2 | `governed.map_of` (NEW) | the one INFO-map reader; `required=` keys | returns the dict | `{}` passes unless a key is `required` (then raises) | non-dict, or a present `tables`/`fields` that is not a dict → raises |
| 3 | `governed.guarded_write` pre-read | `isinstance…else []` and `rows[0] if dict else {}` → `rows_of` | same | same (row absent) | OLD: a non-list was read as ROW ABSENT, and a non-dict first member became `{}`, so the PDP decided on an empty row (a fail-open shape). NEW: raises. **Closes a door.** |
| 4 | `PrincipalKeyStore._as_rows` | filter → `rows_of(noun="principal-key query")` | same | same | OLD `[]` → `verify` "no-such-key" deny, `revoke` NotFound. NEW raises (§3) |
| 5 | `PrincipalStore._as_rows` (also KeepStore's reader) | filter → `rows_of(noun=` default `"principal-substrate query")` | same | same | OLD `[]` → `create` "vanished immediately after it was created", `set_*` → `PrincipalNotFoundError`, `get_*` → None. NEW raises raw `SurrealStoreError`. The post-write reads sit OUTSIDE the wrap (F-3) |
| 6 | `PrincipalStore._table_exists` | → `map_of(required=("tables",))` | same | `{}`: OLD False → NEW raises | OLD False, so `delete` SKIPPED the SF-63-5 owned-row guard (fail-open). NEW raises, inside delete's wrap → `PrincipalStoreError` |
| 7 | `PrincipalStore.delete` cascaded-key count | `int(rows[0].get("count",0))` → `group_all_count` | same | 0 → 0 | OLD: `"3"` coerced to 3, `{"count":None}` → TypeError traceback, non-list → 0. NEW raises → wrapped `PrincipalStoreError` |
| 8 | `_governed_select` | own non-list raise + silent member filter → `rows_of` | same | same | a non-list raised before (same class), but a non-dict MEMBER was silently dropped. NEW raises |
| 9 | `_agent_migration_preconditions` INFO FOR DB | own check → `map_of(required=tables)` | same | `{}` raised before; still raises | OLD `{"tables": []}` was accepted (a list); NEW raises |
| 10 | `_agent_migration_preconditions` INFO FOR TABLE (NEW read) | one read, only when `table in defined` | `defined_fields` = the field keys | `{}` → raises (`fields` required) | raises |
| 11 | `_set_columns` / `_schema_predates_refusal` (NEW) | pre-boot schema gate, FIRST action of the memory, agent and message legs | shipped statements parse correctly (§6) | — | a leg statement outside the grammar can silently NARROW the set (F-1) |
| 12 | memory/agent/message legs: ordering | the schema gate now runs before operator resolution, the keep mint, counts and the message row-refusal | a healthy store is unchanged | — | a schema-behind store is now REFUSED with teaching text, where it used to write silently over 0 rows or raise `InternalError` over ≥1 |
| 13 | `_rows_stamped` | `TypeError` → `rows_of` (`SurrealStoreError`); `noun` required | `len` | 0 | OLD: a non-list gave a TypeError **traceback**, and `[None]` counted as 1 stamped row. NEW raises the laundered class. The write has already landed (F-3) |
| 14 | message leg leftover read | now wrapped: `PrincipalStoreError("the backfill landed (N …) but the leftover count read failed")` | same | 0 | raises; the stderr line names the landed write |
| 15 | `MigrateGovernedResult.unsound_sender_messages` → `messages_left_unmigrated` | rename; the semantics are widened in prose ("superset") | — | — | — |
| 16 | CLI receipt line | key `unsound_sender_messages=` → `messages_left_unmigrated=` | stdout format change (§4) | | |
| 17 | CLI leftover stderr sentence | "were not migrated: their sender has no owner…" → "remain un-migrated after the backfill — commonly…; a row inserted during the run is counted here too" | | | |
| 18 | `_dispatch` fault print | `f"lore-adm: {error}"` → `_fault_line(error)`: plus one `  ← caused by: <str>` line per `__cause__` | | | (§2) |
| 19 | `main()` | wrapped in `_cli_logging()`: a WARNING stderr handler on `loremaster`, which renders `error_class`/`engine_error` extras | | | (§2, F-2) |
| 20 | wrap contexts (principal create, bind subject; key mint) | the reason clauses ("already exists…", "already bound…", "hash collides") are removed; the context is neutral and the reason now comes from the cause chain | | | |
| 21 | `migrate-governed` invalid `--table` | validated in the dispatcher before any store is built (it was inside `migrate_governed`, after the store build and `ensure_ready`) | | | |
| 22 | `report-unmigrated` `--table` | OLD: **no validation at all**, and the name was interpolated into the SELECT (operator-only injection). NEW: `_is_governed_table`, before any I/O | | | |
| 23 | `--table` help (both verbs) | "(63a supports: memory)" → derived "one of: agent, memory, message, brief" | | | |
| 24 | migrate refusal render | `_render_migrate_refusal`: `sanitise_line(table)`; the reason is unsanitised (constant or reason-built) | | | |
| 25 | docstrings (governed module, `GovernedAuditRequired`, `group_all_count` scope, `report_unmigrated_governed_rows`, the `Raises:` blocks, `_dispatch_keep`) | prose; checked in §5 F-P | | | |

## 2. CLI error surface (NEW, fix6.r5)
Order on stderr: the log line is emitted at the moment the seam raises, so it comes BEFORE the fault lines. The fault line is `lore-adm: <error>`, then `  ← caused by: <str(cause)>` for each link.

| verb | (i) raw `SurrealStoreError` + engine detail | (ii) wrapped domain fault with cause | (iii) connection fault | (iv) schema-behind store | (v) invalid `--table` |
|---|---|---|---|---|---|
| migrate-governed | stderr: `governed.<x>.rejected [error_class=…; engine_error=<RAW engine text>]` · `lore-adm: SurrealDB <noun> rejected against 'ws://…' (<class>); see the server log…` · `  ← caused by: <RAW engine text again>` · exit 1 (NIT N-1: printed twice) | message leftover: `lore-adm: the backfill landed (N message row(s) stamped) but the leftover count read failed` + cause lines · exit 1 | `lore-adm: SurrealDB … failed against 'ws://…': <sdk err>` + `← caused by: <sdk err>` · exit 1 (no seam log record; `_raise_attempt_failure` logs only fate 3) | `lore-adm: migrate-governed --table memory REFUSED: the \`memory\` table has no \`scope\` column(s) — … boot the new image once …, then re-run migrate-governed` · exit 1. **But principal+keep `ensure_ready` DDL already ran** (NIT N-3) | `lore-adm: migrate-governed --table <sanitised> REFUSED: migrate-governed does not support table '<sanitised>' — …; nothing was read or written` · exit 1 · no store built (config IS loaded first) |
| report-unmigrated | same shape as (i) | n/a (no wrap on this path) | same as (iii) | not gated: counts every row where the `scope` field is absent (`scope IS NONE` on an undefined field) and emits the WARNING remedy. That is truthful for memory/agent/message. For `brief` the remedy names a verb that REFUSES `brief` (F-5) | `lore-adm: report-unmigrated does not support table '<sanitised>' — the governed tables are …; nothing was read` · exit 1 |
| keep verbs | (i) as above. A wrong-shaped answer is now a raw `SurrealStoreError` naming "principal-substrate query" (F-6) | `KeepStoreError` + cause chain | as (iii) | n/a | n/a |
| principal/key verbs | (i) as above | e.g. `lore-adm: could not create principal 'x'` · `← caused by: SurrealDB principal query rejected … (unique_violation); see the server log…` · `← caused by: <engine text naming the index + VALUE>` · plus the log line. The old "a principal with that email … already exists" sentence is gone; the reason is now the class token plus the raw engine text | as (iii) | n/a | n/a |

**Repeated `main()` in one process:**
- `_cli_logging` removes any stale `_CliStderrHandler`, adds one bound to the CURRENT `sys.stderr`, and removes it in `finally`. So handlers do not duplicate, and nothing writes to a dead stream. It does not touch the root logger, and `propagate` stays True.
- When NO handler is configured anywhere (the standalone lore-adm case), OLD printed WARNING+ records through `logging.lastResort` (message only). NEW prints through the handler, with extras. There is no double print, because lastResort fires only when no handler is found.
- If the ROOT logger has a stderr handler, every record prints TWICE: once plain from root, once with extras from the CLI handler (NIT N-2). This happens under a `basicConfig` host, or a test's root capture.
- If `logging_setup.configure_logging` has run in the same process (a server process), it resets `loremaster` handlers and sets `propagate=False` there. A later `main()` then ADDS a second, unredacted stderr sink beside the redacted JSON one (F-2).

**Secrets to stderr:**
- The CLI handler has NO `RedactingFilter`, and `_fault_line` prints `str(cause)` raw.
- The seam's own comment (`store/_txn.py`, module logger comment) says an ASSERT/coercion rejection "can echo a bound VALUE back verbatim". That value now lands on stderr twice.
- For the key-mint path the bound CONTENT includes the credential **hash** (sha512 of the presented `<name>:<secret>`). A UNIQUE/ASSERT rejection on `hash` would print it.
  - The plaintext secret is never bound to the store, so it cannot leak this way.
  - A hash collision is astronomically unlikely. A schema-behind ASSERT on `hash` is the realistic door. HIGH confidence that the path exists, LOW that it fires.
- A connection string with credentials would not be scrubbed either. I did NOT verify whether the store URL can carry userinfo (NOT TRIED).

**Newline / forgery:**
- Engine text and cause text are unsanitised on stderr. Measured: a cause containing `\nlore-adm: migrate-governed --table memory: scanned=0 …` renders as a forged receipt-shaped line (§6).
- SurrealDB parse errors are multi-line by nature.
- Attacker control is limited to values an engine error echoes. Most are operator-supplied, but stored agent-written values can reach an engine message in the migrate legs (NOT TRIED to construct one).

## 3. Token-verify path trace
Chain: `LoreTokenVerifier.verify_token` (token_verifier.py) → `PrincipalKeyStore.verify` → `_as_rows(SELECT … WHERE hash = $h)` → `rows_of`.

1. **Blank or colon-less credentials** are denied BEFORE any store read (`is_blank`, `parse_credential`), so a Google bearer never reaches the raising read.
2. **Wrong-shaped lookup answer:**
   - OLD: `[]`, so `_deny("no-such-key")` → None. For `verify_token`: the Google branch if one is configured, else None → **401**.
   - NEW: `SurrealStoreError` propagates out of `verify` and `verify_token`, so the Google branch is never tried.
   - The installed stack does not catch it: `mcp.server.auth.middleware.bearer_auth.BearerAuthBackend.authenticate` has no try, and starlette's `AuthenticationMiddleware.__call__` catches only `AuthenticationError`. Starlette's server-error middleware therefore returns **500** (generic body unless debug; I did not verify the debug flag in lore's app — NOT TRIED).
   - fastmcp's `MultiAuth`, which swallows and tries the next source, is not used. lore wires `LoreTokenVerifier` directly or via `RemoteAuthProvider`, whose `verify_token` delegates with no try.
3. **`get_by_email` / `get_by_subject` / `set_subject`** (the api-key owner lookup and Google `_admit`) take the same fate: OLD None → deny, NEW raise → 500.
4. **Non-dict member mixed with a valid row** (e.g. `[None, {row}]`): OLD filtered it out and could AUTHENTICATE on the surviving row. NEW raises. Strictly narrower.
5. **Verdict:** no caller turns the raise into an ALLOW. The caller now sees a 5xx rather than the missing-key 401 (a different deny). This is the intended fail-closed direction: a store fault is no longer disguised as a missing key. Internals reach the log, not the body (MEDIUM: debug flag unverified). A transport fault already took this 500 path before the diff, so nothing about it is new.

## 4. Receipt/format change consumers (`unsound_sender_messages=` → `messages_left_unmigrated=`)
Sweep: an awk over `*.py *.md *.yaml *.yml *.sh *.toml`, excluding `.venv`, `.git` and `docs/design`, in the NEW tree.
- **Production:** `governed.py` (2 hits) and `principals.py` (15). Every hit is the new name; the old name has 0 production hits.
- **Tests:** `test_principals_cli.py` holds the new name at two sites (lines 1382 and 1391). The old name appears once (`_RETIRED_FIELD = "unsound_sender_messages"`), as a deliberate retired-name pin, which is fine.
- **Scripts, YAML, skills, non-design docs:** 0 hits.
- **Root `REPORT-*.md`** (counts only, not read; D2): the old name appears in 6 reports. These are historical prose, not parsers.
- **Silent mis-parse risk:** no in-tree parser of the stdout line was found. An OUT-of-tree script keyed on `unsound_sender_messages=` would read "key absent", not a wrong value. There is no in-tree evidence that such a script exists. The stderr sentence also changed wording, so a grep on "were not migrated" would silently stop matching (NOT TRIED out-of-tree).

## 5. Findings

**F-1 · MAJOR (latent) · `principals._set_columns` / `_schema_predates_refusal`.** The schema gate's column parser silently NARROWS the required-column set when its SET clause is outside its grammar. The end regex `\s(WHERE|RETURN|TIMEOUT|PARALLEL)\s` is not depth-aware, and the loop never asserts `depth == 0` or an empty `current` at the end. Measured on `UPDATE brief SET a = 1, owner_principal = (SELECT VALUE x FROM y WHERE z = 1)[0] WHERE …`: it returns `('a',)`, and the gate with `defined_fields={'a'}` answers **None** (pass), although `owner_principal` is undefined. That is exactly the failure the gate exists to prevent (store-ref §1.9: silent over 0 rows). Its docstring promises "never a silently empty requirement", and it keeps that promise only for the empty case. The three shipped statements parse correctly (§6), so this is latent. It becomes live the day a leg (63c-ii's brief leg, say) writes a subquery or a keyword inside a value. `+=` yields column `'n +'`, which fails closed but gives a false teaching message.
- CLASS: a derived-requirement parser returns a subset, rather than refusing, on input outside its grammar. The property should be ∀ statement: parse is complete or raises.
- SIBLINGS TRIED: subquery with WHERE (narrows); `+=` (wrong name, fail-closed); a quoted comma (raises, good); a newline before WHERE (correct); lowercase `where` (correct, by luck of `partition`).
- SIBLINGS NOT TRIED: `RETURN` inside a function argument; `SET` inside a string literal before the real SET; `MERGE`/`CONTENT` forms (these presumably raise); unbalanced `)` in a string.
- Fix sketch, not applied: raise if `depth != 0` or `current` is non-empty at end-of-clause, and make the end-split depth- and quote-aware.

**F-2 · MAJOR · `principals._cli_logging` / `_CliLogFormatter` / `_fault_line`.** The new stderr log sink bypasses the house redaction seam `logging_setup.RedactingFilter`. It also deliberately renders `engine_error`, which `store/_txn.py` documents as able to "echo a bound VALUE back verbatim", and `_fault_line` prints the raw SDK cause. So lore-adm now prints unscrubbed engine text twice per rejection. On the key-mint path that includes the bound credential **hash**; bearer, `*_PASS=` and similar shapes are not scrubbed either. The audience is the operator's own terminal, and the docstring argues that deliberately. But a new sink that skips the ONE redaction implementation is a ROUTING-IS-NOT-SHARING instance, and `RedactingFilter` would not catch a bare hash anyway, so the argument for bypassing it covers only part of the risk. I rate it MAJOR on the class and MINOR on the concrete exposure; the operator should rule.
- CLASS: every log sink lore installs routes through `RedactingFilter`, and every CLI render of engine text routes through a scrub or sanitiser.
- SIBLINGS TRIED: the handler's filter list (empty); the `_fault_line` cause render (raw); `configure_logging`'s sink (filtered).
- SIBLINGS NOT TRIED: `index/cli.py` and other CLIs' handlers; whether the store URL can carry userinfo; the concrete SurrealDB 3.2.4 wording of a hash ASSERT failure.

**F-3 · MINOR · `rows_of` message used at post-COMMIT sites** (`_rows_stamped` in all three legs; `PrincipalStore.create`/`set_status`/`set_subject`/`set_expires`; `PrincipalKeyStore` mint (`_as_rows` after the CREATE) and revoke). A wrong-shaped answer to an already-executed write now raises "the {noun} read answered a X … — **nothing was decided from it**". The write, however, LANDED. §13 B F-5 fixed exactly this class for the leftover read only ("the backfill landed … but …"). Its siblings keep a message that implies no effect, and the post-write `_as_rows` calls sit outside the wrap, so the CLI shows a raw store error rather than a domain one. The old behaviour was worse ("vanished immediately after it was created" / `PrincipalNotFoundError` after a successful UPDATE), so this is an improvement that stopped at one instance.
- CLASS: a fault after a committed write must name the landed write.
- SIBLINGS TRIED: the 3 legs, 4 principal writes, 2 key writes (read in code).
- SIBLINGS NOT TRIED: KeepStore writes (`keeps.py` reads through `_as_rows` at 6 sites; not read individually).

**F-4 · MINOR · `principals._fault_line`.** There is no cycle guard on the `__cause__` walk, and a 2-cycle hangs forever. Measured: it did not return within 2 s (§6). The stdlib `traceback` module keeps a `_seen` set for exactly this. Reachability is low, since `raise … from` does not produce a cycle, but the CLI's LAST-resort fault renderer can hang. It also ignores `__context__`, so an implicit chain renders as a single line.
- CLASS: a chain walker must terminate on any object graph.
- SIBLINGS TRIED: the cycle case.
- SIBLINGS NOT TRIED: very deep chains.

**F-5 · MINOR · `report-unmigrated --table brief` vs `governed.report_unmigrated_governed_rows`'s WARNING.** `_is_governed_table` now explicitly blesses `brief` for report-unmigrated. A non-zero count then logs "run `lore-adm migrate-governed --table brief` to backfill", a verb that REFUSES brief until 63c-ii. The served prose names a remedy that the code refuses.
- CLASS: a remedy named in served prose must be executable for every member of the validator's domain.
- SIBLINGS TRIED: brief.
- SIBLINGS NOT TRIED: whether `brief` defines `scope` at all (if not, every brief row counts).

**F-6 · MINOR · `PrincipalStore._as_rows(noun=` default `"principal-substrate query")`.** No caller passes `noun`. So every principal read, every KeepStore read (6 sites in `keeps.py`) and every write's post-read report the same noun, and a keep fault says "principal-substrate query". fix6 removed exactly this default from `_rows_stamped` (commit `6cd4eb1`); the sibling kept it.
- CLASS: a raised message must name the read that failed.
- SIBLINGS TRIED: principals/keeps call sites (no `noun=`).
- SIBLINGS NOT TRIED: none.

**F-7 · MINOR · `_dispatch` docstring vs `_set_columns`.** `_set_columns` raises `ValueError` for "a programming defect", and `_dispatch`'s docstring says programming defects "are left to traceback". But `ValueError` IS in the handler tuple, so this defect is laundered into a one-line operator fault with exit 1.
- CLASS: fault class vs handler allowlist.
- SIBLINGS TRIED: `_set_columns`.
- SIBLINGS NOT TRIED: other ValueError raisers reachable from verbs.

**F-8 · MINOR · the brief's own recipe (not the diff).** `cp -a $S/old $S/new` carries the old tree's `.venv`, so any code run in `$S/new` imports `$S/old` (#140 mode 1; measured in §6, first run). Any agent handed this brief who EXECUTES in `new` without a provenance print grades the wrong tree.
- CLASS: every scratch tree asserts its own provenance.
- SIBLINGS TRIED: new.
- SIBLINGS NOT TRIED: other briefs of this wave.
- Fix: run `scratch_copy.sh $S/new` rather than `cp -a`.

**N-1 · NIT.** On a domain rejection the raw engine text is printed twice on stderr: once in the log line's `engine_error=`, once as the last `← caused by:` line.

**N-2 · NIT.** The handler leaves `propagate=True`, so a host with a root stderr handler prints each record twice.

**N-3 · NIT · prose.** `_render_migrate_refusal`'s docstring says "(a refusal wrote nothing)". But `_dispatch_migrate_governed` runs `principal_store.ensure_ready()` and `keep_store.ensure_ready()` (DDL) BEFORE `migrate_governed`, so on a schema-behind store the verb writes principal/keep DDL and THEN refuses. The governed tables are untouched. The word "nothing" over-claims.

**N-4 · NIT · prose (F-P sweep of diff docstrings).**
- Checked and consistent with the code:
  - the `governed.py` module docstring: THREE shape readers, and no other `isinstance(list|dict)` in `governed.py`/`principals.py` outside them (awk-bounded);
  - the `group_all_count` scope paragraph: 5 callers match the 5 found;
  - "report_unmigrated … ONLY caller is the lore-adm verb": 1 call site found;
  - the §13.2 ORDERING BOUND: the gate is the first statement after the imports in all 3 legs;
  - store-ref §1.9 matches the gate's shape.
- Residual: the `MigrateGovernedResult` docstring still says the `messages_left_unmigrated` `None` default exists "ONLY because a closed contract pin constructs this result without the field". That statement is about tests, which I did not verify.

**Fixed by this diff (recorded, not findings):**
- the `_table_exists` fail-open (inventory #6);
- the `guarded_write` empty-row PDP (#3);
- the `verify` mixed-member authenticate (§3.4);
- `report-unmigrated` table injection (#22);
- the `_rows_stamped` TypeError traceback (#13);
- the cascaded-count coercion (#7).

## 6. Probe (instrument pasted verbatim, per brief-base §1) + output
Run from the NEW tree: `PYTHONPATH=$N/loremaster:$N/lorerunes:$N/loresigil:$N/lorescribe uv run --no-sync python ../probe_set_columns.py`. The first run, without PYTHONPATH, printed `loremaster.__file__ = …/blind5/old/…` (D1/F-8).
```python
"""blindreader-63c-i-a-5 probe: _set_columns / _schema_predates_refusal / _fault_line / rows_of / map_of on
inputs outside the shipped statements. Run from the NEW scratch tree: uv run python ../probe_set_columns.py"""
import loremaster, loremaster.principals as p, loremaster.governed as g
print("loremaster.__file__ =", loremaster.__file__)
cases = {
    "shipped-memory": "UPDATE memory SET scope = $scope WHERE scope IS NONE",
    "shipped-agent": "UPDATE agent SET owner_principal = type::record('principal', $owner), owner_agent = id, scope = $scope WHERE scope IS NONE AND owner_principal IS NONE",
    "shipped-message": "UPDATE message SET owner_agent = sender, owner_principal = sender.owner_principal, scope = $scope WHERE scope IS NONE AND owner_principal IS NONE AND sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE",
    "subquery-WHERE-in-value": "UPDATE brief SET a = 1, owner_principal = (SELECT VALUE x FROM y WHERE z = 1)[0] WHERE scope IS NONE",
    "plus-equals": "UPDATE t SET n += 1 WHERE x",
    "string-with-comma": "UPDATE t SET note = 'a, b' WHERE x",
    "newline-before-WHERE": "UPDATE t SET a = 1\nWHERE x",
    "lowercase-where": "UPDATE t SET a = 1, b = 2 where c = 3",
}
for name, stmt in cases.items():
    try:
        print(f"{name}: {p._set_columns(stmt)!r}")
    except Exception as e:
        print(f"{name}: RAISES {type(e).__name__}: {e}")
print("gate subquery case, fields={'a'} ->", p._schema_predates_refusal("brief", cases["subquery-WHERE-in-value"], frozenset({"a"})))
a = RuntimeError("a"); b = RuntimeError("b"); a.__cause__ = b; b.__cause__ = a
import threading, sys
res = {}
t = threading.Thread(target=lambda: res.setdefault("out", p._fault_line(a)), daemon=True); t.start(); t.join(2)
print("fault_line on cause cycle returned within 2s:", "out" in res)
e = p.PrincipalStoreError("could not create principal 'x'")
e.__cause__ = RuntimeError("engine said\nlore-adm: migrate-governed --table memory: scanned=0 backfilled=0")
print("fault_line newline render ->", repr(p._fault_line(e)))
for v in ([], [{}], [{"a": 1}, None], {"a": 1}, None, "x"):
    try: print("rows_of", repr(v), "->", g.rows_of(v, noun="n"))
    except Exception as ex: print("rows_of", repr(v), "-> RAISES", type(ex).__name__)
for v in ({}, {"tables": {}}, {"tables": []}, {"fields": None}, [], None):
    for req in ((), ("tables",)):
        try: print("map_of", repr(v), req, "->", g.map_of(v, noun="n", required=req))
        except Exception as ex: print("map_of", repr(v), req, "-> RAISES", type(ex).__name__)
```
Output (2026-09-30, NEW tree at `5746de5` + bec29190):
```
loremaster.__file__ = …/scratchpad/blind5/new/loremaster/loremaster/__init__.py
shipped-memory: ('scope',)
shipped-agent: ('owner_principal', 'owner_agent', 'scope')
shipped-message: ('owner_agent', 'owner_principal', 'scope')
subquery-WHERE-in-value: ('a',)
plus-equals: ('n +',)
string-with-comma: RAISES ValueError: a SET item without `<column> =`: " b'" in "UPDATE t SET note = 'a, b' WHERE x"
newline-before-WHERE: ('a',)
lowercase-where: ('a', 'b')
gate subquery case, fields={'a'} -> None
fault_line on cause cycle returned within 2s: False
fault_line newline render -> "lore-adm: could not create principal 'x'\n  ← caused by: engine said\nlore-adm: migrate-governed --table memory: scanned=0 backfilled=0"
rows_of [] -> []   | rows_of [{}] -> [{}]   | rows_of [{'a': 1}, None] / {'a': 1} / None / 'x' -> RAISES SurrealStoreError
map_of {} () -> {} | map_of {} ('tables',) -> RAISES | map_of {'tables': {}} (both) -> ok
map_of {'tables': []} / {'fields': None} / [] / None (both) -> RAISES SurrealStoreError
```

## NOT TRIED (deadline-bounded, stated rather than omitted)
- Whether the store URL can carry userinfo (F-2 exposure).
- The debug flag of lore's Starlette app (the 500 body content).
- Out-of-tree consumers of the receipt line.
- KeepStore post-write sites, individually.
- Whether an agent-written stored value can reach an engine error in the migrate legs.
- The `brief` table's `scope` definition.
