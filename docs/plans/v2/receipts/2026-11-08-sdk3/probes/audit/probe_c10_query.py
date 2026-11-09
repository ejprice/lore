"""C10 bound: does SDK 3.0.0 query() RAISE when a LATER statement fails (so run()'s first-statement answer cannot hide it)?
TEST store only; throwaway db in lore_test. CONTROL: an all-OK multi-statement answers one result per statement."""
import asyncio
from surrealdb import AsyncSurreal
URL = "ws://127.0.0.1:18000/rpc"; assert "18500" not in URL
CASES = {"CONTROL ok;ok": "RETURN 1; RETURN 2;",
         "later THROW": "RETURN 1; THROW 'later';",
         "later DDL error": "DEFINE TABLE c10a SCHEMAFULL; DEFINE FIELD x ON c10a TYPE int; CREATE c10a:1 SET x = 'not-an-int';",
         "txn later THROW": "BEGIN; CREATE c10b:1; THROW 'in-txn'; COMMIT;"}
async def main():
    db = AsyncSurreal(URL); await db.connect(); await db.signin({"username": "root", "password": "spikeroot"})
    await db.use("lore_test", "audit66_probe_c10")
    for label, sql in CASES.items():
        try:
            print(f"{label:18} -> RETURNED {await db.query(sql)!r}")
        except Exception as error:
            print(f"{label:18} -> RAISED {type(error).__name__}: {str(error)[:100]}")
    await db.query("REMOVE DATABASE audit66_probe_c10;") if False else None
    await db.close()
asyncio.run(main())
