"""RULING-17's un-probed sub-case: does a SCHEMAFULL `option<datetime>` column admit NULL (literal, and Python None via
the SDK)? CONTROLS: a string is REJECTED (proves the type is enforced); a datetime is accepted."""
import asyncio, uuid
from datetime import datetime, timezone
from surrealdb import AsyncSurreal
URL = "ws://127.0.0.1:18000/rpc"; assert "18500" not in URL
async def attempt(db, label, sql, params=None):
    try:
        await db.query(sql, params or {})
        stored = await db.query(f"SELECT VALUE [s, type::of(s)] FROM t:{label}")
        print(f"{label:16} ACCEPTED stored={stored!r}")
    except Exception as error:
        print(f"{label:16} REJECTED {type(error).__name__}: {str(error)[:110]}")
async def main():
    db = AsyncSurreal(URL); await db.connect(); await db.signin({"username": "root", "password": "spikeroot"})
    name = f"audit66_optnull_{uuid.uuid4().hex[:6]}"
    await db.use("lore_test", name); await db.query(f"DEFINE DATABASE IF NOT EXISTS {name}"); await db.use("lore_test", name)
    try:
        await db.query("DEFINE TABLE t SCHEMAFULL; DEFINE FIELD OVERWRITE s ON t TYPE option<datetime>;")
        await attempt(db, "ctl_datetime", "CREATE t:ctl_datetime SET s = $v", {"v": datetime(2030, 1, 1, tzinfo=timezone.utc)})
        await attempt(db, "ctl_string", "CREATE t:ctl_string SET s = '2030-01-01T00:00:00Z'")
        await attempt(db, "literal_null", "CREATE t:literal_null SET s = NULL")
        await attempt(db, "python_none", "CREATE t:python_none SET s = $v", {"v": None})
        await attempt(db, "content_none", "CREATE t:content_none CONTENT $c", {"c": {"s": None}})
        print("> since admits:", await db.query("SELECT VALUE record::id(id) FROM t WHERE s > $v", {"v": datetime(2026, 1, 1, tzinfo=timezone.utc)}))
    finally:
        await db.query(f"REMOVE DATABASE IF EXISTS {name}"); await db.close()
asyncio.run(main())
