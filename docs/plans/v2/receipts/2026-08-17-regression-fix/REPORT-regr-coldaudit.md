# REPORT — regr-coldaudit

brief-base v14 read
brief project v7 read
store reference §2/§3/§4 read (§3: multi-statement `.query()` validates statement[0] ONLY — use `execute_transaction`/`query_raw`; §2/§4: table/edge names are inline, only VALUES bind)

## SUMMARY BLOCK

- **state:** done
- **VERDICT: GO.** The 140 non-reconciling (135 err + 5 fail) are fixed; ZERO new reds; all three
  load-bearing justifications (D/E/B2) hold; A mirrors production byte-for-byte; B1/C confirmed;
  the packet-07 guard is untouched and still armed. No production code touched.
- **deviations:** none (read-only; wrote only this report; ran the full suite per brief; no tracked file mutated — verified `git status --short` unchanged after my run).
- **Packages considered:** none — no mechanism specified (I graded another agent's artifact; built nothing).
- **Reuse ledger:** none (no new symbols introduced).
- **Graded:** `5c8230c` · HEAD-at-report: `5c8230c` · SAME. ⚠ The tree is UNCOMMITTED — I graded the WORKING TREE (the 5 unstaged test-file edits atop `5c8230c`), not a commit.
- **Instrument 1 (full suite @ working tree):** **446 failed, 9883 passed, 51 skipped, 3 xfailed, 0 errors** (237.84s, PYTEST_EXIT=1). Baseline was 451f + 135e / 9878p. → errors 135→0, failed 451→446, passed +5, **zero new red**. Residual 446 bucket is BYTE-IDENTICAL to the diagnostician's pre-fix auth bucket (same 10 files, same per-file counts); every one is declared in `scripts/pending_contracts.yaml` (auth WIP, pkts 39/45/48/49).
- **Instrument 2 (D/E/B2 justifications):** **all HOLD** — the allowlist/exempt/adjudicate choices were correct, the rejected "migrate/route-through-seam/bind-it" options were genuinely inexpressible.
- **Instrument 3 (A mirrors prod + guard):** **CONFIRMED** — `_seed_agents` call is the exact arg shape of `AgentRegistry.ensure_ready` (agents.py), rides `execute_transaction`→`query_raw` (not bare `.query()`); `MessageLedger` exposes `_url`/`_ensure_connection`/`_drop_connection`; `conftest.py` + `_sdk_guard.py` UNTOUCHED (git).
- **Instrument 4 (B1/C):** **CONFIRMED** — `signin_credentials` & `SurrealStore.__init__` both REQUIRE `SecretStr` (plain str impossible); C docstring now = derived 56 importers / 40 callers (meta-test green; grep cross-check 56 exact / 41 files reference `connect_admin`).
- **decisions-needed:** none. One cross-cutting OBSERVATION (non-blocking): B2's exempt is FILE-LEVEL and its re-open trigger is keyed on *credential-nature*, not *site-count* — a future NEW fake-token site added to the spike file would be silently exempted. Acceptable for a throwaway spike; surfaced per §2. See §CROSS-CUTTING.
- **receipt POINTERS:** §Instrument 1 (bucket + counts) · §Instrument 2 D/E/B2 (source reads) · §Instrument 3 (arg-shape diff) · §Instrument 4 (signatures + counts).

---

## CAPABILITY CHECK (brief-base §4)

Everything the brief demanded was satisfiable: Bash for the full-suite run + git, lore tools (loaded
`ToolSearch "+lore"`) used first-choice for every symbol lookup (`execute_transaction`,
`signin_credentials`, `build_auth_headers`, `AgentRegistry.ensure_ready`, `register_entity_tables`,
`SurrealStore.__init__`/`delete_by_tier`, `MessageLedger._ensure_connection`, `parse_production_trees`,
`_find_indexer_construction_sites`, `_production_python_roots`, `workspace_roots`), the live
spike-surreal test store (`ws://127.0.0.1:18000`) exercised by the `[real]` Cluster-A tests inside the
full suite. No capability gap. Two grep fallbacks, both SAID OUT LOUD and both for the sanctioned
cross-cutting-map / exhaustiveness cases (CLAUDE.md dogfood §3): (a) `Indexer(` call-site enumeration
across all members + scripts (rename/exhaustiveness — one missed site would falsify the D verdict);
(b) `_surreal_harness` importer / `connect_admin` caller counts as an INDEPENDENT second instrument
beside the AST meta-test (C). Not filed as friction — both are the documented grep-honest cases, not
lore gaps.

---

## INSTRUMENT 1 — FULL-SUITE REGRESSION (the definitive no-new-red check)

**Command (backgrounded, PID-watched, `PIPESTATUS` captured so a piped "no tests ran" cannot read as green):**
`uv run pytest -n auto -q -ra --tb=line | tee …/coldaudit-full.log`

**Tail (verbatim):**
```
446 failed, 9883 passed, 51 skipped, 3 xfailed, 6 warnings in 237.84s (0:03:57)
PYTEST_EXIT=1
```
`grep -c "^ERROR " coldaudit-full.log` → **0**.

**Reconciliation vs the pre-fix baseline (451 failed + 135 errors / 9878 passed):**

| metric | pre-fix (`5c8230c` clean) | post-fix (working tree) | delta | required |
|---|---|---|---|---|
| errors | 135 | **0** | −135 | 0 ✓ |
| failed | 451 | **446** | −5 | 446 ✓ |
| passed | 9878 | **9883** | +5 | ↑ (no regressions) ✓ |

The `passed` count rose by only **+5** (not +135) because the 135 Cluster-A errors were **TEARDOWN**
errors on tests whose bodies already PASSED (the autouse guard fires at teardown) — so those 135 were
already inside the 9878 pre-fix `passed`; removing the teardown error drops them from the error bucket
without adding to `passed`. The +5 is exactly B1/B2/C/D/E moving FAILED→PASSED. This fully reconciles;
there is no hidden mass movement.

**Residual 446 bucketed by file (post-fix) — BYTE-IDENTICAL to the diagnostician's pre-fix bucket:**
```
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
 == 446
```
Every one of these 10 files (plus the imported `_auth_fixtures.py`) is named in
`scripts/pending_contracts.yaml` — the auth WIP for packets 39/45/48/49 (#333). **No non-auth file
appears in the FAILED list**, and none of the 5 regression files (`test_secret_typing`,
`test_surreal_harness`, `test_comms_footer`, `test_ast_reach_helpers`) nor `test_message_ledger`
appears — all green. Post-fix FAILED set = pre-fix FAILED set **minus** the 5 regressions. **No new
failure or error anywhere → INSTRUMENT 1 PASS.**

---

## INSTRUMENT 2 — REFUTE the three load-bearing justifications

### D — `test_ast_reach_helpers.py` allowlists `test_ingest_entity_seam.py` — JUSTIFIED (migration genuinely inexpressible)

Read from source (lore_get_symbol):
- `parse_production_trees(*, include_scripts=True, include_skills=False, include_tests=False)` — **NO
  `roots=`/scope parameter** (`_logging_fixtures.py:247`). It parses `*.py` under
  `workspace_roots(...)`.
- `workspace_roots(...)` (`_logging_fixtures.py:170`) yields `(member, root/member/member)` for **every**
  `[tool.uv.workspace] members` entry (loremaster **+ lorerunes + loresigil + lorescribe**), plus a
  single **repo-level** `scripts` when `include_scripts` — **never a member-level `<member>/scripts`.**
- `_production_python_roots()` (`test_ingest_entity_seam.py:1027`) = `[loremaster/loremaster, <repo>/scripts,
  loremaster/scripts]` filtered to existing dirs. `_find_indexer_construction_sites(roots)` walks those
  roots for `Indexer(...)` calls.

Two structural mismatches, both verified:
1. **WIDEN (live):** `parse_production_trees` scans lorerunes/loresigil/lorescribe packages;
   `_find_indexer_construction_sites` scans **loremaster only**. `Indexer` is a loremaster concept —
   grep for `Indexer(` (prod, non-test) finds **exactly 3 sites, ALL in loremaster**
   (`scout.py:771`, `index/cli.py:160`, `server.py:9318`); zero in the other members/scripts. With no
   `roots=` param, `parse_production_trees` **cannot be restricted** to loremaster.
2. **NARROW (contractual):** `parse_production_trees` never parses `<member>/scripts`; the helper's
   `_production_python_roots` contract covers `loremaster/scripts` "the day it lands." (`loremaster/scripts`
   does **not** exist on disk today, so this leg is currently vacuous — but a migration onto
   `parse_production_trees` would parse trees it never parses, so filtering-down could never recover it.)

⇒ The shared parser cannot express the helper's deliberately-derived reach. Migration would both widen
(§7 scope change) and narrow (drop the adversary-bought member-scripts leg). **Allowlist is the correct
choice.** The widen leg alone is dispositive. The full suite confirms the sibling pins
(`dead-entry`/`vacuous`/`planted`) stay green with the entry added.

### E — `test_comms_footer.py` KNOWN_SAFE_DOORS entry for `entity_table` — JUSTIFIED (code-declared, un-bindable, discriminating)

**Provenance trace (lore_get_symbol + lore_impact + source read):**
- `SurrealStore.delete_by_tier` (`surreal.py:1231`) runs `f"DELETE {entity_table} WHERE tier = $tier"`,
  `entity_table` iterating `self._entity_tables`; the `tier` **value** is correctly bound `$tier`.
- `self._entity_tables` is written in exactly two places — `__init__(entity_tables=())` and
  `register_entity_tables(entity_tables)` — each `tuple(...)` of table-name **strings**.
- `lore_impact(register_entity_tables)` → **1 prod consumer, 0 test:
  `loremaster.server.build_app_context`** (the composition root). Its feed (server.py:9184-9192):
  `for ext … for ingest_backend in extension.ingest_backends(ctx): entity_table_names.extend(ingest_backend.entity_tables())`
  → `write_store.register_entity_tables(list(dict.fromkeys(entity_table_names)))`.
- `IngestBackend.entity_tables()` (`extension.py:246`) is a protocol declaration: *"the entity TABLE
  names this backend owns."* → **code-declared table names, NOT user / comms / caller input.**
- A table NAME cannot be a bound parameter in SurrealQL (store §2/§4 — table/edge names inline, only
  values bind); the sibling `DELETE {CHUNK_TABLE}` on the line above interpolates a table name for the
  identical reason. ⇒ The CODE binding it is impossible; a SAFE door is the correct adjudication.

**Independent discrimination check (I read the pin, per brief option 2):** the pin
(`test_comms_footer.py:3083`) computes `undeclared = [d for d in doors if (d[0], d[1]) not in
KNOWN_SAFE_DOORS]`, where `doors` are AST-derived `(path, expr, lineno)` tuples. The entry
`('loremaster/loremaster/store/surreal.py', 'entity_table')` is keyed on the **exact (file, expr)** — it
exempts ONLY an interpolated expr literally named `entity_table` in that exact file; it is **not** a
blanket/file-wide/wildcard exemption. Any other non-constant interpolation in `surreal.py` still reddens.
This matches the fixer's both-way mutation (pointing the door at `entity_table_WRONG_MUTATION` re-reds).
The pin also asserts `sites >= MINIMUM_SITES_SCANNED (100)` — the door addition doesn't shrink the scan,
so the reach floor stays intact. **JUSTIFIED.**

### B2 — `test_secret_typing.py` file-level `_FASTMCP_SPIKE_EXEMPT` — JUSTIFIED (inexpressible + no real credential), with a noted breadth residual

**Seam read:** `build_auth_headers(credential: SecretStr) -> dict[str,str]` (`calibration/counting.py:75`)
returns a **FIXED Anthropic** set `{"x-api-key": <secret bytes>, "anthropic-version", "content-type"}`.

**All 6 flagged spike sites read directly (scripts/fastmcp_migration_spike.py):**

| line | site | expressible via `build_auth_headers`? | real credential? |
|---|---|---|---|
| 209 | `Client(endpoint, auth=BearerAuth(token))` — fastmcp SDK auth OBJECT | No (returns a header dict, not a `BearerAuth`) | No — `token` is a param fed test literals |
| 360 | `FastMCP(auth=CountingVerifier("good-token", …))` — SERVER-side verifier (incoming) | No (not an outgoing header at all) | No — hardcoded `"good-token"` |
| 380 | `"Authorization": "Bearer good-token"` literal | No (`Authorization`/`Bearer` ≠ `x-api-key`/Anthropic) | No — hardcoded literal |
| 385 | `headers={**base_headers, **extra_headers}` httpx merge | No (dict merge of literals, not a seam call) | No |
| 414 | `"Authorization": "Bearer WRONG"` — NEGATIVE control | No (deliberately-invalid literal; cannot ride a SecretStr seam) | No — intentionally wrong |
| 465 | `headers=dict(accept)` + optional `Host` | No (carries `Accept`/`Host`, no auth) | No |

Credential-source grep over the whole spike (`getenv|environ|SecretStr|x-api-key|API_KEY|api_key|secret|read_text|open(`)
→ **zero hits.** The spike sources **no** real/production credential; every token is a hardcoded MCP
test literal. Both legs hold: **no site is seam-expressible, and none carries a real credential →
JUSTIFIED.**

**Breadth residual (surfaced per §2, non-blocking):** the exempt is FILE-LEVEL
(`_FASTMCP_SPIKE_EXEMPT = "scripts/fastmcp_migration_spike.py"`), matching the test's existing
exact-path idiom (`_INCOMING_AUTH_EXEMPT = "loremaster/auth.py"`). It exempts **all present AND future**
construction in that file, and the stated re-open trigger is keyed on *"the spike sends a REAL
credential"* — **not** on *"a new site is added."* So a future NEW `Bearer <fake-token>` site in the
spike would be silently exempted and would NOT trip the pin. This is acceptable for a throwaway packet-59
migration spike (not production/shipped; the repo's threat model targets an honest dev shipping outgoing
auth outside the seam in PRODUCTION code), but the trigger's wording leaves the file unwatched. Worth a
one-line trigger tweak if the lead wants the pin to keep watching that file.

---

## INSTRUMENT 3 — A mirrors production + guard intact — CONFIRMED

**Arg-shape identity (byte-for-byte):**

Production `AgentRegistry.ensure_ready` (`agents.py:481-487`):
```python
await execute_transaction(
    f"BEGIN;\n{ddl}COMMIT;\n", {},
    acquire=self._ensure_connection, drop=self._drop_connection, url=self._url,
)   # ddl = generate_agent_ddl()
```
Fixer's `_seed_agents` (`test_message_ledger.py:250-256`):
```python
await execute_transaction(
    f"BEGIN;\n{generate_agent_ddl()}COMMIT;\n", {},
    acquire=cast(Any, ledger)._ensure_connection, drop=cast(Any, ledger)._drop_connection, url=cast(Any, ledger)._url,
)
```
Same DDL (`generate_agent_ddl()`), same positional `(statement, {})`, same keyword `acquire/drop/url`.

- **Rides `query_raw`, not bare `.query()`:** `execute_transaction` (`_txn.py:1238`) →
  `_run_verified_transaction` → `_txn_query_raw` (`query_raw` + per-statement check) — its docstring:
  *"the counter to the SDK's own `query()` gap … Each attempt … `query_raw`."* The guard's
  multi-statement leg keys on `method_name == "query"` only, so `query_raw` is deliberately outside it →
  the 135 errors clear structurally, not by luck.
- **`MessageLedger` exposes all three accessors:** `self._url` (messages.py:525),
  `_ensure_connection` (535), `_drop_connection` (614). `_ensure_connection` itself uses
  `signin_credentials(user=self._user, password=self._password)` → the seam is the same one production
  rides.
- **Guard UNTOUCHED / still armed:** `git status --short` lists ONLY the 5 test files;
  `loremaster/tests/conftest.py` and `loremaster/tests/_sdk_guard.py` are **not** modified. The fix
  removed the violation (the multi-statement bare `.query()` seed), not the guard — the guard's autouse
  fixture + `_sdk_guard.py` are byte-unchanged, and the full suite exercised it on every `[real]` seed
  test (135 formerly-erroring tests now pass under the live guard).

---

## INSTRUMENT 4 — B1 / C sanity — CONFIRMED

**B1 (both APIs require `SecretStr`; plain `str` impossible ⇒ allowlist correct):**
- `signin_credentials(*, user: str, password: SecretStr)` (`_txn.py:986`) — unwraps via
  `password.get_secret_value()`; a plain `str` is a type error AND a runtime `AttributeError`.
- `SurrealStore.__init__(*, …, password: SecretStr, …)` (`surreal.py:398`) — requires `SecretStr` (#211).
- The 3 probes mint `SecretStr("spikeroot")` — the well-known spike-surreal (TEST store) root literal,
  same shape as the already-allowlisted `scripts/survey_txn_contention_102.py`. Not a production
  credential. Re-open trigger stated (a probe ever sourcing a real credential). **Correct.**

**C (docstring counts = derived counts):**
- Independent grep: **56** test files import `_surreal_harness` — matches the fixer's `54 → 56`.
- `connect_admin`: 41 files reference the symbol; `_surreal_harness.py` both DEFINES (`:634`) and CALLS
  it (`:868`, `:885`); the AST meta-test derives **40 caller files**, matching the fixer's `37 → 40`.
- Ran the authoritative instrument at the working tree:
  `pytest loremaster/tests/test_surreal_harness.py -k DERIVED_counts -q` → **`1 passed, 56 deselected`**.
  Green ⇒ stated docstring counts (56/40) == the test's own AST derivation. The fixer's bonus catch (the
  `37→40` caller staleness the diagnosis missed, because the importer assertion fires first) is real and
  now green.

---

## CROSS-CUTTING OBSERVATIONS (brief-base §2 — surfaced, not silently dropped)

1. **B2 file-level-exempt breadth (non-blocking, detailed in §Instrument 2 B2):** the exempt stops the
   pin watching `fastmcp_migration_spike.py` entirely for present + future sites; its re-open trigger is
   keyed on *credential-nature*, not *new-site*. Acceptable for a throwaway spike; a lead may want the
   trigger reworded to "any new construction in this file" so the pin keeps discriminating. This is a
   trade to note, not a defect in the fix.
2. **All 5 fixes stayed inside the writable set (`loremaster/tests/**`); no production code touched.**
   `git diff --stat` = 5 files, +91/−5, all under `loremaster/tests/`. The diagnosis's "production is
   correct for every cluster" verdict held — every fix routes to an existing seam (`execute_transaction`)
   or edits a test allowlist / adjudication / docstring. E did NOT edit `surreal.py`; B1/B2 did NOT edit
   the scripts.
3. **The fix pattern is the repo's own "a new site reddens the pin the day it lands" property working as
   designed** — four of the five (all but C) were checked-variable / AST invariants firing correctly on
   an un-migrated/un-adjudicated new site from recent packets (07/07a/47a/59). The fixes are the correct
   adjudications, each carrying an evidence block + a named re-open trigger. No invariant was weakened.

---

## VERDICT: **GO**

The 140 non-reconciling reds (135 errors + 5 failures) are all resolved; the full suite shows **zero new
failures or errors** (446f/0e, residual = exactly the 10 `pending_contracts.yaml` auth-WIP files,
identical to the pre-fix bucket); the three load-bearing justifications (D migrate-inexpressible /
E code-declared-un-bindable-and-discriminating / B2 seam-inexpressible-and-no-real-credential) all HOLD;
A mirrors production byte-for-byte and rides `query_raw`; the packet-07 guard is untouched and still
armed; B1 and C are confirmed. No production code was touched. One non-blocking breadth observation on
B2's file-level exempt is surfaced for the lead.
