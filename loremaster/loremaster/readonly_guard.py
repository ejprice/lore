"""The read-only-hosted enforcement guard (packet 39 RE-CUT, design §7 / #295).

⚠ READ-ONLY-hosted banner: in packet 39 EVERY hosted principal (member AND admin) reaches the
read-only tool surface ONLY — there is NO role axis for write (hosted write moves to the RBAC
packets 60-65). So this guard refuses EVERY mutating tool to EVERY principal that lacks the
``lore:write`` scope; in ``HOSTED_OAUTH`` no principal carries it, so every mutating tool is
refused there. ``LAN_BEARER`` api-key principals carry ``lore:write`` (the trusted fleet keeps
full write), and ``LOOPBACK`` runs with no auth (the guard is a no-op — no ambient principal).

The guard is the coarse TOOL-capability layer; it is built to COMPOSE with RBAC's future
row-level PDP (two layers, both must pass, neither preempts — design §7 banner).

ONE default-deny fastmcp ``Middleware`` keyed on the EXISTING
:func:`loremaster.server.partition_tools_by_posture` (``ToolAnnotations.readOnlyHint``,
deny-by-default: ``readOnlyHint is not True`` counts as mutating), with two hooks:

* ``on_list_tools`` FILTERS out every mutating tool when the ambient principal
  (``fastmcp.server.dependencies.get_access_token``) lacks ``lore:write`` → the tool is INVISIBLE
  in ``tools/list`` (the #295 structural leg).
* ``on_call_tool`` REFUSES the same set by RAISING BEFORE ``call_next`` → the tool body NEVER
  runs (the #295 EFFECT leg — WB48 proved a guard that refuses AFTER ``call_next`` renders a
  byte-identical refusal while the body already executed; the placement is load-bearing).

COVERAGE IS A CHECKED VARIABLE (#344/#345): the guard's reach = the tool set it evaluates, and
that set is DERIVED from the live registry (the list ``on_list_tools`` is handed), never a
hand-list — so a newly-registered mutating tool is refused by construction, and a coverage pin
reddens if the registered set grows past the guard's observed set.

⚠ STUB (contract-39-w23, wave-2/3): ``ReadOnlyGuardMiddleware`` is the real interface class; both
hooks raise ``NotImplementedError`` so the enforcement contract (``test_readonly_guard.py`` +
the wire pins) fails BEHAVIOURALLY, never on an ImportError. The builder implements the filter +
the refuse-before-call_next, reusing ``partition_tools_by_posture`` (the ONE partition) and the
``lorerunes.LORE_WRITE`` scope constant (never a re-spelling).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

from lorerunes import LORE_WRITE

__all__ = ["ReadOnlyGuardMiddleware"]


class ReadOnlyGuardMiddleware(Middleware):
    """Default-deny read-only enforcement over the whole tool surface (design §7).

    The ambient principal is read through the fastmcp-native
    :func:`fastmcp.server.dependencies.get_access_token`; a principal is permitted the mutating
    surface iff its minted ``AccessToken`` carries the ``lore:write`` scope
    (:data:`lorerunes.LORE_WRITE`). NO ambient principal (``LOOPBACK`` — no auth) makes the
    guard a NO-OP, so every local single-user session keeps the full surface. In
    ``HOSTED_OAUTH`` no principal carries ``lore:write`` (READ-ONLY-hosted banner), so every
    mutating tool is refused to every hosted principal; ``LAN_BEARER`` api-key principals carry
    it and keep full write.
    """

    async def on_list_tools(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
    ) -> Any:
        """Filter out mutating tools for a principal lacking ``lore:write`` (INVISIBLE leg).

        The reach is DERIVED from the live registry — the list ``call_next`` returns — never a
        hand-list, so a newly-registered mutating tool is filtered by construction (coverage is
        a checked variable, #344/#345). The mutating partition is the ONE shared
        :func:`~loremaster.server.partition_tools_by_posture` (deny-by-default:
        ``readOnlyHint is not True`` counts as mutating), so this filter, the ``on_call_tool``
        refusal, and any render agree by construction (ROUTING-IS-NOT-SHARING).
        """
        tools = await call_next(context)
        if self._principal_may_write():
            return tools
        mutating, _read_only = self._partition_mutating(tools)
        return [tool for tool in tools if tool.name not in mutating]

    async def on_call_tool(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
    ) -> Any:
        """Refuse a mutating tool BEFORE ``call_next`` (the #295 EFFECT leg — body never runs).

        The refusal is RAISED before ``call_next`` so the guarded body NEVER executes — a guard
        that ran the body THEN refused renders a byte-identical refusal while the mutation has
        already happened (finding #295 / WB48), so the placement is load-bearing. Whether the
        called tool mutates is decided by the SAME shared partition over the LIVE registry
        (``list_tools(run_middleware=False)`` — the full, unfiltered set), never a hand-list of
        known built-ins: a synthetic tool the guard has never seen is refused by construction.
        """
        if self._principal_may_write():
            return await call_next(context)
        tool_name = context.message.name
        fastmcp_context = context.fastmcp_context
        if fastmcp_context is None:
            # A restricted principal with no reachable server registry: DENY-BY-DEFAULT — the
            # guard cannot verify the tool is read-only, so it refuses. Unreachable on the wire (a
            # principal implies an HTTP request context; get_access_token is None in-process, so
            # `_principal_may_write` returns True above and this branch is never entered there).
            raise self._refusal(tool_name)
        registry = await fastmcp_context.fastmcp.list_tools(run_middleware=False)
        mutating, _read_only = self._partition_mutating(registry)
        if tool_name in mutating:
            raise self._refusal(tool_name)
        return await call_next(context)

    @staticmethod
    def _principal_may_write() -> bool:
        """Report whether the ambient principal may reach the mutating surface.

        ``True`` when there is NO ambient principal (``LOOPBACK`` — the guard is a no-op) OR the
        principal's minted scopes carry :data:`lorerunes.LORE_WRITE`; ``False`` for a principal
        that lacks it (every hosted principal this READ-ONLY-hosted packet).
        """
        token = get_access_token()
        if token is None:
            return True
        return LORE_WRITE in (token.scopes or [])

    @staticmethod
    def _partition_mutating(tools: Sequence[Any]) -> tuple[frozenset[str], frozenset[str]]:
        """Partition ``tools`` into ``(mutating, read_only)`` via the ONE shared derivation."""
        from loremaster.server import partition_tools_by_posture  # noqa: PLC0415

        return partition_tools_by_posture(tools)

    @staticmethod
    def _refusal(tool_name: str) -> Exception:
        """The structured teaching refusal (Consumer Law) — names the tool, why, and the surface.

        The message NAMES the refused tool (so ``tools/call``'s error result carries it as the
        refusal marker) and the missing capability (``lore:write``, spelled from the shared
        constant so it cannot drift), and points at the remaining read surface.
        """
        from fastmcp.exceptions import ToolError  # noqa: PLC0415

        return ToolError(
            f"{tool_name!r} is refused: this principal has read-only access — it does not carry "
            f"the {LORE_WRITE!r} scope, and {tool_name!r} is a mutating tool. The read-only tool "
            f"surface remains available to this principal."
        )
