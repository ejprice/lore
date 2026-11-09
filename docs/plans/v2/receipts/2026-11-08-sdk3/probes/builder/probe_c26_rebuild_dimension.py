"""C row #26 (R43 R-9 — the instrument the KEEP reason lacked): can REBUILD INDEX do rebuild_embeddings' job,
which is a MODEL change and so a DIMENSION change? 3.3.5 TEST store, throwaway database, SDK 3.0.0.
Fixture: `mem` with an HNSW index DIMENSION 8 over 300 8-dim rows.
L1 CONTROL: plain REBUILD INDEX succeeds (the probe can see a success).
L2: REBUILD INDEX ... DIMENSION 16 — does REBUILD accept a new dimension at all?
L3: a 16-dim row INSERTed while the 8-dim index stands — accepted or refused?
L4: DEFINE INDEX OVERWRITE ... DIMENSION 16 over the stored 8-dim rows — accepted? then a 16-dim KNN: rows?"""
import asyncio, random, time, uuid
from surrealdb import AsyncSurreal
URL = "ws://127.0.0.1:18000/rpc"
assert "18500" not in URL
async def leg(db, label, stmt, params=None):
    t = time.monotonic()
    try:
        r = await db.query(stmt, params or {})
        print("#26", label, "OK in", round(time.monotonic() - t, 3), "s ->", str(r)[:160])
        return r
    except Exception as error:  # noqa: BLE001
        print("#26", label, "RAISES", type(error).__name__, str(error)[:200])
        return None
async def main() -> None:
    db = AsyncSurreal(URL); await db.signin({"username": "root", "password": "spikeroot"})
    name = f"probe_c26_{uuid.uuid4().hex[:8]}"
    await db.query("DEFINE NAMESPACE IF NOT EXISTS lore_test"); await db.use("lore_test", name)
    await db.query(f"DEFINE DATABASE IF NOT EXISTS {name}"); await db.use("lore_test", name)
    try:
        await db.query("DEFINE TABLE mem SCHEMAFULL")
        await db.query("DEFINE FIELD embedding ON mem TYPE array<float>")
        await db.query("DEFINE INDEX mem_hnsw ON mem FIELDS embedding HNSW DIMENSION 8 DIST COSINE TYPE F32")
        await db.query("INSERT INTO mem $rows", {"rows": [{"embedding": [random.random() for _ in range(8)]} for _ in range(300)]})
        await leg(db, "L1 CONTROL REBUILD INDEX", "REBUILD INDEX mem_hnsw ON mem")
        await leg(db, "L2 REBUILD ... DIMENSION 16", "REBUILD INDEX mem_hnsw ON mem DIMENSION 16")
        await leg(db, "L3 INSERT 16-dim row under the 8-dim index", "CREATE mem SET embedding = $v", {"v": [0.5] * 16})
        await leg(db, "L4 DEFINE INDEX OVERWRITE DIMENSION 16 over 8-dim rows",
                  "DEFINE INDEX OVERWRITE mem_hnsw ON mem FIELDS embedding HNSW DIMENSION 16 DIST COSINE TYPE F32")
        knn = await leg(db, "L4b 16-dim KNN after OVERWRITE", "SELECT id FROM mem WHERE embedding <|5,40|> $v", {"v": [0.5] * 16})
        if knn is not None:
            print("#26 L4b rows:", len(knn[0]) if knn and isinstance(knn[0], list) else knn)
    finally:
        await db.query(f"REMOVE DATABASE IF EXISTS {name}"); await db.close()
asyncio.run(main())
