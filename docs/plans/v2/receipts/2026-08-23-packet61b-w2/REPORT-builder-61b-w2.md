# REPORT-builder-61b-w2 — the visible-Keeps resolver + coverage-as-checked-variable

## SUMMARY BLOCK
- brief-base v14 read · brief project v7 read
- **state: done-with-deviations**
- **deviation (PROMINENT):** one edit OUTSIDE the named writable set — `loremaster/tests/test_engine_rejection_seam.py` `_KEEP_INVOCATIONS` gained ONE fault-injection entry for `list_keeps_for_member`. My in-scope born-wrap (design D1, REQUIRED) grew the cross-store reach pin's DERIVED routed-set; the `coverage-as-checked-variable` pin then reds until the invocation map tracks it. Directly-caused regression fixed minimally per brief-base §2 (exact edit + rationale below, §Deviation).
- **Packages considered:** none — no external mechanism specified (all in-repo: shared `wrap_store_rejection` seam, `lorerunes.pdp.keep_scope`, `partition_tools_by_posture` precedent).
- **Reuse ledger:** 4 new symbols, all dispositioned (§DRY ledger).
- **Graded:** n/a — this is a BUILD report, not a verdict on another artifact. Built at HEAD `1048138`; `git rev-parse HEAD` = `1048138` at report time (SAME).
- decisions-needed: none. (One ledger item recommended: fold the D1-noted KeepStore READ-path #406 gap — see §Flags.)
- receipt pointers: 28-pin receipt §Gates; full-suite 8798p/0f §Gates; mutation table §Mutation proofs; deviation §Deviation; DRY §DRY ledger.

## Capability check (brief-base §4)
Brief demands: read/edit 3 files + run gates + lore + a live SurrealDB test store (:18000). All satisfied — lore tools loaded via `ToolSearch "+lore"`, registered on `lore_comms` (session pkt61), spike-surreal :18000 reachable (the 79-test keeps run + EXPLAIN pins hit a real store). No impossibility.

## What I built (minimal)

### 1. `KeepStore.list_keeps_for_member(*, member_email: str) -> list[str]` — `loremaster/loremaster/keeps.py`
The symmetric twin of `list_keeps_for_keeper`, appended after it (the class's read surface). Reads `member_of` **as a PLAIN table** filtered on the LEADING column `in`:
```
SELECT out FROM member_of WHERE in = $principal      # $principal = RecordID(PRINCIPAL_TABLE, member_id)
```
— an IndexScan on the existing `UNIQUE(in, out)` (store ref §2 leading-column IndexScan; §4: a graph traversal never indexes → read the edge as a plain table, NEVER an arrow). Returns **BARE** keep ids (`self._record_id_part(str(row["out"]))`) — the resolver adds the `keep:` prefix.

**WHOLE-METHOD BORN-WRAP (design D1):** the ENTIRE body — the `_resolve_principal_id` resolution read AND the `member_of` SELECT — sits inside ONE `with wrap_store_rejection(KeepStoreError, <context>)`, so no raw `SurrealStoreError` from EITHER escapes into the PDP authz path; transport / exhausted-contention faults pass through untouched (store ref §3). An unknown email still raises `KeepStoreError` from `_resolve_principal_id` (not a `SurrealStoreError` subclass → passes the seam untouched), unregressed.

### 2. `resolve_visible_keeps` — NEW module `loremaster/loremaster/visible_keeps.py`
The thin `loremaster` shell (Fork B/F): reads the bare ids from (1), maps each → its `keep:<id>` scope via the **SHIPPED `lorerunes.pdp.keep_scope`** (the ONE spelling — never a private `f"keep:{k}"`, the ROUTING-IS-NOT-SHARING trap #102), returns a `frozenset[str]` (feeds the frozen `Subject`). The store read lives in `loremaster` (Fork B: the pure core stays store-free). `keep_scope` reads `KEEP_SCOPE_PREFIX` at call time, so the single shared constant governs both the PDP and the resolver — proven by the contract's mutate-the-prefix pin.

### 3. Fork H-a tool-population registry — `loremaster/loremaster/server.py` (beside `partition_tools_by_posture`)
- `_SHARED_READ_CORPUS_TOOLS` (9): `lore_search/read/get_symbol/impact/map/dead_code/diff` + the corpus meta-reads `lore_verify/lore_index`.
- `_REVIEWED_GOVERNED_TOOLS` (6): `lore_comms/recall/remember/tasks/claim_task/findings`.
- `partition_tools_by_population(tools) -> (shared_read, governed)` over the LIVE registry: `shared_read = allowlist ∩ live`; `governed = every other live tool`. **RUNTIME DEFAULT = GOVERNED (fail-closed, D2 asymmetry)** — an unreviewed tool is governed, never opened. `_REVIEWED_GOVERNED_TOOLS` is the growth-pin's review-completeness marker, NOT consulted at runtime (so it is not a fail-open governed blocklist).

The 9+6 partition was DERIVED against the authoritative live set `loremaster.server._ALL_BUILTIN_TOOL_NAMES` (server.py:1722, 15 tools) — not guessed — so the growth pin (∪ == live) and ghost pin (reviewed ⊆ live) are green at the 61 seed.

## Gates (receipts)

**The 28 target pins** (`-n auto`):
```
loremaster/tests/test_keeps_store.py::TestListKeepsForMember   (12)
loremaster/tests/test_visible_keeps_61b.py                     (6)
loremaster/tests/test_tool_population_61b.py                   (10)
28 passed in 7.04s
```

**typecheck** (`./scripts/typecheck.sh`): `Success` for lorerunes/lorescribe/loresigil/loremaster (235 src)/skills/doc/eval/scripts + shellcheck — **0 errors**.

**ruff** (`uv run ruff check .`): `All checks passed!` (one import-order I001 in the new `visible_keeps.py` was auto-fixed — `lorerunes` sorts before `loremaster` in this repo's isort config).

**Full suite** (`loremaster/tests lorerunes/tests -n auto`, AFTER the deviation fix):
```
8798 passed, 50 skipped, 3 xfailed, 6 warnings in 271.04s
```
0 failed. (Before the deviation fix: 8791 passed / **2 failed** — the two `TestTheRoutedSetIsDerivedAndComplete[keep]` set-equality pins; see §Deviation.) The run was clean — no `#405` `-n auto` contention flake occurred, so this IS the honest count; no solo re-run was needed. Live guards (`test_readonly_guard` posture partition, `test_mcp_server` registration exact-set, PDP charter/oracle in lorerunes) are inside this suite and green — my server.py additions register NO new tool (module-level symbols only), so the exact-set surface is unchanged.

## Mutation proofs (real tree, `cp -a` content backup → byte-exact restore)
Instrument: `mutation_proof_61b_w2.py` (throwaway, pasted VERBATIM in §Appendix — it asserts each `old_substr` occurs EXACTLY once, mutates, runs the ONE target pin, restores from `/tmp/pkt61w2_backup`, and re-verifies the sha256 round-trips). All 3 touched files restored **byte-exact** (sha256 IDENTICAL to backup) after the run; the throwaway instruments were then deleted.

| # | mutation | target pin | result |
|---|---|---|---|
| 1 | `keep:`-prefixed return (`str(row["out"])`, no `_record_id_part`) | `test_returns_BARE_keep_ids_not_record_id_strings` | **RED (caught)**, restored |
| 2 | SELECT-only wrap (resolution moved OUTSIDE the `with`) | `test_born_wrapped_RESOLUTION_rejection_becomes_KeepStoreError` | **RED (caught)**, restored |
| 3 | WRONG direction (`WHERE out = $principal`, trailing col) | `test_the_methods_member_of_read_IndexScans_with_a_trailing_TableScan_control` | **RED (caught)**, restored |
| 4 | unclassified live tool (drop `lore_diff` from allowlist) | `test_every_live_tool_is_reviewed_into_a_population` (growth pin) | **RED (caught)**, restored |
| 5 | empty registry (`_build_tools → []`, monkeypatch) | `test_every_live_tool_is_reviewed_into_a_population` + totality pin anti-vacuity `assert live_names` | **RED (caught)** — both pins raised `AssertionError` |
| 6 | shared-read DEFAULT (fail-open: unknown → shared_read) | `test_an_unknown_tool_is_governed_by_default_never_shared_read` | **RED (caught)**, restored |

Mutations 1–4 & 6 are production-code edits (keeps.py / server.py) run through the driver. Mutation 5 (anti-vacuity) is a TEST-INTERNAL guard (`assert live_names`) — no production symbol empties the live registry, so it was proven by running the REAL pin body with `_build_tools` monkeypatched to yield `[]` (throwaway `test_zzz_antivacuity_proof_61b_w2.py`, pasted in §Appendix, deleted after; both the growth pin and the totality pin raised as designed).

## Store discipline (store ref cited, never re-transcribed)
- `member_of` read is a **PLAIN TABLE** SELECT (store ref §4: a graph traversal never indexes → read the edge table as a plain table; the `graph_surreal.py` / `list_household` precedent).
- Filtered on the **LEADING column `in`** → IndexScan on the packet-60 `UNIQUE(in, out)` (store ref §2 leading-column IndexScan; #413 / `probe_read_filter_61b.py`). NO new index added — the EXPLAIN pin's positive control confirms the trailing `WHERE out = $keep` still TableScans (so the leading-IndexScan claim is non-vacuous).
- Bound params only (`$principal` = `RecordID(PRINCIPAL_TABLE, member_id)`); `$principal` is not a protected name (unlike `session`, store ref §2).

## Deviation (brief-base §2 — directly-caused regression, fixed minimally + disclosed)
**File:** `loremaster/tests/test_engine_rejection_seam.py` (NOT in my named writable set; NOT a 61b-w2 contract file — it is a pre-existing cross-store reach pin).

**What & why:** My born-wrap of `list_keeps_for_member` (REQUIRED by design D1 — it feeds the PDP's `visible_keep_ids`, so a raw engine error mid-authorization is the consumer-law leak) makes the method reference `wrap_store_rejection`. `test_engine_rejection_seam.py`'s `_methods_routing_through_seam` DERIVES "methods routing through the seam" and its `TestTheRoutedSetIsDerivedAndComplete[keep]` asserts that derived set EQUALS `_KEEP_INVOCATIONS`. This is the `coverage-as-checked-variable` reach pin (#344/#345) — it is DESIGNED to red until a new routed verb gets its fault-injection invocation. Two pins red'd; the fix is the ONE invocation entry the pin demands:
```python
    "list_keeps_for_member": lambda s: s.list_keeps_for_member(member_email=_KEEPER_EMAIL),
```
(added after `delete_keep` in `_KEEP_INVOCATIONS`, with a comment explaining it is the born-wrapped READ). This also feeds the behaviour ∀ + two-layer mutation-sharing ∀ (`TestSharingProvenByMutation` LAYER1/LAYER2) — all green (`_KEEPER_EMAIL` is seeded by the `stores` fixture; resolution runs through the un-patched composed `PrincipalStore`, so under injection at the keeps `run_query` seam the `member_of` SELECT is what raises). `test_engine_rejection_seam.py` went 59p/2f → **61 passed**.

I chose FIX (not FLAG) because: (a) brief-base §2 explicitly permits minimally fixing a regression my in-scope change directly caused; (b) the design (D1 + Fork I coverage mechanism, design doc lines 606/1620–1640/1696) makes this edit MECHANICAL coverage maintenance the reach pin forces, not a design choice; (c) leaving it would hand the lead's cold audit a red suite it would have to fix anyway. If the lead prefers this land as a separate maintenance commit, revert this one hunk and the two set-equality pins re-red — the exact edit is above.

## Flags (surfaced, not silently resolved)
- **Ledger recommendation (design D1, NOT a w2 pin):** the KeepStore READ paths `list_keeps_for_keeper` / `get_keep` / `list_household` / `_read_membership` are all UNWRAPPED (leak a raw `SurrealStoreError` from their SELECT) — the #406 read-side gap. `list_keeps_for_member` deliberately does NOT clone that gap (it is born-wrapped). D1 recommends the lead fold these READ paths into #406 (with the reachability caveat: a plain SELECT rarely hits a domain-meaningful rejection). Out of w2 scope — surfaced for the lead.
- **`registration_sites.py`: NOT owed.** `resolve_visible_keeps` lives in `loremaster.visible_keeps` and imports `KeepStore` — it is NOT `lorerunes` API, so no workspace-member registration is owed (the contract's Home flag concurs). The contract flagged `loremaster.auth` as an alternative home; I kept the contract's `loremaster.visible_keeps` (the cleanest store-touching split; packet 62 imports it to build the full `Subject`). Low-stakes — the lead/builder may relocate it.

## DRY ledger (brief-base §6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `KeepStore.list_keeps_for_member` | `lore_get_symbol` list_keeps_for_keeper / list_household; `lore_get_symbol` set_keeper (wrap idiom) | the mirror read + the born-wrap idiom | **HAND-ROLLED** (a NEW domain read the contract requires) but REUSES `_resolve_principal_id`, `_query`, `PrincipalStore._as_rows`, `_record_id_part`, `wrap_store_rejection`, `MEMBER_OF_RELATION/PRINCIPAL_TABLE` — mirrors `list_keeps_for_keeper`'s shape; no new helper introduced |
| `resolve_visible_keeps` | `lore_search` "visible keeps resolver Subject" (contract is the only hit) | no pre-existing resolver | **HAND-ROLLED** (NEW shell the contract requires) — REUSES `lorerunes.pdp.keep_scope` (the ONE spelling, mandated) + `KeepStore.list_keeps_for_member`; no `f"keep:{k}"` clone |
| `partition_tools_by_population` | `lore_get_symbol` `partition_tools_by_posture` | the DERIVED-over-live-registry precedent (read/mutating by `readOnlyHint`) | **HAND-ROLLED as a SIBLING** — cannot REUSE/EXTEND `partition_tools_by_posture`: it partitions by a DIFFERENT axis (`readOnlyHint`), and per D2 BOTH populations contain read tools, so the corpus/coordination split needs its own classification. Mirrors its DERIVED-over-live-registry shape + placement |
| `_SHARED_READ_CORPUS_TOOLS`, `_REVIEWED_GOVERNED_TOOLS` | `grep`/read `_ALL_BUILTIN_TOOL_NAMES` (server.py:1722) | the tool UNIVERSE (not a classification) | **HAND-ROLLED** — design D2 mandates two curated human-review sets (the growth pin's completeness marker); no existing classification of tools into these populations exists |

Fallbacks to grep (said out loud per dogfood protocol): used `grep` to (a) confirm `_ALL_BUILTIN_TOOL_NAMES` uniqueness/site (a non-symbol textual seam — the exact string in two frozensets), and (b) locate the seam-coverage `_KEEP_INVOCATIONS` map. Both are the sanctioned grep cases (exhaustiveness of a literal + a config-like map), not a lore weakness — nothing to file.

## Appendix — verbatim instruments (deleted from the tree after the run; the report is their durable home)

### `mutation_proof_61b_w2.py`
```python
#!/usr/bin/env python3
"""Mutation-proof driver for packet 61b-w2 (builder-61b-w2).

Mutates the REAL tree in place (cp -a content backup already taken at
/tmp/pkt61w2_backup), runs the ONE target pin per mutation, asserts it goes RED,
then restores the file byte-exact from the backup and re-asserts identity.
Run: `uv run python mutation_proof_61b_w2.py`
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent
BACKUP = Path("/tmp/pkt61w2_backup")
KEEPS = REPO / "loremaster/loremaster/keeps.py"
SERVER = REPO / "loremaster/loremaster/server.py"

MUTATIONS = [
    ("1. keep:-prefixed return -> bare-id pin reds", KEEPS,
     '        return [self._record_id_part(str(row["out"])) for row in rows]',
     '        return [str(row["out"]) for row in rows]',
     "loremaster/tests/test_keeps_store.py::TestListKeepsForMember::test_returns_BARE_keep_ids_not_record_id_strings"),
    ("2. SELECT-only wrap (resolution outside) -> resolution-wrap pin reds", KEEPS,
     ('        with wrap_store_rejection(\n            KeepStoreError,\n'
      '            f"could not list keeps for member {member_email!r}: "\n'
      '            f"the store rejected the household read",\n        ):\n'
      '            member_id = await self._resolve_principal_id(member_email)\n'),
     ('        member_id = await self._resolve_principal_id(member_email)\n'
      '        with wrap_store_rejection(\n            KeepStoreError,\n'
      '            f"could not list keeps for member {member_email!r}: "\n'
      '            f"the store rejected the household read",\n        ):\n'),
     "loremaster/tests/test_keeps_store.py::TestListKeepsForMember::test_born_wrapped_RESOLUTION_rejection_becomes_KeepStoreError"),
    ("3. WRONG direction (WHERE out=$p) -> direction/EXPLAIN pin reds", KEEPS,
     '                f"SELECT out FROM {MEMBER_OF_RELATION} WHERE in = $principal",',
     '                f"SELECT out FROM {MEMBER_OF_RELATION} WHERE out = $principal",',
     "loremaster/tests/test_keeps_store.py::TestListKeepsForMember::test_the_methods_member_of_read_IndexScans_with_a_trailing_TableScan_control"),
    ("4. unclassified live tool (drop lore_diff from allowlist) -> growth pin reds", SERVER,
     '        "lore_dead_code",\n        "lore_diff",\n        # The corpus meta-reads',
     '        "lore_dead_code",\n        # The corpus meta-reads',
     "loremaster/tests/test_tool_population_61b.py::TestTheGrowthPinRedsUntilANewToolIsReviewed::test_every_live_tool_is_reviewed_into_a_population"),
    ("6. shared-read DEFAULT (fail-open) -> default-governed pin reds", SERVER,
     ('    for tool in tools:\n        if tool.name in _SHARED_READ_CORPUS_TOOLS:\n'
      '            shared_read.add(tool.name)\n'
      '        else:  # UNREVIEWED / coordination -> governed. FAIL-CLOSED (deny-by-default).\n'
      '            governed.add(tool.name)\n'),
     ('    for tool in tools:\n        if tool.name in _REVIEWED_GOVERNED_TOOLS:\n'
      '            governed.add(tool.name)\n'
      '        else:  # MUTATION: fail-OPEN (governed blocklist) — unknown -> shared_read.\n'
      '            shared_read.add(tool.name)\n'),
     "loremaster/tests/test_tool_population_61b.py::TestPartitionToolsByPopulationDefaultsGoverned::test_an_unknown_tool_is_governed_by_default_never_shared_read"),
]

def _digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def _run_pin(node):
    r = subprocess.run(["uv","run","python","-m","pytest",node,"-q","-p","no:cacheprovider"],
                       cwd=REPO, capture_output=True, text=True)
    return r.returncode != 0

def main():
    all_ok = True
    for label, path, old, new, node in MUTATIONS:
        original = path.read_text(encoding="utf-8")
        backup_digest = _digest(BACKUP / path.name)
        assert _digest(path) == backup_digest
        assert original.count(old) == 1, f"[{label}] old occurs {original.count(old)}x"
        path.write_text(original.replace(old, new), encoding="utf-8")
        try: red = _run_pin(node)
        finally: path.write_text((BACKUP / path.name).read_text(encoding="utf-8"), encoding="utf-8")
        restored = _digest(path) == backup_digest
        print(f"[{label}] {'RED(caught)' if red else 'GREEN(SURVIVED!)'}; restored={restored}")
        all_ok = all_ok and red and restored
    print(f"ALL CAUGHT + RESTORED: {all_ok}")

if __name__ == "__main__":
    main()
```
Result (verbatim): mutations 1,2,3,4,6 each `RED (caught); restored byte-exact: True`; `ALL MUTATIONS CAUGHT + RESTORED: True`.

### `test_zzz_antivacuity_proof_61b_w2.py` (mutation 5)
```python
"""THROWAWAY anti-vacuity mutation-proof for the growth + totality pins (builder-61b-w2).
Runs the REAL pin body with _build_tools monkeypatched to yield an empty registry and
asserts it raises (the anti-vacuity guard is NON-vacuous)."""
from __future__ import annotations
from pathlib import Path
from typing import Any
import pytest
import test_tool_population_61b as contract

def _empty_build_tools(tmp_path: Path, *, prepare: Any = None) -> Any:
    async def _co() -> list[Any]:
        return []
    return _co()

async def test_growth_pin_reds_on_empty_registry(tmp_path, monkeypatch):
    monkeypatch.setattr(contract, "_build_tools", _empty_build_tools)
    instance = contract.TestTheGrowthPinRedsUntilANewToolIsReviewed()
    with pytest.raises(AssertionError, match="EMPTY"):
        await instance.test_every_live_tool_is_reviewed_into_a_population(tmp_path)

async def test_totality_pin_reds_on_empty_registry(tmp_path, monkeypatch):
    monkeypatch.setattr(contract, "_build_tools", _empty_build_tools)
    instance = contract.TestPartitionToolsByPopulationCoversTheLiveRegistry()
    with pytest.raises(AssertionError, match="vacuous"):
        await instance.test_every_registered_tool_is_classified_into_exactly_one_population(tmp_path)
```
Result (verbatim): `2 passed in 1.00s` — both pins raise `AssertionError` on an empty registry, proving the anti-vacuity guards fire.
