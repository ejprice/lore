"""C rows #19, #25, #26, #35 on the 3.3.5 TEST store (ws://127.0.0.1:18000, throwaway database), SDK 3.0.0.
#19: the query-recursion-limit rejection — class + details.kind (does ValidationError.is_parse_error cover it?)
#25: does string::starts_with(record::id(id), $p) plan an index scan (could the name.value mirror retire)?
     control: the production form string::starts_with(value, $p) on the indexed mirror column.
#26: does a blocking REBUILD INDEX on an HNSW index succeed on 3.3.5, and how long for N rows?
#35: does record::id(NONE) still RAISE on 3.3.5 (floor_calibration's client-side NONE guard rests on it)?"""
import asyncio, time, uuid, json
from surrealdb import AsyncSurreal, RecordID
from surrealdb import errors as E
URL = "ws://127.0.0.1:18000/rpc"
async def main():
    db = AsyncSurreal(URL); await db.signin({"username": "root", "password": "spikeroot"})
    name = f"probe_c_{uuid.uuid4().hex[:8]}"
    await db.query("DEFINE NAMESPACE IF NOT EXISTS lore_test"); await db.use("lore_test", name)
    await db.query(f"DEFINE DATABASE IF NOT EXISTS {name}"); await db.use("lore_test", name)
    try:
        # 19
        terms = " OR ".join(f"source_text @@ 'w{i}'" for i in range(3000))
        await db.query("DEFINE TABLE c SCHEMALESS")
        try:
            await db.query(f"SELECT * FROM c WHERE {terms}")
            print("#19 no rejection at 3000 OR terms")
        except E.ServerError as e:
            print("#19", type(e).__name__, "kind=", e.kind, "details=", json.dumps(e.details, default=str)[:200],
                  "is_parse_error=", getattr(e, "is_parse_error", None), "msg=", str(e)[:120])
        # 25
        await db.query("DEFINE TABLE name SCHEMAFULL; ")
        await db.query("DEFINE FIELD value ON name TYPE string")
        await db.query("DEFINE INDEX name_value ON name FIELDS value")
        rows = [{"id": RecordID("name", f"pkg.m{i}.sym{j}"), "value": f"pkg.m{i}.sym{j}"} for i in range(50) for j in range(20)]
        await db.query("INSERT INTO name $rows", {"rows": rows})
        for label, stmt in (("native-on-id", "SELECT VALUE id FROM name WHERE string::starts_with(record::id(id), $p) EXPLAIN"),
                            ("control-mirror", "SELECT VALUE id FROM name WHERE string::starts_with(value, $p) EXPLAIN")):
            plan = await db.query(stmt, {"p": "pkg.m1."})
            print("#25", label, json.dumps(plan, default=str)[:400])
        got = await db.query("SELECT VALUE id FROM name WHERE string::starts_with(record::id(id), $p)", {"p": "pkg.m1."})
        print("#25 native-on-id rows:", len(got[0]) if got and isinstance(got[0], list) else got)
        # 26
        await db.query("DEFINE TABLE mem SCHEMAFULL")
        await db.query("DEFINE FIELD embedding ON mem TYPE array<float>")
        await db.query("DEFINE INDEX mem_hnsw ON mem FIELDS embedding HNSW DIMENSION 8 DIST COSINE TYPE F32")
        import random
        await db.query("INSERT INTO mem $rows", {"rows": [{"embedding": [random.random() for _ in range(8)]} for _ in range(2000)]})
        t = time.monotonic()
        try:
            r = await db.query("REBUILD INDEX mem_hnsw ON mem")
            print("#26 REBUILD INDEX ok in", round(time.monotonic() - t, 3), "s ->", r)
            knn = await db.query("SELECT id FROM mem WHERE embedding <|5,40|> $v", {"v": [0.5] * 8})
            print("#26 knn after rebuild rows:", len(knn[0]))
        except Exception as e:  # noqa: BLE001
            print("#26 REBUILD INDEX raised", type(e).__name__, str(e)[:200])
        # 35
        for label, stmt in (("record::id(NONE)", "RETURN record::id(NONE)"), ("control record::id(t:1)", "RETURN record::id(t:1)")):
            try:
                print("#35", label, "->", await db.query(stmt))
            except Exception as e:  # noqa: BLE001
                print("#35", label, "RAISES", type(e).__name__, str(e)[:120])
    finally:
        await db.query(f"REMOVE DATABASE IF EXISTS {name}"); await db.close()
asyncio.run(main())
