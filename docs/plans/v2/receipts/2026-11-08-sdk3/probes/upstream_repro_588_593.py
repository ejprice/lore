"""Minimal repros for two surrealdb==3.0.0 Python SDK defects (#593, #588), run against the TEST store only."""

import asyncio
import importlib.metadata
import sys
import uuid

sys.path.insert(0, "loremaster/tests")
import _surreal_harness as harness  # noqa: E402  (test-store credentials; never printed)

from surrealdb import AsyncSurreal  # noqa: E402
from surrealdb.data.types.datetime import PreciseDatetime  # noqa: E402

TEST_URL = harness.surreal_url()
assert ":18000" in TEST_URL, TEST_URL  # never production


def repro_593() -> None:
    """PreciseDatetime equality and ordering ignore the nanosecond remainder."""
    earlier = PreciseDatetime(2026, 1, 1, 0, 0, 0, 123456, nanosecond=100)
    later = PreciseDatetime(2026, 1, 1, 0, 0, 0, 123456, nanosecond=900)
    print("593 earlier.isoformat_with_nanoseconds():", earlier.isoformat_with_nanoseconds())
    print("593 later.isoformat_with_nanoseconds():  ", later.isoformat_with_nanoseconds())
    print("593 earlier == later:", earlier == later, "(expected False)")
    print("593 earlier < later: ", earlier < later, "(expected True)")
    print("593 max(later, earlier) is later:", max(later, earlier) is later, "(expected True)")
    print("593 max(earlier, later) is later:", max(earlier, later) is later, "(expected True)")
    print("593 len({earlier, later}):", len({earlier, later}), "(expected 2)")


async def repro_588() -> None:
    """batch() raises the cancellation notice, not the THROW, when the THROW's text quotes the notice."""
    namespace, database = "lore_test", f"repro588_{uuid.uuid4().hex}"
    db = AsyncSurreal(TEST_URL)
    await db.connect()
    await db.signin({"username": harness.surreal_user(), "password": harness.surreal_password().get_secret_value()})
    await db.query(f"DEFINE NAMESPACE IF NOT EXISTS {namespace}")
    await db.use(namespace, "default")
    await db.query(f"DEFINE DATABASE {database}")
    await db.use(namespace, database)
    try:
        for label, message in (
            ("control", "lease lost"),
            ("defect", "lease lost: a statement was not executed due to a failed transaction"),
        ):
            try:
                await db.batch().query("CREATE item:1 SET n = 1").query(f"THROW {message!r}").execute()
                print(f"588 {label}: NO RAISE (unexpected)")
            except Exception as error:  # noqa: BLE001  (we report whatever the SDK raises)
                print(f"588 {label}: raised {type(error).__name__}: {error}")
    finally:
        await db.use(namespace, "default")
        await db.query(f"REMOVE DATABASE {database}")
        await db.close()


if __name__ == "__main__":
    print("surrealdb", importlib.metadata.version("surrealdb"), "| python", sys.version.split()[0])
    repro_593()
    asyncio.run(repro_588())
