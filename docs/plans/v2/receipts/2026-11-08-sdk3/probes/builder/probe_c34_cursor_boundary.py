"""C row #34 (R43 R-9 — the row that had NO instrument and shipped #590): does the exclusive boundary
`WHERE u > $since` hold with NO +1 us ceiling, over EVERY path a stamp travels? 3.3.5 TEST store, throwaway db.
Fixture: one row stamped by the engine with a NON-ZERO nanosecond tail (time::now() re-stamped until ns != 0;
the stamp read back is a PreciseDatetime).
L1 in-process rebind: the PreciseDatetime read back, bound as $since -> row EXCLUDED (the old pins' path).
L2 pydantic: a model's `datetime` field keeps the PreciseDatetime (type + ns) -> rebound -> EXCLUDED.
L3 CONTROL (the #590 defect, must REPRODUCE): served text via datetime.isoformat(), parsed back with
   datetime.fromisoformat -> row RE-SERVED. Proves the probe can see the failure.
L4 THE CURSOR CODEC (R43): served_instant_text -> parse_served_instant -> EXCLUDED.
L5 pre-R43 us cursor through the codec parser: re-serves the boundary row (the stated once-only re-serve)."""
import asyncio, uuid
from datetime import datetime
from pydantic import BaseModel
from surrealdb import AsyncSurreal, RecordID
from loremaster.store._txn import parse_served_instant, served_instant_text
URL = "ws://127.0.0.1:18000/rpc"
assert "18500" not in URL
class Row(BaseModel):
    updated_at: datetime
async def excluded(db, since) -> bool:
    got = await db.query("SELECT VALUE id FROM t WHERE u > $since", {"since": since})
    rows = got[0] if got and isinstance(got[0], list) else got
    return RecordID("t", "a") not in rows
async def main() -> None:
    db = AsyncSurreal(URL); await db.signin({"username": "root", "password": "spikeroot"})
    name = f"probe_c34_{uuid.uuid4().hex[:8]}"
    await db.query("DEFINE NAMESPACE IF NOT EXISTS lore_test"); await db.use("lore_test", name)
    await db.query(f"DEFINE DATABASE IF NOT EXISTS {name}"); await db.use("lore_test", name)
    try:
        await db.query("DEFINE TABLE t SCHEMAFULL; DEFINE FIELD u ON t TYPE datetime;")
        await db.query("CREATE t:a SET u = time::now()")
        for _ in range(50):
            got = await db.query("SELECT VALUE u FROM t:a")
            stamp = (got[0] if isinstance(got[0], list) else got)[0]
            if getattr(stamp, "nanosecond", 0):
                break
            await db.query("UPDATE t:a SET u = time::now()")
        print("stamp", type(stamp).__name__, stamp.isoformat_with_nanoseconds(), "ns", stamp.nanosecond)
        assert stamp.nanosecond, "could not obtain a non-zero ns stamp"
        model = Row(updated_at=stamp)
        legs = (
            ("L1 in-process rebind", stamp, True),
            ("L2 pydantic field (type=%s ns=%s)" % (type(model.updated_at).__name__, getattr(model.updated_at, "nanosecond", None)),
             model.updated_at, True),
            ("L3 CONTROL isoformat/fromisoformat (#590)", datetime.fromisoformat(stamp.isoformat()), False),
            ("L4 CODEC served_instant_text/parse_served_instant", parse_served_instant(served_instant_text(stamp)), True),
            ("L5 pre-R43 us cursor via the codec parser", parse_served_instant(stamp.isoformat()), False),
        )
        bad = 0
        for label, since, want_excluded in legs:
            got_excluded = await excluded(db, since)
            ok = got_excluded == want_excluded
            bad += not ok
            print(f"#34 {label}: since={getattr(since, 'isoformat_with_nanoseconds', since.isoformat)()} "
                  f"excluded={got_excluded} expected_excluded={want_excluded} {'OK' if ok else 'UNEXPECTED'}")
        print("PROBE", "PASS" if bad == 0 else f"FAIL ({bad})")
    finally:
        await db.query(f"REMOVE DATABASE IF EXISTS {name}"); await db.close()
asyncio.run(main())
