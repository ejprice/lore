#!/usr/bin/env python3
"""Ensure a project's two lore Qdrant collections exist at the right dimension.

Creates ``lore_<slug>`` (code/docs) and ``lore_<slug>_memory`` (project memory),
both ``size=dim`` / cosine with the base payload indexes, if absent. This is the
``setup``/``start`` collection gate.

**The one thing it must never do is silently recreate a collection.** If an
existing collection's vector size disagrees with ``config.dim``, it STOPS with a
remediation message (exit 3) and changes nothing — auto-recreating would nuke a
real index. This enforces the plan's "STOP on dim mismatch — NEVER auto-recreate"
rule.

It reuses the in-repo, tested :class:`loremaster.store.qdrant.QdrantStore`
(``ensure_collection`` / ``collection_dim``) rather than re-implementing Qdrant
REST calls — so the collection's payload-index set stays identical to what the
indexer and server expect. It therefore requires the loremaster venv on
``sys.path`` (the dispatcher runs it with that interpreter).

Idempotent: re-running against already-correct collections is a no-op (the
underlying ``ensure_collection`` is idempotent on a real server).
"""

from __future__ import annotations

import argparse
import asyncio
import sys

# Exit codes shared with the dispatcher.
_EXIT_OK = 0
_EXIT_ERROR = 2
_EXIT_DIM_MISMATCH = 3

# The memory collection's suffix (matches loremaster's lore_<slug>_memory).
_MEMORY_SUFFIX = "_memory"


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the collection-ensure step."""
    parser = argparse.ArgumentParser(
        prog="ensure_collections",
        description="Ensure lore_<slug> + lore_<slug>_memory exist at the right dim "
        "(STOP on a dim mismatch; never auto-recreate).",
    )
    parser.add_argument("--config", required=True, help="Path to the project lore.yaml.")
    return parser


async def _ensure_one(client, slug: str, dim: int) -> None:  # type: ignore[no-untyped-def]
    """Ensure a single ``lore_<slug>`` collection; STOP on a dim mismatch.

    Reuses :class:`QdrantStore`: ``collection_dim`` reads the existing vector
    size (``None`` if the collection is absent), and ``ensure_collection``
    creates it + its payload indexes idempotently. A size disagreement raises
    :class:`SystemExit(_EXIT_DIM_MISMATCH)` BEFORE any mutation.
    """
    from loremaster.store.qdrant import QdrantStore

    store = QdrantStore(client=client, slug=slug)
    existing_dim = await store.collection_dim()
    if existing_dim is not None and existing_dim != dim:
        print(
            f"ensure_collections: collection {store.collection_name!r} exists with "
            f"vector size {existing_dim}, but config.dim is {dim}. DIM MISMATCH — "
            f"refusing to recreate (that would nuke the index). Remediate manually: "
            f"either fix config.dim/the embedder, or deliberately recreate + reindex.",
            file=sys.stderr,
        )
        raise SystemExit(_EXIT_DIM_MISMATCH)
    await store.ensure_collection(dim)


async def _run(config_path: str) -> int:
    """Wire the Qdrant client from the config and ensure both collections."""
    from loremaster.config import load_config, resolve_secret
    from qdrant_client import AsyncQdrantClient

    config = load_config(config_path)
    slug = config.project.slug
    dim = config.embedding.dim

    client = AsyncQdrantClient(
        url=config.qdrant.url, api_key=resolve_secret(config.qdrant.api_key_env)
    )
    try:
        await _ensure_one(client, slug, dim)
        await _ensure_one(client, f"{slug}{_MEMORY_SUFFIX}", dim)
    finally:
        await client.close()
    return _EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Ensure both collections; loud on failure, silent on success."""
    args = _build_parser().parse_args(argv)
    try:
        return asyncio.run(_run(args.config))
    except SystemExit as exit_signal:
        # Re-raise the typed dim-mismatch / explicit exit code unchanged.
        return int(exit_signal.code) if isinstance(exit_signal.code, int) else _EXIT_ERROR
    except KeyError as error:
        # resolve_secret raises KeyError on a missing/empty secret env var.
        print(f"ensure_collections: {error}", file=sys.stderr)
        return _EXIT_ERROR
    except Exception as error:  # noqa: BLE001 — top-level guard: report, exit loud
        print(f"ensure_collections: failed to ensure collections: {error}", file=sys.stderr)
        return _EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
