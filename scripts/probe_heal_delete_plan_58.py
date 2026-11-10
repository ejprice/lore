# ruff: noqa: E501, PLW0603 - the pasted fence body is kept verbatim (the spec's line width; part F's global)
# Committed copy of packet 58 amendment 17 §INSTRUMENT-2 (docs/design/2026-11-09-packet58-amendment-17.md),
# by contract-58-r53 (lead #20049). Changes vs the pasted fence, and nothing else: loremaster/tests is put on
# sys.path relative to this file (probe_hub_txn_58._surreal_harness, not an absolute path), and every env is
# pinned to the TEST store (probe_hub_txn_58.URL = ws://127.0.0.1:18000/rpc; the harness env override is
# ignored). Sign-in: the env carries the suite harness's TEST-store credential, and every TaskLedger the probe
# builds signs in through loremaster.store._txn.signin_credentials (TaskLedger's own connect path).
# Type annotations added (the gate types `scripts/`); lint-only edits besides: `ruff check --fix` (import order; an import made unused or duplicate by the above dropped);
# `asyncio.run(main())` moved under `if __name__ == "__main__":` so the module is importable.
"""am-17 §9.4: the EXPLAIN plan of the heal's three DELETE forms. A hub with 50 dependents; dependent d00000 also
has a second blocker. TEST store :18000 only."""
import asyncio
import collections
import dataclasses

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
        await s.raw_seed_row(ledger, "hubx", blocked_by=[])
        await s.raw_seed_row(ledger, "otherhub", blocked_by=[])
        ids = await s.bulk_seed_dependents(ledger, "hubx", 50, "d")
        await s.raw_relate(ledger, "otherhub", ids[0])
        params = {"i": RecordID("task", "hubx"), "o": RecordID("task", ids[0])}
        for name, text in (
            ("V1", "DELETE blocks WHERE in = $i AND out = $o EXPLAIN"),
            ("V2", "DELETE $i->blocks WHERE out = $o EXPLAIN"),
            ("V3", "DELETE $o<-blocks WHERE in = $i EXPLAIN"),
        ):
            plan = await s.raw(ledger, text, params)
            ops = collections.Counter(
                (node.get("operation"), (node.get("detail") or {}).get("table")) for node in plan
            )
            print(f"{name} {dict(ops)}")
        print("edges after (51 seeded):", await s.raw(ledger, "SELECT count() AS n FROM blocks GROUP ALL"))
    finally:
        await ledger.close()
        await drop_database(env)


if __name__ == "__main__":
    asyncio.run(main())
