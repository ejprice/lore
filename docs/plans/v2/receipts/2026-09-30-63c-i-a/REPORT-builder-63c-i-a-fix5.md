brief-base v18 read · brief project v7 read

# REPORT — builder-63c-i-a-fix5 (packet 63c-i-a, am-37 §12 item 2 PRODUCTION: the four wraps)

## SUMMARY BLOCK
- **State:** done. No STOP fired: §12 STOP 1 (refusal passthrough), STOP 3 (58 scanner / fates) and "unowned red" were each checked (§2, §4).
- **Deviations:** none. `delete` takes reading B (a whole-body wrap from `get_by_email` through the TXN), as the brief ordered.
- **Packages considered:** none. No mechanism was specified; the edits reuse the existing seam `loremaster.store._txn.wrap_store_rejection`.
- **Odoo-20 portability:** n/a. No Odoo seam was touched.
- **Reuse ledger:** none. 0 new production symbols; the four edits route through the one existing seam.
- **Graded:** n/a. This is a build report, not a verdict.
- **Decisions needed:** none.
- **Receipts:**
  - §1: edit → clause → receipt;
  - §2: the delete-refusal passthrough and the §10.1(a) probe, pasted verbatim;
  - §3: the prose sweep;
  - §4: the declared set and transitions (0 GREEN→RED, exactly the 20 declared RED→GREEN, 36 owned reds);
  - §5: currency, verbatim;
  - §6: DUAL;
  - §7: backups and md5s.

All measurements were taken 2026-09-30 between 02:40 and 02:50Z. They ran in scratch `fix5` = main HEAD `4e2c60c` + A (`299467ba…`) + B (`fd70c6e9…`).
- `4e2c60c` is `def8d51` plus one lead-report-only commit, so nothing under `loremaster/` or `scripts/` moved.
- Provenance: `loremaster.__file__` = `…/scratchpad/fix5/loremaster/loremaster/__init__.py`, printed at setup and again by the probe.
- The base `principals.py` md5 `b9aca87b…` equals fix4's reported final md5. This independently confirms that B landed as fix4 built it.

## 1. Edits → §12 clause → receipt (`loremaster/loremaster/principals.py`, `principal_keys.py` ONLY)
| # | method (symbol) | edit | §12 clause | receipt (node ids, §4) |
|---|---|---|---|---|
| 1 | `PrincipalStore.set_status` | UPDATE inside `wrap_store_rejection(PrincipalStoreError, f"could not set status of principal {email!r} to {status!r}")` | item 2, "wrap `set_status`" | `…boundary_sits_inside_its_stores_wrap[principal::set_status]`, `raw_store_error…[principal-set_status]`, LAYER1/LAYER2 `[principal-set_status]` all went RED→GREEN |
| 2 | `PrincipalStore.set_expires` | ONE wrap enclosing BOTH branches' UPDATEs, `"could not set expiry of principal {email!r}"` | item 2, "`set_expires` (2× UPDATE)" | `[principal::set_expires]` plus its 3 ∀ siblings went RED→GREEN |
| 3 | `PrincipalStore.delete` | ONE wrap from the opening `get_by_email` THROUGH `execute_transaction`, `"could not delete principal {email!r}"`. The body was re-indented by `scratchpad/fix5_wrap_delete.py`: 83 body lines, and `return cascaded` stays outside. | item 2 plus the brief's reading B (fixup R3 two-reading trigger) | `[principal::delete]` plus its 3 ∀ siblings went RED→GREEN. The refusal passthrough is §2. |
| 4 | `PrincipalKeyStore.revoke` | UPDATE inside `wrap_store_rejection(PrincipalKeyStoreError, f"could not revoke key {name!r} for principal {email!r}")`. This matches `mint`'s "…key {name!r} for principal {email!r}" shape. | item 2, "wrap `revoke`" | `[principal_key::revoke]` plus its 3 ∀ siblings went RED→GREEN |
- Each wrap carries a two-line comment in the house form of the existing wraps: "store rejection wraps LOUD; transport / exhausted contention passes through".
- The routed-set pins `…routed_set_equals_the_{invocation_map,known_wrapping_verbs}[principal|principal_key]` (4 nodes) went RED→GREEN on the same build.
- Delta: `principal_keys.py` +12/−6, `principals.py` +121/−98. Most of the second is the `delete` re-indent.

## 2. STOP 1: delete refusals propagate BY CLASS, and the §10.1(a) fate
- **Refusal passthrough.** `wrap_store_rejection` → `reclassify(passthrough=(SurrealConnectionError, TxnContentionExhaustedError), catch=(SurrealStoreError,), …)`, as cited verbatim in fixup R3-1.
  - `PrincipalNotFoundError`, `PrincipalHasKeepsError` and `PrincipalOwnsGovernedRowsError` are `PrincipalStoreError → RuntimeError`, not `SurrealStoreError` (`principals.py` class defs). They are re-raised untouched.
  - Empirical check on the build: `test_fixwave_a19b_63c_i_a.py`, `test_principal_delete_governed_63a.py`, `test_principal_delete_cascade_61.py` and `test_principals_store.py` have **0 failures** (none appears in the §4 remaining-red list). That includes `pytest.raises(owns_governed_error)` and the `_ProbeFault` fail-closed pin (`test_principal_delete_governed_63a.py`). That pin's non-`SurrealStoreError` fault at `INFO FOR DB` still propagates untouched with the wrap now around `_table_exists`.
- **§10.1(a): the malformed owned-row count.** No existing test drives this path: bare awk for `group_all_count` over `loremaster/tests/*.py` found 0 hits. So I wrote a probe (pasted verbatim below; md5 `39a5f76e…`). It is offline and scripts the store; "refused" means "the cascade TXN was never executed".

  | leg | build (`ac7ffd09…`) | base (`b9aca87b…`) |
  |---|---|---|
  | 1: store-level, count answer `{"count": "not-an-int"}` | `PrincipalStoreError: could not delete principal 'owner@example.test'`, `__cause__=SurrealStoreError`, **TXN executed 0 times** | raw `loremaster.store._txn.SurrealStoreError: the governed owned-row count read answered a dict without an integer `count` — nothing was decided from it` escapes (traceback; probe exit 1) |
  | 2: POSITIVE CONTROL, count `[{"count": 0}]` | delete proceeds, returns 0, **TXN executed 1 time** | (not reached) |
  | 3: CLI `lore-adm delete`, malformed count | **rc=1**, stderr `"lore-adm: could not delete principal 'owner@example.test'\n"`, no traceback, TXN 0 | (not reached) |

  **Result: PROBE HELD, exit 0 on the build.** The malformed count is still refused, still exits 1, and now carries the domain teaching.

```python
"""Probe: am-37 §10.1(a) + §12 — PrincipalStore.delete on a MALFORMED owned-row count.

Offline (no store is contacted): a PrincipalStore subclass scripts get_by_email / _table_exists /
_query, and ``principals.execute_transaction`` is replaced by a recorder, so "refused" is measured
as "the cascade TXN was never executed". Legs:
  1. store level, malformed count  -> PrincipalStoreError("could not delete …"), __cause__ is
     SurrealStoreError, TXN NOT executed.
  2. POSITIVE CONTROL, count == 0   -> delete PROCEEDS (TXN executed), so leg 1's refusal is the
     malformed count doing the work, not the harness always refusing.
  3. CLI level, malformed count    -> ``lore-adm delete`` returns exit 1, one ``lore-adm:`` stderr
     line naming "could not delete", no traceback, TXN NOT executed.
Prints loremaster.__file__ first (provenance). Exit 0 iff every leg holds.
"""
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

import loremaster
import loremaster.principal_keys as pk_module
import loremaster.principals as p_module
from loremaster.principals import Principal, PrincipalStore, PrincipalStoreError

print(f"loremaster.__file__ = {loremaster.__file__}")
EMAIL = "owner@example.test"
TXN_CALLS: list[str] = []


async def _recording_txn(statement: str, *_args: Any, **_kwargs: Any) -> None:
    TXN_CALLS.append(statement)


p_module.execute_transaction = _recording_txn  # type: ignore[assignment]


class _ScriptedPrincipalStore(PrincipalStore):
    def __init__(self, count_answer: Any) -> None:
        super().__init__(url="ws://127.0.0.1:1", namespace="n", database="d", user="u", password="p")
        self._count_answer = count_answer

    async def ensure_ready(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def get_by_email(self, email: str) -> Principal | None:
        return Principal(
            id="principal:abc", email=email, subject=None, display_name=None, status="active",
            role="member", expires_at=None, created_at=datetime.now(UTC),
        )

    async def _table_exists(self, table: str) -> bool:
        return True

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        if "FROM keep" in statement:
            return []
        if "FROM memory" in statement:
            return self._count_answer
        if "FROM principal_key" in statement:
            return [{"count": 0}]
        raise AssertionError(f"unscripted statement: {statement}")


class _NullStore:
    def __getattr__(self, name: str) -> Any:
        async def _noop(*_a: Any, **_k: Any) -> None:
            return None
        return _noop


failures: list[str] = []
MALFORMED = {"count": "not-an-int"}  # a dict, not a list of rows

# Leg 1
TXN_CALLS.clear()
try:
    asyncio.run(_ScriptedPrincipalStore(MALFORMED).delete(email=EMAIL))
    failures.append("leg1: delete did not raise on a malformed count")
except PrincipalStoreError as error:
    cause = error.__cause__
    print(f"leg1: raised {type(error).__name__}: {error} | __cause__={type(cause).__name__}")
    if type(error) is not PrincipalStoreError or "could not delete" not in str(error):
        failures.append(f"leg1: wrong class/message {type(error).__name__}: {error}")
    if type(cause).__name__ != "SurrealStoreError":
        failures.append(f"leg1: cause is {type(cause).__name__}, not SurrealStoreError")
print(f"leg1: TXN executed {len(TXN_CALLS)} time(s)")
if TXN_CALLS:
    failures.append("leg1: the cascade TXN executed despite the malformed count")

# Leg 2 (positive control)
TXN_CALLS.clear()
cascaded = asyncio.run(_ScriptedPrincipalStore([{"count": 0}]).delete(email=EMAIL))
print(f"leg2 CONTROL: delete returned {cascaded}, TXN executed {len(TXN_CALLS)} time(s)")
if len(TXN_CALLS) != 1:
    failures.append("leg2: a well-formed zero count did NOT let the delete proceed")

# Leg 3 (CLI)
TXN_CALLS.clear()
p_module.build_principal_store = lambda _c: _ScriptedPrincipalStore(MALFORMED)  # type: ignore[assignment]
p_module.build_keep_store = lambda _c: _NullStore()  # type: ignore[assignment]
pk_module.build_principal_key_store = lambda _c: _NullStore()  # type: ignore[assignment]
config_path = Path(sys.argv[1]) / "lore.yaml"
config_path.parent.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, sys.argv[2])  # the tests dir: reuse the CLI pin's own valid config payload
from test_principals_cli import _config_payload  # noqa: E402
config_path.write_text(yaml.safe_dump(_config_payload(database="probe_fix5")), encoding="utf-8")
import contextlib
import io

stderr = io.StringIO()
with contextlib.redirect_stderr(stderr):
    try:
        rc: Any = p_module.main(["--config", str(config_path), "delete", "--email", EMAIL])
    except SystemExit as error:
        rc = f"SystemExit {error.code}"
    except Exception as error:  # noqa: BLE001
        rc = f"ESCAPED {type(error).__name__}: {error}"
err = stderr.getvalue()
print(f"leg3 CLI: rc={rc!r} stderr={err!r} TXN executed {len(TXN_CALLS)} time(s)")
if rc != 1 or "could not delete" not in err or "Traceback" in err or TXN_CALLS:
    failures.append(f"leg3: CLI fate wrong rc={rc!r} err={err!r} txn={len(TXN_CALLS)}")

print("PROBE HELD" if not failures else "PROBE FAILED:\n  " + "\n  ".join(failures))
sys.exit(1 if failures else 0)
```
Run: `cd <tree> && uv run python fix5_probe_delete_malformed.py <tmpdir> loremaster/tests`.

## 3. Prose sweep (bare awk, both files)
Grep/rg are hook-blocked (#473), so I used awk. Pattern, case-insensitive: `surrealstoreerror|raw store|raw driver|store rejection|unwrapped|propagat|set_status|set_expires|revoke|\.delete|delete\(|wrap_store_rejection`. Every hit was judged against the four methods' new fault fate. Symbols are cited, and line numbers are those of the build (`ac7ffd09…` / `86ef634e…`).

| file:line (build) | hit | verdict |
|---|---|---|
| principals.py:72 | module docstring `async set_status(*, email, status) -> Principal` | signature only, TRUE |
| principals.py:109, :116 | imports `SurrealStoreError`, `wrap_store_rejection` | code, n/a |
| principals.py:390 | `ensure_ready`-TXN docstring `SurrealStoreError: A DDL statement was rejected` | TRUE (DDL is exempt from §12 by rule) |
| principals.py:454 | `_table_exists` "a store / connection error during the probe PROPAGATES" | TRUE of `_table_exists` itself. In `delete` a store error now surfaces as `PrincipalStoreError` and a connection fault untouched: it still propagates, never "absent". |
| principals.py:515 / :644 | existing `create` / `set_subject` wraps | n/a |
| principals.py:576 | `def set_status` | n/a. Docstring `Raises:` lists ValueError and PrincipalNotFoundError. It never named a store-fault class, before or after, so it is NOT false. Left alone, because the brief says to fix only false prose. |
| principals.py:601–603 | my new comment and wrap | TRUE |
| principals.py:659 / :663 | `def set_expires`, "Clones :meth:`set_status`'s shape" | TRUE (both now wrapped). `Raises:` is not false, same as set_status. |
| principals.py:680–682 | my new comment and wrap | TRUE |
| principals.py:707 | `def delete` | `Raises:` lists the 3 typed refusals, still exactly true: they pass untouched. Not false. |
| principals.py:770–772 | my new comment and wrap | TRUE |
| principals.py:810 | "a connection fault during the existence probe PROPAGATES (fail-CLOSED)" | TRUE (`SurrealConnectionError` is in the passthrough) |
| principals.py:815 (pre-fix text) | "A malformed answer raises ``SurrealStoreError`` (the class a REJECTED count read already raises here)" | **FALSE after the wrap**: the method now surfaces it as `PrincipalStoreError`. **FIXED.** The comment now says the answer raises `SurrealStoreError`, "which this method's wrap (am-37 §12) surfaces as `PrincipalStoreError("could not delete …")`; either way the delete does NOT proceed". |
| principals.py:904, :908 | `_require_aware_utc` raises `SurrealStoreError` | unrelated to the four methods, TRUE |
| principals.py:951 | CLI comment listing `revoke-key` | TRUE |
| principals.py:1035 | `state = "revoked"` | code, n/a |
| principals.py:1535, :1549, :1569, :1596 | `_governed_select` / `_agent_migration_preconditions` | governed migration, exempt from §12 by rule, TRUE |
| principals.py:2079–2080 | argparse `revoke-key` help | TRUE |
| principals.py:2194–2245 | `_cmd_delete` / `_cmd_suspend` / `_cmd_unsuspend` / `_cmd_set_expiry` / `_cmd_revoke_key` call sites | code; no catch here (fix4 §11 handler at `_dispatch`), TRUE |
| principals.py:2325, :2330 | `delete-keep` → `KeepStore.delete_keep` | KeepStore, unaffected, TRUE |
| principals.py:2342 | `"revoke-key": _cmd_revoke_key` | code, n/a |
| principals.py:2413, :2426, :2487 | `_dispatch` tuple; `_dispatch_migrate_governed` / `_dispatch_report_unmigrated` "fault propagates to `_dispatch`'s ONE handler" | TRUE |
| principals.py:2518–2530 | `_dispatch_keep` D1 docstring ("an un-wrapped `SurrealStoreError` prints its driver label") | about KeepStore reads; TRUE, unaffected |
| principal_keys.py:39, :55, :65 | module docstring (`revoke` listed, `revoked_at` field, signature) | TRUE |
| principal_keys.py:112 | import `wrap_store_rejection` | n/a |
| principal_keys.py:133, :153, :163 | `_COL_REVOKED_AT`, field docs | TRUE |
| principal_keys.py:303 | `ensure_ready` `SurrealStoreError: A DDL statement was rejected` | TRUE (DDL exempt) |
| principal_keys.py:369 | section banner `mint / list / revoke` | n/a |
| principal_keys.py:423 | `mint` wrap | n/a |
| principal_keys.py:437–454 | `list_for` docstring and SELECT (`revoked keys INCLUDED`) | TRUE |
| principal_keys.py:462–478 | `revoke` docstring. `Raises:` lists PrincipalNotFoundError and PrincipalKeyNotFoundError; "A second revoke … does NOT raise" | TRUE (the wrap does not change the re-revoke path) and not false |
| principal_keys.py:485–492 | my new comment, wrap and UPDATE | TRUE |
| principal_keys.py:514, :549, :560–562, :611, :628 | `verify` / `_row_to_key` revoked_at logic | TRUE, unrelated |

Result: **1 false hit, fixed. 0 others false.** The `Raises:` sections of all four methods are incomplete: none ever named a store-fault class, and `set_subject`'s does. Incomplete is not false, and the brief says to fix only false prose, so they are unchanged. Flagged for the lead as optional polish. They are not a defect under the brief's rule.

## 4. Declared set + transitions
**Declared BEFORE any run** in `scratchpad/fix5-declared-files.txt` (md5 `a3762004…`): 21 files, collected 1039 nodes.
- **Round-3 eight:** `test_engine_rejection_seam.py test_exhaustion_fates.py test_principals_cli.py test_fixwave_a19b_63c_i_a.py test_principal_delete_governed_63a.py test_principal_delete_cascade_61.py test_principal_keys_store.py test_principal_keys_schema.py`.
- **fix4's ten (fix4 report §4):** adds `test_keeps_cli.py test_keep_remediation_cli_61.py test_reanchor_58_r4_lease_fates.py test_reanchor_58_r3_cas_seam.py test_fixwave_a28c_63c_i_a.py test_agent_governance_63c_i_a.py`.
- **AST-scan covering tests:** `lore_impact` caps covering tests at 15 (#518), so I used an AST scan instead (pasted below). It found calls to `.set_status(` / `.set_expires(` / `.revoke(` on any receiver, plus `.delete(` carrying `email=` or a `principal`-named receiver. It adds `test_agent_capability.py test_agent_owns_principal_schema.py test_audit_store.py test_findings_classes_64b.py test_keep_remediation_store_61.py test_principals_store.py test_token_verifier.py`.
  - The scan over-includes on purpose. For example, `test_audit_store.py` / `test_findings_classes_64b.py` hits may be other stores' `delete` / `set_status`. Allowlisting the safe is cheaper than missing a caller.

**Runs.** Both runs used ONE tree with `cmp`-verified swaps of the two production files and principal* `__pycache__` cleared before each run.
- Admission wait-loop: MemAvailable ≥ 20 GiB (20.5 / 21.1 GiB at start).
- Command: `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider -rA <21 files>`. No cap kill occurred.

| run | files | result |
|---|---|---|
| base (A+B) | `b9aca87b…` / `0dec148c…` | **56 failed, 983 passed** (1039) |
| build | `ac7ffd09…` / `86ef634e…` | **36 failed, 1003 passed** (1039) |

- The 7 `ERROR <logger>:_txn.py:…` rows in `-rA` are captured LOG lines, identical on both sides. They are not test outcomes: 36 + 1003 = 1039 collected.
- Transitions (joined by node id, 1039 nodes on both sides):
  - **GREEN→RED: 0.**
  - **RED→GREEN: 20.** This is exactly the declared round-3 set, with nothing missing and nothing extra:
    - `TestEveryDerivedWriteBoundaryIsWrapped::test_the_write_boundary_sits_inside_its_stores_wrap[principal::delete | principal::set_expires | principal::set_status | principal_key::revoke]`
    - `TestTheRoutedSetIsDerivedAndComplete::test_the_routed_set_equals_the_invocation_map[principal | principal_key]`
    - `TestTheRoutedSetIsDerivedAndComplete::test_the_routed_set_equals_the_known_wrapping_verbs[principal | principal_key]`
    - `TestEngineRejectionWrappingBehaviourIsPreserved::test_a_raw_store_error_surfaces_as_the_domain_error[principal-delete | principal-set_expires | principal-set_status | principal_key-revoke]`
    - `TestSharingProvenByMutation::test_dropping_LAYER1_reclassify_moves_every_routed_path[same 4]`
    - `TestSharingProvenByMutation::test_dropping_LAYER2_wrap_store_rejection_moves_every_routed_path[same 4]`
    - (all in `loremaster/tests/test_engine_rejection_seam.py`)
- **Remaining 36 RED, unchanged base→build, all owned** (`scripts/pending_contracts.yaml` in the A+B tree):
  - 9 are `packet-58-contract` (paths `test_exhaustion_fates.py`, `test_reanchor_58_r3_cas_seam.py`, `test_reanchor_58_r4_lease_fates.py`). This is the same 9-id set as fix4 §4:
    - `test_exhaustion_fates.py::…test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS`;
    - r3 CAS `[tasks.py::_reanchor_stragglers]` and the `…static_CAS_member…` legs `[findings.py::_run_guarded | tasks.py::claim_task | tasks.py::_reanchor_stragglers]`;
    - r4 lease `[create | get | release_if_held | update]`.
  - 27 are `test_findings_classes_64b.py::*`, owned by `packet-64b-i-contract` (its registered path `loremaster/tests/test_findings_classes_64b.py`). fix4 did not run this file; the AST scan added it. All 27 are red on base too.
- STOP 3 (58 catch-site scanner / fates): the fates pins are `test_exhaustion_fates.py`. The only red there is the lease-row pin owned by 58, unchanged from base. The both-ways registry pin is GREEN on the build. No row or site is keyed to `set_status` / `set_expires` / `delete` / `revoke`. A `with` adds no `except`. **Not fired.**

AST covering-test scan (instrument, pasted verbatim; md5 `36454be1…`):
```python
"""AST scan of loremaster/tests for calls to the four wrapped methods.

Covers: .set_status(...), .set_expires(...), .revoke(...) on any receiver, and .delete(...)
whose call carries an ``email=`` keyword (PrincipalStore.delete's keyword-only signature) or
whose receiver name mentions 'principal'. Prints one file per line (sorted, unique).
"""
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
hits: dict[str, set[str]] = {}
for path in sorted(root.glob("test_*.py")):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        attr = node.func.attr
        if attr in {"set_status", "set_expires", "revoke"}:
            hits.setdefault(path.name, set()).add(attr)
        elif attr == "delete":
            receiver = ast.unparse(node.func.value).lower()
            if any(k.arg == "email" for k in node.keywords) or "principal" in receiver:
                hits.setdefault(path.name, set()).add("delete")
for name in sorted(hits):
    print(name, ",".join(sorted(hits[name])))
```
- Known bound of this scan: it reaches only direct `.method(` calls in `test_*.py`. It misses a call through a helper module or a `getattr` string. `test_engine_rejection_seam.py`'s invocation map is one such case, and it was in the declared set anyway.
- It reaches no module outside `loremaster/tests` (e.g. `scripts/`, #507). No script calls these four store methods directly: they are reached via `lore-adm`, whose CLI pins are in the set.

## 5. Gates (build tree)
- `uv run ruff check .` → `All checks passed!`
- `uv run ruff format --check` on the two files reports "would reformat". It reports the same on the BASE copies, so this is pre-existing. `ruff format` is not a manifested gate (`scripts/gates.yaml`), and I did not reformat, to keep the delta minimal.
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` gave exit 1, only because of the by-design `pytest NOT_RUN` line. This agrees with the fixup R3-5 reading. The output follows verbatim, with the typecheck owner prose elided mid-line where marked `[…]`; the full log is `scratchpad/fix5-currency.log`:
```
========================================================================
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (owner: packet 58 […]) · packet-64b-i-contract (owner: packet 64b-i […]))
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it would pass.
CURRENCY   : FAIL — claimed but never run: pytest
  (this is NOT the deploy receipt: it answers 'is every gate owned', never 'may this ship')
```
- **RED_ORPHANED legs: 0.** typecheck is RED_ADJUDICATED at 83, the same count fixup R3-5 measured before my edits, so it adds no new mypy residual. ruff is GREEN. pytest was not run, by the brief's rule.

## 6. DUAL: what escaped before, what escapes now
| method | before (A+B) | now |
|---|---|---|
| `set_status` | An engine rejection on the UPDATE (a `SurrealStoreError`, e.g. the status ASSERT backstop or a domain rejection) escaped RAW. At the CLI, fix4's §11 handler laundered it to `lore-adm: <driver label>` exit 1, with no domain teaching. | It escapes as `PrincipalStoreError("could not set status of principal …")` from `SurrealStoreError`. The CLI gives the same exit 1, now naming the operation. Unchanged: `ValueError` (the client-side domain check runs before the wrap), `PrincipalNotFoundError` (raised after the wrap), and transport faults / exhausted contention (untouched). |
| `set_expires` | A raw `SurrealStoreError` from either UPDATE branch. | `PrincipalStoreError("could not set expiry of principal …")`, for both branches. `PrincipalNotFoundError` and transport faults are unchanged. |
| `delete` | A raw `SurrealStoreError` from any of the 6 store calls (`get_by_email` read, keep read, `INFO FOR DB`, owned-count read, key-count read, the cascade TXN), and §10.1(a)'s malformed count as a raw `SurrealStoreError` (probe leg 1 base column). | Every `SurrealStoreError` in that span becomes `PrincipalStoreError("could not delete principal …")`. Still unchanged: the three typed refusals (by class, §2), transport faults and exhausted contention, and non-store exceptions (e.g. `_ProbeFault`, `ValueError` from `int(...)`). The malformed count is still refused: TXN 0, exit 1. |
| `revoke` | A raw `SurrealStoreError` from the UPDATE. | `PrincipalKeyStoreError("could not revoke key … for principal …")`. Unchanged: the preceding `_require_principal_id` read (NOT wrapped — the §12 domain is write boundaries, and it is a read), `PrincipalKeyNotFoundError`, and transport faults. |

Removed behaviour: none. No branch, guard or side effect was deleted. The only behavioural change is the exception CLASS and message for `SurrealStoreError` inside the wrapped spans. The chained `__cause__` preserves the driver error for logs.

## 7. Backups (I committed NO production code; the lead commits after the re-check GO)
| artifact | path | md5 |
|---|---|---|
| **FINAL full 63c-i-a patch** (HEAD → everything; 18 files) | `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/e1f81771-6cf2-4679-b6f7-c87b1afe1196/scratchpad/builder-63c-i-a-fix5.full.patch` | `5f2d7c4366d469e5c2a34d53aa235d6e` |
| production-only delta over A+B (touches ONLY `principals.py`, `principal_keys.py`) | `…/scratchpad/builder-63c-i-a-fix5.delta.patch` | `4e3024e7582a2459b70e349e14fa2f55` |
| build `principals.py` / `principal_keys.py` (`cp -a`) | `…/scratchpad/fix5-build/` | `ac7ffd09bbc7925238db6beb78e8613a` / `86ef634eb304fa216026ae25742fdb2e` |
| base (A+B) copies | `…/scratchpad/fix5-backup-base/` | `b9aca87bba271174053d931ecad9ae82` / `0dec148cbf41fb3b2e024c8fd957f8cd` |
| probe / scan / re-indent script / declared list | `…/scratchpad/fix5_probe_delete_malformed.py`, `fix5_cover_scan.py`, `fix5_wrap_delete.py`, `fix5-declared-files.txt` | `39a5f76e…` / `36454be1…` / `72c5ba66…` / `a3762004…` |
| run logs | `…/scratchpad/fix5-run-{base,build}.log`, `fix5-outcomes-{base,build}.txt`, `fix5-transitions.txt`, `fix5-currency.log` | — |

- HEAD at build: `4e2c60c5f33b12732a421daa4c71d573df4808ac` (main and scratch).
- `git apply --check --cached builder-63c-i-a-fix5.full.patch` at main HEAD: **OK**.
- Composition was proven on throwaway `GIT_INDEX_FILE`s; neither the main index nor the working tree was touched:
  - `read-tree HEAD` + A + B + delta → tree `55a848228b156012e0b06e8d68b4938b065eb1d0`;
  - `read-tree HEAD` + full → the **same tree** `55a84822…`.
