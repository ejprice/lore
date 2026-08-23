#!/usr/bin/env python3
"""Probe: does a ``member_of`` RELATION edge auto-cascade when an endpoint principal
is hard-deleted? — and does the ``keep.keeper`` FIELD LINK dangle in the same delete?

WHY (packet 61a-w1 / finding #402 — a load-bearing #107-class disagreement). The
delete-cascade ruling (design ``2026-08-22-packet61-pdp-audit-rulings.md`` §FR-4) turns
on which of TWO record-link populations auto-clean when a ``principal`` node is deleted:

  * ``keep.keeper: record<principal>`` is a FIELD LINK. Store law
    (``docs/reference/surrealdb-31-capabilities.md`` §2) says ``record<t>`` links do NOT
    auto-clean on target delete — a deleted keeper leaves ``keep.keeper`` DANGLING
    (a #105-class ghost link).
  * ``member_of`` (``principal --member_of--> keep``) is a graph RELATION EDGE. Store law
    §4 says RELATION edges DO self-delete when an endpoint node is deleted (vendor RELATE:
    *"a graph edge will also automatically be deleted if it is no longer connected to a
    record at both `in` and `out`"*; the ENFORCED-clause probe §4 confirmed
    *"deleting either endpoint cascades the edge away and cleans its UNIQUE index entry"*).

⚠ #402's BODY CLAIMS the ``member_of`` edges DANGLE. Store law §4 says they auto-clean.
That is the disagreement — and per ``CLAUDE.md`` (#107: *believed, not probed*) it is
settled BY CONSTRUCTION here, not by picking a side. The verdict decides only the
BUILDER'S MECHANISM (whether the delete transaction needs an explicit
``DELETE member_of WHERE in = ...`` leg): if ``member_of`` auto-cascades, no explicit
DELETE is needed and the contract pins the PROPERTY (zero dangling ``member_of`` after a
member-only delete); if it does NOT, the builder must add the explicit leg.

METHOD (store law, #107 pattern). CONSTRUCTS each state on the live 3.2.x TEST store and
byte-observes the engine's per-statement result via ``query_raw`` (never the bare
``.query()``, which validates ``statement[0]`` only). EVERY negative/absent check is
paired with a POSITIVE CONTROL (the edge/link demonstrably PRESENT before the delete),
so a "clear" is trustworthy (``CLAUDE.md``: a probe needs a control).

SAFETY. Mints its own throwaway database ``test_<pid>_<uuid4>`` under the ``lore_test``
namespace on spike-surreal (``ws://127.0.0.1:18000`` — creds root/spikeroot, matching
``loremaster/tests/_surreal_harness.py``) and drops it on exit. It NEVER touches
production (lore-surreal :18500). The schema it applies is the REAL production emitter
(``surreal_schema.generate_principal_ddl`` + ``generate_keep_ddl``), so the probe reads
the store the shipped code will.

Run: ``uv run python scripts/probe_member_of_cascade.py``
Exit 0 iff every expectation held (self-checking); non-zero on any surprise.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from loremaster.store._txn import bootstrap_session, signin_credentials
from loremaster.store.surreal_schema import (
    KEEP_TABLE,
    MEMBER_OF_RELATION,
    PRINCIPAL_TABLE,
    generate_keep_ddl,
    generate_principal_ddl,
)
from pydantic import SecretStr
from surrealdb import AsyncSurreal, RecordID

# TEST store topology — the spike defaults from ``_surreal_harness.py``. NEVER :18500.
URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"

_KEEPER_ID = "pk_keeper"
_MEMBER_ID = "pm_member"
_KEEP_ID = "k1_space"
# LEG C — a SECOND, independent keep for the OUT-endpoint (keep-node) delete probe
# (the delete_keep mechanism). Its principals are NOT touched by legs A/B.
_KEEPER2_ID = "pk2_keeper"
_MEMBER2_ID = "pm2_member"
_KEEP2_ID = "k2_space"


def unique_database() -> str:
    """``test_<pid>_<uuid4>`` — the harness pattern, so a parallel run never collides."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


@dataclass
class ProbeReport:
    """Accumulates surprises (an empty list == a trustworthy clear)."""

    surprises: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)


async def _statement_ok(connection: Any, statement: str, params: dict[str, Any]) -> tuple[bool, str]:
    """Run ONE statement via ``query_raw`` and byte-observe its per-statement status.

    ``query_raw`` returns ``{"result": [{"status", "result", ...}]}`` and — unlike
    ``.query()`` — does NOT itself raise on a per-statement ERR, so a rejection is a
    readable ``status == "ERR"``. A PARSE error fails the whole RPC request (a top-level
    ``error`` or a raised exception); both shapes are captured.
    """
    try:
        response = await connection.query_raw(statement, params)
    except Exception as error:  # noqa: BLE001 - a probe records every failure shape verbatim
        return False, f"RAISED {type(error).__name__}: {error}"
    if isinstance(response, dict) and isinstance(response.get("error"), dict):
        return False, f"PARSE_ERR {response['error'].get('message', response['error'])}"
    entries = response.get("result") if isinstance(response, dict) else None
    if not isinstance(entries, list) or not entries:
        return False, f"MALFORMED {response!r}"
    entry = entries[0]
    return str(entry.get("status")) == "OK", str(entry.get("result"))


async def _count(connection: Any, statement: str, params: dict[str, Any]) -> int:
    """The integer ``count()`` a ``SELECT count() ... GROUP ALL`` returns (0 if empty)."""
    ok, detail = await _statement_ok(connection, statement, params)
    if not ok:
        raise AssertionError(f"count query failed: {statement} :: {detail}")
    response = await connection.query_raw(statement, params)
    rows = response["result"][0]["result"]
    if not rows:
        return 0
    return int(rows[0].get("count", 0))


async def _expect_ok(
    report: ProbeReport, connection: Any, statement: str, params: dict[str, Any], why: str
) -> None:
    ok, detail = await _statement_ok(connection, statement, params)
    marker = "  " if ok else "!!"
    print(f"{marker} [{'OK' if ok else 'FAIL':<5}] {why}")
    if not ok:
        print(f"        -> {detail}")
        report.surprises.append(f"{why}: expected OK, got {detail} for `{statement}`")


async def _expect_count(
    report: ProbeReport, connection: Any, statement: str, params: dict[str, Any], want: int, why: str
) -> int:
    got = await _count(connection, statement, params)
    marker = "  " if got == want else "!!"
    print(f"{marker} [{got:>2} == {want:<2}] {why}")
    if got != want:
        report.surprises.append(f"{why}: expected count {want}, got {got}")
    return got


async def _row_exists(connection: Any, table: str, row_id: str) -> bool:
    response = await connection.query_raw(
        "SELECT id FROM $row", {"row": RecordID(table, row_id)}
    )
    return bool(response["result"][0]["result"])


async def _keeper_field(connection: Any, keep_id: str) -> str | None:
    """The raw ``keeper`` field value stored on ``keep:<keep_id>`` (a ``str`` of the
    RecordID it points at), or ``None`` if the keep row is gone."""
    response = await connection.query_raw(
        f"SELECT keeper FROM type::record('{KEEP_TABLE}', $id)", {"id": keep_id}
    )
    rows = response["result"][0]["result"]
    if not rows:
        return None
    return str(rows[0].get("keeper"))


async def probe(connection: Any) -> ProbeReport:  # noqa: PLR0915 - linear construction+measurement probe
    report = ProbeReport()

    print("\n=== SCHEMA (real production emitters: principal + keep + member_of) ===")
    for ddl in (generate_principal_ddl(), generate_keep_ddl()):
        # Apply each slice inside its own BEGIN/COMMIT the same way the stores do; but
        # here a single statement-at-a-time apply is fine because the emitters are
        # idempotent DDL — send the whole slice via query and check it did not raise.
        try:
            await connection.query(f"BEGIN;\n{ddl}COMMIT;\n")
            print(f"   [OK   ] applied a schema slice ({ddl.count(';')} statements)")
        except Exception as error:  # noqa: BLE001
            report.surprises.append(f"schema apply failed: {type(error).__name__}: {error}")
            print(f"!! [FAIL ] schema apply raised: {error}")

    print("\n=== SEED: keeper + member principals, a keep, and TWO member_of edges ===")
    keeper = RecordID(PRINCIPAL_TABLE, _KEEPER_ID)
    member = RecordID(PRINCIPAL_TABLE, _MEMBER_ID)
    keep = RecordID(KEEP_TABLE, _KEEP_ID)
    await _expect_ok(
        report, connection,
        f"CREATE type::record('{PRINCIPAL_TABLE}', $id) CONTENT {{ email: $email }}",
        {"id": _KEEPER_ID, "email": "keeper@example.com"}, "create keeper principal",
    )
    await _expect_ok(
        report, connection,
        f"CREATE type::record('{PRINCIPAL_TABLE}', $id) CONTENT {{ email: $email }}",
        {"id": _MEMBER_ID, "email": "member@example.com"}, "create member principal",
    )
    await _expect_ok(
        report, connection,
        f"CREATE type::record('{KEEP_TABLE}', $id) "
        f"CONTENT {{ keeper: type::record('{PRINCIPAL_TABLE}', $kid), type: 'team', name: 'crew' }}",
        {"id": _KEEP_ID, "kid": _KEEPER_ID}, "create keep (keeper FIELD LINK -> keeper principal)",
    )
    # RELATE endpoints MUST be bound RecordID params (store law §4).
    await _expect_ok(
        report, connection,
        f"RELATE $from->{MEMBER_OF_RELATION}->$to",
        {"from": keeper, "to": keep}, "RELATE keeper's own member_of edge (Fork D auto-add)",
    )
    await _expect_ok(
        report, connection,
        f"RELATE $from->{MEMBER_OF_RELATION}->$to",
        {"from": member, "to": keep}, "RELATE member's member_of edge",
    )
    # LEG C scenario — a second, independent keep with its own keeper + member edges,
    # untouched by legs A/B, for the OUT-endpoint (keep-node) delete probe.
    keeper2 = RecordID(PRINCIPAL_TABLE, _KEEPER2_ID)
    member2 = RecordID(PRINCIPAL_TABLE, _MEMBER2_ID)
    keep2 = RecordID(KEEP_TABLE, _KEEP2_ID)
    await _expect_ok(
        report, connection,
        f"CREATE type::record('{PRINCIPAL_TABLE}', $id) CONTENT {{ email: $email }}",
        {"id": _KEEPER2_ID, "email": "keeper2@example.com"}, "create keeper2 principal",
    )
    await _expect_ok(
        report, connection,
        f"CREATE type::record('{PRINCIPAL_TABLE}', $id) CONTENT {{ email: $email }}",
        {"id": _MEMBER2_ID, "email": "member2@example.com"}, "create member2 principal",
    )
    await _expect_ok(
        report, connection,
        f"CREATE type::record('{KEEP_TABLE}', $id) "
        f"CONTENT {{ keeper: type::record('{PRINCIPAL_TABLE}', $kid), type: 'team', name: 'crew2' }}",
        {"id": _KEEP2_ID, "kid": _KEEPER2_ID}, "create keep2 (for the keep-node delete leg)",
    )
    await _expect_ok(
        report, connection, f"RELATE $from->{MEMBER_OF_RELATION}->$to",
        {"from": keeper2, "to": keep2}, "RELATE keeper2's member_of edge",
    )
    await _expect_ok(
        report, connection, f"RELATE $from->{MEMBER_OF_RELATION}->$to",
        {"from": member2, "to": keep2}, "RELATE member2's member_of edge",
    )

    print("\n=== POSITIVE CONTROLS (before any delete) — the edges/link are PRESENT ===")
    await _expect_count(
        report, connection,
        f"SELECT count() FROM {MEMBER_OF_RELATION} GROUP ALL", {}, 4,
        "member_of edge count == 4 (keep1: keeper+member, keep2: keeper2+member2)",
    )
    await _expect_count(
        report, connection,
        f"SELECT count() FROM {MEMBER_OF_RELATION} WHERE in = $p GROUP ALL", {"p": member}, 1,
        "member_of where in=member == 1 (present before delete)",
    )
    await _expect_count(
        report, connection,
        f"SELECT count() FROM {MEMBER_OF_RELATION} WHERE out = $k GROUP ALL", {"k": keep2}, 2,
        "member_of where out=keep2 == 2 (present before keep-node delete)",
    )
    keeper_field_before = await _keeper_field(connection, _KEEP_ID)
    print(f"   keep.keeper (before) = {keeper_field_before!r}")
    if keeper_field_before != f"{PRINCIPAL_TABLE}:{_KEEPER_ID}":
        report.surprises.append(
            f"keep.keeper field not the keeper before delete: {keeper_field_before!r}"
        )

    print("\n=== LEG A: hard-DELETE the MEMBER principal (the ruling's core question) ===")
    await _expect_ok(
        report, connection,
        f"DELETE type::record('{PRINCIPAL_TABLE}', $id)", {"id": _MEMBER_ID},
        "hard-delete member principal",
    )
    member_gone = not await _row_exists(connection, PRINCIPAL_TABLE, _MEMBER_ID)
    print(f"   member principal deleted = {member_gone}")
    if not member_gone:
        report.surprises.append("member principal was not actually deleted")
    member_edge_after = await _expect_count(
        report, connection,
        f"SELECT count() FROM {MEMBER_OF_RELATION} WHERE in = $p GROUP ALL", {"p": member},
        0, "member_of where in=member == 0 AFTER member delete (auto-cascade?)",
    )
    total_after_member = await _count(
        connection, f"SELECT count() FROM {MEMBER_OF_RELATION} GROUP ALL", {}
    )
    keep_survives = await _row_exists(connection, KEEP_TABLE, _KEEP_ID)
    print(f"   member_of total after member delete = {total_after_member} (keeper's edge should remain)")
    print(f"   keep row survives member delete = {keep_survives}")
    if not keep_survives:
        report.surprises.append("the keep row vanished when a MEMBER was deleted (out endpoint)")

    member_of_auto_cascades = member_edge_after == 0
    report.facts.append(
        f"member_of AUTO-CASCADES on `in`-endpoint (member) delete: {member_of_auto_cascades} "
        f"(edge count where in=member went 1 -> {member_edge_after})"
    )

    print("\n=== LEG B: hard-DELETE the KEEPER — FIELD LINK vs RELATION EDGE, one delete ===")
    # In production this delete is REFUSED (refuse-while-keeping); here we delete raw to
    # observe the MECHANISM the ruling's two-populations distinction rests on.
    await _expect_ok(
        report, connection,
        f"DELETE type::record('{PRINCIPAL_TABLE}', $id)", {"id": _KEEPER_ID},
        "hard-delete keeper principal (raw — production REFUSES this)",
    )
    keeper_edge_after = await _expect_count(
        report, connection,
        f"SELECT count() FROM {MEMBER_OF_RELATION} WHERE in = $p GROUP ALL", {"p": keeper},
        0, "member_of where in=keeper == 0 AFTER keeper delete (RELATION auto-cascade)",
    )
    keep_still_there = await _row_exists(connection, KEEP_TABLE, _KEEP_ID)
    keeper_field_after = await _keeper_field(connection, _KEEP_ID)
    print(f"   keep row survives keeper delete = {keep_still_there}")
    print(f"   keep.keeper (after keeper delete) = {keeper_field_after!r}")
    keeper_principal_gone = not await _row_exists(connection, PRINCIPAL_TABLE, _KEEPER_ID)
    print(f"   keeper principal deleted = {keeper_principal_gone}")

    # The two-populations proof: the RELATION edge cascaded (count 0) while the FIELD LINK
    # still points at the now-deleted keeper (dangling) on a surviving keep row.
    field_link_dangles = (
        keep_still_there
        and keeper_principal_gone
        and keeper_field_after == f"{PRINCIPAL_TABLE}:{_KEEPER_ID}"
    )
    report.facts.append(
        f"keep.keeper FIELD LINK DANGLES after keeper delete (does NOT auto-clean): {field_link_dangles} "
        f"(keep survives={keep_still_there}, keeper gone={keeper_principal_gone}, "
        f"keeper field still={keeper_field_after!r})"
    )
    if not field_link_dangles:
        report.surprises.append(
            "keep.keeper did NOT dangle as store-law §2 predicts — re-derive the FIELD-LINK "
            f"cascade assumption (keep_survives={keep_still_there}, "
            f"keeper_field_after={keeper_field_after!r}, keeper_gone={keeper_principal_gone})"
        )
    _ = keeper_edge_after  # named for the trailer

    print("\n=== LEG C: hard-DELETE the KEEP NODE (the delete_keep OUT-endpoint mechanism) ===")
    await _expect_ok(
        report, connection,
        f"DELETE type::record('{KEEP_TABLE}', $id)", {"id": _KEEP2_ID},
        "hard-delete keep2 node",
    )
    keep2_gone = not await _row_exists(connection, KEEP_TABLE, _KEEP2_ID)
    print(f"   keep2 node deleted = {keep2_gone}")
    if not keep2_gone:
        report.surprises.append("keep2 node was not actually deleted")
    keep2_edges_after = await _expect_count(
        report, connection,
        f"SELECT count() FROM {MEMBER_OF_RELATION} WHERE out = $k GROUP ALL", {"k": keep2},
        0, "member_of where out=keep2 == 0 AFTER keep-node delete (auto-cascade?)",
    )
    keeper2_survives = await _row_exists(connection, PRINCIPAL_TABLE, _KEEPER2_ID)
    member2_survives = await _row_exists(connection, PRINCIPAL_TABLE, _MEMBER2_ID)
    print(f"   keeper2 principal survives keep delete = {keeper2_survives}")
    print(f"   member2 principal survives keep delete = {member2_survives}")
    if not (keeper2_survives and member2_survives):
        report.surprises.append(
            "deleting a keep NODE removed its member principals (in-endpoints) — it must not"
        )
    keep_delete_cascades = keep2_edges_after == 0
    report.facts.append(
        f"member_of AUTO-CASCADES on `out`-endpoint (keep-node) delete: {keep_delete_cascades} "
        f"(edge count where out=keep2 went 2 -> {keep2_edges_after}); member principals survive"
    )

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

    print("\n=== SETTLED FACTS ===")
    for fact in report.facts:
        print(f"  * {fact}")
    print("\n=== VERDICT ===")
    if report.surprises:
        print(f"SURPRISES ({len(report.surprises)}) — a claimed clear is NOT trustworthy:")
        for surprise in report.surprises:
            print(f"  - {surprise}")
        return 1
    print("All expectations held. The member_of RELATION edge AUTO-CASCADES on BOTH an")
    print("`in`-endpoint (member/principal) delete AND an `out`-endpoint (keep-node) delete;")
    print("the keep.keeper FIELD LINK DANGLES on a keeper delete. Store law §4 (edges cascade)")
    print("and §2 (field links do not) both CONFIRMED; #402's body claim that member_of edges")
    print("dangle is REFUTED by construction.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
