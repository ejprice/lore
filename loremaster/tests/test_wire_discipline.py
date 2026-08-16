"""RETIRED by packet 59 (fastmcp 3.x migration) — the R16 wire-only invariant's PREMISE dissolved.

Design ``docs/design/2026-08-15-fastmcp-3x-migration.md`` §4 + §7. This file is a
SUPERSEDED-HEADER TOMBSTONE (per the design's "rewrite … OR delete with an explicit
superseded-header if 39 re-authors it"): its content is retired but the address resolves, so a
future reader meets the retirement DELIBERATELY rather than rediscovering it from a green test
that certifies a corpse.

────────────────────────────────────────────────────────────────────────────────────────────
WHY IT IS RETIRED

The invariant killed ONE defect class: ``FastMCP.__init__`` (the **mcp SDK's** bundled FastMCP)
calls ``_setup_handlers``, which binds the BOUND method (``self.call_tool``, ``self.list_tools``,
…) with the low-level server at construction — so anything installed afterward as an instance
attribute is live in-process and DEAD ON THE WIRE (WB30/WB48/WB93, three waves, one root cause).
The whole file — including ``_auth_fixtures.sdk_bound_handler_names()``, which AST-parses
``mcp.server.fastmcp.FastMCP._setup_handlers`` — is DERIVED from that construction-time binding.

Packet 59 swaps lore's façade to standalone ``fastmcp`` 3.x, whose dispatch has **no
``_setup_handlers``** and routes tools through a middleware chain. So:

* the ``sdk_bound_handler_names()`` derivation now reads handler names off a class lore **no
  longer uses** (``mcp.server.fastmcp`` survives only transitively) — a stale referent, the exact
  "tests written before a semantic change certify the OLD world" hazard;
* the construction-time-binding root cause this file mechanised against is **GONE**.

────────────────────────────────────────────────────────────────────────────────────────────
WHAT REPLACES IT — AND WHO OWNS THAT (design §7, blast-radius §7.3 CANNOT-carry-#2)

The CONCERN survives the mechanism: fastmcp middleware **reintroduces placement as a free
variable** (the WB48 class — a middleware that observes/refuses AFTER the tool body ran). So a
wire-only discipline is still load-bearing — but it must be RE-EXPRESSED against the middleware
dispatch contract, over packet-39's posture modules, which do not exist yet (they are 39's
committed-RED pending files). Per design §7, **packet 39 re-expresses** the wire-only invariant
(and re-cuts the R16 ``_setup_handlers`` AST pins that share the retired derivation).

RE-OPEN TRIGGER: packet 39's build. When 39 authors its read-only posture modules on the
``on_call_tool`` / ``on_list_tools`` middleware substrate this migration delivers, it re-expresses
this guard — a receiver-blind AST scan forbidding an in-process middleware/handler invocation in a
posture module — deriving its handler/hook set from fastmcp's dispatch, never a hand-list.

The MIGRATION-side placement guard (the trace middleware must be INSTALLED at the one site, not
merely defined) lives in ``test_fastmcp_migration.py::TestTheTraceMiddlewareIsInstalledAtTheOneFunnel``
with its mutation obligation (design D7) — that is packet 59's half of the same concern.

⚠ DECISION SURFACED TO THE OPERATOR (F4): this tombstone is the RECOMMENDED fate
(delete-with-superseded-header). The alternative is an immediate rewrite against the middleware
dispatch contract — premature, because 39's posture modules are not built. If the operator prefers
the rewrite, or prefers to leave the (now-stale-derivation) invariant in place until 39 lands,
this file changes accordingly.
"""

from __future__ import annotations

import importlib

import pytest


def test_the_tracing_subclass_whose_construction_binding_this_guard_mechanised_is_retired() -> None:
    """The anti-regression half of the tombstone (design M3): the retired referent stays retired.

    This guard's entire rationale was the mcp-SDK ``FastMCP`` subclass (``TracingFastMCP``) whose
    ``call_tool`` override was live-on-wire BY CONSTRUCTION via ``_setup_handlers``. Packet 59
    retires that subclass in favour of an ``on_call_tool`` middleware. If a later change re-adds a
    ``FastMCP`` subclass that binds behaviour at construction, this invariant's premise is back and
    a real (re-expressed) wire-only guard is owed again — this pin goes RED to say so.
    """
    server = importlib.import_module("loremaster.server")
    assert not hasattr(server, "TracingFastMCP"), (
        "loremaster.server.TracingFastMCP is back. Packet 59 retired the subclass (design M3) — "
        "its call_tool override is now an on_call_tool middleware. A returned FastMCP subclass "
        "re-introduces the construction-time-binding class this wire-only discipline existed to "
        "police; re-express the guard for the middleware world (design §7) rather than reviving "
        "this derivation, which reads handler names off a class lore no longer uses."
    )


@pytest.mark.skip(
    reason="RETIRED by packet 59 — the wire-only discipline is re-expressed by packet 39 over the "
    "middleware substrate (design §7). See this module's superseded-header docstring."
)
def test_wire_only_discipline_is_re_expressed_by_packet_39() -> None:
    """Placeholder recording the hand-off, kept visible so the guard is not silently absent."""
