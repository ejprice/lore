# ruff: noqa: E501, PLW0603 - the pasted fence body is kept verbatim (the spec's line width; part F's global)
# Committed copy of packet 58 amendment 17 §INSTRUMENT (docs/design/2026-11-09-packet58-amendment-17.md),
# by contract-58-r53 (lead #20049). Changes vs the pasted fence, and nothing else: loremaster/tests is put on
# sys.path relative to this file (probe_hub_txn_58._surreal_harness, not an absolute path), and every env is
# pinned to the TEST store (probe_hub_txn_58.URL = ws://127.0.0.1:18000/rpc; the harness env override is
# ignored). Sign-in: the env carries the suite harness's TEST-store credential, and every TaskLedger the probe
# builds signs in through loremaster.store._txn.signin_credentials (TaskLedger's own connect path).
# The pinned env is built by ONE helper, `probe_hub_txn_58.fresh_test_store_env` (lead #20070; was one copy per probe).
# Type annotations added (the gate types `scripts/`); lint-only edits besides: `ruff check --fix` (import order; an import made unused or duplicate by the above dropped).
"""am-17: the boot heal's cost CURVE on the REAL schema (TEST store :18000 only), and what drives it.

A  heal wall-clock for ONE chunk of n one-blocker stragglers, n in A_SIZES (the built ledger's own heal).
B  the per-straggler edge DELETE alone, n statements in one transaction over a `blocks` table of n edges:
   V1 = the heal's shape (`DELETE blocks WHERE in = $i AND out = $o`), V2 = the graph-anchored shape
   (`DELETE $i->blocks WHERE out = $o`); control: edges remaining after each == 0, and a V2 on a pair that
   does not exist deletes nothing.
C  a real `supersede_task` of a hub with N dependents under the served 30 s timeout, N in C_SIZES.
Run from the repo root: `uv run python <this file> A|B|C`.
"""
import asyncio
import dataclasses
import sys
import time

from probe_hub_txn_58 import (
    _surreal_harness,  # noqa: E402 - puts loremaster/tests on sys.path
    fresh_test_store_env,  # noqa: E402 - the env pinned to the TEST store
)

_surreal_harness()
import _reanchor_58_support as s  # noqa: E402
from _surreal_harness import (  # noqa: E402
    SurrealEnv,
    drop_database,
)
from loremaster.store import _txn  # noqa: E402
from loremaster.store._txn import TxnFragment, ensure_ready_operation  # noqa: E402
from loremaster.tasks import TaskLedger  # noqa: E402
from surrealdb import RecordID  # noqa: E402

A_SIZES = (500, 1000, 2000, 4000)
B_SIZES = (1000, 2000, 4000)
C_SIZES = (1665, 3332, 6000)



async def fresh() -> tuple[SurrealEnv, TaskLedger]:
    env = fresh_test_store_env()
    assert ":18000" in env.url, "TEST store only"
    ledger = s.new_ledger(env)
    await ledger.ensure_ready()
    return env, ledger


async def edge_count(ledger: TaskLedger) -> int:
    rows = await s.raw(ledger, "SELECT count() AS n FROM blocks GROUP ALL")
    rows = rows if isinstance(rows, list) else [rows]
    return int(rows[0]["n"]) if rows else 0


async def part_a() -> None:
    for n in A_SIZES:
        env, ledger = await fresh()
        try:
            await s.seed_stragglers(ledger, n, 1, "c")
            edges = await edge_count(ledger)
            spy = s.ComposeSpy()
            t = time.monotonic()
            with spy.installed():
                try:
                    await s.boot(env)
                    outcome = "ok"
                except Exception as e:  # noqa: BLE001 - a probe reports what it saw
                    outcome = f"RAISED {type(e).__name__}"
            wall = time.monotonic() - t
            print(f"A n={n} edges_before={edges} heal_rows={spy.heal_rows()} wall={wall:.2f}s "
                  f"outcome={outcome} edges_after={await edge_count(ledger)}", flush=True)
        finally:
            await ledger.close()
            await drop_database(env)


@ensure_ready_operation
async def _apply_long(ledger: TaskLedger, fragments: list[TxnFragment]) -> None:
    await ledger._apply(fragments)  # noqa: SLF001 - the heal's own write door


async def part_b() -> None:
    shapes = {
        "V1 table-anchored": "DELETE blocks WHERE in = $i{k} AND out = $o{k}",
        "V2 graph-anchored": "DELETE $i{k}->blocks WHERE out = $o{k}",
    }
    for n in B_SIZES:
        for name, shape in shapes.items():
            env, ledger = await fresh()
            try:
                await s.raw_seed_row(ledger, "hubx", blocked_by=[])
                ids = await s.bulk_seed_dependents(ledger, "hubx", n, "d")
                before = await edge_count(ledger)
                params = {}
                for k, dep in enumerate(ids):
                    params[f"i{k}"] = RecordID("task", "hubx")
                    params[f"o{k}"] = RecordID("task", dep)
                # control first: a pair that does not exist deletes nothing
                await _apply_long(ledger, [TxnFragment(
                    statements=[shape.format(k="c")],
                    params={"ic": RecordID("task", ids[0]), "oc": RecordID("task", "hubx")})])
                control = await edge_count(ledger)
                frag = TxnFragment(statements=[shape.format(k=k) for k in range(n)], params=params)
                t = time.monotonic()
                try:
                    await _apply_long(ledger, [frag])
                    outcome = "ok"
                except Exception as e:  # noqa: BLE001
                    outcome = f"RAISED {type(e).__name__}: {str(e)[:120]}"
                wall = time.monotonic() - t
                print(f"B {name} n={n} edges_before={before} after_control={control} wall={wall:.2f}s "
                      f"outcome={outcome} edges_after={await edge_count(ledger)}", flush=True)
            finally:
                await ledger.close()
                await drop_database(env)


async def part_c() -> None:
    for n in C_SIZES:
        env, ledger = await fresh()
        try:
            hub = await s.create(ledger, "hub")
            await s.bulk_seed_dependents(ledger, hub, n, "h")
            spy = s.ComposeSpy()
            t = time.monotonic()
            with spy.installed():
                try:
                    await s.supersede(ledger, hub)
                    outcome = "ok"
                except Exception as e:  # noqa: BLE001
                    outcome = f"RAISED {type(e).__name__}"
            wall = time.monotonic() - t
            moved = await s.raw(ledger, "SELECT count() AS n FROM task WHERE blocked_by CONTAINS $h GROUP ALL",
                                {"h": hub})
            print(f"C dependents={n} rows={spy.rows[-1] if spy.rows else None} wall={wall:.2f}s "
                  f"outcome={outcome} still_on_hub={moved}", flush=True)
        finally:
            await ledger.close()
            await drop_database(env)


if __name__ == "__main__":
    print(f"cap={_txn.TXN_ROW_HARD_CAP} request_timeout={_txn.SURREAL_REQUEST_TIMEOUT_SECONDS}", flush=True)
    if sys.argv[1] in ("A", "B", "C"):
        asyncio.run({"A": part_a, "B": part_b, "C": part_c}[sys.argv[1]]())


# ---- parts D / E (added after part B showed V1 and V2 both quadratic) -------------------------------------
import re  # noqa: E402

D_SIZES = (1000, 4000)
E_SIZES = tuple(int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "4000,12500").split(","))
INDEX_DDL = "DEFINE INDEX IF NOT EXISTS blocks_out ON blocks FIELDS out"
_HEAL_DELETE = re.compile(r"DELETE blocks WHERE in = (\$\w+) AND out = (\$\w+)")


async def part_d() -> None:
    """The edge DELETE alone again: V3 anchored at the DEPENDENT (its in-degree is its blocker count), and
    V4 = the heal's own shape with a plain index on `blocks.out`. Controls as part B, plus a V3/V4 leg where
    the dependent has a SECOND blocker whose edge must survive."""
    shapes = {
        "V3 dependent-anchored": ("DELETE $o{k}<-blocks WHERE in = $i{k}", False),
        "V4 table-anchored+index(out)": ("DELETE blocks WHERE in = $i{k} AND out = $o{k}", True),
    }
    for n in D_SIZES:
        for name, (shape, index) in shapes.items():
            env, ledger = await fresh()
            try:
                if index:
                    await s.raw(ledger, INDEX_DDL)
                await s.raw_seed_row(ledger, "hubx", blocked_by=[])
                await s.raw_seed_row(ledger, "otherhub", blocked_by=[])
                ids = await s.bulk_seed_dependents(ledger, "hubx", n, "d")
                await s.raw_relate(ledger, "otherhub", ids[0])  # must SURVIVE the delete of (hubx, ids[0])
                before = await edge_count(ledger)
                params = {}
                for k, dep in enumerate(ids):
                    params[f"i{k}"] = RecordID("task", "hubx")
                    params[f"o{k}"] = RecordID("task", dep)
                await _apply_long(ledger, [TxnFragment(
                    statements=[shape.format(k="c")],
                    params={"ic": RecordID("task", ids[0]), "oc": RecordID("task", "hubx")})])
                control = await edge_count(ledger)
                frag = TxnFragment(statements=[shape.format(k=k) for k in range(n)], params=params)
                t = time.monotonic()
                try:
                    await _apply_long(ledger, [frag])
                    outcome = "ok"
                except Exception as e:  # noqa: BLE001
                    outcome = f"RAISED {type(e).__name__}: {str(e)[:160]}"
                wall = time.monotonic() - t
                survivor = await s.raw(ledger, "SELECT in, out FROM blocks")
                print(f"D {name} n={n} edges_before={before} after_control={control} wall={wall:.2f}s "
                      f"outcome={outcome} edges_after={await edge_count(ledger)} survivor={survivor}", flush=True)
            finally:
                await ledger.close()
                await drop_database(env)


async def part_e() -> None:
    """The REAL heal (built ledger, real schema, one chunk) with the edge DELETE swapped for V3 (statement
    rewrite at `_apply`, production untouched) or served by V4's index. n=12500 is the full 50,000-row chunk."""
    real_apply = TaskLedger._apply  # noqa: SLF001

    async def rewriting_apply(self: TaskLedger, fragments: list[TxnFragment]) -> None:
        swapped = [
            dataclasses.replace(f, statements=[_HEAL_DELETE.sub(r"DELETE \2<-blocks WHERE in = \1", st)
                                               for st in f.statements])
            for f in fragments
        ]
        await real_apply(self, swapped)

    for n in E_SIZES:
        for name in (sys.argv[3].split(",") if len(sys.argv) > 3 else ("V3", "V4")):
            env, ledger = await fresh()
            try:
                if name == "V4":
                    await s.raw(ledger, INDEX_DDL)
                head, ids = await s.seed_stragglers(ledger, n, 1, "e")
                before = await edge_count(ledger)
                spy = s.ComposeSpy()
                if name == "V3":
                    TaskLedger._apply = rewriting_apply  # type: ignore[method-assign]  # noqa: SLF001
                t = time.monotonic()
                try:
                    with spy.installed():
                        try:
                            await s.boot(env)
                            outcome = "ok"
                        except Exception as e:  # noqa: BLE001
                            outcome = f"RAISED {type(e).__name__}: {str(e)[:160]}"
                finally:
                    TaskLedger._apply = real_apply  # type: ignore[method-assign]  # noqa: SLF001
                wall = time.monotonic() - t
                on_head = await s.raw(
                    ledger, "SELECT count() AS n FROM task WHERE blocked_by CONTAINS $h GROUP ALL", {"h": head})
                legacy_edges = await s.raw(
                    ledger, "SELECT count() AS n FROM blocks WHERE in = $l GROUP ALL",
                    {"l": RecordID("task", "elegacy0000000000000000000")})
                print(f"E {name} n={n} edges_before={before} heal_rows={spy.heal_rows()} wall={wall:.2f}s "
                      f"outcome={outcome} rows_on_head={on_head} old_edges_left={legacy_edges} "
                      f"edges_after={await edge_count(ledger)}", flush=True)
            finally:
                await ledger.close()
                await drop_database(env)


if __name__ == "__main__" and sys.argv[1] in ("D", "E"):
    asyncio.run({"D": part_d, "E": part_e}[sys.argv[1]]())


async def part_f() -> None:
    """The RULED build emulated end to end: V3 delete + the packer bound at TXN_ROW_WARN_THRESHOLD (the packer
    reads `_txn.TXN_ROW_HARD_CAP` live, so the probe process sets it to the warn threshold), 12,500 stragglers
    in a world that ALSO holds 20,000 unrelated edges. Expect 5 chunks of 10,000 rows."""
    _txn.TXN_ROW_HARD_CAP = _txn.TXN_ROW_WARN_THRESHOLD
    sys.argv[2:] = ["12500", "V3"]
    global E_SIZES
    E_SIZES = (12500,)
    real_seed = s.seed_stragglers

    async def seed_with_noise(ledger: TaskLedger, total: int, blockers: int, tag: str) -> tuple[str, list[str]]:
        await s.raw_seed_row(ledger, "noisehub", blocked_by=[])
        for part in range(4):
            await s.bulk_seed_dependents(ledger, "noisehub", 5000, f"n{part}x")
        return await real_seed(ledger, total, blockers, tag)

    s.seed_stragglers = seed_with_noise
    await part_e()


if __name__ == "__main__" and sys.argv[1] == "F":
    asyncio.run(part_f())
