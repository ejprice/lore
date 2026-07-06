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
SurrealQL of its own; it composes the graph's existing query surface:

* :meth:`~loremaster.graph_surreal.SurrealCodeGraph.references` — the
  production/test reference-count split (the liveness signal), plus (findings
  #43/#65, this wave) whether the result rode the RISKY bare-fallback channel
  and, when it did, the real colliding qualified name(s) — never presented as
  one unambiguous profile with no signal that it might be a union.
* :meth:`~loremaster.graph_surreal.SurrealCodeGraph.tests_for` — the covering
  tests (the "what exercises this" signal).
* :meth:`~loremaster.graph_surreal.SurrealCodeGraph.blast_radius` — the
  transitive reverse-dependency closure, rolled up by module at ``depth > 1``
  (the ripple signal) and reused as a lightweight EXISTENCE probe (see
  :meth:`ImpactEngine._target_is_known`) for the depth-1 case.

Findings #63/#65 (this wave): an OPTIONAL second collaborator,
:class:`~loremaster.symbols.SymbolResolver` (duck-typed, ``None`` by
default), resolves a DOTTED target through the chunk-store identity
convention (:meth:`ImpactEngine._widen_dotted_target`) BEFORE any graph query
runs — closing the gap where a module-less "Class.method" form (exactly what
``lore_get_symbol`` resolves) either matched nothing in the graph (finding
#63) or, worse, silently rode the graph's bare-fallback OR-term and returned
an unrelated same-named symbol's profile with full apparent confidence
(finding #65). This collaborator issues its OWN store reads (via the
resolver, never SurrealQL authored here) but derives no new state either.

Verdict-bearing output is NEVER served while the graph is mid-rebuild — a
truthy ``rebuild_notice()`` result makes :meth:`ImpactEngine.impact` raise
:class:`ImpactRebuildingError` before any query runs, so a caller never reads a
half-built graph's honestly-empty-looking-but-actually-incomplete answer as a
real verdict.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any, NamedTuple, TypeVar

from pydantic import BaseModel, ConfigDict

from loremaster.graph import CodeGraph, GraphNode, ReferenceSummary

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

# The suffix a depth>1 rollup carries when its module is reached ONLY transitively
# (never a DIRECT consumer of the target). Labelling it keeps a reader from
# mistaking the transitive ripple for direct-consumer usage (design doc S9 /
# FRICTION.md 2026-07-04: a fixture migration mis-scoped because a depth-2 module
# count read as direct usage). CONDITIONAL by construction -- only a module absent
# from the depth-1 reverse set earns it, so the marker genuinely distinguishes.
_TRANSITIVE_ROLLUP_SUFFIX = ", transitive"

# P8d Wave 2 (the impact fold) honest-render additions -- see
# REPORT-builder-flip-w2.md for the full investigation these consume.

# Finding #19 (2nd symptom, CONFIRMED reproducing live): a depth>1 module
# rollup is genuinely computed by walking the shared graph's module-prefix
# "imports" arm (graph_surreal.py's ``_reverse_neighbours`` -- a deliberate,
# tested, Kuzu-parity feature ``blast_radius``/``lore_map`` both rely on, NOT
# a graph bug) -- once a MODULE-kind node enters the BFS frontier (a
# module-level import of the target IS a legitimate depth-1 reference), EVERY
# importer of ANYTHING defined in that module counts, whether or not it uses
# the specific target symbol. Fixing the shared BFS would touch
# graph_surreal.py's traversal core under the map-test-segregation BINDING
# design law for a risk/blast-radius beyond this wave's fold scope -- the fix
# here is HONEST RENDER: always caveat a depth>1 rollup so a large count is
# never mistaken for confirmed usage of the exact symbol queried.
_MODULE_ROLLUP_RIPPLE_CAVEAT = (
    "module rollups (depth>1) follow the transitive MODULE-level import "
    "graph, not confirmed calls to this exact symbol -- a module that "
    "imports something else from the same file can inflate a count; "
    "depth=1 lists only CONFIRMED direct consumers."
)

# Findings #1/#2: ``tests_for``'s name/reference heuristic can miss a
# genuinely covering test (indirectly-exercised helpers, config.py-shaped
# modules). Improving that DETECTION heuristic is OUT of scope for this wave;
# what a genuine zero-covering-tests result must never do is render as a
# bare, confident-looking "tests: 0" -- it must say it is a heuristic miss,
# never a verified absence.
_NO_COVERING_TESTS_TEXT = "none detected (heuristic -- indirect coverage is not traced)"

# Finding #39 (SUPERSEDED by S1, the 2026-07-06 client-needs consult --
# docs/design/2026-07-06-client-needs-consult.md): the rendered covering-tests
# list caps at a sane top-N (the SAME sorted-name order ``_covering_tests``
# already returns, so the kept entries are deterministic) with an explicit,
# non-silent elision trailer (no-silent-caps doctrine). S1 REVERSES #39's
# "structured field stays full" ruling -- its rationale assumed a
# programmatic consumer, but over MCP the model IS the consumer, and both
# surfaces land in the same context: an uncapped structured field taxes the
# SAME context an uncapped render would. The STRUCTURED ``covering_tests``
# field is now capped with the SAME discipline (see ``ImpactEngine.impact``),
# with the elided count carried honestly in ``ImpactResult.covering_tests_
# elided`` -- never overloading the existing consumer/rollup-scoped
# ``elided`` field, which stays scoped to ``direct_consumers``/
# ``module_rollups`` per its own docstring.
_MAX_RENDERED_COVERING_TESTS = 15
_COVERING_TESTS_ELISION_TEMPLATE = "+{count} more (elided by max_covering_tests={cap})"

# T6 (P8d' #54 tweak): when covering tests would otherwise be capped (more
# than _MAX_RENDERED_COVERING_TESTS) AND every one of them lives in the SAME
# file, naming 15 near-identical-looking qualified names plus an elision
# trailer is pure token noise -- one file backing a big suite (the common
# "this helper's whole test module covers it" shape) rolls up to a count +
# that file's module label instead. The STRUCTURED covering_tests field is
# capped the SAME way as every other case (S1) -- this render branch changes
# only the TEXT shape, never whether the wire field is capped; a multi-file
# spread (the general case finding #39/S1 already covers) keeps the existing
# capped enumeration untouched.
_COVERING_TESTS_FILE_ROLLUP_TEMPLATE = "tests: {count} across 1 file ({module})"

# Findings #30/#43/#65 (channel honesty, SUPERSEDES the P8d Wave 2 syntactic
# gate): the graph's ``references()`` now reports whether THIS result
# actually rode the risky bare-fallback/answers_to-bridge channel
# (``ReferenceSummary.bare_fallback_used``) and, when it did, the REAL
# colliding qualified name(s) (``.bare_fallback_candidates`` -- closing #43's
# "name the actual candidates" ask). The caveat below is rendered keyed on
# THAT flag -- never on the syntactic presence of a "." in the query string
# (the old gate): finding #65 proved a DOTTED, even fully-qualified, target
# can silently ride the exact same risky channel a bare query does, with the
# old gate never firing for it at all.
_BARE_FALLBACK_CAVEAT_TEMPLATE = (
    "caveat: this profile rode the bare-name fallback channel -- it may be a "
    "UNION with {candidates}'s own references, not this symbol's exact "
    "profile alone; qualify further (lore_search) to isolate one symbol's "
    "profile."
)
# Disclosed fallback for the (theoretically reachable, never observed live)
# case where the channel WAS used but the graph names no OTHER known
# collidee (an astroid-unresolvable caller whose true target is not itself
# indexed under that bare name) -- still an honest "this could be wrong",
# never a blank or malformed caveat line.
_BARE_FALLBACK_NO_NAMED_CANDIDATE = "another symbol not indexed under this name"

# Concern 6 (REPORT-slate-audit-graphres.md), re-opening a narrower slice of
# finding #65's silent-narrowing class: ``_widen_dotted_target`` resolves a
# DOTTED target through ``SymbolResolver.resolve_with_candidates`` (findings
# #63/#65's PRIMARY fix) but used to discard the match's own
# ``candidate_count``/``disambiguated_by`` disclosure -- a target genuinely
# ambiguous across modules (>= 2 same-identity stored rows the resolver had
# to pick between) was silently widened to ONE winner with no signal that
# other candidates existed. The widened FQN is an EXACT graph match, so the
# bare-fallback caveat below (keyed on the GRAPH's own channel) never fires
# for this case either -- closing the disclosure gap needs its OWN caveat.
# DISCLOSE-AND-SERVE (lead ruling): the resolver's pick is still served --
# refusing to profile a real, resolvable symbol would be a worse regression
# -- but the render now names the REAL candidate count and the REAL
# disambiguation rule the resolver reports (never prose guesswork),
# mirroring S5's ``ResolvedSymbol.candidate_count``/``.disambiguated_by``
# disclosure at the sibling get_symbol tool (cross-tool consistency is
# client design law).
_WIDEN_AMBIGUOUS_CAVEAT_TEMPLATE = (
    "caveat: {original!r} widened to {widened!r} -- resolved 1 of "
    "{candidate_count} same-identity candidates ({rule}); the other "
    "candidate(s) were never profiled. Qualify further (lore_search) to "
    "isolate a specific one."
)
# Disclosed fallback for the (contract-guaranteed unreachable --
# ``ResolutionMatch.disambiguated_by`` is ``None`` only when
# ``candidate_count == 1`` -- see symbols.py) case where the render is asked
# to disclose ambiguity with no named rule: an honest hedge, never a
# malformed caveat line or a crash.
_WIDEN_AMBIGUOUS_NO_NAMED_RULE = "disambiguation rule not disclosed by the resolver"

_T = TypeVar("_T")


class _WidenResult(NamedTuple):
    """``_widen_dotted_target``'s widened FQN plus the resolver's own
    ambiguity disclosure (concern 6, REPORT-slate-audit-graphres.md).

    ``candidate_count``/``disambiguated_by`` are carried straight through
    from :class:`~loremaster.symbols.ResolutionMatch` -- never re-derived
    here -- so :meth:`ImpactEngine._render` can disclose a genuinely
    ambiguous widen (``candidate_count > 1``) instead of silently serving
    the resolver's pick with no signal that other same-identity candidates
    existed.
    """

    target: str
    candidate_count: int
    disambiguated_by: str | None


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
    (``lore_search``) — the teaching-miss standard mirroring
    :class:`~loremaster.symbols.GetSymbolError`.
    """


class ModuleRollup(BaseModel):
    """One module's aggregated consumer count at ``depth > 1``.

    Attributes:
        module: The dotted module name — its owning node's CANONICAL
            (importable) ``qualified_name`` via
            :meth:`~loremaster.graph_surreal.SurrealCodeGraph.
            module_names_by_file`, falling back to the path-derived
            :meth:`~loremaster.graph_surreal.SurrealCodeGraph.
            module_qualified_name` only when a file has no module node
            mapped (finding #52 — never the doubled path-join for a
            workspace-member directory).
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
        covering_tests: Qualified names of the tests exercising ``target``,
            capped at :data:`_MAX_RENDERED_COVERING_TESTS` entries — S1 (the
            2026-07-06 client-needs consult) reverses the #39-era "structured
            field stays full" ruling: over MCP the model IS the consumer, so
            an uncapped structured field taxes the same context an uncapped
            render would. Squeezed-out entries are counted in
            :attr:`covering_tests_elided`, never silent.
        direct_consumers: The depth-1 production consumer names (populated
            only when the EFFECTIVE query depth is 1).
        module_rollups: Per-module consumer-count rollups (populated only
            when the effective query depth is greater than 1), sorted by
            ``consumer_count`` descending then ``module`` ascending.
        elided: The count of entries squeezed out of the rendered
            consumer/rollup list by ``max_consumers`` (0 when nothing was
            squeezed) — never silent, always also named in :attr:`formatted`.
            Scoped to :attr:`direct_consumers`/:attr:`module_rollups` only;
            the covering-tests elision is counted separately in
            :attr:`covering_tests_elided` rather than overloading this field.
        covering_tests_elided: The count of covering-test names squeezed out
            of :attr:`covering_tests` by the same top-N cap the render uses
            (0 when nothing was squeezed) — never silent, always also named
            in :attr:`formatted`.
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
    covering_tests_elided: int
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
        symbol_resolver: Findings #63/#65's PRIMARY fix — the chunk-store
            resolution seam (:class:`~loremaster.symbols.SymbolResolver` in
            production, or a signature-compatible test double). Untyped
            (``Any``, the SAME duck-typed convention as ``graph`` above)
            because only :meth:`~loremaster.symbols.SymbolResolver.
            resolve_with_candidates` and :meth:`~loremaster.symbols.
            SymbolResolver.canonical_module_names` are ever called on it.
            ``None`` (the default) disables resolution widening entirely —
            every existing bare-test wiring (``ImpactEngine(graph=graph)``)
            stays valid unchanged, and a DOTTED target that cannot be widened
            behaves exactly as before (the finding #63 not-found teach).
    """

    def __init__(
        self,
        *,
        graph: Any,
        rebuild_notice: Callable[[], Awaitable[str | None]] | None = None,
        symbol_resolver: Any = None,
    ) -> None:
        self._graph = graph
        self._rebuild_notice = rebuild_notice
        self._symbol_resolver = symbol_resolver

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

        # Findings #63/#65 PRIMARY fix: widen a DOTTED target through the
        # chunk-store identity convention BEFORE any graph query runs, so a
        # module-less "Class.method" form (or any module-qualified variant
        # the resolver's own common-tail matching accepts) resolves to its
        # ONE TRUE graph FQN before the bare-fallback OR-term is ever
        # consulted. ``target`` itself is NEVER reassigned — the caller's own
        # input is echoed back in ``ImpactResult.target`` and the not-found
        # message unchanged; only ``query_target`` (what the graph is asked
        # about) may differ.
        query_target = target
        widen_result: _WidenResult | None = None
        if "." in target:
            widen_result = await self._widen_dotted_target(target)
            if widen_result is not None:
                query_target = widen_result.target

        summary = await self._graph.references(query_target)
        covering_tests, covering_test_modules, covering_test_files = await self._covering_tests(
            query_target
        )
        # S1 (2026-07-06 client-needs consult): cap the STRUCTURED wire field
        # with the SAME discipline the render already applies -- the full,
        # uncapped ``covering_tests`` list stays a local (used by ``_render``
        # for its file-rollup dominance check and by ``_target_is_known`` as
        # an existence signal); only the value that reaches ``ImpactResult``
        # is capped, with the elided count carried honestly.
        covering_tests_for_wire, covering_tests_elided = self._cap(
            covering_tests, _MAX_RENDERED_COVERING_TESTS
        )

        direct_consumers: list[str] = []
        module_rollups: list[ModuleRollup] = []
        transitive_modules: set[str] = set()
        elided = 0
        if depth == 1:
            direct_consumers, elided = self._cap(
                self._production_consumer_names(summary), max_consumers
            )
        else:
            # Fetched ONCE per call, and only when depth>1 pays for it (the
            # depth-1 path above never touches this mapping) — finding #52:
            # both rollup helpers below attribute a blast-radius node's owning
            # module through this IDENTICAL mapping, never a second,
            # potentially doubled derivation.
            module_names_by_file = await self._graph.module_names_by_file()
            rollups = await self._module_rollups(query_target, depth, module_names_by_file)
            transitive_modules = await self._transitive_only_modules(
                query_target, rollups, module_names_by_file
            )
            module_rollups, elided = self._cap(rollups, max_consumers)

        if not await self._target_is_known(
            summary, covering_tests, direct_consumers, module_rollups, query_target
        ):
            message = (
                f"no symbol or module named {target!r} appears in the code "
                f"graph (never indexed, or indexed under a different "
                f"qualified name). Next step: try lore_search({target!r}) to "
                f"locate it."
            )
            if "." in target:
                # Finding #63: the graph only matches an astroid-RESOLVED
                # full FQN or an unresolved bare written name -- an
                # intermediate, module-less "Class.method" form (exactly
                # what lore_get_symbol resolves by identity) matches
                # neither, so this miss may be a resolvable symbol whose
                # module qualifier was simply omitted. Name the one
                # actionable widen-then-retry path rather than leaving a
                # resolvable-shaped target looking like a dead end. (Still
                # the right teach even with a resolver wired: it already
                # tried widening above and found nothing either.)
                message += (
                    f" If {target!r} omits its containing module (a bare "
                    f"Class.method form), lore_get_symbol({target!r}) "
                    f"resolves by identity independent of module "
                    f"qualification -- retry lore_impact with the "
                    f"module-qualified name it names."
                )
            raise ImpactTargetNotFoundError(message)

        verdict = _VERDICT_LIVE if summary.production_references > 0 else _VERDICT_DEAD
        formatted = self._render(
            target=target,
            verdict=verdict,
            production_references=summary.production_references,
            test_references=summary.test_references,
            covering_tests=covering_tests,
            covering_test_modules=covering_test_modules,
            covering_test_files=covering_test_files,
            direct_consumers=direct_consumers,
            module_rollups=module_rollups,
            transitive_modules=transitive_modules,
            elided=elided,
            max_consumers=max_consumers,
            bare_fallback_used=summary.bare_fallback_used,
            bare_fallback_candidates=summary.bare_fallback_candidates,
            widened_target=(widen_result.target if widen_result is not None else None),
            widen_candidate_count=(
                widen_result.candidate_count if widen_result is not None else 1
            ),
            widen_disambiguated_by=(
                widen_result.disambiguated_by if widen_result is not None else None
            ),
        )
        return ImpactResult(
            target=target,
            verdict=verdict,
            production_references=summary.production_references,
            test_references=summary.test_references,
            covering_tests=covering_tests_for_wire,
            direct_consumers=direct_consumers,
            module_rollups=module_rollups,
            elided=elided,
            covering_tests_elided=covering_tests_elided,
            caveat=_CAVEAT_TEXT,
            formatted=formatted,
        )

    async def _widen_dotted_target(self, target: str) -> _WidenResult | None:
        """Resolve a DOTTED ``target`` through the chunk-store identity
        convention to its one true graph FQN (findings #63/#65's PRIMARY
        fix), or ``None`` to proceed with ``target`` unchanged.

        REUSES :class:`~loremaster.symbols.SymbolResolver` verbatim (never a
        parallel resolution implementation — packages-over-hand-rolling):
        :meth:`~loremaster.symbols.SymbolResolver.resolve_with_candidates`
        resolves ``target`` against the chunk store's own identity
        convention (a bare ``ClassName.method``, or a module-qualified
        variant reaching it via common-tail matching), and
        :meth:`~loremaster.symbols.SymbolResolver.canonical_module_names`
        (finding #62's canonical fix) names the matched row's OWNING module
        through the SAME graph-backed ``module_names_by_file`` lookup the
        graph's own node-naming uses — so the widened FQN this builds
        (``f"{module}.{identity}"``) is byte-identical to what
        :meth:`~loremaster.graph.CodeGraph._method_node` (or
        ``_class_node``/``_function_node``) would have named that same chunk.
        Never attempted for a bare target — see :meth:`impact`'s own gate.

        Concern 6 (REPORT-slate-audit-graphres.md): the returned
        :class:`_WidenResult` carries the resolver's OWN
        ``candidate_count``/``disambiguated_by`` disclosure straight through
        (never re-derived) so ``impact()`` can render an honest caveat when
        the widen was genuinely ambiguous (``candidate_count > 1``) instead
        of silently serving the resolver's pick with no signal that other
        same-identity candidates existed.

        Args:
            target: The dotted (``"." in target``) query to widen.

        Returns:
            The widened FQN plus its candidate disclosure, or ``None`` when
            no resolver is wired, the resolver finds nothing (``target`` may
            already be a real full FQN, or is genuinely unknown), or the
            matched row carries no usable module/identity — in every such
            case ``impact()`` simply proceeds with the original ``target``,
            never raising here.
        """
        if self._symbol_resolver is None:
            return None
        match = await self._symbol_resolver.resolve_with_candidates(target)
        if match is None:
            return None
        modules = await self._symbol_resolver.canonical_module_names([match.row])
        module = next(iter(modules), None)
        if module is None:
            return None
        identity = match.row.get("identity")
        if not isinstance(identity, str):
            return None
        return _WidenResult(
            target=f"{module}.{identity}",
            candidate_count=match.candidate_count,
            disambiguated_by=match.disambiguated_by,
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

    async def _covering_tests(
        self, target: str
    ) -> tuple[list[str], dict[str, str], dict[str, tuple[str, str]]]:
        """The sorted, deduplicated qualified test names covering ``target``,
        plus each name's owning-file module label AND its (tier, file_path)
        identity (T6's render-only file rollup; the returned name LIST is
        the unchanged public contract).

        The module label uses the CHEAP static
        :meth:`~loremaster.graph_surreal.SurrealCodeGraph.module_qualified_name`
        derivation (no extra graph query) rather than ``module_names_by_file``
        -- fine for DISPLAY, but that label is ``file_path``-only (it takes no
        ``tier`` argument), so two genuinely different files sharing the same
        tier-relative path in two different tiers derive the IDENTICAL label
        (F3, REPORT-audit-tweaks.md -- the "covering test always lives under a
        single-segment tests/ tree" argument this docstring used to make does
        not save it: tier collision is orthogonal to path depth). The
        returned ``(tier, file_path)`` mapping is the honest per-name file
        IDENTITY the render's "one file dominates" dominance check keys on
        instead of the label.
        """
        nodes = await self._graph.tests_for(target)
        by_name: dict[str, GraphNode] = {}
        for node in nodes:
            by_name.setdefault(node.qualified_name, node)
        names = sorted(by_name)
        modules_by_name = {
            name: self._graph.module_qualified_name(node.file_path)
            for name, node in by_name.items()
        }
        files_by_name = {
            name: (node.tier, node.file_path) for name, node in by_name.items()
        }
        return names, modules_by_name, files_by_name

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

    async def _module_rollups(
        self,
        target: str,
        depth: int,
        module_names_by_file: Mapping[tuple[str, str], str],
    ) -> list[ModuleRollup]:
        """The per-module consumer-count rollup of ``target``'s blast radius.

        Groups every node in the (generously bounded) blast radius by its
        owning module — the node's CANONICAL name via ``module_names_by_file``
        (the SAME identity the module node itself carries), falling back to
        :meth:`module_qualified_name` only for a file absent from that mapping
        (finding #52 — never the doubled path-join) — then sorts by
        ``consumer_count`` descending, ``module`` ascending — the pinned
        determinism order.
        """
        nodes = await self._graph.blast_radius(target, depth, _BLAST_RADIUS_NODE_CAP)
        counts: dict[str, int] = {}
        for node in nodes:
            module = module_names_by_file.get(
                (node.tier, node.file_path), self._graph.module_qualified_name(node.file_path)
            )
            counts[module] = counts.get(module, 0) + 1
        rollups = [
            ModuleRollup(module=module, consumer_count=count)
            for module, count in counts.items()
        ]
        rollups.sort(key=lambda rollup: (-rollup.consumer_count, rollup.module))
        return rollups

    async def _transitive_only_modules(
        self,
        target: str,
        rollups: list[ModuleRollup],
        module_names_by_file: Mapping[tuple[str, str], str],
    ) -> set[str]:
        """The rollup modules reached ONLY transitively (not direct consumers).

        A DIRECT consumer is one reachable at ``depth == 1`` (a single reverse
        hop). This runs the SAME cheap depth-1 :meth:`blast_radius` probe the
        rollups are built from, derives the direct-consumer module set through
        the IDENTICAL ``module_names_by_file`` (falling back to
        :meth:`module_qualified_name`) attribution :meth:`_module_rollups`
        uses — never a second, potentially inconsistent derivation — and
        returns every rollup module NOT in it — the transitive-only ripple.
        Deterministic: the input ``rollups`` are already the pinned sorted
        order and set membership does not perturb it.
        """
        direct_nodes = await self._graph.blast_radius(
            target, _DEPTH_MIN, _BLAST_RADIUS_NODE_CAP
        )
        direct_modules = {
            module_names_by_file.get(
                (node.tier, node.file_path), self._graph.module_qualified_name(node.file_path)
            )
            for node in direct_nodes
        }
        return {rollup.module for rollup in rollups if rollup.module not in direct_modules}

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

    @staticmethod
    def _format_rollup(rollup: ModuleRollup, transitive_modules: set[str]) -> str:
        """Render one module rollup, tagging the transitive-only ones.

        A module reached only through the depth>1 ripple (in ``transitive_modules``)
        carries :data:`_TRANSITIVE_ROLLUP_SUFFIX` inside its count parenthetical so
        it can never be read as a direct-consumer entry; a direct consumer renders
        bare (``module (count)``).
        """
        suffix = _TRANSITIVE_ROLLUP_SUFFIX if rollup.module in transitive_modules else ""
        return f"{rollup.module} ({rollup.consumer_count}{suffix})"

    # -- rendering ---------------------------------------------------------

    @staticmethod
    def _render(
        *,
        target: str,
        verdict: str,
        production_references: int,
        test_references: int,
        covering_tests: list[str],
        covering_test_modules: Mapping[str, str],
        covering_test_files: Mapping[str, tuple[str, str]],
        direct_consumers: list[str],
        module_rollups: list[ModuleRollup],
        transitive_modules: set[str],
        elided: int,
        max_consumers: int,
        bare_fallback_used: bool,
        bare_fallback_candidates: list[str],
        widened_target: str | None,
        widen_candidate_count: int,
        widen_disambiguated_by: str | None,
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
        if widened_target is not None and widen_candidate_count > 1:
            # Concern 6: disclose the RESOLVER's own ambiguity -- never
            # silently serve one of several same-identity candidates with no
            # signal that siblings existed. Fires independently of
            # ``bare_fallback_used`` below; each caveat answers a different
            # question ("was the widen step itself ambiguous" vs "did the
            # GRAPH's own channel need the risky bare-fallback OR-term for
            # the already-widened FQN"), so both may legitimately render for
            # the same result.
            rule = widen_disambiguated_by or _WIDEN_AMBIGUOUS_NO_NAMED_RULE
            lines.append(
                _WIDEN_AMBIGUOUS_CAVEAT_TEMPLATE.format(
                    original=target,
                    widened=widened_target,
                    candidate_count=widen_candidate_count,
                    rule=rule,
                )
            )
        if bare_fallback_used:
            # Findings #43/#65 (channel honesty — supersedes the old #30
            # syntax gate): the caveat keys on whether THIS result actually
            # rode the risky bare-fallback/answers_to-bridge channel, never
            # on whether ``target`` itself contains a ".". Names the real
            # colliding qualified name(s) when the graph reports any.
            candidates = (
                ", ".join(bare_fallback_candidates)
                if bare_fallback_candidates
                else _BARE_FALLBACK_NO_NAMED_CANDIDATE
            )
            lines.append(_BARE_FALLBACK_CAVEAT_TEMPLATE.format(candidates=candidates))
        if covering_tests:
            # F3 (REPORT-audit-tweaks.md): dominance is keyed on the actual
            # (tier, file_path) IDENTITY, never the module LABEL -- a label
            # is ``file_path``-derived only (tier-blind), so two distinct
            # files sharing a tier-relative path in different tiers would
            # otherwise collapse into a false "one file" claim.
            distinct_files = {covering_test_files[name] for name in covering_tests}
            if len(covering_tests) > _MAX_RENDERED_COVERING_TESTS and len(distinct_files) == 1:
                # T6: one file backs every covering test -- roll up to a count
                # + that file's module label instead of enumerating (and
                # eliding) a long near-identical name list. The structured
                # covering_tests field is capped the same way (S1) by the
                # caller; this branch only changes the TEXT shape.
                module = covering_test_modules[covering_tests[0]]
                lines.append(
                    _COVERING_TESTS_FILE_ROLLUP_TEMPLATE.format(
                        count=len(covering_tests), module=module
                    )
                )
            else:
                kept, more = ImpactEngine._cap(covering_tests, _MAX_RENDERED_COVERING_TESTS)
                tests_line = f"tests: {len(covering_tests)} ({', '.join(kept)}"
                if more:
                    # S1 (reverses finding #39): the wire-level covering_tests
                    # field is capped by this SAME call's twin in impact() --
                    # this trailer names the identical elided count, never
                    # claiming access to a full field that no longer exists.
                    tests_line += ", " + _COVERING_TESTS_ELISION_TEMPLATE.format(
                        count=more, cap=_MAX_RENDERED_COVERING_TESTS
                    )
                tests_line += ")"
                lines.append(tests_line)
        else:
            # Findings #1/#2: a genuine miss is a HEURISTIC gap, never a bare
            # confident-looking "tests: 0".
            lines.append(f"tests: {_NO_COVERING_TESTS_TEXT}")
        if direct_consumers:
            lines.append(f"consumers: {', '.join(direct_consumers)}")
        if module_rollups:
            rollup_text = ", ".join(
                ImpactEngine._format_rollup(rollup, transitive_modules)
                for rollup in module_rollups
            )
            lines.append(f"modules: {rollup_text}")
            # Finding #19 (2nd symptom): every depth>1 rollup caveats the
            # module-level import-ripple overstatement risk.
            lines.append(_MODULE_ROLLUP_RIPPLE_CAVEAT)
        if elided:
            lines.append(_ELISION_TEMPLATE.format(count=elided, cap=max_consumers))
        lines.append(_CAVEAT_TEXT)
        return "\n".join(lines)
