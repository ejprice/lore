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

KNOWN BOUND — the emission's kwarg VALUES are not verified in two cells
----------------------------------------------------------------------
**This is a KNOWN, ACCEPTED BOUND (adversary report §FV-3; lead-ruled ACCEPTED at
`f6cb14a`) — not an oversight, and not something to close casually. If you close
it deliberately, delete this paragraph and say so in the same commit.**

**The bound, exactly:** the emission's kwarg **names and arity** are verified for
EVERY dispatch, by construction — :class:`_TraceRecorder` binds against
``inspect.signature(SurrealStore.record_trace)``. Its **values and types** are
verified only where a pin dispatches into a REAL store: success ∀ the registry
(MP-H), error ∀ the registry (MP-I), and success/error on synthetic subjects
(MP-A). **Unverified: (a) the CANCELLED cell against a real store, and (b) digest
CONTENT on the error path** — MP-H/MP-I assert the row LANDS with the right ``tool``
and ``ok``, not that its ``params_hash`` equals the recipe's value.

**Why it is bounded rather than closed — the threat model, which is written down in
this repo and is what makes the verdict mechanical:** the only shapes that survive
in those cells carry a condition chosen specifically to dodge the fixtures
(``if cancelled``, ``if not ok and tool.startswith("lore_")``). Measured, all three
at 491 passed / 0 failed: a wrong-typed ``agent`` or a stringified ``latency_ms``
ONLY on cancelled dispatches, and a digest truncated to 32 hex ONLY for real tools
on the error path. **Every UNCONDITIONAL counterpart of each is already dead** (23,
23, and 2–4 pins respectively). Per the repo's gate threat model — *"a clever
attacker gets through" is not a defect; "an honest engineer's mistake goes
unnoticed" is; and a gate that refuses honest code is a gate that gets switched
OFF* — no honest implementation of this seam contains such a branch, so these are
gate-attacks, not defects.

**And the closure was PRICED, not hand-waved:** a type-aware double (``bind()`` plus
an annotation check) closes two of the three, but it is **not drop-in** — it reddens
``test_every_parameter_the_REAL_signature_declares_is_ACCEPTED`` on a CORRECT build,
because that control feeds type-agnostic sentinels. Adopting it means editing a
CONTROL, and it still leaves the digest shape. That cost is why the bound is
recorded instead.

**NAMED RE-OPEN TRIGGER (the condition under which this trade changes):** the day
the emission passes a value that is neither a literal nor ``isinstance``-guarded —
i.e. any new ``Any``-sourced kwarg — **or** the day a consumer reads ``params_hash``
for EQUALITY rather than for grouping. Either makes the unverified cell reachable by
an honest mistake. The closure at that point is the type-aware double (with its
control fixture corrected first) plus one ``_expected_params_hash`` equality
assertion inside MP-H/MP-I.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import inspect
import io
import json
import logging
import re
import tokenize
from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import anyio
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
from loremaster.server import AppContext, LoreServer, TraceSummary, build_mcp_server
from loremaster.store._txn import _ERROR_CLASS_FIELD_COERCION
from loremaster.store.surreal import SurrealStore, SurrealStoreError
from loremaster.store.surreal_schema import (
    TRACE_IDENTITY_MAX_CHARS,
    TRACE_TABLE,
    TRACE_TS_FIELD,
    _define_field,
    _define_table,
    generate_ddl,
)
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.lowlevel.server import request_ctx
from mcp.shared.context import RequestContext
from mcp.types import CallToolRequest, CallToolRequestParams, TextContent
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
# The fragments the no-raw-content pin looks for. Every one must actually OCCUR in
# _HOSTILE_BODY — the pin asserts that first, because a fragment that does not occur
# is a vacuous iteration that reads as coverage (the file shipped one: "row-shaped").
_HOSTILE_FRAGMENTS: tuple[str, ...] = (
    "forged (kind friction",
    "trailing line",
    "```",
    "[#99 open]",
)
_RAISING_TOOL_MESSAGE = "synthetic probe tool exploded on purpose"
# Long enough that a real latency assertion discriminates a build passing 0 or a
# constant, short enough not to slow the suite.
_SLOW_TOOL_SECONDS = 0.05
_LATENCY_TOLERANCE_MS = 5.0
# MP-D's floor, as a FRACTION of the slow probe's own sleep rather than an absolute
# millisecond figure: the pin must stay meaningful if the sleep is ever retuned, and
# a fraction cannot be satisfied by a constant at any fixture value.
_LATENCY_DIFFERENCE_FRACTION = 0.5
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
_SYNTHETIC_NO_ARGS = "probe_trace_no_arguments"


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

    def probe_trace_no_arguments() -> str:
        """Takes NO arguments — the zero-argument digest subject (MP-E).

        Four registered tools (``lore_map`` / ``lore_index`` / ``lore_diff`` /
        ``lore_dead_code``) are dispatched with ``{}``, so the empty-arguments case
        is a REAL production shape, not an edge case.
        """
        return "no-arguments"

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
        (probe_trace_no_arguments, _SYNTHETIC_NO_ARGS),
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

    **IT BINDS AGAINST THE REAL SIGNATURE, AND THAT IS THE STRUCTURAL PROPERTY:**
    every call is first bound through ``inspect.signature(SurrealStore.record_trace)``,
    so **the double can never accept what the real signature would reject.** A
    keyword the real store does not declare, or a required one the seam forgot,
    raises here exactly as it would there — which turns EVERY double-backed pin in
    this file (success, error, cancellation, all eight identity legs, the hostile
    body, the params-hash battery, all 16 coverage parametrisations) into an
    end-to-end signature check, by construction rather than by remembering to add a
    cell.

    That is the fix for a defect CLASS, not for three instances of it. Three
    grading rounds found the same shape three times — a bad kwarg supplied only for
    successful calls (W11-adjacent), only against a real store (**W30**), only for
    real tools (**W33**), then only on a real tool's FAILURE path (**D4**) and only
    on a CANCELLED dispatch (**D6**). Each was a CELL of the input matrix
    (outcome × store × subject), and chasing cells one pin at a time is the
    enumerate-the-forbidden shape this repo has watched lose six times. Binding
    against the real signature makes the whole matrix hold at once, and **signature
    drift now reddens every consumer instantly** instead of silently widening the
    double.

    HONEST BOUND, stated so nobody over-trusts it: ``Signature.bind`` checks NAMES
    and ARITY, never TYPES or values. A wrong-TYPED argument still passes here and
    is caught only against the real engine — which is what
    :class:`TestADispatchLandsARealRowInTheRealTraceTable` (MP-A/MP-H) and
    ``test_the_widened_columns_still_REJECT_a_wrong_typed_value`` (R7) are for.
    The binder replaces the cell-chasing, not the real-store legs.
    """

    # Bound against the REAL store's signature, resolved once. Deliberately the
    # PRODUCTION signature object rather than a transcribed name list: a list is a
    # copy that goes stale, and the copy is the hole.
    _REAL_SIGNATURE = inspect.signature(SurrealStore.record_trace)

    def __init__(self, *, failure: BaseException | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._failure = failure

    async def record_trace(self, **fields: Any) -> None:
        """Bind against the real signature, then record (then optionally fail).

        Binding happens BEFORE the append and before any injected failure, because
        the real store writes NOTHING when the call itself is malformed: a
        signature mismatch must leave ``calls`` empty, so the pin that expected a
        row fails on the row's absence exactly as it would in production (where
        T5.1's ruled swallow logs the ``TypeError`` and serves the tool anyway).

        Raises:
            TypeError: The emission passed a keyword the real ``record_trace``
                does not declare, or omitted one it requires.
        """
        # ``None`` stands in for the bound ``self`` the unbound signature carries.
        self._REAL_SIGNATURE.bind(None, **fields)
        self.calls.append(dict(fields))
        if self._failure is not None:
            raise self._failure


class TestTheDoubleBindsAgainstTheRealSignature:
    """The CONTROL for :class:`_TraceRecorder`'s binder — the file's own oracle.

    Every double-backed pin in this file now leans on the binder, so a binder that
    silently accepted everything would return the whole contract to the state three
    grading rounds found holes in — and it would do so INVISIBLY, because a
    permissive double makes pins PASS. An instrument with no control is exactly how
    the unsatisfiable ordinal predicate (MP-C) survived authorship; this is that
    lesson applied to the harness itself, before an adversary has to apply it for
    me.

    Three directions, because a one-directional control is how a binder that
    rejects EVERYTHING would also pass: reject the unknown · accept the legal ·
    reject the missing-required.
    """

    # Deliberately the set of names that binds under BOTH the committed signature
    # (where `hit_count`/`session` are REQUIRED) and the T8 one (where they are
    # optional). This control's subject is the BINDER; if the fixture only bound
    # post-T8, these legs would be RED today for T8's reason and would isolate
    # nothing — a control that fails for a neighbouring reason is not a control.
    # T8's own signature change is pinned by FK-3b, where it belongs.
    _LEGAL_CALL: dict[str, Any] = {
        "tool": _SEAM_TOOL,
        "params_hash": _SEAM_PARAMS_HASH,
        "latency_ms": _SEAM_LATENCY_MS,
        "hit_count": None,
        "session": _DECLARED_SESSION,
    }

    async def test_a_keyword_the_real_store_does_not_declare_is_REJECTED(self) -> None:
        recorder = _TraceRecorder()
        with pytest.raises(TypeError) as rejected:
            await recorder.record_trace(**self._LEGAL_CALL, request_id="not-a-real-column")
        assert "request_id" in str(rejected.value), (
            f"the double rejected the call but did not NAME the offending keyword; a builder "
            f"reading this failure needs the parameter, not just a refusal. Served: {rejected.value}"
        )
        assert not recorder.calls, (
            "the double recorded a row for a call the real store would have REJECTED. Nothing may "
            "be recorded on a signature mismatch — the whole point is that the pin expecting a row "
            "fails on the row's ABSENCE, exactly as production behaves when T5.1's swallow logs "
            "the TypeError and serves the tool anyway."
        )

    async def test_the_legal_call_is_ACCEPTED(self) -> None:
        # POSITIVE CONTROL. Without it, a binder that rejected every call would
        # satisfy the leg above and quietly redden the entire contract.
        recorder = _TraceRecorder()
        await recorder.record_trace(**self._LEGAL_CALL)
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["tool"] == _SEAM_TOOL

    async def test_a_MISSING_required_argument_is_REJECTED(self) -> None:
        # The other direction of arity: a build that forgets `params_hash`
        # (or `tool`, or `latency_ms`) is as broken as one that invents a column,
        # and the real store raises for it too.
        recorder = _TraceRecorder()
        with pytest.raises(TypeError) as rejected:
            await recorder.record_trace(tool=_SEAM_TOOL, latency_ms=_SEAM_LATENCY_MS)
        assert "params_hash" in str(rejected.value)
        assert not recorder.calls

    async def test_every_parameter_the_REAL_signature_declares_is_ACCEPTED(self) -> None:
        """The binder must be the real signature, not a name list transcribed from it.

        Derived from ``inspect.signature`` rather than written out, so a parameter
        ADDED to the real ``record_trace`` later is covered without anyone editing
        this test — which is the difference between sharing the signature and
        cloning it. (Values are irrelevant: ``bind`` checks names and arity, never
        types — the honest bound recorded on the recorder itself.)
        """
        declared = [
            name
            for name in inspect.signature(SurrealStore.record_trace).parameters
            if name != "self"
        ]
        assert declared, "the real signature declares nothing — this control is vacuous"
        recorder = _TraceRecorder()
        await recorder.record_trace(**dict.fromkeys(declared))
        assert len(recorder.calls) == 1, (
            f"the double rejected a call using EVERY parameter the real store declares "
            f"({declared!r}) — it is enforcing a narrower, hand-maintained set, which is a copy "
            f"that will go stale against the signature it claims to mirror."
        )


class _SuspendingTraceRecorder(_TraceRecorder):
    """A recorder that SUSPENDS before recording — the real store's own shape.

    ⚠ THIS CLASS EXISTS BECAUSE ITS ABSENCE MADE A PIN UNFALSIFIABLE, and the
    mechanism is worth stating once so nobody "simplifies" it away.

    A cancel scope cancels a TASK; the cancellation is delivered at the task's
    next SUSPENSION POINT. :class:`_TraceRecorder` binds a signature and appends
    to a list — it never awaits anything — so a dispatch cancelled anywhere
    still completes its emission, shielded or not. Measured, all four cells:

    | emission suspends | shielded | row |
    |---|---|---|
    | no  | no  | WRITTEN |   <- the blind cell: no shield needed, so no pin can see one missing
    | no  | yes | WRITTEN |
    | yes | no  | **LOST** |  <- production's shape
    | yes | yes | WRITTEN |

    ``SurrealStore.record_trace`` is a network round-trip and therefore ALWAYS
    suspends, so only the bottom two rows describe production. A cancellation
    pin driven by the non-suspending double asserts a property that holds for
    reasons that do not exist at runtime.
    """

    async def record_trace(self, **fields: Any) -> None:
        """Suspend once, then record exactly as the base recorder does."""
        await asyncio.sleep(0)
        await super().record_trace(**fields)


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


def _app_context_double_over(store: Any) -> Any:
    """The same app-context shape, but over a REAL store (MP-A).

    The ONLY difference from :func:`_app_context_double` is what sits behind
    ``write_store``: a real :class:`SurrealStore` whose ``record_trace`` has a real
    signature and a real engine behind it, so a keyword the store does not accept
    RAISES instead of being swallowed by a ``**fields`` double. That difference is
    the entire W30 hole.
    """
    return SimpleNamespace(write_store=store)


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

    @pytest.mark.parametrize("tool_name", sorted(_MINIMAL_ARGS))
    async def test_every_registered_tool_traces_when_it_SUCCEEDS(
        self,
        traced_server: tuple[Any, _TraceRecorder],
        tool_name: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """MP-B: the SUCCESS cell of the coverage matrix, for EVERY registered tool.

        **THE DEFECT THIS EXISTS TO CATCH (adversary W11):**
        ``if ok and not tool.startswith("probe_"): return`` — a build that traces
        every FAILING call and every synthetic probe, and silently drops every
        SUCCESSFUL real-tool call. Measured: it scored identically to a correct
        build against this contract before this pin existed, because the sibling
        coverage battery dispatches all 15 built-ins against a minimal app-context
        double, so they all take the ERROR leg, and the only success ever traced
        was a synthetic probe. The denominator would then be "calls that failed" —
        and the decay curve packet 06 decides on would be garbage.

        The failed door-attempts are worth recording: keying the skip on the RESULT
        SHAPE instead of the name dies (20 pins) because the synthetic probes return
        the same ``(content, structured)`` tuple the real tools do. Only a
        NAME-keyed skip reached the uncovered cell — which is the six-defeats lesson
        again: the pin has to cover the CELL, not out-guess the shapes.

        Mechanism: the tool manager is stubbed so every dispatch RETURNS through the
        real production override. That is deliberately the narrowest possible
        substitution — ``FastMCP.call_tool`` (the seam under test) and everything in
        it still runs; only the tool BODY is replaced, because the bodies need a
        full AppContext and this pin is about the funnel, not about the tools.
        """
        mcp, recorder = traced_server

        async def _canned_success(
            name: str, arguments: dict[str, Any], **_kwargs: Any
        ) -> list[TextContent]:
            return [TextContent(type="text", text=f"canned:{name}:{sorted(arguments)}")]

        monkeypatch.setattr(mcp._tool_manager, "call_tool", _canned_success)
        with _request_context(_app_context_double(recorder)):
            result = await _dispatch(mcp, tool_name, _MINIMAL_ARGS[tool_name])
        assert f"canned:{tool_name}" in _payload_text(result), (
            "the stub did not reach the caller, so this dispatch did not SUCCEED and the pin is "
            "not testing its own subject"
        )
        assert len(recorder.calls) == 1, (
            f"a SUCCESSFUL dispatch of {tool_name} wrote {len(recorder.calls)} trace rows, "
            f"expected exactly 1. Zero means the emission has a success-path hole for this tool — "
            f"the sibling error-leg battery cannot see it, because against a minimal app context "
            f"every built-in fails."
        )
        row = recorder.calls[0]
        assert row["tool"] == tool_name
        assert row["ok"] is True, (
            f"a dispatch that RETURNED recorded ok={row.get('ok')!r}; the latch must be True only "
            f"here, and it must be True here."
        )

    async def test_a_real_tools_declared_identity_is_harvested_too(
        self, traced_server: tuple[Any, _TraceRecorder], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """R6: tie the KEY rule to a REAL tool, not only to synthetic probes.

        Every identity leg drives a synthetic tool declaring ``agent``/``session``/
        ``action`` — deliberately, so this contract does not wait on the comms verbs
        (AC-17). But nothing then connected the rule to the params a REGISTERED tool
        actually declares. ``lore_comms`` declares ``agent`` and ``action``, and the
        coverage registry already dispatches it with both, so the tie costs one
        assertion: a build whose harvest works only for synthetic probe signatures
        fails here.

        Values deliberately DIFFER from every identity leg's (``coverage-probe`` /
        ``fleet`` vs ``auditor-q`` / ``drain``), so a build keyed on one value set
        cannot satisfy both.
        """
        mcp, recorder = traced_server

        async def _canned_success(
            name: str, arguments: dict[str, Any], **_kwargs: Any
        ) -> list[TextContent]:
            return [TextContent(type="text", text=f"canned:{name}")]

        monkeypatch.setattr(mcp._tool_manager, "call_tool", _canned_success)
        arguments = _MINIMAL_ARGS["lore_comms"]
        assert {"agent", "action"} <= set(arguments), (
            "this pin's premise is that the lore_comms coverage fixture declares agent+action; "
            "the fixture changed and the pin now proves nothing"
        )
        with _request_context(_app_context_double(recorder)):
            await _dispatch(mcp, "lore_comms", arguments)
        assert len(recorder.calls) == 1
        row = recorder.calls[0]
        assert row["agent"] == arguments["agent"], (
            f"the harvest missed a REAL tool's declared agent ({arguments['agent']!r}); it records "
            f"{row.get('agent')!r}. The rule is a PARAM-KEY rule — it must not depend on which "
            f"tool declared the key."
        )
        assert row["action"] == arguments["action"]

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
# MP-A — the seam drives the REAL store (the W30 hole)
# --------------------------------------------------------------------------- #
class TestADispatchLandsARealRowInTheRealTraceTable:
    """Every other seam pin points the emission at a DOUBLE. This one does not.

    **THE DEFECT THIS EXISTS TO CATCH (adversary W30, the blocker):** an emission
    that passes ONE keyword the real ``record_trace`` does not accept — an extra
    kwarg, a renamed kwarg, a value the engine refuses. Measured: such a build
    scores IDENTICALLY to a correct one against the rest of this contract
    (1 failed / 451 passed on the adversary's reference), because
    :class:`_TraceRecorder` accepts ``**fields`` and T5.1's ruled swallow turns the
    real ``TypeError`` into a log line. In production **every trace write would
    fail forever and ``traces.total`` would stay 0 — #147 reproduced by the packet
    that exists to close #147.**

    So the double is the right instrument for WHAT the seam records and the wrong
    instrument for WHETHER the store accepts it. Both legs here dispatch through
    the production ``FastMCP.call_tool`` with a REAL :class:`SurrealStore` behind
    the request's lifespan context, and read the row back with an explicit
    projection.

    The success leg AND the error leg both run: the swallow hides a rejection on
    either path, so a build whose kwargs are wrong only on the failure path (an
    ``ok=False`` row carrying an extra field, say) is invisible to the success leg
    alone.
    """

    async def test_a_successful_dispatch_lands_one_real_row(
        self, probe_server: tuple[Any, _TraceRecorder], trace_store: SurrealStore
    ) -> None:
        mcp, _double = probe_server
        with _request_context(_app_context_double_over(trace_store)):
            result = await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "end-to-end"})
        assert "silent:end-to-end" in _payload_text(result)
        rows = await _trace_rows(trace_store)
        assert len(rows) == 1, (
            f"the dispatch wrote {len(rows)} rows to the REAL trace table, expected 1. Zero means "
            f"the store REJECTED the emission's call and T5.1's swallow hid it — the whole tool "
            f"surface keeps working while telemetry is dead, which is #147's shape exactly. "
            f"Check the server log the swallow writes: a `TypeError: record_trace() got an "
            f"unexpected keyword argument …` here is a seam/store signature mismatch that NO "
            f"double-backed pin in this file can see."
        )
        row = rows[0]
        assert row["tool"] == _SYNTHETIC_SILENT
        assert row["ok"] is True
        assert isinstance(row["ordinal"], int) and not isinstance(row["ordinal"], bool), (
            f"the real row carries ordinal={row['ordinal']!r} — the store-side mint did not run."
        )
        assert re.fullmatch(r"[0-9a-f]{64}", str(row["params_hash"]))

    async def test_a_raising_dispatch_also_lands_one_real_row(
        self, probe_server: tuple[Any, _TraceRecorder], trace_store: SurrealStore
    ) -> None:
        mcp, _double = probe_server
        with _request_context(_app_context_double_over(trace_store)):
            with pytest.raises(ToolError):
                await _dispatch(mcp, _SYNTHETIC_RAISING, {})
        rows = await _trace_rows(trace_store)
        assert len(rows) == 1, (
            "the ERROR leg wrote no row to the REAL store. The failure path's own kwargs must be "
            "acceptable to the store too — a mismatch there is swallowed exactly like the success "
            "path's, and errored calls are part of the denominator packet 06 reads."
        )
        assert rows[0]["ok"] is False
        assert isinstance(rows[0]["ordinal"], int)

    async def test_every_REAL_registered_tool_lands_a_real_row(
        self,
        traced_server: tuple[Any, _TraceRecorder],
        trace_store: SurrealStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """MP-H: the last cell of the 2×2 — REAL registered tools into the REAL store.

        **THE DEFECT THIS EXISTS TO CATCH (adversary W33):** a bad kwarg supplied
        only for real tools —
        ``**({"request_id": "x"} if tool.startswith("lore_") else {})``. Measured at
        485 passed / 0 failed, identical to a correct build, because the coverage of
        "the seam's call is one the store ACCEPTS" had a hole:

        | | against the DOUBLE | against a REAL store |
        |---|---|---|
        | synthetic probe | every seam pin | the three MP-A legs |
        | real registered tool | MP-B + R6 | **nothing — W33 lived here** |

        Production outcome is the packet's worst: every real tool's write raises,
        T5.1's swallow logs it, ``traces.total`` stays 0 forever. #147 again.

        **This closes the cell ∀ TOOLS, not for one.** The prototype dispatched a
        single real tool (`lore_comms`); a build keyed on ONE name rather than the
        `lore_` prefix would walk through that. Sweeping the whole registry against
        ONE store costs a loop instead of 16 database mints — cheaper AND stronger
        than parametrising, and it makes the recorded tool set a checked variable
        again.

        Both mechanisms are reused unchanged: the tool manager is stubbed (MP-B's,
        so no tool body needs a full AppContext) and the request's lifespan context
        carries a REAL ``SurrealStore`` (MP-A's, so a rejected kwarg RAISES instead
        of being absorbed by a ``**fields`` double).
        """
        mcp, _double = traced_server

        async def _canned_success(
            name: str, arguments: dict[str, Any], **_kwargs: Any
        ) -> list[TextContent]:
            return [TextContent(type="text", text=f"canned:{name}")]

        monkeypatch.setattr(mcp._tool_manager, "call_tool", _canned_success)
        registry = sorted(_MINIMAL_ARGS)
        assert registry, "the coverage registry is empty — this pin would be vacuous"
        with _request_context(_app_context_double_over(trace_store)):
            for tool_name in registry:
                result = await _dispatch(mcp, tool_name, _MINIMAL_ARGS[tool_name])
                assert f"canned:{tool_name}" in _payload_text(result), (
                    f"the stub did not reach the caller for {tool_name}, so this dispatch did not "
                    f"SUCCEED and the loop is not testing its own subject"
                )

        rows = await _trace_rows(trace_store)
        landed = sorted(str(row["tool"]) for row in rows)
        assert landed == registry, (
            f"{len(rows)} of {len(registry)} dispatches landed a row in the REAL trace table.\n"
            f"  missing: {sorted(set(registry) - set(landed))}\n"
            f"  unexpected: {sorted(set(landed) - set(registry))}\n"
            f"A tool missing here means the REAL store REJECTED the emission's call for THAT tool "
            f"and T5.1's swallow hid it — the double-backed coverage battery cannot see it, and "
            f"neither can the synthetic-probe real-store legs. Check the server log for a "
            f"`TypeError: record_trace() got an unexpected keyword argument …`."
        )
        assert all(row["ok"] is True for row in rows), (
            f"a stubbed-success dispatch recorded ok False: "
            f"{[row['tool'] for row in rows if row['ok'] is not True]}"
        )
        assert all(isinstance(row["ordinal"], int) for row in rows), (
            "a real row is missing its store-side ordinal mint"
        )

    async def test_every_REAL_registered_tool_that_FAILS_lands_a_real_row(
        self,
        traced_server: tuple[Any, _TraceRecorder],
        trace_store: SurrealStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """MP-I: the last cell — REAL tools × ERROR path × REAL store.

        **THE DEFECT THIS EXISTS TO CATCH (adversary D9b), and why the binder does
        not:** a LEGAL keyword carrying a WRONG-TYPED value, read out of
        ``arguments.get("depth", 7)`` — so its static type is ``Any`` and
        **mypy reports no issues**, while ``Signature.bind`` checks names and arity
        and never types. Measured surviving at 490 passed / 0 failed with the type
        gate clean. Only the ENGINE rejects it, and only on a path some pin actually
        dispatches. The success path is covered by MP-H; this is its error twin.

        Six lines, reusing MP-H's mechanism exactly — the registry loop, one real
        store, the recorded set asserted EQUAL to the registry — with a RAISING
        stub. It closes the NAME family in this cell too (D4 dies here as well).

        ⚠ The stub raises ``ToolError``, deliberately: that is the shape the REAL
        tool manager surfaces, and it is what ``_dispatch_ignoring_tool_failure``
        suppresses. A ``RuntimeError`` stub escapes the dispatch and the probe fails
        for its own reason — the adversary hit exactly that on its first run of this
        prototype and disclosed it, which is the same "a pin is not a pin until it
        has been run" lesson this wave has now paid for on both sides.
        """
        mcp, _double = traced_server

        async def _canned_failure(name: str, arguments: dict[str, Any], **_kwargs: Any) -> None:
            raise ToolError(f"canned failure for {name}")

        monkeypatch.setattr(mcp._tool_manager, "call_tool", _canned_failure)
        registry = sorted(_MINIMAL_ARGS)
        assert registry, "the coverage registry is empty — this pin would be vacuous"
        with _request_context(_app_context_double_over(trace_store)):
            for tool_name in registry:
                await _dispatch_ignoring_tool_failure(mcp, tool_name, _MINIMAL_ARGS[tool_name])

        rows = await _trace_rows(trace_store)
        landed = sorted(str(row["tool"]) for row in rows)
        assert landed == registry, (
            f"{len(rows)} of {len(registry)} FAILING dispatches landed a row in the REAL trace "
            f"table.\n  missing: {sorted(set(registry) - set(landed))}\n"
            f"A tool missing here means the real store REJECTED the emission's call on the ERROR "
            f"path for that tool — a wrong-TYPED value (invisible to both `bind()` and mypy) or a "
            f"failure-path-only bad keyword. The errored population is part of the denominator "
            f"packet 06 reads, so losing it silently biases the curve toward healthy sessions."
        )
        assert all(row["ok"] is False for row in rows), (
            f"a FAILING dispatch recorded ok True: "
            f"{[row['tool'] for row in rows if row['ok'] is not False]}"
        )

    async def test_the_declared_identity_reaches_the_real_row(
        self, probe_server: tuple[Any, _TraceRecorder], trace_store: SurrealStore
    ) -> None:
        # The enrichment columns are the NEW half of the store contract, so the
        # end-to-end leg must carry them: a build whose declared-identity kwargs
        # are individually wrong (a rename, a typo) is otherwise only ever checked
        # against a double that accepts anything.
        mcp, _double = probe_server
        with _request_context(_app_context_double_over(trace_store)):
            await _dispatch(
                mcp,
                _SYNTHETIC_DECLARING,
                {"agent": _DECLARED_AGENT, "session": _DECLARED_SESSION, "action": _DECLARED_ACTION},
            )
        rows = await _trace_rows(trace_store)
        assert len(rows) == 1
        row = rows[0]
        assert row["agent"] == _DECLARED_AGENT
        assert row["session"] == _DECLARED_SESSION
        assert row["action"] == _DECLARED_ACTION
        assert row["transport_session"] == _TRANSPORT_SESSION_ID
        assert row["hit_count"] is None, (
            "the seam must leave hit_count unset even at the store: a fabricated 0 makes every "
            "aggregate over the column lie."
        )


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
        # Kills a build reporting 0, or reporting SECONDS, or measuring after the
        # emission rather than around the tool call.
        #
        # ⚠ It does NOT kill a CONSTANT. This comment used to claim it did, and the
        # claim was false: any constant inside the bracket (a literal 50.0 against
        # a 50 ms fixture) passes — measured by the adversary, with the
        # perturbation control proving the pin discriminates only at its own
        # fixture value. A failure message or comment promising a check the
        # assertion does not perform is a FALSE GATE, so the claim is corrected
        # here rather than left to be inherited. The constant is killed by
        # `test_two_dispatches_of_different_durations_record_different_latencies`,
        # which is fixture-INDEPENDENT by construction.
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

    async def test_two_dispatches_of_different_durations_record_different_latencies(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        """MP-D: a CONSTANT latency dies here, at any fixture value.

        **THE DEFECT THIS EXISTS TO CATCH:** ``latency_ms = 50.0``. It survived the
        bracket pin above — 50 sits inside `45 ≤ latency ≤ elapsed+5` — and shipped
        a build where every row reports the same duration, so no percentile, no
        slow-tool ranking and no "did the trace write add latency" measurement (T5's
        own named re-open trigger) means anything.

        This pin is fixture-INDEPENDENT by construction: it compares TWO dispatches
        of DIFFERENT real durations in one request context and asserts the recorded
        values differ by at least half the sleep. No single constant can satisfy a
        DIFFERENCE, whatever the fixture value is — which is the property the
        bracket could not have, since a bracket is a statement about one value.
        """
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "fast"})
            await _dispatch(mcp, _SYNTHETIC_SLOW, {})
        assert len(recorder.calls) == 2, f"expected two traced dispatches, got {len(recorder.calls)}"
        fast_ms, slow_ms = (float(row["latency_ms"]) for row in recorder.calls)
        # CONTROL that the fixture pair really differs in duration: the slow probe
        # sleeps and the fast one does not, so a failure here is the MEASUREMENT,
        # not the fixture.
        floor_ms = _SLOW_TOOL_SECONDS * 1000 * _LATENCY_DIFFERENCE_FRACTION
        assert slow_ms - fast_ms >= floor_ms, (
            f"the slow dispatch recorded {slow_ms}ms and the fast one {fast_ms}ms — a difference of "
            f"{slow_ms - fast_ms}ms, under the {floor_ms}ms floor. A CONSTANT (or a value measured "
            f"outside the tool call) cannot produce a difference; a real measurement cannot avoid "
            f"one, since the slow probe sleeps {_SLOW_TOOL_SECONDS * 1000}ms and the fast probe "
            f"returns immediately."
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
        """⚠ KNOWN BOUND (blind-audit D1, measured 2026-07-25 at `7574edc`) — this
        pin is NARROW, not false, and a reader who trusts it broadly is the reason
        D1 shipped.

        WHAT IT COVERS: the ``asyncio.Task.cancel`` shape. asyncio cancellation is
        EDGE-triggered — the ``CancelledError`` is delivered once, at the await it
        interrupts — so a later await inside ``finally`` runs normally, and this
        pin genuinely proves the write is not placed in an ``except``/success arm.

        WHAT IT PROVABLY DOES NOT COVER, and this is the half that cost a defect:
        an emission that SUSPENDS, under a LEVEL-triggered anyio cancel scope,
        which is what MCP actually cancels a request with. Two independent
        reasons it cannot see that world:

        1. It cancels the wrong way. anyio scopes re-raise at EVERY subsequent
           await inside the scope; ``Task.cancel`` does not.
        2. :class:`_TraceRecorder` never awaits — it binds a signature and appends
           to a list. A cancellation is only delivered at a task's next SUSPENSION
           POINT, so a non-suspending emission completes whether it is shielded or
           not. ``SurrealStore.record_trace`` is a network round-trip and ALWAYS
           suspends, so production is the one shape this double cannot model.

        MEASURED RECEIPT, not inferred: with
        ``anyio.CancelScope(shield=True)`` REMOVED from ``TracingFastMCP.call_tool``
        — i.e. against the exact build blind-D1 describes, where a cancelled call
        writes NO row — this pin stays **GREEN**. The four cells:

        | emission suspends | shielded | row |
        |---|---|---|
        | no  | no  | WRITTEN  <- this pin lives here |
        | no  | yes | WRITTEN |
        | yes | no  | **LOST**  <- production's shape |
        | yes | yes | WRITTEN |

        THE DISCRIMINATING PIN is
        :meth:`TestTheEmissionSurvivesANYIOsLevelTriggeredCancellation.
        test_a_scope_cancelled_dispatch_STILL_writes_its_row`, which drives a real
        anyio cancel scope through :class:`_SuspendingTraceRecorder`. Removing the
        shield turns THAT one RED while leaving this one green — and that
        asymmetry is the finding, not a flake.

        RE-OPEN TRIGGER: if :class:`_TraceRecorder` ever gains a suspension point,
        or the emission's placement changes, re-derive this bound — it may then
        cover more than it does today, and a stale KNOWN BOUND is its own defect.
        Do not "fix" this pin by pointing it at the suspending recorder: the
        asyncio-cancel shape is worth keeping pinned on its own.
        """
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


class TestTheEmissionSurvivesANYIOsLevelTriggeredCancellation:
    """FIX WAVE — blind-audit D1, the BLOCKING half of the pair.

    The sibling class above cancels through ``asyncio.Task.cancel``, which is
    EDGE-triggered: the ``CancelledError`` is delivered once, at the await it
    interrupts, and a later await inside ``finally`` runs normally. That is why
    it passed against an UNSHIELDED emission — and it is not the mechanism
    production uses.

    **MCP cancels through an anyio cancel scope** (``RequestResponder.cancel``
    -> ``self._cancel_scope.cancel()``), and anyio scopes are LEVEL-triggered:
    once cancelled, EVERY subsequent await inside the scope raises immediately,
    and a ``finally`` block is not exempt. Under that mechanism an unshielded
    emission writes NO row for exactly the population ``ok=False`` exists to
    measure; the ``CancelledError`` is a ``BaseException`` the seam's
    ``except Exception`` never logs; and it REPLACES whatever exception the tool
    was already unwinding. The class docstring claimed the opposite as its
    load-bearing justification.

    So this drives the REAL production mechanism, not a convenient one.

    MUTATION-PROOF OBLIGATION: remove ``anyio.CancelScope(shield=True)`` from
    the emission -> the cancelled leg goes RED (no row) while the sibling
    asyncio-cancel pin stays GREEN. That asymmetry IS the finding.
    """

    async def test_a_scope_cancelled_dispatch_STILL_writes_its_row(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, _plain = probe_server
        recorder = _SuspendingTraceRecorder()
        with _request_context(_app_context_double(recorder)):
            # ``move_on_after`` is a real anyio cancel scope with a deadline —
            # the same construct MCP cancels a request with, and it swallows the
            # cancellation at its own boundary so the assertions below can run.
            with anyio.move_on_after(_CANCEL_AFTER_SECONDS):
                await _dispatch(mcp, _SYNTHETIC_BLOCKING, {})
        assert len(recorder.calls) == 1, (
            "a dispatch cancelled through an ANYIO cancel scope wrote no trace row. anyio "
            "scopes are level-triggered, so the `finally`'s own await raises too — the "
            "emission must be SHIELDED, or the timed-out population (precisely what ok=False "
            "measures) is silently absent and nothing logs it."
        )
        assert recorder.calls[0]["tool"] == _SYNTHETIC_BLOCKING
        assert recorder.calls[0]["ok"] is False, (
            f"the scope-cancelled dispatch recorded ok={recorder.calls[0].get('ok')!r}; the "
            f"success latch must leave it False."
        )

    async def test_positive_control_the_SAME_scope_uncancelled_records_ok_true(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        """Without this, a build that always wrote ``ok=False`` — or a probe that
        never actually cancelled — would satisfy the leg above."""
        mcp, _plain = probe_server
        recorder = _SuspendingTraceRecorder()
        with _request_context(_app_context_double(recorder)):
            with anyio.move_on_after(_BLOCKING_TOOL_SECONDS):
                result = await _dispatch(mcp, _SYNTHETIC_SILENT, {"marker": "uncancelled"})
        assert "silent:uncancelled" in _payload_text(result)
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["ok"] is True

    async def test_the_shielded_write_is_BOUNDED(self) -> None:
        """The shield must not be able to hold a dying request open forever. The
        bound is a named constant, DERIVED here rather than written as a literal,
        and it must sit above the store's own conflict-retry deadline (a healthy
        but contended write must not be cut short and silently lost)."""
        from loremaster.server import _TRACE_EMIT_TIMEOUT_SECONDS
        from loremaster.store._txn import _TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS

        assert _TRACE_EMIT_TIMEOUT_SECONDS > _TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS, (
            "the emission's timeout is at or below the shared retry driver's own deadline, so "
            "a contended-but-healthy trace write is cut short and lost"
        )
        assert _TRACE_EMIT_TIMEOUT_SECONDS <= 30, (
            "an unbounded-in-practice shield defeats the point: a cancelled request would be "
            "held open by its own telemetry"
        )


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


class TestTheCallerCONTROLLEDStringsOnTheWritePathAreBounded:
    """WAVE 3 / blind D4 — the write side of the bound the read side already had.

    Four strings reach a trace row VERBATIM and none of them is ours: the
    dispatched ``tool`` name and the three declared-identity arguments. The
    unknown-tool case is reachable and the diff's own comment says so — the
    dispatch fails INSIDE the funnel and the write sits in a ``finally``, so the
    row is written before the failure surfaces.

    The design wave bounded message pointers with the argument that *"a 2000-char
    'ref' is a BODY wearing a pointer's name — without it the body cap is
    theatre"*. The same argument applies here and the same wave left this side
    open: the window and the display cap bound the served CARDINALITY and nothing
    else, so on a quiet instance a 100 KB tool name ranks inside the top 20 and is
    served straight into the next consumer's status response.

    ⚠ The POLICY differs from the message pointers on purpose — TRUNCATE, not
    REJECT — and the pins below pin that difference rather than assuming it: a
    refused trace row would let a caller SUPPRESS ITS OWN MEASUREMENT and would
    lose a denominator row. A truncated group key is still a usable group key.
    """

    async def test_an_oversize_TOOL_name_is_truncated_and_the_row_STILL_LANDS(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, recorder = probe_server
        oversize = "t" * (TRACE_IDENTITY_MAX_CHARS + 500)
        with suppress(Exception):
            await _dispatch_ignoring_tool_failure(mcp, oversize, {})
        with _request_context(_app_context_double(recorder)):
            with suppress(Exception):
                await _dispatch_ignoring_tool_failure(mcp, oversize, {})
        assert len(recorder.calls) == 1, (
            "an UNKNOWN tool name wrote no trace row. The dispatch fails inside the funnel and "
            "the write is in `finally`, so the row must still land — losing it would let a "
            "caller suppress its own measurement, and errored calls are part of the denominator"
        )
        served = recorder.calls[0]["tool"]
        assert len(served) == TRACE_IDENTITY_MAX_CHARS, (
            f"the tool name was stored at {len(served)} chars, not bounded to "
            f"{TRACE_IDENTITY_MAX_CHARS} — one client calling a 100 KB 'tool' writes a "
            f"full-size row per call, forever"
        )
        assert served == oversize[:TRACE_IDENTITY_MAX_CHARS], (
            "the bound is not a plain prefix, so two different names could collapse "
            "unpredictably rather than deterministically"
        )

    async def test_oversize_DECLARED_identities_are_truncated(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        mcp, recorder = probe_server
        oversize = "a" * (TRACE_IDENTITY_MAX_CHARS + 500)
        with _request_context(_app_context_double(recorder)):
            await _dispatch(
                mcp,
                _SYNTHETIC_DECLARING,
                {"agent": oversize, "session": oversize, "action": oversize},
            )
        assert len(recorder.calls) == 1
        row = recorder.calls[0]
        for key in ("agent", "session", "action"):
            assert len(str(row[key])) == TRACE_IDENTITY_MAX_CHARS, (
                f"declared {key!r} was stored unbounded at {len(str(row[key]))} chars — these "
                f"are RAW ARGUMENT VALUES and the diff stores them plaintext by design"
            )

    async def test_POSITIVE_CONTROL_a_normal_name_is_stored_UNCHANGED(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        """Without this, a build that truncated everything to one character — or
        mangled every value — satisfies both legs above."""
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(
                mcp,
                _SYNTHETIC_DECLARING,
                {"agent": _DECLARED_AGENT, "session": _DECLARED_SESSION, "action": _DECLARED_ACTION},
            )
        assert len(recorder.calls) == 1
        row = recorder.calls[0]
        assert row["tool"] == _SYNTHETIC_DECLARING
        assert row["agent"] == _DECLARED_AGENT
        assert row["session"] == _DECLARED_SESSION
        assert row["action"] == _DECLARED_ACTION

    @pytest.mark.parametrize(
        "column", ["tool", "session", "agent", "action", "transport_session"]
    )
    def test_each_caller_controlled_column_carries_its_STORE_backstop(self, column: str) -> None:
        """The writer truncates; the ASSERT is what stops a writer that does not.
        Pins the EMITTED statement, per the house idiom."""
        statement = _field_statement(generate_ddl(dim=_DIM), TRACE_TABLE, column)
        assert f"ASSERT string::len($value) <= {TRACE_IDENTITY_MAX_CHARS}" in statement, (
            f"trace.{column} has no store-level bound, so any writer that skips the "
            f"truncation stores an unbounded caller-controlled string: {statement!r}"
        )

    def test_CONTROL_a_NON_caller_controlled_column_carries_NO_such_bound(self) -> None:
        """The scope is caller-controlled STRINGS. ``params_hash`` is ours — a
        fixed-width digest — so bounding it would be cargo-culting the rule
        rather than applying it, and this pin says which columns are in scope by
        showing one that is not."""
        statement = _field_statement(generate_ddl(dim=_DIM), TRACE_TABLE, "params_hash")
        assert "ASSERT" not in statement, (
            f"params_hash gained a bound it does not need — it is a 64-char digest this code "
            f"computes, not a caller-supplied string: {statement!r}"
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
    """T6: one deterministic digest over the RAW arguments.

    ⚠ WAVE 3 — THIS DOCSTRING CERTIFIED THE OLD WORLD. It used to say the digest
    was *"the ONLY thing that crosses from arguments into the row … the whole
    privacy boundary"*. That is FALSE and was already false when it was written:
    ``_TRACE_DECLARED_KEYS`` (``agent``/``session``/``action``) are stored
    PLAINTEXT, by design, because an identity that is hashed is an identity
    packet 06 cannot group by. The production docstring was corrected in the fix
    wave and this copy was not — the exact "tests written before a semantic
    change certify the OLD world" shape, in a class named ``…LeaksNothing``,
    retrievable by an agent asking whether the trace row leaks arguments.

    WHAT THE PINS BELOW ACTUALLY ASSERT, which is true and worth keeping: FREE
    TEXT — bodies, briefs, queries, notes — reaches the row ONLY as this digest.
    The no-raw-content leg checks hostile BODY fragments specifically, with a
    present-in-input control, and that is the boundary that matters.
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

    async def test_a_zero_argument_call_still_records_the_full_digest(
        self, probe_server: tuple[Any, _TraceRecorder]
    ) -> None:
        """MP-E: the empty-arguments case is a REAL production shape, not an edge.

        **THE DEFECT THIS EXISTS TO CATCH:** ``if not arguments: return ""``. Four
        REGISTERED tools are dispatched with ``{}`` — ``lore_map``, ``lore_index``,
        ``lore_diff``, ``lore_dead_code`` — so that build gives all four rows an
        empty digest and collapses them into ONE bucket for every per-call
        aggregate. It survived this contract: every other recipe leg passes a
        non-empty dict, which is the guarded-not-∀ shape (guarded by NON-EMPTY
        ARGUMENTS).

        The digest of ``{}`` is a real 64-hex value — ``sha256(b"{}")`` — so
        "there was nothing to hash" is not a defence.
        """
        mcp, recorder = probe_server
        with _request_context(_app_context_double(recorder)):
            await _dispatch(mcp, _SYNTHETIC_NO_ARGS, {})
        assert len(recorder.calls) == 1
        served = recorder.calls[0]["params_hash"]
        assert re.fullmatch(r"[0-9a-f]{64}", str(served)), (
            f"a zero-argument dispatch recorded params_hash={served!r}. The T6 recipe over an "
            f"EMPTY dict is a full digest, not a sentinel: four registered tools take no "
            f"arguments, and an empty digest collapses all of them into one bucket."
        )
        assert served == _expected_params_hash({}), (
            "the zero-argument digest is not the recipe's own value for `{}` — a special case has "
            "been introduced where the recipe needs none."
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
        for fragment in _HOSTILE_FRAGMENTS:
            # CONTROL FIRST (R4): a fragment that is not IN the hostile input cannot
            # be absent-from-the-row for any interesting reason — it is a vacuous
            # element inside a forall-loop, and this file shipped exactly one
            # (`"row-shaped"`, which never occurred in _HOSTILE_BODY). Asserting
            # presence in the INPUT before absence in the OUTPUT makes every
            # iteration load-bearing.
            assert fragment in _HOSTILE_BODY, (
                f"{fragment!r} is not in the hostile body, so asserting its absence from the row "
                f"proves nothing. Fix the fragment list or the fixture — a vacuous element in a "
                f"forall-loop is decoration that reads as coverage."
            )
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
