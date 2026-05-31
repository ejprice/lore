"""Contract tests for ``loremaster.symbols`` — the ``get_symbol`` read tool.

``get_symbol(qualified_name)`` is the second half of the Deliverable-3 read-tool
surface: an anti-hallucination primitive that returns the EXACT stored source of
a named Python symbol — its definition text plus its on-disk location
(file_path / line span / tier) — looked up by its qualified name. Where
``read_file`` answers "show me lines N..M of this file", ``get_symbol`` answers
"show me the definition of ``Calculator.add``" without the caller knowing where
it lives.

The lookup is a **filter-only** store query (no query vector): a symbol is found
by matching the chunk's payload ``identity`` (the python_ast qualified name —
``ClassName``, ``ClassName.method``, or a bare ``function``) against
``qualified_name``, scoped to the Python symbol chunk types
(``class`` / ``method`` / ``function``) so a same-named ``imports`` block or a
fallback ``python_window`` never masquerades as a symbol. This requires a new
filter-only ``scroll`` primitive on :class:`~loremaster.store.qdrant.QdrantStore`
(the store today exposes only the vector-based ``search``).

The tests run against the REAL local Qdrant (the PID-safe ``qdrant_client``
fixture from ``conftest.py``, self-scoped, no global sweep) and embed real
python_ast chunks of a REAL source string with a :class:`FakeEmbedder`, so the
stored ``identity`` / ``chunk_type`` / ``source_text`` / line span are exactly
what the production chunker emits — ground truth, not invented fixtures.
"""

from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from loremaster.index.records import chunk_to_record, sha512_hex
from loremaster.store.qdrant import QdrantStore
from loremaster.symbols import GetSymbolError, ResolvedSymbol, SymbolTool
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

_DIM = 8
_SLUG = "demo"
_TIER = "custom"
_FILE_PATH = "pkg/calc.py"

# A REAL source string the production python_ast chunker splits. The symbols it
# yields (and their identities) are the ground-truth oracle the tests assert
# against — see the values pinned in ``_EXPECTED_*`` below.
_SOURCE = '''"""Module docstring."""
import os


class Calculator:
    """A small calculator."""

    def add(self, a, b):
        """Return the sum."""
        return a + b

    def subtract(self, a, b):
        """Return the difference."""
        return a - b


def helper(value):
    """A free function."""
    return value * 2
'''

# Ground-truth symbol identities/types the chunker emits for ``_SOURCE`` (pinned
# by inspecting the real chunker output, not re-derived from the lookup logic).
_EXPECTED_METHOD = "Calculator.add"
_EXPECTED_CLASS = "Calculator"
_EXPECTED_FUNCTION = "helper"


def _unique_slug() -> str:
    """A per-test slug → collection ``lore_test_<pid>_<uuid4>`` (PID-scoped teardown)."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


def _real_chunks() -> list[Chunk]:
    """Chunk ``_SOURCE`` through the production python_ast chunker."""
    embedder = FakeEmbedder(dim=_DIM)
    ctx = ChunkContext(
        slug=_SLUG,
        file_path=_FILE_PATH,
        count_tokens=lambda text: embedder.count_tokens([text])[0],
        max_input_tokens=embedder.max_input_tokens,
    )
    return PythonAstChunker().chunk(_SOURCE, ctx)


async def _upsert_real_symbols(store: QdrantStore) -> None:
    """Embed + upsert every real chunk of ``_SOURCE`` under ``_TIER``."""
    embedder = FakeEmbedder(dim=_DIM)
    await store.ensure_collection(_DIM)
    chunks = _real_chunks()
    content_hash = sha512_hex(_SOURCE)
    records = [
        chunk_to_record(
            chunk,
            slug=_SLUG,
            tier=_TIER,
            file_path=_FILE_PATH,
            content_hash=content_hash,
            mtime_ns=0,
        )
        for chunk in chunks
    ]
    result = await embedder.embed_documents([record.embedding_text for record in records])
    vectors = [vector for vector in result.vectors if vector is not None]
    await store.upsert(list(zip(records, vectors, strict=True)))


@pytest_asyncio.fixture()
async def store(qdrant_client: AsyncQdrantClient) -> QdrantStore:
    """A QdrantStore on a fresh throwaway collection on the REAL server."""
    return QdrantStore(client=qdrant_client, slug=_unique_slug())


@pytest_asyncio.fixture()
async def tool(store: QdrantStore) -> SymbolTool:
    """A SymbolTool over a store pre-loaded with the real symbols of ``_SOURCE``."""
    await _upsert_real_symbols(store)
    return SymbolTool(store=store)


class TestGetSymbolMethod:
    """A qualified ``Class.method`` resolves to its exact stored definition."""

    async def test_resolves_method_source_and_location(self, tool: SymbolTool) -> None:
        resolved: ResolvedSymbol = await tool.get_symbol(_EXPECTED_METHOD)
        # The source is the EXACT method definition the chunker stored — its body
        # is present and it is the add method, not subtract.
        assert "def add(self, a, b):" in resolved.source
        assert "return a + b" in resolved.source
        assert "subtract" not in resolved.source
        # Location is the real on-disk anchor.
        assert resolved.file_path == _FILE_PATH
        assert resolved.tier == _TIER
        assert resolved.chunk_type == "method"
        assert resolved.qualified_name == _EXPECTED_METHOD

    async def test_method_line_span_matches_the_real_chunk(self, tool: SymbolTool) -> None:
        # The reported line span equals the chunker's own span for the method, so
        # a downstream read_file(tier, path, line_start, line_end) round-trips.
        chunks = _real_chunks()
        expected = next(
            chunk for chunk in chunks if chunk.identity == _EXPECTED_METHOD
        )
        resolved = await tool.get_symbol(_EXPECTED_METHOD)
        assert resolved.line_start == expected.line_start
        assert resolved.line_end == expected.line_end


class TestGetSymbolClassAndFunction:
    """Class headers and free functions resolve, scoped to symbol chunk types."""

    async def test_resolves_class_header(self, tool: SymbolTool) -> None:
        resolved = await tool.get_symbol(_EXPECTED_CLASS)
        assert "class Calculator:" in resolved.source
        assert resolved.chunk_type == "class"

    async def test_resolves_free_function(self, tool: SymbolTool) -> None:
        resolved = await tool.get_symbol(_EXPECTED_FUNCTION)
        assert "def helper(value):" in resolved.source
        assert "return value * 2" in resolved.source
        assert resolved.chunk_type == "function"

    async def test_class_lookup_does_not_return_a_method(self, tool: SymbolTool) -> None:
        # "Calculator" is the class, NOT "Calculator.add" — the bare class name
        # must resolve to the class header, never a method that merely shares the
        # class prefix.
        resolved = await tool.get_symbol(_EXPECTED_CLASS)
        assert resolved.qualified_name == _EXPECTED_CLASS
        assert "def add" not in resolved.source


class TestGetSymbolModuleQualifiedName:
    """A caller's MODULE-qualified dotted name resolves to the bare stored identity.

    The python_ast chunker stores only the *within-file* identity (``Calculator``,
    ``Calculator.add``, ``helper``) — the module path lives in ``file_path``, never
    in ``identity``. But a real caller naturally passes the FULL dotted name
    (``pkg.calc.Calculator.add``), often with the package directory repeated in the
    path (``loremaster.loremaster...``). ``get_symbol`` must resolve those forms to
    the bare stored identity, anchored to the matching module file, without a
    re-index. ``_FILE_PATH`` is ``pkg/calc.py`` → module path ``pkg.calc``.
    """

    async def test_module_qualified_method_resolves(self, tool: SymbolTool) -> None:
        # The real-world failing shape: a fully module-qualified Class.method name.
        resolved = await tool.get_symbol(f"pkg.calc.{_EXPECTED_METHOD}")
        assert resolved.qualified_name == _EXPECTED_METHOD
        assert resolved.chunk_type == "method"
        assert "def add(self, a, b):" in resolved.source
        assert "subtract" not in resolved.source
        assert resolved.file_path == _FILE_PATH

    async def test_module_qualified_class_resolves(self, tool: SymbolTool) -> None:
        resolved = await tool.get_symbol(f"pkg.calc.{_EXPECTED_CLASS}")
        assert resolved.qualified_name == _EXPECTED_CLASS
        assert resolved.chunk_type == "class"
        assert "class Calculator:" in resolved.source
        assert "def add" not in resolved.source

    async def test_module_qualified_function_resolves(self, tool: SymbolTool) -> None:
        resolved = await tool.get_symbol(f"pkg.calc.{_EXPECTED_FUNCTION}")
        assert resolved.qualified_name == _EXPECTED_FUNCTION
        assert resolved.chunk_type == "function"
        assert "def helper(value):" in resolved.source

    async def test_repeated_package_prefix_resolves(self, tool: SymbolTool) -> None:
        # The reported bug: the caller doubles the package directory in the path
        # (``loremaster.loremaster...``). A longer-than-the-file dotted prefix whose
        # tail still path-matches ``file_path`` must still resolve.
        resolved = await tool.get_symbol(f"src.pkg.calc.{_EXPECTED_CLASS}")
        assert resolved.qualified_name == _EXPECTED_CLASS
        assert resolved.chunk_type == "class"

    async def test_wrong_module_prefix_does_not_resolve(self, tool: SymbolTool) -> None:
        # The bare identity ``Calculator`` exists, but not under module ``other.mod``.
        # A module-qualified name whose prefix does NOT path-match the symbol's file
        # must be a clean not-found — never a cross-module wrong hit.
        with pytest.raises(GetSymbolError):
            await tool.get_symbol(f"other.mod.{_EXPECTED_CLASS}")


class TestRepeatedPackageDirBug:
    """The exact reported failure: a deep file path with a repeated package dir.

    Mirrors ``loremaster/loremaster/index/indexer.py`` defining class ``Indexer``,
    where callers passed BOTH the under-qualified ``loremaster.index.indexer.Indexer``
    (no repeated package dir) and the over-qualified
    ``loremaster.loremaster.index.indexer.Indexer`` — neither resolved. Both forms
    must now resolve to the same stored ``Indexer`` via the common-tail module rule.
    """

    _DEEP_FILE_PATH = "loremaster/loremaster/index/indexer.py"
    _DEEP_SOURCE = '''"""Indexer module."""


class Indexer:
    """The orchestrating indexer."""

    def run(self):
        """Drive a pass."""
        return 1
'''

    @pytest_asyncio.fixture()
    async def deep_tool(self, qdrant_client: AsyncQdrantClient) -> SymbolTool:
        """A SymbolTool over a store holding ``Indexer`` at the deep, repeated path."""
        store = QdrantStore(client=qdrant_client, slug=_unique_slug())
        embedder = FakeEmbedder(dim=_DIM)
        await store.ensure_collection(_DIM)
        ctx = ChunkContext(
            slug=_SLUG,
            file_path=self._DEEP_FILE_PATH,
            count_tokens=lambda text: embedder.count_tokens([text])[0],
            max_input_tokens=embedder.max_input_tokens,
        )
        chunks = PythonAstChunker().chunk(self._DEEP_SOURCE, ctx)
        content_hash = sha512_hex(self._DEEP_SOURCE)
        records = [
            chunk_to_record(
                chunk,
                slug=_SLUG,
                tier=_TIER,
                file_path=self._DEEP_FILE_PATH,
                content_hash=content_hash,
                mtime_ns=0,
            )
            for chunk in chunks
        ]
        result = await embedder.embed_documents([record.embedding_text for record in records])
        vectors = [vector for vector in result.vectors if vector is not None]
        await store.upsert(list(zip(records, vectors, strict=True)))
        return SymbolTool(store=store)

    async def test_under_qualified_form_resolves(self, deep_tool: SymbolTool) -> None:
        # No repeated package dir — caller module path is SHORTER than the file's.
        resolved = await deep_tool.get_symbol("loremaster.index.indexer.Indexer")
        assert resolved.qualified_name == "Indexer"
        assert resolved.chunk_type == "class"
        assert "class Indexer:" in resolved.source

    async def test_over_qualified_form_resolves(self, deep_tool: SymbolTool) -> None:
        # Repeated package dir — caller module path EQUALS the file's full path.
        resolved = await deep_tool.get_symbol("loremaster.loremaster.index.indexer.Indexer")
        assert resolved.qualified_name == "Indexer"
        assert resolved.chunk_type == "class"

    async def test_deep_method_resolves(self, deep_tool: SymbolTool) -> None:
        resolved = await deep_tool.get_symbol("loremaster.index.indexer.Indexer.run")
        assert resolved.qualified_name == "Indexer.run"
        assert resolved.chunk_type == "method"
        assert "def run(self):" in resolved.source


class TestCollidingIdentityAcrossFiles:
    """A bare identity that COLLIDES across files resolves to the CORRECT file.

    The python_ast chunker stamps the same within-file ``identity`` for two
    distinct symbols that merely share a name in different modules — a real prod
    collision: class ``EmbeddingConfig`` lives in BOTH
    ``loremaster/loremaster/config.py`` and ``loresigil/loresigil/factory.py``
    (and function ``main`` in both ``server.py`` and ``index/cli.py``). A scroll
    on the bare identity returns ALL of them; a module-qualified lookup must pick
    the sibling whose ``file_path`` matches the caller's module path, regardless of
    scroll order — NOT just the first-scrolled point. Both fully-qualified forms
    must resolve to THEIR own file; neither sibling may be unreachable.
    """

    _SLUG_A = "loremaster"
    _FILE_A = "loremaster/loremaster/config.py"
    _SOURCE_A = '''"""loremaster config module."""


class EmbeddingConfig:
    """The loremaster embedding config."""

    MARKER_A = "loremaster-config-marker"
'''

    _FILE_B = "loresigil/loresigil/factory.py"
    _SOURCE_B = '''"""loresigil factory module."""


class EmbeddingConfig:
    """The loresigil embedding config."""

    MARKER_B = "loresigil-factory-marker"
'''

    @staticmethod
    async def _upsert_file(store: QdrantStore, *, file_path: str, source: str) -> None:
        """Chunk + embed + upsert one real file's symbols into ``store``."""
        embedder = FakeEmbedder(dim=_DIM)
        ctx = ChunkContext(
            slug=_SLUG,
            file_path=file_path,
            count_tokens=lambda text: embedder.count_tokens([text])[0],
            max_input_tokens=embedder.max_input_tokens,
        )
        chunks = PythonAstChunker().chunk(source, ctx)
        content_hash = sha512_hex(source)
        records = [
            chunk_to_record(
                chunk,
                slug=_SLUG,
                tier=_TIER,
                file_path=file_path,
                content_hash=content_hash,
                mtime_ns=0,
            )
            for chunk in chunks
        ]
        result = await embedder.embed_documents([record.embedding_text for record in records])
        vectors = [vector for vector in result.vectors if vector is not None]
        await store.upsert(list(zip(records, vectors, strict=True)))

    @pytest_asyncio.fixture()
    async def colliding_tool(self, qdrant_client: AsyncQdrantClient) -> SymbolTool:
        """A SymbolTool over a store holding TWO files that share identity ``EmbeddingConfig``."""
        store = QdrantStore(client=qdrant_client, slug=_unique_slug())
        await store.ensure_collection(_DIM)
        await self._upsert_file(store, file_path=self._FILE_A, source=self._SOURCE_A)
        await self._upsert_file(store, file_path=self._FILE_B, source=self._SOURCE_B)
        return SymbolTool(store=store)

    async def test_first_sibling_resolves_to_its_own_file(
        self, colliding_tool: SymbolTool
    ) -> None:
        resolved = await colliding_tool.get_symbol("loremaster.config.EmbeddingConfig")
        assert resolved.file_path == self._FILE_A
        assert "loremaster-config-marker" in resolved.source
        assert "loresigil-factory-marker" not in resolved.source

    async def test_other_sibling_resolves_to_its_own_file(
        self, colliding_tool: SymbolTool
    ) -> None:
        # The non-first-scrolled sibling: with a ``points[0]``-only lookup this
        # 404s (or returns the wrong file) — the recall gap the audit caught.
        resolved = await colliding_tool.get_symbol("loresigil.factory.EmbeddingConfig")
        assert resolved.file_path == self._FILE_B
        assert "loresigil-factory-marker" in resolved.source
        assert "loremaster-config-marker" not in resolved.source

    async def test_neither_collision_form_cross_contaminates(
        self, colliding_tool: SymbolTool
    ) -> None:
        # Both fully-qualified forms resolve, each to its OWN file — proving neither
        # sibling is unreachable and the choice is not scroll-order roulette.
        from_a = await colliding_tool.get_symbol("loremaster.config.EmbeddingConfig")
        from_b = await colliding_tool.get_symbol("loresigil.factory.EmbeddingConfig")
        assert {from_a.file_path, from_b.file_path} == {self._FILE_A, self._FILE_B}


class TestUnknownSymbol:
    """An unknown qualified name is a clean not-found, never a wrong hit."""

    async def test_unknown_symbol_raises_clean_not_found(self, tool: SymbolTool) -> None:
        with pytest.raises(GetSymbolError):
            await tool.get_symbol("Calculator.nonexistent_method")

    async def test_imports_block_is_not_a_symbol(self, tool: SymbolTool) -> None:
        # The python_ast chunker stamps an ``imports`` chunk with identity
        # "imports" — but it is NOT a code symbol, so get_symbol("imports") must
        # be a clean not-found, not a leak of the import block as a "symbol".
        with pytest.raises(GetSymbolError):
            await tool.get_symbol("imports")


class TestStoreScrollPrimitive:
    """The new filter-only ``scroll`` primitive QdrantStore.get_symbol relies on.

    ``get_symbol`` cannot use the vector-based ``search`` (it has no query
    vector) — it needs a filter-only lookup. This pins that primitive directly.
    """

    async def test_scroll_filters_by_identity_and_chunk_type(self, store: QdrantStore) -> None:
        await _upsert_real_symbols(store)
        # Exact-match on identity + chunk_type returns exactly the method point.
        points = await store.scroll(
            filters={"identity": _EXPECTED_METHOD, "chunk_type": "method"}, limit=10
        )
        assert len(points) == 1
        payload = points[0].payload
        assert payload is not None
        assert payload["identity"] == _EXPECTED_METHOD
        assert payload["chunk_type"] == "method"
        assert payload["source_text"]  # the stored definition text is carried

    async def test_scroll_returns_empty_for_no_match(self, store: QdrantStore) -> None:
        await _upsert_real_symbols(store)
        points = await store.scroll(
            filters={"identity": "does.not.Exist", "chunk_type": "method"}, limit=10
        )
        assert points == []

    async def test_scroll_does_not_cross_chunk_types(self, store: QdrantStore) -> None:
        # Filtering for identity "imports" under a SYMBOL chunk type yields nothing
        # — the imports chunk's chunk_type is "imports", not class/method/function.
        await _upsert_real_symbols(store)
        for symbol_type in ("class", "method", "function"):
            points = await store.scroll(
                filters={"identity": "imports", "chunk_type": symbol_type}, limit=10
            )
            assert points == [], f"imports must not match chunk_type {symbol_type!r}"
