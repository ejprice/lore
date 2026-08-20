#!/usr/bin/env python3
"""Probe: a UNIQUE index over an ``option<string>`` field vs NONE (unset) values.

WHY (packet 48 — the schema of ``principal.subject``). The operator chose
provisioning **Model B**: an admin pre-creates a principal by email BEFORE first
login, and the OAuth ``subject`` is filled in later. So ``principal.subject`` is
``option<string>``, and MULTIPLE pre-created principals hold ``subject = NONE`` at
the same time. We want ``subject`` UNIQUE so a real OAuth identity maps to <=1
principal. Three things must be settled BY CONSTRUCTION (not opinion), because a
wrong answer is a real bug in the second ``add <email>``:

  Q1. Does a UNIQUE index over ``option<string>`` PERMIT MULTIPLE rows whose value
      is NONE (unset)?  If it REJECTS the 2nd NONE row, a plain
      ``subject option<string> UNIQUE`` breaks Model B.
  Q2. Is there a FILTERED / PARTIAL unique index spelling
      (``... UNIQUE WHERE subject != NONE``) that our engine accepts?
  Q3. Does the backstop we WANT still hold: two rows with the SAME NON-NONE
      subject ARE rejected?  And does that backstop also fire on the Model-B
      UPDATE path (fill a previously-NONE subject to a value another row holds)?

METHOD (store law, #107 pattern). The store reference + the engine's own
CI-verified SurrealQL spec were read FIRST (see the report); this CONSTRUCTS each
state on the live TEST store and byte-observes the engine's per-statement result.
Every negative result is paired with a POSITIVE CONTROL (the UNIQUE demonstrably
firing) so a "clear" is trustworthy.

SAFETY. Mints its own throwaway database ``test_<pid>_<uuid4>`` under the
``lore_test`` namespace on the spike-surreal TEST store
(``ws://127.0.0.1:18000`` — creds root/spikeroot, matching
``loremaster/tests/_surreal_harness.py``), and drops it on exit. It NEVER touches
production (lore-surreal :18500).

Store-law compliance (reference §3): reads/writes go through the SDK's
``query_raw`` — the all-statements call every SurrealQL statement passes through
and the one ``execute_transaction`` itself rides — with EVERY per-statement
``status`` inspected explicitly. It never uses the bare ``.query()`` seam, which
validates only ``statement[0]`` and would hide a later rejection.

Run: ``uv run python scripts/probe_unique_nullable_48.py``
Exit 0 iff every expectation held (self-checking); non-zero on any surprise.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from loremaster.store._txn import bootstrap_session, signin_credentials
from pydantic import SecretStr
from surrealdb import AsyncSurreal

# TEST store topology — the spike defaults from ``_surreal_harness.py``. NEVER :18500.
URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"


def unique_database() -> str:
    """``test_<pid>_<uuid4>`` — the harness pattern, so a parallel run never collides."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


@dataclass
class StatementOutcome:
    """One statement's engine result, byte-observed via ``query_raw``."""

    statement: str
    #: True iff the engine returned status == "OK" for this single statement.
    ok: bool
    #: "OK", "ERR", or "RAISED" (an RPC/parse-level error the SDK surfaced as an exception).
    status: str
    #: The rows (on OK) or the engine's error string (on ERR/RAISED), stringified.
    detail: str


@dataclass
class ProbeReport:
    """Accumulates outcomes and the derived verdicts."""

    outcomes: list[StatementOutcome] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)


async def run_one(connection: Any, statement: str) -> StatementOutcome:
    """Execute ONE statement via ``query_raw`` and byte-observe its per-statement status.

    ``query_raw`` returns ``{"id": ..., "result": [{"status", "result", "time", ...}]}``
    and — unlike ``.query()`` — does NOT itself raise on a per-statement ERR, so a
    UNIQUE violation comes back as a readable ``status == "ERR"`` entry. A genuine
    PARSE error fails the whole RPC request and surfaces as a raised exception; we
    capture both shapes.
    """
    try:
        response = await connection.query_raw(statement)
    except Exception as error:  # noqa: BLE001 - a probe records every failure shape verbatim
        return StatementOutcome(statement, False, "RAISED", f"{type(error).__name__}: {error}")
    # A PARSE error fails the whole RPC request: query_raw returns an envelope with a
    # top-level "error" (no per-statement "result" list) rather than raising.
    if isinstance(response, dict) and isinstance(response.get("error"), dict):
        message = str(response["error"].get("message", response["error"]))
        return StatementOutcome(statement, False, "PARSE_ERR", message)
    entries = response.get("result") if isinstance(response, dict) else None
    if not isinstance(entries, list) or not entries:
        return StatementOutcome(statement, False, "MALFORMED", repr(response))
    entry = entries[0]
    status = str(entry.get("status"))
    detail = str(entry.get("result"))
    return StatementOutcome(statement, status == "OK", status, detail)


async def expect(
    report: ProbeReport,
    connection: Any,
    statement: str,
    *,
    want_ok: bool,
    why: str,
) -> StatementOutcome:
    """Run ``statement``, record it, and flag a surprise if reality != ``want_ok``."""
    outcome = await run_one(connection, statement)
    report.outcomes.append(outcome)
    verdict = "OK " if outcome.ok else f"{outcome.status}"
    marker = "  " if outcome.ok == want_ok else "!!"
    want = "OK" if want_ok else "REJECT"
    print(f"{marker} [{verdict:<6}] want={want:<6} | {statement}")
    if not outcome.ok:
        print(f"        -> {outcome.detail}")
    if outcome.ok != want_ok:
        wanted = "OK" if want_ok else "REJECT"
        report.surprises.append(
            f"{why}: wanted {wanted}, got {outcome.status} for `{statement}` :: {outcome.detail}"
        )
    return outcome


async def probe(connection: Any) -> ProbeReport:
    report = ProbeReport()

    print("\n=== SCHEMA (SCHEMAFULL table, subject option<string>, UNIQUE index) ===")
    # DDL applied statement-by-statement with every status checked (store law §3).
    for ddl in (
        "DEFINE TABLE probe SCHEMAFULL",
        "DEFINE FIELD name ON probe TYPE string",
        "DEFINE FIELD subject ON probe TYPE option<string>",
        "DEFINE INDEX probe_subject_uniq ON probe FIELDS subject UNIQUE",
    ):
        await expect(report, connection, ddl, want_ok=True, why="schema DDL must apply")

    print("\n=== Q1: MULTIPLE NONE (unset) rows under the UNIQUE index ===")
    # subject omitted => NONE for an option<string> field. Three of them.
    await expect(report, connection, "CREATE probe:a1 SET name = 'alpha'", want_ok=True, why="1st NONE row")
    await expect(
        report,
        connection,
        "CREATE probe:a2 SET name = 'beta'",
        want_ok=True,
        why="2nd NONE row (the core question)",
    )
    await expect(report, connection, "CREATE probe:a3 SET name = 'gamma'", want_ok=True, why="3rd NONE row")
    # Explicit NONE, to confirm it behaves like an omitted field.
    await expect(
        report,
        connection,
        "CREATE probe:a4 SET name = 'delta', subject = NONE",
        want_ok=True,
        why="explicit subject = NONE",
    )

    print("\n=== Q3 control: SAME non-NONE subject must be REJECTED (UNIQUE fires) ===")
    await expect(
        report,
        connection,
        "CREATE probe:b1 SET name = 'b1', subject = 'x'",
        want_ok=True,
        why="1st subject='x'",
    )
    await expect(
        report,
        connection,
        "CREATE probe:b2 SET name = 'b2', subject = 'x'",
        want_ok=False,
        why="POSITIVE CONTROL: duplicate subject='x' must be rejected",
    )

    print("\n=== Q3 control: DISTINCT non-NONE subjects must both succeed ===")
    await expect(
        report, connection, "CREATE probe:c1 SET name = 'c1', subject = 'y'", want_ok=True, why="subject='y'"
    )
    await expect(
        report, connection, "CREATE probe:c2 SET name = 'c2', subject = 'z'", want_ok=True, why="subject='z'"
    )

    print("\n=== Q2: FILTERED / PARTIAL unique index spellings (expect PARSE ERROR) ===")
    for spelling in (
        "DEFINE INDEX probe_filtered_ne ON probe FIELDS subject UNIQUE WHERE subject != NONE",
        "DEFINE INDEX probe_filtered_isnot ON probe FIELDS subject UNIQUE WHERE subject IS NOT NONE",
        "DEFINE INDEX probe_filtered_where ON probe FIELDS subject WHERE subject != NONE UNIQUE",
    ):
        await expect(
            report, connection, spelling, want_ok=False, why="filtered UNIQUE is not in the engine grammar"
        )

    print("\n=== Model B UPDATE path: fill a previously-NONE subject; backstop on UPDATE ===")
    await expect(
        report,
        connection,
        "CREATE probe:e1 SET name = 'e1'",
        want_ok=True,
        why="Model-B pre-create e1 (NONE)",
    )
    await expect(
        report,
        connection,
        "CREATE probe:e2 SET name = 'e2'",
        want_ok=True,
        why="Model-B pre-create e2 (NONE), coexisting NONE",
    )
    await expect(
        report,
        connection,
        "UPDATE probe:e1 SET subject = 'oauth-sub-1'",
        want_ok=True,
        why="fill e1's NONE subject (first login)",
    )
    await expect(
        report,
        connection,
        "UPDATE probe:e2 SET subject = 'oauth-sub-1'",
        want_ok=False,
        why="POSITIVE CONTROL: UPDATE to a duplicate non-NONE subject must be rejected",
    )
    await expect(
        report,
        connection,
        "UPDATE probe:e2 SET subject = 'oauth-sub-2'",
        want_ok=True,
        why="fill e2 with a distinct subject",
    )

    print("\n=== Provenance: stored index definition (INFO FOR TABLE probe) ===")
    info = await run_one(connection, "INFO FOR TABLE probe")
    report.outcomes.append(info)
    print(f"   INFO -> {info.detail}")

    print("\n=== Provenance: NONE rows readable + count (fail-open coexistence) ===")
    count = await run_one(connection, "SELECT count() FROM probe WHERE subject = NONE GROUP ALL")
    report.outcomes.append(count)
    print(f"   NONE-count -> {count.detail}")

    return report


async def main() -> int:
    database = unique_database()
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))
    await bootstrap_session(connection, NAMESPACE, database, url=URL)
    print(f"probe database: {NAMESPACE}:{database}  (TEST store {URL})")
    try:
        report = await probe(connection)
    finally:
        try:
            await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
        except Exception as error:  # noqa: BLE001
            print(f"[cleanup warning] {type(error).__name__}: {error}")
        await connection.close()

    print("\n=== VERDICT ===")
    if report.surprises:
        print(f"SURPRISES ({len(report.surprises)}) — a claimed clear is NOT trustworthy:")
        for surprise in report.surprises:
            print(f"  - {surprise}")
        return 1
    print("All expectations held:")
    print("  Q1 multiple-NONE under UNIQUE : ALLOWED (2nd & 3rd NONE + explicit NONE all created)")
    print("  Q2 filtered/partial UNIQUE     : NOT SUPPORTED (every spelling rejected)")
    print("  Q3 same non-NONE rejected      : YES, on CREATE and on the Model-B UPDATE fill path")
    print("  => Model B schema is sound with a plain `subject option<string>` + UNIQUE index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
