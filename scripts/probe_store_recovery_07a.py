"""Packet 07a (store RECOVERY/DEGRADATION) — LIVE bounce-recovery probe of the
REAL ``SurrealStore`` connection path against a FULL server restart.

WHY THIS EXISTS. Findings #164 (2026-07-22) and #250 (its 2026-07-27 production
reproduction) report that a store bounce WEDGES lore-lore's held SurrealDB
connection: the next TWO calls both failed with
``no close frame received or sent`` and did NOT self-heal; only a
``podman restart lore-lore`` fixed it. Both findings pre-date substantial seam
evolution (packet 05a-ii's ``_SDK_AWAIT_BOUNDARY_ERRORS``, the KeyError branch in
``run_query`` / ``_txn_query_raw``). This probe re-grounds the wedge shape on the
CURRENT code against the CURRENT engine, so 07a's fixtures are grounded in
2026-08-17 truth rather than a July inference.

The observed #164/#250 message ``SurrealDB query failed against '…': no close
frame received or sent`` is EXACTLY ``run_query``'s ``SurrealConnectionError``
wording — so the self-heal (``drop`` → null the cached handle) DID fire, yet the
NEXT call still died on ``connection.query()``. The decisive question this probe
isolates: after a full server restart (server gone → back), does

  (A) a brand-NEW SurrealStore (fresh object, fresh socket) connect+query? and
  (B) the OLD long-held SurrealStore's next _query() self-heal, and in how many
      calls?

If (A) works but (B) wedges, the fault is per-store reconnect. If (A) ALSO wedges,
the fault is process/SDK-level (which is what ``podman restart lore-lore`` — a
fresh PROCESS — fixing it implies). A control leg (no bounce) proves the probe can
see a healthy store; a NEGATIVE-CONTROL leg (self-heal disabled → the drill must report a
WEDGE) proves the drill can DETECT a wedge and is not vacuously green (adversary Exp B / F3).

⚠ SCOPE OF THE DRILL (adversary F1): the full-bounce drill exercises the IDLE / connection-close
(pre-send) shape — the next query raises `ConnectionClosedError` ("no close frame received or
sent", a `WebSocketException` in `_CONNECTION_ERRORS`), driving drop→reconnect. It does NOT
exercise the in-flight-`KeyError` branch of `run_query`/`_txn_query_raw`'s literal
`except (*_CONNECTION_ERRORS, KeyError)`; that branch is guarded by the SYNTHETIC unit tests
`TestQuerySeamSdkKeyErrorClassification` / `TestTxnSdkKeyErrorClassification`, not by this drill.

Committed here (``scripts/``) rather than a scratchpad per brief-base §1: an
instrument that establishes a load-bearing claim is a deliverable.

Targets ONLY spike-surreal (ws://127.0.0.1:18000). It RESTARTS that TEST store
(``systemctl --user restart spike-surreal.service``). It refuses to run against
:18500 (production lore-surreal) by construction.

Usage:
    cd loremaster && uv run python ../scripts/probe_store_recovery_07a.py
"""

from __future__ import annotations

import asyncio
import sys
import traceback
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "loremaster"))

from loremaster.store._txn import signin_credentials  # noqa: E402
from loremaster.store.surreal import SurrealStore  # noqa: E402
from pydantic import SecretStr  # noqa: E402
from surrealdb import AsyncSurreal  # noqa: E402

URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = SecretStr("spikeroot")
NAMESPACE = "lore_test"
SERVICE = "spike-surreal.service"

# Hard guard: NEVER touch production (:18500) — a test store bounce is authorised,
# a production one is a firing offence (store reference §9).
assert ":18000" in URL and ":18500" not in URL, "probe must target the TEST store only"


def _unique_database() -> str:
    return f"probe07a_{uuid.uuid4().hex}"


def _exc_shape(error: BaseException) -> str:
    """A one-line, greppable exception fingerprint: type + MRO tail + message."""
    mro = " <- ".join(t.__name__ for t in type(error).__mro__[:5])
    return f"{type(error).__module__}.{type(error).__name__} [{mro}]: {error}"


async def _make_store() -> SurrealStore:
    return SurrealStore(
        url=URL,
        namespace=NAMESPACE,
        database=_unique_database(),
        dim=1024,
        user=USER,
        password=PASSWORD,
    )


async def _query_once(store: SurrealStore, statement: str) -> tuple[bool, str]:
    """Run one _query; return (ok, detail). Never raises."""
    try:
        result = await store._query(statement)
        return True, f"OK -> {result!r}"
    except BaseException as error:  # noqa: BLE001 — the probe records EVERYTHING
        return False, _exc_shape(error)


async def _restart_server() -> None:
    # reset-failed first: systemd rate-limits unit restarts (StartLimitBurst=5 /
    # StartLimitIntervalSec=10s by default), which a tight 20-consecutive drill trips.
    # reset-failed clears the burst counter so each bounce is a genuine full restart.
    reset = await asyncio.create_subprocess_exec(
        "systemctl", "--user", "reset-failed", SERVICE,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    await reset.communicate()
    proc = await asyncio.create_subprocess_exec(
        "systemctl", "--user", "restart", SERVICE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    print(f"    [systemctl restart rc={proc.returncode}] "
          f"{(out or b'').decode().strip()} {(err or b'').decode().strip()}")


async def _wait_server_back(max_seconds: float = 60.0) -> float:
    """Poll a FRESH connection until the server answers. Returns seconds waited.

    This separates 'the server is back' from 'the held store recovered' — the
    exact conflation #250 could not rule out ('whether a longer wait would have
    healed it — nobody waited minutes')."""
    started = asyncio.get_event_loop().time()
    attempt = 0
    while True:
        attempt += 1
        try:
            connection = AsyncSurreal(URL)
            await connection.signin(signin_credentials(user=USER, password=PASSWORD))
            await connection.query("INFO FOR ROOT")
            await connection.close()
            waited = asyncio.get_event_loop().time() - started
            print(f"    [server back after {waited:.2f}s, {attempt} fresh-connect attempts]")
            return waited
        except BaseException as error:  # noqa: BLE001
            if asyncio.get_event_loop().time() - started > max_seconds:
                print(f"    [server DID NOT come back within {max_seconds}s: "
                      f"{_exc_shape(error)}]")
                raise
            await asyncio.sleep(0.5)


async def scenario_control() -> None:
    print("\n" + "=" * 78)
    print("CONTROL — no bounce: a healthy held store answers repeated queries")
    print("=" * 78)
    store = await _make_store()
    try:
        for i in range(3):
            ok, detail = await _query_once(store, "RETURN 1")
            print(f"  call {i}: ok={ok}  {detail}")
    finally:
        await store.close()


async def scenario_idle_bounce() -> None:
    print("\n" + "=" * 78)
    print("SCENARIO 1 — IDLE-then-full-bounce (#164/#250 shape): held store idle,")
    print("  server RESTARTED, then repeated _query() calls. Does it self-heal, "
          "and in how many calls?")
    print("=" * 78)
    held = await _make_store()
    # Establish + cache the connection.
    ok, detail = await _query_once(held, "RETURN 1")
    print(f"  pre-bounce call: ok={ok}  {detail}")
    print(f"  held._connection is set: {held._connection is not None}")

    print("  --- bouncing spike-surreal (full server restart) ---")
    await _restart_server()
    await _wait_server_back()

    # (A) A brand-new store from the SAME process — isolates process/SDK-level wedge.
    print("  (A) fresh SurrealStore (same process) after the bounce:")
    fresh = await _make_store()
    try:
        ok_a, detail_a = await _query_once(fresh, "RETURN 1")
        print(f"      fresh-store call: ok={ok_a}  {detail_a}")
    finally:
        await fresh.close()

    # (B) The OLD held store — does its next _query self-heal?
    print("  (B) OLD held store's next calls (self-heal test):")
    heal_call = None
    for i in range(8):
        conn_before = held._connection is not None
        ok_b, detail_b = await _query_once(held, "RETURN 1")
        conn_after = held._connection is not None
        print(f"      call {i}: ok={ok_b}  conn[{conn_before}->{conn_after}]  {detail_b}")
        if ok_b and heal_call is None:
            heal_call = i
        await asyncio.sleep(0.5)
    print(f"  ==> held store healed on call index: {heal_call} "
          f"(None = never healed within 8 calls = WEDGE reproduced)")
    await held.close()


async def scenario_inflight_bounce() -> None:
    print("\n" + "=" * 78)
    print("SCENARIO 2 — IN-FLIGHT bounce: a query racing the socket drop")
    print("  (store reference §3 KeyError shape). Records the raw exception, then")
    print("  the same self-heal test.")
    print("=" * 78)
    held = await _make_store()
    ok, detail = await _query_once(held, "RETURN 1")
    print(f"  pre-bounce call: ok={ok}  {detail}")

    # Fire a slow-ish query concurrently with the restart so the drop lands in flight.
    async def _slow_query() -> tuple[bool, str]:
        return await _query_once(held, 'RETURN sleep("1500ms")')

    print("  --- launching in-flight query, then bouncing mid-flight ---")
    task = asyncio.ensure_future(_slow_query())
    await asyncio.sleep(0.2)
    await _restart_server()
    ok_if, detail_if = await task
    print(f"  in-flight query result: ok={ok_if}  {detail_if}")
    await _wait_server_back()

    print("  next calls (self-heal test):")
    heal_call = None
    for i in range(8):
        ok_b, detail_b = await _query_once(held, "RETURN 1")
        print(f"      call {i}: ok={ok_b}  {detail_b}")
        if ok_b and heal_call is None:
            heal_call = i
        await asyncio.sleep(0.5)
    print(f"  ==> healed on call index: {heal_call} (None = wedge)")
    await held.close()


async def scenario_20_consecutive() -> None:
    """The packet's mandated drill: bounce the store 20 times in a row against ONE
    long-held store; each bounce must recover WITHOUT a container restart. Record
    the heal-call index per bounce (a single '1' means one sacrificed call then heal;
    'None' within a bounded 5-call window means a real wedge)."""
    print("\n" + "=" * 78)
    print("DRILL — 20-consecutive full bounces on ONE long-held store (recover w/o")
    print("  a container restart). heal-index per bounce; control before + after.")
    print("=" * 78)
    held = await _make_store()
    ok, detail = await _query_once(held, "RETURN 1")
    print(f"  control-before: ok={ok}  {detail}")
    heal_indices: list[int | None] = []
    for bounce in range(20):
        await _restart_server()
        await _wait_server_back()
        heal_at: int | None = None
        for i in range(5):  # bounded window: >1 sacrificed call is a regression to flag
            ok_b, _ = await _query_once(held, "RETURN 1")
            if ok_b:
                heal_at = i
                break
        heal_indices.append(heal_at)
        print(f"  bounce {bounce:2d}: heal-index={heal_at}")
    ok, detail = await _query_once(held, "RETURN 1")
    print(f"  control-after: ok={ok}  {detail}")
    await held.close()
    healed = [h for h in heal_indices if h is not None]
    wedged = [i for i, h in enumerate(heal_indices) if h is None]
    print(f"\n  SUMMARY: {len(healed)}/20 recovered without a container restart; "
          f"heal-index set={sorted(set(healed))}; wedged bounces={wedged}")
    print(f"  ==> {'PASS — 20/20 self-healed' if len(healed) == 20 else 'FAIL — a wedge reproduced'}")


async def scenario_negative_control() -> int:
    """NEGATIVE CONTROL (a probe needs a control) — the drill's own self-test.

    The 20x drill above claims "the store recovers". A drill that ALWAYS prints PASS
    (or whose heal detection rots) would print exactly the same thing on a broken
    store — so the 20/20 is worthless UNLESS the drill can also REPORT a wedge. Here
    we DISABLE the self-heal (patch ``_drop_connection`` to a no-op, so a dead cached
    handle is NEVER nulled — #164's "never re-establishes the session" shape) and
    require the SAME recovery loop to WEDGE. This is the contract-adversary's Exp B
    (REPORT-adversary-07a-1.md §Findings F3 / §Probe record), committed as a permanent
    leg so the committed transcript carries both a positive (20/20) and a negative
    (0/N wedged) result. Returns a process exit code (0 = the negative control held).
    """
    print("\n" + "=" * 78)
    print("NEGATIVE CONTROL — self-heal DISABLED (_drop_connection no-op): the drill")
    print("  MUST now report a WEDGE (proving it can DETECT one; not vacuously green).")
    print("=" * 78)
    held = await _make_store()
    ok, detail = await _query_once(held, "RETURN 1")
    print(f"  control-before: ok={ok}  {detail}")

    async def _noop_drop(connection: object) -> None:
        # wedge injection: the dead cached handle is never nulled, so the next
        # _ensure_connection returns the SAME dead socket and the store can never heal.
        return None

    held._drop_connection = _noop_drop  # type: ignore[method-assign]
    await _restart_server()
    await _wait_server_back()
    heal_at: int | None = None
    for i in range(5):
        ok_b, _ = await _query_once(held, "RETURN 1")
        if ok_b:
            heal_at = i
            break
    await held.close()
    wedged = heal_at is None
    print(f"  with self-heal disabled: heal-index={heal_at} (None = wedged, as REQUIRED)")
    if wedged:
        print("  ==> PASS — the drill DETECTS a wedge; its 20/20 above is a real signal.")
        return 0
    print("  ==> FAIL — the drill is NOT discriminating: it healed with the drop "
          "DISABLED, so its PASS means nothing. Fix the drill before trusting it.")
    return 1


async def main() -> int:
    print("packet 07a store-recovery probe — spike-surreal 3.2.4 (TEST store only)")
    print(f"URL={URL}")
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "basic"):
        await scenario_control()
        await scenario_idle_bounce()
        await scenario_inflight_bounce()
    rc = 0
    if mode in ("all", "drill"):
        await scenario_20_consecutive()
        # The negative control is REQUIRED whenever the drill runs — a positive-only
        # drill is a gate with no control (adversary F3).
        rc = await scenario_negative_control()
    print("\nDONE.")
    return rc


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except BaseException:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)
