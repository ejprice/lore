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
"""

from __future__ import annotations

import shutil
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
        """Copy :attr:`source`'s tree into ``tier``'s snapshot materialisation dir.

        Idempotent: re-acquiring overwrites the tier's snapshot subtree with the
        current source contents (the per-tier rebuild on a version bump).

        Args:
            tier: The tier being acquired (matches :attr:`tier`).
            snapshot_root: The snapshot root the tier's files are materialised
                under, for the live server to bind-mount ``:ro`` and serve.

        Raises:
            FileNotFoundError: If :attr:`source` does not exist — a misconfigured
                static tier fails LOUD here, naming the missing source, rather
                than silently producing an empty snapshot the server can't serve.
        """
        if not self._source.exists():
            raise FileNotFoundError(
                f"source directory for tier {tier!r} does not exist: {self._source}"
            )
        destination = SnapshotLayout(snapshot_root).materialization_dir(tier)
        # symlinks=True PRESERVES links rather than following them: a followed link
        # would content-bake its target (e.g. a vendored ``evil -> /etc/passwd``)
        # into the snapshot as a regular file the read-time resolver can't catch.
        # Preserved, an escaping link is rejected at read by the resolver's full
        # resolve()-against-base check; internal links still resolve. (CWE-59/538.)
        shutil.copytree(self._source, destination, dirs_exist_ok=True, symlinks=True)
