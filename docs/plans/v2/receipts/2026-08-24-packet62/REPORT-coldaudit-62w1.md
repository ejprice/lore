# REPORT-coldaudit-62w1 — COLD AUDIT (REFUTE), packet 62 Wave 1 (`agent.owner_principal` owns-edge store foundation)

- `brief-base v14 read`
- `brief project v7 read`
- store reference read: `docs/reference/surrealdb-31-capabilities.md` — §1.1 (FIELD `OVERWRITE`
  / INDEX `IF NOT EXISTS`; an OVERWRITE index rebuilds on boot), §1.4 (a NEW field on a
  POPULATED table must be `option<>`; a DEFAULT does not rescue a legacy row), §1.5 (the
  OVERWRITE-index boot-crash is HNSW-dim-specific, NOT plain scalar — R1), §1.6 (virgin-DB
  blind spot / dirty-store idiom), §2 (`record<t>` links do NOT auto-clean; `SELECT *` OMITS an
  unset `option<>` column). Cited, never re-transcribed.

## CAPABILITY CHECK (tool honesty §4)
Everything the brief demanded was reachable: spike-surreal test store `ws://127.0.0.1:18000`
was OPEN (systemd `active`, image `v3.2` = 3.2.4); `scripts/scratch_copy.sh` ran and asserted
provenance; lore tools loaded via `ToolSearch "+lore"`; pytest / ruff / typecheck ran; live
probes ran against the throwaway store. **One friction (adversary hit it too):** bare
`rm -rf /tmp/…` is sandbox-denied here — I used a fresh scratch path (`/tmp/cold62w1a`) instead
of pre-cleaning. No mission impact.

---

## SUMMARY BLOCK

- **VERDICT: GO.** Every gate passes on MY re-run; all 3 load-bearing mutation proofs
  discriminate on-point; the dirty-store migration holds LIVE on 3.2.4 with a firing positive
  control; no assertion was weakened; the delete logic is unchanged; both docstrings are
  ground-truth-accurate.
- **Gates (MY counts, HEAD `87d11d6`):** contract **50 passed / 0 failed**; blast radius (8
  suites) **660 passed / 0 failed**; `scripts/typecheck.sh` **all 7 legs OK**; ruff on the 3
  packet-62 files **clean**. Repo-wide `ruff check .` is **RED (exit 1)** — 4× F841 ALL in
  `scripts/probe_dnd_multitag_schema.py`, **none touch a packet-62 file** (finding #424,
  external contamination — see residual R-b).
- **Mutation proofs (independent, provenance-asserted scratch `/tmp/cold62w1a`,
  `loremaster.__file__` INSIDE the scratch):** reference build 50/0 (positive control); MUT1
  required→3 RED (the §1.4 not-poison control + option-wrap + ownerless); MUT2 OVERWRITE
  index→1 RED (offline pin only; live re-appliability GREEN → empirically confirms R1); MUT3
  cascade→2 RED (both dangle pins). Each reds the RIGHT pins for the RIGHT reason.
- **Live dirty-store migration (3.2.4, spike `:18000`):** PASS — a legacy agent written under
  the OLD slice survives the OVERWRITE field-add, reads `owner_principal` None, is NOT
  write-poisoned (unrelated UPDATE succeeds), and a new owned agent is writable. Positive
  control: a REQUIRED-field variant POISONS with the exact #107 signature (`Expected
  record<principal> but found NONE`).
- **AgentRegistry read safety:** confirmed by CONSTRUCTION (`_row_to_agent` hand-picks kwargs;
  no `Agent(**row)` / `model_validate(row)` anywhere) AND LIVE — both an UNSET and a
  deliberately-STAMPED `owner_principal` row round-trip through `get_agent`/`roster` with no
  `extra="forbid"` blow-up. Safe now and for the future item-2 stamp.
- **#423 docstring:** 4-link enumeration matches ground truth (I counted the links live: exactly
  4 unique `(field,table)` `record<principal>` links); dispositions accurate against the ACTUAL
  delete code (cascade / refuse-while-keeping / dangle / dangle).
- **R1 docstring:** corrected claim is TRUE (plain-index OVERWRITE re-applies cleanly, §1.5 —
  MUT2 confirmed the live control stays GREEN); assertion body untouched (git-diff: docstring-only).
- **Removed-behavior DUAL (P8d):** the delete logic is UNCHANGED (only the docstring moved);
  nothing dropped. Corpse sweep clean — no test pins the OLD agent field-set.
- **Packages considered:** none — no mechanism specified (I graded a contract+build that route
  the field/index through the existing in-house `_define_field`/`_plain_index` emitters). My
  probes (`probe_dirtystore_62.py`, the registry-read probe, `mutate62.py`) are auditor scratch
  tooling, pasted verbatim in §Instruments so they survive the disposable scratch tree.
- **Reuse ledger:** none — I introduced no reusable production symbol.
- **Graded:** `87d11d6` · HEAD-at-report: `87d11d6` · SAME. (Working tree carries only the
  3-file build diff + the four `REPORT-*.md`; production `principals.py`/`surreal_schema.py`
  byte-identical to what the adversary graded.)
- **Decisions-needed:** none blocking. #424 (repo-wide ruff RED) needs a lead/owner
  adjudication before any commit that runs the full ruff gate — but it is NOT a wave-1 defect
  (residual R-b).

---

## What I graded (scope)

The uncommitted Wave-1 build in the working tree at HEAD `87d11d6` — packet-62 FINAL SCOPE LINE
items **1 & 4 ONLY** (the store foundation):
- **`surreal_schema.py`** (production): appends `("owner_principal", "option<record<principal>>",
  "")` to `_AGENT_FIELD_SPECS`, a module constant `_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS`, and the
  non-unique `owner_principal` index in `_agent_statements()`; two docstrings updated.
- **`principals.py`** (production): `PrincipalStore.delete` docstring ONLY (#423) — delete logic
  UNCHANGED.
- **`test_agent_owns_principal_schema.py`** (test): the R1 docstring correction ONLY —
  assertion body untouched.

Items 2/3/5/6 (register-time stamp, `stamp_owner` seam, `agent_of`, the anti-injection reach
pin, prose retirement of the 48 guard) are LATER waves and are correctly NOT in this build.

---

## Gate re-runs (MY OWN counts — not relayed)

| gate | command | MY result |
|---|---|---|
| contract | `pytest tests/test_agent_owns_principal_schema.py tests/test_principal_keys_schema.py -p no:randomly -q` | **50 passed in 5.93s** |
| blast radius (8 suites) | `pytest -n auto` over agent_registry, comms_schema, schema_fold_coverage, surreal_schema, principal_delete_cascade_61, audit_schema, keeps_schema, principals_schema | **660 passed in 23.37s** |
| typecheck | `bash scripts/typecheck.sh` | **all 7 legs OK** (lorerunes/lorescribe/loresigil/loremaster[236 files]/skills/docs·eval/scripts + shellcheck) |
| ruff scoped | `ruff check` on the 3 packet-62 files | **All checks passed!** |
| ruff repo-wide | `ruff check .` | **RED, exit 1** — `Found 4 errors`, all F841 in `scripts/probe_dnd_multitag_schema.py:{434,439,445,450}` |

Emitted DDL (live introspection of the shipped `generate_agent_ddl()`):
```
DEFINE FIELD OVERWRITE owner_principal ON agent TYPE option<record<principal>>
DEFINE INDEX IF NOT EXISTS agent_owner_principal ON agent FIELDS owner_principal
```
Agent index names `['agent_session_status','agent_name','agent_owner_principal']` — all unique.

## Mutation proofs (independent — scratch `/tmp/cold62w1a`, provenance ASSERTED)

`loremaster.__file__ = /tmp/cold62w1a/loremaster/loremaster/__init__.py` (I mutated/tested the
SCRATCH build, never the original tree — #140). Each mutation applied from pristine content,
contract subset run, then restored; final state restored to the shipped build.

| variant | contract result | pins that redded (verified, not relayed) |
|---|---|---|
| **reference (correct)** | **50 / 0** | — (positive control: harness distinguishes right from wrong) |
| **MUT1** field `record<principal>` (required, no `option<>`) | **3 / 47** | `…does_not_write_poison_the_legacy_row` (§1.4), `…is_option_wrapped_record_principal`, `…ownerless_reads_owner_principal_as_none` |
| **MUT2** owner index → `DEFINE INDEX OVERWRITE …` | **1 / 49** | OFFLINE `…index_is_IF_NOT_EXISTS_never_OVERWRITE` **only**; the live `…safely_re_appliable` stayed GREEN (empirically confirms R1 / §1.5) |
| **MUT3** delete injects `DELETE agent WHERE owner_principal=…` | **2 / 48** | both `TestPrincipalDeleteDanglesTheOwnedAgentBackLink` pins (single + MANY/∀) |

Counts and reddened-pin identities match the builder's proof table AND the adversary's variants
1/4/8 exactly.

## Live dirty-store migration (3.2.4, spike `ws://127.0.0.1:18000`) — the #107/#131 refute frontier

A green virgin-DB suite does not prove a migration. I constructed a DIRTY store (a legacy agent
row written under the OLD slice) and applied the SHIPPED `generate_agent_ddl()` OVERWRITE
field-add over it (`probe_dirtystore_62.py`, self-checking, exit 0):
```
A1 legacy row survived migration: True
A2 legacy reads owner_principal None: True
A3 unrelated UPDATE of legacy row succeeded (not poisoned): True
A4 new owned agent writable + reads owner back: True (principal:p9)
B1 required-field build POISONS the legacy UPDATE (control fires): True
   signal: InternalError: Couldn't coerce value for field `owner_principal` of `agent:legacy`:
           Expected `record<principal>` but found `NONE`
```
Leg B is the POSITIVE CONTROL: the same dirty-store setup with a REQUIRED (non-`option<>`)
field-add DOES poison — so leg A's clean result is a real negative, not a blind instrument.

## AgentRegistry read safety (the `extra="forbid"` refute frontier)

`AgentRegistry` reads via `SELECT *` (agents.py:542/552/963/1018) but `_row_to_agent`
(agents.py:1037) builds `Agent(id=…, name=…, …)` from HAND-PICKED `row.get(...)` kwargs — it
never does `Agent(**row)` and there is **no `Agent(**row)` / `.model_validate(row)` anywhere in
agents.py** (grep: empty). So an `owner_principal` column in the row is structurally unable to
reach the `extra="forbid"` constructor. Confirmed LIVE (registry-read probe, exit 0): an UNSET
row round-trips (`SELECT *` omits the NONE column, §2), and a deliberately-STAMPED
`owner_principal` row ALSO round-trips through `get_agent`+`roster` with no blow-up (the field is
simply ignored). Safe for this wave AND for the future item-2 stamp — stronger than the contract
author's C-DEF claim, which only needed the unset case.

## #423 docstring correctness (ground-truthed)

Live count of `record<principal>` links across every `generate_*_ddl` surface → exactly FOUR
unique `(field, table)` pairs: `(principal, principal_key)`, `(keeper, keep)`,
`(actor_principal, audit)`, `(owner_principal, agent)`. (7 raw hits collapse to 4 because
`generate_ddl` folds audit/keep/principal_key — but NOT `agent`, which is exactly the reach point
the exact-set pin's `_all_schema_ddl` broadening addresses.) The #423 docstring's dispositions
are accurate against the ACTUAL delete transaction (which DELETEs only `principal_key` + the
`principal` row): `principal_key.principal` = children-first CASCADE; `keep.keeper` =
REFUSE-WHILE-KEEPING (verified: the delete raises `PrincipalHasKeepsError` before any DELETE);
`audit.actor_principal` + `agent.owner_principal` = DANGLE-TOLERATED (the delete touches neither
table). The builder's Deviation 1 (writing `keep.keeper` as REFUSE, not "cascade") is a genuine
correctness improvement over the brief's shorthand, not a semantic drift.

## Removed-behavior DUAL + corpse sweep

- **DUAL (P8d):** the delete logic is byte-for-byte unchanged (git diff: `principals.py` is
  docstring-only; the `execute_transaction` body still DELETEs `principal_key` then `principal`).
  Nothing the old code did was dropped — the only change is prose.
- **R1 test docstring:** git diff confirms the assertion body (`for _ in range(2): await
  _apply_agent_ddl(connection)`) is untouched — docstring-only, as the builder claimed.
- **Corpse sweep (bare patterns, agent table):** no test pins the OLD agent field-set. The only
  hits are a comment (`test_comms_schema.py:479`) and unrelated pydantic model field-sets
  (`FleetRoster` / `AgentRosterMember` in `test_agent_registry.py`) — and both suites pass
  UNMODIFIED in my 660/0 run, so the field-add reddens nothing.

---

## Residuals — individual verdicts (NONE blocking the wave)

- **R-a (trivial, = adversary R3):** the builder & contract reports say the new file has "16
  tests"; collect-only shows **17** (5+3+4+3+2). The declared-RED node LIST (13) is correct and
  fully reproduced. Prose-only miscount.
- **R-b (external gate contamination — NOT a wave-1 defect, but needs adjudication before a
  full-gate commit):** repo-wide `ruff check .` is RED (exit 1) with 4× F841, ALL in
  `scripts/probe_dnd_multitag_schema.py:{434,439,445,450}` (unused `await _explain(...)`
  results). NONE touch a packet-62 file; the packet-62 build is ruff-clean. Finding #424 exists
  (filed by `builder-62w1`). ⚠ **Two metadata errors in #424/the builder report, both immaterial
  to the verdict, flagged for accuracy:** (1) they say the F841 were "introduced by commit
  c6d2cd0" — `git blame` shows all four came from **`e11e381`** ("chore(probe): D&D multi-tag
  schema verification on 3.2.4"), a concurrent D&D session; c6d2cd0 is a docs commit. (2) The
  spawn brief called it "an UNTRACKED, UNOWNED file" — it is git-TRACKED (committed at e11e381).
  The contamination itself (4× F841 in that one dnd file) is exactly what #424 says. Per the
  brief I do not fail the wave on it; I DO flag that the repo-wide ruff gate is red and #424 must
  be owned/fixed (trivial: `del` the unused results or assign `_`) before any commit that runs
  the full ruff gate — the file is unrelated to packet 62 but sits in the same tree.
- **R-c (= adversary R2):** the dangle pins assert the observable OUTCOME (delete succeeds ∧
  agent survives ∧ link stale), not "delete never touches agent." A build that benignly touched
  an agent row while preserving row+link would pass. Not a plausible builder error and not a
  violation of the ruled properties (R3.2). Note only — the pinned properties are the right ones.
- **R-d (= adversary R4):** `_all_schema_ddl`'s reach covers `generate_*_ddl` surfaces only —
  currently vacuous (I confirmed via live introspection that no `record<principal>` DDL exists
  outside a `generate_*_ddl`). An honest stated bound with a live re-open trigger, not a gap.

---

## VERDICT: GO

I re-ran every gate (contract 50/0, blast 660/0, typecheck OK, ruff-scoped clean), independently
reproduced all three load-bearing mutation proofs in a provenance-asserted scratch tree (each
discriminates on-point, positive control 50/0), proved the dirty-store migration holds on a LIVE
3.2.4 store with a firing positive control, confirmed the `option<>` field never poisons a legacy
row and never reaches the `extra="forbid"` Agent model (unset OR stamped), confirmed the #423 and
R1 docstrings against ground truth, and confirmed the delete logic is unchanged with a clean
corpse sweep. The only red gate is external contamination (#424) outside packet-62 scope. No
wrong build I can name survives this contract, and no assertion was weakened. This is a strong,
shippable Wave-1 build. The one thing the lead must action before a full-gate commit is #424
(repo-wide ruff), which is not a packet-62 defect.

---

## Instruments (pasted verbatim — scratch trees are disposable, brief-base §1)

**`probe_dirtystore_62.py`** — live dirty-store migration + poison positive control on 3.2.4:
```python
# (run from repo loremaster/ dir; imports tests/_surreal_harness; NEVER :18500)
import asyncio, sys
from datetime import UTC, datetime
sys.path.insert(0, "tests")
import loremaster
from _surreal_harness import (PRODUCTION_DIM, connect_admin, drop_database, make_env, run, unique_database)
from loremaster.store import surreal_schema
from surrealdb import RecordID
AGENT = surreal_schema.AGENT_TABLE; PRINCIPAL = surreal_schema.PRINCIPAL_TABLE; _OWNER = "owner_principal"
def _statements(ddl): return [s.strip() for s in ddl.split(";") if s.strip()]
def _old_slice():
    kept = [s for s in _statements(surreal_schema.generate_agent_ddl()) if _OWNER not in s]
    return ";\n".join(kept) + ";\n"
def _required_slice():
    return surreal_schema.generate_agent_ddl().replace("option<record<principal>>", "record<principal>")
async def _create_legacy(conn, agent_id):
    now = datetime.now(UTC)
    await run(conn, f"CREATE type::record('{AGENT}', $id) CONTENT $c",
        {"id": agent_id, "c": {"name": f"legacy_{agent_id}", "session": "old_sess", "role": "worker",
         "status": surreal_schema._AGENT_STATUS_ACTIVE, "registered_at": now, "heartbeat_at": now}})
async def main():
    print(f"loremaster.__file__ = {loremaster.__file__}"); ok = True
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM); conn = await connect_admin(env)
    try:
        await run(conn, _old_slice()); await _create_legacy(conn, "legacy")
        await run(conn, surreal_schema.generate_agent_ddl())
        row = (await run(conn, f"SELECT name, {_OWNER} FROM type::record('{AGENT}','legacy')"))[0]
        a1 = row["name"] == "legacy_legacy"; a2 = row[_OWNER] is None
        await run(conn, f"UPDATE type::record('{AGENT}','legacy') SET last_note = 'touched'")
        note = (await run(conn, f"SELECT last_note FROM type::record('{AGENT}','legacy')"))[0]
        a3 = note["last_note"] == "touched"
        now = datetime.now(UTC)
        await run(conn, f"CREATE type::record('{AGENT}','fresh') CONTENT $c",
            {"c": {"name": "fresh", "session": "new", "role": "worker", "status": surreal_schema._AGENT_STATUS_ACTIVE,
                   "registered_at": now, "heartbeat_at": now, _OWNER: RecordID(PRINCIPAL, "p9")}})
        fresh = (await run(conn, f"SELECT {_OWNER} FROM type::record('{AGENT}','fresh')"))[0]
        a4 = str(fresh[_OWNER]) == f"{PRINCIPAL}:p9"
        print("A1", a1, "A2", a2, "A3", a3, "A4", a4); ok = ok and a1 and a2 and a3 and a4
    finally:
        await conn.close(); await drop_database(env)
    env2 = make_env(database=unique_database(), dim=PRODUCTION_DIM); conn2 = await connect_admin(env2); poisoned = False
    try:
        await run(conn2, _old_slice()); await _create_legacy(conn2, "legacy"); await run(conn2, _required_slice())
        try: await run(conn2, f"UPDATE type::record('{AGENT}','legacy') SET last_note = 'x'")
        except Exception as e: poisoned = True; print("B1 signal:", type(e).__name__, str(e)[:120])
        print("B1 control fires:", poisoned); ok = ok and poisoned
    finally:
        await conn2.close(); await drop_database(env2)
    print("RESULT", "PASS" if ok else "FAIL"); return 0 if ok else 1
raise SystemExit(asyncio.run(main()))
```

**registry-read probe** — `owner_principal`-bearing row round-trips without `extra="forbid"`:
```python
import asyncio, sys
sys.path.insert(0, "tests")
import loremaster
from _surreal_harness import PRODUCTION_DIM, make_env, unique_database, connect_admin, run, drop_database
from loremaster.agents import AgentRegistry
from loremaster.store import surreal_schema as s
async def main():
    print("loremaster.__file__ =", loremaster.__file__)
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    reg = AgentRegistry(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    try:
        await reg.ensure_ready(); await reg.register("worker_one", session="sess_x", role="worker")
        a = await reg.get_agent("worker_one", session="sess_x"); unset_ok = a.name == "worker_one"
        admin = await connect_admin(env)
        await run(admin, f"UPDATE {s.AGENT_TABLE} SET owner_principal = type::record('{s.PRINCIPAL_TABLE}','pX') WHERE name = 'worker_one'")
        await admin.close()
        a2 = await reg.get_agent("worker_one", session="sess_x"); await reg.roster(session="sess_x")
        set_ok = a2.name == "worker_one" and not hasattr(a2, "owner_principal")
        print("UNSET", unset_ok, "SET", set_ok)
    finally:
        await reg.close(); await drop_database(env)
raise SystemExit(asyncio.run(main()))
```

**`mutate62.py`** — the 3 mutation proofs (run in the provenance-asserted scratch `/tmp/cold62w1a`):
edits (from pristine content each time): MUT1 `("owner_principal", "option<record<principal>>",
"")` → `("owner_principal", "record<principal>", "")`; MUT2 the `_plain_index(AGENT_TABLE,
f"{AGENT_TABLE}_owner_principal", _AGENT_OWNER_PRINCIPAL_INDEX_FIELDS)` append → a hand-written
`f"DEFINE INDEX OVERWRITE {AGENT_TABLE}_owner_principal ON {AGENT_TABLE} FIELDS owner_principal"`;
MUT3 inject `f"DELETE agent WHERE owner_principal = type::record('{PRINCIPAL_TABLE}', $pid);\n"`
before the `DELETE {PRINCIPAL_TABLE} … $email` line in `PrincipalStore.delete`'s
`execute_transaction`. Each: run `pytest tests/test_agent_owns_principal_schema.py
tests/test_principal_keys_schema.py -p no:randomly -q --tb=no -rf`, capture failed node ids,
restore. Reproduce: `./scripts/scratch_copy.sh /abs/dest` → drop `mutate62.py` at the scratch
root → `cd /abs/dest && uv run python mutate62.py`.
```
[REFERENCE] 0 failed / 50 passed
[MUT1] 3 failed / 47  → …does_not_write_poison_the_legacy_row, …is_option_wrapped_record_principal, …ownerless_reads_owner_principal_as_none
[MUT2] 1 failed / 49  → …index_is_IF_NOT_EXISTS_never_OVERWRITE  (live …safely_re_appliable stayed GREEN)
[MUT3] 2 failed / 48  → …dangles_them_ALL, …succeeds_and_the_agent_survives
```

Scratch tree `/tmp/cold62w1a` restored to the shipped build after the proofs (disposable per
`scratch_copy.sh`; the real tree was never touched — `git status` unchanged throughout).
