"""``LocalDirectorySourceProvider`` — acquire a static tier from a local directory.

The built-in :class:`~loremaster.extension.SourceProvider` for a static tier
sourced from a plain local directory (config ``source:``, plan AMENDMENT 1 /
D7). It makes that directory's files available in the snapshot layout so the
:class:`~loremaster.source.snapshot.SnapshotLayout` resolver finds them — with
NO podman/containers (the podman-image-extraction provider is the deferred odoo
extension's job).

**Materialisation choice: COPY the source tree into the tier's materialisation
dir** (``SnapshotLayout(snapshot_root).materialization_dir(tier)``), rather than
registering the source dir in place. A static tier is *frozen and
version-stamped* — a copy is a genuine point-in-time snapshot the server can
bind-mount ``:ro`` independent of the source's later mutation, and it lands the
files under the snapshot root the resolver searches. ``copytree`` is invoked
with ``symlinks=True`` so symlinks are PRESERVED, not followed: following them
(the default) content-bakes a symlink's *target* — e.g. a vendored package's
``evil -> /etc/passwd`` — into the snapshot as a regular file the read-time
resolver could never detect (CWE-59 / CWE-538). Preserving the link lets the
resolver reject any escaping symlink at read time, while internal-staying links
resolve normally. "Self-contained" therefore means "no link escapes the served
subtree" (enforced by the resolver), NOT "links replaced by copied content."

**A re-acquire REPLACES the tier's snapshot; it never merges into it.** The copy
lands in a staging dir created beside the materialisation dir (same filesystem,
so the swap is two renames, not a second copy); only a COMPLETE copy is swapped
in, and the previous tree is removed with the staging dir. So a file deleted from
the source disappears from the snapshot on the next acquire (the version-bump
rebuild walks exactly the current source), and a copy that fails part-way leaves
the previous snapshot untouched rather than a half-materialised one the server
would serve. Measured 2026-11-07: the earlier ``copytree(dirs_exist_ok=True)``
merge kept 112/91/48 files deleted from three corpus tiers' sources and
re-indexed them under the new version label.

Stated bounds: the two renames are not one atomic step, so a reader in the
instant between them sees the tier absent (a clean not-found), never a mixed
tree; if the second rename itself fails (e.g. a concurrent acquire of the same
tier re-created the dir), the error propagates and the previous tree is removed
with the staging dir, leaving the tier absent until the next acquire (the
indexer's FP-05 guard re-acquires an absent snapshot). A process killed
mid-acquire leaves its hidden ``.<tier>.acquire-*`` staging dir beside the tier;
nothing serves it (tiers resolve by name), but nothing reaps it either. A
materialisation dir that is itself a symlink is replaced by a real directory
(the link is removed, its target untouched) rather than written through.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from loremaster.source.snapshot import SnapshotLayout


class LocalDirectorySourceProvider:
    """Materialise a static tier's files from a local directory into the snapshot.

    Conforms to the :class:`~loremaster.extension.SourceProvider` Protocol
    (``tier`` attribute; ``acquire(tier, snapshot_root)``).

    Args:
        tier: The tier identity this provider acquires.
        source: The local directory whose file tree is materialised into the
            tier's snapshot subdir.
    """

    def __init__(self, tier: str, source: Path) -> None:
        self.tier = tier
        self._source = Path(source)

    def acquire(self, tier: str, snapshot_root: Path) -> None:
        """Replace ``tier``'s snapshot materialisation dir with a copy of :attr:`source`.

        Idempotent: after every successful acquire the materialisation dir holds
        exactly the source's current file set — files and directories deleted
        from the source are gone (the per-tier rebuild on a version bump). The
        copy is staged beside the materialisation dir and swapped in only once
        complete, so a failed copy raises and leaves the previous snapshot as it
        was.

        Args:
            tier: The tier being acquired (matches :attr:`tier`).
            snapshot_root: The snapshot root the tier's files are materialised
                under, for the live server to bind-mount ``:ro`` and serve.

        Raises:
            FileNotFoundError: If :attr:`source` does not exist — a misconfigured
                static tier fails LOUD here, naming the missing source, rather
                than silently producing an empty snapshot the server can't serve.
            OSError: If the copy fails (``shutil.Error`` for per-file failures);
                the previous snapshot is left in place.
        """
        if not self._source.exists():
            raise FileNotFoundError(
                f"source directory for tier {tier!r} does not exist: {self._source}"
            )
        destination = SnapshotLayout(snapshot_root).materialization_dir(tier)
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Stage beside the destination so the swap below is a same-filesystem
        # rename; everything left under ``staging`` (the copy on failure, the
        # previous tree on success) is removed with it.
        staging = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}.acquire-", dir=destination.parent)
        )
        staged = staging / "tree"
        # symlinks=True PRESERVES links rather than following them: a followed link
        # would content-bake its target (e.g. a vendored ``evil -> /etc/passwd``)
        # into the snapshot as a regular file the read-time resolver can't catch.
        # Preserved, an escaping link is rejected at read by the resolver's full
        # resolve()-against-base check; internal links still resolve. (CWE-59/538.)
        try:
            shutil.copytree(self._source, staged, symlinks=True)
            if destination.is_symlink() or destination.exists():
                destination.rename(staging / "previous")
            staged.rename(destination)
        finally:
            shutil.rmtree(staging)
