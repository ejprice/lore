"""Contract tests for ``loremaster.extension`` — the composition surface.

This module pins the *extension API surface* the loremaster base exposes (plan
AMENDMENT 1, §A1.3 — the eleven seams, refined by §A1.10 C2/C3):

* :class:`ExtensionContext` — the shared-services bundle (store, embedder,
  config, ``count_tokens``, manifest) handed to every context-taking seam. It is
  *mutable* so a lifespan hook (seam 9) can stash state on it.
* :class:`Extension` — an ABC base class (NOT a bare Protocol) with a ``name``
  and the eleven seams, **each with a safe no-op/empty default**, so a subclass
  overrides only what it needs and a *bare* server is the generic RAG.
* :class:`ToolSpec` / :class:`PayloadIndexSpec` — the small declarative models
  seams 3 and 8 hand back.
* :class:`SourceProvider` — the indexer-side Protocol (signature only).

The load-bearing invariant the whole framework rests on: **the defaults are
genuinely inert.** A bare :class:`Extension` subclass that overrides nothing must
return ``[]`` / ``None`` / identity for every seam, so that registering zero
extensions yields the generic code/docs RAG. These tests assert that directly,
seam by seam, against a do-nothing subclass — and separately assert that a
:class:`FakeExtension` overriding *every* seam round-trips its overrides.
"""

from __future__ import annotations

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
from loremaster.extension import (
    Extension,
    ExtensionContext,
    PayloadIndexSpec,
    SourceProvider,
    ToolSpec,
)
from loremaster.index.manifest import Manifest
from loresigil.testing import FakeEmbedder
from pydantic import ValidationError
from qdrant_client.models import ScoredPoint


class TestExtensionContext:
    """The shared-services bundle handed to context-taking seams."""

    def test_bundles_the_shared_services_and_is_typed(self, tmp_path: Path) -> None:
        embedder = FakeEmbedder(dim=8)
        config = minimal_config()
        manifest = Manifest(str(tmp_path / "m.db"))
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
        manifest.close()

    def test_is_mutable_so_a_lifespan_hook_can_stash_state(self, tmp_path: Path) -> None:
        # Seam 9 (§A1.3.9): ``on_startup`` "may stash state on the mutable
        # ExtensionContext". A frozen model would make that impossible.

        embedder = FakeEmbedder(dim=8)
        manifest = Manifest(str(tmp_path / "m.db"))
        ctx = ExtensionContext(
            store=object(),
            embedder=embedder,
            config=minimal_config(),
            count_tokens=embedder.count_tokens,
            manifest=manifest,
        )
        ctx.state["session"] = "stashed-by-startup"  # noqa: F821 - attribute under test
        assert ctx.state["session"] == "stashed-by-startup"
        manifest.close()

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

class TestPayloadIndexSpec:
    """The declarative extra-index spec seam 8 hands back."""

    def test_models_a_keyword_field(self) -> None:

        spec = PayloadIndexSpec(field_name="model_name", schema_type="keyword")
        assert spec.field_name == "model_name"
        assert spec.schema_type == "keyword"

    def test_models_a_bool_field(self) -> None:

        spec = PayloadIndexSpec(field_name="is_installed", schema_type="bool")
        assert spec.schema_type == "bool"

    def test_rejects_an_unknown_schema_kind(self) -> None:
        # Qdrant indexes are KEYWORD/BOOL here; an unknown kind is a config bug
        # that must fail loudly rather than silently skip the index. The
        # ``type: ignore`` is deliberate — mypy correctly flags the bad literal at
        # type-check time; this asserts the *runtime* validation also rejects it.
        with pytest.raises(ValidationError):
            PayloadIndexSpec(field_name="x", schema_type="geo")  # type: ignore[arg-type]

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
def ext_context(tmp_path: Path) -> Any:
    """An :class:`ExtensionContext` over fakes for the context-taking seams."""

    embedder = FakeEmbedder(dim=8)
    manifest = Manifest(str(tmp_path / "ctx.db"))
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
        candidates = [_scored("a", 0.9), _scored("b", 0.5)]
        # Identity: same objects, same order — the base must not reshape the set.
        result = bare_extension.augment_candidates("query", candidates, ext_context)
        assert result == candidates
        assert [c.id for c in result] == ["a", "b"]

    def test_seam4_rerank_default_identity(self, bare_extension: Any, ext_context: Any) -> None:
        candidates = [_scored("a", 0.9), _scored("b", 0.5)]
        assert bare_extension.rerank(candidates, ext_context) == candidates

    def test_seam5_format_result_default_none(self, bare_extension: Any, ext_context: Any) -> None:
        # ``None`` ⇒ the base supplies its default citation/format.
        assert bare_extension.format_result(_scored("a", 0.9), ext_context) is None

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
        # ``None`` ⇒ base default classification (C2).
        assert bare_extension.classify_detail("class") is None

def _scored(point_id: str, score: float, payload: dict[str, Any] | None = None) -> ScoredPoint:
    """Build a :class:`ScoredPoint` candidate for the search-pipeline seams."""
    return ScoredPoint(
        id=point_id, version=0, score=score, payload=payload or {}, vector=None
    )

class TestFakeExtensionRoundTrips:
    """A :class:`FakeExtension` overriding every seam returns its overrides.

    This is the mirror of the inert-defaults suite: it proves the seams are real
    override points (not, say, ``@final`` or swallowed), so :class:`LoreServer`
    has something to wire.
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
        # seam 4 — candidate augmentation injects, rerank reorders
        base = [_scored("a", 0.5), _scored("b", 0.9)]
        augmented = ext.augment_candidates("q", base, ext_context)
        assert any(c.id == "injected" for c in augmented)
        reranked = ext.rerank(augmented, ext_context)
        assert [c.score for c in reranked] == sorted(
            (c.score for c in reranked), reverse=True
        )
        # seam 5
        assert ext.format_result(_scored("a", 0.5), ext_context) == "FAKE: a"
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
# Seam 3 LIVE-SERVER wiring: an extension's ToolSpec reaches the MCP surface.
# --------------------------------------------------------------------------- #
# The bug this suite pins: ``LoreServer.tool_specs(ctx)`` collects an extension's
# seam-3 tools as value objects (the composition tests above prove that), but the
# FastMCP server build never registered them — ``_register_tools`` hardcoded only
# the ten built-ins and ignored the server's extension tools. So an extension's
# tools reached the live MCP surface NOWHERE. These tests drive the REAL
# ``build_mcp_server`` + a live ``build_app_context`` (the same path
# ``test_mcp_server.py`` uses) and assert an extension tool (a) APPEARS in
# ``tools/list`` alongside the ten built-ins, (b) exposes its declared input
# schema, and (c) is INVOCABLE end-to-end through the FastMCP tool dispatch with
# the handler closing over the RUNTIME ExtensionContext — not merely callable as a
# bare ``spec.handler()`` (the vacuous version the composition tests already pass).

_DIM = 2048

# The ten built-in tools (the seam-3 wiring must be purely ADDITIVE to these).
_BUILTIN_TOOLS = {
    "search_code",
    "read_file",
    "get_symbol",
    "save_memory",
    "recall_memory",
    "reindex",
    "index_status",
    "what_imports",
    "blast_radius",
    "tests_for",
}


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
        """Build a live :class:`AppContext` over the server (real Qdrant, fake embedder)."""
        from loremaster.server import build_app_context

        slug = server.config.project.slug
        qdrant._lore_created.append(f"lore_{slug}")
        qdrant._lore_created.append(f"lore_{slug}_memory")
        return await build_app_context(
            server=server,
            embedder=FakeEmbedder(dim=_DIM),
            qdrant_client=qdrant,
            manifest_path=tmp_path / "m.db",
            graph_path=tmp_path / "graph.db",
            snapshot_root=tmp_path / "snap",
            start_tasks=False,
        )

    async def test_extension_tool_appears_in_tools_list_with_the_ten_builtins(
        self, tmp_path: Path
    ) -> None:
        # RED today: the extension's ``bump_counter`` tool is collected by
        # ``server.tool_specs`` but NEVER registered, so it is absent from the live
        # ``tools/list``. The ten built-ins are present either way.
        from loremaster.server import LoreServer, build_mcp_server

        slug = self._slug()
        config = _server_config(slug, tmp_path / "live")
        server = LoreServer(config).register_extension(CounterExtension())
        mcp = build_mcp_server(server)

        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        # Purely additive: the ten built-ins are untouched.
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
