"""Packet 58 am-17 §14: what the cycle guard's ONE input costs — the re-open instrument of
``TASK_GUARD_GRAPH_LARGE_ROWS`` (a boot that emits ``task.guard.graph_large`` re-runs this at that size).

Ported from am-17 §INSTRUMENT-4 to the BUILT code (close-out fix-up, finding #641): the bounded closure
legs are gone with ``_bounded_dependency_graph``; the guard's read is ``TaskLedger._read_dependency_graph``.

For a task table of N dependency-bearing rows (N dependents of one hub, the real schema), TEST store only:
  full    ``TaskLedger._read_dependency_graph()`` — the four cycle-guarded writers' one input
  mirror  the boot's ``TaskLedger._read_mirror_state()`` (the column read plus the whole ``blocks`` edge read)
  scc     ``find_row_blocked_by_cycles`` over the full graph for one proposed row, in memory
Controls (each line prints ``ok`` or ``CONTROL FAILED``, and any failure exits 1):
  full returns exactly N rows (the hub's column is empty, so it is not one);
  scc finds no cycle for ``newrow -> d0``, and finds one once ``hub -> newrow`` is added
  (``newrow -> d0 -> hub -> newrow``).

Run from the repo root: ``uv run python scripts/probe_guard_input_58.py 300 20000 [--tests-dir <dir>]``.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import sys
import time
from pathlib import Path
from typing import Any

from probe_hub_txn_58 import URL

#: Dependents seeded per transaction, so no one seeding transaction is huge (§INSTRUMENT-4's slice).
SEED_SLICE = 4000
HUB_ID = "hubx"
NEW_ROW_ID = "newrow"
DEFAULT_TESTS_DIRECTORY = Path(__file__).resolve().parents[1] / "loremaster" / "tests"


def _import_test_helpers(tests_directory: Path) -> tuple[Any, Any]:
    """The suite's real-SurrealDB harness and the packet 58 seeding helpers, from ``tests_directory``."""
    directory = str(tests_directory.resolve())
    if directory not in sys.path:
        sys.path.insert(0, directory)
    import _reanchor_58_support
    import _surreal_harness

    return _surreal_harness, _reanchor_58_support


async def _timed(awaitable: Any) -> tuple[float, Any]:
    """Wall seconds and the result, or the exception's name and text (a probe reports what it saw)."""
    started = time.monotonic()
    try:
        result = await awaitable
    except Exception as error:  # noqa: BLE001 - a probe reports what it saw
        return time.monotonic() - started, f"RAISED {type(error).__name__}: {str(error)[:90]}"
    return time.monotonic() - started, result


def _control(label: str, holds: bool) -> bool:
    """Print one control's verdict; return whether it held."""
    print(f"  control {label}: {'ok' if holds else 'CONTROL FAILED'}", flush=True)
    return holds


async def probe(size: int, harness: Any, support: Any) -> bool:
    """One size: seed, run the three legs and their controls, drop the database.

    Returns True iff every control held.
    """
    from loremaster.tasks import find_row_blocked_by_cycles

    env = dataclasses.replace(
        harness.make_env(database=harness.unique_database(), dim=harness.PRODUCTION_DIM), url=URL
    )
    assert env.url == URL, "TEST store only"
    ledger = support.new_ledger(env)
    await ledger.ensure_ready()
    held = True
    try:
        await support.raw_seed_row(ledger, HUB_ID, blocked_by=[])
        dependents: list[str] = []
        while len(dependents) < size:
            step = min(SEED_SLICE, size - len(dependents))
            dependents += await support.bulk_seed_dependents(ledger, HUB_ID, step, f"d{len(dependents)}x")
        wall, graph = await _timed(ledger._read_dependency_graph())  # noqa: SLF001
        rows = len(graph) if isinstance(graph, dict) else graph
        print(f"N={size} full: {wall:.3f}s rows={rows}", flush=True)
        held &= _control("full returns N rows", rows == size)
        wall, _ = await _timed(ledger._read_mirror_state())  # noqa: SLF001
        print(f"N={size} mirror: {wall:.3f}s", flush=True)
        stored = dict(graph) if isinstance(graph, dict) else {}
        proposed = {NEW_ROW_ID: [dependents[0]]}
        started = time.monotonic()
        miss = find_row_blocked_by_cycles(stored, proposed, {NEW_ROW_ID}, all_or_nothing=True)
        scc_wall = time.monotonic() - started
        stored[HUB_ID] = [NEW_ROW_ID]
        hit = find_row_blocked_by_cycles(stored, proposed, {NEW_ROW_ID}, all_or_nothing=True)
        print(f"N={size} scc: {scc_wall:.3f}s acyclic_hits={len(miss)} control_hits={len(hit)}", flush=True)
        held &= _control("scc finds nothing on the acyclic graph", not miss)
        held &= _control("scc finds the planted cycle", NEW_ROW_ID in hit)
    finally:
        await ledger.close()
        await harness.drop_database(env)
    return held


async def main(sizes: list[int], tests_directory: Path) -> int:
    """Every size in turn; exit 1 if any control failed."""
    harness, support = _import_test_helpers(tests_directory)
    results = [await probe(size, harness, support) for size in sizes]
    return 0 if all(results) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("sizes", nargs="+", type=int, help="dependency-bearing row counts, one run each")
    parser.add_argument(
        "--tests-dir",
        type=Path,
        default=DEFAULT_TESTS_DIRECTORY,
        help="the checkout's loremaster/tests directory (default: the one beside this script)",
    )
    arguments = parser.parse_args()
    sys.exit(asyncio.run(main(arguments.sizes, arguments.tests_dir)))
