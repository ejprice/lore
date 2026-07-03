"""Contract tests for ``loremaster.map.MapEngine`` — the P6-tail map verb.

``lore_map`` (plan §5) is the one-call answer to "orient me in this codebase" —
a token-budgeted, rank-ordered rollup of modules instead of a directory dump.

Contract decisions THIS file transcribes (GIVEN by team-lead as contract
owner, a twice-stalled takeover — this session's role is faithful
transcription of the design below, NOT re-design):

* Engine: ``MapEngine`` in a NEW ``loremaster/loremaster/map.py`` — a pure
  read layer over the code graph. Constructor (keyword-only):
  ``MapEngine(*, graph, count_tokens, rebuild_notice=None)`` where
  ``count_tokens`` is a single-string token estimator (``Callable[[str],
  int]``, no default — the caller MUST supply one, mirroring the real
  chunker's own token-budget convention) and ``rebuild_notice`` is an async
  callable returning ``None`` (settled) or a human-readable notice string (a
  rebuild is in progress), exactly as ``ImpactEngine`` defines it.
* Query: ``await engine.map(budget=1500, focus=None) -> MapResult``.
  ``budget`` clamps to ``[200, 6000]`` (floor 200, default 1500, cap 6000) —
  clamp, never raise, the same tool-surface convention ``ImpactEngine`` uses
  for ``depth``.
* ``MapResult`` (pydantic, ``extra="forbid"``): ``entries`` (list of
  ``MapEntry``), ``elided_modules`` (count of modules squeezed out by
  ``budget`` — explicit, never silent), ``formatted`` (the token-compact
  rendered block). ``MapEntry`` (pydantic, ``extra="forbid"``): ``module``,
  ``rank`` (a PageRank-derived float), ``symbols`` (the module's rendered
  symbol names).
* Ordering: entries sort by ``rank`` DESC, ties broken by ``module`` ASC.
  Tests pin this ORDERING behaviourally (position comparisons, hub-vs-leaf,
  focus-vs-unfocused) — NEVER an exact eigenvector value, which is an
  implementation artifact, not a contract.
* Elision trailer: when ``budget`` squeezes modules out of the rendered
  block, ``formatted`` carries the fragment ``"modules elided (budget"``
  together with a POSITIVE ``elided_modules`` count; the fragment is ABSENT
  when the whole corpus fits (no-silent-caps doctrine, mirrors
  ``ImpactEngine``'s ``"more (elided"`` marker).
* Rebuilding: a non-None ``rebuild_notice()`` result makes ``map()`` raise
  ``MapRebuildingError`` whose message carries the notice AND a retry hint
  ("retry") — verdict-bearing (rank-bearing) outputs are never served
  mid-rebuild, exactly as ``ImpactEngine`` gates ``impact()``.
* Unknown focus (never indexed): ``MapFocusNotFoundError`` naming the focus
  and pointing at a next step ("search_code") — the teaching-miss standard
  (mirrors ``ImpactTargetNotFoundError`` / ``GetSymbolError``).
* Determinism: two identical calls over an unchanged graph produce
  byte-identical ``formatted`` output.

Focus-resolution convention (my transcription choice, per team-lead's "pick
whichever the graph resolves, state which"): ``focus`` is passed as a BARE
symbol name — ``"island_fn"``, not the qualified ``"island.island_fn"`` nor
the module name ``"island"``. This mirrors ``ImpactEngine``'s established
target convention (``test_impact._TARGET = "champion_routing"``, a bare
function name resolved against the same graph) rather than inventing a new
resolution style for a sibling read-layer engine over the same graph.

Expected RED: ``loremaster.map`` does not exist yet. The import happens
lazily inside the ``engine_factory`` fixture, so the file COLLECTS cleanly
and every test fails behaviourally (``ModuleNotFoundError`` at call time),
never as a file-level collection collapse.
"""

from __future__ import annotations

import importlib
import uuid
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from _surreal_fakes import FakeSurrealTrio, fake_surreal_trio
from loremaster.config import LoreConfig
from loremaster.server import LoreServer
from lorescribe.astroid_parse import clear_resolution_cache, reset_search_path_memo
from lorescribe.models import ChunkContext

_DIM = 2048
_TIER = "custom"


@pytest.fixture(autouse=True)
def _reset_astroid_resolution_state() -> Iterator[None]:
    """Reset astroid's process-global resolution state around EVERY test here.

    Every test builds a RESOLUTION-enabled :class:`CodeGraph` via
    ``_build_graph`` (the chunk->resolution seam, with tier/project roots) and
    asserts the in-project reference edges survive. astroid's manager (module
    cache + import-spec caches) and this package's ``sys.path`` /
    package-parent-dir memo are PROCESS-GLOBAL. Production bounds them at SWEEP
    boundaries (the indexer resets once per full sweep via
    :meth:`CodeGraph.reset_resolution_cache`) and the graph no longer wipes the
    cache per file -- so a graph built OUTSIDE a sweep, as these tests do,
    inherits whatever residue an earlier test left in the shared manager (every
    test reuses the SAME module names under a fresh ``tmp_path``). Without this
    autouse reset that residue degrades the corpus's cross-module resolution to a
    bare name (zero reference edges) and the reference-count assertions fail
    purely by test ORDER. Resetting before AND after each test keeps every case
    hermetic regardless of order or selection.
    """
    clear_resolution_cache()
    reset_search_path_memo()
    yield
    clear_resolution_cache()
    reset_search_path_memo()

# --------------------------------------------------------------------------- #
# Contract constants THIS module DEFINES (reported for team-lead/audit review).
# --------------------------------------------------------------------------- #

# Budget clamps (GIVEN: floor 200, default 1500, cap 6000).
_BUDGET_FLOOR = 200
_BUDGET_DEFAULT = 1500
_BUDGET_CAP = 6000

# The explicit elision-trailer fragment rendered when ``budget`` squeezes
# modules out of the formatted block (no-silent-caps doctrine).
_ELISION_FRAGMENT = "modules elided (budget"

# The retry hint every rebuilding error must carry.
_RETRY_FRAGMENT = "retry"

# The teaching-miss next-step fragment every unknown-focus error must carry.
_TEACHING_MISS_FRAGMENT = "search_code"

# Token estimator reused verbatim from the established chunker convention
# (identical lambda to ``ChunkContext.count_tokens`` in ``test_impact.py`` /
# the real indexer) — NOT an invented ratio, the same char/4 estimate the
# production chunk pipeline already uses for budget accounting.
_DEFAULT_COUNT_TOKENS: Callable[[str], int] = lambda text: max(1, len(text) // 4)  # noqa: E731

# Proxy pin against raw dumps (mirrors test_impact's ``< 40`` line pin).
_MAX_FORMATTED_LINES = 40


# --------------------------------------------------------------------------- #
# Corpus — a hub-and-spoke module PLUS an island, pinned BY CONSTRUCTION.
# --------------------------------------------------------------------------- #
# hub.py: the global hub — three production importers (a/b/c) all call it,
# so it must dominate an UNFOCUSED, whole-graph PageRank.
_HUB_SOURCE = """\
def shared_util(x):
    \"\"\"The shared utility every importer in this corpus calls.\"\"\"
    return x
"""

_A_SOURCE = """\
from hub import shared_util


def use_a(x):
    \"\"\"A production caller of the shared hub utility.\"\"\"
    return shared_util(x)
"""

_B_SOURCE = """\
from hub import shared_util


def use_b(x):
    \"\"\"A second production caller of the shared hub utility.\"\"\"
    return shared_util(x)
"""

_C_SOURCE = """\
from hub import shared_util


def use_c(x):
    \"\"\"A third production caller of the shared hub utility.\"\"\"
    return shared_util(x)
"""

# island.py / island_user.py: a two-module neighborhood referenced by
# exactly ONE other file — globally subordinate to the hub, but dominant
# within its own focused neighborhood.
_ISLAND_SOURCE = """\
def island_fn(x):
    \"\"\"Referenced by exactly one file across the whole corpus.\"\"\"
    return x
"""

_ISLAND_USER_SOURCE = """\
from island import island_fn


def use_island(x):
    \"\"\"The lone caller of island_fn -- the island's only neighbor.\"\"\"
    return island_fn(x)
"""

_HUB_MODULE = "hub"
_ISLAND_MODULE = "island"
_ISLAND_USER_MODULE = "island_user"
_FOCUS_SYMBOL = "island_fn"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _slug() -> str:
    return f"test_{uuid.uuid4().hex}"


def _config(*, slug: str, live_path: Path) -> LoreConfig:
    """A validated config with one live tier (mirrors test_impact's fixture)."""
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "roots": [
            {"tier": _TIER, "watch": "live", "path": str(live_path), "include": ["**/*.py"]}
        ],
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
    }
    return LoreConfig.model_validate(payload)


def _chunks_for(server: LoreServer, rel_path: str, source: str) -> list[Any]:
    """Run ``source`` through the REAL chunker registry (the graph's producer)."""
    ctx = ChunkContext(
        slug="oracle",
        file_path=rel_path,
        count_tokens=_DEFAULT_COUNT_TOKENS,
        max_input_tokens=8192,
    )
    return server.registry.dispatch_file(rel_path, source, ctx)


async def _build_graph(
    tmp_path: Path, files: dict[str, str]
) -> tuple[FakeSurrealTrio, LoreServer]:
    """Write ``files``, chunk them for real, and build the fake graph.

    Map is a pure GRAPH read — no store/embedding work is needed, so the
    fixture builds only the graph slice (chunk → build_file_graph), keeping
    every test sub-second (mirrors ``test_impact._build_graph`` exactly).
    """
    slug = _slug()
    for rel_path, source in files.items():
        _write(tmp_path / rel_path, source)
    config = _config(slug=slug, live_path=tmp_path)
    server = LoreServer(config)
    trio = fake_surreal_trio(
        dim=_DIM, tier_roots={_TIER: tmp_path}, project_roots=[tmp_path]
    )
    for rel_path, source in files.items():
        await trio.graph.build_file_graph(_TIER, rel_path, _chunks_for(server, rel_path, source))
    return trio, server


def _full_corpus() -> dict[str, str]:
    return {
        "hub.py": _HUB_SOURCE,
        "a.py": _A_SOURCE,
        "b.py": _B_SOURCE,
        "c.py": _C_SOURCE,
        "island.py": _ISLAND_SOURCE,
        "island_user.py": _ISLAND_USER_SOURCE,
    }


def _index_of_module(entries: list[Any], module: str) -> int:
    """Locate ``module`` in a ``MapResult.entries`` list, or fail loudly."""
    for index, entry in enumerate(entries):
        if entry.module == module:
            return index
    modules = [entry.module for entry in entries]
    raise AssertionError(f"module {module!r} not found in entries: {modules}")


@pytest.fixture()
def engine_factory() -> Callable[..., Any]:
    """Build a ``MapEngine`` via a LAZY import (behavioural red, not
    collection collapse): the module under contract does not exist yet."""

    def _build(
        graph: Any,
        *,
        count_tokens: Callable[[str], int] = _DEFAULT_COUNT_TOKENS,
        rebuild_notice: Callable[[], Awaitable[str | None]] | None = None,
    ) -> Any:
        map_module = importlib.import_module("loremaster.map")
        return map_module.MapEngine(
            graph=graph, count_tokens=count_tokens, rebuild_notice=rebuild_notice
        )

    return _build


def _errors() -> Any:
    """The engine's typed errors, imported lazily for the same reason."""
    return importlib.import_module("loremaster.map")


# --------------------------------------------------------------------------- #
# 1 — global (unfocused) ranking: the hub dominates
# --------------------------------------------------------------------------- #
class TestGlobalRanking:
    """Contract: an unfocused map ranks the most-imported module first."""

    async def test_hub_outranks_leaf_globally(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange: hub.py is imported by three modules (a/b/c); island.py by
        # exactly one (island_user.py) -- hub must dominate global PageRank.
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        # Act
        result = await engine.map(budget=_BUDGET_CAP)

        # Assert: a POSITION comparison, never an eigenvector value.
        hub_index = _index_of_module(result.entries, _HUB_MODULE)
        island_index = _index_of_module(result.entries, _ISLAND_MODULE)
        assert hub_index < island_index, (
            "hub is imported by three modules; island by one -- hub must "
            "rank ahead of island in an unfocused, whole-graph map"
        )


# --------------------------------------------------------------------------- #
# 2 — focused ranking: focus flips the ordering toward its neighborhood
# --------------------------------------------------------------------------- #
class TestFocusedRanking:
    """Contract: focusing the map re-centers rank on a symbol's neighborhood."""

    async def test_focus_flips_the_ordering(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        # Act: focus on the island's own symbol -- its two-module
        # neighborhood must outrank the globally-dominant hub.
        result = await engine.map(budget=_BUDGET_CAP, focus=_FOCUS_SYMBOL)

        # Assert
        hub_index = _index_of_module(result.entries, _HUB_MODULE)
        island_index = _index_of_module(result.entries, _ISLAND_MODULE)
        island_user_index = _index_of_module(result.entries, _ISLAND_USER_MODULE)
        assert island_index < hub_index, (
            "focusing on island_fn must promote its own module above the "
            "globally-dominant hub"
        )
        assert island_user_index < hub_index, (
            "focusing on island_fn must promote its caller's module above "
            "the globally-dominant hub too"
        )


# --------------------------------------------------------------------------- #
# 3/4/5 — budget enforcement: honored, elided-or-not, and clamped
# --------------------------------------------------------------------------- #
class TestBudgetEnforcement:
    """Contract: ``budget`` bounds ``formatted`` and elides explicitly."""

    async def test_budget_is_honored_by_injected_counter(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange: inject the SAME estimator the assertion re-applies, so the
        # bound is checked against the exact counter the engine was told to
        # use -- never a different unit than the one the engine enforces.
        # The counter counts chars-as-tokens (not char/4): at the 200-token
        # floor, six one-symbol modules rendered honestly (~300+ chars each)
        # genuinely overflow the budget, so `elided_modules > 0` is
        # satisfiable without padding the render to force an elision.
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph, count_tokens=lambda s: len(s))

        # Act
        result = await engine.map(budget=_BUDGET_FLOOR)

        # Assert
        assert _DEFAULT_COUNT_TOKENS(result.formatted) <= _BUDGET_FLOOR
        assert result.elided_modules > 0, (
            "six modules cannot fit in a 200-token budget -- some must be "
            "elided, and the count must say so explicitly"
        )
        assert _ELISION_FRAGMENT in result.formatted

    async def test_generous_budget_elides_nothing(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        # Act
        result = await engine.map(budget=_BUDGET_CAP)

        # Assert: this tiny six-module corpus fits comfortably in 6000 tokens.
        assert result.elided_modules == 0
        assert _ELISION_FRAGMENT not in result.formatted

    @pytest.mark.parametrize(
        "requested,expect_elision",
        [
            pytest.param(1, True, id="below-floor-clamps-to-200"),
            pytest.param(999_999, False, id="above-cap-clamps-to-6000"),
        ],
    )
    async def test_budget_clamps(
        self,
        tmp_path: Path,
        engine_factory: Callable[..., Any],
        requested: int,
        expect_elision: bool,
    ) -> None:
        # Clamp, never raise -- the same tool-surface convention
        # ImpactEngine uses for depth. A requested budget of 1 clamps to the
        # floor (200, same elision behavior as the floor test above); a
        # requested budget of 999_999 clamps to the cap (6000, same
        # no-elision behavior as the generous-budget test above). The counter
        # counts chars-as-tokens (len(s), the SAME estimator
        # test_budget_is_honored_by_injected_counter injects), so the
        # clamped-floor case genuinely overflows 200 tokens over six
        # honestly-rendered one-symbol modules -- elision without padding the
        # render (the char/4 default would demand ~800 chars, unreachable
        # honestly for this tiny corpus).
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph, count_tokens=lambda s: len(s))

        result = await engine.map(budget=requested)

        assert (result.elided_modules > 0) is expect_elision
        assert (_ELISION_FRAGMENT in result.formatted) is expect_elision


# --------------------------------------------------------------------------- #
# 6 — deterministic ordering rule: rank DESC, then module ASC
# --------------------------------------------------------------------------- #
class TestOrdering:
    """Contract: entries sort by rank DESC, ties broken by module ASC."""

    async def test_entries_ordered_rank_desc_then_module_asc(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange: a/b/c each import ONLY hub with an identical reference
        # shape -- by construction they are the tie-break case.
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        # Act
        result = await engine.map(budget=_BUDGET_CAP)

        # Assert: rank is non-increasing across the list...
        ranks = [entry.rank for entry in result.entries]
        assert ranks == sorted(ranks, reverse=True), "rank must be non-increasing"
        # ...and any rank tie breaks by module name ascending.
        for previous, current in zip(result.entries, result.entries[1:]):
            if previous.rank == current.rank:
                assert previous.module < current.module, (
                    "ties in rank must break by module name ascending"
                )


# --------------------------------------------------------------------------- #
# 7/8 — rank-bearing output is never served mid-rebuild
# --------------------------------------------------------------------------- #
class TestRebuildingGate:
    """Contract: a non-None rebuild probe blocks ``map()``; None serves it."""

    async def test_rebuilding_probe_blocks_the_map(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        notice = "graph rebuilding: 4/226 files"

        async def _rebuilding() -> str | None:
            return notice

        engine = engine_factory(trio.graph, rebuild_notice=_rebuilding)

        # Act / Assert
        with pytest.raises(_errors().MapRebuildingError) as exc_info:
            await engine.map(budget=_BUDGET_DEFAULT)
        message = str(exc_info.value)
        assert notice in message
        assert _RETRY_FRAGMENT in message.lower()

    async def test_settled_probe_serves(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange
        trio, _server = await _build_graph(tmp_path, _full_corpus())

        async def _settled() -> str | None:
            return None

        engine = engine_factory(trio.graph, rebuild_notice=_settled)

        # Act
        result = await engine.map(budget=_BUDGET_DEFAULT)

        # Assert: a settled probe over a populated graph serves a real map,
        # never an empty/error placeholder.
        assert result.entries
        hub_index = _index_of_module(result.entries, _HUB_MODULE)
        assert hub_index == 0, "the settled call must reach the same hub-first ranking"


# --------------------------------------------------------------------------- #
# 9 — unknown focus: the teaching miss
# --------------------------------------------------------------------------- #
class TestUnknownFocus:
    """Contract: a focus that resolves to nothing raises, naming a next step."""

    async def test_unknown_focus_teaching_miss(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        # Act / Assert
        with pytest.raises(_errors().MapFocusNotFoundError) as exc_info:
            await engine.map(budget=_BUDGET_DEFAULT, focus="totally.bogus.symbol")
        message = str(exc_info.value)
        assert "totally.bogus.symbol" in message
        assert _TEACHING_MISS_FRAGMENT in message


# --------------------------------------------------------------------------- #
# 10/11 — determinism + the compact, non-dump rendered shape
# --------------------------------------------------------------------------- #
class TestDeterminismAndShape:
    """Contract: identical calls are byte-identical; output is a rollup."""

    async def test_identical_calls_byte_identical(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        # Act
        first = await engine.map(budget=_BUDGET_DEFAULT)
        second = await engine.map(budget=_BUDGET_DEFAULT)

        # Assert
        assert first.formatted == second.formatted
        assert [entry.module for entry in first.entries] == [
            entry.module for entry in second.entries
        ]

    async def test_formatted_is_compact_rollups_not_dumps(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        # Act
        result = await engine.map(budget=_BUDGET_CAP)

        # Assert: a six-module corpus must render as compact per-module
        # lines, well under a hundred lines (a proxy pin against raw node
        # dumps), and every entry the engine reports must actually appear in
        # the rendered text (no phantom entries).
        lines = result.formatted.splitlines()
        assert len(lines) < _MAX_FORMATTED_LINES
        for entry in result.entries:
            assert entry.module in result.formatted
