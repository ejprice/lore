"""Tests for :mod:`loremaster.calibration.baseline` — corpus loading, sha256
integrity, schema validation, and the committed baseline's coherence with the
frozen corpus.

The integrity helper is the engine's guard: before comparing token counts it must
be able to prove the on-disk corpus still matches the bytes the baseline was
generated from. These tests pin that helper and the committed artifact together.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from loremaster.calibration import baseline as bl


def _baseline_from_corpus(corpus: dict[str, bytes]) -> dict[str, Any]:
    """A minimally-valid baseline dict whose sha256s match ``corpus`` exactly."""
    files = {
        name: {"claude_tokens": len(data), "voyage_tokens": len(data), "sha256": bl.sha256_hex(data)}
        for name, data in sorted(corpus.items())
    }
    return {
        "schema_version": bl.SCHEMA_VERSION,
        "generated_at": "2026-07-04T00:00:00+00:00",
        "generator": bl.GENERATOR_REL_PATH,
        "model": bl.BASELINE_MODEL,
        "generation_note": bl.GENERATION_NOTE,
        "endpoint": "https://api.anthropic.com/v1/messages/count_tokens",
        "files": files,
        "claude_total": sum(f["claude_tokens"] for f in files.values()),
        "voyage_total": sum(f["voyage_tokens"] for f in files.values()),
    }


class TestCorpusLoading:
    def test_loads_frozen_txt_files_only(self) -> None:
        corpus = bl.load_corpus()
        assert 8 <= len(corpus) <= 15
        assert all(name.endswith(bl.CORPUS_SUFFIX) for name in corpus)
        assert all(isinstance(data, bytes) and data for data in corpus.values())

    def test_total_bytes_in_expected_band(self) -> None:
        corpus = bl.load_corpus()
        total = sum(len(data) for data in corpus.values())
        assert 50_000 <= total <= 160_000

    def test_keys_are_sorted(self) -> None:
        corpus = bl.load_corpus()
        assert list(corpus) == sorted(corpus)


class TestSha256:
    def test_matches_hashlib(self) -> None:
        data = b"the quick brown fox\n"
        assert bl.sha256_hex(data) == hashlib.sha256(data).hexdigest()


class TestIntegrityHelper:
    def test_ok_when_baseline_matches_corpus(self) -> None:
        corpus = bl.load_corpus()
        result = bl.verify_corpus_integrity(_baseline_from_corpus(corpus), corpus)
        assert result.ok
        assert set(result.matched) == set(corpus)
        assert result.mismatched == ()
        assert result.missing == ()
        assert result.unexpected == ()

    def test_detects_sha_mismatch(self) -> None:
        corpus = bl.load_corpus()
        tampered = _baseline_from_corpus(corpus)
        victim = sorted(corpus)[0]
        tampered["files"][victim]["sha256"] = "0" * 64
        result = bl.verify_corpus_integrity(tampered, corpus)
        assert not result.ok
        assert victim in result.mismatched

    def test_detects_missing_baseline_file(self) -> None:
        corpus = bl.load_corpus()
        baseline = _baseline_from_corpus(corpus)
        baseline["files"]["ghost.py.txt"] = {"claude_tokens": 1, "voyage_tokens": 1, "sha256": "0" * 64}
        result = bl.verify_corpus_integrity(baseline, corpus)
        assert not result.ok
        assert "ghost.py.txt" in result.missing

    def test_detects_unexpected_corpus_file(self) -> None:
        corpus = bl.load_corpus()
        baseline = _baseline_from_corpus(corpus)
        dropped = sorted(corpus)[0]
        del baseline["files"][dropped]
        result = bl.verify_corpus_integrity(baseline, corpus)
        assert not result.ok
        assert dropped in result.unexpected


class TestSchemaValidation:
    def test_accepts_wellformed(self) -> None:
        corpus = bl.load_corpus()
        good = _baseline_from_corpus(corpus)
        assert bl.validate_baseline(good) is good

    def test_rejects_wrong_schema_version(self) -> None:
        corpus = bl.load_corpus()
        bad = _baseline_from_corpus(corpus)
        bad["schema_version"] = 999
        with pytest.raises(ValueError):
            bl.validate_baseline(bad)

    def test_rejects_missing_top_level_key(self) -> None:
        corpus = bl.load_corpus()
        bad = _baseline_from_corpus(corpus)
        del bad["endpoint"]
        with pytest.raises(ValueError):
            bl.validate_baseline(bad)

    def test_rejects_claude_total_mismatch(self) -> None:
        corpus = bl.load_corpus()
        bad = _baseline_from_corpus(corpus)
        bad["claude_total"] = bad["claude_total"] + 1
        with pytest.raises(ValueError):
            bl.validate_baseline(bad)

    def test_rejects_non_dict(self) -> None:
        with pytest.raises(ValueError):
            bl.validate_baseline(["not", "a", "dict"])


class TestBaselineRoundTrip:
    def test_save_then_load_is_identity(self, tmp_path: Path) -> None:
        corpus = bl.load_corpus()
        original = _baseline_from_corpus(corpus)
        out = tmp_path / "baseline.json"
        bl.save_baseline(original, out)
        loaded = bl.load_baseline(out)
        assert loaded == original
        # And the file is valid JSON on disk.
        assert json.loads(out.read_text(encoding="utf-8")) == original


class TestCommittedBaseline:
    """Ties the committed ``baseline.json`` to the frozen corpus (lifecycle guard)."""

    def test_committed_baseline_loads_validates_and_matches_corpus(self) -> None:
        committed = bl.load_baseline()  # default = the packaged baseline.json
        bl.validate_baseline(committed)
        assert committed["model"] == bl.BASELINE_MODEL
        assert committed["schema_version"] == bl.SCHEMA_VERSION
        result = bl.verify_corpus_integrity(committed)
        assert result.ok, f"corpus drifted from baseline: {result}"
        assert all(entry["claude_tokens"] > 0 for entry in committed["files"].values())
        assert committed["claude_total"] == sum(
            entry["claude_tokens"] for entry in committed["files"].values()
        )

    def test_committed_baseline_is_not_mutated_by_verify(self) -> None:
        committed = bl.load_baseline()
        snapshot = copy.deepcopy(committed)
        bl.verify_corpus_integrity(committed)
        assert committed == snapshot
