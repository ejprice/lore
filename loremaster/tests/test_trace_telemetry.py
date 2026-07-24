"""Contract tests for the ALL-TOOLS trace telemetry seam (packet 03b, section B).

**Spec (execute verbatim; a genuine gap is a STOP-and-flag, never an improvised
design decision):** ``docs/plans/v2/03b-design-rulings-r2.md`` section B — T1 (the
``FastMCP.call_tool`` subclass-override seam), T2 + T2.1 (the all-``option<>``
schema delta, the ``trace_seq`` native sequence, the 06-read
``(agent, ordinal)`` index), T3 (the one global ordinal), T4 (declared-only
identity + the transport correlator), T5 (emission shape and failure posture),
T6 (``params_hash``), T7 (the pin battery this file IS), T8 (the read surface and
``record_trace`` compatibility). The contract-phase disciplines T7.10–T7.13 are
derived in ``docs/plans/v2/receipts/2026-07-24-packet03b/DIFF-adjudication-03b.md``
sections 3 (AC-05 · AC-06 · AC-12 · AC-13 · AC-15 · AC-17 · AC-18).

**WHY this instrument exists (the load-bearing rationale, so a later reader does
not "simplify" it):** decay is an ABSENCE of drains across increasing tool calls,
and an absence writes no rows — so a drain-only ordinal is a numerator with no
denominator. Packet 06 must decide forced-drain on a MEASURED curve. Every pin
below serves that measurement, which is why coverage is asserted as a CHECKED
VARIABLE (set-equality against the server's own registered surface) rather than
as a list of tool names somebody remembered to update.

RED, NEVER UNCOLLECTABLE
------------------------
None of the telemetry production symbols exists at contract-authoring time
(HEAD ``e7db965``, 2026-07-24): ``server.TracingFastMCP`` is absent,
``SurrealStore.record_trace`` still carries the committed seven-parameter
signature, and ``_TRACE_FIELD_SPECS`` carries neither the widened types nor the
five new columns. Every test here must therefore fail for ITS OWN reason — a
missing production symbol or behaviour — and never at COLLECTION. That is why
the unbuilt surface is reached through the call-time accessors below
(:func:`_tracing_subclass`) and through deliberately ``Any``-typed call sites
(:func:`_record_trace`): a module-level ``from loremaster.server import
TracingFastMCP`` would make this whole file uncollectable, which is a DIFFERENT
state from red — an uncollectable module never runs, and its pins stop being
counted (finding #133).

The ``Any`` typing at those two seams is deliberate and temporary: mypy cannot
see a signature that does not exist yet, so a statically-typed call site would
add mypy errors that no builder can pay except by existing. The RED these pins
serve is the RUNTIME ``TypeError``/``AssertionError``, which names exactly what
is missing.

HARNESS: WHAT IS REAL AND WHAT IS A DOUBLE (and why the double cannot lie)
-------------------------------------------------------------------------
* The SERVER is real: every seam pin builds it through the production
  ``build_mcp_server(LoreServer(config))`` and dispatches through the production
  entry point ``FastMCP.call_tool`` (plus one leg through the LOWLEVEL wire
  handler FastMCP registers at ``__init__`` — the path production actually uses).
  Nothing connects to a store during registration (mirrors
  ``test_mcp_server.py``'s ``TestToolRegistration``).
* The APP CONTEXT is a double carrying exactly one attribute — ``write_store`` —
  because that is the only thing the emission needs. It is delivered through the
  request-scoped lifespan context (``mcp.server.lowlevel.server.request_ctx``),
  which is the SAME channel every registered tool wrapper reads
  (``AppContext`` off ``context.request_context.lifespan_context``). That is not
  an arbitrary harness choice: ``build_mcp_server`` constructs the ``FastMCP``
  instance BEFORE any ``AppContext`` exists (the ``_ProcessLifespanGuard`` builds
  the context lazily, on the first session), so a store cannot be injected at
  construction time — the per-request lifespan context is the only channel by
  which the emission can reach a live store. Escalated in
  ``REPORT-contract-telemetry-03b-r2.md`` (ESC-2) because the spec states the
  emission's shape without naming its store-access channel.
* Because a double CAN declare a dependency into existence and leave production
  unable to construct the surface (the test-environment-is-a-fiction law,
  AC-15), :class:`TestTheEmissionsDependencyIsRealInProduction` introspects the
  REAL ``AppContext`` for the attribute the double provides, with a positive
  control.

FIXTURE DISCRIMINATION — what wrong build does each battery kill?
----------------------------------------------------------------
Read this before adding or "tidying" a fixture; several pins are only
discriminating in combination:

* The coverage battery (T7.1) dispatches every registered tool against the
  minimal app-context double, so MOST built-in tools raise inside their wrapper
  and are traced from the emission's ERROR leg. On its own that battery would
  therefore be satisfied by a build that traces ONLY failures. It is
  :class:`TestTheToolsOutcomeAlwaysWins` — a SUCCEEDING synthetic dispatch
  recording ``ok`` True — that kills that build. Neither battery is sufficient
  alone; both are load-bearing.
* Identity legs drive a SYNTHETIC probe tool declaring ``agent``/``session``/
  ``action`` (AC-17), so this contract has NO dependency on the comms send/drain/
  ack verbs landing first. The declared values are deliberately NOT the values
  the coverage registry uses, and one leg declares ``agent`` WITHOUT ``session``
  — a build that harvests the three keys all-or-nothing passes a monoculture
  fixture and fails that one.
* The session-sticky killer dispatches a DECLARING call and then a SILENT call
  inside the SAME transport session: a build that remembers "probably the same
  agent as the last call" passes every other identity leg and fails that one.
* Ordinal pins never assume 1-based numbering: ``sequence::nextval`` starts at 0
  (re-probed below), so a pin asserting ``ordinal == 1`` for the first row would
  be wrong against a correct build (AC-05).
* Every forall-over-a-collection pin leads with an explicit non-emptiness guard
  (AC-13): ``all()``/``sorted()``/``len(set())`` are trivially true of an empty
  collection, and "the tool call succeeded while the store was broken" is
  trivially true of a build with no telemetry at all.

PROBE RECEIPTS (all fresh 2026-07-24 at HEAD ``e7db965``, TEST store
``ws://127.0.0.1:18000`` only — ``:18500`` is production and was never touched;
each claim carries a positive control):

* ``sequence::nextval`` under the default ``START 0`` returns **0** on its first
  call and **1** on its second (SurrealDB 3.2.1) — so ordinals are 0-based.
  Re-probe of the fact added by commit ``7f23223``, per this packet's
  re-probe-on-contact ruling.
* ``SELECT *`` OMITS an unset ``option<>`` column entirely, while an EXPLICIT
  PROJECTION returns it as ``None``: a row with ``b`` unset came back with keys
  ``['a', 'ord']`` under ``SELECT *`` and as ``{'b': None}`` under
  ``SELECT a, b, ord``; the positive control (a sibling row WITH ``b`` set) came
  back carrying ``b`` under ``SELECT *``, proving the probe can see presence.
  Hence :data:`_TRACE_PROJECTION` — every read leg here projects explicitly, so
  an unset column reads ``None`` instead of raising ``KeyError`` as a harness
  failure that would masquerade as a finding (AC-05). Second re-probe of
  ``7f23223``.
* ``CREATE t CONTENT object::extend($bound, {computed})`` is the working shape
  for minting a column store-side alongside a bound payload; ``CONTENT $c SET
  …`` and ``CONTENT $c MERGE {…}`` are both PARSE ERRORS (both controls
  rejected, each naming its own unexpected token). Recorded because T3 mints the
  ordinal inside the trace write; this file pins the ordinal's OBSERVABLE
  properties, never the statement text.
* Harness mechanics at ``mcp==1.27.2``: a test-set ``request_ctx`` reaches a
  dispatched tool's ``lifespan_context``; ``request.headers.get('mcp-session-id')``
  is reachable in-handler (the correlator's source); a raising tool surfaces
  ``mcp.server.fastmcp.exceptions.ToolError`` carrying the original message;
  cancelling the dispatching task raises ``CancelledError`` out of
  ``call_tool``; with NO request context at all a tool errors with "Context is
  not available outside of a request" (the control).

RULED MID-WAVE (commit ``d0f84d0``) — the two escalations that were open
------------------------------------------------------------------------
* **ESC-1 → Reading B, via the SUCCESS-LATCH mechanism.** ``ok`` initializes
  **False** and is latched **True** only after ``super().call_tool`` RETURNS —
  **no ``except`` arm at all**. So every raise, cancellation included, leaves
  ``ok`` False while the ``finally``-arm write still lands the row. Semantics,
  verbatim: *True iff the dispatch RETURNED a result; False on any raise,
  cancellation included.* A third state was REFUSED (NONE already means "the
  writer did not supply it", and packet 06 filters cancelled and errored
  identically — neither is a call the agent performed; time-to-cancel already
  lives in ``latency_ms``). The previously-deferred assertion is therefore
  PINNED here: :class:`TestACancelledDispatchStillRecordsItsRow` asserts the row
  exists AND carries ``ok`` False.
  *(This wave's own escalation was that ``except Exception`` is a failure-class
  NAME-LIST and ``CancelledError`` the door it misses — the repo's instrument
  lesson reproduced in control flow. The ruled fix allowlists the ONE success
  path instead of enumerating failures, which is why there is no except arm to
  get wrong.)*
* **ESC-2 → CONFIRM channel A** (the request's lifespan context), on the
  construction-order derivation this file's harness already encodes; Reading B
  (reaching through the process guard) was refused as routing-not-sharing. The
  harness is unchanged — it was forcing A already.

WHAT THIS FILE STILL DELIBERATELY DOES NOT PIN (see the report)
--------------------------------------------------------------
* ``hit_count`` written by the seam: T2 REFUSES a generic hit count (0 hits is
  not "unknown"), so there is no served-count writer in this packet and the
  ``limit > pending`` twin fixture has nothing to discriminate. The pin here is
  the honesty pin — the seam records NO hit count — and the twin-fixture
  obligation is recorded as a named re-open trigger for whichever wave first
  adds a served-count writer (report ESC-3, AC-12's own note-for-future).
* The T7.9 deploy smoke (a live-store before/after trace count) is a packet-EXIT
  obligation, not a pytest pin; it is named in the report, not simulated here.
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import logging
import re
from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager, suppress
from types import SimpleNamespace
from typing import Any, cast

import pytest
import pytest_asyncio
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
from loremaster.config import LoreConfig
from loremaster.server import AppContext, LoreServer, build_mcp_server
from loremaster.store.surreal import SurrealStore, SurrealStoreError
from loremaster.store.surreal_schema import (
    TRACE_TABLE,
    _define_field,
    _define_table,
    _trace_statements,
    generate_ddl,
)
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.lowlevel.server import request_ctx
from mcp.shared.context import RequestContext
from mcp.types import CallToolRequest, CallToolRequestParams
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

# --------------------------------------------------------------------------- #
# Call-time access to the UNBUILT surface. See "RED, NEVER UNCOLLECTABLE".
# --------------------------------------------------------------------------- #
_TRACING_SUBCLASS_NAME = "TracingFastMCP"


def _tracing_subclass() -> Any:
    """The ``FastMCP`` subclass T1 rules into existence, fetched at CALL time.

    Returns:
        The ``loremaster.server.TracingFastMCP`` class object.

    Raises:
        AssertionError: The subclass does not exist yet — the expected RED at
            contract time, phrased so it teaches what to build.
    """
    from loremaster import server

    subclass = getattr(server, _TRACING_SUBCLASS_NAME, None)
    assert subclass is not None, (
        f"loremaster.server.{_TRACING_SUBCLASS_NAME} does not exist. T1 rules ONE funnel: "
        f"a FastMCP subclass overriding `call_tool`, constructed at build_mcp_server's single "
        f"FastMCP(...) site. Per-tool emission (a record_trace call in each @mcp.tool wrapper) "
        f"is REFUSED — ~20 forgettable obligations, invisible for any tool added later (#131)."
    )
    return subclass


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
_OTHER_TRANSPORT_SESSION_ID = "0ab74e2c19d8437fa6c05b3e8d91f742"
_MCP_SESSION_HEADER = "mcp-session-id"
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
_RAISING_TOOL_MESSAGE = "synthetic probe tool exploded on purpose"
# Long enough that a real latency assertion discriminates a build passing 0 or a
# constant, short enough not to slow the suite.
_SLOW_TOOL_SECONDS = 0.05
_LATENCY_TOLERANCE_MS = 5.0
_CANCEL_AFTER_SECONDS = 0.05
_BLOCKING_TOOL_SECONDS = 30.0


# --------------------------------------------------------------------------- #
# Synthetic probe tools — registered POST-construction through ``mcp.add_tool``,
# the extension-registration path (T7.1: the leg that kills a per-wrapper build
# for tools the wrappers never met). They also decouple the identity legs from
# the comms verbs (AC-17): the T4 rule is a PARAM-KEY rule, not a tool-name rule,
# so any tool declaring ``agent=`` is captured.
# --------------------------------------------------------------------------- #
_SYNTHETIC_OK = "probe_trace_ok"
_SYNTHETIC_DECLARING = "probe_trace_declaring"
_SYNTHETIC_PARTIAL = "probe_trace_partial_declaration"
_SYNTHETIC_SILENT = "probe_trace_silent"
_SYNTHETIC_INT_AGENT = "probe_trace_int_agent"
_SYNTHETIC_LEDGER_ACTOR = "probe_trace_ledger_actor"
_SYNTHETIC_RAISING = "probe_trace_raising"
_SYNTHETIC_SLOW = "probe_trace_slow"
_SYNTHETIC_BLOCKING = "probe_trace_blocking"
_SYNTHETIC_HOSTILE = "probe_trace_hostile_body"


def _register_synthetic_ok(mcp: Any) -> None:
    """Register the ONE synthetic tool the coverage harness carries."""

    def probe_trace_ok(marker: str) -> str:
        """A synthetic extension-registered tool that always succeeds."""
        return f"traced:{marker}"

    mcp.add_tool(
        probe_trace_ok,
        name=_SYNTHETIC_OK,
        description="Synthetic probe tool registered after construction (contract only).",
    )


def _register_synthetic_probes(mcp: Any) -> None:  # noqa: PLR0915 - one registration per probe shape
    """Register every synthetic probe the behaviour batteries drive."""

    def probe_trace_declaring(agent: str, session: str, action: str) -> str:
        """Declares all three harvested keys (T4.1)."""
        return f"declared:{agent}/{session}/{action}"

    def probe_trace_partial_declaration(agent: str) -> str:
        """Declares ``agent`` and NOTHING else — the all-or-nothing killer."""
        return f"partial:{agent}"

    def probe_trace_silent(marker: str) -> str:
        """Declares none of the harvested keys."""
        return f"silent:{marker}"

    def probe_trace_int_agent(agent: int) -> str:
        """Declares ``agent`` as an INT — T4.1 records a value iff it is a ``str``."""
        return f"int-agent:{agent}"

    def probe_trace_ledger_actor(owner: str, actor: str, created_by: str) -> str:
        """Declares the LEDGER-actor keys T4.1 refuses to harvest."""
        return f"ledger:{owner}/{actor}/{created_by}"

    def probe_trace_raising() -> str:
        """Raises, so the emission's error leg has a real subject."""
        raise RuntimeError(_RAISING_TOOL_MESSAGE)

    async def probe_trace_slow() -> str:
        """Sleeps a measurable interval so latency cannot be a constant."""
        await asyncio.sleep(_SLOW_TOOL_SECONDS)
        return "slow"

    async def probe_trace_blocking() -> str:
        """Blocks until cancelled — the AC-06 cancellation subject."""
        await asyncio.sleep(_BLOCKING_TOOL_SECONDS)
        return "never"

    def probe_trace_hostile_body(body: str, thread: str) -> str:
        """Takes free text, so the params_hash no-raw-content pin has a subject."""
        return f"hostile:{len(body)}:{thread}"

    for function, name in (
        (probe_trace_declaring, _SYNTHETIC_DECLARING),
        (probe_trace_partial_declaration, _SYNTHETIC_PARTIAL),
        (probe_trace_silent, _SYNTHETIC_SILENT),
        (probe_trace_int_agent, _SYNTHETIC_INT_AGENT),
        (probe_trace_ledger_actor, _SYNTHETIC_LEDGER_ACTOR),
        (probe_trace_raising, _SYNTHETIC_RAISING),
        (probe_trace_slow, _SYNTHETIC_SLOW),
        (probe_trace_blocking, _SYNTHETIC_BLOCKING),
        (probe_trace_hostile_body, _SYNTHETIC_HOSTILE),
    ):
        mcp.add_tool(
            function,
            name=name,
            description="Synthetic probe tool registered after construction (contract only).",
        )


# --------------------------------------------------------------------------- #
# The CHECKED coverage variable (T7.1). One entry per registered tool; the
# set-equality pin below makes a tool added WITHOUT a fixture RED
# (deny-by-default) rather than silently unmeasured.
# --------------------------------------------------------------------------- #
_MINIMAL_ARGS: dict[str, dict[str, Any]] = {
    "lore_search": {"query": "champion routing"},
    "lore_get_symbol": {"qualified_name": "loremaster.config.LoreConfig"},
    "lore_verify": {"qualified_name": "loremaster.config.LoreConfig"},
    "lore_impact": {"target": "loremaster.config"},
    "lore_map": {},
    "lore_read": {"tier": "custom", "path": "pkg/router.py"},
    "lore_recall": {"query": "surreal store ports"},
    "lore_remember": {"text": "the trace seam funnels every tool call"},
    "lore_index": {},
    "lore_dead_code": {},
    "lore_diff": {},
    "lore_findings": {"action": "query"},
    "lore_tasks": {"action": "query"},
    "lore_claim_task": {"task_id": "ledger-row-1", "owner": "coverage-probe"},
    "lore_comms": {"action": "fleet", "agent": "coverage-probe"},
    _SYNTHETIC_OK: {"marker": "coverage"},
}


# --------------------------------------------------------------------------- #
# Harness: the trace recorder, the app-context double, the request context.
# --------------------------------------------------------------------------- #
class _TraceRecorder:
    """The ``AppContext.write_store`` stand-in: captures every emission attempt.

    ``calls`` records ATTEMPTS — a failing recorder appends and then raises — so
    a failure-posture pin can prove the emission tried, and a coverage pin using
    a healthy recorder reads the same list as "rows written".

    Keyword-only by construction: ``record_trace`` is keyword-only on the real
    store, so a build calling it positionally fails here with a ``TypeError``
    rather than silently working against a friendlier double.
    """

    def __init__(self, *, failure: BaseException | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._failure = failure

    async def record_trace(self, **fields: Any) -> None:
        """Record (then optionally fail) one emission."""
        self.calls.append(dict(fields))
        if self._failure is not None:
            raise self._failure


class _TransportRequest:
    """A transport request exposing only ``headers`` — the correlator's source.

    Shaped after the streamable-http request object the SDK puts on
    ``RequestContext.request`` (probed: ``request.headers.get('mcp-session-id')``
    is reachable in-handler at ``mcp==1.27.2``).
    """

    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


def _app_context_double(recorder: _TraceRecorder) -> Any:
    """Exactly what the emission needs off the request's lifespan context."""
    return SimpleNamespace(write_store=recorder)


@contextmanager
def _request_context(
    app_context: Any,
    *,
    transport_session: str | None = _TRANSPORT_SESSION_ID,
    transport: bool = True,
) -> Iterator[None]:
    """Install a request-scoped lifespan context for the duration of the block.

    Args:
        app_context: The object the tool wrappers (and the emission) read as
            their ``AppContext``.
        transport_session: The ``mcp-session-id`` header value; ``None`` supplies
            a transport request carrying NO such header.
        transport: ``False`` supplies no transport request at all (the stdio
            shape) — the emission must record ``transport_session`` as NONE and
            still trace the call.
    """
    request: _TransportRequest | None = None
    if transport:
        headers = {} if transport_session is None else {_MCP_SESSION_HEADER: transport_session}
        request = _TransportRequest(headers)
    token = request_ctx.set(
        RequestContext(
            request_id=1,
            meta=None,
            session=cast(Any, None),
            lifespan_context=app_context,
            request=request,
        )
    )
    try:
        yield
    finally:
        request_ctx.reset(token)


def _payload_text(result: Any) -> str:
    """Flatten a ``call_tool`` return into text, tolerating both SDK shapes.

    ``FastMCP.call_tool(convert_result=True)`` returns ``(content, structured)``
    for a tool with an output schema and a bare content sequence otherwise.
    """
    content = result[0] if isinstance(result, tuple) else result
    if isinstance(content, list | tuple):
        return "".join(str(getattr(block, "text", "")) for block in content)
    return str(content)


async def _dispatch(mcp: Any, name: str, arguments: dict[str, Any]) -> Any:
    """Dispatch through the PRODUCTION entry point ``FastMCP.call_tool``."""
    return await mcp.call_tool(name, arguments)


async def _dispatch_ignoring_tool_failure(mcp: Any, name: str, arguments: dict[str, Any]) -> None:
    """Dispatch, letting the tool's own failure stand.

    Only ``ToolError`` is suppressed: every dispatched tool's outcome is
    irrelevant to a COVERAGE pin (the funnel traces success and failure alike),
    but any OTHER exception escaping the seam is a signal, not noise, and must
    fail the test loudly.
    """
    with suppress(ToolError):
        await mcp.call_tool(name, arguments)


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
@pytest.fixture()
def traced_server(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, _TraceRecorder]:
    """A REAL built server (+ one synthetic extension tool) and its recorder.

    Registration only — ``build_mcp_server`` registers tools synchronously and
    nothing connects until the lifespan actually runs (mirrors
    ``test_mcp_server.py``'s ``TestToolRegistration`` and ``test_comms_tool.py``'s
    ``_tools_by_name``).
    """
    monkeypatch.setenv("SURREAL_USER", "root")
    monkeypatch.setenv("SURREAL_PASS", "root")
    mcp = build_mcp_server(LoreServer(_config("trace_coverage")))
    _register_synthetic_ok(mcp)
    return mcp, _TraceRecorder()


@pytest.fixture()
def probe_server(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, _TraceRecorder]:
    """A REAL built server carrying every synthetic probe shape, + its recorder."""
    monkeypatch.setenv("SURREAL_USER", "root")
    monkeypatch.setenv("SURREAL_PASS", "root")
    mcp = build_mcp_server(LoreServer(_config("trace_probes")))
    _register_synthetic_probes(mcp)
    return mcp, _TraceRecorder()


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
class TestTheSeamIsInstalledAtTheOneFunnel:
    """T1: emission lives in a ``FastMCP`` subclass overriding ``call_tool``.

    THE WRONG BUILD this closes: a telemetry implementation that exists, is
    tested in isolation, and is never wired — ``build_mcp_server`` still
    constructing a plain ``FastMCP``. That build passes every emission pin driven
    directly against the subclass, and ``traces.total`` stays 0 forever with every
    gate green: #147's own shape. The one-line mutation (revert the constructor to
    ``FastMCP``) must go RED here AND in the coverage battery.
    """

    def test_build_mcp_server_constructs_the_tracing_subclass(
        self, traced_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, _recorder = traced_server
        subclass = _tracing_subclass()
        assert issubclass(subclass, FastMCP), (
            f"{_TRACING_SUBCLASS_NAME} must SUBCLASS FastMCP — T1's whole argument is that "
            f"`_setup_handlers` registers the BOUND `self.call_tool`, so overriding the method "
            f"puts the emission on the wire path by construction."
        )
        assert type(mcp) is subclass, (
            f"build_mcp_server returned a {type(mcp).__name__}; the single FastMCP(...) "
            f"construction site must become {_TRACING_SUBCLASS_NAME} or NOTHING is traced."
        )

    def test_the_dispatch_entry_point_is_the_subclass_override(
        self, traced_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # A subclass that inherits `call_tool` unchanged would satisfy the pin
        # above and trace nothing: the override itself is the seam.
        mcp, _recorder = traced_server
        subclass = _tracing_subclass()
        assert subclass.call_tool is not FastMCP.call_tool, (
            f"{_TRACING_SUBCLASS_NAME} does not OVERRIDE call_tool — it inherits it, so no "
            f"emission runs. T1's shape is: try/except/finally around `await super().call_tool(...)`."
        )
        assert type(mcp).call_tool is subclass.call_tool
        assert mcp.call_tool.__func__ is subclass.call_tool, (
            "the built server's bound `call_tool` is not the subclass override — the instance's "
            "dispatch entry point has been re-bound to something else."
        )


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
class TestCoverageIsACheckedVariable:
    """Every REGISTERED tool traces — and the registry cannot silently rot.

    THE WRONG BUILD: per-tool emission (a ``record_trace`` call inside each
    ``@mcp.tool`` wrapper). It traces the ~15 tools whose wrappers somebody
    edited and NOTHING registered later — including every extension tool, which
    the wrappers never meet. The set-equality pin plus the post-construction
    synthetic tool close that door: a tool added without a fixture is RED
    (deny-by-default), never quietly unmeasured.
    """

    async def test_the_minimal_args_registry_is_exactly_the_registered_surface(
        self, traced_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, _recorder = traced_server
        registered = {tool.name for tool in await mcp.list_tools()}
        # NON-VACUITY (AC-13): an empty surface makes every set relation below
        # trivially true, and "nothing was missing" would read as coverage.
        assert registered, "the built server registered NO tools — the coverage variable is vacuous"
        assert set(_MINIMAL_ARGS) == registered, (
            "the coverage registry and the REGISTERED surface have diverged. Tools with no "
            f"fixture (they would go unmeasured): {sorted(registered - set(_MINIMAL_ARGS))}. "
            f"Fixtures naming no live tool (they would measure nothing): "
            f"{sorted(set(_MINIMAL_ARGS) - registered)}. Add a minimal-argument entry for each "
            "new tool — a tool with no entry is a tool nobody is measuring, which is exactly how "
            "#147 stayed invisible."
        )

    async def test_the_synthetic_probe_is_registered_after_construction(
        self, traced_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # The synthetic tool must genuinely ride the extension path, or the
        # "tools the wrappers never met" leg proves nothing.
        mcp, _recorder = traced_server
        registered = {tool.name for tool in await mcp.list_tools()}
        assert _SYNTHETIC_OK in registered
        assert not _SYNTHETIC_OK.startswith("lore_"), (
            "the synthetic probe must not masquerade as a built-in: its whole purpose is to be a "
            "tool `_register_tools` never saw."
        )

    @pytest.mark.parametrize("tool_name", sorted(_MINIMAL_ARGS))
    async def test_every_registered_tool_dispatch_records_exactly_one_row(
        self, traced_server: tuple[Any, _TraceRecorder], tool_name: str
    ) -> None:
        # The tool's own OUTCOME is irrelevant here: against a minimal app-context
        # double most built-ins fail inside their wrapper, and the funnel must
        # trace success and failure alike (T5.4 — the write sits in `finally`).
        # A build that traces ONLY failures is killed by
        # TestTheToolsOutcomeAlwaysWins, not by this battery.
        mcp, recorder = traced_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch_ignoring_tool_failure(mcp, tool_name, _MINIMAL_ARGS[tool_name])
        assert len(recorder.calls) == 1, (
            f"dispatching {tool_name} through FastMCP.call_tool wrote {len(recorder.calls)} trace "
            f"rows, expected exactly 1. Zero means this tool is not covered by the funnel; more "
            f"than one means the emission runs twice (a double-counted denominator corrupts the "
            f"decay curve packet 06 reads)."
        )
        assert recorder.calls[0]["tool"] == tool_name, (
            f"the row records tool={recorder.calls[0].get('tool')!r} for a dispatch of "
            f"{tool_name!r} — the funnel must record the DISPATCHED name, not a constant."
        )

    async def test_the_wire_handler_registered_at_construction_traces_too(
        self, traced_server: tuple[Any, _TraceRecorder]
    ) -> None:
        """The path PRODUCTION uses: the lowlevel ``CallToolRequest`` handler.

        ``FastMCP._setup_handlers`` registers ``self.call_tool`` with the lowlevel
        server at ``__init__``. Driving ``FastMCP.call_tool`` directly proves the
        method traces; driving the registered handler proves the WIRE reaches it
        (D9's first door: a refactor that re-registers the base method would keep
        every direct-dispatch pin green).
        """
        mcp, recorder = traced_server
        handler = mcp._mcp_server.request_handlers[CallToolRequest]
        with _request_context(_app_context_double(recorder)):
            result = await handler(
                CallToolRequest(
                    method="tools/call",
                    params=CallToolRequestParams(
                        name=_SYNTHETIC_OK, arguments=_MINIMAL_ARGS[_SYNTHETIC_OK]
                    ),
                )
            )
        assert getattr(result.root, "isError", True) is False, (
            f"the wire dispatch reported an error: {result.root}"
        )
        assert len(recorder.calls) == 1, (
            "a dispatch through the REGISTERED wire handler wrote no trace row — the emission is "
            "reachable only when a test calls the method directly, which production never does."
        )
        assert recorder.calls[0]["tool"] == _SYNTHETIC_OK


# --------------------------------------------------------------------------- #
# T5 — emission shape and failure posture
# --------------------------------------------------------------------------- #
class TestTheToolsOutcomeAlwaysWins:
    """T5.1/T5.4: the tool's result and its error both survive the emission.

    This battery also carries the SUCCESS leg the coverage battery structurally
    cannot: a build emitting only from the error path would pass every coverage
    parametrisation (against the minimal double nearly every built-in fails) and
    dies here.
    """

    async def test_a_successful_dispatch_returns_its_own_result_and_records_ok_true(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            result = await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "kept"})
        assert "silent:kept" in _payload_text(result), (
            "the emission altered a successful tool's result; the tool call's outcome ALWAYS wins."
        )
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["ok"] is True, (
            f"a SUCCESSFUL dispatch recorded ok={recorder.calls[0].get('ok')!r}. `ok` is what lets "
            f"packet 06 exclude errored drains from the numerator — a drain that ERRORED is not a "
            f"drain the agent performed."
        )

    async def test_a_raising_tool_surfaces_unchanged_and_records_ok_false(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            with pytest.raises(ToolError) as raised:
                await _dispatch(mcp, _SYNTHETIC_RAISING, {})
        assert _RAISING_TOOL_MESSAGE in str(raised.value), (
            "the tool's own error must surface UNCHANGED — the emission may never swallow, "
            "rewrite, or replace it."
        )
        assert len(recorder.calls) == 1, (
            "a raising tool wrote no trace row. The write sits in `finally` precisely so the error "
            "leg records: an errored call still advances the DENOMINATOR."
        )
        assert recorder.calls[0]["ok"] is False, (
            f"an ERRORED dispatch recorded ok={recorder.calls[0].get('ok')!r}. Ruled semantics "
            f"(ESC-1, d0f84d0): True iff the dispatch RETURNED a result — False on any raise, "
            f"cancellation included."
        )
        assert recorder.calls[0]["tool"] == _SYNTHETIC_RAISING

    async def test_the_recorded_latency_reflects_the_calls_real_duration(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # Kills a build passing 0, a constant, or a value measured after the
        # emission rather than around the tool call.
        mcp, recorder = probe_server
        loop = asyncio.get_running_loop()
        started = loop.time()
        with _request_context(_app_context_double(recorder)):
            await _dispatch(mcp, _SYNTHETIC_SLOW, {})
        elapsed_ms = (loop.time() - started) * 1000
        assert len(recorder.calls) == 1
        latency_ms = recorder.calls[0]["latency_ms"]
        assert isinstance(latency_ms, float | int) and not isinstance(latency_ms, bool)
        assert latency_ms >= _SLOW_TOOL_SECONDS * 1000 - _LATENCY_TOLERANCE_MS, (
            f"recorded latency {latency_ms}ms is below the tool's own "
            f"{_SLOW_TOOL_SECONDS * 1000}ms sleep — the measurement does not span the tool call."
        )
        assert latency_ms <= elapsed_ms + _LATENCY_TOLERANCE_MS, (
            f"recorded latency {latency_ms}ms exceeds the whole dispatch's {elapsed_ms}ms."
        )

    async def test_the_seam_never_mints_the_ordinal_itself(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # T3: the ordinal is minted SERVER-SIDE inside the trace write. A seam
        # that computes it client-side (a counter, a timestamp, an id) passes
        # every sequential-ordering pin and COLLIDES under concurrency.
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "no-client-mint"})
        assert len(recorder.calls) == 1
        assert "ordinal" not in recorder.calls[0], (
            f"the emission passed ordinal={recorder.calls[0].get('ordinal')!r} to the store. T3 "
            f"rules ONE global native sequence minted inside the write transaction — a "
            f"client-side mint is a THIRD mint policy (#102's clone) and races."
        )

    async def test_the_seam_records_no_hit_count(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # T2's honesty rule: the generic seam cannot know a hit count, and 0 hits
        # is a LIE rather than an absence (it would make the served aggregate
        # wrong). Absence must be REPRESENTABLE, so `hit_count` is option<int>
        # and the seam leaves it unset.
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "no-hits"})
        assert len(recorder.calls) == 1
        assert recorder.calls[0].get("hit_count") is None, (
            f"the seam recorded hit_count={recorder.calls[0].get('hit_count')!r}. Supplying 0 for a "
            f"tool whose result count is unknowable makes `trace_aggregates` lie; NONE is the "
            f"honest value."
        )


class TestATraceWriteFailureNeverTouchesTheCall:
    """T5.1: a trace-write failure is LOUD in the log and INVISIBLE to the caller.

    The DESIGN-LAW section 14 carve-out (fork FK-7, operator-CONFIRMED): section
    14 governs durable lore DATA, where silent loss is data loss. A trace row is
    telemetry ABOUT a call — failing the call to save its telemetry would couple
    the entire served tool surface to an observability row. The carve-out is
    narrow, and these are its instruments.
    """

    async def test_a_failing_store_leaves_a_successful_result_intact(
        self, probe_server: tuple[Any, _TraceRecorder], caplog: pytest.LogCaptureFixture
    ) -> None:
        mcp, _healthy = probe_server
        broken = _TraceRecorder(failure=SurrealStoreError("trace store is down"))
        with caplog.at_level(logging.ERROR, logger="loremaster.server"):
            with _request_context(_app_context_double(broken)):
                result = await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "survives"})
        assert "silent:survives" in _payload_text(result), (
            "a trace-write failure converted a successful tool call into something else."
        )
        assert broken.calls, "the emission never even attempted the write"
        loud = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert loud, (
            "a trace-write failure was swallowed silently. The failure IS loud where it can be: "
            "the server log. A silent failure plus a flatlined traces section is #147 again, with "
            "nothing to diagnose from."
        )
        assert any(record.exc_info is not None for record in loud), (
            "the loud log must carry the exception (a `logger.exception`-shaped event), not a bare "
            "message: the store's own classified error is the diagnostic."
        )
        assert any(
            re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z0-9_]+)+", record.message) for record in loud
        ), (
            "the failure event must be a STRUCTURED dotted event name (the house idiom: "
            "`logger.exception('trace.emit.failed', extra={...})`), never an interpolated "
            "sentence — an unstructured message cannot be counted or alerted on."
        )
        assert any(
            _SYNTHETIC_SILENT in record.message or _SYNTHETIC_SILENT in str(record.__dict__)
            for record in loud
        ), (
            f"the loud log must NAME the tool ({_SYNTHETIC_SILENT}); an anonymous failure cannot "
            f"be attributed to a call."
        )

    async def test_the_positive_control_the_same_call_writes_when_the_store_is_healthy(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # Without this leg, "the call succeeded while the store was broken" is
        # trivially true of a build with NO telemetry at all (AC-13).
        mcp, healthy = probe_server
        with _request_context(_app_context_double(healthy)):
            await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "survives"})
        assert len(healthy.calls) == 1, (
            "the healthy-store control wrote nothing, so the broken-store leg above proves "
            "nothing: it would pass against a build that never emits."
        )

    async def test_a_failing_store_on_a_failing_tool_still_surfaces_the_tools_error(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # Both halves fail at once: the TOOL's error must reach the caller, never
        # the store's. A build that raises from the emission's `finally` replaces
        # the caller's diagnosis with an unrelated one.
        mcp, _healthy = probe_server
        broken = _TraceRecorder(failure=SurrealStoreError("trace store is down"))
        with _request_context(_app_context_double(broken)):
            with pytest.raises(ToolError) as raised:
                await _dispatch(mcp, _SYNTHETIC_RAISING, {})
        assert _RAISING_TOOL_MESSAGE in str(raised.value), (
            f"the caller received {raised.value!r} — the store's failure displaced the tool's own "
            f"error."
        )
        assert "trace store is down" not in str(raised.value)

    async def test_a_dispatch_with_no_reachable_app_context_still_serves_the_tool(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # There is no lifespan context here at all, so the emission cannot find a
        # store. The tool must still be served: telemetry is never a gate on the
        # surface. (Probed: with no request context the SDK's own Context fetch
        # raises, so an emission that reads the context OUTSIDE its own guard
        # takes the tool down with it.)
        mcp, _recorder = probe_server
        result = await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "contextless"})
        assert "silent:contextless" in _payload_text(result)


class TestACancelledDispatchStillRecordsItsRow:
    """AC-06: the ``finally`` placement is LOAD-BEARING, not style.

    Measured (adversary probe P6, three legs): an awaited write in ``finally``
    COMPLETES when the surrounding task is cancelled; the same write placed in an
    ``except Exception`` arm plus the success path loses the row on cancellation.
    That lost population is a struggling session's timed-out calls — exactly the
    denominator packet 06 most needs. This pin exists so a builder cannot
    "simplify" ``finally`` into except+return arms and silently un-trace it.

    **The ``ok`` leg (ESC-1, RULED at ``d0f84d0`` — the SUCCESS LATCH).** ``ok``
    initializes False and is latched True only after ``super().call_tool``
    RETURNS, with NO ``except`` arm — so a cancelled dispatch lands ``ok=False``.
    That is not a style preference: an ``ok=True``-initial flag cleared in an
    ``except Exception`` arm is a failure-class NAME-LIST, and ``CancelledError``
    (a ``BaseException``) is the door it misses — so a timed-out drain would be
    counted as a performed one in the very instrument packet 06 decides on. The
    latch allowlists the ONE success path instead of enumerating failures.
    """

    async def test_cancelling_a_dispatch_mid_flight_still_writes_the_trace_row(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            # The task inherits the current context (including request_ctx) at
            # creation, so the dispatched tool sees the same app-context double.
            task = asyncio.create_task(_dispatch(mcp, _SYNTHETIC_BLOCKING, {}))
            await asyncio.sleep(_CANCEL_AFTER_SECONDS)
            assert not task.done(), "the blocking probe finished before it could be cancelled"
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert len(recorder.calls) == 1, (
            "a CANCELLED dispatch wrote no trace row. The emission's write belongs in `finally`: "
            "an except+return placement loses exactly the timed-out population (probe P6)."
        )
        assert recorder.calls[0]["tool"] == _SYNTHETIC_BLOCKING
        assert recorder.calls[0]["ok"] is False, (
            f"the cancelled dispatch recorded ok={recorder.calls[0].get('ok')!r}. ESC-1's ruled "
            f"SUCCESS-LATCH form (d0f84d0): ok starts False and is latched True only after "
            f"super().call_tool RETURNS, with no except arm — so a cancellation leaves it False. "
            f"True here means the flag is being CLEARED by a failure-class name-list "
            f"(`except Exception`) that CancelledError walks straight past, and a timed-out drain "
            f"then counts as one the agent performed."
        )


# --------------------------------------------------------------------------- #
# T4 — declared-only identity + the transport correlator
# --------------------------------------------------------------------------- #
class TestIdentityIsDeclaredNeverGuessed:
    """T4: record what is DECLARED and what is TRANSPORT-MEASURED; never guess.

    THE WRONG BUILD this battery exists to kill: session-sticky attribution —
    "this transport session said agent=X a moment ago, so this anonymous call is
    probably X too". A guessed identity in a MEASUREMENT INSTRUMENT poisons the
    very curve the instrument exists to produce, invisibly, and no aggregate can
    later tell a guess from a declaration.

    Every leg drives a SYNTHETIC probe tool declaring the harvested keys, because
    T4.1 is a PARAM-KEY rule rather than a tool-name rule (no tool enumeration
    exists to go stale) — which also decouples this contract from the comms verbs
    landing first (AC-17).
    """

    async def test_a_declaring_call_records_all_three_declared_keys(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(
                mcp,
                _SYNTHETIC_DECLARING,
                {"agent": _DECLARED_AGENT, "session": _DECLARED_SESSION, "action": _DECLARED_ACTION},
            )
        assert len(recorder.calls) == 1
        row = recorder.calls[0]
        assert row["agent"] == _DECLARED_AGENT
        assert row["session"] == _DECLARED_SESSION
        assert row["action"] == _DECLARED_ACTION, (
            "without the declared `action`, a drain row is indistinguishable from a heartbeat "
            "inside lore_comms's tool count — the numerator collapses into the denominator."
        )
        assert row["transport_session"] == _TRANSPORT_SESSION_ID

    async def test_a_partial_declaration_records_only_what_was_declared(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # Kills an all-or-nothing harvest (record the three keys only when all
        # three are present) — a build a monoculture fixture would wave through.
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(mcp, _SYNTHETIC_PARTIAL, {"agent": _DECLARED_AGENT})
        assert len(recorder.calls) == 1
        row = recorder.calls[0]
        assert row["agent"] == _DECLARED_AGENT
        assert row.get("session") is None, (
            f"session={row.get('session')!r} on a call that declared none. Only a call that "
            f"DECLARES a fleet session has one; overloading the column with anything else mixes "
            f"two identity vocabularies in one field."
        )
        assert row.get("action") is None

    async def test_a_silent_call_records_NONE_even_after_a_declaring_call_on_the_same_transport(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # THE session-sticky killer. Same transport session, two dispatches: the
        # first declares, the second declares nothing. A build that remembers the
        # first passes every other identity leg and fails here.
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(
                mcp,
                _SYNTHETIC_DECLARING,
                {"agent": _DECLARED_AGENT, "session": _DECLARED_SESSION, "action": _DECLARED_ACTION},
            )
            await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "anonymous"})
        assert len(recorder.calls) == 2, "both dispatches must trace — the denominator counts BOTH"
        first, second = recorder.calls
        assert first["agent"] == _DECLARED_AGENT, "control: the declaring call DID record an agent"
        assert second.get("agent") is None, (
            f"the anonymous call recorded agent={second.get('agent')!r}, inherited from an earlier "
            f"call on the same transport session. NO inference, no session-sticky attribution, no "
            f"'probably the same agent as the last call' — a guessed identity poisons the curve."
        )
        assert second.get("session") is None
        assert second.get("action") is None
        assert second["transport_session"] == _TRANSPORT_SESSION_ID, (
            "the transport correlator is MEASURED, not declared: an anonymous call still carries "
            "it, and packet 06 joins it to declared identities by observed co-occurrence."
        )

    async def test_a_non_string_declared_value_is_recorded_as_NONE(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # T4.1 records a declared value IFF it is a `str`. A build that coerces
        # (`str(value)`) would mint identities like "7" out of a future tool's
        # unrelated integer parameter.
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(mcp, _SYNTHETIC_INT_AGENT, {"agent": 7})
        assert len(recorder.calls) == 1
        assert recorder.calls[0].get("agent") is None, (
            f"agent={recorder.calls[0].get('agent')!r} was coerced from a non-string declared "
            f"value; T4.1 records it only if it IS a str, else NONE."
        )

    async def test_the_heterogeneous_ledger_actor_params_are_NOT_harvested(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # T4.1 refuses `owner`/`actor`/`created_by`: they name LEDGER actors, not
        # comms-registered agents, and stuffing them into trace.agent would make
        # one column an unmarked MIXTURE of two identity vocabularies — the same
        # honesty rule that refused overloading `session` with a transport id.
        # A build harvesting "any identity-looking key" passes every other
        # identity leg here and fails this one.
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(
                mcp,
                _SYNTHETIC_LEDGER_ACTOR,
                {"owner": "ledger-owner", "actor": "ledger-actor", "created_by": "ledger-author"},
            )
        assert len(recorder.calls) == 1, "the call must still be traced — anonymously"
        row = recorder.calls[0]
        assert row.get("agent") is None, (
            f"agent={row.get('agent')!r} was harvested from a ledger-actor parameter. Only the "
            f"three declared keys (agent/session/action) are harvested; everything else is a "
            f"DIFFERENT identity vocabulary."
        )
        assert row.get("session") is None
        assert row.get("action") is None

    async def test_the_correlator_is_NONE_when_the_transport_carries_no_session_header(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder), transport_session=None):
            await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "headerless"})
        assert len(recorder.calls) == 1
        assert recorder.calls[0].get("transport_session") is None

    async def test_the_correlator_is_NONE_when_there_is_no_transport_request_at_all(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # The stdio shape. The call must STILL be traced: a fully anonymous row
        # advances the denominator, and that is most of the point.
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder), transport=False):
            await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "stdio"})
        assert len(recorder.calls) == 1, (
            "a transport with no session id wrote no row. An anonymous call is not an unmeasured "
            "call: absence of identity is not absence of a call."
        )
        assert recorder.calls[0].get("transport_session") is None
        assert recorder.calls[0].get("agent") is None

    async def test_two_transport_sessions_are_recorded_distinctly(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # Parameter monoculture guard: a build hardcoding or interning one
        # correlator value passes every single-value leg above.
        mcp, recorder = probe_server
        for session_id in (_TRANSPORT_SESSION_ID, _OTHER_TRANSPORT_SESSION_ID):
            with _request_context(_app_context_double(recorder), transport_session=session_id):
                await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "correlate"})
        recorded = [row.get("transport_session") for row in recorder.calls]
        assert recorded == [_TRANSPORT_SESSION_ID, _OTHER_TRANSPORT_SESSION_ID], (
            f"recorded correlators {recorded!r} do not track the two distinct transport sessions."
        )


# --------------------------------------------------------------------------- #
# T6 — params_hash
# --------------------------------------------------------------------------- #
class TestParamsHashIsTheRuledRecipeAndLeaksNothing:
    """T6: one deterministic digest over the RAW arguments; no content stored.

    The digest is the ONLY thing that crosses from arguments into the row, so it
    is also the whole privacy boundary: bodies, briefs, and queries pass through
    the hash and nowhere else.
    """

    async def test_the_recipe_is_sha256_over_sorted_json(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, recorder = probe_server
        arguments = {"marker": "recipe"}
        with _request_context(_app_context_double(recorder)):
            await _dispatch(mcp, _SYNTHETIC_SILENT, arguments)
        assert len(recorder.calls) == 1
        served = recorder.calls[0]["params_hash"]
        assert served == _expected_params_hash(arguments), (
            f"params_hash={served!r} is not the T6 recipe "
            f"sha256(json.dumps(arguments, sort_keys=True, default=str)). The recipe is named "
            f"ONCE in the design so every future reader of the column knows what it digests."
        )
        assert re.fullmatch(r"[0-9a-f]{64}", served), (
            f"params_hash must be the FULL lowercase hex digest, got {served!r}"
        )

    async def test_the_same_arguments_hash_identically_and_different_ones_do_not(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "same"})
            await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "same"})
            await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "different"})
        hashes = [row["params_hash"] for row in recorder.calls]
        assert len(hashes) == 3, f"expected three traced dispatches, got {len(hashes)}"
        assert hashes[0] == hashes[1], "identical arguments must digest identically"
        # POSITIVE CONTROL: a build returning one constant satisfies determinism.
        assert hashes[2] != hashes[0], (
            "different arguments produced the SAME digest — a constant satisfies determinism and "
            "measures nothing."
        )

    async def test_key_order_does_not_change_the_digest(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # The `sort_keys=True` half of the recipe: two dicts differing only in
        # insertion order describe the SAME call.
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(
                mcp,
                _SYNTHETIC_DECLARING,
                {"agent": _DECLARED_AGENT, "session": _DECLARED_SESSION, "action": _DECLARED_ACTION},
            )
            await _dispatch(
                mcp,
                _SYNTHETIC_DECLARING,
                {"action": _DECLARED_ACTION, "session": _DECLARED_SESSION, "agent": _DECLARED_AGENT},
            )
        hashes = [row["params_hash"] for row in recorder.calls]
        assert len(hashes) == 2
        assert hashes[0] == hashes[1], (
            "argument key ORDER changed the digest, so the same call digests two ways and every "
            "per-call aggregate over params_hash splits."
        )

    async def test_no_raw_parameter_content_reaches_the_row(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        # Hostile fixture: newlines + a row-shaped forgery line + a backtick run.
        # A build that stored the arguments (or a prefix of them) alongside the
        # hash would put other agents' free text into an observability row and
        # into anything that ever renders one.
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(
                mcp, _SYNTHETIC_HOSTILE, {"body": _HOSTILE_BODY, "thread": "wave9-hostile"}
            )
        assert len(recorder.calls) == 1
        row = recorder.calls[0]
        serialised = json.dumps(row, default=str)
        for fragment in ("row-shaped", "forged (kind friction", "trailing line", "```"):
            assert fragment not in serialised, (
                f"the stored row carries raw parameter content ({fragment!r}). Bodies pass through "
                f"the params_hash and NOWHERE else."
            )
        assert row["params_hash"] == _expected_params_hash(
            {"body": _HOSTILE_BODY, "thread": "wave9-hostile"}
        )


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
        """ESC-1's ruling requires the semantics VERBATIM in the column's comment.

        Not bureaucracy: ``ok`` is a boolean whose meaning is not guessable from
        its name (does a cancelled call count? an errored one?), and packet 06
        filters on it. This repo's own audited failure mode is prose that
        describes behaviour drifting from the behaviour with no gate in between —
        so the ruled sentence gets an instrument rather than a memo.

        Keyed on the distinctive CLAUSE rather than the whole sentence with its
        markup, so a reflow or a different emphasis style does not go RED for a
        cosmetic reason — while a build that documents ``ok`` as "whether the tool
        succeeded" (the wording the latch mechanism exists to correct) does.
        """
        from loremaster.store import surreal_schema

        source_lines = inspect.getsource(surreal_schema).splitlines()
        specs_line = next(
            (index for index, line in enumerate(source_lines) if line.startswith("_TRACE_FIELD_SPECS")),
            None,
        )
        assert specs_line is not None, "could not locate the _TRACE_FIELD_SPECS assignment"
        window = "\n".join(source_lines[max(0, specs_line - _COMMENT_WINDOW_LINES) : specs_line + 1])
        normalised = " ".join(window.split())
        assert _OK_SEMANTICS_CLAUSE in normalised, (
            f"the ruled `ok` semantics are not documented where the column is defined. ESC-1 "
            f"(d0f84d0) requires, verbatim: 'True iff the dispatch RETURNED a result; "
            f"{_OK_SEMANTICS_CLAUSE}.' The mechanism is a SUCCESS LATCH — ok starts False and is "
            f"latched True only on return — and a comment saying merely 'whether the call "
            f"succeeded' leaves the next reader to guess about cancellation, which is exactly the "
            f"population packet 06 needs."
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
            aggregates = await store.trace_aggregates()
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
        assert all(
            later > earlier for earlier, later in zip(ordinals, ordinals[1:], strict=True)
        ), f"ordinals are not strictly increasing: {ordinals!r}"

    async def test_eight_concurrent_writes_mint_eight_distinct_ordinals(
        self, trace_store_factory: Any
    ) -> None:
        # The load-bearing mint pin, at the ruled degree. Separate stores on
        # separate CONNECTIONS: N coroutines on one socket do not contend the way
        # N connections do. THE WRONG BUILD: an ordinal minted client-side, or by
        # read-max-then-CREATE — single-threaded-correct, passes every sequential
        # pin above, and collides here.
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
        aggregates = await trace_store.trace_aggregates()
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
class TestNoProductionProseStillTeachesTheRetiredPlan:
    """The served/read prose must not teach a plan the design REFUSED.

    T5.2 rules AGAINST fire-and-forget emission (the coverage pin must be
    deterministic — "the row exists when the call returns" — or the forall-tools
    gate goes flaky and gets switched off, and a gate that cries wolf is a gate
    nobody keeps). ``record_trace``'s committed docstring teaches exactly that
    retired plan, and this repo's own audited failure pattern is defects clustering
    in natural-language surfaces whose consistency with code NO GATE CHECKS. The
    sweep pattern is BARE and anchor-free: prose mentions carry no structural
    anchors.
    """

    def test_the_record_trace_docstring_no_longer_teaches_fire_and_forget(self) -> None:
        docstring = inspect.getdoc(SurrealStore.record_trace) or ""
        assert docstring, "record_trace lost its docstring"
        assert "fire-and-forget" not in docstring.lower(), (
            "record_trace's docstring still teaches the REFUSED fire-and-forget emission plan. "
            "T5.2 rules the emission is AWAITED INLINE; a docstring promising otherwise teaches "
            "the next reader to build the flaky version."
        )

    def test_the_record_trace_docstring_no_longer_claims_six_core_fields(self) -> None:
        # A count in prose is a claim about behaviour, and this one is now false:
        # the row carries the six committed columns plus five enrichment columns.
        docstring = inspect.getdoc(SurrealStore.record_trace) or ""
        assert "six core" not in docstring.lower(), (
            "record_trace's docstring still says 'six core fields'. Prose that describes "
            "behaviour must be DERIVED from the behaviour, not re-stated beside it — a stale count "
            "is the defect class this repo has now shipped ten instances of."
        )

    def test_the_trace_statements_docstring_no_longer_claims_six_core_fields(self) -> None:
        docstring = inspect.getdoc(_trace_statements) or ""
        assert docstring, "_trace_statements lost its docstring"
        assert "six core" not in docstring.lower(), (
            "_trace_statements' docstring still says 'six core fields' while emitting eleven "
            "columns plus a sequence and an index."
        )
