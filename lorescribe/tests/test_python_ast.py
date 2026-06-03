"""Contract tests for ``lorescribe.python_ast.PythonAstChunker``.

This is a pure-logic AST chunker: it parses a Python source string with the
stdlib ``ast`` module and emits one :class:`~lorescribe.models.Chunk` per
semantic unit. The contract pinned here, from the feature spec (NOT from any
implementation — the module does not exist when these tests are written):

* ``handles(path)`` -> ``True`` iff the path's extension is ``.py``
  (case-insensitive, since the registry normalises extensions).

* ``chunk(source, ctx)`` emits, via ``ast``:
    - exactly ONE ``imports`` chunk covering the module-level imports,
    - one ``class`` chunk per top-level class,
    - one ``method`` chunk per method of a class,
    - one ``function`` chunk per top-level function.
  ``chunk_type`` is therefore drawn from
  ``{"imports", "class", "method", "function"}`` on the happy path.

* **Identity contract** (unique within ``(file, chunk_type)``):
    - function  -> its bare name (``"build_manifest"``),
    - class     -> ``"ClassName"``,
    - method    -> ``"ClassName.method"``,
    - imports   -> the literal ``"imports"``.
  A genuine duplicate within the same ``(file, chunk_type)`` — a redefined
  top-level function, or two same-named methods of one class introduced via a
  conditional ``def`` — gets a ``#N`` disambiguator appended (``"f"``,
  ``"f#1"``, ``"f#2"`` …) so identities never collide. The FIRST occurrence
  keeps the bare identity; later collisions take ``#1``, ``#2``, … in source
  order. This rule is pinned by ``TestDuplicateIdentityDisambiguation``.

* ``metadata`` carries ``class_name`` (the class name, for ``class`` and
  ``method`` chunks), ``method_name`` (for ``method`` and ``function``),
  ``inherits`` (the list of base-class names), and ``decorators`` (the list of
  decorator names). ``line_start`` / ``line_end`` are 1-based AST line numbers.

* ``metadata_header`` is a breadcrumb (``File:`` / ``Class:`` / ``Method:`` …)
  so that ``embedding_text`` (a computed field on ``Chunk``) == header + a
  single newline + source.

* **Syntax-error fallback**: an unparseable source emits fixed-size sliding
  *line* windows, ``chunk_type == "python_window"``, ``identity == "window#N"``
  (N = 0, 1, 2, …), with a small overlap between consecutive windows.

* **Oversize guard (a ``ChunkContext`` invariant)**: no emitted chunk's
  ``source_text`` may exceed ``ctx.max_input_tokens`` as measured by
  ``ctx.count_tokens``. A unit (class / method / function) whose body exceeds
  the cap is sub-split into pieces carrying ``sub_ordinal`` 0, 1, 2, …, each
  at or below the cap, all sharing the unit's identity.

Adversarial pre-flight (each item maps to a covering case or a scoped-out
note) is recorded in the final report, not here.
"""

from __future__ import annotations

import textwrap
from collections.abc import Callable

import pytest
from lorescribe.models import Chunk, ChunkContext

# Target module under contract: ``PythonAstChunker`` is the unit being defined.
from lorescribe.python_ast import PythonAstChunker

from .conftest import (
    SAMPLE_SLUG,
    VOYAGE4_MAX_INPUT_TOKENS,
    approx_token_count,
)

# The four happy-path chunk types the spec pins.
EXPECTED_CHUNK_TYPES: frozenset[str] = frozenset(
    {"imports", "class", "method", "function"}
)

# A realistic, multi-class / multi-method / function / imports Python source.
# Deliberately representative of production code (decorators, inheritance,
# docstrings, a module-level function) rather than a toy. Line numbers below
# are asserted against this exact text, so it is dedented to column 0.
REALISTIC_SOURCE: str = textwrap.dedent(
    '''\
    """A small but realistic module: settings provider + two services."""
    from __future__ import annotations

    import json
    import logging
    from dataclasses import dataclass, field
    from pathlib import Path

    logger = logging.getLogger(__name__)


    @dataclass(frozen=True)
    class Settings:
        """Immutable runtime settings loaded from disk."""

        root: Path
        retries: int = 3

        @classmethod
        def from_file(cls, path: Path) -> "Settings":
            """Load settings from a JSON file."""
            data = json.loads(path.read_text())
            return cls(root=Path(data["root"]), retries=data.get("retries", 3))

        def with_retries(self, retries: int) -> "Settings":
            """Return a copy with a different retry count."""
            return Settings(root=self.root, retries=retries)


    class BaseService:
        """Common service plumbing."""

        def start(self) -> None:
            """Start the service."""
            logger.info("starting %s", type(self).__name__)


    class IndexService(BaseService, dict):
        """Indexes documents; inherits plumbing and dict behaviour."""

        def start(self) -> None:
            """Override: start and warm the cache."""
            super().start()
            self._warm()

        def _warm(self) -> None:
            """Private warm-up step."""
            self.clear()


    def build_manifest(settings: Settings) -> dict[str, int]:
        """Top-level helper that builds a manifest mapping."""
        return {"retries": settings.retries}
    '''
)

# Independently hand-derived ground truth for REALISTIC_SOURCE, indexed by
# (chunk_type, identity). Line numbers are 1-based and were read off the source
# above by hand (NOT produced by the implementation). ``inherits`` is the list
# of base-class names; ``class_name`` is the owning class; ``method_name`` is
# the function/method's bare name; ``decorators`` is the decorator-name list.
#
# Each entry: identity -> dict of the load-bearing fields.
EXPECTED_IMPORTS_IDENTITY: str = "imports"

EXPECTED_CLASSES: dict[str, dict[str, object]] = {
    "Settings": {"inherits": [], "decorators": ["dataclass"]},
    "BaseService": {"inherits": [], "decorators": []},
    # Two explicit bases — exercises multi-base inheritance capture.
    "IndexService": {"inherits": ["BaseService", "dict"], "decorators": []},
}

EXPECTED_METHODS: dict[str, dict[str, object]] = {
    # identity -> (class_name, method_name, decorators)
    "Settings.from_file": {
        "class_name": "Settings",
        "method_name": "from_file",
        "decorators": ["classmethod"],
    },
    "Settings.with_retries": {
        "class_name": "Settings",
        "method_name": "with_retries",
        "decorators": [],
    },
    "BaseService.start": {
        "class_name": "BaseService",
        "method_name": "start",
        "decorators": [],
    },
    "IndexService.start": {
        "class_name": "IndexService",
        "method_name": "start",
        "decorators": [],
    },
    "IndexService._warm": {
        "class_name": "IndexService",
        "method_name": "_warm",
        "decorators": [],
    },
}

EXPECTED_FUNCTIONS: dict[str, dict[str, object]] = {
    "build_manifest": {"method_name": "build_manifest", "decorators": []},
}


def make_ctx(
    *,
    source_path: str = "src/app/services.py",
    max_input_tokens: int = VOYAGE4_MAX_INPUT_TOKENS,
    counter: Callable[[str], int] = approx_token_count,
) -> ChunkContext:
    """Build a ``ChunkContext`` wired to the conftest token counter.

    Mirrors how the consumer injects the embedder's real counter and hard cap;
    tests can shrink ``max_input_tokens`` to force the oversize-guard path.
    """
    return ChunkContext(
        slug=SAMPLE_SLUG,
        file_path=source_path,
        count_tokens=counter,
        max_input_tokens=max_input_tokens,
    )


def chunks_by_type(chunks: list[Chunk], chunk_type: str) -> list[Chunk]:
    """Return chunks of one type, preserving emission order."""
    return [chunk for chunk in chunks if chunk.chunk_type == chunk_type]


def identities(chunks: list[Chunk], chunk_type: str) -> list[str]:
    """Return the identities of chunks of one type, in emission order."""
    return [chunk.identity for chunk in chunks_by_type(chunks, chunk_type)]


class TestHandles:
    """``handles`` claims ``.py`` files, case-insensitively, and nothing else."""

    def setup_method(self) -> None:
        self.chunker = PythonAstChunker()

    def test_handles_dot_py(self) -> None:
        assert self.chunker.handles("src/app/services.py") is True

    def test_handles_is_case_insensitive(self) -> None:
        # The registry normalises extensions to lower-case; a chunker that only
        # matched exact ".py" would silently drop ".PY" files routed to it.
        assert self.chunker.handles("LEGACY/MODULE.PY") is True

    def test_rejects_non_python_extensions(self) -> None:
        assert self.chunker.handles("README.md") is False
        assert self.chunker.handles("config.yaml") is False
        # ".pyc" / ".pyi" are not ".py" — must not be claimed.
        assert self.chunker.handles("app/cache.pyc") is False
        assert self.chunker.handles("app/types.pyi") is False

    def test_rejects_extensionless_path(self) -> None:
        assert self.chunker.handles("Makefile") is False


class TestRealisticChunkSet:
    """A realistic multi-unit source yields the correct, complete chunk set."""

    def setup_method(self) -> None:
        self.chunker = PythonAstChunker()
        self.ctx = make_ctx()
        self.chunks = self.chunker.chunk(REALISTIC_SOURCE, self.ctx)

    def test_returns_list_of_chunks(self) -> None:
        assert isinstance(self.chunks, list)
        assert all(isinstance(chunk, Chunk) for chunk in self.chunks)

    def test_only_expected_chunk_types_emitted(self) -> None:
        # No window / sub-split types on a clean, within-cap parse.
        emitted_types = {chunk.chunk_type for chunk in self.chunks}
        assert emitted_types <= EXPECTED_CHUNK_TYPES
        # All four categories are present in this source.
        assert emitted_types == EXPECTED_CHUNK_TYPES

    def test_exactly_one_imports_chunk(self) -> None:
        imports = chunks_by_type(self.chunks, "imports")
        assert len(imports) == 1
        assert imports[0].identity == EXPECTED_IMPORTS_IDENTITY

    def test_imports_chunk_covers_module_level_imports(self) -> None:
        imports = chunks_by_type(self.chunks, "imports")[0]
        # The four import statements live on source lines 2-7; the imports
        # chunk must cover that span (start at the first import, end no earlier
        # than the last). Independent of how the impl slices the text.
        assert imports.line_start == 2
        assert imports.line_end >= 7
        # Source text actually contains the imported names.
        assert "from __future__ import annotations" in imports.source_text
        assert "from pathlib import Path" in imports.source_text

    def test_class_chunks_match_ground_truth(self) -> None:
        class_chunks = {chunk.identity: chunk for chunk in chunks_by_type(self.chunks, "class")}
        assert set(class_chunks) == set(EXPECTED_CLASSES)
        for identity, expected in EXPECTED_CLASSES.items():
            chunk = class_chunks[identity]
            assert chunk.metadata["class_name"] == identity
            assert chunk.metadata["inherits"] == expected["inherits"]
            assert chunk.metadata["decorators"] == expected["decorators"]

    def test_method_chunks_match_ground_truth(self) -> None:
        method_chunks = {chunk.identity: chunk for chunk in chunks_by_type(self.chunks, "method")}
        assert set(method_chunks) == set(EXPECTED_METHODS)
        for identity, expected in EXPECTED_METHODS.items():
            chunk = method_chunks[identity]
            assert chunk.metadata["class_name"] == expected["class_name"]
            assert chunk.metadata["method_name"] == expected["method_name"]
            assert chunk.metadata["decorators"] == expected["decorators"]

    def test_function_chunks_match_ground_truth(self) -> None:
        function_chunks = {
            chunk.identity: chunk for chunk in chunks_by_type(self.chunks, "function")
        }
        assert set(function_chunks) == set(EXPECTED_FUNCTIONS)
        for identity, expected in EXPECTED_FUNCTIONS.items():
            chunk = function_chunks[identity]
            assert chunk.metadata["method_name"] == expected["method_name"]
            assert chunk.metadata["decorators"] == expected["decorators"]

    def test_inherits_captures_multiple_bases(self) -> None:
        # IndexService(BaseService, dict): both bases, in source order.
        index = {c.identity: c for c in chunks_by_type(self.chunks, "class")}["IndexService"]
        assert index.metadata["inherits"] == ["BaseService", "dict"]

    def test_decorator_capture_on_classmethod(self) -> None:
        from_file = {c.identity: c for c in chunks_by_type(self.chunks, "method")}[
            "Settings.from_file"
        ]
        assert "classmethod" in from_file.metadata["decorators"]

    def test_line_numbers_are_1_based_and_ordered(self) -> None:
        # Every chunk's span is sane: 1-based, start <= end, within the file.
        total_lines = REALISTIC_SOURCE.count("\n") + 1
        for chunk in self.chunks:
            assert chunk.line_start >= 1
            assert chunk.line_end >= chunk.line_start
            assert chunk.line_end <= total_lines

    def test_method_line_span_matches_source(self) -> None:
        # Independent ground truth (read off REALISTIC_SOURCE via ast): the
        # ``with_retries`` method (no decorator) spans lines 25-27 — the
        # ``def`` line through its ``return``.
        with_retries = {c.identity: c for c in chunks_by_type(self.chunks, "method")}[
            "Settings.with_retries"
        ]
        assert with_retries.line_start == 25
        assert with_retries.line_end == 27
        assert "def with_retries" in with_retries.source_text
        assert "return Settings(" in with_retries.source_text

    def test_metadata_header_drives_embedding_text(self) -> None:
        # embedding_text is header + "\n" + source_text (Chunk's computed field).
        # The header must be a non-empty breadcrumb mentioning the file.
        build = {c.identity: c for c in chunks_by_type(self.chunks, "function")}[
            "build_manifest"
        ]
        assert build.metadata_header  # non-empty breadcrumb
        assert "services.py" in build.metadata_header
        assert build.embedding_text == f"{build.metadata_header}\n{build.source_text}"

    def test_method_header_names_class_and_method(self) -> None:
        warm = {c.identity: c for c in chunks_by_type(self.chunks, "method")}[
            "IndexService._warm"
        ]
        # Breadcrumb carries both the owning class and the method name so the
        # embedder sees the qualified context.
        assert "IndexService" in warm.metadata_header
        assert "_warm" in warm.metadata_header


class TestSiblingMethodUniqueness:
    """Two methods of one class get distinct ``ClassName.method`` identities."""

    SOURCE = textwrap.dedent(
        '''\
        class Repo:
            def save(self):
                return 1

            def load(self):
                return 2
        '''
    )

    def setup_method(self) -> None:
        self.chunks = PythonAstChunker().chunk(self.SOURCE, make_ctx())

    def test_distinct_sibling_method_identities(self) -> None:
        method_identities = identities(self.chunks, "method")
        assert method_identities == ["Repo.save", "Repo.load"]
        # No collision — set size equals list size.
        assert len(set(method_identities)) == len(method_identities)


class TestMethodFunctionNameCollisionAcrossTypes:
    """A method and a top-level function sharing a bare name do NOT collide.

    Identity uniqueness is scoped to ``(file, chunk_type)``; a ``method`` named
    ``start`` and a ``function`` named ``start`` are different chunk_types, so
    each keeps the natural identity for its type without a disambiguator.
    """

    SOURCE = textwrap.dedent(
        '''\
        class Engine:
            def start(self):
                return "on"


        def start():
            return "module-level"
        '''
    )

    def setup_method(self) -> None:
        self.chunks = PythonAstChunker().chunk(self.SOURCE, make_ctx())

    def test_method_keeps_qualified_identity(self) -> None:
        assert identities(self.chunks, "method") == ["Engine.start"]

    def test_function_keeps_bare_identity(self) -> None:
        # Same bare name "start", different chunk_type -> no disambiguator.
        assert identities(self.chunks, "function") == ["start"]


class TestDuplicateIdentityDisambiguation:
    """Genuine within-(file, type) duplicates get ``#N`` disambiguators.

    Contract decision (pinned): the conditional ``def run`` pair lives nested
    inside an ``if``/``else`` block of the class body, NOT as direct children
    of ``ClassDef.body``. The spec names "two same-named methods via
    conditional def" as a duplicate case, so the chunker MUST descend into
    nested control flow within a class to surface both definitions (a naive
    ``for stmt in class_node.body`` would emit zero ``Toggle.run`` chunks).
    """

    # A redefined top-level function AND a conditionally-redefined method.
    # First occurrence keeps the bare identity; later ones take #1, #2, ...
    SOURCE = textwrap.dedent(
        '''\
        def handler():
            return "first"


        def handler():
            return "second"


        class Toggle:
            if True:
                def run(self):
                    return "a"
            else:
                def run(self):
                    return "b"
        '''
    )

    def setup_method(self) -> None:
        self.chunks = PythonAstChunker().chunk(self.SOURCE, make_ctx())

    def test_redefined_function_disambiguated(self) -> None:
        # Two top-level ``handler`` defs -> "handler", "handler#1".
        func_identities = identities(self.chunks, "function")
        assert func_identities == ["handler", "handler#1"]
        assert len(set(func_identities)) == len(func_identities)

    def test_conditionally_redefined_method_disambiguated(self) -> None:
        # Two ``Toggle.run`` defs (one per if/else branch) must not collide.
        method_identities = identities(self.chunks, "method")
        assert method_identities == ["Toggle.run", "Toggle.run#1"]
        assert len(set(method_identities)) == len(method_identities)

    def test_no_identity_is_blank(self) -> None:
        # The Chunk model rejects blank identities; assert none slipped through
        # the disambiguation logic with an empty string.
        for chunk in self.chunks:
            assert chunk.identity.strip()


class TestEmptyAndImportsOnly:
    """Empty input yields nothing; an imports-only file yields one chunk."""

    def test_empty_source_yields_no_chunks(self) -> None:
        # Pinned decision: an empty (or whitespace-only) file produces [].
        assert PythonAstChunker().chunk("", make_ctx()) == []
        assert PythonAstChunker().chunk("   \n\n  ", make_ctx()) == []

    def test_imports_only_file_yields_single_imports_chunk(self) -> None:
        source = textwrap.dedent(
            """\
            import os
            import sys
            from pathlib import Path
            """
        )
        chunks = PythonAstChunker().chunk(source, make_ctx())
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "imports"
        assert chunks[0].identity == "imports"
        assert chunks[0].line_start == 1
        assert chunks[0].line_end >= 3

    def test_no_imports_file_emits_no_imports_chunk(self) -> None:
        # A file with only a function and no imports must NOT fabricate an
        # empty imports chunk (which would carry blank source_text).
        source = textwrap.dedent(
            """\
            def ping():
                return "pong"
            """
        )
        chunks = PythonAstChunker().chunk(source, make_ctx())
        assert chunks_by_type(chunks, "imports") == []
        assert identities(chunks, "function") == ["ping"]


class TestSyntaxErrorFallback:
    """Unparseable source falls back to fixed-size sliding line windows."""

    def setup_method(self) -> None:
        # Genuinely unparseable: an unterminated def with broken indentation
        # that ``ast.parse`` rejects with SyntaxError. Make it long enough to
        # span multiple windows so overlap behaviour is observable.
        body_lines = [f"    x_{i} = compute(value_{i}" for i in range(450)]
        self.source = "def broken(:\n" + "\n".join(body_lines) + "\n"
        self.chunks = PythonAstChunker().chunk(self.source, make_ctx())

    def test_fallback_emits_python_window_chunks(self) -> None:
        assert len(self.chunks) >= 2  # >450 lines -> multiple ~200-line windows
        assert all(chunk.chunk_type == "python_window" for chunk in self.chunks)

    def test_window_identities_are_indexed(self) -> None:
        window_identities = [chunk.identity for chunk in self.chunks]
        # window#0, window#1, ... contiguous from 0, all distinct.
        assert window_identities[0] == "window#0"
        assert window_identities == [f"window#{i}" for i in range(len(self.chunks))]
        assert len(set(window_identities)) == len(window_identities)

    def test_windows_overlap_and_cover_all_lines(self) -> None:
        total_lines = self.source.count("\n") + 1
        # First window starts at line 1; last window ends at the final line.
        assert self.chunks[0].line_start == 1
        assert self.chunks[-1].line_end >= total_lines - 1
        # Consecutive windows overlap: each next window starts at or before the
        # previous window's end (small overlap), and strictly advances.
        for previous, following in zip(self.chunks, self.chunks[1:]):
            assert following.line_start > previous.line_start  # progress
            assert following.line_start <= previous.line_end  # overlap, no gap

    def test_window_size_is_bounded(self) -> None:
        # Windows are ~200 lines; none should be absurdly large.
        for chunk in self.chunks:
            span = chunk.line_end - chunk.line_start + 1
            assert span <= 200


class TestOversizeGuard:
    """No emitted chunk exceeds ``ctx.max_input_tokens``; oversize units split."""

    # A class with one very long method body whose source blows past a small
    # injected cap. Built large enough that, at the test counter
    # (len // 4 tokens), the method exceeds the cap and MUST be sub-split.
    @staticmethod
    def _oversize_source() -> str:
        # Body lines are indented to 8 spaces so they sit INSIDE ``execute``
        # (4 spaces = class body, 8 spaces = method body). 400 statements push
        # the method's source past the small injected cap.
        body = "\n".join(f"        step_{i} = transform(payload_{i})" for i in range(400))
        return textwrap.dedent(
            '''\
            class Pipeline:
                def execute(self):
            '''
        ) + body + "\n"

    # Test counter: len // 4 (no max(1, ...)) so arithmetic is clean and the
    # spec's "count_tokens=lambda s: len(s)//4" injection is honoured exactly.
    @staticmethod
    def _quarter_len(text: str) -> int:
        return len(text) // 4

    def test_no_chunk_exceeds_cap_with_small_max_tokens(self) -> None:
        source = self._oversize_source()
        # Small cap that the long method's source clearly exceeds.
        small_cap = 200
        ctx = make_ctx(max_input_tokens=small_cap, counter=self._quarter_len)
        chunks = PythonAstChunker().chunk(source, ctx)
        assert chunks, "expected at least one chunk"
        for chunk in chunks:
            assert self._quarter_len(chunk.source_text) <= small_cap, (
                f"chunk {chunk.chunk_type}:{chunk.identity}#{chunk.sub_ordinal} "
                f"= {self._quarter_len(chunk.source_text)} tokens exceeds cap {small_cap}"
            )

    def test_oversize_unit_is_sub_split_with_sub_ordinals(self) -> None:
        source = self._oversize_source()
        small_cap = 200
        ctx = make_ctx(max_input_tokens=small_cap, counter=self._quarter_len)
        chunks = PythonAstChunker().chunk(source, ctx)
        # The ``execute`` method is oversize -> multiple method chunks sharing
        # the identity "Pipeline.execute", with sub_ordinal 0, 1, 2, ...
        execute_pieces = [
            chunk
            for chunk in chunks
            if chunk.chunk_type == "method" and chunk.identity == "Pipeline.execute"
        ]
        assert len(execute_pieces) >= 2, "oversize method should split into >= 2 pieces"
        sub_ordinals = [chunk.sub_ordinal for chunk in execute_pieces]
        # Contiguous from 0, in order.
        assert sub_ordinals == list(range(len(execute_pieces)))

    def test_within_cap_unit_keeps_single_chunk_sub_ordinal_zero(self) -> None:
        # A small method under the real cap is a single chunk, sub_ordinal 0.
        source = textwrap.dedent(
            '''\
            class Tiny:
                def noop(self):
                    return None
            '''
        )
        chunks = PythonAstChunker().chunk(source, make_ctx())
        noop_pieces = [
            chunk
            for chunk in chunks
            if chunk.chunk_type == "method" and chunk.identity == "Tiny.noop"
        ]
        assert len(noop_pieces) == 1
        assert noop_pieces[0].sub_ordinal == 0


class TestOversizeSubSplitLineRanges:
    """Each sub-chunk of an oversize unit carries the line range for ITS span.

    The existing ``TestOversizeGuard`` proves an oversize unit splits into
    ``sub_ordinal``-stamped pieces under the cap, but it asserts nothing about
    the *line numbers* on those pieces. The regression this class guards: a
    sub-split must not stamp every piece with the whole unit's ``line_start`` /
    ``line_end`` — each piece must report the lines IT actually covers, and the
    pieces together must tile the unit's span contiguously and without overlap.

    The unit is a realistic, many-statement top-level function with a genuine
    multi-line body, so the greedy *line-boundary* split path is exercised (not
    the degenerate single-over-cap-line char-slice path). Ground truth for the
    unit's full span is read independently off the source via ``ast``; the
    per-piece ranges are checked for internal consistency (span == newline
    count), contiguity, and exact coverage of the ``ast`` span.
    """

    # A realistic function: 30 genuine dict-construction statements over
    # parallel inputs, plus a docstring and a return. Each line is real code,
    # not a repeated no-op, so the body resembles production aggregation logic.
    SOURCE: str = (
        '"""Realistic oversize function module."""\n'
        "from __future__ import annotations\n"
        "\n\n"
        "def aggregate_records(name, score, weight):\n"
        '    """Build a list of record dicts from parallel inputs."""\n'
        + "\n".join(
            f'    record_{i} = '
            f'{{"id": {i}, "name": name_{i}, "score": score_{i} * weight_{i}}}'
            for i in range(30)
        )
        + "\n    return [record_0, record_29]\n"
    )

    # The function's identity in the emitted chunks.
    FUNCTION_IDENTITY: str = "aggregate_records"

    @staticmethod
    def _quarter_len(text: str) -> int:
        return len(text) // 4

    @staticmethod
    def _ast_function_span(source: str, name: str) -> tuple[int, int]:
        """Read a top-level function's 1-based ``(line_start, line_end)`` via ast.

        Independent ground truth: derived by the stdlib parser, not by the
        chunker. This function has no decorators, so its first line is the
        ``def`` line — ``node.lineno``.
        """
        import ast

        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                assert node.end_lineno is not None
                return node.lineno, node.end_lineno
        raise AssertionError(f"function {name!r} not found in source")

    def setup_method(self) -> None:
        # A small cap the multi-line function body clearly exceeds, forcing a
        # multi-piece greedy line-boundary split.
        self.small_cap = 60
        self.ctx = make_ctx(max_input_tokens=self.small_cap, counter=self._quarter_len)
        self.chunks = PythonAstChunker().chunk(self.SOURCE, self.ctx)
        self.pieces = [
            chunk
            for chunk in self.chunks
            if chunk.chunk_type == "function"
            and chunk.identity == self.FUNCTION_IDENTITY
        ]

    def test_unit_actually_sub_split(self) -> None:
        # Precondition for the regression: the unit must split into >= 2 pieces,
        # otherwise per-piece line ranges would be trivially the whole span.
        assert len(self.pieces) >= 2, "oversize function should split into >= 2 pieces"
        assert [piece.sub_ordinal for piece in self.pieces] == list(
            range(len(self.pieces))
        )

    def test_each_piece_line_span_matches_its_own_text(self) -> None:
        # The load-bearing assertion: a piece's reported line span must equal
        # the number of physical lines in its own ``source_text`` — NOT the
        # whole unit's span. ``count("\n")`` on keepends-joined source lines is
        # exactly the line count for a multi-line greedy split.
        for piece in self.pieces:
            reported_span = piece.line_end - piece.line_start + 1
            text_line_count = piece.source_text.count("\n")
            assert reported_span == text_line_count, (
                f"sub_ordinal={piece.sub_ordinal} reports {reported_span} lines "
                f"({piece.line_start}-{piece.line_end}) but its source_text has "
                f"{text_line_count} lines"
            )

    def test_pieces_are_contiguous_and_non_overlapping(self) -> None:
        # Each next piece starts exactly one line after the previous ends: no
        # gap (lines lost) and no overlap (lines double-counted).
        for previous, following in zip(self.pieces, self.pieces[1:]):
            assert following.line_start == previous.line_end + 1, (
                f"piece {following.sub_ordinal} starts at {following.line_start}; "
                f"expected {previous.line_end + 1} (contiguous, no gap/overlap)"
            )

    def test_pieces_exactly_cover_the_ast_unit_span(self) -> None:
        # The tiled pieces must span precisely the function's true extent,
        # read independently from ast: first piece at the ``def`` line, last
        # piece at the function's final line.
        ast_start, ast_end = self._ast_function_span(
            self.SOURCE, self.FUNCTION_IDENTITY
        )
        assert self.pieces[0].line_start == ast_start
        assert self.pieces[-1].line_end == ast_end


class TestDecoratedMethodLineSpan:
    """A decorated def's line span runs from its first decorator through its body.

    ``TestRealisticChunkSet`` checks a *decorator-free* method's span; this
    class pins the decorated case (including STACKED decorators): the chunk's
    ``line_start`` must be the first decorator line — so the decorator travels
    with the unit — and ``line_end`` the body's last line. Ground truth is read
    independently off the source via ``ast`` (``decorator_list[0].lineno`` and
    ``node.end_lineno``).
    """

    SOURCE: str = textwrap.dedent(
        '''\
        """Module with stacked- and single-decorator methods."""
        import functools


        class Api:
            """Endpoint handlers."""

            @property
            @functools.lru_cache(maxsize=None)
            def cached_token(self):
                """Return a cached auth token."""
                return self._compute_token()

            @staticmethod
            def plain(self):
                return 0
        '''
    )

    @staticmethod
    def _ast_method_span(source: str, class_name: str, method_name: str) -> tuple[int, int]:
        """Read a method's decorator-inclusive 1-based span via ast.

        ``line_start`` is the first decorator's line when decorated (else the
        ``def`` line); ``line_end`` is the node's ``end_lineno``. Independent of
        the chunker.
        """
        import ast

        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for member in node.body:
                    if (
                        isinstance(member, ast.FunctionDef)
                        and member.name == method_name
                    ):
                        assert member.end_lineno is not None
                        if member.decorator_list:
                            return member.decorator_list[0].lineno, member.end_lineno
                        return member.lineno, member.end_lineno
        raise AssertionError(f"method {class_name}.{method_name} not found")

    def setup_method(self) -> None:
        self.chunks = PythonAstChunker().chunk(self.SOURCE, make_ctx())
        self.methods = {
            chunk.identity: chunk
            for chunk in self.chunks
            if chunk.chunk_type == "method"
        }

    def test_stacked_decorators_included_in_line_span(self) -> None:
        # cached_token carries @property + @functools.lru_cache: the chunk must
        # start at the FIRST decorator line, not the ``def`` line.
        expected_start, expected_end = self._ast_method_span(
            self.SOURCE, "Api", "cached_token"
        )
        cached = self.methods["Api.cached_token"]
        assert cached.line_start == expected_start
        assert cached.line_end == expected_end
        # The decorator and the body's final statement both live in the text.
        assert "@property" in cached.source_text
        assert "@functools.lru_cache" in cached.source_text
        assert "return self._compute_token()" in cached.source_text
        # Both decorators are captured in metadata.
        assert "property" in cached.metadata["decorators"]
        assert "functools.lru_cache" in cached.metadata["decorators"]

    def test_single_decorator_included_in_line_span(self) -> None:
        expected_start, expected_end = self._ast_method_span(
            self.SOURCE, "Api", "plain"
        )
        plain = self.methods["Api.plain"]
        assert plain.line_start == expected_start
        assert plain.line_end == expected_end
        assert "@staticmethod" in plain.source_text
        assert plain.metadata["decorators"] == ["staticmethod"]


class TestEmbeddingTextHeaderBudget:
    """Every emitted chunk's ``embedding_text`` fits the embedder's hard cap.

    This class pins the bug fixed in the header-budget patch: the oversize guard
    in ``_emit_sized`` was sizing ``source_text`` against the cap, but the
    embedder's real input is ``embedding_text = metadata_header + "\\n" + source_text``.
    A unit whose ``source_text`` was exactly AT the cap would overflow it once
    the header's tokens were included — producing an HTTP 422 from the embedder
    and dropping the whole file from the index.

    The contract: for ANY Python source and ANY ``max_input_tokens``, EVERY
    chunk emitted by ``PythonAstChunker.chunk()`` must satisfy
    ``ctx.count_tokens(chunk.embedding_text) <= ctx.max_input_tokens``.

    Reference (independent oracle): the markdown chunker's
    ``_enforce_token_cap`` already measures ``embedding_text`` (the composed
    string), not ``source_text``. This test encodes the same rule for the
    python_ast chunker.

    Covered chunk types:
    - ``imports`` chunk: header is ``"File: <path>"`` only (shortest header).
    - ``method`` chunk: header is ``"File: <path>\\nClass: <C>\\nMethod: <m>"``
      (longest header; largest overflow risk).
    - ``function`` chunk: header is ``"File: <path>\\nFunction: <f>"``
      (intermediate header length).

    Design:
    - CAP = 50 (small, deterministic — avoids 8192-token fixtures while keeping
      the token arithmetic concrete and auditable without a running embedder).
    - FILE_PATH = "loremaster/tests/test_mcp_server.py" — the actual production
      file that triggered the 422. Its length makes the header 10 tokens, enough
      to push a 50-token source to 60 tokens in the composed text.
    - Token counter: ``approx_token_count`` from conftest (``max(1, len // 4)``),
      the same callable the consumer injects in production.
    - All ``source_text`` fixture sizes are derived from the requirement
      (``count_tokens(source) == CAP``) and hand-verified, not from the
      implementation's formula.

    Fixture arithmetic (verified independently, see inline comments):

    ``approx_token_count(text) = max(1, len(text) // 4)``

    headers (from ``_build_metadata_header``; read off the implementation's
    string-building logic, not from a run of the code):
    - imports: ``"File: loremaster/tests/test_mcp_server.py"`` = 41 chars →
      with separator ``\\n`` → 42 chars → ``42 // 4 = 10`` tokens overhead.
    - method: ``"File: ...\\nClass: Processor\\nMethod: process"`` = 74 chars →
      with separator → 75 chars → ``75 // 4 = 18`` tokens overhead.
    - function: ``"File: ...\\nFunction: compute"`` = 59 chars → with separator
      → 60 chars → ``60 // 4 = 15`` tokens overhead.

    Source fixtures (200 chars each → ``200 // 4 = 50`` tokens = CAP):
    - import block: 20 × ``"import os\\n"`` (10 chars each) = 200 chars.
    - method source: ``"    def process(self):\\n"`` (23 chars) +
      3 × (``"        " + "a"*50 + "\\n"``) (59 chars each) = 200 chars.
    - function source: ``"def compute():\\n"`` (15 chars) +
      5 × (``"    " + "b"*32 + "\\n"``) (37 chars each) = 200 chars.

    These fixtures were chosen to make source_tokens == CAP exactly with no
    rounding ambiguity (all lengths are multiples of 4).
    """

    # ------------------------------------------------------------------ #
    # Production-realistic file path: the actual file that caused the 422. #
    # ------------------------------------------------------------------ #
    # "loremaster/tests/test_mcp_server.py" → header = "File: loremaster/tests/test_mcp_server.py"
    # len("File: loremaster/tests/test_mcp_server.py\n") = 42 → 42//4 = 10 tokens overhead
    HEADER_BUDGET_FILE_PATH: str = "loremaster/tests/test_mcp_server.py"

    # Small, deterministic cap. Chosen so the fixture sources fit in 50 tokens
    # and the composed embedding_text overflows by a concrete, auditable amount.
    # Not a round power-of-two; intentionally sized to the fixture arithmetic.
    HEADER_BUDGET_CAP: int = 50

    # ------------------------------------------------------------------ #
    # Source fixtures: each is exactly 200 chars → 50 tokens = CAP.      #
    # Verified independently: len(fixture) == 200, len // 4 == 50.       #
    # ------------------------------------------------------------------ #

    # imports block: 20 lines of "import os\n" (10 chars each = 200 total).
    # Realistic: "import os" is a genuine Python import statement, not filler.
    _IMPORT_LINE: str = "import os\n"          # 10 chars
    _IMPORT_LINE_COUNT: int = 20               # 20 × 10 = 200 chars = 50 tokens

    # method source: 1 def line (23 chars) + 3 body lines (59 chars each).
    # Body lines use "        " (8-space method indent) + 50 "a"s + "\n".
    # 23 + 3×59 = 200 chars = 50 tokens. Indented 4 spaces (class body level).
    _METHOD_DEF_LINE: str = "    def process(self):\n"    # 23 chars
    _METHOD_BODY_LINE: str = "        " + "a" * 50 + "\n" # 59 chars
    _METHOD_BODY_LINE_COUNT: int = 3                        # 3×59 = 177 chars

    # function source: 1 def line (15 chars) + 5 body lines (37 chars each).
    # 15 + 5×37 = 200 chars = 50 tokens. Top-level (no class indent).
    _FUNC_DEF_LINE: str = "def compute():\n"              # 15 chars
    _FUNC_BODY_LINE: str = "    " + "b" * 32 + "\n"       # 37 chars
    _FUNC_BODY_LINE_COUNT: int = 5                          # 5×37 = 185 chars

    @classmethod
    def _import_source(cls) -> str:
        """Return the imports block source: 200 chars, 50 tokens."""
        return cls._IMPORT_LINE * cls._IMPORT_LINE_COUNT

    @classmethod
    def _method_source(cls) -> str:
        """Return the method source: 200 chars, 50 tokens, indented for a class body."""
        return cls._METHOD_DEF_LINE + cls._METHOD_BODY_LINE * cls._METHOD_BODY_LINE_COUNT

    @classmethod
    def _func_source(cls) -> str:
        """Return the top-level function source: 200 chars, 50 tokens."""
        return cls._FUNC_DEF_LINE + cls._FUNC_BODY_LINE * cls._FUNC_BODY_LINE_COUNT

    @classmethod
    def _build_full_source(cls) -> str:
        """Compose a valid Python module containing all three unit types.

        Structure:
          <imports block>        ← 200 chars, imports chunk
          <blank lines>
          class Processor:       ← contains the method chunk
              <method source>
          <blank lines>
          <function source>      ← function chunk
        """
        return (
            cls._import_source()
            + "\n\nclass Processor:\n"
            + cls._method_source()
            + "\n\n"
            + cls._func_source()
        )

    @classmethod
    def _make_header_budget_ctx(cls) -> ChunkContext:
        """Build a ChunkContext using the production file path and the small cap."""
        return ChunkContext(
            slug=SAMPLE_SLUG,
            file_path=cls.HEADER_BUDGET_FILE_PATH,
            count_tokens=approx_token_count,
            max_input_tokens=cls.HEADER_BUDGET_CAP,
        )

    def setup_method(self) -> None:
        self.ctx = self._make_header_budget_ctx()
        self.source = self._build_full_source()
        self.chunks = PythonAstChunker().chunk(self.source, self.ctx)

    # ------------------------------------------------------------------ #
    # Precondition tests: verify the fixture properties independently,   #
    # so a future refactor that silently changes fixture sizes is caught  #
    # before it masks the main behavioural assertion.                     #
    # ------------------------------------------------------------------ #

    def test_fixture_import_source_is_exactly_at_cap(self) -> None:
        """Import source is exactly CAP tokens — precondition for the overflow test."""
        source = self._import_source()
        # Independent check: len is a multiple of 4, so no floor-division rounding.
        assert len(source) == self._IMPORT_LINE_COUNT * len(self._IMPORT_LINE)
        assert approx_token_count(source) == self.HEADER_BUDGET_CAP

    def test_fixture_method_source_is_exactly_at_cap(self) -> None:
        """Method source is exactly CAP tokens — precondition for the overflow test."""
        source = self._method_source()
        assert approx_token_count(source) == self.HEADER_BUDGET_CAP

    def test_fixture_func_source_is_exactly_at_cap(self) -> None:
        """Function source is exactly CAP tokens — precondition for the overflow test."""
        source = self._func_source()
        assert approx_token_count(source) == self.HEADER_BUDGET_CAP

    def test_fixture_source_is_valid_python(self) -> None:
        """The combined source must be parseable — non-parseable source takes the window fallback."""
        import ast
        try:
            ast.parse(self.source)
        except SyntaxError as exc:
            raise AssertionError(f"fixture source is not valid Python: {exc}") from exc

    # ------------------------------------------------------------------ #
    # Main contract: embedding_text of EVERY chunk fits the cap.         #
    # On the buggy code (pre-fix), at least one chunk violates this      #
    # assertion — the test FAILS.                                        #
    # ------------------------------------------------------------------ #

    def test_every_chunk_embedding_text_fits_cap_for_imports_unit(self) -> None:
        """All imports chunk pieces have embedding_text <= cap (File-only header).

        The imports header is ``"File: loremaster/tests/test_mcp_server.py"``
        (10 tokens of overhead). With a source_text AT the cap, the composed
        embedding_text = 60 tokens > 50 (cap). On buggy code this assertion
        fails; after the fix the chunker splits the imports block so that each
        piece's composed text fits.
        """
        import_chunks = chunks_by_type(self.chunks, "imports")
        assert import_chunks, "expected at least one imports chunk"
        for chunk in import_chunks:
            # embedding_text is the REAL embedder input — the string the
            # embedder hard-rejects with HTTP 422 if it exceeds the cap.
            embedding_tokens = approx_token_count(chunk.embedding_text)
            assert embedding_tokens <= self.HEADER_BUDGET_CAP, (
                f"imports chunk (sub_ordinal={chunk.sub_ordinal}) embedding_text "
                f"= {embedding_tokens} tokens, exceeds cap {self.HEADER_BUDGET_CAP}. "
                f"header={repr(chunk.metadata_header)}"
            )

    def test_every_chunk_embedding_text_fits_cap_for_method_unit(self) -> None:
        """All method chunk pieces have embedding_text <= cap (File+Class+Method header).

        The method header is the longest of the three types (three lines:
        File, Class, Method), contributing 18 tokens of overhead. This is the
        highest-overflow-risk case: source_text AT the cap produces
        embedding_text = 68 tokens (18 over). On buggy code this fails.
        """
        method_chunks = [
            chunk for chunk in self.chunks
            if chunk.chunk_type == "method" and chunk.identity == "Processor.process"
        ]
        assert method_chunks, "expected at least one Processor.process method chunk"
        for chunk in method_chunks:
            embedding_tokens = approx_token_count(chunk.embedding_text)
            assert embedding_tokens <= self.HEADER_BUDGET_CAP, (
                f"method chunk (sub_ordinal={chunk.sub_ordinal}) embedding_text "
                f"= {embedding_tokens} tokens, exceeds cap {self.HEADER_BUDGET_CAP}. "
                f"header={repr(chunk.metadata_header)}"
            )

    def test_every_chunk_embedding_text_fits_cap_for_function_unit(self) -> None:
        """All function chunk pieces have embedding_text <= cap (File+Function header).

        The function header contributes 15 tokens of overhead. source_text AT
        the cap → embedding_text = 65 tokens (15 over). On buggy code this fails.
        """
        function_chunks = [
            chunk for chunk in self.chunks
            if chunk.chunk_type == "function" and chunk.identity == "compute"
        ]
        assert function_chunks, "expected at least one compute function chunk"
        for chunk in function_chunks:
            embedding_tokens = approx_token_count(chunk.embedding_text)
            assert embedding_tokens <= self.HEADER_BUDGET_CAP, (
                f"function chunk (sub_ordinal={chunk.sub_ordinal}) embedding_text "
                f"= {embedding_tokens} tokens, exceeds cap {self.HEADER_BUDGET_CAP}. "
                f"header={repr(chunk.metadata_header)}"
            )

    def test_every_emitted_chunk_embedding_text_fits_cap_exhaustive(self) -> None:
        """The universal assertion: no chunk of any type has an overflowing embedding_text.

        This is the single authoritative guard covering ALL chunk types the
        chunker may emit for this source (imports, class, method, function).
        The per-type tests above confirm the three targeted failure modes
        individually; this test catches any residual overflow from a partial fix
        that only corrects some code paths.
        """
        assert self.chunks, "expected at least one chunk"
        violations = [
            (chunk.chunk_type, chunk.identity, chunk.sub_ordinal,
             approx_token_count(chunk.embedding_text))
            for chunk in self.chunks
            if approx_token_count(chunk.embedding_text) > self.HEADER_BUDGET_CAP
        ]
        assert not violations, (
            f"Chunks whose embedding_text exceeds cap={self.HEADER_BUDGET_CAP}: "
            + ", ".join(
                f"{ct}:{identity}#{ordinal}={tokens}tok"
                for ct, identity, ordinal, tokens in violations
            )
        )

    # ------------------------------------------------------------------ #
    # Post-split quality guards: the fix must not produce degenerate or  #
    # uselessly tiny pieces.                                             #
    # ------------------------------------------------------------------ #

    def test_split_pieces_are_non_empty(self) -> None:
        """Every piece emitted by the split has non-blank source_text.

        A degenerate empty-string piece would be embeddable (0 tokens) but
        useless, and a blank identity would be rejected by the Chunk model.
        """
        for chunk in self.chunks:
            assert chunk.source_text.strip(), (
                f"chunk {chunk.chunk_type}:{chunk.identity}#{chunk.sub_ordinal} "
                f"has blank source_text"
            )

    def test_split_produces_at_least_two_pieces_per_overflowing_unit(self) -> None:
        """Units that overflow with a header must split into >= 2 pieces.

        If the fix causes a single 50-token source unit to emit as a single
        piece, the piece's embedding_text still overflows. Splitting means the
        chunker actually distributed the source across multiple sub-ordinal
        chunks.
        """
        # imports: source_text=50 tokens, header overhead=10 → must split
        import_pieces = chunks_by_type(self.chunks, "imports")
        assert len(import_pieces) >= 2, (
            f"imports block (source_text=CAP tokens, header overhead > 0) "
            f"should split into >= 2 pieces after the header-budget fix, "
            f"got {len(import_pieces)}"
        )

        # method: source_text=50 tokens, header overhead=18 → must split
        method_pieces = [
            chunk for chunk in self.chunks
            if chunk.chunk_type == "method" and chunk.identity == "Processor.process"
        ]
        assert len(method_pieces) >= 2, (
            f"Processor.process (source_text=CAP tokens, header overhead > 0) "
            f"should split into >= 2 pieces after the header-budget fix, "
            f"got {len(method_pieces)}"
        )

        # function: source_text=50 tokens, header overhead=15 → must split
        function_pieces = [
            chunk for chunk in self.chunks
            if chunk.chunk_type == "function" and chunk.identity == "compute"
        ]
        assert len(function_pieces) >= 2, (
            f"compute (source_text=CAP tokens, header overhead > 0) "
            f"should split into >= 2 pieces after the header-budget fix, "
            f"got {len(function_pieces)}"
        )

    def test_split_embedding_text_tokens_are_within_reasonable_range(self) -> None:
        """Split pieces use the budget meaningfully: no piece is absurdly small.

        A correct implementation packs each piece as full as possible — greedy
        accumulation of lines until the NEXT line would push embedding_text over
        the cap. The minimum useful piece is one import line (10 chars = 2 tokens
        of source). We assert each piece uses at least 1 token of source so the
        split is not pathological (e.g. one char per piece), and that each
        piece's embedding_text is at most the cap.

        This is a magnitude/sanity-bound check, not an exact equality assertion.
        """
        for chunk in self.chunks:
            source_tokens = approx_token_count(chunk.source_text)
            embedding_tokens = approx_token_count(chunk.embedding_text)
            # Upper bound: the embedder's hard cap (no HTTP 422).
            assert embedding_tokens <= self.HEADER_BUDGET_CAP, (
                f"{chunk.chunk_type}:{chunk.identity}#{chunk.sub_ordinal}: "
                f"embedding_text={embedding_tokens} > cap={self.HEADER_BUDGET_CAP}"
            )
            # Lower bound: at least 1 token of actual source content.
            assert source_tokens >= 1, (
                f"{chunk.chunk_type}:{chunk.identity}#{chunk.sub_ordinal}: "
                f"source_text is effectively empty ({source_tokens} tokens)"
            )

    def test_sub_ordinals_are_contiguous_from_zero(self) -> None:
        """Each split unit's sub_ordinals run 0, 1, 2, … without gaps or duplicates."""
        for chunk_type, identity in [
            ("imports", "imports"),
            ("method", "Processor.process"),
            ("function", "compute"),
        ]:
            pieces = [
                chunk for chunk in self.chunks
                if chunk.chunk_type == chunk_type and chunk.identity == identity
            ]
            if not pieces:
                continue
            sub_ordinals = [chunk.sub_ordinal for chunk in pieces]
            assert sub_ordinals == list(range(len(pieces))), (
                f"{chunk_type}:{identity} sub_ordinals {sub_ordinals} "
                f"are not contiguous from 0"
            )


@pytest.mark.parametrize(
    "path,expected",
    [
        ("a.py", True),
        ("a.PY", True),
        ("a.txt", False),
        ("a", False),
    ],
)
def test_handles_parametrized(path: str, expected: bool) -> None:
    """Table-driven restatement of the handles contract for quick scanning."""
    assert PythonAstChunker().handles(path) is expected
