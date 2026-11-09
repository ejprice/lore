"""C rows #9 (F10, packet doc §R3.7(b)), #16 (_safe_close), #21 (scout's connect ladder) on SDK 3.0.0 + 3.3.5, through
_sdk3_proxy.StoreBounceProxy, on connections from THE shared factory (loremaster.store._txn.open_surreal_connection).
Per sever mode (ABORT, CLOSE_FRAME) x RUNS:
  LIVE leg: LIVE SELECT via query -> subscribe_live -> iterate in a task -> go_down -> observe for OBSERVE_S: raised class
            (module-qualified) / ended / hung; then come_up and record whether the iterator resumed (it should not).
  KILL leg: LIVE SELECT -> go_down -> kill(id) under a 40 s cap (the SDK request timeout is 30 s) -> raised class (or ok); then come_up and kill again.
  CLOSE leg: go_down -> close() -> raised class or ok.
BOOT leg (#21, once): proxy DOWN before the first connect -> first request through a fresh factory connection -> class.
Verdict line per class family: any `websockets.*` class observed anywhere => WebSocketException arm still needed.
Run from loremaster/tests (imports _sdk3_proxy, _surreal_harness)."""
import asyncio, collections, sys, uuid
sys.path.insert(0, ".")
from _sdk3_proxy import SeverMode, StoreBounceProxy
from loremaster.store._txn import open_surreal_connection
URL = "ws://127.0.0.1:18000/rpc"; RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 20; OBSERVE_S = 3.0
def q(e): return f"{type(e).__module__}.{type(e).__qualname__}"
async def conn_on(proxy, db):
    c = open_surreal_connection(proxy.url)
    await c.signin({"username": "root", "password": "spikeroot"}); await c.use("lore_test", db); return c
async def main():
    db = f"probe_f10_{uuid.uuid4().hex[:8]}"
    admin = open_surreal_connection(URL); await admin.signin({"username": "root", "password": "spikeroot"})
    await admin.query("DEFINE NAMESPACE IF NOT EXISTS lore_test"); await admin.use("lore_test", db)
    await admin.query(f"DEFINE DATABASE IF NOT EXISTS {db}"); await admin.use("lore_test", db)
    await admin.query("DEFINE TABLE t SCHEMALESS")
    tally = collections.Counter()
    try:
        for mode in (SeverMode.ABORT, SeverMode.CLOSE_FRAME):
            for run in range(RUNS):
                proxy = StoreBounceProxy(upstream_url=URL); await proxy.start()
                c = await conn_on(proxy, db)
                live = (await c.query("LIVE SELECT * FROM t"))[0]
                sub = c.subscribe_live(live)
                if asyncio.iscoroutine(sub): sub = await sub
                outcome = {}
                async def consume():
                    try:
                        async for _ in sub: pass
                        outcome["live"] = "ended"
                    except BaseException as e:  # noqa: BLE001
                        outcome["live"] = "raised " + q(e)
                task = asyncio.create_task(consume()); await asyncio.sleep(0.2)
                await proxy.go_down(mode)
                try: await asyncio.wait_for(asyncio.shield(task), OBSERVE_S)
                except TimeoutError: outcome["live"] = "hung"
                tally[f"{mode.name} LIVE: {outcome['live']}"] += 1
                try:
                    await asyncio.wait_for(c.kill(live), 40); r = "ok"
                except BaseException as e:  # noqa: BLE001
                    r = "raised " + q(e)
                tally[f"{mode.name} KILL(down): {r}"] += 1
                await proxy.come_up(); await asyncio.sleep(2.5)
                try:
                    await asyncio.wait_for(c.kill(live), 40); r = "ok"
                except BaseException as e:  # noqa: BLE001
                    r = "raised " + q(e)
                tally[f"{mode.name} KILL(after come_up, LIVE the new session never had): {r}"] += 1
                if not task.done(): task.cancel()
                await proxy.go_down(mode)
                try: await asyncio.wait_for(c.close(), 20); r = "ok"
                except BaseException as e:  # noqa: BLE001
                    r = "raised " + q(e)
                tally[f"{mode.name} CLOSE(severed): {r}"] += 1
                await proxy.close()
        proxy = StoreBounceProxy(upstream_url=URL); await proxy.start(); await proxy.go_down()
        c = open_surreal_connection(proxy.url)
        try: await asyncio.wait_for(c.signin({"username": "root", "password": "spikeroot"}), 40); r = "ok"
        except BaseException as e:  # noqa: BLE001
            r = "raised " + q(e)
        tally[f"BOOT first request with the store down: {r}"] += 1
        await proxy.close()
    finally:
        await admin.query(f"REMOVE DATABASE IF EXISTS {db}"); await admin.close()
    for k, v in sorted(tally.items()): print(f"{v:3d}  {k}")
    print("websockets.* observed:", any("websockets." in k for k in tally))
asyncio.run(main())
