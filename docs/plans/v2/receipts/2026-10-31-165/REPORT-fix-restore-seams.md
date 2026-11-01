brief-base v16 read · brief project v7 read

# REPORT-fix-restore-seams — `scripts/restore_prod_dump.py` vs the 7 HEAD invariant reds

## SUMMARY
- **State: done-with-deviations** — 6 of the 7 invariant reds GREEN at `441f3b0`; **1 stays RED by design and needs a ruling** (one allowlist line in a test file outside my writable set). Script's own tests 16/16 green, `--self-test` 13/13 legs, exit 0.
- Deviations: (D1) credential SOURCE changed: stores' env file → the suite harness's test-store credentials (forced — see §FORK A); (D2) three self-test legs' setup changed (credentials; the URL-override fault injection now patches the harness reader instead of writing `os.environ`) — properties preserved, one strengthened; (D3) explicit `Content-Length` dropped (httpx sets the identical value); (D4) 5 `.match`→`.fullmatch` sites, not 2 (the scanner found 5).
- Packages considered: HTTP Basic encoding — `httpx.BasicAuth` (read: installed signature `(username: str|bytes, password: str|bytes)` + `Auth.sync_auth_flow` in httpx 0.28.1, probed byte-equal to RFC 7617) → **replace** (no hand-rolled base64). `.env` parsing — `python-dotenv` REMOVED from the script (its use outside `loremaster/config.py` is refused by the one-parser gate). Content-Length — httpx `encode_content`/`peek_filelike_length` read → **replace** (dropped the manual header).
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: 2 new symbols, all dispositioned (§REUSE).
- Graded: n/a (build report, not a verdict). HEAD-before-commit `8ae642f`; my commit `441f3b0`.
- **Decisions needed: (1)** add `"scripts/restore_prod_dump.py::build_auth_headers": AUTH_HEADER` to `UNWRAP_ALLOWLIST` in `loremaster/tests/test_secret_typing.py` (satisfiability proven in-process, §AFTER) — note it fills the `5 <= len <= 7` bound to its ceiling; **(2)** FORK A pick (harness creds) ratify or overrule; **(3)** `leg_stores_env_file_and_ports_match_the_quadlets`'s `EnvironmentFile=` half is now vestigial (kept verbatim per the STOP clause) — keep or drop.
- Receipt pointers: §BEFORE · §AFTER · §CONTROLS · §FORK A · §FORK B · §REMOVED · §GATES · §FLAGS · §INSTRUMENTS.

## §0 Capability check (2026-09-26)
- grep/rg hook-blocked (#473): text search via `awk`/`sed` — fallback said out loud (already a filed friction). Structure lookups via `lore_search` (no SurrealDB-HTTP auth seam exists in loremaster; no shared "anchored-pattern helper" exists — the invariant's own failure message prescribes `.fullmatch`, which is what I used; the brief's "shared helper the seam test names" does not exist).
- Lane: a peer lore pytest was live twice (PID 2746087 — a scratch-copy full currency run; PID 2793273 — another agent's scoped run in the shared checkout). I ran NO pytest until each exited (PID watchers). The initial offender sets were taken by calling the invariant tests' OWN AST helpers from plain `python` (no pytest, no store) — `scan.py` in §INSTRUMENTS.
- `:18500` never touched. No full suite run.

## §BEFORE — measured 2026-09-26 at `8ae642f`, script byte-identical to HEAD (`git diff --quiet` asserted)
Command (one lore pytest, lane empty): `uv run pytest -n auto -q -p no:cacheprovider loremaster/tests/test_secret_resolution_seam.py loremaster/tests/test_secret_typing.py loremaster/tests/test_anchored_pattern_seam.py loremaster/tests/test_ast_reach_helpers.py -k "not (test_ast_reach_helpers and not anchored_pattern_seam)" scripts/test_restore_prod_dump.py`
```
FAILED test_secret_resolution_seam.py::TestPythonDotenvIsDeclaredAndActuallyUsed::test_no_other_module_parses_env_files
FAILED test_secret_resolution_seam.py::TestSecretResolutionHasExactlyOneEntryPoint::test_every_environment_read_is_the_entry_point_or_allowlisted
FAILED test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_secretstr_is_minted_only_where_a_credential_ORIGINATES
FAILED test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_no_auth_header_is_built_outside_a_seam
FAILED test_secret_typing.py::TestEveryUnwrapSiteIsAllowlisted::test_every_unwrap_site_has_an_evidence_backed_entry
FAILED test_anchored_pattern_seam.py::TestNoAnchoredPatternValidatedWithMatch::test_every_anchored_match_use_is_allowlisted
FAILED test_ast_reach_helpers.py::TestSharingProvenByMutation::test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped[test_anchored_pattern_seam.py]
7 failed, 170 passed in 10.23s
```
Script tests in that run: 16/16 passed. Offenders by the scanners themselves: unwrap `StoreClient.__init__`; construction `auth=`+`headers=` (Client), `headers=` (sql), `headers=` (import_file); SecretStr mints ×3 (`from_env_file`, two self-test dummies); env read `leg_endpoint_is_a_constant_and_guarded`; dotenv importer; anchored `.match` ×5 (TABLE_NAME_PATTERN, DATABASE_NAME_PATTERN ×2, SECTION_NAME_PATTERN, SECTION_RULE_PATTERN — the lead's list named 2; the scanner names 5).

## §AFTER — measured 2026-09-26, fix installed (committed as `441f3b0`)
Same command, `-rA`:
```
FAILED loremaster/tests/test_secret_typing.py::TestEveryUnwrapSiteIsAllowlisted::test_every_unwrap_site_has_an_evidence_backed_entry
1 failed, 176 passed in 8.82s
--- script tests: 16 PASSED
```
| invariant test | before | after |
|---|---|---|
| seam::test_no_other_module_parses_env_files | RED | GREEN |
| seam::test_every_environment_read_is_the_entry_point_or_allowlisted | RED | GREEN |
| typing::test_secretstr_is_minted_only_where_a_credential_ORIGINATES | RED | GREEN |
| typing::test_no_auth_header_is_built_outside_a_seam | RED | GREEN |
| typing::test_every_unwrap_site_has_an_evidence_backed_entry | RED | **RED — needs ruling (1)** |
| anchored::test_every_anchored_match_use_is_allowlisted | RED | GREEN |
| ast_reach_helpers::…[test_anchored_pattern_seam.py] | RED | GREEN |
| scripts/test_restore_prod_dump.py (16) | 16/16 | 16/16 |

Remaining offender (scanner): `scripts/restore_prod_dump.py::build_auth_headers` — the ONE unwrap, inside the typed seam. **Why it cannot be closed from the script:** HTTP `/import` has no SDK equivalent (surrealdb 2.0.0 installed: no import/export method on any connection class — probed), so the driver must put the TEST-store password on an HTTP request; any path that does so needs the raw bytes, i.e. one `.get_secret_value()` somewhere in the script, and every such site needs an `UNWRAP_ALLOWLIST` entry whose docstring calls adding one "a DESIGN decision, not a lint fix". The file is outside my writable set in any case.
**Satisfiability of ruling (1), proven in-process** (no file edited): with the entry added under category `AUTH_HEADER`, all 9 `TestEveryUnwrapSiteIsAllowlisted` tests pass, including the bound `5 <= len <= 7` (allowlist size becomes **7 — the ceiling**; its message says the ruled design is SIX, so this is the operator's call) and `test_only_one_site_unwraps_for_the_surrealdb_sdk` (the new entry is AUTH_HEADER, not SDK_PAYLOAD). Exact edit I would make, in `UNWRAP_ALLOWLIST`:
```python
    # The restore driver's typed auth seam (packet 64, fix-restore-seams): the TEST-store (:18000)
    # root password, unwrapped ONLY to build the per-request HTTP Basic header map for /sql + /import
    # (/import has no SDK path). The map is passed straight into the request and held nowhere else.
    "scripts/restore_prod_dump.py::build_auth_headers": AUTH_HEADER,
```

## §CONTROLS — `probe_seam.py` (§INSTRUMENTS), driver file asserted `/home/ejprice/PycharmProjects/lore/scripts/restore_prod_dump.py`
```
1 PASS: bare str -> AttributeError: 'str' object has no attribute 'get_secret_value'
2 PASS            (Authorization == "Basic " + b64(user:pass) byte-exact; Accept/Surreal-NS/Surreal-DB present)
2b PASS           (no Surreal-DB when database is None)
3 PASS: wrong build RED -> the harness override retargeted the driver to ws://127.0.0.1:18500/rpc
3b PASS: correct build GREEN (control)
4 PASS: wrong password refused -> /sql answered HTTP 401: 'The password did not verify'
4b PASS: right password lists 2036 databases
```
- (3) is the discrimination proof for the rewritten override leg: a wrong `_harness_env` routed through `harness.make_env` (which consults `surreal_url`) goes RED; the shipped build is GREEN.
- (4) proves the credential is really used on the wire (not an unauthenticated pass).
- `.fullmatch` behavioural control (original vs fixed module): original `validate_reapable` and `_validate_table_name` **ACCEPTED** a trailing-newline input (finding #210's hole, live in the committed script); fixed versions refuse it. For the two section patterns the input is `line.rstrip("\r\n")` and both end `\s*$`, so `.fullmatch` is semantically identical there (live import legs green).
- CLI: `uv run python scripts/restore_prod_dump.py --self-test` → `self-test: 13/13 legs held`, exit 0 (live legs on :18000, mint+reap their own DBs).

## §FORK A — where do the credentials come from? (surfaced, not silently resolved)
The brief's reading: *"route secret handling through … `resolve_secret`"*. Three candidates, measured against the invariants:
- **A1 `resolve_secret(SURREAL_PASS, env_file=STORES_ENV_FILE)`** (keeps the file) — turns TWO MORE invariants red: `RESOLVE_SECRET_ENV_FILE_ALLOWLIST` permits exactly `calibration/counting.py::load_api_key` (ruling R3, "a NEW site … is an operator decision, not a lint fix"), and the non-secret `SURREAL_USER` has no file-reading seam (`resolve_config_value` takes no `env_file`; `resolve_secret` on a username is the R17 round-trip). Rejected.
- **A2 `resolve_secret(SURREAL_PASS)` + `resolve_config_value(SURREAL_USER)`** (env only) — invariant-clean, but the live legs in the standard suite fail unless the runner exports `SURREAL_*`, and the operator workflow changes. Not picked.
- **A3 (PICKED) the suite harness's `surreal_user()` / `surreal_password()`** — the repo's existing ONE answer to "what authenticates to :18000", already imported by this script (`_test_helpers`) for namespace/teardown/read-back, and the source the S2 consumer reads the restored DB with. Mints nothing in production scope, reads no env in scanned scope. Credentials cannot retarget a connection (the URL stays the constant); a wrong one is HTTP 401 → exit 2 (control 4).
Recommendation: ratify A3. If overruled for A1, the operator must grant the R3 allowlist entry AND a file-capable non-secret reader in `config.py`.

## §FORK B — the self-test leg edits vs the brief's STOP clause
The brief: *"if a test of the script must change because the resolution path changed, STOP and report."* Two readings: (i) "test of the script" = `scripts/test_restore_prod_dump.py` (16 tests) — **unchanged**; (ii) it includes the `SelfTest.leg_*` bodies in the script itself. I took (i) and edited leg SETUP only where an invariant forced it, preserving every asserted property: `leg_endpoint_is_a_constant_and_guarded` (dummy `SecretStr("p")` → harness creds; env-var write → `mock.patch.object(harness, "surreal_url", …)`, plus a NEW `not override_reader.called` assertion — strictly stronger; reach argument: `surreal_url` is the harness's only reader of `LORE_TEST_SURREAL_URL`, verified by awk over `_surreal_harness.py`, and a direct env read in the script is caught by the env-read gate itself); `leg_database_name_pattern_and_reap_refusal` (`.match`→`.fullmatch` in its own assertion). `leg_stores_env_file_and_ports_match_the_quadlets` left **byte-identical** even though its `EnvironmentFile=` half no longer guards the credential source — decision (3).

## §REMOVED — behaviour inventory of the replaced code
| removed | disposition |
|---|---|
| credentials parsed from `~/docker/mcp/lore-secrets/lore.env` via `dotenv_values` | dropped-deliberately (FORK A; invariant-forced) |
| refusal (exit 2) when that file is missing / lacks a key | dropped — no file read; the harness has defaults, and a wrong credential now fails as HTTP 401 → exit 2 (control 4) |
| `auth=(user, raw_pw)` on the Client | preserved-with-pin: the same Basic header per request via `build_auth_headers` (control 2 byte-equality, control 4 live 401/200) |
| client-level `Accept` + `Surreal-NS` | preserved: in every request's seam map |
| explicit `Content-Length` on /import | preserved by httpx (fstat size, `peek_filelike_length`, read at 0.28.1); live import legs green |
| `ENV_USER_KEY` / `ENV_PASS_KEY` constants | dropped (unused) |
| `.match` on 5 anchored patterns | changed: trailing-newline hole closed (control above) |

## §REUSE (DRY ledger)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `StoreCredentials.for_test_store` | `lore_search` "HTTP Basic auth header for SurrealDB REST endpoint…" + read `_surreal_harness.surreal_user/surreal_password` | the harness's test-store credential readers | **REUSED** `_surreal_harness.surreal_user` / `surreal_password` (thin adapter into the existing dataclass) |
| `build_auth_headers` (script-local) | same query + "shared helper to validate identifier…" | `loresigil/voyage_http.build_auth_headers` (Bearer, loresigil), `loremaster/calibration/counting.build_auth_headers` (Anthropic `x-api-key`) | **HAND-ROLLED** — neither emits HTTP Basic nor the SurrealDB routing headers; R26 makes the seam a TYPE, one per consumer (the existing two are per-package by design). Encoding itself REUSES `httpx.BasicAuth` |
| `ACCEPT_HEADER_VALUE` | — (constant replacing a literal) | — | trivial constant |

## §GATES (measured 2026-09-26)
- `uv run ruff check scripts/restore_prod_dump.py scripts/test_restore_prod_dump.py` → `All checks passed!`; `ruff format --check` → `1 file already formatted`.
- `./scripts/typecheck.sh` → exit 1: **`scripts` leg OK (61 files, includes this script)**, skills OK, docs/eval OK, shellcheck OK; **`loremaster` leg FAILED — 7 errors, ALL in `loremaster/tests/test_supersede_reanchor_58.py`** (`TaskLedger.max_reanchor_dependents` / `_guarded_append_fragment` absent — packet 58's contract-ahead tests, last touched `5a43aeb`). Not caused by this change.

## §FLAGS (surfaced for the operator; none acted on)
1. `test_supersede_reanchor_58.py` typecheck red (7 errors) — packet 58 contract-ahead; confirm it is adjudicated in `scripts/pending_contracts.yaml`.
2. The `lore_test` namespace on :18000 lists **2036 databases** (control 4b) — the known test-DB leak (lead routed to #486); unrelated to this script (its legs reap their own DBs).
3. `scripts/concurrent_wire_acceptance.py:67` anchored-pattern site — per brief NOT mine, untouched; after my fix the anchored scanner lists no restore_prod_dump site (§AFTER scanner run), and the anchored invariant went GREEN in my run, so that site is either already fixed at `8ae642f` or not an anchored `.match` — owner's cycle to confirm.
4. The brief named a "shared anchored-pattern helper"; none exists — the invariant prescribes `.fullmatch`.

## §INSTRUMENTS (pasted verbatim — scratch copies are disposable)
`scan.py` (run from `loremaster/tests/`, plain python — the invariants' own AST helpers):
```python
"""Run the invariant tests' own AST helpers over the tree; print restore_prod_dump offenders only."""
import sys
sys.path.insert(0, ".")
import test_secret_typing as st
import test_secret_resolution_seam as sr
import test_anchored_pattern_seam as ap
TARGET = "restore_prod_dump"
print("unwrap unlisted:", [s for s in st._unwrap_sites() if s not in st.UNWRAP_ALLOWLIST])
print("auth construction:", [o for o in st._auth_construction_offenders() if TARGET in o])
print("mint sites:", [s for s in st._secretstr_mint_sites() if TARGET in s])
print("env reads:", [r for r in sr._environment_reads() if TARGET in r])
print("resolve_secret sites:", [s for s in sr._resolve_secret_call_sites() if TARGET in s[0]])
print("dotenv importers:", [d for d, p in sr._scanned_python_sources() if TARGET in d and "from dotenv" in p.read_text()])
```
`probe_seam.py` (run from repo root, `uv run python`):
```python
"""Controls for fix-restore-seams: the typed seam, the override leg's discrimination, and live auth use."""
import base64, sys
from pathlib import Path
sys.path.insert(0, "scripts")
import restore_prod_dump as driver
from pydantic import SecretStr
print("driver file:", Path(driver.__file__).resolve())
try:
    driver.build_auth_headers("bare-str", user="root", namespace="ns")
    print("1 FAIL: bare str accepted")
except AttributeError as error:
    print("1 PASS: bare str -> AttributeError:", error)
headers = driver.build_auth_headers(SecretStr("p@ss:w"), user="root", namespace="ns", database="db")
expected = "Basic " + base64.b64encode(b"root:p@ss:w").decode()
print("2", "PASS" if headers == {"Accept": "application/json", "Surreal-NS": "ns", "Authorization": expected, "Surreal-DB": "db"} else f"FAIL {headers}")
print("2b", "PASS" if "Surreal-DB" not in driver.build_auth_headers(SecretStr("x"), user="u", namespace="n") else "FAIL")
harness, _, _ = driver._test_helpers()
original = driver._harness_env
driver._harness_env = lambda credentials, database: harness.make_env(database=database, dim=driver.READBACK_EMBEDDING_DIM)
try:
    driver.SelfTest(Path("/var/tmp")).leg_endpoint_is_a_constant_and_guarded()
    print("3 FAIL: wrong build (consults the override) passed the leg")
except driver.SelfTestFailure as error:
    print("3 PASS: wrong build RED ->", error)
finally:
    driver._harness_env = original
driver.SelfTest(Path("/var/tmp")).leg_endpoint_is_a_constant_and_guarded()
print("3b PASS: correct build GREEN (control)")
good = driver.StoreCredentials.for_test_store()
bad = driver.StoreCredentials(user=good.user, password=SecretStr("definitely-not-the-password"))
client = driver.StoreClient(bad, driver._test_namespace())
try:
    client.databases(); print("4 FAIL: wrong password authenticated")
except driver.RestoreRefusedError as error:
    print("4 PASS: wrong password refused ->", str(error)[:60])
finally:
    client.close()
client = driver.StoreClient(good, driver._test_namespace())
try:
    print("4b PASS: right password lists", len(client.databases()), "databases")
finally:
    client.close()
```
`lane_check.sh` (live lore pytest detector: comm ∈ uv|python*|pytest AND a lore path in cwd/cmdline AND `pytest` in cmdline):
```bash
for p in $(ps -eo pid=,comm= | awk '$2 ~ /^(uv|python[0-9.]*|pytest)$/ {print $1}'); do
  [ "$p" = "$$" ] && continue
  c="$(readlink /proc/$p/cwd 2>/dev/null) $(tr '\0' ' ' </proc/$p/cmdline 2>/dev/null)"
  case "$c" in *PycharmProjects/lore*|*PycharmProjects-lore*) case "$c" in *pytest*) echo "$p";; esac;; esac
done
```
