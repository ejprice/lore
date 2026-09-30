brief-base v18 read · brief project v7 read

# REPORT — builder-63c-i-a-fix4 (production side of 63c am-37 §11, R2-1)

## SUMMARY BLOCK
- **State:** done. Measured 2026-09-30 ~02:25–02:32Z. Scratch base: HEAD `9055d61` + `fixup-tests-63c-i-a-2.full.patch` (md5 `85a4d2e1…`). Nothing was committed from scratch; the lead commits after the re-check GO.
- **Deviations:** (D-1) I repointed five keep-verb docstrings and one parser comment that named `_dispatch_keep` as the launderer, which has been false since §11. They are prose only, in `principals.py`, and came up in the brief's sweep (§3). (D-2) I rewrote two further docstring sentences, in `_dispatch_migrate_governed` and `_dispatch_report_unmigrated`, to say where a fault now lands. (D-3) I split the handler tuple across lines for ruff E501 (113 > 110). The order is exact and `ast.unparse` is identical (§2).
- **Packages considered:** none. No mechanism was specified. The edit restructures an existing stdlib `try/except`.
- **Odoo-20 portability:** n/a. No Odoo seam was touched.
- **Reuse ledger:** none. No new production symbols; the edit removes three copies of one policy (4 → 1).
- **Graded:** n/a (builder). Built on `9055d61` + `85a4d2e1`. HEAD-at-report is `e35f8ed`, which is DIFFERENT, 2 commits ahead. Both commits are docs only (`b2affe3` and `e35f8ed` touch `REPORT-fixup-tests-63c-i-a-2.md` and `REPORT-lead-63c.md`). No symbol this build rests on moved. My delta `git apply --check`s over HEAD+`85a4d2e1` AND over HEAD+full2 `e915b90f` (§7).
- **Decisions needed:** none. For the lead's information: §5 R-1 (close-before-print ordering) and R-2 (factory faults are now laundered), both direct consequences of the §11 structure. R2-F1 / am-37 §12 is the lead's, and this build does not touch it.
- **Receipt pointers:** edit table §2 · prose sweep §3 · transitions §4 · DUAL §5 · currency §6 · backups §7 · instruments §8.

## 0. Capability check
- Every demanded capability was present. `lore_comms` registered (`builder-63c-i-a-fix4`, session `63c-20260924`).
- grep/rg are hook-blocked (#473), so every text sweep here used `awk`.
- Covering tests came from an **AST scan** (§8a), not `lore_impact`, per the brief (#518's cap). `lore_impact(loremaster.principals._dispatch)` was run as corroboration. It returned **0 test references / "tests: none detected"** because it does not trace indirect coverage through `main`. The AST scan found 4 files, so lore's view here is a strict under-count. It is the known shape (#518 family), so I filed nothing new.
- Provenance: `loremaster.__file__` = `…/5533465e…/scratchpad/fix4/loremaster/loremaster/__init__.py`. That is inside the scratch copy, and `scratch_copy.sh` asserted all four members.

## 1. Setup receipts
- `scratch_copy.sh` → `git reset --hard HEAD && git clean -fd && git status --short` printed nothing.
- The patch md5 `85a4d2e175a974633d60a81e8020d060` matched, and `git apply` succeeded.
- Base `principals.py` was backed up by `cp -a` (md5 `938f7a24…`). Each swap was `cmp`-verified (SWAPPED / SWAPPED-FINAL lines in the session log).

## 2. Edit → §11 clause → receipt (`loremaster/loremaster/principals.py` ONLY)
| edit | §11 clause | receipt |
|---|---|---|
| `_dispatch`: lazy imports (`KeepStoreError`; `PrincipalKeyStoreError, build_principal_key_store`) moved to the top. Then `_require_config` → `load_surreal_only_config`, OUTSIDE the try. Then `try:` wraps the two named branches, the keep branch, and the principal/key branch with its own nested `try/finally` closes. Then `except (PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError, ValueError) as error:` → `print(f"{_CLI_PROG}: {error}", file=sys.stderr); return 1` | item 3, item 4 (i) | AST (§8b): `_dispatch` catches `['(PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError, ValueError)']` and its handler returns `['1']`. The fates `…matched_to_ITS_site_by_the_caught_expression` pin is GREEN, as is the both-ways pin (§4). |
| `except` blocks deleted from `_dispatch_keep`, `_dispatch_migrate_governed`, `_dispatch_report_unmigrated`. Their `try/finally` closes stay. The now-unused lazy `KeepStoreError` imports in `_dispatch_keep` / `_dispatch_migrate_governed` are dropped (ruff F401 otherwise). | item 4 (ii) | AST: all three have `catches: NONE`. Base had 3 tuples (§5). |
| `_dispatch_keep` docstring: the FR-2 D1 paragraph is rewritten to the §11 item-1 re-ruling. "This frame catches NOTHING"; D1's premise is false for reads; the missed-wrap property lives in the FR-2 wrap pins; D1's intent survives in the stderr line. | item 4 (iii) | §3 sweep |
| (D-1) "laundered by `_dispatch_keep`" → "`_dispatch`" in `_cmd_create_keep`, `_cmd_remove_household`, `_cmd_set_rank`, `_cmd_set_keeper` and `_cmd_delete_keep`. The parser comment above `set_keeper` now names `_dispatch`'s one handler. | P8d class (brief step 3) | §3 |
| (D-2) The failure sentences in the `_dispatch_migrate_governed` / `_dispatch_report_unmigrated` docstrings now say the fault propagates to `_dispatch`'s handler. `_dispatch`'s docstring gained a paragraph naming it the ONE lore-adm handler, stating that its only return is 1, and that out-of-tuple faults traceback (§11 item 3). | P8d class | §3 |

- `ruff check` on the file passes.
- `ruff format --check` reports "would reformat", but that is **pre-existing**: the base file (`938f7a24`) fails the same way, and the drift is in hunks I did not touch (lines ~147, 514, 523, …). `ruff format` is not a manifested gate (`scripts/gates.yaml`). This is surfaced here, not fixed.

## 3. Prose sweep (bare awk, `principals.py` final, md5 `b9aca87b…`)
**Pattern 1:** `D1|does not catch|does NOT catch|SurrealStoreError|traceback|Traceback`

| line | text (abridged) | verdict |
|---|---|---|
| 109 | `SurrealStoreError,` (import) | code — n/a |
| 390 | `SurrealStoreError: A DDL statement was rejected` (ensure_ready Raises) | TRUE |
| 794 | `am-37 §10.1(a)` fail-closed count read raises `SurrealStoreError` | TRUE (and it now lands at `_dispatch` → exit 1, which is R2-1's fix) |
| 883 / 887 | datetime read Raises / raise | TRUE / code |
| 1514 / 1528 / 1575 | `group_all_count` fail-closed policy / raises | TRUE / code |
| 2293 | `§FR-4/D1: UPDATE the keep's keeper` | TRUE. It refers to a DIFFERENT D1 (FR-4's decision), not FR-2 D1. |
| 2346 | `_dispatch`: out-of-tuple fault "is left to traceback" | TRUE (new) |
| 2391 | `SurrealStoreError,` (handler tuple) | code |
| 2466 | report-unmigrated: "stderr + exit 1, never a traceback" | TRUE (new) |
| 2496 / 2501–2508 | `_dispatch_keep` re-ruled D1 paragraph | TRUE (new, §11 item 1) |

No hit for "does not catch" / "does NOT catch" remains.

**Pattern 2:** `[Ll]aunder|is caught|caught (here|by)|catches|mirroring :func`, plus every `_dispatch_keep|_dispatch_migrate_governed|_dispatch_report_unmigrated|except [A-Z(]|catch` mention.

| line | text (abridged) | verdict |
|---|---|---|
| 154 | `_KeepVerbHandler` "dict-dispatched by `_dispatch_keep`" | TRUE (routing, not catching) |
| 252–253 / 270–271 | `PrincipalHasKeepsError` / `PrincipalOwnsGovernedRowsError`: "the CLI's existing `except PrincipalStoreError` (`_dispatch`) launders it … NO new catch clause" | TRUE. `_dispatch`'s tuple still names `PrincipalStoreError`. |
| 355, 910 | `except TxnContentionExhaustedError` / `except ValueError` | code, unrelated |
| 925 | "`SurrealConnectionError`-laundering" (config-section comment) | TRUE. `SurrealConnectionError` ⊂ `SurrealStoreError` (MRO, §5). |
| 2107–2108 | parser comment → "a KeepStoreError is laundered by `_dispatch`'s ONE lore-adm handler" | TRUE (edited, D-1) |
| 2237 | "`_KEEP_VERB_HANDLERS` through `_dispatch_keep`" | TRUE (routing) |
| 2249 / 2278 / 2286 / 2296 / 2307 | keep-verb docstrings "laundered by `_dispatch`" | TRUE (edited, D-1). All were FALSE before the edit. |
| 2337 | `_dispatch`: "Keep verbs route to `_dispatch_keep`" | TRUE |
| 2345 | "none of them catches" | TRUE |
| 2361/2363/2365, 2399/2460/2486 | calls / defs | code |
| 2463 | "the `_dispatch_migrate_governed` idiom" (StoreHandle build) | TRUE |
| 2495 / 2503 | "This frame catches NOTHING" / "OUT of this frame's catch" (history) | TRUE |

The test-file docstrings (F-1..F-3 in the fixup report) are NOT mine. They landed in the test side's docstrings delta `afa519cf`, and they compose with this build (§7).

## 4. Declared set + transitions
**Declared BEFORE any run** (`scratchpad/declared_files.txt`), 10 files:
- the brief's six: `test_principals_cli.py`, `test_exhaustion_fates.py`, `test_keeps_cli.py`, `test_keep_remediation_cli_61.py`, `test_reanchor_58_r4_lease_fates.py`, `test_reanchor_58_r3_cas_seam.py`;
- the AST-scan covering tests (§8a): `test_fixwave_a28c_63c_i_a.py` (`principals._dispatch_migrate_governed`), plus `test_keep_remediation_cli_61.py`, `test_keeps_cli.py` and `test_principals_cli.py` (`p_module.main`), all already listed;
- the brief's four extras: `test_principal_delete_governed_63a.py`, `test_agent_governance_63c_i_a.py`, `test_fixwave_a19b_63c_i_a.py`, plus a28c (already in).

All runs were in ONE tree, each capped with `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300`. MemAvailable at admission was 23.3 / 22.4 / 22.2 GiB. No cap kill occurred.

| run | principals.py md5 | result |
|---|---|---|
| base (`85a4d2e1`) | `938f7a24…` | **25 failed, 641 passed** (666) |
| fix4 pre-docstring-repair | (intermediate) | 9 failed, 657 passed |
| **fix4 final** | `b9aca87b…` | **9 failed, 657 passed** (666). Identical node outcomes to the intermediate run: 0 transitions. |

Transitions base → final (§8c, by node id; the same 666 nodes on both sides):
- **GREEN→RED: 0.**
- **RED→GREEN: 16.**
  - `test_exhaustion_fates.py::TestTheRegistryIsTheAdjudicationBothWays::test_every_non_derived_site_has_a_row_and_every_row_a_site`
  - `test_principals_cli.py::TestEveryLoreAdmVerbLaundersAStoreFault::test_a_domain_rejection_in_ensure_ready_is_a_stderr_line_and_exit_1[<verb>]` for all **15** verbs: `add`, `list`, `delete`, `suspend`, `unsuspend`, `set-expiry`, `mint-key`, `revoke-key`, `list-keys`, `create-keep`, `add-household`, `remove-household`, `set-rank`, `set-keeper`, `delete-keep`.
- **RED→RED: 9**, all owned by `packet-58-contract` (`scripts/pending_contracts.yaml` lines 79–150: the r3 CAS-seam, r4 lease-fates and exhaustion-fates paths):
  - `test_exhaustion_fates.py::…test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS`. Its problems list is exactly the three `store/lease.py::{get,create,release_if_held}#0 … ['logs-error-class']` entries, and none names `principals`.
  - `test_reanchor_58_r3_cas_seam.py`: `…test_the_injected_instance_reaches_the_caller…[tasks.py::_reanchor_stragglers]` and `…test_every_static_CAS_member_has_a_driver…[findings.py::_run_guarded | tasks.py::_reanchor_stragglers | tasks.py::claim_task]`.
  - `test_reanchor_58_r4_lease_fates.py::…test_the_fail_safe_value_is_served…[create | get | release_if_held | update]`.
  - This is the same 9-id set the fixup report's reference build showed (its §3).
- **Composition:** my build + the test side's docstrings delta `afa519cf` on `test_keeps_cli.py` + `test_keep_remediation_cli_61.py` gave **64 passed**. The delta was then reverse-applied; the tree's `git diff --binary HEAD | md5sum` came back to `b10c6d7e…`, which is the delivered full patch.
- STOP checks (§11 item 5): none fired.
  - No pin asserts a dispatcher's `except` tuple except the fates row, which is GREEN.
  - The fates both-ways pin went GREEN.
  - The 58 runtime cross-check reds are the pre-existing owned CAS-population legs. None is keyed to `principals.py`, per the fixup report §1 and the unchanged red set.
  - The per-verb fallback was NOT taken.

## 5. DUAL — removed-behaviour inventory (each removed `except`, and where its fault lands now)
Class facts (MRO, printed live): `SurrealConnectionError` and `TxnDomainRejectionError` ⊂ `SurrealStoreError`; `KeeperLockoutError` and `KeepNotFoundError` ⊂ `KeepStoreError`. `KeepStoreError`, `PrincipalStoreError` and `PrincipalKeyStoreError` are independent `RuntimeError`s.

| removed / changed catch | classes it caught | lands now | adjudication |
|---|---|---|---|
| `_dispatch` old tuple `(PrincipalStoreError, PrincipalKeyStoreError, SurrealConnectionError, ValueError)` | as listed | `_dispatch` new tuple. Every member is there or a subclass of one (`SurrealConnectionError` ⊂ `SurrealStoreError`). The byte-identical print + `return 1` is retained. | **preserved-with-pin** (§11 item 3). Pins: generated `…test_CONTROL_a_transport_fault_takes_the_same_fate[<verb>]` (GREEN on both builds), `test_principals_cli.py` (0 reds in the file on the final build). **Widened** to raw `SurrealStoreError` + `KeepStoreError` (R2-1 fix, §11 item 1 table). |
| `_dispatch_keep` `(KeepStoreError, SurrealConnectionError, ValueError)` | KeepStoreError (+Lockout/NotFound), transport, `--name` ValueError | `_dispatch`'s handler, same fate | **preserved-with-pin** (§11 item 3, "exact fate … byte-identical"). Pins: `test_keeps_cli.py` + `test_keep_remediation_cli_61.py` (64/64 green), generated pin [keep verbs] + transport control. FR-2 D1's exclusion of raw `SurrealStoreError` is **dropped-deliberately**: re-ruled by §11 item 1, and the missed-wrap property moves to the FR-2 wrap pins (fixup round 2 `b2affe3`: 7 KeepStore write boundaries, all wrap-pinned). |
| `_dispatch_migrate_governed` `(PrincipalStoreError, KeepStoreError, SurrealStoreError, ValueError)` | as listed | `_dispatch`'s handler, same fate | **preserved-with-pin** (§11 item 3). Pins: generated pin `[migrate-governed]` (GREEN on both builds); the a28c success path `code == 0` is GREEN. The REFUSED branch (`result.refused` → stderr + `return 1`) is NOT an except, and it is untouched. |
| `_dispatch_report_unmigrated` `(PrincipalStoreError, SurrealStoreError, ValueError)` | as listed, incl. a rejected SELECT on an absent table | `_dispatch`'s handler, same fate | **preserved-with-pin** (§11 item 3). Pins: `test_principals_cli.py::…test_report_unmigrated_on_an_absent_table_fails_loud_not_a_traceback` and generated `[report-unmigrated]`, both GREEN. |

**Residual behaviour changes that follow from the §11 structure (surfaced, not decisions):**
- **R-1 (ordering).** Before, the dispatcher's `except` printed the stderr line BEFORE its `finally` closed the stores. Now the stores close first (inner `finally`), then `_dispatch` prints.
  - Observable only if a `close()` itself raises during fault handling. Then the close exception replaces the original one: it is printed if it is in the tuple, and it tracebacks (with the original as `__context__`) if it is not.
  - Before, the original error was printed first, and then the close exception tracebacked.
  - This is spec-consistent: §11 item 4 (i) prescribes the nested `try/finally` inside `_dispatch`'s handler. No pin covers a raising `close()`. I'm flagging it for the re-check audit.
- **R-2 (widening).** Store-factory calls (`build_principal_store` / `build_keep_store` / `build_principal_key_store`) used to sit OUTSIDE every dispatcher's `try`. Now they sit inside `_dispatch`'s handler, so a factory `ValueError` / store error becomes stderr + exit 1 instead of a traceback. This is consistent with §11 item 1's property ("every store or domain fault"). No pin covers it.
- The fates row is unchanged by me (test side, `_exhaustion_fates.py`). Its `catches=` equals `ast.unparse` of the new tuple: the match-by-expression pin is GREEN.

## 6. Currency (`uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`, no pytest), verbatim tail
```
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (owner: packet 58 (supersede re-anchor + task guarded-append shell + finding 130 + amendments 1-8) — the 58 builder, serial after 63c-i-a; trigger: … ) · packet-64b-i-contract (owner: packet 64b-i (the governed retrofit of lore_findings — substrate + write side + migrate) — the 64b-i builder; trigger: … )
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it would pass.
CURRENCY   : FAIL — claimed but never run: pytest
  (this is NOT the deploy receipt: it answers 'is every gate owned', never 'may this ship')
exit=1
```
- The owner texts are elided with `…`. The full text is in `scratchpad/currency.txt`.
- **RED_ORPHANED = 0** across typecheck and ruff. Typecheck shows 83 residuals, the same count the fixup report measured before its edits, so this build adds 0 mypy errors.
- The FAIL line is the `--legs` mode's by-design rendering of the unrun pytest leg.
- `uv run ruff check .` → `All checks passed!`

## 7. Backups
Scratch dir is `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5533465e-9db2-4ff8-927e-2f8be7ec7080/scratchpad/`.

| artifact | md5 | check |
|---|---|---|
| `builder-63c-i-a-fix4.full.patch` (`git diff --binary HEAD`, base `9055d61`) | `b10c6d7e2590a08a6b79273c27d86a3d` | `git apply --cached --check` over main HEAD `e35f8ed` → OK |
| `builder-63c-i-a-fix4.delta.patch` (production-only, over `85a4d2e1`; touches ONLY `loremaster/loremaster/principals.py`, +77/−81) | `fd70c6e9d4fff15e605660666a60a737` | OK over HEAD+`85a4d2e1`; OK over HEAD+full2 `e915b90f` |
| `principals.py.fix4-final` (`cp -a`) | `b9aca87bba271174053d931ecad9ae82` | = tree file |
| `principals.py.base` (`cp -a`, pre-edit) | `938f7a246938a79ec609d3263871583d` | — |

HEAD sha of the scratch base is `9055d61f817c7ae6f030141d2f960b6983ae8518`; main HEAD at report time is `e35f8ede3b320b64778f9d02d2ca498a1cbbac76`. The scratch tree `…/scratchpad/fix4` is left in place, and it is NOT a worktree.

## 8. Instruments (pasted verbatim, per brief-base §1)
**(a) covering-test AST scan** (`covering_scan.py`), output: `test_fixwave_a28c_63c_i_a.py | attr principals._dispatch_migrate_governed` · `test_keep_remediation_cli_61.py | attr p_module.main` · `test_keeps_cli.py | attr p_module.main` · `test_principals_cli.py | attr p_module.main`
```python
import ast, sys
from pathlib import Path
TARGETS = {"_dispatch", "_dispatch_keep", "_dispatch_migrate_governed", "_dispatch_report_unmigrated", "main"}
root = Path(sys.argv[1]); hits: dict[str, set[str]] = {}
for path in sorted(root.glob("**/*.py")):
    tree = ast.parse(path.read_text(), filename=str(path)); module_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "loremaster.principals":
            for alias in node.names:
                if alias.name in TARGETS:
                    hits.setdefault(str(path.relative_to(root)), set()).add(f"from-import {alias.name}")
        if isinstance(node, ast.ImportFrom) and node.module == "loremaster":
            for alias in node.names:
                if alias.name == "principals": module_aliases.add(alias.asname or "principals")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "loremaster.principals": module_aliases.add(alias.asname or "loremaster")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in TARGETS:
            base = node.value; name = base.id if isinstance(base, ast.Name) else ast.unparse(base)
            if name in module_aliases or name.endswith("principals"):
                hits.setdefault(str(path.relative_to(root)), set()).add(f"attr {name}.{node.attr}")
for file, why in sorted(hits.items()): print(file, "|", ", ".join(sorted(why)))
```
Bound: this scan finds tests that name the symbols through a `loremaster.principals` binding. A test that shells out to the `lore-adm` console script would be invisible to it. The brief's fixed list covers the known CLI suites.

**(b) dispatcher catch/return lister** (`dispatcher_catches.py`), output in §2 and §5:
```python
import ast, sys
tree = ast.parse(open(sys.argv[1]).read())
for fn in ast.walk(tree):
    if isinstance(fn, ast.AsyncFunctionDef) and fn.name.startswith("_dispatch"):
        handlers = [h for n in ast.walk(fn) if isinstance(n, ast.Try) for h in n.handlers]
        types = [ast.unparse(h.type) for h in handlers]
        returns = [ast.unparse(r.value) for h in handlers for r in ast.walk(h) if isinstance(r, ast.Return)]
        print(fn.name, "| catches:", types or "NONE", "| handler returns:", returns)
```

**(c) junit transition differ** (`transitions.py base.xml build.xml`), output in §4:
```python
import sys, xml.etree.ElementTree as ET
def outcomes(path):
    result = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        node = f"{case.get('classname')}::{case.get('name')}"
        failed = any(c.tag in ("failure", "error") for c in case); skipped = any(c.tag == "skipped" for c in case)
        result[node] = "RED" if failed else ("SKIP" if skipped else "GREEN")
    return result
base, build = outcomes(sys.argv[1]), outcomes(sys.argv[2])
print(f"base: {len(base)} nodes, {sum(v == 'RED' for v in base.values())} RED; build: {len(build)} nodes, {sum(v == 'RED' for v in build.values())} RED")
print("only-in-base:", sorted(set(base) - set(build)), "only-in-build:", sorted(set(build) - set(base)))
for label, frm, to in (("GREEN->RED", "GREEN", "RED"), ("RED->GREEN", "RED", "GREEN"), ("RED->RED", "RED", "RED")):
    nodes = sorted(n for n in base if n in build and base[n] == frm and build[n] == to)
    print(f"== {label}: {len(nodes)}"); [print("  ", n) for n in nodes]
```
The build edit itself was exact-substring surgery (`make_fix4.py`, each replacement asserted to match once). The durable artifact is the delta patch above, not the script.
