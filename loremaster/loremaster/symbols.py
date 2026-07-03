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
Qdrant ``qmodels.Record``/``.payload`` wrapper — so every field this module
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

from pathlib import PurePosixPath
from typing import Any

from pydantic import BaseModel, ConfigDict

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
    """

    model_config = ConfigDict(extra="forbid")

    qualified_name: str
    chunk_type: str
    tier: str
    file_path: str
    line_start: int
    line_end: int
    source: str


class SymbolTool:
    """Resolve a qualified Python name to its exact stored definition + location.

    Args:
        store: The :class:`~loremaster.store.surreal.SurrealStore` holding the
            project's indexed chunks. Injected so the same store (and a real
            client in tests) is reused; the tool owns no store wiring itself.
    """

    def __init__(self, *, store: SurrealStore) -> None:
        self._store = store

    async def get_symbol(self, qualified_name: str) -> ResolvedSymbol:
        """Return the stored definition + location for ``qualified_name``.

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
        genuinely-absent symbol — is a clean not-found, never a wrong-file hit.
        This is purely a lookup-side resolution; nothing is re-indexed.

        Args:
            qualified_name: The symbol's qualified name. Either the bare stored
                identity (``ClassName`` / ``ClassName.method`` / ``function``) or
                a module-qualified dotted name (``pkg.mod.ClassName.method``), with
                or without a repeated package directory in the module path.

        Returns:
            The resolved symbol's exact source and location.

        Raises:
            GetSymbolError: If no Python symbol chunk resolves — a clean
                not-found, naming the qualified name.
            SurrealConnectionError: The store's connection is down — propagates
                straight through, never masquerading as a clean not-found.
        """
        exact = await self._find_by_identity(qualified_name)
        if exact is not None:
            return self._to_resolved(exact)
        module_qualified = await self._find_module_qualified(qualified_name)
        if module_qualified is not None:
            return self._to_resolved(module_qualified)
        raise GetSymbolError(
            f"no Python symbol named {qualified_name!r} is indexed "
            f"(searched chunk types {SYMBOL_CHUNK_TYPES!r}). Next step: try "
            f"search_code({qualified_name!r}) for a semantic match, module-qualify "
            f"the name if it collides across files (e.g. 'pkg.mod.Name'), or run "
            f"reindex() if the file was just added."
        )

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

    async def _find_module_qualified(self, qualified_name: str) -> dict[str, Any] | None:
        """Resolve a MODULE-qualified dotted name to its stored row, or ``None``.

        Splits ``qualified_name`` on dots and, for each candidate identity length
        (the trailing 1 then 2 segments — class/function vs ``Class.method``),
        looks up ALL rows carrying that bare identity and returns the FIRST one
        whose ``file_path`` path-matches the remaining leading module segments.
        Considering every collision sibling (not just the first-scrolled row) is
        what makes a same-named symbol in another module reachable by its own
        fully-qualified name — otherwise only one arbitrary sibling would resolve.
        A name with no module prefix (a single segment, already tried as the exact
        identity) or whose prefix matches no candidate's file is ``None``.

        Args:
            qualified_name: The full dotted name the caller passed.

        Returns:
            The matched row, or ``None`` when nothing resolves.
        """
        segments = qualified_name.split(_DOTTED_SEP)
        for identity_length in range(1, _MAX_IDENTITY_SEGMENTS + 1):
            if identity_length >= len(segments):
                # No leading module segments remain — that is the exact case,
                # already handled by ``_find_by_identity``; nothing module-qualified.
                break
            module_segments = segments[:-identity_length]
            candidate_identity = _DOTTED_SEP.join(segments[-identity_length:])
            for row in await self._find_all_by_identity(candidate_identity):
                if self._module_path_matches(row, module_segments):
                    return row
        return None

    @staticmethod
    def _module_path_matches(row: dict[str, Any], module_segments: list[str]) -> bool:
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
        pure_path = PurePosixPath(file_path)
        file_module_segments = list(pure_path.parts[:-1])
        stem = pure_path.name
        if stem.endswith(_PY_SUFFIX):
            stem = stem[: -len(_PY_SUFFIX)]
        # ``__init__`` is the package itself: ``pkg/__init__.py`` -> module ``pkg``.
        if stem and stem != "__init__":
            file_module_segments.append(stem)
        if not module_segments or not file_module_segments:
            return False
        # Compare the common tail: the shorter path's segments must equal the
        # other's trailing segments. Tolerates an extra/missing repeated leading
        # package directory in either direction without a cross-module wrong hit.
        common_length = min(len(module_segments), len(file_module_segments))
        return module_segments[-common_length:] == file_module_segments[-common_length:]

    @staticmethod
    def _to_resolved(row: dict[str, Any]) -> ResolvedSymbol:
        """Map a matched store row into a :class:`ResolvedSymbol`.

        Reads only its six named keys — the row's FLATTENED shape may carry
        extra, unmodeled keys (a real ``signature``, ``llm_summary``, or a
        future ``metadata`` addition) which are simply ignored, never breaking
        resolution.
        """
        return ResolvedSymbol(
            qualified_name=row[_IDENTITY_KEY],
            chunk_type=row[_CHUNK_TYPE_KEY],
            tier=row[_TIER_KEY],
            file_path=row[_FILE_PATH_KEY],
            line_start=row[_LINE_START_KEY],
            line_end=row[_LINE_END_KEY],
            source=row[_SOURCE_TEXT_KEY],
        )
