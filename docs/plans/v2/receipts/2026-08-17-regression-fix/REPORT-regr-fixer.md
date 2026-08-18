# REPORT — regr-fixer

brief-base v14 read
brief project v7 read
store reference §3 read (multi-statement `.query()` validates statement[0] ONLY; use `execute_transaction` which verifies every statement — §3 / READ-THIS fact 4)

## SUMMARY BLOCK

- **state:** done — A/B1/B2/C/D/E all GREEN; 5 files edited; NO production code touched; NO scripts edited
- **deviations:** none
- **notable:** Cluster C had a SECOND stale count the diagnosis did not surface (`connect_admin` callers 37→**40**, in addition to importers 54→**56**) — the DERIVED_counts pin asserts importers first, so the diagnosis (which read only the first assertion) saw only 54→56. The ruling ("re-derive BOTH in the same edit") caught it; I fixed both.
- **Packages considered:** none — no mechanism specified. Every fix ROUTES to an existing seam (`execute_transaction`) or edits a test allowlist/adjudication/docstring; no new mechanism built, no dependency added.
- **Reuse ledger:** none — no new reusable symbol introduced. Cluster A reuses `loremaster.store._txn.execute_transaction` (existing; the exact seam production `AgentRegistry.ensure_ready` uses); no helper/validator/predicate/constant minted anywhere.
- **Graded:** N/A (builder, not rendering a verdict on another's artifact).
- **decisions-needed:** none.
- **B1/B2/D/E option chosen (each per the ruling's "pick the tighter/prefer-X unless the seam can't express it"):** B1=allowlist (API requires SecretStr, plain str impossible); B2=exempt (seam emits Anthropic `x-api-key`, spike needs MCP Bearer/verifier plumbing); D=allowlist (parse_production_trees both widens & narrows the helper's derived reach); E=adjudicate-safe (controlled code-declared table name, un-bindable in SurrealQL).
- **Files edited (all in writable set `loremaster/tests/**`):**
  1. `loremaster/tests/test_message_ledger.py` — A
  2. `loremaster/tests/test_secret_typing.py` — B1 + B2
  3. `loremaster/tests/_surreal_harness.py` — C
  4. `loremaster/tests/test_ast_reach_helpers.py` — D
  5. `loremaster/tests/test_comms_footer.py` — E
- **receipt POINTERS:** §Cluster A–E below (each carries the RED→GREEN count tail; E carries the both-way mutation); §FINAL COMBINED VERIFICATION for the all-files green.

---

## CAPABILITY CHECK (brief-base §4)

Everything the brief demanded is satisfiable: Bash for scoped test runs, live spike-surreal test store (`ws://127.0.0.1:18000`) for the `[real]` Cluster-A tests, lore tools (loaded via `ToolSearch "+lore"`) used first-choice for symbol lookups (`execute_transaction`, `MessageLedger._query`, `signin_credentials`, `build_auth_headers`). No capability gap. No grep fallback needed for a structure question (lore resolved every symbol).

---

## PER-CLUSTER

### Cluster A — `_seed_agents` multi-statement §3 violation (135 errors → 0)

**Root cause (per diagnosis, re-confirmed):** `loremaster/tests/test_message_ledger.py::_seed_agents` routed the MULTI-STATEMENT `generate_agent_ddl()` through the single-statement `_query` → `run_query` → bare `.query()` seam, which validates statement[0] only (store ref §3). Packet-07's autouse `multi_statement_violations` guard (conftest.py) correctly flagged it. Production `AgentRegistry.ensure_ready` (`agents.py:469-490`) applies the SAME DDL correctly via `execute_transaction(f"BEGIN;\n{ddl}COMMIT;\n", …)`.

**Fix (RULING: mirror production; guard untouched):** `loremaster/tests/test_message_ledger.py`
- Added import `from loremaster.store._txn import execute_transaction`.
- `_seed_agents` now applies the agent DDL via `execute_transaction(f"BEGIN;\n{generate_agent_ddl()}COMMIT;\n", {}, acquire=ledger._ensure_connection, drop=ledger._drop_connection, url=ledger._url)` — the exact arg shape `MessageLedger._query` itself hands to `run_query` (`messages.py:628-647`) and that `ensure_ready` hands to `execute_transaction` (`agents.py:483`). This rides `query_raw` (verifies EVERY statement), which the guard's multi-statement leg deliberately excludes (`method_name == "query"` only). The `[fake]` branch is unchanged.

**RED→GREEN:** `uv run pytest loremaster/tests/test_message_ledger.py -n auto -q` →
```
241 passed, 17 skipped in 10.06s
[exited with code 0]
```
(was 130 errors). `test_comms_footer.py` (imports `_seed_agents`, was 5 errors) confirmed in the combined run below.

### Cluster B1 — SecretStr minted outside the pkt-42 allowlist (RED → GREEN)

**RULING option taken: ALLOWLIST the 3 probe files** (the API genuinely requires `SecretStr`; plain `str` is not available — so the tighter "drop the mint" option is impossible).

**API signatures read (lore_get_symbol / grep):**
- `signin_credentials(*, user: str, password: SecretStr)` (`store/_txn.py:986`) — REQUIRES `SecretStr`; unwraps via `password.get_secret_value()`.
- `SurrealStore.__init__(..., password: SecretStr)` (`store/surreal.py:406`) — REQUIRES `SecretStr` (#211: every connection owner holds one).

All three probes pass `PASSWORD` to those APIs. A plain `str` would be a type error AND a runtime `AttributeError` at `.get_secret_value()`. `"spikeroot"` is the well-known spike-surreal (TEST store) root literal — not a production credential — identical shape to the already-allowlisted `scripts/survey_txn_contention_102.py`.

**Fix:** `loremaster/tests/test_secret_typing.py` — added `scripts/probe_query_complexity_07.py`, `scripts/probe_store_error_classes_07.py`, `scripts/probe_store_recovery_07a.py` to the `allowed` tuple in `test_secretstr_is_minted_only_where_a_credential_ORIGINATES`, with an evidence-backed adjudication comment + re-open trigger ("if any probe ever sources a REAL/production credential instead of the `spikeroot` literal").

### Cluster B2 — auth headers built outside the typed seam (RED → GREEN)

**RULING option taken: ALLOWLIST (exact-path exempt) the fastmcp spike** — every one of its 6 flagged sites exercises fastmcp/MCP auth plumbing the seam genuinely cannot express.

**Seam read:** `build_auth_headers(credential: SecretStr) -> dict[str,str]` (`calibration/counting.py:75`) produces a FIXED Anthropic token-counting header set `{"x-api-key", "anthropic-version", "content-type"}`.

**The 6 spike sites (all read):** `Authorization: Bearer <token>` literals (380, 414 — including the `"Bearer WRONG"` NEGATIVE control), a FastMCP SERVER-side `auth=<verifier>` object (360 — incoming, not an outgoing header), a fastmcp `Client(auth=BearerAuth(...))` SDK object (209), and bare httpx `headers=` merges carrying `Host`/`Accept` + test tokens (385, 465). None carries a real credential; all are hardcoded MCP test literals. `build_auth_headers` emits `x-api-key` from a `SecretStr` — a different header name/scheme/source — so no site is expressible through it.

**Fix:** `loremaster/tests/test_secret_typing.py` — added exact-path exempt `_FASTMCP_SPIKE_EXEMPT = "scripts/fastmcp_migration_spike.py"` (mirroring the file's own `_INCOMING_AUTH_EXEMPT` exact-path/C1 "a path is a fact" discipline) to the skip in `_auth_construction_offenders`, with evidence + re-open trigger (real credential sent, OR `build_auth_headers` gains a `Bearer`-emitting overload).

**RED→GREEN (B1+B2):** `uv run pytest loremaster/tests/test_secret_typing.py -q` →
```
69 passed in 10.34s
```

### Cluster C — stale harness docstring counts (RED → GREEN)

**RULING: update the docstring to the DERIVED counts — re-derive BOTH populations in the same edit.**

Derived live via the test's own functions (`test_surreal_harness._harness_importer_files()` / `._connect_admin_caller_files()`):
- importers = **56** (docstring said 54)
- `connect_admin` callers = **40** (docstring said 37 — ALSO stale; the diagnosis saw only 54→56 because the importer assertion fires first)

**Fix:** `loremaster/tests/_surreal_harness.py` module docstring — `54 → 56` importers and `37 → 40` callers.

**RED→GREEN:** `uv run pytest loremaster/tests/test_surreal_harness.py -k DERIVED_counts -q` →
```
1 passed, 56 deselected in 2.07s
```

### Cluster D — un-allowlisted whole-tree parser clone (RED → GREEN)

**RULING option taken: ALLOWLIST** — `parse_production_trees` genuinely cannot express this helper's deliberately-derived reach (migrate would both widen AND narrow it).

**Reach analysis (verified against source + disk):**
- `test_ingest_entity_seam.py::_find_indexer_construction_sites(roots)` walks `_production_python_roots()` = `[loremaster/loremaster, <repo>/scripts, loremaster/scripts]` (its docstring cites CF3 / adversary-Probe-2-leg-B: "a `scripts/` construction site was silently exempt" — the "repo + member scripts" reach was bought with an adversary finding). `Indexer(...)` is a **loremaster** concept (sites: `scout.py`, `index/cli.py`, `server.py` — zero in lorerunes/loresigil/lorescribe/scripts, grep-confirmed).
- `parse_production_trees(include_scripts=True, include_skills=False)` walks `workspace_roots` = **all** member packages (`loremaster/loremaster`, `lorerunes/lorerunes`, `loresigil/loresigil`, `lorescribe/lorescribe`) + repo `scripts` only — it has NO `roots=` param and does NOT cover member-level `<member>/scripts`.
- Migrating would therefore **widen** the scan to other members (a §7 scope change, "not consolidation" — `Indexer` can't exist there) AND **narrow** away the helper's `<member>/scripts` contract. Neither matches the helper's intended reach ⇒ the shared parser cannot express what it needs.
- `test_ingest_entity_seam.py` is NOT in `_MIGRATION_SET` (confirmed), so allowlisting collides with no used-ness pin; and the file DOES carry a live clone, so the dead-entry pin (`test_the_allowlist_carries_no_dead_entries`) stays satisfied.

**Fix:** `loremaster/tests/test_ast_reach_helpers.py` — added `test_ingest_entity_seam.py` to `_ALLOWED_WHOLE_TREE_CLONE_FILES` with the full evidence above + re-open trigger ("`Indexer(...)` becomes cross-member, OR `parse_production_trees` gains a member-scripts/`roots=` param"). Matches the file's existing loremaster-scoped-single-package `test_retry_seam.py`/`test_render_seam_pins.py` entries.

**RED→GREEN (D + sibling controls):** `uv run pytest loremaster/tests/test_ast_reach_helpers.py -k "clone or allowlist or vacuous or planted" -q` →
```
9 passed, 45 deselected in 5.88s
```
**Collateral check (D migration target file):** `uv run pytest loremaster/tests/test_ingest_entity_seam.py -n auto -q` → `45 passed in 12.23s` (exit 0) — its own `TestIndexerConstructionSitesDerivedScan` still green.

### Cluster E — unregistered SAFE door (RED → GREEN + mutation both-way)

**RULING: adjudicate as SAFE — add `('loremaster/loremaster/store/surreal.py', 'entity_table')` to `KNOWN_SAFE_DOORS`. Do NOT edit `surreal.py`.**

**Adjudication (verified against source):** `surreal.py::delete_by_tier` runs `f"DELETE {entity_table} WHERE tier = $tier"` where `entity_table` iterates `self._entity_tables`. That set is a controlled, CODE-DECLARED table-name tuple fed ONLY by the composition root (`build_app_context` unions each `Extension.ingest_backends(ctx)`-declared table set via `register_entity_tables`) — NOT a comms identity, NOT user/caller input. A table NAME cannot be a bound parameter in SurrealQL (store ref §2/§4 — table/edge names are inline, only values bind); the sibling `DELETE {CHUNK_TABLE}` on the line above interpolates a table name for the identical reason (CHUNK_TABLE is a module constant so the scanner never flags it; `entity_table` is a loop var, so it needs a door). The `tier` VALUE is correctly bound `$tier`.

**Fix:** `loremaster/tests/test_comms_footer.py` — added the `entity_table` door to `KNOWN_SAFE_DOORS` with the reason above + re-open trigger ("if `entity_table`/`self._entity_tables` ever derives from user/comms/caller input").

**RED→GREEN:** `uv run pytest loremaster/tests/test_comms_footer.py -k "UNDECLARED or POSITIVE_CONTROL" -q` →
```
20 passed, 228 deselected in 1.59s
```

**MUTATION CHECK (both directions — pin still discriminates, entry did not blanket-disable):**
- Pointed the door at a wrong symbol (`entity_table_WRONG_MUTATION`) → test RE-REDS:
```
E   AssertionError: a NEW non-constant value is interpolated into store query text:
        loremaster/loremaster/store/surreal.py:1254: entity_table
    assert not [('loremaster/loremaster/store/surreal.py', 'entity_table', 1254)]
1 failed, 247 deselected in 0.76s
```
- Restored the correct symbol → GREEN again (see the combined run below). So my entry matches exactly `entity_table` and nothing else — it is not a blanket disable.

---

## FINAL COMBINED VERIFICATION

`uv run pytest loremaster/tests/test_message_ledger.py loremaster/tests/test_comms_footer.py loremaster/tests/test_secret_typing.py loremaster/tests/test_surreal_harness.py loremaster/tests/test_ast_reach_helpers.py -n auto -q` →
```
665 passed, 21 skipped in 21.49s
[exited with code 0]
```
All five affected files (the brief's exact set + `test_message_ledger.py` for A) green in one run: A's 135 errors → 0, and B1/B2/C/D/E's 5 failures → 0. The complete non-reconciling set (135 err + 5 fail = 140) from the diagnosis is resolved. `test_ingest_entity_seam.py` (D's collateral target) separately green: `45 passed`.

**Scope note (brief-base §2):** I did NOT re-run the full 8000-test suite (per brief — the ~446 auth-WIP reds for packets 39/45/48/49 are known/expected and out of my scope). No production file needed changing; the diagnosis's "production is correct" verdict held for every cluster. No file outside my writable set was touched.
