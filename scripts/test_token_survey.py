"""Unit tests for the deterministic core of ``scripts/token_survey.py``.

These cover the four pure, network-free concerns the survey depends on:

* **File discovery + exclusion** — glob by extension, prune excluded directories
  (exact names *and* ``fnmatch`` patterns such as ``odoo-custom-wt-*``), skip
  oversize and empty files.
* **Stratification** — group discovered files by ``(top_level_dir, extension)``.
* **Sampling determinism** — the seeded, stratified sampler yields the *same*
  sample for the same seed and honours the ``ceil(fraction * size)`` /
  ``min(floor, size)`` sizing rule.
* **Statistics math** — file-weighted percentiles, the token-weighted ratio, the
  token-weighted percentile, and the recommended-ceiling derivation.

The live token-counting client (Voyage tokenizer + Anthropic ``count_tokens``
endpoint) is intentionally *out of scope* here — it is exercised by the real
survey run, not by unit tests.
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import pytest

# The survey module lives beside this test file in ``scripts/`` (not an
# installed package), so make that directory importable before importing it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import token_survey as ts  # noqa: E402  (path insert must precede the import)


# --------------------------------------------------------------------------- #
# top_level_dir
# --------------------------------------------------------------------------- #
class TestTopLevelDir:
    def test_nested_file_returns_first_component(self) -> None:
        assert ts.top_level_dir("loremaster/loremaster/graph.py") == "loremaster"

    def test_root_file_returns_root_sentinel(self) -> None:
        assert ts.top_level_dir("README.md") == ts.ROOT_DIR_LABEL


# --------------------------------------------------------------------------- #
# FileDiscovery — globbing + exclusion rules
# --------------------------------------------------------------------------- #
class TestFileDiscovery:
    def _spec(self, root: Path, **kw: object) -> ts.ProjectSpec:
        defaults = dict(
            slug="t",
            root=root,
            include_exts=(".py", ".md"),
            exclude_dir_patterns=(".git", "__pycache__", "odoo-custom-wt-*"),
            follow_symlinks=False,
        )
        defaults.update(kw)
        return ts.ProjectSpec(**defaults)  # type: ignore[arg-type]

    def test_globs_only_requested_extensions(self, tmp_path: Path) -> None:
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "b.md").write_text("# hi\n")
        (tmp_path / "c.json").write_text("{}\n")
        (tmp_path / "d.txt").write_text("nope\n")

        entries, _skips = ts.FileDiscovery(self._spec(tmp_path)).discover()

        rels = {e.relpath for e in entries}
        assert rels == {"a.py", "b.md"}

    def test_prunes_excluded_dirs_exact_and_pattern(self, tmp_path: Path) -> None:
        (tmp_path / "keep.py").write_text("k = 1\n")
        for bad in (".git", "__pycache__", "odoo-custom-wt-pr52"):
            d = tmp_path / bad
            d.mkdir()
            (d / "buried.py").write_text("hidden = 1\n")

        entries, _skips = ts.FileDiscovery(self._spec(tmp_path)).discover()

        assert {e.relpath for e in entries} == {"keep.py"}

    def test_skips_oversize_files_with_log(self, tmp_path: Path) -> None:
        (tmp_path / "small.py").write_text("s = 1\n")
        big = tmp_path / "big.py"
        big.write_text("# " + ("z" * 50))  # tiny, but we cap discovery low
        spec = self._spec(tmp_path)

        entries, skips = ts.FileDiscovery(spec, max_bytes=10).discover()

        assert {e.relpath for e in entries} == {"small.py"}
        assert any(s.relpath == "big.py" and "oversize" in s.reason for s in skips)

    def test_skips_empty_files_with_log(self, tmp_path: Path) -> None:
        (tmp_path / "real.py").write_text("r = 1\n")
        (tmp_path / "empty.py").write_text("")

        entries, skips = ts.FileDiscovery(self._spec(tmp_path)).discover()

        assert {e.relpath for e in entries} == {"real.py"}
        assert any(s.relpath == "empty.py" and "empty" in s.reason for s in skips)

    def test_path_anchored_exclude_prunes_only_at_anchor(self, tmp_path: Path) -> None:
        # A slash-bearing pattern is PATH-anchored: it prunes exactly its
        # relative-path subtree, never a same-named dir elsewhere. (The DI
        # manifest depends on this: demand/data/models is excluded while the
        # real source dir demand/src/demand/models must survive.)
        (tmp_path / "keep.py").write_text("k = 1\n")
        excluded = tmp_path / "demand" / "data" / "models"
        excluded.mkdir(parents=True)
        (excluded / "readme.md").write_text("# checkpoint\n")
        kept_sibling = tmp_path / "demand" / "data" / "reports"
        kept_sibling.mkdir(parents=True)
        (kept_sibling / "brief.md").write_text("# brief\n")
        real_source = tmp_path / "demand" / "src" / "demand" / "models"
        real_source.mkdir(parents=True)
        (real_source / "real.py").write_text("r = 1\n")
        buried_git = tmp_path / ".git"
        buried_git.mkdir()
        (buried_git / "hook.py").write_text("g = 1\n")

        spec = self._spec(
            tmp_path,
            exclude_dir_patterns=(".git", "demand/data/models"),
        )
        entries, _skips = ts.FileDiscovery(spec).discover()

        rels = {e.relpath.replace(os.sep, "/") for e in entries}
        assert rels == {
            "keep.py",
            "demand/data/reports/brief.md",
            "demand/src/demand/models/real.py",
        }

    def test_entry_carries_stratum_metadata(self, tmp_path: Path) -> None:
        pkg = tmp_path / "loremaster"
        pkg.mkdir()
        (pkg / "graph.py").write_text("g = 1\n")

        entries, _skips = ts.FileDiscovery(self._spec(tmp_path)).discover()

        (entry,) = entries
        assert entry.top_dir == "loremaster"
        assert entry.ext == ".py"
        assert entry.relpath == os.path.join("loremaster", "graph.py")
        assert entry.size_bytes > 0


# --------------------------------------------------------------------------- #
# Stratification
# --------------------------------------------------------------------------- #
class TestStratify:
    def _entry(self, relpath: str) -> ts.FileEntry:
        return ts.FileEntry(
            path=Path("/abs") / relpath,
            relpath=relpath,
            top_dir=ts.top_level_dir(relpath),
            ext=Path(relpath).suffix.lower(),
            size_bytes=10,
        )

    def test_groups_by_topdir_and_ext(self) -> None:
        entries = [
            self._entry("loremaster/a.py"),
            self._entry("loremaster/b.py"),
            self._entry("loremaster/c.md"),
            self._entry("loresigil/d.py"),
        ]
        strata = ts.stratify(entries)

        assert set(strata.keys()) == {
            ("loremaster", ".py"),
            ("loremaster", ".md"),
            ("loresigil", ".py"),
        }
        assert len(strata[("loremaster", ".py")]) == 2


# --------------------------------------------------------------------------- #
# Sample sizing rule
# --------------------------------------------------------------------------- #
class TestStratumSampleSize:
    @pytest.mark.parametrize(
        "size, expected",
        [
            (0, 0),
            (1, 1),      # ceil(.1)=1, floor min(5,1)=1
            (3, 3),      # floor min(5,3)=3 dominates
            (40, 5),     # ceil(4)=4, floor 5 dominates
            (50, 5),     # ceil(5)=5 == floor 5
            (100, 10),   # ceil(10)=10 dominates
            (137, 14),   # ceil(13.7)=14
        ],
    )
    def test_sizing(self, size: int, expected: int) -> None:
        assert ts.stratum_sample_size(size, fraction=0.10, min_sample=5) == expected

    def test_never_exceeds_stratum(self) -> None:
        for size in range(0, 30):
            assert ts.stratum_sample_size(size, 0.10, 5) <= size


# --------------------------------------------------------------------------- #
# Sampling determinism
# --------------------------------------------------------------------------- #
class TestSampleStratified:
    def _strata(self, n: int) -> dict[tuple[str, str], list[ts.FileEntry]]:
        entries = [
            ts.FileEntry(
                path=Path(f"/abs/pkg/f{i:03d}.py"),
                relpath=f"pkg/f{i:03d}.py",
                top_dir="pkg",
                ext=".py",
                size_bytes=100 + i,
            )
            for i in range(n)
        ]
        return ts.stratify(entries)

    def test_same_seed_same_sample(self) -> None:
        strata = self._strata(100)
        a = ts.sample_stratified(strata, fraction=0.10, seed=42)
        b = ts.sample_stratified(strata, fraction=0.10, seed=42)
        assert [e.relpath for e in a] == [e.relpath for e in b]

    def test_different_seed_differs(self) -> None:
        strata = self._strata(100)
        a = ts.sample_stratified(strata, fraction=0.10, seed=42)
        b = ts.sample_stratified(strata, fraction=0.10, seed=7)
        assert [e.relpath for e in a] != [e.relpath for e in b]

    def test_sample_size_matches_rule(self) -> None:
        strata = self._strata(100)
        sample = ts.sample_stratified(strata, fraction=0.10, seed=42)
        assert len(sample) == 10  # single stratum of 100 → 10

    def test_sample_is_subset_and_unique(self) -> None:
        strata = self._strata(37)
        sample = ts.sample_stratified(strata, fraction=0.10, seed=42)
        rels = [e.relpath for e in sample]
        all_rels = {e.relpath for group in strata.values() for e in group}
        assert set(rels).issubset(all_rels)
        assert len(rels) == len(set(rels))  # no duplicates

    def test_multi_stratum_totals(self) -> None:
        entries = (
            [
                ts.FileEntry(Path(f"/a/x/{i}.py"), f"x/{i}.py", "x", ".py", 10)
                for i in range(100)
            ]
            + [
                ts.FileEntry(Path(f"/a/y/{i}.md"), f"y/{i}.md", "y", ".md", 10)
                for i in range(3)
            ]
        )
        strata = ts.stratify(entries)
        sample = ts.sample_stratified(strata, fraction=0.10, seed=42)
        # 100-file stratum -> 10, 3-file stratum -> 3 (floor).
        assert len(sample) == 13


# --------------------------------------------------------------------------- #
# Percentiles
# --------------------------------------------------------------------------- #
class TestPercentiles:
    def test_weighted_percentile_unweighted_matches_nearest_rank(self) -> None:
        pairs = [(float(v), 1.0) for v in range(1, 11)]  # 1..10
        assert ts.weighted_percentile(pairs, 0) == 1.0
        assert ts.weighted_percentile(pairs, 100) == 10.0
        assert ts.weighted_percentile(pairs, 50) == 5.0
        assert ts.weighted_percentile(pairs, 95) == 10.0

    def test_weight_shifts_the_tail(self) -> None:
        # 90% of the token-mass sits at ratio 1.0, 10% at 2.0.
        pairs = [(1.0, 90.0), (2.0, 10.0)]
        assert ts.weighted_percentile(pairs, 50) == 1.0
        assert ts.weighted_percentile(pairs, 95) == 2.0

    def test_percentile_helper_is_file_weighted(self) -> None:
        assert ts.percentile([1.0, 2.0, 3.0, 4.0], 100) == 4.0
        assert ts.percentile([5.0], 50) == 5.0

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            ts.weighted_percentile([], 50)


# --------------------------------------------------------------------------- #
# Summary + ceiling derivation
# --------------------------------------------------------------------------- #
class TestSummary:
    def _m(self, voyage: int, claude: int) -> ts.FileMeasurement:
        return ts.FileMeasurement(
            project="t",
            path="pkg/f.py",
            ext=".py",
            bytes=100,
            voyage=voyage,
            claude=claude,
        )

    def test_ratio_is_claude_over_voyage(self) -> None:
        assert self._m(100, 165).ratio == pytest.approx(1.65)

    def test_token_weighted_ratio_is_sum_over_sum(self) -> None:
        # File A: 100 voyage / 200 claude (ratio 2.0);
        # File B: 900 voyage / 900 claude (ratio 1.0).
        # File-mean ratio = 1.5; token-weighted = 1100/1000 = 1.1.
        summary = ts.summarize([self._m(100, 200), self._m(900, 900)])
        assert summary.token_weighted_ratio == pytest.approx(1.1)
        assert summary.file_mean == pytest.approx(1.5)
        assert summary.n == 2
        assert summary.total_voyage == 1000
        assert summary.total_claude == 1100

    def test_token_weighted_p95_weights_by_voyage(self) -> None:
        # A huge low-ratio file must not let a tiny high-ratio file dominate p95.
        summary = ts.summarize([self._m(9000, 9000), self._m(10, 30)])
        # 9000/9010 of the voyage-mass is at ratio 1.0 -> p95 stays 1.0.
        assert summary.token_weighted_p95 == pytest.approx(1.0)

    def test_recommended_ceiling_is_max_p95_rounded_up(self) -> None:
        s1 = ts.summarize([self._m(100, 171), self._m(100, 172)])  # p95 ~1.72
        s2 = ts.summarize([self._m(100, 160), self._m(100, 168)])  # p95 ~1.68
        ceiling = ts.recommended_ceiling([s1, s2])
        assert ceiling == pytest.approx(1.72)

    def test_ceiling_rounds_up_not_to_even(self) -> None:
        # token-weighted p95 of a single 1.611 ratio -> ceil to 1.62.
        s = ts.summarize([self._m(1000, 1611)])
        assert ts.recommended_ceiling([s]) == pytest.approx(1.62)

    def test_ceiling_exact_two_decimals_not_bumped(self) -> None:
        # A clean 1.70 must not float-drift up to 1.71.
        s = ts.summarize([self._m(100, 170)])
        assert ts.recommended_ceiling([s]) == pytest.approx(1.70)


# --------------------------------------------------------------------------- #
# Multi-model plumbing — yardstick-model comparison
# --------------------------------------------------------------------------- #
class TestFileMeasurementModelField:
    def test_default_model_is_backward_compatible(self) -> None:
        # Existing (pre-multi-model) call sites never pass `model=`; the field
        # must default so they keep constructing valid rows.
        m = ts.FileMeasurement(project="t", path="f.py", ext=".py", bytes=10, voyage=100, claude=165)
        assert m.model == ts.ANTHROPIC_MODEL
        assert m.ratio == pytest.approx(1.65)

    def test_to_row_includes_model(self) -> None:
        m = ts.FileMeasurement(
            project="t", path="f.py", ext=".py", bytes=10, voyage=100, claude=165, model="claude-opus-4-8"
        )
        row = m.to_row()
        assert row["model"] == "claude-opus-4-8"


class TestResolveAvailableModels:
    def test_all_ok_survive_in_order(self) -> None:
        survivors, dropped = ts.resolve_available_models(
            {"claude-sonnet-5": None, "claude-opus-4-8": None, "claude-fable-5": None}
        )
        assert survivors == ["claude-sonnet-5", "claude-opus-4-8", "claude-fable-5"]
        assert dropped == []

    def test_failed_model_is_dropped_with_verbatim_error(self) -> None:
        survivors, dropped = ts.resolve_available_models(
            {
                "claude-sonnet-5": None,
                "claude-fable-5": "count_tokens failed (400): org retention policy",
            }
        )
        assert survivors == ["claude-sonnet-5"]
        assert dropped == [("claude-fable-5", "count_tokens failed (400): org retention policy")]

    def test_all_failed_yields_no_survivors(self) -> None:
        survivors, dropped = ts.resolve_available_models({"m1": "boom"})
        assert survivors == []
        assert dropped == [("m1", "boom")]


class TestFilterByModel:
    def _m(self, model: str, path: str = "f.py") -> ts.FileMeasurement:
        return ts.FileMeasurement(
            project="t", path=path, ext=".py", bytes=10, voyage=100, claude=150, model=model
        )

    def test_filters_and_preserves_order(self) -> None:
        measurements = [
            self._m("claude-sonnet-5", "a.py"),
            self._m("claude-opus-4-8", "a.py"),
            self._m("claude-sonnet-5", "b.py"),
        ]
        sonnet_only = ts.filter_by_model(measurements, "claude-sonnet-5")
        assert [m.path for m in sonnet_only] == ["a.py", "b.py"]
        assert all(m.model == "claude-sonnet-5" for m in sonnet_only)

    def test_no_match_returns_empty(self) -> None:
        assert ts.filter_by_model([self._m("claude-sonnet-5")], "claude-fable-5") == []


class TestMaxPairwiseRelativeDelta:
    def test_two_values(self) -> None:
        assert ts.max_pairwise_relative_delta({"a": 100.0, "b": 110.0}) == pytest.approx(0.10)

    def test_three_values_uses_global_min_max(self) -> None:
        # Middle value must not affect the result — only min/max matter.
        assert ts.max_pairwise_relative_delta({"a": 100.0, "b": 105.0, "c": 130.0}) == pytest.approx(0.30)

    def test_single_value_is_zero(self) -> None:
        assert ts.max_pairwise_relative_delta({"a": 42.0}) == 0.0

    def test_empty_is_zero(self) -> None:
        assert ts.max_pairwise_relative_delta({}) == 0.0

    def test_identical_values_is_zero(self) -> None:
        assert ts.max_pairwise_relative_delta({"a": 1.7, "b": 1.7, "c": 1.7}) == 0.0

    def test_zero_baseline_raises(self) -> None:
        with pytest.raises(ValueError):
            ts.max_pairwise_relative_delta({"a": 0.0, "b": 5.0})


class TestCompareModels:
    def test_requires_at_least_two_models(self) -> None:
        with pytest.raises(ValueError):
            ts.compare_models(
                "lore",
                total_claude_by_model={"claude-sonnet-5": 100},
                ratio_by_model={"claude-sonnet-5": 1.6},
                ceiling_by_model={"claude-sonnet-5": 1.7},
            )

    def test_computes_pairwise_deltas_and_passes_through_maps(self) -> None:
        result = ts.compare_models(
            "lore",
            total_claude_by_model={"claude-sonnet-5": 1000, "claude-opus-4-8": 1010},
            ratio_by_model={"claude-sonnet-5": 1.60, "claude-opus-4-8": 1.62},
            ceiling_by_model={"claude-sonnet-5": 1.70, "claude-opus-4-8": 1.75},
        )
        assert result.scope == "lore"
        assert result.models == ("claude-sonnet-5", "claude-opus-4-8")
        assert result.total_claude_by_model == {"claude-sonnet-5": 1000, "claude-opus-4-8": 1010}
        assert result.max_delta_total_claude == pytest.approx(0.01)
        assert result.max_delta_ratio == pytest.approx((1.62 - 1.60) / 1.60)
        assert result.max_delta_ceiling == pytest.approx((1.75 - 1.70) / 1.70)


class TestComputeAgreement:
    def _row(self, project: str, path: str, model: str, claude: int) -> ts.FileMeasurement:
        return ts.FileMeasurement(
            project=project, path=path, ext=".py", bytes=10, voyage=100, claude=claude, model=model
        )

    def test_all_identical_across_models(self) -> None:
        measurements = [
            self._row("lore", "a.py", "claude-sonnet-5", 165),
            self._row("lore", "a.py", "claude-opus-4-8", 165),
            self._row("lore", "a.py", "claude-fable-5", 165),
        ]
        stats = ts.compute_agreement(measurements, ["claude-sonnet-5", "claude-opus-4-8", "claude-fable-5"], scope="lore")
        assert stats.n_complete == 1
        assert stats.n_incomplete == 0
        assert stats.share_identical == pytest.approx(1.0)
        assert stats.max_relative_spread == pytest.approx(0.0)

    def test_divergent_counts_produce_spread(self) -> None:
        measurements = [
            self._row("lore", "a.py", "claude-sonnet-5", 100),
            self._row("lore", "a.py", "claude-opus-4-8", 110),
            self._row("lore", "b.py", "claude-sonnet-5", 200),
            self._row("lore", "b.py", "claude-opus-4-8", 200),
        ]
        stats = ts.compute_agreement(measurements, ["claude-sonnet-5", "claude-opus-4-8"], scope="lore")
        assert stats.n_complete == 2
        assert stats.share_identical == pytest.approx(0.5)  # only b.py agrees
        assert stats.max_relative_spread == pytest.approx(0.10)  # (110-100)/100

    def test_incomplete_file_excluded_from_complete_stats(self) -> None:
        measurements = [
            self._row("lore", "a.py", "claude-sonnet-5", 100),
            self._row("lore", "a.py", "claude-opus-4-8", 100),
            self._row("lore", "b.py", "claude-sonnet-5", 200),  # opus missing for b.py
        ]
        stats = ts.compute_agreement(measurements, ["claude-sonnet-5", "claude-opus-4-8"], scope="lore")
        assert stats.n_complete == 1
        assert stats.n_incomplete == 1
        assert stats.share_identical == pytest.approx(1.0)

    def test_single_model_is_trivially_identical(self) -> None:
        measurements = [self._row("lore", "a.py", "claude-sonnet-5", 100)]
        stats = ts.compute_agreement(measurements, ["claude-sonnet-5"], scope="lore")
        assert stats.n_complete == 1
        assert stats.share_identical == pytest.approx(1.0)
        assert stats.max_relative_spread == pytest.approx(0.0)

    def test_no_complete_files_zeroes_out(self) -> None:
        stats = ts.compute_agreement([], ["claude-sonnet-5", "claude-opus-4-8"], scope="lore")
        assert stats.n_complete == 0
        assert stats.share_identical == 0.0
        assert stats.max_relative_spread == 0.0


class TestCompareToBaseline:
    def _m(self, path: str, claude: int, model: str = "claude-sonnet-5") -> ts.FileMeasurement:
        return ts.FileMeasurement(
            project="lore", path=path, ext=".py", bytes=10, voyage=100, claude=claude, model=model
        )

    def test_identical_counts_are_zero_drift(self) -> None:
        baseline = {"a.py": 165, "b.py": 200}
        new = [self._m("a.py", 165), self._m("b.py", 200)]
        drift = ts.compare_to_baseline(baseline, new, scope="lore", model="claude-sonnet-5")
        assert drift.n_matched == 2
        assert drift.n_identical == 2
        assert drift.max_abs_diff == 0
        assert drift.max_rel_diff == pytest.approx(0.0)

    def test_drift_is_measured(self) -> None:
        baseline = {"a.py": 100}
        new = [self._m("a.py", 105)]
        drift = ts.compare_to_baseline(baseline, new, scope="lore", model="claude-sonnet-5")
        assert drift.n_matched == 1
        assert drift.n_identical == 0
        assert drift.max_abs_diff == 5
        assert drift.max_rel_diff == pytest.approx(0.05)
        assert drift.mean_abs_diff == pytest.approx(5.0)

    def test_unmatched_paths_counted_both_sides(self) -> None:
        baseline = {"a.py": 100, "only_old.py": 50}
        new = [self._m("a.py", 100), self._m("only_new.py", 20)]
        drift = ts.compare_to_baseline(baseline, new, scope="lore", model="claude-sonnet-5")
        assert drift.n_matched == 1
        assert drift.n_unmatched_baseline == 1
        assert drift.n_unmatched_new == 1

    def test_no_overlap_zeroes_out(self) -> None:
        drift = ts.compare_to_baseline({"a.py": 1}, [self._m("only_new.py", 2)], scope="lore", model="claude-sonnet-5")
        assert drift.n_matched == 0
        assert drift.max_abs_diff == 0
        assert drift.max_rel_diff == pytest.approx(0.0)

    def test_only_matching_model_counted(self) -> None:
        baseline = {"a.py": 100}
        new = [self._m("a.py", 999, model="claude-opus-4-8"), self._m("a.py", 100, model="claude-sonnet-5")]
        drift = ts.compare_to_baseline(baseline, new, scope="lore", model="claude-sonnet-5")
        assert drift.n_matched == 1
        assert drift.n_identical == 1


class TestLoadBaselineClaudeCounts:
    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        assert ts.load_baseline_claude_counts(tmp_path / "nope.jsonl") is None

    def test_loads_path_to_claude_map(self, tmp_path: Path) -> None:
        jsonl = tmp_path / "survey_lore.jsonl"
        jsonl.write_text(
            '{"project": "lore", "path": "a.py", "claude": 165, "voyage": 100}\n'
            '{"project": "lore", "path": "b.py", "claude": 200, "voyage": 120}\n'
        )
        counts = ts.load_baseline_claude_counts(jsonl)
        assert counts == {"a.py": 165, "b.py": 200}

    def test_skips_blank_lines(self, tmp_path: Path) -> None:
        jsonl = tmp_path / "s.jsonl"
        jsonl.write_text('{"path": "a.py", "claude": 1}\n\n{"path": "b.py", "claude": 2}\n')
        counts = ts.load_baseline_claude_counts(jsonl)
        assert counts == {"a.py": 1, "b.py": 2}


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
