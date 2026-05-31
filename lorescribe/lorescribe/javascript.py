"""The generic :class:`JavascriptChunker` and its pluggable ``JsProfile`` hook.

``JavascriptChunker`` is a **domain-agnostic** :class:`~lorescribe.base.Chunker`
for ``.js`` source. The generic core detects only *generic* JavaScript
structure and carries ZERO framework- or product-specific knowledge:

* top-level ``function NAME(...) { ... }`` declarations  -> ``js_function``;
* top-level ``class NAME { ... }`` declarations           -> ``js_class``;
* top-level ``export`` declarations (``export function``/``export class``/
  ``export const NAME``/``export default``) named from the exported symbol
  (an anonymous ``export default`` falls back to a ``js_module`` named from the
  file stem);
* the unstructured remainder (top-level statements belonging to no unit)
  -> ``window#N`` line windows (``chunk_type == "window"``).

The within-file ``identity`` is the declared function/class/export name, or
``window#N`` for an anonymous window — distinct per unit, so sibling chunks
never collapse to one downstream point-ID.

Minified bundles (a ``.min.js`` path, or content whose average line length is so
large it is unmistakably machine-generated) carry no semantic value and would
blow the embedder's token cap, so they are skipped entirely (``[]``).

Every emitted chunk is kept at or below ``ctx.max_input_tokens`` (the embedder
rejects over-length inputs, never truncating). A unit (or window) over the cap
is split into line windows that ALWAYS advance and always emit — a file that is
a single over-cap line still produces a chunk, never an empty list.

A pluggable :data:`JsProfile` rides on top, mirroring the XML chunker's
``SchemaProfile``. A profile is any callable ``__call__(block, ctx) ->
ProfileResult | None``. For each candidate :class:`JsBlock` the chunker consults
every registered profile in order; the first non-``None`` result claims the
block (its ``chunk_type`` replaces the generic one and its ``extra_metadata``
merges over the generic block; ``skip=True`` drops the block entirely),
otherwise the generic default applies. This is the seam a domain-specific
profile (one recognising a particular framework's module/widget conventions)
plugs into in ANOTHER package — the generic core here never imports, encodes, or
even names anything domain-specific.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext, ProfileResult

# A file whose average line length exceeds this is treated as minified. Hand
# written JS averages well under this even with the occasional long array/string
# literal on one line; bundlers, by contrast, emit lines packed to many hundreds
# or thousands of characters. The threshold sits above any plausible hand-written
# average (so a lone 600-char literal line is NOT mistaken for minified — it must
# still be chunked, per the no-wedge invariant) yet well below machine-generated
# density.
MINIFIED_AVG_LINE_LENGTH: int = 800

# Maximum number of source lines a window starts from; windows are then shrunk
# until they fit the token cap.
DEFAULT_WINDOW_LINES: int = 200

# The file extension this chunker claims (compared case-insensitively).
JS_EXTENSION: str = ".js"
MINIFIED_EXTENSION: str = ".min.js"

# Generic block kinds the core detects.
KIND_FUNCTION: str = "function"
KIND_CLASS: str = "class"
KIND_MODULE: str = "module"
KIND_WINDOW: str = "window"

# Generic chunk_type tags, keyed by block kind. A profile may override these.
CHUNK_TYPE_BY_KIND: dict[str, str] = {
    KIND_FUNCTION: "js_function",
    KIND_CLASS: "js_class",
    KIND_MODULE: "js_module",
    KIND_WINDOW: "window",
}

# Top-level (column-0) ``function NAME(`` — incl. ``export``/``export default``/
# ``async`` prefixes. Anchored so nested/inner functions are not mistaken for
# top-level units.
_RE_FUNCTION = re.compile(
    r"""^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s+(\w+)\s*\(""",
)

# Top-level ``class NAME`` — incl. ``export``/``export default`` prefixes.
_RE_CLASS = re.compile(
    r"""^(?:export\s+)?(?:default\s+)?class\s+(\w+)""",
)

# A named ``export const|let|var NAME`` declaration (single-line or block-bodied).
_RE_EXPORT_NAMED = re.compile(
    r"""^export\s+(?:const|let|var)\s+(\w+)\b""",
)

# An anonymous ``export default <expr>`` (no borrowable symbol name).
_RE_EXPORT_DEFAULT_ANON = re.compile(
    r"""^export\s+default\b""",
)


@dataclass(frozen=True)
class JsBlock:
    """A candidate unit of JavaScript handed to a :class:`JsProfile`.

    A block is the granularity at which the chunker consults profiles and emits
    chunks. It is the JS analogue of the XML chunker's ``ElementTree.Element``:
    enough structural context for a domain profile to recognise and claim it.

    Attributes:
        kind: The generic structural kind the core detected — one of
            ``"function"``, ``"class"``, ``"module"``, or ``"window"``.
        name: The declared/derived unit name (function/class/export symbol), or
            ``None`` for an anonymous window block. A profile keys its decision
            off this and/or ``source_text``.
        source_text: The block's own raw source text.
        line_start: First source line (1-based) the block covers.
        line_end: Last source line (1-based) the block covers.
    """

    kind: str
    name: str | None
    source_text: str
    line_start: int
    line_end: int


class JsProfile(Protocol):
    """A per-block hook the :class:`JavascriptChunker` consults to customise a chunk.

    A profile inspects a single :class:`JsBlock` (and the per-file
    :class:`ChunkContext`) and returns a :class:`~lorescribe.models.ProfileResult`
    to claim it — a custom ``chunk_type``, ``extra_metadata`` merged over the
    generic block, and an optional ``skip`` flag — or ``None`` to decline,
    letting the next profile (or the generic default) handle the block.
    """

    def __call__(self, block: JsBlock, ctx: ChunkContext) -> ProfileResult | None:
        """Claim ``block`` with a :class:`ProfileResult`, or decline with ``None``."""
        ...


# A profile may be supplied either as a class implementing the Protocol or as a
# bare function with the same signature; both are accepted.
ProfileCallable = Callable[[JsBlock, ChunkContext], "ProfileResult | None"]


@dataclass
class _DetectedUnit:
    """An internal, mutable record of one detected structural unit.

    Used during scanning before blocks are materialised; ``kind``/``name`` map to
    the generic detection, and the line span is 0-indexed inclusive.
    """

    kind: str
    name: str | None
    start: int
    end: int
    body_lines: list[str] = field(default_factory=list)


class JavascriptChunker(Chunker):
    """Generic, domain-agnostic JavaScript chunker with a profile hook.

    Args:
        profiles: An ordered sequence of :data:`JsProfile` callables. For each
            candidate :class:`JsBlock` the chunker consults them in order and the
            first non-``None`` :class:`ProfileResult` wins. Defaults to no
            profiles (pure generic behaviour).
    """

    def __init__(self, profiles: Sequence[ProfileCallable] | None = None) -> None:
        """Store the registered profiles (empty for pure generic behaviour)."""
        self._profiles: list[ProfileCallable] = list(profiles or [])

    def handles(self, path: str) -> bool:
        """Claim ``.js`` files, case-insensitively.

        Routing is by extension only — whether a given ``.js`` file is minified
        is decided inside :meth:`chunk`, so a ``.min.js`` path is still claimed.
        """
        return path.lower().endswith(JS_EXTENSION)

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Split ``source`` into generic, profile-customised chunks.

        Returns ``[]`` for an empty/whitespace-only file and for a minified file
        (a ``.min.js`` path or content with a very large average line length).
        Otherwise the source is scanned into ordered candidate blocks — detected
        ``function``/``class``/``export`` units interleaved with unstructured
        ``window`` remainders — and each block is emitted (consulting profiles
        first), sub-splitting any block that exceeds the token cap.
        """
        if not source or not source.strip():
            return []
        if self._is_minified(source, ctx.file_path):
            return []

        lines = source.splitlines(keepends=True)
        blocks = self._scan_blocks(lines, ctx)

        chunks: list[Chunk] = []
        for block in blocks:
            chunks.extend(self._emit_block(block, ctx))
        self._assign_sub_ordinals(chunks)
        return chunks

    @staticmethod
    def _assign_sub_ordinals(chunks: list[Chunk]) -> None:
        """Re-stamp ``sub_ordinal`` so chunks sharing an ``identity`` stay distinct.

        Identity invariant (see :mod:`lorescribe.models`): ``(identity,
        sub_ordinal)`` is the within-file natural key, and ``sub_ordinal`` exists
        to disambiguate siblings that legitimately share an ``identity``. Two
        distinct top-level units can collide on identity — duplicate function
        names in a concatenated/legacy non-module script, or multiple anonymous
        ``export default`` units all falling back to the same file stem — and
        their keys would otherwise collapse, silently overwriting one chunk with
        the other downstream.

        This mirrors the XML chunker's pass exactly: the first occurrence of each
        identity keeps ``sub_ordinal == 0`` and each subsequent occurrence
        increments, in emission (source) order. A unit already sub-split into N
        cap-fitting windows emits N consecutive chunks of one identity carrying
        ordinals ``0..N-1``; re-stamping in order reproduces that same sequence,
        so the within-unit ordinals are preserved while cross-unit collisions are
        resolved.
        """
        occurrences: dict[str, int] = {}
        for chunk in chunks:
            ordinal = occurrences.get(chunk.identity, 0)
            chunk.sub_ordinal = ordinal
            occurrences[chunk.identity] = ordinal + 1

    # -- detection ----------------------------------------------------------

    @staticmethod
    def _is_minified(source: str, file_path: str) -> bool:
        """Decide whether ``source`` is a minified bundle to be skipped."""
        if file_path.lower().endswith(MINIFIED_EXTENSION):
            return True
        lines = source.splitlines()
        if not lines:
            return False
        average_line_length = sum(len(line) for line in lines) / len(lines)
        return average_line_length > MINIFIED_AVG_LINE_LENGTH

    def _scan_blocks(self, lines: list[str], ctx: ChunkContext) -> list[JsBlock]:
        """Scan source lines into ordered candidate :class:`JsBlock` units.

        Detected structural units (function/class/export) become their own
        blocks; the unstructured lines between (and around) them are gathered
        into ``window`` blocks so no content is dropped. The result is in source
        order, exactly the order profiles are consulted in.
        """
        units = self._detect_units(lines, ctx)
        blocks: list[JsBlock] = []
        cursor = 0
        window_counter = _WindowCounter()
        for unit in units:
            # Flush any unstructured gap before this structural unit as window(s).
            if unit.start > cursor:
                blocks.extend(
                    self._window_blocks(lines, cursor, unit.start, window_counter)
                )
            blocks.append(
                JsBlock(
                    kind=unit.kind,
                    name=unit.name,
                    source_text="".join(lines[unit.start : unit.end + 1]),
                    line_start=unit.start + 1,
                    line_end=unit.end + 1,
                )
            )
            cursor = unit.end + 1
        # Flush any trailing unstructured remainder.
        if cursor < len(lines):
            blocks.extend(
                self._window_blocks(lines, cursor, len(lines), window_counter)
            )
        return blocks

    def _detect_units(self, lines: list[str], ctx: ChunkContext) -> list[_DetectedUnit]:
        """Locate top-level function/class/export units, in source order."""
        units: list[_DetectedUnit] = []
        index = 0
        total = len(lines)
        while index < total:
            stripped = lines[index].lstrip()
            unit = self._match_unit(lines, index, stripped, ctx)
            if unit is None:
                index += 1
                continue
            units.append(unit)
            index = unit.end + 1
        return units

    def _match_unit(
        self, lines: list[str], index: int, stripped: str, ctx: ChunkContext
    ) -> _DetectedUnit | None:
        """Match a structural unit beginning at ``lines[index]``, or ``None``."""
        function_match = _RE_FUNCTION.match(stripped)
        if function_match:
            end = _scan_braces(lines, index)
            return _DetectedUnit(KIND_FUNCTION, function_match.group(1), index, end)

        class_match = _RE_CLASS.match(stripped)
        if class_match:
            end = _scan_braces(lines, index)
            return _DetectedUnit(KIND_CLASS, class_match.group(1), index, end)

        export_named_match = _RE_EXPORT_NAMED.match(stripped)
        if export_named_match:
            end = _scan_statement_or_braces(lines, index)
            # A named export is treated as a module-level unit named from its
            # symbol — the generic core has no opinion on what kind of value it
            # binds, only that it is a named top-level export.
            return _DetectedUnit(KIND_MODULE, export_named_match.group(1), index, end)

        if _RE_EXPORT_DEFAULT_ANON.match(stripped):
            # Anonymous default export: a module unit with no borrowable name; it
            # is named later from the file stem so its identity is never blank.
            end = _scan_statement_or_braces(lines, index)
            return _DetectedUnit(KIND_MODULE, None, index, end)

        return None

    # -- window splitting ---------------------------------------------------

    def _window_blocks(
        self,
        lines: list[str],
        start: int,
        stop: int,
        window_counter: _WindowCounter,
    ) -> list[JsBlock]:
        """Carve ``lines[start:stop]`` into anonymous ``window`` blocks.

        Pure structural windowing by ``DEFAULT_WINDOW_LINES``; per-window token
        fitting happens at emission time. Blank-only spans contribute nothing.
        Each window gets a distinct ``window#N`` identity. Always advances by at
        least one line, so even a single (long) line yields exactly one window —
        never an empty result for non-blank content.
        """
        blocks: list[JsBlock] = []
        cursor = start
        while cursor < stop:
            end = min(cursor + DEFAULT_WINDOW_LINES, stop)
            segment = lines[cursor:end]
            text = "".join(segment)
            if text.strip():
                window_index = window_counter.next()
                blocks.append(
                    JsBlock(
                        kind=KIND_WINDOW,
                        name=f"window#{window_index}",
                        source_text=text,
                        line_start=cursor + 1,
                        line_end=end,
                    )
                )
            cursor = end
        return blocks

    # -- emission -----------------------------------------------------------

    def _emit_block(self, block: JsBlock, ctx: ChunkContext) -> list[Chunk]:
        """Emit chunk(s) for one block, consulting profiles then sub-splitting.

        The first profile to claim the block supplies its ``chunk_type``,
        ``extra_metadata``, and ``skip`` flag; otherwise the generic default for
        the block's kind applies. A block that fits the token cap becomes a
        single chunk; an over-cap block is split into line windows that share the
        block's identity and always advance. ``sub_ordinal`` is stamped later by
        :meth:`_assign_sub_ordinals` over the whole file.
        """
        chunk_type = CHUNK_TYPE_BY_KIND[block.kind]
        extra_metadata: dict[str, Any] = {}

        result = self._first_profile_result(block, ctx)
        if result is not None:
            if result.skip:
                return []
            chunk_type = result.chunk_type
            extra_metadata = dict(result.extra_metadata)

        identity = self._identity_for(block, ctx)
        return self._emit_sized(
            block=block,
            identity=identity,
            chunk_type=chunk_type,
            extra_metadata=extra_metadata,
            ctx=ctx,
        )

    def _first_profile_result(
        self, block: JsBlock, ctx: ChunkContext
    ) -> ProfileResult | None:
        """Return the first non-``None`` profile result, or ``None`` if all decline."""
        for profile in self._profiles:
            result = profile(block, ctx)
            if result is not None:
                return result
        return None

    def _identity_for(self, block: JsBlock, ctx: ChunkContext) -> str:
        """Resolve a non-blank within-file identity for ``block``.

        A named unit uses its declared name; an anonymous module unit (e.g.
        ``export default {...}``) falls back to the file stem so its identity is
        never blank or a misleading ``window#N``. Window blocks already carry a
        ``window#N`` name.
        """
        if block.name is not None:
            return block.name
        return self._file_stem(ctx.file_path) or KIND_MODULE

    @staticmethod
    def _file_stem(file_path: str) -> str:
        """Return the file name without its directory or ``.js`` extension."""
        stem = file_path.rsplit("/", 1)[-1]
        if stem.lower().endswith(JS_EXTENSION):
            stem = stem[: -len(JS_EXTENSION)]
        return stem

    def _emit_sized(
        self,
        *,
        block: JsBlock,
        identity: str,
        chunk_type: str,
        extra_metadata: dict[str, Any],
        ctx: ChunkContext,
    ) -> list[Chunk]:
        """Emit one chunk for a block, sub-splitting it if it exceeds the cap."""
        text = block.source_text
        if ctx.count_tokens(text) <= ctx.max_input_tokens:
            # ``sub_ordinal`` is left at the model default and stamped by the
            # single ``_assign_sub_ordinals`` pass once the whole file is emitted.
            return [
                Chunk(
                    chunk_type=chunk_type,
                    source_text=text,
                    identity=identity,
                    line_start=block.line_start,
                    line_end=block.line_end,
                    metadata=dict(extra_metadata),
                )
            ]
        # Over the cap: split into windows that share this identity (the global
        # ``_assign_sub_ordinals`` pass keeps their keys distinct). Always
        # advances by at least one line, so a single over-cap line still emits.
        return self._sub_split(
            block=block,
            identity=identity,
            chunk_type=chunk_type,
            extra_metadata=extra_metadata,
            ctx=ctx,
        )

    def _sub_split(
        self,
        *,
        block: JsBlock,
        identity: str,
        chunk_type: str,
        extra_metadata: dict[str, Any],
        ctx: ChunkContext,
    ) -> list[Chunk]:
        """Split an over-cap block into cap-fitting, always-advancing windows.

        Windows share ``identity``; their ``sub_ordinal`` is left at the model
        default here and stamped authoritatively by the single
        :meth:`_assign_sub_ordinals` pass over the whole file, so the windows of
        one over-cap unit and any same-named sibling unit all stay distinct. The
        window end always advances by at least one line; a single line longer
        than the cap is emitted alone (the finest the line-granular splitter can
        do without mangling a token), guaranteeing the loop terminates and at
        least one chunk is produced.
        """
        unit_lines = block.source_text.splitlines(keepends=True)
        offset = block.line_start - 1
        chunks: list[Chunk] = []
        start = 0
        total = len(unit_lines)
        while start < total:
            end = self._fit_window_end(unit_lines, start, ctx)
            window_text = "".join(unit_lines[start:end])
            chunks.append(
                Chunk(
                    chunk_type=chunk_type,
                    source_text=window_text,
                    identity=identity,
                    line_start=offset + start + 1,
                    line_end=offset + end,
                    metadata=dict(extra_metadata),
                )
            )
            start = end
        return chunks

    @staticmethod
    def _fit_window_end(unit_lines: list[str], start: int, ctx: ChunkContext) -> int:
        """Return the exclusive end index for a window beginning at ``start``.

        Grows up to ``DEFAULT_WINDOW_LINES`` lines, then shrinks until the window
        text fits the token cap. Always advances by at least one line so a single
        over-cap line cannot wedge the loop (it is emitted alone).
        """
        total = len(unit_lines)
        end = min(start + DEFAULT_WINDOW_LINES, total)
        while end > start + 1:
            text = "".join(unit_lines[start:end])
            if ctx.count_tokens(text) <= ctx.max_input_tokens:
                break
            end -= 1
        return end


class _WindowCounter:
    """Monotonic 0-based counter handing out distinct window ordinals."""

    def __init__(self) -> None:
        self._value = -1

    def next(self) -> int:
        self._value += 1
        return self._value


def _scan_braces(lines: list[str], start: int) -> int:
    """Return the 0-indexed line on which the brace opened at/after ``start`` closes.

    Counts ``{``/``}`` from ``start`` forward. String literals containing braces
    are not parsed (good enough for the generic structural split). If the block
    never closes, returns the last line index so the remainder of the file is
    captured rather than dropped.
    """
    depth = 0
    found_open = False
    for line_index in range(start, len(lines)):
        for character in lines[line_index]:
            if character == "{":
                depth += 1
                found_open = True
            elif character == "}":
                depth -= 1
        if found_open and depth <= 0:
            return line_index
    return len(lines) - 1


def _scan_statement_or_braces(lines: list[str], start: int) -> int:
    """Return the 0-indexed end line for an export unit.

    If the unit opens a brace block (``export default {`` / ``export const x =
    {``), the end is the matching closing brace. Otherwise the unit is a single
    statement ending at the first line carrying a terminating ``;`` (falling back
    to the start line). Keeps the generic split robust for both block-bodied and
    one-line exports without parsing JS.
    """
    if "{" in lines[start]:
        return _scan_braces(lines, start)
    for line_index in range(start, len(lines)):
        if ";" in lines[line_index]:
            return line_index
    return start
