"""Contract tests for ``loremaster.server.LoreServer`` — the composition skeleton.

``LoreServer`` is the composition layer (plan AMENDMENT 1, D1/D2, §A1.9). It is
NOT the FastMCP server (that is the later ``server`` build): no serving, no auth
enforcement. Its job is to COMPOSE — load a :class:`LoreConfig`, register zero or
more :class:`Extension` objects, and expose the wired-up surface (a
:class:`ChunkerRegistry`, payload-index specs, source providers, detail
classification, format/chunk-key/search hooks, lifespan hooks) for the later
indexer/search/server layers to consume.

The load-bearing behaviours these tests pin:

* **Zero extensions ⇒ generic RAG.** A bare ``LoreServer`` dispatches the
  default lorescribe chunkers, uses the base default citation format, and fires
  NO extension hook. Proven against a REAL Python file (the default registry
  chunks it) and a REAL XML file (the base XmlChunker collapses it to one chunk —
  no profile having been wired).
* **Registering a fake extension wires every seam.** The fake chunker becomes
  dispatchable on a REAL Makefile; the fake XML profile reaches the constructed
  XmlChunker and forces ``<threshold>`` elements of a REAL XML file into their
  own chunks; payload-index / source-provider / tool specs are collected;
  classify_detail / format_result / chunk_key override the base defaults; the
  search hooks transform a candidate list; lifespan hooks are awaited.
* **config_model fail-loud.** A registered extension's ``config_model`` validates
  its ``extensions[name]`` slice; a bad slice raises at registration.
* **nit-1 register guard.** An extension chunker that claims a *default suffix*
  already owned by another registered chunker RAISES — closing the deferred
  lorescribe audit nit (a greedy default-suffix claim shadowing a suffix-owner)
  at the composition layer.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from _extension_helpers import (
    FAKE_KEY_VERSION,
    FakeExtension,
    FakeThresholdProfile,
    minimal_config,
)
from loremaster.server import LoreServer
from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext
from pydantic import ValidationError
from qdrant_client.models import ScoredPoint

# A real XML file on this host: a small file the base XmlChunker collapses to a
# single whole-file chunk, with ``<threshold>`` children a profile can force out.
_REAL_XML = Path("/etc/ImageMagick-7/thresholds.xml")

def _count_tokens(text: str) -> int:
    """A cheap per-string token estimate for the dispatch ChunkContext."""
    return max(1, len(text) // 4)

def _chunk_context(file_path: str) -> ChunkContext:
    """Build a :class:`ChunkContext` for driving a chunker over a real file."""
    return ChunkContext(
        slug="lore_ext_test",
        file_path=file_path,
        count_tokens=_count_tokens,
        max_input_tokens=8192,
    )

def _scored(point_id: str, score: float) -> ScoredPoint:
    """Build a :class:`ScoredPoint` candidate for the search-pipeline seams."""
    return ScoredPoint(id=point_id, version=0, score=score, payload={}, vector=None)

@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    """Write a valid tiered ``lore.yaml`` (with a ``fake`` extension slice) to disk."""

    config = minimal_config()
    path = tmp_path / "lore.yaml"
    path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    return path

class TestFromConfig:
    """``LoreServer.from_config`` loads the config and yields a bare server."""

    def test_loads_config_from_disk(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path)
        assert server.config.project.slug == "lore_ext_test"

    def test_a_bare_server_has_no_extensions(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path)
        assert server.extensions == []

class TestBareServerIsGenericRag:
    """Zero extensions ⇒ the generic code/docs RAG; no extension hook fires."""

    def test_default_python_chunker_dispatches(self, config_path: Path) -> None:
        # The bare server's registry must be the default lorescribe registry: a
        # REAL Python file routes to the python_ast chunker and yields real chunks.

        server = LoreServer.from_config(config_path)
        py_path = "/abs/sample.py"
        source = "import os\n\n\ndef alpha():\n    return os.getcwd()\n"
        chunks = server.registry.dispatch_file(py_path, source, _chunk_context(py_path))
        assert chunks, "default python chunker produced no chunks"
        # python_ast emits an imports chunk + a function chunk for ``alpha``.
        identities = {c.identity for c in chunks}
        assert "alpha" in identities

    def test_default_xml_chunker_has_no_profile(self, config_path: Path) -> None:
        # With no extension, the constructed XmlChunker has NO profiles, so a
        # small real XML file collapses to ONE whole-file ``xml_element`` chunk —
        # the threshold elements are NOT forced out (no profile wired).
        if not _REAL_XML.exists():
            pytest.skip(f"{_REAL_XML} not present on this host")

        server = LoreServer.from_config(config_path)
        source = _REAL_XML.read_text(encoding="ISO-8859-1")
        chunks = server.registry.dispatch_file(
            str(_REAL_XML), source, _chunk_context(str(_REAL_XML))
        )
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "xml_element"

    def test_bare_format_result_is_base_default(self, config_path: Path) -> None:
        # No extension overrides the format, so the resolved format hook returns
        # the base default (``None`` ⇒ "use base citation format"), not a custom
        # string. The server resolves "no extension claimed it" to ``None``.

        server = LoreServer.from_config(config_path)
        ctx = server.extension_context(store=object())
        assert server.format_result(_scored("a", 0.9), ctx) is None

    def test_bare_chunk_key_is_base_default(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path)
        ctx = server.extension_context(store=object())
        assert server.chunk_key({"file_path": "a.py"}, ctx) is None

    def test_bare_classify_detail_uses_base_default(self, config_path: Path) -> None:
        # C2: the base ships a default classification of ITS OWN chunk types —
        # signatures/imports/headings = summary; bodies = source. No extension
        # needed for these.

        server = LoreServer.from_config(config_path)
        assert server.classify_detail("imports") == "summary"
        assert server.classify_detail("method") == "source"

    def test_bare_search_hooks_are_identity(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path)
        ctx = server.extension_context(store=object())
        candidates = [_scored("a", 0.9), _scored("b", 0.5)]
        assert server.augment_candidates("q", candidates, ctx) == candidates
        assert server.rerank(candidates, ctx) == candidates

    def test_bare_has_no_extra_payload_indexes_or_providers(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path)
        assert server.payload_index_specs == []
        assert server.source_providers == []

class TestRegisterExtensionWiring:
    """``register_extension`` composes each seam into the server surface."""

    def test_register_returns_self_for_chaining(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path)
        returned = server.register_extension(FakeExtension())
        assert returned is server
        assert [e.name for e in server.extensions] == ["fake"]

    def test_seam1_fake_chunker_becomes_dispatchable_on_real_makefile(
        self, config_path: Path, tmp_path: Path
    ) -> None:
        # Seam 1 over a REAL file: a Makefile (basename-keyed, which the suffix
        # registry cannot route) becomes dispatchable once the extension chunker
        # is registered, and produces chunks driven by the real file content.

        makefile = tmp_path / "Makefile"
        makefile.write_text(
            "build: deps\n\tgcc -o app main.c\n\ntest: build\n\t./run-tests\n",
            encoding="utf-8",
        )
        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        source = makefile.read_text(encoding="utf-8")
        chunks = server.registry.dispatch_file(
            str(makefile), source, _chunk_context(str(makefile))
        )
        identities = {c.identity for c in chunks}
        assert {"build", "test"} <= identities
        assert all(c.chunk_type == "makefile" for c in chunks)

    def test_seam2_xml_profile_reaches_constructed_chunker(
        self, config_path: Path
    ) -> None:
        # Seam 2 over a REAL file: with the fake threshold profile registered, the
        # constructed XmlChunker forces each <threshold> into its own chunk, so a
        # file that collapses to ONE chunk bare now yields MANY profile-claimed
        # chunks. This proves the profile reached the chunker the server built.
        if not _REAL_XML.exists():
            pytest.skip(f"{_REAL_XML} not present on this host")

        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        source = _REAL_XML.read_text(encoding="ISO-8859-1")
        chunks = server.registry.dispatch_file(
            str(_REAL_XML), source, _chunk_context(str(_REAL_XML))
        )
        forced = [c for c in chunks if c.chunk_type == FakeThresholdProfile.CHUNK_TYPE]
        assert len(forced) >= 2, "profile did not force threshold elements into own chunks"
        assert all(c.metadata.get("claimed_by") == "fake" for c in forced)

    def test_seam3_tools_are_collected(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        specs = server.tool_specs(server.extension_context(store=object()))
        assert [s.name for s in specs] == ["fake_tool"]
        assert specs[0].handler("hi") == "echo:hi"

    def test_seam8_payload_indexes_are_collected(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        specs = server.payload_index_specs
        by_field = {s.field_name: s.schema_type for s in specs}
        assert by_field == {"model_name": "keyword", "is_installed": "bool"}

    def test_seam10_source_providers_are_collected(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        assert [p.tier for p in server.source_providers] == ["vendor"]

    def test_seam5_format_result_override(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        ctx = server.extension_context(store=object())
        # The registered extension's format wins over the base default.
        assert server.format_result(_scored("a", 0.9), ctx) == "FAKE: a"

    def test_seam6_chunk_key_override_carries_version(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        ctx = server.extension_context(store=object())
        key = server.chunk_key({"model_name": "sale.order"}, ctx)
        assert key == f"fake:sale.order:v{FAKE_KEY_VERSION}"

    def test_seam11_classify_detail_override(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        # Extension classification wins for its own types; base default still
        # applies for base chunk types the extension does not classify.
        assert server.classify_detail("fake_summary") == "summary"
        assert server.classify_detail("fake_body") == "source"
        assert server.classify_detail("imports") == "summary"  # base fallback

    def test_seam4_search_hooks_transform_candidates(self, config_path: Path) -> None:

        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        ctx = server.extension_context(store=object())
        base = [_scored("a", 0.5), _scored("b", 0.9)]
        augmented = server.augment_candidates("q", base, ctx)
        assert any(c.id == "injected" for c in augmented)
        reranked = server.rerank(augmented, ctx)
        scores = [c.score for c in reranked]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_seam9_lifespan_hooks_awaited(self, config_path: Path) -> None:
        # Fix B (§A1.10): the runner namespaces each extension's state under its
        # own name, so the fake's writes land in the ``fake`` namespace — reachable
        # via ``extension_state`` — rather than the top-level parent ``state``.
        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        ctx = server.extension_context(store=object())
        await server.run_startup_hooks(ctx)
        assert server.extension_state(ctx, "fake")["fake_started"] is True
        await server.run_shutdown_hooks(ctx)
        assert server.extension_state(ctx, "fake")["fake_stopped"] is True

class TestConfigModelValidation:
    """``register_extension`` validates the extension's ``extensions[name]`` slice."""

    def test_valid_slice_passes(self, tmp_path: Path) -> None:

        config = minimal_config(extensions={"fake": {"flavour": "chocolate"}})
        path = tmp_path / "lore.yaml"
        path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
        server = LoreServer.from_config(path).register_extension(FakeExtension())
        # The validated slice is accessible for the extension to consume.
        assert server.extension_config("fake").flavour == "chocolate"  # type: ignore[attr-defined]

    def test_bad_slice_fails_loud(self, tmp_path: Path) -> None:
        # The ``fake`` config model forbids extras; a typo'd key in the slice must
        # raise at registration, not be silently dropped.


        config = minimal_config(extensions={"fake": {"flavor": "misspelled"}})
        path = tmp_path / "lore.yaml"
        path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
        server = LoreServer.from_config(path)
        with pytest.raises(ValidationError):
            server.register_extension(FakeExtension())

    def test_missing_slice_for_extension_with_a_model_fails_loud(
        self, tmp_path: Path
    ) -> None:
        # An extension declaring a required-field config_model but with NO slice
        # present must fail loudly (a required ``flavour`` cannot be defaulted).


        config = minimal_config(extensions={})
        path = tmp_path / "lore.yaml"
        path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
        server = LoreServer.from_config(path)
        with pytest.raises(ValidationError):
            server.register_extension(FakeExtension())

class TestNit1RegisterGuard:
    """A chunker claiming a suffix already owned by another RAISES (audit nit-1)."""

    def test_overlapping_default_suffix_claim_raises(self, config_path: Path) -> None:
        # The deferred lorescribe nit: a greedy default-suffix registration that
        # OVERLAPS an existing suffix-owner is the strict failure case. The base
        # already owns ``.py`` (python_ast); an extension chunker that ALSO claims
        # ``.py`` as a default suffix must be rejected loudly at registration.

        class _PyShadowChunker(Chunker):
            """A chunker greedily claiming ``.py`` — overlaps the base owner."""

            # The server reads a chunker's default suffix claim from this attr.
            default_suffixes = (".py",)

            def handles(self, path: str) -> bool:
                return path.lower().endswith(".py")

            def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
                return [
                    Chunk(
                        chunk_type="shadow",
                        source_text=source,
                        identity="shadow",
                        line_start=1,
                        line_end=1,
                    )
                ]

        class _ShadowExtension(FakeExtension):
            def chunkers(self) -> list[Chunker]:
                return [_PyShadowChunker()]

        server = LoreServer.from_config(config_path)
        with pytest.raises(ValueError, match="(?i)suffix"):
            server.register_extension(_ShadowExtension())

    def test_non_overlapping_suffix_claim_is_allowed(
        self, config_path: Path, tmp_path: Path
    ) -> None:
        # The guard must NOT be over-eager: a chunker claiming a *fresh* suffix
        # (one no other chunker owns) registers cleanly and becomes dispatchable.

        class _CfgChunker(Chunker):
            default_suffixes = (".cfg",)

            def handles(self, path: str) -> bool:
                return path.lower().endswith(".cfg")

            def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
                return [
                    Chunk(
                        chunk_type="cfg",
                        source_text=source,
                        identity="cfg",
                        line_start=1,
                        line_end=1,
                    )
                ]

        class _CfgExtension(FakeExtension):
            def chunkers(self) -> list[Chunker]:
                return [_CfgChunker()]

        server = LoreServer.from_config(config_path).register_extension(_CfgExtension())
        cfg = tmp_path / "app.cfg"
        cfg.write_text("[main]\nkey=value\n", encoding="utf-8")
        chunks = server.registry.dispatch_file(
            str(cfg), cfg.read_text(encoding="utf-8"), _chunk_context(str(cfg))
        )
        assert chunks and chunks[0].chunk_type == "cfg"

    def test_filename_keyed_chunker_without_a_suffix_is_allowed(
        self, config_path: Path
    ) -> None:
        # The FakeMakefileChunker declares NO default suffix (it routes by
        # basename predicate), so it cannot collide with any suffix-owner and the
        # guard must let it register. This is the seam-1 case the guard protects
        # WITHOUT blocking.

        # FakeExtension's chunker is the basename-keyed Makefile chunker.
        server = LoreServer.from_config(config_path).register_extension(FakeExtension())
        assert [e.name for e in server.extensions] == ["fake"]

    def test_greedy_handles_without_declared_suffix_is_refused(self, config_path: Path) -> None:
        # The deeper half of nit-1 (audit-caught): a chunker can declare NO default
        # suffix yet have a greedy ``handles()`` that claims an owned suffix's files —
        # it would STILL shadow the suffix-owner via the registry's predicate tier.
        # The declared-overlap guard alone misses this; a register-time probe of each
        # owned suffix must catch it too.

        class _GreedyChunker(Chunker):
            # Declares no default suffix (so the declared-overlap guard won't fire)…
            def handles(self, path: str) -> bool:
                return path.lower().endswith(".py")  # …but greedily claims .py files.

            def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
                return [
                    Chunk(
                        chunk_type="greedy",
                        source_text=source,
                        identity="greedy",
                        line_start=1,
                        line_end=1,
                    )
                ]

        class _GreedyExtension(FakeExtension):
            def chunkers(self) -> list[Chunker]:
                return [_GreedyChunker()]

        server = LoreServer.from_config(config_path)
        with pytest.raises(ValueError, match="(?i)handles|predicate|shadow"):
            server.register_extension(_GreedyExtension())
