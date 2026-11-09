"""conform-sdk3-66 step-5 DDL-convergence probe (AFTER side).

Connects with the conformance image's SDK to the minted prod-copy DB on the TEST store (:18000 only,
asserted), reads INFO FOR DB + INFO FOR TABLE for every table, and counts ``scope IS NONE`` rows on the
tables the dump showed as pre-63 / un-migrated. Writes JSON to --out. Credentials come from the env
names the conform config declares; they are never printed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from urllib.parse import urlparse

from surrealdb import AsyncSurreal

TEST_STORE_PORT = 18000
SCOPE_TABLES = ("agent", "brief", "finding", "memory", "message", "task")


def single(result):
    """Unwrap a one-statement result the SDK may serve as a one-element list."""
    return result[0] if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict) else result


def count_of(result) -> int:
    """The ``n`` of a ``SELECT count() AS n … GROUP ALL``, served as rows or as ``[rows]``; 0 rows ⇒ 0."""
    rows = result[0] if result and isinstance(result[0], list) else result
    return rows[0]["n"] if rows else 0


async def main() -> None:
    """Read the post-boot schema of the copy and write it as JSON."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if urlparse(args.url).port != TEST_STORE_PORT:
        raise SystemExit(f"refusing: probe is bound to the TEST store port {TEST_STORE_PORT}")
    async with AsyncSurreal(args.url) as db:
        await db.signin({"username": os.environ["CONFORM_SURREAL_USER"], "password": os.environ["CONFORM_SURREAL_PASS"]})
        await db.use(args.namespace, args.database)
        info_db = single(await db.query("INFO FOR DB"))
        tables = sorted(info_db["tables"].keys())
        per_table = {}
        for table in tables:
            per_table[table] = single(await db.query(f"INFO FOR TABLE {table}"))
        scope_none = {}
        for table in SCOPE_TABLES:
            if table in tables:
                rows = await db.query(f"SELECT count() AS n FROM {table} WHERE scope IS NONE GROUP ALL")
                total = await db.query(f"SELECT count() AS n FROM {table} GROUP ALL")
                scope_none[table] = {"scope_none": count_of(rows), "rows": count_of(total)}
    with open(args.out, "w") as handle:
        json.dump({"db": info_db, "tables": per_table, "scope_none": scope_none}, handle, indent=1, default=str)
    print("tables", len(tables), "scope_none", json.dumps(scope_none))


if __name__ == "__main__":
    asyncio.run(main())
