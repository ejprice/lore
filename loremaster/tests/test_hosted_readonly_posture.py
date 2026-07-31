"""CONTRACT — the hosted read-only posture. EVERY assertion here drives the WIRE (R16).

Design ``docs/design/2026-07-31-packet39-google-oauth.md`` §7 + R13/R14/R16.

**The rule:** a tool is hosted-callable **iff** its registered
``ToolAnnotations.readOnlyHint is True``. Everything else — including
``annotations is None`` — is refused for a principal without ``lore:write``.
Deny-by-default, so an unclassified new tool is **born refused**.

------------------------------------------------------------------------------
⚑ WHY THIS MODULE LOOKS THE WAY IT DOES: THREE WAVES, ONE ROOT CAUSE

``FastMCP.__init__`` calls ``_setup_handlers``, which registers the **bound** method
(``self.list_tools``, ``self.call_tool``, …) with the low-level server. **Anything
installed on the server afterwards as an instance attribute is therefore live in-process
and DEAD ON THE WIRE — and an in-process pin cannot tell the difference.** Three wrong
builds walked through that door in three waves, each passing every pin the previous wave
had just added:

* **WB30** — the guard installed as ``mcp.call_tool = _guarded``. Green in-process, never
  ran on the served path.
* **WB48** — the guard placed *after* ``super().call_tool``. The refusal was byte-identical
  to the correct build's and the tool body had **already executed**.
* **WB93** — the ``list_tools`` filter installed as ``mcp.list_tools = _scoped``. Hosted
  ``tools/list`` on the wire returned **15 tools including all six mutating ones**; the
  correct build returns 9.

Each fix pinned the route that had just been broken. R16 kills the CLASS instead, and this
module is one of its three instruments: **no posture claim is proven in process.** Every
refusal, every served surface, every effect assertion below goes through
``_auth_fixtures.wire_session`` — a real ``initialize`` → ``notifications/initialized`` →
``tools/list`` / ``tools/call`` over the assembled ASGI app, authenticated with a real
credential through the real verifier.

``test_wire_discipline.py`` enforces that mechanically, so it is not a rule anyone has to
remember. The in-process helpers live in ``_auth_fixtures`` and this module imports
neither.

**The question to ask of every pin added here:** *"if the mechanism were installed as an
instance attribute after construction, would this pin still pass?"* If yes, it is an
in-process pin wearing a wire pin's name.

------------------------------------------------------------------------------
FINDING #291 — THE DERIVATION, AND WHAT ANCHORS IT

``test_mcp_server.py``'s ``_MUTATING_TOOLS`` was a hand-list beside production's typed
``ToolAnnotations`` and had already drifted (it omits ``lore_claim_task`` / ``lore_tasks``).
Coverage is therefore DERIVED — from ``all_registered_tools()``, the R16 sanctioned
unscoped accessor — and the spec anchor is BEHAVIOUR, named once per tool, with
:data:`EXPECTED_MUTATING_TOOLS` asserted EQUAL to the derived set (equality, which is
precisely what #291's subset check lacked).

------------------------------------------------------------------------------
THE ∀-PROPERTIES

* **classification:** every registered tool is classified, over BOTH registration paths
  (core and extension — R14; the extension path is where this ∀ was FALSE on a correct
  build until the fixture registered one).
* **partition (WB72):** for one principal on the wire, ``served ∩ refused = ∅`` — every
  tool the wire lists is callable, and every tool it refuses is unlisted.
* **effect (R13):** no refused tool's body is ever entered, observed at the ``Tool.run``
  boundary rather than in the refusal message.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from _auth_fixtures import (
    API_KEY_ENV_LAN_CLIENT,
    API_KEY_ENV_LOCAL_AGENT,
    API_KEY_VALUE_LAN_CLIENT,
    API_KEY_VALUE_LOCAL_AGENT,
    OPERATOR_EMAIL,
    SECOND_PRINCIPAL_EMAIL,
    base_config_payload,
    hosted_auth_block,
    slug,
    wire_session,
    write_roster,
)
from mcp.types import ToolAnnotations

# The BEHAVIOURAL anchor (design §7). Each name gets its own refusal fixture, so a
# wrongly-flipped annotation reds a pin BY NAME rather than being blessed by a derived
# expectation. Read off production's six ``ToolAnnotations`` constants and their
# registration sites.
EXPECTED_MUTATING_TOOLS = frozenset(
    {
        "lore_remember",
        "lore_index",
        "lore_findings",
        "lore_comms",
        # ⚠ THE TWO #291 OMITTED. Their presence here is the fix.
        "lore_claim_task",
        "lore_tasks",
    }
)

# The read surface that must REMAIN available to a hosted principal — the whole point of
# admitting them. Also the control set: a build that refused everything would satisfy
# every refusal pin below.
EXPECTED_READ_ONLY_TOOLS = frozenset(
    {
        "lore_search",
        "lore_get_symbol",
        "lore_verify",
        "lore_recall",
        "lore_dead_code",
        "lore_impact",
        "lore_map",
        "lore_read",
        "lore_diff",
    }
)

# The whole registered surface, DERIVED from the two named sets rather than re-listed, so
# a tool cannot be added to one and forgotten here.
ALL_TOOL_NAMES = EXPECTED_READ_ONLY_TOOLS | EXPECTED_MUTATING_TOOLS

# An adversarially UNANNOTATED tool (WB72's exact case): deny-by-default must place it in
# the refused set AND keep it off the served list, with no annotation to reason from.
UNANNOTATED_PROBE_TOOL = "lore_probe_unannotated"


def refusal_marker() -> str:
    """The substring proving the POSTURE GUARD answered, taken from the enum.

    A hand-typed marker that stops matching after a rename makes a refusal pin go GREEN
    while checking nothing — the same class of defect as a guard that is dead on the wire.
    """
    from lorerunes import Posture

    return str(Posture.HOSTED_OAUTH.name)


def hosted_server(tmp_path: Path, *, with_extension: bool = False) -> Any:
    """A composed ``HOSTED_OAUTH`` server, for STRUCTURAL and RENDER assertions only.

    Never used to prove a posture claim — those go over the wire. ``with_extension``
    exists because its absence was a defect: the ∀ classification pin was FALSE on a
    correct build the moment one extension registered, and passed only because this
    fixture registered none (a ∀ evaluated where the branch cannot fire).
    """
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_mcp_server

    roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
    payload = base_config_payload(slug(), tmp_path / "live")
    payload["auth"] = hosted_auth_block(roster)
    server = LoreServer(LoreConfig.model_validate(payload))
    if with_extension:
        from _extension_helpers import CounterExtension

        server.register_extension(CounterExtension())
    return build_mcp_server(server)


def mutating_tool_names(mcp: Any) -> frozenset[str]:
    """The DERIVED refused set: ``{tool : annotations.readOnlyHint is not True}``.

    ⚠ READS ``all_registered_tools()``, NOT ``list_tools`` — R16 part 3. Under R13 the
    served lookup is posture-SCOPED, so deriving from it would be circular (for a hosted
    principal the refused set would be empty by construction). The scoped manager exposes
    ONE explicitly-named unscoped accessor and this is a consumer of it. That accessor
    exists because the ABSENCE of a sanctioned full-registry view is exactly the friction
    that pushed a builder into reaching past the override — the door WB93 walked through.
    A gate that makes honest code awkward gets switched off.
    """
    return frozenset(
        tool.name
        for tool in mcp._tool_manager.all_registered_tools()
        if tool.annotations is None or tool.annotations.readOnlyHint is not True
    )


def readable_tool_names(mcp: Any) -> frozenset[str]:
    """The complement — the read ladder — from the same one derivation."""
    registered = frozenset(tool.name for tool in mcp._tool_manager.all_registered_tools())
    return registered - mutating_tool_names(mcp)


def register_unannotated(mcp: Any) -> None:
    """Register a tool with NO annotations at all (the WB72 fixture)."""

    def _probe() -> str:
        """A newly contributed tool nobody has classified."""
        return "contract-probe-ok"

    mcp.add_tool(_probe, name=UNANNOTATED_PROBE_TOOL)


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export the api-key env vars the hosted auth block references."""
    monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
    monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)


class TestEveryRegisteredToolIsClassified:
    """∀ over BOTH registration paths — the branch this pin used to be blind to."""

    @pytest.mark.parametrize(
        "with_extension", [False, True], ids=["core-only", "with-extension"]
    )
    def test_every_registered_tool_carries_an_explicit_read_only_hint(
        self, tmp_path: Path, with_extension: bool
    ) -> None:
        # ⚑ PARAMETRISED OVER THE REGISTRATION PATH, because that is where this ∀ was
        # FALSE ON A CORRECT BUILD. ``_register_extension_tools`` called ``add_tool(...)``
        # with no ``annotations=`` and ``ToolSpec`` has no field to carry one, so an
        # extension tool reached the served surface unclassified — and the pin passed only
        # because its fixture registered no extensions. R14 rules the synthesis; this is
        # what makes the ∀ true over both paths instead of over the convenient one.
        mcp = hosted_server(tmp_path, with_extension=with_extension)
        registered = mcp._tool_manager.all_registered_tools()
        assert registered, "the ∀ must range over a non-empty registry"
        for tool in registered:
            assert tool.annotations is not None, (
                f"{tool.name} carries no ToolAnnotations. Under R8 the hosted posture is "
                f"DERIVED from readOnlyHint, so this tool is refused by construction and "
                f"its author had no way to say otherwise."
            )
            assert tool.annotations.readOnlyHint is not None, (
                f"{tool.name}'s readOnlyHint is unset (None). Set it explicitly."
            )

    def test_the_derived_mutating_set_equals_the_named_behaviour_fixtures(
        self, tmp_path: Path
    ) -> None:
        # EQUALITY, not the subset check #291's pin performed — a subset check cannot see
        # an omission, which is exactly how two tools went unguarded. If this reds because
        # a NEW tool appeared, add its behavioural fixture below; do not widen a list.
        derived = mutating_tool_names(hosted_server(tmp_path))
        assert derived == EXPECTED_MUTATING_TOOLS, (
            f"the derived refused set and the named behaviour fixtures disagree. Only "
            f"derived: {sorted(derived - EXPECTED_MUTATING_TOOLS)}; only named: "
            f"{sorted(EXPECTED_MUTATING_TOOLS - derived)}."
        )

    def test_the_derived_readable_set_equals_the_named_read_tools(
        self, tmp_path: Path
    ) -> None:
        # The control set. Without it a build annotating EVERY tool non-read-only would
        # satisfy the equality above while leaving a hosted principal with nothing.
        assert readable_tool_names(hosted_server(tmp_path)) == EXPECTED_READ_ONLY_TOOLS


class TestHostedPrincipalsAreRefusedEveryMutatingTool:
    """One NAMED wire fixture per mutating tool, per principal shape."""

    @pytest.mark.parametrize("tool_name", sorted(EXPECTED_MUTATING_TOOLS))
    async def test_a_google_principal_cannot_call_a_mutating_tool_on_the_wire(
        self, tmp_path: Path, tool_name: str
    ) -> None:
        async with wire_session(tmp_path, posture="hosted", principal="google") as wire:
            body = await wire.call(tool_name)
        assert refusal_marker() in body, (
            f"a hosted Google principal reached the MUTATING tool `{tool_name}` over the "
            f"SERVED path. Body: {body[:400]!r}"
        )

    @pytest.mark.parametrize("tool_name", sorted(EXPECTED_READ_ONLY_TOOLS))
    async def test_a_google_principal_is_NOT_refused_a_read_tool_on_the_wire(
        self, tmp_path: Path, tool_name: str
    ) -> None:
        # THE CONTROL for every refusal above, and it is not optional: a guard that
        # refused everything would pass all six. The read ladder is why a Google principal
        # is admitted at all.
        async with wire_session(tmp_path, posture="hosted", principal="google") as wire:
            body = await wire.call(tool_name)
        assert refusal_marker() not in body, (
            f"`{tool_name}` is read-only and must reach dispatch for a hosted principal; "
            f"it was refused. Body: {body[:400]!r}"
        )

    @pytest.mark.parametrize("tool_name", sorted(EXPECTED_MUTATING_TOOLS))
    async def test_an_api_key_principal_is_NOT_refused_a_mutating_tool_on_the_wire(
        self, tmp_path: Path, tool_name: str
    ) -> None:
        # Design §1's mechanical verdict: "an api-key principal can call mutating tools
        # through the hosted port" — INTENDED. api keys are the local/LAN trust anchor.
        async with wire_session(tmp_path, posture="hosted", principal="api_key") as wire:
            body = await wire.call(tool_name)
        assert refusal_marker() not in body, (
            f"an api-key principal was refused `{tool_name}`; api keys retain the FULL "
            f"surface. Body: {body[:400]!r}"
        )

    async def test_an_unannotated_tool_is_born_refused_on_the_wire(
        self, tmp_path: Path
    ) -> None:
        # FAIL-CLOSED BY CONSTRUCTION, and the answer to the design's askable question:
        # "if I registered a new tool right now with no annotations, which pin reds and
        # which guard refuses it?"
        async with wire_session(
            tmp_path, posture="hosted", principal="google", prepare=register_unannotated
        ) as wire:
            body = await wire.call(UNANNOTATED_PROBE_TOOL)
        assert refusal_marker() in body


class TestServedAndRefusedArePartitioned:
    """WB72 — ∀ on the wire: ``served ∩ refused = ∅``, over the FULL registry.

    A build can be self-inconsistent in a way no single-route pin sees: advertise a tool on
    ``tools/list`` that ``tools/call`` will then refuse, or refuse one it never listed. The
    invariant is stated over the whole registry for ONE principal, with an adversarially
    UNANNOTATED tool in the fixture so the partition cannot lean on an annotation existing.
    """

    async def test_every_served_tool_is_callable_and_every_refused_tool_is_unlisted(
        self, tmp_path: Path
    ) -> None:
        async with wire_session(
            tmp_path, posture="hosted", principal="google", prepare=register_unannotated
        ) as wire:
            served = await wire.served_tool_names()
            refused = mutating_tool_names(wire.mcp)
            assert UNANNOTATED_PROBE_TOOL in refused, (
                "the adversarial fixture tool must land in the refused set, or this ∀ is "
                "evaluated without the case it exists for"
            )
            assert not (served & refused), (
                f"the wire OFFERS tools it will refuse: {sorted(served & refused)}. Under "
                f"the trust doctrine a served surface that over-claims is worse than a "
                f"smaller one: the agent burns calls on it and then routes around the MCP."
            )
            # The other half, proven by DISPATCH rather than by the list alone.
            for tool_name in sorted(served):
                body = await wire.call(tool_name)
                assert refusal_marker() not in body, (
                    f"`{tool_name}` was LISTED to this principal and then refused when "
                    f"called — the two routes disagree"
                )

    async def test_the_partition_covers_the_whole_registry(self, tmp_path: Path) -> None:
        # ANTI-VACUITY: served ∪ refused must be the entire registry, or a build could
        # satisfy the disjointness above by serving nothing and refusing nothing.
        async with wire_session(
            tmp_path, posture="hosted", principal="google", prepare=register_unannotated
        ) as wire:
            served = await wire.served_tool_names()
            registered = {
                tool.name for tool in wire.mcp._tool_manager.all_registered_tools()
            }
            assert served | mutating_tool_names(wire.mcp) == registered
            assert served, "a hosted principal must be served a non-empty read ladder"


class TestARefusedToolNeverRUNS:
    """R13 — observe the EFFECT, never the message (WB48, finding #295).

    WB48 placed the guard after ``super().call_tool``: the refusal was byte-identical to
    the correct build's and the tool body had **already executed** (``invocations=1`` vs
    ``0``). Same exception, same bytes, opposite reality.

    **The askable form, for every refusal pin anyone writes:** *"if the guard ran AFTER
    the thing it guards, would this pin still pass?"*

    ``Tool.run``-entry is the effect boundary UPSTREAM of argument validation, so
    ``arguments={}`` can no longer mask a body that ran — the adversary's exact blind spot.
    """

    def _run_entry_recorder(self, monkeypatch: pytest.MonkeyPatch) -> list[str]:
        """Wrap ``Tool.run`` at its ENTRY and record every tool that reaches it."""
        from mcp.server.fastmcp.tools.base import Tool

        entered: list[str] = []
        original = Tool.run

        async def _recording_run(tool_self: Any, *args: Any, **kwargs: Any) -> Any:
            entered.append(tool_self.name)
            return await original(tool_self, *args, **kwargs)

        monkeypatch.setattr(Tool, "run", _recording_run)
        return entered

    async def test_no_refused_tool_body_is_ever_entered_on_the_wire(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # THE DERIVED ∀ EFFECT PIN. Iterates the FULL registry, so a newly added mutating
        # tool is covered the day it is registered — no "tool nobody wrote a counter for".
        entered = self._run_entry_recorder(monkeypatch)
        async with wire_session(tmp_path, posture="hosted", principal="google") as wire:
            refused = mutating_tool_names(wire.mcp)
            assert refused, "the ∀ must range over a non-empty set"
            for tool_name in sorted(refused):
                body = await wire.call(tool_name)
                assert refusal_marker() in body, f"{tool_name} was not refused"
        assert entered == [], (
            f"the bodies of {entered} were ENTERED while being refused. The caller sees a "
            f"correct refusal and the side effect has already happened."
        )

    async def test_the_recorder_CAN_see_a_body_execute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ⚑ THE POSITIVE CONTROL FOR THE INSTRUMENT ITSELF, and it is not optional: a
        # recorder that never fires makes the ∀ above pass on every build, WB48 included.
        entered = self._run_entry_recorder(monkeypatch)
        async with wire_session(tmp_path, posture="hosted", principal="google") as wire:
            await wire.call("lore_search")
        assert "lore_search" in entered, (
            "the Tool.run recorder did not observe a body that demonstrably executed — "
            "the instrument is blind and every ∀ effect assertion above is vacuous"
        )

    async def test_a_no_argument_mutating_tool_is_refused_without_running(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The WB48 probe kept as a contract fixture: a mutating tool with NO REQUIRED
        # ARGUMENTS, so argument validation can never be the reason its body did not run.
        invocations: list[int] = []

        def _prepare(mcp: Any) -> None:
            def probe_write() -> str:
                """A mutating tool with no required arguments."""
                invocations.append(1)
                return "contract-probe-ok"

            mcp.add_tool(
                probe_write,
                name="lore_probe_write",
                annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=False),
            )

        entered = self._run_entry_recorder(monkeypatch)
        async with wire_session(
            tmp_path, posture="hosted", principal="google", prepare=_prepare
        ) as wire:
            body = await wire.call("lore_probe_write")
        assert refusal_marker() in body
        assert not invocations, (
            "the refused tool's body ran before the refusal — and its arguments were "
            "valid, so the write really happened"
        )
        assert "lore_probe_write" not in entered


class TestTheScopedLookupIsTheEnforcementSeam:
    """R13/R16 — the served ``tools/list``, read off the WIRE (WB93's route)."""

    async def test_a_hosted_principal_is_not_offered_refused_tools_on_the_wire(
        self, tmp_path: Path
    ) -> None:
        # ⚑ THE WB93 PIN. The previous wave asserted this in process, and a filter
        # installed as ``mcp.list_tools = _scoped`` passed it while the wire returned all
        # fifteen tools to a hosted Google principal.
        async with wire_session(tmp_path, posture="hosted", principal="google") as wire:
            served = await wire.served_tool_names()
        assert served == EXPECTED_READ_ONLY_TOOLS, (
            f"the hosted principal's served surface must be exactly the read ladder; got "
            f"{sorted(served)}. Leaked mutating tools: "
            f"{sorted(served & EXPECTED_MUTATING_TOOLS)}"
        )

    async def test_an_api_key_principal_is_offered_the_full_surface_on_the_wire(
        self, tmp_path: Path
    ) -> None:
        async with wire_session(tmp_path, posture="hosted", principal="api_key") as wire:
            served = await wire.served_tool_names()
        assert served == ALL_TOOL_NAMES

    async def test_the_loopback_posture_serves_the_full_surface_unauthenticated(
        self, tmp_path: Path
    ) -> None:
        # Protects the EXISTING deployment: with no principal the lookup is unfiltered, or
        # a local single-user deploy silently loses two thirds of its tools.
        async with wire_session(tmp_path, posture="loopback", principal=None) as wire:
            served = await wire.served_tool_names()
        assert served == ALL_TOOL_NAMES

    def test_the_composed_server_installs_a_SCOPED_tool_manager(
        self, tmp_path: Path
    ) -> None:
        # The cheap structural half R13 asks for. It names no class of ours — only that
        # the composed manager is a SUBCLASS of the SDK's, never the stock one. Its
        # behavioural half is the wire pin above; neither alone survived a wave.
        from mcp.server.fastmcp.tools.tool_manager import ToolManager

        manager = hosted_server(tmp_path)._tool_manager
        assert isinstance(manager, ToolManager)
        assert type(manager) is not ToolManager, (
            "the composed FastMCP is carrying the SDK's stock ToolManager, so enforcement "
            "has moved back out into a wrapper whose placement is a free variable again"
        )


class TestTheUnscopedAccessorIsTheSanctionedFullRegistryView:
    """R16 part 3 — remove the friction that pushed builders through the door."""

    def test_the_scoped_manager_exposes_all_registered_tools(self, tmp_path: Path) -> None:
        # The adversary named the friction precisely: the instructions render needs the
        # UNSCOPED registry, and under a scoped ``list_tools`` even the reference build had
        # to reach past its own override. A builder who finds that awkward moves the filter
        # somewhere wire-dead. Giving the honest path a NAME is what stops that.
        manager = hosted_server(tmp_path)._tool_manager
        assert {tool.name for tool in manager.all_registered_tools()} == ALL_TOOL_NAMES, (
            "all_registered_tools() must return the FULL registry regardless of posture "
            "or ambient principal — it is the one sanctioned unscoped view"
        )

    def test_the_accessor_is_unaffected_by_an_ambient_hosted_principal(
        self, tmp_path: Path
    ) -> None:
        # If the accessor were itself scoped, every derivation built on it would silently
        # narrow and the ∀ pins would go vacuous rather than red.
        async def _check() -> None:
            async with wire_session(tmp_path, posture="hosted", principal="google") as wire:
                registered = {
                    tool.name for tool in wire.mcp._tool_manager.all_registered_tools()
                }
                assert registered == ALL_TOOL_NAMES

        asyncio.run(_check())


class TestExtensionToolsAreRefusedWholesale:
    """R14 + WB74 — the core cannot audit a project-authored callable, so it may not CLAIM."""

    def test_an_extension_tool_carries_the_exact_worst_case_annotations(
        self, tmp_path: Path
    ) -> None:
        # WB74: the annotation CLASS was spec-silent — only ``readOnlyHint`` was ruled,
        # leaving every other field a free variable. R14 now names the whole object, worst
        # case on EVERY field, for the same reason on each: the core can verify none of
        # them for a project-authored callable, and an unverifiable hint must claim the
        # conservative direction (an optimistic hint on unaudited code is an over-claim).
        # EXACT EQUALITY, so drift in any field reds — not just the read-only bit.
        from loremaster.server import _EXTENSION_TOOL_ANNOTATIONS

        expected = ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=True,
            idempotentHint=False,
            openWorldHint=True,
        )
        assert _EXTENSION_TOOL_ANNOTATIONS == expected, (
            f"the synthesized extension annotations must be worst-case on every field; "
            f"got {_EXTENSION_TOOL_ANNOTATIONS!r}"
        )

        mcp = hosted_server(tmp_path, with_extension=True)
        extension_tools = [
            tool
            for tool in mcp._tool_manager.all_registered_tools()
            if tool.name not in ALL_TOOL_NAMES
        ]
        assert extension_tools, "the fixture registered no extension tool"
        for tool in extension_tools:
            assert tool.annotations == expected, (
                f"{tool.name} is extension-contributed and must carry the synthesized "
                f"worst-case annotations verbatim; got {tool.annotations!r}"
            )

    async def test_an_extension_tool_is_refused_for_a_hosted_principal_on_the_wire(
        self, tmp_path: Path
    ) -> None:
        async with wire_session(
            tmp_path, posture="hosted", principal="google", with_extension=True
        ) as wire:
            served = await wire.served_tool_names()
            extension_tools = sorted(
                tool.name
                for tool in wire.mcp._tool_manager.all_registered_tools()
                if tool.name not in ALL_TOOL_NAMES
            )
            assert extension_tools, "the fixture registered no extension tool"
            assert not (set(extension_tools) & served), (
                f"extension tools were OFFERED to a hosted principal: "
                f"{sorted(set(extension_tools) & served)}"
            )
            for name in extension_tools:
                assert refusal_marker() in await wire.call(name)

    async def test_an_extension_tool_remains_callable_via_an_api_key_on_the_wire(
        self, tmp_path: Path
    ) -> None:
        # THE CONTROL: refusing extensions on the HOSTED surface must not break them for
        # the local/LAN principals who are the reason extensions exist at all.
        async with wire_session(
            tmp_path, posture="hosted", principal="api_key", with_extension=True
        ) as wire:
            extension_tools = sorted(
                tool.name
                for tool in wire.mcp._tool_manager.all_registered_tools()
                if tool.name not in ALL_TOOL_NAMES
            )
            assert extension_tools
            served = await wire.served_tool_names()
            assert set(extension_tools) <= served
            for name in extension_tools:
                assert refusal_marker() not in await wire.call(name)


class TestTheRefusalTeaches:
    """A refusal a consumer cannot act on is a dead end (the Consumer Law)."""

    async def test_the_refusal_names_the_posture_and_the_tool(self, tmp_path: Path) -> None:
        async with wire_session(tmp_path, posture="hosted", principal="google") as wire:
            body = await wire.call("lore_claim_task")
        assert refusal_marker() in body, "the refusal must name its posture, from the enum"
        assert "lore_claim_task" in body, "the refusal must name the tool it refused"

    async def test_the_refusal_points_at_the_read_surface_that_remains(
        self, tmp_path: Path
    ) -> None:
        # A consumer refused and told nothing routes around the MCP entirely.
        async with wire_session(tmp_path, posture="hosted", principal="google") as wire:
            body = await wire.call("lore_remember")
        assert any(name in body for name in sorted(EXPECTED_READ_ONLY_TOOLS)), (
            f"the refusal must name at least one tool the caller CAN still use; got "
            f"{body[:400]!r}"
        )

    async def test_the_refusal_does_not_leak_the_credential(self, tmp_path: Path) -> None:
        async with wire_session(tmp_path, posture="hosted", principal="google") as wire:
            body = await wire.call("lore_comms")
            assert wire.token is not None
            assert wire.token not in body

    def test_the_refusal_is_a_structured_tool_error(self) -> None:
        # Design §7: "a STRUCTURED tool error (never an unhandled exception)". The SDK
        # renders a ``ToolError`` as ``isError: true`` content the agent can read; any
        # other exception becomes an opaque transport failure.
        from loremaster.server import HostedToolRefusedError
        from mcp.server.fastmcp.exceptions import ToolError

        assert issubclass(HostedToolRefusedError, ToolError)


class TestInstructionsAreHonestAboutThePosture:
    """The Consumer Law: what is served must match what happens (design §7)."""

    def test_the_hosted_instructions_carry_the_refused_set_section(
        self, tmp_path: Path
    ) -> None:
        from loremaster.server import HOSTED_REFUSAL_SECTION_HEADING

        instructions = hosted_server(tmp_path).instructions or ""
        assert HOSTED_REFUSAL_SECTION_HEADING in instructions, (
            "an agent connecting to the hosted surface must be TOLD which tools it cannot "
            "call, or it discovers the boundary by failing calls"
        )

    def test_the_refused_clause_names_EXACTLY_the_refused_set(self, tmp_path: Path) -> None:
        # WB50 — a served surface that LIES. Every earlier section pin checked MEMBERSHIP
        # ("is each refused tool named?"), which a SUPERSET satisfies trivially. A build
        # that dropped the annotation filter served a paragraph calling `lore_search`
        # refused AND available in the same breath. EQUALITY, both directions, against the
        # DERIVATION rather than a literal.
        from loremaster.server import (
            HOSTED_READ_LADDER_MARKER,
            HOSTED_REFUSAL_SECTION_HEADING,
        )

        mcp = hosted_server(tmp_path)
        refused = mutating_tool_names(mcp)
        section = (mcp.instructions or "").split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1]
        refused_clause = section.split(HOSTED_READ_LADDER_MARKER, 1)[0]

        named = {name for name in ALL_TOOL_NAMES if name in refused_clause}
        assert named == refused, (
            f"the served refused-set clause does not match the derivation. Named but not "
            f"refused: {sorted(named - refused)} (OVER-claims — an agent told a read tool "
            f"is refused stops using it). Refused but not named: {sorted(refused - named)} "
            f"(UNDER-claims — the agent finds out by failing calls)."
        )

    def test_the_read_ladder_clause_names_EXACTLY_the_readable_set(
        self, tmp_path: Path
    ) -> None:
        # WB50b — a build whose read-ladder list is EMPTY serves "The read ladder remains
        # fully available: ." and tells a hosted principal it has no surface at all.
        from loremaster.server import (
            HOSTED_READ_LADDER_MARKER,
            HOSTED_REFUSAL_SECTION_HEADING,
        )

        mcp = hosted_server(tmp_path)
        readable = readable_tool_names(mcp)
        assert readable, "the derivation must leave a non-empty read ladder"
        section = (mcp.instructions or "").split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1]
        ladder_clause = section.split(HOSTED_READ_LADDER_MARKER, 1)[1]

        named = {name for name in ALL_TOOL_NAMES if name in ladder_clause}
        assert named == readable, (
            f"the served read-ladder clause does not match the derivation. Missing: "
            f"{sorted(readable - named)}; wrongly offered: {sorted(named - readable)}."
        )

    def test_the_section_is_absent_in_loopback_posture(self, tmp_path: Path) -> None:
        from loremaster.config import LoreConfig
        from loremaster.server import (
            HOSTED_REFUSAL_SECTION_HEADING,
            LoreServer,
            build_mcp_server,
        )

        config = LoreConfig.model_validate(base_config_payload(slug(), tmp_path / "live"))
        mcp = build_mcp_server(LoreServer(config))
        assert HOSTED_REFUSAL_SECTION_HEADING not in (mcp.instructions or "")

    def test_the_instructions_still_name_every_registered_tool(self, tmp_path: Path) -> None:
        # Design §7: tools stay REGISTERED and TAUGHT in every posture; refusal happens at
        # call, honestly explained.
        instructions = hosted_server(tmp_path).instructions or ""
        for name in sorted(ALL_TOOL_NAMES):
            assert name in instructions, f"{name} is registered but not taught"
