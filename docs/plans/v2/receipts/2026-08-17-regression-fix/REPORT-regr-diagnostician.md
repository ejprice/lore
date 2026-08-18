# REPORT — regr-diagnostician

brief-base v14 read
brief project v7 read
store reference §3 read (multi-statement `.query()` validates statement[0] ONLY — §3 / #124 / #144)

## SUMMARY BLOCK

- **state:** done
- **deviations:** none (read-only; no tracked file touched; only this report written)
- **Packages considered:** none — no mechanism specified (diagnostic-only; I render verdicts, build nothing)
- **Reuse ledger:** none (no new symbols introduced)
- **Graded:** `5c8230c` · HEAD-at-report: `5c8230c` · SAME
- **Verdict per cluster (140 non-reconciling failures, all re-derived at `5c8230c`):**
  - **A** (135 errors, `test_message_ledger` 130 + `test_comms_footer` 5): **ONE** root cause — the NEW packet-07 SDK-guard leg (`multi_statement_violations`, commit `147be46`) correctly catches a **PRE-EXISTING TEST-FIXTURE** store-§3 violation in the shared helper `_seed_agents`. **NOT a production regression; NOT a store-artifact; NOT auth-WIP.** Fix = test helper.
  - **B1** (`test_secretstr_is_minted_only_where_a_credential_ORIGINATES`): **REGRESSION** — packets **07 / 07a** added 3 probe scripts that mint `SecretStr` outside the packet-42 allowlist.
  - **B2** (`test_no_auth_header_is_built_outside_a_seam`): **REGRESSION** — packet **59**'s `fastmcp_migration_spike.py` builds auth headers outside the typed seam.
  - **C** (`test_the_harnesss_docstring_counts_are_the_DERIVED_counts`): **REGRESSION (stale docstring)** — `_surreal_harness` docstring says 54 importers; 56 actually import it.
  - **D** (`test_no_unallowlisted_whole_tree_parser_clone_survives`): **REGRESSION** — packet **47a**'s `test_ingest_entity_seam.py` added an un-migrated whole-tree parser clone outside the allowlist.
  - **E** (`test_no_UNDECLARED_value_is_interpolated_into_query_text`): **REGRESSION** — packet **47a**'s `surreal.py:1254` interpolates `entity_table` (a controlled table name) into query text; a SAFE door not registered in `KNOWN_SAFE_DOORS`.
- **Tally:** 0 STORE-ARTIFACTS · 0 STILL-INCOMPLETE (auth 39/45/48/49) among the 140 · 5 failures are REGRESSIONS from recent on-branch packets (07/07a/47a/59) · the 135 errors are one guard-caught pre-existing test-fixture defect.
- **Reconciliation CONFIRMED** (full-suite `-n auto` at `5c8230c`: 451 failed + 135 errors): 446 reconciling failures are ALL inside the 10 auth test files of `pending_contracts.yaml` (11th = imported `_auth_fixtures.py`); 135 errors are ALL Cluster A; 140 non-reconciling = 135 err (A) + 5 fail (B1/B2/C/D/E). No non-auth failure hides in the auth bucket.
- **decisions-needed:**
  1. Cluster A fix owner: fix the TEST HELPER (route DDL through `execute_transaction`) — recommended — vs. narrow the guard. (Lead call; the guard is correct, so I recommend the helper.)
  2. B1/B2: allowlist the probe/spike scripts vs. change them to route through the seam. (Design call — lead/operator.)
- **receipt POINTERS:** §Cluster A–E below (each carries the failing-test tail + the introducing-commit blame); §Reconciliation for the auth-WIP bucket check.

---

## CAPABILITY CHECK (brief-base §4)

Everything the brief demanded was satisfiable: Bash for scoped test runs, git for blame, lore tools (loaded via `ToolSearch "+lore"`), the live spike-surreal store (`ws://127.0.0.1:18000`, `systemctl --user is-active spike-surreal.service` = active; `podman ps` shows it Up). No capability gap. lore fallbacks are noted inline where they occurred.

lore usage: `lore_get_symbol` / `lore_search` used first-choice for symbols (`reject_unknown_agents`, the message-ledger send path). One lore miss: `lore_get_symbol("loremaster.store._txn._attempt")` returned not-found (it is a **nested closure** inside `run_query`, not a module-level symbol — lore indexes class/method/function chunks, not inner closures). Fell back to `grep -n "\.query("` on `_txn.py` — appropriate (a nested-def is outside lore's chunk types). Not filed as friction: nested closures are a documented indexing boundary, not a defect.

---

## CLASSIFICATION TABLE (all at HEAD `5c8230c`)

| Cluster | Failing tests (count) | Root cause (symbol / file:line) | Introducing commit | Classification | Proposed minimal fix (tree / file / kind) |
|---|---|---|---|---|---|
| **A** | `test_message_ledger` (130 err) + `test_comms_footer` (5 err) = **135** | Shared test helper `_seed_agents` (`loremaster/tests/test_message_ledger.py:247`) routes multi-statement `generate_agent_ddl()` through the single-statement `_query` → `run_query` → `connection.query()` seam (`store/_txn.py:1207`). New guard leg `GuardReport.multi_statement_violations` (`_sdk_guard.py`) flags it. | Guard leg added `147be46` (pkt 07). Helper **pre-existing** (predates the guard). | **GUARD-CAUGHT PRE-EXISTING TEST-FIXTURE VIOLATION** (real store-§3 violation, in TEST code; NOT a production regression, NOT store-artifact, NOT auth-WIP). | **TEST-CODE** — `loremaster/tests/test_message_ledger.py::_seed_agents`: apply the agent DDL via `execute_transaction(f"BEGIN;\n{generate_agent_ddl()}COMMIT;\n", …)`, mirroring production `agents.py:483`. (Alt: narrow the guard — not recommended; the guard is doing its job.) |
| **B1** | `test_secretstr_is_minted_only_where_a_credential_ORIGINATES` (1) | `scripts/probe_query_complexity_07.py:54`, `probe_store_error_classes_07.py:38`, `probe_store_recovery_07a.py:65` each `PASSWORD = SecretStr("spikeroot")` — a `SecretStr` mint outside the packet-42 allowlist (`config.py`, `survey_txn_contention_102.py`, `comms_cli.py`). | `147be46` (pkt 07) ×2; `51e69a2` (pkt 07a) ×1. | **REGRESSION** (pkt 07 / 07a) | **SCRIPT or TEST** — either add the 3 probe files to the `allowed` tuple in `test_secret_typing.py` (they mint a hardcoded *test-store* credential, like `comms_cli.py` reads argv), or stop minting `SecretStr` in throwaway probes (use a plain constant). Design call. |
| **B2** | `test_no_auth_header_is_built_outside_a_seam` (1) | `scripts/fastmcp_migration_spike.py` builds `Authorization`/`auth=`/`headers=` at 6 sites (360, 209, 380, 385, 465, 414) outside `build_auth_headers(credential: SecretStr)`. | `ee4bced` (first-added) / `130fa16` (pkt 59). | **REGRESSION** (pkt 59) | **SCRIPT or TEST** — route the spike's header construction through `build_auth_headers`, or allowlist `fastmcp_migration_spike.py` (evidence-backed) if it is a throwaway harness. |
| **C** | `test_the_harnesss_docstring_counts_are_the_DERIVED_counts` (1) | `_surreal_harness.__doc__` states "54 test files import this harness"; **56** actually do. Meta-test asserts stated == derived. | Recent test-file additions (incl. pkt 47a `test_ingest_entity_seam.py`) bumped the count without a docstring update. | **REGRESSION (stale docstring)** — NOT a store-artifact (it counts TEST FILES, a source-tree fact, not store rows). | **DOCSTRING** — `loremaster/tests/_surreal_harness.py`: update the importer count 54→56 (and re-derive the `connect_admin`-caller count in the same edit). |
| **D** | `test_no_unallowlisted_whole_tree_parser_clone_survives` (1) | `loremaster/tests/test_ingest_entity_seam.py::_find_indexer_construction_sites` hand-rolls a whole-tree parse outside `_ALLOWED_WHOLE_TREE_CLONE_FILES` — the #279/#344/#345 consolidation invariant (checked-variable). | `562c9bd` / `06b7142` / `91fc30e` (pkt 47a). | **REGRESSION** (pkt 47a) — the pin is working; a new clone reddened it. | **TEST-CODE** — migrate `_find_indexer_construction_sites` onto `_logging_fixtures.parse_production_trees`, OR add `test_ingest_entity_seam.py` to `_ALLOWED_WHOLE_TREE_CLONE_FILES` with an evidence-backed reason + re-open trigger. |
| **E** | `test_no_UNDECLARED_value_is_interpolated_into_query_text` (1) | `loremaster/loremaster/store/surreal.py:1254`: `f"DELETE {entity_table} WHERE tier = $tier"`, `entity_table` iterated from `self._entity_tables` (a controlled, code-declared table-name set — NOT a comms identity, NOT user input; the `tier` *value* is correctly bound `$tier`). Not registered in `KNOWN_SAFE_DOORS`. | `91fc30e` (pkt 47a). | **REGRESSION** (pkt 47a) — a SAFE table-name door not registered; the injection AST scan (checked-variable, #219/04b2) correctly caught the new door. | **TEST-CODE (adjudication)** — add `('loremaster/loremaster/store/surreal.py', 'entity_table')` to `KNOWN_SAFE_DOORS` in `test_comms_footer.py` with the reason: controlled table name from `self._entity_tables`; SurrealQL cannot bind a table name as a param (same pattern as `CHUNK_TABLE` on the line above). |

**Cluster totals:** A = 135 errors; B1+B2+C+D+E = 5 failures. **140 total**, exactly matching finding #384's non-reconciling set (135 errors + 5 failed).

---

## PER-CLUSTER RECEIPTS

### Cluster A — the multi-statement guard (135 errors, ONE root cause)

**Store-reference citation (§3):** "A multi-statement `.query()` validates statement[0] ONLY. A later statement can fail and roll the whole thing back while `query()` raises *nothing*. Always `execute_transaction`." (`docs/reference/surrealdb-31-capabilities.md` §3 / §"READ THIS BEFORE YOU TOUCH THE STORE" fact 4.) The guard leg enforces exactly this.

**The guard leg (packet 07, `147be46`) — `loremaster/tests/conftest.py:212`:**
```
E   AssertionError: 1 bare .query() call(s) carried MORE THAN ONE statement during this test:
E       store/_txn.py:1207 in _attempt() -> connection.query()
```
The guard attributes the site to the **immediate** caller of `connection.query()` — always `_attempt` in `store/_txn.py` (production) — so the SITE is production even when the *originating* caller is test code. The originating caller is captured below.

**Instrument (throwaway pytest plugin, pasted verbatim per brief-base §1 — it is not committed; re-create to re-run):**
```python
# /tmp/probe_msq_plugin.py — loaded via `PYTHONPATH=/tmp pytest -p probe_msq_plugin -s`
import pathlib, sys, traceback
sys.path.insert(0, str(pathlib.Path("loremaster/tests").resolve()))
def pytest_configure(config):
    import _sdk_guard
    _orig = _sdk_guard._is_multi_statement_query
    def _patched(args):
        r = _orig(args)
        if r:
            sys.stderr.write("\n>>>MSQ_TEXT>>>\n" + repr(args[0]) + "\n>>>MSQ_STACK>>>\n"
                             + "".join(traceback.format_stack(limit=12)) + "\n<<<MSQ<<<\n")
        return r
    _sdk_guard._is_multi_statement_query = _patched
```

**Captured multi-statement text + originating stack (ground truth):**
```
>>>MSQ_TEXT>>>
"DEFINE TABLE IF NOT EXISTS agent SCHEMAFULL;\nDEFINE FIELD OVERWRITE name ON agent ...;
 ... ;\nDEFINE INDEX IF NOT EXISTS agent_name ON agent FIELDS name;\n"   # generate_agent_ddl()
>>>MSQ_STACK>>>
  test_message_ledger.py:317  message_ledger fixture -> _seed_agents(...)
  test_message_ledger.py:247  await cast(Any, ledger)._query(generate_agent_ddl())
  messages.py:638             _query -> run_query(...)
  store/_txn.py:1235          retry_on_conflict(_attempt, ...)
  store/_txn.py:1207          await connection.query(statement, params or {})   # <-- flagged
```

**Shared helper — both clusters:**
```
loremaster/tests/test_message_ledger.py:233  async def _seed_agents(ledger, refs, *, session):
loremaster/tests/test_message_ledger.py:247    await cast(Any, ledger)._query(generate_agent_ddl())
loremaster/tests/test_comms_footer.py:3614     from test_message_ledger import _ref, _seed_agents
```
`_seed_agents` is called by the `message_ledger` fixture (line 317) and directly at 450/577/1302/1766/1807/1850/3641; `test_comms_footer` imports and calls it. Every `[real]`-variant test that seeds agents trips the teardown guard → 130 (`test_message_ledger`) + 5 (`test_comms_footer`) = 135. All 5 `test_comms_footer` errors show the identical `1 bare .query() call(s) carried MORE THAN ONE statement` signature (verified in a full-file run).

**Production applies the SAME DDL correctly (so this is NOT a production defect):**
```
loremaster/loremaster/agents.py:472-484  # ensure_ready
    ddl = generate_agent_ddl()
    await execute_transaction(f"BEGIN;\n{ddl}COMMIT;\n", ...)   # verifies EVERY statement
```
The docstring at `agents.py:473-474` states it applies the slice "inside ONE `BEGIN … COMMIT` via `execute_transaction`, which verifies [every statement]." Only the test helper deviates.

**Why packet 07 shipped green (per brief, verified plausible):** the guard leg is autouse and only sees a *real* `connection.query()`; the `[fake]` in-memory variants never reach `run_query`, and packet 07's scoped gates did not run the `[real]` live-store variants of `test_message_ledger` / `test_comms_footer`. `escapes` is empty (`escapes=[]` in the captured `GuardReport`) — the DDL *did* ride `retry_on_conflict`; it is ONLY the multi-statement leg that fires.

**Recommended fix (TEST-CODE):** change `_seed_agents` to apply the agent DDL through the transaction path (mirror `agents.py`), e.g. `execute_transaction(f"BEGIN;\n{generate_agent_ddl()}COMMIT;\n", acquire=…, drop=…, url=…)`. This routes it through `query_raw`, which the guard leg deliberately excludes (`method_name == "query"` only). The guard is correct and should stay; narrowing it would re-open the store-§3 hole for test seeds.

### Cluster B1 — `SecretStr` minted outside a credential origin

```
E   AssertionError: a SecretStr is minted outside a credential ORIGIN. ... (attack shape S6):
E       scripts/probe_query_complexity_07.py:54
E       scripts/probe_store_error_classes_07.py:38
E       scripts/probe_store_recovery_07a.py:65
FAILED test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_secretstr_is_minted_only_where_a_credential_ORIGINATES
```
Blame:
```
147be46 fix(store): ... (packet 07)   scripts/probe_query_complexity_07.py    (PASSWORD = SecretStr("spikeroot"))
147be46 fix(store): ... (packet 07)   scripts/probe_store_error_classes_07.py (PASSWORD = SecretStr("spikeroot"))
51e69a2 fix(07a): ...                  scripts/probe_store_recovery_07a.py     (PASSWORD = SecretStr("spikeroot"))
```
The packet-42 allowlist (`allowed` tuple in the test) is `config.py`, `survey_txn_contention_102.py`, `comms_cli.py`. These 3 probe scripts mint a hardcoded spike-surreal password — a **test-store literal**, not a production secret. Fix: allowlist them (consistent with `survey_txn_contention_102.py` already being allowlisted) OR drop `SecretStr` from the probes.

### Cluster B2 — auth header built outside the typed seam

```
E   AssertionError: these sites build an outgoing auth header outside the typed seam. R26: route them
    through build_auth_headers(credential: SecretStr) ...:
E       scripts/fastmcp_migration_spike.py:360 auth= not sourced from build_auth_headers()
E       scripts/fastmcp_migration_spike.py:209 auth= not sourced from build_auth_headers()
E       scripts/fastmcp_migration_spike.py:380 builds 'Authorization' outside the seam
E       scripts/fastmcp_migration_spike.py:385 headers= not sourced from build_auth_headers()
E       scripts/fastmcp_migration_spike.py:465 headers= not sourced from build_auth_headers()
E       scripts/fastmcp_migration_spike.py:414 builds 'Authorization' outside the seam
FAILED test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_no_auth_header_is_built_outside_a_seam
```
Blame: `ee4bced chore(59): fastmcp migration spike harness` (first-added), `130fa16 feat(59): migrate MCP server façade → standalone fastmcp 3.x`. This is a **packet 59** migration spike, distinct from the auth-posture packets (39/45/48/49). Fix: route the spike's header construction through `build_auth_headers`, or allowlist the spike file.

### Cluster C — stale harness docstring count

```
E   AssertionError: the harness docstring says 54 test files import it; 56 actually do. That number
    is the stated justification for RULING 1's in-function import, so understating it understates
    the blast radius.
E   assert 54 == 56
FAILED test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts
```
The test counts TEST FILES that import `_surreal_harness` (a **source-tree** fact — not store rows), so this is **NOT** a 3.2.4 store-artifact. Two importers were added since the docstring's "54" (packet 47a's `test_ingest_entity_seam.py` is one). Fix: update the docstring count in `_surreal_harness.py` to the derived values (importers → 56; re-derive the `connect_admin`-caller count in the same edit). Meta-test working as designed.

### Cluster D — un-allowlisted whole-tree parser clone

```
E   AssertionError: these test files hand-roll a whole-tree parse ... OUTSIDE the evidence-backed
    allowlist (finding #279/F4 — 'migrated' is not a checked variable for them):
E       {'test_ingest_entity_seam.py': ['_find_indexer_construction_sites']}
FAILED test_ast_reach_helpers.py::TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist::test_no_unallowlisted_whole_tree_parser_clone_survives
```
Blame: `562c9bd test(47a): RED contract + inert seam stubs`, `06b7142 feat(47a): R2 loud fail-fast guard`. The pin's own docstring names `test_anchored_pattern_seam._parse_production_trees` as the expected RED offender at `641f758` and says "after A-SUB it routes through the shared parser and this passes." That original clone was migrated; **packet 47a added a NEW clone** (`_find_indexer_construction_sites`) that is neither migrated nor allowlisted — the checked-variable property firing correctly. Fix: migrate onto `_logging_fixtures.parse_production_trees` OR allowlist the file with evidence + re-open trigger.

### Cluster E — undeclared value interpolated into query text

```
E   AssertionError: a NEW non-constant value is interpolated into store query text:
E       loremaster/loremaster/store/surreal.py:1254: entity_table
FAILED test_comms_footer.py::TestNoCommsIdentityReachesQueryTEXT::test_no_UNDECLARED_value_is_interpolated_into_query_text
```
Context (`surreal.py:1252-1255`):
```python
await self._query(f"DELETE {CHUNK_TABLE} WHERE tier = $tier", {"tier": tier})
for entity_table in self._entity_tables:
    await self._query(f"DELETE {entity_table} WHERE tier = $tier", {"tier": tier})
```
Blame: `91fc30e feat(47a): GREEN twelfth-seam ingest entity-fragment (40/40)`. `entity_table` is a **controlled table name** from `self._entity_tables` (declared entity tables) — NOT a comms identity (agent/session/brief/recipient name) and NOT user input; the `tier` *value* is correctly bound as `$tier`. SurrealQL cannot bind a table name as a parameter (identical to the `CHUNK_TABLE` interpolation on the line directly above, which IS allowlisted). This is a **SAFE door** packet 47a failed to register. Fix: adjudicate and add `('loremaster/loremaster/store/surreal.py', 'entity_table')` to `KNOWN_SAFE_DOORS` in `test_comms_footer.py`. The AST scan (checked-variable, #219/04b2) is working as designed.

---

## RECONCILIATION (verifying finding #384, not taking it on faith)

Full-suite run at `5c8230c`: `uv run pytest -n auto -q --tb=no -rfE` → **451 failed, 9878 passed, 51 skipped, 3 xfailed, 135 errors** in 240s (exit 1). Matches the brief's baseline exactly (451 + 135). Bucketed by file:

**ERRORS — 135 total, ALL Cluster A (no auth file contributes any error):**
```
130  loremaster/tests/test_message_ledger.py   (Cluster A — _seed_agents multi-statement guard)
  5  loremaster/tests/test_comms_footer.py     (Cluster A — same, via imported _seed_agents)
```

**FAILED — 451 total = 446 auth-WIP + 5 non-auth:**
```
--- 446 RECONCILING, all inside the pending_contracts.yaml auth files ---
 82  loremaster/tests/test_auth_composition.py
 75  loremaster/tests/test_google_token_verifier.py
 70  lorerunes/tests/test_posture.py
 57  loremaster/tests/test_hosted_readonly_posture.py
 46  loremaster/tests/test_allowlist_roster.py
 37  lorerunes/tests/test_roster_parser.py
 25  loremaster/tests/test_auth.py
 21  lorerunes/tests/test_email_normalisation.py
 19  loremaster/tests/test_auth_identity_seam.py
 14  loremaster/tests/test_permission_resolver_seam.py
 == 446  (82+75+70+57+46+37+25+21+19+14 — verified by grep count = 446)
--- 5 NON-RECONCILING (the regression suspects, = Clusters B1/B2/C/D/E) ---
  2  loremaster/tests/test_secret_typing.py    (B1 + B2)
  1  loremaster/tests/test_surreal_harness.py  (C)
  1  loremaster/tests/test_comms_footer.py     (E — distinct from its 5 guard errors)
  1  loremaster/tests/test_ast_reach_helpers.py (D)
```

**VERDICT — finding #384's reconciliation is CONFIRMED:**
- The **446 reconciling failures are ALL inside the 10 auth/posture test files** named in `scripts/pending_contracts.yaml`. The 11th listed file, `loremaster/tests/_auth_fixtures.py`, is a fixture MODULE (no test items) imported by those test files — the shared not-yet-built-symbol references it carries are what fail the importers. **No non-auth-file failure hides in that bucket** — every auth-file failure is a `FAILED`, and the 5 non-auth failures live in distinctly-named files.
- The **135 errors are ALL Cluster A** (130 `test_message_ledger` + 5 `test_comms_footer`) — no auth file produces an error.
- **140 non-reconciling = 135 errors (Cluster A) + 5 failed (B1/B2/C/D/E).** Exactly.

**Scope note (honest bound):** I confirmed the 446 are all in auth FILES (the brief's stated bar: "git + a grep of the FAILED list by file is enough"). I did NOT read all 446 individual assertion messages, so I cannot rule out a genuine non-auth *defect* wearing an auth-file test name — but #333 establishes those files reference not-yet-built auth symbols (packets 39/45/48/49), which is the STILL-INCOMPLETE-PACKET cause. If the lead wants certainty that none of the 446 is a smuggled regression, the settling experiment is: build/stub the auth symbols (or `git stash` the 11 files) and confirm the 446 go green together.

---

## CROSS-CUTTING OBSERVATIONS (brief-base §2 — surfaced, not silently dropped)

1. **All 5 regressions are from RECENT on-branch packets, none from the auth WIP:** pkt 07 (`147be46`), pkt 07a (`51e69a2`), pkt 47a (`562c9bd`/`06b7142`/`91fc30e`), pkt 59 (`ee4bced`/`130fa16`). Four of the five (C excepted) trip **checked-variable / AST invariants that are working exactly as designed** — a new site landed without being migrated/allowlisted/adjudicated. This is the repo's own "a new clone reddens it the day it lands" property firing. The fixes are cheap (allowlist/adjudicate/docstring) and none indicates a broken invariant.

2. **Cluster A is the only one worth a design thought.** The guard's `multi_statement_violations` leg attributes to the *immediate* frame (`_attempt`, always production), so it cannot distinguish a test-origin caller from a production-origin one. Two readings: (a) that is CORRECT — store §3 applies to every caller, and a test that seeds via bare `.query()` could silently get a half-applied schema; (b) the guard is now reddening 135 tests for a pre-existing test-helper shortcut. I recommend reading (a): **fix the helper, keep the guard.** Narrowing the guard to production-origin-only would re-open the §3 hole for every test seed — the exact "route around the weakness" move the trust doctrine forbids. Filed as an observation, not a lore finding, since it is a fix-in-flight, not a lore-tool gap.

3. **STORE-ARTIFACT count is ZERO.** No cluster is driven by the 3.2.4 float (#336). Cluster C *looks* count-shaped but counts TEST FILES (a source-tree fact), and Cluster A's DDL is version-independent (`generate_agent_ddl()` string content, not engine behavior). No 3.2.4 re-probe is needed for any of the 140.
