brief-base v18 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done-with-deviations. All 4 items are built in scratch on HEAD `fb95d1f` + the fix-up patch `2c88b1a9`. The declared-set runs show 0 GREEN→RED and 2 RED→GREEN (the fix-up's two intended reds). Currency `--legs typecheck,ruff` shows **no RED_ORPHANED**: typecheck RED_ADJUDICATED (83 residuals, all owned), ruff GREEN. `ruff check .` is clean.
- **Deviations:**
  - (1) The D-1 fix (the lead's ruling) ships with **no pin**. The fix-up delta has no test for it, and I may not write tests. It is measured only by the fix-up's probe, run on the base gate and the build gate (§ITEMS 1b). A pin needs a test author.
  - (2) Every pytest used `uv run --no-sync` rather than the brief's bare `uv run`. A plain sync inside a scratch copy is #140 poison mode 3, and fix2 did the same.
  - (3) The brief says "`governed._scope_count`", which does not exist. `_scope_count` lives in `principals.py`. See §FORKS F-1.
- **Packages considered:** none. No new mechanism: a stdlib shape check moved to one home, and a list comprehension.
- **Odoo-20 portability:** n/a (no Odoo seam touched).
- **Reuse ledger:** 1 new symbol, `governed.group_all_count`, which EXTENDS (moves and publishes) `principals._group_all_count`. `entries_for` REPLACES `entry_for`. See §DRY.
- **Graded:** n/a (builder).
- **Decisions needed:**
  - (a) **am-37 §8.3's "five readers" is an undercount.** Awk finds at least 6 more tolerant GROUP ALL count readers, two of them fail-OPEN on a delete/alarm path (§FLAGS F-1). Please route them.
  - (b) The receipt rendering fork (§FORKS F-2).
- **Receipt pointers:** §ITEMS · §RUNS · §CURRENCY · §MUTATION · §DUAL · §BACKUP · §INSTRUMENTS.

## CAPABILITY CHECK
Every tool the brief needs was available. grep/rg are hook-blocked, so text searches used awk. The covering tests came from an AST scan (§INSTRUMENTS). I did not use lore for the structure questions: `scripts/` is outside the graph (#507), and the targets were named exactly. That is a fallback to awk, and I am saying so. No friction to file.

## SETUP
- Scratch: `…/5e3e72cf-…/scratchpad/fix3`, made with `scripts/scratch_copy.sh`. After `git reset --hard && git clean -fd` the status was empty. The patch md5 was verified as `2c88b1a990d04c2383c36a9c8bbfb36a` before `git apply`, and it applied cleanly.
- HEAD `fb95d1f9b5e836d343af0658aec2815e02e33e3c`. That is docs-only past `60a369c`, as the brief says.
- `loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5e3e72cf-a647-4837-966a-5e40d72da932/scratchpad/fix3/loremaster/loremaster/__init__.py`, printed again by the probe under mutation.
- Admission: MemAvailable was 27.0–27.2 GiB at each launch. Every run used `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 … -n 8 --timeout=300`. There were no cap kills. The main tree is untouched except for this report.

## ITEMS

| # | item | chokepoint | receipt |
|---|---|---|---|
| 1 | Gate matcher (58 am-14 §1) | `PendingContractRegistry.entries_for(path)`, the ONE per-path registry lookup. `partition_mypy` admits iff `any(entry.admits(e) for _b, entry in entries_for(e.path))`. `entry_for` is **deleted**: awk over the whole tree found its only caller was `partition_mypy`. The one remaining mention is a prose comment in `scripts/test_pending_contract_gate.py` describing the old defect. That file is not mine, and the comment is correct history. | `test_shared_path_error_is_expected_when_ANY_entry_admits_it[named-by-second-entry]` went RED→GREEN. The control and `[named-by-first-entry]` stayed GREEN. Targeted `scripts/test_pending_contract_gate.py` + fates + retry_seam: **749 passed, 1 failed** (the 58 lease red). The two named am-14 orphans are gone from currency. |
| 1b | D-1 sibling (lead ruling) | The same `entries_for`. In `transcript_self_destruct_findings`, "unsymboled" is now judged against the UNION of every entry's `missing_symbols` for the path, not the entry's own. Every per-path registry read in the gate now goes through `entries_for`. I checked the rest by awk: `partition_pytest` uses the `registered_paths` union, and the liveness/exists/no-errors legs iterate entries and do no per-path lookup. | Fix-up probe (§INSTRUMENTS), same probe, two gates. **Base gate:** `SHARED … SELF-DESTRUCT: lorerunes/tests/test_posture.py declares 1 unsymboled 'attr-defined' error(s); 2 observed` and `CONTROL` has no finding. **Build gate:** `SHARED expected 3 unexpected 0` with **no finding**; `CONTROL expected 2 unexpected 0` with no finding. There is no pin (deviation 1). |
| 2 | F-12(a) edit 1 | `principals._dispatch_migrate_governed` except-tuple now reads exactly `(PrincipalStoreError, KeepStoreError, SurrealStoreError, ValueError)`. | `test_exhaustion_fates.py::…::test_every_non_derived_site_has_a_row_and_every_row_a_site` went RED→GREEN. `test_every_row_is_matched_to_ITS_site_by_the_caught_expression` stayed GREEN; it is the `ast.unparse` order pin. |
| 3 | am-37 §8.2 F-a rider | The stdout receipt line, built from `result.unsound_sender_messages`. It appends ` unsound_sender_messages=<int>` **iff the field is measured** (not `None`). The stderr sentence and exit 0 are untouched. See §FORKS F-2. | No pin asserts the receipt bytes (awk over test files for `already_migrated=` / `scanned=` render strings: none). This is am-37's STOP condition, checked, and it does not fire. Covered only by the declared-set run: the a28c CLI render pins stayed GREEN. |
| 4 | am-37 §8.3 DRY | `loremaster.governed.group_all_count(result, *, noun) -> int`. ONE policy: `[]` → 0; `[{"count": int}]` → the int; anything else raises `SurrealStoreError`. `principals._group_all_count` is **deleted**. `principals._scope_count` (the query owner) and the message leg's leftover read both call it through the lazy `from loremaster.governed import …` idiom principals already uses for governed. | §MUTATION: both callers moved. Findings, messages and diff were not touched (routed to 64b). |

## RUNS (declared set: fix2's 72 files ∪ AST covering scan, 74 files, md5 `00b6f2687c0a545e491f0fbda8e470fd`, fixed before any run)
- The covering scan added `test_findings_closeout_64b.py` and `scripts/test_gate_currency.py` beyond fix2's 72. The fix-up's three test files were already in them.
- ONE tree, swapped by `cp` from content backups (`base_content.md5` verified before the swap), with a fresh `PYTHONPYCACHEPREFIX` per state.

| run (2026-09-30Z) | tree | passed | failed | skipped | collected | wall |
|---|---|---|---|---|---|---|
| base 01:17 | fix-up patch | 5926 | 341 | 18 | 6285 | 10m37s |
| **build 01:28** | **+ my 3 files** | **5928** | **339** | 18 | 6285 | 10m56s |

Transitions, from `junit_transitions.py` (§INSTRUMENTS):
```
collected base 6285 build 6285 only-base 0 only-build 0
{'passed->passed': 5926, 'failed->failed': 339, 'skipped->skipped': 18, 'failed->passed': 2}
RED->GREEN loremaster.tests.test_exhaustion_fates.TestTheRegistryIsTheAdjudicationBothWays::test_every_non_derived_site_has_a_row_and_every_row_a_site
RED->GREEN scripts.test_pending_contract_gate::test_shared_path_error_is_expected_when_ANY_entry_admits_it[named-by-second-entry]
```
- **GREEN→RED: 0.**
- Base 341 reconciles with fix2's 340: +2 fix-up intended reds, −1 walker pin that the fix-up turned green.
- Remaining 339 by owner (`red_owners.py`, file → `pending_contracts.yaml` bound):
  - **packet-64b-i: 272**: comms_footer 81, governed_substrate 34, mcp_server 28, findings_migrate 28, findings_classes 27, findings_governance 24, findings_scope_domain 24, findings_schema 17, findings_system_writer 9.
  - **packet-58: 60**: r2_rulings 27, r3_tiers 16, r3_am6 8, r4_lease_fates 4, forgery_door_sweep 3, blocks_edge 1, exhaustion_fates 1 (the lease `logs-error-class` row).
  - **both bounds: 7**: r3_cas_seam 4, r4_state 3.
  - **UNOWNED: 0.** The script first printed "UNOWNED 8" for `loremaster/tests.py`, a classname-parse artifact for class-less tests. Listed individually, all 8 are `test_reanchor_58_r3_am6.py::test_P6_*`, which is registered under packet-58 at `pending_contracts.yaml` (entry `loremaster/tests/test_reanchor_58_r3_am6.py`).

## CURRENCY (build tree, `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`, verbatim, owner prose elided with […] only inside the one very long owner line)
```
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (owner: packet 58 […]) · packet-64b-i-contract (owner: packet 64b-i […])
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it would pass.
CURRENCY   : FAIL — claimed but never run: pytest
EXIT 1
```
- **RED_ORPHANED count: 0.** The fix-up measured `typecheck RED_ORPHANED — 2 residual(s)` (the two `_run_guarded` lines). They are now admitted by 64b-i's entry, and no SELF-DESTRUCT line appears.
- `pytest NOT_RUN` and the exit 1 come only from `--legs`, which the brief mandates. The fix-up's run showed the same.
- `uv run ruff check .` gives `All checks passed!`.
- mypy has 0 unexpected errors, so my three production files add none.

## MUTATION (sharing proven: change the ONE policy, and both callers move)
- The mutation: in `governed.group_all_count`, the empty branch `return 0` became `return 7`.
  - It landed; `diff` printed `706c706 < return 0 / > return 7`.
  - Backup `cp -a`, then restore, then `cmp` against `build_content/governed.py`: RESTORED byte-exact.
- Probe `probe_group_all_sharing.py` (§INSTRUMENTS). It runs each caller's REAL body; only the driver `run_query` and the leg's non-count collaborators are faked.

| state | `_scope_count(empty)` | `_migrate_message_owner.unsound_sender_messages` (empty leftover) | `scanned` |
|---|---|---|---|
| unmutated | 0 | 0 | 1 |
| **mutated** | **7** | **7** | **8** (the `already` read moved too) |
| restored | 0 | 0 | 1 |

Both 63c call sites move with the one policy. There is no private copy left: awk finds no `_group_all_count` in `principals.py`.
- Bound: no existing test pins `unsound_sender_messages`'s value (awk over the test tree: zero hits). The leftover caller is covered by this probe, not by a suite pin.

## DUAL (removed / replaced behaviour, adjudicated)
| removed / replaced | adjudication |
|---|---|
| `PendingContractRegistry.entry_for`: first match wins, `None` for an unregistered path | **dropped-deliberately** (58 am-14 §1: first-match was the hidden "one path, one bound" constant). An unregistered path is **preserved-with-pin**: `entries_for` returns `[]`, so `any()` is False and the error is UNEXPECTED. The existing single-entry / unregistered tests in `test_pending_contract_gate.py` stay GREEN. |
| `partition_mypy` single-entry admission | **preserved-with-pin**: for one entry, `any` over one equals the old check. The am-14 §1 control pins that the union did not become "path admits anything". |
| unsymboled count against the entry's OWN symbols | **dropped-deliberately** (lead ruling D-1). For a single-entry path the union equals its own symbols, so behaviour is identical there. There is **no pin for the shared case** (deviation 1). |
| `principals._group_all_count` | **replaced by `governed.group_all_count`, policy byte-identical**: the same three predicates and the same raised message (`the {noun} read answered a … without an integer \`count\` — nothing was migrated`). The literal `"count"` became `_GROUP_ALL_COUNT_KEY`. The empty→0 branch is covered by existing tests through `_scope_count` (e.g. `test_a_none_scope_count_is_reported_over_a_dirty_memory_table`, GREEN). |
| `_scope_count`'s read | **preserved**: same statement, same noun, same label. Only the reader it calls moved. `test_findings_migrate_64b.py`'s `_scope_count` call-graph reference still resolves. |
| except `SurrealConnectionError` in `_dispatch_migrate_governed` | **dropped-deliberately** (am-37 §6 F-12(a) / §8.1). It is subsumed by the base `SurrealStoreError`. Every other store fault, including `TxnContentionExhaustedError`, now prints to stderr and exits 1 instead of producing a traceback. The fates row pins it. |
| receipt line bytes | **preserved** for the memory and agent tables (their field is `None`, so nothing is appended). The **message table gains** ` unsound_sender_messages=N` (am-37 §8.2 rider). There is no byte pin, as checked above. |

## FORKS (both readings; the pick stated)
- **F-1: "`governed._scope_count`".** No such symbol exists (awk on `governed.py`).
  - Reading A (picked): am-37 §8.3 means `principals._scope_count`, "fail-closed since §6 F-12(b)", which is exactly what fix2 built there. It keeps its QUERY and delegates the READ. It was not deleted, because it owns a statement rather than a policy, and `test_findings_migrate_64b.py` keys a call-graph check on its name.
  - Reading B: it means `governed.report_unmigrated_governed_rows`, the only count reader in `governed.py`. That function is TOLERANT, not fail-closed, so it does not match §8.3's description. It is listed in §FLAGS F-1 instead.
- **F-2: rendering a `None` count.** am-37 says "a typed count beside `scanned`/`backfilled`/`already_migrated`".
  - Reading A (picked): append `unsound_sender_messages=<int>` iff measured. The message table always renders it, 0 included. Memory and agent render nothing, because `None` is the field's "not measured", and serving a count key for an unmeasured set is the over-claim the trust law forbids.
  - Reading B: always append, printing `unsound_sender_messages=None` on memory and agent. That keeps the line shape uniform but puts a non-int after `=` where scripts parse ints.
  - Lead's call. It is a one-line change either way.
- **F-3: signature.** am-37 writes `group_all_count(result) -> int`. I kept the required keyword `noun`, which names the read in the raised message (fix2's behaviour). Dropping it would lose the teaching prose. The routed 64b callers will pass their own noun.

## DRY
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `governed.group_all_count` | none this round. fix2 ran `lore_search("read a SELECT count() GROUP ALL result into an int count helper")` (fix2 §DRY), and am-37 §8.3 names the home. | `findings.FindingLedger._extract_group_count` (tolerant) plus the known copies | **EXTENDED `principals._group_all_count`**: moved to the ruled home and made public. Nothing new was written. |
| `PendingContractRegistry.entries_for` | n/a: `scripts/` is not in lore's graph (#507); awk | `entry_for` (first-match) | **REPLACES `entry_for`** (deleted). am-14 §1 dictates its body. |

## FLAGS (surfaced for the operator; not handled here)
- **F-1: am-37 §8.3's "the idiom is read in FIVE places" is an undercount.**
  - Awk for `GROUP ALL` / `.get("count"` / `_COUNT_KEY` across `loremaster/loremaster/**` (2026-09-30, at `fb95d1f`+fixup) finds these beyond the five, all TOLERANT (`… or 0` / `.get("count", 0)` / `if rows else 0`):
    - `governed.report_unmigrated_governed_rows`: malformed → 0 → **the forgotten-backfill alarm stays silent**;
    - `principals.PrincipalStore` delete path, `owned_count`: malformed → 0 → **the SF-63-5 refuse-while-owning guard is bypassed and the delete dangles owned governed rows (fail-OPEN)**;
    - the same method's `cascaded` count, an audit number only;
    - `tasks.TaskLedger`'s `_extract_group_count` (`tasks.py`, `int(rows[0].get(_COUNT_KEY, 0))`);
    - `store/surreal.py` (`_COUNT_KEY`);
    - `index/surreal_manifest.py` (`_COUNT_ALIAS` reads). This one is **not verified in detail**.
  - These are two populations conflated into one count (the #102/#120 class).
  - Why I did not fix them: the first two are 63-lineage and fail-open, but fixing them changes an alarm or guard's failure mode (raise vs 0 at boot or on delete), which is a design decision. They are also outside the brief's named two copies.
  - The exact fix, if ruled: each becomes `group_all_count(result, noun=…)`. A malformed count then raises `SurrealStoreError`. For the boot alarm, decide whether boot should fail or log.
  - **CLASS:** "every GROUP ALL count read goes through the one reader". **SIBLINGS TRIED:** the two ruled. **NOT TRIED:** the six above. Recommend routing them with 64b's findings/messages/diff step, or ruling the two fail-open ones now.
- **F-2: D-1's fix has no pin** (deviation 1). The class is "unsymboled is judged per path-union". A generated shared-path unsymboled test beside §3a is the missing instrument. It needs a test author, so it should route to the next gate-touching contract.
- **F-3: an adjacent latent case, not probed live.** Two entries on ONE path that both carry an `unsymboled_codes` allowance for the SAME code would each count the same unsymboled errors, so each allowance's `count` must equal the path total. Today no real path has even one allowance on a shared path (fix-up §SIBLING), so this has no reach. It is surfaced, not fixed.

## BACKUP (HEAD `fb95d1f9b5e836d343af0658aec2815e02e33e3c`; scratchpad `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5e3e72cf-a647-4837-966a-5e40d72da932/scratchpad/`)
| file | md5 | content |
|---|---|---|
| `builder-63c-i-a-fix3.full.patch` | `5a1d411c19a59efd5972695bb4b1635c` | `git diff --binary HEAD` = fix2 + tests + mine. `git apply --cached --check` on HEAD: OK. |
| `builder-63c-i-a-fix3.delta.patch` | `abbb0eddc97f41d557ba67a645e246b9` | Mine only, over the fix-up patch, 3 files, +89/−45, built against a temp index of HEAD + `2c88b1a9`. `--check` on HEAD + fix-up: OK. |
| `backup_changed/governed.py` | `cbe762025e736fe1aa780597d81c8603` | `cp -a` |
| `backup_changed/principals.py` | `12e23aae5c3699a2c260e17ec413b5f7` | `cp -a` |
| `backup_changed/pending_contract_gate.py` | `1dcdfadfbf22a4a44c41d647032e3061` | `cp -a` |
| `base_content/*` (pre-edit, `base_content.md5`) | governed `e57f0ef6…`, gate `4651686a…`, principals `ffbb7e46…` | the fix-up base of the same 3 files |
| `declared_fix3.txt` | `00b6f2687c0a545e491f0fbda8e470fd` | the 74-file set |
| `runs/{base,build}.{log,xml}`, `runs/currency_build.log` | — | raw receipts |

## INSTRUMENTS (pasted verbatim, per brief-base §1)
The scripts are also in the scratchpad: `cover_scan.py`, `junit_transitions.py`, `red_owners.py`, `probe_group_all_sharing.py`, and the fix-up's `probe_shared_unsymboled.py`, which is extracted verbatim from `REPORT-fixup-tests-63c-i-a.md` §INSTRUMENTS.

`probe_group_all_sharing.py`:
```python
"""Sharing-by-MUTATION probe (builder-63c-i-a-fix3, 2026-09-30): do BOTH 63c callers of the GROUP ALL
count policy move when governed.group_all_count's policy changes?  Callers exercised END TO END (their
real bodies; only the driver seam `principals.run_query` and the leg's non-count collaborators faked):
  (1) principals._scope_count            -> its return value
  (2) principals._migrate_message_owner  -> result.unsound_sender_messages (the leftover read)
Prints loremaster.__file__ as the provenance receipt. Run once per tree state (unmutated / mutated)."""
import asyncio
from types import SimpleNamespace

import loremaster
import loremaster.principals as principals

print("loremaster.__file__ =", loremaster.__file__)

ANSWERS = {  # noun -> the driver's answer
    "governed scope count": None,  # filled per call below (none=True vs none=False share the noun)
    "governed message-owner backfill": [],
    "governed message-owner leftover count": [],  # EMPTY group -> the policy's "empty" branch
}
calls = []


async def fake_run_query(*, noun, statement, **_):
    calls.append(noun)
    if noun == "governed scope count":
        # the unmigrated read must be non-zero so the leg reaches the leftover read; `already` is EMPTY
        return [{"count": 1}] if "IS NONE" in statement else []
    return ANSWERS[noun]


async def fake_operator(_store):
    return SimpleNamespace(email="op@example.invalid")


class FakeKeepStore:
    async def get_or_create_keyed(self, **_):
        return SimpleNamespace(id="keep:probe")


principals.run_query = fake_run_query
principals._message_leg_refusal = lambda *_a, **_k: None
principals.resolve_operator_principal = fake_operator
handle = SimpleNamespace(acquire=None, drop=None, url="ws://probe.invalid")


async def main():
    scope_empty = await principals._scope_count(handle, "memory", none=False)
    result = await principals._migrate_message_owner(
        handle, FakeKeepStore(), object(), object(), object(), table_defined=True
    )
    print(f"caller1 _scope_count(empty GROUP ALL) = {scope_empty}")
    print(f"caller2 _migrate_message_owner.unsound_sender_messages (empty leftover) = "
          f"{result.unsound_sender_messages} (scanned={result.scanned})")
    print("driver reads observed:", calls)


asyncio.run(main())
```

`cover_scan.py` (AST covering-test scan). Symbols scanned: `_scope_count, _group_all_count, group_all_count, _dispatch_migrate_governed, migrate-governed, migrate_governed, MigrateGovernedResult, entry_for, entries_for, partition_mypy, transcript_self_destruct_findings, PendingContractGate, unsound_sender_messages`:
```python
import ast, sys
from pathlib import Path
root = Path(sys.argv[1]); symbols = set(sys.argv[2].split(","))
hits = {}
for path in sorted(list(root.glob("*/tests/**/*.py")) + list(root.glob("scripts/test_*.py")) + list(root.glob("skills/*/tests/*.py"))):
    try: tree = ast.parse(path.read_text())
    except SyntaxError: continue
    found = set()
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Name): names = [node.id]
        elif isinstance(node, ast.Attribute): names = [node.attr]
        elif isinstance(node, ast.alias): names = [node.name.split(".")[-1], node.asname or ""]
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            found |= {s for s in symbols if s in node.value}
        found |= symbols & set(names)
    if found and path.name.startswith("test_"):
        hits[str(path.relative_to(root))] = sorted(found)
for p, s in hits.items(): print(p, " ".join(s))
```

`junit_transitions.py`:
```python
import sys
import xml.etree.ElementTree as ET
from collections import Counter
def outcomes(path):
    result = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        node = f"{case.get('classname')}::{case.get('name')}"
        tags = {child.tag for child in case}
        result[node] = "failed" if tags & {"failure", "error"} else "skipped" if "skipped" in tags else "passed"
    return result
base, build = outcomes(sys.argv[1]), outcomes(sys.argv[2])
print("collected base", len(base), "build", len(build), "only-base", len(base.keys() - build.keys()),
      "only-build", len(build.keys() - base.keys()))
print(dict(Counter(f"{base[n]}->{build[n]}" for n in base.keys() & build.keys())))
for label, a, b in (("GREEN->RED", "passed", "failed"), ("RED->GREEN", "failed", "passed")):
    for n in sorted(x for x in base.keys() & build.keys() if base[x] == a and build[x] == b):
        print(label, n)
```

`red_owners.py`. Known quirk: a class-less test's classname parses to `<pkg>/tests.py`. I resolved those by listing them (§RUNS).
```python
import sys
import xml.etree.ElementTree as ET
from collections import Counter
import yaml
reg = yaml.safe_load(open(sys.argv[2]))
owners = {}
for bound in reg["bounds"]:
    for entry in bound["files"]:
        owners.setdefault(entry["path"], set()).add(bound["id"])
tally = Counter()
for case in ET.parse(sys.argv[1]).getroot().iter("testcase"):
    if {c.tag for c in case} & {"failure", "error"}:
        path = case.get("classname").rsplit(".", 1)[0].replace(".", "/") + ".py"
        tally[(path, "+".join(sorted(owners.get(path, {"UNOWNED"}))))] += 1
for (path, owner), n in sorted(tally.items(), key=lambda kv: kv[0][1]):
    print(f"{n:4d} {owner:45s} {path}")
print("TOTAL", sum(tally.values()), "UNOWNED", sum(n for (p, o), n in tally.items() if o == "UNOWNED"))
```

There are 339 failing tests in the declared set outside this wave's scope (measured 2026-09-30 at `fb95d1f`+fixup+this build): 272 packet-64b-i, 60 packet-58, 7 owned by both. All are registered bounds, and the base run has every one of them red too. This report does not examine them further.

---

## §10 — round 2: am-37 §10 delta (`cfaf793`), same scratch `fix3`, 2026-09-30 01:45–02:10Z

**SUMMARY (round 2):**
- **State:** done-with-deviations.
- **(a)** `owned_count` is fail-CLOSED through `governed.group_all_count`.
- **(b)** Today a rejected count is LOUD, not silent (stderr + exit 1). A malformed count now takes that same fate, so no ERROR-log change was needed. Receipts below.
- **(c)** The receipt line always renders `unsound_sender_messages=`, and `None` is rendered explicitly.
- Declared set: see §10 RUNS. Currency RED_ORPHANED 0; ruff clean. The sharing mutation covers all 4 callers.
- **Deviation:** my lore identity was retired at round-1 exit, so it cannot re-register (terminal). No lore_comms traffic this round; the report and the native message carry it.
- **Decision needed:** **§10 FLAG R2-1**. `lore-adm delete`'s `_dispatch` does not catch `SurrealStoreError`, so the "store fault reaches the operator through the base-class catch" premise in §10.1(a) is false for that verb.

### §10 ITEMS
| item | chokepoint | receipt |
|---|---|---|
| (a) `PrincipalStore.delete` `owned_count` | `owned_count = group_all_count(await self._query(…), noun="governed owned-row count")`. The raw answer is read directly; the old `_as_rows` step, which turned a non-list into `[]` and so into 0, is gone from this read. | Probe part B, base → build: `delete MALFORMED: PROCEEDED cascaded=0 executed=True` → `SurrealStoreError executed=False`; `delete NON-LIST: PROCEEDED … executed=True` → `SurrealStoreError executed=False`. Unchanged: `delete REJECTED: SurrealStoreError executed=False` and `delete OWNS 2: PrincipalOwnsGovernedRowsError executed=False`. **STOP check:** no pin feeds delete a wrong shape and expects it to proceed. The awk hits are `test_agent_governance_63c_i_a.py`, `test_fixwave_a19b_63c_i_a.py` and `test_principal_delete_governed_63a.py`, which the AST covering scan added (the 75th file): 6/6 GREEN on base and on build. |
| (b) `governed.report_unmigrated_governed_rows` | `count = group_all_count(result, noun="governed unmigrated-scope count")`. | **Today's fate, read first.** The only production caller is `principals._dispatch_report_unmigrated` (the `report-unmigrated` verb; awk finds no boot caller — the other hits are a comment and a `_txn` docstring). Its catch includes `SurrealStoreError`. `run_query` logs a rejection under `governed.unmigrated_count.rejected` and raises `SurrealStoreError`. So a REJECTED count gives stderr + exit 1, which is loud. Probe (base): `report-unmigrated REJECTED: exit=1 stderr='lore-adm: governed unmigrated-scope count rejected…'`; `MALFORMED: exit=0 stdout='report-unmigrated --table memory: unmigrated=0'`, the silent alarm. Probe (build): `MALFORMED: exit=1 stderr='lore-adm: the governed unmigrated-scope count read answered a list without an integer \`count\` — nothing was decided from it'`, the same fate as REJECTED. Today's fate is not silent, so the §10.1(b) rider (log ERROR with `exc_info`) does not trigger. Residual: a malformed answer has no engine detail to log, so it produces no `…rejected` log record; the stderr line carries it. |
| (c) F-2 receipt | The receipt f-string renders every field unconditionally: `scanned={…} backfilled={…} already_migrated={…} unsound_sender_messages={…}`. A `None` prints as `None`. This is one convention for the whole line. The line had no other omission-rendered field; `table_defined=False` has its own separate sentence, as before. | No byte pin (awk, round 1). The declared-set run covers the a28c CLI render pins. |
| shared message | `group_all_count`'s raised tail changed from "nothing was migrated" to **"nothing was decided from it"**, because the reader now also serves a delete guard and an alarm, where "migrated" would be false prose. | awk over the test tree for `nothing was migrated` / `without an integer`: 0 pins. |

### §10 RUNS (declared set unchanged, 74 files md5 `00b6f268…`, re-run on the fix-up base vs build r2; +1 file run separately)
| run (2026-09-30Z) | tree | passed | failed | skipped | collected | wall |
|---|---|---|---|---|---|---|
| base2 01:45 | fix-up patch (`base_content.md5` verified before the swap) | 5926 | 341 | 18 | 6285 | 11m07s |
| **build2 01:56** | **+ round 1 + §10** (`build_content_r2.md5`) | **5928** | **339** | 18 | 6285 | 11m18s |
| extra, base / build | `test_principal_delete_governed_63a.py` (AST scan: new covering file for the delete path) | 6 / 6 | 0 / 0 | — | 6 | ~4s |

Transitions (`junit_transitions.py`, `runs/transitions2.txt`):
```
collected base 6285 build 6285 only-base 0 only-build 0
{'passed->passed': 5926, 'failed->failed': 339, 'skipped->skipped': 18, 'failed->passed': 2}
RED->GREEN loremaster.tests.test_exhaustion_fates.TestTheRegistryIsTheAdjudicationBothWays::test_every_non_derived_site_has_a_row_and_every_row_a_site
RED->GREEN scripts.test_pending_contract_gate::test_shared_path_error_is_expected_when_ANY_entry_admits_it[named-by-second-entry]
```
- **GREEN→RED 0.** The extra delete-path file is `passed->passed 6`.
- The remaining 339 reds are the same set as round 1, with the same owners (64b-i 272 / 58 60 / both 7). `red_owners.py` printed "UNOWNED 8" again, the classname-parse artifact. Listed, they are `test_reanchor_58_r3_am6` ×8, registered under packet-58. **UNOWNED 0.**

### §10 CURRENCY (build r2, verbatim, owner prose truncated at 160 columns)
```
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (owner: packet 58 (supersede re-anchor + task guarded-append shell + finding 130 +
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it wo
CURRENCY   : FAIL — claimed but never run: pytest
EXIT 1
```
**RED_ORPHANED 0.** The `pytest NOT_RUN` line and the exit 1 come only from `--legs`, as in round 1. `uv run ruff check .` gives `All checks passed!`.

### §10 MUTATION (sharing across all FOUR callers, including the new `owned_count` caller)
The mutation is the same as round 1: `governed.group_all_count`'s empty branch `return 0` → `return 7`.
- It landed (`diff`: `707c707`).
- Content backup `cp -a`, then restore, then `cmp` against `build_content/governed.py`: **RESTORED byte-exact**. The mutation was run twice (the second time to capture caller (4)'s printed line), and each run was restored byte-exact.
- Probe `probe_group_all_r2.py`: each caller is given an EMPTY GROUP ALL answer.

| caller | unmutated (build r2) | **mutated** | restored |
|---|---|---|---|
| (1) `principals._scope_count` | 0 | **7** | 0 |
| (2) `_migrate_message_owner.unsound_sender_messages` | 0 | **7** | 0 |
| (3) `PrincipalStore.delete` `owned_count` (NEW) | `PROCEEDED cascaded=0 executed=True` | **`PrincipalOwnsGovernedRowsError executed=False: … they own 7 governed memory row(s)`** | `PROCEEDED …` |
| (4) `governed.report_unmigrated_governed_rows` (NEW) | 0 | **7** (plus the WARNING `governed.unmigrated_rows: 7 memory row(s) carry a NONE scope …`) | 0 |

**Sharing is proven for all four 63c callers.** Receipts: `runs/probe_r2_{base,build,mutated}.txt` in the scratchpad.

### §10 BACKUP (HEAD `fb95d1f9b5e836d343af0658aec2815e02e33e3c`; scratchpad as round 1)
Round 2 SUPERSEDES the round-1 patches.

| file | md5 | content |
|---|---|---|
| `builder-63c-i-a-fix3.r2.full.patch` | `f5897681430ad5e7c5d719dab12815bd` | `git diff --binary HEAD` = fix2 + tests + round 1 + §10. `--check` on HEAD: OK. |
| `builder-63c-i-a-fix3.r2.delta.patch` | `4516d9b1919826eb6b21658c96e79a7a` | Mine (round 1 + §10) over the fix-up patch `2c88b1a9`, 3 files, +101/−51. `--check` on HEAD + fix-up: OK. |
| `backup_changed_r2/governed.py` | `e3b4531fb8f36482ed8d5bed9069a5a3` | `cp -a` |
| `backup_changed_r2/principals.py` | `938f7a246938a79ec609d3263871583d` | `cp -a` |
| `backup_changed_r2/pending_contract_gate.py` | `1dcdfadfbf22a4a44c41d647032e3061` | `cp -a` (unchanged since round 1) |

### §10 INSTRUMENT
`probe_group_all_r2.py` lives in the scratchpad and is pasted here verbatim:
```python
import argparse
import asyncio
import contextlib
import io
from types import SimpleNamespace

import loremaster
import loremaster.governed as governed
import loremaster.principals as principals
from loremaster.store._txn import SurrealStoreError

print("loremaster.__file__ =", loremaster.__file__)
calls = []


async def fake_run_query(*, noun, statement, **_):
    calls.append(noun)
    if noun == "governed scope count":
        return [{"count": 1}] if "IS NONE" in statement else []
    return []


async def fake_operator(_store):
    return SimpleNamespace(email="op@example.invalid")


class FakeKeepStore:
    async def get_or_create_keyed(self, **_):
        return SimpleNamespace(id="keep:probe")


principals.run_query = fake_run_query
principals._message_leg_refusal = lambda *_a, **_k: None
principals.resolve_operator_principal = fake_operator
handle = SimpleNamespace(acquire=None, drop=None, url="ws://probe.invalid")
executed = []


async def fake_execute_transaction(*_a, **_k):
    executed.append(1)


principals.execute_transaction = fake_execute_transaction


def principal_store(owned_answer):
    store = object.__new__(principals.PrincipalStore)

    async def get_by_email(_email):
        return SimpleNamespace(id="principal:p1")

    async def table_exists(_table):
        return True

    async def query(statement, _params=None):
        if "FROM keep" in statement:
            return []
        if "FROM memory" in statement:
            if isinstance(owned_answer, Exception):
                raise owned_answer
            return owned_answer
        return []  # the principal_key cascade count

    store.get_by_email, store._table_exists, store._query = get_by_email, table_exists, query
    store._ensure_connection, store._drop_connection, store._url = None, None, "ws://probe.invalid"
    return store


async def delete_outcome(owned_answer):
    executed.clear()
    try:
        cascaded = await principal_store(owned_answer).delete(email="p@example.invalid")
        return f"PROCEEDED cascaded={cascaded} executed={bool(executed)}"
    except Exception as error:  # noqa: BLE001 - the probe reports the class
        return f"{type(error).__name__} executed={bool(executed)}: {str(error)[:90]}"


async def report_verb(answer):
    async def governed_run_query(**_):
        if isinstance(answer, Exception):
            raise answer
        return answer

    governed.run_query = governed_run_query
    fake_store = SimpleNamespace(_ensure_connection=None, _drop_connection=None, _url="ws://probe.invalid")

    async def noop():
        return None

    fake_store.ensure_ready, fake_store.close = noop, noop
    principals.build_principal_store = lambda _config: fake_store
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = await principals._dispatch_report_unmigrated(argparse.Namespace(table="memory"), None)
    return f"exit={code} stdout={stdout.getvalue().strip()!r} stderr={stderr.getvalue().strip()[:110]!r}"


async def main():
    print("== A: sharing (EMPTY GROUP ALL answer to every caller)")
    print("  (1) _scope_count =", await principals._scope_count(handle, "memory", none=False))
    result = await principals._migrate_message_owner(
        handle, FakeKeepStore(), object(), object(), object(), table_defined=True
    )
    print(f"  (2) message leg unsound_sender_messages = {result.unsound_sender_messages}")
    print("  (3) delete owned_count:", await delete_outcome([]))
    saved = governed.run_query

    async def empty(**_):
        return []

    governed.run_query = empty
    print("  (4) report_unmigrated_governed_rows =", await governed.report_unmigrated_governed_rows(handle, "memory"))
    governed.run_query = saved
    rejected = SurrealStoreError("governed unmigrated-scope count rejected by the engine (probe)")
    print("== B: fate, REJECTED vs MALFORMED")
    print("  report-unmigrated REJECTED :", await report_verb(rejected))
    print("  report-unmigrated MALFORMED:", await report_verb([{"cnt": 1}]))
    print("  delete REJECTED :", await delete_outcome(SurrealStoreError("principal query rejected (probe)")))
    print("  delete MALFORMED:", await delete_outcome([{"cnt": 1}]))
    print("  delete NON-LIST :", await delete_outcome("oops"))
    print("  delete OWNS 2   :", await delete_outcome([{"count": 2}]))


asyncio.run(main())
```

### §10 DUAL
| removed / replaced | adjudication |
|---|---|
| delete: `_as_rows(...)` then `int(rows[0].get("count", 0)) if rows else 0` (malformed or non-list → 0 → delete proceeds) | **old-bug, not re-pinned** (am-37 §10.1(a): fail-OPEN on SF-63-5). Preserved: an empty group → 0 → proceeds, and `{"count": N>0}` → refuses. |
| `report_unmigrated_governed_rows`: malformed → `0` → exit 0 `unmigrated=0` | **old-bug** (the silent-alarm class). Preserved: an empty group → 0, and a well-formed count, including the WARNING when > 0. |
| receipt: omit `unsound_sender_messages` when `None` (my round-1 pick) | **dropped-deliberately**: am-37 §10.2 refuses omit-when-None. |
| raised tail "nothing was migrated" | **dropped-deliberately**: false prose on the new delete and alarm callers. No pin. |

### §10 FLAGS
- **R2-1 (decision needed): `lore-adm delete` renders a store fault as a TRACEBACK.**
  - `principals._dispatch` catches `(PrincipalStoreError, PrincipalKeyStoreError, SurrealConnectionError, ValueError)`, not `SurrealStoreError`.
  - `PrincipalStore._query` raises raw `SurrealStoreError` on an engine rejection. The new malformed-count raise is the same class.
  - Both therefore reach the operator as a traceback. The delete IS refused (fail-closed, probe `executed=False`), so §10.1(a)'s property holds. But §10.1(a)'s "reaches the operator through §6 F-12's base-class catch" is true only for `migrate-governed`, not for this verb.
  - This is pre-existing for REJECTED counts and not new to this delta.
  - Widening `_dispatch` to `SurrealStoreError` would make it a new exhaustion catch site: its caught closure includes `TxnContentionExhaustedError`. That reddens `test_exhaustion_fates` until a `REGISTERED_FATES` row lands. That is a test-side edit, and the same shape as F-12(a), so I did NOT do it. Route: one `principals.py` edit plus one fates row, in one commit.
  - **CLASS:** "every `lore-adm` verb's store fault → stderr + exit 1". **SIBLINGS TRIED:** `migrate-governed` (base catch) and `report-unmigrated` (base catch). **NOT TRIED:** every other `_dispatch_*` verb's tuple (`_dispatch_keep` documents that it catches `KeepStoreError` + `SurrealConnectionError` deliberately, FR-2 D1).
- The rest of the GROUP ALL sweep stays with 64b §DRY, per am-37 §10.1: the `cascaded` count, `tasks`, `store/surreal.py`, `surreal_manifest`, findings, messages and diff. I did not touch them.
