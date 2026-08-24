"""CONTRACT (contract-61b-w2, Fork H-a) — the tool-population classification registry.

Design ``2026-08-22-packet61-pdp-audit-rulings.md`` Fork H(a), REVISED per the sidecar D2
ruling (2026-08-23): every REGISTERED tool is classified into a population —
``shared_read`` (the code/docs corpus, exempt from row-level authorization) or ``governed``
(owner+scope, routed through the PDP by 63/64). The classification is checked OVER the LIVE
tool registry (the ``partition_tools_by_posture``-over-the-live-list precedent, ``loremaster.
server``), so a NEW registered tool is CAUGHT by construction.

TWO REVIEWED SETS + THE SECURITY ASYMMETRY (D2):
* ``_SHARED_READ_CORPUS_TOOLS`` — the OPEN allowlist of corpus reads reviewed as shared_read
  (lore_search/read/get_symbol/impact/map/dead_code/diff, + the corpus meta-reads verify/index).
* ``_REVIEWED_GOVERNED_TOOLS`` — the coordination tools reviewed as governed (lore_comms /
  memory (recall/remember) / tasks (tasks/claim_task) / findings).
* RUNTIME DEFAULT = ``governed`` (FAIL-CLOSED). The security asymmetry: a governed tool
  mistaken as shared_read = a cross-principal LEAK (catastrophic); a shared_read tool mistaken
  as governed = broken functionality (loud/safe). So an UNREVIEWED tool is ``governed`` at
  runtime — never opened by default. ``partition_tools_by_population`` returns
  ``(shared_read, governed)`` where ``shared_read = allowlist ∩ live`` and ``governed`` = every
  other live tool. ``_REVIEWED_GOVERNED_TOOLS`` is the REVIEW-completeness marker for the growth
  pin below — it is NOT a runtime blocklist (the runtime defaults governed regardless), so it is
  not the fail-open governed-blocklist the reach law forbids.

THE GROWTH PIN (reach law #344/#345 / INSTRUMENT-0 — "reds until REVIEWED"): a LIVE registered
tool in NEITHER reviewed set REDS, forcing a human to review each NEW tool (else a new corpus
tool is silently over-gated, or a new coordination tool's classification is unconfirmed). At 61
the seed is GREEN (every current tool is reviewed); a synthetic new tool reds it, while the
runtime meanwhile defaults it GOVERNED (asserted — never open).

FORWARD-NOTE (ledger, NOT a 61 pin): 63/64 should move to a per-tool POPULATION ANNOTATION (no
central sets — the purest reach form, mirroring ``ToolAnnotations.readOnlyHint``) as the
verb-routing carries it. The two-set + growth-pin is the right-sized SEED at 61.

⚠ RED at HEAD: ``loremaster.server`` exports none of ``partition_tools_by_population`` /
``_SHARED_READ_CORPUS_TOOLS`` / ``_REVIEWED_GOVERNED_TOOLS`` → ImportError (every node here RED
via collection error). No ``# type: ignore`` (a forward-ref suppression orphans on GREEN — the
C-DEF "still clean after the build" leg); this is an ADJUDICATED mypy attr-defined error at HEAD
that mypy-clears the moment the builder lands the symbols.

⚠ Classification note surfaced to lead-61 (brief-base §2): D2's SHARED_READ list named the 7
code/docs corpus tools; the LIVE registry also carries ``lore_verify`` (a corpus claim-check
read) and ``lore_index`` (a corpus freshness/health read), which carry no owner+scope. I
classified BOTH as shared_read (corpus reads) so the growth pin's seed is GREEN. If you prefer
to over-gate them (governed — the fail-safe direction), move them to ``_REVIEWED_GOVERNED_TOOLS``;
either keeps the seed green. The representative-fixture pins below do NOT depend on this choice.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# RED at HEAD: none of these exist yet (the builder lands them in loremaster.server) — clean
# forward-references, so these imports are ADJUDICATED mypy attr-defined errors at HEAD that
# mypy-clear the moment the builder lands the symbols, with no suppression comment to orphan.
from loremaster.server import (
    _REVIEWED_GOVERNED_TOOLS,
    _SHARED_READ_CORPUS_TOOLS,
    partition_tools_by_population,
)
from mcp.types import ToolAnnotations
from test_mutating_set_derivation import _build_tools  # the store-free live-registry builder

# Representative tools per population, with DIFFERENT values per bucket (fixtures-must-
# discriminate, PKT-28 C1): two corpus reads that MUST be shared_read, two coordination tools
# that MUST be governed. A build classifying everything one way is caught by the OTHER bucket.
# NOT the full classification (that would be the hand-list the reach law rejects) — just enough
# to discriminate the two directions.
_REPRESENTATIVE_SHARED_READ = frozenset({"lore_search", "lore_get_symbol"})
_REPRESENTATIVE_GOVERNED = frozenset({"lore_comms", "lore_findings"})

_SYNTH_NEW_TOOL = "lore_probe_synth_population_w2"
_SYNTH_BODY_MARKER = "SYNTH-POP-W2"


def _register_synth_tool(mcp: Any) -> None:
    """A ``prepare`` callback registering a SYNTHETIC NEW tool in NEITHER reviewed set (mirrors
    ``test_readonly_guard``'s ``_register_synth_tools``). It is the growth-pin mutation: a new
    tool the classification has never seen, proving (a) the growth pin reds until it is reviewed,
    and (b) the runtime defaults it GOVERNED (fail-closed), never opened."""

    def synth() -> str:
        return _SYNTH_BODY_MARKER

    mcp.tool(name=_SYNTH_NEW_TOOL, annotations=ToolAnnotations(openWorldHint=False))(synth)


async def _live_tool_names(tmp_path: Path, *, prepare: Any = None) -> frozenset[str]:
    tools = await _build_tools(tmp_path, prepare=prepare)
    return frozenset(tool.name for tool in tools)


class TestPartitionToolsByPopulationCoversTheLiveRegistry:
    """Runtime totality + disjointness over the DERIVED (live-registry) set — no tool silently
    NEITHER, no tool in BOTH (reach law #344/#345)."""

    async def test_every_registered_tool_is_classified_into_exactly_one_population(
        self, tmp_path: Path
    ) -> None:
        """Over the REAL registered surface: ``shared_read | governed`` == every live tool name,
        and ``shared_read & governed`` == ∅. A tool classified as NEITHER (a partition that drops
        a tool) reds. Mutation-prove: make the partition omit any tool from both sets → reds."""
        tools = list(await _build_tools(tmp_path))
        live_names = frozenset(tool.name for tool in tools)
        shared_read, governed = partition_tools_by_population(tools)
        assert live_names, "the live registry is empty — the coverage pin is vacuous"
        assert shared_read | governed == live_names, (
            "partition_tools_by_population must classify EVERY registered tool — a tool in "
            f"NEITHER runtime population: missing={sorted(live_names - (shared_read | governed))!r}"
        )
        assert shared_read & governed == frozenset(), (
            f"a tool was classified into BOTH runtime populations: {sorted(shared_read & governed)!r}"
        )


class TestPartitionToolsByPopulationDefaultsGoverned:
    """The security asymmetry (D2): unknown → governed (fail-closed), never silently shared_read."""

    async def test_an_unknown_tool_is_governed_by_default_never_shared_read(
        self, tmp_path: Path
    ) -> None:
        """A SYNTHETIC tool registered on the live server (in neither reviewed set) →
        ``governed`` (needs authorization), NEVER ``shared_read``. Proves the reach is DERIVED
        over the live registry (the synthetic tool GROWS the classified set) AND that the default
        is FAIL-CLOSED. Mutation-prove: a build that defaulted unknown tools to shared_read (a
        governed blocklist / fail-open) reds this — the catastrophic-leak direction of the
        asymmetry."""
        tools = list(await _build_tools(tmp_path, prepare=_register_synth_tool))
        names = frozenset(tool.name for tool in tools)
        assert _SYNTH_NEW_TOOL in names, "the synthetic tool did not register — the pin is vacuous"
        shared_read, governed = partition_tools_by_population(tools)
        assert _SYNTH_NEW_TOOL in governed, (
            "a synthetic (unreviewed) tool must default to GOVERNED (fail-closed): "
            f"shared_read={sorted(shared_read)!r}"
        )
        assert _SYNTH_NEW_TOOL not in shared_read, (
            "a synthetic (unreviewed) tool was silently classified shared_read — the runtime is "
            "fail-OPEN (a governed blocklist), the catastrophic-leak direction (D2 asymmetry)"
        )


class TestTheGrowthPinRedsUntilANewToolIsReviewed:
    """The reds-until-REVIEWED growth pin (D2 / reach law): a LIVE tool in neither reviewed set
    reds, forcing a human to review each NEW tool. The seed (61) is GREEN — every current tool
    is reviewed; a synthetic new tool reds it while the runtime defaults it governed."""

    async def test_every_live_tool_is_reviewed_into_a_population(self, tmp_path: Path) -> None:
        """THE GROWTH PIN: every LIVE registered tool is in ``_SHARED_READ_CORPUS_TOOLS`` OR
        ``_REVIEWED_GOVERNED_TOOLS``. A tool in NEITHER reds — forcing a human to classify each
        new tool (a new corpus tool would otherwise be silently over-gated; a new coordination
        tool's governed classification would be unconfirmed). GREEN at the 61 seed (all reviewed);
        REDS the day a new tool is registered without review."""
        live_names = await _live_tool_names(tmp_path)
        # Adversary (C) ANTI-VACUITY (INSTRUMENT-0): the growth pin is vacuous-green on an EMPTY
        # registry (0 tools → 0 unreviewed → passes). Assert the DERIVED live set is non-empty
        # and re-derived each run, so a broken registry-enumeration reds instead of falsely
        # passing — the guard's OWN coverage is a checked variable.
        assert live_names, (
            "the live tool registry is EMPTY — the reds-until-reviewed growth pin would pass "
            "vacuously (0 tools → 0 unreviewed). The registry enumeration is broken."
        )
        reviewed = _SHARED_READ_CORPUS_TOOLS | _REVIEWED_GOVERNED_TOOLS
        unreviewed = live_names - reviewed
        assert not unreviewed, (
            "live tools not yet reviewed into a population — classify each into "
            "_SHARED_READ_CORPUS_TOOLS or _REVIEWED_GOVERNED_TOOLS (reds-until-reviewed, D2): "
            f"{sorted(unreviewed)!r}"
        )

    async def test_a_synthetic_new_tool_is_unreviewed_and_defaults_governed(
        self, tmp_path: Path
    ) -> None:
        """MUTATION-PROOF of the growth pin: a synthetic NEW tool is in NEITHER reviewed set (so
        the growth pin above would red on this live set — EXACTLY one tool flagged), while the
        runtime meanwhile defaults it GOVERNED (fail-closed, not open). Both halves in one pin:
        the review-gap is detected AND the runtime is safe in the interim."""
        live_with_synth = await _live_tool_names(tmp_path, prepare=_register_synth_tool)
        reviewed = _SHARED_READ_CORPUS_TOOLS | _REVIEWED_GOVERNED_TOOLS
        assert _SYNTH_NEW_TOOL not in reviewed, (
            "the synthetic tool must be UNREVIEWED by construction (in neither set) for this "
            "mutation-proof to exercise the growth pin"
        )
        assert (live_with_synth - reviewed) == {_SYNTH_NEW_TOOL}, (
            "the growth pin must flag EXACTLY the unreviewed new tool: "
            f"{sorted(live_with_synth - reviewed)!r}"
        )
        # Runtime is safe in the review interim: the unreviewed tool is governed, not open.
        tools = list(await _build_tools(tmp_path, prepare=_register_synth_tool))
        shared_read, governed = partition_tools_by_population(tools)
        assert _SYNTH_NEW_TOOL in governed and _SYNTH_NEW_TOOL not in shared_read, (
            "an unreviewed new tool must default GOVERNED at runtime (fail-closed) while it "
            f"awaits review: shared_read={sorted(shared_read)!r}"
        )


class TestTheReviewedSetsMatchTheDesignSection1Mapping:
    """§1 semantics with discriminating fixtures: corpus reads are shared_read; coordination
    tools are governed. Different values per bucket catch a build that classifies everything one
    way (which passes totality + default-governed but is wrong)."""

    async def test_the_corpus_reads_are_shared_read(self, tmp_path: Path) -> None:
        """lore_search / lore_get_symbol (code/docs corpus reads) → shared_read (§1). A build that
        classified everything ``governed`` passes totality but reds here."""
        tools = list(await _build_tools(tmp_path))
        live_names = frozenset(tool.name for tool in tools)
        expected = _REPRESENTATIVE_SHARED_READ & live_names
        assert expected, f"none of {sorted(_REPRESENTATIVE_SHARED_READ)!r} registered — stale fixture"
        shared_read, _governed = partition_tools_by_population(tools)
        assert expected <= shared_read, (
            f"corpus reads must be shared_read (§1): missing={sorted(expected - shared_read)!r}"
        )

    async def test_the_coordination_tools_are_governed(self, tmp_path: Path) -> None:
        """lore_comms / lore_findings (coordination — owner+scope) → governed (§1). A build that
        classified everything ``shared_read`` passes totality but reds here — the OTHER direction
        the two representative buckets discriminate."""
        tools = list(await _build_tools(tmp_path))
        live_names = frozenset(tool.name for tool in tools)
        expected = _REPRESENTATIVE_GOVERNED & live_names
        assert expected, f"none of {sorted(_REPRESENTATIVE_GOVERNED)!r} registered — stale fixture"
        _shared_read, governed = partition_tools_by_population(tools)
        assert expected <= governed, (
            f"coordination tools must be governed (§1): missing={sorted(expected - governed)!r}"
        )


class TestTheReviewedSetsAreCoherent:
    """The two reviewed sets are disjoint and free of ghost entries (a stale name that matches no
    live tool is reach the classification cannot exercise — the switched-off-scanner class)."""

    def test_the_reviewed_sets_are_disjoint(self) -> None:
        """A tool cannot be BOTH reviewed-shared_read and reviewed-governed — that is a
        contradictory review. (Offline — pure set property.)"""
        overlap = _SHARED_READ_CORPUS_TOOLS & _REVIEWED_GOVERNED_TOOLS
        assert not overlap, f"a tool is in BOTH reviewed sets (contradictory): {sorted(overlap)!r}"

    async def test_neither_reviewed_set_has_ghost_entries(self, tmp_path: Path) -> None:
        """Every name in EITHER reviewed set is a LIVE registered tool — a stale entry naming a
        retired/renamed tool reds (a review record that matches nothing is reach the growth pin
        cannot exercise)."""
        live_names = await _live_tool_names(tmp_path)
        ghosts = (_SHARED_READ_CORPUS_TOOLS | _REVIEWED_GOVERNED_TOOLS) - live_names
        assert not ghosts, (
            f"a reviewed set names tools that are not registered (ghost/stale entries): "
            f"{sorted(ghosts)!r}"
        )

    async def test_the_allowlist_does_not_exempt_the_whole_surface(self, tmp_path: Path) -> None:
        """The shared_read allowlist is the SAFE (exempt) set — it must NOT name every registered
        tool, or the ``governed`` population is empty and nothing is ever authorized (fail-open).
        At least the representative coordination tools stay governed."""
        tools = list(await _build_tools(tmp_path))
        live_names = frozenset(tool.name for tool in tools)
        _shared_read, governed = partition_tools_by_population(tools)
        assert governed, "the governed population is empty — the allowlist exempted the whole surface"
        must_govern = _REPRESENTATIVE_GOVERNED & live_names
        assert must_govern <= governed, (
            f"a coordination tool was allowlisted as shared_read: {sorted(must_govern - governed)!r}"
        )


def test_the_classification_registry_lives_in_loremaster_server() -> None:
    """ONE-HOME structural pin: the population partition + BOTH reviewed sets live in
    ``loremaster.server`` beside ``partition_tools_by_posture`` (the sibling DERIVED-over-the-
    live-registry helper), so the classification shares a home and neither drifts. RED at HEAD."""
    from loremaster import server  # noqa: PLC0415

    for symbol in (
        "partition_tools_by_population",
        "_SHARED_READ_CORPUS_TOOLS",
        "_REVIEWED_GOVERNED_TOOLS",
    ):
        assert hasattr(server, symbol), (
            f"loremaster.server must export {symbol!r} (the classification registry, beside "
            "partition_tools_by_posture)"
        )
