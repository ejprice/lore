"""Heading-aware Markdown chunker for project documentation.

``MarkdownChunker`` splits a Markdown file along its heading hierarchy (h1-h4),
size-limits oversized sections, and guarantees every emitted chunk fits the
embedder's hard token cap.

It implements the lore :class:`~lorescribe.base.Chunker` protocol and honours
the **Chunk Identity Contract**: every chunk's ``identity`` is its heading path,
repeated identical heading paths are disambiguated with an *occurrence ordinal*,
and a section split into N pieces carries ``sub_ordinal`` ``0..N-1`` — so no two
chunks in a file ever share an ``(identity, sub_ordinal)`` and collide on the
deterministic point-ID loremaster derives downstream.

Design notes (grounded in observed LangChain behaviour, not assumption):

* ``MarkdownHeaderTextSplitter`` both MERGES adjacent sections sharing an
  identical heading path AND rewrites their content — it strips leading
  indentation inside fenced code blocks and appends trailing spaces to prose
  lines. Either behaviour is unacceptable here: the merge collapses two
  legitimately distinct ``## Notes`` sections (the sibling-collapse bug the
  identity contract forbids), and the rewrite corrupts source code. We therefore
  parse the heading hierarchy directly off the *raw* source so section bodies
  are preserved byte-for-byte and same-named sections stay distinct.

* For size limiting we use the Markdown-aware
  ``RecursiveCharacterTextSplitter.from_language("markdown")`` — but only on the
  prose between code fences. A fenced block that fits the size budget is emitted
  whole and never offered to the splitter, so it can never be torn at an
  internal blank line.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext

# Category every Markdown chunk is stamped with; routed downstream by loremaster.
MARKDOWN_CHUNK_TYPE: str = "markdown_section"

# Character size budget per chunk and the overlap between adjacent splits —
# the bake-off-winning configuration carried over from odoo-code's chunker.
MAX_CHUNK_CHARS: int = 4000
CHUNK_OVERLAP: int = 200

# The deepest heading level (h-number) that opens a new section. Headings deeper
# than this stay inside their parent section as ordinary body content.
MAX_HEADING_DEPTH: int = 4

# Separator joining heading-path segments in both the breadcrumb and identity.
HEADING_PATH_SEPARATOR: str = " > "

# Identity / breadcrumb label for content appearing before the first heading.
PREAMBLE_IDENTITY: str = "(preamble)"

# File extensions this chunker claims (matched case-insensitively).
HANDLED_EXTENSIONS: frozenset[str] = frozenset({".md", ".markdown"})

# An ATX heading line: 1-6 leading '#', a space, then heading text.
_HEADING_LINE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")

# A fenced code-block delimiter line (``` or ~~~), optionally indented, with an
# optional info string after the opening fence.
_FENCE_LINE = re.compile(r"^\s*(`{3,}|~{3,})")


class _Section:
    """A heading-scoped slice of the document: its heading path and raw body lines."""

    def __init__(self, heading_path: tuple[str, ...]) -> None:
        self.heading_path: tuple[str, ...] = heading_path
        self.lines: list[str] = []

    @property
    def body(self) -> str:
        """The section body with surrounding blank lines trimmed, content verbatim."""
        return "\n".join(self.lines).strip()


class MarkdownChunker(Chunker):
    """Split Markdown documentation into heading-scoped, size- and token-bounded chunks."""

    def __init__(self) -> None:
        """Build the Markdown-aware size splitter used for oversized prose runs."""
        self._size_splitter = RecursiveCharacterTextSplitter.from_language(
            Language.MARKDOWN,
            chunk_size=MAX_CHUNK_CHARS,
            chunk_overlap=CHUNK_OVERLAP,
        )

    def handles(self, path: str) -> bool:
        """Report whether ``path`` is a Markdown file this chunker claims.

        Args:
            path: Candidate file path. The suffix is matched case-insensitively.

        Returns:
            ``True`` for ``.md`` / ``.markdown`` (any case), else ``False``.
        """
        return PurePosixPath(path).suffix.lower() in HANDLED_EXTENSIONS

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Split ``source`` into heading-scoped, token-bounded chunks.

        Pipeline: parse the raw source into heading-scoped sections (preserving
        content byte-for-byte) -> size-split each section while keeping fenced
        code blocks whole -> sub-split any piece still over the token cap.
        Identities are heading paths with an occurrence ordinal for repeats;
        size/token splits of one section get contiguous ``sub_ordinal`` values.

        Args:
            source: Full Markdown content of the file.
            ctx: Per-file context carrying ``file_path``, the injected
                ``count_tokens`` callable, and the hard ``max_input_tokens`` cap.

        Returns:
            A list of :class:`~lorescribe.models.Chunk`, or ``[]`` for an empty
            or whitespace-only document.
        """
        if not source.strip():
            return []

        sections = self._parse_sections(source)
        # Occurrence ordinal per distinct heading path: the second (and later)
        # appearance of an identical path gets a "#N" suffix so two same-named
        # sections never share an identity.
        occurrences: dict[tuple[str, ...], int] = {}
        chunks: list[Chunk] = []
        for section in sections:
            body = section.body
            if not body:
                continue
            occurrence_index = occurrences.get(section.heading_path, 0)
            occurrences[section.heading_path] = occurrence_index + 1
            identity = self._build_identity(section.heading_path, occurrence_index)
            metadata_header = self._build_header(ctx.file_path, section.heading_path)
            chunks.extend(
                self._emit_section_chunks(
                    body=body,
                    identity=identity,
                    metadata_header=metadata_header,
                    heading_path=section.heading_path,
                    source=source,
                    ctx=ctx,
                )
            )
        return chunks

    def _parse_sections(self, source: str) -> list[_Section]:
        """Walk the raw source line by line, opening a section at each h1-h4 heading.

        Headings inside fenced code blocks are ignored (a ``#`` comment in a
        shell snippet must not start a new documentation section). Content before
        the first heading becomes a preamble section with an empty heading path.
        """
        sections: list[_Section] = []
        current = _Section(())  # preamble: empty heading path
        path_so_far: tuple[str, ...] = ()
        in_fence = False
        fence_marker = ""
        for line in source.splitlines():
            fence = _FENCE_LINE.match(line)
            if fence is not None:
                marker = fence.group(1)
                if not in_fence:
                    in_fence, fence_marker = True, marker[:3]
                elif marker[:3] == fence_marker:
                    in_fence, fence_marker = False, ""
                current.lines.append(line)
                continue
            if not in_fence:
                heading = _HEADING_LINE.match(line)
                if heading is not None and len(heading.group(1)) <= MAX_HEADING_DEPTH:
                    depth = len(heading.group(1))
                    text = heading.group(2).strip()
                    path_so_far = (*path_so_far[: depth - 1], text)
                    if current.lines or current.heading_path:
                        sections.append(current)
                    current = _Section(path_so_far)
                    continue
            current.lines.append(line)
        sections.append(current)
        return sections

    def _render_breadcrumb(self, heading_path: tuple[str, ...]) -> str:
        """Render a heading path as its human-readable breadcrumb label.

        The single source of truth for the ``h1 > h2 > h3`` rendering shared by
        the identity base and the retrieval header; an empty path (preamble)
        renders as :data:`PREAMBLE_IDENTITY` so neither ever carries a blank label.
        """
        return HEADING_PATH_SEPARATOR.join(heading_path) if heading_path else PREAMBLE_IDENTITY

    def _build_identity(self, heading_path: tuple[str, ...], occurrence_index: int) -> str:
        """Compose a section's identity from its heading path and occurrence ordinal.

        The first appearance of a heading path uses the bare path; a repeated
        identical path appends ``"#N"`` (N>=1) so the two never collide.
        """
        base = self._render_breadcrumb(heading_path)
        if occurrence_index == 0:
            return base
        return f"{base}#{occurrence_index}"

    def _build_header(self, file_path: str, heading_path: tuple[str, ...]) -> str:
        """Compose the ``File: <path>\\nSection: <breadcrumb>`` retrieval header."""
        return f"File: {file_path}\nSection: {self._render_breadcrumb(heading_path)}"

    def _emit_section_chunks(
        self,
        *,
        body: str,
        identity: str,
        metadata_header: str,
        heading_path: tuple[str, ...],
        source: str,
        ctx: ChunkContext,
    ) -> list[Chunk]:
        """Size- and token-split one section body into its sibling chunks.

        The body is first split on the char budget with fenced code blocks kept
        whole; each resulting piece is then sub-split further if its *composed*
        embedding text still exceeds ``ctx.max_input_tokens``. Pieces get
        contiguous ``sub_ordinal`` values starting at 0.
        """
        pieces = self._size_split_protecting_fences(body)
        bounded_pieces: list[str] = []
        for piece in pieces:
            bounded_pieces.extend(self._enforce_token_cap(piece, metadata_header, ctx))

        section_path = HEADING_PATH_SEPARATOR.join(heading_path) if heading_path else ""
        chunks: list[Chunk] = []
        for sub_ordinal, piece in enumerate(bounded_pieces):
            line_start, line_end = self._line_range(piece, source)
            chunks.append(
                Chunk(
                    chunk_type=MARKDOWN_CHUNK_TYPE,
                    source_text=piece,
                    identity=identity,
                    sub_ordinal=sub_ordinal,
                    line_start=line_start,
                    line_end=line_end,
                    metadata={
                        "heading_path": section_path,
                        "token_count": ctx.count_tokens(
                            self._compose_embedding_text(metadata_header, piece)
                        ),
                    },
                    metadata_header=metadata_header,
                )
            )
        return chunks

    def _size_split_protecting_fences(self, body: str) -> list[str]:
        """Split ``body`` to the char budget without ever cutting inside a fitting fence.

        The body is partitioned into fenced and non-fenced segments. A fenced
        block that fits the budget is emitted whole (never offered to the char
        splitter); a fenced block larger than the budget is the one case that
        must be divided, and is handed to the splitter like prose. Non-fenced
        prose runs are size-split normally. Adjacent under-budget segments are
        coalesced so a code block and its surrounding prose stay together when
        they jointly fit.
        """
        segments = self._segment_by_fence(body)
        pieces: list[str] = []
        for text, is_fence in segments:
            if is_fence and len(text) <= MAX_CHUNK_CHARS:
                pieces.append(text)
            else:
                pieces.extend(self._size_splitter.split_text(text))
        coalesced = self._coalesce(pieces)
        return coalesced if coalesced else [body]

    def _segment_by_fence(self, body: str) -> list[tuple[str, bool]]:
        """Partition ``body`` into ``(text, is_fenced_code_block)`` segments in order."""
        segments: list[tuple[str, bool]] = []
        buffer: list[str] = []
        fence_buffer: list[str] = []
        in_fence = False
        fence_marker = ""

        def flush(buf: list[str], is_fence: bool) -> None:
            text = "\n".join(buf).strip("\n")
            if text.strip():
                segments.append((text, is_fence))
            buf.clear()

        for line in body.splitlines():
            fence = _FENCE_LINE.match(line)
            if fence is not None:
                marker = fence.group(1)[:3]
                if not in_fence:
                    flush(buffer, False)
                    in_fence, fence_marker = True, marker
                    fence_buffer.append(line)
                elif marker == fence_marker:
                    fence_buffer.append(line)
                    flush(fence_buffer, True)
                    in_fence, fence_marker = False, ""
                else:
                    fence_buffer.append(line)
                continue
            (fence_buffer if in_fence else buffer).append(line)
        # Unterminated fence: treat the trailing buffer as code rather than lose it.
        flush(fence_buffer if in_fence else buffer, in_fence)
        return segments

    def _coalesce(self, pieces: list[str]) -> list[str]:
        """Merge adjacent pieces that jointly fit the char budget, preserving order.

        Keeps a code block glued to its neighbouring prose when the combined size
        is within budget, so small sections are not fragmented into many tiny
        chunks; pieces are never merged past ``MAX_CHUNK_CHARS``.
        """
        merged: list[str] = []
        for piece in pieces:
            if not piece.strip():
                continue
            if merged and len(merged[-1]) + 2 + len(piece) <= MAX_CHUNK_CHARS:
                merged[-1] = f"{merged[-1]}\n\n{piece}"
            else:
                merged.append(piece)
        return merged

    def _enforce_token_cap(
        self, piece: str, metadata_header: str, ctx: ChunkContext
    ) -> list[str]:
        """Sub-split ``piece`` until every part's embedding text fits the token cap.

        The embedder rejects (HTTP 422) over-length inputs, so the cap is a hard
        correctness constraint. It is measured against the *composed* embedding
        text (``metadata_header`` + piece), the exact string the embedder sees.
        An over-cap piece is re-split at a halved character budget and each part
        re-checked; an indivisible piece is returned as-is (degenerate input).
        """
        composed = self._compose_embedding_text(metadata_header, piece)
        if ctx.count_tokens(composed) <= ctx.max_input_tokens:
            return [piece]
        smaller_budget = max(1, len(piece) // 2)
        finer_splitter = RecursiveCharacterTextSplitter.from_language(
            Language.MARKDOWN,
            chunk_size=smaller_budget,
            chunk_overlap=0,
        )
        sub_pieces = finer_splitter.split_text(piece)
        if len(sub_pieces) <= 1:
            return [piece]
        bounded: list[str] = []
        for sub_piece in sub_pieces:
            bounded.extend(self._enforce_token_cap(sub_piece, metadata_header, ctx))
        return bounded

    def _compose_embedding_text(self, metadata_header: str, source_text: str) -> str:
        """Mirror :attr:`Chunk.embedding_text` so the cap is measured on the real input.

        Kept in lockstep with the model's composition rule (header, one newline,
        source) so the token guard sizes exactly the string the embedder sees.
        """
        if not metadata_header:
            return source_text
        return f"{metadata_header}\n{source_text}"

    def _line_range(self, piece: str, source: str) -> tuple[int, int]:
        """Locate a piece's 1-based ``(line_start, line_end)`` within ``source``.

        Anchors on the piece's first non-blank line. Falls back to ``(1, last)``
        when the anchor cannot be located — line numbers are advisory metadata,
        never a primary identity (per the Chunk Identity Contract).
        """
        source_lines = source.splitlines()
        total = len(source_lines) or 1
        anchor = next((line.strip() for line in piece.splitlines() if line.strip()), "")
        if anchor:
            for index, source_line in enumerate(source_lines, start=1):
                if anchor in source_line:
                    span = max(1, piece.count("\n") + 1)
                    return index, min(total, index + span - 1)
        return 1, total
