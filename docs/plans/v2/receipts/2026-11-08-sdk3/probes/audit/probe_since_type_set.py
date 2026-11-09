"""#597 / S6: which stamp TYPES does `col > $since` ($since a datetime) admit on the 3.3.5 TEST store?
Claimed (servicer r45 probe): admits array, object, uuid, record; excludes string, number, bool, null, duration.
CONTROLS: a datetime AFTER $since is admitted; a datetime BEFORE $since and NONE are excluded."""
import asyncio, uuid, json
from datetime import datetime, timezone
from surrealdb import AsyncSurreal
URL = "ws://127.0.0.1:18000/rpc"; assert "18500" not in URL
SINCE = datetime(2026, 1, 1, tzinfo=timezone.utc)
LITERALS = {"dt_after": "d'2030-01-01T00:00:00Z'", "dt_before": "d'2020-01-01T00:00:00Z'", "none": "NONE",
            "string": "'2030-01-01T00:00:00Z'", "number": "42", "float": "4.2", "bool": "true", "null": "NULL",
            "duration": "1h", "array": "['2030']", "object": "{a: 1}", "uuid": "u'0199c4f1-7d2a-7000-8000-000000000001'",
            "record": "other:x"}
async def main():
    db = AsyncSurreal(URL); await db.connect(); await db.signin({"username": "root", "password": "spikeroot"})
    name = f"audit66_since_types_{uuid.uuid4().hex[:6]}"
    await db.use("lore_test", name); await db.query(f"DEFINE DATABASE IF NOT EXISTS {name}"); await db.use("lore_test", name)
    try:
        for kind, lit in LITERALS.items():
            await db.query(f"CREATE t:{kind} SET kind = '{kind}', s = {lit}")
        got = await db.query("SELECT VALUE kind FROM t WHERE s > $since", {"since": SINCE})
        admitted = sorted(got[0] if got and isinstance(got[0], list) else got)
        print("ADMITTED:", admitted)
        print("EXCLUDED:", sorted(set(LITERALS) - set(admitted)))
        ok = ("dt_after" in admitted and "dt_before" not in admitted and "none" not in admitted)
        print("CONTROLS", "PASS" if ok else "FAIL")
    finally:
        await db.query(f"REMOVE DATABASE IF EXISTS {name}"); await db.close()
asyncio.run(main())
