"""Packet SDK3 contract, round 3 — operator rulings R6 (F5) and R7 (F9 native): the engine's native
prefix match, and the runtime SDK guard's REACH over SDK 3.0's builder methods.

F9 (R7 replaces R6's F9 bullet): retire the ``>= $lo AND < $hi`` range lore uses in place of
``string::starts_with`` (store reference §2 "[PROBED] string::starts_with = TableScan", 3.1.5). On 3.3.5
the native form is index-served by range (scout-40, and re-probed for the multi-prefix OR lore emits:
packet doc §4.F9). Retired "with a pin + mutation like RP1–RP3 (the pin proves the native form is
index-served via the shared EXPLAIN walker)": the engine-fact pin here
(``TestTheNativePrefixMatchIsIndexServed``) and the production-statement pin
(``TestTheModulePrefixReachIsIndexServed``), each with a positive control
that shows the walker SEEING a TableScan. Mutation M-F9 (packet doc §4): defeat the index in
``SurrealCodeGraph._prefix_range_query`` (wrap ``value`` in a function) → the production pin reddens.
Bound, stated: F9's defect is gone on the ENGINE already, so neither pin can be RED at HEAD on a 3.3.5
store; a pin asserting which spelling production uses would be a source-spelling check, which needs
operator approval (global CLAUDE.md) — the retirement itself is therefore carried by the drop list, and
these pins guard that the native form stays index-served wherever it lands.

F5 (R6): ``tests/_sdk_guard.py`` wraps only ``inspect.iscoroutinefunction`` members, and SDK 3.0's
``query`` (and ``select``/``create``/``update``/``upsert``/``delete``/``insert``/``relate``, and the
``batch`` builder) are sync factories returning an awaitable builder — so under SDK 3.0 the guard and its
multi-statement check silently stop observing the one method every seam calls (instrument-lesson row 8).
"Widen ``_sdk_guard`` to the SDK 3.0 sync builder methods; observed ``query`` calls are a checked
variable": ``TestTheSdkGuardReachesTheBuilderDoors``. The door set is DERIVED from the installed SDK class
(a coroutine function, or a method whose annotated return type is awaitable / async-iterable / carries a
coroutine method), never hand-listed, and the derivation's own reach is a checked variable (it must
contain ``query``). GREEN at HEAD (SDK 2.0's doors are all coroutines); RED on SDK 3.0 with the guard as it
stands — the measured reason this pin exists.
"""

from __future__ import annotations

import inspect
import typing
from collections.abc import AsyncIterator
from typing import Any

import _sdk_guard
import pytest
import pytest_asyncio
from _governed_contract import explain, index_served, scans_table
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.store._txn import retry_on_conflict
from loremaster.store.surreal_schema import NAME_TABLE

# The production index the module-prefix reach must read (graph schema: ``name`` keyed by ``value``).
_NAME_VALUE_INDEX = f"{NAME_TABLE}_value"

# Name rows seeded so a TableScan and an index range are distinguishable plans (and results are checked).
_SEEDED_MODULES = 30
_SYMBOLS_PER_MODULE = 10

# Prefix sets the module-prefix reach emits: one, two and three frontier modules (OR'd), a multi-byte
# unicode module, and a prefix ending in the maximum codepoint (the range builder's special case).
_PREFIX_SETS: dict[str, list[str]] = {
    "one": ["pkg.m1."],
    "two": ["pkg.m1.", "pkg.m2."],
    "three_with_unicode": ["pkg.m1.", "pkg.m2.", "pkg.café."],
    "max_codepoint": [f"pkg.m1.{chr(0x10FFFF)}"],
}


def _a_function_defined_in_this_file() -> None:
    """The guard's witness when its notion of "production" is aimed at this file (the controls' idiom)."""


_THIS_FILE_ROOT = _sdk_guard._witness_file(_a_function_defined_in_this_file).parent


@pytest_asyncio.fixture()
async def store_env() -> AsyncIterator[SurrealEnv]:
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def name_table(store_env: SurrealEnv) -> AsyncIterator[Any]:
    """The PRODUCTION graph schema (``SurrealCodeGraph.ensure_ready``) with seeded ``name`` rows; yields an
    admin connection for EXPLAIN."""
    graph = SurrealCodeGraph(
        url=store_env.url,
        namespace=store_env.namespace,
        database=store_env.database,
        user=store_env.user,
        password=store_env.password,
        tier_roots={},
        project_roots=[],
    )
    admin = await connect_admin(store_env)
    try:
        await graph.ensure_ready()
        values = [
            f"pkg.m{module}.sym{symbol}"
            for module in range(_SEEDED_MODULES)
            for symbol in range(_SYMBOLS_PER_MODULE)
        ]
        values += ["pkg.café.widget", "pkg.cafés.other", f"pkg.m1.{chr(0x10FFFF)}"]
        for value in values:
            await run(admin, f"CREATE {NAME_TABLE} SET value = $v", {"v": value})
        yield admin
    finally:
        await admin.close()
        await graph.close()


def _expected(values_prefixes: list[str], seeded: list[str]) -> set[str]:
    return {value for value in seeded if any(value.startswith(prefix) for prefix in values_prefixes)}


class TestTheNativePrefixMatchIsIndexServed:
    """The ENGINE fact F9's retirement rests on, for every shape the reach emits: ``string::starts_with``
    on the indexed ``value`` column — alone or OR'd — reads ``name_value`` and never TableScans ``name``,
    and returns exactly the prefixed names. The control shows the walker sees a TableScan when the index
    cannot serve the predicate."""

    @pytest.mark.parametrize("shape", sorted(_PREFIX_SETS))
    async def test_starts_with_reads_the_index(self, name_table: Any, shape: str) -> None:
        prefixes = _PREFIX_SETS[shape]
        params = {f"p{index}": prefix for index, prefix in enumerate(prefixes)}
        clause = " OR ".join(f"string::starts_with(value, $p{index})" for index in range(len(prefixes)))
        statement = f"SELECT VALUE value FROM {NAME_TABLE} WHERE {clause}"
        plan = await explain(name_table, statement, params)
        assert index_served(plan, _NAME_VALUE_INDEX) and not scans_table(plan, NAME_TABLE), (
            f"[{shape}] string::starts_with is not index-served on this engine: {plan!r}"
        )
        seeded = await run(name_table, f"SELECT VALUE value FROM {NAME_TABLE}")
        assert set(await run(name_table, statement, params)) == _expected(prefixes, seeded)

    async def test_control_a_predicate_the_index_cannot_serve_is_seen_as_a_table_scan(
        self, name_table: Any
    ) -> None:
        plan = await explain(
            name_table,
            f"SELECT VALUE value FROM {NAME_TABLE} WHERE string::starts_with(string::lowercase(value), $p)",
            {"p": "pkg.m1."},
        )
        assert scans_table(plan, NAME_TABLE) and not index_served(plan, _NAME_VALUE_INDEX), (
            f"control: the walker cannot see a TableScan, so the pin above proves nothing: {plan!r}"
        )


class TestTheModulePrefixReachIsIndexServed:
    """The PRODUCTION statement (``SurrealCodeGraph._prefix_range_query`` — whatever form it takes after
    F9) for every prefix-set shape the reach emits: index-served, no TableScan, exactly the prefixed
    names. The pre-existing single-prefix plan pin (``test_graph_surreal``
    ``test_query_plan_hits_the_name_value_index_never_a_table_scan``) covers one prefix; the reach ORs
    one prefix per frontier module, and an OR is where 3.x index service has failed before (#413)."""

    @pytest.mark.parametrize("shape", sorted(_PREFIX_SETS))
    async def test_the_reach_statement_reads_the_index(self, name_table: Any, shape: str) -> None:
        prefixes = _PREFIX_SETS[shape]
        statement, params = SurrealCodeGraph._prefix_range_query(prefixes)
        plan = await explain(name_table, statement, params)
        assert index_served(plan, _NAME_VALUE_INDEX) and not scans_table(plan, NAME_TABLE), (
            f"[{shape}] the module-prefix reach TableScans `{NAME_TABLE}`: {plan!r}"
        )
        seeded = await run(name_table, f"SELECT VALUE value FROM {NAME_TABLE}")
        ids = await run(name_table, statement, params)
        found = await run(name_table, f"SELECT VALUE value FROM {NAME_TABLE} WHERE id IN $ids", {"ids": ids})
        assert set(found) == _expected(prefixes, seeded), f"[{shape}] wrong names: {sorted(found)[:6]}"


def _is_door(function: Any) -> bool:
    """Whether an SDK connection method reaches the store when awaited: a coroutine function, or a method
    whose annotated return type is awaitable, async-iterable, or carries a coroutine method (a builder or
    batch whose ``execute`` does the I/O)."""
    if inspect.iscoroutinefunction(function):
        return True
    try:
        returned = typing.get_type_hints(function).get("return")
    except Exception:  # noqa: BLE001 - an unresolvable annotation is reported by the caller, not hidden
        return True
    origin = typing.get_origin(returned) or returned
    if not isinstance(origin, type):
        return False
    if hasattr(origin, "__await__") or hasattr(origin, "__aiter__"):
        return True
    return any(
        inspect.iscoroutinefunction(member)
        for name, member in inspect.getmembers(origin, inspect.isfunction)
        if not name.startswith("_")
    )


def _doors(connection_class: type) -> set[str]:
    return {
        name
        for name, function in inspect.getmembers(connection_class, inspect.isfunction)
        if not name.startswith("_")
        and name not in _sdk_guard.SAFE_CONNECTION_METHODS
        and _is_door(inspect.unwrap(function))
    }


class TestTheSdkGuardReachesTheBuilderDoors:
    """F5: the guard's reach is the DERIVED door set, a checked variable — never the subset the SDK
    happens to spell ``async def``."""

    def test_every_derived_door_is_guarded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        report = _sdk_guard.install(
            monkeypatch, production_root=_THIS_FILE_ROOT, witness=_a_function_defined_in_this_file
        )
        assert report.armed, "premise: the shared retry driver exists, so the guard can arm"
        for connection_class in _sdk_guard.SDK_CONNECTION_CLASSES:
            doors = _doors(connection_class)
            assert "query" in doors, (
                f"the door derivation cannot see {connection_class.__name__}.query — its reach is not checked"
            )
            unguarded = sorted(
                name for name in doors if not getattr(getattr(connection_class, name), "_sdk_guarded", False)
            )
            assert not unguarded, (
                f"{connection_class.__name__}: the runtime SDK guard does not wrap {unguarded} — calls "
                f"through them escape the retry-driver check AND the multi-statement check, silently"
            )

    async def test_a_query_outside_the_driver_is_an_escape_and_is_observed(
        self, store_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        connection = await connect_admin(store_env)
        try:
            report = _sdk_guard.install(
                monkeypatch, production_root=_THIS_FILE_ROOT, witness=_a_function_defined_in_this_file
            )
            seen: list[str] = []

            def _record_method(event: _sdk_guard.CallEvent, coro: Any) -> Any:
                seen.append(event.method)
                return coro

            monkeypatch.setattr(_sdk_guard, "_CALL_HOOKS", [*_sdk_guard._CALL_HOOKS, _record_method])
            await connection.query("RETURN 1")
            assert any(escape.method == "query" for escape in report.escapes), (
                f"a bare connection.query() outside the retry driver was not recorded as an escape: "
                f"{report.escapes!r}"
            )
            assert "query" in seen, f"the guard's hook chain never observed a query() call (saw {seen!r})"
        finally:
            await connection.close()

    async def test_a_two_statement_query_inside_the_driver_is_a_violation(
        self, store_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        connection = await connect_admin(store_env)
        try:
            report = _sdk_guard.install(
                monkeypatch, production_root=_THIS_FILE_ROOT, witness=_a_function_defined_in_this_file
            )

            async def attempt() -> Any:
                return await connection.query("RETURN 1; RETURN 2")

            await retry_on_conflict(attempt, label="sdk3.guard.probe")
            assert report.multi_statement_violations, (
                "a two-statement query() was not flagged — the guard's #144 posture lost its reach"
            )
            assert not report.escapes, f"premise: the call rode the driver ({report.escapes!r})"
        finally:
            await connection.close()
