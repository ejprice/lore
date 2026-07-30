"""Committed survey probe for finding #102 — measures the REPAIRED
``execute_transaction`` conflict-retry policy's per-mint attempt count and wall
latency against the REAL finding-counter mint shape, live, so the retry
policy's constants (``_TXN_CONFLICT_BACKOFF_BASE_SECONDS`` /
``_TXN_CONFLICT_BACKOFF_CAP_SECONDS`` / ``_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS``
in ``loremaster/loremaster/store/_txn.py``) are set FROM measurement, not
hand-waved.

Finding #102 exists precisely because a retry ladder tuned for 2-way
contention was never re-measured as callers grew to N-way — this script is
the instrument that stops the successor constants from repeating that mistake.

Drives the ACTUAL production seam: ``execute_transaction`` (imported, never
reimplemented) against a transaction fragment built by the REAL
``FindingLedger._report_fragment`` static method — byte-identical to what
``FindingLedger.report()`` sends in production — under N in {2, 8, 16, 32}
GENUINELY CONCURRENT racers, x 50 rounds each, all contending on the SAME
``finding_counter`` singleton row (the exact hot-row shape the finding mint
sees). Each racer gets its own real SDK connection (mirroring realistic
per-agent usage), wrapped only to COUNT ``query_raw`` calls — never to change
behaviour — so the attempt count reported is the seam's real attempt count,
not an estimate.

Targets ONLY spike-surreal (ws://127.0.0.1:18000). NEVER :18500 (production) —
mirrors the DEFAULT_URL/DEFAULT_PASS the test harness
(``loremaster/tests/_surreal_harness.py``) and prior probes
(``scratchpad/probe_sequence_txn_concurrency.py``) already use.

Usage:
    cd loremaster && uv run python ../scripts/survey_txn_contention_102.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "loremaster"))

from loremaster.findings import FindingLedger  # noqa: E402
from loremaster.stats import nearest_rank_percentile  # noqa: E402
from loremaster.store._txn import (  # noqa: E402
    TxnContentionExhaustedError,
    _SurrealConnection,
    compose,
    execute_transaction,
    signin_credentials,  # noqa: E402
)
from pydantic import SecretStr  # noqa: E402
from surrealdb import AsyncSurreal  # noqa: E402

URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = SecretStr("spikeroot")
NAMESPACE = "lore_test"

RACER_COUNTS: tuple[int, ...] = (2, 8, 16, 32)
ROUNDS_PER_RACER_COUNT = 50
PERCENTILES: tuple[int, ...] = (50, 90, 99)


def _unique_database() -> str:
    return f"survey102_{os.getpid()}_{uuid.uuid4().hex}"


async def _connect(database: str) -> _SurrealConnection:
    # ``AsyncSurreal`` is a FACTORY FUNCTION, not a class — annotating with it is a
    # ``valid-type`` error, and every attribute read off the result then reports as
    # missing. ``loremaster.store._txn._SurrealConnection`` is exactly the factory's
    # return union and is already the house alias for a live connection (#188).
    connection = AsyncSurreal(URL)
    # Through the ONE shared seam, not a hand-rolled copy of the payload (#211/#102).
    await connection.signin(signin_credentials(user=USER, password=PASSWORD))
    await connection.use(NAMESPACE, database)
    return connection


class _CountingConnection:
    """Wraps a real, signed-in SDK connection, counting ``query_raw`` calls —
    each one IS an ``execute_transaction`` attempt, so the count read back
    after a call is the seam's true attempt count for that call, no estimate.
    """

    def __init__(self, inner: _SurrealConnection) -> None:
        self._inner = inner
        self.calls = 0

    async def query_raw(self, statement: str, params: dict[str, Any]) -> Any:
        self.calls += 1
        return await self._inner.query_raw(statement, params)

    def check_response_for_error(self, response: Any, method: str) -> None:
        return self._inner.check_response_for_error(response, method)


@dataclass
class MintResult:
    attempts: int
    elapsed_seconds: float
    exhausted: bool


async def _one_mint(database: str) -> MintResult:
    """Drive ONE real finding-mint transaction (the exact production fragment
    shape) through the repaired ``execute_transaction`` over its own real
    connection, and report how many attempts/how long it took.
    """
    raw = await _connect(database)
    counting = _CountingConnection(raw)

    async def _acquire() -> _SurrealConnection:
        return counting  # type: ignore[return-value]

    async def _drop(_: object) -> None:
        raise AssertionError("a conflict must never drop a healthy connection")

    finding_id = uuid.uuid4().hex
    now = datetime.now(UTC)
    fragment = FindingLedger._report_fragment(  # noqa: SLF001 - the real production shape
        finding_id=finding_id,
        kind="friction",
        subject="txn-contention-102-survey",
        body="committed survey probe row — reaped at the end of the run",
        area="lore_txn_contention_survey",
        category="capability_gap",
        created_by="survey-102",
        created_at=now,
        provenance={"created_by": "survey-102", "created_at": now.isoformat(), "events": []},
        supersedes_id=None,
    )
    statement_text, params = compose(fragment)

    started = time.monotonic()
    exhausted = False
    try:
        await execute_transaction(
            statement_text, params, acquire=_acquire, drop=_drop, url=URL
        )
    except TxnContentionExhaustedError:
        exhausted = True
    elapsed = time.monotonic() - started
    await raw.close()
    return MintResult(attempts=counting.calls, elapsed_seconds=elapsed, exhausted=exhausted)


async def _one_round(database: str, racer_count: int) -> list[MintResult]:
    return list(await asyncio.gather(*(_one_mint(database) for _ in range(racer_count))))


def summarise(results: list[MintResult]) -> dict[str, Any]:
    attempts = [float(result.attempts) for result in results]
    latencies = [result.elapsed_seconds for result in results]
    exhausted = sum(1 for result in results if result.exhausted)
    summary: dict[str, Any] = {
        "n": len(results),
        "exhausted": exhausted,
        "attempts_max": max(attempts),
    }
    # Nearest-rank over the POOLED per-attempt samples — never a per-round
    # average, which would hide exactly the tail finding #102 exists to measure.
    for pct in PERCENTILES:
        summary[f"attempts_p{pct}"] = nearest_rank_percentile(attempts, pct)
        summary[f"latency_p{pct}_s"] = round(nearest_rank_percentile(latencies, pct), 4)
    # The lockstep signature check: a healthy jittered seam's attempt
    # distribution should NOT cluster multi-modally at the ceiling — report the
    # distinct attempt-count values observed so the receipt can show the shape,
    # not just a single summary number.
    summary["distinct_attempt_counts"] = sorted({int(value) for value in attempts})
    return summary


async def main() -> None:
    database = _unique_database()
    print(f"=== survey-102: database={database} ===")
    print(f"=== racer_counts={RACER_COUNTS} rounds_each={ROUNDS_PER_RACER_COUNT} ===")

    setup_ledger = FindingLedger(
        url=URL, namespace=NAMESPACE, database=database, user=USER, password=PASSWORD
    )
    await setup_ledger.ensure_ready()
    await setup_ledger.close()

    report: dict[str, Any] = {}
    for racer_count in RACER_COUNTS:
        all_results: list[MintResult] = []
        started = time.monotonic()
        for round_index in range(ROUNDS_PER_RACER_COUNT):
            all_results.extend(await _one_round(database, racer_count))
        wall = time.monotonic() - started
        summary = summarise(all_results)
        summary["wall_seconds"] = round(wall, 2)
        report[str(racer_count)] = summary
        print(f"--- N={racer_count} ({wall:.1f}s wall) ---")
        print(json.dumps(summary, indent=2))

    admin = await _connect(database)
    await admin.query(f"REMOVE DATABASE IF EXISTS {database};")
    await admin.close()

    print("=== FULL REPORT (json) ===")
    print(json.dumps(report, indent=2))
    print("=== DONE ===")


if __name__ == "__main__":
    asyncio.run(main())
