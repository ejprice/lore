"""Contract tests for the batch-indexer CLI (``loremaster.index.cli``).

The CLI is the cold-index entrypoint (``python -m loremaster.index``): it wires
the REAL deployment resources and runs the :class:`~loremaster.index.indexer.Indexer`
over a project's ``lore.yaml``. Since P5 the deployment resources are the unified
SurrealDB write stack — store + manifest + code graph in ONE namespace/database
(:class:`~loremaster.config.SurrealConfig`) — the SAME database the server reads.
A cold index through the CLI MUST land the code graph in that shared database
(``what_imports`` / ``blast_radius`` / ``tests_for`` non-empty afterwards);
pre-P5 this contract was "same graph FILE path as the server" — it is now
"same DATABASE as the server", with the database name derived from the project
slug when ``surreal.database`` is unset.

These tests run the CLI's real wiring against the REAL SurrealDB dev server
(throwaway per-test database under the ``lore_test`` namespace), a **REAL
corpus** (a ``tmp_path`` tree where one module imports a symbol from another),
and a **FakeEmbedder** substituted for the real TEI embedder (the embedder is
loresigil's tested concern — faking it keeps these fast, deterministic, and
network-free).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from _surreal_harness import (
    drop_database as drop_surreal_database,
)
from _surreal_harness import (
    make_env,
    surreal_password,
    surreal_url,
    surreal_user,
    unique_database,
)
from loremaster.graph_surreal import SurrealCodeGraph
from loresigil.testing import FakeEmbedder

# Production embedding dimensionality the FakeEmbedder mimics.
_DIM = 2048

# The namespace every throwaway CLI-test database lives under (the harness's
# own isolation convention).
_TEST_NAMESPACE = "lore_test"

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

# The env-var names the default SurrealConfig references credentials by.
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"


@pytest.fixture()
def fake_embedder_cli(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Substitute the CLI's real-TEI embedder factory with a :class:`FakeEmbedder`.

    The CLI calls ``make_embedder_from_config`` to construct the live TEI
    embedder; faking it at the ``cli`` module boundary keeps the test
    network-free while leaving every other piece of the CLI wiring (store,
    manifest, code-graph, providers, indexer) REAL. The CLI resolves the
    SurrealDB credentials via ``resolve_secret`` (an ``os.environ`` read), so
    the dev server's root credentials — the same ones the harness resolves —
    are exported for the duration of the test.
    """
    from loremaster.index import cli

    monkeypatch.setattr(
        cli, "make_embedder_from_config", lambda _config: FakeEmbedder(dim=_DIM)
    )
    monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password())
    yield


def _slug() -> str:
    return f"test_{uuid.uuid4().hex}"


def _write_lore_yaml(
    *,
    config_path: Path,
    slug: str,
    project_root: Path,
    surreal_database: str | None,
) -> None:
    """Write a minimal explicit-roots ``lore.yaml`` whose live root is the corpus.

    Args:
        surreal_database: An explicit throwaway database name, or ``None`` to
            omit the field and exercise the slug-derived default — the
            "same database the server reads" contract.
    """
    surreal_block: dict[str, Any] = {
        "url": surreal_url(),
        "namespace": _TEST_NAMESPACE,
        "user_env": _SURREAL_USER_ENV,
        "password_env": _SURREAL_PASS_ENV,
    }
    if surreal_database is not None:
        surreal_block["database"] = surreal_database
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
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
        "surreal": surreal_block,
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


async def _assert_graph_populated(database: str, project_root: Path) -> None:
    """The shared-database contract: the CLI's cold index left a queryable graph.

    Opens an INDEPENDENT :class:`SurrealCodeGraph` on the same database (as the
    server would) and asserts the resolved in-project import edge is reachable:
    ``pkg.b``'s ``from pkg.a import compute_curve`` resolves to the symbol FQN
    ``pkg.a.compute_curve``.
    """
    graph = SurrealCodeGraph(
        url=surreal_url(),
        namespace=_TEST_NAMESPACE,
        database=database,
        user=surreal_user(),
        password=surreal_password(),
        tier_roots={"custom": project_root},
        project_roots=[project_root],
    )
    try:
        importers = {node.qualified_name for node in await graph.what_imports("pkg.a.compute_curve")}
        assert "pkg.b" in importers
        assert await graph.indexed_file_count() >= 2
    finally:
        await graph.close()


class TestCliBuildsCodeGraph:
    """A cold index through the CLI builds a populated code-graph (Bug B) in the
    project's SurrealDB database."""

    async def test_cli_run_populates_graph_with_nodes_and_import_edges(
        self,
        tmp_path: Path,
        fake_embedder_cli: None,
    ) -> None:
        slug = _slug()
        database = unique_database()

        project_root = tmp_path / "tree"
        _build_import_corpus(project_root)
        config_path = tmp_path / "lore.yaml"
        _write_lore_yaml(
            config_path=config_path, slug=slug, project_root=project_root,
            surreal_database=database,
        )

        # Call _run directly (the real CLI wiring) — main() owns its own
        # asyncio.run(), which cannot nest inside this async test's loop.
        from loremaster.config import load_config
        from loremaster.index.cli import _run, build_parser

        args = build_parser().parse_args(
            [
                "--config", str(config_path),
                "--snapshot-root", str(tmp_path / "snap"),
            ]
        )
        try:
            summary = await _run(load_config(args.config), args)
            assert summary.files_failed == 0
            assert summary.files_indexed > 0
            await _assert_graph_populated(database, project_root)
        finally:
            await drop_surreal_database(make_env(database=database, dim=_DIM))

    async def test_cli_run_defaults_database_to_project_slug(
        self,
        tmp_path: Path,
        fake_embedder_cli: None,
    ) -> None:
        # With NO surreal.database configured, the CLI must land everything in
        # the slug-derived database — the SAME name the server derives, so a
        # cold CLI index is immediately servable. (Pre-P5 this contract was the
        # shared graph FILE path; the database name is its successor.)
        slug = _slug()  # unique ⇒ the derived database name is also unique

        project_root = tmp_path / "tree"
        _build_import_corpus(project_root)
        config_path = tmp_path / "lore.yaml"
        _write_lore_yaml(
            config_path=config_path, slug=slug, project_root=project_root,
            surreal_database=None,
        )

        from loremaster.config import load_config
        from loremaster.index.cli import _run, build_parser

        config = load_config(config_path)
        assert config.effective_surreal_database == slug  # the derivation itself

        args = build_parser().parse_args(
            [
                "--config", str(config_path),
                "--snapshot-root", str(tmp_path / "snap"),
            ]
        )
        try:
            summary = await _run(config, args)
            assert summary.files_failed == 0
            assert summary.files_indexed > 0
            await _assert_graph_populated(slug, project_root)
        finally:
            await drop_surreal_database(make_env(database=slug, dim=_DIM))
