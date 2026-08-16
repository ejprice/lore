"""CONTRACT (RED at authoring) — finding #291 / INSTRUMENT C.

The read-only / mutating tool partition MUST be DERIVED from the production
``ToolAnnotations`` the server registers, deny-by-default — never a second hand-list
maintained beside them. Design: ``docs/plans/v2/design/2026-08-09-defect-class-prevention.md``
§3 INSTRUMENT C; finding #291.

------------------------------------------------------------------------------
THE DEFECT THIS EXISTS TO KILL (finding #291, measured)

``loremaster/loremaster/server.py`` classifies every tool with the MCP SDK's typed
``mcp.types.ToolAnnotations`` (``readOnlyHint``), passed via ``FastMCP.tool(annotations=…)``.
``test_mcp_server.py`` then keeps a SECOND, hand-maintained source of truth for the same
property::

    _MUTATING_TOOLS = {"lore_remember", "lore_index", "lore_findings", "lore_comms"}

— and it has ALREADY DRIFTED: it omits ``lore_claim_task`` and ``lore_tasks``, which the
production annotations correctly mark ``readOnlyHint=False`` (a claim is a compare-and-set;
a create mints a row). The production annotation is right; the test constant is stale. This
is the repo's ONE-IMPLEMENTATION law inside a gate (a pattern/hand-list to clone is a defect
to clone, #102/#120): a hand-list beside production truth is free to disagree with it, and it
does. It matters beyond tidiness — packet 39's HOSTED_OAUTH refusal set is built from the
mutating set, so a drifted hand-list would make ``lore_claim_task`` / ``lore_tasks`` silently
WRITABLE to remote principals.

------------------------------------------------------------------------------
THE FIX — ONE PRODUCTION derivation, deny-by-default. NOT "add the two missing names" (that
re-creates the defect the day a third mutating tool is added), and NOT a second derivation in
TEST code (that re-creates it one level up — routing is not sharing).

LEAD RULING (Fable DRY review §7 + operator, 2026-08-09; DRY is priority #1): the read-only /
mutating partition is a SINGLE SOURCE OF TRUTH living as a PRODUCTION helper in ``loremaster``.
This contract PINS that production helper; packet 39 later CONSUMES it — its existing
``mutating_tool_names`` folds into a call to this one helper (FOLD-IN NOTE ONLY: packet 39's WIP
is NOT touched by this cycle).

The deliverable this contract pins (the BUILDER creates it in PRODUCTION; here it is imported,
so this contract is RED — "prod derivation absent" — until it exists):

    loremaster.server.partition_tools_by_posture(tools) -> tuple[frozenset[str], frozenset[str]]
        # returns (mutating, read_only), a pure function of the registered tools' annotations
        #   mutating  = {t.name : t.annotations.readOnlyHint is not True}   # DENY-BY-DEFAULT
        #   read_only = {t.name : t.annotations.readOnlyHint is True}

``is not True`` (deny-by-default), not ``== False``: an UNannotated tool (``readOnlyHint is
None``) counts as MUTATING, so a future tool registered without an annotation is refused, not
silently writable. This is "allowlist the safe" applied exactly.

STATED BOUND (honest, and the bridge to packet 39): the helper's input must be the UNSCOPED
registered tool set — the CALLER's responsibility. ``mcp.list_tools()`` IS that set here because
``test_mcp_server`` installs no posture; under a HOSTED posture ``list_tools()`` is FILTERED, so
packet 39 passes its unscoped accessor (``all_registered_tools()``) to the SAME helper. ONE
implementation, two callers — a caller that stays green when a production annotation is flipped
is a private copy wearing the shared name.

------------------------------------------------------------------------------
THE ASKABLE QUESTION (run it against any read-only/mutating split you write):
    "Is my read-only/mutating split READ from the production annotations, or is it a second
     list I have to keep in step with them — and does a test flip when I flip an annotation?"
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from loremaster.server import LoreServer, build_mcp_server
from mcp.types import ToolAnnotations

# The exact tools whose production annotation is mutating (``readOnlyHint=False``). This is an
# INDEPENDENT oracle of expected CONTENTS — a behavioural anchor, read/named here, NOT derived
# from the same ``list_tools()`` it checks — so it catches a real tool being MIS-annotated
# (a wrong build could derive "correctly" from wrong annotations). ``lore_claim_task`` and
# ``lore_tasks`` are the two #291 dropped, present here on purpose.
EXPECTED_MUTATING_TOOLS = frozenset(
    {
        "lore_remember",
        "lore_index",
        "lore_findings",
        "lore_comms",
        "lore_claim_task",
        "lore_tasks",
    }
)
# The read ladder — every tool that does NOT mutate index / memory / ledger state.
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

# A synthetic tool name used for the deny-by-default / reads-the-tool-set controls. Registered
# with NO annotations, it is the case a ``== False`` build would silently mis-file as read-only.
_UNANNOTATED_PROBE = "lore_probe_unannotated_cd"


def _spec_partition(tools: list[Any]) -> tuple[frozenset[str], frozenset[str]]:
    """The CONTRACT's own, independent statement of the derivation predicate — the GRADING ORACLE.

    This is NOT a second source of truth any CONSUMER uses (the ruling forbids that); it is the
    contract's independent oracle, read here ONLY to grade the production helper, so the equality
    pin is ``prod_helper == spec``: two independent computations of the predicate, never
    ``derived == derived`` (the "oracle independent of subject" shape from
    ``test_anchored_pattern_seam``). Deny-by-default: an annotation-less tool is mutating.
    """
    mutating: set[str] = set()
    read_only: set[str] = set()
    for tool in tools:
        annotations = getattr(tool, "annotations", None)
        read_only_hint = getattr(annotations, "readOnlyHint", None) if annotations else None
        if read_only_hint is True:
            read_only.add(tool.name)
        else:  # None (unannotated) or False -> mutating. DENY-BY-DEFAULT.
            mutating.add(tool.name)
    return frozenset(mutating), frozenset(read_only)


def _import_derivation() -> Any:
    """Lazily import the BUILDER's deliverable — the PRODUCTION single-source helper.

    Lazy (not module-level) on purpose: while this contract is RED the symbol does not exist,
    and a module-level import would make COLLECTION fail for the whole file instead of failing
    each pin behaviourally with a clear message (the ``_auth_fixtures`` convention).
    """
    try:
        from loremaster.server import partition_tools_by_posture  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - the RED state at authoring
        pytest.fail(
            "finding #291 deliverable ABSENT: expected ONE PRODUCTION helper "
            "`loremaster.server.partition_tools_by_posture(tools) -> (mutating, read_only)`, "
            "deny-by-default (`readOnlyHint is not True` -> mutating), as the SINGLE source of "
            "truth for the tool-posture partition (packet 39 consumes it — fold-in). Until it "
            f"exists the read-only/mutating split is a hand-list beside production truth. ({exc})"
        )
    return partition_tools_by_posture


def _build_tools(tmp_path: Path, *, prepare: Any = None) -> Any:
    """Build the real server store-free and return ``await mcp.list_tools()``.

    ``build_mcp_server`` + ``list_tools`` touch no store (registration only), so this needs
    neither a live SurrealDB nor the module-local surreal fixture — measured (probe_cd, this
    cycle). ``prepare(mcp)`` may register an adversarial fixture tool before listing.
    """
    from loremaster.config import LoreConfig  # noqa: PLC0415

    # Minimal valid config; the surreal/embedding blocks name env-var keys resolved lazily at
    # SERVE time, never at build — so no credentials are required to enumerate the surface.
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": f"cd_{tmp_path.name}", "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": 2048,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            "url": "ws://127.0.0.1:18000",
            "namespace": "test_cd",
            "user_env": "LORE_SURREAL_USER_CD",
            "password_env": "LORE_SURREAL_PASS_CD",
        },
        "roots": [
            {
                "tier": "custom",
                "watch": "live",
                "path": str(tmp_path / "live"),
                "include": ["**/*.py"],
            }
        ],
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
    config = LoreConfig.model_validate(payload)
    mcp = build_mcp_server(LoreServer(config))
    if prepare is not None:
        prepare(mcp)
    # Returns the ``list_tools()`` coroutine (async under fastmcp too); every caller awaits
    # ``_build_tools(...)``, so the awaitable is awaited exactly once at the call site.
    return mcp.list_tools()


def _register_unannotated(mcp: Any) -> None:
    """Register a tool with NO annotations — the deny-by-default / hardcode discriminator."""

    def probe() -> str:
        """A newly contributed tool whose author forgot the annotation."""
        return "cd-ok"

    # PACKET 59: fastmcp add_tool is single-arg; the name rides the mcp.tool(...) decorator.
    # No annotations kwarg → the tool carries NO readOnlyHint, so partition_tools_by_posture
    # classifies it MUTATING (deny-by-default), which is exactly what this probe pins.
    mcp.tool(name=_UNANNOTATED_PROBE)(probe)


def _live_annotation_constants() -> frozenset[str]:
    """The LIVE surface of EVERY production tool-annotation constant.

    Derived from ``loremaster.server`` on every call — every module global whose name ends
    ``_ANNOTATIONS`` and is a ``ToolAnnotations`` (read-only AND mutating alike). This is the
    surface the LEG-B ∀ mutation proof ranges over; deriving it LIVE (never a hand-list in the
    test) is what makes the proof's reach a CHECKED VARIABLE — a new annotation constant added
    to production joins the surface the day it lands, so the ∀ grows with production instead of
    silently under-covering (finding #347, the reach-is-a-hidden-constant class). Mirrors R16's
    ``sdk_bound_handler_names`` DERIVED (never listed) set in ``test_wire_discipline``. Measured
    at HEAD (probe, this cycle): six constants (``_READ_ONLY``, ``_SAVE_MEMORY``, ``_INDEX``,
    ``_TASK_TOOL``, ``_FINDINGS_TOOL``, ``_COMMS_TOOL``) govern all fifteen tools, and flipping
    each to its OPPOSITE ``readOnlyHint`` rebuilds the surface with exactly its tool(s) moved.
    """
    import loremaster.server as server_module  # noqa: PLC0415

    return frozenset(
        name
        for name in dir(server_module)
        if name.endswith("_ANNOTATIONS")
        and isinstance(getattr(server_module, name), ToolAnnotations)
    )


def _flip_to_opposite(annotation: ToolAnnotations) -> ToolAnnotations:
    """The same annotation with ``readOnlyHint`` flipped to its opposite posture.

    Direction-agnostic so the ∀ proof ranges over EVERY constant: a mutating constant
    (``readOnlyHint`` False/None) flips to read-only (True); a read-only constant (True) flips
    to mutating (False). Only ``readOnlyHint`` matters to the partition; the other hints are
    fixed to inert values.
    """
    new_hint = False if annotation.readOnlyHint is True else True
    return ToolAnnotations(
        readOnlyHint=new_hint, destructiveHint=False, idempotentHint=False, openWorldHint=False
    )


# --------------------------------------------------------------------------- #
# The deliverable must EXIST and be SHARED (the "derivation absent" RED).
# --------------------------------------------------------------------------- #


async def test_the_production_partition_helper_exists(tmp_path: Path) -> None:
    """RED until the builder ships ``loremaster.server.partition_tools_by_posture`` in PRODUCTION.

    WRONG BUILD THIS KILLS: doing nothing (the drift stays), OR putting the derivation in TEST
    code (the ruling requires ONE production source of truth packet 39 can consume). Its absence
    is the defect.
    """
    derive = _import_derivation()
    tools = await _build_tools(tmp_path)
    mutating, read_only = derive(tools)
    assert mutating and read_only, "the derivation returned an empty partition (anti-vacuity)"


# --------------------------------------------------------------------------- #
# Invariant (a): every registered tool carries a non-None readOnlyHint.
# --------------------------------------------------------------------------- #


async def test_every_registered_tool_carries_a_non_none_read_only_hint(
    tmp_path: Path,
) -> None:
    """A tool registered without a ``readOnlyHint`` is a design gap, not a default.

    GREEN at HEAD (all 15 tools annotate one) and goes RED the day a tool ships without one —
    which is exactly a silently-writable hole under deny-by-default. WRONG BUILD THIS KILLS:
    a new tool added with ``annotations=None`` slips in unnoticed.
    """
    tools = await _build_tools(tmp_path)
    missing = [
        tool.name
        for tool in tools
        if getattr(tool, "annotations", None) is None
        or tool.annotations.readOnlyHint is None
    ]
    assert not missing, (
        f"tool(s) registered without an explicit readOnlyHint: {sorted(missing)}. Under "
        f"deny-by-default that is a silently-mutating hole — annotate each one."
    )


async def test_the_non_none_hint_pin_is_not_vacuous(tmp_path: Path) -> None:
    """POSITIVE CONTROL for the pin above: it FIRES on an unannotated tool.

    A pin never observed rejecting anything is indistinguishable from one that cannot. Register
    a tool with no annotations and prove the non-None property is violated for it — so the pin
    above is a real gate, not decoration.
    """
    tools = await _build_tools(tmp_path, prepare=_register_unannotated)
    by_name = {tool.name: tool for tool in tools}
    probe = by_name[_UNANNOTATED_PROBE]
    assert probe.annotations is None or probe.annotations.readOnlyHint is None, (
        "the unannotated fixture tool unexpectedly carries a readOnlyHint; the control cannot "
        "demonstrate the non-None pin firing"
    )


# --------------------------------------------------------------------------- #
# The partition is a genuine DERIVATION: covers the surface, deny-by-default, live.
# --------------------------------------------------------------------------- #


async def test_the_partition_covers_the_surface_exactly_and_is_disjoint(
    tmp_path: Path,
) -> None:
    """mutating ∪ read_only == every registered tool; mutating ∩ read_only == ∅; both non-empty.

    Anti-vacuity + coverage. WRONG BUILD THIS KILLS: a derivation that classifies only some
    tools (a partial partition reads as "no mutating tools leaked" while a whole class is
    unclassified).
    """
    derive = _import_derivation()
    tools = await _build_tools(tmp_path)
    surface = frozenset(tool.name for tool in tools)
    mutating, read_only = derive(tools)
    assert mutating, "the mutating partition is empty (anti-vacuity: the derivation is broken)"
    assert read_only, "the read-only partition is empty (anti-vacuity)"
    assert not (mutating & read_only), (
        f"a tool is in BOTH partitions: {sorted(mutating & read_only)}"
    )
    assert (mutating | read_only) == surface, (
        "the partition does not cover the registered surface exactly; unclassified: "
        f"{sorted(surface - (mutating | read_only))}, phantom: "
        f"{sorted((mutating | read_only) - surface)}"
    )


async def test_deny_by_default_an_unannotated_tool_is_mutating(tmp_path: Path) -> None:
    """An unannotated tool lands in MUTATING, never read_only — and this reads the TOOL SET.

    WRONG BUILDS THIS KILLS, both at once:
    * ``== False`` instead of ``is not True`` — a ``None`` hint would then fall through to
      read_only (silently writable), the exact hole the finding names;
    * a HARDCODED ``return ({…}, {…})`` that ignores ``tools`` — it would never see the
      freshly-registered probe at all, so the probe would be absent from both partitions and
      fail this and the coverage pin.
    """
    derive = _import_derivation()
    tools = await _build_tools(tmp_path, prepare=_register_unannotated)
    mutating, read_only = derive(tools)
    assert _UNANNOTATED_PROBE in mutating, (
        f"{_UNANNOTATED_PROBE!r} (readOnlyHint=None) must be MUTATING under deny-by-default; "
        f"a `== False` predicate or a hardcoded set would drop it. mutating={sorted(mutating)}"
    )
    assert _UNANNOTATED_PROBE not in read_only, (
        f"{_UNANNOTATED_PROBE!r} leaked into the read-only set — deny-by-default violated"
    )


async def test_the_derivation_equals_the_spec_predicate(tmp_path: Path) -> None:
    """The deliverable == the contract's INDEPENDENT statement of the predicate.

    Two independent computations of ``readOnlyHint is not True`` over the real surface, so this
    is not ``derived == derived``. WRONG BUILD THIS KILLS: a subtly different predicate (e.g.
    keying on ``destructiveHint`` or a name substring).
    """
    derive = _import_derivation()
    tools = await _build_tools(tmp_path)
    spec_mutating, spec_read_only = _spec_partition(tools)
    mutating, read_only = derive(tools)
    assert frozenset(mutating) == spec_mutating, (
        f"derived mutating != spec mutating; only-in-derived={sorted(set(mutating) - spec_mutating)}, "
        f"only-in-spec={sorted(spec_mutating - set(mutating))}"
    )
    assert frozenset(read_only) == spec_read_only, (
        f"derived read_only != spec read_only; only-in-derived={sorted(set(read_only) - spec_read_only)}, "
        f"only-in-spec={sorted(spec_read_only - set(read_only))}"
    )


def test_the_live_annotation_surface_is_not_empty_and_names_the_known_constants() -> None:
    """ANTI-VACUITY for the derived flip surface — mirrors R16's
    ``test_the_handler_derivation_is_not_empty`` (``test_wire_discipline``).

    An empty surface would turn the LEG-B ∀ mutation proof into a ∀ over nothing — a gate that
    reads as a pass, the direction that always costs. And the surface must still SEE the
    constants we have #291/#347 receipts against, so a derivation that silently drops one (the
    reach quietly shrinking) is caught HERE with a clear message, not by a tool going unverified
    downstream.
    """
    surface = _live_annotation_constants()
    assert surface, (
        "the live annotation surface is EMPTY — the LEG-B ∀ flip would be vacuous. The "
        "derivation over `loremaster.server` found no `*_ANNOTATIONS` constant; either the "
        "constants were renamed out of the pattern or the module failed to import."
    )
    for known in (
        "_READ_ONLY_ANNOTATIONS",
        "_TASK_TOOL_ANNOTATIONS",
        "_FINDINGS_TOOL_ANNOTATIONS",
        "_COMMS_TOOL_ANNOTATIONS",
    ):
        assert known in surface, (
            f"{known} — an annotation constant with a #291/#347 receipt against it — dropped "
            f"out of the live surface `_live_annotation_constants()`; the reach derivation has "
            f"drifted and the ∀ flip would silently skip it. surface={sorted(surface)}"
        )


@pytest.mark.parametrize("constant_name", sorted(_live_annotation_constants()))
async def test_the_derivation_is_live_over_every_annotation_constant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, constant_name: str
) -> None:
    """MUTATION PROOF, ∀ OVER THE LIVE ANNOTATION SURFACE (finding #347, IDIOM 1 LEG B).

    Generalises the old single-constant proof (which flipped only ``_TASK_TOOL_ANNOTATIONS`` —
    reach two tools of fifteen) to EVERY annotation constant, reusing the ``_core_dropping``
    structure from ``test_store_seam_one_derivation`` (healthy baseline → a LANDING ASSERT that
    the mutation took, CLAUDE.md #194 → the caller-reflects assertion) with the flip-hint
    mechanism in place of drop-seam. For EACH constant: flip its ``readOnlyHint`` to the OPPOSITE
    posture (direction-agnostic, so a read-only constant flips to mutating and vice versa),
    rebuild the production surface, and assert the PRODUCTION partition tracks the flip EXACTLY
    (derived == spec on the flipped surface — LEG A's equality check applied to a mutated
    production source, which is what makes it a liveness proof).

    WRONG BUILD THIS KILLS — C-WB5, the #347 survivor (adversary-cd): a derivation that reads
    the annotations for every tool EXCEPT one it HARDCODES (measured: hardcodes ``lore_findings``
    mutating). The old proof never flipped that tool's constant, so C-WB5 passed all ten pins.
    Here, when ``_FINDINGS_TOOL_ANNOTATIONS`` is the parametrized member, the spec moves
    ``lore_findings`` to read_only but the hardcode keeps it mutating → derived != spec → RED.
    Reach is no longer a hidden constant; it is the live surface, and this test grows with it.
    """
    derive = _import_derivation()
    import loremaster.server as server_module  # noqa: PLC0415

    # Baseline (healthy positive control): the spec partition BEFORE the flip.
    spec_mutating_baseline, _ = _spec_partition(await _build_tools(tmp_path))

    monkeypatch.setattr(
        server_module,
        constant_name,
        _flip_to_opposite(getattr(server_module, constant_name)),
    )
    flipped_tools = await _build_tools(tmp_path)
    spec_mutating_flipped, spec_read_only_flipped = _spec_partition(flipped_tools)

    # LANDING ASSERT (#194, reused from `_core_dropping`): the flip actually MOVED ≥1 tool per
    # the INDEPENDENT spec oracle (direction-agnostic — the symmetric difference), so this ∀
    # member is not a vacuous flip that tests nothing.
    moved = spec_mutating_baseline ^ spec_mutating_flipped
    assert moved, (
        f"flipping production constant {constant_name} did not change the spec partition — it "
        f"governs no tool, so this ∀ member would pass without testing anything. The surface "
        f"derivation may include a constant that annotates no registered tool."
    )

    # THE CALLER REFLECTS THE MUTATION: the production derivation tracks the flipped annotations
    # EXACTLY, both partitions. A hardcode/hand-list of any tool this constant governs — in
    # EITHER direction — diverges from the spec.
    derived_mutating, derived_read_only = derive(flipped_tools)
    assert frozenset(derived_mutating) == spec_mutating_flipped, (
        f"after flipping {constant_name}, the derived MUTATING set diverges from the spec — the "
        f"derivation did not track the flip for every tool the constant governs (a hardcode / "
        f"hand-list, C-WB5's shape). only-in-derived="
        f"{sorted(frozenset(derived_mutating) - spec_mutating_flipped)}, only-in-spec="
        f"{sorted(spec_mutating_flipped - frozenset(derived_mutating))}"
    )
    assert frozenset(derived_read_only) == spec_read_only_flipped, (
        f"after flipping {constant_name}, the derived READ-ONLY set diverges from the spec — the "
        f"moved tools {sorted(moved)} were not tracked. only-in-derived="
        f"{sorted(frozenset(derived_read_only) - spec_read_only_flipped)}, only-in-spec="
        f"{sorted(spec_read_only_flipped - frozenset(derived_read_only))}"
    )


async def test_the_flip_surface_reaches_every_tool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """META-RECURSION (finding #347): the LEG-B flip surface's REACH is a CHECKED VARIABLE.

    The class #347 lives in is reach-is-a-hidden-constant: a proof that flips ONE constant
    verifies liveness only for the tools THAT constant governs. This pin proves the flip surface
    (``_live_annotation_constants()``) reaches EVERY registered tool — flip each constant in turn
    (via the SPEC oracle, INDEPENDENT of the production helper), union the tools that change
    partition, and assert that union equals the FULL registered surface. A surface that omitted
    the constant governing some tool (a hand-list regression, e.g. the old reach of 2/15), or a
    tool annotated inline instead of via a named constant, leaves that tool unreached → RED,
    naming it — so no tool's classification is unverifiable by the ∀ proof.

    Oracle-based ON PURPOSE: this pins the SURFACE's coverage, not the helper's liveness (the
    per-constant ∀ test above owns that). Separating them keeps each instrument single-purpose —
    and this is the pin that reddens if a future author shrinks the surface derivation back to a
    hand-list, which is exactly how #347 would recur.
    """
    import loremaster.server as server_module  # noqa: PLC0415

    baseline_tools = await _build_tools(tmp_path)
    spec_mutating_baseline, spec_read_only_baseline = _spec_partition(baseline_tools)
    full_surface = spec_mutating_baseline | spec_read_only_baseline

    reached: set[str] = set()
    for constant_name in sorted(_live_annotation_constants()):
        with monkeypatch.context() as patched:
            patched.setattr(
                server_module,
                constant_name,
                _flip_to_opposite(getattr(server_module, constant_name)),
            )
            spec_mutating_flipped, _ = _spec_partition(await _build_tools(tmp_path))
        reached |= spec_mutating_baseline ^ spec_mutating_flipped

    unreached = full_surface - reached
    assert not unreached, (
        f"the LEG-B flip surface does NOT reach every registered tool: {sorted(unreached)} are "
        f"governed by an annotation constant ABSENT from the live surface "
        f"`_live_annotation_constants()` (or annotated inline, not via a named constant) — reach "
        f"is a hidden constant (finding #347). Grow the surface derivation, or a tool's "
        f"classification is verified by no ∀ member."
    )


def test_the_flip_hint_technique_discriminates_a_live_read_from_a_hardcode() -> None:
    """POSITIVE CONTROL ON THE PROBE (CLAUDE.md "a probe needs a control"; mirrors the store-seam
    file's ``TestTheMutationProofDiscriminates``).

    Proves the flip-hint technique the ∀ proof relies on actually tells a LIVE annotation read
    from a HARDCODE, independent of the real build — so a green LEG-B pin is not decoration.
    GREEN now and after: a self-contained demonstration that flipping the hint MOVES a reader and
    does NOT move a hardcode (C-WB5's shape).
    """
    mutating_annotation = ToolAnnotations(readOnlyHint=False)
    read_only_annotation = ToolAnnotations(readOnlyHint=True)

    def live_read(annotation: ToolAnnotations) -> str:
        return "read_only" if annotation.readOnlyHint is True else "mutating"

    def hardcode(_annotation: ToolAnnotations) -> str:
        return "mutating"  # C-WB5's shape: ignores the annotation entirely

    assert live_read(mutating_annotation) == "mutating"
    assert live_read(read_only_annotation) == "read_only", (
        "the live reader must MOVE when the hint is flipped — else the flip technique is inert "
        "and the ∀ proof above could not observe liveness"
    )
    assert hardcode(mutating_annotation) == "mutating"
    assert hardcode(read_only_annotation) == "mutating", (
        "the hardcode must NOT move when the hint is flipped — else the LEG-B ∀ proof could not "
        "fail C-WB5 (a hardcode that agrees with the annotations at HEAD)"
    )


# --------------------------------------------------------------------------- #
# Independent expected-CONTENTS oracle (catches a real tool MIS-annotated).
# --------------------------------------------------------------------------- #


async def test_the_known_mutating_tools_are_in_the_mutating_partition(
    tmp_path: Path,
) -> None:
    """The behaviourally-mutating tools — INCLUDING the two #291 dropped — are mutating.

    Oracle read independently of the derivation (named contents, not re-derived), so it catches
    a real tool whose production annotation is WRONG. GREEN at HEAD (production is correct); the
    value is it stays a check the day someone mis-annotates ``lore_tasks``.
    """
    derive = _import_derivation()
    tools = await _build_tools(tmp_path)
    mutating, _ = derive(tools)
    missing = EXPECTED_MUTATING_TOOLS - frozenset(mutating)
    assert not missing, (
        f"tool(s) that mutate state are NOT in the derived mutating set: {sorted(missing)} — "
        f"their production annotation is mis-set (this is the #291 drift class)."
    )


async def test_the_known_read_only_tools_are_in_the_read_only_partition(
    tmp_path: Path,
) -> None:
    """The read ladder is read_only. The dual oracle: a mutating tool mis-annotated read_only
    would land here (silently writable), which is the security-relevant direction.
    """
    derive = _import_derivation()
    tools = await _build_tools(tmp_path)
    _, read_only = derive(tools)
    missing = EXPECTED_READ_ONLY_TOOLS - frozenset(read_only)
    assert not missing, (
        f"read-only tool(s) not in the derived read-only set: {sorted(missing)}"
    )


# --------------------------------------------------------------------------- #
# The #291 instance: no drifted hand-list may remain beside the derivation.
# --------------------------------------------------------------------------- #


async def test_no_drifted_hand_list_survives_beside_the_derivation(
    tmp_path: Path,
) -> None:
    """RED at HEAD: ``test_mcp_server._MUTATING_TOOLS`` == 4 names, the derived set == 6.

    This is the literal #291 instance. If the builder keeps a ``_MUTATING_TOOLS`` /
    ``_READ_ONLY_TOOLS`` name at all, it must EQUAL the derived partition (no drift permitted);
    the cleaner fix — and the ruling's intent — is to DELETE the constants and consume the
    production ``partition_tools_by_posture`` helper, in which case the ``getattr`` default makes
    this pin a no-op for that name. Either way a DRIFTED literal cannot survive. WRONG BUILD THIS
    KILLS: leaving the stale 4-name literal in place.

    Graded against the CONTRACT's own ``_spec_partition`` oracle, not the builder's deliverable,
    so it RED-flags the drift on its own terms even before the deliverable exists.
    """
    tools = await _build_tools(tmp_path)
    mutating, read_only = _spec_partition(tools)

    import test_mcp_server as suite  # noqa: PLC0415

    hand_mutating = getattr(suite, "_MUTATING_TOOLS", None)
    if hand_mutating is not None:
        assert frozenset(hand_mutating) == frozenset(mutating), (
            "a `_MUTATING_TOOLS` literal still stands beside the derivation and DISAGREES with "
            f"it (finding #291 drift). hand-list={sorted(hand_mutating)}, "
            f"derived={sorted(mutating)}. Replace the literal with the derivation (or make it "
            f"equal it) — do not maintain a second source of truth."
        )
    hand_read_only = getattr(suite, "_READ_ONLY_TOOLS", None)
    if hand_read_only is not None:
        assert frozenset(hand_read_only) == frozenset(read_only), (
            "a `_READ_ONLY_TOOLS` literal disagrees with the derived read-only partition; "
            f"hand-list={sorted(hand_read_only)}, derived={sorted(read_only)}."
        )
