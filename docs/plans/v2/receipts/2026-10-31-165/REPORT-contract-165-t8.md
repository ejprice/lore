brief-base v24 read

# REPORT-contract-165-t8 — shared meaning-based fake for `_read_config_field` (#165 T8)

## SUMMARY (measured 2026-10-31 17:53–18:10Z, base HEAD `6f0f09f` + this change's uncommitted test edits)
- receipts: `brief-base v24 read` · `brief project v7 read` (lore_comms register, session fix-165-2026-10-31)
- state: **done-with-deviations**
- deviations: (1) the control and reference legs ran sequentially in ONE scratch (old 6f0f09f tests first, then the migrated ones copied in), not in two scratches; (2) 7 runs, not ~2: reasons in §Runs; (3) the typecheck currency leg was added (repo law allows it every round); (4) one stale comment beyond the two named was rewritten (`test_lore_deploy.py`, the "# 4. .mcp.json was re-merged" block, which described the deleted stub).
- Packages considered: stdlib `contextlib.redirect_stdout` + `exec`, run over production's own `lore_deploy._schema_load_snippet` → `replace_with_adapter`. What I read: the `_read_config_field` and `_schema_load_snippet` source (`lore_get_symbol`), plus a live smoke of the fake. No package builds the model better than production's own snippet, which the fake runs unchanged. `pytest.MonkeyPatch` (installed) installs it.
- Odoo-20 portability: n/a — no Odoo seam touched
- Reuse ledger: 5 new symbols, all dispositioned (§DRY ledger)
- Graded: n/a (contract author; no verdict on another agent's artifact)
- decisions-needed: none blocking. 3 flags for the lead in §Noticed (stale production comment; the fake's `config_path` bound; the oracle's driver-reach bound).
- Fake: `skills/lore-deploy/scripts/config_reader_fake.py` (`ConfigReaderFake`, `realistic_config_document`, `write_config_document`, `RECORDED_STATIC_TIERS`)
- Oracle pin: `test_lore_deploy.py::TestConfigReaderFakeOracle` (10 tests, real subprocess reader)
- Runs, final: HEAD **162 passed / 0 failed** (`t8-head3.log`) · reference **162 passed / 0 failed** (`t8-reference2.log`) · control **23 failed / 129 passed**, all 23 `TypeError: cannot unpack non-iterable int object` (`t8-control.log`) · ruff GREEN · typecheck RED_ADJUDICATED (owned by other packets; 0 orphans from this change, `t8-currency2.log`)
- **Prod-URL fix (directive #18005):** the fake's default `surreal.url` is now the dead `ws://127.0.0.1:9/rpc` (it was the prod store :18500). The guarded HEAD run is `162 passed, LOADED=9 HITS=0`; the positive control is `HITS=4`. HEAD after the fix: 162/0. Oracle: 10/0. Whether any PRE-fix run touched prod is unproven (§Prod-URL fix).
- pointers: §Runs · §Sites · §Production-expression set · §Reference change (verbatim diff) · §Prod-URL fix · logs under `/var/tmp/claude-1000/t8-*.log`

## Routing table (written before any sweep, per brief-base §3)

| step | tier | who | reason |
|---|---|---|---|
| A. inventory sweep (stub sites + production exprs, awk over git ls-files) | 1 | haiku-worker | routed by the brief; a literal command |
| A'. classify hits (STUB vs PROD expr) | 3 | me | the brief assigns it to me. Each verdict needs a read of the enclosing function, which is state outside the span. A sampled draft would miss stubs installed through helpers or fixtures whose names hide the target. 50 hits, read in one pass. |
| D2. scratch copy for reference leg | 1 | haiku-worker | routed by the brief; ran in parallel with A |
| B. read `_schema_load_snippet`, `_read_config_field`, `_loremaster_python`, `_RecreatePathFixture` | inline batch (4 `lore_get_symbol` calls, one message) | me | these feed the fake's semantics directly; small, read whole |
| C. fake + migration + oracle pin | 3 | me | contract authorship |
| D1/D3/D4 runs | 1 | haiku-runner | routed by the brief |
| E. ruff + typecheck currency legs | 1 | haiku-runner | ruff routed by the brief; the typecheck leg is an addition |

`Fan-out: haiku 9 (2 worker, 7 runner) · sonnet 0 · peak 3`

## The fake: location and semantics

**Where it lives:** `skills/lore-deploy/scripts/config_reader_fake.py`. This is a plain module, not a `test_*` module, so pytest does not collect it.
- Both test trees import it the same way they import `lore_deploy`. `scripts/` reaches it through `python -m pytest` run from that directory (cwd on `sys.path`). `tests/test_workspace_probe.py` already does `sys.path.insert(0, SCRIPT_DIR)`.
- I chose this over the precedent of importing from `test_lore_deploy`. Importing a test module drags its tests' fixtures and globals into the importer, and a helper has no tests of its own to carry.

**How it works:** `ConfigReaderFake(document, store_dir)`.
- It serialises the document once to `store_dir/config-reader-fake.lore.yaml`.
- Each call execs `f"{lore_deploy._schema_load_snippet(<that file>)};print({expr})"` in-process, under `contextlib.redirect_stdout`, in a fresh `{"__name__": "__main__"}` namespace.
- `ConfigReaderFake.install(monkeypatch, store_dir, document=None, **fields)` patches it over `lore_deploy._read_config_field`.
- `realistic_config_document(slug=, server_port=, server_path=, surreal_url=, static_tiers=)` builds a schema-valid document. Its values were recorded from this repo's `lore.yaml` on 2026-10-31 at 6f0f09f. It is production-shaped and never production-sourced at test time.

How each behaviour matches the real reader:

| real `_read_config_field` | fake | pinned by |
|---|---|---|
| binds `c` via `_schema_load_snippet` (`LoreConfig.model_validate(yaml.safe_load(file))`; schema-only, no secret) | runs **the same function's output**, so a snippet change reaches it unchanged | every oracle test |
| file content = YAML the reader parses | the document goes through `yaml.safe_dump` → the file → `yaml.safe_load` | every oracle test (same file format for both) |
| globals: `yaml`, `Path`, `LoreConfig`, `c`, builtins (`__import__`) | the identical snippet, so the identical names | `_unmaterialised_static_tiers`'s `Path(...)` / `__import__` expression agrees (oracle) |
| `print({expr})` text substitution, so a comma expression prints space-separated | the same text substitution | `test_multi_argument_print_semantics_agree` |
| returns `stdout.strip()` | returns `captured.getvalue().strip()` | every oracle test |
| non-zero exit → `RuntimeError(f"failed to read {expr!r} from {config_path}: …")` | any exception → `RuntimeError` with the same prefix (`TypeName: message` instead of the stderr traceback) | `test_both_readers_raise_runtime_error_on_an_invalid_config[bad_port_type, unknown_top_level_key]`, `…_on_a_failing_expression` |
| reads `config_path` | **does NOT read `config_path`.** It records it in `.calls` and answers from its own document. Deliberate bound, see §Noticed 2. | — |

## Sites: old stub → new config (11 sites, plus 1 helper deleted)

The awk sweep found 50 hit lines over `files_listed=18` (`/var/tmp/claude-1000/t8-sites.txt`). I classified them by reading each enclosing function:
- 11 STUB installs;
- 13 PRODUCTION call lines;
- 1 production comment;
- `test_launch_snapshot_bind.py`: 5 lines, all docstrings or the real-reader capture and restore, so no stub of its own. Untouched, as the brief allows.
- `test_read_config_field.py`: 10 lines that call the real reader. Untouched.

| site (6f0f09f line) | old stub | new |
|---|---|---|
| `test_lore_deploy.py:40` `test_launch_container_uses_host_user_home…` | `lambda *a, **k: "0"` (every expr → "0") | `ConfigReaderFake.install(monkeypatch, tmp_path/"config-reader")`: live-only, port 9201, `/mcp`. The "/source mount" comment is rewritten. |
| `:102–107` `test_start_when_already_running_still_rewires_mcp_json` | local `"port" in expr` → 9201, else `/mcp` | `install(..., slug=PROJECT_SLUG, server_port=LORE_SERVER_PORT, server_path=LORE_MOUNT_PATH)`; the "contents are irrelevant — stubbed below" comment is rewritten |
| `:214` module `_stub_read_config_field` (`"port"`→9201, `"static"`→"0", else `/mcp`) | — | **deleted** and replaced by `_install_config_reader(monkeypatch, tmp_path)` (live-only, `_LORE_SERVER_PORT`, `_LORE_MOUNT_PATH`). This also removes the "/source mount" comment at ~219. |
| `:330` stale-image recreate | module stub | `_install_config_reader(monkeypatch, tmp_path)` |
| `:450` current-image no-op | module stub | same |
| `:549` fresh launch reconnect reminder | module stub | same |
| `:833` `_RecreatePathFixture.wire_running_and_stale` | module stub | `_install_config_reader(self.monkeypatch, self.tmp_path)` |
| `:1316` `TestProbeSurreal._stub_url_read` | `lambda: self._RPC_URL` for every expr | `install(..., surreal_url=self._RPC_URL)`; the signature gains `tmp_path`, and its 4 callers pass it |
| `:1469` `test_start_proceeds_when_surreal_probe_ok` | module stub | `_install_config_reader` |
| `:1510` `test_start_aborts_when_surreal_probe_fails` | module stub | `_install_config_reader` |
| `test_workspace_probe.py:759` `_arrange` | `lambda c, e: "0"` | `install(..., server_port=9201, server_path=_MOUNT_PATH)`, agreeing with that test's `_read_server_block` stub |
| `test_workspace_probe.py:887` (real-gates arrangement) | `lambda c, e: "0"` | `install(..., server_port=port, server_path=_MOUNT_PATH)`, agreeing with its `_read_server_block` stub |

No assertion was weakened, retargeted or re-scaled. Every migrated config carries zero static roots, the same meaning the old `"0"` and `"static"`→"0" answers encoded. The only value that changed meaning: site 40's port reads would have answered "0" and now answer 9201. No assertion in that test reads the port.

## Production-expression set (how collected, so it is checkable)

**How:** the awk sweep (literal `_read_config_field` occurrences, `git ls-files -- skills/lore-deploy`, 18 files) plus a read of each enclosing function in `lore_deploy.py` at 6f0f09f. That gives 13 call lines in 6 owning functions:

| owning function | expressions (at 6f0f09f) |
|---|---|
| `_read_server_block` | `c.server.host`, `c.server.port`, `c.server.path` |
| `_require_launchable_snapshot` | `_STATIC_ROOT_COUNT_EXPR` (`sum(1 for r in c.roots if r.watch == 'static')`) |
| `_unmaterialised_static_tiers` (called by the above when count > 0) | `__import__('json').dumps({failing-tier dict comprehension over SnapshotLayout(Path(SNAPSHOT_ROOT))})`, built at call time |
| `_probe_embed` | `c.embedding.base_url`, `.endpoint`, `.api_key_env`, `.dim` |
| `_probe_surreal` | `c.surreal.url` |
| `_merge_mcp_from_config` | `c.server.port`, `c.server.path` |

**How the oracle covers it:** `TestConfigReaderFakeOracle` never retypes these strings. It DRIVES the six owning functions with an `_OracleTee`, which answers with the REAL reader so production follows its real path and records `(expr, real, fake)` for every read. Each driver must make ≥1 read, and every row must agree.
- The config is realistic, with non-default values: port 9208, path `/lore/mcp`, a `wss://` surreal URL.
- It declares two prefix-sharing recorded static tiers, one materialised under a tmp `SNAPSHOT_ROOT` and one not, so the per-tier answer is a non-empty dict that names the missing tier.
- The all-materialised case is a separate test.
- Failing configs: a bad port type and an unknown top-level key, where both readers raise `RuntimeError` for `c.server.port` and the count expression. A failing expression (`c.server.no_such_field`) raises in both, with a valid-document control.

**Speed:** about 20 real loremaster subprocesses. Measured inside the full skill run (162 tests, `-n 8`), the whole run took 10.0 s, so I left the class unmarked and in the default run.

## Runs (each `RAN:` checked to be my command; counts read from the logs myself)

| # | label | log | result |
|---|---|---|---|
| 1 | HEAD after migration | `t8-head.log` | **162 passed** (152 pre-migration + 10 oracle; the 10 confirmed by `--collect-only`), EXIT=0 |
| 2 | currency typecheck,ruff | `t8-currency.log` | typecheck **RED_ORPHANED 1, mine**: `probed.append(url) or True` [func-returns-value]. Fixed with a closure. ruff GREEN. |
| 3 | HEAD re-run after the typecheck fix | `t8-head2.log` | 162 passed, EXIT=0 |
| 4 | currency re-run | `t8-currency2.log` | typecheck RED_ADJUDICATED (83 residuals, owned by packet-58-contract and packet-64b-i-contract; none in skills/), **0 orphans**; ruff GREEN; pytest NOT_RUN (by design for `--legs`) |
| 5 | **CONTROL**: reference change + OLD tests (byte-identical to `git show 6f0f09f:<path>`, checked with `cmp`) | `t8-control.log` | **23 failed / 129 passed** (152 = the brief's pre-migration count). All 23 `TypeError: cannot unpack non-iterable int object`: the merged read got `"9201"` from the shared substring stub (`"port"` is a substring of `__import__`) or `"0"` from the lambda stubs. Provenance: `loremaster → /var/tmp/claude-1000/t8-scratch/loremaster/loremaster/__init__.py`, `lore_deploy → /var/tmp/claude-1000/t8-scratch/skills/lore-deploy/scripts/lore_deploy.py` |
| 6 | reference + migrated tests | `t8-reference.log` | **161 passed / 1 failed**. The failure was MY oracle test's `assert len(tee.rows) >= 2`, which pinned *how many reads* production makes: the coupling class this change removes. The fake and the real reader AGREED on the merged read. I removed the assertion and kept the meaning check (the agreed answer names the missing tier). |
| 7 | reference re-run + HEAD final | `t8-reference2.log`, `t8-head3.log` | reference **162 passed / 0 failed**, provenance `loremaster`, `lore_deploy` and `config_reader_fake` all under `/var/tmp/claude-1000/t8-scratch/…`; HEAD **162 passed / 0 failed** |

Every run used `LORE_PYTHON=/var/tmp/claude-1000/t8-scratch/.venv/bin/python` for the scratch legs (finding #558), `systemd-run … MemoryMax=16G`, `-n 8` and `--timeout=300`. The extra runs are a fixture fix (2→3), its currency confirmation (4), and a contract fix the reference leg exposed (6→7).

### Reference change (satisfiability instrument, verbatim; applied ONLY in scratch, `/var/tmp/claude-1000/t8-reference.diff`)
```diff
-_STATIC_ROOT_COUNT_EXPR = "sum(1 for r in c.roots if r.watch == 'static')"
+_STATIC_ROOT_COUNT_EXPR = (
+    "sum(1 for r in c.roots if r.watch == "
+    "__import__('loremaster.config', fromlist=['WATCH_STATIC']).WATCH_STATIC)"
+)
@@ _unmaterialised_static_tiers
-def _unmaterialised_static_tiers(config_path: Path) -> dict[str, str]:
+def _unmaterialised_static_tiers(config_path: Path) -> str:
@@
-    failing: dict[str, str] = json.loads(
-        _read_config_field(config_path, f"__import__('json').dumps({failing_tier_dirs})")
+    return failing_tier_dirs
+
+
+def _snapshot_precondition_read(config_path: Path) -> tuple[int, dict[str, str]]:
+    """REFERENCE (T8 satisfiability): ONE read returning the static count and failing tiers."""
+    count, failing = json.loads(
+        _read_config_field(
+            config_path,
+            f"__import__('json').dumps([{_STATIC_ROOT_COUNT_EXPR}, {_unmaterialised_static_tiers(config_path)}])",
+        )
     )
-    return failing
+    return int(count), dict(failing)
@@ _require_launchable_snapshot
-    static_root_count = _read_config_field(config_path, _STATIC_ROOT_COUNT_EXPR)
-    if static_root_count in ("", "0"):
+    static_root_count, failing = _snapshot_precondition_read(config_path)
+    if static_root_count == 0:
         return False
-    failing = _unmaterialised_static_tiers(config_path)
```
This is a reference for satisfiability only, not a recommended build. Any real version of it should rename `_unmaterialised_static_tiers` (it now returns an expression) and fix the docstring.

## Adversarial pre-flight → coverage
- **Wrong unit/type in the answer** (port as int vs str): the fake returns the printed str, the same as the real reader. Pinned by oracle equality.
- **Print semantics** (comma expr, embedded prints): `test_multi_argument_print_semantics_agree`.
- **Validation failure, two doors** (bad type; `extra="forbid"` key): the parametrized invalid-config test.
- **Expression error**: the failing-expression test, with a valid-document control.
- **Degenerate driver** (zero static roots, so the per-tier read is never reached): covered by the migrated sites (live-only). The oracle uses ≥1 static root so the per-tier read IS reached, and a non-empty answer is required.
- **Prefix-sharing tiers** (`surrealdb-docs` / `surrealql-tests`): used in the oracle.
- **Producer↔consumer seam: `SNAPSHOT_ROOT` crosses into the expression text**: the oracle patches it to tmp; both readers stat the same path.
- **Interpreter seam** (pytest interpreter in-process vs the `LORE_PYTHON` subprocess): the oracle compares across exactly that seam.
- **Fake ignores `config_path`**: scoped out as a deliberate bound (§Noticed 2).
- **A new read site outside the 6 drivers**: scoped out as a bound (§Noticed 3).

## Realism clauses
- ☑ Production-realistic inputs: the document was recorded from the repo's `lore.yaml` (2026-10-31), with ports in the real `DEFAULT_PORT_BASE` range and real static-tier names. Nothing is read live at test time.
- ☑ Independent expected values: the oracle's expected value is the REAL reader's answer, never the fake's formula. The supporting asserts use the declared document values (port, path, the URL → health URL via production's `_surreal_health_url`).
- ☑ Seam coverage: the real host→loremaster subprocess seam is exercised over the same file the fake reads.
- ☐ Magnitude bound: not applicable. No numeric output is derived; config reads are lookups.
- ☑ Shared conventions: `DEFAULT_PORT_BASE`, `SnapshotLayout.materialization_dir` and `_surreal_health_url` come from production. Static tiers are `RECORDED_STATIC_TIERS`.
- ☐ Hostile fixtures: not applicable. Nothing renders stored free text.
- ☐ Input accounting: not applicable. No collection transform.

## DRY ledger
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `ConfigReaderFake` | `lore_get_symbol _read_config_field` / `_schema_load_snippet`; the awk sweep over the skill trees | the 11 ad-hoc stubs (the defect) and no shared fake | HAND-ROLLED as the ONE shared fake. Its config construction is REUSED from `lore_deploy._schema_load_snippet` (never cloned). |
| `realistic_config_document` | `lore_deploy._scaffold_lore_yaml` (production builder); `test_launch_snapshot_bind._repo_config_document` | the scaffold writes a file AND shells out (`_free_port`, a subprocess validation) and has `roots: []`; snapshot_bind derives from the live repo `lore.yaml` (host-path static sources) | HAND-ROLLED as a recorded literal. Neither candidate is hermetic with parametrised fields. |
| `write_config_document` | same | snapshot_bind writes inline with `yaml.safe_dump` | HAND-ROLLED (one line), shared by the fake and the oracle |
| `RECORDED_STATIC_TIERS` + `RECORDED_*` constants | repo `lore.yaml` | the source of the values | recorded literals (clause 5) |
| `_install_config_reader`, `_OracleTee`, `TestConfigReaderFakeOracle` (test-local) | — | — | test-local; `_install_config_reader` replaces the deleted `_stub_read_config_field` |

## Noticed (for the lead)
1. **Stale production comment:** `lore_deploy.py`, the comment above `_STATIC_ROOT_COUNT_EXPR`, says `'static'` is spelled out because the substring stubs misread `__import__`. Once this lands that reason is false, and the brief forbids me to edit production. Suggested edit: drop the last clause, or adopt `WATCH_STATIC` (reference (a) shows it is now satisfiable).
2. **The fake's bound:** it answers from its own document and never reads `config_path` (tests keep `"# stub"` `lore.yaml` placeholders for the presence pre-flight). A production build that read the WRONG config file passes any test that uses the fake. The old stubs had the same blindness, so this is not new. `.calls` records the path if a test wants to pin it. Re-open trigger: a defect where production reads the wrong config file.
3. **The oracle's reach bound:** it drives the 6 functions that own a read at 6f0f09f. A NEW caller of `_read_config_field` in another function is not compared until a driver is added. The awk sweep in this report is the checkable inventory to re-run. Re-open trigger: any new `_read_config_field(` line in `lore_deploy.py` outside those 6 functions.
4. `test_launch_snapshot_bind.py`'s `_VerbStartArrangement` docstring says the fixture "stubs it to '0 static roots'". It now installs the fake over a live-only config. The meaning is still accurate, so I left it unedited (outside my edit licence for that file).
5. The control confirms the brief's pre-migration count: the old tests collect exactly 152.
6. Scratch `/var/tmp/claude-1000/t8-scratch` still exists, holding the reference change. Backups of the 3 original test files are in `/var/tmp/claude-1000/t8-backup/`. Both are disposable.

## Prod-URL fix (lead directive #18005, thread t8-prod-url, 2026-10-31)

**Defect:** `config_reader_fake.RECORDED_SURREAL_URL` defaulted to `ws://127.0.0.1:18500/rpc`, the PRODUCTION lore-surreal store. The old stubs answered junk (`/mcp`) for `c.surreal.url`. The fake answers a real URL, so any test that leaves `_probe_surreal` / `_probe_surreal_health` unstubbed would really `GET /health` production.

**Fix:** the constant is renamed `DEAD_SURREAL_URL = "ws://127.0.0.1:9/rpc"`: the same `ws://host:port/rpc` shape on loopback port 9 (discard), which nothing serves on a dev host. It is the default of `realistic_config_document(surreal_url=)`, with a comment saying why and naming 18500 as prod. The tests that need a prod-shaped value already pass it explicitly and are kept: `TestProbeSurreal._RPC_URL`, which stubs `_probe_surreal_health` in every test, and the oracle's `wss://surreal.example:8000/rpc`, whose test stubs the health probe. No remaining reference to the old name (`awk` over the skill's `.py` files: 0).

**Proof instrument (pasted verbatim per brief-base §1; lives at `/var/tmp/claude-1000/t8-guard/`, not committed).**
- A pytest plugin blocks AND records every attempt on port 18500 at four layers: `lore_deploy._probe_surreal_health` (re-wrapped before each test), `urllib.request.urlopen`, `socket.create_connection`, and `socket.socket.connect` / `connect_ex`.
- Recording is the load-bearing half. Production's `_probe_surreal_health` swallows every `OSError`, so a guard that only raised would pass silently.
- One `loaded-<pid>` marker per process proves the guard was live in every xdist worker.

```python
"""pytest plugin (T8 prod-URL proof): BLOCK and RECORD any attempt to reach the prod store.

Loaded with ``-p t8_prod_guard`` (dir on PYTHONPATH). Blocks, before any connect, every
attempt to reach port ``PROD_PORT`` through three layers:
  * ``lore_deploy._probe_surreal_health`` (re-wrapped before every test, so a test's own
    monkeypatch replaces it for that test only and gets restored to the wrapper);
  * ``urllib.request.urlopen`` (the transport ``_probe_surreal_health`` uses);
  * ``socket.create_connection`` and ``socket.socket.connect`` / ``connect_ex`` (any client).
Production's ``_probe_surreal_health`` swallows every ``OSError``, so raising alone could
pass silently. Every blocked attempt is therefore also APPENDED to
``$T8_GUARD_DIR/hits-<pid>.log`` with the running test's node id. The proof is that the
directory holds no hits after the run, and a positive control shows a hit DOES land.
"""

from __future__ import annotations

import os
import socket
import sys
import urllib.request
from pathlib import Path
from typing import Any

PROD_PORT = 18500
# Optional RECORD-ONLY port (never blocked): set T8_GUARD_RECORD_PORT=9 to count attempts on
# the fake's dead default endpoint, i.e. the attempts that reached 18500 before the fix.
RECORD_PORT = int(os.environ.get("T8_GUARD_RECORD_PORT", "0"))
_current_test = "<no test>"
_HITS_DIR = Path(os.environ["T8_GUARD_DIR"])
_HITS_DIR.mkdir(parents=True, exist_ok=True)
# Liveness receipt: one marker per process that loaded the guard (main + every xdist worker).
(_HITS_DIR / f"loaded-{os.getpid()}").write_text(" ".join(sys.argv[:3]), encoding="utf-8")


def _record(layer: str, target: object) -> None:
    with (_HITS_DIR / f"hits-{os.getpid()}.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{_current_test}\t{layer}\t{target!r}\n")


def _url_of(url_or_request: Any) -> str:
    return str(getattr(url_or_request, "full_url", url_or_request))


_real_urlopen = urllib.request.urlopen


def _guarded_urlopen(url: Any, *args: Any, **kwargs: Any) -> Any:
    if f":{PROD_PORT}" in _url_of(url):
        _record("urlopen", _url_of(url))
        raise OSError(f"t8_prod_guard: blocked {_url_of(url)}")
    return _real_urlopen(url, *args, **kwargs)


urllib.request.urlopen = _guarded_urlopen  # type: ignore[assignment]

_real_create_connection = socket.create_connection


def _guarded_create_connection(address: Any, *args: Any, **kwargs: Any) -> Any:
    if isinstance(address, tuple) and len(address) >= 2 and int(address[1]) == PROD_PORT:
        _record("create_connection", address)
        raise OSError(f"t8_prod_guard: blocked {address}")
    return _real_create_connection(address, *args, **kwargs)


socket.create_connection = _guarded_create_connection  # type: ignore[assignment]

_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex


def _is_prod(address: Any) -> bool:
    return isinstance(address, tuple) and len(address) >= 2 and address[1] == PROD_PORT


def _guarded_connect(self: socket.socket, address: Any) -> Any:
    if RECORD_PORT and isinstance(address, tuple) and len(address) >= 2 and address[1] == RECORD_PORT:
        _record("record-only socket.connect", address)
    if _is_prod(address):
        _record("socket.connect", address)
        raise OSError(f"t8_prod_guard: blocked {address}")
    return _real_connect(self, address)


def _guarded_connect_ex(self: socket.socket, address: Any) -> Any:
    if _is_prod(address):
        _record("socket.connect_ex", address)
        return 111  # ECONNREFUSED
    return _real_connect_ex(self, address)


socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
socket.socket.connect_ex = _guarded_connect_ex  # type: ignore[method-assign]


def _wrap_probe_surreal_health() -> None:
    module = sys.modules.get("lore_deploy")
    if module is None:
        return
    current = module._probe_surreal_health
    if getattr(current, "_t8_guard", False):
        return

    def _guarded_probe(health_url: str, *args: Any, **kwargs: Any) -> bool:
        if f":{PROD_PORT}" in health_url:
            _record("_probe_surreal_health", health_url)
            return False
        return bool(current(health_url, *args, **kwargs))

    _guarded_probe._t8_guard = True  # type: ignore[attr-defined]
    module._probe_surreal_health = _guarded_probe


def pytest_runtest_setup(item: Any) -> None:
    global _current_test
    _current_test = item.nodeid
    _wrap_probe_surreal_health()
```
Positive control (`/var/tmp/claude-1000/t8-guard/control/test_t8_guard_control.py`, verbatim):
```python
"""Positive control for t8_prod_guard: every guarded layer RECORDS a prod-port attempt.

Run with the guard loaded and T8_GUARD_DIR pointed at an empty directory; afterwards that
directory must hold a hit for each of the four layers. Nothing here connects: the guard
blocks before any socket is opened.
"""

from __future__ import annotations

import socket
import urllib.request

import lore_deploy
import pytest

PROD_HEALTH = "http://127.0.0.1:18500/health"


def test_probe_layer_is_blocked() -> None:
    assert lore_deploy._probe_surreal_health(PROD_HEALTH) is False


def test_probe_surreal_end_to_end_is_blocked(tmp_path, monkeypatch) -> None:
    from config_reader_fake import ConfigReaderFake

    ConfigReaderFake.install(monkeypatch, tmp_path, surreal_url="ws://127.0.0.1:18500/rpc")
    monkeypatch.setattr(lore_deploy, "_container_state", lambda name: None)
    assert lore_deploy._probe_surreal(tmp_path / "lore.yaml") == lore_deploy._EXIT_ERROR


def test_urlopen_layer_is_blocked() -> None:
    with pytest.raises(OSError, match="t8_prod_guard"):
        urllib.request.urlopen(PROD_HEALTH, timeout=1)


def test_socket_layer_is_blocked() -> None:
    with pytest.raises(OSError, match="t8_prod_guard"):
        socket.create_connection(("127.0.0.1", 18500), timeout=1)
```

**Runs** (each runner's `RAN:` checked; counts and exit codes read from the logs myself):

| run | RAN (abridged; full in the runner reports) | result |
|---|---|---|
| guard CONTROL | `T8_GUARD_DIR=…/hits-control PYTHONPATH=/var/tmp/claude-1000/t8-guard … pytest -q -p t8_prod_guard … /var/tmp/claude-1000/t8-guard/control` → `t8-guard-control.log` | `4 passed`, `EXIT=0`, **`LOADED=1 HITS=4`**: one hit per test, through the layers `_probe_surreal_health` (direct and via `_probe_surreal` end to end), `urlopen`, `create_connection`. Nothing connected (blocked before any socket). |
| guard PROOF (HEAD suite, both trees) | `T8_GUARD_DIR=…/hits-proof … pytest -q . ../tests -p t8_prod_guard --timeout=300 -n 8 -rf` → `t8-guard-proof.log` | **`162 passed`, `EXIT=0`, `LOADED=9 HITS=0`**: the guard was live in the main process + 8 workers, and **no test made any attempt to reach :18500** |
| HEAD suite | `cd skills/lore-deploy/scripts && systemd-run … pytest -q . ../tests --timeout=300 -p no:cacheprovider -n 8 -rf > t8-head4.log; echo EXIT=$?` | **`162 passed`, `EXIT=0`** |
| oracle | `… pytest -q "test_lore_deploy.py::TestConfigReaderFakeOracle" --timeout=300 -rf > t8-oracle.log; echo EXIT=$?` | **`10 passed`, `EXIT=0`** |
| extra: dead-port recording (record-only, `T8_GUARD_RECORD_PORT=9`) | same as PROOF with `hits-port9` → `t8-guard-port9.log` | `162 passed`, `EXIT=0`, `LOADED=9 HITS=0`. ⚠ **UNCONTROLLED.** The positive control for the record-only layer (one `_probe_surreal_health` call at `127.0.0.1:9`) was **denied by the permission layer** because it opens a real loopback connection, and I did not route it through a subagent. So this zero is NOT evidence. It cannot answer whether any test reached 18500 *before* this fix. |

**What is proven:** at the fixed tree, no test in either skill tree attempts :18500 through any of the four layers (proof `HITS=0`, with the control showing the instrument records). **What is not proven:** whether any of my earlier, pre-fix runs (`t8-head*.log`, `t8-reference*.log`) sent a real `GET /health` to production. The only test that would is one that leaves the health probe unstubbed AND uses the fake's default URL. The uncontrolled port-9 run suggests there are none, but it has no control. If you want it settled, the operator can approve the port-9 control call, or the lead can run it.

**Also noticed:** production's own scaffold (`lore_deploy._scaffold_lore_yaml`) writes `url: ws://127.0.0.1:18500/rpc` into every new `lore.yaml`. That is correct for deploys. But `test_read_config_field.py` and `test_scaffold_config.py` build their configs with it. The proof run covered both files (they are in `.`) with 0 hits, so neither probes today. A future test that scaffolds a config and then calls `_probe_surreal` unstubbed would hit production, and nothing structural stops it. Possible closure, the operator's call: run the guard above permanently from a skill `conftest.py`. That is a run-wide recorder, which needs operator approval under the global rules, so I have not added it.

## Fresh-path pins (directive #18006, thread fresh-path-pins, spec `docs/plans/v2/receipts/2026-10-31-165/RULING-fresh-path.md`, started 2026-10-31 ~18:13Z)

### Routing table (written before any read beyond the spec)
| step | tier | who | reason |
|---|---|---|---|
| scratch copy at HEAD for the reference build | 1 | haiku-worker | literal command, parallel with my reads |
| read `verb_start` fresh path + its preconditions | inline (one function body + the recreate path's A1 handling) | me | feeds the pin design directly; one span, read whole |
| enumerate fresh-path preconditions | 3 | me | the ∀ set IS the contract (spec item 1). A sampled draft would miss a precondition reached through a helper (`_gate_snapshot_precondition`). |
| write pins | 3 | me | contract authorship |
| RED at HEAD, GREEN at reference, ruff | 1 | haiku-runner | test runs |
| reference build in scratch | 3 | me | satisfiability instrument (inside role) |

### Where and what
- **File:** `skills/lore-deploy/scripts/test_lore_deploy.py` (my choice). It holds the shared `ConfigReaderFake` helpers (`_install_config_reader`) and the recreate-path pins this rule mirrors (`TestVerbStartRecreateValidatesBeforeTeardown`). `test_launch_snapshot_bind.py` uses the REAL reader, so it would add a subprocess per test for no extra coverage.
- **New symbols (test-local):** `_PODMAN_READ_ONLY_VERBS`, `_podman_verb`, `_FreshPathArrangement`, `TestVerbStartFreshPathParity` (9 tests).
- **Arrangement:** verb_start runs with `_container_state` answering `"exited"` (`None` for item 2) and every precondition passing. The config comes from the shared fake, and the snapshot gate runs FOR REAL over it. One ordered `events` transcript records every podman call, every precondition probe and every launch attempt.
- **Preconditions (the ∀ set):** read off `verb_start`'s fresh path at `1b8887d`, every check between the `state` read and `_launch_container`. There are 6 cells, each failing the way it really fails:
  - `image_missing` (`_image_exists` → False);
  - `env_file_missing` (the file deleted);
  - `snapshot_unmaterialised` (a recorded static tier, `surrealdb-docs`, under an empty `SNAPSHOT_ROOT`; the real `_require_launchable_snapshot` refuses);
  - `config_unreadable` (a schema-invalid document; the real config read raises, R2);
  - `embed_unreachable` (`_probe_embed` → `_EXIT_ERROR`);
  - `store_unreachable` (`_probe_surreal` → `_EXIT_ERROR`).
- **Left out:** the missing-`lore.yaml` check, which returns before `_container_state` is read and so cannot reach the `rm` at any build.
- **What counts as "touching" the container (allowlist the safe):** any podman call that names `lore-<slug>` with a verb outside the read-only set `{inspect, ps, exists, logs, port, top}` (looking through `podman container <verb>`). A new mutating verb therefore cannot slip past.

### Pins
| pin | spec | RED at HEAD `1b8887d` (reason) |
|---|---|---|
| `test_a_refused_fresh_start_leaves_the_exited_container_in_place[×6]` | item 1 ∀: `_EXIT_ERROR`, zero container mutations, no launch | 6/6: `['podman','rm','-f','lore-freshpath']` issued before the refused precondition |
| `test_the_exited_container_is_removed_after_every_precondition_and_before_launch` | item 1 positive control: with all preconditions passing the exited container IS removed (exactly one `rm`), after the last precondition and before the launch. This catches a build that never removes, where `podman run --name` would collide. | RED: `rm` at index 0, before `precondition:image` (`assert 3 < 0`) |
| `test_a_failed_fresh_launch_exits_loudly_with_the_errors_text[runtime_error_refusal, called_process_error_podman_run]` | item 2: `_EXIT_ERROR` + `str(error)` on stderr, never a raw raise | 2/2: the raw `RuntimeError` / `CalledProcessError` propagates (caught by the arrangement as `pytest.fail`) |

### Runs (`RAN:` lines checked; counts and exit codes read from the logs myself)
| run | command (abridged) | result |
|---|---|---|
| RED at HEAD | `cd skills/lore-deploy/scripts && systemd-run … pytest -q "test_lore_deploy.py::TestVerbStartFreshPathParity" --timeout=300 -rf > t8-fresh-red.log; echo EXIT=$?` | **9 failed**, `EXIT=1`, each for the reason in the table |
| GREEN at the reference | scratch `/var/tmp/claude-1000/t8-scratch3` (made by `scripts/scratch_copy.sh` at 1b8887d, EXIT=0), `LORE_PYTHON=/var/tmp/claude-1000/t8-scratch3/.venv/bin/python`, full skill suite `-n 8` → `t8-fresh-green.log` | **171 passed / 0 failed** (162 + 9), `EXIT=0`. `PROVENANCE /var/tmp/claude-1000/t8-scratch3/loremaster/loremaster/__init__.py /var/tmp/claude-1000/t8-scratch3/skills/lore-deploy/scripts/lore_deploy.py /var/tmp/claude-1000/t8-scratch3/skills/lore-deploy/scripts/config_reader_fake.py` |
| currency typecheck,ruff | `pending_contract_gate.py --currency --legs typecheck,ruff` → `t8-currency3.log` | ruff GREEN; typecheck RED_ADJUDICATED, the same 83 owned residuals (packet-58, packet-64b-i), **no new orphan** |

### Reference build (satisfiability only, applied ONLY in scratch, verbatim `/var/tmp/claude-1000/t8-fresh-reference.diff`)
```diff
--- /var/tmp/claude-1000/t8-fresh-lore_deploy.orig.py	2026-10-31 13:49:08.839907716 -0400
+++ /var/tmp/claude-1000/t8-scratch3/skills/lore-deploy/scripts/lore_deploy.py	2026-10-31 14:15:24.171638144 -0400
@@ -1035,9 +1035,6 @@
             print(_MCP_RECONNECT_REMINDER)
             return _EXIT_OK
 
-    if state is not None:  # exists but not running (e.g. exited) — remove the stale one.
-        _run(["podman", "rm", "-f", container_name], check=False)
-
     if not _image_exists(IMAGE):
         print(f"start: image {IMAGE} missing; run `setup` (which builds it).", file=sys.stderr)
         return _EXIT_ERROR
@@ -1055,7 +1052,15 @@
     if (rc := _probe_surreal(config_path)) != _EXIT_OK:
         return rc
 
-    _launch_container(project, config_path, env_file)
+    # REFERENCE (fresh-path parity): every precondition passed — only now remove the
+    # stale exited container, immediately before the launch.
+    if state is not None:
+        _run(["podman", "rm", "-f", container_name], check=False)
+    try:
+        _launch_container(project, config_path, env_file)
+    except (RuntimeError, subprocess.CalledProcessError) as error:
+        print(f"start: launch of {container_name} failed ({error}).", file=sys.stderr)
+        return _EXIT_ERROR
     host, port, mount = _read_server_block(config_path)
     if (rc := _await_bind(
         container_name, host, port, mount,
```

### Flags
1. **The 9 new pins are RED at HEAD by design, and that red is not yet registered.** `scripts/pending_contracts.yaml` is outside my writable set. Until the builder lands this, a bare `--currency` (its pytest leg) would show them as RED_ORPHANED. The lead should register an owner and trigger, or commit them together with the build.
2. Spec gap, noted rather than assumed: the ruling says the refusal must "always exit loudly". My item-1 pins do NOT assert stderr, because two of the six preconditions (embed, store) are stubbed probes that print nothing themselves. A loudness pin over the stubs would be red at every build. If loudness of each refusal should be pinned too, the real probes' stderr is the seam to drive. Your call.
3. Scratch dirs `/var/tmp/claude-1000/t8-scratch` (stale T8 reference) and `/var/tmp/claude-1000/t8-scratch3` (the fresh-path reference) can be deleted. `/var/tmp/claude-1000/t8-scratch2` was never created (its `rm -rf` was denied by the permission layer; I retried as scratch3 without the `rm`).
