# COPIED VERBATIM from audit66/probe_record_text.py (audit-sdk3-66 instrument) for build-66 R43 R-9 re-run; unchanged below.
"""Stated bound 9a: does record_text (table:key from parts) equal the engine's <string> id for lore-minted keys?
TEST store ws://127.0.0.1:18000 only; RETURN-only, no table written. Control: a non-word key MUST differ."""
import asyncio, os, sys
from surrealdb import AsyncSurreal, RecordID
from ulid import ULID
sys.path.insert(0, "loremaster")
from loremaster.store._txn import record_text

URL = "ws://127.0.0.1:18000/rpc"
assert "18500" not in URL
KEYS = {"ulid": str(ULID()), "ulid2": str(ULID()), "engine_like_digit_led": "4558tcyfmwp3lj775pwi",
        "alpha_led": "abc123", "hex": "deadbeef0123", "CONTROL_non_word": "a-b", "CONTROL_all_digits": "42"}

async def main() -> int:
    db = AsyncSurreal(URL)
    await db.connect()
    await db.signin({"username": os.environ.get("SURREAL_USER", "root"), "password": os.environ.get("SURREAL_PASS", "spikeroot")})
    await db.use("lore_test", "audit66_probe_record_text")
    bad = 0
    for label, key in KEYS.items():
        rid = RecordID("keep", key)
        engine = await db.query("RETURN <string> $r", {"r": rid})
        engine = engine[0] if isinstance(engine, list) else engine  # SDK 3.0 query() answers a list for RETURN
        ours = record_text(rid)
        same = engine == ours
        print(f"{label:24} key={key!r:32} engine={engine!r:42} record_text={ours!r:36} equal={same}")
        if label.startswith("CONTROL") == same:
            bad += 1
    await db.close()
    print("PROBE", "PASS" if bad == 0 else f"FAIL ({bad})")
    return 0 if bad == 0 else 1

sys.exit(asyncio.run(main()))
