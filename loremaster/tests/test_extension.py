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

from pathlib import Path
from typing import Any, Literal

import pytest
from _extension_helpers import FakeExtension, minimal_config
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
