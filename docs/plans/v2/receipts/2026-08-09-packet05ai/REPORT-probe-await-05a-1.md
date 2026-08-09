brief-base v10 read
brief project v7 read

# REPORT-probe-await-05a-1 — build-time store probes for the `await` design

## SUMMARY BLOCK
- Receipt: `brief-base v10 read` · `brief project v7 read`
- State: **done** — both probes have a VERDICT + a passing control.
- Capability check: all tools present; test store `ws://127.0.0.1:18000` reachable; probe ran clean.
- **PROBE 1 VERDICT — FIRES.** An edge-table LIVE SELECT *does* fire on `RELATE`, both whole-table `.live(edge)` and filtered `LIVE SELECT * FROM to WHERE out = agent:a1`. Notification is a normal `CREATE` carrying the full edge record (non-empty). LIVE-on-edge is a **usable contentless wake** — `await` is NOT poll-only. (Poll fallback still mandatory per store-ref §10, unchanged.)
- **PROBE 2 VERDICT — error shape UNCHANGED.** In-flight socket drop → **6/6 awaits raise raw `builtins.KeyError(<request-uuid>)`** (not `CancelledError`); next call → `websockets.exceptions.ConnectionClosedError`. Store-ref lines ~409-411 hold on the live engine.
- Deviations: (1) live server is **surrealdb-3.2.4**, not 3.2.1 (brief + MEMORY.md + store-ref §9 image pin all say 3.2.1) — probes run on 3.2.4. (2) the JSON `latency_to_first_s` is a **drain-grace artifact** (0.4s × queue index), NOT a notify latency — notifications were already enqueued when each write's await returned (sub-write-RTT); true latency not isolated. (3) my version-check leaked 2 `probe_meta_*` DBs — reaped post-hoc; only `:18000` touched.
- Packages considered: **surrealdb-py 2.0.0** — READ the installed `async_ws.py` source to derive the drop mechanism + LIVE transport; verdict `keep` (it is the project SDK). No new mechanism specified — read-only probe.
- Graded: N/A-code — verdicts measure LIVE store behavior `surrealdb-3.2.4+20260803.93ab219`, version-stamped, not a repo sha · HEAD-at-report `ee1d19a` · branch `feat/surreal-unification`.
- Decisions-needed: none blocking. Recommend 3 store-reference doc edits (flagged §"Flagged edits", out of my writable set) + operator awareness of the 3.2.1→3.2.4 store drift.
- Receipt pointers: script verbatim §"Probe script" (also `~/probe-await-05a-scratch/probe_await.py`, throwaway) · raw run `~/probe-await-05a-scratch/run.out` · lore memory `bef131a1-139c-550b-b4aa-bfbd403af390`.

---

## Environment (measured)
- Store: **spike-surreal, TEST**, `ws://127.0.0.1:18000/rpc`. I NEVER connected to `:18500` (production).
- Server version (via `connection.version()`): **`surrealdb-3.2.4+20260803.93ab219`**.
- SDK: `surrealdb` **2.0.0** (`/home/ejprice/PycharmProjects/lore/.venv/.../surrealdb/__init__.py`).
- Throwaway DBs under namespace `probe_ns`, minted `probe_await_p{1,2}_<uuid4>` / `probe_meta_<uuid4>`, all reaped. Left untouched: pre-existing `probe_limit_db` and `x` (not mine).
- Idiom mirrored from the real codebase (read, not copied): connection/bootstrap = `loremaster.store._txn.bootstrap_session` + `signin_credentials`; edge shape = `surreal_schema._define_relation_table` (`TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL`); RELATE = `loremaster.briefs._relate_briefed` (`RELATE $from->edge->$to SET …`, endpoints bound `RecordID`); LIVE transport = `loremaster.scout.CommandSubscriber` (`query("LIVE SELECT … WHERE …")` + `subscribe_live(uuid)`, and whole-table `.live(table)`).

---

## PROBE 1 — Does an edge-table LIVE SELECT fire on `RELATE`?
Settles store-reference §10 line ~819: *"[UNVERIFIED] Does an edge-table LIVE SELECT fire on RELATE? Never probed."*

### DDL / setup (verbatim)
```surql
DEFINE TABLE OVERWRITE message TYPE NORMAL SCHEMALESS
DEFINE TABLE OVERWRITE agent   TYPE NORMAL SCHEMALESS
DEFINE TABLE OVERWRITE to TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL
DEFINE FIELD note ON to TYPE option<string>
DEFINE TABLE OVERWRITE probe_node TYPE NORMAL SCHEMALESS
CREATE message:m1 SET body='hi'  ;  CREATE message:m2 SET body='bye'
CREATE agent:a1  SET name='alpha';  CREATE agent:a2  SET name='bravo'
```
- The edge table `to` (message→to→agent), named exactly as the comms edge, parsed **unquoted** with no issue.
- Three subscriptions established, **no establishment error** (`establish_errors: {}`):
  - **L1** whole-table on the edge: `await connection.live("to")`.
  - **L2** filtered on the edge: `await connection.query("LIVE SELECT * FROM to WHERE out = agent:a1")` (literal inlined per store-ref §10 — params ignored in a LIVE WHERE) + a raw capture queue.
  - **L3** whole-table on a NORMAL node table `probe_node` — the **positive mechanism control**.

### Results (verbatim payloads; full JSON in `run.out`)

| Phase | Write | L1 whole-table edge | L2 filtered `out=agent:a1` | L3 node (control) |
|---|---|---|---|---|
| A · positive control | `CREATE probe_node:c1` | — | — | **FIRES** `action=CREATE`, payload `{id, v:1}` |
| B · **core** | `RELATE m1->to->a1` | **FIRES** `action=CREATE` | **FIRES** `action=CREATE` | — |
| C · spurious control | `RELATE m2->to->a2` | **FIRES** `action=CREATE` | **does NOT fire** ✅ | — |
| D · negative control | `UPDATE message:m1` (node) | **does NOT fire** ✅ | **does NOT fire** ✅ | — |
| E · edge UPDATE | `UPDATE <a1-edge> SET note='wake2'` | **FIRES** `action=UPDATE` | **FIRES** `action=UPDATE` | — |

Phase B core notification (verbatim, full edge record — **not empty**):
```json
{ "action": "CREATE",
  "result": { "id": "RecordID(to:jnqtx26ug5zk6tk6jqe2)", "in": "RecordID(message:m1)",
              "note": "wake", "out": "RecordID(agent:a1)" } }
```
(scout consumes via `subscribe_live`, whose generator yields only `notification["result"]` — so the `action` shown here is present on the wire but invisible to scout; the wake is contentless *as scout uses it*.)

### Controls — why the verdict is trustworthy, not a harness artifact
- **Positive (A):** the identical capture harness DID deliver a notification for a known-good case (node CREATE). So a "no-fire" anywhere is a real no-fire, not a broken probe.
- **Spurious (C):** the filtered L2 (`out=agent:a1`) stayed silent for a `RELATE` whose `out=agent:a2` — the WHERE genuinely discriminates on the edge's `out` column; it is not firing on everything.
- **Negative (D):** neither edge subscription fired on an unrelated node write — edge LIVE is scoped to the edge table.

### VERDICT — **FIRES.**
An edge-table LIVE SELECT fires on `RELATE` on 3.2.4, in **both** forms the design might use (whole-table and filtered-`WHERE out=<recipient literal>`), delivering a normal `CREATE` notification carrying the full edge record. The design's "empty-payload-safe / contentless wake" assumption is satisfied (the payload is in fact non-empty, but harmless — scout ignores it). **LIVE-on-edge is a usable WAKE for `await`; `await` is not forced to be poll-only.**
Corollary confirmed: an edge **UPDATE** re-fires the whole-table subscription (`action=UPDATE`, Phase E) — the exact "re-dispatch storm" the `CommandSubscriber` docstring cites as its reason for using a filtered LIVE rather than `.live(table)`. If `await`'s wake edge is ever UPDATEd after creation, the same caution applies.

### Poll-fallback implication (honest)
The probe UPGRADES LIVE-on-edge from an unverified assumption to a verified usable wake — it is **not** poll-only. It does **not** remove the poll fallback: store-ref §10 already mandates one regardless (LIVE is best-effort, single-node only #5070, no replay on reconnect, and the SDK silently orphans `live_queues` on a socket drop). `await` should therefore be **LIVE-primary + poll-fallback**, the same shape `CommandSubscriber` already implements — now with empirical backing that the LIVE leg actually fires.

### Instrument bound (stated, not hidden)
The JSON field `latency_to_first_s` (0.40s in B/L1, 0.80s in B/L2, etc.) is **not** a notification latency. `fire_and_watch` records `recv_at` only after `drain()` finishes its greedy tail-drain (a 0.4s `wait_for` grace per queue), so the number is `0.4s × queue-index`, an artifact of the instrument. What IS true: every expected notification was already sitting in its queue by the time the triggering write's `await` returned, i.e. it arrived within the write's own commit round-trip (sub-second, localhost). True notify latency was not separately isolated — and does not affect the fires/does-not-fire verdict, which is all the design needs.

---

## PROBE 2 — Socket-drop-in-flight error shape on 3.2.4
Re-confirms store-reference lines ~409-411 (originally [PROBED] on an earlier engine): *"A socket drop with queries in flight surfaces a raw `builtins.KeyError(uuid)` from SDK 2.0.0's response routing … not `CancelledError`. The next call heals via `ConnectionClosedError`. Classify `KeyError` tightly, at the SDK-await boundary only."*

### Method
1. Open a connection; `CREATE agent:a1`.
2. Fire **6 concurrent** `connection.query("SLEEP 2s")` — genuinely in flight (`pending_futures_before_drop = 6`, read off `connection.qry`).
3. Drop the socket underneath them abruptly: **`connection.socket.transport.abort()`** (an RST-like drop, no close handshake; `connection.socket` is a websockets `ClientConnection`).
4. `gather(..., return_exceptions=True)` the 6 awaits; capture each exception verbatim.
5. Then issue one fresh `query("SELECT 1")` and capture its exception.

### Results (verbatim)
- `pending_futures_before_drop`: **6** · `drop_method`: `socket.transport.abort()` · `pending_futures_after_drop`: **0**.
- **All 6 in-flight awaits** raised (6/6):
  ```
  type: builtins.KeyError
  repr: KeyError('38297d2e-680c-4794-a014-7190b751954b')   # each a distinct request-message uuid
  args: ["'<request-uuid>'"]
  ```
- **Next call after drop:**
  ```
  type: websockets.exceptions.ConnectionClosedError
  repr: ConnectionClosedError(None, None, None)
  str:  no close frame received or sent
  ```

### Root cause (read from the SDK, confirmed by the probe)
In `surrealdb/connections/async_ws.py` (SDK 2.0.0): `_recv_task`'s `finally` runs `for fut … fut.cancel()` **then `self.qry.clear()`** synchronously; each `_send` has `finally: del self.qry[query_id]`. When the socket dies, `_recv_task` clears `self.qry` before the cancelled `_send` coroutines resume, so their `del self.qry[query_id]` raises **`KeyError(query_id)`** — masking the `CancelledError`. `query_id` is the request-message uuid, exactly what the 6 KeyErrors carry. The next `_send` finds `self.socket` still truthy (SDK doesn't null it), calls `self.socket.send()` on the dead socket → `ConnectionClosedError`.

### VERDICT — **error-shape-is-`KeyError(request-uuid)` in-flight, `ConnectionClosedError` next-call — UNCHANGED on 3.2.4.**
The classification the store reference mandates still holds. Note the shape is **SDK-side (surrealdb-py 2.0.0), engine-version-independent** — this is why the 3.1.5-era finding reproduces byte-for-shape on 3.2.4, and why it will keep holding until the SDK version changes. **Design consequence for `await`:** any awaited connection op in flight during a socket drop (including establishing/consuming a LIVE) surfaces this `KeyError`, so `await`'s wake/reconnect ladder must catch `KeyError` at the SDK-await boundary — exactly as `CommandSubscriber` already does (`(*_CONNECTION_ERRORS, KeyError)` in `run` / `_consume_live` / `_safe_close` / `_safe_kill`).

---

## Flagged edits (out of my writable set — docs/reference is not mine to change)
Recommended, for the operator/lead to apply to `docs/reference/surrealdb-31-capabilities.md`:
1. **§10, ~line 819** — replace the `[UNVERIFIED] Does an edge-table LIVE SELECT fire on RELATE? Never probed.` line with: *`[PROBED 2026-08-05, surrealdb-3.2.4]` An edge-table LIVE SELECT FIRES on `RELATE` — whole-table `.live(edge)` and filtered `LIVE SELECT * FROM <edge> WHERE out = <literal>` both deliver a normal `CREATE` notification carrying the full edge record `{id,in,out,fields}`; an edge UPDATE re-fires `action=UPDATE` on the whole-table form. Filtered `WHERE out=<literal>` discriminates correctly. Contentless-wake assumption holds. Poll fallback still mandatory (best-effort/no-replay).* (Receipt: this report + lore memory `bef131a1`.)
2. **§3, ~lines 409-411** — append: *`[RE-PROBED 2026-08-05 on 3.2.4: shape UNCHANGED — 6/6 in-flight awaits raise KeyError(request-uuid); next call ConnectionClosedError. Mechanism is SDK 2.0.0-side (_recv_task clears self.qry racing _send's del), engine-version-independent.]`*
3. **§9 OPS, ~line 846** — the image pin reads `docker.io/surrealdb/surrealdb:v3.2.1`, but the LIVE test store reports **3.2.4**. Also MEMORY.md and the brief say the stores are on **3.2.1**. Flagging the drift for an operator ruling: is the running container ahead of the pin, or is the pin stale? (Store-ref §9 is auto-cited by every store brief — a wrong version there mis-teaches.)

## Decisions needed
None block packet 05a. `await` = LIVE-primary + poll-fallback is empirically supported. The only open item is the operator's call on the 3.2.1→3.2.4 version drift (flag #3).

---

## Probe script (verbatim — throwaway, at `~/probe-await-05a-scratch/probe_await.py`; pasted here per brief-base §1 so the instrument survives its scratch dir)
```python
"""Build-time probe for lore packet 05a — settles two empirical store questions
the `await` design depends on, against the TEST store (spike-surreal) ONLY.

PROBE 1: Does an edge-table LIVE SELECT fire on RELATE? (whole-table + filtered
         LIVE-WHERE forms), with a positive mechanism control + spurious/negative
         controls.
PROBE 2: Socket-drop-in-flight error shape on the live engine (re-confirm the
         KeyError(uuid) vs ConnectionClosedError classification from the store
         reference, lines ~409-411).

⚠ Points at ws://127.0.0.1:18000/rpc (TEST) ONLY. Throwaway DBs, reaped at end.
Mirrors the project's real idiom: AsyncSurreal + signin dict + DEFINE NS / use /
DEFINE DB (loremaster.store._txn.bootstrap_session), the `to` edge shape
(message->to->agent, TYPE RELATION ENFORCED SCHEMAFULL, surreal_schema
._define_relation_table), the RELATE $from->edge->$to bound-RecordID form
(loremaster.briefs._relate_briefed), and the filtered LIVE-WHERE +
subscribe_live transport (loremaster.scout.CommandSubscriber).
"""

from __future__ import annotations

import asyncio
import time
import traceback
import uuid
from typing import Any

from surrealdb import AsyncSurreal, RecordID

URL = "ws://127.0.0.1:18000/rpc"  # TEST store. NEVER :18500.
USER = "root"
PASS = "spikeroot"
NS = "probe_ns"


def exc_shape(error: BaseException) -> dict[str, Any]:
    """Verbatim, greppable exception shape."""
    return {
        "type": f"{type(error).__module__}.{type(error).__qualname__}",
        "repr": repr(error),
        "args": [repr(a) for a in getattr(error, "args", ())],
        "str": str(error),
    }


async def connect(db: str) -> Any:
    """AsyncSurreal + signin + bootstrap NS/DB — mirrors bootstrap_session."""
    connection = AsyncSurreal(URL)
    await connection.signin({"username": USER, "password": PASS})
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {NS}")
    await connection.use(NS, db)
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {db}")
    return connection


def register_raw_queue(connection: Any, live_uuid: Any) -> "asyncio.Queue[dict[str, Any]]":
    """Append a raw capture queue to the SDK's live_queues for this uuid.

    _recv_task feeds every registered queue the FULL notification object
    (``{"id", "action", "result"}``). scout consumes via ``subscribe_live``,
    whose generator yields only ``notification["result"]`` (the payload) — so
    the ``action`` is present on the wire but invisible to scout. We capture the
    full object to document the shape.
    """
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    connection.live_queues.setdefault(str(live_uuid), []).append(queue)
    return queue


async def drain(queue: "asyncio.Queue[dict[str, Any]]", first_timeout: float) -> list[dict[str, Any]]:
    """Collect every notification arriving within a window (first waits up to
    ``first_timeout``; then greedily drains the tail with a short grace)."""
    items: list[dict[str, Any]] = []
    try:
        items.append(await asyncio.wait_for(queue.get(), first_timeout))
    except asyncio.TimeoutError:
        return items
    while True:
        try:
            items.append(await asyncio.wait_for(queue.get(), 0.4))
        except asyncio.TimeoutError:
            break
    return items


async def fire_and_watch(
    action_coro: Any,
    watches: list[tuple[str, "asyncio.Queue[dict[str, Any]]", bool]],
    fire_timeout: float = 3.0,
    nofire_timeout: float = 1.5,
) -> dict[str, Any]:
    """Fire one write, then collect from each watched queue.

    ``watches`` = list of (label, queue, expected_to_fire). Latency is measured
    from just-before-the-write to first-notification (so it INCLUDES the write's
    own commit round-trip — an upper bound on pure notify latency).
    NOTE (added in the report, not the code): this number is dominated by
    drain()'s 0.4s tail grace per queue and is NOT a real notify latency.
    """
    fired_at = time.monotonic()
    write_result = await action_coro
    out: dict[str, Any] = {"write_result": _safe(write_result), "watches": {}}
    for label, queue, expected in watches:
        timeout = fire_timeout if expected else nofire_timeout
        items = await drain(queue, timeout)
        recv_at = time.monotonic()
        out["watches"][label] = {
            "expected_fire": expected,
            "fired": bool(items),
            "count": len(items),
            "latency_to_first_s": round(recv_at - fired_at, 4) if items else None,
            "notifications": [_safe(i) for i in items],
        }
    return out


def _safe(value: Any) -> Any:
    """Render RecordID / arbitrary objects to stable strings for the report."""
    if isinstance(value, RecordID):
        return f"RecordID({value.table_name}:{value.id})"
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    return value


async def probe_1() -> dict[str, Any]:
    db = f"probe_await_p1_{uuid.uuid4().hex}"
    report: dict[str, Any] = {"db": db, "phases": {}, "establish_errors": {}}
    connection = await connect(db)
    try:
        # --- schema: node tables, the `to` edge (RELATION/ENFORCED), a plain node control
        await connection.query("DEFINE TABLE OVERWRITE message TYPE NORMAL SCHEMALESS")
        await connection.query("DEFINE TABLE OVERWRITE agent TYPE NORMAL SCHEMALESS")
        await connection.query(
            "DEFINE TABLE OVERWRITE to TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL"
        )
        await connection.query("DEFINE FIELD note ON to TYPE option<string>")
        await connection.query("DEFINE TABLE OVERWRITE probe_node TYPE NORMAL SCHEMALESS")
        await connection.query("CREATE message:m1 SET body='hi'")
        await connection.query("CREATE message:m2 SET body='bye'")
        await connection.query("CREATE agent:a1 SET name='alpha'")
        await connection.query("CREATE agent:a2 SET name='bravo'")

        # --- L3: whole-table LIVE on a NORMAL node table (POSITIVE MECHANISM CONTROL)
        node_uuid = await connection.live("probe_node")
        q3 = register_raw_queue(connection, node_uuid)
        report["phases"]["A_positive_control_node_create"] = await fire_and_watch(
            connection.query("CREATE probe_node:c1 SET v=1"),
            [("L3_node_wholetable", q3, True)],
        )

        # --- L1: whole-table LIVE on the EDGE table
        try:
            edge_whole_uuid = await connection.live("to")
            q1 = register_raw_queue(connection, edge_whole_uuid)
        except Exception as error:  # noqa: BLE001
            report["establish_errors"]["L1_edge_wholetable"] = exc_shape(error)
            q1 = None
        # --- L2: filtered LIVE-WHERE on the EDGE table (inlined literal, per store ref)
        try:
            edge_filtered_uuid = await connection.query(
                "LIVE SELECT * FROM to WHERE out = agent:a1"
            )
            q2 = register_raw_queue(connection, edge_filtered_uuid)
        except Exception as error:  # noqa: BLE001
            report["establish_errors"]["L2_edge_filtered_where"] = exc_shape(error)
            q2 = None

        watches_both: list[tuple[str, Any, bool]] = []
        if q1 is not None:
            watches_both.append(("L1_edge_wholetable", q1, True))
        if q2 is not None:
            watches_both.append(("L2_edge_filtered_out_eq_a1", q2, True))

        # --- CORE: RELATE a matching edge (out = agent:a1) — the design's wake trigger
        report["phases"]["B_core_relate_matching"] = await fire_and_watch(
            connection.query(
                "RELATE $f->to->$t SET note='wake'",
                {"f": RecordID("message", "m1"), "t": RecordID("agent", "a1")},
            ),
            watches_both,
        )

        # --- SPURIOUS control: RELATE non-matching out (a2). L1 should fire; L2 must NOT.
        spurious: list[tuple[str, Any, bool]] = []
        if q1 is not None:
            spurious.append(("L1_edge_wholetable", q1, True))
        if q2 is not None:
            spurious.append(("L2_edge_filtered_out_eq_a1", q2, False))
        report["phases"]["C_spurious_relate_nonmatching_out_a2"] = await fire_and_watch(
            connection.query(
                "RELATE $f->to->$t SET note='other'",
                {"f": RecordID("message", "m2"), "t": RecordID("agent", "a2")},
            ),
            spurious,
        )

        # --- NEGATIVE control: unrelated node write. Neither edge sub should fire.
        negative: list[tuple[str, Any, bool]] = []
        if q1 is not None:
            negative.append(("L1_edge_wholetable", q1, False))
        if q2 is not None:
            negative.append(("L2_edge_filtered_out_eq_a1", q2, False))
        report["phases"]["D_negative_unrelated_node_update"] = await fire_and_watch(
            connection.query("UPDATE message:m1 SET body='changed'"),
            negative,
        )

        # --- EXTRA: UPDATE an existing matching edge — does whole-table re-fire (re-dispatch
        #     storm risk the scout docstring cites)? Does the filtered sub re-fire?
        update_watch: list[tuple[str, Any, bool]] = []
        if q1 is not None:
            update_watch.append(("L1_edge_wholetable", q1, True))
        if q2 is not None:
            update_watch.append(("L2_edge_filtered_out_eq_a1", q2, True))
        report["phases"]["E_update_existing_matching_edge"] = await fire_and_watch(
            _update_first_edge(connection),
            update_watch,
        )
    finally:
        try:
            for uid in list(connection.live_queues.keys()):
                try:
                    await connection.kill(uid)
                except Exception:  # noqa: BLE001
                    pass
        finally:
            await connection.close()
        # reap via a fresh admin connection (independent of the probe's own)
        admin = await connect(db)
        await admin.query(f"REMOVE DATABASE IF EXISTS {db}")
        await admin.close()
    return report


async def _update_first_edge(connection: Any) -> Any:
    """UPDATE the matching (out=agent:a1) edge in place, to test edge-UPDATE firing."""
    rows = await connection.query("SELECT id FROM to WHERE out = agent:a1")
    edge_id = rows[0]["id"] if rows else None
    return await connection.query("UPDATE $edge SET note='wake2'", {"edge": edge_id})


async def probe_2() -> dict[str, Any]:
    db = f"probe_await_p2_{uuid.uuid4().hex}"
    report: dict[str, Any] = {"db": db}
    connection = await connect(db)
    try:
        await connection.query("CREATE agent:a1 SET name='alpha'")

        # sanity: SLEEP keeps a query genuinely in flight at the server
        report["sleep_available"] = True

        # --- IN-FLIGHT DROP: 6 concurrent SLEEP queries, abort the socket underneath them
        in_flight = 6
        tasks = [
            asyncio.ensure_future(connection.query("SLEEP 2s")) for _ in range(in_flight)
        ]
        await asyncio.sleep(0.4)  # let all 6 send; futures now pending at the server
        report["pending_futures_before_drop"] = len(connection.qry)

        socket = connection.socket
        report["socket_type"] = type(socket).__name__
        drop_method = None
        try:
            socket.transport.abort()  # abrupt drop (no close handshake) ~ a network RST
            drop_method = "socket.transport.abort()"
        except Exception:  # noqa: BLE001
            try:
                await socket.close()
                drop_method = "await socket.close()"
            except Exception as error:  # noqa: BLE001
                drop_method = f"FAILED: {exc_shape(error)}"
        report["drop_method"] = drop_method

        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        report["in_flight_count"] = in_flight
        report["in_flight_results"] = [
            exc_shape(r) if isinstance(r, BaseException) else {"NO_EXCEPTION": _safe(r)}
            for r in gathered
        ]
        report["pending_futures_after_drop"] = len(connection.qry)

        # --- NEXT CALL after the drop (store ref: "heals via ConnectionClosedError")
        await asyncio.sleep(0.2)
        try:
            r = await connection.query("SELECT 1")
            report["next_call_after_drop"] = {"NO_EXCEPTION": _safe(r)}
        except BaseException as error:  # noqa: BLE001
            report["next_call_after_drop"] = exc_shape(error)
    finally:
        try:
            await connection.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            admin = await connect(db)
            await admin.query(f"REMOVE DATABASE IF EXISTS {db}")
            await admin.close()
        except Exception as error:  # noqa: BLE001
            report["reap_error"] = exc_shape(error)
    return report


async def main() -> None:
    import json

    header = {}
    probe = await connect(f"probe_meta_{uuid.uuid4().hex}")
    try:
        header["server_version"] = await probe.version()
    finally:
        await probe.close()
    print("=" * 78)
    print("SERVER:", header["server_version"], "| URL:", URL, "(TEST store)")
    print("=" * 78)

    p1 = await probe_1()
    print("\n########## PROBE 1 — edge-table LIVE on RELATE ##########")
    print(json.dumps(p1, indent=2, default=str))

    p2 = await probe_2()
    print("\n########## PROBE 2 — socket-drop-in-flight error shape ##########")
    print(json.dumps(p2, indent=2, default=str))

    print("\n########## MACHINE-SUMMARY ##########")
    print(json.dumps({"server": header, "probe1": p1, "probe2": p2}, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
```
(Known cosmetic: `import traceback` is unused — throwaway probe, left as-is.)
