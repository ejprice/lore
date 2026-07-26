"""The batch-indexer CLI (plan AMENDMENT 1 / D6) — stdlib argparse, no new dep.

A standalone entrypoint that wires the *real* deployment resources and runs the
:class:`~loremaster.index.indexer.Indexer`. Designed to drop into CI/deploy later
(``python -m loremaster.index``), run manually now. It is intentionally thin: all
indexing logic lives in :class:`Indexer`; this module only does the real wiring
that the dependency-injected tests stub out:

* ``make_embedder(config.embedding)`` — the active loresigil embedder;
* the unified SurrealDB write stack (P5): a
  :class:`~loremaster.store.surreal.SurrealStore` +
  :class:`~loremaster.index.surreal_manifest.SurrealManifest` +
  :class:`~loremaster.graph_surreal.SurrealCodeGraph`, all on the project's
  namespace/database from :class:`~loremaster.config.SurrealConfig` — the SAME
  database the server reads, so a cold CLI index is immediately servable (the
  graph tools are non-empty after ``python -m loremaster.index``);
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

from loremaster.config import WATCH_STATIC, LoreConfig, load_config, resolve_secret
from loremaster.embedding import make_embedder_from_config
from loremaster.extension import SourceProvider
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.indexer import Indexer, IndexSummary, graph_roots
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.server import LoreServer
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loremaster.store.surreal import SurrealStore

# Default static-tier snapshot location (plan D8 / the staleness-engine ledger).
_DEFAULT_SNAPSHOT_ROOT = Path.home() / "docker" / "mcp" / "lore-snapshot"


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the batch indexer.

    Returns:
        The configured :class:`argparse.ArgumentParser`. ``--config`` is the path
        to ``lore.yaml``; ``--tier`` optionally restricts the run to one tier
        (routed to the explicit ``Indexer.index_tier`` escape hatch), defaulting
        to ``None`` (index every configured root).

    Note:
        The pre-P5 ``--manifest``/``--graph`` path flags are GONE: the manifest
        and code graph live in the project's SurrealDB database (the ``surreal:``
        section of ``lore.yaml``), not in local files, so there is no path to
        point at — the CLI and the server share state by sharing the database.
    """
    parser = argparse.ArgumentParser(
        prog="loremaster.index",
        description="Batch-build/refresh a project's lore SurrealDB index (per-tier freshness).",
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

    snapshot_root = (
        Path(args.snapshot_root) if args.snapshot_root else _DEFAULT_SNAPSHOT_ROOT
    )

    # The unified SurrealDB write stack: one namespace/database (the SAME one the
    # server reads — shared state by shared database, not shared files) holding
    # chunks + file_text + manifest + code graph, per SurrealConfig. Credentials
    # are resolved by env-var NAME (never inlined), failing loudly when unset.
    # The USERNAME is deliberately not carried as a secret (#211): it is a public
    # default named by SURREAL_DEFAULT_USER_ENV, so it is unwrapped here while
    # the password stays a SecretStr all the way to the SDK seam.
    surreal_user = resolve_secret(config.surreal.user_env).get_secret_value()
    surreal_password = resolve_secret(config.surreal.password_env)
    database = config.effective_surreal_database

    # Wire astroid resolution: the graph resolves each tier's files on disk under
    # these roots, classifying references in-project (kept, as FQNs) vs external
    # (dropped). Derived from the SAME effective roots the indexer walks.
    tier_roots, project_roots = graph_roots(config, snapshot_root)

    embedder = make_embedder_from_config(config.embedding)
    store = SurrealStore(
        url=config.surreal.url,
        namespace=config.surreal.namespace,
        database=database,
        dim=config.embedding.dim,
        user=surreal_user,
        password=surreal_password,
    )
    manifest = SurrealManifest(
        url=config.surreal.url,
        namespace=config.surreal.namespace,
        database=database,
        user=surreal_user,
        password=surreal_password,
    )
    code_graph = SurrealCodeGraph(
        url=config.surreal.url,
        namespace=config.surreal.namespace,
        database=database,
        user=surreal_user,
        password=surreal_password,
        tier_roots=tier_roots,
        project_roots=project_roots,
    )
    try:
        # Explicit readiness (schema application is atomic + per-statement
        # checked): each component applies its DDL slice before the sweep.
        await store.ensure_ready()
        await manifest.ensure_ready()
        await code_graph.ensure_ready()
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
            root = next((r for r in config.effective_roots if r.tier == args.tier), None)
            if root is None:
                known = ", ".join(sorted(r.tier for r in config.effective_roots)) or "(none configured)"
                raise SystemExit(f"unknown --tier {args.tier!r}; configured tiers: {known}")
            return await indexer.index_tier(root)
        return await indexer.index_all()
    finally:
        await store.close()
        await manifest.close()
        await code_graph.close()


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
