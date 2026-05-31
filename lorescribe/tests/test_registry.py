"""Contract tests for ``lorescribe.registry.ChunkerRegistry``.

The registry maps a file's extension to the chunker that handles it and
dispatches a source string to that chunker. The contract pinned here:

* Dispatch routes by extension to the registered chunker and returns ITS
  chunks (the registry is a thin router, not a re-chunker).

* **Unknown extension -> ``[]``** (NOT an exception). Ingestion walks whole
  directories; an unregistered file type must be skipped silently, not crash
  the run. A path with no extension at all is likewise ``[]``.

* A config override mapping can re-route an extension to a different chunker
  key, so a project can say "treat ``.txt`` as markdown" without code changes.

* Extension matching is **case-insensitive** (``.PY`` == ``.py``). This rule
  is pinned deliberately: filesystems differ on case sensitivity, and a
  chunker keyed on lowercase ``.py`` must still claim a ``README.PY`` file.
  The token counter injected into the context is exercised through the
  dispatch path to prove the seam carries the embedder's counter end-to-end.

* ``apply_overrides`` is **all-or-nothing**: a batch containing any unknown
  target key raises AND leaves the routing table exactly as it was — no entry
  from a failing batch is applied. A partial application would leave the
  registry in a half-configured state that nothing else detects.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker
from lorescribe.registry import ChunkerRegistry

from .conftest import (
    SAMPLE_FILE_PATH,
    SAMPLE_SLUG,
    VOYAGE4_MAX_INPUT_TOKENS,
    approx_token_count,
)

# Real on-disk corpus the predicate-dispatch tests route over (owner directive:
# real files, not mocks). The repo's own ``pyproject.toml`` is a real file whose
# BASENAME — not its ``.toml`` suffix — is what a filename-keyed chunker claims;
# this very test module is a real ``.py`` file the suffix map routes by extension.
REPO_PYPROJECT_PATH: str = str(Path(__file__).resolve().parents[2] / "pyproject.toml")
REAL_PYTHON_FILE_PATH: str = str(Path(__file__).resolve())

PYTHON_SOURCE: str = "def post_payroll() -> None:\n    ...\n"
MARKDOWN_SOURCE: str = "# Payroll\n\nDirect deposit posts on day two.\n"


class _MarkerChunker(Chunker):
    """A chunker that stamps which key handled the file, for routing assertions.

    It also invokes the injected token counter so dispatch-path tests can prove
    the ``ChunkContext.count_tokens`` seam is traversed during dispatch.
    """

    def __init__(self, chunk_type: str, claimed_suffix: str) -> None:
        self._chunk_type = chunk_type
        self._claimed_suffix = claimed_suffix

    def handles(self, path: str) -> bool:
        return path.lower().endswith(self._claimed_suffix)

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        return [
            Chunk(
                chunk_type=self._chunk_type,
                source_text=source,
                identity=f"{self._chunk_type}:root",
                line_start=1,
                line_end=source.count("\n") + 1,
                metadata={"token_count": ctx.count_tokens(source)},
            )
        ]


class TestChunkerRegistryDispatch:
    """Routing, the unknown-extension contract, overrides, and case rules."""

    def setup_method(self) -> None:
        self.python_chunker = _MarkerChunker(chunk_type="python_symbol", claimed_suffix=".py")
        self.markdown_chunker = _MarkerChunker(chunk_type="markdown_section", claimed_suffix=".md")
        self.registry = ChunkerRegistry()
        self.registry.register("python", self.python_chunker, extensions=[".py"])
        self.registry.register("markdown", self.markdown_chunker, extensions=[".md"])
        self.ctx = ChunkContext(
            slug=SAMPLE_SLUG,
            file_path=SAMPLE_FILE_PATH,
            count_tokens=approx_token_count,
            max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
        )

    def test_known_extension_routes_to_matching_chunker(self) -> None:
        # Act
        chunks = self.registry.dispatch_file("src/payroll.py", PYTHON_SOURCE, self.ctx)
        # Assert: the PYTHON chunker handled it, not the markdown one.
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "python_symbol"

    def test_distinct_extension_routes_to_other_chunker(self) -> None:
        # Act
        chunks = self.registry.dispatch_file("docs/payroll.md", MARKDOWN_SOURCE, self.ctx)
        # Assert
        assert chunks[0].chunk_type == "markdown_section"

    def test_unknown_extension_returns_empty_list(self) -> None:
        # Act: ``.rst`` is registered to nothing.
        chunks = self.registry.dispatch_file("docs/payroll.rst", "anything", self.ctx)
        # Assert: empty list, NOT an exception — ingestion skips it silently.
        assert chunks == []

    def test_unknown_extension_does_not_raise(self) -> None:
        # Act / Assert: explicit "no exception" guard for the skip contract.
        try:
            result = self.registry.dispatch_file("data/archive.tar.gz", "binary", self.ctx)
        except Exception as exc:  # noqa: BLE001 - the whole point is to forbid raising
            pytest.fail(f"dispatch_file must not raise on unknown extension, raised {exc!r}")
        assert result == []

    def test_path_with_no_extension_returns_empty_list(self) -> None:
        # Act: a dotfile-free, suffix-free path (e.g. a LICENSE or Makefile).
        chunks = self.registry.dispatch_file("repo/LICENSE", "MIT License", self.ctx)
        # Assert
        assert chunks == []

    def test_extension_match_is_case_insensitive(self) -> None:
        # Pinned rule: ``.PY`` resolves to the same chunker as ``.py``. A
        # case-sensitive impl that only matches lowercase fails here.
        chunks = self.registry.dispatch_file("legacy/PAYROLL.PY", PYTHON_SOURCE, self.ctx)
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "python_symbol"

    def test_uppercase_extension_routes_identically_to_lowercase(self) -> None:
        lower = self.registry.dispatch_file("a.md", MARKDOWN_SOURCE, self.ctx)
        upper = self.registry.dispatch_file("A.MD", MARKDOWN_SOURCE, self.ctx)
        # Both must reach the markdown chunker.
        assert lower[0].chunk_type == upper[0].chunk_type == "markdown_section"

    def test_dispatch_traverses_the_injected_token_counter(self) -> None:
        # Act
        chunks = self.registry.dispatch_file("src/payroll.py", PYTHON_SOURCE, self.ctx)
        # Assert: the count attached during dispatch equals the injected
        # counter's own output — proves ctx (and its counter) flowed through
        # the registry into the chunker. Independent expected value.
        assert chunks[0].metadata["token_count"] == approx_token_count(PYTHON_SOURCE)


class TestChunkerRegistryConfigOverride:
    """A config override remaps an extension to a different registered chunker."""

    def setup_method(self) -> None:
        self.python_chunker = _MarkerChunker(chunk_type="python_symbol", claimed_suffix=".py")
        self.markdown_chunker = _MarkerChunker(chunk_type="markdown_section", claimed_suffix=".md")
        self.registry = ChunkerRegistry()
        self.registry.register("python", self.python_chunker, extensions=[".py"])
        self.registry.register("markdown", self.markdown_chunker, extensions=[".md"])
        self.ctx = ChunkContext(
            slug=SAMPLE_SLUG,
            file_path=SAMPLE_FILE_PATH,
            count_tokens=approx_token_count,
            max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
        )

    def test_override_reroutes_extension_to_another_chunker(self) -> None:
        # Arrange: project config says "treat .txt as markdown".
        self.registry.apply_overrides({".txt": "markdown"})
        # Act
        chunks = self.registry.dispatch_file("notes/scratch.txt", MARKDOWN_SOURCE, self.ctx)
        # Assert: the markdown chunker now claims .txt.
        assert chunks[0].chunk_type == "markdown_section"

    def test_override_can_steal_a_default_extension(self) -> None:
        # Arrange: re-route the default .py extension to the markdown chunker.
        self.registry.apply_overrides({".py": "markdown"})
        # Act
        chunks = self.registry.dispatch_file("src/payroll.py", PYTHON_SOURCE, self.ctx)
        # Assert: override wins over the default registration.
        assert chunks[0].chunk_type == "markdown_section"

    def test_override_targeting_unknown_key_is_rejected(self) -> None:
        # Arrange / Act / Assert: pointing an extension at a chunker key that
        # was never registered is a configuration error, surfaced eagerly so a
        # typo in project config fails loudly rather than silently dropping files.
        with pytest.raises((KeyError, ValueError)):
            self.registry.apply_overrides({".txt": "no_such_chunker"})

    def test_unrelated_extensions_unaffected_by_override(self) -> None:
        # Arrange
        self.registry.apply_overrides({".txt": "markdown"})
        # Act: .py is untouched by a .txt override.
        chunks = self.registry.dispatch_file("src/payroll.py", PYTHON_SOURCE, self.ctx)
        # Assert
        assert chunks[0].chunk_type == "python_symbol"

    def test_failed_override_batch_applies_none_of_its_entries(self) -> None:
        # Arrange: a single batch where the FIRST entry is valid (".txt" ->
        # "markdown", a registered key) and a LATER entry targets an
        # unregistered key. Ordering matters: with a per-entry implementation
        # the good ".txt" mapping is written to the routing table *before* the
        # bad entry raises, so this ordering is what exposes partial
        # application. Real configs ship many extension overrides at once; one
        # typo must not leave half of them silently in effect.
        batch: dict[str, str] = {
            ".txt": "markdown",          # valid: registered key, applied first
            ".bad": "no_such_chunker",   # invalid: never registered, raises
        }
        # Act / Assert: the batch must raise on the unknown key.
        with pytest.raises((KeyError, ValueError)):
            self.registry.apply_overrides(batch)
        # Assert: ALL-OR-NOTHING. The good ".txt" entry from the failed batch
        # must NOT have been applied, so ".txt" still routes by its original
        # state — unregistered -> ``[]``. A partial-apply impl leaves ".txt"
        # pointing at the markdown chunker and returns a markdown chunk here,
        # failing this assertion. Independent of the impl: the expectation is
        # the registry's *pre-batch* routing, not anything the override wrote.
        post_raise_chunks = self.registry.dispatch_file(
            "notes/scratch.txt", MARKDOWN_SOURCE, self.ctx
        )
        assert post_raise_chunks == []


class _BasenameChunker(Chunker):
    """A chunker that claims a file by BASENAME, not by extension.

    Models the real motivating case (``Dockerfile``, ``Makefile``,
    ``pyproject.toml``): a chunker whose responsibility is keyed on the file's
    *name*, which the suffix map cannot express. ``handles`` returns ``True`` for
    any path whose basename matches the claimed name, regardless of extension.
    """

    def __init__(self, chunk_type: str, claimed_basename: str) -> None:
        self._chunk_type = chunk_type
        self._claimed_basename = claimed_basename

    def handles(self, path: str) -> bool:
        from pathlib import PurePosixPath

        return PurePosixPath(path).name == self._claimed_basename

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        return [
            Chunk(
                chunk_type=self._chunk_type,
                source_text=source,
                identity=f"{self._chunk_type}:root",
                line_start=1,
                line_end=source.count("\n") + 1,
                metadata={"token_count": ctx.count_tokens(source)},
            )
        ]


class TestChunkerRegistryPredicateDispatch:
    """Dispatch consults a chunker's ``handles`` predicate, not just the suffix.

    The verified gap this pins: ``dispatch_file`` routed purely on the path's
    extension and never consulted ``Chunker.handles(path)``, so a chunker that
    claims a file by BASENAME (``pyproject.toml``, ``Dockerfile``, ``Makefile``)
    could never be reached. The new contract adds a predicate-consulting tier
    with an EXPLICIT precedence:

      1. a config override for the suffix wins (strongest, user-configured signal),
      2. else a registered chunker whose ``handles(path)`` claims the file wins,
      3. else the default suffix→chunker map,
      4. else ``[]`` (unknown — still never raises).

    Real corpus (owner directive): the repo's real ``pyproject.toml`` is routed
    by basename; a real ``.py`` file is routed by the real ``PythonAstChunker``
    via the suffix map; an unknown extension still yields ``[]``.
    """

    def setup_method(self) -> None:
        self.python_chunker = PythonAstChunker()
        self.pyproject_chunker = _BasenameChunker(
            chunk_type="pyproject_manifest", claimed_basename="pyproject.toml"
        )
        self.registry = ChunkerRegistry()
        # The python chunker is bound to its ``.py`` suffix the normal way.
        self.registry.register("python_ast", self.python_chunker, extensions=[".py"])
        # The pyproject chunker claims NO suffix — it can only be reached via its
        # ``handles`` predicate (basename match). ``.toml`` is deliberately left
        # unmapped so a suffix-only router would return ``[]`` for it.
        self.registry.register("pyproject", self.pyproject_chunker, extensions=[])
        self.ctx = ChunkContext(
            slug=SAMPLE_SLUG,
            file_path=SAMPLE_FILE_PATH,
            count_tokens=approx_token_count,
            max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
        )

    def test_basename_predicate_routes_real_pyproject_toml(self) -> None:
        # Arrange: the real repo pyproject.toml on disk — a ``.toml`` file the
        # suffix map does NOT know, reachable only via ``handles`` basename match.
        source = Path(REPO_PYPROJECT_PATH).read_text(encoding="utf-8")
        # Act
        chunks = self.registry.dispatch_file(REPO_PYPROJECT_PATH, source, self.ctx)
        # Assert: the predicate-matching chunker claimed it — a suffix-only
        # router (the verified bug) returns ``[]`` here and fails.
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "pyproject_manifest"

    def test_real_python_file_still_routes_by_suffix_map(self) -> None:
        # The suffix map must still work: a real ``.py`` file (this test module)
        # routes to the real PythonAstChunker, which emits python chunk types.
        source = Path(REAL_PYTHON_FILE_PATH).read_text(encoding="utf-8")
        chunks = self.registry.dispatch_file(REAL_PYTHON_FILE_PATH, source, self.ctx)
        assert len(chunks) >= 1
        # The PythonAstChunker stamps imports/class/method/function types — never
        # the basename chunker's ``pyproject_manifest``.
        assert all(chunk.chunk_type != "pyproject_manifest" for chunk in chunks)
        produced_types = {chunk.chunk_type for chunk in chunks}
        assert produced_types & {"imports", "class", "method", "function"}

    def test_unknown_extension_with_no_predicate_match_still_empty(self) -> None:
        # A ``.toml`` file whose basename is NOT ``pyproject.toml`` matches no
        # predicate and no suffix mapping -> ``[]`` (the unknown contract holds).
        chunks = self.registry.dispatch_file("config/other.toml", "x = 1\n", self.ctx)
        assert chunks == []

    def test_unknown_extension_does_not_raise_with_predicate_tier(self) -> None:
        # The skip-silently contract survives the new predicate tier.
        try:
            result = self.registry.dispatch_file("data/archive.tar.gz", "bin", self.ctx)
        except Exception as exc:  # noqa: BLE001 - the point is to forbid raising
            pytest.fail(f"dispatch_file must not raise on unknown file, raised {exc!r}")
        assert result == []

    def test_config_override_outranks_predicate_match(self) -> None:
        # Precedence tier 1 beats tier 2: re-route ``pyproject.toml``'s natural
        # ``.toml`` suffix to the python chunker via config. Even though the
        # pyproject chunker's ``handles`` still claims the basename, the explicit
        # override must win — otherwise user config could never overrule a
        # greedy predicate.
        self.registry.apply_overrides({".toml": "python_ast"})
        # Real Python that DOES chunk (a bare ``x = 1`` yields no AST chunk — using it
        # was the original vacuity: an empty result trivially satisfies the old assert).
        source = "def champion_route(week):\n    return week + 1\n"
        chunks = self.registry.dispatch_file(REPO_PYPROJECT_PATH, source, self.ctx)
        # Tightened (non-vacuous): assert the override POSITIVELY produced the python
        # chunker's output — non-empty and exactly what PythonAstChunker yields directly —
        # not merely the absence of pyproject_manifest, which an empty result satisfies.
        assert chunks, "override must route to the python chunker, not yield []"
        assert chunks == self.python_chunker.chunk(source, self.ctx)
        assert all(chunk.chunk_type != "pyproject_manifest" for chunk in chunks)

    def test_predicate_outranks_default_suffix_map(self) -> None:
        # Precedence tier 2 beats tier 3. Register a basename chunker that claims
        # a file ALSO covered by a suffix mapping, with no override in play; the
        # predicate match must win over the plain default suffix registration.
        special_md = _BasenameChunker(
            chunk_type="special_readme", claimed_basename="README.md"
        )
        markdown = _MarkerChunker(chunk_type="markdown_section", claimed_suffix=".md")
        registry = ChunkerRegistry()
        registry.register("markdown", markdown, extensions=[".md"])
        registry.register("special_readme", special_md, extensions=[])
        # A generic ``.md`` file (basename != README.md) falls through to the
        # suffix map -> markdown.
        generic = registry.dispatch_file("docs/guide.md", MARKDOWN_SOURCE, self.ctx)
        assert generic[0].chunk_type == "markdown_section"
        # But README.md is claimed by the basename predicate, outranking the
        # ``.md`` suffix mapping.
        readme = registry.dispatch_file("docs/README.md", MARKDOWN_SOURCE, self.ctx)
        assert readme[0].chunk_type == "special_readme"
