"""Packet SDK3 contract, round 3 — operator rulings R3 + R4: a large file INDEXES, in ONE transaction,
with BATCHED rows, under a bound on what strains the server — and a file still refused is NAMED.

R3 (measured 2026-11-07 on production lore-lore boot): ``loremaster/tests/test_comms_tool.py`` composes to
5,113 statements; ``compose()`` refused it against ``TXN_STATEMENT_HARD_CAP = 5000``, so the file was
absent from the index (no chunks, no graph) and the served status said only ``files_failed: 1``.
R4: the file's write stays ONE atomic transaction, but rows travel as one batched ``INSERT`` /
``INSERT RELATION`` per table, so the statement count scales with TABLES, not rows; the cap becomes a
bound on rows or bytes. Rider pins, each here:

* (4a) a test_comms_tool.py-sized file indexes and is searchable — ``TestALargeFileIndexesAndIsSearchable``;
* (4b) a mutation restoring per-row statements reddens the bound pin —
  ``TestTheStatementCountDoesNotGrowWithRows`` is that pin (packet doc §4, mutation M-R4);
* (3)  a file still refused is NAMED on a served surface — ``TestARefusedFileIsNamedOnTheServedStatus``;
* (1)  RELATE / INSERT RELATION do not validate endpoints (store reference §4, #105) — so a batched graph
  write that lands edges before (or without) their endpoints writes DANGLING edges with no error:
  ``TestNoBatchedEdgeDangles``.

The measurement behind the bound (R4 rider 2), OFFLINE — the production pure builders composed with no
socket — is in the packet doc §4.R4 (instrument pasted verbatim there): test_comms_tool.py = 511 chunk
rows, 511 code_node, 1,204 name, 1,858 refers, 1,022 answers_to, 1 file, 1 file_text = 5,108 rows in
5,113 statements (the 5 extra are the per-table DELETEs); the chunk rows carry ~80% of the bytes.

The fixture is SYNTHETIC and sized by construction (``_big_module_source``) rather than a copy of
test_comms_tool.py, so it cannot shrink under the pin when that file is edited; its premise asserts it
writes more rows than the retired statement cap.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import _sdk_guard
import pytest
import pytest_asyncio
from _surreal_harness import PRODUCTION_DIM, connect_admin, make_env, run
from loremaster.server import AppContext
from loremaster.store import _txn
from loremaster.store.surreal_schema import ANSWERS_TO_RELATION, REFERS_RELATION
from test_mcp_server import _config, _make_context, _slug, _surreal_test_env  # noqa: F401 - autouse env

logger = logging.getLogger(__name__)

# The live tier ``test_mcp_server._config`` declares.
_TIER = "custom"

# The retired per-transaction STATEMENT cap (R3). Kept only as the premise yardstick: a file whose rows
# exceed it is a file a per-row-statement build could not have written in one transaction.
_RETIRED_STATEMENT_CAP = 5000

# The large fixture: functions, and calls each function makes (each call is one ``refers`` edge). 600 x 4
# composes to 6,612 statements under the per-row shape (measured offline with the packet doc §4.R4
# instrument): ~6,600 rows, comfortably over the retired cap.
_BIG_PATH = "pkg/big_module.py"
_BIG_FUNCTIONS = 600
_CALLS_PER_FUNCTION = 4

# The small fixture for the growth pin: the same shape at a tenth of the rows.
_SMALL_PATH = "pkg/small_module.py"
_SMALL_FUNCTIONS = 60

# The growth bound: going from the small file to the big one may add at most one statement per this
# many additional rows. A per-row build adds one statement PER row; a per-table batched build adds none;
# a build that chunks a huge INSERT into slices of several hundred rows (for message size) still passes.
_ROWS_PER_ADDED_STATEMENT = 100

# The refusal pin: a row cap shrunk far below the fixture (and a value distinctive enough that its
# appearance in the served status is the bound being named, not a coincidence of some other number).
_SHRUNK_ROW_CAP = 1009
_REFUSED_PATH = "pkg/refused_module.py"

# A phrase only the marker function carries, for the search leg.
_SEARCH_MARKER = "quokka ledger reconciliation"


def _big_module_source(functions: int, *, marker: bool = True) -> str:
    """A Python module of ``functions`` functions, each calling ``_CALLS_PER_FUNCTION`` others (refers
    edges) — one chunk, one code_node, two answers_to and ~5 refers per function."""
    lines = ['"""Synthetic module for the SDK3 R4 batching pins."""', ""]
    for index in range(functions):
        calls = "\n".join(
            f"    total += fn_{(index * 7 + call * 13 + 1) % functions}(depth - 1) if depth else 0"
            for call in range(_CALLS_PER_FUNCTION)
        )
        lines.append(
            f"def fn_{index}(depth: int) -> int:\n"
            f'    """Function {index}."""\n'
            f"    total = {index}\n{calls}\n    return total\n"
        )
    if marker:
        lines.append(
            "def quokka_marker() -> str:\n"
            f'    """The {_SEARCH_MARKER} marker: a phrase no other chunk carries."""\n'
            "    return 'quokka'\n"
        )
    return "\n".join(lines)


@pytest_asyncio.fixture()
async def live_root(tmp_path: Path) -> Path:
    root = tmp_path / "live"
    (root / "pkg").mkdir(parents=True)
    return root


# Each AppContext's database (``_config`` defaults the database to the project slug), so the pins can
# read the store directly with an admin connection.
_DATABASE_OF: dict[int, str] = {}


@pytest_asyncio.fixture()
async def context(tmp_path: Path, live_root: Path) -> AsyncIterator[AppContext]:
    """A booted AppContext (real store, manifest, graph; fake embedder) over an EMPTY live tier."""
    slug = _slug()
    config = _config(slug, live_root)
    ctx = await _make_context(config=config, tmp_path=tmp_path)
    _DATABASE_OF[id(ctx)] = config.effective_surreal_database
    try:
        yield ctx
    finally:
        _DATABASE_OF.pop(id(ctx), None)
        await ctx.aclose()


def _env_of(ctx: AppContext) -> Any:
    return make_env(database=_DATABASE_OF[id(ctx)], dim=PRODUCTION_DIM)


async def _rows_written_for(ctx: AppContext, path: str) -> int:
    """Rows the file's index write landed in its own tables (shared ``name`` rows excluded)."""
    env = _env_of(ctx)
    admin = await connect_admin(env)
    try:
        counts = await run(
            admin,
            "RETURN [count((SELECT id FROM chunk WHERE file_path = $f)), "
            "count((SELECT id FROM code_node WHERE file_path = $f)), "
            f"count((SELECT id FROM {REFERS_RELATION} WHERE src_file_path = $f)), "
            f"count((SELECT id FROM {ANSWERS_TO_RELATION} WHERE file_path = $f))]",
            {"f": path},
        )
    finally:
        await admin.close()
    return int(sum(counts))


class _TransactionSpy:
    """Records every SDK ``query_raw`` request whose text opens a transaction, with the number of
    per-statement results the store answered — through the SDK guard's public call-hook chain, so the
    autouse guard's own caller attribution is untouched."""

    def __init__(self) -> None:
        self.transactions: list[int] = []

    def hook(self, event: _sdk_guard.CallEvent, coro: Any) -> Any:
        if event.method != "query_raw":
            return coro
        text = event.args[0] if event.args else event.kwargs.get("query", "")
        if "BEGIN" not in str(text).upper():
            return coro

        async def _recorded() -> Any:
            response = await coro
            results = response.get("result") if isinstance(response, dict) else None
            self.transactions.append(len(results) if isinstance(results, list) else -1)
            return response

        return _recorded()


@pytest.fixture()
def transaction_spy(monkeypatch: pytest.MonkeyPatch) -> Iterator[_TransactionSpy]:
    spy = _TransactionSpy()
    monkeypatch.setattr(_sdk_guard, "_CALL_HOOKS", [*_sdk_guard._CALL_HOOKS, spy.hook])
    yield spy


class TestALargeFileIndexesAndIsSearchable:
    """R4 rider (4a). The file R3 lost — larger than the old statement cap — lands ``indexed`` and its
    content is findable through the served search."""

    async def test_a_file_over_the_retired_statement_cap_is_indexed_and_found(
        self, context: AppContext, live_root: Path
    ) -> None:
        (live_root / _BIG_PATH).write_text(_big_module_source(_BIG_FUNCTIONS), encoding="utf-8")
        await context.indexer.index_all()

        status = await context.index()
        assert status.files_failed == 0, (
            f"the large file was refused ({status.files_failed} failed): R3's defect — a file over the "
            f"old statement cap is absent from the index"
        )
        rows = await _rows_written_for(context, _BIG_PATH)
        assert rows > _RETIRED_STATEMENT_CAP, (
            f"premise: the fixture must write more rows than the retired {_RETIRED_STATEMENT_CAP}-statement "
            f"cap (it wrote {rows}) — otherwise it proves nothing about a per-row build"
        )
        results = await context.search(_SEARCH_MARKER, k=10)
        joined = "\n".join(result.formatted for result in results)
        assert _BIG_PATH in joined, f"the indexed large file is not searchable: {joined[:400]!r}"


class TestTheStatementCountDoesNotGrowWithRows:
    """R4 rider (4b) — THE BOUND PIN the per-row mutation (M-R4) must redden. The file's index write is
    ONE transaction (one request carrying ``BEGIN``), and the number of statements in it is set by the
    tables it writes, not by the rows: ten times the rows may add at most one statement per
    ``_ROWS_PER_ADDED_STATEMENT`` rows. Rejected option C (a file split across transactions) fails the
    one-transaction leg; the pre-R4 per-row shape fails the growth leg."""

    async def test_ten_times_the_rows_is_one_transaction_with_no_more_statements(
        self, context: AppContext, transaction_spy: _TransactionSpy, live_root: Path
    ) -> None:
        sizes: dict[str, tuple[int, int]] = {}
        for path, functions in ((_SMALL_PATH, _SMALL_FUNCTIONS), (_BIG_PATH, _BIG_FUNCTIONS)):
            source = _big_module_source(functions, marker=False)
            (live_root / path).write_text(source, encoding="utf-8")
            transaction_spy.transactions.clear()
            outcome = await context.indexer.index_file(_TIER, path, source)
            assert outcome.state == "indexed", f"premise: {path} must index (got {outcome.state!r})"
            assert len(transaction_spy.transactions) == 1, (
                f"{path}'s index write was {len(transaction_spy.transactions)} transactions "
                f"({transaction_spy.transactions}) — R4 keeps ONE atomic transaction per file "
                f"(a reader must never see a half-indexed file)"
            )
            sizes[path] = (transaction_spy.transactions[0], await _rows_written_for(context, path))

        (small_statements, small_rows), (big_statements, big_rows) = sizes[_SMALL_PATH], sizes[_BIG_PATH]
        assert big_rows >= 9 * small_rows, f"premise: the big file writes ~10x the rows ({sizes})"
        added_statements = big_statements - small_statements
        allowed = (big_rows - small_rows) // _ROWS_PER_ADDED_STATEMENT
        assert added_statements <= allowed, (
            f"{big_rows - small_rows} more rows cost {added_statements} more statements "
            f"(small: {small_statements} statements / {small_rows} rows; big: {big_statements} / {big_rows}) "
            f"— the statement count still scales with ROWS. R4: one batched INSERT / INSERT RELATION per "
            f"table, so it scales with tables."
        )


class TestARefusedFileIsNamedOnTheServedStatus:
    """R4 rider (3). A file the row bound still refuses must not be silently absent: the served
    ``lore_index`` status names it AND the bound that refused it (a fact, not "some files failed").
    Driven by shrinking the shared row cap below a modest file — the cap must be the ONE module value
    every compose reads, or the shrink would not reach the indexer."""

    async def test_the_refused_file_and_its_bound_appear_in_the_served_status(
        self, context: AppContext, live_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(_txn, "TXN_ROW_HARD_CAP", _SHRUNK_ROW_CAP)
        (live_root / _REFUSED_PATH).write_text(
            _big_module_source(_SMALL_FUNCTIONS * 2, marker=False), encoding="utf-8"
        )
        await context.indexer.index_all()

        status = await context.index()
        assert status.files_failed >= 1, "premise: the shrunk row cap refused the file"
        served = status.model_dump_json()
        assert _REFUSED_PATH in served, (
            f"the served index status counts a failed file but does not NAME it — the consumer cannot "
            f"tell which file is missing from the index: {served[:600]!r}"
        )
        assert str(_SHRUNK_ROW_CAP) in served, (
            "the served status names the refused file but not the BOUND that refused it — a reason "
            "must be a fact the reader can act on (the row cap), not a generic failure"
        )


class TestNoBatchedEdgeDangles:
    """R4 rider (1) / store reference §4 (#105): ``RELATE`` and ``INSERT RELATION`` write an edge whatever
    its endpoints, so a batched graph write that inserts edges before (or without) their ``name`` /
    ``code_node`` endpoints leaves DANGLING edges with no error. Every edge the large file wrote must
    join two records that exist."""

    async def test_every_edge_of_the_large_file_joins_two_existing_records(
        self, context: AppContext, live_root: Path
    ) -> None:
        source = _big_module_source(_BIG_FUNCTIONS, marker=False)
        (live_root / _BIG_PATH).write_text(source, encoding="utf-8")
        outcome = await context.indexer.index_file(_TIER, _BIG_PATH, source)
        assert outcome.state == "indexed", f"premise: the large file must index (got {outcome.state!r})"

        admin = await connect_admin(_env_of(context))
        try:
            # Each edge table's OWN file column (schema: refers carries its source's, answers_to its
            # node's), never ``in.file_path`` — a dangling ``in`` has no file_path to match.
            for relation, file_column in (
                (REFERS_RELATION, "src_file_path"),
                (ANSWERS_TO_RELATION, "file_path"),
            ):
                total, dangling = await run(
                    admin,
                    f"RETURN [count((SELECT id FROM {relation} WHERE {file_column} = $f)), "
                    f"count((SELECT id FROM {relation} WHERE {file_column} = $f "
                    f"AND (!record::exists(in) OR !record::exists(out))))]",
                    {"f": _BIG_PATH},
                )
                assert total > 0, f"premise: the large file wrote {relation} edges"
                assert dangling == 0, (
                    f"{dangling} of {total} {relation} edges point at a record that does not exist — a "
                    f"batched edge insert landed before (or without) its endpoints"
                )
        finally:
            await admin.close()
