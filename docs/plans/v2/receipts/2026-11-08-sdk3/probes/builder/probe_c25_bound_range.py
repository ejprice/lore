"""C row #25, candidate 2 with BOUND parameters (R43 R-9 follow-up): production never interpolates, so can the
record-id range ride a bound $param? Same fixture as probe_c25_id_range.py (1000 `name` rows + 2 traps).
F3 one prefix:  SELECT VALUE id FROM $r, $r = RecordID('name', Range(BoundIncluded(lo), BoundExcluded(hi)))
F4 two prefixes: SELECT VALUE id FROM $r1, $r2 (production ORs several prefixes) — expected = union of both.
CONTROL: the production mirror form over the same prefixes (string::starts_with(value, $p) OR ...).
Each: EXPLAIN plan + row count + exact-set check."""
import asyncio, json, uuid
from surrealdb import AsyncSurreal, BoundExcluded, BoundIncluded, Range, RecordID
URL = "ws://127.0.0.1:18000/rpc"
assert "18500" not in URL
def rng(lo, hi):
    return RecordID("name", Range(BoundIncluded(lo), BoundExcluded(hi)))
async def main() -> None:
    db = AsyncSurreal(URL); await db.signin({"username": "root", "password": "spikeroot"})
    name = f"probe_c25b_{uuid.uuid4().hex[:8]}"
    await db.query("DEFINE NAMESPACE IF NOT EXISTS lore_test"); await db.use("lore_test", name)
    await db.query(f"DEFINE DATABASE IF NOT EXISTS {name}"); await db.use("lore_test", name)
    try:
        await db.query("DEFINE TABLE name SCHEMAFULL")
        await db.query("DEFINE FIELD value ON name TYPE string")
        await db.query("DEFINE INDEX name_value ON name FIELDS value")
        keys = [f"pkg.m{i}.sym{j}" for i in range(50) for j in range(20)] + ["pkg.m1/x", "pkg.m10.sym0x"]
        await db.query("INSERT INTO name $rows", {"rows": [{"id": RecordID("name", k), "value": k} for k in keys]})
        one = {k for k in keys if k.startswith("pkg.m1.")}
        two = one | {k for k in keys if k.startswith("pkg.m2.")}
        forms = (
            ("F3 FROM $r (bound range)", "SELECT VALUE id FROM $r", {"r": rng("pkg.m1.", "pkg.m1/")}, one),
            ("F4 FROM $r1, $r2 (two bound ranges)", "SELECT VALUE id FROM $r1, $r2",
             {"r1": rng("pkg.m1.", "pkg.m1/"), "r2": rng("pkg.m2.", "pkg.m2/")}, two),
            ("CONTROL mirror, two prefixes", "SELECT VALUE id FROM name WHERE string::starts_with(value, $p0) OR string::starts_with(value, $p1)",
             {"p0": "pkg.m1.", "p1": "pkg.m2."}, two),
        )
        for label, stmt, params, expected in forms:
            try:
                plan = await db.query(stmt + " EXPLAIN", params)
                print("#25", label, "PLAN", json.dumps(plan, default=str)[:600])
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
