"""Tests for ``scripts/snapshot_gc.py`` — the legacy-snapshot GC driver.

Covers the PURE partition/classification logic (epoch boundary, the
exactly-equal edge, unclassifiable-timestamp anomaly), manifest rendering, the
total-wipe safety guard, and the ``main``/``run_gc`` wiring (store + stamper
stubbed out, so the test is hermetic and never touches a real SurrealDB).
"""

from __future__ import annotations

import os
import sys
from typing import Any

# The driver lives in ``scripts/`` (not a package) — make it importable. Mirrors
# ``scripts/test_calibration_baseline.py``.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest  # noqa: E402
import snapshot_gc as gc  # type: ignore[import-not-found]  # noqa: E402  (scripts/ is not a package)
from loremaster.diff import SnapshotSummary  # noqa: E402
from pydantic import SecretStr  # noqa: E402

_EPOCH = "2026-07-04T22:42:00Z"


def _summary(
    snapshot_id: str,
    created_at: str,
    *,
    files_total: int = 1,
    chunks_total: int = 1,
) -> SnapshotSummary:
    """A minimal snapshot summary for the pure-logic tests."""
    return SnapshotSummary(
        id=snapshot_id,
        created_at=created_at,
        git_ref=None,
        git_branch=None,
        files_total=files_total,
        chunks_total=chunks_total,
    )


class TestParseEpoch:
    def test_accepts_trailing_z(self) -> None:
        assert gc.parse_epoch("2026-07-04T22:42:00Z") == gc.parse_epoch(
            "2026-07-04T22:42:00+00:00"
        )

    def test_naive_is_interpreted_as_utc(self) -> None:
        # A naive epoch is treated as UTC, equal to the same instant tz-aware.
        assert gc.parse_epoch("2026-07-04T22:42:00") == gc.parse_epoch(
            "2026-07-04T22:42:00Z"
        )

    def test_result_is_timezone_aware(self) -> None:
        assert gc.parse_epoch(_EPOCH).tzinfo is not None

    def test_rejects_garbage(self) -> None:
        with pytest.raises(ValueError):
            gc.parse_epoch("not-a-timestamp")


class TestPartitionSnapshots:
    def test_keeps_newer_deletes_older(self) -> None:
        epoch = gc.parse_epoch(_EPOCH)
        newer = _summary("snapshot:new", "2026-07-04T23:00:00Z")
        older = _summary("snapshot:old", "2026-07-04T10:00:00Z")
        plan = gc.partition_snapshots([newer, older], epoch)
        assert plan.keep == [newer]
        assert plan.delete == [older]

    def test_epoch_boundary_exactly_equal_is_kept(self) -> None:
        # THE pinned edge: a snapshot created at exactly the epoch is KEPT,
        # never deleted (keep >= epoch, including the epoch snapshot itself).
        epoch = gc.parse_epoch(_EPOCH)
        boundary = _summary("snapshot:boundary", "2026-07-04T22:42:00Z")
        plan = gc.partition_snapshots([boundary], epoch)
        assert plan.keep == [boundary]
        assert plan.delete == []

    def test_one_microsecond_before_epoch_is_deleted(self) -> None:
        epoch = gc.parse_epoch(_EPOCH)
        just_before = _summary("snapshot:before", "2026-07-04T22:41:59.999999Z")
        plan = gc.partition_snapshots([just_before], epoch)
        assert plan.delete == [just_before]
        assert plan.keep == []

    def test_offset_and_z_forms_compare_equal(self) -> None:
        # A stored created_at rendered as +00:00 (isoformat) partitions the same
        # as the Z-suffixed epoch.
        epoch = gc.parse_epoch(_EPOCH)
        boundary = _summary("snapshot:iso", "2026-07-04T22:42:00+00:00")
        plan = gc.partition_snapshots([boundary], epoch)
        assert plan.keep == [boundary]

    def test_raises_on_unparseable_created_at(self) -> None:
        # Loud on any anomaly: an unclassifiable timestamp is refused, never
        # silently swept into DELETE.
        epoch = gc.parse_epoch(_EPOCH)
        broken = _summary("snapshot:broken", "whenever")
        with pytest.raises(gc.SnapshotClassificationError) as excinfo:
            gc.partition_snapshots([broken], epoch)
        assert "snapshot:broken" in str(excinfo.value)

    def test_naive_epoch_is_normalised_before_compare(self) -> None:
        # A naive epoch datetime still compares correctly against aware rows.
        from datetime import datetime

        naive_epoch = datetime.fromisoformat("2026-07-04T22:42:00")
        boundary = _summary("snapshot:boundary", "2026-07-04T22:42:00Z")
        plan = gc.partition_snapshots([boundary], naive_epoch)
        assert plan.keep == [boundary]


class TestTotalWipeGuard:
    def test_true_when_keep_empty_and_delete_nonempty(self) -> None:
        epoch = gc.parse_epoch(_EPOCH)
        older = _summary("snapshot:old", "2020-01-01T00:00:00Z")
        plan = gc.partition_snapshots([older], epoch)
        assert gc.is_total_wipe(plan) is True

    def test_false_when_something_is_kept(self) -> None:
        epoch = gc.parse_epoch(_EPOCH)
        newer = _summary("snapshot:new", "2026-07-04T23:00:00Z")
        older = _summary("snapshot:old", "2020-01-01T00:00:00Z")
        plan = gc.partition_snapshots([newer, older], epoch)
        assert gc.is_total_wipe(plan) is False

    def test_false_when_nothing_to_delete(self) -> None:
        epoch = gc.parse_epoch(_EPOCH)
        plan = gc.partition_snapshots([], epoch)
        assert gc.is_total_wipe(plan) is False


class TestRenderManifest:
    def test_marks_dispositions_and_counts(self) -> None:
        epoch = gc.parse_epoch(_EPOCH)
        newer = _summary("snapshot:new", "2026-07-04T23:00:00Z", files_total=7, chunks_total=42)
        older = _summary("snapshot:old", "2026-07-04T10:00:00Z")
        plan = gc.partition_snapshots([newer, older], epoch)
        text = gc.render_manifest([newer, older], plan)
        assert "KEEP" in text
        assert "DELETE" in text
        assert "snapshot:new" in text
        assert "snapshot:old" in text
        # File / chunk counts are shown (the brief's id/created_at/counts).
        assert "files=7" in text
        assert "chunks=42" in text
        # A summary line names both partition sizes.
        assert "KEEP 1" in text
        assert "DELETE 1" in text


class _FakeStamper:
    """Records the snapshot ids handed to ``delete_snapshot`` — never connects."""

    def __init__(self) -> None:
        self.deleted: list[str] = []

    async def delete_snapshot(self, snapshot_id: str) -> None:
        self.deleted.append(snapshot_id)


def _wire_fakes(
    monkeypatch: Any,
    summaries: list[SnapshotSummary],
    stamper: _FakeStamper,
) -> None:
    """Stub out the two store-touching seams so ``run_gc`` is hermetic."""
    # Must return what the REAL ``resolve_secret`` returns — a ``SecretStr`` (#211).
    # A fake that hands back a bare ``str`` tests a seam production does not have.
    monkeypatch.setattr(gc, "resolve_secret", lambda name: SecretStr(f"dummy-{name}"))

    async def _fake_list(**_kwargs: Any) -> list[SnapshotSummary]:
        return summaries

    async def _fake_delete(plan: Any, **_kwargs: Any) -> None:
        for summary in plan.delete:
            await stamper.delete_snapshot(summary.id)

    monkeypatch.setattr(gc, "_list_snapshots", _fake_list)
    monkeypatch.setattr(gc, "_delete_snapshots", _fake_delete)


class TestMainWiring:
    def test_dry_run_prints_manifest_and_deletes_nothing(
        self, monkeypatch: Any, capsys: Any
    ) -> None:
        stamper = _FakeStamper()
        summaries = [
            _summary("snapshot:new", "2026-07-04T23:00:00Z"),
            _summary("snapshot:old", "2026-07-04T10:00:00Z"),
        ]
        _wire_fakes(monkeypatch, summaries, stamper)

        exit_code = gc.main(["--epoch", _EPOCH])

        assert exit_code == 0
        assert stamper.deleted == []  # DRY RUN — nothing deleted
        captured = capsys.readouterr()
        assert "snapshot:old" in captured.out
        assert "DELETE" in captured.out

    def test_execute_deletes_only_the_delete_partition(
        self, monkeypatch: Any, capsys: Any
    ) -> None:
        stamper = _FakeStamper()
        summaries = [
            _summary("snapshot:keep", "2026-07-04T23:00:00Z"),
            _summary("snapshot:doomed", "2026-07-04T10:00:00Z"),
        ]
        _wire_fakes(monkeypatch, summaries, stamper)

        exit_code = gc.main(["--epoch", _EPOCH, "--execute"])

        assert exit_code == 0
        assert stamper.deleted == ["snapshot:doomed"]  # only the older one

    def test_execute_refuses_total_wipe(self, monkeypatch: Any, capsys: Any) -> None:
        # A misconfigured epoch that would keep NOTHING must be refused loudly
        # — the driver never wipes every snapshot.
        stamper = _FakeStamper()
        summaries = [_summary("snapshot:old", "2020-01-01T00:00:00Z")]
        _wire_fakes(monkeypatch, summaries, stamper)

        exit_code = gc.main(["--epoch", _EPOCH, "--execute"])

        assert exit_code != 0
        assert stamper.deleted == []  # refused — nothing deleted
        captured = capsys.readouterr()
        assert "wipe" in captured.err.lower() or "refus" in captured.err.lower()

    def test_unparseable_created_at_is_a_loud_nonzero_exit(
        self, monkeypatch: Any, capsys: Any
    ) -> None:
        stamper = _FakeStamper()
        summaries = [_summary("snapshot:broken", "whenever")]
        _wire_fakes(monkeypatch, summaries, stamper)

        exit_code = gc.main(["--epoch", _EPOCH])

        assert exit_code != 0
        assert stamper.deleted == []
        captured = capsys.readouterr()
        assert "snapshot:broken" in captured.err
