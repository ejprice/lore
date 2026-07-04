"""Contract tests for ``loremaster.extension`` — the composition surface.

This module pins the *extension API surface* the loremaster base exposes (plan
AMENDMENT 1, §A1.3 — the eleven seams, refined by §A1.10 C2/C3, and the P6
read-path cutover §6):

* :class:`ExtensionContext` — the shared-services bundle (store, embedder,
  config, ``count_tokens``, manifest) handed to every context-taking seam. It is
  *mutable* so a lifespan hook (seam 9) can stash state on it.
* :class:`Extension` — an ABC base class (NOT a bare Protocol) with a ``name``
  and the eleven seams, **each with a safe no-op/empty default**, so a subclass
  overrides only what it needs and a *bare* server is the generic RAG.
* :class:`ToolSpec` / :class:`PayloadIndexSpec` — the small declarative models
  seams 3 and 8 hand back.
* :class:`SourceProvider` — the indexer-side Protocol (signature only).

**P6 seam-type cutover (§6 item 3).** The unified SurrealDB store's read path
returns a backend-neutral :class:`~loremaster.store.candidate.Candidate`, never a
``qdrant_client`` ``ScoredPoint``. So the three search-pipeline seams that carry a
candidate — ``augment_candidates`` / ``rerank`` / ``format_result`` — now take and
return :class:`Candidate`, and NO qdrant type is reachable from any seam
signature. This is a *breaking* change to the seam types; it is APPROVED because
no extension ships against loremaster yet. ``chunk_key`` already takes a plain
payload ``dict`` and ``classify_detail`` a plain ``chunk_type`` string, so neither
mentions a backend type and neither changes.

The load-bearing invariant the whole framework rests on: **the defaults are
genuinely inert.** A bare :class:`Extension` subclass that overrides nothing must
return ``[]`` / ``None`` / identity for every seam, so that registering zero
extensions yields the generic code/docs RAG. These tests assert that directly,
seam by seam, against a do-nothing subclass — and separately assert that a
:class:`FakeExtension` overriding *every* seam round-trips its overrides.
"""

from __future__ import annotations

import inspect
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Literal

import pytest
import pytest_asyncio
from _extension_helpers import (
    BUILTIN_COLLISION_NAME,
    SCHEMA_TOOL_FACTOR_DEFAULT,
    CollidingExtension,
    CounterExtension,
    FakeExtension,
    IsolationExtensionA,
    IsolationExtensionB,
    ReservedContextArgExtension,
    SchemaShapesExtension,
    UnannotatedArgExtension,
    minimal_config,
)
from _surreal_fakes import fake_surreal_trio
from loremaster.extension import (
    Extension,
    ExtensionContext,
    SourceProvider,
    ToolSpec,
)
from loremaster.store.candidate import Candidate
from loresigil.testing import FakeEmbedder
from pydantic import ValidationError


class TestExtensionContext:
    """The shared-services bundle handed to context-taking seams."""

    def test_bundles_the_shared_services_and_is_typed(self) -> None:
        embedder = FakeEmbedder(dim=8)
        config = minimal_config()
        manifest = fake_surreal_trio(dim=8).manifest
        # The store needs no live client merely to be carried in the context.
        store = object()  # a stand-in handle; the context only *carries* it
        ctx = ExtensionContext(
            store=store,
            embedder=embedder,
            config=config,
            count_tokens=embedder.count_tokens,
            manifest=manifest,
        )
        assert ctx.store is store
        assert ctx.embedder is embedder
        assert ctx.config is config
        assert ctx.manifest is manifest
        # ``count_tokens`` is the embedder's batch counter, carried verbatim.
        assert ctx.count_tokens(["hello world"]) == embedder.count_tokens(["hello world"])

    def test_is_mutable_so_a_lifespan_hook_can_stash_state(self) -> None:
        # Seam 9 (§A1.3.9): ``on_startup`` "may stash state on the mutable
        # ExtensionContext". A frozen model would make that impossible.

        embedder = FakeEmbedder(dim=8)
        manifest = fake_surreal_trio(dim=8).manifest
        ctx = ExtensionContext(
            store=object(),
            embedder=embedder,
            config=minimal_config(),
            count_tokens=embedder.count_tokens,
            manifest=manifest,
        )
        ctx.state["session"] = "stashed-by-startup"  # noqa: F821 - attribute under test
        assert ctx.state["session"] == "stashed-by-startup"

class TestToolSpec:
    """The declarative tool spec seam 3 hands back (no FastMCP coupling)."""

    def test_carries_name_callable_description_io(self) -> None:

        def _list_modules(tier: str) -> list[str]:
            return [f"mod-in-{tier}"]

        spec = ToolSpec(
            name="list_modules",
            handler=_list_modules,
            description="List modules indexed under a tier.",
            input_schema={"tier": "str"},
            output_schema={"modules": "list[str]"},
        )
        assert spec.name == "list_modules"
        assert spec.description.startswith("List modules")
        assert spec.input_schema == {"tier": "str"}
        assert spec.output_schema == {"modules": "list[str]"}
        # The handler is a real callable invocable without any server machinery.
        assert spec.handler("community") == ["mod-in-community"]

class TestFieldIndexSpec:
    """The declarative extra-index spec seam 8 hands back (P6 close-out rename).

    Renamed from ``PayloadIndexSpec``/``PayloadIndexKind`` to the backend-neutral
    ``FieldIndexSpec`` (``field_name`` + ``kind``): Qdrant's KEYWORD/BOOL-only
    vocabulary is gone, and the model gains a NEW ``"fulltext"`` kind — a
    BM25-indexable text field (the ``llm_summary`` / P9 enrichment hook). The
    import is LOCAL to each test (not hoisted to the top of the module) so a
    not-yet-implemented name fails only that one test, never the whole module's
    collection.
    """

    def test_models_a_keyword_field(self) -> None:
        from loremaster.extension import FieldIndexSpec

        spec = FieldIndexSpec(field_name="model_name", kind="keyword")
        assert spec.field_name == "model_name"
        assert spec.kind == "keyword"

    def test_models_a_bool_field(self) -> None:
        from loremaster.extension import FieldIndexSpec

        spec = FieldIndexSpec(field_name="is_installed", kind="bool")
        assert spec.kind == "bool"

    def test_models_a_fulltext_field(self) -> None:
        # NEW in the P6 close-out: a BM25-indexable text field (the llm_summary /
        # P9 enrichment hook) — the reason this seam moved off Qdrant's
        # KEYWORD/BOOL-only vocabulary onto a backend-neutral one.
        from loremaster.extension import FieldIndexSpec

        spec = FieldIndexSpec(field_name="llm_summary", kind="fulltext")
        assert spec.field_name == "llm_summary"
        assert spec.kind == "fulltext"

    def test_rejects_an_unknown_kind(self) -> None:
        # An unknown kind is a config bug that must fail loudly rather than
        # silently skip the index. The ``type: ignore`` is deliberate — mypy
        # correctly flags the bad literal at type-check time; this asserts the
        # *runtime* validation also rejects it.
        from loremaster.extension import FieldIndexSpec

        with pytest.raises(ValidationError):
            FieldIndexSpec(field_name="x", kind="geo")  # type: ignore[arg-type]

    def test_rejects_an_unexpected_field(self) -> None:
        # extra="forbid" — the same fail-loud-on-typo contract every other
        # declarative seam model (ToolSpec, the pre-rename spec) carries.
        from loremaster.extension import FieldIndexSpec

        with pytest.raises(ValidationError):
            FieldIndexSpec(field_name="x", kind="keyword", schema_type="keyword")  # type: ignore[call-arg]

class TestFieldIndexSpecRenameIsComplete:
    """The pre-P6-close-out ``PayloadIndexSpec``/``PayloadIndexKind`` names are GONE.

    Breaking rename APPROVED (no extension ships against loremaster yet, per the
    module docstring's P6 candidate-cutover precedent) — but a HALF-finished
    rename, where ``FieldIndexSpec`` is added yet the old names stay importable,
    must not ship: an extension author reaching for the old name would silently
    write against a name the store no longer wires anything to.
    """

    def test_payload_index_spec_class_is_absent(self) -> None:
        import loremaster.extension as extension_module

        assert not hasattr(extension_module, "PayloadIndexSpec"), (
            "PayloadIndexSpec must be fully removed by the FieldIndexSpec rename "
            "— a half-rename (both names present) must not ship"
        )

    def test_payload_index_kind_alias_is_absent(self) -> None:
        import loremaster.extension as extension_module

        assert not hasattr(extension_module, "PayloadIndexKind"), (
            "PayloadIndexKind must be fully removed by the FieldIndexSpec rename"
        )

class TestFieldIndexesCollectedByLoreServer:
    """A registered extension's ``FieldIndexSpec``\\ s surface through the SAME
    ``LoreServer`` collection point the pre-rename ``payload_index_specs`` pin
    exercised (``test_server.py``'s ``test_seam8_payload_indexes_are_collected``)
    — mirrored here at the P6 close-out over the renamed model.
    """

    def test_registered_extension_field_indexes_are_collected(self) -> None:
        from loremaster.extension import Extension, FieldIndexSpec
        from loremaster.server import LoreServer

        class _FieldIndexDeclaringExtension(Extension):
            """A local (test-only) extension declaring all three FieldIndexSpec kinds."""

            @property
            def name(self) -> str:
                return "field_index_demo"

            def payload_indexes(self) -> list[FieldIndexSpec]:
                return [
                    FieldIndexSpec(field_name="model_name", kind="keyword"),
                    FieldIndexSpec(field_name="is_installed", kind="bool"),
                    FieldIndexSpec(field_name="llm_summary", kind="fulltext"),
                ]

        server = LoreServer(minimal_config()).register_extension(
            _FieldIndexDeclaringExtension()
        )
        specs = server.payload_index_specs
        by_field = {spec.field_name: spec.kind for spec in specs}
        assert by_field == {
            "model_name": "keyword",
            "is_installed": "bool",
            "llm_summary": "fulltext",
        }

class TestSourceProviderSignature:
    """``SourceProvider`` — signature only (the concrete impl is the next batch)."""

    def test_a_conforming_provider_satisfies_the_protocol(self, tmp_path: Path) -> None:

        class _DummyProvider:
            """A minimal conforming provider — declares ``tier`` + ``acquire``."""

            tier = "vendor"

            def acquire(self, tier: str, snapshot_root: Path) -> None:
                # The contract: materialise the tier's files INTO the snapshot
                # layout (it does not stream bytes). Here we just touch a marker.
                (snapshot_root / f"{tier}.acquired").write_text("ok", encoding="utf-8")

        provider: SourceProvider = _DummyProvider()
        # ``runtime_checkable`` so a structural conformance check is meaningful.
        assert isinstance(provider, SourceProvider)
        provider.acquire("vendor", tmp_path)
        assert (tmp_path / "vendor.acquired").read_text(encoding="utf-8") == "ok"

    def test_a_non_conforming_object_is_rejected_by_isinstance(self) -> None:

        class _MissingAcquire:
            tier = "vendor"

        assert not isinstance(_MissingAcquire(), SourceProvider)

class TestExtensionIsAnAbcNotAProtocol:
    """``Extension`` is an ABC base class with a required ``name`` (D2 / directive)."""

    def test_subclass_must_supply_a_name(self) -> None:
        # The ABC leaves ``name`` abstract — a subclass that does not implement it
        # cannot be instantiated, so an unnamed extension can never be registered.

        class _Unnamed(Extension):
            pass

        with pytest.raises(TypeError):
            _Unnamed()  # type: ignore[abstract]

    def test_named_subclass_overriding_nothing_else_instantiates(self) -> None:

        class _Named(Extension):
            @property
            def name(self) -> str:
                return "bare"

        ext = _Named()
        assert ext.name == "bare"


@pytest.fixture()
def bare_extension() -> Any:
    """A named :class:`Extension` subclass that overrides ONLY ``name``.

    Every seam must therefore use its inert default. This is the structural
    stand-in for "a bare server = generic RAG": if any default is non-inert, a
    test below fails.
    """

    class _Bare(Extension):
        @property
        def name(self) -> str:
            return "bare"

    return _Bare()

@pytest.fixture()
def ext_context() -> Any:
    """An :class:`ExtensionContext` over fakes for the context-taking seams."""

    embedder = FakeEmbedder(dim=8)
    manifest = fake_surreal_trio(dim=8).manifest
    return ExtensionContext(
        store=object(),
        embedder=embedder,
        config=minimal_config(),
        count_tokens=embedder.count_tokens,
        manifest=manifest,
    )

class TestBareDefaultsAreInert:
    """The defaults make a bare extension the generic RAG (the whole point)."""

    def test_seam1_chunkers_default_empty(self, bare_extension: Any) -> None:
        assert bare_extension.chunkers() == []

    def test_seam2_profiles_default_empty(self, bare_extension: Any) -> None:
        assert bare_extension.xml_profiles() == []
        assert bare_extension.js_profiles() == []

    def test_seam3_tools_default_empty(self, bare_extension: Any, ext_context: Any) -> None:
        assert bare_extension.tools(ext_context) == []

    def test_seam4_augment_candidates_default_identity(
        self, bare_extension: Any, ext_context: Any
    ) -> None:
        candidates = [_candidate("a", 0.9), _candidate("b", 0.5)]
        # Identity: same objects, same order — the base must not reshape the set.
        result = bare_extension.augment_candidates("query", candidates, ext_context)
        assert result == candidates
        # P6: the seam now carries backend-neutral Candidates (key, not id).
        assert [c.key for c in result] == ["a", "b"]

    def test_seam4_rerank_default_identity(self, bare_extension: Any, ext_context: Any) -> None:
        candidates = [_candidate("a", 0.9), _candidate("b", 0.5)]
        assert bare_extension.rerank(candidates, ext_context) == candidates

    def test_seam5_format_result_default_none(self, bare_extension: Any, ext_context: Any) -> None:
        # ``None`` ⇒ the base supplies its default citation/format.
        assert bare_extension.format_result(_candidate("a", 0.9), ext_context) is None

    def test_seam6_chunk_key_default_none(self, bare_extension: Any, ext_context: Any) -> None:
        # ``None`` ⇒ the base uses its structural point-ID, not an extension key.
        assert bare_extension.chunk_key({"file_path": "a.py"}, ext_context) is None

    def test_seam7_config_model_default_none(self, bare_extension: Any) -> None:
        # ``None`` ⇒ no extra config slice to validate.
        assert bare_extension.config_model() is None

    def test_seam8_payload_indexes_default_empty(self, bare_extension: Any) -> None:
        assert bare_extension.payload_indexes() == []

    @pytest.mark.asyncio
    async def test_seam9_lifespan_hooks_default_noop(
        self, bare_extension: Any, ext_context: Any
    ) -> None:
        # Awaitable no-ops: they must complete without touching anything.
        assert await bare_extension.on_startup(ext_context) is None
        assert await bare_extension.on_shutdown(ext_context) is None

    def test_seam10_source_providers_default_empty(self, bare_extension: Any) -> None:
        assert bare_extension.source_providers() == []

    def test_seam11_classify_detail_default_none(self, bare_extension: Any) -> None:
        # ``None`` ⇒ base default classification (C2). Unchanged by P6: this seam
        # takes a plain chunk-type string, never a backend candidate type.
        assert bare_extension.classify_detail("class") is None

def _candidate(point_id: str, score: float, payload: dict[str, Any] | None = None) -> Candidate:
    """Build a :class:`~loremaster.store.candidate.Candidate` for the seam tests.

    P6 read-path cutover: the search-pipeline seams operate on the backend-neutral
    :class:`Candidate` (``key`` / ``score`` / ``payload`` / ``origin``), NEVER a
    ``qdrant_client`` ``ScoredPoint``. ``origin="fused"`` mirrors the store's RRF
    hybrid-search hits (the sole production source of these candidates).
    """
    return Candidate(key=point_id, score=score, payload=payload or {}, origin="fused")

class TestFakeExtensionRoundTrips:
    """A :class:`FakeExtension` overriding every seam returns its overrides.

    This is the mirror of the inert-defaults suite: it proves the seams are real
    override points (not, say, ``@final`` or swallowed), so :class:`LoreServer`
    has something to wire.

    NOTE (P6 cross-file dependency): ``_extension_helpers.FakeExtension`` overrides
    the three candidate-carrying seams; with the P6 cutover its
    ``augment_candidates`` must inject a :class:`Candidate` keyed ``"injected"`` and
    ``format_result`` must render ``result.key``. Until that helper is moved
    ScoredPoint→Candidate these assertions stay RED (the helper still emits a
    ``ScoredPoint`` and reads ``.id``).
    """

    def test_every_seam_is_overridable(self, ext_context: Any) -> None:

        ext = FakeExtension()
        assert ext.name == "fake"
        # seam 1
        assert len(ext.chunkers()) == 1
        # seam 2
        assert len(ext.xml_profiles()) == 1
        assert len(ext.js_profiles()) == 1
        # seam 3
        tools = ext.tools(ext_context)
        assert [t.name for t in tools] == ["fake_tool"]
        # seam 4 — candidate augmentation injects, rerank reorders. The injected
        # candidate is a backend-neutral Candidate keyed "injected" (P6).
        base = [_candidate("a", 0.5), _candidate("b", 0.9)]
        augmented = ext.augment_candidates("q", base, ext_context)
        assert any(c.key == "injected" for c in augmented)
        reranked = ext.rerank(augmented, ext_context)
        assert [c.score for c in reranked] == sorted(
            (c.score for c in reranked), reverse=True
        )
        # seam 5 — formats off the Candidate's ``key`` (not a qdrant ``id``).
        assert ext.format_result(_candidate("a", 0.5), ext_context) == "FAKE: a"
        # seam 6 — versioned key
        key = ext.chunk_key({"model_name": "sale.order"}, ext_context)
        assert key is not None and key.startswith("fake:") and ext.key_version == 7
        # seam 7
        model = ext.config_model()
        assert model is not None
        # seam 8
        specs = ext.payload_indexes()
        assert {s.field_name for s in specs} == {"model_name", "is_installed"}
        # seam 10
        assert [p.tier for p in ext.source_providers()] == ["vendor"]
        # seam 11 (C2)
        assert ext.classify_detail("fake_summary") == "summary"
        assert ext.classify_detail("fake_body") == "source"

    @pytest.mark.asyncio
    async def test_lifespan_hooks_are_awaited_and_record_state(self, ext_context: Any) -> None:

        ext = FakeExtension()
        await ext.on_startup(ext_context)
        assert ext_context.state["fake_started"] is True
        await ext.on_shutdown(ext_context)
        assert ext_context.state["fake_stopped"] is True

    def test_classify_detail_return_is_constrained(self) -> None:
        # Seam 11 must return one of the two detail levels (or None). The Literal
        # is the contract; assert the concrete values the fake returns.

        ext = FakeExtension()
        levels: set[Literal["summary", "source"] | None] = {
            ext.classify_detail("fake_summary"),
            ext.classify_detail("fake_body"),
            ext.classify_detail("unknown_to_fake"),
        }
        assert levels == {"summary", "source", None}


# --------------------------------------------------------------------------- #
# P6 seam-type cutover (§6 item 3): the candidate-carrying seams speak Candidate.
# --------------------------------------------------------------------------- #
# The unified SurrealDB read path returns :class:`Candidate`, so the three seams
# that receive/return a candidate must be typed on it, and NO ``qdrant`` /
# ``ScoredPoint`` type may remain reachable from an extension seam signature (the
# whole point of the neutral candidate: a domain extension is decoupled from the
# concrete search backend). Breaking is APPROVED — no extension ships yet.
_CANDIDATE_SEAMS = ("augment_candidates", "rerank", "format_result")


class TestExtensionSeamTypesAreCandidate:
    """The candidate-carrying seams are typed on Candidate, never a qdrant type."""

    @pytest.mark.parametrize("seam_name", _CANDIDATE_SEAMS)
    def test_seam_signature_references_candidate_not_scoredpoint(
        self, seam_name: str
    ) -> None:
        # The seam's declared type must be the backend-neutral Candidate; a
        # lingering ``ScoredPoint`` annotation would recouple every extension to
        # qdrant, defeating the store swap. Inspect the source-level signature
        # (``from __future__ import annotations`` keeps these as strings).
        signature = str(inspect.signature(getattr(Extension, seam_name)))
        assert "Candidate" in signature, (
            f"seam {seam_name!r} must carry the backend-neutral Candidate type; "
            f"got signature {signature!r}"
        )
        assert "ScoredPoint" not in signature, (
            f"seam {seam_name!r} still references the qdrant ScoredPoint type — the "
            f"P6 read path returns Candidate, so no seam may name a backend type"
        )
        assert "qdrant" not in signature.lower(), (
            f"seam {seam_name!r} must not name any qdrant type in its signature"
        )

    def test_extension_module_imports_no_qdrant_scoredpoint(self) -> None:
        # Belt-and-braces on the module itself: with every seam de-qdrant-ified the
        # extension module must not even import ``ScoredPoint`` (a dangling import
        # is a latent recoupling waiting for the next edit to reuse it).
        import loremaster.extension as extension_module

        assert not hasattr(extension_module, "ScoredPoint"), (
            "loremaster.extension must not import qdrant's ScoredPoint after the "
            "P6 candidate cutover"
        )

    def test_a_candidate_flows_through_augment_rerank_format_unchanged_in_type(
        self, ext_context: Any
    ) -> None:
        # The end-to-end type contract: a Candidate handed into augment_candidates
        # survives rerank as a Candidate and is formattable by format_result — the
        # exact chain the search pipeline runs (§6 item 3). If any seam silently
        # re-wrapped it into a backend type, one of these isinstance checks fails.
        ext = FakeExtension()
        seed = [_candidate("hit-1", 0.5, payload={"file_path": "pkg/a.py"})]

        augmented = ext.augment_candidates("q", seed, ext_context)
        assert augmented and all(isinstance(c, Candidate) for c in augmented)

        reranked = ext.rerank(augmented, ext_context)
        assert reranked and all(isinstance(c, Candidate) for c in reranked)

        rendered = ext.format_result(reranked[0], ext_context)
        assert isinstance(rendered, str)


# --------------------------------------------------------------------------- #
# Seam 3 LIVE-SERVER wiring: an extension's ToolSpec reaches the MCP surface.
# --------------------------------------------------------------------------- #
# The bug this suite pins: ``LoreServer.tool_specs(ctx)`` collects an extension's
# seam-3 tools as value objects (the composition tests above prove that), but the
# FastMCP server build never registered them — ``_register_tools`` hardcoded only
# the twelve built-ins and ignored the server's extension tools. So an extension's
# tools reached the live MCP surface NOWHERE. These tests drive the REAL
# ``build_mcp_server`` + a live ``build_app_context`` (the same path
# ``test_mcp_server.py`` uses) and assert an extension tool (a) APPEARS in
# ``tools/list`` alongside the twelve built-ins, (b) exposes its declared input
# schema, and (c) is INVOCABLE end-to-end through the FastMCP tool dispatch with
# the handler closing over the RUNTIME ExtensionContext — not merely callable as a
# bare ``spec.handler()`` (the vacuous version the composition tests already pass).

_DIM = 2048

# The twelve built-in tools (the seam-3 wiring must be purely ADDITIVE to these).
# Each carries the mandatory ``lore_`` service prefix; extension tools do NOT (an
# extension owns its own tool names — only the built-ins are prefixed).
_BUILTIN_TOOLS = {
    "lore_search_code",
    "lore_read_file",
    "lore_get_symbol",
    "lore_save_memory",
    "lore_recall_memory",
    "lore_reindex",
    "lore_index_status",
    "lore_what_imports",
    "lore_blast_radius",
    "lore_tests_for",
    "lore_references",
    "lore_dead_code",
}


def _surreal_url() -> str:
    from _surreal_harness import surreal_url

    return surreal_url()


def _surreal_env_creds(monkeypatch_or_none: Any = None) -> tuple[str, str]:
    from _surreal_harness import surreal_password, surreal_user

    return surreal_user(), surreal_password()


def _server_config(slug: str, live_path: Path) -> Any:
    """A valid :class:`LoreConfig` for a live ``build_app_context`` (dim 2048)."""
    from loremaster.config import LoreConfig

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
        # The P5 write stack: a throwaway per-call database on the dev server
        # (unique via the slug, which each caller mints per test).
        "surreal": {
            "url": _surreal_url(),
            "namespace": "lore_test",
            "database": slug,
            "user_env": "SURREAL_USER",
            "password_env": "SURREAL_PASS",
        },
        "roots": [
            {"tier": "custom", "watch": "live", "path": str(live_path), "include": ["**/*.py"]}
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9234},
    }
    return LoreConfig.model_validate(payload)


class _FakeRequestContext:
    """A stand-in MCP request context exposing the lifespan :class:`AppContext`."""

    def __init__(self, app_context: Any) -> None:
        self.lifespan_context = app_context


class _FakeToolContext:
    """A stand-in FastMCP ``Context`` whose ``request_context`` carries the AppContext.

    A registered extension-tool wrapper reads the live AppContext off the request
    context (to reach the RUNTIME ``ExtensionContext`` the handler closes over);
    this minimal double drives the real wrapper body without standing up the full
    streamable-http session machinery — the same approach ``test_mcp_server.py``
    uses for the built-in wrappers.
    """

    def __init__(self, app_context: Any) -> None:
        self.request_context = _FakeRequestContext(app_context)


class TestSeam3ExtensionToolsAreWiredIntoTheLiveServer:
    """An extension's seam-3 ToolSpec is registered as a live, invocable MCP tool."""

    @pytest_asyncio.fixture()
    async def qdrant(self) -> AsyncIterator[Any]:
        """A real Qdrant client with exact-name (concurrency-safe) teardown."""
        from conftest import QDRANT_URL, _qdrant_api_key
        from qdrant_client import AsyncQdrantClient

        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created: list[str] = []
        client._lore_created = created  # type: ignore[attr-defined]
        try:
            yield client
        finally:
            for name in created:
                for candidate in (name, f"{name}_memory"):
                    if await client.collection_exists(candidate):
                        await client.delete_collection(candidate)
            await client.close()

    @staticmethod
    def _slug() -> str:
        return f"test_{uuid.uuid4().hex}"

    async def _live_context(self, *, server: Any, qdrant: Any, tmp_path: Path) -> Any:
        """Build a live :class:`AppContext` over the server (real Qdrant, fake embedder).

        Exports the dev server's SurrealDB credentials (the P5 write stack
        resolves them by env-var name at construction) — idempotent, the same
        values the harness resolves. The per-test surreal database is the SLUG
        (unique per test); the caller's ``finally`` drops it via
        ``_drop_surreal_db``.
        """
        import os

        from _surreal_harness import surreal_password, surreal_user
        from loremaster.server import build_app_context

        os.environ.setdefault("SURREAL_USER", surreal_user())
        os.environ.setdefault("SURREAL_PASS", surreal_password())
        slug = server.config.project.slug
        qdrant._lore_created.append(f"lore_{slug}")
        qdrant._lore_created.append(f"lore_{slug}_memory")
        return await build_app_context(
            server=server,
            embedder=FakeEmbedder(dim=_DIM),
            qdrant_client=qdrant,
            manifest_path=tmp_path / "m.db",
            snapshot_root=tmp_path / "snap",
            start_tasks=False,
        )

    @staticmethod
    async def _drop_surreal_db(slug: str) -> None:
        """Reap the per-test surreal database (named = the test's unique slug)."""
        from _surreal_harness import drop_database, make_env

        await drop_database(make_env(database=slug, dim=_DIM))

    async def test_extension_tool_appears_in_tools_list_with_the_ten_builtins(
        self, tmp_path: Path
    ) -> None:
        # RED today: the extension's ``bump_counter`` tool is collected by
        # ``server.tool_specs`` but NEVER registered, so it is absent from the live
        # ``tools/list``. The twelve built-ins are present either way.
        from loremaster.server import LoreServer, build_mcp_server

        slug = self._slug()
        config = _server_config(slug, tmp_path / "live")
        server = LoreServer(config).register_extension(CounterExtension())
        mcp = build_mcp_server(server)

        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        # Purely additive: the twelve built-ins are untouched.
        assert _BUILTIN_TOOLS <= names
        # The extension tool now rides alongside them on the live surface.
        assert "bump_counter" in names

    async def test_extension_tool_exposes_its_declared_input_schema(
        self, tmp_path: Path
    ) -> None:
        # The ToolSpec.input_schema ({"count": "int"}) must be translated into the
        # registered tool's parameters so the MCP consumer sees the ``count`` arg.
        from loremaster.server import LoreServer, build_mcp_server

        slug = self._slug()
        config = _server_config(slug, tmp_path / "live")
        server = LoreServer(config).register_extension(CounterExtension())
        mcp = build_mcp_server(server)

        tools = await mcp.list_tools()
        bump = next(t for t in tools if t.name == "bump_counter")
        # The declared ``count`` input is visible on the tool's input schema.
        assert "count" in bump.inputSchema.get("properties", {})

    async def test_extension_tool_is_invocable_end_to_end_with_runtime_ctx(
        self, tmp_path: Path, qdrant: Any
    ) -> None:
        # The real end-to-end proof (not the vacuous ``spec.handler()`` direct call):
        # drive the REGISTERED FastMCP wrapper against a LIVE AppContext and get the
        # handler's result back. The handler closes over the RUNTIME
        # ExtensionContext, whose per-extension state namespace the ``on_startup``
        # hook seeded — so the returned total reflects that live state.
        from loremaster.server import LoreServer, build_mcp_server

        live = tmp_path / "live"
        live.mkdir()
        slug = self._slug()
        config = _server_config(slug, live)
        ext = CounterExtension()
        server = LoreServer(config).register_extension(ext)
        mcp = build_mcp_server(server)
        ctx = await self._live_context(server=server, qdrant=qdrant, tmp_path=tmp_path)
        try:
            tool = mcp._tool_manager.get_tool("bump_counter")  # noqa: SLF001
            assert tool is not None
            # Call the registered wrapper through a fake lifespan Context, exactly as
            # the live streamable-http dispatch would. The runtime ctx's per-extension
            # state was seeded to 100 by on_startup, so a +5 bump returns 105 — proof
            # the handler closed over the RUNTIME context, not a placeholder.
            result = await tool.fn(_FakeToolContext(ctx), count=5)
            assert result == ext.on_startup_seed() + 5
            # A second call accumulates on the SAME live state (105 → 108).
            again = await tool.fn(_FakeToolContext(ctx), count=3)
            assert again == ext.on_startup_seed() + 5 + 3
        finally:
            await ctx.aclose()
            await self._drop_surreal_db(server.config.project.slug)

    async def test_extension_tool_name_colliding_with_a_builtin_raises(
        self, tmp_path: Path
    ) -> None:
        # An extension tool must not silently shadow a built-in (or be shadowed by
        # it). Registering a tool under a built-in name raises a clear error at
        # build time, naming the offending tool.
        from loremaster.server import LoreServer, build_mcp_server

        slug = self._slug()
        config = _server_config(slug, tmp_path / "live")
        server = LoreServer(config).register_extension(CollidingExtension())
        with pytest.raises(ValueError, match=BUILTIN_COLLISION_NAME):
            build_mcp_server(server)

    async def test_two_extensions_with_the_same_tool_name_raises(
        self, tmp_path: Path
    ) -> None:
        # The collision guard covers EXTENSION-vs-EXTENSION too, not just vs a
        # built-in: two extensions contributing the same tool name must raise at
        # registration (the second cannot silently shadow the first). The audit
        # flagged this as untested-but-working — lock it.
        from loremaster.server import LoreServer, build_mcp_server

        slug = self._slug()
        config = _server_config(slug, tmp_path / "live")
        # Two CounterExtension-like extensions both contribute ``bump_counter``;
        # register two distinct extensions whose tools collide on a name.
        server = (
            LoreServer(config)
            .register_extension(CounterExtension())
            .register_extension(_DuplicateBumpExtension())
        )
        with pytest.raises(ValueError, match="bump_counter"):
            build_mcp_server(server)

    async def test_optional_arg_is_not_required_and_invocable_without_it(
        self, tmp_path: Path, qdrant: Any
    ) -> None:
        # CONTRACT GAP #1 (optionality lost). The handler declares
        # ``factor: int = SCHEMA_TOOL_FACTOR_DEFAULT``; the published inputSchema
        # must therefore NOT list ``factor`` in ``required`` (a required scalar with
        # no default stays required), AND the tool must be invocable WITHOUT
        # ``factor`` — the handler supplies its default. RED today: ``factor`` is
        # wrongly published as required (every arg is KEYWORD_ONLY with no default).
        from loremaster.server import LoreServer, build_mcp_server

        live = tmp_path / "live"
        live.mkdir()
        slug = self._slug()
        config = _server_config(slug, live)
        server = LoreServer(config).register_extension(SchemaShapesExtension())
        mcp = build_mcp_server(server)

        tools = await mcp.list_tools()
        echo = next(t for t in tools if t.name == "echo_shapes")
        required = set(echo.inputSchema.get("required", []))
        # The no-default scalar/containers stay required; the defaulted one does not.
        assert "required" in required
        assert "factor" not in required, (
            "an arg with a handler default must publish as NOT required"
        )

        ctx = await self._live_context(server=server, qdrant=qdrant, tmp_path=tmp_path)
        try:
            tool = mcp._tool_manager.get_tool("echo_shapes")  # noqa: SLF001
            # Invoke WITHOUT ``factor`` — the handler's default must apply.
            result = await tool.fn(
                _FakeToolContext(ctx),
                required="r",
                items=["a", "b"],
                mapping={"k": 1},
            )
            assert result["factor"] == SCHEMA_TOOL_FACTOR_DEFAULT
            assert result["items"] == ["a", "b"]
        finally:
            await ctx.aclose()
            await self._drop_surreal_db(server.config.project.slug)

    async def test_non_scalar_args_publish_correct_json_schema_types(
        self, tmp_path: Path
    ) -> None:
        # CONTRACT GAP #2 (non-scalar collapse to string). A ``list[str]`` arg must
        # publish ``type: array`` and a ``dict[str, int]`` arg ``type: object`` — NOT
        # silently ``type: string``. RED today: both collapse to string.
        from loremaster.server import LoreServer, build_mcp_server

        slug = self._slug()
        config = _server_config(slug, tmp_path / "live")
        server = LoreServer(config).register_extension(SchemaShapesExtension())
        mcp = build_mcp_server(server)

        tools = await mcp.list_tools()
        echo = next(t for t in tools if t.name == "echo_shapes")
        props = echo.inputSchema["properties"]
        assert props["items"]["type"] == "array", "list[str] must publish as array, not string"
        assert props["items"]["items"]["type"] == "string"
        assert props["mapping"]["type"] == "object", "dict must publish as object, not string"
        # The required scalar is still a plain string.
        assert props["required"]["type"] == "string"

    async def test_reserved_context_arg_raises_a_clear_error(self, tmp_path: Path) -> None:
        # An arg named ``context`` collides with FastMCP's injected request Context.
        # Registration must raise a CLEAR error naming the offending ToolSpec — never
        # the cryptic internal "duplicate parameter name" crash.
        from loremaster.server import LoreServer, build_mcp_server

        slug = self._slug()
        config = _server_config(slug, tmp_path / "live")
        server = LoreServer(config).register_extension(ReservedContextArgExtension())
        with pytest.raises(ValueError, match="uses_context"):
            build_mcp_server(server)

    async def test_unannotated_arg_fails_loud_not_silent_string(
        self, tmp_path: Path
    ) -> None:
        # An un-annotated handler param would silently publish as ``type: string``
        # (the silent-wrong-schema bug class). Registration must FAIL LOUD naming
        # the offending ToolSpec + field instead of coercing.
        from loremaster.server import LoreServer, build_mcp_server

        slug = self._slug()
        config = _server_config(slug, tmp_path / "live")
        server = LoreServer(config).register_extension(UnannotatedArgExtension())
        with pytest.raises(ValueError, match="mystery"):
            build_mcp_server(server)

    async def test_cross_extension_tool_state_is_isolated(
        self, tmp_path: Path, qdrant: Any
    ) -> None:
        # Two extensions, each with its OWN private lifespan state + a tool reading
        # it. One extension's tool must see ONLY its own sentinel and NEVER the
        # sibling's key (fix B isolation, exercised through the live tool surface).
        # The audit flagged cross-extension isolation as untested-on-the-tool-path.
        from loremaster.server import LoreServer, build_mcp_server

        live = tmp_path / "live"
        live.mkdir()
        slug = self._slug()
        config = _server_config(slug, live)
        server = (
            LoreServer(config)
            .register_extension(IsolationExtensionA())
            .register_extension(IsolationExtensionB())
        )
        mcp = build_mcp_server(server)
        ctx = await self._live_context(server=server, qdrant=qdrant, tmp_path=tmp_path)
        try:
            tool_a = mcp._tool_manager.get_tool("read_state_a")  # noqa: SLF001
            tool_b = mcp._tool_manager.get_tool("read_state_b")  # noqa: SLF001
            out_a = await tool_a.fn(_FakeToolContext(ctx))
            out_b = await tool_b.fn(_FakeToolContext(ctx))
            # Each sees its own sentinel...
            assert out_a["own"] == "alpha"
            assert out_b["own"] == "beta"
            # ...and NEVER the sibling's key (no state bleed across extensions).
            assert out_a["saw_sibling"] is False
            assert out_b["saw_sibling"] is False
        finally:
            await ctx.aclose()
            await self._drop_surreal_db(server.config.project.slug)


class _DuplicateBumpExtension(Extension):
    """A second extension that re-uses ``bump_counter`` to force an ext-vs-ext clash."""

    @property
    def name(self) -> str:
        return "duplicate_bumper"

    def tools(self, ctx: ExtensionContext) -> list[ToolSpec]:
        def _also_bump(count: int = 1) -> int:
            return count

        return [
            ToolSpec(
                name="bump_counter",
                handler=_also_bump,
                description="A colliding second bump tool.",
                input_schema={"count": "int"},
                output_schema={"total": "int"},
            )
        ]


# --------------------------------------------------------------------------- #
# ctx.store flip: the runtime ExtensionContext must carry the UNIFIED SurrealDB
# store the search pipeline reads, never the legacy QdrantStore (P6 close-out).
# --------------------------------------------------------------------------- #
class TestRuntimeExtensionContextStoreIsUnifiedSurreal:
    """P6 close-out ctx.store flip: the RUNTIME ``ExtensionContext.store`` the
    search seams + startup hooks receive must be the unified SurrealStore the
    search pipeline reads (``AppContext.write_store``), never the legacy
    ``QdrantStore`` (``AppContext.store``).

    Pinned against the REAL ``build_app_context`` composition — the strongest
    testable seam for this bug: at the ``_make_pipeline``/fake-trio level
    ``test_search.py`` already wires ``ctx.store`` onto a Surreal-SHAPED fake (it
    has to, to drive the P6 pipeline at all), so a fake-level test alone would
    stay green even if the PRODUCTION composition still wired the legacy Qdrant
    handle into ``extension_ctx``. Only a live ``build_app_context`` run can catch
    that composition-level regression, mirroring
    ``TestSeam3ExtensionToolsAreWiredIntoTheLiveServer``'s live-server pattern.
    """

    @pytest_asyncio.fixture()
    async def qdrant(self) -> AsyncIterator[Any]:
        """A real Qdrant client with exact-name (concurrency-safe) teardown."""
        from conftest import QDRANT_URL, _qdrant_api_key
        from qdrant_client import AsyncQdrantClient

        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created: list[str] = []
        client._lore_created = created  # type: ignore[attr-defined]
        try:
            yield client
        finally:
            for name in created:
                for candidate in (name, f"{name}_memory"):
                    if await client.collection_exists(candidate):
                        await client.delete_collection(candidate)
            await client.close()

    @staticmethod
    def _slug() -> str:
        return f"test_{uuid.uuid4().hex}"

    async def _live_context(self, *, server: Any, qdrant: Any, tmp_path: Path) -> Any:
        """Build a live :class:`AppContext` over the server (real Qdrant/Surreal, fake embedder)."""
        import os

        from _surreal_harness import surreal_password, surreal_user
        from loremaster.server import build_app_context

        os.environ.setdefault("SURREAL_USER", surreal_user())
        os.environ.setdefault("SURREAL_PASS", surreal_password())
        slug = server.config.project.slug
        qdrant._lore_created.append(f"lore_{slug}")
        qdrant._lore_created.append(f"lore_{slug}_memory")
        return await build_app_context(
            server=server,
            embedder=FakeEmbedder(dim=_DIM),
            qdrant_client=qdrant,
            manifest_path=tmp_path / "m.db",
            snapshot_root=tmp_path / "snap",
            start_tasks=False,
        )

    @staticmethod
    async def _drop_surreal_db(slug: str) -> None:
        """Reap the per-test surreal database (named = the test's unique slug)."""
        from _surreal_harness import drop_database, make_env

        await drop_database(make_env(database=slug, dim=_DIM))

    async def test_runtime_ctx_store_is_the_unified_surreal_store(
        self, tmp_path: Path, qdrant: Any
    ) -> None:
        from loremaster.server import LoreServer
        from loremaster.store.qdrant import QdrantStore

        live = tmp_path / "live"
        live.mkdir()
        slug = self._slug()
        config = _server_config(slug, live)
        server = LoreServer(config)
        ctx = await self._live_context(server=server, qdrant=qdrant, tmp_path=tmp_path)
        try:
            runtime_ctx = ctx.extension_ctx
            assert runtime_ctx is not None, "startup hooks must have set the runtime ctx"
            # Duck-type: the unified store speaks hybrid_search (BM25 ⊕ HNSW via
            # RRF); the legacy QdrantStore has NO such method (search()/scroll()
            # only) — a lingering Qdrant handle fails this immediately.
            assert hasattr(runtime_ctx.store, "hybrid_search")
            assert hasattr(runtime_ctx.store, "scroll")
            assert not isinstance(runtime_ctx.store, QdrantStore)
            # It is the VERY object the search pipeline reads — not a same-shaped
            # sibling instance that happens to point at a different database.
            assert runtime_ctx.store is ctx.write_store
            # The P7 cutover removed AppContext's vestigial `store` attribute
            # entirely (pinned in test_memory_cutover.py); there is no longer a
            # legacy handle to compare against, so assert it stays gone.
            assert not hasattr(ctx, "store")
        finally:
            await ctx.aclose()
            await self._drop_surreal_db(server.config.project.slug)

    async def test_ctx_store_round_trips_the_same_chunk_the_write_path_wrote(
        self, tmp_path: Path, qdrant: Any
    ) -> None:
        # Behavioural proof (not just type/identity): a chunk written through
        # ``ctx.write_store`` is findable through the RUNTIME
        # ``ExtensionContext.store`` an extension hook receives, AND through the
        # live search pipeline — the fake-trio pipeline tests can't catch a wrong
        # production wiring (their ctx.store is always the same fake object the
        # pipeline reads), so this drives the REAL build_app_context composition.
        from _surreal_harness import chunk_record
        from loremaster.server import LoreServer

        live = tmp_path / "live"
        live.mkdir()
        slug = self._slug()
        config = _server_config(slug, live)
        server = LoreServer(config)
        ctx = await self._live_context(server=server, qdrant=qdrant, tmp_path=tmp_path)
        try:
            record = chunk_record(
                tier="custom",
                file_path="pkg/routing.py",
                identity="champion_routing_ctx_store_probe",
                ident_text="champion routing warehouse dispatch probe",
                slug=slug,
            )
            embed_result = await ctx.embedder.embed_documents([record.embedding_text])
            [doc_vector] = embed_result.vectors
            assert doc_vector is not None
            await ctx.write_store.upsert([(record, doc_vector)])

            runtime_ctx = ctx.extension_ctx
            assert runtime_ctx is not None

            # (a) the runtime ctx's store — what an extension hook receives —
            # finds the exact row the write path wrote.
            rows = await runtime_ctx.store.scroll(
                filters={"identity": "champion_routing_ctx_store_probe"}, limit=5
            )
            assert len(rows) == 1
            assert rows[0]["content_hash"] == record.payload["content_hash"]

            # (b) the LIVE search pipeline (built over the SAME write_store)
            # serves that identical chunk for a matching query — the pipeline
            # and the ctx.store an extension hook sees are ONE corpus, not two.
            results = await ctx.search_pipeline.search_code(record.embedding_text, k=5)
            assert any(r.chunk_key == record.point_id for r in results)
        finally:
            await ctx.aclose()
            await self._drop_surreal_db(server.config.project.slug)
