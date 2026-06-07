"""The batch-indexer CLI (plan AMENDMENT 1 / D6) — stdlib argparse, no new dep.

A standalone entrypoint that wires the *real* deployment resources and runs the
:class:`~loremaster.index.indexer.Indexer`. Designed to drop into CI/deploy later
(``python -m loremaster.index``), run manually now. It is intentionally thin: all
indexing logic lives in :class:`Indexer`; this module only does the real wiring
that the dependency-injected tests stub out:

* ``make_embedder(config.embedding)`` — the active loresigil embedder;
* a real :class:`~loremaster.store.qdrant.QdrantStore` over an
  :class:`~qdrant_client.AsyncQdrantClient` (collection ``lore_<slug>``), with
  every extension-declared payload index applied;
* the SQLite :class:`~loremaster.index.manifest.Manifest`;
* :meth:`~loremaster.server.LoreServer.from_config` for the composed chunker
  registry + the extensions' source providers, PLUS the built-in
  :class:`~loremaster.source.local_directory.LocalDirectorySourceProvider` per
  static root (the generic default — a static tier sourced from a local dir).

Unix-philosophy output: silent on success, the run summary to stdout, loud
(non-zero exit) only on failure.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from qdrant_client import AsyncQdrantClient

from loremaster.config import WATCH_STATIC, LoreConfig, load_config, resolve_secret
from loremaster.embedding import make_embedder_from_config
from loremaster.extension import SourceProvider
from loremaster.graph import CodeGraph
from loremaster.index.indexer import Indexer, IndexSummary, graph_roots
from loremaster.index.manifest import Manifest
from loremaster.server import LoreServer
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loremaster.store.qdrant import QdrantStore

# Default manifest + snapshot locations (plan D8 / the staleness-engine ledger).
_DEFAULT_MANIFEST_DIR = Path.home() / ".local" / "state" / "lore"
_DEFAULT_SNAPSHOT_ROOT = Path.home() / "docker" / "mcp" / "lore-snapshot"


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the batch indexer.

    Returns:
        The configured :class:`argparse.ArgumentParser`. ``--config`` is the path
        to ``lore.yaml``; ``--tier`` optionally restricts the run to one tier
        (the explicit ``reindex(tier=…)`` escape hatch), defaulting to ``None``
        (index every configured root).
    """
    parser = argparse.ArgumentParser(
        prog="loremaster.index",
        description="Batch-build/refresh a project's lore Qdrant index (per-tier freshness).",
    )
    parser.add_argument(
        "--config", required=True, help="Path to the project lore.yaml configuration."
    )
    parser.add_argument(
        "--tier",
        default=None,
        help="Restrict the run to one tier (default: index every configured root).",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to the SQLite manifest (default: ~/.local/state/lore/<slug>.db).",
    )
    parser.add_argument(
        "--graph",
        default=None,
        help=(
            "Path to the SQLite code-graph the server reads "
            "(default: alongside the manifest, ~/.local/state/lore/<slug>.graph.kuzu)."
        ),
    )
    parser.add_argument(
        "--snapshot-root",
        default=None,
        help="Static-tier snapshot root (default: ~/docker/mcp/lore-snapshot).",
    )
    return parser


def _source_providers(server: LoreServer, config: LoreConfig) -> list[SourceProvider]:
    """Compose the extensions' providers + a built-in provider per static root.

    The generic default for a ``static`` root is a
    :class:`LocalDirectorySourceProvider` over its configured ``source`` — unless
    an extension already contributed a provider for that tier (e.g. the deferred
    odoo podman-image extractor), in which case the extension's provider wins.
    """
    providers: list[SourceProvider] = list(server.source_providers)
    covered = {provider.tier for provider in providers}
    for root in config.roots:
        if root.watch == WATCH_STATIC and root.tier not in covered and root.source:
            providers.append(LocalDirectorySourceProvider(root.tier, Path(root.source)))
    return providers


async def _run(config: LoreConfig, args: argparse.Namespace) -> IndexSummary:
    """Wire the real resources, run the indexer, and return its summary."""
    server = LoreServer(config)

    manifest_path = (
        Path(args.manifest)
        if args.manifest
        else _DEFAULT_MANIFEST_DIR / f"{config.project.slug}.db"
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = Manifest(str(manifest_path))

    # The code-graph lives at the SAME shared path the server reads — alongside
    # the manifest as ``<slug>.graph.kuzu`` (both are bind-mounted into the
    # container). Building it here is what makes the graph tools (what_imports /
    # blast_radius / tests_for) non-empty after a cold ``python -m loremaster.index``.
    graph_path = (
        Path(args.graph)
        if args.graph
        else manifest_path.parent / f"{config.project.slug}.graph.kuzu"
    )
    graph_path.parent.mkdir(parents=True, exist_ok=True)

    snapshot_root = (
        Path(args.snapshot_root) if args.snapshot_root else _DEFAULT_SNAPSHOT_ROOT
    )

    # Wire astroid resolution: the graph resolves each tier's files on disk under
    # these roots, classifying references in-project (kept, as FQNs) vs external
    # (dropped). Derived from the SAME effective roots the indexer walks.
    tier_roots, project_roots = graph_roots(config, snapshot_root)
    code_graph = CodeGraph(
        str(graph_path), tier_roots=tier_roots, project_roots=project_roots
    )

    embedder = make_embedder_from_config(config.embedding)
    client = AsyncQdrantClient(
        url=config.qdrant.url, api_key=resolve_secret(config.qdrant.api_key_env)
    )
    try:
        store = QdrantStore(
            client=client,
            slug=config.project.slug,
            extra_keyword_indexes=[
                spec.field_name
                for spec in server.payload_index_specs
                if spec.schema_type == "keyword"
            ],
            extra_bool_indexes=[
                spec.field_name
                for spec in server.payload_index_specs
                if spec.schema_type == "bool"
            ],
        )
        await store.ensure_collection(config.embedding.dim)
        indexer = Indexer(
            store=store,
            embedder=embedder,
            manifest=manifest,
            registry=server.registry,
            source_providers=_source_providers(server, config),
            config=config,
            snapshot_root=snapshot_root,
            code_graph=code_graph,
        )
        if args.tier is not None:
            root = next((r for r in config.roots if r.tier == args.tier), None)
            if root is None:
                known = ", ".join(sorted(r.tier for r in config.roots)) or "(none configured)"
                raise SystemExit(f"unknown --tier {args.tier!r}; configured tiers: {known}")
            return await indexer.index_tier(root)
        return await indexer.index_all()
    finally:
        await client.close()
        manifest.close()
        code_graph.close()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint: parse args, run the indexer, report the summary.

    Args:
        argv: Optional explicit argument vector (for tests); defaults to
            ``sys.argv[1:]``.

    Returns:
        Process exit code: ``0`` when no file failed, ``1`` when at least one
        file is in the ``failed`` state (loud failure, Unix philosophy).
    """
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    summary = asyncio.run(_run(config, args))
    # Summary to stdout (a deploy step captures it); non-zero exit on any failure.
    print(
        f"indexed={summary.files_indexed} failed={summary.files_failed} "
        f"skipped={summary.files_skipped} rebuilt={summary.tiers_rebuilt} "
        f"tier_skipped={summary.tiers_skipped}"
    )
    return 1 if summary.files_failed else 0
