"""``ImpactEngine`` — the P6-tail ``lore_impact`` verb: "who depends on this?"

``lore_impact`` (plan §5) answers, in one call, the question that today costs a
whole Explore-agent sweep: which code depends on a symbol, is it safe to touch,
and — if it looks unused — is that a heuristic or a certainty? The motivating
incident (FRICTION.md's seam-sweep entry, and a near-miss this session where a
production base class was almost deleted on an undercounted reference profile)
is why every verdict this engine returns carries an explicit epistemic caveat
(see :data:`_CAVEAT_TEXT`): astroid's static inference can UNDERCOUNT
dynamic/framework-mediated references, so a ``dead (heuristic)`` verdict is a
lead to investigate, never a deletion order.

:class:`ImpactEngine` is a PURE READ layer over the code graph
(:class:`~loremaster.graph_surreal.SurrealCodeGraph` in production, or its
in-memory test double) — it derives no new graph state and issues no new
SurrealQL; it composes the graph's existing query surface:

* :meth:`~loremaster.graph_surreal.SurrealCodeGraph.references` — the
  production/test reference-count split (the liveness signal).
* :meth:`~loremaster.graph_surreal.SurrealCodeGraph.tests_for` — the covering
  tests (the "what exercises this" signal).
* :meth:`~loremaster.graph_surreal.SurrealCodeGraph.blast_radius` — the
  transitive reverse-dependency closure, rolled up by module at ``depth > 1``
  (the ripple signal) and reused as a lightweight EXISTENCE probe (see
  :meth:`ImpactEngine._target_is_known`) for the depth-1 case.

Verdict-bearing output is NEVER served while the graph is mid-rebuild — a
truthy ``rebuild_notice()`` result makes :meth:`ImpactEngine.impact` raise
:class:`ImpactRebuildingError` before any query runs, so a caller never reads a
half-built graph's honestly-empty-looking-but-actually-incomplete answer as a
real verdict.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict

from loremaster.graph import CodeGraph, ReferenceSummary

# --------------------------------------------------------------------------- #
# Depth / consumer-cap bounds (plan §5).
# --------------------------------------------------------------------------- #

# ``depth`` clamps to this inclusive range rather than raising — the tool-
# surface convention already used for k/depth-style params elsewhere (e.g.
# ``blast_radius``'s own callers): a caller-supplied out-of-range value is a
# best-effort request, not a hard error.
_DEPTH_MIN = 1
_DEPTH_MAX = 4

# The default ceiling on rendered consumer names / module rollups when the
# caller does not specify ``max_consumers``.
_DEFAULT_MAX_CONSUMERS = 25

# The raw node ceiling ``blast_radius`` is asked for before module-rollup
# grouping (depth > 1). Deliberately generous and INDEPENDENT of
# ``max_consumers``, which caps the RENDERED module-rollup list length, not
# the raw node count the rollup is computed from.
_BLAST_RADIUS_NODE_CAP = 500

# The verdict literals. "dead (heuristic)" carries its epistemic status in the
# value itself, so a consumer can never quote the verdict without the hedge.
_VERDICT_LIVE = "live"
_VERDICT_DEAD = "dead (heuristic)"

# The caveat riding on EVERY verdict (live or dead) — the near-miss lesson,
# contractualised. Must name both the HEURISTIC nature of the count and the
# UNDERCOUNT direction of its error (astroid's static inference misses
# dynamic/framework-mediated call sites; it never fabricates a reference).
_CAVEAT_TEXT = (
    "caveat: reference counts are a HEURISTIC bounded by astroid's static "
    "inference — dynamic and framework-mediated call sites can UNDERCOUNT "
    "true usage, so a verdict is a lead to investigate, never a deletion order."
)

# The retry hint every rebuilding-error message carries.
_RETRY_HINT = "retry the impact query once the rebuild settles"

# The explicit elision-marker fragment rendered when ``max_consumers`` squeezes
# entries out of a rendered list (no-silent-caps doctrine).
_ELISION_TEMPLATE = "+{count} more (elided by max_consumers={cap})"

_T = TypeVar("_T")


class ImpactRebuildingError(Exception):
    """Raised when a verdict is requested while the code graph is rebuilding.

    Never served mid-rebuild: an honestly-empty-looking graph mid-build could
    otherwise be misread as a real ``dead (heuristic)`` verdict. The message
    carries the caller-supplied rebuild notice verbatim plus a retry hint.
    """


class ImpactTargetNotFoundError(Exception):
    """Raised when ``target`` matches no symbol or module the graph has ever
    indexed (as opposed to an indexed-but-unreferenced symbol, which is a
    valid ``dead (heuristic)`` result, never an error).

    The message names the target and points at the next step
    (``search_code``) — the teaching-miss standard mirroring
    :class:`~loremaster.symbols.GetSymbolError`.
    """


class ModuleRollup(BaseModel):
    """One module's aggregated consumer count at ``depth > 1``.

    Attributes:
        module: The dotted module name (as derived by
            :meth:`~loremaster.graph_surreal.SurrealCodeGraph.module_qualified_name`).
        consumer_count: The number of distinct blast-radius nodes attributed to
            this module.
    """

    model_config = ConfigDict(extra="forbid")

    module: str
    consumer_count: int


class ImpactResult(BaseModel):
    """The full answer to "who depends on this?" for one target symbol/module.

    Attributes:
        target: The symbol or module name that was queried.
        verdict: :data:`_VERDICT_LIVE` when a production reference exists,
            else :data:`_VERDICT_DEAD` — always paired with :attr:`caveat`.
        production_references: Distinct non-test references to ``target``.
        test_references: Distinct test-only references to ``target``.
        covering_tests: Qualified names of the tests exercising ``target``.
        direct_consumers: The depth-1 production consumer names (populated
            only when the EFFECTIVE query depth is 1).
        module_rollups: Per-module consumer-count rollups (populated only
            when the effective query depth is greater than 1), sorted by
            ``consumer_count`` descending then ``module`` ascending.
        elided: The count of entries squeezed out of the rendered
            consumer/rollup list by ``max_consumers`` (0 when nothing was
            squeezed) — never silent, always also named in :attr:`formatted`.
        caveat: The astroid-bounds caveat (:data:`_CAVEAT_TEXT`) — never
            empty, on every verdict.
        formatted: The compact, token-efficient rendered block a caller can
            surface directly.
    """

    model_config = ConfigDict(extra="forbid")

    target: str
    verdict: str
    production_references: int
    test_references: int
    covering_tests: list[str]
    direct_consumers: list[str]
    module_rollups: list[ModuleRollup]
    elided: int
    caveat: str
    formatted: str


class ImpactEngine:
    """Compose the code graph's read surface into one "who depends on this?"
    answer.

    A pure read layer: it holds no store/embedding dependency and derives no
    new graph state, only composing :meth:`~loremaster.graph_surreal.
    SurrealCodeGraph.references` / ``tests_for`` / ``blast_radius``.

    Args:
        graph: The code graph (:class:`~loremaster.graph_surreal.
            SurrealCodeGraph` in production, or a signature-compatible test
            double) to query. Untyped (``Any``) because the engine only
            depends on the four async methods named above — the SAME
            duck-typed dependency-injection convention already used for
            ``code_graph`` elsewhere (e.g. ``server.reconcile_store_divergence``).
        rebuild_notice: An optional async callable returning ``None`` when the
            graph is settled, or a human-readable notice string while a
            rebuild is in progress. ``None`` for the whole parameter means
            "never rebuilding" (the bare-test wiring) — no probe is ever
            called.
    """

    def __init__(
        self,
        *,
        graph: Any,
        rebuild_notice: Callable[[], Awaitable[str | None]] | None = None,
    ) -> None:
        self._graph = graph
        self._rebuild_notice = rebuild_notice

    async def impact(
        self,
        target: str,
        depth: int = 1,
        max_consumers: int = _DEFAULT_MAX_CONSUMERS,
    ) -> ImpactResult:
        """Return the full impact profile of ``target``.

        Args:
            target: The qualified (or bare) symbol/module name to profile.
            depth: The reverse-hop depth for the ripple computation; clamped
                to ``1..4`` (never raises on an out-of-range value).
            max_consumers: The cap on the rendered consumer/rollup list
                length; entries squeezed out are counted in
                :attr:`ImpactResult.elided` and named explicitly in
                :attr:`ImpactResult.formatted` (never a silent cap).

        Returns:
            The composed :class:`ImpactResult`.

        Raises:
            ImpactRebuildingError: The graph is mid-rebuild (``rebuild_notice``
                returned a non-``None`` notice) — checked BEFORE any query.
            ImpactTargetNotFoundError: ``target`` matches no node the graph has
                ever indexed.
        """
        await self._raise_if_rebuilding()
        depth = self._clamp_depth(depth)

        summary = await self._graph.references(target)
        covering_tests = await self._covering_tests(target)

        direct_consumers: list[str] = []
        module_rollups: list[ModuleRollup] = []
        elided = 0
        if depth == 1:
            direct_consumers, elided = self._cap(
                self._production_consumer_names(summary), max_consumers
            )
        else:
            rollups = await self._module_rollups(target, depth)
            module_rollups, elided = self._cap(rollups, max_consumers)

        if not await self._target_is_known(
            summary, covering_tests, direct_consumers, module_rollups, target
        ):
            raise ImpactTargetNotFoundError(
                f"no symbol or module named {target!r} appears in the code "
                f"graph (never indexed, or indexed under a different "
                f"qualified name). Next step: try search_code({target!r}) to "
                f"locate it."
            )

        verdict = _VERDICT_LIVE if summary.production_references > 0 else _VERDICT_DEAD
        formatted = self._render(
            target=target,
            verdict=verdict,
            production_references=summary.production_references,
            test_references=summary.test_references,
            covering_tests=covering_tests,
            direct_consumers=direct_consumers,
            module_rollups=module_rollups,
            elided=elided,
            max_consumers=max_consumers,
        )
        return ImpactResult(
            target=target,
            verdict=verdict,
            production_references=summary.production_references,
            test_references=summary.test_references,
            covering_tests=covering_tests,
            direct_consumers=direct_consumers,
            module_rollups=module_rollups,
            elided=elided,
            caveat=_CAVEAT_TEXT,
            formatted=formatted,
        )

    # -- gates ---------------------------------------------------------------

    async def _raise_if_rebuilding(self) -> None:
        """Raise :class:`ImpactRebuildingError` iff the probe reports a notice.

        ``None`` for the whole ``rebuild_notice`` dependency skips the probe
        entirely (the bare-test wiring never calls an absent callable).
        """
        if self._rebuild_notice is None:
            return
        notice = await self._rebuild_notice()
        if notice is not None:
            raise ImpactRebuildingError(f"graph rebuilding: {notice} — {_RETRY_HINT}")

    @staticmethod
    def _clamp_depth(depth: int) -> int:
        """Clamp ``depth`` into ``[_DEPTH_MIN, _DEPTH_MAX]`` (never raises)."""
        return max(_DEPTH_MIN, min(_DEPTH_MAX, depth))

    # -- composition -----------------------------------------------------

    async def _covering_tests(self, target: str) -> list[str]:
        """The sorted, deduplicated qualified names of tests covering ``target``."""
        nodes = await self._graph.tests_for(target)
        return sorted({node.qualified_name for node in nodes})

    @staticmethod
    def _production_consumer_names(summary: ReferenceSummary) -> list[str]:
        """The sorted, deduplicated PRODUCTION-side names from a reference summary.

        ``ReferenceSummary.referencing`` mixes production and test referrers;
        this filters to non-test file paths via the SAME
        :meth:`~loremaster.graph.CodeGraph._is_test_path` helper the graph
        itself uses to build the split, so the direct-consumer list stays
        aligned with the counted ``production_references`` split under normal
        operation (both derive from the identical per-source classification).
        """
        return sorted(
            {
                node.qualified_name
                for node in summary.referencing
                if not CodeGraph._is_test_path(node.file_path)
            }
        )

    async def _module_rollups(self, target: str, depth: int) -> list[ModuleRollup]:
        """The per-module consumer-count rollup of ``target``'s blast radius.

        Groups every node in the (generously bounded) blast radius by its
        owning module (:meth:`module_qualified_name` applied to
        ``node.file_path`` — the SAME derivation the graph used to name the
        module node in the first place), then sorts by ``consumer_count``
        descending, ``module`` ascending — the pinned determinism order.
        """
        nodes = await self._graph.blast_radius(target, depth, _BLAST_RADIUS_NODE_CAP)
        counts: dict[str, int] = {}
        for node in nodes:
            module = self._graph.module_qualified_name(node.file_path)
            counts[module] = counts.get(module, 0) + 1
        rollups = [
            ModuleRollup(module=module, consumer_count=count)
            for module, count in counts.items()
        ]
        rollups.sort(key=lambda rollup: (-rollup.consumer_count, rollup.module))
        return rollups

    async def _target_is_known(
        self,
        summary: ReferenceSummary,
        covering_tests: list[str],
        direct_consumers: list[str],
        module_rollups: list[ModuleRollup],
        target: str,
    ) -> bool:
        """Whether ``target`` is a genuinely indexed node, not a typo.

        Any positive signal already computed (a reference, a covering test, a
        consumer, a rollup) proves existence outright. When every signal is
        empty — the "indexed but zero consumers" case is indistinguishable
        from "never indexed" using ONLY those signals — a single cheap 1-hop
        :meth:`blast_radius` probe is the fallback: a node's own structural
        ``defines`` edge (module/class -> symbol) is walked by
        ``blast_radius``'s kind-unfiltered reverse traversal, so a genuinely
        defined-but-unreferenced symbol still surfaces its defining module
        here even though it has no TRUE (non-structural) reference.
        """
        if (
            summary.production_references
            or summary.test_references
            or covering_tests
            or direct_consumers
            or module_rollups
        ):
            return True
        probe = await self._graph.blast_radius(target, 1, 1)
        return bool(probe)

    @staticmethod
    def _cap(items: list[_T], max_consumers: int) -> tuple[list[_T], int]:
        """Bound ``items`` at ``max_consumers``, returning ``(kept, elided)``.

        Never a silent cap: the elided COUNT is always returned so the
        renderer can name it explicitly.
        """
        if len(items) <= max_consumers:
            return items, 0
        return items[:max_consumers], len(items) - max_consumers

    # -- rendering ---------------------------------------------------------

    @staticmethod
    def _render(
        *,
        target: str,
        verdict: str,
        production_references: int,
        test_references: int,
        covering_tests: list[str],
        direct_consumers: list[str],
        module_rollups: list[ModuleRollup],
        elided: int,
        max_consumers: int,
    ) -> str:
        """Render the compact, token-efficient impact block.

        One line per fact — never a raw dump — so a one-symbol impact query
        over a small corpus stays well under the pinned line-count ceiling
        even with every optional section present. ``max_consumers`` is the
        caller's OWN cap (rendered verbatim in the elision marker) — never the
        kept-plus-elided total, which is a different, larger number whenever
        the cap actually bit.
        """
        lines = [
            f"impact: {target}",
            f"verdict: {verdict}",
            f"{production_references} prod / {test_references} test references",
        ]
        if covering_tests:
            lines.append(f"tests: {len(covering_tests)} ({', '.join(covering_tests)})")
        else:
            lines.append("tests: 0")
        if direct_consumers:
            lines.append(f"consumers: {', '.join(direct_consumers)}")
        if module_rollups:
            rollup_text = ", ".join(
                f"{rollup.module} ({rollup.consumer_count})" for rollup in module_rollups
            )
            lines.append(f"modules: {rollup_text}")
        if elided:
            lines.append(_ELISION_TEMPLATE.format(count=elided, cap=max_consumers))
        lines.append(_CAVEAT_TEXT)
        return "\n".join(lines)
