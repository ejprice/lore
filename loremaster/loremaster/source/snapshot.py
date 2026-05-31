"""Single source of truth for tier↔location (C5) + the C4 safe path resolver.

The always-on loremaster server never carries the static tiers
(community/enterprise/pip/stdlib) on its own disk. A batch indexer materialises
each tier into a host snapshot dir (``~/docker/mcp/lore-snapshot/<tier>/…``,
plan AMENDMENT 1 / D8); the server bind-mounts that dir ``:ro`` at ``/source``
and locates files within it through this module — the ONE place that knows
where a tier's files live.

``SnapshotLayout`` is that single source of truth, in BOTH directions:

* **Forward (C5):** :meth:`SnapshotLayout.tier_locations` maps a tier to an
  ORDERED LIST of physical directories under the snapshot root. The mapping is
  many-to-one in reality — ``pip`` resolves to ``pip-packages`` *then*
  ``apt-packages`` (the apt+pip→``pip`` merge odoo-code expresses across
  ``discovery.py``/``read_file.py``). :meth:`SnapshotLayout.materialization_dir`
  is the first/canonical location, i.e. where a provider *writes* a tier.
* **Reverse (C5):** :meth:`SnapshotLayout.resolve` tries the tier's locations IN
  ORDER and returns the first that *contains* the file (as a safe absolute
  path), or ``None`` if none does. ``None`` is the clean not-found / rejected
  sentinel — there is no exception-as-control-flow for the miss case.

The reverse lookup applies the **C4 two-tier containment check**, mirroring
odoo-code's ``read_file.py:144-159``, so the file-serving boundary is safe even
though one tier base (the live custom root) is itself a directory symlink:

1. **Input sanitisation** — an absolute ``rel_path`` or any ``..`` path
   component is rejected outright (belt-and-suspenders with step 2).
2. **normpath-contain the base** — the joined candidate must normalise to a path
   inside the tier base's *normalised* path. The base is normalised, NOT
   ``resolve()``-d, so a tier base that is itself a symlinked directory (the
   live-root case) is ALLOWED — its literal location is still inside the served
   subtree.
3. **resolve()-check the FULL candidate** — the candidate's fully ``resolve()``-d
   real target (following EVERY link in the chain — intermediate directory
   symlinks included) must stay within the *resolved base*; otherwise REJECTED.
   This catches an escape via a symlinked intermediate dir (a plain file behind
   ``evil -> /etc``) that a final-component-only check missed, as well as a final
   file symlink, while still permitting the legitimately-symlinked base of step 2
   (anchoring on ``base.resolve()`` — its real target — not the snapshot root).
"""

from __future__ import annotations

import os
from pathlib import Path

# The canonical, frozen tier→ordered-subdirs map: the SINGLE source of truth for
# where a tier's files live, keyed on subdir names RELATIVE to the snapshot root
# so the map is portable across deployments. ``pip`` is the many-to-one case
# (apt+pip→pip): pip files are preferred in ``pip-packages`` and fall back to
# ``apt-packages`` (mirrors odoo-code read_file.py:116-117). A tier absent from
# this map falls back to a single subdir named after the tier itself, so a
# generic (non-odoo) project's arbitrary tier name works without registration.
TIER_SUBDIRS: dict[str, tuple[str, ...]] = {
    "custom": ("custom",),
    "community": ("community",),
    "enterprise": ("enterprise",),
    "thirdparty": ("thirdparty",),
    "pip": ("pip-packages", "apt-packages"),
    "stdlib": ("stdlib",),
}


class SnapshotLayout:
    """Resolve tier↔location within one snapshot root (the single source of truth).

    Args:
        snapshot_root: The on-disk root every tier's files are materialised
            under and served from (bind-mounted ``:ro`` at ``/source`` in the
            live server).
    """

    def __init__(self, snapshot_root: Path) -> None:
        # Absolute + normalised so containment checks compare apples to apples,
        # regardless of how the caller spelled the root.
        self._snapshot_root = Path(os.path.abspath(snapshot_root))

    @property
    def snapshot_root(self) -> Path:
        """The absolute snapshot root every tier is materialised/served under."""
        return self._snapshot_root

    def tier_locations(self, tier: str) -> list[Path]:
        """Return the ORDERED list of physical locations for ``tier`` (C5 forward).

        Args:
            tier: The tier name.

        Returns:
            Absolute directories under the snapshot root, in lookup order. A
            known tier uses :data:`TIER_SUBDIRS`; an unknown tier falls back to a
            single ``<snapshot_root>/<tier>`` location.
        """
        subdirs = TIER_SUBDIRS.get(tier, (tier,))
        return [self._snapshot_root / subdir for subdir in subdirs]

    def materialization_dir(self, tier: str) -> Path:
        """Return the canonical write target for ``tier`` (its first location).

        Args:
            tier: The tier name.

        Returns:
            The directory a :class:`SourceProvider` materialises ``tier`` into.
        """
        return self.tier_locations(tier)[0]

    def resolve(self, tier: str, rel_path: str) -> Path | None:
        """Resolve ``(tier, rel_path)`` to a SAFE, existing absolute path (C5 + C4).

        Tries each of the tier's locations IN ORDER, returning the first that
        contains the file as a safe path (C4 containment). A path that escapes
        its base, or does not exist in any location, yields ``None``.

        Args:
            tier: The tier to look the file up in.
            rel_path: The file path relative to a tier location.

        Returns:
            The safe absolute path to the existing file, or ``None`` if no
            location contains it (or every candidate fails the containment
            guard).
        """
        for base in self.tier_locations(tier):
            safe = self._safe_path(base, rel_path)
            if safe is not None and safe.exists():
                return safe
        return None

    @classmethod
    def contained_path(cls, base: Path, rel_path: str) -> Path | None:
        """Public C4 containment for an ARBITRARY base (the live-root reuse point).

        The reverse :meth:`resolve` is snapshot-tier-scoped, but the C4 check
        itself is base-agnostic: a live workspace root needs the IDENTICAL
        containment guard (reject ``../``, absolute paths, and escaping
        file/intermediate symlinks) without going through the tier→location map.
        Exposing the one audited algorithm as a public method lets the
        ``read_file`` live path reuse it verbatim — single source of truth, never
        a reimplementation. Existence is the caller's concern (matches
        ``_safe_path``: a contained-but-nonexistent path is still returned).

        Args:
            base: The directory the candidate must stay within (e.g. a live root).
            rel_path: The candidate path relative to ``base``.

        Returns:
            The safe contained candidate path, or ``None`` if rejected.
        """
        return cls._safe_path(base, rel_path)

    @staticmethod
    def _safe_path(base: Path, rel_path: str) -> Path | None:
        """Apply the C4 two-tier containment check for one ``(base, rel_path)``.

        Mirrors odoo-code ``read_file.py:144-159``. Returns the contained
        candidate path (which may or may not exist — existence is the caller's
        concern), or ``None`` if ``rel_path`` is malformed or escapes ``base``.

        Args:
            base: The tier-location directory the file must stay within.
            rel_path: The candidate file path relative to ``base``.

        Returns:
            The safe candidate path, or ``None`` if rejected.
        """
        # (1) Input sanitisation — reject absolute paths and any ``..`` component
        # up front (matches read_file.py:42-47); the normpath check below also
        # catches these, but rejecting early keeps the intent explicit.
        if os.path.isabs(rel_path):
            return None
        if any(part == ".." for part in rel_path.split("/")):
            return None

        candidate = base / rel_path

        # (2) normpath-contain: the candidate must normalise to a path inside the
        # NORMALISED base. The base is normalised, NOT resolve()-d, so a tier
        # base that is itself a directory symlink (the live custom root) passes —
        # its literal location is still under the served snapshot subtree.
        norm_candidate = os.path.normpath(candidate)
        norm_base = os.path.normpath(base)
        if norm_candidate != norm_base and not norm_candidate.startswith(norm_base + os.sep):
            return None

        # (3) resolve()-check the FULL candidate, following EVERY link in the chain
        # — intermediate directory symlinks included. Checking only a final-component
        # symlink let an escape through a symlinked INTERMEDIATE dir (e.g. a plain
        # file behind ``evil -> /etc``) slip past, since its last component is not a
        # symlink and step (2) is purely lexical (CWE-59 / CWE-22). The resolved real
        # target must stay within the RESOLVED base: anchoring on ``base.resolve()``
        # (not the snapshot root) lets a legitimately-symlinked live-root base pass —
        # ``base.resolve()`` is its real bind-mount target, so files under it stay
        # ``relative_to`` it — while any path escaping via an intermediate OR final
        # symlink is rejected. ``resolve(strict=False)`` leaves a contained-but-
        # nonexistent tail in place (existence stays the caller's concern); ``OSError``
        # guards broken/cyclic links.
        try:
            Path(candidate).resolve().relative_to(base.resolve())
        except (ValueError, OSError):
            return None

        return Path(norm_candidate)
