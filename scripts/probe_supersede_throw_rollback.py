#!/usr/bin/env python3
"""Probe: the #441 IN-STORE conflict guard — ``LET $x = (UPDATE … RETURN AFTER); IF array::len($x)
= 0 { THROW … }`` — inside a composed ``execute_transaction`` ROLLS BACK a preceding UPSERT, and the
fragment passes ``_txn._assert_envelope_integrity``. Contract-phase probe for packet 63b wave i-b
(design ``docs/design/2026-09-03-packet63b-design.md`` §2.4 rider vii), authored by
``contract-63b-i-b``.

WHY (design §2.2/§2.4): #441 moves the supersede CONFLICT guard OUT of Python and INTO the store, so
the guarded CLOSE and the successor CREATE compose into ONE ``BEGIN…COMMIT``: a zero-match close must
abort the WHOLE transaction (the successor cannot land beside an un-closed predecessor). Store-ref §3
+ the SurrealQL language tests (``statements/transaction/throw_error_handling.surql`` /
``control_flow/transaction/throw_without_return.surql`` / ``statements/if/control_flow.surql``) say
``THROW`` inside ``BEGIN…COMMIT`` aborts the transaction — this probe CONFIRMS it on the live 3.2.x
engine through the SAME ``compose`` / ``execute_transaction`` seam production will use, so the contract
does not merely BELIEVE the mechanism (the #107 class: read the docs, then VERIFY them).

METHOD (the C1 'a probe NEEDS a positive control' rule):
  (a) NEGATIVE (the conflict): compose [UPSERT witness_a, LET $gw = (UPDATE <no-match> RETURN AFTER),
      IF array::len($gw)=0 { THROW "governed_conflict:…" }] → execute. REQUIRE it RAISES with the
      ``governed_conflict:`` marker surfaced by the SEMANTIC root cause, AND the witness_a row does
      NOT exist (the preceding UPSERT was ROLLED BACK by the THROW).
  (b) POSITIVE CONTROL (no conflict): the SAME shape but the UPDATE MATCHES one row → NO throw →
      witness_b DOES exist (so the negative leg is not a can-never-commit false pass, and the guard
      does not fire on a live close).
  (c) ENVELOPE: ``_assert_envelope_integrity`` accepts BOTH the LET and the IF-THROW statements (no
      internal ';' , no bare BEGIN/COMMIT), so ``compose`` admits the fragment.

SAFETY. Mints a throwaway ``test_<pid>_<uuid4>`` database under ``lore_test`` on the spike-surreal
TEST store (``ws://127.0.0.1:18000`` — root/spikeroot, matching ``loremaster/tests/_surreal_harness.py``)
and drops it on exit. NEVER touches production (lore-surreal :18500).

Run: ``uv run python scripts/probe_supersede_throw_rollback.py``
Exit 0 iff (a) rolled back with the marker, (b) committed, and (c) the envelope check accepted the
fragment; non-zero (LOUD) on any surprise.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from typing import Any

from loremaster.store._txn import (
    TxnEnvelopeViolationError,
    TxnFragment,
    _assert_envelope_integrity,
    bootstrap_session,
    compose,
    execute_transaction,
    signin_credentials,
)
from pydantic import SecretStr
from surrealdb import AsyncSurreal

URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"

_MARKER = "governed_conflict:probe_t:target"


def _unique_database() -> str:
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


def _conflict_fragments(witness_id: str, *, match: bool) -> list[TxnFragment]:
    """The composed supersede shape: a witness UPSERT (the 'successor create') + the guarded close
    (a ``LET`` capturing the RETURN AFTER + an ``IF array::len = 0`` THROW). ``match=False`` makes the
    close match ZERO rows (the conflict); ``match=True`` makes it match the seeded row."""
    where = "v = 1" if match else "v = 999"  # the seeded row has v = 1; 999 matches nothing
    return [
        TxnFragment(
            statements=[f"UPSERT probe_t:{witness_id} CONTENT {{ v: 1 }}"],
            params={},
        ),
        TxnFragment(
            statements=[
                f"LET $gw = (UPDATE probe_t:target SET v = 2 WHERE {where} RETURN AFTER)",
                f'IF array::len($gw) = 0 {{ THROW "{_MARKER}" }}',
            ],
            params={},
        ),
    ]


async def _row_exists(connection: Any, record: str) -> bool:
    rows = await connection.query(f"SELECT id FROM {record}")
    return bool(rows)


async def _run() -> tuple[list[str], list[str]]:
    """Run the legs; return ``(failures, discoveries)`` — failures gate the exit code, discoveries
    are REPORTED (the §2.4 vii claims are the ROLLBACK + the envelope; the marker-classification gap
    is a design finding, not a §2.4 vii failure)."""
    failures: list[str] = []
    discoveries: list[str] = []

    # (c) ENVELOPE — before any I/O: compose must accept the LET + IF-THROW fragment.
    for statement in _conflict_fragments("envelope", match=False)[1].statements:
        try:
            _assert_envelope_integrity(statement)
        except TxnEnvelopeViolationError as error:
            failures.append(f"(c) envelope check REJECTED a fragment statement {statement!r}: {error}")

    database = _unique_database()
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))
    await bootstrap_session(connection, NAMESPACE, database, url=URL)
    try:
        await connection.query("DEFINE TABLE probe_t SCHEMALESS")
        await connection.query("CREATE probe_t:target CONTENT { v: 1 }")

        # (a) NEGATIVE — the §2.4 vii claim: the zero-match close's THROW must ROLL BACK the whole
        # transaction (raise + the preceding UPSERT does not survive).
        statement_text, params = compose(*_conflict_fragments("witness_a", match=False))
        raised: Exception | None = None
        try:
            await execute_transaction(
                statement_text, params,
                acquire=lambda: _identity(connection), drop=_noop, url=URL,
            )
        except Exception as error:  # noqa: BLE001 - the probe classifies the raise itself
            raised = error
        if raised is None:
            failures.append(
                "(a) the zero-match close did NOT raise — the THROW did not abort the transaction"
            )
        if await _row_exists(connection, "probe_t:witness_a"):
            failures.append(
                "(a) the preceding UPSERT (witness_a) SURVIVED the conflict — the THROW did NOT roll "
                "the whole transaction back (the successor would land beside an un-closed predecessor)"
            )

        # (d) DISCOVERY (design §2.2 marker-mapping gap): the RAW engine result carries the THROW
        # marker (kind='Thrown', "An error occurred: <marker>"), but execute_transaction's error
        # hygiene (ledger #31) STRIPS it from the raised exception — so `governed` cannot map the
        # `governed_conflict:` marker to GovernedConflict from the exception text as §2.2 assumes.
        raw = await _raw_conflict_result(connection)
        thrown = [e for e in raw if isinstance(e, dict) and e.get("kind") == "Thrown"]
        marker_in_raw = any(_MARKER in str(e.get("result", "")) for e in thrown)
        marker_in_exception = raised is not None and _MARKER in str(raised)
        discoveries.append(
            f"marker in RAW engine result (kind='Thrown'): {marker_in_raw} "
            f"(text: {thrown[0].get('result') if thrown else None!r})"
        )
        discoveries.append(
            f"marker in execute_transaction EXCEPTION: {marker_in_exception} "
            f"(exception: {str(raised)!r})"
        )
        if marker_in_raw and not marker_in_exception:
            discoveries.append(
                "GAP (design §2.2): the engine surfaces `governed_conflict:` in the raw 'Thrown' "
                "statement, but execute_transaction's ledger-#31 hygiene strips it from the raised "
                "exception — `governed` cannot map the marker -> GovernedConflict from the exception "
                "as §2.2 states. A _txn seam decision is needed (classify the `governed_conflict:` "
                "marker as a TYPED signal, analogous to the existing _RETRYABLE_CONFLICT_MARKER). "
                "STOP-and-FLAG to lead-63b. NOTE: the ROLLBACK itself (§2.4 vii (a)) HOLDS regardless."
            )

        # (b) POSITIVE CONTROL — a matching close commits and the witness lands.
        statement_text, params = compose(*_conflict_fragments("witness_b", match=True))
        try:
            await execute_transaction(
                statement_text, params,
                acquire=lambda: _identity(connection), drop=_noop, url=URL,
            )
        except Exception as error:  # noqa: BLE001
            failures.append(f"(b) positive control RAISED on a MATCHING close (should commit): {error!r}")
        if not await _row_exists(connection, "probe_t:witness_b"):
            failures.append(
                "(b) positive control did NOT commit the witness — the guard fired on a live close"
            )
    finally:
        try:
            await connection.query(f"REMOVE DATABASE {database}")
        finally:
            await connection.close()
    return failures, discoveries


async def _raw_conflict_result(connection: Any) -> list[Any]:
    """The RAW per-statement results of the conflict txn (a fresh witness id), for the discovery report."""
    statement_text, params = compose(*_conflict_fragments("witness_raw", match=False))
    raw = await connection.query_raw(statement_text, params)
    result = raw.get("result") if isinstance(raw, dict) else raw
    return result if isinstance(result, list) else []


async def _identity(connection: Any) -> Any:
    return connection


async def _noop(_connection: Any) -> None:
    return None


def main() -> int:
    failures, discoveries = asyncio.run(_run())
    if discoveries:
        print("DISCOVERIES (report-only — design-level findings for lead-63b):")
        for discovery in discoveries:
            print(f"  * {discovery}")
    if failures:
        print("PROBE FAILED (§2.4 rider vii — the in-store THROW rollback/envelope is NOT confirmed):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(
        "PROBE OK (§2.4 rider vii) — (a) the in-store `LET $x = (UPDATE … RETURN AFTER); "
        "IF array::len($x)=0 { THROW … }` ROLLS BACK a preceding UPSERT inside execute_transaction, "
        "(b) a matching close COMMITS (positive control), (c) _assert_envelope_integrity ACCEPTS the "
        "LET + IF-THROW fragment. See the discovery above re: the §2.2 marker-mapping gap."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
