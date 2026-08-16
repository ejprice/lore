"""Contract tests for packet 45 — the built-in tool ALLOWLIST + served-prose derivation.

Packet 45 (= multi-user Part 2; resolves finding #296) makes the built-in MCP tool
surface a FUNCTION OF THE ENABLED SET declared per deploy in a ``tools:`` section:

* A disabled tool is **NEVER REGISTERED** — absent from ``list_tools()`` AND uncallable
  by the SDK's own dispatch (#296 option 2A; the EFFECT, not a marker — #295).
* Served PROSE (the ``instructions`` block AND every tool/param description) names
  EXACTLY the enabled tools — no dangling cross-reference to a disabled neighbour and no
  gutted section header. ``build_instructions(_ALL_BUILTIN_TOOL_NAMES)`` reproduces
  today's ``_INSTRUCTIONS`` BYTE-EXACT, so the terminating CL3 anchor
  (``test_comms_tool.py::test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs``)
  and its control stay GREEN untouched — the derivation is ADDITIVE.

Design of record: ``docs/design/2026-08-13-packet45-served-prose-derivation.md`` (the
ruled shapes) and ``docs/plans/v2/45-tool-allowlist.md`` §"Kickoff rulings". Spec:
``docs/design/2026-08-01-multi-user-lore-proposal.md`` §Part 2.

FIXTURE DISCRIMINATION (CLAUDE.md — "what WRONG build would still pass this?"). Every
served-surface pin is parametrised over ``{full, a non-trivial subset, the lore-dnd
EXACT set, empty}`` (:data:`_ALL_FIXTURES`). A one-tool subset cannot distinguish "the
filter works" from "a single hardcoded name is dropped", so the non-trivial fixtures are
MULTI-tool and DIFFER from each other; the empty fixture is the ONLY one that disables
``lore_search``/``lore_read`` (enabled in every other fixture), which is what makes
filter coverage a *checked variable* over all 15 registration sites (L2-1 reach-check,
CLAUDE.md INSTRUMENT 0) rather than a coverage constant the guard silently under-runs.

RED STATE (this contract, against the packet-45 STUBS): the mechanism is unbuilt, so
``build_instructions`` / ``render_sample_tools_section`` raise ``NotImplementedError``,
the ``tools:`` allowlist is IGNORED (all 15 built-ins always register), and no boot
validation fires. Each load-bearing pin below carries its expected-RED node id (from
``--collect-only``) and the one-line mutation that reddens it, in its docstring.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

# ``import test_mcp_server`` is the running-MCP-server harness. RE-1 (packet 45) made its
# ``_ALL_BUILTIN_TOOL_NAMES`` an ALIAS of the production constant, so importing the suite
# also single-sources the universe — the same object this module imports from the server.
import test_mcp_server as _suite
from _extension_helpers import BUILTIN_COLLISION_NAME, CollidingExtension
from fastmcp import FastMCP
from fastmcp.exceptions import NotFoundError
from loremaster.config import LoreConfig, ToolsConfig
from loremaster.server import (
    _ALL_BUILTIN_TOOL_NAMES,
    LoreServer,
    _register_tools,
    build_instructions,
    build_mcp_server,
    partition_tools_by_posture,
    render_sample_tools_section,
)
from test_comms_tool import _declared_instructions, _msg
from test_mcp_server import _config, _slug

# The tool-name-token regex is REUSED from the every-token pin (DRY §6): a change to that
# recogniser must move both pins together, not silently diverge. It matches ``lore_``
# followed by lowercase/underscore word chars.
_TOOL_NAME_TOKEN = _suite.TestNoDeadToolNamesInAgentFacingText._TOOL_NAME_TOKEN


# --------------------------------------------------------------------------- #
# Fixtures — the enabled-set corpus the served-surface pins parametrise over.
# --------------------------------------------------------------------------- #
_FULL: frozenset[str] = frozenset(_ALL_BUILTIN_TOOL_NAMES)

# A non-trivial subset that is DISTINCT from lore-dnd and exercises a compound LADDER
# step (get_symbol / read) plus the MEMORY remember/recall clause.
_SUBSET: frozenset[str] = frozenset(
    {"lore_search", "lore_read", "lore_get_symbol", "lore_remember", "lore_recall"}
)

# lore-dnd's EXACT allowlist (rulings §4): a search-only instance. ENABLED is five tools;
# every graph/memory/ledger/comms tool is disabled — the driving real consumer.
_LORE_DND_ENABLED: frozenset[str] = frozenset(
    {"lore_search", "lore_read", "lore_index", "lore_diff", "lore_findings"}
)
_LORE_DND_DISABLED: frozenset[str] = frozenset(
    {
        "lore_map",
        "lore_get_symbol",
        "lore_verify",
        "lore_impact",
        "lore_dead_code",
        "lore_remember",
        "lore_recall",
        "lore_tasks",
        "lore_claim_task",
        "lore_comms",
    }
)

_EMPTY: frozenset[str] = frozenset()

# Non-empty fixtures build a FULL server (boot passes even in the finished build); the
# empty fixture is handled specially (build_mcp_server LOUD-FAILS on an empty total
# surface — Fork B — so the empty coverage/prose pins use the lower-level seams).
_NONEMPTY_FIXTURES = [
    pytest.param(_FULL, id="full"),
    pytest.param(_SUBSET, id="subset"),
    pytest.param(_LORE_DND_ENABLED, id="lore-dnd"),
]
# The empty fixture is added for the PURE-FUNCTION prose pins (structural / empty
# biconditional), which call ``build_instructions``/token helpers directly and so are
# NOT subject to ``build_mcp_server``'s Fork-B boot-empty loud-fail.
_ALL_FIXTURES = _NONEMPTY_FIXTURES + [pytest.param(_EMPTY, id="empty")]

# A section label ("HEADER:" / "HONEST FAILURE:") alone on a line, with nothing after
# it — the gutted-header shape a naive clause-stripper leaves when it removes a section's
# only content but not its header.
_GUTTED_HEADER = re.compile(r"^[A-Z][A-Z ]+:\s*$", re.MULTILINE)


def test_fixture_sets_are_coherent_with_the_declared_universe() -> None:
    """Self-check: the fixtures are real subsets of the universe, and the lore-dnd
    fixture is EXACTLY rulings §4 (a typo here would silently weaken every pin that
    consumes it — a fixture that cannot discriminate is decoration)."""
    assert _SUBSET < _FULL and len(_SUBSET) >= 2
    assert _LORE_DND_ENABLED < _FULL
    # rulings §4 partition: enabled ⊍ disabled == universe, disjoint.
    assert _LORE_DND_ENABLED | _LORE_DND_DISABLED == _FULL
    assert _LORE_DND_ENABLED.isdisjoint(_LORE_DND_DISABLED)
    # the empty fixture is the ONLY one disabling search+read (the L2-1 reach argument).
    assert {"lore_search", "lore_read"} <= _SUBSET
    assert {"lore_search", "lore_read"} <= _LORE_DND_ENABLED


# --------------------------------------------------------------------------- #
# Helpers.
# --------------------------------------------------------------------------- #
def _make_config(
    tmp_path: Path,
    enabled: frozenset[str] | None = None,
    *,
    identity: str | None = None,
) -> LoreConfig:
    """A valid :class:`LoreConfig` with an optional ``tools:`` allowlist / identity.

    ``enabled is None`` ⇒ no ``tools:`` section (``config.tools is None`` ⇒ all
    built-ins); a set ⇒ a ``tools.enabled`` allowlist carrying exactly those names.
    """
    config = _config(_slug(), tmp_path / "live")
    updates: dict[str, Any] = {}
    if enabled is not None:
        updates["tools"] = ToolsConfig(enabled=sorted(enabled))
    if identity is not None:
        updates["identity"] = identity
    return config.model_copy(update=updates) if updates else config


def _build(
    tmp_path: Path,
    enabled: frozenset[str] | None = None,
    *,
    identity: str | None = None,
) -> Any:
    """Build the FastMCP server for a config with the given allowlist / identity."""
    return build_mcp_server(LoreServer(_make_config(tmp_path, enabled, identity=identity)))


async def _registered_builtins(mcp: Any) -> set[str]:
    """The BUILT-IN tools currently registered on ``mcp`` (extensions excluded)."""
    names = {tool.name for tool in await mcp.list_tools()}
    return names & set(_ALL_BUILTIN_TOOL_NAMES)


def _tool_description_texts(tool: Any) -> list[str]:
    """Every agent-facing text on ONE registered tool: its top-level ``description``
    plus every per-parameter ``inputSchema`` field description.

    Shared (DRY §6) by the whole-surface token union (:func:`_served_lore_tokens`, E2)
    and the per-tool cross-reference map (:func:`_builtin_crossref_map`, MP-1) so the
    two cannot silently diverge on WHICH text they scan. The F2 defect class lives in a
    PARAMETER description, not a top-level one — a scan limited to top-level text alone
    would miss it (CLAUDE.md rename-sweep law).
    """
    texts: list[str] = [tool.description or ""]
    properties = (tool.parameters or {}).get("properties", {})
    for field_schema in properties.values():
        texts.append(field_schema.get("description") or "")
    return texts


async def _served_lore_tokens(mcp: Any) -> set[str]:
    """Every ``lore_``-shaped token across the WHOLE served surface of ``mcp``.

    The union the biconditional (E2) governs: the server ``instructions`` + every
    registered tool's top-level ``description`` + every per-parameter description.
    """
    texts: list[str] = [mcp.instructions or ""]
    for tool in await mcp.list_tools():
        texts.extend(_tool_description_texts(tool))
    tokens: set[str] = set()
    for text in texts:
        tokens |= set(_TOOL_NAME_TOKEN.findall(text))
    return tokens


async def _builtin_crossref_map(mcp: Any) -> dict[str, set[str]]:
    """Map each registered BUILT-IN ``A`` → the set of OTHER built-in names its own
    served text references (a cross-reference ``A→B``).

    The reach set MP-1 quantifies over: for each registered built-in, the ``lore_``
    tokens in its top-level + per-parameter descriptions that name a DIFFERENT built-in.
    DERIVED from the built server (as adversary-45's ``_adv_xref.py`` did), never a
    hand-list — a 16th tool or a new cross-reference extends the set automatically
    (INSTRUMENT-0, CLAUDE.md). Extensions are not part of the built-in cross-reference
    graph and are skipped.
    """
    universe = set(_ALL_BUILTIN_TOOL_NAMES)
    crossrefs: dict[str, set[str]] = {}
    for tool in await mcp.list_tools():
        if tool.name not in universe:
            continue
        named: set[str] = set()
        for text in _tool_description_texts(tool):
            named |= set(_TOOL_NAME_TOKEN.findall(text))
        referents = (named & universe) - {tool.name}
        if referents:
            crossrefs[tool.name] = referents
    return crossrefs


async def _register_only_builtins(tmp_path: Path, enabled: frozenset[str]) -> set[str]:
    """Register built-ins under ``enabled`` via the registration seam ALONE, bypassing
    ``build_mcp_server``'s boot validation.

    Used for the empty-set coverage pin (L2-1): ``build_mcp_server`` LOUD-FAILS on the
    empty TOTAL surface (Fork B), yet the ``_gated_tool`` filter must still be proven to
    run over ALL 15 registration sites at ``enabled = ∅``. Driving ``_register_tools``
    directly exercises exactly that filter code without invoking the boot-empty policy.
    """
    config = _make_config(tmp_path, enabled)
    mcp = FastMCP(name="reach-check")
    _register_tools(mcp, LoreServer(config))
    names = {tool.name for tool in await mcp.list_tools()}
    return names & set(_ALL_BUILTIN_TOOL_NAMES)


# =========================================================================== #
# PHASE 1 — MECHANISM
# =========================================================================== #


class TestConfigToolsSection:
    """A (config): the ``tools:`` allowlist parses; absent ⇒ all built-ins; an unknown
    enabled name and an empty TOTAL surface fail boot LOUDLY (Fork B)."""

    def test_absent_tools_section_is_none_and_empty_enabled_is_legal_at_parse(self) -> None:
        """Absent ``tools:`` ⇒ ``config.tools is None``; an EMPTY ``enabled`` set is
        LEGAL at the config layer (Fork B — boot, not parse, decides emptiness).

        Parse-level contract; GREEN once the config field exists (it is a STUB field).
        """
        assert "tools" in LoreConfig.model_fields
        assert ToolsConfig(enabled=[]).enabled == []  # empty is legal at parse
        assert ToolsConfig(enabled=["lore_search", "lore_read"]).enabled == [
            "lore_search",
            "lore_read",
        ]

    async def test_absent_tools_section_registers_ALL_builtins(self, tmp_path: Path) -> None:
        """Absent ``tools:`` (``config.tools is None``) ⇒ the FULL built-in surface —
        the ruled default keeps every existing ``lore.yaml`` and pin green.

        expected-RED node: none in stub (this pins the DEFAULT path, already true).
        MUTATION that reddens it: the filter defaulting to deny when ``tools is None``.
        """
        mcp = _build(tmp_path, enabled=None)
        assert await _registered_builtins(mcp) == set(_ALL_BUILTIN_TOOL_NAMES)

    async def test_unknown_enabled_name_fails_boot_LOUDLY(self, tmp_path: Path) -> None:
        """An ``enabled`` name outside the DECLARED UNIVERSE fails boot loudly, naming
        BOTH the unknown name and (evidence it validated against the universe) a known
        one — a typo cannot silently register nothing (spec §Part2 "typo safety").

        expected-RED (stub): ``test_unknown_enabled_name_fails_boot_LOUDLY`` — no
        validation exists, so ``build_mcp_server`` returns without raising.
        MUTATION that reddens a finished build: drop the universe-membership check.
        POSITIVE CONTROL below proves the loud-fail is SPECIFIC to the unknown name.
        """
        with pytest.raises(ValueError) as exc_info:
            _build(tmp_path, enabled=frozenset({"lore_search", "lore_bogus_tool"}))
        message = str(exc_info.value)
        assert "lore_bogus_tool" in message, "the loud-fail must NAME the unknown tool"
        assert "lore_search" in message or "lore_map" in message or "universe" in message.lower(), (
            "the loud-fail must show the KNOWN set (evidence it checked the universe), "
            "not merely reject blindly"
        )

    async def test_CONTROL_a_valid_allowlist_boots_without_raising(self, tmp_path: Path) -> None:
        """POSITIVE CONTROL for the two loud-fail pins: a config whose ``enabled`` names
        are all valid AND non-empty boots CLEANLY (no raise) and serves a non-empty
        surface — so the loud-fails above are specific to (unknown name / empty surface),
        not a blanket "any ``tools:`` section fails".

        Green in BOTH the stub and a finished build (it asserts no raise + non-empty
        surface, NOT that the filter narrowed the set — that is C's job)."""
        mcp = _build(tmp_path, enabled=_LORE_DND_ENABLED)  # must not raise
        assert mcp is not None
        assert await _registered_builtins(mcp), "a valid allowlist serves a non-empty surface"

    async def test_empty_total_surface_fails_boot_LOUDLY(self, tmp_path: Path) -> None:
        """FORK B: an empty ``enabled`` built-in set with NO extension tools ⇒ the TOTAL
        served surface ``(built-ins ∩ enabled) ∪ extension-tools`` is empty ⇒ boot
        LOUD-FAILS (a zero-tool server is operationally meaningless).

        expected-RED (stub): ``test_empty_total_surface_fails_boot_LOUDLY`` — no boot
        validation, so an empty-allowlist server is returned silently.
        MUTATION that reddens a finished build: skip the total-surface-empty guard.
        Its POSITIVE CONTROL is ``test_CONTROL_a_valid_allowlist_boots_without_raising``
        (one enabled tool ⇒ non-empty total ⇒ boots): the fail is emptiness, not size.
        """
        with pytest.raises(ValueError):
            _build(tmp_path, enabled=_EMPTY)


class TestUniverseIsSingleSourced:
    """B / RE-1: the declared universe is ONE production object; the test-side name is
    its alias; and it equals the registered FULL surface (the anti-drift guard, L2-3)."""

    def test_test_side_universe_is_the_SAME_object_as_production(self) -> None:
        """RE-1 mutation proof: the test-side ``_ALL_BUILTIN_TOOL_NAMES`` is literally
        the production object — not a parallel hand-list that can drift (#291). Change
        the prod frozenset and every consumer changes with it; a private copy would fail
        this identity check.
        """
        assert _suite._ALL_BUILTIN_TOOL_NAMES is _ALL_BUILTIN_TOOL_NAMES

    async def test_production_universe_equals_the_registered_full_surface(
        self, tmp_path: Path
    ) -> None:
        """The declared universe == the FULL registered built-in surface. This is the
        anti-drift guard (L2-3): a 16th ``@mcp.tool`` added without extending the
        universe reddens here (and the tool would be silently un-enablable / mis-validated).

        expected-RED node: none in stub (universe == surface today).
        MUTATION that reddens it: add a built-in tool without adding its name here.
        """
        mcp = _build(tmp_path, enabled=None)
        assert await _registered_builtins(mcp) == set(_ALL_BUILTIN_TOOL_NAMES)


class TestNeverRegisterFilter:
    """C: a disabled built-in is NEVER REGISTERED — the exact-set equality is pinned
    BOTH directions (a disabled tool ABSENT, not merely "the enabled one present")."""

    @pytest.mark.parametrize("enabled", _NONEMPTY_FIXTURES)
    async def test_registered_builtins_are_EXACTLY_the_enabled_set(
        self, tmp_path: Path, enabled: frozenset[str]
    ) -> None:
        """For every non-empty fixture, the registered built-ins == the enabled set —
        enabled tools PRESENT and disabled tools ABSENT (both directions).

        expected-RED nodes (stub): the ``[subset]`` and ``[lore-dnd]`` params — the
        allowlist is ignored, so all 15 register and the disabled tools leak in.
        (``[full]`` is green in stub — nothing is disabled there.)
        MUTATION that reddens a finished build: a ``@mcp.tool`` site left un-gated.
        """
        mcp = _build(tmp_path, enabled=enabled)
        assert await _registered_builtins(mcp) == set(enabled)

    async def test_empty_enabled_registers_EXACTLY_zero_builtins_reach_check(
        self, tmp_path: Path
    ) -> None:
        """L2-1 / INSTRUMENT-0 reach check: at ``enabled = ∅`` EXACTLY zero built-ins
        register. This makes filter coverage a CHECKED VARIABLE over all 15 sites — the
        empty fixture is the only one disabling ``lore_search``/``lore_read``, so a single
        bypassed ``@mcp.tool`` site (which would keep its tool registered regardless of
        config) survives here as ``count > 0``.

        expected-RED (stub): ``test_empty_enabled_registers_EXACTLY_zero_builtins_reach_check``
        — the filter is unbuilt, so all 15 register.
        MUTATION that reddens a finished build: leave ANY one of the 15 sites un-gated.
        """
        assert await _register_only_builtins(tmp_path, _EMPTY) == set()


class TestDisabledToolIsUncallableOnTheWire:
    """D (#296): a disabled tool is absent from ``list_tools()`` AND uncallable via the
    SDK's own dispatch — the EFFECT (#295), never a marker. Never-registration is immune
    to the wire-vs-instance split #296 names; this pin PROVES it."""

    async def test_disabled_tool_is_absent_and_uncallable(self, tmp_path: Path) -> None:
        """Under lore-dnd, ``lore_map`` is disabled: absent from ``list_tools()`` AND
        ``call_tool('lore_map', {})`` raises "Unknown tool" (the low-level dispatch has
        no handler for it) — NOT merely a filtered listing over a live wire handler.

        expected-RED (stub): ``test_disabled_tool_is_absent_and_uncallable`` — the tool
        still registers, so it is PRESENT in ``list_tools()`` and ``call_tool`` reaches
        its real handler (raising "Error executing tool lore_map: ...", NOT "Unknown
        tool"), which the ``match`` below rejects.
        MUTATION that reddens a finished build: filter ``list_tools()`` POST-construction
        while leaving the wire handler live (the #296 wrong-instance fix — this pin kills it).
        """
        assert "lore_map" in _LORE_DND_DISABLED  # fixture guard
        mcp = _build(tmp_path, enabled=_LORE_DND_ENABLED)
        names = {tool.name for tool in await mcp.list_tools()}
        assert "lore_map" not in names, "a disabled tool must be ABSENT from list_tools()"
        # PACKET 59: fastmcp raises ``NotFoundError('Unknown tool: lore_map')`` for an
        # absent tool (a ``ToolError`` sibling under ``FastMCPError``, not a subclass).
        with pytest.raises(NotFoundError, match=r"[Uu]nknown tool.*lore_map"):
            await mcp.call_tool("lore_map", {})


class TestCollisionGuardChecksTheDeclaredUniverse:
    """G (L2-4): the extension collision guard checks the DECLARED UNIVERSE, not just the
    registered set — so a DISABLED built-in's reserved name is not claimable by an
    extension (else ``tools/list`` would show the name present but bound to the WRONG
    handler, and the biconditional would stay GREEN over a forgery)."""

    async def test_disabled_builtin_name_not_claimable_by_an_extension(
        self, tmp_path: Path
    ) -> None:
        """Disable the built-in ``lore_search`` AND register an extension whose tool
        claims that exact name ⇒ ``build_mcp_server`` LOUD-FAILS (ValueError naming the
        collided name), because the name is RESERVED by the declared universe even though
        the built-in is not registered on this deploy.

        ⚠ This pin is GREEN in the stub for a DIFFERENT reason (the filter is unbuilt, so
        ``lore_search`` still registers and the *registered-set* guard fires). Its true
        discrimination is a build where the filter IS applied but the guard still checks
        only the REGISTERED set — then ``lore_search`` is unregistered, the guard misses,
        the extension shadows the name, and no ValueError is raised.
        MUTATION that reddens it: keep the guard on ``get_tool(...)`` (registered set)
        instead of ``_ALL_BUILTIN_TOOL_NAMES``.
        """
        assert BUILTIN_COLLISION_NAME == "lore_search"  # fixture guard
        enabled = frozenset(_ALL_BUILTIN_TOOL_NAMES) - {BUILTIN_COLLISION_NAME}
        config = _make_config(tmp_path, enabled)
        server = LoreServer(config).register_extension(CollidingExtension())
        with pytest.raises(ValueError, match=BUILTIN_COLLISION_NAME):
            build_mcp_server(server)

    def test_collision_guard_docstring_names_the_declared_universe(self) -> None:
        """Prose-consistency (P8d natural-language-surface class): the guard's own
        docstring must state it checks the DECLARED UNIVERSE (a disabled built-in's name
        is reserved), so a future reader does not "fix" the universe check back to the
        registered set believing the docstring's old "already exists on ``mcp``" story.

        expected-RED (stub): the current docstring only says a name that "already exists
        on ``mcp``" collides — it does not mention the universe / a disabled built-in.
        """
        from loremaster.server import _register_extension_tools

        doc = (_register_extension_tools.__doc__ or "").lower()
        assert "universe" in doc or "disabled built-in" in doc, (
            "the collision-guard docstring must teach that a DISABLED built-in's name is "
            "still reserved by the declared universe (prose must match the code)"
        )


class TestSampleToolsSectionIsGeneratedFromTheUniverse:
    """H (2B): the commented sample ``tools:`` section is GENERATED from the universe, so
    the discoverability artifact cannot drift from the code (a hand-list is the artifact
    this repo has the most receipts against)."""

    def test_sample_section_names_exactly_the_universe(self) -> None:
        """The ``lore_``-shaped tokens in the rendered sample == the declared universe
        EXACTLY — every built-in listed as an ``allow``, none extra, none missing.

        expected-RED (stub): ``render_sample_tools_section`` raises ``NotImplementedError``.
        MUTATION that reddens a finished build: hardcode the sample instead of deriving it.
        """
        sample = render_sample_tools_section()
        assert set(_TOOL_NAME_TOKEN.findall(sample)) == set(_ALL_BUILTIN_TOOL_NAMES)


# =========================================================================== #
# PHASE 2 — SERVED PROSE
#
# E4 (kickoff): do NOT parametrise the SUBSTANTIAL(>=800) / rollup / memory-stance /
# citation-substring instructions pins (``test_mcp_server.py::TestServerInstructions``)
# over reduced sets — a reduced surface is LEGITIMATELY shorter, so forcing >=800 on it
# would force padding, which is over-claim. Those pins stay FULL-SET anchors and are
# untouched here; the reduced-surface coherence is carried by the biconditional +
# structural pins below instead.
# =========================================================================== #


class TestBuildInstructionsFullSetIsByteExact:
    """E1 [ANCHOR]: ``build_instructions(_ALL_BUILTIN_TOOL_NAMES)`` reproduces today's
    served ``_INSTRUCTIONS`` BYTE-EXACT, so the whole existing instructions/CL3 family
    stays green with ZERO edits and the derivation is ADDITIVE, not a rewrite."""

    def test_full_set_reproduces_todays_instructions_byte_exact(self) -> None:
        """``build_instructions(full)`` == the INDEPENDENT transcription CL3 already
        declares (``test_comms_tool._declared_instructions`` — 7 non-comms paragraphs +
        the ruled comms block). Byte-exact against that oracle ⟺ byte-exact against the
        served ``_INSTRUCTIONS`` (CL3 pins ``_INSTRUCTIONS == _declared_instructions``).

        expected-RED (stub): ``build_instructions`` raises ``NotImplementedError``.
        MUTATION that reddens a finished build: any drift in a section builder's full-set
        output (a lost wrap-point space, a reordered clause) — the CONTROL
        ``test_comms_tool::test_CONTROL_the_declared_NON_comms_paragraphs_are_byte_exact``
        splits "comms block wrong" from "someone else's paragraph mis-transcribed".
        """
        cap = _msg().MESSAGE_BODY_MAX_CHARS
        assert build_instructions(_FULL) == _declared_instructions(cap)


class TestInstructionsInterpSiteWiresBuildInstructions:
    """WIRING (adversary-45 attack 3, FLAG #2): the ``instructions`` interpolation site
    in ``build_mcp_server`` actually CALLS ``build_instructions`` with the ENABLED set —
    not the frozen ``_INSTRUCTIONS`` literal, nor ``build_instructions(_FULL)``
    regardless of config. E2 catches an interp-site fumble only TRANSITIVELY (via tokens):
    a builder who keeps the module constant correct but wires the wrong object into
    ``mcp.instructions`` on a reduced surface would pass full/default and redden only on
    E2's reduced fixtures. This pins the served instructions byte-exact against
    ``build_instructions`` of the enabled set directly."""

    async def test_reduced_surface_instructions_are_build_instructions_of_enabled(
        self, tmp_path: Path
    ) -> None:
        """On the lore-dnd reduced surface, ``mcp.instructions`` == ``build_instructions``
        applied to the ACTUALLY-registered built-in set with ``config.identity`` — exactly
        the interp-site call. The argument is DERIVED from the registered surface (not an
        assumed effective-enabled computation), so only the true wiring passes; C
        (registered == enabled) independently pins that set == lore-dnd, and E1 forces
        ``build_instructions`` to be byte-exact over a frozenset (hence order-insensitive),
        so the reconstructed argument is deterministic.

        expected-RED (stub): ``build_instructions`` raises ``NotImplementedError`` (the
        derivation is unbuilt), so the right-hand side errors before comparison.
        MUTATION that reddens a finished build: wire ``instructions=_INSTRUCTIONS`` (the
        full literal) or ``build_instructions(_FULL)`` regardless of the enabled set.
        """
        config = _make_config(tmp_path, _LORE_DND_ENABLED)
        mcp = build_mcp_server(LoreServer(config))
        registered = frozenset(await _registered_builtins(mcp))
        assert (mcp.instructions or "") == build_instructions(
            registered, identity=config.identity
        )


class TestServedProseNamesExactlyTheEnabledTools:
    """E2 [BICONDITIONAL]: the ``lore_`` tokens across the WHOLE served surface (server
    instructions + every tool/param description) == the enabled built-in set — the single
    emergent gate that does not care HOW the prose is assembled (#295, observe the EFFECT).

    Forward (⊆): no disabled tool is named anywhere (this SUBSUMES the every-token pin at
    every subset — a surviving tool's own description must drop its cross-reference to a
    disabled neighbour). Backward (⊇): every enabled tool is named."""

    @pytest.mark.parametrize("enabled", _NONEMPTY_FIXTURES)
    async def test_served_lore_tokens_equal_the_enabled_set(
        self, tmp_path: Path, enabled: frozenset[str]
    ) -> None:
        """expected-RED nodes (stub): ``[subset]`` and ``[lore-dnd]`` — the served
        surface is the FULL ``_INSTRUCTIONS`` + all 15 descriptions (the interp rewire and
        description surgery are unbuilt), so disabled tools' names (e.g. ``lore_get_symbol``
        in ``lore_search``'s own description) leak in. (``[full]`` is green in stub.)
        MUTATION that reddens a finished build: leave a disabled neighbour's name in a
        surviving tool's description (forward ⊆), or drop an enabled tool's clause (⊇).
        """
        mcp = _build(tmp_path, enabled=enabled)
        assert await _served_lore_tokens(mcp) == set(enabled)

    async def test_empty_surface_names_no_tool(self, tmp_path: Path) -> None:
        """ANTI-VACUITY note: at ``enabled = ∅`` the biconditional ``∅ == ∅`` is trivially
        true, so this case proves little ALONE — its discrimination comes from running
        ALONGSIDE the non-trivial ``[subset]``/``[lore-dnd]`` params above (§2.5 pin 4) and
        the C reach-check. It still pins that the empty-surface instructions name NO tool
        AND that zero descriptions exist to name one.

        expected-RED (stub): ``build_instructions`` raises ``NotImplementedError``.
        """
        assert set(_TOOL_NAME_TOKEN.findall(build_instructions(_EMPTY))) == set()
        assert await _register_only_builtins(tmp_path, _EMPTY) == set()


class TestEveryDescriptionCrossRefDropsItsDisabledReferent:
    """MP-1 (adversary-45 attack 2): cross-reference guard coverage is a CHECKED
    VARIABLE over the DERIVED description graph — not the ``(referrer, referent)`` pairs
    the E2 fixtures happen to split.

    E2's forward (⊆) leg reddens only for a disabled tool that SOME E2 fixture disables
    while a referrer stays enabled — a HIDDEN CONSTANT (the pairs ``{subset, lore-dnd}``
    split; adversary-45 measured 18 of 24 description cross-references UNEXERCISED by it,
    e.g. leaking ``lore_search→lore_read`` stays GREEN across all four E2 fixtures). This
    pin ENUMERATES the actual cross-references from the built full server and, for EACH
    ``A→B``, builds the witness config ``_FULL − {B}`` (B disabled, every referrer A≠B
    enabled) and asserts the disabled referent ``B`` is absent from A's served
    description AND from the whole served surface. Coverage now grows with the graph: a
    16th tool or a new cross-reference is quantified over automatically, and a single
    hardcoded cross-reference reddens (INSTRUMENT-0, CLAUDE.md)."""

    async def test_every_crossref_drops_its_disabled_referent(self, tmp_path: Path) -> None:
        """expected-RED node (stub): this test. ``build_mcp_server`` ignores the
        allowlist and serves the FULL ``_INSTRUCTIONS`` + all 15 descriptions, so on the
        witness ``_FULL − {B}`` the disabled referent ``B``'s token is STILL present in
        every referrer's served description (``lore_search``'s description still names
        disabled ``lore_read``) and on the whole served surface. The proved-leak scenario
        adversary-45 found (``lore_search→lore_read``, one of the 18 E2-unexercised
        cross-references) is caught here.
        MUTATION that reddens a finished build: leave a disabled neighbour's name in a
        surviving tool's description, or in the served instructions.
        """
        full = _build(tmp_path, enabled=_FULL)
        crossrefs = await _builtin_crossref_map(full)
        pairs = sorted((a, b) for a, referents in crossrefs.items() for b in referents)
        # ANTI-VACUITY (INSTRUMENT-0 / #291): the ∀ below is vacuous if the enumeration
        # is empty. The full server's descriptions cross-reference heavily (adversary-45
        # enumerated 24); a build returning zero cross-references — descriptions that
        # stopped naming neighbours — is a coverage collapse, caught here rather than
        # silently waved through as a passing ∀ over nothing.
        assert len(pairs) >= 20, (
            f"expected >= 20 derived description cross-references (adversary-45 found 24); "
            f"enumerated {len(pairs)}: {pairs}"
        )
        # Group by referent B: the witness _FULL − {B} disables exactly B and keeps every
        # referrer A (A != B) enabled — one reduced build per distinct referent.
        referrers_of: dict[str, set[str]] = {}
        for referrer, referent in pairs:
            referrers_of.setdefault(referent, set()).add(referrer)
        leaks: list[str] = []
        for referent, referrers in sorted(referrers_of.items()):
            witness = frozenset(_FULL) - {referent}
            mcp = _build(tmp_path, enabled=witness)
            if referent in await _served_lore_tokens(mcp):
                leaks.append(
                    f"surface: disabled {referent} named on the served surface of "
                    f"witness _FULL−{{{referent}}}"
                )
            witness_crossrefs = await _builtin_crossref_map(mcp)
            for referrer in sorted(referrers):
                if referent in witness_crossrefs.get(referrer, set()):
                    leaks.append(
                        f"desc: {referrer}→{referent} — {referrer}'s served description "
                        f"still names disabled {referent}"
                    )
        assert not leaks, (
            f"disabled referents leaked into served text on reduced surfaces "
            f"({len(leaks)} leak(s)):\n" + "\n".join(leaks)
        )


class TestServedProseIsStructurallyCoherent:
    """E3 [STRUCTURAL]: the derivation leaves no gutted section header and no dangling
    ``->`` on ANY enabled subset — the two grammatical wrecks a clause-stripper produces.
    Modeling LADDER as ordered steps re-joined by ``->`` and dropping a section's header
    with its last clause is what eliminates the class; these pins prove it did."""

    @pytest.mark.parametrize("enabled", _ALL_FIXTURES)
    def test_no_gutted_header_and_no_dangling_arrow(self, enabled: frozenset[str]) -> None:
        """expected-RED (stub): ``build_instructions`` raises ``NotImplementedError`` for
        every fixture.
        MUTATION that reddens a finished build: strip the LADDER's disabled steps without
        re-joining (leaves ``-> ->`` / a trailing ``->``), or drop MEMORY's last clause
        while keeping the ``MEMORY:`` header (gutted header).
        """
        text = build_instructions(enabled)
        gutted = _GUTTED_HEADER.findall(text)
        assert not gutted, f"a section header was left with an empty body: {gutted!r}"
        assert "-> ->" not in text, "collapsed LADDER left a doubled arrow"
        for line in text.splitlines():
            stripped = line.strip()
            assert not stripped.startswith("->"), f"line starts with a dangling arrow: {line!r}"
            assert not stripped.endswith("->"), f"line ends with a dangling arrow: {line!r}"


class TestIdentityLineIsConfigAuthorable:
    """F [FORK A]: the IDENTITY/preamble line is config-authorable — the DEFAULT is
    today's exact string (so it does not AUTO-GENERATE an over-claim and CL3 stays green),
    and a CUSTOM string is served VERBATIM. lore-dnd authors its true identity in pkt 54;
    packet 45's obligation is only "do not auto-generate an over-claim on a reduced surface"
    (the Trust Leg-1 defect: the default IDENTITY line names a code-graph RAG / durable
    memory / fleet ledgers that a search-only instance lacks, and no ``lore_``-token pin
    can catch that natural-language over-claim)."""

    def test_default_identity_is_todays_exact_paragraph(self) -> None:
        """DEFAULT (``identity=None``) ⇒ today's exact IDENTITY paragraph, byte-exact.

        expected-RED (stub): ``build_instructions`` raises ``NotImplementedError``.
        MUTATION that reddens a finished build: derive the identity from families and
        drift the phrase, or drop the default.
        """
        from loremaster.server import _INSTRUCTIONS

        todays_identity = _INSTRUCTIONS.split("\n\n")[0]
        assert build_instructions(_FULL, identity=None).split("\n\n")[0] == todays_identity

    async def test_custom_identity_is_served_verbatim(self, tmp_path: Path) -> None:
        """A ``config.identity`` string is served VERBATIM as the first paragraph — the
        operator (who owns the allowlist) authors the true "what is this instance" claim.

        expected-RED (stub): ``build_mcp_server`` ignores ``config.identity`` and serves
        the full ``_INSTRUCTIONS``, whose first paragraph is today's over-claim, not the
        custom string.
        MUTATION that reddens a finished build: ignore ``config.identity`` / hardcode it.
        """
        custom = (
            "IDENTITY: a search-only lore instance — semantic code+docs search and "
            "hash-verified span reads, cited and freshness-honest."
        )
        mcp = _build(tmp_path, enabled=_LORE_DND_ENABLED, identity=custom)
        assert (mcp.instructions or "").split("\n\n")[0] == custom


class TestPartitionReadsOnlyRegisteredTools:
    """I (verify, don't break): the #291 read-only/mutating partition is DERIVED from the
    REGISTERED annotations — a disabled tool contributes none, so it is absent from BOTH
    partitions. This confirms packet 39's assumption ("partition input = the registered
    set") holds under filtering: the input is just smaller. (``test_mutating_set_derivation``
    builds the DEFAULT config, so it is unaffected — regression-verified separately.)"""

    async def test_partition_of_a_reduced_surface_excludes_disabled_tools(
        self, tmp_path: Path
    ) -> None:
        """expected-RED (stub): the filter is unbuilt, so all 15 register and the partition
        (correctly, over what is registered) includes the disabled tools ⇒ ``both`` is the
        full surface, not a subset of the lore-dnd enabled set.
        MUTATION that reddens a finished build: a ``@mcp.tool`` site left un-gated (its
        disabled tool keeps contributing an annotation to the partition).
        """
        mcp = _build(tmp_path, enabled=_LORE_DND_ENABLED)
        mutating, read_only = partition_tools_by_posture(await mcp.list_tools())
        both = mutating | read_only
        assert both <= set(_LORE_DND_ENABLED), "the partition may name only ENABLED tools"
        assert both.isdisjoint(_LORE_DND_DISABLED), "no DISABLED tool in either partition"
