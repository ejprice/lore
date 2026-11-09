"""Drop row #14 (C): can SDK 3.0.0's native db.batch() replace _txn.compose + the root-cause selector?
Gate (packet doc §R3.4): T6 — a THROW whose text QUOTES the cascade notice must surface as kind `Thrown`; a
db.batch() whose selector skips any failure whose message contains "not executed due to a failed transaction"
reports a cascade/Cancelled/COMMIT notice instead. Also X12: does it expose EVERY failed statement (lore logs all)?
Leg 1 (T6): [CREATE ok, THROW quoting the notice, CREATE] -> which error class/kind/text does execute() raise?
Leg 2 (control): [CREATE ok, THROW 'plain', CREATE] -> class/kind (proves the probe reads a THROW correctly).
Leg 3: nothing committed after either (all-or-nothing)."""
import asyncio, uuid
from surrealdb import AsyncSurreal
from surrealdb import errors as E
URL = "ws://127.0.0.1:18000/rpc"
async def main():
    db = AsyncSurreal(URL); await db.signin({"username": "root", "password": "spikeroot"})
    name = f"probe_batch_{uuid.uuid4().hex[:8]}"
    await db.query("DEFINE NAMESPACE IF NOT EXISTS lore_test"); await db.use("lore_test", name)
    await db.query(f"DEFINE DATABASE IF NOT EXISTS {name}"); await db.use("lore_test", name)
    try:
        for label, thrown in (("T6 quoting", "boom: The query was not executed due to a failed transaction"),
                              ("control plain", "boom plain")):
            b = db.batch().query("CREATE t:a SET v = 1").query("THROW $m", {"m": thrown}).query("CREATE t:b SET v = 2")
            try:
                r = await b.execute(); print(label, "NO RAISE", r)
            except E.ServerError as e:
                print(label, "->", type(e).__name__, "kind=", e.kind, "| text:", str(e)[:110])
            try:
                rows = (await db.query("SELECT * FROM t"))[0]
            except E.NotFoundError:
                rows = "table t does not exist (nothing committed)"
            print(label, "committed rows after:", rows)
    finally:
        await db.query(f"REMOVE DATABASE IF EXISTS {name}"); await db.close()
asyncio.run(main())
