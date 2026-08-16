"""Contract for the trace-telemetry STORE + WRITE POLICY (packet 03b §B; RE-AUTHORED packet 59).

⚠ RE-AUTHORED BY PACKET 59 (fastmcp 3.x migration, ``docs/design/2026-08-15-fastmcp-3x-migration.md``
§4). This file used to carry BOTH halves of the trace contract. The migration re-homes the FUNNEL
half — how the emission is TRIGGERED (the retired ``TracingFastMCP.call_tool`` subclass → an
``on_call_tool`` middleware; the ``ok``-latch, the shielded/bounded ``finally``, the
trace-never-surfaces posture, declared identity, coverage-∀, the real-store W30/W33 legs, and the
params-hash-carries-free-text-only-as-a-digest hostile-body pin) — into
``test_fastmcp_migration.py``, where they are pinned against the NEW middleware seam (design §5a
B1–B8). Those funnel pins were REMOVED here rather than left green, because they asserted against a
seam the migration DELETES (``TracingFastMCP`` / ``mcp.server.lowlevel.server.request_ctx`` /
``FastMCP.call_tool`` dispatch) — a green suite that still asserts the corpse is the exact
"tests written before a semantic change certify the OLD world" hazard.

WHAT REMAINS HERE is the trace-store WRITE POLICY, which the migration leaves UNCHANGED (design M4 —
``_record_tool_trace`` and ``SurrealStore.record_trace`` are reused verbatim; only their CALLER
moves). These pins do not touch the funnel:

* T2 / T2.1 — the ``trace`` table schema DELTA (the widened + added ``option<>`` columns, the
  ``(agent, ordinal)`` index) and its migration onto a DIRTY store;
* T3 — the ONE global native sequence and the store-side ORDINAL mint;
* T8 — ``record_trace``'s keyword-only signature;
* DD-1.b — the WINDOWED hot aggregate read and the served per-tool aggregate cap;
* the monotonicity predicate control and the index-fields parser control;
* the no-prod-prose-teaches-the-retired-plan scan.

All run against the REAL TEST store (``ws://127.0.0.1:18000`` — ``:18500`` is PRODUCTION and is
never a test target), on a fresh throwaway database per test.

PROBE RECEIPTS (fresh 2026-07-24 at HEAD ``e7db965``, re-probed on contact per packet 03b's ruling;
each carries a positive control) that ground the store-side pins below:

* ``sequence::nextval`` under the default ``START 0`` returns **0** on its first call and **1** on
  its second (SurrealDB 3.2.1) — ordinals are 0-based, so a pin asserting ``ordinal == 1`` for the
  first row would be wrong against a correct build.
* ``SELECT *`` OMITS an unset ``option<>`` column entirely while an EXPLICIT PROJECTION returns it
  as ``None`` — hence :data:`_TRACE_PROJECTION`; every read leg here projects explicitly.
* ``CREATE t CONTENT object::extend($bound, {computed})`` is the working shape for minting a column
  store-side alongside a bound payload; ``CONTENT $c SET …`` and ``CONTENT $c MERGE {…}`` are both
  PARSE ERRORS (controls rejected, each naming its own token).

RED, NEVER UNCOLLECTABLE (still in force for the store-side unbuilt surface): the store symbols this
file pins that did not exist at 03b's authoring were reached through ``Any``-typed call sites so a
pin fails for ITS OWN reason (a runtime ``TypeError``/``AssertionError``), never at COLLECTION.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import inspect
import io
import json
import re
import tokenize
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
import pytest_asyncio
from _surreal_fakes import FakeSurrealStore
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealConnection,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.config import DEFAULT_TELEMETRY_WINDOW_DAYS, LoreConfig
from loremaster.server import AppContext, TraceSummary
from loremaster.store._txn import _ERROR_CLASS_FIELD_COERCION
from loremaster.store.surreal import SurrealStore, SurrealStoreError
from loremaster.store.surreal_schema import (
    TRACE_TABLE,
    TRACE_TS_FIELD,
    _define_field,
    _define_table,
    generate_ddl,
)
from test_surreal_schema import _field_statement

# --------------------------------------------------------------------------- #
# The telemetry vocabulary this contract pins (T2 / T2.1 / T3).
# --------------------------------------------------------------------------- #
# The two committed columns T2 WIDENS: the generic seam cannot know a hit count
# (0 hits is a lie, not an absence) and only a call that DECLARES a fleet session
# has one. Representable absence is the honesty requirement.
_TRACE_WIDENED_COLUMNS: dict[str, str] = {
    "hit_count": "option<int>",
    "session": "option<string>",
}
# The five columns T2 ADDS, each ``option<>`` (the store reference's mandated
# shape for a new field on a table that may already be populated).
_TRACE_ADDED_COLUMNS: dict[str, str] = {
    "agent": "option<string>",
    "action": "option<string>",
    "transport_session": "option<string>",
    "ordinal": "option<int>",
    "ok": "option<bool>",
}
# The committed columns T2 leaves ALONE — asserted unchanged so the delta cannot
# quietly reshape the served row while nobody is looking.
_TRACE_UNCHANGED_COLUMNS: dict[str, str] = {
    "tool": "string",
    "params_hash": "string",
    "latency_ms": "number",
    "token_cost": "option<int>",
    "model": "option<string>",
}
# T3: ONE global native sequence. No BATCH/START clause (a changed one never
# migrates onto an existing store — #146), and ``IF NOT EXISTS`` because a bare
# DEFINE SEQUENCE raises on the re-apply ``ensure_ready`` performs every boot.
# DD-1.b: the aggregate read is WINDOWED, and the window is a REQUIRED argument.
# Derived from the production default rather than written as 14, so a re-tune
# re-derives every consumer instead of silently unbinding these reads.
_TELEMETRY_WINDOW_DAYS = DEFAULT_TELEMETRY_WINDOW_DAYS
_TRACE_SEQUENCE_NAME = "trace_seq"
_TRACE_SEQUENCE_STATEMENT = f"DEFINE SEQUENCE IF NOT EXISTS {_TRACE_SEQUENCE_NAME}"
# T2.1: the 06-read index, shipped inside the free window (the trace table is
# empty until 03b deploys, then grows on EVERY tool call).
_TRACE_INDEX_NAME = "trace_agent_ordinal"
_TRACE_INDEX_FIELDS = ("agent", "ordinal")
# ESC-1 (RULED at `d0f84d0`): the `ok` column's semantics, which must be documented
# verbatim where the column is DEFINED. The distinctive clause of *"True iff the
# dispatch RETURNED a result; False on any raise, cancellation included."*
_OK_SEMANTICS_CLAUSE = "False on any raise, cancellation included"
# How far above the `_TRACE_FIELD_SPECS` assignment its explanatory comment block
# may sit and still count as "where the column is defined".
_COMMENT_WINDOW_LINES = 60

# Every trace column, in one place, so read legs can PROJECT EXPLICITLY. A
# ``SELECT *`` read of an unset ``option<>`` column raises ``KeyError`` (probed —
# see the module docstring), which surfaces as a harness failure rather than as a
# finding; an explicit projection reads ``None`` (AC-05).
_TRACE_PROJECTION: tuple[str, ...] = (
    "tool",
    "params_hash",
    "hit_count",
    "latency_ms",
    "session",
    "agent",
    "action",
    "transport_session",
    "ordinal",
    "ok",
    "ts",
)


async def _record_trace(store: Any, **overrides: Any) -> None:
    """One ``record_trace`` call at the T8 signature.

    ``store`` is typed ``Any`` on purpose: the four new keyword-only parameters do
    not exist yet, so a statically-typed call site would be a mypy error no
    builder can pay except by building. The RED here is the runtime ``TypeError``
    naming the unexpected keyword argument.

    Deliberately omits ``hit_count`` and ``session`` — T8 makes both OPTIONAL in
    the signature, so a build that leaves either REQUIRED fails here too.

    Args:
        store: The store under test (real or fake).
        **overrides: Field values replacing the defaults below.
    """
    fields: dict[str, Any] = {
        "tool": _SEAM_TOOL,
        "params_hash": _SEAM_PARAMS_HASH,
        "latency_ms": _SEAM_LATENCY_MS,
        "agent": _DECLARED_AGENT,
        "action": _DECLARED_ACTION,
        "transport_session": _TRANSPORT_SESSION_ID,
        "ok": True,
    }
    fields.update(overrides)
    await store.record_trace(**fields)


# --------------------------------------------------------------------------- #
# Fixture DATA. A LOCAL, minimal LoreConfig builder — deliberately NOT imported
# from test_mcp_server.py or test_comms_tool.py (neither is a designed shared
# module, unlike the underscore-prefixed ``_*.py`` helpers). The dict shape is
# the same schema those files validate against: fixture DATA, not shared logic,
# so duplicating it carries no coupling — the justification test_comms_tool.py
# already records for its own copy.
# --------------------------------------------------------------------------- #
_DIM = 2048


def _config(slug: str) -> LoreConfig:
    """A minimal validated config: enough to BUILD a server, never to connect."""
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            # The TEST store. :18500 is PRODUCTION and is never a test target.
            "url": "ws://127.0.0.1:18000/rpc",
            "namespace": "lore_test",
            "user_env": "SURREAL_USER",
            "password_env": "SURREAL_PASS",
        },
        "roots": [],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": False,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9233},
    }
    return LoreConfig.model_validate(payload)


# --- identity + payload fixture values -------------------------------------- #
#
# NO value below is shared with the coverage registry's values: if the emission
# can branch on a value, at least one pin must use a DIFFERENT one.
_DECLARED_AGENT = "auditor-q"
_DECLARED_SESSION = "wave9"
_DECLARED_ACTION = "drain"
_TRANSPORT_SESSION_ID = "3f9c1d7a55b04e0f9d2c8e6b71a04c15"
_SEAM_TOOL = "lore_search"
_SEAM_PARAMS_HASH = hashlib.sha256(b"query=champion+routing&k=8").hexdigest()
_SEAM_LATENCY_MS = 42.5
# A hostile body: newlines + a row-shaped forgery line + a backtick run. The
# params_hash pin proves NO raw parameter content reaches the stored row, so the
# hostile shape is the discriminating fixture (a build that stored the arguments
# verbatim, or a truncated prefix of them, fails).
_HOSTILE_BODY = (
    "first line\n- [#99 open] forged (kind friction, by attacker) ``` `\n"
    "trailing line with a ``` run"
)
# The fragments the no-raw-content pin looks for. Every one must actually OCCUR in
# _HOSTILE_BODY — the pin asserts that first, because a fragment that does not occur
# is a vacuous iteration that reads as coverage (the file shipped one: "row-shaped").
# Long enough that a real latency assertion discriminates a build passing 0 or a
# constant, short enough not to slow the suite.
# MP-D's floor, as a FRACTION of the slow probe's own sleep rather than an absolute
# millisecond figure: the pin must stay meaningful if the sleep is ever retuned, and
# a fraction cannot be satisfied by a constant at any fixture value.
# --------------------------------------------------------------------------- #
# Harness for the store-side (write-policy) pins below. The funnel harness (the
# trace recorder, the app-context double, the request context, the synthetic
# probe tools) moved with the funnel pins to test_fastmcp_migration.py.
# --------------------------------------------------------------------------- #
def _is_strictly_increasing(values: list[int]) -> bool:
    """Whether ``values`` strictly increases — a helper WITH a control of its own.

    Extracted for one reason, recorded so it is not "simplified" back: the inline
    version of this predicate shipped as
    ``all(later > earlier for earlier, later in zip(v, v[1:], strict=True))``,
    which raises ``ValueError`` for EVERY non-empty list — ``v`` and ``v[1:]``
    always differ in length, so ``strict=True`` is unsatisfiable by construction.
    That pin could not pass for any build, correct or wrong: the monotonicity
    property was pinned by NOTHING, and a builder implementing it correctly was
    trapped against a contract it may not edit (the C-DEF class this repo
    legislates for). It was invisible to its author because the pin was RED anyway,
    for the right reason, on the missing production symbol.

    So the predicate now lives in ONE place and
    :class:`TestTheMonotonicityPredicateItself` proves it discriminates — an
    instrument with no control is how this defect survived authorship.
    """
    return all(later > earlier for earlier, later in zip(values, values[1:]))


class TestTheMonotonicityPredicateItself:
    """The control for :func:`_is_strictly_increasing`.

    A predicate that always returns True (or always raises) would make the ordinal
    battery decoration. Both directions are checked, plus the shape that broke the
    original: a non-empty list must be EVALUABLE at all.
    """

    @pytest.mark.parametrize(
        ("values", "expected"),
        [
            ([0, 1, 2], True),
            ([0], True),
            ([0, 0, 1], False),
            ([1, 0], False),
            ([0, 2, 1], False),
        ],
    )
    def test_the_predicate_discriminates(self, values: list[int], expected: bool) -> None:
        assert _is_strictly_increasing(values) is expected

    def test_the_predicate_is_evaluable_on_a_non_empty_list(self) -> None:
        # The regression guard: the original inline form raised ValueError here
        # rather than returning a verdict, so it could never pass.
        assert _is_strictly_increasing([0, 1, 2]) is True


def _returning(rows: list[dict[str, Any]]) -> Any:
    """An async ``trace_aggregates`` stand-in that DEMANDS the window kwarg.

    It accepts ``window_days`` as KEYWORD-ONLY and asserts it was supplied,
    mirroring the real signature: a caller that dropped the window would
    otherwise read an unbounded scan against this double and pass.
    """

    async def _call(*, window_days: int) -> list[dict[str, Any]]:
        assert window_days > 0, "the aggregate read must carry a positive window"
        return rows

    return _call


def _aggregate_context(rows: list[dict[str, Any]], *, window_days: int) -> Any:
    """An ``AppContext``-shaped double for the windowed per-tool aggregate."""
    return cast(
        Any,
        SimpleNamespace(
            write_store=SimpleNamespace(trace_aggregates=_returning(rows)),
            _config=SimpleNamespace(
                telemetry=SimpleNamespace(aggregate_window_days=window_days)
            ),
        ),
    )


def _expected_params_hash(arguments: dict[str, Any]) -> str:
    """The T6 recipe, computed independently of the production code.

    T6 rules the recipe exactly: ``sha256`` over
    ``json.dumps(arguments, sort_keys=True, default=str)``, full hex. Re-deriving
    it here makes the pin an ORACLE rather than a tautology over whatever the
    implementation happens to compute.
    """
    payload = json.dumps(arguments, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture()
async def trace_store() -> AsyncIterator[SurrealStore]:
    """A ready real :class:`SurrealStore` on a fresh throwaway database.

    Follows the ``test_surreal_store.py::trace_store`` "real" branch idiom: it
    calls the harness helpers (``make_env`` / ``connect_admin`` /
    ``drop_database``) directly rather than depending on the ``surreal_env``
    fixture, because resolving one async fixture from inside another async
    fixture's own body re-enters pytest-asyncio's shared function-scoped runner.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    store = SurrealStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        dim=env.dim,
        user=env.user,
        password=env.password,
    )
    await store.ensure_ready()
    try:
        yield store
    finally:
        await store.close()
        await drop_database(env)


@pytest_asyncio.fixture()
async def trace_store_factory() -> AsyncIterator[Any]:
    """A factory minting INDEPENDENT ready stores on ONE shared database.

    The concurrency pin needs separate CONNECTIONS: N coroutines on ONE socket do
    not contend the way N connections do (the packet-03 mint pin's own measured
    rationale, ``test_message_ledger.py::TestConcurrentSendsMintDistinctSeqs``).
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    created: list[SurrealStore] = []

    async def make() -> SurrealStore:
        store = SurrealStore(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            dim=env.dim,
            user=env.user,
            password=env.password,
        )
        await store.ensure_ready()
        created.append(store)
        return store

    try:
        yield make
    finally:
        for store in created:
            await store.close()
        await drop_database(env)


@pytest_asyncio.fixture()
async def dirty_trace_db() -> AsyncIterator[tuple[SurrealConnection, SurrealEnv]]:
    """A raw admin connection on a fresh database, for the migration pin.

    The migration pin owns its own schema: it applies the OLD trace definition,
    dirties the store, and only THEN lets the production ``ensure_ready`` apply
    today's — so it needs a bare connection, never a store that has already
    applied the current schema.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    connection = await connect_admin(env)
    try:
        yield connection, env
    finally:
        await connection.close()
        await drop_database(env)


# --------------------------------------------------------------------------- #
# T1 / T7.2 — the seam is INSTALLED (the no-op-fix door)
# --------------------------------------------------------------------------- #
class TestTheEmissionsDependencyIsRealInProduction:
    """AC-15's discipline applied to THIS wave: the double cannot invent wiring.

    The seam batteries deliver the app context as a double carrying
    ``write_store``. If production's real ``AppContext`` did not carry that
    attribute, every one of those pins would pass while the deployed emission had
    no store to write through — a harness double declaring a dependency into
    existence (the test-environment-is-a-fiction law). This introspects the REAL
    class, with a positive control proving the introspection can see wiring at all
    and a negative control proving it can also NOT see something.
    """

    def test_the_real_app_context_accepts_the_store_the_emission_writes_through(self) -> None:
        parameters = inspect.signature(AppContext.__init__).parameters
        assert "write_store" in parameters, (
            "AppContext no longer accepts `write_store`; the emission reaches its store off the "
            "request's lifespan context, so a rename here silently un-wires telemetry."
        )
        # POSITIVE CONTROL: the introspection demonstrably sees other real wiring.
        assert "embedder" in parameters
        # NEGATIVE CONTROL: it is not simply answering True.
        assert "trace_store_that_does_not_exist" not in parameters
        assert hasattr(SurrealStore, "record_trace"), (
            "the store the emission writes through must expose `record_trace`."
        )


# --------------------------------------------------------------------------- #
# T7.1 — coverage as a CHECKED VARIABLE
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# MP-A — the seam drives the REAL store (the W30 hole)
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# T5 — emission shape and failure posture
# --------------------------------------------------------------------------- #
class TestTheHotAggregateReadIsWINDOWEDAtTheQueryNotJustTheRender:
    """DD-1.b. The per-tool aggregate runs on EVERY status call over a table that
    grows by one row per served tool call, forever. Unwindowed it is a full scan
    whose cost rises with the table's whole lifetime.

    THE WRONG BUILD THE DESIGN NAMES FIRST, and it is the one no assertion about
    NUMBERS can see: window the RENDER but not the QUERY. At small N every served
    figure is identical, so only the QUERY TEXT and the EXPLAIN plan discriminate.

    EXPLAIN RECEIPT (spike-surreal `ws://127.0.0.1:18000`, 3.2.1, throwaway DB —
    `:18500` never touched), with the pre-change shape as its CONTROL:

        WINDOWED    -> Aggregate / IndexScan{index: trace_ts, access: ">d'…'"}
        UNWINDOWED  -> Aggregate / TableScan{table: trace}

    The control is what makes it a receipt rather than a claim: the SAME probe
    shows the scan the window removes.
    """

    @staticmethod
    def _statements(store: Any) -> list[str]:
        """Every statement the store issues, captured at its own query seam."""
        seen: list[str] = []
        original = store._query

        async def _spy(statement: str, params: dict[str, Any] | None = None) -> Any:
            seen.append(statement)
            return await original(statement, params)

        store._query = _spy
        return seen

    async def test_the_aggregate_query_carries_the_ts_window_conjunct(
        self, trace_store: SurrealStore
    ) -> None:
        seen = self._statements(trace_store)
        await trace_store.trace_aggregates(window_days=_TELEMETRY_WINDOW_DAYS)
        assert seen, "the spy observed no statement — it is detached from the query seam"
        aggregate = [text for text in seen if "GROUP BY" in text]
        assert len(aggregate) == 1, f"expected ONE aggregate statement, got {aggregate!r}"
        assert "WHERE ts >" in aggregate[0], (
            f"the aggregate query carries no `WHERE ts >` conjunct, so the SCAN is unbounded "
            f"however the numbers are rendered — the wrong build DD-1.b names first, and it is "
            f"invisible to every assertion about the served values: {aggregate[0]!r}"
        )
        assert "$cutoff" in aggregate[0], (
            "the cutoff is not a BOUND PARAM — an interpolated datetime is both an injection "
            "surface and a value no plan can reuse"
        )

    async def test_an_OUT_OF_WINDOW_row_is_excluded_from_the_served_numbers(
        self, trace_store: SurrealStore
    ) -> None:
        """The second wrong build: window the QUERY but keep counting everything,
        or window nothing and claim you did. One in-window row and one row well
        outside it — a build with no window reports 2."""
        await _record_trace(trace_store)
        stale = datetime.now(UTC) - timedelta(days=_TELEMETRY_WINDOW_DAYS + 30)
        await trace_store._query(
            f"CREATE {TRACE_TABLE} CONTENT $content",
            {
                "content": {
                    "tool": _SEAM_TOOL,
                    "params_hash": _SEAM_PARAMS_HASH,
                    "latency_ms": _SEAM_LATENCY_MS,
                    "ts": stale,
                }
            },
        )
        rows = await _trace_rows(trace_store)
        assert len(rows) == 2, f"fixture check: both rows must EXIST, got {len(rows)}"
        aggregates = await trace_store.trace_aggregates(window_days=_TELEMETRY_WINDOW_DAYS)
        for_tool = [row for row in aggregates if row.get("tool") == _SEAM_TOOL]
        assert len(for_tool) == 1, f"expected one group for {_SEAM_TOOL}: {aggregates!r}"
        assert for_tool[0]["calls"] == 1, (
            f"the aggregate counted {for_tool[0]['calls']} calls where only ONE is inside the "
            f"{_TELEMETRY_WINDOW_DAYS}-day window — the row exists (asserted above), so this is "
            f"the window not being applied, not a missing row"
        )

    async def test_the_cutoff_is_computed_PER_CALL_never_cached(
        self, trace_store: SurrealStore
    ) -> None:
        """The third wrong build: compute the cutoff once and cache it. A stale
        cutoff silently widens back toward the unbounded scan, and every number
        stays plausible. Two reads, and their cutoffs must DIFFER."""
        cutoffs: list[Any] = []
        original = trace_store._query

        async def _spy(statement: str, params: dict[str, Any] | None = None) -> Any:
            if params and "cutoff" in params:
                cutoffs.append(params["cutoff"])
            return await original(statement, params)

        trace_store._query = _spy  # type: ignore[method-assign]
        await trace_store.trace_aggregates(window_days=_TELEMETRY_WINDOW_DAYS)
        await asyncio.sleep(0.01)
        await trace_store.trace_aggregates(window_days=_TELEMETRY_WINDOW_DAYS)
        assert len(cutoffs) == 2, (
            f"the spy captured {len(cutoffs)} cutoffs — it is not observing the bound param"
        )
        assert cutoffs[0] != cutoffs[1], (
            "both reads used the SAME cutoff, so it is computed once and cached. A cached "
            "cutoff ages: the window silently widens back toward a full scan while every "
            "served number stays plausible"
        )

    async def test_the_window_the_numbers_are_computed_over_is_SERVED(self) -> None:
        """Derived prose, made mechanical: the served summary carries the window
        itself, so a consumer never has to guess whether a count is windowed or
        lifetime — and the description cannot drift from the value."""
        from loremaster.server import AppContext

        rows = [{"tool": _SEAM_TOOL, "calls": 3, "latest": None}]
        summary = await AppContext._trace_summary(
            _aggregate_context(rows, window_days=_TELEMETRY_WINDOW_DAYS)
        )
        assert summary.window_days == _TELEMETRY_WINDOW_DAYS
        served = " ".join((TraceSummary.__doc__ or "").split())
        assert "WINDOWED" in served, (
            "the served model's own docstring does not say its numbers are windowed — a "
            "consumer reading them as lifetime totals draws the wrong conclusion from a quiet "
            "week, which is the served-prose class this repo keeps paying for"
        )


class TestTheServedPerToolAggregateIsCappedAndCounted:
    """FIX WAVE — blind-audit D6 (the served half; retention is ledgered).

    ``TraceSummary.by_tool`` is returned as STRUCTURED OUTPUT with no display
    cap, and its group key is the DISPATCHED tool name — which is
    caller-supplied. An unknown name still reaches the seam (the dispatch fails
    INSIDE the funnel, so the row is written before the failure surfaces), so a
    client repeatedly calling one typo permanently grows every future
    ``lore_index`` response. It was the one list in this packet's blast radius
    with no cap.

    Capped AND counted: a silent truncation would read as "that is all the
    tools", and ``total`` deliberately stays the TRUE total, so the disclosure
    is what keeps the two numbers consistent rather than contradictory.
    """

    async def test_an_over_cap_aggregate_is_capped_and_the_remainder_COUNTED(self) -> None:
        from loremaster.server import _TRACE_BY_TOOL_CAP, AppContext

        over = _TRACE_BY_TOOL_CAP + 7
        rows = [
            {"tool": f"probe_tool_{index:03d}", "calls": index + 1, "latest": None}
            for index in range(over)
        ]
        context = _aggregate_context(rows, window_days=_TELEMETRY_WINDOW_DAYS)
        summary = await AppContext._trace_summary(context)
        assert summary.window_days == _TELEMETRY_WINDOW_DAYS, (
            "the served summary does not carry the window its numbers were computed over — a "
            "consumer would read windowed counts as lifetime totals"
        )
        assert len(summary.by_tool) == _TRACE_BY_TOOL_CAP, (
            f"the served per-tool list carried {len(summary.by_tool)} of {over} entries — an "
            f"uncapped list whose keys a CALLER controls grows every future status response"
        )
        assert summary.tools_elided == over - _TRACE_BY_TOOL_CAP, (
            "the cap did not DISCLOSE its remainder; a silent truncation reads as 'that is all "
            "the tools'"
        )
        assert summary.total == sum(int(cast(int, row["calls"])) for row in rows), (
            "the total shrank to match the display window — it must stay the TRUE total across "
            "every tool, which is what tools_elided exists to reconcile"
        )
        assert summary.by_tool == sorted(summary.by_tool, key=lambda item: item.tool), (
            "the served slice is not name-sorted, so the render is not deterministic"
        )
        busiest = {f"probe_tool_{index:03d}" for index in range(over - _TRACE_BY_TOOL_CAP, over)}
        assert {item.tool for item in summary.by_tool} == busiest, (
            "the cap kept the ALPHABET rather than the SIGNAL — selection is by call count, or "
            "a busy tool vanishes behind an idle one whose name sorts earlier"
        )

    async def test_positive_control_an_UNDER_cap_aggregate_elides_nothing(self) -> None:
        from loremaster.server import _TRACE_BY_TOOL_CAP, AppContext

        under = _TRACE_BY_TOOL_CAP - 2
        rows = [
            {"tool": f"probe_tool_{index:03d}", "calls": index + 1, "latest": None}
            for index in range(under)
        ]
        context = _aggregate_context(rows, window_days=_TELEMETRY_WINDOW_DAYS)
        summary = await AppContext._trace_summary(context)
        assert len(summary.by_tool) == under
        assert summary.tools_elided == 0, (
            "an under-cap aggregate disclosed a remainder it does not have"
        )


# --------------------------------------------------------------------------- #
# T4 — declared-only identity + the transport correlator
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# T6 — params_hash
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# T2 / T2.1 — the schema delta (offline, statement-level)
# --------------------------------------------------------------------------- #
def _index_fields(ddl: str, name: str) -> tuple[str, ...]:
    """The FIELDS list of the ``DEFINE INDEX`` statement named exactly ``name``.

    Parses the FIELDS CLAUSE rather than substring-matching the statement: an
    index NAMED ``trace_agent_ordinal`` contains both column names as substrings,
    so a substring assertion would pass over ANY fields list (the AC-12 rider).

    Args:
        ddl: The generated DDL.
        name: The exact index name.

    Returns:
        The fields, in declared order.

    Raises:
        AssertionError: No ``DEFINE INDEX`` statement carries that exact name, or
            it carries no parseable FIELDS clause.
    """
    pattern = re.compile(
        rf"^DEFINE INDEX (?:IF NOT EXISTS |OVERWRITE )?{re.escape(name)}"
        rf"\s+ON\s+\S+\s+FIELDS\s+(?P<fields>[^\n;]+)"
    )
    for statement in (line.strip() for line in ddl.split(";\n")):
        match = pattern.match(statement)
        if match:
            return tuple(field.strip() for field in match.group("fields").split(","))
    raise AssertionError(f"no DEFINE INDEX statement named exactly {name!r} in the generated DDL")


def _index_statement(ddl: str, name: str) -> str:
    """The whole ``DEFINE INDEX`` statement named exactly ``name``."""
    for statement in (line.strip() for line in ddl.split(";\n")):
        if re.match(rf"^DEFINE INDEX (?:IF NOT EXISTS |OVERWRITE )?{re.escape(name)}\s+ON\s", statement):
            return statement
    raise AssertionError(f"no DEFINE INDEX statement named exactly {name!r} in the generated DDL")


class TestTheIndexFieldsParserItself:
    """The parser above is an INSTRUMENT, so it gets a control of its own.

    A probe that cannot fail is worth nothing: this proves the parser reads the
    FIELDS clause and NOT the index name — the exact trap AC-12's rider names.
    """

    def test_it_reads_the_fields_clause_of_a_real_committed_index(self) -> None:
        # POSITIVE CONTROL over a MULTI-FIELD index that exists TODAY, so the
        # parser is known to work — including its comma split — before the trace
        # index it is aimed at exists.
        ddl = generate_ddl(dim=_DIM)
        assert _index_fields(ddl, "chunk_tier_file") == ("tier", "file_path")

    def test_it_is_not_fooled_by_an_index_whose_NAME_contains_the_column_names(self) -> None:
        forged = (
            f"DEFINE INDEX IF NOT EXISTS {_TRACE_INDEX_NAME} ON {TRACE_TABLE} FIELDS tool;\n"
            "DEFINE TABLE IF NOT EXISTS decoy SCHEMAFULL;\n"
        )
        assert _index_fields(forged, _TRACE_INDEX_NAME) == ("tool",), (
            "the parser returned the index NAME's substrings instead of its FIELDS clause — the "
            "substring trap AC-12's rider exists to prevent."
        )


class TestTheTraceSchemaDelta:
    """T2: the widened + new columns, all ``option<>``, all ``OVERWRITE``.

    ``DEFINE FIELD IF NOT EXISTS`` is a NO-OP on a field that already exists, so
    a TYPE change under it never migrates a deployed store and the schema
    silently stops converging on the code (#107, a 100% production outage). The
    all-``option<>`` shape is also what makes this delta cheap: there is no
    REQUIRED new column whose removal would green a committed pin, so no wrong
    schema is the cheapest path to green.
    """

    @pytest.mark.parametrize(
        ("column", "type_expr"), sorted({**_TRACE_WIDENED_COLUMNS, **_TRACE_ADDED_COLUMNS}.items())
    )
    def test_each_enrichment_column_is_defined_option_typed_with_OVERWRITE(
        self, column: str, type_expr: str
    ) -> None:
        # `_field_statement` itself asserts the OVERWRITE guard kind and fails
        # with a #107-shaped message if the definition regressed to IF NOT EXISTS.
        statement = _field_statement(generate_ddl(dim=_DIM), TRACE_TABLE, column)
        assert f"TYPE {type_expr}" in statement, (
            f"trace.{column} must be `TYPE {type_expr}`: the generic seam cannot know a value for "
            f"every tool, so absence must be REPRESENTABLE rather than faked with a zero or an "
            f"empty string. Served: {statement!r}"
        )

    @pytest.mark.parametrize(("column", "type_expr"), sorted(_TRACE_UNCHANGED_COLUMNS.items()))
    def test_the_committed_columns_keep_their_definitions(self, column: str, type_expr: str) -> None:
        # The delta is ADDITIVE: a reshape that "tidies" latency_ms to int (or
        # narrows an accounting column) is a silent data change nothing else here
        # would catch.
        statement = _field_statement(generate_ddl(dim=_DIM), TRACE_TABLE, column)
        assert f"TYPE {type_expr}" in statement, f"trace.{column} changed: {statement!r}"

    def test_the_ok_columns_ruled_semantics_are_documented_where_it_is_DEFINED(self) -> None:
        """ESC-1's ruling requires the semantics VERBATIM where the column is defined.

        Not bureaucracy: ``ok`` is a boolean whose meaning is not guessable from
        its name (does a cancelled call count? an errored one?), and packet 06
        filters on it. This repo's own audited failure mode is prose that describes
        behaviour drifting from the behaviour with no gate in between — so the ruled
        sentence gets an instrument rather than a memo.

        Keyed on the distinctive CLAUSE rather than the whole sentence with its
        markup, so a reflow does not go RED for a cosmetic reason — while a build
        that documents ``ok`` as "whether the tool call succeeded" (the wording the
        latch mechanism exists to correct) does.

        Two fixes over its first version, both from the adversary (R1/R9):
        1. The window now spans the comment block AND the tuple body, and comment
           markers are stripped before normalising — the first version failed a
           reference build whose sentence was VERBATIM but wrapped across two ``#``
           lines and placed inline beside the ``ok`` entry. A pin that reddens a
           correct build is a builder trap even when it cannot green a wrong one.
        2. The ORACLE is checked too. It defines the same column for every
           fake-backed consumer, and it was teaching the retired reading — a
           corpse that this pin, scanning only the schema module, could not see.
        """
        from loremaster.store import surreal_schema

        source_lines = inspect.getsource(surreal_schema).splitlines()
        specs_line = next(
            (index for index, line in enumerate(source_lines) if line.startswith("_TRACE_FIELD_SPECS")),
            None,
        )
        assert specs_line is not None, "could not locate the _TRACE_FIELD_SPECS assignment"
        end_line = next(
            (
                index
                for index, line in enumerate(source_lines[specs_line:], start=specs_line)
                if line.startswith(")")
            ),
            specs_line,
        )
        window = "\n".join(source_lines[max(0, specs_line - _COMMENT_WINDOW_LINES) : end_line + 1])
        # Strip comment markers before normalising: the ruled sentence wrapped over
        # two `#` lines is the SAME sentence, and a pin that cannot see that is
        # brittle rather than strict.
        normalised = " ".join(window.replace("#", " ").split())
        for surface, text in (
            ("surreal_schema's trace field specs", normalised),
            (
                "the ORACLE FakeSurrealStore.record_trace docstring",
                " ".join((inspect.getdoc(FakeSurrealStore.record_trace) or "").split()),
            ),
        ):
            assert _OK_SEMANTICS_CLAUSE in text, (
                f"{surface} does not document the ruled `ok` semantics. ESC-1 (d0f84d0) requires, "
                f"verbatim: 'True iff the dispatch RETURNED a result; {_OK_SEMANTICS_CLAUSE}.' The "
                f"mechanism is a SUCCESS LATCH — ok starts False and is latched True only on "
                f"return — and prose saying merely 'whether the tool call succeeded' leaves the "
                f"next reader to guess about cancellation, which is exactly the population packet "
                f"06 needs. Every surface that DEFINES this column must teach the same reading."
            )

    def test_the_trace_sequence_is_defined_once_with_no_batch_or_start_clause(self) -> None:
        statements = [line.strip() for line in generate_ddl(dim=_DIM).split(";\n")]
        matching = [
            statement
            for statement in statements
            if statement.startswith("DEFINE SEQUENCE") and _TRACE_SEQUENCE_NAME in statement
        ]
        assert len(matching) == 1, (
            f"expected exactly one DEFINE SEQUENCE for {_TRACE_SEQUENCE_NAME}, got {matching!r}"
        )
        assert matching[0] == _TRACE_SEQUENCE_STATEMENT, (
            f"the sequence must be exactly {_TRACE_SEQUENCE_STATEMENT!r}. `IF NOT EXISTS` because a "
            f"bare DEFINE SEQUENCE RAISES on the re-apply ensure_ready performs every boot (a "
            f"boot-time crash); and NO BATCH/START clause, because a changed one never migrates "
            f"onto an existing store (#146). Served: {matching[0]!r}"
        )

    def test_the_06_read_index_ships_in_the_free_window(self) -> None:
        # T2.1: a new index on a POPULATED table builds, blocking, at the first
        # ensure_ready carrying it. The trace table is empty until 03b deploys and
        # then grows on EVERY tool call, so this line is free exactly once —
        # shipped now, or paid for by packet 06 at every store's next boot.
        ddl = generate_ddl(dim=_DIM)
        assert _index_fields(ddl, _TRACE_INDEX_NAME) == _TRACE_INDEX_FIELDS, (
            f"the 06-read index must be FIELDS {', '.join(_TRACE_INDEX_FIELDS)} — packet 06's "
            f"per-agent curve filters agent and orders by ordinal."
        )
        statement = _index_statement(ddl, _TRACE_INDEX_NAME)
        assert statement.startswith(f"DEFINE INDEX IF NOT EXISTS {_TRACE_INDEX_NAME} "), (
            f"the index must be `IF NOT EXISTS` (an INDEX OVERWRITE re-validates/rebuilds a "
            f"populated index and can raise at boot). Served: {statement!r}"
        )
        assert f" ON {TRACE_TABLE} " in statement
        assert "UNIQUE" not in statement, (
            "the (agent, ordinal) index must be PLAIN: two rows may legitimately share an agent, "
            "and a UNIQUE index would reject the second."
        )

    def test_the_ts_index_ships_in_the_SAME_free_window(self) -> None:
        """DD-1.a — the one DEPLOY-GATED line in the design wave.

        The trace table is empty exactly once: production holds zero rows today
        (independently read on the live store before this deploy), and after it
        the table grows on EVERY served tool call. An index added later BUILDS,
        blocking, at every store's next boot. Unlike the deliberately-withheld
        ``transport_session`` index, BOTH consumers are named and designed — the
        windowed aggregate read that ships with it, and the retention sweep a
        later packet lands once it has read the curve these rows exist to
        produce — so the free-window argument is whole rather than speculative.

        It carries no behavioural pin BY DESIGN (an index changes plan, not
        result), which is exactly why it needs a structural one: without this,
        deleting the line is invisible until someone measures a boot.

        Rider, obeyed: parse the FIELDS clause, never substring the statement —
        an index NAMED ``trace_ts`` contains ``ts`` as a substring, so a
        substring assertion would pass over ANY fields list.
        """
        ddl = generate_ddl(dim=_DIM)
        assert _index_fields(ddl, f"{TRACE_TABLE}_ts") == (TRACE_TS_FIELD,), (
            f"the ts index must be FIELDS {TRACE_TS_FIELD} exactly — it is what makes the "
            f"windowed aggregate a range IndexScan instead of a full TableScan"
        )
        statement = _index_statement(ddl, f"{TRACE_TABLE}_ts")
        assert statement.startswith(f"DEFINE INDEX IF NOT EXISTS {TRACE_TABLE}_ts "), (
            f"the index must be `IF NOT EXISTS` — an INDEX OVERWRITE re-validates and rebuilds "
            f"a populated index and can raise at boot. Served: {statement!r}"
        )
        assert "UNIQUE" not in statement, (
            "the ts index must be PLAIN: many trace rows legitimately share a timestamp, and a "
            "UNIQUE index would reject the second one"
        )

    def test_no_transport_session_index_is_shipped(self) -> None:
        # A deliberate NON-shipment with a named decision point: packet 06's join
        # design may not need it, and the free-window argument is weaker for an
        # index whose consumer is undesigned. If 06 wants it, 06 rules it and
        # pays the build cost KNOWINGLY. This pin makes an accidental addition
        # visible rather than silently inherited.
        ddl = generate_ddl(dim=_DIM)
        trace_indexes = [
            statement.strip()
            for statement in ddl.split(";\n")
            if statement.strip().startswith("DEFINE INDEX") and f" ON {TRACE_TABLE} " in statement
        ]
        assert trace_indexes, "no trace index at all — the 06-read index is missing entirely"
        assert not [
            statement for statement in trace_indexes if "transport_session" in statement
        ], (
            "a transport_session index appeared. If packet 06's join needs it, that is 06's "
            "ruling to make with the build cost in view — delete this pin in the same commit and "
            "say so (it is a KNOWN, DELIBERATE non-shipment, not an oversight)."
        )


# --------------------------------------------------------------------------- #
# T2 — the dirty-store migration (the ONE instrument a virgin DB cannot be)
# --------------------------------------------------------------------------- #
# The OLD trace field specs, FROZEN as a literal. Deriving them from production
# would make this pin vacuous the moment the delta lands (old == new); a virgin
# fixture cannot see this packet's one schema-touching change at all.
_OLD_TRACE_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("tool", "string", ""),
    ("params_hash", "string", ""),
    ("hit_count", "int", ""),
    ("latency_ms", "number", ""),
    ("session", "string", ""),
    ("ts", "datetime", "DEFAULT time::now()"),
    ("token_cost", "option<int>", ""),
    ("model", "option<string>", ""),
)
_LEGACY_TRACE_HIT_COUNT = 8
_LEGACY_TRACE_SESSION = "orchestrator-session-7f3a"
# A sequence the migration pin defines ITSELF, purely as the positive control for
# its `INFO FOR DB` sequence introspection.
_CONTROL_SEQUENCE_NAME = "telemetry_control_seq"


async def _declared(connection: SurrealConnection, statement: str, section: str) -> set[str]:
    """The NAMES in one section of an ``INFO FOR …`` introspection.

    Names only, never definition text: the engine RENDERS ``option<int>`` back as
    ``none | int`` (probed 2026-07-24, 3.2.1), so an assertion against the DDL's
    own spelling would fail against a correct build. The type expressions are
    pinned where they are AUTHORED — against the generator's output — and presence
    is pinned here, against the live store.
    """
    info = await run(connection, statement)
    payload = info[section] if isinstance(info, dict) else {}
    return set(payload) if isinstance(payload, dict) else set()


async def _trace_rows(store: Any) -> list[dict[str, Any]]:
    """Every trace row, read through an EXPLICIT projection (AC-05).

    ``SELECT *`` OMITS an unset ``option<>`` column entirely, so ``row["ordinal"]``
    after a star read raises ``KeyError`` — a harness failure that would read as a
    finding. An explicit projection returns the column as ``None`` (both probed,
    2026-07-24, 3.2.1). Read through the store's own ``_query`` seam, the same
    TEST introspection ``test_surreal_store.py::_recorded_traces`` uses: the store
    has no public trace-read API and the aggregates deliberately group by tool.
    """
    raw = await store._query(f"SELECT {', '.join(_TRACE_PROJECTION)} FROM {TRACE_TABLE}")
    if not isinstance(raw, list):
        return []
    return [row for row in raw if isinstance(row, dict)]


class TestTheTraceDeltaMigratesADirtyStore:
    """#107's law, applied to this packet's one schema change.

    Every test in this repo mints a VIRGIN throwaway database, and a fixture that
    guarantees a clean slate cannot test what only happens on a dirty one — while
    every long-lived deployment IS dirty. #107 shipped 1040 tests green, a cold
    audit GO and a passing adversary, and broke a production verb 100%, because
    ``DEFINE FIELD IF NOT EXISTS`` never migrated a widened definition. This pin
    is the instrument for the trace slice: OLD definition applied, a row written
    under it, then the REAL production ``ensure_ready`` — after which a new-shape
    write must land and the legacy row must survive and still read.
    """

    @staticmethod
    async def _apply_old_trace_ddl(connection: SurrealConnection) -> None:
        """Apply the OLD trace definition, one statement per call.

        One statement per ``query()`` on purpose: the SDK inspects only the FIRST
        statement's status of a multi-statement query, so a later rejection would
        roll the schema back server-side while ``query()`` raised nothing at all.
        """
        await run(connection, _define_table(TRACE_TABLE))
        for name, type_expr, constraint in _OLD_TRACE_FIELD_SPECS:
            await run(connection, _define_field(TRACE_TABLE, name, type_expr, constraint=constraint))
        # The sequence-introspection control (see its use below): a sequence this
        # test defined itself, so "trace_seq is absent" is a real absence.
        await run(connection, f"DEFINE SEQUENCE IF NOT EXISTS {_CONTROL_SEQUENCE_NAME}")

    @staticmethod
    async def _dirty_the_store(connection: SurrealConnection) -> None:
        """Write ONE legacy-shaped trace row: the condition the defect needs."""
        await run(
            connection,
            f"CREATE type::record('{TRACE_TABLE}', $id) CONTENT $content",
            {
                "id": "legacy",
                "content": {
                    "tool": _SEAM_TOOL,
                    "params_hash": _SEAM_PARAMS_HASH,
                    "hit_count": _LEGACY_TRACE_HIT_COUNT,
                    "latency_ms": _SEAM_LATENCY_MS,
                    "session": _LEGACY_TRACE_SESSION,
                },
            },
        )

    @staticmethod
    async def _store_on(env: SurrealEnv) -> SurrealStore:
        """A store on an EXISTING database — ``ensure_ready`` is the migration."""
        return SurrealStore(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            dim=env.dim,
            user=env.user,
            password=env.password,
        )

    async def test_the_delta_lands_on_a_store_that_already_carries_the_old_definition(
        self, dirty_trace_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        connection, env = dirty_trace_db
        await self._apply_old_trace_ddl(connection)
        await self._dirty_the_store(connection)

        store = await self._store_on(env)
        await store.ensure_ready()
        try:
            # The NEW shape must be writable: every enrichment column present,
            # hit_count and session omitted (both now optional).
            await _record_trace(store)
            rows = await _trace_rows(store)
            written = [row for row in rows if row.get("agent") == _DECLARED_AGENT]
            assert len(written) == 1, (
                "a new-shape trace write did not land on a store that already carried the OLD "
                "trace definition. That is #107 exactly: the widened/added definitions never "
                "reached the deployed store, so only a FRESH database would ever accept this row."
            )
            assert written[0]["action"] == _DECLARED_ACTION
            assert written[0]["transport_session"] == _TRANSPORT_SESSION_ID
            assert written[0]["ok"] is True
            assert isinstance(written[0]["ordinal"], int)
        finally:
            await store.close()

    async def test_the_legacy_row_survives_the_migration_and_still_reads(
        self, dirty_trace_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        # A migration that "converges" the schema by destroying the rows living
        # under it has migrated nothing.
        connection, env = dirty_trace_db
        await self._apply_old_trace_ddl(connection)
        await self._dirty_the_store(connection)

        store = await self._store_on(env)
        await store.ensure_ready()
        try:
            # FIRST: prove the widened definition actually LANDED on the dirty
            # store. Without this, the NONE assertions below are VACUOUS — an
            # explicit projection of a column that does not exist reads None too,
            # so a schema that never migrated would satisfy them.
            declared = await _declared(connection, f"INFO FOR TABLE {TRACE_TABLE}", "fields")
            # POSITIVE CONTROL: the introspection sees the committed columns, so
            # an empty/missing answer below is a real absence, not a blind read.
            assert {"tool", "params_hash", "ts"} <= declared, (
                f"the trace introspection returned {sorted(declared)!r} — it cannot even see the "
                f"committed columns, so it proves nothing about the new ones."
            )
            missing = set(_TRACE_ADDED_COLUMNS) - declared
            assert not missing, (
                f"the enrichment columns {sorted(missing)} are NOT declared on a store that "
                f"already carried the OLD trace table. That is #107: the definitions converge only "
                f"on a FRESH database, and every long-lived deployment is not one."
            )

            rows = await _trace_rows(store)
            legacy = [row for row in rows if row.get("session") == _LEGACY_TRACE_SESSION]
            assert len(legacy) == 1, "the pre-existing trace row did not survive the migration"
            assert legacy[0]["hit_count"] == _LEGACY_TRACE_HIT_COUNT, (
                "the legacy row's int hit_count no longer reads back after the widening to "
                "option<int> — a widening must converge the SCHEMA without rewriting the DATA."
            )
            # The enrichment columns are unset on a pre-delta row and read NONE
            # through an explicit projection — the humble `option<>` shape.
            assert legacy[0]["ordinal"] is None
            assert legacy[0]["agent"] is None
        finally:
            await store.close()

    async def test_the_sequence_and_the_06_read_index_land_on_the_existing_table(
        self, dirty_trace_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        # T2.1's free window is exactly this moment: the index is created on a
        # table that ALREADY EXISTS (and, on a real deployment, may hold rows).
        # Pinning it against the LIVE store rather than only against the emitted
        # DDL is the difference between proving the recipe and proving the cake.
        connection, env = dirty_trace_db
        await self._apply_old_trace_ddl(connection)
        await self._dirty_the_store(connection)

        store = await self._store_on(env)
        await store.ensure_ready()
        try:
            indexes = await _declared(connection, f"INFO FOR TABLE {TRACE_TABLE}", "indexes")
            assert _TRACE_INDEX_NAME in indexes, (
                f"the 06-read index {_TRACE_INDEX_NAME} is absent after ensure_ready on an "
                f"EXISTING trace table; declared indexes: {sorted(indexes)!r}"
            )
            sequences = await _declared(connection, "INFO FOR DB", "sequences")
            # POSITIVE CONTROL: a sequence this test defined ITSELF is visible, so
            # an absent trace_seq below is a real absence rather than a blind read.
            # (Deliberately not `message_seq`: the message DDL rides its own
            # generator, not `generate_ddl`, so `ensure_ready` never defines it —
            # a control that fails for its own reason proves nothing.)
            assert _CONTROL_SEQUENCE_NAME in sequences, (
                f"the sequence introspection returned {sorted(sequences)!r} — it cannot even see "
                f"the control sequence this test defined, so it proves nothing about trace_seq."
            )
            assert _TRACE_SEQUENCE_NAME in sequences, (
                f"{_TRACE_SEQUENCE_NAME} was not defined by ensure_ready; the ordinal has no mint."
            )
        finally:
            await store.close()

    async def test_the_served_aggregate_still_reads_both_generations_of_row(
        self, dirty_trace_db: tuple[SurrealConnection, SurrealEnv]
    ) -> None:
        # T8: `trace_aggregates` is UNCHANGED by the delta (a GROUP BY over one
        # column is column-additive-safe). Proven on a store holding BOTH an
        # old-shaped and a new-shaped row, since that is the only state where a
        # broken read would show.
        connection, env = dirty_trace_db
        await self._apply_old_trace_ddl(connection)
        await self._dirty_the_store(connection)

        store = await self._store_on(env)
        await store.ensure_ready()
        try:
            await _record_trace(store)
            aggregates = await store.trace_aggregates(window_days=_TELEMETRY_WINDOW_DAYS)
            for_tool = [row for row in aggregates if row.get("tool") == _SEAM_TOOL]
            assert len(for_tool) == 1, f"expected one aggregate group for {_SEAM_TOOL}, got {aggregates!r}"
            assert for_tool[0]["calls"] == 2, (
                f"the served call count is {for_tool[0]['calls']}, not 2. The aggregate must count "
                f"ROWS across both generations — an old row that stops being counted is a "
                f"denominator that silently shrinks."
            )
        finally:
            await store.close()


# --------------------------------------------------------------------------- #
# T3 — the ordinal, at the store where it is minted
# --------------------------------------------------------------------------- #
class TestTheOrdinalIsMintedByTheStore:
    """T3: ONE global native sequence, minted inside the trace write.

    Global, not per-agent: per-agent order is derivable (filter by identity, sort
    by ordinal), while the GLOBAL INTERLEAVING — which a per-agent counter
    destroys — is exactly what "drains against surrounding tool calls" needs.

    Ordinals are 0-BASED (``sequence::nextval`` starts at 0 under the default
    ``START 0``, re-probed 2026-07-24 on 3.2.1), so nothing here assumes 1.
    """

    async def test_every_written_row_carries_an_int_ordinal_never_NONE(
        self, trace_store: SurrealStore
    ) -> None:
        # The schema CANNOT enforce this: `ordinal` is option<int> (the humble
        # shape for a new column on a possibly-populated table), so the contract
        # is the only thing forcing presence. The cheapest green path for a
        # builder is to leave it unset — this pin closes it.
        for ok_value in (True, False):
            await _record_trace(trace_store, ok=ok_value)
        rows = await _trace_rows(trace_store)
        assert len(rows) == 2, f"expected two trace rows, got {len(rows)}"
        for row in rows:
            assert isinstance(row["ordinal"], int) and not isinstance(row["ordinal"], bool), (
                f"a written trace row carries ordinal={row['ordinal']!r}. The emission ALWAYS "
                f"supplies the ordinal; the schema's `option<int>` is the humble shape for a "
                f"pre-extension row, not a licence to omit it."
            )
            assert row["ordinal"] >= 0

    async def test_sequential_writes_carry_strictly_increasing_distinct_ordinals(
        self, trace_store: SurrealStore
    ) -> None:
        written = 3
        for index in range(written):
            await _record_trace(trace_store, params_hash=_expected_params_hash({"i": index}))
        ordinals = sorted(cast(int, row["ordinal"]) for row in await _trace_rows(trace_store))
        assert len(ordinals) == written, f"expected {written} rows, got {len(ordinals)}"
        assert len(set(ordinals)) == written, f"ordinals repeat: {ordinals!r}"
        # Via the controlled predicate (see _is_strictly_increasing's docstring: the
        # inline `strict=True` form this replaces could not pass for ANY build).
        assert _is_strictly_increasing(ordinals), (
            f"ordinals are not strictly increasing: {ordinals!r}"
        )

    async def test_eight_concurrent_writes_mint_eight_distinct_ordinals(
        self, trace_store_factory: Any
    ) -> None:
        # The load-bearing mint pin, at the ruled degree. Separate stores on
        # separate CONNECTIONS: N coroutines on one socket do not contend the way
        # N connections do.
        #
        # WHAT IT KILLS, stated accurately: a read-max-then-CREATE mint, and any
        # mint whose numbers collide across CONCURRENT writers in ONE process.
        # ⚠ It does NOT kill every client-side mint — this comment used to claim it
        # did, and the adversary measured the counter-example: a PER-PROCESS
        # client-side counter passes this pin (all 8 writers share one process, so
        # its numbers are distinct) and is caught instead by
        # `test_a_count_is_derived_from_ROWS_never_from_ordinal_arithmetic`, whose
        # engine-burn control it cannot reproduce, and by
        # `test_the_seam_never_mints_the_ordinal_itself`. Corrected here rather
        # than left as an inherited over-claim: a comment promising a check the
        # assertion does not perform is a false gate.
        writers = 8
        stores = [await trace_store_factory() for _ in range(writers)]
        await asyncio.gather(
            *[
                _record_trace(store, params_hash=_expected_params_hash({"writer": index}))
                for index, store in enumerate(stores)
            ]
        )
        rows = await _trace_rows(stores[0])
        ordinals = [row["ordinal"] for row in rows]
        assert len(ordinals) == writers, f"expected {writers} rows, got {len(ordinals)}: {rows!r}"
        assert all(isinstance(ordinal, int) for ordinal in ordinals), (
            f"a concurrent write recorded a non-int ordinal: {ordinals!r}"
        )
        assert len(set(ordinals)) == writers, (
            f"{writers} concurrent writes minted {len(set(ordinals))} distinct ordinals: "
            f"{sorted(ordinals)!r}. A collision here means the mint is not the engine's."
        )

    async def test_a_count_is_derived_from_ROWS_never_from_ordinal_arithmetic(
        self, trace_store: SurrealStore
    ) -> None:
        # Gaps in the sequence are REAL and benign (an aborted call burning a
        # number costs nothing) — the ordinal is an ORDERING KEY, never a count.
        # `max(ordinal) - min(ordinal)` is a wrong build, and this is the pin that
        # says so with a real gap in the data.
        await _record_trace(trace_store)
        await trace_store._query(f'RETURN sequence::nextval("{_TRACE_SEQUENCE_NAME}")')
        await _record_trace(trace_store)
        rows = await _trace_rows(trace_store)
        ordinals = sorted(cast(int, row["ordinal"]) for row in rows)
        assert len(ordinals) == 2, f"expected two rows, got {len(ordinals)}"
        # CONTROL: a number was genuinely burned, so span != count here.
        assert ordinals[-1] > ordinals[0] + 1, (
            f"no gap was created ({ordinals!r}), so this pin cannot discriminate row-counting from "
            f"ordinal arithmetic — the burn did not take."
        )
        aggregates = await trace_store.trace_aggregates(window_days=_TELEMETRY_WINDOW_DAYS)
        for_tool = [row for row in aggregates if row.get("tool") == _SEAM_TOOL]
        assert len(for_tool) == 1
        assert for_tool[0]["calls"] == len(rows), (
            f"the served count is {for_tool[0]['calls']} for {len(rows)} rows spanning ordinals "
            f"{ordinals!r} — a count derived from ordinal arithmetic rather than from the ROW SET."
        )


class TestRecordTraceAtTheNewSignature:
    """T8: ``record_trace`` gains the four optional params; both widened ones read.

    The committed per-key pins in ``test_surreal_store.py`` stay green by design
    (every new column is ``option<>``), so these legs cover only what the delta
    ADDS: the new parameters actually reaching the row, and an unset optional
    reading NONE rather than a fabricated zero or empty string.
    """

    async def test_the_declared_fields_round_trip(self, trace_store: SurrealStore) -> None:
        await _record_trace(trace_store, session=_DECLARED_SESSION, hit_count=None)
        rows = await _trace_rows(trace_store)
        assert len(rows) == 1
        row = rows[0]
        assert row["agent"] == _DECLARED_AGENT
        assert row["action"] == _DECLARED_ACTION
        assert row["transport_session"] == _TRANSPORT_SESSION_ID
        assert row["session"] == _DECLARED_SESSION
        assert row["ok"] is True
        assert row["hit_count"] is None, (
            "an explicitly-unknown hit count must store NONE; a zero would make every aggregate "
            "over the column lie."
        )

    async def test_an_anonymous_row_stores_NONE_in_every_declared_column(
        self, trace_store: SurrealStore
    ) -> None:
        # The fully anonymous row: a call that declared nothing still lands, and
        # its absent identity is REPRESENTED rather than invented.
        await _record_trace(
            trace_store, agent=None, action=None, transport_session=None, ok=False
        )
        rows = await _trace_rows(trace_store)
        assert len(rows) == 1
        row = rows[0]
        assert row["agent"] is None
        assert row["action"] is None
        assert row["transport_session"] is None
        assert row["session"] is None
        assert row["ok"] is False
        # ...and it STILL advances the denominator, which is the whole point.
        assert isinstance(row["ordinal"], int)
        assert row["tool"] == _SEAM_TOOL

    async def test_the_widened_columns_still_REJECT_a_wrong_typed_value(
        self, trace_store: SurrealStore
    ) -> None:
        """R7 CLOSED: `option<int>` widens the DOMAIN, it does not remove the TYPE.

        The adversary recorded this as an unpinned property in BOTH worlds (no pin
        ever asserted a type rejection for these columns), i.e. not a regression —
        but "not a regression" is how a silent loosening to ``any`` or ``option<any>``
        ships. `option<int>` must still refuse a string; the difference from `int` is
        that NONE becomes representable, not that anything goes.

        Driven through a raw CREATE rather than ``record_trace`` because the point is
        the ENGINE's constraint, not the writer's typing: mypy already stops a
        wrong-typed Python call, and mypy is not what production faces.
        """
        with pytest.raises(SurrealStoreError) as rejected:
            await trace_store._query(
                f"CREATE {TRACE_TABLE} CONTENT $content",
                {
                    "content": {
                        "tool": _SEAM_TOOL,
                        "params_hash": _SEAM_PARAMS_HASH,
                        "latency_ms": _SEAM_LATENCY_MS,
                        "hit_count": "not-an-int",
                    }
                },
            )
        # Classified as a FIELD COERCION rejection — not a connection fault, not a
        # parse error. The store deliberately REDACTS the engine's field detail into
        # the server log, so the class is what a test can honestly assert; the
        # positive control below is what makes it discriminating.
        # (This assertion first read `"hit_count" in str(...)`, which the redaction
        # makes unsatisfiable for every build — the same cannot-pass class as MP-C,
        # caught here by running it.)
        assert _ERROR_CLASS_FIELD_COERCION in str(rejected.value), (
            f"the engine rejected the write, but not as a {_ERROR_CLASS_FIELD_COERCION!r} — a probe "
            f"that passes for the wrong reason (a parse error, a dropped connection) proves "
            f"nothing. Served: {rejected.value}"
        )
        # POSITIVE CONTROL: the same shape with a legal value IS accepted, so the
        # rejection above is about the TYPE and not about the statement.
        await trace_store._query(
            f"CREATE {TRACE_TABLE} CONTENT $content",
            {
                "content": {
                    "tool": _SEAM_TOOL,
                    "params_hash": _SEAM_PARAMS_HASH,
                    "latency_ms": _SEAM_LATENCY_MS,
                    "hit_count": 3,
                }
            },
        )
        rows = await _trace_rows(trace_store)
        assert [row["hit_count"] for row in rows] == [3]

    async def test_the_ok_column_stores_a_real_boolean(self, trace_store: SurrealStore) -> None:
        # `option<bool>` and not a string/int flag: a build storing "True"/1
        # would make every `ok = false` filter in packet 06 silently empty.
        await _record_trace(trace_store, ok=False)
        rows = await _trace_rows(trace_store)
        assert len(rows) == 1
        assert rows[0]["ok"] is False, f"ok stored as {rows[0]['ok']!r}, not a boolean"


# --------------------------------------------------------------------------- #
# T8 — the retired plan in production prose (AC-19's telemetry slice)
# --------------------------------------------------------------------------- #
# The retired telemetry vocabulary: phrases that describe the plan T5.2 REFUSED
# (fire-and-forget emission, a later serving-layer phase, no caller wiring it) or a
# column count the delta falsifies. Each is a PHRASE, not a word, so an unrelated
# sentence cannot trip it.
_RETIRED_TELEMETRY_PROSE: tuple[str, ...] = (
    "fire-and-forget",
    "six core",
    "no caller yet",
    "later serving-layer phase",
    "not yet wired",
    "never wired",
)
# The tokens that make a piece of prose TELEMETRY prose. A comment or docstring
# mentioning none of these is out of this sweep's scope — which is what keeps a
# legitimate "left for a later phase" elsewhere in the same module from tripping it.
_TELEMETRY_PROSE_TOKENS: tuple[str, ...] = ("trace", "tracing", "telemetry")
# The modules whose telemetry prose is swept. Not a list of DOCSTRINGS (that is the
# name-list shape this repo has watched lose six times) — a list of MODULES, every
# comment and string in which is scanned.
_SWEPT_PROSE_MODULES: tuple[str, ...] = (
    "loremaster.store.surreal",
    "loremaster.store.surreal_schema",
    "loremaster.server",
)


def _telemetry_prose_offenders(source: str) -> list[tuple[str, str]]:
    """Every ``(retired phrase, prose excerpt)`` in ``source``'s telemetry prose.

    Scans COMMENT and STRING tokens — so docstrings, module headers and inline
    comments are all in scope — and considers only those mentioning a telemetry
    token, because the same modules legitimately say things like "left for a later
    phase" about unrelated subsystems. A gate that fires on honest prose is a gate
    that gets switched off; a gate that only looks at three docstrings somebody
    named by hand misses the fourth.
    """
    offenders: list[tuple[str, str]] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type not in (tokenize.COMMENT, tokenize.STRING):
            continue
        prose = " ".join(token.string.replace("#", " ").split())
        lowered = prose.lower()
        if not any(marker in lowered for marker in _TELEMETRY_PROSE_TOKENS):
            continue
        offenders.extend(
            (phrase, prose) for phrase in _RETIRED_TELEMETRY_PROSE if phrase in lowered
        )
    return offenders


class TestNoProductionProseStillTeachesTheRetiredPlan:
    """No telemetry prose in production may teach a plan the design REFUSED.

    T5.2 rules AGAINST fire-and-forget emission (the coverage gate must be
    deterministic — "the row exists when the call returns" — or it goes flaky and
    gets switched off, and a gate that cries wolf is a gate nobody keeps). Several
    production surfaces teach exactly that retired plan, plus a column count the
    delta falsifies, and this repo's own audited failure pattern is defects
    clustering in natural-language surfaces whose consistency with code NO GATE
    CHECKS.

    **This is a SWEEP, not a list of docstrings.** Its first version named three
    docstrings by hand and the adversary found three MORE unguarded corpses — one of
    them `TraceSummary`'s, which is the docstring of the model ``lore_index``
    SERVES, i.e. the served-prose class this packet is supposed to be closing. A
    name-list is the instrument shape this repo has watched lose six times; the
    sweep covers every comment and string in the three modules, so prose written
    LATER is covered without anyone remembering to extend a list.

    Scoped by TELEMETRY TOKEN rather than by module, deliberately: the same modules
    legitimately say "left for a later phase" about unrelated subsystems, and a gate
    that reddens honest prose is a gate someone switches off — the threat model here
    is the honest author who edits a trace docstring, not an adversary.
    """

    @pytest.mark.parametrize("module_name", _SWEPT_PROSE_MODULES)
    def test_no_telemetry_prose_teaches_the_retired_plan(self, module_name: str) -> None:
        module = importlib.import_module(module_name)
        offenders = _telemetry_prose_offenders(inspect.getsource(module))
        assert not offenders, (
            f"{module_name} still teaches the retired telemetry plan in "
            f"{len(offenders)} place(s):\n"
            + "\n".join(f"  · {phrase!r} in: {prose[:160]}" for phrase, prose in offenders)
            + "\n\nThe emission is AWAITED INLINE (T5.2), it IS wired (T1), and the row carries "
            "eleven columns plus a server-stamped ts — every phrase above describes a plan the "
            "design refused or a count the delta falsifies. Prose that describes behaviour must be "
            "DERIVED from it or CHECKED against it; this is the check."
        )

    def test_the_sweep_itself_fires(self) -> None:
        """THE CONTROL: the sweep must SEE a corpse, and must IGNORE honest prose.

        Without this, a sweep whose token filter or tokenizer walk silently matched
        nothing would pass all three module legs forever and read as coverage. Both
        directions, on samples built here.
        """
        corpse = '"""The trace row is written fire-and-forget by a later phase."""\n'
        assert _telemetry_prose_offenders(corpse), (
            "the sweep did not flag a docstring that both mentions the trace row AND teaches the "
            "retired plan — it cannot see what it certifies"
        )
        # NEGATIVE, and it must be DISCRIMINATING: retired phrasing about a
        # DIFFERENT subject is not this pin's business, because a gate that reddens
        # honest prose is a gate someone switches off.
        #
        # ⚠ The sample carries a RETIRED PHRASE deliberately (adversary RG-R1): the
        # first version said only "left for a later phase" — no retired phrase at
        # all — so an UNSCOPED sweep (token filter removed) returned `[]` for it
        # too, and this leg passed for both the correct instrument and a broken one.
        # Measured by the adversary: with the phrase present, the unscoped sweep
        # returns a hit and this assertion FAILS, which is what makes the scoping
        # the thing the control actually proves.
        assert not _telemetry_prose_offenders(
            "# app-level retry/backoff is left for a later serving-layer phase\n"
        ), (
            "the sweep flagged retired phrasing about a NON-telemetry subject. Its scope is "
            "telemetry prose; firing on an honest sentence about another subsystem is how an "
            "instrument earns a `# noqa` and stops guarding anything."
        )
        # NEGATIVE: honest telemetry prose passes.
        assert not _telemetry_prose_offenders(
            '"""Persist one trace row: awaited inline, ts stamped server-side."""\n'
        )
