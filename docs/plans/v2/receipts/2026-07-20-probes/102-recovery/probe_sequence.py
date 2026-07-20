"""Empirical probe: does SurrealDB 3.1.5 have a native atomic sequence mechanism?

Ad-hoc probe script (probe-sequence-1). NOT a test, NOT production code. Talks
ONLY to spike-surreal (ws://127.0.0.1:18000) on a throwaway database minted via
the same unique_database() idiom as the real test harness
(loremaster/tests/_surreal_harness.py), so it can never collide with, or leak
into, another concurrent session on the shared spike server.

NEVER point this at :18500 (production lore-surreal).
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import traceback
import uuid
from typing import Any

from surrealdb import AsyncSurreal
from surrealdb.errors import SurrealError

URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"


def unique_database() -> str:
    """Mirrors _surreal_harness.unique_database(): test_<pid>_<uuid4>."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


async def connect(database: str) -> AsyncSurreal:
    connection = AsyncSurreal(URL)
    await connection.signin({"username": USER, "password": PASSWORD})
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await connection.use(NAMESPACE, database)
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    return connection


async def try_statement(connection: AsyncSurreal, label: str, statement: str) -> dict[str, Any]:
    """Run one statement, capture success value or exact exception text."""
    try:
        result = await connection.query(statement)
        return {"label": label, "statement": statement, "ok": True, "result": result, "error": None}
    except SurrealError as error:
        return {
            "label": label,
            "statement": statement,
            "ok": False,
            "result": None,
            "error": f"{type(error).__name__}: {error}",
        }
    except Exception as error:  # noqa: BLE001 - probe wants ANY exception surfaced verbatim
        return {
            "label": label,
            "statement": statement,
            "ok": False,
            "result": None,
            "error": f"UNEXPECTED {type(error).__name__}: {error}",
        }


async def main() -> None:
    database = unique_database()
    print(f"=== database: {database} ===")
    connection = await connect(database)

    findings: list[dict[str, Any]] = []

    # --- Positive control 1: trivial arithmetic round-trip ------------------
    findings.append(await try_statement(connection, "positive_control_arithmetic", "RETURN 1 + 1;"))

    # --- Positive control 2: real CREATE/SELECT round-trip -------------------
    marker = uuid.uuid4().hex
    findings.append(
        await try_statement(
            connection,
            "positive_control_create",
            f"CREATE probe_marker SET value = '{marker}';",
        )
    )
    findings.append(
        await try_statement(
            connection,
            "positive_control_select",
            f"SELECT value FROM probe_marker WHERE value = '{marker}';",
        )
    )

    # --- Negative control: knowingly-bogus function --------------------------
    findings.append(
        await try_statement(connection, "negative_control_bogus_function", "RETURN bogus::nope();")
    )

    # --- Candidate existence checks -------------------------------------------
    findings.append(await try_statement(connection, "define_sequence_bare", "DEFINE SEQUENCE probe_seq;"))
    findings.append(
        await try_statement(connection, "sequence_nextval_no_arg", "RETURN sequence::nextval();")
    )
    findings.append(
        await try_statement(
            connection, "sequence_nextval_with_arg", 'RETURN sequence::nextval("probe_seq");'
        )
    )
    findings.append(
        await try_statement(
            connection, "sequence_next_with_arg_wrong_name", 'RETURN sequence::next("probe_seq");'
        )
    )
    findings.append(
        await try_statement(
            connection,
            "sequence_nextval_undefined_seq",
            'RETURN sequence::nextval("never_defined_seq_xyz");',
        )
    )
    findings.append(await try_statement(connection, "info_for_db", "INFO FOR DB;"))

    # --- DEFINE SEQUENCE with BATCH / START / TIMEOUT clauses -----------------
    findings.append(
        await try_statement(
            connection,
            "define_sequence_full_clause",
            "DEFINE SEQUENCE probe_seq_full BATCH 10 START 100 TIMEOUT 5s;",
        )
    )
    findings.append(
        await try_statement(
            connection,
            "sequence_nextval_full_clause_seq",
            'RETURN sequence::nextval("probe_seq_full");',
        )
    )

    # --- Transaction behaviour: sequence call alongside other statements ------
    txn_statement = (
        "BEGIN TRANSACTION;\n"
        'LET $a = sequence::nextval("probe_seq");\n'
        f"CREATE probe_txn_marker SET seq_value = $a, tag = '{marker}';\n"
        "COMMIT TRANSACTION;\n"
    )
    findings.append(await try_statement(connection, "sequence_inside_transaction", txn_statement))
    findings.append(
        await try_statement(
            connection,
            "sequence_inside_transaction_readback",
            f"SELECT seq_value FROM probe_txn_marker WHERE tag = '{marker}';",
        )
    )

    for finding in findings:
        print("-" * 80)
        print(f"[{finding['label']}]")
        print(f"  statement: {finding['statement']!r}")
        print(f"  ok: {finding['ok']}")
        if finding["ok"]:
            print(f"  result: {finding['result']!r}")
        else:
            print(f"  error: {finding['error']}")

    await connection.close()
    print("\n=== DONE (single-connection phase) ===")
    print(f"DATABASE_NAME_FOR_REUSE={database}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:  # noqa: BLE001 - probe: surface any crash verbatim
        traceback.print_exc()
        sys.exit(1)
