"""Generate the synthetic ``per-query-rows.jsonl`` exhibit for the 11-i-b consumer consult.

⚠ **SYNTHETIC EXHIBIT GENERATOR — it emits no measurement.** Every value it writes is a
sentinel drawn from the two visibly-artificial families documented in the package's
``00-README.md``: two-digit repunits (``0.ababab``) for cosines, strictly monotone digit runs
for counts. The generator exists so the file's internal coherence is DERIVED rather than
hand-typed: hit cosines descend by a fixed repunit step from the query's response-best cosine,
so ranks are monotone by construction, and ``absence_verdict_fired`` is COMPUTED from the
anchor-gated predicate rather than asserted.

The sampling rule is stated rather than random: four queries per group, anchored at the group's
portable-instrument p95 / median / p25 / min, so the sample spans the group instead of favouring
its head. The file is a 24-row sample of a 1740-row run.

Run: ``python consult-11ib/tools/make_exhibit_jsonl.py <output-path>``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BANNER = "SYNTHETIC EXHIBIT — no value in this document is a measurement"

#: The chosen portable floor. Absence fires on ``max_cosine < floor AND NOT anchor``.
FLOOR_PORTABLE = 456_789

#: The capture depth (k'), and the shown slice (SURVEY_K), in ranks.
K_PRIME = 30
SHOWN_K = 10

#: Each hit is one repunit step below the previous one, floored so no cosine goes non-positive.
HIT_STEP_MICRO = 10_101
MIN_HIT_MICRO = 10_101

#: Where a self-retrieving probe's own source chunk sits in its capture. Fixed rather than
#: varied so a reader can DERIVE the ``self_retrieved`` flag from the hit list instead of
#: taking the flag's word for it.
SELF_RETRIEVAL_RANK = 3

#: ``(group, [p95, median, p25, min] in micro-units, anchored-count, sample query texts)``.
#: The four positions come straight from ``02-per-group-distributions.md``'s portable rows;
#: the anchored count is ``floor(4 * group anchor rate)`` from ``03-anchor-rates.md``.
GROUPS: tuple[tuple[str, tuple[int, int, int, int], int, tuple[str, ...]], ...] = (
    (
        "human-prose",
        (888_888, 646_464, 494_949, 333_333),
        0,
        (
            "how does the server decide it must not start up",
            "where is the once-per-process startup lease enforced",
            "what happens when an embedding input is too long to embed",
            "which module owns the chunk model the indexer consumes",
        ),
    ),
    (
        "human-implementation-vocabulary",
        (727_272, 646_464, 606_060, 414_141),
        2,
        (
            "retry_on_conflict backoff jitter",
            "ensure_ready idempotent schema slice",
            "hybrid_search fused rank candidate",
            "resolve_secret blankness predicate",
        ),
    ),
    (
        "synthesized-identifier",
        (797_979, 727_272, 686_868, 646_464),
        3,
        (
            "FloorCalibrationStore",
            "corpus_content_digest",
            "SurrealLeaderLock",
            "enumerate_calibration_pool",
        ),
    ),
    (
        "self-supervised-answered",
        (909_090, 686_868, 575_757, 393_939),
        2,
        (
            "head_identity — The ONE head-identity function (F6).",
            "record_measurement — Append one measurement row and, when adopt, advance the head.",
            "LeaseFence — The immutable (holder_identity, fence_epoch) snapshot a run commits under.",
            "MeasurementReceipt — What a completed run's commit returns.",
        ),
    ),
    (
        "hold-out-absent",
        (494_949, 333_333, 262_626, 121_212),
        0,
        (
            "what does the withheld module's exported helper return on an empty input",
            "which constant bounds the withheld retry loop",
            "how is the withheld adapter's fence epoch advanced",
            "what error does the withheld validator raise on a blank value",
        ),
    ),
    (
        "legacy-nonsense",
        (474_747, 262_626, 212_121, 131_313),
        0,
        (
            "porcelain trombone gradient of the quarterly wombat",
            "seventeen violet apostrophes reticulating",
            "the smell of Thursday in a filing cabinet",
            "unhelpful marmalade telemetry cascade",
        ),
    ),
)

POSITION_LABELS = ("p95", "median", "p25", "min")


def _micro_to_float(micro: int) -> float:
    """Render micro-units as a six-decimal float that repr's exactly."""
    return round(micro / 1_000_000, 6)


def _hits(group_slug: str, query_index: int, best_micro: int, source_point_id: str | None,
          self_retrieved: bool) -> list[dict[str, object]]:
    """The k' hit capture: monotone descending by a fixed repunit step, by construction."""
    hits: list[dict[str, object]] = []
    for rank in range(1, K_PRIME + 1):
        cosine_micro = max(best_micro - (rank - 1) * HIT_STEP_MICRO, MIN_HIT_MICRO)
        point_id = f"chunk:synthetic_{group_slug}_{query_index}_{rank:02d}"
        if self_retrieved and source_point_id is not None and rank == SELF_RETRIEVAL_RANK:
            point_id = source_point_id
        hits.append(
            {
                "rank": rank,
                "point_id": point_id,
                "vector_cosine": _micro_to_float(cosine_micro),
                "shown": rank <= SHOWN_K,
            }
        )
    return hits


def build_rows() -> list[dict[str, object]]:
    """Every row, coherent by construction with the package's summary artifacts."""
    rows: list[dict[str, object]] = []
    for group, positions, anchored_count, texts in GROUPS:
        group_slug = group.replace("-", "_")
        for query_index, (best_micro, label, text) in enumerate(
            zip(positions, POSITION_LABELS, texts, strict=True)
        ):
            has_anchor = query_index < anchored_count
            fired = best_micro < FLOOR_PORTABLE and not has_anchor
            is_self_supervised = group == "self-supervised-answered"
            source_point_id = (
                f"chunk:synthetic_source_{group_slug}_{query_index}" if is_self_supervised else None
            )
            # The lowest-positioned self-supervised probe is the file's one drop, so the
            # drop-cause vocabulary in 08 has a worked instance a reader can follow.
            self_retrieved = is_self_supervised and label != "min"
            drop_cause = (
                None
                if not is_self_supervised or self_retrieved
                else "source_chunk_absent_from_kprime"
            )
            rows.append(
                {
                    "_synthetic": True,
                    "query_id": f"q_{group_slug}_{query_index}",
                    "group": group,
                    "sampled_at_position": label,
                    "query_text": text,
                    "response_best_cosine": _micro_to_float(best_micro),
                    "has_verbatim_anchor": has_anchor,
                    "absence_verdict_fired": fired,
                    "source_point_id": source_point_id,
                    "self_retrieved": self_retrieved if is_self_supervised else None,
                    "self_retrieval_drop_cause": drop_cause,
                    "hits": _hits(group_slug, query_index, best_micro, source_point_id,
                                  self_retrieved),
                }
            )
    return rows


def main(destination: Path) -> None:
    """Write the banner line followed by one JSON object per query."""
    lines = [json.dumps({"_banner": BANNER}, ensure_ascii=False)]
    lines.extend(json.dumps(row, ensure_ascii=False) for row in build_rows())
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
