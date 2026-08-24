# REPORT-coldaudit-61b-w2 — COLD AUDIT of packet 61b-w2 (visible-Keeps resolver + coverage registry)

## SUMMARY BLOCK
- brief-base v14 read · brief project v7 read
- **VERDICT: GO** — every gate re-run GREEN solo; all 6 mutation proofs re-derived RED-and-restored on an INDEPENDENT instrument; the Fork F resolver reads `member_of` as a plain-table leading-column IndexScan, returns bare ids, is whole-method born-wrapped; the resolver→PDP `keep:<id>` spelling ties end-to-end; the Fork H-a registry defaults GOVERNED (fail-closed) with a live-derived, anti-vacuous growth pin; the §2 deviation is a REGISTRATION not a weakening; boundary clean (no governed-verb routing, no 62/63 reach).
- state: **done**
- deviations (in the BUILD, all disclosed by the builder & confirmed legitimate here): (1) one edit outside w2's writable set — `test_engine_rejection_seam.py::_KEEP_INVOCATIONS` gained one fault-injection entry for the born-wrapped read; confirmed a REGISTRATION the coverage-as-checked-variable pin FORCED, not a weakening (§Deviation-legitimacy).
- **Packages considered:** none — no external mechanism specified (audit re-runs existing gates/instruments; all in-repo).
- **Reuse ledger:** none new — this is an audit; my one instrument (`mutate.py`) is pasted §Instruments.
- **Graded:** `1048138` · HEAD-at-report `1048138` · SAME. (Wave UNCOMMITTED; graded artifacts = the 5 tracked diffs + 2 new src + 2 new test files + the design doc.)
- decisions-needed (surfaced, NOT blockers): (1) `lore_verify`/`lore_index` classified `shared_read` — builder+contract flagged; a lead judgment (defensible: both are ownerless corpus meta-reads; over-gating to governed is the fail-safe alt). (2) #406 read-gap ledger fold (D1 rider — a lead ledger action). (3) Fork H-c verb-routing pin → pkt 63 ledger (named trigger). (4) `visible_keeps` module home (low-stakes).
- receipt pointers: gates §Gate re-runs; mutation table §Mutation re-derivation; resolver §Fork F; spelling tie §Spelling; registry §Fork H-a; deviation §Deviation-legitimacy; boundary §Boundary; residuals §Residuals.

## Capability check (brief-base §4)
All demands satisfiable: read the diff/spec/reports (done), lore tools loaded (`ToolSearch "+lore"`), registered on `lore_comms` (session pkt61), spike-surreal test store `ws://127.0.0.1:18000` reachable (the pins + mutations hit a real store). No impossibility.

## Gate re-runs (independent, SOLO — counts pasted)

| gate | command | verdict |
|---|---|---|
| ruff | `uv run ruff check .` | **`All checks passed!`** |
| typecheck | `./scripts/typecheck.sh` | **8 legs OK** (lorerunes/lorescribe/loresigil/loremaster 235src/skills/docs-eval/scripts + shellcheck), 0 errors |
| currency | `scripts/pending_contract_gate.py --currency` | **PASS** — manifest (typecheck, ruff, pytest) all GREEN, no RED_ORPHANED (exit 0) |
| 28 contract pins | `TestListKeepsForMember` + `test_visible_keeps_61b` + `test_tool_population_61b` | **28 passed in 6.31s** |
| §2-deviation coverage | `test_engine_rejection_seam.py` | **61 passed in 16.06s** |
| full suite (scoped) | `pytest loremaster/tests lorerunes/tests -n auto` (SOLO, 283.58s) | **8798 passed, 50 skipped, 3 xfailed, 0 failed** |

⚠ Note: the currency gate's `pytest` leg IS the full `-n auto` suite over every testpath (a SUPERSET of `loremaster/tests lorerunes/tests` — it adds `lorescribe/tests` + `loresigil/tests` + the `scripts/` guards) and it ran SOLO to GREEN. That is independent full-suite evidence; the scoped run below gives the counted receipt.

## Fork F resolver — direction + index + wrap (brief pt 3)
`KeepStore.list_keeps_for_member` (`keeps.py:850`) reviewed against the D1 ruling (design doc §"Fork F/H addendum" D1) and store law:
- **Direction / PLAIN TABLE:** issues `SELECT out FROM member_of WHERE in = $principal` (`$principal = RecordID(PRINCIPAL_TABLE, member_id)`). NO arrow (`->`/`<-`) — read as a plain edge table, per store-ref **§4** (a graph traversal never uses a secondary index → read the edge as a plain table). Mirror of `list_household`'s reverse `WHERE out = $keep`. ✓
- **Index (leading column):** `WHERE in = $p` is the LEADING column of `member_of`'s `UNIQUE(in, out)` (packet 60) → IndexScan, store-ref **§2** (composite leading-column IndexScans; `IN`-in-`OR`/#413 corollary). NO new index added. Independently EXPLAIN-probed below.
- **BARE ids:** returns `[self._record_id_part(str(row["out"])) for row in rows]` (`keeps.py:911`) — the `xyz` of `keep:xyz`; the resolver adds the prefix. ✓
- **WHOLE-METHOD born-wrap (D1 + adversary B):** the ENTIRE body — `_resolve_principal_id` resolution read AND the `member_of` SELECT — sits inside ONE `with wrap_store_rejection(KeepStoreError, …)` (`keeps.py:897`). A raw `SurrealStoreError` from EITHER surfaces as `KeepStoreError` (never a raw engine error into the authz path); transport/exhausted-contention faults pass through untouched (store-ref **§3**). The deliberate unknown-email `KeepStoreError` from `_resolve_principal_id` is not a `SurrealStoreError` subclass, so the seam passes it through. Verified by mutations #2, #3 below + the D1/B pins.

## Spelling tie: resolver → PDP (brief pt 4)
`resolve_visible_keeps` (`visible_keeps.py:25`) maps each bare id → `keep_scope(bare)` = `f"{KEEP_SCOPE_PREFIX}{bare}"` = `keep:<id>` — the SHARED `lorerunes.pdp.keep_scope` (ONE spelling; never a private `f"keep:{k}"`). Independently confirmed the exact value the shipped PDP consumes matches, end-to-end and PURE (no store):
```
keep_scope('abc123') = 'keep:abc123'
ScopeInKeeps.matches(in-keep)=True  matches(out-keep)=False
ScopeEq.to_surql       -> scope = $s_…   {'…':'keep:abc123'}   # binds keep:<id>
ScopeInKeeps.to_surql  -> '(scope = $k_…)' {'…':'keep:abc123'} # PARENTHESISED (#416), binds keep:<id>
authorize(READ,in-keep)=True   authorize(READ,out-keep)=False
```
The resolver's output value IS exactly what `ScopeInKeeps`/`ScopeEq` compare `resource.scope` against — a mismatch would silently break isolation; there is none. (`keep_scope` reads `KEEP_SCOPE_PREFIX` at call time, so the single constant governs both sides — mutation-proven by the resolver's prefix-mutation pin.)

## Fork H-a registry — REACH + default-governed (brief pt 5)
`server.py:10631–10693`. Reviewed against D2 (design doc §"Fork F/H addendum" D2):
- **DERIVED over live registry, not a hand-list:** `partition_tools_by_population(tools)` → `shared_read = _SHARED_READ_CORPUS_TOOLS ∩ live`; `governed = every other live tool`. Growth/totality/default pins all derive `live_names` from `_build_tools` (the store-free live-registry builder), not a literal.
- **RUNTIME DEFAULT = GOVERNED (fail-closed):** the `else` branch adds every unreviewed tool to `governed`. `_REVIEWED_GOVERNED_TOOLS` is NOT consulted at runtime (review-completeness marker only) — so it can never be a fail-open governed blocklist. The D2 asymmetry (governed-as-shared_read = catastrophic leak; shared_read-as-governed = safe/loud) is honored. Mutation #6 proves the fail-open direction reds.
- **Growth pin non-vacuous:** `assert live_names` guards the empty-registry vacuous-green (adversary C). A synthetic unclassified tool reds the growth pin (mutation #4). Anti-vacuity proven by mutation #5.
- **Partition (exactly one population):** totality pin `shared_read | governed == live_names` AND `shared_read & governed == ∅`. Ghost pin `(reviewed) − live == ∅`; disjoint pin `shared_read_reviewed & governed_reviewed == ∅`.

## §2 deviation legitimacy (brief pt 6)
The one out-of-writable-set edit (`test_engine_rejection_seam.py`, +8 lines) adds `"list_keeps_for_member"` to `_KEEP_INVOCATIONS`.
- **It is a REGISTRATION the coverage-as-checked-variable pin FORCED, not a weakening.** `_methods_routing_through_seam` (AST-derives every KeepStore method referencing `wrap_store_rejection`) NOW includes `list_keeps_for_member` (born-wrapped). `TestTheRoutedSetIsDerivedAndComplete[keep]` asserts `routed == set(_KEEP_INVOCATIONS)` — so the born-wrap FORCES the invocation entry, else the equality reds (the builder's disclosed 2 red pins). The new entry becomes a REAL fault-injection subject (`expected_wrappers=frozenset(_KEEP_INVOCATIONS)`), i.e. MORE coverage.
- **Read/write classification correct:** `list_keeps_for_member` is in `_KEEPSTORE_READ_METHODS` and EXCLUDED from the AST-derived `_WRITE_PATHS` (its statement literal begins `SELECT`, not a mutating keyword). The disjointness pin (`_KEEPSTORE_READ_METHODS.isdisjoint(_WRITE_PATHS)`) holds. So the write-side #400 coverage set is unchanged; the read gets its own wrap pins.
- **Discrimination preserved (two independent ways):** a build where `list_keeps_for_member` does NOT wrap → (a) the AST routed set drops it, so `routed == _KEEP_INVOCATIONS` reds; (b) the dedicated `test_born_wrapped_engine_rejection_becomes_KeepStoreError` reds. Confirmed GREEN: `test_engine_rejection_seam.py` = 61 passed.

## Boundary (brief pt 7)
- **NO governed VERB routed through `authorize`/`authorize_filter`:** `test_tool_population_61b.py` = 0 `authorize`/`authorize_filter` calls (classification only). `partition_tools_by_population` is DEFINED but NOT wired into any runtime verb-routing at 61 (only self-referenced in its docstring/comment) — a SEED. Fork H-c (per-governed-verb routing) correctly DEFERRED to pkt 63 with a named trigger. ✓
- The 4 `authorize(` in `test_visible_keeps_61b.py` are the LEGITIMATE Fork F end-to-end pin (READ-authz of a keep-scoped `Resource` via a `Subject` built from the resolver output) — not governed-verb routing.
- **No 62 credential reach:** the production diff touches no `secret`/`credential`/`principal_key`/`mint` surface. ✓

## Mutation re-derivation (INDEPENDENT instrument — real tree, cp -a backup, byte-exact restore)
Instrument: my OWN `mutate.py` (NOT the builder's; pasted §Instruments) — mutates the REAL tree, runs the ONE target pin, asserts RED, restores from `/tmp/coldaudit61bw2/backup`, re-asserts sha256 identity. `#140` receipt: `PROVENANCE loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` — the pins ran against the REAL tree I mutated. All 3 touched files restored byte-exact (sha256 identical to backup) after the run; whole `git diff --stat` unchanged (`5 files, +625/-1`), zero residue.

| # | mutation | target pin | result |
|---|---|---|---|
| 1 | `keep:`-prefixed return (drop `_record_id_part`) | `test_returns_BARE_keep_ids_not_record_id_strings` | **RED (caught)**, restored |
| 2 | SELECT-only wrap (resolution moved OUTSIDE the `with`) | `test_born_wrapped_RESOLUTION_rejection_becomes_KeepStoreError` | **RED (caught)**, restored |
| 3 | WRONG direction (`WHERE out = $principal`, trailing col) | `test_the_methods_member_of_read_IndexScans_with_a_trailing_TableScan_control` | **RED (caught)**, restored |
| 4 | unclassified live tool (drop `lore_diff` from allowlist) | `test_every_live_tool_is_reviewed_into_a_population` (growth pin) | **RED (caught)**, restored |
| 5 | empty registry (`_build_tools → []`, monkeypatch) | growth pin `assert live_names` + totality pin `assert live_names` (anti-vacuity) | **RED (caught)** — both raised `AssertionError` (`2 passed` = both guards fire) |
| 6 | shared-read DEFAULT (fail-open: unknown → shared_read) | `test_an_unknown_tool_is_governed_by_default_never_shared_read` | **RED (caught)**, restored |

**Mutation #3 verified RIGHT-REASON on the LIVE 3.2.4 store** (re-run in isolation): the mutated trailing-column query's EXPLAIN plan = `operators=['SelectProject', 'TableScan']` on `member_of` → the pin's `not _explain_scans_table(...)` assertion fails (`AssertionError: the method's member_of read TableScanned`), while the correct leading `WHERE in = $p` IndexScans. So the leading-vs-trailing discrimination (store-ref §2 / #413) is proven LIVE, not asserted from prose. Mutations #1/#2 also hit the real store (unique DBs minted).

## Residuals
- **R1 (decision, not a defect):** `lore_verify` + `lore_index` classified `shared_read` (D2 named 7 corpus tools; live registry has 9 ownerless corpus reads). Builder + contract flagged to lead-61. DEFENSIBLE: both are ownerless corpus meta-reads (a claim-check and a freshness/health read — no per-principal data), so `shared_read` is correct; over-gating to governed is the fail-SAFE alternative and keeps the seed green either way. Lead judgment; not a blocker.
- **R2 (ledger, D1 rider):** the mirror KeepStore READ paths (`list_keeps_for_keeper`/`get_keep`/`list_household`/`_read_membership`) + `PrincipalStore.get_by_email` are UNWRAPPED (#406-class read-gap). `list_keeps_for_member` deliberately does NOT clone the gap. The D1 ruling recommends folding these into #406 (with the low-reachability caveat — a plain SELECT rarely hits a domain `SurrealStoreError`). A lead ledger action.
- **R3 (ledger):** Fork H-c per-governed-verb routing pin → pkt 63, named trigger (design doc). A lead ledger action.
- **R4 (low-stakes):** `resolve_visible_keeps` home = new module `loremaster.visible_keeps`; contract flagged `loremaster.auth` as an alternative. NOT `lorerunes` API → no `registration_sites.py` owed. Relocatable.

## Instruments (verbatim — /tmp is not durable; this report is their home)

### `mutate.py` (mutations 1,2,3,4,6 — REAL-tree, byte-exact restore, #140 provenance)
```python
#!/usr/bin/env python3
"""INDEPENDENT cold-audit mutation-proof for packet 61b-w2 (coldaudit-61b-w2).
Mutates the REAL tree (cp -a backup at /tmp/coldaudit61bw2/backup), runs the ONE target pin
per mutation, asserts RED, restores byte-exact, re-asserts sha256. Prints loremaster.__file__."""
from __future__ import annotations
import hashlib, subprocess
from pathlib import Path
REPO = Path("/home/ejprice/PycharmProjects/lore")
BACKUP = Path("/tmp/coldaudit61bw2/backup")
KEEPS = REPO / "loremaster/loremaster/keeps.py"
SERVER = REPO / "loremaster/loremaster/server.py"
MUTATIONS = [
  ("1 keep-prefixed return", KEEPS,
   '        return [self._record_id_part(str(row["out"])) for row in rows]',
   '        return [str(row["out"]) for row in rows]',
   "loremaster/tests/test_keeps_store.py::TestListKeepsForMember::test_returns_BARE_keep_ids_not_record_id_strings"),
  ("2 SELECT-only wrap (resolution outside)", KEEPS,
   ('        with wrap_store_rejection(\n            KeepStoreError,\n'
    '            f"could not list keeps for member {member_email!r}: "\n'
    '            f"the store rejected the household read",\n        ):\n'
    '            member_id = await self._resolve_principal_id(member_email)\n'),
   ('        member_id = await self._resolve_principal_id(member_email)\n'
    '        with wrap_store_rejection(\n            KeepStoreError,\n'
    '            f"could not list keeps for member {member_email!r}: "\n'
    '            f"the store rejected the household read",\n        ):\n'),
   "loremaster/tests/test_keeps_store.py::TestListKeepsForMember::test_born_wrapped_RESOLUTION_rejection_becomes_KeepStoreError"),
  ("3 wrong direction WHERE out", KEEPS,
   '                    f"SELECT out FROM {MEMBER_OF_RELATION} WHERE in = $principal",',
   '                    f"SELECT out FROM {MEMBER_OF_RELATION} WHERE out = $principal",',
   "loremaster/tests/test_keeps_store.py::TestListKeepsForMember::test_the_methods_member_of_read_IndexScans_with_a_trailing_TableScan_control"),
  ("4 drop lore_diff (unclassified live tool)", SERVER,
   '        "lore_dead_code",\n        "lore_diff",\n        # The corpus meta-reads',
   '        "lore_dead_code",\n        # The corpus meta-reads',
   "loremaster/tests/test_tool_population_61b.py::TestTheGrowthPinRedsUntilANewToolIsReviewed::test_every_live_tool_is_reviewed_into_a_population"),
  ("6 fail-open default (unknown -> shared_read)", SERVER,
   ('    for tool in tools:\n        if tool.name in _SHARED_READ_CORPUS_TOOLS:\n'
    '            shared_read.add(tool.name)\n'
    '        else:  # UNREVIEWED / coordination -> governed. FAIL-CLOSED (deny-by-default).\n'
    '            governed.add(tool.name)\n'),
   ('    for tool in tools:\n        if tool.name in _REVIEWED_GOVERNED_TOOLS:\n'
    '            governed.add(tool.name)\n'
    '        else:  # MUTATED: fail-OPEN — unknown -> shared_read (the catastrophic direction).\n'
    '            shared_read.add(tool.name)\n'),
   "loremaster/tests/test_tool_population_61b.py::TestPartitionToolsByPopulationDefaultsGoverned::test_an_unknown_tool_is_governed_by_default_never_shared_read"),
]
def _digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _run_pin(node):
    r = subprocess.run(["uv","run","python","-m","pytest",node,"-q","-p","no:cacheprovider"],
                       cwd=REPO, capture_output=True, text=True)
    return r.returncode != 0, "\n".join((r.stdout+r.stderr).strip().splitlines()[-3:])
def main():
    import loremaster
    print(f"PROVENANCE loremaster.__file__ = {loremaster.__file__}")
    assert str(loremaster.__file__).startswith(str(REPO))
    all_ok = True
    for label, path, old, new, node in MUTATIONS:
        original = path.read_text(encoding="utf-8"); bd = _digest(BACKUP/path.name)
        assert _digest(path) == bd; assert original.count(old) == 1
        path.write_text(original.replace(old, new), encoding="utf-8")
        try: red, tail = _run_pin(node)
        finally: path.write_text((BACKUP/path.name).read_text(encoding="utf-8"), encoding="utf-8")
        restored = _digest(path) == bd
        print(f"[{label}] {'RED(caught)' if red else 'GREEN(SURVIVED!!)'} | restored_byte_exact={restored}")
        all_ok = all_ok and red and restored
    print(f"ALL 5 CAUGHT + RESTORED BYTE-EXACT: {all_ok}")
if __name__ == "__main__": main()
```
Result (verbatim): `PROVENANCE loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`; each of mutations 1,2,3,4,6 `RED(caught) | restored_byte_exact=True`; `ALL 5 CAUGHT + RESTORED BYTE-EXACT: True`.

### `test_zzz_coldaudit_antivacuity_61b_w2.py` (mutation 5 — anti-vacuity, run in loremaster/tests/ then deleted)
```python
"""THROWAWAY anti-vacuity mutation-proof (coldaudit-61b-w2). Runs the REAL growth + totality
pin bodies with the live-registry enumeration monkeypatched EMPTY, asserts each RAISES."""
from pathlib import Path
from typing import Any
import pytest
import test_tool_population_61b as contract
def _empty_build_tools(tmp_path: Path, *, prepare: Any = None) -> Any:
    async def _co() -> list[Any]: return []
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
Result (verbatim): `2 passed` — both the growth pin (`assert live_names … EMPTY`) and the totality pin (`assert live_names … vacuous`) raise on an empty registry, proving the adversary-C anti-vacuity guards are non-vacuous.

## Verification-law honesty note
- The scoped full suite + all 6 mutations ran SOLO (nothing else touching the store) — no `#405` `-n auto` contention flake occurred; the counts are honest.
- lore-first was used for symbol/structure lookups; three sanctioned grep fallbacks (SAID per dogfood protocol): the `_SHARED_READ_CORPUS_TOOLS`/`_REVIEWED_GOVERNED_TOOLS` frozenset literals, the `_KEEP_INVOCATIONS` map, and the retired-name-free `authorize`/`credential` boundary sweep — all non-symbol textual seams (the sanctioned cases), not a lore weakness. Nothing to file.
- One instrument-honesty check on myself: mutation #3's 0.55s runtime looked too fast for a store EXPLAIN, so I RE-RAN it in isolation and read the actual `AssertionError` (a live `['SelectProject','TableScan']` plan) rather than trusting the driver's `returncode != 0` — a red for the RIGHT reason, confirmed.
