"""AST-based Python chunker for the lorescribe ingestion pipeline.

:class:`PythonAstChunker` parses a Python source string with the stdlib
``ast`` module and emits one :class:`~lorescribe.models.Chunk` per semantic
unit: a single ``imports`` chunk, one ``class`` chunk per top-level class, one
``method`` chunk per method (including methods defined inside control flow such
as ``if``/``else`` or ``try`` blocks within a class body), and one
``function`` chunk per top-level function.

Three invariants make this a *correctness* component rather than a best-effort
splitter:

* **Identity uniqueness** within ``(file, chunk_type)``. The natural identity
  is the function name, ``ClassName``, ``ClassName.method``, or the literal
  ``"imports"``. A genuine duplicate within the same ``(file, chunk_type)`` —
  a redefined top-level function, or two same-named methods reached via a
  conditional ``def`` — collides downstream into one point-ID, so every
  collision after the first gets a ``#N`` disambiguator (``"f"``, ``"f#1"``,
  ``"f#2"`` …) in source order.

* **Syntax-error fallback.** Unparseable source cannot be walked, so the
  chunker degrades to fixed-size sliding *line* windows with a small overlap,
  ``chunk_type == "python_window"`` and ``identity == "window#N"``.

* **Oversize guard.** No emitted chunk's ``embedding_text`` (the composed
  ``metadata_header + "\\n" + source_text``) may exceed
  ``ctx.max_input_tokens`` as measured by ``ctx.count_tokens`` — the embedder
  rejects (never truncates) over-length inputs. A unit whose composed
  embedding_text exceeds the cap is sub-split into ``sub_ordinal``-stamped
  pieces, each whose COMPOSED embedding_text is at or below the cap.
"""

from __future__ import annotations

import ast
import warnings
from pathlib import PurePosixPath

from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext

# The file extension this chunker claims (lower-cased for case-insensitive
# matching, mirroring the registry's normalisation).
PYTHON_EXTENSION: str = ".py"

# Chunk-type tags this chunker stamps.
CHUNK_TYPE_IMPORTS: str = "imports"
CHUNK_TYPE_CLASS: str = "class"
CHUNK_TYPE_METHOD: str = "method"
CHUNK_TYPE_FUNCTION: str = "function"
CHUNK_TYPE_WINDOW: str = "python_window"

# The fixed identity for the sole imports chunk.
IMPORTS_IDENTITY: str = CHUNK_TYPE_IMPORTS

# Syntax-error fallback window geometry, in lines. A window is at most
# ``FALLBACK_WINDOW_LINES`` lines; consecutive windows overlap by
# ``FALLBACK_OVERLAP_LINES`` so a unit straddling a boundary is not lost.
FALLBACK_WINDOW_LINES: int = 200
FALLBACK_OVERLAP_LINES: int = 20

# Separator joining disambiguated identities: ``name#1``, ``name#2`` ...
IDENTITY_DISAMBIGUATOR: str = "#"


class _IdentityAllocator:
    """Hands out collision-free identities scoped to a ``(file, chunk_type)``.

    The first request for a given ``(chunk_type, base_identity)`` returns the
    bare base; each subsequent request appends ``#1``, ``#2`` … in call order.
    Scoping by ``chunk_type`` is deliberate: a ``method`` named ``start`` and a
    ``function`` named ``start`` share a bare name but live in different
    ``chunk_type`` buckets, so neither needs a disambiguator.
    """

    def __init__(self) -> None:
        """Initialise with no identities seen."""
        # Maps (chunk_type, base_identity) -> count of times already allocated.
        self._seen: dict[tuple[str, str], int] = {}

    def allocate(self, chunk_type: str, base_identity: str) -> str:
        """Return a unique identity for ``base_identity`` within ``chunk_type``.

        Args:
            chunk_type: The chunk category the identity is scoped to.
            base_identity: The natural identity (function name, ``ClassName``,
                ``ClassName.method``, ...).

        Returns:
            ``base_identity`` on first use; ``f"{base_identity}#{n}"`` for the
            ``n``-th collision (``n`` counting from 1) thereafter.
        """
        key = (chunk_type, base_identity)
        count = self._seen.get(key, 0)
        self._seen[key] = count + 1
        if count == 0:
            return base_identity
        return f"{base_identity}{IDENTITY_DISAMBIGUATOR}{count}"


class PythonAstChunker(Chunker):
    """Splits Python source into AST-derived, embedder-sized chunks."""

    def handles(self, path: str) -> bool:
        """Report whether ``path`` is a Python source file.

        Matching is on the ``.py`` extension and case-insensitive (``.PY`` is a
        Python file); ``.pyc`` / ``.pyi`` and extension-less paths are not
        claimed.

        Args:
            path: The candidate file path.

        Returns:
            ``True`` iff the path's extension is ``.py`` (any case).
        """
        return PurePosixPath(path).suffix.lower() == PYTHON_EXTENSION

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Split ``source`` into chunks, honouring the oversize cap.

        On a clean parse, emits the imports / class / method / function chunk
        set. On :class:`SyntaxError`, degrades to sliding-window chunks. Every
        returned chunk's ``embedding_text`` (composed header + source) is at or
        below ``ctx.max_input_tokens``.

        Args:
            source: The full Python source text.
            ctx: Per-file context carrying the slug, file path, injected token
                counter, and the embedder's hard token cap.

        Returns:
            The emitted chunks; ``[]`` for an empty / whitespace-only source.
        """
        if not source.strip():
            return []

        try:
            # SyntaxWarning (e.g. invalid escape sequences) is not a parse
            # failure — suppress it so it does not pollute the caller's stream.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast.parse(source)
        except SyntaxError:
            return self._chunk_fallback(source, ctx)

        lines = source.splitlines(keepends=True)
        allocator = _IdentityAllocator()
        chunks: list[Chunk] = []

        chunks.extend(self._build_imports_chunk(tree, lines, source, ctx, allocator))

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                chunks.extend(self._chunk_class(node, lines, ctx, allocator))
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                chunks.extend(
                    self._chunk_function_like(
                        node,
                        lines,
                        ctx,
                        allocator,
                        chunk_type=CHUNK_TYPE_FUNCTION,
                        base_identity=node.name,
                        class_name=None,
                        inherits=[],
                    )
                )

        return chunks

    # -- Imports ----------------------------------------------------------

    def _build_imports_chunk(
        self,
        tree: ast.Module,
        lines: list[str],
        source: str,
        ctx: ChunkContext,
        allocator: _IdentityAllocator,
    ) -> list[Chunk]:
        """Build the single module-level imports chunk, if any imports exist.

        Returns an empty list when the module has no top-level imports, so a
        no-imports file never carries a blank imports chunk.
        """
        import_nodes = [
            node
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
        ]
        if not import_nodes:
            return []

        line_start = min(node.lineno for node in import_nodes)
        line_end = max(node.end_lineno or node.lineno for node in import_nodes)
        import_source = "".join(lines[line_start - 1 : line_end])
        header = self._build_metadata_header(ctx, CHUNK_TYPE_IMPORTS)
        identity = allocator.allocate(CHUNK_TYPE_IMPORTS, IMPORTS_IDENTITY)
        metadata: dict[str, object] = {
            "class_name": None,
            "method_name": None,
            "inherits": [],
            "decorators": [],
        }
        return self._emit_sized(
            chunk_type=CHUNK_TYPE_IMPORTS,
            identity=identity,
            source_text=import_source,
            line_start=line_start,
            line_end=line_end,
            metadata=metadata,
            metadata_header=header,
            ctx=ctx,
        )

    # -- Classes & methods ------------------------------------------------

    def _chunk_class(
        self,
        class_node: ast.ClassDef,
        lines: list[str],
        ctx: ChunkContext,
        allocator: _IdentityAllocator,
    ) -> list[Chunk]:
        """Emit a ``class`` header chunk plus a ``method`` chunk per method.

        Methods are discovered by descending through the class body, including
        those nested inside control-flow blocks (``if``/``else``, ``try``,
        ``with``), so a conditionally-defined method is not lost.
        """
        inherits = [base.id for base in class_node.bases if isinstance(base, ast.Name)]
        decorators = self._decorator_names(class_node)
        class_name = class_node.name

        chunks: list[Chunk] = []

        # Walk the class body once: the method list both bounds the header (it
        # ends just before the first method) and drives the per-method chunks.
        methods = self._iter_methods(class_node)

        # Class header: the class line through the line before its first method
        # (or the whole class when it has no methods), trimmed of trailing blanks.
        header_start = class_node.lineno
        if methods:
            header_end = self._definition_start_line(methods[0]) - 1
        else:
            header_end = class_node.end_lineno or class_node.lineno
        if header_end < header_start:
            header_end = header_start
        while header_end > header_start and lines[header_end - 1].strip() == "":
            header_end -= 1

        header_source = "".join(lines[header_start - 1 : header_end])
        class_identity = allocator.allocate(CHUNK_TYPE_CLASS, class_name)
        chunks.extend(
            self._emit_sized(
                chunk_type=CHUNK_TYPE_CLASS,
                identity=class_identity,
                source_text=header_source,
                line_start=header_start,
                line_end=header_end,
                metadata={
                    "class_name": class_name,
                    "method_name": None,
                    "inherits": inherits,
                    "decorators": decorators,
                },
                metadata_header=self._build_metadata_header(
                    ctx, CHUNK_TYPE_CLASS, class_name=class_name
                ),
                ctx=ctx,
            )
        )

        for method_node in methods:
            chunks.extend(
                self._chunk_function_like(
                    method_node,
                    lines,
                    ctx,
                    allocator,
                    chunk_type=CHUNK_TYPE_METHOD,
                    base_identity=f"{class_name}.{method_node.name}",
                    class_name=class_name,
                    inherits=inherits,
                )
            )

        return chunks

    @staticmethod
    def _iter_methods(
        class_node: ast.ClassDef,
    ) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
        """Return the class's methods in source order, descending into control flow.

        A method may be a direct child of the class body or nested inside an
        ``if``/``else``, ``try``, or ``with`` block (conditional definitions).
        Nested classes are NOT descended into — their methods belong to the
        nested class, not this one.
        """
        methods: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

        def visit(body: list[ast.stmt]) -> None:
            for stmt in body:
                if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
                    methods.append(stmt)
                elif isinstance(stmt, ast.If):
                    visit(stmt.body)
                    visit(stmt.orelse)
                elif isinstance(stmt, ast.Try):
                    visit(stmt.body)
                    for handler in stmt.handlers:
                        visit(handler.body)
                    visit(stmt.orelse)
                    visit(stmt.finalbody)
                elif isinstance(stmt, ast.With | ast.AsyncWith):
                    visit(stmt.body)
                # ast.ClassDef is intentionally skipped: nested-class methods
                # are not this class's methods.

        visit(class_node.body)
        # Source order: control-flow recursion can interleave; sort by line.
        methods.sort(key=lambda node: node.lineno)
        return methods

    # -- Functions / methods (shared) -------------------------------------

    def _chunk_function_like(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        lines: list[str],
        ctx: ChunkContext,
        allocator: _IdentityAllocator,
        *,
        chunk_type: str,
        base_identity: str,
        class_name: str | None,
        inherits: list[str],
    ) -> list[Chunk]:
        """Emit chunk(s) for one function or method, sub-splitting if oversize."""
        decorators = self._decorator_names(node)
        line_start = self._definition_start_line(node)
        line_end = node.end_lineno or node.lineno
        unit_source = "".join(lines[line_start - 1 : line_end])
        identity = allocator.allocate(chunk_type, base_identity)
        header = self._build_metadata_header(
            ctx, chunk_type, class_name=class_name, method_name=node.name
        )
        metadata: dict[str, object] = {
            "class_name": class_name,
            "method_name": node.name,
            "inherits": inherits,
            "decorators": decorators,
        }
        return self._emit_sized(
            chunk_type=chunk_type,
            identity=identity,
            source_text=unit_source,
            line_start=line_start,
            line_end=line_end,
            metadata=metadata,
            metadata_header=header,
            ctx=ctx,
        )

    # -- Sizing / oversize guard ------------------------------------------

    @staticmethod
    def _compose_embedding_text(metadata_header: str, source_text: str) -> str:
        """Mirror :attr:`Chunk.embedding_text` so the cap is measured on the real embedder input.

        Kept in lockstep with the model's composition rule (header, one newline,
        source) so the token guard sizes exactly the string the embedder sees.
        When the header is empty, returns the bare source (no leading newline).

        This is the same composition rule as :meth:`MarkdownChunker._compose_embedding_text`.
        """
        if not metadata_header:
            return source_text
        return f"{metadata_header}\n{source_text}"

    def _emit_sized(
        self,
        *,
        chunk_type: str,
        identity: str,
        source_text: str,
        line_start: int,
        line_end: int,
        metadata: dict[str, object],
        metadata_header: str,
        ctx: ChunkContext,
    ) -> list[Chunk]:
        """Emit one chunk, or several ``sub_ordinal``-stamped pieces if oversize.

        The cap is measured against the COMPOSED embedding_text
        (``metadata_header + "\\n" + source_text``) — the exact string the
        embedder sees — not against ``source_text`` alone. This mirrors the
        markdown chunker's ``_enforce_token_cap`` and prevents header tokens
        from pushing an at-cap source over the embedder's hard limit.

        A unit whose composed text exceeds ``ctx.max_input_tokens`` is split on
        line boundaries into consecutive pieces, each whose composed text is at
        or below the cap, all sharing ``identity`` and carrying ``sub_ordinal``
        0, 1, 2, …. Line numbers on each piece reflect the slice it covers.
        """
        # Guard on the COMPOSED text (header + "\n" + source), not source alone.
        composed = self._compose_embedding_text(metadata_header, source_text)
        if ctx.count_tokens(composed) <= ctx.max_input_tokens:
            return [
                Chunk(
                    chunk_type=chunk_type,
                    source_text=source_text,
                    identity=identity,
                    sub_ordinal=0,
                    line_start=line_start,
                    line_end=line_end,
                    metadata=dict(metadata),
                    metadata_header=metadata_header,
                )
            ]

        pieces = self._split_to_cap(source_text, metadata_header, ctx)
        chunks: list[Chunk] = []
        current_line = line_start
        for sub_ordinal, piece_text in enumerate(pieces):
            # Clamp the cursor to the unit's true span: char-slicing a single
            # over-cap physical line yields many fragments with no embedded
            # newline, and advancing the cursor once per fragment would walk
            # ``line_start`` past ``line_end``. Every fragment of that final
            # line must keep reporting that line, not a fabricated later one.
            piece_start = min(current_line, line_end)
            piece_line_count = piece_text.count("\n") or 1
            piece_end = min(piece_start + piece_line_count - 1, line_end)
            chunks.append(
                Chunk(
                    chunk_type=chunk_type,
                    source_text=piece_text,
                    identity=identity,
                    sub_ordinal=sub_ordinal,
                    line_start=piece_start,
                    line_end=piece_end,
                    metadata=dict(metadata),
                    metadata_header=metadata_header,
                )
            )
            current_line = piece_end + 1
        return chunks

    @staticmethod
    def _split_to_cap(
        source_text: str, metadata_header: str, ctx: ChunkContext
    ) -> list[str]:
        """Split ``source_text`` on line boundaries so each piece's COMPOSED embedding_text fits.

        The cap is checked against ``metadata_header + "\\n" + piece`` (the
        actual embedder input), not against ``piece`` alone. This ensures the
        header's token overhead is subtracted from each piece's source budget.

        Greedy: accumulate whole lines until adding the next would push the
        composed text over the cap, then start a new piece. A single line whose
        composed text alone exceeds the cap is character-sliced via
        :meth:`_char_slice` (last resort — still header-aware).

        Edge case (mirror markdown's degenerate handling): if the header alone
        is at or above the cap, emit the smallest reasonable piece per line and
        move on — do not infinite-loop or crash.
        """
        raw_lines = source_text.splitlines(keepends=True)
        pieces: list[str] = []
        current = ""
        for line in raw_lines:
            candidate = current + line
            # Check composed size of the candidate accumulation.
            composed_candidate = PythonAstChunker._compose_embedding_text(
                metadata_header, candidate
            )
            if current and ctx.count_tokens(composed_candidate) > ctx.max_input_tokens:
                # Current accumulation is full — flush it and restart with this line.
                pieces.append(current)
                current = ""
                candidate = line
                composed_candidate = PythonAstChunker._compose_embedding_text(
                    metadata_header, candidate
                )
            if ctx.count_tokens(composed_candidate) > ctx.max_input_tokens and not current:
                # Single line alone overflows even with no accumulation: hard char-slice.
                pieces.extend(
                    PythonAstChunker._char_slice(line, metadata_header, ctx)
                )
                current = ""
                continue
            current = candidate
        if current:
            pieces.append(current)
        return pieces or [source_text]

    @staticmethod
    def _char_slice(text: str, metadata_header: str, ctx: ChunkContext) -> list[str]:
        """Character-slice ``text`` into pieces whose COMPOSED embedding_text is <= cap.

        This is the last-resort path for a single physical line that exceeds the
        cap even without any accumulation. The cap is checked against the composed
        text (header + piece), matching the same rule as ``_split_to_cap``.

        Edge case (mirror markdown's degenerate handling): if an indivisible
        piece still overflows (e.g. the header itself is at/above the cap), emit
        the piece as-is rather than infinite-looping. Correctness for the normal
        case takes priority; degenerate inputs are handled gracefully.
        """
        cap = ctx.max_input_tokens
        pieces: list[str] = []
        start = 0
        # Estimate a step from the observed chars-per-token ratio of the source
        # text alone, clamped >= 1. The composed overhead is accounted for in the
        # shrink loop below — the initial step is just a fast-path estimate.
        token_count = max(1, ctx.count_tokens(text))
        chars_per_token = max(1, len(text) // token_count)
        step = max(1, cap * chars_per_token)
        while start < len(text):
            end = start + step
            piece = text[start:end]
            composed = PythonAstChunker._compose_embedding_text(metadata_header, piece)
            # Shrink until the COMPOSED text fits the cap, or until we cannot
            # halve further (degenerate: emit as-is to avoid an infinite loop).
            while ctx.count_tokens(composed) > cap and len(piece) > 1:
                piece = piece[: len(piece) // 2]
                composed = PythonAstChunker._compose_embedding_text(
                    metadata_header, piece
                )
            pieces.append(piece)
            start += len(piece)
        return pieces

    # -- Syntax-error fallback --------------------------------------------

    def _chunk_fallback(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Emit overlapping fixed-size line windows for unparseable source.

        Each window is at most :data:`FALLBACK_WINDOW_LINES` lines, consecutive
        windows overlap by :data:`FALLBACK_OVERLAP_LINES`, and each window is
        still capped to ``ctx.max_input_tokens`` via the oversize guard.
        """
        lines = source.splitlines(keepends=True)
        if not lines:
            return []

        header = self._build_metadata_header(ctx, CHUNK_TYPE_WINDOW)
        step = FALLBACK_WINDOW_LINES - FALLBACK_OVERLAP_LINES
        chunks: list[Chunk] = []
        window_index = 0
        start = 0
        while start < len(lines):
            end = min(start + FALLBACK_WINDOW_LINES, len(lines))
            window_text = "".join(lines[start:end])
            chunks.extend(
                self._emit_sized(
                    chunk_type=CHUNK_TYPE_WINDOW,
                    identity=f"window{IDENTITY_DISAMBIGUATOR}{window_index}",
                    source_text=window_text,
                    line_start=start + 1,
                    line_end=end,
                    metadata={
                        "class_name": None,
                        "method_name": None,
                        "inherits": [],
                        "decorators": [],
                    },
                    metadata_header=header,
                    ctx=ctx,
                )
            )
            window_index += 1
            if end >= len(lines):
                break
            start += step
        return chunks

    # -- Helpers ----------------------------------------------------------

    @staticmethod
    def _definition_start_line(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> int:
        """Return the first source line of a def, including any leading decorator.

        A decorated definition's chunk should start at the first decorator, not
        the ``def`` keyword, so the decorator travels with the unit.
        """
        if node.decorator_list:
            return node.decorator_list[0].lineno
        return node.lineno

    @staticmethod
    def _decorator_names(
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    ) -> list[str]:
        """Extract decorator names (``classmethod``, ``api.depends``, ...)."""
        names: list[str] = []
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name):
                    names.append(f"{target.value.id}.{target.attr}")
                else:
                    names.append(target.attr)
            elif isinstance(target, ast.Name):
                names.append(target.id)
        return names

    @staticmethod
    def _build_metadata_header(
        ctx: ChunkContext,
        chunk_type: str,
        *,
        class_name: str | None = None,
        method_name: str | None = None,
    ) -> str:
        """Build the breadcrumb prepended to source to form ``embedding_text``.

        Always names the file; adds ``Class:`` for class/method chunks and
        ``Method:``/``Function:`` for method/function chunks so the embedder
        sees the qualified context.
        """
        parts = [f"File: {ctx.file_path}"]
        if class_name is not None:
            parts.append(f"Class: {class_name}")
        if method_name is not None:
            label = "Method" if chunk_type == CHUNK_TYPE_METHOD else "Function"
            parts.append(f"{label}: {method_name}")
        return "\n".join(parts)
