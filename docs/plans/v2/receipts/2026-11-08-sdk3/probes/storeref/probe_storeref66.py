"""probe_storeref66 — re-measures the SDK 3.0.0 facts the store reference §0b states (storeref-sdk3-66, 2026-11-08).

Offline legs (O*) need no store. Store legs (S*) run ONLY against the TEST store ws://127.0.0.1:18000 in one
throwaway database that is REMOVED in `finally`. Every leg prints a decisive line and a CONTROL; the script
exits non-zero if any expectation fails. Run: `cd loremaster && uv run python <this file>`.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timezone

import surrealdb
from surrealdb import RecordID
from surrealdb.data.types.datetime import PreciseDatetime, parse_instant

from loremaster.store._txn import (
    SurrealStoreError,
    one_statement_result,
    open_surreal_connection,
    record_text,
)

TEST_URL = "ws://127.0.0.1:18000/rpc"  # the TEST store; never :18500
TEST_USER, TEST_PASS = "root", "spikeroot"  # tests/_surreal_harness.py spike defaults
NAMESPACE = "lore_test"
DATABASE = f"test_storeref66_{uuid.uuid4().hex}"
FAILS: list[str] = []


def check(label: str, condition: bool, detail: object) -> None:
    """Print one leg's verdict; record a failure."""
    print(f"{'PASS' if condition else 'FAIL'} {label}: {detail}")
    if not condition:
        FAILS.append(label)


def offline() -> None:
    """O1–O4: stdlib/SDK datetime and RecordID facts, no store."""
    nine = "2026-11-08T18:17:45.186697518+00:00"
    parsed = datetime.fromisoformat(nine)
    check("O1 fromisoformat truncates 9->6 silently", parsed.microsecond == 186697 and parsed.isoformat() == "2026-11-08T18:17:45.186697+00:00", parsed.isoformat())
    six = "2026-11-08T18:17:45.186697+00:00"
    check("O1 control: 6 digits round-trip exact", datetime.fromisoformat(six).isoformat() == six, six)
    for digits in range(1, 10):
        text = "2026-11-08T18:17:45." + "123456789"[:digits] + "Z"
        instant = parse_instant(text)
        check(f"O2 parse_instant {digits} digit(s)", isinstance(instant, PreciseDatetime) and instant.isoformat_with_nanoseconds().startswith("2026-11-08T18:17:45." + "123456789"[:digits]), instant.isoformat_with_nanoseconds())
    round_trip = parse_instant("2026-11-08T18:17:45.186697518Z").isoformat_with_nanoseconds()
    check("O2 codec round-trip keeps ns", round_trip == "2026-11-08T18:17:45.186697518Z", round_trip)
    a = parse_instant("2026-11-08T18:17:45.186697001Z")
    b = parse_instant("2026-11-08T18:17:45.186697002Z")
    check("O3 PreciseDatetime == ignores ns", (a == b) is True and (a < b) is False, f"ns {a.nanosecond}/{b.nanosecond}: eq={a == b} lt={a < b}")
    c = parse_instant("2026-11-08T18:17:45.186698001Z")
    check("O3 control: a different microsecond compares", (a == c) is False and (a < c) is True, f"eq={a == c} lt={a < c}")
    renders = {key: str(RecordID("kt", key)) for key in ("abc", "01JABCDEFGHJKMNPQRSTVWXYZ0", "42", "a-b", 42)}
    print(f"INFO O4 SDK str(RecordID): {renders}")
    word = RecordID("kt", "abc")
    check("O5 control: a word key round-trips through str/parse", RecordID.parse(str(word)) == word, str(word))
    broken = {key: RecordID.parse(str(RecordID("kt", key))) == RecordID("kt", key) for key in ("01JABCDEFGHJKMNPQRSTVWXYZ0", "a-b", 42)}
    check("O5 str(RecordID) does NOT round-trip for digit-led / non-word / int keys", not any(broken.values()), broken)
    check("O5 RecordID is hashable on 3.0.0", len({word, RecordID("kt", "abc")}) == 1, "set of two equal ids has 1 member")


async def store() -> None:
    """S1–S6 against one throwaway database on the TEST store."""
    connection = open_surreal_connection(TEST_URL)
    await connection.signin({"username": TEST_USER, "password": TEST_PASS})
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await connection.use(NAMESPACE, DATABASE)
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {DATABASE}")
    try:
        # S1 result shape
        two = await connection.query("RETURN 1; RETURN 2;")
        one = await connection.query("RETURN 1;")
        check("S1 query() answers one entry per statement", two == [1, 2] and one == [1], f"two={two!r} one={one!r}")
        try:
            one_statement_result(two)
            check("S1 seam refuses a two-statement answer", False, "no raise")
        except SurrealStoreError as error:
            check("S1 seam refuses a two-statement answer", True, type(error).__name__)
        check("S1 control: seam selects a one-statement answer", one_statement_result(one) == 1, one_statement_result(one))
        # S2 a LATER statement fails, no transaction
        try:
            result = await connection.query("CREATE probe_a:1 SET v = 1; THROW 'boom'; CREATE probe_a:2 SET v = 2;")
            raised = f"NO RAISE, result={result!r}"
        except Exception as error:  # the class is the measurement
            raised = f"{type(error).__module__}.{type(error).__name__}: {error}"
        rows = await connection.query("SELECT VALUE record::id(id) FROM probe_a ORDER BY id;")
        check("S2 a later statement's failure RAISES from query()", not raised.startswith("NO RAISE"), raised)
        print(f"INFO S2 rows left (no BEGIN: each statement its own txn): {rows!r}")
        control = await connection.query("CREATE probe_b:1; CREATE probe_b:2;")
        check("S2 control: two good statements raise nothing", isinstance(control, list) and len(control) == 2, f"{len(control)} entries")
        # S2b the same inside BEGIN/COMMIT
        try:
            await connection.query("BEGIN; CREATE probe_c:1; THROW 'boom'; COMMIT;")
            raised_txn = "NO RAISE"
        except Exception as error:
            details = getattr(error, "details", None)
            raised_txn = f"{type(error).__name__} kind={getattr(error, 'kind', None)!r} details={details!r}: {error}"
        try:
            rows_txn: object = await connection.query("SELECT * FROM probe_c;")
        except Exception as error:  # 3.3.5: SELECT over a never-created table raises NotFoundError
            rows_txn = f"{type(error).__name__}: {error}"
        nothing_committed = rows_txn == [[]] or (isinstance(rows_txn, str) and rows_txn.startswith("NotFoundError"))
        check("S2b in-transaction THROW raises and nothing commits", raised_txn != "NO RAISE" and nothing_committed, f"{raised_txn} · rows={rows_txn!r}")
        # S3 engine id text vs record_text vs str(RecordID)
        keys: list[object] = ["abc", "01JABCDEFGHJKMNPQRSTVWXYZ0", "4558tc0abc", "42", "a-b", 42]
        for key in keys:
            await connection.query("CREATE $id;", {"id": RecordID("kt", key)})
            engine = one_statement_result(await connection.query("RETURN <string> $id;", {"id": RecordID("kt", key)}))
            parts = record_text(RecordID("kt", key))
            print(f"INFO S3 key={key!r}: engine={engine!r} record_text={parts!r} str={str(RecordID('kt', key))!r} equal={engine == parts}")
        # S4 `> $since` type set (SCHEMALESS table)
        await connection.query(
            "CREATE st:string SET v = '2030-01-01T00:00:00Z'; CREATE st:number SET v = 5; CREATE st:float SET v = 1.5;"
            " CREATE st:bool SET v = true; CREATE st:null SET v = NULL; CREATE st:duration SET v = 1h;"
            " CREATE st:array SET v = [1]; CREATE st:object SET v = {a: 1}; CREATE st:uuid SET v = rand::uuid();"
            " CREATE st:record SET v = kt:abc; CREATE st:after SET v = d'2030-01-01T00:00:00Z';"
            " CREATE st:before SET v = d'2000-01-01T00:00:00Z'; CREATE st:none;"
        )
        since = datetime(2020, 1, 1, tzinfo=timezone.utc)
        admitted = sorted(one_statement_result(await connection.query("SELECT VALUE record::id(id) FROM st WHERE v > $since;", {"since": since})))
        print(f"INFO S4 admitted by `v > $since` (datetime 2020-01-01): {admitted}")
        check("S4 control: datetime-after admitted, datetime-before excluded", "after" in admitted and "before" not in admitted, admitted)
        check("S4 admits exactly {array, object, record, uuid, after}", admitted == sorted(["array", "object", "record", "uuid", "after"]), admitted)
        # S5 option<datetime> on SCHEMAFULL: NULL vs Python None
        await connection.query("DEFINE TABLE sf SCHEMAFULL; DEFINE FIELD n ON sf TYPE string; DEFINE FIELD t ON sf TYPE option<datetime>;")
        outcomes: dict[str, str] = {}
        for label, statement, params in (
            ("literal NULL", "CREATE sf:null SET n = 'a', t = NULL;", None),
            ("string (control)", "CREATE sf:string SET n = 'b', t = 'x';", None),
            ("datetime (control)", "CREATE sf:dt SET n = 'c', t = $t;", {"t": since}),
            ("python None", "CREATE sf:pynone CONTENT $content;", {"content": {"n": "d", "t": None}}),
        ):
            try:
                await connection.query(statement, params) if params else await connection.query(statement)
                outcomes[label] = "accepted"
            except Exception as error:
                outcomes[label] = f"rejected ({type(error).__name__})"
        stored = one_statement_result(await connection.query("SELECT t = NONE AS is_none, t = NULL AS is_null FROM ONLY sf:pynone;"))
        print(f"INFO S5 outcomes: {outcomes}; sf:pynone stored: {stored!r}")
        check("S5 literal NULL rejected; None accepted; controls as expected", outcomes["literal NULL"].startswith("rejected") and outcomes["string (control)"].startswith("rejected") and outcomes["datetime (control)"] == "accepted" and outcomes["python None"] == "accepted" and stored.get("is_none") is True, outcomes)
    finally:
        await connection.query(f"REMOVE DATABASE IF EXISTS {DATABASE};")
        gone = await connection.query("INFO FOR NS;")
        check("cleanup: throwaway DB removed", DATABASE not in str(gone), DATABASE)
        await connection.close()
        try:
            await connection.close()
            check("S6 close() twice raises nothing", True, "ok")
        except Exception as error:
            check("S6 close() twice raises nothing", False, f"{type(error).__name__}: {error}")


def main() -> int:
    """Run every leg; non-zero on any failed expectation."""
    import importlib.metadata

    print(f"PROVENANCE python={sys.version.split()[0]} surrealdb={importlib.metadata.version('surrealdb')} at {surrealdb.__file__} store={TEST_URL} db={DATABASE}")
    offline()
    asyncio.run(store())
    print(f"FAILS={FAILS}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
