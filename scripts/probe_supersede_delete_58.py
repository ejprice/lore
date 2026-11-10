# ruff: noqa: E501, PLW0603 - the pasted fence body is kept verbatim (the spec's line width; part F's global)
# Committed copy of packet 58 amendment 17 §INSTRUMENT-2 (docs/design/2026-11-09-packet58-amendment-17.md),
# by contract-58-r53 (lead #20049). Changes vs the pasted fence, and nothing else: loremaster/tests is put on
# sys.path relative to this file (probe_hub_txn_58._surreal_harness, not an absolute path), and every env is
# pinned to the TEST store (probe_hub_txn_58.URL = ws://127.0.0.1:18000/rpc; the harness env override is
# ignored). Sign-in: the env carries the suite harness's TEST-store credential, and every TaskLedger the probe
# builds signs in through loremaster.store._txn.signin_credentials (TaskLedger's own connect path).
# Type annotations added (the gate types `scripts/`); lint-only edits besides: `ruff check --fix` (import order; an import made unused or duplicate by the above dropped).
"""am-17 §9: the supersede's edge DELETE — is a DELETE's plan observable (EXPLAIN), and do the two forms
delete the same set at the same cost? TEST store :18000 only. Run from the repo root: `uv run python <file>`."""
import asyncio
import dataclasses
import json
import sys
import time

from probe_hub_txn_58 import URL as TEST_STORE_URL  # noqa: E402 - ws://127.0.0.1:18000/rpc, the TEST store
from probe_hub_txn_58 import _surreal_harness  # noqa: E402 - puts loremaster/tests on sys.path

_surreal_harness()
import _reanchor_58_support as s  # noqa: E402
from _surreal_harness import (  # noqa: E402
    PRODUCTION_DIM,
    SurrealEnv,
    drop_database,
    make_env,
    unique_database,
)
from surrealdb import RecordID  # noqa: E402

FORMS = {
    "T table-anchored": "DELETE blocks WHERE in = $old",
    "G graph-anchored": "DELETE $old->blocks",
}
HUB, NOISE = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (3000, 30000)



def fresh_test_store_env() -> SurrealEnv:
    """A fresh throwaway database on the TEST store ONLY: the harness env (its TEST-store credential),
    with the URL pinned to ``TEST_STORE_URL`` whatever the harness env override says."""
    env = dataclasses.replace(make_env(database=unique_database(), dim=PRODUCTION_DIM), url=TEST_STORE_URL)
    assert env.url == TEST_STORE_URL, "TEST store only"
    return env

async def main() -> None:
    env = fresh_test_store_env()
    assert ":18000" in env.url, "TEST store only"
    ledger = s.new_ledger(env)
    await ledger.ensure_ready()
    try:
        old = RecordID("task", "hubx")
        await s.raw_seed_row(ledger, "hubx", blocked_by=[])
        await s.raw_seed_row(ledger, "noisehub", blocked_by=[])
        await s.bulk_seed_dependents(ledger, "hubx", 5, "p")
        # 1. is a DELETE's plan observable?  (each attempt reports what the engine said)
        for text in (
            "DELETE blocks WHERE in = $old EXPLAIN",
            "DELETE $old->blocks EXPLAIN",
            "EXPLAIN DELETE blocks WHERE in = $old",
            "SELECT * FROM blocks WHERE in = $old EXPLAIN",
            "SELECT * FROM $old->blocks EXPLAIN",
        ):
            try:
                plan = await s.raw(ledger, text, {"old": old})
                print(f"PLAN  {text!r} -> {json.dumps(plan, default=str)[:700]}", flush=True)
            except Exception as e:  # noqa: BLE001 - a probe reports what it saw
                print(f"PLAN  {text!r} -> RAISED {type(e).__name__}: {str(e)[:200]}", flush=True)
        left = await s.raw(ledger, "SELECT count() AS n FROM blocks GROUP ALL")
        print(f"edges after the EXPLAIN attempts (5 seeded; an EXPLAIN must not delete): {left}", flush=True)
    finally:
        await ledger.close()
        await drop_database(env)
    # 2. same set, and cost against unrelated edges
    for name, form in FORMS.items():
        for noise in (0, NOISE):
            env = fresh_test_store_env()
            ledger = s.new_ledger(env)
            await ledger.ensure_ready()
            try:
                await s.raw_seed_row(ledger, "hubx", blocked_by=[])
                await s.raw_seed_row(ledger, "noisehub", blocked_by=[])
                ids = await s.bulk_seed_dependents(ledger, "hubx", HUB, "d")
                await s.raw_relate(ledger, ids[0], "noisehub")   # an edge INTO another row FROM a dependent: survives
                await s.raw_relate(ledger, "noisehub", "hubx")   # an edge INTO the hub: must survive (out = hub)
                for part in range(noise // 5000):
                    await s.bulk_seed_dependents(ledger, "noisehub", 5000, f"n{part}x")
                before = await s.raw(ledger, "SELECT count() AS n FROM blocks GROUP ALL")
                t = time.monotonic()
                await s.raw(ledger, form, {"old": RecordID("task", "hubx")})
                wall = time.monotonic() - t
                after = await s.raw(ledger, "SELECT count() AS n FROM blocks GROUP ALL")
                from_hub = await s.raw(ledger, "SELECT count() AS n FROM blocks WHERE in = $o GROUP ALL",
                                       {"o": RecordID("task", "hubx")})
                into_hub = await s.raw(ledger, "SELECT count() AS n FROM blocks WHERE out = $o GROUP ALL",
                                       {"o": RecordID("task", "hubx")})
                print(f"SET   {name} hub={HUB} noise={noise} before={before} after={after} from_hub={from_hub} "
                      f"into_hub={into_hub} wall={wall:.3f}s", flush=True)
            finally:
                await ledger.close()
                await drop_database(env)


asyncio.run(main())
