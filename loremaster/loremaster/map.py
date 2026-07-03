"""``MapEngine`` — the P6-tail ``lore_map`` verb: "orient me in this codebase."

``lore_map`` (plan §5) answers, in one call, the question that today costs a
directory dump plus a lot of guessing: which modules MATTER in this project (or
in the neighborhood of one symbol), ranked, and rendered inside a token budget
instead of as a raw node dump.

:class:`MapEngine` is a PURE READ layer over the code graph
(:class:`~loremaster.graph_surreal.SurrealCodeGraph` in production, or its
in-memory test double) — mirroring :class:`~loremaster.impact.ImpactEngine`'s
shape (same rebuild gate / clamp / teaching-miss idioms) but answering a
DIFFERENT question shape: impact is target-keyed ("who depends on THIS
symbol?"); map is corpus-wide ("what matters HERE, optionally centered on a
symbol's neighborhood?"). That difference is exactly why map needs a
WHOLE-GRAPH read the target-keyed surface does not otherwise provide — see the
``KNOWN GRAPH-SURFACE GAP`` note below.

The algorithm, end to end:

1. **Extraction** — pull every graph node (:meth:`~loremaster.graph_surreal.
   SurrealCodeGraph.all_nodes`) and derive two things from it: the MODULE
   vertex set (every distinct owning module, via
   :meth:`~loremaster.graph_surreal.SurrealCodeGraph.module_qualified_name`
   applied to each node's ``file_path`` — the SAME derivation
   :class:`~loremaster.impact.ImpactEngine._module_rollups` already uses, so a
   module is never named two different ways across the two engines) and each
   module's rendered SYMBOL names (every non-module node's bare last segment,
   grouped by owning module).
2. **Adjacency** — for each discovered module, :meth:`~loremaster.graph_surreal.
   SurrealCodeGraph.what_imports` gives its DIRECT importer modules; each
   importer contributes one directed edge ``importer -> imported`` (an import
   is modelled as a vote FOR the thing depended on — the same "many importers
   make a hub important" intuition a citation graph runs on).
3. **PageRank** — a plain power iteration (:data:`_DAMPING` / fixed
   :data:`_PAGE_RANK_ITERATIONS`, deterministic — no epsilon-based early stop,
   no numpy/networkx dependency) over that directed adjacency. Every iteration
   is built from SORTED module/edge lists, never a bare dict/set walk, so the
   floating-point summation order — and therefore the result — is
   byte-reproducible across calls (the determinism contract).
4. **Personalization** — an unfocused query teleports uniformly (every module
   equally "important a priori"); a focused query teleports onto the modules a
   cheap depth-1 :meth:`~loremaster.graph_surreal.SurrealCodeGraph.blast_radius`
   probe surfaces around the focus symbol — the SAME existence-probe idiom
   :meth:`~loremaster.impact.ImpactEngine._target_is_known` already uses (a
   symbol's own structural ``defines`` edge is walked by blast_radius's
   kind-unfiltered reverse traversal, so even a symbol with zero TRUE
   references still resolves to its defining module). An empty probe means the
   focus was never indexed: :class:`MapFocusNotFoundError`.
5. **Rendering** — module rollup lines are appended in rank order, measuring
   the growing block with the INJECTED ``count_tokens`` after each line; the
   walk stops the moment the next line (or, at the very end, the elision
   trailer itself) would exceed ``budget``, so ``count_tokens(formatted) <=
   budget`` holds unconditionally, never just "usually." Every module dropped
   this way is counted in ``elided_modules`` and named in the trailer — the
   no-silent-caps doctrine :class:`~loremaster.impact.ImpactEngine` already
   applies to its own consumer lists.

KNOWN GRAPH-SURFACE GAP (flagged to the contract owner, not invented
unilaterally): as of this writing neither :class:`~loremaster.graph_surreal.
SurrealCodeGraph` nor its faithful test double exposes a whole-graph node
enumeration — every existing query (``what_imports`` / ``blast_radius`` /
``tests_for`` / ``references``) is target-keyed, and ``dead_code`` is
liveness-filtered and tier-scoped. :meth:`_extract_module_graph` below calls
``self._graph.all_nodes()`` — a minimal proposed addition (every ``code_node``
row across every tier, mirroring ``dead_code``'s existing tier-scoped scan
shape but unfiltered) — which does not exist yet on either the real graph or
:class:`~loremaster.graph_surreal` test doubles. Until it lands, every
whole-graph query raises ``AttributeError`` there, loudly, rather than
silently returning an empty/wrong map.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict

from loremaster.graph import KIND_MODULE, CodeGraph

# --------------------------------------------------------------------------- #
# Budget bounds (contract: floor 200, default 1500, cap 6000).
# --------------------------------------------------------------------------- #

# ``budget`` clamps to this inclusive range rather than raising — the SAME
# tool-surface convention ``ImpactEngine`` uses for ``depth``: a caller-supplied
# out-of-range value is a best-effort request, not a hard error.
_BUDGET_FLOOR = 200
_BUDGET_DEFAULT = 1500
_BUDGET_CAP = 6000

# --------------------------------------------------------------------------- #
# PageRank parameters — plain power iteration, no third-party graph library.
# --------------------------------------------------------------------------- #

# The classic PageRank damping factor (the probability mass that follows an
# edge each iteration; the remainder teleports per the personalization
# vector). 0.85 is the original Brin/Page value and the near-universal default
# in every PageRank implementation since — not tuned for this corpus.
_DAMPING = 0.85

# A FIXED iteration count (rather than an epsilon-convergence loop) — simpler
# to reason about and exactly as deterministic: the same graph run twice
# performs the identical sequence of floating-point operations. 50 iterations
# is generously past the point a damping of 0.85 has converged to
# floating-point noise on any repo-scale graph (a random surfer's influence
# decays by 0.85 per hop, so by hop 50 a single edge's contribution is
# ~0.85**50 ≈ 3e-4 of its original weight).
_PAGE_RANK_ITERATIONS = 50

# The depth-1 existence/neighborhood probe used to resolve a ``focus`` symbol
# to its owning + referencing modules — the SAME cheap idiom
# ``ImpactEngine._target_is_known`` already uses (a structural ``defines``
# edge is walked by blast_radius's kind-unfiltered reverse traversal, so a
# symbol resolves to its defining module even with zero true references).
_FOCUS_PROBE_DEPTH = 1
_FOCUS_PROBE_MAX_RESULTS = 500

# --------------------------------------------------------------------------- #
# Rendering fragments.
# --------------------------------------------------------------------------- #

# The explicit elision-trailer fragment rendered when ``budget`` squeezes
# modules out of the rendered block (no-silent-caps doctrine, mirrors
# ``ImpactEngine``'s ``"more (elided"`` marker).
_ELISION_FRAGMENT = "modules elided (budget"

# The retry hint every rebuilding-error message carries.
_RETRY_HINT = "retry the map query once the rebuild settles"

# Placeholder rendered for a module with no derived symbols (a module with
# only import/expression-level statements the chunker does not chunk as a
# class/function/method — never left as a blank, confusing line).
_NO_SYMBOLS_PLACEHOLDER = "(no symbols)"


class MapRebuildingError(Exception):
    """Raised when a map is requested while the code graph is rebuilding.

    Verdict-bearing (rank-bearing) output is never served mid-rebuild — a
    half-built graph's honestly-sparse-looking module set could otherwise be
    misread as the true ranking. The message carries the caller-supplied
    rebuild notice verbatim plus a retry hint.
    """


class MapFocusNotFoundError(Exception):
    """Raised when ``focus`` matches no symbol or module the graph has ever
    indexed.

    The message names the focus and points at the next step
    (``search_code``) — the teaching-miss standard mirroring
    :class:`~loremaster.impact.ImpactTargetNotFoundError` /
    :class:`~loremaster.symbols.GetSymbolError`.
    """


class MapEntry(BaseModel):
    """One module's rank + rendered symbol names.

    Attributes:
        module: The dotted module name (as derived by
            :meth:`~loremaster.graph_surreal.SurrealCodeGraph.
            module_qualified_name`).
        rank: The module's PageRank score (an implementation artifact — never
            compared for an exact value, only for relative ORDER).
        symbols: The module's rendered symbol names (bare last segment of
            each non-module node owned by the module), sorted ascending.
    """

    model_config = ConfigDict(extra="forbid")

    module: str
    rank: float
    symbols: list[str]


class MapResult(BaseModel):
    """The full answer to "orient me in this codebase" for one map query.

    Attributes:
        entries: The rank-ordered, budget-fitted :class:`MapEntry` list
            (rank DESC, ties broken by ``module`` ASC) — ONLY the modules
            that fit inside ``budget``, never a truncated-but-still-present
            entry for one that did not.
        elided_modules: The count of modules squeezed out of ``entries`` by
            ``budget`` — explicit, never silent (0 when the whole corpus
            fit).
        formatted: The compact, token-bounded rendered block a caller can
            surface directly; ``count_tokens(formatted) <= budget`` always
            holds.
    """

    model_config = ConfigDict(extra="forbid")

    entries: list[MapEntry]
    elided_modules: int
    formatted: str


class MapEngine:
    """Compose the code graph's read surface into one "orient me here" map.

    A pure read layer: it holds no store/embedding dependency and derives no
    new graph state, only composing :meth:`~loremaster.graph_surreal.
    SurrealCodeGraph.all_nodes` / ``what_imports`` / ``blast_radius`` (see the
    module docstring's ``KNOWN GRAPH-SURFACE GAP`` note for ``all_nodes``).

    Args:
        graph: The code graph (:class:`~loremaster.graph_surreal.
            SurrealCodeGraph` in production, or a signature-compatible test
            double) to query. Untyped (``Any``) — the SAME duck-typed
            dependency-injection convention :class:`~loremaster.impact.
            ImpactEngine` already uses for its own ``graph`` dependency.
        count_tokens: A single-string token estimator the caller MUST supply
            (mirrors the real chunker's own token-budget convention) — used
            to measure the growing rendered block against ``budget``.
        rebuild_notice: An optional async callable returning ``None`` when
            the graph is settled, or a human-readable notice string while a
            rebuild is in progress. ``None`` for the whole parameter means
            "never rebuilding" (the bare-test wiring) — no probe is ever
            called.
    """

    def __init__(
        self,
        *,
        graph: Any,
        count_tokens: Callable[[str], int],
        rebuild_notice: Callable[[], Awaitable[str | None]] | None = None,
    ) -> None:
        self._graph = graph
        self._count_tokens = count_tokens
        self._rebuild_notice = rebuild_notice

    async def map(self, budget: int = _BUDGET_DEFAULT, focus: str | None = None) -> MapResult:
        """Return the rank-ordered, budget-fitted map of the code graph.

        Args:
            budget: The token ceiling for :attr:`MapResult.formatted`;
                clamped to ``[200, 6000]`` (never raises on an out-of-range
                value).
            focus: An optional BARE symbol name to re-center the ranking on
                (mirrors :class:`~loremaster.impact.ImpactEngine`'s target
                convention). ``None`` ranks the whole graph uniformly.

        Returns:
            The composed :class:`MapResult`.

        Raises:
            MapRebuildingError: The graph is mid-rebuild (``rebuild_notice``
                returned a non-``None`` notice) — checked BEFORE any query.
            MapFocusNotFoundError: ``focus`` matches no node the graph has
                ever indexed.
        """
        await self._raise_if_rebuilding()
        budget = self._clamp_budget(budget)

        modules, out_edges, symbols_by_module = await self._extract_module_graph()

        personalization = (
            await self._resolve_focus_personalization(focus, modules)
            if focus is not None
            else self._uniform_personalization(modules)
        )
        ranks = self._page_rank(modules, out_edges, personalization)

        entries = [
            MapEntry(
                module=module,
                rank=ranks.get(module, 0.0),
                symbols=symbols_by_module.get(module, []),
            )
            for module in modules
        ]
        entries.sort(key=lambda entry: (-entry.rank, entry.module))

        kept_entries, elided, formatted = self._render(entries, budget)
        return MapResult(entries=kept_entries, elided_modules=elided, formatted=formatted)

    # -- gates ----------------------------------------------------------

    async def _raise_if_rebuilding(self) -> None:
        """Raise :class:`MapRebuildingError` iff the probe reports a notice.

        ``None`` for the whole ``rebuild_notice`` dependency skips the probe
        entirely (the bare-test wiring never calls an absent callable) —
        identical idiom to :meth:`~loremaster.impact.ImpactEngine.
        _raise_if_rebuilding`.
        """
        if self._rebuild_notice is None:
            return
        notice = await self._rebuild_notice()
        if notice is not None:
            raise MapRebuildingError(f"graph rebuilding: {notice} — {_RETRY_HINT}")

    @staticmethod
    def _clamp_budget(budget: int) -> int:
        """Clamp ``budget`` into ``[_BUDGET_FLOOR, _BUDGET_CAP]`` (never raises)."""
        return max(_BUDGET_FLOOR, min(_BUDGET_CAP, budget))

    # -- extraction -------------------------------------------------------

    async def _extract_module_graph(
        self,
    ) -> tuple[list[str], dict[str, list[str]], dict[str, list[str]]]:
        """Derive the module vertex set, its import adjacency, and its symbols.

        Returns:
            A tuple ``(modules, out_edges, symbols_by_module)``:

            * ``modules`` — every distinct owning module, SORTED ascending
              (the PageRank vertex set).
            * ``out_edges`` — ``importer_module -> [imported_module, ...]``,
              each list SORTED ascending, built from one
              :meth:`~loremaster.graph_surreal.SurrealCodeGraph.what_imports`
              call per module (a self-import, were one ever derivable, is
              dropped — it contributes nothing to relative ranking).
            * ``symbols_by_module`` — ``module -> [bare_symbol_name, ...]``,
              each list SORTED ascending, gathered from every non-module node
              owned by that module.
        """
        nodes = await self._graph.all_nodes()

        modules: set[str] = set()
        symbols_by_module: dict[str, set[str]] = {}
        for node in nodes:
            module = self._graph.module_qualified_name(node.file_path)
            modules.add(module)
            if node.kind != KIND_MODULE:
                symbols_by_module.setdefault(module, set()).add(
                    CodeGraph._bare_name(node.qualified_name)
                )

        sorted_modules = sorted(modules)
        out_edges: dict[str, set[str]] = {module: set() for module in sorted_modules}
        for module in sorted_modules:
            importers = await self._graph.what_imports(module)
            for importer_node in importers:
                importer_module = importer_node.qualified_name
                if importer_module in out_edges and importer_module != module:
                    out_edges[importer_module].add(module)

        return (
            sorted_modules,
            {module: sorted(targets) for module, targets in out_edges.items()},
            {module: sorted(names) for module, names in symbols_by_module.items()},
        )

    # -- personalization ----------------------------------------------------

    @staticmethod
    def _uniform_personalization(modules: Sequence[str]) -> dict[str, float]:
        """An unfocused query: every module is equally important a priori."""
        if not modules:
            return {}
        weight = 1.0 / len(modules)
        return {module: weight for module in modules}

    async def _resolve_focus_personalization(
        self, focus: str, known_modules: Sequence[str]
    ) -> dict[str, float]:
        """Resolve ``focus`` to a teleport vector over its own neighborhood.

        A depth-1, kind-unfiltered :meth:`~loremaster.graph_surreal.
        SurrealCodeGraph.blast_radius` probe surfaces BOTH the focus symbol's
        own defining module (via its structural ``defines`` edge) and any
        module with a true (import/call/inherit) reference into it — exactly
        the "focus's neighborhood" the contract asks the personalization
        vector to concentrate on. An empty probe means ``focus`` was never
        indexed under any name the graph recognises.

        Args:
            focus: The bare symbol name to resolve.
            known_modules: The current whole-graph module vertex set — the
                probe's hits are intersected against this so a stale/foreign
                module can never silently enter the personalization vector.

        Returns:
            An even-weight distribution over the resolved focus module(s)
            (summing to 1.0), zero elsewhere.

        Raises:
            MapFocusNotFoundError: ``focus`` resolves to no known module.
        """
        probe_nodes = await self._graph.blast_radius(
            focus, _FOCUS_PROBE_DEPTH, _FOCUS_PROBE_MAX_RESULTS
        )
        focus_modules = sorted(
            {self._graph.module_qualified_name(node.file_path) for node in probe_nodes}
            & set(known_modules)
        )
        if not focus_modules:
            raise MapFocusNotFoundError(
                f"no symbol or module named {focus!r} appears in the code "
                f"graph (never indexed, or indexed under a different "
                f"qualified name). Next step: try search_code({focus!r}) to "
                f"locate it."
            )
        weight = 1.0 / len(focus_modules)
        return {module: weight for module in focus_modules}

    # -- PageRank -------------------------------------------------------

    @staticmethod
    def _page_rank(
        modules: Sequence[str],
        out_edges: Mapping[str, Sequence[str]],
        personalization: Mapping[str, float],
    ) -> dict[str, float]:
        """Plain power-iteration (personalized) PageRank over a directed graph.

        A dangling module (zero out-edges — nothing it "votes for") would
        otherwise leak its accumulated rank out of the system every
        iteration; instead its mass is redistributed each round according to
        ``personalization`` (uniform in the unfocused case, concentrated on
        the focus neighborhood otherwise) — the standard personalized-PageRank
        treatment, and the SAME vector already driving the restart term, so
        one vector serves both roles.

        ``modules`` and every ``out_edges`` value are iterated in the SORTED
        order the caller already guarantees, so the floating-point summation
        order — and therefore the result — is identical across repeated calls
        on an unchanged graph (the determinism contract).

        Args:
            modules: The vertex set (assumed sorted by the caller).
            out_edges: ``module -> [imported_module, ...]`` (assumed sorted).
            personalization: The teleport/restart weight per module, summing
                to 1.0 over ``modules``.

        Returns:
            ``module -> rank`` for every module in ``modules``.
        """
        if not modules:
            return {}
        rank: dict[str, float] = {module: personalization.get(module, 0.0) for module in modules}
        out_degree = {module: len(out_edges.get(module, ())) for module in modules}

        for _iteration in range(_PAGE_RANK_ITERATIONS):
            new_rank = {
                module: (1.0 - _DAMPING) * personalization.get(module, 0.0) for module in modules
            }
            dangling_mass = sum(rank[module] for module in modules if out_degree[module] == 0)
            for module in modules:
                degree = out_degree[module]
                if degree == 0:
                    continue
                share = _DAMPING * rank[module] / degree
                for target in out_edges[module]:
                    new_rank[target] += share
            if dangling_mass:
                for module in modules:
                    new_rank[module] += _DAMPING * dangling_mass * personalization.get(module, 0.0)
            rank = new_rank

        return rank

    # -- rendering --------------------------------------------------------

    @staticmethod
    def _render_module_line(entry: MapEntry) -> str:
        """One compact, SELF-DESCRIBING rollup line: the module, its
        PageRank score, and its symbol names.

        The rank is labelled (``rank <float>``) and the names are labelled
        (``symbols: ...``) rather than packed into bare brackets, so a caller
        surfacing the block directly reads what each value IS without a
        legend — honest, self-documenting information density, never padding.
        """
        symbol_text = ", ".join(entry.symbols) if entry.symbols else _NO_SYMBOLS_PLACEHOLDER
        return f"{entry.module}  (rank {entry.rank:.4f})  symbols: {symbol_text}"

    @staticmethod
    def _elision_trailer(elided: int, budget: int) -> str:
        """The explicit elision-trailer line (carries :data:`_ELISION_FRAGMENT`)."""
        return f"{elided} {_ELISION_FRAGMENT}={budget} tokens)"

    def _render(
        self, entries: Sequence[MapEntry], budget: int
    ) -> tuple[list[MapEntry], int, str]:
        """Greedily render ``entries`` (already rank-ordered) within ``budget``.

        Appends one rollup line per module, measuring the growing block with
        the injected ``count_tokens`` after each addition; the walk stops the
        moment the NEXT line would exceed ``budget`` (never a partial line).
        When anything was squeezed out, the elision trailer is appended too —
        popping already-kept lines first if needed so the trailer itself
        never pushes the block over budget, guaranteeing
        ``count_tokens(formatted) <= budget`` unconditionally.

        Args:
            entries: The full rank-ordered entry list.
            budget: The already-clamped token ceiling.

        Returns:
            ``(kept_entries, elided_count, formatted_text)``.
        """
        kept_lines: list[str] = []
        kept_entries: list[MapEntry] = []
        for entry in entries:
            trial_lines = [*kept_lines, self._render_module_line(entry)]
            if self._count_tokens("\n".join(trial_lines)) > budget:
                break
            kept_lines = trial_lines
            kept_entries.append(entry)

        elided = len(entries) - len(kept_entries)
        if elided:
            trailer = self._elision_trailer(elided, budget)
            trial_text = "\n".join([*kept_lines, trailer])
            # Pop already-kept lines (rarest, lowest-ranked first) until the
            # trailer itself fits too -- the trailer's own token cost must
            # never be the thing that breaks the budget invariant.
            while self._count_tokens(trial_text) > budget and kept_entries:
                kept_lines.pop()
                kept_entries.pop()
                elided += 1
                trailer = self._elision_trailer(elided, budget)
                trial_text = "\n".join([*kept_lines, trailer])
            kept_lines.append(trailer)

        return kept_entries, elided, "\n".join(kept_lines)
