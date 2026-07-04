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
from pathlib import PurePosixPath
from typing import Any, Final, Literal

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
    """

    def __init__(self, *, store: SurrealStore) -> None:
        self._store = store

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
        exact = await self._find_by_identity(qualified_name)
        if exact is not None:
            return exact
        return await self._find_module_qualified(qualified_name)

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
    """

    def __init__(self, *, store: SurrealStore) -> None:
        self._resolver = SymbolResolver(store=store)

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
                not-found, naming the qualified name.
            SurrealConnectionError: The store's connection is down — propagates
                straight through, never masquerading as a clean not-found.
        """
        row = await self._resolver.resolve(qualified_name)
        if row is not None:
            return self._to_resolved(row)
        raise GetSymbolError(
            f"no Python symbol named {qualified_name!r} is indexed "
            f"(searched chunk types {SYMBOL_CHUNK_TYPES!r}). Next step: try "
            f"search_code({qualified_name!r}) for a semantic match, module-qualify "
            f"the name if it collides across files (e.g. 'pkg.mod.Name'), or run "
            f"reindex() if the file was just added."
        )

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
