"""INFO FOR NS lore_test on the TEST store: count databases (positive control) and list any test_dump_20261108* (must be none)."""
import asyncio, os
from surrealdb import AsyncSurreal
async def main() -> None:
    async with AsyncSurreal("ws://127.0.0.1:18000/rpc") as db:
        await db.signin({"username": os.environ["CONFORM_SURREAL_USER"], "password": os.environ["CONFORM_SURREAL_PASS"]})
        await db.use("lore_test", "lore_test")
        res = await db.query("INFO FOR NS")
        info = res[0] if isinstance(res, list) else res
        names = sorted(info["databases"].keys())
        print("lore_test databases total:", len(names))
        print("test_dump_20261108* present:", [n for n in names if n.startswith("test_dump_20261108")])
        print("test_dump_* present (any date):", len([n for n in names if n.startswith("test_dump_")]))
asyncio.run(main())
