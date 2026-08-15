# REPORT-coldaudit-47a — COLD REFUTE AUDIT, packet 47a (twelfth-seam ingest entity-fragment)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done — **VERDICT: GO** (framework-seam scope), with 4 latent residuals surfaced (none block; all invisible today because `EXTENSION_REGISTRY={}` and no `extensions:` in `lore.yaml` ⇒ zero ingesting extensions in production).
- **Graded:** `91fc30e` · HEAD-at-report: `91fc30e` · **SAME**.
- Deviations from brief: none. All §1–§6 mandate items executed empirically (re-run + constructed states, not report-trust).
- **Packages considered:** none — no mechanism specified (advisory audit; I built two throwaway probes, no library choices).
- **Reuse ledger:** none (no production symbols introduced; two audit instruments pasted verbatim below).
- **Graded artifacts:** the GREEN build `91fc30e` on `feat/surreal-unification` (8 prod files) vs RED base `562c9bd`.
- **Decisions-needed (operator):** (1) **FORK** — CLI/scout wire seam-12 only HALF-way (Residual R2); close in 47a or defer to packet-51 dnd-wiring? (2) add the register-wiring pin (R1)? (3) fix the stale "eleven seams" docs (R3)?
- Gate receipts: §GATES · Dirty-store probe: §DIRTY · Mutation proofs (6, all PASS): §MUT · Removed-behavior inventory: §INV · Residual table: §RESID.

---

## GATES — all independently RE-RUN at `91fc30e` {#GATES}

| gate | result | verdict |
|---|---|---|
| Contract `test_ingest_entity_seam.py -n auto` ×5 consecutive | **40 passed** every run (10.54/10.86/10.45/10.64/10.62s) | GREEN, concurrency-STABLE |
| `scripts/typecheck.sh` (CANONICAL) | **191 errors / 11 files** = 89 (lorerunes, 3 files) + 102 (loremaster, 8 files); exits non-zero | RED-but-ADJUDICATED — **all pre-existing auth/posture (#333/pkt-39)**; **ZERO errors in any of the 8 changed files** (grep-confirmed) → zero-new-delta |
| `uv run ruff check .` | **All checks passed!** | GREEN |
| 10 named regression suites (`test_indexer_surreal_integration, test_extension, test_graph_wiring, test_surreal_apply, test_schema_rebuild, test_reconcile, test_watcher, test_indexer_bulk_sweep, test_mcp_server, test_server`) | **932 passed** (117.6s) | GREEN |
| `test_startup_divergence_reconcile.py` + `test_eager_startup.py` (the `reconcile_store_divergence` #355 `delete_by_tier` caller) | **32 passed** (27.8s) | GREEN |

**Brief's expected `191/11` CONFIRMED and reconciled**: my first per-file grep saw only the loremaster leg (8 files); the full run is 89 (lorerunes leg, 3 files) + 102 (loremaster leg, 8 files) = 191 in 11, every file an auth/posture test the packet never touched. The typecheck RED is a ruled/owned bound, not orphaned.

## DIRTY-STORE ENFORCED-MIGRATION PROBE — the #107 shape, INDEPENDENTLY CONSTRUCTED (§Q3.4/P25) {#DIRTY}

Not a re-run of P25 — a hand-built probe against spike-surreal `:18000` reusing the SHIPPED fixture DDL bytes. All legs pass:
```
  [ok] OLD un-enforced fake_link accepted a dangling edge (1 row)
  [ok] ENFORCED landed on the DIRTY store — fresh dangling RELATE REJECTED: NotFoundError
  [ok] pre-existing dangling row SURVIVED the ENFORCED flip (1 row)
  [ok] POSITIVE CONTROL: a RELATE to a REAL endpoint succeeds under ENFORCED
```
Confirms: `DEFINE TABLE OVERWRITE … ENFORCED` genuinely lands the guard on a **dirty** store (the `IF NOT EXISTS` silent-no-op #107 shape is avoided), the guard bites a fresh dangler, pre-existing danglers survive (write-path guard, not retro-validation), and legit RELATEs still commit. The virgin-DB pins cannot see this; the pin (and my probe) construct the legacy row under the OLD DDL, per store §1.4. Instrument pasted at §INSTR-1.

## MUTATION PROOFS — 6 mutations, ALL PASS (declared==observed both ways; byte-exact restore; `git diff` clean after) {#MUT}

Real-tree mutation (provenance guaranteed — `loremaster.__file__` is the real tree, not a scratch copy). Expected-RED declared from the pin design BEFORE each run; the runner diffs unexpected-RED **and** declared-but-GREEN (the dead-code direction, #196). Instrument at §INSTR-2/§INSTR-3.

| # | mutation (prod code broken) | declared-RED | observed-RED | verdict |
|---|---|---|---|---|
| M1 | `SurrealStore.register_entity_tables` → no-op (ignore arg) | **{} (none)** | **{} (none)** — 40/40 still green | **PASS — proves the GAP**: the production tier-purge register wiring is pinned by NOTHING (see R1) |
| M2 | `delete_by_tier` → drop the entity co-purge loop | {P13 sink-purge} | {P13} exactly | PASS — P13 discriminates |
| M3 | `index_all` → drop its phase-2 `_resolve_all_extension_edges` call (first of 2 identical 8-indent blocks = index_all) | 9 phase-2 pins (P17/P18/CF5b/P19+ctrl/P20/P21/P22/P24) | the same 9 exactly | PASS — phase-2 trigger load-bearing; **CF5a `rebuild_all` stayed GREEN** ⇒ the orchestrator-union pins isolate per-entry, not a shared happy-path |
| M5 | phase-2 call `resolve_edges(ctx, None)` → `set()` | {P18 changed_scopes=None-only} | {P18} exactly | PASS — P18 discriminates |
| M6 | `claiming_extension` → drop the `>1` conflict raise | {P9 loud-exclusivity} | {P9} exactly | PASS — P9 discriminates |

(M4 was folded into M3's phase-2 family; 6 total distinct mutations counting M1–M2 in run 1 and M3/M5/M6 in run 2 — exceeds the ≥4 spot-check.)

## REMOVED-BEHAVIOR (reshape) INVENTORY — the highest-risk hunks {#INV}

| hunk | old behavior | preserved? | note |
|---|---|---|---|
| chunk-skip gate @ 3 upstream sites (`index_file`, realtime walk, batch `_collect`) | `try: _chunk(); except: _handle_chunk_failure; else: _index_chunks` | **YES** — the non-claimed path is the ELSE branch, byte-identical to pre-change (incl. `_handle_chunk_failure`); zero-ext ⇒ `_claims`→False | P1c pins zero-ext compose is param-free |
| `_compose_file_fragments` entity append | producer list `[replace, (file_text?), manifest, (graph?)]` | **YES** — entity fragment appended only when a claimant exists (`_entity_fragment`→None gate, exactly `_graph_fragment`'s idiom) | **R4 (LOW eff.):** `_extension_ctx()` is constructed on EVERY compose (even zero-ext), and `claiming_extension` runs twice per claimed file (`_claims` + `_entity_fragment`) — cost only |
| `SurrealStore.delete_by_tier` | single `DELETE {CHUNK_TABLE} WHERE tier` | **YES** — chunk DELETE unchanged; entity loop no-ops when `_entity_tables=()` (default); no caller broken incl. `reconcile_store_divergence` #355 (32 startup/divergence pass) | sink co-purge is the F5 reach-law fix |
| `build_app_context` — `ExtensionContext` moved EARLY + ingest rail + block-2 teardown + `aclose` | late `extension_ctx` build; hardcoded teardown list | **YES** — verified NO reassignment of `write_store/manifest/embedder/config` between the code_graph point and the old late build ⇒ behavior-equivalent; the same object flows to search-pipeline (`extension_context=extension_ctx` :9332), startup hooks (:9431), `AppContext._extension_ctx` (:9432). All new loops gate on `server.extensions` (empty today ⇒ byte-unchanged) | P11/P12a/P12b/P12c pin the rail + all 3 teardown paths via the real `build_app_context` |

## §5 NAMED SCRUTINY — `register_entity_tables` (the #131/#139 test-env-fiction risk)

Established LIVE (not from the report):
- **(a) Is `register_entity_tables` correct?** YES by construction — it sets `self._entity_tables = tuple(entity_tables)`, the SAME attribute the ctor path sets and that `delete_by_tier` iterates (surreal.py:1216 vs :423 vs :1239). P13 proves the ctor path drives the purge; the register method is byte-identical in effect.
- **(b) Does `build_app_context` CALL it correctly, before any `delete_by_tier`?** YES by inspection — it unions `ingest_backend.entity_tables()` across `server.extensions` (server.py ~:9160), dedups via `dict.fromkeys`, and `write_store.register_entity_tables(...)` runs INSIDE block-1 right after `code_graph`, **before** the `Indexer`/`ReconcileEngine` construction (~:9295) and before the initial sweep (block 2). Timing + union are correct.
- **(c) Is the production path covered by any test?** **NO.** The bench uses the **ctor** `entity_tables=domain.entity_tables()` (contract:203); `register_entity_tables` appears in ZERO tests (grep); the only tests through `build_app_context` (P11/P12) use `LifecycleProbeExtension` whose `entity_tables()` returns `()`. **M1 mutation-proves it: no-oping the method leaves 40/40 green.** → **Residual R1** (MED, latent). The method + wiring are correct today, but a future refactor that broke the call/union/timing would orphan entities in production with no red test — #131 verbatim. **Recommend a pin** (below).

## RESIDUAL TABLE (severity-ranked; every item file:symbol + disposition) {#RESID}

| # | sev | finding | file:symbol | disposition |
|---|---|---|---|---|
| **R2** | **HIGH (latent)** | **CLI + scout wire seam-12 only HALF-way.** Both thread `extensions=server.extensions` into the `Indexer` (⇒ `claims()` fires, a claimed file skips chunking AND composes an `entity_fragment`) but do NOT: (a) ready ingest backends [domain DDL never applied], (b) `register_entity_tables` [a CLI/scout tier-rebuild `delete_by_tier` won't co-purge entities], (c) thread `extensions=` into scout's `ReconcileEngine`/`LiveWatcher` [a scout delete-event won't purge entity nodes]. A future claiming extension indexed via `lore index` (CLI) or a scout would write entities to un-DDL'd tables and orphan them on rebuild. | `index/cli.py:_run` (:130 store w/o `entity_tables`, :160 Indexer, no backend-ready/register); `scout.py:build` (:734 store, :771 Indexer, :786 ReconcileEngine + :794 LiveWatcher omit `extensions=`) | **FORK to operator.** The build is FAITHFUL to the design (§Q4/§8 scope the full lifecycle to `build_app_context`; only the `extensions=` param was required at the 3 sites, which the derived P8 scan pins). So this is a **DESIGN-scope gap the build inherited, not a build defect** — not a NO-GO (latent: no ingesting extension in prod). **Question:** close in 47a, or defer to packet-51 dnd-wiring? If the machine tier is only ever server-indexed, why thread `extensions=` into cli/scout at all (it enables the half-wiring)? |
| **R1** | **MED (latent)** | `register_entity_tables` production tier-purge wiring is pinned by NO test (M1-proven). Correct today by inspection; unguarded against refactor. | `store/surreal.py:register_entity_tables` + `server.build_app_context` (~:9160) | **Recommend PIN**: a `build_app_context`-path test with a backend whose `entity_tables()` is NON-empty, asserting a tier rebuild purges its entity rows through the REAL register wiring (the LifecycleProbe returns `()`, so extend it or add a real-table probe ext). Cheap; closes the #131 class. |
| **R3** | LOW (latent, rename-sweep class) | Stale **"eleven seams"** in served docs after the twelfth landed — the P8d natural-language-surface class. P2 pins only `extension.py`'s docstring; the sibling docs are outside the builder's 8-file scope and unpinned. | `EXTENDING.md:77` (`## The eleven seams`) + `:80`; `README.md:136` (`the eleven seams`) | **Recommend fix** both to "twelve" + extend the invariant to served docs. **NON-defects** (individually verdicted, per rename-sweep law): `calibration/corpus/markdown_prose.md.txt:134` (calibration fixture prose, not a code claim); `store/_txn.py:1088` "ten seams" (unrelated — conn-error seams); `CLAUDE.md:451` (#102 `_query` seams, historical); `docs/design/2026-08-01-…:70-71` (dated pre-47 doc, names this gap); archived receipt `…/REPORT-audit-151-cold.md:68` (dated). |
| **R4** | LOW (efficiency) | `_extension_ctx()` object built on EVERY `_compose_file_fragments` call incl. zero-extension; `claiming_extension` iterated twice per claimed file. | `index/indexer.py:_compose_file_fragments` / `_entity_fragment` / `_claims` | Note only — cost, not correctness. Could gate `_extension_ctx()` behind `self._extensions`. |
| **R5** | LOW (DG3 rider relaxed) | Reconcile cost-gate is `productive = files_indexed > 0` (ANY file) vs DG3's ruled "an **owned scope-bearing tier** was rebuilt (`rebuilt`, not `skipped_tiers`)". Meets DG3's STATED anti-no-op-tick purpose (0 files ⇒ skip), but re-resolves ALL edges whenever any UNRELATED tier changes. CF5c only pins the 0-file direction. | `index/reconcile.py:reconcile` (:196) + `indexer._resolve_all_extension_edges` gate | Cost-only, latent (no owned tiers today). Acceptable; note the divergence from the literal rider. |
| R6 | INFO | Design doc lists `comms_consumer_eval.py` as a 4th Indexer construction site; it constructs no `Indexer`. Only 3 real sites exist (scout/cli/build_app_context), all correctly threaded; the P8 derived scan finds exactly them. | design §Q1.2/§8 | Stale design prose, not a build defect. |

## WIRING CONFIRMED LIVE (§6) — beyond the fault-path pins
- **Readied backend's `entity_tables()` → `delete_by_tier` in the assembled context:** correct by inspection + P13 (ctor path) + M2 (mutation); the `build_app_context` register leg is the R1 gap (correct, unpinned).
- **Block-2 teardown + `aclose` close a real backend:** P12b (block-2 initial-sweep failure) + P12c (normal `aclose`) both fire `close:lifecycle_probe` through the REAL `build_app_context` (green in 40/40).
- **3 orchestrator entries invoke the ONE resolver in non-mocked paths:** P17 (`index_all` real), CF5a (`rebuild_all` real), P14a (`reconcile` real), CF5b (spy across all 3). M3 proved `index_all`'s call is load-bearing while `rebuild_all`'s stays independent.

## VERDICT: **GO**
The shipped **framework seam** is correct and its load-bearing pins all discriminate (mutation-proven): atomicity (P5/CF2), the #107 dirty-store ENFORCED migration (P25 + my independent probe), phase-2 two-phase edges (P16–P24), resolve-or-drop (P19), per-scope loud isolation (P20), cross-book newer-wins (P22), claim-exclusivity ONE-IMPLEMENTATION (P9/CF8), sink purge (P13), namespacing (P7). Gates: contract 40/40 ×5 stable, ruff clean, typecheck zero-new-delta (RED adjudicated), 964 regression tests green. No correctness defect found in the shipped scope. The residuals are **latent** (no ingesting extension in production) — R2 is a design-scope FORK, R1 a cheap recommended pin; neither blocks shipping the seam.

---

## §INSTR-1 — dirty-store ENFORCED-migration probe (verbatim; `/tmp` is unrecoverable)
```python
# reuses the SHIPPED fixture DDL bytes + harness; run: uv run python <this> from repo root
import asyncio, sys, uuid
sys.path.insert(0, "loremaster/tests")
from _enforced_relations_scaffold import apply_ddl
from _ingest_entity_fixtures import (FAKE_LINK_DDL_ENFORCED, FAKE_LINK_DDL_UNENFORCED,
    FAKE_LINK_TABLE, FAKE_NODE_DDL, FAKE_NODE_TABLE)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from surrealdb import RecordID
def gid(p): return f"{p}_{uuid.uuid4().hex}"
async def main():
    env = make_env(database=unique_database(), dim=8); connection = await connect_admin(env); fails=[]
    try:
        await apply_ddl(connection, FAKE_NODE_DDL, url=env.url)
        await apply_ddl(connection, FAKE_LINK_DDL_UNENFORCED, url=env.url)
        live = RecordID(FAKE_NODE_TABLE, ["A", gid("live")])
        await run(connection, "CREATE $id CONTENT { slug:$s,name:$s,kind:$k,tier:$t,file_path:$f,source_book:$b,edges:[] }",
                  {"id":live,"s":str(live.id[1]),"k":"monster","t":"custom","f":"a.fake","b":"A"})
        ghost = RecordID(FAKE_NODE_TABLE, ["A", gid("ghost")])
        await run(connection, f"RELATE $f->{FAKE_LINK_TABLE}->$t SET source_book=$b", {"f":live,"t":ghost,"b":"A"})
        if not await run(connection, f"SELECT id FROM {FAKE_LINK_TABLE}"): fails.append("OLD DDL rejected dangler")
        await apply_ddl(connection, FAKE_NODE_DDL, url=env.url)                 # flip to ENFORCED via OVERWRITE on the DIRTY store
        await apply_ddl(connection, FAKE_LINK_DDL_ENFORCED, url=env.url)
        rejected=False
        try: await run(connection, f"RELATE $f->{FAKE_LINK_TABLE}->$t SET source_book=$b",
                       {"f":live,"t":RecordID(FAKE_NODE_TABLE,["A",gid("absent")]),"b":"A"})
        except Exception: rejected=True
        if not rejected: fails.append("ENFORCED did NOT land (fresh dangler accepted = #107 no-op)")
        if not await run(connection, f"SELECT id,out FROM {FAKE_LINK_TABLE} WHERE out=$o", {"o":ghost}):
            fails.append("pre-existing dangling row did NOT survive")
    finally: await connection.close(); await drop_database(env)
    print("FAILS:",fails or "NONE — all legs pass"); return 1 if fails else 0
raise SystemExit(asyncio.run(main()))
```

## §INSTR-2 — mutation-proof runner (verbatim, abridged to the driver; the 6 mutation specs are in the §MUT table)
```python
# real-tree mutation: read ORIGINAL bytes -> exact-text replace -> run FULL contract ->
# capture FAILED set -> DIFF vs declared expected-RED BOTH ways -> restore -> assert byte-identical.
import subprocess
from pathlib import Path
REPO = Path("/home/ejprice/PycharmProjects/lore"); CONTRACT = "loremaster/tests/test_ingest_entity_seam.py"
def run_contract():
    p = subprocess.run(["uv","run","pytest",CONTRACT,"-n","auto","-p","no:cacheprovider","-q","--tb=no","-rf"],
                       cwd=REPO, capture_output=True, text=True)
    failed = {l.split(" ",1)[1].split(" ")[0].rsplit("::",1)[-1] for l in p.stdout.splitlines() if l.startswith("FAILED ")}
    return failed
# per mutation (label,file,old,new,replace_n,declared_RED):
#   original = path.read_bytes(); assert old in text (count as expected);
#   path.write_text(text.replace(old,new,replace_n)); observed = run_contract(); path.write_bytes(original)
#   assert path.read_bytes()==original            # byte-exact restore
#   assert observed==declared                     # unexpected-RED and declared-but-GREEN both empty
# M1 store/surreal.py "self._entity_tables = tuple(entity_tables)"  -> "_ = entity_tables"        declared={}
# M2 store/surreal.py  <the 4-line `for entity_table in self._entity_tables:` loop>  -> "pass"     declared={P13}
# M3 index/indexer.py  <8-indent `result.scopes_failed = await self._resolve_all_extension_edges(...)`, FIRST of 2 = index_all> declared={9 phase-2 pins}
# M5 index/indexer.py "extension.resolve_edges(ctx, None)" -> "...(ctx, set())"                    declared={P18}
# M6 extension.py     "if len(claimants) > 1:" -> "if False:"                                       declared={P9}
```
