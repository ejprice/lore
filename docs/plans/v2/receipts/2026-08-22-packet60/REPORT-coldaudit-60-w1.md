# REPORT-coldaudit-60-w1

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done — verdict rendered.
- **Graded:** working tree at `b9e6335` + the UNCOMMITTED packet-60 wave-1 changes (`keeps.py` new; `surreal_schema.py`, `_enforced_relations_scaffold.py`, `test_enforced_relations.py`, `test_retry_seam.py`, `test_keeps_*.py` modified/new). · HEAD-at-report: `b9e6335` · SAME (auditing the uncommitted delta on this HEAD).
- **VERDICT: NO-GO (NARROW / prose-only).** The build is FUNCTIONALLY CORRECT — all gates green, all 14 independent live-store probes pass with positive controls, every Fork A–F + store-law clause verified. The single blocking class is **stale "RED STUB"-era prose in production + scaffold files** (5 sites) — the exact "natural-language surface whose consistency with code no gate checks" class (PKT-28 C1 / rename-sweep law). Fix the 5 prose sites (docs-only, exact edits below), re-confirm ruff/mypy, then commit. This is NOT a rebuild — the code, schema and behaviour are independently verified correct.
- **Deviations:** (1) Ran probes IN-PLACE against the working tree (not a `scratch_copy.sh` copy) because the code under audit is UNCOMMITTED — a scratch copy risks excluding the untracked `keeps.py` or the #140 poison; ran with an asserted `loremaster.keeps.__file__` receipt instead, and mutated NO file (probes only mint throwaway test DBs). (2) My first idle-gate-contract write clobbered `builder-60-w1`'s contract file; restored it immediately.
- **Packages considered:** none — no mechanism specified (audit only; the one instrument I built is the probe script, pasted verbatim in §5).
- **Reuse ledger:** none (no production symbols introduced).
- **Graded:** GO-blocking defects = 1 class (stale stub prose, 5 sites, LOW severity each, MUST-FIX-before-commit). Correctness/contract-gap defects = 0.
- **Decisions-needed:** the lead chooses the fix mechanism (self-apply the docs edit vs. one-shot fixer) — see §6.
- **Receipt pointers:** gate counts §2; diff-read §3; probe receipts §4 + verbatim instrument §5; defect list §6; residuals §7.

---

## 1. First actions / capability check
- Read `~/.claude/orchestration/brief-base.md` (v14) and `docs/reference/surrealdb-31-capabilities.md` (§0/§1.1/§1.4/§1.5/§1.7/§1.8/§2/§3/§4 — cited below, never re-transcribed).
- Registered on `lore_comms` (`coldaudit-60-w1`, role auditor, session pkt60, cadence ≤30m); claimed + `in_progress` task `80336866ad714b19b5056ea4802ebaf5`.
- lore index currency: `lore_index()` — watched root `/workspace` @ `feat/surreal-unification` / `b9e6335`, last_sync ~5m, files_failed 0. I relied on the ACTUAL files (git diff + Read), not graph-derived answers, so staleness of the index vs. the uncommitted tree does not bear on this verdict. lore tools used for helper-symbol lookups only.
- Tooling: full tool access; live spike TEST store `ws://127.0.0.1:18000` reachable (systemd `spike-surreal.service` active; container up 4d). Never touched `:18500`.

## 2. Gate re-runs (my own, passed-COUNTs from the tail)
| gate | command | result |
|---|---|---|
| pytest (scoped, `-n auto`) | `test_keeps_schema.py test_keeps_store.py test_enforced_relations.py test_blocks_edge.py test_retry_seam.py test_surreal_schema.py test_surreal_store.py` | **1301 passed, 1 warning in 34.59s** (exit 0) |
| mypy | `scripts/typecheck.sh` | **Success — 0 issues** across lorerunes/lorescribe/loresigil/loremaster(221)/skills/docs-eval/scripts + shellcheck (exit 0) |
| ruff | `uv run ruff check .` | **All checks passed!** (exit 0) |

- The lone pytest warning is a pre-existing `RuntimeWarning: coroutine '_empty_subscription' was never awaited` at `test_retry_seam.py:3216` — test-hygiene, unrelated to packet 60 (present in a scout live-subscription test).
- No "no tests ran" pipe-lie: the 1301 passed-count is in the pasted tail.

## 3. Production diff-read (refute frame) — every risky hunk, verified against Forks A–F + store law
All helper emitters verified by reading their source (`lore_get_symbol`), NOT by trusting the DDL string:
- `_define_field` → `DEFINE FIELD OVERWRITE …` ✓ (§1.1 FIELD row / #107).
- `_define_table` → `DEFINE TABLE IF NOT EXISTS … SCHEMAFULL` ✓ (§1.1 plain-table row / §1.7).
- `_define_relation_table(enforced=True)` → `DEFINE TABLE OVERWRITE member_of TYPE RELATION IN principal OUT keep ENFORCED SCHEMAFULL` ✓ (§1.1 RELATION row + §4 "Shape to ship").
- `_plain_index` → `DEFINE INDEX IF NOT EXISTS … FIELDS keeper` (non-unique) ✓; `_unique_index` → `… FIELDS in, out UNIQUE` (`IF NOT EXISTS`) ✓ (§1.1 INDEX row / §1.5 — never OVERWRITE an index).
- `_CHUNK_STRING_TYPE = "string"`; `_NON_EMPTY_STRING_ASSERT = "ASSERT string::len(string::trim($value)) > 0"` (trim-aware; skips on NONE for `option<>`, fires on present empty string) ✓.

| ruling | requirement | build | verdict |
|---|---|---|---|
| **A** | keeper = indexed `keep.keeper record<principal>` FIELD LINK; NO `keeps` edge | `_KEEP_FIELD_SPECS[0]=("keeper","record<principal>","")` + `_plain_index(keep,"keep_keeper",("keeper",))`; no `keeps` edge anywhere | ✓ |
| **B** | `name` `option<string>` non-empty-if-present; `created_at datetime DEFAULT time::now()`; `type` closed {project,team,session,dm} call-time-derived NO default; id=`ulid()` | fields exactly as ruled; `type` ASSERT derived at call time in `_keep_statements` from `_KEEP_TYPES`, NO `DEFAULT`; `create_keep` mints `str(ULID())` | ✓ |
| **C** | `member_of.rank` string `DEFAULT 'contributor'` ASSERT closed `{contributor}` call-time from `_KEEP_RANKS`; widen-safe | derived at call time in `_member_of_statements`; `_KEEP_RANKS=('contributor',)`, `_KEEP_RANK_CONTRIBUTOR='contributor'` | ✓ |
| **D** | create_keep AUTO-ADDS keeper to household at `contributor`, ATOMIC (one `execute_transaction`) | `compose(TxnFragment([CREATE keep, RELATE keeper->member_of->keep]))` → one `execute_transaction`; keeper resolved via composed `PrincipalStore.get_by_email` | ✓ (probe (a)) |
| **E** | a `dm` keep is JUST `type='dm'` + manual household; NO auto-create, NO 2-member cap | no comms coupling, no member-count cap; `dm` handled as an ordinary type | ✓ |
| **F** | `member_of` ENFORCED + UNIQUE(in,out); add idempotent; remove refuses keeper; set_rank trivial | ENFORCED+UNIQUE emitted; `add_household_member` check-first no-op; `remove_household_member` raises `KeeperLockoutError`; `set_rank` UPDATEs edge field | ✓ (probes (b),(d)) |

Store-law read-surface checks (refute):
- **§2 / attack-9 trap:** `get_keep` and `list_keeps_for_keeper` use the EXPLICIT `_KEEP_READ_PROJECTION = "id, keeper, type, name, created_at"` (never `SELECT *`), and map `name` via `_optional_str(row.get("name"))` → a NONE `option<>` reads back `None`, not a `KeyError`. `_row_to_membership` reads via `_MEMBER_OF_READ_PROJECTION`. ✓
- **§3:** create_keep is the ONLY multi-statement write and it rides `execute_transaction` (every-statement checked), never a lax `query()`. ✓
- **§4:** `list_household`/`_read_membership` read `member_of` as a PLAIN table (`WHERE out = $keep` / `WHERE in=$m AND out=$k`, endpoints bound as `RecordID`) — no arrow traversal. `list_keeps_for_keeper` filters the indexed `keeper` field. ✓
- **#102/#120:** `KeepStore._query` is named EXACTLY `_query`, delegates to shared `run_query` with `noun="keep query"` / `label="keep.query.rejected"` (matching the `test_retry_seam.py` registration added this wave — finding #397 contract-gap, already fixed). No hand-rolled retry/classification. Email→id resolution COMPOSES `PrincipalStore.get_by_email` (no cloned resolver). ✓
- **generate_ddl fold order:** `_keep_statements()` then `_member_of_statements()` folded AFTER `_principal_key_statements()` — `principal` before `keep` (keeper link target) before `member_of` (ENFORCED IN principal / OUT keep). ✓ (pinned by `test_member_of_is_declared_AFTER_{keep,principal}`).
- **Edge emitted IDENTICALLY by both paths** (`generate_keep_ddl` slice and `generate_ddl`): both consume the one `_member_of_statements()` emitter. ✓ (pinned by `test_BOTH_paths_emit_the_IDENTICAL_member_of_statement`).

## 4. Independent probe receipts (construct → observe, each with a POSITIVE CONTROL)
Instrument: `/tmp/coldaudit60_probe.py` (verbatim in §5). Ran in-place `uv run python`; **14/14 PASS**.
Provenance (proves which tree was probed): `loremaster.keeps.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/keeps.py`, `loremaster.__file__` and `surreal_schema.__file__` likewise in the working tree.

| probe | construct | observed | control |
|---|---|---|---|
| **(a) atomicity** | monkeypatch `_principals.get_by_email` → GHOST principal id; call `create_keep` | `SurrealStoreError` raised (ENFORCED refuses ghost IN endpoint) **AND keep count before=1 after=1** — CREATE rolled back with the RELATE | normal create adds exactly one row (before=1→after=2) |
| **(b) keeper-lockout** | `remove_household_member(keeper)` on a fresh keep | `KeeperLockoutError` raised; keeper still in household | non-keeper removal SUCCEEDS (member gone) |
| **(c) nameless round-trip** | `create_keep(type='dm')` then `get_keep` + `list_keeps_for_keeper` | both return `name is None`, no raise | a named keep in the SAME calls carries `name='hasname'` |
| **(d) ENFORCED live** | RELATE `member_of` to a non-existent keep | refused (`NotFoundError`) | RELATE to the real keep accepted |
| **(e) keeper index** | `EXPLAIN SELECT id FROM keep WHERE keeper=$p` | `IndexScan` present | `WHERE type=$t` EXPLAIN → `TableScan` (plan-inspection provably sees both; §4 traversal-trap escaped) |

The `store.transaction.rolled_back` log line emitted during probe (a) independently corroborates the rollback.

## 5. Verbatim instrument
Pasted in full (brief-base §1 — a `/tmp` path is unrecoverable). Run from repo root: `uv run python <this>`. Observed: **14/14 PASS**, exit 0.
```python
"""Cold-audit pkt60 independent probes — construct+observe against the LIVE spike
test store (ws://127.0.0.1:18000), NEVER :18500. Run in-place against the working
tree (the code under audit is UNCOMMITTED); provenance asserted by printing
loremaster.keeps.__file__. Each probe has a POSITIVE CONTROL."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime

import loremaster
import loremaster.keeps as keeps_mod
import loremaster.store.surreal_schema as schema_mod

sys.path.insert(0, "loremaster/tests")
from _surreal_harness import (  # noqa: E402
    PRODUCTION_DIM, connect_admin, drop_database, make_env, run, unique_database,
)
from loremaster.keeps import KeeperLockoutError, KeepStore  # noqa: E402
from loremaster.principals import Principal, PrincipalStore  # noqa: E402
from surrealdb import RecordID  # noqa: E402

KEEPER = "alice@example.com"
MEMBER = "bob@example.com"
results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


async def main() -> int:
    print("=== PROVENANCE ===")
    print("loremaster.__file__       :", loremaster.__file__)
    print("loremaster.keeps.__file__ :", keeps_mod.__file__)
    print("surreal_schema.__file__   :", schema_mod.__file__)

    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    principals = PrincipalStore(url=env.url, namespace=env.namespace,
                               database=env.database, user=env.user, password=env.password)
    store = KeepStore(url=env.url, namespace=env.namespace,
                      database=env.database, user=env.user, password=env.password)
    await principals.ensure_ready()
    await store.ensure_ready()
    for email in (KEEPER, MEMBER):
        await principals.create(email=email)
    admin = await connect_admin(env)

    async def keep_count() -> int:
        try:
            rows = await run(admin, "SELECT count() FROM keep GROUP ALL", {})
        except Exception:
            return 0
        return int(rows[0]["count"]) if rows else 0

    try:
        # (e) keeper index fires
        k = await store.create_keep(keeper_email=KEEPER, type="project", name="idx")
        keeper_row = await principals.get_by_email(KEEPER)
        assert keeper_row is not None
        keeper_bare = keeper_row.id.split(":", 1)[1]
        plan_keeper = await run(admin, "SELECT id FROM keep WHERE keeper = $p EXPLAIN",
                                {"p": RecordID("principal", keeper_bare)})
        plan_type = await run(admin, "SELECT id FROM keep WHERE type = $t EXPLAIN", {"t": "project"})

        def ops(plan: object) -> list[str]:
            out: list[str] = []
            def walk(n: object) -> None:
                if isinstance(n, dict):
                    for key in ("operator", "operation"):
                        v = n.get(key)
                        if isinstance(v, str):
                            out.append(v)
                    for c in n.values():
                        walk(c)
                elif isinstance(n, list):
                    for c in n:
                        walk(c)
            walk(plan)
            return out

        keeper_ops, type_ops = ops(plan_keeper), ops(plan_type)
        record("(e) keeper EXPLAIN is IndexScan", "IndexScan" in keeper_ops, f"ops={keeper_ops}")
        record("(e) POS-CONTROL type EXPLAIN is TableScan", "TableScan" in type_ops, f"ops={type_ops}")

        # (d) member_of ENFORCED rejects a dangling RELATE
        member_row = await principals.get_by_email(MEMBER)
        assert member_row is not None
        member_bare = member_row.id.split(":", 1)[1]
        ghost_keep = "ghostkeepdoesnotexist000000"
        dangling_refused = False
        try:
            await run(admin, "RELATE $m->member_of->$k",
                      {"m": RecordID("principal", member_bare), "k": RecordID("keep", ghost_keep)})
        except Exception as e:  # noqa: BLE001
            dangling_refused = True; detail = type(e).__name__
        else:
            detail = "ACCEPTED (dangling edge written — ENFORCED not live!)"
        record("(d) ENFORCED refuses dangling RELATE", dangling_refused, detail)
        real_ok = False
        try:
            await run(admin, "RELATE $m->member_of->$k",
                      {"m": RecordID("principal", member_bare),
                       "k": RecordID("keep", k.id.split(":", 1)[1])})
            real_ok = True
        except Exception as e:  # noqa: BLE001
            real_detail = f"{type(e).__name__}: {e}"
        record("(d) POS-CONTROL real RELATE accepted", real_ok,
               "accepted" if real_ok else real_detail)

        # (a) create_keep atomicity — ghost keeper -> no orphan keep
        before = await keep_count()
        fake = Principal(id="principal:ghostkeeper00000000000000", email=KEEPER, subject=None,
                         display_name=None, status="active", role="member",
                         expires_at=None, created_at=datetime.now(UTC))

        async def _ghost_get(email: str) -> Principal | None:
            return fake

        orig = store._principals.get_by_email
        store._principals.get_by_email = _ghost_get  # type: ignore[method-assign]
        raised = False
        try:
            await store.create_keep(keeper_email=KEEPER, type="project", name="atom")
        except Exception as e:  # noqa: BLE001
            raised = True; araise = type(e).__name__
        finally:
            store._principals.get_by_email = orig  # type: ignore[method-assign]
        after = await keep_count()
        record("(a) ghost-keeper create_keep RAISES", raised, araise if raised else "did NOT raise")
        record("(a) ATOMIC: no orphan keep row", after == before,
               f"keep count before={before} after={after} (must be equal)")
        b2 = await keep_count()
        await store.create_keep(keeper_email=KEEPER, type="team", name="poscontrol")
        a2 = await keep_count()
        record("(a) POS-CONTROL normal create adds one row", a2 == b2 + 1, f"before={b2} after={a2}")

        # (b) keeper-lockout
        kb = await store.create_keep(keeper_email=KEEPER, type="project", name="lock")
        await store.add_household_member(keep_id=kb.id, member_email=MEMBER)
        locked = False
        try:
            await store.remove_household_member(keep_id=kb.id, member_email=KEEPER)
        except KeeperLockoutError:
            locked = True
        record("(b) remove keeper raises KeeperLockoutError", locked,
               "raised" if locked else "did NOT raise (keeper removable!)")
        hh = await store.list_household(kb.id)
        keeper_present = any(m.member_id == keeper_bare for m in hh)
        record("(b) keeper still in household after refusal", keeper_present,
               f"household={[m.member_id for m in hh]}")
        await store.remove_household_member(keep_id=kb.id, member_email=MEMBER)
        hh2 = await store.list_household(kb.id)
        member_gone = not any(m.member_id == member_bare for m in hh2)
        record("(b) POS-CONTROL non-keeper removal succeeds", member_gone,
               f"household_after={[m.member_id for m in hh2]}")

        # (c) nameless keep round-trips as name=None
        dm = await store.create_keep(keeper_email=KEEPER, type="dm")
        named = await store.create_keep(keeper_email=KEEPER, type="project", name="hasname")
        got_dm = await store.get_keep(dm.id)
        record("(c) get_keep(dm).name is None", got_dm is not None and got_dm.name is None,
               f"name={getattr(got_dm, 'name', '<none returned>')!r}")
        record("(c) POS-CONTROL get_keep(named).name preserved",
               (await store.get_keep(named.id)).name == "hasname", "read back")
        listed = await store.list_keeps_for_keeper(KEEPER)
        by_id = {kp.id: kp for kp in listed}
        record("(c) list_keeps includes nameless as name=None",
               dm.id in by_id and by_id[dm.id].name is None, f"nameless_in_list={dm.id in by_id}")
        record("(c) POS-CONTROL list_keeps named carries name",
               named.id in by_id and by_id[named.id].name == "hasname", "read back")
    finally:
        await admin.close()
        await store.close()
        await principals.close()
        await drop_database(env)

    print("\n=== SUMMARY ===")
    failed = [n for n, ok, _ in results if not ok]
    print(f"{sum(1 for _, ok, _ in results if ok)}/{len(results)} probes PASS")
    if failed:
        print("FAILED:", failed); return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```
It is a throwaway audit instrument, not a repo asset; if the lead wants it retained I can move it under `scripts/`.

## 6. The blocking defect class — stale "RED STUB"-era prose (MUST-FIX before commit)
Every site below describes the module as an unimplemented STUB, but the code is fully implemented — a future agent reading these would be actively misled (e.g. keeps.py:12 tells a reader "Do NOT implement the CRUD here — that is the builder's GREEN step", on a module whose CRUD is complete). This is the exact class PKT-28 C1 / the rename-sweep law flag as green-at-gate (no gate checks prose↔code consistency). Each is LOW severity individually; the CLASS is a must-fix. All are docs-only — no behaviour, no re-gate beyond re-running ruff/mypy.

| # | file:symbol | current (stale) | fix |
|---|---|---|---|
| 1 | `keeps.py` module docstring (lines ~3–12) | "⚠⚠ RED STUB … every CRUD verb raises `NotImplementedError` … The builder fills the CRUD bodies … Do NOT implement the CRUD here" | Delete the RED-STUB framing; state the module is the implemented KeepStore substrate (keep the accurate public-surface list below it). |
| 2 | `keeps.py` `KeepStore.ensure_ready` docstring (lines ~278–279) | "⚠⚠ STUB NOTE: `generate_keep_ddl` currently emits `""`, so this applies an empty transaction and creates NO table — the RED-by-design state." | Delete the STUB NOTE paragraph (the surrounding accurate DDL description stays). |
| 3 | `surreal_schema.py` `generate_ddl` fold comment (line ~1726) | "⚠ Stub emits nothing today." | Delete that sentence (the fold-order rationale above it is correct and stays). |
| 4 | `surreal_schema.py` keep-slice header comment (lines ~1959–1974) | "⚠⚠ RED STUBS … `_keep_statements`/`_member_of_statements` emit `[]` and `generate_keep_ddl` emits `""` … the stub emits no keep table/fields/index … Do NOT \"fix\" the emptiness here — it is the contract." | Replace the RED-STUBS block with a plain description of the implemented slice (the constants/specs prose below it is accurate and stays). |
| 5 | `_enforced_relations_scaffold.py` `ALL_DDL_GENERATORS` comment (lines ~94–95) | "⚠ RED-by-design until then: `generate_keep_ddl` STUBS to `""` … so it emits no relation table yet." | Delete the RED-by-design sentence; the edge is now emitted. |

Recommendation (right-size to importance): this is a 5-hunk docs-only cleanup. Cheapest correct path is a single one-shot fixer (or the lead applies it directly), then `ruff check .` + `scripts/typecheck.sh` re-confirm and commit. No behavioural re-gate needed. I did NOT edit (brief-base §2 — I review, I don't fix).

## 7. RESIDUALS (each with an individual verdict — read these, not just the summary)
| # | observation | verdict |
|---|---|---|
| R1 | **Pre-existing packet-49 stale STUB prose** at `surreal_schema.py:133–136` and `:1855–1866` ("⚠⚠ STUB (contract-49-1) … field specs / emitters below are RED stubs") — SAME class as §6, but COMMITTED and OUTSIDE packet 60. | Surfaced per scope law (not mine to fix). Recommend the operator let the §6 fixer clean these too while it is in the file — cheap, same class. NOT a packet-60 blocker. |
| R2 | `remove_household_member` keeper-lockout is check-then-DELETE (not atomic) — a theoretical TOCTOU if two admins raced. | Benign for wave 1: the `lore-adm` admin path is single-writer; no concurrent-removal requirement in scope. No pin needed now; a re-open trigger would be a multi-writer admin surface. |
| R3 | `KeepStore` has no production consumers yet (`lore_dead_code` would flag it). | Expected — it is NEW substrate (packet 60 is commit-only, deploys with 65; CLI verbs are a later wave). Not dead code. |
| R4 | `create_keep` returns `get_keep(keep_id)` (an extra read-back after commit). | Correct and intentional (returns the engine-stamped row). Minor extra round-trip, acceptable. |
| R5 | §1.4 relevance: the rank-widening dirty-store pin (`TestTheRankDomainWidensSafelyOnADirtyStore`) is the ONLY §1.4 pin, and it is NON-VACUOUS (positive control `…the_widened_constraint_is_WIDER_not_GONE` asserts a garbage rank is still rejected post-widen; passed). The `member_of` ENFORCED-flip dirty-store migration is a §1.1 hazard, not §1.4. Greenfield tables ⇒ §1.4 does not bite at birth. | Confirmed as the brief asked. Non-vacuous. ✓ |
| R6 | Idle-gate contract clobber (my early sloppy `ls -t | head` write hit `builder-60-w1`'s contract file). | Restored `{"artifact":"REPORT-builder-60-w1.md"}` immediately; my own contract written correctly. No lasting effect (builder-60-w1 is one-shot and done). |
| R7 | Contract-gap for the wave-2 lesson (like #397): none new found. The retry-seam registration gap (#397) was already caught+fixed this wave (`REPORT-fixer-60-retry-seam.md`); the contract is otherwise strongly discriminating (positive controls throughout, ≥2-member/≥2-keep small-N discrimination, quantifier/flatness exact-set pins, dirty-store migration legs). | Nothing to route to wave 2. |

## VERDICT
**NO-GO — NARROW / PROSE-ONLY.** The packet-60 wave-1 build is FUNCTIONALLY CORRECT and INDEPENDENTLY VERIFIED (1301 pytest passed, mypy clean, ruff clean, 14/14 live probes with positive controls, every Fork A–F + store-law clause confirmed on the real engine). It MUST NOT commit as-is because of the 5 stale "RED STUB"-era prose sites (§6) — the green-at-gate natural-language-consistency defect class. Fix those 5 docs-only sites, re-run ruff + typecheck, then commit. No rebuild, no behavioural re-gate. (If the lead deems shipping-then-fixing acceptable it is the lead's call — but the cheaper, cleaner path is fix-before-commit.)
