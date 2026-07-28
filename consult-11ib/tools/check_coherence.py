"""Audit the honest exhibit package for arithmetic coherence and sentinel implausibility.

The exhibit rules say every value must be arithmetically COHERENT (so each keyed question has
exactly one right answer) and magnitude-IMPLAUSIBLE (so no value can be quoted as a real lore
measurement). Both properties are checked here rather than claimed in a report, because a claim
about arithmetic that nothing re-derives is exactly the kind of prose this repo keeps catching.

Two independent legs:

1. **Presence** — every number this script reasons about is asserted to appear, as text, in the
   exhibit file that is supposed to carry it. Without this leg the script is a private twin of
   the exhibit and drifts from it silently.
2. **Relations** — the sums, differences, rates, percentile brackets and gate verdicts are
   re-derived and compared.

Plus the implausibility leg: every INDEPENDENTLY CHOSEN real value must be a two-digit repunit
(``0.ababab``) or an ascending digit run (``0.123456``-shape). Derived values are exempt by
definition — they are whatever the arithmetic makes them.

**REACH — stated because a gate is an invariant only over what it actually inspects.**

- **Positionally checked, cell by cell** (a value moved between cells is caught): every stats
  row, delta row, width line and cross-group row in ``02``; both tables in ``03``; the
  decomposition and per-hit rows in ``06``.
- **Schema- and predicate-checked, row by row:** ``per-query-rows.jsonl`` — every row's field
  set, its hit capture's depth and monotonicity, its ``shown`` flags against ``SURVEY_K``, its
  ``absence_verdict_fired`` against the anchor-gated predicate, and every cosine against the
  sentinel rule. **This leg was ABSENT until 2026-07-28 and its absence was a real hole:** an
  adversary truncated the file to one row and corrupted it four ways, and this script — whose
  reach statement did not mention the file at all — exited 0.
- **Presence-only** (a duplicate elsewhere in the same file can mask an edit — MEASURED, see
  :meth:`Auditor.present`): the tables in ``01``, ``05``, ``07`` and ``08``.
- **Not checked at all: the PROSE.** This is the load-bearing limit. Every falsehood an
  adversary planted in this package's sentences — an inverted scope bound, a stability claim
  over an n = 15 pool, an instruction to render stored free text unsanitised, an assertion that
  two instruments' cosines are commensurable — passed this script with exit 0. **Arithmetic
  coherence is not honesty**, and no extension of this script gets there; that is what the
  consult battery's keys are for.

Silent on success, loud on failure; non-zero exit on any violation.

Run: ``python consult-11ib/tools/check_coherence.py consult-11ib/honest``
"""

from __future__ import annotations

import json
import re
import sys
from decimal import Decimal
from pathlib import Path

FLOOR_LEGACY = Decimal("0.345678")
FLOOR_PORTABLE = Decimal("0.456789")
HEADLINE_DELTA = Decimal("0.111111")

#: Totals the exhibit states. Named rather than inlined so a violation message says WHICH
#: quantity disagreed, and so the script reads as a declaration of the package's claims.
TOTAL_QUERIES = 1740
BELOW_FLOOR_TOTAL = 815
ANCHORED_BELOW_TOTAL = 39
FIRED_TOTAL = 776
ANSWERED_QUERIES = 964
REAL_UNION_N = 357
REAL_UNION_BELOW = 23
REAL_UNION_FALSE_FIRES = 11
ANCHORED_TOTAL = 407
NONSENSE_N = 345
NONSENSE_BELOW = 324
NONSENSE_CAUGHT = 321
DROP_TOTAL = 45
ADOPTED_N = 411
ABSENT_LEG_DROPS = 34
ABSENT_SAMPLES = 533
SHOWN_K = 10
SHOWN_HITS = 9640
HITS_BELOW_FLOOR = 3456
MIDLIST_BELOW_FLOOR = 3417
MIDLIST_DENOMINATOR = 8676
EMBED_BUDGET = 34567
EMBEDS_USED = 23456
EMBED_REMAINING = 11111
AGREEMENT_NUMERATOR = 1739
FALSE_FIRE_BAR = Decimal("0.05")
CATCH_BAR = Decimal("0.60")
DROP_GATE = Decimal("0.20")
AGREEMENT_BAR = Decimal("0.98")
F2_CALIBRATED_GAP = Decimal("0.010101")
OBSERVED_FLOOR_DRIFT = Decimal("0.000012")

#: ``group -> (n, legacy stats, portable stats)`` where stats are
#: ``(min, p5, p25, median, p75, p95, max, mean)``. Read off ``02``.
GROUPS: dict[str, tuple[int, tuple[str, ...], tuple[str, ...]]] = {
    "human-prose": (
        123,
        ("0.313131", "0.373737", "0.454545", "0.535353", "0.616161", "0.696969", "0.777777", "0.525252"),
        ("0.333333", "0.404040", "0.494949", "0.646464", "0.757575", "0.888888", "0.939393", "0.636363"),
    ),
    "human-implementation-vocabulary": (
        234,
        ("0.474747", "0.494949", "0.515151", "0.535353", "0.555555", "0.575757", "0.595959", "0.535353"),
        ("0.414141", "0.464646", "0.606060", "0.646464", "0.686868", "0.727272", "0.767676", "0.646464"),
    ),
    "synthesized-identifier": (
        15,
        ("0.606060", "0.616161", "0.636363", "0.666666", "0.696969", "0.717171", "0.737373", "0.666666"),
        ("0.646464", "0.656565", "0.686868", "0.727272", "0.767676", "0.797979", "0.818181", "0.727272"),
    ),
    "self-supervised-answered": (
        456,
        ("0.353535", "0.424242", "0.505050", "0.575757", "0.646464", "0.727272", "0.808080", "0.575757"),
        ("0.393939", "0.464646", "0.575757", "0.686868", "0.797979", "0.909090", "0.949494", "0.676767"),
    ),
    "hold-out-absent": (
        567,
        ("0.101010", "0.161616", "0.222222", "0.282828", "0.343434", "0.404040", "0.464646", "0.292929"),
        ("0.121212", "0.191919", "0.262626", "0.333333", "0.414141", "0.494949", "0.565656", "0.343434"),
    ),
    "legacy-nonsense": (
        345,
        ("0.121212", "0.151515", "0.191919", "0.232323", "0.363636", "0.515151", "0.646464", "0.303030"),
        ("0.131313", "0.171717", "0.212121", "0.262626", "0.303030", "0.474747", "0.606060", "0.292929"),
    ),
}

#: ``group -> (below floor, anchored among them, absence fired)`` at ``F_portable``. From ``03``.
BELOW_SLICE: dict[str, tuple[int, int, int]] = {
    "human-prose": (12, 8, 4),
    "human-implementation-vocabulary": (11, 4, 7),
    "synthesized-identifier": (0, 0, 0),
    "self-supervised-answered": (12, 6, 6),
    "hold-out-absent": (456, 18, 438),
    "legacy-nonsense": (NONSENSE_BELOW, 3, NONSENSE_CAUGHT),
}

#: ``group -> anchored count`` over the whole group. From ``03``.
ANCHORED: dict[str, int] = {
    "human-prose": 12,
    "human-implementation-vocabulary": 123,
    "synthesized-identifier": 12,
    "self-supervised-answered": 234,
    "hold-out-absent": 23,
    "legacy-nonsense": 3,
}

#: ``cause -> count`` for the self-retrieval drops in ``08``.
DROPS: dict[str, int] = {
    "source_chunk_absent_from_kprime": 23,
    "sibling_chunk_same_file_only": 12,
    "holdout_file_exclusion_applied": 10,
}

#: The per-hit distribution row in ``06``: the seven percentiles then the mean.
PER_HIT = ("0.212121", "0.272727", "0.363636", "0.515151", "0.616161", "0.757575", "0.898989")
PER_HIT_MEAN = "0.525252"

#: ``(run 1, delta, run 2)`` for every field ``07`` reports drifting between the two runs.
RUN_DELTAS: tuple[tuple[str, str, str], ...] = (
    ("0.456789", "0.000012", "0.456801"),
    ("0.404040", "0.000023", "0.404063"),
    ("0.505050", "0.000034", "0.505084"),
    ("0.434343", "0.000045", "0.434388"),
)

#: Percentile labels in the order the stats tuples use them, with their cumulative fraction.
PERCENTILES: tuple[tuple[str, Decimal], ...] = (
    ("min", Decimal("0.00")),
    ("p5", Decimal("0.05")),
    ("p25", Decimal("0.25")),
    ("median", Decimal("0.50")),
    ("p75", Decimal("0.75")),
    ("p95", Decimal("0.95")),
    ("max", Decimal("1.00")),
)

MEDIAN_POSITION = 3
P5_POSITION = 1
P95_POSITION = 5
STAT_COUNT = 8

BANNER = "SYNTHETIC EXHIBIT — no value in this document is a measurement"
REPUNIT = re.compile(r"^0\.(\d)(\d)\1\2\1\2$")
DIGIT_RUNS = frozenset({"0.123456", "0.234567", "0.345678", "0.456789"})

DISTRIBUTIONS = "02-per-group-distributions.md"
ANCHOR_RATES = "03-anchor-rates.md"
SUMMARY = "01-summary.md"
PROVENANCE = "05-adopted-row-provenance.md"
PER_HIT_FILE = "06-per-hit-decomposition.md"
DETERMINISM = "07-determinism-and-run-receipt.md"
DROPS_FILE = "08-drop-diagnostics.md"


def _render_delta(delta: Decimal) -> str:
    """A signed six-decimal delta as the exhibit renders it (U+2212 for negatives)."""
    return f"{'+' if delta >= 0 else '−'}{abs(delta):.6f}"


def _rate(numerator: int, denominator: int) -> str:
    """A rate rendered the way every exhibit table renders one."""
    return f"{Decimal(numerator) / Decimal(denominator):.6f}"


class Auditor:
    """Collects violations rather than raising on the first one, so a run reports all of them."""

    def __init__(self, package: Path) -> None:
        self.package = package
        self.violations: list[str] = []
        self._text: dict[str, str] = {}

    def text(self, filename: str) -> str:
        """The exhibit file's text, read once."""
        if filename not in self._text:
            self._text[filename] = (self.package / filename).read_text(encoding="utf-8")
        return self._text[filename]

    def check(self, condition: bool, message: str) -> None:
        """Record a violation when ``condition`` is false."""
        if not condition:
            self.violations.append(message)

    def present(self, filename: str, value: str, why: str) -> None:
        """Assert a value appears as text in the file that is supposed to carry it.

        ⚠ **This leg is substring-only and it has a MEASURED blind spot.** A value that also
        occurs somewhere else in the same file still satisfies it, so an edit to one cell of a
        table passes as long as the old string survives anywhere. A positive control proved
        this: corrupting one Δ cell in ``02`` left the run green because the same number
        appeared in that group's width line. Anything whose POSITION matters is checked by
        :meth:`row` instead; ``present`` is for values that appear once and carry no structure.
        """
        self.check(value in self.text(filename), f"{filename}: {why} — {value!r} not present")

    def row(self, filename: str, heading: str, label: str, expected: tuple[str, ...],
            why: str, limit: int | None = None) -> None:
        """Assert one markdown table row, CELL BY CELL, under a given heading.

        Positional, so a value moving between cells is caught — which substring presence
        cannot see.
        """
        text = self.text(filename)
        start = text.find(heading)
        if start < 0:
            self.violations.append(f"{filename}: {why} — heading {heading!r} not found")
            return
        end = text.find("\n## ", start + len(heading))
        section = text[start : end if end > 0 else len(text)]
        for line in section.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            cells = [cell.strip().strip("*").strip() for cell in stripped.strip("|").split("|")]
            if cells and cells[0] == label:
                found = tuple(cell.strip("`") for cell in cells[1:])[:limit]
                self.check(
                    found == expected,
                    f"{filename}: {why} — row {label!r} is {found}, expected {expected}",
                )
                return
        self.violations.append(f"{filename}: {why} — row {label!r} not found under {heading!r}")

    def sentinel(self, value: str, why: str) -> None:
        """Assert an independently chosen real value is visibly artificial."""
        self.check(
            bool(REPUNIT.match(value)) or value in DIGIT_RUNS,
            f"implausibility: {why} — {value!r} is neither repunit nor digit run",
        )

    def bracket(self, fraction: Decimal, stats: tuple[str, ...], where: str) -> None:
        """Assert a below-floor FRACTION sits between the percentiles bracketing the floor."""
        lower_label = lower_frac = None
        upper_label = upper_frac = None
        for (label, cumulative), value in zip(PERCENTILES, stats[:7], strict=True):
            if Decimal(value) <= FLOOR_PORTABLE:
                lower_label, lower_frac = label, cumulative
            elif upper_label is None:
                upper_label, upper_frac = label, cumulative
        low = lower_frac if lower_frac is not None else Decimal(0)
        high = upper_frac if upper_frac is not None else Decimal(1)
        self.check(
            low <= fraction <= high,
            f"{where}: below-floor fraction {fraction} outside "
            f"[{lower_label or 'below-min'}={low}, {upper_label or 'above-max'}={high}]",
        )


def audit_floors(auditor: Auditor) -> None:
    """The two floors, their delta, and the intervals that must bracket them."""
    auditor.sentinel(str(FLOOR_LEGACY), "F_legacy")
    auditor.sentinel(str(FLOOR_PORTABLE), "F_portable")
    auditor.check(
        FLOOR_PORTABLE - FLOOR_LEGACY == HEADLINE_DELTA,
        f"01: F_portable - F_legacy != {HEADLINE_DELTA}",
    )
    auditor.present(SUMMARY, str(HEADLINE_DELTA), "the headline delta")
    for low, floor, high, name in (
        ("0.303030", FLOOR_LEGACY, "0.393939", "F_legacy"),
        ("0.404040", FLOOR_PORTABLE, "0.505050", "F_portable"),
    ):
        auditor.check(
            Decimal(low) < floor < Decimal(high), f"01: the interval does not bracket {name}"
        )
        auditor.sentinel(low, f"{name} ci_low")
        auditor.sentinel(high, f"{name} ci_high")


def audit_groups(auditor: Auditor) -> None:
    """Every per-group table in ``02``, plus its width line and its cross-group restatement."""
    total_n = 0
    cross_group: list[tuple[str, str, str, str, str]] = []
    for index, (group, (n, legacy, portable)) in enumerate(GROUPS.items(), start=1):
        total_n += n
        heading = f"## Group {index} — `{group}` (n = {n})"
        for label, stats in (("legacy", legacy), ("portable", portable)):
            ordered = [Decimal(value) for value in stats[:7]]
            auditor.check(
                ordered == sorted(ordered), f"02/{group}/{label}: percentiles are not monotone"
            )
            auditor.check(
                ordered[0] <= Decimal(stats[7]) <= ordered[-1],
                f"02/{group}/{label}: mean outside [min, max]",
            )
            for value in stats:
                auditor.sentinel(value, f"02/{group}/{label}")
            auditor.row(DISTRIBUTIONS, heading, label, stats, f"{group} stats")
        deltas = tuple(
            _render_delta(Decimal(portable[position]) - Decimal(legacy[position]))
            for position in range(STAT_COUNT)
        )
        auditor.row(DISTRIBUTIONS, heading, "Δ", deltas, f"{group} deltas")
        legacy_width = Decimal(legacy[P95_POSITION]) - Decimal(legacy[P5_POSITION])
        portable_width = Decimal(portable[P95_POSITION]) - Decimal(portable[P5_POSITION])
        auditor.present(
            DISTRIBUTIONS,
            f"p5–p95 width: legacy `{legacy_width:.6f}` · portable `{portable_width:.6f}` · "
            f"**Δ width `{_render_delta(portable_width - legacy_width)}`**",
            f"{group} width line",
        )
        cross_group.append(
            (
                group,
                deltas[MEDIAN_POSITION],
                deltas[P5_POSITION],
                deltas[P95_POSITION],
                _render_delta(portable_width - legacy_width),
            )
        )
    auditor.check(total_n == TOTAL_QUERIES, f"02: group sizes sum to {total_n}, not {TOTAL_QUERIES}")
    for group, median_delta, p5_delta, p95_delta, width_delta in cross_group:
        auditor.row(
            DISTRIBUTIONS, "## Cross-group view", f"`{group}`",
            (median_delta, p5_delta, p95_delta, width_delta), f"{group} cross-group row",
        )


def audit_below_slice(auditor: Auditor) -> None:
    """The anchor-gated below-floor slice, and its consistency with the distributions."""
    below_total = anchored_total = fired_total = 0
    for group, (below, anchored, fired) in BELOW_SLICE.items():
        n, _, portable = GROUPS[group]
        below_total += below
        anchored_total += anchored
        fired_total += fired
        auditor.check(below - anchored == fired, f"03/{group}: {below} - {anchored} != {fired}")
        auditor.check(
            anchored <= ANCHORED[group],
            f"03/{group}: {anchored} anchored below floor exceeds the group's {ANCHORED[group]}",
        )
        auditor.bracket(Decimal(below) / Decimal(n), portable, f"03/{group}")
        auditor.row(
            ANCHOR_RATES, "## Where the gate actually bit", f"`{group}`",
            (str(below), str(anchored), str(fired)), f"{group} below-floor slice",
        )
    auditor.check(below_total == BELOW_FLOOR_TOTAL, f"03: below-floor total is {below_total}")
    auditor.check(anchored_total == ANCHORED_BELOW_TOTAL, f"03: anchored-below is {anchored_total}")
    auditor.check(fired_total == FIRED_TOTAL, f"03: fired total is {fired_total}")
    answered = TOTAL_QUERIES - fired_total
    auditor.check(answered == ANSWERED_QUERIES, f"03: answered is {answered}")
    auditor.present(ANCHOR_RATES, str(ANSWERED_QUERIES), "the answered-query denominator")


def audit_acceptance(auditor: Auditor) -> None:
    """The two pre-registered legs, and the real union they are measured over."""
    prose = BELOW_SLICE["human-prose"]
    vocabulary = BELOW_SLICE["human-implementation-vocabulary"]
    union_n = GROUPS["human-prose"][0] + GROUPS["human-implementation-vocabulary"][0]
    auditor.check(union_n == REAL_UNION_N, f"01: the real union is {union_n}")
    auditor.check(prose[0] + vocabulary[0] == REAL_UNION_BELOW, "01: union below-floor disagrees")
    auditor.check(
        prose[2] + vocabulary[2] == REAL_UNION_FALSE_FIRES, "01: union false fires disagree"
    )
    false_fire = Decimal(REAL_UNION_FALSE_FIRES) / Decimal(REAL_UNION_N)
    catch = Decimal(NONSENSE_CAUGHT) / Decimal(NONSENSE_N)
    auditor.check(false_fire <= FALSE_FIRE_BAR, "01: acceptance leg 1 does not pass its own bar")
    auditor.check(catch >= CATCH_BAR, "01: acceptance leg 2 does not pass its own bar")
    auditor.present(SUMMARY, f"{false_fire:.6f}", "acceptance leg 1 value")
    auditor.present(SUMMARY, f"{catch:.6f}", "acceptance leg 2 value")
    auditor.bracket(
        Decimal(NONSENSE_BELOW) / Decimal(NONSENSE_N), GROUPS["legacy-nonsense"][2], "01/catch"
    )


def audit_anchor_rates(auditor: Auditor) -> None:
    """The whole-group anchor rates in ``03``."""
    anchored_sum = 0
    for group, anchored in ANCHORED.items():
        n = GROUPS[group][0]
        anchored_sum += anchored
        auditor.check(anchored <= n, f"03/{group}: anchored {anchored} exceeds n {n}")
        auditor.row(
            ANCHOR_RATES, "## Rate per group", f"`{group}`",
            (str(anchored), str(n)), f"{group} anchor counts", limit=2,
        )
        auditor.present(ANCHOR_RATES, _rate(anchored, n), f"{group} rate")
    auditor.check(anchored_sum == ANCHORED_TOTAL, f"03: anchored total is {anchored_sum}")
    auditor.present(ANCHOR_RATES, _rate(ANCHORED_TOTAL, TOTAL_QUERIES), "overall anchor rate")


def audit_drops(auditor: Auditor) -> None:
    """The C13 self-retrieval split, the C9 absent-leg drops, and the gate they must pass."""
    answered_pool = GROUPS["self-supervised-answered"][0]
    drop_total = sum(DROPS.values())
    auditor.check(drop_total == DROP_TOTAL, f"08: drops sum to {drop_total}")
    auditor.check(
        Decimal(drop_total) / Decimal(answered_pool) <= DROP_GATE,
        "08: the self-retrieval drop rate fails its own 20% gate",
    )
    for cause, count in DROPS.items():
        auditor.present(DROPS_FILE, cause, "drop cause name")
        auditor.present(DROPS_FILE, _rate(count, answered_pool), f"{cause} rate")
    auditor.check(answered_pool - drop_total == ADOPTED_N, "08: adopted_n disagrees")
    auditor.present(PROVENANCE, str(ADOPTED_N), "adopted_n on the row")
    auditor.check(
        GROUPS["hold-out-absent"][0] - ABSENT_LEG_DROPS == ABSENT_SAMPLES,
        "08: surviving absent samples disagree",
    )
    auditor.present(
        DROPS_FILE,
        _rate(drop_total - DROPS["sibling_chunk_same_file_only"], answered_pool),
        "the path-match counterfactual rate",
    )


def audit_per_hit(auditor: Auditor) -> None:
    """The over-flag decomposition, and the identity that makes its best-hit leg checkable."""
    auditor.check(
        ANSWERED_QUERIES * SHOWN_K == SHOWN_HITS, f"06: shown hits disagree with {SHOWN_K}x answered"
    )
    auditor.check(
        ANCHORED_BELOW_TOTAL + MIDLIST_BELOW_FLOOR == HITS_BELOW_FLOOR,
        "06: best-hit + mid-list != total below floor",
    )
    auditor.check(
        ANSWERED_QUERIES + MIDLIST_DENOMINATOR == SHOWN_HITS, "06: the denominators do not sum"
    )
    for label, count, denominator in (
        ("all shown hits", HITS_BELOW_FLOOR, SHOWN_HITS),
        ("best hit (rank 1)", ANCHORED_BELOW_TOTAL, ANSWERED_QUERIES),
        ("mid-list (ranks 2–10)", MIDLIST_BELOW_FLOOR, MIDLIST_DENOMINATOR),
    ):
        auditor.present(PER_HIT_FILE, _rate(count, denominator), f"{count}/{denominator} rate")
        auditor.row(
            PER_HIT_FILE, "## Over-flag decomposition", label,
            (str(count), str(denominator)), f"{label} counts", limit=2,
        )
    auditor.row(
        PER_HIT_FILE, "## Per-hit cosine distribution", str(SHOWN_HITS),
        (*PER_HIT, PER_HIT_MEAN), "per-hit distribution row",
    )
    auditor.bracket(Decimal(HITS_BELOW_FLOOR) / Decimal(SHOWN_HITS), PER_HIT, "06/per-hit")
    for value in (*PER_HIT, PER_HIT_MEAN):
        auditor.sentinel(value, "06/per-hit distribution")


def audit_determinism(auditor: Auditor) -> None:
    """The typed verdict, the two conditions it rests on, and the run's cost accounting."""
    auditor.check(
        OBSERVED_FLOOR_DRIFT < F2_CALIBRATED_GAP,
        "07: |Δfloor| is not inside the F2-calibrated gap it claims to be inside",
    )
    agreement = Decimal(AGREEMENT_NUMERATOR) / Decimal(TOTAL_QUERIES)
    auditor.check(agreement >= AGREEMENT_BAR, "07: agreement fails its own bar")
    auditor.present(DETERMINISM, f"{agreement:.6f}", "decision agreement")
    for run_one, delta, run_two in RUN_DELTAS:
        auditor.check(
            Decimal(run_one) + Decimal(delta) == Decimal(run_two),
            f"07: {run_one} + {delta} != {run_two}",
        )
        auditor.present(DETERMINISM, run_two, "run-2 value")
    auditor.check(
        EMBED_BUDGET - EMBEDS_USED == EMBED_REMAINING, "07: the embed budget does not reconcile"
    )
    auditor.present(DETERMINISM, "within_ci_by_construction", "typed verdict")


JSONL_NAME = "per-query-rows.jsonl"
JSONL_ROWS = 24
K_PRIME = 30
REQUIRED_ROW_KEYS = frozenset(
    {
        "_synthetic", "query_id", "group", "sampled_at_position", "query_text",
        "response_best_cosine", "has_verbatim_anchor", "absence_verdict_fired",
        "source_point_id", "self_retrieved", "self_retrieval_drop_cause", "hits",
    }
)
REQUIRED_HIT_KEYS = frozenset({"rank", "point_id", "vector_cosine", "shown"})


def audit_jsonl(auditor: Auditor) -> None:
    """The per-query rows: schema, capture depth, monotonicity, and every derived flag.

    C6(b) requires *"the per-query jsonl rows themselves"*, and until 2026-07-28 no instrument
    in this packet inspected them — so a truncated, fabricated file passed every gate. Each
    predicate below is re-derived from the row rather than read off it.
    """
    path = auditor.package / JSONL_NAME
    if not path.exists():
        auditor.violations.append(f"{JSONL_NAME}: absent")
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        auditor.violations.append(f"{JSONL_NAME}: empty")
        return
    auditor.check(
        json.loads(lines[0]).get("_banner") == BANNER, f"{JSONL_NAME}: first line is not the banner"
    )
    rows = [json.loads(line) for line in lines[1:]]
    auditor.check(len(rows) == JSONL_ROWS, f"{JSONL_NAME}: {len(rows)} rows, expected {JSONL_ROWS}")
    for row in rows:
        query = row.get("query_id", "<no query_id>")
        auditor.check(
            set(row) == REQUIRED_ROW_KEYS,
            f"{JSONL_NAME}/{query}: field set is {sorted(set(row) ^ REQUIRED_ROW_KEYS)} off spec",
        )
        auditor.check(row.get("_synthetic") is True, f"{JSONL_NAME}/{query}: not marked synthetic")
        auditor.check(
            row.get("group") in GROUPS, f"{JSONL_NAME}/{query}: group {row.get('group')!r} unknown"
        )
        best = row.get("response_best_cosine")
        auditor.sentinel(f"{best:.6f}", f"{JSONL_NAME}/{query} response_best_cosine")
        hits = row.get("hits") or []
        auditor.check(
            len(hits) == K_PRIME, f"{JSONL_NAME}/{query}: {len(hits)} hits, expected k' = {K_PRIME}"
        )
        cosines = [hit.get("vector_cosine") for hit in hits]
        auditor.check(
            cosines == sorted(cosines, reverse=True),
            f"{JSONL_NAME}/{query}: hit cosines are not monotone descending",
        )
        auditor.check(
            bool(hits) and cosines[0] == best,
            f"{JSONL_NAME}/{query}: rank-1 cosine != response_best_cosine",
        )
        for hit in hits:
            auditor.check(
                set(hit) == REQUIRED_HIT_KEYS, f"{JSONL_NAME}/{query}: a hit's field set is off spec"
            )
            auditor.check(
                hit.get("shown") is (hit.get("rank", 0) <= SHOWN_K),
                f"{JSONL_NAME}/{query}: rank {hit.get('rank')} `shown` disagrees with "
                f"SURVEY_K = {SHOWN_K} (bound (ii))",
            )
            auditor.sentinel(f"{hit.get('vector_cosine'):.6f}", f"{JSONL_NAME}/{query} hit cosine")
        auditor.check(
            row.get("absence_verdict_fired")
            == (Decimal(f"{best:.6f}") < FLOOR_PORTABLE and not row.get("has_verbatim_anchor")),
            f"{JSONL_NAME}/{query}: absence_verdict_fired disagrees with the anchor-gated predicate",
        )
        auditor.check(
            [hit["rank"] for hit in hits] == list(range(1, K_PRIME + 1)),
            f"{JSONL_NAME}/{query}: ranks are not 1..{K_PRIME}",
        )


def audit_banner(auditor: Auditor) -> None:
    """Exhibit rule 1: every page carries the banner on its first line."""
    for path in sorted(auditor.package.iterdir()):
        first = path.read_text(encoding="utf-8").splitlines()[0]
        auditor.check(BANNER in first, f"{path.name}: first line does not carry the banner")


def audit(package: Path) -> list[str]:
    """Every coherence and implausibility relation the honest package claims."""
    auditor = Auditor(package)
    for leg in (
        audit_floors,
        audit_groups,
        audit_below_slice,
        audit_acceptance,
        audit_anchor_rates,
        audit_drops,
        audit_per_hit,
        audit_determinism,
        audit_jsonl,
        audit_banner,
    ):
        leg(auditor)
    return auditor.violations


if __name__ == "__main__":
    problems = audit(Path(sys.argv[1]))
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        sys.exit(1)
