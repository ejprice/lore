"""Contract tests for ``loremaster.source`` — the static-tier source/snapshot layer.

This is the substrate that lets the always-on server serve files for *static*
tiers (community/enterprise/pip/stdlib) it never carried on its own disk: a
batch indexer materialises each tier into a host snapshot dir, the server
bind-mounts that dir ``:ro`` at ``/source``, and a tier→location resolver finds
files within it (plan AMENDMENT 1 — D7 ``SourceProvider`` seam, D8 snapshot
serving contract, C4 read-containment algorithm, C5 tier↔location as an ORDERED
LIST, many-to-one).

Two units under test:

* :class:`loremaster.source.snapshot.SnapshotLayout` — the SINGLE SOURCE OF
  TRUTH for tier↔location plus the C4 safe path resolver:

  - **Forward (C5):** ``tier_locations(tier)`` returns an ORDERED LIST of
    physical directories under the snapshot root (NOT 1:1 — ``pip`` resolves to
    ``pip-packages`` then ``apt-packages``, the real apt+pip→``pip`` merge from
    odoo-code's ``discovery.py``/``read_file.py``). ``materialization_dir(tier)``
    is the first (canonical write target).
  - **Reverse (C5 + C4):** ``resolve(tier, rel_path)`` tries the tier's
    locations IN ORDER, returning the first that *contains* the file as a SAFE
    absolute path, or ``None`` (clean not-found/rejected sentinel — no
    exceptions-as-control-flow for the miss case).
  - **C4 safe containment** (hardened past odoo-code ``read_file.py:144-159``): (a)
    normpath-contains the file within the tier base (rejecting ``../`` traversal);
    (b) ALLOWS a tier base that is itself a symlinked directory (the
    live-root-symlink case — normpath the base, do NOT ``resolve()`` it away);
    (c) ``resolve()``-checks the FULL candidate against the resolved base, so an
    escape via a symlinked INTERMEDIATE directory (not just a final file symlink)
    is REJECTED — the audit-caught CWE-59 hole the final-only check had.

* :class:`loremaster.source.local_directory.LocalDirectorySourceProvider` —
  implements the ``SourceProvider`` Protocol (``tier``; ``acquire(tier,
  snapshot_root)``) for a static tier sourced from a plain local directory
  (config ``source:``), materialising its files into the snapshot layout so the
  resolver finds them.

Every test uses REAL ``tmp_path`` directory trees and REAL ``os.symlink`` — the
filesystem is the ground-truth oracle for containment, not the resolver's own
logic (owner directive: real over mocks for the core).
"""

from __future__ import annotations

import os
from pathlib import Path

from loremaster.extension import SourceProvider
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loremaster.source.snapshot import TIER_SUBDIRS, SnapshotLayout


def _write(path: Path, text: str) -> Path:
    """Create ``path``'s parents and write ``text``; return ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class TestTierLocationsForward:
    """C5 forward mapping: tier → ORDERED LIST of physical locations."""

    def test_locations_are_absolute_dirs_under_the_snapshot_root(self) -> None:
        layout = SnapshotLayout(Path("/snap"))
        for location in layout.tier_locations("community"):
            assert location.is_absolute()
            # Every location lives under the snapshot root (the served subtree).
            assert os.path.normpath(location).startswith(os.path.normpath("/snap") + os.sep)

    def test_single_location_tier_maps_one_to_one(self) -> None:
        layout = SnapshotLayout(Path("/snap"))
        assert layout.tier_locations("community") == [Path("/snap/community")]

    def test_pip_tier_has_two_locations_in_order(self) -> None:
        # The apt+pip→pip many-to-one: pip files preferentially in pip-packages,
        # falling back to apt-packages (mirrors odoo-code read_file.py:116-117).
        layout = SnapshotLayout(Path("/snap"))
        locations = layout.tier_locations("pip")
        assert locations == [Path("/snap/pip-packages"), Path("/snap/apt-packages")]

    def test_materialization_dir_is_the_first_location(self) -> None:
        layout = SnapshotLayout(Path("/snap"))
        for tier in ("community", "pip"):
            assert layout.materialization_dir(tier) == layout.tier_locations(tier)[0]

    def test_unknown_tier_falls_back_to_a_subdir_named_after_the_tier(self) -> None:
        # A generic (non-odoo) project's arbitrary tier name just works: its
        # single location is <snapshot_root>/<tier>.
        layout = SnapshotLayout(Path("/snap"))
        assert layout.tier_locations("vendor") == [Path("/snap/vendor")]

    def test_source_of_truth_map_is_keyed_on_relative_subdirs(self) -> None:
        # The canonical map is portable (relative subdir names, not baked-in
        # absolute paths), so it is the SINGLE source of truth across roots.
        assert TIER_SUBDIRS["pip"] == ("pip-packages", "apt-packages")
        assert TIER_SUBDIRS["community"] == ("community",)


class TestResolveReverseLookup:
    """C5 reverse lookup: try the tier's locations IN ORDER, first hit wins."""

    def test_resolves_a_file_in_the_single_location(self, tmp_path: Path) -> None:
        layout = SnapshotLayout(tmp_path)
        target = _write(tmp_path / "community" / "pkg" / "mod.py", "x = 1\n")
        resolved = layout.resolve("community", "pkg/mod.py")
        assert resolved == target

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        layout = SnapshotLayout(tmp_path)
        (tmp_path / "community").mkdir()
        assert layout.resolve("community", "pkg/absent.py") is None

    def test_resolved_path_actually_exists(self, tmp_path: Path) -> None:
        layout = SnapshotLayout(tmp_path)
        _write(tmp_path / "community" / "a.py", "a\n")
        resolved = layout.resolve("community", "a.py")
        assert resolved is not None and resolved.exists()

    def test_second_location_is_searched_when_first_lacks_the_file(self, tmp_path: Path) -> None:
        # THE C5 many-location case (apt+pip→pip analog): a file present ONLY in
        # the SECOND location (apt-packages) must still be found via the reverse
        # lookup walking the ordered list.
        layout = SnapshotLayout(tmp_path)
        (tmp_path / "pip-packages").mkdir()  # first location exists but is empty
        target = _write(tmp_path / "apt-packages" / "lxml" / "etree.py", "cython\n")
        resolved = layout.resolve("pip", "lxml/etree.py")
        assert resolved == target

    def test_first_location_wins_when_both_contain_the_file(self, tmp_path: Path) -> None:
        # Order matters: when both locations have the path, the FIRST in the
        # ordered list is returned (pip-packages preferred over apt-packages).
        layout = SnapshotLayout(tmp_path)
        first = _write(tmp_path / "pip-packages" / "dup.py", "from pip\n")
        _write(tmp_path / "apt-packages" / "dup.py", "from apt\n")
        resolved = layout.resolve("pip", "dup.py")
        assert resolved == first


class TestC4ContainmentSecurity:
    """C4 — the security-critical containment cases (mirrors read_file.py:144-159)."""

    def test_symlinked_tier_base_outside_snapshot_still_resolves_a_normal_file(
        self, tmp_path: Path
    ) -> None:
        # CASE (i) — the LIVE-ROOT case that MUST work: the tier's base directory
        # is itself a symlink to a real dir OUTSIDE the snapshot root (a host
        # checkout bind-mounted in). A normal file inside it resolves OK, because
        # C4 normpath-contains the base (does NOT resolve() the base away).
        snapshot_root = tmp_path / "snap"
        snapshot_root.mkdir()
        real_checkout = tmp_path / "outside" / "checkout"
        target = _write(real_checkout / "src" / "live.py", "live = True\n")
        # The tier base <snapshot>/custom is a directory symlink to the checkout.
        os.symlink(real_checkout, snapshot_root / "custom")

        layout = SnapshotLayout(snapshot_root)
        resolved = layout.resolve("custom", "src/live.py")
        # Resolves to the real file through the symlinked base.
        assert resolved is not None
        assert resolved.resolve() == target.resolve()

    def test_dotdot_traversal_escaping_the_base_is_rejected(self, tmp_path: Path) -> None:
        # CASE (ii) — a rel_path with ../ escaping the tier base is REJECTED.
        layout = SnapshotLayout(tmp_path)
        _write(tmp_path / "community" / "ok.py", "ok\n")
        # A real secret one level above the base; ../ must NOT reach it.
        _write(tmp_path / "secret.py", "SECRET = 1\n")
        assert layout.resolve("community", "../secret.py") is None

    def test_dotdot_traversal_to_a_sibling_location_is_rejected(self, tmp_path: Path) -> None:
        # ../ that lands inside ANOTHER real snapshot subdir is still a traversal
        # OUT of the requested tier's base, and is REJECTED.
        layout = SnapshotLayout(tmp_path)
        _write(tmp_path / "enterprise" / "ent.py", "ent\n")
        (tmp_path / "community").mkdir()
        assert layout.resolve("community", "../enterprise/ent.py") is None

    def test_absolute_rel_path_is_rejected(self, tmp_path: Path) -> None:
        # An absolute "rel_path" must never be honoured (it would ignore the base).
        layout = SnapshotLayout(tmp_path)
        secret = _write(tmp_path / "elsewhere" / "abs.py", "ABS = 1\n")
        assert layout.resolve("community", str(secret)) is None

    def test_file_symlink_inside_base_pointing_outside_is_rejected(self, tmp_path: Path) -> None:
        # CASE (iii) — THE escaping-file-symlink case: a file that lives INSIDE
        # the tier base but is a symlink pointing OUTSIDE the base is REJECTED,
        # because C4 resolve()-checks the final file even when the base is normal.
        layout = SnapshotLayout(tmp_path)
        base = tmp_path / "community"
        base.mkdir()
        secret = _write(tmp_path / "outside_secret.py", "SECRET = 1\n")
        # escape.py is physically inside community/ but symlinks to the secret.
        os.symlink(secret, base / "escape.py")
        assert layout.resolve("community", "escape.py") is None

    def test_escaping_file_symlink_rejected_even_under_a_symlinked_base(
        self, tmp_path: Path
    ) -> None:
        # The two cases combined: a legitimately symlinked live-root base AND an
        # escaping file symlink inside it. The base symlink is allowed, but the
        # escaping file symlink is STILL rejected (resolve-check anchored on the
        # resolved base, not the snapshot root).
        snapshot_root = tmp_path / "snap"
        snapshot_root.mkdir()
        real_checkout = tmp_path / "outside" / "checkout"
        real_checkout.mkdir(parents=True)
        os.symlink(real_checkout, snapshot_root / "custom")
        secret = _write(tmp_path / "way_outside.py", "SECRET = 1\n")
        os.symlink(secret, real_checkout / "leak.py")

        layout = SnapshotLayout(snapshot_root)
        assert layout.resolve("custom", "leak.py") is None

    def test_internal_file_symlink_staying_inside_base_is_allowed(self, tmp_path: Path) -> None:
        # Counterpart to the rejection: a file symlink that stays INSIDE the base
        # is fine — the resolve-check rejects ESCAPE, not symlinks per se.
        layout = SnapshotLayout(tmp_path)
        base = tmp_path / "community"
        real = _write(base / "real" / "impl.py", "impl\n")
        os.symlink(real, base / "alias.py")
        resolved = layout.resolve("community", "alias.py")
        assert resolved is not None
        assert resolved.resolve() == real.resolve()

    def test_normal_nested_file_resolves(self, tmp_path: Path) -> None:
        # CASE (iv) — a normal nested file (no symlink, no traversal) resolves.
        layout = SnapshotLayout(tmp_path)
        target = _write(tmp_path / "enterprise" / "deep" / "nested" / "x.py", "deep\n")
        resolved = layout.resolve("enterprise", "deep/nested/x.py")
        assert resolved == target

    def test_intermediate_directory_symlink_escape_is_rejected(self, tmp_path: Path) -> None:
        # CRITICAL (audit, CWE-59/22): a symlinked INTERMEDIATE directory inside the
        # base, pointing OUTSIDE it, with a PLAIN file behind it. The final path
        # component is NOT a symlink, so a resolve-only-the-final-symlink check skips
        # it and the lexical normpath-contain passes ("evil/leak" is lexically inside
        # base) — yet it reads a file outside the snapshot. The resolver MUST follow
        # the whole chain and reject it.
        layout = SnapshotLayout(tmp_path)
        base = tmp_path / "community"
        base.mkdir()
        outside = tmp_path / "outside_area"
        _write(outside / "leak", "ESCAPED-VIA-INTERMEDIATE-SYMLINK\n")
        os.symlink(outside, base / "evil")  # intermediate DIR symlink escaping base
        assert layout.resolve("community", "evil/leak") is None


class TestLocalDirectorySourceProviderConformance:
    """The provider conforms to the merged ``SourceProvider`` Protocol."""

    def test_is_structurally_a_source_provider(self, tmp_path: Path) -> None:
        provider = LocalDirectorySourceProvider(tier="community", source=tmp_path)
        # runtime_checkable Protocol — an object missing acquire/tier is rejected.
        assert isinstance(provider, SourceProvider)

    def test_tier_attribute_matches_construction(self, tmp_path: Path) -> None:
        provider = LocalDirectorySourceProvider(tier="enterprise", source=tmp_path)
        assert provider.tier == "enterprise"


class TestLocalDirectoryProviderAcquire:
    """``acquire`` materialises a real local dir into the snapshot layout."""

    def test_acquired_files_are_reachable_through_the_resolver(self, tmp_path: Path) -> None:
        # THE end-to-end seam: acquire a REAL local dir as a static tier, then the
        # snapshot resolver finds its files (D7 materialise → D8 serve).
        source = tmp_path / "src_community"
        _write(source / "pkg" / "mod.py", "VALUE = 42\n")
        _write(source / "pkg" / "sub" / "deep.py", "DEEP = 1\n")
        _write(source / "top.py", "TOP = 1\n")

        snapshot_root = tmp_path / "snapshot"
        snapshot_root.mkdir()
        provider = LocalDirectorySourceProvider(tier="community", source=source)
        provider.acquire("community", snapshot_root)

        layout = SnapshotLayout(snapshot_root)
        for rel, expected in (
            ("pkg/mod.py", "VALUE = 42\n"),
            ("pkg/sub/deep.py", "DEEP = 1\n"),
            ("top.py", "TOP = 1\n"),
        ):
            resolved = layout.resolve("community", rel)
            assert resolved is not None, f"{rel} should be reachable after acquire"
            assert resolved.read_text(encoding="utf-8") == expected

    def test_materialises_into_the_tier_materialization_dir(self, tmp_path: Path) -> None:
        # The files land specifically in the layout's materialization dir for the
        # tier (the first/canonical location), not some other place.
        source = tmp_path / "src"
        _write(source / "a.py", "a\n")
        snapshot_root = tmp_path / "snap"
        snapshot_root.mkdir()
        LocalDirectorySourceProvider(tier="community", source=source).acquire(
            "community", snapshot_root
        )
        layout = SnapshotLayout(snapshot_root)
        materialized = layout.materialization_dir("community") / "a.py"
        assert materialized.is_file()
        assert materialized.read_text(encoding="utf-8") == "a\n"

    def test_acquire_is_idempotent(self, tmp_path: Path) -> None:
        # Re-acquiring the same tier (e.g. a rebuild) does not error on the
        # already-present snapshot subtree and reflects the current source.
        source = tmp_path / "src"
        _write(source / "a.py", "first\n")
        snapshot_root = tmp_path / "snap"
        snapshot_root.mkdir()
        provider = LocalDirectorySourceProvider(tier="community", source=source)
        provider.acquire("community", snapshot_root)
        # Mutate the source and re-acquire.
        _write(source / "a.py", "second\n")
        _write(source / "b.py", "new\n")
        provider.acquire("community", snapshot_root)

        layout = SnapshotLayout(snapshot_root)
        a = layout.resolve("community", "a.py")
        b = layout.resolve("community", "b.py")
        assert a is not None and a.read_text(encoding="utf-8") == "second\n"
        assert b is not None and b.read_text(encoding="utf-8") == "new\n"

    def test_acquire_missing_source_raises_clearly(self, tmp_path: Path) -> None:
        # A misconfigured static tier (source path does not exist) fails LOUD at
        # acquire time, not as a silent empty snapshot the server later can't
        # serve. The error names the missing source for remediation.
        snapshot_root = tmp_path / "snap"
        snapshot_root.mkdir()
        missing = tmp_path / "does_not_exist"
        provider = LocalDirectorySourceProvider(tier="community", source=missing)
        try:
            provider.acquire("community", snapshot_root)
        except FileNotFoundError as exc:
            assert str(missing) in str(exc)
        else:  # pragma: no cover - explicit contract assertion
            raise AssertionError("acquire must raise FileNotFoundError on a missing source")

    def test_acquire_preserves_symlinks_so_escaping_links_are_rejected_at_read(
        self, tmp_path: Path
    ) -> None:
        # HIGH (audit, CWE-59/538): a source tier shipping an ESCAPING symlink (a
        # vendored pip package with evil -> a host secret) must NOT be content-baked
        # into the snapshot as a regular file (which the read-time resolver could
        # never catch). acquire must PRESERVE the symlink, so the resolver REJECTS it.
        source = tmp_path / "src"
        _write(source / "pkg" / "ok.py", "ok\n")
        secret = _write(tmp_path / "host_secret.txt", "TOPSECRET-HOST-CONTENT\n")
        os.symlink(secret, source / "pkg" / "evil")  # escaping symlink in the source

        snapshot_root = tmp_path / "snap"
        snapshot_root.mkdir()
        LocalDirectorySourceProvider(tier="community", source=source).acquire(
            "community", snapshot_root
        )
        layout = SnapshotLayout(snapshot_root)
        materialized_evil = layout.materialization_dir("community") / "pkg" / "evil"
        # The symlink is PRESERVED, not copied as the secret's content…
        assert materialized_evil.is_symlink(), "escaping symlink must be preserved, not content-baked"
        # …and the resolver rejects it as an escape (never serves the secret)…
        assert layout.resolve("community", "pkg/evil") is None
        # …while the legitimate sibling file still resolves.
        assert layout.resolve("community", "pkg/ok.py") is not None
