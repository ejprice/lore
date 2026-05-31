"""Plain-text fallback chunker for ``.txt`` and ``.rst`` files.

Uses ``RecursiveCharacterTextSplitter`` (langchain) to window the source into
token-bounded chunks.  Each window is identified as ``window#N`` with a
matching ``sub_ordinal`` so downstream point-ID derivation stays deterministic
and collision-free.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from langchain_text_splitters import RecursiveCharacterTextSplitter

from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext

_CLAIMED_EXTENSIONS: frozenset[str] = frozenset({".txt", ".rst"})

# ``RecursiveCharacterTextSplitter`` works in characters.  We need chunks that
# fit within ``ctx.max_input_tokens``.  The real token counter is injected via
# the context, so we size windows conservatively using a 4-chars-per-token
# heuristic for the splitter's character budget, then re-check each window
# against the real counter and split further if necessary.
_CHARS_PER_TOKEN_ESTIMATE: int = 4


class TextChunker(Chunker):
    """Generic plain-text chunker for ``.txt`` and ``.rst`` files.

    Splits the source text into windows using
    ``RecursiveCharacterTextSplitter``, keeping every window at or below the
    embedder's ``max_input_tokens`` cap as measured by the injected token
    counter.  Empty or whitespace-only sources produce an empty list.
    """

    def handles(self, path: str) -> bool:
        """Return ``True`` for ``.txt`` and ``.rst`` extensions (case-insensitive).

        Args:
            path: File path or extension string to test.

        Returns:
            ``True`` if the path ends in ``.txt`` or ``.rst``.
        """
        extension = PurePosixPath(path).suffix.lower()
        return extension in _CLAIMED_EXTENSIONS

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Split ``source`` into token-bounded windows.

        Each window is identified as ``window#N`` (N = 0-based index) with a
        matching ``sub_ordinal``.  The injected ``ctx.count_tokens`` is used as
        the authoritative size measurement so every emitted chunk stays within
        ``ctx.max_input_tokens``.

        Args:
            source: Full file content.
            ctx: Per-file context with slug, file path, token counter, and cap.

        Returns:
            A list of :class:`~lorescribe.models.Chunk` objects, or ``[]``
            when ``source`` is empty or whitespace-only.
        """
        if not source or not source.strip():
            return []

        # Derive a character budget from the token cap.  We use the
        # conservative 4-chars-per-token heuristic for the splitter; a
        # second pass below trims any window that the real counter still
        # finds over-length.
        char_budget = ctx.max_input_tokens * _CHARS_PER_TOKEN_ESTIMATE

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=char_budget,
            chunk_overlap=0,
            length_function=len,
        )
        raw_windows: list[str] = splitter.split_text(source)

        # Second pass: any window the injected counter still considers over
        # budget gets split again at the character level.
        windows: list[str] = []
        for raw in raw_windows:
            windows.extend(self._fit_to_cap(raw, ctx))

        # Filter degenerate (empty / whitespace-only) windows that the
        # splitter may emit on pathological inputs.
        windows = [w for w in windows if w.strip()]

        chunks: list[Chunk] = []
        source_lines = source.splitlines(keepends=True)

        # Track a cumulative search offset so repeated-content windows resolve to
        # their OWN occurrence in the source, not always the first. Windows are
        # emitted in document order with no overlap, so each window's match must
        # start at or after the previous window's end.
        search_from = 0
        for ordinal, window_text in enumerate(windows):
            line_start, line_end, match_end = _locate_lines(
                window_text, source_lines, source, search_from
            )
            search_from = match_end
            chunks.append(
                Chunk(
                    chunk_type="text",
                    source_text=window_text,
                    identity=f"window#{ordinal}",
                    sub_ordinal=ordinal,
                    line_start=line_start,
                    line_end=line_end,
                )
            )

        return chunks

    def _fit_to_cap(self, text: str, ctx: ChunkContext) -> list[str]:
        """Split ``text`` into sub-windows that each fit within the token cap.

        Uses the injected ``ctx.count_tokens`` as the authoritative measure.
        If ``text`` is already within ``ctx.max_input_tokens``, it is returned
        as-is.  Otherwise it is bisected recursively until every piece fits.

        Args:
            text: Text to fit.
            ctx: Context supplying the counter and cap.

        Returns:
            A list of one or more strings, each ≤ ``ctx.max_input_tokens``
            tokens as measured by ``ctx.count_tokens`` — except an irreducible
            single character that still exceeds the cap, which is emitted as-is
            rather than recursed on forever.
        """
        if ctx.count_tokens(text) <= ctx.max_input_tokens:
            return [text]

        # A single character that still exceeds the cap is irreducible: bisecting
        # it yields ("", text) and would recurse on the same input forever. Emit
        # it as-is — the embedder will reject it, but the chunker must not hang.
        if len(text) <= 1:
            return [text]

        # Bisect by character count until every piece fits.
        mid = len(text) // 2
        left = text[:mid]
        right = text[mid:]
        result: list[str] = []
        if left:
            result.extend(self._fit_to_cap(left, ctx))
        if right:
            result.extend(self._fit_to_cap(right, ctx))
        return result


def _locate_lines(
    window_text: str,
    source_lines: list[str],
    source: str,
    search_from: int = 0,
) -> tuple[int, int, int]:
    """Return the 1-based line span for ``window_text`` and the match end offset.

    Finds the occurrence of ``window_text`` at or after ``search_from`` and
    converts the character offsets to line numbers. Threading ``search_from``
    forward across windows means repeated/identical content resolves to its own
    occurrence rather than always the first — without it, every duplicate window
    would report line ``(1, 1)``. Falls back to ``(1, 1, search_from)`` if the
    text is not found (shouldn't happen in practice).

    Args:
        window_text: The window whose span to locate.
        source_lines: ``source.splitlines(keepends=True)`` — precomputed for
            efficiency when processing many windows.
        source: The original full source string.
        search_from: Character offset to begin searching from. The caller
            advances this past each located window so the next search skips
            already-consumed content.

    Returns:
        A ``(line_start, line_end, match_end_char)`` tuple. ``line_start`` and
        ``line_end`` are both 1-based and ≥ 1; ``match_end_char`` is the
        character offset just past the located window (or ``search_from`` on a
        miss), suitable to pass back as the next ``search_from``.
    """
    start_char = source.find(window_text, search_from)
    if start_char == -1:
        return 1, 1, search_from
    end_char = start_char + len(window_text) - 1

    line_start = 1
    line_end = 1
    cumulative = 0
    for line_number, line in enumerate(source_lines, start=1):
        line_end_char = cumulative + len(line) - 1
        if cumulative <= start_char <= line_end_char:
            line_start = line_number
        if cumulative <= end_char <= line_end_char:
            line_end = line_number
            break
        cumulative += len(line)

    return max(1, line_start), max(1, line_end), end_char + 1
