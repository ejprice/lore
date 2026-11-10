# Cold audit, packet 58 fix wave (DELTA) — dimension: receipt verification (ca58d-receipts)

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read · landmines recalled (10 returned, k=50, so the set is complete)
- State: done. Verdict for this dimension: **the FIXWAVE-2 and contract receipts are VALID at `cdf1ce4`; FIXWAVE-1's receipts are MISMATCHED (a different tree); I re-ran them on the graded commit: 2316 passed, 0 failed, EXIT=0 (§3); the `packet-58-fixwave` registry entry should be DELETED now: all 17 of its ids are green at `cdf1ce4`, and while the entry exists the packet's full-suite currency renders pytest RED_ORPHANED with 17 SELF-DESTRUCT lines (§4).**
- Graded: `cdf1ce4` · HEAD-at-report: `cdf1ce4` · SAME (live tree, 2026-11-10)
- Deviations: (1) the test runs went inline, not to a `haiku-runner`: this agent has no `Agent` tool. (2) FIXWAVE-1's mismatched gate was re-run on `cdf1ce4` (the graded commit) rather than on `70665b9` (§3 says why).
- Packages considered: none, no mechanism specified (two audit instruments, pasted in §6).
- Odoo-20 portability: n/a, no Odoo seam touched.
- Reuse ledger: none (no production code).
- Findings: F1 major (registry entry not discharged by the build; a full-suite currency would go RED_ORPHANED) · F2 minor (FIXWAVE-1 TREE does not match `70665b9`) · F3 minor (the currency render's "owned by" lists every bound, filed as **#633**) · F4 minor (wording problems in the builder's receipt prose).
- Decisions needed: the lead should delete `packet-58-fixwave` from `scripts/pending_contracts.yaml` (one-concern commit) before the packet's full suite runs. I did not edit it, as the brief asked.
- Receipt pointers: §1 tree identity · §2 the registry against RED/SAT/build · §3 the FIXWAVE-1 re-run · §4 the discharge probe · §5 currency · §6 instruments.

All measurements below were made 2026-11-10 against graded commit `cdf1ce4`, in my scratch copy
`/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58d/ca58d-receipts`
(`scratch_copy.sh`, then `git checkout cdf1ce4 -- .`; HEAD `cdf1ce4`; status: untracked REPORT files plus one sibling auditor's file only;
`loremaster.__file__` = `<copy>/loremaster/loremaster/__init__.py`; `tree_id.sh` TREE=`1ae664a9…f50e`, DIRTY_FILES=6, all of them untracked).
Logs: `…/scratchpad/ca58d/logs/`.

## 1. Tree identity — do the builder's and the contract's gate trees match the commits that landed them? (HIGH)
Method: `tree_vs_commit.sh` (§6) compares every non-ignored file on disk in a gate's scratch tree with the blob at a commit.
The builder's scratch trees still exist, and `tree_id.sh` on each one today reproduces the TREE in its gate logs
(fw1 `c01c402b…8b308`, fw2 `1bfc28b9…45c49`, fw1mut `74b21ebf…`, fw2mut `c84fe9b8…`), so the trees were not touched after the runs.
| gate tree | compared to | differing paths (excluding untracked REPORT-*.md) | verdict |
|---|---|---|---|
| builder `fw2` (FIXWAVE-2 gates, TREE `1bfc28b9…`) | `cdf1ce4` | **none** | **MATCH**. Literal check: `git archive cdf1ce4` plus fw2's 5 REPORT files hashes to TREE=`1bfc28b9c9fd25f880b400584daab095104f3d4a584299592ce456f543245c49`, byte-equal to the log header |
| builder `fw1` (FIXWAVE-1 gates, TREE `c01c402b…`) | `70665b9` | `CLAUDE.md`, `scripts/mutation_proof.py`, `scripts/pending_contract_gate.py`, `scripts/test_parked_contracts.py` | **MISMATCH (F2)**. The 4 production files are byte-equal to `70665b9`. The 4 differing files are the lead's commits `e0df22b` and `8fc46f0`, which landed between the builder's base `25cfd16` and `70665b9`. `70665b9` plus fw1's REPORT files hashes to `17e999be…` ≠ `c01c402b…` |
| control: builder `fw1` | `25cfd16` | the 4 production files | the instrument discriminates (it sees the builder's diff) |
| contract `c58r53/fw/base` (§FIXWAVE gates, TREE `e4e9628e…`) | `25cfd16` | none | MATCH |
| contract `c58r53/fw13/base` (§FIXWAVE-13 gates, TREE `02b94041…`) | `1130ac9` | none | MATCH |
Coverage line for each comparison: `disk_files=1842–1846 commit_files=1838–1840` (log: the command output in §6).

## 2. The `packet-58-fixwave` registry entry against RED, SAT and the build (HIGH)
Instrument: `junit_vs_registry.py` (§6) reads the entry from `scripts/pending_contracts.yaml` at `cdf1ce4` (the live registry is byte-equal to `cdf1ce4`; `git diff --quiet` was clean) and reports each id's fate in each junit file, plus every failure the entry does not own.
| junit | tree | entry ids found | fates | failures not in the entry |
|---|---|---|---|---|
| contract `fw-red.xml` (the declaration of 9, made at 01:00:27, before the run started at 01:01:18) | `380414c` + contract | 9/17 (the 8 §13 ids did not exist yet) | 9 failed | 0 |
| contract `fw13-red.xml` (the declaration of 17, made at 02:04:52, before the run started at 02:05:28; `declared_red.txt` md5 `66fc44be…`, as reported) | `cec81c2` + contract | 17/17 | **17 failed** | **0** over 2 736 testcases |
| contract `fw13-red2.xml` (the final test bytes, the 2 re-keyed files) | `02b94041…` = `1130ac9` | 14/17 (the other 3 live in files the re-key did not touch) | 14 failed | 0 |
| contract `fw13-sat.xml` / `fw13-sat2.xml` | reference | 17/17 → 16 passed + 1 (R6 mutation 2, re-keyed) → 14/14 passed after the re-key | — | 0 |
| builder `fw2.xml` (`--run-parked`, 24 selectors) | **`cdf1ce4`** (§1) | **17/17** | **17 passed** | 30, every one owned by `packet-64b-i-contract` (with YAML decoding, the `[\t]` id matches too, so the builder's "29 of 30 by name" undercounts: it is 30/30) |
| builder `fw1b.xml` | fw1 tree | 3/17 (`test_reanchor_58_fixwave.py` was not in the run's file list; the R6 ids did not exist yet) | 3 failed (the part-2 ids, as the builder says) | 0 |
- **The entry owns exactly the ids that were red:** declared = registry = observed-red (17 = 17 = 17; set differences empty), with 0 unowned failures in the 34-file RED.
- **All 17 ids are green at `cdf1ce4`** (fw2.xml, whose TREE equals `cdf1ce4` plus untracked reports). Per the operator's 2026-10-31 rule I did not re-run a valid receipt.

## 3. FIXWAVE-1's mismatched gate, re-run on the graded commit
Why `cdf1ce4` and not `70665b9`: the verdict is on `cdf1ce4`. FIXWAVE-2's valid run (24 files) does not include `test_findings.py` or `test_sdk3_row_bound.py`, which are in FIXWAVE-1's set and cover part 1's `findings.py` / `_txn.py` marker change. Re-running FIXWAVE-1's exact command on `cdf1ce4` closes that gap and re-establishes part 1's gate on the tree that ships.
Command (FIXWAVE-1's own, from `haiku-run-dbxPIb.log.sh`): `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest <the same 15 files> -q -n 8 -p no:cacheprovider --timeout=300 --junitxml=…/fw1-rerun.xml`, with a file-existence guard first (15/15 present). The log is `…/scratchpad/ca58d/logs/fw1-rerun.log`, with the `tree_id.sh` header TREE=`1ae664a9…`.
**RESULT (2026-11-10, HEAD `cdf1ce4`, TREE `1ae664a9…`): `2316 passed, 1 skipped … in 370.17s`, `EXIT=0`.**
- 0 failed. `fw1-rerun.log:65`: "parked contracts: 29 test(s) deselected (entries: packet-64b-i-contract)", the same 29 that fw1b deselected.
- The 5 `packet-58-fixwave` ids inside this set all **passed** (hub cap+1 [0] and [2], the over-weight row, R6 mutations 1 and 2). 0 failures outside the entry.
- Part 1's gate now holds on the graded tree, including `test_findings.py` and `test_sdk3_row_bound.py`. F2 is closed as a receipt gap with no behavioural consequence.

## 4. Should `packet-58-fixwave` be discharged now? YES (HIGH)
- Its own `reopen_trigger` says *"then every id below goes GREEN and this entry self-destructs and is deleted with the build"*. The build commit `cdf1ce4` did not delete it (the registry at `cdf1ce4` still carries the entry, `active: true`, 17 ids). The build left the rider undone.
- **Consequence, measured without a pytest run** (`discharge_probe.py`, §6): fw2.xml (the `cdf1ce4` tree) was fed to the currency gate's own judges (`PendingContractGate.partition_pytest`, `pytest_self_destruct_findings`), with an xunit1 `file` bridge because the builder's junit is xunit2, which the gate's reader refuses.
  - **As committed:** 30 failures owned · 0 UNEXPECTED · **17 SELF-DESTRUCT lines** ("adjudicated red … (bound 'packet-58-fixwave') is green — delete it with the fix."). `_residuals_for` turns these into pytest residuals, and `gate_currency` then marks the gate **RED_ORPHANED**. So the packet's once-per-packet full-suite currency at `cdf1ce4` would FAIL on pytest for this reason alone. (Code read: `scripts/pending_contract_gate.py::_residuals_for`, `::gate_currency`.)
  - **Positive control, with the entry removed:** 30 failures owned (all 64b-i) · 0 UNEXPECTED · **0 self-destruct**.
  - Log: `…/scratchpad/ca58d/logs/discharge_probe.log` (EXIT=0).
- Removing the entry changes nothing on typecheck/ruff: `packet-58-fixwave` claims no mypy line (no `missing_symbols` / `unsymboled_codes`), and all 50 typecheck residuals sit in 64b-i files (§5).
- **Recommendation:** delete the whole `packet-58-fixwave` bound in one commit (lead), then run `--verify-registry`. Not done by me: I was told not to edit it.

## 5. Currency, typecheck + ruff (once, in my copy, at `cdf1ce4`) (HIGH)
`uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` → log `…/logs/currency.log`, TREE `1ae664a9…`, EXIT=1.
- typecheck **RED_ADJUDICATED — 50 residual(s)** · ruff **GREEN** · the only ORPHAN is the leg-filtered `pytest NOT_RUN` (#621).
- **RED_ORPHANED = 0 over typecheck/ruff.**
- `--verify-registry` → `…/logs/verify-registry.log`, EXIT=0 (`self-destruct: 9 import-checked absent · 34 UNCHECKED`, all 64b-i symbols).
- The 50 errors are spread over these files, in builder `typecheck_fw1b.log` and `typecheck_fw2.log` alike: 64b findings files plus `test_comms_footer.py`, `test_mcp_server.py` (6), `test_reanchor_58_r3_cas_seam.py` (1) and `test_reanchor_58_r4_state.py` (1). **No fix-wave test file appears.**

## Findings
**F1 (major, product-process; HIGH).** `scripts/pending_contracts.yaml` at `cdf1ce4` still carries `packet-58-fixwave` (17 ids, `active: true`), and all 17 are green at `cdf1ce4`. Its own trigger says it is "deleted with the build". With it in place, the currency gate's pytest leg emits 17 SELF-DESTRUCT residuals, so pytest renders RED_ORPHANED at the packet's full-suite close-out. Receipt: §4 (`discharge_probe.log`, with and without the entry). Fix: delete the bound.

**F2 (minor, receipt; HIGH).** FIXWAVE-1's gate TREE `c01c402b…` is not the tree of `70665b9`: fw1 is `25cfd16` plus the builder's diff, and lacks `e0df22b` and `8fc46f0` (`CLAUDE.md`, `scripts/mutation_proof.py`, `scripts/pending_contract_gate.py`, `scripts/test_parked_contracts.py`). The production bytes did land unchanged. `8fc46f0` touches the parked-contract deselection loader that the run used. On a valid-UTF-8 registry the behaviour is the same (code read, MEDIUM), but the receipt does not describe the commit. Closed by §3's re-run on `cdf1ce4`.

**F3 (minor, served English in the gate script, pre-existing, not fix-wave code; HIGH). Filed as #633.** `scripts/pending_contract_gate.py::gate_currency` builds the RED_ADJUDICATED "owned by:" list from **every** registry bound (`for bound in gate.registry.bounds`), not from the bounds that own a residual. At `cdf1ce4` it serves "owned by: packet-58-fixwave … · packet-64b-i-contract …" for 50 mypy residuals, of which 58-fixwave owns 0. The builder copied this into both FIXWAVE receipt tables ("owners packet-58-fixwave, packet-64b-i-contract"). The contract's §FIXWAVE gate row says the opposite, and correctly: "packet-58-fixwave claims no mypy error". Do you want it fixed in this packet?

**F4 (minor, receipt wording; HIGH).**
- (a) FIXWAVE-1 says the typecheck's 50 errors are "64b findings tests + 58 `_run_guarded` + **fixwave test files**". No fix-wave test file is among them (§5).
- (b) FIXWAVE-1 says "the 64b findings tests in `test_findings.py`/`test_mcp_server.py` were not red in this scratch run". They were **deselected**, not run: `fw1b.log:747`, "parked contracts: 29 test(s) deselected (entries: packet-64b-i-contract)". The 3-failed count stands. The prose reads as "they passed", which is not what happened.
- (c) FIXWAVE-2's "29 of 30 match registry `red_nodeids` by name" undercounts: decoded, 30/30 match, and the gate's own partition owns all 30 (§4).

Verified with no defect (each against its own log or junit): fw1b 3 failed / 2312 passed / EXIT=1 · ruff_fw1b EXIT=0 · fw2 30 failed / 2455 passed / EXIT=1 · ruff_fw2 EXIT=0 · typecheck_fw1b/fw2 `Found 50 errors` · currency_fw1b/fw2 ruff GREEN, typecheck RED_ADJUDICATED, only the pytest NOT_RUN orphan · fw1mut 4 failed / 328 passed · fw2mut 20 failed / 269 passed. Contract: fw-red 9/2715, fw-red2 6/1, fw-sat 1/2723, fw-sat2 7 passed, fw13-red 17/2718, fw13-red2 14/5, fw13-sat 1/2734, fw13-sat2 19 passed. The two declarations' md5s match the report (`98552d57…`, `66fc44be…`), and each predates its run.
Not verified by me (other dimensions or out of reach): the content of the mutation self-checks (fw1mut ran on a tree that still held the F7b try, per the builder's own note: a self-check, not a gate) and the probes' adequacy.

## 6. Instruments (pasted verbatim; scratch copies are disposable)
`tree_vs_commit.sh`:
```bash
#!/usr/bin/env bash
# tree_vs_commit.sh <repo> <commit> <worktree>
# Compare every non-ignored file on disk in <worktree> (tracked + untracked, as tree_id.sh
# hashes them) against the blob of the same path in <commit> of <repo>. Prints one line per
# differing path: ONLY_DISK / ONLY_COMMIT / DIFFER, then a coverage line. Exit 0 always.
set -euo pipefail
repo=$1; commit=$2; wt=$3
declare -A blob
while IFS=$'\t' read -r meta path; do blob["$path"]=$(awk '{print $3}' <<<"$meta"); done < <(git -C "$repo" ls-tree -r "$commit")
n_disk=0; n_diff=0
declare -A seen
while IFS= read -r -d '' p; do
  [ -f "$wt/$p" ] || continue
  n_disk=$((n_disk+1)); seen["$p"]=1
  h=$(git -C "$wt" hash-object --no-filters -- "$p")
  if [ -z "${blob[$p]:-}" ]; then echo "ONLY_DISK $p"; n_diff=$((n_diff+1))
  elif [ "$h" != "${blob[$p]}" ]; then echo "DIFFER $p"; n_diff=$((n_diff+1)); fi
done < <(git -C "$wt" ls-files -z --cached --others --exclude-standard | sort -z -u)
n_commit=0
for p in "${!blob[@]}"; do n_commit=$((n_commit+1)); [ -n "${seen[$p]:-}" ] || { echo "ONLY_COMMIT $p"; n_diff=$((n_diff+1)); }; done
echo "COVERAGE disk_files=$n_disk commit_files=$n_commit differing=$n_diff"
```
The literal TREE reconstruction: `git archive <commit> | tar -x -C <d>`, then copy the gate tree's `REPORT-*.md` into `<d>`, `git -C <d> init`, and hash with `tree_id.sh`'s own pipeline.

`junit_vs_registry.py <registry> <entry-id> <junit>...`:
```python
import sys, xml.etree.ElementTree as ET, yaml
def nodeid(tc):
    cls = tc.get("classname", ""); name = tc.get("name", "")
    parts = cls.split(".")
    for i in range(len(parts), 0, -1):
        mod = "/".join(parts[:i])
        if parts[i - 1].startswith("test_") or parts[i - 1].startswith("_"):
            return "::".join([mod + ".py", *parts[i:], name])
    return f"{cls}::{name}"
def fate(tc):
    for tag in ("failure", "error", "skipped"):
        if tc.find(tag) is not None:
            return {"failure": "failed"}.get(tag, tag)
    return "passed"
reg = yaml.safe_load(open(sys.argv[1])); entries = reg["bounds"]
by_id = {e["id"]: e for e in entries}
owned = {n for f in by_id[sys.argv[2]]["files"] for n in f.get("red_nodeids", [])}
all_owned = {n: e["id"] for e in entries for f in e.get("files", []) for n in f.get("red_nodeids", [])}
print(f"entry {sys.argv[2]}: {len(owned)} ids")
for path in sys.argv[3:]:
    cases = {nodeid(tc): fate(tc) for tc in ET.parse(path).iter("testcase")}
    fates = {n: cases.get(n, "ABSENT") for n in owned}
    tally = {}
    for v in fates.values(): tally[v] = tally.get(v, 0) + 1
    print(f"== {path}\n  COVERAGE testcases={len(cases)} entry_ids_found={sum(v != 'ABSENT' for v in fates.values())}/{len(owned)} entry_fates={tally}")
    for n, v in sorted(fates.items()):
        if v != "passed": print(f"  ENTRY {v}: {n}")
    other = sorted(n for n, v in cases.items() if v in ("failed", "error") and n not in owned)
    print(f"  failures_not_in_entry={len(other)}")
    for n in other: print(f"    {all_owned.get(n, 'UNOWNED')}: {n}")
```

`discharge_probe.py <junit> <selector>...` (run from the copy root):
```python
import sys, dataclasses, tempfile, yaml
from pathlib import Path
sys.path.insert(0, "scripts")
import pending_contract_gate as g
junit, selection = Path(sys.argv[1]), tuple(sys.argv[2:])
import xml.etree.ElementTree as ET
# BRIDGE: the builder's junit is xunit2 (no `file` attr); derive it from classname.
tree = ET.parse(junit)
for tc in tree.iter("testcase"):
    if not tc.get("file"):
        parts = tc.get("classname", "").split(".")
        idx = max(i for i, part in enumerate(parts) if part.startswith("test_"))
        tc.set("file", "/".join(parts[: idx + 1]) + ".py")
run = dataclasses.replace(g.JUnitReportReader.read(ET.tostring(tree.getroot(), encoding="unicode")), selection=selection)
print(f"run: passed={run.passed} failing={len(run.outcomes)} collected={len(run.collected)} selectors={len(selection)}")
reg_path = Path("scripts/pending_contracts.yaml")
raw = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
without = dict(raw, bounds=[b for b in raw["bounds"] if b["id"] != "packet-58-fixwave"])
tmp = Path(tempfile.mkdtemp(dir=Path(sys.argv[0]).parent)) / "registry_without_58fixwave.yaml"
tmp.write_text(yaml.safe_dump(without, allow_unicode=True, sort_keys=False), encoding="utf-8")
for label, path in (("AS COMMITTED", reg_path), ("WITHOUT packet-58-fixwave", tmp)):
    gate = g.PendingContractGate(g.PendingContractRegistry.load(path), Path.cwd())
    part = gate.partition_pytest(run)
    sd = gate.pytest_self_destruct_findings(run)
    print(f"== {label}: bounds={[b.id for b in gate.registry.bounds]}")
    print(f"   expected(owned) failures={len(part.expected)} UNEXPECTED={len(part.unexpected)} self-destruct/stale findings={len(sd)}")
    for o in part.unexpected: print(f"   UNEXPECTED {o.node_id}")
    for line in sd: print(f"   {line[:200]}")
```
Routing: every step ran inline. I have no `Agent` tool, so there was no haiku-runner. The test runs: 1 pytest (§3) and 2 gate-script runs (§5). Everything else read existing logs and junit files.
