"""Contract tests for ``loremaster.symbols`` — the ``get_symbol`` read tool.

``get_symbol(qualified_name)`` is the second half of the Deliverable-3 read-tool
surface: an anti-hallucination primitive that returns the EXACT stored source of
a named Python symbol — its definition text plus its on-disk location
(file_path / line span / tier) — looked up by its qualified name. Where
``read_file`` answers "show me lines N..M of this file", ``get_symbol`` answers
"show me the definition of ``Calculator.add``" without the caller knowing where
it lives.

**P6 store port (fixture/typing port, behavioural contract UNCHANGED).** This
module ports the tool's fixture story off the real Qdrant server onto the
in-memory async :class:`~_surreal_fakes.FakeSurrealStore` (built by
:func:`~_surreal_fakes.fake_surreal_trio`), cast to the real production
:class:`~loremaster.store.surreal.SurrealStore` type at the one fixture
boundary that constructs it (mirrors ``test_search.py``'s cast-to-
``SurrealManifest`` idiom), so the GREEN phase can swap ``SymbolTool``'s
``store: QdrantStore`` annotation for ``store: SurrealStore`` and every
downstream test keeps its real production type. Fixtures still index REAL
python_ast chunks of REAL source strings through the deterministic
:class:`~loresigil.testing.FakeEmbedder` — ground truth, never hand-faked
payloads — but write them through :meth:`FakeSurrealStore.upsert` instead of a
live Qdrant collection.

**RED against current code.** The lookup is a filter-only store query: a
symbol is found by matching the chunk's ``identity`` — the python_ast qualified
name — against ``qualified_name``, scoped to the Python *symbol* chunk types
(``class`` / ``method`` / ``function``). Today's ``symbols.py`` reads each
scrolled hit as ``point.payload`` — a Qdrant ``qmodels.Record`` attribute
access. :meth:`FakeSurrealStore.scroll` (like the real ``SurrealStore.scroll``
it fakes) hands back plain FLATTENED ``dict`` rows with no such wrapper, so
every one of these tests fails with ``AttributeError: 'dict' object has no
attribute 'payload'`` the moment ``get_symbol`` reaches a matched row — a
genuine behavioural RED, not a mere import/collection error. The GREEN port
reads named row KEYS directly (see :class:`TestTolerantRowReading`, which pins
that contract at the seam).

The pinned contract (unchanged from the pre-port version, plus P6 additions):

* **Exact + module-qualified resolution.** A bare stored identity resolves
  directly; a caller's fully MODULE-qualified dotted name (with or without a
  repeated package directory) resolves via the common-tail module-path rule.
* **Collision fan-out is genuinely order-independent (symbols.py:193).** A bare
  identity that collides across files must let EVERY sibling resolve by its own
  fully-qualified name, regardless of the store's scroll order —
  :class:`TestCollidingIdentityAcrossFiles` computes the fake's REAL ascending-
  point-id scroll order and explicitly queries for the sibling that a
  ``points[0]``-only bug would mask.
* **The scroll fetch is bounded, never unbounded (P6 new pin).**
  :class:`TestScrollLimitBoundary` seeds more colliding siblings than
  ``_SCROLL_LIMIT`` fetches and pins that a sibling beyond the fetched window is
  a clean not-found, not a crash or an arbitrary wrong hit — the documented
  "small ceiling guards a pathological corpus" trade-off, exercised for real.
* **Tolerant row reading (P6 new pin).** A row carrying keys ``_to_resolved``
  never reads — the real ``signature`` metadata P6's chunker now stamps, an
  unconsumed real ``llm_summary`` schema column, or an entirely unmodeled future
  key riding the FLEXIBLE ``metadata`` blob — must not break resolution.
* **Clean not-found, never a crash, never a wrong hit.** An unknown name or a
  non-symbol chunk type (``imports``) raises :class:`GetSymbolError` naming the
  qualified name and pointing at concrete next steps (``search_code`` /
  module-qualify / ``reindex``).
* **A downed store is LOUD, never a silent not-found (P6 new pin).**
  :class:`TestStoreDownIsNeverSilentNotFound` arms
  :meth:`FakeSurrealStore.arm_connection_failure` and pins that
  :class:`~loremaster.store.surreal.SurrealConnectionError` propagates out of
  ``get_symbol`` for a symbol that genuinely exists — an outage must never
  masquerade as "this symbol doesn't exist" — and that the tool recovers on the
  very next call once the armed trip is consumed (degradation -> recovery).

**OPEN QUESTION for P8 (not tested here, by design).** P6's chunker now stamps
a real rendered ``signature`` on every function/method row, but
:class:`~loremaster.symbols.ResolvedSymbol` has no ``signature`` field today
(``model_config = ConfigDict(extra="forbid")``, and ``_to_resolved`` reads only
its six named payload keys) — there is no natural place for it to flow to yet.
This file deliberately does NOT invent one; :class:`TestTolerantRowReading`
only proves the extra key's mere presence cannot break the CURRENT contract.
Whether/how a rendered signature should surface on ``ResolvedSymbol`` is left
to the P8 read-surface work.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import NamedTuple, cast

import pytest
import pytest_asyncio
from _surreal_fakes import FakeSurrealStore, fake_surreal_trio
from _surreal_harness import PRODUCTION_DIM, SLUG, TIER_A, chunk_record, unit_vector
from loremaster.index.records import Record, chunk_to_record, sha512_hex
from loremaster.store.surreal import SurrealConnectionError, SurrealStore
from loremaster.symbols import _SCROLL_LIMIT, GetSymbolError, ResolvedSymbol, SymbolTool
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker
from loresigil.testing import FakeEmbedder

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

# A key name that does not exist in the schema today, standing in for whatever
# enrichment column a future phase might add next (``metadata`` is a FLEXIBLE
# object, so an arbitrary key here is exactly how such an addition would
# really arrive on a row). Nothing asserts on its VALUE — only that its mere
# PRESENCE cannot break resolution.
_UNMODELED_FUTURE_KEY = "not_yet_a_real_column"


def _chunk_source(source: str, file_path: str, *, slug: str = SLUG) -> list[Chunk]:
    """The REAL python_ast chunker's output for ``source``.

    Used as an independent oracle for line-span assertions — never re-derived
    from the ``get_symbol`` lookup logic under test.
    """
    embedder = FakeEmbedder(dim=PRODUCTION_DIM)
    ctx = ChunkContext(
        slug=slug,
        file_path=file_path,
        count_tokens=lambda text: embedder.count_tokens([text])[0],
        max_input_tokens=embedder.max_input_tokens,
    )
    return PythonAstChunker().chunk(source, ctx)


async def _upsert_source(
    store: SurrealStore, source: str, file_path: str, *, tier: str = TIER_A, slug: str = SLUG
) -> list[Record]:
    """Chunk ``source`` through the REAL python_ast chunker, embed it with the
    deterministic :class:`FakeEmbedder`, and upsert the result into ``store``.

    Ground truth, not invented fixtures: the stored ``identity`` / ``chunk_type``
    / ``source_text`` / line span / ``signature`` are EXACTLY what the
    production chunker + :func:`chunk_to_record` emit for real Python source.

    Returns:
        The upserted records. ``.point_id`` is the SAME key
        :meth:`FakeSurrealStore.scroll` ties on, letting a test compute the
        real ascending-scroll order it will see for a set of siblings.
    """
    embedder = FakeEmbedder(dim=PRODUCTION_DIM)
    chunks = _chunk_source(source, file_path, slug=slug)
    content_hash = sha512_hex(source)
    records = [
        chunk_to_record(
            chunk, slug=slug, tier=tier, file_path=file_path,
            content_hash=content_hash, mtime_ns=0,
        )
        for chunk in chunks
    ]
    result = await embedder.embed_documents([record.embedding_text for record in records])
    vectors = [vector for vector in result.vectors if vector is not None]
    await store.upsert(list(zip(records, vectors, strict=True)))
    return records


@pytest.fixture()
def fake_store() -> FakeSurrealStore:
    """The raw fake store — used only by tests needing its fake-only control
    surface (:meth:`FakeSurrealStore.arm_connection_failure`); everything that
    drives :class:`SymbolTool` normally goes through :func:`store` instead, so
    the tool is always exercised against the real production type."""
    return fake_surreal_trio(dim=PRODUCTION_DIM).store


@pytest.fixture()
def store(fake_store: FakeSurrealStore) -> SurrealStore:
    """``fake_store`` cast to :class:`SurrealStore` — the real type
    :class:`SymbolTool` will depend on once the P6 port lands (today's
    ``QdrantStore``-typed constructor accepts it anyway; Python does not
    enforce the annotation at runtime, which is exactly what makes the
    fixture/typing port possible ahead of the implementation swap)."""
    return cast(SurrealStore, fake_store)


@pytest_asyncio.fixture()
async def tool(store: SurrealStore) -> SymbolTool:
    """A :class:`SymbolTool` over a store pre-loaded with the real symbols of ``_SOURCE``."""
    await _upsert_source(store, _SOURCE, _FILE_PATH)
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
        assert resolved.tier == TIER_A
        assert resolved.chunk_type == "method"
        assert resolved.qualified_name == _EXPECTED_METHOD

    async def test_method_line_span_matches_the_real_chunk(self, tool: SymbolTool) -> None:
        # The reported line span equals the chunker's own span for the method, so
        # a downstream read_file(tier, path, line_start, line_end) round-trips.
        chunks = _chunk_source(_SOURCE, _FILE_PATH)
        expected = next(chunk for chunk in chunks if chunk.identity == _EXPECTED_METHOD)
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
    async def deep_tool(self, store: SurrealStore) -> SymbolTool:
        """A SymbolTool over a store holding ``Indexer`` at the deep, repeated path."""
        await _upsert_source(store, self._DEEP_SOURCE, self._DEEP_FILE_PATH)
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
    ``loremaster/loremaster/config.py`` and ``loresigil/loresigil/factory.py``.
    A scroll on the bare identity returns ALL of them; a module-qualified lookup
    must pick the sibling whose ``file_path`` matches the caller's module path,
    regardless of scroll order — NOT just the first-scrolled point.
    """

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

    @pytest_asyncio.fixture()
    async def colliding_records(self, store: SurrealStore) -> tuple[Record, Record]:
        """The two files' ``EmbeddingConfig`` class records, upserted into ``store``."""
        records_a = await _upsert_source(store, self._SOURCE_A, self._FILE_A)
        records_b = await _upsert_source(store, self._SOURCE_B, self._FILE_B)
        record_a = next(r for r in records_a if r.payload["identity"] == "EmbeddingConfig")
        record_b = next(r for r in records_b if r.payload["identity"] == "EmbeddingConfig")
        return record_a, record_b

    @pytest_asyncio.fixture()
    async def colliding_tool(
        self, store: SurrealStore, colliding_records: tuple[Record, Record]
    ) -> SymbolTool:
        """A SymbolTool over a store holding TWO files that share identity ``EmbeddingConfig``."""
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

    async def test_sibling_masked_by_ascending_scroll_order_still_resolves_correctly(
        self, colliding_tool: SymbolTool, colliding_records: tuple[Record, Record]
    ) -> None:
        # ``FakeSurrealStore.scroll`` ties on ASCENDING point id (cc37a73's
        # contractual order, matching the real store's ``ORDER BY`` clause) —
        # NOT insertion order. Compute which sibling that order puts at
        # ``points[0]``: a ``_find_by_identity``/module-qualified lookup that
        # (bug-prone) trusted only ``points[0]`` would resolve EVERY query to
        # that one sibling, masking the other regardless of which module the
        # caller actually asked for. Query for the MASKED sibling explicitly —
        # genuinely order-adversarial, not just "both directions happen to work".
        record_a, record_b = colliding_records
        first_by_scroll_order, masked_by_scroll_order = sorted(
            (record_a, record_b), key=lambda record: record.point_id
        )
        assert first_by_scroll_order.point_id != masked_by_scroll_order.point_id
        masked_file = masked_by_scroll_order.payload["file_path"]
        masked_qualified_name = (
            "loremaster.config.EmbeddingConfig"
            if masked_file == self._FILE_A
            else "loresigil.factory.EmbeddingConfig"
        )

        resolved = await colliding_tool.get_symbol(masked_qualified_name)

        assert resolved.file_path == masked_file
        assert resolved.source == masked_by_scroll_order.payload["source_text"]


class TestScrollLimitBoundary:
    """SymbolTool's collision scan is bounded by ``_SCROLL_LIMIT`` — symbols.py's
    own documented ceiling ("a small ceiling guards a pathological corpus
    without an unbounded scan"). A collision within the fetched window resolves;
    one beyond it is a clean not-found, proving the tool genuinely requests a
    BOUNDED scroll and fails safely at the boundary rather than crashing or
    silently favouring an arbitrary sibling.
    """

    _SIBLING_COUNT = _SCROLL_LIMIT + 3
    _IDENTITY = "Config"
    _CHUNK_TYPE = "class"

    class _Boundary(NamedTuple):
        tool: SymbolTool
        ordered_records: list[Record]

    @pytest_asyncio.fixture()
    async def boundary(self, store: SurrealStore) -> TestScrollLimitBoundary._Boundary:
        """A tool over MORE colliding ``Config`` siblings than ``_SCROLL_LIMIT`` fetches."""
        pairs = [
            (
                chunk_record(
                    tier=TIER_A,
                    file_path=f"pkg/mod_{index}.py",
                    identity=self._IDENTITY,
                    chunk_type=self._CHUNK_TYPE,
                    source_text=f"class Config:\n    MARKER = {index}\n",
                ),
                unit_vector(0, PRODUCTION_DIM),
            )
            for index in range(self._SIBLING_COUNT)
        ]
        await store.upsert(pairs)
        ordered_records = sorted((record for record, _vector in pairs), key=lambda r: r.point_id)
        return self._Boundary(tool=SymbolTool(store=store), ordered_records=ordered_records)

    async def test_sibling_within_the_scroll_window_resolves(
        self, boundary: TestScrollLimitBoundary._Boundary
    ) -> None:
        # The SMALLEST point id is guaranteed to land inside ANY _SCROLL_LIMIT-
        # sized ascending fetch, however many siblings exist beyond it.
        within_limit = boundary.ordered_records[0]
        module = PurePosixPath(within_limit.payload["file_path"]).stem

        resolved = await boundary.tool.get_symbol(f"pkg.{module}.{self._IDENTITY}")

        assert resolved.file_path == within_limit.payload["file_path"]
        assert resolved.source == within_limit.payload["source_text"]

    async def test_sibling_beyond_the_scroll_window_is_a_clean_not_found(
        self, boundary: TestScrollLimitBoundary._Boundary
    ) -> None:
        # The LARGEST point id, with _SIBLING_COUNT > _SCROLL_LIMIT siblings,
        # sorts past index _SCROLL_LIMIT - 1 — never inside the fetched window.
        beyond_limit = boundary.ordered_records[-1]
        module = PurePosixPath(beyond_limit.payload["file_path"]).stem

        with pytest.raises(GetSymbolError):
            await boundary.tool.get_symbol(f"pkg.{module}.{self._IDENTITY}")


class TestUnknownSymbol:
    """An unknown qualified name is a clean not-found — never a wrong hit, never
    a crash — and the error itself is actionable."""

    async def test_unknown_symbol_raises_clean_not_found(self, tool: SymbolTool) -> None:
        with pytest.raises(GetSymbolError):
            await tool.get_symbol("Calculator.nonexistent_method")

    async def test_imports_block_is_not_a_symbol(self, tool: SymbolTool) -> None:
        # The python_ast chunker stamps an ``imports`` chunk with identity
        # "imports" — but it is NOT a code symbol, so get_symbol("imports") must
        # be a clean not-found, not a leak of the import block as a "symbol".
        with pytest.raises(GetSymbolError):
            await tool.get_symbol("imports")

    async def test_not_found_error_names_the_symbol_and_next_steps(
        self, tool: SymbolTool
    ) -> None:
        missing_name = "Calculator.nonexistent_method"
        with pytest.raises(GetSymbolError) as exc_info:
            await tool.get_symbol(missing_name)

        message = str(exc_info.value)
        # The anti-hallucination contract: the message must name WHAT was
        # searched for and offer concrete, actionable next steps — never a
        # bare "not found" that leaves the caller guessing.
        assert missing_name in message
        assert "search_code" in message
        assert "reindex" in message


class TestTolerantRowReading:
    """A row carrying keys ``_to_resolved`` never reads must not break
    resolution — the forward-compatible contract an open ``dict`` row demands.
    A new enrichment column lands on the row before any reader consumes it
    (P6's ``signature``, the schema's own ``llm_summary``, or something not yet
    invented riding the FLEXIBLE ``metadata`` blob); ``get_symbol`` must still
    resolve exactly as it would without the extra key.
    """

    async def test_resolves_despite_a_real_unconsumed_signature_field(
        self, store: SurrealStore
    ) -> None:
        # P6 already stamps a REAL rendered `signature` on every method/function
        # row (astroid's own as_string() composition — see chunk_to_record /
        # lorescribe.python_ast). ResolvedSymbol has no such field today; the
        # row must nonetheless resolve exactly as it would without it.
        await _upsert_source(store, _SOURCE, _FILE_PATH)
        rows = await store.scroll(
            filters={"identity": _EXPECTED_METHOD, "chunk_type": "method"}, limit=10
        )
        assert rows[0].get("signature"), "fixture sanity: the real chunker must stamp signature"
        tool = SymbolTool(store=store)

        resolved = await tool.get_symbol(_EXPECTED_METHOD)

        assert resolved.qualified_name == _EXPECTED_METHOD
        assert "def add(self, a, b):" in resolved.source

    async def test_resolves_despite_a_real_llm_summary_and_an_unmodeled_key(
        self, store: SurrealStore
    ) -> None:
        record = chunk_record(
            tier=TIER_A,
            file_path="pkg/widget.py",
            identity="Widget",
            chunk_type="class",
            source_text='class Widget:\n    """A UI widget."""\n',
            llm_summary="A reusable UI widget class.",
            metadata={_UNMODELED_FUTURE_KEY: "unmodeled-value"},
        )
        await store.upsert([(record, unit_vector(0, PRODUCTION_DIM))])
        tool = SymbolTool(store=store)

        resolved = await tool.get_symbol("Widget")

        assert resolved.qualified_name == "Widget"
        assert resolved.file_path == "pkg/widget.py"
        assert "class Widget:" in resolved.source


class TestStoreDownIsNeverSilentNotFound:
    """A downed store connection must propagate loudly, never masquerade as a
    clean not-found — the anti-hallucination boundary between "this symbol
    genuinely doesn't exist" (``GetSymbolError``) and "the store couldn't even
    answer" (``SurrealConnectionError``). Conflating the two would make an
    agent treat a transient outage as proof a real symbol was deleted.
    """

    async def test_armed_connection_failure_raises_for_a_symbol_that_exists(
        self, tool: SymbolTool, fake_store: FakeSurrealStore
    ) -> None:
        fake_store.arm_connection_failure(times=1)

        with pytest.raises(SurrealConnectionError):
            await tool.get_symbol(_EXPECTED_METHOD)

    async def test_recovers_after_the_armed_trip_is_consumed(
        self, tool: SymbolTool, fake_store: FakeSurrealStore
    ) -> None:
        # Degradation -> recovery: a single-trip arm must not permanently wedge
        # the tool — the SAME store answers correctly again right after.
        fake_store.arm_connection_failure(times=1)
        with pytest.raises(SurrealConnectionError):
            await tool.get_symbol(_EXPECTED_METHOD)

        resolved = await tool.get_symbol(_EXPECTED_METHOD)

        assert resolved.qualified_name == _EXPECTED_METHOD


class TestStoreScrollPrimitive:
    """The filter-only ``scroll`` primitive ``get_symbol`` relies on, exercised
    with REAL chunker-produced rows — the seam between the chunker/store-write
    path and the FLATTENED ``dict`` rows ``scroll`` hands back (no Qdrant
    ``Record``/``.payload`` wrapper on this store; every field is a plain key).
    """

    async def test_scroll_filters_by_identity_and_chunk_type(self, store: SurrealStore) -> None:
        await _upsert_source(store, _SOURCE, _FILE_PATH)
        # Exact-match on identity + chunk_type returns exactly the method row.
        rows = await store.scroll(
            filters={"identity": _EXPECTED_METHOD, "chunk_type": "method"}, limit=10
        )
        assert len(rows) == 1
        row = rows[0]
        assert isinstance(row, dict)
        assert row["identity"] == _EXPECTED_METHOD
        assert row["chunk_type"] == "method"
        assert row["source_text"]  # the stored definition text is carried

    async def test_scroll_returns_empty_for_no_match(self, store: SurrealStore) -> None:
        await _upsert_source(store, _SOURCE, _FILE_PATH)
        rows = await store.scroll(
            filters={"identity": "does.not.Exist", "chunk_type": "method"}, limit=10
        )
        assert rows == []

    async def test_scroll_does_not_cross_chunk_types(self, store: SurrealStore) -> None:
        # Filtering for identity "imports" under a SYMBOL chunk type yields nothing
        # — the imports chunk's chunk_type is "imports", not class/method/function.
        await _upsert_source(store, _SOURCE, _FILE_PATH)
        for symbol_type in ("class", "method", "function"):
            rows = await store.scroll(
                filters={"identity": "imports", "chunk_type": symbol_type}, limit=10
            )
            assert rows == [], f"imports must not match chunk_type {symbol_type!r}"
