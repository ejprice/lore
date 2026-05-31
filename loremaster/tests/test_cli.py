"""Contract tests for the batch-indexer CLI (``loremaster.index.cli``).

The CLI is the cold-index entrypoint (``python -m loremaster.index``): it wires
the REAL deployment resources and runs the :class:`~loremaster.index.indexer.Indexer`
over a project's ``lore.yaml``. The deployed server builds a
:class:`~loremaster.graph.CodeGraph` and passes it to the indexer so the graph
tools (``what_imports`` / ``blast_radius`` / ``tests_for``) work; a cold index
through the CLI MUST do the same, at the SAME shared graph path the server reads
(``<manifest_dir>/<slug>.graph.db``) — otherwise the graph tools return empty on
a freshly-cold-indexed deployment.

These tests run the CLI's real wiring against a **REAL local Qdrant** (throwaway
``lore_test_<uuid>`` collection), a **REAL corpus** (a ``tmp_path`` tree where one
module imports a symbol from another), a temp-file manifest + graph, and a
**FakeEmbedder** substituted for the real TEI embedder (the embedder is loresigil's
tested concern — faking it keeps these fast, deterministic, and network-free).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
import yaml
from loremaster.graph import KIND_MODULE, CodeGraph
from loremaster.store.qdrant import QdrantStore
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

# Production embedding dimensionality the FakeEmbedder mimics.
_DIM = 2048

# A module that DEFINES a symbol other modules import.
_MODULE_A = """\
def compute_curve(week):
    \"\"\"Return the curve value for a week.\"\"\"
    return week * 2
"""

# A module that IMPORTS the defining module — the import edge under test.
_MODULE_B = """\
from pkg.a import compute_curve


def headline(week):
    \"\"\"Render the headline for a week.\"\"\"
    return compute_curve(week) + 1
"""


@pytest_asyncio.fixture()
async def store_factory() -> AsyncIterator[Any]:
    """Builder for a :class:`QdrantStore` with exact-name (concurrency-safe) teardown."""
    from conftest import QDRANT_URL, _qdrant_api_key

    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    created: list[str] = []

    def _make(slug: str) -> QdrantStore:
        store = QdrantStore(client=client, slug=slug)
        created.append(store.collection_name)
        return store

    try:
        yield _make
    finally:
        for name in created:
            if await client.collection_exists(name):
                await client.delete_collection(name)
        await client.close()


@pytest.fixture()
def fake_embedder_cli(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Substitute the CLI's real-TEI embedder factory with a :class:`FakeEmbedder`.

    The CLI calls ``make_embedder_from_config`` to construct the live TEI
    embedder; faking it at the ``cli`` module boundary keeps the test
    network-free while leaving every other piece of the CLI wiring (store,
    manifest, code-graph, providers, indexer) REAL. The CLI resolves the Qdrant
    API key via ``resolve_secret`` (an ``os.environ`` read), so the key — read
    from the same authoritative dotenv source the rest of the suite uses — is
    exported into the environment for the duration of the test.
    """
    from conftest import _QDRANT_KEY_NAME, _qdrant_api_key
    from loremaster.index import cli

    monkeypatch.setattr(
        cli, "make_embedder_from_config", lambda _config: FakeEmbedder(dim=_DIM)
    )
    monkeypatch.setenv(_QDRANT_KEY_NAME, _qdrant_api_key())
    yield


def _slug() -> str:
    return f"test_{uuid.uuid4().hex}"


def _write_lore_yaml(*, config_path: Path, slug: str, project_root: Path) -> None:
    """Write a minimal explicit-roots ``lore.yaml`` whose live root is the corpus."""
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": str(project_root)},
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
            {"tier": "custom", "watch": "live", "path": str(project_root), "include": ["**/*.py"]}
        ],
        "include": ["**/*.py"],
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
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def _build_import_corpus(project_root: Path) -> None:
    """Create ``pkg/a.py`` (defines a symbol) and ``pkg/b.py`` (imports it)."""
    pkg = project_root / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "a.py").write_text(_MODULE_A, encoding="utf-8")
    (pkg / "b.py").write_text(_MODULE_B, encoding="utf-8")


class TestCliBuildsCodeGraph:
    """A cold index through the CLI builds a populated code-graph (Bug B)."""

    async def test_cli_run_populates_graph_with_nodes_and_import_edges(
        self,
        tmp_path: Path,
        store_factory: Any,
        fake_embedder_cli: None,
    ) -> None:
        # Pre-create the throwaway collection under the session-scoped slug so the
        # store_factory teardown reaps it (the CLI opens its OWN client/store, but
        # ensure_collection is idempotent and the collection name is deterministic).
        slug = _slug()
        store_factory(slug)

        project_root = tmp_path / "tree"
        _build_import_corpus(project_root)
        config_path = tmp_path / "lore.yaml"
        _write_lore_yaml(config_path=config_path, slug=slug, project_root=project_root)
        manifest_path = tmp_path / "state" / f"{slug}.db"
        graph_path = tmp_path / "state" / f"{slug}.graph.db"

        # Call _run directly (the real CLI wiring) — main() owns its own
        # asyncio.run(), which cannot nest inside this async test's loop.
        from loremaster.config import load_config
        from loremaster.index.cli import _run, build_parser

        args = build_parser().parse_args(
            [
                "--config", str(config_path),
                "--manifest", str(manifest_path),
                "--graph", str(graph_path),
                "--snapshot-root", str(tmp_path / "snap"),
            ]
        )
        summary = await _run(load_config(args.config), args)
        assert summary.files_failed == 0
        assert summary.files_indexed > 0

        # The graph file at the explicit path exists and holds real nodes.
        assert graph_path.exists()
        graph = CodeGraph(str(graph_path))
        try:
            node_count = graph.connection.execute(
                "SELECT COUNT(*) AS c FROM nodes"
            ).fetchone()["c"]
            assert node_count > 0, "cold index built NO graph nodes"
            # The module nodes for both files are present.
            module_count = graph.connection.execute(
                "SELECT COUNT(*) AS c FROM nodes WHERE kind = ?", (KIND_MODULE,)
            ).fetchone()["c"]
            assert module_count >= 2
            # The import edge is reachable via the reverse lookup: pkg.b imports pkg.a.
            importers = {node.qualified_name for node in graph.what_imports("pkg.a")}
            assert "pkg.b" in importers
        finally:
            graph.close()

    async def test_cli_run_defaults_graph_path_alongside_manifest(
        self,
        tmp_path: Path,
        store_factory: Any,
        fake_embedder_cli: None,
    ) -> None:
        # With NO --graph, the CLI must build the graph at the SAME path the
        # server reads: <manifest_dir>/<slug>.graph.db. A mismatch means the
        # server serves an empty graph after a cold index.
        slug = _slug()
        store_factory(slug)

        project_root = tmp_path / "tree"
        _build_import_corpus(project_root)
        config_path = tmp_path / "lore.yaml"
        _write_lore_yaml(config_path=config_path, slug=slug, project_root=project_root)
        manifest_path = tmp_path / "state" / f"{slug}.db"

        from loremaster.config import load_config
        from loremaster.index.cli import _run, build_parser

        args = build_parser().parse_args(
            [
                "--config", str(config_path),
                "--manifest", str(manifest_path),
                "--snapshot-root", str(tmp_path / "snap"),
            ]
        )
        summary = await _run(load_config(args.config), args)
        assert summary.files_failed == 0
        assert summary.files_indexed > 0

        # The server-shared default path: alongside the manifest, <slug>.graph.db.
        expected_graph_path = manifest_path.parent / f"{slug}.graph.db"
        assert expected_graph_path.exists(), "default graph path not written"
        graph = CodeGraph(str(expected_graph_path))
        try:
            importers = {node.qualified_name for node in graph.what_imports("pkg.a")}
            assert "pkg.b" in importers
        finally:
            graph.close()
