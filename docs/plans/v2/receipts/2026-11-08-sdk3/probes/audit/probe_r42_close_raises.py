"""R42 override (7d44cf1), R17: what does await_inbox serve when traffic WAS found and the teardown close() raises?
Store-free: fake connect / drain. CONTROL: the same run with a close() that succeeds returns the found entries."""
import asyncio, contextlib, sys
from surrealdb.errors import SurrealError
from loremaster.inbox_awaiter import InboxAwaiter
from loremaster.messages import MessageDrainResult

class _Entry:
    thread = None; grade = "signal"

def _result(n):
    return MessageDrainResult.model_construct(entries=[_Entry()] * n, total_pending=n, directive_pending=0, stamped_seqs=[], peeked=True)

class _Conn:
    def __init__(self, close_raises): self.close_raises = close_raises; self.closed = False
    async def query(self, *a, **k): return ["live-uuid"]  # SDK 3.0: one per-statement result
    async def subscribe_live(self, *_):
        async def gen():
            await asyncio.Event().wait()
            yield None
        return gen()
    async def kill(self, *_): return None
    @contextlib.contextmanager
    def timeout(self, *_): yield
    async def close(self):
        self.closed = True
        if self.close_raises: raise SurrealError("close failed over a severed socket (injected)")

async def run(close_raises):
    calls = {"n": 0}
    async def drain(**_):
        calls["n"] += 1
        return _result(0 if calls["n"] == 1 else 2)   # nothing at the snapshot, traffic on the first poll
    async def connect(): return _Conn(close_raises)
    async def no_sleep(_): return None
    awaiter = InboxAwaiter(connect=connect, drain=drain, sleep=no_sleep, budget_s=5.0, poll_interval_s=0.01)
    try:
        result = await awaiter.await_inbox(agent_id="a1", limit=10)
        return f"RETURNED entries={len(result.entries)} total_pending={result.total_pending}"
    except BaseException as error:
        return f"RAISED {type(error).__module__}.{type(error).__name__}: {error}"

print("CONTROL close ok   :", asyncio.run(run(False)))
print("CASE    close raise:", asyncio.run(run(True)))
