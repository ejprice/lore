# COPIED VERBATIM from audit66/probe_record_text_2.py (audit-sdk3-66 instrument) for build-66 R43 R-9 re-run; unchanged below.
"""Bound 9a, second leg: lore-minted NON-word keys — the uuid5 memory id and the composite [tier, path] file id."""
import asyncio, sys, uuid
from surrealdb import AsyncSurreal, RecordID
sys.path.insert(0, "loremaster")
from loremaster.store._txn import record_text
from loremaster.memory.local import derive_memory_id  # noqa: F401 (shape witness)
URL = "ws://127.0.0.1:18000/rpc"; assert "18500" not in URL
CASES = {"memory_uuid5": RecordID("memory", str(uuid.uuid5(uuid.NAMESPACE_URL, "x"))),
         "file_array": RecordID("file", ["lore", "loremaster/loremaster/server.py"])}
async def main():
    db = AsyncSurreal(URL); await db.connect(); await db.signin({"username": "root", "password": "spikeroot"})
    await db.use("lore_test", "audit66_probe_record_text")
    for label, rid in CASES.items():
        engine = await db.query("RETURN <string> $r", {"r": rid}); engine = engine[0] if isinstance(engine, list) else engine
        print(f"{label:14} engine={engine!r} record_text={record_text(rid)!r} equal={engine == record_text(rid)}")
    await db.close()
asyncio.run(main())
