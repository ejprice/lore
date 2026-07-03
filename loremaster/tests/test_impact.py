"""Contract tests for ``loremaster.impact.ImpactEngine`` — the P6-tail impact verb.

``lore_impact`` (plan §5) is the one-call answer to "who depends on this?" —
the question shape that today costs a whole Explore-agent sweep (FRICTION.md's
seam-sweep entry is the live justification, and this session's near-miss — a
production base class almost deleted on an undercounted reference profile — is
the live justification for the CAVEAT contract below).

Contract decisions THIS file pins (team-lead as contract owner, twice-stalled
takeover):

* Engine: ``ImpactEngine`` in a NEW ``loremaster/loremaster/impact.py`` — a
  pure read layer over the code graph. Constructor (keyword-only):
  ``ImpactEngine(*, graph, rebuild_notice=None)`` where ``rebuild_notice`` is
  an async callable returning ``None`` (settled) or a human-readable notice
  string (a rebuild is in progress). ``None`` for the whole dep = never
  rebuilding (the bare-test wiring).
* Query: ``await engine.impact(target, depth=1, max_consumers=25) ->
  ImpactResult``. ``depth`` clamps to 1..4; ``max_consumers`` caps every
  rendered consumer list with an EXPLICIT elision marker (never a silent cap).
* ``ImpactResult`` (pydantic, ``extra="forbid"``): target, verdict
  (``"live"`` | ``"dead (heuristic)"``), production_references,
  test_references, covering_tests (qualified names), direct_consumers
  (depth 1), module_rollups (depth > 1: ``ModuleRollup {module,
  consumer_count}``, sorted consumer_count DESC then module ASC), elided
  (count squeezed out by ``max_consumers``), caveat (NEVER empty), formatted
  (the token-compact rendered block).
* THE CAVEAT IS PART OF EVERY VERDICT: astroid-inference bounds mean the
  counts can UNDERCOUNT dynamic/framework-mediated references — a deadness
  verdict is a heuristic to investigate, not a sentence. The caveat string
  must name both facts (substrings pinned: "heuristic", "undercount").
* Verdict-bearing outputs are NEVER served mid-rebuild: a non-None
  ``rebuild_notice()`` result makes ``impact()`` raise
  ``ImpactRebuildingError`` whose message carries the notice AND a retry
  hint ("retry"). An EMPTY-BUT-HEALTHY graph is not an error: a symbol that
  exists with zero consumers is a valid ``dead (heuristic)`` result.
* Unknown target (never indexed): ``ImpactTargetNotFoundError`` naming the
  target and pointing at a next step ("search_code") — the teaching-miss
  standard (mirrors ``GetSymbolError``).

Expected RED: ``loremaster.impact`` does not exist yet. The import happens
lazily inside the ``engine_factory`` fixture, so the file COLLECTS cleanly and
every test fails behaviourally (ModuleNotFoundError at call time), never as a
file-level collection collapse.
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

# Depth clamps (plan §5: depth 1..4; rollups replace max_results at depth>1).
_DEPTH_MIN = 1
_DEPTH_MAX = 4

# The verdict literals. "dead (heuristic)" carries its epistemic status in the
# value itself — a consumer can never quote the verdict without the hedge.
_VERDICT_LIVE = "live"
_VERDICT_DEAD = "dead (heuristic)"

# Substrings every caveat must carry (the near-miss lesson, contractualised).
_CAVEAT_MUST_MENTION = ("heuristic", "undercount")

# The explicit elision marker fragment rendered when max_consumers squeezes
# consumers out of the formatted block (no-silent-caps doctrine).
_ELISION_FRAGMENT = "more (elided"

# The retry hint every rebuilding error must carry.
_RETRY_FRAGMENT = "retry"


# --------------------------------------------------------------------------- #
# Corpus — reference profiles pinned BY CONSTRUCTION (hand-known, tiny).
# --------------------------------------------------------------------------- #
# reflib defines the target (champion_routing) and an orphan nothing references.
_REFLIB_SOURCE = """\
def champion_routing(week):
    \"\"\"Route the 36-week curve champion warehouse.\"\"\"
    return week * 2


def orphan_helper(week):
    \"\"\"Defined but never referenced by anyone — the dead-heuristic case.\"\"\"
    return week
"""

# A production caller (depth-1 consumer of champion_routing).
_CONSUMER_SOURCE = """\
from reflib import champion_routing


def dispatch(week):
    \"\"\"A production caller of champion_routing.\"\"\"
    return champion_routing(week)
"""

# A second-hop production module (imports consumer, never reflib) — the
# depth-2 ripple that must appear ONLY at depth >= 2.
_CONSUMER2_SOURCE = """\
import consumer


def relay(week):
    \"\"\"A second-hop caller: depends on consumer, not on reflib directly.\"\"\"
    return consumer.dispatch(week)
"""

# A test caller — counts on the TEST side of the split, and is the covering
# test tests_for surfaces.
_TEST_REFLIB_SOURCE = """\
from reflib import champion_routing


def test_champion_routing():
    assert champion_routing(1) == 2
"""

_TARGET = "champion_routing"
_ORPHAN = "orphan_helper"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _slug() -> str:
    return f"test_{uuid.uuid4().hex}"


def _config(*, slug: str, live_path: Path) -> LoreConfig:
    """A validated config with one live tier (mirrors test_search's fixture)."""
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
        count_tokens=lambda text: max(1, len(text) // 4),
        max_input_tokens=8192,
    )
    return server.registry.dispatch_file(rel_path, source, ctx)


async def _build_graph(
    tmp_path: Path, files: dict[str, str]
) -> tuple[FakeSurrealTrio, LoreServer]:
    """Write ``files``, chunk them for real, and build the fake graph.

    Impact is a pure GRAPH read — no store/embedding work is needed, so the
    fixture builds only the graph slice (chunk → build_file_graph), keeping
    every test sub-second.
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
        "reflib.py": _REFLIB_SOURCE,
        "consumer.py": _CONSUMER_SOURCE,
        "consumer2.py": _CONSUMER2_SOURCE,
        "tests/test_reflib.py": _TEST_REFLIB_SOURCE,
    }


@pytest.fixture()
def engine_factory() -> Callable[..., Any]:
    """Build an ``ImpactEngine`` via a LAZY import (behavioural red, not
    collection collapse): the module under contract does not exist yet."""

    def _build(
        graph: Any,
        *,
        rebuild_notice: Callable[[], Awaitable[str | None]] | None = None,
    ) -> Any:
        impact_module = importlib.import_module("loremaster.impact")
        return impact_module.ImpactEngine(graph=graph, rebuild_notice=rebuild_notice)

    return _build


def _errors() -> Any:
    """The engine's typed errors, imported lazily for the same reason."""
    return importlib.import_module("loremaster.impact")


# --------------------------------------------------------------------------- #
# 1/2/3 — depth-1 core: split, covering tests, live verdict
# --------------------------------------------------------------------------- #
class TestDepthOneCore:
    async def test_depth_one_splits_prod_and_test_consumers(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1)

        # By construction: consumer.py (prod) + tests/test_reflib.py (test).
        assert result.production_references >= 1
        assert result.test_references >= 1
        # Direct consumers name the prod caller; the split is not merged.
        assert any("consumer" in name for name in result.direct_consumers)

    async def test_covering_tests_ride_the_result(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1)

        assert result.covering_tests, "the corpus has a covering test by construction"
        assert any("test_reflib" in name for name in result.covering_tests)

    async def test_live_verdict_when_production_references_exist(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1)

        assert result.verdict == _VERDICT_LIVE
        assert result.verdict in result.formatted


# --------------------------------------------------------------------------- #
# 4/5 — the dead-heuristic verdict + the caveat on EVERY verdict
# --------------------------------------------------------------------------- #
class TestVerdictAndCaveat:
    async def test_orphan_symbol_gets_dead_heuristic_verdict(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_ORPHAN, depth=1)

        assert result.verdict == _VERDICT_DEAD
        assert result.production_references == 0
        # A defined-but-unreferenced symbol is a VALID result — never an error
        # (honest emptiness on a healthy graph).

    @pytest.mark.parametrize("target", [_TARGET, _ORPHAN])
    async def test_every_verdict_carries_the_astroid_bounds_caveat(
        self, tmp_path: Path, engine_factory: Callable[..., Any], target: str
    ) -> None:
        # The near-miss lesson: reference counts must SAY what they cannot
        # see. Live and dead verdicts alike carry the caveat — in the
        # structured field AND the rendered block.
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(target, depth=1)

        assert result.caveat
        for fragment in _CAVEAT_MUST_MENTION:
            assert fragment in result.caveat.lower()
        assert result.caveat in result.formatted


# --------------------------------------------------------------------------- #
# 6/7 — depth semantics: clamping + per-module rollup at depth > 1
# --------------------------------------------------------------------------- #
class TestDepthSemantics:
    async def test_depth_two_rolls_up_by_module_and_reaches_the_second_hop(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=2)

        modules = [rollup.module for rollup in result.module_rollups]
        assert modules, "depth 2 renders per-module rollups, not a flat node dump"
        # The second hop (consumer2 imports consumer, never reflib) appears
        # ONLY because depth >= 2 followed the transitive edge.
        assert any("consumer2" in module for module in modules)
        # Rollups carry counts, and every count is positive.
        assert all(rollup.consumer_count >= 1 for rollup in result.module_rollups)

    async def test_depth_one_does_not_reach_the_second_hop(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1)

        assert not any("consumer2" in name for name in result.direct_consumers), (
            "consumer2 never references the target directly — it must not "
            "appear at depth 1"
        )

    @pytest.mark.parametrize("requested,effective_reaches_hop2", [(0, False), (99, True)])
    async def test_depth_clamps_to_bounds(
        self,
        tmp_path: Path,
        engine_factory: Callable[..., Any],
        requested: int,
        effective_reaches_hop2: bool,
    ) -> None:
        # Below-floor clamps to 1 (no second hop); above-cap clamps to 4 (the
        # second hop is within reach). Clamp, never raise — the tool-surface
        # convention for k/depth style params.
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=requested)

        reached = any(
            "consumer2" in rollup.module for rollup in result.module_rollups
        ) or any("consumer2" in name for name in result.direct_consumers)
        assert reached == effective_reaches_hop2


# --------------------------------------------------------------------------- #
# 8 — verdicts are never served mid-rebuild (graded honest-emptiness)
# --------------------------------------------------------------------------- #
class TestRebuildingGate:
    async def test_rebuilding_probe_blocks_the_verdict_with_retry_hint(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        notice = "graph rebuilding: 3/118 files"

        async def _rebuilding() -> str | None:
            return notice

        engine = engine_factory(trio.graph, rebuild_notice=_rebuilding)

        with pytest.raises(_errors().ImpactRebuildingError) as exc_info:
            await engine.impact(_TARGET, depth=1)
        message = str(exc_info.value)
        assert notice in message
        assert _RETRY_FRAGMENT in message.lower()

    async def test_settled_probe_serves_normally(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())

        async def _settled() -> str | None:
            return None

        engine = engine_factory(trio.graph, rebuild_notice=_settled)

        result = await engine.impact(_TARGET, depth=1)
        assert result.verdict == _VERDICT_LIVE


# --------------------------------------------------------------------------- #
# 9 — unknown target: the teaching miss
# --------------------------------------------------------------------------- #
class TestUnknownTarget:
    async def test_unknown_target_raises_naming_it_and_the_next_step(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        with pytest.raises(_errors().ImpactTargetNotFoundError) as exc_info:
            await engine.impact("totally.bogus.symbol", depth=1)
        message = str(exc_info.value)
        assert "totally.bogus.symbol" in message
        assert "search_code" in message


# --------------------------------------------------------------------------- #
# 10/11 — determinism + the bounded, explicitly-elided consumer list
# --------------------------------------------------------------------------- #
class TestDeterminismAndBounds:
    async def test_identical_graph_yields_identical_output(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        first = await engine.impact(_TARGET, depth=2)
        second = await engine.impact(_TARGET, depth=2)

        assert first.formatted == second.formatted
        assert [r.module for r in first.module_rollups] == [
            r.module for r in second.module_rollups
        ]

    async def test_consumer_cap_elides_explicitly_never_silently(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Three distinct prod consumers; max_consumers=2 must (a) bound the
        # listed names, (b) COUNT the squeezed-out remainder in ``elided``,
        # (c) SAY so in the rendered block (no-silent-caps doctrine).
        files = _full_corpus()
        files["consumer_b.py"] = _CONSUMER_SOURCE.replace("dispatch", "dispatch_b")
        files["consumer_c.py"] = _CONSUMER_SOURCE.replace("dispatch", "dispatch_c")
        trio, _server = await _build_graph(tmp_path, files)
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1, max_consumers=2)

        assert len(result.direct_consumers) == 2
        assert result.elided >= 1
        assert _ELISION_FRAGMENT in result.formatted
        assert "max_consumers=2" in result.formatted, (
            "the elision line must report the TRUE cap, not the total"
        )

    async def test_formatted_block_is_compact_and_carries_the_split(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1)

        assert f"{result.production_references} prod" in result.formatted
        assert f"{result.test_references} test" in result.formatted
        assert "tests:" in result.formatted
        # Token-compact: a one-symbol depth-1 impact over a 4-file corpus must
        # render well under a hundred lines (a proxy pin against raw dumps).
        assert len(result.formatted.splitlines()) < 40
