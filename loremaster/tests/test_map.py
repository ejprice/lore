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
* Query: ``await engine.map(budget=2500, focus=None) -> MapResult``.
  ``budget`` clamps to ``[200, 6000]`` (floor 200, default 2500, cap 6000) —
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
from types import SimpleNamespace
from typing import Any

import pytest
from _surreal_fakes import FakeSurrealTrio, fake_surreal_trio
from loremaster.config import LoreConfig
from loremaster.graph import CodeGraph
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

# Budget clamps (GIVEN: floor 200, default 2500, cap 6000).
_BUDGET_FLOOR = 200
_BUDGET_DEFAULT = 2500  # re-denominated 2026-07-04 under 1.78 calibration, operator-approved
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
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
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
        engine = engine_factory(trio.graph, count_tokens=len)

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
        engine = engine_factory(trio.graph, count_tokens=len)

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


# =========================================================================== #
# P7-TAIL POLISH WAVE (ledger task #6) — the map test-segregation + symbol-cap
# semantic law the P8 tool-surface redesign must honor. Behavioural expectations
# below come from the BINDING spec (docs/design/2026-07-04-map-test-segregation.md
# §2-§7, incl. the 7a/7b/7c symbol-cap escape hatches) and the FRICTION.md
# receipts (2026-07-04 lore_map entries) — NEVER from how the current engine
# renders. These classes ADD pins; the existing hub/island tests above (a
# zero-test-module corpus) are untouched by the spec's changes, so none is
# migrated.
# =========================================================================== #

# --- rendering fragments the spec DEFINES (single source of truth = the design
# doc; kept as named constants so P8 may re-word rendering with one edit here). --

# §3/§4: the literal expansion affordance a caller types to include tests. This
# is the SEMANTIC token (the flag name), not a cosmetic phrase — pinned verbatim.
_TESTS_INCLUDE_AFFORDANCE = "tests=true"
# §6: the [test] tag on any test node rendering in a mixed/inverted context.
_TEST_TAG = "[test]"
# §7a: the TEACHING trailer that names its own expansion verb by name —
# ``+K more — focus=<module> for the full list``.
_SYMBOL_CAP_TEACH_VERB = "focus="
_SYMBOL_CAP_TEACH_TAIL = "for the full list"

# --- the mixed prod/test corpus (test infra as an import hub — the friction) ---

# Two production modules that are over-endowed with symbols (the symbol-dump
# friction of FRICTION.md 2026-07-04: _surreal_fakes rendered 80+ names). ``many``
# is the focus target for §7b; ``other`` is the non-focused cap control.
_OVER_ENDOWED_SYMBOL_COUNT = 12
_MANY_SYMBOL_PREFIX = "sym_"
_OTHER_SYMBOL_PREFIX = "oth_"

_CORE_MODULE = "core"
_LONELY_MODULE = "lonely"
_MANY_SYMBOL_MODULE = "many"
_OTHER_SYMBOL_MODULE = "other"
_TEST_HARNESS_MODULE = "tests._harness"
_TEST_ALPHA_MODULE = "tests.test_alpha"

# Focus symbols, both resolvable via the engine's depth-1 ``defines``-edge probe.
_TEST_HUB_FOCUS_SYMBOL = "harness_util"  # a symbol OWNED by the test hub module
_MANY_FOCUS_SYMBOL = "sym_0"  # a symbol OWNED by the over-endowed ``many`` module

# core: a PRODUCTION utility imported by every test file (heavy test-edge mass).
_CORE_SOURCE = """\
def core_fn(x):
    \"\"\"A production utility the whole test suite imports (test-edge mass).\"\"\"
    return x
"""

# lonely: PRODUCTION, imported by nobody — the rank-mass control for §2.
_LONELY_SOURCE = """\
def lonely_fn(x):
    \"\"\"A production function no one references — the rank-mass control.\"\"\"
    return x
"""

# tests/_harness: TEST infra imported by all three test files (the TOP test hub,
# ``_surreal_harness``'s shape) — highest PageRank yet never wanted first.
_HARNESS_SOURCE = """\
def harness_util(x):
    \"\"\"Shared test-harness helper every test file imports (the test hub).\"\"\"
    return x
"""


def _over_endowed_source(prefix: str) -> str:
    """A production module defining many functions (the symbol-dump friction)."""
    return (
        "\n\n".join(
            f"def {prefix}{i}(x):\n"
            f'    """One of many symbols in an over-endowed module."""\n'
            f"    return x"
            for i in range(_OVER_ENDOWED_SYMBOL_COUNT)
        )
        + "\n"
    )


def _test_file_source(name: str) -> str:
    """A test module importing BOTH the test hub and a production module."""
    return (
        "from tests._harness import harness_util\n"
        "from core import core_fn\n"
        "\n\n"
        f"def test_{name}():\n"
        "    assert core_fn(harness_util(1)) == 1\n"
    )


def _test_infra_corpus() -> dict[str, str]:
    """A mixed prod/test corpus where TEST INFRA is an import hub (the friction).

    * ``core.py`` — production, imported by every test file (heavy test-edge mass).
    * ``lonely.py`` — production, referenced by nobody (§2 rank-mass control).
    * ``many.py`` / ``other.py`` — production, each over-endowed with 12 symbols
      (the symbol-dump friction; ``other`` is the non-focused cap control, §7b).
    * ``tests/_harness.py`` — TEST infra, imported by all 3 test files (top hub).
    * ``tests/test_alpha|beta|gamma.py`` — test files importing the hub + core.
    """
    corpus = {
        "core.py": _CORE_SOURCE,
        "lonely.py": _LONELY_SOURCE,
        "many.py": _over_endowed_source(_MANY_SYMBOL_PREFIX),
        "other.py": _over_endowed_source(_OTHER_SYMBOL_PREFIX),
        "tests/_harness.py": _HARNESS_SOURCE,
    }
    for name in ("alpha", "beta", "gamma"):
        corpus[f"tests/test_{name}.py"] = _test_file_source(name)
    return corpus


# The EXACT set of test modules in the corpus — derived from the SAME classifier
# production uses (``CodeGraph._is_test_path`` + ``module_qualified_name``), never
# a hand-copied literal list, so a change to the test-path convention can never
# let this fixture and production silently disagree (clause 5).
_TEST_MODULES = frozenset(
    CodeGraph.module_qualified_name(rel_path)
    for rel_path in _test_infra_corpus()
    if CodeGraph._is_test_path(rel_path)
)


def _find_line(formatted: str, fragment: str) -> str | None:
    """Return the first rendered line containing ``fragment``, else ``None``."""
    for line in formatted.splitlines():
        if fragment in line:
            return line
    return None


# --------------------------------------------------------------------------- #
# Spec §2 — the default map EXCLUDES test infra, but keeps its rank-mass.
# --------------------------------------------------------------------------- #
class TestDefaultMapExcludesTestInfra:
    """Contract (spec §2): the unfocused map excludes test-infra modules from the
    RENDERING, while their import edges keep feeding rank mass into production
    modules — the rank-mass-vs-rendering split. Tests are never wanted first on a
    cold orientation call (FRICTION.md 2026-07-04: test infra ranked 1-2-4)."""

    async def test_no_test_module_appears_in_the_default_rendering(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange: a corpus whose highest-PageRank module is the TEST hub.
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)

        # Act
        result = await engine.map(budget=_BUDGET_CAP)

        # Assert: not one test module survives into the rendered entries or block.
        rendered_modules = {entry.module for entry in result.entries}
        assert not (rendered_modules & _TEST_MODULES), (
            "the default map must exclude every test-infra module from the "
            f"rendering; leaked: {sorted(rendered_modules & _TEST_MODULES)}"
        )
        # Team-lead ruling on the §2/§3 pin contradiction flagged in
        # REPORT-polish-green.md's ⛔ block: design §3 (docs/design/
        # 2026-07-04-map-test-segregation.md) MANDATES the always-on elision
        # line NAME the top test hub(s) -- a blanket "no test module anywhere
        # in formatted" over-applies §2's rendering exclusion (module ENTRIES
        # / rollup lines) to that summary line too. Scope this exclusion to
        # NON-elision lines; the elision line (the one carrying the
        # tests=true affordance) is exempt and is pinned separately by
        # TestDefaultMapTestElisionLine.
        non_elision_lines = [
            line
            for line in result.formatted.splitlines()
            if _TESTS_INCLUDE_AFFORDANCE not in line
        ]
        for test_module in _TEST_MODULES:
            for line in non_elision_lines:
                assert test_module not in line, (
                    f"a non-elision rendered line must not name test module "
                    f"{test_module!r}: {line!r}"
                )

    async def test_production_rank_still_reflects_test_edge_mass(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # A production module heavily imported BY TESTS (``core``, 3 test importers)
        # must still OUTRANK an equally-sized unreferenced production module
        # (``lonely``, 0 importers) — excluding test NODES from the render must not
        # drop their EDGES' contribution to production rank.
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.map(budget=_BUDGET_CAP)

        core_index = _index_of_module(result.entries, _CORE_MODULE)
        lonely_index = _index_of_module(result.entries, _LONELY_MODULE)
        assert core_index < lonely_index, (
            "core is imported by three test files; lonely by nobody — core must "
            "outrank lonely even though the test edges' owning nodes are elided"
        )


# --------------------------------------------------------------------------- #
# Spec §3 — the always-on, never-silent test-infra elision line.
# --------------------------------------------------------------------------- #
class TestDefaultMapTestElisionLine:
    """Contract (spec §3): the default map carries an ALWAYS-RENDERED test-infra
    elision line — naming the top test hub(s) and a count, plus the literal
    expansion affordance (tests=true) — present even when budget is ample, and
    ABSENT only when the corpus has zero test modules (no-silent-caps doctrine)."""

    async def test_default_map_carries_the_always_on_test_elision_line(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange + Act at an AMPLE budget (the line is always-on, not a spillover).
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)
        result = await engine.map(budget=_BUDGET_CAP)

        # Assert: the affordance line exists, names the top test hub, and carries a
        # count — the one-glance content Sonnet's cost + Opus's information resolve to.
        elision_line = _find_line(result.formatted, _TESTS_INCLUDE_AFFORDANCE)
        assert elision_line is not None, (
            "the default map must always render a test-infra elision line carrying "
            f"the {_TESTS_INCLUDE_AFFORDANCE!r} affordance, even at ample budget"
        )
        assert _TEST_HARNESS_MODULE in elision_line, (
            "the elision line must NAME the top test hub (the highest-rank test "
            "module) so the reader knows what scaffolding exists"
        )
        assert any(character.isdigit() for character in elision_line), (
            "the elision line must carry a count of omitted test modules"
        )

    async def test_no_test_elision_line_when_corpus_has_no_test_modules(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # The line is CONDITIONAL: the existing hub/island corpus has zero test
        # modules, so no test-infra elision line (nor its affordance) may appear.
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.map(budget=_BUDGET_CAP)

        assert _TESTS_INCLUDE_AFFORDANCE not in result.formatted, (
            "a corpus with zero test modules must render no test-infra elision line"
        )


# --------------------------------------------------------------------------- #
# Spec §4 — tests=true appends the segregated, rolled-up test section.
# --------------------------------------------------------------------------- #
class TestTestsTrueSection:
    """Contract (spec §4): ``tests=true`` appends the compact, ROLLED-UP
    segregated test section — test modules present and marked [test], and
    symbol-capped like everything else — WITHOUT displacing production."""

    async def test_tests_true_renders_the_segregated_marked_test_section(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)

        # Act: opt IN to the test section.
        result = await engine.map(budget=_BUDGET_CAP, tests=True)

        # Assert: the top test hub now renders, marked as a test node, and
        # production is still present (tests=true APPENDS, never replaces).
        rendered_modules = {entry.module for entry in result.entries}
        assert _TEST_HARNESS_MODULE in rendered_modules, (
            "tests=true must render the segregated test section (the test hub)"
        )
        assert _TEST_TAG in result.formatted, (
            "the rolled-up test section must MARK its test nodes with the [test] tag"
        )
        assert _CORE_MODULE in rendered_modules, (
            "tests=true appends the test section; production must remain present"
        )


# --------------------------------------------------------------------------- #
# Spec §5 (+ §6 [test] tag) — focus on a test node AUTO-INVERTS.
# --------------------------------------------------------------------------- #
class TestFocusInvertsOnTestNode:
    """Contract (spec §5): focus= resolving to a test symbol/module AUTO-INVERTS
    — the focused test neighborhood renders at full prominence, tagged [test]
    (spec §6's mixed-context marker), with production neighbors still present."""

    async def test_focus_on_test_symbol_promotes_the_test_module_to_full_prominence(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)

        # Act: focus on a symbol OWNED by the test hub module.
        result = await engine.map(budget=_BUDGET_CAP, focus=_TEST_HUB_FOCUS_SYMBOL)

        # Assert: the focused test module is promoted to the top (auto-invert)...
        assert _index_of_module(result.entries, _TEST_HARNESS_MODULE) == 0, (
            "focusing on a test symbol must promote its test module to full "
            "prominence (rank position 0)"
        )
        # ...and production neighbors are NOT hidden by the inversion.
        assert any(entry.module == _CORE_MODULE for entry in result.entries), (
            "auto-invert must keep production neighbors present, not hide them"
        )

    async def test_focused_test_view_tags_the_test_module(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # In the inverted (mixed) view, test nodes carry the [test] tag so a reader
        # cannot mistake scaffolding for production even when it renders first.
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.map(budget=_BUDGET_CAP, focus=_TEST_HUB_FOCUS_SYMBOL)

        assert _TEST_TAG in result.formatted, (
            "the focused/inverted view must tag test modules with [test]"
        )

    async def test_focus_on_test_module_name_auto_inverts(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # SB-1 (REPORT-polish-audit.md): the always-on elision line ADVERTISES
        # the exact string "tests._harness" as the hub to pass to focus= for
        # the full test view ("test infra omitted: tests._harness ... --
        # tests=true to include"). §5 requires focus= resolving to a TEST
        # node to auto-invert regardless of whether the caller typed a bare
        # symbol or the module name printed by the tool's own output -- a
        # module-name focus must behave IDENTICALLY to a symbol-name focus
        # (test_focus_on_test_symbol_promotes_the_test_module_to_full_prominence
        # / test_focused_test_view_tags_the_test_module above), never silently
        # fall through to the un-inverted, un-tagged production-only view.
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)

        # Act: focus using the EXACT module-name string the elision line prints.
        result = await engine.map(budget=_BUDGET_CAP, focus=_TEST_HARNESS_MODULE)

        # Assert: the focused test module is promoted to the top (auto-invert)...
        assert _index_of_module(result.entries, _TEST_HARNESS_MODULE) == 0, (
            "focus=<test module name> (as printed by the elision line) must "
            "auto-invert -- promoting its own module to full prominence (rank "
            "position 0), never silently stay demoted out of the view"
        )
        # ...tagged [test] so a reader never mistakes it for production...
        assert _TEST_TAG in result.formatted, (
            "the auto-inverted view reached via a module-name focus must still "
            "tag the test module with [test]"
        )
        # ...and production neighbors are NOT hidden by the inversion.
        assert any(entry.module == _CORE_MODULE for entry in result.entries), (
            "auto-invert via a module-name focus must keep production "
            "neighbors present, not hide them"
        )


# --------------------------------------------------------------------------- #
# Spec §6/§7 — symbol caps everywhere, with the teaching trailer + escape hatches.
# --------------------------------------------------------------------------- #
class TestSymbolCaps:
    """Contract (spec §6/§7): symbol caps EVERYWHERE — an over-endowed module
    renders top-N symbols plus a TEACHING trailer that names its expansion verb
    (``focus=<module> for the full list``, §7a); the cap scales with budget (§7c);
    focus= lifts ONLY the focused module's cap (§7b)."""

    async def test_over_endowed_module_is_capped_with_a_teaching_trailer(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange: ``many`` defines 12 symbols — an unfocused map must NOT dump all
        # of them (budget spends on module breadth over symbol depth).
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)

        # Act
        result = await engine.map(budget=_BUDGET_DEFAULT)

        # Assert: fewer than all 12 symbol names render (a real cap)...
        rendered_symbol_count = result.formatted.count(_MANY_SYMBOL_PREFIX)
        assert rendered_symbol_count < _OVER_ENDOWED_SYMBOL_COUNT, (
            f"an over-endowed module ({_OVER_ENDOWED_SYMBOL_COUNT} symbols) must "
            f"render a CAPPED subset by default, not a full dump; rendered "
            f"{rendered_symbol_count}"
        )
        # ...and the trailer TEACHES its expansion verb by name (§7a).
        assert f"{_SYMBOL_CAP_TEACH_VERB}{_MANY_SYMBOL_MODULE}" in result.formatted, (
            "the '+K more' trailer must teach the expansion verb by name "
            f"({_SYMBOL_CAP_TEACH_VERB}{_MANY_SYMBOL_MODULE})"
        )
        assert _SYMBOL_CAP_TEACH_TAIL in result.formatted, (
            "the trailer must point at the full-list affordance ('for the full list')"
        )

    async def test_symbol_cap_scales_with_budget(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # §7c: the cap is a budget-allocation policy, not an information ceiling —
        # the SAME corpus at a higher budget renders strictly MORE symbols for the
        # top over-endowed module.
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)

        low_budget = await engine.map(budget=_BUDGET_DEFAULT)
        high_budget = await engine.map(budget=_BUDGET_CAP)

        low_symbols = low_budget.formatted.count(_MANY_SYMBOL_PREFIX)
        high_symbols = high_budget.formatted.count(_MANY_SYMBOL_PREFIX)
        assert high_symbols > low_symbols, (
            "a higher budget must render strictly more symbols for the top "
            f"over-endowed module (breadth-first cap policy); {low_symbols} -> "
            f"{high_symbols}"
        )

    async def test_focus_lifts_only_the_focused_modules_symbol_cap(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # §7b: focusing on a module is the "I care about this one" signal — its own
        # symbol cap lifts to the full list; a DIFFERENT over-endowed neighbor
        # stays capped.
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)

        # Act: focus on a symbol OWNED by ``many`` (the over-endowed module).
        result = await engine.map(budget=_BUDGET_DEFAULT, focus=_MANY_FOCUS_SYMBOL)

        # Assert: the focused module shows its FULL symbol list...
        focused_symbols = result.formatted.count(_MANY_SYMBOL_PREFIX)
        assert focused_symbols == _OVER_ENDOWED_SYMBOL_COUNT, (
            "focus= must LIFT the focused module's symbol cap (full list within "
            f"budget); rendered {focused_symbols} of {_OVER_ENDOWED_SYMBOL_COUNT}"
        )
        # ...while a non-focused over-endowed neighbor stays capped (ONLY the
        # focused module's cap lifts).
        neighbor_symbols = result.formatted.count(_OTHER_SYMBOL_PREFIX)
        assert neighbor_symbols < _OVER_ENDOWED_SYMBOL_COUNT, (
            "focus= must lift ONLY the focused module's cap; the non-focused "
            f"'other' module must stay capped, rendered {neighbor_symbols}"
        )

    async def test_focus_on_module_name_lifts_that_modules_symbol_cap(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # SB-1 (REPORT-polish-audit.md): the +K-more trailer TEACHES its own
        # expansion verb by name -- "focus=many for the full list" -- naming
        # the MODULE, not a symbol. §7b promises focus= lifts "that module's"
        # symbol cap; the caller who follows the trailer LITERALLY (types the
        # module name it just printed) must get the same lift as focusing a
        # symbol owned by that module
        # (test_focus_lifts_only_the_focused_modules_symbol_cap above), never
        # a silent no-op that re-prints the identical capped trailer.
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph)

        # Act: focus using the EXACT module-name string the trailer prints.
        result = await engine.map(budget=_BUDGET_DEFAULT, focus=_MANY_SYMBOL_MODULE)

        # Assert: the focused module shows its FULL symbol list...
        focused_symbols = result.formatted.count(_MANY_SYMBOL_PREFIX)
        assert focused_symbols == _OVER_ENDOWED_SYMBOL_COUNT, (
            "focus=<module name> (as printed by the tool's own trailer) must "
            f"LIFT that module's symbol cap; rendered {focused_symbols} of "
            f"{_OVER_ENDOWED_SYMBOL_COUNT}"
        )
        # ...while a non-focused over-endowed neighbor stays capped (ONLY the
        # focused module's cap lifts).
        neighbor_symbols_via_module_focus = result.formatted.count(_OTHER_SYMBOL_PREFIX)
        assert neighbor_symbols_via_module_focus < _OVER_ENDOWED_SYMBOL_COUNT, (
            "focus=<module name> must lift ONLY the focused module's cap; the "
            "non-focused 'other' module must stay capped, rendered "
            f"{neighbor_symbols_via_module_focus}"
        )


# =========================================================================== #
# P7-TAIL POLISH WAVE (ledger task #6) — ADDENDUM spec point 10b: TOKEN-BUDGET
# CALIBRATION. lore enforces budgets in VOYAGE tokens (the pinned voyage-4
# tokenizer) but consumers pay in CLAUDE tokens; the voyage→claude ratio is
# survey-final 2026-07-04: max per-project TOKEN-WEIGHTED p95 over a
# deterministic 10% stratified sample (1,116 files, 2.85M claude tokens; lore
# 1.704 / odoo 1.776 / di 1.729); tool scripts/token_survey.py; supersedes the
# six-sample pilot (1.61-1.72);
# pinned at the observed MAXIMUM — ceiling semantics: a budget is a promise that
# must hold for the worst observed content shape. An uncalibrated budget
# under-counts the consumer's real cost by up to ~78%. GREEN introduces a
# provenance-documented ``TOKEN_BUDGET_CALIBRATION`` (=1.78) in
# ``loremaster.server`` and applies it in the budget-counting path
# (``AppContext._count_tokens_single``): counted = ceil(voyage × calibration).
# These pins ride the SAME budget seam as TestBudgetEnforcement above. This
# class ADDS pins; no existing budget NUMBER changes — only the counting currency.
# =========================================================================== #

# The measured voyage→claude ratio, pinned as a LITERAL so a silent re-tune
# breaks a test (the addendum's explicit anti-drift requirement). Provenance:
# survey-final 2026-07-04: max per-project TOKEN-WEIGHTED p95 over a
# deterministic 10% stratified sample (1,116 files, 2.85M claude tokens; lore
# 1.704 / odoo 1.776 / di 1.729); tool scripts/token_survey.py; supersedes the
# six-sample pilot (1.61-1.72).
_EXPECTED_CALIBRATION = 1.78
# Provenance markers the constant's documentation must carry (measurement model +
# year) so a silent change to the ratio is auditable at the source.
_MEASUREMENT_MODEL_MARK = "sonnet"
_MEASUREMENT_DATE_MARK = "2026"
# A budget the test-infra corpus OVERFLOWS even in raw voyage tokens (measured:
# the full render is ~259 voyage tokens; at 200 the budget binds and elides), so
# the calibrated bound genuinely bites rather than passing on a tiny render.
_CALIBRATION_PROBE_BUDGET = _BUDGET_FLOOR


def _token_budget_calibration() -> float:
    """The production calibration constant (dynamic attribute access → behavioural
    RED while it does not exist yet — AttributeError at call time, never a
    collection collapse nor a typecheck error on the not-yet-defined name)."""
    import loremaster.server as server_module

    return float(getattr(server_module, "TOKEN_BUDGET_CALIBRATION"))


def _voyage_token_count(text: str) -> int:
    """The RAW voyage-token count of ``text`` via the pinned tokenizer — the
    INDEPENDENT measurement (the production counting path uses this same
    tokenizer, but this call bypasses any calibration the engine applied)."""
    from loresigil.tokens import VoyageTokenCounter

    return VoyageTokenCounter().count(text)


def _production_calibrated_counter() -> Callable[[str], int]:
    """The EXACT production single-string counter — ``AppContext._count_tokens_single``
    over a real, offline voyage tokenizer.

    Calling the production method (not a re-implementation of its formula) is what
    keeps this pin honest: the calibration lives INSIDE that method, so a counter
    built any other way could not tell an uncalibrated build from a calibrated
    one. ``FakeEmbedder(use_exact_tokenizer=True)`` counts through the identical
    :class:`~loresigil.tokens.VoyageTokenCounter` the production embedder uses.
    """
    from typing import cast

    from loremaster.server import AppContext
    from loresigil.testing import FakeEmbedder

    embedder = FakeEmbedder(dim=_DIM, use_exact_tokenizer=True)
    # A structural stand-in: ``_count_tokens_single`` reads only ``self.embedder``.
    # cast satisfies the static type; at runtime it is a no-op over the namespace.
    namespace = cast(AppContext, SimpleNamespace(embedder=embedder))
    return lambda text: AppContext._count_tokens_single(namespace, text)


def _server_source_window_around(symbol: str, radius: int = 600) -> str:
    """The server-module source text surrounding ``symbol`` (``""`` if absent)."""
    import loremaster.server

    source = Path(loremaster.server.__file__).read_text(encoding="utf-8")
    index = source.find(symbol)
    if index == -1:
        return ""
    return source[max(0, index - radius) : index + radius]


class TestTokenBudgetCalibration:
    """Contract (spec §10b): map budgets denominate in ~Claude-token currency via
    a provenance-documented calibration constant. lore counts in voyage tokens
    but consumers pay in Claude tokens (survey-final 2026-07-04: max
    per-project TOKEN-WEIGHTED p95 over a deterministic 10% stratified sample,
    1,116 files, 2.85M claude tokens; lore 1.704 / odoo 1.776 / di 1.729; tool
    scripts/token_survey.py; supersedes the six-sample pilot 1.61-1.72) —
    pinned at the observed MAXIMUM (ceiling semantics: a budget is a promise
    that must hold for the worst observed content shape). An uncalibrated
    budget silently under-counts the consumer's real cost by up to ~78%."""

    def test_calibration_constant_is_the_measured_ratio(self) -> None:
        # A pinned literal: a silent change to the calibration must break this test.
        calibration = _token_budget_calibration()  # RED: does not exist yet
        assert calibration == _EXPECTED_CALIBRATION, (
            f"the calibration constant must be the measured voyage→claude ratio "
            f"{_EXPECTED_CALIBRATION}; a silent re-tune must break a test"
        )
        assert calibration > 1.0, (
            "claude tokens outnumber voyage tokens for the same text — the "
            "calibration must inflate the count, never deflate it"
        )

    def test_calibration_constant_documents_its_provenance(self) -> None:
        # Anti-silent-drift: the measurement's model + date must be documented at
        # the source so any future change is auditable (not a bare magic number).
        window = _server_source_window_around("TOKEN_BUDGET_CALIBRATION")
        assert _MEASUREMENT_MODEL_MARK in window.lower(), (
            "the calibration constant must document the measurement MODEL "
            f"(expected mention of {_MEASUREMENT_MODEL_MARK!r})"
        )
        assert _MEASUREMENT_DATE_MARK in window, (
            "the calibration constant must document the measurement DATE "
            f"(expected a {_MEASUREMENT_DATE_MARK} date)"
        )

    async def test_rendered_map_fits_the_claude_denominated_budget(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Build the engine with the PRODUCTION calibrated counter, render at a
        # budget the corpus overflows, then measure the render's RAW voyage tokens
        # INDEPENDENTLY. A budget of B must now buy at most ~B Claude tokens, i.e.
        # at most B / calibration voyage tokens.
        calibration = _token_budget_calibration()
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph, count_tokens=_production_calibrated_counter())

        result = await engine.map(budget=_CALIBRATION_PROBE_BUDGET)

        # Precondition: the budget must actually bind, or the bound is vacuous.
        assert result.elided_modules > 0, (
            "the probe budget must overflow the corpus so the calibrated bound bites"
        )
        raw_voyage_tokens = _voyage_token_count(result.formatted)
        assert raw_voyage_tokens <= _CALIBRATION_PROBE_BUDGET / calibration, (
            f"a budget of {_CALIBRATION_PROBE_BUDGET} must buy at most "
            f"{_CALIBRATION_PROBE_BUDGET / calibration:.1f} voyage tokens "
            f"(~Claude-token denomination); rendered {raw_voyage_tokens}"
        )

    async def test_elision_trailer_survives_the_tighter_effective_budget(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # No silent-drop regression: under the tighter calibrated effective budget
        # (fewer modules fit), the explicit elision trailer must still render —
        # the no-silent-caps doctrine holds at the new effective sizes. Uses the
        # production counter directly (no dependence on the constant), so it stays
        # a behavioural regression lock even before the constant lands.
        trio, _server = await _build_graph(tmp_path, _test_infra_corpus())
        engine = engine_factory(trio.graph, count_tokens=_production_calibrated_counter())

        result = await engine.map(budget=_CALIBRATION_PROBE_BUDGET)

        assert result.elided_modules > 0, (
            "the probe budget must overflow the corpus (modules must be elided)"
        )
        assert _ELISION_FRAGMENT in result.formatted, (
            "the explicit module-elision trailer must still render under the "
            "tighter calibrated budget — never a silent drop"
        )
