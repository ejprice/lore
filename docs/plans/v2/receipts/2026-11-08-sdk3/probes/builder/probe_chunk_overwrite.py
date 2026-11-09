"""R4 rider 1 / X13 / R27-2a probe: does a batched INSERT ... ON DUPLICATE KEY UPDATE <every chunk column> =
$input.<col> overwrite a chunk row exactly as the retired per-row `UPSERT ... CONTENT` did?

Runs on the 3.3.5 TEST store (ws://127.0.0.1:18000) in a throwaway namespace/database with lore's REAL
chunk DDL. Three legs, each byte-diffing SELECT * output of OLD vs NEW:
  1. overwrite: row A (with llm_summary) then A' (WITHOUT llm_summary, different text) -> A' wholly.
  2. intra-batch duplicate id in ONE statement: [A, A'] -> A' (last write wins, upsert's documented contract).
  3. control: the NEW form WITHOUT the ON DUPLICATE clause must FAIL on leg 1 (proves the clause is load-bearing).
Exit 0 iff every leg matches and the control fails.
"""
import asyncio, sys, uuid
from surrealdb import AsyncSurreal, RecordID
from loremaster.store.surreal_schema import generate_ddl, CHUNK_COLUMNS

URL = "ws://127.0.0.1:18000/rpc"

def row(key: str, text: str, summary: str | None) -> dict:
    r = {"tier": "t", "file_path": "f.py", "chunk_type": "function", "identity": "m.f", "sub_ordinal": 0,
         "content_hash": text, "mtime_ns": 1, "line_start": 1, "line_end": 2, "source_text": text,
         "ident_text": "m.f f", "metadata": {"k": text}, "embedding": [0.1] * 8}
    if summary is not None:
        r["llm_summary"] = summary
    return r

UPDATE = ", ".join(f"{c} = $input.{c}" for c in CHUNK_COLUMNS)

async def main() -> int:
    db = AsyncSurreal(URL)
    await db.signin({"username": "root", "password": "spikeroot"})
    ns, name = "lore_test", f"probe_overwrite_{uuid.uuid4().hex[:8]}"
    await db.query(f"DEFINE NAMESPACE IF NOT EXISTS {ns}")
    await db.use(ns, name)
    await db.query(f"DEFINE DATABASE IF NOT EXISTS {name}")
    await db.use(ns, name)
    ok = True
    try:
        await db.query_raw(generate_ddl(dim=8, analyzer_name="probe_an"), {})
        a, a2 = row("k", "first", "sum"), row("k", "second", None)
        async def old(key):
            for r in (a, a2):
                await db.query("UPSERT type::record('chunk', $id) CONTENT $c", {"id": key, "c": r})
            return await db.query("SELECT * FROM type::record('chunk', $id)", {"id": key})
        async def new(key, rows_seq, clause=True):
            stmt = "INSERT INTO chunk $rows" + (f" ON DUPLICATE KEY UPDATE {UPDATE}" if clause else "")
            for rows in rows_seq:
                await db.query(stmt, {"rows": [{**r, "id": RecordID("chunk", key)} for r in rows]})
            return await db.query("SELECT * FROM type::record('chunk', $id)", {"id": key})
        o = await old("old1"); n = await new("new1", [[a], [a2]])
        strip = lambda res: [{k: v for k, v in r.items() if k != "id"} for r in res[0]]
        leg1 = strip(o) == strip(n); print("leg1 overwrite OLD==NEW:", leg1, "\n OLD", strip(o), "\n NEW", strip(n)); ok &= leg1
        n2 = await new("new2", [[a, a2]])
        leg2 = strip(n2) == strip(o); print("leg2 intra-batch dup last-wins:", leg2, strip(n2)); ok &= leg2
        try:
            await new("ctl", [[a], [a2]], clause=False)
            print("control: plain INSERT over an existing id did NOT fail — clause not proven load-bearing"); ok = False
        except Exception as e:  # noqa: BLE001
            print("control: plain INSERT over an existing id FAILED as expected:", type(e).__name__, str(e)[:120])
        missing = await db.query("RETURN {a: 1}.missing")
        print("$input.<absent key> reads:", missing)
    finally:
        await db.query(f"REMOVE DATABASE IF EXISTS {name}")
        await db.close()
    print("PROBE", "PASS" if ok else "FAIL")
    return 0 if ok else 1

sys.exit(asyncio.run(main()))
