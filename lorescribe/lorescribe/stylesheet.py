"""CSS/SCSS stylesheet chunker for lorescribe.

Uses overlapping sliding-line windows (~200 lines, ~40 overlap).
Skips minified files: either the filename contains ``.min.css`` OR the
source's average line length exceeds ``MINIFIED_AVG_LINE_LEN``.

Each window is emitted as a :class:`~lorescribe.models.Chunk` with:

* ``chunk_type="stylesheet"``
* ``identity="window#N"`` — sequential, distinct, starting from 0.
* ``sub_ordinal=0`` — each window has a unique identity; no siblings.
* ``line_start`` / ``line_end`` — 1-based line numbers for the window.

Every emitted chunk is kept at or below ``ctx.max_input_tokens`` as
measured by ``ctx.count_tokens``. If the default window size would
produce an over-length chunk, the window is shrunk line-by-line until
it fits.
"""

from __future__ import annotations

import logging
from pathlib import PurePosixPath

from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext

logger = logging.getLogger(__name__)

# Target lines per sliding window.
WINDOW_SIZE: int = 200

# Overlap lines between adjacent windows.
OVERLAP: int = 40

# Stride between window start positions.
STEP: int = WINDOW_SIZE - OVERLAP  # 160

# Average characters per line above which a file is considered minified.
MINIFIED_AVG_LINE_LEN: int = 200

# Extensions this chunker claims (stored normalised / lowercase).
_CLAIMED_EXTENSIONS: frozenset[str] = frozenset({".css", ".scss"})


def _is_minified_by_content(source: str) -> bool:
    """Return ``True`` if the source's average line length exceeds the threshold."""
    lines = source.splitlines()
    if not lines:
        return False
    avg_len = sum(len(line) for line in lines) / len(lines)
    return avg_len > MINIFIED_AVG_LINE_LEN


def _is_minified_by_filename(file_path: str) -> bool:
    """Return ``True`` if the file path indicates a minified file.

    Matches ``.min.css`` (case-insensitive) by checking whether the
    lowercased basename ends with ``.min.css``.
    """
    name = PurePosixPath(file_path).name.lower()
    return name.endswith(".min.css")


class StylesheetChunker(Chunker):
    """Chunker for CSS and SCSS source files.

    Splits stylesheet source into overlapping sliding-line windows
    (~200 lines, ~40 overlap). Skips minified files.
    """

    def handles(self, path: str) -> bool:
        """Return ``True`` for ``.css`` and ``.scss`` files (case-insensitive).

        Args:
            path: The on-disk path of a candidate file.

        Returns:
            ``True`` when the path's extension (lowercased) is ``.css``
            or ``.scss``; ``False`` otherwise.
        """
        extension = PurePosixPath(path).suffix.lower()
        return extension in _CLAIMED_EXTENSIONS

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Split a stylesheet source into overlapping window chunks.

        Skips:

        * Empty / whitespace-only source.
        * Files whose path ends in ``.min.css``.
        * Files whose content is minified (avg line length > threshold).

        Args:
            source: Full text of the CSS/SCSS file.
            ctx: Per-file context (slug, file path, token counter, cap).

        Returns:
            A list of :class:`~lorescribe.models.Chunk` objects with
            ``chunk_type="stylesheet"`` and sequential ``window#N``
            identities.  Returns ``[]`` for skipped files.
        """
        # --- skip: empty / whitespace-only
        if not source or not source.strip():
            return []

        # --- skip: minified filename
        if _is_minified_by_filename(ctx.file_path):
            return []

        # --- skip: minified content
        if _is_minified_by_content(source):
            return []

        lines = source.splitlines(keepends=True)
        total_lines = len(lines)
        chunks: list[Chunk] = []
        window_index = 0
        start = 0  # 0-based index into ``lines``

        while start < total_lines:
            end = min(start + WINDOW_SIZE, total_lines)  # exclusive upper bound

            # Shrink the window if it would exceed the token cap.
            window_end = end
            window_text: str | None = None
            while window_end > start:
                candidate = "".join(lines[start:window_end])
                if ctx.count_tokens(candidate) <= ctx.max_input_tokens:
                    window_text = candidate
                    break
                window_end -= 1

            if window_text is None:
                # Even a single line exceeds the cap — skip this window to
                # avoid emitting an un-embeddable chunk.
                logger.warning(
                    "stylesheet window starting at line %d exceeds token cap %d; skipping",
                    start + 1,
                    ctx.max_input_tokens,
                )
                if end >= total_lines:
                    break
                start += STEP
                continue

            line_start = start + 1          # convert 0-based to 1-based
            line_end = window_end           # already 1-based (exclusive → inclusive)

            chunks.append(
                Chunk(
                    chunk_type="stylesheet",
                    source_text=window_text,
                    identity=f"window#{window_index}",
                    sub_ordinal=0,
                    line_start=line_start,
                    line_end=line_end,
                )
            )
            window_index += 1

            if end >= total_lines:
                break
            start += STEP

        return chunks
