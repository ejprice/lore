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
symbol's neighborhood?").

P7-tail POLISH WAVE — test segregation + symbol caps (binding design:
``docs/design/2026-07-04-map-test-segregation.md``). Four live-P7 frictions are
fixed here:

1. **Test-infra dominance** (§2). PageRank conflates "heavily depended on by
   tests" with "structurally central", so an unfocused map ranked test harnesses
   on top. Fix: test nodes keep feeding RANK MASS into production (a
   test-hammered module IS real signal), but are EXCLUDED from the default
   RENDERING. Tests are reached via a targeted call — ``tests=True``, ``focus=``
   on a test symbol, or ``tests_for``.
2. **Never-silent elision** (§3). The default map always renders a test-infra
   elision line naming the top test hub(s) + an omitted count + the literal
   ``tests=true`` affordance — Sonnet's budget discipline carrying Opus's
   "you should know scaffolding exists" content in one glance.
3. **Symbol dumps** (§7). An over-endowed module rendered every symbol (80+),
   starving module breadth. Fix: a per-module top-N symbol cap whose trailer
   TEACHES its own expansion verb (``+K more — focus=<module> for the full
   list``); N scales with ``budget`` (a breadth-first allocation policy, never an
   information ceiling); ``focus=`` on a module LIFTS only that module's cap.
4. **Auto-invert** (§5). ``focus=`` resolving to a test symbol promotes the test
   neighborhood to full prominence (the safety valve without which the default
   test demotion becomes a trap), with production neighbors still present and
   test nodes ``[test]``-tagged (§6).

The ranking pipeline is unchanged from P6: whole-graph extraction
(:meth:`_extract_module_graph`), import adjacency, a deterministic power-
iteration PageRank (:meth:`_page_rank`), and a personalization vector that is
uniform (unfocused) or concentrated on a ``focus`` symbol's blast-radius
neighborhood. Rendering (:meth:`_render`) is greedy under the injected
``count_tokens`` so ``count_tokens(formatted) <= budget`` holds unconditionally,
with every squeezed-out module counted in ``elided_modules`` and named in an
explicit trailer (the no-silent-caps doctrine).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict

from loremaster.graph import KIND_MODULE, CodeGraph

# --------------------------------------------------------------------------- #
# Budget bounds (contract: floor 200, default 2500, cap 6000).
# --------------------------------------------------------------------------- #

# ``budget`` clamps to this inclusive range rather than raising — the SAME
# tool-surface convention ``ImpactEngine`` uses for ``depth``: a caller-supplied
# out-of-range value is a best-effort request, not a hard error.
_BUDGET_FLOOR = 200
_BUDGET_DEFAULT = 2500  # re-denominated 2026-07-04 under 1.78 calibration, operator-approved
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
# Symbol-cap policy (§7) — breadth-first budget allocation, never a ceiling.
# --------------------------------------------------------------------------- #

# Per-module symbol cap = ``max(_MIN_SYMBOL_CAP, budget // _SYMBOL_CAP_BUDGET_
# DIVISOR)``. The cap SCALES with ``budget`` (§7c: a higher budget renders
# strictly more symbols for the top over-endowed module) — a budget-allocation
# policy that spends breadth-first (more modules) before depth (more symbols per
# module), NOT an information ceiling: ``focus=<module>`` lifts a module's cap to
# its full list, and the complete file is honestly served by ``lore_read_file``.
_SYMBOL_CAP_BUDGET_DIVISOR = 250
_MIN_SYMBOL_CAP = 3

# The number of top test hubs the always-on elision line names (§3: "top 2-3
# hubs").
_TOP_TEST_HUBS = 3

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

# §6: the ``[test]`` tag on any test node rendering in a mixed/inverted context
# (secondary insurance — placement is the primary fix, per the design doc).
_TEST_TAG = "[test]"

# §3: the always-on, never-silent test-infra elision line. It NAMES the top test
# hub(s), carries the omitted-module COUNT, and teaches the literal ``tests=true``
# expansion affordance — one glance tells the reader what scaffolding exists and
# how to include it, without spending render budget interleaving it.
_TEST_ELISION_PREFIX = "test infra omitted: "
_TESTS_INCLUDE_AFFORDANCE = "tests=true"
_TEST_ELISION_INCLUDE_SUFFIX = " to include"

# §7a: the TEACHING symbol-cap trailer — it names its own expansion verb by name
# (``+K more — focus=<module> for the full list``) so the cap is never a dead
# end; the reader learns the exact next call that lifts it.
_SYMBOL_CAP_MORE_PREFIX = "+"
_SYMBOL_CAP_TEACH_VERB = "focus="
_SYMBOL_CAP_TEACH_TAIL = "for the full list"


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
            entry for one that did not. In the DEFAULT map these are the
            production modules only; ``tests=True`` or a test-symbol ``focus=``
            additionally includes the segregated test modules.
        elided_modules: The count of RENDERED-set modules squeezed out of
            ``entries`` by ``budget`` — explicit, never silent (0 when the
            whole rendered set fit). Test modules segregated out of the default
            map are NOT counted here — they carry their own always-on elision
            line.
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
    SurrealCodeGraph.all_nodes` / ``what_imports`` / ``blast_radius``.

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

    async def map(
        self,
        budget: int = _BUDGET_DEFAULT,
        focus: str | None = None,
        tests: bool = False,
    ) -> MapResult:
        """Return the rank-ordered, budget-fitted map of the code graph.

        Args:
            budget: The token ceiling for :attr:`MapResult.formatted`;
                clamped to ``[200, 6000]`` (never raises on an out-of-range
                value).
            focus: An optional BARE (or dotted) symbol name to re-center the
                ranking on (mirrors :class:`~loremaster.impact.ImpactEngine`'s
                target convention). ``None`` ranks the whole graph uniformly. A
                focus resolving to a TEST symbol AUTO-INVERTS (§5): its test
                neighborhood is promoted to full prominence, ``[test]``-tagged.
            tests: When ``True``, append the segregated, ``[test]``-marked
                test-infra section (§4). The default (``False``) EXCLUDES test
                modules from the rendering — their edges still feed rank mass —
                and surfaces the always-on ``tests=true`` elision line instead.

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

        modules, out_edges, symbols_by_module, module_is_test, symbol_owners = (
            await self._extract_module_graph()
        )

        if focus is not None:
            personalization = await self._resolve_focus_personalization(focus, modules)
            # §7b: focusing on a symbol lifts ONLY its OWNING module(s)' symbol
            # cap (the "I care about this one" signal); referrer neighbors stay
            # capped. §5: a focus OWNED by a test module auto-inverts. SB-1: a
            # focus that IS itself a module's qualified name -- the exact
            # string the §7a trailer ("focus=<module> for the full list") and
            # the §3 elision line print back at the caller -- must lift ITS
            # OWN cap and trip its OWN auto-invert too, not just symbol
            # focuses. This is a whole-string match against `modules` (never
            # folded into `symbol_owners`'s bare-segment keys), so it cannot
            # collide with an unrelated symbol sharing a module's bare last
            # segment -- pre-existing symbol-focus behavior is unchanged.
            direct_module_match = {focus} & set(modules)
            lifted_modules = (symbol_owners.get(focus, set()) | direct_module_match) & set(modules)
            is_test_focus = any(module_is_test.get(module, False) for module in lifted_modules)
        else:
            personalization = self._uniform_personalization(modules)
            lifted_modules = set()
            is_test_focus = False

        ranks = self._page_rank(modules, out_edges, personalization)

        all_entries = [
            MapEntry(
                module=module,
                rank=ranks.get(module, 0.0),
                symbols=symbols_by_module.get(module, []),
            )
            for module in modules
        ]
        all_entries.sort(key=lambda entry: (-entry.rank, entry.module))

        # Test modules keep feeding rank mass above (they were part of the
        # PageRank vertex set), but are segregated OUT of the default rendering.
        include_tests = tests or is_test_focus
        if include_tests:
            entries_to_render = all_entries
            test_elision_line: str | None = None
        else:
            entries_to_render = [
                entry for entry in all_entries if not module_is_test.get(entry.module, False)
            ]
            omitted_test_entries = [
                entry for entry in all_entries if module_is_test.get(entry.module, False)
            ]
            test_elision_line = (
                self._test_elision_line(omitted_test_entries)
                if omitted_test_entries
                else None
            )

        symbol_cap = self._symbol_cap(budget)
        kept_entries, elided, formatted = self._render(
            entries_to_render,
            budget,
            module_is_test=module_is_test,
            symbol_cap=symbol_cap,
            lifted_modules=lifted_modules,
            test_elision_line=test_elision_line,
        )
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

    @staticmethod
    def _symbol_cap(budget: int) -> int:
        """The per-module symbol cap for ``budget`` (§7c — scales with budget).

        A breadth-first allocation policy: at a low budget fewer symbols per
        module leaves room for more MODULES; a higher budget affords a strictly
        larger cap. Never below :data:`_MIN_SYMBOL_CAP` so even the floor budget
        renders a meaningful glimpse of a module's surface.
        """
        return max(_MIN_SYMBOL_CAP, budget // _SYMBOL_CAP_BUDGET_DIVISOR)

    # -- extraction -------------------------------------------------------

    async def _extract_module_graph(
        self,
    ) -> tuple[
        list[str],
        dict[str, list[str]],
        dict[str, list[str]],
        dict[str, bool],
        dict[str, set[str]],
    ]:
        """Derive the module vertex set, import adjacency, symbols, and metadata.

        Returns:
            A tuple ``(modules, out_edges, symbols_by_module, module_is_test,
            symbol_owners)``:

            * ``modules`` — every distinct owning module, SORTED ascending
              (the PageRank vertex set — production AND test modules; test edges
              MUST feed production rank mass even though test nodes are later
              segregated out of the default rendering).
            * ``out_edges`` — ``importer_module -> [imported_module, ...]``,
              each list SORTED ascending, one
              :meth:`~loremaster.graph_surreal.SurrealCodeGraph.what_imports`
              call per module (a self-import is dropped).
            * ``symbols_by_module`` — ``module -> [bare_symbol_name, ...]``,
              each list SORTED ascending.
            * ``module_is_test`` — ``module -> bool`` via the SAME classifier
              the graph itself carries for ``references()``
              (:meth:`~loremaster.graph.CodeGraph._is_test_path` over the owning
              file), never a second heuristic (§clause 5).
            * ``symbol_owners`` — ``symbol_name -> {owning_module, ...}`` keyed
              by BOTH the bare last segment AND the full qualified name, so a
              ``focus=`` in either form resolves to the DEFINING module(s) for
              the cap-lift + auto-invert decisions.
        """
        nodes = await self._graph.all_nodes()

        modules: set[str] = set()
        symbols_by_module: dict[str, set[str]] = defaultdict(set)
        module_is_test: dict[str, bool] = {}
        symbol_owners: dict[str, set[str]] = defaultdict(set)
        for node in nodes:
            module = self._graph.module_qualified_name(node.file_path)
            modules.add(module)
            module_is_test[module] = module_is_test.get(module, False) or CodeGraph._is_test_path(
                node.file_path
            )
            if node.kind != KIND_MODULE:
                bare = CodeGraph._bare_name(node.qualified_name)
                symbols_by_module[module].add(bare)
                symbol_owners[bare].add(module)
                symbol_owners[node.qualified_name].add(module)

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
            module_is_test,
            {name: set(owners) for name, owners in symbol_owners.items()},
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
            focus: The bare (or dotted) symbol name to resolve.
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

    def _render_symbols(
        self, entry: MapEntry, symbol_cap: int, lifted: bool
    ) -> tuple[str, str]:
        """Render one module's symbols, capped unless its cap is LIFTED (§7).

        Returns ``(symbol_text, trailer)``. When the module's symbol count
        exceeds ``symbol_cap`` and its cap is not lifted, only the top
        ``symbol_cap`` names render and the TEACHING trailer names the exact
        expansion verb (``focus=<module> for the full list``, §7a) — the cap is
        never a dead end. A lifted (focused) module renders its FULL list.
        """
        symbols = entry.symbols
        if lifted or len(symbols) <= symbol_cap:
            shown = symbols
            trailer = ""
        else:
            shown = symbols[:symbol_cap]
            hidden = len(symbols) - symbol_cap
            trailer = (
                f" ({_SYMBOL_CAP_MORE_PREFIX}{hidden} more — "
                f"{_SYMBOL_CAP_TEACH_VERB}{entry.module} {_SYMBOL_CAP_TEACH_TAIL})"
            )
        symbol_text = ", ".join(shown) if shown else _NO_SYMBOLS_PLACEHOLDER
        return symbol_text, trailer

    def _render_module_line(
        self, entry: MapEntry, *, is_test: bool, symbol_cap: int, lifted: bool
    ) -> str:
        """One compact, SELF-DESCRIBING rollup line: module, rank, symbols.

        The rank is labelled (``rank <float>``) and the names labelled
        (``symbols: ...``) so a caller reads what each value IS without a
        legend. A test module rendering in a mixed/inverted context carries the
        ``[test]`` tag (§6) so scaffolding can never be mistaken for production,
        even when it renders first.
        """
        tag = f" {_TEST_TAG}" if is_test else ""
        symbol_text, trailer = self._render_symbols(entry, symbol_cap, lifted)
        return f"{entry.module}{tag}  (rank {entry.rank:.4f})  symbols: {symbol_text}{trailer}"

    @staticmethod
    def _test_elision_line(omitted_test_entries: Sequence[MapEntry]) -> str:
        """The always-on, never-silent test-infra elision line (§3).

        Names the top :data:`_TOP_TEST_HUBS` test modules by rank (``omitted_
        test_entries`` arrive already rank-sorted), carries the total omitted
        count, and teaches the literal :data:`_TESTS_INCLUDE_AFFORDANCE`
        expansion verb — the one-glance content that resolves Sonnet's budget
        discipline against Opus's "you should know scaffolding exists".
        """
        hubs = [entry.module for entry in omitted_test_entries[:_TOP_TEST_HUBS]]
        hub_list = ", ".join(hubs)
        extra = len(omitted_test_entries) - len(hubs)
        more = f" (+{extra} more)" if extra > 0 else ""
        count = len(omitted_test_entries)
        return (
            f"{_TEST_ELISION_PREFIX}{hub_list}{more} ({count} test modules) — "
            f"{_TESTS_INCLUDE_AFFORDANCE}{_TEST_ELISION_INCLUDE_SUFFIX}"
        )

    @staticmethod
    def _elision_trailer(elided: int, budget: int) -> str:
        """The explicit module-elision trailer line (carries
        :data:`_ELISION_FRAGMENT`)."""
        return f"{elided} {_ELISION_FRAGMENT}={budget} tokens)"

    def _render(
        self,
        entries: Sequence[MapEntry],
        budget: int,
        *,
        module_is_test: Mapping[str, bool],
        symbol_cap: int,
        lifted_modules: set[str],
        test_elision_line: str | None,
    ) -> tuple[list[MapEntry], int, str]:
        """Greedily render ``entries`` (already rank-ordered) within ``budget``.

        Appends one rollup line per module, measuring the growing block with
        the injected ``count_tokens`` after each addition; the walk stops the
        moment the NEXT line would exceed ``budget`` (never a partial line). The
        always-on test-infra elision line (``test_elision_line``, §3) is treated
        as a MANDATORY tail — its token cost is reserved throughout the greedy
        walk so the final block still fits. When production modules are squeezed
        out, the explicit module-elision trailer is appended too, popping
        already-kept lines (lowest-ranked first) until the trailer plus the
        mandatory tail all fit. The clamped floor (:data:`_BUDGET_FLOOR`)
        guarantees the mandatory tail alone always fits.

        Args:
            entries: The full rank-ordered entry list to render.
            budget: The already-clamped token ceiling.
            module_is_test: The prod/test classification per module (drives the
                ``[test]`` tag).
            symbol_cap: The per-module symbol cap for this budget.
            lifted_modules: Modules whose symbol cap is lifted (the focused
                module's full list).
            test_elision_line: The always-on test-infra elision line, or
                ``None`` when the corpus has no omitted test modules.

        Returns:
            ``(kept_entries, elided_count, formatted_text)``.
        """
        mandatory_tail = [test_elision_line] if test_elision_line else []
        kept_lines: list[str] = []
        kept_entries: list[MapEntry] = []
        for entry in entries:
            line = self._render_module_line(
                entry,
                is_test=module_is_test.get(entry.module, False),
                symbol_cap=symbol_cap,
                lifted=entry.module in lifted_modules,
            )
            trial_lines = [*kept_lines, line, *mandatory_tail]
            if self._count_tokens("\n".join(trial_lines)) > budget:
                break
            kept_lines.append(line)
            kept_entries.append(entry)

        elided = len(entries) - len(kept_entries)
        tail: list[str] = []
        if elided:
            trailer = self._elision_trailer(elided, budget)
            # Pop already-kept lines (lowest-ranked first) until the trailer plus
            # the mandatory tail fit too -- their own token cost must never be
            # the thing that breaks the budget invariant.
            while kept_entries and self._count_tokens(
                "\n".join([*kept_lines, trailer, *mandatory_tail])
            ) > budget:
                kept_lines.pop()
                kept_entries.pop()
                elided += 1
                trailer = self._elision_trailer(elided, budget)
            tail.append(trailer)
        tail.extend(mandatory_tail)

        return kept_entries, elided, "\n".join([*kept_lines, *tail])
