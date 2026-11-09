"""The teardown-kill bound (build-66 defect fix): with the store DOWN, how long do scout's and the awaiter's
best-effort _safe_kill take, and do they raise? Control: a bare connection.kill() under the same outage (the
unbounded SDK 3.0 behaviour, ~30 s TransportTimeoutError). The kill is issued 3 s after the store drops, once
the SDK is reconnecting (the state probe_c_proxy measured). Run from loremaster/tests."""
import asyncio, sys, time, uuid
sys.path.insert(0, ".")
from _sdk3_proxy import StoreBounceProxy
from loremaster.inbox_awaiter import InboxAwaiter
from loremaster.scout import CommandSubscriber
from loremaster.store._txn import open_surreal_connection
URL = "ws://127.0.0.1:18000/rpc"
async def leg(label, kill):
    proxy = StoreBounceProxy(upstream_url=URL); await proxy.start()
    c = open_surreal_connection(proxy.url); await c.signin({"username": "root", "password": "spikeroot"})
    db = f"probe_kill_{uuid.uuid4().hex[:6]}"
    await c.query("DEFINE NAMESPACE IF NOT EXISTS lore_test"); await c.use("lore_test", db)
    await c.query(f"DEFINE DATABASE IF NOT EXISTS {db}"); await c.use("lore_test", db)
    await c.query("DEFINE TABLE t SCHEMALESS")
    live = (await c.query("LIVE SELECT * FROM t"))[0]
    await proxy.go_down(); await asyncio.sleep(3.0)  # let the SDK enter its reconnect loop (as probe_c_proxy)
    t = time.monotonic()
    try: await kill(c, live); r = "returned"
    except BaseException as e: r = f"raised {type(e).__module__}.{type(e).__name__}"  # noqa: BLE001
    print(f"{label}: {r} after {time.monotonic() - t:.2f}s"); await proxy.close()
async def main():
    await leg("scout _safe_kill", CommandSubscriber._safe_kill)
    awaiter = InboxAwaiter.__new__(InboxAwaiter)
    await leg("awaiter _safe_kill", awaiter._safe_kill)
    await leg("CONTROL bare kill()", lambda c, live: c.kill(live))
asyncio.run(main())
