"""Percentiles of lore_search latency_ms from the prod-copy trace table (prod's served history), TEST store only."""
import asyncio, os, sys
from surrealdb import AsyncSurreal
async def main(db_name: str) -> None:
    async with AsyncSurreal("ws://127.0.0.1:18000/rpc") as db:
        await db.signin({"username": os.environ["CONFORM_SURREAL_USER"], "password": os.environ["CONFORM_SURREAL_PASS"]})
        await db.use("lore_test", db_name)
        res = await db.query("SELECT latency_ms, ts FROM trace WHERE tool = 'lore_search' AND ts < d'2026-11-08T22:56:20Z' ORDER BY ts DESC LIMIT 2000")
        rows = res[0] if res and isinstance(res[0], list) else res
        lat = sorted(float(r["latency_ms"]) for r in rows if r.get("latency_ms") is not None)
        q = lambda p: lat[min(len(lat) - 1, int(p * len(lat)))]
        print(f"n={len(lat)} p50={q(0.5):.0f}ms p90={q(0.9):.0f}ms p99={q(0.99):.0f}ms max={lat[-1]:.0f}ms newest_ts={rows[0]['ts'] if rows else None} oldest_ts={rows[-1]['ts'] if rows else None}")
asyncio.run(main(sys.argv[1]))
