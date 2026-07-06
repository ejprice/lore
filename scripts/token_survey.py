"""Token-calibration survey over the lore / odoo / demand-intelligence corpora.

Purpose
-------
lore counts token budgets in *Voyage* currency (via
:class:`loresigil.tokens.VoyageTokenCounter`), but when the same text is handed
to Claude it is billed/limited in *Claude* tokens.  The two tokenizers disagree,
so lore needs a calibrated ceiling ``claude_tokens <= CEILING * voyage_tokens``
to convert a Voyage budget into a safe Claude budget.

This tool replaces a six-file pilot (ratio range 1.61-1.72) with a *measured*
distribution over a stratified 10% sample of each real corpus.  It emits per-file
JSONL rows and a markdown summary, and derives a single recommended ceiling
constant = the max over projects of each project's token-weighted p95 ratio,
rounded up to two decimals.

Design
------
The deterministic core — discovery, exclusion, stratification, seeded sampling,
and the statistics math — is pure and unit-tested (``test_token_survey.py``).
The live token-counting client (Voyage tokenizer + Anthropic ``count_tokens``
endpoint) is the only network surface and is intentionally test-exempt.

Sampling is *stratified* by ``(top-level directory, extension)`` and *seeded*, so
the same seed always reproduces the same sample.  Each stratum contributes
``ceil(fraction * size)`` files, floored at ``min(5, size)`` and capped at the
stratum size, drawn deterministically from the sorted file list.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import fnmatch
import json
import math
import os
import random
import statistics
import sys
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

import httpx
from loresigil.tokens import VoyageTokenCounter

# --------------------------------------------------------------------------- #
# Constants — no magic values
# --------------------------------------------------------------------------- #
DEFAULT_FRACTION: float = 0.10
DEFAULT_SEED: int = 42
#: Files larger than this are skipped (logged, never silently dropped).
MAX_FILE_BYTES: int = int(1.5 * 1024 * 1024)  # 1.5 MiB
#: Each stratum contributes at least this many files (or all of it, if smaller).
MIN_STRATUM_SAMPLE: int = 5
#: Sentinel top-level "directory" for files that live directly in the repo root.
ROOT_DIR_LABEL: str = "<root>"

#: Anthropic token-counting endpoint (billed as free; no completion generated).
ANTHROPIC_COUNT_TOKENS_URL: str = "https://api.anthropic.com/v1/messages/count_tokens"
ANTHROPIC_MODEL: str = "claude-sonnet-5"
#: The yardstick question — do these three share one tokenizer generation?
#: (see docs/design/2026-07-04-token-survey-results.md). Order is preserved
#: through probing/reporting so the report reads in this priority order.
DEFAULT_MODELS: tuple[str, ...] = ("claude-sonnet-5", "claude-opus-4-8", "claude-fable-5")
ANTHROPIC_VERSION: str = "2023-06-01"
ANTHROPIC_API_KEY_ENV: str = "ANTHROPIC_API_KEY"
#: The operator-authorised env file the key is sourced from when not already set.
DEFAULT_ENV_FILE: Path = Path.home() / "docker" / "mcp" / ".env"

#: Progress hook signature: ``(project_slug, files_done, files_total) -> None``.
ProgressCallback = Callable[[str, int, int], None]

MAX_CONCURRENCY: int = 4
MAX_RETRIES: int = 6
RETRY_BASE_DELAY_S: float = 1.0
RETRY_MAX_DELAY_S: float = 30.0
PROGRESS_EVERY: int = 200

# Percentiles reported for the ratio distributions.
PCT_P5: float = 5.0
PCT_MEDIAN: float = 50.0
PCT_P95: float = 95.0


# --------------------------------------------------------------------------- #
# Value objects
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ProjectSpec:
    """A corpus to survey: where it lives and how to discover its files."""

    slug: str
    root: Path
    include_exts: tuple[str, ...]
    exclude_dir_patterns: tuple[str, ...]
    follow_symlinks: bool = False
    #: Optional human note surfaced in the report (e.g. worktree-exclusion count).
    note: str = ""


@dataclass(frozen=True)
class FileEntry:
    """A discovered, eligible file plus its stratification metadata."""

    path: Path
    relpath: str
    top_dir: str
    ext: str
    size_bytes: int


@dataclass(frozen=True)
class SkipRecord:
    """A file excluded during discovery/counting, with the reason (always logged)."""

    relpath: str
    reason: str


@dataclass(frozen=True)
class FileMeasurement:
    """A counted file: token counts in both currencies and their ratio.

    One instance is *one (file, model)* pair — a multi-model survey produces
    ``len(models)`` measurements per sampled file, all sharing the same
    ``project``/``path``/``voyage`` but a distinct ``model``/``claude``. This
    keeps :func:`summarize` untouched (it already operates on any homogeneous
    list of measurements); callers select a model's slice with
    :func:`filter_by_model` before summarizing.
    """

    project: str
    path: str
    ext: str
    bytes: int
    voyage: int
    claude: int
    #: Which Claude model produced ``claude``. Defaults to the historical
    #: single-model constant so pre-existing call sites need no changes.
    model: str = ANTHROPIC_MODEL

    @property
    def ratio(self) -> float:
        """claude_tokens / voyage_tokens (voyage is guaranteed > 0 by discovery)."""
        return self.claude / self.voyage

    def to_row(self) -> dict[str, object]:
        """A JSON-serialisable per-file survey row."""
        return {
            "project": self.project,
            "path": self.path,
            "ext": self.ext,
            "bytes": self.bytes,
            "voyage": self.voyage,
            "model": self.model,
            "claude": self.claude,
            "ratio": round(self.ratio, 6),
        }


@dataclass(frozen=True)
class RatioSummary:
    """Aggregate ratio statistics for a set of measurements (one label)."""

    label: str
    n: int
    total_voyage: int
    total_claude: int
    token_weighted_ratio: float
    file_mean: float
    file_median: float
    file_p5: float
    file_p95: float
    file_max: float
    token_weighted_p5: float
    token_weighted_p95: float


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #
def top_level_dir(relpath: str) -> str:
    """Return the first path component of ``relpath`` (or the root sentinel).

    Args:
        relpath: A path relative to a project root, e.g. ``loremaster/x.py``.

    Returns:
        The first path component (``loremaster``), or :data:`ROOT_DIR_LABEL`
        when the file sits directly in the root (no separator).
    """
    parts = Path(relpath).parts
    return parts[0] if len(parts) > 1 else ROOT_DIR_LABEL


class FileDiscovery:
    """Walk a project root, applying the corpus's inclusion/exclusion rules.

    Excluded directories are pruned during the walk.  Two pattern flavours are
    supported so a single ``exclude_dir_patterns`` tuple can express both:

    * **Bare-name patterns** (no ``/``, e.g. ``.git``, ``__pycache__``,
      ``odoo-custom-wt-*``) match a directory *basename* at any depth — the right
      semantics for caches/VCS/worktree dirs that recur throughout a tree.
    * **Path-anchored patterns** (containing ``/``, e.g. ``demand/data/models``,
      ``validation/artifacts``) match a directory by its path *relative to the
      project root*, so they prune exactly that subtree and never a same-named
      directory elsewhere.  The DI manifest depends on this: ``demand/data/models``
      is excluded while the real source dir ``demand/src/demand/models`` survives.

    Oversize and empty files are skipped at ``stat`` time.  Binary/non-UTF-8 files
    cannot be detected without reading, so they are caught later at count time —
    never silently.
    """

    def __init__(self, spec: ProjectSpec, max_bytes: int = MAX_FILE_BYTES) -> None:
        self._spec = spec
        self._max_bytes = max_bytes

    def _dir_excluded(self, dirpath: str, name: str) -> bool:
        """Whether the subdirectory ``name`` under ``dirpath`` is excluded.

        Path-anchored patterns are matched against the subdirectory's path
        relative to the project root; bare-name patterns against its basename.
        """
        rel_posix = os.path.relpath(
            os.path.join(dirpath, name), self._spec.root
        ).replace(os.sep, "/")
        for pattern in self._spec.exclude_dir_patterns:
            if "/" in pattern:
                if fnmatch.fnmatch(rel_posix, pattern):
                    return True
            elif fnmatch.fnmatch(name, pattern):
                return True
        return False

    def discover(self) -> tuple[list[FileEntry], list[SkipRecord]]:
        """Discover eligible files under the project root.

        Returns:
            A tuple ``(entries, skips)`` — ``entries`` sorted by relative path for
            determinism, ``skips`` recording every excluded file with its reason.
        """
        root = self._spec.root
        include_exts = {ext.lower() for ext in self._spec.include_exts}
        entries: list[FileEntry] = []
        skips: list[SkipRecord] = []

        for dirpath, dirnames, filenames in os.walk(
            root, followlinks=self._spec.follow_symlinks
        ):
            # Prune excluded directories in place so os.walk never descends them.
            dirnames[:] = [
                d for d in dirnames if not self._dir_excluded(dirpath, d)
            ]
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in include_exts:
                    continue
                abspath = Path(dirpath) / filename
                relpath = os.path.relpath(abspath, root)
                try:
                    size_bytes = abspath.stat().st_size
                except OSError as exc:  # broken symlink, race, permissions
                    skips.append(SkipRecord(relpath, f"stat_error:{exc.errno}"))
                    continue
                if size_bytes == 0:
                    skips.append(SkipRecord(relpath, "empty:0-bytes"))
                    continue
                if size_bytes > self._max_bytes:
                    skips.append(
                        SkipRecord(relpath, f"oversize:{size_bytes}>{self._max_bytes}")
                    )
                    continue
                entries.append(
                    FileEntry(
                        path=abspath,
                        relpath=relpath,
                        top_dir=top_level_dir(relpath),
                        ext=ext,
                        size_bytes=size_bytes,
                    )
                )

        entries.sort(key=lambda entry: entry.relpath)
        skips.sort(key=lambda skip: skip.relpath)
        return entries, skips


# --------------------------------------------------------------------------- #
# Stratification + sampling
# --------------------------------------------------------------------------- #
def stratify(entries: Iterable[FileEntry]) -> dict[tuple[str, str], list[FileEntry]]:
    """Group entries into strata keyed by ``(top_dir, ext)``.

    Args:
        entries: Discovered files.

    Returns:
        A dict mapping each ``(top_dir, ext)`` key to its (path-sorted) files.
    """
    strata: dict[tuple[str, str], list[FileEntry]] = {}
    for entry in entries:
        strata.setdefault((entry.top_dir, entry.ext), []).append(entry)
    for group in strata.values():
        group.sort(key=lambda entry: entry.relpath)
    return strata


def stratum_sample_size(
    stratum_size: int,
    fraction: float = DEFAULT_FRACTION,
    min_sample: int = MIN_STRATUM_SAMPLE,
) -> int:
    """Number of files to draw from a stratum of ``stratum_size``.

    ``ceil(fraction * size)`` files, floored at ``min(min_sample, size)`` and
    capped at ``size`` (never sample more files than exist).
    """
    if stratum_size <= 0:
        return 0
    proportional = math.ceil(fraction * stratum_size)
    floor = min(min_sample, stratum_size)
    return min(stratum_size, max(proportional, floor))


def sample_stratified(
    strata: dict[tuple[str, str], list[FileEntry]],
    fraction: float = DEFAULT_FRACTION,
    seed: int = DEFAULT_SEED,
    min_sample: int = MIN_STRATUM_SAMPLE,
) -> list[FileEntry]:
    """Draw a deterministic, seeded, stratified sample.

    Strata are visited in sorted key order and each is sampled from its
    path-sorted file list with a single seeded RNG, so the same ``seed`` always
    reproduces the same sample.

    Returns:
        The sampled files, sorted by relative path.
    """
    rng = random.Random(seed)
    sample: list[FileEntry] = []
    for key in sorted(strata.keys()):
        group = strata[key]
        ordered = sorted(group, key=lambda entry: entry.relpath)
        k = stratum_sample_size(len(ordered), fraction, min_sample)
        sample.extend(rng.sample(ordered, k))
    sample.sort(key=lambda entry: entry.relpath)
    return sample


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def weighted_percentile(pairs: Sequence[tuple[float, float]], pct: float) -> float:
    """Weighted nearest-rank percentile of ``pairs`` of ``(value, weight)``.

    Values are ordered ascending; the returned value is the first whose
    cumulative weight reaches ``pct%`` of the total weight.  With uniform weights
    this reduces to the ordinary nearest-rank percentile; weighting by token
    count answers "for X% of the token-mass, the ratio is at most this".

    Args:
        pairs: ``(value, weight)`` pairs; every weight must be > 0.
        pct: Percentile in ``[0, 100]``.

    Returns:
        The percentile value.

    Raises:
        ValueError: If ``pairs`` is empty.
    """
    if not pairs:
        raise ValueError("weighted_percentile requires at least one (value, weight)")
    ordered = sorted(pairs, key=lambda vw: vw[0])
    total_weight = math.fsum(weight for _value, weight in ordered)
    threshold = (pct / 100.0) * total_weight
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return ordered[-1][0]


def percentile(values: Sequence[float], pct: float) -> float:
    """File-weighted (uniform-weight) percentile — thin wrapper over the weighted one."""
    return weighted_percentile([(value, 1.0) for value in values], pct)


def summarize(measurements: Sequence[FileMeasurement], label: str = "") -> RatioSummary:
    """Aggregate ratio statistics over a set of measurements.

    Computes both *file-weighted* percentiles (each file counts once) and the
    *token-weighted* ratio and percentiles (each file weighted by its Voyage
    token count — the quantity the ceiling multiplies).
    """
    if not measurements:
        raise ValueError("cannot summarize an empty measurement set")
    ratios = [m.ratio for m in measurements]
    total_voyage = sum(m.voyage for m in measurements)
    total_claude = sum(m.claude for m in measurements)
    voyage_weighted = [(m.ratio, float(m.voyage)) for m in measurements]
    return RatioSummary(
        label=label,
        n=len(measurements),
        total_voyage=total_voyage,
        total_claude=total_claude,
        token_weighted_ratio=total_claude / total_voyage,
        file_mean=statistics.fmean(ratios),
        file_median=statistics.median(ratios),
        file_p5=percentile(ratios, PCT_P5),
        file_p95=percentile(ratios, PCT_P95),
        file_max=max(ratios),
        token_weighted_p5=weighted_percentile(voyage_weighted, PCT_P5),
        token_weighted_p95=weighted_percentile(voyage_weighted, PCT_P95),
    )


def recommended_ceiling(summaries: Sequence[RatioSummary]) -> float:
    """The recommended ceiling: max token-weighted p95 across projects, ceil'd to 2dp.

    Args:
        summaries: One :class:`RatioSummary` per project.

    Returns:
        ``ceil(max_p95 * 100) / 100`` — a value that safely bounds 95% of the
        token-mass in every surveyed project.
    """
    if not summaries:
        raise ValueError("cannot derive a ceiling from no summaries")
    max_p95 = max(summary.token_weighted_p95 for summary in summaries)
    # Round before ceil so float drift (1.70 -> 169.9999) does not bump the value.
    return math.ceil(round(max_p95 * 100.0, 6)) / 100.0


# --------------------------------------------------------------------------- #
# Multi-model (yardstick) plumbing — pure, unit-tested
# --------------------------------------------------------------------------- #
def resolve_available_models(
    probe_results: Mapping[str, str | None],
) -> tuple[list[str], list[tuple[str, str]]]:
    """Split a model-probe result into survivors and dropped-with-reason.

    Args:
        probe_results: ``{model: None}`` for a model that probed cleanly, or
            ``{model: error_message}`` (verbatim) for one that failed.

    Returns:
        ``(survivors, dropped)`` — ``survivors`` preserves the input mapping's
        iteration order; ``dropped`` pairs each failed model with its verbatim
        error message, for the run to flag and continue without it.
    """
    survivors = [model for model, error in probe_results.items() if error is None]
    dropped = [(model, error) for model, error in probe_results.items() if error is not None]
    return survivors, dropped


def filter_by_model(measurements: Sequence[FileMeasurement], model: str) -> list[FileMeasurement]:
    """The subset of ``measurements`` counted by ``model``, order preserved."""
    return [measurement for measurement in measurements if measurement.model == model]


def max_pairwise_relative_delta(values_by_key: Mapping[str, float]) -> float:
    """The max pairwise relative delta ``(max - min) / min`` across ``values_by_key``.

    Only the global min and max matter (the pair realising the max delta is
    always the extremes) — a middle value can never widen it further.

    Args:
        values_by_key: One value per key (e.g. per model). Fewer than two
            values has no pairwise delta.

    Returns:
        ``0.0`` for 0 or 1 values, or when all values are identical.

    Raises:
        ValueError: If the minimum value is exactly ``0`` and values differ
            (a relative delta against a zero baseline is undefined).
    """
    values = list(values_by_key.values())
    if len(values) < 2:
        return 0.0
    lo, hi = min(values), max(values)
    if lo == hi:
        return 0.0
    if lo == 0.0:
        raise ValueError("cannot compute a relative delta against a zero baseline")
    return (hi - lo) / lo


@dataclass(frozen=True)
class CrossModelComparison:
    """Cross-model spread stats for one scope (a project slug, or ``overall``)."""

    scope: str
    models: tuple[str, ...]
    total_claude_by_model: dict[str, int]
    token_weighted_ratio_by_model: dict[str, float]
    ceiling_by_model: dict[str, float]
    max_delta_total_claude: float
    max_delta_ratio: float
    max_delta_ceiling: float


def compare_models(
    scope: str,
    total_claude_by_model: Mapping[str, int],
    ratio_by_model: Mapping[str, float],
    ceiling_by_model: Mapping[str, float],
) -> CrossModelComparison:
    """Compute the max pairwise cross-model delta on three axes for one scope.

    Args:
        scope: A project slug, or ``"overall"``.
        total_claude_by_model: Raw summed Claude-token totals, per model.
        ratio_by_model: The token-weighted ``claude/voyage`` ratio, per model.
        ceiling_by_model: The ceiling-relevant statistic for this scope, per
            model — the project's own token-weighted p95 for a per-project
            scope, or the actual :func:`recommended_ceiling` for ``"overall"``.

    Raises:
        ValueError: If fewer than two models are given (nothing to compare).
    """
    if len(total_claude_by_model) < 2:
        raise ValueError("compare_models requires at least two models")
    return CrossModelComparison(
        scope=scope,
        models=tuple(total_claude_by_model.keys()),
        total_claude_by_model=dict(total_claude_by_model),
        token_weighted_ratio_by_model=dict(ratio_by_model),
        ceiling_by_model=dict(ceiling_by_model),
        max_delta_total_claude=max_pairwise_relative_delta(
            {model: float(total) for model, total in total_claude_by_model.items()}
        ),
        max_delta_ratio=max_pairwise_relative_delta(ratio_by_model),
        max_delta_ceiling=max_pairwise_relative_delta(ceiling_by_model),
    )


@dataclass(frozen=True)
class AgreementStats:
    """Per-file cross-model agreement for one scope.

    ``n_complete`` files had a successful count from *every* requested model;
    ``n_incomplete`` files were missing at least one model's count (a per-file
    partial failure) and are excluded from the agreement/spread stats below.
    """

    scope: str
    models: tuple[str, ...]
    n_complete: int
    n_incomplete: int
    share_identical: float
    max_relative_spread: float


def compute_agreement(
    measurements: Sequence[FileMeasurement], models: Sequence[str], *, scope: str
) -> AgreementStats:
    """Group per-model measurements by ``(project, path)`` and score agreement.

    Args:
        measurements: Any mix of per-model measurements (e.g. one project's,
            or the whole corpus's).
        models: The models a file must have a count from to be "complete".
        scope: A label for the resulting :class:`AgreementStats` (a project
            slug, or ``"overall"``).
    """
    by_file: dict[tuple[str, str], dict[str, int]] = {}
    for measurement in measurements:
        by_file.setdefault((measurement.project, measurement.path), {})[
            measurement.model
        ] = measurement.claude

    required = set(models)
    complete: list[dict[str, int]] = []
    n_incomplete = 0
    for counts in by_file.values():
        if required.issubset(counts.keys()):
            complete.append(counts)
        else:
            n_incomplete += 1

    if not complete:
        return AgreementStats(
            scope=scope,
            models=tuple(models),
            n_complete=0,
            n_incomplete=n_incomplete,
            share_identical=0.0,
            max_relative_spread=0.0,
        )

    identical = 0
    max_spread = 0.0
    for counts in complete:
        values = [counts[model] for model in models]
        if len(set(values)) == 1:
            identical += 1
        lo, hi = min(values), max(values)
        spread = 0.0 if lo == 0 else (hi - lo) / lo
        max_spread = max(max_spread, spread)

    return AgreementStats(
        scope=scope,
        models=tuple(models),
        n_complete=len(complete),
        n_incomplete=n_incomplete,
        share_identical=identical / len(complete),
        max_relative_spread=max_spread,
    )


@dataclass(frozen=True)
class DriftStats:
    """Drift between a baseline (prior single-model) survey and a fresh recount."""

    scope: str
    model: str
    n_matched: int
    n_unmatched_baseline: int
    n_unmatched_new: int
    n_identical: int
    max_abs_diff: int
    max_rel_diff: float
    mean_abs_diff: float


def compare_to_baseline(
    baseline_counts_by_path: Mapping[str, int],
    new_measurements: Sequence[FileMeasurement],
    *,
    scope: str,
    model: str,
) -> DriftStats:
    """Compare a baseline ``{path: claude_tokens}`` map to a fresh recount.

    Only ``new_measurements`` counted by ``model`` are considered (a
    multi-model measurement list is filtered internally), matched to the
    baseline by ``path``. This is an endpoint-stability receipt: the same
    file, same model, counted on a different day, should not drift.
    """
    new_by_path = {
        measurement.path: measurement.claude
        for measurement in new_measurements
        if measurement.model == model
    }
    baseline_paths = set(baseline_counts_by_path)
    new_paths = set(new_by_path)
    matched = baseline_paths & new_paths

    if not matched:
        return DriftStats(
            scope=scope,
            model=model,
            n_matched=0,
            n_unmatched_baseline=len(baseline_paths - new_paths),
            n_unmatched_new=len(new_paths - baseline_paths),
            n_identical=0,
            max_abs_diff=0,
            max_rel_diff=0.0,
            mean_abs_diff=0.0,
        )

    abs_diffs: list[int] = []
    rel_diffs: list[float] = []
    identical = 0
    for path in matched:
        old = baseline_counts_by_path[path]
        new = new_by_path[path]
        diff = abs(new - old)
        abs_diffs.append(diff)
        rel_diffs.append(0.0 if old == 0 else diff / old)
        if diff == 0:
            identical += 1

    return DriftStats(
        scope=scope,
        model=model,
        n_matched=len(matched),
        n_unmatched_baseline=len(baseline_paths - new_paths),
        n_unmatched_new=len(new_paths - baseline_paths),
        n_identical=identical,
        max_abs_diff=max(abs_diffs),
        max_rel_diff=max(rel_diffs),
        mean_abs_diff=statistics.fmean(abs_diffs),
    )


def load_baseline_claude_counts(jsonl_path: Path) -> dict[str, int] | None:
    """Load ``{path: claude_tokens}`` from a legacy single-model survey JSONL.

    Returns:
        ``None`` if ``jsonl_path`` does not exist (baseline comparison is
        optional — the first-ever run has nothing to compare against).
    """
    if not jsonl_path.is_file():
        return None
    counts: dict[str, int] = {}
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        counts[row["path"]] = int(row["claude"])
    return counts


# --------------------------------------------------------------------------- #
# Live token counting (network surface — test-exempt)
# --------------------------------------------------------------------------- #
def load_api_key(env_file: Path = DEFAULT_ENV_FILE) -> str:
    """Resolve the Anthropic API key from the environment or the operator env file.

    The key is never logged, printed, or copied.  Prefers an already-exported
    ``ANTHROPIC_API_KEY``; otherwise parses it out of ``env_file``.

    Raises:
        RuntimeError: If no key can be found.
    """
    from_env = os.environ.get(ANTHROPIC_API_KEY_ENV)
    if from_env:
        return from_env.strip()
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{ANTHROPIC_API_KEY_ENV}="):
                value = stripped.split("=", 1)[1].strip().strip("'\"")
                if value:
                    return value
    raise RuntimeError(
        f"{ANTHROPIC_API_KEY_ENV} not set and not found in {env_file}"
    )


class ClaudeTokenCounter:
    """Counts Claude tokens for a text via the Anthropic ``count_tokens`` endpoint.

    Retries on 429/5xx with exponential backoff, honouring a ``Retry-After``
    header when present.  On persistent failure the caller records the file as
    failed and continues (the survey never aborts on a single bad file).
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str = ANTHROPIC_MODEL,
        client: httpx.Client | None = None,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self._model = model
        self._max_retries = max_retries
        self._headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        # Track ownership so a client shared across several per-model counters
        # (see MultiModelClaudeCounter) is only closed once, by its owner.
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=60.0)

    @property
    def model(self) -> str:
        return self._model

    def count(self, text: str) -> int:
        """Return the Claude ``input_tokens`` for ``text``.

        Raises:
            RuntimeError: If the endpoint keeps failing past ``max_retries``.
        """
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": text}],
        }
        last_error: str = ""
        for attempt in range(self._max_retries):
            try:
                response = self._client.post(
                    ANTHROPIC_COUNT_TOKENS_URL, headers=self._headers, json=payload
                )
            except httpx.HTTPError as exc:
                last_error = f"transport:{type(exc).__name__}"
                self._sleep_backoff(attempt, None)
                continue
            if response.status_code == 200:
                return int(response.json()["input_tokens"])
            if response.status_code == 429 or response.status_code >= 500:
                last_error = f"http:{response.status_code}"
                self._sleep_backoff(attempt, response.headers.get("retry-after"))
                continue
            # 4xx other than 429 are not retryable (bad request / auth).
            raise RuntimeError(
                f"count_tokens failed ({response.status_code}): {response.text[:200]}"
            )
        raise RuntimeError(f"count_tokens exhausted retries ({last_error})")

    @staticmethod
    def _sleep_backoff(attempt: int, retry_after: str | None) -> None:
        """Sleep before a retry, honouring ``Retry-After`` when the server sets it."""
        if retry_after is not None:
            try:
                time.sleep(min(float(retry_after), RETRY_MAX_DELAY_S))
                return
            except ValueError:
                pass
        delay = min(RETRY_BASE_DELAY_S * (2**attempt), RETRY_MAX_DELAY_S)
        time.sleep(delay)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


class MultiModelClaudeCounter:
    """One :class:`ClaudeTokenCounter` per model, sharing a single ``httpx.Client``.

    Answers the yardstick question directly: for the *same text*, does the
    Claude token count depend on which model is asked? A shared HTTP client
    keeps connection pooling working across models; per-file counting still
    goes through one model at a time (see ``SurveyRunner``), so at most
    ``MAX_CONCURRENCY`` requests are ever in flight regardless of model count.
    """

    def __init__(
        self, api_key: str, models: Sequence[str], *, max_retries: int = MAX_RETRIES
    ) -> None:
        self._client = httpx.Client(timeout=60.0)
        self._counters: dict[str, ClaudeTokenCounter] = {
            model: ClaudeTokenCounter(
                api_key, model=model, client=self._client, max_retries=max_retries
            )
            for model in models
        }

    @property
    def models(self) -> tuple[str, ...]:
        """The models still active (probed OK and not yet dropped), in order."""
        return tuple(self._counters.keys())

    def count(self, text: str, model: str) -> int:
        """Return the Claude ``input_tokens`` for ``text`` under ``model``."""
        return self._counters[model].count(text)

    def probe(self, probe_text: str = "ping") -> dict[str, str | None]:
        """Attempt one trivial count per model; ``None`` on success, else the
        verbatim error message — never raises, so a bad model never aborts the
        others' probes.
        """
        results: dict[str, str | None] = {}
        for model, counter in self._counters.items():
            try:
                counter.count(probe_text)
                results[model] = None
            except RuntimeError as exc:
                results[model] = str(exc)
        return results

    def drop(self, model: str) -> None:
        """Remove ``model`` from future counting (e.g. after a failed probe)."""
        self._counters.pop(model, None)

    def close(self) -> None:
        self._client.close()


# --------------------------------------------------------------------------- #
# Survey orchestration
# --------------------------------------------------------------------------- #
@dataclass
class ProjectResult:
    """Everything the survey produced for one project."""

    slug: str
    note: str
    discovered: int
    sampled: int
    measurements: list[FileMeasurement] = field(default_factory=list)
    discovery_skips: list[SkipRecord] = field(default_factory=list)
    count_skips: list[SkipRecord] = field(default_factory=list)
    failures: list[SkipRecord] = field(default_factory=list)


class SurveyRunner:
    """Runs the sample-and-count survey for one project, writing JSONL as it goes."""

    def __init__(
        self,
        claude_counter: MultiModelClaudeCounter,
        voyage_counter: VoyageTokenCounter,
        jsonl_path: Path,
        *,
        fraction: float = DEFAULT_FRACTION,
        seed: int = DEFAULT_SEED,
        concurrency: int = MAX_CONCURRENCY,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self._claude = claude_counter
        self._models = claude_counter.models
        self._voyage = voyage_counter
        self._jsonl_path = jsonl_path
        self._fraction = fraction
        self._seed = seed
        self._concurrency = concurrency
        self._progress = progress_callback
        self._write_lock = Lock()
        self._counter_lock = Lock()

    def run(self, spec: ProjectSpec) -> ProjectResult:
        """Discover, sample, and count one project (every active model, per file)."""
        entries, discovery_skips = FileDiscovery(spec).discover()
        strata = stratify(entries)
        sample = sample_stratified(strata, self._fraction, self._seed)
        result = ProjectResult(
            slug=spec.slug,
            note=spec.note,
            discovered=len(entries),
            sampled=len(sample),
            discovery_skips=discovery_skips,
        )

        done = 0
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self._concurrency
        ) as pool:
            futures = {
                pool.submit(self._measure_one, spec.slug, entry): entry
                for entry in sample
            }
            # Progress is counted per FILE, not per (file, model) outcome — a
            # 3-model run still reports "counted 200/933" in file terms.
            for future in concurrent.futures.as_completed(futures):
                outcomes = future.result()
                for outcome in outcomes:
                    if isinstance(outcome, FileMeasurement):
                        result.measurements.append(outcome)
                        self._write_row(outcome)
                    elif outcome.reason.startswith("failed"):
                        result.failures.append(outcome)
                    else:
                        result.count_skips.append(outcome)
                done += 1
                if self._progress and done % PROGRESS_EVERY == 0:
                    self._progress(spec.slug, done, len(sample))

        result.measurements.sort(key=lambda measurement: (measurement.path, measurement.model))
        if self._progress:
            self._progress(spec.slug, done, len(sample))
        return result

    def _measure_one(
        self, slug: str, entry: FileEntry
    ) -> list["FileMeasurement | SkipRecord"]:  # noqa: UP037 -- unquoting would drop
        # this string from the ast.Constant set this pinned survey tool's byte-
        # identity receipt walks; kept quoted deliberately (see F841/UP037 note
        # in the lint-cleanup report).
        """Count one file in Voyage currency once, then every active model (worker thread).

        Concurrency is bounded per file, not per (file, model) call: this
        worker thread holds at most one in-flight HTTP request at a time (the
        loop over models is sequential), so the pool's ``max_workers`` bounds
        total concurrent Anthropic calls across every model, not just per model.
        """
        try:
            text = entry.path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            return [SkipRecord(entry.relpath, f"binary_or_unreadable:{type(exc).__name__}")]
        if not text.strip():
            return [SkipRecord(entry.relpath, "empty:whitespace-only")]
        with self._counter_lock:
            voyage = self._voyage.count(text)
        if voyage <= 0:
            return [SkipRecord(entry.relpath, "empty:zero-voyage-tokens")]

        outcomes: list["FileMeasurement | SkipRecord"] = []  # noqa: UP037 -- see note above
        for model in self._models:
            try:
                claude = self._claude.count(text, model)
            except RuntimeError as exc:
                outcomes.append(SkipRecord(entry.relpath, f"failed:{model}:{exc}"))
                continue
            outcomes.append(
                FileMeasurement(
                    project=slug,
                    path=entry.relpath,
                    ext=entry.ext,
                    bytes=entry.size_bytes,
                    voyage=voyage,
                    claude=claude,
                    model=model,
                )
            )
        return outcomes

    def _write_row(self, measurement: FileMeasurement) -> None:
        """Append one JSONL row (thread-safe)."""
        with self._write_lock:
            with self._jsonl_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(measurement.to_row()) + "\n")


# --------------------------------------------------------------------------- #
# Project specs + manifest handling
# --------------------------------------------------------------------------- #
LORE_ROOT = Path.home() / "PycharmProjects" / "lore"
ODOO_ROOT = Path.home() / "PycharmProjects" / "pp-odoo" / "odoo15"
DI_ROOT = Path.home() / "PycharmProjects" / "pp-odoo" / "demand_intelligence"

STANDARD_EXCLUDES: tuple[str, ...] = (
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
)


def lore_spec() -> ProjectSpec:
    """The lore monorepo: ``**/*.py`` + ``**/*.md`` honouring lore.yaml excludes."""
    return ProjectSpec(
        slug="lore",
        root=LORE_ROOT,
        include_exts=(".py", ".md"),
        exclude_dir_patterns=(".git", ".venv", "__pycache__", ".pytest_cache", ".claude", "data"),
        follow_symlinks=False,
        note="lore.yaml exclude_dirs honoured; **/*.py + **/*.md.",
    )


def odoo_spec() -> ProjectSpec:
    """The Odoo 15 tree: ``**/*.py`` excluding git-worktree duplicates.

    ``odoo/``, ``enterprise/`` and ``addons/`` are symlinks into the vendor
    sources, so symlink-following is enabled to survey the real corpus.  The
    ``odoo-custom-wt-*`` git worktrees are near-exact duplicates of
    ``odoo-custom`` and are excluded to avoid double-counting the same code.
    """
    return ProjectSpec(
        slug="odoo",
        root=ODOO_ROOT,
        include_exts=(".py",),
        exclude_dir_patterns=STANDARD_EXCLUDES + ("odoo-custom-wt-*",),
        follow_symlinks=True,
        note="Symlinked vendor sources followed; odoo-custom-wt-* worktrees excluded.",
    )


def di_spec_from_manifest(manifest_path: Path) -> ProjectSpec | None:
    """Build the DI spec from the curated manifest, or ``None`` if absent.

    The manifest is authored by a separate agent (curated file selection); we
    never guess DI's strata.  Expected shape::

        {"include_globs": ["src/**/*.py", ...],
         "exclude_dirs": ["lightning_logs", ...],
         "notes": "..."}

    ``include_globs`` are reduced to their distinct extensions (the discovery
    walk globs by extension); ``exclude_dirs`` become directory-prune patterns.
    """
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    include_globs = manifest.get("include_globs", [])
    exts = sorted({Path(glob).suffix.lower() for glob in include_globs if Path(glob).suffix})
    if not exts:
        exts = [".py"]
    exclude_dirs = tuple(manifest.get("exclude_dirs", [])) + STANDARD_EXCLUDES
    return ProjectSpec(
        slug="di",
        root=DI_ROOT,
        include_exts=tuple(exts),
        exclude_dir_patterns=exclude_dirs,
        follow_symlinks=False,
        note=f"From manifest: {manifest.get('notes', '(no notes)')}",
    )


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def _fmt(value: float) -> str:
    return f"{value:.4f}"


def build_markdown_summary(
    project_summaries: dict[str, RatioSummary],
    ext_summaries: dict[str, dict[str, RatioSummary]],
    overall: RatioSummary,
    ceiling: float,
    results: dict[str, ProjectResult],
) -> str:
    """Render the human-readable markdown summary (per project, per ext, overall)."""
    lines: list[str] = ["# Token-Calibration Survey — Summary", ""]

    lines.append("## Recommended ceiling")
    lines.append("")
    lines.append(
        f"**CLAUDE_PER_VOYAGE_CEILING = {ceiling:.2f}** "
        "— max over surveyed projects of each project's token-weighted p95 ratio, "
        "rounded up to 2 decimals."
    )
    lines.append("")
    lines.append("Per-project token-weighted p95 (the inputs to the max):")
    lines.append("")
    for slug, summary in project_summaries.items():
        lines.append(f"- `{slug}`: {_fmt(summary.token_weighted_p95)}")
    lines.append("")

    header = (
        "| scope | N | voyage tok | claude tok | tok-wt ratio | "
        "file mean | file median | file p5 | file p95 | file max | tok-wt p95 |"
    )
    divider = "|" + "|".join(["---"] * 11) + "|"

    def row(name: str, summary: RatioSummary) -> str:
        return (
            f"| {name} | {summary.n} | {summary.total_voyage} | {summary.total_claude} "
            f"| {_fmt(summary.token_weighted_ratio)} | {_fmt(summary.file_mean)} "
            f"| {_fmt(summary.file_median)} | {_fmt(summary.file_p5)} "
            f"| {_fmt(summary.file_p95)} | {_fmt(summary.file_max)} "
            f"| {_fmt(summary.token_weighted_p95)} |"
        )

    lines.append("## Per project")
    lines.append("")
    lines.append(header)
    lines.append(divider)
    for slug, summary in project_summaries.items():
        lines.append(row(slug, summary))
    lines.append(row("**overall**", overall))
    lines.append("")

    lines.append("## Per extension (within project)")
    lines.append("")
    lines.append(header)
    lines.append(divider)
    for slug, per_ext in ext_summaries.items():
        for ext, summary in per_ext.items():
            lines.append(row(f"{slug} {ext}", summary))
    lines.append("")

    lines.append("## Discovery / skip / failure counts")
    lines.append("")
    lines.append("| project | discovered | sampled | measured | disc-skips | count-skips | failures |")
    lines.append("|---|---|---|---|---|---|---|")
    for slug, result in results.items():
        lines.append(
            f"| {slug} | {result.discovered} | {result.sampled} "
            f"| {len(result.measurements)} | {len(result.discovery_skips)} "
            f"| {len(result.count_skips)} | {len(result.failures)} |"
        )
    lines.append("")
    return "\n".join(lines)


def per_extension_summaries(
    measurements: Sequence[FileMeasurement],
) -> dict[str, RatioSummary]:
    """Summaries grouped by extension for one project's measurements."""
    by_ext: dict[str, list[FileMeasurement]] = {}
    for measurement in measurements:
        by_ext.setdefault(measurement.ext, []).append(measurement)
    return {
        ext: summarize(group, label=ext)
        for ext, group in sorted(by_ext.items())
    }


def _project_result_for_model(result: ProjectResult, model: str) -> ProjectResult:
    """A single-model view of a multi-model :class:`ProjectResult`.

    Discovery/sampling counts are model-independent (shared); file-level count
    skips (binary, empty, zero-voyage) occur once per file before the
    per-model loop and are likewise shared. Only ``measurements`` and
    ``failures`` are per-model and need filtering — this lets each model's
    section reuse :func:`build_markdown_summary` unchanged.
    """
    failed_prefix = f"failed:{model}:"
    return ProjectResult(
        slug=result.slug,
        note=result.note,
        discovered=result.discovered,
        sampled=result.sampled,
        measurements=filter_by_model(result.measurements, model),
        discovery_skips=result.discovery_skips,
        count_skips=result.count_skips,
        failures=[f for f in result.failures if f.reason.startswith(failed_prefix)],
    )


def build_yardstick_markdown(  # noqa: PLR0912, PLR0915 - committed survey instrument, deliberately linear
    requested_models: Sequence[str],
    active_models: Sequence[str],
    dropped_models: Sequence[tuple[str, str]],
    project_summaries_by_model: dict[str, dict[str, RatioSummary]],
    ext_summaries_by_model: dict[str, dict[str, dict[str, RatioSummary]]],
    overall_by_model: dict[str, RatioSummary],
    ceiling_by_model: dict[str, float],
    comparisons: Sequence[CrossModelComparison],
    agreement_overall: AgreementStats,
    agreement_by_project: dict[str, AgreementStats],
    drifts: Sequence[DriftStats],
    results: dict[str, ProjectResult],
) -> str:
    """Render the cross-model yardstick report: does the model matter?

    Structure: model availability -> per-model recommended ceilings -> the
    cross-model delta table (the operator's actual question) -> per-file
    agreement -> the sonnet-5 endpoint-stability receipt -> full per-model
    detail (each reusing :func:`build_markdown_summary` unchanged).
    """
    lines: list[str] = ["# Token-Calibration Yardstick Survey — Cross-Model Summary", ""]

    lines.append("## Models")
    lines.append("")
    lines.append(f"- Requested: {', '.join(requested_models)}")
    lines.append(f"- Active (survived probe): {', '.join(active_models) or '(none)'}")
    if dropped_models:
        lines.append("- Dropped (probe failed — verbatim error):")
        for model, error in dropped_models:
            lines.append(f"  - `{model}`: {error}")
    lines.append("")

    lines.append("## Recommended ceiling, per model")
    lines.append("")
    lines.append("| model | ceiling |")
    lines.append("|---|---|")
    for model in active_models:
        if model in ceiling_by_model:
            lines.append(f"| {model} | {ceiling_by_model[model]:.2f} |")
    lines.append("")
    if len(ceiling_by_model) >= 2:
        lines.append(
            f"Max pairwise relative delta across per-model ceilings: "
            f"{max_pairwise_relative_delta(ceiling_by_model) * 100:.2f}%"
        )
        lines.append("")

    lines.append("## Cross-model comparison (max pairwise relative delta)")
    lines.append("")
    lines.append("| scope | models | Δ total-claude | Δ tok-wt ratio | Δ ceiling-input |")
    lines.append("|---|---|---|---|---|")
    if comparisons:
        for comparison in comparisons:
            lines.append(
                f"| {comparison.scope} | {', '.join(comparison.models)} "
                f"| {comparison.max_delta_total_claude * 100:.3f}% "
                f"| {comparison.max_delta_ratio * 100:.3f}% "
                f"| {comparison.max_delta_ceiling * 100:.3f}% |"
            )
    else:
        lines.append("| (fewer than two active models — no comparison possible) | | | | |")
    lines.append("")
    lines.append(
        "`ceiling-input` = each project's own token-weighted p95; for the "
        "`overall` row it is the actual recommended ceiling (max p95 across "
        "projects), per model."
    )
    lines.append("")

    lines.append("## Per-file agreement (share of files where ALL active models count IDENTICALLY)")
    lines.append("")
    lines.append("| scope | n complete | n incomplete | share identical | max relative spread |")
    lines.append("|---|---|---|---|---|")
    lines.append(
        f"| overall | {agreement_overall.n_complete} | {agreement_overall.n_incomplete} "
        f"| {agreement_overall.share_identical * 100:.2f}% "
        f"| {agreement_overall.max_relative_spread * 100:.3f}% |"
    )
    for slug, stats in agreement_by_project.items():
        lines.append(
            f"| {slug} | {stats.n_complete} | {stats.n_incomplete} "
            f"| {stats.share_identical * 100:.2f}% | {stats.max_relative_spread * 100:.3f}% |"
        )
    lines.append("")

    if drifts:
        lines.append(f"## Endpoint-stability receipt ({ANTHROPIC_MODEL} vs prior single-model survey)")
        lines.append("")
        lines.append(
            "| project | matched | unmatched (baseline-only) | unmatched (new-only) "
            "| identical | max abs diff | max rel diff | mean abs diff |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for drift in drifts:
            lines.append(
                f"| {drift.scope} | {drift.n_matched} | {drift.n_unmatched_baseline} "
                f"| {drift.n_unmatched_new} | {drift.n_identical} | {drift.max_abs_diff} "
                f"| {drift.max_rel_diff * 100:.3f}% | {_fmt(drift.mean_abs_diff)} |"
            )
        lines.append("")

    lines.append("## Per-model detail")
    lines.append("")
    for model in active_models:
        if model not in project_summaries_by_model:
            lines.append(f"### {model}")
            lines.append("")
            lines.append("(no measurements — every file failed for this model)")
            lines.append("")
            continue
        lines.append(f"### {model}")
        lines.append("")
        per_model_results = {
            slug: _project_result_for_model(result, model) for slug, result in results.items()
        }
        model_markdown = build_markdown_summary(
            project_summaries_by_model[model],
            ext_summaries_by_model[model],
            overall_by_model[model],
            ceiling_by_model[model],
            per_model_results,
        )
        # Demote: this per-model report owns its own H1, but only the
        # yardstick report as a whole should have one.
        model_lines = model_markdown.splitlines()
        if model_lines and model_lines[0].startswith("# "):
            model_lines = model_lines[1:]
        lines.extend(model_lines)
        lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _default_output_dir() -> Path:
    scratch = os.environ.get("TOKEN_SURVEY_OUT")
    if scratch:
        return Path(scratch)
    return Path.cwd() / "token_survey_out"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Token-calibration survey (voyage vs claude).")
    parser.add_argument("--fraction", type=float, default=DEFAULT_FRACTION)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--concurrency", type=int, default=MAX_CONCURRENCY)
    parser.add_argument("--out-dir", type=Path, default=_default_output_dir())
    parser.add_argument(
        "--projects",
        nargs="+",
        default=["lore", "odoo", "di"],
        help="Subset of {lore, odoo, di} to survey.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to the DI curated manifest (default: <out-dir>/di_manifest.json).",
    )
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument(
        "--progress-file",
        type=Path,
        default=None,
        help="Append progress lines to this file (e.g. REPORT-calib-tool.md).",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=list(DEFAULT_MODELS),
        help="Claude models to count against (the yardstick question).",
    )
    parser.add_argument(
        "--jsonl-prefix",
        default="survey",
        help="Filename prefix for this run's per-file JSONL (avoid clobbering a prior run's).",
    )
    parser.add_argument(
        "--summary-filename",
        default="survey_summary.md",
        help="Filename for the markdown summary (avoid clobbering a prior run's).",
    )
    parser.add_argument(
        "--baseline-prefix",
        default="survey",
        help=(
            "Filename prefix of a prior single-model run's JSONL, used only for the "
            f"{ANTHROPIC_MODEL} endpoint-stability drift receipt (skipped if absent)."
        ),
    )
    return parser


def resolve_specs(requested: Sequence[str], manifest_path: Path) -> tuple[list[ProjectSpec], list[str]]:
    """Resolve requested project slugs into specs, reporting any skipped."""
    specs: list[ProjectSpec] = []
    notices: list[str] = []
    for slug in requested:
        if slug == "lore":
            specs.append(lore_spec())
        elif slug == "odoo":
            specs.append(odoo_spec())
        elif slug == "di":
            di = di_spec_from_manifest(manifest_path)
            if di is None:
                notices.append(
                    f"SKIP di: manifest not found at {manifest_path} "
                    "(curated selection required — strata never guessed)."
                )
            else:
                specs.append(di)
        else:
            notices.append(f"SKIP {slug}: unknown project slug.")
    return specs, notices


def main(argv: Sequence[str] | None = None) -> int:  # noqa: PLR0912, PLR0915 - survey instrument, linear
    args = build_arg_parser().parse_args(argv)
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve the DI manifest relative to the *actual* out-dir when not given
    # explicitly, so --out-dir and the manifest never drift apart.
    manifest_path: Path = args.manifest or (out_dir / "di_manifest.json")
    specs, notices = resolve_specs(args.projects, manifest_path)
    for notice in notices:
        print(notice, file=sys.stderr)
    if not specs:
        print("No projects to survey.", file=sys.stderr)
        return 1

    api_key = load_api_key(args.env_file)
    voyage_counter = VoyageTokenCounter()

    def progress(slug: str, done: int, total: int) -> None:
        message = f"[{slug}] counted {done}/{total}"
        print(message, file=sys.stderr)
        if args.progress_file is not None:
            with args.progress_file.open("a", encoding="utf-8") as handle:
                handle.write(f"- {message}\n")

    def note(message: str) -> None:
        print(message, file=sys.stderr)
        if args.progress_file is not None:
            with args.progress_file.open("a", encoding="utf-8") as handle:
                handle.write(f"- {message}\n")

    claude = MultiModelClaudeCounter(api_key, args.models, max_retries=MAX_RETRIES)
    probe_results = claude.probe()
    active_models, dropped_models = resolve_available_models(probe_results)
    for model, error in dropped_models:
        note(f"MODEL DROPPED (probe failed): {model}: {error}")
        claude.drop(model)
    if not active_models:
        print("No models survived the probe.", file=sys.stderr)
        claude.close()
        return 1
    note(f"Active models: {', '.join(active_models)}")

    results: dict[str, ProjectResult] = {}
    all_measurements: list[FileMeasurement] = []

    try:
        for spec in specs:
            jsonl_path = out_dir / f"{args.jsonl_prefix}_{spec.slug}.jsonl"
            jsonl_path.write_text("", encoding="utf-8")  # fresh, deterministic run
            runner = SurveyRunner(
                claude,
                voyage_counter,
                jsonl_path,
                fraction=args.fraction,
                seed=args.seed,
                concurrency=args.concurrency,
                progress_callback=progress,
            )
            result = runner.run(spec)
            results[spec.slug] = result
            all_measurements.extend(result.measurements)
            print(
                f"[{spec.slug}] discovered={result.discovered} sampled={result.sampled} "
                f"measured={len(result.measurements)} skips={len(result.count_skips)} "
                f"failures={len(result.failures)}",
                file=sys.stderr,
            )
    finally:
        claude.close()

    if not all_measurements:
        print("No measurements produced.", file=sys.stderr)
        return 1

    # --- Per-model stats -------------------------------------------------- #
    project_summaries_by_model: dict[str, dict[str, RatioSummary]] = {}
    ext_summaries_by_model: dict[str, dict[str, dict[str, RatioSummary]]] = {}
    overall_by_model: dict[str, RatioSummary] = {}
    ceiling_by_model: dict[str, float] = {}

    for model in active_models:
        per_project: dict[str, RatioSummary] = {}
        per_ext: dict[str, dict[str, RatioSummary]] = {}
        for spec in specs:
            model_measurements = filter_by_model(results[spec.slug].measurements, model)
            if model_measurements:
                per_project[spec.slug] = summarize(model_measurements, label=f"{spec.slug}:{model}")
                per_ext[spec.slug] = per_extension_summaries(model_measurements)
        if per_project:
            project_summaries_by_model[model] = per_project
            ext_summaries_by_model[model] = per_ext
            overall_by_model[model] = summarize(
                filter_by_model(all_measurements, model), label=f"overall:{model}"
            )
            ceiling_by_model[model] = recommended_ceiling(list(per_project.values()))

    models_with_data = [m for m in active_models if m in project_summaries_by_model]
    if not models_with_data:
        print("No model produced any measurements.", file=sys.stderr)
        return 1

    # --- Cross-model comparison -------------------------------------------- #
    comparisons: list[CrossModelComparison] = []
    for spec in specs:
        slug = spec.slug
        models_here = [m for m in models_with_data if slug in project_summaries_by_model[m]]
        if len(models_here) >= 2:
            comparisons.append(
                compare_models(
                    slug,
                    {m: project_summaries_by_model[m][slug].total_claude for m in models_here},
                    {m: project_summaries_by_model[m][slug].token_weighted_ratio for m in models_here},
                    {m: project_summaries_by_model[m][slug].token_weighted_p95 for m in models_here},
                )
            )
    if len(models_with_data) >= 2:
        comparisons.append(
            compare_models(
                "overall",
                {m: overall_by_model[m].total_claude for m in models_with_data},
                {m: overall_by_model[m].token_weighted_ratio for m in models_with_data},
                # The "overall" ceiling-input is the ACTUAL derived ceiling
                # (max p95 across projects), not a pooled p95 — it is the tool's
                # real output, so its cross-model delta is the one that matters.
                dict(ceiling_by_model),
            )
        )

    # --- Per-file agreement -------------------------------------------------#
    agreement_overall = compute_agreement(all_measurements, models_with_data, scope="overall")
    agreement_by_project = {
        spec.slug: compute_agreement(results[spec.slug].measurements, models_with_data, scope=spec.slug)
        for spec in specs
    }

    # --- Endpoint-stability receipt (sonnet-5 vs the prior single-model run) #
    drifts: list[DriftStats] = []
    if ANTHROPIC_MODEL in models_with_data:
        for spec in specs:
            baseline_path = out_dir / f"{args.baseline_prefix}_{spec.slug}.jsonl"
            baseline_counts = load_baseline_claude_counts(baseline_path)
            if baseline_counts is not None:
                new_for_model = filter_by_model(results[spec.slug].measurements, ANTHROPIC_MODEL)
                drifts.append(
                    compare_to_baseline(
                        baseline_counts, new_for_model, scope=spec.slug, model=ANTHROPIC_MODEL
                    )
                )

    markdown = build_yardstick_markdown(
        args.models,
        models_with_data,
        dropped_models,
        project_summaries_by_model,
        ext_summaries_by_model,
        overall_by_model,
        ceiling_by_model,
        comparisons,
        agreement_overall,
        agreement_by_project,
        drifts,
        results,
    )
    summary_path = out_dir / args.summary_filename
    summary_path.write_text(markdown, encoding="utf-8")
    print(f"Summary written to {summary_path}", file=sys.stderr)
    for model in models_with_data:
        print(f"Recommended ceiling [{model}]: {ceiling_by_model[model]:.2f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
