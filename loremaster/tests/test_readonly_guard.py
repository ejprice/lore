"""CONTRACT (contract-39-w23) — the read-only-hosted enforcement guard (design §7 / §13 g4).

⚠ TWO HALVES, and only the STRUCTURAL half is in this file today:

* **STRUCTURAL (here, now):** ``ReadOnlyGuardMiddleware`` is a fastmcp ``Middleware`` that
  OVERRIDES BOTH ``on_list_tools`` (the INVISIBLE leg) AND ``on_call_tool`` (the REFUSE leg). A
  build that implements only the refusal (leaving mutating tools VISIBLE in ``tools/list``) is
  the #295 structural-leg omission these pins catch.

* **WIRE / #295 EFFECT (deferred — contract ESC-1):** the substance of enforcement — every
  mutating tool refused AND body-NEVER-run for every hosted principal, ``served ∩ refused = ∅``
  on the wire, the guard's reach == the registry, one annotation flip moving a tool across
  guard+list+render, and the read-only positive control — can ONLY be observed on the REAL wire
  (get_access_token supplies the ambient principal; the #295 law is that a proxy/exception
  observation cannot distinguish a guard that refuses BEFORE ``call_next`` from one that runs the
  body THEN refuses — WB48). Driving that wire needs the RECUT hosted ``wire_session`` harness
  (the stale one emits ``mode: "google_oauth"``, invalid under the recut ``AuthConfig``, and
  admits via a roster file, not the principal DB). That harness recut is contract ESC-1; the wire
  pins are authored against it once it lands (their exact assertions are spec'd in
  ``REPORT-contract-39-w23.md`` §Deferred-wire-pins). Partition CLASSIFICATION itself is already
  pinned (``test_mutating_set_derivation.py`` / ``test_tool_allowlist.py`` / ``test_mcp_server.py``)
  — this file does not duplicate it.

CONTRACT-FIRST: the structural pins are GREEN-now GUARDS (they redden on a build that drops the
visibility hook or the Middleware base). The stub's hooks raise ``NotImplementedError`` (the
enforcement BEHAVIOUR is builder GREEN work); the structural pins assert only the class SHAPE.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _auth_fixtures import wire_session
from _refusal_effect import assert_tool_refused_and_did_not_run
from fastmcp.server.middleware import Middleware
from loremaster.readonly_guard import ReadOnlyGuardMiddleware
from mcp.types import ToolAnnotations

# Synthetic probe tools registered via ``wire_session(prepare=…)`` — the #295 pattern
# (``test_refusal_observes_effect``): the composed server's real built-ins need the live
# AppContext (stubbed in the wire harness), so a synthetic tool is how the guard's EFFECT is
# observed on the wire. A synthetic MUTATING tool (``readOnlyHint=False``) is ALSO the
# coverage/reach check: it is not one of the 6 built-in mutating names, so a guard that refuses
# it proves the reach is DERIVED from the registry (``partition_tools_by_posture``), not a
# hand-list of known built-ins (#344/#345).
_SYNTH_MUTATING = "lore_probe_synth_mutating_w23"
_SYNTH_READ_ONLY = "lore_probe_synth_read_only_w23"
# The DENY-BY-DEFAULT probe (adversary-39-w23 #2): a tool whose ``readOnlyHint`` is None
# (UNCLASSIFIED). ``partition_tools_by_posture`` keys on ``readOnlyHint is not True`` (server.py:
# 10451), so None → mutating → DENIED. A hand-rolled ``readOnlyHint is False`` guard ADMITS it
# (None is not False), so pinning it refused+invisible reds that wrong build.
_SYNTH_UNCLASSIFIED = "lore_probe_synth_unclassified_w23"
_BODY_RAN_MARKER = "SYNTH-BODY-RAN-W23"


@dataclass
class _EffectCounters:
    """Per-tool invocation counters — ``0`` means the guarded body never ran (the #295 EFFECT)."""

    mutating: int = 0
    read_only: int = 0
    unclassified: int = 0


def _register_synth_tools(counters: _EffectCounters) -> Any:
    """A ``prepare`` callback registering synthetic mutating + read-only + UNCLASSIFIED tools."""

    def _prepare(mcp: Any) -> None:
        def synth_mutating() -> str:
            counters.mutating += 1
            return _BODY_RAN_MARKER

        def synth_read_only() -> str:
            counters.read_only += 1
            return _BODY_RAN_MARKER

        def synth_unclassified() -> str:
            counters.unclassified += 1
            return _BODY_RAN_MARKER

        mcp.tool(
            name=_SYNTH_MUTATING,
            annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=False),
        )(synth_mutating)
        mcp.tool(
            name=_SYNTH_READ_ONLY,
            annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
        )(synth_read_only)
        # readOnlyHint LEFT UNSET (None) — the deny-by-default probe.
        mcp.tool(
            name=_SYNTH_UNCLASSIFIED,
            annotations=ToolAnnotations(openWorldHint=False),
        )(synth_unclassified)

    return _prepare


class TestReadOnlyGuardMiddlewareShape:
    def test_the_guard_is_a_fastmcp_middleware(self) -> None:
        # It must be a fastmcp ``Middleware`` so it composes into the ``middleware=[…]`` chain and
        # runs on the wire. WRONG BUILD: an ASGI wrapper (the retired BearerAuthMiddleware shape)
        # or a plain class — it would never be invoked by the fastmcp dispatch.
        assert issubclass(ReadOnlyGuardMiddleware, Middleware)

    def test_the_guard_overrides_both_the_list_and_call_hooks(self) -> None:
        # BOTH legs are required and fail independently: ``on_list_tools`` makes a mutating tool
        # INVISIBLE in tools/list (the #295 structural leg), ``on_call_tool`` REFUSES a direct
        # call (the #295 EFFECT leg). WRONG BUILD THIS CATCHES: a guard that overrides only
        # ``on_call_tool`` — it refuses a call but leaves the mutating tools listed (a hosted
        # principal still SEES them, and a served∩refused=∅ pin would redden on the wire).
        own = vars(ReadOnlyGuardMiddleware)
        assert "on_list_tools" in own, (
            "ReadOnlyGuardMiddleware must OVERRIDE on_list_tools (the invisibility leg) — "
            "inheriting the base pass-through leaves mutating tools visible in tools/list"
        )
        assert "on_call_tool" in own, (
            "ReadOnlyGuardMiddleware must OVERRIDE on_call_tool (the refusal / #295 EFFECT leg)"
        )


class TestReadOnlyGuardOnTheHostedWire:
    """The #295 EFFECT + coverage + served∩refused on the REAL recut hosted wire (§13 g4).

    ⚠ These drive the recut ``wire_session(posture="hosted")`` — the composed app authenticating a
    real member principal (admitted against a throwaway principal DB, design §9 R12; NO role axis —
    every hosted principal is read-only this packet). Against the STUB composition (``FastMCP(auth=…)``
    not yet wired; the pre-recut ``build_asgi_app`` still ships ``BearerAuthMiddleware``) the hosted
    ``initialize`` is refused (401), so these are RED by the wire failing to establish until the
    builder's composition lands — GREEN once the composition authenticates the member AND the guard
    refuses the mutating surface. (This is why the substance of enforcement is a WIRE pin: the #295
    law is that a proxy/exception observation cannot distinguish refuse-before-``call_next`` from
    run-body-then-refuse; only the effect on the real wire can.)
    """

    async def test_a_hosted_mutating_tool_is_refused_and_its_body_never_runs(
        self, tmp_path: Path
    ) -> None:
        # THE #295 EFFECT pin AND the coverage/reach check in one: a SYNTHETIC mutating tool (not a
        # known built-in) is refused to a hosted member AND its body never runs (counter == 0). The
        # refusal names the refused tool (Consumer Law: "posture name, tool name, why"), so the
        # tool name is the refusal marker. WRONG BUILD THIS CATCHES: WB48 — a guard that runs the
        # body THEN refuses (identical refusal text, counter == 1); AND a guard whose reach is a
        # hand-list of the 6 built-ins (it would never refuse this synthetic tool).
        counters = _EffectCounters()
        async with wire_session(
            tmp_path,
            posture="hosted",
            principal="google",
            prepare=_register_synth_tools(counters),
        ) as wire:
            await assert_tool_refused_and_did_not_run(
                wire.call,
                _SYNTH_MUTATING,
                {},
                effect_count=lambda: counters.mutating,
                refusal_marker=_SYNTH_MUTATING,
            )

    async def test_an_unclassified_tool_is_denied_by_default_for_a_hosted_member(
        self, tmp_path: Path
    ) -> None:
        # DENY-BY-DEFAULT (adversary-39-w23 #2): a tool whose readOnlyHint is None (UNCLASSIFIED)
        # is refused AND its body never runs for a hosted member — because the partition keys on
        # `readOnlyHint is not True` (None → mutating), NOT `is False`. WRONG BUILD THIS CATCHES: a
        # hand-rolled `readOnlyHint is False` guard, which ADMITS the None tool (None is not False)
        # — it passes every OTHER enforcement pin (they use readOnlyHint=False tools) and only
        # THIS one reds it. Same deny-by-default reach law the guard's coverage serves.
        counters = _EffectCounters()
        async with wire_session(
            tmp_path,
            posture="hosted",
            principal="google",
            prepare=_register_synth_tools(counters),
        ) as wire:
            await assert_tool_refused_and_did_not_run(
                wire.call,
                _SYNTH_UNCLASSIFIED,
                {},
                effect_count=lambda: counters.unclassified,
                refusal_marker=_SYNTH_UNCLASSIFIED,
            )
            assert _SYNTH_UNCLASSIFIED not in await wire.served_tool_names(), (
                "an unclassified (readOnlyHint=None) tool must also be INVISIBLE (deny-by-default)"
            )

    async def test_served_intersection_refused_is_empty_for_a_hosted_member(
        self, tmp_path: Path
    ) -> None:
        # served ∩ refused = ∅ on the wire: the synthetic MUTATING tool is INVISIBLE in tools/list
        # for a hosted member, while the synthetic READ-ONLY tool is VISIBLE (every listed tool is
        # callable, every refused tool is unlisted). WRONG BUILD: a guard that refuses calls but
        # does not filter the list (the mutating tool stays visible) — the #295 structural leg.
        counters = _EffectCounters()
        async with wire_session(
            tmp_path,
            posture="hosted",
            principal="google",
            prepare=_register_synth_tools(counters),
        ) as wire:
            served = await wire.served_tool_names()
        assert _SYNTH_MUTATING not in served, "a mutating tool must be INVISIBLE to a hosted member"
        assert _SYNTH_READ_ONLY in served, "a read-only tool must remain VISIBLE to a hosted member"

    async def test_a_read_only_tool_is_visible_and_its_body_runs(self, tmp_path: Path) -> None:
        # POSITIVE CONTROL (design §7): a read-only tool is visible AND its body RUNS for a hosted
        # member — proving the harness can SEE a body execute (the effect observer is not stuck at 0,
        # so the refused pin's counter == 0 is a real observation, not a dead harness). WRONG BUILD:
        # a guard that over-refuses (refuses read-only tools too).
        counters = _EffectCounters()
        async with wire_session(
            tmp_path,
            posture="hosted",
            principal="google",
            prepare=_register_synth_tools(counters),
        ) as wire:
            body = await wire.call(_SYNTH_READ_ONLY, {})
        assert _BODY_RAN_MARKER in body, "a read-only tool's body must run for a hosted member"
        assert counters.read_only == 1, "the read-only tool's body must have executed exactly once"

    async def test_one_annotation_flip_moves_a_tool_across_guard_and_list(
        self, tmp_path: Path
    ) -> None:
        # ONE partition (``readOnlyHint``) feeds BOTH the guard and the list: the SAME tool name is
        # visible+runs when registered read-only, invisible+refused when registered mutating. WRONG
        # BUILD: a guard/list keyed on two different sources (a tool visible but refused, or hidden
        # but callable — served∩refused ≠ ∅).
        flip_name = "lore_probe_flip_w23"
        ran = {"count": 0}

        def _prepare_read_only(mcp: Any) -> None:
            def _tool() -> str:
                ran["count"] += 1
                return _BODY_RAN_MARKER

            mcp.tool(
                name=flip_name,
                annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
            )(_tool)

        def _prepare_mutating(mcp: Any) -> None:
            def _tool() -> str:
                ran["count"] += 1
                return _BODY_RAN_MARKER

            mcp.tool(
                name=flip_name,
                annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=False),
            )(_tool)

        # read-only annotation → visible + body runs.
        async with wire_session(
            tmp_path, posture="hosted", principal="google", prepare=_prepare_read_only
        ) as wire:
            assert flip_name in await wire.served_tool_names(), (
                "the read-only annotation must make the tool VISIBLE"
            )
        # mutating annotation → invisible.
        async with wire_session(
            tmp_path, posture="hosted", principal="google", prepare=_prepare_mutating
        ) as wire:
            assert flip_name not in await wire.served_tool_names(), (
                "the SAME name with a mutating annotation must move it INVISIBLE — one partition "
                "feeds both the guard and the list"
            )


class TestFullSurfaceUnaffectedPostures:
    """LOOPBACK keeps the full surface — the guard is a no-op with no ambient principal (design §7).

    (The LAN api-key full-write control is verifier-level in wave-1 —
    ``test_token_verifier.py::test_api_key_principal_keeps_full_write`` — and its wire form differs
    stub-vs-build in api-key MECHANISM; see REPORT §Deferred-wire-pins.)
    """

    async def test_loopback_has_the_full_surface(self, tmp_path: Path) -> None:
        # GREEN-now guard: with NO auth (loopback), get_access_token() is None, so the guard must be
        # a NO-OP — every tool visible + callable. WRONG BUILD: a guard that refuses when there is
        # no ambient principal would break EVERY local single-user session (they carry no bearer).
        counters = _EffectCounters()
        async with wire_session(
            tmp_path,
            posture="loopback",
            principal=None,
            prepare=_register_synth_tools(counters),
        ) as wire:
            served = await wire.served_tool_names()
            assert _SYNTH_MUTATING in served, "loopback must keep the mutating tool visible (no guard)"
            body = await wire.call(_SYNTH_MUTATING, {})
        assert _BODY_RAN_MARKER in body and counters.mutating == 1, (
            "loopback must run the mutating tool's body (the guard is a no-op with no principal)"
        )

