"""The ``get_symbol`` MCP read tool — exact, anti-hallucination symbol lookup.

``get_symbol(qualified_name)`` is the second half of the Deliverable-3 read-tool
surface. Where :mod:`loremaster.read_file` answers "show me lines N..M of this
file", this answers "show me the definition of ``Calculator.add``" — returning
the EXACT stored source of a named Python symbol plus its on-disk location
(file_path / line span / tier), so the model quotes the real definition rather
than recalling a plausible-looking one.

The lookup is a **filter-only** store query (no query vector): a symbol is found
by matching the chunk's stored ``identity`` — the python_ast qualified name
(``ClassName``, ``ClassName.method``, or a bare ``function``) — against
``qualified_name``, scoped to the Python *symbol* chunk types
(``class`` / ``method`` / ``function``). Scoping by chunk type is what keeps a
same-named ``imports`` block or a fallback ``python_window`` from masquerading as
a symbol: ``get_symbol("imports")`` is a clean not-found, not a leak of the
import block. The query rides the store's
:meth:`~loremaster.store.surreal.SurrealStore.scroll` filter-only primitive over
the ``identity`` + ``chunk_type`` columns.

**P6 store port.** ``scroll`` hands back plain FLATTENED ``dict`` rows — no
raw vector-store ``Record``/``.payload`` wrapper — so every field this module
reads (``identity`` / ``chunk_type`` / ``tier`` / ``file_path`` / ``line_start``
/ ``line_end`` / ``source_text``) is a direct dict-key lookup on the row itself.
A row may carry extra, unmodeled keys (a real ``signature`` the chunker stamps,
the schema's own ``llm_summary``, or anything else riding the flexible
``metadata`` blob) — this module reads only its six named keys and tolerates
whatever else rides along. A downed store surfaces as
:class:`~loremaster.store.surreal.SurrealConnectionError` propagating straight
out of :meth:`SymbolTool.get_symbol` — an outage must never masquerade as a
clean not-found.

The tool is dependency-injected with the
:class:`~loremaster.store.surreal.SurrealStore` so the same store machinery (and
a real-server client in tests) is reused; it owns no store wiring of its own.
"""

from __future__ import annotations

import ast
import textwrap
from collections.abc import Mapping, Sequence
from fnmatch import fnmatch
from pathlib import PurePosixPath
from typing import Any, Final, Literal, NamedTuple

from pydantic import BaseModel, ConfigDict, Field, model_validator

from loremaster.store.surreal import SurrealStore

# The python_ast chunk types that ARE code symbols (mirrors lorescribe's
# ``CHUNK_TYPE_CLASS``/``METHOD``/``FUNCTION``). Deliberately EXCLUDES ``imports``
# and ``python_window`` so a non-symbol chunk never resolves as a symbol.
SYMBOL_CHUNK_TYPES: tuple[str, ...] = ("class", "method", "function")

# How many candidate rows a single per-(identity, chunk_type) scroll fetches.
# A symbol's identity is unique within its ``(file, chunk_type)`` (the python_ast
# ``_IdentityAllocator`` disambiguates collisions with ``#N``), so one match per
# tier/file is expected; a small ceiling guards a pathological corpus without an
# unbounded scan.
_SCROLL_LIMIT = 8

# S2 fix (2026-07-06, REPORT-slate-scout-s2.md §3-4c): the METHOD chunk type,
# named locally rather than imported (this module's own convention already
# hand-lists ``SYMBOL_CHUNK_TYPES`` rather than importing lorescribe's
# ``CHUNK_TYPE_*`` constants).
_METHOD_CHUNK_TYPE = "method"

# The bound on the suffix-match scan (below) that scopes ALL stored METHOD rows
# (no identity filter — a method's stored identity is always ``ClassName.
# method``, never a bare tail, so an identity-filtered scroll can never find one
# by its bare method name alone). Generous but bounded — the SAME "never an
# unbounded scan" convention as ``_SCROLL_LIMIT`` above and
# ``map.py``'s ``_FOCUS_PROBE_MAX_RESULTS`` / ``diff.py``'s ``_MAX_LIST_LIMIT``
# elsewhere in this codebase, sized larger because this scan expects to filter
# down from MANY rows rather than fetch a near-unique match. This is a
# DEGRADED-TEACHING hint only (see ``_find_method_rows_by_suffix``): it fires
# solely on an already-missed resolution, so a corpus with more than this many
# stored methods may not surface every real sibling beyond the bound — a
# disclosed limitation, never a claim of exhaustiveness, and never a
# correctness regression (an incomplete hint is strictly better than today's
# unconditional silence).
#
# Finding #78 (2026-07-07): the prior bound of 500 was measured against this
# repo's OWN corpus and found badly undersized. Read receipt: `grep -rE '^
# (async )?def ' loremaster lorescribe loresigil skills` on 2026-07-07 counted
# ~4,484 top-level method-shaped definitions (~975 production, ~3,509 test —
# test code outnumbers production ~3.6:1 here), nearly 9x the old bound. A
# window that small let the store's deterministic-but-arbitrary ascending-id
# order crowd real production methods out of the fetch entirely (the live
# miss: ``LoreServer._enforce_search_budget``, real owner ``AppContext``,
# never surfaced) while letting whichever test row happened to land in-window
# outrank an out-of-window production one. Raised to comfortably exceed the
# measured corpus (~2x headroom over ~4,484) while remaining a firm, disclosed
# bound — never a claim this scan is literally unbounded (this teach-only path
# tolerates the extra cost: it fires solely on an already-missed resolution,
# per the constant's pre-existing rationale above).
_SUFFIX_SCROLL_LIMIT = 10_000

# Finding #62: the minimum segment count for
# ``_module_segments_from_file_path``'s repeated-leading-segment check
# (``segments[0] == segments[1]`` needs at least 2 elements to compare).
_MIN_SEGMENTS_TO_CHECK_FOR_A_REPEAT = 2

# Finding #78: production-vs-test preference for the suffix scan below. A bare
# method-tail suffix match spans the WHOLE corpus (any file, any class), so a
# test fixture that merely happens to share a production method's bare name
# could otherwise pollute -- or even outrank -- the real production teach.
# These mirror ``loremaster.graph.CodeGraph``'s own ``_TESTS_DIR_NAME`` /
# ``TEST_PATH_GLOBS`` constants EXACTLY (same dir name, same globs), kept as a
# LOCAL, disclosed duplicate rather than an import: this module deliberately
# carries no compile-time dependency on ``loremaster.graph`` (the
# ``code_graph`` constructor argument on :class:`SymbolResolver` is typed
# ``Any`` for precisely this reason). Duplicating four lines is the disclosed
# cost of keeping that boundary -- the same trade-off
# ``_module_segments_from_file_path`` already accepts for its own local
# heuristic (finding #62).
_TESTS_DIR_NAME = "tests"
_TEST_PATH_GLOBS: tuple[str, ...] = ("test_*.py", "*_test.py")

# Row keys read off the matched row (stamped by ``chunk_to_record``).
_IDENTITY_KEY = "identity"
_CHUNK_TYPE_KEY = "chunk_type"
_TIER_KEY = "tier"
_FILE_PATH_KEY = "file_path"
_LINE_START_KEY = "line_start"
_LINE_END_KEY = "line_end"
_SOURCE_TEXT_KEY = "source_text"

# The dotted separator a caller uses between module path, class, and member, and
# the path separator the stored ``file_path`` uses. The stored ``identity`` only
# ever holds the within-file qualified name (``ClassName`` / ``ClassName.method``
# / ``function``) — at most this many trailing dotted segments. The module path
# the caller prepends maps onto ``file_path``, never onto ``identity``.
_DOTTED_SEP = "."
_MAX_IDENTITY_SEGMENTS = 2
_PY_SUFFIX = ".py"

# P8d Wave 4a (finding #18, index-lag honesty): a not-found may simply be a
# not-yet-re-embedded file rather than a genuine absence — static text (no
# mtime probing) naming the two real recovery verbs.
_INDEX_LAG_HINT = (
    "If this file was recently edited, the index may be lagging — retry "
    "lore_search(wait_for_fresh=True) or lore_index(reconcile=True)."
)

# S5 (client-needs consult, 2026-07-06 — Sonnet informant §5/§7): the two real
# disambiguation mechanisms ``SymbolResolver.resolve`` can apply when a bare
# identity resolves to more than one stored candidate. Named as public
# constants (mirroring ``VERIFY_REBUILD_CAVEAT``) so a reported rule can never
# drift from what the code actually did — the caller (and this module's own
# tests) reads the SAME string the resolver stamped, never a re-typed copy.
RESOLUTION_RULE_BARE_IDENTITY: Final = (
    "chunk-type priority (class > method > function), first-stored match"
)
RESOLUTION_RULE_MODULE_QUALIFIED: Final = "module-path match against the qualified name supplied"


class GetSymbolError(Exception):
    """Raised when a qualified name resolves to no stored Python symbol.

    The message names the qualified name so the caller knows exactly what was
    not found — the clean not-found contract (never a wrong hit, never a crash).
    """


class ResolvedSymbol(BaseModel):
    """A resolved Python symbol's stored definition and on-disk location.

    Attributes:
        qualified_name: The qualified name that was resolved (the chunk
            ``identity`` — ``ClassName`` / ``ClassName.method`` / ``function``).
        chunk_type: The python_ast chunk type (``class`` / ``method`` /
            ``function``).
        tier: The source tier/root the symbol's file belongs to.
        file_path: The tier-relative path of the file defining the symbol — pairs
            with the line span for a ``read_file`` round-trip.
        line_start: First source line (1-based) of the definition.
        line_end: Last source line (1-based) of the definition.
        source: The EXACT stored definition text (the chunk's ``source_text``).
        candidate_count: How many stored rows share the identity this name
            resolved to, scanned across every symbol chunk type — 1 when the
            match was unique, more when a real same-named sibling is stored
            elsewhere (S5, client-needs consult 2026-07-06: trust in a
            resolution should never require already knowing the corpus).
        disambiguated_by: The REAL mechanism :meth:`SymbolResolver.resolve`
            used to pick this one row from among ``candidate_count`` stored
            siblings — ``None`` exactly when ``candidate_count`` is 1 (nothing
            needed disambiguating). One of :data:`RESOLUTION_RULE_BARE_IDENTITY`
            / :data:`RESOLUTION_RULE_MODULE_QUALIFIED` when it is not ``None``.
    """

    model_config = ConfigDict(extra="forbid")

    qualified_name: str
    chunk_type: str
    tier: str
    file_path: str
    line_start: int
    line_end: int
    source: str
    candidate_count: int
    disambiguated_by: str | None


class ResolutionMatch(NamedTuple):
    """A resolved row plus how many stored candidates shared the identity it matched.

    ``candidate_count`` is the number of stored rows carrying the SAME bare
    identity as ``row`` — scanned across every symbol chunk type via
    :meth:`SymbolResolver._find_all_by_identity`, the identical machinery the
    miss path already runs in :meth:`SymbolResolver.find_siblings` — 1 when the
    match was unique, more when a real same-named sibling is stored elsewhere.
    ``disambiguated_by`` names the REAL mechanism :meth:`SymbolResolver.resolve`
    used to pick ``row`` from among them; it is ``None`` exactly when
    ``candidate_count`` is 1 (nothing needed disambiguating).
    """

    row: dict[str, Any]
    candidate_count: int
    disambiguated_by: str | None


class SymbolResolver:
    """Resolve a qualified Python name to the stored chunk ROW it names, or ``None``.

    The shared, tool-agnostic resolution seam extracted from ``SymbolTool``: it
    owns the two-stage lookup (exact-identity, then module-qualified common-tail
    matching) and hands back the raw matched store row, leaving the caller to
    decide what a hit or a miss MEANS. :class:`SymbolTool` maps a hit into a
    :class:`ResolvedSymbol` and raises :class:`GetSymbolError` on a miss;
    :class:`VerifyTool` maps a hit into a summary and a miss into a
    ``not_found`` result — same resolution, two error postures. Both ride this
    ONE resolver so their resolution semantics can never drift apart.

    Args:
        store: The :class:`~loremaster.store.surreal.SurrealStore` holding the
            project's indexed chunks. Injected so the same store (and a real
            client in tests) is reused; the resolver owns no store wiring itself.
        code_graph: Finding #62's canonical fix. The code graph
            (:class:`~loremaster.graph_surreal.SurrealCodeGraph` in
            production, or a signature-compatible test double) to consult for
            :meth:`canonical_module_names`'s graph-backed module lookup.
            Untyped (``Any``) because only ``module_names_by_file()`` is
            ever called on it — the SAME duck-typed convention
            :class:`~loremaster.impact.ImpactEngine` already uses for its own
            ``graph`` dependency. ``None`` (the default) means no graph is
            available — every lookup then falls back to the path-derived
            heuristic (:meth:`_module_segments_from_file_path`), exactly the
            pre-#62-upgrade behaviour; this keeps every bare-test wiring
            (``SymbolResolver(store=store)``) valid unchanged.
    """

    def __init__(self, *, store: SurrealStore, code_graph: Any | None = None) -> None:
        self._store = store
        self._code_graph = code_graph

    async def resolve(self, qualified_name: str) -> dict[str, Any] | None:
        """Return the stored row ``qualified_name`` names, or ``None`` if none does.

        Resolves against the symbol chunk types (``class`` / ``method`` /
        ``function``) only — scoping to symbol types is what makes a same-named
        ``imports`` block or a fallback window never resolve as a symbol.

        Resolution is two-stage. First an EXACT match on the stored ``identity``
        (a bare ``ClassName`` / ``ClassName.method`` / ``function``) — the form
        the chunker stores; the first such chunk wins (a bare identity passed
        directly is unambiguous to the caller). If that misses and
        ``qualified_name`` is dotted, it is treated as MODULE-qualified
        (``pkg.mod.ClassName.method``): the trailing 1–2 segments are the candidate
        stored identity and the leading segments are the module path. The lookup
        considers EVERY stored chunk carrying that bare identity and returns the
        one whose ``file_path`` path-matches the caller's module path. So when a
        bare identity collides across files, each sibling is reachable by its OWN
        fully-qualified name (the correct file resolves, not an arbitrary one);
        a name whose module path matches no stored file — a different module, or a
        genuinely-absent symbol — is a clean ``None``, never a wrong-file hit.
        This is purely a lookup-side resolution; nothing is re-indexed.

        Args:
            qualified_name: The symbol's qualified name. Either the bare stored
                identity (``ClassName`` / ``ClassName.method`` / ``function``) or
                a module-qualified dotted name (``pkg.mod.ClassName.method``), with
                or without a repeated package directory in the module path.

        Returns:
            The matched store row (a FLATTENED ``dict``), or ``None`` when no
            Python symbol chunk resolves.

        Raises:
            SurrealConnectionError: The store's connection is down — propagates
                straight through, never masquerading as a clean ``None``.
        """
        match = await self.resolve_with_candidates(qualified_name)
        return match.row if match is not None else None

    async def resolve_with_candidates(self, qualified_name: str) -> ResolutionMatch | None:
        """Resolve like :meth:`resolve`, plus the candidate count/rule to disclose.

        :meth:`resolve` delegates to this method (never the reverse), so the
        two can never drift apart on which row wins — this is simply
        :meth:`resolve`'s own two-stage walk (stage 1: bare exact-identity;
        stage 2: module-qualified common-tail match), with each stage also
        reporting how many stored rows shared the winning identity and, when
        more than one did, the REAL rule used to pick this one (S5):

        * Stage 1 (:meth:`_find_by_identity`): the candidate set is EVERY
          stored row sharing the bare identity, across all symbol chunk types
          (:meth:`_find_all_by_identity` — the same machinery the miss path
          already runs in :meth:`find_siblings`); the rule is
          :data:`RESOLUTION_RULE_BARE_IDENTITY` (the chunk-type-priority,
          first-stored scan :meth:`_find_by_identity` actually performs).
        * Stage 2 (module-qualified common-tail match): the candidate set is
          the rows :meth:`_module_qualified_candidates` gathered at the
          identity length that matched; the rule is
          :data:`RESOLUTION_RULE_MODULE_QUALIFIED` (the caller's own module
          qualification is what picked this row out of its siblings).

        Args:
            qualified_name: Same as :meth:`resolve`.

        Returns:
            The winning row plus its candidate count/rule, or ``None`` when
            :meth:`resolve` would also return ``None``.

        Raises:
            SurrealConnectionError: The store's connection is down — propagates
                straight through, never masquerading as a clean ``None``.
        """
        exact = await self._find_by_identity(qualified_name)
        if exact is not None:
            candidate_count = len(await self._find_all_by_identity(qualified_name))
            return ResolutionMatch(
                row=exact,
                candidate_count=candidate_count,
                disambiguated_by=(
                    RESOLUTION_RULE_BARE_IDENTITY if candidate_count > 1 else None
                ),
            )
        for module_segments, candidates in await self._module_qualified_candidates(
            qualified_name
        ):
            for row in candidates:
                if self._module_path_matches(row, module_segments):
                    candidate_count = len(candidates)
                    return ResolutionMatch(
                        row=row,
                        candidate_count=candidate_count,
                        disambiguated_by=(
                            RESOLUTION_RULE_MODULE_QUALIFIED if candidate_count > 1 else None
                        ),
                    )
        return None

    async def _find_by_identity(self, identity: str) -> dict[str, Any] | None:
        """Return the first symbol row whose stored ``identity`` equals ``identity``.

        Scans the symbol chunk types in order and returns the first exact match,
        or ``None`` when no symbol chunk carries that identity. Used by the
        EXACT-match fast path, where the caller passed the bare stored identity and
        any match is correct; module-qualified resolution uses
        :meth:`_find_all_by_identity` instead, to disambiguate cross-file collisions.

        Args:
            identity: The bare within-file identity to match exactly.

        Returns:
            The matched row, or ``None``.
        """
        for chunk_type in SYMBOL_CHUNK_TYPES:
            rows = await self._store.scroll(
                filters={_IDENTITY_KEY: identity, _CHUNK_TYPE_KEY: chunk_type},
                limit=_SCROLL_LIMIT,
            )
            if rows:
                return rows[0]
        return None

    async def _find_all_by_identity(self, identity: str) -> list[dict[str, Any]]:
        """Return EVERY symbol row whose stored ``identity`` equals ``identity``.

        A bare identity can COLLIDE across files (the python_ast chunker stamps the
        same within-file ``identity`` for same-named symbols in different modules —
        e.g. ``EmbeddingConfig`` in two packages). Module-qualified resolution must
        see all of them to pick the one whose ``file_path`` matches the caller's
        module path; testing only the first-scrolled row would make every other
        sibling unreachable (and which one is reachable is scroll-order-dependent).

        Args:
            identity: The bare within-file identity to match exactly.

        Returns:
            All matching rows across the symbol chunk types (possibly empty);
            order is not significant — the caller filters by ``file_path``.
        """
        matches: list[dict[str, Any]] = []
        for chunk_type in SYMBOL_CHUNK_TYPES:
            matches.extend(
                await self._store.scroll(
                    filters={_IDENTITY_KEY: identity, _CHUNK_TYPE_KEY: chunk_type},
                    limit=_SCROLL_LIMIT,
                )
            )
        return matches

    @staticmethod
    def _is_test_path(file_path: str) -> bool:
        """Whether ``file_path`` is a test file (glob or ``tests/`` dir).

        Finding #78: mirrors ``loremaster.graph.CodeGraph._is_test_path``
        exactly (same constants, same rule) — see :data:`_TESTS_DIR_NAME` /
        :data:`_TEST_PATH_GLOBS` for why this is a local disclosed duplicate
        rather than an import. Used by :meth:`_find_method_rows_by_suffix` to
        prefer a production-owned method over a same-named test fixture when
        a suffix match spans both.
        """
        path = PurePosixPath(file_path)
        if _TESTS_DIR_NAME in path.parts:
            return True
        return any(fnmatch(path.name, glob) for glob in _TEST_PATH_GLOBS)

    async def _find_method_rows_by_suffix(self, tail: str) -> list[dict[str, Any]]:
        """Every stored METHOD row whose identity ends with ``.{tail}`` (any
        class), production rows preferred over test rows.

        S2 fix (2026-07-06, REPORT-slate-scout-s2.md §3-4c): a stored method
        identity is ALWAYS ``ClassName.method`` (never a bare tail), so an
        exact-identity lookup on a bare method name — the only thing
        :meth:`_module_qualified_candidates`'s trailing-1-segment candidate can
        ever try — can never find one. Without this, a wrong-or-missing CLASS
        guess (the live failure: ``LoreServer._enforce_search_budget`` when the
        real owner is ``AppContext``) finds zero candidates at ANY identity
        length and degrades SILENTLY — the asymmetry versus a wrong-MODULE
        guess, which the SAME candidate machinery already teaches via
        :meth:`find_siblings`. This closes it with a suffix match scoped to
        METHOD-chunk rows only (class/function identities are already reachable
        by their own exact bare tail, so they need no suffix arm).

        No store-level suffix/``LIKE`` primitive exists (:meth:`~loremaster.
        store.surreal.SurrealStore.scroll` is exact-match-only by design), so
        this fetches a BOUNDED, unfiltered-by-identity window of method rows
        (:data:`_SUFFIX_SCROLL_LIMIT`, raised at finding #78 to comfortably
        exceed this repo's measured corpus) and filters client-side — a
        degraded teaching hint, not an exhaustive guarantee (see the
        constant's own docstring for the disclosed bound).

        Finding #78: a bare tail can ALSO match a test fixture that merely
        happens to share the production method's name — the suffix match has
        no class context to disambiguate the two. When the fetched-and-
        filtered rows include at least one PRODUCTION row
        (:meth:`_is_test_path` false), every test row is dropped from the
        result — a teach must never name a test module when a production
        definition exists. When EVERY matching row is a test row, they are
        returned as-is: teaching a test-only symbol, honestly labelled by its
        own (test-shaped) module name, is strictly better than a silent miss.

        Args:
            tail: The bare (undotted) candidate method name to suffix-match.

        Returns:
            Every fetched method row whose identity ends with ``.{tail}``,
            filtered to production-only rows when at least one matched;
            possibly empty; order is not significant.
        """
        rows = await self._store.scroll(
            filters={_CHUNK_TYPE_KEY: _METHOD_CHUNK_TYPE},
            limit=_SUFFIX_SCROLL_LIMIT,
        )
        suffix = f"{_DOTTED_SEP}{tail}"
        matches = [row for row in rows if str(row.get(_IDENTITY_KEY, "")).endswith(suffix)]
        production_matches = [
            row for row in matches if not self._is_test_path(str(row.get(_FILE_PATH_KEY, "")))
        ]
        return production_matches if production_matches else matches

    async def find_siblings(self, qualified_name: str) -> list[dict[str, Any]]:
        """The sibling rows sharing ``qualified_name``'s bare tail, ANY module.

        P8d Wave 4a (finding #17): when a module-qualified lookup misses
        (:meth:`resolve` returned ``None``), this answers "does the BARE name
        exist somewhere else?" — the first identity-length whose bare tail has
        ANY stored row wins (mirroring :meth:`resolve_with_candidates`'s own
        length-priority order), regardless of whether ITS module path matches
        the caller's prefix. :class:`SymbolTool` uses this to name the real
        module(s) holding the symbol instead of a bare not-found. ``[]`` for a
        bare (non-dotted) name — there is no "other module" to suggest.

        Args:
            qualified_name: The full dotted name the caller passed.

        Returns:
            Every row sharing the bare tail at the first non-empty identity
            length, or ``[]`` when nothing shares any candidate tail.
        """
        for _module_segments, candidates in await self._module_qualified_candidates(
            qualified_name
        ):
            if candidates:
                return candidates
        return []

    async def _module_qualified_candidates(
        self, qualified_name: str
    ) -> list[tuple[list[str], list[dict[str, Any]]]]:
        """The ``(module_segments, candidate_rows)`` pairs a dotted name tries, in order.

        Shared by :meth:`resolve_with_candidates` (which additionally filters by
        module-path match to pick the winning row) and :meth:`find_siblings`
        (which does not) — a SINGLE place walks the trailing-1-then-2-segment
        identity-length priority so the two can never drift apart on which
        candidates a given dotted name considers.

        At ``identity_length == 1`` (a bare tail — the shape a wrong-or-missing
        CLASS guess reduces to, e.g. ``LoreServer._enforce_search_budget``
        trying bare ``_enforce_search_budget``), the exact-identity match ABOVE
        can only ever find a class/function collision (a method's stored
        identity is never bare). The candidate set is widened with a METHOD
        suffix match (:meth:`_find_method_rows_by_suffix`, S2 fix) so a
        same-named method under a DIFFERENT class also surfaces here — closing
        the wrong-class/wrong-module asymmetry :meth:`find_siblings` teaches.
        """
        segments = qualified_name.split(_DOTTED_SEP)
        pairs: list[tuple[list[str], list[dict[str, Any]]]] = []
        for identity_length in range(1, _MAX_IDENTITY_SEGMENTS + 1):
            if identity_length >= len(segments):
                # No leading module segments remain — that is the exact case,
                # already handled by ``_find_by_identity``; nothing module-qualified.
                break
            module_segments = segments[:-identity_length]
            candidate_identity = _DOTTED_SEP.join(segments[-identity_length:])
            candidates = await self._find_all_by_identity(candidate_identity)
            if identity_length == 1:
                candidates = candidates + await self._find_method_rows_by_suffix(
                    candidate_identity
                )
            pairs.append((module_segments, candidates))
        return pairs

    @staticmethod
    def _module_segments_from_file_path(file_path: str) -> list[str]:
        """Derive the dotted module path segments a stored ``file_path`` maps to.

        ``pkg/calc.py`` -> ``["pkg", "calc"]``; ``pkg/__init__.py`` -> ``["pkg"]``
        (``__init__`` is the package itself, never its own segment).

        Finding #62 (2026-07-06, REPORT-slate-scout-s2.md §3 side note): a
        workspace-member directory whose Python package shares its OWN name —
        this repo's own layout, ``loremaster/loremaster/server.py`` —
        otherwise doubles here (``["loremaster", "loremaster", "server"]``),
        which surfaced verbatim in :meth:`SymbolTool.get_symbol`'s miss-teach
        message as ``loremaster.loremaster.server``. An immediately-repeated
        LEADING segment is collapsed to one — a LOCAL heuristic, not the
        canonical fix ``loremaster.map``'s finding #52 uses
        (``module_names_by_file``, a GRAPH-level lookup keyed off the file's
        own synthesized module node; this resolver has no graph dependency —
        see REPORT-slate-builder-s2.md decisions-needed for the wiring change
        that would be needed to share it). Confirmed safe for
        :meth:`_module_path_matches`'s CALLER: that comparison is common-TAIL
        based (``[-common_length:]``), so shortening a duplicated leading
        segment cannot turn an existing match into a miss (the compared tail
        is unchanged) — only fixes the segments a MISS TEACH message prints. A
        project with a genuine, deliberately same-named NESTED subpackage
        (``foo/foo/bar.py`` where both really are packages) would be
        mis-collapsed too — a disclosed trade-off for a teaching-only value,
        never presented as authoritative.
        """
        pure_path = PurePosixPath(file_path)
        segments = list(pure_path.parts[:-1])
        stem = pure_path.name
        if stem.endswith(_PY_SUFFIX):
            stem = stem[: -len(_PY_SUFFIX)]
        if stem and stem != "__init__":
            segments.append(stem)
        if len(segments) >= _MIN_SEGMENTS_TO_CHECK_FOR_A_REPEAT and segments[0] == segments[1]:
            segments = segments[1:]
        return segments

    async def canonical_module_names(self, rows: Sequence[dict[str, Any]]) -> set[str]:
        """The DISTINCT canonical module name(s) owning each row's file.

        Finding #62's canonical fix: :meth:`SymbolTool.get_symbol`'s sibling-
        teach path (the only caller) needs "which module(s) really define
        this bare name" — this consults the injected code graph's
        ``module_names_by_file()`` ONCE for every row (the SAME graph-level
        lookup :class:`~loremaster.map.MapEngine`'s finding #52 fix and
        :meth:`~loremaster.server.AppContext._resolve_changed_modules` both
        read), falling back PER ROW to the path-derived
        :meth:`_module_segments_from_file_path` heuristic (finding #62's
        ORIGINAL, narrower fix) when no graph was wired at construction, or
        the mapping has no entry for a given ``(tier, file_path)`` (a
        non-Python file, a half-purged store, or a bare-test wiring with no
        graph dependency) — never a ``KeyError``, and the heuristic never
        overrides an available canonical answer.

        The heuristic fallback is kept deliberately, as defense-in-depth: it
        only collapses an immediately-repeated LEADING path segment, so it
        cannot reproduce the graph's on-disk ``__init__.py``-probed canonical
        name in general — a ``src/`` layout with no repeated segment
        anywhere is the decisive counter-example (see
        ``TestCanonicalModuleNameTeaching`` in the test suite) — exactly why
        the canonical route is preferred whenever a graph is available.

        Args:
            rows: The candidate rows (as returned by :meth:`find_siblings`)
                to name the owning module of.

        Returns:
            The distinct module names, one per distinct owning file; empty
            when ``rows`` carries no row with a string ``file_path``.
        """
        module_names_by_file: Mapping[tuple[str, str], str] = {}
        if self._code_graph is not None:
            module_names_by_file = await self._code_graph.module_names_by_file()
        names: set[str] = set()
        for row in rows:
            file_path = row.get(_FILE_PATH_KEY)
            if not isinstance(file_path, str):
                continue
            tier = row.get(_TIER_KEY)
            canonical = (
                module_names_by_file.get((tier, file_path)) if isinstance(tier, str) else None
            )
            names.add(
                canonical
                if canonical is not None
                else ".".join(self._module_segments_from_file_path(file_path))
            )
        return names

    @classmethod
    def _module_path_matches(cls, row: dict[str, Any], module_segments: list[str]) -> bool:
        """Whether the row's module path is a trailing match of ``module_segments``.

        The stored ``file_path`` (e.g. ``pkg/calc.py``) maps to a dotted module
        path (``pkg.calc``). The caller's module path and the file's module path
        must agree on their COMMON TAIL — the trailing segments of the shorter,
        compared in order, must equal the other's tail. That makes all of:
        exactly-qualified (``pkg.calc.X``), over-qualified / repeated-package
        (``loremaster.loremaster.index.indexer.X``), and under-qualified / missing
        the repeated package dir (``loremaster.index.indexer.X``) resolve to the
        same row, while an unrelated ``other.mod.X`` does not (its tail differs).
        The reported bug passed BOTH the under- and over-qualified forms; the
        common-tail rule accepts each without a wrong cross-module hit.

        Args:
            row: The candidate matched row (its ``file_path`` is the anchor).
            module_segments: The caller's leading dotted segments (the module path).

        Returns:
            ``True`` when the file's and caller's module paths share a full
            common tail (the shorter path equals the other's trailing segments).
        """
        file_path = row.get(_FILE_PATH_KEY)
        if not isinstance(file_path, str):
            return False
        file_module_segments = cls._module_segments_from_file_path(file_path)
        if not module_segments or not file_module_segments:
            return False
        # Compare the common tail: the shorter path's segments must equal the
        # other's trailing segments. Tolerates an extra/missing repeated leading
        # package directory in either direction without a cross-module wrong hit.
        common_length = min(len(module_segments), len(file_module_segments))
        return module_segments[-common_length:] == file_module_segments[-common_length:]


class SymbolTool:
    """Resolve a qualified Python name to its exact stored definition + location.

    A thin adapter over :class:`SymbolResolver`: it delegates the lookup and maps
    the outcome into the get_symbol contract — a hit becomes a
    :class:`ResolvedSymbol` (the exact definition + on-disk anchor), a miss becomes
    a :class:`GetSymbolError` (a clean, actionable not-found). ``verify`` shares the
    SAME resolver but answers a different question (does a CLAIM hold?), so
    resolution can never drift between the two tools.

    Args:
        store: The :class:`~loremaster.store.surreal.SurrealStore` holding the
            project's indexed chunks. Injected so the same store (and a real
            client in tests) is reused; the tool owns no store wiring itself.
        code_graph: Finding #62's canonical fix — forwarded to
            :class:`SymbolResolver` so the miss-teach path's module naming
            can prefer the graph's canonical ``module_names_by_file()``
            lookup over the path-derived heuristic. ``None`` (the default)
            keeps the pre-#62-upgrade heuristic-only behaviour.
    """

    def __init__(self, *, store: SurrealStore, code_graph: Any | None = None) -> None:
        self._resolver = SymbolResolver(store=store, code_graph=code_graph)

    async def get_symbol(self, qualified_name: str) -> ResolvedSymbol:
        """Return the stored definition + location for ``qualified_name``.

        Delegates resolution to :meth:`SymbolResolver.resolve` (exact identity,
        then module-qualified common-tail matching) and maps its outcome: a
        matched row becomes a :class:`ResolvedSymbol`; a ``None`` becomes a clean,
        actionable :class:`GetSymbolError` naming the qualified name.

        Args:
            qualified_name: The symbol's qualified name. Either the bare stored
                identity (``ClassName`` / ``ClassName.method`` / ``function``) or
                a module-qualified dotted name (``pkg.mod.ClassName.method``), with
                or without a repeated package directory in the module path.

        Returns:
            The resolved symbol's exact source and location.

        Raises:
            GetSymbolError: If no Python symbol chunk resolves — a clean
                not-found, naming the qualified name. When the BARE tail
                resolves under a DIFFERENT module (P8d Wave 4a, finding #17),
                the message names the real module(s) holding it instead of a
                bare miss.
            SurrealConnectionError: The store's connection is down — propagates
                straight through, never masquerading as a clean not-found.
        """
        match = await self._resolver.resolve_with_candidates(qualified_name)
        if match is not None:
            return self._to_resolved(match)
        siblings = await self._resolver.find_siblings(qualified_name)
        if siblings:
            modules = sorted(await self._resolver.canonical_module_names(siblings))
            if modules:
                raise GetSymbolError(
                    f"no Python symbol named {qualified_name!r} is indexed under that "
                    f"module path, but the bare name is defined in: {', '.join(modules)}. "
                    f"Next step: module-qualify with one of those modules, or try "
                    f"lore_search({qualified_name!r}). {_INDEX_LAG_HINT}"
                )
        raise GetSymbolError(
            f"no Python symbol named {qualified_name!r} is indexed "
            f"(searched chunk types {SYMBOL_CHUNK_TYPES!r}). Next step: try "
            f"lore_search({qualified_name!r}) for a semantic match, or module-qualify "
            f"the name if it collides across files (e.g. 'pkg.mod.Name'). "
            f"{_INDEX_LAG_HINT}"
        )

    @staticmethod
    def _to_resolved(match: ResolutionMatch) -> ResolvedSymbol:
        """Map a matched store row + its candidate disclosure into a :class:`ResolvedSymbol`.

        Reads only the row's six named keys — its FLATTENED shape may carry
        extra, unmodeled keys (a real ``signature``, ``llm_summary``, or a
        future ``metadata`` addition) which are simply ignored, never breaking
        resolution. ``candidate_count``/``disambiguated_by`` are carried
        straight through from ``match`` (S5) — never re-derived here.
        """
        row = match.row
        return ResolvedSymbol(
            qualified_name=row[_IDENTITY_KEY],
            chunk_type=row[_CHUNK_TYPE_KEY],
            tier=row[_TIER_KEY],
            file_path=row[_FILE_PATH_KEY],
            line_start=row[_LINE_START_KEY],
            line_end=row[_LINE_END_KEY],
            source=row[_SOURCE_TEXT_KEY],
            candidate_count=match.candidate_count,
            disambiguated_by=match.disambiguated_by,
        )


# ``verify``'s three terminal verdicts. ``confirmed`` = the symbol resolved and
# every supplied expectation held; ``mismatch`` = it resolved but at least one
# expectation failed; ``not_found`` = nothing resolved (a RESULT, never an
# exception — answering "does this exist?" is verify's whole job).
_STATUS_CONFIRMED: Final = "confirmed"
_STATUS_MISMATCH: Final = "mismatch"
_STATUS_NOT_FOUND: Final = "not_found"

# The claim labels a :class:`VerifyMismatch` carries, naming WHICH expectation
# failed so the caller can tell a wrong-path claim from a wrong-signature one.
_CLAIM_FILE_PATH = "file_path"
_CLAIM_SIGNATURE = "signature"

# Fallback-only terminator. The header is normally derived from the parsed AST
# (the body boundary — comment/string-safe by construction); this ``:`` scan is
# used ONLY when a stored chunk fails to parse as a single def/class (a degenerate
# row that is never a real symbol chunk), so verify degrades instead of crashing.
_HEADER_TERMINATOR = ":"

# The caveat line the SERVER layer stamps onto a ``not_found`` :class:`VerifyResult`
# when it detects that a schema rebuild is re-embedding the corpus. During that
# window a symbol may simply be not-yet-re-embedded, so ``not_found`` is a possible
# TRANSIENT false negative — the caveat says so (operator disposition:
# serve-and-say-so, never suppress the answer). ``verify`` itself never sets this
# (it has no manifest to consult); it defaults ``None`` so every wave-A construction
# stays valid, and the server sets it via ``model_copy`` (see ``AppContext.verify``).
VERIFY_REBUILD_CAVEAT: Final = (
    "CAVEAT: a schema rebuild is in progress — this not_found may be a TRANSIENT "
    "false negative (the symbol may be not-yet-re-embedded). Re-run verify once the "
    "rebuild settles before trusting this absence."
)


class VerifiedSummary(BaseModel):
    """The resolved-symbol summary ``verify`` echoes back — the stored TRUTH.

    Carries the same on-disk anchor as :class:`ResolvedSymbol` but summarised: the
    definition HEADER line(s) — the decorators plus the complete signature, never
    the docstring or body — enough for the caller to eyeball what actually exists
    without dumping the whole definition.

    Attributes:
        qualified_name: The resolved chunk ``identity``.
        chunk_type: The python_ast chunk type (``class`` / ``method`` /
            ``function``).
        tier: The source tier/root the symbol's file belongs to.
        file_path: The tier-relative path of the file defining the symbol.
        line_start: First source line (1-based) of the definition.
        line_end: Last source line (1-based) of the definition.
        header: The definition's header — every ``source_text`` line strictly
            before the first body statement (so any decorators and the full,
            possibly multi-line, signature are kept whole; the docstring and body
            are dropped). A one-line ``def f(): return x`` — whose body shares the
            signature's physical line — keeps that single line. Derived from the
            parsed AST, so a trailing comment or a ``:`` inside a comment on the
            signature never leaks the body in or truncates the signature out.
    """

    model_config = ConfigDict(extra="forbid")

    qualified_name: str
    chunk_type: str
    tier: str
    file_path: str
    line_start: int
    line_end: int
    header: str


class VerifyMismatch(BaseModel):
    """One failed expectation — what was CLAIMED versus what is actually stored.

    Attributes:
        claim: Which expectation failed (:data:`_CLAIM_FILE_PATH` /
            :data:`_CLAIM_SIGNATURE`).
        claimed: The value the caller asserted.
        actual: The stored truth that contradicts it (the ACTUAL path, or the
            ACTUAL header the fragment was not found in).
    """

    model_config = ConfigDict(extra="forbid")

    claim: str
    claimed: str
    actual: str


class VerifyResult(BaseModel):
    """The verdict ``verify`` returns for a symbol/signature/location claim.

    ``status`` is exactly one of ``confirmed`` / ``mismatch`` / ``not_found``.
    ``summary`` carries the stored truth whenever resolution succeeded (both
    ``confirmed`` and ``mismatch``) and is ``None`` on ``not_found``.
    ``mismatches`` lists every failed expectation (non-empty exactly when
    ``status`` is ``mismatch``).

    Attributes:
        status: The terminal verdict (``confirmed`` / ``mismatch`` /
            ``not_found``).
        summary: The resolved-symbol summary (the stored truth), or ``None`` when
            nothing resolved.
        mismatches: The failed expectations; empty unless ``status`` is
            ``mismatch``.
        rebuilding_caveat: An OPTIONAL caveat line (defaulting ``None``) the SERVER
            layer stamps onto a ``not_found`` verdict when a schema rebuild is
            re-embedding the corpus — during that window a ``not_found`` may be a
            TRANSIENT false negative (the symbol not-yet-re-embedded). ``verify``
            never sets it (it has no manifest to consult). The ``status`` invariant
            below now BINDS this field too: a non-``None`` caveat is legal ONLY when
            ``status`` is ``not_found`` — a ``confirmed``/``mismatch`` verdict can
            never carry one, since only a schema-rebuild-affected absence is ever
            transient.
    """

    model_config = ConfigDict(extra="forbid")

    status: Literal["confirmed", "mismatch", "not_found"]
    summary: VerifiedSummary | None = None
    mismatches: list[VerifyMismatch] = Field(default_factory=list)
    rebuilding_caveat: str | None = None

    @model_validator(mode="after")
    def _check_status_invariant(self) -> VerifyResult:
        """Make the ``status`` ↔ ``summary`` ↔ ``mismatches`` ↔ ``rebuilding_caveat``
        contract structural.

        Enforces, at construction, the invariants the docstring promises so a
        malformed verdict can never be built (not merely avoided by the ``verify``
        path): ``summary`` is ``None`` EXACTLY on ``not_found``; ``mismatches`` is
        non-empty EXACTLY on ``mismatch``; and ``rebuilding_caveat`` may be
        non-``None`` ONLY when ``status`` is ``not_found`` (audit-waveb-1 finding
        #3 — the server only ever stamps a caveat onto a ``not_found`` verdict
        during an active rebuild window, so a ``confirmed``/``mismatch`` result
        carrying one would be a defect, not a legitimate value).
        """
        if (self.summary is None) != (self.status == _STATUS_NOT_FOUND):
            raise ValueError(
                "summary must be None exactly when status is "
                f"{_STATUS_NOT_FOUND!r}; got status={self.status!r} with "
                f"summary={'None' if self.summary is None else 'a summary'}"
            )
        if bool(self.mismatches) != (self.status == _STATUS_MISMATCH):
            raise ValueError(
                "mismatches must be non-empty exactly when status is "
                f"{_STATUS_MISMATCH!r}; got status={self.status!r} with "
                f"{len(self.mismatches)} mismatch(es)"
            )
        if self.rebuilding_caveat is not None and self.status != _STATUS_NOT_FOUND:
            raise ValueError(
                "rebuilding_caveat must be None unless status is "
                f"{_STATUS_NOT_FOUND!r}; got status={self.status!r} with a "
                "non-None rebuilding_caveat"
            )
        return self


class VerifyTool:
    """Verify a symbol/signature/location CLAIM against the stored truth.

    The anti-hallucination verb: before an agent repeats "``X`` lives in ``Y`` with
    signature ``Z``", ``verify`` checks it and answers ``confirmed`` /
    ``mismatch`` / ``not_found`` with the stored facts. It rides the SAME
    :class:`SymbolResolver` as :class:`SymbolTool` (so a name resolves to the same
    row through both), but where ``get_symbol`` RAISES on a miss, ``verify`` returns
    ``not_found`` as a RESULT — its whole job is answering "does this exist?".

    Args:
        store: The :class:`~loremaster.store.surreal.SurrealStore` holding the
            project's indexed chunks. Injected so the same store is reused; the
            tool owns no store wiring itself.
    """

    def __init__(self, *, store: SurrealStore) -> None:
        self._resolver = SymbolResolver(store=store)

    async def verify(
        self,
        qualified_name: str,
        expected_file_path: str | None = None,
        expected_signature_fragment: str | None = None,
    ) -> VerifyResult:
        """Check ``qualified_name`` (and any supplied expectations) against the store.

        Resolves ``qualified_name`` through the shared :class:`SymbolResolver`. A
        miss is a ``not_found`` RESULT (never an exception). On a hit, each
        supplied expectation is checked against the stored truth:

        * ``expected_file_path`` matches when it whole-path-segment-suffix-matches
          the stored tier-relative ``file_path`` in EITHER direction
          (``loremaster/symbols.py`` matches ``loremaster/loremaster/symbols.py``;
          a mid-segment fragment like ``ymbols.py`` does not). A miss names the
          ACTUAL path.
        * ``expected_signature_fragment`` matches when it is a substring of the
          definition HEADER (the decorators plus the complete signature — every
          ``source_text`` line strictly before the first body statement, derived
          from the parsed AST so a trailing comment can neither leak the body in
          nor truncate the signature out). A miss shows the ACTUAL header.

        The verdict is ``confirmed`` when every supplied expectation holds (or none
        was supplied), ``mismatch`` when at least one fails.

        Args:
            qualified_name: The symbol's qualified name (bare identity or a
                module-qualified dotted name), resolved exactly as ``get_symbol``.
            expected_file_path: An optional claimed tier-relative path to check.
            expected_signature_fragment: An optional substring to check against the
                definition header.

        Returns:
            The :class:`VerifyResult` verdict — ``confirmed`` / ``mismatch`` /
            ``not_found`` with the stored truth and any failed expectations.

        Raises:
            SurrealConnectionError: The store's connection is down — propagates
                straight through, never masquerading as a ``not_found`` verdict.
        """
        row = await self._resolver.resolve(qualified_name)
        if row is None:
            return VerifyResult(status=_STATUS_NOT_FOUND)
        summary = self._to_summary(row)
        mismatches: list[VerifyMismatch] = []
        if expected_file_path is not None and not self._file_path_matches(
            expected_file_path, summary.file_path
        ):
            mismatches.append(
                VerifyMismatch(
                    claim=_CLAIM_FILE_PATH,
                    claimed=expected_file_path,
                    actual=summary.file_path,
                )
            )
        if (
            expected_signature_fragment is not None
            and expected_signature_fragment not in summary.header
        ):
            mismatches.append(
                VerifyMismatch(
                    claim=_CLAIM_SIGNATURE,
                    claimed=expected_signature_fragment,
                    actual=summary.header,
                )
            )
        status: Literal["confirmed", "mismatch"] = (
            _STATUS_MISMATCH if mismatches else _STATUS_CONFIRMED
        )
        return VerifyResult(status=status, summary=summary, mismatches=mismatches)

    @classmethod
    def _to_summary(cls, row: dict[str, Any]) -> VerifiedSummary:
        """Map a matched store row into a :class:`VerifiedSummary`.

        Reads only its named keys (tolerating extra, unmodeled row keys) and
        summarises ``source_text`` down to its definition header via
        :meth:`_definition_header` — the on-disk anchor plus the header line(s),
        never the full body.
        """
        return VerifiedSummary(
            qualified_name=row[_IDENTITY_KEY],
            chunk_type=row[_CHUNK_TYPE_KEY],
            tier=row[_TIER_KEY],
            file_path=row[_FILE_PATH_KEY],
            line_start=row[_LINE_START_KEY],
            line_end=row[_LINE_END_KEY],
            header=cls._definition_header(row[_SOURCE_TEXT_KEY]),
        )

    @staticmethod
    def _definition_header(source_text: str) -> str:
        """Return the definition HEADER — decorators + the complete signature.

        Comment- and string-SAFE by construction: the header is the set of
        ``source_text`` lines strictly BEFORE the first body statement, taken from
        the parsed AST rather than a ``:``-terminator text scan (which a trailing
        ``# noqa``/``# type: ignore`` after the colon, or a ``:`` inside a comment on
        the opening line, would defeat — leaking the body into the header or
        truncating the signature). Any decorators precede the ``def``/``class`` line
        and ARE included. A one-line ``def f(): return x`` has nothing strictly
        before its body, so its single def line is kept.

        The chunk is :func:`textwrap.dedent`-ed (method chunks are indented) before
        parsing; line numbers are stable across the dedent, so the header is sliced
        from the ORIGINAL ``source_text`` to preserve its on-disk indentation. If the
        stored chunk does not parse as a single top-level ``def``/``class`` (a
        degenerate row that is never a real symbol chunk), it falls back to the
        legacy ``:``-terminator scan rather than crashing ``verify``.
        """
        try:
            module = ast.parse(textwrap.dedent(source_text))
        except SyntaxError:
            return VerifyTool._header_by_terminator_scan(source_text)
        definition = next(
            (
                node
                for node in module.body
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
            ),
            None,
        )
        if definition is None or not definition.body:
            return VerifyTool._header_by_terminator_scan(source_text)
        # ``definition.lineno`` is the ``def``/``class`` keyword line (decorators
        # carry their own, earlier linenos). ``body[0].lineno`` is the first body
        # statement. The header is every line strictly before the body — UNLESS the
        # body shares the signature's line (a one-liner), where the def line is kept.
        definition_line = definition.lineno
        body_line = definition.body[0].lineno
        header_end = body_line if body_line == definition_line else body_line - 1
        return "\n".join(source_text.splitlines()[:header_end])

    @staticmethod
    def _header_by_terminator_scan(source_text: str) -> str:
        """Legacy ``:``-terminator header scan — the degenerate-chunk fallback only.

        Accumulates physical lines up to and INCLUDING the first whose stripped text
        ends with ``:``; a chunk with no such line falls back to the whole text. Used
        solely when :meth:`_definition_header` cannot parse the chunk as a single
        def/class (never a real symbol chunk), so ``verify`` degrades gracefully.
        """
        header_lines: list[str] = []
        for line in source_text.splitlines():
            header_lines.append(line)
            if line.rstrip().endswith(_HEADER_TERMINATOR):
                return "\n".join(header_lines)
        return "\n".join(header_lines)

    @staticmethod
    def _file_path_matches(claimed: str, actual: str) -> bool:
        """Whether ``claimed`` whole-path-segment-suffix-matches ``actual``.

        Splits both on the path separator and compares their COMMON TAIL: the
        shorter path's segments must equal the other's trailing segments. This
        makes ``loremaster/symbols.py`` match ``loremaster/loremaster/symbols.py``
        (and vice versa) while a mid-segment fragment like ``ymbols.py`` — a
        single segment that is not equal to ``symbols.py`` — does not. Whole
        segments only; never a substring match.
        """
        claimed_segments = list(PurePosixPath(claimed).parts)
        actual_segments = list(PurePosixPath(actual).parts)
        if not claimed_segments or not actual_segments:
            return False
        common_length = min(len(claimed_segments), len(actual_segments))
        return claimed_segments[-common_length:] == actual_segments[-common_length:]
