"""Packet 07 item 4 — is the QUERY-TOO-COMPLEX (expression recursion depth) rejection
still reachable on SurrealDB 3.2.4?

The classifier's ``_ERROR_CLASS_QUERY_TOO_COMPLEX`` branch keys on
``_QUERY_RECURSION_DEPTH_MARKER = "recursion depth"`` — the live text of finding #66's
"Parse error: Exceeded expression recursion depth limit ... this expression nests or
chains operators too deeply" on 3.1.5 (40 fulltext tokens / 120 ``@@`` clauses rejected).

⚠ THE ANSWER, AND THE CORRECTION THAT PRODUCED IT (a "probe needs a control" self-catch,
2026-08-17): the branch is **LIVE on 3.2.4** — proven by the EXISTING LIVE TESTS, NOT by
this probe. Every isolated shape this probe tries is a FALSE-NEGATIVE:

  * simple-operator chains (``1=1``/``v=i`` OR-chains, nested parens, chained ``+``, nested
    fn calls, nested subqueries) execute fine to extreme sizes (40000 OR-clauses, 64000
    nested parens);
  * even ``probe_fulltext_at_chain`` — a bare ``(f1 @@ $p OR f2 @@ $p) AND ...`` chain at
    400 ``@@`` clauses — executes FINE in isolation.

The recursion-depth limit is tripped ONLY by the FULL ``hybrid_search`` / ``recall``
RRF-fusion query (the ``@@`` chain EMBEDDED in ``search::score`` / ``search::rrf`` / the
dual-arm UNION — a much deeper parse tree than the predicate alone), at finding #66's
~40-token / 120-clause boundary. Reproducing that whole query in a standalone probe is not
worth it: **the authoritative instrument already exists and is green on 3.2.4** —
``test_bypassing_both_clamps_still_raises_a_classified_store_error``
(``test_surreal_store.py::TestResidualRejectionStillLaunders`` +
``test_memory_backend.py::TestRecursionDepthClassificationAtRecallSeam``) run the REAL path
with the clamps bypassed and assert the laundered "query too complex" label, which passes
ONLY if the engine still emits "recursion depth". So ``_ERROR_CLASS_QUERY_TOO_COMPLEX`` is
LIVE and needs no change. This probe's value is the NEGATIVE-space receipt: the limit is a
whole-query-depth property, not reproducible from any single construct in isolation.

Targets ONLY spike-surreal (ws://127.0.0.1:18000). NEVER :18500 (production).

Usage:
    cd loremaster && uv run python ../scripts/probe_query_complexity_07.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "loremaster"))

from loremaster.store._txn import signin_credentials  # noqa: E402
from pydantic import SecretStr  # noqa: E402
from surrealdb import AsyncSurreal  # noqa: E402

URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = SecretStr("spikeroot")
NAMESPACE = "lore_test"


async def _connect(database: str) -> Any:
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=PASSWORD))
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await connection.use(NAMESPACE, database)
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    return connection


async def _run(connection: Any, statement: str) -> tuple[str, str]:
    """Return (outcome, text): outcome ∈ {ok, err, raised}; text = the ERR/exception text."""
    try:
        raw = await connection.query_raw(statement)
        for entry in raw.get("result") or []:
            if isinstance(entry, dict) and entry.get("status") == "ERR":
                return "err", str(entry.get("result"))
        return "ok", ""
    except Exception as error:  # noqa: BLE001 — probe: report whatever surfaced
        return "raised", f"{type(error).__name__}: {error}"


def _report(label: str, outcome: str, text: str) -> None:
    hit = "recursion depth" in text.lower()
    marker = "  <<< 'recursion depth' MARKER PRESENT" if hit else ""
    snippet = text if len(text) <= 200 else text[:200] + "…"
    print(f"  [{outcome:6}] {label}: {snippet!r}{marker}")


async def probe_or_chains(connection: Any) -> None:
    print("\n== OR-clause chains (finding #66's original shape) ==")
    for count in (400, 1000, 2000, 4000, 8000, 16000):
        predicate = " OR ".join(["1 = 1"] * count)
        outcome, text = await _run(connection, f"RETURN ({predicate})")
        _report(f"{count} OR-clauses", outcome, text)


async def probe_nested_parens(connection: Any) -> None:
    print("\n== nested-parens depth ==")
    for depth in (100, 500, 1000, 2000, 4000):
        expr = "(" * depth + "true" + ")" * depth
        outcome, text = await _run(connection, f"RETURN {expr}")
        _report(f"paren depth {depth}", outcome, text)


async def probe_arithmetic_chain(connection: Any) -> None:
    print("\n== chained arithmetic (+ operators) ==")
    for count in (1000, 4000, 8000, 16000):
        expr = "+".join(["1"] * count)
        outcome, text = await _run(connection, f"RETURN {expr}")
        _report(f"{count} + operators", outcome, text)


async def probe_nested_arrays(connection: Any) -> None:
    print("\n== nested array literal depth ==")
    for depth in (100, 500, 1000, 2000):
        expr = "[" * depth + "]" * depth
        outcome, text = await _run(connection, f"RETURN {expr}")
        _report(f"array nest depth {depth}", outcome, text)


async def probe_deep_parens(connection: Any) -> None:
    print("\n== VERY deep nested parens (recursive-descent stack trigger) ==")
    for depth in (8000, 16000, 32000, 64000):
        expr = "(" * depth + "true" + ")" * depth
        outcome, text = await _run(connection, f"RETURN {expr}")
        _report(f"paren depth {depth}", outcome, text)


async def probe_nested_functions(connection: Any) -> None:
    print("\n== nested function calls array::flatten(...) ==")
    for depth in (500, 2000, 8000, 32000):
        expr = "array::flatten(" * depth + "[[1]]" + ")" * depth
        outcome, text = await _run(connection, f"RETURN {expr}")
        _report(f"fn nest depth {depth}", outcome, text)


async def probe_nested_subqueries(connection: Any) -> None:
    print("\n== nested SELECT subqueries ==")
    for depth in (50, 200, 500, 1000):
        expr = "SELECT * FROM (" * depth + "SELECT 1" + ")" * depth
        outcome, text = await _run(connection, expr)
        _report(f"subquery nest depth {depth}", outcome, text)


async def probe_where_or_on_a_table(connection: Any) -> None:
    print("\n== WHERE-clause OR chain on a real table (SIMPLE '=' operator — still a proxy) ==")
    await connection.query("DEFINE TABLE cx SCHEMALESS; CREATE cx:1 SET v = 1;")
    for count in (1000, 4000, 16000, 40000):
        predicate = " OR ".join([f"v = {i}" for i in range(count)])
        outcome, text = await _run(connection, f"SELECT * FROM cx WHERE {predicate}")
        _report(f"WHERE {count} '=' OR-clauses", outcome, text)


async def probe_fulltext_at_chain(connection: Any) -> None:
    """THE AUTHORITATIVE shape — finding #66's real BM25 predicate:
    ``(f1 @@ $ft0 OR f2 @@ $ft0) AND (f1 @@ $ft1 OR f2 @@ $ft1) AND ...``, which needs a
    FULLTEXT-indexed field. Mirrors ``LocalMemoryBackend._build_fulltext_predicate``.
    """
    print("\n== FULLTEXT @@ OR/AND chain (THE #66 shape — the real trigger) ==")
    await connection.query(
        "DEFINE ANALYZER IF NOT EXISTS ftq TOKENIZERS blank FILTERS lowercase;"
    )
    await connection.query("DEFINE TABLE ftx SCHEMALESS;")
    await connection.query("DEFINE INDEX ftx_f1 ON ftx FIELDS f1 FULLTEXT ANALYZER ftq BM25;")
    await connection.query("DEFINE INDEX ftx_f2 ON ftx FIELDS f2 FULLTEXT ANALYZER ftq BM25;")
    await connection.query("CREATE ftx:1 SET f1 = 'alpha beta', f2 = 'gamma delta';")
    fields = ("f1", "f2")
    for tokens in (30, 60, 120, 200):
        clauses = []
        params: dict[str, Any] = {}
        for index in range(tokens):
            param = f"__ft{index}"
            params[param] = f"tok{index}"
            clauses.append("(" + " OR ".join(f"{field} @@ ${param}" for field in fields) + ")")
        predicate = "(" + " AND ".join(clauses) + ")"
        statement = f"SELECT * FROM ftx WHERE {predicate}"
        try:
            raw = await connection.query_raw(statement, params)
            outcome, text = "ok", ""
            for entry in raw.get("result") or []:
                if isinstance(entry, dict) and entry.get("status") == "ERR":
                    outcome, text = "err", str(entry.get("result"))
                    break
        except Exception as error:  # noqa: BLE001
            outcome, text = "raised", f"{type(error).__name__}: {error}"
        _report(f"{tokens} tokens = {tokens * len(fields)} @@ clauses", outcome, text)


async def main() -> None:
    database = f"probe07q_{uuid.uuid4().hex}"
    connection = await _connect(database)
    version = await connection.version()
    print(f"engine version: {version}")
    print(f"probe database: {NAMESPACE}:{database} @ {URL}")
    try:
        await probe_or_chains(connection)
        await probe_nested_parens(connection)
        await probe_arithmetic_chain(connection)
        await probe_nested_arrays(connection)
        await probe_deep_parens(connection)
        await probe_nested_functions(connection)
        await probe_nested_subqueries(connection)
        await probe_where_or_on_a_table(connection)
        await probe_fulltext_at_chain(connection)
    finally:
        await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
