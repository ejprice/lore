"""Contract tests for packet 03b's ALL-TOOLS trace telemetry — delta table row **H**.

Spec (execute verbatim; a genuine gap is a STOP-and-flag, never an improvised design
decision — see this module's escalations in ``REPORT-contract-telemetry-03b.md``):

* ``docs/plans/v2/03b-comms-surface-design-rulings.md`` §S6v2 (drain/all-tools telemetry —
  **v1 is SUPERSEDED**, do not implement it) and §S7 (caller identity), plus the
  consolidated delta table rows **F** (schema), **G** (``server.py`` seam) and **H** (this
  file).
* ``docs/plans/v2/03b-comms-message-surface.md`` — the packet, including the operator's
  2026-07-24 scope widening to all-tools tracing and its five consequences.
* ``docs/plans/v2/receipts/2026-07-24-packet03b/REPORT-scout-147-traces.md`` §5 — the #147
  diagnosis this contract rests on: ``SurrealStore.record_trace`` exists, is correct, and
  has ZERO production callers in source AND in the deployed artifact.
* ``docs/reference/surrealdb-31-capabilities.md`` — repo STORE LAW, read first because this
  contract governs a schema change. §1.1 (``OVERWRITE`` for fields, ``IF NOT EXISTS`` for
  indexes/analyzers/tables/sequences), §1.4 (schema converges but DATA does not; a NEW
  required field on a POPULATED table), §1.6 (the virgin-DB blind spot that hid #107), §5
  (native sequences: ``sequence::nextval``, gaps are real, seq is an ORDERING key).

WHAT THIS FILE PINS, IN ONE SENTENCE: that the telemetry emission is an invariant over
**every tool the server actually registers** — derived, never enumerated — and that the
per-caller key which gives the decay curve its denominator is stable within an MCP session
and distinct across sessions.

THE FAILURE MODE THIS FILE EXISTS TO PREVENT, NAMED. lore has been defeated six times by
instruments keyed on a NAME LIST (CLAUDE.md, "the instrument lesson"): a label's literal,
a symbol's name, ``async def _query``, three SDK method names, two receiver names — and,
closest to home, **a runtime gate keyed on the four tests that armed it, defeated by a path
no test executed.** That last one is precisely this contract's own failure mode, so the
coverage pin below does the one thing that answers it: it makes COVERAGE A CHECKED
VARIABLE. The registered set is read from the server's OWN registration
(``FastMCP.list_tools``); every member is driven through the REAL dispatch entry point
(``FastMCP.call_tool``); and the observed set is asserted EQUAL to it — never ``>=``, never
a floor, never a hardcoded list. A tool added by packet 04 that the seam does not cover
turns this file RED without anybody remembering to update it.

RED BY DESIGN, AND RED FOR THE RIGHT REASON. At authoring time (HEAD ``7d2ad32``,
2026-07-23) NONE of the row-F/row-G production symbols exist: there is no tracing
``call_tool`` seam, no ``loremaster.server._annotate_trace``, no ``TracingFastMCP``, and
``SurrealStore.record_trace`` still carries the pre-03b signature. Every pin here is
expected to fail at RUN time with an ``AttributeError``/``AssertionError`` naming the
missing seam — **never at COLLECTION time**. That distinction is load-bearing and it has
already cost this repo a wave: finding #133, where a module-level import of a not-yet-built
module made six suites UNCOLLECTABLE and ~1,220 tests silently stopped being counted.
Hence: every production symbol that packet 03b introduces is reached through the CALL-TIME
accessor :func:`_server_attr`, never a module-level ``from loremaster.server import ...``.
(PLC0415 import-outside-top-level is an ignored house idiom in this repo.)

STORE SAFETY. Every live pin in this file runs against the TEST store
``ws://127.0.0.1:18000`` via ``_surreal_harness`` (``unique_database()`` mints a virgin
``test_<pid>_<uuid4>`` per test, which is what makes ``-n auto`` safe). ``:18500`` is
PRODUCTION and is never touched: the deploy-smoke leg (§J) is a pure assertion FUNCTION
over a payload the lead obtains from the deployed artifact — this file opens no connection
to it.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import inspect
import json
from collections.abc import AsyncIterator, Mapping, Sequence
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import httpx
import pytest
import pytest_asyncio
from _comms_fakes import (
    FakeAgentDatabase,
    FakeAgentRegistry,
    FakeBriefDatabase,
    FakeBriefLedger,
)
from _surreal_harness import (
    PRODUCTION_DIM,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.config import LoreConfig
from loremaster.server import AppContext, LoreServer, build_mcp_server
from loremaster.store.surreal import SurrealStore
from loremaster.store.surreal_schema import TRACE_TABLE
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.lowlevel.server import request_ctx
from mcp.shared.context import RequestContext

# --------------------------------------------------------------------------- #
# CALL-TIME accessors for the production symbols packet 03b introduces.
#
# See the module docstring: a module-level import of a not-yet-built symbol makes
# the WHOLE file uncollectable (#133), which is a strictly worse failure than a
# red test — an uncollectable module's pins are not red, they are ABSENT, and the
# suite tail happily reports a passed-count that no longer includes them.
# --------------------------------------------------------------------------- #


def _server_attr(name: str) -> Any:
    """Resolve ``loremaster.server.<name>`` at CALL time, or fail nameing the packet.

    Raises:
        AttributeError: The symbol does not exist yet — i.e. packet 03b's delta
            row **G** has not landed. This is the contract's designed RED.
    """
    import loremaster.server as server_module

    try:
        return getattr(server_module, name)
    except AttributeError as error:  # pragma: no cover - the RED path until row G lands
        raise AttributeError(
            f"loremaster.server.{name} does not exist — packet 03b delta row G "
            f"(design rulings §S6v2/§S7) has not landed. This contract is RED BY DESIGN "
            f"until the tracing dispatch seam ships; it is NOT a typo or an import-path bug."
        ) from error


def _annotate_trace(**fields: Any) -> None:
    """The ONE request-scoped domain-enrichment helper (design §S6v2 item 3).

    ⚠ NAME PRESCRIBED BY THIS CONTRACT AND ESCALATED. The design rulings name the
    channel ("ONE narrow helper whose key set is CLOSED") but not the symbol. This
    contract binds it to ``loremaster.server._annotate_trace``; the builder brief
    must carry that name verbatim. See ``REPORT-contract-telemetry-03b.md``
    escalation E1.
    """
    _server_attr("_annotate_trace")(**fields)


# The CLOSED annotation key set (design §S6v2 item 3). ``agent`` is the str of the
# resolved agent RecordID; ``session`` the EXPLICIT fleet session; ``hit_count`` /
# ``pending`` / ``peeked`` are drain's served count, total_pending and peek flag.
_ANNOTATION_KEYS: tuple[str, ...] = ("agent", "session", "hit_count", "pending", "peeked")
# Fields the SEAM owns. An annotator must never be able to forge them — a handler
# that could rewrite ``tool`` or ``caller`` would make the coverage pin below a
# liar in exactly the way the six-defeats table describes.
_SEAM_OWNED_FIELDS: tuple[str, ...] = ("tool", "caller", "seq", "latency_ms", "params_hash")

# Wire column names on the ``trace`` table (design §S6v2 item 5). Read as literal
# keys because that is what a ``SELECT`` hands back; the schema module's own
# constants are the builder's business, this contract pins the WIRE.
TRACE_CALLER = "caller"
TRACE_SEQ = "seq"
TRACE_AGENT = "agent"
TRACE_PENDING = "pending"
TRACE_PEEKED = "peeked"
TRACE_TOOL = "tool"
TRACE_HIT_COUNT = "hit_count"
TRACE_SESSION = "session"
TRACE_LATENCY_MS = "latency_ms"
TRACE_PARAMS_HASH = "params_hash"

_DIM = 2048

# --------------------------------------------------------------------------- #
# Probe tools registered onto the REAL built server.
#
# These are not decoration: they are how this contract proves the seam covers
# tools it was never told about — the property the whole packet turns on. A pin
# that only drives today's built-ins cannot distinguish "coverage by seam" from
# "coverage by a list somebody happened to keep current".
# --------------------------------------------------------------------------- #

PROBE_OK = "probe_trace_ok"
PROBE_BOOM = "probe_trace_boom"
PROBE_SLOW = "probe_trace_slow"
PROBE_ECHO = "probe_trace_echo"
PROBE_ANNOTATE = "probe_trace_annotate"
PROBE_PLAIN = "probe_trace_plain"
PROBE_ANNOTATE_THEN_BOOM = "probe_trace_annotate_then_boom"
PROBE_BAD_KEY = "probe_trace_bad_key"
PROBE_SEAM_FORGE = "probe_trace_seam_forge"
PROBE_LATE = "probe_trace_late_registration"

# A value no lore tool would ever produce, used to prove argument VALUES never
# reach the trace row (§S6v2 item 2: "a HASH, so message bodies never enter the
# trace, private by construction").
_SECRET = "STOP-and-re-run-the-gate-xyzzy-9f3c-secret-body"

# The annotation payload the drain-shaped probe contributes. Every value is
# DISTINCT and none coincides with another — a fixture where ``hit_count`` equalled
# ``pending`` could not tell a build that writes total_pending into hit_count from
# a correct one (the small-N / arithmetic-alignment class, CLAUDE.md).
_PROBE_ANNOTATION: dict[str, Any] = {
    "agent": "agent:a_fixer_b_03b",
    "session": "wave7",
    "hit_count": 2,
    "pending": 5,
    "peeked": True,
}

_SLOW_TOOL_SLEEP_S = 0.06
_SLOW_TOOL_FLOOR_MS = 40.0
# Generous ceiling: a wall-clock upper bound that still catches a build stamping a
# monotonic-clock READING (nanoseconds since boot) instead of an elapsed duration.
_LATENCY_CEILING_MS = 60_000.0

_CONCURRENT_SEQ_WRITERS = 8


def _config(slug: str) -> LoreConfig:
    """A minimal, valid :class:`LoreConfig` for ``build_mcp_server``.

    Fixture DATA, deliberately local (the same stance ``test_comms_tool.py``
    states): duplicating a validated dict couples nothing, whereas importing a
    non-``_``-prefixed test module as a helper does.
    """
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


# --------------------------------------------------------------------------- #
# The recording write_store double + the request-context harness.
# --------------------------------------------------------------------------- #


class _RecordingStore:
    """A ``write_store`` double that captures every ``record_trace`` call verbatim.

    Deliberately ``**fields``-shaped rather than mirroring a fixed signature: a
    build that renames a column (``caller_key=`` for ``caller=``) is captured under
    the WRONG key and the assertion fails naming it, instead of the double raising
    a ``TypeError`` that reads like a harness bug.
    """

    def __init__(self, *, fail_with: BaseException | None = None) -> None:
        self.rows: list[dict[str, Any]] = []
        self.fail_with = fail_with
        self.next_seq = 0

    async def record_trace(self, **fields: Any) -> None:
        await asyncio.sleep(0)
        if self.fail_with is not None:
            raise self.fail_with
        self.next_seq += 1
        # The real store mints ``seq`` inside its own CREATE (§S6v2 item 4), so the
        # double mints one too: a caller that supplies ``seq=`` is caught by the
        # signature pin in §H, not silently accepted here.
        self.rows.append({TRACE_SEQ: self.next_seq, **fields})

    def rows_for(self, tool: str) -> list[dict[str, Any]]:
        return [row for row in self.rows if row.get(TRACE_TOOL) == tool]

    def one_row_for(self, tool: str) -> dict[str, Any]:
        matches = self.rows_for(tool)
        assert len(matches) == 1, (
            f"expected exactly ONE trace row for {tool!r}, got {len(matches)}: "
            f"{[row.get(TRACE_TOOL) for row in self.rows]}"
        )
        return matches[0]


class _SessionStandIn:
    """A stand-in for the SDK's ``ServerSession`` object.

    Only its OBJECT IDENTITY matters: §S7 rung 1 keys a ``WeakKeyDictionary`` on
    the session object, so a test needs distinct, weak-referenceable objects — not
    a real session. Weak-referenceability is why this is a class and not
    ``object()``-with-attributes.
    """

    def __init__(self, label: str) -> None:
        self.label = label


@contextlib.contextmanager
def _request_context(app_context: Any, *, session: Any, request_id: int = 1) -> Any:
    """Install a real ``RequestContext`` so ``FastMCP.get_context()`` resolves.

    ``FastMCP.call_tool`` calls ``self.get_context()``, which reads the low-level
    server's ``request_ctx`` ContextVar. Setting it here is how a test drives the
    PRODUCTION dispatch entry point without standing up the streamable-http
    session machinery. (The real-transport legs in §E do stand it up, precisely so
    that this shortcut is never the only evidence.)
    """
    token = request_ctx.set(
        RequestContext(
            request_id=request_id,
            meta=None,
            session=session,
            lifespan_context=app_context,
            request=None,
        )
    )
    try:
        yield
    finally:
        request_ctx.reset(token)


def _register_probe_tools(mcp: Any) -> None:
    """Register the probe tools onto an already-built server.

    Registration AFTER ``build_mcp_server`` is the point: these tools are exactly
    the "tool a future packet adds" case, and the seam must cover them without
    having been told they exist.
    """

    async def probe_ok() -> str:
        return "ok"

    async def probe_boom() -> str:
        raise RuntimeError("probe_trace_boom raises on purpose (the error-path leg)")

    async def probe_slow() -> str:
        await asyncio.sleep(_SLOW_TOOL_SLEEP_S)
        return "slow"

    async def probe_echo(secret: str) -> str:
        return "echoed"

    async def probe_annotate() -> str:
        _annotate_trace(**_PROBE_ANNOTATION)
        return "annotated"

    async def probe_plain() -> str:
        return "plain"

    async def probe_annotate_then_boom() -> str:
        _annotate_trace(**_PROBE_ANNOTATION)
        raise RuntimeError("annotated, then raised (the error-path leak leg)")

    async def probe_bad_key() -> str:
        # A LEGAL key alongside an ILLEGAL one: the row must end up carrying
        # NEITHER (atomic refusal), not the legal half.
        _annotate_trace(agent="agent:a_should_not_land", bogus_key_03b=1)
        return "unreachable"

    async def probe_seam_forge() -> str:
        _annotate_trace(tool="lore_pretend", caller="forged-caller")
        return "unreachable"

    for name, fn, description in (
        (PROBE_OK, probe_ok, "Probe: returns successfully."),
        (PROBE_BOOM, probe_boom, "Probe: raises."),
        (PROBE_SLOW, probe_slow, "Probe: sleeps, then returns."),
        (PROBE_ECHO, probe_echo, "Probe: takes a secret argument and ignores it."),
        (PROBE_ANNOTATE, probe_annotate, "Probe: contributes domain annotations."),
        (PROBE_PLAIN, probe_plain, "Probe: contributes nothing."),
        (
            PROBE_ANNOTATE_THEN_BOOM,
            probe_annotate_then_boom,
            "Probe: annotates, then raises.",
        ),
        (PROBE_BAD_KEY, probe_bad_key, "Probe: annotates an illegal key."),
        (PROBE_SEAM_FORGE, probe_seam_forge, "Probe: tries to annotate seam-owned fields."),
    ):
        mcp.add_tool(fn, name=name, description=description)


def _probe_arguments() -> dict[str, dict[str, Any]]:
    """Arguments for the tools that need them during the coverage sweep."""
    return {PROBE_ECHO: {"secret": _SECRET}}


async def _sweep_every_registered_tool(mcp: Any, recorder: _RecordingStore) -> list[str]:
    """Drive EVERY registered tool once through the real dispatch entry point.

    Most built-in lore tools will raise (their arguments are missing and the app
    context is a double) — that is not a weakness of the sweep, it is the whole
    point of the seam's ``try/finally``: an errored pull is still a pull. The
    SUCCESS leg is supplied by the probe tools, so the sweep contains both fates
    and a build that only writes rows on the error path is caught by
    ``test_a_succeeding_call_writes_its_row``.

    Returns:
        The dispatch order, so a caller can compare it to the observed order.
    """
    arguments = _probe_arguments()
    dispatched: list[str] = []
    with _request_context(SimpleNamespace(write_store=recorder), session=_SessionStandIn("sweep")):
        for tool in await mcp.list_tools():
            dispatched.append(tool.name)
            with contextlib.suppress(Exception):
                await mcp.call_tool(tool.name, arguments.get(tool.name, {}))
    return dispatched


@pytest_asyncio.fixture()
async def traced_server() -> AsyncIterator[tuple[Any, _RecordingStore]]:
    """A REAL ``build_mcp_server`` product + the probe tools + a recording store."""
    mcp = build_mcp_server(LoreServer(_config("trace_telemetry_03b")))
    _register_probe_tools(mcp)
    yield mcp, _RecordingStore()


async def _call(
    mcp: Any,
    recorder: _RecordingStore,
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    session: Any = None,
    request_id: int = 1,
    app_context: Any = None,
) -> Any:
    """Dispatch ONE tool through the real seam. Exceptions propagate to the caller."""
    context = app_context if app_context is not None else SimpleNamespace(write_store=recorder)
    with _request_context(
        context, session=session if session is not None else _SessionStandIn("s"), request_id=request_id
    ):
        return await mcp.call_tool(name, arguments or {})


# =========================================================================== #
# Section B — COVERAGE AS A CHECKED VARIABLE (row H pin 1)
# =========================================================================== #


class TestCoverageIsACheckedVariable:
    """The registered set and the traced set must be EQUAL — derived, never listed.

    THE THREAT MODEL, written into the instrument rather than left to a reviewer
    (CLAUDE.md: "a gate needs a threat model"). This pin is for the HONEST
    ENGINEER who adds a tool in packet 04, 05 or 06 and never learns that
    telemetry exists — #147's own shape, where a status surface reported a field
    nobody consumed so nobody noticed it was dead. It is NOT a boundary against an
    author who deliberately routes around ``FastMCP.call_tool``; anyone who can
    commit here can already ship anything. Verdicts follow mechanically: "a tool
    registered by a future packet goes untraced" IS a defect; "a hand-rolled
    transport could bypass the seam" is not.
    """

    async def test_every_registered_tool_writes_a_trace_row(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        mcp, recorder = traced_server
        dispatched = await _sweep_every_registered_tool(mcp, recorder)

        registered = set(dispatched)
        observed = {row[TRACE_TOOL] for row in recorder.rows}
        assert observed == registered, (
            "SET EQUALITY over the REGISTERED tool surface is the invariant, not a floor: "
            f"registered-but-never-traced={sorted(registered - observed)}; "
            f"traced-but-not-registered={sorted(observed - registered)}. A tool a later "
            "packet registers must be covered BY THE SEAM, never by anyone remembering to "
            "add its name to a list."
        )

    async def test_the_traced_order_is_the_dispatch_order(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """Set equality alone would admit a build that writes rows it never dispatched.

        What wrong build does this catch: one that, on ANY call, emits one row per
        registered tool (or that batches/replays names). Set equality passes; an
        ordered, one-row-per-dispatch comparison does not.
        """
        mcp, recorder = traced_server
        dispatched = await _sweep_every_registered_tool(mcp, recorder)
        observed = [row[TRACE_TOOL] for row in recorder.rows]
        pairs = zip(observed, dispatched, strict=False)
        divergence = next((index for index, (a, b) in enumerate(pairs) if a != b), "n/a")
        assert observed == dispatched, (
            "each dispatch writes EXACTLY ONE row, in dispatch order — "
            f"dispatched {len(dispatched)} tools, observed {len(observed)} rows; "
            f"first divergence at index {divergence}"
        )

    async def test_the_coverage_derivation_is_live_not_a_snapshot(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """THE SELF-ATTACK on the coverage pin itself.

        A coverage pin that reads a STALE registration snapshot would pass forever
        while the served surface grew past it. Register a tool the fixture never
        mentioned, sweep again, and demand the new name appear on BOTH sides. This
        is the positive control for the instrument, not for the code: it proves the
        pin can SEE a new tool at all.
        """
        mcp, recorder = traced_server

        async def probe_late() -> str:
            return "late"

        mcp.add_tool(probe_late, name=PROBE_LATE, description="Probe: registered after the fixture.")
        dispatched = await _sweep_every_registered_tool(mcp, recorder)

        assert PROBE_LATE in dispatched, (
            "the sweep must read the registration LIVE (FastMCP.list_tools), so a tool "
            "registered after the fixture is dispatched too — otherwise the coverage pin "
            "is grading a snapshot"
        )
        assert PROBE_LATE in {row[TRACE_TOOL] for row in recorder.rows}, (
            f"{PROBE_LATE} was dispatched through the real seam but wrote no trace row — "
            "the seam does not cover tools registered after build time, which is exactly "
            "the packet-04/05/06 case"
        )

    async def test_a_succeeding_call_writes_its_row(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """POSITIVE CONTROL for the error-path leg below.

        What wrong build does this catch: one that emits ONLY from the ``except``
        arm. Most of the sweep rides error paths, so without this leg the coverage
        pin would green-light a seam that never traces a successful call — i.e.
        every real drain, search and read in production.
        """
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_OK)
        assert recorder.rows_for(PROBE_OK), (
            "a tool that RETURNED NORMALLY wrote no trace row; the emission must live in "
            "a finally, covering both fates"
        )

    async def test_a_raising_call_still_writes_its_row(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """The error-path leg (§S6v2 item 2: "an errored pull is still a pull")."""
        mcp, recorder = traced_server
        with pytest.raises(Exception):  # noqa: B017 - the SDK wraps handler errors; the TYPE is not the pin
            await _call(mcp, recorder, PROBE_BOOM)
        assert recorder.rows_for(PROBE_BOOM), (
            "a tool that RAISED wrote no trace row. An errored pull is still a pull — a "
            "seam that traces only successes systematically under-counts exactly the "
            "sessions where an agent is struggling, which is the population the decay "
            "curve is about"
        )

    async def test_every_row_carries_a_caller_key(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """``caller`` is schema-``option`` but seam-written on EVERY row (§S6v2 item 5).

        Presence is enforced HERE, by pin, because the schema deliberately cannot:
        the column is ``option<string>`` so the store layer's own probes can write
        without one. What wrong build does this catch: one that writes ``caller``
        only when it happens to resolve a session, leaving generic calls
        unattributed — a denominator with holes, which is a denominator that lies.
        """
        mcp, recorder = traced_server
        await _sweep_every_registered_tool(mcp, recorder)
        missing = [row[TRACE_TOOL] for row in recorder.rows if not row.get(TRACE_CALLER)]
        assert recorder.rows, "the sweep wrote no rows at all — nothing to check"
        assert not missing, (
            f"{len(missing)} trace rows carry no caller key ({missing[:5]}). Per-caller "
            "attribution is what gives the decay curve a denominator; a row without it is "
            "a call that cannot be attributed to any agent"
        )

    async def test_seqs_are_distinct_and_increasing_across_a_sweep(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """``seq`` is a global ORDERING key: strictly increasing, never reused.

        Gaps are legal and expected (store reference §5: an aborted transaction
        burns a number), so this asserts strict monotonicity and distinctness —
        never contiguity, and never that ``seq`` is a count.
        """
        mcp, recorder = traced_server
        dispatched = await _sweep_every_registered_tool(mcp, recorder)
        seqs = [row[TRACE_SEQ] for row in recorder.rows]
        # NON-VACUITY GUARD, first. Every assertion below (all / sorted / set-size)
        # is TRIVIALLY TRUE of an empty list, so without this the pin greens on a
        # seam that writes nothing at all — the exact shape it exists to catch.
        assert len(seqs) == len(dispatched), (
            f"expected one seq per dispatched tool ({len(dispatched)}), got {len(seqs)} — "
            "an empty row set satisfies every ordering assertion below vacuously"
        )
        assert all(isinstance(value, int) for value in seqs), f"seq must be int, got {seqs[:5]}"
        assert seqs == sorted(seqs), f"seq must be non-decreasing in dispatch order: {seqs[:10]}"
        assert len(set(seqs)) == len(seqs), (
            f"seq must be DISTINCT per row — {len(seqs) - len(set(seqs))} duplicates. A "
            "duplicated ordering key destroys the interleaving the global sequence exists "
            "to preserve"
        )


# =========================================================================== #
# Section C — the seam's own recorded fields: latency, params_hash, privacy
# =========================================================================== #


class TestTheSeamRecordsItsOwnFieldsHonestly:
    async def test_latency_measures_the_dispatch(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """``latency_ms`` is wall-to-wall around the delegate (§S6v2 item 2).

        What wrong build does this catch: one that records a constant (0, or the
        clock reading), or that starts the timer after the delegate returns. The
        fixture sleeps a KNOWN duration so the assertion has something to
        discriminate against — a floor of 0 would pass any build at all.
        """
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_SLOW)
        latency = recorder.one_row_for(PROBE_SLOW)[TRACE_LATENCY_MS]
        assert isinstance(latency, int | float), f"latency_ms must be a number, got {latency!r}"
        assert latency >= _SLOW_TOOL_FLOOR_MS, (
            f"a tool that slept {_SLOW_TOOL_SLEEP_S * 1000:.0f}ms recorded latency_ms="
            f"{latency} — the timer must span the delegated call, not a constant"
        )
        assert latency < _LATENCY_CEILING_MS, (
            f"latency_ms={latency} is implausible for a {_SLOW_TOOL_SLEEP_S:.2f}s sleep — "
            "this is a clock READING, not an elapsed duration"
        )

    async def test_a_fast_call_records_a_plausible_latency(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """CONTROL for the pin above: the fast leg must be BELOW the slow floor.

        Without this, a build hardcoding a large constant passes the slow pin. Two
        fixtures at different true durations are what make the measurement a
        measurement.
        """
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_OK)
        latency = recorder.one_row_for(PROBE_OK)[TRACE_LATENCY_MS]
        assert 0 <= latency < _SLOW_TOOL_FLOOR_MS, (
            f"an immediate tool recorded latency_ms={latency}, at or above the {_SLOW_TOOL_FLOOR_MS}ms "
            "floor the SLEEPING probe must clear — the two are indistinguishable, so the "
            "seam is not timing anything"
        )

    async def test_the_params_hash_is_stable_for_identical_arguments(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_ECHO, {"secret": _SECRET})
        await _call(mcp, recorder, PROBE_ECHO, {"secret": _SECRET})
        hashes = [row[TRACE_PARAMS_HASH] for row in recorder.rows_for(PROBE_ECHO)]
        assert len(hashes) == 2
        assert hashes[0] == hashes[1], (
            "params_hash must be a STABLE digest: identical arguments produced "
            f"{hashes[0]!r} then {hashes[1]!r}. An unstable digest (dict ordering, a "
            "nonce, an id()) makes every downstream grouping meaningless"
        )

    async def test_the_params_hash_discriminates_different_arguments(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """CONTROL: stability is worthless if the digest is a constant."""
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_ECHO, {"secret": _SECRET})
        await _call(mcp, recorder, PROBE_ECHO, {"secret": f"{_SECRET}-different"})
        hashes = [row[TRACE_PARAMS_HASH] for row in recorder.rows_for(PROBE_ECHO)]
        assert hashes[0] != hashes[1], (
            "different arguments produced the SAME params_hash — a constant passes the "
            "stability pin and tells you nothing"
        )

    async def test_argument_values_never_enter_the_trace_row(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """Private by construction (§S6v2 item 2): a HASH, never the arguments.

        What wrong build does this catch: one that stores ``repr(arguments)``
        alongside (or instead of) the digest. Once ``lore_comms send`` rides this
        seam, the arguments dict contains message BODIES — free text written by
        other agents — and a trace table is not where that belongs.
        """
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_ECHO, {"secret": _SECRET})
        row = recorder.one_row_for(PROBE_ECHO)
        serialised = json.dumps(row, default=str)
        assert _SECRET not in serialised, (
            "an argument VALUE appears verbatim in the trace row: "
            f"{[key for key, value in row.items() if _SECRET in str(value)]}. Arguments are "
            "hashed precisely so message bodies never enter the trace"
        )


# =========================================================================== #
# Section D — the request-scoped annotation channel (row H, annotation-leak leg)
# =========================================================================== #


class TestTheAnnotationChannel:
    """ONE writer (the seam) + ONE narrow, CLOSED-key enrichment helper (§S6v2 item 3).

    The design's shape is deliberate and this class pins each half of it: handlers
    never call ``record_trace`` (so there is no second writer to drift), and the
    one tool with domain knowledge contributes through a channel whose key set is
    DENY-BY-DEFAULT — the "allowlist the safe" side of the six-defeats lesson,
    rather than a name-keyed list of "tools allowed to self-record".
    """

    async def test_an_annotating_call_lands_its_domain_fields(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """POSITIVE CONTROL — without it, the leak pin below passes vacuously.

        "The second row was unannotated" proves nothing if NO row is ever
        annotated. This is the same self-caught trap the C1 audits recorded: a
        probe that passed for the wrong reason.
        """
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_ANNOTATE)
        row = recorder.one_row_for(PROBE_ANNOTATE)
        for key, expected in _PROBE_ANNOTATION.items():
            assert row.get(key) == expected, (
                f"annotation {key!r} did not reach the trace row: expected {expected!r}, "
                f"got {row.get(key)!r}"
            )

    async def test_annotations_do_not_leak_into_the_next_call(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """The annotation channel is REQUEST-SCOPED (a ContextVar reset by token).

        What wrong build does this catch: a module-level dict, or a ContextVar
        that is set but never reset. Both pass every single-call test and then
        stamp one drain's ``hit_count`` onto every subsequent ``lore_search`` —
        silently inflating exactly the numbers packet 06 will read.
        """
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_ANNOTATE)
        await _call(mcp, recorder, PROBE_PLAIN)
        leaked = {
            key: recorder.one_row_for(PROBE_PLAIN).get(key)
            for key in _ANNOTATION_KEYS
            if recorder.one_row_for(PROBE_PLAIN).get(key) is not None
        }
        assert not leaked, (
            f"a NON-annotating call inherited the previous call's annotations: {leaked}. "
            "The channel must be minted fresh per dispatch and reset in a finally"
        )

    async def test_annotations_do_not_leak_after_a_raising_call(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """The reset must live in a ``finally``, not on the success path.

        What wrong build does this catch: one that resets the ContextVar after the
        delegate returns. It passes the leak pin above (both calls succeed) and
        leaks forever after the first errored dispatch.
        """
        mcp, recorder = traced_server
        with pytest.raises(Exception):  # noqa: B017 - the raise is the fixture, not the pin
            await _call(mcp, recorder, PROBE_ANNOTATE_THEN_BOOM)
        annotated = recorder.one_row_for(PROBE_ANNOTATE_THEN_BOOM)
        assert annotated.get("hit_count") == _PROBE_ANNOTATION["hit_count"], (
            "a call that annotated and THEN raised lost its annotations; the row is written "
            "in a finally and must fold in whatever was contributed before the failure"
        )
        await _call(mcp, recorder, PROBE_PLAIN)
        leaked = {
            key: recorder.one_row_for(PROBE_PLAIN).get(key)
            for key in _ANNOTATION_KEYS
            if recorder.one_row_for(PROBE_PLAIN).get(key) is not None
        }
        assert not leaked, (
            f"annotations survived a RAISING dispatch and leaked into the next call: {leaked}. "
            "The channel reset belongs in the same finally as the write"
        )

    async def test_an_unknown_annotation_key_is_refused_loudly(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """Deny-by-default: an unknown key RAISES, naming itself and the legal set.

        ⚠ READING ESCALATED (report escalation E2). §S6v2 item 3 says "an unknown
        key RAISES (deny-by-default at the merge)". This contract pins the raise at
        the ANNOTATE CALL, not at the seam's merge, because the seam's failure
        posture (item 6) CATCHES telemetry errors and serves the result unmodified
        — so a merge-time raise would be swallowed into a log line, converting a
        deny-by-default guard into a silent no-op. That is the very defeat class
        the guard exists to avoid.
        """
        mcp, recorder = traced_server
        with pytest.raises(Exception) as rejection:
            await _call(mcp, recorder, PROBE_BAD_KEY)
        message = str(rejection.value)
        assert "bogus_key_03b" in message, (
            f"the refusal must NAME the offending key; got: {message!r}. An unnamed refusal "
            "sends the next engineer hunting"
        )
        assert any(key in message for key in _ANNOTATION_KEYS), (
            f"the refusal must name the LEGAL key set so the closed set is discoverable from "
            f"the failure alone; got: {message!r}"
        )

    async def test_a_refused_annotation_lands_none_of_its_keys(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """Refusal is ATOMIC — the legal half of a bad payload must not land.

        What wrong build does this catch: one that merges key-by-key and raises on
        reaching the bad one, leaving a half-applied annotation. The row would then
        carry a domain field from a call that FAILED its own validation — a number
        with no valid provenance, which is worse than a missing one.
        """
        mcp, recorder = traced_server
        with pytest.raises(Exception):  # noqa: B017 - covered by the pin above
            await _call(mcp, recorder, PROBE_BAD_KEY)
        row = recorder.one_row_for(PROBE_BAD_KEY)
        assert row.get(TRACE_AGENT) is None, (
            f"the LEGAL key of a refused annotation payload landed anyway "
            f"({TRACE_AGENT}={row.get(TRACE_AGENT)!r}); validation must precede any merge"
        )

    async def test_seam_owned_fields_cannot_be_annotated(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """A handler must not be able to forge ``tool``/``caller``/``seq``/timing.

        What wrong build does this catch: a channel that merges ANY key the seam
        also writes, letting a handler rewrite the very fields the coverage pin
        reads. Set equality over ``tool`` is only an invariant while ``tool`` is
        seam-owned.
        """
        mcp, recorder = traced_server
        with pytest.raises(Exception) as rejection:
            await _call(mcp, recorder, PROBE_SEAM_FORGE)
        assert any(field in str(rejection.value) for field in _SEAM_OWNED_FIELDS), (
            "annotating a SEAM-OWNED field must be refused naming it; got: "
            f"{str(rejection.value)!r}"
        )
        row = recorder.one_row_for(PROBE_SEAM_FORGE)
        assert row[TRACE_TOOL] == PROBE_SEAM_FORGE, (
            f"a handler forged the seam's own tool name: row says {row[TRACE_TOOL]!r}"
        )
        assert row.get(TRACE_CALLER) != "forged-caller", "a handler forged the caller key"


# =========================================================================== #
# Section E — S7 caller identity: the MEASUREMENT, the rule, and the outcome
# =========================================================================== #

_TRANSPORT_HOST = "127.0.0.1"
_TRANSPORT_PORT = 8765
_TRANSPORT_BASE = f"http://{_TRANSPORT_HOST}:{_TRANSPORT_PORT}"
_TRANSPORT_PATH = "/mcp"


def _asgi_client_factory(app: Any) -> Any:
    """An httpx client factory that speaks to ``app`` in-process (no socket).

    ⚠ The Host header MUST match the FastMCP instance's ``host:port`` — the SDK's
    DNS-rebinding middleware answers ``421 Misdirected Request`` otherwise, which
    surfaces as an opaque client error rather than "your base_url is wrong".
    Measured 2026-07-23 while settling the S7 fact below.
    """

    def factory(
        headers: dict[str, str] | None = None,
        timeout: Any = None,
        auth: Any = None,
    ) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url=_TRANSPORT_BASE,
            headers=headers,
            timeout=timeout,
            auth=auth,
        )

    return factory


async def _drive_one_mcp_session(app: Any, *, tool: str, calls: int) -> None:
    """Open ONE real streamable-http MCP session and call ``tool`` ``calls`` times."""
    async with streamablehttp_client(
        f"{_TRANSPORT_BASE}{_TRANSPORT_PATH}", httpx_client_factory=_asgi_client_factory(app)
    ) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as client:
            await client.initialize()
            for _ in range(calls):
                await client.call_tool(tool, {})


class TestTheS7RungSelectionFact:
    """The ONE fact §S7 could not settle read-only, converted into a live gate.

    §S7 designs TWO rungs for the caller key and states the decision rule:

      * **rung 1** — a server-minted uuid held in a ``WeakKeyDictionary`` keyed on
        the SDK's ``ServerSession`` OBJECT. Valid IFF that object is per-MCP-SESSION.
      * **rung 2 (fallback)** — the ``mcp-session-id`` header via
        ``request_context``. Same key semantics, streamable-http only, with the
        stdio gap documented.

    **MEASURED 2026-07-23 by this contract's author, ``mcp`` 1.27.2, in-process
    streamable-http against a real ``ClientSession``: the ``ServerSession`` object
    IS per-MCP-session** — identical ``id()`` across two calls (request_id 1 and 3)
    in one session, a different object in a second session, and the
    ``mcp-session-id`` header present and matching the client-visible session id in
    both. **Rung 1 is therefore SELECTED and the fallback is not needed.** The
    receipt lives in ``REPORT-contract-telemetry-03b.md`` §"S7 measurement".

    This test is the STANDING form of that measurement: it is GREEN today and goes
    RED the day the SDK (or a ``stateless_http=True`` flip) changes the fact — at
    which point the decision rule fires and the rung must be RE-SELECTED, not
    patched. That is why the fact is pinned separately from the outcome pins below:
    an outcome pin tells you the key broke; this one tells you WHY and what to do.
    """

    async def test_the_server_session_object_is_per_mcp_session(self) -> None:
        observed: list[dict[str, Any]] = []
        probe = FastMCP(
            name="s7-rung-probe",
            host=_TRANSPORT_HOST,
            port=_TRANSPORT_PORT,
            streamable_http_path=_TRANSPORT_PATH,
        )

        @probe.tool(name=PROBE_OK, description="Probe: records the session object identity.")
        async def _observe(context: Context[Any, Any, Any]) -> str:
            request_context = context.request_context
            observed.append(
                {
                    "session_id": id(request_context.session),
                    "request_id": request_context.request_id,
                    "header": (
                        request_context.request.headers.get("mcp-session-id")
                        if request_context.request is not None
                        else None
                    ),
                }
            )
            return "ok"

        app = probe.streamable_http_app()
        async with app.router.lifespan_context(app):
            await _drive_one_mcp_session(app, tool=PROBE_OK, calls=2)
            await _drive_one_mcp_session(app, tool=PROBE_OK, calls=1)

        assert len(observed) == 3, f"expected 3 observations, got {observed}"
        first, second, other_session = observed
        assert first["request_id"] != second["request_id"], (
            "the two same-session calls must be distinct REQUESTS, or this measures nothing"
        )
        assert first["session_id"] == second["session_id"], (
            "S7 DECISION RULE FIRED: the SDK now mints a ServerSession object PER REQUEST, "
            "so rung 1 (WeakKeyDictionary keyed on the session object) is INVALID — it would "
            "degenerate to a fresh key per call and every per-agent denominator would read 1. "
            "Switch to the designed fallback rung (the mcp-session-id header via "
            "request_context, streamable-http only, stdio gap documented). Do NOT patch the "
            "object-keyed implementation."
        )
        assert first["session_id"] != other_session["session_id"], (
            "CONTROL: two DIFFERENT MCP sessions shared one ServerSession object — the key "
            "would collide across agents and pool every caller into one"
        )
        assert first["header"] and first["header"] == second["header"], (
            "the fallback rung's input (the mcp-session-id header) must also be present and "
            "stable — if rung 1 ever fails there must be somewhere to fall back TO"
        )
        assert other_session["header"] != first["header"], (
            "CONTROL: the mcp-session-id header did not change across MCP sessions"
        )


class TestTheCallerKeyAtTheSeam:
    """The OUTCOME property, mechanism-agnostic: stable within a session, distinct across.

    Pinned at the seam (a synthetic session object) AND end-to-end over the real
    transport (below). Neither leg alone is sufficient and this contract says so:
    the seam leg cannot see a transport that hands out session objects
    differently, and the transport leg cannot cheaply cover the reconnect and
    multi-session shapes.
    """

    async def test_the_same_session_yields_the_same_caller_key(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        mcp, recorder = traced_server
        session = _SessionStandIn("agent-fixer-b")
        await _call(mcp, recorder, PROBE_OK, session=session, request_id=1)
        await _call(mcp, recorder, PROBE_PLAIN, session=session, request_id=2)
        callers = [row[TRACE_CALLER] for row in recorder.rows]
        assert len(callers) == 2, f"expected 2 traced calls, got {len(callers)}: {recorder.rows}"
        assert callers[0] == callers[1], (
            f"two calls in ONE session got different caller keys ({callers}). A build that "
            "mints a fresh key per call is indistinguishable from stateless degeneration, and "
            "makes every agent look like a one-call agent"
        )

    async def test_different_sessions_yield_different_caller_keys(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """CONTROL for the pin above: a CONSTANT key would pass stability trivially."""
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_OK, session=_SessionStandIn("agent-a"), request_id=1)
        await _call(mcp, recorder, PROBE_OK, session=_SessionStandIn("agent-b"), request_id=1)
        callers = [row[TRACE_CALLER] for row in recorder.rows]
        assert len(callers) == 2, f"expected 2 traced calls, got {len(callers)}: {recorder.rows}"
        assert callers[0] != callers[1], (
            f"two DIFFERENT sessions shared one caller key ({callers}). Every agent would pool "
            "into a single caller and the per-agent denominator would be meaningless — and a "
            "constant key passes the same-session pin"
        )

    async def test_the_caller_key_is_server_minted_not_caller_supplied(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """§S7: the key is server-minted, so it is trusted-charset BY CONSTRUCTION.

        What wrong build does this catch: one that keys on a client-declared value
        (``client_id``) or echoes caller text. Then the key is attacker-chosen,
        two agents can collide deliberately, and any future render of it inherits
        an injection surface the design explicitly closed.
        """
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_ECHO, {"secret": _SECRET}, session=_SessionStandIn("x"))
        caller = recorder.one_row_for(PROBE_ECHO)[TRACE_CALLER]
        assert isinstance(caller, str) and caller, f"caller must be a non-empty string, got {caller!r}"
        assert _SECRET not in caller, "the caller key echoes caller-supplied text"
        assert all(char.isalnum() or char in "-_" for char in caller), (
            f"caller key {caller!r} leaves the safe charset; a server-minted opaque id keeps "
            "the no-injection-surface property S7 relies on"
        )


class TestTheCallerKeyOverTheRealTransport:
    """END-TO-END over real streamable-http, per §S7 item 3's measurement clause.

    Uses ``TracingFastMCP`` directly (the ONE production name this file binds
    besides ``_annotate_trace``; both are prescribed by delta row G) with a probe
    lifespan, so the transport leg costs a few milliseconds instead of lore's full
    heavy startup. Everything else in this file reaches the seam through
    ``build_mcp_server``, so the production factory is never assumed to be wired.
    """

    @staticmethod
    def _probe_server(recorder: _RecordingStore) -> Any:
        import contextlib as _contextlib

        @_contextlib.asynccontextmanager
        async def _lifespan(_server: Any) -> AsyncIterator[Any]:
            yield SimpleNamespace(write_store=recorder)

        tracing_cls = _server_attr("TracingFastMCP")
        probe = tracing_cls(
            name="s7-transport-probe",
            host=_TRANSPORT_HOST,
            port=_TRANSPORT_PORT,
            streamable_http_path=_TRANSPORT_PATH,
            lifespan=_lifespan,
        )

        async def probe_ok() -> str:
            return "ok"

        probe.add_tool(probe_ok, name=PROBE_OK, description="Probe: returns successfully.")
        return probe

    async def test_one_session_two_calls_one_caller_key(self) -> None:
        recorder = _RecordingStore()
        app = self._probe_server(recorder).streamable_http_app()
        async with app.router.lifespan_context(app):
            await _drive_one_mcp_session(app, tool=PROBE_OK, calls=2)
        callers = [row[TRACE_CALLER] for row in recorder.rows]
        assert len(callers) == 2, f"expected 2 traced calls over the real transport, got {callers}"
        assert callers[0] == callers[1], (
            f"over the REAL streamable-http transport, two calls in one MCP session got "
            f"different caller keys ({callers}) — the seam-level pin passed and the real "
            "transport did not, which is the gap the test-environment-is-a-fiction law names"
        )

    async def test_two_sessions_two_caller_keys(self) -> None:
        """CONTROL: the transport leg must also be able to SEE a difference."""
        recorder = _RecordingStore()
        app = self._probe_server(recorder).streamable_http_app()
        async with app.router.lifespan_context(app):
            await _drive_one_mcp_session(app, tool=PROBE_OK, calls=1)
            await _drive_one_mcp_session(app, tool=PROBE_OK, calls=1)
        callers = [row[TRACE_CALLER] for row in recorder.rows]
        assert len(callers) == 2, f"expected 2 traced calls, got {callers}"
        assert callers[0] != callers[1], (
            f"two DIFFERENT MCP sessions over the real transport shared one caller key "
            f"({callers})"
        )


# =========================================================================== #
# Section F — the failure posture (§S6v2 item 6)
# =========================================================================== #


class TestTelemetryNeverBreaksTheCall:
    """Never fail a call for telemetry; never fail SILENTLY.

    §S6v2 item 6 rules the posture: the seam AWAITS the write, and on failure
    catches, logs loudly server-side, and returns the tool result UNMODIFIED.
    Fire-and-forget is REFUSED (it re-creates #147's silent zero), and mutating a
    tool's output is REFUSED (it would break every other tool's pinned render).
    """

    async def test_a_failing_trace_write_does_not_fail_the_tool_call(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """⚠ THE NON-VACUITY GUARD IS THE FIRST ASSERTION, DELIBERATELY.

        "The call succeeded while the store was broken" is TRUE of a build with no
        telemetry at all — this pin would green on the un-fixed tree, which is the
        fixture-that-cannot-discriminate class. So the healthy leg runs first and
        must prove the seam REACHES the store; only then does the broken leg mean
        anything.
        """
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_OK)
        assert recorder.rows_for(PROBE_OK), (
            "NON-VACUITY GUARD: a HEALTHY store received no write, so the broken-store leg "
            "below would pass on a build that has no telemetry seam at all"
        )
        broken = _RecordingStore(fail_with=RuntimeError("the store is down"))
        result = await _call(mcp, broken, PROBE_OK, app_context=SimpleNamespace(write_store=broken))
        assert result is not None, "a telemetry failure must never fail the tool call"

    async def test_a_failing_trace_write_does_not_modify_the_result(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """The seam serves the result UNMODIFIED — no notice line, no wrapper.

        What wrong build does this catch: v1's STRUCK drain-render telemetry-failure
        notice, resurrected. Comparing a healthy dispatch against a failing-store
        dispatch is the only way to see a difference a single-leg test cannot — and
        the healthy leg doubles as this pin's non-vacuity guard.
        """
        mcp, recorder = traced_server
        healthy = await _call(mcp, recorder, PROBE_OK)
        assert recorder.rows_for(PROBE_OK), (
            "NON-VACUITY GUARD: the healthy leg wrote no trace row, so 'the two results match' "
            "would be comparing two untraced calls"
        )
        broken = _RecordingStore(fail_with=RuntimeError("the store is down"))
        degraded = await _call(mcp, broken, PROBE_OK, app_context=SimpleNamespace(write_store=broken))
        assert str(degraded) == str(healthy), (
            "a telemetry failure changed the served result. The seam writes AFTER the handler "
            "returns and must never reach into any tool's output"
        )

    async def test_a_dispatch_without_a_request_context_still_serves(
        self, traced_server: tuple[Any, _RecordingStore]
    ) -> None:
        """No lifespan context ⇒ nowhere to write ⇒ still serve, never crash.

        ``FastMCP.get_context()`` tolerates a missing request context and hands back
        a ``Context`` whose ``request_context`` is ``None``. A seam that dereferences
        it unguarded turns an untraceable call into a 500 — and lore's own eager
        ASGI startup path dispatches outside a session.

        Same discipline as its siblings: the WITH-context leg runs first, so this
        cannot green on a tree that has no seam.
        """
        mcp, recorder = traced_server
        await _call(mcp, recorder, PROBE_OK)
        assert recorder.rows_for(PROBE_OK), (
            "NON-VACUITY GUARD: with a request context present the seam wrote nothing, so the "
            "without-context leg below proves nothing"
        )
        assert await mcp.call_tool(PROBE_OK, {}) is not None, (
            "a dispatch with NO request context must still serve its result — the seam has "
            "nowhere to write, which is a reason to skip the row, never to fail the call"
        )


# =========================================================================== #
# Section G — the [real] leg: a real drain writes a fully enriched row
# =========================================================================== #


def _msg_fakes() -> Any:
    """The packet-03 message fake, imported at CALL time (see the module docstring)."""
    import _message_fakes

    return _message_fakes


def _comms_double(*, write_store: Any) -> Any:
    """An ``AppContext``-shaped double carrying a REAL write_store + fake ledgers.

    The composition is deliberate: the TRACE side is real (a live SurrealStore on a
    virgin test database, so the row is read back with a real ``SELECT``), while the
    comms LEDGERS are the already-built adversarial fakes — their contract is
    ``test_message_ledger.py``'s, not this file's. Extends ``test_comms_tool.py``'s
    ``_harness`` shape with the two attributes a traced dispatch needs:
    ``write_store`` and a bound ``comms``.
    """
    double = SimpleNamespace(
        write_store=write_store,
        agent_registry=FakeAgentRegistry(db=FakeAgentDatabase()),
        brief_ledger=FakeBriefLedger(db=FakeBriefDatabase()),
        message_ledger=_msg_fakes().FakeMessageLedger(db=_msg_fakes().FakeMessageDatabase()),
        config=SimpleNamespace(
            comms=SimpleNamespace(
                stale_heartbeat_s=600,
                fleet_limit=20,
                drain_limit=20,
                brief_body_warn_chars=4000,
            )
        ),
    )
    # ``AppContext.comms`` is called UNBOUND against the double (test_comms_tool.py's
    # ``_harness`` stance): the dispatcher's own contract is what is under test, not the
    # write stack a fully-built AppContext drags in. The cast tells mypy what the double
    # satisfies structurally — it is a harness-typing artifact, NOT a forward reference,
    # so it is silenced here rather than left for row F to pay.
    double.comms = functools.partial(AppContext.comms, cast(AppContext, double))
    return double


# The drain fixture's numbers are DELIBERATELY pairwise-distinct so no two fields
# can be confused: 5 pending, 2 served, limit 2. A fixture where served == pending
# (the natural "seed 2, drain 2") could not tell ``hit_count`` from ``pending``.
_DRAIN_SEEDED = 5
_DRAIN_LIMIT = 2
_DRAIN_AGENT = "fixer-b"
_DRAIN_SENDER = "lead"
_DRAIN_SESSION = "wave7"


async def _seed_inbox(double: Any) -> str:
    """Register two agents, then send ``_DRAIN_SEEDED`` messages to the drainer.

    Returns:
        The resolved agent RecordID string the annotation must carry.
    """
    ledger = double.message_ledger
    recipient_id = FakeAgentRegistry._agent_id(_DRAIN_SESSION, _DRAIN_AGENT)  # noqa: SLF001
    sender_id = FakeAgentRegistry._agent_id(_DRAIN_SESSION, _DRAIN_SENDER)  # noqa: SLF001
    await double.comms(action="register", agent=_DRAIN_AGENT, session=_DRAIN_SESSION, role="builder")
    await double.comms(action="register", agent=_DRAIN_SENDER, session=_DRAIN_SESSION, role="lead")
    ledger.register_agent(agent_id=recipient_id, name=_DRAIN_AGENT)
    ledger.register_agent(agent_id=sender_id, name=_DRAIN_SENDER)
    sender = SimpleNamespace(id=sender_id, name=_DRAIN_SENDER)
    recipient = SimpleNamespace(id=recipient_id, name=_DRAIN_AGENT)
    for index in range(_DRAIN_SEEDED):
        await ledger.send(
            sender=sender,
            session=_DRAIN_SESSION,
            body=f"wave 3 item {index} — receipts in the archived wave report",
            grade="directive" if index == 0 else "signal",
            recipients=[recipient],
        )
    return recipient_id


@pytest_asyncio.fixture()
async def live_trace_store() -> AsyncIterator[SurrealStore]:
    """A REAL :class:`SurrealStore` on a virgin throwaway database (TEST store only).

    ``unique_database()`` mints ``test_<pid>_<uuid4>`` precisely so a concurrent
    pytest process never collides on or reaps this database — which is what makes
    ``-n auto`` safe here.
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


# ⚠ EXPLICIT PROJECTION, NOT ``SELECT *`` — and the difference is load-bearing.
# ``SELECT *`` OMITS a column whose value is NONE, so ``row["session"]`` raises
# ``KeyError`` on exactly the generic rows this contract is about, and a pin
# asserting "session is None" dies on a harness error instead of reporting its
# finding. An EXPLICIT projection reads a NONE-valued (or absent) column back as
# ``None`` (store reference §2), so every row has a uniform shape.
# ⚠ The same section names the price: a typo'd projection degrades SILENTLY into a
# null. That is acceptable here BECAUSE the assertions are two-sided — §G and §H
# demand ``caller``/``seq``/``agent`` be PRESENT, so a projection that silently
# nulled them would go RED, not green.
_TRACE_PROJECTION = ", ".join(
    (
        TRACE_TOOL,
        TRACE_PARAMS_HASH,
        TRACE_HIT_COUNT,
        TRACE_LATENCY_MS,
        TRACE_SESSION,
        TRACE_CALLER,
        TRACE_SEQ,
        TRACE_AGENT,
        TRACE_PENDING,
        TRACE_PEEKED,
        "ts",
    )
)


async def _live_rows(store: SurrealStore) -> list[dict[str, Any]]:
    """Every persisted trace row, ordered by the mint (the store has no read API).

    P8a shipped the write path only; the aggregate is per-tool. Reading through
    the store's private ``_query`` is a TEST introspection, the same stance
    ``test_surreal_store.py::_recorded_traces`` records.
    """
    raw = await store._query(  # noqa: SLF001
        f"SELECT {_TRACE_PROJECTION} FROM {TRACE_TABLE} ORDER BY {TRACE_SEQ}"
    )
    return [row for row in raw if isinstance(row, dict)] if isinstance(raw, list) else []


class TestARealDrainWritesAnEnrichedRow:
    """The ``[real]``-leg row pin (row H): a comms drain, through the real seam,
    landing ONE row in a REAL store with every enrichment field present and correct.

    This is the leg that proves the annotation channel and the seam compose against
    the actual schema rather than against a double that would accept anything.
    """

    async def test_a_drain_lands_every_enrichment_field(
        self, traced_server: tuple[Any, _RecordingStore], live_trace_store: SurrealStore
    ) -> None:
        mcp, _recorder = traced_server
        double = _comms_double(write_store=live_trace_store)
        agent_id = await _seed_inbox(double)

        await _call(
            mcp,
            _RecordingStore(),
            "lore_comms",
            {
                "action": "drain",
                "agent": _DRAIN_AGENT,
                "session": _DRAIN_SESSION,
                "limit": _DRAIN_LIMIT,
            },
            app_context=double,
        )

        rows = [row for row in await _live_rows(live_trace_store) if row[TRACE_TOOL] == "lore_comms"]
        assert len(rows) == 1, f"expected exactly one lore_comms trace row, got {len(rows)}"
        row = rows[0]
        assert row[TRACE_HIT_COUNT] == _DRAIN_LIMIT, (
            f"hit_count must be the SERVED count ({_DRAIN_LIMIT}), got {row[TRACE_HIT_COUNT]} — "
            f"a build writing total_pending here would read {_DRAIN_SEEDED}"
        )
        assert row[TRACE_PENDING] == _DRAIN_SEEDED, (
            f"pending must be total_pending ({_DRAIN_SEEDED}), got {row[TRACE_PENDING]}"
        )
        assert row[TRACE_PEEKED] is False, (
            f"a STAMPING drain must record peeked=False, got {row[TRACE_PEEKED]!r}"
        )
        assert row[TRACE_AGENT] == agent_id, (
            f"agent must be the RESOLVED agent RecordID {agent_id!r}, got {row[TRACE_AGENT]!r} — "
            "the caller-supplied name is not the identity the join needs"
        )
        assert row[TRACE_SESSION] == _DRAIN_SESSION, (
            f"session must be the EXPLICIT fleet session, got {row[TRACE_SESSION]!r}. Per S7 the "
            "caller key NEVER goes here — trace.session stays the documented fleet identity"
        )
        assert row[TRACE_CALLER] and row[TRACE_CALLER] != _DRAIN_SESSION, (
            "caller must be the transport-session key, kept SEPARATE from the fleet session "
            "(S7's no-overloading rule); the two are joined by data, never by one column"
        )
        assert isinstance(row[TRACE_SEQ], int), f"seq must be an int, got {row[TRACE_SEQ]!r}"

    async def test_a_peek_records_peeked_true(
        self, traced_server: tuple[Any, _RecordingStore], live_trace_store: SurrealStore
    ) -> None:
        """CONTROL: ``peeked`` must DISCRIMINATE, not be a constant False.

        A build hardcoding ``peeked=False`` passes the drain pin above. Packet 06
        must be able to separate a peek from a stamping pull — they are different
        behaviours and only one discharges the inbox.
        """
        mcp, _recorder = traced_server
        double = _comms_double(write_store=live_trace_store)
        await _seed_inbox(double)

        await _call(
            mcp,
            _RecordingStore(),
            "lore_comms",
            {
                "action": "drain",
                "agent": _DRAIN_AGENT,
                "session": _DRAIN_SESSION,
                "limit": _DRAIN_LIMIT,
                "peek": True,
            },
            app_context=double,
        )
        rows = [row for row in await _live_rows(live_trace_store) if row[TRACE_TOOL] == "lore_comms"]
        assert len(rows) == 1, f"expected exactly one lore_comms trace row, got {len(rows)}"
        assert rows[0][TRACE_PEEKED] is True, (
            f"a PEEK must record peeked=True, got {rows[0][TRACE_PEEKED]!r} — a constant here "
            "makes the flag decoration"
        )

    async def test_a_generic_tool_leaves_the_comms_columns_empty(
        self, traced_server: tuple[Any, _RecordingStore], live_trace_store: SurrealStore
    ) -> None:
        """The honest-unknown leg (§S6v2 item 5): a generic call records NONE.

        What wrong build does this catch: one that derives a "content block count"
        proxy for ``hit_count`` on generic calls — explicitly REFUSED as a lying
        metric. A stored 0 and an honest NONE are different claims.
        """
        mcp, _recorder = traced_server
        await _call(
            mcp,
            _RecordingStore(),
            PROBE_OK,
            app_context=SimpleNamespace(write_store=live_trace_store),
        )
        rows = [row for row in await _live_rows(live_trace_store) if row[TRACE_TOOL] == PROBE_OK]
        assert len(rows) == 1, f"expected one generic trace row, got {len(rows)}"
        row = rows[0]
        for column in (TRACE_HIT_COUNT, TRACE_SESSION, TRACE_AGENT, TRACE_PENDING, TRACE_PEEKED):
            assert row.get(column) is None, (
                f"a generic (non-comms) call recorded {column}={row.get(column)!r}; the honest "
                "value is NONE — a fabricated proxy is a metric that lies"
            )
        assert row[TRACE_CALLER], "caller is seam-written on EVERY row, generic calls included"


# =========================================================================== #
# Section H — ``seq`` is minted STORE-SIDE by one global native sequence
# =========================================================================== #


class TestSeqIsMintedByTheStore:
    """§S6v2 item 4: ``sequence::nextval("trace_seq")`` INSIDE ``record_trace``'s CREATE,
    "so every writer mints by construction, no drift possible".

    This is the #102 clone terrain: a seam-side counter would be a THIRD mint
    policy beside ``finding_counter`` / ``brief_counter``, and the first divergence
    would be invisible. The pins below prove the mint lives in the store, not in
    any caller — by SIGNATURE (no ``seq`` parameter to supply) and by BEHAVIOUR
    (two independent store objects share one counter).
    """

    def test_record_trace_takes_no_seq_parameter(self) -> None:
        """The structural half: a caller cannot supply ``seq``, so no caller can drift.

        What wrong build does this catch: one that keeps ``record_trace`` dumb and
        mints the ordinal in the seam. Every other pin in this file would pass —
        the rows would carry increasing seqs — while a second writer (packet 06's
        analysis tooling, a backfill script) would silently mint its own series.
        """
        parameters = inspect.signature(SurrealStore.record_trace).parameters
        assert TRACE_SEQ not in parameters, (
            f"record_trace exposes a {TRACE_SEQ!r} parameter ({list(parameters)}), so the mint "
            "lives in its CALLERS. One global native sequence inside the CREATE is the ruled "
            "shape precisely so a second writer cannot start a competing series"
        )
        for column in (TRACE_CALLER, TRACE_AGENT, TRACE_PENDING, TRACE_PEEKED):
            assert column in parameters, (
                f"record_trace has no {column!r} parameter ({list(parameters)}) — delta row F's "
                "new columns are unreachable from the write path"
            )

    async def test_two_writes_get_distinct_increasing_seqs(
        self, live_trace_store: SurrealStore
    ) -> None:
        await live_trace_store.record_trace(
            tool="lore_search", params_hash="a" * 8, latency_ms=1.5, caller="c-1"
        )
        await live_trace_store.record_trace(
            tool="lore_read", params_hash="b" * 8, latency_ms=2.5, caller="c-1"
        )
        seqs = [row[TRACE_SEQ] for row in await _live_rows(live_trace_store)]
        assert len(seqs) == 2, f"expected 2 rows, got {len(seqs)}"
        assert seqs[0] < seqs[1], f"seq must increase across writes, got {seqs}"

    async def test_two_store_objects_share_one_sequence(
        self, live_trace_store: SurrealStore
    ) -> None:
        """The mint is GLOBAL and store-side, not per-process or per-connection.

        What wrong build does this catch: an in-process counter (a module global,
        an instance attribute). It yields increasing, distinct seqs on ONE object
        and duplicate series the moment a second connection writes — and lore runs
        one connection per session.
        """
        second = SurrealStore(
            url=live_trace_store._url,  # noqa: SLF001 - test introspection, mirrors the harness idiom
            namespace=live_trace_store._namespace,  # noqa: SLF001
            database=live_trace_store._database,  # noqa: SLF001
            dim=PRODUCTION_DIM,
            user=live_trace_store._user,  # noqa: SLF001
            password=live_trace_store._password,  # noqa: SLF001
        )
        await second.ensure_ready()
        try:
            await live_trace_store.record_trace(
                tool="lore_search", params_hash="a" * 8, latency_ms=1.0, caller="c-1"
            )
            await second.record_trace(
                tool="lore_search", params_hash="a" * 8, latency_ms=1.0, caller="c-2"
            )
        finally:
            await second.close()
        seqs = [row[TRACE_SEQ] for row in await _live_rows(live_trace_store)]
        assert len(set(seqs)) == 2, (
            f"two independent store objects minted the SAME seq ({seqs}) — the counter is "
            "per-object, not the store's one global sequence"
        )

    async def test_eight_concurrent_writers_mint_eight_distinct_seqs(
        self, live_trace_store: SurrealStore
    ) -> None:
        """Contention leg at the repo's ≥8-way floor (never 2-way).

        Store reference §5 documents ``sequence::nextval`` as contention-free (3200
        calls, 100% distinct), so this is a re-certification against OUR write
        shape, not a rediscovery. A single green run never clears a concurrency
        test — the exit receipt requires 20 consecutive.
        """

        async def write(index: int) -> None:
            await live_trace_store.record_trace(
                tool=f"probe_concurrent_{index}",
                params_hash=f"{index:08d}",
                latency_ms=float(index),
                caller=f"c-{index}",
            )

        await asyncio.gather(*(write(index) for index in range(_CONCURRENT_SEQ_WRITERS)))
        seqs = [row[TRACE_SEQ] for row in await _live_rows(live_trace_store)]
        assert len(seqs) == _CONCURRENT_SEQ_WRITERS, (
            f"expected {_CONCURRENT_SEQ_WRITERS} rows under {_CONCURRENT_SEQ_WRITERS}-way "
            f"concurrency, got {len(seqs)} — rows were LOST, not merely reordered"
        )
        assert len(set(seqs)) == _CONCURRENT_SEQ_WRITERS, (
            f"{_CONCURRENT_SEQ_WRITERS - len(set(seqs))} duplicate seqs under concurrency: {seqs}"
        )


# =========================================================================== #
# Section I — the schema change itself (delta row F), including the DIRTY store
# =========================================================================== #

# The trace table AS IT EXISTS ON THE PRODUCTION STORE TODAY — eight columns,
# ``session`` and ``hit_count`` REQUIRED. Scout-probed read-only on :18500,
# 2026-07-24: the table is DEFINED and holds count() = 0. Written out verbatim
# because the migration pin below needs an OLD world to migrate FROM, and the new
# emitter can no longer produce one.
_OLD_TRACE_DDL: tuple[str, ...] = (
    f"DEFINE TABLE IF NOT EXISTS {TRACE_TABLE} SCHEMAFULL",
    f"DEFINE FIELD OVERWRITE {TRACE_TOOL} ON {TRACE_TABLE} TYPE string",
    f"DEFINE FIELD OVERWRITE {TRACE_PARAMS_HASH} ON {TRACE_TABLE} TYPE string",
    f"DEFINE FIELD OVERWRITE {TRACE_HIT_COUNT} ON {TRACE_TABLE} TYPE int",
    f"DEFINE FIELD OVERWRITE {TRACE_LATENCY_MS} ON {TRACE_TABLE} TYPE number",
    f"DEFINE FIELD OVERWRITE {TRACE_SESSION} ON {TRACE_TABLE} TYPE string",
    f"DEFINE FIELD OVERWRITE ts ON {TRACE_TABLE} TYPE datetime DEFAULT time::now()",
    f"DEFINE FIELD OVERWRITE token_cost ON {TRACE_TABLE} TYPE option<int>",
    f"DEFINE FIELD OVERWRITE model ON {TRACE_TABLE} TYPE option<string>",
)


class TestTheTraceSchemaDelta:
    """Delta row F, pinned BEHAVIOURALLY — what the store accepts, not what a spec tuple says.

    Store law governs every item here: fields migrate with ``DEFINE FIELD
    OVERWRITE`` (§1.1; ``IF NOT EXISTS`` is a silent no-op and caused #107),
    indexes and sequences stay ``IF NOT EXISTS`` (flipping them is the boot-crash
    direction), and a schema change converges the SCHEMA but never the DATA (§1.4).
    """

    async def test_a_generic_row_may_omit_session_and_hit_count(
        self, live_trace_store: SurrealStore
    ) -> None:
        """The LOOSENING half of row F: generic calls carry neither.

        What wrong build does this catch: a builder who adds the five new columns
        and forgets that ``session``/``hit_count`` are still REQUIRED — every
        generic trace write then raises, the seam catches it, logs, and serves on,
        and ``traces.total`` stays at 0 forever with every gate green. That is
        #147, reproduced inside its own fix.
        """
        await live_trace_store.record_trace(
            tool="lore_search", params_hash="c" * 8, latency_ms=3.25, caller="c-1"
        )
        rows = await _live_rows(live_trace_store)
        assert len(rows) == 1, f"the generic write did not land: {rows}"
        assert rows[0][TRACE_SESSION] is None, (
            f"session must store NONE for a generic call, got {rows[0][TRACE_SESSION]!r}"
        )
        assert rows[0][TRACE_HIT_COUNT] is None, (
            f"hit_count must store NONE for a generic call, got {rows[0][TRACE_HIT_COUNT]!r}"
        )

    async def test_the_new_columns_land_on_an_ALREADY_EXISTING_trace_table(self) -> None:
        """THE #107 PIN. Every other test in this file mints a VIRGIN database.

        A clean-slate fixture structurally cannot see a migration defect — that is
        why 1040 tests, a cold audit and a contract-adversary all passed #107 while
        ``brief_publish`` was 100% down in production (store reference §1.6). Every
        long-lived deployment is a DIRTY store. So: apply the OLD trace DDL, DIRTY
        it with a row that is legal only under the old world, then apply the
        PRODUCTION emitter's DDL and demand (a) the loosening actually landed and
        (b) the pre-existing row survived.

        ⚠ KNOWN BOUND, recorded rather than closed: ``seq`` ships NON-``option``
        (§S6v2 item 5), so an existing row that predates it is left WRITE-POISONED
        per store reference §1.4 — readable, but rejected on any future UPDATE.
        That is acceptable here for a reason with a receipt, not by assumption:
        trace rows are append-only (``record_trace``'s docstring: "a trace is an
        append-only event, never keyed/deduped") and production holds ZERO of them
        (scout-probed :18500, 2026-07-24). Re-open trigger: the day anything
        UPDATEs a trace row, or any store carries pre-03b trace rows.
        """
        import loremaster.store.surreal_schema as schema_module

        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        connection = await connect_admin(env)
        try:
            for statement in _OLD_TRACE_DDL:
                await run(connection, statement)
            legacy_stamp = datetime.now(UTC)
            await run(
                connection,
                f"CREATE {TRACE_TABLE}:legacy CONTENT $content",
                {
                    "content": {
                        TRACE_TOOL: "lore_search",
                        TRACE_PARAMS_HASH: "d" * 8,
                        TRACE_HIT_COUNT: 3,
                        TRACE_LATENCY_MS: 12.5,
                        TRACE_SESSION: "pre-03b-session",
                        "ts": legacy_stamp,
                    }
                },
            )

            # The NEW world, through the PRODUCTION emitter — never hand-rolled DDL.
            for statement in schema_module._trace_statements():  # noqa: SLF001
                await run(connection, statement)

            # (a) The loosening LANDED: a row with no session / no hit_count is now legal.
            #     Under the old definition this raises; that is the whole #107 shape.
            await run(
                connection,
                f"CREATE {TRACE_TABLE}:migrated CONTENT $content",
                {
                    "content": {
                        TRACE_TOOL: "lore_read",
                        TRACE_PARAMS_HASH: "e" * 8,
                        TRACE_LATENCY_MS: 4.0,
                        TRACE_CALLER: "c-migrated",
                        TRACE_SEQ: 1,
                    }
                },
            )
            # Explicit projection — see ``_TRACE_PROJECTION``: ``SELECT *`` omits a
            # NONE column, which is precisely the value under test here.
            migrated = await run(
                connection, f"SELECT {_TRACE_PROJECTION} FROM {TRACE_TABLE}:migrated"
            )
            assert migrated and migrated[0][TRACE_SESSION] is None, (
                "the session loosening did not land on the EXISTING table — DEFINE FIELD "
                "IF NOT EXISTS is a silent no-op on an existing field (store reference §1.1 / "
                "#107); fields MUST use OVERWRITE"
            )

            # (b) The pre-existing row SURVIVED — readable, not rewritten, not dropped.
            legacy = await run(
                connection, f"SELECT {_TRACE_PROJECTION} FROM {TRACE_TABLE}:legacy"
            )
            assert legacy and legacy[0][TRACE_SESSION] == "pre-03b-session", (
                "the pre-existing row did not survive the migration; §1.4 says old rows are "
                "left intact and readable — anything else is data loss"
            )
        finally:
            await connection.close()
            await drop_database(env)

    async def test_the_trace_ddl_uses_the_ruled_guards(self) -> None:
        """Guard-kind pin: fields ``OVERWRITE``; table / index / sequence ``IF NOT EXISTS``.

        Not style. Flipping an INDEX to ``OVERWRITE`` re-indexes every row at every
        boot and HARD-FAILS ``ensure_ready`` on a dimension change; a bare ``DEFINE
        SEQUENCE`` RAISES on the re-apply every boot performs. Both are boot-time
        crashes, and both are one word away.
        """
        import loremaster.store.surreal_schema as schema_module

        statements = schema_module._trace_statements()  # noqa: SLF001
        for statement in statements:
            if statement.startswith("DEFINE FIELD"):
                assert "OVERWRITE" in statement, (
                    f"field DDL must be OVERWRITE (store reference §1.1 / #107): {statement}"
                )
            elif statement.startswith(("DEFINE TABLE", "DEFINE INDEX", "DEFINE SEQUENCE")):
                assert "IF NOT EXISTS" in statement, (
                    f"table/index/sequence DDL must be IF NOT EXISTS — OVERWRITE on an index "
                    f"rebuilds at boot and a bare DEFINE SEQUENCE raises: {statement}"
                )
        joined = "\n".join(statements)
        assert "DEFINE SEQUENCE IF NOT EXISTS trace_seq" in joined, (
            "the trace sequence (§S6v2 item 4) is not declared; without it every CREATE that "
            f"calls sequence::nextval fails. Statements: {statements}"
        )
        assert "trace_caller_seq" in joined, (
            "the (caller, seq) index (§S6v2 item 5) is not declared. Its free window is NOW — "
            "the prod table is empty today; the same line shipped later builds over months of "
            "all-tools rows at boot (store reference §1.5)"
        )
        assert "BATCH" not in joined and "START" not in joined, (
            "the sequence must carry neither BATCH nor START — a changed one never migrates "
            "onto an existing store (#146), so setting either creates a permanent divergence"
        )


# =========================================================================== #
# Section J — the DEPLOY SMOKE assertion (row H, artifact leg)
# =========================================================================== #

DEPLOY_SMOKE_MIN_TRACES = 2
DEPLOY_SMOKE_REQUIRED_TOOLS: tuple[str, ...] = ("lore_comms", "lore_search")


def assert_deploy_smoke_traces(traces: Mapping[str, Any]) -> None:
    """Assert the 03b deploy smoke over ``lore_index``'s served ``traces`` block.

    THE LEAD RUNS THIS, against the DEPLOYED artifact, after one live drain and one
    live search::

        from test_trace_telemetry import assert_deploy_smoke_traces
        assert_deploy_smoke_traces(lore_index_payload["traces"])

    **Why this leg is not optional.** Pinning the source proves the RECIPE; only the
    running artifact proves the CAKE. Both of this repo's worst outages lived in the
    gap between the dev host and the container: #107 (a widened ASSERT that never
    migrated — 1040 tests green, a cold audit GO, a passing adversary, and
    ``brief_publish`` 100% down) and #131 (the image had no ``git``; the OSError was
    swallowed into a silent ``(None, None)`` for months). In both, the deploy smoke
    was the only instrument that caught it. And #147 — the defect this packet fixes —
    is itself that shape: a status surface reporting a field nobody consumed.

    It is written as a FUNCTION rather than prose because a procedure in a report
    drifts and cannot be mutation-proven, while this one has its own controls
    (:class:`TestTheDeploySmokeAssertionDiscriminates`). It opens no connection: the
    payload comes from the lead's live ``lore_index`` call, so PRODUCTION ``:18500``
    is never touched by the suite.

    Args:
        traces: The ``traces`` block of a live ``lore_index`` response — a mapping
            with ``total`` and ``by_tool`` (a list of ``{tool, calls}``).

    Raises:
        AssertionError: The artifact is not recording, or is recording only the
            comms leg (which would leave generic coverage unproven).
    """
    total = traces.get("total")
    by_tool_raw = traces.get("by_tool") or []
    by_tool = {
        str(entry.get("tool")): entry.get("calls")
        for entry in by_tool_raw
        if isinstance(entry, Mapping)
    }
    assert isinstance(total, int) and total >= DEPLOY_SMOKE_MIN_TRACES, (
        f"the DEPLOYED artifact served traces.total={total!r}, below the {DEPLOY_SMOKE_MIN_TRACES} "
        "a live drain plus a live search must produce. The source may be perfect; this says the "
        "ARTIFACT is not recording (#147's own shape, and #107/#131's gap)"
    )
    missing = [tool for tool in DEPLOY_SMOKE_REQUIRED_TOOLS if tool not in by_tool]
    assert not missing, (
        f"traces.by_tool is missing {missing} (saw {sorted(by_tool)}). BOTH tools are required: "
        "lore_comms alone would prove only the comms leg, leaving the all-tools seam — the whole "
        "point of the operator's scope widening — unproven in the artifact"
    )


class TestTheDeploySmokeAssertionDiscriminates:
    """Controls for the smoke assertion: it must accept a good payload, and reject
    two DIFFERENTLY-broken ones for DIFFERENT reasons.

    "The bad input was rejected" is worthless until the good input is shown
    accepted and a differently-broken input is shown rejected for a different
    cause — otherwise the probe may be failing on a parse error and would
    green-light the case it exists to catch.
    """

    @staticmethod
    def _payload(total: int, tools: Sequence[str]) -> dict[str, Any]:
        return {
            "total": total,
            "by_tool": [{"tool": tool, "calls": 1} for tool in tools],
            "latest_at": "2026-07-24T00:00:00Z",
        }

    def test_a_live_artifact_payload_passes(self) -> None:
        assert_deploy_smoke_traces(self._payload(2, DEPLOY_SMOKE_REQUIRED_TOOLS))

    def test_a_silent_artifact_fails_on_the_total(self) -> None:
        with pytest.raises(AssertionError) as rejection:
            assert_deploy_smoke_traces(self._payload(0, ()))
        assert "traces.total" in str(rejection.value)

    def test_a_comms_only_artifact_fails_for_a_DIFFERENT_reason(self) -> None:
        with pytest.raises(AssertionError) as rejection:
            assert_deploy_smoke_traces(self._payload(2, ("lore_comms", "lore_comms")))
        message = str(rejection.value)
        assert "by_tool" in message and "lore_search" in message, (
            f"a comms-only artifact must be rejected for the MISSING-TOOL reason, not the total "
            f"reason; got: {message!r}"
        )

    def test_an_empty_payload_fails_rather_than_passing_vacuously(self) -> None:
        with pytest.raises(AssertionError):
            assert_deploy_smoke_traces({})
