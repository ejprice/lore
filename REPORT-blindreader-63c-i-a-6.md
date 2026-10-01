brief-base v18 read

# REPORT — blindreader-63c-i-a-6 (contract-blind diff read, wave 63c-i-a, r5 → r7)

## SUMMARY BLOCK
- **State:** done-with-deviations. **Deadline:** 40 min from 23:36 EDT 2026-09-30; report written at about 23:55. No item NOT TRIED.
- **Deviation 1:** the `scratch_copy.sh` copies arrived with an INCOMPLETE `.git/objects` (`git reset --hard HEAD` failed with `fatal: bad object HEAD`). In each copy I added `.git/objects/info/alternates` pointing at the main object store. That is read-only use of the main repo, and it mutated only my copies. After that, `reset --hard` + `clean -fd` + `git apply` succeeded. Provenance was printed in every probe; see §0.
- **Deviation 2:** lore indexes the main tree, not these patch trees, so every read was direct (awk/sed/diff/python AST). grep was never used (hook-blocked).
- **Packages considered:** none — no mechanism specified (read-only grader). Observation only: the SET-clause scanner is a hand-rolled SurrealQL lexer subset. I did not evaluate any SurrealQL parser package.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none (no symbols written).
- **Graded:** r7.full patch md5 `b15c06b0…` vs r5.full `bec29190…`, both applied on `d9b79be` · HEAD-at-report: `9e99fc2` · DIFFERENT (1 behind). The only intervening commit is `9e99fc2`, which touches only `REPORT-lead-63c.md` (not read). No graded symbol moved.
- **Verdict:** **no BLOCKER and no MAJOR.** There are 8 findings: 4 MINOR and 4 NIT. Under the operator cap they are all residuals.
  - The SET-clause parser now returns the exact set for every string, escape, bracket, subquery, `+=`/`-=` and case probe. It still returns a **SUBSET** for comments (`/* */`, `--`, `#`), `⟨…⟩` record ids, backtick values and a second `SET`. That is latent: no live leg statement contains any of those triggers (F1).
  - The `_LANDED_SHAPE_FAULT` text promises *"a re-run is idempotent"*. That is false for the CREATE/mint sinks (F2).
- **Decisions needed:** none blocking. Whether F1 and F2 get fixed now or are ledgered is the operator's call (both MINOR).
- **Receipt pointers:** §0 provenance · §1 inventory · §2 parser table (instrument in §A1) · §3 redaction table (§A2, §A5) · §4 domain table (§A3, §A4) · §5 dependency direction · §6 findings.

## 0. Trees & provenance
- `S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/c1b366dd-9add-4155-a131-d03a2c13dfa6/scratchpad/blind6`.
- Patch checksums verified: OLD (r5.full) = `bec291900a49c2e5df0704ef912fd5b9`; NEW (r7.full) = `b15c06b054e661ae9c591d1151ddc257`.
- Both trees were applied on `d9b79be`. Every probe printed its `loremaster.__file__`:
  - `…/blind6/old/loremaster/loremaster/__init__.py`
  - `…/blind6/new/loremaster/loremaster/__init__.py`
- Delta between the two trees:
  - Package files that differ: `governed.py`, `keeps.py`, `logging_setup.py`, `principal_keys.py`, `principals.py`, plus `scripts/restore_prod_dump.py`.
  - `docs/reference/surrealdb-31-capabilities.md` is **byte-identical** between r5 and r7 (an empty diff). Both trees carry the same change vs HEAD.
  - `agents.py`, `server.py` and `store/_txn.py` differ from HEAD but are identical between r5 and r7. They are outside this delta.

## 1. Changed-behaviour inventory (r5 → r7, derived from the diff)
| # | site (symbol) | old fate | new fate |
|---|---|---|---|
| 1 | `principals._set_columns` | Used a regex split on `\sSET\s` / `\s(WHERE\|RETURN\|TIMEOUT\|PARALLEL)\s` with paren-only depth. It was not quote-aware and was case-sensitive. Faults raised `ValueError`, which sits inside the lore-adm handler tuple, so the result was stderr + exit 1. | Uses the `_SetClauseScanner` single pass: quote/escape-aware, `()[]{}` on one stack, mismatched closers caught, keywords case-insensitive, `_SET_ITEM` validates `<ident> <op>= <value>`. Faults raise `GovernedStatementError` (a `RuntimeError`), which is **outside** the handler tuple, so the result is a traceback. This is deliberate per the docstring. |
| 2 | `governed.rows_of` | Had one read-wording template. | Adds `landed=` → `_LANDED_SHAPE_FAULT` ("…LANDED (committed)… a re-run is idempotent"). |
| 3 | `PrincipalStore._as_rows`, `PrincipalKeyStore._as_rows` | `noun` defaulted to `"principal-substrate query"` / `"principal-key query"`. | `noun` is REQUIRED (keyword-only, no default). 7 write sinks pass `landed=True`: principal create, status, subject, expiry; key mint, revoke; `_rows_stamped`. Every read names its noun. |
| 4 | `KeepStore` reads (6 sites) | Generic noun. | Named nouns. |
| 5 | `logging_setup._scrub_text` → `scrub_text` | Private; 4 patterns. | Public. A 5th pattern runs last: `_CREDENTIAL_HASH_RE` (128+ hex, non-hex-bounded). This affects **every** `RedactingFilter` sink, including the MCP server's `configure_logging` handlers. |
| 6 | `principals._cli_logging` | The stderr handler had no filter. | `RedactingFilter()` is attached, so the msg, args and every extra (`engine_error` included) are scrubbed. |
| 7 | `principals._fault_line` | Raw `str(error)` and `str(cause)`. The `__cause__` walk had no cycle guard: a cyclic chain looped forever. | Every line goes through `scrub_text`. A `seen` set over ids is added, so a cyclic chain terminates (probed: a 2-cycle renders 2 lines, §A5). |
| 8 | report-unmigrated `--table` domain | `_MIGRATE_VALID_TABLES` (agent, memory, message, brief). The refusal was printed in-frame with "…; nothing was read", exit 1. | `governed_tables()` = agent, brief, finding, memory, message, task. The refusal is raised as `GovernedTableRefusedError(ValueError)` → handler → `lore-adm: …` exit 1. The **"nothing was read" clause is gone** (F7). |
| 9 | migrate-governed `--table` validator | `_is_governed_table` (bool). | `_migrate_table_refusal` → `validate_governed_table` over `_MIGRATE_VALID_TABLES`. The domain is unchanged. |
| 10 | migrate invalid-table refusal text | Named "task/finding land at 64". | Pointers are derived only over `_MIGRATE_VALID_TABLES ∖ _MIGRATING_TABLES` = `brief`. **finding/task lost their pointer** (F5). |
| 11 | migrate dispatch | Had a `table ==` branch per leg, with a "not defined" branch for the 3 leg tables. | `_MIGRATE_LEGS` mapping + `_LegCall`. The order is now: `not in _MIGRATE_LEGS` → not-supported, then `not table_defined`. For `brief` the fate is the same as before. |
| 12 | `_not_supported(valid_table, table_defined=None)` | Rendered generic text. | Raises `AssertionError`. This is a new defensive branch with no reachable caller today. |
| 13 | `report_unmigrated_governed_rows` | Did no validation (caller-validated). Its remedy always named `migrate-governed`. | Validates internally. The remedy is derived: pending → reason + packet; leg-bearing → `migrate-governed`; otherwise "no migrate verb accepts …". **No path names a refusing verb** (§4). |
| 14 | report-unmigrated `--help` | Showed `_TABLE_HELP_DOMAIN`. | Shows `_report_table_help_domain()`, computed **at `build_parser()` time**. That runs every `generate_*_ddl` (F4). |
| 15 | `restore_prod_dump.py` | Had its own `PENDING_GOVERNED_TABLES` dict. Nodes came from test-tree `governed_node_tables`. | Consumes `loremaster.governed`. Relations still come from the test tree. The **slice is byte-identical** (15 tables, same provenance, both trees; §A4). |
| 16 | comment in `_migrate_message_owner` | "rows skipped because SENDER unsound". | Says the read also counts rows inserted during the run. This matches the stderr line printed by the dispatch. |

## 2. SET-clause parser probe (instrument §A1; 35 statements, each run in both trees)
| statement shape | r5 (old) | r7 (new) |
|---|---|---|
| baseline `a = 1, b = type::record('principal', $o) WHERE` | EXACT | EXACT |
| string containing `, WHERE ` | RAISE | **EXACT** |
| string with `)(` | EXACT | EXACT |
| `\'` escape + keyword in string | RAISE | **EXACT** |
| `"…"` string with `, RETURN` | RAISE | **EXACT** |
| nested `[1, {k: (2, 3)}]` | RAISE | **EXACT** |
| subquery `(SELECT … WHERE … LIMIT 1)` | **SUBSET `()`** | EXACT |
| `+=`, `-=`, `+?=` | WRONG (`'a +'`…) | EXACT |
| lowercase `set`/`where` | RAISE | EXACT |
| tabs/newlines | EXACT | EXACT |
| NBSP separators | EXACT | EXACT |
| unicode identifier `café` | EXACT | RAISE (ASCII-only `_SET_ITEM`; fail-closed) |
| `/* WHERE */` before a later item | SUBSET | **SUBSET `('a',)`** |
| `-- see WHERE below\n, b = 2` | SUBSET | **SUBSET** |
| `# RETURN note\n, b = 2` | SUBSET | **SUBSET** |
| `UPDATE t /* SET x = 1 */ SET a = 1, b = 2` | WRONG `('x','b')` | **WRONG `('x','b')`**: column `a` is lost and phantom `x` is added |
| comment containing a comma | RAISE | RAISE |
| `-- don't` (quote in comment) | EXACT | RAISE (unterminated) |
| `a = k:⟨x WHERE y⟩, b = 2` | SUBSET | **SUBSET** |
| `a = k:⟨x, b = 2⟩` | SUPERSET | SUPERSET (phantom `b`) |
| ``a = `x WHERE y`, b = 2`` | SUBSET | **SUBSET** |
| `SET a = 1 SET b = 2` | SUBSET | **SUBSET** |
| `UNSET`/`EXPLAIN` tail, `WHERE(` adjacent | EXACT | EXACT |
| dotted / backtick target, `==`, `,,`, trailing comma, unterminated, mismatched, no SET, SET only in string | old accepted 6 of these | **all RAISE** |

Coverage: the r7 scanner closes every string, escape, bracket, subquery and operator case. It leaves one residual class, **depth-0 text the scanner does not model as opaque**: comments, `⟨…⟩` and backticks.

Live exposure: an AST scan of every `UPDATE … SET` literal in `principals.py` (§A1b) found **0** live leg statements containing `--`, `/*`, `#`, `⟨` or a backtick. The exposure is latent (F1).

## 3. Redaction / CLI surface (instrument §A2, §A5)
| input to `scrub_text` | result |
|---|---|
| credential sha512 (128 lower) in an engine echo | REDACTED |
| content sha512 (`content_hash=<128>`, `digest <128>`) | **REDACTED**: over-redacts; this is the documented KNOWN BOUND |
| 129-hex run | REDACTED (the rule is `{128,}`) |
| 127-hex run, sha256 (64), git SHA (40) | UNCHANGED |
| UPPERCASE 128 | REDACTED |
| 128 split by `\n` (64+64) or by a space | **UNCHANGED**: under-redacts. The non-hex boundary makes each half 64 |
| `0x<128>`, `g<128>g`, `a_<128>_b` | REDACTED (the boundary is only non-hex) |
| two sha256 concatenated (=128) | REDACTED (indistinguishable by design) |
| fullwidth digits ×128 | UNCHANGED (the explicit ASCII class) |

Stderr per fault class (new tree):
- **Handler-tuple faults** (`PrincipalStoreError` / `PrincipalKeyStoreError` / `KeepStoreError` / `SurrealStoreError` / `ValueError` incl. `GovernedTableRefusedError`) render as `lore-adm: <scrubbed>`, plus `  ← caused by: <scrubbed>` per `__cause__`, with cycles terminated. Probed: a 128-hex engine echo became `***REDACTED***`, and a 2-cycle chain rendered 2 lines and exited.
- **`GovernedStatementError` / `AssertionError` / other** produce a Python traceback. That is outside the handler and unscrubbed, by design.
- **Library log records at WARNING+** go to the `_CliStderrHandler` → `RedactingFilter`, which scrubs them.
- **migrate refusal receipts** go through `_render_migrate_refusal` → `print(…)`, which is **NOT routed through `scrub_text`**. Probed with a 128-hex `--table`: the report refusal printed `'***REDACTED***'`, while the migrate refusal printed the raw 128 hex (§A3). The reasons are built only from counts, ids and table names, so no credential reaches this sink today. But the docstring claim of "one redaction for every sink" is false (F6).
- **migrate summary lines** (stdout, plus the `messages_left_unmigrated` stderr line) are unscrubbed. They contain counts only.

Effect of the `scrub_text` promotion on other sinks:
- Every `configure_logging` handler (the MCP server) now redacts 128+ hex runs everywhere.
- **Intended targets:**
  - `principal_key.hash` echoes;
  - `token_verifier`'s `sha512_hex(token)` key, if it is ever logged.
- **Collateral:**
  - Manifest, `file_text` and `snapshot_entry` rows carry file-level content sha512s (`store_read`, `diff.py`).
  - I found no logger or raise that interpolates such a VALUE. `store_read._integrity_error` takes only `(tier, path)`.
  - An engine-echoed rejection of a manifest write (an ASSERT/UNIQUE message quoting `sha512 = …`) would be redacted in the server log. That is a diagnostic-only loss, inside the stated bound.
- Siblings NOT tried: a live engine rejection of a manifest write, to see whether the engine echoes the value at all.

## 4. Governed-table domains (instrument §A3, §A4)
| table | `governed_tables()` | report-unmigrated | migrate-governed | migrate leg | report remedy (count>0) | restore slice |
|---|---|---|---|---|---|---|
| agent | ✔ (DDL) | ACCEPT | ACCEPT | ✔ | `run lore-adm migrate-governed --table agent` | derived |
| memory | ✔ (DDL) | ACCEPT | ACCEPT | ✔ | migrate-governed | derived |
| message | ✔ (DDL) | ACCEPT | ACCEPT | ✔ | migrate-governed (which may refuse on agent-first order; that refusal teaches the order) | derived |
| brief | ✔ (pending 63c-ii) | ACCEPT | ACCEPT (reads preconditions, then "does not yet migrate `brief` — lands at packet 63c-ii") | – | pending reason + packet | pending |
| finding | ✔ (pending 64b) | ACCEPT | REFUSE (zero I/O; **no pointer to 64b**, F5) | – | pending reason + packet | pending |
| task | ✔ (pending 64a) | ACCEPT | REFUSE (zero I/O; **no pointer to 64a**) | – | pending reason + packet | pending |
| briefed, to | ✘ (relations) | REFUSE | REFUSE | – | – | derived (relation) |
| blocks | ✘ | REFUSE | REFUSE | – | – | relation |
| principal, keep, member_of, audit, principal_key, finding_counter | ✘ | REFUSE | REFUSE | – | – | dependency |
| `AGENT`, `agent `, `agent\n`, `x';DROP`, 128×`f` | ✘ | REFUSE | REFUSE | – | – | – |

Remedy text:
- **No path names a refusing verb.** The `migrate-governed` remedy appears only for `_MIGRATING_TABLES`, which is derived from `_MIGRATE_LEGS` keys.
- `governed_tables() ⊇` every table either verb serves.
- The report domain ⊋ the migrate domain (finding, task), and that difference is explained by the remedy text.

Derivation:
- `ddl_governed_tables()` = {agent, memory, message} over 15 `generate_*_ddl` generators. `generate_ddl` is included, which duplicates its parts harmlessly.
- A liberal unanchored `DEFINE FIELD` scan gives the same set (0 anchored misses on today's DDL).
- The package DDL is byte-equal to the test-tree scaffold DDL (29192 chars).

Hostile DDL fed to `governed_node_tables_of`:
- comment-prefixed `DEFINE FIELD` → `[]`. That is a **SUBSET**, and it is inherited identically from the test-tree predicate (F3).
- backticked / `⟨⟩` table → the name **with its quotes** (`'`a`'`).
- lowercase, `IF NOT EXISTS`/`OVERWRITE`/`ON TABLE`, `;` in an ASSERT string → correct.
- `REMOVE FIELD` after `DEFINE` → still counted (the predicate is over DEFINEs only).

## 5. Dependency direction
- **`loremaster/loremaster/**` imports nothing from `scripts` or the test tree.** Checked by a first-token `from`/`import` scan, at module level and indented, over every package `.py`: 0 hits.
- **`scripts/restore_prod_dump.py` still depends on the TEST tree.** `_test_helpers()` inserts `loremaster/tests` into `sys.path` and imports `_surreal_harness`, `_governed_contract` and `_enforced_relations_scaffold`.
  - `SliceDeriver.__init__` calls it unconditionally, even when `emitted_ddl` is supplied.
  - Relations still derive from `_governed_contract.governed_relation_tables` over the scaffold DDL.
- **In the image:** the `Containerfile` COPYs `loremaster/` wholesale but **not `scripts/`**, so the script cannot run in the image at all. Its test-tree dependency is a dev-checkout requirement, unchanged in kind by this delta.
- The new consequence is narrower: node derivation (package) and relation derivation (test tree) now come from **two different DDL texts** (package generators vs scaffold). They are byte-equal today; nothing in the script asserts that.

## 6. Findings
**F1: SET-clause scanner returns a SUBSET (or the wrong set) for comments, `⟨…⟩` and backticks** · MINOR
- **Where:** `principals._SetClauseScanner` / `_set_columns` / `_keyword_at`.
- **What happens:** a clause keyword inside a comment, inside `⟨…⟩` or inside a backtick identifier is honoured at depth 0. So `/* WHERE */`, `-- … WHERE`, `# RETURN`, `⟨x WHERE y⟩` and ``` `x WHERE y` ``` truncate the clause, and a commented `SET` opens the wrong clause (`('x','b')`, losing `a`).
- **Why it matters:** the docstring says "COMPLETE OR RAISE, never a subset". `_schema_predates_refusal` consumes the set, so a dropped column is never checked against `INFO FOR TABLE`. Per the store-ref note in its own docstring, the UPDATE is then SILENT over zero rows and raises out of context over one or more.
- **Exposure:** latent. 0 live leg statements carry a trigger (§A1b). Under the honest-developer model, an inline `-- comment` in a leg literal is plausible.
- **CLASS:** *every depth-0 lexical region SurrealQL treats as opaque (comments, `⟨⟩`, backtick identifiers) must be opaque to the scanner, or the scanner must raise when it sees one.* An allowlist alternative: raise on any character outside a small safe set at depth 0.
- **SIBLINGS TRIED:** block/line/hash comments, `⟨⟩` with WHERE and with a comma, backtick value, a second `SET`, a comment before the top-level `SET`, a quote inside a comment.
- **SIBLINGS NOT TRIED:** `//` comments; nested `/* /* */ */`; `r"…"`/`s'…'`/`d'…'` prefixed strings (expected fine); a `$param` named `where`; `ONLY`/`IF` clauses after SET.

**F2: `_LANDED_SHAPE_FAULT` claims "a re-run is idempotent", which is false for the CREATE/mint sinks** · MINOR
- **Where:** `governed._LANDED_SHAPE_FAULT` / `_shape_fault`; callers `PrincipalStore.create` (`noun="principal create"`) and `PrincipalKeyStore.mint` (`noun="principal-key mint"`).
- **The UNIQUE indexes that make a re-run fail** (read from the generated DDL): `principal_email`, `principal_subject`, `principal_key_principal_name (principal, name)`.
- **Consequences:**
  - A re-run after a landed-but-misshapen `create` hits the UNIQUE email rejection.
  - After a landed mint, the secret was **never shown**, and a re-run with the same name is a UNIQUE (principal,name) rejection. The real remedy is "revoke `<name>`, then mint again", not a re-run.
  - The UPDATE sinks (status/subject/expiry/revoke/backfill) are idempotent, so the claim holds for 5 of the 7 sinks.
- **CLASS:** *a shared fault template must not assert a property of the operation that only some of its callers have.* The template's promise must be a parameter derived per sink, or be dropped.
- **SIBLINGS TRIED:** all 7 `landed=True` call sites, enumerated from the diff.
- **SIBLINGS NOT TRIED:** a live probe of what the engine answers on the duplicate (I reasoned from the DDL; no store was touched).

**F3: `governed_node_tables_of` drops a comment-prefixed `DEFINE FIELD` and keeps quote characters in table names** · MINOR
- **Where:** `governed._DEFINE_FIELD_ON` (anchored `^DEFINE`) over `ddl.split(";")`.
- **What happens:**
  - A `-- note\nDEFINE FIELD …` chunk does not match, so the table **shrinks out** of the governed set.
  - `ON \`a\`` / `ON ⟨a⟩` yield the quoted name.
- **Where it matters:** `restore_prod_dump.SliceDeriver.is_governed_shape` applies this to a DUMP's per-table DDL. A dump rendering comments or escaped names would be judged pre-63 shape.
- **Exposure:** latent. Today's generated DDL has 0 misses. The defect is inherited byte-for-byte from the test-tree `_governed_contract.governed_node_tables`; it was not introduced here.
- **ONE IMPLEMENTATION:** the docstring says "so the property has one implementation", but the test-tree copy (its own regex and splitter) still exists. Mutating one does not change the other.
- **CLASS:** *a DDL predicate must parse the statement grammar the engine accepts (comments, escaped identifiers), or raise on what it cannot read. A smaller set is the silent direction.*
- **SIBLINGS TRIED:** comment prefix, backtick, `⟨⟩`, lowercase, `IF NOT EXISTS`/`OVERWRITE`/`ON TABLE`, `;` in a string, REMOVE-after-DEFINE.
- **SIBLINGS NOT TRIED:** a real `surreal export` of a 3.2.4 store (I did not read any dump).

**F4: `lore-adm` as a whole depends on the governed-set derivation at parser build** · MINOR
- **Where:** `principals.build_parser` → `_report_table_help_domain()` → `governed_tables()` → `_emitted_schema_ddl()`.
- **What happens:** probed by giving one generator a required parameter. `build_parser()` then raises `TypeError` (§A5), so **every** lore-adm verb, including `key revoke`, dies with a traceback because of a help string.
- **Mitigation:** fail-closed is intended for the derivation, and the derivation's own tests would also go red at dev time, so the honest developer would see it first.
- **CLASS:** *help/prose derivations should not have a larger failure domain than the verb they describe.* Compute them lazily, or catch at the help seam.
- **SIBLINGS TRIED:** a required-param generator.
- **SIBLINGS NOT TRIED:** a generator that raises at call time; the import cost of running 15 generators per CLI start.

**F5: the migrate refusal for `finding`/`task` lost its pointer to packets 64b/64a** · NIT
- **Where:** `principals._not_supported` (`legless` iterates `_MIGRATE_VALID_TABLES` only).
- **Old vs new:** the old text said "task/finding land at 64". The new text names only `brief`'s packet, even though `PENDING_GOVERNED_TABLES` carries 64b/64a.
- **CLASS:** *the pointer list is derived over the migrate domain, not the governed domain.*
- **SIBLINGS TRIED:** finding, task, nope.
- **SIBLINGS NOT TRIED:** none.

**F6: two prose over-claims about the redaction seam** · NIT
- **Where:**
  - the `logging_setup.scrub_text` docstring ("THE one scrub every lore sink routes through");
  - the `principals._fault_line` docstring ("one redaction for every sink").
- **What happens:** `_render_migrate_refusal` and the migrate summary prints bypass it. Probed: a 128-hex `--table` is redacted on the report refusal and printed raw on the migrate refusal.
- **Exposure:** no credential reaches the bypassing sinks today.
- **CLASS:** *a claim quantified over "every sink" needs the sink set derived (e.g. every `print(..., file=sys.stderr)` in the CLI module) or must be narrowed in the prose.*
- **SIBLINGS TRIED:** report refusal, migrate refusal, fault line, CLI log handler.
- **SIBLINGS NOT TRIED:** other modules' `print` sinks (keeps/principal_keys CLI paths).

**F7: the report-unmigrated refusal dropped its zero-I/O receipt clause** · NIT
- **Where:** `_dispatch_report_unmigrated`.
- **Old vs new:** old text was `…; nothing was read`. New text is `…— its tables are …` with no receipt clause. The sibling migrate refusal still says "nothing was read or written".
- **CLASS:** *refusal receipts across sibling verbs state the same I/O facts.*
- **SIBLINGS TRIED:** both verbs.
- **SIBLINGS NOT TRIED:** n/a.

**F8: prose drift** · NIT
- **Stale help-domain comment:** in `principals._TABLE_HELP_DOMAIN`, the comment says "for BOTH table verbs". Report now uses `_report_table_help_domain()`.
- **Two orderings of one domain:** the report help orders its domain migrate-first (`agent, memory, message, brief, finding, task`), while its refusal sorts it (`agent, brief, finding, memory, message, task`). Both are on the same verb.
- **Bare REPORT citation in production code:** the `logging_setup._CREDENTIAL_HASH_RE` comment cites the bare `REPORT-builder-63c-i-a-fix6.md §RESUME 2`. A repo-root REPORT is a non-durable address per CLAUDE.md citation law; cite the archived path once it is archived.
- **CLASS:** derived-prose drift.
- **SIBLINGS NOT TRIED:** a full sweep of every new docstring against the code.

Non-findings, checked:
- The `_fault_line` cycle guard terminates.
- `_MIGRATING_TABLES` equals the `_MIGRATE_LEGS` keys.
- The brief dispatch fate is unchanged.
- The restore slice is byte-identical r5 vs r7.
- No `scripts` import in the package.
- `GovernedTableRefusedError` is a `ValueError` and is caught by the handler.
- Every hostile `--table` is refused before any I/O.

## Appendix — instruments (pasted verbatim; they lived in my scratch)
### A1 `probe_parser.py` (run as `cd $S/<tree> && .venv/bin/python $S/probe_parser.py`)
```python
"""Blind-reader probe: hostile statements through principals._set_columns (old vs new tree)."""
import sys, loremaster
from loremaster import principals as p
print("loremaster.__file__ =", loremaster.__file__)
CASES = [
 ("baseline", "UPDATE t SET a = 1, b = type::record('principal', $o) WHERE x = 1", ("a","b")),
 ("string-with-comma-keyword", "UPDATE t SET a = 'x, WHERE y', b = 2 WHERE z", ("a","b")),
 ("string-with-paren", "UPDATE t SET a = 'x)(', b = 2", ("a","b")),
 ("escaped-quote", r"UPDATE t SET a = 'it\'s, WHERE', b = 2", ("a","b")),
 ("dq-string", 'UPDATE t SET a = "x, RETURN y", b = 2', ("a","b")),
 ("nested-brackets", "UPDATE t SET a = [1, {k: (2, 3)}], b = 2", ("a","b")),
 ("subquery", "UPDATE t SET a = (SELECT x FROM y WHERE z = 1 LIMIT 1), b = 2 WHERE c", ("a","b")),
 ("plus-eq", "UPDATE t SET a += 1, b -= 2, c +?= 3", ("a","b","c")),
 ("lowercase", "update t set a = 1, b = 2 where c", ("a","b")),
 ("tabs-newlines", "UPDATE t\nSET\ta = 1,\n\tb = 2\nWHERE c", ("a","b")),
 ("unicode-ident", "UPDATE t SET café = 1, b = 2", ("café","b")),
 ("nbsp-sep", "UPDATE t SET a = 1, b = 2", ("a","b")),
 ("block-comment-with-WHERE", "UPDATE t SET a = 1 /* WHERE */, b = 2 WHERE c", ("a","b")),
 ("line-comment-with-WHERE", "UPDATE t SET a = 1 -- see WHERE below\n, b = 2 WHERE c", ("a","b")),
 ("hash-comment-RETURN", "UPDATE t SET a = 1 # RETURN note\n, b = 2", ("a","b")),
 ("comment-with-SET-before-clause", "UPDATE t /* SET x = 1 */ SET a = 1, b = 2", ("a","b")),
 ("comment-with-comma", "UPDATE t SET a = 1, /* , */ b = 2", ("a","b")),
 ("comment-with-quote", "UPDATE t SET a = 1 -- don't\n, b = 2", ("a","b")),
 ("angle-record-id-WHERE", "UPDATE t SET a = k:⟨x WHERE y⟩, b = 2", ("a","b")),
 ("angle-record-id-comma", "UPDATE t SET a = k:⟨x, b = 2⟩", ("a",)),
 ("backtick-value-WHERE", "UPDATE t SET a = `x WHERE y`, b = 2", ("a","b")),
 ("second-SET", "UPDATE t SET a = 1 SET b = 2", ("a","b")),
 ("UNSET-tail", "UPDATE t SET a = 1 UNSET b", ("a",)),
 ("EXPLAIN-tail", "UPDATE t SET a = 1 EXPLAIN", ("a",)),
 ("WHERE-paren-adjacent", "UPDATE t SET a = 1 WHERE(c = 1)", ("a",)),
 ("dotted-target", "UPDATE t SET a.b = 1", None),
 ("backtick-target", "UPDATE t SET `a` = 1", None),
 ("empty-item", "UPDATE t SET a = 1,, b = 2", None),
 ("trailing-comma", "UPDATE t SET a = 1, WHERE c", None),
 ("eqeq", "UPDATE t SET a == 1", None),
 ("unterminated", "UPDATE t SET a = 'x", None),
 ("mismatched", "UPDATE t SET a = (1]", None),
 ("no-SET", "UPDATE t CONTENT {a: 1}", None),
 ("SET-in-string-only", "UPDATE t CONTENT {a: ' SET b = 1'}", None),
 ("value-starts-with-keyword", "UPDATE t SET a = WHERE, b = 2", ("a","b")),
]
for name, stmt, expect in CASES:
    try:
        got = p._set_columns(stmt); out = repr(got)
        verdict = "EXACT" if expect is not None and got == expect else ("SUBSET" if expect and set(got) < set(expect) else ("SUPERSET/WRONG" if expect else "ACCEPTED(expected raise)"))
    except Exception as e:
        out = f"RAISE {type(e).__name__}"; verdict = "RAISE" if expect is None else "RAISE(expected set)"
    print(f"{name:34} | {verdict:22} | {out}")
```
### A1b live-leg exposure scan (`probe_legs.py`)
```python
import ast, loremaster, pathlib
print("loremaster.__file__ =", loremaster.__file__)
src = pathlib.Path(loremaster.__file__).parent / "principals.py"
tree = ast.parse(src.read_text())
for node in ast.walk(tree):
    if isinstance(node, ast.JoinedStr | ast.Constant):
        try: text = ast.unparse(node)
        except Exception: continue
        if "UPDATE" in text and " SET " in text.upper():
            flags = [k for k in ("--", "/*", "#", "⟨", "`") if k in text]
            print(node.lineno, flags, text[:160].replace("\n"," "))
```
Result: 7 UPDATE literals (memory/agent/message legs and 4 principal updates), all with `[]` flags. The flagged hits were docstrings, not statements.

### A2 `probe_redact.py`
```python
import hashlib, loremaster
from loremaster.logging_setup import scrub_text, REDACTED
print("loremaster.__file__ =", loremaster.__file__)
h = hashlib.sha512(b"k:secret").hexdigest()
cases = {
 "credential sha512 (128 lower)": f"index contains '{h}'",
 "content sha512 in log": f"chunk content_hash={h}",
 "content sha512 bare": f"digest {h} for file a.py",
 "129-hex run": f"x {h}a y", "127-hex run": f"x {h[:127]} y",
 "UPPERCASE 128": f"x {h.upper()} y",
 "split by newline 64+64": f"x {h[:64]}\n{h[64:]} y", "split by space": f"x {h[:64]} {h[64:]} y",
 "0x-prefixed": f"0x{h}", "inside identifier g..g": f"g{h}g", "underscore-joined": f"a_{h}_b",
 "two sha256 concatenated (=128)": hashlib.sha256(b'a').hexdigest()+hashlib.sha256(b'b').hexdigest(),
 "hyphenated uuid x4 (not run)": "-".join([h[:32]]*4), "fullwidth digits": "０"*128,
 "sha256 alone": hashlib.sha256(b'a').hexdigest(), "git sha": "d9b79bee065ae976422b223cdde4a2e9ad3ed06b",
}
for k,v in cases.items():
    out = scrub_text(v)
    print(f"{k:32} | {'REDACTED' if REDACTED in out else ('UNCHANGED' if out==v else 'CHANGED')} | {out[:90]!r}")
```
### A3 `probe_cli.py` (dispatch frames with `config=None`; validation precedes any store build, so there is zero I/O)
```python
import asyncio, argparse, io, contextlib, sys, loremaster
from loremaster import principals as p
print("loremaster.__file__ =", loremaster.__file__)
H = "f" * 128
for verb, fn in (("report-unmigrated", p._dispatch_report_unmigrated), ("migrate-governed", p._dispatch_migrate_governed)):
    for table in ("nope", "finding", "task", H, "x\nlore-adm: forged"):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            try:
                rc = asyncio.run(fn(argparse.Namespace(table=table), None))
            except (ValueError,) as e:
                print(p._fault_line(e), file=sys.stderr); rc = "1 (handler)"
            except Exception as e:
                rc = f"ESCAPED {type(e).__name__}: {str(e)[:80]}"
        print(f"{verb:18} {table[:14]!r:18} rc={rc} stderr={err.getvalue().strip()[:330]!r}")
```
For the accepted tables (`finding`/`task` on report), the `AttributeError: 'NoneType' … surreal` escape is my harness passing `config=None` past validation. It is not a defect.

### A4 `probe_domain.py` / `probe_restore.py`
In summary, these probes:
- printed `ddl_governed_tables`, `PENDING_GOVERNED_TABLES`, `governed_tables`, `_MIGRATE_VALID_TABLES` and `_MIGRATING_TABLES`;
- ran a liberal unanchored `DEFINE FIELD` regex over `g._emitted_schema_ddl()`, plus the anchored-miss count;
- ran hostile DDL through `governed_node_tables_of` and through the test-tree `_governed_contract.governed_node_tables`;
- ran the validator over every name in §4;
- called `_not_supported` for finding, brief and nope;
- built `SliceDeriver().governed_slice()` in both trees, and compared `g._emitted_schema_ddl() == _enforced_relations_scaffold.emitted_schema_ddl()`.

Every result is in §4/§5. The scripts are kept at `$S/probe_domain.py` and `$S/probe_restore.py`; this paragraph is the durable record of what they did.

### A5 parser-build fragility + fault-line probe
```python
from loremaster import principals as p, governed as g
from loremaster.store import surreal_schema as s
orig = s.generate_task_ddl
def generate_task_ddl(required_thing): return ""
s.generate_task_ddl = generate_task_ddl; g.ddl_governed_tables.cache_clear()
try: p.build_parser(); print("build_parser OK")
except Exception as e: print("build_parser RAISES:", type(e).__name__, e)   # -> TypeError
s.generate_task_ddl = orig; g.ddl_governed_tables.cache_clear()
from loremaster.store._txn import SurrealStoreError
import hashlib
h = hashlib.sha512(b"key:s").hexdigest()
a = SurrealStoreError(f"index contains '{h}'"); b = ValueError("inner"); a.__cause__ = b; b.__cause__ = a
print(p._fault_line(a))   # -> "lore-adm: index contains '***REDACTED***'\n  ← caused by: inner"
```
