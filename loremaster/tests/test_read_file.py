"""Contract tests for ``loremaster.read_file`` — the tier-aware file-span reader.

``read_file(tier, path, line_start, line_end)`` is one half of the Deliverable-3
MCP read-tool surface: an anti-hallucination primitive that returns the EXACT
on-disk text of a file span, with a ``[SOURCE:...]`` provenance header, so the
model quotes real source rather than recalling it.

It is **tier-aware** (plan AMENDMENT 1 / D8 — tier→location serving):

* a ``live`` tier reads from the injected **live workspace root** (a host
  checkout the always-on server watches), and
* a ``static`` tier resolves through the merged
  :class:`~loremaster.source.snapshot.SnapshotLayout` (community/enterprise/pip/
  stdlib materialised under the snapshot root).

The security boundary (C4 containment) is load-bearing in BOTH directions: the
static path reuses ``SnapshotLayout.resolve`` (the merged, audited C4 resolver —
NOT reimplemented), and the live path applies the SAME containment to the live
root (a ``../`` traversal or an escaping symlink is rejected, never served). A
miss — unknown tier, missing file, traversal, or an out-of-range span — is a
clean error value, never a partial read and never a path escape.

Every test uses REAL ``tmp_path`` trees and REAL ``os.symlink`` so the
filesystem is the ground-truth oracle for containment, exactly as
``tests/test_source.py`` does for the resolver it reuses.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from loremaster.read_file import FileSpan, ReadFileError, ReadFileTool
from loremaster.source.snapshot import SnapshotLayout

# A multi-line live-tier source whose line content is distinct per line, so an
# off-by-one or a wrong-span read is detectable (line N's text contains "N").
_LIVE_SOURCE = "".join(f"line {n}\n" for n in range(1, 11))

# The live tier name and a static tier name the snapshot layout knows.
_LIVE_TIER = "custom"
_STATIC_TIER = "community"


def _write(path: Path, text: str) -> Path:
    """Create ``path``'s parents and write ``text``; return ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _tool(
    live_root: Path,
    snapshot_root: Path,
    *,
    known_tiers: set[str] | None = None,
) -> ReadFileTool:
    """Build a ReadFileTool wired to a live root + a snapshot layout.

    The live tier (``custom``) reads from ``live_root``; every other (static)
    tier resolves through the ``SnapshotLayout`` over ``snapshot_root``.
    ``known_tiers`` is the set of CONFIGURED tier names (so an unknown tier can be
    told apart from a missing file); defaults to the live + the canonical static
    tier this module exercises.
    """
    return ReadFileTool(
        live_roots={_LIVE_TIER: live_root},
        snapshot_layout=SnapshotLayout(snapshot_root),
        known_tiers=known_tiers if known_tiers is not None else {_LIVE_TIER, _STATIC_TIER, "pip"},
    )


class TestLiveTierRead:
    """A live tier reads the exact span from the injected live workspace root."""

    def test_reads_full_file_when_no_span_given(self, tmp_path: Path) -> None:
        live_root = tmp_path / "checkout"
        _write(live_root / "src" / "mod.py", _LIVE_SOURCE)
        span = _tool(live_root, tmp_path / "snap").read_file(_LIVE_TIER, "src/mod.py")
        # No span ⇒ the whole file, byte-for-byte.
        assert span.text == _LIVE_SOURCE
        assert span.line_start == 1
        assert span.line_end == 10

    def test_reads_exact_inclusive_line_span(self, tmp_path: Path) -> None:
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        # Lines 3..5 inclusive — three lines, each naming its own number.
        span = _tool(live_root, tmp_path / "snap").read_file(
            _LIVE_TIER, "a.py", line_start=3, line_end=5
        )
        assert span.text == "line 3\nline 4\nline 5\n"
        assert span.line_start == 3
        assert span.line_end == 5

    def test_single_line_span_start_equals_end(self, tmp_path: Path) -> None:
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        span = _tool(live_root, tmp_path / "snap").read_file(
            _LIVE_TIER, "a.py", line_start=7, line_end=7
        )
        assert span.text == "line 7\n"

    def test_line_start_only_reads_to_end_of_file(self, tmp_path: Path) -> None:
        # An open-ended span (start given, end omitted) runs to EOF.
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        span = _tool(live_root, tmp_path / "snap").read_file(
            _LIVE_TIER, "a.py", line_start=9
        )
        assert span.text == "line 9\nline 10\n"
        assert span.line_start == 9
        assert span.line_end == 10


class TestSourceHeader:
    """The result carries a [SOURCE:...] provenance header naming tier/path/span."""

    def test_header_names_tier_path_and_line_span(self, tmp_path: Path) -> None:
        live_root = tmp_path / "checkout"
        _write(live_root / "pkg" / "thing.py", _LIVE_SOURCE)
        span = _tool(live_root, tmp_path / "snap").read_file(
            _LIVE_TIER, "pkg/thing.py", line_start=2, line_end=4
        )
        header = span.header
        # The provenance header is a [SOURCE:...] citation the model can echo.
        assert header.startswith("[SOURCE:")
        assert header.endswith("]")
        # It names the tier, the path, and the resolved line span.
        assert _LIVE_TIER in header
        assert "pkg/thing.py" in header
        assert "2" in header and "4" in header

    def test_rendered_output_prepends_header_to_span_text(self, tmp_path: Path) -> None:
        # The full rendered tool output is the header followed by the span text,
        # so a caller gets provenance + content in one string.
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        span = _tool(live_root, tmp_path / "snap").read_file(
            _LIVE_TIER, "a.py", line_start=1, line_end=2
        )
        rendered = span.render()
        assert rendered.startswith(span.header)
        assert rendered.endswith(span.text)
        assert span.text in rendered


class TestStaticTierRead:
    """A static tier resolves through the merged SnapshotLayout resolver."""

    def test_reads_a_static_tier_file_via_the_snapshot_resolver(self, tmp_path: Path) -> None:
        snapshot_root = tmp_path / "snap"
        # Materialise a community file the way the provider would, under the
        # tier's canonical location (community/...).
        layout = SnapshotLayout(snapshot_root)
        target = _write(layout.materialization_dir(_STATIC_TIER) / "pkg" / "core.py", _LIVE_SOURCE)
        assert target.exists()  # ground-truth file on disk

        span = _tool(tmp_path / "checkout", snapshot_root).read_file(
            _STATIC_TIER, "pkg/core.py", line_start=4, line_end=6
        )
        assert span.text == "line 4\nline 5\nline 6\n"
        assert _STATIC_TIER in span.header

    def test_static_pip_tier_second_location_is_searched(self, tmp_path: Path) -> None:
        # The C5 many-location case (apt+pip→pip): a file present only in the
        # SECOND pip location must still be read — proving the reader delegates to
        # the ordered-list resolver rather than guessing a single dir.
        snapshot_root = tmp_path / "snap"
        (snapshot_root / "pip-packages").mkdir(parents=True)  # first location empty
        _write(snapshot_root / "apt-packages" / "lxml" / "etree.py", _LIVE_SOURCE)
        span = _tool(tmp_path / "checkout", snapshot_root).read_file(
            "pip", "lxml/etree.py", line_start=1, line_end=1
        )
        assert span.text == "line 1\n"


class TestContainmentRejection:
    """C4 — traversal and escaping symlinks are rejected in BOTH tiers."""

    def test_live_dotdot_traversal_is_rejected(self, tmp_path: Path) -> None:
        # A ../ escaping the LIVE root must not reach a secret one level above it.
        live_root = tmp_path / "checkout"
        _write(live_root / "ok.py", _LIVE_SOURCE)
        _write(tmp_path / "secret.py", "SECRET = 1\n")
        with pytest.raises(ReadFileError):
            _tool(live_root, tmp_path / "snap").read_file(_LIVE_TIER, "../secret.py")

    def test_live_absolute_path_is_rejected(self, tmp_path: Path) -> None:
        live_root = tmp_path / "checkout"
        _write(live_root / "ok.py", _LIVE_SOURCE)
        secret = _write(tmp_path / "elsewhere" / "abs.py", "ABS = 1\n")
        with pytest.raises(ReadFileError):
            _tool(live_root, tmp_path / "snap").read_file(_LIVE_TIER, str(secret))

    def test_live_escaping_file_symlink_is_rejected(self, tmp_path: Path) -> None:
        # A file physically inside the live root but symlinking OUTSIDE it is
        # rejected — the live root gets the SAME resolve()-against-base C4 guard
        # the static resolver applies (CWE-59).
        live_root = tmp_path / "checkout"
        live_root.mkdir()
        secret = _write(tmp_path / "outside_secret.py", "SECRET = 1\n")
        os.symlink(secret, live_root / "escape.py")
        with pytest.raises(ReadFileError):
            _tool(live_root, tmp_path / "snap").read_file(_LIVE_TIER, "escape.py")

    def test_live_intermediate_directory_symlink_escape_is_rejected(self, tmp_path: Path) -> None:
        # CWE-59/22: a symlinked INTERMEDIATE directory escaping the live root,
        # with a PLAIN file behind it (final component not a symlink). The reader
        # must follow the whole chain and reject it.
        live_root = tmp_path / "checkout"
        live_root.mkdir()
        outside = tmp_path / "outside_area"
        _write(outside / "leak", "ESCAPED\n")
        os.symlink(outside, live_root / "evil")
        with pytest.raises(ReadFileError):
            _tool(live_root, tmp_path / "snap").read_file(_LIVE_TIER, "evil/leak")

    def test_static_dotdot_traversal_is_rejected(self, tmp_path: Path) -> None:
        # The static path delegates to SnapshotLayout.resolve, which rejects ../.
        snapshot_root = tmp_path / "snap"
        layout = SnapshotLayout(snapshot_root)
        _write(layout.materialization_dir(_STATIC_TIER) / "ok.py", _LIVE_SOURCE)
        _write(snapshot_root / "secret.py", "SECRET = 1\n")
        with pytest.raises(ReadFileError):
            _tool(tmp_path / "checkout", snapshot_root).read_file(
                _STATIC_TIER, "../secret.py"
            )

    def test_static_escaping_symlink_is_rejected(self, tmp_path: Path) -> None:
        # An escaping file symlink inside a static tier base is rejected by the
        # reused resolver — never served.
        snapshot_root = tmp_path / "snap"
        layout = SnapshotLayout(snapshot_root)
        base = layout.materialization_dir(_STATIC_TIER)
        base.mkdir(parents=True)
        secret = _write(tmp_path / "host_secret.py", "SECRET = 1\n")
        os.symlink(secret, base / "leak.py")
        with pytest.raises(ReadFileError):
            _tool(tmp_path / "checkout", snapshot_root).read_file(_STATIC_TIER, "leak.py")


class TestMissingAndOutOfRange:
    """Missing files, unknown tiers, and out-of-range spans are clean errors."""

    def test_missing_file_raises_clean_error(self, tmp_path: Path) -> None:
        live_root = tmp_path / "checkout"
        live_root.mkdir()
        with pytest.raises(ReadFileError):
            _tool(live_root, tmp_path / "snap").read_file(_LIVE_TIER, "nope.py")

    def test_unknown_tier_raises_clean_error(self, tmp_path: Path) -> None:
        # A tier that is neither the live tier nor resolvable by the snapshot
        # layout (no such materialised dir) is a clean not-found, not a crash.
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        with pytest.raises(ReadFileError):
            _tool(live_root, tmp_path / "snap").read_file(
                "no_such_tier", "whatever.py"
            )

    def test_line_start_past_end_of_file_raises(self, tmp_path: Path) -> None:
        # A start beyond EOF (the file has 10 lines) is out of range — a clean
        # error, never an empty silent read.
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        with pytest.raises(ReadFileError):
            _tool(live_root, tmp_path / "snap").read_file(
                _LIVE_TIER, "a.py", line_start=50
            )

    def test_line_end_before_line_start_raises(self, tmp_path: Path) -> None:
        # An inverted span (end < start) is invalid input — rejected loudly.
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        with pytest.raises(ReadFileError):
            _tool(live_root, tmp_path / "snap").read_file(
                _LIVE_TIER, "a.py", line_start=5, line_end=2
            )

    def test_non_positive_line_start_raises(self, tmp_path: Path) -> None:
        # Lines are 1-based; a zero or negative start is invalid (would otherwise
        # alias Python's negative indexing and read from the tail).
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        with pytest.raises(ReadFileError):
            _tool(live_root, tmp_path / "snap").read_file(
                _LIVE_TIER, "a.py", line_start=0
            )

    def test_line_end_past_eof_is_clamped_not_errored(self, tmp_path: Path) -> None:
        # A valid start with an end past EOF clamps to the last line (a generous
        # read), distinct from a start past EOF (which is a hard error). This
        # mirrors a tolerant "give me from line 8 onward" request.
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        span = _tool(live_root, tmp_path / "snap").read_file(
            _LIVE_TIER, "a.py", line_start=8, line_end=999
        )
        assert span.text == "line 8\nline 9\nline 10\n"
        assert span.line_end == 10


class TestFileSpanValueObject:
    """FileSpan is a plain, inspectable value object (no raw path leakage)."""

    def test_span_exposes_tier_path_and_span_fields(self, tmp_path: Path) -> None:
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        span: FileSpan = _tool(live_root, tmp_path / "snap").read_file(
            _LIVE_TIER, "a.py", line_start=1, line_end=3
        )
        assert span.tier == _LIVE_TIER
        assert span.path == "a.py"
        assert span.line_start == 1
        assert span.line_end == 3


class TestErrorDisambiguation:
    """The three failure modes are DISTINCT, actionable messages (Item 6).

    Today read_file conflates unknown-tier / missing-file / containment-rejection
    into one vague message. Each must instead carry its OWN clear, actionable text:
    an unknown tier LISTS the configured tiers; a genuinely-missing file says "not
    found in tier X" + a next step; a containment rejection names the guard. The
    containment guard behaviour is UNCHANGED — only the messaging improves — so the
    traversal-still-blocked assertions below stay non-vacuous (a real secret one
    level up is NOT served).
    """

    def test_unknown_tier_lists_the_configured_tiers(self, tmp_path: Path) -> None:
        live_root = tmp_path / "checkout"
        _write(live_root / "a.py", _LIVE_SOURCE)
        tool = _tool(live_root, tmp_path / "snap", known_tiers={_LIVE_TIER, _STATIC_TIER})
        with pytest.raises(ReadFileError) as exc_info:
            tool.read_file("no_such_tier", "whatever.py")
        message = str(exc_info.value)
        assert "no_such_tier" in message, "the error must name the bad tier"
        assert "tier" in message.lower()
        # It LISTS the configured tiers so the caller can correct the typo.
        assert _LIVE_TIER in message and _STATIC_TIER in message

    def test_missing_file_says_not_found_in_tier_with_next_step(
        self, tmp_path: Path
    ) -> None:
        # A KNOWN tier (live) but the file is absent (and NOT a traversal) — a
        # distinct "not found in tier X" message that points at a next step.
        live_root = tmp_path / "checkout"
        live_root.mkdir()
        tool = _tool(live_root, tmp_path / "snap")
        with pytest.raises(ReadFileError) as exc_info:
            tool.read_file(_LIVE_TIER, "absent.py")
        message = str(exc_info.value)
        assert "absent.py" in message
        assert "not found" in message.lower()
        assert _LIVE_TIER in message
        # A next step (reindex / search_code / verify the path) is suggested.
        assert any(hint in message.lower() for hint in ("reindex", "search_code", "verify", "check")), (
            "a missing-file error must point the caller at a next step"
        )
        # The message must NOT pretend it might be a containment rejection (the
        # conflated old text). This is what makes the disambiguation real.
        assert "containment" not in message.lower()

    def test_missing_static_file_says_not_found_in_tier(self, tmp_path: Path) -> None:
        # A KNOWN static tier whose file is absent — distinct "not found" message,
        # not an unknown-tier or containment one.
        snapshot_root = tmp_path / "snap"
        layout = SnapshotLayout(snapshot_root)
        layout.materialization_dir(_STATIC_TIER).mkdir(parents=True)
        tool = _tool(tmp_path / "checkout", snapshot_root)
        with pytest.raises(ReadFileError) as exc_info:
            tool.read_file(_STATIC_TIER, "gone.py")
        message = str(exc_info.value)
        assert "gone.py" in message
        assert "not found" in message.lower()
        assert _STATIC_TIER in message
        assert "containment" not in message.lower()

    def test_live_containment_rejection_has_its_own_message_and_still_blocks(
        self, tmp_path: Path
    ) -> None:
        # A ../ traversal on a known live tier gets the CONTAINMENT message — and
        # the secret one level up is STILL not served (the guard is unchanged; this
        # assertion is non-vacuous because the secret exists and would leak if the
        # guard regressed).
        live_root = tmp_path / "checkout"
        _write(live_root / "ok.py", _LIVE_SOURCE)
        _write(tmp_path / "secret.py", "SECRET = 1\n")
        tool = _tool(live_root, tmp_path / "snap")
        with pytest.raises(ReadFileError) as exc_info:
            tool.read_file(_LIVE_TIER, "../secret.py")
        message = str(exc_info.value)
        assert "containment" in message.lower() or "traversal" in message.lower(), (
            "a traversal rejection must carry the containment-specific message"
        )
        # The secret's CONTENT must never appear in the error (no leak).
        assert "SECRET = 1" not in message

    def test_static_containment_rejection_has_its_own_message(self, tmp_path: Path) -> None:
        snapshot_root = tmp_path / "snap"
        layout = SnapshotLayout(snapshot_root)
        layout.materialization_dir(_STATIC_TIER).mkdir(parents=True)
        _write(snapshot_root / "secret.py", "SECRET = 1\n")
        tool = _tool(tmp_path / "checkout", snapshot_root)
        with pytest.raises(ReadFileError) as exc_info:
            tool.read_file(_STATIC_TIER, "../secret.py")
        message = str(exc_info.value)
        assert "containment" in message.lower() or "traversal" in message.lower()
        assert "SECRET = 1" not in message
