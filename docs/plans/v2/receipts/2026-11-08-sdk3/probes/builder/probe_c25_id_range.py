"""C row #25, the SECOND ruled candidate (R43 R-9): can an ID RANGE replace the name.value mirror?
3.3.5 TEST store (ws://127.0.0.1:18000, throwaway database), SDK 3.0.0. Fixture: 1000 `name` rows keyed by their
own value `pkg.m<i>.sym<j>` (i<50, j<20) + two TRAPS that a wrong bound would admit: `pkg.m1/x` (just past the
'.' -> '/' increment) and `pkg.m10.sym0` (a sibling module sharing the text prefix `pkg.m1`).
Prefix `pkg.m1.` must select EXACTLY the 20 `pkg.m1.sym<j>` rows.
Forms: F1 WHERE id >= $lo AND id < $hi (bound RecordIDs) · F2 the FROM range literal name:⟨lo⟩..⟨hi⟩
(interpolated, PROBE ONLY) · CONTROL the production mirror form string::starts_with(value, $p) (IndexScan).
Each: EXPLAIN plan + selected-row count + exact-set check."""
import asyncio, json, uuid
from surrealdb import AsyncSurreal, RecordID
URL = "ws://127.0.0.1:18000/rpc"
assert "18500" not in URL
PREFIX, HI = "pkg.m1.", "pkg.m1/"   # '/' is '.' + 1: the classic increment upper bound for a prefix ending in '.'
async def main() -> None:
    db = AsyncSurreal(URL); await db.signin({"username": "root", "password": "spikeroot"})
    name = f"probe_c25r_{uuid.uuid4().hex[:8]}"
    await db.query("DEFINE NAMESPACE IF NOT EXISTS lore_test"); await db.use("lore_test", name)
    await db.query(f"DEFINE DATABASE IF NOT EXISTS {name}"); await db.use("lore_test", name)
    try:
        await db.query("DEFINE TABLE name SCHEMAFULL")
        await db.query("DEFINE FIELD value ON name TYPE string")
        await db.query("DEFINE INDEX name_value ON name FIELDS value")
        keys = [f"pkg.m{i}.sym{j}" for i in range(50) for j in range(20)] + ["pkg.m1/x", "pkg.m10.sym0x"]
        await db.query("INSERT INTO name $rows", {"rows": [{"id": RecordID("name", k), "value": k} for k in keys]})
        expected = {k for k in keys if k.startswith(PREFIX)}
        print("fixture rows", len(keys), "expected", len(expected))
        forms = (
            ("F1 id >= $lo AND id < $hi", "SELECT VALUE id FROM name WHERE id >= $lo AND id < $hi",
             {"lo": RecordID("name", PREFIX), "hi": RecordID("name", HI)}),
            ("F2 FROM range literal", f"SELECT VALUE id FROM name:⟨{PREFIX}⟩..⟨{HI}⟩", {}),
            ("CONTROL mirror starts_with", "SELECT VALUE id FROM name WHERE string::starts_with(value, $p)", {"p": PREFIX}),
        )
        for label, stmt, params in forms:
            try:
                plan = await db.query(stmt + " EXPLAIN", params)
                print("#25", label, "PLAN", json.dumps(plan, default=str)[:500])
            except Exception as error:  # noqa: BLE001
                print("#25", label, "PLAN RAISES", type(error).__name__, str(error)[:200])
            try:
                got = await db.query(stmt, params)
                rows = got[0] if got and isinstance(got[0], list) else got
                selected = {str(r.id) for r in rows}
                print("#25", label, "rows", len(selected), "exact", selected == expected,
                      "extra", sorted(selected - expected)[:5], "missing", len(expected - selected))
            except Exception as error:  # noqa: BLE001
                print("#25", label, "RAISES", type(error).__name__, str(error)[:200])
    finally:
        await db.query(f"REMOVE DATABASE IF EXISTS {name}"); await db.close()
asyncio.run(main())
