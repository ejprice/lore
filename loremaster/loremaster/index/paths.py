"""Shared path-scope predicates for the indexer, reconcile, and watcher.

The same two questions — "is this tier-relative path in scope for indexing?" and
"which directories under a root survive the exclude-dir prune?" — are asked by
:mod:`loremaster.index.indexer` (the walk), :mod:`loremaster.index.reconcile`
(the deletion diff), and :mod:`loremaster.index.watcher` (event filtering +
observer scheduling). Keeping the logic in ONE place is the lesson the plan calls
out (the drift that produced 15+ copies of one routine): a watcher whose scope
disagreed with the walk's scope would either index files the walk purges, or fail
to watch files the walk indexes. These helpers make "watch scope == walk scope ==
reconcile scope" true by construction.

* :func:`is_included` — the include/exclude glob test, applied to a single
  tier-relative POSIX path.
* :func:`walked_dirs` — the directories under a root that survive the
  ``exclude_dirs`` prune (the watcher's scheduling-level prune; the same prune
  ``os.walk`` callers apply in place).
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from loremaster.config import LoreConfig, RootConfig


def is_included(config: LoreConfig, root: RootConfig, rel_path: str) -> bool:
    """Decide whether a tier-relative path is in scope for indexing.

    A path is included iff it matches at least one of the root's ``include``
    globs (an empty include list means "include everything under the root") AND
    matches none of the root's ``exclude`` globs nor the project-level
    ``exclude_globs``. ``PurePosixPath.full_match`` honours ``**`` across
    segments (so ``**/*.py`` matches both ``a.py`` and ``src/a.py``).

    Args:
        config: The project config (supplies ``exclude_globs``).
        root: The root whose per-root ``include``/``exclude`` globs apply.
        rel_path: The tier-relative POSIX path to test.

    Returns:
        ``True`` if the path is in scope, ``False`` otherwise.
    """
    path = PurePosixPath(rel_path)
    for pattern in (*root.exclude, *config.exclude_globs):
        if path.full_match(pattern):
            return False
    if not root.include:
        return True
    return any(path.full_match(pattern) for pattern in root.include)


def walked_dirs(config: LoreConfig, base: Path) -> Iterator[str]:
    """Yield every directory under ``base`` that survives the ``exclude_dirs`` prune.

    Walks ``base`` with ``config.exclude_dirs`` pruned IN PLACE at the
    ``os.walk`` level — so a ``.git``/``.venv``/worktree-copy subtree is never
    descended. This is both the watcher's scheduling-level prune (each yielded
    dir becomes a non-recursive watch) and the same traversal the index/reconcile
    walks perform.

    Args:
        config: The project config (supplies ``exclude_dirs``).
        base: The root directory to walk.

    Yields:
        Each surviving directory path (as a string), starting with ``base``.
    """
    exclude_dir_names = set(config.exclude_dirs)
    for dirpath, dirnames, _filenames in os.walk(base):
        dirnames[:] = [name for name in dirnames if name not in exclude_dir_names]
        yield dirpath
