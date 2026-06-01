"""Shared test doubles for the extension-framework contract tests.

These are mocks for the EXTENSION side (sanctioned by the owner directive:
"fake extension … mocks fine for the EXTENSION"). Where a seam *actually
chunks*, the doubles drive the REAL lorescribe chunkers over a REAL file — only
the extension wrapper is fake.

Contents:

* :func:`minimal_config` — a valid :class:`~loremaster.config.LoreConfig` with an
  ``extensions: {"fake": {...}}`` slice the :class:`FakeExtension` validates.
* :class:`FakeMakefileChunker` — a real :class:`~lorescribe.base.Chunker` keyed on
  the *basename* ``Makefile`` (a filename-keyed chunker, the seam-1 use case), so
  registering it makes a Makefile dispatchable where the bare registry would not
  claim it.
* :class:`FakeThresholdProfile` / :class:`FakeJsProfile` — profiles claiming a
  generic element/block with ``force_own_chunk`` so they demonstrably reach the
  constructed XML/JS chunkers.
* :class:`FakeSourceProvider` — a conforming :class:`SourceProvider`.
* :class:`FakeConfigModel` — the pydantic model seam 7 validates the ``fake``
  config slice with (rejects a bad slice — fail-loud).
* :class:`FakeExtension` — overrides every one of the eleven seams.
"""

from __future__ import annotations

import xml.etree.ElementTree as ElementTree
from pathlib import Path
from typing import Any, Literal

from loremaster.config import LoreConfig
from loremaster.extension import (
    Extension,
    ExtensionContext,
    PayloadIndexSpec,
    ToolSpec,
)
from lorescribe.base import Chunker
from lorescribe.javascript import JsBlock
from lorescribe.models import Chunk, ChunkContext, ProfileResult
from pydantic import BaseModel, ConfigDict
from qdrant_client.models import ScoredPoint

# The version the fake's semantic memory-key carries (seam 6 — carries a
# key_version). A distinct, recognisable number so a test can pin it.
FAKE_KEY_VERSION = 7

# The basename the FakeMakefileChunker claims by predicate (seam-1 filename use
# case the suffix-only registry cannot express).
MAKEFILE_BASENAME = "Makefile"


def minimal_config(extensions: dict[str, dict[str, Any]] | None = None) -> LoreConfig:
    """Build a valid :class:`LoreConfig` carrying a ``fake`` extension slice.

    Args:
        extensions: Override the ``extensions`` block. Defaults to a valid
            ``fake`` slice (``{"fake": {"flavour": "vanilla"}}``).

    Returns:
        A validated config suitable for an :class:`ExtensionContext`.
    """
    if extensions is None:
        extensions = {"fake": {"flavour": "vanilla"}}
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": "lore_ext_test", "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": 8,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "include": ["**/*.py"],
        "exclude_dirs": [".git"],
        "exclude_globs": ["uv.lock"],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
        "extensions": extensions,
    }
    return LoreConfig.model_validate(payload)


class FakeMakefileChunker(Chunker):
    """A real, filename-keyed chunker: claims a ``Makefile`` basename (seam 1).

    The bare lorescribe registry routes by suffix and cannot express a
    basename-keyed chunker. This double is a genuine :class:`Chunker` (it
    implements both ABC methods and returns real :class:`Chunk` objects), so
    registering it via the extension makes a ``Makefile`` *dispatchable* through
    the predicate tier — the exact thing seam 1 exists to enable.
    """

    chunk_type = "makefile"

    def handles(self, path: str) -> bool:
        """Claim a path whose basename is exactly ``Makefile``."""
        return path.rsplit("/", 1)[-1] == MAKEFILE_BASENAME

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Emit one chunk per non-blank ``target:`` rule in the Makefile.

        A make rule (``target: deps``) starts at column 0 and contains a colon.
        Each becomes a chunk identified by the target name, so the output is
        driven by the REAL file content, not a hardcoded stub.
        """
        chunks: list[Chunk] = []
        for lineno, line in enumerate(source.splitlines(), start=1):
            if line and not line[0].isspace() and ":" in line and not line.startswith("#"):
                target = line.split(":", 1)[0].strip()
                if target:
                    chunks.append(
                        Chunk(
                            chunk_type=self.chunk_type,
                            source_text=line,
                            identity=target,
                            line_start=lineno,
                            line_end=lineno,
                        )
                    )
        return chunks


class FakeThresholdProfile:
    """An XML ``SchemaProfile`` claiming ``<threshold>`` with ``force_own_chunk``.

    Demonstrates seam 2 reaching the constructed :class:`XmlChunker`: a small XML
    file (e.g. ``thresholds.xml``) collapses to a single whole-file chunk under
    the size tier, but a profile that claims its ``<threshold>`` children with
    ``force_own_chunk=True`` forces each into its own chunk — visible proof the
    profile was wired in.
    """

    THRESHOLD_TAG = "threshold"
    CHUNK_TYPE = "fake_threshold"

    def __call__(
        self, element: ElementTree.Element, ctx: ChunkContext
    ) -> ProfileResult | None:
        """Claim a ``<threshold>`` element; decline everything else."""
        if element.tag.rsplit("}", 1)[-1] == self.THRESHOLD_TAG:
            return ProfileResult(
                chunk_type=self.CHUNK_TYPE,
                extra_metadata={"claimed_by": "fake"},
                force_own_chunk=True,
            )
        return None


class FakeJsProfile:
    """A ``JsProfile`` claiming a generic ``function`` block (seam 2, JS side)."""

    CHUNK_TYPE = "fake_js_widget"

    def __call__(self, block: JsBlock, ctx: ChunkContext) -> ProfileResult | None:
        """Claim a generic ``function`` block; decline everything else."""
        if block.kind == "function":
            return ProfileResult(
                chunk_type=self.CHUNK_TYPE, extra_metadata={"claimed_by": "fake"}
            )
        return None


class FakeSourceProvider:
    """A conforming :class:`SourceProvider` for a ``vendor`` tier (seam 10)."""

    tier = "vendor"

    def acquire(self, tier: str, snapshot_root: Path) -> None:
        """Materialise a marker file into the snapshot layout."""
        (snapshot_root / f"{tier}.acquired").write_text("ok", encoding="utf-8")


class FakeConfigModel(BaseModel):
    """The pydantic model seam 7 validates the ``fake`` config slice with.

    ``extra="forbid"`` so a typo'd key in the ``extensions.fake`` block fails
    loudly — the fail-loud behaviour the contract requires.
    """

    model_config = ConfigDict(extra="forbid")

    flavour: str


class FakeExtension(Extension):
    """An :class:`Extension` overriding every one of the eleven seams.

    Each override is trivial but *observably distinct* from the inert default, so
    a test can prove the seam was wired (chunker dispatchable, profile reached,
    candidates reshaped, format/key/classification overridden, lifespan awaited).
    """

    key_version = FAKE_KEY_VERSION

    @property
    def name(self) -> str:
        return "fake"

    # seam 1
    def chunkers(self) -> list[Chunker]:
        return [FakeMakefileChunker()]

    # seam 2
    def xml_profiles(self) -> list[Any]:
        return [FakeThresholdProfile()]

    def js_profiles(self) -> list[Any]:
        return [FakeJsProfile()]

    # seam 3
    def tools(self, ctx: ExtensionContext) -> list[ToolSpec]:
        def _fake_tool(q: str) -> str:
            return f"echo:{q}"

        return [
            ToolSpec(
                name="fake_tool",
                handler=_fake_tool,
                description="A fake index-backed tool.",
                input_schema={"q": "str"},
                output_schema={"echo": "str"},
            )
        ]

    # seam 4 (C3) — inject a candidate, then reorder by score descending
    def augment_candidates(
        self, query: str, candidates: list[ScoredPoint], ctx: ExtensionContext
    ) -> list[ScoredPoint]:
        injected = ScoredPoint(
            id="injected", version=0, score=1.0, payload={"injected": True}, vector=None
        )
        return [injected, *candidates]

    def rerank(
        self, candidates: list[ScoredPoint], ctx: ExtensionContext
    ) -> list[ScoredPoint]:
        return sorted(candidates, key=lambda c: c.score, reverse=True)

    # seam 5
    def format_result(self, result: ScoredPoint, ctx: ExtensionContext) -> str | None:
        return f"FAKE: {result.id}"

    # seam 6 — versioned semantic memory-key
    def chunk_key(self, payload: dict[str, Any], ctx: ExtensionContext) -> str | None:
        model = payload.get("model_name", "?")
        return f"fake:{model}:v{self.key_version}"

    # seam 7
    def config_model(self) -> type[BaseModel] | None:
        return FakeConfigModel

    # seam 8
    def payload_indexes(self) -> list[PayloadIndexSpec]:
        return [
            PayloadIndexSpec(field_name="model_name", schema_type="keyword"),
            PayloadIndexSpec(field_name="is_installed", schema_type="bool"),
        ]

    # seam 9
    async def on_startup(self, ctx: ExtensionContext) -> None:
        ctx.state["fake_started"] = True

    async def on_shutdown(self, ctx: ExtensionContext) -> None:
        ctx.state["fake_stopped"] = True

    # seam 10
    def source_providers(self) -> list[Any]:
        return [FakeSourceProvider()]

    # seam 11 (C2)
    def classify_detail(self, chunk_type: str) -> Literal["summary", "source"] | None:
        if chunk_type == "fake_summary":
            return "summary"
        if chunk_type == "fake_body":
            return "source"
        return None


# The name an extension tool deliberately collides with — one of the ten
# built-ins (the search tool). Registering a tool under this name must RAISE so an
# extension can never silently shadow a built-in on the live MCP surface (seam-3
# wiring guard).
BUILTIN_COLLISION_NAME = "search_code"


class CounterExtension(Extension):
    """A single-seam :class:`Extension` contributing ONE tool that uses the ctx (seam 3).

    Mirrors the seam-3 wiring deliverable's requirement that the registered MCP
    tool's handler closes over the RUNTIME :class:`ExtensionContext` (real
    embedder/store/manifest built in ``build_app_context``) and can reach its own
    per-extension lifespan ``state`` namespace via
    :meth:`~loremaster.server.LoreServer.extension_state`. The tool increments a
    counter the ``on_startup`` hook seeded into that namespace, so a call that
    returns the bumped value proves the handler ran against the live ctx — not a
    composition placeholder. The declared ``count`` input is the amount to add, so
    the registered tool's input schema must expose it.
    """

    # The per-extension ``state`` key the counter lives under (seeded at startup,
    # bumped by every tool call) — proof the runtime ctx + state namespace flow in.
    STATE_KEY = "counter_total"

    @property
    def name(self) -> str:
        return "counter"

    def on_startup_seed(self) -> int:
        """The value ``on_startup`` seeds the counter at (a recognisable non-zero)."""
        return 100

    async def on_startup(self, ctx: ExtensionContext) -> None:
        """Seed the per-extension state namespace the tool handler will bump."""
        ctx.state[self.STATE_KEY] = self.on_startup_seed()

    def tools(self, ctx: ExtensionContext) -> list[ToolSpec]:
        """Contribute one counter tool whose handler closes over the runtime ``ctx``.

        The handler reads/writes ``ctx.state`` — which, at runtime, is the
        extension's private lifespan-state namespace — so a call's return value
        reflects state the ``on_startup`` hook seeded: end-to-end proof the live
        context (not a placeholder) reached the handler.
        """

        def _bump(count: int = 1) -> int:
            current: int = ctx.state.get(self.STATE_KEY, 0)
            total = current + count
            ctx.state[self.STATE_KEY] = total
            return total

        return [
            ToolSpec(
                name="bump_counter",
                handler=_bump,
                description="Increment the extension's counter by ``count`` and return the total.",
                input_schema={"count": "int"},
                output_schema={"total": "int"},
            )
        ]


class CollidingExtension(Extension):
    """An :class:`Extension` whose tool name shadows a built-in — must be refused.

    The seam-3 wiring guard: an extension tool that re-uses one of the ten
    built-in names (here :data:`BUILTIN_COLLISION_NAME`) must raise a clear error
    at registration rather than silently shadowing — or being shadowed by — the
    built-in on the live MCP surface.
    """

    @property
    def name(self) -> str:
        return "collider"

    def tools(self, ctx: ExtensionContext) -> list[ToolSpec]:
        def _shadow() -> str:
            return "shadow"

        return [
            ToolSpec(
                name=BUILTIN_COLLISION_NAME,
                handler=_shadow,
                description="A tool that collides with a built-in name.",
                input_schema={},
                output_schema={"x": "str"},
            )
        ]
