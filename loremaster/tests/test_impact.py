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
        assert "lore_search" in message


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


# =========================================================================== #
# P7-TAIL POLISH WAVE (ledger task #6) — the semantic law for the map/impact
# frictions the P8 tool-surface redesign must honor. Behavioural expectations
# below come from the BINDING spec (docs/design/2026-07-04-map-test-segregation.md
# §8/§9) and the FRICTION.md receipts (2026-07-03/04 lore_impact entries) — NEVER
# from how the current engine happens to render. These classes ADD pins; they
# never weaken the existing behaviour above.
# =========================================================================== #

# The module-qualified form of the same target the bare ``_TARGET`` names — the
# TWO forms whose covering-tests result the answers_to bridge must reconcile
# (FRICTION.md's "0-vs-137" bare-name drop). Derived from the corpus BY
# CONSTRUCTION: ``champion_routing`` is defined in ``reflib.py`` → module
# ``reflib`` → qualified name ``reflib.champion_routing``.
_QUALIFIED_TARGET = f"reflib.{_TARGET}"

# The design-doc §9 requirement: a depth>1 module rollup reached ONLY
# transitively must be LABELED transitive so a reader cannot mistake the ripple
# for direct-consumer usage (the receipt: a fixture migration mis-scoped because
# a depth-2 count read as direct usage). Source of the marker word: the spec /
# FRICTION.md phrasing ("transitive via …" / a direct/transitive split), matched
# case-insensitively so the exact rendering wording stays P8's to choose.
_TRANSITIVE_MARKER = "transitive"

# The corpus's two consumer roles, pinned BY CONSTRUCTION (see the source
# fixtures above): ``consumer`` imports ``reflib`` (a DIRECT depth-1 consumer of
# the target); ``consumer2`` imports ``consumer`` and never ``reflib`` (reaches
# the target ONLY at depth >= 2 — the transitive-only ripple).
_DIRECT_CONSUMER_MODULE = "consumer"
_TRANSITIVE_CONSUMER_MODULE = "consumer2"


def _rollup_entry(formatted: str, module: str) -> str:
    """Return the single ``module (count[, transitive])`` entry for ``module``.

    The "modules: " line joins every rollup with ", " -- the SAME separator
    used inside a transitive entry's own parenthetical (", transitive") -- so
    a naive substring/split check cannot tell "does module X's OWN entry
    carry the marker" from "does the marker appear ANYWHERE on the line".
    Anchoring on ``"{module} ("`` and slicing to the matching close-paren
    isolates exactly one module's entry, killing the label-everything mutant
    (``_transitive_only_modules`` suffixing every rollup) that a whole-line
    substring check lets through.
    """
    start = formatted.find(f"{module} (")
    assert start != -1, f"no rollup entry found for module {module!r} in: {formatted!r}"
    end = formatted.find(")", start)
    assert end != -1, f"unterminated rollup entry for module {module!r} in: {formatted!r}"
    return formatted[start : end + 1]


# --------------------------------------------------------------------------- #
# Spec §8 / FRICTION 2026-07-03 — the bare-name covering-tests bridge.
# --------------------------------------------------------------------------- #
class TestBareNameCoveringTestsBridge:
    """Contract: covering tests resolve through the SAME answers_to bare-name
    bridge as the reference counts — ``impact`` on a BARE identity surfaces the
    same covering tests as the module-qualified form, never a silent ``tests:
    0`` when the qualified form has tests (FRICTION.md's 0-vs-137 drop).

    Primary behaviour pinned = the BRIDGE (bare ≡ qualified). The spec's
    FALLBACK route (an explicit "tests unresolved for bare names — qualify"
    notice instead of a silent 0) is NOT pinned here: were the implementation to
    take that route, this equality would fail and the fallback would need its
    own pin. See REPORT-polish-contract.md — against the in-memory graph double
    this bridge already holds (the double's ``tests_for`` rides bare names), so
    this class is a GREEN regression-lock at the engine seam; the LIVE friction
    lives in the REAL ``graph_surreal.tests_for`` (which looks up only literal
    bare/FQN name-ids, never ``answers_to``) and its RED reproduction belongs in
    ``test_graph_surreal.py`` — flagged for the team-lead as a writable-set gap.
    """

    async def test_bare_target_yields_the_same_covering_tests_as_the_qualified_form(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange: the corpus has a covering test (tests/test_reflib.py) for the
        # target champion_routing, reachable under BOTH its bare and qualified name.
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        # Act: query the SAME target two ways — bare vs module-qualified.
        result_bare = await engine.impact(_TARGET, depth=1)
        result_qualified = await engine.impact(_QUALIFIED_TARGET, depth=1)

        # Assert: the qualified form has covering tests by construction, and the
        # bare form must reconcile to the SAME set via the answers_to bridge — a
        # bare identity may never surface FEWER covering tests than its qualifier.
        assert result_qualified.covering_tests, (
            "the corpus has a covering test by construction (tests/test_reflib.py)"
        )
        assert set(result_bare.covering_tests) == set(result_qualified.covering_tests), (
            "a bare target must ride the answers_to bridge to the SAME covering "
            "tests as its module-qualified form (the 0-vs-137 friction)"
        )

    async def test_bare_target_never_renders_a_silent_tests_zero(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # The friction's harm was the RENDER: a bare query showed "tests: 0" while
        # the qualifier showed 137 — a silent 0 reads as a real answer. When the
        # qualified form has tests, the bare render must NOT claim zero.
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result_bare = await engine.impact(_TARGET, depth=1)

        assert result_bare.covering_tests, (
            "the bare target must resolve its covering tests, not drop them"
        )
        assert "tests: 0" not in result_bare.formatted, (
            "a bare target with covering tests must never render a silent 'tests: 0'"
        )


# --------------------------------------------------------------------------- #
# Spec §9 / FRICTION 2026-07-04 — depth>1 rollups are labeled TRANSITIVE.
# --------------------------------------------------------------------------- #
class TestDepthTwoTransitiveLabeling:
    """Contract: a depth>1 module rollup reached only transitively is LABELED
    transitive, so a reader cannot mistake the ripple for direct-consumer usage
    (FRICTION.md 2026-07-04: a fixture migration mis-scoped because a depth-2
    module count read as direct usage). The marker is CONDITIONAL — it appears
    only when a transitive-only consumer exists, so it genuinely distinguishes."""

    async def test_depth_two_marks_the_transitive_only_consumer(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Arrange: consumer2 imports consumer imports reflib (the target's module)
        # — consumer2 reaches the target ONLY via the depth-2 transitive edge.
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        # Act
        result = await engine.impact(_TARGET, depth=2)

        # Assert: the transitive-only consumer is reached at depth 2...
        assert any(
            _TRANSITIVE_CONSUMER_MODULE in rollup.module for rollup in result.module_rollups
        ), "consumer2 reaches the target only transitively — it appears at depth 2"
        # ...and the render marks ONLY the transitive-only consumer's entry --
        # a "label every rollup" mutant (suffixing consumer TOO) must not
        # survive: the DIRECT consumer's own entry must stay bare while the
        # transitive-only consumer's entry carries the marker.
        direct_entry = _rollup_entry(result.formatted, _DIRECT_CONSUMER_MODULE)
        transitive_entry = _rollup_entry(result.formatted, _TRANSITIVE_CONSUMER_MODULE)
        assert _TRANSITIVE_MARKER not in direct_entry.lower(), (
            f"{_DIRECT_CONSUMER_MODULE!r} is a DIRECT depth-1 consumer of the "
            f"target -- its rollup entry {direct_entry!r} must NOT carry the "
            "transitive label"
        )
        assert _TRANSITIVE_MARKER in transitive_entry.lower(), (
            f"{_TRANSITIVE_CONSUMER_MODULE!r} reaches the target ONLY via the "
            f"depth-2 ripple -- its rollup entry {transitive_entry!r} must "
            "carry the transitive label"
        )

    async def test_depth_one_renders_direct_consumers_and_emits_no_modules_rollup_line(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # SF-2 (REPORT-polish-audit.md): this test was VACUOUS under its old
        # name/assertion. At depth == 1, impact populates ONLY
        # direct_consumers -- module_rollups stays empty by construction (see
        # this file's own docstring: "module_rollups (depth > 1: ...)") -- so
        # the ONE place a transitive suffix could ever render (the "modules: "
        # rollup line) is never emitted AT ALL, regardless of whether the
        # suffix logic is correct, broken, or absent. The absence of the
        # marker here proves depth gates module_rollups; it does NOT prove
        # the label itself is conditional on real transitivity (the depth-2
        # pin above is what proves that).
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1)

        assert any(
            _DIRECT_CONSUMER_MODULE in name for name in result.direct_consumers
        ), "depth 1 must still render the direct consumer by name"
        assert "modules:" not in result.formatted, (
            "depth 1 populates ONLY direct_consumers -- the modules: rollup "
            "line must not be emitted at all (nothing exists yet to roll up)"
        )


# =========================================================================== #
# P8D WAVE 2 (THE IMPACT FOLD) -- finding #19 investigation + the honest-render
# findings (#1/#2 covering-tests, #39 elision cap, #30 bare-name teach) it
# consumes. See REPORT-builder-flip-w2.md for the full live-repro receipts.
# =========================================================================== #

# Finding #19's ORIGINAL live repro target (FRICTION.md 2026-07-04,
# "sanitiser-residual"): ``loremaster.search._sanitise_line``, a module-private
# leaf function called from 7 production sites across search.py/diff.py. Live
# re-repro THIS session (against the current HEAD, via lore_impact/lore_references
# over the real index) shows depth=1 direct_consumers is ALREADY populated
# correctly (8 distinct prod consumers) -- the empty-list symptom no longer
# reproduces (fixed by an earlier commit that queries ``references()`` by BOTH
# the qualified AND bare name id, landing before this wave). The corpus below
# locks that fix in as a regression pin with the SAME repro shape (a private
# leaf helper, several distinct production callers).
_PRIVATE_LEAF_SOURCE = """\
def _sanitize(text):
    \"\"\"A module-private leaf helper (mirrors finding #19's repro shape).\"\"\"
    return text.strip()
"""

_PRIVATE_CONSUMER_A_SOURCE = """\
from privlib import _sanitize


def format_a(text):
    \"\"\"A production caller of the private leaf helper.\"\"\"
    return _sanitize(text)
"""

_PRIVATE_CONSUMER_B_SOURCE = """\
from privlib import _sanitize


def format_b(text):
    \"\"\"A second, independent production caller.\"\"\"
    return _sanitize(text)
"""

_PRIVATE_CONSUMER_C_SOURCE = """\
from privlib import _sanitize


def format_c(text):
    \"\"\"A third, independent production caller.\"\"\"
    return _sanitize(text)
"""

_PRIVATE_TARGET = "privlib._sanitize"


class TestPrivateLeafDirectConsumers:
    """Finding #19 (first symptom): depth=1 ``direct_consumers`` must NEVER be
    empty for a module-private leaf function with real production callers,
    even though ``production_references`` counts them (the "objectively wrong
    []" the finding's migration note calls out). Live re-repro against the
    ORIGINAL finding target (this session, via lore_impact/lore_references)
    shows this is ALREADY fixed; this pins the fix as a regression guard using
    the same repro shape (several distinct production callers of a private
    leaf helper) rather than re-deriving a fresh, unverified corpus.
    """

    async def test_direct_consumers_lists_every_production_caller_of_a_private_leaf(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        files = {
            "privlib.py": _PRIVATE_LEAF_SOURCE,
            "consumer_a.py": _PRIVATE_CONSUMER_A_SOURCE,
            "consumer_b.py": _PRIVATE_CONSUMER_B_SOURCE,
            "consumer_c.py": _PRIVATE_CONSUMER_C_SOURCE,
        }
        trio, _server = await _build_graph(tmp_path, files)
        engine = engine_factory(trio.graph)

        result = await engine.impact(_PRIVATE_TARGET, depth=1)

        # The bug (if it reproduced) would show production_references > 0
        # while direct_consumers stayed empty -- assert them CONSISTENT, not
        # just each independently non-zero.
        assert result.production_references >= 3
        assert len(result.direct_consumers) >= 3, (
            "direct_consumers must list the private leaf's real production "
            f"callers, never []; got {result.direct_consumers!r} against "
            f"{result.production_references} counted production references"
        )
        for module in ("consumer_a", "consumer_b", "consumer_c"):
            assert any(module in name for name in result.direct_consumers), (
                f"{module!r} is a genuine production caller and must be named "
                f"in direct_consumers; got {result.direct_consumers!r}"
            )


# Finding #19 (second symptom, CONFIRMED reproducing live via lore_impact
# against loremaster.search._sanitise_line: server.py -- which imports
# DiffEngine/SnapshotSummary from loremaster.diff, nothing to do with
# _sanitise_line -- showed up as a depth-2 module_rollups consumer purely
# because it imports SOMETHING from the SAME module as a genuine depth-1
# consumer). Root cause (graph_surreal.py's ``_reverse_neighbours``): once a
# MODULE-kind node enters the BFS frontier (a module-level import of the
# target IS a legitimate depth-1 reference), the "module-prefix imports arm"
# -- a DELIBERATE, tested, Kuzu-parity feature genuinely needed by
# blast_radius/lore_map's own semantics, not a graph bug -- pulls in EVERY
# importer of ANYTHING under that module, not only importers of the target
# symbol. This is a real, reproducing overstatement; fixing the shared BFS
# would touch graph_surreal.py's traversal core (used by lore_map too, under
# the map-test-segregation BINDING design law) for a risk/blast-radius far
# beyond this wave's fold scope. The chosen fix is HONEST RENDER (matching the
# #1/#2/#30 pattern): a depth>1 rollup ALWAYS carries an explicit caveat that
# its counts follow the module import graph, not confirmed calls to the exact
# symbol -- never silently overstated as if every rollup member calls the
# target.
_ROLLUP_TARGET_SOURCE = """\
def rollup_target(x):
    \"\"\"The depth>1 rollup-honesty repro target (finding #19, 2nd symptom).\"\"\"
    return x
"""

_ROLLUP_CONSUMER_SOURCE = """\
from pkg.rlib import rollup_target


def uses_target(x):
    \"\"\"A genuine DIRECT (depth-1) consumer.\"\"\"
    return rollup_target(x)


def unrelated(x):
    \"\"\"Lives in the SAME module as the direct consumer but shares NO
    relation to rollup_target -- importers of THIS symbol are the
    import-ripple noise the depth>1 rollup caveat must call out.
    \"\"\"
    return x * 2
"""

_ROLLUP_IMPORTER_SOURCE = """\
from pkg.rconsumer import unrelated


def call_it(x):
    \"\"\"Imports something UNRELATED to rollup_target from the SAME module as
    its direct consumer -- must show up in the depth-2 rollup ONLY because of
    the shared module, never because it calls rollup_target.
    \"\"\"
    return unrelated(x)
"""

_ROLLUP_TARGET = "pkg.rlib.rollup_target"
_ROLLUP_RIPPLE_IMPORTER_MODULE = "rimporter"


class TestModuleRollupImportRippleCaveat:
    """Finding #19 (second symptom): a depth>1 module rollup must carry an
    explicit caveat that its counts follow the transitive MODULE import graph
    -- not confirmed calls to the exact symbol -- so a reader never mistakes a
    large/ripple-inflated count for confirmed usage of the queried symbol.
    """

    async def test_ripple_importer_appears_in_the_rollup_by_construction(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # First prove the corpus actually reproduces the ripple mechanism
        # (the live finding's shape) before asserting the caveat renders.
        files = {
            "pkg/rlib.py": _ROLLUP_TARGET_SOURCE,
            "pkg/rconsumer.py": _ROLLUP_CONSUMER_SOURCE,
            "pkg/rimporter.py": _ROLLUP_IMPORTER_SOURCE,
        }
        trio, _server = await _build_graph(tmp_path, files)
        engine = engine_factory(trio.graph)

        result = await engine.impact(_ROLLUP_TARGET, depth=2)

        modules = [rollup.module for rollup in result.module_rollups]
        assert any(_ROLLUP_RIPPLE_IMPORTER_MODULE in module for module in modules), (
            "the corpus is constructed so rimporter reaches the target ONLY "
            f"via the module-level import ripple; got rollups {modules!r} -- "
            "if this fails, the corpus no longer reproduces the mechanism "
            "the caveat below must warn about"
        )

    async def test_depth_two_rollup_carries_the_import_ripple_caveat(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        files = {
            "pkg/rlib.py": _ROLLUP_TARGET_SOURCE,
            "pkg/rconsumer.py": _ROLLUP_CONSUMER_SOURCE,
            "pkg/rimporter.py": _ROLLUP_IMPORTER_SOURCE,
        }
        trio, _server = await _build_graph(tmp_path, files)
        engine = engine_factory(trio.graph)

        result = await engine.impact(_ROLLUP_TARGET, depth=2)

        assert "import graph" in result.formatted.lower(), (
            "a depth>1 rollup must caveat that its counts follow the module "
            f"import graph, not confirmed symbol usage; got {result.formatted!r}"
        )

    async def test_depth_one_never_carries_the_rollup_caveat(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # The ripple caveat is scoped to depth>1 -- depth 1 has no rollups to
        # caveat, so it must not appear (never a generic always-on banner).
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1)

        assert "import graph" not in result.formatted.lower()


class TestCoveringTestsHonestRender:
    """Findings #1/#2: ``tests_for``'s name/reference heuristic can miss a
    genuinely-covering test (indirectly-exercised helpers, config.py-shaped
    modules) -- improving THAT detection heuristic is explicitly OUT of scope
    for this wave. What IS in scope: a genuine zero-covering-tests result must
    NEVER render as a bare, confident-looking ``tests: 0`` -- it must carry
    the heuristic caveat so a reader knows "none detected" is not the same
    claim as "verified uncovered".
    """

    async def test_zero_covering_tests_renders_the_heuristic_caveat_not_bare_zero(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # _ORPHAN (orphan_helper) has zero references AND zero covering tests
        # by construction (_full_corpus's reflib.py defines it, nothing calls
        # or tests it).
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_ORPHAN, depth=1)

        assert not result.covering_tests
        assert "tests: 0" not in result.formatted, (
            "a genuine covering-tests miss must never render as a bare, "
            f"confident-looking 'tests: 0'; got {result.formatted!r}"
        )
        assert "heuristic" in result.formatted.lower(), (
            "the no-covering-tests render must carry the heuristic caveat "
            "(tests_for can miss indirectly-exercised helpers -- #1/#2)"
        )

    async def test_nonzero_covering_tests_still_render_normally(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        # Regression guard: the honest-empty render must not leak onto the
        # POSITIVE case (a real covering test must still render its name).
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1)

        assert any("test_reflib" in name for name in result.covering_tests)
        assert any("test_reflib" in line for line in result.formatted.splitlines())


class TestCoveringTestsElisionCap:
    """Finding #39: the rendered covering-tests list must cap at a sane top-N
    with an EXPLICIT, non-silent elision trailer (no-silent-caps doctrine) --
    the structured ``covering_tests`` field stays the FULL, uncapped list (a
    programmatic caller loses nothing); only the compact TEXT block caps.
    """

    async def test_covering_tests_render_caps_with_an_announced_elision(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        files = _full_corpus()
        # Add enough additional covering tests to exceed any reasonable cap.
        for i in range(20):
            files[f"tests/test_extra_{i}.py"] = _TEST_REFLIB_SOURCE.replace(
                "test_champion_routing", f"test_champion_routing_extra_{i}"
            )
        trio, _server = await _build_graph(tmp_path, files)
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1)

        assert len(result.covering_tests) > 15, (
            "the STRUCTURED covering_tests field must stay the FULL, "
            f"uncapped list; got only {len(result.covering_tests)}"
        )
        assert "more" in result.formatted.lower(), (
            "the rendered block must announce the elision explicitly (never "
            f"a silent truncation); got {result.formatted!r}"
        )
        assert "covering_tests" in result.formatted, (
            "the elision trailer must teach how to see the rest honestly -- "
            "pointing at the (uncapped) structured covering_tests field"
        )


class TestBareNameUnionCaveat:
    """Finding #30: a bare (unqualified) target may collide with a same-named
    symbol in another module; ``references()`` UNIONS every collidee's profile
    silently (by design -- see graph_surreal.py's ``references`` docstring).
    The render must TEACH this rather than present the union as if it were one
    unambiguous symbol's exact profile. The stronger ask (name the actual
    colliding candidate modules) needs a new engine-level introspection surface
    (``_bare_name_answerers`` is private/internal) -- flagged in
    REPORT-builder-flip-w2.md as a follow-on, out of this wave's writable set.
    """

    async def test_bare_target_render_carries_the_union_caveat(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_TARGET, depth=1)  # _TARGET is bare.

        assert "bare name" in result.formatted.lower(), (
            "a bare-target query must teach that it may be a same-named-symbol "
            f"union, not a single unambiguous profile; got {result.formatted!r}"
        )

    async def test_qualified_target_never_carries_the_bare_name_caveat(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_QUALIFIED_TARGET, depth=1)  # module-qualified.

        assert "bare name" not in result.formatted.lower(), (
            "an already-qualified target names ONE unambiguous symbol -- the "
            "bare-name union caveat must not render for it"
        )


class TestUnknownBareTarget:
    """Finding #30 (the no-match half): an unresolvable BARE name must still
    raise the existing ``ImpactTargetNotFoundError`` teaching path -- never an
    all-zero render that looks like a valid (if dead) verdict. Mirrors
    ``TestUnknownTarget`` above (which pins the dotted-name case) for a
    single-segment, no-dot bare name.
    """

    async def test_unknown_bare_target_raises_naming_it_and_the_next_step(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _full_corpus())
        engine = engine_factory(trio.graph)

        with pytest.raises(_errors().ImpactTargetNotFoundError) as exc_info:
            await engine.impact("totallybogus", depth=1)
        message = str(exc_info.value)
        assert "totallybogus" in message
        assert "lore_search" in message


# --------------------------------------------------------------------------- #
# 9 — finding #53: a from-imported MODULE target renders "live" (engine-level,
# fake graph). ``impact()`` itself changes NOT AT ALL for this fix (P8d′
# SPEC 1 §1.3): it is a pure passthrough over ``graph.references`` /
# ``graph.tests_for``, so this pins that the FIX in graph_surreal.py (mirrored
# in the fake graph's ``references``/``tests_for``) is what flips the render —
# not any change to this engine.
#
# RED before the fix: ``references("rlib.factory")`` returns zero production
# references (the module's own name is never the ``imports`` edge dst — only
# ``rlib.factory.make_widget`` is), so ``impact()`` renders the exact
# ``loresigil.factory`` false "dead (heuristic), 0 refs" verdict reproduced
# live this session (``lore_impact("loresigil.factory")``).
#
# CORPUS: the exact loresigil.factory repro shape — a REAL package (with
# ``__init__.py``) containing a submodule (``factory.py``) whose symbol is
# from-imported both cross-package (a top-level ``consumer.py``) and by a
# test file whose name deliberately does NOT match the module/symbol stem
# (defeats the ``test_x`` <-> ``x`` name heuristic, mirroring the graph-level
# fixture in test_graph_surreal.py's TestTestsForModuleTarget).
# --------------------------------------------------------------------------- #

_RLIB_FACTORY_SOURCE = """\
def make_widget(value):
    \"\"\"Reached via a cross-package from-import, never a plain module import.\"\"\"
    return value
"""

_RLIB_CONSUMER_SOURCE = """\
from rlib.factory import make_widget


def run(value):
    \"\"\"A production caller that imports the SYMBOL, not the module.\"\"\"
    return make_widget(value)
"""

_RLIB_TEST_SOURCE = """\
from rlib.factory import make_widget


def test_widget_end_to_end():
    assert make_widget(1) == 1
"""

_RLIB_MODULE_TARGET = "rlib.factory"


def _rlib_module_target_corpus() -> dict[str, str]:
    return {
        "rlib/__init__.py": "",
        "rlib/factory.py": _RLIB_FACTORY_SOURCE,
        "consumer.py": _RLIB_CONSUMER_SOURCE,
        "tests/test_widget_use.py": _RLIB_TEST_SOURCE,
    }


class TestModuleTargetImpact:
    """finding #53: ``lore_impact`` on a from-imported MODULE renders "live",
    names its consumer, and surfaces its covering test — never the false
    "dead, 0 refs" verdict."""

    async def test_module_target_renders_live_with_consumer_and_covering_test(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_graph(tmp_path, _rlib_module_target_corpus())
        engine = engine_factory(trio.graph)

        result = await engine.impact(_RLIB_MODULE_TARGET, depth=1)

        assert result.verdict == _VERDICT_LIVE
        assert result.production_references == 1
        assert result.direct_consumers == ["consumer"]
        assert any("test_widget_use" in name for name in result.covering_tests)
        assert result.verdict in result.formatted


# =========================================================================== #
# P8d' SPEC 2 (finding #52) — canonical module labels. A depth>1 module
# rollup over a doubled-member-dir layout (``outer/outer/mod.py``, mirroring
# the real repo's ``loremaster/loremaster/``) must render the CANONICAL
# (importable) module name (``outer.mod``), never the raw path-join
# (``outer.outer.mod``) ``_module_rollups``/``_transitive_only_modules`` used
# to derive. Built through the SAME derivation the real indexer uses
# (``graph.importable_module_name(base, file_path)``, exactly
# ``Indexer._importable_module_name``'s own call).
# =========================================================================== #

_OUTER_MOD_TARGET_SOURCE = """\
def target_fn(x):
    \"\"\"The symbol whose depth>1 rollup must render under its CANONICAL module.\"\"\"
    return x
"""

_OUTER_MOD_CONSUMER_SOURCE = """\
from outer.mod import target_fn


def call_target(x):
    \"\"\"The lone importer of the doubled-member-dir module's target symbol.\"\"\"
    return target_fn(x)
"""

_OUTER_MOD_TARGET = "outer.mod.target_fn"
_OUTER_MOD_MODULE = "outer.mod"
_OUTER_MOD_DOUBLED = "outer.outer.mod"  # the OLD path-join derivation -- must NEVER appear
_OUTER_MOD_CONSUMER_MODULE = "consumer"


async def _build_doubled_layout_graph(tmp_path: Path) -> tuple[FakeSurrealTrio, LoreServer]:
    """Build the ``outer/outer/mod.py`` corpus with TRUE importable module names.

    ``outer/outer/__init__.py`` is written to disk ONLY (never graphed) --
    exactly what ``importable_module_name``'s on-disk package-top probe needs.
    Every graphed file's ``module_name`` is computed via
    ``graph.importable_module_name(tmp_path, rel_path)``, the IDENTICAL call
    ``Indexer._importable_module_name`` delegates to in production, never the
    bare ``module_qualified_name`` path-join ``_build_graph``'s default
    omission would derive for a doubled member dir.
    """
    disk_only = {"outer/outer/__init__.py": ""}
    graph_files = {
        "outer/outer/mod.py": _OUTER_MOD_TARGET_SOURCE,
        "consumer.py": _OUTER_MOD_CONSUMER_SOURCE,
    }
    slug = _slug()
    for rel_path, source in {**disk_only, **graph_files}.items():
        _write(tmp_path / rel_path, source)
    config = _config(slug=slug, live_path=tmp_path)
    server = LoreServer(config)
    trio = fake_surreal_trio(dim=_DIM, tier_roots={_TIER: tmp_path}, project_roots=[tmp_path])
    for rel_path, source in graph_files.items():
        module_name = trio.graph.importable_module_name(tmp_path, rel_path)
        await trio.graph.build_file_graph(
            _TIER, rel_path, _chunks_for(server, rel_path, source), module_name=module_name
        )
    return trio, server


class TestDoubledLayoutRollupLabels:
    """finding #52: a depth>1 module rollup over a doubled-member-dir corpus
    renders the CANONICAL module name, never the raw path-join."""

    async def test_rollup_over_doubled_layout_corpus_renders_canonical_module(
        self, tmp_path: Path, engine_factory: Callable[..., Any]
    ) -> None:
        trio, _server = await _build_doubled_layout_graph(tmp_path)
        engine = engine_factory(trio.graph)

        result = await engine.impact(_OUTER_MOD_TARGET, depth=2)

        rollup_modules = {rollup.module for rollup in result.module_rollups}
        assert _OUTER_MOD_MODULE in rollup_modules, (
            "the target's own defining module must roll up under its "
            f"CANONICAL name {_OUTER_MOD_MODULE!r}; got {rollup_modules}"
        )
        assert not any(module.startswith("outer.outer") for module in rollup_modules), (
            f"no rollup module may render the doubled path-join form; got {rollup_modules}"
        )
        assert _OUTER_MOD_DOUBLED not in result.formatted, (
            "the doubled path-join form must never appear in the rendered block"
        )
